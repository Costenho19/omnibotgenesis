#!/usr/bin/env python3
"""
Tests for Regime-Conditioned Kelly (RCK) — ADR-035
Regime-segmented Kelly inputs with 3-level fallback chain.
"""
import pytest
from unittest.mock import patch, MagicMock
from omnix_core.sizing.regime_conditioned_kelly import (
    RegimeConditionedKelly,
    RegimeKellyStats,
    CONSERVATIVE_DEFAULTS,
    RCK_MIN_SAMPLES_DEFAULT,
    RCK_MIN_GLOBAL_DEFAULT,
)

SYMBOL = "XBTUSD"


def make_rck(db_url=None, **kwargs) -> RegimeConditionedKelly:
    rck = RegimeConditionedKelly(db_url=db_url or "postgresql://fake:5432/fake")
    for k, v in kwargs.items():
        setattr(rck, k, v)
    return rck


def make_trades(n: int, win_frac: float = 0.6, avg_win: float = 0.025, avg_loss: float = 0.015):
    trades = []
    wins = int(n * win_frac)
    for i in range(n):
        if i < wins:
            trades.append({"profit_loss": avg_win})
        else:
            trades.append({"profit_loss": -avg_loss})
    return trades


# ───────────────────────────── TestRegimeKellyStats ──────────────────────

class TestRegimeKellyStats:
    def test_to_dict_contains_all_keys(self):
        s = RegimeKellyStats(0.60, 0.025, 0.015, 30, "TRENDING", "HIGH")
        d = s.to_dict()
        assert "win_rate" in d
        assert "avg_win" in d
        assert "avg_loss" in d
        assert "sample_count" in d
        assert "regime" in d
        assert "confidence" in d
        assert "fallback_used" in d
        assert "fallback_level" in d
        assert "timestamp" in d

    def test_win_loss_ratio_computed(self):
        s = RegimeKellyStats(0.60, 0.030, 0.015, 30, "TRENDING", "HIGH")
        assert abs(s.win_loss_ratio - 2.0) < 0.001

    def test_win_loss_ratio_no_div_zero(self):
        s = RegimeKellyStats(0.60, 0.025, 0.0, 30, "TRENDING", "HIGH")
        assert s.win_loss_ratio == 1.0

    def test_kelly_fraction_raw_positive(self):
        s = RegimeKellyStats(0.65, 0.03, 0.015, 30, "TRENDING", "HIGH")
        assert s.kelly_fraction_raw > 0.0

    def test_kelly_fraction_raw_not_negative(self):
        s = RegimeKellyStats(0.20, 0.01, 0.05, 30, "TRENDING", "HIGH")
        assert s.kelly_fraction_raw >= 0.0


# ───────────────────────────── TestFallbackChain ─────────────────────────

class TestFallbackChain:
    def test_no_db_url_returns_defaults(self):
        rck = RegimeConditionedKelly(db_url=None)
        rck.db_url = None
        result = rck.get_regime_stats("TRENDING", SYMBOL)
        assert result.fallback_level == "DEFAULTS"
        assert result.fallback_used is True

    def test_sufficient_regime_samples_no_fallback(self):
        rck = make_rck(min_samples=5)
        regime_trades = make_trades(20, win_frac=0.65)
        with patch.object(rck, "_query_trades", side_effect=[regime_trades, []]):
            result = rck.get_regime_stats("TRENDING", SYMBOL)
        assert result.fallback_used is False
        assert result.fallback_level == "REGIME"

    def test_insufficient_regime_falls_to_global(self):
        rck = make_rck(min_samples=10, min_global=5)
        regime_trades = make_trades(3)
        global_trades = make_trades(20)
        with patch.object(rck, "_query_trades", side_effect=[regime_trades, global_trades]):
            result = rck.get_regime_stats("TRENDING", SYMBOL)
        assert result.fallback_used is True
        assert result.fallback_level == "GLOBAL"

    def test_insufficient_global_falls_to_defaults(self):
        rck = make_rck(min_samples=10, min_global=5)
        with patch.object(rck, "_query_trades", side_effect=[[], []]):
            result = rck.get_regime_stats("TRENDING", SYMBOL)
        assert result.fallback_level == "DEFAULTS"
        assert result.win_rate == CONSERVATIVE_DEFAULTS["win_rate"]

    def test_exception_returns_defaults(self):
        rck = make_rck()
        with patch.object(rck, "_compute_stats", side_effect=RuntimeError("DB down")):
            result = rck.get_regime_stats("TRENDING", SYMBOL)
        assert result.fallback_level == "DEFAULTS"
        assert result.fallback_used is True

    def test_defaults_are_conservative(self):
        rck = RegimeConditionedKelly(db_url=None)
        rck.db_url = None
        result = rck.get_regime_stats("VOLATILE")
        assert result.win_rate == 0.50
        assert result.avg_win == 0.01
        assert result.avg_loss == 0.01


# ───────────────────────────── TestRegimeStatsQuery ──────────────────────

class TestRegimeStatsQuery:
    def test_win_rate_computed_correctly(self):
        rck = make_rck(min_samples=5)
        trades = make_trades(10, win_frac=0.70)
        with patch.object(rck, "_query_trades", side_effect=[trades, []]):
            result = rck.get_regime_stats("TRENDING", SYMBOL)
        assert abs(result.win_rate - 0.70) < 0.01

    def test_avg_win_computed(self):
        rck = make_rck(min_samples=5)
        trades = make_trades(10, win_frac=0.60, avg_win=0.025)
        with patch.object(rck, "_query_trades", side_effect=[trades, []]):
            result = rck.get_regime_stats("TRENDING", SYMBOL)
        assert result.avg_win > 0.0

    def test_avg_loss_computed(self):
        rck = make_rck(min_samples=5)
        trades = make_trades(10, win_frac=0.60, avg_loss=0.015)
        with patch.object(rck, "_query_trades", side_effect=[trades, []]):
            result = rck.get_regime_stats("TRENDING", SYMBOL)
        assert result.avg_loss > 0.0

    def test_regime_in_result(self):
        rck = make_rck(min_samples=5)
        trades = make_trades(15)
        with patch.object(rck, "_query_trades", side_effect=[trades, []]):
            result = rck.get_regime_stats("VOLATILE", SYMBOL)
        assert result.regime == "VOLATILE"

    def test_sample_count_reflects_data(self):
        rck = make_rck(min_samples=5)
        trades = make_trades(25)
        with patch.object(rck, "_query_trades", side_effect=[trades, []]):
            result = rck.get_regime_stats("TRENDING", SYMBOL)
        assert result.sample_count == 25

    def test_all_wins_no_division_error(self):
        rck = make_rck(min_samples=5)
        trades = [{"profit_loss": 0.02}] * 10
        with patch.object(rck, "_query_trades", side_effect=[trades, []]):
            result = rck.get_regime_stats("TRENDING", SYMBOL)
        assert result.win_rate == 1.0
        assert result.avg_loss >= 0.001

    def test_all_losses_no_division_error(self):
        rck = make_rck(min_samples=5)
        trades = [{"profit_loss": -0.02}] * 10
        with patch.object(rck, "_query_trades", side_effect=[trades, []]):
            result = rck.get_regime_stats("TRENDING", SYMBOL)
        assert result.win_rate == 0.0
        assert result.avg_win >= 0.001

    def test_uppercase_regime_normalization(self):
        rck = RegimeConditionedKelly(db_url=None)
        rck.db_url = None
        result = rck.get_regime_stats("trending")
        assert result.regime == "TRENDING"


# ───────────────────────────── TestConfidenceLevels ──────────────────────

class TestConfidenceLevels:
    def test_30_plus_samples_high_confidence(self):
        rck = make_rck(min_samples=5)
        trades = make_trades(35)
        with patch.object(rck, "_query_trades", side_effect=[trades, []]):
            result = rck.get_regime_stats("TRENDING", SYMBOL)
        assert result.confidence == "HIGH"

    def test_10_29_samples_medium_confidence(self):
        rck = make_rck(min_samples=5)
        trades = make_trades(15)
        with patch.object(rck, "_query_trades", side_effect=[trades, []]):
            result = rck.get_regime_stats("TRENDING", SYMBOL)
        assert result.confidence == "MEDIUM"

    def test_global_fallback_is_low_confidence(self):
        rck = make_rck(min_samples=10, min_global=5)
        with patch.object(rck, "_query_trades", side_effect=[make_trades(3), make_trades(15)]):
            result = rck.get_regime_stats("TRENDING", SYMBOL)
        assert result.confidence == "LOW"

    def test_defaults_are_low_confidence(self):
        rck = RegimeConditionedKelly(db_url=None)
        rck.db_url = None
        result = rck.get_regime_stats("VOLATILE")
        assert result.confidence == "LOW"

    def test_fallback_used_false_on_regime_data(self):
        rck = make_rck(min_samples=5)
        trades = make_trades(20)
        with patch.object(rck, "_query_trades", side_effect=[trades, []]):
            result = rck.get_regime_stats("TRENDING", SYMBOL)
        assert result.fallback_used is False

    def test_fallback_used_true_on_global(self):
        rck = make_rck(min_samples=10, min_global=5)
        with patch.object(rck, "_query_trades", side_effect=[make_trades(2), make_trades(20)]):
            result = rck.get_regime_stats("TRENDING", SYMBOL)
        assert result.fallback_used is True


# ───────────────────────────── TestCalcStats ─────────────────────────────

class TestCalcStats:
    def test_empty_trades_returns_defaults(self):
        stats = RegimeConditionedKelly._calc_stats([])
        assert stats["win_rate"] == CONSERVATIVE_DEFAULTS["win_rate"]

    def test_win_rate_bounded_0_1(self):
        trades = make_trades(10, win_frac=1.5)
        stats = RegimeConditionedKelly._calc_stats(trades)
        assert 0.0 <= stats["win_rate"] <= 1.0

    def test_avg_win_positive(self):
        trades = make_trades(10, avg_win=0.03)
        stats = RegimeConditionedKelly._calc_stats(trades)
        assert stats["avg_win"] > 0.0

    def test_avg_loss_positive(self):
        trades = make_trades(10, avg_loss=0.02)
        stats = RegimeConditionedKelly._calc_stats(trades)
        assert stats["avg_loss"] > 0.0

    def test_minimum_floor_applied(self):
        trades = [{"profit_loss": 0.00001}]
        stats = RegimeConditionedKelly._calc_stats(trades)
        assert stats["avg_win"] >= 0.001


# ───────────────────────────── TestIntegrationWithKelly ──────────────────

class TestIntegrationWithKelly:
    def test_stats_usable_by_kelly_optimizer(self):
        from omnix_services.trading_service.kelly_criterion import KellyCriterionOptimizer
        rck = RegimeConditionedKelly(db_url=None)
        rck.db_url = None
        stats = rck.get_regime_stats("TRENDING")
        kelly = KellyCriterionOptimizer(fractional_kelly=0.5)
        result = kelly.calculate_optimal_position(
            win_rate=stats.win_rate,
            avg_win=stats.avg_win,
            avg_loss=stats.avg_loss,
            total_capital=10000.0,
        )
        assert "kelly_fraction" in result or "position_size" in result

    def test_high_confidence_gives_aggressive_kelly(self):
        rck = make_rck(min_samples=5)
        good_trades = make_trades(40, win_frac=0.70, avg_win=0.03, avg_loss=0.01)
        with patch.object(rck, "_query_trades", side_effect=[good_trades, []]):
            result = rck.get_regime_stats("TRENDING", SYMBOL)
        assert result.kelly_fraction_raw > 0.0

    def test_default_stats_not_aggressive(self):
        rck = RegimeConditionedKelly(db_url=None)
        rck.db_url = None
        stats = rck.get_regime_stats("VOLATILE")
        assert stats.kelly_fraction_raw == 0.0

    def test_different_regimes_different_stats(self):
        rck = make_rck(min_samples=3)
        trending_trades = make_trades(10, win_frac=0.70, avg_win=0.03)
        bearish_trades = make_trades(10, win_frac=0.30, avg_loss=0.03)
        with patch.object(rck, "_query_trades", side_effect=[trending_trades, []]):
            trending_stats = rck.get_regime_stats("TRENDING", SYMBOL)
        with patch.object(rck, "_query_trades", side_effect=[bearish_trades, []]):
            bearish_stats = rck.get_regime_stats("BEARISH", SYMBOL)
        assert trending_stats.win_rate > bearish_stats.win_rate

    def test_result_is_always_returned(self):
        rck = make_rck()
        with patch.object(rck, "_query_trades", side_effect=Exception("crash")):
            result = rck.get_regime_stats("TRENDING", SYMBOL)
        assert isinstance(result, RegimeKellyStats)

    def test_to_dict_is_json_serializable(self):
        import json
        rck = RegimeConditionedKelly(db_url=None)
        rck.db_url = None
        stats = rck.get_regime_stats("TRENDING")
        serialized = json.dumps(stats.to_dict())
        assert isinstance(serialized, str)
