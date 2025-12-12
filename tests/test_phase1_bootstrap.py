"""
Phase 1 Bootstrap Tests
========================
Tests for src/omnix/config/settings.py and src/omnix/bootstrap/

These tests verify that the Phase 1 refactoring maintains backward compatibility
and correctly centralizes configuration.
"""

import os
import pytest
from unittest.mock import patch


class TestSettings:
    """Tests for centralized Settings class."""
    
    def test_settings_import(self):
        """Verify Settings can be imported from new location."""
        from src.omnix.config import get_settings, Settings
        assert get_settings is not None
        assert Settings is not None
    
    def test_settings_singleton(self):
        """Verify get_settings returns cached instance."""
        from src.omnix.config import get_settings, clear_settings_cache
        clear_settings_cache()
        
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
    
    def test_settings_defaults(self):
        """Verify sensible defaults are set."""
        from src.omnix.config import get_settings, clear_settings_cache
        clear_settings_cache()
        
        settings = get_settings()
        assert settings.port == 5000 or isinstance(settings.port, int)
        assert settings.db_pool_min >= 1
        assert settings.db_pool_max >= settings.db_pool_min
    
    def test_settings_trading_profile(self):
        """Verify trading profile can be read."""
        from src.omnix.config import get_settings, clear_settings_cache
        clear_settings_cache()
        
        settings = get_settings()
        assert isinstance(settings.trading_profile, str)
    
    def test_settings_paper_mode(self):
        """Verify paper_mode is a boolean."""
        from src.omnix.config import get_settings, clear_settings_cache
        clear_settings_cache()
        
        settings = get_settings()
        assert isinstance(settings.paper_mode, bool)
    
    def test_settings_to_dict(self):
        """Verify to_dict masks sensitive values."""
        from src.omnix.config import get_settings, clear_settings_cache
        clear_settings_cache()
        
        settings = get_settings()
        data = settings.to_dict()
        
        assert 'trading_profile' in data
        assert 'paper_mode' in data
        if settings.database_url:
            assert data['database_url'] == '***'
    
    @patch.dict(os.environ, {'TRADING_PROFILE': 'TEST_PROFILE'})
    def test_settings_reads_env(self):
        """Verify settings reads from environment."""
        from src.omnix.config import get_settings, clear_settings_cache
        clear_settings_cache()
        
        settings = get_settings()
        assert settings.trading_profile == 'TEST_PROFILE'


class TestContainer:
    """Tests for DI Container."""
    
    def test_container_import(self):
        """Verify Container can be imported."""
        from src.omnix.bootstrap import Container, get_container
        assert Container is not None
        assert get_container is not None
    
    def test_container_create(self):
        """Verify Container.create() works."""
        from src.omnix.bootstrap import Container
        container = Container.create(lazy=True)
        assert container is not None
    
    def test_container_settings_access(self):
        """Verify container provides settings access."""
        from src.omnix.bootstrap import Container
        container = Container.create(lazy=True)
        
        settings = container.settings
        assert settings is not None
        assert hasattr(settings, 'trading_profile')
    
    def test_container_health_check(self):
        """Verify health_check returns expected structure."""
        from src.omnix.bootstrap import Container
        container = Container.create(lazy=True)
        
        health = container.health_check()
        assert 'database' in health
        assert 'cache' in health
        assert 'settings' in health
    
    def test_get_container_singleton(self):
        """Verify get_container returns same instance."""
        from src.omnix.bootstrap import get_container, reset_container
        reset_container()
        
        c1 = get_container()
        c2 = get_container()
        assert c1 is c2


class TestRuntime:
    """Tests for bootstrap runtime."""
    
    def test_bootstrap_import(self):
        """Verify bootstrap functions can be imported."""
        from src.omnix.bootstrap import bootstrap_omnix, quick_bootstrap
        assert bootstrap_omnix is not None
        assert quick_bootstrap is not None
    
    def test_quick_bootstrap(self):
        """Verify quick_bootstrap returns container."""
        from src.omnix.bootstrap import quick_bootstrap, reset_container
        reset_container()
        
        container = quick_bootstrap()
        assert container is not None
    
    def test_validate_environment(self):
        """Verify validate_environment returns expected structure."""
        from src.omnix.bootstrap import validate_environment
        
        valid, errors, warnings = validate_environment()
        assert isinstance(valid, bool)
        assert isinstance(errors, list)
        assert isinstance(warnings, list)


class TestProtocols:
    """Tests for Protocol interfaces."""
    
    def test_protocols_import(self):
        """Verify Protocol interfaces can be imported."""
        from src.omnix.bootstrap import (
            IDatabaseGateway,
            IRedisCache,
            ITradingService,
            IMarketDataService,
        )
        assert IDatabaseGateway is not None
        assert IRedisCache is not None
        assert ITradingService is not None
        assert IMarketDataService is not None


class TestLegacyCompatibility:
    """Integration tests to verify compatibility with legacy modules."""
    
    def test_main_module_import(self):
        """Verify main.py can be parsed without errors."""
        import ast
        with open('main.py', 'r') as f:
            source = f.read()
        ast.parse(source)
    
    def test_trading_profiles_accessible(self):
        """Verify trading profiles remain accessible."""
        from omnix_core.config import trading_profiles
        assert hasattr(trading_profiles, 'PRODUCTION_STABLE') or \
               hasattr(trading_profiles, 'INSTITUTIONAL_PROFILE') or \
               hasattr(trading_profiles, 'get_profile_by_name')
    
    def test_database_gateway_import(self):
        """Verify database gateway can be imported."""
        from omnix_services.database_service.database_gateway import DatabaseGateway
        assert DatabaseGateway is not None
    
    def test_redis_cache_import(self):
        """Verify redis cache can be imported."""
        from omnix_core.cache.redis_cache import RedisCache
        assert RedisCache is not None
    
    def test_settings_env_coverage(self):
        """Verify settings covers key environment variables used in legacy code."""
        from src.omnix.config import get_settings
        settings = get_settings()
        
        legacy_env_keys = [
            'database_url',
            'redis_url',
            'trading_profile',
            'paper_mode',
            'telegram_bot_token',
            'kraken_api_key',
            'gemini_api_key',
            'session_secret',
            'port',
            'log_level',
        ]
        
        for key in legacy_env_keys:
            assert hasattr(settings, key), f"Settings missing legacy key: {key}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
