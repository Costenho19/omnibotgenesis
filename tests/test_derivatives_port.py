"""
OMNIX V7.0 - DerivativesPort Tests
===================================
Unit tests for DerivativesPort and DerivativesAdapter.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from src.omnix.ports.driven.derivatives_port import (
    DerivativesPort,
    FuturesContract,
    ContractType,
    DerivativesPosition,
    MarginStatus,
    MarginType,
    HedgeOrder,
    HedgeType,
    HedgeRecommendation,
    FundingAnalysis,
    DerivativesSummary,
)
from src.omnix.infrastructure.adapters.derivatives_adapter import DerivativesAdapter


class TestDerivativesEnums:
    """Test derivatives-related enums."""
    
    def test_contract_types(self):
        assert ContractType.PERPETUAL.value == "perpetual"
        assert ContractType.QUARTERLY.value == "quarterly"
        assert ContractType.MONTHLY.value == "monthly"
        assert ContractType.WEEKLY.value == "weekly"
        assert ContractType.OPTION_CALL.value == "option_call"
        assert ContractType.OPTION_PUT.value == "option_put"
    
    def test_hedge_types(self):
        assert HedgeType.DELTA_NEUTRAL.value == "delta_neutral"
        assert HedgeType.PROTECTIVE_PUT.value == "protective_put"
        assert HedgeType.COVERED_CALL.value == "covered_call"
        assert HedgeType.COLLAR.value == "collar"
        assert HedgeType.INVERSE.value == "inverse"
    
    def test_margin_types(self):
        assert MarginType.ISOLATED.value == "isolated"
        assert MarginType.CROSS.value == "cross"


class TestFuturesContract:
    """Test FuturesContract DTO."""
    
    def test_futures_contract_creation(self):
        contract = FuturesContract(
            symbol="BTC-PERP",
            contract_type=ContractType.PERPETUAL,
            underlying="BTC",
            mark_price=50000.0,
            index_price=49900.0,
            funding_rate=0.0001,
            open_interest=100000000,
            volume_24h=500000000
        )
        
        assert contract.symbol == "BTC-PERP"
        assert contract.is_perpetual is True
        assert contract.premium_pct > 0
    
    def test_non_perpetual_contract(self):
        contract = FuturesContract(
            symbol="BTC-DEC25",
            contract_type=ContractType.QUARTERLY,
            underlying="BTC",
            expiry=datetime(2025, 12, 31)
        )
        
        assert contract.is_perpetual is False


class TestMarginStatus:
    """Test MarginStatus DTO."""
    
    def test_margin_status_safe(self):
        status = MarginStatus(
            total_collateral_usd=100000,
            available_margin_usd=60000,
            used_margin_usd=40000,
            maintenance_margin_usd=20000,
            margin_ratio=60.0,
            account_leverage=2.5,
            liquidation_risk=10.0
        )
        
        assert status.is_safe is True
        assert status.is_critical is False
    
    def test_margin_status_critical(self):
        status = MarginStatus(
            total_collateral_usd=100000,
            available_margin_usd=15000,
            used_margin_usd=85000,
            maintenance_margin_usd=80000,
            margin_ratio=15.0,
            account_leverage=6.7,
            liquidation_risk=85.0
        )
        
        assert status.is_safe is False
        assert status.is_critical is True


class TestDerivativesPosition:
    """Test DerivativesPosition DTO."""
    
    def test_profitable_position(self):
        position = DerivativesPosition(
            symbol="ETH-PERP",
            contract_type=ContractType.PERPETUAL,
            side="long",
            size=10.0,
            size_usd=35000,
            entry_price=3000.0,
            mark_price=3500.0,
            unrealized_pnl=5000.0,
            unrealized_pnl_pct=16.67
        )
        
        assert position.is_profitable is True
    
    def test_losing_position(self):
        position = DerivativesPosition(
            symbol="ETH-PERP",
            contract_type=ContractType.PERPETUAL,
            side="long",
            size=10.0,
            size_usd=30000,
            entry_price=3000.0,
            mark_price=2800.0,
            unrealized_pnl=-2000.0,
            unrealized_pnl_pct=-6.67
        )
        
        assert position.is_profitable is False


class TestHedgeOrder:
    """Test HedgeOrder DTO."""
    
    def test_hedge_order_balanced(self):
        hedge = HedgeOrder(
            hedge_id="H001",
            hedge_type=HedgeType.DELTA_NEUTRAL,
            spot_symbol="BTC/USD",
            hedge_symbol="BTC-PERP",
            spot_size_usd=50000,
            hedge_size_usd=50000,
            hedge_ratio=1.0,
            entry_price=50000,
            target_delta=0.0,
            current_delta=0.05,
            status="active"
        )
        
        assert hedge.is_balanced is True
    
    def test_hedge_order_unbalanced(self):
        hedge = HedgeOrder(
            hedge_id="H002",
            hedge_type=HedgeType.DELTA_NEUTRAL,
            spot_symbol="BTC/USD",
            hedge_symbol="BTC-PERP",
            spot_size_usd=50000,
            hedge_size_usd=40000,
            hedge_ratio=0.8,
            entry_price=50000,
            target_delta=0.0,
            current_delta=0.25,
            status="active"
        )
        
        assert hedge.is_balanced is False


class TestDerivativesAdapter:
    """Test DerivativesAdapter implementation."""
    
    def test_adapter_initialization(self):
        adapter = DerivativesAdapter()
        
        assert adapter._derivatives_manager is None
        assert adapter._futures_client is None
        assert adapter._hedging_service is None
        assert adapter._margin_engine is None
        assert adapter._initialized is False
    
    def test_adapter_with_injected_services(self):
        mock_manager = Mock()
        mock_client = Mock()
        
        adapter = DerivativesAdapter(
            derivatives_manager=mock_manager,
            futures_client=mock_client
        )
        
        assert adapter._derivatives_manager == mock_manager
        assert adapter._futures_client == mock_client
    
    def test_contract_type_mapping(self):
        adapter = DerivativesAdapter()
        
        assert adapter._map_contract_type("perpetual") == ContractType.PERPETUAL
        assert adapter._map_contract_type("quarterly") == ContractType.QUARTERLY
        assert adapter._map_contract_type("call") == ContractType.OPTION_CALL
    
    def test_hedge_type_mapping(self):
        adapter = DerivativesAdapter()
        
        assert adapter._map_hedge_type("delta_neutral") == HedgeType.DELTA_NEUTRAL
        assert adapter._map_hedge_type("protective_put") == HedgeType.PROTECTIVE_PUT
        assert adapter._map_hedge_type("covered_call") == HedgeType.COVERED_CALL
    
    def test_margin_type_mapping(self):
        adapter = DerivativesAdapter()
        
        assert adapter._map_margin_type("isolated") == MarginType.ISOLATED
        assert adapter._map_margin_type("cross") == MarginType.CROSS
    
    def test_health_check_no_services(self):
        adapter = DerivativesAdapter()
        health = adapter.health_check()
        
        assert 'healthy' in health
        assert 'adapter' in health
        assert health['adapter'] == 'DerivativesAdapter'
        assert 'components' in health
    
    def test_get_margin_status_fallback(self):
        adapter = DerivativesAdapter()
        
        result = adapter.get_margin_status()
        
        assert isinstance(result, MarginStatus)
        assert result.margin_ratio == 100
    
    def test_get_derivatives_summary(self):
        adapter = DerivativesAdapter()
        
        result = adapter.get_derivatives_summary()
        
        assert isinstance(result, DerivativesSummary)
        assert result.total_positions >= 0
    
    def test_calculate_hedge_requirement(self):
        adapter = DerivativesAdapter()
        
        result = adapter.calculate_hedge_requirement(
            spot_symbol="BTC/USD",
            spot_size_usd=50000,
            target_delta=0.0
        )
        
        assert isinstance(result, HedgeRecommendation)
    
    def test_is_derivatives_available(self):
        adapter = DerivativesAdapter()
        
        is_available, reason = adapter.is_derivatives_available()
        
        assert isinstance(is_available, bool)
        assert isinstance(reason, str)


class TestDerivativesPortProtocol:
    """Test that DerivativesAdapter implements DerivativesPort protocol."""
    
    def test_adapter_has_required_methods(self):
        adapter = DerivativesAdapter()
        
        required_methods = [
            'get_futures_contracts',
            'get_contract_info',
            'get_derivatives_positions',
            'get_margin_status',
            'calculate_hedge_requirement',
            'execute_hedge',
            'get_active_hedges',
            'rebalance_hedge',
            'analyze_funding_rates',
            'get_derivatives_summary',
            'set_leverage',
            'set_margin_type',
            'is_derivatives_available',
            'health_check',
        ]
        
        for method_name in required_methods:
            assert hasattr(adapter, method_name), f"Missing method: {method_name}"
            assert callable(getattr(adapter, method_name)), f"Not callable: {method_name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
