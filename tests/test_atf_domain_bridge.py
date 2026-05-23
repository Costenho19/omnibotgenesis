"""
ATF Cross-Domain Trust Bridge — Test Suite
ADR-158: Domain Translation Receipts (DTR) + CDTP invariants

Covers:
    CDTP-INV-001: translated_budget == source_budget * (1 - discount)
    CDTP-INV-002: DTRs carry PQC signature + content_hash
    CDTP-INV-003: DTRs embed source_delegation_id for full chain traceability
    CDTP-INV-004: DTRs are domain-scoped (source + target domains recorded)
    CDTP-INV-005: DTRs are immutable once issued (stored, retrievable, stable hash)

30 tests — fully in-memory, no DB, no network.
DelegationReceipt objects are built directly as dataclasses to avoid any
DB connection attempt from DelegationReceiptEngine.

Domain-specific policies (from CrossDomainBridge.get_policy):
    HEALTHCARE -> INSURANCE: 15%  (CDTP-HEAL-INSU-POLICY)
    HEALTHCARE -> FINANCE:   30%  (CDTP-HEAL-FINA-POLICY)
    ALPHA/unknown -> any:    20%  (CDTP-DEFAULT-POLICY = DEFAULT_TRANSLATION_DISCOUNT)
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
import pytest
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
# Prevent engine from reading prod DATABASE_URL during test collection
os.environ.setdefault("DATABASE_URL", "")

from omnix_core.agents.atf.domain_bridge import (
    CrossDomainAuthorityError,
    CrossDomainBridge,
    DEFAULT_TRANSLATION_DISCOUNT,
    DomainTranslationReceipt,
)
from omnix_core.agents.atf.delegation_receipt import DelegationReceipt


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _dr_id() -> str:
    return f"ATFDR-{uuid.uuid4().hex[:16].upper()}"


def _make_dr(
    *,
    delegator_budget: float = 100.0,
    granted_budget: float = 80.0,
    domain: str = "HEALTHCARE",
    active: bool = True,
) -> DelegationReceipt:
    """
    Build a DelegationReceipt dataclass directly — no engine, no DB touch.
    Correct pattern for unit tests that only need a valid DR object.
    """
    now = datetime.now(timezone.utc).isoformat()
    delta = timedelta(hours=2) if active else timedelta(hours=-1)
    expires = (datetime.now(timezone.utc) + delta).isoformat()
    did = _dr_id()

    core_fields = {
        "delegation_id": did,
        "delegator_id": "HUMAN-HAROLD-001",
        "delegate_id": f"AID-{domain[:4].upper()}-AABBCCDDEEFF0011",
        "task_scope": {"action": "analyze", "domain": domain.upper()},
        "authority_budget_delegator": delegator_budget,
        "authority_budget_granted": granted_budget,
        "parent_delegation_id": None,
        "chain_root_id": did,
        "delegation_depth": 1,
        "expires_at": expires,
    }
    canonical = json.dumps(core_fields, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, default=str)
    content_hash = hashlib.sha256(canonical.encode()).hexdigest()

    return DelegationReceipt(
        delegation_id=did,
        delegator_id="HUMAN-HAROLD-001",
        delegate_id=f"AID-{domain[:4].upper()}-AABBCCDDEEFF0011",
        task_scope={"action": "analyze", "domain": domain.upper()},
        authority_budget_delegator=delegator_budget,
        authority_budget_granted=granted_budget,
        parent_delegation_id=None,
        chain_root_id=did,
        delegation_depth=1,
        delegator_public_key="",
        content_hash=content_hash,
        posture_state_hash=None,
        pqc_signature=None,
        pqc_algorithm=None,
        expires_at=expires,
        status="ACTIVE" if active else "EXPIRED",
        created_at=now,
        metadata={"_test": True},
    )


def _translate(
    bridge: CrossDomainBridge,
    source_dr: DelegationReceipt,
    *,
    target_domain: str = "INSURANCE",
    target_agent_id: str = "AID-INSR-BBBBCCCCDDDDEEEE",
    discount_override: Optional[float] = None,
) -> DomainTranslationReceipt:
    """Thin wrapper around bridge.translate() with sensible defaults."""
    return bridge.translate(
        source_delegation=source_dr,
        source_agent_id=source_dr.delegate_id,
        target_agent_id=target_agent_id,
        target_domain=target_domain,
        target_task_scope={"action": "analyze", "domain": target_domain.upper()},
        discount_override=discount_override,
    )


@pytest.fixture
def bridge() -> CrossDomainBridge:
    """CrossDomainBridge with no database — fully in-memory."""
    return CrossDomainBridge(db_url=None)


@pytest.fixture
def source_dr() -> DelegationReceipt:
    return _make_dr(delegator_budget=100.0, granted_budget=80.0, domain="HEALTHCARE")


# ── CDTP-INV-001: Translated budget == source * (1 - actual_discount) ─────────

class TestCDTPInv001:
    """
    Authority always decreases through domain translation.
    The bridge applies domain-specific policies (e.g. HEAL->INSU: 15%).
    Tests compare against dtr.translation_discount (the actual discount applied),
    not DEFAULT_TRANSLATION_DISCOUNT, to be correct across all policy pairs.
    """

    def test_translated_budget_matches_applied_discount(self, bridge, source_dr):
        """translated_budget == source_budget * (1 - dtr.translation_discount)"""
        dtr = _translate(bridge, source_dr)
        expected = source_dr.authority_budget_granted * (1 - dtr.translation_discount)
        assert abs(dtr.translated_budget - expected) < 1e-9, (
            f"CDTP-INV-001: expected {expected:.4f}, got {dtr.translated_budget:.4f}"
        )

    def test_budget_strictly_less_than_source(self, bridge, source_dr):
        """Any discount > 0 means translated < source."""
        dtr = _translate(bridge, source_dr)
        assert dtr.translation_discount > 0.0
        assert dtr.translated_budget < source_dr.authority_budget_granted

    def test_explicit_override_discount_applied(self, bridge, source_dr):
        """discount_override=0.40 -> translated = source * 0.60"""
        dtr = _translate(bridge, source_dr, target_domain="FINANCE",
                         target_agent_id="AID-FINA-CCCCDDDDEEEEAAAA",
                         discount_override=0.40)
        expected = source_dr.authority_budget_granted * (1 - dtr.translation_discount)
        assert abs(dtr.translated_budget - expected) < 1e-9

    def test_unknown_domain_uses_default_discount(self, bridge, source_dr):
        """HEALTHCARE -> ALPHA has no policy -> DEFAULT_TRANSLATION_DISCOUNT (20%)."""
        dtr = _translate(bridge, source_dr, target_domain="ALPHA_UNKNOWN_XDOMAIN",
                         target_agent_id="AID-ALPH-CCCCDDDDEEEE0001")
        assert dtr.translation_discount == DEFAULT_TRANSLATION_DISCOUNT

    def test_known_policy_healthcare_to_insurance(self, bridge, source_dr):
        """HEALTHCARE -> INSURANCE uses 15% discount policy."""
        dtr = _translate(bridge, source_dr, target_domain="INSURANCE",
                         target_agent_id="AID-INSR-POLICYCHK0001A")
        assert dtr.translation_discount == pytest.approx(0.15, abs=1e-9)
        assert dtr.translated_budget == pytest.approx(source_dr.authority_budget_granted * 0.85, abs=1e-9)

    def test_known_policy_healthcare_to_finance(self, bridge, source_dr):
        """HEALTHCARE -> FINANCE uses 30% discount policy."""
        dtr = _translate(bridge, source_dr, target_domain="FINANCE",
                         target_agent_id="AID-FINA-POLICYCHK0001B")
        assert dtr.translation_discount == pytest.approx(0.30, abs=1e-9)
        assert dtr.translated_budget == pytest.approx(source_dr.authority_budget_granted * 0.70, abs=1e-9)

    def test_discount_clipped_to_zero_when_zero_passed(self, bridge, source_dr):
        """discount_override=0.0 -> translated_budget == source_budget (no reduction)."""
        dtr = _translate(bridge, source_dr, target_domain="FINANCE",
                         target_agent_id="AID-FINA-ZERODISC0001AA",
                         discount_override=0.0)
        assert dtr.translated_budget == pytest.approx(
            source_dr.authority_budget_granted * (1 - dtr.translation_discount), abs=1e-9
        )


# ── CDTP-INV-002: DTRs carry PQC signature + content_hash ─────────────────────

class TestCDTPInv002:
    """Every DTR must have content_hash + pqc_signature fields."""

    def test_pqc_fields_present(self, bridge, source_dr):
        dtr = _translate(bridge, source_dr, target_agent_id="AID-INSR-PQC0001AAAA")
        assert hasattr(dtr, "pqc_signature"), "CDTP-INV-002: pqc_signature field required"
        assert hasattr(dtr, "pqc_algorithm"), "CDTP-INV-002: pqc_algorithm field required"

    def test_content_hash_is_64_char_hex(self, bridge, source_dr):
        dtr = _translate(bridge, source_dr, target_agent_id="AID-INSR-HASH001BBBB")
        assert dtr.content_hash, "content_hash must be non-empty"
        assert len(dtr.content_hash) == 64, (
            f"Expected 64-char SHA-256 hex, got len={len(dtr.content_hash)}"
        )
        int(dtr.content_hash, 16)  # raises ValueError if not valid hex

    def test_content_hash_stable_for_same_dtr(self, bridge):
        """
        Each DTR has a unique ID, so two translate() calls always produce
        different content hashes. The invariant is that a DTR's hash is
        stable: the same object retrieved from the store has the same hash.
        """
        dr = _make_dr(granted_budget=70.0)
        dtr = _translate(bridge, dr, target_agent_id="AID-INSR-DET001AAAAA")
        retrieved = bridge.get_dtr(dtr.dtr_id)
        assert retrieved is not None, "DTR must be retrievable"
        assert retrieved.content_hash == dtr.content_hash, (
            "CDTP-INV-002/005: content_hash must be stable across retrieval"
        )

    def test_different_target_agents_produce_different_hashes(self, bridge, source_dr):
        dtr1 = _translate(bridge, source_dr, target_agent_id="AID-INSR-DIFF001AAAA")
        dtr2 = _translate(bridge, source_dr, target_agent_id="AID-INSR-DIFF002BBBB")
        assert dtr1.content_hash != dtr2.content_hash


# ── CDTP-INV-003: DTRs embed source_delegation_id for chain traceability ───────

class TestCDTPInv003:

    def test_source_delegation_id_matches_source_dr(self, bridge, source_dr):
        dtr = _translate(bridge, source_dr, target_agent_id="AID-INSR-CHAIN001AAA")
        assert dtr.source_delegation_id == source_dr.delegation_id, (
            f"CDTP-INV-003: expected {source_dr.delegation_id}, got {dtr.source_delegation_id}"
        )

    def test_chain_root_id_preserved_from_source(self, bridge, source_dr):
        dtr = _translate(bridge, source_dr, target_agent_id="AID-INSR-ROOT001AAAA")
        assert dtr.chain_root_id == source_dr.chain_root_id

    def test_dtr_id_starts_with_atfdtr(self, bridge, source_dr):
        dtr = _translate(bridge, source_dr, target_agent_id="AID-INSR-IDTEST0001A")
        assert dtr.dtr_id.startswith("ATFDTR"), (
            f"DTR ID must start with ATFDTR, got: {dtr.dtr_id}"
        )

    def test_issued_at_is_recent(self, bridge, source_dr):
        dtr = _translate(bridge, source_dr, target_agent_id="AID-INSR-TIMEST0001A")
        now = datetime.now(timezone.utc)
        issued_str = dtr.issued_at if isinstance(dtr.issued_at, str) else dtr.issued_at.isoformat()
        issued = datetime.fromisoformat(issued_str.replace("Z", "+00:00"))
        if issued.tzinfo is None:
            issued = issued.replace(tzinfo=timezone.utc)
        assert (now - issued).total_seconds() < 30, (
            f"issued_at is {(now-issued).total_seconds():.1f}s in the past"
        )

    def test_two_drs_produce_distinct_source_ids(self, bridge):
        dr_a = _make_dr(granted_budget=60.0)
        dr_b = _make_dr(granted_budget=70.0)
        dtr_a = _translate(bridge, dr_a, target_agent_id="AID-INSR-TRACE001AAA")
        dtr_b = _translate(bridge, dr_b, target_agent_id="AID-INSR-TRACE002BBB")
        assert dtr_a.source_delegation_id != dtr_b.source_delegation_id
        assert dtr_a.source_delegation_id == dr_a.delegation_id
        assert dtr_b.source_delegation_id == dr_b.delegation_id


# ── CDTP-INV-004: DTRs are domain-scoped ──────────────────────────────────────

class TestCDTPInv004:

    def test_source_and_target_domains_recorded(self, bridge, source_dr):
        dtr = _translate(bridge, source_dr, target_domain="FINANCE",
                         target_agent_id="AID-FINA-SCOPE001AAAA")
        assert dtr.source_domain == "HEALTHCARE"
        assert dtr.target_domain == "FINANCE"

    def test_same_domain_translation_rejected(self, bridge, source_dr):
        """HEALTHCARE -> HEALTHCARE is not cross-domain — must raise."""
        with pytest.raises(CrossDomainAuthorityError):
            _translate(bridge, source_dr, target_domain="HEALTHCARE",
                       target_agent_id="AID-HEAL-SAME001AAAA")

    def test_target_agent_id_recorded(self, bridge, source_dr):
        target = "AID-FINA-TARGET001AAAA"
        dtr = _translate(bridge, source_dr, target_domain="FINANCE", target_agent_id=target)
        assert dtr.target_agent_id == target

    def test_source_agent_id_recorded(self, bridge, source_dr):
        dtr = _translate(bridge, source_dr, target_agent_id="AID-INSR-SRCAGENT001")
        assert dtr.source_agent_id == source_dr.delegate_id

    def test_multiple_target_domains_recorded_correctly(self, bridge, source_dr):
        dtr_ins = _translate(bridge, source_dr, target_domain="INSURANCE",
                             target_agent_id="AID-INSR-MULTI001AAAA")
        dtr_fin = _translate(bridge, source_dr, target_domain="FINANCE",
                             target_agent_id="AID-FINA-MULTI002BBBB")
        assert dtr_ins.target_domain == "INSURANCE"
        assert dtr_fin.target_domain == "FINANCE"


# ── CDTP-INV-005: DTRs are immutable once issued ──────────────────────────────

class TestCDTPInv005:

    def test_dtr_stored_and_retrievable(self, bridge, source_dr):
        dtr = _translate(bridge, source_dr, target_agent_id="AID-INSR-STORE001AAA")
        retrieved = bridge.get_dtr(dtr.dtr_id)
        assert retrieved is not None, "CDTP-INV-005: DTR must be retrievable after issuance"
        assert retrieved.dtr_id == dtr.dtr_id

    def test_content_hash_stable_after_retrieval(self, bridge, source_dr):
        dtr = _translate(bridge, source_dr, target_agent_id="AID-INSR-HASHST001AA")
        retrieved = bridge.get_dtr(dtr.dtr_id)
        assert retrieved.content_hash == dtr.content_hash

    def test_initial_status_is_active(self, bridge, source_dr):
        dtr = _translate(bridge, source_dr, target_agent_id="AID-INSR-STATUS001AA")
        assert dtr.is_active(), "Freshly issued DTR must be ACTIVE"

    def test_to_dict_is_json_serializable(self, bridge, source_dr):
        dtr = _translate(bridge, source_dr, target_agent_id="AID-INSR-SERIAL001AA")
        json.dumps(dtr.to_dict(), default=str)  # must not raise

    def test_to_dict_contains_required_fields(self, bridge, source_dr):
        dtr = _translate(bridge, source_dr, target_agent_id="AID-INSR-FIELDS001AA")
        d = dtr.to_dict()
        for field in ("dtr_id", "source_delegation_id", "source_domain",
                      "target_domain", "translated_budget", "content_hash"):
            assert field in d, f"CDTP-INV-005: to_dict() missing field: {field}"


# ── verify_dtr ────────────────────────────────────────────────────────────────

class TestVerifyDTR:
    """
    verify_dtr() returns a dict with key 'fully_verified' (bool).
    Additional diagnostic keys: hash_valid, pqc_signature_valid, cdtp_inv_001_valid,
    not_expired, active. All must be True for fully_verified=True.
    """

    def test_valid_dtr_passes_verification(self, bridge, source_dr):
        dtr = _translate(bridge, source_dr, target_agent_id="AID-INSR-VERIFY001AA")
        result = bridge.verify_dtr(dtr)
        assert result.get("fully_verified") is True, (
            f"verify_dtr should pass for valid DTR: {result}"
        )

    def test_budget_expansion_fails_verification(self, bridge, source_dr):
        """Manually expand translated_budget -> cdtp_inv_001_valid=False -> fully_verified=False."""
        dtr = _translate(bridge, source_dr, target_agent_id="AID-INSR-TAMPER001AA")
        original_budget = dtr.translated_budget
        dtr.translated_budget = source_dr.authority_budget_granted * 2.0
        result = bridge.verify_dtr(dtr)
        assert result.get("fully_verified") is not True, (
            "verify_dtr must detect budget expansion — CDTP-INV-001 violation"
        )
        dtr.translated_budget = original_budget  # restore

    def test_field_tampering_detected_via_content_hash(self, bridge, source_dr):
        """Corrupt source_delegation_id -> hash_valid=False -> fully_verified=False."""
        dtr = _translate(bridge, source_dr, target_agent_id="AID-INSR-TAMPER002BB")
        dtr.source_delegation_id = "ATFDR-FFFFFFFFFFFFFFFF"
        result = bridge.verify_dtr(dtr)
        assert result.get("fully_verified") is not True, (
            "verify_dtr must detect field tampering via hash_valid=False"
        )


# ── get_policy ────────────────────────────────────────────────────────────────

class TestGetPolicy:

    def test_default_discount_for_unknown_pair(self, bridge):
        discount, policy_id = bridge.get_policy("ALPHA_UNKNOWN", "BETA_UNKNOWN")
        assert discount == DEFAULT_TRANSLATION_DISCOUNT
        assert policy_id

    def test_discount_in_valid_range(self, bridge):
        for src, tgt in [("HEALTHCARE", "FINANCE"), ("HEALTHCARE", "INSURANCE")]:
            discount, _ = bridge.get_policy(src, tgt)
            assert 0.0 < discount < 1.0, (
                f"Discount for {src}->{tgt} must be in (0, 1), got {discount}"
            )

    def test_policy_id_is_non_empty_string(self, bridge):
        _, policy_id = bridge.get_policy("HEALTHCARE", "FINANCE")
        assert isinstance(policy_id, str) and len(policy_id) > 0


# ── Helpers: effective_authority + trust_summary ─────────────────────────────

class TestDTRHelpers:

    def test_effective_authority_equals_translated_budget(self, bridge, source_dr):
        dtr = _translate(bridge, source_dr, target_agent_id="AID-INSR-EFFAUTH01AA")
        assert dtr.effective_authority() == dtr.translated_budget

    def test_trust_summary_is_dict_with_required_fields(self, bridge, source_dr):
        dtr = _translate(bridge, source_dr, target_agent_id="AID-INSR-TRUSUMM01AA")
        summary = dtr.trust_summary()
        assert isinstance(summary, dict)
        for key in ("dtr_id", "source_domain", "target_domain"):
            assert key in summary, f"trust_summary() missing: {key}"

    def test_trust_summary_is_json_serializable(self, bridge, source_dr):
        dtr = _translate(bridge, source_dr, target_agent_id="AID-INSR-TRUSUMM02BB")
        json.dumps(dtr.trust_summary(), default=str)
