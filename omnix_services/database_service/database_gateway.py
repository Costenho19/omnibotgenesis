"""
OMNIX Database Gateway
Unified database connection pool for Dashboard and Enterprise services

Phase 2 Implementation (Dec 2025):
- Single connection pool for entire system
- Fork-safe singleton pattern for Gunicorn workers
- Dual interfaces: raw pool access + execute_query()
- Built-in telemetry logging

Usage:
    from omnix_services.database_service.database_gateway import DatabaseGateway
    
    # Raw pool access (Dashboard style)
    with DatabaseGateway.get_pool().connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trades")
    
    # Execute query (Enterprise style)
    result = DatabaseGateway.execute_query("SELECT * FROM trades WHERE id = %s", (trade_id,))
"""

import os
import logging
import threading
import time
import atexit
from typing import Optional, List, Tuple, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)

_gateway_lock = threading.Lock()
_gateway_instance = None
_owner_pid = None


class DatabaseGateway:
    """
    Fork-safe singleton database gateway.
    
    Provides unified access to PostgreSQL for both Dashboard and Enterprise services.
    Automatically reinitializes after process fork (Gunicorn workers).
    """
    
    _pool = None
    _pool_lock = threading.Lock()
    _connected = False
    _error_message = None
    _telemetry_thread = None
    _telemetry_stop_event = threading.Event()
    _telemetry_interval = 300  # 5 minutes
    _total_requests = 0
    _total_query_time_ms = 0
    _instance_pid = None
    
    def __init__(self):
        self._instance_pid = os.getpid()
        self._init_pool()
    
    @classmethod
    def get_instance(cls) -> 'DatabaseGateway':
        """Get or create the singleton instance (fork-safe)."""
        global _gateway_instance, _owner_pid, _gateway_lock
        
        current_pid = os.getpid()
        
        with _gateway_lock:
            if _gateway_instance is None or _owner_pid != current_pid:
                if _owner_pid != current_pid and _gateway_instance is not None:
                    logger.info(f"🔄 DatabaseGateway: Fork detected (was pid={_owner_pid}, now pid={current_pid})")
                    cls._reset_pool()
                
                _gateway_instance = cls()
                _owner_pid = current_pid
                logger.info(f"📊 DatabaseGateway singleton created (pid={current_pid})")
            
            return _gateway_instance
    
    @classmethod
    def _reset_pool(cls):
        """Reset pool state after fork - called internally."""
        cls._pool = None
        cls._connected = False
        cls._telemetry_thread = None
        cls._telemetry_stop_event = threading.Event()
        cls._total_requests = 0
        cls._total_query_time_ms = 0
    
    @classmethod
    def reinit_after_fork(cls):
        """
        Reinitialize pool after Gunicorn fork.
        Call this from Gunicorn's post_fork hook.
        """
        global _gateway_instance, _owner_pid
        
        current_pid = os.getpid()
        logger.info(f"🔄 DatabaseGateway.reinit_after_fork() called (pid={current_pid})")
        
        with _gateway_lock:
            cls._reset_pool()
            _gateway_instance = cls()
            _owner_pid = current_pid
        
        logger.info(f"✅ DatabaseGateway reinitialized for worker (pid={current_pid})")
    
    def _get_database_url(self) -> Optional[str]:
        """Get DATABASE_URL from multiple sources."""
        url = os.environ.get('DATABASE_URL')
        if url:
            if url.startswith('postgres://'):
                url = url.replace('postgres://', 'postgresql://', 1)
            return url
        
        url = os.environ.get('POSTGRES_URL')
        if url:
            if url.startswith('postgres://'):
                url = url.replace('postgres://', 'postgresql://', 1)
            return url
        
        url = os.environ.get('DATABASE_PUBLIC_URL')
        if url:
            if url.startswith('postgres://'):
                url = url.replace('postgres://', 'postgresql://', 1)
            return url
        
        return None
    
    def _init_pool(self):
        """Initialize the connection pool."""
        database_url = self._get_database_url()
        
        if not database_url:
            self._error_message = "No DATABASE_URL found in environment"
            logger.warning(f"⚠️ DatabaseGateway: {self._error_message}")
            self._connected = False
            return
        
        try:
            from psycopg_pool import ConnectionPool
            
            min_size = int(os.environ.get('DB_POOL_MIN', '2'))
            max_size = int(os.environ.get('DB_POOL_MAX', '10'))
            
            with self._pool_lock:
                self._pool = ConnectionPool(
                    conninfo=database_url,
                    min_size=min_size,
                    max_size=max_size,
                    timeout=30.0,
                    max_lifetime=3600.0,
                    max_idle=600.0,
                    open=True,
                    name=f"omnix_gateway_pool_pid{os.getpid()}"
                )
            
            self._connected = True
            self._error_message = None
            logger.info(f"✅ DatabaseGateway pool initialized (pid={os.getpid()}): min={min_size}, max={max_size}")
            
            self._start_telemetry()
            atexit.register(self._shutdown)
            
        except ImportError as e:
            self._error_message = f"psycopg_pool not installed: {e}"
            logger.error(f"❌ DatabaseGateway: {self._error_message}")
            self._connected = False
        except Exception as e:
            self._error_message = f"Pool initialization failed: {str(e)[:200]}"
            logger.error(f"❌ DatabaseGateway pool failed: {e}")
            self._connected = False
    
    def _start_telemetry(self):
        """Start background telemetry logging thread."""
        if self._telemetry_thread is not None and self._telemetry_thread.is_alive():
            return
        
        self._telemetry_stop_event.clear()
        self._telemetry_thread = threading.Thread(
            target=self._telemetry_loop,
            daemon=True,
            name=f"GatewayTelemetry-{os.getpid()}"
        )
        self._telemetry_thread.start()
        logger.info(f"📊 Gateway telemetry started (pid={os.getpid()}, interval={self._telemetry_interval}s)")
    
    def _telemetry_loop(self):
        """Background loop for telemetry logging."""
        my_pid = os.getpid()
        
        while not self._telemetry_stop_event.wait(self._telemetry_interval):
            if os.getpid() != my_pid:
                logger.warning(f"⚠️ Gateway telemetry thread orphaned after fork, exiting")
                break
            
            try:
                stats = self.get_pool_stats()
                if stats.get('status') == 'active':
                    logger.info(
                        f"📊 GATEWAY_TELEMETRY [pid={my_pid}]: "
                        f"size={stats.get('pool_size', 0)}, "
                        f"available={stats.get('pool_available', 0)}, "
                        f"waiting={stats.get('requests_waiting', 0)}, "
                        f"total_requests={self._total_requests}, "
                        f"avg_query_ms={stats.get('avg_query_time_ms', 0):.1f}"
                    )
            except Exception as e:
                logger.warning(f"⚠️ Gateway telemetry error: {e}")
    
    def _shutdown(self):
        """Clean shutdown of pool and telemetry."""
        self._telemetry_stop_event.set()
        
        if self._telemetry_thread and self._telemetry_thread.is_alive():
            self._telemetry_thread.join(timeout=2.0)
        
        if self._pool:
            try:
                self._pool.close()
                logger.info(f"✅ DatabaseGateway pool closed (pid={os.getpid()})")
            except Exception as e:
                logger.warning(f"⚠️ Error closing gateway pool: {e}")
    
    @classmethod
    def get_pool(cls):
        """
        Get the connection pool for raw access (Dashboard style).
        
        Usage:
            pool = DatabaseGateway.get_pool()
            if pool:
                with pool.connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(...)
        """
        instance = cls.get_instance()
        return instance._pool
    
    @classmethod
    @contextmanager
    def get_connection(cls):
        """
        Get a connection from the pool using context manager.
        
        Usage:
            with DatabaseGateway.get_connection() as conn:
                if conn:
                    cursor = conn.cursor()
                    cursor.execute(...)
        """
        instance = cls.get_instance()
        
        if instance._pool is None:
            yield None
            return
        
        try:
            with instance._pool.connection() as conn:
                instance._total_requests += 1
                yield conn
        except Exception as e:
            instance._error_message = f"Connection error: {str(e)[:200]}"
            logger.error(f"❌ Gateway connection error: {e}")
            yield None
    
    @classmethod
    def execute_query(cls, query: str, params: tuple = None, fetch: bool = True) -> Optional[List[Tuple]]:
        """
        Execute a query and return results (Enterprise style).
        
        Args:
            query: SQL query string with %s placeholders
            params: Tuple of parameters (optional)
            fetch: Whether to fetch results (True for SELECT, False for INSERT/UPDATE)
        
        Returns:
            List of tuples for SELECT queries, None for INSERT/UPDATE or on error
        
        Usage:
            # SELECT query
            rows = DatabaseGateway.execute_query("SELECT * FROM trades WHERE id = %s", (trade_id,))
            if rows:
                for row in rows:
                    trade_id, symbol, side = row[0], row[1], row[2]
            
            # INSERT/UPDATE query
            DatabaseGateway.execute_query(
                "INSERT INTO trades (symbol, side) VALUES (%s, %s)",
                ('BTC', 'buy'),
                fetch=False
            )
        """
        instance = cls.get_instance()
        
        if instance._pool is None:
            logger.warning("⚠️ Gateway execute_query: Pool not available")
            return None
        
        start_time = time.time()
        
        try:
            with instance._pool.connection() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                instance._total_requests += 1
                
                if fetch and cursor.description:
                    result = cursor.fetchall()
                else:
                    conn.commit()
                    result = None
                
                elapsed_ms = (time.time() - start_time) * 1000
                instance._total_query_time_ms += elapsed_ms
                
                return result
                
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"❌ Gateway execute_query error ({elapsed_ms:.1f}ms): {e}")
            logger.error(f"   Query: {query[:100]}...")
            return None
    
    @classmethod
    def get_pool_stats(cls) -> dict:
        """Get connection pool statistics for health checks and telemetry."""
        instance = cls.get_instance()
        
        if instance._pool is None:
            return {
                'status': 'not_initialized',
                'error': instance._error_message,
                'pid': os.getpid()
            }
        
        try:
            stats = instance._pool.get_stats()
            avg_query_time = 0
            if instance._total_requests > 0:
                avg_query_time = instance._total_query_time_ms / instance._total_requests
            
            return {
                'status': 'active',
                'pool_size': getattr(stats, 'pool_size', 0),
                'pool_available': getattr(stats, 'pool_available', 0),
                'requests_waiting': getattr(stats, 'requests_waiting', 0),
                'requests_num': getattr(stats, 'requests_num', 0),
                'total_requests': instance._total_requests,
                'avg_query_time_ms': avg_query_time,
                'pid': os.getpid(),
                'pool_name': instance._pool.name if hasattr(instance._pool, 'name') else 'unknown'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'pid': os.getpid()
            }
    
    @classmethod
    def is_connected(cls) -> bool:
        """Check if the database is connected."""
        instance = cls.get_instance()
        return instance._connected and instance._pool is not None
    
    @classmethod
    def get_error(cls) -> Optional[str]:
        """Get the last error message if any."""
        instance = cls.get_instance()
        return instance._error_message


def get_gateway_pool():
    """
    Convenience function to get the gateway pool.
    For backwards compatibility with Dashboard code.
    """
    return DatabaseGateway.get_pool()


@contextmanager
def get_gateway_connection():
    """
    Convenience context manager to get a connection.
    For backwards compatibility with Dashboard code.
    """
    with DatabaseGateway.get_connection() as conn:
        yield conn


def gateway_execute_query(query: str, params: tuple = None, fetch: bool = True):
    """
    Convenience function to execute a query.
    For backwards compatibility with Enterprise code.
    """
    return DatabaseGateway.execute_query(query, params, fetch)
