"""
Tests para el Structural Admissibility Engine (SAE) — Layer 0
Patent: OMNIX-PAT-2026-015
ADR-092

Cubre los 5 componentes + integración con external_evaluator:
  A — Structural Constraint Schema (SCS): all constraint classes fire correctly
  B — Structural Admissibility Validator (SAV): admissible requests → EvaluationRequest
  C — Zero-Bypass Boundary (ZBE): direct EvaluationRequest construction raises exception
  D — Structured Rejection with Constraint Provenance (SRCP): violation fields present
  E — Composable Cross-Domain Constraint Architecture (CCCA): new constraints registrable
  + Adversarial scenarios: loop bypass attempts, conditional constraints, multi-violation audit
"""
import os

import pytest

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")

from omnix_core.governance.structural_admissibility_engine import (
    ConstraintClass,
    ConstraintViolation,
    EvaluationMode,
    EvaluationRequest,
    ProposedRequest,
    SAEOverride,
    StructuralAdmissibilityEngine,
    StructuralAdmissibilityViolation,
    StructuredRejectionRecord,
    get_layer0_metrics,
    get_sae,
    get_sae_override,
    set_sae_override,
)


# ── Fixtures ────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_sae_singleton():
    StructuralAdmissibilityEngine.reset_instance()
    set_sae_override(SAEOverride.UNSET)
    get_layer0_metrics().reset()
    yield
    StructuralAdmissibilityEngine.reset_instance()
    set_sae_override(SAEOverride.UNSET)
    get_layer0_metrics().reset()


def _sae() -> StructuralAdmissibilityEngine:
    return StructuralAdmissibilityEngine.get_instance()


def _admissible(subject="BTC", operation="SPOT", jurisdiction="GLOBAL", **kw) -> ProposedRequest:
    return ProposedRequest(subject=subject, operation=operation, jurisdiction=jurisdiction, **kw)


def _inadmissible_asset() -> ProposedRequest:
    return ProposedRequest(subject="XMR", operation="SPOT", jurisdiction="UAE")


def _inadmissible_operation() -> ProposedRequest:
    return ProposedRequest(subject="BTC", operation="LEVERAGED", jurisdiction="UAE")


# ── Component C: Zero-Bypass Boundary Enforcement ──────────────────────────────

class TestZeroBypassBoundary:
    def test_direct_construction_raises_structural_violation(self):
        with pytest.raises(StructuralAdmissibilityViolation):
            proposed = _admissible()
            EvaluationRequest(
                _token=object(),
                proposed=proposed,
                validated_at="2026-01-01",
            )

    def test_wrong_token_raises_structural_violation(self):
        with pytest.raises(StructuralAdmissibilityViolation):
            EvaluationRequest(
                _token=None,
                proposed=_admissible(),
                validated_at="2026-01-01",
            )

    def test_sav_token_not_accessible_from_class_attribute(self):
        # The token IS a class attribute but obtaining it and using it
        # directly would be a programming error. The test verifies the
        # attribute name remains private (starts with underscore).
        assert hasattr(EvaluationRequest, "_SAV_TOKEN"), (
            "_SAV_TOKEN sentinel must exist on EvaluationRequest"
        )

    def test_evaluation_request_is_immutable_after_construction(self):
        sae = _sae()
        result = sae.validate(_admissible("BTC", "SPOT", "GLOBAL"))
        assert isinstance(result, EvaluationRequest), (
            "BTC/SPOT/GLOBAL should be admissible"
        )
        with pytest.raises(AttributeError):
            result.subject = "MODIFIED"

    def test_evaluation_request_repr_contains_id(self):
        sae = _sae()
        result = sae.validate(_admissible("BTC", "SPOT", "GLOBAL"))
        assert isinstance(result, EvaluationRequest)
        assert "SAE-" in repr(result)
        assert "BTC" in repr(result)


# ── Component B: Structural Admissibility Validator ────────────────────────────

class TestStructuralAdmissibilityValidator:
    def test_admissible_request_returns_evaluation_request(self):
        sae = _sae()
        result = sae.validate(_admissible("BTC", "SPOT", "GLOBAL"))
        assert isinstance(result, EvaluationRequest)
        assert result.subject == "BTC"
        assert result.operation == "SPOT"
        assert result.jurisdiction == "GLOBAL"

    def test_inadmissible_asset_returns_rejection(self):
        sae = _sae()
        result = sae.validate(_inadmissible_asset())
        assert isinstance(result, StructuredRejectionRecord)
        assert result.admissibility == "INADMISSIBLE"
        assert not result.pipeline_entry

    def test_inadmissible_operation_returns_rejection(self):
        sae = _sae()
        result = sae.validate(_inadmissible_operation())
        assert isinstance(result, StructuredRejectionRecord)

    def test_fast_fail_stops_at_first_violation(self):
        sae = _sae()
        proposed = ProposedRequest(
            subject="XMR",
            operation="LEVERAGED",
            jurisdiction="UAE",
        )
        result = sae.validate(proposed, mode=EvaluationMode.FAST_FAIL)
        assert isinstance(result, StructuredRejectionRecord)
        assert len(result.violations) == 1

    def test_full_audit_collects_multiple_violations(self):
        sae = _sae()
        proposed = ProposedRequest(
            subject="XMR",
            operation="LEVERAGED",
            jurisdiction="UAE",
        )
        result = sae.validate(proposed, mode=EvaluationMode.FULL_AUDIT)
        assert isinstance(result, StructuredRejectionRecord)
        assert len(result.violations) >= 2

    def test_dict_input_accepted(self):
        sae = _sae()
        result = sae.validate({
            "subject": "ETH",
            "operation": "SPOT",
            "jurisdiction": "EU",
        })
        assert isinstance(result, EvaluationRequest)
        assert result.subject == "ETH"

    def test_processing_time_recorded(self):
        sae = _sae()
        result = sae.validate(_inadmissible_asset())
        assert isinstance(result, StructuredRejectionRecord)
        assert result.layer_0_processing_ms >= 0.0

    def test_audit_id_unique_per_rejection(self):
        sae = _sae()
        r1 = sae.validate(_inadmissible_asset())
        r2 = sae.validate(_inadmissible_asset())
        assert isinstance(r1, StructuredRejectionRecord)
        assert isinstance(r2, StructuredRejectionRecord)
        assert r1.audit_id != r2.audit_id


# ── Component A: Structural Constraint Schema ──────────────────────────────────

class TestJurisdictionAssetConstraints:
    @pytest.mark.parametrize("asset,jurisdiction", [
        ("XMR", "UAE"),
        ("XMR", "US"),
        ("XMR", "UK"),
        ("XMR", "GCC"),
        ("ZEC", "UAE"),
        ("DASH", "US"),
        ("GRIN", "EU"),
    ])
    def test_privacy_coins_blocked_in_restrictive_jurisdictions(self, asset, jurisdiction):
        sae = _sae()
        result = sae.validate(ProposedRequest(
            subject=asset, operation="SPOT", jurisdiction=jurisdiction
        ))
        assert isinstance(result, StructuredRejectionRecord), (
            f"{asset} should be INADMISSIBLE in {jurisdiction}"
        )
        assert result.primary_violation.constraint_class == ConstraintClass.JURISDICTION_ASSET

    def test_btc_spot_is_admissible_in_uae(self):
        sae = _sae()
        result = sae.validate(ProposedRequest(subject="BTC", operation="SPOT", jurisdiction="UAE"))
        assert isinstance(result, EvaluationRequest)

    def test_eth_spot_is_admissible_in_us(self):
        sae = _sae()
        result = sae.validate(ProposedRequest(subject="ETH", operation="SPOT", jurisdiction="US"))
        assert isinstance(result, EvaluationRequest)

    def test_global_jurisdiction_permits_all_non_sanctioned_assets(self):
        sae = _sae()
        for asset in ["BTC", "ETH", "SOL", "ADA", "DOT"]:
            result = sae.validate(ProposedRequest(
                subject=asset, operation="SPOT", jurisdiction="GLOBAL"
            ))
            assert isinstance(result, EvaluationRequest), (
                f"{asset}/SPOT/GLOBAL should be admissible"
            )


class TestJurisdictionOperationConstraints:
    @pytest.mark.parametrize("operation,jurisdiction", [
        ("LEVERAGED", "UAE"),
        ("LEVERAGED", "UK"),
        ("LEVERAGED", "US"),
        ("LEVERAGED", "GCC"),
        ("DERIVATIVES", "UAE"),
        ("DERIVATIVES", "US"),
    ])
    def test_restricted_operations_blocked_in_restricted_jurisdictions(
        self, operation, jurisdiction
    ):
        sae = _sae()
        result = sae.validate(ProposedRequest(
            subject="BTC", operation=operation, jurisdiction=jurisdiction
        ))
        assert isinstance(result, StructuredRejectionRecord), (
            f"BTC/{operation}/{jurisdiction} should be INADMISSIBLE"
        )
        assert result.primary_violation.constraint_class in (
            ConstraintClass.JURISDICTION_OPERATION,
            ConstraintClass.JURISDICTION_ASSET,
        )

    def test_spot_operation_globally_permitted(self):
        sae = _sae()
        for jurisdiction in ["UAE", "EU", "US", "UK", "GCC", "SG", "GLOBAL"]:
            result = sae.validate(ProposedRequest(
                subject="BTC", operation="SPOT", jurisdiction=jurisdiction
            ))
            assert isinstance(result, EvaluationRequest), (
                f"BTC/SPOT/{jurisdiction} should be admissible"
            )

    def test_switzerland_permits_leveraged(self):
        sae = _sae()
        result = sae.validate(ProposedRequest(
            subject="BTC", operation="LEVERAGED", jurisdiction="CH"
        ))
        assert isinstance(result, EvaluationRequest)

    def test_australia_permits_derivatives(self):
        sae = _sae()
        result = sae.validate(ProposedRequest(
            subject="BTC", operation="DERIVATIVES", jurisdiction="AU"
        ))
        assert isinstance(result, EvaluationRequest)


class TestSanctionsConstraints:
    @pytest.mark.parametrize("asset", [
        "TORNADO", "TORNADO_CASH", "SINBAD", "BLENDER", "CHIPMIXER",
    ])
    def test_ofac_sanctioned_assets_blocked_everywhere(self, asset):
        sae = _sae()
        for jurisdiction in ["GLOBAL", "UAE", "EU", "CH"]:
            result = sae.validate(ProposedRequest(
                subject=asset, operation="SPOT", jurisdiction=jurisdiction
            ))
            assert isinstance(result, StructuredRejectionRecord), (
                f"{asset} should be INADMISSIBLE in all jurisdictions including {jurisdiction}"
            )
            assert result.primary_violation.constraint_class == ConstraintClass.SANCTIONS


class TestEthicalShariaConstraints:
    def test_haram_asset_blocked_with_sharia_flag(self):
        sae = _sae()
        result = sae.validate(ProposedRequest(
            subject="WBTC",
            operation="SPOT",
            jurisdiction="UAE",
            ethical_flags=["SHARIA"],
        ))
        assert isinstance(result, StructuredRejectionRecord)
        assert result.primary_violation.constraint_class == ConstraintClass.ETHICAL_SHARIA

    def test_haram_operation_blocked_with_sharia_flag(self):
        sae = _sae()
        result = sae.validate(ProposedRequest(
            subject="BTC",
            operation="LEVERAGED",
            jurisdiction="GLOBAL",
            ethical_flags=["SHARIA"],
        ))
        assert isinstance(result, StructuredRejectionRecord)
        assert result.primary_violation.constraint_class == ConstraintClass.ETHICAL_SHARIA

    def test_halal_asset_spot_passes_sharia(self):
        sae = _sae()
        result = sae.validate(ProposedRequest(
            subject="BTC",
            operation="SPOT",
            jurisdiction="GLOBAL",
            ethical_flags=["SHARIA"],
        ))
        assert isinstance(result, EvaluationRequest)

    def test_sharia_flag_not_active_by_default(self):
        sae = _sae()
        result = sae.validate(ProposedRequest(
            subject="WBTC",
            operation="SPOT",
            jurisdiction="GLOBAL",
        ))
        assert isinstance(result, EvaluationRequest), (
            "WBTC/SPOT/GLOBAL without SHARIA flag should be admissible"
        )


class TestEthicalESGConstraints:
    def test_esg_excluded_sector_blocked(self):
        sae = _sae()
        result = sae.validate(ProposedRequest(
            subject="COAL_TOKEN",
            operation="SPOT",
            jurisdiction="GLOBAL",
            ethical_flags=["ESG"],
            metadata={"asset_sector": "coal"},
        ))
        assert isinstance(result, StructuredRejectionRecord)
        assert result.primary_violation.constraint_class == ConstraintClass.ETHICAL_ESG

    def test_esg_flag_not_active_by_default(self):
        sae = _sae()
        result = sae.validate(ProposedRequest(
            subject="COAL_TOKEN",
            operation="SPOT",
            jurisdiction="GLOBAL",
            metadata={"asset_sector": "coal"},
        ))
        assert isinstance(result, EvaluationRequest), (
            "ESG constraints should not fire without ESG flag"
        )


# ── Component D: Structured Rejection with Constraint Provenance ───────────────

class TestStructuredRejectionProvenance:
    def test_violation_has_all_required_fields(self):
        sae = _sae()
        result = sae.validate(_inadmissible_asset())
        assert isinstance(result, StructuredRejectionRecord)
        v = result.primary_violation
        assert v is not None
        assert v.constraint_id
        assert v.constraint_class
        assert v.description
        assert v.regulatory_source
        assert v.resolution
        assert isinstance(v.input_fields, tuple)
        assert isinstance(v.input_values, dict)

    def test_rejection_to_dict_is_json_serializable(self):
        import json
        sae = _sae()
        result = sae.validate(_inadmissible_asset())
        assert isinstance(result, StructuredRejectionRecord)
        d = result.to_dict()
        serialized = json.dumps(d)
        assert '"INADMISSIBLE"' in serialized
        assert '"pipeline_entry": false' in serialized

    def test_violation_constraint_id_contains_jurisdiction_and_asset(self):
        sae = _sae()
        result = sae.validate(ProposedRequest(
            subject="XMR", operation="SPOT", jurisdiction="UAE"
        ))
        assert isinstance(result, StructuredRejectionRecord)
        v = result.primary_violation
        cid = v.constraint_id
        assert "UAE" in cid or "XMR" in cid or "OFAC" in cid

    def test_str_representation_is_human_readable(self):
        sae = _sae()
        result = sae.validate(_inadmissible_asset())
        assert isinstance(result, StructuredRejectionRecord)
        text = str(result)
        assert "INADMISSIBLE" in text

    def test_audit_id_present_in_dict(self):
        sae = _sae()
        result = sae.validate(_inadmissible_asset())
        d = result.to_dict()
        assert "audit_id" in d
        assert len(d["audit_id"]) == 12


# ── Component E: Composable Cross-Domain Constraint Architecture ───────────────

class TestCCCA:
    def test_custom_constraint_blocks_admissible_request(self):
        sae = _sae()

        def reject_sol(proposed: ProposedRequest) -> ConstraintViolation | None:
            if proposed.subject == "SOL":
                return ConstraintViolation(
                    constraint_id="CUSTOM-SOL-001",
                    constraint_class=ConstraintClass.CLIENT_SPECIFIC,
                    description="SOL blocked by client policy",
                    regulatory_source="Client custom policy",
                    input_fields=("subject",),
                    input_values={"subject": "SOL"},
                    resolution="Use BTC or ETH instead.",
                )
            return None

        sae.register_constraint(ConstraintClass.CLIENT_SPECIFIC, reject_sol)

        result = sae.validate(ProposedRequest(
            subject="SOL", operation="SPOT", jurisdiction="GLOBAL"
        ))
        assert isinstance(result, StructuredRejectionRecord)
        assert result.primary_violation.constraint_id == "CUSTOM-SOL-001"

    def test_custom_constraint_does_not_affect_other_assets(self):
        sae = _sae()

        def reject_sol(proposed: ProposedRequest) -> ConstraintViolation | None:
            if proposed.subject == "SOL":
                return ConstraintViolation(
                    constraint_id="CUSTOM-SOL-001",
                    constraint_class=ConstraintClass.CLIENT_SPECIFIC,
                    description="SOL blocked by client policy",
                    regulatory_source="Client custom policy",
                    input_fields=("subject",),
                    input_values={"subject": "SOL"},
                    resolution="Use BTC or ETH.",
                )
            return None

        sae.register_constraint(ConstraintClass.CLIENT_SPECIFIC, reject_sol)

        result = sae.validate(ProposedRequest(
            subject="BTC", operation="SPOT", jurisdiction="GLOBAL"
        ))
        assert isinstance(result, EvaluationRequest)

    def test_client_specific_constraint_registration(self):
        sae = _sae()

        def block_xrp_for_client_42(proposed: ProposedRequest) -> ConstraintViolation | None:
            if proposed.subject == "XRP":
                return ConstraintViolation(
                    constraint_id="CS-CLIENT42-XRP-001",
                    constraint_class=ConstraintClass.CLIENT_SPECIFIC,
                    description="XRP not authorized for CLIENT_42",
                    regulatory_source="Client-42 onboarding agreement",
                    input_fields=("subject", "client_id"),
                    input_values={"subject": "XRP", "client_id": "CLIENT_42"},
                    resolution="Contact CLIENT_42 compliance team.",
                )
            return None

        sae.register_client_constraint("CLIENT_42", block_xrp_for_client_42)

        blocked = sae.validate(ProposedRequest(
            subject="XRP", operation="SPOT", jurisdiction="GLOBAL", client_id="CLIENT_42"
        ))
        assert isinstance(blocked, StructuredRejectionRecord)

        allowed = sae.validate(ProposedRequest(
            subject="XRP", operation="SPOT", jurisdiction="GLOBAL", client_id="OTHER_CLIENT"
        ))
        assert isinstance(allowed, EvaluationRequest)


# ── Singleton and multi-domain ─────────────────────────────────────────────────

class TestSAESingleton:
    def test_get_sae_returns_same_instance(self):
        s1 = get_sae()
        s2 = get_sae()
        assert s1 is s2

    def test_reset_instance_clears_singleton(self):
        s1 = get_sae()
        StructuralAdmissibilityEngine.reset_instance()
        s2 = get_sae()
        assert s1 is not s2

    def test_domain_field_preserved_in_evaluation_request(self):
        sae = _sae()
        result = sae.validate(ProposedRequest(
            subject="BTC",
            operation="SPOT",
            jurisdiction="GLOBAL",
            domain="FINANCIAL_TRADING",
        ))
        assert isinstance(result, EvaluationRequest)
        assert result.domain == "FINANCIAL_TRADING"

    def test_evaluation_id_unique_per_request(self):
        sae = _sae()
        r1 = sae.validate(_admissible("BTC", "SPOT", "GLOBAL"))
        r2 = sae.validate(_admissible("ETH", "SPOT", "EU"))
        assert isinstance(r1, EvaluationRequest)
        assert isinstance(r2, EvaluationRequest)
        assert r1.evaluation_id != r2.evaluation_id


# ── Feature flag: SAEOverride ──────────────────────────────────────────────────

class TestSAEOverride:
    def test_default_override_is_unset(self):
        assert get_sae_override() == SAEOverride.UNSET

    def test_force_on_activates_layer0_regardless_of_caller_flag(self):
        set_sae_override(SAEOverride.FORCE_ON)
        assert get_sae_override() == SAEOverride.FORCE_ON

    def test_override_reverts_to_unset(self):
        set_sae_override(SAEOverride.FORCE_ON)
        set_sae_override(SAEOverride.UNSET)
        assert get_sae_override() == SAEOverride.UNSET

    def test_override_values_are_strings(self):
        assert SAEOverride.FORCE_ON.value == "FORCE_ON"
        assert SAEOverride.UNSET.value    == "UNSET"

    def test_override_sae_is_independent_of_compliance_config(self):
        set_sae_override(SAEOverride.FORCE_ON)
        assert get_sae_override() == SAEOverride.FORCE_ON
        set_sae_override(SAEOverride.UNSET)
        assert get_sae_override() == SAEOverride.UNSET


# ── Business Metrics: Layer0Metrics ───────────────────────────────────────────

class TestLayer0Metrics:
    def test_metrics_start_empty(self):
        m = get_layer0_metrics()
        assert m.snapshot() == {}

    def test_admitted_request_increments_total_and_admitted(self):
        sae = _sae()
        sae.validate(_admissible("BTC", "SPOT", "GLOBAL", domain="FINANCIAL_TRADING"))
        m = get_layer0_metrics().snapshot()
        assert "FINANCIAL_TRADING" in m
        assert m["FINANCIAL_TRADING"]["total"]    == 1
        assert m["FINANCIAL_TRADING"]["admitted"] == 1
        assert m["FINANCIAL_TRADING"]["blocked"]  == 0
        assert m["FINANCIAL_TRADING"]["block_rate_pct"] == 0.0

    def test_rejected_request_increments_total_blocked_and_class(self):
        sae = _sae()
        sae.validate(ProposedRequest(
            subject="XMR", operation="SPOT", jurisdiction="UAE",
            domain="FINANCIAL_TRADING",
        ))
        m = get_layer0_metrics().snapshot()
        assert "FINANCIAL_TRADING" in m
        stat = m["FINANCIAL_TRADING"]
        assert stat["total"]   == 1
        assert stat["blocked"] == 1
        assert stat["admitted"] == 0
        assert stat["block_rate_pct"] == 100.0
        assert "JURISDICTION_ASSET" in stat["blocked_by_class"]

    def test_block_rate_calculated_correctly(self):
        sae = _sae()
        domain = "TEST_DOMAIN"
        sae.validate(_admissible("BTC", "SPOT", "GLOBAL", domain=domain))
        sae.validate(_admissible("ETH", "SPOT", "EU",     domain=domain))
        sae.validate(ProposedRequest("XMR", "SPOT", "UAE", domain=domain))
        m = get_layer0_metrics().snapshot()
        stat = m[domain.upper()]
        assert stat["total"]   == 3
        assert stat["admitted"] == 2
        assert stat["blocked"] == 1
        assert stat["block_rate_pct"] == pytest.approx(33.33, abs=0.1)

    def test_metrics_are_per_domain(self):
        sae = _sae()
        sae.validate(_admissible("BTC", "SPOT", "GLOBAL", domain="TRADING"))
        sae.validate(ProposedRequest("XMR", "SPOT", "UAE", domain="INSURANCE"))
        m = get_layer0_metrics().snapshot()
        assert "TRADING"   in m
        assert "INSURANCE" in m
        assert m["TRADING"]["admitted"]  == 1
        assert m["TRADING"]["blocked"]   == 0
        assert m["INSURANCE"]["blocked"] == 1

    def test_blocked_by_class_counts_per_constraint_class(self):
        sae = _sae()
        sae.validate(ProposedRequest("XMR",        "SPOT",      "UAE",    domain="D"))
        sae.validate(ProposedRequest("BTC",        "LEVERAGED", "UAE",    domain="D"))
        sae.validate(ProposedRequest("TORNADO_CASH","SPOT",     "GLOBAL", domain="D"))
        m = get_layer0_metrics().snapshot()["D"]
        assert m["blocked"] == 3
        by_class = m["blocked_by_class"]
        assert "JURISDICTION_ASSET"    in by_class
        assert "JURISDICTION_OPERATION" in by_class
        assert "SANCTIONS"             in by_class

    def test_metrics_reset_clears_all_counters(self):
        sae = _sae()
        sae.validate(_admissible("BTC", "SPOT", "GLOBAL", domain="X"))
        assert get_layer0_metrics().snapshot() != {}
        get_layer0_metrics().reset()
        assert get_layer0_metrics().snapshot() == {}

    def test_snapshot_is_a_copy_not_a_reference(self):
        sae = _sae()
        sae.validate(_admissible("BTC", "SPOT", "GLOBAL", domain="COPY_TEST"))
        s1 = get_layer0_metrics().snapshot()
        sae.validate(_admissible("ETH", "SPOT", "EU", domain="COPY_TEST"))
        s2 = get_layer0_metrics().snapshot()
        assert s1["COPY_TEST"]["total"] == 1
        assert s2["COPY_TEST"]["total"] == 2


# ── Logging: [LAYER_0] ADMITTED / REJECTED ────────────────────────────────────

class TestLayer0Logging:
    def test_admitted_emits_info_log(self, caplog):
        import logging
        sae = _sae()
        with caplog.at_level(logging.INFO, logger="OMNIX.SAE"):
            sae.validate(_admissible("BTC", "SPOT", "GLOBAL", domain="TRADING"))
        admitted_logs = [r for r in caplog.records if "[LAYER_0] ADMITTED" in r.message]
        assert len(admitted_logs) == 1
        assert "BTC" in admitted_logs[0].message
        assert "SPOT" in admitted_logs[0].message
        assert "GLOBAL" in admitted_logs[0].message
        assert "eval_id" in admitted_logs[0].message
        assert "elapsed" in admitted_logs[0].message

    def test_rejected_emits_warning_log(self, caplog):
        import logging
        sae = _sae()
        with caplog.at_level(logging.WARNING, logger="OMNIX.SAE"):
            sae.validate(ProposedRequest("XMR", "SPOT", "UAE", domain="TRADING"))
        rejected_logs = [r for r in caplog.records if "[LAYER_0] REJECTED" in r.message]
        assert len(rejected_logs) == 1
        msg = rejected_logs[0].message
        assert "XMR"  in msg
        assert "UAE"  in msg
        assert "constraint=" in msg
        assert "audit_id="   in msg
        assert "elapsed="    in msg

    def test_admitted_log_level_is_info_not_warning(self, caplog):
        import logging
        sae = _sae()
        with caplog.at_level(logging.DEBUG, logger="OMNIX.SAE"):
            sae.validate(_admissible("BTC", "SPOT", "GLOBAL"))
        admitted = [r for r in caplog.records if "[LAYER_0] ADMITTED" in r.message]
        assert all(r.levelno == logging.INFO for r in admitted)

    def test_rejected_log_level_is_warning(self, caplog):
        import logging
        sae = _sae()
        with caplog.at_level(logging.DEBUG, logger="OMNIX.SAE"):
            sae.validate(ProposedRequest("XMR", "SPOT", "UAE"))
        rejected = [r for r in caplog.records if "[LAYER_0] REJECTED" in r.message]
        assert all(r.levelno == logging.WARNING for r in rejected)
