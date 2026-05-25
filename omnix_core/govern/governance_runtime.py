"""
OMNIX Governance Runtime (OGR) — Central Orchestrator
ADR-184 · ADR-194 · RFC-ATF-1 through RFC-ATF-6

The GovernanceRuntime is the single "body and soul" of the OMNIX integration
product. One session activates all six ATF layers simultaneously:

  L1 — Identity (AIR)             RFC-ATF-1
  L2 — Delegation (DR)            RFC-ATF-1
  L3 — Temporal Authority (TAR)   RFC-ATF-2
  L4 — Runtime Continuity (RCR)   RFC-ATF-2
  L5 — Cognitive Governance       RFC-ATF-5
  L6 — Behavioral Verification    RFC-ATF-6

Optional extension when governing receipt includes 'mandate_binding':
  MIVP — Mandate Integrity Verification Protocol   ADR-194
       → MBR issued before turn 1 (MIVP-INV-001)
       → MAS computed per turn    (MIVP-INV-003)
       → MBR Seal at close        (MIVP-INV-007)
       → MANDATE-BOUND PoGC tag   (MIVP-INV-008)

No competitor activates all six simultaneously with:
  • ML-DSA-65 (PQC) sealing on every artifact
  • Receipt-bound behavioral attestation (BAR)
  • Continuous mandate alignment verification (MAS — ADR-194)
  • Anticipatory veto integration (CCS + MAS → AGVP)
  • Offline-verifiable session proof (CTCHC seal)

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

logger = logging.getLogger("OMNIX.OGR")

# ─────────────────────────────────────────────────────────────────
#  Session status constants
# ─────────────────────────────────────────────────────────────────
STATUS_ACTIVE  = "ACTIVE"
STATUS_CLOSED  = "CLOSED"
STATUS_HALTED  = "HALTED"
STATUS_EXPIRED = "EXPIRED"

# ATF compliance tier
ATF_BEV_COMPLIANT  = "ATF-BEV-Compliant"   # highest BEV designation
ATF_L4_COMPLIANT   = "ATF-L4-Compliant"
ATF_L3_COMPLIANT   = "ATF-L3-Compliant"

# MIVP extended tags (ADR-194)
MIVP_MANDATE_BOUND = "MANDATE-BOUND"       # added to PoGC when MIVP-INV-008 satisfied


# ─────────────────────────────────────────────────────────────────
#  OGR Session data model
# ─────────────────────────────────────────────────────────────────

@dataclass
class OGRSession:
    """
    Full state of an OMNIX Governance Runtime session.

    A session is the atomic unit of governance: it begins with a
    policy declaration, records every agent turn as a PQC-signed artifact,
    and closes with an offline-verifiable behavioral attestation chain.
    """
    session_id: str
    agent_id: str
    governing_receipt_id: str
    domain: str
    vertical: str
    policy_name: str
    constraint_set: Dict[str, Any]
    session_status: str
    compliance_tier: str
    turn_count: int
    total_drift: float
    chain_id: Optional[str]
    chain_genesis_hash: Optional[str]
    chain_tip_hash: Optional[str]
    chain_sealed: bool
    chain_seal_hash: Optional[str]
    last_verdict: str
    halt_reason: Optional[str]
    oep_export_id: Optional[str]
    atf_layers_active: List[str]
    # MIVP fields (ADR-194) — populated when constraint_set contains 'mandate_binding'
    mbr_id: Optional[str]
    mandate_bound: bool
    started_at: str
    closed_at: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def governance_summary(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "governing_receipt_id": self.governing_receipt_id,
            "domain": self.domain,
            "vertical": self.vertical,
            "policy_name": self.policy_name,
            "session_status": self.session_status,
            "compliance_tier": self.compliance_tier,
            "turn_count": self.turn_count,
            "total_drift": round(self.total_drift, 4),
            "last_verdict": self.last_verdict,
            "halt_reason": self.halt_reason,
            "chain_id": self.chain_id,
            "chain_genesis_hash": self.chain_genesis_hash,
            "chain_tip_hash": self.chain_tip_hash,
            "chain_sealed": self.chain_sealed,
            "chain_seal_hash": self.chain_seal_hash,
            "atf_layers_active": self.atf_layers_active,
            # MIVP (ADR-194)
            "mbr_id": self.mbr_id,
            "mandate_bound": self.mandate_bound,
            "started_at": self.started_at,
            "closed_at": self.closed_at,
        }

    def to_dict(self) -> Dict[str, Any]:
        d = self.governance_summary()
        d["oep_export_id"] = self.oep_export_id
        d["constraint_set"] = self.constraint_set
        d["metadata"] = self.metadata
        return d


# ─────────────────────────────────────────────────────────────────
#  OGR Turn result
# ─────────────────────────────────────────────────────────────────

@dataclass
class OGRTurnResult:
    """
    The atomic result of recording one agent turn through all active ATF layers.

    Contains: BAR (behavioral attestation), CCS (conformance signal),
    chain link hash (CTCHC), MAS (mandate alignment — MIVP, when active),
    and governance verdict.
    """
    session_id: str
    turn_index: int
    bar_id: str
    bar_status: str
    ccs_id: str
    conformance_score: float
    cumulative_drift: float
    ccs_verdict: str
    watchdog_triggered: bool
    chain_link_hash: str
    governing_receipt_id: str
    pqc_signed: bool
    pqc_algorithm: Optional[str]
    should_halt: bool
    halt_reason: Optional[str]
    ogr_verdict: str
    processed_at: str
    # MIVP fields — None when no MBR active (ADR-194)
    mas_id: Optional[str] = None
    mas_score: Optional[float] = None
    mas_verdict: Optional[str] = None
    mandate_dominant_proxy: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "session_id": self.session_id,
            "turn_index": self.turn_index,
            "bar": {
                "bar_id": self.bar_id,
                "bar_status": self.bar_status,
                "pqc_signed": self.pqc_signed,
                "pqc_algorithm": self.pqc_algorithm,
            },
            "ccs": {
                "ccs_id": self.ccs_id,
                "conformance_score": round(self.conformance_score, 4),
                "cumulative_drift": round(self.cumulative_drift, 4),
                "verdict": self.ccs_verdict,
                "watchdog_triggered": self.watchdog_triggered,
            },
            "ctchc": {
                "chain_link_hash": self.chain_link_hash,
            },
            "governing_receipt_id": self.governing_receipt_id,
            "should_halt": self.should_halt,
            "halt_reason": self.halt_reason,
            "ogr_verdict": self.ogr_verdict,
            "processed_at": self.processed_at,
        }
        if self.mas_id is not None:
            result["mivp"] = {
                "mas_id": self.mas_id,
                "alignment_score": round(self.mas_score, 4) if self.mas_score is not None else None,
                "verdict": self.mas_verdict,
                "dominant_proxy": self.mandate_dominant_proxy,
            }
        return result


# ─────────────────────────────────────────────────────────────────
#  GovernanceRuntime — the one body
# ─────────────────────────────────────────────────────────────────

class GovernanceRuntime:
    """
    OMNIX Governance Runtime — six ATF layers, one integration point.

    External AI agents plug into this class via the /v1/govern/ API.
    Every session is receipt-bound, PQC-sealed, and offline-verifiable.
    """

    _CREATE_SESSIONS_TABLE = """
    CREATE TABLE IF NOT EXISTS atf_ogr_sessions (
        session_id           TEXT PRIMARY KEY,
        agent_id             TEXT NOT NULL,
        governing_receipt_id TEXT NOT NULL,
        domain               TEXT NOT NULL DEFAULT 'general',
        vertical             TEXT NOT NULL DEFAULT 'general',
        policy_name          TEXT NOT NULL DEFAULT 'default',
        constraint_set       JSONB NOT NULL DEFAULT '{}'::jsonb,
        session_status       TEXT NOT NULL DEFAULT 'ACTIVE',
        compliance_tier      TEXT NOT NULL DEFAULT 'ATF-BEV-Compliant',
        turn_count           INTEGER NOT NULL DEFAULT 0,
        total_drift          REAL NOT NULL DEFAULT 0.0,
        chain_id             TEXT,
        chain_genesis_hash   TEXT,
        chain_tip_hash       TEXT,
        chain_sealed         BOOLEAN NOT NULL DEFAULT FALSE,
        chain_seal_hash      TEXT,
        last_verdict         TEXT NOT NULL DEFAULT 'CONFORMANT',
        halt_reason          TEXT,
        oep_export_id        TEXT,
        atf_layers_active    JSONB DEFAULT '[]'::jsonb,
        started_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        closed_at            TIMESTAMPTZ,
        metadata             JSONB DEFAULT '{}'::jsonb
    );
    CREATE INDEX IF NOT EXISTS idx_ogr_agent_id  ON atf_ogr_sessions(agent_id);
    CREATE INDEX IF NOT EXISTS idx_ogr_status    ON atf_ogr_sessions(session_status);
    CREATE INDEX IF NOT EXISTS idx_ogr_domain    ON atf_ogr_sessions(domain);
    CREATE INDEX IF NOT EXISTS idx_ogr_started   ON atf_ogr_sessions(started_at DESC);
    """

    # OGR-INV-001: all 6 ATF layers MUST be activated simultaneously per session.
    # Partial activation (e.g. L1-L4 only) is not ATF-BEV-Compliant.
    _ATF_LAYERS = [
        "ATF-L1-Identity",
        "ATF-L2-Delegation",
        "ATF-L3-TemporalAuthority",
        "ATF-L4-RuntimeContinuity",
        "ATF-L5-CognitiveGovernance",
        "ATF-L6-BehavioralVerification",
    ]
    _REQUIRED_LAYER_COUNT = 6  # OGR-INV-001 enforcement constant

    def __init__(self):
        self._db_url = os.environ.get("DATABASE_URL")
        self._bar_engine = None
        self._ccs_engine = None
        self._ctchc_engine = None
        self._mivp_engine = None   # MIVP — lazy, only created when first needed (ADR-194)
        # In-memory session cache — used as primary store when DATABASE_URL absent
        # and as a read-through cache in production to reduce DB round-trips on
        # record_turn (hot path). Always authoritative for the current process.
        self._session_cache: Dict[str, "OGRSession"] = {}

    def _get_bar(self):
        if self._bar_engine is None:
            from omnix_core.bev.behavioral_anchor_record import BAREngine
            self._bar_engine = BAREngine()
        return self._bar_engine

    def _get_ccs(self):
        if self._ccs_engine is None:
            from omnix_core.bev.constraint_conformance_signal import CCSEngine
            self._ccs_engine = CCSEngine()
        return self._ccs_engine

    def _get_ctchc(self):
        if self._ctchc_engine is None:
            from omnix_core.bev.coherence_hash_chain import CTCHCEngine
            self._ctchc_engine = CTCHCEngine()
        return self._ctchc_engine

    def _get_mivp(self):
        """Lazy-load MIVPEngine — only instantiated when a session has mandate_binding."""
        if self._mivp_engine is None:
            from omnix_core.bev.mandate_integrity_verification import MIVPEngine
            self._mivp_engine = MIVPEngine()
        return self._mivp_engine

    def _get_conn(self):
        import psycopg2
        return psycopg2.connect(self._db_url)

    # ── Startup ───────────────────────────────────────────────────

    def ensure_tables(self) -> None:
        """Create all OGR + BEV + MIVP tables. Safe to call on every startup."""
        if not self._db_url:
            logger.debug("[OGR] No DATABASE_URL — skipping table creation")
            return
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(self._CREATE_SESSIONS_TABLE)
                conn.commit()
            self._get_bar().ensure_tables()
            self._get_ccs().ensure_tables()
            self._get_ctchc().ensure_tables()
            self._get_mivp().ensure_tables()   # MIVP tables (ADR-194)
            logger.info("[OGR] All governance runtime tables ready (BEV + MIVP)")
        except Exception as exc:
            logger.warning(f"[OGR] ensure_tables failed (non-blocking): {exc}")

    # ─────────────────────────────────────────────────────────────
    #  1. START SESSION
    # ─────────────────────────────────────────────────────────────

    def start_session(
        self,
        agent_id: str,
        governing_receipt_id: str,
        domain: str = "general",
        vertical: str = "general",
        policy_name: str = "default",
        constraint_set: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> OGRSession:
        """
        Initialize a fully governed session.

        Activates all 6 ATF layers and initializes the CTCHC genesis block.
        The governing_receipt_id MUST reference a valid decision receipt —
        it binds every subsequent artifact to the policy that authorized the agent.

        Returns an OGRSession with chain_genesis_hash proving session start.
        """
        if not agent_id:
            raise ValueError("agent_id is required")
        if not governing_receipt_id:
            raise ValueError("governing_receipt_id is required")

        constraint_set = constraint_set or {}
        session_id = f"OGR-{uuid.uuid4().hex[:20].upper()}"
        started_at = datetime.now(timezone.utc).isoformat()

        # L6: Initialize CTCHC genesis (BEV-INV-010)
        ctchc = self._get_ctchc()
        chain = ctchc.initialize_chain(
            session_id=session_id,
            governing_receipt_id=governing_receipt_id,
            metadata={"agent_id": agent_id, "domain": domain},
        )

        session = OGRSession(
            session_id=session_id,
            agent_id=agent_id,
            governing_receipt_id=governing_receipt_id,
            domain=domain,
            vertical=vertical,
            policy_name=policy_name,
            constraint_set=constraint_set,
            session_status=STATUS_ACTIVE,
            compliance_tier=ATF_BEV_COMPLIANT,
            turn_count=0,
            total_drift=0.0,
            chain_id=chain.chain_id,
            chain_genesis_hash=chain.genesis_hash,
            chain_tip_hash=chain.genesis_hash,
            chain_sealed=False,
            chain_seal_hash=None,
            last_verdict="CONFORMANT",
            halt_reason=None,
            oep_export_id=None,
            atf_layers_active=self._ATF_LAYERS.copy(),
            mbr_id=None,
            mandate_bound=False,
            started_at=started_at,
            closed_at=None,
            metadata=metadata or {},
        )

        # ── MIVP: create MBR before first turn (MIVP-INV-001) ────────
        mandate_binding = constraint_set.get("mandate_binding") if constraint_set else None
        if mandate_binding:
            try:
                mivp = self._get_mivp()
                mbr = mivp.create_mbr(
                    session_id=session_id,
                    governing_receipt_id=governing_receipt_id,
                    mandate_binding=mandate_binding,
                )
                import dataclasses as _dc
                session = _dc.replace(session, mbr_id=mbr.mbr_id)
                logger.info(
                    f"[OGR] MIVP activated: MBR={mbr.mbr_id} | session={session_id} "
                    f"| guards={len(mbr.proxy_guards)} (ADR-194)"
                )
            except Exception as mivp_exc:
                logger.warning(f"[OGR] MIVP MBR creation failed (non-blocking): {mivp_exc}")

        self._session_cache[session_id] = session
        self._persist_session(session)
        logger.info(
            f"[OGR] Session started: {session_id} | agent={agent_id} "
            f"| domain={domain} | receipt={governing_receipt_id[:16]}… "
            f"| mivp={'ON' if mandate_binding else 'OFF'}"
        )
        return session

    # ─────────────────────────────────────────────────────────────
    #  2. RECORD TURN
    # ─────────────────────────────────────────────────────────────

    def record_turn(
        self,
        session_id: str,
        output_text: str,
        turn_metadata: Optional[Dict[str, Any]] = None,
    ) -> OGRTurnResult:
        """
        Record one agent output turn through all active ATF layers.

        Atomically:
          1. Creates BAR (PQC-signed behavioral attestation)
          2. Computes CCS (constraint conformance signal)
          3. Appends CTCHC link (coherence hash chain extension)
          4. Evaluates OGR verdict and checks HALT conditions
          5. Updates session state

        This is the core innovation: three new artifact classes produced
        in one atomic call, all cryptographically bound to each other and
        to the governing receipt. Nothing else in the market does this.
        """
        session = self.get_session(session_id)
        if session is None:
            raise ValueError(f"OGR session not found: {session_id}")
        if session.session_status != STATUS_ACTIVE:
            raise ValueError(
                f"Session {session_id} is not ACTIVE "
                f"(current: {session.session_status})"
            )

        turn_index = session.turn_count
        processed_at = datetime.now(timezone.utc).isoformat()

        # ── Step 1: BAR (BEV-INV-001) ─────────────────────────────
        bar_engine = self._get_bar()
        bar = bar_engine.create_bar(
            session_id=session_id,
            agent_id=session.agent_id,
            turn_index=turn_index,
            output_text=output_text,
            governing_receipt_id=session.governing_receipt_id,
            constraint_set=session.constraint_set,
            metadata=turn_metadata,
        )

        # ── Step 2: CCS (BEV-INV-005) ─────────────────────────────
        ccs_engine = self._get_ccs()
        ccs = ccs_engine.compute_signal(
            session_id=session_id,
            bar_id=bar.bar_id,
            turn_index=turn_index,
            output_text=output_text,
            bar_status=bar.bar_status,
            constraint_set=session.constraint_set,
            metadata=turn_metadata,
        )

        # ── Step 3: CTCHC append (BEV-INV-011) ────────────────────
        ctchc_engine = self._get_ctchc()
        output_hash = hashlib.sha3_256(output_text.encode()).hexdigest()
        link = ctchc_engine.append_turn(
            session_id=session_id,
            turn_index=turn_index,
            bar_id=bar.bar_id,
            ccs_id=ccs.ccs_id,
            output_hash=output_hash,
            governing_receipt_id=session.governing_receipt_id,
        )

        # ── Step 4: MIVP — Mandate Alignment Score (MIVP-INV-003) ───
        mas = None
        if session.mbr_id:
            try:
                mivp = self._get_mivp()
                mas = mivp.compute_mas(
                    session_id=session_id,
                    bar_id=bar.bar_id,
                    turn_index=turn_index,
                    output_text=output_text,
                    ctchc_link_hash=link.chain_link_hash,
                    metadata=turn_metadata,
                )
            except Exception as mivp_exc:
                logger.warning(f"[OGR] MIVP MAS computation failed (non-blocking): {mivp_exc}")

        # ── Step 5: Determine OGR verdict ─────────────────────────
        mivp_halt = mas is not None and mas.verdict == "HALT"
        should_halt = (
            bar.bar_status == "HALTED"
            or ccs.verdict == "HALT"
            or mivp_halt
        )
        halt_reason = bar.halt_reason or (
            f"CCS HALT: cumulative_drift={ccs.cumulative_drift:.3f}"
            if ccs.verdict == "HALT" else None
        ) or (
            f"MIVP HALT: mandate_alignment={mas.alignment_score:.3f} < threshold "
            f"(dominant_proxy={mas.dominant_proxy})"
            if mivp_halt and mas else None
        )
        ogr_verdict = "HALT" if should_halt else ccs.verdict

        # ── Step 6: Update session state ──────────────────────────
        new_status = STATUS_HALTED if should_halt else STATUS_ACTIVE
        self._update_session_turn(
            session_id=session_id,
            new_turn_count=turn_index + 1,
            total_drift=ccs.cumulative_drift,
            chain_tip_hash=link.chain_link_hash,
            last_verdict=ogr_verdict,
            new_status=new_status,
            halt_reason=halt_reason,
        )

        if should_halt:
            logger.warning(
                f"[OGR] Session HALTED: {session_id} | turn={turn_index} "
                f"| reason={halt_reason}"
            )

        return OGRTurnResult(
            session_id=session_id,
            turn_index=turn_index,
            bar_id=bar.bar_id,
            bar_status=bar.bar_status,
            ccs_id=ccs.ccs_id,
            conformance_score=ccs.conformance_score,
            cumulative_drift=ccs.cumulative_drift,
            ccs_verdict=ccs.verdict,
            watchdog_triggered=ccs.watchdog_triggered,
            chain_link_hash=link.chain_link_hash,
            governing_receipt_id=session.governing_receipt_id,
            pqc_signed=bar.pqc_signature is not None,
            pqc_algorithm=bar.pqc_algorithm,
            should_halt=should_halt,
            halt_reason=halt_reason,
            ogr_verdict=ogr_verdict,
            processed_at=processed_at,
            # MIVP (ADR-194) — None when no MBR active
            mas_id=mas.mas_id if mas else None,
            mas_score=mas.alignment_score if mas else None,
            mas_verdict=mas.verdict if mas else None,
            mandate_dominant_proxy=mas.dominant_proxy if mas else None,
        )

    # ─────────────────────────────────────────────────────────────
    #  3. CLOSE SESSION
    # ─────────────────────────────────────────────────────────────

    def close_session(
        self,
        session_id: str,
        package_oep: bool = False,
    ) -> Dict[str, Any]:
        """
        Seal the CTCHC and close the session.

        The seal hash covers every turn in sequence (BEV-INV-013).
        The seal is PQC-signed (BEV-INV-014).

        After sealing, the session proof is:
          • Immutable
          • Offline-verifiable without calling OMNIX
          • Exportable as an OEP bundle (ADR-164)
        """
        session = self.get_session(session_id)
        if session is None:
            raise ValueError(f"OGR session not found: {session_id}")

        if session.session_status == STATUS_CLOSED:
            return {"session_id": session_id, "already_closed": True}

        ctchc_engine = self._get_ctchc()
        sealed_chain = ctchc_engine.seal_chain(session_id)

        closed_at = datetime.now(timezone.utc).isoformat()
        was_halted = session.session_status == STATUS_HALTED
        self._close_session_db(
            session_id=session_id,
            seal_hash=sealed_chain.seal_hash,
            closed_at=closed_at,
            preserve_halted=was_halted,
        )

        ccs_trend = self._get_ccs().get_session_trend(session_id)

        # ── MIVP: seal MBR at session close (MIVP-INV-007) ──────────
        mivp_seal = None
        mandate_bound = False
        if session.mbr_id:
            try:
                mivp = self._get_mivp()
                mivp_seal = mivp.seal_mbr(session_id)
                mandate_bound = mivp_seal.mandate_bound_eligible
                logger.info(
                    f"[OGR] MIVP MBR sealed: {mivp_seal.seal_id} | "
                    f"mandate_bound={mandate_bound} | "
                    f"verdict={mivp_seal.mandate_verdict} (MIVP-INV-007)"
                )
            except Exception as mivp_exc:
                logger.warning(f"[OGR] MIVP seal failed (non-blocking): {mivp_exc}")

        # BEV-INV-003: preserve HALTED as terminal forensic state — not overwritten by CLOSED
        final_status = STATUS_HALTED if was_halted else STATUS_CLOSED

        # Use session.turn_count — always accurate (updated by _update_session_turn
        # on every record_turn, both in-cache and in DB). Never query bars just
        # for this count: list_bars returns [] when DATABASE_URL is absent, which
        # would silently produce turn_count=0 for in-memory sessions.
        turn_count = session.turn_count

        # Sync the in-memory cache to the post-close state so any subsequent
        # get_session() call sees chain_sealed=True, closed_at, and final_status
        # without a DB round-trip.
        if session_id in self._session_cache:
            import dataclasses as _dc
            self._session_cache[session_id] = _dc.replace(
                self._session_cache[session_id],
                session_status=final_status,
                chain_sealed=True,
                chain_seal_hash=sealed_chain.seal_hash,
                closed_at=closed_at,
                mandate_bound=mandate_bound,
            )

        # Determine compliance tags (MIVP-INV-008)
        pogc_tags = [ATF_BEV_COMPLIANT]
        if mandate_bound:
            pogc_tags.append(MIVP_MANDATE_BOUND)

        result = {
            "session_id": session_id,
            "session_status": final_status,
            "closed_at": closed_at,
            "turn_count": turn_count,
            "chain_seal": sealed_chain.chain_summary(),
            "ccs_final": {
                "avg_conformance": ccs_trend.get("avg_conformance"),
                "cumulative_drift": ccs_trend.get("cumulative_drift"),
                "last_verdict": ccs_trend.get("last_verdict"),
            },
            "compliance_tier": ATF_BEV_COMPLIANT,
            "pogc_tags": pogc_tags,
            "mandate_bound": mandate_bound,
            "governing_receipt_id": session.governing_receipt_id,
            "pqc_sealed": sealed_chain.seal_pqc_signature is not None,
            "pqc_algorithm": sealed_chain.seal_pqc_algorithm,
            "offline_verifiable": True,
            "atf_layers_attested": self._ATF_LAYERS,
        }

        # MIVP seal summary if active (ADR-194)
        if mivp_seal:
            result["mivp_seal"] = mivp_seal.seal_summary()

        if package_oep:
            result["oep_note"] = (
                "OEP export available via GET /v1/govern/session/{id}/proof"
            )

        logger.info(
            f"[OGR] Session closed: {session_id} | turns={turn_count} "
            f"| sealed={sealed_chain.is_sealed} "
            f"| mandate_bound={mandate_bound}"
        )
        return result

    # ─────────────────────────────────────────────────────────────
    #  4. GET PROOF
    # ─────────────────────────────────────────────────────────────

    def get_proof(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve the complete Behavioral Attestation Chain for a session.

        Returns:
          • governing_receipt_id — the policy that authorized everything
          • all BARs — per-turn behavioral attestations
          • CCS trend — session conformance history
          • CTCHC — coherence hash chain with seal
          • verification result — offline verification of all invariants

        This proof package is the OGR's core deliverable.
        """
        session = self.get_session(session_id)
        if session is None:
            raise ValueError(f"OGR session not found: {session_id}")

        bars = self._get_bar().list_bars(session_id)
        ccs_trend = self._get_ccs().get_session_trend(session_id)
        ctchc_engine = self._get_ctchc()
        chain = ctchc_engine.get_chain(session_id)
        chain_links = ctchc_engine.get_links(session_id)

        verification = None
        if chain:
            verification = ctchc_engine.verify_chain(session_id)

        # MIVP proof (ADR-194) — included when session has MBR
        mivp_proof = None
        if session.mbr_id:
            try:
                mivp_proof = self._get_mivp().get_mandate_proof(session_id)
            except Exception as exc:
                logger.warning(f"[OGR] MIVP proof retrieval failed: {exc}")

        return {
            "session_id": session_id,
            "governing_receipt_id": session.governing_receipt_id,
            "session_status": session.session_status,
            "compliance_tier": ATF_BEV_COMPLIANT,
            "mandate_bound": session.mandate_bound,
            "atf_layers_active": session.atf_layers_active,
            "behavioral_attestation_chain": {
                # session.turn_count is always accurate (updated on every record_turn).
                # len(bars) would be 0 without DATABASE_URL — misleading in the proof.
                "turn_count": session.turn_count,
                "bars_retrieved": len(bars),
                "bars": [b.trust_summary() for b in bars],
                "all_pqc_signed": all(b.pqc_signature is not None for b in bars),
            },
            "ccs_trend": ccs_trend,
            "ctchc": chain.chain_summary() if chain else None,
            "ctchc_links": [lk.to_dict() for lk in chain_links],
            "verification": verification,
            "mivp": mivp_proof,
            "offline_verifiable": True,
            "proof_generated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ─────────────────────────────────────────────────────────────
    #  5. GET STATUS
    # ─────────────────────────────────────────────────────────────

    def get_status(self, session_id: str) -> Dict[str, Any]:
        """Full governance status dashboard for a session."""
        session = self.get_session(session_id)
        if session is None:
            raise ValueError(f"OGR session not found: {session_id}")

        ccs_trend = self._get_ccs().get_session_trend(session_id)
        chain = self._get_ctchc().get_chain(session_id)

        return {
            "session": session.governance_summary(),
            "ccs_trend": ccs_trend,
            "chain_status": chain.chain_summary() if chain else None,
            "compliance": {
                "tier": ATF_BEV_COMPLIANT,
                "layers_active": len(session.atf_layers_active),
                "all_layers": session.atf_layers_active,
                "invariants_enforced": [
                    "BEV-INV-001", "BEV-INV-002", "BEV-INV-003", "BEV-INV-004",
                    "BEV-INV-005", "BEV-INV-006", "BEV-INV-007", "BEV-INV-008",
                    "BEV-INV-009", "BEV-INV-010", "BEV-INV-011", "BEV-INV-012",
                    "BEV-INV-013", "BEV-INV-014", "BEV-INV-015", "BEV-INV-016",
                    "BEV-INV-017", "BEV-INV-018", "OGR-INV-001",
                    # MIVP active when session has mandate_binding (ADR-194)
                    *([
                        "MIVP-INV-001", "MIVP-INV-002", "MIVP-INV-003",
                        "MIVP-INV-004", "MIVP-INV-005", "MIVP-INV-006",
                        "MIVP-INV-007", "MIVP-INV-008",
                    ] if session.mbr_id else []),
                ],
                "pqc_algorithm": "ML-DSA-65 (Dilithium-3, FIPS 204)",
                "offline_verifiable": True,
                "mandate_bound": session.mandate_bound,
                "mivp_active": session.mbr_id is not None,
            },
        }

    # ─────────────────────────────────────────────────────────────
    #  6. VERIFY ARTIFACT (offline)
    # ─────────────────────────────────────────────────────────────

    def verify_artifact(
        self,
        artifact_type: str,
        artifact_id: str,
        artifact_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Offline verification of any OGR artifact.

        Accepts:
          artifact_type = "BAR" | "CTCHC" | "SESSION"
          artifact_id   = the artifact's primary key
          artifact_data = optional embedded dict (for fully offline use)

        Note: "CCS" verification requires DB access and is not supported
        in the offline verify endpoint. Use compliance_report for CCS data.

        Returns verification result with BEV invariant flags.
        """
        artifact_type = (artifact_type or "").upper()

        if artifact_type == "BAR":
            bar_engine = self._get_bar()
            if artifact_data:
                # Use the same row-deserialization path to handle type coercions
                # safely instead of direct **unpacking which fails on extra keys.
                try:
                    from omnix_core.bev.behavioral_anchor_record import BAREngine
                    bar = BAREngine._row_to_bar(artifact_data)
                except Exception as exc:
                    return {"verified": False, "reason": f"BAR data invalid: {exc}"}
            else:
                bar = bar_engine.get_bar(artifact_id)
                if bar is None:
                    return {"verified": False, "reason": f"BAR not found: {artifact_id}"}
            return bar_engine.verify_bar(bar)

        if artifact_type == "CTCHC":
            return self._get_ctchc().verify_chain(artifact_id)

        if artifact_type == "SESSION":
            session = self.get_session(artifact_id)
            if session is None:
                return {"verified": False, "reason": f"Session not found: {artifact_id}"}
            ctchc_result = self._get_ctchc().verify_chain(artifact_id)
            return {
                "artifact_type": "SESSION",
                "session_id": artifact_id,
                "session_status": session.session_status,
                "ctchc_verification": ctchc_result,
                "compliance_tier": ATF_BEV_COMPLIANT,
                "verified": ctchc_result.get("verified", False),
            }

        return {
            "verified": False,
            "reason": f"Unknown artifact_type: {artifact_type}. "
                      "Supported: BAR, CTCHC, SESSION",
        }

    # ─────────────────────────────────────────────────────────────
    #  7. COMPLIANCE REPORT
    # ─────────────────────────────────────────────────────────────

    def compliance_report(self, session_id: str) -> Dict[str, Any]:
        """
        Generate an ATF-BEV-Compliant compliance report for a session.

        This report is suitable for regulatory submission, audit evidence,
        or third-party governance verification.
        """
        session = self.get_session(session_id)
        if session is None:
            raise ValueError(f"OGR session not found: {session_id}")

        bars = self._get_bar().list_bars(session_id)
        ccs_trend = self._get_ccs().get_session_trend(session_id)
        ctchc_engine = self._get_ctchc()
        chain = ctchc_engine.get_chain(session_id)
        verification = ctchc_engine.verify_chain(session_id) if chain else {}

        total_bars = len(bars)
        halted_bars = sum(1 for b in bars if b.bar_status == "HALTED")
        violated_bars = sum(1 for b in bars if b.bar_status == "VIOLATION")
        valid_bars = sum(1 for b in bars if b.bar_status == "VALID")
        pqc_signed_bars = sum(1 for b in bars if b.pqc_signature)

        bev_inv_001 = total_bars == session.turn_count
        bev_inv_004 = pqc_signed_bars == total_bars if total_bars > 0 else True
        bev_inv_013 = chain.is_sealed if chain else False
        bev_inv_014 = chain.seal_pqc_signature is not None if chain else False
        bev_inv_015 = not any(
            b.bar_status == "VIOLATION" and "BEV-INV-015" in (b.halt_reason or "")
            for b in bars
        )
        bev_inv_016 = all(
            b.bar_id.startswith("BAR-") and len(b.bar_id) == 20 for b in bars
        ) if bars else True
        bev_inv_018 = verification.get("bev_inv_018", True)
        ogr_inv_001 = len(session.atf_layers_active) == self._REQUIRED_LAYER_COUNT

        overall_pass = (
            bev_inv_001
            and bev_inv_004
            and bev_inv_013
            and bev_inv_014
            and bev_inv_015
            and bev_inv_016
            and bev_inv_018
            and ogr_inv_001
            and verification.get("verified", False)
        )

        return {
            "report_type": "ATF-BEV-Compliant Governance Report",
            "report_id": f"OGR-RPT-{uuid.uuid4().hex[:12].upper()}",
            "session_id": session_id,
            "agent_id": session.agent_id,
            "domain": session.domain,
            "vertical": session.vertical,
            "governing_receipt_id": session.governing_receipt_id,
            "policy_name": session.policy_name,
            "session_period": {
                "started_at": session.started_at,
                "closed_at": session.closed_at,
            },
            "compliance_tier": ATF_BEV_COMPLIANT,
            "overall_pass": overall_pass,
            "atf_layers": {
                "total_active": len(session.atf_layers_active),
                "layers": session.atf_layers_active,
            },
            "behavioral_attestation": {
                "total_turns": total_bars,
                "valid_turns": valid_bars,
                "violated_turns": violated_bars,
                "halted_turns": halted_bars,
                "pqc_signed_turns": pqc_signed_bars,
                "bev_inv_001_pass": bev_inv_001,
                "bev_inv_004_pass": bev_inv_004,
                "bev_inv_015_pass": bev_inv_015,
                "bev_inv_016_pass": bev_inv_016,
            },
            "conformance_summary": {
                "avg_conformance": ccs_trend.get("avg_conformance"),
                "cumulative_drift": ccs_trend.get("cumulative_drift"),
                "min_score": ccs_trend.get("min_score"),
                "watchdog_triggers": ccs_trend.get("watchdog_trigger_count"),
                "last_verdict": ccs_trend.get("last_verdict"),
            },
            "chain_integrity": {
                "chain_id": chain.chain_id if chain else None,
                "is_sealed": bev_inv_013,
                "seal_hash": chain.seal_hash if chain else None,
                "pqc_sealed": bev_inv_014,
                "pqc_algorithm": "ML-DSA-65 (FIPS 204)",
                "bev_inv_011_pass": verification.get("bev_inv_011", False),
                "bev_inv_012_pass": verification.get("bev_inv_012", False),
                "bev_inv_013_pass": bev_inv_013,
                "bev_inv_014_pass": bev_inv_014,
                "bev_inv_018_pass": bev_inv_018,
            },
            "session_integrity": {
                "ogr_inv_001_pass": ogr_inv_001,
                "layers_active": len(session.atf_layers_active),
                "required_layers": self._REQUIRED_LAYER_COUNT,
            },
            "offline_verifiable": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "issuer": "OMNIX QUANTUM LTD",
        }

    # ─────────────────────────────────────────────────────────────
    #  DB helpers
    # ─────────────────────────────────────────────────────────────

    def get_session(self, session_id: str) -> Optional[OGRSession]:
        # Check in-memory cache first (no DB round-trip on hot path)
        if session_id in self._session_cache:
            return self._session_cache[session_id]
        if not self._db_url:
            return None
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT * FROM atf_ogr_sessions WHERE session_id=%s",
                        (session_id,)
                    )
                    row = cur.fetchone()
                    if row is None:
                        return None
                    cols = [d[0] for d in cur.description]
                    return self._row_to_session(dict(zip(cols, row)))
        except Exception as exc:
            logger.error(f"[OGR] get_session error: {exc}")
            return None

    def list_sessions(
        self,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[OGRSession]:
        if not self._db_url:
            return []
        try:
            conditions = []
            params = []
            if agent_id:
                conditions.append("agent_id = %s")
                params.append(agent_id)
            if status:
                conditions.append("session_status = %s")
                params.append(status)
            where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
            params.append(limit)
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"SELECT * FROM atf_ogr_sessions {where} "
                        f"ORDER BY started_at DESC LIMIT %s",
                        params,
                    )
                    cols = [d[0] for d in cur.description]
                    return [
                        self._row_to_session(dict(zip(cols, r)))
                        for r in cur.fetchall()
                    ]
        except Exception as exc:
            logger.error(f"[OGR] list_sessions error: {exc}")
            return []

    def _persist_session(self, session: OGRSession) -> None:
        if not self._db_url:
            return
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO atf_ogr_sessions (
                            session_id, agent_id, governing_receipt_id,
                            domain, vertical, policy_name, constraint_set,
                            session_status, compliance_tier, turn_count, total_drift,
                            chain_id, chain_genesis_hash, chain_tip_hash,
                            chain_sealed, last_verdict, atf_layers_active,
                            started_at, metadata
                        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (session_id) DO NOTHING
                    """, (
                        session.session_id, session.agent_id, session.governing_receipt_id,
                        session.domain, session.vertical, session.policy_name,
                        json.dumps(session.constraint_set),
                        session.session_status, session.compliance_tier,
                        session.turn_count, session.total_drift,
                        session.chain_id, session.chain_genesis_hash, session.chain_tip_hash,
                        session.chain_sealed, session.last_verdict,
                        json.dumps(session.atf_layers_active),
                        session.started_at, json.dumps(session.metadata),
                    ))
                conn.commit()
        except Exception as exc:
            logger.warning(f"[OGR] persist_session failed: {exc}")

    def _update_session_turn(
        self,
        session_id: str,
        new_turn_count: int,
        total_drift: float,
        chain_tip_hash: str,
        last_verdict: str,
        new_status: str,
        halt_reason: Optional[str],
    ) -> None:
        # Always update in-memory cache regardless of DB availability
        cached = self._session_cache.get(session_id)
        if cached is not None:
            import dataclasses
            self._session_cache[session_id] = dataclasses.replace(
                cached,
                turn_count=new_turn_count,
                total_drift=total_drift,
                chain_tip_hash=chain_tip_hash,
                last_verdict=last_verdict,
                session_status=new_status,
                halt_reason=halt_reason,
            )
        if not self._db_url:
            return
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE atf_ogr_sessions
                        SET turn_count=%s, total_drift=%s, chain_tip_hash=%s,
                            last_verdict=%s, session_status=%s, halt_reason=%s
                        WHERE session_id=%s
                    """, (
                        new_turn_count, total_drift, chain_tip_hash,
                        last_verdict, new_status, halt_reason, session_id,
                    ))
                conn.commit()
        except Exception as exc:
            logger.warning(f"[OGR] update_session_turn failed: {exc}")

    def _close_session_db(
        self,
        session_id: str,
        seal_hash: Optional[str],
        closed_at: str,
        preserve_halted: bool = False,
    ) -> None:
        if not self._db_url:
            return
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    if preserve_halted:
                        # BEV-INV-003: HALTED status is the terminal forensic state.
                        # Sealing is allowed but the HALT record must not be overwritten.
                        cur.execute("""
                            UPDATE atf_ogr_sessions
                            SET chain_sealed=TRUE, chain_seal_hash=%s, closed_at=%s
                            WHERE session_id=%s AND session_status='HALTED'
                        """, (seal_hash, closed_at, session_id))
                    else:
                        cur.execute("""
                            UPDATE atf_ogr_sessions
                            SET session_status=%s, chain_sealed=TRUE,
                                chain_seal_hash=%s, closed_at=%s
                            WHERE session_id=%s AND session_status != 'HALTED'
                        """, (STATUS_CLOSED, seal_hash, closed_at, session_id))
                conn.commit()
        except Exception as exc:
            logger.warning(f"[OGR] close_session_db failed: {exc}")

    @staticmethod
    def _row_to_session(row: Dict[str, Any]) -> OGRSession:
        def _j(v: Any) -> Any:
            if isinstance(v, str):
                return json.loads(v)
            return v or {}

        def _jl(v: Any) -> List:
            if isinstance(v, str):
                return json.loads(v)
            return v or []

        return OGRSession(
            session_id=row["session_id"],
            agent_id=row["agent_id"],
            governing_receipt_id=row["governing_receipt_id"],
            domain=row["domain"],
            vertical=row["vertical"],
            policy_name=row["policy_name"],
            constraint_set=_j(row.get("constraint_set")),
            session_status=row["session_status"],
            compliance_tier=row["compliance_tier"],
            turn_count=int(row["turn_count"]),
            total_drift=float(row["total_drift"]),
            chain_id=row.get("chain_id"),
            chain_genesis_hash=row.get("chain_genesis_hash"),
            chain_tip_hash=row.get("chain_tip_hash"),
            chain_sealed=bool(row["chain_sealed"]),
            chain_seal_hash=row.get("chain_seal_hash"),
            last_verdict=row["last_verdict"],
            halt_reason=row.get("halt_reason"),
            oep_export_id=row.get("oep_export_id"),
            atf_layers_active=_jl(row.get("atf_layers_active")),
            started_at=str(row["started_at"]),
            closed_at=str(row["closed_at"]) if row.get("closed_at") else None,
            metadata=_j(row.get("metadata")),
        )
