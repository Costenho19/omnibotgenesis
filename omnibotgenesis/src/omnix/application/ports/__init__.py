"""
OMNIX V7.0 Application Ports
==============================
Protocol interfaces for dependency injection.

These ports define the contracts between application layer
and infrastructure. Implementations are provided via the DI container.
"""

from src.omnix.application.ports.trading_port import (
    ITradingService,
    IOrderExecutor,
)
from src.omnix.application.ports.market_data_port import (
    IMarketDataService,
    IPriceProvider,
)
from src.omnix.application.ports.repository_ports import (
    IRiskRepository,
    ISignalRepository,
    ITradeRepository,
    IPositionRepository,
)
from src.omnix.application.ports.telegram_port import (
    ITelegramBot,
    ITelegramNotifier,
    TelegramMessage,
    TelegramResponse,
)

__all__ = [
    "ITradingService",
    "IOrderExecutor",
    "IMarketDataService",
    "IPriceProvider",
    "IRiskRepository",
    "ISignalRepository",
    "ITradeRepository",
    "IPositionRepository",
    "ITelegramBot",
    "ITelegramNotifier",
    "TelegramMessage",
    "TelegramResponse",
]
