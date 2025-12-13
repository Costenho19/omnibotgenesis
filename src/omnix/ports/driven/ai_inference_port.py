"""
OMNIX AI Inference Port - LLM Interface Contract

This Protocol defines the contract for AI model inference.
All methods are ASYNC for optimal performance with network I/O.

SOLID Principles:
- SRP: Only AI inference operations
- ISP: Minimal interface for LLM interactions
- DIP: Depend on this abstraction, not specific providers
"""

from typing import Protocol, Optional, List, Dict, Any, runtime_checkable


@runtime_checkable
class AIInferencePort(Protocol):
    """
    Contract for AI model inference (Gemini, OpenAI, Claude).
    
    Implementations:
    - omnix_services.ai_service.providers.gemini_provider.GeminiProvider
    - omnix_services.ai_service.providers.openai_provider.OpenAIProvider
    - omnix_services.ai_service.providers.anthropic_provider.AnthropicProvider
    """
    
    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum response tokens
            temperature: Creativity (0.0-1.0)
            
        Returns:
            Generated text response
        """
        ...
    
    async def analyze_market(
        self,
        market_data: Dict[str, Any],
        context: str = ""
    ) -> Dict[str, Any]:
        """
        Analyze market data and return insights.
        
        Args:
            market_data: OHLCV, indicators, sentiment data
            context: Additional context for analysis
            
        Returns:
            Dict with:
            - analysis: str
            - sentiment: str ('bullish', 'bearish', 'neutral')
            - confidence: float (0.0-1.0)
            - key_points: List[str]
        """
        ...
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Multi-turn conversation.
        
        Args:
            messages: List of {'role': 'user'/'assistant', 'content': str}
            system_prompt: Optional system instructions
            
        Returns:
            Assistant response
        """
        ...
    
    def get_model_info(self) -> Dict[str, str]:
        """
        Get model name and version.
        
        Returns:
            Dict with:
            - name: str (e.g., 'gemini-2.0-flash')
            - provider: str (e.g., 'google')
            - version: str
        """
        ...
