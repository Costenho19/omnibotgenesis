"""
OMNIX V7.0 Bootstrap Package
=============================
Phase 1: Bootstrap & Config - DI Container and runtime initialization.

Usage:
    from src.omnix.bootstrap import Container, get_container, bootstrap_omnix
    
    # Quick access to container
    container = get_container()
    
    # Full bootstrap with validation
    result = bootstrap_omnix()
    if result.success:
        container = result.container
"""

from .container import (
    Container,
    get_container,
    reset_container,
    IDatabaseGateway,
    IRedisCache,
    ITradingService,
    IMarketDataService,
)

from .runtime import (
    bootstrap_omnix,
    quick_bootstrap,
    BootstrapResult,
    configure_logging,
    validate_environment,
)

__all__ = [
    'Container',
    'get_container',
    'reset_container',
    'IDatabaseGateway',
    'IRedisCache',
    'ITradingService',
    'IMarketDataService',
    'bootstrap_omnix',
    'quick_bootstrap',
    'BootstrapResult',
    'configure_logging',
    'validate_environment',
]
