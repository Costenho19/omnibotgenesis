"""
OMNIX V6.5.4d Smoke Tests

Phase 0 Foundation - Basic import and structure verification
These tests verify critical modules can be imported without errors.
"""
import pytest


class TestCoreImports:
    """Verify core module imports work correctly."""

    def test_import_trading_profiles(self):
        """Trading profiles should be importable."""
        from omnix_core.config import trading_profiles
        assert hasattr(trading_profiles, 'ProfileName')

    def test_import_logger(self):
        """Logger utility should be importable."""
        from omnix_core.utils import logger
        assert hasattr(logger, 'get_logger')

    def test_import_redis_cache(self):
        """Redis cache should be importable."""
        from omnix_core.cache import redis_cache
        assert hasattr(redis_cache, 'RedisCache')


class TestServiceImports:
    """Verify service module imports work correctly."""

    def test_import_ai_service_interfaces(self):
        """AI service interfaces should be importable (SOLID reference)."""
        from omnix_services.ai_service.interfaces import ai_gateway
        assert hasattr(ai_gateway, 'AIGatewayProtocol')

    def test_import_ai_service_container(self):
        """AI service container should be importable (DI reference)."""
        from omnix_services.ai_service import container
        assert hasattr(container, 'AIServiceContainer')

    def test_import_database_gateway(self):
        """Database gateway should be importable."""
        from omnix_services.database_service import database_gateway
        assert database_gateway is not None


class TestPortsImports:
    """Verify hexagonal ports are importable."""

    def test_import_driven_ports(self):
        """Driven ports should be importable."""
        from omnix.ports import driven
        assert driven is not None

    def test_import_driver_ports(self):
        """Driver ports should be importable."""
        from omnix.ports import driver
        assert driver is not None

    def test_import_trading_port(self):
        """Trading port protocol should be importable."""
        from omnix.ports.driven.trading_port import TradingPort
        assert TradingPort is not None


class TestConfigImports:
    """Verify configuration modules work correctly."""

    def test_import_settings(self):
        """Settings module should be importable."""
        from omnix_config import settings
        assert settings is not None

    def test_trading_profile_enum(self):
        """Trading profile should have expected values."""
        from omnix_core.config.trading_profiles import ProfileName
        assert hasattr(ProfileName, 'PRODUCTION_STABLE')


class TestStructureVerification:
    """Verify project structure is correct."""

    def test_src_omnix_exists(self):
        """New src/omnix structure should exist."""
        from pathlib import Path
        src_omnix = Path("src/omnix")
        assert src_omnix.exists(), "src/omnix directory should exist"

    def test_src_omnix_subdirs(self):
        """src/omnix should have required subdirectories."""
        from pathlib import Path
        required_dirs = ["domain", "application", "infrastructure", "interfaces", "config", "bootstrap"]
        for dir_name in required_dirs:
            path = Path(f"src/omnix/{dir_name}")
            assert path.exists(), f"src/omnix/{dir_name} should exist"
