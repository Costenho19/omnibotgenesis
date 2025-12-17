"""
OMNIX V7.0 - PortfolioPort Tests
================================
Unit tests for PortfolioPort and PortfolioAdapter.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from src.omnix.ports.driven.portfolio_port import (
    PortfolioPort,
    PortfolioPosition,
    PortfolioView,
    ExposureReport,
    RebalanceOrder,
    RebalanceCommand,
    RebalanceStrategy,
    TargetAllocation,
    AllocationPlan,
    AssetClass,
)
from src.omnix.infrastructure.adapters.portfolio_adapter import PortfolioAdapter


class TestPortfolioEnums:
    """Test portfolio-related enums."""
    
    def test_asset_classes(self):
        assert AssetClass.CRYPTO.value == "crypto"
        assert AssetClass.STOCKS.value == "stocks"
        assert AssetClass.FOREX.value == "forex"
        assert AssetClass.DERIVATIVES.value == "derivatives"
    
    def test_rebalance_strategies(self):
        assert RebalanceStrategy.THRESHOLD.value == "threshold"
        assert RebalanceStrategy.CALENDAR.value == "calendar"
        assert RebalanceStrategy.TACTICAL.value == "tactical"
        assert RebalanceStrategy.RISK_PARITY.value == "risk_parity"


class TestPortfolioPosition:
    """Test PortfolioPosition DTO."""
    
    def test_position_creation(self):
        position = PortfolioPosition(
            symbol="BTC",
            asset_class=AssetClass.CRYPTO,
            quantity=1.5,
            avg_entry_price=45000,
            current_price=50000,
            market_value_usd=75000,
            unrealized_pnl=7500,
            unrealized_pnl_pct=11.1,
            weight_pct=50.0,
            target_weight_pct=40.0
        )
        
        assert position.symbol == "BTC"
        assert position.is_overweight is True
        assert position.is_underweight is False
    
    def test_underweight_position(self):
        position = PortfolioPosition(
            symbol="ETH",
            asset_class=AssetClass.CRYPTO,
            quantity=10.0,
            avg_entry_price=3000,
            current_price=3500,
            market_value_usd=35000,
            unrealized_pnl=5000,
            unrealized_pnl_pct=16.67,
            weight_pct=20.0,
            target_weight_pct=30.0
        )
        
        assert position.is_overweight is False
        assert position.is_underweight is True


class TestPortfolioView:
    """Test PortfolioView DTO."""
    
    def test_portfolio_view_creation(self):
        view = PortfolioView(
            total_value_usd=100000,
            cash_usd=20000,
            invested_usd=80000,
            positions=[],
            position_count=0,
            asset_allocation={'crypto': 80, 'cash': 20},
            unrealized_pnl=5000,
            unrealized_pnl_pct=6.25,
            realized_pnl_today=500
        )
        
        assert view.total_value_usd == 100000
        assert view.cash_pct == 20.0
    
    def test_empty_portfolio_cash_pct(self):
        view = PortfolioView(
            total_value_usd=0,
            cash_usd=0,
            invested_usd=0,
            positions=[],
            position_count=0,
            asset_allocation={},
            unrealized_pnl=0,
            unrealized_pnl_pct=0,
            realized_pnl_today=0
        )
        
        assert view.cash_pct == 100.0


class TestRebalanceCommand:
    """Test RebalanceCommand DTO."""
    
    def test_neutral_rebalance(self):
        command = RebalanceCommand(
            command_id="R001",
            strategy=RebalanceStrategy.THRESHOLD,
            orders=[],
            total_buy_usd=5000,
            total_sell_usd=5000,
            net_flow_usd=0,
            estimated_cost_usd=10,
            drift_before_pct=8.5,
            drift_after_pct=1.2
        )
        
        assert command.is_neutral is True
    
    def test_non_neutral_rebalance(self):
        command = RebalanceCommand(
            command_id="R002",
            strategy=RebalanceStrategy.TACTICAL,
            orders=[],
            total_buy_usd=10000,
            total_sell_usd=5000,
            net_flow_usd=5000,
            estimated_cost_usd=25,
            drift_before_pct=15.0,
            drift_after_pct=2.0
        )
        
        assert command.is_neutral is False


class TestPortfolioAdapter:
    """Test PortfolioAdapter implementation."""
    
    def test_adapter_initialization(self):
        adapter = PortfolioAdapter()
        
        assert adapter._portfolio_engine is None
        assert adapter._portfolio_optimizer is None
        assert adapter._exposure_manager is None
        assert adapter._rebalancer is None
        assert adapter._initialized is False
    
    def test_adapter_with_injected_services(self):
        mock_engine = Mock()
        mock_optimizer = Mock()
        
        adapter = PortfolioAdapter(
            portfolio_engine=mock_engine,
            portfolio_optimizer=mock_optimizer
        )
        
        assert adapter._portfolio_engine == mock_engine
        assert adapter._portfolio_optimizer == mock_optimizer
    
    def test_asset_class_mapping(self):
        adapter = PortfolioAdapter()
        
        assert adapter._map_asset_class("crypto") == AssetClass.CRYPTO
        assert adapter._map_asset_class("stocks") == AssetClass.STOCKS
        assert adapter._map_asset_class("forex") == AssetClass.FOREX
    
    def test_rebalance_strategy_mapping(self):
        adapter = PortfolioAdapter()
        
        assert adapter._map_rebalance_strategy("threshold") == RebalanceStrategy.THRESHOLD
        assert adapter._map_rebalance_strategy("calendar") == RebalanceStrategy.CALENDAR
        assert adapter._map_rebalance_strategy("risk_parity") == RebalanceStrategy.RISK_PARITY
    
    def test_health_check_no_services(self):
        adapter = PortfolioAdapter()
        health = adapter.health_check()
        
        assert 'healthy' in health
        assert 'adapter' in health
        assert health['adapter'] == 'PortfolioAdapter'
        assert 'components' in health
    
    def test_get_portfolio_view_fallback(self):
        adapter = PortfolioAdapter()
        
        result = adapter.get_portfolio_view()
        
        assert isinstance(result, PortfolioView)
        assert result.total_value_usd == 0
    
    def test_get_exposure_report_fallback(self):
        adapter = PortfolioAdapter()
        
        result = adapter.get_exposure_report()
        
        assert isinstance(result, ExposureReport)
        assert result.leverage == 1
    
    def test_calculate_rebalance_fallback(self):
        adapter = PortfolioAdapter()
        
        result = adapter.calculate_rebalance()
        
        assert isinstance(result, RebalanceCommand)
        assert result.status == 'failed'
    
    def test_set_allocation_plan(self):
        adapter = PortfolioAdapter()
        
        plan = AllocationPlan(
            plan_id="P001",
            name="Test Plan",
            targets=[],
            rebalance_strategy=RebalanceStrategy.THRESHOLD
        )
        
        result = adapter.set_allocation_plan(plan)
        
        assert result is True
        assert adapter._active_plan == plan


class TestPortfolioPortProtocol:
    """Test that PortfolioAdapter implements PortfolioPort protocol."""
    
    def test_adapter_has_required_methods(self):
        adapter = PortfolioAdapter()
        
        required_methods = [
            'get_portfolio_view',
            'get_positions',
            'get_exposure_report',
            'calculate_rebalance',
            'execute_rebalance',
            'get_allocation_plan',
            'set_allocation_plan',
            'get_drift_analysis',
            'get_performance_metrics',
            'get_correlation_matrix',
            'health_check',
        ]
        
        for method_name in required_methods:
            assert hasattr(adapter, method_name), f"Missing method: {method_name}"
            assert callable(getattr(adapter, method_name)), f"Not callable: {method_name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
