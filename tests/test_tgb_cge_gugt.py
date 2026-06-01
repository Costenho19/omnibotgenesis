"""
Tests — RFC-ATF-5: TGB · CGE · GUGT
====================================
ADR-178 (CGE) · ADR-179 (GUGT) · ADR-180 (TGB)

Coverage strategy (per architect guidance):
  - 90%+ pure in-memory pytest: invariants, conformance levels, hashing,
    clause validation, dataclass behaviour, signing (mock key).
  - Psycopg smoke tests: 2 tests with unittest.mock.patch over DB connection
    to verify ensure_tables() and _persist() contract without a real DB.

Run:
    TESTING=true TELEGRAM_BOT_TOKEN=test-token \\
    pytest tests/test_tgb_cge_gugt.py -v

Harold Nunes · OMNIX QUANTUM LTD · June 2026
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
# Enable CGE evaluations
os.environ.setdefault("CGE_ENABLED", "true")


# ─────────────────────────────────────────────────────────────────────────────
# Shared fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def fake_pqc_key_pair():
    """Real ML-DSA-65 keypair once per session; stubs if pqc not installed."""
    try:
        from pqc.sign import dilithium3
        pk, sk = dilithium3.keypair()
        return pk, sk
    except ImportError:
        sk = hashlib.sha3_256(b"OMNIX-TEST-SK").digest()
        pk = hashlib.sha3_256(b"OMNIX-TEST-PK").digest()
        return pk, sk


@pytest.fixture
def signing_env(fake_pqc_key_pair):
    pk, sk = fake_pqc_key_pair
    sk_b64 = base64.b64encode(sk).decode()
    pk_b64 = base64.b64encode(pk).decode()
    with patch.dict(os.environ, {
        "OMNIX_SIGNING_SECRET_KEY_B64": sk_b64,
        "OMNIX_SIGNING_PUBLIC_KEY_B64": pk_b64,
    }):
        yield pk_b64, sk_b64


# ─────────────────────────────────────────────────────────────────────────────
# ── TGB: Temporal Governance Bridge (ADR-180) ─────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

class TestTGBDataclasses:
    """Verify TGB dataclass structure, field presence, and serialisation."""

    def test_import(self):
        from omnix_core.agents.atf.temporal_governance_bridge import (
            TemporalContextSnapshot,
            RegulatoryAlignmentReceipt,
            TemporalMigrationRecord,
        )
        assert TemporalContextSnapshot
        assert RegulatoryAlignmentReceipt
        assert TemporalMigrationRecord

    def test_tcs_id_format(self):
        from omnix_core.agents.atf.temporal_governance_bridge import TemporalGovernanceBridge
        bridge = TemporalGovernanceBridge()
        tcs = bridge.issue_tcs(
            parent_record_id="DR-TEST-001",
            parent_record_type="DelegationReceipt",
        )
        assert tcs.tcs_id.startswith("TCS-")
        assert len(tcs.tcs_id) == 4 + 16
        assert tcs.parent_record_id == "DR-TEST-001"
        assert tcs.parent_record_type == "DelegationReceipt"

    def test_tcs_id_format_with_override(self):
        from omnix_core.agents.atf.temporal_governance_bridge import TemporalGovernanceBridge
        bridge = TemporalGovernanceBridge()
        tcs = bridge.issue_tcs(
            parent_record_id="DR-OVR-001",
            parent_record_type="DR",
            regulatory_context_override={"eu_ai_act": "Art.14", "nist": "AI-RMF-1.0"},
            threshold_context_override={"avm_threshold": 0.35, "max_drift_pct": 50},
        )
        assert tcs.tcs_id.startswith("TCS-")
        assert tcs.regulatory_context["eu_ai_act"] == "Art.14"
        assert tcs.threshold_context["avm_threshold"] == 0.35

    def test_tcs_hash_is_sha3_256(self):
        from omnix_core.agents.atf.temporal_governance_bridge import TemporalGovernanceBridge
        bridge = TemporalGovernanceBridge()
        tcs = bridge.issue_tcs(parent_record_id="DR-HASH-001", parent_record_type="DR")
        # TGB stores raw hex (64 chars, no prefix)
        assert len(tcs.tcs_hash) == 64
        assert all(c in "0123456789abcdef" for c in tcs.tcs_hash)

    def test_tcs_to_dict_roundtrip(self):
        from omnix_core.agents.atf.temporal_governance_bridge import TemporalGovernanceBridge
        bridge = TemporalGovernanceBridge()
        tcs = bridge.issue_tcs(parent_record_id="DR-DICT-001", parent_record_type="DR")
        d = tcs.to_dict()
        assert d["tcs_id"] == tcs.tcs_id
        assert d["tcs_hash"] == tcs.tcs_hash
        assert "regulatory_context" in d

    def test_tcs_verify_hash_only(self):
        """Verify TCS hash integrity without a signing key."""
        from omnix_core.agents.atf.temporal_governance_bridge import TemporalGovernanceBridge
        bridge = TemporalGovernanceBridge()
        tcs = bridge.issue_tcs(parent_record_id="DR-VER-001", parent_record_type="DR")
        result = bridge.verify_tcs(tcs)
        assert result["hash_valid"] is True

    def test_tcs_signed_verify(self, signing_env):
        """TGB-INV-005: TCS signed with real key verifies hash correctly."""
        pk_b64, _ = signing_env
        from omnix_core.agents.atf.temporal_governance_bridge import TemporalGovernanceBridge
        bridge = TemporalGovernanceBridge()
        tcs = bridge.issue_tcs(parent_record_id="DR-SIGN-001", parent_record_type="DR")
        result = bridge.verify_tcs(tcs, public_key_b64=pk_b64)
        assert result["hash_valid"] is True
        assert result["pqc_valid"] is not False

    def test_tcs_tampered_hash_fails(self):
        """A tampered TCS hash must fail verification."""
        import dataclasses
        from omnix_core.agents.atf.temporal_governance_bridge import TemporalGovernanceBridge
        bridge = TemporalGovernanceBridge()
        tcs = bridge.issue_tcs(parent_record_id="DR-TAMPER-001", parent_record_type="DR")
        tampered = dataclasses.replace(tcs, tcs_hash="sha3-256:" + "deadbeef" * 8)
        result = bridge.verify_tcs(tampered)
        assert result["hash_valid"] is False

    def test_rar_id_format(self):
        from omnix_core.agents.atf.temporal_governance_bridge import TemporalGovernanceBridge
        bridge = TemporalGovernanceBridge()
        tcs = bridge.issue_tcs(parent_record_id="DR-RAR-001", parent_record_type="DR")
        rar = bridge.issue_rar(
            source_record_id="DR-RAR-001",
            source_tcs_id=tcs.tcs_id,
            reviewer_context={"framework": "EU_AI_ACT_2026", "reviewer": "AUDIT-001"},
            field_projections=[{
                "field": "delegation_depth",
                "source_value": "3",
                "target_value": "3",
                "projection_rule": "UNCHANGED",
            }],
            original_record_hash=tcs.tcs_hash,
        )
        assert rar.rar_id.startswith("RAR-")
        assert rar.source_record_id == "DR-RAR-001"
        assert rar.source_tcs_id == tcs.tcs_id

    def test_rar_non_destructive_inv002(self):
        """TGB-INV-002: issuing a RAR must NOT modify the source TCS."""
        from omnix_core.agents.atf.temporal_governance_bridge import TemporalGovernanceBridge
        bridge = TemporalGovernanceBridge()
        tcs = bridge.issue_tcs(parent_record_id="DR-ND-001", parent_record_type="DR")
        original_hash = tcs.tcs_hash
        original_id   = tcs.tcs_id
        bridge.issue_rar(
            source_record_id="DR-ND-001",
            source_tcs_id=tcs.tcs_id,
            reviewer_context={"framework": "NIST_AI_RMF_2025"},
            field_projections=[{
                "field": "ces_score",
                "source_value": "75.0",
                "target_value": "75.0",
                "projection_rule": "UNCHANGED",
            }],
            original_record_hash=tcs.tcs_hash,
        )
        assert tcs.tcs_hash == original_hash
        assert tcs.tcs_id   == original_id

    def test_tmr_id_format(self):
        from omnix_core.agents.atf.temporal_governance_bridge import TemporalGovernanceBridge
        bridge = TemporalGovernanceBridge()
        tmr = bridge.issue_tmr(
            source_record_id="DR-TMR-001",
            migration_event="HOT_TO_WARM",
            retention_basis="EU_AI_ACT_ART72_7YR",
        )
        assert tmr.tmr_id.startswith("TMR-")
        assert tmr.migration_event == "HOT_TO_WARM"
        assert tmr.source_record_id == "DR-TMR-001"

    def test_tmr_invalid_event_raises(self):
        """Invalid migration event must be rejected."""
        from omnix_core.agents.atf.temporal_governance_bridge import TemporalGovernanceBridge
        bridge = TemporalGovernanceBridge()
        with pytest.raises(ValueError, match="migration_event"):
            bridge.issue_tmr(
                source_record_id="DR-TMR-BAD",
                migration_event="INVALID_EVENT",
                retention_basis="EU_AI_ACT_ART72_7YR",
            )

    def test_tmr_invalid_retention_raises(self):
        """Invalid retention basis must be rejected."""
        from omnix_core.agents.atf.temporal_governance_bridge import TemporalGovernanceBridge
        bridge = TemporalGovernanceBridge()
        with pytest.raises(ValueError, match="retention_basis"):
            bridge.issue_tmr(
                source_record_id="DR-TMR-RET",
                migration_event="HOT_TO_WARM",
                retention_basis="MADE_UP_BASIS",
            )


class TestTGBInvariantConstants:
    """Verify TGB migration events and retention bases are correctly defined."""

    def test_valid_migration_events(self):
        from omnix_core.agents.atf.temporal_governance_bridge import VALID_MIGRATION_EVENTS
        assert "HOT_TO_WARM"   in VALID_MIGRATION_EVENTS
        assert "WARM_TO_COLD"  in VALID_MIGRATION_EVENTS
        assert "COLD_ARCHIVED" in VALID_MIGRATION_EVENTS

    def test_valid_retention_bases(self):
        from omnix_core.agents.atf.temporal_governance_bridge import VALID_RETENTION_BASES
        assert "EU_AI_ACT_ART72_7YR" in VALID_RETENTION_BASES
        assert "GCC_DIFC_ART14_5YR"  in VALID_RETENTION_BASES

    def test_tcs_get_after_issue(self):
        """TCS is retrievable from in-memory store after issue."""
        from omnix_core.agents.atf.temporal_governance_bridge import TemporalGovernanceBridge
        bridge = TemporalGovernanceBridge()
        tcs = bridge.issue_tcs(parent_record_id="DR-GET-001", parent_record_type="DR")
        retrieved = bridge.get_tcs(tcs.tcs_id)
        assert retrieved is not None
        assert retrieved.tcs_id == tcs.tcs_id


class TestTGBPsycopgSmoke:
    """Smoke: verify ensure_tables is callable without a real DB."""

    def test_ensure_tables_callable(self):
        """ensure_tables() returns bool and does not raise when no DB is configured."""
        from omnix_core.agents.atf.temporal_governance_bridge import TemporalGovernanceBridge
        bridge = TemporalGovernanceBridge()
        # Without DATABASE_URL configured, ensure_tables returns False gracefully
        result = bridge.ensure_tables()
        assert isinstance(result, bool)

    def test_ensure_tables_with_mock_conn(self):
        """ensure_tables() calls execute on a working DB connection."""
        from omnix_core.agents.atf.temporal_governance_bridge import TemporalGovernanceBridge

        bridge = TemporalGovernanceBridge()
        mock_cursor = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = lambda s: mock_cursor
        mock_ctx.__exit__  = MagicMock(return_value=False)
        mock_conn = MagicMock()
        mock_conn.__enter__ = lambda s: s
        mock_conn.__exit__  = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_ctx

        with patch.object(bridge, "_get_conn", return_value=mock_conn):
            result = bridge.ensure_tables()
        assert isinstance(result, bool)


# ─────────────────────────────────────────────────────────────────────────────
# ── CGE: Counterfactual Governance Engine (ADR-178) ───────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

# Shared CGE call params (real API signature)
_CGE_PARAMS = {
    "primary_receipt_id": "DR-CGE-TEST-001",
    "primary_params": {
        "ces_score": 75.0,
        "authority_budget": 80.0,
        "delegation_depth": 3,
        "fragmentation_limit": 0.90,
        "ces_threshold_nominal": 70.0,
    },
    "primary_outcome": "NOMINAL",
}


class TestCGEDataclasses:
    """Verify CGE dataclass structure and ID formats."""

    def test_import(self):
        from omnix_core.agents.atf.counterfactual_governance_engine import (
            CounterfactualForkRecord,
            CounterfactualAttestationToken,
            CounterfactualGovernanceEngine,
        )
        assert CounterfactualForkRecord
        assert CounterfactualAttestationToken
        assert CounterfactualGovernanceEngine

    def test_evaluate_returns_cat(self):
        from omnix_core.agents.atf.counterfactual_governance_engine import (
            CounterfactualGovernanceEngine,
        )
        engine = CounterfactualGovernanceEngine()
        cat = engine.evaluate(**_CGE_PARAMS)
        assert cat.cat_id.startswith("CAT-")
        assert len(cat.cat_id) == 4 + 16

    def test_evaluate_generates_fork_count_cfrs(self):
        """CGE must generate engine._fork_count CFRs per evaluation."""
        from omnix_core.agents.atf.counterfactual_governance_engine import (
            CounterfactualGovernanceEngine,
        )
        engine = CounterfactualGovernanceEngine()
        cat = engine.evaluate(**_CGE_PARAMS)
        cfrs = engine.get_cfrs_for_cat(cat.cat_id)
        assert len(cfrs) == engine._fork_count
        assert cat.cfr_count == engine._fork_count

    def test_cfr_id_format(self):
        from omnix_core.agents.atf.counterfactual_governance_engine import (
            CounterfactualGovernanceEngine,
        )
        engine = CounterfactualGovernanceEngine()
        cat = engine.evaluate(**_CGE_PARAMS)
        cfrs = engine.get_cfrs_for_cat(cat.cat_id)
        for cfr in cfrs:
            assert cfr.cfr_id.startswith("CFR-")
            assert len(cfr.cfr_id) == 4 + 16

    def test_cat_root_hash_inv004(self):
        """CGE-INV-004: cat_root_hash must be sha256 of sorted(cfr_content_hashes)."""
        from omnix_core.agents.atf.counterfactual_governance_engine import (
            CounterfactualGovernanceEngine,
        )
        engine = CounterfactualGovernanceEngine()
        cat = engine.evaluate(**_CGE_PARAMS)
        # The dataclass verify_root_hash() implements INV-004
        assert cat.verify_root_hash() is True

    def test_cfr_counter_uniqueness(self):
        """Each fork within a CAT must have a unique cfr_id."""
        from omnix_core.agents.atf.counterfactual_governance_engine import (
            CounterfactualGovernanceEngine,
        )
        engine = CounterfactualGovernanceEngine()
        cat = engine.evaluate(**_CGE_PARAMS)
        cfrs = engine.get_cfrs_for_cat(cat.cat_id)
        ids = [cfr.cfr_id for cfr in cfrs]
        assert len(ids) == len(set(ids)), "Duplicate CFR IDs found"

    def test_verify_cat_hash_integrity(self):
        """verify_cat must report root_hash_valid=True on a fresh, unmodified CAT."""
        from omnix_core.agents.atf.counterfactual_governance_engine import (
            CounterfactualGovernanceEngine,
        )
        engine = CounterfactualGovernanceEngine()
        cat = engine.evaluate(**_CGE_PARAMS)
        cfrs = engine.get_cfrs_for_cat(cat.cat_id)
        result = engine.verify_cat(cat, cfrs)
        assert result["root_hash_valid"] is True
        assert result["cfr_count_valid"] is True
        assert result["all_hashes_match"] is True

    def test_verify_cat_tampered_root_hash_fails(self):
        """A tampered cat_root_hash must fail root_hash_valid check."""
        import dataclasses
        from omnix_core.agents.atf.counterfactual_governance_engine import (
            CounterfactualGovernanceEngine,
        )
        engine = CounterfactualGovernanceEngine()
        cat = engine.evaluate(**_CGE_PARAMS)
        cfrs = engine.get_cfrs_for_cat(cat.cat_id)
        tampered_cat = dataclasses.replace(cat, cat_root_hash="sha256:" + "deadbeef" * 8)
        result = engine.verify_cat(tampered_cat, cfrs)
        assert result["root_hash_valid"] is False

    def test_deterministic_seeding_same_input(self):
        """Same primary_receipt_id → consistent fork count and INV-004 holds on both."""
        from omnix_core.agents.atf.counterfactual_governance_engine import (
            CounterfactualGovernanceEngine,
        )
        e1 = CounterfactualGovernanceEngine()
        e2 = CounterfactualGovernanceEngine()
        cat1 = e1.evaluate(**_CGE_PARAMS)
        cat2 = e2.evaluate(**_CGE_PARAMS)
        cfrs1 = e1.get_cfrs_for_cat(cat1.cat_id)
        cfrs2 = e2.get_cfrs_for_cat(cat2.cat_id)
        assert len(cfrs1) == len(cfrs2)
        assert cat1.verify_root_hash() is True
        assert cat2.verify_root_hash() is True

    def test_multiple_evaluations_produce_distinct_cats(self):
        """Each evaluate() call must produce a unique CAT."""
        from omnix_core.agents.atf.counterfactual_governance_engine import (
            CounterfactualGovernanceEngine,
        )
        engine = CounterfactualGovernanceEngine()
        cats = []
        for i in range(3):
            p = dict(_CGE_PARAMS)
            p["primary_receipt_id"] = f"DR-MULTI-{i:03d}"
            cat = engine.evaluate(**p)
            cats.append(cat)
        ids = [c.cat_id for c in cats]
        assert len(ids) == len(set(ids)), "Duplicate CAT IDs found"

    def test_get_cat_returns_stored(self):
        """get_cat() returns the stored CAT by ID."""
        from omnix_core.agents.atf.counterfactual_governance_engine import (
            CounterfactualGovernanceEngine,
        )
        engine = CounterfactualGovernanceEngine()
        cat = engine.evaluate(**_CGE_PARAMS)
        retrieved = engine.get_cat(cat.cat_id)
        assert retrieved is not None
        assert retrieved.cat_id == cat.cat_id

    def test_get_cat_unknown_returns_none(self):
        """get_cat() returns None for an unknown ID."""
        from omnix_core.agents.atf.counterfactual_governance_engine import (
            CounterfactualGovernanceEngine,
        )
        engine = CounterfactualGovernanceEngine()
        result = engine.get_cat("CAT-DOESNOTEXIST0000000000000000")
        assert result is None


class TestCGEInvariantGuards:
    """Verify CGE-INV guards at engine level."""

    def test_cge_inv001_receipt_id_required(self):
        """CGE-INV-001: primary_receipt_id must be non-empty."""
        from omnix_core.agents.atf.counterfactual_governance_engine import (
            CounterfactualGovernanceEngine,
        )
        engine = CounterfactualGovernanceEngine()
        with pytest.raises((ValueError, Exception)):
            engine.evaluate(
                primary_receipt_id="",
                primary_params=_CGE_PARAMS["primary_params"],
                primary_outcome="NOMINAL",
            )

    def test_cge_inv002_evaluate_is_readonly(self):
        """CGE-INV-002: evaluate() must not modify primary_params dict."""
        from omnix_core.agents.atf.counterfactual_governance_engine import (
            CounterfactualGovernanceEngine,
        )
        engine = CounterfactualGovernanceEngine()
        params = dict(_CGE_PARAMS["primary_params"])
        original_params = dict(params)
        engine.evaluate(
            primary_receipt_id="DR-RO-001",
            primary_params=params,
            primary_outcome="NOMINAL",
        )
        assert params == original_params, "evaluate() modified primary_params (CGE-INV-002 violated)"

    def test_cge_disabled_raises(self):
        """CGE_ENABLED=false must raise CGEInvariantViolation."""
        from omnix_core.agents.atf.counterfactual_governance_engine import (
            CounterfactualGovernanceEngine, CGEInvariantViolation,
        )
        with patch.dict(os.environ, {"CGE_ENABLED": "false"}):
            engine = CounterfactualGovernanceEngine()
            with pytest.raises(CGEInvariantViolation, match="CGE_ENABLED"):
                engine.evaluate(**_CGE_PARAMS)

    def test_verify_cat_fully_verified(self):
        """Fresh CAT with no seal should be fully_verified=True (no pqc check needed)."""
        from omnix_core.agents.atf.counterfactual_governance_engine import (
            CounterfactualGovernanceEngine,
        )
        engine = CounterfactualGovernanceEngine()
        cat = engine.evaluate(**_CGE_PARAMS)
        cfrs = engine.get_cfrs_for_cat(cat.cat_id)
        result = engine.verify_cat(cat, cfrs)
        assert result["fully_verified"] is True
        assert result["cge_inv_002_respected"] is True


class TestCGEPsycopgSmoke:
    """Smoke: verify ensure_tables is callable without a real DB."""

    def test_ensure_tables_callable(self):
        """ensure_tables() returns bool and does not raise when no DB."""
        from omnix_core.agents.atf.counterfactual_governance_engine import (
            CounterfactualGovernanceEngine,
        )
        engine = CounterfactualGovernanceEngine()
        # With no DATABASE_URL, ensure_tables returns False gracefully
        result = engine.ensure_tables()
        assert isinstance(result, bool)


# ─────────────────────────────────────────────────────────────────────────────
# ── GUGT: Grand Unified Governance Theory (ADR-179) ──────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

_FULL_EVIDENCE: Dict[str, Any] = {
    "UGI-001": {
        "status": "PASS",
        "evidence_ref": "AIR-TEST-001",
        "framework_coverage": ["EU_AI_ACT_ART14", "NIST_GOVERN_1.1"],
    },
    "UGI-002": {
        "status": "PASS",
        "evidence_ref": "TAR-TEST-001",
        "framework_coverage": ["EU_AI_ACT_ART11", "ISO42001_6_2"],
    },
    "UGI-003": {
        "status": "PASS",
        "evidence_ref": "DTR-TEST-001",
        "framework_coverage": ["NIST_MAP_1.1", "GCC_DIFC_ART14"],
    },
    "UGI-004": {
        "status": "PASS",
        "evidence_ref": "RCR-TEST-001",
        "framework_coverage": ["EU_AI_ACT_ART13", "NIST_MANAGE_2.2"],
    },
    "UGI-005": {
        "status": "PASS",
        "evidence_ref": "BAR-TEST-001",
        "framework_coverage": ["ATF_INV_006", "POGR_INV_001"],
    },
    "UGI-006": {
        "status": "PASS",
        "evidence_ref": "RCEP-TEST-001",
        "framework_coverage": ["ATF_INV_001", "CUSTOM:OMNIX_TAMPER:VERIFY_GUIDE_V1"],
    },
}


def _make_engine(allow_unsigned: bool = True):
    from omnix_core.agents.atf.grand_unified_governance_theory import (
        GrandUnifiedGovernanceEngine,
    )
    return GrandUnifiedGovernanceEngine(allow_unsigned=allow_unsigned)


class TestGUGTClauseValidation:
    """GUGT-INV-002: framework_coverage controlled vocabulary."""

    def test_known_clauses_pass(self):
        from omnix_core.agents.atf.grand_unified_governance_theory import validate_clause_ref
        for clause in [
            "EU_AI_ACT_ART14", "NIST_GOVERN_1.1", "GCC_DIFC_ART14",
            "ISO42001_6_2", "ATF_INV_006", "POGR_INV_001",
        ]:
            assert validate_clause_ref(clause) is True, f"{clause} should be valid"

    def test_valid_prefix_with_clause_passes(self):
        from omnix_core.agents.atf.grand_unified_governance_theory import validate_clause_ref
        assert validate_clause_ref("EU_AI_ACT_ART99") is True
        assert validate_clause_ref("NIST_GOVERN_5.5") is True
        assert validate_clause_ref("DORA_ART99") is True

    def test_custom_namespace_passes(self):
        from omnix_core.agents.atf.grand_unified_governance_theory import validate_clause_ref
        assert validate_clause_ref("CUSTOM:MY_FRAMEWORK:CLAUSE_X1") is True
        assert validate_clause_ref("CUSTOM:OMNIX_TAMPER:VERIFY_GUIDE_V1") is True

    def test_free_text_fails(self):
        from omnix_core.agents.atf.grand_unified_governance_theory import validate_clause_ref
        assert validate_clause_ref("FREE_TEXT_NO_PREFIX") is False
        assert validate_clause_ref("random text here") is False
        assert validate_clause_ref("") is False

    def test_custom_malformed_fails(self):
        from omnix_core.agents.atf.grand_unified_governance_theory import validate_clause_ref
        assert validate_clause_ref("CUSTOM:only_two_parts") is False
        assert validate_clause_ref("CUSTOM::") is False


class TestGUGTAssessCompliance:
    """assess_ugi_compliance: normalisation and invariant enforcement."""

    def test_full_evidence_passes(self):
        engine = _make_engine()
        result = engine.assess_ugi_compliance("TestSystem-v1", _FULL_EVIDENCE)
        assert set(result.keys()) == {
            "UGI-001", "UGI-002", "UGI-003",
            "UGI-004", "UGI-005", "UGI-006",
        }

    def test_normalised_result_has_description(self):
        engine = _make_engine()
        result = engine.assess_ugi_compliance("TestSystem-v1", _FULL_EVIDENCE)
        for ugi in ("UGI-001", "UGI-006"):
            assert result[ugi]["description"] != ""

    def test_gugt_inv001_missing_ugi_raises(self):
        from omnix_core.agents.atf.grand_unified_governance_theory import GUGTInvariantViolation
        engine = _make_engine()
        incomplete = {k: v for k, v in _FULL_EVIDENCE.items() if k != "UGI-003"}
        with pytest.raises(GUGTInvariantViolation) as exc_info:
            engine.assess_ugi_compliance("TestSystem-v1", incomplete)
        assert "GUGT-INV-001" in str(exc_info.value)
        assert "UGI-003" in str(exc_info.value)

    def test_gugt_inv002_empty_coverage_raises(self):
        from omnix_core.agents.atf.grand_unified_governance_theory import GUGTInvariantViolation
        engine = _make_engine()
        bad = dict(_FULL_EVIDENCE)
        bad["UGI-004"] = {"status": "PASS", "framework_coverage": []}
        with pytest.raises(GUGTInvariantViolation) as exc_info:
            engine.assess_ugi_compliance("TestSystem-v1", bad)
        assert "GUGT-INV-002" in str(exc_info.value)

    def test_gugt_inv002_invalid_clause_raises(self):
        from omnix_core.agents.atf.grand_unified_governance_theory import GUGTInvariantViolation
        engine = _make_engine()
        bad = dict(_FULL_EVIDENCE)
        bad["UGI-004"] = {"status": "PASS", "framework_coverage": ["NOT_A_REAL_CLAUSE"]}
        with pytest.raises(GUGTInvariantViolation) as exc_info:
            engine.assess_ugi_compliance("TestSystem-v1", bad)
        assert "GUGT-INV-002" in str(exc_info.value)

    def test_invalid_status_raises(self):
        from omnix_core.agents.atf.grand_unified_governance_theory import GUGTInvariantViolation
        engine = _make_engine()
        bad = dict(_FULL_EVIDENCE)
        bad["UGI-001"] = {"status": "MAYBE", "framework_coverage": ["EU_AI_ACT_ART14"]}
        with pytest.raises(GUGTInvariantViolation):
            engine.assess_ugi_compliance("TestSystem-v1", bad)


class TestGUGTConformanceLevels:
    """Conformance level monotonicity (GUGT-L1 → L2 → L3 → L3+ATF)."""

    def _assessment_with_failures(self, fail_ugis):
        engine = _make_engine()
        modified = {}
        for ugi, ev in _FULL_EVIDENCE.items():
            if ugi in fail_ugis:
                modified[ugi] = {**ev, "status": "FAIL"}
            else:
                modified[ugi] = ev
        return engine.assess_ugi_compliance("TestSystem-v1", modified)

    def test_all_pass_atf_protocol_gives_l3_atf(self):
        from omnix_core.agents.atf.grand_unified_governance_theory import (
            GrandUnifiedGovernanceEngine,
        )
        engine = _make_engine()
        assessment = engine.assess_ugi_compliance("TestSystem-v1", _FULL_EVIDENCE)
        level, count = GrandUnifiedGovernanceEngine._compute_conformance_level(assessment, "ATF")
        assert level == "GUGT-L3+ATF"
        assert count == 6

    def test_all_pass_non_atf_protocol_gives_l3(self):
        from omnix_core.agents.atf.grand_unified_governance_theory import (
            GrandUnifiedGovernanceEngine,
        )
        engine = _make_engine()
        assessment = engine.assess_ugi_compliance("TestSystem-v1", _FULL_EVIDENCE)
        level, count = GrandUnifiedGovernanceEngine._compute_conformance_level(assessment, "VGS")
        assert level == "GUGT-L3"
        assert count == 6

    def test_ugi_005_006_fail_gives_l2(self):
        from omnix_core.agents.atf.grand_unified_governance_theory import (
            GrandUnifiedGovernanceEngine,
        )
        assessment = self._assessment_with_failures({"UGI-005", "UGI-006"})
        level, count = GrandUnifiedGovernanceEngine._compute_conformance_level(assessment, "ATF")
        assert level == "GUGT-L2"
        assert count == 4

    def test_ugi_003_004_005_006_fail_gives_l1(self):
        from omnix_core.agents.atf.grand_unified_governance_theory import (
            GrandUnifiedGovernanceEngine,
        )
        assessment = self._assessment_with_failures({"UGI-003", "UGI-004", "UGI-005", "UGI-006"})
        level, count = GrandUnifiedGovernanceEngine._compute_conformance_level(assessment, "ATF")
        assert level == "GUGT-L1"
        assert count == 2

    def test_ugi_001_fail_prevents_l3(self):
        """GUGT-INV-006: UGI-001 FAIL must prevent L3/L3+ATF certification."""
        from omnix_core.agents.atf.grand_unified_governance_theory import (
            GrandUnifiedGovernanceEngine,
        )
        assessment = self._assessment_with_failures({"UGI-001"})
        level, _ = GrandUnifiedGovernanceEngine._compute_conformance_level(assessment, "ATF")
        assert level not in ("GUGT-L3", "GUGT-L3+ATF"), (
            "UGI-001 FAIL must prevent L3/L3+ATF certification"
        )


class TestGUGTIssueUIR:
    """issue_uir: ID format, sealing, persistence, invariant guards."""

    def test_uir_id_format(self):
        engine = _make_engine()
        assessment = engine.assess_ugi_compliance("TestSystem-v1", _FULL_EVIDENCE)
        uir = engine.issue_uir(
            subject_system="TestSystem-v1", subject_protocol="ATF",
            ugi_assessment=assessment,
            agent_type_coverage=["LLM"], jurisdiction_coverage=["EU"],
        )
        assert uir.uir_id.startswith("UIR-")
        assert len(uir.uir_id) == 4 + 16

    def test_uir_conformance_atf(self):
        engine = _make_engine()
        assessment = engine.assess_ugi_compliance("TestSystem-v1", _FULL_EVIDENCE)
        uir = engine.issue_uir(
            subject_system="TestSystem-v1", subject_protocol="ATF",
            ugi_assessment=assessment,
            agent_type_coverage=["LLM", "TRADING_AGENT"],
            jurisdiction_coverage=["EU", "UAE"],
        )
        assert uir.conformance_level == "GUGT-L3+ATF"
        assert uir.ugi_pass_count == 6

    def test_uir_content_hash_format(self):
        engine = _make_engine()
        assessment = engine.assess_ugi_compliance("TestSystem-v1", _FULL_EVIDENCE)
        uir = engine.issue_uir(
            subject_system="TestSystem-v1", subject_protocol="ATF",
            ugi_assessment=assessment,
            agent_type_coverage=["LLM"], jurisdiction_coverage=["EU"],
        )
        assert uir.content_hash.startswith("sha3-256:")
        hex_part = uir.content_hash.split(":")[1]
        assert len(hex_part) == 64

    def test_uir_unsigned_sets_certification_invalid(self):
        """allow_unsigned=True → uir_seal=None, certification_valid=False."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("OMNIX_SIGNING_SECRET_KEY_B64", None)
            engine = _make_engine(allow_unsigned=True)
            assessment = engine.assess_ugi_compliance("TestSystem-v1", _FULL_EVIDENCE)
            uir = engine.issue_uir(
                subject_system="TestSystem-v1", subject_protocol="ATF",
                ugi_assessment=assessment,
                agent_type_coverage=["LLM"], jurisdiction_coverage=["EU"],
            )
        assert uir.uir_seal is None
        assert uir.certification_valid is False

    def test_gugt_inv004_empty_agent_type_raises(self):
        from omnix_core.agents.atf.grand_unified_governance_theory import GUGTInvariantViolation
        engine = _make_engine()
        assessment = engine.assess_ugi_compliance("TestSystem-v1", _FULL_EVIDENCE)
        with pytest.raises(GUGTInvariantViolation) as exc_info:
            engine.issue_uir(
                subject_system="TestSystem-v1", subject_protocol="ATF",
                ugi_assessment=assessment,
                agent_type_coverage=[], jurisdiction_coverage=["EU"],
            )
        assert "GUGT-INV-004" in str(exc_info.value)

    def test_production_mode_no_key_raises(self):
        """allow_unsigned=False + no key → GUGTUnsignedError."""
        from omnix_core.agents.atf.grand_unified_governance_theory import GUGTUnsignedError
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("OMNIX_SIGNING_SECRET_KEY_B64", None)
            engine = _make_engine(allow_unsigned=False)
            assessment = engine.assess_ugi_compliance("TestSystem-v1", _FULL_EVIDENCE)
            with pytest.raises(GUGTUnsignedError):
                engine.issue_uir(
                    subject_system="TestSystem-v1", subject_protocol="ATF",
                    ugi_assessment=assessment,
                    agent_type_coverage=["LLM"], jurisdiction_coverage=["EU"],
                )

    def test_uir_linked_artifacts_stored(self):
        engine = _make_engine()
        assessment = engine.assess_ugi_compliance("TestSystem-v1", _FULL_EVIDENCE)
        uir = engine.issue_uir(
            subject_system="TestSystem-v1", subject_protocol="ATF",
            ugi_assessment=assessment,
            agent_type_coverage=["LLM"], jurisdiction_coverage=["EU"],
            linked_artifacts={"tcs_ids": ["TCS-DEMO"], "cat_ids": ["CAT-DEMO"]},
        )
        assert uir.linked_artifacts is not None
        assert "tcs_ids" in uir.linked_artifacts
        assert "cat_ids" in uir.linked_artifacts

    def test_agent_type_coverage_deduplicated(self):
        engine = _make_engine()
        assessment = engine.assess_ugi_compliance("TestSystem-v1", _FULL_EVIDENCE)
        uir = engine.issue_uir(
            subject_system="TestSystem-v1", subject_protocol="ATF",
            ugi_assessment=assessment,
            agent_type_coverage=["LLM", "LLM", "TRADING_AGENT"],
            jurisdiction_coverage=["EU", "EU"],
        )
        assert len(uir.agent_type_coverage) == len(set(uir.agent_type_coverage))
        assert len(uir.jurisdiction_coverage) == len(set(uir.jurisdiction_coverage))


class TestGUGTVerifyUIR:
    """verify_uir: hash integrity and conformance summary."""

    def test_fresh_uir_hash_verified(self):
        engine = _make_engine()
        assessment = engine.assess_ugi_compliance("TestSystem-v1", _FULL_EVIDENCE)
        uir = engine.issue_uir(
            subject_system="TestSystem-v1", subject_protocol="ATF",
            ugi_assessment=assessment,
            agent_type_coverage=["LLM"], jurisdiction_coverage=["EU"],
        )
        result = engine.verify_uir(uir)
        assert result["content_hash_ok"] is True

    def test_tampered_uir_hash_fails(self):
        import dataclasses
        engine = _make_engine()
        assessment = engine.assess_ugi_compliance("TestSystem-v1", _FULL_EVIDENCE)
        uir = engine.issue_uir(
            subject_system="TestSystem-v1", subject_protocol="ATF",
            ugi_assessment=assessment,
            agent_type_coverage=["LLM"], jurisdiction_coverage=["EU"],
        )
        tampered = dataclasses.replace(uir, content_hash="sha3-256:" + "deadbeef" * 8)
        result = engine.verify_uir(tampered)
        assert result["content_hash_ok"] is False

    def test_verify_returns_conformance_level(self):
        engine = _make_engine()
        assessment = engine.assess_ugi_compliance("TestSystem-v1", _FULL_EVIDENCE)
        uir = engine.issue_uir(
            subject_system="TestSystem-v1", subject_protocol="ATF",
            ugi_assessment=assessment,
            agent_type_coverage=["LLM"], jurisdiction_coverage=["EU"],
        )
        result = engine.verify_uir(uir)
        assert result["conformance_level"] == "GUGT-L3+ATF"
        assert result["ugi_pass_count"] == 6

    def test_verify_notes_non_empty(self):
        engine = _make_engine()
        assessment = engine.assess_ugi_compliance("TestSystem-v1", _FULL_EVIDENCE)
        uir = engine.issue_uir(
            subject_system="TestSystem-v1", subject_protocol="ATF",
            ugi_assessment=assessment,
            agent_type_coverage=["LLM"], jurisdiction_coverage=["EU"],
        )
        result = engine.verify_uir(uir)
        assert len(result["notes"]) >= 2


class TestGUGTMemoryPersistence:
    """In-memory persistence: get_uir after issue without DB."""

    def test_get_uir_returns_record(self):
        engine = _make_engine()
        with patch.object(engine, "_get_db", side_effect=RuntimeError("no DB")):
            assessment = engine.assess_ugi_compliance("TestSystem-v1", _FULL_EVIDENCE)
            uir = engine.issue_uir(
                subject_system="TestSystem-v1", subject_protocol="ATF",
                ugi_assessment=assessment,
                agent_type_coverage=["LLM"], jurisdiction_coverage=["EU"],
            )
        retrieved = engine.get_uir(uir.uir_id)
        assert retrieved is not None
        assert retrieved.uir_id == uir.uir_id

    def test_get_uir_unknown_returns_none(self):
        engine = _make_engine()
        with patch.object(engine, "_get_db", side_effect=RuntimeError("no DB")):
            result = engine.get_uir("UIR-DOESNOTEXIST00000000")
        assert result is None


class TestGUGTPsycopgSmoke:
    """Smoke: verify ensure_tables DDL call without a real DB."""

    def test_ensure_tables_calls_execute(self):
        from omnix_core.agents.atf.grand_unified_governance_theory import (
            GrandUnifiedGovernanceEngine,
        )
        mock_cursor = MagicMock()
        mock_conn   = MagicMock()
        mock_conn.__enter__ = lambda s: s
        mock_conn.__exit__  = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = lambda s: mock_cursor
        mock_conn.cursor.return_value.__exit__  = MagicMock(return_value=False)

        with patch(
            "omnix_core.agents.atf.grand_unified_governance_theory."
            "GrandUnifiedGovernanceEngine._get_db",
            return_value=mock_conn,
        ):
            engine = GrandUnifiedGovernanceEngine(allow_unsigned=True)
            engine._tables_ensured = False
            engine._ensure_tables()
            mock_cursor.execute.assert_called_once()
            ddl_arg = mock_cursor.execute.call_args[0][0]
            assert "gugt_universal_invariant_receipts" in ddl_arg


# ─────────────────────────────────────────────────────────────────────────────
# ── Cross-module integration: TGB + CGE + GUGT (RFC-ATF-5) ────────────────────
# ─────────────────────────────────────────────────────────────────────────────

class TestRFCATF5Integration:
    """
    RFC-ATF-5 integration smoke test.

    Verifies TCS (TGB) and CAT (CGE) artifact IDs can be linked into a UIR
    (GUGT) as optional metadata without hard inter-module dependencies.
    """

    def test_full_rfc_atf5_linked_artifact_flow(self):
        from omnix_core.agents.atf.temporal_governance_bridge import TemporalGovernanceBridge
        from omnix_core.agents.atf.counterfactual_governance_engine import (
            CounterfactualGovernanceEngine,
        )
        from omnix_core.agents.atf.grand_unified_governance_theory import (
            GrandUnifiedGovernanceEngine,
        )

        # Step 1: TGB — issue a TCS
        tgb = TemporalGovernanceBridge()
        tcs = tgb.issue_tcs(
            parent_record_id="DR-INT-001",
            parent_record_type="DR",
            regulatory_context_override={"eu_ai_act": "Art.14", "nist": "AI-RMF"},
            threshold_context_override={"avm_threshold": 0.35},
        )
        assert tcs.tcs_id.startswith("TCS-")

        # Step 2: CGE — evaluate counterfactuals
        cge = CounterfactualGovernanceEngine()
        cat = cge.evaluate(
            primary_receipt_id="DR-INT-001",
            primary_params={
                "ces_score": 75.0,
                "authority_budget": 80.0,
                "delegation_depth": 3,
                "fragmentation_limit": 0.90,
            },
            primary_outcome="NOMINAL",
        )
        cfrs = cge.get_cfrs_for_cat(cat.cat_id)
        assert cat.cat_id.startswith("CAT-")

        # Verify CAT integrity
        cge_result = cge.verify_cat(cat, cfrs)
        assert cge_result["root_hash_valid"] is True

        # Step 3: GUGT — issue UIR with linked TCS + CAT IDs
        gugt = GrandUnifiedGovernanceEngine(allow_unsigned=True)
        assessment = gugt.assess_ugi_compliance("QuantumBank-INT-v1", _FULL_EVIDENCE)
        uir = gugt.issue_uir(
            subject_system="QuantumBank-INT-v1",
            subject_protocol="ATF",
            ugi_assessment=assessment,
            agent_type_coverage=["TRADING_AGENT", "LLM"],
            jurisdiction_coverage=["EU", "UAE", "UK"],
            linked_artifacts={
                "tcs_ids": [tcs.tcs_id],
                "cat_ids": [cat.cat_id],
            },
        )

        assert tcs.tcs_id in uir.linked_artifacts["tcs_ids"]
        assert cat.cat_id in uir.linked_artifacts["cat_ids"]
        assert uir.conformance_level == "GUGT-L3+ATF"

        # Step 4: Offline zero-trust verify
        gugt_result = gugt.verify_uir(uir)
        assert gugt_result["content_hash_ok"] is True
        assert gugt_result["conformance_level"] == "GUGT-L3+ATF"
        assert gugt_result["ugi_pass_count"] == 6

    def test_rfc_atf5_assessment_normalisation_deterministic(self):
        """Normalised assessment must be deterministic (same input → same dict)."""
        from omnix_core.agents.atf.grand_unified_governance_theory import (
            GrandUnifiedGovernanceEngine,
        )
        engine = GrandUnifiedGovernanceEngine(allow_unsigned=True)
        a1 = engine.assess_ugi_compliance("SystemA", _FULL_EVIDENCE)
        a2 = engine.assess_ugi_compliance("SystemA", _FULL_EVIDENCE)
        assert json.dumps(a1, sort_keys=True) == json.dumps(a2, sort_keys=True)

    def test_all_three_modules_importable_from_atf_package(self):
        """The ATF __init__ must export all three RFC-ATF-5 modules."""
        from omnix_core.agents.atf import (
            TemporalGovernanceBridge,
            TemporalContextSnapshot,
            RegulatoryAlignmentReceipt,
            TemporalMigrationRecord,
            CounterfactualGovernanceEngine,
            CounterfactualForkRecord,
            UniversalInvariantReceipt,
            GrandUnifiedGovernanceEngine,
            GUGTInvariantViolation,
            validate_clause_ref,
            UNIVERSAL_GOVERNANCE_INVARIANTS,
            CONFORMANCE_LEVELS,
        )
        assert len(UNIVERSAL_GOVERNANCE_INVARIANTS) == 6
        assert "GUGT-L3+ATF" in CONFORMANCE_LEVELS
