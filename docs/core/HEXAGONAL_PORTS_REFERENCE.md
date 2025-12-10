# OMNIX Hexagonal Architecture - Ports Reference

> **Version Control**: Current system version is defined in `omnix_config/settings.py`.

**Document Version:** 1.0  
**Created:** December 10, 2025  
**Phase 1 Completed:** December 9, 2025  
**Status:** ACTIVE - Foundation for V7.0

---

## Overview

The hexagonal architecture (Ports & Adapters) separates business logic from infrastructure concerns. This document describes the Protocol interfaces defined in Phase 1.

**Location:** `omnix/ports/`

---

## Directory Structure

```
omnix/
├── __init__.py
└── ports/
    ├── __init__.py              # Main exports
    ├── verify_ports.py          # Verification utility
    ├── driven/                  # Output ports (infrastructure)
    │   ├── __init__.py
    │   ├── ai_inference_port.py
    │   ├── cache_port.py
    │   ├── database_port.py
    │   ├── market_data_port.py
    │   ├── notification_port.py
    │   └── trading_port.py
    └── driver/                  # Input ports (application)
        ├── __init__.py
        ├── rest_api_port.py
        └── telegram_port.py
```

---

## Driven Ports (Output - Infrastructure)

These ports define contracts for external infrastructure services.

### 1. TradingPort

**File:** `driven/trading_port.py`  
**Purpose:** Contract for exchange adapters (Kraken, Alpaca, Paper)

```python
class TradingPort(Protocol):
    def execute_order(symbol, side, amount, order_type) -> Dict
    def get_ticker(symbol) -> Dict
    def get_balance() -> Dict[str, Decimal]
    def get_open_positions() -> List[Dict]
    def cancel_order(order_id) -> bool
    def is_connected() -> bool
```

**Implementations:** KrakenClient, AlpacaService, PaperTradingManager

### 2. DatabasePort

**File:** `driven/database_port.py`  
**Purpose:** Contract for database operations

```python
class DatabasePort(Protocol):
    async def execute_query(query, params) -> List[Dict]
    async def execute_command(query, params) -> int
    async def get_connection() -> Any
    def is_healthy() -> bool
```

**Implementations:** DatabaseService, PaperTradingRepository

### 3. CachePort

**File:** `driven/cache_port.py`  
**Purpose:** Contract for caching layer

```python
class CachePort(Protocol):
    def get(key) -> Optional[Any]
    def set(key, value, ttl) -> bool
    def delete(key) -> bool
    def exists(key) -> bool
    def clear_pattern(pattern) -> int
```

**Implementations:** RedisCache

### 4. AIInferencePort

**File:** `driven/ai_inference_port.py`  
**Purpose:** Contract for AI/LLM providers

```python
class AIInferencePort(Protocol):
    async def generate_response(prompt, context) -> str
    async def analyze_sentiment(text) -> Dict
    def get_model_info() -> Dict
    def is_available() -> bool
```

**Implementations:** GeminiProvider, OpenAIProvider, AnthropicProvider

### 5. MarketDataPort

**File:** `driven/market_data_port.py`  
**Purpose:** Contract for market data feeds

```python
class MarketDataPort(Protocol):
    def get_ohlcv(symbol, timeframe, limit) -> List[Dict]
    def get_orderbook(symbol, limit) -> Dict
    def get_recent_trades(symbol, limit) -> List[Dict]
    def subscribe_ticker(symbol, callback) -> str
    def unsubscribe(subscription_id) -> bool
```

**Implementations:** KrakenData, AlphaVantageService

### 6. NotificationPort

**File:** `driven/notification_port.py`  
**Purpose:** Contract for notification services

```python
class NotificationPort(Protocol):
    async def send_message(recipient, message, priority) -> bool
    async def send_alert(alert_type, data) -> bool
    def get_delivery_status(message_id) -> str
```

**Implementations:** TelegramUtils, SmartAlerts

---

## Driver Ports (Input - Application)

These ports define contracts for incoming requests.

### 7. TelegramPort

**File:** `driver/telegram_port.py`  
**Purpose:** Contract for Telegram bot interface

```python
class TelegramPort(Protocol):
    async def handle_message(update, context) -> None
    async def handle_callback(update, context) -> None
    def register_handlers(application) -> None
    def get_user_session(user_id) -> Dict
```

**Implementations:** EnterpriseBot

### 8. RESTAPIPort

**File:** `driver/rest_api_port.py`  
**Purpose:** Contract for REST API endpoints

```python
class RESTAPIPort(Protocol):
    def register_routes(app) -> None
    def get_metrics() -> Dict
    def health_check() -> Dict
```

**Implementations:** Flask blueprints in omnix_dashboard/

---

## Verification

Use the verification utility to check port definitions:

```bash
python -c "from omnix.ports.verify_ports import verify_all; verify_all()"
```

---

## Migration Path

### Current State (V6.5.4c)
- Ports defined as Protocol interfaces
- Existing code unchanged
- Ports coexist with current architecture

### Future State (V7.0)
- Adapters implement Port protocols
- Dependency injection via containers
- Full hexagonal separation

---

## Related Documentation

- [ARCHITECTURE_REFACTORING_CHECKLIST.md](ARCHITECTURE_REFACTORING_CHECKLIST.md) - Full migration plan
- [OMNIX_MODULE_CATALOG.md](OMNIX_MODULE_CATALOG.md) - Module inventory
- [TRADING_PROFILES_V6.5.4c.md](TRADING_PROFILES_V6.5.4c.md) - Current configuration

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| Dec 10, 2025 | 1.0 | Initial documentation |
| Dec 9, 2025 | - | Phase 1 implementation completed |
