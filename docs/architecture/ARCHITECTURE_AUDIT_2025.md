# OMNIX V6.5.4c Architecture Audit

**Version:** 1.0  
**Date:** December 10, 2025  
**Auditor:** Architecture Review Board  
**Status:** DIAGNOSTIC COMPLETE

---

## Executive Summary

Este documento presenta una auditoría completa del codebase OMNIX V6.5.4c, identificando problemas de arquitectura y proponiendo una estructura objetivo alineada con las mejores prácticas Python 2025.

**Hallazgo Principal:** El sistema tiene funcionalidad enterprise robusta pero sufre de acoplamiento excesivo, responsabilidades mezcladas, y ausencia de boundaries de dominio claros. La reestructuración permitirá escalar a B2C SaaS.

---

## Table of Contents

1. [Principios de Referencia 2025](#1-principios-de-referencia-2025)
2. [Diagnóstico del Estado Actual](#2-diagnóstico-del-estado-actual)
3. [Problemas Identificados](#3-problemas-identificados)
4. [Estructura Objetivo](#4-estructura-objetivo)
5. [Mapeo Legacy → Target](#5-mapeo-legacy--target)
6. [Prioridades de Refactoring](#6-prioridades-de-refactoring)

---

## 1. Principios de Referencia 2025

### 1.1 Clean Architecture

```
┌─────────────────────────────────────────┐
│     Frameworks & Drivers (Outermost)    │  Flask, PostgreSQL, Redis, Kraken API
├─────────────────────────────────────────┤
│          Interface Adapters             │  Blueprints, Telegram handlers, CLI
├─────────────────────────────────────────┤
│        Application / Use Cases          │  Trading orchestration, Risk evaluation
├─────────────────────────────────────────┤
│            Domain (Core)                │  Entities, Value Objects, Domain Services
└─────────────────────────────────────────┘

Regla de Dependencia: Las dependencias apuntan hacia adentro (domain).
```

### 1.2 SOLID Principles

| Principio | Descripción | Estado OMNIX |
|-----------|-------------|--------------|
| **S**ingle Responsibility | Una clase, una razón para cambiar | ❌ Violado |
| **O**pen/Closed | Abierto a extensión, cerrado a modificación | ⚠️ Parcial |
| **L**iskov Substitution | Subtipos sustituibles | ⚠️ Parcial |
| **I**nterface Segregation | Interfaces pequeñas y específicas | ⚠️ Parcial |
| **D**ependency Inversion | Depender de abstracciones | ❌ Violado |

### 1.3 Hexagonal Architecture (Ports & Adapters)

```
                    ┌─────────────────────┐
    Driving         │                     │         Driven
    Adapters        │      DOMAIN         │         Adapters
                    │                     │
  ┌──────────┐      │   ┌───────────┐     │      ┌──────────┐
  │ Flask    │──────│──▶│  Ports    │◀────│──────│ Postgres │
  │ Telegram │      │   │ (Protocol)│     │      │ Redis    │
  │ CLI      │      │   └───────────┘     │      │ Kraken   │
  └──────────┘      │                     │      └──────────┘
                    └─────────────────────┘

Inbound Ports: Interfaces que reciben comandos (ITradeExecutor)
Outbound Ports: Interfaces para sistemas externos (IMarketData)
```

### 1.4 Python 2025 Best Practices

| Práctica | Recomendación |
|----------|---------------|
| Project Structure | `src/` layout con pyproject.toml |
| Type Hints | `typing.Protocol` sobre `abc.ABC` |
| DI | Constructor injection o `dependency-injector` |
| Config | Pydantic Settings centralizado |
| Testing | pytest + mocks para ports |
| Package Manager | UV o Poetry con workspaces |

---

## 2. Diagnóstico del Estado Actual

### 2.1 Estructura de Directorios

```
OMNIX V6.5.4c/
├── omnix/                    # Hexagonal ports (incompleto)
│   └── ports/
│       ├── driven/           # 6 output ports definidos
│       └── driver/           # 2 input ports definidos
├── omnix_api/                # Stripe integration (abandonado)
├── omnix_config/             # Settings dispersos
├── omnix_core/               # Mezcla domain + infrastructure
│   ├── bot/                  # AutoTradingBot (monolítico)
│   ├── cache/                # Redis implementation
│   ├── config/               # Trading profiles
│   ├── strategies/           # ARES, Non-Markovian (domain)
│   └── ...
├── omnix_dashboard/          # Flask app + blueprints
├── omnix_risk/               # Risk services (duplicado)
├── omnix_services/           # 20+ servicios mezclados
│   ├── ai_service/           # Bien estructurado (SOLID)
│   ├── database_service/     # DatabaseGateway
│   ├── telegram_service/     # Enterprise bot
│   └── ...
├── omnix_strategies/         # Regime switcher (huérfano)
├── omnix_testing/            # Backtesting framework
└── main.py                   # Bootstrap monolítico
```

### 2.2 Métricas de Código

| Métrica | Valor | Evaluación |
|---------|-------|------------|
| Archivos Python | ~180 | Alto |
| Líneas de código | ~45,000 | Significativo |
| Paquetes top-level | 11 | Fragmentado |
| Tests | ~5 | ❌ Insuficiente |
| Type coverage | ~20% | ⚠️ Bajo |
| Imports circulares | Varios | ❌ Problemático |

### 2.3 Componentes Bien Estructurados

| Componente | Ubicación | Por qué funciona |
|------------|-----------|------------------|
| AI Service | `omnix_services/ai_service/` | Interfaces, providers, DI container |
| Database Gateway | `omnix_services/database_service/` | Singleton con connection pool |
| Hexagonal Ports | `omnix/ports/` | Protocols definidos correctamente |
| Trading Profiles | `omnix_core/config/` | Single source of truth |

---

## 3. Problemas Identificados

### 3.1 CRÍTICO: main.py Monolítico

**Archivo:** `main.py` (~300 líneas)

**Problema:** Mezcla todas las responsabilidades:
- Limpieza de cache Redis
- Migraciones de base de datos
- Inicialización de bots
- Flask app creation
- Background trading loop

**Violaciones:**
- SRP: Múltiples razones para cambiar
- DIP: Instancia implementaciones concretas directamente
- Clean Architecture: Framework en el centro

**Impacto:** Imposible hacer testing unitario, cambiar componentes, o escalar.

```python
# ACTUAL (problemático)
async def main():
    redis_cache.cleanup()              # Infraestructura
    await database_service.migrate()   # Infraestructura
    bot = TelegramBot(...)             # Interface
    flask_app = create_app()           # Interface
    trading_loop()                     # Application
```

---

### 3.2 ALTO: Acoplamiento Cross-Package

**Problema:** Dashboard importa directamente de services, services instancian otros services a nivel de módulo.

**Ejemplos:**
```python
# omnix_dashboard/blueprints/core.py
from omnix_services.database_service import database_gateway  # Acoplado
from omnix_services.market_intelligence import fear_greed_service  # Acoplado

# omnix_services/trading_service/trading_service.py
from omnix_services.monitoring.risk_guardian import RiskGuardian  # Instancia global
risk_guardian = RiskGuardian()  # Singleton a nivel módulo
```

**Impacto:** 
- Imposible hacer DI
- Tests requieren toda la infraestructura
- Cambiar una implementación rompe múltiples archivos

---

### 3.3 ALTO: Dominio Fragmentado

**Problema:** Lógica de negocio dispersa en 3+ paquetes sin boundaries claros.

| Concepto | Ubicaciones | Duplicación |
|----------|-------------|-------------|
| Trading Logic | `omnix_core/bot/`, `omnix_services/trading_service/` | Sí |
| Risk Management | `omnix_risk/`, `omnix_services/risk_management/`, `omnix_services/monitoring/` | Sí |
| Strategies | `omnix_core/strategies/`, `omnix_strategies/`, `omnix_services/trading_service/` | Sí |
| Portfolio | `omnix_services/portfolio_management/` | No |

**Impacto:** 
- Difícil encontrar código
- Comportamiento inconsistente
- Refactoring peligroso

---

### 3.4 ALTO: Ports No Utilizados

**Problema:** Los ports en `omnix/ports/` están definidos pero no integrados.

```python
# omnix/ports/driven/trading_port.py - DEFINIDO
class TradingPort(Protocol):
    def execute_order(self, order: Order) -> OrderResult: ...

# PERO los servicios no los usan:
# omnix_services/trading_service/kraken_client.py - IGNORA EL PORT
class KrakenClient:
    def execute_order(self, ...):  # No implementa Protocol
```

**Impacto:** Hexagonal architecture iniciada pero abandonada.

---

### 3.5 MEDIO: Configuración Dispersa

**Ubicaciones de configuración:**
1. `omnix_config/settings.py` - Parcial
2. `omnix_config/env_manager.py` - Parcial
3. `os.getenv()` directo - En ~50 archivos
4. Hardcoded defaults - Dispersos
5. `omnix_core/config/trading_profiles.py` - Trading específico

**Impacto:** 
- Difícil cambiar configuración
- Inconsistencia entre ambientes
- Secrets expuestos en código

---

### 3.6 MEDIO: Testing Insuficiente

**Estado actual:**
```
tests/
├── test_intent_detection.py    # 1 test
└── test_pqc_security.py        # 1 test
```

**Cobertura:** <1%

**Áreas sin tests:**
- Trading execution
- Risk calculations
- AI responses
- Database operations
- Telegram commands

---

## 4. Estructura Objetivo

### 4.1 Layout Propuesto (src/)

```
src/
└── omnix/
    ├── domain/                    # Lógica de negocio pura (SIN dependencias externas)
    │   ├── trading/
    │   │   ├── __init__.py
    │   │   ├── entities.py        # Trade, Signal, Position, Order
    │   │   ├── value_objects.py   # Price, Quantity, Pair, Timeframe
    │   │   ├── services.py        # TradingDomainService
    │   │   └── exceptions.py      # TradingError, InsufficientFunds
    │   ├── risk/
    │   │   ├── entities.py        # RiskProfile, DrawdownState
    │   │   ├── value_objects.py   # RiskLevel, Percentage
    │   │   └── services.py        # RiskCalculator
    │   ├── portfolio/
    │   │   ├── entities.py        # Portfolio, Allocation
    │   │   └── services.py        # PortfolioOptimizer
    │   ├── ai/
    │   │   ├── entities.py        # Conversation, Analysis
    │   │   └── services.py        # AIAnalysisDomain
    │   └── strategies/
    │       ├── base.py            # StrategyProtocol
    │       ├── ares.py            # ARES V1/V2
    │       ├── quantum_momentum.py
    │       └── non_markovian.py
    │
    ├── application/               # Use Cases + Ports
    │   ├── trading/
    │   │   ├── __init__.py
    │   │   ├── execute_trade.py   # ExecuteTradeUseCase
    │   │   ├── scan_market.py     # ScanMarketUseCase
    │   │   └── ports.py           # IMarketData, IOrderExecutor (Protocols)
    │   ├── risk/
    │   │   ├── evaluate_risk.py   # EvaluateRiskUseCase
    │   │   └── ports.py           # IRiskStorage
    │   ├── ai/
    │   │   ├── analyze_market.py  # AnalyzeMarketUseCase
    │   │   └── ports.py           # IAIProvider, IContextStorage
    │   └── portfolio/
    │       ├── optimize.py        # OptimizePortfolioUseCase
    │       └── ports.py           # IPortfolioStorage
    │
    ├── infrastructure/            # Adapters (implementaciones concretas)
    │   ├── persistence/
    │   │   ├── __init__.py
    │   │   ├── postgres/
    │   │   │   ├── connection.py  # DatabaseGateway
    │   │   │   ├── repositories.py # TradeRepository, RiskRepository
    │   │   │   └── migrations/
    │   │   └── redis/
    │   │       ├── cache.py       # RedisCache
    │   │       └── state.py       # RedisState
    │   ├── external/
    │   │   ├── kraken/
    │   │   │   ├── client.py      # KrakenAdapter (implements IMarketData, IOrderExecutor)
    │   │   │   └── websocket.py
    │   │   ├── alpaca/
    │   │   │   └── client.py      # AlpacaAdapter
    │   │   ├── ai/
    │   │   │   ├── gemini.py      # GeminiAdapter (implements IAIProvider)
    │   │   │   ├── openai.py
    │   │   │   └── anthropic.py
    │   │   └── stripe/
    │   │       └── client.py      # StripeAdapter
    │   └── messaging/
    │       └── telegram/
    │           └── adapter.py     # TelegramAdapter
    │
    ├── interfaces/                # Entry Points
    │   ├── flask_app/
    │   │   ├── __init__.py        # create_app() factory
    │   │   ├── blueprints/
    │   │   │   ├── core.py
    │   │   │   ├── market.py
    │   │   │   ├── system.py
    │   │   │   └── api.py         # REST API para B2C
    │   │   ├── extensions.py      # Flask extensions + DI
    │   │   └── middleware.py      # Auth, rate limiting
    │   ├── telegram/
    │   │   ├── bot.py             # TelegramBot
    │   │   └── handlers/
    │   ├── cli/
    │   │   └── commands.py        # CLI commands
    │   └── streamlit/
    │       └── app.py             # Investor dashboard
    │
    ├── config/                    # Configuración centralizada
    │   ├── __init__.py
    │   ├── settings.py            # Pydantic BaseSettings
    │   ├── profiles.py            # TradingProfiles
    │   └── logging.py             # Logging config
    │
    └── bootstrap/                 # DI Container + Entry Point
        ├── __init__.py
        ├── container.py           # DIContainer con constructor injection
        └── main.py                # Entry point limpio

tests/                             # Separado del código fuente
├── unit/
│   ├── domain/
│   ├── application/
│   └── infrastructure/
├── integration/
└── e2e/

docs/
├── architecture/
├── audits/
└── core/

pyproject.toml                     # Config central (UV workspace)
Procfile                           # Railway: gunicorn
railway.json                       # Railway: main.py
```

### 4.2 Dependencias Entre Capas

```
┌────────────────────────────────────────────────────────────────┐
│                        interfaces/                              │
│   Flask blueprints, Telegram handlers, CLI commands            │
│   DEPENDE DE: application (use cases)                          │
├────────────────────────────────────────────────────────────────┤
│                        application/                             │
│   Use cases, orchestration, ports (Protocols)                  │
│   DEPENDE DE: domain (entities, services)                      │
├────────────────────────────────────────────────────────────────┤
│                        domain/                                  │
│   Entities, value objects, domain services                     │
│   DEPENDE DE: NADA (puro Python)                               │
├────────────────────────────────────────────────────────────────┤
│                     infrastructure/                             │
│   Adapters que implementan ports                               │
│   DEPENDE DE: application/ports (Protocols)                    │
└────────────────────────────────────────────────────────────────┘
```

---

## 5. Mapeo Legacy → Target

### 5.1 Paquetes Principales

| Legacy | Target | Acción |
|--------|--------|--------|
| `omnix_core/strategies/` | `src/omnix/domain/strategies/` | MOVER |
| `omnix_core/bot/auto_trading_bot.py` | `src/omnix/application/trading/` | REFACTORIZAR |
| `omnix_core/cache/` | `src/omnix/infrastructure/persistence/redis/` | MOVER |
| `omnix_core/config/` | `src/omnix/config/` | MOVER |
| `omnix_services/database_service/` | `src/omnix/infrastructure/persistence/postgres/` | MOVER |
| `omnix_services/ai_service/` | `src/omnix/infrastructure/external/ai/` | ADAPTAR |
| `omnix_services/telegram_service/` | `src/omnix/interfaces/telegram/` | MOVER |
| `omnix_services/trading_service/` | SEPARAR | Domain → domain/, Kraken → infrastructure/ |
| `omnix_services/monitoring/` | `src/omnix/application/risk/` | REFACTORIZAR |
| `omnix_risk/` | MERGE con `src/omnix/domain/risk/` | CONSOLIDAR |
| `omnix_dashboard/` | `src/omnix/interfaces/flask_app/` | MOVER |
| `omnix/ports/` | `src/omnix/application/*/ports.py` | DISTRIBUIR |
| `main.py` | `src/omnix/bootstrap/main.py` | REFACTORIZAR |

### 5.2 Archivos Críticos

| Archivo Legacy | Archivo Target | Complejidad |
|----------------|----------------|-------------|
| `main.py` | `bootstrap/main.py` + `container.py` | ALTA |
| `auto_trading_bot.py` | `application/trading/scan_market.py` + domain | ALTA |
| `database_gateway.py` | `infrastructure/persistence/postgres/connection.py` | MEDIA |
| `enterprise_bot.py` | `interfaces/telegram/bot.py` | MEDIA |
| `app.py` (dashboard) | `interfaces/flask_app/__init__.py` | MEDIA |

---

## 6. Prioridades de Refactoring

### 6.1 Matriz de Impacto vs Esfuerzo

```
                    IMPACTO
                    │
           HIGH     │  ┌─────────────┐     ┌─────────────┐
                    │  │ Config      │     │ main.py     │
                    │  │ Centralizar │     │ Bootstrap   │
                    │  └─────────────┘     └─────────────┘
                    │
           MEDIUM   │  ┌─────────────┐     ┌─────────────┐
                    │  │ Ports       │     │ Domain      │
                    │  │ Integrar    │     │ Consolidar  │
                    │  └─────────────┘     └─────────────┘
                    │
           LOW      │  ┌─────────────┐     ┌─────────────┐
                    │  │ Tests       │     │ Cleanup     │
                    │  │ Añadir      │     │ Legacy      │
                    │  └─────────────┘     └─────────────┘
                    │
                    └──────────────────────────────────────▶ ESFUERZO
                              LOW         MEDIUM        HIGH
```

### 6.2 Orden Recomendado

1. **Config Centralizado** (Quick Win)
   - Crear `src/omnix/config/settings.py` con Pydantic
   - Migrar `os.getenv()` dispersos
   - Impacto: Todos los módulos

2. **Bootstrap Limpio** (Fundación)
   - Refactorizar `main.py` a `bootstrap/`
   - Crear `container.py` para DI
   - Impacto: Entry point, testing

3. **Ports Integración** (Hexagonal)
   - Conectar ports existentes a adapters
   - Blueprints consumen ports, no implementaciones
   - Impacto: Dashboard, testing

4. **Domain Consolidación** (Clean Architecture)
   - Mover strategies a `domain/`
   - Eliminar duplicación risk
   - Impacto: Trading, risk

5. **Tests Coverage** (Quality)
   - Unit tests para domain
   - Integration tests para adapters
   - Impacto: Confidence, CI

---

## Conclusión

OMNIX V6.5.4c tiene funcionalidad enterprise robusta pero necesita reestructuración arquitectónica para:

1. **Escalar a B2C** - Multi-tenant, rate limiting, auth
2. **Mantener calidad** - Tests, DI, separation of concerns
3. **Evolucionar rápido** - Cambiar adapters sin tocar domain

El plan de migración Strangler Fig permite hacerlo **incrementalmente** sin romper producción.

---

## Siguiente Paso

Ver `docs/architecture/MIGRATION_ROADMAP.md` para el plan detallado de ejecución.

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Dec 10, 2025 | Architecture Board | Initial audit |
