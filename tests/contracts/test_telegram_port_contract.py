"""
OMNIX TelegramPort Contract Tests
==================================
Phase 4D: Contract tests ensuring TelegramBotAdapter implements ITelegramBot.

All ITelegramBot implementations MUST pass these tests.
"""

import pytest
import asyncio
from typing import Protocol, Optional, Dict, Any, Callable, Awaitable, runtime_checkable
from dataclasses import dataclass
from unittest.mock import MagicMock, AsyncMock, patch


@runtime_checkable
class TelegramBotPort(Protocol):
    """Contract for Telegram bot operations."""
    
    async def start(self) -> bool:
        ...
    
    async def stop(self) -> bool:
        ...
    
    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: Optional[Dict[str, Any]] = None,
    ) -> bool:
        ...
    
    async def send_voice(
        self,
        chat_id: int,
        voice_data: bytes,
        caption: Optional[str] = None,
    ) -> bool:
        ...
    
    def is_running(self) -> bool:
        ...
    
    def health_check(self) -> Dict[str, Any]:
        ...


class MockUpdater:
    """Mock PTB v20+ Updater for testing."""
    
    def __init__(self):
        self.running = False
    
    async def start_polling(self):
        self.running = True
    
    async def stop(self):
        self.running = False


class MockApplication:
    """Mock PTB v20+ Application for testing."""
    
    def __init__(self):
        self.bot = AsyncMock()
        self.bot.send_message = AsyncMock(return_value=True)
        self.bot.send_voice = AsyncMock(return_value=True)
        self.bot.edit_message_text = AsyncMock(return_value=True)
        self.bot.answer_callback_query = AsyncMock(return_value=True)
        self.add_handler = MagicMock()
        self.updater = MockUpdater()
        self.running = False
        self._initialized = False
    
    async def initialize(self):
        self._initialized = True
    
    async def start(self):
        self.running = True
    
    async def stop(self):
        self.running = False
    
    async def shutdown(self):
        self._initialized = False


class MockTelegramBot:
    """Mock EnterpriseTelegramBot for testing."""
    
    def __init__(self, db_manager=None):
        self.application = MockApplication()
        self.is_running = True
        self._handlers = []
    
    async def start(self):
        return True
    
    async def stop(self):
        return True
    
    def run(self):
        pass


class MockCacheAdapter:
    """Mock CacheAdapter for session storage testing."""
    
    def __init__(self):
        self._store: Dict[str, Any] = {}
        self._connected = True
    
    def is_connected(self) -> bool:
        return self._connected
    
    def get_json(self, key: str) -> Optional[Dict]:
        return self._store.get(key)
    
    def set_json(self, key: str, value: Dict, ttl_seconds: int = 300) -> bool:
        self._store[key] = value
        return True
    
    def delete(self, key: str) -> bool:
        self._store.pop(key, None)
        return True


@pytest.fixture
def mock_bot():
    """Create mock Telegram bot."""
    return MockTelegramBot()


@pytest.fixture
def mock_cache():
    """Create mock cache adapter."""
    return MockCacheAdapter()


@pytest.fixture
def adapter(mock_bot, mock_cache):
    """Create TelegramBotAdapter with mocked dependencies."""
    with patch('src.omnix.infrastructure.adapters.telegram_adapter.TelegramBotAdapter._initialize_bot'):
        from src.omnix.infrastructure.adapters.telegram_adapter import TelegramBotAdapter, UserSessionManager
        
        adapter = TelegramBotAdapter()
        adapter._bot = mock_bot
        adapter._is_initialized = True
        adapter._session_manager = UserSessionManager(cache_adapter=mock_cache)
        return adapter


class TestTelegramPortContract:
    """Contract tests for ITelegramBot implementations."""
    
    def test_has_start_method(self, adapter):
        """Adapter must have async start method."""
        assert hasattr(adapter, 'start')
        assert asyncio.iscoroutinefunction(adapter.start)
    
    def test_has_stop_method(self, adapter):
        """Adapter must have async stop method."""
        assert hasattr(adapter, 'stop')
        assert asyncio.iscoroutinefunction(adapter.stop)
    
    def test_has_send_message_method(self, adapter):
        """Adapter must have async send_message method."""
        assert hasattr(adapter, 'send_message')
        assert asyncio.iscoroutinefunction(adapter.send_message)
    
    def test_has_send_voice_method(self, adapter):
        """Adapter must have async send_voice method."""
        assert hasattr(adapter, 'send_voice')
        assert asyncio.iscoroutinefunction(adapter.send_voice)
    
    def test_has_is_running_method(self, adapter):
        """Adapter must have is_running method."""
        assert hasattr(adapter, 'is_running')
        assert callable(adapter.is_running)
    
    def test_has_health_check_method(self, adapter):
        """Adapter must have health_check method."""
        assert hasattr(adapter, 'health_check')
        assert callable(adapter.health_check)
    
    def test_has_register_command_handler_method(self, adapter):
        """Adapter must have register_command_handler method."""
        assert hasattr(adapter, 'register_command_handler')
        assert callable(adapter.register_command_handler)
    
    def test_has_register_message_handler_method(self, adapter):
        """Adapter must have register_message_handler method."""
        assert hasattr(adapter, 'register_message_handler')
        assert callable(adapter.register_message_handler)
    
    def test_has_register_callback_handler_method(self, adapter):
        """Adapter must have register_callback_handler method."""
        assert hasattr(adapter, 'register_callback_handler')
        assert callable(adapter.register_callback_handler)


class TestTelegramBotAdapterOperations:
    """Test TelegramBotAdapter core operations."""
    
    @pytest.mark.asyncio
    async def test_send_message_returns_bool(self, adapter):
        """send_message must return bool."""
        result = await adapter.send_message(
            chat_id=123456,
            text="Test message"
        )
        assert isinstance(result, bool)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_send_voice_returns_bool(self, adapter):
        """send_voice must return bool."""
        result = await adapter.send_voice(
            chat_id=123456,
            voice_data=b"test audio data"
        )
        assert isinstance(result, bool)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_edit_message_returns_bool(self, adapter):
        """edit_message must return bool."""
        result = await adapter.edit_message(
            chat_id=123456,
            message_id=789,
            text="Edited message"
        )
        assert isinstance(result, bool)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_answer_callback_query_returns_bool(self, adapter):
        """answer_callback_query must return bool."""
        result = await adapter.answer_callback_query(
            callback_query_id="query123"
        )
        assert isinstance(result, bool)
        assert result is True
    
    def test_is_running_returns_bool(self, adapter):
        """is_running must return bool."""
        result = adapter.is_running()
        assert isinstance(result, bool)
    
    def test_health_check_returns_dict(self, adapter):
        """health_check must return status dictionary."""
        health = adapter.health_check()
        assert isinstance(health, dict)
        assert 'healthy' in health
        assert 'initialized' in health
        assert 'running' in health


class TestUserSessionManager:
    """Test UserSessionManager for state isolation."""
    
    @pytest.fixture
    def session_manager(self, mock_cache):
        from src.omnix.infrastructure.adapters.telegram_adapter import UserSessionManager
        return UserSessionManager(cache_adapter=mock_cache)
    
    def test_get_session_creates_new(self, session_manager):
        """get_session must create new session for unknown user."""
        session = session_manager.get_session(user_id=12345, chat_id=67890)
        assert session is not None
        assert session.user_id == 12345
        assert session.chat_id == 67890
    
    def test_get_session_returns_existing(self, session_manager):
        """get_session must return existing session."""
        session1 = session_manager.get_session(user_id=12345, chat_id=67890)
        session2 = session_manager.get_session(user_id=12345, chat_id=67890)
        assert session1 is session2
    
    def test_save_session_persists_state(self, session_manager):
        """save_session must persist session state."""
        from src.omnix.infrastructure.adapters.telegram_adapter import ConversationState
        
        session = session_manager.get_session(user_id=12345, chat_id=67890)
        session.set_state(ConversationState.AWAITING_CONFIRMATION, {"action": "buy"})
        
        result = session_manager.save_session(session)
        assert result is True
    
    def test_delete_session_removes_session(self, session_manager):
        """delete_session must remove session."""
        session_manager.get_session(user_id=12345, chat_id=67890)
        result = session_manager.delete_session(user_id=12345)
        assert result is True
    
    def test_get_active_sessions_count(self, session_manager):
        """get_active_sessions_count must return int."""
        session_manager.get_session(user_id=111, chat_id=1)
        session_manager.get_session(user_id=222, chat_id=2)
        
        count = session_manager.get_active_sessions_count()
        assert isinstance(count, int)
        assert count == 2


class TestUserSession:
    """Test UserSession dataclass."""
    
    def test_session_creation(self):
        """UserSession must be creatable with required fields."""
        from src.omnix.infrastructure.adapters.telegram_adapter import UserSession, ConversationState
        
        session = UserSession(user_id=123, chat_id=456)
        assert session.user_id == 123
        assert session.chat_id == 456
        assert session.state == ConversationState.IDLE
        assert session.context_data == {}
    
    def test_session_update_activity(self):
        """update_activity must update last_activity timestamp."""
        from src.omnix.infrastructure.adapters.telegram_adapter import UserSession
        
        session = UserSession(user_id=123, chat_id=456)
        assert session.last_activity is None
        
        session.update_activity()
        assert session.last_activity is not None
    
    def test_session_set_state(self):
        """set_state must transition state and update context."""
        from src.omnix.infrastructure.adapters.telegram_adapter import UserSession, ConversationState
        
        session = UserSession(user_id=123, chat_id=456)
        session.set_state(ConversationState.AWAITING_SYMBOL, {"symbol": "BTC"})
        
        assert session.state == ConversationState.AWAITING_SYMBOL
        assert session.context_data["symbol"] == "BTC"
    
    def test_session_reset(self):
        """reset must return to IDLE state and clear context."""
        from src.omnix.infrastructure.adapters.telegram_adapter import UserSession, ConversationState
        
        session = UserSession(user_id=123, chat_id=456)
        session.set_state(ConversationState.PROCESSING, {"data": "test"})
        session.pending_action = "buy"
        
        session.reset()
        
        assert session.state == ConversationState.IDLE
        assert session.context_data == {}
        assert session.pending_action is None


class TestConversationState:
    """Test ConversationState enum."""
    
    def test_all_states_defined(self):
        """All conversation states must be defined."""
        from src.omnix.infrastructure.adapters.telegram_adapter import ConversationState
        
        assert hasattr(ConversationState, 'IDLE')
        assert hasattr(ConversationState, 'AWAITING_CONFIRMATION')
        assert hasattr(ConversationState, 'AWAITING_INPUT')
        assert hasattr(ConversationState, 'AWAITING_SYMBOL')
        assert hasattr(ConversationState, 'AWAITING_AMOUNT')
        assert hasattr(ConversationState, 'PROCESSING')
    
    def test_states_have_string_values(self):
        """All states must have string values."""
        from src.omnix.infrastructure.adapters.telegram_adapter import ConversationState
        
        for state in ConversationState:
            assert isinstance(state.value, str)


class TestTelegramBotAdapterTelemetry:
    """Test telemetry tracking in TelegramBotAdapter."""
    
    def test_initial_telemetry_zero(self, adapter):
        """Initial telemetry counters should be zero."""
        assert adapter._request_count == 0
        assert adapter._message_count == 0
        assert adapter._command_count == 0
        assert adapter._callback_count == 0
        assert adapter._error_count == 0
    
    @pytest.mark.asyncio
    async def test_send_message_increments_counters(self, adapter):
        """send_message should increment telemetry counters."""
        await adapter.send_message(chat_id=123, text="Test")
        
        assert adapter._request_count == 1
        assert adapter._message_count == 1
    
    @pytest.mark.asyncio
    async def test_answer_callback_increments_counters(self, adapter):
        """answer_callback_query should increment callback counter."""
        await adapter.answer_callback_query(callback_query_id="test123")
        
        assert adapter._request_count == 1
        assert adapter._callback_count == 1
    
    def test_health_check_includes_telemetry(self, adapter):
        """Health check should include telemetry metrics."""
        health = adapter.health_check()
        
        assert 'request_count' in health
        assert 'message_count' in health
        assert 'command_count' in health
        assert 'callback_count' in health
        assert 'error_count' in health
        assert 'avg_latency_ms' in health
        assert 'error_rate_pct' in health
        assert 'active_sessions' in health
    
    def test_health_check_does_not_inflate_telemetry(self, adapter):
        """health_check must NOT inflate telemetry counters."""
        initial_count = adapter._request_count
        
        adapter.health_check()
        adapter.health_check()
        adapter.health_check()
        
        assert adapter._request_count == initial_count


class TestTelegramBotAdapterGracefulDegradation:
    """Test graceful degradation when bot unavailable."""
    
    @pytest.fixture
    def adapter_no_bot(self):
        """Create adapter without initialized bot."""
        with patch('src.omnix.infrastructure.adapters.telegram_adapter.TelegramBotAdapter._initialize_bot'):
            from src.omnix.infrastructure.adapters.telegram_adapter import TelegramBotAdapter
            
            adapter = TelegramBotAdapter()
            adapter._bot = None
            adapter._is_initialized = False
            return adapter
    
    @pytest.mark.asyncio
    async def test_send_message_returns_false_no_bot(self, adapter_no_bot):
        """send_message should return False when bot unavailable."""
        result = await adapter_no_bot.send_message(chat_id=123, text="Test")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_voice_returns_false_no_bot(self, adapter_no_bot):
        """send_voice should return False when bot unavailable."""
        result = await adapter_no_bot.send_voice(chat_id=123, voice_data=b"test")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_start_returns_false_no_bot(self, adapter_no_bot):
        """start should return False when bot unavailable."""
        result = await adapter_no_bot.start()
        assert result is False
    
    def test_is_running_returns_false_no_bot(self, adapter_no_bot):
        """is_running should return False when bot unavailable."""
        assert adapter_no_bot.is_running() is False
    
    def test_health_check_shows_unhealthy(self, adapter_no_bot):
        """health_check should show unhealthy when bot unavailable."""
        health = adapter_no_bot.health_check()
        assert health['healthy'] is False
        assert health['initialized'] is False


class TestSessionManagerRedisIntegration:
    """Test UserSessionManager Redis integration."""
    
    def test_session_stored_in_redis(self, mock_cache):
        """Session should be stored in Redis when available."""
        from src.omnix.infrastructure.adapters.telegram_adapter import UserSessionManager, ConversationState
        
        manager = UserSessionManager(cache_adapter=mock_cache)
        session = manager.get_session(user_id=999, chat_id=888)
        session.set_state(ConversationState.AWAITING_INPUT)
        manager.save_session(session)
        
        key = f"omnix:telegram:session:999"
        assert key in mock_cache._store
        stored = mock_cache._store[key]
        assert stored['user_id'] == 999
        assert stored['state'] == 'awaiting_input'
    
    def test_session_falls_back_to_local(self):
        """Session should fall back to local storage when Redis unavailable."""
        from src.omnix.infrastructure.adapters.telegram_adapter import UserSessionManager
        
        manager = UserSessionManager(cache_adapter=None)
        session = manager.get_session(user_id=123, chat_id=456)
        
        assert session is not None
        assert 123 in manager._local_sessions


class TestTelegramBotAdapterLifecycle:
    """Test async lifecycle management for PTB v20+ compliance."""
    
    @pytest.mark.asyncio
    async def test_start_initializes_application(self, adapter):
        """start() should properly initialize PTB Application."""
        result = await adapter.start()
        assert result is True
        assert adapter._bot.application._initialized is True
        assert adapter._bot.application.running is True
    
    @pytest.mark.asyncio
    async def test_start_starts_updater_polling(self, adapter):
        """start() should start updater polling and set running=True."""
        await adapter.start()
        assert adapter._bot.application.updater.running is True
    
    @pytest.mark.asyncio
    async def test_stop_shuts_down_application(self, adapter):
        """stop() should properly shutdown PTB Application."""
        await adapter.start()
        assert adapter._bot.application.updater.running is True
        
        result = await adapter.stop()
        assert result is True
        assert adapter._bot.application.updater.running is False
    
    @pytest.mark.asyncio
    async def test_start_stop_lifecycle(self, adapter):
        """Full start/stop lifecycle should work correctly."""
        assert await adapter.start() is True
        assert adapter._bot.application.running is True
        assert adapter._bot.application.updater.running is True
        
        assert await adapter.stop() is True
        assert adapter._bot.application.updater.running is False
    
    @pytest.mark.asyncio
    async def test_start_returns_false_when_not_initialized(self):
        """start() should return False if bot not initialized."""
        with patch('src.omnix.infrastructure.adapters.telegram_adapter.TelegramBotAdapter._initialize_bot'):
            from src.omnix.infrastructure.adapters.telegram_adapter import TelegramBotAdapter
            
            adapter = TelegramBotAdapter()
            adapter._bot = None
            adapter._is_initialized = False
            
            result = await adapter.start()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_stop_stops_updater_when_running(self, adapter):
        """stop() should call updater.stop() when updater is running."""
        await adapter.start()
        assert adapter._bot.application.updater.running is True
        
        await adapter.stop()
        assert adapter._bot.application.updater.running is False
    
    @pytest.mark.asyncio
    async def test_stop_returns_true_when_not_initialized(self):
        """stop() should return True when bot not initialized (idempotent)."""
        with patch('src.omnix.infrastructure.adapters.telegram_adapter.TelegramBotAdapter._initialize_bot'):
            from src.omnix.infrastructure.adapters.telegram_adapter import TelegramBotAdapter
            
            adapter = TelegramBotAdapter()
            adapter._bot = None
            adapter._is_initialized = False
            
            result = await adapter.stop()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_is_running_reflects_lifecycle_state(self, adapter):
        """is_running() should reflect True after start, False after stop."""
        assert adapter.is_running() is False
        
        await adapter.start()
        assert adapter.is_running() is True
        
        await adapter.stop()
        assert adapter.is_running() is False
    
    @pytest.mark.asyncio
    async def test_health_check_running_reflects_lifecycle(self, adapter):
        """health_check 'running' should reflect lifecycle state."""
        health_before = adapter.health_check()
        assert health_before['running'] is False
        
        await adapter.start()
        health_running = adapter.health_check()
        assert health_running['running'] is True
        
        await adapter.stop()
        health_stopped = adapter.health_check()
        assert health_stopped['running'] is False
    
    @pytest.mark.asyncio
    async def test_start_failure_keeps_is_running_false(self, mock_cache):
        """start() failure should keep is_running=False."""
        with patch('src.omnix.infrastructure.adapters.telegram_adapter.TelegramBotAdapter._initialize_bot'):
            from src.omnix.infrastructure.adapters.telegram_adapter import TelegramBotAdapter, UserSessionManager
            
            adapter = TelegramBotAdapter()
            adapter._is_initialized = True
            
            failing_app = MagicMock()
            failing_app.initialize = AsyncMock(side_effect=Exception("Init failed"))
            
            mock_bot = MagicMock()
            mock_bot.application = failing_app
            adapter._bot = mock_bot
            adapter._session_manager = UserSessionManager(cache_adapter=mock_cache)
            
            result = await adapter.start()
            assert result is False
            assert adapter.is_running() is False
    
    @pytest.mark.asyncio
    async def test_start_updater_failure_keeps_is_running_false(self, mock_cache):
        """start() with updater failure should keep is_running=False."""
        with patch('src.omnix.infrastructure.adapters.telegram_adapter.TelegramBotAdapter._initialize_bot'):
            from src.omnix.infrastructure.adapters.telegram_adapter import TelegramBotAdapter, UserSessionManager
            
            adapter = TelegramBotAdapter()
            adapter._is_initialized = True
            
            failing_updater = MagicMock()
            failing_updater.start_polling = AsyncMock(side_effect=Exception("Polling failed"))
            
            failing_app = MagicMock()
            failing_app.initialize = AsyncMock()
            failing_app.start = AsyncMock()
            failing_app.updater = failing_updater
            
            mock_bot = MagicMock()
            mock_bot.application = failing_app
            adapter._bot = mock_bot
            adapter._session_manager = UserSessionManager(cache_adapter=mock_cache)
            
            result = await adapter.start()
            assert result is False
            assert adapter.is_running() is False
    
    @pytest.mark.asyncio
    async def test_stop_failure_keeps_is_running_true(self, mock_cache):
        """stop() failure should keep is_running=True to reflect actual state."""
        with patch('src.omnix.infrastructure.adapters.telegram_adapter.TelegramBotAdapter._initialize_bot'):
            from src.omnix.infrastructure.adapters.telegram_adapter import TelegramBotAdapter, UserSessionManager
            
            adapter = TelegramBotAdapter()
            adapter._is_initialized = True
            adapter._is_running = True
            
            failing_updater = MagicMock()
            failing_updater.running = True
            failing_updater.stop = AsyncMock(side_effect=Exception("Stop failed"))
            
            failing_app = MagicMock()
            failing_app.updater = failing_updater
            failing_app.running = True
            
            mock_bot = MagicMock()
            mock_bot.application = failing_app
            adapter._bot = mock_bot
            adapter._session_manager = UserSessionManager(cache_adapter=mock_cache)
            
            result = await adapter.stop()
            assert result is False
            assert adapter.is_running() is True
