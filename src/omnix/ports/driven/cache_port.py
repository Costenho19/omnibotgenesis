"""
OMNIX Cache Port - Redis Interface Contract

This Protocol defines the contract for caching operations.
All methods are SYNCHRONOUS (Redis client is sync).

SOLID Principles:
- SRP: Only cache operations
- ISP: Minimal interface for caching
- DIP: Depend on this abstraction, not RedisCache directly
"""

from typing import Protocol, Optional, Any, runtime_checkable


@runtime_checkable
class CachePort(Protocol):
    """
    Contract for caching operations (Redis).
    
    Implementation: omnix_core.cache.redis_cache.RedisCache
    """
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if exists, None otherwise
        """
        ...
    
    def set(
        self, 
        key: str, 
        value: Any, 
        ttl_seconds: int = 300
    ) -> bool:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds (default 5 minutes)
            
        Returns:
            True if set successfully
        """
        ...
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted (or didn't exist)
        """
        ...
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists
        """
        ...
    
    def get_json(self, key: str) -> Optional[dict]:
        """
        Get JSON value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Parsed JSON dict if exists, None otherwise
        """
        ...
    
    def set_json(
        self, 
        key: str, 
        value: dict, 
        ttl_seconds: int = 300
    ) -> bool:
        """
        Set JSON value in cache.
        
        Args:
            key: Cache key
            value: Dict to serialize and cache
            ttl_seconds: Time to live in seconds
            
        Returns:
            True if set successfully
        """
        ...
