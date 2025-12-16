"""
OMNIX V7.0 AI Gateway Compatibility Shim
=========================================
Bridges GeminiAdapter (AIInferencePort) with AITextGatewayPort (legacy compatible).

This shim allows GeminiAdapter to replace RoutingAIGateway from legacy code.
It translates TextGenerationRequest/Response to prompt-based calls.

Migration Status: Phase 3 - AI Service Integration
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, AsyncIterator

from src.omnix.ports.driven.ai_text_gateway_port import (
    AITextGatewayPort,
    TextGenerationRequest,
    TextGenerationResponse,
    ModelInfo,
    ModelProvider,
)

logger = logging.getLogger(__name__)

HTTP_ERROR_MESSAGES = {
    400: "Bad request - prompt may be invalid",
    401: "API key invalid or expired",
    403: "Access denied - verify API permissions",
    404: "Model not found or unavailable",
    429: "Rate limit exceeded - quota exhausted",
    500: "Provider internal error",
    503: "Provider temporarily unavailable",
}


def _extract_http_status(error: Exception) -> tuple[int, str]:
    """
    Extract HTTP status code and message from various exception types.
    
    Returns:
        Tuple of (http_code, error_message). http_code is 0 if not HTTP-related.
    """
    error_str = str(error)
    
    if hasattr(error, 'status_code'):
        code = error.status_code
        msg = HTTP_ERROR_MESSAGES.get(code, f"HTTP {code} error")
        return code, msg
    
    if hasattr(error, 'response') and hasattr(error.response, 'status_code'):
        code = error.response.status_code
        msg = HTTP_ERROR_MESSAGES.get(code, f"HTTP {code} error")
        return code, msg
    
    if hasattr(error, 'code'):
        code = error.code if isinstance(error.code, int) else 0
        if code:
            msg = HTTP_ERROR_MESSAGES.get(code, f"HTTP {code} error")
            return code, msg
    
    for code in [401, 403, 404, 429, 500, 503]:
        if str(code) in error_str:
            return code, HTTP_ERROR_MESSAGES.get(code, f"HTTP {code} error")
    
    return 0, error_str


class AIGatewayShim:
    """
    Compatibility shim that implements AITextGatewayPort.
    
    Wraps GeminiAdapter to provide the same interface as RoutingAIGateway.
    This enables feature flag switching between legacy and V7 AI services.
    
    Translation:
    - TextGenerationRequest.prompt → GeminiAdapter.generate_text(prompt)
    - GeminiAdapter response (str) → TextGenerationResponse
    
    Features:
    - Provider fallback chain (Gemini → OpenAI → Anthropic)
    - Streaming support
    - Request/response telemetry
    - Health monitoring
    """
    
    def __init__(
        self,
        gemini_adapter: Optional[Any] = None,
        primary_provider: ModelProvider = ModelProvider.GEMINI,
        fallback_order: Optional[List[ModelProvider]] = None,
        max_retries: int = 3,
    ):
        """
        Initialize the AI Gateway Shim.
        
        Args:
            gemini_adapter: GeminiAdapter instance (lazy-loaded if None)
            primary_provider: Primary AI provider to use
            fallback_order: Order of providers for failover
            max_retries: Maximum retry attempts
        """
        self._gemini_adapter = gemini_adapter
        self._primary_provider = primary_provider
        self._fallback_order = fallback_order or [
            ModelProvider.GEMINI,
            ModelProvider.OPENAI,
            ModelProvider.ANTHROPIC,
        ]
        self._max_retries = max_retries
        
        self._request_count = 0
        self._error_count = 0
        self._last_request: Optional[datetime] = None
        self._provider_used: ModelProvider = primary_provider
    
    def _get_adapter(self) -> Optional[Any]:
        """Lazy-load GeminiAdapter."""
        if self._gemini_adapter is not None:
            return self._gemini_adapter
        
        try:
            from src.omnix.infrastructure.adapters.gemini_adapter import GeminiAdapter
            self._gemini_adapter = GeminiAdapter()
            logger.info("AIGatewayShim: GeminiAdapter loaded")
            return self._gemini_adapter
        except ImportError as e:
            logger.warning(f"AIGatewayShim: GeminiAdapter not available: {e}")
            return None
        except Exception as e:
            logger.error(f"AIGatewayShim: Failed to load GeminiAdapter: {e}")
            return None
    
    def _build_prompt(self, request: TextGenerationRequest) -> str:
        """Build full prompt from request, including system prompt if provided."""
        if request.system_prompt:
            return f"{request.system_prompt}\n\n{request.prompt}"
        return request.prompt
    
    async def generate_text(
        self,
        request: TextGenerationRequest
    ) -> TextGenerationResponse:
        """
        Generate text using GeminiAdapter.
        
        Translates TextGenerationRequest to prompt-based call and wraps
        the response in TextGenerationResponse.
        """
        self._request_count += 1
        self._last_request = datetime.utcnow()
        start_time = time.time()
        
        adapter = self._get_adapter()
        if adapter is None:
            self._error_count += 1
            return TextGenerationResponse(
                content="",
                provider_used=self._primary_provider,
                model_used="unknown",
                success=False,
                error_message="AI adapter not available"
            )
        
        prompt = self._build_prompt(request)
        
        try:
            response_text = await adapter.generate_text(
                prompt=prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            latency_ms = (time.time() - start_time) * 1000
            provider_name = getattr(adapter, '_provider_name', 'gemini')
            self._provider_used = ModelProvider(provider_name) if provider_name in ['gemini', 'openai', 'anthropic'] else ModelProvider.GEMINI
            
            return TextGenerationResponse(
                content=response_text,
                provider_used=self._provider_used,
                model_used=adapter.get_model_info().get('name', 'gemini-2.0-flash'),
                latency_ms=latency_ms,
                success=True,
                metadata={
                    'user_id': request.user_id,
                    'adapter': 'GeminiAdapter'
                }
            )
            
        except Exception as e:
            self._error_count += 1
            latency_ms = (time.time() - start_time) * 1000
            
            http_code, http_msg = _extract_http_status(e)
            
            if http_code:
                logger.error(
                    f"❌ AIGatewayShim [Gemini] HTTP {http_code}: {http_msg}\n"
                    f"   Provider: {self._primary_provider.value}\n"
                    f"   Full error: {e}"
                )
            else:
                logger.error(f"❌ AIGatewayShim: generate_text error: {e}")
            
            logger.warning(
                f"⚠️ FALLBACK CHAIN: Gemini failed → "
                f"(OpenAI/Anthropic fallback not yet implemented in V7 shim)"
            )
            
            return TextGenerationResponse(
                content="",
                provider_used=self._primary_provider,
                model_used="unknown",
                latency_ms=latency_ms,
                success=False,
                error_message=f"[HTTP {http_code}] {http_msg}" if http_code else str(e),
                metadata={
                    'http_code': http_code,
                    'provider_failed': self._primary_provider.value,
                }
            )
    
    async def generate_text_stream(
        self,
        request: TextGenerationRequest
    ) -> AsyncIterator[str]:
        """
        Stream text response from AI model.
        
        Note: If GeminiAdapter doesn't support streaming natively,
        this falls back to generating the full response and yielding it.
        """
        self._request_count += 1
        self._last_request = datetime.utcnow()
        
        adapter = self._get_adapter()
        if adapter is None:
            self._error_count += 1
            yield "[Error: AI adapter not available]"
            return
        
        prompt = self._build_prompt(request)
        
        try:
            if hasattr(adapter, 'generate_text_stream'):
                async for chunk in adapter.generate_text_stream(
                    prompt=prompt,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature
                ):
                    yield chunk
            else:
                response_text = await adapter.generate_text(
                    prompt=prompt,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature
                )
                yield response_text
                
        except Exception as e:
            self._error_count += 1
            http_code, http_msg = _extract_http_status(e)
            
            if http_code:
                logger.error(
                    f"❌ AIGatewayShim [Gemini] STREAM HTTP {http_code}: {http_msg}\n"
                    f"   Provider: {self._primary_provider.value}\n"
                    f"   Full error: {e}"
                )
            else:
                logger.error(f"❌ AIGatewayShim: generate_text_stream error: {e}")
            
            error_text = f"[HTTP {http_code}] {http_msg}" if http_code else str(e)
            yield f"[Error: {error_text}]"
    
    def get_available_models(self) -> List[ModelInfo]:
        """Get list of available AI models."""
        models = []
        
        for provider in self._fallback_order:
            if self.is_provider_available(provider):
                model_name = {
                    ModelProvider.GEMINI: "gemini-2.0-flash",
                    ModelProvider.OPENAI: "gpt-4o",
                    ModelProvider.ANTHROPIC: "claude-3-sonnet",
                }.get(provider, "unknown")
                
                models.append(ModelInfo(
                    provider=provider,
                    model_name=model_name,
                    max_tokens=4096,
                    supports_streaming=True,
                ))
        
        return models
    
    def is_provider_available(self, provider: ModelProvider) -> bool:
        """Check if a specific provider is configured and available."""
        adapter = self._get_adapter()
        if adapter is None:
            return False
        
        providers = getattr(adapter, '_providers', {})
        return provider.value in providers
    
    def get_primary_provider(self) -> ModelProvider:
        """Get the primary/default AI provider."""
        return self._primary_provider
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of AI gateway and providers."""
        adapter = self._get_adapter()
        
        if adapter is None:
            return {
                'healthy': False,
                'providers': {},
                'primary_provider': self._primary_provider.value,
                'request_count': self._request_count,
                'error_count': self._error_count,
            }
        
        adapter_health = adapter.health_check() if hasattr(adapter, 'health_check') else {}
        
        return {
            'healthy': True,
            'providers': {p.value: self.is_provider_available(p) for p in self._fallback_order},
            'primary_provider': self._primary_provider.value,
            'request_count': self._request_count,
            'error_count': self._error_count,
            'adapter_health': adapter_health,
        }


def get_ai_gateway_shim() -> AIGatewayShim:
    """Factory function to create AIGatewayShim instance."""
    return AIGatewayShim()
