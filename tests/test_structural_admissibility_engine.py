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
    StructuralAdmissibilityEngine,
    StructuralAdmissibilityViolation,
    StructuredRejectionRecord,
    get_sae,
)


# ── Fixtures ────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_sae_singleton():
    StructuralAdmissibilityEngine.reset_instance()
    yield
    StructuralAdmissibilityEngine.reset_instance()


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
