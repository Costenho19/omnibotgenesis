"""
OMNIX Driven Ports - Output Interfaces

These ports define contracts for external services that the application
depends on (databases, caches, exchanges, AI providers, etc.).

All driven ports are defined as typing.Protocol for structural subtyping,
allowing any class that implements the required methods to be used.
"""

from src.omnix.ports.driven.trading_port import TradingPort
from src.omnix.ports.driven.database_port import (
    DatabasePort,
    TradeRepositoryPort,
    PositionRepositoryPort,
    UserRepositoryPort,
)
from src.omnix.ports.driven.cache_port import CachePort
from src.omnix.ports.driven.ai_inference_port import AIInferencePort
from src.omnix.ports.driven.market_data_port import MarketDataPort, TechnicalIndicatorPort
from src.omnix.ports.driven.notification_port import NotificationPort

__all__ = [
    "TradingPort",
    "DatabasePort",
    "TradeRepositoryPort",
    "PositionRepositoryPort",
    "UserRepositoryPort",
    "CachePort",
    "AIInferencePort",
    "MarketDataPort",
    "TechnicalIndicatorPort",
    "NotificationPort",
]
