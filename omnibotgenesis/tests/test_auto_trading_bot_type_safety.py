"""
Type Safety Tests for AutoTradingBot - Dec 30, 2025

Tests the safe_float() normalization in _build_strategy_signals() and other methods
to ensure string values from APIs don't cause TypeError comparisons.

REGRESSION TESTS for the error:
    TypeError: '>=' not supported between instances of 'str' and 'int'
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from omnix_core.bot.auto_trading_bot import safe_float


class TestSafeFloatFunction:
    """Tests for the safe_float() utility function"""
    
    def test_safe_float_with_int(self):
        """Normal case: int value"""
        assert safe_float(7) == 7.0
        assert safe_float(-3) == -3.0
        assert safe_float(0) == 0.0
    
    def test_safe_float_with_float(self):
        """Normal case: float value"""
        assert safe_float(0.5) == 0.5
        assert safe_float(0.75) == 0.75
        assert safe_float(-0.1) == -0.1
    
    def test_safe_float_with_string_int(self):
        """CRITICAL: String that represents an integer"""
        assert safe_float("7") == 7.0
        assert safe_float("-3") == -3.0
        assert safe_float("0") == 0.0
    
    def test_safe_float_with_string_float(self):
        """CRITICAL: String that represents a float"""
        assert safe_float("0.5") == 0.5
        assert safe_float("0.75") == 0.75
        assert safe_float("-0.1") == -0.1
    
    def test_safe_float_with_percentage_string(self):
        """CRITICAL: String with % symbol (common from APIs)"""
        assert safe_float("50%") == 50.0
        assert safe_float("75.5%") == 75.5
        assert safe_float("0%") == 0.0
    
    def test_safe_float_with_whitespace(self):
        """Strings with leading/trailing whitespace"""
        assert safe_float("  7  ") == 7.0
        assert safe_float(" 0.5 ") == 0.5
        assert safe_float("  50%  ") == 50.0
    
    def test_safe_float_with_none(self):
        """None should return default"""
        assert safe_float(None) == 0.0
        assert safe_float(None, default=5.0) == 5.0
    
    def test_safe_float_with_invalid_string(self):
        """Invalid strings should return default"""
        assert safe_float("invalid") == 0.0
        assert safe_float("BUY") == 0.0
        assert safe_float("N/A") == 0.0
        assert safe_float("", default=0.5) == 0.5
    
    def test_safe_float_preserves_negative(self):
        """Negative values should be preserved"""
        assert safe_float("-7") == -7.0
        assert safe_float("-0.5") == -0.5
        assert safe_float(-10) == -10.0


class TestStrategySignalPayloads:
    """
    Tests that strategy dictionaries with string values don't cause TypeError.
    These simulate the payloads that come from external APIs.
    """
    
    def test_quantum_momentum_string_signal(self):
        """Quantum signal as string should not raise TypeError"""
        quantum = {'signal': '7', 'confidence': '0.8'}
        signal_val = safe_float(quantum.get('signal', 0))
        confidence = safe_float(quantum.get('confidence', 0.5))
        
        assert signal_val >= 7
        assert isinstance(signal_val, float)
        assert isinstance(confidence, float)
    
    def test_monte_carlo_string_win_rate(self):
        """Monte Carlo win_rate as string/percentage should work"""
        mc = {'win_rate': '0.65'}
        win_rate = safe_float(mc.get('win_rate', 0.5))
        win_rate_pct = win_rate * 100 if win_rate <= 1 else win_rate
        
        assert win_rate_pct >= 55
        assert isinstance(win_rate_pct, float)
    
    def test_monte_carlo_percentage_string(self):
        """Monte Carlo with percentage string (65%)"""
        mc = {'win_rate': '65%'}
        win_rate = safe_float(mc.get('win_rate', 0.5))
        assert win_rate == 65.0
    
    def test_kalman_string_values(self):
        """Kalman strength/confidence as strings"""
        kalman = {'trend': 'BULLISH', 'strength': '0.7', 'confidence': '0.8'}
        strength = safe_float(kalman.get('strength', 0.5))
        confidence = safe_float(kalman.get('confidence', 0.7))
        
        assert isinstance(strength, float)
        assert isinstance(confidence, float)
        assert strength >= 0.5
    
    def test_kelly_string_optimal_fraction(self):
        """Kelly optimal_fraction as string"""
        kelly = {'optimal_fraction': '0.12'}
        optimal_size = safe_float(kelly.get('optimal_fraction', 0))
        
        assert optimal_size > 0.10
        assert isinstance(optimal_size, float)
    
    def test_sentiment_string_score(self):
        """Sentiment score as string"""
        sentiment = {'overall_score': '75'}
        score = safe_float(sentiment.get('overall_score', 50))
        
        assert score >= 75
        assert isinstance(score, float)
    
    def test_black_swan_string_probability(self):
        """Black swan crash_probability as string"""
        bs = {'risk_level': 'HIGH', 'crash_probability': '0.35'}
        crash_prob = safe_float(bs.get('crash_probability', 0))
        
        assert isinstance(crash_prob, float)
        assert crash_prob > 0.3
    
    def test_non_markovian_string_scores(self):
        """Non-Markovian with string confidence and metrics"""
        nm = {
            'signal': 'BUY',
            'confidence': '70',
            'metrics': {
                'bullish_score': '65',
                'bearish_score': '35'
            }
        }
        confidence = safe_float(nm.get('confidence', 0)) / 100.0
        bullish = safe_float(nm.get('metrics', {}).get('bullish_score', 0))
        bearish = safe_float(nm.get('metrics', {}).get('bearish_score', 0))
        
        assert isinstance(confidence, float)
        assert isinstance(bullish, float)
        assert isinstance(bearish, float)
        assert confidence == 0.7
    
    def test_mixed_types_in_payload(self):
        """Payload with mixed int, float, and string types"""
        payload = {
            'int_val': 7,
            'float_val': 0.5,
            'str_int': '10',
            'str_float': '0.75',
            'str_pct': '50%',
            'none_val': None,
            'invalid': 'N/A'
        }
        
        assert safe_float(payload['int_val']) == 7.0
        assert safe_float(payload['float_val']) == 0.5
        assert safe_float(payload['str_int']) == 10.0
        assert safe_float(payload['str_float']) == 0.75
        assert safe_float(payload['str_pct']) == 50.0
        assert safe_float(payload['none_val']) == 0.0
        assert safe_float(payload['invalid']) == 0.0


class TestComparisonOperations:
    """
    Tests that numeric comparisons work after safe_float conversion.
    These are the exact patterns that were causing TypeError in production.
    """
    
    def test_comparison_gte_with_string(self):
        """'>=' comparison with string value - the original error"""
        signal_val = safe_float("7")
        assert signal_val >= 7
        assert not (signal_val >= 8)
    
    def test_comparison_lte_with_string(self):
        """'<=' comparison with string value"""
        signal_val = safe_float("-7")
        assert signal_val <= -7
        assert not (signal_val <= -8)
    
    def test_comparison_gt_with_string(self):
        """'>' comparison with string value"""
        optimal = safe_float("0.12")
        assert optimal > 0.10
        assert not (optimal > 0.15)
    
    def test_comparison_lt_with_string(self):
        """'<' comparison with string value"""
        optimal = safe_float("0.005")
        assert optimal < 0.01
    
    def test_arithmetic_with_string(self):
        """Arithmetic operations after safe_float"""
        score = safe_float("75")
        normalized = score / 100.0
        assert normalized == 0.75
        
        multiplied = safe_float("0.5") * 100
        assert multiplied == 50.0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
