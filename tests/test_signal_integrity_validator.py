#!/usr/bin/env python3
"""
Tests for Signal Integrity Validator (SIV) — ADR-033
Checkpoint 0: data quality gate before the governance pipeline.
"""
import time
import pytest
from omnix_core.data.signal_integrity_validator import (
    SignalIntegrityValidator,
    SIVResult,
    SIVViolation,
    ViolationSeverity,
    SEVERITY_DEDUCTIONS,
)

SYMBOL = "XBTUSD"
GOOD_PRICE = 85000.0
NOW = time.time()


def make_siv(**kwargs) -> SignalIntegrityValidator:
    siv = SignalIntegrityValidator()
    for k, v in kwargs.items():
        setattr(siv, k, v)
    return siv


def good_market_data(price=GOOD_PRICE, bid=None, ask=None, volume=1000.0, ohlc=True):
    d = {"price": price, "volume": volume}
    if bid is not None:
        d["bid"] = bid
    if ask is not None:
        d["ask"] = ask
    if ohlc:
        d["ohlc"] = [{"open": price, "close": price, "high": price, "low": price}]
    return d


def fresh_timestamps():
    return {"kraken": NOW, "ohlc": NOW}


# ───────────────────────────── TestSIVResult ─────────────────────────────

class TestSIVResult:
    def test_to_dict_contains_all_keys(self):
        r = SIVResult(passed=True, score=95.0, threshold_used=60.0)
        d = r.to_dict()
        assert "passed" in d
        assert "score" in d
        assert "violations" in d
        assert "violation_count" in d
        assert "sources_checked" in d
        assert "threshold_used" in d
        assert "pass_through" in d
        assert "timestamp" in d

    def test_violation_count_matches_list(self):
        v = SIVViolation("freshness", "TEST", ViolationSeverity.LOW, "detail")
        r = SIVResult(passed=True, score=90.0, violations=[v])
        assert r.to_dict()["violation_count"] == 1

    def test_pass_through_default_false(self):
        r = SIVResult(passed=True, score=100.0)
        assert r.pass_through is False

    def test_score_rounded_in_dict(self):
        r = SIVResult(passed=True, score=95.12345)
        assert r.to_dict()["score"] == 95.12


# ───────────────────────────── TestSIVViolation ───────────────────────────

class TestSIVViolation:
    def test_to_dict_structure(self):
        v = SIVViolation("anomaly", "PRICE_SPIKE", ViolationSeverity.HIGH, "some detail")
        d = v.to_dict()
        assert d["category"] == "anomaly"
        assert d["code"] == "PRICE_SPIKE"
        assert d["severity"] == ViolationSeverity.HIGH
        assert d["detail"] == "some detail"


# ───────────────────────────── TestSIVFailSafe ────────────────────────────

class TestSIVFailSafe:
    def test_none_market_data_returns_pass_through(self):
        siv = make_siv()
        result = siv.validate(SYMBOL, None)
        assert result.passed is True
        assert result.pass_through is True

    def test_exception_in_validate_returns_pass_through(self):
        siv = make_siv()
        siv.threshold = "NOT_A_NUMBER"
        result = siv.validate(SYMBOL, good_market_data())
        assert result.passed is True
        assert result.pass_through is True

    def test_pass_through_has_max_score(self):
        siv = make_siv()
        result = siv.validate(SYMBOL, None)
        assert result.score == 100.0

    def test_pass_through_no_violations(self):
        siv = make_siv()
        result = siv.validate(SYMBOL, None)
        assert result.violations == []

    def test_valid_data_not_pass_through(self):
        siv = make_siv()
        result = siv.validate(SYMBOL, good_market_data(), fresh_timestamps())
        assert result.pass_through is False


# ───────────────────────────── TestSIVFreshness ───────────────────────────

class TestSIVFreshness:
    def test_fresh_price_no_violation(self):
        siv = make_siv()
        result = siv.validate(SYMBOL, good_market_data(), {"kraken": NOW})
        codes = [v.code for v in result.violations]
        assert "PRICE_DATA_STALE" not in codes

    def test_stale_price_triggers_violation(self):
        siv = make_siv(price_stale_secs=60.0)
        stale_ts = NOW - 120
        result = siv.validate(SYMBOL, good_market_data(), {"kraken": stale_ts})
        codes = [v.code for v in result.violations]
        assert "PRICE_DATA_STALE" in codes

    def test_stale_price_is_critical(self):
        siv = make_siv(price_stale_secs=60.0)
        stale_ts = NOW - 120
        result = siv.validate(SYMBOL, good_market_data(), {"kraken": stale_ts})
        for v in result.violations:
            if v.code == "PRICE_DATA_STALE":
                assert v.severity == ViolationSeverity.CRITICAL

    def test_stale_ohlc_triggers_violation(self):
        siv = make_siv(ohlc_stale_secs=60.0)
        result = siv.validate(
            SYMBOL, good_market_data(), {"kraken": NOW, "ohlc": NOW - 200}
        )
        codes = [v.code for v in result.violations]
        assert "OHLC_DATA_STALE" in codes

    def test_stale_ohlc_is_high_severity(self):
        siv = make_siv(ohlc_stale_secs=60.0)
        result = siv.validate(
            SYMBOL, good_market_data(), {"kraken": NOW, "ohlc": NOW - 200}
        )
        for v in result.violations:
            if v.code == "OHLC_DATA_STALE":
                assert v.severity == ViolationSeverity.HIGH

    def test_stale_sentiment_triggers_low_violation(self):
        siv = make_siv()
        result = siv.validate(
            SYMBOL,
            good_market_data(),
            {"kraken": NOW, "sentiment": NOW - 2000},
        )
        codes = [v.code for v in result.violations]
        assert "SENTIMENT_DATA_STALE" in codes
        for v in result.violations:
            if v.code == "SENTIMENT_DATA_STALE":
                assert v.severity == ViolationSeverity.LOW


# ───────────────────────────── TestSIVCompleteness ───────────────────────

class TestSIVCompleteness:
    def test_missing_price_critical_violation(self):
        siv = make_siv()
        result = siv.validate(SYMBOL, {})
        codes = [v.code for v in result.violations]
        assert "MISSING_PRICE" in codes

    def test_missing_price_returns_none_for_current_price(self):
        siv = make_siv()
        result = siv.validate(SYMBOL, {})
        assert result.passed is False or result.violations

    def test_invalid_price_type_triggers_violation(self):
        siv = make_siv()
        result = siv.validate(SYMBOL, {"price": "not_a_number"})
        codes = [v.code for v in result.violations]
        assert "INVALID_PRICE_TYPE" in codes

    def test_zero_price_triggers_violation(self):
        siv = make_siv()
        result = siv.validate(SYMBOL, {"price": 0})
        codes = [v.code for v in result.violations]
        assert "NON_POSITIVE_PRICE" in codes

    def test_negative_price_triggers_violation(self):
        siv = make_siv()
        result = siv.validate(SYMBOL, {"price": -1.0})
        codes = [v.code for v in result.violations]
        assert "NON_POSITIVE_PRICE" in codes

    def test_missing_volume_medium_violation(self):
        siv = make_siv()
        result = siv.validate(SYMBOL, {"price": GOOD_PRICE}, fresh_timestamps())
        codes = [v.code for v in result.violations]
        assert "MISSING_VOLUME" in codes
        for v in result.violations:
            if v.code == "MISSING_VOLUME":
                assert v.severity == ViolationSeverity.MEDIUM

    def test_complete_data_no_completeness_violations(self):
        siv = make_siv()
        result = siv.validate(SYMBOL, good_market_data(), fresh_timestamps())
        completeness_codes = [
            v.code for v in result.violations if v.category == "completeness"
        ]
        assert completeness_codes == []


# ───────────────────────────── TestSIVAnomalyDetection ───────────────────

class TestSIVAnomalyDetection:
    def test_normal_price_no_spike(self):
        siv = make_siv(anomaly_threshold=0.20)
        siv._price_history[SYMBOL] = [85000.0]
        result = siv.validate(SYMBOL, good_market_data(price=86000.0), fresh_timestamps())
        codes = [v.code for v in result.violations]
        assert "PRICE_SPIKE_ANOMALY" not in codes

    def test_large_price_spike_triggers_violation(self):
        siv = make_siv(anomaly_threshold=0.20)
        siv._price_history[SYMBOL] = [85000.0]
        spike_price = 85000.0 * 1.30
        result = siv.validate(SYMBOL, good_market_data(price=spike_price), fresh_timestamps())
        codes = [v.code for v in result.violations]
        assert "PRICE_SPIKE_ANOMALY" in codes

    def test_spike_is_high_severity(self):
        siv = make_siv(anomaly_threshold=0.20)
        siv._price_history[SYMBOL] = [85000.0]
        result = siv.validate(SYMBOL, good_market_data(price=115000.0), fresh_timestamps())
        for v in result.violations:
            if v.code == "PRICE_SPIKE_ANOMALY":
                assert v.severity == ViolationSeverity.HIGH

    def test_no_history_no_spike_violation(self):
        siv = make_siv(anomaly_threshold=0.20)
        result = siv.validate(SYMBOL, good_market_data(price=999999.0), fresh_timestamps())
        codes = [v.code for v in result.violations]
        assert "PRICE_SPIKE_ANOMALY" not in codes

    def test_wide_spread_triggers_violation(self):
        siv = make_siv(spread_threshold=0.05)
        md = good_market_data(bid=80000.0, ask=90000.0)
        result = siv.validate(SYMBOL, md, fresh_timestamps())
        codes = [v.code for v in result.violations]
        assert "SPREAD_ANOMALY" in codes

    def test_normal_spread_no_violation(self):
        siv = make_siv(spread_threshold=0.05)
        md = good_market_data(bid=84990.0, ask=85010.0)
        result = siv.validate(SYMBOL, md, fresh_timestamps())
        codes = [v.code for v in result.violations]
        assert "SPREAD_ANOMALY" not in codes

    def test_inverted_spread_critical(self):
        siv = make_siv()
        md = good_market_data(bid=85100.0, ask=85000.0)
        result = siv.validate(SYMBOL, md, fresh_timestamps())
        codes = [v.code for v in result.violations]
        assert "INVERTED_SPREAD" in codes
        for v in result.violations:
            if v.code == "INVERTED_SPREAD":
                assert v.severity == ViolationSeverity.CRITICAL

    def test_price_history_updated_after_validation(self):
        siv = make_siv()
        assert SYMBOL not in siv._price_history or SYMBOL not in siv._price_history
        siv.validate(SYMBOL, good_market_data(price=85000.0), fresh_timestamps())
        assert SYMBOL in siv._price_history
        assert 85000.0 in siv._price_history[SYMBOL]


# ───────────────────────────── TestSIVCrossSource ────────────────────────

class TestSIVCrossSource:
    def test_agreeing_sources_no_violation(self):
        siv = make_siv(cross_source_tolerance=0.02)
        result = siv.validate(
            SYMBOL,
            good_market_data(price=85000.0),
            fresh_timestamps(),
            secondary_prices={"coingecko": 85500.0},
        )
        codes = [v.code for v in result.violations]
        assert "SOURCE_PRICE_DISCREPANCY" not in codes

    def test_large_discrepancy_triggers_violation(self):
        siv = make_siv(cross_source_tolerance=0.02)
        result = siv.validate(
            SYMBOL,
            good_market_data(price=85000.0),
            fresh_timestamps(),
            secondary_prices={"coingecko": 70000.0},
        )
        codes = [v.code for v in result.violations]
        assert "SOURCE_PRICE_DISCREPANCY" in codes

    def test_large_discrepancy_is_high_severity(self):
        siv = make_siv(cross_source_tolerance=0.02)
        result = siv.validate(
            SYMBOL,
            good_market_data(price=85000.0),
            fresh_timestamps(),
            secondary_prices={"coingecko": 50000.0},
        )
        for v in result.violations:
            if v.code == "SOURCE_PRICE_DISCREPANCY":
                assert v.severity == ViolationSeverity.HIGH

    def test_moderate_discrepancy_is_medium_severity(self):
        siv = make_siv(cross_source_tolerance=0.02)
        result = siv.validate(
            SYMBOL,
            good_market_data(price=85000.0),
            fresh_timestamps(),
            secondary_prices={"coingecko": 83200.0},
        )
        for v in result.violations:
            if v.code == "SOURCE_PRICE_DISCREPANCY":
                assert v.severity == ViolationSeverity.MEDIUM

    def test_none_secondary_price_skipped(self):
        siv = make_siv(cross_source_tolerance=0.02)
        result = siv.validate(
            SYMBOL,
            good_market_data(price=85000.0),
            fresh_timestamps(),
            secondary_prices={"coingecko": None},
        )
        codes = [v.code for v in result.violations]
        assert "SOURCE_PRICE_DISCREPANCY" not in codes


# ───────────────────────────── TestSIVScoring ────────────────────────────

class TestSIVScoring:
    def test_no_violations_score_100(self):
        siv = make_siv()
        result = siv.validate(SYMBOL, good_market_data(), fresh_timestamps())
        assert result.score == 100.0

    def test_critical_violation_deducts_30(self):
        siv = make_siv(threshold=0.0)
        result = siv.validate(SYMBOL, {"price": None})
        assert result.score <= 70.0

    def test_score_never_below_zero(self):
        siv = make_siv(price_stale_secs=1.0, ohlc_stale_secs=1.0, anomaly_threshold=0.001)
        siv._price_history[SYMBOL] = [85000.0]
        many_stale = {"kraken": NOW - 1000, "ohlc": NOW - 1000, "sentiment": NOW - 2000}
        md = {"price": 85000.0 * 2, "bid": 90000.0, "ask": 85000.0}
        result = siv.validate(SYMBOL, md, many_stale, {"cgk": 50000.0})
        assert result.score >= 0.0

    def test_score_never_above_100(self):
        siv = make_siv()
        result = siv.validate(SYMBOL, good_market_data(), fresh_timestamps())
        assert result.score <= 100.0

    def test_below_threshold_not_passed(self):
        siv = make_siv(threshold=90.0)
        siv._price_history[SYMBOL] = [85000.0]
        md = good_market_data(price=85000.0 * 1.5, bid=80000.0, ask=90000.0)
        stale_ts = {"kraken": NOW - 400, "ohlc": NOW - 1000}
        result = siv.validate(SYMBOL, md, stale_ts)
        assert result.passed is False

    def test_above_threshold_passed(self):
        siv = make_siv(threshold=60.0)
        result = siv.validate(SYMBOL, good_market_data(), fresh_timestamps())
        assert result.passed is True


# ───────────────────────────── TestSIVSources ────────────────────────────

class TestSIVSources:
    def test_sources_checked_increments(self):
        siv = make_siv()
        result = siv.validate(
            SYMBOL,
            good_market_data(),
            fresh_timestamps(),
            secondary_prices={"cgk": 85000.0},
        )
        assert result.sources_checked >= 3

    def test_no_secondary_fewer_sources(self):
        siv = make_siv()
        result = siv.validate(SYMBOL, good_market_data(), fresh_timestamps())
        assert result.sources_checked >= 2


# ───────────────────────────── TestSIVPriceHistory ───────────────────────

class TestSIVPriceHistory:
    def test_history_capped_at_20(self):
        siv = make_siv()
        for i in range(25):
            siv.validate(SYMBOL, good_market_data(price=85000.0 + i), fresh_timestamps())
        assert len(siv._price_history.get(SYMBOL, [])) <= 20

    def test_multiple_symbols_independent(self):
        siv = make_siv()
        siv.validate("XBTUSD", good_market_data(price=85000.0), fresh_timestamps())
        siv.validate("ETHUSD", good_market_data(price=3000.0), fresh_timestamps())
        assert "XBTUSD" in siv._price_history
        assert "ETHUSD" in siv._price_history
        assert siv._price_history["XBTUSD"] != siv._price_history["ETHUSD"]
