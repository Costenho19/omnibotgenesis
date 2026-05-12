"""
OMNIX Agent Trust Fabric — Trust Lattice
ADR-156: Directed acyclic graph of agents and delegation receipts.

The Trust Lattice is the central data structure of the ATF:
  - Nodes  → AgentIdentity records (registered agents)
  - Edges  → DelegationReceipt records (signed delegation events)
  - Root   → human Tier-1 operator or Tier-2 acting under Tier-1 authority

Key properties guaranteed by the lattice:
  - Acyclicity: delegation_depth strictly increases — no cycles possible
  - Monotonic authority: budget strictly decreases root → leaf
  - Full traceability: any leaf traces to its human root via chain_root_id
  - Independent verifiability: verify_chain() needs no platform access

ADR-156 — Harold Nunes — OMNIX QUANTUM LTD — May 2026
"""
from __future__ import annotations

import logging
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from omnix_core.agents.atf.agent_identity import AgentIdentity, AgentIdentityEngine
from omnix_core.agents.atf.delegation_receipt import (
    DelegationReceipt,
    DelegationReceiptEngine,
    AuthorityExpansionViolation,
)

logger = logging.getLogger("OMNIX.ATF.Lattice")


@dataclass
class ChainNode:
    """A single node in a verified delegation chain path."""
    depth: int
    actor_id: str
    actor_type: str
    delegation_id: Optional[str]
    authority_budget: float
    authority_reduction_pct: float
    pqc_signed: bool
    hash_valid: bool
    pqc_signature_valid: bool
    task_scope: Dict[str, Any]
    created_at: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VerificationResult:
    """
    Full verification result for an agent's delegation chain.

    Fields:
        agent_id        — the agent whose chain was verified
        chain           — ordered list from root (depth 0) to leaf
        fully_verified  — True if every receipt in the chain is valid
        chain_depth     — total depth of the chain
        root_actor_id   — originating human/system at depth 0
        leaf_budget     — authority budget at the leaf (the acting agent)
        mar_valid       — monotonic authority reduction holds throughout
        all_pqc_signed  — every receipt in the chain has a PQC signature
        chain_root_id   — ID of the root delegation receipt
        verified_at     — ISO UTC timestamp
        failure_reason  — human-readable failure description (or None)
    """
    agent_id: str
    chain: List[ChainNode]
    fully_verified: bool
    chain_depth: int
    root_actor_id: str
    leaf_budget: float
    mar_valid: bool
    all_pqc_signed: bool
    chain_root_id: Optional[str]
    verified_at: str
    failure_reason: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["chain"] = [n.to_dict() for n in self.chain]
        return d

    def summary(self) -> Dict[str, Any]:
        return {
            "agent_id":       self.agent_id,
            "fully_verified": self.fully_verified,
            "chain_depth":    self.chain_depth,
            "leaf_budget":    self.leaf_budget,
            "mar_valid":      self.mar_valid,
            "all_pqc_signed": self.all_pqc_signed,
            "root_actor_id":  self.root_actor_id,
            "chain_root_id":  self.chain_root_id,
            "verified_at":    self.verified_at,
        }


class TrustLattice:
    """
    The OMNIX Agent Trust Fabric lattice — the authoritative graph of
    agent identities and delegation receipts.

    Design contract:
        register_agent()     → AgentIdentity (delegates to AgentIdentityEngine)
        delegate()           → DelegationReceipt (delegates to DelegationReceiptEngine)
        verify_chain()       → VerificationResult for any agent or delegation
        get_lattice_state()  → current snapshot of all nodes and edges
        chain_completeness() → ATF CCS — completeness score for a chain

    Thread safety: internal routing tables protected by a lock.
    The underlying engines handle their own thread safety.
    """

    def __init__(self, db_url: Optional[str] = None):
        self._identity_engine = AgentIdentityEngine(db_url=db_url)
        self._delegation_engine = DelegationReceiptEngine(db_url=db_url)
        self._agent_delegations: Dict[str, List[str]] = {}
        self._lock = threading.Lock()

    def ensure_tables(self) -> bool:
        a = self._identity_engine.ensure_tables()
        b = self._delegation_engine.ensure_tables()
        return a and b

    def register_agent(
        self,
        display_name: str,
        domain: str,
        vertical: str = "general",
        authority_budget: float = 50.0,
        registered_by: str = "system",
        registration_tier: int = 2,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentIdentity:
        """Register a new agent into the trust lattice."""
        identity = self._identity_engine.register_agent(
            display_name=display_name,
            domain=domain,
            vertical=vertical,
            authority_budget=authority_budget,
            registered_by=registered_by,
            registration_tier=registration_tier,
            capabilities=capabilities,
            metadata=metadata,
        )
        with self._lock:
            self._agent_delegations.setdefault(identity.agent_id, [])
        return identity

    def delegate(
        self,
        delegator_id: str,
        delegate_id: str,
        task_scope: Dict[str, Any],
        authority_budget_delegator: float,
        authority_budget_granted: float,
        delegator_public_key: str = "",
        delegator_sk_b64: Optional[str] = None,
        parent_delegation_id: Optional[str] = None,
        chain_root_id: Optional[str] = None,
        delegation_depth: int = 0,
        expires_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DelegationReceipt:
        """
        Create a delegation from delegator to delegate.

        Enforces ATF-INV-001 (Monotonic Authority Reduction):
        Raises AuthorityExpansionViolation if granted > delegator budget.
        """
        receipt = self._delegation_engine.create_delegation(
            delegator_id=delegator_id,
            delegate_id=delegate_id,
            task_scope=task_scope,
            authority_budget_delegator=authority_budget_delegator,
            authority_budget_granted=authority_budget_granted,
            delegator_public_key=delegator_public_key,
            delegator_sk_b64=delegator_sk_b64,
            parent_delegation_id=parent_delegation_id,
            chain_root_id=chain_root_id,
            delegation_depth=delegation_depth,
            expires_at=expires_at,
            metadata=metadata,
        )
        with self._lock:
            self._agent_delegations.setdefault(delegate_id, [])
            self._agent_delegations[delegate_id].append(receipt.delegation_id)
        return receipt

    def verify_chain(
        self,
        agent_id: Optional[str] = None,
        delegation_id: Optional[str] = None,
    ) -> VerificationResult:
        """
        Verify the full delegation chain for an agent or a specific receipt.

        The verification is self-contained: every DelegationReceipt embeds
        the delegator's public key, enabling independent verification without
        platform access. This mirrors OMNIX's governance receipt model.

        Args:
            agent_id:      Verify the most recent active delegation chain for this agent.
            delegation_id: Verify the chain ending at this specific delegation receipt.

        Returns:
            VerificationResult with the full path from root to leaf.
        """
        now = datetime.now(timezone.utc).isoformat()

        receipt = self._resolve_leaf_receipt(agent_id, delegation_id)

        if receipt is None:
            return VerificationResult(
                agent_id=agent_id or "unknown",
                chain=[],
                fully_verified=False,
                chain_depth=0,
                root_actor_id="unknown",
                leaf_budget=0.0,
                mar_valid=False,
                all_pqc_signed=False,
                chain_root_id=None,
                verified_at=now,
                failure_reason="No delegation receipt found for agent",
            )

        chain_receipts = self._collect_chain(receipt)
        chain_nodes: List[ChainNode] = []
        fully_verified = True
        mar_valid = True
        all_pqc_signed = True
        failure_reason: Optional[str] = None
        prev_budget = 100.0

        for i, dr in enumerate(chain_receipts):
            vr = self._delegation_engine.verify_receipt(dr)

            if not vr["hash_valid"]:
                fully_verified = False
                failure_reason = f"Content hash mismatch at depth {dr.delegation_depth} ({dr.delegation_id})"

            if not vr["mar_invariant_valid"]:
                mar_valid = False
                fully_verified = False
                failure_reason = (
                    f"ATF-INV-001 VIOLATED at depth {dr.delegation_depth}: "
                    f"granted={dr.authority_budget_granted} > "
                    f"delegator={dr.authority_budget_delegator}"
                )

            if dr.authority_budget_granted > prev_budget and i > 0:
                mar_valid = False
                fully_verified = False
                failure_reason = (
                    f"Authority expansion detected at depth {dr.delegation_depth}: "
                    f"{dr.authority_budget_granted} > {prev_budget} (cross-receipt)"
                )
            prev_budget = dr.authority_budget_granted

            if dr.pqc_signature is None:
                all_pqc_signed = False

            node = ChainNode(
                depth=dr.delegation_depth,
                actor_id=dr.delegate_id,
                actor_type="agent" if dr.delegation_depth > 0 else "human_operator",
                delegation_id=dr.delegation_id,
                authority_budget=dr.authority_budget_granted,
                authority_reduction_pct=dr.authority_reduction_pct(),
                pqc_signed=dr.pqc_signature is not None,
                hash_valid=vr["hash_valid"],
                pqc_signature_valid=vr["pqc_signature_valid"],
                task_scope=dr.task_scope,
                created_at=dr.created_at,
            )
            chain_nodes.append(node)

        root_actor = chain_receipts[0].delegator_id if chain_receipts else "unknown"
        leaf_budget = chain_receipts[-1].authority_budget_granted if chain_receipts else 0.0
        chain_root_id = chain_receipts[0].chain_root_id if chain_receipts else None

        return VerificationResult(
            agent_id=receipt.delegate_id,
            chain=chain_nodes,
            fully_verified=fully_verified,
            chain_depth=len(chain_nodes),
            root_actor_id=root_actor,
            leaf_budget=leaf_budget,
            mar_valid=mar_valid,
            all_pqc_signed=all_pqc_signed,
            chain_root_id=chain_root_id,
            verified_at=now,
            failure_reason=failure_reason,
        )

    def _resolve_leaf_receipt(
        self,
        agent_id: Optional[str],
        delegation_id: Optional[str],
    ) -> Optional[DelegationReceipt]:
        if delegation_id:
            return self._delegation_engine.get_delegation(delegation_id)
        if agent_id:
            with self._lock:
                ids = self._agent_delegations.get(agent_id, [])
            for did in reversed(ids):
                dr = self._delegation_engine.get_delegation(did)
                if dr and dr.status == "ACTIVE":
                    return dr
            delegations = self._delegation_engine.list_delegations(
                delegate_id=agent_id, status="ACTIVE"
            )
            if delegations:
                return sorted(delegations, key=lambda d: d.delegation_depth, reverse=True)[0]
        return None

    def _collect_chain(self, leaf: DelegationReceipt) -> List[DelegationReceipt]:
        """
        Traverse the delegation chain from the leaf back to the root.
        Returns the chain ordered from root (depth 0) to leaf.
        Guards against cycles with a visited set.
        """
        chain: List[DelegationReceipt] = [leaf]
        visited = {leaf.delegation_id}
        current = leaf

        MAX_DEPTH = 50
        while current.parent_delegation_id and len(chain) < MAX_DEPTH:
            parent_id = current.parent_delegation_id
            if parent_id in visited:
                logger.error(f"[ATF.Lattice] Cycle detected in delegation chain at {parent_id}")
                break
            parent = self._delegation_engine.get_delegation(parent_id)
            if parent is None:
                logger.warning(f"[ATF.Lattice] Parent receipt {parent_id} not found — chain truncated")
                break
            visited.add(parent_id)
            chain.append(parent)
            current = parent

        chain.reverse()
        return chain

    def get_lattice_state(self) -> Dict[str, Any]:
        """
        Return a snapshot of the current trust lattice state.
        Includes all registered agents and all active delegation receipts.
        """
        agents = self._identity_engine.list_agents()
        all_delegations: List[DelegationReceipt] = []
        for a in agents:
            all_delegations.extend(
                self._delegation_engine.list_delegations(delegate_id=a.agent_id)
            )

        return {
            "agents": [a.trust_summary() for a in agents],
            "delegations": [d.trust_summary() for d in all_delegations],
            "total_agents": len(agents),
            "total_delegations": len(all_delegations),
            "snapshot_at": datetime.now(timezone.utc).isoformat(),
        }

    def chain_completeness_score(self, agent_id: str) -> Dict[str, Any]:
        """
        ATF Chain Completeness Score — analogous to CCS (ADR-155) but for agent chains.

        Components (max 100 points):
            chain_integrity      40 pts  — all receipt hashes valid; -10 per break
            pqc_coverage         30 pts  — all receipts PQC-signed; -10 per unsigned
            mar_score            20 pts  — MAR invariant holds throughout
            depth_score          10 pts  — at least 1 delegation exists

        Verdicts:
            ≥ 90  COMPLETE      — fully defensible delegation chain
            70-89 DEGRADED      — minor gaps; investigation recommended
            50-69 PARTIAL       — significant gaps; audit uncertain
            < 50  COMPROMISED   — chain cannot be trusted

        Returns dict with score, verdict, and component breakdown.
        """
        result = self.verify_chain(agent_id=agent_id)

        if not result.chain:
            return {
                "agent_id": agent_id,
                "atf_ccs": 0,
                "atf_ccs_verdict": "NO_DATA",
                "components": {},
                "fully_verified": False,
            }

        total = 0.0
        components: Dict[str, Any] = {}

        hash_breaks = sum(1 for n in result.chain if not n.hash_valid)
        chain_integrity = max(0.0, 40.0 - hash_breaks * 10.0)
        components["chain_integrity_score"] = chain_integrity
        total += chain_integrity

        unsigned_count = sum(1 for n in result.chain if not n.pqc_signed)
        pqc_coverage = max(0.0, 30.0 - unsigned_count * 10.0)
        components["pqc_coverage_score"] = pqc_coverage
        total += pqc_coverage

        mar_score = 20.0 if result.mar_valid else 0.0
        components["mar_invariant_score"] = mar_score
        total += mar_score

        depth_score = 10.0 if result.chain_depth >= 1 else 0.0
        components["depth_score"] = depth_score
        total += depth_score

        ccs = round(total, 1)
        if ccs >= 90:
            verdict = "COMPLETE"
        elif ccs >= 70:
            verdict = "DEGRADED"
        elif ccs >= 50:
            verdict = "PARTIAL"
        else:
            verdict = "COMPROMISED"

        return {
            "agent_id":          agent_id,
            "atf_ccs":           ccs,
            "atf_ccs_verdict":   verdict,
            "components":        components,
            "chain_depth":       result.chain_depth,
            "leaf_budget":       result.leaf_budget,
            "all_pqc_signed":    result.all_pqc_signed,
            "mar_valid":         result.mar_valid,
            "fully_verified":    result.fully_verified,
            "root_actor_id":     result.root_actor_id,
        }
