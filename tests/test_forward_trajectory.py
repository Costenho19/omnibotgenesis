#!/usr/bin/env python3
"""
Tests for Forward Trajectory Implicator (FTI) — ADR-034
Checkpoint 7b: forward-looking complement to TCV (Checkpoint 7).
"""
import pytest
from omnix_core.temporal.forward_trajectory import (
    ForwardTrajectoryImplicator,
    FTIResult,
    _ADVERSE_REGIMES,
    _REGIME_PERSISTENCE,
    FTI_THRESHOLD_DEFAULT,
    FTI_HORIZON_DEFAULT,
)

SYMBOL = "XBTUSD"


def make_fti(**kwargs) -> ForwardTrajectoryImplicator:
    fti = ForwardTrajectoryImplicator()
    for k, v in kwargs.items():
        setattr(fti, k, v)
    return fti


def trending_up_context():
    return {
        "current_regime": "TRENDING",
        "regime_history": ["TRENDING"] * 5,
        "recent_ema_scores": [50.0, 55.0, 60.0, 65.0, 70.0],
        "hmm_transition_matrix": {
            "TRENDING": {"TRENDING": 0.82, "RANGING": 0.12, "VOLATILE": 0.06, "BEARISH": 0.00},
        },
    }


def volatile_context():
    return {
        "current_regime": "VOLATILE",
        "regime_history": ["RANGING", "VOLATILE", "BEARISH", "VOLATILE", "RANGING"],
        "recent_ema_scores": [60.0, 45.0, 55.0, 40.0, 50.0],
        "hmm_transition_matrix": {
            "VOLATILE": {"BEARISH": 0.35, "BULLISH": 0.30, "VOLATILE": 0.25, "NEUTRAL": 0.10},
        },
    }


# ───────────────────────────── TestFTIResult ─────────────────────────────

class TestFTIResult:
    def test_to_dict_contains_all_keys(self):
        r = FTIResult(passed=True, implied_score=75.0)
        d = r.to_dict()
        assert "passed" in d
        assert "implied_score" in d
        assert "regime_transition_risk" in d
        assert "dimension_scores" in d
        assert "horizon_cycles" in d
        assert "proposed_action" in d
        assert "current_regime" in d
        assert "threshold_used" in d
        assert "pass_through" in d
        assert "timestamp" in d

    def test_score_rounded_in_dict(self):
        r = FTIResult(passed=True, implied_score=72.12345)
        assert r.to_dict()["implied_score"] == 72.12

    def test_pass_through_default_false(self):
        r = FTIResult(passed=True, implied_score=80.0)
        assert r.pass_through is False

    def test_default_horizon(self):
        r = FTIResult(passed=True, implied_score=80.0)
        assert r.horizon_cycles == FTI_HORIZON_DEFAULT


# ───────────────────────────── TestFTIFailSafe ────────────────────────────

class TestFTIFailSafe:
    def test_exception_returns_pass_through(self):
        fti = make_fti()
        fti.threshold = "NOT_A_NUMBER"
        result = fti.evaluate("BUY", SYMBOL, {})
        assert result.passed is True
        assert result.pass_through is True

    def test_pass_through_score_is_100(self):
        fti = make_fti()
        fti.threshold = "BROKEN"
        result = fti.evaluate("BUY", SYMBOL, {})
        assert result.implied_score == 100.0

    def test_pass_through_no_dimension_scores(self):
        fti = make_fti()
        fti.threshold = object()
        result = fti.evaluate("BUY", SYMBOL, {})
        assert result.pass_through is True

    def test_empty_context_no_exception(self):
        fti = make_fti()
        result = fti.evaluate("HOLD", SYMBOL, {})
        assert isinstance(result, FTIResult)
        assert result.pass_through is False

    def test_none_context_no_exception(self):
        fti = make_fti()
        result = fti.evaluate("BUY", SYMBOL, None)
        assert isinstance(result, FTIResult)
        assert result.pass_through is False


# ───────────────────────────── TestFTIRegimeTransitionRisk ───────────────

class TestFTIRegimeTransitionRisk:
    def test_low_adverse_probability_high_score(self):
        fti = make_fti()
        ctx = {
            "current_regime": "TRENDING",
            "hmm_transition_matrix": {
                "TRENDING": {"TRENDING": 0.90, "BEARISH": 0.05, "VOLATILE": 0.05}
            },
        }
        result = fti.evaluate("BUY", SYMBOL, ctx)
        assert result.dimension_scores["regime_transition_risk_score"] > 50.0

    def test_high_adverse_probability_low_score(self):
        fti = make_fti(threshold=0.0)
        ctx = {
            "current_regime": "TRENDING",
            "hmm_transition_matrix": {
                "TRENDING": {"TRENDING": 0.10, "BEARISH": 0.60, "VOLATILE": 0.30}
            },
        }
        result = fti.evaluate("BUY", SYMBOL, ctx)
        assert result.dimension_scores["regime_transition_risk_score"] < 50.0

    def test_hold_action_no_adverse_regime(self):
        fti = make_fti()
        ctx = {
            "current_regime": "VOLATILE",
            "hmm_transition_matrix": {
                "VOLATILE": {"BEARISH": 0.50, "BULLISH": 0.50}
            },
        }
        result = fti.evaluate("HOLD", SYMBOL, ctx)
        assert result.regime_transition_risk == 0.0

    def test_no_hmm_matrix_uses_persistence(self):
        fti = make_fti()
        ctx = {"current_regime": "TRENDING"}
        result = fti.evaluate("BUY", SYMBOL, ctx)
        assert result.dimension_scores["regime_transition_risk_score"] > 0.0

    def test_volatile_regime_lower_persistence_score(self):
        fti = make_fti()
        ctx_trending = {"current_regime": "TRENDING"}
        ctx_volatile = {"current_regime": "VOLATILE"}
        r_trending = fti.evaluate("BUY", SYMBOL, ctx_trending)
        r_volatile = fti.evaluate("BUY", SYMBOL, ctx_volatile)
        assert (
            r_trending.dimension_scores["regime_transition_risk_score"]
            > r_volatile.dimension_scores["regime_transition_risk_score"]
        )

    def test_transition_risk_in_result(self):
        fti = make_fti()
        ctx = {
            "current_regime": "BEARISH",
            "hmm_transition_matrix": {
                "BEARISH": {"BEARISH": 0.70, "BULLISH": 0.20, "NEUTRAL": 0.10}
            },
        }
        result = fti.evaluate("SELL", SYMBOL, ctx)
        assert 0.0 <= result.regime_transition_risk <= 1.0

    def test_score_bounded_0_100(self):
        fti = make_fti()
        ctx = {
            "current_regime": "TRENDING",
            "hmm_transition_matrix": {
                "TRENDING": {"BEARISH": 0.99, "VOLATILE": 0.01}
            },
        }
        result = fti.evaluate("BUY", SYMBOL, ctx)
        assert 0.0 <= result.dimension_scores["regime_transition_risk_score"] <= 100.0

    def test_unknown_regime_uses_default_persistence(self):
        fti = make_fti()
        ctx = {"current_regime": "UNKNOWN_REGIME_XYZ"}
        result = fti.evaluate("BUY", SYMBOL, ctx)
        assert result.dimension_scores["regime_transition_risk_score"] >= 0.0


# ───────────────────────────── TestFTIImpliedConsistency ─────────────────

class TestFTIImpliedConsistency:
    def test_stable_regime_high_consistency(self):
        fti = make_fti()
        ctx = {
            "current_regime": "TRENDING",
            "regime_history": ["TRENDING"] * 5,
        }
        result = fti.evaluate("BUY", SYMBOL, ctx)
        assert result.dimension_scores["implied_decision_consistency"] > 50.0

    def test_volatile_history_lower_consistency(self):
        fti = make_fti()
        ctx = {
            "current_regime": "VOLATILE",
            "regime_history": ["TRENDING", "BEARISH", "VOLATILE", "RANGING", "NEUTRAL"],
        }
        result = fti.evaluate("BUY", SYMBOL, ctx)
        assert result.dimension_scores["implied_decision_consistency"] < 60.0

    def test_empty_history_neutral_score(self):
        fti = make_fti()
        ctx = {"current_regime": "TRENDING", "regime_history": []}
        result = fti.evaluate("BUY", SYMBOL, ctx)
        assert result.dimension_scores["implied_decision_consistency"] == 50.0

    def test_no_history_key_neutral_score(self):
        fti = make_fti()
        ctx = {"current_regime": "TRENDING"}
        result = fti.evaluate("BUY", SYMBOL, ctx)
        assert result.dimension_scores["implied_decision_consistency"] == 50.0

    def test_consistency_bounded_0_100(self):
        fti = make_fti()
        ctx = {
            "current_regime": "BULLISH",
            "regime_history": ["BEARISH", "VOLATILE", "RANGING", "NEUTRAL", "RANGING"],
        }
        r = fti.evaluate("BUY", SYMBOL, ctx)
        assert 0.0 <= r.dimension_scores["implied_decision_consistency"] <= 100.0

    def test_compatible_regime_buy_increases_score(self):
        fti = make_fti()
        ctx_compatible = {
            "current_regime": "BULLISH",
            "regime_history": ["BULLISH", "UPTREND", "TRENDING", "NEUTRAL", "BULLISH"],
        }
        ctx_incompatible = {
            "current_regime": "BEARISH",
            "regime_history": ["BEARISH", "DOWNTREND", "BEARISH", "VOLATILE", "BEARISH"],
        }
        r_compat = fti.evaluate("BUY", SYMBOL, ctx_compatible)
        r_incompat = fti.evaluate("BUY", SYMBOL, ctx_incompatible)
        assert (
            r_compat.dimension_scores["implied_decision_consistency"]
            >= r_incompat.dimension_scores["implied_decision_consistency"]
        )

    def test_sell_compatible_regime_improves_score(self):
        fti = make_fti()
        ctx = {
            "current_regime": "BEARISH",
            "regime_history": ["BEARISH", "DOWNTREND", "BEARISH", "BEARISH", "BEARISH"],
        }
        result = fti.evaluate("SELL", SYMBOL, ctx)
        assert result.dimension_scores["implied_decision_consistency"] > 30.0

    def test_horizon_controls_history_window(self):
        fti_short = make_fti(horizon=2)
        fti_long = make_fti(horizon=5)
        ctx = {
            "current_regime": "TRENDING",
            "regime_history": ["BEARISH", "BEARISH", "TRENDING", "TRENDING", "TRENDING"],
        }
        r_short = fti_short.evaluate("BUY", SYMBOL, ctx)
        r_long = fti_long.evaluate("BUY", SYMBOL, ctx)
        assert r_short.dimension_scores["implied_decision_consistency"] != r_long.dimension_scores["implied_decision_consistency"]


# ───────────────────────────── TestFTISignalMomentum ─────────────────────

class TestFTISignalMomentum:
    def test_rising_scores_buy_high_momentum(self):
        fti = make_fti()
        ctx = {"recent_ema_scores": [40.0, 50.0, 60.0, 70.0, 80.0]}
        result = fti.evaluate("BUY", SYMBOL, ctx)
        assert result.dimension_scores["signal_momentum_sustainability"] > 60.0

    def test_declining_scores_buy_low_momentum(self):
        fti = make_fti()
        ctx = {"recent_ema_scores": [80.0, 70.0, 60.0, 50.0, 40.0]}
        result = fti.evaluate("BUY", SYMBOL, ctx)
        assert result.dimension_scores["signal_momentum_sustainability"] < 50.0

    def test_declining_scores_sell_high_momentum(self):
        fti = make_fti()
        ctx = {"recent_ema_scores": [80.0, 70.0, 60.0, 50.0, 40.0]}
        result = fti.evaluate("SELL", SYMBOL, ctx)
        assert result.dimension_scores["signal_momentum_sustainability"] > 50.0

    def test_flat_scores_hold_high_score(self):
        fti = make_fti()
        ctx = {"recent_ema_scores": [60.0, 60.0, 60.0, 60.0, 60.0]}
        result = fti.evaluate("HOLD", SYMBOL, ctx)
        assert result.dimension_scores["signal_momentum_sustainability"] >= 90.0

    def test_single_score_neutral(self):
        fti = make_fti()
        ctx = {"recent_ema_scores": [75.0]}
        result = fti.evaluate("BUY", SYMBOL, ctx)
        assert result.dimension_scores["signal_momentum_sustainability"] == 50.0

    def test_momentum_bounded_0_100(self):
        fti = make_fti()
        ctx = {"recent_ema_scores": [0.0, 0.0, 0.0, 100.0, 100.0]}
        result = fti.evaluate("BUY", SYMBOL, ctx)
        assert 0.0 <= result.dimension_scores["signal_momentum_sustainability"] <= 100.0


# ───────────────────────────── TestFTIThreshold ──────────────────────────

class TestFTIThreshold:
    def test_above_threshold_passes(self):
        fti = make_fti(threshold=10.0)
        result = fti.evaluate("HOLD", SYMBOL, {})
        assert result.passed is True

    def test_below_threshold_fails(self):
        fti = make_fti(threshold=200.0)
        result = fti.evaluate("BUY", SYMBOL, trending_up_context())
        assert result.passed is False

    def test_threshold_reflected_in_result(self):
        fti = make_fti(threshold=30.0)
        result = fti.evaluate("BUY", SYMBOL, {})
        assert result.threshold_used == 30.0

    def test_default_threshold_is_conservative(self):
        assert FTI_THRESHOLD_DEFAULT == 25

    def test_strongly_adverse_context_fails(self):
        fti = make_fti(threshold=FTI_THRESHOLD_DEFAULT)
        ctx = {
            "current_regime": "VOLATILE",
            "hmm_transition_matrix": {
                "VOLATILE": {"BEARISH": 0.70, "VOLATILE": 0.20, "BULLISH": 0.10}
            },
            "recent_ema_scores": [80.0, 70.0, 60.0, 50.0, 40.0],
            "regime_history": ["VOLATILE", "BEARISH", "VOLATILE", "BEARISH", "VOLATILE"],
        }
        result = fti.evaluate("BUY", SYMBOL, ctx)
        assert result.passed is False


# ───────────────────────────── TestFTIHorizonConfig ──────────────────────

class TestFTIHorizonConfig:
    def test_default_horizon(self):
        fti = make_fti()
        assert fti.horizon == FTI_HORIZON_DEFAULT

    def test_custom_horizon_reflected_in_result(self):
        fti = make_fti(horizon=10)
        result = fti.evaluate("BUY", SYMBOL, {})
        assert result.horizon_cycles == 10

    def test_longer_horizon_increases_risk(self):
        fti_short = make_fti(horizon=1, threshold=0)
        fti_long = make_fti(horizon=20, threshold=0)
        ctx = {"current_regime": "VOLATILE"}
        r_short = fti_short.evaluate("BUY", SYMBOL, ctx)
        r_long = fti_long.evaluate("BUY", SYMBOL, ctx)
        assert (
            r_short.dimension_scores["regime_transition_risk_score"]
            >= r_long.dimension_scores["regime_transition_risk_score"]
        )

    def test_horizon_1_minimum_risk(self):
        fti = make_fti(horizon=1, threshold=0)
        ctx = {
            "current_regime": "TRENDING",
            "hmm_transition_matrix": {
                "TRENDING": {"TRENDING": 0.95, "BEARISH": 0.05}
            },
        }
        result = fti.evaluate("BUY", SYMBOL, ctx)
        assert result.dimension_scores["regime_transition_risk_score"] >= 50.0


# ───────────────────────────── TestFTILinearSlope ────────────────────────

class TestFTILinearSlope:
    def test_rising_slope_positive(self):
        slope = ForwardTrajectoryImplicator._linear_slope([1.0, 2.0, 3.0, 4.0, 5.0])
        assert slope > 0.0

    def test_declining_slope_negative(self):
        slope = ForwardTrajectoryImplicator._linear_slope([5.0, 4.0, 3.0, 2.0, 1.0])
        assert slope < 0.0

    def test_flat_slope_zero(self):
        slope = ForwardTrajectoryImplicator._linear_slope([5.0, 5.0, 5.0, 5.0, 5.0])
        assert slope == 0.0

    def test_single_value_zero(self):
        slope = ForwardTrajectoryImplicator._linear_slope([42.0])
        assert slope == 0.0

    def test_slope_bounded(self):
        slope = ForwardTrajectoryImplicator._linear_slope([0.0] * 4 + [1000.0])
        assert -1.0 <= slope <= 1.0
