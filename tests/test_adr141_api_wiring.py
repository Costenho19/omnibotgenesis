"""
ADR-141 — Module API Wiring Test Suite

Validates that all four governance modules are correctly wired to their
API endpoints and that the UDCL CAG Layer 0d integration works.

Modules tested:
  OscillationInsightEngine  → GET /api/analytics/oscillation          (ADR-134)
  AnomalyResponseEngine     → /api/governance/anomaly/*               (ADR-129)
  Execution Integrity Layer → /api/governance/execution/*             (ADR-131)
  Context Admission Gate    → UDCL Layer 0d via cag_enabled=true      (ADR-050)

Groups:
  T01–T10  Oscillation API endpoint (public, no auth)
  T11–T20  Anomaly Response API endpoints (authenticated)
  T21–T30  Execution Integrity API endpoints (authenticated)
  T31–T40  UDCL CAG Layer 0d integration
  T41–T45  ADR-141 schema/catalog verification
"""

import os
import sys
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")

# Shared mock client used by all authenticated-endpoint tests
_MOCK_CLIENT = {"client_id": "adr141-test-client", "key_expires_in_days": None}


# ─────────────────────────────────────────────────────────────────────────────
# IMPORTANT: server.py imports gov_blueprint as `from api.gov_blueprint import …`
# so the module is registered in sys.modules under the key "api.gov_blueprint",
# NOT "omnix_web.api.gov_blueprint".  All patch() calls must use that key.
# ─────────────────────────────────────────────────────────────────────────────
_BP_PATH = "api.gov_blueprint"


@pytest.fixture(autouse=True)
def _clear_brute_force_store():
    """
    Clear the in-memory brute-force store before (and after) each test.

    _brute_force_store is a module-level dict in gov_blueprint that
    persists for the entire pytest session.  Previous failed-auth attempts
    push 127.0.0.1 past _BRUTE_FORCE_MAX=5, causing every subsequent
    request to return 429 before the endpoint logic runs.
    """
    import sys
    bp = sys.modules.get(_BP_PATH)
    if bp and hasattr(bp, "_brute_force_store"):
        bp._brute_force_store.clear()
    yield
    bp = sys.modules.get(_BP_PATH)
    if bp and hasattr(bp, "_brute_force_store"):
        bp._brute_force_store.clear()


@contextmanager
def _bypass_security():
    """
    Bypass all IP/rate-limit security checks for the Flask test client.

    Patches the four security gate functions in the correct module path
    ("api.gov_blueprint" — how server.py imports it).
    """
    with patch(f"{_BP_PATH}._is_ip_blocked",          return_value=False), \
         patch(f"{_BP_PATH}._is_brute_force_locked",  return_value=False), \
         patch(f"{_BP_PATH}._is_client_rate_limited", return_value=False), \
         patch(f"{_BP_PATH}._record_failed_auth",     return_value=None):
        yield


@contextmanager
def _auth_bypass():
    """Bypass auth + security together."""
    with _bypass_security(), \
         patch(f"{_BP_PATH}._require_auth",
               return_value=(_MOCK_CLIENT, None)):
        yield


# ── Flask test client setup ───────────────────────────────────────────────────

@pytest.fixture(scope="module")
def flask_app():
    """Create Flask test application."""
    try:
        from omnix_web.api.server import app
        app.config["TESTING"] = True
        return app
    except Exception:
        pytest.skip("Flask app not importable in this environment")


@pytest.fixture(scope="module")
def client(flask_app):
    return flask_app.test_client()


# ── T01–T10: Oscillation API ──────────────────────────────────────────────────

class TestOscillationAPI:
    """GET /api/analytics/oscillation — ADR-134. Public endpoint."""

    def _mock_oie(self):
        return (
            patch("omnix_core.governance.oscillation_insight.OscillationInsightEngine"
                  "._fetch_weekly_windows", return_value=[]),
            patch("omnix_core.governance.oscillation_insight.OscillationInsightEngine"
                  "._fetch_latency_by_decision_type", return_value={}),
        )

    def test_T01_oscillation_endpoint_exists(self, client):
        """T01: Endpoint returns a response (not 404/405)."""
        p1, p2 = self._mock_oie()
        with p1, p2:
            resp = client.get("/api/analytics/oscillation")
        assert resp.status_code not in (404, 405)

    def test_T02_oscillation_returns_json(self, client):
        """T02: Response is JSON."""
        p1, p2 = self._mock_oie()
        with p1, p2:
            resp = client.get("/api/analytics/oscillation")
        assert resp.content_type.startswith("application/json")

    def test_T03_oscillation_adr_header(self, client):
        """T03: Response includes X-OMNIX-ADR: ADR-134 header."""
        p1, p2 = self._mock_oie()
        with p1, p2:
            resp = client.get("/api/analytics/oscillation")
        assert resp.headers.get("X-OMNIX-ADR") == "ADR-134"

    def test_T04_oscillation_cache_control_header(self, client):
        """T04: Cache-Control header prevents caching."""
        p1, p2 = self._mock_oie()
        with p1, p2:
            resp = client.get("/api/analytics/oscillation")
        cc = resp.headers.get("Cache-Control", "")
        assert "no-cache" in cc or "no-store" in cc

    def test_T05_oscillation_invalid_num_weeks_returns_400(self, client):
        """T05: num_weeks outside 1–26 → 400."""
        resp = client.get("/api/analytics/oscillation?num_weeks=99")
        assert resp.status_code == 400
        data = resp.get_json()
        assert "num_weeks" in str(data.get("error", "")).lower()

    def test_T06_oscillation_num_weeks_zero_returns_400(self, client):
        """T06: num_weeks=0 → 400."""
        resp = client.get("/api/analytics/oscillation?num_weeks=0")
        assert resp.status_code == 400

    def test_T07_oscillation_invalid_view_returns_400(self, client):
        """T07: Invalid view parameter → 400."""
        resp = client.get("/api/analytics/oscillation?view=bogus_view")
        assert resp.status_code == 400
        data = resp.get_json()
        assert "view" in str(data.get("error", "")).lower()

    def test_T08_oscillation_valid_views_accepted(self, client):
        """T08: All 5 valid view values accepted without 400."""
        valid_views = ["full", "profile", "phases", "asymmetry", "dampening"]
        p1, p2 = self._mock_oie()
        with p1, p2:
            for v in valid_views:
                resp = client.get(f"/api/analytics/oscillation?view={v}")
                assert resp.status_code in (200, 503), (
                    f"view={v} returned unexpected {resp.status_code}"
                )

    def test_T09_oscillation_no_auth_required(self, client):
        """T09: No X-API-Key required (public endpoint)."""
        p1, p2 = self._mock_oie()
        with p1, p2:
            resp = client.get("/api/analytics/oscillation")
        assert resp.status_code not in (401, 403)

    def test_T10_oscillation_db_error_returns_503(self, client):
        """T10: DB error → 503, not 500 (fail-safe)."""
        with patch(
            "omnix_core.governance.oscillation_insight.OscillationInsightEngine.oscillation_report",
            side_effect=RuntimeError("DB connection failed"),
        ):
            resp = client.get("/api/analytics/oscillation")
        assert resp.status_code == 503


# ── T11–T20: Anomaly Response API ─────────────────────────────────────────────

class TestAnomalyResponseAPI:
    """POST /api/governance/anomaly/* — ADR-129. Authenticated endpoints."""

    def test_T11_anomaly_response_requires_auth(self, client):
        """T11: POST /anomaly/response without API key → 401 (or 429 from rate limit)."""
        with _bypass_security():
            resp = client.post("/api/governance/anomaly/response", json={}, headers={})
        assert resp.status_code in (401, 403)

    def test_T12_anomaly_active_requires_auth(self, client):
        """T12: GET /anomaly/active without API key → 401."""
        with _bypass_security():
            resp = client.get("/api/governance/anomaly/active")
        assert resp.status_code in (401, 403)

    def test_T13_anomaly_summary_requires_auth(self, client):
        """T13: GET /anomaly/summary without API key → 401."""
        with _bypass_security():
            resp = client.get("/api/governance/anomaly/summary")
        assert resp.status_code in (401, 403)

    def test_T14_anomaly_history_requires_auth(self, client):
        """T14: GET /anomaly/history without API key → 401."""
        with _bypass_security():
            resp = client.get("/api/governance/anomaly/history")
        assert resp.status_code in (401, 403)

    def test_T15_anomaly_acknowledge_requires_auth(self, client):
        """T15: POST /anomaly/<id>/acknowledge without API key → 401."""
        with _bypass_security():
            resp = client.post("/api/governance/anomaly/test-rec-id/acknowledge")
        assert resp.status_code in (401, 403)

    def test_T16_anomaly_resolve_requires_auth(self, client):
        """T16: POST /anomaly/<id>/resolve without API key → 401."""
        with _bypass_security():
            resp = client.post("/api/governance/anomaly/test-rec-id/resolve")
        assert resp.status_code in (401, 403)

    def test_T17_anomaly_response_returns_adr_header(self, client):
        """T17: Anomaly response endpoint returns X-OMNIX-ADR: ADR-129."""
        mock_result = {
            "domain": None, "available": True,
            "anomalies": {"available": True, "anomalies": []},
            "recommendations": [], "new_logged": 0, "active_count": 0,
            "overall_severity": "NONE", "generated_at": "2026-05-07T00:00:00Z",
        }
        with _auth_bypass(), \
             patch("omnix_web.api.gov_blueprint._get_anomaly_engine") as mock_ef:
            mock_e = MagicMock()
            mock_e.full_response_cycle.return_value = mock_result
            mock_ef.return_value = mock_e
            resp = client.post("/api/governance/anomaly/response", json={})
        assert resp.headers.get("X-OMNIX-ADR") == "ADR-129"

    def test_T18_anomaly_active_returns_count_field(self, client):
        """T18: GET /anomaly/active includes count field."""
        with _auth_bypass(), \
             patch("omnix_web.api.gov_blueprint._get_anomaly_engine") as mock_ef:
            mock_e = MagicMock()
            mock_e.get_active.return_value = []
            mock_ef.return_value = mock_e
            resp = client.get("/api/governance/anomaly/active")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "count" in data
        assert "recommendations" in data

    def test_T19_anomaly_acknowledge_invalid_id_returns_400(self, client):
        """T19: Acknowledge with rec_id > 64 chars → 400."""
        long_id = "x" * 65
        with _auth_bypass():
            resp = client.post(f"/api/governance/anomaly/{long_id}/acknowledge")
        assert resp.status_code == 400

    def test_T20_anomaly_resolve_not_found_returns_404(self, client):
        """T20: Resolve returns 404 when recommendation not found."""
        with _auth_bypass(), \
             patch("omnix_web.api.gov_blueprint._get_anomaly_engine") as mock_ef:
            mock_e = MagicMock()
            mock_e.resolve.return_value = False
            mock_ef.return_value = mock_e
            resp = client.post("/api/governance/anomaly/nonexistent-rec/resolve", json={})
        assert resp.status_code == 404


# ── T21–T30: Execution Integrity API ─────────────────────────────────────────

class TestExecutionIntegrityAPI:
    """POST/GET /api/governance/execution/* — ADR-131. Authenticated endpoints."""

    def test_T21_execution_receipts_list_requires_auth(self, client):
        """T21: GET /execution/receipts without API key → 401."""
        with _bypass_security():
            resp = client.get("/api/governance/execution/receipts")
        assert resp.status_code in (401, 403)

    def test_T22_execution_receipt_get_requires_auth(self, client):
        """T22: GET /execution/receipts/<id> without API key → 401."""
        with _bypass_security():
            resp = client.get("/api/governance/execution/receipts/test-order-id")
        assert resp.status_code in (401, 403)

    def test_T23_execution_intent_requires_auth(self, client):
        """T23: POST /execution/intent without API key → 401."""
        with _bypass_security():
            resp = client.post("/api/governance/execution/intent", json={})
        assert resp.status_code in (401, 403)

    def test_T24_execution_intent_missing_fields_returns_400(self, client):
        """T24: Intent without required fields → 400."""
        with _auth_bypass():
            resp = client.post(
                "/api/governance/execution/intent",
                json={"order_id": "ORD-001"},
                content_type="application/json",
            )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "Missing required fields" in str(data.get("error", ""))

    def test_T25_execution_intent_invalid_side_returns_400(self, client):
        """T25: Intent with invalid side → 400."""
        body = {
            "order_id":            "ORD-001",
            "decision_receipt_id": "REC-001",
            "symbol":              "BTC-USD",
            "side":                "LONG",
            "size_usd":            10000.0,
        }
        with _auth_bypass():
            resp = client.post(
                "/api/governance/execution/intent",
                json=body,
                content_type="application/json",
            )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "BUY" in str(data.get("error", "")) or "SELL" in str(data.get("error", ""))

    def test_T26_execution_intent_requires_json(self, client):
        """T26: Intent without Content-Type: application/json → 400."""
        with _auth_bypass():
            resp = client.post("/api/governance/execution/intent", data="not-json")
        assert resp.status_code == 400

    def test_T27_execution_receipts_invalid_status_returns_400(self, client):
        """T27: List with invalid status filter → 400."""
        with _auth_bypass():
            resp = client.get("/api/governance/execution/receipts?status=INVALID_STATUS")
        assert resp.status_code == 400

    def test_T28_execution_receipt_get_invalid_id_returns_400(self, client):
        """T28: Get receipt with order_id > 128 chars → 400."""
        long_id = "x" * 129
        with _auth_bypass():
            resp = client.get(f"/api/governance/execution/receipts/{long_id}")
        assert resp.status_code == 400

    def test_T29_execution_intent_adr_header(self, client):
        """T29: Successful intent log returns X-OMNIX-ADR: ADR-131 and 201."""
        body = {
            "order_id":            "ORD-ADR131-TEST",
            "decision_receipt_id": "REC-TEST-001",
            "symbol":              "ETH-USD",
            "side":                "BUY",
            "size_usd":            5000.0,
        }
        with _auth_bypass(), \
             patch(f"{_BP_PATH}._get_execution_receipt_engine") as mock_factory:
            mock_engine = MagicMock()
            mock_engine.log_intent.return_value = "test-receipt-id"
            mock_factory.return_value = mock_engine
            resp = client.post(
                "/api/governance/execution/intent",
                json=body,
                content_type="application/json",
            )
        assert resp.status_code == 201
        assert resp.headers.get("X-OMNIX-ADR") == "ADR-131"

    def test_T30_execution_intent_invariant_message_on_failure(self, client):
        """T30: On engine failure, intent endpoint returns 503 with ADR-131 message."""
        body = {
            "order_id":            "ORD-FAIL",
            "decision_receipt_id": "REC-FAIL",
            "symbol":              "BTC-USD",
            "side":                "SELL",
            "size_usd":            1000.0,
        }
        with _auth_bypass(), \
             patch("omnix_web.api.omnix_engine.execution_receipt"
                   ".ExecutionReceiptRegistry",
                   side_effect=RuntimeError("DB down")):
            resp = client.post(
                "/api/governance/execution/intent",
                json=body,
                content_type="application/json",
            )
        assert resp.status_code == 503
        data = resp.get_json()
        assert data.get("intent_logged") is False
        assert "ADR-131" in str(data.get("error", ""))


# ── T31–T40: UDCL CAG Layer 0d integration ────────────────────────────────────

class TestUDCLCagIntegration:
    """UDCL cag_enabled=True → Layer 0d runs — ADR-050 + ADR-138."""

    def _make_udcl(self):
        from omnix_core.governance.unified_control_layer import UnifiedDecisionControlLayer
        return UnifiedDecisionControlLayer(MagicMock(), MagicMock())

    def test_T31_udcl_has_cag_enabled_parameter(self):
        """T31: UDCL evaluate() accepts cag_enabled parameter."""
        import inspect
        from omnix_core.governance.unified_control_layer import UnifiedDecisionControlLayer
        params = inspect.signature(UnifiedDecisionControlLayer.evaluate).parameters
        assert "cag_enabled" in params

    def test_T32_udcl_version_updated(self):
        """T32: UDCL VERSION is ≥ 1.2.x after ADR-141 wiring."""
        from omnix_core.governance.unified_control_layer import UnifiedDecisionControlLayer
        major, minor, *_ = UnifiedDecisionControlLayer.VERSION.split(".")
        assert int(major) >= 1
        assert int(minor) >= 2

    def test_T33_cag_in_pillar_catalog(self):
        """T33: CAG appears in PILLAR_CATALOG as Layer 0d."""
        from omnix_core.governance.unified_control_layer import UnifiedDecisionControlLayer
        catalog = UnifiedDecisionControlLayer.PILLAR_CATALOG
        cag_entries = [p for p in catalog if p["id"] == "context_admission_gate"]
        assert len(cag_entries) == 1
        assert cag_entries[0]["layer"] == "Layer 0d"
        assert cag_entries[0]["adr"]   == "ADR-050"

    def test_T34_cag_catalog_is_opt_in(self):
        """T34: CAG is not mandatory (opt-in by design)."""
        from omnix_core.governance.unified_control_layer import UnifiedDecisionControlLayer
        catalog = UnifiedDecisionControlLayer.PILLAR_CATALOG
        cag = next(p for p in catalog if p["id"] == "context_admission_gate")
        assert cag["mandatory"] is False

    def test_T35_udcl_schema_documents_cag_enabled(self):
        """T35: get_schema() documents cag_enabled parameter."""
        from omnix_core.governance.unified_control_layer import UnifiedDecisionControlLayer
        schema   = UnifiedDecisionControlLayer.get_schema()
        req_body = schema.get("request_body", {})
        assert "cag_enabled" in req_body

    def test_T36_udcl_schema_has_cag_design_invariant(self):
        """T36: get_schema() includes a CAG design invariant."""
        from omnix_core.governance.unified_control_layer import UnifiedDecisionControlLayer
        schema     = UnifiedDecisionControlLayer.get_schema()
        invariants = schema.get("design_invariants", [])
        assert any("CAG" in i for i in invariants)

    def test_T37_run_cag_pass_through_when_disabled(self):
        """T37: _run_cag with disabled config → passed=True (pass-through)."""
        from omnix_core.governance.context_admission_gate import CAGResult
        udcl = self._make_udcl()

        disabled_result = CAGResult(
            admitted=True, pass_through=True,
            reason="CAG_DISABLED", admission_score=0.0,
            evaluation_state="DISABLED",
        )
        with patch(
            "omnix_core.governance.context_admission_gate.ContextAdmissionGate.evaluate",
            return_value=disabled_result,
        ):
            result = udcl._run_cag(
                domain="trading",
                global_volatility=0.0,
                cross_pair_correlation=0.0,
                liquidity_score=0.0,
                macro_risk=0.0,
            )
        assert result.passed is True
        assert result.pillar == "context_admission_gate"
        assert result.layer  == "Layer 0d"

    def test_T38_run_cag_fail_closed_on_exception(self):
        """T38: _run_cag raises exception → passed=False (fail-closed per ADR-116)."""
        udcl = self._make_udcl()

        with patch(
            "omnix_core.governance.context_admission_gate.ContextAdmissionGate.evaluate",
            side_effect=RuntimeError("Unexpected module failure"),
        ):
            result = udcl._run_cag(
                domain="trading",
                global_volatility=0.0,
                cross_pair_correlation=0.0,
                liquidity_score=0.0,
                macro_risk=0.0,
            )
        assert result.passed is False
        assert result.detail.get("evaluation_state") == "FAIL_CLOSED"

    def test_T39_cag_enabled_parameter_default_is_false(self):
        """T39: cag_enabled defaults to False → existing callers unaffected."""
        import inspect
        from omnix_core.governance.unified_control_layer import UnifiedDecisionControlLayer
        sig   = inspect.signature(UnifiedDecisionControlLayer.evaluate)
        param = sig.parameters.get("cag_enabled")
        assert param is not None
        assert param.default is False

    def test_T40_check_pillar_health_includes_cag(self):
        """T40: check_pillar_health() attempts to import ContextAdmissionGate."""
        from omnix_core.governance.unified_control_layer import UnifiedDecisionControlLayer
        health = UnifiedDecisionControlLayer.check_pillar_health()
        assert "context_admission_gate" in health.get("pillars", {})


# ── T41–T45: ADR-141 schema/catalog verification ──────────────────────────────

class TestADR141SchemaVerification:
    """Structural correctness of ADR-141 wiring."""

    _ADR_PATH = os.path.join(
        os.path.dirname(__file__), "..", "docs", "adr",
        "ADR-141-module-api-wiring-oscillation-anomaly-execution-cag.md",
    )

    def _adr_content(self) -> str:
        assert os.path.exists(self._ADR_PATH), "ADR-141 file not found"
        return open(self._ADR_PATH).read()

    def test_T41_pillar_catalog_layer_ordering(self):
        """T41: PILLAR_CATALOG has exact layer ordering: 0, 0b, 0c, 0d, 1-2, 3, 4, 5."""
        from omnix_core.governance.unified_control_layer import UnifiedDecisionControlLayer
        catalog  = UnifiedDecisionControlLayer.PILLAR_CATALOG
        layers   = [p["layer"] for p in catalog]
        expected = [
            "Layer 0", "Layer 0b", "Layer 0c", "Layer 0d",
            "Layer 1-2", "Layer 3", "Layer 4", "Layer 5",
        ]
        assert layers == expected, f"Layer ordering mismatch: {layers}"

    def test_T42_adr141_references_all_four_module_adrs(self):
        """T42: ADR-141 references ADR-134, ADR-129, ADR-131, and ADR-050."""
        content = self._adr_content()
        for adr in ("ADR-134", "ADR-129", "ADR-131", "ADR-050"):
            assert adr in content, f"ADR-141 missing reference to {adr}"

    def test_T43_adr141_documents_all_api_endpoints(self):
        """T43: ADR-141 documents the key API paths for all four modules."""
        content   = self._adr_content()
        endpoints = [
            "/api/analytics/oscillation",
            "/api/governance/anomaly/response",
            "/api/governance/anomaly/active",
            "/api/governance/anomaly/summary",
            "/api/governance/anomaly/history",
            "/api/governance/execution/intent",
            "/api/governance/execution/receipts",
        ]
        for ep in endpoints:
            assert ep in content, f"ADR-141 missing endpoint: {ep}"

    def test_T44_blueprint_allows_cag_enabled_key(self):
        """T44: gov_blueprint UDCL evaluate accepts cag_enabled in body."""
        import inspect
        import omnix_web.api.gov_blueprint as bp_module
        src = inspect.getsource(bp_module.api_udcl_evaluate)
        assert "cag_enabled" in src

    def test_T45_blueprint_allows_ctag_enabled_key(self):
        """T45: gov_blueprint UDCL evaluate accepts ctag_enabled in body."""
        import inspect
        import omnix_web.api.gov_blueprint as bp_module
        src = inspect.getsource(bp_module.api_udcl_evaluate)
        assert "ctag_enabled" in src
