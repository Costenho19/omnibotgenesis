"""
OMNIX V7.0 Phase 3b Integration Tests
======================================
Tests for Flask App Factory and Telegram Adapter integration.

Run with: pytest tests/test_phase3b_integration.py -v
"""

import pytest
import logging
from unittest.mock import Mock, patch, AsyncMock

logger = logging.getLogger(__name__)


class TestFlaskAppFactory:
    """Tests for Flask App Factory with DI Container."""
    
    def test_create_app_returns_flask_instance(self):
        """Test that create_app returns a Flask application."""
        from src.omnix.interfaces.flask_app import create_app
        
        app = create_app()
        
        assert app is not None
        assert hasattr(app, 'config')
        assert 'CONTAINER' in app.config
    
    def test_create_app_with_custom_container(self):
        """Test that create_app accepts custom container."""
        from src.omnix.interfaces.flask_app import create_app
        from src.omnix.bootstrap.container import Container
        
        container = Container.create()
        app = create_app(container=container)
        
        assert app.config['CONTAINER'] is container
    
    def test_health_endpoint(self):
        """Test health endpoint returns healthy status."""
        from src.omnix.interfaces.flask_app import create_app
        
        app = create_app()
        client = app.test_client()
        
        response = client.get('/health')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert 'use_app_layer' in data
    
    def test_health_detailed_endpoint(self):
        """Test detailed health endpoint returns container status."""
        from src.omnix.interfaces.flask_app import create_app
        
        app = create_app()
        client = app.test_client()
        
        response = client.get('/health/detailed')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert 'container' in data
    
    def test_container_status_endpoint(self):
        """Test container status API endpoint."""
        from src.omnix.interfaces.flask_app import create_app
        
        app = create_app()
        client = app.test_client()
        
        response = client.get('/api/container/status')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'database' in data
        assert 'cache' in data
        assert 'use_app_layer' in data


class TestTelegramPort:
    """Tests for Telegram Port definitions."""
    
    def test_telegram_message_dataclass(self):
        """Test TelegramMessage dataclass fields."""
        from src.omnix.application.ports.telegram_port import TelegramMessage
        
        msg = TelegramMessage(
            chat_id=123456,
            user_id=789,
            username="testuser",
            text="Hello",
            message_id=1,
            is_command=True,
            command="start",
            command_args="arg1"
        )
        
        assert msg.chat_id == 123456
        assert msg.user_id == 789
        assert msg.username == "testuser"
        assert msg.text == "Hello"
        assert msg.message_id == 1
        assert msg.is_command is True
        assert msg.command == "start"
        assert msg.command_args == "arg1"
    
    def test_telegram_response_dataclass(self):
        """Test TelegramResponse dataclass fields."""
        from src.omnix.application.ports.telegram_port import TelegramResponse
        
        response = TelegramResponse(
            chat_id=123456,
            text="Response text",
            parse_mode="HTML",
            reply_to_message_id=5,
            reply_markup={"inline_keyboard": []}
        )
        
        assert response.chat_id == 123456
        assert response.text == "Response text"
        assert response.parse_mode == "HTML"
        assert response.reply_to_message_id == 5
        assert response.reply_markup == {"inline_keyboard": []}
    
    def test_telegram_response_defaults(self):
        """Test TelegramResponse default values."""
        from src.omnix.application.ports.telegram_port import TelegramResponse
        
        response = TelegramResponse(
            chat_id=123456,
            text="Simple response"
        )
        
        assert response.parse_mode == "HTML"
        assert response.reply_to_message_id is None
        assert response.reply_markup is None


class TestTelegramBotAdapter:
    """Tests for TelegramBotAdapter."""
    
    def test_adapter_initialization_without_bot(self):
        """Test adapter initializes gracefully when bot unavailable."""
        with patch('src.omnix.infrastructure.adapters.telegram_adapter.TelegramBotAdapter._initialize_bot') as mock_init:
            mock_init.return_value = None
            
            from src.omnix.infrastructure.adapters.telegram_adapter import TelegramBotAdapter
            adapter = TelegramBotAdapter()
            
            assert adapter is not None
    
    def test_health_check_returns_dict(self):
        """Test health_check returns proper structure."""
        with patch('src.omnix.infrastructure.adapters.telegram_adapter.TelegramBotAdapter._initialize_bot'):
            from src.omnix.infrastructure.adapters.telegram_adapter import TelegramBotAdapter
            adapter = TelegramBotAdapter()
            adapter._is_initialized = False
            adapter._bot = None
            
            health = adapter.health_check()
            
            assert isinstance(health, dict)
            assert 'initialized' in health
            assert 'running' in health
            assert 'has_bot' in health
            assert 'has_application' in health
    
    def test_is_running_when_not_initialized(self):
        """Test is_running returns False when not initialized."""
        with patch('src.omnix.infrastructure.adapters.telegram_adapter.TelegramBotAdapter._initialize_bot'):
            from src.omnix.infrastructure.adapters.telegram_adapter import TelegramBotAdapter
            adapter = TelegramBotAdapter()
            adapter._is_initialized = False
            adapter._bot = None
            
            assert adapter.is_running() is False
    
    @pytest.mark.asyncio
    async def test_start_returns_false_when_not_initialized(self):
        """Test start returns False when bot not initialized."""
        with patch('src.omnix.infrastructure.adapters.telegram_adapter.TelegramBotAdapter._initialize_bot'):
            from src.omnix.infrastructure.adapters.telegram_adapter import TelegramBotAdapter
            adapter = TelegramBotAdapter()
            adapter._is_initialized = False
            adapter._bot = None
            
            result = await adapter.start()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_stop_returns_true_when_not_initialized(self):
        """Test stop returns True when bot not initialized (nothing to stop)."""
        with patch('src.omnix.infrastructure.adapters.telegram_adapter.TelegramBotAdapter._initialize_bot'):
            from src.omnix.infrastructure.adapters.telegram_adapter import TelegramBotAdapter
            adapter = TelegramBotAdapter()
            adapter._is_initialized = False
            adapter._bot = None
            
            result = await adapter.stop()
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_send_message_returns_false_when_not_initialized(self):
        """Test send_message returns False when not initialized."""
        with patch('src.omnix.infrastructure.adapters.telegram_adapter.TelegramBotAdapter._initialize_bot'):
            from src.omnix.infrastructure.adapters.telegram_adapter import TelegramBotAdapter
            adapter = TelegramBotAdapter()
            adapter._is_initialized = False
            adapter._bot = None
            
            result = await adapter.send_message(
                chat_id=123456,
                text="Test message"
            )
            
            assert result is False


class TestContainerIntegration:
    """Tests for Container with new Phase 3b adapters."""
    
    def test_container_has_telegram_adapter_property(self):
        """Test container has telegram_adapter property."""
        from src.omnix.bootstrap.container import Container
        
        container = Container.create()
        
        assert hasattr(container, 'telegram_adapter')
    
    def test_container_has_database_manager_property(self):
        """Test container has database_manager property."""
        from src.omnix.bootstrap.container import Container
        
        container = Container.create()
        
        assert hasattr(container, 'database_manager')
    
    def test_container_health_check_includes_new_adapters(self):
        """Test container health_check includes telegram and database_manager status."""
        from src.omnix.bootstrap.container import Container
        
        container = Container.create()
        health = container.health_check()
        
        assert 'telegram_adapter' in health
        assert 'database_manager' in health


class TestMainBootstrapSelector:
    """Tests for main.py USE_APP_LAYER selector."""
    
    def test_use_app_layer_flag_is_defined(self):
        """Test USE_APP_LAYER flag is readable from env_config."""
        from omnix_config import env_config
        
        result = env_config.get('USE_APP_LAYER', default='false', cast_type=bool)
        
        assert isinstance(result, bool)
        assert result is False
    
    def test_container_get_container_function(self):
        """Test get_container returns container instance."""
        from src.omnix.bootstrap.container import get_container, reset_container
        
        reset_container()
        container = get_container()
        
        assert container is not None
        
        container2 = get_container()
        assert container is container2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
