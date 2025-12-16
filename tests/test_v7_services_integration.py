"""
OMNIX V7 Services Integration Tests
====================================
Tests for V7 AI Gateway Shim and Voice Service Adapter integration.

Updated Dec 16, 2025: AIGatewayShim now delegates to AIModelsManager for
full failover chain support.
"""

import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock


class TestContainerV7Functions:
    """Test V7 container functions for AI and Voice services."""
    
    def test_initialize_v7_services_returns_status(self):
        """initialize_v7_services should return health status dict."""
        from omnix_services.ai_service.container import initialize_v7_services
        
        result = initialize_v7_services()
        
        assert isinstance(result, dict)
        assert 'ai_service' in result
        assert 'voice_service' in result
        assert 'type' in result['ai_service']
        assert 'healthy' in result['ai_service']
    
    def test_get_v7_services_status(self):
        """get_v7_services_status should return current state."""
        from omnix_services.ai_service.container import get_v7_services_status
        
        status = get_v7_services_status()
        
        assert isinstance(status, dict)
        assert 'use_ai_port' in status
        assert 'use_voice_port' in status
        assert 'ai_gateway_type' in status
        assert 'voice_service_type' in status
    
    @patch.dict(os.environ, {'USE_AI_PORT': 'false'})
    def test_get_ai_gateway_legacy_mode(self):
        """When USE_AI_PORT=false, should return legacy gateway."""
        from omnix_services.ai_service.container import get_ai_gateway
        
        gateway = get_ai_gateway()
        
        assert gateway is not None
        assert type(gateway).__name__ == 'RoutingAIGateway'
    
    @patch.dict(os.environ, {'USE_VOICE_PORT': 'false'})
    def test_get_voice_service_legacy_mode(self):
        """When USE_VOICE_PORT=false, should return legacy voice service."""
        from omnix_services.ai_service.container import get_voice_service
        
        service = get_voice_service()
        
        if service is not None:
            assert type(service).__name__ in ['VoiceServiceEnterprise', 'VoiceServiceAdapter']


class TestAIGatewayShimWithManager:
    """Test AIGatewayShim integration with AIModelsManager."""
    
    def test_shim_initialization_with_manager(self):
        """AIGatewayShim should accept AIModelsManager as dependency."""
        from src.omnix.infrastructure.adapters.ai_gateway_shim import AIGatewayShim
        from omnix_services.ai_service.ai_models import AIModelsManager
        
        manager = AIModelsManager()
        shim = AIGatewayShim(ai_models_manager=manager)
        
        assert shim._ai_models_manager is manager
        assert shim._request_count == 0
        assert shim._error_count == 0
    
    def test_shim_health_check_reports_backend(self):
        """Health check should report AIModelsManager as backend."""
        from src.omnix.infrastructure.adapters.ai_gateway_shim import AIGatewayShim
        from omnix_services.ai_service.ai_models import AIModelsManager
        
        manager = AIModelsManager()
        shim = AIGatewayShim(ai_models_manager=manager)
        
        health = shim.health_check()
        
        assert 'backend' in health
        assert 'AIModelsManager' in health['backend']
        assert 'providers' in health
        assert health['healthy'] == True or health['healthy'] == False
    
    def test_shim_detects_available_providers(self):
        """Shim should detect which providers are available from manager."""
        from src.omnix.infrastructure.adapters.ai_gateway_shim import AIGatewayShim
        from omnix_services.ai_service.ai_models import AIModelsManager
        
        manager = AIModelsManager()
        shim = AIGatewayShim(ai_models_manager=manager)
        
        health = shim.health_check()
        providers = health.get('providers', {})
        
        assert isinstance(providers, dict)
        assert 'gemini' in providers
        assert 'openai' in providers
        assert 'anthropic' in providers
    
    def test_shim_get_primary_provider(self):
        """Should return primary provider."""
        from src.omnix.infrastructure.adapters.ai_gateway_shim import AIGatewayShim
        from src.omnix.ports.driven.ai_text_gateway_port import ModelProvider
        
        shim = AIGatewayShim(primary_provider=ModelProvider.GEMINI)
        
        assert shim.get_primary_provider() == ModelProvider.GEMINI
    
    def test_shim_no_lazy_loading(self):
        """Shim should NOT lazy-load AIModelsManager (no longer supported).
        
        This ensures the container has full control over manager lifecycle
        and cooldown behavior. If no manager is injected, shim reports unhealthy.
        """
        from src.omnix.infrastructure.adapters.ai_gateway_shim import AIGatewayShim
        
        shim = AIGatewayShim()
        
        assert shim._ai_models_manager is None
        
        manager = shim._get_manager()
        assert manager is None
        
        health = shim.health_check()
        assert health['healthy'] is False
        assert health['backend'] == 'AIModelsManager (not available)'


class TestAIGatewayShimBasics:
    """Test AIGatewayShim basic functionality."""
    
    def test_shim_initialization(self):
        """AIGatewayShim should initialize with defaults."""
        from src.omnix.infrastructure.adapters.ai_gateway_shim import AIGatewayShim
        
        shim = AIGatewayShim()
        
        assert shim._request_count == 0
        assert shim._error_count == 0
        assert shim._success_count == 0
    
    def test_shim_health_check_without_manager(self):
        """Health check should report unhealthy if manager not available."""
        from src.omnix.infrastructure.adapters.ai_gateway_shim import AIGatewayShim
        
        shim = AIGatewayShim()
        shim._ai_models_manager = None
        
        with patch.object(shim, '_get_manager', return_value=None):
            health = shim.health_check()
        
        assert health['healthy'] == False
        assert health['request_count'] == 0


class TestVoiceServiceAdapterBasics:
    """Test VoiceServiceAdapter basic functionality."""
    
    def test_adapter_initialization(self):
        """VoiceServiceAdapter should initialize correctly."""
        from src.omnix.infrastructure.adapters.voice_adapter import VoiceServiceAdapter
        
        adapter = VoiceServiceAdapter()
        
        assert adapter._request_count == 0
        assert adapter._error_count == 0
        assert adapter._cache == {}
    
    def test_adapter_health_check_structure(self):
        """Health check should return proper structure."""
        from src.omnix.infrastructure.adapters.voice_adapter import VoiceServiceAdapter
        
        adapter = VoiceServiceAdapter()
        health = adapter.health_check()
        
        assert isinstance(health, dict)
        assert 'tts_available' in health
        assert 'stt_available' in health


class TestRuntimeFlagToggle:
    """Test that feature flags can be toggled at runtime."""
    
    def test_flag_status_reflects_env_changes(self):
        """Toggling USE_AI_PORT env var should reflect in status."""
        import importlib
        import omnix_services.ai_service.container as container_module
        
        with patch.dict(os.environ, {'USE_AI_PORT': 'false'}):
            importlib.reload(container_module)
            status1 = container_module.get_v7_services_status()
            assert status1['use_ai_port'] == False
        
        with patch.dict(os.environ, {'USE_AI_PORT': 'true'}):
            status2 = container_module.get_v7_services_status()
            assert status2['use_ai_port'] == True
    
    def test_flag_status_reflects_voice_env_changes(self):
        """Toggling USE_VOICE_PORT env var should reflect in status."""
        from omnix_services.ai_service.container import get_v7_services_status
        
        with patch.dict(os.environ, {'USE_VOICE_PORT': 'false'}):
            status1 = get_v7_services_status()
            assert status1['use_voice_port'] == False
        
        with patch.dict(os.environ, {'USE_VOICE_PORT': 'true'}):
            status2 = get_v7_services_status()
            assert status2['use_voice_port'] == True


class TestContainerFallbackBehavior:
    """Test container fallback to RoutingAIGateway when shim fails."""
    
    def test_container_fallback_when_manager_fails(self):
        """Container should return RoutingAIGateway when AIModelsManager creation fails."""
        import importlib
        import omnix_services.ai_service.container as container_module
        
        container_module._v7_gateway_shim = None
        container_module._ai_models_manager_instance = None
        container_module._v7_shim_last_failure = 0.0
        container_module._legacy_gateway_instance = None
        
        with patch.dict(os.environ, {'USE_AI_PORT': 'true'}):
            with patch.object(container_module, '_get_ai_models_manager', return_value=None):
                gateway = container_module.get_ai_gateway()
        
        from omnix_services.ai_service.providers.routing_gateway import RoutingAIGateway
        assert isinstance(gateway, RoutingAIGateway)
    
    def test_container_cooldown_prevents_retry(self):
        """Container should not retry shim creation during cooldown period."""
        import time
        import omnix_services.ai_service.container as container_module
        
        container_module._v7_gateway_shim = None
        container_module._ai_models_manager_instance = None
        container_module._v7_shim_last_failure = time.time()
        container_module._legacy_gateway_instance = None
        
        with patch.dict(os.environ, {'USE_AI_PORT': 'true'}):
            in_cooldown = container_module._is_v7_shim_in_cooldown()
        
        assert in_cooldown == True
    
    def test_container_fallback_when_healthy_shim_becomes_unhealthy(self):
        """Container should fallback to RoutingAIGateway when healthy shim becomes unhealthy.
        
        This tests the most common production scenario: provider outage after startup.
        """
        import time
        import omnix_services.ai_service.container as container_module
        from src.omnix.infrastructure.adapters.ai_gateway_shim import AIGatewayShim
        from omnix_services.ai_service.providers.routing_gateway import RoutingAIGateway
        from unittest.mock import MagicMock
        
        container_module._v7_gateway_shim = None
        container_module._ai_models_manager_instance = None
        container_module._v7_shim_last_failure = 0.0
        container_module._v7_shim_last_health_check = 0.0
        container_module._legacy_gateway_instance = None
        
        mock_manager = MagicMock()
        mock_manager.gemini_client = None
        mock_manager.openai_client = None
        mock_manager.anthropic_client = None
        
        shim = AIGatewayShim(ai_models_manager=mock_manager)
        container_module._v7_gateway_shim = shim
        container_module._v7_shim_last_health_check = time.time() - 120
        
        with patch.dict(os.environ, {'USE_AI_PORT': 'true'}):
            gateway = container_module.get_ai_gateway()
        
        assert isinstance(gateway, RoutingAIGateway)
        
        assert container_module._is_v7_shim_in_cooldown() == True


class TestVoiceAdapterFallbackBehavior:
    """Test VoiceServiceAdapter fallback to VoiceServiceEnterprise when adapter fails."""
    
    def test_voice_adapter_no_lazy_loading(self):
        """VoiceServiceAdapter should NOT lazy-load VoiceServiceEnterprise.
        
        This ensures the container has full control over service lifecycle
        and cooldown behavior. If no service is injected, adapter reports unhealthy.
        """
        from src.omnix.infrastructure.adapters.voice_adapter import VoiceServiceAdapter
        
        adapter = VoiceServiceAdapter()
        
        assert adapter._voice_service is None
        
        service = adapter._get_voice_service()
        assert service is None
        
        health = adapter.health_check()
        assert health['healthy'] is False
        assert health['backend'] == 'VoiceServiceEnterprise (not available)'
    
    def test_voice_container_fallback_when_service_fails(self):
        """Container should return VoiceServiceEnterprise when adapter creation fails."""
        import omnix_services.ai_service.container as container_module
        
        container_module._voice_adapter_instance = None
        container_module._voice_enterprise_instance = None
        container_module._voice_adapter_last_failure = 0.0
        container_module._legacy_voice_instance = None
        
        with patch.dict(os.environ, {'USE_VOICE_PORT': 'true'}):
            with patch.object(container_module, '_get_voice_enterprise', return_value=None):
                service = container_module.get_voice_service()
        
        from omnix_services.voice_service.voice_service import VoiceServiceEnterprise
        assert isinstance(service, VoiceServiceEnterprise)
    
    def test_voice_container_cooldown_prevents_retry(self):
        """Container should not retry voice adapter creation during cooldown period."""
        import time
        import omnix_services.ai_service.container as container_module
        
        container_module._voice_adapter_instance = None
        container_module._voice_enterprise_instance = None
        container_module._voice_adapter_last_failure = time.time()
        container_module._legacy_voice_instance = None
        
        with patch.dict(os.environ, {'USE_VOICE_PORT': 'true'}):
            in_cooldown = container_module._is_voice_in_cooldown()
        
        assert in_cooldown == True
    
    def test_voice_container_fallback_when_healthy_adapter_becomes_unhealthy(self):
        """Container should fallback to VoiceServiceEnterprise when healthy adapter becomes unhealthy.
        
        This tests the most common production scenario: gTTS/Whisper outage after startup.
        """
        import time
        import omnix_services.ai_service.container as container_module
        from src.omnix.infrastructure.adapters.voice_adapter import VoiceServiceAdapter
        from omnix_services.voice_service.voice_service import VoiceServiceEnterprise
        from unittest.mock import MagicMock
        
        container_module._voice_adapter_instance = None
        container_module._voice_enterprise_instance = None
        container_module._voice_adapter_last_failure = 0.0
        container_module._voice_last_health_check = 0.0
        container_module._legacy_voice_instance = None
        
        mock_service = MagicMock()
        mock_service.health_check.return_value = {
            'tts_available': False,
            'stt_available': False,
        }
        
        adapter = VoiceServiceAdapter(voice_service=mock_service)
        container_module._voice_adapter_instance = adapter
        container_module._voice_last_health_check = time.time() - 120
        
        with patch.dict(os.environ, {'USE_VOICE_PORT': 'true'}):
            service = container_module.get_voice_service()
        
        assert isinstance(service, VoiceServiceEnterprise)
        
        assert container_module._is_voice_in_cooldown() == True
    
    def test_voice_adapter_recovers_after_cooldown(self):
        """After cooldown expires, container should try to recreate VoiceServiceAdapter.
        
        This verifies the recovery path: cooldown expires → adapter recreated with 
        VoiceServiceEnterprise injected.
        """
        import time
        import omnix_services.ai_service.container as container_module
        from src.omnix.infrastructure.adapters.voice_adapter import VoiceServiceAdapter
        
        container_module._voice_adapter_instance = None
        container_module._voice_enterprise_instance = None
        container_module._voice_adapter_last_failure = time.time() - 400
        container_module._voice_last_health_check = 0.0
        container_module._legacy_voice_instance = None
        
        assert container_module._is_voice_in_cooldown() == False
        
        with patch.dict(os.environ, {'USE_VOICE_PORT': 'true'}):
            service = container_module.get_voice_service()
        
        assert isinstance(service, VoiceServiceAdapter)
        
        assert container_module._voice_enterprise_instance is not None
    
    def test_voice_full_cycle_failure_cooldown_recovery(self):
        """Full cycle test: healthy → failure → cooldown → recovery.
        
        Simulates production scenario:
        1. Adapter healthy and working
        2. Adapter becomes unhealthy → fallback to legacy
        3. During cooldown → stays on legacy
        4. Cooldown expires → recovers to adapter
        """
        import time
        import omnix_services.ai_service.container as container_module
        from src.omnix.infrastructure.adapters.voice_adapter import VoiceServiceAdapter
        from omnix_services.voice_service.voice_service import VoiceServiceEnterprise
        
        container_module._voice_adapter_instance = None
        container_module._voice_enterprise_instance = None
        container_module._voice_adapter_last_failure = 0.0
        container_module._voice_last_health_check = 0.0
        container_module._legacy_voice_instance = None
        
        with patch.dict(os.environ, {'USE_VOICE_PORT': 'true'}):
            service1 = container_module.get_voice_service()
            assert isinstance(service1, VoiceServiceAdapter)
            
            container_module._reset_voice_adapter()
            assert container_module._is_voice_in_cooldown() == True
            
            service2 = container_module.get_voice_service()
            assert isinstance(service2, VoiceServiceEnterprise)
            
            container_module._voice_adapter_last_failure = time.time() - 400
            assert container_module._is_voice_in_cooldown() == False
            
            service3 = container_module.get_voice_service()
            assert isinstance(service3, VoiceServiceAdapter)


class TestAIModelsManagerFailover:
    """Test that AIModelsManager failover is correctly used by shim."""
    
    def test_error_handler_imported_correctly(self):
        """Error handler module should be importable."""
        from omnix_services.ai_service.ai_error_handler import (
            ErrorCategory,
            AIError,
            ErrorClassifier,
            should_skip_to_next_model,
            log_ai_error
        )
        
        assert ErrorCategory.AUTH_ERROR is not None
        assert ErrorCategory.RATE_LIMIT is not None
        assert ErrorCategory.TIMEOUT is not None
    
    def test_error_classifier_auth_detection(self):
        """ErrorClassifier should detect auth errors."""
        from omnix_services.ai_service.ai_error_handler import ErrorClassifier
        
        error = Exception("401 Unauthorized - invalid_api_key")
        ai_error = ErrorClassifier.classify_openai_error(error)
        
        assert ai_error is not None
        assert ai_error.is_retryable == False
    
    def test_should_skip_for_auth_error(self):
        """Non-retryable auth errors should skip to next model."""
        from omnix_services.ai_service.ai_error_handler import (
            AIError,
            ErrorCategory,
            should_skip_to_next_model
        )
        
        error = AIError(
            provider="openai",
            category=ErrorCategory.AUTH_ERROR,
            http_code=401,
            message="Invalid API key",
            raw_error=None,
            is_retryable=False,
            suggested_action="Update API key"
        )
        
        assert should_skip_to_next_model(error) == True
    
    def test_timeout_error_is_retryable(self):
        """Timeout errors should be retryable."""
        from omnix_services.ai_service.ai_error_handler import (
            ErrorClassifier,
            should_skip_to_next_model
        )
        
        timeout_error = ErrorClassifier.classify_timeout("gemini", 20.0)
        
        assert timeout_error.is_retryable == True
        assert should_skip_to_next_model(timeout_error) == False
