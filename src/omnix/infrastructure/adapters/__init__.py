"""
OMNIX V7.0 Infrastructure Adapters
===================================
Adapters implementing application ports by wrapping legacy services.

Available Adapters:
- TradingServiceAdapter: Wraps TradingService for ITradingService port
- RiskGuardianAdapter: Wraps RiskGuardian for IRiskPort
- CoherenceEngineAdapter: Wraps CoherenceEngine for ICoherenceEnginePort
- KrakenAdapter: Implements TradingPort + MarketDataPort for Kraken exchange
- GeminiAdapter: Implements AIInferencePort for AI inference (Gemini/OpenAI/Anthropic)
- TelegramBotAdapter: Implements ITelegramBot for Telegram bot operations
- NotificationAdapter: Implements NotificationPort for Telegram notifications (Phase 4A)
- CacheAdapter: Implements CachePort for Redis cache operations (Phase 4B)
- DatabaseAdapter: Implements DatabasePort for PostgreSQL operations (Phase 4C)

Migration Status: Phase 4C - MEDIUM-COUPLING SERVICES MIGRATION
"""

from src.omnix.infrastructure.adapters.trading_adapter import TradingServiceAdapter
from src.omnix.infrastructure.adapters.risk_adapter import RiskGuardianAdapter
from src.omnix.infrastructure.adapters.coherence_adapter import CoherenceEngineAdapter
from src.omnix.infrastructure.adapters.kraken_adapter import KrakenAdapter
from src.omnix.infrastructure.adapters.gemini_adapter import GeminiAdapter
from src.omnix.infrastructure.adapters.telegram_adapter import TelegramBotAdapter
from src.omnix.infrastructure.adapters.notification_adapter import NotificationAdapter
from src.omnix.infrastructure.adapters.cache_adapter import CacheAdapter
from src.omnix.infrastructure.adapters.database_adapter import DatabaseAdapter
from src.omnix.infrastructure.adapters.market_intel_adapter import MarketIntelAdapter
from src.omnix.infrastructure.adapters.execution_adapter import ExecutionAdapter
from src.omnix.infrastructure.adapters.risk_control_adapter import RiskControlAdapter
from src.omnix.infrastructure.adapters.derivatives_adapter import DerivativesAdapter
from src.omnix.infrastructure.adapters.portfolio_adapter import PortfolioAdapter
from src.omnix.infrastructure.adapters.optimization_adapter import OptimizationAdapter
from src.omnix.infrastructure.adapters.intent_classification_adapter import (
    IntentClassificationAdapter,
    NLPCommandShim,
)

__all__ = [
    "TradingServiceAdapter",
    "RiskGuardianAdapter",
    "CoherenceEngineAdapter",
    "KrakenAdapter",
    "GeminiAdapter",
    "TelegramBotAdapter",
    "NotificationAdapter",
    "CacheAdapter",
    "DatabaseAdapter",
    "MarketIntelAdapter",
    "ExecutionAdapter",
    "RiskControlAdapter",
    "DerivativesAdapter",
    "PortfolioAdapter",
    "OptimizationAdapter",
    "IntentClassificationAdapter",
    "NLPCommandShim",
]
