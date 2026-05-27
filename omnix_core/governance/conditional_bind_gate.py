"""
OMNIX Conditional Bind Gate (CBG) — ADR-135

Resolves Eduardo Monteiro's open question from the SPG exchange (ADR-133):

    "Detection alone exposes the condition — but doesn't necessarily change the outcome."

    "Once ambiguity is detected, how (or whether) the system resolves it
     before consequence is allowed."

ADR-133 (State Provenance Guard) surfaces lineage ambiguity as advisory —
the evaluation proceeds regardless of the verdict. ADR-135 closes that gap:
when ambiguity persists beyond a configurable severity threshold, the bind
is CONDITIONALLY BLOCKED until a qualified human explicitly attests that
the consequence may proceed despite the unresolved lineage ambiguity.

Architecture position:
    Layer 0   — Structural Admissibility Engine  (SAE)
    Layer 0b  — State Provenance Guard           (SPG — ADR-133)
    Layer 0c  — Conditional Bind Gate            ← THIS MODULE (ADR-135)
    Layer 1   — OMNIX Runtime Pipeline (CP-0 … CP-11 + TIE)
    Layer 2   — Trajectory Invariant Engine
    Layer 3   — PQC Evidence & Receipt Layer

The CBG activates ONLY when SPG returns AMBIGUOUS verdict (lineage_singularity < 50
or contradiction_count ≥ 2). SINGULAR and INDETERMINATE states pass through
without creating a gate.

Gate lifecycle:
    PENDING   — gate created, bind blocked, awaiting attestation
    ATTESTED  — human explicitly approved bind; consequence may proceed
    BLOCKED   — human or system explicitly blocked the bind permanently
    EXPIRED   — timeout elapsed (default: 60 min) without attestation; auto-blocks

Design constraints:
    • Fail-safe: any exception returns a safe BindGateResult with gate_required=False
      (fail-open on engine errors — the gate layer itself must not disrupt governance)
    • Additive: does not modify decision_receipts, governance_overrides, or any
      existing table. bind_gate_records is a standalone audit table.
    • Idempotent: evaluate() with the same spg_id returns the existing gate if already created
    • Justification required: attestation requires ≥ ATTEST_MIN_JUSTIFICATION_CHARS
    • Fully auditable: every state transition is timestamped and logged
    • Thread-safe: no shared mutable state; DB is the source of truth

ADR Reference: ADR-135
Regulatory alignment:
    • EU AI Act Art. 14(4)(c) — humans can interpret and override with accountability
    • EU AI Act Art. 9     — risk management traceability at execution boundary
    • NIST AI RMF GOVERN 1.7 — measurable oversight quality
    • MiFID II — pre-trade formation and execution accountability

Author: OMNIX Quantum Ltd — Harold Alberto Nunes Rodelo
Date: 2026-04-28
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger("OMNIX.CBG")


# ── Configuration ─────────────────────────────────────────────────────────────

GATE_TIMEOUT_MINUTES: int   = 60    # PENDING gates expire after this
ATTEST_MIN_JUSTIFICATION_CHARS: int = 80  # Minimum chars for attestation justification
                                           # (stricter than OSE's 50 — binding consequence)
AMBIGUITY_SCORE_THRESHOLD: float = 50.0  # lineage_singularity < this → gate triggers
AMBIGUITY_CONTRADICTION_THRESHOLD: int = 2  # contradiction_count ≥ this → gate triggers
                                            # regardless of score


# ── Enums ─────────────────────────────────────────────────────────────────────

class GateStatus(str, Enum):
    PENDING  = "PENDING"   # Gate active — bind blocked, awaiting attestation
    ATTESTED = "ATTESTED"  # Human approved bind explicitly
    BLOCKED  = "BLOCKED"   # Bind permanently blocked (human or system)
    EXPIRED  = "EXPIRED"   # Timeout elapsed — auto-blocks


class GateVerdict(str, Enum):
    PASS         = "PASS"          # No gate needed — SPG SINGULAR or INDETERMINATE
    GATE_CREATED = "GATE_CREATED"  # Gate created — bind blocked until attested
    GATE_EXISTS  = "GATE_EXISTS"   # Existing gate returned (idempotent)
    ATTESTED     = "ATTESTED"      # Gate already attested — bind allowed
    BLOCKED      = "BLOCKED"       # Gate blocked — bind permanently rejected
    EXPIRED      = "EXPIRED"       # Gate expired — bind auto-blocked


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class BindGateRecord:
    """
    Full record of a conditional bind gate for a specific evaluation.

    Created when SPG returns AMBIGUOUS verdict above the severity threshold.
    Persisted in bind_gate_records table.
    """
    gate_id:              str
    spg_id:               str
    decision_id:          str
    domain:               Optional[str]
    lineage_singularity:  float
    contradiction_count:  int
    spg_verdict:          str               # AMBIGUOUS | INDETERMINATE
    gate_status:          GateStatus
    bind_allowed:         bool              # True only when ATTESTED
    attester_id:          Optional[str]
    justification:        Optional[str]
    block_reason:         Optional[str]
    created_at:           datetime
    expires_at:           datetime
    attested_at:          Optional[datetime]
    blocked_at:           Optional[datetime]
    oversight_session_id: Optional[str]
    gate_hash:            str               # SHA-256(gate_id+spg_id+decision_id)
    adr_reference:        str = "ADR-135"

    def to_dict(self) -> dict:
        return {
            "gate_id":               self.gate_id,
            "spg_id":                self.spg_id,
            "decision_id":           self.decision_id,
            "domain":                self.domain,
            "lineage_singularity":   round(self.lineage_singularity, 2),
            "contradiction_count":   self.contradiction_count,
            "spg_verdict":           self.spg_verdict,
            "gate_status":           self.gate_status.value,
            "bind_allowed":          self.bind_allowed,
            "attester_id":           self.attester_id,
            "justification":         self.justification,
            "block_reason":          self.block_reason,
            "created_at":            self.created_at.isoformat(),
            "expires_at":            self.expires_at.isoformat(),
            "attested_at":           self.attested_at.isoformat() if self.attested_at else None,
            "blocked_at":            self.blocked_at.isoformat() if self.blocked_at else None,
            "oversight_session_id":  self.oversight_session_id,
            "gate_hash":             self.gate_hash,
            "adr_reference":         self.adr_reference,
        }


@dataclass
class BindGateResult:
    """
    Result returned by evaluate() — tells the caller whether a gate was created
    and whether bind is currently allowed.

    bind_allowed=True  → consequence may proceed (no ambiguity, or already attested)
    bind_allowed=False → consequence is blocked (gate PENDING, BLOCKED, or EXPIRED)
    """
    gate_required:        bool
    bind_allowed:         bool
    verdict:              GateVerdict
    reason:               str
    gate_id:              Optional[str]
    lineage_singularity:  float
    contradiction_count:  int
    spg_verdict:          str
    gate_record:          Optional[BindGateRecord]
    adr_reference:        str = "ADR-135"

    def to_dict(self) -> dict:
        return {
            "gate_required":       self.gate_required,
            "bind_allowed":        self.bind_allowed,
            "verdict":             self.verdict.value,
            "reason":              self.reason,
            "gate_id":             self.gate_id,
            "lineage_singularity": round(self.lineage_singularity, 2),
            "contradiction_count": self.contradiction_count,
            "spg_verdict":         self.spg_verdict,
            "gate_record":         self.gate_record.to_dict() if self.gate_record else None,
            "adr_reference":       self.adr_reference,
        }


# ── DB helpers ────────────────────────────────────────────────────────────────

def _get_conn():
    """Lazy psycopg2 connection — avoids import errors in test environments."""
    import psycopg
    db_url = os.environ.get("OMNIX_DB_URL") or os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError(
            "No database URL configured — ConditionalBindGate requires "
            "OMNIX_DB_URL or DATABASE_URL."
        )
    return psycopg.connect(db_url)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _gate_id() -> str:
    return f"CBG-{uuid.uuid4().hex[:16].upper()}"


def _gate_hash(gate_id: str, spg_id: str, decision_id: str) -> str:
    raw = f"{gate_id}:{spg_id}:{decision_id}"
    return "sha256:" + hashlib.sha256(raw.encode()).hexdigest()


# ── Schema ────────────────────────────────────────────────────────────────────

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS bind_gate_records (
    gate_id               VARCHAR(64)   PRIMARY KEY,
    spg_id                VARCHAR(64)   NOT NULL,
    decision_id           VARCHAR(128)  NOT NULL,
    domain                VARCHAR(64),
    lineage_singularity   FLOAT         NOT NULL,
    contradiction_count   INTEGER       NOT NULL DEFAULT 0,
    spg_verdict           VARCHAR(20)   NOT NULL,
    gate_status           VARCHAR(20)   NOT NULL DEFAULT 'PENDING',
    bind_allowed          BOOLEAN       NOT NULL DEFAULT FALSE,
    attester_id           VARCHAR(128),
    justification         TEXT,
    block_reason          TEXT,
    created_at            TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    expires_at            TIMESTAMPTZ   NOT NULL,
    attested_at           TIMESTAMPTZ,
    blocked_at            TIMESTAMPTZ,
    oversight_session_id  VARCHAR(64),
    gate_hash             VARCHAR(80)   NOT NULL,
    metadata              JSONB
);
"""

_CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_cbg_spg_id      ON bind_gate_records (spg_id)",
    "CREATE INDEX IF NOT EXISTS idx_cbg_decision_id ON bind_gate_records (decision_id)",
    "CREATE INDEX IF NOT EXISTS idx_cbg_status      ON bind_gate_records (gate_status)",
    "CREATE INDEX IF NOT EXISTS idx_cbg_expires_at  ON bind_gate_records (expires_at)",
    "CREATE INDEX IF NOT EXISTS idx_cbg_domain      ON bind_gate_records (domain)",
]


# ── Core engine ───────────────────────────────────────────────────────────────

class ConditionalBindGate:
    """
    Conditional Bind Gate — ADR-135.

    Governs the transition from lineage ambiguity detection (SPG) to
    consequence allowance (bind). When SPG returns AMBIGUOUS verdict,
    the CBG creates a gate record and blocks the bind until a qualified
    human explicitly attests that execution may proceed.

    Usage:
        cbg = ConditionalBindGate()
        cbg.ensure_schema()

        # 1. Evaluate after SPG
        result = cbg.evaluate(
            spg_id="SPG-A3F2B1C9",
            spg_verdict="AMBIGUOUS",
            lineage_singularity=28.0,
            contradiction_count=3,
            decision_id="receipt-001",
            domain="trading",
        )

        if not result.bind_allowed:
            # Return gate_id to client — they must attest before proceeding
            return {"blocked": True, "gate_id": result.gate_id}

        # 2. Client attests (separate request, after human review)
        record = cbg.attest(
            gate_id="CBG-A3F2B1C9D0E4F5A6",
            attester_id="harold@omnixquantum.net",
            justification="Reviewed contradictions — market data confirms BULLISH formation despite cross-signal noise. Consequence approved.",
        )

        # 3. Re-evaluate — now ATTESTED, bind allowed
        result = cbg.evaluate(spg_id="SPG-A3F2B1C9", ...)
        assert result.bind_allowed is True
    """

    def ensure_schema(self) -> None:
        """Create bind_gate_records table and indexes if they do not exist."""
        conn = _get_conn()
        try:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(_CREATE_TABLE)
                for idx in _CREATE_INDEXES:
                    cur.execute(idx)
            logger.info("[CBG] Schema OK — bind_gate_records ready")
        except Exception as exc:
            logger.error("[CBG] ensure_schema error: %s", exc)
        finally:
            conn.close()

    # ── Public API ────────────────────────────────────────────────────────────

    def evaluate(
        self,
        *,
        spg_id:               str,
        spg_verdict:          str,
        lineage_singularity:  float,
        contradiction_count:  int,
        decision_id:          str,
        domain:               Optional[str] = None,
        metadata:             Optional[dict] = None,
    ) -> BindGateResult:
        """
        Evaluate whether a conditional bind gate is required for this SPG result.

        Returns:
            BindGateResult with bind_allowed=True  → consequence may proceed
            BindGateResult with bind_allowed=False → consequence blocked; gate_id provided

        Gate trigger conditions (either is sufficient):
            • lineage_singularity < AMBIGUITY_SCORE_THRESHOLD (50)
            • contradiction_count ≥ AMBIGUITY_CONTRADICTION_THRESHOLD (2)
            AND spg_verdict == "AMBIGUOUS"

        Idempotent: if a gate already exists for this spg_id, returns the existing gate
        status without creating a duplicate.

        Fail-safe: any DB exception returns bind_allowed=True with gate_required=False
        (engine errors must not block governance decisions — the gate layer itself
        cannot become a failure point).
        """
        try:
            return self._evaluate(
                spg_id=spg_id,
                spg_verdict=spg_verdict,
                lineage_singularity=lineage_singularity,
                contradiction_count=contradiction_count,
                decision_id=decision_id,
                domain=domain,
                metadata=metadata,
            )
        except Exception as exc:
            logger.error("[CBG] evaluate() error (spg_id=%s): %s", spg_id, exc)
            return BindGateResult(
                gate_required=False,
                bind_allowed=True,
                verdict=GateVerdict.PASS,
                reason="CBG engine error — fail-safe: bind allowed (gate layer must not block)",
                gate_id=None,
                lineage_singularity=lineage_singularity,
                contradiction_count=contradiction_count,
                spg_verdict=spg_verdict,
                gate_record=None,
            )

    def attest(
        self,
        *,
        gate_id:      str,
        attester_id:  str,
        justification: str,
    ) -> BindGateRecord:
        """
        Explicitly attest that consequence may proceed despite lineage ambiguity.

        The attester takes cryptographic ownership of the decision to proceed.
        The justification is permanently stored in the audit trail and embedded
        in any downstream VC via the humanSigner block (ADR-130).

        Args:
            gate_id:      CBG gate identifier (e.g. "CBG-A3F2B1C9D0E4F5A6")
            attester_id:  Human identifier — email, employee ID, or OAuth subject
            justification: Explicit reasoning for allowing bind (≥ ATTEST_MIN_JUSTIFICATION_CHARS)

        Raises:
            ValueError: gate not found, wrong status, justification too short, or expired
        """
        if len(justification.strip()) < ATTEST_MIN_JUSTIFICATION_CHARS:
            raise ValueError(
                f"Attestation justification too short: {len(justification.strip())} chars. "
                f"Minimum required: {ATTEST_MIN_JUSTIFICATION_CHARS} chars. "
                "The justification must explicitly document why bind is appropriate "
                "despite the detected lineage ambiguity."
            )

        conn = _get_conn()
        try:
            with conn.cursor() as cur:
                # Fetch current gate
                cur.execute(
                    "SELECT gate_status, expires_at FROM bind_gate_records WHERE gate_id = %s",
                    (gate_id,),
                )
                row = cur.fetchone()
                if not row:
                    raise ValueError(f"Gate not found: {gate_id}")

                status, expires_at = row
                if status == GateStatus.ATTESTED.value:
                    raise ValueError(f"Gate {gate_id} is already ATTESTED.")
                if status in (GateStatus.BLOCKED.value, GateStatus.EXPIRED.value):
                    raise ValueError(
                        f"Gate {gate_id} is {status} — attestation not allowed. "
                        "A new evaluation is required."
                    )
                if _now() >= expires_at:
                    # Auto-expire and reject
                    cur.execute(
                        """UPDATE bind_gate_records
                           SET gate_status = 'EXPIRED', blocked_at = %s
                           WHERE gate_id = %s""",
                        (_now(), gate_id),
                    )
                    conn.commit()
                    raise ValueError(
                        f"Gate {gate_id} has expired. "
                        f"The {GATE_TIMEOUT_MINUTES}-minute attestation window has closed. "
                        "Submit a new evaluation to open a fresh gate."
                    )

                now = _now()
                cur.execute(
                    """UPDATE bind_gate_records
                       SET gate_status  = 'ATTESTED',
                           bind_allowed = TRUE,
                           attester_id  = %s,
                           justification = %s,
                           attested_at  = %s
                       WHERE gate_id = %s""",
                    (attester_id, justification.strip(), now, gate_id),
                )
                conn.commit()

            logger.info(
                "[CBG] Gate ATTESTED gate_id=%s attester=%s",
                gate_id, attester_id,
            )
            return self._fetch_record(gate_id)
        except ValueError:
            raise
        except Exception as exc:
            conn.rollback()
            logger.error("[CBG] attest() error gate_id=%s: %s", gate_id, exc)
            raise
        finally:
            conn.close()

    def block(
        self,
        *,
        gate_id:     str,
        reason:      str,
        blocked_by:  Optional[str] = None,
    ) -> BindGateRecord:
        """
        Permanently block a bind gate — consequence will not proceed.

        May be called by a human reviewer or by the system after policy evaluation.
        BLOCKED is a terminal state — it cannot be reversed. A new evaluation
        is required to re-open the question.

        Args:
            gate_id:    CBG gate identifier
            reason:     Explanation for the block (stored in audit trail)
            blocked_by: Optional human/system identifier
        """
        conn = _get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT gate_status FROM bind_gate_records WHERE gate_id = %s",
                    (gate_id,),
                )
                row = cur.fetchone()
                if not row:
                    raise ValueError(f"Gate not found: {gate_id}")
                status = row[0]
                if status in (GateStatus.ATTESTED.value,):
                    raise ValueError(
                        f"Gate {gate_id} is already ATTESTED — cannot be blocked. "
                        "An attested bind cannot be retroactively blocked via the CBG."
                    )
                if status == GateStatus.BLOCKED.value:
                    raise ValueError(f"Gate {gate_id} is already BLOCKED.")

                now = _now()
                cur.execute(
                    """UPDATE bind_gate_records
                       SET gate_status  = 'BLOCKED',
                           bind_allowed = FALSE,
                           block_reason = %s,
                           attester_id  = %s,
                           blocked_at   = %s
                       WHERE gate_id = %s""",
                    (reason, blocked_by, now, gate_id),
                )
                conn.commit()

            logger.info("[CBG] Gate BLOCKED gate_id=%s blocked_by=%s", gate_id, blocked_by)
            return self._fetch_record(gate_id)
        except ValueError:
            raise
        except Exception as exc:
            conn.rollback()
            logger.error("[CBG] block() error gate_id=%s: %s", gate_id, exc)
            raise
        finally:
            conn.close()

    def query(self, gate_id: str) -> BindGateRecord:
        """
        Retrieve the current state of a bind gate.

        Auto-expires the gate if the timeout has elapsed and status is still PENDING.

        Raises:
            ValueError: gate not found
        """
        conn = _get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT gate_status, expires_at FROM bind_gate_records WHERE gate_id = %s",
                    (gate_id,),
                )
                row = cur.fetchone()
                if not row:
                    raise ValueError(f"Gate not found: {gate_id}")
                status, expires_at = row
                if status == GateStatus.PENDING.value and _now() >= expires_at:
                    cur.execute(
                        """UPDATE bind_gate_records
                           SET gate_status = 'EXPIRED', blocked_at = %s
                           WHERE gate_id = %s""",
                        (_now(), gate_id),
                    )
                    conn.commit()
            return self._fetch_record(gate_id)
        except ValueError:
            raise
        except Exception as exc:
            logger.error("[CBG] query() error gate_id=%s: %s", gate_id, exc)
            raise
        finally:
            conn.close()

    def expire_stale(self) -> int:
        """
        Expire all PENDING gates whose timeout has elapsed.

        Returns the number of gates expired. Intended for periodic maintenance
        (cron job or admin endpoint).
        """
        conn = _get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE bind_gate_records
                       SET gate_status = 'EXPIRED',
                           blocked_at  = %s
                       WHERE gate_status = 'PENDING'
                         AND expires_at <= %s
                       RETURNING gate_id""",
                    (_now(), _now()),
                )
                rows = cur.fetchall()
                conn.commit()
            count = len(rows)
            if count:
                logger.info("[CBG] Expired %d stale gate(s)", count)
            return count
        except Exception as exc:
            conn.rollback()
            logger.error("[CBG] expire_stale() error: %s", exc)
            return 0
        finally:
            conn.close()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _evaluate(
        self,
        *,
        spg_id:               str,
        spg_verdict:          str,
        lineage_singularity:  float,
        contradiction_count:  int,
        decision_id:          str,
        domain:               Optional[str],
        metadata:             Optional[dict],
    ) -> BindGateResult:
        """Internal evaluate — raises on error (caller wraps in fail-safe)."""

        # 1. SINGULAR or INDETERMINATE → no gate required, bind allowed immediately
        if spg_verdict != "AMBIGUOUS":
            return BindGateResult(
                gate_required=False,
                bind_allowed=True,
                verdict=GateVerdict.PASS,
                reason=(
                    f"SPG verdict is {spg_verdict} — lineage singularity is above "
                    "the ambiguity threshold. Bind allowed without attestation."
                ),
                gate_id=None,
                lineage_singularity=lineage_singularity,
                contradiction_count=contradiction_count,
                spg_verdict=spg_verdict,
                gate_record=None,
            )

        # 2. AMBIGUOUS — check if gate already exists for this spg_id (idempotency)
        existing = self._find_gate_by_spg_id(spg_id)
        if existing:
            # Auto-expire if timeout elapsed
            if (existing.gate_status == GateStatus.PENDING
                    and _now() >= existing.expires_at):
                existing = self._auto_expire(existing.gate_id)

            verdict = GateVerdict.GATE_EXISTS
            if existing.gate_status == GateStatus.ATTESTED:
                verdict = GateVerdict.ATTESTED
            elif existing.gate_status == GateStatus.BLOCKED:
                verdict = GateVerdict.BLOCKED
            elif existing.gate_status == GateStatus.EXPIRED:
                verdict = GateVerdict.EXPIRED

            return BindGateResult(
                gate_required=True,
                bind_allowed=existing.bind_allowed,
                verdict=verdict,
                reason=self._reason_for_status(existing.gate_status, existing.gate_id),
                gate_id=existing.gate_id,
                lineage_singularity=lineage_singularity,
                contradiction_count=contradiction_count,
                spg_verdict=spg_verdict,
                gate_record=existing,
            )

        # 3. AMBIGUOUS + no existing gate → create new gate
        score_triggers  = lineage_singularity < AMBIGUITY_SCORE_THRESHOLD
        contra_triggers = contradiction_count >= AMBIGUITY_CONTRADICTION_THRESHOLD

        if not (score_triggers or contra_triggers):
            # AMBIGUOUS verdict but below both thresholds — treat as advisory only
            return BindGateResult(
                gate_required=False,
                bind_allowed=True,
                verdict=GateVerdict.PASS,
                reason=(
                    "SPG verdict is AMBIGUOUS but below gate trigger thresholds "
                    f"(score={lineage_singularity:.1f} ≥ {AMBIGUITY_SCORE_THRESHOLD} "
                    f"and contradictions={contradiction_count} < "
                    f"{AMBIGUITY_CONTRADICTION_THRESHOLD}). Advisory mode applies."
                ),
                gate_id=None,
                lineage_singularity=lineage_singularity,
                contradiction_count=contradiction_count,
                spg_verdict=spg_verdict,
                gate_record=None,
            )

        gate = self._create_gate(
            spg_id=spg_id,
            spg_verdict=spg_verdict,
            lineage_singularity=lineage_singularity,
            contradiction_count=contradiction_count,
            decision_id=decision_id,
            domain=domain,
            metadata=metadata,
        )

        return BindGateResult(
            gate_required=True,
            bind_allowed=False,
            verdict=GateVerdict.GATE_CREATED,
            reason=(
                f"Lineage ambiguity gate created. "
                f"lineage_singularity={lineage_singularity:.1f} "
                f"contradictions={contradiction_count}. "
                f"Bind is blocked until explicit attestation. "
                f"Gate expires in {GATE_TIMEOUT_MINUTES} minutes."
            ),
            gate_id=gate.gate_id,
            lineage_singularity=lineage_singularity,
            contradiction_count=contradiction_count,
            spg_verdict=spg_verdict,
            gate_record=gate,
        )

    def _create_gate(
        self,
        *,
        spg_id:               str,
        spg_verdict:          str,
        lineage_singularity:  float,
        contradiction_count:  int,
        decision_id:          str,
        domain:               Optional[str],
        metadata:             Optional[dict],
    ) -> BindGateRecord:
        gid     = _gate_id()
        now     = _now()
        expires = now + timedelta(minutes=GATE_TIMEOUT_MINUTES)
        ghash   = _gate_hash(gid, spg_id, decision_id)

        conn = _get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO bind_gate_records
                       (gate_id, spg_id, decision_id, domain,
                        lineage_singularity, contradiction_count, spg_verdict,
                        gate_status, bind_allowed, created_at, expires_at,
                        gate_hash, metadata)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,'PENDING',FALSE,%s,%s,%s,%s)""",
                    (
                        gid, spg_id, decision_id, domain,
                        lineage_singularity, contradiction_count, spg_verdict,
                        now, expires, ghash,
                        json.dumps(metadata) if metadata else None,
                    ),
                )
                conn.commit()
            logger.info(
                "[CBG] Gate CREATED gate_id=%s spg_id=%s score=%.1f contradictions=%d",
                gid, spg_id, lineage_singularity, contradiction_count,
            )
        except Exception as exc:
            conn.rollback()
            logger.error("[CBG] _create_gate error: %s", exc)
            raise
        finally:
            conn.close()

        return BindGateRecord(
            gate_id=gid,
            spg_id=spg_id,
            decision_id=decision_id,
            domain=domain,
            lineage_singularity=lineage_singularity,
            contradiction_count=contradiction_count,
            spg_verdict=spg_verdict,
            gate_status=GateStatus.PENDING,
            bind_allowed=False,
            attester_id=None,
            justification=None,
            block_reason=None,
            created_at=now,
            expires_at=expires,
            attested_at=None,
            blocked_at=None,
            oversight_session_id=None,
            gate_hash=ghash,
        )

    def _fetch_record(self, gate_id: str) -> BindGateRecord:
        """Fetch a BindGateRecord from DB by gate_id."""
        conn = _get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT gate_id, spg_id, decision_id, domain,
                              lineage_singularity, contradiction_count, spg_verdict,
                              gate_status, bind_allowed, attester_id, justification,
                              block_reason, created_at, expires_at, attested_at,
                              blocked_at, oversight_session_id, gate_hash
                       FROM bind_gate_records WHERE gate_id = %s""",
                    (gate_id,),
                )
                row = cur.fetchone()
            if not row:
                raise ValueError(f"Gate not found after write: {gate_id}")
            return self._row_to_record(row)
        finally:
            conn.close()

    def _find_gate_by_spg_id(self, spg_id: str) -> Optional[BindGateRecord]:
        """Return existing gate for this spg_id, or None."""
        conn = _get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT gate_id, spg_id, decision_id, domain,
                              lineage_singularity, contradiction_count, spg_verdict,
                              gate_status, bind_allowed, attester_id, justification,
                              block_reason, created_at, expires_at, attested_at,
                              blocked_at, oversight_session_id, gate_hash
                       FROM bind_gate_records WHERE spg_id = %s
                       ORDER BY created_at DESC LIMIT 1""",
                    (spg_id,),
                )
                row = cur.fetchone()
            if not row:
                return None
            return self._row_to_record(row)
        except Exception as exc:
            logger.error("[CBG] _find_gate_by_spg_id error spg_id=%s: %s", spg_id, exc)
            return None
        finally:
            conn.close()

    def _auto_expire(self, gate_id: str) -> BindGateRecord:
        """Auto-expire a PENDING gate whose timeout has elapsed."""
        conn = _get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE bind_gate_records
                       SET gate_status = 'EXPIRED', blocked_at = %s
                       WHERE gate_id = %s""",
                    (_now(), gate_id),
                )
                conn.commit()
            logger.info("[CBG] Gate auto-expired gate_id=%s", gate_id)
        except Exception as exc:
            conn.rollback()
            logger.error("[CBG] _auto_expire error gate_id=%s: %s", gate_id, exc)
        finally:
            conn.close()
        return self._fetch_record(gate_id)

    @staticmethod
    def _row_to_record(row: tuple) -> BindGateRecord:
        (
            gate_id, spg_id, decision_id, domain,
            lineage_singularity, contradiction_count, spg_verdict,
            gate_status_str, bind_allowed, attester_id, justification,
            block_reason, created_at, expires_at, attested_at,
            blocked_at, oversight_session_id, gate_hash,
        ) = row
        return BindGateRecord(
            gate_id=gate_id,
            spg_id=spg_id,
            decision_id=decision_id,
            domain=domain,
            lineage_singularity=float(lineage_singularity),
            contradiction_count=int(contradiction_count),
            spg_verdict=spg_verdict,
            gate_status=GateStatus(gate_status_str),
            bind_allowed=bool(bind_allowed),
            attester_id=attester_id,
            justification=justification,
            block_reason=block_reason,
            created_at=created_at,
            expires_at=expires_at,
            attested_at=attested_at,
            blocked_at=blocked_at,
            oversight_session_id=oversight_session_id,
            gate_hash=gate_hash,
        )

    @staticmethod
    def _reason_for_status(status: GateStatus, gate_id: str) -> str:
        reasons = {
            GateStatus.PENDING:  (
                f"Gate {gate_id} is PENDING — bind blocked. "
                f"Submit attestation to allow consequence to proceed."
            ),
            GateStatus.ATTESTED: (
                f"Gate {gate_id} is ATTESTED — bind explicitly approved. "
                "Consequence may proceed."
            ),
            GateStatus.BLOCKED:  (
                f"Gate {gate_id} is BLOCKED — bind permanently rejected. "
                "A new evaluation is required."
            ),
            GateStatus.EXPIRED:  (
                f"Gate {gate_id} has EXPIRED — the attestation window closed. "
                "A new evaluation is required."
            ),
        }
        return reasons.get(status, f"Gate {gate_id} status: {status.value}")


# ── Module-level singleton ─────────────────────────────────────────────────────

_cbg_instance: Optional[ConditionalBindGate] = None


def get_conditional_bind_gate() -> ConditionalBindGate:
    """Return the module-level ConditionalBindGate singleton."""
    global _cbg_instance
    if _cbg_instance is None:
        _cbg_instance = ConditionalBindGate()
    return _cbg_instance
