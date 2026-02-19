"""
OMNIX Decision Governance - Prompt Builder

Concrete implementation of PromptBuilderProtocol.
Delegates to existing PromptsContextManager for backward compatibility.

Part of Phase 2: Complete DI Container (AI Service Refactoring Roadmap)
"""

from typing import Dict, List, Any, Optional, TYPE_CHECKING
from omnix_core.utils.logger import get_logger
from omnix_services.ai_service.interfaces.prompt_builder import (
    PromptBuilderProtocol,
    PromptContext,
    UserIntent,
)

if TYPE_CHECKING:
    from omnix_services.ai_service.ai_prompts import PromptsContextManager

logger = get_logger(__name__)


INTENT_INSTRUCTIONS = {
    UserIntent.GREETING: """Respond in a friendly and professional manner.
Briefly mention your availability for market analysis.
Keep the response short (2-3 sentences).""",

    UserIntent.MARKET_ANALYSIS: """You are a senior quantitative analyst at OMNIX Decision Governance.

ACTIVE ANALYSIS ENGINES:
- Monte Carlo Simulation (10,000 iterations)
- Black Swan Detection (tail risk)
- HMM Regime Analysis (market state)
- Kalman Filter (noise reduction)
- Non-Markovian Memory Kernel (temporal patterns)

RESPONSE FORMAT:
1. Executive Summary (2 lines)
2. Technical Analysis with REAL data from context
3. Identified Risks
4. Clear Recommendation (LONG / SHORT / NEUTRAL)

CRITICAL: Use ONLY real data from the provided context.
NEVER invent prices, percentages or market data.""",

    UserIntent.TRADING_QUERY: """You are an institutional trade executor.

BEFORE CONFIRMING ANY TRADE:
1. Verify the exact symbol (BTC, ETH, etc.)
2. Confirm the amount in USD
3. Show current market price
4. Show estimated fees

NEVER execute a trade without explicit user confirmation.""",

    UserIntent.PORTFOLIO: """You are an institutional portfolio manager.

DISPLAY:
- Current balance by asset
- Total and per-position P&L
- Risk exposure metrics
- Rebalancing suggestions (if applicable)

Use data from the provided context.
Format numbers clearly with currency symbols.""",

    UserIntent.HELP: """You are an OMNIX system guide.

MAIN COMMANDS:
/autotrading start|stop|status - Automated trading bot
/paper_buy BTC 100 - Simulated purchase ($100 of BTC)
/paper_sell ETH 50 - Simulated sale
/balance - View current balance
/analysis BTC - Technical analysis

Respond concisely with clear examples.""",

    UserIntent.GENERAL: """You are a conversational assistant.
Maintain trading context but allow casual conversation.
If you detect an opportunity to offer market analysis, suggest it subtly.
Keep responses friendly and professional.""",

    UserIntent.VIDEO_ANALYSIS: """You are a financial video/image analyzer.
Examine the provided visual content.
Identify charts, technical indicators, price levels.
Provide analysis based on what you observe.""",

    UserIntent.NEWS: """You are a financial news analyst.
Synthesize relevant market news.
Identify potential impact on prices.
Cite sources when possible.""",

    UserIntent.TECHNICAL: """You are a technical analysis expert.
Explain technical concepts clearly.
Use practical examples when useful.
Adapt complexity to the user's level."""
}


class OmnixPromptBuilder:
    """
    Concrete implementation of PromptBuilderProtocol.
    
    Wraps the existing PromptsContextManager while providing
    a clean interface that follows the protocol contract.
    
    This allows gradual migration to the new DI-based architecture
    while maintaining backward compatibility.
    """
    
    def __init__(self, prompts_manager: Optional["PromptsContextManager"] = None):
        """
        Initialize with optional PromptsContextManager.
        
        Args:
            prompts_manager: Existing prompts manager to delegate to.
                           If None, will be lazy-loaded.
        """
        self._prompts_manager = prompts_manager
        self._initialized = False
        logger.info("OmnixPromptBuilder created (lazy initialization)")
    
    def _ensure_initialized(self) -> None:
        """Lazy initialization of prompts manager."""
        if self._initialized:
            return
        
        if self._prompts_manager is None:
            try:
                from omnix_services.ai_service.ai_prompts import PromptsContextManager
                self._prompts_manager = PromptsContextManager()
                logger.info("PromptsContextManager loaded")
            except ImportError as e:
                logger.error(f"Failed to load PromptsContextManager: {e}")
        
        self._initialized = True
    
    def analyze_intent(self, message: str) -> UserIntent:
        """
        Analyze user message to determine intent.
        
        Delegates to PromptsContextManager.analyze_intent() and maps
        the string result to UserIntent enum.
        """
        self._ensure_initialized()
        
        if self._prompts_manager is None:
            return UserIntent.GENERAL
        
        try:
            intent_str = self._prompts_manager.analyze_intent(message)
            
            intent_mapping = {
                "greeting": UserIntent.GREETING,
                "market_analysis": UserIntent.MARKET_ANALYSIS,
                "trading_query": UserIntent.TRADING_QUERY,
                "trading": UserIntent.TRADING_QUERY,
                "portfolio": UserIntent.PORTFOLIO,
                "help": UserIntent.HELP,
                "general": UserIntent.GENERAL,
                "video_analysis": UserIntent.VIDEO_ANALYSIS,
                "news": UserIntent.NEWS,
                "technical": UserIntent.TECHNICAL,
            }
            
            return intent_mapping.get(intent_str.lower(), UserIntent.GENERAL)
            
        except Exception as e:
            logger.error(f"Error analyzing intent: {e}")
            return UserIntent.GENERAL
    
    def build_system_prompt(
        self,
        context: PromptContext
    ) -> str:
        """
        Build complete system prompt with all context.
        
        Combines:
        - Base system instructions
        - Intent-specific instructions
        - Market data context
        - Trading context
        - Web search results
        """
        self._ensure_initialized()
        
        parts = []
        
        parts.append("You are OMNIX, the Decision Governance Infrastructure assistant for automated trading systems.")
        parts.append(f"\nUser: {context.user_name}")
        
        intent_instructions = self.get_intent_specific_instructions(context.intent)
        if intent_instructions:
            parts.append(f"\n{intent_instructions}")
        
        if context.real_context_data:
            parts.append("\n\n## SYSTEM CONTEXT:")
            parts.append(self._format_context_data(context.real_context_data))
        
        if context.market_data:
            parts.append("\n\n## REAL-TIME MARKET DATA:")
            parts.append(self._format_market_data(context.market_data))
        
        if context.trading_context:
            parts.append("\n\n## TRADING CONTEXT:")
            parts.append(self._format_trading_context(context.trading_context))
        
        if context.web_search_results:
            parts.append("\n\n## WEB SEARCH RESULTS:")
            parts.append(context.web_search_results)
        
        parts.append("\n\n## LANGUAGE POLICY [CRITICAL]\nALWAYS respond in the SAME language the user writes their message. Maintain a professional but accessible tone.")
        
        return "\n".join(parts)
    
    def build_user_prompt(
        self,
        context: PromptContext
    ) -> str:
        """
        Build formatted user prompt.
        
        Includes conversation history for context continuity.
        """
        self._ensure_initialized()
        
        parts = []
        
        if context.conversation_history:
            truncated = self.truncate_history(context.conversation_history)
            if truncated:
                parts.append("Recent conversation history:")
                for msg in truncated:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")[:200]
                    parts.append(f"[{role}]: {content}")
                parts.append("")
        
        parts.append(f"Current user message: {context.user_message}")
        
        return "\n".join(parts)
    
    def get_intent_specific_instructions(
        self,
        intent: UserIntent
    ) -> str:
        """Get specialized instructions for a specific intent."""
        return INTENT_INSTRUCTIONS.get(intent, INTENT_INSTRUCTIONS[UserIntent.GENERAL])
    
    def truncate_history(
        self,
        history: List[Dict[str, str]],
        max_messages: int = 10
    ) -> List[Dict[str, str]]:
        """Truncate conversation history to fit context window."""
        if not history:
            return []
        
        return history[-max_messages:]
    
    def _format_context_data(self, data: Dict[str, Any]) -> str:
        """Format real context data for inclusion in prompt."""
        if not data:
            return "No disponible"
        
        lines = []
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"- {key}:")
                for k, v in value.items():
                    lines.append(f"  - {k}: {v}")
            else:
                lines.append(f"- {key}: {value}")
        
        return "\n".join(lines)
    
    def _format_market_data(self, data: Dict[str, Any]) -> str:
        """Format market data for inclusion in prompt."""
        if not data:
            return "No disponible"
        
        lines = []
        for symbol, info in data.items():
            if isinstance(info, dict):
                price = info.get("price", "N/A")
                change = info.get("change_24h", "N/A")
                lines.append(f"- {symbol}: ${price} ({change}% 24h)")
            else:
                lines.append(f"- {symbol}: {info}")
        
        return "\n".join(lines) if lines else "No disponible"
    
    def _format_trading_context(self, data: Dict[str, Any]) -> str:
        """Format trading context for inclusion in prompt."""
        if not data:
            return "No disponible"
        
        lines = []
        
        if "positions" in data:
            lines.append("Posiciones abiertas:")
            for pos in data["positions"]:
                lines.append(f"  - {pos}")
        
        if "balance" in data:
            lines.append(f"Balance: ${data['balance']}")
        
        if "pnl" in data:
            lines.append(f"P&L: ${data['pnl']}")
        
        return "\n".join(lines) if lines else "No disponible"
