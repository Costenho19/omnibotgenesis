"""
OMNIX NotificationPort Contract Tests
======================================
Phase 4A: Contract tests ensuring NotificationAdapter implements NotificationPort.

All NotificationPort implementations MUST pass these tests.
"""

import pytest
from typing import Protocol, runtime_checkable
from unittest.mock import AsyncMock, MagicMock, patch


@runtime_checkable
class NotificationPort(Protocol):
    """Contract for notification operations."""
    
    async def send_message(
        self,
        recipient_id: str,
        message: str,
        parse_mode: str = 'HTML'
    ) -> bool:
        ...
    
    async def send_trade_alert(
        self,
        recipient_id: str,
        trade_data: dict
    ) -> bool:
        ...


class MockTelegramAdapter:
    """Mock TelegramBotAdapter for testing."""
    
    def __init__(self):
        self.sent_messages = []
        self._is_initialized = True
    
    async def send_message(self, chat_id: int, text: str, parse_mode: str = "HTML") -> bool:
        self.sent_messages.append({
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        })
        return True
    
    def health_check(self):
        return {'initialized': True, 'running': True}


class TestNotificationPortContract:
    """Contract tests for NotificationPort implementations."""
    
    @pytest.fixture
    def mock_telegram_adapter(self):
        return MockTelegramAdapter()
    
    @pytest.fixture
    def adapter(self, mock_telegram_adapter):
        from src.omnix.infrastructure.adapters.notification_adapter import NotificationAdapter
        return NotificationAdapter(telegram_adapter=mock_telegram_adapter)
    
    def test_implements_protocol(self, adapter):
        """NotificationAdapter must implement NotificationPort protocol."""
        assert isinstance(adapter, NotificationPort)
    
    def test_has_send_message_method(self, adapter):
        """Adapter must have async send_message method."""
        assert hasattr(adapter, 'send_message')
        assert callable(adapter.send_message)
    
    def test_has_send_trade_alert_method(self, adapter):
        """Adapter must have async send_trade_alert method."""
        assert hasattr(adapter, 'send_trade_alert')
        assert callable(adapter.send_trade_alert)
    
    @pytest.mark.asyncio
    async def test_send_message_returns_bool(self, adapter, mock_telegram_adapter):
        """send_message must return bool."""
        result = await adapter.send_message(
            recipient_id="123456",
            message="Test message",
            parse_mode="HTML"
        )
        assert isinstance(result, bool)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_send_message_accepts_required_params(self, adapter, mock_telegram_adapter):
        """send_message must accept recipient_id and message."""
        result = await adapter.send_message(
            recipient_id="123456",
            message="Hello World"
        )
        assert result is True
        assert len(mock_telegram_adapter.sent_messages) == 1
        assert mock_telegram_adapter.sent_messages[0]['chat_id'] == 123456
        assert mock_telegram_adapter.sent_messages[0]['text'] == "Hello World"
    
    @pytest.mark.asyncio
    async def test_send_message_default_parse_mode(self, adapter, mock_telegram_adapter):
        """send_message default parse_mode should be 'HTML'."""
        await adapter.send_message(recipient_id="123456", message="Test")
        assert mock_telegram_adapter.sent_messages[0]['parse_mode'] == "HTML"
    
    @pytest.mark.asyncio
    async def test_send_trade_alert_returns_bool(self, adapter, mock_telegram_adapter):
        """send_trade_alert must return bool."""
        result = await adapter.send_trade_alert(
            recipient_id="123456",
            trade_data={
                'symbol': 'BTC/USD',
                'side': 'BUY',
                'amount': 0.5,
                'price': 45000.00
            }
        )
        assert isinstance(result, bool)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_send_trade_alert_formats_message(self, adapter, mock_telegram_adapter):
        """send_trade_alert must format trade data into message."""
        await adapter.send_trade_alert(
            recipient_id="123456",
            trade_data={
                'symbol': 'BTC/USD',
                'side': 'BUY',
                'amount': 0.5,
                'price': 45000.00
            }
        )
        assert len(mock_telegram_adapter.sent_messages) == 1
        text = mock_telegram_adapter.sent_messages[0]['text']
        assert 'BTC/USD' in text
        assert 'BUY' in text
        assert '45,000.00' in text
    
    @pytest.mark.asyncio
    async def test_send_message_handles_empty_message(self, adapter, mock_telegram_adapter):
        """send_message should handle empty messages gracefully."""
        result = await adapter.send_message(recipient_id="123456", message="")
        assert result is True
        assert len(mock_telegram_adapter.sent_messages) == 0
    
    @pytest.mark.asyncio
    async def test_send_message_handles_invalid_recipient(self, adapter):
        """send_message should return False for invalid recipient_id."""
        result = await adapter.send_message(
            recipient_id="invalid",
            message="Test"
        )
        assert result is False
    
    def test_health_check_returns_dict(self, adapter):
        """health_check must return status dictionary."""
        health = adapter.health_check()
        assert isinstance(health, dict)
        assert 'healthy' in health
        assert 'telegram_adapter_available' in health


class TestNotificationAdapterTelemetry:
    """Test telemetry tracking in NotificationAdapter."""
    
    @pytest.fixture
    def mock_telegram_adapter(self):
        return MockTelegramAdapter()
    
    @pytest.fixture
    def adapter(self, mock_telegram_adapter):
        from src.omnix.infrastructure.adapters.notification_adapter import NotificationAdapter
        return NotificationAdapter(telegram_adapter=mock_telegram_adapter)
    
    @pytest.mark.asyncio
    async def test_request_count_increments(self, adapter, mock_telegram_adapter):
        """Request count should increment on each call."""
        assert adapter._request_count == 0
        
        await adapter.send_message(recipient_id="123", message="Test 1")
        assert adapter._request_count == 1
        
        await adapter.send_message(recipient_id="123", message="Test 2")
        assert adapter._request_count == 2
    
    @pytest.mark.asyncio
    async def test_success_count_increments(self, adapter, mock_telegram_adapter):
        """Success count should increment on successful sends."""
        await adapter.send_message(recipient_id="123", message="Test")
        assert adapter._success_count == 1
    
    @pytest.mark.asyncio
    async def test_health_check_includes_telemetry(self, adapter, mock_telegram_adapter):
        """Health check should include telemetry metrics."""
        await adapter.send_message(recipient_id="123", message="Test")
        
        health = adapter.health_check()
        assert health['request_count'] == 1
        assert health['success_count'] == 1
        assert health['success_rate_pct'] == 100.0
        assert health['last_request'] is not None


class TestNotificationAdapterMessageSplitting:
    """Test message splitting for Telegram limits."""
    
    @pytest.fixture
    def mock_telegram_adapter(self):
        return MockTelegramAdapter()
    
    @pytest.fixture
    def adapter(self, mock_telegram_adapter):
        from src.omnix.infrastructure.adapters.notification_adapter import NotificationAdapter
        return NotificationAdapter(telegram_adapter=mock_telegram_adapter)
    
    @pytest.mark.asyncio
    async def test_short_message_not_split(self, adapter, mock_telegram_adapter):
        """Short messages should be sent as single message."""
        await adapter.send_message(recipient_id="123", message="Short message")
        assert len(mock_telegram_adapter.sent_messages) == 1
    
    @pytest.mark.asyncio
    async def test_long_message_gets_split(self, adapter, mock_telegram_adapter):
        """Messages exceeding limit should be split."""
        long_message = "A" * 5000
        await adapter.send_message(recipient_id="123", message=long_message)
        assert len(mock_telegram_adapter.sent_messages) >= 2


class TestNotificationAdapterTradeAlertFormatting:
    """Test trade alert message formatting."""
    
    @pytest.fixture
    def mock_telegram_adapter(self):
        return MockTelegramAdapter()
    
    @pytest.fixture
    def adapter(self, mock_telegram_adapter):
        from src.omnix.infrastructure.adapters.notification_adapter import NotificationAdapter
        return NotificationAdapter(telegram_adapter=mock_telegram_adapter)
    
    @pytest.mark.asyncio
    async def test_buy_alert_has_green_emoji(self, adapter, mock_telegram_adapter):
        """BUY alerts should use green emoji."""
        await adapter.send_trade_alert(
            recipient_id="123",
            trade_data={'symbol': 'BTC/USD', 'side': 'BUY', 'amount': 1, 'price': 50000}
        )
        text = mock_telegram_adapter.sent_messages[0]['text']
        assert "🟢" in text
    
    @pytest.mark.asyncio
    async def test_sell_alert_has_red_emoji(self, adapter, mock_telegram_adapter):
        """SELL alerts should use red emoji."""
        await adapter.send_trade_alert(
            recipient_id="123",
            trade_data={'symbol': 'BTC/USD', 'side': 'SELL', 'amount': 1, 'price': 50000}
        )
        text = mock_telegram_adapter.sent_messages[0]['text']
        assert "🔴" in text
    
    @pytest.mark.asyncio
    async def test_profit_loss_included_when_present(self, adapter, mock_telegram_adapter):
        """P/L should be included when provided."""
        await adapter.send_trade_alert(
            recipient_id="123",
            trade_data={
                'symbol': 'BTC/USD',
                'side': 'SELL',
                'amount': 1,
                'price': 55000,
                'profit_loss': 5000,
                'profit_loss_pct': 10.0
            }
        )
        text = mock_telegram_adapter.sent_messages[0]['text']
        assert "P/L" in text
        assert "5,000.00" in text
        assert "+10.00%" in text
    
    @pytest.mark.asyncio
    async def test_reason_included_when_present(self, adapter, mock_telegram_adapter):
        """Trade reason should be included when provided."""
        await adapter.send_trade_alert(
            recipient_id="123",
            trade_data={
                'symbol': 'BTC/USD',
                'side': 'BUY',
                'amount': 1,
                'price': 50000,
                'reason': 'RSI oversold signal'
            }
        )
        text = mock_telegram_adapter.sent_messages[0]['text']
        assert "RSI oversold signal" in text
