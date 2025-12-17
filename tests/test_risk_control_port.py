"""
OMNIX V7.0 - RiskControlPort Tests
===================================
Unit tests for RiskControlPort and RiskControlAdapter.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from src.omnix.ports.driven.risk_control_port import (
    RiskControlPort,
    RiskAssessmentRequest,
    RiskDecision,
    RiskLevel,
    CircuitBreakEvent,
    CircuitBreakerState,
    LimitStatus,
    LimitType,
    PositionRisk,
    PortfolioRiskSummary,
    Alert,
    AlertPriority,
)
from src.omnix.infrastructure.adapters.risk_control_adapter import RiskControlAdapter


class TestRiskEnums:
    """Test risk-related enums."""
    
    def test_risk_levels(self):
        assert RiskLevel.MINIMAL.value == "minimal"
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MODERATE.value == "moderate"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"
        assert RiskLevel.EXTREME.value == "extreme"
    
    def test_circuit_breaker_states(self):
        assert CircuitBreakerState.CLOSED.value == "closed"
        assert CircuitBreakerState.OPEN.value == "open"
        assert CircuitBreakerState.HALF_OPEN.value == "half_open"
    
    def test_alert_priorities(self):
        assert AlertPriority.DEBUG.value == "debug"
        assert AlertPriority.INFO.value == "info"
        assert AlertPriority.WARNING.value == "warning"
        assert AlertPriority.ERROR.value == "error"
        assert AlertPriority.CRITICAL.value == "critical"
    
    def test_limit_types(self):
        assert LimitType.POSITION_SIZE.value == "position_size"
        assert LimitType.DAILY_LOSS.value == "daily_loss"
        assert LimitType.DRAWDOWN.value == "drawdown"


class TestRiskDecision:
    """Test RiskDecision DTO."""
    
    def test_risk_decision_creation(self):
        decision = RiskDecision(
            approved=True,
            risk_level=RiskLevel.LOW,
            score=25.0,
            reasons=["Position within limits"],
            warnings=["Near daily loss limit"]
        )
        
        assert decision.approved is True
        assert decision.risk_level == RiskLevel.LOW
        assert decision.score == 25.0
        assert decision.is_blocked is False
        assert decision.is_high_risk is False
    
    def test_risk_decision_high_risk(self):
        decision = RiskDecision(
            approved=False,
            risk_level=RiskLevel.CRITICAL,
            score=85.0,
            veto_source="DrawdownGuard"
        )
        
        assert decision.is_blocked is True
        assert decision.is_high_risk is True


class TestCircuitBreakEvent:
    """Test CircuitBreakEvent DTO."""
    
    def test_circuit_break_event_creation(self):
        event = CircuitBreakEvent(
            breaker_id="main",
            state=CircuitBreakerState.OPEN,
            trigger_reason="Daily loss exceeded",
            triggered_at=datetime.now(),
            affected_symbols=["BTC", "ETH"]
        )
        
        assert event.breaker_id == "main"
        assert event.is_active is True
    
    def test_circuit_break_closed(self):
        event = CircuitBreakEvent(
            breaker_id="test",
            state=CircuitBreakerState.CLOSED,
            trigger_reason="",
            triggered_at=datetime.now()
        )
        
        assert event.is_active is False


class TestLimitStatus:
    """Test LimitStatus DTO."""
    
    def test_limit_status_creation(self):
        status = LimitStatus(
            limit_type=LimitType.POSITION_SIZE,
            limit_value=50000,
            current_value=35000,
            utilization_pct=70.0,
            is_breached=False,
            headroom=15000
        )
        
        assert status.limit_type == LimitType.POSITION_SIZE
        assert status.is_near_limit is False
    
    def test_limit_near_threshold(self):
        status = LimitStatus(
            limit_type=LimitType.DAILY_LOSS,
            limit_value=1000,
            current_value=850,
            utilization_pct=85.0,
            is_breached=False,
            headroom=150
        )
        
        assert status.is_near_limit is True


class TestRiskControlAdapter:
    """Test RiskControlAdapter implementation."""
    
    def test_adapter_initialization(self):
        adapter = RiskControlAdapter()
        
        assert adapter._circuit_breaker is None
        assert adapter._limits_engine is None
        assert adapter._position_monitor is None
        assert adapter._alert_dispatcher is None
        assert adapter._initialized is False
    
    def test_adapter_with_injected_services(self):
        mock_cb = Mock()
        mock_limits = Mock()
        
        adapter = RiskControlAdapter(
            circuit_breaker=mock_cb,
            limits_engine=mock_limits
        )
        
        assert adapter._circuit_breaker == mock_cb
        assert adapter._limits_engine == mock_limits
    
    def test_risk_level_mapping(self):
        adapter = RiskControlAdapter()
        
        assert adapter._map_risk_level(5) == RiskLevel.MINIMAL
        assert adapter._map_risk_level(15) == RiskLevel.LOW
        assert adapter._map_risk_level(35) == RiskLevel.MODERATE
        assert adapter._map_risk_level(60) == RiskLevel.HIGH
        assert adapter._map_risk_level(80) == RiskLevel.CRITICAL
        assert adapter._map_risk_level(95) == RiskLevel.EXTREME
    
    def test_circuit_state_mapping(self):
        adapter = RiskControlAdapter()
        
        assert adapter._map_circuit_state("open") == CircuitBreakerState.OPEN
        assert adapter._map_circuit_state("closed") == CircuitBreakerState.CLOSED
        assert adapter._map_circuit_state("half_open") == CircuitBreakerState.HALF_OPEN
    
    def test_health_check_no_services(self):
        adapter = RiskControlAdapter()
        health = adapter.health_check()
        
        assert 'healthy' in health
        assert 'adapter' in health
        assert health['adapter'] == 'RiskControlAdapter'
        assert 'components' in health
    
    def test_assess_trade_risk_fallback(self):
        adapter = RiskControlAdapter()
        
        request = RiskAssessmentRequest(
            symbol="BTC/USD",
            side="buy",
            size_usd=10000
        )
        
        result = adapter.assess_trade_risk(request)
        
        assert isinstance(result, RiskDecision)
        assert result.approved is True
        assert result.risk_level == RiskLevel.MODERATE
    
    def test_is_trading_allowed(self):
        adapter = RiskControlAdapter()
        
        is_allowed, reason = adapter.is_trading_allowed()
        
        assert isinstance(is_allowed, bool)
        assert isinstance(reason, str)
    
    def test_dispatch_alert(self):
        adapter = RiskControlAdapter()
        
        alert = adapter.dispatch_alert(
            priority=AlertPriority.WARNING,
            category="risk",
            title="Test Alert",
            message="This is a test"
        )
        
        assert isinstance(alert, Alert)
        assert alert.priority == AlertPriority.WARNING
        assert alert.title == "Test Alert"
    
    def test_get_recent_alerts(self):
        adapter = RiskControlAdapter()
        
        adapter.dispatch_alert(
            priority=AlertPriority.INFO,
            category="test",
            title="Alert 1",
            message="Message 1"
        )
        
        alerts = adapter.get_recent_alerts(hours=1)
        
        assert len(alerts) >= 1


class TestRiskControlPortProtocol:
    """Test that RiskControlAdapter implements RiskControlPort protocol."""
    
    def test_adapter_has_required_methods(self):
        adapter = RiskControlAdapter()
        
        required_methods = [
            'assess_trade_risk',
            'get_circuit_breaker_status',
            'trip_circuit_breaker',
            'reset_circuit_breaker',
            'get_limit_status',
            'check_limits',
            'get_position_risks',
            'get_portfolio_risk_summary',
            'dispatch_alert',
            'get_recent_alerts',
            'acknowledge_alert',
            'is_trading_allowed',
            'health_check',
        ]
        
        for method_name in required_methods:
            assert hasattr(adapter, method_name), f"Missing method: {method_name}"
            assert callable(getattr(adapter, method_name)), f"Not callable: {method_name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
