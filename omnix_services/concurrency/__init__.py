"""
OMNIX Concurrency Module
========================
Sistema modular de cache inteligente y gestión de concurrencia optimizada.
Extraído de main.py para arquitectura modular.

Incluye:
- IntelligentCacheSystem: Cache TTL con gestión automática de memoria
- OptimizedConcurrencyManager: Gestión de thread pools con priorización de tareas
"""

from .cache_system import IntelligentCacheSystem
from .concurrency_manager import OptimizedConcurrencyManager
from .resource_manager import ScalableResourceManager

__all__ = [
    'IntelligentCacheSystem',
    'OptimizedConcurrencyManager',
    'ScalableResourceManager'
]
