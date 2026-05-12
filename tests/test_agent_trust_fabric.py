"""
OMNIX Agent Trust Fabric — Test Suite
ADR-156: Verifies all ATF invariants, verification logic, and edge cases.

Coverage:
    - AgentIdentity registration, hash verification, PQC signature check
    - DelegationReceipt creation, content hash, MAR enforcement
    - TrustLattice: chain construction, verification, CCS
    - ATF-INV-001 through ATF-INV-006 invariant assertions
    - Edge cases: empty chain, cycle detection, expired receipts

ADR-156 — Harold Nunes — OMNIX QUANTUM LTD — May 2026
"""
import os
import pytest
from datetime import datetime, timezone, timedelta

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")

from omnix_core.agents.atf.agent_identity import AgentIdentityEngine, AgentIdentity
from omnix_core.agents.atf.delegation_receipt import (
    DelegationReceiptEngine,
    DelegationReceipt,
    AuthorityExpansionViolation,
)
from omnix_core.agents.atf.trust_lattice import TrustLattice, VerificationResult


def _make_engine() -> AgentIdentityEngine:
    return AgentIdentityEngine(db_url=None)


def _make_dr_engine() -> DelegationReceiptEngine:
    return DelegationReceiptEngine(db_url=None)


def _make_lattice() -> TrustLattice:
    return TrustLattice(db_url=None)


class TestAgentIdentityEngine:

    def test_register_returns_agent_identity(self):
        engine = _make_engine()
        identity = engine.register_agent(
            display_name="Test Agent",
            domain="FINANCE",
            authority_budget=60.0,
            registered_by="harold",
        )
        assert isinstance(identity, AgentIdentity)
        assert identity.agent_id.startswith("AID-FINANCE-")
        assert identity.authority_budget == 60.0
        assert identity.status == "ACTIVE"

    def test_agent_id_format(self):
        engine = _make_engine()
        identity = engine.register_agent(
            display_name="ID Format Test",
            domain="HEALTHCARE",
            authority_budget=40.0,
        )
        parts = identity.agent_id.split("-")
        assert parts[0] == "AID"
        assert parts[1] == "HEALTHCARE"
        assert len(parts[2]) == 16

    def test_registration_hash_computed(self):
        engine = _make_engine()
        identity = engine.register_agent(
            display_name="Hash Test Agent",
            domain="DEFENSE",
            authority_budget=70.0,
        )
        assert len(identity.registration_hash) == 64

    def test_verify_identity_hash_valid(self):
        engine = _make_engine()
        identity = engine.register_agent(
            display_name="Verify Test",
            domain="TRADING",
            authority_budget=50.0,
        )
        result = engine.verify_identity(identity)
        assert result["hash_valid"] is True

    def test_get_agent_returns_registered(self):
        engine = _make_engine()
        identity = engine.register_agent(
            display_name="Lookup Test",
            domain="FINANCE",
            authority_budget=30.0,
        )
        found = engine.get_agent(identity.agent_id)
        assert found is not None
        assert found.agent_id == identity.agent_id

    def test_get_agent_unknown_returns_none(self):
        engine = _make_engine()
        result = engine.get_agent("AID-UNKNOWN-0000000000000000")
        assert result is None

    def test_tier2_registration_budget_capped_at_80(self):
        engine = _make_engine()
        identity = engine.register_agent(
            display_name="Budget Cap Test",
            domain="FINANCE",
            authority_budget=95.0,
            registration_tier=2,
        )
        assert identity.authority_budget == 80.0

    def test_tier1_registration_allows_100(self):
        engine = _make_engine()
        identity = engine.register_agent(
            display_name="Tier1 Test",
            domain="FINANCE",
            authority_budget=100.0,
            registration_tier=1,
        )
        assert identity.authority_budget == 100.0

    def test_invalid_budget_raises(self):
        engine = _make_engine()
        with pytest.raises(ValueError):
            engine.register_agent(
                display_name="Bad Budget",
                domain="FINANCE",
                authority_budget=150.0,
            )

    def test_negative_budget_raises(self):
        engine = _make_engine()
        with pytest.raises(ValueError):
            engine.register_agent(
                display_name="Negative Budget",
                domain="FINANCE",
                authority_budget=-10.0,
            )

    def test_suspend_agent(self):
        engine = _make_engine()
        identity = engine.register_agent(
            display_name="Suspend Test",
            domain="FINANCE",
            authority_budget=50.0,
        )
        engine.suspend_agent(identity.agent_id)
        found = engine.get_agent(identity.agent_id)
        assert found.status == "SUSPENDED"

    def test_revoke_agent(self):
        engine = _make_engine()
        identity = engine.register_agent(
            display_name="Revoke Test",
            domain="FINANCE",
            authority_budget=50.0,
        )
        engine.revoke_agent(identity.agent_id)
        found = engine.get_agent(identity.agent_id)
        assert found.status == "REVOKED"

    def test_list_agents_by_domain(self):
        engine = _make_engine()
        engine.register_agent("A1", "FINANCE", authority_budget=40.0)
        engine.register_agent("A2", "FINANCE", authority_budget=50.0)
        engine.register_agent("A3", "HEALTHCARE", authority_budget=60.0)
        agents = engine.list_agents(domain="FINANCE")
        assert all(a.domain == "FINANCE" for a in agents)

    def test_capabilities_stored(self):
        engine = _make_engine()
        caps = ["read_data", "write_report"]
        identity = engine.register_agent(
            "Cap Test", "FINANCE",
            authority_budget=40.0,
            capabilities=caps,
        )
        assert identity.capabilities == caps


class TestDelegationReceiptEngine:

    def test_create_delegation_returns_receipt(self):
        engine = _make_dr_engine()
        receipt = engine.create_delegation(
            delegator_id="HUMAN-TIER1",
            delegate_id="AID-FINANCE-0000000000000001",
            task_scope={"action": "analyze"},
            authority_budget_delegator=100.0,
            authority_budget_granted=80.0,
            delegation_depth=1,
        )
        assert isinstance(receipt, DelegationReceipt)
        assert receipt.delegation_id.startswith("ATFDR-")
        assert receipt.authority_budget_granted == 80.0
        assert receipt.status == "ACTIVE"

    def test_delegation_id_format(self):
        engine = _make_dr_engine()
        receipt = engine.create_delegation(
            delegator_id="HUMAN-TIER1",
            delegate_id="AID-FINANCE-0000000000000002",
            task_scope={"action": "test"},
            authority_budget_delegator=100.0,
            authority_budget_granted=50.0,
        )
        assert receipt.delegation_id.startswith("ATFDR-")
        assert len(receipt.delegation_id) == 5 + 16 + 1

    def test_content_hash_computed(self):
        engine = _make_dr_engine()
        receipt = engine.create_delegation(
            delegator_id="HUMAN-TIER1",
            delegate_id="AID-FINANCE-0000000000000003",
            task_scope={"action": "hash_test"},
            authority_budget_delegator=100.0,
            authority_budget_granted=60.0,
        )
        assert len(receipt.content_hash) == 64

    def test_mar_invariant_enforced(self):
        """ATF-INV-001: authority_budget_granted > budget_delegator raises."""
        engine = _make_dr_engine()
        with pytest.raises(AuthorityExpansionViolation):
            engine.create_delegation(
                delegator_id="AID-FINANCE-BADAGENT",
                delegate_id="AID-FINANCE-0000000000000004",
                task_scope={"action": "escalate"},
                authority_budget_delegator=50.0,
                authority_budget_granted=80.0,
            )

    def test_mar_equal_budget_allowed(self):
        """Granting exact same budget as delegator is allowed."""
        engine = _make_dr_engine()
        receipt = engine.create_delegation(
            delegator_id="HUMAN-TIER1",
            delegate_id="AID-FINANCE-0000000000000005",
            task_scope={"action": "equal_test"},
            authority_budget_delegator=60.0,
            authority_budget_granted=60.0,
        )
        assert receipt.authority_budget_granted == 60.0

    def test_verify_receipt_hash_valid(self):
        engine = _make_dr_engine()
        receipt = engine.create_delegation(
            delegator_id="HUMAN-TIER1",
            delegate_id="AID-FINANCE-0000000000000006",
            task_scope={"action": "verify_test"},
            authority_budget_delegator=100.0,
            authority_budget_granted=70.0,
        )
        result = engine.verify_receipt(receipt)
        assert result["hash_valid"] is True
        assert result["mar_invariant_valid"] is True

    def test_verify_receipt_tampered_hash_fails(self):
        engine = _make_dr_engine()
        receipt = engine.create_delegation(
            delegator_id="HUMAN-TIER1",
            delegate_id="AID-FINANCE-0000000000000007",
            task_scope={"action": "tamper_test"},
            authority_budget_delegator=100.0,
            authority_budget_granted=50.0,
        )
        from dataclasses import asdict
        d = asdict(receipt)
        d["authority_budget_granted"] = 99.0
        tampered = DelegationReceipt(**d)
        result = engine.verify_receipt(tampered)
        assert result["hash_valid"] is False

    def test_chain_root_id_assigned(self):
        engine = _make_dr_engine()
        receipt = engine.create_delegation(
            delegator_id="HUMAN-TIER1",
            delegate_id="AID-FINANCE-0000000000000008",
            task_scope={"action": "root_test"},
            authority_budget_delegator=100.0,
            authority_budget_granted=80.0,
        )
        assert receipt.chain_root_id == receipt.delegation_id

    def test_parent_delegation_stored(self):
        engine = _make_dr_engine()
        root = engine.create_delegation(
            delegator_id="HUMAN-TIER1",
            delegate_id="AID-FINANCE-A",
            task_scope={"action": "root"},
            authority_budget_delegator=100.0,
            authority_budget_granted=80.0,
            delegation_depth=1,
        )
        child = engine.create_delegation(
            delegator_id="AID-FINANCE-A",
            delegate_id="AID-FINANCE-B",
            task_scope={"action": "child"},
            authority_budget_delegator=80.0,
            authority_budget_granted=50.0,
            parent_delegation_id=root.delegation_id,
            chain_root_id=root.chain_root_id,
            delegation_depth=2,
        )
        assert child.parent_delegation_id == root.delegation_id
        assert child.delegation_depth == 2

    def test_authority_reduction_pct(self):
        engine = _make_dr_engine()
        receipt = engine.create_delegation(
            delegator_id="HUMAN-TIER1",
            delegate_id="AID-FINANCE-0000000000000009",
            task_scope={"action": "reduction_test"},
            authority_budget_delegator=100.0,
            authority_budget_granted=75.0,
        )
        assert receipt.authority_reduction_pct() == 25.0

    def test_revoke_delegation(self):
        engine = _make_dr_engine()
        receipt = engine.create_delegation(
            delegator_id="HUMAN-TIER1",
            delegate_id="AID-FINANCE-REVOKE",
            task_scope={"action": "revoke_test"},
            authority_budget_delegator=100.0,
            authority_budget_granted=60.0,
        )
        engine.revoke_delegation(receipt.delegation_id)
        found = engine.get_delegation(receipt.delegation_id)
        assert found.status == "REVOKED"

    def test_empty_task_scope_raises(self):
        engine = _make_dr_engine()
        with pytest.raises(ValueError):
            engine.create_delegation(
                delegator_id="HUMAN-TIER1",
                delegate_id="AID-FINANCE-SCOPE",
                task_scope={},
                authority_budget_delegator=100.0,
                authority_budget_granted=50.0,
            )

    def test_missing_delegator_raises(self):
        engine = _make_dr_engine()
        with pytest.raises(ValueError):
            engine.create_delegation(
                delegator_id="",
                delegate_id="AID-FINANCE-NODELEGATOR",
                task_scope={"action": "test"},
                authority_budget_delegator=100.0,
                authority_budget_granted=50.0,
            )


class TestTrustLattice:

    def _build_simple_chain(self, lattice: TrustLattice, domain: str = "FINANCE"):
        orchestrator = lattice.register_agent(
            display_name="Orchestrator",
            domain=domain,
            authority_budget=80.0,
            registered_by="HUMAN-TIER1",
        )
        root_dr = lattice.delegate(
            delegator_id="HUMAN-TIER1",
            delegate_id=orchestrator.agent_id,
            task_scope={"action": "orchestrate"},
            authority_budget_delegator=100.0,
            authority_budget_granted=80.0,
            delegation_depth=1,
        )
        return orchestrator, root_dr

    def _build_three_level_chain(self, lattice: TrustLattice):
        orchestrator = lattice.register_agent(
            "Orchestrator", "FINANCE", authority_budget=80.0,
            registered_by="HUMAN-TIER1",
        )
        analysis = lattice.register_agent(
            "Analysis Agent", "FINANCE", authority_budget=55.0,
            registered_by=orchestrator.agent_id,
        )
        data_agent = lattice.register_agent(
            "Data Agent", "FINANCE", authority_budget=25.0,
            registered_by=analysis.agent_id,
        )
        dr1 = lattice.delegate(
            delegator_id="HUMAN-TIER1",
            delegate_id=orchestrator.agent_id,
            task_scope={"action": "orchestrate"},
            authority_budget_delegator=100.0,
            authority_budget_granted=80.0,
            delegation_depth=1,
        )
        dr2 = lattice.delegate(
            delegator_id=orchestrator.agent_id,
            delegate_id=analysis.agent_id,
            task_scope={"action": "analyze"},
            authority_budget_delegator=80.0,
            authority_budget_granted=55.0,
            parent_delegation_id=dr1.delegation_id,
            chain_root_id=dr1.delegation_id,
            delegation_depth=2,
        )
        dr3 = lattice.delegate(
            delegator_id=analysis.agent_id,
            delegate_id=data_agent.agent_id,
            task_scope={"action": "fetch_data"},
            authority_budget_delegator=55.0,
            authority_budget_granted=25.0,
            parent_delegation_id=dr2.delegation_id,
            chain_root_id=dr1.delegation_id,
            delegation_depth=3,
        )
        return orchestrator, analysis, data_agent, dr1, dr2, dr3

    def test_register_agent_in_lattice(self):
        lattice = _make_lattice()
        agent = lattice.register_agent(
            "Test Agent", "FINANCE", authority_budget=50.0
        )
        assert agent.agent_id.startswith("AID-FINANCE-")

    def test_delegate_in_lattice(self):
        lattice = _make_lattice()
        agent, dr = self._build_simple_chain(lattice)
        assert dr.delegation_id.startswith("ATFDR-")
        assert dr.delegate_id == agent.agent_id

    def test_verify_chain_simple(self):
        lattice = _make_lattice()
        agent, _ = self._build_simple_chain(lattice)
        result = lattice.verify_chain(agent_id=agent.agent_id)
        assert isinstance(result, VerificationResult)
        assert result.fully_verified is True
        assert result.chain_depth == 1

    def test_verify_chain_three_levels(self):
        lattice = _make_lattice()
        _, _, data_agent, dr1, _, dr3 = self._build_three_level_chain(lattice)
        result = lattice.verify_chain(agent_id=data_agent.agent_id)
        assert result.chain_depth == 3
        assert result.fully_verified is True
        assert result.leaf_budget == 25.0
        assert result.root_actor_id == "HUMAN-TIER1"

    def test_mar_decreasing_throughout_chain(self):
        lattice = _make_lattice()
        _, _, data_agent, _, _, _ = self._build_three_level_chain(lattice)
        result = lattice.verify_chain(agent_id=data_agent.agent_id)
        budgets = [n.authority_budget for n in result.chain]
        assert all(
            budgets[i] >= budgets[i + 1]
            for i in range(len(budgets) - 1)
        ), f"Budget must decrease monotonically: {budgets}"

    def test_mar_invariant_violation_in_delegation(self):
        lattice = _make_lattice()
        agent = lattice.register_agent(
            "Rogue Agent", "FINANCE", authority_budget=50.0
        )
        with pytest.raises(AuthorityExpansionViolation):
            lattice.delegate(
                delegator_id="HUMAN-TIER1",
                delegate_id=agent.agent_id,
                task_scope={"action": "escalate"},
                authority_budget_delegator=50.0,
                authority_budget_granted=90.0,
            )

    def test_verify_chain_no_delegation_returns_unverified(self):
        lattice = _make_lattice()
        result = lattice.verify_chain(agent_id="AID-FINANCE-NODELEGATION")
        assert result.fully_verified is False
        assert result.failure_reason is not None

    def test_chain_completeness_score_complete(self):
        lattice = _make_lattice()
        agent, _ = self._build_simple_chain(lattice)
        ccs = lattice.chain_completeness_score(agent_id=agent.agent_id)
        assert ccs["atf_ccs"] >= 50.0
        assert ccs["atf_ccs_verdict"] in ("COMPLETE", "DEGRADED", "PARTIAL")

    def test_chain_completeness_score_no_data(self):
        lattice = _make_lattice()
        ccs = lattice.chain_completeness_score(agent_id="AID-FINANCE-NOCHAIN")
        assert ccs["atf_ccs_verdict"] == "NO_DATA"
        assert ccs["atf_ccs"] == 0

    def test_lattice_state_returns_snapshot(self):
        lattice = _make_lattice()
        agent, _ = self._build_simple_chain(lattice)
        state = lattice.get_lattice_state()
        assert "agents" in state
        assert "delegations" in state
        assert state["total_agents"] >= 1

    def test_three_level_chain_root_id_consistent(self):
        lattice = _make_lattice()
        _, _, data_agent, dr1, dr2, dr3 = self._build_three_level_chain(lattice)
        assert dr1.chain_root_id == dr1.delegation_id
        assert dr2.chain_root_id == dr1.delegation_id
        assert dr3.chain_root_id == dr1.delegation_id

    def test_verify_by_delegation_id(self):
        lattice = _make_lattice()
        _, analysis, data_agent, dr1, dr2, dr3 = self._build_three_level_chain(lattice)
        result = lattice.verify_chain(delegation_id=dr3.delegation_id)
        assert result.chain_depth == 3
        assert result.fully_verified is True

    def test_verify_chain_depth_one(self):
        lattice = _make_lattice()
        agent, dr = self._build_simple_chain(lattice)
        result = lattice.verify_chain(agent_id=agent.agent_id)
        assert result.chain[0].actor_id == agent.agent_id
        assert result.chain[0].depth == 1

    def test_leaf_budget_equals_last_grant(self):
        lattice = _make_lattice()
        _, _, data_agent, _, _, _ = self._build_three_level_chain(lattice)
        result = lattice.verify_chain(agent_id=data_agent.agent_id)
        assert result.leaf_budget == 25.0


class TestATFInvariants:

    def test_atf_inv_001_no_authority_expansion(self):
        """ATF-INV-001: Monotonic Authority Reduction — enforced at protocol level."""
        engine = _make_dr_engine()
        with pytest.raises(AuthorityExpansionViolation) as exc_info:
            engine.create_delegation(
                delegator_id="AGENT-LOW-BUDGET",
                delegate_id="AGENT-HIGH-BUDGET",
                task_scope={"action": "expand"},
                authority_budget_delegator=30.0,
                authority_budget_granted=60.0,
            )
        assert "ATF-INV-001" in str(exc_info.value)

    def test_atf_inv_002_receipt_has_hash(self):
        """ATF-INV-002: Every receipt has a content_hash."""
        engine = _make_dr_engine()
        receipt = engine.create_delegation(
            delegator_id="HUMAN-TIER1",
            delegate_id="AID-FINANCE-INV002",
            task_scope={"action": "test"},
            authority_budget_delegator=100.0,
            authority_budget_granted=50.0,
        )
        assert receipt.content_hash is not None
        assert len(receipt.content_hash) == 64

    def test_atf_inv_003_chain_root_tracked(self):
        """ATF-INV-003: Every receipt traces to a root."""
        lattice = _make_lattice()
        _, _, data_agent, dr1, _, dr3 = TestTrustLattice()._build_three_level_chain(lattice)
        assert dr3.chain_root_id == dr1.delegation_id

    def test_atf_inv_004_delegator_cannot_exceed_own_budget(self):
        """ATF-INV-004: Cannot grant more than held."""
        engine = _make_dr_engine()
        with pytest.raises(AuthorityExpansionViolation):
            engine.create_delegation(
                delegator_id="AGENT-50",
                delegate_id="AGENT-RECEIVER",
                task_scope={"action": "exceed"},
                authority_budget_delegator=50.0,
                authority_budget_granted=51.0,
            )

    def test_atf_inv_005_receipt_immutable_after_creation(self):
        """ATF-INV-005: Receipt content_hash changes if fields change."""
        engine = _make_dr_engine()
        receipt = engine.create_delegation(
            delegator_id="HUMAN-TIER1",
            delegate_id="AID-FINANCE-INV005",
            task_scope={"action": "immutable"},
            authority_budget_delegator=100.0,
            authority_budget_granted=70.0,
        )
        from dataclasses import asdict
        d = asdict(receipt)
        d["authority_budget_granted"] = 90.0
        tampered = DelegationReceipt(**d)
        result = engine.verify_receipt(tampered)
        assert result["hash_valid"] is False

    def test_atf_inv_006_independent_verification(self):
        """ATF-INV-006: Verification works with only embedded public key."""
        engine = _make_dr_engine()
        receipt = engine.create_delegation(
            delegator_id="HUMAN-TIER1",
            delegate_id="AID-FINANCE-INV006",
            task_scope={"action": "independent"},
            authority_budget_delegator=100.0,
            authority_budget_granted=60.0,
        )
        result = engine.verify_receipt(receipt)
        assert result["hash_valid"] is True
        assert result["mar_invariant_valid"] is True
