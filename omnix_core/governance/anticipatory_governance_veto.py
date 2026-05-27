"""
OMNIX Governance — Anticipatory Governance Veto Protocol (AGVP)
ADR-174: Two-layer veto architecture for proactive governance failure detection.

The Anticipatory Governance Veto Protocol closes the detection latency gap in the
AVM's reactive evaluation model. The AGVPWatchdog continuously monitors all calibrated
domains. When it detects that live signals have drifted beyond the AVM threshold —
without any pending governance request — it emits a ProactiveVetoReceipt (PVR).

A PVR is a PQC-signed, database-persisted governance artifact. It precedes all subsequent
governance requests for the affected domain. When a request subsequently arrives, it does
not cause the veto. It finds it already in the ledger.

Two-Layer Veto Architecture:
    Layer 1 — Reactive Veto   (ADR-076): Triggered at request time by AVM.evaluate()
    Layer 2 — Anticipatory Veto (ADR-174): Triggered by AGVPWatchdog continuous polling

AGV Invariants (ADR-174 §Invariants):
    AGV-INV-001: ACTIVE PVR blocks with same authority as reactive AVM drift block
    AGV-INV-002: Watchdog cannot revoke its own PVRs — only admin revocation permitted
    AGV-INV-003: Watchdog interval must be >= AGVP_MIN_INTERVAL_SECONDS (30)
    AGV-INV-004: PVR content_hash commits to domain + tenant_id + drift_score +
                 signals_at_assessment + assessment_timestamp
    AGV-INV-005: PVR only emitted when AVM result has is_valid=False AND pass_through=False
    AGV-INV-006: Auto-recalibration (ADR-120) skips domains with active PVRs

ADR-174 — Harold Nunes — OMNIX QUANTUM LTD — May 2026
Priority Record: OMNIX-PAR-2026-AGVP-001
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("OMNIX.AGVP")

# ── Constants ────────────────────────────────────────────────────────────────

AGVP_MIN_INTERVAL_SECONDS: int = 30       # AGV-INV-003
AGVP_DEFAULT_INTERVAL_SECONDS: int = 60
AGVP_DEFAULT_MAX_SIGNAL_AGE_SECONDS: int = 300   # 5 minutes — stale signals skipped

_PVR_STATUS_ACTIVE = "ACTIVE"
_PVR_STATUS_REVOKED = "REVOKED"

# ── Database DDL ─────────────────────────────────────────────────────────────

DDL_AGVP = """
CREATE TABLE IF NOT EXISTS avm_anticipatory_veto_receipts (
    pvr_id                    TEXT PRIMARY KEY,
    tenant_id                 TEXT NOT NULL DEFAULT 'default',
    domain                    TEXT NOT NULL,
    drift_score               REAL NOT NULL,
    drift_threshold           REAL NOT NULL,
    drift_components          JSONB,
    signals_at_assessment     JSONB,
    signals_seen_at           TIMESTAMPTZ,
    snapshot_id               TEXT,
    assessment_timestamp      TIMESTAMPTZ NOT NULL,
    veto_effective_from       TIMESTAMPTZ NOT NULL,
    block_reason              TEXT,
    status                    TEXT NOT NULL DEFAULT 'ACTIVE',
    revoked_at                TIMESTAMPTZ,
    revoked_by                TEXT,
    revocation_reason         TEXT,
    watchdog_interval_seconds INTEGER,
    content_hash              TEXT,
    pqc_signature             TEXT,
    pqc_algorithm             TEXT DEFAULT 'ML-DSA-65',
    created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    structural_shift_class    TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_agvp_active_pvr_per_domain
    ON avm_anticipatory_veto_receipts (tenant_id, domain)
    WHERE status = 'ACTIVE';

CREATE INDEX IF NOT EXISTS idx_agvp_tenant_domain_status
    ON avm_anticipatory_veto_receipts (tenant_id, domain, status);

CREATE INDEX IF NOT EXISTS idx_agvp_created_at
    ON avm_anticipatory_veto_receipts (created_at DESC);
"""


# ── PQC Signing (identical pattern to DSPP / other ATF modules) ──────────────

def _pqc_sign(content_hash: str) -> Tuple[str, str]:
    """
    Sign content_hash with ML-DSA-65 (Dilithium-3).
    Returns (signature_b64, algorithm).
    Falls back to TESTING stub when TESTING=true or key unavailable.
    """
    if os.environ.get("TESTING", "").lower() == "true":
        return "TESTING", "ML-DSA-65"
    try:
        import base64
        sk_b64 = os.environ.get("OMNIX_SIGNING_SECRET_KEY_B64", "")
        if not sk_b64:
            logger.warning("[AGVP] OMNIX_SIGNING_SECRET_KEY_B64 not set — PVR unsigned")
            return "UNSIGNED", "ML-DSA-65"
        from dilithium_py.ml_dsa import ML_DSA_65
        sk = base64.b64decode(sk_b64)
        sig = ML_DSA_65.sign(sk, content_hash.encode("utf-8"))
        return base64.b64encode(sig).decode("utf-8"), "ML-DSA-65"
    except Exception as exc:
        logger.warning(f"[AGVP] PQC signing failed: {exc} — PVR unsigned")
        return "UNSIGNED", "ML-DSA-65"


def _compute_content_hash(pvr_id: str, tenant_id: str, domain: str,
                          drift_score: float, drift_threshold: float,
                          signals_at_assessment: dict,
                          assessment_timestamp: str,
                          veto_effective_from: str,
                          snapshot_id: str) -> str:
    """
    AGV-INV-004: Content hash commits to all forensically significant fields.
    Uses canonical JSON (sorted keys) for determinism.
    """
    payload = {
        "pvr_id": pvr_id,
        "tenant_id": tenant_id,
        "domain": domain,
        "drift_score": round(drift_score, 6),
        "drift_threshold": round(drift_threshold, 6),
        "signals_at_assessment": {k: round(v, 6) for k, v in sorted(signals_at_assessment.items())},
        "assessment_timestamp": assessment_timestamp,
        "veto_effective_from": veto_effective_from,
        "snapshot_id": snapshot_id,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ── ProactiveVetoReceipt dataclass ────────────────────────────────────────────

@dataclass
class ProactiveVetoReceipt:
    """
    A PVR is a PQC-signed governance artifact emitted by the AGVP Watchdog.
    It records that a domain exceeded its AVM drift threshold without any
    pending governance request — the veto precedes the request.

    Identifier format: OMNIX-PVR-{16HEX}
    """
    pvr_id: str
    tenant_id: str
    domain: str
    drift_score: float
    drift_threshold: float
    drift_components: Dict[str, float]
    signals_at_assessment: Dict[str, float]
    signals_seen_at: str                   # ISO UTC — when signals were last received
    snapshot_id: str
    assessment_timestamp: str             # When watchdog evaluated
    veto_effective_from: str              # Same as assessment_timestamp
    block_reason: str
    status: str                           # ACTIVE | REVOKED
    revoked_at: Optional[str]
    revoked_by: Optional[str]
    revocation_reason: Optional[str]
    watchdog_interval_seconds: int
    content_hash: str
    pqc_signature: str
    pqc_algorithm: str
    created_at: str
    structural_shift_class: Optional[str] = None  # SSD (ADR-175): STABLE | DRIFT_WITH_INSTABILITY | STRUCTURAL_SHIFT | INSUFFICIENT_DATA

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def is_active(self) -> bool:
        return self.status == _PVR_STATUS_ACTIVE


# ── Signal cache entry ────────────────────────────────────────────────────────

@dataclass
class _SignalCacheEntry:
    signals: Dict[str, float]
    seen_at: float   # time.monotonic() at time of update
    snapshot_id: str


# ── Module-level signal cache (thread-safe) ───────────────────────────────────
# Updated by the governance pipeline (before any PVR check) to preserve
# signal observability even when a domain is blocked (breaks deadlock).

_signal_cache: Dict[str, _SignalCacheEntry] = {}   # key: "{tenant_id}:{domain}"
_signal_cache_lock = threading.Lock()

# In-memory PVR cache for fast lookup (mirrors DB state for ACTIVE PVRs)
_active_pvr_cache: Dict[str, ProactiveVetoReceipt] = {}  # key: "{tenant_id}:{domain}"
_pvr_cache_lock = threading.Lock()


# ── DB helpers ────────────────────────────────────────────────────────────────

def _get_db_conn():
    """Get a psycopg2 connection from DATABASE_URL."""
    import psycopg
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        raise RuntimeError("[AGVP] DATABASE_URL not set — DB persistence unavailable")
    conn = psycopg.connect(db_url)
    None.register_uuid(conn)
    return conn


def _ensure_table() -> bool:
    """Idempotent DDL for the PVR table. Returns True on success."""
    try:
        conn = _get_db_conn()
        with conn, conn.cursor() as cur:
            cur.execute(DDL_AGVP)
        conn.close()
        return True
    except Exception as exc:
        logger.warning(f"[AGVP] Could not ensure DB table: {exc}")
        return False


def _persist_pvr(pvr: ProactiveVetoReceipt) -> bool:
    """
    Insert PVR into DB. Uses ON CONFLICT DO NOTHING for multi-dyno idempotency.
    The UNIQUE INDEX on (tenant_id, domain) WHERE status='ACTIVE' ensures only
    one active PVR per domain per tenant regardless of concurrent watchdog instances.
    Returns True if inserted, False if skipped (already exists).
    """
    try:
        conn = _get_db_conn()
        signals_seen_at = None
        if pvr.signals_seen_at:
            from dateutil.parser import parse as _parse_dt
            try:
                signals_seen_at = _parse_dt(pvr.signals_seen_at)
            except Exception:
                signals_seen_at = None

        with conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO avm_anticipatory_veto_receipts (
                    pvr_id, tenant_id, domain, drift_score, drift_threshold,
                    drift_components, signals_at_assessment, signals_seen_at,
                    snapshot_id, assessment_timestamp, veto_effective_from,
                    block_reason, status, watchdog_interval_seconds,
                    content_hash, pqc_signature, pqc_algorithm, created_at,
                    structural_shift_class
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s
                )
                ON CONFLICT DO NOTHING
                RETURNING pvr_id
            """, (
                pvr.pvr_id, pvr.tenant_id, pvr.domain,
                pvr.drift_score, pvr.drift_threshold,
                json.dumps(pvr.drift_components),
                json.dumps(pvr.signals_at_assessment),
                signals_seen_at,
                pvr.snapshot_id,
                pvr.assessment_timestamp, pvr.veto_effective_from,
                pvr.block_reason, pvr.status,
                pvr.watchdog_interval_seconds,
                pvr.content_hash, pvr.pqc_signature, pvr.pqc_algorithm,
                pvr.created_at,
                pvr.structural_shift_class,
            ))
            row = cur.fetchone()
        conn.close()
        if row:
            logger.info(f"[AGVP] PVR persisted — pvr_id={pvr.pvr_id} domain={pvr.domain}")
            return True
        else:
            logger.debug(f"[AGVP] PVR insert skipped (already exists) — domain={pvr.domain}")
            return False
    except Exception as exc:
        logger.error(f"[AGVP] DB persist failed for domain={pvr.domain}: {exc}")
        return False


def _load_active_pvr_from_db(domain: str, tenant_id: str = "default") -> Optional[ProactiveVetoReceipt]:
    """Load the active PVR for a domain from DB, if any."""
    try:
        conn = _get_db_conn()
        with conn, conn.cursor() as cur:
            cur.execute("""
                SELECT pvr_id, tenant_id, domain, drift_score, drift_threshold,
                       drift_components, signals_at_assessment, signals_seen_at,
                       snapshot_id, assessment_timestamp, veto_effective_from,
                       block_reason, status, revoked_at, revoked_by,
                       revocation_reason, watchdog_interval_seconds,
                       content_hash, pqc_signature, pqc_algorithm, created_at
                FROM avm_anticipatory_veto_receipts
                WHERE tenant_id = %s AND domain = %s AND status = 'ACTIVE'
                LIMIT 1
            """, (tenant_id, domain))
            row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return _row_to_pvr(row)
    except Exception as exc:
        logger.warning(f"[AGVP] DB load for domain={domain}: {exc}")
        return None


def _revoke_pvr_in_db(pvr_id: str, revoked_by: str, reason: str) -> bool:
    """Mark a PVR as REVOKED in DB."""
    try:
        conn = _get_db_conn()
        now = datetime.now(timezone.utc).isoformat()
        with conn, conn.cursor() as cur:
            cur.execute("""
                UPDATE avm_anticipatory_veto_receipts
                SET status = 'REVOKED', revoked_at = %s, revoked_by = %s, revocation_reason = %s
                WHERE pvr_id = %s AND status = 'ACTIVE'
                RETURNING pvr_id
            """, (now, revoked_by, reason, pvr_id))
            row = cur.fetchone()
        conn.close()
        return row is not None
    except Exception as exc:
        logger.error(f"[AGVP] DB revoke failed pvr_id={pvr_id}: {exc}")
        return False


def _list_active_pvrs_from_db(tenant_id: str = "default") -> List[Dict[str, Any]]:
    """Load all active PVRs for a tenant (used by watchdog at startup)."""
    try:
        conn = _get_db_conn()
        with conn, conn.cursor() as cur:
            cur.execute("""
                SELECT pvr_id, tenant_id, domain, drift_score, drift_threshold,
                       drift_components, signals_at_assessment, signals_seen_at,
                       snapshot_id, assessment_timestamp, veto_effective_from,
                       block_reason, status, revoked_at, revoked_by,
                       revocation_reason, watchdog_interval_seconds,
                       content_hash, pqc_signature, pqc_algorithm, created_at
                FROM avm_anticipatory_veto_receipts
                WHERE tenant_id = %s AND status = 'ACTIVE'
                ORDER BY created_at DESC
            """, (tenant_id,))
            rows = cur.fetchall()
        conn.close()
        return [_row_to_pvr(r) for r in rows]
    except Exception as exc:
        logger.warning(f"[AGVP] DB list active PVRs: {exc}")
        return []


def _row_to_pvr(row: tuple) -> ProactiveVetoReceipt:
    """Convert a DB row tuple to a ProactiveVetoReceipt."""
    def _iso(v) -> Optional[str]:
        if v is None:
            return None
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v)

    def _dict(v) -> dict:
        if v is None:
            return {}
        if isinstance(v, dict):
            return v
        try:
            return json.loads(v)
        except Exception:
            return {}

    return ProactiveVetoReceipt(
        pvr_id=row[0],
        tenant_id=row[1],
        domain=row[2],
        drift_score=float(row[3]),
        drift_threshold=float(row[4]),
        drift_components=_dict(row[5]),
        signals_at_assessment=_dict(row[6]),
        signals_seen_at=_iso(row[7]) or "",
        snapshot_id=row[8] or "",
        assessment_timestamp=_iso(row[9]) or "",
        veto_effective_from=_iso(row[10]) or "",
        block_reason=row[11] or "",
        status=row[12],
        revoked_at=_iso(row[13]),
        revoked_by=row[14],
        revocation_reason=row[15],
        watchdog_interval_seconds=row[16] or AGVP_DEFAULT_INTERVAL_SECONDS,
        content_hash=row[17] or "",
        pqc_signature=row[18] or "",
        pqc_algorithm=row[19] or "ML-DSA-65",
        created_at=_iso(row[20]) or "",
    )


# ── PVR factory ───────────────────────────────────────────────────────────────

def _create_pvr(
    domain: str,
    tenant_id: str,
    drift_score: float,
    drift_threshold: float,
    drift_components: Dict[str, float],
    signals_at_assessment: Dict[str, float],
    signals_seen_at: str,
    snapshot_id: str,
    block_reason: str,
    watchdog_interval_seconds: int,
    structural_shift_class: Optional[str] = None,
) -> ProactiveVetoReceipt:
    """
    Build and sign a ProactiveVetoReceipt. Does NOT persist — call _persist_pvr().
    """
    pvr_id = f"OMNIX-PVR-{uuid.uuid4().hex[:16].upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()

    content_hash = _compute_content_hash(
        pvr_id=pvr_id,
        tenant_id=tenant_id,
        domain=domain,
        drift_score=drift_score,
        drift_threshold=drift_threshold,
        signals_at_assessment=signals_at_assessment,
        assessment_timestamp=now_iso,
        veto_effective_from=now_iso,
        snapshot_id=snapshot_id,
    )
    pqc_sig, pqc_alg = _pqc_sign(content_hash)

    return ProactiveVetoReceipt(
        pvr_id=pvr_id,
        tenant_id=tenant_id,
        domain=domain,
        drift_score=drift_score,
        drift_threshold=drift_threshold,
        drift_components=drift_components,
        signals_at_assessment=signals_at_assessment,
        signals_seen_at=signals_seen_at,
        snapshot_id=snapshot_id,
        assessment_timestamp=now_iso,
        veto_effective_from=now_iso,
        block_reason=block_reason,
        status=_PVR_STATUS_ACTIVE,
        revoked_at=None,
        revoked_by=None,
        revocation_reason=None,
        watchdog_interval_seconds=watchdog_interval_seconds,
        content_hash=content_hash,
        pqc_signature=pqc_sig,
        pqc_algorithm=pqc_alg,
        created_at=now_iso,
        structural_shift_class=structural_shift_class,
    )


# ── AGVPWatchdog ──────────────────────────────────────────────────────────────

class AGVPWatchdog:
    """
    Daemon thread that continuously monitors all calibrated AVM domains.

    Operation cycle (every AGVP_WATCHDOG_INTERVAL_SECONDS):
      For each domain with cached signals:
        1. Skip if signals are stale (> AGVP_MAX_SIGNAL_AGE_SECONDS)
        2. Skip if an ACTIVE PVR already exists (idempotent — AGV-INV-001)
        3. Call AVM.evaluate(signals, domain)
        4. If is_valid=False AND pass_through=False (AGV-INV-005):
           → Emit PVR, persist to DB, fire Telegram alert
        5. If domain has ACTIVE PVR but drift has recovered:
           → Log RECOVERY_CANDIDATE (AGV-INV-002: watchdog cannot self-revoke)

    Multi-process safety: DB UNIQUE INDEX ensures only one ACTIVE PVR per tenant+domain.
    Concurrent watchdog instances calling _persist_pvr() will see ON CONFLICT DO NOTHING.
    """

    def __init__(
        self,
        tenant_id: str = "default",
        interval_seconds: int = AGVP_DEFAULT_INTERVAL_SECONDS,
        max_signal_age_seconds: int = AGVP_DEFAULT_MAX_SIGNAL_AGE_SECONDS,
    ):
        # AGV-INV-003: enforce minimum interval
        if interval_seconds < AGVP_MIN_INTERVAL_SECONDS:
            raise ValueError(
                f"AGV-INV-003 violation: watchdog interval {interval_seconds}s < "
                f"minimum {AGVP_MIN_INTERVAL_SECONDS}s. "
                "Continuous monitoring requires a non-zero, non-instantaneous interval."
            )
        self.tenant_id = tenant_id
        self.interval_seconds = interval_seconds
        self.max_signal_age_seconds = max_signal_age_seconds
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def start(self) -> None:
        """Start the watchdog daemon thread."""
        if self._running:
            logger.warning("[AGVP.Watchdog] Already running — start() ignored")
            return

        enabled = os.environ.get("AGVP_ENABLED", "true").lower() != "false"
        if not enabled:
            logger.info("[AGVP.Watchdog] AGVP_ENABLED=false — watchdog will not start")
            return

        _ensure_table()
        self._load_active_pvrs_into_cache()

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._watchdog_loop,
            name="omnix-agvp-watchdog",
            daemon=True,
        )
        self._thread.start()
        self._running = True
        logger.info(
            f"[AGVP.Watchdog] Started — interval={self.interval_seconds}s "
            f"max_signal_age={self.max_signal_age_seconds}s tenant={self.tenant_id}"
        )

    def stop(self) -> None:
        """Signal the watchdog to stop after the current cycle."""
        self._stop_event.set()
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=self.interval_seconds + 5)
        logger.info("[AGVP.Watchdog] Stopped")

    def is_running(self) -> bool:
        return self._running and (self._thread is not None) and self._thread.is_alive()

    def _load_active_pvrs_into_cache(self) -> None:
        """On startup, load all active PVRs from DB into memory cache."""
        pvrs = _list_active_pvrs_from_db(self.tenant_id)
        with _pvr_cache_lock:
            for pvr in pvrs:
                cache_key = f"{pvr.tenant_id}:{pvr.domain}"
                _active_pvr_cache[cache_key] = pvr
        if pvrs:
            logger.info(f"[AGVP.Watchdog] Loaded {len(pvrs)} active PVR(s) from DB into cache")

    def _watchdog_loop(self) -> None:
        """Main watchdog loop — runs until stop_event is set."""
        logger.info("[AGVP.Watchdog] Loop started")
        while not self._stop_event.is_set():
            try:
                self._run_cycle()
            except Exception as exc:
                logger.error(f"[AGVP.Watchdog] Cycle error (will retry): {exc}", exc_info=True)
            self._stop_event.wait(timeout=self.interval_seconds)
        logger.info("[AGVP.Watchdog] Loop ended")

    def _run_cycle(self) -> None:
        """
        Single watchdog evaluation cycle.
        Evaluates all domains with fresh cached signals.
        """
        now = time.monotonic()

        with _signal_cache_lock:
            snapshot = dict(_signal_cache)

        if not snapshot:
            logger.debug("[AGVP.Watchdog] No cached signals — cycle skipped")
            return

        from omnix_core.governance.avm_engine import AVMEngine
        avm = AVMEngine(tenant_id=self.tenant_id)

        domains_evaluated = 0
        domains_vetoed = 0
        domains_skipped_stale = 0
        domains_skipped_pvr = 0
        domains_recovery_candidate = 0

        for cache_key, entry in snapshot.items():
            if not cache_key.startswith(f"{self.tenant_id}:"):
                continue

            domain = cache_key[len(self.tenant_id) + 1:]

            # ── Freshness check ──────────────────────────────────────────────
            age_seconds = now - entry.seen_at
            if age_seconds > self.max_signal_age_seconds:
                logger.debug(
                    f"[AGVP.Watchdog] domain={domain} — signals stale "
                    f"({age_seconds:.0f}s > {self.max_signal_age_seconds}s) — skipped"
                )
                domains_skipped_stale += 1
                continue

            # ── Idempotency check — skip if already vetoed ───────────────────
            existing_pvr = _get_cached_active_pvr(domain, self.tenant_id)
            if existing_pvr is None:
                # Also check DB (another dyno may have emitted)
                existing_pvr = _load_active_pvr_from_db(domain, self.tenant_id)
                if existing_pvr:
                    # Cache it locally
                    with _pvr_cache_lock:
                        _active_pvr_cache[cache_key] = existing_pvr

            if existing_pvr is not None:
                # AGV-INV-002: watchdog cannot self-revoke — check for recovery candidate
                try:
                    avm_result = avm._get_avm().evaluate(entry.signals, domain)
                    if avm_result.is_valid and not avm_result.pass_through:
                        logger.info(
                            f"[AGVP.Watchdog] RECOVERY_CANDIDATE — domain={domain} "
                            f"drift={avm_result.drift_score:.1f} ≤ threshold — "
                            f"pvr_id={existing_pvr.pvr_id}. "
                            "Admin revocation required to resume governance (AGV-INV-002)."
                        )
                        domains_recovery_candidate += 1
                    else:
                        domains_skipped_pvr += 1
                except Exception:
                    domains_skipped_pvr += 1
                continue

            # ── AVM evaluation ───────────────────────────────────────────────
            try:
                avm_result = avm._get_avm().evaluate(entry.signals, domain)
            except Exception as exc:
                logger.warning(f"[AGVP.Watchdog] AVM evaluate failed domain={domain}: {exc}")
                continue

            domains_evaluated += 1

            # AGV-INV-005: only emit PVR on genuine drift block (not pass_through)
            if avm_result.is_valid or avm_result.pass_through:
                continue

            # ── Emit Proactive Veto Receipt ──────────────────────────────────
            signals_seen_at_iso = datetime.fromtimestamp(
                datetime.now(timezone.utc).timestamp() - age_seconds,
                tz=timezone.utc
            ).isoformat()

            # Extract SSD structural shift class (ADR-175) for PVR attestation
            _ssd_report = avm_result.structural_shift_report
            _ssd_class = (
                _ssd_report.get("shift_class")
                if isinstance(_ssd_report, dict)
                else None
            )

            pvr = _create_pvr(
                domain=domain,
                tenant_id=self.tenant_id,
                drift_score=avm_result.drift_score,
                drift_threshold=avm_result.drift_threshold,
                drift_components=avm_result.drift_components,
                signals_at_assessment=dict(entry.signals),
                signals_seen_at=signals_seen_at_iso,
                snapshot_id=avm_result.snapshot_id,
                block_reason=(
                    f"ANTICIPATORY_VETO: {avm_result.block_reason or 'Drift exceeded threshold'} "
                    f"[detected by AGVPWatchdog, interval={self.interval_seconds}s, "
                    f"signal_age={age_seconds:.0f}s] (ADR-174)"
                ),
                watchdog_interval_seconds=self.interval_seconds,
                structural_shift_class=_ssd_class,
            )

            inserted = _persist_pvr(pvr)
            if inserted:
                # Update in-memory cache
                with _pvr_cache_lock:
                    _active_pvr_cache[cache_key] = pvr

                domains_vetoed += 1
                logger.warning(
                    f"[AGVP.Watchdog] PROACTIVE_VETO EMITTED — "
                    f"pvr_id={pvr.pvr_id} domain={domain} "
                    f"drift={pvr.drift_score:.1f} > threshold={pvr.drift_threshold:.1f} "
                    f"snapshot={pvr.snapshot_id}"
                )
                self._fire_anticipatory_alert(pvr)

        if domains_evaluated > 0 or domains_vetoed > 0:
            logger.info(
                f"[AGVP.Watchdog] Cycle complete — "
                f"evaluated={domains_evaluated} vetoed={domains_vetoed} "
                f"skipped_pvr={domains_skipped_pvr} stale={domains_skipped_stale} "
                f"recovery_candidates={domains_recovery_candidate}"
            )

    def _fire_anticipatory_alert(self, pvr: ProactiveVetoReceipt) -> None:
        """Fire Telegram alert for proactive veto emission."""
        try:
            from omnix_core.governance.avm_alerts import fire_avm_alert
            fire_avm_alert(
                event_type="ANTICIPATORY_VETO",
                domain=pvr.domain,
                detail=(
                    f"🛡️ PROACTIVE VETO EMITTED (ADR-174 AGVP)\n"
                    f"pvr_id: {pvr.pvr_id}\n"
                    f"drift_score: {pvr.drift_score:.1f} > threshold: {pvr.drift_threshold:.1f}\n"
                    f"All governance requests for domain '{pvr.domain}' are now blocked.\n"
                    f"Admin revocation required to resume. block_reason: {pvr.block_reason[:200]}"
                ),
                snapshot_id=pvr.snapshot_id,
            )
        except Exception as exc:
            logger.warning(f"[AGVP.Watchdog] Alert fire failed: {exc}")


# ── AGVPEngine — Public API ───────────────────────────────────────────────────

class AGVPEngine:
    """
    Public API for the Anticipatory Governance Veto Protocol.

    Exposes:
      update_domain_signals()  — called by governance pipeline BEFORE any PVR check
      get_active_pvr()         — check if a domain has an active proactive veto
      has_active_pvr()         — boolean convenience wrapper
      revoke_pvr()             — admin-only PVR revocation (AGV-INV-002)
      list_active_pvrs()       — list all active PVRs for a tenant
      start_watchdog()         — start the background monitoring thread
      stop_watchdog()          — stop the monitoring thread
      watchdog_status()        — health and metrics
    """

    def __init__(self, tenant_id: str = "default"):
        self.tenant_id = tenant_id
        self._watchdog: Optional[AGVPWatchdog] = None

    # ── Signal management ─────────────────────────────────────────────────────

    def update_domain_signals(
        self,
        domain: str,
        signals: Dict[str, float],
        snapshot_id: str = "",
    ) -> None:
        """
        Update the signal cache for a domain. Called by the governance pipeline
        BEFORE checking for active PVRs — preserves observability regardless of
        block status (breaks the watchdog observability deadlock, ADR-174 §Design).

        This method is unconditional: it always runs, even when a PVR is active.
        """
        cache_key = f"{self.tenant_id}:{domain}"
        entry = _SignalCacheEntry(
            signals=dict(signals),
            seen_at=time.monotonic(),
            snapshot_id=snapshot_id,
        )
        with _signal_cache_lock:
            _signal_cache[cache_key] = entry

    # ── PVR query ─────────────────────────────────────────────────────────────

    def get_active_pvr(self, domain: str) -> Optional[ProactiveVetoReceipt]:
        """
        Return the active PVR for this domain, or None if no proactive veto is in effect.

        Checks in-memory cache first (fast path), then DB (cold path on first access
        or after process restart). The result is cached in memory after DB lookup.

        AGV-INV-001: An ACTIVE PVR has the same blocking authority as a reactive veto.
        """
        cache_key = f"{self.tenant_id}:{domain}"

        # Fast path: in-memory cache
        pvr = _get_cached_active_pvr(domain, self.tenant_id)
        if pvr is not None:
            return pvr

        # Cold path: DB (process restart, other dyno emitted PVR)
        pvr = _load_active_pvr_from_db(domain, self.tenant_id)
        if pvr is not None:
            with _pvr_cache_lock:
                _active_pvr_cache[cache_key] = pvr
        return pvr

    def has_active_pvr(self, domain: str) -> bool:
        """Boolean check for active PVR — convenience wrapper."""
        return self.get_active_pvr(domain) is not None

    # ── Admin operations ──────────────────────────────────────────────────────

    def revoke_pvr(
        self,
        pvr_id: str,
        revoked_by: str,
        reason: str,
        admin_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Revoke an active PVR. Admin-only operation (AGV-INV-002).

        The watchdog cannot call this method — revocation requires explicit admin
        action with documented reason. This creates an accountability record:
        the admin attests that the domain is safe to resume governance.

        Args:
            pvr_id:      The PVR to revoke (OMNIX-PVR-*)
            revoked_by:  Identity of the admin performing revocation
            reason:      Documented reason for revocation
            admin_token: Optional — validated against AGVP_ADMIN_TOKEN env var
                         If AGVP_ADMIN_TOKEN is set, token must match.

        Returns:
            {success: bool, pvr_id: str, message: str}
        """
        # Token validation
        required_token = os.environ.get("AGVP_ADMIN_TOKEN", "")
        if required_token and admin_token != required_token:
            logger.warning(
                f"[AGVP] revoke_pvr rejected — invalid admin_token "
                f"pvr_id={pvr_id} revoked_by={revoked_by}"
            )
            return {
                "success": False,
                "pvr_id": pvr_id,
                "message": "AGV-INV-002: Invalid admin token — revocation denied",
            }

        if not revoked_by or not reason:
            return {
                "success": False,
                "pvr_id": pvr_id,
                "message": "AGV-INV-002: revoked_by and reason are required for PVR revocation",
            }

        ok = _revoke_pvr_in_db(pvr_id, revoked_by, reason)
        if ok:
            # Invalidate in-memory cache — find by pvr_id
            with _pvr_cache_lock:
                keys_to_remove = [
                    k for k, v in _active_pvr_cache.items()
                    if v.pvr_id == pvr_id and v.tenant_id == self.tenant_id
                ]
                for k in keys_to_remove:
                    del _active_pvr_cache[k]

            logger.info(
                f"[AGVP] PVR REVOKED — pvr_id={pvr_id} "
                f"revoked_by={revoked_by} reason={reason[:100]}"
            )
            return {
                "success": True,
                "pvr_id": pvr_id,
                "message": f"PVR {pvr_id} revoked by {revoked_by}",
            }
        else:
            return {
                "success": False,
                "pvr_id": pvr_id,
                "message": f"PVR {pvr_id} not found or already revoked",
            }

    def list_active_pvrs(self) -> List[ProactiveVetoReceipt]:
        """List all active PVRs for this tenant from DB."""
        return _list_active_pvrs_from_db(self.tenant_id)

    def list_pvr_history(
        self, domain: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Load PVR history (all statuses) for audit purposes."""
        try:
            conn = _get_db_conn()
            with conn, conn.cursor() as cur:
                if domain:
                    cur.execute("""
                        SELECT pvr_id, domain, drift_score, drift_threshold,
                               status, assessment_timestamp, revoked_at,
                               revoked_by, block_reason, content_hash
                        FROM avm_anticipatory_veto_receipts
                        WHERE tenant_id = %s AND domain = %s
                        ORDER BY created_at DESC LIMIT %s
                    """, (self.tenant_id, domain, limit))
                else:
                    cur.execute("""
                        SELECT pvr_id, domain, drift_score, drift_threshold,
                               status, assessment_timestamp, revoked_at,
                               revoked_by, block_reason, content_hash
                        FROM avm_anticipatory_veto_receipts
                        WHERE tenant_id = %s
                        ORDER BY created_at DESC LIMIT %s
                    """, (self.tenant_id, limit))
                rows = cur.fetchall()
            conn.close()
            return [
                {
                    "pvr_id": r[0], "domain": r[1], "drift_score": r[2],
                    "drift_threshold": r[3], "status": r[4],
                    "assessment_timestamp": str(r[5]) if r[5] else None,
                    "revoked_at": str(r[6]) if r[6] else None,
                    "revoked_by": r[7], "block_reason": r[8], "content_hash": r[9],
                }
                for r in rows
            ]
        except Exception as exc:
            logger.warning(f"[AGVP] list_pvr_history failed: {exc}")
            return []

    # ── Watchdog lifecycle ────────────────────────────────────────────────────

    def start_watchdog(
        self,
        interval_seconds: Optional[int] = None,
        max_signal_age_seconds: Optional[int] = None,
    ) -> None:
        """
        Start the AGVP background watchdog thread.
        Safe to call multiple times — subsequent calls are no-ops if already running.
        """
        interval = interval_seconds or int(
            os.environ.get("AGVP_WATCHDOG_INTERVAL_SECONDS", str(AGVP_DEFAULT_INTERVAL_SECONDS))
        )
        max_age = max_signal_age_seconds or int(
            os.environ.get("AGVP_MAX_SIGNAL_AGE_SECONDS", str(AGVP_DEFAULT_MAX_SIGNAL_AGE_SECONDS))
        )
        if self._watchdog is None or not self._watchdog.is_running():
            self._watchdog = AGVPWatchdog(
                tenant_id=self.tenant_id,
                interval_seconds=interval,
                max_signal_age_seconds=max_age,
            )
            self._watchdog.start()

    def stop_watchdog(self) -> None:
        """Stop the AGVP watchdog thread."""
        if self._watchdog and self._watchdog.is_running():
            self._watchdog.stop()
            self._watchdog = None

    def watchdog_status(self) -> Dict[str, Any]:
        """Return watchdog health and current PVR counts."""
        active_pvrs = _list_active_pvrs_from_db(self.tenant_id)
        with _signal_cache_lock:
            monitored_domains = [
                k[len(self.tenant_id) + 1:]
                for k in _signal_cache
                if k.startswith(f"{self.tenant_id}:")
            ]
        return {
            "watchdog_running": self._watchdog.is_running() if self._watchdog else False,
            "interval_seconds": self._watchdog.interval_seconds if self._watchdog else None,
            "monitored_domains": monitored_domains,
            "active_pvr_count": len(active_pvrs),
            "active_pvrs": [p.pvr_id for p in active_pvrs],
            "tenant_id": self.tenant_id,
        }


# ── Module-level helpers ──────────────────────────────────────────────────────

def _get_cached_active_pvr(domain: str, tenant_id: str) -> Optional[ProactiveVetoReceipt]:
    cache_key = f"{tenant_id}:{domain}"
    with _pvr_cache_lock:
        return _active_pvr_cache.get(cache_key)


def update_domain_signals(
    domain: str,
    signals: Dict[str, float],
    tenant_id: str = "default",
    snapshot_id: str = "",
) -> None:
    """
    Module-level shortcut for update_domain_signals().
    Called by the governance pipeline entry point (avm_engine.py) BEFORE any
    PVR check — preserves watchdog observability regardless of block state.
    """
    AGVPEngine(tenant_id).update_domain_signals(domain, signals, snapshot_id)


def get_active_pvr(domain: str, tenant_id: str = "default") -> Optional[ProactiveVetoReceipt]:
    """Module-level shortcut — check for active anticipatory veto."""
    return AGVPEngine(tenant_id).get_active_pvr(domain)


def has_active_pvr(domain: str, tenant_id: str = "default") -> bool:
    """Module-level boolean check — is this domain under an active proactive veto?"""
    return get_active_pvr(domain, tenant_id) is not None


# ── ADR-120 integration guard (AGV-INV-006) ───────────────────────────────────

def is_domain_safe_for_recalibration(domain: str, tenant_id: str = "default") -> Tuple[bool, str]:
    """
    AGV-INV-006: Returns (True, "") if domain can be auto-recalibrated.
    Returns (False, reason) if an active PVR blocks recalibration.

    Called by auto_recalibrate_stale_domains() before recalibrating any domain.
    """
    pvr = get_active_pvr(domain, tenant_id)
    if pvr is None:
        return True, ""
    return False, (
        f"AGV-INV-006: Domain '{domain}' has an active PVR ({pvr.pvr_id}, "
        f"emitted {pvr.veto_effective_from}). "
        "Auto-recalibration is frozen. Admin must revoke PVR before recalibration."
    )


# ── Singleton watchdog for process-level deployment ───────────────────────────

_process_watchdog: Optional[AGVPWatchdog] = None
_process_watchdog_lock = threading.Lock()


def start_process_watchdog(tenant_id: str = "default") -> AGVPWatchdog:
    """
    Start the process-level singleton watchdog. Safe to call from Flask startup,
    run_services.py, or any WSGI worker initializer. Subsequent calls are no-ops.
    """
    global _process_watchdog
    with _process_watchdog_lock:
        if _process_watchdog is None or not _process_watchdog.is_running():
            interval = int(os.environ.get(
                "AGVP_WATCHDOG_INTERVAL_SECONDS",
                str(AGVP_DEFAULT_INTERVAL_SECONDS)
            ))
            _process_watchdog = AGVPWatchdog(
                tenant_id=tenant_id,
                interval_seconds=interval,
            )
            _process_watchdog.start()
    return _process_watchdog


def stop_process_watchdog() -> None:
    """Stop the process-level singleton watchdog."""
    global _process_watchdog
    with _process_watchdog_lock:
        if _process_watchdog and _process_watchdog.is_running():
            _process_watchdog.stop()
            _process_watchdog = None
