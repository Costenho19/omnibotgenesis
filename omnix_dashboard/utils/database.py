"""
OMNIX Dashboard - Database Utilities
Connection pooling and database management

Phase 1 (Dec 2025): Added telemetry logging for pool monitoring
"""

import os
import logging
import threading
import time
import atexit
from contextlib import contextmanager

logger = logging.getLogger(__name__)

DB_AVAILABLE = False
DB_ERROR_MESSAGE = None
DB_POOL = None
_TELEMETRY_THREAD = None
_TELEMETRY_STOP_EVENT = threading.Event()
_TELEMETRY_LOCK = threading.Lock()
_TELEMETRY_INTERVAL = 300  # 5 minutes


def get_database_url():
    """Get DATABASE_URL - checks multiple possible variable names"""
    url = os.environ.get('DATABASE_URL')
    if url:
        return url
    url = os.environ.get('POSTGRES_URL')
    if url:
        return url
    url = os.environ.get('DATABASE_PUBLIC_URL')
    if url:
        return url
    return None


def init_connection_pool():
    """Initialize psycopg3 connection pool - call once at startup"""
    global DB_POOL, DB_AVAILABLE, DB_ERROR_MESSAGE
    
    database_url = get_database_url()
    if not database_url:
        DB_ERROR_MESSAGE = "No DATABASE_URL found in environment"
        logger.warning(DB_ERROR_MESSAGE)
        DB_AVAILABLE = False
        return False
    
    try:
        from psycopg_pool import ConnectionPool
        
        min_size = int(os.environ.get('DB_POOL_MIN', '2'))
        max_size = int(os.environ.get('DB_POOL_MAX', '10'))
        
        DB_POOL = ConnectionPool(
            conninfo=database_url,
            min_size=min_size,
            max_size=max_size,
            timeout=30.0,
            max_lifetime=3600.0,
            max_idle=600.0,
            open=True,
            name="omnix_dashboard_pool"
        )
        
        DB_AVAILABLE = True
        DB_ERROR_MESSAGE = None
        logger.info(f"Connection pool initialized: min={min_size}, max={max_size}")
        return True
        
    except ImportError as e:
        DB_ERROR_MESSAGE = f"psycopg_pool not installed: {e}"
        logger.error(DB_ERROR_MESSAGE)
        DB_AVAILABLE = False
        return False
    except Exception as e:
        DB_ERROR_MESSAGE = f"Pool initialization failed: {str(e)[:200]}"
        logger.error(f"Connection pool failed: {e}")
        DB_AVAILABLE = False
        return False


@contextmanager
def get_db_connection():
    """Get connection from pool using context manager.
    
    Usage:
        with get_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute(...)
    """
    global DB_AVAILABLE, DB_ERROR_MESSAGE, DB_POOL
    
    if DB_POOL is None:
        init_connection_pool()
    
    if DB_POOL is None:
        yield None
        return
    
    try:
        with DB_POOL.connection() as conn:
            DB_AVAILABLE = True
            yield conn
    except Exception as e:
        DB_ERROR_MESSAGE = f"Connection error: {str(e)[:200]}"
        logger.error(f"Database connection error: {e}")
        DB_AVAILABLE = False
        yield None


def get_pool_stats():
    """Get connection pool statistics for health checks"""
    if DB_POOL is None:
        return {'status': 'not_initialized'}
    try:
        stats = DB_POOL.get_stats()
        return {
            'status': 'active',
            'pool_size': getattr(stats, 'pool_size', 0),
            'pool_available': getattr(stats, 'pool_available', 0),
            'requests_waiting': getattr(stats, 'requests_waiting', 0),
            'requests_num': getattr(stats, 'requests_num', 0),
            'usage_ms': getattr(stats, 'usage_ms', 0),
            'requests_queued': getattr(stats, 'requests_queued', 0),
            'pool_min': int(os.environ.get('DB_POOL_MIN', '2')),
            'pool_max': int(os.environ.get('DB_POOL_MAX', '10'))
        }
    except Exception as e:
        logger.error(f"Error getting pool stats: {e}")
        return {'status': 'error', 'error': str(e)}


def shutdown_pool():
    """Gracefully close connection pool and stop telemetry on shutdown"""
    global DB_POOL, _TELEMETRY_THREAD
    
    # Signal telemetry thread to stop
    _TELEMETRY_STOP_EVENT.set()
    
    # Wait for telemetry thread to finish (with timeout)
    if _TELEMETRY_THREAD is not None and _TELEMETRY_THREAD.is_alive():
        try:
            _TELEMETRY_THREAD.join(timeout=2.0)
        except Exception:
            pass
    _TELEMETRY_THREAD = None
    
    # Close database pool
    if DB_POOL:
        try:
            DB_POOL.close()
            logger.info("Connection pool closed gracefully")
        except Exception as e:
            logger.error(f"Error closing pool: {e}")
        DB_POOL = None


def _log_pool_telemetry():
    """Background thread to log pool stats every 5 minutes (Phase 1 telemetry)
    
    Uses stop event for clean shutdown and process ID for multi-worker awareness.
    """
    pid = os.getpid()
    
    while not _TELEMETRY_STOP_EVENT.is_set():
        try:
            stats = get_pool_stats()
            if stats.get('status') == 'active':
                logger.info(
                    f"📊 POOL TELEMETRY [pid={pid}]: "
                    f"size={stats.get('pool_size', 0)}, "
                    f"available={stats.get('pool_available', 0)}, "
                    f"waiting={stats.get('requests_waiting', 0)}, "
                    f"total_requests={stats.get('requests_num', 0)}, "
                    f"usage_ms={stats.get('usage_ms', 0)}"
                )
            else:
                logger.warning(f"📊 POOL TELEMETRY [pid={pid}]: status={stats.get('status')}")
        except Exception as e:
            logger.error(f"📊 POOL TELEMETRY ERROR [pid={pid}]: {e}")
        
        # Wait with stop event check for faster shutdown response
        _TELEMETRY_STOP_EVENT.wait(timeout=_TELEMETRY_INTERVAL)


def _start_telemetry_thread():
    """Start the background telemetry thread (Phase 1)
    
    Thread-safe implementation that prevents multiple threads from starting.
    Uses lock to prevent race conditions in multi-threaded environments.
    """
    global _TELEMETRY_THREAD
    
    # Check if telemetry is enabled via environment variable
    if os.environ.get('DISABLE_POOL_TELEMETRY', 'false').lower() == 'true':
        logger.info("📊 Pool telemetry disabled via DISABLE_POOL_TELEMETRY=true")
        return
    
    with _TELEMETRY_LOCK:
        # Double-check inside lock to prevent race conditions
        if _TELEMETRY_THREAD is not None and _TELEMETRY_THREAD.is_alive():
            return  # Already running
        
        # Reset stop event in case of restart
        _TELEMETRY_STOP_EVENT.clear()
        
        _TELEMETRY_THREAD = threading.Thread(
            target=_log_pool_telemetry, 
            daemon=True, 
            name=f"pool-telemetry-{os.getpid()}"
        )
        _TELEMETRY_THREAD.start()
        logger.info(f"📊 Pool telemetry started (pid={os.getpid()}, interval={_TELEMETRY_INTERVAL}s)")


# Register shutdown handler for clean exit
atexit.register(shutdown_pool)


def init_database():
    """Initialize database connection pool and start telemetry (Phase 1)"""
    global DB_AVAILABLE
    
    if init_connection_pool():
        with get_db_connection() as conn:
            if conn:
                DB_AVAILABLE = True
                logger.info("Database connected: Real data mode ACTIVE (pooled)")
                # Start telemetry thread for Phase 1 monitoring
                _start_telemetry_thread()
                return True
    
    DB_AVAILABLE = False
    return False


def is_db_available():
    """Check if database is available"""
    return DB_AVAILABLE


def get_db_error():
    """Get last database error message"""
    return DB_ERROR_MESSAGE
