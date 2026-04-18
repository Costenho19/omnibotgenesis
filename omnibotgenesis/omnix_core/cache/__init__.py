"""
OMNIX V6.5.4 - Cache Module
"""

from omnix_core.cache.redis_cache import (
    RedisCache, 
    cache, 
    cache_result, 
    get_redis_cache,
    get_redis_client
)

__all__ = ['RedisCache', 'cache', 'cache_result', 'get_redis_cache', 'get_redis_client']
