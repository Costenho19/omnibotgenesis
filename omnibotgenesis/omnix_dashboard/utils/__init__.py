"""
OMNIX Dashboard Utilities
Shared utilities for the OMNIX Dashboard application
"""

from .database import (
    get_database_url,
    init_connection_pool,
    get_db_connection,
    get_pool_stats,
    shutdown_pool,
    init_database,
    DB_AVAILABLE,
    DB_ERROR_MESSAGE,
    DB_POOL
)

from .decorators import require_api_key
from .auth import init_security

from .external_apis import (
    fetch_with_timeout,
    http_get_with_timeout,
    API_EXECUTOR
)

from .queries import (
    get_paper_trades,
    get_balance_history,
    calculate_metrics,
    get_strategy_breakdown,
    get_asset_breakdown
)

__all__ = [
    'get_database_url',
    'init_connection_pool', 
    'get_db_connection',
    'get_pool_stats',
    'shutdown_pool',
    'init_database',
    'DB_AVAILABLE',
    'DB_ERROR_MESSAGE',
    'DB_POOL',
    'require_api_key',
    'init_security',
    'fetch_with_timeout',
    'http_get_with_timeout',
    'API_EXECUTOR',
    'get_paper_trades',
    'get_balance_history',
    'calculate_metrics',
    'get_strategy_breakdown',
    'get_asset_breakdown'
]
