# OMNIX V6.5 INSTITUTIONAL+ - Project Structure Documentation

**Version:** V6.5 INSTITUTIONAL+  
**Last Updated:** December 2024  
**Lines of Code:** ~85,000+ across 120+ Python modules  
**Main Entry Point:** `main.py`

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Root Directory](#root-directory)
4. [Core System (omnix_core/)](#core-system)
5. [Services Layer (omnix_services/)](#services-layer)
6. [Dashboard (omnix_dashboard/)](#dashboard)
7. [API Layer (omnix_api/)](#api-layer)
8. [Testing (omnix_testing/)](#testing)
9. [Data Flow](#data-flow)
10. [Deployment](#deployment)

---

## Project Overview

**OMNIX V6.5 INSTITUTIONAL+** is an enterprise-grade automated trading system for cryptocurrency and stocks, designed for 24/7 operation. Key features:

- **Dual Market Support**: Kraken (crypto) + Alpaca (stocks)
- **AI/ML Integration**: Gemini 2.0 Flash, GPT-4o, Claude
- **Post-Quantum Security**: NIST 2024 compliant (Kyber-768 + Dilithium-3)
- **Non-Markovian Memory**: Regime detection with on-chain intelligence
- **Adaptive Parameter Engine**: Auto-calibration based on market conditions
- **6 Portfolio Modules**: Risk Parity, Black-Litterman, Kelly, HRP, Mean-Variance, CVaR
- **9 Protection Modules**: HMM, Kalman, Monte Carlo, ARES, Gap/Earnings Protection
- **Paper Trading**: $1M virtual capital for track record generation

**Business Goal**: Secure $400K seed funding at $2.5M valuation with verifiable trading performance.

---

## Architecture Diagram

```
                            OMNIX V6.5 INSTITUTIONAL+
┌─────────────────────────────────────────────────────────────────────────┐
│                              ENTRY POINTS                                │
│                    main.py (Bot) | start_dashboard.py                    │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         │                           │                           │
         ▼                           ▼                           ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   omnix_core/   │      │omnix_services/  │      │omnix_dashboard/ │
│                 │      │                 │      │                 │
│ - strategies/   │◄────►│ - trading/      │◄────►│ - app.py        │
│ - security/     │      │ - ai_service/   │      │ - templates/    │
│ - quantum/      │      │ - telegram/     │      │ - static/       │
│ - bot/          │      │ - database/     │      │                 │
│ - cache/        │      │ - portfolio/    │      │ 25+ API         │
│                 │      │ - adaptive/     │      │ endpoints       │
│                 │      │ - on_chain/     │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
         │                           │                           │
         │                           ▼                           │
         │              ┌─────────────────────┐                  │
         └─────────────►│   EXTERNAL SERVICES  │◄────────────────┘
                        │                      │
                        │ - Kraken API         │
                        │ - Alpaca API         │
                        │ - PostgreSQL         │
                        │ - Redis              │
                        │ - Gemini/OpenAI      │
                        │ - Telegram           │
                        │ - Finnhub            │
                        │ - Alpha Vantage      │
                        └──────────────────────┘
```

---

## Root Directory

```
omnix/
├── main.py                         # Main bot entry point
├── start_dashboard.py              # Dashboard entry point
├── requirements.txt                # Python dependencies (150+)
├── replit.md                       # Project documentation
├── railway.json                    # Railway deployment config
│
├── omnix_core/                     # Core business logic (9 modules)
├── omnix_services/                 # Service layer (22 modules)
├── omnix_dashboard/                # Flask web dashboard
├── omnix_api/                      # REST API & payments
├── omnix_testing/                  # Validation & backtesting
├── omnix_config/                   # Configuration management
│
├── docs/                           # Documentation
│   ├── core/                       # Architecture docs
│   ├── deployment/                 # Deployment guides
│   ├── testing/                    # Testing docs
│   └── archive/                    # Historical docs
│
├── backtesting_results/            # Backtest output
└── investor_presentation/          # Investor reports
```

---

## Core System

**Location:** `omnix_core/` (9 modules)

```
omnix_core/
├── __init__.py
│
├── strategies/                      # ARES Quantum Trading Strategies
│   ├── ares_v1.py                  # ARES V1 Swing (55-65% win rate)
│   └── ares_v2.py                  # ARES V2 Scalping M1 (60-70% win rate)
│
├── security/                        # Post-Quantum Cryptography
│   ├── pqc_security.py             # NIST 2024 PQC (Kyber-768)
│   └── pqc_encryption.py           # Encryption utilities
│
├── quantum/                         # Quantum Enhancements
│   └── enhancements.py             # QRNG & QAOA integration
│
├── bot/                            # Autonomous Trading Bot
│   └── auto_trading_bot.py         # AutoTradingBot V6.4 PREMIUM
│
├── trading_system.py               # Main Trading System
├── cache/                          # Redis caching layer
├── context/                        # Context management
└── models/                         # Data models
```

### Key Components

- **ARES V1**: Swing trading strategy with 6 institutional indicators
- **ARES V2**: M1 scalping with 5 precision indicators
- **AutoTradingBot**: Multi-crypto scanning, tiered signals, ramp-up system
- **PQC Security**: Post-quantum cryptography for institutional compliance

---

## Services Layer

**Location:** `omnix_services/` (22 modules)

```
omnix_services/
├── trading_service/                 # Enterprise Trading
│   ├── trading_service.py          # Main trading service
│   ├── kraken_client.py            # Kraken REST API
│   ├── paper_trading_manager.py    # $1M virtual trading
│   └── advanced_features.py        # HMM, Kalman, Sentiment
│
├── ai_service/                      # AI & Machine Learning
│   ├── ai_service.py               # Conversational AI
│   └── ai_models.py                # Multi-LLM (Gemini, GPT-4o, Claude)
│
├── adaptive_engine/                 # V6.5 Adaptive Parameter Engine
│   ├── regime_signal_processor.py  # Non-Markovian signals
│   ├── parameter_calibrator.py     # Dynamic SL/TP adjustment
│   ├── cooldown_manager.py         # 15-min calibration cooldown
│   └── microstructure_analyzer.py  # Spread/volume analysis
│
├── on_chain_service/               # V6.5 On-Chain Intelligence
│   ├── whale_tracker.py            # ClankApp whale transactions
│   ├── exchange_flow_analyzer.py   # Net flow detection
│   └── smart_money_signal.py       # Weighted composite scoring
│
├── portfolio_management/           # Goldman-Sachs Level Optimization
│   ├── risk_parity.py              # Risk parity allocation
│   ├── black_litterman.py          # Black-Litterman model
│   ├── kelly_criterion.py          # Kelly optimal sizing
│   ├── hrp_optimizer.py            # Hierarchical risk parity
│   ├── mean_variance.py            # Markowitz optimization
│   └── cvar_optimizer.py           # CVaR optimization
│
├── stock_trading/                  # Stock Trading Premium V6.3
│   └── stock_trading_premium.py    # Alpaca integration
│
├── derivatives/                    # Derivatives Trading
│   ├── margin_engine.py            # Margin calculations
│   ├── hedging_service.py          # Hedging strategies
│   └── funding_arbitrage.py        # Funding rate arbitrage
│
├── market_intelligence/            # Market Data & Analysis
│   ├── fear_greed_analyzer.py      # Fear & Greed Index
│   ├── finnhub_service.py          # News & sentiment
│   └── alpha_vantage_service.py    # Technical indicators
│
├── database_service/               # PostgreSQL (44 tables)
│   └── database_manager.py         # Connection management
│
├── telegram_service/               # Telegram Bot (CEO-style AI)
│   └── enterprise_bot.py           # Personal Assistant V6.4
│
├── coherence_service/              # 6-Tier Veto System
│   └── coherence_engine.py         # Multi-strategy consensus
│
├── monitoring/                     # Performance Monitoring
│   ├── ai_risk_guardian.py         # AI risk monitoring
│   └── performance_tracker.py      # Metrics tracking
│
└── notifications/                  # Alert System
    └── notification_service.py     # Telegram notifications
```

---

## Dashboard

**Location:** `omnix_dashboard/`

```
omnix_dashboard/
├── app.py                          # Flask application (25+ endpoints)
├── templates/
│   ├── index.html                  # Main dashboard (Bloomberg-style)
│   ├── terminal.html               # Terminal view
│   └── classic.html                # Classic view
└── static/
    ├── css/                        # Stylesheets
    └── js/                         # JavaScript
```

### API Endpoints (25)

**Core Views (5):** `/`, `/terminal`, `/classic`, `/api/health`, `/api/debug`

**Trading Data (6):** `/api/metrics`, `/api/trades`, `/api/equity-curve`, `/api/portfolio`, `/api/positions`, `/api/signals/active`

**Market Data (5):** `/api/market/crypto`, `/api/market/stocks`, `/api/market/ohlc/<symbol>`, `/api/market/volume`, `/api/news`

**Market Intelligence (8):** Fear & Greed, Finnhub News, Technical Indicators, Sentiment Analysis

**System (1):** `/api/system/status`

---

## Testing

**Location:** `omnix_testing/`

```
omnix_testing/
├── backtesting/
│   ├── backtesting_engine.py       # Historical simulation
│   ├── kraken_data_downloader.py   # OHLC data with caching
│   └── metrics_calculator.py       # Sharpe, Sortino, drawdown
│
├── pdf_report_generator.py         # Investor PDF reports
├── institutional_stress_suite.py   # Stress testing
├── historical_events_validator.py  # Black swan testing
└── run_premium_validation.py       # Interactive validation
```

---

## Data Flow

### Trading Signal Generation

```
Market Data (Kraken/Alpaca)
         ↓
Non-Markovian Kernel V6.5 + On-Chain Intelligence
         ↓
Regime Detection (bullish/bearish/sideways)
         ↓
Adaptive Parameter Engine (calibrate SL/TP/size)
         ↓
ARES V1/V2 Signal Generation
         ↓
Coherence Engine Validation (6-tier veto)
         ↓
AI Risk Guardian Check
         ↓
Execute Trade (Paper or Real)
         ↓
PostgreSQL Persistence + Telegram Notification
```

### User Interaction Flow

```
Telegram User
    ↓
EnterpriseTelegramBot (Personal Assistant V6.4)
    ↓
├─► ConversationalAI → Gemini 2.0 Flash
├─► TradingService → ARES Strategies
├─► PortfolioManager → 6 Optimization Modules
└─► DatabaseManager → PostgreSQL (44 tables)
```

---

## Deployment

### Railway (Production)
- Auto-deploys from GitHub push to `main` branch
- Bot runs 24/7 with auto-restart
- Dashboard accessible via public URL

### Replit (Development)
- Code editing and testing only
- NEVER run bot on both platforms simultaneously
- Stop workflows before ending sessions

### Configuration
- `railway.json`: Railway deployment settings
- `replit.md`: Project documentation
- `.env` / Replit Secrets: Environment variables

---

## Development Guidelines

### Code Conventions
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions: `snake_case()`
- Type hints required

### Adding New Features
1. Identify layer (core/services/dashboard)
2. Create module in correct directory
3. Add imports to `__init__.py`
4. Update documentation
5. Test locally
6. Deploy to Railway

---

**Document Version:** 3.0  
**OMNIX V6.5 INSTITUTIONAL+**  
**Last Updated:** December 2024
