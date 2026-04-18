"""
OMNIX V7.0 AI Gateway Compatibility Shim
=========================================
Bridges V7 Hexagonal Architecture with Legacy AIModelsManager.

ARCHITECTURE DECISION (Dec 16, 2025):
This shim is a PURE ADAPTER that delegates to the legacy AIModelsManager,
which contains all the production-tested logic:
- Multi-provider failover (Gemini → OpenAI → Anthropic)
- Intelligent error classification (retryable vs non-retryable)
- Adaptive timeouts (Gemini 20s, OpenAI 15s, Anthropic 15s)
- Exponential backoff for rate limits

The shim ONLY translates between:
- V7 TextGenerationRequest/Response ↔ Legacy prompt/response format

This follows the Strangler Fig pattern: new interface wraps legacy implementation.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, AsyncIterator, Union

from src.omnix.ports.driven.ai_text_gateway_port import (
    AITextGatewayPort,
    TextGenerationRequest,
    TextGenerationResponse,
    ModelInfo,
    ModelProvider,
)

logger = logging.getLogger(__name__)


class AIGatewayShim:
    """
    Compatibility shim that implements AITextGatewayPort.
    
    DELEGATES to legacy AIModelsManager for actual AI generation.
    This ensures USE_AI_PORT=true uses the same proven failover logic
    as the legacy system.
    
    Translation:
    - TextGenerationRequest → AIModelsManager.generate(prompt, system_prompt)
    - AIModelsManager response (str) → TextGenerationResponse
    """
    
    def __init__(
        self,
        ai_models_manager: Optional[Any] = None,
        primary_provider: ModelProvider = ModelProvider.GEMINI,
    ):
        """
        Initialize the AI Gateway Shim.
        
        Args:
            ai_models_manager: Legacy AIModelsManager instance (lazy-loaded if None)
            primary_provider: Primary AI provider (for metadata only)
        """
        self._ai_models_manager = ai_models_manager
        self._primary_provider = primary_provider
        
        self._request_count = 0
        self._error_count = 0
        self._success_count = 0
        self._last_request: Optional[datetime] = None
        self._provider_used: ModelProvider = primary_provider
        self._initialized = False
    
    def _get_manager(self) -> Optional[Any]:
        """
        Get the injected AIModelsManager (NO lazy initialization).
        
        This method only returns the manager if it was explicitly injected
        during construction. It does NOT create a new manager to avoid
        violating the container's cooldown mechanism.
        
        The container is responsible for injecting the manager when creating
        the shim. If no manager was injected, returns None and the shim
        reports unhealthy, triggering fallback to RoutingAIGateway.
        """
        return self._ai_models_manager
    
    def _build_prompt(self, request: TextGenerationRequest) -> tuple[str, str]:
        """
        Extract prompt and system_prompt from request.
        
        Returns:
            Tuple of (prompt, system_prompt)
        """
        return request.prompt, request.system_prompt or ""
    
    def _determine_provider_used(self, manager: Any) -> ModelProvider:
        """Determine which provider was actually used from manager state."""
        if hasattr(manager, 'last_provider_used'):
            provider_name = manager.last_provider_used
            if 'gemini' in provider_name.lower():
                return ModelProvider.GEMINI
            elif 'gpt' in provider_name.lower() or 'openai' in provider_name.lower():
                return ModelProvider.OPENAI
            elif 'claude' in provider_name.lower() or 'anthropic' in provider_name.lower():
                return ModelProvider.ANTHROPIC
        return self._primary_provider
    
    async def generate_text(
        self,
        request: TextGenerationRequest
    ) -> TextGenerationResponse:
        """
        Generate text by delegating to legacy AIModelsManager.
        
        The AIModelsManager handles:
        - Provider selection and failover
        - Error classification and retry logic
        - Timeout management
        - Response validation
        """
        self._request_count += 1
        self._last_request = datetime.utcnow()
        start_time = time.time()
        
        manager = self._get_manager()
        if manager is None:
            self._error_count += 1
            return TextGenerationResponse(
                content="",
                provider_used=self._primary_provider,
                model_used="unknown",
                success=False,
                error_message="AIModelsManager not available - check legacy service initialization"
            )
        
        prompt, system_prompt = self._build_prompt(request)
        
        try:
            response_text = await manager.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                max_retries=3
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            if response_text:
                self._success_count += 1
                self._provider_used = self._determine_provider_used(manager)
                
                model_name = "gemini-2.0-flash"
                if self._provider_used == ModelProvider.OPENAI:
                    model_name = "gpt-4o"
                elif self._provider_used == ModelProvider.ANTHROPIC:
                    model_name = "claude-sonnet-4"
                
                return TextGenerationResponse(
                    content=response_text,
                    provider_used=self._provider_used,
                    model_used=model_name,
                    latency_ms=latency_ms,
                    success=True,
                    metadata={
                        'user_id': request.user_id,
                        'adapter': 'AIGatewayShim',
                        'backend': 'AIModelsManager'
                    }
                )
            else:
                self._error_count += 1
                return TextGenerationResponse(
                    content="",
                    provider_used=self._primary_provider,
                    model_used="unknown",
                    latency_ms=latency_ms,
                    success=False,
                    error_message="All AI providers failed - check Railway logs for diagnostics",
                    metadata={
                        'adapter': 'AIGatewayShim',
                        'hint': 'Verify API keys: GEMINI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY'
                    }
                )
                
        except Exception as e:
            self._error_count += 1
            latency_ms = (time.time() - start_time) * 1000
            
            logger.error(f"❌ AIGatewayShim.generate_text exception: {e}")
            
            return TextGenerationResponse(
                content="",
                provider_used=self._primary_provider,
                model_used="unknown",
                latency_ms=latency_ms,
                success=False,
                error_message=str(e),
                metadata={
                    'adapter': 'AIGatewayShim',
                    'exception_type': type(e).__name__
                }
            )
    
    async def generate_text_stream(
        self,
        request: TextGenerationRequest
    ) -> AsyncIterator[str]:
        """
        Stream text response from AI model.
        
        Note: AIModelsManager doesn't support native streaming,
        so we generate the full response and yield it.
        """
        self._request_count += 1
        self._last_request = datetime.utcnow()
        
        response = await self.generate_text(request)
        
        if response.success:
            yield response.content
        else:
            yield f"[Error: {response.error_message}]"
    
    def get_available_models(self) -> List[ModelInfo]:
        """Get list of available AI models."""
        manager = self._get_manager()
        models = []
        
        if manager:
            if hasattr(manager, 'openai_client') and manager.openai_client:
                models.append(ModelInfo(
                    provider=ModelProvider.OPENAI,
                    model_name="gpt-4o",
                    max_tokens=4096,
                    supports_streaming=True,
                ))
            
            if hasattr(manager, 'gemini_client') and manager.gemini_client:
                models.append(ModelInfo(
                    provider=ModelProvider.GEMINI,
                    model_name="gemini-2.0-flash",
                    max_tokens=8000,
                    supports_streaming=True,
                ))
            
            if hasattr(manager, 'anthropic_client') and manager.anthropic_client:
                models.append(ModelInfo(
                    provider=ModelProvider.ANTHROPIC,
                    model_name="claude-sonnet-4",
                    max_tokens=4000,
                    supports_streaming=True,
                ))
        
        return models
    
    def is_provider_available(self, provider: ModelProvider) -> bool:
        """Check if a specific provider is configured and available."""
        manager = self._get_manager()
        if not manager:
            return False
        
        if provider == ModelProvider.OPENAI:
            return hasattr(manager, 'openai_client') and manager.openai_client is not None
        elif provider == ModelProvider.GEMINI:
            return hasattr(manager, 'gemini_client') and manager.gemini_client is not None
        elif provider == ModelProvider.ANTHROPIC:
            return hasattr(manager, 'anthropic_client') and manager.anthropic_client is not None
        
        return False
    
    def get_primary_provider(self) -> ModelProvider:
        """Get the primary/default AI provider."""
        return self._primary_provider
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check health of AI gateway and providers.
        
        Reports healthy=True only if manager is available AND at least one
        provider has a valid client. This ensures the container can fallback
        to legacy gateway if the shim is unhealthy.
        """
        manager = self._get_manager()
        
        if manager is None:
            return {
                'healthy': False,
                'initialized': False,
                'backend': 'AIModelsManager (not available)',
                'providers': {'gemini': False, 'openai': False, 'anthropic': False},
                'primary_provider': self._primary_provider.value,
                'request_count': self._request_count,
                'success_count': self._success_count,
                'error_count': self._error_count,
                'error_rate': self._error_count / max(self._request_count, 1),
                'last_request': self._last_request.isoformat() if self._last_request else None,
            }
        
        providers_status = {}
        for provider in [ModelProvider.GEMINI, ModelProvider.OPENAI, ModelProvider.ANTHROPIC]:
            providers_status[provider.value] = self.is_provider_available(provider)
        
        at_least_one_available = any(providers_status.values())
        error_rate = self._error_count / max(self._request_count, 1)
        too_many_errors = error_rate > 0.8 and self._request_count >= 5
        
        healthy = at_least_one_available and not too_many_errors
        
        return {
            'healthy': healthy,
            'initialized': self._initialized,
            'backend': 'AIModelsManager (legacy with full failover)',
            'providers': providers_status,
            'providers_count': sum(1 for v in providers_status.values() if v),
            'primary_provider': self._primary_provider.value,
            'request_count': self._request_count,
            'success_count': self._success_count,
            'error_count': self._error_count,
            'success_rate': self._success_count / max(self._request_count, 1),
            'error_rate': error_rate,
            'last_request': self._last_request.isoformat() if self._last_request else None,
        }


def get_ai_gateway_shim(ai_models_manager: Optional[Any] = None) -> AIGatewayShim:
    """Factory function to create AIGatewayShim instance."""
    return AIGatewayShim(ai_models_manager=ai_models_manager)
