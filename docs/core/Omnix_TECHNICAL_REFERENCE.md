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

#### 8.1.1 Dependency Inventory (Complete from requirements.txt)

**Core Trading & Math:**

| Package | Version | Used By | Purpose |
|---------|---------|---------|---------|
| `numpy` | 1.26.4 | All strategies, quantum modules | Numerical computing |
| `scipy` | 1.12.0 | ARES protocols, portfolio optimization | Scientific computing |
| `ccxt` | 4.5.1 | TradingSystem, KrakenClient | Crypto exchange API (Kraken) |
| `pandas` | 2.2.0 | Backtesting, analytics | Data analysis |

**AI & ML:**

| Package | Version | Used By | Purpose |
|---------|---------|---------|---------|
| `google-generativeai` | 0.8.5 | AI Service | Gemini AI (⚠️ DEPRECATED Aug 2025) |
| `openai` | 1.101.0 | AI Service, Voice Service | GPT-4o, Whisper |
| `anthropic` | (missing) | AI Service | Claude (needs to be added) |

**Voice & Media:**

| Package | Version | Used By | Purpose |
|---------|---------|---------|---------|
| `gTTS` | 2.5.4 | Voice Service | Google Text-to-Speech |
| `youtube-transcript-api` | 0.6.1 | Video Learning Analyzer | YouTube transcripts |
| `yt-dlp` | >=2024.1.0 | Video Learning Analyzer | Video downloads |

**Web Framework & Servers:**

| Package | Version | Used By | Purpose |
|---------|---------|---------|---------|
| `Flask` | 3.1.2 | Dashboard | Web framework |
| `flask-cors` | (unpinned) | Dashboard | CORS support |
| `gunicorn` | 23.0.0 | Dashboard | Production server (Railway) |
| `gevent` | >=24.2.1 | Dashboard | Async workers |
| `waitress` | 3.0.2 | Dashboard | Alternative WSGI server |
| `fastapi` | 0.109.0 | API endpoints | Async API framework |
| `uvicorn` | 0.27.0 | FastAPI | ASGI server |

**Database:**

| Package | Version | Used By | Purpose |
|---------|---------|---------|---------|
| `psycopg[binary,pool]` | >=3.1.0 | DatabaseGateway, DatabaseServiceEnterprise | PostgreSQL v3 driver |
| `redis` | 5.0.1 | RedisCache, UserSessionManager | Caching, state |

**Telegram:**

| Package | Version | Used By | Purpose |
|---------|---------|---------|---------|
| `python-telegram-bot` | 20.7 | TelegramService | Main Telegram integration |
| `telegram` | (unpinned) | Legacy/utils | Telegram utilities |

**HTTP & Async:**

| Package | Version | Used By | Purpose |
|---------|---------|---------|---------|
| `requests` | 2.32.5 | External APIs | Sync HTTP client |
| `aiohttp` | >=3.9.0 | Async services | Async HTTP client |
| `httpx` | >=0.25.0,<1.0.0 | AI services | Modern HTTP client |
| `websockets` | 12.0 | Real-time feeds | WebSocket support |

**Security:**

| Package | Version | Used By | Purpose |
|---------|---------|---------|---------|
| `pypqc` | (unpinned) | PostQuantumSecurity | Kyber-768, Dilithium-3 |

**Visualization & Reports:**

| Package | Version | Used By | Purpose |
|---------|---------|---------|---------|
| `plotly` | 5.24.1 | Chart generation | Interactive charts |
| `kaleido` | 0.2.1 | Chart export | Static image export |
| `matplotlib` | 3.9.3 | Testing/backtesting | Static charts |
| `seaborn` | 0.13.2 | Analytics | Statistical plots |
| `reportlab` | 4.2.5 | PDF generation | Investor reports |
| `PyPDF2` | 3.0.1 | PDF manipulation | PDF utilities |

**Data Storage:**

| Package | Version | Used By | Purpose |
|---------|---------|---------|---------|
| `tables` | 3.9.2 | Backtesting | HDF5 storage |
| `pyarrow` | 18.1.0 | Data processing | Parquet/Arrow format |

**Utilities:**

| Package | Version | Used By | Purpose |
|---------|---------|---------|---------|
| `python-dotenv` | 1.0.0 | Config | Environment loading |
| `python-decouple` | 3.8 | Config | Settings management |
| `pillow` | 10.2.0 | Image processing | Image utilities |
| `pytz` | 2024.1 | Time handling | Timezone support |
| `tqdm` | 4.67.1 | Progress bars | CLI progress |
| `beautifulsoup4` | 4.12.3 | NewsScraperService | HTML parsing |
| `prometheus-client` | 0.20.0 | MetricsEngine | Monitoring |

**External Services:**

| Package | Version | Used By | Purpose |
|---------|---------|---------|---------|
| `stripe` | 5.0.0 | Payments | Payment processing |
| `alpaca-trade-api` | (unpinned) | Stock Trading Service | Alpaca API |
| `dwave-ocean-sdk` | (unpinned) | Quantum optimization | D-Wave integration |

#### 8.1.2 Compatibility Prerequisites (CRITICAL)

**⚠️ MUST VERIFY BEFORE ANY UPDATES:**

| Prerequisite | Required | Reason | Verification |
|--------------|----------|--------|--------------|
| **Python Version** | ≥3.10 | Flask 3.1.x (≥3.9) + scipy 1.14.1 (≥3.10) | `python --version` on Railway |
| **httpx Version** | ~=0.27 | python-telegram-bot 21.9 requires exactly 0.27.x | Pin in requirements.txt |

**Railway Python Version Check:**
```bash
# SSH to Railway or check build logs
python --version
# Must show Python 3.10.x or higher
```

**httpx Conflict Resolution:**
```txt
# CURRENT (INCOMPATIBLE with PTB 21.9):
httpx>=0.25.0,<1.0.0

# REQUIRED (for python-telegram-bot 21.9):
httpx~=0.27.2
```

**Compatibility Matrix (Validated via Internet Research Dec 4, 2025):**

| Package Proposed | Compatible With | Conflicts | Resolution |
|------------------|-----------------|-----------|------------|
| psycopg 3.3.1 | Flask 3.1.2, gunicorn 23.0.0 | None | ✅ Safe |
| scipy 1.14.1 | numpy 1.26.4 | Python 3.9 | Requires Python 3.10+ |
| pandas 2.2.3 | plotly 5.24.1, numpy 1.26.4 | None | ✅ Safe |
| pypqc 0.0.6.2 | All (uses stable ABI cp37-abi3) | None | ✅ Safe |
| ccxt 4.5.24+ | requests 2.32.5 | None | ✅ Safe |
| anthropic 0.75.0 | httpx 0.27.x | None | ✅ Safe |
| python-telegram-bot 21.9 | Python 3.10+ | **httpx constraint** | Change to ~=0.27 |

**Anchor Packages (Already Updated - Must Remain Compatible):**

| Package | Version | Python Min | Status |
|---------|---------|------------|--------|
| Flask | 3.1.2 | 3.9 | ✅ Anchor |
| gunicorn | 23.0.0 | 3.7 | ✅ Anchor |
| plotly | 5.24.1 | 3.8 | ✅ Anchor |
| requests | 2.32.5 | 3.8 | ✅ Anchor |

#### 8.1.3 Version Matrix (Audited December 4, 2025)

**Packages Requiring Updates:**

| Package | Current | Latest Stable | Proposed | Risk Level |
|---------|---------|---------------|----------|------------|
| `psycopg[binary,pool]` | >=3.1.0 | 3.3.1 | ==3.3.1 | 🟢 LOW |
| `pandas` | 2.2.0 | 2.2.3 | ==2.2.3 | 🟢 LOW |
| `pypqc` | (unpinned) | 0.0.6.2 | ==0.0.6.2 | 🟢 LOW |
| `scipy` | 1.12.0 | 1.14.1 | ==1.14.1 | 🟢 LOW |
| `ccxt` | 4.5.1 | 4.5.24+ | >=4.5.24 | 🟡 MEDIUM |
| `python-telegram-bot` | 20.7 | 22.5 | ==21.9 | 🟡 MEDIUM |
| `anthropic` | (missing) | 0.75.0 | ==0.75.0 | 🟡 MEDIUM |

**Packages to Keep Current (Stable):**

| Package | Current | Latest Stable | Status |
|---------|---------|---------------|--------|
| `openai` | 1.101.0 | 2.x | ✅ KEEP 1.101.0 (v2 breaking) |
| `Flask` | 3.1.2 | 3.1.x | ✅ CURRENT |
| `gunicorn` | 23.0.0 | 23.0.0 | ✅ CURRENT |
| `plotly` | 5.24.1 | 5.24.1 | ✅ CURRENT |
| `requests` | 2.32.5 | 2.32.5 | ✅ CURRENT |

**High-Risk Packages (Do NOT Update):**

| Package | Current | Latest | Risk | Reason |
|---------|---------|--------|------|--------|
| `numpy` | 1.26.4 | 2.2.0 | 🔴 HIGH | ABI breaking changes |
| `redis` | 5.0.1 | 7.1.0 | 🔴 HIGH | Drops Python 3.9 |
| `kaleido` | 0.2.1 | 1.2.0 | 🔴 HIGH | Requires external Chrome |
| `google-generativeai` | 0.8.5 | DEPRECATED | 🔴 HIGH | End of life Aug 2025 |

#### 8.1.4 Risk Analysis and Compatibility Notes

**🟢 LOW RISK - Safe to Update:**

| Package | Notes |
|---------|-------|
| `psycopg 3.3.1` | Minor version bump, maintains psycopg3 tuple-based API. Requires Python 3.10+. |
| `pandas 2.2.3` | Bug fixes only, compatible with numpy 1.26.x and 2.x. |
| `pypqc 0.0.6.2` | **SECURITY PATCH** - Fixes KyberSlash vulnerability (private key timing attack). Drop-in replacement. |
| `scipy 1.14.1` | Compatible with numpy 1.26.x. First version with Python 3.13 support. |

**🟡 MEDIUM RISK - Requires Testing:**

| Package | Notes |
|---------|-------|
| `ccxt 4.5.24+` | Active development. Must verify Kraken API compatibility. Added `orjson` optional for performance. |
| `python-telegram-bot 21.9` | **DO NOT UPGRADE TO v22+** - v22 has breaking changes with modular dependencies. v21.9 is last stable before breaking changes. |
| `anthropic 0.75.0` | **MISSING FROM requirements.txt** but used in code. Must add for Claude support. |

**Note on OpenAI:** Current version 1.101.0 is stable and should be kept. Do NOT upgrade to v2.x which has breaking API changes.

**🔴 HIGH RISK - Do Not Update:**

| Package | Current | Latest | Reason |
|---------|---------|--------|--------|
| `numpy` | 1.26.4 | 2.2.0 | **ABI BREAKING CHANGES** - NumPy 2.0 breaks binary compatibility with scipy, pandas, and many compiled extensions. |
| `redis` | 5.0.1 | 7.1.0 | **DROPS PYTHON 3.9 SUPPORT** - v7.1 requires Python 3.10+. Must verify Railway Python version first. |
| `kaleido` | 0.2.1 | 1.2.0 | **BREAKING CHANGES** - v1.0+ no longer bundles Chrome, requires external Chrome installation. Not suitable for Railway. |
| `google-generativeai` | 0.8.5 | DEPRECATED | **END OF LIFE: AUGUST 31, 2025** - Must migrate to `google-genai` SDK before deprecation. Requires code changes. |

#### 8.1.5 Deprecation Warnings

**⚠️ CRITICAL: Google Generative AI SDK Deprecation**

| Item | Details |
|------|---------|
| Package | `google-generativeai` |
| Deprecation Date | August 31, 2025 |
| Replacement | `google-genai` (new unified SDK) |
| Migration Guide | https://ai.google.dev/gemini-api/docs/migrate |
| Impact | `omnix_services/ai_service/` requires code refactoring |
| Action | Plan migration in dedicated iteration before Aug 2025 |

**New SDK Example:**
```python
# OLD (deprecated)
import google.generativeai as genai
genai.configure(api_key="...")
model = genai.GenerativeModel('gemini-2.0-flash')

# NEW (google-genai)
from google import genai
client = genai.Client(api_key="...")
response = client.models.generate_content(model='gemini-2.0-flash', contents='...')
```

#### 8.1.6 Security Patches

| Package | Version | CVE/Advisory | Description |
|---------|---------|--------------|-------------|
| `pypqc` | 0.0.6.2 | KyberSlash (GMS-2024-382) | Private key recovery via timing attack. Fixed Jan 26, 2024. |

#### 8.1.7 Python Version Compatibility

| Package | Python 3.9 | Python 3.10 | Python 3.11 | Python 3.12 | Python 3.13 |
|---------|------------|-------------|-------------|-------------|-------------|
| psycopg 3.3.x | ❌ | ✅ | ✅ | ✅ | ✅ |
| redis 5.0.x | ✅ | ✅ | ✅ | ✅ | ❌ |
| redis 7.1.x | ❌ | ✅ | ✅ | ✅ | ✅ |
| numpy 1.26.x | ✅ | ✅ | ✅ | ✅ | ❌ |
| numpy 2.2.x | ❌ | ✅ | ✅ | ✅ | ✅ |
| scipy 1.14.x | ❌ | ✅ | ✅ | ✅ | ✅ |
| pandas 2.2.x | ✅ | ✅ | ✅ | ✅ | ✅ |
| python-telegram-bot 21.x | ✅ | ✅ | ✅ | ✅ | ✅ |
| python-telegram-bot 22.x | ❌ | ✅ | ✅ | ✅ | ✅ |

**Railway Production:** Verify Python version before updating redis or psycopg.

#### 8.1.8 Dependency Update Plan

**Phase A: Low Risk (Immediate)**
```
psycopg[binary,pool]==3.3.1
pandas==2.2.3
scipy==1.14.1
pypqc==0.0.6.2
```

**Phase B: Medium Risk (With Testing)**
```
# PREREQUISITE: Change httpx constraint FIRST
httpx~=0.27.2  # Required for python-telegram-bot 21.9

ccxt>=4.5.24
python-telegram-bot==21.9
anthropic==0.75.0
```

**Phase C: Cleanup**
- Remove duplicate entries in requirements.txt (gevent, psycopg appear twice)
- Pin all unpinned dependencies

**Phase D: Deferred (Requires Code Changes)**
- Migrate `google-generativeai` → `google-genai` (before Aug 2025)
- Evaluate NumPy 2.0 migration when ecosystem stabilizes

#### 8.1.9 requirements.txt Issues

| Issue | Location | Fix |
|-------|----------|-----|
| Duplicate `gevent` | Lines 18, 76 | Remove line 76 |
| Duplicate `psycopg[binary,pool]` | Lines 26-27, 77 | Remove line 77 |
| Missing `anthropic` | - | Add `anthropic==0.75.0` |
| Unpinned `pypqc` | Line 43 | Pin to `==0.0.6.2` |
| Unpinned `alpaca-trade-api` | Line 61 | Pin to specific version |
| Unpinned `flask-cors` | Line 75 | Pin to specific version |
| Unpinned `dwave-ocean-sdk` | Line 74 | Pin to specific version |
| **httpx constraint** | Line 47 | Change `>=0.25.0,<1.0.0` to `~=0.27.2` |

#### 8.1.10 Railway Deployment Verification

**Pre-Update Checklist:**

| Step | Command/Action | Expected Result |
|------|----------------|-----------------|
| 1. Check Python Version | `python --version` in Railway logs | Python 3.10.x or higher |
| 2. Verify current packages | `pip freeze` | Baseline versions noted |
| 3. Backup database | Railway dashboard | Checkpoint created |

**Post-Update Validation:**

```bash
# Railway deployment test sequence
1. Deploy to Railway (push to main)
2. Check build logs for pip install errors
3. Verify bot startup: "OMNIX V6.5.2 INSTITUTIONAL+ iniciado"
4. Test Telegram connection: /status command
5. Test Dashboard: /api/health endpoint
6. Verify database: /api/db-diagnostics endpoint
7. Monitor for 1 hour before marking stable
```

**Rollback Procedure:**
```bash
# If errors occur, revert to previous requirements.txt
git revert HEAD
git push origin main
# Railway will auto-deploy previous version
```

**Python Version Control in Railway:**

Railway determines Python version from these files (in order of precedence):
1. `runtime.txt` - e.g., `python-3.11.7`
2. `.python-version` - e.g., `3.11.7`
3. `Pipfile` - python_version field
4. Default: Latest stable Python

**Recommended: Create `runtime.txt`:**
```txt
python-3.11.7
```

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
| 2.2 | Dec 4, 2025 | Agent | **Major update to Section 8.1**: Complete dependency audit with version matrix, risk analysis, compatibility notes, deprecation warnings (google-generativeai), security patches (pypqc KyberSlash), Python version compatibility table, and phased update plan |

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
