"""
OMNIX INSTITUTIONAL+ - Routing AI Gateway

Implements AIGatewayProtocol with intelligent routing, load balancing,
and automatic failover between providers.
"""

import logging
import random
from typing import List, Optional, AsyncIterator, Dict

from ..interfaces.ai_gateway import (
    AIGatewayProtocol,
    TextGenerationRequest,
    TextGenerationResponse,
    ModelInfo,
    ModelProvider,
)
from .base_provider import BaseAIProvider

logger = logging.getLogger(__name__)


class RoutingAIGateway:
    """
    Intelligent routing gateway for AI providers.
    
    Features:
    - Automatic failover between providers
    - Load balancing (round-robin, weighted, random)
    - Provider health monitoring
    - Request routing based on preferences
    
    Implements AIGatewayProtocol.
    """

    def __init__(
        self,
        providers: Optional[Dict[ModelProvider, BaseAIProvider]] = None,
        primary_provider: ModelProvider = ModelProvider.GEMINI,
        fallback_order: Optional[List[ModelProvider]] = None,
        max_retries: int = 3,
    ):
        self.providers = providers or {}
        self.primary_provider = primary_provider
        self.fallback_order = fallback_order or [
            ModelProvider.OPENAI,
            ModelProvider.GEMINI,
            ModelProvider.ANTHROPIC,
        ]
        self.max_retries = max_retries
        self._request_count = 0

    def register_provider(
        self,
        provider: BaseAIProvider
    ) -> None:
        """Register a new AI provider."""
        self.providers[provider.provider_type] = provider
        logger.info(f"Registered provider: {provider.provider_type.value}")

    def _get_available_providers(self) -> List[BaseAIProvider]:
        """Get list of available providers in fallback order."""
        available = []
        for provider_type in self.fallback_order:
            if provider_type in self.providers:
                provider = self.providers[provider_type]
                if provider.is_available():
                    available.append(provider)
        return available

    def _select_provider(
        self,
        preferred: Optional[ModelProvider] = None
    ) -> Optional[BaseAIProvider]:
        """Select best available provider."""
        if preferred and preferred in self.providers:
            provider = self.providers[preferred]
            if provider.is_available():
                return provider

        if self.primary_provider in self.providers:
            provider = self.providers[self.primary_provider]
            if provider.is_available():
                return provider

        available = self._get_available_providers()
        return available[0] if available else None

    async def generate_text(
        self,
        request: TextGenerationRequest
    ) -> TextGenerationResponse:
        """
        Generate text with automatic failover.
        
        Tries providers in order until one succeeds.
        """
        self._request_count += 1
        errors = []

        for provider in self._get_available_providers():
            try:
                response = await provider.generate_text(request)
                if response.success:
                    return response
                errors.append(f"{provider.provider_type.value}: {response.error_message}")
            except Exception as e:
                errors.append(f"{provider.provider_type.value}: {str(e)}")
                logger.warning(f"Provider {provider.provider_type.value} failed: {e}")

        error_summary = "; ".join(errors) if errors else "No providers available"
        logger.error(f"All providers failed: {error_summary}")

        return TextGenerationResponse(
            content="",
            provider_used=self.primary_provider,
            model_used="",
            success=False,
            error_message=f"All providers failed: {error_summary}",
        )

    async def generate_text_stream(
        self,
        request: TextGenerationRequest
    ) -> AsyncIterator[str]:
        """Stream text with automatic failover."""
        provider = self._select_provider(request.preferred_provider)

        if not provider:
            yield "[Error: No AI providers available]"
            return

        try:
            async for chunk in provider.generate_text_stream(request):
                yield chunk
        except Exception as e:
            logger.error(f"Stream failed: {e}")
            yield f"[Error: {str(e)}]"

    def get_available_models(self) -> List[ModelInfo]:
        """Get all available models from all providers."""
        models = []
        for provider in self.providers.values():
            if provider.is_available():
                models.extend(provider.get_models())
        return models

    def is_provider_available(self, provider: ModelProvider) -> bool:
        """Check if a specific provider is available."""
        if provider in self.providers:
            return self.providers[provider].is_available()
        return False

    def get_primary_provider(self) -> ModelProvider:
        """Get the primary provider."""
        return self.primary_provider

    def get_stats(self) -> Dict:
        """Get gateway statistics."""
        return {
            "total_requests": self._request_count,
            "providers_registered": len(self.providers),
            "providers_available": sum(
                1 for p in self.providers.values() if p.is_available()
            ),
            "primary_provider": self.primary_provider.value,
        }
