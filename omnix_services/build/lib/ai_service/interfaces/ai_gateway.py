"""
OMNIX INSTITUTIONAL+ - AI Gateway Protocol

Defines the contract for AI model providers (OpenAI, Gemini, Anthropic).
Follows Dependency Inversion Principle - high-level modules depend on this abstraction.
"""

from typing import Protocol, Optional, Dict, Any, List, AsyncIterator
from dataclasses import dataclass, field
from enum import Enum


class ModelProvider(Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"


@dataclass
class ModelInfo:
    provider: ModelProvider
    model_name: str
    max_tokens: int = 4096
    supports_vision: bool = False
    supports_streaming: bool = True
    cost_per_1k_tokens: float = 0.0


@dataclass
class TextGenerationRequest:
    prompt: str
    system_prompt: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    images: Optional[List[bytes]] = None
    preferred_provider: Optional[ModelProvider] = None


@dataclass
class TextGenerationResponse:
    content: str
    provider_used: ModelProvider
    model_used: str
    tokens_used: int = 0
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None


class AIGatewayProtocol(Protocol):
    """
    Protocol for AI model gateway.
    
    Single Responsibility: Route requests to appropriate AI providers.
    Open/Closed: New providers can be added without modifying this interface.
    Liskov Substitution: Any implementation is interchangeable.
    Interface Segregation: Focused on text generation only.
    Dependency Inversion: High-level code depends on this abstraction.
    """

    async def generate_text(
        self,
        request: TextGenerationRequest
    ) -> TextGenerationResponse:
        """Generate text response from AI model."""
        ...

    async def generate_text_stream(
        self,
        request: TextGenerationRequest
    ) -> AsyncIterator[str]:
        """Stream text response from AI model."""
        ...

    def get_available_models(self) -> List[ModelInfo]:
        """Get list of available AI models."""
        ...

    def is_provider_available(self, provider: ModelProvider) -> bool:
        """Check if a specific provider is configured and available."""
        ...

    def get_primary_provider(self) -> ModelProvider:
        """Get the primary/default AI provider."""
        ...
