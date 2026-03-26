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
