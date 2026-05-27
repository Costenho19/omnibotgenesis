"""
OMNIX Oversight Surface Engine (OSE) — ADR-124.

Governs the *quality* of human oversight moments, not just their existence.

Problem addressed (Tudela, 2026):
  Admissibility defines which decisions can exist.
  Governability requires that those decisions remain controllable once
  presented to a human. Within admissible states, the way information
  is structured, timed and framed can shape — and limit — how
  judgment is actually formed.

The OSE governs three dimensions of the oversight moment:
  1. Deliberation Window  — minimum time before a supervisor can submit.
  2. Framing Governance   — required fields must be present and visible.
  3. Override Friction    — structured justification mandatory for reversals.

And produces one composite metric:
  Epistemic Quality Score (EQS) — 0.0–1.0 measure of whether the oversight
  moment was genuinely deliberative.

Aligns with:
  EU AI Act  — Article 14 (human oversight of high-risk AI)
  NIST AI RMF — GOVERN 1.7, MANAGE 4.1
  ADR-029 — Governance Compliance Modules

Design principle: purely additive. Never modifies decision_receipts or
governance_overrides. An oversight session is a metadata record ABOUT
the oversight moment, not about the decision itself.
"""

import hashlib
import json
import logging
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger("OMNIX.Governance.OversightSurface")

DELIBERATION_WINDOW_SECONDS: int = 30
OVERRIDE_MIN_JUSTIFICATION_CHARS: int = 50
SESSION_EXPIRY_HOURS: int = 48

FRAMING_REQUIRED_FIELDS: list[str] = [
    "risk_score",
    "domain",
    "original_decision",
    "block_reason",
]

VALID_ACTIONS: set[str] = {"CONFIRMED", "OVERRIDDEN", "ESCALATED"}
VALID_STATUSES: set[str] = {"PENDING", "OPEN", "SUBMITTED", "EXPIRED"}


def _get_conn():
    db_url = os.environ.get("DATABASE_URL") or os.environ.get("OMNIX_DB_URL")
    if not db_url:
        raise RuntimeError(
            "DATABASE_URL not configured — OversightSurfaceEngine requires "
            "database access. Set DATABASE_URL or OMNIX_DB_URL."
        )
    return psycopg.connect(db_url)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _session_id() -> str:
    return f"OSE-{uuid.uuid4().hex[:16].upper()}"


class OversightSurfaceEngine:
    """
    Governs the quality of human oversight moments in OMNIX.

    Lifecycle of an oversight session:
        PENDING  → session created, not yet presented to reviewer
        OPEN     → session presented (deliberation timer starts)
        SUBMITTED → reviewer submitted action (CONFIRMED / OVERRIDDEN / ESCALATED)
        EXPIRED  → SESSION_EXPIRY_HOURS elapsed without submission
    """

    def ensure_schema(self) -> None:
        """Create oversight_sessions table if it does not exist."""
        ddl = """
        CREATE TABLE IF NOT EXISTS oversight_sessions (
            session_id              VARCHAR(64)  PRIMARY KEY,
            decision_id             VARCHAR(128) NOT NULL,
            reviewer_id             VARCHAR(128),
            domain                  VARCHAR(64),
            original_decision       VARCHAR(32),
            created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            presented_at            TIMESTAMPTZ,
            submitted_at            TIMESTAMPTZ,
            action                  VARCHAR(32),
            justification           TEXT,
            deliberation_seconds    FLOAT,
            framing_score           FLOAT,
            eqs_score               FLOAT,
            status                  VARCHAR(32)  NOT NULL DEFAULT 'PENDING',
            decision_snapshot       JSONB,
            metadata                JSONB
        );
        CREATE INDEX IF NOT EXISTS idx_ose_decision_id
            ON oversight_sessions (decision_id);
        CREATE INDEX IF NOT EXISTS idx_ose_status
            ON oversight_sessions (status);
        CREATE INDEX IF NOT EXISTS idx_ose_domain
            ON oversight_sessions (domain);
        """
        conn = _get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(ddl)
            logger.info("[OSE] oversight_sessions schema verified/created")
        except Exception as e:
            logger.error("[OSE] ensure_schema failed: %s: %s", type(e).__name__, e)
            raise
        finally:
            conn.close()

    def create_session(
        self,
        decision_id: str,
        domain: str,
        original_decision: str,
        decision_snapshot: dict | None = None,
        reviewer_id: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """
        Create a new oversight session for a decision requiring human review.

        Args:
            decision_id:        Receipt ID or decision identifier.
            domain:             Governance domain (trading, medical, etc.).
            original_decision:  The AI decision (APPROVED, BLOCKED, HOLD).
            decision_snapshot:  Full decision payload for framing context.
            reviewer_id:        Optional — pre-assign a reviewer.
            metadata:           Optional extra context.

        Returns:
            Session dict with session_id, status, and framing_score.
        """
        if not decision_id or not domain or not original_decision:
            raise ValueError("decision_id, domain and original_decision are required")

        session_id = _session_id()
        snapshot = decision_snapshot or {}
        framing_score = self._assess_framing(snapshot)

        conn = _get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO oversight_sessions
                            (session_id, decision_id, reviewer_id, domain,
                             original_decision, created_at, status,
                             framing_score, decision_snapshot, metadata)
                        VALUES (%s,%s,%s,%s,%s,%s,'PENDING',%s,%s,%s)
                        """,
                        (
                            session_id,
                            str(decision_id)[:128],
                            str(reviewer_id)[:128] if reviewer_id else None,
                            str(domain)[:64],
                            str(original_decision)[:32],
                            _now(),
                            framing_score,
                            json.dumps(snapshot),
                            json.dumps(metadata or {}),
                        ),
                    )
            logger.info(
                "[OSE] session created: %s | decision=%s domain=%s framing=%.2f",
                session_id, decision_id, domain, framing_score,
            )
            return {
                "session_id": session_id,
                "decision_id": decision_id,
                "domain": domain,
                "original_decision": original_decision,
                "status": "PENDING",
                "framing_score": framing_score,
                "framing_missing": self._missing_framing_fields(snapshot),
                "created_at": _now().isoformat(),
            }
        except Exception as e:
            logger.error("[OSE] create_session error: %s: %s", type(e).__name__, e)
            raise
        finally:
            conn.close()

    def open_session(self, session_id: str) -> dict:
        """
        Mark session as OPEN — starts the deliberation timer.
        Must be called when the oversight UI is presented to the reviewer.

        Returns:
            Updated session dict with deliberation_window_seconds.
        """
        session = self._load_session(session_id)
        if session["status"] not in ("PENDING", "OPEN"):
            raise ValueError(
                f"Session {session_id} cannot be opened from status={session['status']}"
            )
        self._check_expiry(session)

        now = _now()
        conn = _get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE oversight_sessions
                        SET status='OPEN', presented_at=%s
                        WHERE session_id=%s AND status IN ('PENDING','OPEN')
                        """,
                        (now, session_id),
                    )
            logger.info("[OSE] session opened: %s (deliberation timer started)", session_id)
            return {
                "session_id": session_id,
                "status": "OPEN",
                "presented_at": now.isoformat(),
                "deliberation_window_seconds": DELIBERATION_WINDOW_SECONDS,
                "submit_available_after": (
                    now + timedelta(seconds=DELIBERATION_WINDOW_SECONDS)
                ).isoformat(),
            }
        except Exception as e:
            logger.error("[OSE] open_session error: %s: %s", type(e).__name__, e)
            raise
        finally:
            conn.close()

    def submit_review(
        self,
        session_id: str,
        reviewer_id: str,
        action: str,
        justification: str | None = None,
    ) -> dict:
        """
        Submit a human review decision for an oversight session.

        Enforces:
          - Deliberation window (min time since open)
          - Override friction (justification required for OVERRIDDEN)
          - Session must be in OPEN status

        Args:
            session_id:   OSE session identifier.
            reviewer_id:  Human reviewer identifier.
            action:       CONFIRMED | OVERRIDDEN | ESCALATED
            justification: Required when action=OVERRIDDEN.

        Returns:
            Dict with action, eqs_score, deliberation_seconds, and audit_hash.
        """
        if not reviewer_id:
            raise ValueError("reviewer_id is required")
        action = (action or "").upper().strip()
        if action not in VALID_ACTIONS:
            raise ValueError(f"action must be one of {sorted(VALID_ACTIONS)}")

        session = self._load_session(session_id)
        self._check_expiry(session)

        if session["status"] != "OPEN":
            raise ValueError(
                f"Session {session_id} is not OPEN (status={session['status']}). "
                "Call open_session first."
            )

        presented_at = session.get("presented_at")
        if not presented_at:
            raise ValueError(
                f"Session {session_id} has no presented_at timestamp. "
                "Call open_session before submit_review."
            )

        now = _now()
        if isinstance(presented_at, str):
            presented_at = datetime.fromisoformat(presented_at)
        if presented_at.tzinfo is None:
            presented_at = presented_at.replace(tzinfo=timezone.utc)

        deliberation_seconds = (now - presented_at).total_seconds()

        if deliberation_seconds < DELIBERATION_WINDOW_SECONDS:
            remaining = DELIBERATION_WINDOW_SECONDS - deliberation_seconds
            raise ValueError(
                f"Deliberation window not met. "
                f"Please wait {remaining:.0f} more second(s) before submitting. "
                f"Minimum deliberation: {DELIBERATION_WINDOW_SECONDS}s."
            )

        if action == "OVERRIDDEN":
            justification = (justification or "").strip()
            if len(justification) < OVERRIDE_MIN_JUSTIFICATION_CHARS:
                raise ValueError(
                    f"OVERRIDDEN requires a justification of at least "
                    f"{OVERRIDE_MIN_JUSTIFICATION_CHARS} characters "
                    f"(provided: {len(justification)})."
                )

        snapshot = session.get("decision_snapshot") or {}
        if isinstance(snapshot, str):
            try:
                snapshot = json.loads(snapshot)
            except Exception:
                snapshot = {}

        framing_score = session.get("framing_score") or self._assess_framing(snapshot)
        eqs = self._compute_eqs(
            deliberation_seconds=deliberation_seconds,
            framing_score=framing_score,
            action=action,
            justification=justification or "",
        )

        audit_hash = hashlib.sha256(
            f"{session_id}:{reviewer_id}:{action}:{now.isoformat()}".encode()
        ).hexdigest()[:32]

        conn = _get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE oversight_sessions
                        SET status='SUBMITTED',
                            submitted_at=%s,
                            reviewer_id=%s,
                            action=%s,
                            justification=%s,
                            deliberation_seconds=%s,
                            eqs_score=%s
                        WHERE session_id=%s AND status='OPEN'
                        """,
                        (
                            now,
                            str(reviewer_id)[:128],
                            action,
                            justification or None,
                            deliberation_seconds,
                            eqs,
                            session_id,
                        ),
                    )
            logger.info(
                "[OSE] session submitted: %s | action=%s eqs=%.3f deliberation=%.1fs reviewer=%s",
                session_id, action, eqs, deliberation_seconds, reviewer_id,
            )
            return {
                "session_id": session_id,
                "action": action,
                "status": "SUBMITTED",
                "deliberation_seconds": round(deliberation_seconds, 2),
                "eqs_score": round(eqs, 4),
                "eqs_label": self._eqs_label(eqs),
                "framing_score": round(framing_score, 4),
                "audit_hash": audit_hash,
                "submitted_at": now.isoformat(),
                "reviewer_id": reviewer_id,
            }
        except Exception as e:
            logger.error("[OSE] submit_review error: %s: %s", type(e).__name__, e)
            raise
        finally:
            conn.close()

    def get_session(self, session_id: str) -> dict:
        """Return full session record, refreshing expiry status if needed."""
        session = self._load_session(session_id)
        try:
            self._check_expiry(session)
            session = self._load_session(session_id)
        except Exception as e:
            logger.debug("[OSE] get_session expiry check: %s", e)
        return self._serialize_session(session)

    def list_sessions(
        self,
        status: str | None = None,
        domain: str | None = None,
        reviewer_id: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """List oversight sessions with optional filters."""
        limit = max(1, min(int(limit), 200))
        filters: list[str] = []
        params: list[Any] = []

        if status:
            filters.append("status = %s")
            params.append(status.upper()[:32])
        if domain:
            filters.append("domain = %s")
            params.append(domain[:64])
        if reviewer_id:
            filters.append("reviewer_id = %s")
            params.append(reviewer_id[:128])

        where = ("WHERE " + " AND ".join(filters)) if filters else ""
        params.append(limit)

        conn = _get_conn()
        try:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    f"""
                    SELECT * FROM oversight_sessions
                    {where}
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    params,
                )
                rows = cur.fetchall()
            return [self._serialize_session(dict(r)) for r in rows]
        except Exception as e:
            logger.error("[OSE] list_sessions error: %s: %s", type(e).__name__, e)
            raise
        finally:
            conn.close()

    def expire_stale_sessions(self) -> int:
        """Mark PENDING/OPEN sessions older than SESSION_EXPIRY_HOURS as EXPIRED."""
        cutoff = _now() - timedelta(hours=SESSION_EXPIRY_HOURS)
        conn = _get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE oversight_sessions
                        SET status='EXPIRED'
                        WHERE status IN ('PENDING','OPEN')
                          AND created_at < %s
                        """,
                        (cutoff,),
                    )
                    count = cur.rowcount
            if count:
                logger.info("[OSE] expired %d stale session(s)", count)
            return count
        except Exception as e:
            logger.error("[OSE] expire_stale_sessions: %s: %s", type(e).__name__, e)
            raise
        finally:
            conn.close()

    def _load_session(self, session_id: str) -> dict:
        conn = _get_conn()
        try:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    "SELECT * FROM oversight_sessions WHERE session_id = %s",
                    (session_id,),
                )
                row = cur.fetchone()
            if not row:
                raise ValueError(f"Session not found: {session_id}")
            return dict(row)
        except Exception as e:
            logger.error("[OSE] _load_session error: %s: %s", type(e).__name__, e)
            raise
        finally:
            conn.close()

    def _check_expiry(self, session: dict) -> None:
        if session.get("status") in ("SUBMITTED", "EXPIRED"):
            return
        created_at = session.get("created_at")
        if created_at:
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            age_hours = (_now() - created_at).total_seconds() / 3600
            if age_hours >= SESSION_EXPIRY_HOURS:
                conn = _get_conn()
                try:
                    with conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                "UPDATE oversight_sessions SET status='EXPIRED' "
                                "WHERE session_id=%s AND status IN ('PENDING','OPEN')",
                                (session["session_id"],),
                            )
                    logger.warning(
                        "[OSE] session expired: %s (age=%.1fh)", session["session_id"], age_hours
                    )
                except Exception as e:
                    logger.error("[OSE] _check_expiry update: %s: %s", type(e).__name__, e)
                finally:
                    conn.close()
                raise ValueError(
                    f"Session {session['session_id']} has expired after {SESSION_EXPIRY_HOURS}h."
                )

    def _assess_framing(self, snapshot: dict) -> float:
        """Return fraction of required framing fields present in snapshot."""
        if not snapshot or not isinstance(snapshot, dict):
            return 0.0
        present = sum(
            1 for f in FRAMING_REQUIRED_FIELDS
            if snapshot.get(f) not in (None, "", [], {})
        )
        return round(present / len(FRAMING_REQUIRED_FIELDS), 4)

    def _missing_framing_fields(self, snapshot: dict) -> list[str]:
        return [
            f for f in FRAMING_REQUIRED_FIELDS
            if snapshot.get(f) in (None, "", [], {})
        ]

    def _compute_eqs(
        self,
        deliberation_seconds: float,
        framing_score: float,
        action: str,
        justification: str,
    ) -> float:
        """
        Epistemic Quality Score — 0.0 to 1.0.

        Weights:
          40% — deliberation time (saturates at 2× window)
          40% — framing completeness
          20% — justification quality (only matters for OVERRIDDEN)
        """
        target_seconds = DELIBERATION_WINDOW_SECONDS * 2
        time_score = min(1.0, deliberation_seconds / max(target_seconds, 1))

        if action == "OVERRIDDEN":
            just_score = min(1.0, len(justification) / 200)
        else:
            just_score = 1.0

        eqs = (time_score * 0.4) + (framing_score * 0.4) + (just_score * 0.2)
        return round(min(1.0, max(0.0, eqs)), 4)

    @staticmethod
    def _eqs_label(eqs: float) -> str:
        if eqs >= 0.85:
            return "HIGH"
        if eqs >= 0.60:
            return "MEDIUM"
        if eqs >= 0.35:
            return "LOW"
        return "MINIMAL"

    def _serialize_session(self, row: dict) -> dict:
        """Convert DB row to JSON-serializable dict."""
        result = {}
        for k, v in row.items():
            if isinstance(v, datetime):
                result[k] = v.isoformat()
            elif isinstance(v, (dict, list)):
                result[k] = v
            else:
                result[k] = v
        if "eqs_score" in result and result["eqs_score"] is not None:
            result["eqs_label"] = self._eqs_label(float(result["eqs_score"]))
        if "framing_score" in result and result["framing_score"] is not None:
            snapshot = result.get("decision_snapshot") or {}
            if isinstance(snapshot, str):
                try:
                    snapshot = json.loads(snapshot)
                except Exception:
                    snapshot = {}
            result["framing_missing"] = self._missing_framing_fields(snapshot)
        return result
