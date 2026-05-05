"""
OMNIX INSTITUTIONAL+ - Redis Context Provider

Concrete implementation of ContextProviderProtocol.
Uses Redis for fast access, PostgreSQL for persistence.

Part of Phase 2: Complete DI Container (AI Service Refactoring Roadmap)
"""

import time
from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING
from omnix_core.utils.logger import get_logger
from omnix_services.ai_service.interfaces.context_provider import (
    ContextProviderProtocol,
    ConversationContext,
    ConversationMessage,
)

if TYPE_CHECKING:
    from omnix_core.cache.redis_state import RedisConversationHistory, RedisUserPreferences

logger = get_logger(__name__)


def _to_chat_id(user_id: str) -> int:
    """Convert user_id string to chat_id int for Redis API compatibility."""
    try:
        return int(user_id)
    except ValueError:
        return hash(user_id) % (10**9)


class RedisContextProvider:
    """
    Concrete implementation of ContextProviderProtocol.
    
    Delegates to existing Redis/PostgreSQL infrastructure:
    - RedisConversationHistory for message history
    - RedisUserPreferences for user preferences
    - RealContextProvider for market context
    
    This provider acts as a facade, unifying multiple data sources
    into a single coherent interface for the AI service.
    """
    
    def __init__(self):
        self._conversation_history: Optional["RedisConversationHistory"] = None
        self._user_preferences: Optional["RedisUserPreferences"] = None
        self._real_context_provider = None
        self._initialized = False
        logger.info("RedisContextProvider created (lazy initialization)")
    
    def _ensure_initialized(self) -> None:
        """Lazy initialization of dependencies."""
        if self._initialized:
            return
            
        try:
            from omnix_core.cache.redis_state import get_conversation_history
            self._conversation_history = get_conversation_history()
        except ImportError as e:
            logger.warning(f"RedisConversationHistory not available: {e}")
            self._conversation_history = None
        
        try:
            from omnix_core.cache.redis_state import get_user_preferences
            self._user_preferences = get_user_preferences()
        except ImportError as e:
            logger.warning(f"RedisUserPreferences not available: {e}")
            self._user_preferences = None
        
        try:
            from omnix_core.context import get_real_context_provider
            self._real_context_provider = get_real_context_provider()
        except ImportError as e:
            logger.warning(f"RealContextProvider not available: {e}")
            self._real_context_provider = None
        
        self._initialized = True
        logger.info("RedisContextProvider initialized")
    
    def get_conversation_history(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[ConversationMessage]:
        """
        Get recent conversation messages for user.
        
        Delegates to RedisConversationHistory.get_history()
        """
        self._ensure_initialized()
        
        if self._conversation_history is None:
            return []
        
        try:
            chat_id = _to_chat_id(user_id)
            raw_messages = self._conversation_history.get_history(chat_id)
            
            messages = []
            for msg in raw_messages[-limit:]:
                timestamp = msg.get("timestamp")
                if isinstance(timestamp, str):
                    timestamp = None
                    
                messages.append(ConversationMessage(
                    role=msg.get("role", "user"),
                    content=msg.get("content", ""),
                    timestamp=timestamp,
                    metadata=msg.get("metadata", {})
                ))
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting conversation history for {user_id}: {e}")
            return []
    
    def add_message(
        self,
        user_id: str,
        message: ConversationMessage
    ) -> None:
        """
        Add a message to conversation history.
        
        Stores in Redis with TTL, persists to PostgreSQL via existing infrastructure.
        """
        self._ensure_initialized()
        
        if self._conversation_history is None:
            logger.warning("Conversation history not available, message not saved")
            return
        
        try:
            chat_id = _to_chat_id(user_id)
            raw_message = {
                "role": message.role,
                "content": message.content,
                "timestamp": message.timestamp or time.time(),
                "metadata": message.metadata or {}
            }
            
            self._conversation_history.add_message(chat_id, raw_message)
            
        except Exception as e:
            logger.error(f"Error adding message for {user_id}: {e}")
    
    def clear_history(
        self,
        user_id: str
    ) -> None:
        """Clear conversation history for user."""
        self._ensure_initialized()
        
        if self._conversation_history is None:
            return
        
        try:
            chat_id = _to_chat_id(user_id)
            self._conversation_history.clear_history(chat_id)
            logger.info(f"Cleared conversation history for {user_id}")
        except Exception as e:
            logger.error(f"Error clearing history for {user_id}: {e}")
    
    def get_user_preferences(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get user preferences from Redis/PostgreSQL.
        
        Returns default preferences if not found.
        """
        self._ensure_initialized()
        
        try:
            if self._user_preferences:
                chat_id = _to_chat_id(user_id)
                prefs = self._user_preferences.get_preferences(chat_id)
                if prefs:
                    return prefs
                    
        except Exception as e:
            logger.error(f"Error getting preferences for {user_id}: {e}")
        
        return {
            "language": "es",
            "response_style": "premium",
            "notifications_enabled": True
        }
    
    def set_user_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> None:
        """Set user preferences."""
        self._ensure_initialized()
        
        try:
            if self._user_preferences:
                chat_id = _to_chat_id(user_id)
                self._user_preferences.update_preferences(chat_id, preferences)
                logger.info(f"Updated preferences for {user_id}")
                
        except Exception as e:
            logger.error(f"Error setting preferences for {user_id}: {e}")
    
    def get_market_context(self) -> Dict[str, Any]:
        """
        Get current market context data.
        
        Aggregates from RealContextProvider if available.
        """
        self._ensure_initialized()
        
        if self._real_context_provider is None:
            return {
                "available": False,
                "reason": "RealContextProvider not available"
            }
        
        try:
            context = self._real_context_provider.get_full_context()
            
            return {
                "available": True,
                "timestamp": time.time(),
                "data": context
            }
            
        except Exception as e:
            logger.error(f"Error getting market context: {e}")
            return {
                "available": False,
                "reason": str(e)
            }
    
    def get_full_context(
        self,
        user_id: str
    ) -> ConversationContext:
        """
        Get complete context for a user.
        
        Combines:
        - Conversation history (last 10 messages)
        - User preferences
        - Market context
        - Session data
        """
        self._ensure_initialized()
        
        messages = self.get_conversation_history(user_id, limit=10)
        preferences = self.get_user_preferences(user_id)
        market_context = self.get_market_context()
        
        return ConversationContext(
            user_id=user_id,
            messages=messages,
            preferences=preferences,
            market_context=market_context,
            session_data={}
        )
