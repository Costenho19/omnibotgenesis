"""
OMNIX Ports - Interface Contracts (Hexagonal Architecture)

This package defines Protocol-based interfaces following SOLID principles:

Driven Ports (Output - towards external services):
- TradingPort: Exchange adapters (Kraken, Alpaca, Paper)
- DatabasePort: PostgreSQL repositories
- CachePort: Redis operations
- AIInferencePort: LLM providers (Gemini, OpenAI, Claude)
- MarketDataPort: Market data providers
- NotificationPort: Messaging (Telegram)

Driver Ports (Input - from users):
- RestApiPort: Flask API endpoints
- TelegramPort: Bot command handlers

Usage:
    from src.omnix.ports.driven import TradingPort, CachePort
    from src.omnix.ports.driver import TelegramPort
"""

from src.omnix.ports import driven
from src.omnix.ports import driver

__all__ = ["driven", "driver"]
