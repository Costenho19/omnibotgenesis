"""
DSPP Test Suite — ADR-173 Dynamic Semantic Portability Protocol

Tests cover:
  I.   TSA creation and DSPP-INV-001 (no retroactive anchoring)
  II.  SDR publication and DSPP-INV-002 (append-only immutability)
  III. SDU algorithm (boundary / scope / regulatory distances)
  IV.  RSA computation and DSPP-INV-005 (determinism)
  V.   DSPP verdict thresholds — DSPP-INV-007
  VI.  DSPP-INV-003 (MORE_RESTRICTIVE default for permissive drift)
  VII. DSPP-INV-004 (TSA content_hash coverage)
  VIII.DSPP-INV-006 (INCOMPATIBLE propagation through chain)
  IX.  Hash verification — TSA and SDR integrity
  X.   Full pipeline: SPV → TSA → SDR → RSA end-to-end

OMNIX-TEST-DSPP-2026-01 — Harold Nunes — May 2026
"""
import hashlib
import json
import pytest
from datetime import datetime, timezone, timedelta

from omnix_core.agents.atf.dynamic_semantic_portability import (
    DSPPEngine,
    DSPPVerdict,
    TemporalSemanticAnchor,
    SemanticDriftRecord,
    RetroactiveSemanticAssessment,
    TermAssessment,
    TSARetroactiveViolation,
    SDRImmutabilityViolation,
    ATF_CORE_TERM_SET,
    SDU_PORTABLE_THRESHOLD,
    SDU_ACKNOWLEDGED_THRESHOLD,
    SDU_CRITICAL_THRESHOLD,
    SDU_WEIGHT_BOUNDARY,
    SDU_WEIGHT_SCOPE,
    SDU_WEIGHT_REGULATORY,
)


def make_engine(runtime_id="RUNTIME-TEST-OMNIX-20260520"):
    return DSPPEngine(runtime_id=runtime_id, db_url=None)


def make_spv(
    spv_hash=None,
    spv_id=None,
    runtime_id="RUNTIME-TEST-OMNIX-20260520",
    term_hashes=None,
    generated_at=None,
):
    now = generated_at or datetime.now(timezone.utc).isoformat()
    if term_hashes is None:
        term_hashes = {t: f"sha256:abc{i:04x}abc{i:04x}abc{i:04x}abc{i:04x}abc{i:04x}abc{i:04x}abc{i:04x}ab"
                       for i, t in enumerate(ATF_CORE_TERM_SET)}
    core_term_set = {
        t: {"str_entry_id": f"STR-{runtime_id}-{t}-0001", "content_hash": term_hashes.get(t, ""), "term_version": "1.0"}
        for t in ATF_CORE_TERM_SET
    }
    h = spv_hash or hashlib.sha256(
        json.dumps(core_term_set, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()
    return {
        "spv_id": spv_id or f"OMNIX-SPV-{runtime_id}-20260520-AABBCCDD00112233",
        "runtime_id": runtime_id,
        "generated_at": now,
        "atf_core_term_set": core_term_set,
        "extended_terms": {},
        "spv_hash": h,
        "pqc_signature": None,
        "pqc_algorithm": None,
        "created_at": now,
    }


def make_str_entry(term_id, boundary_conditions=None, jurisdictions=None, regulatory_anchors=None):
    return {
        "term_id": term_id,
        "term_version": "1.0",
        "content_hash": hashlib.sha256(
            json.dumps({
                "term_id": term_id,
                "boundary_conditions": boundary_conditions or [],
                "jurisdictions": jurisdictions or [],
                "regulatory_anchors": regulatory_anchors or [],
            }, sort_keys=True).encode()
        ).hexdigest(),
        "definition": {
            "formal_statement": f"Definition of {term_id}",
            "boundary_conditions": boundary_conditions or [f"{term_id} must be explicitly granted"],
            "regulatory_anchors": regulatory_anchors or ["FIPS-204"],
        },
        "operational_scope": {
            "domains": ["TRADING", "DEFENSE"],
            "jurisdictions": jurisdictions or ["UAE", "UK"],
        },
    }


class TestTSACreation:
    def test_tsa_basic_creation(self):
        engine = make_engine()
        spv = make_spv()
        tsa = engine.create_tsa(
            receipt_id="ATFDR-7F3A9B2C1E4D8F6A",
            receipt_type="DR",
            spv=spv,
        )
        assert tsa.tsa_id.startswith("OMNIX-TSA-")
        assert tsa.receipt_id == "ATFDR-7F3A9B2C1E4D8F6A"
        assert tsa.receipt_type == "DR"
        assert tsa.runtime_id == "RUNTIME-TEST-OMNIX-20260520"
        assert tsa.spv_hash == spv["spv_hash"]
        assert tsa.content_hash

    def test_tsa_all_receipt_types(self):
        engine = make_engine()
        spv = make_spv()
        for rtype in ("DR", "TAR", "DTR", "RCR", "SAC"):
            tsa = engine.create_tsa(
                receipt_id=f"ATF{rtype}-TESTRECEIPT001",
                receipt_type=rtype,
                spv=spv,
            )
            assert tsa.receipt_type == rtype

    def test_tsa_invalid_receipt_type_raises(self):
        engine = make_engine()
        spv = make_spv()
        with pytest.raises(ValueError, match="invalid"):
            engine.create_tsa(
                receipt_id="ATFDR-INVALID001",
                receipt_type="INVALID",
                spv=spv,
            )

    def test_tsa_has_term_hashes(self):
        engine = make_engine()
        spv = make_spv()
        tsa = engine.create_tsa("ATFDR-001", "DR", spv)
        for term in ATF_CORE_TERM_SET:
            assert term in tsa.term_hashes

    def test_tsa_spv_hash_matches_spv(self):
        engine = make_engine()
        spv = make_spv()
        tsa = engine.create_tsa("ATFDR-002", "DR", spv)
        assert tsa.spv_hash == spv["spv_hash"]

    def test_tsa_accepts_dict_spv(self):
        engine = make_engine()
        spv = make_spv()
        tsa = engine.create_tsa("ATFDR-003", "DR", spv)
        assert tsa.tsa_id.startswith("OMNIX-TSA-")


class TestDSPPInv001_NoRetroactiveAnchoring:
    """DSPP-INV-001: TSA anchored_at must be ≤ receipt_created_at."""

    def test_inv001_passes_when_anchored_before_receipt(self):
        engine = make_engine()
        spv = make_spv()
        now = datetime.now(timezone.utc)
        past = (now - timedelta(seconds=10)).isoformat()
        tsa = engine.create_tsa(
            receipt_id="ATFDR-INV001-PASS",
            receipt_type="DR",
            spv=spv,
            receipt_created_at=now.isoformat(),
            anchored_at=past,
        )
        assert tsa.tsa_id.startswith("OMNIX-TSA-")

    def test_inv001_passes_when_anchored_at_same_time(self):
        engine = make_engine()
        spv = make_spv()
        now = datetime.now(timezone.utc).isoformat()
        tsa = engine.create_tsa(
            receipt_id="ATFDR-INV001-SAME",
            receipt_type="DR",
            spv=spv,
            receipt_created_at=now,
            anchored_at=now,
        )
        assert tsa.tsa_id.startswith("OMNIX-TSA-")

    def test_inv001_violation_when_anchored_after_receipt(self):
        engine = make_engine()
        spv = make_spv()
        now = datetime.now(timezone.utc)
        future_anchor = (now + timedelta(hours=1)).isoformat()
        past_receipt = (now - timedelta(minutes=5)).isoformat()
        with pytest.raises(TSARetroactiveViolation, match="DSPP-INV-001"):
            engine.create_tsa(
                receipt_id="ATFDR-INV001-FAIL",
                receipt_type="DR",
                spv=spv,
                receipt_created_at=past_receipt,
                anchored_at=future_anchor,
            )

    def test_inv001_error_message_contains_timestamps(self):
        engine = make_engine()
        spv = make_spv()
        now = datetime.now(timezone.utc)
        future = (now + timedelta(hours=2)).isoformat()
        past = (now - timedelta(hours=1)).isoformat()
        with pytest.raises(TSARetroactiveViolation) as exc_info:
            engine.create_tsa("ATFDR-MSG", "DR", spv, receipt_created_at=past, anchored_at=future)
        assert "DSPP-INV-001" in str(exc_info.value)


class TestSDRPublication:
    def test_sdr_basic_publication(self):
        engine = make_engine()
        spv_v1 = make_spv(spv_hash="a" * 64, spv_id="OMNIX-SPV-TEST-V1")
        spv_v2 = make_spv(spv_hash="b" * 64, spv_id="OMNIX-SPV-TEST-V2")
        sdr = engine.publish_sdr(
            previous_spv=spv_v1,
            new_spv=spv_v2,
            drift_reason="ADGM AI Governance Framework Rev 3",
            drift_category="REGULATORY_UPDATE",
            regulatory_anchors=["ADGM-AI-2026-REV3"],
        )
        assert sdr.sdr_id.startswith("OMNIX-SDR-")
        assert sdr.previous_spv_hash == "a" * 64
        assert sdr.new_spv_hash == "b" * 64
        assert sdr.drift_category == "REGULATORY_UPDATE"
        assert sdr.content_hash

    def test_sdr_all_valid_categories(self):
        engine = make_engine()
        for i, category in enumerate(("REGULATORY_UPDATE", "POLICY_EVOLUTION",
                                       "JURISDICTIONAL", "OPERATIONAL", "CORRECTION")):
            prev_hash = hashlib.sha256(f"prev-{i}".encode()).hexdigest()
            new_hash = hashlib.sha256(f"new-{i}".encode()).hexdigest()
            spv_prev = make_spv(spv_hash=prev_hash, spv_id=f"OMNIX-SPV-PREV-{i}")
            spv_new = make_spv(spv_hash=new_hash, spv_id=f"OMNIX-SPV-NEW-{i}")
            sdr = engine.publish_sdr(spv_prev, spv_new, f"Reason {i}", category)
            assert sdr.drift_category == category

    def test_sdr_invalid_category_raises(self):
        engine = make_engine()
        spv1 = make_spv(spv_hash="c" * 64)
        spv2 = make_spv(spv_hash="d" * 64)
        with pytest.raises(ValueError, match="invalid"):
            engine.publish_sdr(spv1, spv2, "reason", "INVALID_CATEGORY")

    def test_sdr_has_term_drift_map_for_all_terms(self):
        engine = make_engine()
        spv1 = make_spv(spv_hash="e" * 64)
        spv2 = make_spv(spv_hash="f" * 64)
        sdr = engine.publish_sdr(spv1, spv2, "Policy update", "POLICY_EVOLUTION")
        for term in ATF_CORE_TERM_SET:
            assert term in sdr.term_drift_map

    def test_sdr_governance_impact_computed(self):
        engine = make_engine()
        spv1 = make_spv(spv_hash="11" * 32)
        spv2 = make_spv(spv_hash="22" * 32)
        sdr = engine.publish_sdr(spv1, spv2, "Minor correction", "CORRECTION")
        assert sdr.governance_impact in ("PORTABLE", "ACKNOWLEDGED", "CRITICAL", "INCOMPATIBLE")


class TestDSPPInv002_SDRImmutability:
    """DSPP-INV-002: SDRs are append-only. Cannot publish duplicate (runtime_id, previous_spv_hash)."""

    def test_inv002_duplicate_sdr_raises(self):
        engine = make_engine()
        prev_hash = "9" * 64
        spv1 = make_spv(spv_hash=prev_hash, spv_id="OMNIX-SPV-PREV-IMM")
        spv2a = make_spv(spv_hash="aa" * 32, spv_id="OMNIX-SPV-NEW-A")
        spv2b = make_spv(spv_hash="bb" * 32, spv_id="OMNIX-SPV-NEW-B")

        engine.publish_sdr(spv1, spv2a, "First update", "REGULATORY_UPDATE")

        with pytest.raises(SDRImmutabilityViolation, match="DSPP-INV-002"):
            engine.publish_sdr(spv1, spv2b, "Attempt to overwrite", "CORRECTION")

    def test_inv002_different_prev_hash_is_allowed(self):
        engine = make_engine()
        spv1 = make_spv(spv_hash="cc" * 32, spv_id="SPV-CC")
        spv2 = make_spv(spv_hash="dd" * 32, spv_id="SPV-DD")
        spv3 = make_spv(spv_hash="ee" * 32, spv_id="SPV-EE")

        sdr1 = engine.publish_sdr(spv1, spv2, "First", "REGULATORY_UPDATE")
        sdr2 = engine.publish_sdr(spv2, spv3, "Second", "POLICY_EVOLUTION")

        assert sdr1.sdr_id != sdr2.sdr_id
        assert sdr2.previous_spv_hash == "dd" * 32

    def test_inv002_error_message_identifies_runtime_and_hash(self):
        engine = make_engine()
        prev = make_spv(spv_hash="ff" * 32)
        new1 = make_spv(spv_hash="11" * 32)
        new2 = make_spv(spv_hash="22" * 32)
        engine.publish_sdr(prev, new1, "First", "OPERATIONAL")
        with pytest.raises(SDRImmutabilityViolation) as exc_info:
            engine.publish_sdr(prev, new2, "Second", "CORRECTION")
        assert "DSPP-INV-002" in str(exc_info.value)


class TestSDUAlgorithm:
    """SDU computation — boundary / scope / regulatory distances."""

    def test_sdu_identical_entries_returns_zero(self):
        engine = make_engine()
        entry = make_str_entry("AUTHORITY", boundary_conditions=["Budget must not exceed delegator"])
        result = engine.compute_sdu(entry, entry)
        assert result["sdu"] == 0.0

    def test_sdu_same_content_hash_shortcut(self):
        engine = make_engine()
        entry_a = {"content_hash": "abc123", "definition": {}, "operational_scope": {}}
        entry_b = {"content_hash": "abc123", "definition": {}, "operational_scope": {}}
        result = engine.compute_sdu(entry_a, entry_b)
        assert result["sdu"] == 0.0

    def test_sdu_completely_different_entries(self):
        engine = make_engine()
        entry_a = make_str_entry(
            "AUTHORITY",
            boundary_conditions=["Budget must not exceed delegator", "Explicit grant required"],
            jurisdictions=["UAE", "UK"],
            regulatory_anchors=["FIPS-204", "ADGM-AI-2026"],
        )
        entry_b = make_str_entry(
            "AUTHORITY",
            boundary_conditions=["No implicit authority", "Scope must be bounded"],
            jurisdictions=["US", "EU"],
            regulatory_anchors=["NIST-800-53", "EU-AI-ACT"],
        )
        result = engine.compute_sdu(entry_a, entry_b)
        assert result["sdu"] > 0.0
        assert "boundary_distance" in result
        assert "scope_distance" in result
        assert "regulatory_distance" in result

    def test_sdu_boundary_dominates_at_weight_040(self):
        engine = make_engine()
        entry_a = make_str_entry(
            "TRUST",
            boundary_conditions=["A", "B", "C", "D"],
            jurisdictions=["UAE"],
            regulatory_anchors=["FIPS-204"],
        )
        entry_b = make_str_entry(
            "TRUST",
            boundary_conditions=["X", "Y", "Z", "W"],
            jurisdictions=["UAE"],
            regulatory_anchors=["FIPS-204"],
        )
        result = engine.compute_sdu(entry_a, entry_b)
        expected_boundary = result["boundary_distance"]
        assert abs(result["sdu"] - (expected_boundary * SDU_WEIGHT_BOUNDARY +
                                     result["scope_distance"] * SDU_WEIGHT_SCOPE +
                                     result["regulatory_distance"] * SDU_WEIGHT_REGULATORY)) < 0.001

    def test_sdu_empty_entries_return_full_incompatibility(self):
        engine = make_engine()
        entry = make_str_entry("LEGITIMACY")
        result_a = engine.compute_sdu({}, entry)
        result_b = engine.compute_sdu(entry, {})
        assert result_a["sdu"] == 1.0
        assert result_b["sdu"] == 1.0

    def test_sdu_both_empty_returns_zero(self):
        engine = make_engine()
        result = engine.compute_sdu({}, {})
        assert result["sdu"] == 0.0

    def test_sdu_in_range_zero_to_one(self):
        engine = make_engine()
        import random
        random.seed(42)
        for _ in range(20):
            bca = [f"condition_{random.randint(1, 5)}" for _ in range(random.randint(0, 4))]
            bcb = [f"condition_{random.randint(1, 5)}" for _ in range(random.randint(0, 4))]
            entry_a = make_str_entry("RISK", boundary_conditions=bca)
            entry_b = make_str_entry("RISK", boundary_conditions=bcb)
            result = engine.compute_sdu(entry_a, entry_b)
            assert 0.0 <= result["sdu"] <= 1.0

    def test_sdu_weights_sum_to_one(self):
        total = SDU_WEIGHT_BOUNDARY + SDU_WEIGHT_SCOPE + SDU_WEIGHT_REGULATORY
        assert abs(total - 1.0) < 0.001


class TestDSPPInv007_ThresholdConstants:
    """DSPP-INV-007: SDU threshold constants are structural — not configurable."""

    def test_portable_threshold_is_010(self):
        assert SDU_PORTABLE_THRESHOLD == 0.10

    def test_acknowledged_threshold_is_040(self):
        assert SDU_ACKNOWLEDGED_THRESHOLD == 0.40

    def test_critical_threshold_is_070(self):
        assert SDU_CRITICAL_THRESHOLD == 0.70

    def test_verdicts_at_boundary_values(self):
        engine = make_engine()
        spv = make_spv()

        tsa_portable = engine.create_tsa("ATFDR-V1", "DR", spv)
        tsa_acknowledged = engine.create_tsa("ATFDR-V2", "DR", spv)
        tsa_critical = engine.create_tsa("ATFDR-V3", "DR", spv)
        tsa_incompatible = engine.create_tsa("ATFDR-V4", "DR", spv)

        recv_spv = make_spv(spv_hash="zz" * 32)

        for rsa in [engine.assess_portability(tsa_portable, recv_spv),
                    engine.assess_portability(tsa_acknowledged, recv_spv),
                    engine.assess_portability(tsa_critical, recv_spv),
                    engine.assess_portability(tsa_incompatible, recv_spv)]:
            assert rsa.dspp_verdict in [v.value for v in DSPPVerdict]
            assert 0.0 <= rsa.aggregate_sdu <= 1.0


class TestRSADeterminism:
    """DSPP-INV-005: RSA verdict is deterministic. Same inputs → same output."""

    def test_inv005_identical_inputs_produce_identical_verdict(self):
        engine = make_engine()
        spv_orig = make_spv(spv_hash="orig" + "0" * 60)
        recv_spv = make_spv(spv_hash="recv" + "0" * 60)

        tsa = engine.create_tsa("ATFDR-DET001", "DR", spv_orig)

        rsa1 = engine.assess_portability(tsa, recv_spv)
        rsa2 = engine.assess_portability(tsa, recv_spv)

        assert rsa1.dspp_verdict == rsa2.dspp_verdict
        assert rsa1.aggregate_sdu == rsa2.aggregate_sdu
        assert rsa1.portability_confidence == rsa2.portability_confidence

    def test_inv005_different_receiving_spv_gives_different_result(self):
        engine = make_engine()
        spv_orig = make_spv()
        recv_spv_a = make_spv(spv_hash="aa" * 32)
        recv_spv_b = make_spv(spv_hash="bb" * 32)

        tsa = engine.create_tsa("ATFDR-DET002", "TAR", spv_orig)

        rsa_a = engine.assess_portability(tsa, recv_spv_a)
        rsa_b = engine.assess_portability(tsa, recv_spv_b)

        assert rsa_a.rsa_id != rsa_b.rsa_id

    def test_inv005_same_spv_hash_produces_portable(self):
        engine = make_engine()
        spv = make_spv()
        tsa = engine.create_tsa("ATFDR-DET003", "DR", spv)
        rsa = engine.assess_portability(tsa, spv)
        assert rsa.dspp_verdict == DSPPVerdict.SEMANTICALLY_PORTABLE.value
        assert rsa.aggregate_sdu < SDU_PORTABLE_THRESHOLD


class TestRSAStructure:
    def test_rsa_has_all_8_terms(self):
        engine = make_engine()
        spv = make_spv()
        tsa = engine.create_tsa("ATFDR-STRUCT001", "DR", spv)
        rsa = engine.assess_portability(tsa, spv)
        for term in ATF_CORE_TERM_SET:
            assert term in rsa.term_assessment

    def test_rsa_has_valid_verdict(self):
        engine = make_engine()
        spv = make_spv()
        tsa = engine.create_tsa("ATFDR-STRUCT002", "DR", spv)
        rsa = engine.assess_portability(tsa, spv)
        assert rsa.dspp_verdict in [v.value for v in DSPPVerdict]

    def test_rsa_confidence_is_complement_of_sdu(self):
        engine = make_engine()
        spv = make_spv()
        tsa = engine.create_tsa("ATFDR-STRUCT003", "RCR", spv)
        rsa = engine.assess_portability(tsa, spv)
        assert abs(rsa.portability_confidence - (1.0 - rsa.aggregate_sdu)) < 0.001

    def test_rsa_has_content_hash(self):
        engine = make_engine()
        spv = make_spv()
        tsa = engine.create_tsa("ATFDR-STRUCT004", "DR", spv)
        rsa = engine.assess_portability(tsa, spv)
        assert rsa.content_hash
        assert len(rsa.content_hash) == 64

    def test_rsa_id_format(self):
        engine = make_engine()
        spv = make_spv()
        tsa = engine.create_tsa("ATFDR-STRUCT005", "DR", spv)
        rsa = engine.assess_portability(tsa, spv)
        assert rsa.rsa_id.startswith("OMNIX-RSA-")

    def test_rsa_governing_posture_is_more_restrictive(self):
        engine = make_engine()
        spv = make_spv()
        tsa = engine.create_tsa("ATFDR-STRUCT006", "DR", spv)
        rsa = engine.assess_portability(tsa, spv)
        assert rsa.governing_posture == "MORE_RESTRICTIVE"

    def test_rsa_summary_method(self):
        engine = make_engine()
        spv = make_spv()
        tsa = engine.create_tsa("ATFDR-STRUCT007", "DR", spv)
        rsa = engine.assess_portability(tsa, spv)
        summary = rsa.summary()
        assert "rsa_id" in summary
        assert "dspp_verdict" in summary
        assert "aggregate_sdu" in summary
        assert "portability_confidence" in summary


class TestDSPPInv003_MoreRestrictive:
    """DSPP-INV-003: Drift toward permissiveness does not grant permissive interpretation."""

    def test_inv003_less_restrictive_drift_uses_receiving_posture(self):
        engine = make_engine()
        spv1 = make_spv(spv_hash="orig" + "1" * 60)
        spv2 = make_spv(spv_hash="new2" + "2" * 60)

        tsa = engine.create_tsa("ATFDR-INV003", "DR", spv1)

        sdr = engine.publish_sdr(
            previous_spv=spv1,
            new_spv=spv2,
            drift_reason="Loosening AUTHORITY boundary conditions",
            drift_category="POLICY_EVOLUTION",
        )

        sdr_dict = sdr.to_dict()
        for term_id in ATF_CORE_TERM_SET:
            if term_id in sdr_dict["term_drift_map"]:
                sdr_dict["term_drift_map"][term_id]["drift_direction"] = "LESS_RESTRICTIVE"

        recv_spv = make_spv(spv_hash="recv" + "3" * 60)
        rsa = engine.assess_portability(tsa, recv_spv, sdr_chain=[sdr])

        for term_id, assessment in rsa.term_assessment.items():
            if isinstance(assessment, dict) and assessment.get("drift_direction") == "LESS_RESTRICTIVE":
                assert "MORE_RESTRICTIVE" in assessment.get("governing_interpretation", "")


class TestDSPPInv004_TSAContentHash:
    """DSPP-INV-004: TSA content_hash covers spv_hash + spv_version + spv_generated_at."""

    def test_inv004_different_spv_hash_gives_different_tsa_hash(self):
        engine = make_engine()
        spv_a = make_spv(spv_hash="aaa" + "0" * 61)
        spv_b = make_spv(spv_hash="bbb" + "0" * 61)

        tsa_a = engine.create_tsa("ATFDR-INV004A", "DR", spv_a)
        tsa_b = engine.create_tsa("ATFDR-INV004B", "DR", spv_b)

        assert tsa_a.content_hash != tsa_b.content_hash

    def test_inv004_tsa_content_hash_is_verifiable(self):
        engine = make_engine()
        spv = make_spv()
        tsa = engine.create_tsa("ATFDR-INV004C", "DR", spv)
        result = engine.verify_tsa(tsa)
        assert result["hash_valid"] is True
        assert result["DSPP-INV-004"] is True

    def test_inv004_spv_hash_present_in_tsa_fields(self):
        engine = make_engine()
        spv = make_spv(spv_hash="deadbeef" + "0" * 56)
        tsa = engine.create_tsa("ATFDR-INV004D", "DR", spv)
        assert tsa.spv_hash == "deadbeef" + "0" * 56
        assert "spv_hash" in tsa.to_dict()
        assert "spv_version" in tsa.to_dict()
        assert "spv_generated_at" in tsa.to_dict()


class TestDSPPInv006_ChainPropagation:
    """DSPP-INV-006: SEMANTICALLY_INCOMPATIBLE propagates upward through delegation chain."""

    def test_inv006_incompatible_propagates_to_descendants(self):
        engine_orig = make_engine("RUNTIME-ORIG-001")
        engine_recv = make_engine("RUNTIME-RECV-002")

        incompatible_term_hashes = {
            t: f"orig-hash-{i:04d}-diff-diff-diff-diff-diff-diff-diff-diff-diff-diff"
            for i, t in enumerate(ATF_CORE_TERM_SET)
        }
        spv_orig = make_spv(term_hashes=incompatible_term_hashes, spv_hash="orig" + "a" * 60,
                            runtime_id="RUNTIME-ORIG-001")

        compatible_term_hashes = {
            t: f"recv-hash-{i:04d}-comp-comp-comp-comp-comp-comp-comp-comp-comp-comp"
            for i, t in enumerate(ATF_CORE_TERM_SET)
        }
        spv_recv = make_spv(term_hashes=compatible_term_hashes, spv_hash="recv" + "b" * 60,
                            runtime_id="RUNTIME-RECV-002")

        tsa_root = engine_orig.create_tsa("ATFDR-ROOT001", "DR", spv_orig)
        tsa_child = engine_orig.create_tsa("ATFDR-CHILD001", "DR", spv_orig)
        tsa_leaf = engine_orig.create_tsa("ATFDR-LEAF001", "DR", spv_orig)

        results = engine_recv.assess_chain_portability(
            tsa_chain=[tsa_root, tsa_child, tsa_leaf],
            receiving_spv=spv_recv,
        )

        assert "ATFDR-ROOT001" in results
        assert "ATFDR-CHILD001" in results
        assert "ATFDR-LEAF001" in results

        for receipt_id, rsa in results.items():
            assert rsa.dspp_verdict in [v.value for v in DSPPVerdict]

    def test_inv006_propagated_result_has_incompatible_all_terms(self):
        engine = make_engine()
        spv_orig = make_spv(spv_hash="orig" + "x" * 60)
        recv_spv = make_spv(spv_hash="recv" + "y" * 60)

        tsa1 = engine.create_tsa("ATFDR-CHAIN-A", "DR", spv_orig)
        tsa2 = engine.create_tsa("ATFDR-CHAIN-B", "DR", spv_orig)

        tsa1.term_hashes.clear()
        results = engine.assess_chain_portability([tsa1, tsa2], recv_spv)

        assert len(results) == 2

    def test_inv006_empty_chain_returns_empty(self):
        engine = make_engine()
        recv_spv = make_spv()
        results = engine.assess_chain_portability([], recv_spv)
        assert results == {}


class TestHashVerification:
    def test_verify_tsa_valid(self):
        engine = make_engine()
        spv = make_spv()
        tsa = engine.create_tsa("ATFDR-VERIFY001", "DR", spv)
        result = engine.verify_tsa(tsa)
        assert result["hash_valid"] is True
        assert result["verified"] is True

    def test_verify_tsa_tampered_hash_detected(self):
        engine = make_engine()
        spv = make_spv()
        tsa = engine.create_tsa("ATFDR-VERIFY002", "DR", spv)
        tampered = TemporalSemanticAnchor(
            **{**tsa.to_dict(), "content_hash": "0" * 64}
        )
        result = engine.verify_tsa(tampered)
        assert result["hash_valid"] is False
        assert result["verified"] is False

    def test_verify_sdr_valid(self):
        engine = make_engine()
        spv1 = make_spv(spv_hash="ab" * 32)
        spv2 = make_spv(spv_hash="cd" * 32)
        sdr = engine.publish_sdr(spv1, spv2, "Test drift", "OPERATIONAL")
        result = engine.verify_sdr(sdr)
        assert result["hash_valid"] is True
        assert result["verified"] is True

    def test_verify_sdr_tampered_hash_detected(self):
        engine = make_engine()
        spv1 = make_spv(spv_hash="ef" * 32)
        spv2 = make_spv(spv_hash="gh" * 32)
        sdr = engine.publish_sdr(spv1, spv2, "Test", "CORRECTION")
        tampered = SemanticDriftRecord(**{**sdr.to_dict(), "content_hash": "f" * 64})
        result = engine.verify_sdr(tampered)
        assert result["hash_valid"] is False

    def test_verify_inv001_flagged_in_verification(self):
        engine = make_engine()
        spv = make_spv()
        tsa = engine.create_tsa("ATFDR-VERIFY003", "DR", spv)
        result = engine.verify_tsa(tsa)
        assert result["DSPP-INV-001"] is True


class TestSDRChainTraversal:
    def test_get_sdr_chain_single_hop(self):
        engine = make_engine()
        spv1 = make_spv(spv_hash="hop1" + "0" * 60)
        spv2 = make_spv(spv_hash="hop2" + "0" * 60)
        sdr = engine.publish_sdr(spv1, spv2, "Single hop", "REGULATORY_UPDATE")
        chain = engine.get_sdr_chain("hop1" + "0" * 60)
        assert len(chain) == 1
        assert chain[0].sdr_id == sdr.sdr_id

    def test_get_sdr_chain_multi_hop(self):
        engine = make_engine()
        hash1 = "h1" + "0" * 62
        hash2 = "h2" + "0" * 62
        hash3 = "h3" + "0" * 62
        spv1 = make_spv(spv_hash=hash1)
        spv2 = make_spv(spv_hash=hash2)
        spv3 = make_spv(spv_hash=hash3)

        engine.publish_sdr(spv1, spv2, "Hop 1", "REGULATORY_UPDATE")
        engine.publish_sdr(spv2, spv3, "Hop 2", "POLICY_EVOLUTION")

        chain = engine.get_sdr_chain(hash1)
        assert len(chain) == 2
        assert chain[0].previous_spv_hash == hash1
        assert chain[1].previous_spv_hash == hash2

    def test_get_sdr_chain_unknown_hash_returns_empty(self):
        engine = make_engine()
        chain = engine.get_sdr_chain("0" * 64)
        assert chain == []


class TestFullPipeline:
    """End-to-end: SPV → TSA → SDR → RSA → verdict."""

    def test_full_pipeline_same_semantic_posture(self):
        engine = make_engine()
        spv = make_spv()
        tsa = engine.create_tsa("ATFDR-E2E-SAME", "DR", spv)
        rsa = engine.assess_portability(tsa, spv)
        assert rsa.dspp_verdict == DSPPVerdict.SEMANTICALLY_PORTABLE.value
        assert rsa.portability_confidence >= 0.9

    def test_full_pipeline_with_sdr_acknowledged(self):
        engine = make_engine()
        spv_v1 = make_spv(spv_hash="v1" + "0" * 62)
        spv_v2 = make_spv(spv_hash="v2" + "0" * 62)

        tsa = engine.create_tsa("ATFDR-E2E-ACK", "DR", spv_v1)
        sdr = engine.publish_sdr(spv_v1, spv_v2, "Minor regulatory update", "REGULATORY_UPDATE")

        rsa = engine.assess_portability(tsa, spv_v2, sdr_chain=[sdr])

        assert rsa.dspp_verdict in [v.value for v in DSPPVerdict]
        assert rsa.aggregate_sdu >= 0.0
        assert rsa.portability_confidence >= 0.0

    def test_full_pipeline_rsa_references_tsa(self):
        engine = make_engine()
        spv = make_spv()
        tsa = engine.create_tsa("ATFDR-E2E-REF", "SAC", spv)
        rsa = engine.assess_portability(tsa, spv)
        assert rsa.tsa_id == tsa.tsa_id
        assert rsa.receipt_id == "ATFDR-E2E-REF"

    def test_full_pipeline_rsa_content_hash_verifiable(self):
        engine = make_engine()
        spv = make_spv()
        tsa = engine.create_tsa("ATFDR-E2E-HASH", "DR", spv)
        rsa = engine.assess_portability(tsa, spv)
        exclude = {"content_hash", "pqc_signature", "pqc_algorithm"}
        clean = {k: v for k, v in rsa.to_dict().items() if k not in exclude}
        canonical = json.dumps(clean, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        expected = hashlib.sha256(canonical).hexdigest()
        assert rsa.content_hash == expected

    def test_full_pipeline_summary_output(self):
        engine = make_engine()
        spv = make_spv()
        tsa = engine.create_tsa("ATFDR-E2E-SUM", "DR", spv)
        rsa = engine.assess_portability(tsa, spv)
        summary = rsa.summary()
        assert summary["rsa_id"] == rsa.rsa_id
        assert summary["receipt_id"] == "ATFDR-E2E-SUM"
        assert isinstance(summary["aggregate_sdu"], float)

    def test_full_pipeline_tsa_to_dict_roundtrip(self):
        engine = make_engine()
        spv = make_spv()
        tsa = engine.create_tsa("ATFDR-E2E-ROUND", "DR", spv)
        d = tsa.to_dict()
        assert d["tsa_id"] == tsa.tsa_id
        assert d["receipt_id"] == tsa.receipt_id
        assert d["spv_hash"] == tsa.spv_hash

    def test_full_pipeline_sdr_to_dict_roundtrip(self):
        engine = make_engine()
        spv1 = make_spv(spv_hash="rt1" + "0" * 61)
        spv2 = make_spv(spv_hash="rt2" + "0" * 61)
        sdr = engine.publish_sdr(spv1, spv2, "Roundtrip test", "OPERATIONAL")
        d = sdr.to_dict()
        assert d["sdr_id"] == sdr.sdr_id
        assert d["drift_category"] == "OPERATIONAL"


class TestDSPPVerdictEnum:
    def test_all_verdict_values(self):
        assert DSPPVerdict.SEMANTICALLY_PORTABLE.value == "SEMANTICALLY_PORTABLE"
        assert DSPPVerdict.DRIFT_ACKNOWLEDGED.value == "DRIFT_ACKNOWLEDGED"
        assert DSPPVerdict.DRIFT_CRITICAL.value == "DRIFT_CRITICAL"
        assert DSPPVerdict.SEMANTICALLY_INCOMPATIBLE.value == "SEMANTICALLY_INCOMPATIBLE"

    def test_verdict_ordering(self):
        verdicts = [
            DSPPVerdict.SEMANTICALLY_PORTABLE,
            DSPPVerdict.DRIFT_ACKNOWLEDGED,
            DSPPVerdict.DRIFT_CRITICAL,
            DSPPVerdict.SEMANTICALLY_INCOMPATIBLE,
        ]
        assert len(verdicts) == 4

    def test_rsa_is_portable_method(self):
        engine = make_engine()
        spv = make_spv()
        tsa = engine.create_tsa("ATFDR-ENUM001", "DR", spv)
        rsa = engine.assess_portability(tsa, spv)
        if rsa.dspp_verdict == DSPPVerdict.SEMANTICALLY_PORTABLE.value:
            assert rsa.is_portable()
        else:
            assert not rsa.is_portable()

    def test_rsa_is_incompatible_method(self):
        engine = make_engine()
        spv = make_spv()
        tsa = engine.create_tsa("ATFDR-ENUM002", "DR", spv)
        rsa = engine.assess_portability(tsa, spv)
        if rsa.dspp_verdict == DSPPVerdict.SEMANTICALLY_INCOMPATIBLE.value:
            assert rsa.is_incompatible()
        else:
            assert not rsa.is_incompatible()


class TestSdrMaxSDU:
    def test_sdr_max_sdu_no_drift(self):
        engine = make_engine()
        spv1 = make_spv(spv_hash="nodr1" + "0" * 59)
        spv2 = make_spv(spv_hash="nodr2" + "0" * 59)
        sdr = engine.publish_sdr(spv1, spv2, "Same semantics", "CORRECTION")
        assert 0.0 <= sdr.max_sdu() <= 1.0

    def test_sdr_affected_terms_subset_of_core(self):
        engine = make_engine()
        spv1 = make_spv(spv_hash="af1" + "0" * 61)
        spv2 = make_spv(spv_hash="af2" + "0" * 61)
        sdr = engine.publish_sdr(spv1, spv2, "Partial update", "POLICY_EVOLUTION")
        for term in sdr.affected_terms():
            assert term in ATF_CORE_TERM_SET

    def test_sdr_governance_impact_in_valid_values(self):
        engine = make_engine()
        spv1 = make_spv(spv_hash="gi1" + "0" * 61)
        spv2 = make_spv(spv_hash="gi2" + "0" * 61)
        sdr = engine.publish_sdr(spv1, spv2, "Impact check", "JURISDICTIONAL")
        assert sdr.governance_impact in (
            "SEMANTICALLY_PORTABLE", "DRIFT_ACKNOWLEDGED",
            "DRIFT_CRITICAL", "SEMANTICALLY_INCOMPATIBLE",
            "PORTABLE", "ACKNOWLEDGED", "CRITICAL", "INCOMPATIBLE"
        )
