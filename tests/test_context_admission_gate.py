"""
Tests for Context Admission Gate (CAG) — ADR-050
Session-level pre-admission gate for global market conditions.
"""

import os
import sys
import pytest

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")


class TestCAGDisabled:
    """Gate disabled — always pass-through"""

    def _gate(self, **kwargs):
        from omnix_core.governance.context_admission_gate import (
            ContextAdmissionGate, CAGConfig,
        )
        cfg = CAGConfig(enabled=False, **kwargs)
        return ContextAdmissionGate(cfg)

    def test_disabled_gate_admits_all(self):
        gate = self._gate()
        r = gate.evaluate(
            global_volatility=99.0,
            cross_pair_correlation=99.0,
            liquidity_score=0.0,
            macro_risk=99.0,
        )
        assert r.admitted is True
        assert r.pass_through is True

    def test_disabled_gate_has_no_violation(self):
        gate = self._gate()
        r = gate.evaluate(global_volatility=99.0)
        assert r.violation == ""

    def test_disabled_gate_score_100(self):
        gate = self._gate()
        r = gate.evaluate()
        assert r.admission_score == 100.0


class TestCAGVolatility:
    """Check 1: global_volatility must be BELOW threshold"""

    def _gate(self, **kwargs):
        from omnix_core.governance.context_admission_gate import (
            ContextAdmissionGate, CAGConfig,
        )
        cfg = CAGConfig(enabled=True, **kwargs)
        return ContextAdmissionGate(cfg)

    def test_volatility_below_threshold_admitted(self):
        gate = self._gate(global_volatility_threshold=80.0)
        r = gate.evaluate(global_volatility=50.0, liquidity_score=100.0)
        assert r.admitted is True

    def test_volatility_at_threshold_blocked(self):
        gate = self._gate(global_volatility_threshold=80.0)
        r = gate.evaluate(global_volatility=80.0, liquidity_score=100.0)
        assert r.admitted is False
        assert "GLOBAL_VOLATILITY" in r.violation

    def test_volatility_above_threshold_blocked(self):
        gate = self._gate(global_volatility_threshold=80.0)
        r = gate.evaluate(global_volatility=95.0, liquidity_score=100.0)
        assert r.admitted is False
        assert "GLOBAL_VOLATILITY" in r.violation

    def test_volatility_check_recorded_in_gate_checks(self):
        gate = self._gate(global_volatility_threshold=80.0)
        r = gate.evaluate(global_volatility=90.0, liquidity_score=100.0)
        vol_check = next((c for c in r.gate_checks if c["parameter"] == "global_volatility"), None)
        assert vol_check is not None
        assert vol_check["result"] == "FAIL"


class TestCAGCorrelation:
    """Check 2: cross_pair_correlation must be BELOW threshold"""

    def _gate(self, **kwargs):
        from omnix_core.governance.context_admission_gate import (
            ContextAdmissionGate, CAGConfig,
        )
        cfg = CAGConfig(enabled=True, **kwargs)
        return ContextAdmissionGate(cfg)

    def test_correlation_below_threshold_admitted(self):
        gate = self._gate(cross_pair_correlation_threshold=90.0)
        r = gate.evaluate(cross_pair_correlation=50.0, liquidity_score=100.0)
        assert r.admitted is True

    def test_correlation_at_threshold_blocked(self):
        gate = self._gate(cross_pair_correlation_threshold=90.0)
        r = gate.evaluate(cross_pair_correlation=90.0, liquidity_score=100.0)
        assert r.admitted is False
        assert "CORRELATION" in r.violation

    def test_correlation_above_threshold_blocked(self):
        gate = self._gate(cross_pair_correlation_threshold=90.0)
        r = gate.evaluate(cross_pair_correlation=95.0, liquidity_score=100.0)
        assert r.admitted is False
        assert "CORRELATION" in r.violation


class TestCAGLiquidity:
    """Check 3: liquidity_score must be ABOVE minimum"""

    def _gate(self, **kwargs):
        from omnix_core.governance.context_admission_gate import (
            ContextAdmissionGate, CAGConfig,
        )
        cfg = CAGConfig(enabled=True, **kwargs)
        return ContextAdmissionGate(cfg)

    def test_liquidity_above_minimum_admitted(self):
        gate = self._gate(liquidity_score_minimum=20.0)
        r = gate.evaluate(liquidity_score=80.0)
        assert r.admitted is True

    def test_liquidity_at_minimum_admitted(self):
        gate = self._gate(liquidity_score_minimum=20.0)
        r = gate.evaluate(liquidity_score=20.0)
        assert r.admitted is True

    def test_liquidity_below_minimum_blocked(self):
        gate = self._gate(liquidity_score_minimum=20.0)
        r = gate.evaluate(liquidity_score=10.0)
        assert r.admitted is False
        assert "LIQUIDITY" in r.violation

    def test_liquidity_zero_blocked(self):
        gate = self._gate(liquidity_score_minimum=20.0)
        r = gate.evaluate(liquidity_score=0.0)
        assert r.admitted is False


class TestCAGMacroRisk:
    """Check 4: macro_risk must be BELOW ceiling"""

    def _gate(self, **kwargs):
        from omnix_core.governance.context_admission_gate import (
            ContextAdmissionGate, CAGConfig,
        )
        cfg = CAGConfig(enabled=True, **kwargs)
        return ContextAdmissionGate(cfg)

    def test_macro_risk_below_ceiling_admitted(self):
        gate = self._gate(macro_risk_ceiling=85.0)
        r = gate.evaluate(macro_risk=50.0, liquidity_score=100.0)
        assert r.admitted is True

    def test_macro_risk_at_ceiling_blocked(self):
        gate = self._gate(macro_risk_ceiling=85.0)
        r = gate.evaluate(macro_risk=85.0, liquidity_score=100.0)
        assert r.admitted is False
        assert "MACRO_RISK" in r.violation

    def test_macro_risk_above_ceiling_blocked(self):
        gate = self._gate(macro_risk_ceiling=85.0)
        r = gate.evaluate(macro_risk=92.0, liquidity_score=100.0)
        assert r.admitted is False


class TestCAGAdmissionScore:
    """Admission score range and logic"""

    def _gate(self, **kwargs):
        from omnix_core.governance.context_admission_gate import (
            ContextAdmissionGate, CAGConfig,
        )
        cfg = CAGConfig(enabled=True, **kwargs)
        return ContextAdmissionGate(cfg)

    def test_admission_score_range_admitted(self):
        gate = self._gate()
        r = gate.evaluate(
            global_volatility=10.0,
            cross_pair_correlation=10.0,
            liquidity_score=90.0,
            macro_risk=10.0,
        )
        assert 0.0 <= r.admission_score <= 100.0
        assert r.admission_score == 100.0

    def test_admission_score_never_negative(self):
        gate = self._gate()
        r = gate.evaluate(
            global_volatility=99.0,
            cross_pair_correlation=99.0,
            liquidity_score=0.0,
            macro_risk=99.0,
        )
        assert r.admission_score >= 0.0

    def test_four_gate_checks_recorded(self):
        gate = self._gate()
        r = gate.evaluate(
            global_volatility=10.0,
            cross_pair_correlation=10.0,
            liquidity_score=90.0,
            macro_risk=10.0,
        )
        assert len(r.gate_checks) == 4


class TestCAGEnvConfig:
    """load_cag_config_from_env factory"""

    def test_disabled_by_default(self):
        from omnix_core.governance.context_admission_gate import load_cag_config_from_env
        os.environ.pop("CAG_ENABLED", None)
        cfg = load_cag_config_from_env()
        assert cfg.enabled is False

    def test_enabled_via_env(self):
        from omnix_core.governance.context_admission_gate import load_cag_config_from_env
        os.environ["CAG_ENABLED"] = "true"
        cfg = load_cag_config_from_env()
        assert cfg.enabled is True
        os.environ["CAG_ENABLED"] = "false"

    def test_custom_thresholds_via_env(self):
        from omnix_core.governance.context_admission_gate import load_cag_config_from_env
        os.environ["CAG_ENABLED"] = "true"
        os.environ["CAG_VOLATILITY_THRESHOLD"] = "60.0"
        os.environ["CAG_LIQUIDITY_MINIMUM"] = "30.0"
        cfg = load_cag_config_from_env()
        assert cfg.global_volatility_threshold == 60.0
        assert cfg.liquidity_score_minimum == 30.0
        os.environ["CAG_ENABLED"] = "false"
        os.environ.pop("CAG_VOLATILITY_THRESHOLD", None)
        os.environ.pop("CAG_LIQUIDITY_MINIMUM", None)

    def test_default_thresholds_match_constants(self):
        from omnix_core.governance.context_admission_gate import (
            load_cag_config_from_env,
            CAG_DEFAULT_VOLATILITY_THRESHOLD,
            CAG_DEFAULT_CORRELATION_THRESHOLD,
            CAG_DEFAULT_LIQUIDITY_MINIMUM,
            CAG_DEFAULT_MACRO_RISK_CEILING,
        )
        os.environ["CAG_ENABLED"] = "true"
        cfg = load_cag_config_from_env()
        assert cfg.global_volatility_threshold == CAG_DEFAULT_VOLATILITY_THRESHOLD
        assert cfg.cross_pair_correlation_threshold == CAG_DEFAULT_CORRELATION_THRESHOLD
        assert cfg.liquidity_score_minimum == CAG_DEFAULT_LIQUIDITY_MINIMUM
        assert cfg.macro_risk_ceiling == CAG_DEFAULT_MACRO_RISK_CEILING
        os.environ["CAG_ENABLED"] = "false"


class TestCAGFullSessionScenarios:
    """End-to-end session admission scenarios"""

    def _gate(self, **kwargs):
        from omnix_core.governance.context_admission_gate import (
            ContextAdmissionGate, CAGConfig,
        )
        cfg = CAGConfig(enabled=True, **kwargs)
        return ContextAdmissionGate(cfg)

    def test_ideal_market_conditions_admitted(self):
        gate = self._gate()
        r = gate.evaluate(
            global_volatility=20.0,
            cross_pair_correlation=30.0,
            liquidity_score=85.0,
            macro_risk=15.0,
        )
        assert r.admitted is True
        assert r.pass_through is False
        assert r.admission_score == 100.0

    def test_extreme_conditions_blocked(self):
        gate = self._gate()
        r = gate.evaluate(
            global_volatility=95.0,
            cross_pair_correlation=95.0,
            liquidity_score=5.0,
            macro_risk=95.0,
        )
        assert r.admitted is False
        assert r.admission_score < 100.0

    def test_single_violation_blocks_when_block_on_any(self):
        gate = self._gate(
            global_volatility_threshold=80.0,
            block_on_any_violation=True,
        )
        r = gate.evaluate(
            global_volatility=85.0,
            cross_pair_correlation=10.0,
            liquidity_score=90.0,
            macro_risk=10.0,
        )
        assert r.admitted is False

    def test_pass_through_false_when_enabled_and_admitted(self):
        gate = self._gate()
        r = gate.evaluate(
            global_volatility=10.0,
            cross_pair_correlation=10.0,
            liquidity_score=90.0,
            macro_risk=10.0,
        )
        assert r.admitted is True
        assert r.pass_through is False

    def test_global_volatility_stored_in_result(self):
        gate = self._gate()
        r = gate.evaluate(global_volatility=45.0, liquidity_score=80.0)
        assert r.global_volatility == 45.0

    def test_liquidity_stored_in_result(self):
        gate = self._gate()
        r = gate.evaluate(liquidity_score=72.0)
        assert r.liquidity_score == 72.0


# ──────────────────────────────────────────────────────────────────────────────
# ADR-050 INTEGRATION TESTS: Bot loop integration, receipt, DB, fail-safe
# ──────────────────────────────────────────────────────────────────────────────

class TestCAGBotIntegration:
    """
    Tests for _run_cag_cycle_check integration in AutoTradingBot.
    All DB and receipt calls are mocked — no real connections needed.
    """

    def _make_bot(self):
        """Return a minimal AutoTradingBot instance with mocked subsystems."""
        from unittest.mock import MagicMock, patch
        from omnix_core.bot.auto_trading_bot import AutoTradingBot

        with patch.object(AutoTradingBot, "__init__", lambda self, *a, **kw: None):
            bot = AutoTradingBot.__new__(AutoTradingBot)
            bot.db_service = MagicMock()
            bot.db_service.log_session_admission_event = MagicMock(return_value=True)
            bot.receipt_engine = MagicMock()
            bot.receipt_engine.get_last_hash = MagicMock(return_value="00" * 32)
            bot.receipt_engine.generate_receipt = MagicMock(
                return_value={"receipt_id": "REC-TESTCAG-001"}
            )
            bot.receipt_engine.store_receipt = MagicMock(return_value=True)
            return bot

    def test_cag_disabled_env_returns_true(self):
        """When CAG_ENABLED is not set (default=false), returns True (pass-through)."""
        import os
        from unittest.mock import patch

        bot = self._make_bot()

        with patch.dict(os.environ, {"CAG_ENABLED": "false"}):
            result = bot._run_cag_cycle_check(symbol="BTC/USD", user_id="user1")

        assert result is True

    def test_cag_enabled_all_safe_returns_true(self):
        """CAG_ENABLED=true, all params safe → admitted → returns True."""
        import os
        from unittest.mock import patch

        bot = self._make_bot()

        with patch.dict(os.environ, {
            "CAG_ENABLED": "true",
            "CAG_GLOBAL_VOLATILITY": "10.0",
            "CAG_CROSS_PAIR_CORRELATION": "10.0",
            "CAG_LIQUIDITY_SCORE": "90.0",
            "CAG_MACRO_RISK": "10.0",
        }):
            result = bot._run_cag_cycle_check(symbol="ETH/USD", user_id="user1")

        assert result is True

    def test_cag_enabled_high_volatility_returns_false(self):
        """CAG_ENABLED=true, volatility=99 → BLOCKED → returns False."""
        import os
        from unittest.mock import patch

        bot = self._make_bot()

        with patch.dict(os.environ, {
            "CAG_ENABLED": "true",
            "CAG_GLOBAL_VOLATILITY": "99.0",
            "CAG_CROSS_PAIR_CORRELATION": "10.0",
            "CAG_LIQUIDITY_SCORE": "90.0",
            "CAG_MACRO_RISK": "10.0",
        }):
            result = bot._run_cag_cycle_check(symbol="BTC/USD", user_id="user2")

        assert result is False

    def test_cag_blocked_triggers_receipt_generation(self):
        """When CAG blocks, receipt_engine.generate_receipt is called."""
        import os
        from unittest.mock import patch

        bot = self._make_bot()

        with patch.dict(os.environ, {
            "CAG_ENABLED": "true",
            "CAG_GLOBAL_VOLATILITY": "99.0",
            "CAG_CROSS_PAIR_CORRELATION": "10.0",
            "CAG_LIQUIDITY_SCORE": "90.0",
            "CAG_MACRO_RISK": "10.0",
        }):
            bot._run_cag_cycle_check(symbol="BTC/USD", user_id="")

        bot.receipt_engine.generate_receipt.assert_called_once()

    def test_cag_blocked_receipt_has_correct_decision(self):
        """Receipt input contains decision='BLOCK' and veto_type=CONTEXT_ADMISSION_BLOCKED."""
        import os
        from unittest.mock import patch

        bot = self._make_bot()

        with patch.dict(os.environ, {
            "CAG_ENABLED": "true",
            "CAG_GLOBAL_VOLATILITY": "99.0",
            "CAG_CROSS_PAIR_CORRELATION": "10.0",
            "CAG_LIQUIDITY_SCORE": "90.0",
            "CAG_MACRO_RISK": "10.0",
        }):
            bot._run_cag_cycle_check(symbol="BTC/USD", user_id="")

        call_args = bot.receipt_engine.generate_receipt.call_args
        receipt_input = call_args[0][0]
        assert receipt_input["decision"] == "BLOCK"
        assert "CONTEXT_ADMISSION_BLOCKED" in str(receipt_input)

    def test_cag_blocked_persists_to_db(self):
        """When CAG blocks, log_session_admission_event is called on db_service."""
        import os
        from unittest.mock import patch

        bot = self._make_bot()

        with patch.dict(os.environ, {
            "CAG_ENABLED": "true",
            "CAG_GLOBAL_VOLATILITY": "99.0",
            "CAG_CROSS_PAIR_CORRELATION": "10.0",
            "CAG_LIQUIDITY_SCORE": "90.0",
            "CAG_MACRO_RISK": "10.0",
        }):
            bot._run_cag_cycle_check(symbol="XBT/USD", user_id="user7")

        bot.db_service.log_session_admission_event.assert_called_once()
        kwargs = bot.db_service.log_session_admission_event.call_args[1]
        assert kwargs["admitted"] is False
        assert kwargs["symbol"] == "XBT/USD"
        assert kwargs["user_id"] == "user7"

    def test_cag_admitted_no_receipt_generated(self):
        """When CAG admits, receipt_engine is NOT called."""
        import os
        from unittest.mock import patch

        bot = self._make_bot()

        with patch.dict(os.environ, {
            "CAG_ENABLED": "true",
            "CAG_GLOBAL_VOLATILITY": "10.0",
            "CAG_CROSS_PAIR_CORRELATION": "10.0",
            "CAG_LIQUIDITY_SCORE": "90.0",
            "CAG_MACRO_RISK": "10.0",
        }):
            result = bot._run_cag_cycle_check(symbol="BTC/USD", user_id="")

        assert result is True
        bot.receipt_engine.generate_receipt.assert_not_called()

    def test_cag_fail_safe_exception_returns_true(self):
        """If CAG evaluate raises, method returns True (fail-safe pass-through)."""
        import os
        from unittest.mock import patch, MagicMock
        from omnix_core.bot.auto_trading_bot import AutoTradingBot

        bot = self._make_bot()

        # Force exception inside evaluate
        with patch("omnix_core.bot.auto_trading_bot.ContextAdmissionGate") as MockGate:
            instance = MagicMock()
            instance.evaluate.side_effect = RuntimeError("simulated hardware failure")
            MockGate.return_value = instance

            with patch.dict(os.environ, {"CAG_ENABLED": "true"}):
                result = bot._run_cag_cycle_check(symbol="BTC/USD", user_id="")

        assert result is True

    def test_cag_no_db_service_does_not_crash(self):
        """If db_service is None, method still runs without crashing."""
        import os
        from unittest.mock import patch

        bot = self._make_bot()
        bot.db_service = None

        with patch.dict(os.environ, {
            "CAG_ENABLED": "true",
            "CAG_GLOBAL_VOLATILITY": "99.0",
        }):
            result = bot._run_cag_cycle_check(symbol="BTC/USD", user_id="")

        # Should return False (blocked) or True (fail-safe), but never crash
        assert isinstance(result, bool)

    def test_cag_no_receipt_engine_does_not_crash(self):
        """If receipt_engine is None/falsy, method still runs without crashing."""
        import os
        from unittest.mock import patch

        bot = self._make_bot()
        bot.receipt_engine = None

        with patch.dict(os.environ, {
            "CAG_ENABLED": "true",
            "CAG_GLOBAL_VOLATILITY": "99.0",
        }):
            result = bot._run_cag_cycle_check(symbol="BTC/USD", user_id="")

        assert isinstance(result, bool)


class TestCAGDatabaseMethod:
    """
    Tests for DatabaseServiceEnterprise.log_session_admission_event.
    """

    def test_method_exists_on_db_service(self):
        """log_session_admission_event method is present in DatabaseServiceEnterprise."""
        from omnix_services.database_service.database_service import DatabaseServiceEnterprise
        assert hasattr(DatabaseServiceEnterprise, "log_session_admission_event")

    def test_method_returns_false_when_not_connected(self):
        """Returns False gracefully when DB is not connected."""
        from omnix_services.database_service.database_service import DatabaseServiceEnterprise
        from unittest.mock import patch

        with patch.object(DatabaseServiceEnterprise, "__init__", lambda self: None):
            svc = DatabaseServiceEnterprise.__new__(DatabaseServiceEnterprise)
            svc.connected = False

        result = svc.log_session_admission_event(
            event_id="EVT-TEST-001",
            admitted=False,
            admission_score=20.0,
            violation="volatility_threshold",
        )
        assert result is False

    def test_method_signature_accepts_all_fields(self):
        """Method accepts all expected keyword parameters without TypeError."""
        from omnix_services.database_service.database_service import DatabaseServiceEnterprise
        from unittest.mock import patch
        import inspect

        sig = inspect.signature(DatabaseServiceEnterprise.log_session_admission_event)
        params = set(sig.parameters.keys())
        required = {
            "event_id", "admitted", "admission_score", "violation",
            "global_volatility", "cross_pair_correlation", "liquidity_score", "macro_risk",
            "cag_config", "gate_checks", "receipt_id", "user_id", "symbol",
        }
        assert required.issubset(params)
