"""
OMNIX V7.0 Gemini Infrastructure Adapter

Implements AIInferencePort protocol by wrapping the legacy
AI service providers. Provides fallback chain, telemetry,
and structured error handling.

Phase 3: Interfaces Migration
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


class GeminiAdapter:
    """
    Infrastructure adapter for Gemini AI (primary) with fallbacks.
    
    Implements AIInferencePort:
    - generate_text: Text generation from prompt
    - analyze_market: Market analysis with structured output
    - chat: Multi-turn conversation
    - get_model_info: Model metadata
    
    Features:
    - Primary: Google Gemini 2.0 Flash
    - Fallback chain: Gemini -> OpenAI -> Anthropic -> Legacy AI Service
    - Telemetry and request tracking
    - Rate limiting awareness
    - Structured error handling
    """
    
    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        max_retries: int = 3,
        timeout: float = 30.0
    ):
        """
        Initialize Gemini adapter with fallback chain.
        
        Args:
            gemini_api_key: Gemini API key (uses settings if None)
            openai_api_key: OpenAI API key for fallback
            anthropic_api_key: Anthropic API key for fallback
            max_retries: Maximum retry attempts
            timeout: Request timeout in seconds
        """
        self._gemini_key = gemini_api_key
        self._openai_key = openai_api_key
        self._anthropic_key = anthropic_api_key
        self._max_retries = max_retries
        self._timeout = timeout
        
        self._providers: Dict[str, Any] = {}
        self._failed_providers: Dict[str, datetime] = {}
        self._provider_order = ["gemini", "openai", "anthropic", "legacy"]
        self._provider_name = "unknown"
        self._request_count = 0
        self._error_count = 0
        self._fallback_count = 0
        self._last_request: Optional[datetime] = None
        self._provider_recovery_seconds = 300
    
    def _is_provider_recovered(self, name: str) -> bool:
        """Check if a failed provider has had time to recover."""
        if name not in self._failed_providers:
            return True
        
        failed_at = self._failed_providers[name]
        recovery_time = (datetime.utcnow() - failed_at).total_seconds()
        return recovery_time >= self._provider_recovery_seconds
    
    def _mark_provider_failed(self, name: str):
        """Mark a provider as failed with timestamp."""
        self._failed_providers[name] = datetime.utcnow()
        if name in self._providers:
            del self._providers[name]
        logger.warning(f"GeminiAdapter: {name} marked as failed, will retry in {self._provider_recovery_seconds}s")
    
    def _init_provider(self, name: str) -> Optional[Any]:
        """Initialize a specific provider by name."""
        if not self._is_provider_recovered(name):
            return None
        
        if name in self._providers:
            return self._providers[name]
        
        try:
            if name == "gemini":
                from omnix_services.ai_service.providers.gemini_provider import GeminiProvider
                self._providers[name] = GeminiProvider()
                logger.info("GeminiAdapter: Gemini provider initialized")
            elif name == "openai":
                from omnix_services.ai_service.providers.openai_provider import OpenAIProvider
                self._providers[name] = OpenAIProvider()
                logger.info("GeminiAdapter: OpenAI provider initialized")
            elif name == "anthropic":
                from omnix_services.ai_service.providers.anthropic_provider import AnthropicProvider
                self._providers[name] = AnthropicProvider()
                logger.info("GeminiAdapter: Anthropic provider initialized")
            elif name == "legacy":
                self._providers[name] = self._create_legacy_fallback()
                logger.info("GeminiAdapter: Legacy fallback initialized")
            
            if name in self._failed_providers:
                del self._failed_providers[name]
                logger.info(f"GeminiAdapter: {name} provider recovered")
            
            return self._providers.get(name)
        except Exception as e:
            logger.warning(f"GeminiAdapter: {name} provider failed to initialize: {e}")
            self._mark_provider_failed(name)
            return None
    
    def _get_available_providers(self) -> List[str]:
        """Get ordered list of providers available for this request."""
        available = []
        for name in self._provider_order:
            if self._is_provider_recovered(name) or name == "legacy":
                available.append(name)
        return available if available else ["legacy"]
    
    async def _call_with_fallback(
        self,
        method_name: str,
        call_fn: Callable[[Any], T],
        fallback_value: T
    ) -> T:
        """
        Call provider method with runtime fallback cascade.
        
        If current provider fails, tries next provider in chain.
        Providers recover after _provider_recovery_seconds.
        
        Args:
            method_name: Name for logging
            call_fn: Async function that takes provider and returns result
            fallback_value: Value to return if all providers fail
            
        Returns:
            Result from successful provider or fallback_value
        """
        available_providers = self._get_available_providers()
        
        for provider_name in available_providers:
            provider = self._init_provider(provider_name)
            if provider is None:
                continue
            
            self._provider_name = provider_name
            
            try:
                result = await call_fn(provider)
                return result
            except Exception as e:
                self._error_count += 1
                self._fallback_count += 1
                logger.warning(
                    f"GeminiAdapter.{method_name} failed with {provider_name}: {e}"
                )
                
                self._mark_provider_failed(provider_name)
                
                if provider_name != "legacy":
                    logger.info(
                        f"GeminiAdapter.{method_name}: Falling back to next provider"
                    )
        
        logger.error(f"GeminiAdapter.{method_name}: All providers exhausted")
        return fallback_value
    
    def _create_legacy_fallback(self):
        """Create legacy AI service fallback wrapper."""
        class LegacyFallback:
            async def generate(self, prompt: str, **kwargs) -> str:
                try:
                    from omnix_services.ai_service.ai_service import ConversationalAIService
                    service = ConversationalAIService()
                    response = await service.generate_response(
                        chat_id=0,
                        user_message=prompt,
                        user_name="System"
                    )
                    if isinstance(response, dict):
                        return response.get("response", str(response))
                    return str(response) if response else ""
                except Exception as e:
                    return f"AI service unavailable: {e}"
            
            async def chat(self, messages: list, system_prompt: str = "") -> str:
                prompt = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in messages])
                return await self.generate(prompt)
            
            async def generate_text(self, prompt: str, **kwargs) -> str:
                return await self.generate(prompt, **kwargs)
        
        return LegacyFallback()
    
    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text from prompt (AIInferencePort).
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum response tokens
            temperature: Creativity (0.0-1.0)
            
        Returns:
            Generated text response
        """
        self._request_count += 1
        self._last_request = datetime.utcnow()
        
        async def _call_provider(provider) -> str:
            if hasattr(provider, 'generate'):
                result = await provider.generate(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return result if isinstance(result, str) else str(result)
            elif hasattr(provider, 'generate_text'):
                result = await provider.generate_text(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return result if isinstance(result, str) else str(result)
            else:
                raise AttributeError("Provider has no generate method")
        
        return await self._call_with_fallback(
            "generate_text",
            _call_provider,
            f"Error: All AI providers failed"
        )
    
    
    async def analyze_market(
        self,
        market_data: Dict[str, Any],
        context: str = ""
    ) -> Dict[str, Any]:
        """
        Analyze market data and return insights (AIInferencePort).
        
        Args:
            market_data: OHLCV, indicators, sentiment data
            context: Additional context for analysis
            
        Returns:
            Analysis result dictionary
        """
        self._request_count += 1
        self._last_request = datetime.utcnow()
        
        try:
            prompt = self._build_market_analysis_prompt(market_data, context)
            
            response = await self.generate_text(
                prompt=prompt,
                max_tokens=1500,
                temperature=0.3
            )
            
            return self._parse_market_analysis(response, market_data)
            
        except Exception as e:
            self._error_count += 1
            logger.error(f"GeminiAdapter.analyze_market failed: {e}")
            return {
                "analysis": f"Analysis failed: {e}",
                "sentiment": "neutral",
                "confidence": 0.0,
                "key_points": []
            }
    
    def _build_market_analysis_prompt(
        self,
        market_data: Dict[str, Any],
        context: str
    ) -> str:
        """Build structured prompt for market analysis."""
        symbol = market_data.get("symbol", "Unknown")
        price = market_data.get("price", 0)
        change_24h = market_data.get("change_24h", 0)
        volume = market_data.get("volume", 0)
        rsi = market_data.get("rsi", 50)
        
        return f"""Analyze the following market data for {symbol}:

Current Price: ${price:,.2f}
24h Change: {change_24h:+.2f}%
Volume: ${volume:,.0f}
RSI: {rsi:.1f}

{context}

Provide:
1. Brief analysis (2-3 sentences)
2. Sentiment (bullish/bearish/neutral)
3. Confidence level (0-100%)
4. Key points (3 bullet points)

Format your response clearly with labeled sections."""
    
    def _parse_market_analysis(
        self,
        response: str,
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse AI response into structured analysis."""
        response_lower = response.lower()
        
        if "bullish" in response_lower:
            sentiment = "bullish"
        elif "bearish" in response_lower:
            sentiment = "bearish"
        else:
            sentiment = "neutral"
        
        confidence = 0.5
        if "high confidence" in response_lower or "strongly" in response_lower:
            confidence = 0.8
        elif "low confidence" in response_lower or "uncertain" in response_lower:
            confidence = 0.3
        
        lines = response.split("\n")
        key_points = [
            line.strip().lstrip("•-*123. ")
            for line in lines
            if line.strip() and len(line.strip()) > 10
        ][:3]
        
        return {
            "analysis": response[:500],
            "sentiment": sentiment,
            "confidence": confidence,
            "key_points": key_points,
            "symbol": market_data.get("symbol", "Unknown"),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Multi-turn conversation (AIInferencePort).
        
        Args:
            messages: List of {'role': 'user'/'assistant', 'content': str}
            system_prompt: Optional system instructions
            
        Returns:
            Assistant response
        """
        self._request_count += 1
        self._last_request = datetime.utcnow()
        
        async def _call_provider(provider) -> str:
            if hasattr(provider, 'chat'):
                result = await provider.chat(
                    messages=messages,
                    system_prompt=system_prompt or ""
                )
                return result if isinstance(result, str) else str(result)
            else:
                formatted_prompt = self._format_chat_as_prompt(messages, system_prompt)
                return await self.generate_text(formatted_prompt)
        
        return await self._call_with_fallback(
            "chat",
            _call_provider,
            "Error: Chat unavailable"
        )
    
    def _format_chat_as_prompt(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str]
    ) -> str:
        """Format chat messages as single prompt for fallback."""
        parts = []
        
        if system_prompt:
            parts.append(f"System: {system_prompt}\n")
        
        for msg in messages:
            role = msg.get("role", "user").capitalize()
            content = msg.get("content", "")
            parts.append(f"{role}: {content}")
        
        parts.append("Assistant:")
        return "\n".join(parts)
    
    def get_model_info(self) -> Dict[str, str]:
        """
        Get model name and version (AIInferencePort).
        
        Returns:
            Model information dictionary
        """
        provider_models = {
            "gemini": {"name": "gemini-2.0-flash", "provider": "google", "version": "2.0"},
            "openai": {"name": "gpt-4o", "provider": "openai", "version": "4o"},
            "anthropic": {"name": "claude-3-5-sonnet", "provider": "anthropic", "version": "3.5"},
            "legacy": {"name": "legacy-ai-service", "provider": "omnix", "version": "6.5.4d"}
        }
        
        return provider_models.get(self._provider_name, {
            "name": "unknown",
            "provider": "unknown",
            "version": "unknown"
        })
    
    def health_check(self) -> Dict[str, Any]:
        """
        Health check for monitoring.
        
        Returns:
            Health status dictionary (never raises)
        """
        try:
            available_providers = self._get_available_providers()
        except Exception:
            available_providers = []
        
        try:
            cached_providers = list(self._providers.keys())
        except Exception:
            cached_providers = []
        
        try:
            failed_providers = list(self._failed_providers.keys())
        except Exception:
            failed_providers = []
        
        try:
            model_info = self.get_model_info()
        except Exception:
            model_info = {"name": "unknown", "provider": "unknown", "version": "unknown"}
        
        return {
            "adapter": "GeminiAdapter",
            "provider": self._provider_name,
            "initialized": len(cached_providers) > 0,
            "available_providers": available_providers,
            "cached_providers": cached_providers,
            "failed_providers": failed_providers,
            "last_request": self._last_request.isoformat() if self._last_request else None,
            "request_count": self._request_count,
            "error_count": self._error_count,
            "fallback_count": self._fallback_count,
            "error_rate": self._error_count / max(self._request_count, 1),
            "model_info": model_info
        }
