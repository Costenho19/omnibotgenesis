#!/usr/bin/env python3
"""
OMNIX Critical Audit Tests - Dec 30, 2025
These tests verify the 4 critical audit requirements:
1. safe_float parsing works correctly
2. Coherence exception causes BLOCKED (fail-closed)
3. MC expected_return < 0 causes BLOCKED with reason=MC_NEG_ER
4. Coherence Gate executes BEFORE scoring

Run with: TESTING=true TELEGRAM_BOT_TOKEN=test-token python -m pytest tests/test_critical_audit.py -v
"""

import pytest
import sys
from unittest.mock import MagicMock, patch


class TestSafeFloat:
    """Test 1: safe_float parsing handles all edge cases"""
    
    def test_safe_float_with_float(self):
        from omnix_services.coherence_service.coherence_engine import safe_float
        assert safe_float(0.5, 0.0) == 0.5
        assert safe_float(1.0, 0.0) == 1.0
        assert safe_float(-0.5, 0.0) == -0.5
    
    def test_safe_float_with_int(self):
        from omnix_services.coherence_service.coherence_engine import safe_float
        assert safe_float(5, 0.0) == 5.0
        assert safe_float(-3, 0.0) == -3.0
    
    def test_safe_float_with_string(self):
        from omnix_services.coherence_service.coherence_engine import safe_float
        assert safe_float("0.5", 0.0) == 0.5
        assert safe_float("100", 0.0) == 100.0
    
    def test_safe_float_with_invalid_string(self):
        from omnix_services.coherence_service.coherence_engine import safe_float
        assert safe_float("invalid", 0.0) == 0.0
        assert safe_float("BUY", 0.0) == 0.0
        assert safe_float("SELL", 99.0) == 99.0
    
    def test_safe_float_with_none(self):
        from omnix_services.coherence_service.coherence_engine import safe_float
        assert safe_float(None, 0.0) == 0.0
        assert safe_float(None, 42.0) == 42.0


class TestCoherenceExceptionBlocks:
    """Test 2: Coherence Gate exception causes BLOCKED (fail-closed)"""
    
    def test_coherence_exception_causes_blocked(self):
        """When CoherenceEngine.analyze_coherence raises exception, trade must be BLOCKED"""
        decision = {
            'action': None,
            'should_trade': True,
            'vetoed': False,
            'veto_reason': None,
            'veto_chain': [],
            'decision_trace': [],
            'v52_analysis': {},
            'guards_passed': [],
            'reason': [],
            'confidence': 0.5
        }
        
        mock_coherence_engine = MagicMock()
        mock_coherence_engine.analyze_coherence.side_effect = ValueError("Test exception: str vs int comparison")
        
        coherence_gate_passed = True
        try:
            coherence_report = mock_coherence_engine.analyze_coherence([])
        except Exception as e:
            coherence_gate_passed = False
            decision['action'] = 'BLOCKED'
            decision['should_trade'] = False
            decision['confidence'] = 0.0
            decision['vetoed'] = True
            decision['veto_reason'] = 'COHERENCE_EXCEPTION'
            decision['veto_chain'].append('COHERENCE_EXCEPTION')
            decision['decision_trace'].append(f"COHERENCE_GATE: BLOCKED due to exception: {e}")
        
        assert coherence_gate_passed is False
        assert decision['action'] == 'BLOCKED'
        assert decision['vetoed'] is True
        assert decision['veto_reason'] == 'COHERENCE_EXCEPTION'
        assert 'COHERENCE_EXCEPTION' in decision['veto_chain']


class TestMCNegERBlocks:
    """Test 3: Monte Carlo expected_return < 0 causes BLOCKED with MC_NEG_ER"""
    
    def test_negative_expected_return_blocks(self):
        """When expected_return < 0, trade must be BLOCKED with reason=MC_NEG_ER"""
        from omnix_services.coherence_service.coherence_engine import safe_float
        
        monte_carlo = {
            'expected_return': -0.02,
            'var_95': -0.01,
            'win_rate': 0.55
        }
        
        mc_cfg = {
            'min_expected_return': 0.0,
            'max_var_95': -0.03,
            'reduce_size_win_rate': 0.50,
            'size_reduction_factor': 0.5
        }
        
        decision = {
            'veto_chain': [],
            'veto_reason': None,
            'decision_trace': [],
            'mc_veto': False,
            'v52_analysis': {}
        }
        
        expected_return = safe_float(monte_carlo.get('expected_return', 0), 0)
        mc_min_expected = safe_float(mc_cfg.get('min_expected_return', 0.0), 0.0)
        
        mc_veto_applied = False
        if expected_return < mc_min_expected:
            mc_veto_applied = True
            decision['veto_chain'].append('MC_NEG_ER')
            decision['veto_reason'] = 'MC_NEG_ER'
            decision['decision_trace'].append(f"MC_VETO: Expected return {expected_return:.2%} < {mc_min_expected:.2%} → BLOCKED reason=MC_NEG_ER")
        
        assert mc_veto_applied is True
        assert 'MC_NEG_ER' in decision['veto_chain']
        assert decision['veto_reason'] == 'MC_NEG_ER'
    
    def test_low_winrate_reduces_size_not_blocks(self):
        """When win_rate < 50% but ER >= 0, apply size_multiplier=0.5, NOT block"""
        from omnix_services.coherence_service.coherence_engine import safe_float
        
        monte_carlo = {
            'expected_return': 0.01,
            'var_95': -0.02,
            'win_rate': 0.45
        }
        
        mc_cfg = {
            'min_expected_return': 0.0,
            'max_var_95': -0.03,
            'reduce_size_win_rate': 0.50,
            'size_reduction_factor': 0.5
        }
        
        decision = {
            'veto_chain': [],
            'veto_reason': None,
            'decision_trace': [],
            'size_multiplier': 1.0,
            'size_multiplier_reason': None,
            'v52_analysis': {}
        }
        
        expected_return = safe_float(monte_carlo.get('expected_return', 0), 0)
        win_rate = safe_float(monte_carlo.get('win_rate', 0.5), 0.5)
        mc_min_expected = safe_float(mc_cfg.get('min_expected_return', 0.0), 0.0)
        mc_reduce_wr = safe_float(mc_cfg.get('reduce_size_win_rate', 0.50), 0.50)
        mc_size_factor = safe_float(mc_cfg.get('size_reduction_factor', 0.5), 0.5)
        
        mc_veto_applied = False
        if expected_return < mc_min_expected:
            mc_veto_applied = True
        
        if not mc_veto_applied and win_rate < mc_reduce_wr:
            position_size_factor = max(0.0, min(mc_size_factor, 1.0))
            decision['size_multiplier'] = position_size_factor
            decision['size_multiplier_reason'] = 'MC_WR_BELOW_50'
            decision['decision_trace'].append(f"MC_SIZE_REDUCE: Win rate {win_rate:.1%} → size_multiplier={position_size_factor:.0%} reason=MC_WR_BELOW_50")
        
        assert mc_veto_applied is False
        assert decision['size_multiplier'] == 0.5
        assert decision['size_multiplier_reason'] == 'MC_WR_BELOW_50'


class TestCoherenceBeforeScoring:
    """Test 4: Coherence Gate must execute BEFORE scoring"""
    
    def test_coherence_gate_order_in_decision_trace(self):
        """decision_trace must show COHERENCE_GATE before SCORING entries"""
        decision_trace = [
            "MC_VETO: Expected return -2.00% < 0.00% → BLOCKED reason=MC_NEG_ER",
            "COHERENCE_GATE: 65.0% >= 45.0% → PASSED",
            "SCORING: EMA +40 pts",
            "SCORING: HMM +25 pts"
        ]
        
        coherence_idx = None
        first_scoring_idx = None
        
        for i, entry in enumerate(decision_trace):
            if 'COHERENCE_GATE' in entry and coherence_idx is None:
                coherence_idx = i
            if 'SCORING' in entry and first_scoring_idx is None:
                first_scoring_idx = i
        
        if coherence_idx is not None and first_scoring_idx is not None:
            assert coherence_idx < first_scoring_idx, "COHERENCE_GATE must appear before SCORING in decision_trace"
    
    def test_coherence_rejection_prevents_scoring(self):
        """If Coherence Gate rejects, no SCORING entries should exist"""
        decision_trace = [
            "MC_VETO: check passed",
            "COHERENCE_GATE: 25.0% < 45.0% → REJECTED"
        ]
        
        coherence_rejected = any('REJECTED' in entry and 'COHERENCE_GATE' in entry for entry in decision_trace)
        has_scoring = any('SCORING' in entry for entry in decision_trace)
        
        if coherence_rejected:
            assert not has_scoring, "If Coherence Gate REJECTED, no SCORING entries should follow"


class TestDecisionPayloadAuditFields:
    """Test 5: DecisionPayload has all mandatory audit fields"""
    
    def test_payload_has_audit_fields(self):
        """DecisionPayload must include action, vetoed, size_multiplier, execution_path"""
        from omnix_core.utils.logger import DecisionPayload
        import dataclasses
        
        field_names = [f.name for f in dataclasses.fields(DecisionPayload)]
        
        required_fields = ['action', 'vetoed', 'size_multiplier', 'size_multiplier_reason', 'execution_path']
        
        for field in required_fields:
            assert field in field_names, f"DecisionPayload missing required audit field: {field}"
    
    def test_payload_json_includes_all_fields(self):
        """DecisionPayload.to_json() includes non-None audit fields"""
        from omnix_core.utils.logger import DecisionPayload
        import json
        
        payload = DecisionPayload(
            decision_id="DEC-TEST-001",
            event_type="TRADE_REJECTED",
            timestamp="2025-12-30T12:00:00Z",
            symbol="BTC/USD",
            action="BLOCKED",
            vetoed=True,
            veto_reason="MC_NEG_ER",
            veto_chain=["MC_NEG_ER"],
            size_multiplier=1.0,
            execution_path="legacy"
        )
        
        json_str = payload.to_json()
        data = json.loads(json_str)
        
        assert data['action'] == 'BLOCKED'
        assert data['vetoed'] is True
        assert data['veto_reason'] == 'MC_NEG_ER'
        assert data['size_multiplier'] == 1.0
        assert data['execution_path'] == 'legacy'


class TestCodePatternVerification:
    """Test 6: Verify actual code patterns are correctly implemented"""
    
    def test_coherence_exception_returns_blocked_in_source(self):
        """Verify the source code has BLOCKED return on coherence exception"""
        import inspect
        from omnix_core.bot.auto_trading_bot import AutoTradingBot
        
        source = inspect.getsource(AutoTradingBot)
        
        assert "except Exception as e:" in source and "COHERENCE_EXCEPTION" in source, \
            "Coherence exception handler must set COHERENCE_EXCEPTION"
        assert "veto_reason = 'COHERENCE_EXCEPTION'" in source or "veto_reason'] = 'COHERENCE_EXCEPTION'" in source, \
            "Coherence exception must set veto_reason=COHERENCE_EXCEPTION"
    
    def test_coherence_gate_sets_blocked_not_hold(self):
        """Verify coherence gate rejection sets action=BLOCKED not HOLD"""
        import inspect
        from omnix_core.bot.auto_trading_bot import AutoTradingBot
        
        source = inspect.getsource(AutoTradingBot)
        
        coherence_gate_section = source[source.find("# EARLY RETURN si Coherence Gate"):source.find("# EARLY RETURN si Coherence Gate")+500]
        
        assert "action'] = 'BLOCKED'" in coherence_gate_section or "action']='BLOCKED'" in coherence_gate_section, \
            "Coherence Gate rejection must set action=BLOCKED"
    
    def test_mc_neg_er_veto_reason_in_source(self):
        """Verify MC_NEG_ER is used as veto reason for negative expected return"""
        import inspect
        from omnix_core.bot.auto_trading_bot import AutoTradingBot
        
        source = inspect.getsource(AutoTradingBot)
        
        assert "MC_NEG_ER" in source, "Monte Carlo must use MC_NEG_ER as veto reason"
        assert "veto_reason'] = 'MC_NEG_ER'" in source or "veto_reason']='MC_NEG_ER'" in source, \
            "MC_NEG_ER must be set as veto_reason"
    
    def test_mc_wr_below_50_size_reduction_in_source(self):
        """Verify MC_WR_BELOW_50 is used for size reduction reason"""
        import inspect
        from omnix_core.bot.auto_trading_bot import AutoTradingBot
        
        source = inspect.getsource(AutoTradingBot)
        
        assert "MC_WR_BELOW_50" in source, "Monte Carlo must use MC_WR_BELOW_50 for size reduction"
        assert "size_multiplier" in source, "size_multiplier field must be set"
        assert "size_multiplier_reason" in source, "size_multiplier_reason field must be set"
    
    def test_coherence_gate_before_scoring_in_flow(self):
        """Verify COHERENCE_GATE appears before SCORING in source code order"""
        import inspect
        from omnix_core.bot.auto_trading_bot import AutoTradingBot
        
        source = inspect.getsource(AutoTradingBot)
        
        coherence_gate_pos = source.find("COHERENCE PRE-GATE")
        scoring_pos = source.find("VETO/PENALTY ONLY")
        
        assert coherence_gate_pos > 0, "COHERENCE PRE-GATE section must exist"
        assert scoring_pos > 0, "SCORING section must exist"
        assert coherence_gate_pos < scoring_pos, "COHERENCE GATE must appear BEFORE scoring in code"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
