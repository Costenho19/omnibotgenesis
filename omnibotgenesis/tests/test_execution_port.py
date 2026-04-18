"""
OMNIX V7.0 - ExecutionPort Tests
=================================
Unit and integration tests for ExecutionPort and ExecutionAdapter.

Test Categories:
1. Unit tests with mocked services
2. DTO construction tests
3. Health check tests
4. Integration tests (when services available)
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from src.omnix.ports.driven.execution_port import (
    ExecutionPort,
    LiquidityReport,
    VolatilityMetrics,
    VolatilityRegime,
    CorrelationMatrix,
    ContagionLevel,
    SlippagePrediction,
    ExecutionTiming,
    ExecutionOrder,
    ExecutionResult,
    ExecutionStyle,
    ExecutionUrgency,
    MarketCondition,
)
from src.omnix.infrastructure.adapters.execution_adapter import ExecutionAdapter


class TestExecutionEnums:
    """Test execution-related enums."""
    
    def test_execution_styles(self):
        """Test all ExecutionStyle enum values."""
        assert ExecutionStyle.MARKET.value == "market"
        assert ExecutionStyle.LIMIT.value == "limit"
        assert ExecutionStyle.TWAP.value == "twap"
        assert ExecutionStyle.VWAP.value == "vwap"
        assert ExecutionStyle.ICEBERG.value == "iceberg"
    
    def test_execution_urgency(self):
        """Test all ExecutionUrgency enum values."""
        assert ExecutionUrgency.CRITICAL.value == "critical"
        assert ExecutionUrgency.HIGH.value == "high"
        assert ExecutionUrgency.NORMAL.value == "normal"
        assert ExecutionUrgency.LOW.value == "low"
        assert ExecutionUrgency.PASSIVE.value == "passive"
    
    def test_market_conditions(self):
        """Test all MarketCondition enum values."""
        assert MarketCondition.FAVORABLE.value == "favorable"
        assert MarketCondition.NEUTRAL.value == "neutral"
        assert MarketCondition.ADVERSE.value == "adverse"
        assert MarketCondition.CRISIS.value == "crisis"
    
    def test_volatility_regimes(self):
        """Test all VolatilityRegime enum values."""
        assert VolatilityRegime.LOW.value == "low"
        assert VolatilityRegime.NORMAL.value == "normal"
        assert VolatilityRegime.HIGH.value == "high"
        assert VolatilityRegime.EXTREME.value == "extreme"
    
    def test_contagion_levels(self):
        """Test all ContagionLevel enum values."""
        assert ContagionLevel.LOW.value == "low"
        assert ContagionLevel.ELEVATED.value == "elevated"
        assert ContagionLevel.HIGH.value == "high"
        assert ContagionLevel.EXTREME.value == "extreme"


class TestLiquidityReport:
    """Test LiquidityReport DTO."""
    
    def test_liquidity_report_creation(self):
        """Test LiquidityReport dataclass creation."""
        report = LiquidityReport(
            symbol="BTC/USD",
            liquidity_score=0.85,
            bid_depth_usd=1000000.0,
            ask_depth_usd=950000.0,
            spread_bps=5.0,
            depth_imbalance=0.026,
            hidden_liquidity_detected=True,
            hidden_liquidity_confidence=0.7,
            tblr_ratio=1.05,
            optimal_order_size_usd=50000.0
        )
        
        assert report.symbol == "BTC/USD"
        assert report.liquidity_score == 0.85
        assert report.is_liquid is True
    
    def test_liquidity_is_liquid_property(self):
        """Test is_liquid property threshold."""
        liquid_report = LiquidityReport(
            symbol="BTC/USD",
            liquidity_score=0.7,
            bid_depth_usd=100000,
            ask_depth_usd=100000,
            spread_bps=10,
            depth_imbalance=0,
            hidden_liquidity_detected=False,
            hidden_liquidity_confidence=0,
            tblr_ratio=1.0,
            optimal_order_size_usd=10000
        )
        assert liquid_report.is_liquid is True
        
        illiquid_report = LiquidityReport(
            symbol="SHITCOIN/USD",
            liquidity_score=0.3,
            bid_depth_usd=1000,
            ask_depth_usd=1000,
            spread_bps=100,
            depth_imbalance=0,
            hidden_liquidity_detected=False,
            hidden_liquidity_confidence=0,
            tblr_ratio=0.5,
            optimal_order_size_usd=100
        )
        assert illiquid_report.is_liquid is False


class TestSlippagePrediction:
    """Test SlippagePrediction DTO."""
    
    def test_slippage_prediction_creation(self):
        """Test SlippagePrediction dataclass creation."""
        prediction = SlippagePrediction(
            expected_slippage_bps=15.0,
            worst_case_slippage_bps=45.0,
            best_case_slippage_bps=5.0,
            confidence=0.85
        )
        
        assert prediction.expected_slippage_bps == 15.0
        assert prediction.expected_slippage_pct == 0.15
        assert prediction.is_acceptable is True
    
    def test_slippage_acceptability(self):
        """Test is_acceptable property threshold (50 bps)."""
        acceptable = SlippagePrediction(
            expected_slippage_bps=40.0,
            worst_case_slippage_bps=80.0,
            best_case_slippage_bps=20.0,
            confidence=0.7
        )
        assert acceptable.is_acceptable is True
        
        unacceptable = SlippagePrediction(
            expected_slippage_bps=60.0,
            worst_case_slippage_bps=120.0,
            best_case_slippage_bps=30.0,
            confidence=0.6
        )
        assert unacceptable.is_acceptable is False


class TestExecutionOrder:
    """Test ExecutionOrder DTO."""
    
    def test_execution_order_creation(self):
        """Test ExecutionOrder dataclass creation."""
        order = ExecutionOrder(
            symbol="ETH/USD",
            side="buy",
            size_usd=10000.0,
            urgency=ExecutionUrgency.NORMAL,
            max_slippage_bps=50.0
        )
        
        assert order.symbol == "ETH/USD"
        assert order.side == "buy"
        assert order.size_usd == 10000.0
        assert order.urgency == ExecutionUrgency.NORMAL
    
    def test_execution_order_defaults(self):
        """Test ExecutionOrder default values."""
        order = ExecutionOrder(
            symbol="BTC/USD",
            side="sell",
            size_usd=5000.0
        )
        
        assert order.urgency == ExecutionUrgency.NORMAL
        assert order.max_slippage_bps == 50.0
        assert order.prefer_passive is False
        assert order.split_allowed is True


class TestExecutionAdapter:
    """Test ExecutionAdapter implementation."""
    
    def test_adapter_initialization(self):
        """Test adapter initializes without external services."""
        adapter = ExecutionAdapter()
        
        assert adapter._execution_protocol is None
        assert adapter._liquidity_analyzer is None
        assert adapter._correlation_engine is None
        assert adapter._volatility_engine is None
        assert adapter._initialized is False
    
    def test_adapter_with_injected_services(self):
        """Test adapter with injected mock services."""
        mock_protocol = Mock()
        mock_liquidity = Mock()
        mock_correlation = Mock()
        mock_volatility = Mock()
        
        adapter = ExecutionAdapter(
            execution_protocol=mock_protocol,
            liquidity_analyzer=mock_liquidity,
            correlation_engine=mock_correlation,
            volatility_engine=mock_volatility
        )
        
        assert adapter._execution_protocol == mock_protocol
        assert adapter._liquidity_analyzer == mock_liquidity
    
    def test_volatility_regime_mapping(self):
        """Test _map_volatility_regime method."""
        adapter = ExecutionAdapter()
        
        assert adapter._map_volatility_regime("low") == VolatilityRegime.LOW
        assert adapter._map_volatility_regime("NORMAL") == VolatilityRegime.NORMAL
        assert adapter._map_volatility_regime("high") == VolatilityRegime.HIGH
        assert adapter._map_volatility_regime("extreme") == VolatilityRegime.EXTREME
    
    def test_contagion_level_mapping(self):
        """Test _map_contagion_level method."""
        adapter = ExecutionAdapter()
        
        assert adapter._map_contagion_level("low") == ContagionLevel.LOW
        assert adapter._map_contagion_level("elevated") == ContagionLevel.ELEVATED
        assert adapter._map_contagion_level("HIGH") == ContagionLevel.HIGH
    
    def test_execution_style_mapping(self):
        """Test _map_execution_style method."""
        adapter = ExecutionAdapter()
        
        assert adapter._map_execution_style("market") == ExecutionStyle.MARKET
        assert adapter._map_execution_style("TWAP") == ExecutionStyle.TWAP
        assert adapter._map_execution_style("vwap") == ExecutionStyle.VWAP
    
    def test_market_condition_mapping(self):
        """Test _map_market_condition method."""
        adapter = ExecutionAdapter()
        
        assert adapter._map_market_condition("favorable") == MarketCondition.FAVORABLE
        assert adapter._map_market_condition("NEUTRAL") == MarketCondition.NEUTRAL
        assert adapter._map_market_condition("adverse") == MarketCondition.ADVERSE
    
    def test_health_check_no_services(self):
        """Test health_check when services not initialized."""
        adapter = ExecutionAdapter()
        health = adapter.health_check()
        
        assert 'healthy' in health
        assert 'adapter' in health
        assert health['adapter'] == 'ExecutionAdapter'
        assert 'components' in health
    
    def test_evaluate_liquidity_fallback(self):
        """Test evaluate_liquidity returns fallback when services unavailable."""
        adapter = ExecutionAdapter()
        adapter._initialized = False
        
        result = adapter.evaluate_liquidity("BTC/USD", 10000.0)
        
        assert result is not None
        assert result.symbol == "BTC/USD"
        assert isinstance(result, LiquidityReport)
    
    def test_compute_micro_volatility_fallback(self):
        """Test compute_micro_volatility returns fallback when services unavailable."""
        adapter = ExecutionAdapter()
        adapter._initialized = False
        
        result = adapter.compute_micro_volatility("BTC/USD")
        
        assert result is not None
        assert result.symbol == "BTC/USD"
        assert result.regime == VolatilityRegime.NORMAL
    
    def test_is_execution_safe_logic(self):
        """Test is_execution_safe method logic."""
        adapter = ExecutionAdapter()
        
        is_safe, reason = adapter.is_execution_safe("BTC/USD", 1000.0)
        
        assert isinstance(is_safe, bool)
        assert isinstance(reason, str)
    
    def test_get_execution_summary(self):
        """Test get_execution_summary returns expected structure."""
        adapter = ExecutionAdapter()
        
        summary = adapter.get_execution_summary("BTC/USD")
        
        assert 'symbol' in summary
        assert 'liquidity_score' in summary
        assert 'volatility_regime' in summary
        assert summary['symbol'] == "BTC/USD"


class TestExecutionPortProtocol:
    """Test that ExecutionAdapter implements ExecutionPort protocol."""
    
    def test_adapter_has_required_methods(self):
        """Verify adapter has all required protocol methods."""
        adapter = ExecutionAdapter()
        
        required_methods = [
            'evaluate_liquidity',
            'assess_correlation',
            'compute_micro_volatility',
            'predict_slippage',
            'get_optimal_timing',
            'route_execution',
            'get_market_condition',
            'get_execution_summary',
            'is_execution_safe',
            'health_check',
        ]
        
        for method_name in required_methods:
            assert hasattr(adapter, method_name), f"Missing method: {method_name}"
            assert callable(getattr(adapter, method_name)), f"Not callable: {method_name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
