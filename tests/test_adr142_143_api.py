"""
Tests for ADR-142 (Breach Containment Engine) and ADR-143 (Multi-Domain Risk Governance).

Coverage:
  BCE module unit tests (T01–T18)
  MDRG module unit tests (T19–T36)
  API endpoint tests via Flask test client (T37–T55)

NOTE: Uses unittest.mock.patch (no pytest-mock dependency).
"""

import json
import sys
import os
import datetime
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "omnix_web"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "omnix_web", "api"))

_BP_PATH = "api.gov_blueprint"


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _make_mock_bce(contained: bool):
    from omnix_core.governance.breach_containment import (
        ContainmentStatus, BreachEvent, STATUS_ACTIVE, SEVERITY_HIGH, TRIGGER_API
    )
    bce = MagicMock()
    bce.get_status.return_value = ContainmentStatus(
        is_contained    = contained,
        active_event_id = "BCE-MOCK000001" if contained else None,
        trigger_code    = TRIGGER_API if contained else None,
        severity        = SEVERITY_HIGH if contained else None,
        summary         = "Mock containment" if contained else None,
        triggered_at    = datetime.datetime.utcnow().isoformat() if contained else None,
        triggered_by    = "test" if contained else None,
        total_events    = 1 if contained else 0,
        last_event_at   = None,
    )
    bce.activate_containment.return_value = BreachEvent(
        event_id    = "BCE-MOCK000002",
        status      = STATUS_ACTIVE,
        trigger_code= TRIGGER_API,
        severity    = SEVERITY_HIGH,
        summary     = "Mock activation",
        detail      = {},
        triggered_by= "test",
        released_by = None,
        release_note= None,
        triggered_at= datetime.datetime.utcnow().isoformat(),
        released_at = None,
        is_active   = True,
    )
    bce.assess_environment.return_value = {
        "threats_detected":  False,
        "indicator_count":   0,
        "indicators":        [],
        "recommended_action":"CLEAR",
        "assessed_at":       datetime.datetime.utcnow().isoformat(),
        "adr":               "ADR-142",
    }
    bce.get_history.return_value = {
        "events": [], "total": 0, "limit": 20, "offset": 0, "has_more": False,
    }
    bce.release_containment.return_value = {
        "success":      True,
        "event_id":     "BCE-MOCK000001",
        "authorized_by":"test",
        "released_at":  datetime.datetime.utcnow().isoformat(),
        "message":      "Containment released.",
    }
    return bce


def _make_mock_mdrg():
    mdrg = MagicMock()
    mdrg.get_catalog.return_value = {
        "vectors":         ["financial", "technical", "legal", "human"],
        "signal_catalog":  {},
        "default_weights": {"financial": 0.35, "technical": 0.25, "legal": 0.25, "human": 0.15},
        "thresholds":      {"blocked": 80.0, "review": 60.0, "hard_block_per_vector": 95.0},
        "decision_logic":  "composite ≥ 80 → BLOCKED | 60–79 → REVIEW | <60 → APPROVED",
        "adr":             "ADR-143",
    }
    mdrg.evaluate.return_value = {
        "assessment_id":    "MDRG-MOCK000001",
        "subject":          "ACME_CORP",
        "client_domain":    "logistics",
        "decision":         "APPROVED",
        "decision_reason":  "Composite risk score 24.5 < 60.0",
        "composite_score":  24.5,
        "vector_scores":    {"financial":20.0,"technical":15.0,"legal":5.0,"human":10.0},
        "hard_block_vector":None,
        "weights_used":     {"financial":0.35,"technical":0.25,"legal":0.25,"human":0.15},
        "breakdown":        [],
        "thresholds":       {"blocked":80.0,"review":60.0,"hard_block_per_vector":95.0},
        "assessed_by":      "test",
        "assessed_at":      datetime.datetime.utcnow().isoformat(),
        "adr":              "ADR-143",
    }
    mdrg.get_history.return_value = {
        "assessments": [], "total": 0, "limit": 20, "offset": 0, "has_more": False,
    }
    mdrg.get_summary.return_value = {
        "total_assessments": 0, "by_decision": {},
        "averages": {"composite":None,"financial":None,"technical":None,"legal":None,"human":None},
        "adr": "ADR-143",
    }
    return mdrg


def _auth_patch():
    """Return patch for _require_auth → valid client, no error."""
    return patch(
        f"{_BP_PATH}._require_auth",
        return_value=({"client_id": "test-client", "client_name": "Test"}, None),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# BCE module unit tests — T01–T18
# ═══════════════════════════════════════════════════════════════════════════════

class TestBreachContainmentModule:

    def test_T01_module_importable(self):
        from omnix_core.governance.breach_containment import BreachContainmentEngine
        assert BreachContainmentEngine is not None

    def test_T02_constants_defined(self):
        from omnix_core.governance.breach_containment import (
            STATUS_INACTIVE, STATUS_ACTIVE, STATUS_RELEASED,
            TRIGGER_MANUAL, TRIGGER_TIMING_ANOMALY, TRIGGER_CHECKSUM_MISMATCH,
            TRIGGER_PROCESS_ANOMALY, TRIGGER_AUTH_FAILURE, TRIGGER_API,
            SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM,
        )
        assert STATUS_ACTIVE     == "ACTIVE"
        assert STATUS_RELEASED   == "RELEASED"
        assert TRIGGER_CHECKSUM_MISMATCH == "CHECKSUM_MISMATCH"
        assert SEVERITY_CRITICAL == "CRITICAL"

    def test_T03_containment_status_dataclass(self):
        from omnix_core.governance.breach_containment import ContainmentStatus
        s = ContainmentStatus(
            is_contained=False, active_event_id=None, trigger_code=None,
            severity=None, summary=None, triggered_at=None, triggered_by=None,
            total_events=0, last_event_at=None,
        )
        d = s.to_dict()
        assert d["is_contained"] is False
        assert d["adr"] == "ADR-142"
        assert "design_invariant" in d

    def test_T04_breach_event_dataclass(self):
        from omnix_core.governance.breach_containment import (
            BreachEvent, STATUS_ACTIVE, SEVERITY_HIGH, TRIGGER_API
        )
        ev = BreachEvent(
            event_id="BCE-TEST001", status=STATUS_ACTIVE,
            trigger_code=TRIGGER_API, severity=SEVERITY_HIGH,
            summary="Test breach", detail={}, triggered_by="test",
            released_by=None, release_note=None,
            triggered_at="2026-05-08T00:00:00+00:00",
            released_at=None, is_active=True,
        )
        d = ev.to_dict()
        assert d["event_id"] == "BCE-TEST001"
        assert d["status"]   == STATUS_ACTIVE
        assert d["is_active"] is True

    def test_T05_assess_no_threats_when_no_inputs(self):
        from omnix_core.governance.breach_containment import BreachContainmentEngine
        bce    = BreachContainmentEngine()
        result = bce.assess_environment()
        assert result["threats_detected"]  is False
        assert result["recommended_action"] == "CLEAR"
        assert result["indicator_count"]   == 0
        assert result["adr"]               == "ADR-142"

    def test_T06_assess_timing_anomaly_detected(self):
        from omnix_core.governance.breach_containment import (
            BreachContainmentEngine, TRIGGER_TIMING_ANOMALY
        )
        bce    = BreachContainmentEngine()
        result = bce.assess_environment(
            latency_ms=500, expected_latency_ms=50, latency_sigma=5,
        )
        assert result["threats_detected"] is True
        types = [i["type"] for i in result["indicators"]]
        assert TRIGGER_TIMING_ANOMALY in types

    def test_T07_assess_timing_within_3sigma_no_threat(self):
        from omnix_core.governance.breach_containment import BreachContainmentEngine
        bce    = BreachContainmentEngine()
        result = bce.assess_environment(
            latency_ms=55, expected_latency_ms=50, latency_sigma=5,
        )
        assert result["threats_detected"] is False

    def test_T08_assess_checksum_mismatch_critical(self):
        from omnix_core.governance.breach_containment import (
            BreachContainmentEngine, TRIGGER_CHECKSUM_MISMATCH, SEVERITY_CRITICAL
        )
        bce    = BreachContainmentEngine()
        result = bce.assess_environment(
            avm_snapshot_hash="abc123", expected_hash="def456",
        )
        assert result["threats_detected"] is True
        assert any(i["type"]     == TRIGGER_CHECKSUM_MISMATCH for i in result["indicators"])
        assert any(i["severity"] == SEVERITY_CRITICAL         for i in result["indicators"])
        assert result["recommended_action"] == "ACTIVATE_CONTAINMENT"

    def test_T09_assess_checksum_match_no_threat(self):
        from omnix_core.governance.breach_containment import BreachContainmentEngine
        bce    = BreachContainmentEngine()
        result = bce.assess_environment(
            avm_snapshot_hash="abc123", expected_hash="abc123",
        )
        assert result["threats_detected"] is False

    def test_T10_assess_auth_failure_surge(self):
        from omnix_core.governance.breach_containment import (
            BreachContainmentEngine, TRIGGER_AUTH_FAILURE
        )
        bce    = BreachContainmentEngine()
        result = bce.assess_environment(auth_failure_count=15)
        assert result["threats_detected"] is True
        types  = [i["type"] for i in result["indicators"]]
        assert TRIGGER_AUTH_FAILURE in types

    def test_T11_assess_auth_below_threshold_no_threat(self):
        from omnix_core.governance.breach_containment import BreachContainmentEngine
        bce    = BreachContainmentEngine()
        result = bce.assess_environment(auth_failure_count=5)
        assert result["threats_detected"] is False

    def test_T12_assess_multiple_indicators_activate_recommended(self):
        from omnix_core.governance.breach_containment import BreachContainmentEngine
        bce    = BreachContainmentEngine()
        result = bce.assess_environment(
            latency_ms=500, expected_latency_ms=50, latency_sigma=5,
            auth_failure_count=15,
        )
        assert result["recommended_action"] == "ACTIVATE_CONTAINMENT"
        assert result["indicator_count"]    >= 2

    def test_T13_assess_returns_assessed_at_and_adr(self):
        from omnix_core.governance.breach_containment import BreachContainmentEngine
        bce    = BreachContainmentEngine()
        result = bce.assess_environment()
        assert "assessed_at" in result
        assert result["adr"] == "ADR-142"

    def test_T14_event_id_format(self):
        from omnix_core.governance.breach_containment import _event_id
        eid = _event_id()
        assert eid.startswith("BCE-")
        assert len(eid) == 16  # "BCE-" + 12 hex chars

    def test_T15_containment_status_contained_has_design_invariant(self):
        from omnix_core.governance.breach_containment import ContainmentStatus
        s = ContainmentStatus(
            is_contained=True, active_event_id="BCE-ABC",
            trigger_code="MANUAL_OPERATOR", severity="HIGH",
            summary="Test", triggered_at="2026-05-08T00:00:00+00:00",
            triggered_by="ops", total_events=1, last_event_at=None,
        )
        d = s.to_dict()
        assert "design_invariant" in d
        assert "BLOCKED" in d["design_invariant"]

    def test_T16_assess_single_high_threat_monitor_or_activate(self):
        from omnix_core.governance.breach_containment import BreachContainmentEngine
        bce    = BreachContainmentEngine()
        result = bce.assess_environment(
            latency_ms=200, expected_latency_ms=50, latency_sigma=5,
        )
        assert result["threats_detected"] is True
        assert result["recommended_action"] in ("MONITOR", "ACTIVATE_CONTAINMENT")

    def test_T17_engine_has_all_methods(self):
        from omnix_core.governance.breach_containment import BreachContainmentEngine
        bce = BreachContainmentEngine()
        for m in ["ensure_table", "get_status", "activate_containment",
                  "release_containment", "assess_environment", "get_history"]:
            assert hasattr(bce, m), f"Missing method: {m}"

    def test_T18_breach_table_name_correct(self):
        import omnix_core.governance.breach_containment as bce_mod
        assert bce_mod._TABLE == "breach_containment_events"


# ═══════════════════════════════════════════════════════════════════════════════
# MDRG module unit tests — T19–T36
# ═══════════════════════════════════════════════════════════════════════════════

class TestMultiDomainRiskModule:

    def test_T19_module_importable(self):
        from omnix_core.governance.multi_domain_risk import MultiDomainRiskEngine
        assert MultiDomainRiskEngine is not None

    def test_T20_constants_defined(self):
        from omnix_core.governance.multi_domain_risk import (
            THRESHOLD_BLOCKED, THRESHOLD_REVIEW, HARD_BLOCK_SCORE,
            VECTOR_FINANCIAL, VECTOR_TECHNICAL, VECTOR_LEGAL, VECTOR_HUMAN,
        )
        assert THRESHOLD_BLOCKED == 80.0
        assert THRESHOLD_REVIEW  == 60.0
        assert HARD_BLOCK_SCORE  == 95.0
        assert VECTOR_FINANCIAL  == "financial"
        assert VECTOR_HUMAN      == "human"

    def test_T21_catalog_returns_four_vectors(self):
        from omnix_core.governance.multi_domain_risk import MultiDomainRiskEngine
        catalog = MultiDomainRiskEngine().get_catalog()
        assert set(catalog["vectors"]) == {"financial", "technical", "legal", "human"}
        assert "signal_catalog"   in catalog
        assert "default_weights"  in catalog
        assert "thresholds"       in catalog
        assert catalog["adr"]     == "ADR-143"

    def test_T22_default_weights_sum_to_one(self):
        from omnix_core.governance.multi_domain_risk import _DEFAULT_WEIGHTS
        total = sum(_DEFAULT_WEIGHTS.values())
        assert abs(total - 1.0) < 1e-9

    def test_T23_score_financial_pure_risk(self):
        from omnix_core.governance.multi_domain_risk import _score_financial
        result = _score_financial({"capital_exposure_pct": 90, "leverage_ratio": 15, "credit_score": 10})
        assert result["vector"] == "financial"
        assert result["score"]  > 50.0

    def test_T24_score_financial_low_risk(self):
        from omnix_core.governance.multi_domain_risk import _score_financial
        result = _score_financial({
            "capital_exposure_pct": 5, "liquidity_ratio": 5.0,
            "leverage_ratio": 1.0, "credit_score": 90,
        })
        assert result["score"] < 30.0

    def test_T25_score_technical_high_uptime_low_risk(self):
        from omnix_core.governance.multi_domain_risk import _score_technical
        result = _score_technical({"uptime_pct": 99.99, "error_rate_pct": 0.0, "latency_p99_ms": 100})
        assert result["score"] < 20.0

    def test_T26_score_legal_aml_flag_high_risk(self):
        from omnix_core.governance.multi_domain_risk import _score_legal
        result = _score_legal({"aml_flag": 1})
        assert result["score"] >= 20.0

    def test_T27_score_human_full_coverage_low_risk(self):
        from omnix_core.governance.multi_domain_risk import _score_human
        result = _score_human({"oversight_coverage_pct": 100, "fatigue_index": 0, "operator_error_rate_pct": 0})
        assert result["score"] < 15.0

    def test_T28_evaluate_low_risk_approved_no_db(self, monkeypatch):
        from omnix_core.governance.multi_domain_risk import MultiDomainRiskEngine
        engine = MultiDomainRiskEngine()
        monkeypatch.setattr(engine, "_ensure",  lambda: None)
        monkeypatch.setattr(engine, "_persist", lambda *a, **kw: None)
        result = engine.evaluate(
            subject="TEST_SUBJECT_LOW",
            risk_signals={
                "financial": {"capital_exposure_pct": 5, "leverage_ratio": 1.0, "liquidity_ratio": 4.0},
                "technical": {"uptime_pct": 99.9, "error_rate_pct": 0.1, "latency_p99_ms": 150},
                "legal":     {"regulatory_violations": 0, "aml_flag": 0},
                "human":     {"oversight_coverage_pct": 95, "fatigue_index": 5},
            },
        )
        assert result["decision"]        == "APPROVED"
        assert result["composite_score"]  < 60.0
        assert result["assessment_id"].startswith("MDRG-")
        assert result["adr"]             == "ADR-143"

    def test_T29_evaluate_high_risk_blocked_no_db(self, monkeypatch):
        """All four vectors at maximum stress → composite ≥ 80 → BLOCKED."""
        from omnix_core.governance.multi_domain_risk import MultiDomainRiskEngine
        engine = MultiDomainRiskEngine()
        monkeypatch.setattr(engine, "_ensure",  lambda: None)
        monkeypatch.setattr(engine, "_persist", lambda *a, **kw: None)
        result = engine.evaluate(
            subject="TEST_SUBJECT_HIGH",
            risk_signals={
                "financial": {
                    "capital_exposure_pct": 100,
                    "leverage_ratio":       40,
                    "credit_score":         0,
                    "liquidity_ratio":      0,
                    "concentration_pct":    100,
                },
                "technical": {
                    "uptime_pct":              50,
                    "error_rate_pct":          20,
                    "latency_p99_ms":          30_000,
                    "dependency_failure_count":20,
                    "last_incident_hours":     1,
                },
                "legal": {
                    "regulatory_violations":   15,
                    "aml_flag":                1,
                    "jurisdiction_risk_score": 95,
                    "pending_litigation":      20,
                    "license_expiry_days":     0,
                },
                "human": {
                    "fatigue_index":           95,
                    "oversight_coverage_pct":  5,
                    "operator_error_rate_pct": 20,
                    "training_currency_days":  365,
                    "escalation_backlog":      100,
                },
            },
        )
        assert result["decision"]        == "BLOCKED"
        assert result["composite_score"] >= 80.0

    def test_T30_hard_block_single_vector_legal(self, monkeypatch):
        """Legal vector with all signals maxed → vector score ≥ 95 → BLOCKED regardless of composite."""
        from omnix_core.governance.multi_domain_risk import MultiDomainRiskEngine
        engine = MultiDomainRiskEngine()
        monkeypatch.setattr(engine, "_ensure",  lambda: None)
        monkeypatch.setattr(engine, "_persist", lambda *a, **kw: None)
        result = engine.evaluate(
            subject="HARD_BLOCK_TEST",
            risk_signals={
                "financial": {"capital_exposure_pct": 5},
                "technical": {"uptime_pct": 99.9},
                "legal": {
                    "regulatory_violations":   15,   # → 100
                    "aml_flag":                1,    # → 100
                    "jurisdiction_risk_score": 95,   # → 95
                    "pending_litigation":      20,   # → 100
                    "license_expiry_days":     0,    # → 100
                },
                "human": {"fatigue_index": 5},
            },
        )
        assert result["decision"]          == "BLOCKED"
        assert result["hard_block_vector"] is not None

    def test_T31_custom_weights_normalized(self, monkeypatch):
        from omnix_core.governance.multi_domain_risk import MultiDomainRiskEngine
        engine = MultiDomainRiskEngine()
        monkeypatch.setattr(engine, "_ensure",  lambda: None)
        monkeypatch.setattr(engine, "_persist", lambda *a, **kw: None)
        result = engine.evaluate(
            subject="CUSTOM_WEIGHTS",
            risk_signals={"financial": {"capital_exposure_pct": 10}},
            weights={"financial": 2, "technical": 2, "legal": 1, "human": 1},
        )
        total_w = sum(result["weights_used"].values())
        assert abs(total_w - 1.0) < 1e-6

    def test_T32_evaluate_returns_breakdown_per_vector(self, monkeypatch):
        from omnix_core.governance.multi_domain_risk import MultiDomainRiskEngine
        engine = MultiDomainRiskEngine()
        monkeypatch.setattr(engine, "_ensure",  lambda: None)
        monkeypatch.setattr(engine, "_persist", lambda *a, **kw: None)
        result = engine.evaluate(
            subject="BREAKDOWN_TEST",
            risk_signals={"financial": {"capital_exposure_pct": 20}},
        )
        assert "breakdown" in result
        assert len(result["breakdown"]) == 4
        vectors = {b["vector"] for b in result["breakdown"]}
        assert vectors == {"financial", "technical", "legal", "human"}

    def test_T33_evaluate_returns_thresholds(self, monkeypatch):
        from omnix_core.governance.multi_domain_risk import MultiDomainRiskEngine
        engine = MultiDomainRiskEngine()
        monkeypatch.setattr(engine, "_ensure",  lambda: None)
        monkeypatch.setattr(engine, "_persist", lambda *a, **kw: None)
        result = engine.evaluate(subject="X", risk_signals={"financial": {}})
        assert result["thresholds"]["blocked"] == 80.0
        assert result["thresholds"]["review"]  == 60.0

    def test_T34_assessment_id_format(self):
        from omnix_core.governance.multi_domain_risk import _assessment_id
        aid = _assessment_id()
        assert aid.startswith("MDRG-")
        assert len(aid) == 17  # "MDRG-" + 12 hex chars

    def test_T35_engine_has_all_public_methods(self):
        from omnix_core.governance.multi_domain_risk import MultiDomainRiskEngine
        engine = MultiDomainRiskEngine()
        for m in ["evaluate", "get_catalog", "get_history", "get_summary", "ensure_table"]:
            assert hasattr(engine, m), f"Missing method: {m}"

    def test_T36_signal_catalog_has_all_four_vectors(self):
        from omnix_core.governance.multi_domain_risk import _SIGNAL_CATALOG
        assert set(_SIGNAL_CATALOG.keys()) == {"financial", "technical", "legal", "human"}
        for v, signals in _SIGNAL_CATALOG.items():
            assert len(signals) >= 4, f"Vector {v} has too few signals ({len(signals)})"


# ═══════════════════════════════════════════════════════════════════════════════
# Flask API endpoint tests — T37–T55
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def app():
    from api.server import app as flask_app
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture(scope="module")
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def clear_brute_force():
    import importlib
    bp = importlib.import_module(_BP_PATH)
    if hasattr(bp, "_brute_force_store"):
        bp._brute_force_store.clear()


_AUTH_HDR = {"X-API-Key": "OMNIX-test-key-1234"}


class TestBreachContainmentAPI:
    """T37–T46: BCE API endpoints."""

    def test_T37_breach_status_public_no_auth(self, client):
        mock_bce = _make_mock_bce(contained=False)
        with patch(f"{_BP_PATH}._get_bce", return_value=mock_bce):
            resp = client.get("/api/governance/breach/status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "is_contained" in data
        assert data["is_contained"] is False
        assert data["adr"] == "ADR-142"

    def test_T38_breach_status_returns_adr_header(self, client):
        mock_bce = _make_mock_bce(contained=False)
        with patch(f"{_BP_PATH}._get_bce", return_value=mock_bce):
            resp = client.get("/api/governance/breach/status")
        assert resp.headers.get("X-OMNIX-ADR") == "ADR-142"

    def test_T39_breach_activate_requires_auth(self, client):
        resp = client.post("/api/governance/breach/activate", json={
            "trigger_code": "API_TRIGGERED",
            "severity":     "HIGH",
            "summary":      "Test",
        })
        assert resp.status_code == 401

    def test_T40_breach_activate_success(self, client):
        mock_bce = _make_mock_bce(contained=False)
        auth_ret = ({"client_id": "test-client"}, None)
        with patch(f"{_BP_PATH}._require_auth", return_value=auth_ret), \
             patch(f"{_BP_PATH}._get_bce", return_value=mock_bce):
            resp = client.post(
                "/api/governance/breach/activate",
                json={"trigger_code": "API_TRIGGERED", "severity": "HIGH", "summary": "Test threat"},
                headers=_AUTH_HDR,
            )
        assert resp.status_code == 201
        data = resp.get_json()
        assert "event"   in data
        assert data["adr"]    == "ADR-142"
        assert data["status"] == "CONTAINMENT_ACTIVATED"

    def test_T41_breach_activate_invalid_trigger_code(self, client):
        auth_ret = ({"client_id": "test-client"}, None)
        with patch(f"{_BP_PATH}._require_auth", return_value=auth_ret):
            resp = client.post(
                "/api/governance/breach/activate",
                json={"trigger_code": "INVALID_CODE", "severity": "HIGH", "summary": "Test"},
                headers=_AUTH_HDR,
            )
        assert resp.status_code == 400

    def test_T42_breach_activate_invalid_severity(self, client):
        auth_ret = ({"client_id": "test-client"}, None)
        with patch(f"{_BP_PATH}._require_auth", return_value=auth_ret):
            resp = client.post(
                "/api/governance/breach/activate",
                json={"trigger_code": "API_TRIGGERED", "severity": "BANANA", "summary": "Test"},
                headers=_AUTH_HDR,
            )
        assert resp.status_code == 400

    def test_T43_breach_release_missing_note(self, client):
        mock_bce = _make_mock_bce(contained=True)
        auth_ret = ({"client_id": "test-client"}, None)
        with patch(f"{_BP_PATH}._require_auth", return_value=auth_ret), \
             patch(f"{_BP_PATH}._get_bce", return_value=mock_bce):
            resp = client.post(
                "/api/governance/breach/release",
                json={"event_id": "BCE-ABC123456789", "authorized_by": "ciso"},
                headers=_AUTH_HDR,
            )
        assert resp.status_code == 400

    def test_T44_breach_assess_authenticated(self, client):
        mock_bce = _make_mock_bce(contained=False)
        auth_ret = ({"client_id": "test-client"}, None)
        with patch(f"{_BP_PATH}._require_auth", return_value=auth_ret), \
             patch(f"{_BP_PATH}._get_bce", return_value=mock_bce):
            resp = client.post(
                "/api/governance/breach/assess",
                json={"auth_failure_count": 0},
                headers=_AUTH_HDR,
            )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "threats_detected" in data
        assert data["adr"] == "ADR-142"

    def test_T45_breach_history_requires_auth(self, client):
        resp = client.get("/api/governance/breach/history")
        assert resp.status_code == 401

    def test_T46_breach_history_success(self, client):
        mock_bce = _make_mock_bce(contained=False)
        auth_ret = ({"client_id": "test-client"}, None)
        with patch(f"{_BP_PATH}._require_auth", return_value=auth_ret), \
             patch(f"{_BP_PATH}._get_bce", return_value=mock_bce):
            resp = client.get("/api/governance/breach/history", headers=_AUTH_HDR)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "events" in data
        assert data["adr"] == "ADR-142"


class TestMultiDomainRiskAPI:
    """T47–T55: MDRG API endpoints."""

    def test_T47_risk_catalog_public_no_auth(self, client):
        mock_mdrg = _make_mock_mdrg()
        with patch(f"{_BP_PATH}._get_mdrg", return_value=mock_mdrg):
            resp = client.get("/api/governance/risk/catalog")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "vectors"      in data
        assert data["adr"]    == "ADR-143"
        assert resp.headers.get("X-OMNIX-ADR") == "ADR-143"

    def test_T48_risk_evaluate_requires_auth(self, client):
        resp = client.post("/api/governance/risk/evaluate", json={
            "subject":      "TEST",
            "risk_signals": {"financial": {"capital_exposure_pct": 10}},
        })
        assert resp.status_code == 401

    def test_T49_risk_evaluate_missing_subject(self, client):
        auth_ret = ({"client_id": "test-client"}, None)
        with patch(f"{_BP_PATH}._require_auth", return_value=auth_ret):
            resp = client.post(
                "/api/governance/risk/evaluate",
                json={"risk_signals": {"financial": {}}},
                headers=_AUTH_HDR,
            )
        assert resp.status_code == 400

    def test_T50_risk_evaluate_missing_signals(self, client):
        auth_ret = ({"client_id": "test-client"}, None)
        with patch(f"{_BP_PATH}._require_auth", return_value=auth_ret):
            resp = client.post(
                "/api/governance/risk/evaluate",
                json={"subject": "TEST"},
                headers=_AUTH_HDR,
            )
        assert resp.status_code == 400

    def test_T51_risk_evaluate_invalid_vector(self, client):
        auth_ret = ({"client_id": "test-client"}, None)
        with patch(f"{_BP_PATH}._require_auth", return_value=auth_ret):
            resp = client.post(
                "/api/governance/risk/evaluate",
                json={"subject": "TEST", "risk_signals": {"banana": {"x": 1}}},
                headers=_AUTH_HDR,
            )
        assert resp.status_code == 400

    def test_T52_risk_evaluate_success(self, client):
        mock_mdrg = _make_mock_mdrg()
        auth_ret  = ({"client_id": "test-client"}, None)
        with patch(f"{_BP_PATH}._require_auth", return_value=auth_ret), \
             patch(f"{_BP_PATH}._get_mdrg", return_value=mock_mdrg):
            resp = client.post(
                "/api/governance/risk/evaluate",
                json={
                    "subject":       "ACME_CORP",
                    "risk_signals":  {"financial": {"capital_exposure_pct": 20}},
                    "client_domain": "logistics",
                },
                headers=_AUTH_HDR,
            )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "decision"  in data
        assert data["decision"] in ("APPROVED", "REVIEW", "BLOCKED")
        assert data["adr"] == "ADR-143"

    def test_T53_risk_history_requires_auth(self, client):
        resp = client.get("/api/governance/risk/history")
        assert resp.status_code == 401

    def test_T54_risk_history_success(self, client):
        mock_mdrg = _make_mock_mdrg()
        auth_ret  = ({"client_id": "test-client"}, None)
        with patch(f"{_BP_PATH}._require_auth", return_value=auth_ret), \
             patch(f"{_BP_PATH}._get_mdrg", return_value=mock_mdrg):
            resp = client.get("/api/governance/risk/history", headers=_AUTH_HDR)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "assessments" in data
        assert data["adr"]   == "ADR-143"

    def test_T55_risk_summary_requires_auth(self, client):
        resp = client.get("/api/governance/risk/summary")
        assert resp.status_code == 401
