"""
Phase 4 — CalibrationInsightEngine tests (ADR-128)

All tests run without a real DB. The FilterCalibrationMetricsService is
replaced by a MockMetricsService that returns controlled data.

Run:
    TESTING=true TELEGRAM_BOT_TOKEN=test-token \
        python -m pytest tests/test_phase4_calibration_insight.py -v --tb=short
"""

import os
import sys
import pytest

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import MagicMock, patch
from omnix_core.governance.calibration_insight import (
    CalibrationInsightEngine,
    CalibrationAnomaly,
    get_insight_engine,
    _avg_hold_rate,
    _avg_pass_rate,
    _avg_block_rate,
    _classify_trend,
    _upgrade_severity,
    _build_summary,
    _overall_severity,
    BLOCK_RATE_DROP_THRESHOLD,
    HOLD_SPIKE_THRESHOLD,
    DCI_SURGE_THRESHOLD,
    COHERENCE_DRIFT_THRESHOLD,
    BS_HIGH_SURGE_THRESHOLD,
    ESCALATION_SURGE_THRESHOLD,
)


# ── Mock service builder ──────────────────────────────────────────────────────

def _make_gate_stats(
    block_rate: float = 0.30,
    pass_rate:  float = 0.65,
    hold_rate:  float = 0.05,
    total:      int   = 100,
) -> dict:
    """Build a gate_stats dict as returned by query_all_gate_stats()."""
    eligible = total
    return {
        gate: {
            "gate": gate, "window": "1d", "domain": None,
            "total": total, "eligible": eligible,
            "pass_count":  int(pass_rate * eligible),  "pass_rate":  pass_rate,
            "block_count": int(block_rate * eligible), "block_rate": block_rate,
            "hold_count":  int(hold_rate * eligible),  "hold_rate":  hold_rate,
            "skip_count":  0,
        }
        for gate in (
            "layer0", "cag", "coherence", "mc", "black_swan",
            "ecw", "sharia", "aml", "fraud", "jurisdiction",
        )
    }


def _make_dci(avg: float = 30.0, p50: float = 28.0, p90: float = 55.0,
              total: int = 80) -> dict:
    return {
        "window": "1d", "domain": None, "total_with_dci": total,
        "avg": avg, "min": 0.0, "max": 95.0, "p50": p50, "p90": p90,
        "aligned_count": 50, "aligned_rate": 0.625,
        "tensioned_count": 20, "tensioned_rate": 0.25,
        "contradictory_count": 10, "contradictory_rate": 0.125,
    }


def _make_bs(high_rate: float = 0.05, total: int = 100) -> dict:
    high_c = int(high_rate * total)
    low_c  = int(0.15 * total)
    none_c = total - high_c - low_c
    return {
        "window": "1d", "domain": None, "total": total,
        "none_count": none_c, "none_rate": none_c / total,
        "low_count":  low_c,  "low_rate":  0.15,
        "high_count": high_c, "high_rate": high_rate,
        "unknown_count": 0,
    }


def _make_esc(esc_rate: float = 0.02, total: int = 100) -> dict:
    esc_c = int(esc_rate * total)
    return {
        "window": "1d", "domain": None,
        "total": total,
        "escalation_count":    esc_c,
        "escalation_rate":     esc_rate,
        "escalation_blocked":  esc_c,
        "escalation_approved": 0,
    }


def _make_service(
    gate_stats_fn=None,
    dci_fn=None,
    bs_fn=None,
    esc_fn=None,
    raise_on_call: bool = False,
) -> MagicMock:
    """Build a mock FilterCalibrationMetricsService."""
    svc = MagicMock()
    svc.db_url = "postgresql://mock:5432/mock"

    if raise_on_call:
        svc.query_all_gate_stats.side_effect = RuntimeError("No DB")
        svc.query_dci_distribution.side_effect = RuntimeError("No DB")
        svc.query_black_swan_frequency.side_effect = RuntimeError("No DB")
        svc.query_escalation_events.side_effect = RuntimeError("No DB")
    else:
        svc.query_all_gate_stats.side_effect = gate_stats_fn or (lambda **kw: _make_gate_stats())
        svc.query_dci_distribution.side_effect = dci_fn or (lambda **kw: _make_dci())
        svc.query_black_swan_frequency.side_effect = bs_fn or (lambda **kw: _make_bs())
        svc.query_escalation_events.side_effect = esc_fn or (lambda **kw: _make_esc())

    return svc


# ══════════════════════════════════════════════════════════════════════════════
# T01 — CalibrationAnomaly dataclass
# ══════════════════════════════════════════════════════════════════════════════

class TestCalibrationAnomaly:

    def test_to_dict_has_required_keys(self):
        a = CalibrationAnomaly(
            anomaly_type="BLOCK_RATE_DROP", severity="MEDIUM", domain="trading",
            description="test", current_value=0.1, baseline_value=0.3,
            deviation=0.2, threshold=0.15,
            window_current="1h", window_baseline="1d",
            detected_at="2026-04-25T00:00:00+00:00",
        )
        d = a.to_dict()
        assert d["anomaly_type"]    == "BLOCK_RATE_DROP"
        assert d["severity"]        == "MEDIUM"
        assert d["domain"]          == "trading"
        assert d["deviation"]       == 0.2
        assert d["threshold"]       == 0.15
        assert d["window_current"]  == "1h"
        assert d["window_baseline"] == "1d"

    def test_to_dict_rounds_floats(self):
        a = CalibrationAnomaly(
            anomaly_type="DCI_SURGE", severity="HIGH", domain=None,
            description="d", current_value=40.123456, baseline_value=30.0,
            deviation=10.123456, threshold=10.0,
            window_current="1h", window_baseline="1d",
            detected_at="2026-04-25T00:00:00+00:00",
        )
        d = a.to_dict()
        assert len(str(d["current_value"]).split(".")[-1]) <= 4


# ══════════════════════════════════════════════════════════════════════════════
# T02 — Threshold constants sanity
# ══════════════════════════════════════════════════════════════════════════════

class TestThresholdConstants:

    def test_block_rate_drop_threshold(self):
        assert BLOCK_RATE_DROP_THRESHOLD == pytest.approx(0.15)

    def test_hold_spike_threshold(self):
        assert HOLD_SPIKE_THRESHOLD == pytest.approx(0.10)

    def test_dci_surge_threshold(self):
        assert DCI_SURGE_THRESHOLD == pytest.approx(10.0)

    def test_coherence_drift_threshold(self):
        assert COHERENCE_DRIFT_THRESHOLD == pytest.approx(10.0)

    def test_bs_high_surge_threshold(self):
        assert BS_HIGH_SURGE_THRESHOLD == pytest.approx(0.05)

    def test_escalation_surge_threshold(self):
        assert ESCALATION_SURGE_THRESHOLD == pytest.approx(0.05)


# ══════════════════════════════════════════════════════════════════════════════
# T03 — Helper functions
# ══════════════════════════════════════════════════════════════════════════════

class TestHelpers:

    def test_avg_hold_rate_normal(self):
        stats = _make_gate_stats(hold_rate=0.08)
        result = _avg_hold_rate(stats)
        assert abs(result - 0.08) < 0.001

    def test_avg_hold_rate_empty(self):
        assert _avg_hold_rate({}) == 0.0

    def test_avg_pass_rate_normal(self):
        stats = _make_gate_stats(pass_rate=0.70)
        result = _avg_pass_rate(stats)
        assert abs(result - 0.70) < 0.001

    def test_avg_block_rate_normal(self):
        stats = _make_gate_stats(block_rate=0.25)
        result = _avg_block_rate(stats)
        assert abs(result - 0.25) < 0.001

    def test_avg_block_rate_no_eligible(self):
        stats = {"g": {"eligible": 0, "block_rate": 0.5}}
        assert _avg_block_rate(stats) == 0.0

    def test_classify_trend_rising(self):
        assert _classify_trend(15.0, threshold=5.0) == "RISING"

    def test_classify_trend_falling(self):
        assert _classify_trend(-8.0, threshold=5.0) == "FALLING"

    def test_classify_trend_stable(self):
        assert _classify_trend(2.0, threshold=5.0) == "STABLE"

    def test_classify_trend_unknown_none(self):
        assert _classify_trend(None, threshold=5.0) == "UNKNOWN"

    def test_upgrade_severity_medium_to_high(self):
        assert _upgrade_severity("MEDIUM") == "HIGH"

    def test_upgrade_severity_high_to_critical(self):
        assert _upgrade_severity("HIGH") == "CRITICAL"

    def test_upgrade_severity_critical_unchanged(self):
        assert _upgrade_severity("CRITICAL") == "CRITICAL"

    def test_build_summary_counts(self):
        dicts = [
            {"severity": "HIGH"},
            {"severity": "MEDIUM"},
            {"severity": "CRITICAL"},
        ]
        s = _build_summary(dicts)
        assert s["total"]    == 3
        assert s["critical"] == 1
        assert s["high"]     == 1
        assert s["medium"]   == 1

    def test_overall_severity_critical(self):
        assert _overall_severity({"critical": 1, "high": 0, "medium": 0, "low": 0}, 1) == "CRITICAL"

    def test_overall_severity_none(self):
        assert _overall_severity({"critical": 0, "high": 0, "medium": 0, "low": 0}, 0) == "NONE"

    def test_overall_severity_high(self):
        assert _overall_severity({"critical": 0, "high": 2, "medium": 0, "low": 0}, 2) == "HIGH"


# ══════════════════════════════════════════════════════════════════════════════
# T04 — CalibrationInsightEngine construction
# ══════════════════════════════════════════════════════════════════════════════

class TestEngineConstruction:

    def test_init_with_service(self):
        svc = _make_service()
        engine = CalibrationInsightEngine(svc)
        assert engine._svc is svc

    def test_init_without_service_creates_default(self):
        engine = CalibrationInsightEngine(db_url="postgresql://x:5432/y")
        assert engine._svc is not None

    def test_get_insight_engine_with_service(self):
        svc = _make_service()
        engine = get_insight_engine(svc)
        assert engine._svc is svc


# ══════════════════════════════════════════════════════════════════════════════
# T05 — snapshot()
# ══════════════════════════════════════════════════════════════════════════════

class TestSnapshot:

    def _engine_with_db_patch(self, svc):
        engine = CalibrationInsightEngine(svc)
        conn_mock = MagicMock()
        row_mock = (200, 140, 50, 10)
        conn_mock.cursor.return_value.fetchone.return_value = row_mock
        engine._query_decision_summary = MagicMock(return_value={
            "total": 200, "APPROVED": 140, "BLOCKED": 50, "HOLD": 10,
        })
        return engine

    def test_snapshot_returns_available_true(self):
        svc = _make_service()
        engine = self._engine_with_db_patch(svc)
        result = engine.snapshot(window="1d")
        assert result["available"] is True

    def test_snapshot_has_gate_stats(self):
        svc = _make_service()
        engine = self._engine_with_db_patch(svc)
        result = engine.snapshot(window="1d")
        assert "gate_stats" in result
        assert len(result["gate_stats"]) == 10  # 10 gates

    def test_snapshot_has_decision_summary(self):
        svc = _make_service()
        engine = self._engine_with_db_patch(svc)
        result = engine.snapshot(window="1d")
        assert "decision_summary" in result
        assert result["decision_summary"]["APPROVED"] == 140

    def test_snapshot_unavailable_on_db_error(self):
        svc = _make_service(raise_on_call=True)
        engine = CalibrationInsightEngine(svc)
        result = engine.snapshot(window="1d")
        assert result["available"] is False
        assert result["gate_stats"] == {}

    def test_snapshot_window_forwarded(self):
        svc = _make_service()
        engine = self._engine_with_db_patch(svc)
        result = engine.snapshot(window="1w")
        assert result["window"] == "1w"

    def test_snapshot_domain_forwarded(self):
        svc = _make_service()
        engine = self._engine_with_db_patch(svc)
        result = engine.snapshot(domain="trading", window="1d")
        assert result["domain"] == "trading"


# ══════════════════════════════════════════════════════════════════════════════
# T06 — dci_trend()
# ══════════════════════════════════════════════════════════════════════════════

class TestDciTrend:

    def test_dci_trend_stable(self):
        svc = _make_service(dci_fn=lambda **kw: _make_dci(avg=30.0))
        engine = CalibrationInsightEngine(svc)
        result = engine.dci_trend()
        assert result["trend_direction"] == "STABLE"
        assert result["available"] is True

    def test_dci_trend_rising_detected(self):
        """1h avg 20pts higher than 1d → RISING."""
        def dci_by_window(**kw):
            w = kw.get("window", "1d")
            return _make_dci(avg=50.0 if w == "1h" else 30.0)

        svc = _make_service(dci_fn=dci_by_window)
        engine = CalibrationInsightEngine(svc)
        result = engine.dci_trend()
        assert result["trend_direction"] == "RISING"
        assert result["delta_1h_vs_1d"] == pytest.approx(20.0)

    def test_dci_trend_falling_detected(self):
        def dci_by_window(**kw):
            w = kw.get("window", "1d")
            return _make_dci(avg=10.0 if w == "1h" else 30.0)

        svc = _make_service(dci_fn=dci_by_window)
        engine = CalibrationInsightEngine(svc)
        result = engine.dci_trend()
        assert result["trend_direction"] == "FALLING"

    def test_dci_trend_all_windows_present(self):
        svc = _make_service()
        engine = CalibrationInsightEngine(svc)
        result = engine.dci_trend()
        assert "1h" in result["windows"]
        assert "1d" in result["windows"]
        assert "1w" in result["windows"]

    def test_dci_trend_delta_none_when_no_data(self):
        svc = _make_service(dci_fn=lambda **kw: _make_dci(avg=None, total=0))
        engine = CalibrationInsightEngine(svc)
        result = engine.dci_trend()
        assert result["delta_1h_vs_1d"] is None

    def test_dci_trend_available_false_on_error(self):
        svc = _make_service(raise_on_call=True)
        engine = CalibrationInsightEngine(svc)
        result = engine.dci_trend()
        assert result["available"] is False


# ══════════════════════════════════════════════════════════════════════════════
# T07 — coherence_distribution()
# ══════════════════════════════════════════════════════════════════════════════

class TestCoherenceDistribution:

    def _engine_with_coh_patch(self, coh_return: dict):
        svc = _make_service()
        engine = CalibrationInsightEngine(svc)
        engine._query_coherence_distribution = MagicMock(return_value=coh_return)
        return engine

    def test_coherence_distribution_keys(self):
        coh = {
            "window": "1d", "domain": None, "available": True,
            "total_with_coh": 80,
            "avg": 65.0, "min": 10.0, "max": 95.0, "p50": 62.0, "p90": 88.0,
            "high_count": 30,  "high_rate": 0.375,
            "medium_count": 40, "medium_rate": 0.50,
            "low_count": 10,   "low_rate": 0.125,
        }
        engine = self._engine_with_coh_patch(coh)
        result = engine.coherence_distribution(window="1d")
        assert result["available"] is True
        assert result["total_with_coh"] == 80
        assert "high_rate" in result
        assert "medium_rate" in result
        assert "low_rate" in result

    def test_coherence_distribution_unavailable_on_error(self):
        svc = _make_service()
        engine = CalibrationInsightEngine(svc)
        engine._query_coherence_distribution = MagicMock(
            side_effect=RuntimeError("No DB")
        )
        result = engine.coherence_distribution(window="1d")
        assert result["available"] is False
        assert result["total_with_coh"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# T08 — bs_trend()
# ══════════════════════════════════════════════════════════════════════════════

class TestBsTrend:

    def test_bs_trend_stable(self):
        svc = _make_service(bs_fn=lambda **kw: _make_bs(high_rate=0.05))
        engine = CalibrationInsightEngine(svc)
        result = engine.bs_trend()
        assert result["trend_direction"] == "STABLE"
        assert result["available"] is True

    def test_bs_trend_rising(self):
        def bs_by_window(**kw):
            w = kw.get("window", "1d")
            return _make_bs(high_rate=0.20 if w == "1h" else 0.05)

        svc = _make_service(bs_fn=bs_by_window)
        engine = CalibrationInsightEngine(svc)
        result = engine.bs_trend()
        assert result["trend_direction"] == "RISING"
        assert result["delta_high_1h_vs_1d"] == pytest.approx(0.15, abs=0.001)

    def test_bs_trend_all_windows_present(self):
        svc = _make_service()
        engine = CalibrationInsightEngine(svc)
        result = engine.bs_trend()
        for w in ("1h", "1d", "1w"):
            assert w in result["windows"]

    def test_bs_trend_unavailable_on_error(self):
        svc = _make_service(raise_on_call=True)
        engine = CalibrationInsightEngine(svc)
        result = engine.bs_trend()
        assert result["available"] is False


# ══════════════════════════════════════════════════════════════════════════════
# T09 — detect_anomalies()
# ══════════════════════════════════════════════════════════════════════════════

class TestDetectAnomalies:

    def _engine_no_anomalies(self):
        """Engine whose data produces zero anomalies."""
        def gate_stats(**kw):
            return _make_gate_stats(block_rate=0.30, hold_rate=0.03)

        def dci(**kw):
            w = kw.get("window", "1d")
            return _make_dci(avg=30.0)

        def bs(**kw):
            return _make_bs(high_rate=0.04)

        def esc(**kw):
            return _make_esc(esc_rate=0.01)

        svc = _make_service(gate_stats_fn=gate_stats, dci_fn=dci, bs_fn=bs, esc_fn=esc)
        engine = CalibrationInsightEngine(svc)
        engine._query_coherence_distribution = MagicMock(
            return_value={
                "window": "1h", "domain": None, "available": True,
                "total_with_coh": 100, "avg": 65.0,
                "min": 10.0, "max": 95.0, "p50": 62.0, "p90": 88.0,
                "high_count": 60, "high_rate": 0.60,
                "medium_count": 30, "medium_rate": 0.30,
                "low_count": 10, "low_rate": 0.10,
            }
        )
        return engine

    def test_no_anomalies_normal_data(self):
        engine = self._engine_no_anomalies()
        result = engine.detect_anomalies()
        assert result["available"] is True
        assert result["overall_severity"] == "NONE"
        assert len(result["anomalies"]) == 0

    def test_block_rate_drop_detected(self):
        """Coherence block_rate: 1h=0.05, 1d=0.30 → drop=0.25 > 0.15 threshold."""
        call_count = {"n": 0}
        def gate_stats(**kw):
            w = kw.get("window", "1d")
            block = 0.05 if w == "1h" else 0.30
            return _make_gate_stats(block_rate=block, hold_rate=0.02)

        svc = _make_service(gate_stats_fn=gate_stats)
        engine = CalibrationInsightEngine(svc)
        engine._query_coherence_distribution = MagicMock(return_value={
            "window": "1h", "domain": None, "available": True,
            "total_with_coh": 100, "avg": 65.0,
            "min": 10.0, "max": 95.0, "p50": 62.0, "p90": 88.0,
            "high_count": 60, "high_rate": 0.60,
            "medium_count": 30, "medium_rate": 0.30,
            "low_count": 10, "low_rate": 0.10,
        })
        result = engine.detect_anomalies()
        types = [a["anomaly_type"] for a in result["anomalies"]]
        assert "BLOCK_RATE_DROP" in types

    def test_hold_spike_detected(self):
        """Average hold_rate: 1h=0.25, 1d=0.05 → delta=0.20 > 0.10 threshold."""
        def gate_stats(**kw):
            w = kw.get("window", "1d")
            hold = 0.25 if w == "1h" else 0.05
            return _make_gate_stats(block_rate=0.30, hold_rate=hold)

        svc = _make_service(gate_stats_fn=gate_stats)
        engine = CalibrationInsightEngine(svc)
        engine._query_coherence_distribution = MagicMock(return_value={
            "window": "1h", "domain": None, "available": True,
            "total_with_coh": 100, "avg": 65.0,
            "min": 10.0, "max": 95.0, "p50": 62.0, "p90": 88.0,
            "high_count": 60, "high_rate": 0.60,
            "medium_count": 30, "medium_rate": 0.30,
            "low_count": 10, "low_rate": 0.10,
        })
        result = engine.detect_anomalies()
        types = [a["anomaly_type"] for a in result["anomalies"]]
        assert "HOLD_SPIKE" in types

    def test_dci_surge_detected(self):
        """1h avg DCI=55, 1d avg DCI=30 → delta=25 > 10 threshold."""
        def dci(**kw):
            w = kw.get("window", "1d")
            return _make_dci(avg=55.0 if w == "1h" else 30.0)

        svc = _make_service(dci_fn=dci)
        engine = CalibrationInsightEngine(svc)
        engine._query_coherence_distribution = MagicMock(return_value={
            "window": "1h", "domain": None, "available": True,
            "total_with_coh": 100, "avg": 65.0,
            "min": 10.0, "max": 95.0, "p50": 62.0, "p90": 88.0,
            "high_count": 60, "high_rate": 0.60,
            "medium_count": 30, "medium_rate": 0.30,
            "low_count": 10, "low_rate": 0.10,
        })
        result = engine.detect_anomalies()
        types = [a["anomaly_type"] for a in result["anomalies"]]
        assert "DCI_SURGE" in types

    def test_coherence_drift_detected(self):
        """1h avg coh=40, 1d avg coh=65 → drift=25 > 10 threshold."""
        def coh_dist(**kw):
            w = kw.get("window", "1d")
            avg = 40.0 if w == "1h" else 65.0
            return {
                "window": w, "domain": None, "available": True,
                "total_with_coh": 100, "avg": avg,
                "min": 10.0, "max": 95.0, "p50": avg, "p90": avg + 10,
                "high_count": 30, "high_rate": 0.30,
                "medium_count": 50, "medium_rate": 0.50,
                "low_count": 20, "low_rate": 0.20,
            }

        svc = _make_service()
        engine = CalibrationInsightEngine(svc)
        engine._query_coherence_distribution = MagicMock(side_effect=coh_dist)
        result = engine.detect_anomalies()
        types = [a["anomaly_type"] for a in result["anomalies"]]
        assert "COHERENCE_DRIFT" in types

    def test_bs_high_surge_detected(self):
        """1h BS_HIGH rate=0.25, 1d=0.04 → delta=0.21 > 0.05 threshold."""
        def bs(**kw):
            w = kw.get("window", "1d")
            return _make_bs(high_rate=0.25 if w == "1h" else 0.04)

        svc = _make_service(bs_fn=bs)
        engine = CalibrationInsightEngine(svc)
        engine._query_coherence_distribution = MagicMock(return_value={
            "window": "1h", "domain": None, "available": True,
            "total_with_coh": 100, "avg": 65.0,
            "min": 10.0, "max": 95.0, "p50": 62.0, "p90": 88.0,
            "high_count": 60, "high_rate": 0.60,
            "medium_count": 30, "medium_rate": 0.30,
            "low_count": 10, "low_rate": 0.10,
        })
        result = engine.detect_anomalies()
        types = [a["anomaly_type"] for a in result["anomalies"]]
        assert "BS_HIGH_SURGE" in types

    def test_escalation_surge_detected(self):
        """1h esc_rate=0.20, 1d=0.01 → delta=0.19 > 0.05 threshold."""
        def esc(**kw):
            w = kw.get("window", "1d")
            return _make_esc(esc_rate=0.20 if w == "1h" else 0.01)

        svc = _make_service(esc_fn=esc)
        engine = CalibrationInsightEngine(svc)
        engine._query_coherence_distribution = MagicMock(return_value={
            "window": "1h", "domain": None, "available": True,
            "total_with_coh": 100, "avg": 65.0,
            "min": 10.0, "max": 95.0, "p50": 62.0, "p90": 88.0,
            "high_count": 60, "high_rate": 0.60,
            "medium_count": 30, "medium_rate": 0.30,
            "low_count": 10, "low_rate": 0.10,
        })
        result = engine.detect_anomalies()
        types = [a["anomaly_type"] for a in result["anomalies"]]
        assert "ESCALATION_SURGE" in types

    def test_anomaly_result_structure(self):
        engine = self._engine_no_anomalies()
        result = engine.detect_anomalies()
        assert "anomalies" in result
        assert "summary" in result
        assert "overall_severity" in result
        assert "analyzed_at" in result
        assert "available" in result
        assert "domain" in result

    def test_summary_counts_match_anomaly_list(self):
        def gate_stats(**kw):
            w = kw.get("window", "1d")
            block = 0.05 if w == "1h" else 0.30
            hold  = 0.25 if w == "1h" else 0.03
            return _make_gate_stats(block_rate=block, hold_rate=hold)

        svc = _make_service(gate_stats_fn=gate_stats)
        engine = CalibrationInsightEngine(svc)
        engine._query_coherence_distribution = MagicMock(return_value={
            "window": "1h", "domain": None, "available": True,
            "total_with_coh": 100, "avg": 65.0,
            "min": 10.0, "max": 95.0, "p50": 62.0, "p90": 88.0,
            "high_count": 60, "high_rate": 0.60,
            "medium_count": 30, "medium_rate": 0.30,
            "low_count": 10, "low_rate": 0.10,
        })
        result = engine.detect_anomalies()
        total_in_summary = sum(result["summary"][k] for k in ("critical", "high", "medium", "low"))
        assert total_in_summary == len(result["anomalies"])

    def test_unavailable_on_service_error(self):
        svc = _make_service(raise_on_call=True)
        engine = CalibrationInsightEngine(svc)
        engine._query_coherence_distribution = MagicMock(
            side_effect=RuntimeError("No DB")
        )
        result = engine.detect_anomalies()
        assert result["available"] is False
        assert result["anomalies"] == []

    def test_anomaly_description_non_empty(self):
        def gate_stats(**kw):
            w = kw.get("window", "1d")
            return _make_gate_stats(block_rate=0.05 if w == "1h" else 0.30)

        svc = _make_service(gate_stats_fn=gate_stats)
        engine = CalibrationInsightEngine(svc)
        engine._query_coherence_distribution = MagicMock(return_value={
            "window": "1h", "domain": None, "available": True,
            "total_with_coh": 100, "avg": 65.0,
            "min": 10.0, "max": 95.0, "p50": 62.0, "p90": 88.0,
            "high_count": 60, "high_rate": 0.60,
            "medium_count": 30, "medium_rate": 0.30,
            "low_count": 10, "low_rate": 0.10,
        })
        result = engine.detect_anomalies()
        for anomaly in result["anomalies"]:
            assert len(anomaly["description"]) > 10


# ══════════════════════════════════════════════════════════════════════════════
# T10 — domain_comparison()
# ══════════════════════════════════════════════════════════════════════════════

class TestDomainComparison:

    def test_domain_comparison_all_domains_present(self):
        svc = _make_service()
        engine = CalibrationInsightEngine(svc)
        domains = ["trading", "credit", "insurance"]
        result = engine.domain_comparison(domains, window="1d")
        for d in domains:
            assert d in result["domains"]

    def test_domain_comparison_has_key_metrics(self):
        svc = _make_service()
        engine = CalibrationInsightEngine(svc)
        result = engine.domain_comparison(["trading"], window="1d")
        trading = result["domains"]["trading"]
        assert "pass_rate"        in trading
        assert "block_rate"       in trading
        assert "hold_rate"        in trading
        assert "avg_dci"          in trading
        assert "bs_high_rate"     in trading
        assert "escalation_rate"  in trading

    def test_domain_comparison_available_true(self):
        svc = _make_service()
        engine = CalibrationInsightEngine(svc)
        result = engine.domain_comparison(["trading"])
        assert result["domains"]["trading"]["available"] is True

    def test_domain_comparison_available_false_on_error(self):
        svc = _make_service(raise_on_call=True)
        engine = CalibrationInsightEngine(svc)
        result = engine.domain_comparison(["trading"])
        assert result["domains"]["trading"]["available"] is False

    def test_domain_comparison_window_forwarded(self):
        svc = _make_service()
        engine = CalibrationInsightEngine(svc)
        result = engine.domain_comparison(["trading"], window="1w")
        assert result["window"] == "1w"


# ══════════════════════════════════════════════════════════════════════════════
# T11 — full_report()
# ══════════════════════════════════════════════════════════════════════════════

class TestFullReport:

    def _engine_for_full_report(self):
        svc = _make_service()
        engine = CalibrationInsightEngine(svc)
        engine._query_coherence_distribution = MagicMock(return_value={
            "window": "1d", "domain": None, "available": True,
            "total_with_coh": 100, "avg": 65.0,
            "min": 10.0, "max": 95.0, "p50": 62.0, "p90": 88.0,
            "high_count": 60, "high_rate": 0.60,
            "medium_count": 30, "medium_rate": 0.30,
            "low_count": 10, "low_rate": 0.10,
        })
        engine._query_decision_summary = MagicMock(return_value={
            "total": 200, "APPROVED": 140, "BLOCKED": 50, "HOLD": 10,
        })
        return engine

    def test_full_report_top_level_keys(self):
        engine = self._engine_for_full_report()
        result = engine.full_report(domain="trading", window="1d")
        for key in ("domain", "window", "available", "snapshot", "dci_trend",
                    "coherence", "bs_trend", "anomalies", "generated_at"):
            assert key in result

    def test_full_report_domain_forwarded(self):
        engine = self._engine_for_full_report()
        result = engine.full_report(domain="credit", window="1d")
        assert result["domain"] == "credit"

    def test_full_report_window_forwarded(self):
        engine = self._engine_for_full_report()
        result = engine.full_report(window="1w")
        assert result["window"] == "1w"

    def test_full_report_anomalies_is_dict(self):
        engine = self._engine_for_full_report()
        result = engine.full_report()
        assert isinstance(result["anomalies"], dict)
        assert "anomalies" in result["anomalies"]
