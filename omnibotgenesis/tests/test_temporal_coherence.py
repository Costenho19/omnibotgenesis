#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Temporal Coherence Validation (TCV) — OMNIX Checkpoint 7
ADR-032 | March 2026

Coverage:
  - TCVResult dataclass structure and serialization
  - Fail-safe behavior (DB unavailable, exceptions, insufficient data)
  - Coherent trajectory scenarios → admissible=True
  - Incoherent trajectory scenarios → dimension analysis
  - Individual scoring dimensions (direction_coherence, regime_alignment, signal_stability)
  - Signal taxonomy normalization (_normalize_direction)
  - Dual data source merge and normalization
  - Pass-through flag semantics
"""

import pytest
from unittest.mock import patch, MagicMock
from omnix_core.temporal.coherence_validator import (
    TemporalCoherenceValidator,
    TCVResult,
    _normalize_direction,
    TCV_THRESHOLD_DEFAULT,
)


def make_shadow_events(
    n: int,
    ema_signal: str = "BULLISH",
    hmm_regime: str = "BULLISH",
    ema_score: float = 70.0,
) -> list:
    """Generate n synthetic shadow_trade_events rows."""
    return [
        {
            "ema_score_f": ema_score,
            "signal_raw": ema_signal,
            "hmm_regime": hmm_regime,
            "action_raw": "BUY",
            "normalized_direction": _normalize_direction(ema_signal),
            "normalized_action": "BUY",
            "source": "shadow",
            "created_at": "2026-03-01T00:00:00Z",
        }
        for _ in range(n)
    ]


def make_mixed_events(signals: list, regimes: list = None, scores: list = None) -> list:
    """Generate events with varying signals/regimes for incoherence testing."""
    regimes = regimes or ["NEUTRAL"] * len(signals)
    scores = scores or [50.0] * len(signals)
    return [
        {
            "ema_score_f": scores[i],
            "signal_raw": signals[i],
            "hmm_regime": regimes[i],
            "action_raw": signals[i],
            "normalized_direction": _normalize_direction(signals[i]),
            "normalized_action": _normalize_direction(signals[i]),
            "source": "shadow",
            "created_at": f"2026-03-0{i+1}T00:00:00Z",
        }
        for i in range(len(signals))
    ]


class TestNormalizeDirection:
    """_normalize_direction handles all known signal taxonomies."""

    def test_bullish_signals_map_to_buy(self):
        for s in ("BULLISH", "LONG", "BUY", "STRONG_BUY", "UPTREND"):
            assert _normalize_direction(s) == "BUY", f"Failed for {s}"

    def test_bearish_signals_map_to_sell(self):
        for s in ("BEARISH", "SHORT", "SELL", "STRONG_SELL", "DOWNTREND"):
            assert _normalize_direction(s) == "SELL", f"Failed for {s}"

    def test_neutral_signals_map_to_hold(self):
        for s in ("NEUTRAL", "NONE", "RANGING", "VOLATILE"):
            assert _normalize_direction(s) == "HOLD", f"Failed for {s}"

    def test_none_returns_hold(self):
        assert _normalize_direction(None) == "HOLD"

    def test_empty_string_returns_hold(self):
        assert _normalize_direction("") == "HOLD"

    def test_unknown_returns_hold(self):
        assert _normalize_direction("SIDEWAYS") == "HOLD"

    def test_case_insensitive(self):
        assert _normalize_direction("bullish") == "BUY"
        assert _normalize_direction("Bearish") == "SELL"


class TestTCVResult:
    """TCVResult dataclass structure and serialization."""

    def test_to_dict_contains_all_required_fields(self):
        result = TCVResult(
            admissible=True,
            trajectory_score=85.0,
            reason="TEMPORALLY_ADMISSIBLE",
            pass_through=False,
        )
        d = result.to_dict()
        required = {
            "admissible", "trajectory_score", "reason",
            "dimension_scores", "events_analyzed",
            "threshold_used", "data_sources", "pass_through", "timestamp",
        }
        assert required.issubset(d.keys())

    def test_to_dict_rounds_to_two_decimal_places(self):
        result = TCVResult(
            admissible=True,
            trajectory_score=85.3456789,
            reason="test",
            dimension_scores={"direction_coherence": 90.12345},
        )
        d = result.to_dict()
        assert d["trajectory_score"] == 85.35
        assert d["dimension_scores"]["direction_coherence"] == 90.12

    def test_pass_through_false_by_default(self):
        result = TCVResult(admissible=True, trajectory_score=90.0, reason="ok")
        assert result.pass_through is False

    def test_data_sources_defaults_to_empty_list(self):
        result = TCVResult(admissible=True, trajectory_score=90.0, reason="ok")
        assert result.data_sources == []


class TestTCVFailSafe:
    """Fail-safe: on any error → admissible=True with pass_through=True."""

    def test_no_db_url_returns_admissible_pass_through(self):
        validator = TemporalCoherenceValidator(db_url=None)
        result = validator.validate("BUY", "XBTUSD")
        assert result.admissible is True
        assert result.pass_through is True

    def test_invalid_db_url_returns_admissible(self):
        validator = TemporalCoherenceValidator(db_url="invalid://url")
        result = validator.validate("BUY", "XBTUSD")
        assert result.admissible is True

    def test_exception_in_validate_internal_triggers_failsafe(self):
        validator = TemporalCoherenceValidator(db_url=None)
        with patch.object(validator, "_validate_internal", side_effect=RuntimeError("boom")):
            result = validator.validate("BUY", "XBTUSD")
        assert result.admissible is True
        assert result.pass_through is True
        assert "TCV_FAILSAFE" in result.reason

    def test_insufficient_events_returns_admissible_pass_through(self):
        validator = TemporalCoherenceValidator(db_url=None)
        with patch.object(validator, "_fetch_trajectory", return_value=(make_shadow_events(1), ["shadow"])):
            result = validator.validate("BUY", "XBTUSD")
        assert result.admissible is True
        assert result.pass_through is True
        assert "INSUFFICIENT" in result.reason

    def test_zero_events_pass_through(self):
        validator = TemporalCoherenceValidator(db_url=None)
        with patch.object(validator, "_fetch_trajectory", return_value=([], [])):
            result = validator.validate("BUY", "XBTUSD")
        assert result.admissible is True
        assert result.pass_through is True


class TestTCVCoherentTrajectory:
    """Coherent trajectories return admissible=True with high scores."""

    def test_stable_bullish_trajectory_buy_is_admissible(self):
        validator = TemporalCoherenceValidator(db_url=None)
        events = make_shadow_events(10, ema_signal="BULLISH", hmm_regime="BULLISH", ema_score=70.0)
        with patch.object(validator, "_fetch_trajectory", return_value=(events, ["shadow"])):
            result = validator.validate(
                "BUY", "XBTUSD",
                context={"hmm_regime": "BULLISH", "ema_score": 72.0},
            )
        assert result.admissible is True
        assert result.trajectory_score >= TCV_THRESHOLD_DEFAULT
        assert result.pass_through is False

    def test_stable_bearish_trajectory_sell_is_admissible(self):
        validator = TemporalCoherenceValidator(db_url=None)
        events = make_shadow_events(10, ema_signal="BEARISH", hmm_regime="BEARISH", ema_score=30.0)
        with patch.object(validator, "_fetch_trajectory", return_value=(events, ["shadow"])):
            result = validator.validate(
                "SELL", "XBTUSD",
                context={"hmm_regime": "BEARISH", "ema_score": 28.0},
            )
        assert result.admissible is True

    def test_hold_in_volatile_regime_is_admissible(self):
        validator = TemporalCoherenceValidator(db_url=None)
        events = make_shadow_events(8, ema_signal="NEUTRAL", hmm_regime="VOLATILE", ema_score=50.0)
        with patch.object(validator, "_fetch_trajectory", return_value=(events, ["shadow"])):
            result = validator.validate(
                "HOLD", "XBTUSD",
                context={"hmm_regime": "VOLATILE"},
            )
        assert result.admissible is True

    def test_mixed_sources_reported_in_data_sources(self):
        validator = TemporalCoherenceValidator(db_url=None)
        events = make_shadow_events(5, ema_signal="BULLISH", hmm_regime="BULLISH")
        with patch.object(validator, "_fetch_trajectory", return_value=(events, ["shadow", "trade"])):
            result = validator.validate("BUY", "XBTUSD")
        assert "shadow" in result.data_sources
        assert "trade" in result.data_sources


class TestTCVIncoherentTrajectory:
    """Incoherent trajectories register low dimension scores."""

    def test_buy_against_sustained_bearish_regime_scores_zero_alignment(self):
        validator = TemporalCoherenceValidator(db_url=None)
        events = make_shadow_events(10, ema_signal="BEARISH", hmm_regime="BEARISH", ema_score=20.0)
        with patch.object(validator, "_fetch_trajectory", return_value=(events, ["shadow"])):
            result = validator.validate(
                "BUY", "XBTUSD",
                context={"hmm_regime": "BEARISH", "ema_score": 22.0},
            )
        assert result.dimension_scores["regime_alignment"] == 0.0

    def test_buy_against_sustained_bearish_fails_strict_threshold(self):
        validator = TemporalCoherenceValidator(db_url=None)
        validator.threshold = 70.0
        events = make_shadow_events(10, ema_signal="BEARISH", hmm_regime="BEARISH", ema_score=20.0)
        with patch.object(validator, "_fetch_trajectory", return_value=(events, ["shadow"])):
            result = validator.validate(
                "BUY", "XBTUSD",
                context={"hmm_regime": "BEARISH", "ema_score": 22.0},
            )
        assert result.admissible is False
        assert result.trajectory_score < 70.0

    def test_wildly_alternating_signals_score_low_stability(self):
        validator = TemporalCoherenceValidator(db_url=None)
        signals = ["BULLISH", "BEARISH"] * 5
        events = make_mixed_events(signals, regimes=["NEUTRAL"] * 10)
        stability = validator._score_signal_stability(events)
        assert stability < 15.0

    def test_non_monotonic_scores_penalize_direction_coherence(self):
        validator = TemporalCoherenceValidator(db_url=None)
        events = make_mixed_events(
            signals=["BULLISH"] * 10,
            scores=[10.0, 90.0, 5.0, 95.0, 8.0, 92.0, 12.0, 88.0, 6.0, 94.0],
        )
        score = validator._score_direction_coherence(events, {})
        assert score < 60.0


class TestTCVDirectionCoherence:
    """direction_coherence dimension: monotonicity of EMA-score deltas."""

    def setup_method(self):
        self.validator = TemporalCoherenceValidator(db_url=None)

    def test_monotonically_increasing_scores_score_100(self):
        events = make_mixed_events(
            signals=["BULLISH"] * 5,
            scores=[50.0, 55.0, 60.0, 65.0, 70.0],
        )
        score = self.validator._score_direction_coherence(events, {})
        assert score == 100.0

    def test_monotonically_decreasing_scores_score_100(self):
        events = make_mixed_events(
            signals=["BEARISH"] * 5,
            scores=[70.0, 65.0, 60.0, 55.0, 50.0],
        )
        score = self.validator._score_direction_coherence(events, {})
        assert score == 100.0

    def test_alternating_scores_score_near_zero(self):
        events = make_mixed_events(
            signals=["NEUTRAL"] * 6,
            scores=[30.0, 70.0, 30.0, 70.0, 30.0, 70.0],
        )
        score = self.validator._score_direction_coherence(events, {})
        assert score < 20.0

    def test_single_event_returns_zero_no_evidence(self):
        # ADR-065: insufficient data → score=0, not assumed coherence
        score = self.validator._score_direction_coherence(make_shadow_events(1), {})
        assert score == 0.0


class TestTCVRegimeAlignment:
    """regime_alignment dimension: dominant regime vs proposed action."""

    def setup_method(self):
        self.validator = TemporalCoherenceValidator(db_url=None)

    def test_buy_in_bullish_scores_high(self):
        events = make_shadow_events(5, hmm_regime="BULLISH")
        score = self.validator._score_regime_alignment(events, "BUY", {"hmm_regime": "BULLISH"})
        assert score >= 75.0

    def test_sell_in_bearish_scores_high(self):
        events = make_shadow_events(5, hmm_regime="BEARISH")
        score = self.validator._score_regime_alignment(events, "SELL", {"hmm_regime": "BEARISH"})
        assert score >= 75.0

    def test_buy_in_bearish_scores_zero(self):
        events = make_shadow_events(5, hmm_regime="BEARISH")
        score = self.validator._score_regime_alignment(events, "BUY", {"hmm_regime": "BEARISH"})
        assert score == 0.0

    def test_mixed_regime_below_threshold_returns_neutral(self):
        events = make_mixed_events(
            signals=["NEUTRAL"] * 6,
            regimes=["BULLISH", "BEARISH", "NEUTRAL", "VOLATILE", "BULLISH", "TRENDING"],
        )
        score = self.validator._score_regime_alignment(events, "BUY", {})
        assert score == 65.0

    def test_empty_regime_returns_neutral_score(self):
        events = make_shadow_events(5, hmm_regime="")
        score = self.validator._score_regime_alignment(events, "BUY", {})
        assert score == 65.0

    def test_hold_in_volatile_scores_high(self):
        events = make_shadow_events(5, hmm_regime="VOLATILE")
        score = self.validator._score_regime_alignment(events, "HOLD", {"hmm_regime": "VOLATILE"})
        assert score >= 75.0


class TestTCVSignalStability:
    """signal_stability dimension: inverse of direction flip rate."""

    def setup_method(self):
        self.validator = TemporalCoherenceValidator(db_url=None)

    def test_stable_bullish_signals_score_100(self):
        events = make_shadow_events(8, ema_signal="BULLISH")
        score = self.validator._score_signal_stability(events)
        assert score == 100.0

    def test_stable_bearish_signals_score_100(self):
        events = make_shadow_events(8, ema_signal="BEARISH")
        score = self.validator._score_signal_stability(events)
        assert score == 100.0

    def test_alternating_signals_score_near_zero(self):
        signals = ["BULLISH", "BEARISH"] * 5
        events = make_mixed_events(signals)
        score = self.validator._score_signal_stability(events)
        assert score < 15.0

    def test_single_event_returns_zero_no_evidence(self):
        # ADR-065: insufficient data → score=0, not assumed stability
        score = self.validator._score_signal_stability(make_shadow_events(1))
        assert score == 0.0

    def test_long_short_taxonomy_normalized_correctly(self):
        events = make_mixed_events(["LONG", "LONG", "LONG", "LONG"])
        for e in events:
            e["normalized_direction"] = _normalize_direction(e["signal_raw"])
        score = self.validator._score_signal_stability(events)
        assert score == 100.0


class TestTCVScoreRange:
    """Trajectory score always in [0, 100]."""

    def test_score_range_for_all_actions(self):
        validator = TemporalCoherenceValidator(db_url=None)
        for action in ("BUY", "SELL", "HOLD"):
            events = make_shadow_events(6, ema_signal="BULLISH", hmm_regime="BULLISH")
            with patch.object(validator, "_fetch_trajectory", return_value=(events, ["shadow"])):
                result = validator.validate(action, "XBTUSD")
            assert 0.0 <= result.trajectory_score <= 100.0, f"Out of range for action={action}"

    def test_dimension_scores_all_in_range(self):
        validator = TemporalCoherenceValidator(db_url=None)
        events = make_shadow_events(7, ema_signal="BULLISH", hmm_regime="BULLISH")
        with patch.object(validator, "_fetch_trajectory", return_value=(events, ["shadow"])):
            result = validator.validate("BUY", "XBTUSD")
        for k, v in result.dimension_scores.items():
            assert 0.0 <= v <= 100.0, f"Dimension {k}={v} out of range"


class TestTCVResultFields:
    """TCVResult contains all observability fields."""

    def test_result_has_three_dimension_scores(self):
        validator = TemporalCoherenceValidator(db_url=None)
        events = make_shadow_events(5)
        with patch.object(validator, "_fetch_trajectory", return_value=(events, ["shadow"])):
            result = validator.validate("BUY", "XBTUSD")
        expected_dims = {"direction_coherence", "regime_alignment", "signal_stability"}
        assert expected_dims == set(result.dimension_scores.keys())

    def test_events_analyzed_matches_input_count(self):
        validator = TemporalCoherenceValidator(db_url=None)
        events = make_shadow_events(7)
        with patch.object(validator, "_fetch_trajectory", return_value=(events, ["shadow"])):
            result = validator.validate("BUY", "XBTUSD")
        assert result.events_analyzed == 7

    def test_custom_threshold_reflected_in_result(self):
        validator = TemporalCoherenceValidator(db_url=None)
        validator.threshold = 45.0
        events = make_shadow_events(5)
        with patch.object(validator, "_fetch_trajectory", return_value=(events, ["shadow"])):
            result = validator.validate("BUY", "XBTUSD")
        assert result.threshold_used == 45.0

    def test_pass_through_false_when_evaluated(self):
        validator = TemporalCoherenceValidator(db_url=None)
        events = make_shadow_events(5)
        with patch.object(validator, "_fetch_trajectory", return_value=(events, ["shadow"])):
            result = validator.validate("BUY", "XBTUSD")
        assert result.pass_through is False

    def test_timestamp_is_iso_format(self):
        validator = TemporalCoherenceValidator(db_url=None)
        events = make_shadow_events(5)
        with patch.object(validator, "_fetch_trajectory", return_value=(events, ["shadow"])):
            result = validator.validate("BUY", "XBTUSD")
        from datetime import datetime
        datetime.fromisoformat(result.timestamp)


class TestTCVMergeAndNormalize:
    """_merge_and_normalize handles dual-source combination correctly."""

    def setup_method(self):
        self.validator = TemporalCoherenceValidator(db_url=None)

    def test_shadow_and_trade_rows_combined(self):
        shadow = [{"ema_score": 70.0, "ema_signal": "BULLISH", "hmm_regime": "BULLISH",
                   "intended_action": "BUY", "coherence_score": 80.0, "created_at": "2026-03-01T00:00:00Z"}]
        trade = [{"strategy_confidence": 75.0, "ema_regime_signal": "LONG", "hmm_regime": "BULLISH",
                  "side": "buy", "created_at": "2026-03-01T01:00:00Z"}]

        shadow_norm = [{"ema_score": 70.0, "signal_raw": "BULLISH", "hmm_regime": "BULLISH",
                        "action_raw": "BUY", "source": "shadow", "created_at": "2026-03-01T00:00:00Z"}]
        trade_norm = [{"ema_score": 75.0, "signal_raw": "LONG", "hmm_regime": "BULLISH",
                       "action_raw": "buy", "source": "trade", "created_at": "2026-03-01T01:00:00Z"}]

        merged = self.validator._merge_and_normalize(shadow_norm, trade_norm)
        assert len(merged) == 2

    def test_normalized_direction_populated(self):
        rows = [{"signal_raw": "LONG", "action_raw": "buy", "ema_score": 60.0,
                 "hmm_regime": "BULLISH", "source": "trade", "created_at": None}]
        merged = self.validator._merge_and_normalize(rows, [])
        assert merged[0]["normalized_direction"] == "BUY"
        assert merged[0]["normalized_action"] == "BUY"

    def test_invalid_ema_score_sets_none(self):
        rows = [{"signal_raw": "NEUTRAL", "action_raw": "hold", "ema_score": "not_a_number",
                 "hmm_regime": "NEUTRAL", "source": "shadow", "created_at": None}]
        merged = self.validator._merge_and_normalize(rows, [])
        assert merged[0]["ema_score_f"] is None
