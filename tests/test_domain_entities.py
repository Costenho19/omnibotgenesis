"""
OMNIX V7.0 Domain Entity Tests
================================
Unit tests for domain entities and value objects.

These tests verify that domain logic works correctly
without any infrastructure dependencies.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from src.omnix.domain.trading.entities import (
    Trade,
    Position,
    Signal,
    TradeDirection,
    TradeStatus,
    SignalStrength,
    PositionStatus,
)
from src.omnix.domain.trading.value_objects import (
    Money,
    Quantity,
    SymbolPair,
    ConfidenceScore,
    PriceLevel,
)
from src.omnix.domain.risk.entities import (
    RiskAlert,
    LimitState,
    CircuitState,
    RiskLevel,
    AlertType,
    CircuitBreakerStatus,
)
from src.omnix.domain.support.market import (
    MarketSnapshot,
    StrategyVote,
    RegimeState,
    MarketRegime,
    CoherenceResult,
)


class TestTradeEntity:
    """Tests for Trade entity."""
    
    def test_trade_creation(self):
        """Test basic trade creation."""
        trade = Trade(
            pair="BTC/USD",
            direction=TradeDirection.BUY,
            quantity=0.1,
            entry_price=50000.0,
            strategy="quantum_momentum",
            confidence=0.75,
        )
        
        assert trade.pair == "BTC/USD"
        assert trade.direction == TradeDirection.BUY
        assert trade.quantity == 0.1
        assert trade.entry_price == 50000.0
        assert trade.status == TradeStatus.PENDING
        assert trade.is_paper is True
    
    def test_calculate_pnl_long(self):
        """Test P&L calculation for long position."""
        trade = Trade(
            direction=TradeDirection.BUY,
            quantity=1.0,
            entry_price=100.0,
            fees=1.0,
        )
        
        assert trade.calculate_pnl(110.0) == 9.0
        assert trade.calculate_pnl(90.0) == -11.0
        assert trade.is_profitable(110.0) is True
        assert trade.is_profitable(90.0) is False
    
    def test_calculate_pnl_short(self):
        """Test P&L calculation for short position."""
        trade = Trade(
            direction=TradeDirection.SELL,
            quantity=1.0,
            entry_price=100.0,
            fees=1.0,
        )
        
        assert trade.calculate_pnl(90.0) == 9.0
        assert trade.calculate_pnl(110.0) == -11.0
    
    def test_stop_loss_trigger(self):
        """Test stop loss detection."""
        trade = Trade(
            direction=TradeDirection.BUY,
            entry_price=100.0,
            stop_loss=95.0,
        )
        
        assert trade.should_stop_loss(96.0) is False
        assert trade.should_stop_loss(95.0) is True
        assert trade.should_stop_loss(90.0) is True
    
    def test_take_profit_trigger(self):
        """Test take profit detection."""
        trade = Trade(
            direction=TradeDirection.BUY,
            entry_price=100.0,
            take_profit=110.0,
        )
        
        assert trade.should_take_profit(105.0) is False
        assert trade.should_take_profit(110.0) is True
        assert trade.should_take_profit(115.0) is True
    
    def test_close_trade(self):
        """Test closing a trade."""
        trade = Trade(
            direction=TradeDirection.BUY,
            quantity=1.0,
            entry_price=100.0,
        )
        
        trade.close(exit_price=110.0)
        
        assert trade.exit_price == 110.0
        assert trade.status == TradeStatus.CLOSED
        assert trade.pnl == 10.0
        assert trade.closed_at is not None
    
    def test_trade_serialization(self):
        """Test trade to_dict and from_dict."""
        trade = Trade(
            pair="ETH/USD",
            direction=TradeDirection.SELL,
            quantity=5.0,
            entry_price=2000.0,
            strategy="ares_v1",
        )
        
        data = trade.to_dict()
        restored = Trade.from_dict(data)
        
        assert restored.pair == trade.pair
        assert restored.direction == trade.direction
        assert restored.quantity == trade.quantity
    
    def test_trade_direction_parsing(self):
        """Test direction parsing from strings."""
        assert TradeDirection.from_string("buy") == TradeDirection.BUY
        assert TradeDirection.from_string("LONG") == TradeDirection.BUY
        assert TradeDirection.from_string("sell") == TradeDirection.SELL
        assert TradeDirection.from_string("SHORT") == TradeDirection.SELL


class TestSignalEntity:
    """Tests for Signal entity."""
    
    def test_signal_strength_from_score(self):
        """Test signal strength classification."""
        assert SignalStrength.from_score(5) == SignalStrength.WEAK
        assert SignalStrength.from_score(8) == SignalStrength.MODERATE
        assert SignalStrength.from_score(12) == SignalStrength.STRONG
        assert SignalStrength.from_score(15) == SignalStrength.VERY_STRONG
        assert SignalStrength.from_score(20) == SignalStrength.VERY_STRONG
    
    def test_signal_actionability(self):
        """Test signal actionability check."""
        strong_signal = Signal(
            strength=SignalStrength.STRONG,
            confidence=0.7,
            coherence_passed=True,
        )
        assert strong_signal.is_actionable() is True
        
        weak_signal = Signal(
            strength=SignalStrength.WEAK,
            confidence=0.7,
        )
        assert weak_signal.is_actionable() is False
        
        vetoed_signal = Signal(
            strength=SignalStrength.STRONG,
            confidence=0.7,
            coherence_passed=False,
        )
        assert vetoed_signal.is_actionable() is False
    
    def test_signal_from_strategy_output(self):
        """Test creating signal from strategy analysis."""
        signal = Signal.from_strategy_output(
            pair="BTC/USD",
            direction="buy",
            score=14.5,
            strategy="quantum_momentum",
            votes={"qm": 0.8, "mc": 0.7, "hmm": 0.6},
            confidence=0.75,
        )
        
        assert signal.pair == "BTC/USD"
        assert signal.direction == TradeDirection.BUY
        assert signal.strength == SignalStrength.STRONG
        assert signal.score == 14.5


class TestValueObjects:
    """Tests for value objects."""
    
    def test_money_arithmetic(self):
        """Test Money arithmetic operations."""
        usd100 = Money.from_float(100.0, "USD")
        usd50 = Money.from_float(50.0, "USD")
        
        assert (usd100 + usd50).to_float() == 150.0
        assert (usd100 - usd50).to_float() == 50.0
        assert (usd100 * 2).to_float() == 200.0
        assert (usd100 / 2).to_float() == 50.0
    
    def test_money_currency_mismatch(self):
        """Test Money raises on currency mismatch."""
        usd = Money.from_float(100.0, "USD")
        eur = Money.from_float(100.0, "EUR")
        
        with pytest.raises(ValueError):
            _ = usd + eur
    
    def test_quantity_non_negative(self):
        """Test Quantity enforces non-negative."""
        qty = Quantity.from_float(10.0)
        assert qty.to_float() == 10.0
        
        with pytest.raises(ValueError):
            Quantity.from_float(-5.0)
    
    def test_symbol_pair_parsing(self):
        """Test SymbolPair parsing from various formats."""
        assert SymbolPair.from_string("BTC/USD").base == "BTC"
        assert SymbolPair.from_string("BTC-USD").quote == "USD"
        assert SymbolPair.from_string("BTCUSD").base == "BTC"
        assert SymbolPair.from_string("XXBTZUSD").base == "BTC"
    
    def test_symbol_pair_formats(self):
        """Test SymbolPair output formats."""
        pair = SymbolPair("ETH", "USD")
        
        assert pair.to_standard() == "ETH/USD"
        assert pair.to_compact() == "ETHUSD"
        assert pair.to_kraken() == "ETH/USD"
    
    def test_confidence_score_clamping(self):
        """Test ConfidenceScore clamps to valid range."""
        normal = ConfidenceScore(0.7)
        assert normal.value == 0.7
        
        over = ConfidenceScore(1.5)
        assert over.value == 1.0
        
        under = ConfidenceScore(-0.5)
        assert under.value == 0.0
    
    def test_confidence_categories(self):
        """Test ConfidenceScore categorization."""
        assert ConfidenceScore(0.9).category == "very_high"
        assert ConfidenceScore(0.7).category == "high"
        assert ConfidenceScore(0.5).category == "medium"
        assert ConfidenceScore(0.3).category == "low"
        assert ConfidenceScore(0.1).category == "very_low"


class TestRiskEntities:
    """Tests for risk domain entities."""
    
    def test_risk_alert_creation(self):
        """Test RiskAlert factory methods."""
        drawdown = RiskAlert.drawdown_alert(0.12, 0.10)
        assert drawdown.alert_type == AlertType.DRAWDOWN
        assert drawdown.is_blocking is True
        
        daily_loss = RiskAlert.daily_loss_alert(500.0, 300.0)
        assert daily_loss.alert_type == AlertType.DAILY_LOSS
        assert daily_loss.level == RiskLevel.CRITICAL
    
    def test_risk_alert_lifecycle(self):
        """Test RiskAlert acknowledgement."""
        alert = RiskAlert(message="Test alert")
        assert alert.is_active() is True
        
        alert.acknowledge()
        assert alert.is_acknowledged is True
        assert alert.is_active() is False
    
    def test_limit_state_tracking(self):
        """Test LimitState updates."""
        limit = LimitState(
            name="daily_trades",
            limit_type="count",
            max_value=10,
            warning_threshold=0.8,
        )
        
        limit.update(5)
        assert limit.usage_ratio == 0.5
        assert limit.is_warning is False
        assert limit.is_exceeded is False
        
        limit.update(8)
        assert limit.is_warning is True
        
        limit.update(10)
        assert limit.is_exceeded is True
    
    def test_circuit_breaker_flow(self):
        """Test CircuitState state machine."""
        circuit = CircuitState(
            name="trading",
            failure_threshold=3,
            success_threshold=2,
        )
        
        assert circuit.is_closed is True
        
        circuit.record_failure("error 1")
        circuit.record_failure("error 2")
        assert circuit.is_closed is True
        
        circuit.record_failure("error 3")
        assert circuit.is_open is True
        
        circuit.force_close()
        assert circuit.is_closed is True


class TestMarketEntities:
    """Tests for market support entities."""
    
    def test_market_regime_properties(self):
        """Test MarketRegime helper properties."""
        assert MarketRegime.TRENDING_BULL.is_bullish is True
        assert MarketRegime.TRENDING_BEAR.is_bearish is True
        assert MarketRegime.RANGING.is_neutral is True
        assert MarketRegime.HIGH_VOLATILITY.allows_trading is False
    
    def test_market_snapshot(self):
        """Test MarketSnapshot creation."""
        snapshot = MarketSnapshot(
            pair="BTC/USD",
            price=50000.0,
            bid=49990.0,
            ask=50010.0,
            spread=20.0,
        )
        
        assert snapshot.spread_pct == pytest.approx(0.04, rel=0.01)
        assert snapshot.is_liquid is True
    
    def test_strategy_vote(self):
        """Test StrategyVote operations."""
        vote = StrategyVote(
            strategy_name="quantum_momentum",
            direction="buy",
            score=0.8,
            weight=1.5,
        )
        
        assert vote.is_bullish is True
        assert vote.weighted_score == pytest.approx(1.2)
    
    def test_coherence_result(self):
        """Test CoherenceResult aggregation."""
        result = CoherenceResult(pair="BTC/USD")
        
        result.add_vote(StrategyVote(strategy_name="qm", direction="buy", score=0.8))
        result.add_vote(StrategyVote(strategy_name="mc", direction="buy", score=0.7))
        result.add_vote(StrategyVote(strategy_name="hmm", direction="sell", score=0.6))
        
        assert result.vote_count == 3
        assert result.bullish_count == 2
        assert result.bearish_count == 1
        
        consensus = result.calculate_consensus()
        assert consensus == pytest.approx(0.667, rel=0.01)


class TestRiskLevelComparison:
    """Tests for RiskLevel comparison."""
    
    def test_risk_level_ordering(self):
        """Test RiskLevel can be compared."""
        assert RiskLevel.LOW < RiskLevel.MEDIUM
        assert RiskLevel.MEDIUM < RiskLevel.HIGH
        assert RiskLevel.HIGH < RiskLevel.CRITICAL
        assert RiskLevel.CRITICAL < RiskLevel.EMERGENCY
        
        assert RiskLevel.EMERGENCY >= RiskLevel.LOW


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
