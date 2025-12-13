# OMNIX V7.0 Migration Plan

**Version:** 2.0 (Consolidated)  
**Date:** December 12, 2025  
**Pattern:** Strangler Fig  
**Status:** Phase 0 Complete | Phase 1 Ready

> **Note:** This document consolidates the previous `MIGRATION_ROADMAP.md` and `MODERNIZATION_ROADMAP.md` into a single source of truth for V7.0 migration planning.

---

## Executive Summary

Este documento define el plan de migración incremental de OMNIX V6.5.4c hacia una arquitectura Clean/Hexagonal moderna, manteniendo la estabilidad de producción en Railway.

**Duración Total:** 6-8 semanas (después de 500 trades)  
**Riesgo de Producción:** BAJO (migración incremental)  
**Compatibilidad:** 100% backward compatible durante migración

---

## Trade-Gated Timeline

| Milestone | Trigger | Actions |
|-----------|---------|---------|
| **Phase 0** | Immediate | ✅ Foundation complete (Dec 11, 2025) |
| **Phase 1** | Immediate | Bootstrap & Config (low risk) |
| 200 trades | Track record | AI Service DI Phase 2 |
| 400 trades | Track record | AI Service Refactor Phase 3 |
| **500 trades** | Track record | **Phases 2-4: Full architecture migration** |
| 55% win rate + 14 days | Stability | Semantic Router production |

**Priority:** Track record generation > Code refactoring. Phases 2-4 blocked until 500-trade milestone.

---

## Componentes a Preservar (NO modificar)

Estos componentes YA están bien estructurados y sirven como **modelo**:

| Componente | Ubicación | Razón |
|------------|-----------|-------|
| AI Service | `omnix_services/ai_service/` | DI container, protocols, providers |
| Hexagonal Ports | `omnix/ports/` | 8 protocols definidos (Fase 1 completa) |
| Trading Profiles | `omnix_core/config/trading_profiles.py` | Single source of truth |
| Database Gateway | `omnix_services/database_service/` | Connection pool funcional |

**Regla:** Replicar patrones del AI Service, no reinventarlos

---

## Table of Contents

1. [Estrategia: Strangler Fig Pattern](#1-estrategia-strangler-fig-pattern)
2. [Fases de Migración](#2-fases-de-migración)
3. [Fase 0: Foundation](#3-fase-0-foundation)
4. [Fase 1: Bootstrap & Config](#4-fase-1-bootstrap--config)
5. [Fase 2: Domain & Application](#5-fase-2-domain--application)
6. [Fase 3: Interfaces](#6-fase-3-interfaces)
7. [Fase 4: Cleanup](#7-fase-4-cleanup)
8. [Riesgos y Mitigación](#8-riesgos-y-mitigación)
9. [Checklist de Verificación](#9-checklist-de-verificación)

---

## 1. Estrategia: Strangler Fig Pattern

### 1.1 Por Qué Strangler Fig

El patrón Strangler Fig permite migrar código legacy **incrementalmente**:

```
┌─────────────────────────────────────────────────────────────┐
│  FASE 0      FASE 1       FASE 2       FASE 3      FASE 4  │
│                                                             │
│  ████████    ██████░░     ████░░░░     ██░░░░░░    ░░░░░░░░ │  ← Legacy
│  ░░░░░░░░    ░░░░░░██     ░░░░████     ░░██████    ████████ │  ← New
│                                                             │
│  100% old    80% old      50% old      20% old     0% old   │
└─────────────────────────────────────────────────────────────┘
```

**Ventajas:**
- Zero downtime durante migración
- Rollback fácil si hay problemas
- Railway auto-deploy funciona normalmente
- Cada fase es deployable a producción

### 1.2 Reglas de Migración

1. **No Big Bang** - Nunca reescribir todo de una vez
2. **Feature Parity** - Nueva estructura debe tener misma funcionalidad antes de eliminar legacy
3. **Tests First** - Agregar tests antes de mover código
4. **Import Aliases** - Usar re-exports para compatibilidad

```python
# Ejemplo: Re-export para compatibilidad
# omnix_core/config/__init__.py (legacy)
from src.omnix.config.profiles import TradingProfiles  # Forward to new

# Código existente sigue funcionando:
from omnix_core.config import TradingProfiles  # No changes needed
```

---

## 2. Fases de Migración

| Fase | Nombre | Duración | Trigger | Estado |
|------|--------|----------|---------|--------|
| 0 | Foundation | 1 semana | **AHORA** (no afecta trading) | ✅ **COMPLETADA** (Dec 11, 2025) |
| 1 | Bootstrap & Config | 1 semana | **AHORA** (bajo riesgo) | ✅ **COMPLETADA** (Dec 12, 2025) |
| 2 | Domain & Application | 2 semanas | **AHORA** (bajo riesgo) | ✅ **COMPLETADA** (Dec 12, 2025) |
| 3 | Infrastructure Adapters | 1 semana | **AHORA** (bajo riesgo) | ✅ **COMPLETADA** (Dec 12, 2025) |
| 3b | Flask Factory & Telegram Migration | 1 semana | **AHORA** (bajo riesgo) | ✅ **COMPLETADA** (Dec 13, 2025) |
| 4 | Cleanup & Organization | 1 semana | **AHORA** (bajo riesgo) | ✅ **COMPLETADA** (Dec 13, 2025) |

### 2.2 Phase 4 Progress (Dec 13, 2025)

| Deliverable | Status | Notes |
|-------------|--------|-------|
| 4.1-4.3: Thin wrappers (main.py, wsgi.py) | ✅ | Delegate to src/omnix/bootstrap/ |
| 4.4: scripts/ directory | ✅ | Utility scripts moved |
| 4.5: tests/integration/ | ✅ | test_railway_startup.py moved |
| 4.6-4.8: Import Audit | ✅ | See docs/current/IMPORT_AUDIT.md |
| 4.9: import-linter | ✅ | 3 contracts passing |
| 4.10: Dead code removal | ✅ | **REMOVED** (Dec 13): alerts/, regime_switcher.py, on_chain_service/ |
| 4.11: Documentation updates | ✅ | IMPORT_AUDIT.md, ARCHITECTURE.md updated |

**Phase 4 COMPLETE** (Dec 13, 2025): 10-pillar stability audit passed, dead code removed.

**Nota:** Fases 0-1 son de **bajo riesgo** y pueden ejecutarse durante track record generation. Fases 2-4 requieren milestone de 500 trades para minimizar riesgo de regresión

### 2.1 Fase 0 - Entregables Completados (Dec 11, 2025)

| Entregable | Ubicación | Estado |
|------------|-----------|--------|
| Dependency Graph | `docs/architecture/phase0/DEPENDENCY_GRAPH.md` | ✅ |
| ADR-001 | `docs/adr/ADR-001-hexagonal-migration-strategy.md` | ✅ |
| Module Catalog | `docs/architecture/MODULE_CATALOG.md` | ✅ |
| pyproject.toml | `/pyproject.toml` | ✅ |
| src/omnix/ structure | `/src/omnix/` | ✅ |
| Smoke tests | `tests/test_smoke.py` | ✅ (13/13 pass) |
| pytest config | `tests/conftest.py` | ✅ |

---

## 3. Fase 0: Foundation

**Objetivo:** Preparar herramientas y estructura base sin cambiar código existente.

### 3.1 Tareas

| ID | Tarea | Horas | Prioridad |
|----|-------|-------|-----------|
| 0.1 | Crear `pyproject.toml` con UV workspace | 2 | P0 |
| 0.2 | Configurar `ruff` para linting | 1 | P0 |
| 0.3 | Configurar `mypy` para type checking | 2 | P0 |
| 0.4 | Crear estructura `src/omnix/` vacía | 1 | P0 |
| 0.5 | Generar dependency graph actual | 2 | P1 |
| 0.6 | Documentar imports circulares | 2 | P1 |
| 0.7 | Baseline de tests (pytest setup) | 2 | P1 |

### 3.2 Archivos a Crear

```
pyproject.toml                 # UV/Poetry config
src/
└── omnix/
    ├── __init__.py           # Package marker
    ├── domain/
    │   └── __init__.py
    ├── application/
    │   └── __init__.py
    ├── infrastructure/
    │   └── __init__.py
    ├── interfaces/
    │   └── __init__.py
    ├── config/
    │   └── __init__.py
    └── bootstrap/
        └── __init__.py
```

### 3.3 pyproject.toml Template

```toml
[project]
name = "omnix"
version = "6.5.4c"
description = "OMNIX Institutional+ Trading System"
requires-python = ">=3.11"
dependencies = [
    # Migrar desde requirements.txt
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/omnix"]

[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "I", "N", "W"]

[tool.mypy]
python_version = "3.11"
strict = false  # Incremental adoption
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
```

### 3.4 Verificación Fase 0

- [ ] `uv sync` o `poetry install` funciona
- [ ] `ruff check .` pasa (con warnings aceptados)
- [ ] `mypy src/` pasa (con warnings aceptados)
- [ ] `pytest` descubre tests
- [ ] Railway deploy sigue funcionando
- [ ] Dependency graph generado

---

## 4. Fase 1: Bootstrap & Config

**Objetivo:** Centralizar configuración y limpiar main.py.

### 4.1 Tareas

| ID | Tarea | Horas | Prioridad |
|----|-------|-------|-----------|
| 1.1 | Crear `src/omnix/config/settings.py` con Pydantic | 4 | P0 |
| 1.2 | Migrar `os.getenv()` dispersos a settings | 4 | P0 |
| 1.3 | Crear `src/omnix/bootstrap/container.py` | 4 | P0 |
| 1.4 | Refactorizar `main.py` a usar container | 4 | P0 |
| 1.5 | Mover `trading_profiles.py` a nuevo config | 2 | P1 |
| 1.6 | Crear re-exports para compatibilidad legacy | 2 | P1 |
| 1.7 | Tests para settings y container | 4 | P1 |

### 4.2 Settings Centralizado

```python
# src/omnix/config/settings.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    database_url: str
    redis_url: str
    
    # API Keys
    kraken_api_key: str = ""
    kraken_api_secret: str = ""
    telegram_bot_token: str
    gemini_api_key: str = ""
    
    # Trading
    trading_profile: str = "PRODUCTION_STABLE"
    max_trade_usd: float = 20000.0
    drawdown_limit: float = 0.15
    
    # Features
    enable_ares_v1: bool = True
    enable_ares_v2: bool = True
    enable_paper_trading: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### 4.3 DI Container

```python
# src/omnix/bootstrap/container.py
from dataclasses import dataclass
from typing import Protocol

class IDatabaseGateway(Protocol):
    async def execute(self, query: str) -> list: ...

class IRedisCache(Protocol):
    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str, ttl: int = 3600) -> None: ...

@dataclass
class Container:
    settings: Settings
    database: IDatabaseGateway
    cache: IRedisCache
    # Add more as needed
    
    @classmethod
    def create(cls) -> "Container":
        from src.omnix.config.settings import get_settings
        from src.omnix.infrastructure.persistence.postgres import PostgresGateway
        from src.omnix.infrastructure.persistence.redis import RedisCache
        
        settings = get_settings()
        return cls(
            settings=settings,
            database=PostgresGateway(settings.database_url),
            cache=RedisCache(settings.redis_url),
        )
```

### 4.4 main.py Limpio

```python
# src/omnix/bootstrap/main.py
import asyncio
import logging
from src.omnix.bootstrap.container import Container

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting OMNIX V6.5.4c INSTITUTIONAL+")
    
    # Create DI container
    container = Container.create()
    
    # Initialize components via container
    # (Components receive dependencies, not fetch them)
    
    # Start services
    await start_services(container)

if __name__ == "__main__":
    asyncio.run(main())
```

### 4.5 Entregables Fase 1 - Completados (Dec 12, 2025)

| Entregable | Ubicación | Estado |
|------------|-----------|--------|
| Settings centralizado | `src/omnix/config/settings.py` | ✅ |
| DI Container | `src/omnix/bootstrap/container.py` | ✅ |
| Bootstrap Runtime | `src/omnix/bootstrap/runtime.py` | ✅ |
| Re-exports config | `src/omnix/config/__init__.py` | ✅ |
| Re-exports bootstrap | `src/omnix/bootstrap/__init__.py` | ✅ |
| Phase 1 Tests | `tests/test_phase1_bootstrap.py` | ✅ (16/16 pass) |

### 4.6 Verificación Fase 1

- [x] `from src.omnix.config import get_settings` funciona
- [x] Todas las env vars centralizadas en Settings
- [x] `Container.create()` instancia correctamente
- [ ] `main.py` legacy usa container (deferred - no breaking changes)
- [x] Re-exports mantienen compatibilidad
- [x] Railway deploy funciona (no changes to production code)
- [x] Tests de settings pasan (16/16)

---

## 5. Fase 2: Domain & Application

**Objetivo:** Separar lógica de negocio en capas domain/application.

### 5.1 Tareas

| ID | Tarea | Horas | Prioridad |
|----|-------|-------|-----------|
| 2.1 | Crear entities de trading (Trade, Signal, Position) | 4 | P0 |
| 2.2 | Crear value objects (Price, Quantity, Pair) | 2 | P0 |
| 2.3 | Mover strategies a `domain/strategies/` | 4 | P0 |
| 2.4 | Crear `ExecuteTradeUseCase` | 4 | P0 |
| 2.5 | Crear `ScanMarketUseCase` | 4 | P0 |
| 2.6 | Definir ports (IMarketData, IOrderExecutor) | 4 | P0 |
| 2.7 | Consolidar risk en `domain/risk/` | 4 | P1 |
| 2.8 | Eliminar duplicación omnix_risk ↔ omnix_services | 4 | P1 |
| 2.9 | Tests para domain services | 6 | P1 |
| 2.10 | Tests para use cases | 6 | P1 |

### 5.2 Domain Entities

```python
# src/omnix/domain/trading/entities.py
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

class TradeDirection(Enum):
    BUY = "buy"
    SELL = "sell"

class TradeStatus(Enum):
    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    FAILED = "failed"

@dataclass
class Trade:
    id: str
    pair: str
    direction: TradeDirection
    quantity: float
    entry_price: float
    status: TradeStatus
    strategy: str
    confidence: float
    created_at: datetime
    executed_at: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    
    def calculate_pnl(self, current_price: float) -> float:
        if self.direction == TradeDirection.BUY:
            return (current_price - self.entry_price) * self.quantity
        return (self.entry_price - current_price) * self.quantity
    
    def is_profitable(self, current_price: float) -> bool:
        return self.calculate_pnl(current_price) > 0
```

### 5.3 Application Ports

```python
# src/omnix/application/trading/ports.py
from typing import Protocol
from src.omnix.domain.trading.entities import Trade, TradeDirection

class IMarketData(Protocol):
    """Port for fetching market data"""
    async def get_current_price(self, pair: str) -> float: ...
    async def get_ohlcv(self, pair: str, timeframe: str, limit: int) -> list: ...
    async def get_orderbook(self, pair: str) -> dict: ...

class IOrderExecutor(Protocol):
    """Port for executing orders"""
    async def execute_order(
        self,
        pair: str,
        direction: TradeDirection,
        quantity: float,
        price: Optional[float] = None,
    ) -> Trade: ...
    
    async def cancel_order(self, order_id: str) -> bool: ...

class ITradeStorage(Protocol):
    """Port for persisting trades"""
    async def save_trade(self, trade: Trade) -> None: ...
    async def get_trade(self, trade_id: str) -> Trade | None: ...
    async def get_recent_trades(self, limit: int = 100) -> list[Trade]: ...
```

### 5.4 Use Case Example

```python
# src/omnix/application/trading/execute_trade.py
from dataclasses import dataclass
from src.omnix.application.trading.ports import IMarketData, IOrderExecutor, ITradeStorage
from src.omnix.domain.trading.entities import Trade, TradeDirection

@dataclass
class ExecuteTradeRequest:
    pair: str
    direction: TradeDirection
    quantity: float
    strategy: str
    confidence: float

@dataclass  
class ExecuteTradeUseCase:
    market_data: IMarketData
    order_executor: IOrderExecutor
    trade_storage: ITradeStorage
    
    async def execute(self, request: ExecuteTradeRequest) -> Trade:
        # 1. Get current price
        price = await self.market_data.get_current_price(request.pair)
        
        # 2. Execute order
        trade = await self.order_executor.execute_order(
            pair=request.pair,
            direction=request.direction,
            quantity=request.quantity,
            price=price,
        )
        
        # 3. Update trade metadata
        trade.strategy = request.strategy
        trade.confidence = request.confidence
        
        # 4. Persist
        await self.trade_storage.save_trade(trade)
        
        return trade
```

### 5.5 Verificación Fase 2

- [ ] Domain entities no importan infrastructure
- [ ] Use cases solo dependen de ports (Protocols)
- [ ] Strategies movidas a domain
- [ ] Risk consolidado sin duplicación
- [ ] Tests domain pasan (sin mocks de DB)
- [ ] Tests use cases pasan (con mocks de ports)
- [ ] Railway deploy funciona

---

## 6. Fase 3: Interfaces

**Objetivo:** Refactorizar Flask/Telegram para consumir use cases via ports.

### 6.1 Tareas

| ID | Tarea | Horas | Prioridad |
|----|-------|-------|-----------|
| 3.1 | Crear Flask app factory en `interfaces/flask_app/` | 4 | P0 |
| 3.2 | Refactorizar blueprints a consumir use cases | 6 | P0 |
| 3.3 | Inyectar container en Flask app context | 2 | P0 |
| 3.4 | Mover Telegram bot a `interfaces/telegram/` | 4 | P1 |
| 3.5 | Telegram handlers consumen use cases | 4 | P1 |
| 3.6 | Crear adapters en infrastructure (Kraken, Gemini) | 6 | P0 |
| 3.7 | Conectar adapters a ports | 4 | P0 |
| 3.8 | Tests integration para Flask | 4 | P1 |

### 6.2 Flask App Factory

```python
# src/omnix/interfaces/flask_app/__init__.py
from flask import Flask
from src.omnix.bootstrap.container import Container

def create_app(container: Container | None = None) -> Flask:
    app = Flask(__name__)
    
    # Use provided container or create new
    if container is None:
        container = Container.create()
    
    # Store in app context
    app.container = container
    
    # Register blueprints
    from src.omnix.interfaces.flask_app.blueprints import (
        core_bp, market_bp, system_bp, api_bp
    )
    app.register_blueprint(core_bp)
    app.register_blueprint(market_bp, url_prefix="/market")
    app.register_blueprint(system_bp, url_prefix="/system")
    app.register_blueprint(api_bp, url_prefix="/api/v1")
    
    return app
```

### 6.3 Blueprint Consumiendo Use Cases

```python
# src/omnix/interfaces/flask_app/blueprints/market.py
from flask import Blueprint, jsonify, current_app

market_bp = Blueprint("market", __name__)

@market_bp.route("/price/<pair>")
async def get_price(pair: str):
    container = current_app.container
    
    # Use case via port
    price = await container.market_data.get_current_price(pair)
    
    return jsonify({"pair": pair, "price": price})

@market_bp.route("/analysis/<pair>")
async def get_analysis(pair: str):
    container = current_app.container
    
    # Use case
    from src.omnix.application.ai.analyze_market import AnalyzeMarketUseCase
    
    use_case = AnalyzeMarketUseCase(
        market_data=container.market_data,
        ai_provider=container.ai_provider,
    )
    
    analysis = await use_case.execute(pair)
    return jsonify(analysis)
```

### 6.4 Adapter Implementation

```python
# src/omnix/infrastructure/external/kraken/client.py
from src.omnix.application.trading.ports import IMarketData, IOrderExecutor
from src.omnix.domain.trading.entities import Trade, TradeDirection

class KrakenAdapter(IMarketData, IOrderExecutor):
    """Implements both market data and order execution ports"""
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        # Initialize Kraken client
    
    async def get_current_price(self, pair: str) -> float:
        # Implementation using Kraken API
        ...
    
    async def get_ohlcv(self, pair: str, timeframe: str, limit: int) -> list:
        # Implementation
        ...
    
    async def execute_order(
        self,
        pair: str,
        direction: TradeDirection,
        quantity: float,
        price: float | None = None,
    ) -> Trade:
        # Implementation
        ...
```

### 6.5 Verificación Fase 3

- [ ] Flask app factory funciona
- [ ] Blueprints no importan infrastructure directamente
- [ ] Container inyectado en app context
- [ ] Adapters implementan ports correctamente
- [ ] Telegram bot usa use cases
- [ ] Railway deploy funciona
- [ ] Integration tests pasan

---

## 7. Fase 4: Cleanup

**Objetivo:** Eliminar código legacy y finalizar migración.

### 7.1 Tareas

| ID | Tarea | Horas | Prioridad |
|----|-------|-------|-----------|
| 4.1 | Mover `main.py` y `wsgi.py` a `src/omnix/bootstrap/` | 2 | P0 |
| 4.2 | Crear directorio `scripts/` y mover utilidades de la raíz | 2 | P0 |
| 4.3 | Mover `test_railway_startup.py` a `tests/integration/` | 1 | P1 |
| 4.4 | Actualizar Procfile y railway.json con nuevas rutas | 1 | P0 |
| 4.5 | Evaluar y eliminar `start_dashboard.py` si es redundante | 1 | P1 |
| 4.6 | Eliminar re-exports de compatibilidad | 2 | P0 |
| 4.7 | Eliminar paquetes legacy vacíos | 2 | P0 |
| 4.8 | Actualizar imports en todo el codebase | 4 | P0 |
| 4.9 | Configurar import linter (no cross-layer imports) | 2 | P1 |
| 4.10 | Eliminar código muerto | 4 | P1 |
| 4.11 | Actualizar documentación | 4 | P1 |
| 4.12 | Final test coverage report | 2 | P1 |
| 4.13 | Performance benchmarks | 2 | P2 |

### 7.1.1 Archivos Raíz a Reorganizar

| Archivo | Destino | Notas |
|---------|---------|-------|
| `main.py` | `src/omnix/bootstrap/main.py` | Entrypoint principal |
| `wsgi.py` | `src/omnix/bootstrap/wsgi.py` | Producción WSGI |
| `start_dashboard.py` | `scripts/` o DELETE | Evaluar redundancia |
| `chat_with_bot.py` | `scripts/` | Utilidad testing |
| `generate_investor_report.py` | `scripts/` | Reportes inversores |
| `send_telegram_message.py` | `scripts/` | Utilidad Telegram |
| `get_my_telegram_id.py` | `scripts/` | Helper Telegram |
| `test_railway_startup.py` | `tests/integration/` | Test deployment |
| `verify_code.py` | `scripts/` | Verificación código |

### 7.2 Paquetes a Eliminar

| Paquete Legacy | Razón |
|----------------|-------|
| `omnix_core/` | Migrado a `src/omnix/domain/` y `src/omnix/application/` |
| `omnix_services/` | Migrado a `src/omnix/infrastructure/` e `interfaces/` |
| `omnix_risk/` | Consolidado en `src/omnix/domain/risk/` |
| `omnix_strategies/` | Consolidado en `src/omnix/domain/strategies/` |
| `omnix_api/` | Migrado a `src/omnix/interfaces/flask_app/blueprints/api.py` |
| `omnix_config/` | Migrado a `src/omnix/config/` |
| `omnix_dashboard/` | Migrado a `src/omnix/interfaces/flask_app/` |
| `omnix_reports/` | Migrado a `src/omnix/application/reports/` |

### 7.3 Import Linter Rules

```toml
# pyproject.toml
[tool.import-linter]
root_package = "omnix"

[[tool.import-linter.contracts]]
name = "Domain independence"
type = "forbidden"
source_modules = ["omnix.domain"]
forbidden_modules = ["omnix.infrastructure", "omnix.interfaces"]

[[tool.import-linter.contracts]]
name = "Application layer"
type = "layers"
layers = ["omnix.interfaces", "omnix.application", "omnix.domain"]
```

### 7.4 Verificación Fase 4

- [ ] No quedan paquetes legacy
- [ ] Import linter pasa sin errores
- [ ] Código muerto eliminado
- [ ] Documentación actualizada
- [ ] Test coverage > 60%
- [ ] Performance igual o mejor
- [ ] Railway deploy funciona

---

## 8. Riesgos y Mitigación

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Railway deploy falla | BAJA | ALTO | Test local antes de push, rollback rápido |
| Imports circulares nuevos | MEDIA | MEDIO | Import linter en CI |
| Regresión funcional | MEDIA | ALTO | Tests antes de mover código |
| Telegram bot offline | BAJA | ALTO | Mantener legacy hasta migración completa |
| Performance degradation | BAJA | MEDIO | Benchmarks en cada fase |

---

## 9. Checklist de Verificación

### Pre-Migración
- [ ] Backup de base de datos
- [ ] Documentar estado actual de producción
- [ ] Crear branch `architecture-migration`
- [ ] Comunicar plan al equipo

### Por Fase
- [ ] Tests pasan localmente
- [ ] Lint/type checks pasan
- [ ] Deploy a staging (si existe)
- [ ] Deploy a producción vía Railway
- [ ] Verificar funcionalidad crítica
- [ ] Monitorear logs 24h

### Post-Migración
- [ ] Test coverage > 60%
- [ ] Documentación actualizada
- [ ] Performance benchmarks documentados
- [ ] Retrospectiva del proceso

---

## Timeline Visual

```
Semana 1       Semana 2       Semana 3       Semana 4       Semana 5       Semana 6
│              │              │              │              │              │
├── FASE 0 ───┤              │              │              │              │
│  Foundation │              │              │              │              │
│              ├── FASE 1 ───┤              │              │              │
│              │  Bootstrap  │              │              │              │
│              │              ├─────── FASE 2 ──────┤              │              │
│              │              │    Domain/App       │              │              │
│              │              │              │              ├── FASE 3 ───┤
│              │              │              │              │  Interfaces │
│              │              │              │              │              ├── FASE 4 ──▶
│              │              │              │              │              │  Cleanup
▼              ▼              ▼              ▼              ▼              ▼
```

---

## Siguiente Paso

1. Revisar `docs/architecture/ARCHITECTURE_AUDIT_2025.md` para contexto
2. Comenzar Fase 0 con `pyproject.toml` y estructura base
3. Ejecutar tareas en orden de prioridad

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Dec 10, 2025 | Architecture Board | Initial roadmap |
