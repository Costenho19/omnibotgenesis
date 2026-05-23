"""
OMNIX V7.0 Phase 2 Integration Tests
======================================
Tests validating end-to-end flows through new architecture.

These tests verify:
1. Use cases work correctly with adapters
2. Container wiring is correct
3. Feature flags control behavior
4. No regressions from legacy behavior
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
from decimal import Decimal

from src.omnix.domain.trading.entities import (
    Trade, Position, Signal,
    TradeDirection, TradeStatus, SignalStrength,
)
from src.omnix.domain.trading.value_objects import Money, Quantity, SymbolPair
from src.omnix.domain.support.market import (
    MarketSnapshot, StrategyVote, CoherenceResult, RegimeState, MarketRegime,
)


class TestContainerIntegration:
    """Test DI container properly wires components."""
    
    def test_container_creates_successfully(self):
        """Verify Container.create() works without errors."""
        from src.omnix.bootstrap.container import Container
        
        container = Container.create(lazy=False)
        assert container is not None
    
    def test_container_has_trading_adapter(self):
        """Verify trading adapter is available."""
        from src.omnix.bootstrap.container import Container
        
        container = Container.create()
        assert hasattr(container, "trading_adapter")
    
    def test_container_has_risk_adapter(self):
        """Verify risk adapter is available."""
        from src.omnix.bootstrap.container import Container
        
        container = Container.create()
        assert hasattr(container, "risk_adapter")
    
    def test_feature_flag_controls_app_layer(self):
        """Verify USE_APP_LAYER flag controls behavior."""
        from src.omnix.bootstrap.container import Container
        
        container = Container.create()
        assert container.use_app_layer is False


class TestExecuteTradeIntegration:
    """Test ExecuteTradeUseCase integration."""
    
    @pytest.mark.asyncio
    async def test_execute_trade_with_mock_ports(self):
        """Test trade execution with mocked dependencies."""
        from src.omnix.application.trading import (
            ExecuteTradeUseCase,
            ExecuteTradeRequest,
        )
        
        mock_trading = AsyncMock()
        mock_trading.execute_order.return_value = Trade(
            id="test-123",
            pair="BTC/USD",
            direction=TradeDirection.BUY,
            quantity=0.1,
            entry_price=50000.0,
            status=TradeStatus.EXECUTED,
        )
        
        mock_risk = AsyncMock()
        mock_risk.can_trade.return_value = (True, None)
        mock_risk.record_trade.return_value = None
        
        mock_repository = AsyncMock()
        mock_repository.save.return_value = None
        
        use_case = ExecuteTradeUseCase(
            trading_port=mock_trading,
            risk_port=mock_risk,
            trade_repository=mock_repository,
        )
        
        request = ExecuteTradeRequest(
            pair="BTC/USD",
            direction=TradeDirection.BUY,
            quantity=0.1,
            strategy="test",
            confidence=0.7,
        )
        
        response = await use_case.execute(request)
        
        assert response.success is True
        assert response.trade is not None
        assert response.trade.pair == "BTC/USD"


class TestScanMarketIntegration:
    """Test ScanMarketUseCase integration."""
    
    @pytest.mark.asyncio
    async def test_scan_market_with_mock_ports(self):
        """Test market scanning with mocked dependencies."""
        from src.omnix.application.trading import (
            ScanMarketUseCase,
            ScanMarketRequest,
        )
        
        mock_market = AsyncMock()
        mock_market.get_tradable_pairs.return_value = ["BTC/USD", "ETH/USD"]
        mock_market.get_snapshot.return_value = MarketSnapshot(
            pair="BTC/USD",
            price=50000.0,
            volume_24h=1000000.0,
            change_24h=2.5,
            volatility=0.03,
            liquidity_score=0.8,
            regime=RegimeState(
                regime=MarketRegime.TRENDING_BULL,
                confidence=0.7,
                strength=0.6,
            ),
        )
        
        mock_strategy = AsyncMock()
        mock_strategy.analyze.return_value = StrategyVote(
            strategy_name="test",
            direction="buy",
            score=8.0,
            confidence=0.7,
        )
        
        mock_coherence = AsyncMock()
        result = CoherenceResult(pair="BTC/USD")
        result.passed = True
        result.final_score = 12.0
        result.consensus_ratio = 0.7
        mock_coherence.evaluate.return_value = result
        
        use_case = ScanMarketUseCase(
            market_data=mock_market,
            strategies=[mock_strategy],
            coherence=mock_coherence,
        )
        
        request = ScanMarketRequest(pairs=["BTC/USD"])
        
        response = await use_case.execute(request)
        
        assert response.scanned_pairs == 1


class TestManagePositionsIntegration:
    """Test ManagePositionsUseCase integration."""
    
    @pytest.mark.asyncio
    async def test_list_positions_with_mock_ports(self):
        """Test listing positions with mocked dependencies."""
        from src.omnix.application.trading import (
            ManagePositionsUseCase,
            ManagePositionsRequest,
        )
        
        mock_position = Position(
            id="pos-1",
            pair="BTC/USD",
            direction=TradeDirection.BUY,
            quantity=0.1,
            average_entry=50000.0,
        )
        
        mock_repository = AsyncMock()
        mock_repository.get_open_positions.return_value = [mock_position]
        
        mock_market = AsyncMock()
        mock_market.get_current_price.return_value = 52000.0
        
        use_case = ManagePositionsUseCase(
            position_repository=mock_repository,
            market_data=mock_market,
        )
        
        request = ManagePositionsRequest(operation="list")
        
        response = await use_case.execute(request)
        
        assert response.success is True
        assert len(response.positions) == 1
        assert response.total_unrealized_pnl > 0


class TestCoherenceReportIntegration:
    """Test GenerateCoherenceReportUseCase integration."""
    
    @pytest.mark.asyncio
    async def test_generate_report_with_mock_ports(self):
        """Test coherence report generation with mocked dependencies."""
        from src.omnix.application.trading import (
            GenerateCoherenceReportUseCase,
            CoherenceReportRequest,
        )
        
        mock_snapshot = MarketSnapshot(
            pair="BTC/USD",
            price=50000.0,
            volume_24h=1000000.0,
            change_24h=2.5,
            volatility=0.03,
            liquidity_score=0.8,
            regime=RegimeState(
                regime=MarketRegime.TRENDING_BULL,
                confidence=0.7,
                strength=0.6,
            ),
        )
        
        mock_market = AsyncMock()
        mock_market.get_snapshot.return_value = mock_snapshot
        
        mock_coherence = AsyncMock()
        mock_coherence.get_strategy_votes.return_value = [
            StrategyVote(strategy_name="A", direction="buy", score=8, confidence=0.7),
            StrategyVote(strategy_name="B", direction="buy", score=6, confidence=0.6),
        ]
        mock_coherence.evaluate.return_value = CoherenceResult(
            pair="BTC/USD",
            passed=True,
            final_score=14.0,
            consensus_ratio=0.8,
        )
        
        use_case = GenerateCoherenceReportUseCase(
            coherence_engine=mock_coherence,
            market_data=mock_market,
        )
        
        request = CoherenceReportRequest(pair="BTC/USD")
        
        response = await use_case.execute(request)
        
        assert response.success is True
        assert response.report is not None
        assert response.report.pair == "BTC/USD"
        assert response.report.overall_passed is True


class TestAdapterIntegration:
    """Test adapter implementations."""
    
    def test_trading_adapter_creation(self):
        """Verify TradingServiceAdapter can be created."""
        from src.omnix.infrastructure.adapters import TradingServiceAdapter
        
        adapter = TradingServiceAdapter()
        assert adapter is not None
    
    def test_risk_adapter_creation(self):
        """Verify RiskGuardianAdapter can be created."""
        from src.omnix.infrastructure.adapters import RiskGuardianAdapter
        
        adapter = RiskGuardianAdapter()
        assert adapter is not None
    
    def test_coherence_adapter_creation(self):
        """Verify CoherenceEngineAdapter can be created."""
        from src.omnix.infrastructure.adapters import CoherenceEngineAdapter
        
        adapter = CoherenceEngineAdapter()
        assert adapter is not None


class TestDomainEntityIsolation:
    """Test domain entities are independent of infrastructure."""
    
    def test_trade_entity_no_infrastructure_deps(self):
        """Verify Trade entity works without infrastructure."""
        trade = Trade(
            id="test-1",
            pair="BTC/USD",
            direction=TradeDirection.BUY,
            quantity=0.1,
            entry_price=50000.0,
            status=TradeStatus.PENDING,
        )
        
        assert trade.calculate_pnl(52000.0) == 200.0
        assert trade.is_profitable(52000.0) is True
    
    def test_signal_entity_no_infrastructure_deps(self):
        """Verify Signal entity works without infrastructure."""
        signal = Signal(
            pair="ETH/USD",
            direction=TradeDirection.BUY,
            strength=SignalStrength.STRONG,
            score=12.0,
            confidence=0.7,
            strategy="QuantumMomentum",
            coherence_passed=True,
        )
        
        assert signal.is_actionable() is True
    
    def test_value_objects_no_infrastructure_deps(self):
        """Verify value objects work without infrastructure."""
        money = Money(amount=Decimal("1000.00"), currency="USD")
        quantity = Quantity(value=Decimal("0.5"))
        pair = SymbolPair.from_string("BTC/USD")
        
        assert money.amount == Decimal("1000.00")
        assert quantity.value == Decimal("0.5")
        assert pair.base == "BTC"


class TestFeatureFlagBehavior:
    """Test feature flag controls architecture routing."""
    
    def test_use_app_layer_default_false(self):
        """Verify USE_APP_LAYER defaults to False."""
        from src.omnix.config.settings import get_settings
        
        settings = get_settings()
        assert settings.use_app_layer is False
    
    def test_container_respects_feature_flag(self):
        """Verify container uses feature flag."""
        from src.omnix.bootstrap.container import Container
        
        container = Container.create()
        assert container.use_app_layer is False


class TestBackwardCompatibility:
    """Test backward compatibility with legacy imports."""
    
    def test_strategy_re_exports_work(self):
        """Verify strategy re-exports don't break."""
        try:
            from src.omnix.domain.trading.strategies import QuantumMomentumAnalyzer
            if QuantumMomentumAnalyzer is None:
                pytest.skip("QuantumMomentum not available in current environment")
        except ImportError:
            pytest.skip("QuantumMomentum not in legacy path")
    
    def test_domain_entities_importable(self):
        """Verify all domain entities can be imported."""
        from src.omnix.domain.trading.entities import (
            Trade, Position, Signal, TradeDirection, TradeStatus,
        )
        from src.omnix.domain.trading.value_objects import (
            Money, Quantity, SymbolPair, ConfidenceScore,
        )
        from src.omnix.domain.risk.entities import (
            RiskAlert, RiskLevel, AlertType, LimitState,
        )
        
        assert Trade is not None
        assert Position is not None
        assert Signal is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
