"""
OMNIX Intelligent Cache System
==============================
Sistema de cache inteligente con TTL y gestión automática de memoria.
Optimiza rendimiento mediante caching de datos frecuentemente accedidos.
"""

import logging
import time
from collections import defaultdict

logger = logging.getLogger(__name__)


class IntelligentCacheSystem:
    """Cache inteligente para optimizar rendimiento - IMPLEMENTADO AHORA"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        from functools import lru_cache
        import time
        
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = {}
        self.timestamps = {}
        self.hit_count = 0
        self.miss_count = 0
        
        logger.info(f"💾 CACHE INTELIGENTE ACTIVADO - Max: {max_size} items, TTL: {ttl_seconds}s")
    
    def get(self, key: str):
        """Obtener valor del cache con verificación TTL"""
        current_time = time.time()
        
        # Verificar si existe y no ha expirado
        if key in self.cache and key in self.timestamps:
            if current_time - self.timestamps[key] < self.ttl_seconds:
                self.hit_count += 1
                logger.debug(f"💾 CACHE HIT: {key}")
                return self.cache[key]
            else:
                # Expirado - eliminar
                self._remove_key(key)
        
        self.miss_count += 1
        logger.debug(f"💾 CACHE MISS: {key}")
        return None
    
    def set(self, key: str, value, force: bool = False):
        """Guardar valor en cache con gestión de memoria"""
        current_time = time.time()
        
        # Limpiar cache si está lleno
        if len(self.cache) >= self.max_size:
            self._cleanup_expired()
            
            # Si sigue lleno, eliminar más antiguos
            if len(self.cache) >= self.max_size:
                self._remove_oldest(int(self.max_size * 0.2))  # Eliminar 20%
        
        self.cache[key] = value
        self.timestamps[key] = current_time
        
        logger.debug(f"💾 CACHE SET: {key} (Size: {len(self.cache)}/{self.max_size})")
    
    def _remove_key(self, key: str):
        """Eliminar clave específica"""
        if key in self.cache:
            del self.cache[key]
        if key in self.timestamps:
            del self.timestamps[key]
    
    def _cleanup_expired(self):
        """Limpiar entradas expiradas"""
        current_time = time.time()
        expired_keys = []
        
        for key, timestamp in self.timestamps.items():
            if current_time - timestamp >= self.ttl_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_key(key)
        
        if expired_keys:
            logger.info(f"💾 CACHE CLEANUP: {len(expired_keys)} items expirados eliminados")
    
    def _remove_oldest(self, count: int):
        """Eliminar las entradas más antiguas"""
        if not self.timestamps:
            return
        
        # Ordenar por timestamp y eliminar los más antiguos
        sorted_keys = sorted(self.timestamps.keys(), key=lambda k: self.timestamps[k])
        keys_to_remove = sorted_keys[:count]
        
        for key in keys_to_remove:
            self._remove_key(key)
        
        logger.info(f"💾 CACHE EVICTION: {len(keys_to_remove)} items más antiguos eliminados")
    
    def get_stats(self) -> dict:
        """Estadísticas del cache"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': f"{hit_rate:.1f}%",
            'utilization': f"{len(self.cache)/self.max_size*100:.1f}%"
        }
    
    def invalidate_pattern(self, pattern: str):
        """Invalidar cache por patrón"""
        keys_to_remove = []
        for key in self.cache.keys():
            if pattern in key:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self._remove_key(key)
        
        logger.info(f"💾 CACHE INVALIDATE: {len(keys_to_remove)} items con patrón '{pattern}'")
