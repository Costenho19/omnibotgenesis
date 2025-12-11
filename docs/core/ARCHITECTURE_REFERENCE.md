# OMNIX V6.5.4d Architecture Reference

**Version:** 6.5.4d INSTITUTIONAL+ PREMIUM  
**Last Updated:** December 11, 2025  
**Status:** Active Production System

---

## Table of Contents

1. [Module Catalog](#1-module-catalog)
2. [Hexagonal Ports (Protocol Interfaces)](#2-hexagonal-ports)
3. [Dashboard Architecture](#3-dashboard-architecture)
4. [Service Layer](#4-service-layer)
5. [Data Layer](#5-data-layer)
6. [V6.5.4d Changes](#6-v654d-changes)

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
