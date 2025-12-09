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


def get_ai_gateway() -> RoutingAIGateway:
    """
    Get the AI gateway from the container.
    
    Convenience function for direct access to the gateway.
    """
    container = get_container()
    return container.ai_gateway()
