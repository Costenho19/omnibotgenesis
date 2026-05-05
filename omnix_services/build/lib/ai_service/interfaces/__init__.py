"""
OMNIX INSTITUTIONAL+ - AI Service Interfaces

Protocol definitions for AI service components following SOLID principles.
All concrete implementations must adhere to these contracts.
"""

from .ai_gateway import (
    AIGatewayProtocol,
    TextGenerationRequest,
    TextGenerationResponse,
    ModelInfo,
)
from .prompt_builder import PromptBuilderProtocol, PromptContext
from .style_renderer import StyleRendererProtocol, RenderOptions
from .context_provider import ContextProviderProtocol, ConversationContext

__all__ = [
    "AIGatewayProtocol",
    "TextGenerationRequest",
    "TextGenerationResponse",
    "ModelInfo",
    "PromptBuilderProtocol",
    "PromptContext",
    "StyleRendererProtocol",
    "RenderOptions",
    "ContextProviderProtocol",
    "ConversationContext",
]
