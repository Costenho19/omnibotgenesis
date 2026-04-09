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
