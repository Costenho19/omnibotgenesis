"""
OMNIX INSTITUTIONAL+ - Dependency Injection Container

Central container for managing AI service dependencies.
Uses dependency-injector library following SOLID principles.
"""

import os
import logging
from typing import Optional
from dependency_injector import containers, providers

from .interfaces.ai_gateway import ModelProvider
from .providers.gemini_provider import GeminiProvider
from .providers.openai_provider import OpenAIProvider
from .providers.anthropic_provider import AnthropicProvider
from .providers.routing_gateway import RoutingAIGateway
from .providers.redis_context_provider import RedisContextProvider
from .providers.omnix_prompt_builder import OmnixPromptBuilder
from .providers.omnix_style_renderer import OmnixStyleRenderer

logger = logging.getLogger(__name__)


def _create_routing_gateway(
    gemini: GeminiProvider,
    openai: OpenAIProvider,
    anthropic: AnthropicProvider,
) -> RoutingAIGateway:
    """Factory function to create and configure the routing gateway."""
    gateway = RoutingAIGateway(
        primary_provider=ModelProvider.GEMINI,
        max_retries=3,
    )
    gateway.register_provider(gemini)
    gateway.register_provider(openai)
    gateway.register_provider(anthropic)
    return gateway


class AIServiceContainer(containers.DeclarativeContainer):
    """
    Dependency Injection container for AI services.
    
    Manages lifecycle and wiring of:
    - AI Providers (Gemini, OpenAI, Anthropic)
    - Routing Gateway
    
    Usage:
        container = AIServiceContainer()
        gateway = container.ai_gateway()
        response = await gateway.generate_text(request)
    """

    config = providers.Configuration()

    gemini_provider = providers.Singleton(
        GeminiProvider,
        api_key=config.gemini_api_key,
    )

    openai_provider = providers.Singleton(
        OpenAIProvider,
        api_key=config.openai_api_key,
    )

    anthropic_provider = providers.Singleton(
        AnthropicProvider,
        api_key=config.anthropic_api_key,
    )

    ai_gateway = providers.Singleton(
        _create_routing_gateway,
        gemini=gemini_provider,
        openai=openai_provider,
        anthropic=anthropic_provider,
    )

    context_provider = providers.Singleton(
        RedisContextProvider,
    )

    prompt_builder = providers.Singleton(
        OmnixPromptBuilder,
    )

    style_renderer = providers.Singleton(
        OmnixStyleRenderer,
    )


def create_container() -> AIServiceContainer:
    """
    Factory function to create and configure the DI container.
    
    Reads API keys from environment variables.
    """
    container = AIServiceContainer()

    container.config.gemini_api_key.from_env(
        "GOOGLE_AI_API_KEY",
        default=os.getenv("GEMINI_API_KEY", ""),
    )
    container.config.openai_api_key.from_env(
        "OPENAI_API_KEY",
        default="",
    )
    container.config.anthropic_api_key.from_env(
        "ANTHROPIC_API_KEY",
        default="",
    )

    logger.info("AI Service container initialized")
    return container


_container_instance: Optional[AIServiceContainer] = None


def get_container() -> AIServiceContainer:
    """Get or create the global container instance."""
    global _container_instance
    if _container_instance is None:
        _container_instance = create_container()
    return _container_instance


_legacy_gateway_instance = None
_v7_gateway_shim = None
_v7_shim_last_health_check = 0.0
_V7_HEALTH_CHECK_INTERVAL = 60.0


def _is_use_ai_port_enabled() -> bool:
    """Check USE_AI_PORT flag per-request for dynamic fallback."""
    return os.environ.get('USE_AI_PORT', 'false').lower() == 'true'


def get_ai_gateway():
    """
    Get the AI gateway with V7.0 port switching.
    
    V7.0 Migration: When USE_AI_PORT=true, uses AIGatewayShim (hexagonal).
    AIGatewayShim wraps GeminiAdapter and provides AIGatewayProtocol interface.
    Otherwise, uses legacy RoutingAIGateway.
    
    Per-request evaluation with periodic health revalidation allows dynamic fallback.
    """
    global _legacy_gateway_instance, _v7_gateway_shim, _v7_shim_last_health_check
    import time
    
    if _is_use_ai_port_enabled():
        try:
            current_time = time.time()
            need_health_check = (
                _v7_gateway_shim is None or 
                (current_time - _v7_shim_last_health_check) > _V7_HEALTH_CHECK_INTERVAL
            )
            
            if _v7_gateway_shim is None:
                from src.omnix.infrastructure.adapters.ai_gateway_shim import AIGatewayShim
                _v7_gateway_shim = AIGatewayShim()
            
            if need_health_check:
                health = _v7_gateway_shim.health_check()
                _v7_shim_last_health_check = current_time
                
                if not health.get('healthy', False):
                    logger.warning("⚠️ AIGatewayShim unhealthy, falling back to RoutingAIGateway")
                    _v7_gateway_shim = None
                else:
                    logger.debug("✅ USE_AI_PORT=true - Using AIGatewayShim (V7.0 hexagonal)")
                    return _v7_gateway_shim
            else:
                return _v7_gateway_shim
                
        except ImportError as e:
            logger.warning(f"⚠️ AIGatewayShim import failed: {e}, using RoutingAIGateway")
            _v7_gateway_shim = None
        except Exception as e:
            logger.error(f"❌ AIGatewayShim error: {e}, using RoutingAIGateway")
            _v7_gateway_shim = None
    
    if _legacy_gateway_instance is None:
        container = get_container()
        _legacy_gateway_instance = container.ai_gateway()
    
    return _legacy_gateway_instance


_voice_adapter_instance = None
_voice_last_health_check = 0.0
_VOICE_HEALTH_CHECK_INTERVAL = 60.0
_legacy_voice_instance = None


def _is_use_voice_port_enabled() -> bool:
    """Check USE_VOICE_PORT flag per-request for dynamic fallback."""
    return os.environ.get('USE_VOICE_PORT', 'false').lower() == 'true'


def get_voice_service():
    """
    Get the voice service with V7.0 port switching.
    
    V7.0 Migration: When USE_VOICE_PORT=true, uses VoiceServiceAdapter (hexagonal).
    Otherwise, uses legacy VoiceServiceEnterprise.
    
    Per-request evaluation with periodic health revalidation.
    """
    global _voice_adapter_instance, _voice_last_health_check, _legacy_voice_instance
    import time
    
    if _is_use_voice_port_enabled():
        try:
            current_time = time.time()
            need_health_check = (
                _voice_adapter_instance is None or
                (current_time - _voice_last_health_check) > _VOICE_HEALTH_CHECK_INTERVAL
            )
            
            if _voice_adapter_instance is None:
                from src.omnix.infrastructure.adapters.voice_adapter import VoiceServiceAdapter
                _voice_adapter_instance = VoiceServiceAdapter()
            
            if need_health_check:
                health = _voice_adapter_instance.health_check()
                _voice_last_health_check = current_time
                
                if not (health.get('tts_available', False) or health.get('stt_available', False)):
                    logger.warning("⚠️ VoiceServiceAdapter unhealthy, falling back to VoiceServiceEnterprise")
                    _voice_adapter_instance = None
                else:
                    logger.debug("✅ USE_VOICE_PORT=true - Using VoiceServiceAdapter (V7.0 hexagonal)")
                    return _voice_adapter_instance
            else:
                return _voice_adapter_instance
                
        except ImportError as e:
            logger.warning(f"⚠️ VoiceServiceAdapter import failed: {e}, using VoiceServiceEnterprise")
            _voice_adapter_instance = None
        except Exception as e:
            logger.error(f"❌ VoiceServiceAdapter error: {e}, using VoiceServiceEnterprise")
            _voice_adapter_instance = None
    
    if _legacy_voice_instance is None:
        try:
            from omnix_services.voice_service.voice_service import VoiceServiceEnterprise
            _legacy_voice_instance = VoiceServiceEnterprise()
        except ImportError:
            logger.error("❌ VoiceServiceEnterprise not available")
            return None
    
    return _legacy_voice_instance


def initialize_v7_services() -> dict:
    """
    Initialize V7 AI and Voice services at application startup.
    
    Logs detailed status of each service and returns health summary.
    Call this from main_entry.py or EnterpriseTelegramBot.__init__
    """
    result = {
        'ai_service': {'type': 'unknown', 'healthy': False, 'error': None},
        'voice_service': {'type': 'unknown', 'healthy': False, 'error': None}
    }
    
    logger.info("=" * 60)
    logger.info("🚀 INITIALIZING V7 SERVICES")
    logger.info("=" * 60)
    
    use_ai_port = _is_use_ai_port_enabled()
    use_voice_port = _is_use_voice_port_enabled()
    
    logger.info(f"📌 Feature Flags:")
    logger.info(f"   USE_AI_PORT = {use_ai_port}")
    logger.info(f"   USE_VOICE_PORT = {use_voice_port}")
    
    try:
        ai_service = get_ai_gateway()
        if ai_service:
            service_type = type(ai_service).__name__
            result['ai_service']['type'] = service_type
            
            if hasattr(ai_service, 'health_check'):
                health = ai_service.health_check()
                result['ai_service']['healthy'] = health.get('healthy', True)
                logger.info(f"✅ AI Service: {service_type}")
                logger.info(f"   Health: {health}")
            else:
                result['ai_service']['healthy'] = True
                logger.info(f"✅ AI Service: {service_type} (legacy, no health_check)")
        else:
            result['ai_service']['error'] = 'Service is None'
            logger.error("❌ AI Service: Failed to initialize")
    except Exception as e:
        result['ai_service']['error'] = str(e)
        logger.error(f"❌ AI Service initialization error: {e}")
    
    try:
        voice_service = get_voice_service()
        if voice_service:
            service_type = type(voice_service).__name__
            result['voice_service']['type'] = service_type
            
            if hasattr(voice_service, 'health_check'):
                health = voice_service.health_check()
                tts_ok = health.get('tts_available', False)
                stt_ok = health.get('stt_available', False)
                result['voice_service']['healthy'] = tts_ok or stt_ok
                logger.info(f"✅ Voice Service: {service_type}")
                logger.info(f"   TTS: {'✅' if tts_ok else '❌'}, STT: {'✅' if stt_ok else '❌'}")
            else:
                result['voice_service']['healthy'] = True
                logger.info(f"✅ Voice Service: {service_type} (legacy, no health_check)")
        else:
            result['voice_service']['error'] = 'Service is None'
            logger.error("❌ Voice Service: Failed to initialize")
    except Exception as e:
        result['voice_service']['error'] = str(e)
        logger.error(f"❌ Voice Service initialization error: {e}")
    
    logger.info("=" * 60)
    logger.info(f"🏁 V7 SERVICES READY: AI={result['ai_service']['healthy']}, Voice={result['voice_service']['healthy']}")
    logger.info("=" * 60)
    
    return result


def get_v7_services_status() -> dict:
    """
    Get current status of V7 services without reinitializing.
    Useful for health endpoints and diagnostics.
    """
    return {
        'use_ai_port': _is_use_ai_port_enabled(),
        'use_voice_port': _is_use_voice_port_enabled(),
        'ai_gateway_type': type(_v7_gateway_shim).__name__ if _v7_gateway_shim else (
            type(_legacy_gateway_instance).__name__ if _legacy_gateway_instance else 'None'
        ),
        'voice_service_type': type(_voice_adapter_instance).__name__ if _voice_adapter_instance else (
            type(_legacy_voice_instance).__name__ if _legacy_voice_instance else 'None'
        ),
    }
