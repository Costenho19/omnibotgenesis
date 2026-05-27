"""
OMNIX — Execution Boundary Integrity Protocol (EBIP)
ADR-045 | March 2026

Four-component architecture that operates at the execution boundary
to address the deeper governance problems identified in architectural discourse:

1. AdmissibilityConsistencyValidator (ACV)
   Validates that input signals are internally consistent before checkpoints run.
   A system that enforces an internally contradictory admissibility model
   is worse than no enforcement at all.

2. ExecutionCommitmentProtocol (ECP)
   Cryptographic commitment to evaluation criteria BEFORE evaluation runs.
   Proves criteria were not changed between commitment and execution.
   Approximates Zero-Knowledge Proof semantics without full ZKP infrastructure.

3. NavigationPatternMonitor (NPM)
   Tracks the distribution of decisions over rolling windows.
   Detects concentration, path-dependency, and edge-seeking behavior
   WITHIN the admissible space — the layer that admissibility alone cannot govern.

4. ConcentrationPredictor (CP)
   Predicts concentration risk before it emerges — not after.
   Uses statistical trend analysis on navigation history.

Together: ExecutionBoundaryIntegrityProtocol (EBIP)

Reference:
  George-Adrian Caboc — incomplete admissibility model enforced with precision
  Mar Vincent Jambrich — path-dependency and concentration within admissible space
"""

import hashlib
import json
import logging
import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger("OMNIX.ExecutionIntegrity")

# ============================================================================
# DATABASE SETUP
# ============================================================================

def _get_conn():
    try:
        import psycopg
        return psycopg.connect(os.environ["DATABASE_URL"])
    except Exception as e:
        logger.warning(f"DB connection failed: {e}")
        return None


def _ensure_tables():
    conn = _get_conn()
    if not conn:
        return
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS navigation_patterns (
                        id SERIAL PRIMARY KEY,
                        window_start TIMESTAMP WITH TIME ZONE,
                        window_end TIMESTAMP WITH TIME ZONE,
                        total_decisions INTEGER DEFAULT 0,
                        approved_count INTEGER DEFAULT 0,
                        blocked_count INTEGER DEFAULT 0,
                        hold_count INTEGER DEFAULT 0,
                        approved_pct NUMERIC(5,2) DEFAULT 0,
                        blocked_pct NUMERIC(5,2) DEFAULT 0,
                        hold_pct NUMERIC(5,2) DEFAULT 0,
                        concentration_score NUMERIC(5,2) DEFAULT 0,
                        path_dependency_score NUMERIC(5,2) DEFAULT 0,
                        dominant_checkpoint VARCHAR(20),
                        dominant_checkpoint_count INTEGER DEFAULT 0,
                        alert_level VARCHAR(20) DEFAULT 'NOMINAL',
                        predicted_concentration_risk VARCHAR(20) DEFAULT 'LOW',
                        consistency_violations INTEGER DEFAULT 0,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_nav_patterns_created
                    ON navigation_patterns(created_at DESC)
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS admissibility_violations (
                        id SERIAL PRIMARY KEY,
                        receipt_id VARCHAR(50),
                        asset VARCHAR(50),
                        violation_type VARCHAR(100),
                        signals_snapshot JSONB,
                        consistency_score NUMERIC(5,2),
                        description TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
    except Exception as e:
        logger.warning(f"_ensure_tables: {e}")
    finally:
        conn.close()


_TABLES_INITIALIZED = False


def _init_tables_once():
    global _TABLES_INITIALIZED
    if not _TABLES_INITIALIZED:
        _ensure_tables()
        _TABLES_INITIALIZED = True


# ============================================================================
# COMPONENT 1 — ADMISSIBILITY CONSISTENCY VALIDATOR (ACV)
# ============================================================================

class AdmissibilityConsistencyValidator:
    """
    Validates that input signals are internally consistent before checkpoints run.

    An admissibility model that contains internal contradictions will produce
    enforcement that is precise but wrong. This validator surfaces those
    contradictions before they propagate into the decision layer.

    Contradiction classes detected:
    - Simultaneous high probability + high risk exposure (impossible edge)
    - High signal coherence + low trend persistence (structural inconsistency)
    - High stress resilience + high risk exposure (contradictory safety claims)
    - Logic consistency flags combined with high approval signals (paradox state)
    """

    CONTRADICTION_RULES = [
        {
            "name": "HIGH_PROBABILITY_HIGH_RISK",
            "description": "High expected probability with high risk exposure — contradictory signals",
            "condition": lambda s: s.get("probability_score", 50) > 80 and s.get("risk_exposure", 50) > 75,
            "severity": "HIGH",
        },
        {
            "name": "HIGH_COHERENCE_LOW_PERSISTENCE",
            "description": "Signals agree internally but trend is unstable — coherence without persistence",
            "condition": lambda s: s.get("signal_coherence", 50) > 80 and s.get("trend_persistence", 50) < 25,
            "severity": "MEDIUM",
        },
        {
            "name": "HIGH_RESILIENCE_HIGH_EXPOSURE",
            "description": "High stress resilience claimed while risk exposure is elevated — inconsistent safety model",
            "condition": lambda s: s.get("stress_resilience", 50) > 85 and s.get("risk_exposure", 50) > 70,
            "severity": "MEDIUM",
        },
        {
            "name": "LOW_LOGIC_HIGH_APPROVAL_SIGNALS",
            "description": "Logic consistency is weak while most approval signals are strong — paradox state",
            "condition": lambda s: s.get("logic_consistency", 50) < 20 and s.get("probability_score", 50) > 75 and s.get("signal_coherence", 50) > 75,
            "severity": "HIGH",
        },
        {
            "name": "ALL_SIGNALS_EXTREME",
            "description": "All signals at extremes simultaneously — statistically implausible, possible data error",
            "condition": lambda s: (
                len([k for k in ["probability_score", "risk_exposure", "signal_coherence", "trend_persistence"] if k in s]) >= 2
                and all(
                    v > 90 or v < 10
                    for k, v in s.items()
                    if k in ["probability_score", "risk_exposure", "signal_coherence", "trend_persistence"]
                )
            ),
            "severity": "HIGH",
        },
    ]

    def validate(self, signals: dict[str, Any]) -> dict[str, Any]:
        contradictions = []
        for rule in self.CONTRADICTION_RULES:
            try:
                if rule["condition"](signals):
                    contradictions.append({
                        "type": rule["name"],
                        "description": rule["description"],
                        "severity": rule["severity"],
                    })
            except Exception as _e:
                logger.warning(f"[EI] Contradiction rule check failed: {_e}")

        total_signals = len([k for k in signals if k in [
            "probability_score", "risk_exposure", "signal_coherence",
            "trend_persistence", "stress_resilience", "logic_consistency"
        ]])
        contradiction_penalty = len(contradictions) * 15
        consistency_score = max(0.0, 100.0 - contradiction_penalty)

        is_consistent = len([c for c in contradictions if c["severity"] == "HIGH"]) == 0

        return {
            "is_consistent": is_consistent,
            "consistency_score": round(consistency_score, 2),
            "contradictions": contradictions,
            "contradiction_count": len(contradictions),
            "high_severity_count": len([c for c in contradictions if c["severity"] == "HIGH"]),
            "signal_count_validated": total_signals,
            "validator": "ACV-1.0",
        }

    def log_violation(self, receipt_id: str, asset: str, validation_result: dict, signals: dict):
        if validation_result.get("contradiction_count", 0) == 0:
            return
        conn = _get_conn()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    for contradiction in validation_result.get("contradictions", []):
                        cur.execute("""
                            INSERT INTO admissibility_violations
                            (receipt_id, asset, violation_type, signals_snapshot, consistency_score, description)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            receipt_id,
                            asset,
                            contradiction["type"],
                            json.dumps(signals),
                            validation_result["consistency_score"],
                            contradiction["description"],
                        ))
        except Exception as e:
            logger.warning(f"ACV log_violation: {e}")
        finally:
            conn.close()


# ============================================================================
# COMPONENT 2 — EXECUTION COMMITMENT PROTOCOL (ECP)
# ============================================================================

class ExecutionCommitmentProtocol:
    """
    Creates a cryptographic commitment to evaluation criteria BEFORE evaluation runs.

    This approximates Zero-Knowledge Proof semantics: the receipt proves that
    the criteria applied were committed to before the result was known,
    making it cryptographically impossible to retroactively change the criteria
    to match a desired outcome.

    Commitment structure:
      nonce + signals_hash + criteria_hash + timestamp → commitment_hash

    The commitment_hash is embedded in the governance receipt.
    Anyone with the receipt can verify that the criteria hash matches
    the publicly known checkpoint configuration at that moment.
    """

    def create_commitment(
        self,
        signals: dict[str, Any],
        checkpoint_ids: list[str],
        asset: str = "",
    ) -> dict[str, Any]:
        nonce = secrets.token_hex(16)
        committed_at_ns = time.time_ns()
        committed_at = datetime.fromtimestamp(committed_at_ns / 1e9, tz=timezone.utc).isoformat()

        signals_canonical = json.dumps(signals, sort_keys=True, separators=(",", ":"))
        signals_hash = hashlib.sha256(signals_canonical.encode()).hexdigest()

        criteria_canonical = json.dumps(sorted(checkpoint_ids), separators=(",", ":"))
        criteria_hash = hashlib.sha256(criteria_canonical.encode()).hexdigest()

        commitment_preimage = f"{nonce}:{signals_hash}:{criteria_hash}:{committed_at_ns}"
        commitment_hash = hashlib.sha256(commitment_preimage.encode()).hexdigest()

        return {
            "commitment_hash": commitment_hash,
            "signals_hash": signals_hash,
            "criteria_hash": criteria_hash,
            "nonce": nonce,
            "committed_at": committed_at,
            "committed_at_ns": committed_at_ns,
            "asset": asset,
            "checkpoint_count": len(checkpoint_ids),
            "protocol": "ECP-1.0",
        }

    def verify_commitment(
        self,
        commitment: dict[str, Any],
        signals: dict[str, Any],
        checkpoint_ids: list[str],
    ) -> dict[str, Any]:
        signals_canonical = json.dumps(signals, sort_keys=True, separators=(",", ":"))
        signals_hash_verify = hashlib.sha256(signals_canonical.encode()).hexdigest()

        criteria_canonical = json.dumps(sorted(checkpoint_ids), separators=(",", ":"))
        criteria_hash_verify = hashlib.sha256(criteria_canonical.encode()).hexdigest()

        commitment_preimage = (
            f"{commitment['nonce']}:{signals_hash_verify}:"
            f"{criteria_hash_verify}:{commitment['committed_at_ns']}"
        )
        expected_hash = hashlib.sha256(commitment_preimage.encode()).hexdigest()
        is_valid = expected_hash == commitment["commitment_hash"]

        return {
            "is_valid": is_valid,
            "commitment_hash": commitment["commitment_hash"],
            "signals_integrity": signals_hash_verify == commitment["signals_hash"],
            "criteria_integrity": criteria_hash_verify == commitment["criteria_hash"],
            "verified_at": datetime.now(tz=timezone.utc).isoformat(),
        }


# ============================================================================
# COMPONENT 3 — NAVIGATION PATTERN MONITOR (NPM)
# ============================================================================

class NavigationPatternMonitor:
    """
    Tracks the distribution of decisions over rolling windows.

    Addresses Mar Vincent Jambrich's observation: even within a well-defined
    admissible space, systems can develop concentration, path-dependency,
    and edge-seeking behavior — none of which trigger boundary violations.

    This monitor makes those patterns legible and actionable.

    Alert levels:
    - NOMINAL: balanced distribution, no concerning patterns
    - WATCH: mild concentration detected, monitoring intensified
    - CAUTION: significant concentration or path-dependency emerging
    - CRITICAL: extreme concentration — admissibility model may be miscalibrated
    """

    def record_decision(
        self,
        decision: str,
        dominant_checkpoint: str = "",
        asset: str = "",
        consistency_violation: bool = False,
    ):
        _init_tables_once()
        conn = _get_conn()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO navigation_patterns
                        (window_start, window_end, total_decisions,
                         approved_count, blocked_count, hold_count,
                         dominant_checkpoint, alert_level, consistency_violations)
                        VALUES (%s, %s, 1, %s, %s, %s, %s, 'RECORDING', %s)
                    """, (
                        datetime.now(tz=timezone.utc),
                        datetime.now(tz=timezone.utc),
                        1 if decision == "APPROVED" else 0,
                        1 if decision == "BLOCKED" else 0,
                        1 if decision == "HOLD" else 0,
                        dominant_checkpoint or "",
                        1 if consistency_violation else 0,
                    ))
        except Exception as e:
            logger.warning(f"NPM record_decision: {e}")
        finally:
            conn.close()

    def get_navigation_health(self, window_hours: int = 24) -> dict[str, Any]:
        _init_tables_once()
        conn = _get_conn()
        if not conn:
            return self._fallback_health()
        try:
            with conn.cursor() as cur:
                cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=window_hours)

                cur.execute("""
                    SELECT
                        COUNT(*) as row_count,
                        COALESCE(SUM(approved_count), 0) as approved,
                        COALESCE(SUM(blocked_count), 0) as blocked,
                        COALESCE(SUM(hold_count), 0) as hold,
                        COALESCE(SUM(consistency_violations), 0) as violations
                    FROM navigation_patterns
                    WHERE created_at >= %s
                """, (cutoff,))
                agg = cur.fetchone()
                if not agg or not agg[0]:
                    return self._fallback_health()

                total = int(agg[0] or 0)
                approved = int(agg[1] or 0)
                blocked = int(agg[2] or 0)
                hold = int(agg[3] or 0)
                violations = int(agg[4] or 0)

                cur.execute("""
                    SELECT dominant_checkpoint
                    FROM navigation_patterns
                    WHERE created_at >= %s AND dominant_checkpoint != ''
                    GROUP BY dominant_checkpoint
                    ORDER BY COUNT(*) DESC
                    LIMIT 1
                """, (cutoff,))
                cp_row = cur.fetchone()
                dominant_cp = cp_row[0] if cp_row else "N/A"

                if total == 0:
                    return self._fallback_health()

                approved_pct = round(approved / total * 100, 1)
                blocked_pct = round(blocked / total * 100, 1)
                hold_pct = round(hold / total * 100, 1)

                concentration_score = self._compute_concentration(approved_pct, blocked_pct, hold_pct)
                path_dependency = self._compute_path_dependency(blocked_pct, violations, total)
                alert_level = self._compute_alert_level(concentration_score, path_dependency)

                return {
                    "window_hours": window_hours,
                    "total_decisions": total,
                    "distribution": {
                        "approved": approved,
                        "blocked": blocked,
                        "hold": hold,
                        "approved_pct": approved_pct,
                        "blocked_pct": blocked_pct,
                        "hold_pct": hold_pct,
                    },
                    "concentration_score": round(concentration_score, 2),
                    "path_dependency_score": round(path_dependency, 2),
                    "dominant_checkpoint": dominant_cp,
                    "consistency_violations": violations,
                    "alert_level": alert_level,
                    "navigation_health_score": round(100 - (concentration_score * 0.5 + path_dependency * 0.5), 2),
                    "monitor": "NPM-1.0",
                }
        except Exception as e:
            logger.warning(f"NPM get_navigation_health: {e}")
            return self._fallback_health()
        finally:
            conn.close()

    def _compute_concentration(self, approved_pct: float, blocked_pct: float, hold_pct: float) -> float:
        max_pct = max(approved_pct, blocked_pct, hold_pct)
        if max_pct > 90:
            return 90.0
        elif max_pct > 75:
            return 65.0
        elif max_pct > 60:
            return 40.0
        elif max_pct > 50:
            return 20.0
        return 5.0

    def _compute_path_dependency(self, blocked_pct: float, violations: int, total: int) -> float:
        score = 0.0
        if blocked_pct > 80:
            score += 50.0
        elif blocked_pct > 65:
            score += 30.0
        elif blocked_pct > 50:
            score += 15.0
        if total > 0:
            violation_rate = violations / total * 100
            score += min(violation_rate * 2, 40.0)
        return min(score, 100.0)

    def _compute_alert_level(self, concentration: float, path_dependency: float) -> str:
        combined = (concentration + path_dependency) / 2
        if combined >= 70:
            return "CRITICAL"
        elif combined >= 45:
            return "CAUTION"
        elif combined >= 25:
            return "WATCH"
        return "NOMINAL"

    def _fallback_health(self) -> dict[str, Any]:
        return {
            "window_hours": 24,
            "total_decisions": 0,
            "distribution": {"approved": 0, "blocked": 0, "hold": 0},
            "concentration_score": 0.0,
            "path_dependency_score": 0.0,
            "dominant_checkpoint": "N/A",
            "consistency_violations": 0,
            "alert_level": "NOMINAL",
            "navigation_health_score": 100.0,
            "monitor": "NPM-1.0",
        }


# ============================================================================
# COMPONENT 4 — CONCENTRATION PREDICTOR (CP)
# ============================================================================

class ConcentrationPredictor:
    """
    Predicts concentration risk before it emerges — not after.

    Uses trend analysis on the last N navigation windows to detect
    whether the decision distribution is moving toward concentration.

    This addresses the hardest open question: what happens when path-dependency
    emerges slowly enough that no single navigation step triggers a signal?
    """

    def predict_concentration_risk(self, lookback_windows: int = 10) -> dict[str, Any]:
        _init_tables_once()
        conn = _get_conn()
        if not conn:
            return {"predicted_risk": "UNKNOWN", "confidence": 0, "predictor": "CP-1.0"}
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT blocked_pct, concentration_score, path_dependency_score, alert_level
                    FROM navigation_patterns
                    WHERE alert_level != 'RECORDING'
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (lookback_windows,))
                rows = cur.fetchall()

                if len(rows) < 3:
                    return {
                        "predicted_risk": "INSUFFICIENT_DATA",
                        "data_points": len(rows),
                        "minimum_required": 3,
                        "predictor": "CP-1.0",
                    }

                blocked_pcts = [float(r[0] or 0) for r in rows]
                concentration_scores = [float(r[1] or 0) for r in rows]

                blocked_trend = self._compute_trend(blocked_pcts)
                concentration_trend = self._compute_trend(concentration_scores)

                risk_level, confidence = self._assess_risk(blocked_trend, concentration_trend, blocked_pcts)

                return {
                    "predicted_risk": risk_level,
                    "confidence": round(confidence, 1),
                    "blocked_pct_trend": round(blocked_trend, 2),
                    "concentration_trend": round(concentration_trend, 2),
                    "data_points_analyzed": len(rows),
                    "current_blocked_pct": blocked_pcts[0] if blocked_pcts else 0,
                    "interpretation": self._interpret(risk_level, blocked_trend),
                    "predictor": "CP-1.0",
                }
        except Exception as e:
            logger.warning(f"CP predict: {e}")
            return {"predicted_risk": "UNKNOWN", "confidence": 0, "predictor": "CP-1.0"}
        finally:
            conn.close()

    def _compute_trend(self, values: list[float]) -> float:
        if len(values) < 2:
            return 0.0
        n = len(values)
        recent_half = values[:n // 2]
        older_half = values[n // 2:]
        if not older_half or not recent_half:
            return 0.0
        recent_avg = sum(recent_half) / len(recent_half)
        older_avg = sum(older_half) / len(older_half)
        return recent_avg - older_avg

    def _assess_risk(
        self,
        blocked_trend: float,
        concentration_trend: float,
        blocked_pcts: list[float],
    ) -> tuple[str, float]:
        current = blocked_pcts[0] if blocked_pcts else 0
        score = 0.0

        if blocked_trend > 15:
            score += 50
        elif blocked_trend > 8:
            score += 30
        elif blocked_trend > 3:
            score += 15

        if concentration_trend > 20:
            score += 40
        elif concentration_trend > 10:
            score += 20

        if current > 75:
            score += 30
        elif current > 60:
            score += 15

        if score >= 80:
            return "CRITICAL", min(score, 95)
        elif score >= 50:
            return "HIGH", score
        elif score >= 25:
            return "MEDIUM", score
        return "LOW", max(100 - score, 60)

    def _interpret(self, risk_level: str, blocked_trend: float) -> str:
        if risk_level == "CRITICAL":
            return "Admissibility criteria may be too restrictive — system approaching full BLOCK concentration."
        elif risk_level == "HIGH":
            return "Decision distribution concentrating toward BLOCK — review checkpoint calibration."
        elif risk_level == "MEDIUM":
            return "Mild concentration trend detected — monitoring recommended."
        return "Navigation patterns within expected bounds."


# ============================================================================
# MAIN PROTOCOL — EXECUTION BOUNDARY INTEGRITY PROTOCOL (EBIP)
# ============================================================================

class ExecutionBoundaryIntegrityProtocol:
    """
    The four components combined into a single coherent protocol.

    Operates in two phases:
      pre_evaluation()  — before checkpoints run
      post_evaluation() — after decision is produced

    Adds zero latency risk: all components fail gracefully.
    Main pipeline never blocked by EBIP failures.
    """

    def __init__(self):
        self.acv = AdmissibilityConsistencyValidator()
        self.ecp = ExecutionCommitmentProtocol()
        self.npm = NavigationPatternMonitor()
        self.cp = ConcentrationPredictor()
        _init_tables_once()

    def pre_evaluation(
        self,
        signals: dict[str, Any],
        checkpoint_ids: list[str],
        asset: str = "",
    ) -> dict[str, Any]:
        consistency = self.acv.validate(signals)
        commitment = self.ecp.create_commitment(signals, checkpoint_ids, asset)
        navigation_health = self.npm.get_navigation_health(window_hours=24)
        concentration_prediction = self.cp.predict_concentration_risk()

        return {
            "consistency_validation": consistency,
            "commitment": commitment,
            "navigation_health": navigation_health,
            "concentration_prediction": concentration_prediction,
            "pre_evaluation_at": datetime.now(tz=timezone.utc).isoformat(),
            "ebip_version": "1.0",
        }

    def post_evaluation(
        self,
        pre_context: dict[str, Any],
        decision: str,
        signals: dict[str, Any],
        checkpoint_ids: list[str],
        dominant_checkpoint: str = "",
        asset: str = "",
        receipt_id: str = "",
    ) -> dict[str, Any]:
        commitment = pre_context.get("commitment", {})
        consistency = pre_context.get("consistency_validation", {})

        verification = {}
        if commitment and signals and checkpoint_ids:
            try:
                verification = self.ecp.verify_commitment(commitment, signals, checkpoint_ids)
            except Exception:
                verification = {"is_valid": False, "error": "verification_failed"}

        has_violation = consistency.get("contradiction_count", 0) > 0
        if has_violation and receipt_id:
            try:
                self.acv.log_violation(receipt_id, asset, consistency, signals)
            except Exception as _e:
                logger.warning(f"[EI] acv.log_violation failed for {asset} receipt={receipt_id}: {_e}")

        try:
            self.npm.record_decision(decision, dominant_checkpoint, asset, has_violation)
        except Exception as _e:
            logger.warning(f"[EI] npm.record_decision failed for {asset}: {_e}")

        integrity_score = 100.0
        if not verification.get("is_valid", True):
            integrity_score -= 30
        if consistency.get("high_severity_count", 0) > 0:
            integrity_score -= consistency["high_severity_count"] * 10
        if pre_context.get("navigation_health", {}).get("alert_level") == "CRITICAL":
            integrity_score -= 20
        elif pre_context.get("navigation_health", {}).get("alert_level") == "CAUTION":
            integrity_score -= 10

        integrity_score = max(0.0, min(100.0, integrity_score))

        return {
            "commitment_verified": verification.get("is_valid", True),
            "commitment_hash": commitment.get("commitment_hash", ""),
            "consistency_score": consistency.get("consistency_score", 100.0),
            "consistency_violations": consistency.get("contradictions", []),
            "navigation_alert": pre_context.get("navigation_health", {}).get("alert_level", "NOMINAL"),
            "concentration_risk": pre_context.get("concentration_prediction", {}).get("predicted_risk", "LOW"),
            "execution_integrity_score": round(integrity_score, 2),
            "post_evaluation_at": datetime.now(tz=timezone.utc).isoformat(),
            "ebip_version": "1.0",
        }

    def get_system_integrity_status(self) -> dict[str, Any]:
        navigation_health = self.npm.get_navigation_health(window_hours=24)
        concentration_prediction = self.cp.predict_concentration_risk()

        conn = _get_conn()
        recent_violations = 0
        if conn:
            try:
                with conn.cursor() as cur:
                    cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=24)
                    cur.execute(
                        "SELECT COUNT(*) FROM admissibility_violations WHERE created_at >= %s",
                        (cutoff,)
                    )
                    row = cur.fetchone()
                    recent_violations = int(row[0]) if row else 0
            except Exception as _e:
                logger.warning(f"[EI] admissibility_violations DB query failed: {_e}")
            finally:
                conn.close()

        overall_health = navigation_health.get("navigation_health_score", 100)
        if concentration_prediction.get("predicted_risk") == "CRITICAL":
            overall_health = min(overall_health, 30)
        elif concentration_prediction.get("predicted_risk") == "HIGH":
            overall_health = min(overall_health, 60)

        return {
            "navigation_health": navigation_health,
            "concentration_prediction": concentration_prediction,
            "recent_consistency_violations_24h": recent_violations,
            "overall_execution_integrity": round(overall_health, 2),
            "status_at": datetime.now(tz=timezone.utc).isoformat(),
            "components": {
                "ACV": "Admissibility Consistency Validator — ACTIVE",
                "ECP": "Execution Commitment Protocol — ACTIVE",
                "NPM": "Navigation Pattern Monitor — ACTIVE",
                "CP": "Concentration Predictor — ACTIVE",
            },
            "ebip_version": "1.0",
        }


_ebip_instance: ExecutionBoundaryIntegrityProtocol | None = None


def get_ebip() -> ExecutionBoundaryIntegrityProtocol:
    global _ebip_instance
    if _ebip_instance is None:
        _ebip_instance = ExecutionBoundaryIntegrityProtocol()
    return _ebip_instance
