"""
AVM Database Persistence Bridge (ADR-064 extension)

Provides PostgreSQL-backed persistence for AVM calibration snapshots,
solving the ephemeral filesystem problem in containerized deployments (Railway).

Strategy:
  1. On startup: load snapshots from DB → write to local JSON (so AVM can read them)
  2. On save: write to both DB and local JSON (dual persistence)
  3. On load: DB is the source of truth; JSON is the local cache

This class wraps AssumptionValidityMonitor without modifying its core.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("OMNIX.AVM.DBBridge")


# ── SQL ────────────────────────────────────────────────────────────────────────

DDL = """
CREATE TABLE IF NOT EXISTS avm_calibration_snapshots (
    domain              VARCHAR(64)  PRIMARY KEY,
    snapshot_id         VARCHAR(32)  NOT NULL,
    parameter_version   VARCHAR(32)  NOT NULL,
    baseline_signals    JSONB        NOT NULL,
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

UPSERT = """
INSERT INTO avm_calibration_snapshots (
    domain, snapshot_id, parameter_version, baseline_signals,
    checkpoint_thresholds, drift_threshold, max_age_hours,
    description, tags, calibrated_at, calibrated_at_epoch, updated_at
) VALUES (
    %(domain)s, %(snapshot_id)s, %(parameter_version)s,
    %(baseline_signals)s::jsonb, %(checkpoint_thresholds)s::jsonb,
    %(drift_threshold)s, %(max_age_hours)s, %(description)s,
    %(tags)s::jsonb, %(calibrated_at)s, %(calibrated_at_epoch)s, NOW()
)
ON CONFLICT (domain) DO UPDATE SET
    snapshot_id         = EXCLUDED.snapshot_id,
    parameter_version   = EXCLUDED.parameter_version,
    baseline_signals    = EXCLUDED.baseline_signals,
    checkpoint_thresholds = EXCLUDED.checkpoint_thresholds,
    drift_threshold     = EXCLUDED.drift_threshold,
    max_age_hours       = EXCLUDED.max_age_hours,
    description         = EXCLUDED.description,
    tags                = EXCLUDED.tags,
    calibrated_at       = EXCLUDED.calibrated_at,
    calibrated_at_epoch = EXCLUDED.calibrated_at_epoch,
    updated_at          = NOW();
"""

SELECT_ALL = "SELECT * FROM avm_calibration_snapshots;"
SELECT_ONE = "SELECT * FROM avm_calibration_snapshots WHERE domain = %s;"


class AVMDatabaseBridge:
    """
    Bridges AVM calibration snapshots to PostgreSQL.
    Operates independently of the core AVM module — no imports from it.
    """

    def __init__(self, db_url: Optional[str] = None):
        self._db_url = db_url or os.environ.get("DATABASE_URL")
        self._available = bool(self._db_url)

    def _get_conn(self):
        import psycopg2
        return psycopg2.connect(self._db_url)

    def ensure_table(self) -> bool:
        if not self._available:
            return False
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(DDL)
                conn.commit()
            logger.info("[AVM.DB] Table avm_calibration_snapshots ready")
            return True
        except Exception as e:
            logger.warning(f"[AVM.DB] Could not ensure table: {e}")
            return False

    def save_snapshot(self, snapshot_dict: dict) -> bool:
        if not self._available:
            return False
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(UPSERT, {
                        "domain":               snapshot_dict["domain"],
                        "snapshot_id":          snapshot_dict["snapshot_id"],
                        "parameter_version":    snapshot_dict["parameter_version"],
                        "baseline_signals":     json.dumps(snapshot_dict.get("baseline_signals", {})),
                        "checkpoint_thresholds": json.dumps(snapshot_dict.get("checkpoint_thresholds", {})),
                        "drift_threshold":      snapshot_dict.get("drift_threshold", 0.2),
                        "max_age_hours":        snapshot_dict.get("max_age_hours", 72.0),
                        "description":          snapshot_dict.get("description", ""),
                        "tags":                 json.dumps(snapshot_dict.get("tags", [])),
                        "calibrated_at":        snapshot_dict.get("calibrated_at", datetime.now(timezone.utc).isoformat()),
                        "calibrated_at_epoch":  snapshot_dict.get("calibrated_at_epoch", 0.0),
                    })
                conn.commit()
            logger.info(f"[AVM.DB] Snapshot persisted — domain={snapshot_dict['domain']} id={snapshot_dict['snapshot_id']}")
            return True
        except Exception as e:
            logger.warning(f"[AVM.DB] Could not persist snapshot: {e}")
            return False

    def load_all_snapshots(self) -> dict[str, dict]:
        if not self._available:
            return {}
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(SELECT_ALL)
                    cols = [d[0] for d in cur.description]
                    rows = cur.fetchall()
            result = {}
            for row in rows:
                d = dict(zip(cols, row))
                domain = d["domain"]
                result[domain] = {
                    "snapshot_id":          d["snapshot_id"],
                    "parameter_version":    d["parameter_version"],
                    "domain":               domain,
                    "baseline_signals":     d["baseline_signals"] if isinstance(d["baseline_signals"], dict) else {},
                    "checkpoint_thresholds": d["checkpoint_thresholds"] if isinstance(d["checkpoint_thresholds"], dict) else {},
                    "drift_threshold":      float(d["drift_threshold"]),
                    "max_age_hours":        float(d["max_age_hours"]),
                    "description":          d["description"],
                    "tags":                 d["tags"] if isinstance(d["tags"], list) else [],
                    "calibrated_at":        str(d["calibrated_at"]),
                    "calibrated_at_epoch":  float(d["calibrated_at_epoch"]),
                }
            logger.info(f"[AVM.DB] Loaded {len(result)} snapshots from DB: {list(result.keys())}")
            return result
        except Exception as e:
            logger.warning(f"[AVM.DB] Could not load snapshots: {e}")
            return {}

    def restore_to_json(self, snapshots_dir: str = "avm_snapshots") -> int:
        """
        Load all DB snapshots and write them to local JSON files
        so the core AVM module can read them.
        Returns count of restored snapshots.
        """
        import pathlib
        snapshots = self.load_all_snapshots()
        if not snapshots:
            return 0
        p = pathlib.Path(snapshots_dir)
        p.mkdir(parents=True, exist_ok=True)
        count = 0
        for domain, data in snapshots.items():
            safe = domain.replace("/", "_").replace(" ", "_").lower()
            path = p / f"{safe}_calibration.json"
            try:
                with open(path, "w") as f:
                    json.dump(data, f, indent=2)
                count += 1
            except Exception as e:
                logger.warning(f"[AVM.DB] Could not write JSON for domain={domain}: {e}")
        logger.info(f"[AVM.DB] Restored {count}/{len(snapshots)} snapshots to {snapshots_dir}/")
        return count

    def is_available(self) -> bool:
        return self._available
