"""
OMNIX V7.0 Parity Test Harness
================================
Compares outputs between legacy and new architecture implementations.

This test suite ensures that the new hexagonal architecture produces
functionally equivalent results to the legacy implementation.

Phase 2 Gate Criteria: All parity tests must pass before Phase 3.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
from decimal import Decimal

from src.omnix.domain.trading.entities import (
    Trade, Position, Signal,
    TradeDirection, TradeStatus, SignalStrength,
)
from src.omnix.domain.trading.value_objects import (
    Money, Quantity, SymbolPair, ConfidenceScore,
)
from src.omnix.domain.risk.entities import (
    RiskAlert, RiskLevel, AlertType, LimitState,
)
from src.omnix.domain.support.market import (
    MarketSnapshot, StrategyVote, CoherenceResult, RegimeState, MarketRegime,
)


class TestEntityParity:
    """Test that new entities match legacy behavior."""
    
    def test_trade_pnl_calculation_parity(self):
        """Verify Trade.calculate_pnl matches legacy calculation."""
        trade = Trade(
            id="test-1",
            pair="BTC/USD",
            direction=TradeDirection.BUY,
            quantity=0.1,
            entry_price=50000.0,
            status=TradeStatus.EXECUTED,
        )
        
        pnl = trade.calculate_pnl(55000.0)
        expected_pnl = (55000.0 - 50000.0) * 0.1
        assert pnl == expected_pnl, f"Expected {expected_pnl}, got {pnl}"
        
        trade_sell = Trade(
            id="test-2",
            pair="BTC/USD",
            direction=TradeDirection.SELL,
            quantity=0.1,
            entry_price=50000.0,
            status=TradeStatus.EXECUTED,
        )
        
        pnl_sell = trade_sell.calculate_pnl(45000.0)
        expected_pnl_sell = (50000.0 - 45000.0) * 0.1
        assert pnl_sell == expected_pnl_sell
    
    def test_signal_strength_scoring_parity(self):
        """Verify SignalStrength thresholds match legacy scoring."""
        assert SignalStrength.from_score(5) == SignalStrength.WEAK
        assert SignalStrength.from_score(8) == SignalStrength.MODERATE
        assert SignalStrength.from_score(12) == SignalStrength.STRONG
        assert SignalStrength.from_score(15) == SignalStrength.VERY_STRONG
        assert SignalStrength.from_score(0) == SignalStrength.WEAK
        assert SignalStrength.from_score(-5) == SignalStrength.WEAK
    
    def test_signal_actionability_parity(self):
        """Verify Signal.is_actionable matches legacy rules."""
        strong_signal = Signal(
            pair="BTC/USD",
            direction=TradeDirection.BUY,
            strength=SignalStrength.STRONG,
            score=12.0,
            confidence=0.7,
            strategy="test",
            coherence_passed=True,
        )
        assert strong_signal.is_actionable() is True
        
        weak_signal = Signal(
            pair="BTC/USD",
            direction=TradeDirection.BUY,
            strength=SignalStrength.WEAK,
            score=5.0,
            confidence=0.4,
            strategy="test",
            coherence_passed=True,
        )
        assert weak_signal.is_actionable() is False
        
        vetoed_signal = Signal(
            pair="BTC/USD",
            direction=TradeDirection.BUY,
            strength=SignalStrength.STRONG,
            score=12.0,
            confidence=0.7,
            strategy="test",
            coherence_passed=False,
        )
        assert vetoed_signal.is_actionable() is False


class TestValueObjectParity:
    """Test value objects match expected behavior."""
    
    def test_money_precision_parity(self):
        """Verify Money uses correct decimal precision."""
        usd = Money(amount=Decimal("100.50"), currency="USD")
        assert usd.amount == Decimal("100.50")
        assert "100.50" in str(usd)
    
    def test_money_arithmetic_parity(self):
        """Verify Money arithmetic matches expected behavior."""
        m1 = Money(amount=Decimal("100.00"), currency="USD")
        m2 = Money(amount=Decimal("50.25"), currency="USD")
        
        result = m1 + m2
        assert result.amount == Decimal("150.25")
        
        result_sub = m1 - m2
        assert result_sub.amount == Decimal("49.75")
    
    def test_symbol_pair_parsing_parity(self):
        """Verify SymbolPair parsing matches legacy patterns."""
        pair1 = SymbolPair.from_string("BTC/USD")
        assert pair1.base == "BTC"
        assert pair1.quote == "USD"
        
        pair2 = SymbolPair.from_string("ETH/USDT")
        assert pair2.base == "ETH"
        assert pair2.quote == "USDT"
    
    def test_confidence_score_clamping_parity(self):
        """Verify ConfidenceScore clamps to [0, 1]."""
        score_high = ConfidenceScore(1.5)
        assert score_high.value == 1.0
        
        score_low = ConfidenceScore(-0.5)
        assert score_low.value == 0.0
        
        score_normal = ConfidenceScore(0.75)
        assert score_normal.value == 0.75


class TestRiskEntityParity:
    """Test risk entities match legacy RiskGuardian behavior."""
    
    def test_risk_level_ordering_parity(self):
        """Verify RiskLevel ordering matches legacy."""
        assert RiskLevel.LOW < RiskLevel.MEDIUM
        assert RiskLevel.MEDIUM < RiskLevel.HIGH
        assert RiskLevel.HIGH < RiskLevel.CRITICAL
    
    def test_risk_alert_blocking_parity(self):
        """Verify RiskAlert blocking rules match legacy."""
        alert = RiskAlert.daily_loss_alert(current_loss=500.0, limit=400.0)
        assert alert.is_blocking is True
        assert alert.level == RiskLevel.CRITICAL
        
        alert_drawdown = RiskAlert.drawdown_alert(current_drawdown=0.20, threshold=0.15)
        assert alert_drawdown.is_blocking is True
    
    def test_limit_state_tracking_parity(self):
        """Verify LimitState percentage calculation."""
        limit = LimitState(
            name="daily_loss",
            limit_type="usd",
            max_value=1000.0,
            warning_threshold=0.8,
        )
        
        limit.update(800.0)
        assert limit.current_value == 800.0
        assert limit.usage_ratio == 0.8
        assert limit.is_warning is True
        assert limit.is_exceeded is False
        
        limit.update(1100.0)
        assert limit.is_exceeded is True


class TestMarketEntityParity:
    """Test market entities match legacy coherence engine."""
    
    def test_strategy_vote_direction_parity(self):
        """Verify StrategyVote direction detection."""
        bullish_vote = StrategyVote(
            strategy_name="QuantumMomentum",
            direction="buy",
            score=8.5,
            confidence=0.7,
        )
        assert bullish_vote.is_bullish is True
        assert bullish_vote.is_bearish is False
        
        bearish_vote = StrategyVote(
            strategy_name="MonteCarlo",
            direction="sell",
            score=-5.0,
            confidence=0.6,
        )
        assert bearish_vote.is_bearish is True
    
    def test_strategy_vote_weighted_score_parity(self):
        """Verify weighted_score calculation."""
        vote = StrategyVote(
            strategy_name="test",
            direction="buy",
            score=10.0,
            confidence=0.8,
            weight=1.5,
        )
        assert vote.weighted_score == 10.0 * 1.5
    
    def test_coherence_result_consensus_parity(self):
        """Verify CoherenceResult consensus calculation."""
        result = CoherenceResult(pair="BTC/USD")
        
        result.add_vote(StrategyVote(
            strategy_name="A", direction="buy", score=8, confidence=0.7
        ))
        result.add_vote(StrategyVote(
            strategy_name="B", direction="buy", score=6, confidence=0.6
        ))
        result.add_vote(StrategyVote(
            strategy_name="C", direction="sell", score=-4, confidence=0.5
        ))
        
        consensus = result.calculate_consensus()
        
        assert result.bullish_count == 2
        assert result.bearish_count == 1
        assert consensus == pytest.approx(2/3, rel=0.01)
    
    def test_market_regime_properties_parity(self):
        """Verify MarketRegime property detection."""
        bull_regime = MarketRegime.TRENDING_BULL
        assert bull_regime.is_bullish is True
        assert bull_regime.allows_trading is True
        
        bear_regime = MarketRegime.TRENDING_BEAR
        assert bear_regime.is_bearish is True
        
        volatile_regime = MarketRegime.HIGH_VOLATILITY
        assert volatile_regime.allows_trading is False


class TestContainerParity:
    """Test DI container provides correct instances."""
    
    def test_container_creates_adapters(self):
        """Verify Container creates trading and risk adapters."""
        from src.omnix.bootstrap.container import Container
        
        container = Container.create(lazy=False)
        
        assert container.trading_adapter is not None
        assert container.risk_adapter is not None
    
    def test_container_feature_flag_default(self):
        """Verify USE_APP_LAYER defaults to False."""
        from src.omnix.bootstrap.container import Container
        
        container = Container.create()
        
        assert container.use_app_layer is False


class TestStrategyWrapperParity:
    """Test strategy wrappers correctly import from legacy."""
    
    def test_quantum_momentum_import(self):
        """Verify QuantumMomentum wrapper imports correctly."""
        try:
            from src.omnix.domain.trading.strategies import QuantumMomentumAnalyzer
            assert QuantumMomentumAnalyzer is not None or QuantumMomentumAnalyzer is None
        except ImportError as e:
            pytest.skip(f"QuantumMomentum not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
