"""
OMNIX V7 Services Integration Tests
====================================
Tests for V7 AI Gateway Shim and Voice Service Adapter integration.
"""

import pytest
import os
from unittest.mock import patch, MagicMock


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


class TestAIGatewayShimErrorHandling:
    """Test AIGatewayShim HTTP error handling."""
    
    def test_extract_http_status_from_401_error(self):
        """Should extract 401 status code from error."""
        from src.omnix.infrastructure.adapters.ai_gateway_shim import _extract_http_status
        
        class MockError(Exception):
            status_code = 401
        
        error = MockError("Unauthorized")
        code, msg = _extract_http_status(error)
        
        assert code == 401
        assert "API key invalid" in msg or "expired" in msg
    
    def test_extract_http_status_from_429_error(self):
        """Should extract 429 status code from error."""
        from src.omnix.infrastructure.adapters.ai_gateway_shim import _extract_http_status
        
        class MockError(Exception):
            status_code = 429
        
        error = MockError("Rate limited")
        code, msg = _extract_http_status(error)
        
        assert code == 429
        assert "Rate limit" in msg or "quota" in msg.lower()
    
    def test_extract_http_status_from_string_error(self):
        """Should extract status code from error string containing HTTP code."""
        from src.omnix.infrastructure.adapters.ai_gateway_shim import _extract_http_status
        
        error = Exception("API error 401: Invalid key")
        code, msg = _extract_http_status(error)
        
        assert code == 401
    
    def test_extract_http_status_no_code(self):
        """Should return 0 for non-HTTP errors."""
        from src.omnix.infrastructure.adapters.ai_gateway_shim import _extract_http_status
        
        error = Exception("Generic error")
        code, msg = _extract_http_status(error)
        
        assert code == 0
        assert msg == "Generic error"


class TestAIGatewayShimBasics:
    """Test AIGatewayShim basic functionality."""
    
    def test_shim_initialization(self):
        """AIGatewayShim should initialize with defaults."""
        from src.omnix.infrastructure.adapters.ai_gateway_shim import AIGatewayShim
        
        shim = AIGatewayShim()
        
        assert shim._request_count == 0
        assert shim._error_count == 0
        assert shim._max_retries == 3
    
    def test_shim_health_check_without_adapter(self):
        """Health check should report unhealthy if adapter not available."""
        from src.omnix.infrastructure.adapters.ai_gateway_shim import AIGatewayShim
        
        shim = AIGatewayShim()
        shim._gemini_adapter = None
        
        with patch.object(shim, '_get_adapter', return_value=None):
            health = shim.health_check()
        
        assert health['healthy'] == False
        assert health['request_count'] == 0
    
    def test_shim_get_primary_provider(self):
        """Should return primary provider."""
        from src.omnix.infrastructure.adapters.ai_gateway_shim import AIGatewayShim
        from src.omnix.ports.driven.ai_text_gateway_port import ModelProvider
        
        shim = AIGatewayShim(primary_provider=ModelProvider.GEMINI)
        
        assert shim.get_primary_provider() == ModelProvider.GEMINI


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
