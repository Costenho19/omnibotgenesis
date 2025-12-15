"""
OMNIX V7.0 Cache Infrastructure Adapter
========================================
Phase 4B: Implements CachePort by wrapping legacy RedisCache singleton.
Strangler Fig pattern - zero modifications to legacy code.

Migration Status: Phase 4B - MEDIUM-COUPLING SERVICES MIGRATION
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class CacheAdapter:
    """
    Infrastructure adapter for Redis cache operations.
    
    Implements CachePort:
    - get: Get value from cache
    - set: Set value with TTL
    - delete: Delete key
    - exists: Check key existence
    - get_json: Get JSON value
    - set_json: Set JSON value
    
    Features:
    - Lazy loading of RedisCache singleton
    - Connection health monitoring
    - Graceful degradation if Redis unavailable
    - Telemetry and request tracking
    
    Strangler Fig: Wraps legacy RedisCache without modification.
    """
    
    def __init__(
        self,
        redis_cache: Optional[Any] = None,
        default_ttl: int = 300
    ):
        """
        Initialize cache adapter.
        
        Args:
            redis_cache: RedisCache instance (lazy-loaded if None)
            default_ttl: Default TTL in seconds (5 minutes)
        """
        self._redis_cache = redis_cache
        self._default_ttl = default_ttl
        
        self._request_count = 0
        self._hit_count = 0
        self._miss_count = 0
        self._error_count = 0
        self._last_request: Optional[datetime] = None
    
    def _get_redis_cache(self) -> Optional[Any]:
        """Lazy-load RedisCache singleton."""
        if self._redis_cache is not None:
            return self._redis_cache
        
        try:
            from omnix_core.cache.redis_cache import RedisCache
            get_instance = getattr(RedisCache, 'get_instance', None)
            if get_instance:
                self._redis_cache = get_instance()
            else:
                self._redis_cache = RedisCache()
            logger.info("CacheAdapter: RedisCache loaded")
            return self._redis_cache
        except ImportError as e:
            logger.warning(f"CacheAdapter: RedisCache not available: {e}")
            return None
        except Exception as e:
            logger.error(f"CacheAdapter: Failed to load RedisCache: {e}")
            return None
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Implements CachePort.get.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if exists, None otherwise
        """
        self._request_count += 1
        self._last_request = datetime.utcnow()
        
        cache = self._get_redis_cache()
        if cache is None:
            self._miss_count += 1
            return None
        
        try:
            value = cache.get(key)
            if value is not None:
                self._hit_count += 1
            else:
                self._miss_count += 1
            return value
        except Exception as e:
            logger.error(f"CacheAdapter: get error for key '{key}': {e}")
            self._error_count += 1
            self._miss_count += 1
            return None
    
    def set(
        self, 
        key: str, 
        value: Any, 
        ttl_seconds: int = 300
    ) -> bool:
        """
        Set value in cache with TTL.
        
        Implements CachePort.set.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds
            
        Returns:
            True if set successfully
        """
        self._request_count += 1
        self._last_request = datetime.utcnow()
        
        cache = self._get_redis_cache()
        if cache is None:
            self._error_count += 1
            return False
        
        try:
            return cache.set(key, value, ttl=ttl_seconds)
        except Exception as e:
            logger.error(f"CacheAdapter: set error for key '{key}': {e}")
            self._error_count += 1
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Implements CachePort.delete.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted (or didn't exist)
        """
        self._request_count += 1
        self._last_request = datetime.utcnow()
        
        cache = self._get_redis_cache()
        if cache is None:
            return True
        
        try:
            return cache.delete(key)
        except Exception as e:
            logger.error(f"CacheAdapter: delete error for key '{key}': {e}")
            self._error_count += 1
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Implements CachePort.exists.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists
        """
        self._request_count += 1
        self._last_request = datetime.utcnow()
        
        cache = self._get_redis_cache()
        if cache is None:
            return False
        
        try:
            return cache.exists(key)
        except Exception as e:
            logger.error(f"CacheAdapter: exists error for key '{key}': {e}")
            self._error_count += 1
            return False
    
    def get_json(self, key: str) -> Optional[dict]:
        """
        Get JSON value from cache.
        
        Implements CachePort.get_json.
        Note: Legacy RedisCache already deserializes JSON internally.
        
        Args:
            key: Cache key
            
        Returns:
            Parsed JSON dict if exists, None otherwise
        """
        value = self.get(key)
        if value is None:
            return None
        
        if isinstance(value, dict):
            return value
        
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                logger.warning(f"CacheAdapter: get_json failed to parse key '{key}'")
                return None
        
        return None
    
    def set_json(
        self, 
        key: str, 
        value: dict, 
        ttl_seconds: int = 300
    ) -> bool:
        """
        Set JSON value in cache.
        
        Implements CachePort.set_json.
        Note: Legacy RedisCache already serializes to JSON internally.
        
        Args:
            key: Cache key
            value: Dict to serialize and cache
            ttl_seconds: Time to live in seconds
            
        Returns:
            True if set successfully
        """
        return self.set(key, value, ttl_seconds)
    
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        cache = self._get_redis_cache()
        if cache is None:
            return False
        
        if hasattr(cache, 'client') and cache.client:
            try:
                cache.client.ping()
                return True
            except Exception:
                return False
        
        return False
    
    def health_check(self) -> Dict[str, Any]:
        """Get adapter health status and telemetry."""
        cache = self._get_redis_cache()
        connected = self.is_connected()
        
        hit_rate = (
            self._hit_count / (self._hit_count + self._miss_count) * 100
            if (self._hit_count + self._miss_count) > 0 else 0.0
        )
        
        error_rate = (
            self._error_count / self._request_count * 100
            if self._request_count > 0 else 0.0
        )
        
        return {
            'healthy': connected,
            'redis_cache_available': cache is not None,
            'connected': connected,
            'request_count': self._request_count,
            'hit_count': self._hit_count,
            'miss_count': self._miss_count,
            'error_count': self._error_count,
            'hit_rate_pct': round(hit_rate, 2),
            'error_rate_pct': round(error_rate, 2),
            'last_request': self._last_request.isoformat() if self._last_request else None,
        }
