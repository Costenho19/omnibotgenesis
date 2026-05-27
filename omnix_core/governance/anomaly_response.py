"""
ADR-129 — Phase 5: Anomaly Response Layer

Controlled recommendation engine that converts CalibrationInsightEngine anomalies
(ADR-128) into traceable, reversible, non-destructive governance recommendations.

Design Principles
─────────────────
1. RECOMMENDATION-FIRST: Every output is a recommendation, never a forced action.
   No governance layer is bypassed. No decision is overridden automatically.
2. REVERSIBLE: All recommendations carry a lifecycle (ACTIVE → ACKNOWLEDGED →
   RESOLVED | EXPIRED). Any recommendation can be closed without side effects.
3. TRACEABLE: Every recommendation is persisted to `anomaly_recommendations`
   with full audit fields (who acknowledged, when resolved, resolution note).
4. NON-DESTRUCTIVE: The response engine has no write path to governance tables,
   AVM models, or the decision receipt system.

Anomaly → Action Mapping
─────────────────────────
BLOCK_RATE_DROP   → SUSPEND_RECALIBRATION
    The coherence gate block rate dropped below baseline. Automated threshold
    recalibration should be paused until root cause is identified and block
    rate recovers.

DCI_SURGE         → REDUCE_POSITION_SIZING
    Decision Contradiction Index surged in the last hour. Recommend reducing
    maximum position sizing limits (advisory) to limit exposure during the
    high-contradiction window.

HOLD_SPIKE        → FLAG_OPERATIONAL_ALERT
    The hold rate spiked across gates — manual review queue may be saturated.
    Operations team should be flagged to increase review capacity or reassess
    auto-approve thresholds for low-risk decisions.

COHERENCE_DRIFT   → TRIGGER_AVM_REVIEW
    Internal signal agreement has drifted significantly. The AVM model weights
    or upstream data feeds for the affected domain should be reviewed.

BS_HIGH_SURGE     → MONITOR_BS_LEVELS
    Black Swan HIGH events surged in the last hour. Risk monitoring frequency
    should increase; alert the risk committee if rate exceeds 20% within 1h.

ESCALATION_SURGE  → ESCALATION_REVIEW
    ADR-119 escalation (BS_HIGH_COHERENCE_ESCALATION) events surged. Review
    coherence threshold configuration to determine if a recalibration is safe.

Usage
─────
    from omnix_core.governance.anomaly_response import AnomalyResponseEngine
    from omnix_core.governance.calibration_insight import CalibrationInsightEngine

    engine   = AnomalyResponseEngine()
    response = engine.full_response_cycle(domain="trading")

    # response = {
    #   "domain":           "trading",
    #   "anomalies":        { ... CalibrationInsightEngine.detect_anomalies() },
    #   "recommendations":  [ { action_code, severity, urgency, status, ... } ],
    #   "new_logged":       int,
    #   "active_count":     int,
    #   "generated_at":     str,
    # }
"""

import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("OMNIX.AnomalyResponse")

_TABLE = "anomaly_recommendations"

# ── Status constants ──────────────────────────────────────────────────────────
STATUS_ACTIVE       = "ACTIVE"
STATUS_ACKNOWLEDGED = "ACKNOWLEDGED"
STATUS_RESOLVED     = "RESOLVED"
STATUS_EXPIRED      = "EXPIRED"

_VALID_STATUSES = {STATUS_ACTIVE, STATUS_ACKNOWLEDGED, STATUS_RESOLVED, STATUS_EXPIRED}

# ── Urgency levels ────────────────────────────────────────────────────────────
URGENCY_IMMEDIATE  = "IMMEDIATE"   # CRITICAL anomaly — respond within 15 min
URGENCY_URGENT     = "URGENT"      # HIGH anomaly — respond within 1h
URGENCY_ELEVATED   = "ELEVATED"    # MEDIUM anomaly — respond within 4h
URGENCY_MONITORING = "MONITORING"  # LOW anomaly — respond within 24h

_SEVERITY_TO_URGENCY: Dict[str, str] = {
    "CRITICAL": URGENCY_IMMEDIATE,
    "HIGH":     URGENCY_URGENT,
    "MEDIUM":   URGENCY_ELEVATED,
    "LOW":      URGENCY_MONITORING,
}

# ── Action codes ──────────────────────────────────────────────────────────────
ACTION_SUSPEND_RECALIBRATION = "SUSPEND_RECALIBRATION"
ACTION_REDUCE_POSITION_SIZING = "REDUCE_POSITION_SIZING"
ACTION_FLAG_OPERATIONAL_ALERT = "FLAG_OPERATIONAL_ALERT"
ACTION_TRIGGER_AVM_REVIEW    = "TRIGGER_AVM_REVIEW"
ACTION_MONITOR_BS_LEVELS     = "MONITOR_BS_LEVELS"
ACTION_ESCALATION_REVIEW     = "ESCALATION_REVIEW"

# ── Default expiry window ─────────────────────────────────────────────────────
_DEFAULT_EXPIRY_HOURS = 24


# ── Anomaly → recommendation specification ───────────────────────────────────

@dataclass
class _ActionSpec:
    action_code:         str
    action_description:  str
    rationale:           str
    is_reversible:       bool = True


_ANOMALY_ACTION_MAP: Dict[str, _ActionSpec] = {
    "BLOCK_RATE_DROP": _ActionSpec(
        action_code        = ACTION_SUSPEND_RECALIBRATION,
        action_description = (
            "Suspend automated coherence gate threshold recalibration. "
            "Manual review required before resuming — block rate must recover to "
            "within 5pp of the 1d baseline before recalibration is safe."
        ),
        rationale = (
            "A sudden drop in block_rate may indicate filter weakening, upstream "
            "data quality degradation, or a misconfigured recalibration cycle. "
            "Suspending recalibration preserves the current thresholds and prevents "
            "a feedback loop that could further reduce blocking capacity."
        ),
        is_reversible = True,
    ),
    "DCI_SURGE": _ActionSpec(
        action_code        = ACTION_REDUCE_POSITION_SIZING,
        action_description = (
            "Recommend reducing maximum position sizing limits by 25% for the "
            "affected domain until DCI returns to TENSIONED or ALIGNED band "
            "(avg DCI < 70). No existing positions are affected — this applies "
            "to new decisions only."
        ),
        rationale = (
            "A DCI surge indicates high internal contradiction between governance "
            "signals. Operating with full position sizing during contradictory "
            "conditions amplifies risk. A 25% reduction is conservative, reversible, "
            "and limits exposure without halting operations."
        ),
        is_reversible = True,
    ),
    "HOLD_SPIKE": _ActionSpec(
        action_code        = ACTION_FLAG_OPERATIONAL_ALERT,
        action_description = (
            "Flag operational alert: HOLD queue is spiking. Recommended actions — "
            "(1) alert operations team to increase manual review capacity; "
            "(2) assess whether auto-approve thresholds can be temporarily widened "
            "for decisions with coherence_score > 80 and DCI < 35."
        ),
        rationale = (
            "A HOLD spike means decisions are queuing for manual review faster than "
            "they are being processed. Sustained hold saturation degrades decision "
            "throughput and may cause SLA violations. The flag is advisory — no "
            "thresholds are changed automatically."
        ),
        is_reversible = True,
    ),
    "COHERENCE_DRIFT": _ActionSpec(
        action_code        = ACTION_TRIGGER_AVM_REVIEW,
        action_description = (
            "Trigger AVM (Autonomous Valuation Model) review for the affected domain. "
            "Review checklist: (1) verify upstream data feed freshness; "
            "(2) check model weight staleness (>72h triggers auto-recalib per ADR-120); "
            "(3) confirm domain signals are within expected range bounds."
        ),
        rationale = (
            "Coherence drift — whether upward or downward — signals a shift in how "
            "aligned the input signals are. This may indicate stale model weights, "
            "changed market conditions, or a data quality issue. AVM review is the "
            "lowest-risk first response before any threshold adjustments."
        ),
        is_reversible = True,
    ),
    "BS_HIGH_SURGE": _ActionSpec(
        action_code        = ACTION_MONITOR_BS_LEVELS,
        action_description = (
            "Escalate Black Swan monitoring frequency to 15-minute intervals. "
            "Alert the risk committee if BS_HIGH rate exceeds 20% within any "
            "subsequent 1h window. No automated position changes until manual "
            "risk committee review is completed."
        ),
        rationale = (
            "A surge in BS_HIGH events indicates elevated systemic risk in the "
            "current window. Heightened monitoring allows early detection of a "
            "sustained BS_HIGH period vs. a transient spike. Manual review prevents "
            "overreaction to short-duration noise."
        ),
        is_reversible = True,
    ),
    "ESCALATION_SURGE": _ActionSpec(
        action_code        = ACTION_ESCALATION_REVIEW,
        action_description = (
            "Review ADR-119 escalation configuration for the affected domain. "
            "Determine if the current coherence threshold under BS_HIGH conditions "
            "is appropriately calibrated. Document findings in the governance log "
            "before any threshold changes are approved."
        ),
        rationale = (
            "A surge in BS_HIGH_COHERENCE_ESCALATION events may indicate the "
            "escalation trigger is too sensitive, or that genuine systemic stress "
            "is occurring. Review determines which case applies and what — if any — "
            "recalibration is warranted. No recalibration proceeds without operator approval."
        ),
        is_reversible = True,
    ),
}


# ── Recommendation dataclass ──────────────────────────────────────────────────

@dataclass
class AnomalyRecommendation:
    """
    A single governance recommendation generated from a detected anomaly.

    All fields are immutable after creation except status lifecycle fields
    (acknowledged_at/by, resolved_at/note) which are updated via DB calls.
    """
    id:                  str              # UUID v4
    anomaly_type:        str
    severity:            str
    urgency:             str
    domain:              Optional[str]
    action_code:         str
    action_description:  str
    rationale:           str
    is_reversible:       bool
    status:              str              = STATUS_ACTIVE
    created_at:          str             = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    anomaly_detected_at: Optional[str]   = None
    expires_at:          Optional[str]   = None
    acknowledged_at:     Optional[str]   = None
    acknowledged_by:     Optional[str]   = None
    resolved_at:         Optional[str]   = None
    resolved_note:       Optional[str]   = None
    auto_generated:      bool            = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id":                  self.id,
            "anomaly_type":        self.anomaly_type,
            "severity":            self.severity,
            "urgency":             self.urgency,
            "domain":              self.domain,
            "action_code":         self.action_code,
            "action_description":  self.action_description,
            "rationale":           self.rationale,
            "is_reversible":       self.is_reversible,
            "status":              self.status,
            "created_at":          self.created_at,
            "anomaly_detected_at": self.anomaly_detected_at,
            "expires_at":          self.expires_at,
            "acknowledged_at":     self.acknowledged_at,
            "acknowledged_by":     self.acknowledged_by,
            "resolved_at":         self.resolved_at,
            "resolved_note":       self.resolved_note,
            "auto_generated":      self.auto_generated,
        }


# ── Schema ────────────────────────────────────────────────────────────────────

_CREATE_TABLE = f"""
CREATE TABLE IF NOT EXISTS {_TABLE} (
    id                   VARCHAR(36)   PRIMARY KEY,
    created_at           TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    anomaly_type         VARCHAR(50)   NOT NULL,
    severity             VARCHAR(20)   NOT NULL,
    urgency              VARCHAR(20)   NOT NULL DEFAULT 'ELEVATED',
    domain               VARCHAR(50),
    action_code          VARCHAR(50)   NOT NULL,
    action_description   TEXT          NOT NULL,
    rationale            TEXT          NOT NULL,
    is_reversible        BOOLEAN       NOT NULL DEFAULT TRUE,
    status               VARCHAR(20)   NOT NULL DEFAULT 'ACTIVE',
    anomaly_detected_at  TIMESTAMPTZ,
    expires_at           TIMESTAMPTZ,
    acknowledged_at      TIMESTAMPTZ,
    acknowledged_by      VARCHAR(100),
    resolved_at          TIMESTAMPTZ,
    resolved_note        TEXT,
    auto_generated       BOOLEAN       NOT NULL DEFAULT TRUE
)
"""

_CREATE_INDEXES = [
    f"CREATE INDEX IF NOT EXISTS idx_ar_domain_status   ON {_TABLE}(domain, status, created_at DESC)",
    f"CREATE INDEX IF NOT EXISTS idx_ar_status_ts       ON {_TABLE}(status, created_at DESC)",
    f"CREATE INDEX IF NOT EXISTS idx_ar_anomaly_type    ON {_TABLE}(anomaly_type, created_at DESC)",
    f"CREATE INDEX IF NOT EXISTS idx_ar_expires         ON {_TABLE}(expires_at) WHERE status = 'ACTIVE'",
]


# ── DB helpers ────────────────────────────────────────────────────────────────

def _get_db_conn(db_url: str):
    import psycopg
    return psycopg.connect(db_url, connect_timeout=10)


def _maybe_connect(db_url: Optional[str], conn):
    """Return (own_conn, conn). Raises RuntimeError if no URL and no conn."""
    if conn is not None:
        return False, conn
    if not db_url:
        raise RuntimeError("[AR] No DB URL configured")
    return True, _get_db_conn(db_url)


def _close_if_own(own_conn: bool, conn) -> None:
    if own_conn:
        try:
            conn.close()
        except Exception:
            pass


# ── Main engine ───────────────────────────────────────────────────────────────

class AnomalyResponseEngine:
    """
    Controlled recommendation engine for governance anomalies.

    Takes the output of CalibrationInsightEngine.detect_anomalies() and:
    1. Generates structured recommendations (in-memory, no DB).
    2. Persists recommendations to `anomaly_recommendations`.
    3. Manages the recommendation lifecycle (ACTIVE → ACKNOWLEDGED → RESOLVED).
    4. Provides audit history queries.

    All responses are RECOMMENDATIONS only. Nothing is executed automatically.
    Governance decisions, AVM models, and gate thresholds are never modified.

    Thread-safe: concurrent calls serialize at the DB connection level only.
    """

    def __init__(
        self,
        db_url:                Optional[str] = None,
        insight_engine         = None,
        expiry_hours:          int   = _DEFAULT_EXPIRY_HOURS,
    ):
        """
        Parameters
        ──────────
        db_url         : explicit DB URL (overrides OMNIX_DB_URL env var).
        insight_engine : CalibrationInsightEngine instance for full_response_cycle().
                         If None, one is created using db_url.
        expiry_hours   : hours after which ACTIVE recommendations auto-expire (default 24).
        """
        self.db_url       = db_url or os.environ.get("OMNIX_DB_URL") or os.environ.get("DATABASE_URL")
        self.expiry_hours = expiry_hours
        self._insight     = insight_engine

    # ── Schema management ─────────────────────────────────────────────────────

    def ensure_schema(self, conn=None) -> bool:
        """Create the anomaly_recommendations table and indexes if not present."""
        own_conn = conn is None
        if own_conn:
            if not self.db_url:
                logger.warning("[AR] No DB URL — schema not created")
                return False
            try:
                conn = _get_db_conn(self.db_url)
            except Exception as exc:
                logger.error("[AR] DB connection failed for schema: %s", exc)
                return False

        try:
            cur = conn.cursor()
            cur.execute(_CREATE_TABLE)
            for idx_sql in _CREATE_INDEXES:
                cur.execute(idx_sql)
            conn.commit()
            cur.close()
            logger.info("[AR] Schema ensured: %s", _TABLE)
            return True
        except Exception as exc:
            logger.error("[AR] Schema creation error: %s", exc)
            try:
                conn.rollback()
            except Exception:
                pass
            return False
        finally:
            _close_if_own(own_conn, conn)

    # ── Recommendation generation (pure — no DB) ──────────────────────────────

    def generate_recommendations(
        self,
        anomaly_result: Dict[str, Any],
        *,
        expiry_hours: Optional[int] = None,
    ) -> List[AnomalyRecommendation]:
        """
        Generate AnomalyRecommendation objects from a detect_anomalies() result.

        Pure function — no DB access, no side effects.

        Parameters
        ──────────
        anomaly_result : dict returned by CalibrationInsightEngine.detect_anomalies()
        expiry_hours   : override instance default (for testing).

        Returns
        ───────
        List of AnomalyRecommendation (one per detected anomaly that has a mapping).
        """
        if not anomaly_result.get("available", False):
            return []

        domain      = anomaly_result.get("domain")
        anomalies   = anomaly_result.get("anomalies", [])
        exp_hours   = expiry_hours if expiry_hours is not None else self.expiry_hours
        now         = datetime.now(timezone.utc)
        expires_at  = (now + timedelta(hours=exp_hours)).isoformat()

        recommendations: List[AnomalyRecommendation] = []

        for anomaly in anomalies:
            atype    = anomaly.get("anomaly_type", "")
            severity = anomaly.get("severity", "MEDIUM")
            det_at   = anomaly.get("detected_at")

            spec = _ANOMALY_ACTION_MAP.get(atype)
            if spec is None:
                logger.debug("[AR] No action mapping for anomaly_type=%s — skipping", atype)
                continue

            urgency = _SEVERITY_TO_URGENCY.get(severity, URGENCY_ELEVATED)

            rec = AnomalyRecommendation(
                id                 = str(uuid.uuid4()),
                anomaly_type       = atype,
                severity           = severity,
                urgency            = urgency,
                domain             = domain,
                action_code        = spec.action_code,
                action_description = spec.action_description,
                rationale          = spec.rationale,
                is_reversible      = spec.is_reversible,
                status             = STATUS_ACTIVE,
                created_at         = now.isoformat(),
                anomaly_detected_at = det_at,
                expires_at         = expires_at,
                auto_generated     = True,
            )
            recommendations.append(rec)

        return recommendations

    # ── Persistence ───────────────────────────────────────────────────────────

    def log_recommendations(
        self,
        recommendations: List[AnomalyRecommendation],
        *,
        conn = None,
    ) -> int:
        """
        Persist a list of recommendations to the DB.

        Skips duplicates silently — if a recommendation with the same id already
        exists, the INSERT is ignored (ON CONFLICT DO NOTHING).

        Returns the number of recommendations successfully inserted.
        """
        if not recommendations:
            return 0

        own_conn = conn is None
        try:
            own_conn_flag, conn = _maybe_connect(self.db_url, conn)
        except RuntimeError as exc:
            logger.warning("[AR] log_recommendations: %s", exc)
            return 0

        written = 0
        try:
            cur = conn.cursor()
            for rec in recommendations:
                try:
                    cur.execute(
                        f"""
                        INSERT INTO {_TABLE}
                            (id, created_at, anomaly_type, severity, urgency, domain,
                             action_code, action_description, rationale,
                             is_reversible, status, anomaly_detected_at,
                             expires_at, auto_generated)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (id) DO NOTHING
                        """,
                        (
                            rec.id, rec.created_at, rec.anomaly_type, rec.severity,
                            rec.urgency, rec.domain,
                            rec.action_code, rec.action_description, rec.rationale,
                            rec.is_reversible, rec.status, rec.anomaly_detected_at,
                            rec.expires_at, rec.auto_generated,
                        ),
                    )
                    if cur.rowcount > 0:
                        written += 1
                except Exception as row_exc:
                    logger.error("[AR] Row insert error: %s", row_exc)
                    try:
                        conn.rollback()
                    except Exception:
                        pass
            conn.commit()
            cur.close()
            if written:
                logger.info("[AR] Logged %d recommendations to %s", written, _TABLE)
        except Exception as exc:
            logger.error("[AR] log_recommendations batch error: %s", exc)
            try:
                conn.rollback()
            except Exception:
                pass
        finally:
            _close_if_own(own_conn_flag, conn)

        return written

    # ── Lifecycle transitions ─────────────────────────────────────────────────

    def acknowledge(
        self,
        rec_id:         str,
        acknowledged_by: str,
        *,
        conn = None,
    ) -> bool:
        """
        Mark a recommendation as ACKNOWLEDGED by an operator.

        Only transitions ACTIVE → ACKNOWLEDGED. Returns True on success.
        """
        return self._transition(
            rec_id        = rec_id,
            new_status    = STATUS_ACKNOWLEDGED,
            from_statuses = (STATUS_ACTIVE,),
            extra_sets    = "acknowledged_at = NOW(), acknowledged_by = %s",
            extra_params  = (acknowledged_by,),
            conn          = conn,
        )

    def resolve(
        self,
        rec_id:        str,
        resolved_note: str = "",
        *,
        conn = None,
    ) -> bool:
        """
        Mark a recommendation as RESOLVED with an optional note.

        Transitions ACTIVE or ACKNOWLEDGED → RESOLVED. Returns True on success.
        """
        return self._transition(
            rec_id        = rec_id,
            new_status    = STATUS_RESOLVED,
            from_statuses = (STATUS_ACTIVE, STATUS_ACKNOWLEDGED),
            extra_sets    = "resolved_at = NOW(), resolved_note = %s",
            extra_params  = (resolved_note or "",),
            conn          = conn,
        )

    def expire_stale(
        self,
        *,
        hours: Optional[int] = None,
        conn  = None,
    ) -> int:
        """
        Expire ACTIVE recommendations whose expires_at has passed.

        If hours is provided, expires recommendations older than that many hours
        regardless of their expires_at column.

        Returns number of recommendations expired.
        """
        own_conn_flag, conn = (False, conn) if conn is not None else (True, None)
        try:
            if conn is None:
                if not self.db_url:
                    logger.warning("[AR] expire_stale: no DB URL")
                    return 0
                conn = _get_db_conn(self.db_url)
                own_conn_flag = True

            cur = conn.cursor()
            if hours is not None:
                cur.execute(
                    f"""
                    UPDATE {_TABLE}
                    SET status = %s
                    WHERE status = %s
                      AND created_at <= NOW() - INTERVAL '%s hours'
                    """,
                    (STATUS_EXPIRED, STATUS_ACTIVE, hours),
                )
            else:
                cur.execute(
                    f"""
                    UPDATE {_TABLE}
                    SET status = %s
                    WHERE status = %s
                      AND expires_at IS NOT NULL
                      AND expires_at <= NOW()
                    """,
                    (STATUS_EXPIRED, STATUS_ACTIVE),
                )
            count = cur.rowcount or 0
            conn.commit()
            cur.close()
            if count:
                logger.info("[AR] Expired %d stale recommendations", count)
            return count
        except Exception as exc:
            logger.error("[AR] expire_stale error: %s", exc)
            try:
                conn.rollback()
            except Exception:
                pass
            return 0
        finally:
            _close_if_own(own_conn_flag, conn)

    # ── Query interface ───────────────────────────────────────────────────────

    def get_active(
        self,
        *,
        domain: Optional[str] = None,
        conn   = None,
    ) -> List[Dict[str, Any]]:
        """
        Return all ACTIVE recommendations, optionally filtered by domain.

        Returns list of dicts (same structure as AnomalyRecommendation.to_dict()).
        """
        return self._query_recommendations(
            statuses=[STATUS_ACTIVE], domain=domain, conn=conn
        )

    def get_history(
        self,
        *,
        domain:  Optional[str] = None,
        limit:   int           = 50,
        conn     = None,
    ) -> List[Dict[str, Any]]:
        """
        Return full recommendation history (all statuses), newest first.

        Parameters
        ──────────
        domain : filter by domain, or None for all.
        limit  : max rows to return (default 50).
        """
        return self._query_recommendations(
            statuses=list(_VALID_STATUSES), domain=domain, limit=limit, conn=conn
        )

    def summary(
        self,
        *,
        domain: Optional[str] = None,
        conn   = None,
    ) -> Dict[str, Any]:
        """
        Summary of recommendation counts by status and action_code.

        Returns
        ───────
        {
            "domain":   str | None,
            "available": bool,
            "active":       int,
            "acknowledged": int,
            "resolved":     int,
            "expired":      int,
            "by_action": { action_code: int, ... },
        }
        """
        own_conn_flag, conn = (False, conn) if conn is not None else (True, None)
        try:
            if conn is None:
                if not self.db_url:
                    return _empty_summary(domain)
                conn = _get_db_conn(self.db_url)
                own_conn_flag = True

            domain_filter = "AND domain = %s" if domain else ""
            params: Tuple = (domain,) if domain else ()

            cur = conn.cursor()
            cur.execute(
                f"""
                SELECT
                    COUNT(*) FILTER (WHERE status = 'ACTIVE')        AS active,
                    COUNT(*) FILTER (WHERE status = 'ACKNOWLEDGED')  AS acknowledged,
                    COUNT(*) FILTER (WHERE status = 'RESOLVED')      AS resolved,
                    COUNT(*) FILTER (WHERE status = 'EXPIRED')       AS expired
                FROM {_TABLE}
                WHERE 1=1 {domain_filter}
                """,
                params,
            )
            row = cur.fetchone() or (0, 0, 0, 0)

            cur.execute(
                f"""
                SELECT action_code, COUNT(*) AS cnt
                FROM {_TABLE}
                WHERE 1=1 {domain_filter}
                GROUP BY action_code
                ORDER BY cnt DESC
                """,
                params,
            )
            by_action = {r[0]: int(r[1]) for r in cur.fetchall()}
            cur.close()

            return {
                "domain":       domain,
                "available":    True,
                "active":       int(row[0] or 0),
                "acknowledged": int(row[1] or 0),
                "resolved":     int(row[2] or 0),
                "expired":      int(row[3] or 0),
                "by_action":    by_action,
            }
        except Exception as exc:
            logger.warning("[AR] summary error: %s", exc)
            return _empty_summary(domain)
        finally:
            _close_if_own(own_conn_flag, conn)

    # ── Full response cycle ───────────────────────────────────────────────────

    def full_response_cycle(
        self,
        *,
        domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Complete anomaly detection + recommendation generation + persistence.

        Steps:
        1. Run CalibrationInsightEngine.detect_anomalies(domain=domain)
        2. Generate recommendations from detected anomalies
        3. Log recommendations to DB
        4. Return structured result

        Parameters
        ──────────
        domain : governance domain, or None for all domains.

        Returns
        ───────
        {
            "domain":           str | None,
            "available":        bool,
            "anomalies":        { ... detect_anomalies() output },
            "recommendations":  [ { rec.to_dict() } ],
            "new_logged":       int,
            "active_count":     int,
            "overall_severity": str,
            "generated_at":     str,
        }
        """
        ts = datetime.now(timezone.utc).isoformat()

        # 1. Ensure insight engine
        insight = self._get_or_create_insight_engine()

        # 2. Detect anomalies
        try:
            anomaly_result = insight.detect_anomalies(domain=domain)
        except Exception as exc:
            logger.error("[AR] full_response_cycle: detect_anomalies failed: %s", exc)
            return {
                "domain":           domain,
                "available":        False,
                "anomalies":        {"available": False, "anomalies": []},
                "recommendations":  [],
                "new_logged":       0,
                "active_count":     0,
                "overall_severity": "NONE",
                "generated_at":     ts,
            }

        # 3. Generate recommendations (pure)
        recommendations = self.generate_recommendations(anomaly_result)

        # 4. Log to DB (best effort — failures do not block the response)
        new_logged = 0
        try:
            new_logged = self.log_recommendations(recommendations)
        except Exception as exc:
            logger.warning("[AR] full_response_cycle: log_recommendations failed: %s", exc)

        # 5. Count current active recommendations for this domain
        active_count = 0
        try:
            active_recs = self.get_active(domain=domain)
            active_count = len(active_recs)
        except Exception:
            active_count = len(recommendations)

        return {
            "domain":           domain,
            "available":        anomaly_result.get("available", False),
            "anomalies":        anomaly_result,
            "recommendations":  [r.to_dict() for r in recommendations],
            "new_logged":       new_logged,
            "active_count":     active_count,
            "overall_severity": anomaly_result.get("overall_severity", "NONE"),
            "generated_at":     ts,
        }

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _get_or_create_insight_engine(self):
        if self._insight is not None:
            return self._insight
        try:
            from omnix_core.governance.calibration_insight import CalibrationInsightEngine
            self._insight = CalibrationInsightEngine(db_url=self.db_url)
        except Exception as exc:
            logger.error("[AR] Could not create CalibrationInsightEngine: %s", exc)
            raise
        return self._insight

    def _transition(
        self,
        rec_id:        str,
        new_status:    str,
        from_statuses: Tuple[str, ...],
        extra_sets:    str,
        extra_params:  Tuple,
        conn           = None,
    ) -> bool:
        own_conn_flag, conn = (False, conn) if conn is not None else (True, None)
        try:
            if conn is None:
                if not self.db_url:
                    logger.warning("[AR] _transition: no DB URL")
                    return False
                conn = _get_db_conn(self.db_url)
                own_conn_flag = True

            placeholders = ", ".join(["%s"] * len(from_statuses))
            cur = conn.cursor()
            cur.execute(
                f"""
                UPDATE {_TABLE}
                SET status = %s, {extra_sets}
                WHERE id = %s AND status IN ({placeholders})
                """,
                (new_status, *extra_params, rec_id, *from_statuses),
            )
            updated = cur.rowcount > 0
            conn.commit()
            cur.close()
            if updated:
                logger.info("[AR] Recommendation %s → %s", rec_id, new_status)
            return updated
        except Exception as exc:
            logger.error("[AR] _transition error (%s → %s): %s", rec_id, new_status, exc)
            try:
                conn.rollback()
            except Exception:
                pass
            return False
        finally:
            _close_if_own(own_conn_flag, conn)

    def _query_recommendations(
        self,
        *,
        statuses: List[str],
        domain:   Optional[str] = None,
        limit:    int           = 200,
        conn      = None,
    ) -> List[Dict[str, Any]]:
        own_conn_flag, conn = (False, conn) if conn is not None else (True, None)
        try:
            if conn is None:
                if not self.db_url:
                    return []
                conn = _get_db_conn(self.db_url)
                own_conn_flag = True

            placeholders = ", ".join(["%s"] * len(statuses))
            domain_filter = "AND domain = %s" if domain else ""
            params: Tuple = (*statuses, *((domain,) if domain else ()))

            cur = conn.cursor()
            cur.execute(
                f"""
                SELECT id, created_at, anomaly_type, severity, urgency, domain,
                       action_code, action_description, rationale,
                       is_reversible, status, anomaly_detected_at,
                       expires_at, acknowledged_at, acknowledged_by,
                       resolved_at, resolved_note, auto_generated
                FROM {_TABLE}
                WHERE status IN ({placeholders}) {domain_filter}
                ORDER BY created_at DESC
                LIMIT {int(limit)}
                """,
                params,
            )
            rows = cur.fetchall()
            cur.close()

            results = []
            for row in rows:
                results.append({
                    "id":                  row[0],
                    "created_at":          row[1].isoformat() if hasattr(row[1], "isoformat") else str(row[1]),
                    "anomaly_type":        row[2],
                    "severity":            row[3],
                    "urgency":             row[4],
                    "domain":              row[5],
                    "action_code":         row[6],
                    "action_description":  row[7],
                    "rationale":           row[8],
                    "is_reversible":       row[9],
                    "status":              row[10],
                    "anomaly_detected_at": row[11].isoformat() if hasattr(row[11], "isoformat") else row[11],
                    "expires_at":          row[12].isoformat() if hasattr(row[12], "isoformat") else row[12],
                    "acknowledged_at":     row[13].isoformat() if hasattr(row[13], "isoformat") else row[13],
                    "acknowledged_by":     row[14],
                    "resolved_at":         row[15].isoformat() if hasattr(row[15], "isoformat") else row[15],
                    "resolved_note":       row[16],
                    "auto_generated":      row[17],
                })
            return results

        except Exception as exc:
            logger.warning("[AR] _query_recommendations error: %s", exc)
            return []
        finally:
            _close_if_own(own_conn_flag, conn)


# ── Module-level helpers ──────────────────────────────────────────────────────

def get_response_engine(
    insight_engine = None,
    db_url:          Optional[str] = None,
) -> AnomalyResponseEngine:
    """
    Convenience factory — returns an AnomalyResponseEngine.

    If insight_engine is provided it is injected directly.
    Otherwise the engine creates its own CalibrationInsightEngine on demand.
    """
    return AnomalyResponseEngine(insight_engine=insight_engine, db_url=db_url)


def _empty_summary(domain: Optional[str]) -> Dict[str, Any]:
    return {
        "domain":       domain,
        "available":    False,
        "active":       0,
        "acknowledged": 0,
        "resolved":     0,
        "expired":      0,
        "by_action":    {},
    }
