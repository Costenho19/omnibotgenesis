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

    def test_disabled_gate_score_0(self):
        gate = self._gate()
        r = gate.evaluate()
        assert r.admission_score == 0.0


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
    Tests for _run_cag_session_check (ADR-050 session-level gate) in AutoTradingBot.
    CAG is called ONCE per trading cycle, BEFORE the symbol loop.
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
            bot.config = {"trading_pair": "MULTI"}
            return bot

    def test_cag_session_check_method_exists(self):
        """_run_cag_session_check method exists on AutoTradingBot."""
        bot = self._make_bot()
        assert hasattr(bot, "_run_cag_session_check")
        assert callable(bot._run_cag_session_check)

    def test_cag_disabled_env_returns_true(self):
        """When CAG_ENABLED is not set (default=false), returns True (pass-through)."""
        import os
        from unittest.mock import patch

        bot = self._make_bot()

        with patch.dict(os.environ, {"CAG_ENABLED": "false"}):
            result = bot._run_cag_session_check(user_id="user1", session_id="SES-TEST-001")

        assert result is True

    def test_cag_enabled_all_safe_returns_true(self):
        """CAG_ENABLED=true, all params safe → SESSION ADMITTED → returns True."""
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
            result = bot._run_cag_session_check(user_id="user1", session_id="SES-TEST-002")

        assert result is True

    def test_cag_enabled_high_volatility_returns_false(self):
        """CAG_ENABLED=true, volatility=99 → SESSION BLOCKED → returns False."""
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
            result = bot._run_cag_session_check(user_id="user2", session_id="SES-TEST-003")

        assert result is False

    def test_cag_blocked_triggers_receipt_generation(self):
        """When session is blocked, receipt_engine.generate_receipt is called."""
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
            bot._run_cag_session_check(user_id="", session_id="SES-TEST-004")

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
            bot._run_cag_session_check(user_id="", session_id="SES-TEST-005")

        call_args = bot.receipt_engine.generate_receipt.call_args
        receipt_input = call_args[0][0]
        assert receipt_input["decision"] == "BLOCK"
        assert "CONTEXT_ADMISSION_BLOCKED" in str(receipt_input)

    def test_cag_blocked_receipt_has_session_id(self):
        """Receipt context_admission block contains the session_id."""
        import os
        from unittest.mock import patch

        bot = self._make_bot()
        test_session_id = "SES-RECEIPT-TEST-006"

        with patch.dict(os.environ, {
            "CAG_ENABLED": "true",
            "CAG_GLOBAL_VOLATILITY": "99.0",
            "CAG_CROSS_PAIR_CORRELATION": "10.0",
            "CAG_LIQUIDITY_SCORE": "90.0",
            "CAG_MACRO_RISK": "10.0",
        }):
            bot._run_cag_session_check(user_id="", session_id=test_session_id)

        call_args = bot.receipt_engine.generate_receipt.call_args
        receipt_input = call_args[0][0]
        assert test_session_id in str(receipt_input)

    def test_cag_blocked_persists_to_db(self):
        """When session is blocked, log_session_admission_event is called on db_service."""
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
            bot._run_cag_session_check(user_id="user7", session_id="SES-TEST-007")

        bot.db_service.log_session_admission_event.assert_called_once()
        kwargs = bot.db_service.log_session_admission_event.call_args[1]
        assert kwargs["admitted"] is False
        assert kwargs["symbol"] == "SESSION"
        assert kwargs["user_id"] == "user7"

    def test_cag_admitted_no_receipt_generated(self):
        """When session is admitted, receipt_engine is NOT called."""
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
            result = bot._run_cag_session_check(user_id="", session_id="SES-TEST-008")

        assert result is True
        bot.receipt_engine.generate_receipt.assert_not_called()

    def test_cag_fail_safe_exception_returns_true(self):
        """If cag_evaluate_session raises, method returns True (fail-safe pass-through)."""
        import os
        from unittest.mock import patch

        bot = self._make_bot()

        with patch("omnix_core.bot.auto_trading_bot.cag_evaluate_session",
                   side_effect=RuntimeError("simulated hardware failure")):
            with patch.dict(os.environ, {"CAG_ENABLED": "true"}):
                result = bot._run_cag_session_check(user_id="", session_id="SES-TEST-009")

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
            result = bot._run_cag_session_check(user_id="", session_id="SES-TEST-010")

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
            result = bot._run_cag_session_check(user_id="", session_id="SES-TEST-011")

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
        import inspect

        sig = inspect.signature(DatabaseServiceEnterprise.log_session_admission_event)
        params = set(sig.parameters.keys())
        required = {
            "event_id", "admitted", "admission_score", "violation",
            "global_volatility", "cross_pair_correlation", "liquidity_score", "macro_risk",
            "cag_config", "gate_checks", "receipt_id", "user_id", "symbol",
            "session_id",
        }
        assert required.issubset(params)

    def test_method_signature_has_compat_columns(self):
        """DB method has compatibility columns: session_id (mapped to decision, reason_code, etc)."""
        from omnix_services.database_service.database_service import DatabaseServiceEnterprise
        import inspect

        sig = inspect.signature(DatabaseServiceEnterprise.log_session_admission_event)
        params = set(sig.parameters.keys())
        assert "session_id" in params


class TestCAGReceiptEngine:
    """
    Tests for context_admission inclusion in DecisionReceiptEngine.
    """

    def test_context_admission_included_in_receipt_payload(self):
        """context_admission block is included in the generated receipt when present."""
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        from unittest.mock import patch, MagicMock

        engine = DecisionReceiptEngine.__new__(DecisionReceiptEngine)
        engine.db_url = None
        engine._signing_keys = None
        engine._provider = None

        with patch.object(engine, '_append_to_transparency_chain'):
            receipt = engine.generate_receipt({
                "symbol": "BTC/USD",
                "decision": "BLOCK",
                "decision_trace": ["CAG SESSION_BLOCKED: volatility_threshold"],
                "context_admission": {
                    "check": "enabled",
                    "result": "blocked",
                    "admission_score": 20.0,
                    "violation": "volatility_threshold",
                    "veto_type": "CONTEXT_ADMISSION_BLOCKED",
                    "parameters": {
                        "global_volatility": 99.0,
                        "cross_pair_correlation": 10.0,
                        "liquidity_score": 90.0,
                        "macro_risk": 10.0,
                    },
                    "gate_checks": [],
                },
            })

        assert "context_admission" in receipt
        assert receipt["context_admission"]["veto_type"] == "CONTEXT_ADMISSION_BLOCKED"

    def test_veto_type_is_first_class_field_in_receipt(self):
        """veto_type=CONTEXT_ADMISSION_BLOCKED appears as a first-class receipt field."""
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        from unittest.mock import patch

        engine = DecisionReceiptEngine.__new__(DecisionReceiptEngine)
        engine.db_url = None
        engine._signing_keys = None
        engine._provider = None

        with patch.object(engine, '_append_to_transparency_chain'):
            receipt = engine.generate_receipt({
                "symbol": "ETH/USD",
                "decision": "BLOCK",
                "context_admission": {
                    "veto_type": "CONTEXT_ADMISSION_BLOCKED",
                    "admission_score": 15.0,
                },
            })

        assert receipt.get("veto_type") == "CONTEXT_ADMISSION_BLOCKED"

    def test_receipt_content_hash_includes_context_admission(self):
        """content_hash changes when context_admission changes — it's included in signing."""
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        from unittest.mock import patch

        engine = DecisionReceiptEngine.__new__(DecisionReceiptEngine)
        engine.db_url = None
        engine._signing_keys = None
        engine._provider = None

        base = {"symbol": "BTC/USD", "decision": "BLOCK"}
        with_ca = {**base, "context_admission": {"veto_type": "CONTEXT_ADMISSION_BLOCKED"}}

        with patch.object(engine, '_append_to_transparency_chain'):
            r1 = engine.generate_receipt(base)
            r2 = engine.generate_receipt(with_ca)

        assert r1["content_hash"] != r2["content_hash"]


class TestCAGMarketParams:
    """
    Tests for _get_cag_market_params — computed from bot session state.
    """

    def _make_bot(self, config_overrides=None):
        from unittest.mock import MagicMock
        from omnix_core.bot.auto_trading_bot import AutoTradingBot

        with __import__('unittest.mock', fromlist=['patch']).patch.object(
            AutoTradingBot, "__init__", lambda self, *a, **kw: None
        ):
            bot = AutoTradingBot.__new__(AutoTradingBot)
            bot.config = {
                "trading_pairs": ["BTC/USD"],
                "max_position_size_pct": 5.0,
                "paper_mode": True,
                "stop_loss_pct": 3.0,
            }
            if config_overrides:
                bot.config.update(config_overrides)
            return bot

    def test_returns_dict_with_four_keys(self):
        """_get_cag_market_params returns dict with 4 expected keys."""
        import os
        from unittest.mock import patch

        bot = self._make_bot()
        with patch.dict(os.environ, {
            "CAG_GLOBAL_VOLATILITY": "-1",
            "CAG_CROSS_PAIR_CORRELATION": "-1",
            "CAG_LIQUIDITY_SCORE": "-1",
            "CAG_MACRO_RISK": "-1",
        }):
            params = bot._get_cag_market_params("BTC/USD")

        assert set(params.keys()) == {
            "global_volatility", "cross_pair_correlation",
            "liquidity_score", "macro_risk", "_liquidity_source",
        }

    def test_paper_mode_gives_liquidity_100(self):
        """Paper mode → liquidity_score = 100.0 (no real execution constraints)."""
        import os
        from unittest.mock import patch

        bot = self._make_bot({"paper_mode": True})
        with patch.dict(os.environ, {"CAG_LIQUIDITY_SCORE": "-1"}):
            params = bot._get_cag_market_params("BTC/USD")

        assert params["liquidity_score"] == 100.0

    def test_real_mode_gives_liquidity_85(self):
        """Real mode → liquidity_score = 85.0 (Kraken major pairs, slight spread discount)."""
        import os
        from unittest.mock import patch

        bot = self._make_bot({"paper_mode": False})
        with patch.dict(os.environ, {"CAG_LIQUIDITY_SCORE": "-1"}):
            params = bot._get_cag_market_params("BTC/USD")

        assert params["liquidity_score"] == 85.0

    def test_cag_params_use_cached_black_swan_prob(self):
        """When _cag_signals_cache has black_swan_prob, global_volatility reflects it."""
        import os
        from unittest.mock import patch

        bot = self._make_bot()
        bot._cag_signals_cache = {"black_swan_prob": 0.70, "hmm_regime": "BEAR"}

        with patch.dict(os.environ, {"CAG_GLOBAL_VOLATILITY": "-1", "CAG_MACRO_RISK": "-1"}):
            params = bot._get_cag_market_params("BTC/USD")

        # black_swan_prob=0.70 → global_volatility = 70.0
        assert params["global_volatility"] == 70.0
        # macro_risk = 70.0 (bsp*100) + 10.0 (BEAR overlay) = 80.0
        assert params["macro_risk"] == 80.0

    def test_cag_params_bear_regime_raises_correlation(self):
        """BEAR regime in cache produces higher cross_pair_correlation than BULL."""
        import os
        from unittest.mock import patch

        bot_bear = self._make_bot()
        bot_bear._cag_signals_cache = {"black_swan_prob": 0.2, "hmm_regime": "BEAR"}

        bot_bull = self._make_bot()
        bot_bull._cag_signals_cache = {"black_swan_prob": 0.2, "hmm_regime": "BULL"}

        with patch.dict(os.environ, {
            "CAG_CROSS_PAIR_CORRELATION": "-1",
            "CAG_GLOBAL_VOLATILITY": "-1",
            "CAG_MACRO_RISK": "-1",
        }):
            p_bear = bot_bear._get_cag_market_params("BTC/USD")
            p_bull = bot_bull._get_cag_market_params("BTC/USD")

        assert p_bear["cross_pair_correlation"] > p_bull["cross_pair_correlation"]

    def test_cag_params_no_cache_gives_conservative_defaults(self):
        """When _cag_signals_cache is empty, params use conservative safe defaults."""
        import os
        from unittest.mock import patch

        bot = self._make_bot()
        bot._cag_signals_cache = {}  # empty cache

        with patch.dict(os.environ, {
            "CAG_GLOBAL_VOLATILITY": "-1",
            "CAG_CROSS_PAIR_CORRELATION": "-1",
            "CAG_LIQUIDITY_SCORE": "-1",
            "CAG_MACRO_RISK": "-1",
        }):
            params = bot._get_cag_market_params("BTC/USD")

        # Without cache, defaults should be conservative (not blocking)
        assert params["global_volatility"] == 30.0
        assert params["macro_risk"] == 20.0

    def test_update_cag_signals_cache_extracts_real_signals(self):
        """_update_cag_signals_cache stores black_swan_prob and hmm_regime from analysis."""
        bot = self._make_bot()
        bot._cag_signals_cache = {}

        analysis = {
            "black_swan": {"crash_probability": 0.35},
            "hmm_regime": {"regime": "BEAR", "confidence": 0.8},
            "current_price": 45000.0,
            "v52_analysis": {},
        }
        bot._update_cag_signals_cache(analysis)

        assert bot._cag_signals_cache["black_swan_prob"] == 0.35
        assert bot._cag_signals_cache["hmm_regime"] == "BEAR"
        assert bot._cag_signals_cache["hmm_confidence"] == 0.8
        assert bot._cag_signals_cache["current_price"] == 45000.0

    def test_env_override_takes_precedence(self):
        """Operator env var override takes precedence over computed values."""
        import os
        from unittest.mock import patch

        bot = self._make_bot()
        with patch.dict(os.environ, {
            "CAG_GLOBAL_VOLATILITY": "99.0",
            "CAG_CROSS_PAIR_CORRELATION": "50.0",
            "CAG_LIQUIDITY_SCORE": "30.0",
            "CAG_MACRO_RISK": "75.0",
        }):
            params = bot._get_cag_market_params("BTC/USD")

        assert params["global_volatility"] == 99.0
        assert params["cross_pair_correlation"] == 50.0
        assert params["liquidity_score"] == 30.0
        assert params["macro_risk"] == 75.0

    def test_more_pairs_increases_correlation_score(self):
        """More trading pairs → higher cross_pair_correlation (crypto co-movement)."""
        import os
        from unittest.mock import patch

        bot1 = self._make_bot({"trading_pairs": ["BTC/USD"]})
        bot5 = self._make_bot({"trading_pairs": ["BTC/USD", "ETH/USD", "XRP/USD", "SOL/USD", "ADA/USD"]})

        with patch.dict(os.environ, {"CAG_CROSS_PAIR_CORRELATION": "-1"}):
            p1 = bot1._get_cag_market_params("BTC/USD")
            p5 = bot5._get_cag_market_params("BTC/USD")

        assert p5["cross_pair_correlation"] > p1["cross_pair_correlation"]

    def test_all_values_are_non_negative(self):
        """All returned CAG parameter values are >= 0."""
        import os
        from unittest.mock import patch

        bot = self._make_bot()
        with patch.dict(os.environ, {
            "CAG_GLOBAL_VOLATILITY": "-1",
            "CAG_CROSS_PAIR_CORRELATION": "-1",
            "CAG_LIQUIDITY_SCORE": "-1",
            "CAG_MACRO_RISK": "-1",
        }):
            params = bot._get_cag_market_params("BTC/USD")

        for key, val in params.items():
            if not isinstance(val, (int, float)):
                continue
            assert val >= 0.0, f"{key} should be >= 0, got {val}"


# ──────────────────────────────────────────────────────────────────────────────
# ADR-050: evaluate_session() + SessionAdmissionResult — module-level API tests
# ──────────────────────────────────────────────────────────────────────────────

class TestEvaluateSessionAPI:
    """
    ADR-050: Tests for the module-level evaluate_session() function and
    SessionAdmissionResult type alias. These verify the public contract used by
    the bot and external_evaluator.
    """

    def test_evaluate_session_exists_and_callable(self):
        """evaluate_session is importable from context_admission_gate."""
        from omnix_core.governance.context_admission_gate import evaluate_session
        assert callable(evaluate_session)

    def test_session_admission_result_exists(self):
        """SessionAdmissionResult is importable and is an alias for CAGResult."""
        from omnix_core.governance.context_admission_gate import (
            SessionAdmissionResult, CAGResult
        )
        assert SessionAdmissionResult is CAGResult

    def test_evaluate_session_disabled_config_admits(self):
        """With disabled config, evaluate_session admits the session (pass-through)."""
        from omnix_core.governance.context_admission_gate import (
            evaluate_session, CAGConfig, SessionAdmissionResult
        )
        result = evaluate_session(
            global_volatility=99.0,
            cross_pair_correlation=99.0,
            liquidity_score=1.0,
            macro_risk=99.0,
            session_id="SES-UNIT-001",
            config=CAGConfig(enabled=False),
        )
        assert isinstance(result, SessionAdmissionResult)
        assert result.admitted is True
        assert result.pass_through is True

    def test_evaluate_session_enabled_safe_params_admits(self):
        """With enabled config and safe params, evaluate_session admits."""
        from omnix_core.governance.context_admission_gate import (
            evaluate_session, CAGConfig, SessionAdmissionResult
        )
        cfg = CAGConfig(
            enabled=True,
            global_volatility_threshold=80.0,
            cross_pair_correlation_threshold=90.0,
            liquidity_score_minimum=20.0,
            macro_risk_ceiling=85.0,
        )
        result = evaluate_session(
            global_volatility=10.0,
            cross_pair_correlation=15.0,
            liquidity_score=90.0,
            macro_risk=10.0,
            session_id="SES-UNIT-002",
            config=cfg,
        )
        assert isinstance(result, SessionAdmissionResult)
        assert result.admitted is True

    def test_evaluate_session_enabled_high_volatility_blocks(self):
        """With enabled config and high volatility, evaluate_session blocks."""
        from omnix_core.governance.context_admission_gate import (
            evaluate_session, CAGConfig, SessionAdmissionResult
        )
        cfg = CAGConfig(
            enabled=True,
            global_volatility_threshold=80.0,
            cross_pair_correlation_threshold=90.0,
            liquidity_score_minimum=20.0,
            macro_risk_ceiling=85.0,
        )
        result = evaluate_session(
            global_volatility=99.0,
            cross_pair_correlation=15.0,
            liquidity_score=90.0,
            macro_risk=10.0,
            session_id="SES-UNIT-003",
            config=cfg,
        )
        assert isinstance(result, SessionAdmissionResult)
        assert result.admitted is False
        assert result.pass_through is False

    def test_evaluate_session_accepts_session_id_param(self):
        """evaluate_session accepts session_id keyword argument without error."""
        from omnix_core.governance.context_admission_gate import evaluate_session, CAGConfig
        result = evaluate_session(
            global_volatility=0.0,
            cross_pair_correlation=0.0,
            liquidity_score=100.0,
            macro_risk=0.0,
            session_id="SES-UNIT-CUSTOM-IDXYZ",
            config=CAGConfig(enabled=False),
        )
        assert result is not None

    def test_evaluate_session_fail_safe_on_bad_config(self):
        """evaluate_session returns pass-through result on config/exception path."""
        from omnix_core.governance.context_admission_gate import evaluate_session, SessionAdmissionResult
        from unittest.mock import patch
        with patch("omnix_core.governance.context_admission_gate.ContextAdmissionGate",
                   side_effect=RuntimeError("boom")):
            result = evaluate_session(session_id="SES-UNIT-ERR-001")
        assert isinstance(result, SessionAdmissionResult)
        assert result.admitted is True
        assert result.pass_through is True
