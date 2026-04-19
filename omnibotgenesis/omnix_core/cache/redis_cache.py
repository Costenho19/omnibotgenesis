"""
OMNIX V6.5.4 ENTERPRISE - Redis Cache System
Performance: 10x faster responses
Capacity: 50K+ concurrent users

V6.5.4 Updates:
- Added get_redis_client() for raw client access
- Added reconnect() method for lazy recovery
- Improved cache_result with normalized/hashed keys
"""

import json
import redis
import logging
import hashlib
from typing import Any, Optional, Callable
from functools import wraps
from omnix_config.settings import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Enterprise Redis Cache Manager"""
    
    def __init__(self):
        """Initialize Redis connection"""
        try:
            # Priority 1: Use REDIS_URL if available (Railway external connection)
            redis_url = settings.redis.url if hasattr(settings.redis, 'url') else None
            if not redis_url:
                from omnix_config.env_manager import env_config
                redis_url = env_config.get('REDIS_URL')
            
            if redis_url:
                # Connect using full URL (Railway TCP proxy)
                self.client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_keepalive=True,
                    socket_connect_timeout=10,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                logger.info(f"✅ Redis connecting via URL: {redis_url.split('@')[1] if '@' in redis_url else 'configured'}")
            else:
                # Fallback: Use host/port configuration
                self.client = redis.Redis(
                    host=settings.redis.host,
                    port=settings.redis.port,
                    db=settings.redis.db,
                    password=settings.redis.password,
                    decode_responses=True,
                    socket_keepalive=True,
                    socket_connect_timeout=5,
                    retry_on_timeout=True
                )
                logger.info(f"✅ Redis connecting via host/port: {settings.redis.host}:{settings.redis.port}")
            
            # Test connection
            self.client.ping()
            logger.info("✅ Redis connection verified successfully!")
        except redis.ConnectionError as e:
            logger.warning(f"⚠️ Redis not available - Running without cache: {e}")
            self.client = None
        except Exception as e:
            logger.error(f"❌ Redis initialization error: {e}")
            self.client = None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.client:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL"""
        if not self.client:
            return False
        
        try:
            ttl = ttl or settings.redis.ttl
            serialized = json.dumps(value)
            self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.client:
            return False
        
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.client:
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.client:
            return False
        
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter"""
        if not self.client:
            return None
        
        try:
            return self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error: {e}")
            return None
    
    def get_ttl(self, key: str) -> int:
        """Get remaining TTL of key"""
        if not self.client:
            return -1
        
        try:
            return self.client.ttl(key)
        except Exception as e:
            logger.error(f"Cache TTL error: {e}")
            return -1
    
    def reconnect(self) -> bool:
        """
        Attempt to reconnect to Redis if connection was lost.
        Returns True if connection is now available.
        """
        if self.client:
            try:
                self.client.ping()
                return True
            except Exception:
                self.client = None
        
        try:
            redis_url = settings.redis.url if hasattr(settings.redis, 'url') else None
            if not redis_url:
                from omnix_config.env_manager import env_config
                redis_url = env_config.get('REDIS_URL')
            
            if redis_url:
                self.client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_keepalive=True,
                    socket_connect_timeout=10,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
            else:
                self.client = redis.Redis(
                    host=settings.redis.host,
                    port=settings.redis.port,
                    db=settings.redis.db,
                    password=settings.redis.password,
                    decode_responses=True,
                    socket_keepalive=True,
                    socket_connect_timeout=5,
                    retry_on_timeout=True
                )
            
            self.client.ping()
            logger.info("✅ Redis reconnected successfully!")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Redis reconnect failed: {e}")
            self.client = None
            return False
    
    def is_connected(self) -> bool:
        """Check if Redis connection is active"""
        if not self.client:
            return False
        try:
            self.client.ping()
            return True
        except Exception:
            return False


def _normalize_cache_key(prefix: str, func_name: str, args: tuple, kwargs: dict) -> str:
    """
    Generate a normalized, hashed cache key.
    Serializes all argument values for uniqueness while using hash for security.
    """
    try:
        def serialize_arg(a):
            if isinstance(a, (dict, list)):
                return json.dumps(a, sort_keys=True, default=str)
            elif isinstance(a, set):
                return json.dumps(sorted(str(x) for x in a), default=str)
            else:
                return repr(a)
        
        key_data = {
            "func": func_name,
            "args": [serialize_arg(a) for a in args],
            "kwargs": {k: serialize_arg(v) for k, v in sorted(kwargs.items())}
        }
        key_json = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.sha256(key_json.encode()).hexdigest()[:16]
        return f"{prefix}:{func_name}:{key_hash}"
    except Exception:
        fallback_hash = hashlib.sha256(f"{args}:{kwargs}".encode()).hexdigest()[:12]
        return f"{prefix}:{func_name}:{fallback_hash}"


# Decorator para cache automático
def cache_result(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator to cache function results.
    V6.5.4: Uses normalized/hashed keys for security and consistency.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = _normalize_cache_key(key_prefix, func.__name__, args, kwargs)
            
            cached = cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached
            
            result = func(*args, **kwargs)
            
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cache MISS: {cache_key}")
            
            return result
        return wrapper
    return decorator


# Global cache instance with V7.0 port switching
def _create_cache_instance():
    """Create cache instance based on USE_CACHE_PORT flag.
    
    V7.0 Migration: When USE_CACHE_PORT=true, uses CacheAdapter (hexagonal).
    Otherwise, uses legacy RedisCache directly.
    """
    import os
    use_cache_port = os.getenv("USE_CACHE_PORT", "false").lower() == "true"
    
    if use_cache_port:
        try:
            from src.omnix.infrastructure.adapters.cache_adapter import CacheAdapter
            adapter = CacheAdapter()
            if adapter.is_connected():
                logger.info("✅ USE_CACHE_PORT=true - Using CacheAdapter (V7.0 hexagonal)")
                return adapter
            else:
                logger.warning("⚠️ CacheAdapter not connected, falling back to RedisCache")
        except ImportError as e:
            logger.warning(f"⚠️ CacheAdapter import failed: {e}, using RedisCache")
        except Exception as e:
            logger.error(f"❌ CacheAdapter creation failed: {e}, using RedisCache")
    
    return RedisCache()


cache = _create_cache_instance()


def get_redis_cache():
    """Get global Redis cache instance for multi-user architecture.
    
    Returns CacheAdapter or RedisCache depending on USE_CACHE_PORT flag.
    """
    return cache


def get_redis_client() -> Optional[redis.Redis]:
    """
    Get raw Redis client for direct access.
    Used by WebSearchManager and other services that need native Redis operations.
    
    Returns:
        Redis client instance or None if not connected
    """
    global cache
    if cache.client:
        return cache.client
    
    if cache.reconnect():
        return cache.client
    
    return None
