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

## System Architecture

### Core Engines

The system is built around several core engines:

-   **AutoTradingBot V6.4 PREMIUM**: Features multi-crypto scanning (BTC, ETH, SOL rotation every 25 seconds), tiered signal strength, a ramp-up system, HMM quality filter for confidence-weighted regime detection, and drawdown protection mechanisms. Trade counters persist via PostgreSQL.
-   **Non-Markovian Memory Kernel V6.5**: Detects regime transitions, recognizes cyclical patterns, performs memory coherence scoring, and integrates on-chain signals for enhanced temporal memory.
-   **Coherence Engine V5.4 ULTRA**: Utilizes a 6-Tier Veto System for validating strategy agreement, requiring multi-strategy consensus before trade execution with a balanced threshold and signal-strength bypass for strong signals.
-   **AI Risk Guardian V5.4**: Monitors for overtrading, drawdown, and prevents revenge trading to protect capital.

### Portfolio Management

**Portfolio Management V6.4 INSTITUTIONAL+** implements Goldman-Sachs level optimization, including:

-   **RiskModelEngine**: Calculates covariance, correlation, and beta using Ledoit-Wolf shrinkage.
-   **PortfolioOptimizer**: Applies Markowitz and Black-Litterman models with OMNIX views.
-   **VolatilityTargetingEngine**: Dynamically sizes positions (Conservative 5%, Moderate 10%, Aggressive 15%).
-   **ExposureManager**: Enforces sector/asset/beta limits and net/gross compliance.
-   **ClusteringRiskDetector**: Identifies hidden concentration risks through correlation clustering.
-   **OmnixPortfolioEngine**: Orchestrates the unified portfolio management layer.

### Derivatives Trading Module

Supports paper/real trading modes and includes a MarginEngine, KrakenFuturesClient, HedgingService, and FundingArbitrageAnalyzer for managing perpetuals and hedging.

### Stock Trading Premium V6.3 ULTRA

Integrates 9 active institutional modules: Monte Carlo, Kalman Filter, HMM, ARES-STOCK, Non-Markovian Memory, Coherence Engine, Risk Guardian, Gap Protection, and Earnings Protector.

### Adaptive Parameter Engine V6.5 ULTRA

An auto-calibration system for ARES strategies based on market regime. It includes a RegimeSignalProcessor, ParameterCalibrator, CooldownManager, MicrostructureAnalyzer, and safety features like pending calibrations queue and Risk Guardian validation.

### On-Chain Data Intelligence V6.5

Provides institutional-grade blockchain analytics using free APIs, featuring:

-   **WhaleTracker**: Monitors large transactions with circuit breakers.
-   **Arkham Intelligence Integration**: Enriches wallet identities with known entities.
-   **ExchangeFlowAnalyzer**: Detects net flow trends.
-   **NetworkMetricsCollector**: Gathers BTC/ETH health metrics.
-   **SmartMoneySignal**: A weighted composite scoring system.

### UI/UX Decisions

The system includes a web dashboard built with Flask, providing multiple views (main, terminal-style, classic) and a comprehensive set of API endpoints for performance metrics, trading data, market data, market intelligence, and system status.

### Data Flow

Market Data (Kraken/Alpaca) feeds into the Non-Markovian Kernel, which is boosted by On-Chain Intelligence. This leads to Regime Detection and Signal Generation, feeding the Adaptive Parameter Engine. After Coherence Engine Validation and a Risk Guardian Check, trades are executed, persisted in PostgreSQL, and notifications are sent via Telegram.

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

-   **PostgreSQL (Railway)**: Main persistence, handling 35+ tables (e.g., trades, analysis, conversations, balance_history, derivatives, community intelligence, risk management, adaptive engine data, user settings).
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
- **RegimeSignalProcessor**: Processes Non-Markovian Kernel signals for regime detection
- **ParameterCalibrator**: Dynamically adjusts SL/TP/position size per regime (accumulation, distribution, trending, volatile)
- **CooldownManager**: 15-min default cooldown, minimum 5 trades between calibrations
- **MicrostructureAnalyzer**: Fine-tunes based on spread, volume, liquidity
- **Safety Features**: Pending calibrations queue, open position checks, Risk Guardian validation
- **Smooth Transitions**: Exponential smoothing (0.3 factor) prevents sudden parameter jumps
- **Critical Override**: High-volatility regimes bypass cooldown for immediate protection
- **Database Tables**: adaptive_parameters, calibration_events, calibration_metrics

### On-Chain Data Intelligence V6.5
100% FREE APIs - No API keys required:
- **WhaleTracker (ClankApp)**: Transactions >$100K, circuit breaker (3 failures, 5-min cooldown), retry with exponential backoff
- **Arkham Intelligence**: Wallet identity enrichment, 10+ known entities (Binance, Coinbase, Jump Trading, Wintermute, Galaxy Digital, etc.), 1-hour cache TTL
- **ExchangeFlowAnalyzer**: Net flow trend detection, accumulation vs distribution phases
- **NetworkMetricsCollector**: BTC/ETH health (active addresses, tx counts, hash rates)
- **SmartMoneySignal**: Weighted scoring (whale 30%, exchange flow 25%, network 20%, smart money 25%)
- **Kernel Integration**: On-chain signals boost regime detection (neutral 10%, bullish/bearish 20%)

---

## Project Structure

```
omnix/
├── omnix_core/           # Core trading engine (9 modules)
│   ├── bot/              # AutoTradingBot V6.4 PREMIUM
│   ├── cache/            # Redis cache layer
│   ├── context/          # Real Context Provider
│   ├── quantum/          # Quantum RNG, Portfolio Optimizer
│   ├── security/         # Post-quantum cryptography
│   ├── strategies/       # Non-Markovian Kernel, ARES, HMM
│   └── trading_system.py # Main orchestrator
├── omnix_services/       # Business services (22 modules)
│   ├── adaptive_engine/  # V6.5 Adaptive Parameter Engine
│   ├── ai_service/       # AI prompts, context manager
│   ├── coherence_service/# Coherence Engine V5.4 ULTRA
│   ├── database_service/ # PostgreSQL DAL (35+ tables)
│   ├── derivatives/      # Perpetuals, hedging, funding arb
│   ├── market_intelligence/ # Fear & Greed, Finnhub, Alpha Vantage
│   ├── monitoring/       # Risk Guardian V5.4
│   ├── notifications/    # Trade alerts, daily summaries
│   ├── on_chain_service/ # V6.5 On-Chain Intelligence
│   ├── portfolio_management/ # Goldman-Sachs optimization
│   ├── stock_trading/    # Stock Trading Premium V6.3
│   ├── telegram_service/ # Telegram bot integration
│   ├── trading_service/  # Order execution, Monte Carlo
│   └── user_settings/    # Personal Assistant V6.4
├── omnix_dashboard/      # Web dashboard (Flask)
│   ├── templates/        # dashboard.html, terminal.html
│   └── app.py            # 25+ API endpoints
├── omnix_api/            # REST API (Stripe payments)
├── omnix_testing/        # Validation suite
└── sql/                  # Database scripts
```

---

## Dashboard API Endpoints (27 endpoints)

### Core Views (5)
- `GET /` - Main dashboard
- `GET /terminal` - Bloomberg-style terminal
- `GET /classic` - Classic view
- `GET /api/health` - Health check
- `GET /api/debug` - Debug information

### Trading Data (6)
- `GET /api/metrics` - Performance metrics from PostgreSQL
- `GET /api/trades` - Recent trades history
- `GET /api/equity-curve` - Equity curve data
- `GET /api/portfolio` - Portfolio composition
- `GET /api/positions` - Open positions
- `GET /api/signals/active` - Active trading signals

### Market Data (5)
- `GET /api/market/crypto` - Real-time crypto prices (Kraken)
- `GET /api/market/stocks` - Stock prices (Alpaca)
- `GET /api/market/ohlc/<symbol>` - OHLC candlestick data
- `GET /api/market/volume` - Volume analysis
- `GET /api/news` - Market news feed

### Market Intelligence (10)
- `GET /api/market/fear-greed` - Fear & Greed Index (Alternative.me)
- `GET /api/market/finnhub-news` - Finnhub market news
- `GET /api/market/technical-indicators/<symbol>` - Technical indicators (Alpha Vantage)
- `GET /api/intelligence/fear-greed` - Fear & Greed with recommendations
- `GET /api/intelligence/finnhub/news` - Extended Finnhub news feed
- `GET /api/intelligence/finnhub/sentiment/<symbol>` - Symbol-specific sentiment
- `GET /api/intelligence/alpha-vantage/technical/<symbol>` - RSI, MACD, Bollinger Bands
- `GET /api/intelligence/summary` - Combined intelligence summary

### System Status (1)
- `GET /api/system/status` - System health and workflow status

---

## Database Schema (35+ Tables)

### Core (6): users, user_contacts, trades, analysis, conversations, balance_history
### Paper Trading (2): paper_trading_balances, paper_trading_trades
### Derivatives (6): derivatives_balances, trades, positions, funding_log, hedges, funding_opportunities
### Conversational Brain (3): trade_reasonings, trade_evaluations, pending_evaluations
### Community (9): community_feedback, strategy_votes, user_contributions, detected_patterns, improvement_proposals, community_signals, signal_executions, signal_votes, alpha_leaderboard
### Risk (4): risk_guardian_events, risk_limits, risk_limit_breaches, circuit_breaker_status
### Adaptive V6.5 (3): adaptive_parameters, calibration_events, calibration_metrics
### System (4): schema_migrations, video_transcript_cache, sharia_validations, user_settings

---

## Environment Variables

### Required
- DATABASE_URL - PostgreSQL connection
- REDIS_URL - Redis connection
- SESSION_SECRET - Session encryption
- FINNHUB_API_KEY - Finnhub API
- ALPHA_VANTAGE_API_KEY - Alpha Vantage

### Optional
- TELEGRAM_BOT_TOKEN - Telegram bot
- KRAKEN_API_KEY / KRAKEN_API_SECRET - Kraken
- ALPACA_API_KEY / ALPACA_SECRET_KEY - Alpaca
- GEMINI_API_KEY - Google Gemini
- OPENAI_API_KEY - OpenAI
- STRIPE_SECRET_KEY - Stripe

---

## Telegram Commands (Personal Assistant V6.4)

- `/miconfig` - View configuration
- `/perfil` - Set risk profile
- `/limites` - Trading limits
- `/proteccion` - Protection settings
- `/estrategias` - Enable/disable strategies
- `/cryptos` - Tradeable cryptos
- `/autotrading` - Toggle auto-trading
- `/pausar` / `/reanudar` - Pause/resume
- `/onboarding` - Setup wizard
- `/resumen` - Daily summary

Natural Language: "quiero ser mas agresivo", "maximo $500 por trade", "pausa el trading"

---

## Testing Suite (omnix_testing)

- **backtesting_engine.py**: Historical simulation
- **kraken_data_downloader.py**: OHLC with caching
- **metrics_calculator.py**: Sharpe, Sortino, drawdown
- **chart_generator.py**: Plotly visualizations
- **pdf_report_generator.py**: Investor PDF reports
- **institutional_stress_suite.py**: Stress testing
- **historical_events_validator.py**: Black swan testing
- **regime_metrics.py**: Regime-specific performance

---

## Version History

| Version | Date | Features |
|---------|------|----------|
| V6.5 | Dec 2024 | Adaptive Parameter Engine, On-Chain Intelligence, Arkham |
| V6.4 | Nov 2024 | Portfolio INSTITUTIONAL+, Market Intelligence, Personal Assistant |
| V6.3 | Nov 2024 | Stock Trading ULTRA, Real Data Integration |
| V6.2 | Oct 2024 | RMS Memory-Enhanced, Derivatives |
| V6.1 | Oct 2024 | Non-Markovian Kernel, Coherence Engine |
| V6.0 | Sep 2024 | Multi-Exchange Arbitrage, Institutional Compliance |

---

*Last Updated: December 2024 | OMNIX V6.5 INSTITUTIONAL+ | Target: $400K seed at $2.5M valuation*