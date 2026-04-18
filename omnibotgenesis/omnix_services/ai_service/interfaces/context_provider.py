"""
OMNIX INSTITUTIONAL+ - Context Provider Protocol

Defines the contract for conversation context and state management.
Abstracts Redis/PostgreSQL storage from business logic.
"""

from typing import Protocol, Optional, Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class ConversationMessage:
    role: str
    content: str
    timestamp: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationContext:
    user_id: str
    messages: List[ConversationMessage] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    market_context: Dict[str, Any] = field(default_factory=dict)
    session_data: Dict[str, Any] = field(default_factory=dict)


class ContextProviderProtocol(Protocol):
    """
    Protocol for conversation context management.
    
    Responsibilities:
    - Store and retrieve conversation history
    - Manage user preferences
    - Provide market context data
    - Handle session state
    """

    def get_conversation_history(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[ConversationMessage]:
        """Get recent conversation messages for user."""
        ...

    def add_message(
        self,
        user_id: str,
        message: ConversationMessage
    ) -> None:
        """Add a message to conversation history."""
        ...

    def clear_history(
        self,
        user_id: str
    ) -> None:
        """Clear conversation history for user."""
        ...

    def get_user_preferences(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Get user preferences."""
        ...

    def set_user_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> None:
        """Set user preferences."""
        ...

    def get_market_context(self) -> Dict[str, Any]:
        """Get current market context data."""
        ...

    def get_full_context(
        self,
        user_id: str
    ) -> ConversationContext:
        """Get complete context for a user."""
        ...
