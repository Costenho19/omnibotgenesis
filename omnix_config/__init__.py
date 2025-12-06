"""
OMNIX Configuration Package
Centralized system configuration with advanced environment variable management
"""

from .settings import settings, VERSION, VERSION_NAME, VERSION_BANNER
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
    'VERSION',
    'VERSION_NAME', 
    'VERSION_BANNER',
    'EnvConfig',
    'env_config',
    'get_env',
    'get_required_env',
    'EnvCategory',
    'EnvSource'
]
