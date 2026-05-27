"""
OMNIX INSTITUTIONAL+ - Gemini Provider

Google Gemini AI implementation following AIGatewayProtocol.
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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from google import genai as genai_type
    from google.genai import types as types_type

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    types = None
    GEMINI_AVAILABLE = False
    logger.warning("google-genai not installed")


class GeminiProvider(BaseAIProvider):
    """
    Gemini AI provider implementation.
    
    Primary provider for OMNIX - uses Gemini 2.0 Flash.
    """

    def __init__(self, api_key: Optional[str] = None):
        self._client = None
        super().__init__(api_key or os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GEMINI_API_KEY"))

    def _initialize(self) -> None:
        """Initialize Gemini client."""
        if not GEMINI_AVAILABLE:
            logger.warning("Gemini SDK not available")
            self._available = False
            return

        if not self.api_key:
            logger.warning("Gemini API key not configured")
            self._available = False
            return

        try:
            self._client = genai.Client(api_key=self.api_key)  # type: ignore[union-attr]
            self._available = True
            logger.info("Gemini provider initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self._available = False

    @property
    def provider_type(self) -> ModelProvider:
        return ModelProvider.GEMINI

    @property
    def default_model(self) -> str:
        return "gemini-2.5-flash"

    def get_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(
                provider=ModelProvider.GEMINI,
                model_name="gemini-2.5-flash",
                max_tokens=8192,
                supports_vision=True,
                supports_streaming=True,
                cost_per_1k_tokens=0.0001,
            ),
            ModelInfo(
                provider=ModelProvider.GEMINI,
                model_name="gemini-1.5-pro",
                max_tokens=32768,
                supports_vision=True,
                supports_streaming=True,
                cost_per_1k_tokens=0.0035,
            ),
        ]

    async def generate_text(
        self,
        request: TextGenerationRequest
    ) -> TextGenerationResponse:
        """Generate text using Gemini."""
        if not self._available or not self._client:
            return self._create_error_response(
                Exception("Gemini not available"),
                request
            )

        self._log_request(request)
        start_time = time.time()

        try:
            contents = []
            if request.system_prompt:
                contents.append(request.system_prompt + "\n\n")
            contents.append(request.prompt)

            response = self._client.models.generate_content(
                model=self.default_model,
                contents="".join(contents),
                config=types.GenerateContentConfig(  # type: ignore[union-attr]
                    max_output_tokens=request.max_tokens,
                    temperature=request.temperature,
                ),
            )

            content = response.text if response.text else ""
            latency_ms = (time.time() - start_time) * 1000

            result = TextGenerationResponse(
                content=content,
                provider_used=self.provider_type,
                model_used=self.default_model,
                tokens_used=len(content.split()) * 2,
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
        """Stream text using Gemini."""
        if not self._available or not self._client:
            yield "[Error: Gemini not available]"
            return

        try:
            contents = []
            if request.system_prompt:
                contents.append(request.system_prompt + "\n\n")
            contents.append(request.prompt)

            response = self._client.models.generate_content_stream(
                model=self.default_model,
                contents="".join(contents),
                config=types.GenerateContentConfig(  # type: ignore[union-attr]
                    max_output_tokens=request.max_tokens,
                    temperature=request.temperature,
                ),
            )

            for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"Gemini stream error: {e}")
            yield f"[Error: {str(e)}]"
