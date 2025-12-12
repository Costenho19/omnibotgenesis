# OMNIX V6.5.4d Architecture Reference

**Version:** 6.5.4d INSTITUTIONAL+ PREMIUM  
**Last Updated:** December 12, 2025  
**Status:** Active Production System

---

## Table of Contents

1. [Module Catalog](#1-module-catalog)
2. [Hexagonal Ports (Protocol Interfaces)](#2-hexagonal-ports)
3. [Dashboard Architecture](#3-dashboard-architecture)
4. [Service Layer](#4-service-layer)
5. [Data Layer](#5-data-layer)
6. [V6.5.4d Changes](#6-v654d-changes)
7. [Functional Domain Map](#7-functional-domain-map)
8. [Bootstrap Architecture (V7.0 Phase 1)](#8-bootstrap-architecture-v70-phase-1)
   - [7.1 Resumen de Dominios](#71-resumen-de-dominios)
   - [7.2 Trading Signal Fabric](#72-dominio-1-trading-signal-fabric)
   - [7.3 Market & Data Ingestion](#73-dominio-2-market--data-ingestion)
   - [7.4 Execution & Brokerage](#74-dominio-3-execution--brokerage)
   - [7.5 Risk & Protection](#75-dominio-4-risk--protection)
   - [7.6 AI & Communication](#76-dominio-5-ai--communication)
   - [7.7 User Interfaces](#77-dominio-6-user-interfaces)
   - [7.8 Persistence & Analytics](#78-dominio-7-persistence--analytics)
   - [7.9 Security & Quantum](#79-dominio-8-security--quantum)
   - [7.10 Portfolio Optimization](#710-dominio-9-portfolio-optimization)
   - [7.11 B2C SaaS](#711-dominio-10-b2c-saas-strategic)
   - [7.12 Legacy/Dormant Modules](#712-dominio-11-legacydormant-modules)
   - [7.13 Data Flow End-to-End](#713-flujo-de-datos-end-to-end)
   - [7.14 Cross-Domain Dependencies](#714-dependencias-cruzadas-entre-dominios)

---

## 1. Module Catalog

### 1.1 Core Trading Engines

| Module | Location | Purpose | Dependencies |
|--------|----------|---------|--------------|
| AutoTradingBot V6.5.4d | `omnix_core/bot/auto_trading_bot.py` | Multi-crypto scanner, tiered signals, HMM filter, emergency SL | All strategies |
| TradingSystem V6.5 | `omnix_core/trading_system.py` | Order execution orchestrator | Kraken client |
| CoherenceEngine V6.5 ULTRA | `omnix_services/coherence_service/coherence_engine.py` | 6-tier veto system | Strategy votes |
| Non-Markovian Kernel V6.5 | `omnix_core/strategies/non_markovian_kernel.py` | Temporal memory + on-chain signals | Redis cache |
| Risk Guardian V5.4 | `omnix_services/monitoring/risk_guardian.py` | Overtrading + drawdown protection | Trade history |

### 1.2 Signal Generation Strategies

| Strategy | Location | Signal Type | Weight |
|----------|----------|-------------|--------|
| QuantumMomentum | `omnix_services/trading_service/quantum_momentum.py` | Primary directional | High |
| Monte Carlo | `omnix_services/trading_service/monte_carlo.py` | Probability validation | High |
| Kelly Criterion | `omnix_services/trading_service/kelly_criterion.py` | Position sizing | Medium |
| Black Swan | `omnix_services/trading_service/black_swan.py` | Veto on extreme risk | Veto power |
| HMM Regime | `omnix_services/trading_service/hmm_regime.py` | Market state context | Context |
| Kalman Filter | `omnix_services/trading_service/kalman_filter.py` | Signal noise reduction | Medium |

### 1.3 ARES Strategies (Production Calibration)

| Strategy | Location | Status | Min Confidence | Purpose |
|----------|----------|--------|---------------|---------|
| ARES V1 (Swing) | `omnix_core/strategies/ares_v1.py` | ACTIVE | 70% | Multi-day positions |
| ARES V2 (Scalping) | `omnix_core/strategies/ares_v2.py` | ACTIVE | 75% | Intraday quick trades |

**Note:** ARES strategies share 3 trades/day limit, tracked separately from production metrics.

### 1.4 Support Modules

| Module | Location | Purpose | Trigger |
|--------|----------|---------|---------|
| CAES V6.5.4 | `omnix_core/strategies/caes_module.py` | Dynamic position sizing (0.5x-3x) | Every trade |
| Adaptive Parameter Engine | `omnix_services/adaptive_engine/adaptive_engine.py` | Auto-calibration by regime | Regime change |
| On-Chain Intelligence | `omnix_services/on_chain_service/on_chain_service.py` | Whale tracking, DeFi metrics | Market analysis |
| Execution Protocol V6.5.4d | `omnix_services/execution_service/execution_protocol.py` | 4-layer institutional execution | Trade execution |
| InstitutionalDecisionLogger | `omnix_core/utils/logger.py` | Audit trail for investor reports | All decisions |

### 1.5 AI Service Architecture (SOLID Compliant)

| Component | Location | Purpose |
|-----------|----------|---------|
| ConversationalAIService | `omnix_services/ai_service/ai_service.py` | Main orchestrator |
| RoutingAIGateway | `omnix_services/ai_service/providers/routing_gateway.py` | Multi-provider routing |
| Providers | `omnix_services/ai_service/providers/` | Gemini, OpenAI, Anthropic |
| DI Container | `omnix_services/ai_service/container.py` | 3 providers registered |
| Quantum Physics Validator | `omnix_core/quantum/physics_validator.py` | Scientific accuracy |
| Web Search Service | `omnix_services/web_search_service/` | Tavily integration |

---

## 2. Hexagonal Ports

OMNIX uses hexagonal architecture with protocol ports in `omnix/ports/`. **Phase 1 complete, Phase 2 (integration) deferred to V7.0.**

### 2.1 Driven Ports (Output - System calls external)

| Port | File | Purpose | Methods |
|------|------|---------|---------|
| TradingPort | `driven/trading_port.py` | Exchange operations | `execute_order()`, `get_balance()` |
| DatabasePort | `driven/database_port.py` | Data persistence | `execute_query()`, `save_trade()` |
| CachePort | `driven/cache_port.py` | Caching operations | `get()`, `set()`, `delete()` |
| NotificationPort | `driven/notification_port.py` | User notifications | `send_message()` |
| AIInferencePort | `driven/ai_inference_port.py` | AI model calls | `generate()` |
| MarketDataPort | `driven/market_data_port.py` | Market prices | `get_ohlcv()`, `get_ticker()` |

### 2.2 Driver Ports (Input - External calls system)

| Port | File | Purpose | Methods |
|------|------|---------|---------|
| RestApiPort | `driver/rest_api_port.py` | Flask API handlers | HTTP endpoints |
| TelegramPort | `driver/telegram_port.py` | Bot command handlers | Message handling |

### 2.3 Port Implementation Status

| Port | Protocol Defined | Adapter Exists | Integrated via DI |
|------|-----------------|----------------|-------------------|
| TradingPort | ✅ | ✅ KrakenClient | ⬜ Deferred V7.0 |
| DatabasePort | ✅ | ✅ DatabaseGateway | ⬜ Deferred V7.0 |
| CachePort | ✅ | ✅ RedisCache | ⬜ Deferred V7.0 |
| NotificationPort | ✅ | ✅ TelegramUtils | ⬜ Deferred V7.0 |
| AIInferencePort | ✅ | ✅ AI Providers | ✅ Via container.py |
| MarketDataPort | ✅ | ✅ KrakenData | ⬜ Deferred V7.0 |

**Technical Debt Note:** Adapters exist but are not injected through ports. Services import implementations directly. Full DI integration planned for V7.0 after 500-trade milestone.

---

## 3. Dashboard Architecture

### 3.1 Flask Dashboard (Port 5000)

**Location:** `omnix_dashboard/`

| Endpoint Category | Examples | Purpose |
|-------------------|----------|---------|
| API Metrics | `/api/metrics`, `/api/sharpe` | Trading performance data |
| Reports | `/api/report/pdf` | Investor report generation |
| Calibration | `/api/calibration` | System calibration status |
| Market Data | `/api/market/prices` | Real-time prices |
| Health | `/api/health`, `/api/db-diagnostics` | System status |

**Key Files:**
- `app.py` - Main Flask application
- `blueprints/` - Route modules (core, market, system, intelligence, snapshots, views)
- `utils/database.py` - Database connection via Gateway
- `utils/queries.py` - SQL query templates

### 3.2 Streamlit Dashboard (Port 8080)

**Location:** `omnix_dashboard/streamlit_app.py`

| Widget | Data Source | Update |
|--------|-------------|--------|
| Balance Chart | `/api/balance-history` | 30s |
| Win Rate Gauge | `/api/metrics` | 60s |
| Trade Table | `/api/trades` | 30s |
| P&L Chart | `/api/metrics` | 60s |
| Sharpe/Sortino | `/api/sharpe` | 60s |

### 3.3 API Client

**Location:** `omnix_dashboard/api_client.py`

```python
class OmnixAPIClient:
    def get_metrics() -> dict
    def get_trades(limit: int) -> List[Trade]
    def get_balance_history() -> List[BalancePoint]
    def generate_report() -> bytes  # PDF
```

---

## 4. Service Layer

### 4.1 Services Catalog (24 Subpackages)

| Service | Location | Purpose |
|---------|----------|---------|
| TradingService | `omnix_services/trading_service/` | Order management, strategies |
| PaperTradingManager | `omnix_services/trading_service/paper_trading_manager.py` | Paper trade execution |
| TelegramService | `omnix_services/telegram_service/` | Bot interface |
| AIService | `omnix_services/ai_service/` | Conversational AI (SOLID) |
| DatabaseService | `omnix_services/database_service/` | Data access |
| CoherenceService | `omnix_services/coherence_service/` | 6-tier veto engine |
| ExecutionService | `omnix_services/execution_service/` | Trade execution protocol |
| MonitoringService | `omnix_services/monitoring/` | Risk Guardian, metrics |
| AdaptiveEngine | `omnix_services/adaptive_engine/` | Parameter auto-calibration |
| OnChainService | `omnix_services/on_chain_service/` | Blockchain analytics |
| PortfolioManagement | `omnix_services/portfolio_management/` | Institutional optimization |
| RiskManagement | `omnix_services/risk_management/` | Circuit breaker, limits |
| MarketData | `omnix_services/market_data/` | Price feeds, sentiment |
| MarketIntelligence | `omnix_services/market_intelligence/` | Fear/Greed, news |
| StockTrading | `omnix_services/stock_trading/` | Alpaca integration |
| Derivatives | `omnix_services/derivatives/` | Futures, hedging |
| Analytics | `omnix_services/analytics/` | Fibonacci, patterns |
| Alerts | `omnix_services/alerts/` | Smart notifications |
| Notifications | `omnix_services/notifications/` | Telegram, daily summary |
| UserSettings | `omnix_services/user_settings/` | Per-user configuration |
| VoiceService | `omnix_services/voice_service/` | Voice commands |
| WebSearchService | `omnix_services/web_search_service/` | Tavily search |
| CommunityIntelligence | `omnix_services/community_intelligence/` | Social signals |
| Concurrency | `omnix_services/concurrency/` | Thread management |

### 4.2 Database Gateway

**Location:** `omnix_services/database_service/database_gateway.py`

```
ALL Consumers → DatabaseGateway → Single Pool → PostgreSQL

Features:
- Fork-safe singleton pattern
- Connection pooling (2-15 connections)
- Auto-reconnection
- Tuple-based row access (psycopg3)
```

**Feature Flags:**
- `USE_UNIFIED_GATEWAY=true` - Route through gateway
- `DISABLE_AUTO_MIGRATIONS=true` - Skip startup migrations

---

## 5. Data Layer

### 5.1 PostgreSQL Schema (42 Tables)

| Category | Tables | FK Coverage |
|----------|--------|-------------|
| Core User | 4 | 100% |
| Trading | 5 | 100% |
| Risk Management | 8 | 100% |
| Derivatives | 6 | 100% |
| Community | 5 | 100% |
| Snapshots/Analytics | 6 | 100% |
| System | 8 | N/A |

**Key Tables:**
- `users` - Master user table (PK: user_id)
- `paper_trading_trades` - Paper trade records
- `paper_trading_balances` - User balances
- `risk_guardian_events` - Risk events log
- `decision_logs` - Institutional audit trail

### 5.2 Redis Cache

**Location:** `omnix_core/cache/redis_cache.py`

| Namespace | TTL | Purpose |
|-----------|-----|---------|
| `market:` | 60s | Price data |
| `user:` | 5min | User state |
| `conv:` | 1hr | Conversation history |
| `rate:` | 1min | Rate limiting |

### 5.3 Data Integrity

| Protection | Implementation |
|------------|----------------|
| Foreign Keys | 38 FKs across 42 tables (90%) |
| Tuple Access | psycopg3 returns tuples, not dicts |
| System User | `user_id='system'` for orphan records |
| Defensive Migrations | Column existence checks before ALTER |

---

## 6. V6.5.4d Changes

### 6.1 Entry Threshold Adjustment

| Parameter | V6.5.4c | V6.5.4d | Effect |
|-----------|---------|---------|--------|
| score_strong | 12 | 12 | No change |
| score_moderate | 10 | **12** | MODERATE signals disabled |
| score_very_strong | 15 | 15 | No change |

**Result:** Only STRONG (≥12) or VERY_STRONG (≥15) trades allowed. No more MODERATE entries.

### 6.2 Emergency Stop Loss

```python
class AutoTradingBot:
    EMERGENCY_SL_PCT = 0.02  # 2% maximum absolute loss
```

**Priority Order:**
1. Emergency SL (loss > 2%) - IMMEDIATE EXIT
2. Take Profit check
3. Calibrated Stop Loss

### 6.3 Symbol Exclusions

| Symbol | Status | Reason |
|--------|--------|--------|
| ADA/USD | EXCLUDED | 0% win rate over 12 trades |

### 6.4 Macro Trend Veto

| Condition | Penalty | Effect |
|-----------|---------|--------|
| Kalman BEARISH (strength > 0.6) | -15 points | Blocks most trades |
| HMM trending_bear state | -10 points | Additional penalty |

---

## 7. Functional Domain Map

Esta sección organiza todos los módulos de OMNIX por **capacidad de negocio**, documentando su propósito funcional, APIs externas consumidas, y relaciones entre dominios.

### 7.1 Resumen de Dominios

| # | Dominio | Propósito | Estado | Paquetes Principales |
|---|---------|-----------|--------|---------------------|
| 1 | **Trading Signal Fabric** | Generación y validación de señales | CORE | trading_service, coherence_service, strategies/ |
| 2 | **Market & Data Ingestion** | Datos de mercado y enriquecimiento | CORE | market_data, market_intelligence, on_chain_service |
| 3 | **Execution & Brokerage** | Ejecución de órdenes en exchanges | CORE | execution_service, trading_system.py, kraken_client |
| 4 | **Risk & Protection** | Gestión de riesgo y protección | CORE | risk_management, monitoring, omnix_risk/ |
| 5 | **AI & Communication** | IA conversacional y búsqueda | CORE | ai_service, web_search_service, voice_service |
| 6 | **User Interfaces** | Interfaces de usuario | INTERFACE | telegram_service, omnix_dashboard/ |
| 7 | **Persistence & Analytics** | Almacenamiento y métricas | INFRASTRUCTURE | database_service, cache/, analytics |
| 8 | **Security & Quantum** | Seguridad post-cuántica | CORE | security/, quantum/ |
| 9 | **Portfolio Optimization** | Optimización institucional | SUPPORT | portfolio_management, optimization |
| 10 | **B2C SaaS** | Monetización futura | STRATEGIC | omnix_api/, user_settings |
| 11 | **Legacy/Dormant** | Código legacy o sin usar | LEGACY | alerts, concurrency, regime_switcher |

---

### 7.2 Dominio 1: Trading Signal Fabric

**Propósito:** Generación, agregación y validación de señales de trading mediante múltiples estrategias con consenso.

| Paquete | Ubicación | Función | APIs Externas | Importado Por |
|---------|-----------|---------|---------------|---------------|
| **TradingService** | `omnix_services/trading_service/` | Estrategias de señal (Quantum Momentum, Monte Carlo, HMM, Kalman, Kelly, Black Swan) | Kraken REST/WebSocket | auto_trading_bot.py |
| **CoherenceService** | `omnix_services/coherence_service/` | Sistema de veto 6-Tier para consenso de señales | Ninguna | auto_trading_bot.py |
| **AdaptiveEngine** | `omnix_services/adaptive_engine/` | Auto-calibración de parámetros por régimen de mercado | Ninguna | auto_trading_bot.py |
| **NonMarkovianKernel** | `omnix_core/strategies/non_markovian_kernel.py` | Memoria temporal + integración on-chain | Redis | auto_trading_bot.py |
| **CAES Module** | `omnix_core/strategies/caes_module.py` | Position sizing dinámico (0.5x-3x) | Ninguna | auto_trading_bot.py |
| **ARES V1/V2** | `omnix_core/strategies/ares_v1.py, ares_v2.py` | Swing + Scalping para track record | Ninguna | auto_trading_bot.py |
| **Optimization** | `omnix_services/optimization/` | ML-based weight optimization, auto-learner | Ninguna | auto_trading_bot.py |

**Flujo interno:**
```
Estrategias (6+) → CoherenceEngine (veto) → AdaptiveEngine (calibración) → CAES (sizing) → Señal Final
```

---

### 7.3 Dominio 2: Market & Data Ingestion

**Propósito:** Obtención de datos de mercado, on-chain, noticias y sentimiento para enriquecer análisis.

| Paquete | Ubicación | Función | APIs Externas | Importado Por |
|---------|-----------|---------|---------------|---------------|
| **MarketData** | `omnix_services/market_data/` | Precios, orderbook, arbitrage scanner | Kraken REST/WebSocket | trading_service, dashboard |
| **MarketIntelligence** | `omnix_services/market_intelligence/` | Fear & Greed, noticias, indicadores técnicos | AlphaVantage, Finnhub, Alternative.me | dashboard, ai_service |
| **OnChainService** | `omnix_services/on_chain_service/` | Whale tracking, exchange flows, network metrics | *APIs planned but not yet integrated* | Not actively imported (DORMANT) |
| **WebSearchService** | `omnix_services/web_search_service/` | Búsqueda web en tiempo real | Tavily | ai_service, enterprise_bot |
| **NewsScraper** | `omnix_services/news_scraper.py` | Scraping de noticias | Ninguna | market_intelligence |
| **SymbolClassifier** | `omnix_services/symbol_classifier.py` | Clasificación crypto/stock de símbolos | Ninguna | enterprise_bot |

**APIs Externas Consumidas:**

| API | Servicio | Datos Proporcionados | Rate Limit |
|-----|----------|---------------------|------------|
| Kraken REST | market_data | OHLCV, ticker, orderbook | 15 req/min |
| Kraken WebSocket | market_data | Real-time prices, trades | Streaming |
| AlphaVantage | market_intelligence | Technical indicators (RSI, MACD) | 5 req/min (free) |
| Finnhub | market_intelligence | News, sentiment, fundamentals | 60 req/min |
| Alternative.me | market_intelligence | Fear & Greed Index | 30 req/hour |
| Tavily | web_search_service | Web search results | Per API key |

---

### 7.4 Dominio 3: Execution & Brokerage

**Propósito:** Ejecución de órdenes en exchanges con protocolo institucional de 4 capas.

| Paquete | Ubicación | Función | APIs Externas | Importado Por |
|---------|-----------|---------|---------------|---------------|
| **ExecutionService** | `omnix_services/execution_service/` | Protocolo 4-capas: liquidez, correlación, micro-volatilidad | Ninguna (usa kraken_client) | auto_trading_bot |
| **TradingSystem** | `omnix_core/trading_system.py` | Orquestador de ejecución de órdenes | Kraken REST | main.py, enterprise_bot |
| **KrakenClient** | `omnix_services/trading_service/kraken_client.py` | Cliente de Kraken para crypto | Kraken REST | trading_system, execution_service |
| **PaperTradingManager** | `omnix_services/trading_service/paper_trading_manager.py` | Ejecución simulada para paper trading | Ninguna | auto_trading_bot, enterprise_bot |
| **Derivatives** | `omnix_services/derivatives/` | Futuros Kraken, margin, hedging | Kraken Futures API | main.py (condicional) |
| **StockTrading** | `omnix_services/stock_trading/` | Trading de acciones | Alpaca API | enterprise_bot |
| **PositionManager** | `omnix_services/trading_service/position_manager.py` | Gestión de posiciones abiertas | Ninguna | auto_trading_bot |

**Exchanges Soportados:**

| Exchange | Tipo | Estado | Paquete |
|----------|------|--------|---------|
| Kraken Spot | Crypto | CORE - Producción | kraken_client.py |
| Kraken Futures | Crypto Derivatives | STRATEGIC | derivatives/ |
| Alpaca | Stocks | SUPPORT | stock_trading/ |

---

### 7.5 Dominio 4: Risk & Protection

**Propósito:** Gestión de riesgo multinivel con circuit breakers, límites y protección de portfolio.

| Paquete | Ubicación | Función | APIs Externas | Importado Por |
|---------|-----------|---------|---------------|---------------|
| **RiskManagement** | `omnix_services/risk_management/` | Circuit breaker, límites, position monitor | Ninguna | auto_trading_bot, enterprise_bot |
| **Monitoring** | `omnix_services/monitoring/` | Risk Guardian V5.4, métricas, performance tracker | Ninguna | auto_trading_bot |
| **OmnixRisk** | `omnix_risk/` | Audit logger, cascade protection, dead man switch, USD calculator | Ninguna | trading_system, dashboard |
| **MemoryRiskAdapter** | `omnix_services/risk_management/memory_risk_adapter.py` | Adaptador kernel → risk system | Ninguna | auto_trading_bot |
| **RollbackProtocol** | `omnix_core/risk/rollback_protocol.py` | Rollback de trades fallidos | Ninguna | auto_trading_bot |

**Capas de Protección:**

```
┌─────────────────────────────────────────────────────────────┐
│  Capa 1: Emergency SL (2% max loss)                         │
│  Capa 2: Risk Guardian (daily loss limit, overtrading)      │
│  Capa 3: Circuit Breaker (halt on extreme events)           │
│  Capa 4: Cascade Protection (portfolio-level stops)         │
│  Capa 5: Dead Man Switch (inactivity protection)            │
└─────────────────────────────────────────────────────────────┘
```

---

### 7.6 Dominio 5: AI & Communication

**Propósito:** IA conversacional multi-proveedor, búsqueda web y servicios de voz.

| Paquete | Ubicación | Función | APIs Externas | Importado Por |
|---------|-----------|---------|---------------|---------------|
| **AIService** | `omnix_services/ai_service/` | Orquestador AI con DI container (modelo SOLID) | Gemini, OpenAI, Anthropic | enterprise_bot, auto_trading_bot |
| **Providers** | `omnix_services/ai_service/providers/` | Gemini (primario), OpenAI, Anthropic (fallback) | Ver abajo | ai_service |
| **VideoAnalyzer** | `omnix_services/ai_service/video/` | Análisis de video para aprendizaje | OpenAI Whisper | enterprise_bot |
| **VoiceService** | `omnix_services/voice_service/` | STT (Whisper) + TTS para respuestas de voz | OpenAI Whisper | trading_system.py (VoiceEngine, VoiceServiceEnterprise), enterprise_bot.py |
| **QuantumPhysicsValidator** | `omnix_core/quantum/physics_validator.py` | Validación de precisión científica en respuestas | Ninguna | ai_prompts |

**Proveedores AI:**

| Proveedor | Modelo | Rol | Rate Limit |
|-----------|--------|-----|------------|
| Google Gemini | 2.0 Flash | Primario | 60 RPM |
| OpenAI | GPT-4o | Backup | Per API key |
| Anthropic | Claude | Fallback | Per API key |

---

### 7.7 Dominio 6: User Interfaces

**Propósito:** Interfaces de usuario para interacción con el sistema.

| Paquete | Ubicación | Función | Puerto | Importado Por |
|---------|-----------|---------|--------|---------------|
| **TelegramService** | `omnix_services/telegram_service/` | Bot Telegram (7,812 líneas) | N/A | main.py |
| **FlaskDashboard** | `omnix_dashboard/` | API REST + terminal web | 5000 | Streamlit, usuarios |
| **StreamlitDashboard** | `omnix_dashboard/streamlit_app.py` | Visualización interactiva para inversores | 8080 | N/A |
| **Notifications** | `omnix_services/notifications/` | Trade notifications, daily summary | N/A | auto_trading_bot |
| **InlineKeyboards** | `omnix_services/telegram_service/inline_keyboards.py` | Botones interactivos Telegram | N/A | enterprise_bot |

**Endpoints Dashboard (selección):**

| Categoría | Endpoints | Función |
|-----------|-----------|---------|
| Métricas | `/api/metrics`, `/api/sharpe` | Performance trading |
| Reportes | `/api/report/pdf` | Generación PDF |
| Market | `/api/market/prices` | Precios real-time |
| Health | `/api/health`, `/api/db-diagnostics` | Estado sistema |

---

### 7.8 Dominio 7: Persistence & Analytics

**Propósito:** Almacenamiento de datos, caching y generación de reportes analíticos.

| Paquete | Ubicación | Función | Tecnología | Importado Por |
|---------|-----------|---------|------------|---------------|
| **DatabaseService** | `omnix_services/database_service/` | Gateway PostgreSQL, migraciones | PostgreSQL | 45+ archivos |
| **RedisCache** | `omnix_core/cache/` | Caching, estado de sesión | Redis | trading_service, ai_service |
| **Analytics** | `omnix_services/analytics/` | Institutional metrics, Fibonacci, volume profile | Ninguna | dashboard, omnix_reports |
| **OmnixReports** | `omnix_reports/` | Generador de pitch deck PDF | ReportLab | dashboard |

**Tablas PostgreSQL (42 total):**

| Categoría | Tablas | Propósito |
|-----------|--------|-----------|
| Core User | 4 | users, user_settings, sessions, preferences |
| Trading | 5 | paper_trading_trades, paper_trading_balances, orders, positions |
| Risk | 8 | risk_guardian_events, circuit_breaker_logs, limits |
| Derivatives | 6 | futures_positions, hedging_records |
| Community | 5 | signal_contributions, rewards, feedback |
| Analytics | 6 | decision_logs, snapshots, calibration_history |

---

### 7.9 Dominio 8: Security & Quantum

**Propósito:** Seguridad post-cuántica y mejoras cuánticas para trading.

| Paquete | Ubicación | Función | APIs Externas | Importado Por |
|---------|-----------|---------|---------------|---------------|
| **PQCSecurity** | `omnix_core/security/pqc_security.py` | Encriptación Dilithium post-cuántica | Ninguna | trading_system, trading_service |
| **QuantumEnhancements** | `omnix_core/quantum/enhancements.py` | QRNG (Quantum Random Number Generator) | ANU QRNG | monte_carlo, enterprise_bot |
| **DWaveQAOA** | `omnix_core/quantum/dwave_qaoa.py` | Optimización cuántica (futuro) | D-Wave (planned) | Ninguno actualmente |
| **PhysicsValidator** | `omnix_core/quantum/physics_validator.py` | Validación científica de respuestas AI | Ninguna | ai_prompts |
| **TestingFramework** | `omnix_core/quantum/testing_framework.py` | Tests para componentes cuánticos | Ninguna | tests/ |

---

### 7.10 Dominio 9: Portfolio Optimization

**Propósito:** Optimización de portfolio a nivel institucional.

| Paquete | Ubicación | Función | Algoritmos | Importado Por |
|---------|-----------|---------|------------|---------------|
| **PortfolioManagement** | `omnix_services/portfolio_management/` | Optimización institucional | Markowitz, Black-Litterman, HRP | auto_trading_bot |
| **PortfolioOptimizer** | `.../institutional/portfolio_optimizer.py` | Engine de optimización | Kelly Criterion, Risk Parity | portfolio_management |
| **ExposureManager** | `.../institutional/exposure_manager.py` | Gestión de exposición | CVaR | portfolio_management |
| **VolatilityTargeting** | `.../institutional/volatility_targeting.py` | Targeting de volatilidad | Volatility scaling | portfolio_management |

---

### 7.11 Dominio 10: B2C SaaS (STRATEGIC)

**Propósito:** Infraestructura para monetización futura del producto.

| Paquete | Ubicación | Función | APIs Externas | Estado |
|---------|-----------|---------|---------------|--------|
| **OmnixAPI** | `omnix_api/` | Integración Stripe para pagos | Stripe | STRATEGIC - Scaffolded |
| **UserSettings** | `omnix_services/user_settings/` | Configuración por usuario, perfiles de riesgo | Ninguna | ACTIVE |

**Planes B2C Planificados:**

| Plan | Precio | Funciones |
|------|--------|-----------|
| Básico | $19/mes | Alertas, análisis básico |
| Pro | $29/mes | Trading signals, AI assistant |
| Premium | $49/mes | Full access, portfolio optimization |

---

### 7.12 Dominio 11: Legacy/Dormant Modules

**Propósito:** Código legacy o sin uso activo que requiere evaluación.

| Paquete | Ubicación | Estado | Razón | Recomendación |
|---------|-----------|--------|-------|---------------|
| **Alerts** | `omnix_services/alerts/` | DORMANT | No hay imports activos; notifications/ se usa en su lugar | Consolidar en notifications/ o deprecar |
| **Concurrency** | `omnix_services/concurrency/` | ACTIVE | Importado en `main.py` (IntelligentCacheSystem, OptimizedConcurrencyManager) | Mantener; evaluar consolidación en V7.0 |
| **RegimeSwitcher** | `omnix_strategies/regime_switcher.py` | LEGACY | Sin imports directos; funcionalidad en adaptive_engine | Deprecar en V7.0 |
| **CommunityIntelligence** | `omnix_services/community_intelligence/` | PARTIAL | Solo usado por Telegram commands | Evaluar integración con trading pipeline o archivar |
| **OnChainService** | `omnix_services/on_chain_service/` | DORMANT | Sin imports activos; APIs externas no integradas | Activar en V7.0 con feature flag |

**Nota Importante:** Verificar imports reales antes de deprecar:
```bash
grep -r "from omnix_services.<package>" . --include="*.py"
```

**Plan de Remediación:** Ver `docs/current/TECHNICAL_DEBT.md`

---

### 7.13 Flujo de Datos End-to-End

> **Nota:** Este diagrama muestra el flujo **automatizado** principal. Rutas adicionales incluyen:
> - **Telegram Manual:** Usuario → enterprise_bot → TradingService → Execution (bypass de auto-scan)
> - **Dashboard Read:** PostgreSQL → Flask API → Streamlit (read-only consumption)
> - **Voice Commands:** VoiceService → enterprise_bot → Trading commands

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 OMNIX V6.5.4d DATA FLOW (Automated Trading Path)            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐      │
│  │   EXTERNAL APIs  │    │  ON-CHAIN [*]    │    │   NEWS/SENTIMENT │      │
│  │  (Kraken, Alpaca)│    │  *Planned/Dormant│    │ (Finnhub, F&G)   │      │
│  └────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘      │
│           │                       │                       │                 │
│           ▼                       ▼                       ▼                 │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                     MARKET DATA INGESTION                          │    │
│  │  market_data/ + market_intelligence/ + on_chain_service/           │    │
│  └────────────────────────────────┬───────────────────────────────────┘    │
│                                   │                                         │
│                                   ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                      REDIS CACHE (TTL: 60s-1hr)                    │    │
│  │  omnix_core/cache/redis_cache.py                                   │    │
│  └────────────────────────────────┬───────────────────────────────────┘    │
│                                   │                                         │
│                                   ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                     SIGNAL GENERATION STACK                        │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │    │
│  │  │ Quantum     │  │ Monte Carlo │  │ HMM Regime  │  │ Kalman    │ │    │
│  │  │ Momentum    │  │             │  │             │  │ Filter    │ │    │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬─────┘ │    │
│  │         └─────────────────┴─────────────────┴───────────────┘       │    │
│  │                                   │                                 │    │
│  │                    ┌──────────────▼──────────────┐                  │    │
│  │                    │   Non-Markovian Kernel      │                  │    │
│  │                    │   (Temporal Memory)         │ [*on_chain TBD]  │    │
│  │                    └──────────────┬──────────────┘                  │    │
│  └───────────────────────────────────┼────────────────────────────────┘    │
│                                      │                                      │
│                                      ▼                                      │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                    COHERENCE ENGINE (6-Tier Veto)                  │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  │    │
│  │  │ Tier 1  │  │ Tier 2  │  │ Tier 3  │  │ Tier 4  │  │ Tier 5  │  │    │
│  │  │ Signal  │→ │ Context │→ │ Risk    │→ │ Memory  │→ │ Macro   │  │    │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘  │    │
│  │                                                           │        │    │
│  │                                                    ┌──────▼──────┐ │    │
│  │                                                    │ Tier 6 VETO │ │    │
│  │                                                    │ (Final Gate)│ │    │
│  │                                                    └──────┬──────┘ │    │
│  └───────────────────────────────────────────────────────────┼────────┘    │
│                                                              │              │
│                                      ┌───────────────────────┘              │
│                                      │ PASS/BLOCK                           │
│                                      ▼                                      │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                        RISK GUARDIAN V5.4                          │    │
│  │  Daily Loss Check → Overtrading Check → Revenge Trade Check        │    │
│  └────────────────────────────────────┬───────────────────────────────┘    │
│                                       │ APPROVED                            │
│                                       ▼                                     │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                    EXECUTION PROTOCOL (4-Layer)                    │    │
│  │  Liquidity Check → Correlation Check → Micro-Volatility → Execute  │    │
│  └────────────────────────────────────┬───────────────────────────────┘    │
│                                       │                                     │
│           ┌───────────────────────────┼───────────────────────────┐        │
│           │                           │                           │        │
│           ▼                           ▼                           ▼        │
│  ┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────┐   │
│  │   POSTGRESQL    │    │   TELEGRAM/DASHBOARD │    │   INVESTOR      │   │
│  │   (42 tables)   │    │   (Notifications)    │    │   REPORTS       │   │
│  └─────────────────┘    └──────────────────────┘    └─────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 7.14 Dependencias Cruzadas Entre Dominios

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CROSS-DOMAIN DEPENDENCY MATRIX                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  auto_trading_bot.py (HUB CENTRAL)                                          │
│  ├── omnix_services/monitoring/           (Risk Guardian)                   │
│  ├── omnix_services/optimization/         (Adaptive Weights)                │
│  ├── omnix_services/ai_service/           (Video Learning)                  │
│  ├── omnix_services/coherence_service/    (6-Tier Veto)                     │
│  ├── omnix_services/risk_management/      (Circuit Breaker, Limits)         │
│  ├── omnix_services/adaptive_engine/      (Parameter Calibration)           │
│  ├── omnix_services/trading_service/      (Position Manager)                │
│  ├── omnix_services/execution_service/    (Execution Protocol)              │
│  ├── omnix_core/strategies/               (Non-Markovian, CAES, ARES)       │
│  ├── omnix_core/config/                   (Trading Profiles)                │
│  ├── omnix_core/sessions/                 (User Sessions)                   │
│  └── omnix_core/risk/                     (Rollback Protocol)               │
│                                                                             │
│  enterprise_bot.py (TELEGRAM INTERFACE)                                     │
│  ├── omnix_services/ai_service/           (Conversational AI)               │
│  ├── omnix_services/trading_service/      (Trading Commands)                │
│  ├── omnix_services/market_data/          (Arbitrage Scanner)               │
│  ├── omnix_services/community_intelligence/ (Signal Contribution)           │
│  ├── omnix_services/voice_service/        (Voice Responses)                 │
│  ├── omnix_services/web_search_service/   (Web Search)                      │
│  ├── omnix_services/stock_trading/        (Stock Commands)                  │
│  ├── omnix_services/risk_management/      (Risk Dashboard)                  │
│  ├── omnix_services/user_settings/        (User Preferences)                │
│  ├── omnix_services/notifications/        (Trade Alerts)                    │
│  └── omnix_core/quantum/                  (QRNG, Physics Validator)         │
│                                                                             │
│  NonMarkovianKernel (BRIDGE TO ON-CHAIN)                                    │
│  └── omnix_services/on_chain_service/     (Whale + Exchange Flows)          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Bootstrap Architecture (V7.0 Phase 1)

**Status:** Completed December 12, 2025  
**Purpose:** Centralized configuration and dependency injection for V7.0 migration

### 8.1 Settings Module

**Location:** `src/omnix/config/settings.py`

Provides centralized access to all environment variables with sensible defaults:

```python
from src.omnix.config import get_settings

settings = get_settings()
print(settings.trading_profile)  # 'PRODUCTION_STABLE'
print(settings.paper_mode)       # True
print(settings.database_url)     # Database connection string
```

**Key Properties:**

| Category | Properties |
|----------|------------|
| Database | `database_url`, `redis_url`, `db_pool_min`, `db_pool_max` |
| Trading | `trading_profile`, `paper_mode`, `max_trade_usd`, `drawdown_limit` |
| API Keys | `kraken_api_key`, `telegram_bot_token`, `gemini_api_key`, `openai_api_key` |
| Features | `enable_ares_v1`, `enable_ares_v2`, `use_unified_gateway` |
| Environment | `is_railway`, `is_replit`, `log_level`, `port` |

### 8.2 DI Container

**Location:** `src/omnix/bootstrap/container.py`

Provides dependency injection with Protocol interfaces:

```python
from src.omnix.bootstrap import Container, get_container

container = get_container()
db = container.database      # IDatabaseGateway
cache = container.cache      # IRedisCache
settings = container.settings
```

**Protocol Interfaces:**

| Protocol | Purpose | Null Object |
|----------|---------|-------------|
| `IDatabaseGateway` | PostgreSQL access | `NullDatabase` |
| `IRedisCache` | Redis caching | `NullCache` |
| `ITradingService` | Trading operations | N/A |
| `IMarketDataService` | Market data | N/A |

### 8.3 Bootstrap Runtime

**Location:** `src/omnix/bootstrap/runtime.py`

Orchestrates application startup:

```python
from src.omnix.bootstrap import bootstrap_omnix

result = bootstrap_omnix()
if result.success:
    container = result.container
    # Application ready
```

**Bootstrap Sequence:**

1. Configure logging
2. Validate environment variables
3. Initialize DI container
4. Verify database connection
5. Prime Redis cache
6. Return `BootstrapResult`

### 8.4 Backward Compatibility

Legacy code continues to work without changes. New code can use centralized imports:

```python
# Legacy (still works)
import os
db_url = os.environ.get('DATABASE_URL')

# New (recommended)
from src.omnix.config import get_settings
settings = get_settings()
db_url = settings.database_url
```

### 8.5 Tests

**Location:** `tests/test_phase1_bootstrap.py`

16 tests covering:
- Settings singleton and caching
- Container creation and health checks
- Protocol interface imports
- Environment variable reading
- Bootstrap runtime execution

---

## Appendix: Directory Structure

```
omnix/
├── ports/                    # 8 hexagonal protocol interfaces
│   ├── driven/               # Output ports (Trading, DB, Cache, AI, Market, Notification)
│   └── driver/               # Input ports (RestApi, Telegram)
├── omnix_api/                # Stripe integration (B2C planned)
├── omnix_config/             # Settings, env manager
├── omnix_core/
│   ├── bot/                  # AutoTradingBot V6.5.4d
│   ├── cache/                # Redis integration
│   ├── config/               # Trading profiles (single source of truth)
│   ├── context/              # Real data provider
│   ├── quantum/              # Physics validator, QAOA
│   ├── risk/                 # Rollback protocol
│   ├── security/             # Post-quantum cryptography
│   ├── sessions/             # User session manager
│   ├── strategies/           # ARES V1/V2, CAES, Non-Markovian
│   └── utils/                # Logger, rate limiter
├── omnix_dashboard/          # Flask + Streamlit dashboards
├── omnix_reports/            # Pitch deck generator
├── omnix_risk/               # Portfolio summary, cascade protection
├── omnix_services/           # 24 service subpackages
├── omnix_strategies/         # Regime switcher (legacy)
├── omnix_testing/            # Backtesting framework
├── docs/                     # Technical documentation
├── main.py                   # Bootstrap entry point
└── requirements.txt          # Python dependencies
```

---

## Appendix B: Module Migration Map (V7.0 Target)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  src/omnix/                    LEGACY → TARGET                          │
│                                                                          │
│  ├── domain/                 ← omnix_core/strategies/                   │
│  │   ├── trading/                omnix_core/risk/                       │
│  │   ├── risk/                   omnix_services/coherence_service/      │
│  │   └── strategies/             omnix_services/monitoring/ (domain)    │
│  │                                                                       │
│  ├── application/            ← omnix_core/bot/                          │
│  │   ├── trading/                omnix_services/execution_service/      │
│  │   ├── analysis/               omnix_services/ai_service/             │
│  │   └── reports/                omnix_reports/                         │
│  │                                                                       │
│  ├── infrastructure/         ← omnix_core/cache/                        │
│  │   ├── persistence/            omnix_services/database_service/       │
│  │   ├── external/               omnix_services/trading_service/        │
│  │   └── notifications/          omnix_services/market_data/            │
│  │                                                                       │
│  ├── interfaces/             ← omnix_dashboard/                         │
│  │   ├── flask_app/              omnix_services/telegram_service/       │
│  │   └── telegram/                                                       │
│  │                                                                       │
│  ├── config/                 ← omnix_config/                            │
│  │   └── settings.py             omnix_core/config/                     │
│  │                                                                       │
│  └── bootstrap/              ← main.py                                  │
│      └── container.py                                                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix C: Dependency Injection Status

| Component | Current | Target |
|-----------|---------|--------|
| AI Service | DI Container | Keep (reference model) |
| Database | Singleton | Inject via port |
| Redis Cache | Singleton | Inject via port |
| Kraken Client | Direct import | Inject via port |
| Telegram Bot | Direct import | Inject via port |
| Risk Guardian | Direct import | Inject via port |

---

## Appendix D: Type Coverage

| Package | Estimated Coverage | Target |
|---------|-------------------|--------|
| `omnix_core/` | ~15% | 60% |
| `omnix_services/ai_service/` | ~60% | 80% |
| `omnix_services/` (other) | ~10% | 60% |
| `omnix_dashboard/` | ~5% | 40% |

---

*Last updated: December 12, 2025*
