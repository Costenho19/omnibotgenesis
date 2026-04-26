"""
OMNIX V7.0 Database Infrastructure Adapter
===========================================
Phase 4C: Implements DatabasePort by wrapping legacy DatabaseGateway.
Strangler Fig pattern - zero modifications to legacy code.

Migration Status: Phase 4C - MEDIUM-COUPLING SERVICES MIGRATION
"""

import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

logger = logging.getLogger(__name__)


class DatabaseAdapter:
    """
    Infrastructure adapter for database operations.
    
    Implements DatabasePort:
    - execute_query: Execute raw SQL queries
    - health_check: Check database connectivity
    
    Features:
    - Lazy loading of DatabaseGateway singleton
    - Connection health monitoring
    - Graceful degradation if database unavailable
    - Telemetry and request tracking
    
    Strangler Fig: Wraps legacy DatabaseGateway without modification.
    """
    
    def __init__(
        self,
        database_gateway: Optional[Any] = None
    ):
        """
        Initialize database adapter.
        
        Args:
            database_gateway: DatabaseGateway instance (lazy-loaded if None)
        """
        self._database_gateway = database_gateway
        
        self._request_count = 0
        self._query_count = 0
        self._error_count = 0
        self._total_query_time_ms = 0.0
        self._last_request: Optional[datetime] = None
    
    @property
    def _pool(self) -> Optional[Any]:
        """
        Legacy compatibility property.
        
        Some legacy services access database_service._pool directly.
        This property delegates to the gateway's current pool without
        mutating telemetry counters.
        
        Unlike get_pool(), this property:
        - Does NOT increment request_count
        - Does NOT log errors
        - Always returns the gateway's current pool (not cached)
        
        Returns:
            Connection pool if available, None otherwise
        """
        gateway = self._get_database_gateway()
        if gateway is None:
            return None
        
        try:
            return gateway.get_pool()
        except Exception:
            return None
    
    def _get_database_gateway(self) -> Optional[Any]:
        """Lazy-load DatabaseGateway singleton."""
        if self._database_gateway is not None:
            return self._database_gateway
        
        try:
            from omnix_services.database_service.database_gateway import DatabaseGateway
            self._database_gateway = DatabaseGateway.get_instance()
            logger.info("DatabaseAdapter: DatabaseGateway loaded")
            return self._database_gateway
        except ImportError as e:
            logger.warning(f"DatabaseAdapter: DatabaseGateway not available: {e}")
            return None
        except Exception as e:
            logger.error(f"DatabaseAdapter: Failed to load DatabaseGateway: {e}")
            return None
    
    def execute_query(
        self, 
        query: str, 
        params: Optional[Tuple] = None,
        fetch: bool = True
    ) -> Optional[List[Tuple]]:
        """
        Execute raw SQL query.
        
        Implements DatabasePort.execute_query.
        
        Args:
            query: SQL query string
            params: Query parameters tuple
            fetch: Whether to fetch results
            
        Returns:
            List of tuples if fetch=True, None otherwise
        """
        self._request_count += 1
        self._query_count += 1
        self._last_request = datetime.utcnow()
        
        gateway = self._get_database_gateway()
        if gateway is None:
            self._error_count += 1
            return None
        
        start_time = time.time()
        
        try:
            result = gateway.execute_query(query, params, fetch=fetch)
            elapsed_ms = (time.time() - start_time) * 1000
            self._total_query_time_ms += elapsed_ms
            return result
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            self._total_query_time_ms += elapsed_ms
            logger.error(f"DatabaseAdapter: execute_query error ({elapsed_ms:.1f}ms): {e}")
            self._error_count += 1
            return None
    
    def get_pool(self) -> Optional[Any]:
        """
        Get the connection pool for raw access.
        
        Provides access to underlying pool for Dashboard-style operations.
        
        Returns:
            Connection pool if available, None otherwise
        """
        self._request_count += 1
        self._last_request = datetime.utcnow()
        
        gateway = self._get_database_gateway()
        if gateway is None:
            return None
        
        try:
            return gateway.get_pool()
        except Exception as e:
            logger.error(f"DatabaseAdapter: get_pool error: {e}")
            self._error_count += 1
            return None
    
    def get_connection(self):
        """
        Get a connection from the pool using context manager.
        
        Usage:
            with adapter.get_connection() as conn:
                if conn:
                    cursor = conn.cursor()
                    cursor.execute(...)
        
        Returns:
            Context manager yielding connection or None
        """
        self._request_count += 1
        self._last_request = datetime.utcnow()
        
        gateway = self._get_database_gateway()
        if gateway is None:
            from contextlib import contextmanager
            logger.warning(
                "DatabaseAdapter: get_connection called but gateway is unavailable. "
                "Yielding None — callers MUST check 'if conn is not None' before use. "
                "I-3: null connection adapter active."
            )
            @contextmanager
            def null_connection():
                yield None
            return null_connection()
        
        try:
            return gateway.get_connection()
        except Exception as e:
            logger.error(f"DatabaseAdapter: get_connection error: {e}")
            self._error_count += 1
            from contextlib import contextmanager
            logger.warning(
                "DatabaseAdapter: get_connection fallback to null after error. "
                "Yielding None — callers MUST check 'if conn is not None' before use."
            )
            @contextmanager
            def null_connection():
                yield None
            return null_connection()
    
    def is_connected(self) -> bool:
        """Check if database is connected."""
        gateway = self._get_database_gateway()
        if gateway is None:
            return False
        
        try:
            return gateway.is_connected()
        except Exception:
            return False
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        gateway = self._get_database_gateway()
        if gateway is None:
            return {
                'status': 'not_available',
                'error': 'DatabaseGateway not loaded'
            }
        
        try:
            return gateway.get_pool_stats()
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check database connectivity.
        
        Implements DatabasePort.health_check.
        
        Note: Does NOT issue queries when gateway unavailable (graceful degradation).
        Version probe is a lightweight internal check that doesn't inflate telemetry.
        
        Returns:
            Dict with:
            - connected: bool
            - latency_ms: float
            - version: str (if available)
        """
        gateway = self._get_database_gateway()
        connected = self.is_connected()
        
        avg_query_time = 0.0
        if self._query_count > 0:
            avg_query_time = self._total_query_time_ms / self._query_count
        
        error_rate = 0.0
        if self._request_count > 0:
            error_rate = self._error_count / self._request_count * 100
        
        result = {
            'healthy': connected,
            'database_gateway_available': gateway is not None,
            'connected': connected,
            'request_count': self._request_count,
            'query_count': self._query_count,
            'error_count': self._error_count,
            'avg_query_time_ms': round(avg_query_time, 2),
            'error_rate_pct': round(error_rate, 2),
            'last_request': self._last_request.isoformat() if self._last_request else None,
        }
        
        if gateway is not None:
            try:
                pool_stats = gateway.get_pool_stats()
                result['pool_status'] = pool_stats.get('status', 'unknown')
                result['pool_size'] = pool_stats.get('pool_size', 0)
                result['pool_available'] = pool_stats.get('pool_available', 0)
            except Exception as e:
                result['pool_error'] = str(e)
        
        latency_ms = 0.0
        version = 'unknown'
        
        if connected and gateway is not None:
            start = time.time()
            try:
                rows = gateway.execute_query("SELECT version()")
                latency_ms = (time.time() - start) * 1000
                if rows and len(rows) > 0:
                    version = str(rows[0][0])[:50]
            except Exception:
                pass
        
        result['latency_ms'] = round(latency_ms, 2)
        result['version'] = version
        
        return result
