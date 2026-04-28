"""
ADR-134 — Governance Oscillation & Hesitation Asymmetry Engine
Test suite — 35 tests

Groups:
  T01–T05  Import, instantiation, pure helpers
  T06–T10  oscillation_profile() pattern classification
  T11–T15  phase_segmented_analysis() boundary detection
  T16–T20  hesitation_asymmetry() coefficient & interpretation
  T21–T25  dampening_curve() direction classification
  T26–T30  oscillation_report() full + executive summary
  T31–T35  Edge cases & fail-safe behaviour
"""

import math
import os
import sys
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from omnix_core.governance.oscillation_insight import (
    DAMPENING_AMPLITUDE_DELTA,
    HIGH_OSCILLATION_STD,
    LATENCY_ASYMMETRY_THRESHOLD,
    MIN_DECISIONS_PER_WINDOW,
    MIN_WINDOWS_FOR_OSCILLATION,
    OSCILLATION_STD_THRESHOLD,
    PHASE_BOUNDARY_THRESHOLD,
    OscillationInsightEngine,
    PhaseSegment,
    WeeklyHoldWindow,
    _canonical_decision,
    _linear_slope,
    get_oscillation_engine,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_window(
    offset: int,
    hold_rate: float,
    total: int = 100,
    block_rate: float = 0.20,
    approved_rate: float = None,
) -> WeeklyHoldWindow:
    ar = approved_rate if approved_rate is not None else round(1.0 - hold_rate - block_rate, 4)
    return WeeklyHoldWindow(
        week_offset   = offset,
        week_start    = f"2026-03-{(10 + offset):02d}T00:00:00+00:00",
        week_end      = f"2026-03-{(17 + offset):02d}T00:00:00+00:00",
        total         = total,
        hold_count    = int(hold_rate * total),
        hold_rate     = hold_rate,
        block_rate    = block_rate,
        approved_rate = ar,
    )


def _engine_with_mock_windows(windows: List[WeeklyHoldWindow]) -> OscillationInsightEngine:
    engine = OscillationInsightEngine(db_url="mock://")
    engine._fetch_weekly_windows = MagicMock(return_value=windows)
    return engine


def _engine_with_mock_latency(latency: Dict[str, Any]) -> OscillationInsightEngine:
    engine = OscillationInsightEngine(db_url="mock://")
    engine._fetch_latency_by_decision_type = MagicMock(return_value=latency)
    return engine


# ── T01–T05: Import, instantiation, helpers ───────────────────────────────────

def test_T01_import_module():
    from omnix_core.governance import oscillation_insight
    assert hasattr(oscillation_insight, "OscillationInsightEngine")


def test_T02_instantiation():
    engine = OscillationInsightEngine(db_url="postgresql://mock/db")
    assert engine is not None
    assert engine._db_url == "postgresql://mock/db"


def test_T03_get_oscillation_engine_factory():
    with patch.dict(os.environ, {"OMNIX_DB_URL": "postgresql://mock/db"}):
        engine = get_oscillation_engine()
        assert isinstance(engine, OscillationInsightEngine)


def test_T04_linear_slope_basic():
    slope = _linear_slope([1.0, 2.0, 3.0, 4.0])
    assert slope is not None
    assert slope > 0, "Rising series should have positive slope"


def test_T05_canonical_decision_normalisation():
    assert _canonical_decision("APPROVED") == "APPROVED"
    assert _canonical_decision("APPROVE")  == "APPROVED"
    assert _canonical_decision("PASS")     == "APPROVED"
    assert _canonical_decision("BLOCKED")  == "BLOCKED"
    assert _canonical_decision("BLOCK")    == "BLOCKED"
    assert _canonical_decision("HOLD")     == "HOLD"
    assert _canonical_decision("DEFER")    == "HOLD"


# ── T06–T10: oscillation_profile() ───────────────────────────────────────────

def test_T06_pattern_cycling():
    windows = [
        _make_window(i, hold_rate)
        for i, hold_rate in enumerate([0.90, 0.53, 0.87, 0.49, 0.92, 0.54, 0.88, 0.51])
    ]
    engine = _engine_with_mock_windows(windows)
    result = engine.oscillation_profile(domain="trading")
    assert result["available"] is True
    assert result["pattern"] == "CYCLING", f"Expected CYCLING, got {result['pattern']}"
    assert result["statistics"]["std_dev"] >= OSCILLATION_STD_THRESHOLD


def test_T07_pattern_stable():
    windows = [_make_window(i, 0.62) for i in range(6)]
    engine = _engine_with_mock_windows(windows)
    result = engine.oscillation_profile()
    assert result["pattern"] == "STABLE"
    assert result["statistics"]["std_dev"] < OSCILLATION_STD_THRESHOLD


def test_T08_pattern_drifting():
    windows = [_make_window(i, 0.40 + i * 0.06) for i in range(6)]
    engine = _engine_with_mock_windows(windows)
    result = engine.oscillation_profile()
    assert result["pattern"] == "DRIFTING"


def test_T09_pattern_insufficient_data():
    windows = [_make_window(i, 0.60) for i in range(2)]
    engine = _engine_with_mock_windows(windows)
    result = engine.oscillation_profile()
    assert result["pattern"] == "INSUFFICIENT_DATA"


def test_T10_profile_statistics_correct():
    rates = [0.50, 0.60, 0.70, 0.80, 0.50, 0.60, 0.70, 0.80]
    windows = [_make_window(i, r) for i, r in enumerate(rates)]
    engine = _engine_with_mock_windows(windows)
    result = engine.oscillation_profile()
    stats = result["statistics"]
    assert stats["min_hold_rate"] == pytest.approx(0.50, abs=0.001)
    assert stats["max_hold_rate"] == pytest.approx(0.80, abs=0.001)
    assert stats["amplitude"]     == pytest.approx(0.30, abs=0.001)
    assert stats["valid_windows"] == 8


# ── T11–T15: phase_segmented_analysis() ──────────────────────────────────────

def test_T11_no_boundary_detected():
    windows = [_make_window(i, 0.60 + i * 0.01) for i in range(6)]
    engine = _engine_with_mock_windows(windows)
    result = engine.phase_segmented_analysis()
    assert result["boundaries_detected"] == 0
    assert result["continuity_warning"] is False
    assert len(result["segments"]) == 1
    assert result["segments"][0]["phase"] == "BASELINE"


def test_T12_boundary_detected_on_large_shift():
    rates = [0.90, 0.91, 0.52, 0.53, 0.54, 0.55]
    windows = [_make_window(i, r) for i, r in enumerate(rates)]
    engine = _engine_with_mock_windows(windows)
    result = engine.phase_segmented_analysis(boundary_threshold=0.20)
    assert result["boundaries_detected"] >= 1
    assert result["continuity_warning"] is True


def test_T13_two_segments_built():
    rates = [0.92, 0.90, 0.53, 0.51, 0.50, 0.49]
    windows = [_make_window(i, r) for i, r in enumerate(rates)]
    engine = _engine_with_mock_windows(windows)
    result = engine.phase_segmented_analysis(boundary_threshold=0.20)
    assert len(result["segments"]) >= 2


def test_T14_phase_labels_assigned():
    rates = [0.90, 0.50, 0.52, 0.51]
    windows = [_make_window(i, r) for i, r in enumerate(rates)]
    engine = _engine_with_mock_windows(windows)
    result = engine.phase_segmented_analysis(boundary_threshold=0.20)
    phases = [s["phase"] for s in result["segments"]]
    assert any("PRE" in p or "BASELINE" in p or "POST" in p for p in phases)


def test_T15_segment_avg_hold_rate_correct():
    rates = [0.90, 0.90, 0.50, 0.50]
    windows = [_make_window(i, r) for i, r in enumerate(rates)]
    engine = _engine_with_mock_windows(windows)
    result = engine.phase_segmented_analysis(boundary_threshold=0.20)
    avgs = [s["avg_hold_rate"] for s in result["segments"]]
    assert any(a >= 0.85 for a in avgs) or any(a <= 0.55 for a in avgs)


# ── T16–T20: hesitation_asymmetry() ──────────────────────────────────────────

def test_T16_asymmetry_detected_when_hold_faster():
    latency = {
        "HOLD":    {"avg_ms": 120.0, "p50_ms": 115.0, "p90_ms": 140.0, "count": 80},
        "BLOCKED": {"avg_ms": 180.0, "p50_ms": 175.0, "p90_ms": 210.0, "count": 30},
        "APPROVED":{"avg_ms": 160.0, "p50_ms": 155.0, "p90_ms": 185.0, "count": 50},
    }
    engine = _engine_with_mock_latency(latency)
    engine._fetch_weekly_windows = MagicMock(return_value=[])
    result = engine.hesitation_asymmetry()
    assert result["available"] is True
    assert result["asymmetry_detected"] is True
    coeff = result["asymmetry_coefficient"]
    assert coeff == pytest.approx(120.0 / 180.0, abs=0.01)
    assert coeff < LATENCY_ASYMMETRY_THRESHOLD


def test_T17_no_asymmetry_when_hold_slower():
    latency = {
        "HOLD":    {"avg_ms": 200.0, "p50_ms": 195.0, "p90_ms": 230.0, "count": 60},
        "BLOCKED": {"avg_ms": 180.0, "p50_ms": 175.0, "p90_ms": 210.0, "count": 40},
        "APPROVED":{"avg_ms": 160.0, "p50_ms": 155.0, "p90_ms": 185.0, "count": 50},
    }
    engine = _engine_with_mock_latency(latency)
    result = engine.hesitation_asymmetry()
    assert result["asymmetry_detected"] is False
    assert result["asymmetry_coefficient"] >= 1.0


def test_T18_coefficient_none_when_no_block_data():
    latency = {
        "HOLD":    {"avg_ms": 120.0, "p50_ms": 115.0, "p90_ms": 140.0, "count": 80},
        "APPROVED":{"avg_ms": 160.0, "p50_ms": 155.0, "p90_ms": 185.0, "count": 50},
    }
    engine = _engine_with_mock_latency(latency)
    result = engine.hesitation_asymmetry()
    assert result["asymmetry_coefficient"] is None


def test_T19_interpretation_string_present():
    latency = {
        "HOLD":    {"avg_ms": 110.0, "p50_ms": 108.0, "p90_ms": 130.0, "count": 70},
        "BLOCKED": {"avg_ms": 190.0, "p50_ms": 185.0, "p90_ms": 215.0, "count": 30},
        "APPROVED":{"avg_ms": 160.0, "p50_ms": 155.0, "p90_ms": 185.0, "count": 50},
    }
    engine = _engine_with_mock_latency(latency)
    result = engine.hesitation_asymmetry()
    assert isinstance(result["asymmetry_interpretation"], str)
    assert len(result["asymmetry_interpretation"]) > 20


def test_T20_latency_by_type_keys_present():
    latency = {
        "HOLD":    {"avg_ms": 130.0, "p50_ms": 125.0, "p90_ms": 150.0, "count": 60},
        "BLOCKED": {"avg_ms": 160.0, "p50_ms": 155.0, "p90_ms": 185.0, "count": 40},
        "APPROVED":{"avg_ms": 140.0, "p50_ms": 135.0, "p90_ms": 165.0, "count": 55},
    }
    engine = _engine_with_mock_latency(latency)
    result = engine.hesitation_asymmetry()
    for key in ("HOLD", "BLOCKED", "APPROVED"):
        assert key in result["latency_by_type"]
        assert "avg_ms" in result["latency_by_type"][key]


# ── T21–T25: dampening_curve() ────────────────────────────────────────────────

def test_T21_dampening_detected():
    first_half  = [_make_window(i + 4, 0.50 + (i % 2) * 0.35) for i in range(4)]
    second_half = [_make_window(i,     0.60 + (i % 2) * 0.05) for i in range(4)]
    windows = second_half + first_half
    engine = _engine_with_mock_windows(windows)
    result = engine.dampening_curve(num_weeks=8)
    assert result["available"] is True
    assert result["curve_direction"] in ("DAMPENING", "STABLE", "AMPLIFYING")
    assert result["amplitude_delta"] is not None


def test_T22_dampening_direction_logic():
    first_half_windows  = [_make_window(i + 4, 0.90 if i % 2 == 0 else 0.50) for i in range(4)]
    second_half_windows = [_make_window(i,     0.62 if i % 2 == 0 else 0.58) for i in range(4)]
    windows = second_half_windows + first_half_windows
    engine = _engine_with_mock_windows(windows)
    result = engine.dampening_curve(num_weeks=8)
    assert result["curve_direction"] == "DAMPENING"
    assert result["amplitude_delta"] < 0


def test_T23_amplifying_direction():
    first_half_windows  = [_make_window(i + 4, 0.62 if i % 2 == 0 else 0.58) for i in range(4)]
    second_half_windows = [_make_window(i,     0.90 if i % 2 == 0 else 0.50) for i in range(4)]
    windows = second_half_windows + first_half_windows
    engine = _engine_with_mock_windows(windows)
    result = engine.dampening_curve(num_weeks=8)
    assert result["curve_direction"] == "AMPLIFYING"
    assert result["amplitude_delta"] > 0


def test_T24_stable_when_amplitude_unchanged():
    windows = [_make_window(i, 0.65) for i in range(8)]
    engine = _engine_with_mock_windows(windows)
    result = engine.dampening_curve(num_weeks=8)
    assert result["curve_direction"] == "STABLE"
    assert abs(result["amplitude_delta"]) <= DAMPENING_AMPLITUDE_DELTA


def test_T25_insufficient_data_dampening():
    windows = [_make_window(i, 0.60) for i in range(2)]
    engine = _engine_with_mock_windows(windows)
    result = engine.dampening_curve(num_weeks=2)
    assert result["curve_direction"] == "INSUFFICIENT_DATA"


# ── T26–T30: oscillation_report() ────────────────────────────────────────────

def test_T26_full_report_structure():
    windows = [_make_window(i, 0.62) for i in range(6)]
    latency = {
        "HOLD":    {"avg_ms": 160.0, "p50_ms": 155.0, "p90_ms": 185.0, "count": 60},
        "BLOCKED": {"avg_ms": 170.0, "p50_ms": 165.0, "p90_ms": 195.0, "count": 40},
        "APPROVED":{"avg_ms": 150.0, "p50_ms": 145.0, "p90_ms": 175.0, "count": 55},
    }
    engine = OscillationInsightEngine(db_url="mock://")
    engine._fetch_weekly_windows = MagicMock(return_value=windows)
    engine._fetch_latency_by_decision_type = MagicMock(return_value=latency)
    result = engine.oscillation_report(domain="trading")
    for key in ("oscillation_profile", "phase_segmented", "hesitation_asymmetry",
                "dampening_curve", "executive_summary"):
        assert key in result, f"Missing key: {key}"


def test_T27_executive_summary_has_risk_level():
    windows = [_make_window(i, 0.62) for i in range(6)]
    latency = {"HOLD": {"avg_ms": 160.0, "count": 60},
               "BLOCKED": {"avg_ms": 170.0, "count": 40}}
    engine = OscillationInsightEngine(db_url="mock://")
    engine._fetch_weekly_windows = MagicMock(return_value=windows)
    engine._fetch_latency_by_decision_type = MagicMock(return_value=latency)
    result = engine.oscillation_report()
    summary = result["executive_summary"]
    assert "risk_level" in summary
    assert summary["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")


def test_T28_critical_risk_on_dampening_plus_asymmetry():
    first_half  = [_make_window(i + 4, 0.90 if i % 2 == 0 else 0.50) for i in range(4)]
    second_half = [_make_window(i,     0.63 if i % 2 == 0 else 0.61) for i in range(4)]
    windows = second_half + first_half
    latency = {
        "HOLD":    {"avg_ms": 110.0, "p50_ms": 108.0, "p90_ms": 130.0, "count": 80},
        "BLOCKED": {"avg_ms": 200.0, "p50_ms": 195.0, "p90_ms": 230.0, "count": 30},
        "APPROVED":{"avg_ms": 160.0, "p50_ms": 155.0, "p90_ms": 185.0, "count": 50},
    }
    engine = OscillationInsightEngine(db_url="mock://")
    engine._fetch_weekly_windows = MagicMock(return_value=windows)
    engine._fetch_latency_by_decision_type = MagicMock(return_value=latency)
    result = engine.oscillation_report()
    assert result["executive_summary"]["risk_level"] in ("HIGH", "CRITICAL")


def test_T29_signals_list_not_empty():
    windows = [_make_window(i, 0.62) for i in range(6)]
    latency = {"HOLD": {"avg_ms": 160.0, "count": 60},
               "BLOCKED": {"avg_ms": 170.0, "count": 40}}
    engine = OscillationInsightEngine(db_url="mock://")
    engine._fetch_weekly_windows = MagicMock(return_value=windows)
    engine._fetch_latency_by_decision_type = MagicMock(return_value=latency)
    result = engine.oscillation_report()
    assert len(result["executive_summary"]["signals"]) >= 1


def test_T30_report_adr_field():
    windows = [_make_window(i, 0.60) for i in range(4)]
    latency = {}
    engine = OscillationInsightEngine(db_url="mock://")
    engine._fetch_weekly_windows = MagicMock(return_value=windows)
    engine._fetch_latency_by_decision_type = MagicMock(return_value=latency)
    result = engine.oscillation_report()
    assert "ADR-134" in result["adr"]


# ── T31–T35: Edge cases & fail-safe ──────────────────────────────────────────

def test_T31_db_error_returns_available_false():
    engine = OscillationInsightEngine(db_url="postgresql://invalid/db")
    engine._fetch_weekly_windows = MagicMock(side_effect=Exception("DB down"))
    result = engine.oscillation_profile()
    assert result["available"] is False


def test_T32_empty_window_list_handled():
    engine = _engine_with_mock_windows([])
    result = engine.oscillation_profile()
    assert result["available"] is True
    assert result["pattern"] == "INSUFFICIENT_DATA"


def test_T33_sparse_windows_excluded():
    windows = [
        _make_window(0, 0.60, total=5),
        _make_window(1, 0.70, total=3),
        _make_window(2, 0.80, total=100),
        _make_window(3, 0.65, total=100),
        _make_window(4, 0.72, total=100),
        _make_window(5, 0.68, total=100),
    ]
    engine = _engine_with_mock_windows(windows)
    result = engine.oscillation_profile()
    assert result["statistics"]["valid_windows"] == 4


def test_T34_weekly_hold_window_to_dict():
    w = _make_window(0, 0.72)
    d = w.to_dict()
    assert d["hold_rate"] == pytest.approx(0.72, abs=0.001)
    assert "week_offset" in d
    assert "week_start" in d


def test_T35_linear_slope_insufficient_data():
    assert _linear_slope([]) is None
    assert _linear_slope([0.5]) is None
    slope = _linear_slope([0.5, 0.5, 0.5])
    assert slope == pytest.approx(0.0, abs=1e-6)
