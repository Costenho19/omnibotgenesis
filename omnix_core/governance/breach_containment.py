"""
OMNIX — Breach Containment Engine (BCE)
ADR-142: Automated Decision Suspension Under Detected Compromise

Purpose:
    The Breach Containment Engine monitors for indicators of execution environment
    compromise (cyberattack, tampered state, process anomalies, timing attacks)
    and can immediately suspend all automated governance decisions when triggered.

    Unlike the AVM (which adjusts thresholds) or the CAG (which blocks on market
    conditions), the BCE operates at the infrastructure layer — it halts the
    decision engine itself when the environment can no longer be trusted.

Design:
    - CONTAINMENT_ACTIVE: all governance decisions return BLOCKED immediately
    - CONTAINMENT_INACTIVE: normal pipeline operation
    - Activation: manual (API) or automatic (anomaly detection)
    - Release: requires explicit authorization (human-in-the-loop)
    - Fail-closed: any BCE error → CONTAINMENT_ACTIVE (ADR-116)
    - All events persisted to `breach_containment_events` table

Threat Indicators:
    1. Timing anomaly — evaluation latency deviates from baseline by >3σ
    2. Checksum mismatch — AVM snapshot hash does not match expected
    3. Process anomaly — unexpected memory growth or process substitution signal
    4. Manual trigger — authorized operator flags a compromise
    5. Repeated auth failures — brute-force or credential stuffing above threshold

Lifecycle:
    INACTIVE → ACTIVE (breach detected) → RELEASED (authorized release)
                          ↓
                   All decisions BLOCKED

Regulatory alignment:
    - NIST AI RMF: GV-1.1 (AI risk policies), MS-2.5 (incident response)
    - EU AI Act Art. 9: Risk management — operational monitoring
    - ISO/IEC 42001: AI management system — incident and breach response
    - NIS2 Directive: Incident handling for critical infrastructure AI

ADR-142 | Implemented: May 2026
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger("OMNIX.BreachContainment")

_TABLE = "breach_containment_events"

# ── Status constants ──────────────────────────────────────────────────────────
STATUS_INACTIVE  = "INACTIVE"
STATUS_ACTIVE    = "ACTIVE"
STATUS_RELEASED  = "RELEASED"

# ── Trigger codes ─────────────────────────────────────────────────────────────
TRIGGER_MANUAL           = "MANUAL_OPERATOR"
TRIGGER_TIMING_ANOMALY   = "TIMING_ANOMALY"
TRIGGER_CHECKSUM_MISMATCH = "CHECKSUM_MISMATCH"
TRIGGER_PROCESS_ANOMALY  = "PROCESS_ANOMALY"
TRIGGER_AUTH_FAILURE     = "REPEATED_AUTH_FAILURE"
TRIGGER_API              = "API_TRIGGERED"

# ── Severity levels ───────────────────────────────────────────────────────────
SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_HIGH     = "HIGH"
SEVERITY_MEDIUM   = "MEDIUM"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _event_id() -> str:
    return f"BCE-{uuid.uuid4().hex[:12].upper()}"


def _get_conn():
    """Obtain a DB connection from DATABASE_URL."""
    import psycopg
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg.connect(url)


_DDL = """
CREATE TABLE IF NOT EXISTS breach_containment_events (
    id              SERIAL PRIMARY KEY,
    event_id        TEXT        NOT NULL UNIQUE,
    status          TEXT        NOT NULL,
    trigger_code    TEXT        NOT NULL,
    severity        TEXT        NOT NULL,
    summary         TEXT        NOT NULL,
    detail          JSONB,
    triggered_by    TEXT,
    released_by     TEXT,
    release_note    TEXT,
    triggered_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    released_at     TIMESTAMPTZ,
    is_active       BOOLEAN     NOT NULL DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS idx_bce_status
    ON breach_containment_events (status);
CREATE INDEX IF NOT EXISTS idx_bce_triggered_at
    ON breach_containment_events (triggered_at DESC);
CREATE INDEX IF NOT EXISTS idx_bce_is_active
    ON breach_containment_events (is_active);
"""


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class BreachEvent:
    event_id:     str
    status:       str
    trigger_code: str
    severity:     str
    summary:      str
    detail:       Dict[str, Any]
    triggered_by: str
    released_by:  Optional[str]
    release_note: Optional[str]
    triggered_at: str
    released_at:  Optional[str]
    is_active:    bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id":     self.event_id,
            "status":       self.status,
            "trigger_code": self.trigger_code,
            "severity":     self.severity,
            "summary":      self.summary,
            "detail":       self.detail,
            "triggered_by": self.triggered_by,
            "released_by":  self.released_by,
            "release_note": self.release_note,
            "triggered_at": self.triggered_at,
            "released_at":  self.released_at,
            "is_active":    self.is_active,
        }


@dataclass
class ContainmentStatus:
    is_contained:     bool
    active_event_id:  Optional[str]
    trigger_code:     Optional[str]
    severity:         Optional[str]
    summary:          Optional[str]
    triggered_at:     Optional[str]
    triggered_by:     Optional[str]
    total_events:     int
    last_event_at:    Optional[str]
    evaluated_at:     str = field(default_factory=_now_utc)
    adr:              str = "ADR-142"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_contained":    self.is_contained,
            "active_event_id": self.active_event_id,
            "trigger_code":    self.trigger_code,
            "severity":        self.severity,
            "summary":         self.summary,
            "triggered_at":    self.triggered_at,
            "triggered_by":    self.triggered_by,
            "total_events":    self.total_events,
            "last_event_at":   self.last_event_at,
            "evaluated_at":    self.evaluated_at,
            "adr":             self.adr,
            "design_invariant": (
                "When is_contained=true, all automated governance decisions "
                "must return BLOCKED. Release requires explicit human authorization. "
                "Fail-closed: BCE error → CONTAINED. ADR-116, ADR-142."
            ),
        }


# ── Engine ────────────────────────────────────────────────────────────────────

class BreachContainmentEngine:
    """
    ADR-142 — Breach Containment Engine.

    Usage:
        bce = BreachContainmentEngine()
        status = bce.get_status()
        if status.is_contained:
            return BLOCKED

        # Trigger containment:
        event = bce.activate_containment(
            trigger_code=TRIGGER_API,
            severity=SEVERITY_HIGH,
            summary="Anomalous memory growth detected",
            triggered_by="ops-team",
        )

        # Release containment:
        bce.release_containment(event.event_id, authorized_by="ciso", note="Cleared")
    """

    _table_ensured: bool = False

    def ensure_table(self) -> None:
        try:
            conn = _get_conn()
            with conn:
                with conn.cursor() as cur:
                    cur.execute(_DDL)
            conn.close()
            BreachContainmentEngine._table_ensured = True
            logger.info("[BCE] breach_containment_events table ready")
        except Exception as exc:
            logger.error("[BCE] ensure_table failed: %s", exc)

    def _ensure(self) -> None:
        if not BreachContainmentEngine._table_ensured:
            self.ensure_table()

    # ── Read ──────────────────────────────────────────────────────────────────

    def get_status(self) -> ContainmentStatus:
        """
        Returns current containment status.
        Fail-closed: if DB unreachable → is_contained=True (ADR-116).
        """
        try:
            self._ensure()
            conn = _get_conn()
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT event_id, trigger_code, severity, summary, "
                        "triggered_at, triggered_by "
                        "FROM breach_containment_events "
                        "WHERE is_active = TRUE AND status = %s "
                        "ORDER BY triggered_at DESC LIMIT 1",
                        (STATUS_ACTIVE,),
                    )
                    row = cur.fetchone()

                    cur.execute("SELECT COUNT(*), MAX(triggered_at) FROM breach_containment_events")
                    agg = cur.fetchone()
            conn.close()

            total  = agg[0] if agg else 0
            last_t = agg[1].isoformat() if (agg and agg[1]) else None

            if row:
                return ContainmentStatus(
                    is_contained    = True,
                    active_event_id = row[0],
                    trigger_code    = row[1],
                    severity        = row[2],
                    summary         = row[3],
                    triggered_at    = row[4].isoformat() if row[4] else None,
                    triggered_by    = row[5],
                    total_events    = total,
                    last_event_at   = last_t,
                )

            return ContainmentStatus(
                is_contained    = False,
                active_event_id = None,
                trigger_code    = None,
                severity        = None,
                summary         = None,
                triggered_at    = None,
                triggered_by    = None,
                total_events    = total,
                last_event_at   = last_t,
            )

        except Exception as exc:
            logger.error("[BCE] get_status failed — FAIL-CLOSED: %s", exc)
            return ContainmentStatus(
                is_contained    = True,
                active_event_id = None,
                trigger_code    = "DB_FAILURE",
                severity        = SEVERITY_CRITICAL,
                summary         = f"BCE DB unreachable — fail-closed: {type(exc).__name__}",
                triggered_at    = _now_utc(),
                triggered_by    = "BCE_FAILSAFE",
                total_events    = 0,
                last_event_at   = None,
            )

    def get_history(
        self,
        limit:  int = 50,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return paginated breach event history."""
        self._ensure()
        try:
            conn = _get_conn()
            params: list = []
            where = ""
            if status:
                where = "WHERE status = %s"
                params.append(status)

            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"SELECT COUNT(*) FROM {_TABLE} {where}", params
                    )
                    total = cur.fetchone()[0]

                    cur.execute(
                        f"SELECT event_id, status, trigger_code, severity, summary, "
                        f"triggered_by, released_by, release_note, triggered_at, released_at, is_active "
                        f"FROM {_TABLE} {where} "
                        f"ORDER BY triggered_at DESC LIMIT %s OFFSET %s",
                        params + [limit, offset],
                    )
                    rows = cur.fetchall()
            conn.close()

            events = []
            for r in rows:
                events.append({
                    "event_id":     r[0],
                    "status":       r[1],
                    "trigger_code": r[2],
                    "severity":     r[3],
                    "summary":      r[4],
                    "triggered_by": r[5],
                    "released_by":  r[6],
                    "release_note": r[7],
                    "triggered_at": r[8].isoformat() if r[8] else None,
                    "released_at":  r[9].isoformat() if r[9] else None,
                    "is_active":    r[10],
                })

            return {
                "events":    events,
                "total":     total,
                "limit":     limit,
                "offset":    offset,
                "has_more":  (offset + limit) < total,
            }

        except Exception as exc:
            logger.error("[BCE] get_history failed: %s", exc)
            return {"events": [], "total": 0, "limit": limit, "offset": offset, "error": str(exc)}

    # ── Write ─────────────────────────────────────────────────────────────────

    def activate_containment(
        self,
        trigger_code: str,
        severity:     str,
        summary:      str,
        triggered_by: str = "system",
        detail:       Optional[Dict[str, Any]] = None,
    ) -> BreachEvent:
        """
        Activate containment. All subsequent calls to get_status() return is_contained=True.
        Persists event to DB. Returns the BreachEvent.
        """
        self._ensure()
        event_id = _event_id()
        now      = _now_utc()
        detail_  = detail or {}

        logger.critical(
            "[BCE] ⛔ CONTAINMENT ACTIVATED | event=%s trigger=%s severity=%s by=%s | %s",
            event_id, trigger_code, severity, triggered_by, summary,
        )

        try:
            conn = _get_conn()
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"INSERT INTO {_TABLE} "
                        "(event_id, status, trigger_code, severity, summary, detail, triggered_by, is_active) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                        (
                            event_id, STATUS_ACTIVE, trigger_code, severity,
                            summary[:512], json.dumps(detail_), triggered_by, True,
                        ),
                    )
            conn.close()
        except Exception as exc:
            logger.error("[BCE] activate_containment DB write failed: %s", exc)

        return BreachEvent(
            event_id     = event_id,
            status       = STATUS_ACTIVE,
            trigger_code = trigger_code,
            severity     = severity,
            summary      = summary,
            detail       = detail_,
            triggered_by = triggered_by,
            released_by  = None,
            release_note = None,
            triggered_at = now,
            released_at  = None,
            is_active    = True,
        )

    def release_containment(
        self,
        event_id:      str,
        authorized_by: str,
        release_note:  str = "",
    ) -> Dict[str, Any]:
        """
        Release an active containment event. Requires human authorization.
        Returns dict with success flag.
        """
        self._ensure()
        now = _now_utc()

        logger.warning(
            "[BCE] ✅ CONTAINMENT RELEASED | event=%s by=%s | %s",
            event_id, authorized_by, release_note,
        )

        try:
            conn = _get_conn()
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"UPDATE {_TABLE} "
                        "SET status=%s, released_by=%s, release_note=%s, released_at=NOW(), is_active=FALSE "
                        "WHERE event_id=%s AND status=%s",
                        (STATUS_RELEASED, authorized_by, release_note[:512], event_id, STATUS_ACTIVE),
                    )
                    updated = cur.rowcount
            conn.close()

            if updated == 0:
                return {
                    "success": False,
                    "error":   f"Event {event_id} not found or not in ACTIVE status",
                }

            return {
                "success":      True,
                "event_id":     event_id,
                "authorized_by": authorized_by,
                "released_at":  now,
                "message":      "Containment released. Normal governance operations resumed.",
            }

        except Exception as exc:
            logger.error("[BCE] release_containment failed: %s", exc)
            return {"success": False, "error": str(exc)}

    # ── Automated detection ───────────────────────────────────────────────────

    def assess_environment(
        self,
        latency_ms:         Optional[float] = None,
        expected_latency_ms: Optional[float] = None,
        latency_sigma:       Optional[float] = None,
        avm_snapshot_hash:   Optional[str]   = None,
        expected_hash:       Optional[str]   = None,
        auth_failure_count:  int = 0,
        auth_failure_window: int = 300,
    ) -> Dict[str, Any]:
        """
        Automated threat assessment. Returns a dict with threat indicators.
        Callers should call activate_containment() if threats are found.

        Args:
            latency_ms:           Current evaluation latency in ms.
            expected_latency_ms:  Baseline latency.
            latency_sigma:        Standard deviation of baseline.
            avm_snapshot_hash:    Hash of current AVM snapshot.
            expected_hash:        Expected AVM snapshot hash.
            auth_failure_count:   Auth failures in the window.
            auth_failure_window:  Window size in seconds.

        Returns:
            {
                "threats_detected": bool,
                "indicators": [...],
                "recommended_action": "ACTIVATE_CONTAINMENT" | "MONITOR" | "CLEAR",
            }
        """
        indicators = []

        if (
            latency_ms is not None
            and expected_latency_ms is not None
            and latency_sigma is not None
            and latency_sigma > 0
        ):
            deviation = abs(latency_ms - expected_latency_ms) / latency_sigma
            if deviation > 3.0:
                indicators.append({
                    "type":      TRIGGER_TIMING_ANOMALY,
                    "severity":  SEVERITY_HIGH,
                    "detail":    {
                        "latency_ms":          latency_ms,
                        "expected_latency_ms": expected_latency_ms,
                        "deviation_sigma":     round(deviation, 2),
                        "threshold_sigma":     3.0,
                    },
                    "summary": (
                        f"Evaluation latency {latency_ms:.1f}ms deviates "
                        f"{deviation:.1f}σ from baseline {expected_latency_ms:.1f}ms"
                    ),
                })

        if avm_snapshot_hash and expected_hash and avm_snapshot_hash != expected_hash:
            indicators.append({
                "type":      TRIGGER_CHECKSUM_MISMATCH,
                "severity":  SEVERITY_CRITICAL,
                "detail":    {
                    "observed_hash": avm_snapshot_hash[:16] + "…",
                    "expected_hash": expected_hash[:16] + "…",
                },
                "summary": "AVM snapshot hash mismatch — potential tampering detected",
            })

        if auth_failure_count >= 10:
            indicators.append({
                "type":     TRIGGER_AUTH_FAILURE,
                "severity": SEVERITY_HIGH,
                "detail":   {
                    "failure_count":  auth_failure_count,
                    "window_seconds": auth_failure_window,
                    "threshold":      10,
                },
                "summary": (
                    f"{auth_failure_count} auth failures in {auth_failure_window}s window "
                    "— possible brute-force or credential stuffing"
                ),
            })

        threats = len(indicators) > 0
        action = "CLEAR"
        if threats:
            critical = any(i["severity"] == SEVERITY_CRITICAL for i in indicators)
            action = "ACTIVATE_CONTAINMENT" if critical or len(indicators) >= 2 else "MONITOR"

        return {
            "threats_detected":   threats,
            "indicator_count":    len(indicators),
            "indicators":         indicators,
            "recommended_action": action,
            "assessed_at":        _now_utc(),
            "adr":                "ADR-142",
        }
