"""
OMNIX INSTITUTIONAL+ - Anthropic Provider

Anthropic Claude implementation following AIGatewayProtocol.
"""

import os
import time
import logging
from typing import Optional, List, AsyncIterator

from ..interfaces.ai_gateway import (
    TextGenerationRequest,
    TextGenerationResponse,
    ModelInfo,
    ModelProvider,
)
from .base_provider import BaseAIProvider

logger = logging.getLogger(__name__)

try:
    from anthropic import Anthropic, AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    Anthropic = None  # type: ignore
    AsyncAnthropic = None  # type: ignore
    ANTHROPIC_AVAILABLE = False
    logger.warning("anthropic not installed")


class AnthropicProvider(BaseAIProvider):
    """
    Anthropic Claude provider implementation.
    
    Fallback provider for OMNIX - uses Claude 3.5 Sonnet.
    """

    def __init__(self, api_key: Optional[str] = None):
        self._client = None
        self._async_client = None
        super().__init__(api_key or os.getenv("ANTHROPIC_API_KEY"))

    def _initialize(self) -> None:
        """Initialize Anthropic client."""
        if not ANTHROPIC_AVAILABLE:
            logger.warning("Anthropic SDK not available")
            self._available = False
            return

        if not self.api_key:
            logger.warning("Anthropic API key not configured")
            self._available = False
            return

        try:
            self._client = Anthropic(api_key=self.api_key)
            self._async_client = AsyncAnthropic(api_key=self.api_key)
            self._available = True
            logger.info("Anthropic provider initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic: {e}")
            self._available = False

    @property
    def provider_type(self) -> ModelProvider:
        return ModelProvider.ANTHROPIC

    @property
    def default_model(self) -> str:
        return "claude-3-5-sonnet-20241022"

    def get_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(
                provider=ModelProvider.ANTHROPIC,
                model_name="claude-3-5-sonnet-20241022",
                max_tokens=8192,
                supports_vision=True,
                supports_streaming=True,
                cost_per_1k_tokens=0.003,
            ),
            ModelInfo(
                provider=ModelProvider.ANTHROPIC,
                model_name="claude-3-opus-20240229",
                max_tokens=4096,
                supports_vision=True,
                supports_streaming=True,
                cost_per_1k_tokens=0.015,
            ),
        ]

    async def generate_text(
        self,
        request: TextGenerationRequest
    ) -> TextGenerationResponse:
        """Generate text using Anthropic."""
        if not self._available or not self._async_client:
            return self._create_error_response(
                Exception("Anthropic not available"),
                request
            )

        self._log_request(request)
        start_time = time.time()

        try:
            response = await self._async_client.messages.create(
                model=self.default_model,
                max_tokens=request.max_tokens,
                system=request.system_prompt or "",
                messages=[
                    {"role": "user", "content": request.prompt}
                ],
            )

            content = ""
            if response.content and len(response.content) > 0:
                first_block = response.content[0]
                if hasattr(first_block, 'text'):
                    content = first_block.text

            latency_ms = (time.time() - start_time) * 1000
            tokens_used = (
                response.usage.input_tokens + response.usage.output_tokens
                if response.usage else 0
            )

            result = TextGenerationResponse(
                content=content,
                provider_used=self.provider_type,
                model_used=self.default_model,
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                success=True,
            )

            self._log_response(result)
            return result

        except Exception as e:
            return self._create_error_response(e, request)

    async def generate_text_stream(
        self,
        request: TextGenerationRequest
    ) -> AsyncIterator[str]:
        """Stream text using Anthropic."""
        if not self._available or not self._async_client:
            yield "[Error: Anthropic not available]"
            return

        try:
            async with self._async_client.messages.stream(
                model=self.default_model,
                max_tokens=request.max_tokens,
                system=request.system_prompt or "",
                messages=[
                    {"role": "user", "content": request.prompt}
                ],
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            logger.error(f"Anthropic stream error: {e}")
            yield f"[Error: {str(e)}]"
