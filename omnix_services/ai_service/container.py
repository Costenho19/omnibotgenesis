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


def _is_use_ai_port_enabled() -> bool:
    """Check USE_AI_PORT flag per-request for dynamic fallback."""
    return os.environ.get('USE_AI_PORT', 'false').lower() == 'true'


def get_ai_gateway():
    """
    Get the AI gateway with V7.0 port switching.
    
    V7.0 Migration: When USE_AI_PORT=true, uses AIGatewayShim (hexagonal).
    AIGatewayShim wraps GeminiAdapter and provides AIGatewayProtocol interface.
    Otherwise, uses legacy RoutingAIGateway.
    
    Per-request evaluation allows dynamic fallback if V7 adapter fails.
    """
    global _legacy_gateway_instance, _v7_gateway_shim
    
    if _is_use_ai_port_enabled():
        try:
            if _v7_gateway_shim is None:
                from src.omnix.infrastructure.adapters.ai_gateway_shim import AIGatewayShim
                _v7_gateway_shim = AIGatewayShim()
            
            health = _v7_gateway_shim.health_check()
            if health.get('healthy', False):
                logger.debug("✅ USE_AI_PORT=true - Using AIGatewayShim (V7.0 hexagonal)")
                return _v7_gateway_shim
            else:
                logger.warning("⚠️ AIGatewayShim unhealthy, falling back to RoutingAIGateway")
        except ImportError as e:
            logger.warning(f"⚠️ AIGatewayShim import failed: {e}, using RoutingAIGateway")
        except Exception as e:
            logger.error(f"❌ AIGatewayShim error: {e}, using RoutingAIGateway")
    
    if _legacy_gateway_instance is None:
        container = get_container()
        _legacy_gateway_instance = container.ai_gateway()
    
    return _legacy_gateway_instance


_voice_adapter_instance = None


def _is_use_voice_port_enabled() -> bool:
    """Check USE_VOICE_PORT flag per-request for dynamic fallback."""
    return os.environ.get('USE_VOICE_PORT', 'false').lower() == 'true'


def get_voice_service():
    """
    Get the voice service with V7.0 port switching.
    
    V7.0 Migration: When USE_VOICE_PORT=true, uses VoiceServiceAdapter (hexagonal).
    Otherwise, uses legacy VoiceServiceEnterprise.
    """
    global _voice_adapter_instance
    
    if _is_use_voice_port_enabled():
        try:
            if _voice_adapter_instance is None:
                from src.omnix.infrastructure.adapters.voice_adapter import VoiceServiceAdapter
                _voice_adapter_instance = VoiceServiceAdapter()
            
            health = _voice_adapter_instance.health_check()
            if health.get('tts_available', False) or health.get('stt_available', False):
                logger.debug("✅ USE_VOICE_PORT=true - Using VoiceServiceAdapter (V7.0 hexagonal)")
                return _voice_adapter_instance
            else:
                logger.warning("⚠️ VoiceServiceAdapter unhealthy, falling back to VoiceServiceEnterprise")
        except ImportError as e:
            logger.warning(f"⚠️ VoiceServiceAdapter import failed: {e}, using VoiceServiceEnterprise")
        except Exception as e:
            logger.error(f"❌ VoiceServiceAdapter error: {e}, using VoiceServiceEnterprise")
    
    try:
        from omnix_services.voice_service.voice_service import VoiceServiceEnterprise
        return VoiceServiceEnterprise()
    except ImportError:
        logger.error("❌ VoiceServiceEnterprise not available")
        return None
