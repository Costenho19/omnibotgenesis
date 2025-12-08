"""
OMNIX INSTITUTIONAL+ - AI Service Package

Conversational AI with Multi-Model Strategy and Dependency Injection.

Architecture Overview:
- interfaces/: Protocol definitions (AIGatewayProtocol, PromptBuilderProtocol, etc.)
- providers/: Concrete AI provider implementations (Gemini, OpenAI, Anthropic)
- adapters/: Legacy compatibility and external integrations
- testing/: Mock implementations for unit testing
- container.py: Dependency injection container

Usage (New - Recommended):
    from omnix_services.ai_service import get_ai_gateway
    gateway = get_ai_gateway()
    response = await gateway.generate_text(request)

Usage (Legacy - Backward Compatible):
    from omnix_services.ai_service import get_ai_service
    service = get_ai_service()
    response = await service.generate_response(...)
"""

from omnix_config.settings import VERSION

from .ai_service import ConversationalAIService
from .ai_service import get_ai_service as _legacy_get_ai_service
from .ai_models import AIModelsManager
from .ai_styles import VisualStylesManager
from .ai_prompts import PromptsContextManager
from .conversational_brain import ConversationalBrain, get_conversational_brain
from .conversational_ai_adapter import ConversationalAI

from .container import (
    AIServiceContainer,
    get_container,
    get_ai_gateway,
    create_container,
)

from .interfaces.ai_gateway import (
    AIGatewayProtocol,
    TextGenerationRequest,
    TextGenerationResponse,
    ModelProvider,
    ModelInfo,
)

from .providers.routing_gateway import RoutingAIGateway


def get_ai_service() -> ConversationalAIService:
    """
    Get the AI service instance.
    
    BACKWARD COMPATIBLE: This function maintains the same interface
    as before the DI refactoring. For new code, prefer get_ai_gateway().
    """
    return _legacy_get_ai_service()


__all__ = [
    'ConversationalAIService',
    'get_ai_service',
    'AIModelsManager',
    'VisualStylesManager',
    'PromptsContextManager',
    'ConversationalBrain',
    'get_conversational_brain',
    'ConversationalAI',
    'AIServiceContainer',
    'get_container',
    'get_ai_gateway',
    'create_container',
    'AIGatewayProtocol',
    'TextGenerationRequest',
    'TextGenerationResponse',
    'ModelProvider',
    'ModelInfo',
    'RoutingAIGateway',
]

__version__ = VERSION
