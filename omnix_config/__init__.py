"""
OMNIX V6.0 ULTRA - Configuration Package
Centraliza toda la configuración del sistema con gestión avanzada de variables de entorno
"""

from .settings import settings
from .env_manager import (
    EnvConfig,
    env_config,
    get_env,
    get_required_env,
    EnvCategory,
    EnvSource
)

__all__ = [
    'settings',
    'EnvConfig',
    'env_config',
    'get_env',
    'get_required_env',
    'EnvCategory',
    'EnvSource'
]
