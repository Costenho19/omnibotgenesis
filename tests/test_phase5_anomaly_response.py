"""
Phase 5 — AnomalyResponseEngine tests (ADR-129)

All tests run without a real DB. DB calls are either intercepted via mock connections
or the engine is configured with no DB URL to exercise graceful degradation.

Run:
    TESTING=true TELEGRAM_BOT_TOKEN=test-token \
        python -m pytest tests/test_phase5_anomaly_response.py -v --tb=short
"""

import os
import sys
import uuid
import pytest

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import MagicMock, patch, call
from omnix_core.governance.anomaly_response import (
    AnomalyResponseEngine,
    AnomalyRecommendation,
    get_response_engine,
    _empty_summary,
    STATUS_ACTIVE,
    STATUS_ACKNOWLEDGED,
    STATUS_RESOLVED,
    STATUS_EXPIRED,
    URGENCY_IMMEDIATE,
    URGENCY_URGENT,
    URGENCY_ELEVATED,
    URGENCY_MONITORING,
    ACTION_SUSPEND_RECALIBRATION,
    ACTION_REDUCE_POSITION_SIZING,
    ACTION_FLAG_OPERATIONAL_ALERT,
    ACTION_TRIGGER_AVM_REVIEW,
    ACTION_MONITOR_BS_LEVELS,
    ACTION_ESCALATION_REVIEW,
    _ANOMALY_ACTION_MAP,
    _SEVERITY_TO_URGENCY,
)


# ── Fixtures / builders ───────────────────────────────────────────────────────

def _anomaly(atype: str, severity: str = "MEDIUM") -> dict:
    """Build a single anomaly dict as returned by detect_anomalies()."""
    return {
        "anomaly_type":    atype,
        "severity":        severity,
        "domain":          "trading",
        "description":     f"{atype} detected",
        "current_value":   0.05,
        "baseline_value":  0.30,
        "deviation":       0.25,
        "threshold":       0.15,
        "window_current":  "1h",
        "window_baseline": "1d",
        "detected_at":     "2026-04-25T12:00:00+00:00",
    }


def _anomaly_result(
    anomaly_types: list,
    severity:      str   = "MEDIUM",
    available:     bool  = True,
    domain:        str   = "trading",
    overall:       str   = "MEDIUM",
) -> dict:
    """Build a detect_anomalies() result dict."""
    anomalies = [_anomaly(t, severity) for t in anomaly_types]
    return {
        "domain":           domain,
        "available":        available,
        "anomalies":        anomalies,
        "summary":          {"total": len(anomalies), "critical": 0, "high": 0, "medium": len(anomalies), "low": 0},
        "overall_severity": overall,
        "analyzed_at":      "2026-04-25T12:00:00+00:00",
    }


def _engine_no_db() -> AnomalyResponseEngine:
    """Engine with no DB URL — all DB calls degrade gracefully."""
    with patch.dict(os.environ, {"DATABASE_URL": "", "OMNIX_DB_URL": ""}):
        return AnomalyResponseEngine(db_url=None)


def _mock_conn(rowcount: int = 1) -> MagicMock:
    """Build a mock psycopg2 connection."""
    conn = MagicMock()
    cur  = MagicMock()
    cur.rowcount = rowcount
    cur.fetchone.return_value = (2, 1, 3, 0)   # active, ack, resolved, expired
    cur.fetchall.return_value = []
    conn.cursor.return_value = cur
    return conn


# ══════════════════════════════════════════════════════════════════════════════
# T01 — Constants and mappings
# ══════════════════════════════════════════════════════════════════════════════

class TestConstants:

    def test_all_six_anomaly_types_have_mapping(self):
        expected = {
            "BLOCK_RATE_DROP", "DCI_SURGE", "HOLD_SPIKE",
            "COHERENCE_DRIFT", "BS_HIGH_SURGE", "ESCALATION_SURGE",
        }
        assert set(_ANOMALY_ACTION_MAP.keys()) == expected

    def test_action_codes_are_distinct(self):
        codes = [spec.action_code for spec in _ANOMALY_ACTION_MAP.values()]
        assert len(codes) == len(set(codes)), "Action codes must be unique"

    def test_all_action_specs_have_description_and_rationale(self):
        for atype, spec in _ANOMALY_ACTION_MAP.items():
            assert len(spec.action_description) > 20, f"{atype}: description too short"
            assert len(spec.rationale) > 20, f"{atype}: rationale too short"

    def test_all_action_specs_are_reversible(self):
        for atype, spec in _ANOMALY_ACTION_MAP.items():
            assert spec.is_reversible is True, f"{atype} should be reversible"

    def test_severity_urgency_mapping_complete(self):
        for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
            assert sev in _SEVERITY_TO_URGENCY

    def test_critical_maps_to_immediate(self):
        assert _SEVERITY_TO_URGENCY["CRITICAL"] == URGENCY_IMMEDIATE

    def test_high_maps_to_urgent(self):
        assert _SEVERITY_TO_URGENCY["HIGH"] == URGENCY_URGENT

    def test_medium_maps_to_elevated(self):
        assert _SEVERITY_TO_URGENCY["MEDIUM"] == URGENCY_ELEVATED

    def test_low_maps_to_monitoring(self):
        assert _SEVERITY_TO_URGENCY["LOW"] == URGENCY_MONITORING

    def test_block_rate_drop_maps_to_suspend_recalibration(self):
        assert _ANOMALY_ACTION_MAP["BLOCK_RATE_DROP"].action_code == ACTION_SUSPEND_RECALIBRATION

    def test_dci_surge_maps_to_reduce_position_sizing(self):
        assert _ANOMALY_ACTION_MAP["DCI_SURGE"].action_code == ACTION_REDUCE_POSITION_SIZING

    def test_hold_spike_maps_to_flag_operational_alert(self):
        assert _ANOMALY_ACTION_MAP["HOLD_SPIKE"].action_code == ACTION_FLAG_OPERATIONAL_ALERT

    def test_coherence_drift_maps_to_trigger_avm_review(self):
        assert _ANOMALY_ACTION_MAP["COHERENCE_DRIFT"].action_code == ACTION_TRIGGER_AVM_REVIEW

    def test_bs_high_surge_maps_to_monitor_bs_levels(self):
        assert _ANOMALY_ACTION_MAP["BS_HIGH_SURGE"].action_code == ACTION_MONITOR_BS_LEVELS

    def test_escalation_surge_maps_to_escalation_review(self):
        assert _ANOMALY_ACTION_MAP["ESCALATION_SURGE"].action_code == ACTION_ESCALATION_REVIEW


# ══════════════════════════════════════════════════════════════════════════════
# T02 — AnomalyRecommendation dataclass
# ══════════════════════════════════════════════════════════════════════════════

class TestAnomalyRecommendation:

    def _make_rec(self, **kwargs) -> AnomalyRecommendation:
        defaults = dict(
            id="test-id-123", anomaly_type="DCI_SURGE", severity="HIGH",
            urgency=URGENCY_URGENT, domain="trading",
            action_code=ACTION_REDUCE_POSITION_SIZING,
            action_description="Reduce sizing", rationale="DCI high",
            is_reversible=True,
        )
        defaults.update(kwargs)
        return AnomalyRecommendation(**defaults)

    def test_to_dict_has_all_required_keys(self):
        rec = self._make_rec()
        d = rec.to_dict()
        for key in (
            "id", "anomaly_type", "severity", "urgency", "domain",
            "action_code", "action_description", "rationale",
            "is_reversible", "status", "created_at",
            "anomaly_detected_at", "expires_at",
            "acknowledged_at", "acknowledged_by",
            "resolved_at", "resolved_note", "auto_generated",
        ):
            assert key in d, f"Missing key: {key}"

    def test_default_status_is_active(self):
        rec = self._make_rec()
        assert rec.status == STATUS_ACTIVE

    def test_auto_generated_is_true_by_default(self):
        rec = self._make_rec()
        assert rec.auto_generated is True

    def test_is_reversible_preserved(self):
        rec = self._make_rec(is_reversible=True)
        assert rec.to_dict()["is_reversible"] is True


# ══════════════════════════════════════════════════════════════════════════════
# T03 — generate_recommendations() — pure function
# ══════════════════════════════════════════════════════════════════════════════

class TestGenerateRecommendations:

    def _engine(self) -> AnomalyResponseEngine:
        return _engine_no_db()

    def test_no_recommendations_when_not_available(self):
        engine = self._engine()
        result = engine.generate_recommendations({"available": False, "anomalies": []})
        assert result == []

    def test_no_recommendations_when_no_anomalies(self):
        engine = self._engine()
        result = engine.generate_recommendations(_anomaly_result([]))
        assert result == []

    def test_one_recommendation_per_anomaly(self):
        engine = self._engine()
        ar = _anomaly_result(["DCI_SURGE", "HOLD_SPIKE"])
        recs = engine.generate_recommendations(ar)
        assert len(recs) == 2

    def test_all_six_anomaly_types_generate_recommendations(self):
        engine = self._engine()
        all_types = [
            "BLOCK_RATE_DROP", "DCI_SURGE", "HOLD_SPIKE",
            "COHERENCE_DRIFT", "BS_HIGH_SURGE", "ESCALATION_SURGE",
        ]
        ar = _anomaly_result(all_types)
        recs = engine.generate_recommendations(ar)
        assert len(recs) == 6

    def test_unknown_anomaly_type_skipped(self):
        engine = self._engine()
        ar = _anomaly_result(["UNKNOWN_ANOMALY_XYZ"])
        recs = engine.generate_recommendations(ar)
        assert len(recs) == 0

    def test_recommendation_has_uuid(self):
        engine = self._engine()
        recs = engine.generate_recommendations(_anomaly_result(["DCI_SURGE"]))
        assert len(recs) == 1
        # Should be parseable as UUID
        uid = uuid.UUID(recs[0].id)
        assert str(uid) == recs[0].id

    def test_recommendation_has_correct_action_code(self):
        engine = self._engine()
        recs = engine.generate_recommendations(_anomaly_result(["DCI_SURGE"]))
        assert recs[0].action_code == ACTION_REDUCE_POSITION_SIZING

    def test_recommendation_urgency_from_severity(self):
        engine = self._engine()
        recs_crit = engine.generate_recommendations(_anomaly_result(["DCI_SURGE"], severity="CRITICAL"))
        recs_low  = engine.generate_recommendations(_anomaly_result(["DCI_SURGE"], severity="LOW"))
        assert recs_crit[0].urgency == URGENCY_IMMEDIATE
        assert recs_low[0].urgency  == URGENCY_MONITORING

    def test_recommendation_status_is_active(self):
        engine = self._engine()
        recs = engine.generate_recommendations(_anomaly_result(["HOLD_SPIKE"]))
        assert recs[0].status == STATUS_ACTIVE

    def test_recommendation_is_reversible(self):
        engine = self._engine()
        recs = engine.generate_recommendations(_anomaly_result(["COHERENCE_DRIFT"]))
        assert recs[0].is_reversible is True

    def test_recommendation_domain_preserved(self):
        engine = self._engine()
        ar = _anomaly_result(["BS_HIGH_SURGE"], domain="credit")
        recs = engine.generate_recommendations(ar)
        assert recs[0].domain == "credit"

    def test_recommendation_expires_at_set(self):
        engine = _engine_no_db()
        recs = engine.generate_recommendations(_anomaly_result(["ESCALATION_SURGE"]))
        assert recs[0].expires_at is not None

    def test_custom_expiry_hours(self):
        engine = _engine_no_db()
        recs_24 = engine.generate_recommendations(_anomaly_result(["DCI_SURGE"]), expiry_hours=24)
        recs_1  = engine.generate_recommendations(_anomaly_result(["DCI_SURGE"]), expiry_hours=1)
        # Both should have expires_at set (can't easily compare without parsing, but not None)
        assert recs_24[0].expires_at is not None
        assert recs_1[0].expires_at  is not None
        # 24h expiry should be later than 1h expiry
        assert recs_24[0].expires_at > recs_1[0].expires_at

    def test_anomaly_detected_at_forwarded(self):
        engine = _engine_no_db()
        recs = engine.generate_recommendations(_anomaly_result(["DCI_SURGE"]))
        assert recs[0].anomaly_detected_at == "2026-04-25T12:00:00+00:00"

    def test_auto_generated_true(self):
        engine = _engine_no_db()
        recs = engine.generate_recommendations(_anomaly_result(["DCI_SURGE"]))
        assert recs[0].auto_generated is True

    def test_unique_ids_across_recommendations(self):
        engine = _engine_no_db()
        ar = _anomaly_result(["BLOCK_RATE_DROP", "DCI_SURGE", "HOLD_SPIKE"])
        recs = engine.generate_recommendations(ar)
        ids = [r.id for r in recs]
        assert len(ids) == len(set(ids)), "All recommendation IDs should be unique"


# ══════════════════════════════════════════════════════════════════════════════
# T04 — log_recommendations()
# ══════════════════════════════════════════════════════════════════════════════

class TestLogRecommendations:

    def test_log_empty_list_returns_zero(self):
        engine = _engine_no_db()
        assert engine.log_recommendations([]) == 0

    def test_log_without_db_url_returns_zero(self):
        engine = _engine_no_db()
        recs = engine.generate_recommendations(_anomaly_result(["DCI_SURGE"]))
        result = engine.log_recommendations(recs)
        assert result == 0

    def test_log_with_mock_conn_inserts_rows(self):
        engine = _engine_no_db()
        recs = engine.generate_recommendations(_anomaly_result(["DCI_SURGE", "HOLD_SPIKE"]))
        conn = _mock_conn(rowcount=1)
        written = engine.log_recommendations(recs, conn=conn)
        assert written == 2

    def test_log_uses_on_conflict_do_nothing(self):
        engine = _engine_no_db()
        recs = engine.generate_recommendations(_anomaly_result(["DCI_SURGE"]))
        conn = _mock_conn(rowcount=1)
        engine.log_recommendations(recs, conn=conn)
        sql_calls = conn.cursor().execute.call_args_list
        assert any("ON CONFLICT" in str(c) for c in sql_calls)

    def test_log_zero_when_conflict(self):
        """rowcount=0 simulates ON CONFLICT DO NOTHING (duplicate)."""
        engine = _engine_no_db()
        recs = engine.generate_recommendations(_anomaly_result(["DCI_SURGE"]))
        conn = _mock_conn(rowcount=0)
        written = engine.log_recommendations(recs, conn=conn)
        assert written == 0


# ══════════════════════════════════════════════════════════════════════════════
# T05 — Lifecycle transitions (acknowledge, resolve)
# ══════════════════════════════════════════════════════════════════════════════

class TestLifecycleTransitions:

    def test_acknowledge_success(self):
        engine = _engine_no_db()
        conn = _mock_conn(rowcount=1)
        result = engine.acknowledge("test-id", "operator@omnix.com", conn=conn)
        assert result is True

    def test_acknowledge_failure_not_found(self):
        engine = _engine_no_db()
        conn = _mock_conn(rowcount=0)
        result = engine.acknowledge("nonexistent-id", "op@test.com", conn=conn)
        assert result is False

    def test_acknowledge_without_db_returns_false(self):
        engine = _engine_no_db()
        result = engine.acknowledge("test-id", "op@test.com")
        assert result is False

    def test_resolve_success(self):
        engine = _engine_no_db()
        conn = _mock_conn(rowcount=1)
        result = engine.resolve("test-id", "Issue resolved after investigation", conn=conn)
        assert result is True

    def test_resolve_failure_not_found(self):
        engine = _engine_no_db()
        conn = _mock_conn(rowcount=0)
        result = engine.resolve("nonexistent-id", conn=conn)
        assert result is False

    def test_resolve_without_db_returns_false(self):
        engine = _engine_no_db()
        result = engine.resolve("test-id", "note")
        assert result is False

    def test_acknowledge_updates_correct_columns(self):
        engine = _engine_no_db()
        conn = _mock_conn(rowcount=1)
        engine.acknowledge("test-id", "auditor@omnix.com", conn=conn)
        sql_calls = [str(c) for c in conn.cursor().execute.call_args_list]
        assert any("acknowledged_at" in c for c in sql_calls)
        assert any("acknowledged_by" in c for c in sql_calls)

    def test_resolve_updates_correct_columns(self):
        engine = _engine_no_db()
        conn = _mock_conn(rowcount=1)
        engine.resolve("test-id", "Root cause fixed", conn=conn)
        sql_calls = [str(c) for c in conn.cursor().execute.call_args_list]
        assert any("resolved_at" in c for c in sql_calls)
        assert any("resolved_note" in c for c in sql_calls)


# ══════════════════════════════════════════════════════════════════════════════
# T06 — expire_stale()
# ══════════════════════════════════════════════════════════════════════════════

class TestExpireStale:

    def test_expire_stale_no_db_returns_zero(self):
        engine = _engine_no_db()
        assert engine.expire_stale() == 0

    def test_expire_stale_with_conn_returns_rowcount(self):
        engine = _engine_no_db()
        conn = _mock_conn(rowcount=5)
        result = engine.expire_stale(conn=conn)
        assert result == 5

    def test_expire_stale_with_hours_uses_different_sql(self):
        engine = _engine_no_db()
        conn = _mock_conn(rowcount=3)
        engine.expire_stale(hours=48, conn=conn)
        sql_calls = [str(c) for c in conn.cursor().execute.call_args_list]
        assert any("hours" in c.lower() or "INTERVAL" in c for c in sql_calls)


# ══════════════════════════════════════════════════════════════════════════════
# T07 — get_active() and get_history()
# ══════════════════════════════════════════════════════════════════════════════

class TestQueryMethods:

    def test_get_active_no_db_returns_empty_list(self):
        engine = _engine_no_db()
        result = engine.get_active()
        assert result == []

    def test_get_history_no_db_returns_empty_list(self):
        engine = _engine_no_db()
        result = engine.get_history()
        assert result == []

    def test_get_active_with_mock_conn(self):
        engine = _engine_no_db()
        conn = MagicMock()
        cur  = MagicMock()
        cur.fetchall.return_value = []
        conn.cursor.return_value  = cur
        result = engine.get_active(conn=conn)
        assert isinstance(result, list)

    def test_get_active_queries_only_active_status(self):
        engine = _engine_no_db()
        conn = MagicMock()
        cur  = MagicMock()
        cur.fetchall.return_value = []
        conn.cursor.return_value  = cur
        engine.get_active(conn=conn)
        sql_str = str(cur.execute.call_args)
        assert STATUS_ACTIVE in sql_str


# ══════════════════════════════════════════════════════════════════════════════
# T08 — summary()
# ══════════════════════════════════════════════════════════════════════════════

class TestSummary:

    def test_summary_no_db_returns_available_false(self):
        engine = _engine_no_db()
        result = engine.summary()
        assert result["available"] is False

    def test_summary_with_conn_returns_counts(self):
        engine = _engine_no_db()
        conn = MagicMock()
        cur  = MagicMock()
        cur.fetchone.return_value = (3, 1, 2, 0)
        cur.fetchall.return_value = [
            ("SUSPEND_RECALIBRATION", 2),
            ("REDUCE_POSITION_SIZING", 1),
        ]
        conn.cursor.return_value = cur
        result = engine.summary(conn=conn)
        assert result["active"]       == 3
        assert result["acknowledged"] == 1
        assert result["resolved"]     == 2
        assert result["expired"]      == 0
        assert "SUSPEND_RECALIBRATION" in result["by_action"]

    def test_empty_summary_helper(self):
        s = _empty_summary("trading")
        assert s["domain"]    == "trading"
        assert s["available"] is False
        assert s["active"]    == 0

    def test_summary_domain_forwarded(self):
        engine = _engine_no_db()
        result = engine.summary(domain="credit")
        assert result["domain"] == "credit"


# ══════════════════════════════════════════════════════════════════════════════
# T09 — full_response_cycle()
# ══════════════════════════════════════════════════════════════════════════════

class TestFullResponseCycle:

    def _engine_with_mock_insight(self, anomaly_types: list, severity: str = "MEDIUM"):
        """Engine whose CalibrationInsightEngine is mocked."""
        mock_insight = MagicMock()
        mock_insight.detect_anomalies.return_value = _anomaly_result(
            anomaly_types, severity=severity
        )
        engine = AnomalyResponseEngine(db_url=None, insight_engine=mock_insight)
        return engine

    def test_full_cycle_returns_required_keys(self):
        engine = self._engine_with_mock_insight(["DCI_SURGE"])
        result = engine.full_response_cycle(domain="trading")
        for key in ("domain", "available", "anomalies", "recommendations",
                    "new_logged", "active_count", "overall_severity", "generated_at"):
            assert key in result

    def test_full_cycle_no_anomalies(self):
        engine = self._engine_with_mock_insight([])
        result = engine.full_response_cycle()
        assert result["recommendations"] == []
        assert result["new_logged"] == 0

    def test_full_cycle_generates_recommendations(self):
        engine = self._engine_with_mock_insight(["DCI_SURGE", "HOLD_SPIKE"])
        result = engine.full_response_cycle()
        assert len(result["recommendations"]) == 2

    def test_full_cycle_domain_forwarded(self):
        engine = self._engine_with_mock_insight(["DCI_SURGE"])
        result = engine.full_response_cycle(domain="insurance")
        assert result["domain"] == "insurance"

    def test_full_cycle_severity_preserved(self):
        engine = self._engine_with_mock_insight(["DCI_SURGE"], severity="CRITICAL")
        result = engine.full_response_cycle()
        assert result["recommendations"][0]["severity"] == "CRITICAL"
        assert result["recommendations"][0]["urgency"]  == URGENCY_IMMEDIATE

    def test_full_cycle_insight_error_returns_unavailable(self):
        mock_insight = MagicMock()
        mock_insight.detect_anomalies.side_effect = RuntimeError("DB down")
        engine = AnomalyResponseEngine(db_url=None, insight_engine=mock_insight)
        result = engine.full_response_cycle()
        assert result["available"] is False
        assert result["recommendations"] == []

    def test_full_cycle_overall_severity_forwarded(self):
        engine = self._engine_with_mock_insight(["ESCALATION_SURGE"], severity="HIGH")
        result = engine.full_response_cycle()
        assert result["overall_severity"] == "MEDIUM"

    def test_full_cycle_recommendations_have_action_code(self):
        engine = self._engine_with_mock_insight(["BS_HIGH_SURGE"])
        result = engine.full_response_cycle()
        rec = result["recommendations"][0]
        assert rec["action_code"] == ACTION_MONITOR_BS_LEVELS

    def test_full_cycle_recommendations_are_reversible(self):
        engine = self._engine_with_mock_insight(["BLOCK_RATE_DROP"])
        result = engine.full_response_cycle()
        assert result["recommendations"][0]["is_reversible"] is True


# ══════════════════════════════════════════════════════════════════════════════
# T10 — get_response_engine() factory
# ══════════════════════════════════════════════════════════════════════════════

class TestFactory:

    def test_get_response_engine_returns_engine(self):
        engine = get_response_engine()
        assert isinstance(engine, AnomalyResponseEngine)

    def test_get_response_engine_with_insight(self):
        mock_insight = MagicMock()
        engine = get_response_engine(insight_engine=mock_insight)
        assert engine._insight is mock_insight

    def test_get_response_engine_with_db_url(self):
        engine = get_response_engine(db_url="postgresql://x:5432/y")
        assert engine.db_url == "postgresql://x:5432/y"
