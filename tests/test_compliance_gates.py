"""
Tests for Compliance Gates — CP-9 AML, CP-10 Fraud, CP-11 Jurisdiction
ADR-047, ADR-048, ADR-049
"""

import os
import sys
import pytest

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")


class TestAMLGate:
    """CP-9: AML Gate — FATF/FinCEN/UAE Central Bank"""

    def _gate(self, **kwargs):
        from omnix_core.governance.aml_gate import AMLGate, AMLGateConfig
        cfg = AMLGateConfig(enabled=True, **kwargs)
        return AMLGate(cfg)

    def test_disabled_gate_always_passes(self):
        from omnix_core.governance.aml_gate import AMLGate, AMLGateConfig
        gate = AMLGate(AMLGateConfig(enabled=False))
        r = gate.evaluate("XMR/USD", "BUY")
        assert r.admissible
        assert r.pass_through

    def test_privacy_coin_blocked(self):
        gate = self._gate(block_privacy_coins=True)
        r = gate.evaluate("XMR/USD", "BUY")
        assert not r.admissible
        assert "PRIVACY_COIN" in r.violation

    def test_mixer_token_blocked_independently(self):
        gate = self._gate(block_privacy_coins=False, block_mixer_tokens=True)
        r = gate.evaluate("TORN/USD", "BUY")
        assert not r.admissible
        assert "MIXER" in r.violation

    def test_mixer_disabled_passes(self):
        gate = self._gate(block_privacy_coins=True, block_mixer_tokens=False)
        r = gate.evaluate("TORN/USD", "BUY")
        assert r.admissible

    def test_clean_asset_passes(self):
        gate = self._gate(block_privacy_coins=True, block_mixer_tokens=True)
        r = gate.evaluate("BTC/USD", "BUY")
        assert r.admissible
        assert not r.violation

    def test_hold_action_passes_privacy_coin(self):
        gate = self._gate(block_privacy_coins=True)
        r = gate.evaluate("XMR/USD", "HOLD")
        assert r.admissible

    def test_aml_score_range(self):
        gate = self._gate()
        r = gate.evaluate("ETH/USD", "BUY")
        assert 0.0 <= r.aml_score <= 100.0

    def test_load_aml_config_from_env_defaults(self):
        from omnix_core.governance.aml_gate import load_aml_config_from_env
        cfg = load_aml_config_from_env()
        assert cfg.enabled is False
        assert cfg.block_privacy_coins is True
        assert cfg.block_mixer_tokens is True

    def test_env_enabled_flag(self):
        from omnix_core.governance.aml_gate import load_aml_config_from_env
        os.environ["AML_GATE_ENABLED"] = "true"
        cfg = load_aml_config_from_env()
        assert cfg.enabled is True
        os.environ["AML_GATE_ENABLED"] = "false"


class TestFraudGate:
    """CP-10: Fraud Detection Gate — EU AI Act Art.6 / MiFID II / SEC"""

    def _gate(self, **kwargs):
        from omnix_core.governance.fraud_gate import FraudGate, FraudGateConfig
        cfg = FraudGateConfig(enabled=True, **kwargs)
        return FraudGate(cfg)

    def test_disabled_gate_always_passes(self):
        from omnix_core.governance.fraud_gate import FraudGate, FraudGateConfig
        gate = FraudGate(FraudGateConfig(enabled=False))
        r = gate.evaluate("BTC/USD", "BUY")
        assert r.admissible
        assert r.pass_through

    def test_high_dci_blocks_buy(self):
        gate = self._gate(dci_threshold=65.0, block_extreme_dci=True)
        r = gate.evaluate("BTC/USD", "BUY", dci_score=85.0)
        assert not r.admissible
        assert "EXTREME_DCI" in r.violation

    def test_low_dci_passes(self):
        gate = self._gate(dci_threshold=65.0, block_extreme_dci=True)
        r = gate.evaluate("BTC/USD", "BUY", dci_score=30.0)
        assert r.admissible

    def test_high_dci_blocked_regardless_of_action(self):
        gate = self._gate(dci_threshold=65.0, block_extreme_dci=True)
        r = gate.evaluate("BTC/USD", "BUY", dci_score=90.0)
        assert not r.admissible
        assert r.violation == "EXTREME_DCI"

    def test_integrity_score_range(self):
        gate = self._gate()
        r = gate.evaluate("BTC/USD", "BUY", dci_score=50.0)
        assert 0.0 <= r.integrity_score <= 100.0

    def test_load_fraud_config_from_env_defaults(self):
        from omnix_core.governance.fraud_gate import load_fraud_config_from_env
        cfg = load_fraud_config_from_env()
        assert cfg.enabled is False


class TestJurisdictionGate:
    """CP-11: Jurisdiction Gate — UAE VARA / EU MiCA / US FinCEN / GCC"""

    def _gate(self, jurisdiction="UAE", **kwargs):
        from omnix_core.governance.jurisdiction_gate import JurisdictionGate, JurisdictionGateConfig
        cfg = JurisdictionGateConfig(enabled=True, jurisdiction=jurisdiction, **kwargs)
        return JurisdictionGate(cfg)

    def test_disabled_gate_always_passes(self):
        from omnix_core.governance.jurisdiction_gate import JurisdictionGate, JurisdictionGateConfig
        gate = JurisdictionGate(JurisdictionGateConfig(enabled=False))
        r = gate.evaluate("XMR/USD", "BUY", "spot")
        assert r.admissible
        assert r.pass_through

    def test_uae_spot_btc_passes(self):
        gate = self._gate("UAE")
        r = gate.evaluate("BTC/USD", "BUY", "spot")
        assert r.admissible

    def test_uae_leveraged_blocked(self):
        gate = self._gate("UAE")
        r = gate.evaluate("BTC/USD", "BUY", "leveraged")
        assert not r.admissible
        assert "LEVERAGE" in r.violation

    def test_uae_privacy_coin_blocked(self):
        gate = self._gate("UAE")
        r = gate.evaluate("XMR/USD", "BUY", "spot")
        assert not r.admissible

    def test_us_xmr_blocked(self):
        gate = self._gate("US")
        r = gate.evaluate("XMR/USD", "BUY", "spot")
        assert not r.admissible

    def test_eu_btc_passes(self):
        gate = self._gate("EU")
        r = gate.evaluate("BTC/USD", "BUY", "spot")
        assert r.admissible

    def test_global_xmr_passes(self):
        gate = self._gate("GLOBAL")
        r = gate.evaluate("XMR/USD", "BUY", "spot")
        assert r.admissible

    def test_compliance_score_range(self):
        gate = self._gate("UAE")
        r = gate.evaluate("BTC/USD", "BUY", "spot")
        assert 0.0 <= r.compliance_score <= 100.0

    def test_jurisdiction_in_result(self):
        gate = self._gate("UAE")
        r = gate.evaluate("BTC/USD", "BUY", "spot")
        assert r.jurisdiction == "UAE"

    def test_env_op_type(self):
        from omnix_core.governance.jurisdiction_gate import load_jurisdiction_config_from_env
        os.environ["JURISDICTION"] = "UAE"
        os.environ["JURISDICTION_GATE_ENABLED"] = "true"
        os.environ["JURISDICTION_OP_TYPE"] = "leveraged"
        cfg = load_jurisdiction_config_from_env()
        assert cfg.jurisdiction == "UAE"
        assert cfg.operation_type == "leveraged"
        os.environ["JURISDICTION_GATE_ENABLED"] = "false"
        os.environ.pop("JURISDICTION_OP_TYPE", None)

    def test_hold_action_passes(self):
        gate = self._gate("UAE")
        r = gate.evaluate("XMR/USD", "HOLD", "spot")
        assert r.admissible


class TestComplianceGatesIntegration:
    """Integration: B2B External API compliance_config"""

    def _engine(self):
        from omnix_core.governance.external_evaluator import GovernanceEvaluationEngine
        return GovernanceEvaluationEngine()

    def _signals(self):
        return {
            'probability_score': 80,
            'risk_exposure': 25,
            'signal_coherence': 75,
            'trend_persistence': 70,
            'stress_resilience': 65,
            'logic_consistency': 80,
        }

    def test_no_compliance_config_xmr_approved(self):
        r = self._engine().evaluate(self._signals(), asset="XMR/USD")
        assert r["decision"] == "APPROVED"
        assert "compliance" not in r

    def test_aml_blocks_xmr(self):
        r = self._engine().evaluate(self._signals(), asset="XMR/USD",
                                    compliance_config={"aml_enabled": True})
        assert r["decision"] == "BLOCKED"
        assert r["compliance"]["aml_compliance"]["result"] == "failed"

    def test_aml_passes_btc(self):
        r = self._engine().evaluate(self._signals(), asset="BTC/USD",
                                    compliance_config={"aml_enabled": True})
        assert r["decision"] == "APPROVED"
        assert r["compliance"]["aml_compliance"]["result"] == "passed"

    def test_jurisdiction_blocks_xmr_uae(self):
        r = self._engine().evaluate(self._signals(), asset="XMR/USD",
                                    compliance_config={
                                        "jurisdiction_enabled": True,
                                        "jurisdiction": "UAE",
                                    })
        assert r["decision"] == "BLOCKED"
        assert r["compliance"]["jurisdiction_compliance"]["result"] == "failed"

    def test_jurisdiction_blocks_leverage_uae(self):
        r = self._engine().evaluate(self._signals(), asset="BTC/USD",
                                    compliance_config={
                                        "jurisdiction_enabled": True,
                                        "jurisdiction": "UAE",
                                        "operation_type": "leveraged",
                                    })
        assert r["decision"] == "BLOCKED"

    def test_jurisdiction_passes_btc_uae_spot(self):
        r = self._engine().evaluate(self._signals(), asset="BTC/USD",
                                    compliance_config={
                                        "jurisdiction_enabled": True,
                                        "jurisdiction": "UAE",
                                        "operation_type": "spot",
                                    })
        assert r["decision"] == "APPROVED"

    def test_compliance_block_propagates_to_veto_chain(self):
        r = self._engine().evaluate(self._signals(), asset="XMR/USD",
                                    compliance_config={"aml_enabled": True})
        cp9_veto = any(v.get("checkpoint_id") == "CP-9" for v in r["veto_chain"])
        assert cp9_veto

    def test_compliance_block_in_decision_trace(self):
        r = self._engine().evaluate(self._signals(), asset="XMR/USD",
                                    compliance_config={"aml_enabled": True})
        trace_has_aml = any("AML_VETO" in t for t in r["decision_trace"])
        assert trace_has_aml

    def test_bad_signals_still_blocked_even_without_compliance(self):
        bad = {'probability_score': 20, 'risk_exposure': 95, 'signal_coherence': 15,
               'trend_persistence': 10, 'stress_resilience': 10, 'logic_consistency': 10}
        r = self._engine().evaluate(bad, asset="BTC/USD")
        assert r["decision"] == "BLOCKED"
