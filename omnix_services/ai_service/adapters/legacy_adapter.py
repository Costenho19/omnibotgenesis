"""
OMNIX INSTITUTIONAL+ - Legacy Adapter

Provides backward compatibility with existing code that uses
the old singleton pattern (get_ai_service()).

This adapter wraps the new DI-based services to maintain
compatibility during migration.
"""

import logging
from typing import Optional, Dict, Any, List

from ..container import get_container, get_ai_gateway as _get_ai_gateway
from ..interfaces.ai_gateway import TextGenerationRequest, ModelProvider
from ..providers.routing_gateway import RoutingAIGateway

logger = logging.getLogger(__name__)


class LegacyAIServiceAdapter:
    """
    Adapter that mimics the old ConversationalAIService interface.
    
    Wraps the new RoutingAIGateway to provide backward compatibility.
    Existing code can continue using the same API while we migrate.
    """

    def __init__(self, gateway: Optional[RoutingAIGateway] = None):
        self._gateway = gateway or _get_ai_gateway()
        logger.info("LegacyAIServiceAdapter initialized (DI-backed)")

    async def generate_response(
        self,
        chat_id: int,
        user_message: str,
        user_name: str = 'Usuario',
        market_data: Optional[Dict[str, Any]] = None,
        apply_visual_style: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate AI response - compatible with old interface.
        
        This method bridges the old API to the new RoutingAIGateway.
        """
        request = TextGenerationRequest(
            prompt=user_message,
            user_id=str(chat_id),
            metadata={
                "user_name": user_name,
                "market_data": market_data,
                "apply_visual_style": apply_visual_style,
            },
        )

        response = await self._gateway.generate_text(request)

        return {
            "response": response.content,
            "success": response.success,
            "provider": response.provider_used.value,
            "model": response.model_used,
            "tokens_used": response.tokens_used,
            "latency_ms": response.latency_ms,
            "error": response.error_message,
        }

    def is_available(self) -> bool:
        """Check if any AI provider is available."""
        return len(self._gateway.get_available_models()) > 0

    def get_stats(self) -> Dict[str, Any]:
        """Get gateway statistics."""
        return self._gateway.get_stats()


_legacy_service_instance: Optional[LegacyAIServiceAdapter] = None


def get_ai_service() -> LegacyAIServiceAdapter:
    """
    Get the AI service instance.
    
    BACKWARD COMPATIBLE: Returns a LegacyAIServiceAdapter that
    wraps the new DI-based RoutingAIGateway.
    
    Existing code can continue using:
        from omnix_services.ai_service import get_ai_service
        service = get_ai_service()
        response = await service.generate_response(...)
    """
    global _legacy_service_instance
    if _legacy_service_instance is None:
        _legacy_service_instance = LegacyAIServiceAdapter()
    return _legacy_service_instance


def get_ai_gateway() -> RoutingAIGateway:
    """
    Get the AI gateway directly.
    
    NEW API: For new code that wants to use the modern interface.
    """
    return _get_ai_gateway()
