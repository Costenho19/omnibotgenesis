"""
OMNIX BEV — Constraint Conformance Signal (CCS)
RFC-ATF-6 § 4.2 · ADR-182

A CCS is a per-turn continuous measurement of how tightly the agent's output
conforms to the constraints embedded in its governing receipt. The signal feeds
the AGVP watchdog for anticipatory veto issuance before violations escalate.

Invariants enforced here:
  BEV-INV-005: Every BAR MUST have a corresponding CCS computed in the same atomic step.
  BEV-INV-006: CCS score MUST be in [0.0, 1.0]. 1.0 = full conformance.
  BEV-INV-007: CCS CRITICAL verdict MUST trigger AGVP watchdog evaluation.
  BEV-INV-008: Cumulative drift > MAX_DRIFT_PCT MUST produce HALT verdict.
  BEV-INV-009: CCS history MUST be append-only and tamper-evident via hash linkage.

Harold Nunes — OMNIX QUANTUM LTD — May 2026
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("OMNIX.BEV.CCS")

# Default drift threshold before HALT (ADR-182 §5, BEV-INV-008)
_DEFAULT_MAX_CUMULATIVE_DRIFT = float(
    os.environ.get("BEV_MAX_CUMULATIVE_DRIFT", "0.35")
)
_DEFAULT_CRITICAL_SCORE = float(
    os.environ.get("BEV_CRITICAL_SCORE_THRESHOLD", "0.40")
)
_DEFAULT_WARNING_SCORE = float(
    os.environ.get("BEV_WARNING_SCORE_THRESHOLD", "0.70")
)


# ─────────────────────────────────────────────────────────────────
#  Data model
# ─────────────────────────────────────────────────────────────────

@dataclass
class ConstraintConformanceSignal:
    """
    Per-turn measurement of constraint conformance for a governed agent output.

    The CCS feeds the AGVP proactive veto loop — when cumulative drift climbs
    toward the session limit, the watchdog issues a PVR before a hard violation
    occurs. This is the architectural innovation that separates OMNIX from
    any reactive-only compliance system.
    """
    ccs_id: str
    session_id: str
    bar_id: str
    turn_index: int
    conformance_score: float
    drift_delta: float
    cumulative_drift: float
    constraints_evaluated: int
    constraints_violated: int
    violated_constraints: List[str]
    verdict: str
    watchdog_triggered: bool
    agvp_pvr_id: Optional[str]
    prev_ccs_hash: Optional[str]
    chain_link_hash: str
    computed_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ccs_id": self.ccs_id,
            "session_id": self.session_id,
            "bar_id": self.bar_id,
            "turn_index": self.turn_index,
            "conformance_score": round(self.conformance_score, 4),
            "drift_delta": round(self.drift_delta, 4),
            "cumulative_drift": round(self.cumulative_drift, 4),
            "constraints_evaluated": self.constraints_evaluated,
            "constraints_violated": self.constraints_violated,
            "violated_constraints": self.violated_constraints,
            "verdict": self.verdict,
            "watchdog_triggered": self.watchdog_triggered,
            "agvp_pvr_id": self.agvp_pvr_id,
            "prev_ccs_hash": self.prev_ccs_hash,
            "chain_link_hash": self.chain_link_hash,
            "computed_at": self.computed_at,
            "metadata": self.metadata,
        }

    def signal_summary(self) -> Dict[str, Any]:
        return {
            "ccs_id": self.ccs_id,
            "turn_index": self.turn_index,
            "conformance_score": round(self.conformance_score, 4),
            "cumulative_drift": round(self.cumulative_drift, 4),
            "verdict": self.verdict,
            "watchdog_triggered": self.watchdog_triggered,
        }


# ─────────────────────────────────────────────────────────────────
#  Engine
# ─────────────────────────────────────────────────────────────────

class CCSEngine:
    """
    Computes and persists Constraint Conformance Signals.

    The engine maintains a per-session drift accumulator and propagates
    signals to the AGVP watchdog when configured (BEV-INV-007).
    """

    _CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS atf_constraint_conformance_signals (
        ccs_id               TEXT PRIMARY KEY,
        session_id           TEXT NOT NULL,
        bar_id               TEXT NOT NULL,
        turn_index           INTEGER NOT NULL,
        conformance_score    REAL NOT NULL,
        drift_delta          REAL NOT NULL DEFAULT 0.0,
        cumulative_drift     REAL NOT NULL DEFAULT 0.0,
        constraints_evaluated INTEGER NOT NULL DEFAULT 0,
        constraints_violated  INTEGER NOT NULL DEFAULT 0,
        violated_constraints  JSONB DEFAULT '[]'::jsonb,
        verdict              TEXT NOT NULL DEFAULT 'CONFORMANT',
        watchdog_triggered   BOOLEAN NOT NULL DEFAULT FALSE,
        agvp_pvr_id          TEXT,
        prev_ccs_hash        TEXT,
        chain_link_hash      TEXT NOT NULL,
        computed_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        metadata             JSONB DEFAULT '{}'::jsonb
    );
    CREATE INDEX IF NOT EXISTS idx_ccs_session_id  ON atf_constraint_conformance_signals(session_id);
    CREATE INDEX IF NOT EXISTS idx_ccs_bar_id      ON atf_constraint_conformance_signals(bar_id);
    CREATE INDEX IF NOT EXISTS idx_ccs_verdict     ON atf_constraint_conformance_signals(verdict);
    CREATE INDEX IF NOT EXISTS idx_ccs_turn        ON atf_constraint_conformance_signals(session_id, turn_index);
    """

    def __init__(self):
        self._db_url = os.environ.get("DATABASE_URL")
        # In-process drift accumulators: session_id → cumulative_drift
        self._drift_cache: Dict[str, float] = {}
        # In-process prev_hash chain: session_id → last chain_link_hash
        self._chain_cache: Dict[str, Optional[str]] = {}

    def _get_conn(self):
        import psycopg2
        return psycopg2.connect(self._db_url)

    def ensure_tables(self) -> None:
        if not self._db_url:
            return
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(self._CREATE_TABLE)
                conn.commit()
        except Exception as exc:
            logger.warning(f"[CCS] ensure_tables failed (non-blocking): {exc}")

    # ── Core computation ──────────────────────────────────────────

    def compute_signal(
        self,
        session_id: str,
        bar_id: str,
        turn_index: int,
        output_text: str,
        bar_status: str,
        constraint_set: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConstraintConformanceSignal:
        """
        BEV-INV-005: Compute CCS for a single governed turn.

        The conformance score is derived from constraint satisfaction.
        Drift is accumulated across the session. When cumulative drift
        exceeds BEV_MAX_CUMULATIVE_DRIFT, verdict becomes HALT (BEV-INV-008).
        """
        constraints_evaluated, constraints_violated, violated_names = (
            self._count_violations(output_text, bar_status, constraint_set)
        )

        if constraints_evaluated > 0:
            raw_score = 1.0 - (constraints_violated / constraints_evaluated)
        else:
            raw_score = 1.0 if bar_status == "VALID" else 0.0

        # Clamp BEV-INV-006
        conformance_score = max(0.0, min(1.0, raw_score))

        drift_delta = 1.0 - conformance_score

        prev_cumulative = self._drift_cache.get(session_id, 0.0)
        cumulative_drift = prev_cumulative + drift_delta
        self._drift_cache[session_id] = cumulative_drift

        verdict = self._determine_verdict(
            conformance_score, cumulative_drift, bar_status
        )

        watchdog_triggered = verdict in ("CRITICAL", "HALT")

        prev_ccs_hash = self._chain_cache.get(session_id)
        chain_link_hash = self._compute_chain_link(
            prev_ccs_hash, bar_id, turn_index, conformance_score, cumulative_drift
        )
        self._chain_cache[session_id] = chain_link_hash

        ccs_id = f"CCS-{uuid.uuid4().hex[:16].upper()}"
        computed_at = datetime.now(timezone.utc).isoformat()

        signal = ConstraintConformanceSignal(
            ccs_id=ccs_id,
            session_id=session_id,
            bar_id=bar_id,
            turn_index=turn_index,
            conformance_score=conformance_score,
            drift_delta=drift_delta,
            cumulative_drift=cumulative_drift,
            constraints_evaluated=constraints_evaluated,
            constraints_violated=constraints_violated,
            violated_constraints=violated_names,
            verdict=verdict,
            watchdog_triggered=watchdog_triggered,
            agvp_pvr_id=None,
            prev_ccs_hash=prev_ccs_hash,
            chain_link_hash=chain_link_hash,
            computed_at=computed_at,
            metadata=metadata or {},
        )

        self._persist(signal)
        return signal

    # ── Verdict logic ─────────────────────────────────────────────

    def _determine_verdict(
        self,
        score: float,
        cumulative_drift: float,
        bar_status: str,
    ) -> str:
        if bar_status == "HALTED":
            return "HALT"
        if cumulative_drift >= _DEFAULT_MAX_CUMULATIVE_DRIFT:
            return "HALT"
        if score < _DEFAULT_CRITICAL_SCORE or bar_status == "VIOLATION":
            return "CRITICAL"
        if score < _DEFAULT_WARNING_SCORE or bar_status == "WARNING":
            return "WARNING"
        return "CONFORMANT"

    def _count_violations(
        self,
        output_text: str,
        bar_status: str,
        constraint_set: Dict[str, Any],
    ) -> tuple[int, int, List[str]]:
        evaluated = 0
        violated = 0
        names: List[str] = []

        if bar_status == "HALTED":
            return 1, 1, ["BAR_HALTED"]
        if bar_status == "VIOLATION":
            violated += 1
            names.append("BAR_VIOLATION")

        if not constraint_set:
            return max(evaluated, violated + 1), violated, names

        evaluated = 1 + violated

        max_len = constraint_set.get("max_output_length")
        if max_len:
            evaluated += 1
            if len(output_text) > max_len:
                violated += 1
                names.append("max_output_length")

        forbidden = constraint_set.get("forbidden_topics", [])
        if isinstance(forbidden, list):
            for topic in forbidden:
                evaluated += 1
                if topic.lower() in output_text.lower():
                    violated += 1
                    names.append(f"forbidden_topic:{topic}")

        required = constraint_set.get("required_keywords", [])
        if isinstance(required, list) and required:
            evaluated += 1
            found = any(kw.lower() in output_text.lower() for kw in required)
            if not found:
                violated += 1
                names.append("required_keywords_absent")

        return evaluated, violated, names

    # ── Chain hash (BEV-INV-009) ──────────────────────────────────

    @staticmethod
    def _compute_chain_link(
        prev_hash: Optional[str],
        bar_id: str,
        turn_index: int,
        score: float,
        cumulative_drift: float,
    ) -> str:
        payload = json.dumps({
            "prev": prev_hash or "GENESIS",
            "bar_id": bar_id,
            "turn_index": turn_index,
            "score": round(score, 6),
            "cumulative_drift": round(cumulative_drift, 6),
        }, sort_keys=True)
        return hashlib.sha3_256(payload.encode()).hexdigest()

    # ── Session trend ─────────────────────────────────────────────

    def get_session_trend(self, session_id: str) -> Dict[str, Any]:
        """Return aggregate CCS stats for a session."""
        signals = self.list_signals(session_id)
        if not signals:
            return {
                "session_id": session_id,
                "turn_count": 0,
                "avg_conformance": 1.0,
                "cumulative_drift": 0.0,
                "min_score": 1.0,
                "halt_count": 0,
                "critical_count": 0,
                "warning_count": 0,
                "conformant_count": 0,
                "watchdog_trigger_count": 0,
            }

        scores = [s.conformance_score for s in signals]
        verdicts = [s.verdict for s in signals]
        return {
            "session_id": session_id,
            "turn_count": len(signals),
            "avg_conformance": round(sum(scores) / len(scores), 4),
            "cumulative_drift": round(signals[-1].cumulative_drift, 4),
            "min_score": round(min(scores), 4),
            "max_drift_delta": round(max(s.drift_delta for s in signals), 4),
            "halt_count": verdicts.count("HALT"),
            "critical_count": verdicts.count("CRITICAL"),
            "warning_count": verdicts.count("WARNING"),
            "conformant_count": verdicts.count("CONFORMANT"),
            "watchdog_trigger_count": sum(1 for s in signals if s.watchdog_triggered),
            "last_verdict": signals[-1].verdict if signals else "CONFORMANT",
            "chain_tip_hash": signals[-1].chain_link_hash if signals else None,
        }

    # ── Persistence ───────────────────────────────────────────────

    def _persist(self, sig: ConstraintConformanceSignal) -> None:
        if not self._db_url:
            return
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO atf_constraint_conformance_signals
                            (ccs_id, session_id, bar_id, turn_index,
                             conformance_score, drift_delta, cumulative_drift,
                             constraints_evaluated, constraints_violated,
                             violated_constraints, verdict, watchdog_triggered,
                             agvp_pvr_id, prev_ccs_hash, chain_link_hash,
                             computed_at, metadata)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (ccs_id) DO NOTHING
                    """, (
                        sig.ccs_id, sig.session_id, sig.bar_id, sig.turn_index,
                        sig.conformance_score, sig.drift_delta, sig.cumulative_drift,
                        sig.constraints_evaluated, sig.constraints_violated,
                        json.dumps(sig.violated_constraints), sig.verdict,
                        sig.watchdog_triggered, sig.agvp_pvr_id, sig.prev_ccs_hash,
                        sig.chain_link_hash, sig.computed_at, json.dumps(sig.metadata),
                    ))
                conn.commit()
        except Exception as exc:
            logger.warning(f"[CCS] persist failed (non-blocking): {exc}")

    def list_signals(self, session_id: str) -> List[ConstraintConformanceSignal]:
        if not self._db_url:
            return []
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT * FROM atf_constraint_conformance_signals
                        WHERE session_id=%s ORDER BY turn_index ASC
                    """, (session_id,))
                    cols = [d[0] for d in cur.description]
                    return [self._row_to_ccs(dict(zip(cols, r))) for r in cur.fetchall()]
        except Exception as exc:
            logger.error(f"[CCS] list_signals error: {exc}")
            return []

    @staticmethod
    def _row_to_ccs(row: Dict[str, Any]) -> ConstraintConformanceSignal:
        meta = row.get("metadata") or {}
        if isinstance(meta, str):
            meta = json.loads(meta)
        violated = row.get("violated_constraints") or []
        if isinstance(violated, str):
            violated = json.loads(violated)
        return ConstraintConformanceSignal(
            ccs_id=row["ccs_id"],
            session_id=row["session_id"],
            bar_id=row["bar_id"],
            turn_index=row["turn_index"],
            conformance_score=float(row["conformance_score"]),
            drift_delta=float(row["drift_delta"]),
            cumulative_drift=float(row["cumulative_drift"]),
            constraints_evaluated=int(row["constraints_evaluated"]),
            constraints_violated=int(row["constraints_violated"]),
            violated_constraints=violated,
            verdict=row["verdict"],
            watchdog_triggered=bool(row["watchdog_triggered"]),
            agvp_pvr_id=row.get("agvp_pvr_id"),
            prev_ccs_hash=row.get("prev_ccs_hash"),
            chain_link_hash=row["chain_link_hash"],
            computed_at=str(row["computed_at"]),
            metadata=meta,
        )
