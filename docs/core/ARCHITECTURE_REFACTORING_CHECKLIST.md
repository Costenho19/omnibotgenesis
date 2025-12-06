# OMNIX V7.0 - Architecture Refactoring Checklist

**Document Version:** 1.3  
**Created:** December 5, 2025  
**Last Updated:** December 6, 2025  
**Status:** DRAFT - Pending Implementation (Post-Funding)  
**Estimated Total Effort:** 45-60 days (conservative)

> **RELATED DOCUMENTATION:**
> - [Omnix_TECHNICAL_REFERENCE.md](Omnix_TECHNICAL_REFERENCE.md) - Current V6.5.3 architecture
> - [OMNIX_MODULE_CATALOG.md](OMNIX_MODULE_CATALOG.md) - Complete module inventory
> - [TRADING_FLOW_ARCHITECTURE.md](TRADING_FLOW_ARCHITECTURE.md) - Trading execution flow
> - [DATABASE_AUDIT_REPORT.md](DATABASE_AUDIT_REPORT.md) - Database schema reference

> **IMPORTANT NOTES:**
> - **Sync adapters:** TradingPort (ccxt), DatabasePort (psycopg) - blocking I/O
> - **Async adapters:** AIInferencePort, NotificationPort, MarketDataPort - network I/O benefits from async
> - Async wrappers for sync code via `asyncio.to_thread()` when needed
> - Trading must remain operational during migration (24/7 requirement)
> - PQC security and AI integrations must not regress

---

## Executive Summary

This document provides a comprehensive, task-by-task checklist for modernizing OMNIX from V6.5.3 to V7.0, adopting 2024-2025 software engineering standards including:

- **SOLID Principles** compliance
- **Hexagonal Architecture** (Ports & Adapters)
- **Dependency Injection** with `dependency-injector` library
- **Protocol-based interfaces** (typing.Protocol)
- **Modern Python tooling** (pyproject.toml, uv, ruff, mypy)

---

## Table of Contents

1. [Current State Analysis](#1-current-state-analysis)
2. [Target Architecture](#2-target-architecture)
3. [Phase 1: Protocol Ports (No Breaking Changes)](#phase-1-protocol-ports-no-breaking-changes)
4. [Phase 2: Dependency Injection Setup](#phase-2-dependency-injection-setup)
5. [Phase 3: Infrastructure Adapters](#phase-3-infrastructure-adapters)
6. [Phase 4: Monolithic File Refactoring](#phase-4-monolithic-file-refactoring)
7. [Phase 5: Testing & Validation](#phase-5-testing--validation)
8. [Risk Matrix](#risk-matrix)
9. [Rollback Procedures](#rollback-procedures)

---

## 1. Current State Analysis

> **NOTE:** For detailed current state, see:
> - [OMNIX_MODULE_CATALOG.md](OMNIX_MODULE_CATALOG.md) - Complete module inventory (~95,000 lines)
> - [Omnix_TECHNICAL_REFERENCE.md](Omnix_TECHNICAL_REFERENCE.md) - Architecture reference V6.5.3

### 1.1 SOLID Violations Identified (V6.5.3)

| Principle | Violation | Files Affected | Severity |
|-----------|-----------|----------------|----------|
| **SRP** | Files with 10+ responsibilities | `trading_system.py` (5,576), `enterprise_bot.py` (7,654), `auto_trading_bot.py` (3,932) | HIGH |
| **SRP** | Database service handles 50+ operations | `database_service.py` (4,860 lines) | HIGH |
| **OCP** | Hard-coded strategy lists requiring modification | `auto_trading_bot.py` lines 110-120 | MEDIUM |
| **OCP** | if/elif chains for market types | `coherence_engine.py`, `adaptive_engine.py` | MEDIUM |
| **LSP** | Inconsistent paper trading implementations | `paper_trading.py` vs `paper_trading_manager.py` | LOW |
| **ISP** | Fat interfaces (DatabaseService 50+ methods) | `database_service.py` | HIGH |
| **DIP** | Direct imports between layers | `omnix_core` → `omnix_services` | HIGH |

### 1.2 Summary Statistics (December 6, 2025)

| Package | Modules | Lines | Refactoring Priority |
|---------|---------|-------|---------------------|
| omnix_core | 20 | ~20,131 | P0-P1 |
| omnix_services | 150+ | ~62,613 | P0-P2 |
| omnix_dashboard | 40+ | ~9,037 | Well structured |
| **Total** | **160+** | **~95,000** | |

*For complete module breakdown, see [OMNIX_MODULE_CATALOG.md](OMNIX_MODULE_CATALOG.md)*

---

## 2. Target Architecture

### 2.1 Hexagonal Structure

```
omnix/
├── domain/                      # Pure business logic (NO external deps)
│   ├── entities/                # Trade, Position, Signal, User
│   ├── value_objects/           # Money, Percentage, SymbolPair
│   ├── services/                # Domain services (pure logic)
│   ├── events/                  # Domain events
│   └── exceptions/              # Domain exceptions
│
├── application/                 # Use cases (orchestration)
│   ├── use_cases/               # ExecuteTrade, AnalyzeMarket
│   ├── commands/                # Command objects
│   ├── queries/                 # Query objects
│   ├── dtos/                    # Data Transfer Objects
│   └── handlers/                # Command/Event handlers
│
├── ports/                       # Interface contracts (Protocols)
│   ├── driven/                  # Output ports (DB, Exchange, AI)
│   │   ├── trading_port.py
│   │   ├── database_port.py
│   │   ├── cache_port.py
│   │   ├── ai_inference_port.py
│   │   ├── market_data_port.py
│   │   └── notification_port.py
│   └── driver/                  # Input ports (API, Bot)
│       ├── rest_api_port.py
│       └── telegram_port.py
│
├── infrastructure/              # Concrete implementations
│   ├── adapters/
│   │   ├── exchanges/           # KrakenAdapter, AlpacaAdapter
│   │   ├── database/            # PostgresRepository
│   │   ├── cache/               # RedisAdapter
│   │   ├── ai/                  # GeminiAdapter, OpenAIAdapter
│   │   └── messaging/           # TelegramAdapter
│   ├── persistence/             # ORM models, migrations
│   └── config/                  # Settings, environment
│
├── bootstrap/                   # Application factory & DI
│   ├── containers.py            # DI containers
│   ├── app_factory.py           # Create application
│   └── wiring.py                # Wire dependencies
│
└── entrypoints/                 # Application entry points
    ├── flask_app.py             # Dashboard
    ├── telegram_bot.py          # Bot
    └── cli.py                   # Scripts
```

---

## Phase 1: Protocol Ports (No Breaking Changes)

**Duration:** 2-3 days  
**Risk Level:** LOW  
**Goal:** Add interface contracts without modifying existing code

### 1.1 Create Directory Structure

| Task ID | Task | File/Location | Effort | Dependencies | Status |
|---------|------|---------------|--------|--------------|--------|
| P1-001 | Create `ports/` package directory | `ports/__init__.py` | 5 min | None | ⬜ |
| P1-002 | Create `ports/driven/` subdirectory | `ports/driven/__init__.py` | 5 min | P1-001 | ⬜ |
| P1-003 | Create `ports/driver/` subdirectory | `ports/driver/__init__.py` | 5 min | P1-001 | ⬜ |

### 1.2 Define Trading Port

| Task ID | Task | Details | Effort | Dependencies | Status |
|---------|------|---------|--------|--------------|--------|
| P1-004 | Create `TradingPort` Protocol | `ports/driven/trading_port.py` | 30 min | P1-002 | ⬜ |

**Acceptance Criteria for P1-004:**
```python
# ports/driven/trading_port.py
from typing import Protocol, Optional, List, Dict, Any
from decimal import Decimal

class TradingPort(Protocol):
    """
    Contract for exchange adapters (Kraken, Alpaca, Paper).
    NOTE: All methods are SYNCHRONOUS (ccxt is sync by default).
    Use asyncio.to_thread() for async contexts if needed.
    """
    
    def execute_order(
        self,
        symbol: str,
        side: str,  # 'buy' | 'sell'
        amount: Decimal,
        order_type: str = 'market'
    ) -> Dict[str, Any]:
        """Execute a trade order. Returns order result."""
        ...
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get current price for symbol."""
        ...
    
    def get_balance(self) -> Dict[str, Decimal]:
        """Get account balances."""
        ...
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions."""
        ...
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order."""
        ...
    
    def is_connected(self) -> bool:
        """Check if exchange connection is active."""
        ...
```

**Type imports required:**
```python
from typing import Protocol, Optional, List, Dict, Any, runtime_checkable
from decimal import Decimal
from datetime import datetime
```

### 1.3 Define Database Port

| Task ID | Task | Details | Effort | Dependencies | Status |
|---------|------|---------|--------|--------------|--------|
| P1-005 | Create `DatabasePort` Protocol | `ports/driven/database_port.py` | 45 min | P1-002 | ⬜ |

**Acceptance Criteria for P1-005:**
```python
# ports/driven/database_port.py
from typing import Protocol, Optional, List, Dict, Any, Tuple

class DatabasePort(Protocol):
    """Contract for database operations"""
    
    def execute_query(
        self, 
        query: str, 
        params: Optional[Tuple] = None,
        fetch: bool = True
    ) -> Optional[List[Tuple]]:
        """Execute raw SQL query."""
        ...
    
    def health_check(self) -> Dict[str, Any]:
        """Check database connectivity."""
        ...

class TradeRepositoryPort(Protocol):
    """Contract for trade persistence"""
    
    def save_trade(self, trade: Dict[str, Any]) -> Optional[str]:
        """Save a trade record. Returns trade_id."""
        ...
    
    def get_trade_by_id(self, trade_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve trade by ID."""
        ...
    
    def get_trades_by_user(
        self, 
        user_id: str, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get trades for a user."""
        ...
    
    def update_trade(self, trade_id: str, updates: Dict[str, Any]) -> bool:
        """Update trade record."""
        ...

class PositionRepositoryPort(Protocol):
    """Contract for position persistence"""
    
    def save_position(self, position: Dict[str, Any]) -> Optional[str]:
        ...
    
    def get_open_positions(self, user_id: str) -> List[Dict[str, Any]]:
        ...
    
    def close_position(self, position_id: str, close_data: Dict) -> bool:
        ...

class UserRepositoryPort(Protocol):
    """Contract for user persistence"""
    
    def ensure_user_exists(
        self, 
        user_id: str, 
        username: Optional[str] = None
    ) -> bool:
        ...
    
    def get_user_settings(self, user_id: str) -> Optional[Dict[str, Any]]:
        ...
    
    def update_user_settings(self, user_id: str, settings: Dict) -> bool:
        ...
```

### 1.4 Define Cache Port

| Task ID | Task | Details | Effort | Dependencies | Status |
|---------|------|---------|--------|--------------|--------|
| P1-006 | Create `CachePort` Protocol | `ports/driven/cache_port.py` | 20 min | P1-002 | ⬜ |

**Acceptance Criteria for P1-006:**
```python
# ports/driven/cache_port.py
from typing import Protocol, Optional, Any

class CachePort(Protocol):
    """Contract for caching operations (Redis)"""
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        ...
    
    def set(
        self, 
        key: str, 
        value: Any, 
        ttl_seconds: int = 300
    ) -> bool:
        """Set value in cache with TTL."""
        ...
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        ...
    
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        ...
    
    def get_json(self, key: str) -> Optional[dict]:
        """Get JSON value from cache."""
        ...
    
    def set_json(
        self, 
        key: str, 
        value: dict, 
        ttl_seconds: int = 300
    ) -> bool:
        """Set JSON value in cache."""
        ...
```

### 1.5 Define AI Inference Port

| Task ID | Task | Details | Effort | Dependencies | Status |
|---------|------|---------|--------|--------------|--------|
| P1-007 | Create `AIInferencePort` Protocol | `ports/driven/ai_inference_port.py` | 30 min | P1-002 | ⬜ |

**Acceptance Criteria for P1-007:**
```python
# ports/driven/ai_inference_port.py
from typing import Protocol, Optional, List, Dict, Any

class AIInferencePort(Protocol):
    """Contract for AI model inference (Gemini, OpenAI, Claude)"""
    
    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Generate text from prompt."""
        ...
    
    async def analyze_market(
        self,
        market_data: Dict[str, Any],
        context: str = ""
    ) -> Dict[str, Any]:
        """Analyze market data and return insights."""
        ...
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """Multi-turn conversation."""
        ...
    
    def get_model_info(self) -> Dict[str, str]:
        """Get model name and version."""
        ...
```

### 1.6 Define Market Data Port

| Task ID | Task | Details | Effort | Dependencies | Status |
|---------|------|---------|--------|--------------|--------|
| P1-008 | Create `MarketDataPort` Protocol | `ports/driven/market_data_port.py` | 25 min | P1-002 | ⬜ |

**Acceptance Criteria for P1-008:**
```python
# ports/driven/market_data_port.py
from typing import Protocol, List, Dict, Any, Optional
from datetime import datetime

class MarketDataPort(Protocol):
    """Contract for market data providers"""
    
    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = '1h',
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get OHLCV candles."""
        ...
    
    async def get_orderbook(
        self,
        symbol: str,
        depth: int = 20
    ) -> Dict[str, Any]:
        """Get order book."""
        ...
    
    async def get_recent_trades(
        self,
        symbol: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get recent trades."""
        ...
    
    async def get_fear_greed_index(self) -> Dict[str, Any]:
        """Get Fear & Greed Index."""
        ...

class TechnicalIndicatorPort(Protocol):
    """Contract for technical analysis"""
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        ...
    
    def calculate_macd(
        self, 
        prices: List[float]
    ) -> Dict[str, float]:
        ...
    
    def calculate_bollinger_bands(
        self, 
        prices: List[float], 
        period: int = 20
    ) -> Dict[str, float]:
        ...
```

### 1.7 Define Notification Port

| Task ID | Task | Details | Effort | Dependencies | Status |
|---------|------|---------|--------|--------------|--------|
| P1-009 | Create `NotificationPort` Protocol | `ports/driven/notification_port.py` | 20 min | P1-002 | ⬜ |

**Acceptance Criteria for P1-009:**
```python
# ports/driven/notification_port.py
from typing import Protocol, Optional, List

class NotificationPort(Protocol):
    """Contract for sending notifications"""
    
    async def send_message(
        self,
        recipient_id: str,
        message: str,
        parse_mode: str = 'HTML'
    ) -> bool:
        """Send text message."""
        ...
    
    async def send_trade_alert(
        self,
        recipient_id: str,
        trade_data: dict
    ) -> bool:
        """Send formatted trade alert."""
        ...
    
    async def send_daily_summary(
        self,
        recipient_id: str,
        summary_data: dict
    ) -> bool:
        """Send daily trading summary."""
        ...
```

### 1.8 Define Driver Ports (Input)

| Task ID | Task | Details | Effort | Dependencies | Status |
|---------|------|---------|--------|--------------|--------|
| P1-010 | Create `TelegramBotPort` Protocol | `ports/driver/telegram_port.py` | 25 min | P1-003 | ⬜ |
| P1-011 | Create `RESTAPIPort` Protocol | `ports/driver/rest_api_port.py` | 20 min | P1-003 | ⬜ |

### 1.9 Export All Ports

| Task ID | Task | Details | Effort | Dependencies | Status |
|---------|------|---------|--------|--------------|--------|
| P1-012 | Update `ports/__init__.py` with exports | Export all Protocols | 15 min | P1-004 to P1-011 | ⬜ |
| P1-013 | Add type hints to existing services (read-only) | Document current signatures | 2 hours | P1-012 | ⬜ |
| P1-014 | Verify Protocols with mypy | `mypy ports/` | 30 min | P1-012 | ⬜ |

**Phase 1 Checklist Summary:**
- [ ] 14 tasks total
- [ ] Estimated: 6-8 hours
- [ ] Risk: LOW (no code changes)
- [ ] Rollback: Delete `ports/` directory

---

## Phase 2: Dependency Injection Setup

**Duration:** 3-4 days  
**Risk Level:** MEDIUM  
**Goal:** Add DI container without breaking legacy imports

### 2.1 Install Dependencies

| Task ID | Task | Command/File | Effort | Dependencies | Status |
|---------|------|--------------|--------|--------------|--------|
| P2-001 | Add `dependency-injector` to requirements | `dependency-injector>=4.48.0` | 5 min | None | ⬜ |
| P2-002 | Verify installation | `pip install dependency-injector` | 5 min | P2-001 | ⬜ |

### 2.2 Create Bootstrap Package

| Task ID | Task | File/Location | Effort | Dependencies | Status |
|---------|------|---------------|--------|--------------|--------|
| P2-003 | Create `bootstrap/` directory | `bootstrap/__init__.py` | 5 min | P2-002 | ⬜ |
| P2-004 | Create configuration provider | `bootstrap/config.py` | 30 min | P2-003 | ⬜ |

**Acceptance Criteria for P2-004:**
```python
# bootstrap/config.py
from dependency_injector import containers, providers
import os

class ConfigContainer(containers.DeclarativeContainer):
    """Configuration settings container"""
    
    config = providers.Configuration()
    
    # Database settings
    database_url = providers.Callable(
        lambda: os.environ.get('DATABASE_URL', '')
    )
    
    # Redis settings
    redis_url = providers.Callable(
        lambda: os.environ.get('REDIS_URL', '')
    )
    
    # Exchange API keys
    kraken_api_key = providers.Callable(
        lambda: os.environ.get('KRAKEN_API_KEY', '')
    )
    kraken_api_secret = providers.Callable(
        lambda: os.environ.get('KRAKEN_API_SECRET', '')
    )
    
    # AI API keys
    gemini_api_key = providers.Callable(
        lambda: os.environ.get('GEMINI_API_KEY', '')
    )
    
    # Trading mode
    paper_mode = providers.Callable(
        lambda: os.environ.get('TRADING_MODE', 'paper') == 'paper'
    )
```

### 2.3 Create Database Container

| Task ID | Task | File/Location | Effort | Dependencies | Status |
|---------|------|---------------|--------|--------------|--------|
| P2-005 | Create `DatabaseContainer` | `bootstrap/containers/database.py` | 1 hour | P2-004 | ⬜ |

**Acceptance Criteria for P2-005:**
```python
# bootstrap/containers/database.py
from dependency_injector import containers, providers
from omnix_services.database_service.database_gateway import DatabaseGateway
from omnix_services.database_service.database_manager import DatabaseManager

class DatabaseContainer(containers.DeclarativeContainer):
    """Database services container"""
    
    config = providers.Configuration()
    
    # Singleton for connection pool
    gateway = providers.Singleton(
        DatabaseGateway.get_instance
    )
    
    # Factory for database manager (adapter pattern)
    manager = providers.Singleton(
        DatabaseManager
    )
    
    # Trade repository (future: will implement TradeRepositoryPort)
    trade_repository = providers.Factory(
        lambda manager: manager,  # Placeholder - will be real adapter
        manager=manager
    )
```

### 2.4 Create Trading Container

| Task ID | Task | File/Location | Effort | Dependencies | Status |
|---------|------|---------------|--------|--------------|--------|
| P2-006 | Create `TradingContainer` | `bootstrap/containers/trading.py` | 1.5 hours | P2-004 | ⬜ |

**Acceptance Criteria for P2-006:**
```python
# bootstrap/containers/trading.py
from dependency_injector import containers, providers

class TradingContainer(containers.DeclarativeContainer):
    """Trading services container"""
    
    config = providers.Configuration()
    database = providers.DependenciesContainer()
    
    # Lazy import to avoid circular dependencies
    @providers.Singleton
    def trading_system():
        from omnix_core.trading_system import TradingSystem
        return TradingSystem()
    
    @providers.Singleton  
    def auto_trading_bot():
        from omnix_core.bot.auto_trading_bot import AutoTradingBot
        return AutoTradingBot()
    
    @providers.Factory
    def paper_trading_manager(database_manager):
        from omnix_services.trading_service.paper_trading_manager import PaperTradingManager
        return PaperTradingManager(database_manager)
    
    # Strategy registry (future: plugin system)
    @providers.Singleton
    def strategy_registry():
        return {}  # Will hold strategy instances
```

### 2.5 Create AI Container

| Task ID | Task | File/Location | Effort | Dependencies | Status |
|---------|------|---------------|--------|--------------|--------|
| P2-007 | Create `AIContainer` | `bootstrap/containers/ai.py` | 1 hour | P2-004 | ⬜ |

**Acceptance Criteria for P2-007:**
```python
# bootstrap/containers/ai.py
from dependency_injector import containers, providers

class AIContainer(containers.DeclarativeContainer):
    """AI services container"""
    
    config = providers.Configuration()
    
    @providers.Singleton
    def gemini_client():
        from omnix_services.ai_service.ai_models import get_gemini_model
        return get_gemini_model()
    
    @providers.Singleton
    def openai_client():
        import openai
        import os
        openai.api_key = os.environ.get('OPENAI_API_KEY', '')
        return openai
    
    @providers.Singleton
    def conversational_brain():
        from omnix_services.ai_service.conversational_ai_adapter import ConversationalBrain
        return ConversationalBrain()
```

### 2.6 Create Cache Container

| Task ID | Task | File/Location | Effort | Dependencies | Status |
|---------|------|---------------|--------|--------------|--------|
| P2-008 | Create `CacheContainer` | `bootstrap/containers/cache.py` | 45 min | P2-004 | ⬜ |

**Acceptance Criteria for P2-008:**
```python
# bootstrap/containers/cache.py
from dependency_injector import containers, providers

class CacheContainer(containers.DeclarativeContainer):
    """Cache services container"""
    
    config = providers.Configuration()
    
    @providers.Singleton
    def redis_cache():
        from omnix_core.cache.redis_cache import RedisCache
        return RedisCache()
    
    @providers.Singleton
    def state_manager():
        from omnix_core.cache.redis_state_manager import RedisStateManager
        return RedisStateManager()
```

### 2.7 Create Master Application Container

| Task ID | Task | File/Location | Effort | Dependencies | Status |
|---------|------|---------------|--------|--------------|--------|
| P2-009 | Create `ApplicationContainer` | `bootstrap/containers/__init__.py` | 1 hour | P2-005 to P2-008 | ⬜ |

**Acceptance Criteria for P2-009:**
```python
# bootstrap/containers/__init__.py
from dependency_injector import containers, providers
from .config import ConfigContainer
from .database import DatabaseContainer
from .trading import TradingContainer
from .ai import AIContainer
from .cache import CacheContainer

class ApplicationContainer(containers.DeclarativeContainer):
    """Master application container - wires all sub-containers"""
    
    # Configuration
    config = providers.Container(ConfigContainer)
    
    # Infrastructure containers
    database = providers.Container(
        DatabaseContainer,
        config=config.config
    )
    
    cache = providers.Container(
        CacheContainer,
        config=config.config
    )
    
    # Service containers
    ai = providers.Container(
        AIContainer,
        config=config.config
    )
    
    trading = providers.Container(
        TradingContainer,
        config=config.config,
        database=database
    )

# Global container instance
container = ApplicationContainer()
```

### 2.8 Wire to Flask Dashboard

| Task ID | Task | File/Location | Effort | Dependencies | Status |
|---------|------|---------------|--------|--------------|--------|
| P2-010 | Create Flask app factory with DI | `bootstrap/app_factory.py` | 1.5 hours | P2-009 | ⬜ |
| P2-011 | Wire DI to dashboard blueprints | `omnix_dashboard/app.py` modification | 1 hour | P2-010 | ⬜ |

**Acceptance Criteria for P2-010:**
```python
# bootstrap/app_factory.py
from flask import Flask
from dependency_injector.wiring import inject, Provide
from .containers import ApplicationContainer, container

def create_app(config_name: str = 'development') -> Flask:
    """Application factory with DI support"""
    
    # Initialize container
    container.config.from_dict({
        'environment': config_name
    })
    
    # Create Flask app
    app = Flask(__name__)
    
    # Wire container to modules that need injection
    container.wire(modules=[
        'omnix_dashboard.blueprints.api',
        'omnix_dashboard.blueprints.health',
        'omnix_dashboard.blueprints.trades',
    ])
    
    # Register blueprints
    from omnix_dashboard.blueprints import register_blueprints
    register_blueprints(app)
    
    # Store container reference
    app.container = container
    
    return app
```

### 2.9 Maintain Backward Compatibility

| Task ID | Task | File/Location | Effort | Dependencies | Status |
|---------|------|---------------|--------|--------------|--------|
| P2-012 | Create legacy bridge module | `bootstrap/legacy_bridge.py` | 45 min | P2-009 | ⬜ |
| P2-013 | Add deprecation warnings to direct imports | Various files | 2 hours | P2-012 | ⬜ |

**Acceptance Criteria for P2-012:**
```python
# bootstrap/legacy_bridge.py
"""
Legacy bridge - provides backward-compatible access to services
while emitting deprecation warnings.

Usage (old code):
    from omnix_services.database_service import DatabaseManager
    db = DatabaseManager()  # Direct instantiation

Usage (new code):
    from bootstrap.containers import container
    db = container.database.manager()  # DI injection
"""
import warnings
from functools import wraps

def deprecated_import(new_location: str):
    """Decorator to mark imports as deprecated"""
    def decorator(cls):
        original_init = cls.__init__
        
        @wraps(original_init)
        def new_init(self, *args, **kwargs):
            warnings.warn(
                f"{cls.__name__} direct instantiation is deprecated. "
                f"Use DI: {new_location}",
                DeprecationWarning,
                stacklevel=2
            )
            return original_init(self, *args, **kwargs)
        
        cls.__init__ = new_init
        return cls
    return decorator
```

### 2.10 Documentation & Testing

| Task ID | Task | Details | Effort | Dependencies | Status |
|---------|------|---------|--------|--------------|--------|
| P2-014 | Document DI usage patterns | `docs/DI_USAGE_GUIDE.md` | 1 hour | P2-011 | ⬜ |
| P2-015 | Write container unit tests | `tests/test_containers.py` | 2 hours | P2-009 | ⬜ |
| P2-016 | Integration test: DI + Flask | `tests/test_di_flask.py` | 1.5 hours | P2-011 | ⬜ |

**Phase 2 Checklist Summary:**
- [ ] 16 tasks total
- [ ] Estimated: 3-4 days
- [ ] Risk: MEDIUM (parallel systems)
- [ ] Rollback: Remove `bootstrap/` directory, revert `requirements.txt`

---

## Phase 3: Infrastructure Adapters

**Duration:** 5-7 days  
**Risk Level:** MEDIUM-HIGH  
**Goal:** Create concrete adapters implementing Port protocols

### 3.1 Create Infrastructure Directory

| Task ID | Task | File/Location | Effort | Dependencies | Status |
|---------|------|---------------|--------|--------------|--------|
| P3-001 | Create `infrastructure/` package | `infrastructure/__init__.py` | 5 min | Phase 2 | ⬜ |
| P3-002 | Create `infrastructure/adapters/` | Subdirectories | 10 min | P3-001 | ⬜ |

### 3.2 Database Adapters

| Task ID | Task | File/Location | Effort | Dependencies | Status |
|---------|------|---------------|--------|--------------|--------|
| P3-003 | Create `PostgresRepository` adapter | `infrastructure/adapters/database/postgres_repository.py` | 3 hours | P3-002 | ⬜ |
| P3-004 | Create `InMemoryRepository` for tests | `infrastructure/adapters/database/inmemory_repository.py` | 2 hours | P3-002 | ⬜ |

**Acceptance Criteria for P3-003:**
```python
# infrastructure/adapters/database/postgres_repository.py
from typing import Optional, List, Dict, Any, Tuple
from ports.driven.database_port import (
    DatabasePort, 
    TradeRepositoryPort,
    PositionRepositoryPort
)
from omnix_services.database_service.database_gateway import DatabaseGateway

class PostgresRepository:
    """
    Implements DatabasePort, TradeRepositoryPort, PositionRepositoryPort.
    Adapts DatabaseGateway to the Port protocols.
    """
    
    def __init__(self):
        self._gateway = DatabaseGateway.get_instance()
    
    # DatabasePort implementation
    def execute_query(
        self, 
        query: str, 
        params: Optional[Tuple] = None,
        fetch: bool = True
    ) -> Optional[List[Tuple]]:
        return self._gateway.execute_query(query, params, fetch)
    
    def health_check(self) -> Dict[str, Any]:
        stats = self._gateway.get_pool_stats()
        return {
            'connected': stats.get('status') == 'active',
            'pool_size': stats.get('pool_size', 0),
            'available': stats.get('pool_available', 0)
        }
    
    # TradeRepositoryPort implementation
    def save_trade(self, trade: Dict[str, Any]) -> Optional[str]:
        query = """
            INSERT INTO paper_trades 
            (user_id, symbol, side, entry_price, quantity, status, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            RETURNING id
        """
        params = (
            trade['user_id'],
            trade['symbol'],
            trade['side'],
            trade['entry_price'],
            trade['quantity'],
            trade.get('status', 'open')
        )
        result = self.execute_query(query, params, fetch=True)
        return str(result[0][0]) if result else None
    
    def get_trade_by_id(self, trade_id: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM paper_trades WHERE id = %s"
        result = self.execute_query(query, (trade_id,), fetch=True)
        if result:
            return self._row_to_trade_dict(result[0])
        return None
    
    def get_trades_by_user(
        self, 
        user_id: str, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        query = """
            SELECT * FROM paper_trades 
            WHERE user_id = %s 
            ORDER BY timestamp DESC 
            LIMIT %s
        """
        result = self.execute_query(query, (user_id, limit), fetch=True)
        return [self._row_to_trade_dict(row) for row in (result or [])]
    
    def _row_to_trade_dict(self, row: Tuple) -> Dict[str, Any]:
        """Convert database row to trade dictionary"""
        return {
            'id': row[0],
            'user_id': row[1],
            'symbol': row[2],
            'side': row[3],
            'entry_price': float(row[4]) if row[4] else None,
            'quantity': float(row[5]) if row[5] else None,
            'status': row[6],
            'timestamp': row[7]
        }
```

**Acceptance Criteria for P3-004:**
```python
# infrastructure/adapters/database/inmemory_repository.py
from typing import Optional, List, Dict, Any, Tuple
from uuid import uuid4
from datetime import datetime

class InMemoryRepository:
    """
    In-memory implementation of database ports for testing.
    No external dependencies.
    """
    
    def __init__(self):
        self._trades: Dict[str, Dict] = {}
        self._positions: Dict[str, Dict] = {}
        self._users: Dict[str, Dict] = {}
    
    def execute_query(
        self, 
        query: str, 
        params: Optional[Tuple] = None,
        fetch: bool = True
    ) -> Optional[List[Tuple]]:
        # For testing, just return empty results
        return [] if fetch else None
    
    def health_check(self) -> Dict[str, Any]:
        return {'connected': True, 'pool_size': 1, 'available': 1}
    
    def save_trade(self, trade: Dict[str, Any]) -> Optional[str]:
        trade_id = str(uuid4())
        self._trades[trade_id] = {
            **trade,
            'id': trade_id,
            'timestamp': datetime.utcnow()
        }
        return trade_id
    
    def get_trade_by_id(self, trade_id: str) -> Optional[Dict[str, Any]]:
        return self._trades.get(trade_id)
    
    def get_trades_by_user(
        self, 
        user_id: str, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        user_trades = [
            t for t in self._trades.values() 
            if t.get('user_id') == user_id
        ]
        return sorted(
            user_trades, 
            key=lambda x: x.get('timestamp', datetime.min),
            reverse=True
        )[:limit]
```

### 3.3 Exchange Adapters

| Task ID | Task | File/Location | Effort | Dependencies | Status |
|---------|------|---------------|--------|--------------|--------|
| P3-005 | Create `KrakenAdapter` | `infrastructure/adapters/exchanges/kraken_adapter.py` | 4 hours | P3-002 | ⬜ |
| P3-006 | Create `AlpacaAdapter` | `infrastructure/adapters/exchanges/alpaca_adapter.py` | 3 hours | P3-002 | ⬜ |
| P3-007 | Create `PaperTradingAdapter` | `infrastructure/adapters/exchanges/paper_adapter.py` | 2 hours | P3-002 | ⬜ |

**Acceptance Criteria for P3-005:**
```python
# infrastructure/adapters/exchanges/kraken_adapter.py
from typing import Dict, Any, List, Optional
from decimal import Decimal
import ccxt
from ports.driven.trading_port import TradingPort

class KrakenAdapter:
    """
    Implements TradingPort for Kraken exchange.
    Wraps ccxt.kraken client.
    NOTE: All methods are SYNCHRONOUS (ccxt is sync by default).
    """
    
    def __init__(self, api_key: str = '', api_secret: str = ''):
        self._client = ccxt.kraken({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'timeout': 30000
        })
        self._connected = False
    
    def execute_order(
        self,
        symbol: str,
        side: str,
        amount: Decimal,
        order_type: str = 'market'
    ) -> Dict[str, Any]:
        try:
            order = self._client.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=float(amount)
            )
            return {
                'success': True,
                'order_id': order['id'],
                'symbol': symbol,
                'side': side,
                'amount': float(amount),
                'price': order.get('price'),
                'status': order['status']
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        ticker = self._client.fetch_ticker(symbol)
        return {
            'symbol': symbol,
            'price': ticker['last'],
            'bid': ticker['bid'],
            'ask': ticker['ask'],
            'volume': ticker['quoteVolume'],
            'change_24h': ticker.get('percentage')
        }
    
    def get_balance(self) -> Dict[str, Decimal]:
        balance = self._client.fetch_balance()
        return {
            currency: Decimal(str(data.get('free', 0)))
            for currency, data in balance.items()
            if isinstance(data, dict) and data.get('free', 0) > 0
        }
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        orders = self._client.fetch_open_orders()
        return [
            {
                'order_id': o['id'],
                'symbol': o['symbol'],
                'side': o['side'],
                'amount': o['amount'],
                'price': o['price']
            }
            for o in orders
        ]
    
    def cancel_order(self, order_id: str) -> bool:
        try:
            self._client.cancel_order(order_id)
            return True
        except:
            return False
    
    def is_connected(self) -> bool:
        try:
            self._client.fetch_status()
            return True
        except:
            return False
```

### 3.4 Cache Adapters

| Task ID | Task | File/Location | Effort | Dependencies | Status |
|---------|------|---------------|--------|--------------|--------|
| P3-008 | Create `RedisAdapter` | `infrastructure/adapters/cache/redis_adapter.py` | 2 hours | P3-002 | ⬜ |
| P3-009 | Create `InMemoryCacheAdapter` | `infrastructure/adapters/cache/inmemory_cache.py` | 1 hour | P3-002 | ⬜ |

### 3.5 AI Adapters

| Task ID | Task | File/Location | Effort | Dependencies | Status |
|---------|------|---------------|--------|--------------|--------|
| P3-010 | Create `GeminiAdapter` | `infrastructure/adapters/ai/gemini_adapter.py` | 2 hours | P3-002 | ⬜ |
| P3-011 | Create `OpenAIAdapter` | `infrastructure/adapters/ai/openai_adapter.py` | 2 hours | P3-002 | ⬜ |
| P3-012 | Create `MockAIAdapter` for tests | `infrastructure/adapters/ai/mock_adapter.py` | 1 hour | P3-002 | ⬜ |

### 3.6 Messaging Adapters

| Task ID | Task | File/Location | Effort | Dependencies | Status |
|---------|------|---------------|--------|--------------|--------|
| P3-013 | Create `TelegramAdapter` | `infrastructure/adapters/messaging/telegram_adapter.py` | 3 hours | P3-002 | ⬜ |

### 3.7 Update DI Containers

| Task ID | Task | File/Location | Effort | Dependencies | Status |
|---------|------|---------------|--------|--------------|--------|
| P3-014 | Register adapters in DatabaseContainer | `bootstrap/containers/database.py` | 1 hour | P3-003, P3-004 | ⬜ |
| P3-015 | Register adapters in TradingContainer | `bootstrap/containers/trading.py` | 1 hour | P3-005 to P3-007 | ⬜ |
| P3-016 | Register adapters in CacheContainer | `bootstrap/containers/cache.py` | 30 min | P3-008, P3-009 | ⬜ |
| P3-017 | Register adapters in AIContainer | `bootstrap/containers/ai.py` | 30 min | P3-010 to P3-012 | ⬜ |

### 3.8 Adapter Tests

| Task ID | Task | File/Location | Effort | Dependencies | Status |
|---------|------|---------------|--------|--------------|--------|
| P3-018 | Unit tests for PostgresRepository | `tests/adapters/test_postgres.py` | 2 hours | P3-003 | ⬜ |
| P3-019 | Unit tests for KrakenAdapter | `tests/adapters/test_kraken.py` | 2 hours | P3-005 | ⬜ |
| P3-020 | Contract tests (adapter vs port) | `tests/contracts/` | 3 hours | P3-014 to P3-017 | ⬜ |

**Phase 3 Checklist Summary:**
- [ ] 20 tasks total
- [ ] Estimated: 5-7 days
- [ ] Risk: MEDIUM-HIGH (replacing implementations)
- [ ] Rollback: Remove `infrastructure/` directory, revert container changes

---

## Phase 4: Monolithic File Refactoring

**Duration:** 20-30 days  
**Risk Level:** HIGH  
**Goal:** Split large files into focused modules

> **MANDATORY:** All Phase 4 tasks MUST use the **Acceptance Criteria Template** defined in the "Acceptance Criteria Template (Phase 4)" section below. Before marking any P4-XXX task complete, verify:
> 1. ✅ Extraction Complete (new module exists, code moved, imports updated)
> 2. ✅ Dependency Wiring (DI provider registered, consumers updated)
> 3. ✅ Test Coverage (>80% unit tests, integration tests pass)
> 4. ✅ Documentation (docstrings, this checklist updated)
> 5. ✅ Backward Compatibility (original API unchanged, deprecation warnings)
> 6. ✅ Migration Safety (24/7 trading uninterrupted, PQC works, AI responds)

### 4.1 Refactor `trading_system.py` (5,576 lines → ~6 files)

| Task ID | Task | Details | Effort | Dependencies | Status |
|---------|------|---------|--------|--------------|--------|
| P4-001 | Extract `domain/entities/trading.py` | Trade, Position, Order entities | 2 hours | Phase 3 | ⬜ |
| P4-002 | Extract `domain/services/multi_currency.py` | Multi-currency logic (lines 333-621) | 3 hours | P4-001 | ⬜ |
| P4-003 | Extract `domain/services/pqc_signing.py` | PQC signing (lines 305-332) | 1 hour | P4-001 | ⬜ |
| P4-004 | Extract `application/use_cases/execute_trade.py` | Trade execution (lines 870-1012) | 3 hours | P4-001, P4-002 | ⬜ |
| P4-005 | Extract `infrastructure/adapters/exchanges/kraken_client.py` | Kraken init (lines 210-267) | 2 hours | P4-004 | ⬜ |
| P4-006 | Refactor `TradingSystem` to orchestrator | Thin wrapper using extracted modules | 4 hours | P4-001 to P4-005 | ⬜ |

**Acceptance Criteria for P4-006:**
- `TradingSystem` class < 500 lines
- All methods delegate to extracted services
- Backward-compatible API (same method signatures)
- 100% test coverage for public methods

### 4.2 Refactor `enterprise_bot.py` (7,627 lines → ~10 files)

| Task ID | Task | Details | Effort | Dependencies | Status |
|---------|------|---------|--------|--------------|--------|
| P4-007 | Extract `application/handlers/start_handler.py` | /start, /help commands | 2 hours | Phase 3 | ⬜ |
| P4-008 | Extract `application/handlers/trade_handler.py` | /buy, /sell, /trade commands | 3 hours | P4-007 | ⬜ |
| P4-009 | Extract `application/handlers/analysis_handler.py` | /analysis, /signals | 2 hours | P4-007 | ⬜ |
| P4-010 | Extract `application/handlers/portfolio_handler.py` | /portfolio, /balance | 2 hours | P4-007 | ⬜ |
| P4-011 | Extract `infrastructure/adapters/messaging/formatters.py` | Message formatting | 2 hours | P4-007 | ⬜ |
| P4-012 | Extract `infrastructure/adapters/messaging/keyboards.py` | Inline keyboards | 1 hour | P4-007 | ⬜ |
| P4-013 | Extract `application/handlers/callback_router.py` | Callback query routing | 2 hours | P4-011, P4-012 | ⬜ |
| P4-014 | Refactor `EnterpriseTelegramBot` to thin dispatcher | Route to handlers | 4 hours | P4-007 to P4-013 | ⬜ |

**Acceptance Criteria for P4-014:**
- `EnterpriseTelegramBot` class < 800 lines
- Each handler < 300 lines
- Clear separation: routing vs logic vs formatting
- All commands still functional

### 4.3 Refactor `auto_trading_bot.py` (3,660 lines → ~5 files)

| Task ID | Task | Details | Effort | Dependencies | Status |
|---------|------|---------|--------|--------------|--------|
| P4-015 | Extract `domain/services/strategy_registry.py` | Strategy loading & registration | 2 hours | Phase 3 | ⬜ |
| P4-016 | Extract `application/orchestrators/trading_cycle.py` | Main trading loop | 3 hours | P4-015 | ⬜ |
| P4-017 | Extract `domain/services/signal_aggregator.py` | Strategy signal aggregation | 2 hours | P4-015 | ⬜ |
| P4-018 | Extract `domain/services/position_sizer.py` | CAES position sizing | 2 hours | P4-017 | ⬜ |
| P4-019 | Refactor `AutoTradingBot` to orchestrator | Thin wrapper | 3 hours | P4-015 to P4-018 | ⬜ |

### 4.4 Refactor `database_service.py` (4,818 lines → ~8 files)

| Task ID | Task | Details | Effort | Dependencies | Status |
|---------|------|---------|--------|--------------|--------|
| P4-020 | Already done: Use `DatabaseGateway` | Pool management extracted | 0 | - | ✅ |
| P4-021 | Extract `infrastructure/persistence/trade_repository.py` | Trade CRUD | 2 hours | P3-003 | ⬜ |
| P4-022 | Extract `infrastructure/persistence/position_repository.py` | Position CRUD | 2 hours | P4-021 | ⬜ |
| P4-023 | Extract `infrastructure/persistence/user_repository.py` | User CRUD | 1.5 hours | P4-021 | ⬜ |
| P4-024 | Extract `infrastructure/persistence/balance_repository.py` | Balance history | 1.5 hours | P4-021 | ⬜ |
| P4-025 | Extract `infrastructure/persistence/analysis_repository.py` | Analysis records | 1.5 hours | P4-021 | ⬜ |
| P4-026 | Refactor `DatabaseServiceEnterprise` to facade | Thin wrapper | 3 hours | P4-021 to P4-025 | ⬜ |

### 4.5 Other Large Files

| Task ID | Task | Details | Effort | Dependencies | Status |
|---------|------|---------|--------|--------------|--------|
| P4-027 | Refactor `advanced_intelligence.py` (1,330 lines) | Split by analysis type | 4 hours | Phase 3 | ⬜ |
| P4-028 | Refactor `analytics_engine.py` (1,092 lines) | Split metrics vs telemetry | 3 hours | Phase 3 | ⬜ |
| P4-029 | Refactor `advanced_features.py` (1,216 lines) | Split by feature | 3 hours | Phase 3 | ⬜ |
| P4-030 | Refactor `adaptive_engine.py` (936 lines) | Extract calibration logic | 2 hours | Phase 3 | ⬜ |

**Phase 4 Checklist Summary:**
- [ ] 30 tasks total
- [ ] Estimated: 20-30 days (realistic: each major refactor = 3-5 days)
- [ ] Risk: HIGH (core refactoring)
- [ ] Prerequisites: All Phase 2-3 DI providers registered
- [ ] Rollback: Git revert to pre-Phase 4 commit

**IMPORTANT:** Phase 4 tasks must follow the Acceptance Criteria Template defined in the "Acceptance Criteria Template" section below.

---

## Phase 5: Testing & Validation

**Duration:** 3-5 days  
**Risk Level:** LOW  
**Goal:** Ensure all changes maintain functionality

### 5.1 Unit Tests

| Task ID | Task | Coverage Target | Effort | Dependencies | Status |
|---------|------|-----------------|--------|--------------|--------|
| P5-001 | Test all Port protocols | 100% | 3 hours | Phase 1 | ⬜ |
| P5-002 | Test DI containers | 100% | 2 hours | Phase 2 | ⬜ |
| P5-003 | Test database adapters | 90% | 3 hours | Phase 3 | ⬜ |
| P5-004 | Test exchange adapters | 80% | 3 hours | Phase 3 | ⬜ |
| P5-005 | Test extracted domain services | 90% | 4 hours | Phase 4 | ⬜ |

### 5.2 Integration Tests

| Task ID | Task | Scope | Effort | Dependencies | Status |
|---------|------|-------|--------|--------------|--------|
| P5-006 | Test Flask + DI integration | Dashboard endpoints | 3 hours | Phase 2 | ⬜ |
| P5-007 | Test trading flow end-to-end | Paper trade execution | 4 hours | Phase 4 | ⬜ |
| P5-008 | Test Telegram handlers | Command responses | 3 hours | Phase 4 | ⬜ |

### 5.3 Contract Tests

| Task ID | Task | Verify | Effort | Dependencies | Status |
|---------|------|--------|--------|--------------|--------|
| P5-009 | Verify adapters satisfy Ports | Protocol compliance | 2 hours | Phase 3 | ⬜ |
| P5-010 | Verify backward compatibility | Legacy API unchanged | 2 hours | Phase 4 | ⬜ |

### 5.4 Performance Validation

| Task ID | Task | Metric | Effort | Dependencies | Status |
|---------|------|--------|--------|--------------|--------|
| P5-011 | Benchmark DI overhead | < 5ms per injection | 2 hours | Phase 2 | ⬜ |
| P5-012 | Benchmark adapter performance | No regression | 2 hours | Phase 3 | ⬜ |

**Phase 5 Checklist Summary:**
- [ ] 12 tasks total
- [ ] Estimated: 3-5 days
- [ ] Risk: LOW
- [ ] Outcome: Confidence in production readiness

---

## Migration Safety Constraints

### CRITICAL: 24/7 Trading Continuity
The bot runs continuously on Railway. During migration:
- ❌ NEVER deploy partially refactored code to Railway
- ❌ NEVER break backward compatibility of public APIs
- ✅ ALWAYS maintain facade wrappers for existing consumers
- ✅ ALWAYS test complete features in Replit before Railway sync
- ✅ ALWAYS have rollback plan before any Railway deployment

### Non-Regression Requirements

| Component | Requirement | Verification |
|-----------|-------------|--------------|
| **PQC Security** | Kyber-768/Dilithium-3 signing must work | Test sign/verify cycle |
| **AI Integrations** | Gemini, OpenAI, Claude must respond | Test each provider |
| **Risk Guardian** | Must block high-risk trades | Test VETO scenarios |
| **Coherence Engine** | Score thresholds (30%/45%) unchanged | Validate score ranges |
| **CAES System** | Position sizing multipliers preserved | Test 0.5x-3.0x range |
| **Non-Markovian Kernel** | Memory decay τ=12h, ε=0.35, Ω=0.523 | Validate parameters |

---

## Required DI Providers (Before Phase 4)

The following providers MUST be registered in Phase 2-3 before Phase 4 refactoring can begin:

### Missing from Current Plan

| Provider | Container | Used By | Priority |
|----------|-----------|---------|----------|
| `TelegramBotAdapter` | TelegramContainer (NEW) | EnterpriseTelegramBot | P0 |
| `AdaptiveEngine` | TradingContainer | auto_trading_bot.py | P0 |
| `CoherenceEngine` | TradingContainer | auto_trading_bot.py, enterprise_bot.py | P0 |
| `RiskGuardian` | TradingContainer | auto_trading_bot.py | P0 |
| `NonMarkovianKernel` | TradingContainer | auto_trading_bot.py (CAES) | P1 |
| `MonteCarloSimulator` | TradingContainer | auto_trading_bot.py | P1 |
| `HMMRegimeDetector` | TradingContainer | auto_trading_bot.py | P1 |
| `AresV1Strategy` | StrategyContainer (NEW) | auto_trading_bot.py | P1 |
| `AresV2Strategy` | StrategyContainer (NEW) | auto_trading_bot.py | P1 |
| `PaperTradingManager` | TradingContainer | enterprise_bot.py | P0 |

### New Container Required

```python
# bootstrap/containers/telegram.py
class TelegramContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    trading = providers.DependenciesContainer()
    database = providers.DependenciesContainer()
    
    @providers.Singleton
    def telegram_bot():
        from omnix_services.telegram_service.enterprise_bot import EnterpriseTelegramBot
        return EnterpriseTelegramBot()
    
    @providers.Factory
    def command_handlers(bot, trading_system, db_manager):
        # Returns dict of command -> handler mappings
        return {}

# bootstrap/containers/strategies.py
class StrategyContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    
    @providers.Singleton
    def ares_v1():
        from omnix_core.strategies.ares_v1 import AresProtocolV1
        return AresProtocolV1()
    
    @providers.Singleton
    def ares_v2():
        from omnix_core.strategies.ares_v2 import AresProtocolV2
        return AresProtocolV2()
    
    @providers.Singleton
    def non_markovian_kernel():
        from omnix_core.strategies.non_markovian_kernel import NonMarkovianKernel
        return NonMarkovianKernel()
```

---

## Acceptance Criteria Template (Phase 4)

Every Phase 4 refactoring task MUST include:

### Template Structure
```markdown
### Task P4-XXX: [Task Name]

**Input:** [Source file(s) and line ranges]
**Output:** [New file(s) to create]
**Effort:** [Hours estimate]
**Risk:** [LOW/MEDIUM/HIGH]

#### Acceptance Criteria

1. **Extraction Complete**
   - [ ] New module created at specified path
   - [ ] All relevant code moved from source file
   - [ ] Source file imports new module
   - [ ] No duplicate code between files

2. **Dependency Wiring**
   - [ ] DI provider registered in appropriate container
   - [ ] All consumers updated to use injected instance
   - [ ] Circular imports eliminated

3. **Test Coverage**
   - [ ] Unit tests for extracted module (>80%)
   - [ ] Integration test with original caller
   - [ ] No regression in existing tests

4. **Documentation**
   - [ ] Module docstring added
   - [ ] Public methods documented
   - [ ] ARCHITECTURE_REFACTORING_CHECKLIST.md updated

5. **Backward Compatibility**
   - [ ] Original API signature unchanged
   - [ ] Deprecation warning added to old path (if applicable)
   - [ ] Legacy imports still work

#### Verification Commands
```bash
# Run tests for extracted module
pytest tests/domain/services/test_[module].py -v

# Verify no import errors
python -c "from [new_path] import [Class]"

# Check original still works
python -c "from [old_path] import [Class]"
```

#### Rollback
```bash
git checkout HEAD -- [source_file]
rm -rf [new_path]
```
```

---

## Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| DI adds latency | LOW | LOW | Benchmark in Phase 2 |
| Circular imports with Protocols | MEDIUM | MEDIUM | Use `TYPE_CHECKING` guard |
| Breaking changes in API | MEDIUM | HIGH | Maintain facade wrappers |
| Database migration issues | LOW | HIGH | No schema changes in this refactor |
| Telegram bot downtime | MEDIUM | MEDIUM | Test in Replit before Railway |
| Team unfamiliar with patterns | MEDIUM | MEDIUM | Document extensively |
| **EnterpriseTelegramBot rewrite (7.6K LOC)** | HIGH | HIGH | Incremental extraction, feature flags |
| **PQC security regression** | LOW | CRITICAL | Dedicated test suite, sign/verify validation |
| **AI provider failures post-refactor** | MEDIUM | HIGH | Provider fallback chain preserved |
| **24/7 trading interruption** | LOW | CRITICAL | Railway blue-green deployment |
| **Risk Guardian bypass** | LOW | CRITICAL | Integration tests before each deploy |

---

## Rollback Procedures

### Phase 1 Rollback
```bash
rm -rf ports/
git checkout HEAD -- .
```

### Phase 2 Rollback
```bash
rm -rf bootstrap/
pip uninstall dependency-injector
git checkout HEAD -- requirements.txt omnix_dashboard/app.py
```

### Phase 3 Rollback
```bash
rm -rf infrastructure/
git checkout HEAD -- bootstrap/containers/
```

### Phase 4 Rollback
```bash
# Restore from Git
git checkout HEAD~1 -- omnix_core/ omnix_services/
```

---

## Progress Tracking

### Overall Progress

| Phase | Tasks | Completed | Progress | Est. Days |
|-------|-------|-----------|----------|-----------|
| Phase 1: Protocols | 14 | 0 | 0% | 2-3 |
| Phase 2: DI Setup | 20 | 0 | 0% | 5-7 |
| Phase 3: Adapters | 20 | 0 | 0% | 7-10 |
| Phase 4: Refactoring | 30 | 0 | 0% | 20-30 |
| Phase 5: Testing | 12 | 0 | 0% | 5-7 |
| **TOTAL** | **96** | **0** | **0%** | **45-60** |

### Milestone Dates

| Milestone | Target Date | Actual Date | Status |
|-----------|-------------|-------------|--------|
| Phase 1 Complete | TBD | - | ⬜ |
| Phase 2 Complete | TBD | - | ⬜ |
| Phase 3 Complete | TBD | - | ⬜ |
| Phase 4 Complete | TBD | - | ⬜ |
| Phase 5 Complete | TBD | - | ⬜ |
| V7.0 Release | TBD | - | ⬜ |

---

## Appendix A: File Mapping (Old → New)

| Current Location | New Location | Notes |
|------------------|--------------|-------|
| `omnix_core/trading_system.py` | `domain/services/` + `application/use_cases/` | Split into 6 files |
| `omnix_services/telegram_service/enterprise_bot.py` | `application/handlers/` + `infrastructure/adapters/messaging/` | Split into 10 files |
| `omnix_core/bot/auto_trading_bot.py` | `application/orchestrators/` + `domain/services/` | Split into 5 files |
| `omnix_services/database_service/database_service.py` | `infrastructure/persistence/` | Split into 8 files |

---

## Appendix B: Dependency Graph

```
                    ┌─────────────────┐
                    │   entrypoints   │
                    │ (Flask, Telegram)│
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    bootstrap    │
                    │ (DI Containers) │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
┌─────────▼─────────┐ ┌──────▼──────┐ ┌────────▼────────┐
│   application     │ │    ports    │ │ infrastructure  │
│   (use cases)     │ │ (protocols) │ │   (adapters)    │
└─────────┬─────────┘ └──────┬──────┘ └────────┬────────┘
          │                  │                  │
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                    ┌────────▼────────┐
                    │     domain      │
                    │ (entities, pure │
                    │   business)     │
                    └─────────────────┘
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Dec 5, 2025 | Agent | Initial checklist with 92 tasks across 5 phases |
| 1.1 | Dec 5, 2025 | Agent | Added Migration Safety Constraints, Required DI Providers section, Acceptance Criteria Template, updated Risk Matrix with HIGH/CRITICAL items, corrected effort estimates (45-60 days), fixed sync/async patterns in code examples |
| 1.2 | Dec 5, 2025 | Agent | Clarified sync vs async adapter distinction (TradingPort/DatabasePort = sync, AI/Notification/MarketData = async), fixed KrakenAdapter to sync, aligned all code samples with Protocol signatures |

---

**Document End**
