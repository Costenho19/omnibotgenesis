"""
OMNIX V5.1 ENTERPRISE - Rate Limiting System
Previene abuso de APIs y protege contra DDoS
Token Bucket Algorithm con Redis
"""

import time
import asyncio
from functools import wraps
from typing import Callable, Optional
from omnix_core.cache.redis_cache import cache
from omnix_core.utils.logger import get_logger

logger = get_logger(__name__)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    pass


class RateLimiter:
    """
    Token Bucket Rate Limiter with Redis backend
    Supports distributed rate limiting across multiple instances
    """
    
    def __init__(
        self,
        max_requests: int = 60,
        window: int = 60,
        key_prefix: str = "rate_limit"
    ):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum requests allowed in window
            window: Time window in seconds
            key_prefix: Redis key prefix
        """
        self.max_requests = max_requests
        self.window = window
        self.key_prefix = key_prefix
    
    def _make_key(self, identifier: str) -> str:
        """Generate Redis key for rate limit"""
        return f"{self.key_prefix}:{identifier}"
    
    def is_allowed(self, identifier: str) -> tuple[bool, int]:
        """
        Check if request is allowed for identifier
        
        Args:
            identifier: Unique identifier (user_id, chat_id, IP, etc)
            
        Returns:
            Tuple of (is_allowed, requests_remaining)
        """
        key = self._make_key(identifier)
        
        # If Redis not available, allow request (fail open)
        if not cache.client:
            logger.warning("Redis not available, rate limiting disabled")
            return True, self.max_requests
        
        try:
            # Get current count
            current_count = cache.increment(key, 1)
            
            if current_count is None:
                # First request
                cache.set(key, 1, self.window)
                return True, self.max_requests - 1
            
            # Set expiry on first increment
            if current_count == 1:
                cache.client.expire(key, self.window)
            
            # Check limit
            if current_count <= self.max_requests:
                return True, self.max_requests - current_count
            else:
                # Rate limit exceeded
                remaining_ttl = cache.get_ttl(key)
                logger.warning(
                    f"Rate limit exceeded for {identifier}: "
                    f"{current_count}/{self.max_requests} "
                    f"(resets in {remaining_ttl}s)"
                )
                return False, 0
        
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            # Fail open on errors
            return True, self.max_requests
    
    def get_reset_time(self, identifier: str) -> int:
        """Get time in seconds until rate limit resets"""
        key = self._make_key(identifier)
        return cache.get_ttl(key)


def rate_limit(
    max_requests: int = 60,
    window: int = 60,
    identifier_func: Optional[Callable] = None,
    key_prefix: str = "rate_limit"
):
    """
    Rate limiting decorator for functions/methods
    
    Args:
        max_requests: Maximum requests allowed in window
        window: Time window in seconds
        identifier_func: Function to extract identifier from args/kwargs
        key_prefix: Redis key prefix
    
    Example:
        @rate_limit(max_requests=10, window=60)
        async def generate_ai_response(chat_id, message):
            # This will be rate limited to 10 requests/minute per chat_id
            pass
        
        @rate_limit(max_requests=100, window=60, identifier_func=lambda *args, **kwargs: kwargs['user_id'])
        async def process_request(user_id, data):
            pass
    """
    
    limiter = RateLimiter(max_requests, window, key_prefix)
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract identifier
            if identifier_func:
                identifier = identifier_func(*args, **kwargs)
            elif args:
                # Use first argument as identifier (e.g., chat_id, user_id)
                identifier = str(args[0])
            else:
                # Use 'global' for functions without clear identifier
                identifier = 'global'
            
            # Check rate limit
            allowed, remaining = limiter.is_allowed(identifier)
            
            if not allowed:
                reset_time = limiter.get_reset_time(identifier)
                error_msg = (
                    f"Rate limit exceeded. "
                    f"Limit: {max_requests} requests per {window}s. "
                    f"Resets in {reset_time}s."
                )
                logger.warning(f"Rate limit exceeded for {identifier}")
                raise RateLimitExceeded(error_msg)
            
            # Log remaining requests
            if remaining < max_requests * 0.2:  # Warn at 20% remaining
                logger.info(
                    f"Rate limit warning for {identifier}: "
                    f"{remaining} requests remaining"
                )
            
            # Execute function
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Extract identifier
            if identifier_func:
                identifier = identifier_func(*args, **kwargs)
            elif args:
                identifier = str(args[0])
            else:
                identifier = 'global'
            
            # Check rate limit
            allowed, remaining = limiter.is_allowed(identifier)
            
            if not allowed:
                reset_time = limiter.get_reset_time(identifier)
                error_msg = (
                    f"Rate limit exceeded. "
                    f"Limit: {max_requests} requests per {window}s. "
                    f"Resets in {reset_time}s."
                )
                logger.warning(f"Rate limit exceeded for {identifier}")
                raise RateLimitExceeded(error_msg)
            
            # Execute function
            return func(*args, **kwargs)
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Predefined rate limiters for common use cases
class RateLimiters:
    """Collection of predefined rate limiters"""
    
    # AI Generation: 60 requests per minute per user
    AI_GENERATION = RateLimiter(max_requests=60, window=60, key_prefix="ai_gen")
    
    # Trading: 15 requests per minute per user (conservative for API protection)
    TRADING = RateLimiter(max_requests=15, window=60, key_prefix="trading")
    
    # Price queries: 60 requests per minute per user
    PRICE_QUERY = RateLimiter(max_requests=60, window=60, key_prefix="price")
    
    # General API: 100 requests per minute per user
    GENERAL_API = RateLimiter(max_requests=100, window=60, key_prefix="api")
    
    # Global (per IP): 200 requests per minute
    GLOBAL = RateLimiter(max_requests=200, window=60, key_prefix="global")
