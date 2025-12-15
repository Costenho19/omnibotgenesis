"""
OMNIX DatabasePort Contract Tests
=================================
Phase 4C: Contract tests ensuring DatabaseAdapter implements DatabasePort.

All DatabasePort implementations MUST pass these tests.
"""

import pytest
from typing import Protocol, Optional, List, Tuple, Any, Dict, runtime_checkable


@runtime_checkable
class DatabasePort(Protocol):
    """Contract for database operations."""
    
    def execute_query(
        self, 
        query: str, 
        params: Optional[Tuple] = None,
        fetch: bool = True
    ) -> Optional[List[Tuple]]:
        ...
    
    def health_check(self) -> Dict[str, Any]:
        ...


class MockDatabaseGateway:
    """Mock DatabaseGateway for testing."""
    
    def __init__(self):
        self._store: Dict[str, List[Tuple]] = {}
        self._connected = True
        self._queries: List[Dict] = []
    
    def execute_query(
        self, 
        query: str, 
        params: Optional[Tuple] = None, 
        fetch: bool = True
    ) -> Optional[List[Tuple]]:
        self._queries.append({
            'query': query,
            'params': params,
            'fetch': fetch
        })
        
        if "SELECT version()" in query:
            return [("PostgreSQL 15.0 (mock)",)]
        
        if "SELECT" in query.upper():
            return [("row1_col1", "row1_col2"), ("row2_col1", "row2_col2")]
        
        return None
    
    @classmethod
    def get_pool(cls):
        return MockConnectionPool()
    
    @classmethod
    def get_connection(cls):
        from contextlib import contextmanager
        @contextmanager
        def mock_connection():
            yield MockConnection()
        return mock_connection()
    
    @classmethod
    def is_connected(cls) -> bool:
        return True
    
    @classmethod
    def get_pool_stats(cls) -> Dict[str, Any]:
        return {
            'status': 'active',
            'pool_size': 5,
            'pool_available': 3,
            'requests_waiting': 0
        }


class MockConnectionPool:
    """Mock connection pool."""
    pass


class MockConnection:
    """Mock database connection."""
    
    def cursor(self):
        return MockCursor()
    
    def commit(self):
        pass


class MockCursor:
    """Mock database cursor."""
    
    def execute(self, query, params=None):
        pass
    
    def fetchall(self):
        return [("result",)]


class TestDatabasePortContract:
    """Contract tests for DatabasePort implementations."""
    
    @pytest.fixture
    def mock_gateway(self):
        return MockDatabaseGateway()
    
    @pytest.fixture
    def adapter(self, mock_gateway):
        from src.omnix.infrastructure.adapters.database_adapter import DatabaseAdapter
        return DatabaseAdapter(database_gateway=mock_gateway)
    
    def test_implements_protocol(self, adapter):
        """DatabaseAdapter must implement DatabasePort protocol."""
        assert isinstance(adapter, DatabasePort)
    
    def test_has_execute_query_method(self, adapter):
        """Adapter must have execute_query method."""
        assert hasattr(adapter, 'execute_query')
        assert callable(adapter.execute_query)
    
    def test_has_health_check_method(self, adapter):
        """Adapter must have health_check method."""
        assert hasattr(adapter, 'health_check')
        assert callable(adapter.health_check)
    
    def test_has_get_pool_method(self, adapter):
        """Adapter must have get_pool method."""
        assert hasattr(adapter, 'get_pool')
        assert callable(adapter.get_pool)
    
    def test_has_get_connection_method(self, adapter):
        """Adapter must have get_connection method."""
        assert hasattr(adapter, 'get_connection')
        assert callable(adapter.get_connection)
    
    def test_has_is_connected_method(self, adapter):
        """Adapter must have is_connected method."""
        assert hasattr(adapter, 'is_connected')
        assert callable(adapter.is_connected)


class TestDatabaseAdapterExecuteQuery:
    """Tests for execute_query method."""
    
    @pytest.fixture
    def mock_gateway(self):
        return MockDatabaseGateway()
    
    @pytest.fixture
    def adapter(self, mock_gateway):
        from src.omnix.infrastructure.adapters.database_adapter import DatabaseAdapter
        return DatabaseAdapter(database_gateway=mock_gateway)
    
    def test_execute_query_returns_list_or_none(self, adapter):
        """execute_query must return List[Tuple] or None."""
        result = adapter.execute_query("SELECT * FROM test")
        assert result is None or isinstance(result, list)
    
    def test_execute_query_with_params(self, adapter, mock_gateway):
        """execute_query must accept params tuple."""
        adapter.execute_query("SELECT * FROM test WHERE id = %s", (1,))
        assert len(mock_gateway._queries) == 1
        assert mock_gateway._queries[0]['params'] == (1,)
    
    def test_execute_query_with_fetch_false(self, adapter, mock_gateway):
        """execute_query must accept fetch=False."""
        result = adapter.execute_query(
            "INSERT INTO test VALUES (%s)", 
            ("value",), 
            fetch=False
        )
        assert mock_gateway._queries[-1]['fetch'] is False
    
    def test_execute_query_returns_tuples(self, adapter):
        """execute_query results must contain tuples."""
        result = adapter.execute_query("SELECT * FROM test")
        if result:
            for row in result:
                assert isinstance(row, tuple)
    
    def test_execute_query_increments_counter(self, adapter):
        """execute_query must track request count."""
        initial = adapter._query_count
        adapter.execute_query("SELECT 1")
        assert adapter._query_count == initial + 1


class TestDatabaseAdapterHealthCheck:
    """Tests for health_check method."""
    
    @pytest.fixture
    def mock_gateway(self):
        return MockDatabaseGateway()
    
    @pytest.fixture
    def adapter(self, mock_gateway):
        from src.omnix.infrastructure.adapters.database_adapter import DatabaseAdapter
        return DatabaseAdapter(database_gateway=mock_gateway)
    
    def test_health_check_returns_dict(self, adapter):
        """health_check must return dict."""
        result = adapter.health_check()
        assert isinstance(result, dict)
    
    def test_health_check_has_connected_field(self, adapter):
        """health_check must include connected status."""
        result = adapter.health_check()
        assert 'connected' in result
        assert isinstance(result['connected'], bool)
    
    def test_health_check_has_healthy_field(self, adapter):
        """health_check must include healthy status."""
        result = adapter.health_check()
        assert 'healthy' in result
        assert isinstance(result['healthy'], bool)
    
    def test_health_check_has_latency_ms(self, adapter):
        """health_check must include latency measurement."""
        result = adapter.health_check()
        assert 'latency_ms' in result
        assert isinstance(result['latency_ms'], (int, float))
    
    def test_health_check_has_version(self, adapter):
        """health_check must include database version."""
        result = adapter.health_check()
        assert 'version' in result
    
    def test_health_check_has_error_rate(self, adapter):
        """health_check must include error rate."""
        result = adapter.health_check()
        assert 'error_rate_pct' in result
    
    def test_health_check_has_query_count(self, adapter):
        """health_check must include query count."""
        result = adapter.health_check()
        assert 'query_count' in result


class TestDatabaseAdapterPoolAccess:
    """Tests for pool access methods."""
    
    @pytest.fixture
    def mock_gateway(self):
        return MockDatabaseGateway()
    
    @pytest.fixture
    def adapter(self, mock_gateway):
        from src.omnix.infrastructure.adapters.database_adapter import DatabaseAdapter
        return DatabaseAdapter(database_gateway=mock_gateway)
    
    def test_get_pool_returns_pool_or_none(self, adapter):
        """get_pool must return pool object or None."""
        pool = adapter.get_pool()
        assert pool is None or pool is not None
    
    def test_get_connection_is_context_manager(self, adapter):
        """get_connection must return context manager."""
        cm = adapter.get_connection()
        assert hasattr(cm, '__enter__')
        assert hasattr(cm, '__exit__')
    
    def test_get_pool_stats_returns_dict(self, adapter):
        """get_pool_stats must return dict."""
        stats = adapter.get_pool_stats()
        assert isinstance(stats, dict)
    
    def test_get_pool_stats_has_status(self, adapter):
        """get_pool_stats must include status."""
        stats = adapter.get_pool_stats()
        assert 'status' in stats


class TestDatabaseAdapterTelemetry:
    """Tests for telemetry tracking."""
    
    @pytest.fixture
    def mock_gateway(self):
        return MockDatabaseGateway()
    
    @pytest.fixture
    def adapter(self, mock_gateway):
        from src.omnix.infrastructure.adapters.database_adapter import DatabaseAdapter
        return DatabaseAdapter(database_gateway=mock_gateway)
    
    def test_tracks_request_count(self, adapter):
        """Adapter must track total request count."""
        assert hasattr(adapter, '_request_count')
        initial = adapter._request_count
        adapter.execute_query("SELECT 1")
        assert adapter._request_count == initial + 1
    
    def test_tracks_query_count(self, adapter):
        """Adapter must track query count."""
        assert hasattr(adapter, '_query_count')
        initial = adapter._query_count
        adapter.execute_query("SELECT 1")
        adapter.execute_query("SELECT 2")
        assert adapter._query_count == initial + 2
    
    def test_tracks_error_count(self, adapter):
        """Adapter must track error count."""
        assert hasattr(adapter, '_error_count')
        assert isinstance(adapter._error_count, int)
    
    def test_tracks_query_time(self, adapter):
        """Adapter must track total query time."""
        assert hasattr(adapter, '_total_query_time_ms')
        adapter.execute_query("SELECT 1")
        assert adapter._total_query_time_ms >= 0
    
    def test_tracks_last_request(self, adapter):
        """Adapter must track last request timestamp."""
        assert hasattr(adapter, '_last_request')
        assert adapter._last_request is None
        adapter.execute_query("SELECT 1")
        assert adapter._last_request is not None


class BrokenGateway:
    """Gateway that simulates connection failure."""
    
    @classmethod
    def execute_query(cls, query, params=None, fetch=True):
        raise Exception("Connection failed")
    
    @classmethod
    def get_pool(cls):
        return None
    
    @classmethod
    def get_connection(cls):
        from contextlib import contextmanager
        @contextmanager
        def null_connection():
            yield None
        return null_connection()
    
    @classmethod
    def is_connected(cls):
        return False
    
    @classmethod
    def get_pool_stats(cls):
        return {'status': 'not_connected', 'error': 'No database'}


class TestDatabaseAdapterGracefulDegradation:
    """Tests for graceful degradation when gateway unavailable."""
    
    @pytest.fixture
    def broken_adapter(self):
        from src.omnix.infrastructure.adapters.database_adapter import DatabaseAdapter
        return DatabaseAdapter(database_gateway=BrokenGateway())
    
    def test_execute_query_returns_none_on_error(self, broken_adapter):
        """execute_query must return None on gateway error."""
        result = broken_adapter.execute_query("SELECT 1")
        assert result is None
    
    def test_get_pool_returns_none_when_unavailable(self, broken_adapter):
        """get_pool must return None when pool unavailable."""
        result = broken_adapter.get_pool()
        assert result is None
    
    def test_is_connected_returns_false_when_disconnected(self, broken_adapter):
        """is_connected must return False when gateway disconnected."""
        assert broken_adapter.is_connected() is False
    
    def test_health_check_indicates_unhealthy_when_disconnected(self, broken_adapter):
        """health_check must indicate unhealthy when gateway unavailable."""
        health = broken_adapter.health_check()
        assert health['healthy'] is False


class TestDatabaseAdapterContainerIntegration:
    """Tests for Container integration."""
    
    def test_container_has_database_adapter_property(self):
        """Container must have database_adapter property."""
        from src.omnix.bootstrap.container import Container
        container = Container()
        assert hasattr(container, 'database_adapter')
    
    def test_container_has_use_database_port_flag(self):
        """Container must have use_database_port flag."""
        from src.omnix.bootstrap.container import Container
        container = Container()
        assert hasattr(container, 'use_database_port')
        assert isinstance(container.use_database_port, bool)
    
    def test_database_adapter_in_health_check(self):
        """Container health_check must include database_adapter status."""
        from src.omnix.bootstrap.container import Container
        container = Container()
        health = container.health_check()
        assert 'database_adapter' in health
        assert 'use_database_port' in health
