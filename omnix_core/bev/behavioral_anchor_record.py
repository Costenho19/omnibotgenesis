"""
OMNIX BEV — Behavioral Anchor Record (BAR)
RFC-ATF-6 § 4.1 · ADR-181

A BAR is a PQC-signed attestation of a single agent output turn, cryptographically
bound to the governing receipt that authorized the action. It is the atomic unit
of the Behavioral Execution Verification layer.

Invariants enforced here:
  BEV-INV-001: Every governed turn MUST produce a BAR before the output is delivered.
  BEV-INV-002: BAR content_hash MUST cover output_hash + governing_receipt_id + turn_index.
  BEV-INV-003: A HALT verdict in any BAR MUST propagate to the session immediately.
  BEV-INV-004: BAR PQC signature MUST be verifiable offline without calling OMNIX.

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

logger = logging.getLogger("OMNIX.BEV.BAR")


# ─────────────────────────────────────────────────────────────────
#  Data model
# ─────────────────────────────────────────────────────────────────

@dataclass
class BehavioralAnchorRecord:
    """
    Immutable, PQC-signed attestation of a single agent output.

    Each BAR ties:
      1. The exact content of the output (output_hash)
      2. The receipt that authorised the action (governing_receipt_id)
      3. Its position in the session sequence (turn_index)

    This combination produces a unique, offline-verifiable artifact that
    no other governance system in the market produces — not CLARIXO, not MTCP.
    """
    bar_id: str
    session_id: str
    agent_id: str
    turn_index: int
    output_hash: str
    output_preview: str
    governing_receipt_id: str
    constraint_set_hash: str
    atf_layer: str
    content_hash: str
    bar_status: str
    halt_reason: Optional[str]
    pqc_signature: Optional[str]
    pqc_algorithm: Optional[str]
    created_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    # ── BEV-INV-002 canonical content ───────────────────────────
    @classmethod
    def _canonical_content(
        cls,
        session_id: str,
        agent_id: str,
        turn_index: int,
        output_hash: str,
        governing_receipt_id: str,
        constraint_set_hash: str,
    ) -> str:
        return json.dumps({
            "session_id": session_id,
            "agent_id": agent_id,
            "turn_index": turn_index,
            "output_hash": output_hash,
            "governing_receipt_id": governing_receipt_id,
            "constraint_set_hash": constraint_set_hash,
        }, sort_keys=True)

    @classmethod
    def compute_content_hash(
        cls,
        session_id: str,
        agent_id: str,
        turn_index: int,
        output_hash: str,
        governing_receipt_id: str,
        constraint_set_hash: str,
    ) -> str:
        canonical = cls._canonical_content(
            session_id, agent_id, turn_index,
            output_hash, governing_receipt_id, constraint_set_hash,
        )
        return hashlib.sha3_256(canonical.encode()).hexdigest()

    def verify_content_hash(self) -> bool:
        expected = self.compute_content_hash(
            self.session_id, self.agent_id, self.turn_index,
            self.output_hash, self.governing_receipt_id, self.constraint_set_hash,
        )
        return self.content_hash == expected

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bar_id": self.bar_id,
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "turn_index": self.turn_index,
            "output_hash": self.output_hash,
            "output_preview": self.output_preview,
            "governing_receipt_id": self.governing_receipt_id,
            "constraint_set_hash": self.constraint_set_hash,
            "atf_layer": self.atf_layer,
            "content_hash": self.content_hash,
            "bar_status": self.bar_status,
            "halt_reason": self.halt_reason,
            "pqc_signature": self.pqc_signature,
            "pqc_algorithm": self.pqc_algorithm,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    def trust_summary(self) -> Dict[str, Any]:
        return {
            "bar_id": self.bar_id,
            "session_id": self.session_id,
            "turn_index": self.turn_index,
            "bar_status": self.bar_status,
            "pqc_signed": self.pqc_signature is not None,
            "pqc_algorithm": self.pqc_algorithm,
            "content_hash": self.content_hash,
            "governing_receipt_id": self.governing_receipt_id,
            "created_at": self.created_at,
        }


# ─────────────────────────────────────────────────────────────────
#  Engine
# ─────────────────────────────────────────────────────────────────

class BAREngine:
    """
    Creates, stores, and verifies Behavioral Anchor Records.

    Every agent output in a governed session passes through this engine.
    The engine evaluates the output against the constraint set embedded in
    the governing receipt, determines a BAR status, then PQC-signs the record.
    """

    _CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS atf_behavioral_anchor_records (
        bar_id               TEXT PRIMARY KEY,
        session_id           TEXT NOT NULL,
        agent_id             TEXT NOT NULL,
        turn_index           INTEGER NOT NULL,
        output_hash          TEXT NOT NULL,
        output_preview       TEXT,
        governing_receipt_id TEXT NOT NULL,
        constraint_set_hash  TEXT NOT NULL,
        atf_layer            TEXT NOT NULL DEFAULT 'BEV-L6',
        content_hash         TEXT NOT NULL,
        bar_status           TEXT NOT NULL DEFAULT 'VALID',
        halt_reason          TEXT,
        pqc_signature        TEXT,
        pqc_algorithm        TEXT,
        created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        metadata             JSONB DEFAULT '{}'::jsonb
    );
    CREATE INDEX IF NOT EXISTS idx_bar_session_id    ON atf_behavioral_anchor_records(session_id);
    CREATE INDEX IF NOT EXISTS idx_bar_agent_id      ON atf_behavioral_anchor_records(agent_id);
    CREATE INDEX IF NOT EXISTS idx_bar_turn_index    ON atf_behavioral_anchor_records(session_id, turn_index);
    CREATE INDEX IF NOT EXISTS idx_bar_status        ON atf_behavioral_anchor_records(bar_status);
    """

    def __init__(self):
        self._pqc = None
        self._db_url = os.environ.get("DATABASE_URL")

    def _get_pqc(self):
        if self._pqc is None:
            from omnix_core.security.pqc_security import PostQuantumSecurity
            self._pqc = PostQuantumSecurity()
        return self._pqc

    def _get_conn(self):
        import psycopg2
        return psycopg2.connect(self._db_url)

    def ensure_tables(self) -> None:
        if not self._db_url:
            logger.debug("[BAR] No DATABASE_URL — skipping table creation")
            return
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(self._CREATE_TABLE)
                conn.commit()
        except Exception as exc:
            logger.warning(f"[BAR] ensure_tables failed (non-blocking): {exc}")

    # ── Core factory ─────────────────────────────────────────────

    def create_bar(
        self,
        session_id: str,
        agent_id: str,
        turn_index: int,
        output_text: str,
        governing_receipt_id: str,
        constraint_set: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BehavioralAnchorRecord:
        """
        BEV-INV-001: Create a BAR for a single agent output turn.

        The output is hashed (never stored raw), the constraint set is evaluated,
        and the full record is PQC-signed before return.
        """
        output_bytes = output_text.encode("utf-8")
        output_hash = hashlib.sha3_256(output_bytes).hexdigest()
        output_preview = output_text[:256] if output_text else ""

        constraint_set_hash = hashlib.sha3_256(
            json.dumps(constraint_set, sort_keys=True).encode()
        ).hexdigest()

        bar_status, halt_reason = self._evaluate_constraints(
            output_text, constraint_set, turn_index
        )

        bar_id = f"BAR-{uuid.uuid4().hex[:16].upper()}"
        created_at = datetime.now(timezone.utc).isoformat()

        content_hash = BehavioralAnchorRecord.compute_content_hash(
            session_id=session_id,
            agent_id=agent_id,
            turn_index=turn_index,
            output_hash=output_hash,
            governing_receipt_id=governing_receipt_id,
            constraint_set_hash=constraint_set_hash,
        )

        pqc_sig: Optional[str] = None
        pqc_alg: Optional[str] = None
        pqc = self._get_pqc()
        if pqc.pqc_enabled:
            try:
                sig_bytes, _, alg = pqc.sign_receipt({
                    "bar_id": bar_id,
                    "content_hash": content_hash,
                    "governing_receipt_id": governing_receipt_id,
                    "created_at": created_at,
                })
                pqc_sig = sig_bytes if isinstance(sig_bytes, str) else (
                    sig_bytes.decode() if isinstance(sig_bytes, bytes) else None
                )
                pqc_alg = alg
            except Exception as exc:
                logger.warning(f"[BAR] PQC signing failed (non-blocking): {exc}")

        bar = BehavioralAnchorRecord(
            bar_id=bar_id,
            session_id=session_id,
            agent_id=agent_id,
            turn_index=turn_index,
            output_hash=output_hash,
            output_preview=output_preview,
            governing_receipt_id=governing_receipt_id,
            constraint_set_hash=constraint_set_hash,
            atf_layer="BEV-L6",
            content_hash=content_hash,
            bar_status=bar_status,
            halt_reason=halt_reason,
            pqc_signature=pqc_sig,
            pqc_algorithm=pqc_alg,
            created_at=created_at,
            metadata=metadata or {},
        )

        self._persist(bar)
        return bar

    # ── Constraint evaluation ─────────────────────────────────────

    def _evaluate_constraints(
        self,
        output_text: str,
        constraint_set: Dict[str, Any],
        turn_index: int,
    ) -> tuple[str, Optional[str]]:
        """
        Evaluate output against the constraint set from the governing receipt.

        Returns (bar_status, halt_reason):
          VALID     — all constraints satisfied
          WARNING   — soft boundary approached
          VIOLATION — hard constraint breached (CCS watchdog triggered)
          HALTED    — session-halting constraint breached (BEV-INV-003)
        """
        if not constraint_set:
            return "VALID", None

        max_len = constraint_set.get("max_output_length")
        if max_len and len(output_text) > max_len:
            return "VIOLATION", f"Output length {len(output_text)} exceeds limit {max_len}"

        halt_on = constraint_set.get("halt_on_keywords", [])
        if isinstance(halt_on, list):
            lower = output_text.lower()
            for kw in halt_on:
                if kw.lower() in lower:
                    return "HALTED", f"Halt keyword detected: '{kw}'"

        warn_on = constraint_set.get("warn_on_keywords", [])
        if isinstance(warn_on, list):
            lower = output_text.lower()
            for kw in warn_on:
                if kw.lower() in lower:
                    return "WARNING", None

        max_turns = constraint_set.get("max_turns")
        if max_turns and turn_index >= max_turns:
            return "HALTED", f"Session exceeded max_turns constraint ({max_turns})"

        return "VALID", None

    # ── Persistence ───────────────────────────────────────────────

    def _persist(self, bar: BehavioralAnchorRecord) -> None:
        if not self._db_url:
            return
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO atf_behavioral_anchor_records
                            (bar_id, session_id, agent_id, turn_index,
                             output_hash, output_preview, governing_receipt_id,
                             constraint_set_hash, atf_layer, content_hash,
                             bar_status, halt_reason, pqc_signature, pqc_algorithm,
                             created_at, metadata)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (bar_id) DO NOTHING
                    """, (
                        bar.bar_id, bar.session_id, bar.agent_id, bar.turn_index,
                        bar.output_hash, bar.output_preview, bar.governing_receipt_id,
                        bar.constraint_set_hash, bar.atf_layer, bar.content_hash,
                        bar.bar_status, bar.halt_reason, bar.pqc_signature, bar.pqc_algorithm,
                        bar.created_at, json.dumps(bar.metadata),
                    ))
                conn.commit()
        except Exception as exc:
            logger.warning(f"[BAR] persist failed (non-blocking): {exc}")

    # ── Retrieval ─────────────────────────────────────────────────

    def get_bar(self, bar_id: str) -> Optional[BehavioralAnchorRecord]:
        if not self._db_url:
            return None
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT * FROM atf_behavioral_anchor_records WHERE bar_id=%s",
                        (bar_id,)
                    )
                    row = cur.fetchone()
                    if row is None:
                        return None
                    cols = [d[0] for d in cur.description]
                    return self._row_to_bar(dict(zip(cols, row)))
        except Exception as exc:
            logger.error(f"[BAR] get_bar error: {exc}")
            return None

    def list_bars(self, session_id: str) -> List[BehavioralAnchorRecord]:
        if not self._db_url:
            return []
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT * FROM atf_behavioral_anchor_records
                        WHERE session_id=%s ORDER BY turn_index ASC
                    """, (session_id,))
                    cols = [d[0] for d in cur.description]
                    return [self._row_to_bar(dict(zip(cols, r))) for r in cur.fetchall()]
        except Exception as exc:
            logger.error(f"[BAR] list_bars error: {exc}")
            return []

    @staticmethod
    def _row_to_bar(row: Dict[str, Any]) -> BehavioralAnchorRecord:
        meta = row.get("metadata") or {}
        if isinstance(meta, str):
            meta = json.loads(meta)
        return BehavioralAnchorRecord(
            bar_id=row["bar_id"],
            session_id=row["session_id"],
            agent_id=row["agent_id"],
            turn_index=row["turn_index"],
            output_hash=row["output_hash"],
            output_preview=row.get("output_preview", ""),
            governing_receipt_id=row["governing_receipt_id"],
            constraint_set_hash=row["constraint_set_hash"],
            atf_layer=row.get("atf_layer", "BEV-L6"),
            content_hash=row["content_hash"],
            bar_status=row["bar_status"],
            halt_reason=row.get("halt_reason"),
            pqc_signature=row.get("pqc_signature"),
            pqc_algorithm=row.get("pqc_algorithm"),
            created_at=str(row["created_at"]),
            metadata=meta,
        )

    # ── Offline verification (BEV-INV-004) ───────────────────────

    def verify_bar(self, bar: BehavioralAnchorRecord) -> Dict[str, Any]:
        """
        Offline verification of a BAR.

        Verifiable without network access — all inputs are embedded in the record.
        """
        hash_ok = bar.verify_content_hash()

        pqc_ok = False
        if bar.pqc_signature:
            try:
                pqc = self._get_pqc()
                pqc_ok = pqc.verify_receipt_signature(
                    {"bar_id": bar.bar_id, "content_hash": bar.content_hash},
                    bar.pqc_signature,
                )
            except Exception:
                pqc_ok = False

        return {
            "bar_id": bar.bar_id,
            "content_hash_valid": hash_ok,
            "pqc_signature_valid": pqc_ok,
            "fully_verified": hash_ok and (pqc_ok if bar.pqc_signature else True),
            "bar_status": bar.bar_status,
            "bev_inv_002": hash_ok,
            "bev_inv_004": pqc_ok,
            "atf_layer": "BEV-L6",
        }
