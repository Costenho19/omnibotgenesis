# OMNIX V6.5.4c Architecture Reference

**Version:** 6.5.4c INSTITUTIONAL+ PREMIUM  
**Last Updated:** December 10, 2025  
**Status:** Active Production System

---

## Table of Contents

1. [Module Catalog](#1-module-catalog)
2. [Hexagonal Ports (Protocol Interfaces)](#2-hexagonal-ports)
3. [Dashboard Architecture](#3-dashboard-architecture)
4. [Service Layer](#4-service-layer)
5. [Data Layer](#5-data-layer)

---

## 1. Module Catalog

### 1.1 Core Trading Engines

| Module | Location | Purpose | Dependencies |
|--------|----------|---------|--------------|
| AutoTradingBot V6.5.4 | `omnix_core/auto_trading_bot.py` | Multi-crypto scanner, tiered signals, HMM filter | All strategies |
| TradingSystem V6.5 | `omnix_core/trading_system.py` | Order execution orchestrator | Kraken client |
| CoherenceEngine V6.5 ULTRA | `omnix_core/strategies/coherence_engine.py` | 6-tier veto system | Strategy votes |
| Non-Markovian Kernel V6.5 | `omnix_core/strategies/non_markovian_memory.py` | Temporal memory + on-chain signals | Redis cache |
| Risk Guardian V5.4 | `omnix_core/risk/risk_guardian.py` | Overtrading + drawdown protection | Trade history |

### 1.2 Signal Generation Strategies

| Strategy | Location | Signal Type | Weight |
|----------|----------|-------------|--------|
| QuantumMomentum | `omnix_core/strategies/quantum_momentum.py` | Primary directional | High |
| Monte Carlo | `omnix_core/strategies/monte_carlo.py` | Probability validation | High |
| Kelly Criterion | `omnix_core/strategies/kelly_criterion.py` | Position sizing | Medium |
| Black Swan | `omnix_core/strategies/black_swan_detector.py` | Veto on extreme risk | Veto power |
| HMM Regime | `omnix_core/strategies/hmm_regime.py` | Market state context | Context |
| Kalman Filter | `omnix_core/strategies/kalman_filter.py` | Signal noise reduction | Medium |
| Sentiment Analysis | `omnix_core/strategies/sentiment_analysis.py` | Market sentiment | Low |

### 1.3 Experimental Strategies (ARES)

| Strategy | Status | Min Confidence | Purpose |
|----------|--------|---------------|---------|
| ARES V1 (Swing) | ACTIVE | 70% | Multi-day positions |
| ARES V2 (Scalping) | ACTIVE | 75% | Intraday quick trades |

**Note:** ARES strategies share 3 trades/day limit, tracked separately from production metrics.

### 1.4 Support Modules

| Module | Purpose | Trigger |
|--------|---------|---------|
| CAES (Confidence-Adaptive Entry) | Dynamic position sizing | Every trade |
| Adaptive Parameter Engine | Auto-calibration by regime | Regime change |
| On-Chain Intelligence | Whale tracking, DeFi metrics | Market analysis |
| Execution Protocol V6.5.4 | 4-layer institutional execution | Trade execution |
| InstitutionalDecisionLogger | Audit trail for investor reports | All decisions |

### 1.5 AI Service Architecture

| Component | Location | Purpose |
|-----------|----------|---------|
| ConversationalAIService | `omnix_services/ai_service/ai_service.py` | Main orchestrator (371 lines) |
| RoutingAIGateway | `omnix_services/ai_service/gateway.py` | Multi-provider routing |
| Providers | `omnix_services/ai_service/providers/` | Gemini, OpenAI, Anthropic |
| DI Container | `omnix_services/ai_service/container.py` | 3 providers registered |
| Quantum Physics Validator | `omnix_services/ai_service/quantum_validator.py` | Scientific accuracy |
| Web Search Service | `omnix_services/ai_service/web_search/` | Tavily integration |

---

## 2. Hexagonal Ports

OMNIX uses hexagonal architecture with protocol ports in `omnix/ports/`. Phase 1 complete.

### 2.1 Driven Ports (Output - System calls external)

| Port | File | Purpose | Methods |
|------|------|---------|---------|
| ExchangePort | `exchange.py` | Exchange operations | `place_order()`, `get_balance()`, `get_ticker()` |
| DatabasePort | `database.py` | Data persistence | `execute_query()`, `save_trade()`, `get_user()` |
| CachePort | `cache.py` | Caching operations | `get()`, `set()`, `delete()`, `exists()` |
| NotificationPort | `notification.py` | User notifications | `send_telegram()`, `send_email()` |
| AIGatewayPort | `ai_gateway.py` | AI model calls | `generate_text()`, `analyze_image()` |
| MarketDataPort | `market_data.py` | Market prices | `get_ohlcv()`, `get_order_book()` |

### 2.2 Driver Ports (Input - External calls system)

| Port | File | Purpose | Methods |
|------|------|---------|---------|
| TradingBotPort | `trading_bot.py` | Bot control | `start()`, `stop()`, `get_status()` |
| UserCommandPort | `user_command.py` | User inputs | `handle_command()`, `parse_input()` |
| WebhookPort | `webhook.py` | External events | `handle_exchange_event()`, `handle_alert()` |
| SchedulerPort | `scheduler.py` | Timed tasks | `schedule_task()`, `run_cron()` |
| HealthCheckPort | `health_check.py` | System monitoring | `check_health()`, `get_metrics()` |
| ConfigPort | `config.py` | Configuration | `get_profile()`, `update_settings()` |

### 2.3 Port Implementation Status

| Port | Protocol Defined | Adapter Implemented | Tests |
|------|-----------------|---------------------|-------|
| ExchangePort | ✅ | ✅ KrakenAdapter | ⬜ |
| DatabasePort | ✅ | ✅ PostgresAdapter | ⬜ |
| CachePort | ✅ | ✅ RedisAdapter | ⬜ |
| NotificationPort | ✅ | ✅ TelegramAdapter | ⬜ |
| AIGatewayPort | ✅ | ✅ GeminiAdapter | ⬜ |
| MarketDataPort | ✅ | ✅ KrakenDataAdapter | ⬜ |
| TradingBotPort | ✅ | ⬜ Planned V7.0 | ⬜ |
| UserCommandPort | ✅ | ⬜ Planned V7.0 | ⬜ |

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
- `utils/database.py` - Database connection via Gateway
- `utils/metrics_calculator.py` - Sharpe, Sortino, Calmar
- `utils/report_generator.py` - PDF report creation

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

**Location:** `omnix_dashboard/utils/api_client.py`

```python
class OmnixAPIClient:
    def get_metrics() -> dict
    def get_trades(limit: int) -> List[Trade]
    def get_balance_history() -> List[BalancePoint]
    def generate_report() -> bytes  # PDF
```

---

## 4. Service Layer

### 4.1 Services Catalog

| Service | Location | Purpose |
|---------|----------|---------|
| TradingService | `omnix_services/trading_service/` | Order management |
| PaperTradingManager | `omnix_services/trading_service/paper_trading_manager.py` | Paper trade execution |
| TelegramService | `omnix_services/telegram_service/` | Bot interface |
| AIService | `omnix_services/ai_service/` | Conversational AI |
| DatabaseService | `omnix_services/database_service/` | Data access |
| MarketDataService | `omnix_services/market_data_service/` | Price feeds |

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

## Appendix: Directory Structure

```
omnix/
├── ports/                    # 12 hexagonal protocol interfaces
│   ├── driven/               # Output ports (Exchange, DB, Cache, etc.)
│   └── driver/               # Input ports (Bot, Commands, Webhooks)
├── omnix_core/
│   ├── config/
│   │   └── trading_profiles.py  # Single source of truth for profiles
│   ├── strategies/           # All trading strategies
│   ├── risk/                 # Risk management modules
│   └── cache/                # Redis integration
├── omnix_services/
│   ├── ai_service/           # Conversational AI
│   ├── database_service/     # Database Gateway
│   ├── trading_service/      # Paper/real trading
│   └── telegram_service/     # Bot interface
├── omnix_dashboard/
│   ├── app.py                # Flask API (port 5000)
│   └── streamlit_app.py      # Investor dashboard (port 8080)
└── docs/
    ├── core/                 # Technical documentation
    └── audits/               # Investor-facing audits
```
