"""
OMNIX INSTITUTIONAL+ - Base AI Provider

Abstract base class for all AI providers following Template Method pattern.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, List, AsyncIterator

from ..interfaces.ai_gateway import (
    TextGenerationRequest,
    TextGenerationResponse,
    ModelInfo,
    ModelProvider,
)

logger = logging.getLogger(__name__)


class BaseAIProvider(ABC):
    """
    Base class for AI providers.
    
    Provides common functionality like logging, error handling,
    and defines the contract for concrete providers.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self._available = False
        self._initialize()

    @abstractmethod
    def _initialize(self) -> None:
        """Initialize the provider with API key validation."""
        ...

    @property
    @abstractmethod
    def provider_type(self) -> ModelProvider:
        """Return the provider type."""
        ...

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Return the default model name."""
        ...

    @abstractmethod
    async def generate_text(
        self,
        request: TextGenerationRequest
    ) -> TextGenerationResponse:
        """Generate text using this provider."""
        ...

    @abstractmethod
    async def generate_text_stream(
        self,
        request: TextGenerationRequest
    ) -> AsyncIterator[str]:
        """Stream text generation."""
        ...

    @abstractmethod
    def get_models(self) -> List[ModelInfo]:
        """Get available models for this provider."""
        ...

    def is_available(self) -> bool:
        """Check if provider is properly configured."""
        return self._available

    def _log_request(self, request: TextGenerationRequest) -> None:
        """Log request for debugging."""
        logger.debug(
            f"[{self.provider_type.value}] Request: "
            f"prompt_len={len(request.prompt)}, "
            f"max_tokens={request.max_tokens}, "
            f"temp={request.temperature}"
        )

    def _log_response(self, response: TextGenerationResponse) -> None:
        """Log response for debugging."""
        logger.debug(
            f"[{self.provider_type.value}] Response: "
            f"content_len={len(response.content)}, "
            f"tokens={response.tokens_used}, "
            f"latency={response.latency_ms:.0f}ms"
        )

    def _create_error_response(
        self,
        error: Exception,
        request: TextGenerationRequest
    ) -> TextGenerationResponse:
        """Create error response."""
        logger.error(f"[{self.provider_type.value}] Error: {error}")
        return TextGenerationResponse(
            content="",
            provider_used=self.provider_type,
            model_used=self.default_model,
            success=False,
            error_message=str(error),
        )
