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

import logging

from omnix_config.settings import VERSION

logger = logging.getLogger(__name__)

# ConversationalAI FIRST — only stdlib deps, must always be available
try:
    from .conversational_ai_adapter import ConversationalAI
except ImportError as e:
    logger.warning(f"ConversationalAI not available: {e}")
    ConversationalAI = None

# Core services — may fail if redis_cache, rate_limiter, or omnix_core deps unavailable
try:
    from .ai_service import ConversationalAIService
    from .ai_service import get_ai_service as _legacy_get_ai_service
    from .ai_models import AIModelsManager
    from .ai_styles import VisualStylesManager
    from .ai_prompts import PromptsContextManager
    from .conversational_brain import ConversationalBrain, get_conversational_brain
    _core_services_available = True
except ImportError as e:
    logger.warning(f"AI core services not available: {e}")
    ConversationalAIService = None
    _legacy_get_ai_service = None
    AIModelsManager = None
    VisualStylesManager = None
    PromptsContextManager = None
    ConversationalBrain = None
    get_conversational_brain = None
    _core_services_available = False

# DI container — may fail if dependency_injector unavailable on Railway
try:
    from .container import (
        AIServiceContainer,
        get_container,
        get_ai_gateway,
        create_container,
    )
except ImportError:
    AIServiceContainer = None
    get_container = None
    get_ai_gateway = None
    create_container = None

# Protocol definitions — stdlib only, should always load
try:
    from .interfaces.ai_gateway import (
        AIGatewayProtocol,
        TextGenerationRequest,
        TextGenerationResponse,
        ModelProvider,
        ModelInfo,
    )
except ImportError as e:
    logger.warning(f"AI gateway interfaces not available: {e}")
    AIGatewayProtocol = None
    TextGenerationRequest = None
    TextGenerationResponse = None
    ModelProvider = None
    ModelInfo = None

# Routing gateway — may fail if provider SDKs unavailable
try:
    from .providers.routing_gateway import RoutingAIGateway
except ImportError as e:
    logger.warning(f"RoutingAIGateway not available: {e}")
    RoutingAIGateway = None


def get_ai_service():
    """
    Get the AI service instance.

    BACKWARD COMPATIBLE: This function maintains the same interface
    as before the DI refactoring. For new code, prefer get_ai_gateway().
    """
    if _legacy_get_ai_service is None:
        return None
    return _legacy_get_ai_service()


__all__ = [
    'ConversationalAI',
    'ConversationalAIService',
    'get_ai_service',
    'AIModelsManager',
    'VisualStylesManager',
    'PromptsContextManager',
    'ConversationalBrain',
    'get_conversational_brain',
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
