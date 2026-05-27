"""
OMNIX Measurement & Monitoring Engine — Module 2 of 5 Governance Compliance Modules.

Aligns with:
- NIST AI RMF: MEASURE function (performance and risk measurement)
- ISO/IEC 42001: Clause 9.1 (Monitoring, measurement, analysis and evaluation)

ADR-029: Governance Compliance Modules
"""

import json
import logging
import math
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger("OMNIX.Governance.Measurement")

DRIFT_ALERT_THRESHOLD = 2.0
DRIFT_WARNING_THRESHOLD = 1.0


def _get_conn():
    return psycopg.connect(os.environ["DATABASE_URL"])


class MeasurementMonitoringEngine:
    """
    Signal drift detection and performance metrics time-series engine.

    Tracks approval/block rates per checkpoint, detects statistical drift
    between baseline and current signal distributions, and emits anomaly
    alerts when drift exceeds configurable thresholds.

    NIST AI RMF MEASURE: Quantifies AI risk impacts and tracks performance over time.
    ISO 42001 §9.1: Establishes what, how, and when to monitor/measure.
    """

    def record_metrics(
        self,
        client_id: str,
        checkpoint_id: str,
        approval_rate: float,
        block_rate: float,
        avg_score: float,
        window_start: datetime,
        window_end: datetime,
    ) -> dict[str, Any]:
        """Store a performance metrics snapshot for a checkpoint."""
        conn = _get_conn()
        try:
            cur = conn.cursor(row_factory=dict_row)
            cur.execute(
                """
                INSERT INTO governance_metrics
                    (client_id, checkpoint_id, approval_rate, block_rate, avg_score, window_start, window_end)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (client_id, checkpoint_id, approval_rate, block_rate, avg_score, window_start, window_end),
            )
            row = dict(cur.fetchone())
            conn.commit()
            for f in ("window_start", "window_end", "created_at"):
                if row.get(f):
                    row[f] = row[f].isoformat()
            row["id"] = str(row["id"])
            return row
        finally:
            conn.close()

    def detect_drift(
        self,
        client_id: str,
        signal_name: str,
        current_values: list[float],
        baseline_mean: float | None = None,
        baseline_std: float | None = None,
    ) -> dict[str, Any]:
        """
        Detect statistical drift in a signal compared to baseline.

        Drift score = |current_mean - baseline_mean| / baseline_std
        Alert levels:
          >= 2.0 → ALERT
          >= 1.0 → WARNING
          < 1.0  → OK
        """
        if not current_values:
            return {"error": "No values provided for drift detection"}

        n = len(current_values)
        current_mean = sum(current_values) / n
        current_std = math.sqrt(sum((x - current_mean) ** 2 for x in current_values) / max(n - 1, 1))

        if baseline_mean is None or baseline_std is None:
            baseline = self._get_baseline_from_db(client_id, signal_name)
            baseline_mean = baseline.get("mean", 50.0)
            baseline_std = baseline.get("std", 15.0)

        effective_std = baseline_std if baseline_std > 0 else 1.0
        drift_score = abs(current_mean - baseline_mean) / effective_std

        if drift_score >= DRIFT_ALERT_THRESHOLD:
            alert_level = "ALERT"
        elif drift_score >= DRIFT_WARNING_THRESHOLD:
            alert_level = "WARNING"
        else:
            alert_level = "OK"

        baseline_stats = {"mean": baseline_mean, "std": baseline_std}
        current_stats = {"mean": current_mean, "std": current_std, "n": n}

        conn = _get_conn()
        try:
            cur = conn.cursor(row_factory=dict_row)
            cur.execute(
                """
                INSERT INTO governance_drift_log
                    (client_id, signal_name, baseline_stats, current_stats, drift_score, threshold, alert_level)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    client_id, signal_name,
                    json.dumps(baseline_stats), json.dumps(current_stats),
                    drift_score, DRIFT_ALERT_THRESHOLD, alert_level,
                ),
            )
            row = dict(cur.fetchone())
            conn.commit()
            for f in ("detected_at", "created_at"):
                if row.get(f):
                    row[f] = row[f].isoformat()
            row["id"] = str(row["id"])
        finally:
            conn.close()

        if alert_level in ("ALERT", "WARNING"):
            logger.warning(
                f"[DRIFT] {alert_level} client={client_id} signal={signal_name} "
                f"drift={drift_score:.3f} baseline_mean={baseline_mean:.2f} current_mean={current_mean:.2f}"
            )

        return {
            "signal_name": signal_name,
            "drift_score": round(drift_score, 3),
            "alert_level": alert_level,
            "baseline_stats": baseline_stats,
            "current_stats": current_stats,
            "threshold_alert": DRIFT_ALERT_THRESHOLD,
            "threshold_warning": DRIFT_WARNING_THRESHOLD,
            "interpretation": (
                f"Signal '{signal_name}' has drifted {drift_score:.2f} standard deviations from baseline. "
                f"{'Immediate review recommended.' if alert_level == 'ALERT' else 'Monitor closely.' if alert_level == 'WARNING' else 'Within normal range.'}"
            ),
        }

    def _get_baseline_from_db(self, client_id: str, signal_name: str) -> dict:
        """Retrieve the most recent baseline stats for this signal from governance_metrics."""
        try:
            conn = _get_conn()
            cur = conn.cursor(row_factory=dict_row)
            cur.execute(
                """
                SELECT avg_score FROM governance_metrics
                WHERE client_id = %s AND checkpoint_id = %s
                ORDER BY created_at DESC LIMIT 30
                """,
                (client_id, signal_name),
            )
            rows = cur.fetchall()
            conn.close()
            if rows:
                vals = [float(r["avg_score"]) for r in rows if r["avg_score"] is not None]
                if vals:
                    mean = sum(vals) / len(vals)
                    std = math.sqrt(sum((v - mean) ** 2 for v in vals) / max(len(vals) - 1, 1))
                    return {"mean": mean, "std": max(std, 1.0)}
        except Exception as e:
            logger.debug(f"Baseline lookup failed for {signal_name}: {e}")
        return {"mean": 50.0, "std": 15.0}

    def get_metrics(self, client_id: str, days: int = 30) -> list[dict]:
        """Return performance metrics for the last N days, grouped by checkpoint."""
        conn = _get_conn()
        try:
            cur = conn.cursor(row_factory=dict_row)
            cur.execute(
                """
                SELECT checkpoint_id,
                       COUNT(*) as snapshots,
                       AVG(approval_rate) as avg_approval_rate,
                       AVG(block_rate) as avg_block_rate,
                       AVG(avg_score) as avg_score,
                       MIN(window_start) as earliest,
                       MAX(window_end) as latest
                FROM governance_metrics
                WHERE client_id = %s AND created_at >= NOW() - INTERVAL '%s days'
                GROUP BY checkpoint_id
                ORDER BY checkpoint_id
                """,
                (client_id, days),
            )
            rows = [dict(r) for r in cur.fetchall()]
            for row in rows:
                for f in ("earliest", "latest"):
                    if row.get(f):
                        row[f] = row[f].isoformat()
                for f in ("avg_approval_rate", "avg_block_rate", "avg_score"):
                    if row.get(f) is not None:
                        row[f] = float(row[f])
            return rows
        finally:
            conn.close()

    def get_drift_logs(self, client_id: str, alert_only: bool = False, limit: int = 50) -> list[dict]:
        """Return drift log entries, optionally filtered to ALERT/WARNING only."""
        conn = _get_conn()
        try:
            cur = conn.cursor(row_factory=dict_row)
            if alert_only:
                cur.execute(
                    """
                    SELECT * FROM governance_drift_log
                    WHERE client_id=%s AND alert_level IN ('ALERT','WARNING')
                    ORDER BY detected_at DESC LIMIT %s
                    """,
                    (client_id, limit),
                )
            else:
                cur.execute(
                    "SELECT * FROM governance_drift_log WHERE client_id=%s ORDER BY detected_at DESC LIMIT %s",
                    (client_id, limit),
                )
            rows = [dict(r) for r in cur.fetchall()]
            for row in rows:
                for f in ("detected_at", "created_at"):
                    if row.get(f):
                        row[f] = row[f].isoformat()
                row["id"] = str(row["id"])
            return rows
        finally:
            conn.close()

    def compute_checkpoint_stats(self, client_id: str, days: int = 30) -> dict[str, Any]:
        """
        Compute live approval/block stats per checkpoint from decision_receipts.
        Reads decision_receipts.veto_chain (array JSON) to determine which
        checkpoints fired. Does NOT modify any table.
        """
        conn = _get_conn()
        try:
            cur = conn.cursor(row_factory=dict_row)
            cur.execute(
                """
                SELECT decision, veto_chain, created_at
                FROM decision_receipts
                WHERE client_id = %s AND created_at >= NOW() - INTERVAL '%s days'
                ORDER BY created_at DESC
                """,
                (client_id, days),
            )
            rows = cur.fetchall()
            conn.close()

            total = len(rows)
            approved = sum(1 for r in rows if r["decision"] == "APPROVED")
            blocked = total - approved

            checkpoint_vetos: dict[str, int] = {}
            for row in rows:
                veto_chain = row.get("veto_chain")
                if isinstance(veto_chain, str):
                    try:
                        veto_chain = json.loads(veto_chain)
                    except Exception:
                        veto_chain = []
                if isinstance(veto_chain, list):
                    for veto in veto_chain:
                        cp = str(veto).split(":")[0] if ":" in str(veto) else str(veto)
                        checkpoint_vetos[cp] = checkpoint_vetos.get(cp, 0) + 1

            return {
                "client_id": client_id,
                "period_days": days,
                "total_evaluations": total,
                "approved": approved,
                "blocked": blocked,
                "approval_rate": round(approved / total * 100, 2) if total > 0 else None,
                "block_rate": round(blocked / total * 100, 2) if total > 0 else None,
                "checkpoint_veto_counts": checkpoint_vetos,
                "data_source": "decision_receipts (read-only, no modification)",
                "framework": "NIST AI RMF MEASURE — ISO 42001 §9.1",
            }
        except Exception as e:
            logger.error(f"compute_checkpoint_stats error: {e}")
            return {"error": str(e), "client_id": client_id}
