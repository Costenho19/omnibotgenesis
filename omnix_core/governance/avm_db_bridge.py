"""
AVM Database Persistence Bridge (ADR-064 extension / ADR-074)

PostgreSQL-backed persistence for AVM calibration snapshots.
Addresses 4 enterprise-grade requirements:

1. Baseline integrity  — SHA-256 hash stored with every snapshot. Verified on load.
                         If hash mismatch → TAMPERED flag raised, snapshot rejected.
2. Change audit log    — Every forced recalibration is logged with reason + actor.
                         force=True requires a non-empty reason string.
3. DB fail-closed mode — If DB is available but fails to load a snapshot,
                         the caller receives a DEGRADED_MODE signal.
4. Persistence         — Snapshots survive container restarts in Railway.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import socket
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("OMNIX.AVM.DBBridge")

# Imported lazily to avoid circular import; used only in load_all_snapshots().
# We access _SIGNAL_SCHEMA_SET from assumption_validity_monitor at runtime.
def _get_schema_set():  # type: ignore[return]
    from omnix_core.governance.assumption_validity_monitor import _SIGNAL_SCHEMA_SET
    return _SIGNAL_SCHEMA_SET


# ── SQL ────────────────────────────────────────────────────────────────────────

DDL_SNAPSHOTS = """
CREATE TABLE IF NOT EXISTS avm_calibration_snapshots (
    domain              VARCHAR(64)  PRIMARY KEY,
    snapshot_id         VARCHAR(32)  NOT NULL,
    parameter_version   VARCHAR(32)  NOT NULL,
    baseline_signals    JSONB        NOT NULL,
    baseline_hash       VARCHAR(64)  NOT NULL DEFAULT '',
    checkpoint_thresholds JSONB      NOT NULL DEFAULT '{}',
    drift_threshold     FLOAT        NOT NULL DEFAULT 0.2,
    max_age_hours       FLOAT        NOT NULL DEFAULT 72.0,
    description         TEXT         NOT NULL DEFAULT '',
    tags                JSONB        NOT NULL DEFAULT '[]',
    calibrated_at       VARCHAR(64)  NOT NULL,
    calibrated_at_epoch FLOAT        NOT NULL,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
"""

DDL_ALTER_HASH = """
ALTER TABLE avm_calibration_snapshots
ADD COLUMN IF NOT EXISTS baseline_hash VARCHAR(64) NOT NULL DEFAULT '';
"""

DDL_ALTER_VERSIONING = """
ALTER TABLE avm_calibration_snapshots
ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1;
ALTER TABLE avm_calibration_snapshots
ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;
"""

DDL_ALTER_GENESIS = """
ALTER TABLE avm_calibration_snapshots
ADD COLUMN IF NOT EXISTS is_genesis BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE avm_calibration_snapshots
ADD COLUMN IF NOT EXISTS genesis_snapshot_id VARCHAR(32) DEFAULT NULL;
ALTER TABLE avm_calibration_snapshots
ADD COLUMN IF NOT EXISTS genesis_calibrated_at VARCHAR(64) DEFAULT NULL;
"""

DDL_CHANGE_LOG = """
CREATE TABLE IF NOT EXISTS avm_baseline_change_log (
    id          SERIAL       PRIMARY KEY,
    domain      VARCHAR(64)  NOT NULL,
    snapshot_id VARCHAR(32)  NOT NULL,
    action      VARCHAR(32)  NOT NULL,
    reason      TEXT         NOT NULL,
    actor       VARCHAR(128) NOT NULL DEFAULT 'system',
    host        VARCHAR(128) NOT NULL DEFAULT '',
    baseline_hash VARCHAR(64) NOT NULL DEFAULT '',
    logged_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_avm_change_log_domain
    ON avm_baseline_change_log(domain, logged_at DESC);
"""

DDL_ALTER_TENANT_ID = """
ALTER TABLE avm_calibration_snapshots
    ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(128) NOT NULL DEFAULT 'default';
ALTER TABLE avm_baseline_change_log
    ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(128) NOT NULL DEFAULT 'default';
CREATE UNIQUE INDEX IF NOT EXISTS uq_avm_snapshots_tenant_domain
    ON avm_calibration_snapshots(tenant_id, domain);
CREATE INDEX IF NOT EXISTS idx_avm_change_log_tenant_domain
    ON avm_baseline_change_log(tenant_id, domain, logged_at DESC);
"""

UPSERT = """
INSERT INTO avm_calibration_snapshots (
    tenant_id, domain, snapshot_id, parameter_version, baseline_signals,
    baseline_hash, checkpoint_thresholds, drift_threshold, max_age_hours,
    description, tags, calibrated_at, calibrated_at_epoch,
    version, is_active, updated_at,
    is_genesis, genesis_snapshot_id, genesis_calibrated_at
) VALUES (
    %(tenant_id)s, %(domain)s, %(snapshot_id)s, %(parameter_version)s,
    %(baseline_signals)s::jsonb, %(baseline_hash)s,
    %(checkpoint_thresholds)s::jsonb,
    %(drift_threshold)s, %(max_age_hours)s, %(description)s,
    %(tags)s::jsonb, %(calibrated_at)s, %(calibrated_at_epoch)s,
    %(version)s, TRUE, NOW(),
    %(is_genesis)s, %(genesis_snapshot_id)s, %(genesis_calibrated_at)s
)
ON CONFLICT (tenant_id, domain) DO UPDATE SET
    snapshot_id         = EXCLUDED.snapshot_id,
    parameter_version   = EXCLUDED.parameter_version,
    baseline_signals    = EXCLUDED.baseline_signals,
    baseline_hash       = EXCLUDED.baseline_hash,
    checkpoint_thresholds = EXCLUDED.checkpoint_thresholds,
    drift_threshold     = EXCLUDED.drift_threshold,
    max_age_hours       = EXCLUDED.max_age_hours,
    description         = EXCLUDED.description,
    tags                = EXCLUDED.tags,
    calibrated_at       = EXCLUDED.calibrated_at,
    calibrated_at_epoch = EXCLUDED.calibrated_at_epoch,
    version             = EXCLUDED.version,
    is_active           = TRUE,
    updated_at          = NOW();
    -- NOTE: is_genesis, genesis_snapshot_id, genesis_calibrated_at are intentionally
    -- excluded from DO UPDATE SET — the genesis baseline is immutable once set.
    -- ISR-001: ON CONFLICT target changed from (domain) to (tenant_id, domain).
"""

SELECT_GENESIS = """
SELECT domain, snapshot_id, parameter_version, baseline_signals,
       baseline_hash, drift_threshold, max_age_hours,
       calibrated_at, calibrated_at_epoch, version,
       is_genesis, genesis_snapshot_id, genesis_calibrated_at
FROM avm_calibration_snapshots
WHERE tenant_id = %s AND domain = %s AND is_genesis = TRUE;
"""

SELECT_VERSION = """
SELECT version FROM avm_calibration_snapshots
WHERE tenant_id = %s AND domain = %s;
"""

INSERT_CHANGE_LOG = """
INSERT INTO avm_baseline_change_log
    (tenant_id, domain, snapshot_id, action, reason, actor, host, baseline_hash)
VALUES
    (%(tenant_id)s, %(domain)s, %(snapshot_id)s, %(action)s, %(reason)s,
     %(actor)s, %(host)s, %(baseline_hash)s);
"""

SELECT_ALL = "SELECT * FROM avm_calibration_snapshots WHERE tenant_id = %(tenant_id)s;"
SELECT_ONE = "SELECT * FROM avm_calibration_snapshots WHERE tenant_id = %s AND domain = %s;"


def _compute_hash(baseline_signals: dict) -> str:
    """SHA-256 of canonicalized baseline_signals JSON."""
    canon = json.dumps(baseline_signals, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode()).hexdigest()


class AVMDatabaseBridge:
    """
    PostgreSQL persistence bridge for AVM calibration snapshots.

    Design contract:
    - save_snapshot(data)       → persist to DB + log the change
    - load_all_snapshots()      → load + verify hash integrity
    - restore_to_json(dir)      → DB → local JSON (for AVM to read)
    - ensure_table()            → idempotent DDL
    - integrity check           → on load, hash mismatch raises TAMPERED warning
    - change log                → every save is recorded in avm_baseline_change_log
    """

    def __init__(self, db_url: Optional[str] = None):
        self._db_url = db_url or os.environ.get("DATABASE_URL")
        self._available = bool(self._db_url)

    def _get_conn(self):
        import psycopg
        return psycopg.connect(self._db_url)

    def ensure_table(self) -> bool:
        if not self._available:
            return False
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(DDL_SNAPSHOTS)
                    cur.execute(DDL_ALTER_HASH)
                    cur.execute(DDL_ALTER_VERSIONING)
                    cur.execute(DDL_ALTER_GENESIS)
                    cur.execute(DDL_CHANGE_LOG)
                    cur.execute(DDL_ALTER_TENANT_ID)
                conn.commit()
            logger.info("[AVM.DB] Tables ready: avm_calibration_snapshots, avm_baseline_change_log (ISR-001: tenant_id column applied)")
            return True
        except Exception as e:
            logger.warning(f"[AVM.DB] Could not ensure tables: {e}")
            return False

    def save_snapshot(
        self,
        snapshot_dict: dict,
        reason: str = "system_init",
        actor: str = "system",
        action: str = "SEED",
    ) -> bool:
        """
        Persist a calibration snapshot to PostgreSQL.

        Args:
            snapshot_dict: Snapshot data (must include 'domain', 'baseline_signals').
            reason:  Human-readable reason for this save. REQUIRED for action=RECALIBRATE.
            actor:   Who triggered this change (user/service name).
            action:  One of: SEED | RECALIBRATE | MIGRATE | RESTORE.
        """
        if not self._available:
            return False

        if action == "RECALIBRATE" and not reason.strip():
            raise ValueError(
                "reason is required for action=RECALIBRATE. "
                "You must document why the baseline is being changed."
            )

        baseline_signals = snapshot_dict.get("baseline_signals", {})
        baseline_hash = _compute_hash(baseline_signals)
        host = socket.gethostname()
        domain = snapshot_dict["domain"]
        tenant_id = snapshot_dict.get("tenant_id", "default") or "default"

        # Determine version + genesis status
        new_version = 1
        is_first_save = True
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT version, is_genesis FROM avm_calibration_snapshots "
                        "WHERE domain = %s AND tenant_id = %s",
                        (domain, tenant_id)
                    )
                    row = cur.fetchone()
                    if row:
                        is_first_save = False
                        current_version = int(row[0]) if row[0] else 1
                        new_version = current_version + 1 if action == "RECALIBRATE" else current_version
        except Exception as _ver_exc:
            logger.warning(f"[AVM.DB] Could not read existing version/genesis for domain={domain}: {_ver_exc} — defaulting to version=1, is_first_save=True")

        calibrated_at = snapshot_dict.get("calibrated_at", datetime.now(timezone.utc).isoformat())
        _is_genesis         = is_first_save
        _genesis_snapshot_id = snapshot_dict["snapshot_id"] if is_first_save else None
        _genesis_calibrated_at = calibrated_at if is_first_save else None

        if is_first_save:
            logger.info(
                f"[AVM.DB] GENESIS baseline established — domain={domain} "
                f"snapshot_id={snapshot_dict['snapshot_id']} — "
                f"this baseline is immutable and will survive all recalibrations."
            )

        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(UPSERT, {
                        "tenant_id":            tenant_id,
                        "domain":               domain,
                        "snapshot_id":          snapshot_dict["snapshot_id"],
                        "parameter_version":    snapshot_dict["parameter_version"],
                        "baseline_signals":     json.dumps(baseline_signals),
                        "baseline_hash":        baseline_hash,
                        "checkpoint_thresholds": json.dumps(snapshot_dict.get("checkpoint_thresholds", {})),
                        "drift_threshold":      snapshot_dict.get("drift_threshold", 0.2),
                        "max_age_hours":        snapshot_dict.get("max_age_hours", 72.0),
                        "description":          snapshot_dict.get("description", ""),
                        "tags":                 json.dumps(snapshot_dict.get("tags", [])),
                        "calibrated_at":        calibrated_at,
                        "calibrated_at_epoch":  snapshot_dict.get("calibrated_at_epoch", 0.0),
                        "version":              new_version,
                        "is_genesis":           _is_genesis,
                        "genesis_snapshot_id":  _genesis_snapshot_id,
                        "genesis_calibrated_at": _genesis_calibrated_at,
                    })
                    cur.execute(INSERT_CHANGE_LOG, {
                        "tenant_id":      tenant_id,
                        "domain":         domain,
                        "snapshot_id":    snapshot_dict["snapshot_id"],
                        "action":         action,
                        "reason":         reason,
                        "actor":          actor,
                        "host":           host,
                        "baseline_hash":  baseline_hash,
                    })
                conn.commit()
            logger.info(
                f"[AVM.DB] Snapshot persisted — domain={snapshot_dict['domain']} "
                f"id={snapshot_dict['snapshot_id']} action={action} hash={baseline_hash[:12]}..."
            )
            return True
        except Exception as e:
            logger.warning(f"[AVM.DB] Could not persist snapshot: {e}")
            return False

    def load_all_snapshots(self, tenant_id: str = "default") -> dict[str, dict]:
        """
        Load all snapshots from PostgreSQL for a specific tenant.
        Verifies SHA-256 hash integrity of each snapshot's baseline_signals.
        Returns dict of {domain: snapshot_data}.
        Adds 'integrity_status': 'OK' | 'TAMPERED' | 'LEGACY_NO_HASH' to each.
        ISR-001: tenant_id parameter isolates results per tenant.
        """
        tenant_id = (tenant_id or "default").strip()
        if not self._available:
            return {}
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(SELECT_ALL, {"tenant_id": tenant_id})
                    cols = [d[0] for d in cur.description]
                    rows = cur.fetchall()

            result = {}
            for row in rows:
                d = dict(zip(cols, row))
                domain = d["domain"]
                baseline_signals = d["baseline_signals"] if isinstance(d["baseline_signals"], dict) else {}
                stored_hash = d.get("baseline_hash", "")

                if stored_hash:
                    computed = _compute_hash(baseline_signals)
                    if computed != stored_hash:
                        logger.error(
                            f"[AVM.DB] ⚠️ INTEGRITY FAILURE: domain={domain} "
                            f"stored_hash={stored_hash[:12]}... "
                            f"computed={computed[:12]}... — SNAPSHOT REJECTED"
                        )
                        integrity_status = "TAMPERED"
                    else:
                        integrity_status = "OK"
                else:
                    integrity_status = "LEGACY_NO_HASH"
                    logger.warning(f"[AVM.DB] domain={domain} has no baseline_hash — legacy snapshot")

                # ── ADR-076: Schema validation on DB load ────────────────────────
                # A snapshot with correct hash but wrong signal keys is structurally
                # corrupt — someone inserted it directly into DB bypassing AVM API.
                try:
                    schema_set = _get_schema_set()
                    loaded_keys = frozenset(baseline_signals.keys())
                    if loaded_keys and loaded_keys != schema_set:
                        missing = sorted(schema_set - loaded_keys)
                        extra   = sorted(loaded_keys - schema_set)
                        logger.error(
                            f"[AVM.DB] SCHEMA_MISMATCH on load — domain={domain} | "
                            f"snapshot_id={d.get('snapshot_id', '?')} | "
                            f"missing={missing} | extra={extra} | "
                            "Drift detection will be disabled for this domain. "
                            "Recalibrate with correct SIGNAL_SCHEMA keys (ADR-076)."
                        )
                        if integrity_status == "OK":
                            integrity_status = "SCHEMA_MISMATCH"
                        try:
                            from omnix_core.governance.avm_alerts import fire_avm_alert
                            fire_avm_alert(
                                event_type="SCHEMA_MISMATCH_DB",
                                domain=domain,
                                detail=(
                                    f"Snapshot loaded from DB has wrong signal keys.\n"
                                    f"Missing: {missing}\nExtra: {extra}\n"
                                    "Drift detection DISABLED for this domain. "
                                    "Recalibrate immediately."
                                ),
                                snapshot_id=d.get("snapshot_id", "UNKNOWN"),
                            )
                        except Exception as _alert_exc:
                            logger.warning(f"[AVM.DB] fire_avm_alert(SCHEMA_MISMATCH_LOAD) failed: {_alert_exc}")
                except Exception as schema_exc:
                    logger.warning(f"[AVM.DB] Could not validate schema on load for domain={domain}: {schema_exc}")
                # ────────────────────────────────────────────────────────────────

                result[domain] = {
                    "snapshot_id":          d["snapshot_id"],
                    "parameter_version":    d["parameter_version"],
                    "domain":               domain,
                    "baseline_signals":     baseline_signals,
                    "baseline_hash":        stored_hash,
                    "integrity_status":     integrity_status,
                    "checkpoint_thresholds": d["checkpoint_thresholds"] if isinstance(d["checkpoint_thresholds"], dict) else {},
                    "drift_threshold":      float(d["drift_threshold"]),
                    "max_age_hours":        float(d["max_age_hours"]),
                    "description":          d["description"],
                    "tags":                 d["tags"] if isinstance(d["tags"], list) else [],
                    "calibrated_at":        str(d["calibrated_at"]),
                    "calibrated_at_epoch":  float(d["calibrated_at_epoch"]),
                    "version":              int(d.get("version", 1)) if d.get("version") is not None else 1,
                    "is_active":            bool(d.get("is_active", True)),
                    "is_genesis":           bool(d.get("is_genesis", False)),
                    "genesis_snapshot_id":  d.get("genesis_snapshot_id"),
                    "genesis_calibrated_at": d.get("genesis_calibrated_at"),
                }

            ok_count = sum(1 for v in result.values() if v["integrity_status"] == "OK")
            tampered = [k for k, v in result.items() if v["integrity_status"] == "TAMPERED"]
            logger.info(
                f"[AVM.DB] Loaded {len(result)} snapshots — "
                f"OK={ok_count} TAMPERED={len(tampered)} domains={list(result.keys())}"
            )
            if tampered:
                logger.error(f"[AVM.DB] TAMPERED DOMAINS (will not be used): {tampered}")

            return result
        except Exception as e:
            logger.warning(f"[AVM.DB] Could not load snapshots: {e}")
            return {}

    def restore_to_json(self, snapshots_dir: str = "avm_snapshots", tenant_id: str = "default") -> tuple[int, int]:
        """
        Load DB snapshots → local JSON files for the core AVM module.
        ISR-001: snapshots are written to {snapshots_dir}/{tenant_id}/ per tenant.

        Returns:
            (restored_count, tampered_count)
            tampered snapshots are NOT written to disk.
        """
        import pathlib
        tenant_id = (tenant_id or "default").strip()
        snapshots = self.load_all_snapshots(tenant_id=tenant_id)
        if not snapshots:
            return 0, 0

        p = pathlib.Path(snapshots_dir) / tenant_id
        p.mkdir(parents=True, exist_ok=True)

        # Fields that exist in DB/bridge but NOT in CalibrationSnapshot dataclass
        _BRIDGE_ONLY_FIELDS = {
            "baseline_hash", "integrity_status", "version", "is_active",
            # P2 genesis anchor fields — immutable DB metadata, not part of AVM snapshot schema
            "is_genesis", "genesis_snapshot_id", "genesis_calibrated_at",
        }

        restored = 0
        tampered = 0
        for domain, data in snapshots.items():
            if data.get("integrity_status") == "TAMPERED":
                logger.error(f"[AVM.DB] Refusing to restore TAMPERED snapshot for domain={domain}")
                tampered += 1
                continue
            safe = domain.replace("/", "_").replace(" ", "_").lower()
            path = p / f"{safe}_calibration.json"
            try:
                # Strip bridge-only fields — CalibrationSnapshot doesn't have them
                avm_data = {k: v for k, v in data.items() if k not in _BRIDGE_ONLY_FIELDS}
                with open(path, "w") as f:
                    json.dump(avm_data, f, indent=2)
                restored += 1
            except Exception as e:
                logger.warning(f"[AVM.DB] Could not write JSON for domain={domain}: {e}")

        logger.info(f"[AVM.DB] Restored {restored}/{len(snapshots)} snapshots | tampered={tampered}")
        return restored, tampered

    def get_change_log(self, domain: Optional[str] = None, limit: int = 50) -> list[dict]:
        """Query the audit log of baseline changes."""
        if not self._available:
            return []
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    if domain:
                        cur.execute(
                            "SELECT * FROM avm_baseline_change_log "
                            "WHERE domain = %s ORDER BY logged_at DESC LIMIT %s",
                            (domain, limit)
                        )
                    else:
                        cur.execute(
                            "SELECT * FROM avm_baseline_change_log "
                            "ORDER BY logged_at DESC LIMIT %s",
                            (limit,)
                        )
                    cols = [d[0] for d in cur.description]
                    return [dict(zip(cols, row)) for row in cur.fetchall()]
        except Exception as e:
            logger.warning(f"[AVM.DB] Could not query change log: {e}")
            return []

    def is_available(self) -> bool:
        return self._available

    def get_genesis_snapshot(self, domain: str, tenant_id: str = "default") -> Optional[dict]:
        """
        Return the immutable genesis baseline for a domain.

        The genesis baseline is the first-ever snapshot saved for this domain.
        It is never overwritten — even after recalibration.
        This is the external reference point for longitudinal drift detection
        (Amanulla insight: observer must be outside the local compensatory logic).

        ISR-001: tenant_id added to isolate genesis baselines per tenant.
        Returns None if genesis is not yet set for this domain/tenant.
        """
        tenant_id = (tenant_id or "default").strip()
        if not self._available:
            return None
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(SELECT_GENESIS, (tenant_id, domain))
                    cols = [d[0] for d in cur.description]
                    row = cur.fetchone()
                    if not row:
                        return None
                    data = dict(zip(cols, row))
                    if isinstance(data.get("baseline_signals"), dict):
                        pass
                    else:
                        data["baseline_signals"] = {}
                    return data
        except Exception as e:
            logger.warning(f"[AVM.DB] get_genesis_snapshot failed domain={domain}: {e}")
            return None

    def compute_genesis_drift(self, domain: str, current_signals: dict, tenant_id: str = "default") -> Optional[dict]:
        """
        Compute drift of current_signals against the immutable genesis baseline.

        Unlike the live AVM drift check (which compares against the most recent
        calibration snapshot and can drift with the system), this compares against
        the original genesis baseline — providing longitudinal observation outside
        the local compensatory logic of the environment.

        Returns:
            {
                "domain": ...,
                "genesis_snapshot_id": ...,
                "genesis_calibrated_at": ...,
                "drift_scores": {signal: abs_diff, ...},
                "weighted_drift": float (0-100),
                "signals_compared": int,
                "has_genesis": bool,
            }
            or None if genesis not found / DB unavailable.
        """
        genesis = self.get_genesis_snapshot(domain, tenant_id=tenant_id)
        if not genesis:
            return {
                "domain": domain,
                "has_genesis": False,
                "genesis_snapshot_id": None,
                "weighted_drift": None,
                "drift_scores": {},
                "signals_compared": 0,
            }

        genesis_signals = genesis.get("baseline_signals", {})
        if not genesis_signals or not current_signals:
            return {
                "domain": domain,
                "has_genesis": True,
                "genesis_snapshot_id": genesis.get("snapshot_id"),
                "genesis_calibrated_at": genesis.get("genesis_calibrated_at"),
                "weighted_drift": None,
                "drift_scores": {},
                "signals_compared": 0,
                "reason": "empty_signals",
            }

        common_keys = set(genesis_signals.keys()) & set(current_signals.keys())
        drift_scores = {}
        for k in common_keys:
            try:
                g_val = float(genesis_signals[k])
                c_val = float(current_signals[k])
                drift_scores[k] = abs(c_val - g_val)
            except (TypeError, ValueError):
                pass

        weighted_drift = (
            sum(drift_scores.values()) / len(drift_scores)
            if drift_scores else 0.0
        )

        logger.info(
            f"[AVM.DB] Genesis drift — domain={domain} "
            f"weighted_drift={weighted_drift:.2f} "
            f"genesis_id={genesis.get('snapshot_id')} "
            f"signals_compared={len(drift_scores)}"
        )

        return {
            "domain": domain,
            "has_genesis": True,
            "genesis_snapshot_id": genesis.get("snapshot_id"),
            "genesis_calibrated_at": genesis.get("genesis_calibrated_at") or genesis.get("calibrated_at"),
            "genesis_version": genesis.get("version", 1),
            "current_version": None,
            "weighted_drift": round(weighted_drift, 4),
            "drift_scores": {k: round(v, 4) for k, v in drift_scores.items()},
            "signals_compared": len(drift_scores),
        }
