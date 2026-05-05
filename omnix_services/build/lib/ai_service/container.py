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
_V7_SHIM_COOLDOWN_SECONDS = 300.0
_v7_shim_last_failure = 0.0
_ai_models_manager_instance = None


def _is_use_ai_port_enabled() -> bool:
    """Check USE_AI_PORT flag per-request for dynamic fallback."""
    return os.environ.get('USE_AI_PORT', 'false').lower() == 'true'


def _get_ai_models_manager():
    """Get or create singleton AIModelsManager instance."""
    global _ai_models_manager_instance
    if _ai_models_manager_instance is None:
        try:
            from omnix_services.ai_service.ai_models import AIModelsManager
            _ai_models_manager_instance = AIModelsManager()
            logger.info("✅ AIModelsManager singleton created (with full failover chain)")
        except Exception as e:
            logger.error(f"❌ Failed to create AIModelsManager: {e}")
            return None
    return _ai_models_manager_instance


def _reset_v7_shim():
    """
    Reset V7 shim and manager singletons and mark failure timestamp.
    
    After reset, the system will use legacy gateway until cooldown expires.
    This prevents hot-loop recreation attempts when manager is unavailable.
    """
    global _v7_gateway_shim, _ai_models_manager_instance, _v7_shim_last_health_check, _v7_shim_last_failure
    import time
    _v7_gateway_shim = None
    _ai_models_manager_instance = None
    _v7_shim_last_health_check = 0.0
    _v7_shim_last_failure = time.time()
    logger.info(f"🔄 V7 shim reset - using legacy gateway for {_V7_SHIM_COOLDOWN_SECONDS}s cooldown")


def _is_v7_shim_in_cooldown() -> bool:
    """Check if we're in cooldown period after a shim failure."""
    import time
    if _v7_shim_last_failure == 0.0:
        return False
    elapsed = time.time() - _v7_shim_last_failure
    return elapsed < _V7_SHIM_COOLDOWN_SECONDS


def get_ai_gateway():
    """
    Get the AI gateway with V7.0 port switching.
    
    V7.0 Migration (Dec 16, 2025): When USE_AI_PORT=true, uses AIGatewayShim.
    
    ARCHITECTURE: AIGatewayShim is now a PURE ADAPTER that delegates to
    AIModelsManager (legacy). This ensures the shim uses the same proven
    failover logic: Gemini → OpenAI → Anthropic with intelligent error handling.
    
    FAILOVER BEHAVIOR:
    - If shim initialization fails → falls back to RoutingAIGateway
    - If health check fails (manager None, no providers, high error rate) → resets and falls back
    - If USE_AI_PORT=false → uses RoutingAIGateway directly
    
    Per-request evaluation with periodic health revalidation allows dynamic fallback.
    """
    global _legacy_gateway_instance, _v7_gateway_shim, _v7_shim_last_health_check
    import time
    
    fallback_to_legacy = False
    
    if _is_use_ai_port_enabled() and not _is_v7_shim_in_cooldown():
        try:
            current_time = time.time()
            need_health_check = (
                _v7_gateway_shim is None or 
                (current_time - _v7_shim_last_health_check) > _V7_HEALTH_CHECK_INTERVAL
            )
            
            if _v7_gateway_shim is None:
                from src.omnix.infrastructure.adapters.ai_gateway_shim import AIGatewayShim
                ai_manager = _get_ai_models_manager()
                if ai_manager is None:
                    logger.warning("⚠️ AIModelsManager creation failed, using RoutingAIGateway")
                    _reset_v7_shim()
                    fallback_to_legacy = True
                else:
                    _v7_gateway_shim = AIGatewayShim(ai_models_manager=ai_manager)
                    logger.info("✅ AIGatewayShim created with AIModelsManager backend")
            
            if not fallback_to_legacy and _v7_gateway_shim is not None and need_health_check:
                health = _v7_gateway_shim.health_check()
                _v7_shim_last_health_check = current_time
                
                if not health.get('healthy', False):
                    logger.warning(
                        f"⚠️ AIGatewayShim unhealthy: providers={health.get('providers')}, "
                        f"error_rate={health.get('error_rate', 0):.2f} - falling back to RoutingAIGateway"
                    )
                    _reset_v7_shim()
                    fallback_to_legacy = True
                else:
                    logger.debug(f"✅ USE_AI_PORT=true - AIGatewayShim healthy: {health.get('providers', {})}")
                    return _v7_gateway_shim
            elif not fallback_to_legacy and _v7_gateway_shim is not None:
                return _v7_gateway_shim
                
        except ImportError as e:
            logger.warning(f"⚠️ AIGatewayShim import failed: {e}, using RoutingAIGateway")
            _reset_v7_shim()
            fallback_to_legacy = True
        except Exception as e:
            logger.error(f"❌ AIGatewayShim error: {e}, using RoutingAIGateway")
            _reset_v7_shim()
            fallback_to_legacy = True
    
    if _legacy_gateway_instance is None:
        container = get_container()
        _legacy_gateway_instance = container.ai_gateway()
    
    return _legacy_gateway_instance


_voice_adapter_instance = None
_voice_last_health_check = 0.0
_VOICE_HEALTH_CHECK_INTERVAL = 60.0
_VOICE_COOLDOWN_SECONDS = 300.0
_voice_adapter_last_failure = 0.0
_legacy_voice_instance = None
_voice_enterprise_instance = None


def _is_use_voice_port_enabled() -> bool:
    """Check USE_VOICE_PORT flag per-request for dynamic fallback."""
    return os.environ.get('USE_VOICE_PORT', 'false').lower() == 'true'


def _get_voice_enterprise():
    """Get or create VoiceServiceEnterprise instance."""
    global _voice_enterprise_instance
    if _voice_enterprise_instance is None:
        try:
            from omnix_services.voice_service.voice_service import VoiceServiceEnterprise
            _voice_enterprise_instance = VoiceServiceEnterprise()
            logger.info("✅ VoiceServiceEnterprise created for adapter injection")
        except Exception as e:
            logger.error(f"❌ Failed to create VoiceServiceEnterprise: {e}")
            return None
    return _voice_enterprise_instance


def _reset_voice_adapter():
    """
    Reset V7 voice adapter (NOT the enterprise service) and mark failure timestamp.
    
    After reset, the system will use legacy service until cooldown expires.
    This prevents hot-loop recreation attempts when adapter is unavailable.
    
    NOTE: We do NOT reset _voice_enterprise_instance because the underlying
    service (gTTS/Whisper) is still valid. Only the adapter wrapper had issues.
    After cooldown, we can recreate the adapter using the same enterprise service.
    """
    global _voice_adapter_instance, _voice_last_health_check, _voice_adapter_last_failure
    import time
    _voice_adapter_instance = None
    _voice_last_health_check = 0.0
    _voice_adapter_last_failure = time.time()
    logger.info(f"🔄 V7 voice adapter reset - using legacy service for {_VOICE_COOLDOWN_SECONDS}s cooldown")


def _is_voice_in_cooldown() -> bool:
    """Check if we're in cooldown period after a voice adapter failure."""
    import time
    if _voice_adapter_last_failure == 0.0:
        return False
    elapsed = time.time() - _voice_adapter_last_failure
    return elapsed < _VOICE_COOLDOWN_SECONDS


def get_voice_service():
    """
    Get the voice service with V7.0 port switching.
    
    V7.0 Migration: When USE_VOICE_PORT=true, uses VoiceServiceAdapter (hexagonal).
    Otherwise, uses legacy VoiceServiceEnterprise.
    
    ARCHITECTURE: VoiceServiceAdapter is a PURE ADAPTER that delegates to
    VoiceServiceEnterprise (legacy). This ensures the adapter uses the same
    proven TTS/STT logic as the legacy system.
    
    FALLBACK BEHAVIOR:
    - If adapter initialization fails → falls back to VoiceServiceEnterprise
    - If health check fails (service None, no TTS/STT, high error rate) → resets and falls back
    - If USE_VOICE_PORT=false → uses VoiceServiceEnterprise directly
    
    Per-request evaluation with periodic health revalidation allows dynamic fallback.
    """
    global _voice_adapter_instance, _voice_last_health_check, _legacy_voice_instance
    import time
    
    fallback_to_legacy = False
    
    if _is_use_voice_port_enabled() and not _is_voice_in_cooldown():
        try:
            current_time = time.time()
            need_health_check = (
                _voice_adapter_instance is None or
                (current_time - _voice_last_health_check) > _VOICE_HEALTH_CHECK_INTERVAL
            )
            
            if _voice_adapter_instance is None:
                from src.omnix.infrastructure.adapters.voice_adapter import VoiceServiceAdapter
                voice_enterprise = _get_voice_enterprise()
                if voice_enterprise is None:
                    logger.warning("⚠️ VoiceServiceEnterprise creation failed, using legacy")
                    _reset_voice_adapter()
                    fallback_to_legacy = True
                else:
                    _voice_adapter_instance = VoiceServiceAdapter(voice_service=voice_enterprise)
                    logger.info("✅ VoiceServiceAdapter created with VoiceServiceEnterprise backend")
            
            if not fallback_to_legacy and _voice_adapter_instance is not None and need_health_check:
                health = _voice_adapter_instance.health_check()
                _voice_last_health_check = current_time
                
                if not health.get('healthy', False):
                    logger.warning(
                        f"⚠️ VoiceServiceAdapter unhealthy: tts={health.get('tts_available')}, "
                        f"stt={health.get('stt_available')}, error_rate={health.get('error_rate', 0):.2f} - "
                        f"falling back to VoiceServiceEnterprise"
                    )
                    _reset_voice_adapter()
                    fallback_to_legacy = True
                else:
                    logger.debug(f"✅ USE_VOICE_PORT=true - VoiceServiceAdapter healthy: {health}")
                    return _voice_adapter_instance
            elif not fallback_to_legacy and _voice_adapter_instance is not None:
                return _voice_adapter_instance
                
        except ImportError as e:
            logger.warning(f"⚠️ VoiceServiceAdapter import failed: {e}, using VoiceServiceEnterprise")
            _reset_voice_adapter()
            fallback_to_legacy = True
        except Exception as e:
            logger.error(f"❌ VoiceServiceAdapter error: {e}, using VoiceServiceEnterprise")
            _reset_voice_adapter()
            fallback_to_legacy = True
    
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
