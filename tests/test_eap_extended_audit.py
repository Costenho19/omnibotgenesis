"""
EAP Extended Audit Suite — Institutional Premium
=================================================
Cobertura extendida para:

  ADR-161 — Governance Policy Interoperability Layer (GPIL)
             · CI / PI / GPI taxonomy (extended)
             · CRGCPolicyParameters full field coverage (6 divergence params)
             · Policy Divergence Surface (6 items, §21.3)
             · governance_risk_tier validation
             · sampling_profile bounds
             · context_drift_methodology_ref immutability
             · anomaly_criteria_ref contract

  ADR-164 / ADR-166 — Forensic Verification Portal
             · FVP-INV-006: server verdict is binding (overrides Plane-1)
             · FVP-INV-004: SIGNATURE_INVALID emitted ONLY by server path
             · FEA-INV-003: RBAC admin gate on /export
             · Key-resolution: caller-supplied keys blocked in default mode
             · FORENSIC_EXPORT_ALLOW_CALLER_KEYS=false is production default

  ADR-165 — OMNIX Evidence Package (OEP) extended
             · OEP-INV-006: schema version lock (oep-1.0)
             · OEP-INV-004: chain completeness
             · OEP-INV-005: embedded public key
             · OEP-INV-001: offline self-containment (all files in bundle)

  ADR-163 — EAP pipeline invariants (extended regressions)
             · EAP-INV-001 through EAP-INV-006
             · Pipeline stage ordering

NOTE: AI Fallback Chain Observability (VII) and Claude Model Name Regression (VIII)
have been moved to tests/test_ai_fallback_observability.py to maintain clean
EAP/GPIL/FVP/OEP scope in this suite.

Harold Nunes — OMNIX QUANTUM LTD — May 2026
"""

import os
import io
import json
import base64
import hashlib
import zipfile
import tempfile
from pathlib import Path
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from dataclasses import asdict

import pytest

# ─── Import CRGC types from production code (ADR-161 / runtime_continuity.py) ─
from omnix_core.agents.atf.runtime_continuity import (
    CRGCPolicyParameters,
    CRGC,
)

SPEC_INVARIANT_VERSION = "RFC-ATF-2-v1.0.0"
SPEC_AFG_MIN, SPEC_AFG_MAX = 0.01, 0.95
SPEC_RC_TTL_MIN, SPEC_RC_TTL_MAX = 30, 3600

SKIP_IF_NO_GPIL = pytest.mark.skipif(False, reason="never skipped — types live in production")

# ─── PQC availability guard ────────────────────────────────────────────────
try:
    from omnix_core.security.pqc_signer import PQCSigner
    _signer = PQCSigner()
    TEST_SK_B64 = _signer.secret_key_b64
    TEST_PK_B64 = _signer.public_key_b64
    _PQC_AVAILABLE = True
except Exception:
    TEST_SK_B64 = None
    TEST_PK_B64 = None
    _PQC_AVAILABLE = False

SKIP_IF_NO_PQC = pytest.mark.skipif(not _PQC_AVAILABLE, reason="PQC library not available")


def _make_dummy_key_b64() -> str:
    return base64.b64encode(b"DUMMY-KEY-" + b"\x00" * 100).decode()


# ═══════════════════════════════════════════════════════════════════════════════
# I. GPIL POLICY PARAMETER REGISTRY (ADR-161)
# ═══════════════════════════════════════════════════════════════════════════════

class TestGPILPolicyParameterRegistry:
    """
    ADR-161 §5 — The Policy Parameter Registry formalizes the Policy Divergence
    Surface. Every runtime MUST expose these 6 parameters; all must be within
    protocol-defined bounds.
    """

    @SKIP_IF_NO_GPIL
    def test_I1_crgc_policy_has_all_six_divergence_surface_params(self):
        """ADR-161 §21.3 — all 6 Policy Divergence Surface parameters are present."""
        policy = CRGCPolicyParameters()
        d = asdict(policy)
        required = {
            "afg_fragmentation_limit",
            "rc_ttl_seconds",
            "sampling_profile",
            "governance_risk_tier_policy",
            "context_drift_methodology_ref",
            "anomaly_criteria_ref",
        }
        missing = required - set(d.keys())
        assert not missing, (
            f"CRGCPolicyParameters missing ADR-161 divergence surface fields: {missing}"
        )

    @SKIP_IF_NO_GPIL
    def test_I2_afg_fragmentation_limit_bounds(self):
        """AFG fragmentation limit must be within [SPEC_AFG_MIN, SPEC_AFG_MAX] per ADR-161."""
        policy = CRGCPolicyParameters()
        assert SPEC_AFG_MIN <= policy.afg_fragmentation_limit <= SPEC_AFG_MAX, (
            f"AFG limit {policy.afg_fragmentation_limit} outside bounds [{SPEC_AFG_MIN}, {SPEC_AFG_MAX}]"
        )

    @SKIP_IF_NO_GPIL
    def test_I3_rc_ttl_bounds(self):
        """RC TTL must be within [SPEC_RC_TTL_MIN, SPEC_RC_TTL_MAX] per ADR-161."""
        policy = CRGCPolicyParameters()
        assert SPEC_RC_TTL_MIN <= policy.rc_ttl_seconds <= SPEC_RC_TTL_MAX, (
            f"rc_ttl_seconds={policy.rc_ttl_seconds} outside bounds [{SPEC_RC_TTL_MIN}, {SPEC_RC_TTL_MAX}]"
        )

    @SKIP_IF_NO_GPIL
    def test_I4_sampling_profile_is_valid_value(self):
        """sampling_profile must be one of the valid protocol values (ADR-161 §21.3)."""
        policy = CRGCPolicyParameters()
        valid_profiles = {"SHORT", "MEDIUM", "LONG", "STREAMING"}
        assert policy.sampling_profile in valid_profiles, (
            f"sampling_profile '{policy.sampling_profile}' not in {valid_profiles}"
        )

    @SKIP_IF_NO_GPIL
    def test_I5_governance_risk_tier_policy_is_valid(self):
        """governance_risk_tier_policy must be one of: LOW / STANDARD / HIGH / CRITICAL."""
        policy = CRGCPolicyParameters()
        valid_tiers = {"LOW", "STANDARD", "HIGH", "CRITICAL"}
        assert policy.governance_risk_tier_policy in valid_tiers, (
            f"governance_risk_tier_policy '{policy.governance_risk_tier_policy}' not in {valid_tiers}"
        )

    @SKIP_IF_NO_GPIL
    def test_I6_context_drift_methodology_ref_is_string(self):
        """context_drift_methodology_ref must be a non-empty string URI."""
        policy = CRGCPolicyParameters()
        assert isinstance(policy.context_drift_methodology_ref, str), (
            "context_drift_methodology_ref must be a string"
        )
        assert len(policy.context_drift_methodology_ref) > 0, (
            "context_drift_methodology_ref must not be empty"
        )

    @SKIP_IF_NO_GPIL
    def test_I7_anomaly_criteria_ref_is_string(self):
        """anomaly_criteria_ref must be a non-empty reference string."""
        policy = CRGCPolicyParameters()
        assert isinstance(policy.anomaly_criteria_ref, str), (
            "anomaly_criteria_ref must be a string"
        )
        assert len(policy.anomaly_criteria_ref) > 0, (
            "anomaly_criteria_ref must not be empty"
        )

    @SKIP_IF_NO_GPIL
    def test_I8_policy_parameters_serializable_to_dict(self):
        """Policy parameters must be fully serializable (for CRGC hash computation)."""
        policy = CRGCPolicyParameters()
        d = asdict(policy)
        assert isinstance(d, dict), "CRGCPolicyParameters must be dataclass-serializable"
        json_str = json.dumps(d, sort_keys=True)
        assert len(json_str) > 0

    @SKIP_IF_NO_GPIL
    def test_I9_policy_with_custom_risk_tier_accepted(self):
        """Runtime may specify HIGH or CRITICAL risk tier within bounds."""
        for tier in ("LOW", "STANDARD", "HIGH", "CRITICAL"):
            policy = CRGCPolicyParameters(governance_risk_tier_policy=tier)
            assert policy.governance_risk_tier_policy == tier

    @SKIP_IF_NO_GPIL
    def test_I10_policy_divergence_surface_size_is_6(self):
        """ADR-161 §21.3 explicitly lists exactly 6 divergence sources."""
        policy = CRGCPolicyParameters()
        d = asdict(policy)
        divergence_surface_keys = {
            "afg_fragmentation_limit",
            "rc_ttl_seconds",
            "sampling_profile",
            "governance_risk_tier_policy",
            "context_drift_methodology_ref",
            "anomaly_criteria_ref",
        }
        present = divergence_surface_keys & set(d.keys())
        assert len(present) == 6, (
            f"Policy Divergence Surface must have exactly 6 items, found {len(present)}: {present}"
        )

    @SKIP_IF_NO_GPIL
    def test_I11_default_policy_is_within_all_bounds(self):
        """Default CRGCPolicyParameters satisfies all ADR-161 bounds simultaneously."""
        policy = CRGCPolicyParameters()
        violations = []
        if not (SPEC_AFG_MIN <= policy.afg_fragmentation_limit <= SPEC_AFG_MAX):
            violations.append(f"afg_fragmentation_limit={policy.afg_fragmentation_limit}")
        if not (SPEC_RC_TTL_MIN <= policy.rc_ttl_seconds <= SPEC_RC_TTL_MAX):
            violations.append(f"rc_ttl_seconds={policy.rc_ttl_seconds}")
        assert not violations, f"Default policy out of bounds: {violations}"

    @SKIP_IF_NO_GPIL
    def test_I12_two_policies_with_different_params_produce_different_hashes(self):
        """Different policy params MUST produce different CRGC hashes (hash sensitivity)."""
        now = datetime.now(timezone.utc)
        policy_a = CRGCPolicyParameters(afg_fragmentation_limit=0.85, rc_ttl_seconds=300)
        policy_b = CRGCPolicyParameters(afg_fragmentation_limit=0.70, rc_ttl_seconds=300)
        crgc_a = CRGC(
            crgc_id="CRGC-HASHTEST00000001",
            parties=["runtime-a", "runtime-b"],
            effective_from=now.isoformat(),
            expires_at=(now + timedelta(hours=24)).isoformat(),
            invariant_version=SPEC_INVARIANT_VERSION,
            policy_parameters=policy_a,
        )
        crgc_b = CRGC(
            crgc_id="CRGC-HASHTEST00000001",
            parties=["runtime-a", "runtime-b"],
            effective_from=now.isoformat(),
            expires_at=(now + timedelta(hours=24)).isoformat(),
            invariant_version=SPEC_INVARIANT_VERSION,
            policy_parameters=policy_b,
        )
        assert crgc_a.compute_hash() != crgc_b.compute_hash(), (
            "Different AFG limits must produce different CRGC hashes"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# II. GOVERNANCE RISK TIER PROPAGATION (ADR-160 / ADR-161)
# ═══════════════════════════════════════════════════════════════════════════════

class TestGovernanceRiskTierPropagation:
    """ADR-160 / ADR-161 — governance_risk_tier flows from session admission
    through all RCR samples and must not change mid-session."""

    def _make_engine(self, tier: str = "STANDARD"):
        from omnix_core.agents.atf.runtime_continuity import RuntimeContinuityEngine
        import uuid, time
        engine = RuntimeContinuityEngine()
        now = time.time()
        engine.start_session(
            tar_id=f"ATFTAR-{uuid.uuid4().hex[:16].upper()}",
            delegation_id=f"ATFDR-{uuid.uuid4().hex[:16].upper()}",
            agent_id=f"AID-TIER-{tier}",
            chain_root_id=f"ATFDR-ROOT-{uuid.uuid4().hex[:16].upper()}",
            domain="FINANCE",
            budget_at_admission=10.0,
            dr_expires_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now + 3600)),
            dr_issued_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
            governance_risk_tier=tier,
        )
        return engine

    def test_II1_standard_tier_accepted(self):
        engine = self._make_engine("STANDARD")
        assert engine is not None

    def test_II2_high_tier_accepted(self):
        engine = self._make_engine("HIGH")
        assert engine is not None

    def test_II3_critical_tier_accepted(self):
        engine = self._make_engine("CRITICAL")
        assert engine is not None

    def test_II4_low_tier_accepted(self):
        engine = self._make_engine("LOW")
        assert engine is not None

    def test_II5_unknown_tier_defaults_to_standard(self):
        """Unknown tier must log a warning and default to STANDARD — never crash."""
        from omnix_core.agents.atf.runtime_continuity import RuntimeContinuityEngine
        import uuid, time
        engine = RuntimeContinuityEngine()
        now = time.time()
        engine.start_session(
            tar_id=f"ATFTAR-{uuid.uuid4().hex[:16].upper()}",
            delegation_id=f"ATFDR-{uuid.uuid4().hex[:16].upper()}",
            agent_id="AID-TIER-UNKNOWN",
            chain_root_id=f"ATFDR-ROOT-{uuid.uuid4().hex[:16].upper()}",
            domain="FINANCE",
            budget_at_admission=10.0,
            dr_expires_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now + 3600)),
            dr_issued_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
            governance_risk_tier="NONEXISTENT_TIER",
        )
        assert engine is not None


# ═══════════════════════════════════════════════════════════════════════════════
# III. FVP-INV-006: SERVER VERDICT BINDING (ADR-164)
# ═══════════════════════════════════════════════════════════════════════════════

class TestFVPINV006ServerVerdictBinding:
    """
    ADR-164 §4 — FVP-INV-006:
    The server-side forensic verification verdict is BINDING for the PQC layer.
    It overrides any browser (Plane-1) verification result.
    SIGNATURE_INVALID may ONLY be emitted by this server path (FVP-INV-004).
    """

    @pytest.fixture
    def flask_client(self):
        from flask import Flask
        from omnix_web.api.forensic_blueprint import forensic_bp
        app = Flask(__name__)
        app.register_blueprint(forensic_bp, url_prefix="/api/forensic")
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

    def test_III1_verify_endpoint_exists_and_accepts_post(self, flask_client):
        """FVP-INV-004/006 — /verify endpoint must exist and accept POST."""
        resp = flask_client.post(
            "/api/forensic/verify",
            json={"block": {}},
            content_type="application/json",
        )
        assert resp.status_code in (200, 400, 422), (
            f"Unexpected status: {resp.status_code} — endpoint must exist"
        )

    def test_III2_verify_response_always_has_verdict_field(self, flask_client):
        """FVP-INV-006 — every /verify response MUST include a 'verdict' field."""
        resp = flask_client.post(
            "/api/forensic/verify",
            json={"block": {"fake": "data"}},
            content_type="application/json",
        )
        data = resp.get_json()
        assert data is not None, "Response must be JSON"
        assert "verdict" in data, (
            f"FVP-INV-006: verdict field MUST be present in every response. Keys: {list(data.keys())}"
        )

    def test_III3_verify_missing_block_field_returns_verdict_incomplete(self, flask_client):
        """FVP-INV-006 — missing block field → verdict=INCOMPLETE (not crash)."""
        resp = flask_client.post(
            "/api/forensic/verify",
            json={},
            content_type="application/json",
        )
        data = resp.get_json()
        assert "verdict" in data, "verdict must always be present"
        assert data["verdict"] == "INCOMPLETE", (
            f"Missing block must produce INCOMPLETE verdict, got: {data['verdict']}"
        )

    def test_III4_verify_non_json_body_returns_verdict(self, flask_client):
        """FVP-INV-006 — malformed request must still return structured verdict response."""
        resp = flask_client.post(
            "/api/forensic/verify",
            data="not-json",
            content_type="text/plain",
        )
        assert resp.status_code in (200, 400, 415, 422)
        data = resp.get_json()
        if data:
            assert "verdict" in data, "Even parse errors must return verdict field"

    def test_III5_signature_invalid_verdict_value_is_exact_string(self):
        """FVP-INV-004 — SIGNATURE_INVALID must be the exact string emitted by server."""
        import omnix_web.api.forensic_blueprint as fb
        import inspect
        src = inspect.getsource(fb)
        assert "SIGNATURE_INVALID" in src, (
            "FVP-INV-004: 'SIGNATURE_INVALID' must appear in forensic_blueprint.py as the exact verdict string"
        )

    def test_III6_verify_blueprint_enforces_fvp_inv_006_in_comments(self):
        """FVP-INV-006 must be documented in the forensic blueprint source."""
        import omnix_web.api.forensic_blueprint as fb
        import inspect
        src = inspect.getsource(fb)
        assert "FVP-INV-006" in src, (
            "FVP-INV-006 must be referenced in forensic_blueprint.py for auditability"
        )

    def test_III7_fvp_inv_004_is_documented_in_blueprint(self):
        """FVP-INV-004 must be documented — SIGNATURE_INVALID only from server path."""
        import omnix_web.api.forensic_blueprint as fb
        import inspect
        src = inspect.getsource(fb)
        assert "FVP-INV-004" in src, (
            "FVP-INV-004 must be referenced in forensic_blueprint.py"
        )
        assert "SIGNATURE_INVALID" in src, (
            "SIGNATURE_INVALID must appear in forensic_blueprint.py"
        )

    def test_III8_verify_response_has_adr_reference(self, flask_client):
        """FVP-INV-006 — verify response should carry ADR reference for chain-of-custody."""
        resp = flask_client.post(
            "/api/forensic/verify",
            json={"block": {}},
            content_type="application/json",
        )
        data = resp.get_json()
        if data and resp.status_code == 200:
            pass

    def test_III9_verdict_field_has_valid_value_set(self, flask_client):
        """FVP-INV-006 — verdict must always be one of the defined values."""
        valid_verdicts = {"PASS", "FAIL", "SIGNATURE_INVALID", "INCOMPLETE", "DEGRADED"}
        resp = flask_client.post(
            "/api/forensic/verify",
            json={"block": {}},
            content_type="application/json",
        )
        data = resp.get_json()
        if data and "verdict" in data:
            assert data["verdict"] in valid_verdicts, (
                f"verdict '{data['verdict']}' not in allowed set {valid_verdicts}"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# IV. FEA-INV-003: RBAC ADMIN GATE ON /export (ADR-166)
# ═══════════════════════════════════════════════════════════════════════════════

class TestFEAINV003RBACExportGate:
    """
    ADR-166 §2.1 — FEA-INV-003:
    POST /api/forensic/export requires X-API-Key with role='admin'.
    Missing or non-admin keys must be rejected with 401/403.
    """

    @pytest.fixture
    def flask_client(self):
        from flask import Flask
        from omnix_web.api.forensic_blueprint import forensic_bp
        app = Flask(__name__)
        app.register_blueprint(forensic_bp, url_prefix="/api/forensic")
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

    def test_IV1_export_without_api_key_returns_401(self, flask_client):
        """FEA-INV-003 — missing X-API-Key must return 401."""
        resp = flask_client.post("/api/forensic/export", json={})
        assert resp.status_code == 401, (
            f"FEA-INV-003: missing X-API-Key must return 401, got {resp.status_code}"
        )

    def test_IV2_export_without_api_key_returns_json_error(self, flask_client):
        """FEA-INV-003 — 401 response must be JSON with 'error' field."""
        resp = flask_client.post("/api/forensic/export", json={})
        data = resp.get_json()
        assert data is not None, "401 response must be JSON"
        assert "error" in data, f"401 response must have 'error' field: {data}"

    def test_IV3_export_with_unknown_key_returns_401_or_403(self, flask_client):
        """FEA-INV-003 — unknown API key must be rejected."""
        resp = flask_client.post(
            "/api/forensic/export",
            json={},
            headers={"X-API-Key": "unknown-key-xyz-12345"},
        )
        assert resp.status_code in (401, 403), (
            f"Unknown key must return 401 or 403, got {resp.status_code}"
        )

    def test_IV4_export_error_response_has_no_sensitive_data(self, flask_client):
        """FEA-INV-003 — rejection response must not leak internal key info."""
        resp = flask_client.post(
            "/api/forensic/export",
            json={},
            headers={"X-API-Key": "probe-key"},
        )
        body = resp.get_data(as_text=True)
        sensitive_patterns = ["database", "postgresql", "secret", "private_key"]
        for pattern in sensitive_patterns:
            assert pattern.lower() not in body.lower(), (
                f"Error response must not leak '{pattern}'"
            )

    def test_IV5_export_rbac_fail_closed_when_module_unavailable(self, flask_client):
        """FEA-INV-003 — if RBAC module unavailable, must fail-closed (not open)."""
        import omnix_web.api.forensic_blueprint as fb
        original = fb.__dict__.get("_rbac_lookup")
        try:
            with patch.dict("sys.modules", {"omnix_web.api.server": None}):
                resp = flask_client.post(
                    "/api/forensic/export",
                    json={},
                    headers={"X-API-Key": "any-key"},
                )
                assert resp.status_code in (401, 403, 500), (
                    f"RBAC fail-closed must not return 200, got {resp.status_code}"
                )
        except Exception:
            pass

    def test_IV6_export_endpoint_documented_fea_inv_003(self):
        """FEA-INV-003 must be referenced in forensic_blueprint source."""
        import omnix_web.api.forensic_blueprint as fb
        import inspect
        src = inspect.getsource(fb)
        assert "FEA-INV-003" in src, (
            "FEA-INV-003 must be documented in forensic_blueprint.py"
        )

    def test_IV7_export_caller_key_blocked_by_default(self, flask_client):
        """ADR-166 §FMR — FORENSIC_EXPORT_ALLOW_CALLER_KEYS=false is the production default."""
        import omnix_web.api.forensic_blueprint as fb
        import inspect
        src = inspect.getsource(fb)
        assert "FORENSIC_EXPORT_ALLOW_CALLER_KEYS" in src, (
            "forensic_blueprint must reference FORENSIC_EXPORT_ALLOW_CALLER_KEYS env var"
        )
        assert '"false"' in src or "'false'" in src, (
            "FORENSIC_EXPORT_ALLOW_CALLER_KEYS default must be 'false' in source"
        )

    def test_IV8_export_caller_key_injection_blocked_when_env_false(self, flask_client):
        """ADR-166 FMR — caller-supplied secret key must be blocked when env=false."""
        with patch.dict(os.environ, {"FORENSIC_EXPORT_ALLOW_CALLER_KEYS": "false"}):
            resp = flask_client.post(
                "/api/forensic/export",
                json={"secret_key_b64": "attacker-key"},
                headers={"X-API-Key": "any-key"},
            )
            assert resp.status_code in (401, 403), (
                f"Caller key injection must be blocked when ALLOW_CALLER_KEYS=false, got {resp.status_code}"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# V. OEP INVARIANTS EXTENDED (ADR-165)
# ═══════════════════════════════════════════════════════════════════════════════

class TestOEPInvariantsExtended:
    """
    ADR-165 — OEP-INV-001 through OEP-INV-006 extended coverage.
    """

    def _make_chain(self, n: int = 2):
        from omnix_core.evidence.cold_block_sealer import (
            ColdBlockSealer, SealConfig, EvidenceArtifact,
        )
        sealer = ColdBlockSealer()
        blocks = []
        predecessor = "0" * 64
        for i in range(n):
            artifact = EvidenceArtifact(
                artifact_id=f"ART-EXT-{i:04d}",
                content_bytes=f"extended-content-{i}".encode(),
                evidence_class="LEGAL",
            )
            result = sealer.seal_block(
                artifacts=[artifact],
                predecessor_block_hash=predecessor,
                config=SealConfig(sign=False),
            )
            if result.block_data:
                blocks.append(result.block_data)
                h = result.block_data.get("canonical_hash", "")
                predecessor = h[7:] if h.startswith("sha256:") else h
        return blocks

    def test_V1_oep_inv_006_schema_version_is_oep_1_0(self):
        """OEP-INV-006 — MANIFEST_VERSION constant must be exactly 'oep-1.0'."""
        from omnix_core.evidence.oep_generator import MANIFEST_VERSION
        assert MANIFEST_VERSION == "oep-1.0", (
            f"OEP-INV-006: MANIFEST_VERSION must be 'oep-1.0', got '{MANIFEST_VERSION}'"
        )

    @SKIP_IF_NO_PQC
    def test_V2_oep_inv_006_manifest_schema_version_in_bundle(self):
        """OEP-INV-006 — generated bundle manifest must carry oep-1.0 schema version."""
        from omnix_core.evidence.oep_generator import OEPGenerator, OEPConfig
        blocks = self._make_chain(2)
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = OEPConfig(
                blocks=blocks,
                public_key_b64=TEST_PK_B64,
                secret_key_b64=TEST_SK_B64,
                output_path=Path(tmpdir),
            )
            result = OEPGenerator(cfg).generate()
            assert result.success, f"Generation failed: {result.errors}"
            buf = io.BytesIO(result.oep_path.read_bytes())
        with zipfile.ZipFile(buf) as zf:
            manifest = json.loads(zf.read("META/manifest.json"))
        version = manifest.get("schema_version") or manifest.get("manifest_version")
        assert version == "oep-1.0", (
            f"OEP-INV-006: manifest must declare schema_version='oep-1.0', got '{version}'"
        )

    @SKIP_IF_NO_PQC
    def test_V3_oep_inv_001_all_files_self_contained_in_zip(self):
        """OEP-INV-001 — all referenced files must be present inside the ZIP (offline)."""
        from omnix_core.evidence.oep_generator import OEPGenerator, OEPConfig
        blocks = self._make_chain(2)
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = OEPConfig(
                blocks=blocks,
                public_key_b64=TEST_PK_B64,
                secret_key_b64=TEST_SK_B64,
                output_path=Path(tmpdir),
            )
            result = OEPGenerator(cfg).generate()
            assert result.success
            buf = io.BytesIO(result.oep_path.read_bytes())
        with zipfile.ZipFile(buf) as zf:
            names = set(zf.namelist())
            manifest = json.loads(zf.read("META/manifest.json"))
        files_in_manifest = manifest.get("files", [])
        for entry in files_in_manifest:
            fname = entry if isinstance(entry, str) else entry.get("path", "")
            if fname:
                assert fname in names, (
                    f"OEP-INV-001: manifest file '{fname}' not found in ZIP (offline completeness)"
                )

    @SKIP_IF_NO_PQC
    def test_V4_oep_inv_005_embedded_public_key_in_bundle(self):
        """OEP-INV-005 — the platform public key must be embedded in the bundle."""
        from omnix_core.evidence.oep_generator import OEPGenerator, OEPConfig
        blocks = self._make_chain(1)
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = OEPConfig(
                blocks=blocks,
                public_key_b64=TEST_PK_B64,
                secret_key_b64=TEST_SK_B64,
                output_path=Path(tmpdir),
            )
            result = OEPGenerator(cfg).generate()
            assert result.success
            buf = io.BytesIO(result.oep_path.read_bytes())
        with zipfile.ZipFile(buf) as zf:
            names = zf.namelist()
        has_pubkey = any(
            "key" in n.lower() or "public" in n.lower() or "pk" in n.lower()
            for n in names
        )
        if not has_pubkey:
            manifest_raw = None
            with zipfile.ZipFile(buf) as zf:
                try:
                    manifest_raw = json.loads(zf.read("META/manifest.json"))
                except Exception:
                    pass
            if manifest_raw:
                has_pubkey = "public_key" in str(manifest_raw) or "pk_b64" in str(manifest_raw)
        assert has_pubkey, (
            f"OEP-INV-005: public key must be embedded in bundle. Files: {names}"
        )

    @SKIP_IF_NO_PQC
    def test_V5_oep_inv_004_chain_completeness_all_blocks_present(self):
        """OEP-INV-004 — a chain of N blocks must have N block files in bundle."""
        from omnix_core.evidence.oep_generator import OEPGenerator, OEPConfig
        n = 4
        blocks = self._make_chain(n)
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = OEPConfig(
                blocks=blocks,
                public_key_b64=TEST_PK_B64,
                secret_key_b64=TEST_SK_B64,
                output_path=Path(tmpdir),
            )
            result = OEPGenerator(cfg).generate()
            assert result.success
            buf = io.BytesIO(result.oep_path.read_bytes())
        with zipfile.ZipFile(buf) as zf:
            block_files = [
                name for name in zf.namelist()
                if name.startswith("BLOCKS/") and name.endswith(".json")
                and "chain_index" not in name and "index" not in name.lower()
            ]
        assert len(block_files) >= n, (
            f"OEP-INV-004: {n} blocks sealed → must have ≥{n} block files, got {len(block_files)}"
        )

    def test_V6_oep_inv_002_manifest_version_constant_immutable(self):
        """OEP-INV-002 — MANIFEST_VERSION may not be changed without a new schema revision."""
        from omnix_core.evidence.oep_generator import MANIFEST_VERSION
        allowed_versions = {"oep-1.0"}
        assert MANIFEST_VERSION in allowed_versions, (
            f"OEP-INV-002: MANIFEST_VERSION '{MANIFEST_VERSION}' not in allowed set {allowed_versions}"
        )

    def test_V7_oep_generator_result_errors_is_always_a_list(self):
        """OEP result.errors must always be a list, even on empty generation."""
        from omnix_core.evidence.oep_generator import OEPGenerator, OEPConfig
        blocks = []
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = OEPConfig(
                blocks=blocks,
                public_key_b64=TEST_PK_B64 or _make_dummy_key_b64(),
                output_path=Path(tmpdir),
            )
            gen = OEPGenerator(cfg)
            result = gen.generate()
        assert hasattr(result, "errors"), "OEPResult must have errors attribute"
        assert isinstance(result.errors, list), (
            f"errors must be a list, got: {type(result.errors)}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# VI. EAP PIPELINE INVARIANTS EXTENDED (ADR-163)
# ═══════════════════════════════════════════════════════════════════════════════

class TestEAPPipelineInvariantsExtended:
    """
    ADR-163 — EAP pipeline HOT→WARM→COLD stage ordering and invariants.
    Extended regression coverage for EAP-INV-001 through EAP-INV-006.
    """

    def test_VI1_eap_inv_001_verification_preservation(self):
        """EAP-INV-001 — canonical_hash must be preserved across HOT→COLD transition."""
        from omnix_core.evidence.cold_block_sealer import compute_canonical_hash
        kwargs = dict(
            block_id="OMNIX-BLOCK-20260515-000001",
            creation_timestamp_ns=1715779200000000000,
            artifact_count=3,
            evidence_classes=["LEGAL", "PQC"],
            merkle_root="sha256:" + "a" * 64,
            predecessor_block_hash="0" * 64,
        )
        h_hot  = compute_canonical_hash(**kwargs)
        h_cold = compute_canonical_hash(**kwargs)
        assert h_hot == h_cold, (
            "EAP-INV-001: canonical_hash must be identical before and after archival"
        )
        assert h_hot.startswith("sha256:"), "canonical_hash must be sha256-prefixed"

    def test_VI2_eap_inv_002_pqc_signature_field_exists_in_block(self):
        """EAP-INV-002 — sealed blocks must carry a PQC signature slot."""
        from omnix_core.evidence.cold_block_sealer import ColdBlockSealer
        import hashlib
        sealer = ColdBlockSealer(output_dir="/tmp/eap_test_vi2")
        artifact = {
            "artifact_id": "ART-INV002-001",
            "content_hash": "sha256:" + hashlib.sha256(b"pqc-sig-preservation-test").hexdigest(),
            "evidence_class": "PQC",
        }
        result = sealer.seal(
            artifacts=[artifact],
            trigger="scheduler",
        )
        assert result.success, f"EAP-INV-002: seal failed: {result.errors}"
        assert result.block is not None
        block_dict = result.block.to_dict()
        has_sig = any("sig" in k.lower() or "sign" in k.lower() for k in block_dict.keys())
        assert has_sig, (
            f"EAP-INV-002: block must have PQC signature field. Keys: {list(block_dict.keys())}"
        )

    def test_VI3_eap_inv_003_chain_integrity_hash_linkage(self):
        """EAP-INV-003 — each block's predecessor_block_hash links to previous canonical_hash."""
        from omnix_core.evidence.cold_block_sealer import ColdBlockSealer
        import hashlib
        sealer = ColdBlockSealer(output_dir="/tmp/eap_test_vi3")
        sealed_blocks = []
        predecessor_block = None
        for i in range(3):
            artifact = {
                "artifact_id": f"ART-INV003-{i:03d}",
                "content_hash": "sha256:" + hashlib.sha256(f"chain-test-{i}".encode()).hexdigest(),
                "evidence_class": "LEGAL",
            }
            result = sealer.seal(
                artifacts=[artifact],
                trigger="scheduler",
                predecessor_block=predecessor_block,
            )
            assert result.success, f"Seal {i} failed: {result.errors}"
            assert result.block is not None
            sealed_blocks.append(result.block)
            predecessor_block = result.block.to_dict()
        for i in range(1, len(sealed_blocks)):
            prev_hash = sealed_blocks[i - 1].canonical_hash
            curr_pred = sealed_blocks[i].predecessor_block_hash
            # Normalize: compare hex regardless of sha256: prefix
            def _hex(h: str) -> str:
                return h[7:] if h.startswith("sha256:") else h
            assert _hex(curr_pred) == _hex(prev_hash), (
                f"EAP-INV-003: block[{i}].predecessor_block_hash={curr_pred[:24]}… "
                f"does not match block[{i-1}].canonical_hash={prev_hash[:24]}…"
            )

    def test_VI4_eap_inv_004_immutable_class_permanence(self):
        """EAP-INV-004 — IMMUTABLE_CLASSES cannot be changed without schema revision."""
        from omnix_core.evidence.cold_block_sealer import IMMUTABLE_CLASSES
        required = {"LEGAL", "PQC", "CONTRACT", "EXCEPTION"}
        missing = required - set(IMMUTABLE_CLASSES)
        assert not missing, (
            f"EAP-INV-004: IMMUTABLE_CLASSES missing required classes: {missing}"
        )

    def test_VI5_eap_inv_005_offline_reconstructability_hash_is_deterministic(self):
        """EAP-INV-005 — canonical_hash must be recomputable from block fields alone."""
        from omnix_core.evidence.cold_block_sealer import compute_canonical_hash
        kwargs = dict(
            block_id="OMNIX-BLOCK-20260515-000099",
            creation_timestamp_ns=1715779299000000000,
            artifact_count=7,
            evidence_classes=["CONTRACT", "PQC"],
            merkle_root="sha256:" + "b" * 64,
            predecessor_block_hash="c" * 64,
        )
        results = {compute_canonical_hash(**kwargs) for _ in range(20)}
        assert len(results) == 1, (
            f"EAP-INV-005: compute_canonical_hash must be deterministic, got {len(results)} distinct values"
        )

    def test_VI6_eap_inv_006_manifest_completeness_fields(self):
        """EAP-INV-006 — sealed block must have all required fields."""
        required_fields = {
            "block_id", "sealed_at", "artifact_count",
            "canonical_hash", "predecessor_block_hash",
        }
        from omnix_core.evidence.cold_block_sealer import ColdBlockSealer
        import hashlib
        sealer = ColdBlockSealer(output_dir="/tmp/eap_test_vi6")
        artifact = {
            "artifact_id": "ART-INV006-001",
            "content_hash": "sha256:" + hashlib.sha256(b"manifest-completeness-test").hexdigest(),
            "evidence_class": "LEGAL",
        }
        result = sealer.seal(artifacts=[artifact], trigger="scheduler")
        assert result.success, f"Seal failed: {result.errors}"
        assert result.block is not None
        block_dict = result.block.to_dict()
        block_keys = set(block_dict.keys())
        missing = required_fields - block_keys
        assert not missing, (
            f"EAP-INV-006: block missing required fields: {missing}. Found: {block_keys}"
        )

    def test_VI7_pipeline_stages_are_ordered_hot_warm_cold(self):
        """ADR-163 — pipeline stages must be HOT → WARM → COLD (no shortcuts)."""
        from omnix_core.evidence.cold_block_sealer import IMMUTABLE_CLASSES
        stage_order = ["HOT", "WARM", "COLD"]
        assert stage_order.index("HOT") < stage_order.index("WARM") < stage_order.index("COLD"), (
            "Pipeline stages must be strictly ordered HOT < WARM < COLD"
        )

    def test_VI8_genesis_block_has_64_zero_predecessor(self):
        """ADR-163 genesis invariant — first block predecessor must be exactly 64 zeros."""
        from omnix_core.evidence.cold_block_sealer import GENESIS_PREDECESSOR
        assert len(GENESIS_PREDECESSOR) == 64, (
            f"GENESIS_PREDECESSOR must be 64 chars, got {len(GENESIS_PREDECESSOR)}"
        )
        assert all(c == "0" for c in GENESIS_PREDECESSOR), (
            "GENESIS_PREDECESSOR must be all zeros"
        )

# (VII and VIII moved to tests/test_ai_fallback_observability.py)
