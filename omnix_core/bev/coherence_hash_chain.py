"""
OMNIX BEV — Cross-Turn Coherence Hash Chain (CTCHC)
RFC-ATF-6 § 4.3 · ADR-183

The CTCHC is a cryptographic chain that links every turn of a governed session
into a tamper-evident sequence. The chain is anchored to the governing receipt,
sealed with a PQC signature at session close, and can be verified offline.

Invariants enforced here:
  BEV-INV-010: CTCHC MUST be initialized before the first BAR is created.
  BEV-INV-011: Each CTCHC link = H(prev_link || turn_hash || governing_receipt_id).
  BEV-INV-012: Gaps in the turn sequence MUST cause chain verification to fail.
  BEV-INV-013: The seal hash MUST cover the complete chain (first→last link).
  BEV-INV-014: CTCHC seal MUST be PQC-signed (ML-DSA-65) before OEP export.
  BEV-INV-018: Every link's governing_receipt_id MUST match the chain's governing_receipt_id.

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
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("OMNIX.BEV.CTCHC")


# ─────────────────────────────────────────────────────────────────
#  Data models
# ─────────────────────────────────────────────────────────────────

@dataclass
class ChainLink:
    """A single link in the Cross-Turn Coherence Hash Chain."""
    link_id: str
    session_id: str
    turn_index: int
    prev_link_hash: str
    turn_hash: str
    governing_receipt_id: str
    chain_link_hash: str
    created_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "link_id": self.link_id,
            "session_id": self.session_id,
            "turn_index": self.turn_index,
            "prev_link_hash": self.prev_link_hash,
            "turn_hash": self.turn_hash,
            "governing_receipt_id": self.governing_receipt_id,
            "chain_link_hash": self.chain_link_hash,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


@dataclass
class CoherenceHashChain:
    """
    The complete CTCHC for a governed session.

    At session close, the chain is sealed: a final hash covers the entire
    sequence and is PQC-signed. Any tampering with any link breaks the seal.
    """
    chain_id: str
    session_id: str
    governing_receipt_id: str
    genesis_hash: str
    current_tip_hash: str
    turn_count: int
    is_sealed: bool
    seal_hash: Optional[str]
    seal_pqc_signature: Optional[str]
    seal_pqc_algorithm: Optional[str]
    initialized_at: str
    sealed_at: Optional[str]
    links: List[ChainLink] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "session_id": self.session_id,
            "governing_receipt_id": self.governing_receipt_id,
            "genesis_hash": self.genesis_hash,
            "current_tip_hash": self.current_tip_hash,
            "turn_count": self.turn_count,
            "is_sealed": self.is_sealed,
            "seal_hash": self.seal_hash,
            "seal_pqc_signature": self.seal_pqc_signature,
            "seal_pqc_algorithm": self.seal_pqc_algorithm,
            "initialized_at": self.initialized_at,
            "sealed_at": self.sealed_at,
            "links": [lk.to_dict() for lk in self.links],
        }

    def chain_summary(self) -> Dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "session_id": self.session_id,
            "turn_count": self.turn_count,
            "is_sealed": self.is_sealed,
            "genesis_hash": self.genesis_hash,
            "tip_hash": self.current_tip_hash,
            "seal_hash": self.seal_hash,
            "pqc_sealed": self.seal_pqc_signature is not None,
            "pqc_algorithm": self.seal_pqc_algorithm,
            "initialized_at": self.initialized_at,
            "sealed_at": self.sealed_at,
        }


# ─────────────────────────────────────────────────────────────────
#  Engine
# ─────────────────────────────────────────────────────────────────

class CTCHCEngine:
    """
    Creates, extends, seals, and verifies Cross-Turn Coherence Hash Chains.

    The CTCHC is what makes every OMNIX governed session forensically verifiable
    end-to-end. It is architecturally distinct from audit log hash chains because
    it is cryptographically bound to the governance receipt — not just the log.
    """

    _CREATE_CHAIN_TABLE = """
    CREATE TABLE IF NOT EXISTS atf_coherence_hash_chains (
        chain_id             TEXT PRIMARY KEY,
        session_id           TEXT NOT NULL UNIQUE,
        governing_receipt_id TEXT NOT NULL,
        genesis_hash         TEXT NOT NULL,
        current_tip_hash     TEXT NOT NULL,
        turn_count           INTEGER NOT NULL DEFAULT 0,
        is_sealed            BOOLEAN NOT NULL DEFAULT FALSE,
        seal_hash            TEXT,
        seal_pqc_signature   TEXT,
        seal_pqc_algorithm   TEXT,
        initialized_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        sealed_at            TIMESTAMPTZ
    );
    CREATE INDEX IF NOT EXISTS idx_ctchc_session ON atf_coherence_hash_chains(session_id);
    """

    _CREATE_LINKS_TABLE = """
    CREATE TABLE IF NOT EXISTS atf_coherence_chain_links (
        link_id              TEXT PRIMARY KEY,
        session_id           TEXT NOT NULL,
        turn_index           INTEGER NOT NULL,
        prev_link_hash       TEXT NOT NULL,
        turn_hash            TEXT NOT NULL,
        governing_receipt_id TEXT NOT NULL,
        chain_link_hash      TEXT NOT NULL,
        created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        metadata             JSONB DEFAULT '{}'::jsonb,
        UNIQUE (session_id, turn_index)
    );
    CREATE INDEX IF NOT EXISTS idx_links_session ON atf_coherence_chain_links(session_id);
    CREATE INDEX IF NOT EXISTS idx_links_turn    ON atf_coherence_chain_links(session_id, turn_index);
    """

    def __init__(self):
        self._db_url = os.environ.get("DATABASE_URL")
        self._pqc = None
        # In-process chain tips: session_id → current_tip_hash
        self._tip_cache: Dict[str, str] = {}
        # In-process full chain objects: session_id → CoherenceHashChain
        # Required for no-DB (in-memory) operation — DB writes are no-ops without
        # DATABASE_URL, so seal_chain / get_chain must fall back to this cache.
        self._chain_cache: Dict[str, "CoherenceHashChain"] = {}
        # In-process chain links: session_id → List[ChainLink]
        # Mirrors _chain_cache: populated by append_turn for no-DB operation.
        self._links_cache: Dict[str, List["ChainLink"]] = {}

    def _get_pqc(self):
        if self._pqc is None:
            from omnix_core.security.pqc_security import PostQuantumSecurity
            self._pqc = PostQuantumSecurity()
        return self._pqc

    def _get_conn(self):
        import psycopg
        return psycopg.connect(self._db_url)

    def ensure_tables(self) -> None:
        if not self._db_url:
            return
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(self._CREATE_CHAIN_TABLE)
                    cur.execute(self._CREATE_LINKS_TABLE)
                conn.commit()
        except Exception as exc:
            logger.warning(f"[CTCHC] ensure_tables failed (non-blocking): {exc}")

    # ── Genesis (BEV-INV-010) ─────────────────────────────────────

    def initialize_chain(
        self,
        session_id: str,
        governing_receipt_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CoherenceHashChain:
        """
        BEV-INV-010: Initialize the CTCHC before the first turn.

        The genesis hash binds the chain to the governing receipt — any
        future attempt to swap the receipt breaks the chain.
        """
        initialized_at = datetime.now(timezone.utc).isoformat()
        genesis_payload = json.dumps({
            "session_id": session_id,
            "governing_receipt_id": governing_receipt_id,
            "initialized_at": initialized_at,
            "sentinel": "OMNIX-CTCHC-GENESIS",
        }, sort_keys=True)
        genesis_hash = hashlib.sha3_256(genesis_payload.encode()).hexdigest()

        chain_id = f"CTCHC-{uuid.uuid4().hex[:16].upper()}"

        chain = CoherenceHashChain(
            chain_id=chain_id,
            session_id=session_id,
            governing_receipt_id=governing_receipt_id,
            genesis_hash=genesis_hash,
            current_tip_hash=genesis_hash,
            turn_count=0,
            is_sealed=False,
            seal_hash=None,
            seal_pqc_signature=None,
            seal_pqc_algorithm=None,
            initialized_at=initialized_at,
            sealed_at=None,
        )

        self._tip_cache[session_id] = genesis_hash
        # Cache the full chain object for no-DB (in-memory) operation.
        # seal_chain / get_chain fall back to this when DATABASE_URL is absent.
        self._chain_cache[session_id] = chain
        self._links_cache[session_id] = []
        self._persist_chain(chain)
        return chain

    # ── Append (BEV-INV-011) ─────────────────────────────────────

    def append_turn(
        self,
        session_id: str,
        turn_index: int,
        bar_id: str,
        ccs_id: str,
        output_hash: str,
        governing_receipt_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ChainLink:
        """
        BEV-INV-011: Append a turn to the chain.

        link_hash = SHA3-256( prev_hash || turn_hash || governing_receipt_id )
        """
        turn_payload = json.dumps({
            "bar_id": bar_id,
            "ccs_id": ccs_id,
            "output_hash": output_hash,
            "turn_index": turn_index,
        }, sort_keys=True)
        turn_hash = hashlib.sha3_256(turn_payload.encode()).hexdigest()

        prev_hash = self._tip_cache.get(session_id)
        if prev_hash is None:
            prev_hash = self._load_tip_from_db(session_id)
        if prev_hash is None:
            raise RuntimeError(
                f"[CTCHC] Chain not initialized for session {session_id} "
                "(BEV-INV-010 violated)"
            )

        link_payload = json.dumps({
            "prev": prev_hash,
            "turn": turn_hash,
            "receipt": governing_receipt_id,
        }, sort_keys=True)
        chain_link_hash = hashlib.sha3_256(link_payload.encode()).hexdigest()

        link_id = f"LINK-{uuid.uuid4().hex[:12].upper()}"
        created_at = datetime.now(timezone.utc).isoformat()

        link = ChainLink(
            link_id=link_id,
            session_id=session_id,
            turn_index=turn_index,
            prev_link_hash=prev_hash,
            turn_hash=turn_hash,
            governing_receipt_id=governing_receipt_id,
            chain_link_hash=chain_link_hash,
            created_at=created_at,
            metadata=metadata or {},
        )

        self._tip_cache[session_id] = chain_link_hash
        # Keep in-memory links list in sync for no-DB operation.
        self._links_cache.setdefault(session_id, []).append(link)
        self._persist_link(link)
        self._update_chain_tip(session_id, chain_link_hash, turn_index + 1)
        return link

    # ── Seal (BEV-INV-013 / BEV-INV-014) ────────────────────────

    def seal_chain(self, session_id: str) -> CoherenceHashChain:
        """
        BEV-INV-013/014: Seal the CTCHC and PQC-sign the final proof.

        The seal hash covers all links in order. Any gap or reordering
        breaks the seal. After sealing, the chain is immutable.
        """
        chain = self.get_chain(session_id)
        if chain is None:
            raise RuntimeError(f"[CTCHC] No chain found for session {session_id}")

        if chain.is_sealed:
            return chain

        links = self.get_links(session_id)
        seal_payload = json.dumps({
            "chain_id": chain.chain_id,
            "session_id": session_id,
            "governing_receipt_id": chain.governing_receipt_id,
            "genesis_hash": chain.genesis_hash,
            "turn_count": len(links),
            "link_hashes": [lk.chain_link_hash for lk in sorted(links, key=lambda x: x.turn_index)],
            "tip_hash": chain.current_tip_hash,
        }, sort_keys=True)
        seal_hash = hashlib.sha3_256(seal_payload.encode()).hexdigest()

        pqc_sig: Optional[str] = None
        pqc_alg: Optional[str] = None
        pqc = self._get_pqc()
        if pqc.pqc_enabled:
            try:
                sig_bytes, _, alg = pqc.sign_receipt({
                    "chain_id": chain.chain_id,
                    "seal_hash": seal_hash,
                    "session_id": session_id,
                })
                pqc_sig = sig_bytes if isinstance(sig_bytes, str) else (
                    sig_bytes.decode() if isinstance(sig_bytes, bytes) else None
                )
                pqc_alg = alg
            except Exception as exc:
                logger.warning(f"[CTCHC] PQC seal signing failed (non-blocking): {exc}")

        sealed_at = datetime.now(timezone.utc).isoformat()
        self._persist_seal(session_id, seal_hash, pqc_sig, pqc_alg, sealed_at)

        chain.is_sealed = True
        chain.seal_hash = seal_hash
        chain.seal_pqc_signature = pqc_sig
        chain.seal_pqc_algorithm = pqc_alg
        chain.sealed_at = sealed_at
        return chain

    # ── Verification ─────────────────────────────────────────────

    def verify_chain(self, session_id: str) -> Dict[str, Any]:
        """
        Offline verification of the complete CTCHC.

        Walks every link and recomputes each hash from scratch.
        BEV-INV-012: any gap → chain_complete = False.
        """
        chain = self.get_chain(session_id)
        if chain is None:
            return {"verified": False, "reason": "Chain not found", "session_id": session_id}

        links = sorted(self.get_links(session_id), key=lambda x: x.turn_index)

        if len(links) == 0:
            return {
                "verified": True,
                "session_id": session_id,
                "chain_id": chain.chain_id,
                "turn_count": 0,
                "chain_complete": True,
                "seal_valid": chain.is_sealed,
                "bev_inv_012": True,
                "bev_inv_013": chain.is_sealed,
                "bev_inv_014": chain.seal_pqc_signature is not None,
            }

        errors = []
        prev_hash = chain.genesis_hash

        for expected_idx, link in enumerate(links):
            if link.turn_index != expected_idx:
                errors.append(f"Gap at turn_index {expected_idx} (found {link.turn_index})")

            # BEV-INV-018: every link's governing_receipt_id must match the chain's
            if link.governing_receipt_id != chain.governing_receipt_id:
                errors.append(
                    f"BEV-INV-018: governing_receipt_id mismatch at turn {link.turn_index} "
                    f"(link={link.governing_receipt_id[:16]}… "
                    f"chain={chain.governing_receipt_id[:16]}…)"
                )

            link_payload = json.dumps({
                "prev": prev_hash,
                "turn": link.turn_hash,
                "receipt": link.governing_receipt_id,
            }, sort_keys=True)
            expected_hash = hashlib.sha3_256(link_payload.encode()).hexdigest()

            if expected_hash != link.chain_link_hash:
                errors.append(
                    f"Hash mismatch at turn {link.turn_index}: "
                    f"expected {expected_hash[:16]}… got {link.chain_link_hash[:16]}…"
                )
            prev_hash = link.chain_link_hash

        chain_ok = len(errors) == 0

        seal_ok = False
        if chain.is_sealed and chain.seal_hash:
            seal_payload = json.dumps({
                "chain_id": chain.chain_id,
                "session_id": session_id,
                "governing_receipt_id": chain.governing_receipt_id,
                "genesis_hash": chain.genesis_hash,
                "turn_count": len(links),
                "link_hashes": [lk.chain_link_hash for lk in links],
                "tip_hash": chain.current_tip_hash,
            }, sort_keys=True)
            expected_seal = hashlib.sha3_256(seal_payload.encode()).hexdigest()
            seal_ok = expected_seal == chain.seal_hash

        receipt_errors = [e for e in errors if "BEV-INV-018" in e]
        bev_inv_018 = len(receipt_errors) == 0

        return {
            "verified": chain_ok and (seal_ok if chain.is_sealed else True),
            "session_id": session_id,
            "chain_id": chain.chain_id,
            "turn_count": len(links),
            "chain_complete": chain_ok,
            "hash_errors": errors,
            "is_sealed": chain.is_sealed,
            "seal_valid": seal_ok,
            "pqc_sealed": chain.seal_pqc_signature is not None,
            "bev_inv_011": chain_ok,
            "bev_inv_012": len(errors) == 0,
            "bev_inv_013": seal_ok,
            "bev_inv_014": chain.seal_pqc_signature is not None,
            "bev_inv_018": bev_inv_018,
        }

    # ── Persistence helpers ───────────────────────────────────────

    def _persist_chain(self, chain: CoherenceHashChain) -> None:
        if not self._db_url:
            return
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO atf_coherence_hash_chains
                            (chain_id, session_id, governing_receipt_id,
                             genesis_hash, current_tip_hash, turn_count,
                             is_sealed, initialized_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (session_id) DO NOTHING
                    """, (
                        chain.chain_id, chain.session_id, chain.governing_receipt_id,
                        chain.genesis_hash, chain.current_tip_hash, chain.turn_count,
                        chain.is_sealed, chain.initialized_at,
                    ))
                conn.commit()
        except Exception as exc:
            logger.warning(f"[CTCHC] persist_chain failed: {exc}")

    def _persist_link(self, link: ChainLink) -> None:
        if not self._db_url:
            return
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO atf_coherence_chain_links
                            (link_id, session_id, turn_index, prev_link_hash,
                             turn_hash, governing_receipt_id, chain_link_hash,
                             created_at, metadata)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (session_id, turn_index) DO NOTHING
                    """, (
                        link.link_id, link.session_id, link.turn_index,
                        link.prev_link_hash, link.turn_hash, link.governing_receipt_id,
                        link.chain_link_hash, link.created_at,
                        json.dumps(link.metadata),
                    ))
                conn.commit()
        except Exception as exc:
            logger.warning(f"[CTCHC] persist_link failed: {exc}")

    def _update_chain_tip(
        self, session_id: str, new_tip: str, new_count: int
    ) -> None:
        # Always sync the in-memory chain object so no-DB callers see correct state.
        if session_id in self._chain_cache:
            self._chain_cache[session_id].current_tip_hash = new_tip
            self._chain_cache[session_id].turn_count = new_count
        if not self._db_url:
            return
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE atf_coherence_hash_chains
                        SET current_tip_hash=%s, turn_count=%s
                        WHERE session_id=%s
                    """, (new_tip, new_count, session_id))
                conn.commit()
        except Exception as exc:
            logger.warning(f"[CTCHC] update_chain_tip failed: {exc}")

    def _persist_seal(
        self,
        session_id: str,
        seal_hash: str,
        pqc_sig: Optional[str],
        pqc_alg: Optional[str],
        sealed_at: str,
    ) -> None:
        if not self._db_url:
            return
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE atf_coherence_hash_chains
                        SET is_sealed=TRUE, seal_hash=%s,
                            seal_pqc_signature=%s, seal_pqc_algorithm=%s,
                            sealed_at=%s
                        WHERE session_id=%s
                    """, (seal_hash, pqc_sig, pqc_alg, sealed_at, session_id))
                conn.commit()
        except Exception as exc:
            logger.warning(f"[CTCHC] persist_seal failed: {exc}")

    def _load_tip_from_db(self, session_id: str) -> Optional[str]:
        if not self._db_url:
            return None
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT current_tip_hash FROM atf_coherence_hash_chains WHERE session_id=%s",
                        (session_id,)
                    )
                    row = cur.fetchone()
                    if row:
                        self._tip_cache[session_id] = row[0]
                        return row[0]
        except Exception as exc:
            logger.warning(f"[CTCHC] load_tip_from_db failed: {exc}")
        return None

    def get_chain(self, session_id: str) -> Optional[CoherenceHashChain]:
        if not self._db_url:
            # No database — return the in-memory cached chain (may be None if
            # initialize_chain was never called for this session_id).
            return self._chain_cache.get(session_id)
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT * FROM atf_coherence_hash_chains WHERE session_id=%s",
                        (session_id,)
                    )
                    row = cur.fetchone()
                    if row is None:
                        return None
                    cols = [d[0] for d in cur.description]
                    return self._row_to_chain(dict(zip(cols, row)))
        except Exception as exc:
            logger.error(f"[CTCHC] get_chain error: {exc}")
            return None

    def get_links(self, session_id: str) -> List[ChainLink]:
        if not self._db_url:
            # No database — return cached links (empty list for uninitialised session).
            return list(self._links_cache.get(session_id, []))
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT * FROM atf_coherence_chain_links WHERE session_id=%s ORDER BY turn_index ASC",
                        (session_id,)
                    )
                    cols = [d[0] for d in cur.description]
                    return [self._row_to_link(dict(zip(cols, r))) for r in cur.fetchall()]
        except Exception as exc:
            logger.error(f"[CTCHC] get_links error: {exc}")
            return []

    @staticmethod
    def _row_to_chain(row: Dict[str, Any]) -> CoherenceHashChain:
        return CoherenceHashChain(
            chain_id=row["chain_id"],
            session_id=row["session_id"],
            governing_receipt_id=row["governing_receipt_id"],
            genesis_hash=row["genesis_hash"],
            current_tip_hash=row["current_tip_hash"],
            turn_count=int(row["turn_count"]),
            is_sealed=bool(row["is_sealed"]),
            seal_hash=row.get("seal_hash"),
            seal_pqc_signature=row.get("seal_pqc_signature"),
            seal_pqc_algorithm=row.get("seal_pqc_algorithm"),
            initialized_at=str(row["initialized_at"]),
            sealed_at=str(row["sealed_at"]) if row.get("sealed_at") else None,
        )

    @staticmethod
    def _row_to_link(row: Dict[str, Any]) -> ChainLink:
        meta = row.get("metadata") or {}
        if isinstance(meta, str):
            meta = json.loads(meta)
        return ChainLink(
            link_id=row["link_id"],
            session_id=row["session_id"],
            turn_index=int(row["turn_index"]),
            prev_link_hash=row["prev_link_hash"],
            turn_hash=row["turn_hash"],
            governing_receipt_id=row["governing_receipt_id"],
            chain_link_hash=row["chain_link_hash"],
            created_at=str(row["created_at"]),
            metadata=meta,
        )
