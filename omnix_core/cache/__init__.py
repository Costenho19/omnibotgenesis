"""
OMNIX V6.5.3 - Cache Module
"""

from omnix_core.cache.redis_cache import RedisCache, cache, cache_result, get_redis_cache

__all__ = ['RedisCache', 'cache', 'cache_result', 'get_redis_cache']
