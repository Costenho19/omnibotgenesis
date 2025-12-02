# OMNIX V6.5 INSTITUTIONAL+ - Automated Trading System

## Overview

OMNIX V6.5 INSTITUTIONAL+ is an enterprise-grade automated cryptocurrency and stock trading system designed for 24/7 operation. Its primary purpose is paper trading to build a credible track record for investor presentations, targeting $400K seed funding at $2.5M valuation. Key capabilities include AI integration, post-quantum cryptography, real-time market analysis, Non-Markovian Temporal Memory with On-Chain Data Intelligence, adaptive parameter calibration, institutional portfolio optimization, derivatives trading, and dual-market support for Kraken (crypto) and Alpaca (stocks). The system aims for 20-50 trades/day with a 55%+ win rate, multi-crypto scanning, and tiered signal strengths.

## User Preferences

**Communication**: Simple, everyday language (Spanish primary).

### Deployment Policy (CRITICAL)
| Environment | Purpose | Status |
|-------------|---------|--------|
| **Railway** | PRODUCTION (24/7) | Bot runs permanently |
| **Replit** | DEVELOPMENT | Code editing and tests only |

**NEVER run the bot on Replit and Railway simultaneously** - Telegram allows only ONE active connection per token.

### Workflow for Debugging
1. **Railway Logs**: User provides logs directly for debugging
2. **DO NOT start bot locally** - Use Railway logs provided
3. **Code sync**: GitHub -> Railway auto-deploy from main branch
4. **After testing on Replit**: ALWAYS stop workflow before ending session

### Bot Testing Protocol (MANDATORY)
> **REGLA OBLIGATORIA**: Cada vez que se active el bot en Replit para testing:
> 1. Realizar las pruebas necesarias
> 2. **APAGAR el workflow del bot ANTES de terminar la sesión**
> 3. Verificar que el workflow esté detenido
>
> **Razón**: Telegram solo permite UNA conexión activa por token. Si el bot corre en Replit y Railway al mismo tiempo, habrá conflictos y errores de conexión.

## System Architecture

### Core Engines

The system is built around several core engines:

-   **AutoTradingBot V6.4 PREMIUM**: Features multi-crypto scanning, tiered signal strength, a ramp-up system, HMM quality filter for confidence-weighted regime detection, and drawdown protection.
-   **Non-Markovian Memory Kernel V6.5**: Detects regime transitions, recognizes cyclical patterns, performs memory coherence scoring, and integrates on-chain signals.
-   **Coherence Engine V5.4 ULTRA**: Utilizes a 6-Tier Veto System for validating strategy agreement, requiring multi-strategy consensus before trade execution.
-   **AI Risk Guardian V5.4**: Monitors for overtrading, drawdown, and prevents revenge trading.

### Portfolio Management

**Portfolio Management V6.4 INSTITUTIONAL+** implements Goldman-Sachs level optimization, including Markowitz and Black-Litterman models, dynamic position sizing, exposure management, and risk detection.

### Derivatives Trading Module

Supports paper/real trading modes and includes a MarginEngine, KrakenFuturesClient, HedgingService, and FundingArbitrageAnalyzer.

### Stock Trading Premium V6.3 ULTRA

Integrates 9 active institutional modules: Monte Carlo, Kalman Filter, HMM, ARES-STOCK, Non-Markovian Memory, Coherence Engine, Risk Guardian, Gap Protection, and Earnings Protector.

### Adaptive Parameter Engine V6.5 ULTRA

An auto-calibration system for ARES strategies based on market regime. It includes a RegimeSignalProcessor, ParameterCalibrator, CooldownManager, MicrostructureAnalyzer, and safety features.

### On-Chain Data Intelligence V6.5

Provides institutional-grade blockchain analytics using free APIs, featuring WhaleTracker, Arkham Intelligence Integration, ExchangeFlowAnalyzer, NetworkMetricsCollector, and SmartMoneySignal.

### UI/UX Decisions

The system includes a web dashboard built with Flask, providing multiple views (main, terminal-style, classic) and a comprehensive set of API endpoints for performance metrics, trading data, market data, market intelligence, and system status.

### Backend Architecture (December 2024 Refactor)

**Flask Blueprints Architecture (12 files, 1961 lines):**
```
omnix_dashboard/
├── app.py                  # Application factory (90 lines, 95% reduction)
├── run.py                  # WSGI entry point
├── blueprints/             # 5 Blueprints, 25 routes total
│   ├── views.py           # HTML pages (3 routes)
│   ├── core.py            # Core APIs (6 routes)
│   ├── market.py          # Market data (7 routes)
│   ├── intelligence.py    # External APIs (4 routes)
│   └── system.py          # System status (5 routes)
└── utils/                  # Shared utilities (586 lines)
    ├── database.py        # PostgreSQL connection pool
    ├── decorators.py      # API authentication
    ├── external_apis.py   # HTTP client with retry
    └── queries.py         # SQL query functions
```

**Key Improvements:**
- Application factory pattern for testability
- Connection pooling (min=2, max=10)
- Absolute imports for package independence
- Modular route organization by domain

### Frontend Architecture (December 2024 Refactor)

**Modular CSS (18 files, 1562 lines) - BEM Methodology:**
```
omnix_dashboard/static/css/
├── base/ (variables.css, reset.css, typography.css)
├── components/ (panel.css, card.css, ticker.css, signal.css, badge.css, chart.css, table.css, news.css, protection.css)
├── layouts/ (header.css, terminal-grid.css, animations.css)
├── pages/ (terminal.css, dashboard.css)
└── main.css (imports all modules)
```

**Modular JavaScript (11 files, 1318 lines) - IIFE Pattern:**
```
omnix_dashboard/static/js/
├── core/ (api.js, utils.js, clock.js)
├── components/ (charts.js, ticker.js, signals.js, volume.js, news.js, feargreed.js)
└── pages/ (terminal.js, dashboard.js)
```

**Jinja2 Template Inheritance:**
- `base.html`: Centralized head, shared CSS/JS, extensible blocks (title, extra_css, body_class, content, extra_js)
- `terminal.html`: Extends base.html, Trading Terminal view (216 lines)
- `dashboard.html`: Extends base.html, Classic institutional view (314 lines)

### Data Flow

Market Data (Kraken/Alpaca) feeds into the Non-Markovian Kernel, boosted by On-Chain Intelligence. This leads to Regime Detection and Signal Generation, feeding the Adaptive Parameter Engine. After Coherence Engine Validation and a Risk Guardian Check, trades are executed, persisted in PostgreSQL, and notifications are sent via Telegram.

## External Dependencies

### APIs and Services

-   **Kraken Exchange**: Primary crypto data and order execution.
-   **Alpaca**: Stock data and historical bars.
-   **Google Gemini (2.0 Flash)**: Primary AI model.
-   **OpenAI (GPT-4o, Whisper)**: AI services and transcription.
-   **Anthropic Claude**: AI fallback.
-   **CoinGecko**: Backup crypto prices.
-   **ClankApp**: Whale transaction tracking.
-   **Arkham Intelligence**: Wallet identity enrichment.
-   **Alternative.me**: Fear and Greed Index.
-   **Finnhub**: Market news and sentiment.
-   **Alpha Vantage**: Technical indicators.
-   **ANU QRNG**: Quantum random numbers.
-   **Stripe**: Payment processing.

### Databases

-   **PostgreSQL (Railway)**: Main persistence for trades, analysis, conversations, balance history, derivatives, community intelligence, risk management, adaptive engine data, and user settings.
-   **Redis (Railway)**: Used for caching, state management, and rate limiting.

### Key Python Libraries

-   **Core Trading**: numpy, scipy, ccxt, pandas
-   **AI/ML**: google-generativeai, openai, anthropic
-   **Telegram**: python-telegram-bot
-   **Database**: psycopg (v3), redis
-   **HTTP**: requests, aiohttp, httpx, websockets
-   **Security**: pypqc (post-quantum)
-   **Reporting**: plotly, kaleido, reportlab, PyPDF2
---

## What's New in V6.5

### Adaptive Parameter Engine V6.5 ULTRA
- **RegimeSignalProcessor**: Processes Non-Markovian Kernel signals
- **ParameterCalibrator**: Dynamically adjusts SL/TP/position size per regime
- **CooldownManager**: 15-min cooldown, min 5 trades between calibrations
- **MicrostructureAnalyzer**: Fine-tunes based on spread, volume, liquidity
- **Safety Features**: Pending calibrations queue, open position checks, Risk Guardian validation
- **Database Tables**: adaptive_parameters, calibration_events, calibration_metrics

### On-Chain Data Intelligence V6.5
100% FREE APIs - No API keys required:
- **WhaleTracker (ClankApp)**: Transactions >$100K with circuit breaker and retry logic
- **Arkham Intelligence**: Wallet identity enrichment (Binance, Coinbase, Jump Trading, etc.)
- **ExchangeFlowAnalyzer**: Net flow trend detection
- **NetworkMetricsCollector**: BTC/ETH health metrics
- **SmartMoneySignal**: Weighted composite scoring
- **Kernel Integration**: On-chain signals boost regime detection

---

## Project Structure

omnix/
- omnix_core/ (9 modules): bot, cache, context, quantum, security, strategies, trading_system.py
- omnix_services/ (22 modules): adaptive_engine, ai_service, coherence_service, database_service, derivatives, market_intelligence, monitoring, notifications, on_chain_service, portfolio_management, stock_trading, telegram_service, trading_service, user_settings
- omnix_dashboard/: Flask dashboard with 25+ API endpoints
- omnix_api/: REST API with Stripe payments
- omnix_testing/: Validation suite

---

## Dashboard API Endpoints (25)

### Core Views (5): /, /terminal, /classic, /api/health, /api/debug
### Trading Data (6): /api/metrics, /api/trades, /api/equity-curve, /api/portfolio, /api/positions, /api/signals/active
### Market Data (5): /api/market/crypto, /api/market/stocks, /api/market/ohlc/<symbol>, /api/market/volume, /api/news
### Market Intelligence (8): /api/market/fear-greed, /api/market/finnhub-news, /api/market/technical-indicators/<symbol>, /api/intelligence/fear-greed, /api/intelligence/finnhub/news, /api/intelligence/finnhub/sentiment/<symbol>, /api/intelligence/alpha-vantage/technical/<symbol>, /api/intelligence/summary
### System (1): /api/system/status

---

## Database Schema (35+ Tables)

- Core (6): users, user_contacts, trades, analysis, conversations, balance_history
- Paper Trading (2): paper_trading_balances, paper_trading_trades
- Derivatives (6): derivatives_balances, trades, positions, funding_log, hedges, funding_opportunities
- Conversational Brain (3): trade_reasonings, trade_evaluations, pending_evaluations
- Community (9): community_feedback, strategy_votes, user_contributions, detected_patterns, improvement_proposals, community_signals, signal_executions, signal_votes, alpha_leaderboard
- Risk (4): risk_guardian_events, risk_limits, risk_limit_breaches, circuit_breaker_status
- Adaptive V6.5 (3): adaptive_parameters, calibration_events, calibration_metrics
- System (4): schema_migrations, video_transcript_cache, sharia_validations, user_settings

---

## Environment Variables

### Required: DATABASE_URL, REDIS_URL, SESSION_SECRET, FINNHUB_API_KEY, ALPHA_VANTAGE_API_KEY
### Optional: TELEGRAM_BOT_TOKEN, KRAKEN_API_KEY, KRAKEN_API_SECRET, ALPACA_API_KEY, ALPACA_SECRET_KEY, GEMINI_API_KEY, OPENAI_API_KEY, STRIPE_SECRET_KEY

---

## Telegram Commands (Personal Assistant V6.4)

/miconfig, /perfil, /limites, /proteccion, /estrategias, /cryptos, /autotrading, /pausar, /reanudar, /onboarding, /resumen

Natural Language: "quiero ser mas agresivo", "maximo $500 por trade", "pausa el trading"

---

## Testing Suite (omnix_testing)

- backtesting_engine.py: Historical simulation
- kraken_data_downloader.py: OHLC with caching
- metrics_calculator.py: Sharpe, Sortino, drawdown
- pdf_report_generator.py: Investor PDF reports
- institutional_stress_suite.py: Stress testing
- historical_events_validator.py: Black swan testing

---

## Version History

| Version | Date | Features |
|---------|------|----------|
| V6.5 | Dec 2024 | Adaptive Parameter Engine, On-Chain Intelligence |
| V6.4 | Nov 2024 | Portfolio INSTITUTIONAL+, Market Intelligence |
| V6.3 | Nov 2024 | Stock Trading ULTRA, Real Data Integration |
| V6.2 | Oct 2024 | RMS Memory-Enhanced, Derivatives |
| V6.1 | Oct 2024 | Non-Markovian Kernel, Coherence Engine |
| V6.0 | Sep 2024 | Multi-Exchange Arbitrage, Institutional Compliance |

---

*Last Updated: December 2024 | OMNIX V6.5 INSTITUTIONAL+ | $400K seed at $2.5M valuation*
