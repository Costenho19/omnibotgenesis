"""
OMNIX V6.5.4d Test Configuration

Phase 0 Foundation - Pytest baseline setup

CRITICAL: Environment variables MUST be set BEFORE any imports
that could trigger omnix_config loading.
"""
import os

os.environ["TESTING"] = "true"
os.environ["TELEGRAM_BOT_TOKEN"] = "test-mode-token-for-pytest"
os.environ.setdefault("TRADING_PROFILE", "PAPER_AGGRESSIVE")

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def mock_env(monkeypatch):
    """Set up mock environment variables for testing."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
    monkeypatch.setenv("TESTING", "true")


@pytest.fixture
def sample_trade_data():
    """Sample trade data for testing."""
    return {
        "pair": "BTC/USD",
        "direction": "buy",
        "quantity": 0.01,
        "entry_price": 50000.0,
        "confidence": 0.75,
        "strategy": "QuantumMomentum",
    }


@pytest.fixture
def sample_market_data():
    """Sample market data for testing."""
    return {
        "pair": "BTC/USD",
        "price": 50000.0,
        "volume_24h": 1000000000,
        "change_24h": 2.5,
        "high_24h": 51000.0,
        "low_24h": 49000.0,
    }
