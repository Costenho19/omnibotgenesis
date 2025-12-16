"""
OMNIX V7.0 AI Text Gateway Port
================================
Protocol definition for AI text generation gateway.

Compatible with legacy AIGatewayProtocol (TextGenerationRequest/Response).
This port enables the hexagonal adapter to replace RoutingAIGateway.

Migration Status: Phase 3 - AI Service Integration
"""

from typing import Protocol, Optional, List, Dict, Any, AsyncIterator, runtime_checkable
from dataclasses import dataclass, field
from enum import Enum


class ModelProvider(Enum):
    """Supported AI model providers."""
    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"


@dataclass
class ModelInfo:
    """AI model metadata."""
    provider: ModelProvider
    model_name: str
    max_tokens: int = 4096
    supports_vision: bool = False
    supports_streaming: bool = True
    cost_per_1k_tokens: float = 0.0


@dataclass
class TextGenerationRequest:
    """Request DTO for text generation - compatible with legacy AIGatewayProtocol."""
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
    """Response DTO for text generation - compatible with legacy AIGatewayProtocol."""
    content: str
    provider_used: ModelProvider
    model_used: str
    tokens_used: int = 0
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None


@runtime_checkable
class AITextGatewayPort(Protocol):
    """
    Protocol for AI text generation gateway.
    
    Compatible with legacy AIGatewayProtocol from omnix_services/ai_service.
    Enables GeminiAdapter to replace RoutingAIGateway via feature flag.
    
    SOLID Principles:
    - SRP: Only text generation routing
    - ISP: Focused interface for gateway operations
    - DIP: High-level code depends on this abstraction
    """
    
    async def generate_text(
        self,
        request: TextGenerationRequest
    ) -> TextGenerationResponse:
        """
        Generate text response from AI model.
        
        Args:
            request: TextGenerationRequest with prompt and options
            
        Returns:
            TextGenerationResponse with content and metadata
        """
        ...
    
    async def generate_text_stream(
        self,
        request: TextGenerationRequest
    ) -> AsyncIterator[str]:
        """
        Stream text response from AI model.
        
        Args:
            request: TextGenerationRequest with prompt and options
            
        Yields:
            Text chunks as they are generated
        """
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
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check health of AI gateway and providers.
        
        Returns:
            Dict with:
            - healthy: bool
            - providers: Dict[str, bool] (availability per provider)
            - primary_provider: str
            - request_count: int
        """
        ...
