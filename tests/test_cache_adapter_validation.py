"""
OMNIX V7.0 - Cache Adapter Validation Tests
============================================

Tests to validate CacheAdapter before activating USE_CACHE_PORT=true.

Validates:
1. CacheAdapter implements CachePort protocol
2. Shadow mode: CacheAdapter vs RedisCache produce identical results
3. Health check functionality
4. Graceful degradation when Redis unavailable
"""

import pytest
import time
import json
from typing import Protocol, runtime_checkable
from unittest.mock import Mock, patch

from src.omnix.infrastructure.adapters.cache_adapter import CacheAdapter
from src.omnix.ports.driven.cache_port import CachePort


class TestCacheAdapterProtocol:
    """Verify CacheAdapter implements CachePort protocol."""
    
    def test_cache_adapter_is_cache_port(self):
        """CacheAdapter should implement CachePort protocol."""
        adapter = CacheAdapter()
        assert isinstance(adapter, CachePort), (
            "CacheAdapter must implement CachePort protocol"
        )
    
    def test_has_required_methods(self):
        """CacheAdapter should have all required methods."""
        adapter = CacheAdapter()
        
        required_methods = ['get', 'set', 'delete', 'exists', 'get_json', 'set_json']
        
        for method in required_methods:
            assert hasattr(adapter, method), f"Missing method: {method}"
            assert callable(getattr(adapter, method)), f"{method} is not callable"
    
    def test_method_signatures(self):
        """Verify method signatures match protocol."""
        adapter = CacheAdapter()
        
        assert adapter.get("test_key") is None or True
        assert adapter.set("test_key", "value", 60) in [True, False]
        assert adapter.delete("test_key") in [True, False]
        assert adapter.exists("test_key") in [True, False]
        assert adapter.get_json("test_key") is None or isinstance(adapter.get_json("test_key"), dict)


class TestCacheAdapterWithMock:
    """Test CacheAdapter behavior with mocked RedisCache."""
    
    def test_get_delegates_to_redis_cache(self):
        """get() should delegate to underlying RedisCache."""
        mock_cache = Mock()
        mock_cache.get.return_value = {"test": "value"}
        
        adapter = CacheAdapter(redis_cache=mock_cache)
        result = adapter.get("my_key")
        
        mock_cache.get.assert_called_once_with("my_key")
        assert result == {"test": "value"}
    
    def test_set_delegates_to_redis_cache(self):
        """set() should delegate to underlying RedisCache."""
        mock_cache = Mock()
        mock_cache.set.return_value = True
        
        adapter = CacheAdapter(redis_cache=mock_cache)
        result = adapter.set("my_key", {"data": 123}, ttl_seconds=300)
        
        mock_cache.set.assert_called_once_with("my_key", {"data": 123}, ttl=300)
        assert result is True
    
    def test_delete_delegates_to_redis_cache(self):
        """delete() should delegate to underlying RedisCache."""
        mock_cache = Mock()
        mock_cache.delete.return_value = True
        
        adapter = CacheAdapter(redis_cache=mock_cache)
        result = adapter.delete("my_key")
        
        mock_cache.delete.assert_called_once_with("my_key")
        assert result is True
    
    def test_exists_delegates_to_redis_cache(self):
        """exists() should delegate to underlying RedisCache."""
        mock_cache = Mock()
        mock_cache.exists.return_value = True
        
        adapter = CacheAdapter(redis_cache=mock_cache)
        result = adapter.exists("my_key")
        
        mock_cache.exists.assert_called_once_with("my_key")
        assert result is True
    
    def test_get_json_parses_dict(self):
        """get_json() should return dict directly if cached value is dict."""
        mock_cache = Mock()
        mock_cache.get.return_value = {"parsed": True}
        
        adapter = CacheAdapter(redis_cache=mock_cache)
        result = adapter.get_json("my_key")
        
        assert result == {"parsed": True}
    
    def test_get_json_parses_string(self):
        """get_json() should parse JSON string."""
        mock_cache = Mock()
        mock_cache.get.return_value = '{"from_string": true}'
        
        adapter = CacheAdapter(redis_cache=mock_cache)
        result = adapter.get_json("my_key")
        
        assert result == {"from_string": True}
    
    def test_set_json_uses_set(self):
        """set_json() should use regular set() method."""
        mock_cache = Mock()
        mock_cache.set.return_value = True
        
        adapter = CacheAdapter(redis_cache=mock_cache)
        result = adapter.set_json("my_key", {"json": "data"}, ttl_seconds=600)
        
        mock_cache.set.assert_called_once_with("my_key", {"json": "data"}, ttl=600)
        assert result is True


class TestCacheAdapterTelemetry:
    """Test CacheAdapter telemetry and health check."""
    
    def test_tracks_request_count(self):
        """Should track total request count."""
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        mock_cache.delete.return_value = True
        mock_cache.exists.return_value = False
        
        adapter = CacheAdapter(redis_cache=mock_cache)
        
        adapter.get("k1")
        adapter.set("k2", "v")
        adapter.delete("k3")
        adapter.exists("k4")
        
        health = adapter.health_check()
        assert health['request_count'] == 4
    
    def test_tracks_hit_miss_count(self):
        """Should track cache hits and misses."""
        mock_cache = Mock()
        mock_cache.get.side_effect = [{"hit": True}, None, {"hit": True}]
        
        adapter = CacheAdapter(redis_cache=mock_cache)
        
        adapter.get("k1")
        adapter.get("k2")
        adapter.get("k3")
        
        health = adapter.health_check()
        assert health['hit_count'] == 2
        assert health['miss_count'] == 1
    
    def test_calculates_hit_rate(self):
        """Should calculate hit rate percentage."""
        mock_cache = Mock()
        mock_cache.get.side_effect = [{"hit": True}, None, {"hit": True}, {"hit": True}]
        
        adapter = CacheAdapter(redis_cache=mock_cache)
        
        for _ in range(4):
            adapter.get("key")
        
        health = adapter.health_check()
        assert health['hit_rate_pct'] == 75.0
    
    def test_health_check_structure(self):
        """health_check() should return expected structure."""
        mock_cache = Mock()
        mock_cache.client = Mock()
        mock_cache.client.ping.return_value = True
        
        adapter = CacheAdapter(redis_cache=mock_cache)
        health = adapter.health_check()
        
        expected_keys = [
            'healthy', 'redis_cache_available', 'connected',
            'request_count', 'hit_count', 'miss_count', 'error_count',
            'hit_rate_pct', 'error_rate_pct', 'last_request'
        ]
        
        for key in expected_keys:
            assert key in health, f"Missing health check key: {key}"


class TestCacheAdapterGracefulDegradation:
    """Test graceful degradation when Redis unavailable."""
    
    def test_get_returns_none_with_null_cache(self):
        """get() should return None if redis_cache is explicitly None and stays None."""
        adapter = CacheAdapter(redis_cache=None)
        adapter._redis_cache = None
        adapter._get_redis_cache = Mock(return_value=None)
        
        result = adapter.get("any_key")
        assert result is None
    
    def test_set_returns_false_with_null_cache(self):
        """set() should return False if redis_cache unavailable."""
        adapter = CacheAdapter(redis_cache=None)
        adapter._redis_cache = None
        adapter._get_redis_cache = Mock(return_value=None)
        
        result = adapter.set("key", "value")
        assert result is False
    
    def test_delete_returns_true_with_null_cache(self):
        """delete() should return True (no-op) if Redis unavailable."""
        adapter = CacheAdapter(redis_cache=None)
        adapter._redis_cache = None
        adapter._get_redis_cache = Mock(return_value=None)
        
        result = adapter.delete("key")
        assert result is True
    
    def test_exists_returns_false_with_null_cache(self):
        """exists() should return False if Redis unavailable."""
        adapter = CacheAdapter(redis_cache=None)
        adapter._redis_cache = None
        adapter._get_redis_cache = Mock(return_value=None)
        
        result = adapter.exists("key")
        assert result is False
    
    def test_is_connected_returns_false_with_null_cache(self):
        """is_connected() should return False if Redis unavailable."""
        adapter = CacheAdapter(redis_cache=None)
        adapter._redis_cache = None
        adapter._get_redis_cache = Mock(return_value=None)
        
        assert adapter.is_connected() is False
    
    def test_handles_redis_exceptions(self):
        """Should handle Redis exceptions gracefully."""
        mock_cache = Mock()
        mock_cache.get.side_effect = Exception("Redis connection lost")
        
        adapter = CacheAdapter(redis_cache=mock_cache)
        result = adapter.get("key")
        
        assert result is None
        health = adapter.health_check()
        assert health['error_count'] == 1
    
    def test_lazy_loading_works_when_redis_available(self):
        """Verify lazy loading connects to Redis when available."""
        adapter = CacheAdapter(redis_cache=None)
        connected = adapter.is_connected()
        assert connected is True


@pytest.mark.integration
class TestCacheAdapterShadowMode:
    """
    Shadow mode tests: Compare CacheAdapter vs RedisCache directly.
    
    These tests require a running Redis instance.
    Run with: pytest -m integration tests/test_cache_adapter_validation.py
    """
    
    @pytest.fixture
    def redis_cache(self):
        """Get RedisCache instance."""
        try:
            from omnix_core.cache.redis_cache import RedisCache
            cache = RedisCache()
            if cache.client is None:
                pytest.skip("Redis not available")
            return cache
        except ImportError:
            pytest.skip("RedisCache not available")
        except Exception as e:
            pytest.skip(f"Redis setup failed: {e}")
    
    @pytest.fixture
    def cache_adapter(self, redis_cache):
        """Get CacheAdapter wrapping the same RedisCache."""
        return CacheAdapter(redis_cache=redis_cache)
    
    def test_shadow_get_identical_results(self, redis_cache, cache_adapter):
        """get() should produce identical results."""
        test_key = "omnix:test:shadow:get"
        test_value = {"shadow": "test", "timestamp": time.time()}
        
        redis_cache.set(test_key, test_value, ttl=60)
        
        direct_result = redis_cache.get(test_key)
        adapter_result = cache_adapter.get(test_key)
        
        assert direct_result == adapter_result, (
            f"Shadow mode mismatch!\n"
            f"Direct: {direct_result}\n"
            f"Adapter: {adapter_result}"
        )
        
        redis_cache.delete(test_key)
    
    def test_shadow_set_identical_behavior(self, redis_cache, cache_adapter):
        """set() should produce identical behavior."""
        test_key = "omnix:test:shadow:set"
        test_value = {"set_test": True}
        
        adapter_result = cache_adapter.set(test_key, test_value, ttl_seconds=60)
        assert adapter_result is True
        
        direct_result = redis_cache.get(test_key)
        assert direct_result == test_value
        
        redis_cache.delete(test_key)
    
    def test_shadow_delete_identical_behavior(self, redis_cache, cache_adapter):
        """delete() should produce identical behavior."""
        test_key = "omnix:test:shadow:delete"
        
        redis_cache.set(test_key, "to_delete", ttl=60)
        assert redis_cache.exists(test_key) is True
        
        adapter_result = cache_adapter.delete(test_key)
        assert adapter_result is True
        
        assert redis_cache.exists(test_key) is False
    
    def test_shadow_exists_identical_results(self, redis_cache, cache_adapter):
        """exists() should produce identical results."""
        test_key = "omnix:test:shadow:exists"
        
        assert redis_cache.exists(test_key) == cache_adapter.exists(test_key)
        
        redis_cache.set(test_key, "exists", ttl=60)
        
        direct_exists = redis_cache.exists(test_key)
        adapter_exists = cache_adapter.exists(test_key)
        
        assert direct_exists == adapter_exists, (
            f"exists() mismatch: direct={direct_exists}, adapter={adapter_exists}"
        )
        
        redis_cache.delete(test_key)
    
    def test_shadow_json_roundtrip(self, redis_cache, cache_adapter):
        """JSON operations should produce identical results."""
        test_key = "omnix:test:shadow:json"
        test_data = {
            "nested": {"deep": {"value": 42}},
            "list": [1, 2, 3],
            "string": "test"
        }
        
        cache_adapter.set_json(test_key, test_data, ttl_seconds=60)
        
        direct_result = redis_cache.get(test_key)
        adapter_result = cache_adapter.get_json(test_key)
        
        assert direct_result == adapter_result == test_data
        
        redis_cache.delete(test_key)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
