"""
Tests for Price Stale Detection and Admin Alerts
OMNIX V6.5.4d INSTITUTIONAL+

Tests:
1. Price freshness validation (fresh, warning, stale)
2. Trading blocked on stale prices
3. Admin alerts triggered on stale events
4. Cooldown prevents alert spam
"""

import time
import pytest
from unittest.mock import Mock, patch, MagicMock

from omnix_services.market_data.validators import (
    MarketDataValidator,
    PriceDataState,
    PriceFreshness,
    StaleCheckConfig,
    validate_price_freshness,
    is_price_tradeable,
    get_market_data_validator
)


class TestPriceFreshness:
    """Test price freshness detection"""
    
    def setup_method(self):
        MarketDataValidator._instance = None
    
    def test_fresh_price_is_tradeable(self):
        """Price fetched just now should be fresh and tradeable"""
        config = StaleCheckConfig(
            stale_threshold_seconds=30.0,
            warning_threshold_seconds=20.0
        )
        validator = MarketDataValidator(config=config)
        
        current_time = time.time()
        state = validator.validate_price(
            symbol="BTC/USD",
            price=95000.0,
            fetch_timestamp=current_time - 5.0,
            source="Kraken"
        )
        
        assert state.freshness == PriceFreshness.FRESH
        assert state.is_tradeable is True
        assert state.age_seconds < 10
    
    def test_warning_price_still_tradeable(self):
        """Price approaching stale threshold should show warning but still tradeable"""
        config = StaleCheckConfig(
            stale_threshold_seconds=30.0,
            warning_threshold_seconds=20.0
        )
        validator = MarketDataValidator(config=config)
        
        current_time = time.time()
        state = validator.validate_price(
            symbol="ETH/USD",
            price=3500.0,
            fetch_timestamp=current_time - 25.0,
            source="Kraken"
        )
        
        assert state.freshness == PriceFreshness.WARNING
        assert state.is_tradeable is True
        assert 20 <= state.age_seconds < 30
    
    def test_stale_price_blocks_trading(self):
        """Price older than threshold should be stale and block trading"""
        config = StaleCheckConfig(
            stale_threshold_seconds=30.0,
            warning_threshold_seconds=20.0,
            block_trading_on_stale=True
        )
        validator = MarketDataValidator(config=config)
        
        current_time = time.time()
        state = validator.validate_price(
            symbol="SOL/USD",
            price=125.0,
            fetch_timestamp=current_time - 45.0,
            source="Kraken"
        )
        
        assert state.freshness == PriceFreshness.STALE
        assert state.is_tradeable is False
        assert state.age_seconds >= 30
        assert "stale" in state.reason.lower() or "old" in state.reason.lower()
    
    def test_stale_price_allows_trading_when_disabled(self):
        """Stale price should allow trading when block_trading_on_stale is False"""
        config = StaleCheckConfig(
            stale_threshold_seconds=30.0,
            block_trading_on_stale=False
        )
        validator = MarketDataValidator(config=config)
        
        current_time = time.time()
        state = validator.validate_price(
            symbol="ADA/USD",
            price=0.45,
            fetch_timestamp=current_time - 60.0,
            source="Kraken"
        )
        
        assert state.freshness == PriceFreshness.STALE
        assert state.is_tradeable is True
    
    def test_disabled_validator_always_fresh(self):
        """When validator is disabled, all prices should be fresh"""
        config = StaleCheckConfig(enabled=False)
        validator = MarketDataValidator(config=config)
        
        current_time = time.time()
        state = validator.validate_price(
            symbol="BTC/USD",
            price=95000.0,
            fetch_timestamp=current_time - 1000.0,
            source="Kraken"
        )
        
        assert state.freshness == PriceFreshness.FRESH
        assert state.is_tradeable is True


class TestAdminAlerts:
    """Test admin alert functionality"""
    
    def setup_method(self):
        MarketDataValidator._instance = None
    
    def test_stale_event_triggers_callback(self):
        """Stale price should trigger admin alert callback"""
        callback_mock = Mock()
        
        config = StaleCheckConfig(stale_threshold_seconds=30.0)
        validator = MarketDataValidator(config=config, admin_alert_callback=callback_mock)
        
        current_time = time.time()
        validator.validate_price(
            symbol="BTC/USD",
            price=95000.0,
            fetch_timestamp=current_time - 45.0,
            source="Kraken"
        )
        
        assert callback_mock.called
        call_args = callback_mock.call_args
        assert call_args.kwargs["event_type"] == "price_stale"
        assert "BTC/USD" in call_args.kwargs["title"]
    
    def test_cooldown_prevents_spam(self):
        """Multiple stale events should not spam alerts (cooldown)"""
        callback_mock = Mock()
        
        config = StaleCheckConfig(stale_threshold_seconds=30.0)
        validator = MarketDataValidator(config=config, admin_alert_callback=callback_mock)
        validator._alert_cooldown_seconds = 60
        
        current_time = time.time()
        
        validator.validate_price("BTC/USD", 95000.0, current_time - 45.0)
        validator.validate_price("BTC/USD", 95100.0, current_time - 46.0)
        validator.validate_price("BTC/USD", 95200.0, current_time - 47.0)
        
        assert callback_mock.call_count == 1
    
    def test_stale_stats_tracking(self):
        """Validator should track stale event statistics"""
        config = StaleCheckConfig(stale_threshold_seconds=30.0)
        validator = MarketDataValidator(config=config)
        
        current_time = time.time()
        
        validator._alert_cooldown_seconds = 0
        
        validator.validate_price("BTC/USD", 95000.0, current_time - 45.0)
        validator.validate_price("ETH/USD", 3500.0, current_time - 50.0)
        validator.validate_price("BTC/USD", 95100.0, current_time - 46.0)
        
        stats = validator.get_stale_stats()
        
        assert stats["total_stale_events"] == 3
        assert stats["stale_event_counts"]["BTC/USD"] == 2
        assert stats["stale_event_counts"]["ETH/USD"] == 1


class TestAlertDispatcherIntegration:
    """Test AlertDispatcher admin alert functionality"""
    
    def test_add_admin_chat_id(self):
        """Should be able to add admin chat IDs"""
        from omnix_services.risk_management.alert_dispatcher import AlertDispatcher
        
        AlertDispatcher._instance = None
        dispatcher = AlertDispatcher()
        
        dispatcher.add_admin_chat_id("123456789")
        dispatcher.add_admin_chat_id("987654321")
        dispatcher.add_admin_chat_id("123456789")
        
        assert len(dispatcher._admin_chat_ids) == 2
        assert "123456789" in dispatcher._admin_chat_ids
        assert "987654321" in dispatcher._admin_chat_ids
    
    def test_admin_alert_cooldown(self):
        """Admin alerts should respect cooldown by event type"""
        from omnix_services.risk_management.alert_dispatcher import AlertDispatcher
        from omnix_services.risk_management.risk_models import RiskSeverity
        
        AlertDispatcher._instance = None
        dispatcher = AlertDispatcher()
        dispatcher._admin_cooldown_seconds = 60
        
        result1 = dispatcher.send_admin_alert_sync(
            event_type="price_stale",
            severity=RiskSeverity.WARNING,
            title="Test Alert 1",
            message="First alert"
        )
        
        result2 = dispatcher.send_admin_alert_sync(
            event_type="price_stale",
            severity=RiskSeverity.WARNING,
            title="Test Alert 2",
            message="Should be blocked by cooldown"
        )
        
        result3 = dispatcher.send_admin_alert_sync(
            event_type="redis_down",
            severity=RiskSeverity.CRITICAL,
            title="Different Event",
            message="Different event type, should work"
        )
        
        assert result1 is True
        assert result2 is False
        assert result3 is True


class TestHelperFunctions:
    """Test module-level helper functions"""
    
    def setup_method(self):
        MarketDataValidator._instance = None
    
    def test_validate_price_freshness_function(self):
        """Test the validate_price_freshness helper function"""
        current_time = time.time()
        
        state = validate_price_freshness(
            symbol="BTC/USD",
            price=95000.0,
            fetch_timestamp=current_time - 5.0,
            source="Kraken"
        )
        
        assert isinstance(state, PriceDataState)
        assert state.symbol == "BTC/USD"
        assert state.price == 95000.0
    
    def test_is_price_tradeable_function(self):
        """Test the is_price_tradeable helper function"""
        current_time = time.time()
        
        is_fresh = is_price_tradeable(
            symbol="BTC/USD",
            price=95000.0,
            fetch_timestamp=current_time - 5.0
        )
        
        assert is_fresh is True
        
        is_stale = is_price_tradeable(
            symbol="BTC/USD",
            price=95000.0,
            fetch_timestamp=current_time - 60.0
        )
        
        assert is_stale is False
