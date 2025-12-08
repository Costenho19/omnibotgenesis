"""
OMNIX INSTITUTIONAL+ - OpenAI Provider

OpenAI GPT implementation following AIGatewayProtocol.
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
    from openai import OpenAI, AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai not installed")


class OpenAIProvider(BaseAIProvider):
    """
    OpenAI GPT provider implementation.
    
    Secondary provider for OMNIX - uses GPT-4o.
    """

    def __init__(self, api_key: Optional[str] = None):
        self._client = None
        self._async_client = None
        super().__init__(api_key or os.getenv("OPENAI_API_KEY"))

    def _initialize(self) -> None:
        """Initialize OpenAI client."""
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI SDK not available")
            self._available = False
            return

        if not self.api_key:
            logger.warning("OpenAI API key not configured")
            self._available = False
            return

        try:
            self._client = OpenAI(api_key=self.api_key)
            self._async_client = AsyncOpenAI(api_key=self.api_key)
            self._available = True
            logger.info("OpenAI provider initialized")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            self._available = False

    @property
    def provider_type(self) -> ModelProvider:
        return ModelProvider.OPENAI

    @property
    def default_model(self) -> str:
        return "gpt-4o"

    def get_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(
                provider=ModelProvider.OPENAI,
                model_name="gpt-4o",
                max_tokens=4096,
                supports_vision=True,
                supports_streaming=True,
                cost_per_1k_tokens=0.005,
            ),
            ModelInfo(
                provider=ModelProvider.OPENAI,
                model_name="gpt-4o-mini",
                max_tokens=16384,
                supports_vision=True,
                supports_streaming=True,
                cost_per_1k_tokens=0.00015,
            ),
        ]

    async def generate_text(
        self,
        request: TextGenerationRequest
    ) -> TextGenerationResponse:
        """Generate text using OpenAI."""
        if not self._available or not self._async_client:
            return self._create_error_response(
                Exception("OpenAI not available"),
                request
            )

        self._log_request(request)
        start_time = time.time()

        try:
            messages = []
            if request.system_prompt:
                messages.append({
                    "role": "system",
                    "content": request.system_prompt
                })
            messages.append({
                "role": "user",
                "content": request.prompt
            })

            response = await self._async_client.chat.completions.create(
                model=self.default_model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            )

            content = response.choices[0].message.content or ""
            latency_ms = (time.time() - start_time) * 1000
            tokens_used = response.usage.total_tokens if response.usage else 0

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
        """Stream text using OpenAI."""
        if not self._available or not self._async_client:
            yield "[Error: OpenAI not available]"
            return

        try:
            messages = []
            if request.system_prompt:
                messages.append({
                    "role": "system",
                    "content": request.system_prompt
                })
            messages.append({
                "role": "user",
                "content": request.prompt
            })

            stream = await self._async_client.chat.completions.create(
                model=self.default_model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI stream error: {e}")
            yield f"[Error: {str(e)}]"
