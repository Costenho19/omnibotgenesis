"""
OMNIX CachePort Contract Tests
==============================
Phase 4B: Contract tests ensuring CacheAdapter implements CachePort.

All CachePort implementations MUST pass these tests.
"""

import pytest
from typing import Protocol, Optional, Any, runtime_checkable


@runtime_checkable
class CachePort(Protocol):
    """Contract for cache operations."""
    
    def get(self, key: str) -> Optional[Any]:
        ...
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        ...
    
    def delete(self, key: str) -> bool:
        ...
    
    def exists(self, key: str) -> bool:
        ...
    
    def get_json(self, key: str) -> Optional[dict]:
        ...
    
    def set_json(self, key: str, value: dict, ttl_seconds: int = 300) -> bool:
        ...


class MockRedisCache:
    """Mock RedisCache for testing."""
    
    def __init__(self):
        self._store: dict = {}
        self.client = self
    
    def get(self, key: str) -> Optional[Any]:
        return self._store.get(key)
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        self._store[key] = value
        return True
    
    def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
        return True
    
    def exists(self, key: str) -> bool:
        return key in self._store
    
    def ping(self):
        return True


class TestCachePortContract:
    """Contract tests for CachePort implementations."""
    
    @pytest.fixture
    def mock_redis(self):
        return MockRedisCache()
    
    @pytest.fixture
    def adapter(self, mock_redis):
        from src.omnix.infrastructure.adapters.cache_adapter import CacheAdapter
        return CacheAdapter(redis_cache=mock_redis)
    
    def test_implements_protocol(self, adapter):
        """CacheAdapter must implement CachePort protocol."""
        assert isinstance(adapter, CachePort)
    
    def test_has_get_method(self, adapter):
        """Adapter must have get method."""
        assert hasattr(adapter, 'get')
        assert callable(adapter.get)
    
    def test_has_set_method(self, adapter):
        """Adapter must have set method."""
        assert hasattr(adapter, 'set')
        assert callable(adapter.set)
    
    def test_has_delete_method(self, adapter):
        """Adapter must have delete method."""
        assert hasattr(adapter, 'delete')
        assert callable(adapter.delete)
    
    def test_has_exists_method(self, adapter):
        """Adapter must have exists method."""
        assert hasattr(adapter, 'exists')
        assert callable(adapter.exists)
    
    def test_has_get_json_method(self, adapter):
        """Adapter must have get_json method."""
        assert hasattr(adapter, 'get_json')
        assert callable(adapter.get_json)
    
    def test_has_set_json_method(self, adapter):
        """Adapter must have set_json method."""
        assert hasattr(adapter, 'set_json')
        assert callable(adapter.set_json)
    
    def test_get_returns_none_for_missing_key(self, adapter):
        """get must return None for non-existent key."""
        result = adapter.get("nonexistent_key")
        assert result is None
    
    def test_set_returns_bool(self, adapter):
        """set must return bool."""
        result = adapter.set("test_key", "test_value")
        assert isinstance(result, bool)
        assert result is True
    
    def test_get_returns_set_value(self, adapter):
        """get must return value that was set."""
        adapter.set("my_key", {"data": 123})
        result = adapter.get("my_key")
        assert result == {"data": 123}
    
    def test_delete_returns_bool(self, adapter):
        """delete must return bool."""
        adapter.set("key_to_delete", "value")
        result = adapter.delete("key_to_delete")
        assert isinstance(result, bool)
        assert result is True
    
    def test_delete_removes_key(self, adapter):
        """delete must remove key from cache."""
        adapter.set("key_to_delete", "value")
        adapter.delete("key_to_delete")
        assert adapter.get("key_to_delete") is None
    
    def test_exists_returns_bool(self, adapter):
        """exists must return bool."""
        result = adapter.exists("some_key")
        assert isinstance(result, bool)
    
    def test_exists_true_for_existing_key(self, adapter):
        """exists must return True for existing key."""
        adapter.set("existing_key", "value")
        assert adapter.exists("existing_key") is True
    
    def test_exists_false_for_missing_key(self, adapter):
        """exists must return False for missing key."""
        assert adapter.exists("missing_key") is False
    
    def test_get_json_returns_dict(self, adapter):
        """get_json must return dict or None."""
        adapter.set("json_key", {"name": "test", "count": 42})
        result = adapter.get_json("json_key")
        assert isinstance(result, dict)
        assert result["name"] == "test"
        assert result["count"] == 42
    
    def test_get_json_returns_none_for_missing(self, adapter):
        """get_json must return None for missing key."""
        result = adapter.get_json("missing_json")
        assert result is None
    
    def test_set_json_returns_bool(self, adapter):
        """set_json must return bool."""
        result = adapter.set_json("json_key", {"key": "value"})
        assert isinstance(result, bool)
        assert result is True
    
    def test_set_json_stores_dict(self, adapter):
        """set_json must store dict that can be retrieved."""
        adapter.set_json("my_json", {"nested": {"data": [1, 2, 3]}})
        result = adapter.get_json("my_json")
        assert result == {"nested": {"data": [1, 2, 3]}}
    
    def test_health_check_returns_dict(self, adapter):
        """health_check must return status dictionary."""
        health = adapter.health_check()
        assert isinstance(health, dict)
        assert 'healthy' in health
        assert 'connected' in health


class TestCacheAdapterTelemetry:
    """Test telemetry tracking in CacheAdapter."""
    
    @pytest.fixture
    def mock_redis(self):
        return MockRedisCache()
    
    @pytest.fixture
    def adapter(self, mock_redis):
        from src.omnix.infrastructure.adapters.cache_adapter import CacheAdapter
        return CacheAdapter(redis_cache=mock_redis)
    
    def test_request_count_increments(self, adapter):
        """Request count should increment on each operation."""
        assert adapter._request_count == 0
        
        adapter.get("key1")
        assert adapter._request_count == 1
        
        adapter.set("key2", "value")
        assert adapter._request_count == 2
    
    def test_hit_count_increments_on_hit(self, adapter):
        """Hit count should increment when key exists."""
        adapter.set("existing", "value")
        adapter.get("existing")
        assert adapter._hit_count == 1
    
    def test_miss_count_increments_on_miss(self, adapter):
        """Miss count should increment when key missing."""
        adapter.get("nonexistent")
        assert adapter._miss_count == 1
    
    def test_health_check_includes_telemetry(self, adapter):
        """Health check should include telemetry metrics."""
        adapter.set("key", "value")
        adapter.get("key")
        adapter.get("missing")
        
        health = adapter.health_check()
        assert health['request_count'] == 3
        assert health['hit_count'] == 1
        assert health['miss_count'] == 1
        assert 'hit_rate_pct' in health
        assert 'error_rate_pct' in health


class BrokenRedisCache:
    """Mock for Redis cache that simulates unavailable Redis."""
    client = None
    
    def get(self, key: str):
        return None
    
    def set(self, key: str, value, ttl: int = 300):
        return False
    
    def delete(self, key: str):
        return True
    
    def exists(self, key: str):
        return False


class TestCacheAdapterGracefulDegradation:
    """Test graceful degradation when Redis unavailable."""
    
    @pytest.fixture
    def broken_redis(self):
        return BrokenRedisCache()
    
    @pytest.fixture
    def adapter_no_redis(self, broken_redis):
        from src.omnix.infrastructure.adapters.cache_adapter import CacheAdapter
        return CacheAdapter(redis_cache=broken_redis)
    
    def test_get_returns_none_when_no_redis(self, adapter_no_redis):
        """get should return None when Redis unavailable."""
        result = adapter_no_redis.get("any_key")
        assert result is None
    
    def test_set_returns_false_when_no_redis(self, adapter_no_redis):
        """set should return False when Redis unavailable."""
        result = adapter_no_redis.set("any_key", "value")
        assert result is False
    
    def test_delete_returns_true_when_no_redis(self, adapter_no_redis):
        """delete should return True when Redis unavailable (idempotent)."""
        result = adapter_no_redis.delete("any_key")
        assert result is True
    
    def test_exists_returns_false_when_no_redis(self, adapter_no_redis):
        """exists should return False when Redis unavailable."""
        result = adapter_no_redis.exists("any_key")
        assert result is False
    
    def test_is_connected_returns_false_when_no_redis(self, adapter_no_redis):
        """is_connected should return False when Redis unavailable."""
        assert adapter_no_redis.is_connected() is False
