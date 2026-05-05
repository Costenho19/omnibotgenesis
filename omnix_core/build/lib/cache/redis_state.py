"""
OMNIX V5.1 ENTERPRISE - Redis State Management
Stateless Architecture for Horizontal Scaling
Soporta 100K+ usuarios con múltiples instancias
"""

import json
import logging
from typing import Any, Optional, List, Dict
from datetime import datetime, timedelta
from omnix_core.cache.redis_cache import cache
from omnix_core.utils.logger import get_logger

logger = get_logger(__name__)


class RedisStateManager:
    """Base class for Redis-backed state management"""
    
    def __init__(self, key_prefix: str, default_ttl: int = 3600):
        """
        Initialize state manager
        
        Args:
            key_prefix: Prefix for Redis keys
            default_ttl: Default TTL in seconds (1 hour default)
        """
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        self.cache = cache
    
    def _make_key(self, identifier: str) -> str:
        """Generate Redis key with prefix"""
        return f"{self.key_prefix}:{identifier}"
    
    def get(self, identifier: str) -> Optional[Any]:
        """Get state from Redis"""
        key = self._make_key(identifier)
        return self.cache.get(key)
    
    def set(self, identifier: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set state in Redis"""
        key = self._make_key(identifier)
        ttl = ttl or self.default_ttl
        return self.cache.set(key, value, ttl)
    
    def delete(self, identifier: str) -> bool:
        """Delete state from Redis"""
        key = self._make_key(identifier)
        return self.cache.delete(key)
    
    def exists(self, identifier: str) -> bool:
        """Check if state exists"""
        key = self._make_key(identifier)
        return self.cache.exists(key)


class RedisConversationHistory(RedisStateManager):
    """
    Redis-backed conversation history
    Replaces in-memory dictionary for horizontal scaling
    """
    
    def __init__(self):
        # TTL de 24 horas para historiales de conversación
        super().__init__(key_prefix="conversation_history", default_ttl=86400)
        self.max_messages = 10  # Mantener últimos 10 mensajes como Harold pidió
    
    def get_history(self, chat_id: int) -> List[Dict]:
        """
        Get conversation history for chat_id (from Redis LIST)
        
        Args:
            chat_id: Unique chat identifier
            
        Returns:
            List of conversation messages
        """
        if not self.cache.client:
            return []
        
        try:
            key = self._make_key(str(chat_id))
            
            # Get all items from Redis list (atomic)
            items = self.cache.client.lrange(key, 0, -1)
            
            if not items:
                return []
            
            # Deserialize JSON strings to dicts
            history = []
            for item in items:
                try:
                    if isinstance(item, bytes):
                        item = item.decode('utf-8')
                    history.append(json.loads(item))
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse history item: {e}")
                    continue
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get history for chat {chat_id}: {e}")
            return []
    
    def add_message(self, chat_id: int, message: Dict) -> bool:
        """
        Add message to conversation history (THREAD-SAFE with atomic Redis ops)
        
        Args:
            chat_id: Unique chat identifier
            message: Message dictionary
            
        Returns:
            Success boolean
        """
        if not self.cache.client:
            logger.warning("Redis not available, message not saved")
            return False
        
        try:
            # Create a COPY of message to avoid mutation (thread-safe)
            message_copy = {**message}
            
            # Add timestamp if not present
            if 'timestamp' not in message_copy:
                message_copy['timestamp'] = datetime.now().isoformat()
            
            key = self._make_key(str(chat_id))
            
            # Use Redis Pipeline for atomic operations
            pipe = self.cache.client.pipeline()
            
            # RPUSH adds to end of list (atomic) - using COPIED message
            pipe.rpush(key, json.dumps(message_copy))
            
            # LTRIM keeps only last N messages (atomic)
            pipe.ltrim(key, -self.max_messages, -1)
            
            # Set expiry
            pipe.expire(key, self.default_ttl)
            
            # Execute all operations atomically
            pipe.execute()
            
            logger.debug(f"Added message to chat {chat_id} history (atomic)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add message for chat {chat_id}: {e}")
            return False
    
    def clear_history(self, chat_id: int) -> bool:
        """Clear conversation history for chat_id"""
        success = self.delete(str(chat_id))
        if success:
            logger.info(f"Cleared history for chat {chat_id}")
        return success
    
    def get_recent_intents(self, chat_id: int, limit: int = 5) -> List[str]:
        """Get recent intents from conversation history"""
        history = self.get_history(chat_id)
        
        # Extract intents from recent messages
        intents = []
        for msg in history[-limit:]:
            if 'intent' in msg:
                intents.append(msg['intent'])
        
        return intents
    
    def get_conversation_summary(self, chat_id: int) -> str:
        """Generate summary of conversation"""
        history = self.get_history(chat_id)
        
        if not history:
            return "Nueva conversación"
        
        # Count intents
        intent_counts = {}
        for msg in history:
            intent = msg.get('intent', 'unknown')
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        # Find main intent
        if intent_counts:
            main_intent = max(intent_counts.items(), key=lambda x: x[1])[0]
            summary = f"Conversación activa ({len(history)} mensajes). "
            summary += f"Tema principal: {main_intent.replace('_', ' ')}."
        else:
            summary = f"Conversación activa ({len(history)} mensajes)."
        
        return summary


class RedisUserPreferences(RedisStateManager):
    """
    Redis-backed user preferences
    Replaces in-memory dictionary for horizontal scaling
    """
    
    def __init__(self):
        # TTL de 30 días para preferencias de usuario
        super().__init__(key_prefix="user_preferences", default_ttl=2592000)
    
    def get_preferences(self, chat_id: int) -> Dict[str, Any]:
        """
        Get user preferences for chat_id
        
        Args:
            chat_id: Unique chat identifier
            
        Returns:
            Dictionary of user preferences
        """
        prefs = self.get(str(chat_id))
        if prefs is None:
            return {}
        
        # Ensure it's a dict
        if not isinstance(prefs, dict):
            logger.warning(f"Invalid preferences format for chat {chat_id}, resetting")
            return {}
        
        return prefs
    
    def set_preference(self, chat_id: int, key: str, value: Any) -> bool:
        """
        Set single user preference
        
        Args:
            chat_id: Unique chat identifier
            key: Preference key
            value: Preference value
            
        Returns:
            Success boolean
        """
        prefs = self.get_preferences(chat_id)
        prefs[key] = value
        
        success = self.set(str(chat_id), prefs)
        
        if success:
            logger.debug(f"Set preference for chat {chat_id}: {key} = {value}")
        else:
            logger.error(f"Failed to set preference for chat {chat_id}")
        
        return success
    
    def get_preference(self, chat_id: int, key: str, default: Any = None) -> Any:
        """Get single user preference"""
        prefs = self.get_preferences(chat_id)
        return prefs.get(key, default)
    
    def update_preferences(self, chat_id: int, preferences: Dict[str, Any]) -> bool:
        """Update multiple preferences at once"""
        current_prefs = self.get_preferences(chat_id)
        current_prefs.update(preferences)
        
        success = self.set(str(chat_id), current_prefs)
        
        if success:
            logger.info(f"Updated {len(preferences)} preferences for chat {chat_id}")
        
        return success
    
    def clear_preferences(self, chat_id: int) -> bool:
        """Clear all preferences for chat_id"""
        success = self.delete(str(chat_id))
        if success:
            logger.info(f"Cleared preferences for chat {chat_id}")
        return success


class RedisMarketContext(RedisStateManager):
    """
    Redis-backed market context (shared across all users)
    Global market data cache
    """
    
    def __init__(self):
        # TTL de 5 minutos para datos de mercado
        super().__init__(key_prefix="market_context", default_ttl=300)
    
    def get_market_data(self, symbol: str = "BTC") -> Optional[Dict[str, Any]]:
        """Get market data for symbol"""
        return self.get(symbol)
    
    def update_market_data(self, symbol: str, data: Dict[str, Any]) -> bool:
        """Update market data for symbol"""
        success = self.set(symbol, data, ttl=300)  # 5 minutes
        
        if success:
            logger.debug(f"Updated market data for {symbol}")
        
        return success
    
    def get_global_context(self) -> Dict[str, Any]:
        """Get all market context"""
        # Get common symbols
        symbols = ['BTC', 'ETH', 'ADA', 'SOL']
        context = {}
        
        for symbol in symbols:
            data = self.get_market_data(symbol)
            if data:
                context[symbol] = data
        
        return context


# Global instances (singleton pattern)
_conversation_history = None
_user_preferences = None
_market_context = None


def get_conversation_history() -> RedisConversationHistory:
    """Get singleton conversation history instance"""
    global _conversation_history
    if _conversation_history is None:
        _conversation_history = RedisConversationHistory()
    return _conversation_history


def get_user_preferences() -> RedisUserPreferences:
    """Get singleton user preferences instance"""
    global _user_preferences
    if _user_preferences is None:
        _user_preferences = RedisUserPreferences()
    return _user_preferences


def get_market_context() -> RedisMarketContext:
    """Get singleton market context instance"""
    global _market_context
    if _market_context is None:
        _market_context = RedisMarketContext()
    return _market_context


# Export instances for backward compatibility
conversation_history = get_conversation_history()
user_preferences = get_user_preferences()
market_context = get_market_context()
