# OMNIX V6.5.2 INSTITUTIONAL+ - Technical Reference

**Document Version:** 2.0  
**Created:** December 4, 2025  
**Last Updated:** December 4, 2025  
**Status:** ✅ COMPLETE (Auditoría Técnica Fase 1B)

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

### 1.2 Codebase Statistics

| Metric | Count |
|--------|-------|
| Total Python Packages | 10 |
| Total Python Modules | ~180+ |
| Total Lines of Code | ~100,000+ |
| Database Tables | 45 |
| Foreign Key Constraints | 41 (91% coverage) |
| Dashboard Endpoints | 25+ |
| Flask Blueprints | 6 |
| JS Components | 11 |

---

## 2. Package Architecture

### 2.1 Package Inventory

```
omnix/
├── omnix_core/           # Core trading logic (18 modules, ~15,000 lines)
├── omnix_services/       # Service layer (90+ modules in 22 subpackages, ~60,000 lines)
├── omnix_dashboard/      # Flask web dashboard (40+ files, ~8,000 lines)
├── omnix_api/            # REST API & Stripe (3 modules)
├── omnix_config/         # Configuration management (3 modules, ~850 lines)
├── omnix_reports/        # Report generation (1 module)
├── omnix_risk/           # Risk management extensions (6 modules)
├── omnix_strategies/     # Strategy extensions (1 module)
├── omnix_testing/        # Backtesting & validation (15+ modules)
├── scripts/              # Utility scripts (2 files)
├── tests/                # Unit tests (1 file)
├── sql/                  # SQL scripts (2 files)
└── Root Files            # main.py, entrypoints (8 files, ~1,500 lines)
```

---

## 3. omnix_core/ - Core Trading System

**Purpose:** Central trading engine, strategies, security, caching, and user sessions.  
**Total Modules:** 18 across 10 subpackages  
**Lines of Code:** ~15,000

### 3.1 Subpackage Inventory

| Subpackage | Files | LOC | Primary Purpose | Key Classes |
|------------|-------|-----|-----------------|-------------|
| `bot/` | 2 | ~4,000 | Trading automation | `AutoTradingBot`, `PaperTradingManager` |
| `strategies/` | 3 | ~1,900 | ARES trading protocols | `AresProtocolV1`, `AresProtocolV2`, `NonMarkovianKernel` |
| `security/` | 2 | ~670 | Post-Quantum Cryptography | `PostQuantumSecurity` |
| `quantum/` | 4 | ~6,250 | QRNG, D-Wave, Physics | `QuantumRandomNumberGenerator`, `DWavePortfolioOptimizer`, `QuantumPhysicsValidator` |
| `cache/` | 2 | ~540 | Redis caching | `RedisCache`, `RedisStateManager` |
| `sessions/` | 1 | ~560 | Multi-user sessions | `UserSessionManager`, `UserTradingSession` |
| `context/` | 1 | ~315 | Real data provider | `OMNIXRealContextProvider` |
| `utils/` | 2 | ~360 | Logging, rate limiting | `ColoredFormatter`, `RateLimiter` |
| `models/` | 0 | 0 | (Empty - placeholder) | - |
| `queue/` | 0 | 0 | (Empty - placeholder) | - |
| Root | 1 | ~5,500 | Trading system core | `TradingSystem` |

### 3.2 Key Module Details

#### 3.2.1 omnix_core/trading_system.py (5,487 lines)

**Purpose:** Core trading engine with Kraken integration and advanced modules.

**Key Features:**
- Multi-currency trading system with auto-switch
- Post-quantum security integration (Kyber-768, Dilithium-3)
- ARES strategies integration (V1 Swing, V2 Scalping)
- Advanced modules: OrderBook, Volatility, Microstructure, Risk

**Dependencies:** `omnix_services.trading_service.analyzers`, `omnix_services.optimization`, `ccxt`

---

#### 3.2.2 omnix_core/bot/auto_trading_bot.py (3,270 lines)

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
| ARES V1 | 680 | 55%-65% | Swing | -0.95% |
| ARES V2 | 588 | 60%-70% | M1 Scalping | -0.28% |

**ARES V1 Architecture (3 Layers):**
1. **ANF (Adaptive Noise Filter):** Filters 90% of low-value trades
2. **ISA (Institutional Signal Analysis):** 6 professional signals
3. **SXE (Smart Execution Engine):** Hedge fund-style execution

---

#### 3.2.4 Non-Markovian Kernel (631 lines)

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
| `pqc_security.py` | 469 | Real PQC (Kyber-768, Dilithium-3) via `pypqc` |
| `pqc_encryption.py` | 200 | Simulated fallback when pypqc unavailable |

**Standards:** NIST FIPS 203 (ML-KEM) + FIPS 204 (ML-DSA)

---

#### 3.2.6 Quantum Computing Integration

| Module | Lines | Purpose | External Service |
|--------|-------|---------|------------------|
| `enhancements.py` | 588 | QRNG + Portfolio Optimizer | ANU Quantum API |
| `dwave_qaoa.py` | 351 | Quantum Annealing | D-Wave Leap |
| `physics_validator.py` | 4,460 | 24 verified physics formulas | - |
| `testing_framework.py` | 853 | AI response validation | - |

---

## 4. omnix_services/ - Service Layer

**Total Subpackages:** 22  
**Total Modules:** 90+  
**Lines of Code:** ~60,000

### 4.1 Complete Subpackage Inventory

| Subpackage | Files | Key Classes/Exports | Dependencies |
|------------|-------|---------------------|--------------|
| **database_service/** | 4 | `DatabaseGateway`, `DatabaseManager`, `DatabaseServiceEnterprise` | psycopg, psycopg_pool |
| **trading_service/** | 15 | `TradingServiceEnterprise`, `KrakenAPIClient`, `MonteCarloSimulator`, `BlackSwanDetector` | ccxt, requests |
| **ai_service/** | 9 | `ConversationalAIService`, `ConversationalBrain`, `AIModelsManager`, `VideoLearningAnalyzer` | google-generativeai, openai, anthropic |
| **monitoring/** | 5 | `MetricsEngine`, `AIRiskGuardian`, `AdvancedPerformanceTracker` | prometheus_client |
| **risk_management/** | 7 | `LimitsEngine`, `CircuitBreaker`, `PositionMonitor`, `AlertDispatcher`, `MemoryRiskAdapter` | - |
| **coherence_service/** | 2 | `CoherenceEngine`, `CoherenceReport` | - |
| **portfolio_management/** | 6 | `OmnixPortfolioEngine`, `PortfolioOptimizer`, `VolatilityTargetingEngine`, `RiskModelEngine` | numpy, scipy |
| **derivatives/** | 7 | `DerivativesManager`, `KrakenFuturesClient`, `MarginEngine`, `HedgingService` | - |
| **stock_trading/** | 10 | `AlpacaService`, `StockAnalyzer`, `StockStrategyEngine` | alpaca-trade-api |
| **adaptive_engine/** | 1 | `AdaptiveParameterEngine`, `RegimeType` | - |
| **on_chain_service/** | 5 | `OnChainDataService`, `WhaleTracker`, `ExchangeFlowAnalyzer` | requests |
| **community_intelligence/** | 5 | `CommunityFeedbackManager`, `CommunityAnalyzer`, `RewardSystem` | - |
| **telegram_service/** | 4 | `EnterpriseTelegramBot`, `CallbackHandler` | python-telegram-bot |
| **notifications/** | 3 | `TradeNotificationService`, `DailySummaryService` | - |
| **market_data/** | 10 | `fetch_market_snapshot`, `get_fear_greed_index`, `detect_arbitrage_opportunities` | requests |
| **market_intelligence/** | 3 | `FearGreedService`, `FinnhubService`, `AlphaVantageService` | requests |
| **optimization/** | 6 | `AdaptiveWeightSystem`, `AutoLearningSystem`, `GeneticOptimizer`, `AdvancedMLModule` | numpy, scipy |
| **analytics/** | 3 | `AutoFibonacciAnalyzer`, `VolumeProfileAnalyzer`, `ChartPatternAnalyzer` | - |
| **alerts/** | 1 | `SmartAlertEngine` | - |
| **voice_service/** | 2 | `VoiceServiceEnterprise`, `VoiceEngine` | openai (whisper) |
| **user_settings/** | 2 | `UserSettingsService`, `RiskProfile`, `TradingLimits` | - |
| **concurrency/** | 3 | `IntelligentCacheSystem`, `OptimizedConcurrencyManager`, `ScalableResourceManager` | - |

### 4.2 Database Service Architecture

```
database_service/
├── database_gateway.py    # Unified gateway (Phase 2) - Fork-safe singleton
├── database_manager.py    # Adapter for legacy compatibility
├── database_service.py    # Enterprise service (4,819 lines)
└── optimize_indexes.sql   # Index optimization script
```

**Key Architecture Decisions:**
- `DatabaseGateway`: Fork-safe singleton for Gunicorn workers
- Feature flag: `USE_UNIFIED_GATEWAY` (default: false)
- Telemetry: Pool stats logged every 5 minutes
- Contract: All code uses tuple-based rows `row[n]`, NOT dict access

---

### 4.3 Trading Service Stack

```
trading_service/
├── trading_service.py     # Orchestrator (438 lines)
├── kraken_client.py       # Thread-safe nonce, rate limiting (295 lines)
├── monte_carlo.py         # 10,000 simulations
├── black_swan.py          # Kurtosis/Skewness detection
├── hmm_regime.py          # Hidden Markov Model
├── kalman_filter.py       # Adaptive filtering
├── kelly_criterion.py     # Position sizing
├── quantum_momentum.py    # 6-component strategy
├── pqc_security.py        # Post-quantum (duplicate of core)
├── backtesting_engine.py  # Historical testing
├── paper_trading_manager.py
└── analyzers/
    ├── orderbook.py
    ├── volatility.py
    └── microstructure.py
```

---

### 4.4 AI Service Architecture

```
ai_service/
├── ai_service.py              # Main service
├── conversational_brain.py    # "Bot que piensa en voz alta" (623 lines)
├── ai_models.py               # Model management
├── ai_prompts.py              # Context management
├── ai_styles.py               # Visual styles
├── conversational_ai_adapter.py
├── formatters/
│   └── institutional_formatter.py
└── video/
    ├── analyzer.py
    ├── integration.py
    └── learning_analyzer.py
```

**AI Model Priority:**
1. Gemini 2.0 Flash (Primary)
2. GPT-4o (Fallback 1)
3. Claude Sonnet (Fallback 2)

---

### 4.5 Risk Management System (RMS) V6.2

```
risk_management/
├── risk_models.py         # RiskLimit, RiskBreach, RiskMetrics, RiskConfig
├── limits_engine.py       # Pre-trade validation (memory-enhanced)
├── position_monitor.py    # Real-time position monitoring
├── circuit_breaker.py     # Automatic trading halt
├── alert_dispatcher.py    # Telegram notifications
├── risk_dashboard.py      # Investor dashboard
└── memory_risk_adapter.py # Non-Markovian Kernel integration (NEW V6.2)
```

**Risk Guardian Config:**
- Max trades/day: 20
- Max trades/hour: 10
- Max drawdown (reduce size): 10%
- Max drawdown (stop trading): 20%
- Max daily loss: 5%
- Consecutive losses trigger: 3

---

### 4.6 Portfolio Management (Institutional+)

```
portfolio_management/institutional/
├── portfolio_engine.py        # OmnixPortfolioEngine
├── portfolio_optimizer.py     # Markowitz, Black-Litterman
├── risk_model_engine.py       # VaR, CVaR, drawdown
├── volatility_targeting.py    # Dynamic position sizing
├── exposure_manager.py        # Sector/asset exposure
└── clustering_risk.py         # Correlation clustering
```

---

## 5. omnix_dashboard/ - Web Dashboard

**Framework:** Flask 3.x with Blueprints  
**Production Server:** Gunicorn with gevent workers

### 5.1 Architecture

```
omnix_dashboard/
├── app.py                # Application factory (92 lines)
├── gunicorn.conf.py      # Gunicorn configuration
├── run.py                # Development server
├── blueprints/
│   ├── views.py          # HTML routes (/, /terminal, /classic)
│   ├── core.py           # /api/metrics, /api/trades, /api/health, /api/positions
│   ├── market.py         # /api/ticker, /api/fear-greed, /api/news
│   ├── intelligence.py   # /api/adaptive, /api/riskguardian, /api/signals
│   ├── system.py         # /api/debug, /api/db-diagnostics
│   └── snapshots.py      # /api/snapshots
├── utils/
│   ├── database.py       # Connection pooling (USE_UNIFIED_GATEWAY feature flag)
│   ├── queries.py        # SQL queries (tuple-based row access)
│   ├── decorators.py     # @require_api_key
│   └── external_apis.py  # HTTP helpers with timeout
├── static/
│   ├── css/              # 19 CSS files (modular components)
│   └── js/
│       ├── core/         # api.js, clock.js, utils.js
│       ├── components/   # 11 components (charts, ticker, signals, etc.)
│       └── pages/        # dashboard.js, terminal.js
└── templates/
    ├── base.html
    ├── dashboard.html
    └── terminal.html     # Bloomberg-style trading terminal
```

### 5.2 API Endpoints

| Blueprint | Endpoint | Purpose |
|-----------|----------|---------|
| **core** | `/api/metrics` | Trading performance metrics |
| **core** | `/api/trades` | Recent trade history |
| **core** | `/api/positions` | Open positions with live prices |
| **core** | `/api/health` | System health check |
| **core** | `/api/equity-curve` | Balance over time |
| **market** | `/api/ticker` | Real-time crypto prices |
| **market** | `/api/fear-greed` | Market sentiment index |
| **market** | `/api/news` | Market news |
| **intelligence** | `/api/adaptive` | Adaptive engine status |
| **intelligence** | `/api/riskguardian` | Risk guardian status |
| **intelligence** | `/api/signals` | Active trading signals |
| **system** | `/api/debug` | Debug information |
| **system** | `/api/db-diagnostics` | Pool health |
| **snapshots** | `/api/snapshots` | Portfolio snapshots |

### 5.3 Frontend Components

| Component | File | Purpose |
|-----------|------|---------|
| Charts | `charts.js` | Equity curve, trade distribution |
| Ticker | `ticker.js` | Real-time price ticker |
| Signals | `signals.js` | Trading signal display |
| Fear & Greed | `feargreed.js` | Market sentiment gauge |
| Risk Guardian | `riskguardian.js` | Risk status panel |
| Adaptive | `adaptive.js` | Adaptive engine status |
| Benchmarks | `benchmarks.js` | Performance vs market |
| Volume | `volume.js` | Volume analysis |
| News | `news.js` | Market news feed |
| Status Bar | `statusbar.js` | System status |
| Snapshots | `snapshots.js` | Portfolio snapshots |

---

## 6. Other Packages

### 6.1 omnix_config/ (3 modules, ~850 lines)

| Module | Purpose |
|--------|---------|
| `settings.py` | Centralized settings via dataclasses |
| `env_manager.py` | Environment variable management (580 lines) |
| `grafana/omnix_dashboard.json` | Grafana dashboard config |

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

| Consumer | Connection Method |
|----------|-------------------|
| Dashboard | `DatabaseGateway` (Phase 2) or legacy pool |
| Enterprise Services | `DatabaseServiceEnterprise` |
| Auto Trading Bot | `DatabaseManager` adapter |
| AI Risk Guardian | `DatabaseManager.get_connection()` |

---

## 8. Dependency Matrix

### 8.1 External Dependencies

| Package | Version | Used By |
|---------|---------|---------|
| `ccxt` | - | TradingSystem, KrakenClient |
| `redis` | - | RedisCache, UserSessionManager |
| `psycopg` | 3.x | DatabaseGateway, DatabaseServiceEnterprise |
| `psycopg_pool` | - | Dashboard connection pooling |
| `pypqc` | - | PostQuantumSecurity |
| `numpy` | - | All strategies, quantum modules |
| `scipy` | - | ARES protocols, portfolio optimization |
| `flask` | 3.x | Dashboard |
| `flask-cors` | - | Dashboard CORS |
| `gunicorn` | - | Production server |
| `gevent` | - | Async workers |
| `google-generativeai` | - | Gemini AI |
| `openai` | - | GPT-4o, Whisper |
| `anthropic` | - | Claude |
| `python-telegram-bot` | - | TelegramService |
| `prometheus_client` | - | MetricsEngine |
| `plotly` | - | Chart generation |
| `kaleido` | - | Static chart export |
| `reportlab` | - | PDF generation |
| `requests` | - | External API calls |
| `aiohttp` | - | Async HTTP |

### 8.2 Internal Dependency Graph

```
main.py
├── omnix_config/
│   ├── env_manager.py
│   └── settings.py
├── omnix_core/
│   ├── bot/auto_trading_bot.py
│   │   ├── omnix_services/monitoring/
│   │   ├── omnix_services/optimization/
│   │   ├── omnix_services/ai_service/
│   │   ├── omnix_services/coherence_service/
│   │   ├── omnix_services/risk_management/
│   │   ├── omnix_services/adaptive_engine/
│   │   └── omnix_core/strategies/
│   └── trading_system.py
│       └── omnix_services/trading_service/
├── omnix_services/
│   ├── database_service/
│   ├── trading_service/
│   ├── telegram_service/
│   └── stock_trading/
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

---

## 12. Appendix: File Counts by Package

| Package | Python Files | Other Files | Total |
|---------|--------------|-------------|-------|
| omnix_core | 18 | 0 | 18 |
| omnix_services | 90+ | 1 (SQL) | 91+ |
| omnix_dashboard | 12 | 30+ (JS/CSS/HTML) | 42+ |
| omnix_api | 3 | 0 | 3 |
| omnix_config | 2 | 1 (JSON) | 3 |
| omnix_reports | 1 | 0 | 1 |
| omnix_risk | 6 | 0 | 6 |
| omnix_strategies | 1 | 0 | 1 |
| omnix_testing | 15+ | 10+ (data/reports) | 25+ |
| scripts | 1 | 1 (MD) | 2 |
| tests | 1 | 0 | 1 |
| sql | 2 | 0 | 2 |
| Root | 8 | 0 | 8 |
| **TOTAL** | **~160+** | **~45+** | **~205+** |
