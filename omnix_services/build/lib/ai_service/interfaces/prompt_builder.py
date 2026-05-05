"""
OMNIX INSTITUTIONAL+ - Prompt Builder Protocol

Defines the contract for prompt construction and context management.
Separates prompt logic from AI model interaction.
"""

from typing import Protocol, Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum


class UserIntent(Enum):
    GREETING = "greeting"
    MARKET_ANALYSIS = "market_analysis"
    TRADING_QUERY = "trading_query"
    PORTFOLIO = "portfolio"
    HELP = "help"
    GENERAL = "general"
    VIDEO_ANALYSIS = "video_analysis"
    NEWS = "news"
    TECHNICAL = "technical"


@dataclass
class PromptContext:
    user_id: str
    user_name: str = "Usuario"
    user_message: str = ""
    intent: UserIntent = UserIntent.GENERAL
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    market_data: Optional[Dict[str, Any]] = None
    trading_context: Optional[Dict[str, Any]] = None
    web_search_results: Optional[str] = None
    real_context_data: Optional[Dict[str, Any]] = None
    additional_context: Dict[str, Any] = field(default_factory=dict)


class PromptBuilderProtocol(Protocol):
    """
    Protocol for prompt construction.
    
    Responsibilities:
    - Analyze user intent
    - Build system prompts with appropriate context
    - Manage conversation history integration
    """

    def analyze_intent(self, message: str) -> UserIntent:
        """Analyze user message to determine intent."""
        ...

    def build_system_prompt(
        self,
        context: PromptContext
    ) -> str:
        """Build complete system prompt with all context."""
        ...

    def build_user_prompt(
        self,
        context: PromptContext
    ) -> str:
        """Build formatted user prompt."""
        ...

    def get_intent_specific_instructions(
        self,
        intent: UserIntent
    ) -> str:
        """Get specialized instructions for a specific intent."""
        ...

    def truncate_history(
        self,
        history: List[Dict[str, str]],
        max_messages: int = 10
    ) -> List[Dict[str, str]]:
        """Truncate conversation history to fit context window."""
        ...
