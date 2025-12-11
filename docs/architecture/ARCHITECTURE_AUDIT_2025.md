# OMNIX V6.5.4d Architecture Audit

**Version:** 1.1  
**Date:** December 11, 2025  
**Auditor:** Architecture Review Board  
**Status:** DIAGNOSTIC COMPLETE - REFACTORING DEFERRED

---

## Executive Summary

Este documento presenta una auditoría completa del codebase OMNIX V6.5.4d, identificando problemas de arquitectura y proponiendo una estructura objetivo alineada con las mejores prácticas Python 2025.

**Hallazgo Principal:** El sistema tiene funcionalidad enterprise robusta pero sufre de acoplamiento excesivo, responsabilidades mezcladas, y ausencia de boundaries de dominio claros. La reestructuración permitirá escalar a B2C SaaS.

**Decisión V6.5.4d:** Todo refactoring está **DIFERIDO** hasta completar el milestone de 500 trades para track record de inversionistas. Ver `docs/core/TECHNICAL_DEBT.md` para registro de deuda técnica.

### V6.5.4d Trading Improvements (December 2025)

| Cambio | Implementación | Impacto |
|--------|---------------|---------|
| Emergency Stop Loss | `EMERGENCY_SL_PCT = 0.02` (clase) | Limita pérdidas a 2% máximo |
| Entry Thresholds | `score_moderate = 12` (igual a strong) | Solo trades STRONG/VERY_STRONG |
| ADA/USD Excluded | `CalibrationTier.EXCLUDED` | Bloquea par con 0% win rate |
| Macro Trend Veto | Kalman -15pts, HMM -10pts | Bloquea trades en tendencia bajista |

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

### 2.1 Estructura de Directorios (V6.5.4d - Actualizado)

```
OMNIX V6.5.4d/
├── omnix/                    # Hexagonal ports (definidos, no integrados)
│   └── ports/
│       ├── driven/           # 6 output ports (TradingPort, DatabasePort, etc.)
│       └── driver/           # 2 input ports (RestApiPort, TelegramPort)
├── omnix_api/                # Stripe integration (B2C preparación)
├── omnix_config/             # Settings, env_manager
├── omnix_core/
│   ├── bot/                  # AutoTradingBot V6.5.4d + EMERGENCY_SL_PCT
│   ├── cache/                # RedisCache, RedisState
│   ├── config/               # Trading profiles (single source of truth)
│   ├── context/              # Real data provider
│   ├── quantum/              # Physics validator, QAOA
│   ├── risk/                 # Rollback protocol
│   ├── security/             # Post-quantum cryptography
│   ├── sessions/             # User session manager
│   ├── strategies/           # ARES V1/V2, CAES, Non-Markovian
│   └── utils/                # Logger, rate limiter
├── omnix_dashboard/          # Flask (5000) + Streamlit (8080)
├── omnix_reports/            # Pitch deck generator
├── omnix_risk/               # Portfolio summary, cascade protection
├── omnix_services/           # 24 service subpackages
│   ├── ai_service/           # SOLID compliant (model for refactoring)
│   ├── coherence_service/    # CoherenceEngine V6.5 ULTRA
│   ├── database_service/     # DatabaseGateway
│   ├── execution_service/    # Execution Protocol V6.5.4d
│   ├── monitoring/           # Risk Guardian V5.4
│   ├── telegram_service/     # Enterprise bot (7.8k lines)
│   ├── trading_service/      # Strategies: Monte Carlo, Kalman, HMM, etc.
│   └── ...                   # 17 more subpackages
├── omnix_strategies/         # Regime switcher (legacy, consider deprecation)
├── omnix_testing/            # Backtesting framework
└── main.py                   # Bootstrap (monolítico - V7.0 refactor)
```

### 2.2 Métricas de Código (Actualizadas)

| Métrica | Valor | Evaluación |
|---------|-------|------------|
| Archivos Python | ~268 | Alto |
| Líneas de código | ~114,000 | Enterprise scale |
| Paquetes top-level | 13 | Fragmentado |
| Tests | ~5 | ❌ Insuficiente |
| Type coverage | ~20% | ⚠️ Bajo |
| Imports circulares | Varios | ❌ Problemático |
| Database tables | 42 | ✅ Completo |

### 2.3 Componentes Bien Estructurados

| Componente | Ubicación | Por qué funciona |
|------------|-----------|------------------|
| AI Service | `omnix_services/ai_service/` | Interfaces, providers, DI container |
| Database Gateway | `omnix_services/database_service/` | Singleton con connection pool |
| Hexagonal Ports | `omnix/ports/` | Protocols definidos correctamente |
| Trading Profiles | `omnix_core/config/` | Single source of truth |

### 2.4 AI Service como Modelo de Referencia (CRÍTICO)

El módulo `omnix_services/ai_service/` **YA implementa** arquitectura moderna correctamente. Debe usarse como **plantilla** para refactorizar otros módulos.

**Estructura actual de AI Service:**
```
omnix_services/ai_service/
├── interfaces/                    # Protocols (ports)
│   ├── ai_gateway.py             # AIGatewayProtocol
│   ├── context_provider.py       # ContextProviderProtocol
│   ├── prompt_builder.py         # PromptBuilderProtocol
│   └── style_renderer.py         # StyleRendererProtocol
├── providers/                     # Adapters (implementaciones)
│   ├── gemini_provider.py        # Implements AIGatewayProtocol
│   ├── openai_provider.py        # Implements AIGatewayProtocol
│   ├── anthropic_provider.py     # Implements AIGatewayProtocol
│   ├── routing_gateway.py        # Multi-provider routing
│   └── ...
├── adapters/                      # Legacy compatibility
│   └── legacy_adapter.py
├── testing/                       # Mocks for unit tests
│   └── fakes.py
├── container.py                   # DI Container
└── ai_service.py                  # Main service (orchestrator)
```

**Patrones a replicar:**
1. **Protocols en interfaces/** - Contratos separados de implementaciones
2. **Providers en providers/** - Cada proveedor implementa Protocol
3. **Container DI** - Factory con lazy initialization
4. **Legacy adapter** - Backward compatibility sin romper código existente
5. **Testing fakes** - Mocks que implementan Protocols

### 2.5 Hexagonal Ports Existentes (Fase 1 Completa)

Los ports en `omnix/ports/` ya están definidos y deben **integrarse**, no reemplazarse:

**Driven Ports (Output):**
| Port | Archivo | Propósito |
|------|---------|-----------|
| `TradingPort` | `driven/trading_port.py` | Exchange adapters |
| `DatabasePort` | `driven/database_port.py` | PostgreSQL repositories |
| `CachePort` | `driven/cache_port.py` | Redis operations |
| `AIInferencePort` | `driven/ai_inference_port.py` | LLM providers |
| `MarketDataPort` | `driven/market_data_port.py` | Market data |
| `NotificationPort` | `driven/notification_port.py` | Telegram messaging |

**Driver Ports (Input):**
| Port | Archivo | Propósito |
|------|---------|-----------|
| `RestApiPort` | `driver/rest_api_port.py` | Flask API endpoints |
| `TelegramPort` | `driver/telegram_port.py` | Bot command handlers |

**Estado:** Definidos pero NO integrados. Fase 2 del MODERNIZATION_ROADMAP pendiente.

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

OMNIX V6.5.4d tiene funcionalidad enterprise robusta pero necesita reestructuración arquitectónica para:

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
