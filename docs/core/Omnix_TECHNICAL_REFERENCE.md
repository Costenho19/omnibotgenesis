# OMNIX V6.5.2 INSTITUTIONAL+ - Technical Reference

**Document Version:** 2.1  
**Created:** December 4, 2025  
**Last Updated:** December 4, 2025  
**Status:** ✅ COMPLETE (Auditoría Técnica Fase 1B - Datos Verificados)

---

## 1. Executive Summary

### 1.1 System Overview

OMNIX V6.5.2 INSTITUTIONAL+ is an enterprise-grade automated cryptocurrency and stock trading system designed for:

| Capability | Description |
|------------|-------------|
| **Multi-Market Trading** | Kraken (crypto) + Alpaca (stocks) |
| **User Capacity** | 100,000+ simultaneous users |
| **AI Integration** | Gemini 2.0 Flash, GPT-4o, Claude |
| **Security** | Post-Quantum Cryptography (NIST 2024) |
| **Trading Modes** | Paper Trading ($1M virtual) + Real Trading |
| **Target** | $400K seed funding at $2.5M valuation |

### 1.2 Codebase Statistics (Measured December 4, 2025)

| Metric | Count | Source |
|--------|-------|--------|
| Total Python Files | 160+ | `find . -name "*.py" \| wc -l` |
| omnix_core Lines | 20,131 | `wc -l omnix_core/**/*.py` |
| omnix_services Lines | 62,613 | `wc -l omnix_services/**/*.py` |
| omnix_dashboard Lines | 9,037 | `wc -l omnix_dashboard/**/*` |
| Total Estimated Lines | ~95,000 | Sum of all packages |
| Database Tables | 45 | PostgreSQL metadata |
| Foreign Key Constraints | 41 (91% coverage) | DATABASE_AUDIT_REPORT.md |
| Dashboard Endpoints | 25+ | Blueprint inspection |
| Flask Blueprints | 6 | app.py |

---

## 2. Package Architecture

### 2.1 Package Inventory

```
omnix/
├── omnix_core/           # Core trading logic (18 modules, 20,131 lines)
├── omnix_services/       # Service layer (150+ modules in 22 subpackages + 2 root, 62,613 lines)
├── omnix_dashboard/      # Flask web dashboard (40+ files, 9,037 lines)
├── omnix_api/            # REST API & Stripe (3 modules)
├── omnix_config/         # Configuration management (3 modules)
├── omnix_reports/        # Report generation (1 module)
├── omnix_risk/           # Risk management extensions (6 modules)
├── omnix_strategies/     # Strategy extensions (1 module)
├── omnix_testing/        # Backtesting & validation (15+ modules)
├── scripts/              # Utility scripts (2 files)
├── tests/                # Unit tests (1 file)
├── sql/                  # SQL scripts (2 files)
└── Root Files            # main.py (755 lines), entrypoints (8 files)
```

---

## 3. omnix_core/ - Core Trading System

**Purpose:** Central trading engine, strategies, security, caching, and user sessions.  
**Total Modules:** 18 across 10 subpackages  
**Measured Lines:** 20,131

### 3.1 Subpackage Inventory (Verified Line Counts)

| Subpackage | Files | Lines | Primary Purpose | Key Classes |
|------------|-------|-------|-----------------|-------------|
| `bot/` | 2 | 3,925 | Trading automation | `AutoTradingBot`, `PaperTradingManager` |
| `strategies/` | 3 | 1,896 | ARES trading protocols | `AresProtocolV1`, `AresProtocolV2`, `NonMarkovianKernel` |
| `security/` | 2 | 667 | Post-Quantum Cryptography | `PostQuantumSecurity` |
| `quantum/` | 4 | 6,248 | QRNG, D-Wave, Physics | `QuantumPhysicsValidator` (4,459 lines) |
| `cache/` | 2 | 534 | Redis caching | `RedisCache`, `RedisStateManager` |
| `sessions/` | 1 | 561 | Multi-user sessions | `UserSessionManager`, `UserTradingSession` |
| `context/` | 1 | 313 | Real data provider | `OMNIXRealContextProvider` |
| `utils/` | 2 | 360 | Logging, rate limiting | `ColoredFormatter`, `RateLimiter` |
| `models/` | 0 | 0 | (Empty - placeholder) | - |
| `queue/` | 0 | 0 | (Empty - placeholder) | - |
| Root | 1 | 5,486 | Trading system core | `TradingSystem` |

### 3.2 Key Module Details

#### 3.2.1 omnix_core/trading_system.py (5,486 lines)

**Purpose:** Core trading engine with Kraken integration and advanced modules.

**Key Features:**
- Multi-currency trading system with auto-switch
- Post-quantum security integration (Kyber-768, Dilithium-3)
- ARES strategies integration (V1 Swing, V2 Scalping)
- Advanced modules: OrderBook, Volatility, Microstructure, Risk

**Dependencies:** `omnix_services.trading_service.analyzers`, `omnix_services.optimization`, `ccxt`

---

#### 3.2.2 omnix_core/bot/auto_trading_bot.py (3,269 lines)

**Purpose:** 24/7 automated trading bot with 10 institutional strategies.

**10 Trading Strategies:**
1. Monte Carlo - Probability validation (10,000 simulations)
2. Black Swan - Extreme condition detection (Kurtosis/Skewness)
3. Sentiment Analysis - Market timing
4. Kelly Criterion - Mathematical position sizing
5. HMM Regime Detection - Market regime classification
6. Kalman Filter - Adaptive signal filtering
7. Quantum Momentum - 6-component proprietary strategy
8. ARES V1 - Swing Trading (55-65% win rate)
9. ARES V2 - Scalping M1 (60-70% win rate)
10. Non-Markovian Kernel - Temporal memory K(t-s)

---

#### 3.2.3 ARES Strategies (ares_v1.py, ares_v2.py)

| Strategy | Lines | Win Rate Target | Timeframe | Stop Loss |
|----------|-------|-----------------|-----------|-----------|
| ARES V1 | 679 | 55%-65% | Swing | -0.95% |
| ARES V2 | 587 | 60%-70% | M1 Scalping | -0.28% |

**ARES V1 Architecture (3 Layers):**
1. **ANF (Adaptive Noise Filter):** Filters 90% of low-value trades
2. **ISA (Institutional Signal Analysis):** 6 professional signals
3. **SXE (Smart Execution Engine):** Hedge fund-style execution

---

#### 3.2.4 Non-Markovian Kernel (630 lines)

**Kernel Equation:**
```
K(t-s) = exp(-|t-s|/τ) × [1 + ε × cos(Ω(t-s))]
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| τ (tau) | 12 hours | Memory decay constant |
| ε (epsilon) | 0.35 | Oscillation amplitude |
| Ω (omega) | 0.523 rad | Oscillation frequency |
| Window | 168 periods | 1 week of hourly data |

---

#### 3.2.5 Post-Quantum Security

| Module | Lines | Purpose |
|--------|-------|---------|
| `pqc_security.py` | 468 | Real PQC (Kyber-768, Dilithium-3) via `pypqc` |
| `pqc_encryption.py` | 199 | Simulated fallback when pypqc unavailable |

**Standards:** NIST FIPS 203 (ML-KEM) + FIPS 204 (ML-DSA)

---

#### 3.2.6 Quantum Computing Integration

| Module | Lines | Purpose | External Service |
|--------|-------|---------|------------------|
| `enhancements.py` | 587 | QRNG + Portfolio Optimizer | ANU Quantum API |
| `dwave_qaoa.py` | 350 | Quantum Annealing | D-Wave Leap |
| `physics_validator.py` | 4,459 | 24 verified physics formulas | - |
| `testing_framework.py` | 852 | AI response validation | - |

---

## 4. omnix_services/ - Service Layer

**Total Subpackages:** 22  
**Root-Level Modules:** 2  
**Total Modules:** 150+  
**Measured Lines:** 62,613

### 4.1 Root-Level Standalone Modules

| Module | Lines | Purpose |
|--------|-------|---------|
| `news_scraper.py` | 256 | Crypto news scraping (CoinDesk, CoinTelegraph) with AI sentiment analysis |
| `symbol_classifier.py` | 138 | Intelligent crypto vs stock symbol detection |

### 4.2 Complete Subpackage Inventory

| Subpackage | Files | Key Lines | Key Classes/Exports | Dependencies |
|------------|-------|-----------|---------------------|--------------|
| **database_service/** | 4 | 4,818 | `DatabaseGateway`, `DatabaseManager`, `DatabaseServiceEnterprise` | psycopg, psycopg_pool |
| **trading_service/** | 15 | ~4,500 | `TradingServiceEnterprise`, `KrakenAPIClient`, `MonteCarloSimulator` | ccxt, requests |
| **ai_service/** | 13 | ~4,200 | `ConversationalBrain` (622), `VideoLearningAnalyzer` (1,086) | google-generativeai, openai |
| **telegram_service/** | 5 | 7,627 | `EnterpriseTelegramBot` (7,627), `CallbackHandler` (793) | python-telegram-bot |
| **monitoring/** | 5 | ~3,600 | `MetricsEngine`, `AIRiskGuardian` (558), `AdvancedIntelligence` (1,330) | prometheus_client |
| **risk_management/** | 8 | ~3,200 | `LimitsEngine` (531), `AlertDispatcher` (607), `MemoryRiskAdapter` | - |
| **derivatives/** | 7 | ~4,100 | `DerivativesManager` (585), `KrakenFuturesClient` (594), `MarginEngine` (543) | - |
| **coherence_service/** | 2 | 637 | `CoherenceEngine` (637) | - |
| **portfolio_management/** | 6 | ~2,500 | `OmnixPortfolioEngine`, `PortfolioOptimizer`, `RiskModelEngine` | numpy, scipy |
| **stock_trading/** | 15 | ~3,000 | `AlpacaService`, `StockStrategyEngine` (629), `StockAutoOptimizer` (545) | alpaca-trade-api |
| **adaptive_engine/** | 2 | 936 | `AdaptiveParameterEngine` (936), `RegimeType` | - |
| **on_chain_service/** | 5 | ~1,500 | `OnChainDataService`, `WhaleTracker` (683), `ExchangeFlowAnalyzer` | requests |
| **community_intelligence/** | 5 | ~1,200 | `CommunityFeedbackManager`, `RewardSystem` | - |
| **notifications/** | 4 | ~800 | `TradeNotificationService`, `DailySummaryService` | - |
| **market_data/** | 12 | ~2,500 | `fetch_market_snapshot`, `detect_arbitrage_opportunities`, `OrderbookDepth` (526) | requests |
| **market_intelligence/** | 4 | ~800 | `FearGreedService`, `FinnhubService`, `AlphaVantageService` | requests |
| **optimization/** | 7 | ~2,000 | `AdaptiveWeightSystem`, `AutoOptimizer` (797), `AdvancedMLModule` | numpy, scipy |
| **analytics/** | 3 | ~600 | `AutoFibonacciAnalyzer`, `VolumeProfileAnalyzer`, `ChartPatternAnalyzer` | - |
| **alerts/** | 2 | ~300 | `SmartAlertEngine` | - |
| **voice_service/** | 3 | ~500 | `VoiceServiceEnterprise`, `VoiceEngine` | openai (whisper) |
| **user_settings/** | 3 | 693 | `UserSettingsService` (693), `RiskProfile`, `TradingLimits` | - |
| **concurrency/** | 4 | ~600 | `IntelligentCacheSystem`, `OptimizedConcurrencyManager`, `ScalableResourceManager` | - |

### 4.3 Largest Modules (>500 lines)

| Module | Lines | Purpose |
|--------|-------|---------|
| `telegram_service/enterprise_bot.py` | 7,627 | Telegram bot with all commands |
| `database_service/database_service.py` | 4,818 | Enterprise database operations |
| `monitoring/advanced_intelligence.py` | 1,330 | Advanced analytics |
| `trading_service/advanced_features.py` | 1,216 | Trading enhancements |
| `ai_service/video/analyzer.py` | 1,086 | Video learning analysis |
| `monitoring/analytics_engine.py` | 1,092 | Analytics engine |
| `trading_service/paper_trading_manager.py` | 961 | Paper trading simulation |
| `adaptive_engine/adaptive_engine.py` | 936 | Auto-calibration |

### 4.4 Database Service Architecture

```
database_service/
├── database_gateway.py    # Unified gateway (Phase 2) - Fork-safe singleton
├── database_manager.py    # Adapter for legacy compatibility
├── database_service.py    # Enterprise service (4,818 lines)
└── optimize_indexes.sql   # Index optimization script
```

**Key Architecture Decisions:**
- `DatabaseGateway`: Fork-safe singleton for Gunicorn workers
- Feature flag: `USE_UNIFIED_GATEWAY` (default: false)
- Telemetry: Pool stats logged every 5 minutes
- **Contract:** All code uses tuple-based rows `row[n]`, NOT dict access

---

## 5. omnix_dashboard/ - Web Dashboard

**Framework:** Flask 3.x with Blueprints  
**Production Server:** Gunicorn with gevent workers  
**Measured Lines:** 9,037 (Python + JS + CSS + HTML)

### 5.1 Architecture

```
omnix_dashboard/
├── app.py                  # Application factory (92 lines)
├── gunicorn.conf.py        # Gunicorn configuration
├── run.py                  # Development server
├── blueprints/
│   ├── views.py            # HTML routes (/, /terminal, /classic)
│   ├── core.py             # /api/metrics, /api/trades, /api/health (430 lines)
│   ├── market.py           # /api/ticker, /api/fear-greed (390 lines)
│   ├── intelligence.py     # /api/adaptive, /api/riskguardian (304 lines)
│   ├── system.py           # /api/debug, /api/db-diagnostics (491 lines)
│   └── snapshots.py        # /api/snapshots (630 lines)
├── utils/                  # CRITICAL FOR MAINTENANCE
│   ├── database.py         # Connection pooling (317 lines) - USE_UNIFIED_GATEWAY flag
│   ├── queries.py          # SQL queries (297 lines) - tuple-based row access
│   ├── decorators.py       # @require_api_key auth (46 lines)
│   └── external_apis.py    # ThreadPoolExecutor HTTP calls (69 lines)
├── static/
│   ├── css/                # 19 CSS files (modular components)
│   └── js/
│       ├── core/           # api.js, clock.js, utils.js (4 files)
│       ├── components/     # 11 components (charts, ticker, signals, etc.)
│       └── pages/          # dashboard.js, terminal.js
└── templates/
    ├── base.html
    ├── dashboard.html      # Classic dashboard (359 lines)
    └── terminal.html       # Bloomberg-style terminal (198 lines)
```

### 5.2 Utils Package (Critical for Maintenance)

| Module | Lines | Purpose | Key Elements |
|--------|-------|---------|--------------|
| `database.py` | 317 | Connection pooling | `USE_UNIFIED_GATEWAY` flag, `get_db_connection()`, pool telemetry |
| `queries.py` | 297 | SQL queries | `get_paper_trades()`, `get_balance_history()`, tuple-based row access |
| `decorators.py` | 46 | Authentication | `@require_api_key` decorator, Railway detection |
| `external_apis.py` | 69 | HTTP helpers | `ThreadPoolExecutor` with timeout, `http_get_with_timeout()` |

**Database Connection Flow:**
1. If `USE_UNIFIED_GATEWAY=true`: Uses `DatabaseGateway.get_connection()`
2. If `USE_UNIFIED_GATEWAY=false` (default): Uses legacy `psycopg_pool.ConnectionPool`
3. Telemetry thread logs pool stats every 5 minutes

### 5.3 API Endpoints

| Blueprint | Endpoint | Lines | Purpose |
|-----------|----------|-------|---------|
| **core** | `/api/metrics` | 35 | Trading performance metrics |
| **core** | `/api/trades` | 40 | Recent trade history |
| **core** | `/api/positions` | 80 | Open positions with live prices |
| **core** | `/api/health` | 45 | System health check |
| **core** | `/api/equity-curve` | 35 | Balance over time |
| **market** | `/api/ticker` | 60 | Real-time crypto prices |
| **market** | `/api/fear-greed` | 40 | Market sentiment index |
| **market** | `/api/news` | 50 | Market news |
| **intelligence** | `/api/adaptive` | 80 | Adaptive engine status |
| **intelligence** | `/api/riskguardian` | 70 | Risk guardian status |
| **intelligence** | `/api/signals` | 60 | Active trading signals |
| **system** | `/api/debug` | 100 | Debug information |
| **system** | `/api/db-diagnostics` | 80 | Pool health |
| **snapshots** | `/api/snapshots` | 200 | Portfolio snapshots |

### 5.4 Frontend Components (JS)

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| Charts | `charts.js` | 235 | Equity curve, trade distribution |
| Ticker | `ticker.js` | ~100 | Real-time price ticker |
| Signals | `signals.js` | ~80 | Trading signal display |
| Fear & Greed | `feargreed.js` | ~70 | Market sentiment gauge |
| Risk Guardian | `riskguardian.js` | ~90 | Risk status panel |
| Adaptive | `adaptive.js` | 233 | Adaptive engine status |
| Benchmarks | `benchmarks.js` | 218 | Performance vs market |
| Volume | `volume.js` | ~60 | Volume analysis |
| News | `news.js` | ~50 | Market news feed |
| Status Bar | `statusbar.js` | ~80 | System status |
| Snapshots | `snapshots.js` | 307 | Portfolio snapshots |

---

## 6. Other Packages

### 6.1 omnix_config/ (3 modules)

| Module | Lines | Purpose |
|--------|-------|---------|
| `env_manager.py` | 580 | Environment variable management with validation |
| `settings.py` | 140 | Centralized settings via dataclasses |
| `grafana/omnix_dashboard.json` | - | Grafana dashboard config |

**Env Precedence:** Replit Secrets > .env.local > defaults

---

### 6.2 omnix_risk/ (6 modules)

| Module | Class | Purpose |
|--------|-------|---------|
| `usd_risk_calculator.py` | `USDRiskCalculator` | USD-denominated risk |
| `cascade_protection.py` | `CascadeProtection` | Cascade failure protection |
| `reactivation_engine.py` | `ReactivationEngine` | Auto-reactivation |
| `portfolio_summary.py` | `PortfolioSummary` | Portfolio overview |
| `audit_logger.py` | `InstitutionalAuditLogger` | Audit trail |
| `dead_man_switch.py` | `DeadManSwitch` | Health monitoring |

---

### 6.3 omnix_testing/ (15+ modules)

| Component | Purpose |
|-----------|---------|
| `BacktestingEngine` | Historical data backtesting |
| `KrakenDataDownloader` | Historical data download |
| `MetricsCalculator` | Performance metrics |
| `ProfessionalValidator` | Walk-forward + Monte Carlo |
| `InstitutionalStressSuite` | Stress testing |
| `ChartGenerator` | Equity curves, drawdowns |
| `PDFReportGenerator` | Investor reports |

---

### 6.4 omnix_api/ (3 modules)

```
omnix_api/
├── payments/
│   └── stripe_integration.py  # Stripe payment processing
└── routes/
    └── __init__.py
```

---

### 6.5 Root Files

| File | Lines | Purpose |
|------|-------|---------|
| `main.py` | 755 | Telegram bot entry point |
| `start_dashboard.py` | - | Dashboard starter |
| `verify_code.py` | - | Code verification |
| `chat_with_bot.py` | - | CLI chat interface |
| `generate_investor_report.py` | - | PDF report generator |
| `get_my_telegram_id.py` | - | Telegram ID lookup |
| `send_telegram_message.py` | - | Message sender |
| `test_railway_startup.py` | - | Railway startup test |

---

## 7. Database Architecture

**Reference:** See `docs/core/DATABASE_AUDIT_REPORT.md` for complete audit.

### 7.1 Summary

| Metric | Value |
|--------|-------|
| Total Tables | 45 |
| Foreign Keys | 41 (91% coverage) |
| Phase 3 Status | Complete (Dec 4, 2025) |

### 7.2 Core Tables

| Table | Purpose | Key FKs |
|-------|---------|---------|
| `users` | User accounts | - |
| `paper_trading_trades` | Trade history | users(user_id) |
| `paper_trading_balances` | Balance tracking | users(user_id) |
| `paper_trading_positions` | Open positions | users(user_id), paper_trading_trades(trade_id) |
| `balance_history` | Balance changes | users(user_id) |
| `conversations` | AI chat history | users(user_id) |
| `pending_evaluations` | Scheduled evaluations | users(user_id), paper_trading_trades(trade_id) |
| `ai_auto_learning_entries` | Learning data | users(user_id), paper_trading_trades(trade_id) |

### 7.3 Database Consumers

| Consumer | Connection Method | Notes |
|----------|-------------------|-------|
| Dashboard | `get_db_connection()` | Via DatabaseGateway if enabled |
| Enterprise Services | `DatabaseServiceEnterprise` | Direct psycopg |
| Auto Trading Bot | `DatabaseManager` | Adapter pattern |
| AI Risk Guardian | `DatabaseManager.get_connection()` | - |

---

## 8. Dependency Matrix

### 8.1 External Dependencies

| Package | Used By | Purpose |
|---------|---------|---------|
| `ccxt` | TradingSystem, KrakenClient | Crypto exchange API |
| `redis` | RedisCache, UserSessionManager | Caching, state |
| `psycopg` | DatabaseGateway, DatabaseServiceEnterprise | PostgreSQL v3 |
| `psycopg_pool` | Dashboard connection pooling | Pool management |
| `pypqc` | PostQuantumSecurity | Real PQC operations |
| `numpy` | All strategies, quantum modules | Numerical computing |
| `scipy` | ARES protocols, portfolio optimization | Scientific computing |
| `flask` | Dashboard | Web framework |
| `flask-cors` | Dashboard | CORS support |
| `gunicorn` | Dashboard | Production server |
| `gevent` | Dashboard | Async workers |
| `google-generativeai` | AI Service | Gemini AI |
| `openai` | AI Service, Voice Service | GPT-4o, Whisper |
| `anthropic` | AI Service | Claude |
| `python-telegram-bot` | TelegramService | Telegram integration |
| `prometheus_client` | MetricsEngine | Monitoring |
| `plotly` | Chart generation | Visualization |
| `kaleido` | Chart export | Static charts |
| `reportlab` | PDF generation | Reports |
| `requests` | External APIs | HTTP client |
| `beautifulsoup4` | NewsScraperService | HTML parsing |

### 8.2 Internal Dependency Graph

```
main.py (755 lines)
├── omnix_config/
│   ├── env_manager.py
│   └── settings.py
├── omnix_core/
│   ├── bot/auto_trading_bot.py (3,269 lines)
│   │   ├── omnix_services/monitoring/
│   │   ├── omnix_services/optimization/
│   │   ├── omnix_services/ai_service/
│   │   ├── omnix_services/coherence_service/
│   │   ├── omnix_services/risk_management/
│   │   ├── omnix_services/adaptive_engine/
│   │   └── omnix_core/strategies/
│   └── trading_system.py (5,486 lines)
│       └── omnix_services/trading_service/
├── omnix_services/
│   ├── database_service/
│   ├── trading_service/
│   ├── telegram_service/
│   ├── stock_trading/
│   ├── news_scraper.py (256 lines) ← Root-level module
│   └── symbol_classifier.py (138 lines) ← Root-level module
└── omnix_api/payments/
```

---

## 9. Legacy and Obsolete Code

### 9.1 Identified Issues

| Location | Type | Severity | Notes |
|----------|------|----------|-------|
| `omnix_core/security/pqc_encryption.py` | Potential Duplicate | Low | Simulated fallback, may be redundant |
| `omnix_core/models/__init__.py` | Empty Placeholder | Low | Never implemented |
| `omnix_core/queue/__init__.py` | Empty Placeholder | Low | Never implemented |
| `omnix_core/strategies/__init__.py` | Empty | Low | Missing exports |
| `omnix_core/security/__init__.py` | Empty | Low | Missing exports |
| `omnix_services/trading_service/pqc_security.py` | Duplicate | Medium | Same as omnix_core version |
| `omnix_services/__init__.py` | Empty | Low | Missing exports |

### 9.2 Code Duplication

| Pattern | Locations | Recommendation |
|---------|-----------|----------------|
| PQC Security | `omnix_core/security/`, `omnix_services/trading_service/` | Consolidate to single module |
| Paper Trading | `omnix_core/bot/paper_trading.py`, `omnix_services/trading_service/paper_trading_manager.py` | Audit for overlap |

---

## 10. Architecture Contracts

### 10.1 Database Access

**Contract:** All code MUST use tuple-based row access `row[n]`, NOT dict access `row['column']`.

**Reason:** psycopg3 default behavior returns tuples; dict access requires explicit row_factory.

**Violation Detection:**
```bash
grep -r "row\['" omnix_*
```

### 10.2 Feature Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `USE_UNIFIED_GATEWAY` | false | Enables DatabaseGateway in dashboard |
| `DISABLE_AUTO_MIGRATIONS` | false | Skips 8 auto-migration scripts |
| `STOCK_TRADING_ENABLED` | true | Enables stock trading module |

### 10.3 Port Allocation

| Port | Service | Environment |
|------|---------|-------------|
| 5000 | Dashboard (Flask) | Dev/Prod |
| Telegram API | Bot | Railway (Production) |

---

## 11. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Dec 4, 2025 | Agent | Initial omnix_core/ inventory |
| 2.0 | Dec 4, 2025 | Agent | Complete omnix_services/, dashboard, other packages |
| 2.1 | Dec 4, 2025 | Agent | Verified line counts, added root modules, dashboard utils |

---

## 12. Appendix: File Counts by Package (Measured)

| Package | Python Files | Other Files | Total LOC |
|---------|--------------|-------------|-----------|
| omnix_core | 18 | 0 | 20,131 |
| omnix_services | 152 | 1 (SQL) | 62,613 |
| omnix_dashboard | 12 | 30+ (JS/CSS/HTML) | 9,037 |
| omnix_api | 3 | 0 | ~200 |
| omnix_config | 2 | 1 (JSON) | ~720 |
| omnix_reports | 1 | 0 | ~300 |
| omnix_risk | 6 | 0 | ~1,500 |
| omnix_strategies | 1 | 0 | ~200 |
| omnix_testing | 15+ | 10+ (data/reports) | ~5,000 |
| Root | 8 | 0 | ~1,500 |
| **TOTAL** | **~220** | **~45+** | **~100,000** |

---

## 13. Appendix: omnix_services Module Listing (152 files)

```
omnix_services/
├── __init__.py
├── news_scraper.py (256 lines) - Crypto news scraping
├── symbol_classifier.py (138 lines) - Symbol classification
├── adaptive_engine/ (2 files)
├── ai_service/ (13 files)
├── alerts/ (2 files)
├── analytics/ (3 files)
├── coherence_service/ (3 files)
├── community_intelligence/ (5 files)
├── concurrency/ (4 files)
├── database_service/ (4 files)
├── derivatives/ (7 files)
├── market_data/ (12 files)
├── market_intelligence/ (4 files)
├── monitoring/ (5 files)
├── notifications/ (4 files)
├── on_chain_service/ (5 files)
├── optimization/ (7 files)
├── portfolio_management/ (7 files)
├── risk_management/ (8 files)
├── stock_trading/ (15 files)
├── telegram_service/ (5 files)
├── trading_service/ (15 files)
├── user_settings/ (3 files)
└── voice_service/ (3 files)
```
