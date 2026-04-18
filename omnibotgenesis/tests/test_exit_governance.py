#!/usr/bin/env python3
"""
Tests for Exit Governance Layer (EGL) — ADR-036
3-gate exit governance pipeline with PQC-signed receipts.
"""
import pytest
from unittest.mock import MagicMock, patch
from omnix_core.governance.exit_governance import (
    ExitGovernanceEngine,
    ExitGovernanceResult,
    _REGIME_TP_MULTIPLIERS,
    _REGIME_SL_MULTIPLIERS,
)

SYMBOL = "XBTUSD"
ENTRY_PRICE = 85000.0
TP_PRICE = 87550.0   # +3%
SL_PRICE = 83300.0   # -2%


def make_egl(db_url=None, tcv=None) -> ExitGovernanceEngine:
    with patch.object(ExitGovernanceEngine, "_ensure_db_schema", return_value=None), \
         patch.object(ExitGovernanceEngine, "_init_pqc", return_value=None):
        egl = ExitGovernanceEngine(db_url="", tcv_instance=tcv)
    egl.db_url = None
    egl._pqc_keys = None
    egl._dilithium3 = None
    egl._store_receipt = lambda *a, **kw: None
    return egl


def make_position(action="BUY", entry=ENTRY_PRICE, tp=TP_PRICE, sl=SL_PRICE):
    return {
        "position_id": "test-pos-001",
        "symbol": SYMBOL,
        "action": action,
        "entry_price": entry,
        "take_profit_price": tp,
        "stop_loss_price": sl,
    }


def long_buy_context(ema="SELL"):
    return {"ema_signal_direction": ema, "recent_ema_scores": [60, 55, 50]}


# ───────────────────────────── TestExitGovernanceResult ──────────────────

class TestExitGovernanceResult:
    def test_to_dict_contains_all_keys(self):
        r = ExitGovernanceResult(should_exit=True, reason="TP_EXIT", confidence=85.0)
        d = r.to_dict()
        assert "should_exit" in d
        assert "reason" in d
        assert "confidence" in d
        assert "regime_adjusted_tp" in d
        assert "regime_adjusted_sl" in d
        assert "gate1_threshold_verdict" in d
        assert "gate2_coherence_verdict" in d
        assert "gate3_tcv_verdict" in d
        assert "regime_used" in d
        assert "exit_receipt_id" in d
        assert "pqc_signature" in d
        assert "pass_through" in d
        assert "timestamp" in d

    def test_pass_through_default_false(self):
        r = ExitGovernanceResult(should_exit=True, reason="x", confidence=80.0)
        assert r.pass_through is False

    def test_confidence_rounded_in_dict(self):
        r = ExitGovernanceResult(should_exit=True, reason="x", confidence=85.1234)
        assert r.to_dict()["confidence"] == 85.12

    def test_receipt_id_is_uuid_format(self):
        import re
        r = ExitGovernanceResult(should_exit=True, reason="x", confidence=80.0)
        assert re.match(r"[0-9a-f-]{36}", r.exit_receipt_id)

    def test_tp_rounded_in_dict(self):
        r = ExitGovernanceResult(
            should_exit=True, reason="x", confidence=80.0, regime_adjusted_tp=87550.12345678901
        )
        assert len(str(r.to_dict()["regime_adjusted_tp"]).split(".")[-1]) <= 8


# ───────────────────────────── TestRegimeAdjustedThresholds ──────────────

class TestRegimeAdjustedThresholds:
    def test_trending_widens_tp(self):
        egl = make_egl()
        pos = make_position(tp=TP_PRICE)
        r = egl.evaluate_exit(pos, ENTRY_PRICE * 1.04, False, False, regime="TRENDING")
        assert r.regime_adjusted_tp > TP_PRICE

    def test_trending_tightens_sl(self):
        egl = make_egl()
        pos = make_position(sl=SL_PRICE)
        r = egl.evaluate_exit(pos, ENTRY_PRICE, False, False, regime="TRENDING")
        assert r.regime_adjusted_sl > SL_PRICE

    def test_ranging_narrows_tp(self):
        egl = make_egl()
        pos = make_position(tp=TP_PRICE)
        r = egl.evaluate_exit(pos, ENTRY_PRICE * 1.03, False, False, regime="RANGING")
        assert r.regime_adjusted_tp < TP_PRICE

    def test_ranging_widens_sl(self):
        egl = make_egl()
        pos = make_position(sl=SL_PRICE)
        r = egl.evaluate_exit(pos, ENTRY_PRICE, False, False, regime="RANGING")
        assert r.regime_adjusted_sl < SL_PRICE

    def test_volatile_tightens_both(self):
        egl = make_egl()
        pos = make_position(tp=TP_PRICE, sl=SL_PRICE)
        r = egl.evaluate_exit(pos, ENTRY_PRICE, False, False, regime="VOLATILE")
        assert r.regime_adjusted_tp < TP_PRICE
        assert r.regime_adjusted_sl > SL_PRICE

    def test_bearish_most_conservative_tp(self):
        egl = make_egl()
        pos = make_position(tp=TP_PRICE, sl=SL_PRICE)
        r_trending = egl.evaluate_exit(pos, ENTRY_PRICE, False, False, regime="TRENDING")
        r_bearish = egl.evaluate_exit(pos, ENTRY_PRICE, False, False, regime="BEARISH")
        assert r_bearish.regime_adjusted_tp < r_trending.regime_adjusted_tp

    def test_neutral_no_change(self):
        egl = make_egl()
        pos = make_position(tp=TP_PRICE, sl=SL_PRICE)
        r = egl.evaluate_exit(pos, ENTRY_PRICE, False, False, regime="NEUTRAL")
        assert abs(r.regime_adjusted_tp - TP_PRICE) < 0.01
        assert abs(r.regime_adjusted_sl - SL_PRICE) < 0.01

    def test_unknown_regime_uses_default(self):
        egl = make_egl()
        pos = make_position(tp=TP_PRICE, sl=SL_PRICE)
        r = egl.evaluate_exit(pos, ENTRY_PRICE, False, False, regime="UNKNOWN_XYZ")
        assert r.regime_adjusted_tp == pytest.approx(TP_PRICE, rel=0.001)

    def test_adjusted_tp_reflected_in_result(self):
        egl = make_egl()
        pos = make_position(tp=TP_PRICE)
        r = egl.evaluate_exit(pos, ENTRY_PRICE, False, False, regime="TRENDING")
        assert r.regime_adjusted_tp is not None
        assert r.regime_adjusted_tp > 0

    def test_sl_exit_overrides_coherence(self):
        egl = make_egl()
        pos = make_position(entry=ENTRY_PRICE, sl=SL_PRICE)
        sl_price_hit = SL_PRICE - 100.0
        r = egl.evaluate_exit(
            pos, sl_price_hit, False, True, regime="VOLATILE",
            context={"ema_signal_direction": "BUY"}
        )
        assert r.should_exit is True
        assert "SL_EXIT" in r.reason


# ───────────────────────────── TestExitCoherenceGate ─────────────────────

class TestExitCoherenceGate:
    def test_ema_sell_confirms_buy_exit(self):
        egl = make_egl()
        pos = make_position(entry=ENTRY_PRICE, tp=TP_PRICE)
        tp_hit_price = ENTRY_PRICE + (TP_PRICE - ENTRY_PRICE) * 1.5
        r = egl.evaluate_exit(
            pos, tp_hit_price, True, False, regime="TRENDING",
            context={"ema_signal_direction": "SELL"}
        )
        assert r.gate2_coherence_verdict is True

    def test_ema_buy_and_small_loss_denies_exit(self):
        egl = make_egl()
        pos = make_position(entry=ENTRY_PRICE, tp=TP_PRICE)
        loss_price = ENTRY_PRICE * 0.995
        r = egl.evaluate_exit(
            pos, loss_price, False, False, regime="TRENDING",
            context={"ema_signal_direction": "BUY"}
        )
        assert r.gate2_coherence_verdict is False

    def test_ema_buy_and_profit_allows_exit(self):
        egl = make_egl()
        pos = make_position(entry=ENTRY_PRICE, tp=TP_PRICE)
        profit_price = TP_PRICE * 1.5
        r = egl.evaluate_exit(
            pos, profit_price, True, False, regime="RANGING",
            context={"ema_signal_direction": "BUY"}
        )
        assert r.gate2_coherence_verdict is True

    def test_no_ema_context_defaults_to_allow(self):
        egl = make_egl()
        pos = make_position(entry=ENTRY_PRICE, tp=TP_PRICE)
        tp_hit = TP_PRICE + 100
        r = egl.evaluate_exit(pos, tp_hit, True, False, regime="NEUTRAL", context={})
        assert r.gate2_coherence_verdict is True

    def test_sell_position_ema_buy_confirms_exit(self):
        egl = make_egl()
        pos = make_position(action="SELL", entry=ENTRY_PRICE, tp=ENTRY_PRICE * 0.97)
        price_below_tp = ENTRY_PRICE * 0.96
        r = egl.evaluate_exit(
            pos, price_below_tp, True, False, regime="BEARISH",
            context={"ema_signal_direction": "BUY"}
        )
        assert r.gate2_coherence_verdict is True

    def test_confidence_is_in_range(self):
        egl = make_egl()
        pos = make_position(entry=ENTRY_PRICE, tp=TP_PRICE)
        r = egl.evaluate_exit(
            pos, TP_PRICE * 1.1, True, False, regime="NEUTRAL",
            context={"ema_signal_direction": "SELL"}
        )
        assert 0.0 <= r.confidence <= 100.0

    def test_gate1_false_gate2_false_no_exit(self):
        egl = make_egl()
        pos = make_position(entry=ENTRY_PRICE, tp=TP_PRICE, sl=SL_PRICE)
        r = egl.evaluate_exit(
            pos, ENTRY_PRICE * 1.005, False, False, regime="TRENDING",
            context={"ema_signal_direction": "BUY"}
        )
        assert r.should_exit is False

    def test_gate1_tp_hit_gate2_coherent_exits(self):
        egl = make_egl()
        pos = make_position(entry=ENTRY_PRICE, tp=TP_PRICE, sl=SL_PRICE)
        adj_tp = ENTRY_PRICE + (TP_PRICE - ENTRY_PRICE) * _REGIME_TP_MULTIPLIERS.get("RANGING", 1.0)
        above_adj_tp = adj_tp + 100.0
        r = egl.evaluate_exit(
            pos, above_adj_tp, True, False, regime="RANGING",
            context={"ema_signal_direction": "SELL"}
        )
        assert r.should_exit is True


# ───────────────────────────── TestTCVExitCheck ──────────────────────────

class TestTCVExitCheck:
    def test_no_tcv_gate3_is_none(self):
        egl = make_egl(tcv=None)
        pos = make_position(entry=ENTRY_PRICE, tp=TP_PRICE)
        r = egl.evaluate_exit(pos, TP_PRICE * 1.2, True, False, regime="TRENDING")
        assert r.gate3_tcv_verdict is None

    def test_with_tcv_gate3_evaluated_on_exit(self):
        mock_tcv = MagicMock()
        mock_tcv.validate.return_value = MagicMock(admissible=True)
        egl = make_egl(tcv=mock_tcv)
        pos = make_position(entry=ENTRY_PRICE, tp=TP_PRICE)
        adj_tp = ENTRY_PRICE + (TP_PRICE - ENTRY_PRICE) * 1.3
        r = egl.evaluate_exit(
            pos, adj_tp * 1.1, True, False, regime="TRENDING",
            context={"ema_signal_direction": "SELL"}
        )
        assert r.gate3_tcv_verdict is not None

    def test_tcv_exception_returns_neutral(self):
        mock_tcv = MagicMock()
        mock_tcv.validate.side_effect = Exception("TCV crash")
        egl = make_egl(tcv=mock_tcv)
        pos = make_position(entry=ENTRY_PRICE, tp=TP_PRICE)
        r = egl.evaluate_exit(
            pos, TP_PRICE * 2, True, False, regime="TRENDING",
            context={"ema_signal_direction": "SELL"}
        )
        assert isinstance(r, ExitGovernanceResult)

    def test_gate3_only_evaluated_on_naive_exit(self):
        mock_tcv = MagicMock()
        mock_tcv.validate.return_value = MagicMock(admissible=True)
        egl = make_egl(tcv=mock_tcv)
        pos = make_position(entry=ENTRY_PRICE, tp=TP_PRICE)
        r = egl.evaluate_exit(
            pos, ENTRY_PRICE, False, False, regime="NEUTRAL",
            context={"ema_signal_direction": "SELL"}
        )
        assert r.gate3_tcv_verdict is None

    def test_regime_in_result(self):
        egl = make_egl()
        pos = make_position()
        r = egl.evaluate_exit(pos, ENTRY_PRICE, False, False, regime="VOLATILE")
        assert r.regime_used == "VOLATILE"


# ───────────────────────────── TestExitReceipt ───────────────────────────

class TestExitReceipt:
    def test_receipt_id_present(self):
        egl = make_egl()
        pos = make_position()
        r = egl.evaluate_exit(pos, ENTRY_PRICE, False, False)
        assert len(r.exit_receipt_id) == 36

    def test_pqc_signature_present(self):
        egl = make_egl()
        pos = make_position()
        r = egl.evaluate_exit(pos, ENTRY_PRICE, False, False)
        assert len(r.pqc_signature) > 0

    def test_receipt_id_unique_per_evaluation(self):
        egl = make_egl()
        pos = make_position()
        r1 = egl.evaluate_exit(pos, ENTRY_PRICE, False, False)
        r2 = egl.evaluate_exit(pos, ENTRY_PRICE, False, False)
        assert r1.exit_receipt_id != r2.exit_receipt_id

    def test_signature_is_hex_string(self):
        egl = make_egl()
        pos = make_position()
        r = egl.evaluate_exit(pos, ENTRY_PRICE, False, False)
        assert isinstance(r.pqc_signature, str)
        assert len(r.pqc_signature) > 0

    def test_sign_receipt_sha256_fallback(self):
        egl = make_egl()
        egl._pqc_keys = None
        egl._dilithium3 = None
        payload = {"test": "data", "amount": 100}
        sig = egl._sign_receipt(payload)
        assert len(sig) == 64

    def test_sign_receipt_different_payloads_different_sigs(self):
        egl = make_egl()
        egl._pqc_keys = None
        egl._dilithium3 = None
        sig1 = egl._sign_receipt({"key": "value1"})
        sig2 = egl._sign_receipt({"key": "value2"})
        assert sig1 != sig2


# ───────────────────────────── TestFailSafe ──────────────────────────────

class TestFailSafe:
    def test_exception_returns_pass_through(self):
        egl = make_egl()
        pos = make_position()
        with patch.object(egl, "_evaluate_internal", side_effect=RuntimeError("crash")):
            r = egl.evaluate_exit(pos, ENTRY_PRICE, True, False)
        assert r.pass_through is True

    def test_pass_through_preserves_naive_exit_true(self):
        egl = make_egl()
        pos = make_position()
        with patch.object(egl, "_evaluate_internal", side_effect=RuntimeError("crash")):
            r = egl.evaluate_exit(pos, ENTRY_PRICE, True, False)
        assert r.should_exit is True

    def test_pass_through_preserves_naive_exit_false(self):
        egl = make_egl()
        pos = make_position()
        with patch.object(egl, "_evaluate_internal", side_effect=RuntimeError("crash")):
            r = egl.evaluate_exit(pos, ENTRY_PRICE, False, False)
        assert r.should_exit is False

    def test_no_db_no_crash(self):
        with patch.object(ExitGovernanceEngine, "_ensure_db_schema", return_value=None):
            egl = ExitGovernanceEngine(db_url=None)
        egl.db_url = None
        pos = make_position()
        r = egl.evaluate_exit(pos, ENTRY_PRICE, False, False)
        assert isinstance(r, ExitGovernanceResult)

    def test_always_returns_result_type(self):
        egl = make_egl()
        pos = make_position()
        r = egl.evaluate_exit(pos, ENTRY_PRICE, True, False)
        assert isinstance(r, ExitGovernanceResult)


# ───────────────────────────── TestIntegration ───────────────────────────

class TestIntegration:
    def test_sl_hit_always_exits(self):
        egl = make_egl()
        pos = make_position(entry=ENTRY_PRICE, sl=SL_PRICE)
        sl_breach_price = SL_PRICE - 1000.0
        r = egl.evaluate_exit(pos, sl_breach_price, False, True, regime="TRENDING")
        assert r.should_exit is True

    def test_no_hit_no_exit(self):
        egl = make_egl()
        pos = make_position(entry=ENTRY_PRICE, tp=TP_PRICE, sl=SL_PRICE)
        mid_price = ENTRY_PRICE * 1.01
        r = egl.evaluate_exit(pos, mid_price, False, False, regime="TRENDING")
        assert r.should_exit is False

    def test_gate_verdicts_logged_in_result(self):
        egl = make_egl()
        pos = make_position(entry=ENTRY_PRICE, tp=TP_PRICE, sl=SL_PRICE)
        r = egl.evaluate_exit(pos, ENTRY_PRICE * 1.5, True, False, regime="NEUTRAL",
                              context={"ema_signal_direction": "SELL"})
        assert isinstance(r.gate1_threshold_verdict, bool)
        assert isinstance(r.gate2_coherence_verdict, bool)

    def test_result_serializable_to_dict(self):
        import json
        egl = make_egl()
        pos = make_position()
        r = egl.evaluate_exit(pos, ENTRY_PRICE, False, False)
        json_str = json.dumps(r.to_dict())
        assert isinstance(json_str, str)

    def test_high_confidence_on_clear_sl_hit(self):
        egl = make_egl()
        pos = make_position(entry=ENTRY_PRICE, sl=SL_PRICE)
        r = egl.evaluate_exit(pos, SL_PRICE - 500, False, True, regime="BEARISH")
        assert r.confidence >= 85.0
