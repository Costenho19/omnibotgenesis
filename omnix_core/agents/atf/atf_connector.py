"""
OMNIX Agent Trust Fabric — Governance Pipeline Connector
=========================================================
Bridges the governance decision pipeline (ADR-028) with the Agent Trust
Fabric (ADR-156), Temporal Authority (ADR-157), and Cross-Domain Trust
(ADR-158).

When a governance evaluation request includes ATF context (agent_id +
delegation_id), this connector:

    1. Resolves the Delegation Receipt (DR) for the agent
    2. Issues a Temporal Admissibility Record (TAR) at the exact nanosecond
       of admission — BEFORE the governance pipeline executes
    3. Returns ATFContext: DR + TAR + trust summary to embed in the receipt

The resulting governance receipt carries:
    - atf_context.delegation_id    — DR authorizing the agent
    - atf_context.tar_id           — TAR proving DR was valid at execution_ns
    - atf_context.execution_ns     — nanosecond-precise admission timestamp
    - atf_context.chain_root_id    — human origin of the agent's authority
    - atf_context.authority_budget — normalized authority at time of decision
    - atf_context.pqc_signed       — whether TAR is Dilithium-3 signed

This creates the complete governance chain:

    Human Tier-1
        │  DelegationReceipt (ATFDR-...)
        ▼
    Agent (AID-DOMAIN-...)
        │  TemporalAdmissibilityRecord (ATFTAR-...)
        ▼
    Governance Evaluation Request
        │  GovernanceReceipt (OMNIX-...-RECEIPTS)
        ▼
    Verifiable Decision Record

Every step is PQC-signed and independently verifiable.
The TAR.execution_ref field links back to the GovernanceReceipt ID.

Usage in gov_blueprint.py:
    from omnix_core.agents.atf.atf_connector import ATFConnector, ATFContext

    # At the start of evaluate():
    atf_ctx = ATFConnector.admit(
        agent_id=data.get("agent_id"),
        delegation_id=data.get("delegation_id"),
        task_action=f"governance_evaluation:{domain}:{asset}",
        execution_ref=receipt_id,  # from DecisionReceiptEngine
    )
    if atf_ctx:
        receipt["atf_context"] = atf_ctx.to_dict()

ADR-156/157 — Harold Nunes — OMNIX QUANTUM LTD — May 2026
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger("OMNIX.ATF.Connector")


@dataclass
class ATFContext:
    """
    ATF context embedded in a GovernanceReceipt.

    Provides the complete trust provenance chain for the agent that
    submitted the governance request:

        delegation_id    — ATFDR-... DR authorizing the agent
        tar_id           — ATFTAR-... TAR proving authority at admission_ns
        agent_id         — AID-DOMAIN-... of the requesting agent
        delegator_id     — AID or HUMAN of the delegator
        admission_status — ADMITTED | REJECTED | NOT_PRESENT
        execution_ns     — nanosecond Unix timestamp of TAR issuance
        execution_ts     — ISO UTC timestamp
        authority_budget — authority granted at time of decision
        chain_root_id    — chain_root_id of the DR (traces to human origin)
        domain           — governance domain of the DR
        pqc_signed       — True if TAR is Dilithium-3 signed
        connector_hash   — SHA-256 of this context dict (tamper detection)
    """
    delegation_id: str
    tar_id: str
    agent_id: str
    delegator_id: str
    admission_status: str
    execution_ns: int
    execution_ts: str
    authority_budget: float
    chain_root_id: str
    domain: str
    pqc_signed: bool
    connector_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def is_admitted(self) -> bool:
        return self.admission_status == "ADMITTED"

    def trust_summary(self) -> str:
        """One-line human-readable trust summary."""
        return (
            f"Agent {self.agent_id} | "
            f"DR {self.delegation_id} | "
            f"TAR {self.tar_id} | "
            f"budget={self.authority_budget:.0f} | "
            f"status={self.admission_status} | "
            f"ns={self.execution_ns}"
        )

    @staticmethod
    def absent() -> "ATFContext":
        """Sentinel for requests with no ATF context."""
        return ATFContext(
            delegation_id="",
            tar_id="",
            agent_id="",
            delegator_id="",
            admission_status="NOT_PRESENT",
            execution_ns=time.time_ns(),
            execution_ts="",
            authority_budget=0.0,
            chain_root_id="",
            domain="",
            pqc_signed=False,
            connector_hash="",
        )


class ATFConnector:
    """
    Connector between the governance pipeline and ATF.

    All methods are class-level (stateless) for zero-overhead import.
    The lattice and engines are lazily imported and instantiated per call
    to avoid circular imports and database connections at module load time.

    Thread safety: each call creates its own engine instances. Safe for
    concurrent use under WSGI multi-threading.
    """

    @classmethod
    def admit(
        cls,
        agent_id: Optional[str],
        delegation_id: Optional[str],
        task_action: str,
        execution_ref: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[ATFContext]:
        """
        Issue a TAR for a governance evaluation request.

        Called synchronously at the START of the governance pipeline,
        before any AI/AVM/veto logic executes. This ensures the TAR
        nanosecond timestamp precedes the governance decision.

        Args:
            agent_id:       AID of the requesting agent (or None)
            delegation_id:  ATFDR-... of the agent's active DR (or None)
            task_action:    Action string, e.g. "governance_evaluation:FINANCE:AAPL"
            execution_ref:  GovernanceReceipt ID to cross-reference (or None)
            metadata:       Additional context dict

        Returns:
            ATFContext (always) — admission_status tells whether ATF admitted
            None               — if agent_id and delegation_id are both absent
                                 (backward-compatible: legacy non-ATF requests)

        ATF admission does NOT block the governance pipeline.
        A REJECTED TAR is logged but does not prevent evaluation.
        The caller decides whether to block on rejected TARs.
        """
        if not agent_id and not delegation_id:
            return None

        try:
            return cls._do_admit(
                agent_id=agent_id or "",
                delegation_id=delegation_id or "",
                task_action=task_action,
                execution_ref=execution_ref,
                metadata=metadata or {},
            )
        except Exception as exc:
            logger.warning(f"[ATF.Connector] admit() non-blocking failure: {exc}")
            return None

    @classmethod
    def _do_admit(
        cls,
        agent_id: str,
        delegation_id: str,
        task_action: str,
        execution_ref: Optional[str],
        metadata: Dict[str, Any],
    ) -> ATFContext:
        from omnix_core.agents.atf.temporal_authority import TemporalAuthorityEngine
        from omnix_core.agents.atf.trust_lattice import TrustLattice

        lattice = TrustLattice()
        engine = TemporalAuthorityEngine()

        dr = None
        if delegation_id:
            dr = lattice._delegation_engine.get_delegation(delegation_id)

        if dr is None and agent_id:
            delegations = lattice._delegation_engine.list_delegations(
                delegate_id=agent_id, status="ACTIVE"
            )
            if delegations:
                dr = delegations[0]

        if dr is None:
            stub_dr = {
                "delegation_id": delegation_id or f"UNKNOWN-{agent_id}",
                "delegator_id": "UNKNOWN",
                "delegate_id": agent_id,
                "task_scope": {"action": task_action, "domain": "UNKNOWN"},
                "authority_budget_granted": 0.0,
                "authority_budget_delegator": 0.0,
                "status": "UNKNOWN",
                "chain_root_id": delegation_id or "",
                "expires_at": None,
            }
            tar = engine.admit_execution(
                delegation_receipt=stub_dr,
                agent_id=agent_id,
                task_action=task_action,
                execution_ref=execution_ref,
                metadata={**metadata, "connector_note": "DR not found in lattice"},
            )
            return cls._build_context(tar, stub_dr)

        tar = engine.admit_execution(
            delegation_receipt=dr,
            agent_id=agent_id,
            task_action=task_action,
            execution_ref=execution_ref,
            metadata=metadata,
        )

        logger.info(
            f"[ATF.Connector] TAR={tar.tar_id} "
            f"agent={agent_id} DR={dr.delegation_id if hasattr(dr, 'delegation_id') else delegation_id} "
            f"status={tar.admission_status} execution_ref={execution_ref}"
        )

        return cls._build_context(
            tar,
            dr.to_dict() if hasattr(dr, "to_dict") else dr,
        )

    @staticmethod
    def _build_context(tar: Any, dr: Dict[str, Any]) -> ATFContext:
        fields = {
            "delegation_id":    tar.delegation_id,
            "tar_id":           tar.tar_id,
            "agent_id":         tar.agent_id,
            "delegator_id":     dr.get("delegator_id", ""),
            "admission_status": tar.admission_status,
            "execution_ns":     tar.execution_ns,
            "execution_ts":     tar.execution_ts,
            "authority_budget": tar.authority_budget,
            "chain_root_id":    tar.chain_root_id,
            "domain":           tar.domain,
            "pqc_signed":       tar.pqc_signature is not None,
        }
        connector_hash = hashlib.sha256(
            json.dumps(fields, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

        return ATFContext(**fields, connector_hash=connector_hash)

    @classmethod
    def embed_in_receipt(
        cls,
        receipt: Dict[str, Any],
        atf_ctx: Optional[ATFContext],
    ) -> Dict[str, Any]:
        """
        Embed ATFContext into a governance receipt dict.
        Non-destructive: returns the same dict with atf_context added.
        Safe to call with atf_ctx=None (no-op).
        """
        if atf_ctx is not None and atf_ctx.admission_status != "NOT_PRESENT":
            receipt["atf_context"] = atf_ctx.to_dict()
            receipt["atf_tar_id"] = atf_ctx.tar_id
            receipt["atf_delegation_id"] = atf_ctx.delegation_id
            receipt["atf_chain_root_id"] = atf_ctx.chain_root_id
        return receipt

    @classmethod
    def verify_chain(
        cls,
        receipt: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Verify the full ATF trust chain for a governance receipt.

        Given a GovernanceReceipt dict with an embedded atf_context,
        reconstructs the DR→TAR→GovernanceReceipt chain and verifies:
            - DR content hash
            - DR PQC signature
            - DR MAR invariant
            - TAR content hash
            - TAR admission status
            - TAR execution_ref matches the receipt_id

        Returns a dict with full verification status.
        """
        atf = receipt.get("atf_context")
        if not atf:
            return {
                "atf_present": False,
                "fully_verified": False,
                "reason": "No ATF context in this receipt",
            }

        result: Dict[str, Any] = {
            "atf_present": True,
            "delegation_id": atf.get("delegation_id"),
            "tar_id": atf.get("tar_id"),
            "agent_id": atf.get("agent_id"),
            "chain_root_id": atf.get("chain_root_id"),
            "authority_budget": atf.get("authority_budget"),
            "execution_ns": atf.get("execution_ns"),
            "admission_status": atf.get("admission_status"),
            "pqc_signed": atf.get("pqc_signed"),
            "dr_verified": False,
            "tar_verified": False,
            "fully_verified": False,
        }

        try:
            from omnix_core.agents.atf.trust_lattice import TrustLattice
            from omnix_core.agents.atf.temporal_authority import TemporalAuthorityEngine

            lattice = TrustLattice()
            engine = TemporalAuthorityEngine()

            delegation_id = atf.get("delegation_id", "")
            tar_id = atf.get("tar_id", "")

            if delegation_id:
                dr = lattice._delegation_engine.get_delegation(delegation_id)
                if dr:
                    dr_vr = lattice._delegation_engine.verify_receipt(dr)
                    result["dr_verified"] = dr_vr.get("fully_verified", False)
                    result["dr_verification"] = dr_vr

            if tar_id:
                tar = engine.get_tar(tar_id)
                if tar:
                    tar_vr = engine.verify_tar(tar)
                    result["tar_verified"] = tar_vr.get("fully_verified", False)
                    result["tar_verification"] = tar_vr
                    receipt_id = receipt.get("receipt_id", "")
                    if receipt_id and tar.execution_ref:
                        result["execution_ref_match"] = (tar.execution_ref == receipt_id)

            result["fully_verified"] = (
                result["dr_verified"] and
                result["tar_verified"] and
                atf.get("admission_status") == "ADMITTED"
            )

        except Exception as exc:
            logger.warning(f"[ATF.Connector] verify_chain failed: {exc}")
            result["error"] = str(exc)

        return result
