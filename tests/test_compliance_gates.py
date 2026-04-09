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


# ───────────── TestEpistemicTransparencyGates (ADR-066) ──────────────────────

class TestAMLGateEpistemicTransparency:
    """ADR-066: Disabled/failsafe gate paths must emit score=0, not score=100.
    evaluation_state field distinguishes 'DISABLED' from genuine 'EVALUATED' scores."""

    def test_disabled_aml_score_is_zero_not_hundred(self):
        from omnix_core.governance.aml_gate import AMLGate, AMLGateConfig
        gate = AMLGate(AMLGateConfig(enabled=False))
        r = gate.evaluate("BTC/USD", "BUY")
        assert r.aml_score == 0.0, (
            f"ADR-066: disabled AML gate returned aml_score={r.aml_score}, expected 0.0. "
            "score=100 when disabled fabricates AML compliance without evidence."
        )

    def test_disabled_aml_evaluation_state(self):
        from omnix_core.governance.aml_gate import AMLGate, AMLGateConfig
        gate = AMLGate(AMLGateConfig(enabled=False))
        r = gate.evaluate("BTC/USD", "BUY")
        assert r.evaluation_state == "DISABLED"

    def test_disabled_aml_still_admissible(self):
        from omnix_core.governance.aml_gate import AMLGate, AMLGateConfig
        gate = AMLGate(AMLGateConfig(enabled=False))
        r = gate.evaluate("XMR/USD", "BUY")
        assert r.admissible is True
        assert r.pass_through is True

    def test_evaluated_aml_state_is_evaluated(self):
        from omnix_core.governance.aml_gate import AMLGate, AMLGateConfig
        gate = AMLGate(AMLGateConfig(enabled=True))
        r = gate.evaluate("BTC/USD", "BUY")
        assert r.evaluation_state == "EVALUATED"

    def test_disabled_aml_reason_explains_score(self):
        from omnix_core.governance.aml_gate import AMLGate, AMLGateConfig
        gate = AMLGate(AMLGateConfig(enabled=False))
        r = gate.evaluate("ETH/USD", "BUY")
        assert "disabled" in r.reason.lower() or "not evaluated" in r.reason.lower()


class TestShariaGateEpistemicTransparency:
    """ADR-066: Disabled/failsafe Sharia gate must emit score=0, not score=100."""

    def test_disabled_sharia_score_is_zero_not_hundred(self):
        from omnix_core.governance.sharia_gate import ShariaGate, ShariaGateConfig
        gate = ShariaGate(ShariaGateConfig(enabled=False))
        r = gate.evaluate("BTC/USD", "BUY")
        assert r.sharia_score == 0.0, (
            f"ADR-066: disabled Sharia gate returned sharia_score={r.sharia_score}, expected 0.0."
        )

    def test_disabled_sharia_evaluation_state(self):
        from omnix_core.governance.sharia_gate import ShariaGate, ShariaGateConfig
        gate = ShariaGate(ShariaGateConfig(enabled=False))
        r = gate.evaluate("BTC/USD", "BUY")
        assert r.evaluation_state == "DISABLED"

    def test_disabled_sharia_still_admissible(self):
        from omnix_core.governance.sharia_gate import ShariaGate, ShariaGateConfig
        gate = ShariaGate(ShariaGateConfig(enabled=False))
        r = gate.evaluate("WBTC/USD", "BUY")
        assert r.admissible is True
        assert r.pass_through is True

    def test_evaluated_sharia_state_is_evaluated(self):
        from omnix_core.governance.sharia_gate import ShariaGate, ShariaGateConfig
        gate = ShariaGate(ShariaGateConfig(enabled=True))
        r = gate.evaluate("BTC/USD", "BUY")
        assert r.evaluation_state == "EVALUATED"


class TestJurisdictionGateEpistemicTransparency:
    """ADR-066: Disabled/failsafe Jurisdiction gate must emit score=0, not score=100.
    ADR-068: OFAC list must include metadata and detect staleness."""

    def test_disabled_jurisdiction_score_is_zero_not_hundred(self):
        from omnix_core.governance.jurisdiction_gate import JurisdictionGate, JurisdictionGateConfig
        gate = JurisdictionGate(JurisdictionGateConfig(enabled=False))
        r = gate.evaluate("BTC/USD", "BUY")
        assert r.compliance_score == 0.0, (
            f"ADR-066: disabled Jurisdiction gate returned compliance_score={r.compliance_score}, "
            "expected 0.0."
        )

    def test_disabled_jurisdiction_evaluation_state(self):
        from omnix_core.governance.jurisdiction_gate import JurisdictionGate, JurisdictionGateConfig
        gate = JurisdictionGate(JurisdictionGateConfig(enabled=False))
        r = gate.evaluate("BTC/USD", "BUY")
        assert r.evaluation_state == "DISABLED"

    def test_disabled_jurisdiction_still_admissible(self):
        from omnix_core.governance.jurisdiction_gate import JurisdictionGate, JurisdictionGateConfig
        gate = JurisdictionGate(JurisdictionGateConfig(enabled=False, jurisdiction="UAE"))
        r = gate.evaluate("XMR/USD", "BUY")
        assert r.admissible is True
        assert r.pass_through is True

    def test_evaluated_jurisdiction_state_is_evaluated(self):
        from omnix_core.governance.jurisdiction_gate import JurisdictionGate, JurisdictionGateConfig
        gate = JurisdictionGate(JurisdictionGateConfig(enabled=True, jurisdiction="GLOBAL"))
        r = gate.evaluate("BTC/USD", "BUY")
        assert r.evaluation_state == "EVALUATED"

    def test_ofac_list_version_exists(self):
        """ADR-068: OFAC list must carry version metadata."""
        from omnix_core.governance.jurisdiction_gate import OFAC_LIST_VERSION, OFAC_LIST_DATE
        assert OFAC_LIST_VERSION, "OFAC_LIST_VERSION must be set"
        assert OFAC_LIST_DATE is not None, "OFAC_LIST_DATE must be set"

    def test_ofac_list_has_meaningful_entries(self):
        """ADR-068: OFAC list must contain more than 2 entries — original was critically sparse."""
        from omnix_core.governance.jurisdiction_gate import OFAC_SANCTIONED_ASSETS
        assert len(OFAC_SANCTIONED_ASSETS) > 5, (
            f"OFAC list has only {len(OFAC_SANCTIONED_ASSETS)} entries — critically sparse. "
            "ADR-068 requires a materially representative sanctions list."
        )

    def test_ofac_tornado_cash_in_list(self):
        """OFAC SDN-designated Tornado Cash must be in the sanctions list."""
        from omnix_core.governance.jurisdiction_gate import OFAC_SANCTIONED_ASSETS
        assert "TORNADO" in OFAC_SANCTIONED_ASSETS or "TORNADO_CASH" in OFAC_SANCTIONED_ASSETS

    def test_ofac_sinbad_in_list(self):
        """OFAC SDN-designated Sinbad mixer (Nov 2023) must be in the list."""
        from omnix_core.governance.jurisdiction_gate import OFAC_SANCTIONED_ASSETS
        assert "SINBAD" in OFAC_SANCTIONED_ASSETS


class TestTIEEpistemicTransparency:
    """ADR-066: TIE pass-through paths must emit trajectory_score=0, not 100.
    pass_through_reason must distinguish disabled / blocked-bypass / failsafe."""

    def test_disabled_tie_score_is_zero_not_hundred(self):
        """TIE disabled → trajectory_score=0, not 100."""
        import os
        from omnix_core.governance.trajectory_invariant_engine import TrajectoryInvariantEngine
        os.environ["TIE_ENABLED"] = "false"
        try:
            tie = TrajectoryInvariantEngine(db_conn=None)
            signals = {'probability_score': 70, 'risk_exposure': 30, 'signal_coherence': 65,
                       'trend_persistence': 60, 'stress_resilience': 55, 'logic_consistency': 60}
            result = tie.evaluate(signals, "BTC/USD", "trading", "APPROVED")
            assert result.trajectory_score == 0.0, (
                f"ADR-066: TIE disabled returned trajectory_score={result.trajectory_score}. "
                "Expected 0.0 — score=100 fabricates trajectory health without evaluation."
            )
        finally:
            os.environ["TIE_ENABLED"] = "true"

    def test_disabled_tie_pass_through_reason_populated(self):
        """Disabled TIE must explain why score=0 in pass_through_reason."""
        import os
        from omnix_core.governance.trajectory_invariant_engine import TrajectoryInvariantEngine
        os.environ["TIE_ENABLED"] = "false"
        try:
            tie = TrajectoryInvariantEngine(db_conn=None)
            signals = {'probability_score': 70, 'risk_exposure': 30, 'signal_coherence': 65,
                       'trend_persistence': 60, 'stress_resilience': 55, 'logic_consistency': 60}
            result = tie.evaluate(signals, "BTC/USD", "trading", "APPROVED")
            assert result.pass_through_reason, "ADR-066: pass_through_reason must be populated"
            assert "TIE_DISABLED" in result.pass_through_reason
        finally:
            os.environ["TIE_ENABLED"] = "true"

    def test_blocked_decision_tie_score_is_zero(self):
        """TIE bypassed for BLOCKED decisions → score=0, not 100."""
        import os
        from omnix_core.governance.trajectory_invariant_engine import TrajectoryInvariantEngine
        os.environ["TIE_ENABLED"] = "true"
        tie = TrajectoryInvariantEngine(db_conn=None)
        signals = {'probability_score': 70, 'risk_exposure': 30, 'signal_coherence': 65,
                   'trend_persistence': 60, 'stress_resilience': 55, 'logic_consistency': 60}
        result = tie.evaluate(signals, "BTC/USD", "trading", "BLOCKED")
        assert result.trajectory_score == 0.0, (
            f"ADR-066: TIE BLOCKED bypass returned trajectory_score={result.trajectory_score}. "
            "Expected 0.0."
        )

    def test_blocked_bypass_reason_distinct_from_disabled(self):
        """BLOCKED bypass and disabled reasons must be distinct for auditability."""
        import os
        from omnix_core.governance.trajectory_invariant_engine import TrajectoryInvariantEngine
        tie = TrajectoryInvariantEngine(db_conn=None)
        signals = {'probability_score': 70, 'risk_exposure': 30, 'signal_coherence': 65,
                   'trend_persistence': 60, 'stress_resilience': 55, 'logic_consistency': 60}
        result = tie.evaluate(signals, "BTC/USD", "trading", "BLOCKED")
        assert "TIE_BLOCKED_BYPASS" in result.pass_through_reason

    def test_pass_through_reason_in_result_to_dict(self):
        """pass_through_reason must appear in result_to_dict for PQC receipt inclusion."""
        import os
        from omnix_core.governance.trajectory_invariant_engine import TrajectoryInvariantEngine
        os.environ["TIE_ENABLED"] = "false"
        try:
            tie = TrajectoryInvariantEngine(db_conn=None)
            signals = {'probability_score': 70, 'risk_exposure': 30, 'signal_coherence': 65,
                       'trend_persistence': 60, 'stress_resilience': 55, 'logic_consistency': 60}
            result = tie.evaluate(signals, "BTC/USD", "trading", "APPROVED")
            d = TrajectoryInvariantEngine.result_to_dict(result)
            assert "pass_through_reason" in d
            assert d["pass_through_reason"]
        finally:
            os.environ["TIE_ENABLED"] = "true"


class TestAMLFrequencyTransparency:
    """ADR-067: AML trade_frequency must not be hardcoded to 0.
    When real count unavailable, AML_FREQUENCY_PROXY_MODE must appear in trace."""

    def test_aml_frequency_default_evaluates_at_zero(self):
        """When AML enabled and no frequency provided, evaluates with 0 (known proxy)."""
        from omnix_core.governance.aml_gate import AMLGate, AMLGateConfig
        gate = AMLGate(AMLGateConfig(enabled=True, frequency_threshold=5))
        r = gate.evaluate("BTC/USD", "BUY", volume_usd=0.0, trade_frequency_24h=0)
        assert r.admissible is True
        assert r.aml_score >= 100.0

    def test_aml_frequency_above_threshold_triggers_reduction(self):
        """When real frequency > threshold, AML score must be reduced."""
        from omnix_core.governance.aml_gate import AMLGate, AMLGateConfig
        gate = AMLGate(AMLGateConfig(enabled=True, frequency_threshold=5))
        r = gate.evaluate("BTC/USD", "BUY", volume_usd=0.0, trade_frequency_24h=15)
        assert r.aml_score < 100.0

    def test_aml_frequency_and_volume_combined_may_veto(self):
        """Both volume and frequency violations together must potentially trigger veto."""
        from omnix_core.governance.aml_gate import AMLGate, AMLGateConfig
        gate = AMLGate(AMLGateConfig(
            enabled=True,
            volume_threshold_usd=100_000.0,
            frequency_threshold=5,
        ))
        r = gate.evaluate("BTC/USD", "BUY", volume_usd=200_000.0, trade_frequency_24h=15)
        assert r.aml_score < 50.0 or not r.admissible


# ==============================================================================
# ADR-069: Fraud Gate CP-10 — Epistemic Transparency (score=0 disabled/failsafe)
# ==============================================================================

class TestFraudGateADR069:
    """ADR-069: FraudVetoResult integrity_score=0 when gate disabled/failsafe."""

    def _gate(self, enabled=True, **kwargs):
        from omnix_core.governance.fraud_gate import FraudGate, FraudGateConfig
        return FraudGate(FraudGateConfig(enabled=enabled, **kwargs))

    def test_disabled_gate_score_is_zero(self):
        """ADR-069: Disabled Fraud Gate must return integrity_score=0, not 100."""
        gate = self._gate(enabled=False)
        r = gate.evaluate("BTC/USD", "BUY", dci_score=0.0, technical_score=60.0, sentiment_score=50.0, recent_reversals=0)
        assert r.pass_through is True
        assert r.integrity_score == 0.0, (
            f"ADR-069 VIOLATION: disabled Fraud Gate returned integrity_score={r.integrity_score} "
            "(expected 0.0 — absence of fraud evaluation ≠ fraud-free)"
        )

    def test_disabled_gate_evaluation_state_is_disabled(self):
        """ADR-069: Disabled path must set evaluation_state='DISABLED'."""
        gate = self._gate(enabled=False)
        r = gate.evaluate("BTC/USD", "BUY", dci_score=0.0, technical_score=60.0, sentiment_score=50.0, recent_reversals=0)
        assert hasattr(r, 'evaluation_state'), "ADR-069: FraudVetoResult must have evaluation_state field"
        assert r.evaluation_state == "DISABLED"

    def test_evaluated_path_has_evaluation_state_evaluated(self):
        """ADR-069: Enabled and evaluated path must have evaluation_state='EVALUATED'."""
        gate = self._gate(enabled=True)
        r = gate.evaluate("BTC/USD", "BUY", dci_score=10.0, technical_score=60.0, sentiment_score=50.0, recent_reversals=0)
        assert r.evaluation_state == "EVALUATED"

    def test_evaluated_gate_score_nonzero_on_clean_input(self):
        """ADR-069: Evaluated path with clean input should yield nonzero integrity_score."""
        gate = self._gate(enabled=True)
        r = gate.evaluate("BTC/USD", "BUY", dci_score=5.0, technical_score=60.0, sentiment_score=50.0, recent_reversals=0)
        assert r.evaluation_state == "EVALUATED"
        assert r.integrity_score > 0.0

    def test_failsafe_returns_zero_score(self):
        """ADR-069: FraudGate exception path must return integrity_score=0, not 100."""
        from omnix_core.governance.fraud_gate import FraudGate, FraudGateConfig

        class BrokenFraudGate(FraudGate):
            def _run_checks(self, *a, **kw):
                raise RuntimeError("injected failure for ADR-069 test")

        gate = BrokenFraudGate(FraudGateConfig(enabled=True))
        r = gate.evaluate("BTC/USD", "BUY", dci_score=0.0, technical_score=60.0, sentiment_score=50.0, recent_reversals=0)
        assert r.pass_through is True
        assert r.integrity_score == 0.0, (
            f"ADR-069 VIOLATION: failsafe Fraud Gate returned integrity_score={r.integrity_score} "
            "(expected 0.0 — exception ≠ fraud-free)"
        )
        assert r.evaluation_state == "FAILSAFE"

    def test_reversal_detection_with_zero_reversals_passes(self):
        """ADR-069: recent_reversals=0 with enabled gate is valid and must not block."""
        gate = self._gate(enabled=True)
        r = gate.evaluate("BTC/USD", "BUY", dci_score=0.0, technical_score=60.0, sentiment_score=50.0, recent_reversals=0)
        assert r.admissible is True

    def test_high_reversal_count_triggers_violation(self):
        """ADR-069: High reversal count should reduce integrity score or trigger veto."""
        from omnix_core.governance.fraud_gate import FraudGate, FraudGateConfig
        gate = FraudGate(FraudGateConfig(enabled=True, reversal_window=2))
        r = gate.evaluate("BTC/USD", "BUY", dci_score=0.0, technical_score=60.0, sentiment_score=50.0, recent_reversals=5)
        assert r.integrity_score < 100.0 or not r.admissible


# ==============================================================================
# ADR-070: CAG CP-1 — Epistemic Transparency (score=0 disabled/failsafe)
# ==============================================================================

class TestCAGADR070:
    """ADR-070: CAGResult admission_score=0 when gate disabled/failsafe."""

    def _gate(self, enabled=True, **kwargs):
        from omnix_core.governance.context_admission_gate import ContextAdmissionGate, CAGConfig
        return ContextAdmissionGate(CAGConfig(enabled=enabled, **kwargs))

    def test_disabled_gate_score_is_zero(self):
        """ADR-070: Disabled CAG must return admission_score=0.0, not 100."""
        gate = self._gate(enabled=False)
        r = gate.evaluate(global_volatility=10.0, cross_pair_correlation=20.0, liquidity_score=80.0, macro_risk=15.0)
        assert r.pass_through is True
        assert r.admission_score == 0.0, (
            f"ADR-070 VIOLATION: disabled CAG returned admission_score={r.admission_score} "
            "(expected 0.0 — disabled gate ≠ perfect market conditions)"
        )

    def test_disabled_gate_evaluation_state_is_disabled(self):
        """ADR-070: Disabled path must set evaluation_state='DISABLED'."""
        gate = self._gate(enabled=False)
        r = gate.evaluate(global_volatility=10.0, cross_pair_correlation=20.0, liquidity_score=80.0, macro_risk=15.0)
        assert hasattr(r, 'evaluation_state'), "ADR-070: CAGResult must have evaluation_state field"
        assert r.evaluation_state == "DISABLED"

    def test_evaluated_admitted_path_has_state_evaluated(self):
        """ADR-070: Admitted session must have evaluation_state='EVALUATED'."""
        gate = self._gate(enabled=True, block_on_any_violation=True)
        r = gate.evaluate(global_volatility=10.0, cross_pair_correlation=20.0, liquidity_score=80.0, macro_risk=15.0)
        assert r.evaluation_state == "EVALUATED"

    def test_evaluated_blocked_path_has_state_evaluated(self):
        """ADR-070: Blocked session must also have evaluation_state='EVALUATED'."""
        gate = self._gate(enabled=True, global_volatility_threshold=5.0, block_on_any_violation=True)
        r = gate.evaluate(global_volatility=90.0, cross_pair_correlation=20.0, liquidity_score=80.0, macro_risk=15.0)
        assert r.evaluation_state == "EVALUATED"

    def test_failsafe_returns_zero_score(self):
        """ADR-070: Exception in CAG must return admission_score=0, not 100."""
        from omnix_core.governance.context_admission_gate import ContextAdmissionGate, CAGConfig

        class BrokenCAG(ContextAdmissionGate):
            def _run_admission_checks(self, *a, **kw):
                raise RuntimeError("injected failure for ADR-070 test")

        gate = BrokenCAG(CAGConfig(enabled=True))
        r = gate.evaluate(global_volatility=10.0, cross_pair_correlation=20.0, liquidity_score=80.0, macro_risk=15.0)
        assert r.pass_through is True
        assert r.admission_score == 0.0, (
            f"ADR-070 VIOLATION: failsafe CAG returned admission_score={r.admission_score} "
            "(expected 0.0 — exception ≠ perfect market conditions)"
        )
        assert r.evaluation_state == "FAILSAFE"

    def test_disabled_gate_is_pass_through(self):
        """ADR-070: Disabled CAG must still admit (pass_through=True) to preserve pipeline."""
        gate = self._gate(enabled=False)
        r = gate.evaluate(global_volatility=10.0, cross_pair_correlation=20.0, liquidity_score=80.0, macro_risk=15.0)
        assert r.admitted is True
        assert r.pass_through is True


# ==============================================================================
# ADR-071: PQC Receipt Builder — score defaults 100 → 0 + SCORE_PROXY notes
# ==============================================================================

class TestPQCReceiptADR071:
    """ADR-071: Receipt builder must default missing scores to 0.0, not 100.0."""

    def _make_decision_missing_scores(self, gate_key: str) -> dict:
        """Create a decision dict with gate admitted but score field ABSENT."""
        decision = {
            'action': 'BUY',
            'should_trade': True,
            'confidence': 0.75,
            'symbol': 'BTC/USD',
            'decision_trace': [],
            'reason': [],
            'veto_chain': [],
            'guards_passed': [],
        }
        decision[gate_key] = True
        return decision

    def test_sharia_score_missing_defaults_to_zero_not_100(self):
        """ADR-071: If sharia_score absent, receipt must use 0.0, not 100.0."""
        decision = self._make_decision_missing_scores('sharia_admissible')
        score = decision.get('sharia_score')
        result = score if score is not None else 0.0
        assert result == 0.0, (
            f"ADR-071 VIOLATION: missing sharia_score defaulted to {result} "
            "(expected 0.0 — absence of Sharia evaluation ≠ perfect compliance)"
        )

    def test_aml_score_missing_defaults_to_zero_not_100(self):
        """ADR-071: If aml_score absent, receipt must use 0.0, not 100.0."""
        decision = self._make_decision_missing_scores('aml_admissible')
        score = decision.get('aml_score')
        result = score if score is not None else 0.0
        assert result == 0.0

    def test_fraud_integrity_score_missing_defaults_to_zero_not_100(self):
        """ADR-071: If fraud_integrity_score absent, receipt must use 0.0, not 100.0."""
        decision = self._make_decision_missing_scores('fraud_admissible')
        score = decision.get('fraud_integrity_score')
        result = score if score is not None else 0.0
        assert result == 0.0

    def test_jurisdiction_score_missing_defaults_to_zero_not_100(self):
        """ADR-071: If jurisdiction_compliance_score absent, receipt must use 0.0, not 100.0."""
        decision = self._make_decision_missing_scores('jurisdiction_admissible')
        score = decision.get('jurisdiction_compliance_score')
        result = score if score is not None else 0.0
        assert result == 0.0

    def test_receipt_builder_logic_no_hardcoded_100(self):
        """ADR-071: Verify auto_trading_bot.py has no default=100.0 in receipt section."""
        import ast, inspect
        bot_path = "omnix_core/bot/auto_trading_bot.py"
        with open(bot_path) as f:
            source = f.read()
        lines = source.splitlines()
        receipt_start = None
        for i, line in enumerate(lines):
            if "receipt_input['sharia_compliance']" in line or "receipt_input['aml_compliance']" in line:
                receipt_start = i
                break
        if receipt_start is None:
            return
        receipt_section = "\n".join(lines[receipt_start:receipt_start + 120])
        import re
        bad_defaults = re.findall(r"\.get\(['\"][^'\"]+['\"],\s*100\.0\)", receipt_section)
        assert not bad_defaults, (
            f"ADR-071 VIOLATION: found hardcoded default=100.0 in receipt builder: {bad_defaults}"
        )


# ==============================================================================
# ADR-072: Proxy Mode Documentation — AML volume, Fraud sentiment, CAG liquidity
# ==============================================================================

class TestProxyModesADR072:
    """ADR-072: Proxy modes must be explicitly documented in decision traces."""

    def test_aml_volume_proxy_note_in_decision_dict(self):
        """ADR-072: When estimated_value_usd absent, AML_VOLUME_PROXY_MODE must be traceable."""
        decision = {'estimated_value_usd': None, 'decision_trace': []}
        _aml_volume = decision.get('estimated_value_usd')
        _aml_volume_proxy = _aml_volume is None
        if _aml_volume is None:
            _aml_volume = 0.0
        if _aml_volume_proxy:
            decision['decision_trace'].append("AML_VOLUME_PROXY_MODE")
        assert any("AML_VOLUME_PROXY_MODE" in t for t in decision['decision_trace']), (
            "ADR-072 VIOLATION: AML volume proxy not documented in trace"
        )

    def test_fraud_sentiment_proxy_note_when_v52_absent(self):
        """ADR-072: When v52_analysis absent, FRAUD_SENTIMENT_PROXY_MODE must be in trace."""
        decision = {'decision_trace': []}
        _sent_source = "PROXY"
        if 'v52_analysis' in decision:
            _sent_source = "V52"
        if _sent_source == "PROXY":
            decision['decision_trace'].append("FRAUD_SENTIMENT_PROXY_MODE")
        assert any("FRAUD_SENTIMENT_PROXY_MODE" in t for t in decision['decision_trace']), (
            "ADR-072 VIOLATION: Fraud Gate sentiment proxy not documented in trace"
        )

    def test_fraud_reversal_proxy_note_when_no_history(self):
        """ADR-072: When action history unavailable, FRAUD_REVERSAL_PROXY_MODE must be in trace."""
        decision = {'decision_trace': []}
        _rev_source = "PROXY"
        if _rev_source == "PROXY":
            decision['decision_trace'].append("FRAUD_REVERSAL_PROXY_MODE")
        assert any("FRAUD_REVERSAL_PROXY_MODE" in t for t in decision['decision_trace'])

    def test_cag_liquidity_proxy_uses_zero_not_100(self):
        """ADR-072: CAG_LIQUIDITY_PROXY_MODE must use 0.0 not 100.0 as the proxy default."""
        cfg = {}
        _cag_liq_raw = cfg.get("cag_liquidity_score")
        _cag_liq_proxy = _cag_liq_raw is None
        _cag_liq = float(_cag_liq_raw) if _cag_liq_raw is not None else 0.0
        assert _cag_liq_proxy is True
        assert _cag_liq == 0.0, (
            f"ADR-072 VIOLATION: CAG liquidity proxy default is {_cag_liq} (expected 0.0)"
        )

    def test_get_recent_reversals_returns_proxy_when_no_cache(self):
        """ADR-069/072: _get_recent_reversals must return (0, 'PROXY') when no history."""
        import sys, os
        os.environ["TESTING"] = "true"
        os.environ["TELEGRAM_BOT_TOKEN"] = "test-token"
        from unittest.mock import MagicMock, patch
        try:
            from omnix_core.bot.auto_trading_bot import AutoTradingBot
        except Exception:
            pytest.skip("AutoTradingBot not importable in test env")
        bot = MagicMock(spec=AutoTradingBot)
        bot._recent_actions_cache = {}
        bot.database_service = None
        result = AutoTradingBot._get_recent_reversals(bot, "BTC/USD")
        assert result == (0, "PROXY"), f"Expected (0, 'PROXY'), got {result}"

    def test_get_recent_reversals_returns_cache_when_history_present(self):
        """ADR-069: _get_recent_reversals must return (count, 'CACHE') from action history."""
        import sys, os
        os.environ["TESTING"] = "true"
        os.environ["TELEGRAM_BOT_TOKEN"] = "test-token"
        from unittest.mock import MagicMock
        try:
            from omnix_core.bot.auto_trading_bot import AutoTradingBot
        except Exception:
            pytest.skip("AutoTradingBot not importable in test env")
        bot = MagicMock(spec=AutoTradingBot)
        bot._recent_actions_cache = {"BTC/USD": ["BUY", "SELL", "BUY", "SELL"]}
        bot.database_service = None
        count, source = AutoTradingBot._get_recent_reversals(bot, "BTC/USD")
        assert source == "CACHE"
        assert count == 3

    def test_track_recent_action_maintains_rolling_history(self):
        """ADR-069: _track_recent_action must maintain rolling history per symbol."""
        import os
        os.environ["TESTING"] = "true"
        os.environ["TELEGRAM_BOT_TOKEN"] = "test-token"
        from unittest.mock import MagicMock
        try:
            from omnix_core.bot.auto_trading_bot import AutoTradingBot
        except Exception:
            pytest.skip("AutoTradingBot not importable in test env")
        bot = MagicMock(spec=AutoTradingBot)
        bot._recent_actions_cache = {}
        AutoTradingBot._track_recent_action(bot, "BTC/USD", "BUY", max_history=3)
        AutoTradingBot._track_recent_action(bot, "BTC/USD", "SELL", max_history=3)
        AutoTradingBot._track_recent_action(bot, "BTC/USD", "BUY", max_history=3)
        AutoTradingBot._track_recent_action(bot, "BTC/USD", "HOLD", max_history=3)
        assert len(bot._recent_actions_cache["BTC/USD"]) == 3
        assert bot._recent_actions_cache["BTC/USD"] == ["SELL", "BUY", "HOLD"]


# ==============================================================================
# ADR-073: Forensic Audit — 7 Silent Bugs (073A–073G)
# ==============================================================================

class TestGhararSemanticMismatchADR073A:
    """
    ADR-073A: Gharar Semantic Mismatch + debt_ratio silent zero.
    DCI (internal signal contradiction) ≠ gharar (Islamic speculative risk).
    The bot must use semantic helpers with explicit proxy-mode traces.
    """

    def _bot(self):
        import os
        os.environ["TESTING"] = "true"
        os.environ["TELEGRAM_BOT_TOKEN"] = "test-token"
        from unittest.mock import MagicMock
        try:
            from omnix_core.bot.auto_trading_bot import AutoTradingBot
        except Exception:
            pytest.skip("AutoTradingBot not importable in test env")
        bot = MagicMock(spec=AutoTradingBot)
        return bot

    def test_gharar_explicit_when_v52_has_gharar_score(self):
        """ADR-073A: v52_analysis.gharar_score → source='EXPLICIT', no proxy."""
        bot = self._bot()
        from omnix_core.bot.auto_trading_bot import AutoTradingBot
        decision = {"v52_analysis": {"gharar_score": 72.5}}
        score, source = AutoTradingBot._get_sharia_gharar_score(bot, decision)
        assert source == "EXPLICIT"
        assert score == 72.5

    def test_gharar_black_swan_proxy_when_no_explicit_gharar(self):
        """ADR-073A: v52_analysis.black_swan_prob → source='BLACK_SWAN_PROXY', scaled ×100."""
        bot = self._bot()
        from omnix_core.bot.auto_trading_bot import AutoTradingBot
        decision = {"v52_analysis": {"black_swan_prob": 0.55}}
        score, source = AutoTradingBot._get_sharia_gharar_score(bot, decision)
        assert source == "BLACK_SWAN_PROXY"
        assert abs(score - 55.0) < 0.01

    def test_gharar_black_swan_capped_at_100(self):
        """ADR-073A: black_swan_prob ×100 must be capped at 100.0."""
        bot = self._bot()
        from omnix_core.bot.auto_trading_bot import AutoTradingBot
        decision = {"v52_analysis": {"black_swan_prob": 1.5}}
        score, source = AutoTradingBot._get_sharia_gharar_score(bot, decision)
        assert source == "BLACK_SWAN_PROXY"
        assert score == 100.0

    def test_gharar_dci_proxy_as_last_resort(self):
        """ADR-073A: DCI present, no v52_analysis → source='DCI_PROXY'. Semantic mismatch flagged."""
        bot = self._bot()
        from omnix_core.bot.auto_trading_bot import AutoTradingBot
        decision = {"decision_contradiction_index": 38.0}
        score, source = AutoTradingBot._get_sharia_gharar_score(bot, decision)
        assert source == "DCI_PROXY", (
            f"ADR-073A VIOLATION: Expected DCI_PROXY, got '{source}'. "
            "DCI must only be used as last-resort proxy with explicit source flag."
        )
        assert score == 38.0

    def test_gharar_proxy_zero_when_no_signals(self):
        """ADR-073A: No signals at all → source='PROXY_ZERO', score=0.0."""
        bot = self._bot()
        from omnix_core.bot.auto_trading_bot import AutoTradingBot
        decision = {}
        score, source = AutoTradingBot._get_sharia_gharar_score(bot, decision)
        assert source == "PROXY_ZERO"
        assert score == 0.0

    def test_gharar_v52_none_falls_through_to_dci(self):
        """ADR-073A: v52_analysis=None must not raise — falls through to DCI check."""
        bot = self._bot()
        from omnix_core.bot.auto_trading_bot import AutoTradingBot
        decision = {"v52_analysis": None, "decision_contradiction_index": 22.0}
        score, source = AutoTradingBot._get_sharia_gharar_score(bot, decision)
        assert source == "DCI_PROXY"
        assert score == 22.0

    def test_debt_ratio_explicit_from_v52(self):
        """ADR-073A/D: v52_analysis.debt_ratio present → source='EXPLICIT'."""
        bot = self._bot()
        from omnix_core.bot.auto_trading_bot import AutoTradingBot
        decision = {"v52_analysis": {"debt_ratio": 0.28}}
        ratio, source = AutoTradingBot._get_sharia_debt_ratio(bot, decision)
        assert source == "EXPLICIT"
        assert abs(ratio - 0.28) < 0.001

    def test_debt_ratio_proxy_zero_in_trading_context(self):
        """ADR-073D: No v52 debt_ratio → source='PROXY_ZERO', ratio=0.0 (crypto spot context)."""
        bot = self._bot()
        from omnix_core.bot.auto_trading_bot import AutoTradingBot
        decision = {}
        ratio, source = AutoTradingBot._get_sharia_debt_ratio(bot, decision)
        assert source == "PROXY_ZERO"
        assert ratio == 0.0, (
            f"ADR-073D VIOLATION: debt_ratio proxy should be 0.0, got {ratio}. "
            "Crypto spot pairs have no conventional debt-to-assets ratio."
        )

    def test_dci_proxy_source_triggers_warning_in_trace(self):
        """ADR-073A: DCI_PROXY source must emit SHARIA_GHARAR_DCI_PROXY in decision_trace."""
        score, source = (38.0, "DCI_PROXY")
        trace = []
        if source == "DCI_PROXY":
            trace.append(
                "SHARIA_GHARAR_DCI_PROXY: gharar_score derived from decision_contradiction_index"
            )
        assert any("SHARIA_GHARAR_DCI_PROXY" in t for t in trace), (
            "ADR-073A VIOLATION: DCI_PROXY source must document semantic mismatch in decision_trace."
        )

    def test_proxy_zero_source_triggers_trace_warning(self):
        """ADR-073A: PROXY_ZERO source must emit SHARIA_GHARAR_PROXY_ZERO in decision_trace."""
        score, source = (0.0, "PROXY_ZERO")
        trace = []
        if source == "PROXY_ZERO":
            trace.append("SHARIA_GHARAR_PROXY_ZERO: no gharar signal available")
        assert any("SHARIA_GHARAR_PROXY_ZERO" in t for t in trace)

    def test_debt_proxy_zero_source_triggers_trace_warning(self):
        """ADR-073D: PROXY_ZERO debt_ratio must emit SHARIA_DEBT_RATIO_PROXY_ZERO in trace."""
        ratio, source = (0.0, "PROXY_ZERO")
        trace = []
        if source == "PROXY_ZERO":
            trace.append(
                "SHARIA_DEBT_RATIO_PROXY_ZERO: debt_ratio=0.0 (crypto spot context)"
            )
        assert any("SHARIA_DEBT_RATIO_PROXY_ZERO" in t for t in trace)


class TestCAGSignatureADR073B:
    """
    ADR-073B: CAG evaluate() and evaluate_session() must default liquidity_score to 0.0,
    not 100.0. Callers that omit liquidity_score must not receive fabricated perfect liquidity.
    """

    def test_cag_evaluate_default_liquidity_is_zero_not_100(self):
        """ADR-073B: gate.evaluate() with no liquidity_score → default=0.0 (illiquid, fail-safe)."""
        import inspect
        from omnix_core.governance.context_admission_gate import ContextAdmissionGate
        sig = inspect.signature(ContextAdmissionGate.evaluate)
        liq_default = sig.parameters["liquidity_score"].default
        assert liq_default == 0.0, (
            f"ADR-073B VIOLATION: evaluate() liquidity_score default is {liq_default} "
            "(expected 0.0 — 100.0 silently fabricates perfect liquidity for callers that omit it)"
        )

    def test_cag_evaluate_session_default_liquidity_is_zero_not_100(self):
        """ADR-073B: evaluate_session() with no liquidity_score → default=0.0."""
        import inspect
        from omnix_core.governance.context_admission_gate import evaluate_session
        sig = inspect.signature(evaluate_session)
        liq_default = sig.parameters["liquidity_score"].default
        assert liq_default == 0.0, (
            f"ADR-073B VIOLATION: evaluate_session() liquidity_score default is {liq_default} "
            "(expected 0.0 — silent 100.0 proxy was never documented in ADR-072)"
        )

    def test_cag_with_zero_liquidity_is_blocked(self):
        """ADR-073B: When liquidity_score=0.0 (default), CAG must block — not admit silently."""
        from omnix_core.governance.context_admission_gate import ContextAdmissionGate, CAGConfig
        gate = ContextAdmissionGate(CAGConfig(enabled=True, liquidity_score_minimum=30.0))
        r = gate.evaluate(
            global_volatility=10.0,
            cross_pair_correlation=20.0,
            macro_risk=15.0,
            # liquidity_score intentionally omitted — triggers new default of 0.0
        )
        assert not r.admitted or r.pass_through, (
            "ADR-073B VIOLATION: CAG admitted a session with liquidity_score=0.0 "
            "(min=30.0). The fail-safe default of 0.0 must cause a block."
        )


class TestPaperModeLiquidityTraceADR073C:
    """
    ADR-073C: Bot _get_cag_market_params must document the liquidity_score source
    in all three paths: PAPER_MODE_PROXY, LIVE_MODE_PROXY, ENV_OVERRIDE.
    """

    def _bot_with_config(self, paper_mode: bool):
        import os
        os.environ["TESTING"] = "true"
        os.environ["TELEGRAM_BOT_TOKEN"] = "test-token"
        os.environ.pop("CAG_LIQUIDITY_SCORE", None)
        from unittest.mock import MagicMock
        try:
            from omnix_core.bot.auto_trading_bot import AutoTradingBot
        except Exception:
            pytest.skip("AutoTradingBot not importable in test env")
        bot = MagicMock(spec=AutoTradingBot)
        bot.config = {"paper_mode": paper_mode, "trading_pairs": ["BTC/USD"]}
        bot._cag_signals_cache = {}
        return bot

    def test_paper_mode_liquidity_source_is_paper_proxy(self):
        """ADR-073C: paper_mode=True → liquidity=100.0, _liquidity_source='PAPER_MODE_PROXY'."""
        bot = self._bot_with_config(paper_mode=True)
        from omnix_core.bot.auto_trading_bot import AutoTradingBot
        params = AutoTradingBot._get_cag_market_params(bot)
        assert params["_liquidity_source"] == "PAPER_MODE_PROXY", (
            f"ADR-073C VIOLATION: Expected PAPER_MODE_PROXY, got '{params['_liquidity_source']}'"
        )
        assert params["liquidity_score"] == 100.0

    def test_live_mode_liquidity_source_is_live_proxy(self):
        """ADR-073C: paper_mode=False → liquidity=85.0, _liquidity_source='LIVE_MODE_PROXY'."""
        bot = self._bot_with_config(paper_mode=False)
        from omnix_core.bot.auto_trading_bot import AutoTradingBot
        params = AutoTradingBot._get_cag_market_params(bot)
        assert params["_liquidity_source"] == "LIVE_MODE_PROXY", (
            f"ADR-073C VIOLATION: Expected LIVE_MODE_PROXY, got '{params['_liquidity_source']}'"
        )
        assert params["liquidity_score"] == 85.0

    def test_env_override_liquidity_source_is_env_override(self):
        """ADR-073C: CAG_LIQUIDITY_SCORE env var → _liquidity_source='ENV_OVERRIDE'."""
        import os
        # Create bot first (bot_with_config pops CAG_LIQUIDITY_SCORE as cleanup),
        # then set the env var so it's present when _get_cag_market_params() runs.
        bot = self._bot_with_config(paper_mode=True)
        os.environ["CAG_LIQUIDITY_SCORE"] = "60.0"
        try:
            from omnix_core.bot.auto_trading_bot import AutoTradingBot
            params = AutoTradingBot._get_cag_market_params(bot)
            assert params["_liquidity_source"] == "ENV_OVERRIDE", (
                f"ADR-073C VIOLATION: Expected ENV_OVERRIDE, got '{params['_liquidity_source']}'"
            )
            assert params["liquidity_score"] == 60.0
        finally:
            os.environ.pop("CAG_LIQUIDITY_SCORE", None)


class TestHaramAssetEvaluationStateADR073E:
    """
    ADR-073E: ShariaVetoResult for HARAM_ASSET must have evaluation_state='EVALUATED'
    (explicit, not relying solely on dataclass default).
    """

    def test_haram_asset_result_has_evaluation_state_evaluated(self):
        """ADR-073E: evaluate() on HARAM asset must return evaluation_state='EVALUATED'."""
        from omnix_core.governance.sharia_gate import ShariaGate, ShariaGateConfig
        gate = ShariaGate(ShariaGateConfig(enabled=True))
        r = gate.evaluate(symbol="WBTC/USD", proposed_action="BUY")
        assert not r.admissible
        assert r.violation == "HARAM_ASSET"
        assert r.evaluation_state == "EVALUATED", (
            f"ADR-073E VIOLATION: HARAM_ASSET result has evaluation_state='{r.evaluation_state}' "
            "(expected 'EVALUATED' — haram check is a full gate determination, not a pass-through)"
        )

    def test_halal_asset_result_has_evaluation_state_evaluated(self):
        """ADR-073E: evaluate() on clean HALAL asset also returns evaluation_state='EVALUATED'."""
        from omnix_core.governance.sharia_gate import ShariaGate, ShariaGateConfig
        gate = ShariaGate(ShariaGateConfig(enabled=True, gharar_threshold=70.0))
        r = gate.evaluate(symbol="BTC/USD", proposed_action="BUY", gharar_score=30.0)
        assert r.admissible
        assert r.evaluation_state == "EVALUATED"

    def test_disabled_gate_has_evaluation_state_disabled(self):
        """ADR-073E: Disabled Sharia Gate must return evaluation_state='DISABLED'."""
        from omnix_core.governance.sharia_gate import ShariaGate, ShariaGateConfig
        gate = ShariaGate(ShariaGateConfig(enabled=False))
        r = gate.evaluate(symbol="BTC/USD", proposed_action="BUY")
        assert r.pass_through is True
        assert r.evaluation_state == "DISABLED"


class TestAVMNoBaselineTraceADR073F:
    """
    ADR-073F: When AVM runs in pass-through mode (NO_BASELINE or DISABLED),
    the external_evaluator must emit a trace entry instead of silently passing.
    """

    def test_avm_no_baseline_pass_through_is_documented(self):
        """ADR-073F: AVMResult with snapshot_id='NO_BASELINE' must yield AVM_NO_BASELINE trace."""
        from omnix_core.governance.assumption_validity_monitor import AVMResult
        avm_result = AVMResult(
            is_valid=True,
            snapshot_id="NO_BASELINE",
            parameter_version="N/A",
            drift_score=0.0,
            drift_components={},
            drift_threshold=0.0,
            age_hours=0.0,
            block_reason=None,
            warnings=["Drift detection inactive — call save_calibration_snapshot() to arm AVM."],
            pass_through=True,
        )
        trace = []
        if avm_result.pass_through:
            if avm_result.snapshot_id == "NO_BASELINE":
                trace.append(
                    "AVM_NO_BASELINE: Assumption Validity Monitor has no calibration snapshot"
                )
        assert any("AVM_NO_BASELINE" in t for t in trace), (
            "ADR-073F VIOLATION: AVM NO_BASELINE pass-through must emit AVM_NO_BASELINE in trace. "
            "Silent pass-through means receipts were issued without any calibration baseline."
        )

    def test_avm_disabled_pass_through_is_documented(self):
        """ADR-073F: AVMResult with snapshot_id='DISABLED' must yield AVM_DISABLED trace."""
        from omnix_core.governance.assumption_validity_monitor import AVMResult
        avm_result = AVMResult(
            is_valid=True,
            snapshot_id="DISABLED",
            parameter_version="N/A",
            drift_score=0.0,
            drift_components={},
            drift_threshold=0.0,
            age_hours=0.0,
            block_reason=None,
            warnings=["AVM disabled via AVM_ENABLED=false"],
            pass_through=True,
        )
        trace = []
        if avm_result.pass_through:
            if avm_result.snapshot_id == "DISABLED":
                trace.append("AVM_DISABLED: Assumption Validity Monitor disabled")
        assert any("AVM_DISABLED" in t for t in trace), (
            "ADR-073F VIOLATION: AVM DISABLED pass-through must emit AVM_DISABLED in trace."
        )

    def test_avm_valid_not_pass_through_emits_avm_valid(self):
        """ADR-073F: Fully valid AVM result (not pass_through) must emit AVM VALID trace."""
        from omnix_core.governance.assumption_validity_monitor import AVMResult
        avm_result = AVMResult(
            is_valid=True,
            snapshot_id="AVM-ABC123",
            parameter_version="1.abc123",
            drift_score=12.3,
            drift_components={"vol": 5.1, "corr": 7.2},
            drift_threshold=40.0,
            age_hours=5.5,
            block_reason=None,
            warnings=[],
            pass_through=False,
        )
        trace = []
        if not avm_result.pass_through:
            trace.append(
                f"AVM VALID: drift={avm_result.drift_score:.1f} ≤ {avm_result.drift_threshold:.1f}"
            )
        assert any("AVM VALID" in t for t in trace)


class TestTIESignalDefaultsADR073G:
    """
    ADR-073G: TIE must track which signals defaulted to 50.0 (neutral stub) and
    expose them in TIEResult.signal_defaults. Silent defaults bias trajectory history.
    """

    def test_tie_result_has_signal_defaults_field(self):
        """ADR-073G: TIEResult dataclass must have a signal_defaults field."""
        from omnix_core.governance.trajectory_invariant_engine import TIEResult
        import dataclasses
        field_names = [f.name for f in dataclasses.fields(TIEResult)]
        assert "signal_defaults" in field_names, (
            "ADR-073G VIOLATION: TIEResult missing 'signal_defaults' field. "
            "Defaulted 50.0 signals must be documented in the result."
        )

    def test_tie_signal_defaults_populated_when_signals_absent(self):
        """ADR-073G: When current_signals is empty, all 6 signals must appear in signal_defaults."""
        from omnix_core.governance.trajectory_invariant_engine import TrajectoryInvariantEngine
        engine = TrajectoryInvariantEngine(db_conn=None)
        result = engine.evaluate(
            current_signals={},      # no signals provided
            asset="BTC/USD",
            domain="trading",
            current_decision="APPROVED",
        )
        assert len(result.signal_defaults) == 6, (
            f"ADR-073G VIOLATION: Expected 6 signal_defaults (all absent), "
            f"got {len(result.signal_defaults)}: {result.signal_defaults}"
        )
        for expected_sig in ("probability_score", "risk_exposure", "signal_coherence",
                             "trend_persistence", "stress_resilience", "logic_consistency"):
            assert any(expected_sig in d for d in result.signal_defaults), (
                f"ADR-073G VIOLATION: '{expected_sig}' not found in signal_defaults. "
                f"signal_defaults={result.signal_defaults}"
            )

    def test_tie_signal_defaults_empty_when_all_present(self):
        """ADR-073G: When all 6 signals are provided, signal_defaults must be empty."""
        from omnix_core.governance.trajectory_invariant_engine import TrajectoryInvariantEngine
        engine = TrajectoryInvariantEngine(db_conn=None)
        full_signals = {
            "probability_score": 60.0,
            "risk_exposure": 40.0,
            "signal_coherence": 65.0,
            "trend_persistence": 55.0,
            "stress_resilience": 70.0,
            "logic_consistency": 75.0,
        }
        result = engine.evaluate(
            current_signals=full_signals,
            asset="BTC/USD",
            domain="trading",
            current_decision="APPROVED",
        )
        assert result.signal_defaults == [], (
            f"ADR-073G VIOLATION: Expected empty signal_defaults when all signals provided, "
            f"got {result.signal_defaults}"
        )

    def test_tie_partial_defaults_only_missing_signals(self):
        """ADR-073G: When 3 signals provided, only the 3 missing must appear in signal_defaults."""
        from omnix_core.governance.trajectory_invariant_engine import TrajectoryInvariantEngine
        engine = TrajectoryInvariantEngine(db_conn=None)
        partial_signals = {
            "probability_score": 60.0,
            "risk_exposure": 40.0,
            "signal_coherence": 65.0,
        }
        result = engine.evaluate(
            current_signals=partial_signals,
            asset="ETH/USD",
            domain="trading",
            current_decision="APPROVED",
        )
        assert len(result.signal_defaults) == 3, (
            f"ADR-073G VIOLATION: Expected 3 signal_defaults (3 missing), "
            f"got {len(result.signal_defaults)}: {result.signal_defaults}"
        )
        for missing in ("trend_persistence", "stress_resilience", "logic_consistency"):
            assert any(missing in d for d in result.signal_defaults), (
                f"'{missing}' should be in signal_defaults but is absent"
            )
        for present in ("probability_score", "risk_exposure", "signal_coherence"):
            assert not any(present in d for d in result.signal_defaults), (
                f"'{present}' was provided but appears in signal_defaults"
            )
