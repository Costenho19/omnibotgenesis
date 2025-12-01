# OMNIX V6.5 INSTITUTIONAL+ - Automated Trading System

### Overview
OMNIX V6.5 INSTITUTIONAL+ is an enterprise-grade automated cryptocurrency and stock trading system designed for 24/7 operation. Its primary purpose is paper trading to build a credible track record for investor presentations, targeting $400K seed funding at a $2.5M valuation. Key capabilities include AI integration, post-quantum cryptography, real-time market analysis, Non-Markovian temporal memory with On-Chain Data Intelligence, Memory-Enhanced Risk Management, Adaptive Parameter Calibration, and institutional-grade portfolio optimization (Markowitz + Black-Litterman). The system supports over 50 cryptocurrencies and 100 stocks, incorporating modules for institutional compliance and derivatives trading.

### User Preferences
User Communication Preference: Simple, everyday language (Spanish primary).

**Deployment Policy (CRITICAL)**
- **Railway = PRODUCTION (24/7)** - Bot runs permanently here.
- **Replit = DEVELOPMENT ONLY** - For code editing and specific tests.
- **NEVER run the bot on Replit and Railway simultaneously** - Telegram allows only ONE active connection per token. Two instances cause lost messages, polling conflicts, and disconnections.
- **After testing on Replit**: Always stop the workflow before ending the session.
- Code synchronizes with GitHub; Railway deploys automatically from the `main` branch.

**Workflow for Debugging:**
- **Railway Logs**: The user will provide logs directly when needed for debugging.
- **DO NOT start the bot locally** to get logs - use the Railway logs provided by the user.
- **Only edit code here** - tests are validated on Railway after automatic deployment.
- **If started for test/control**: Once everything is confirmed, AUTOMATICALLY STOP the workflow before finishing.

### System Architecture

#### UI/UX Decisions
- **Market Dashboard**: Provides an institutional-grade dashboard with real-time Kraken data, market sentiment, top gainers/losers, 24h volumes, and visual trends for 6 cryptocurrencies.
- **Reporting**: Generates professional, investor-ready PDF reports (25-35 pages) with executive summaries, methodology, results, risk analysis, and trade logs, utilizing Plotly for 5 institutional-quality visualizations.
- **Performance Dashboard V6.4 REAL DATA**: Premium web dashboard connected to PostgreSQL, displaying real-time trading metrics, equity curve, and portfolio data.

#### Technical Implementations
- **Core Strategies**: Incorporates Monte Carlo Simulations, Black Swan Detection, Kelly Criterion, HMM Regime Detection, Dual Kalman Filter, Quantum Momentum, ARES V1/V2, Non-Markovian Kernel, and Order Book Analysis.
- **Non-Markovian Memory Kernel V6.5**: Captures temporal dependencies to detect regime transitions and integrates with On-Chain Data Intelligence.
- **On-Chain Data Intelligence V6.5**: Provides institutional-grade blockchain analytics using free APIs for WhaleTracker, Arkham Intelligence integration, ExchangeFlowAnalyzer, NetworkMetricsCollector, and SmartMoneySignal aggregation.
- **Adaptive Parameter Engine V6.5 ULTRA**: An auto-calibration system for ARES strategies that dynamically adjusts parameters (SL/TP/position size) based on market regime, utilizing a `RegimeSignalProcessor`, `ParameterCalibrator`, `CooldownManager`, and `MicrostructureAnalyzer`.
- **AutoTradingBot V6.4 PREMIUM**: Optimized for 20-50 trades/day with a 55%+ win rate, featuring multi-crypto scanning, tiered signal strength, a ramp-up system, HMM quality filter, Coherence Engine, drawdown protection, and state persistence via PostgreSQL.
- **Notification Services V6.4 PREMIUM**: Provides real-time Telegram trade alerts and daily summaries, including performance benchmarks against Bitcoin HODL.
- **AI & Machine Learning**: Includes a conversational AI ("Cerebro Conversacional") for reasoning explanations and an Auto-Learning System for strategy parameter optimization.
- **Risk Management & Protection**: Features Coherence Engine V5.4 ULTRA (6-Tier Veto System), AI Risk Guardian V5.4 (real-time risk supervision), and RMS V6.2 MEMORY-ENHANCED (predictive risk assessment). Includes an Auto-Optimization Engine, Multi-Exchange Arbitrage V6.0, and an Institutional Compliance Suite.
- **Derivatives Trading Module**: Orchestrates perpetuals trading with paper/real modes, `MarginEngine`, `KrakenFuturesClient`, `HedgingService`, `FundingArbitrageAnalyzer`, and Telegram integration.
- **Portfolio Management V6.4 INSTITUTIONAL+**: Offers Goldman-Sachs level portfolio optimization with modules like `RiskModelEngine`, `PortfolioOptimizer` (Markowitz + Black-Litterman), `VolatilityTargetingEngine`, `ExposureManager`, and `ClusteringRiskDetector`.
- **Market Intelligence System V6.4**: Integrates live external data for market sentiment (Fear & Greed Index), news (Finnhub), and technical indicators (Alpha Vantage).
- **OMNIX Personal Assistant Premium V6.4**: Allows per-user custom configuration via Telegram, including risk profiles, personalized limits, and natural language processing for command execution.
- **Robust Market Data System**: Utilizes a 3-source fallback (Kraken Auth → Kraken Public → CoinGecko) with JSON validation and timeouts.
- **Real Data Integration V6.4**: Portfolio commands fetch real historical data from Kraken OHLC and Alpaca Bars API for stocks.
- **Stock Trading Premium V6.3 ULTRA**: Institutional-grade stock trading with 9 active modules including Monte Carlo, Kalman Filter, HMM, ARES-STOCK, Non-Markovian Memory, Coherence Engine, Risk Guardian, Gap Protection, and Earnings Protector.

#### System Design Choices
- **Modular Architecture**: Composed of 75+ specialized Python modules organized into `omnix_core/`, `omnix_services/`, `omnix_testing/`.
- **Centralized Database Layer**: All database logic is managed within `omnix_services/database_service/`, featuring 33 code-managed tables and 22+ DAL methods with transactional schema migrations.
- **Unified Configuration**: Centralized `env_manager.py` for environment variables.
- **Deployment**: Designed for 24/7 operation on Railway (Production) and Replit (Development).

### External Dependencies

#### APIs & Services
- **Kraken Exchange**: Primary for market data, account info, and order execution.
- **Google Gemini**: Gemini 2.0 Flash (primary AI model).
- **OpenAI**: GPT-4o, Whisper (for AI services).
- **Anthropic Claude**: Optional AI fallback.
- **Stripe**: Payment processing.
- **CoinGecko API**: Backup price data.
- **ANU QRNG API**: For true quantum randomness.
- **ClankApp API**: Free whale transaction tracking (no API key required).
- **Arkham Intelligence API**: Free wallet identity enrichment (no API key required).
- **Alternative.me API**: Fear & Greed Index (free, no key needed).
- **Finnhub API**: Market news and sentiment.
- **Alpha Vantage API**: Technical indicators.
- **Alpaca API**: Historical stock data.

#### Databases
- **PostgreSQL (Railway)**: Main relational database hosted on Railway, managing 33 tables for core operations, risk, derivatives, community, signals, and video transcript caching. Uses `psycopg3` driver with SSL.
- **Redis (Railway)**: External in-memory cache for persistent state management, conversation history, market data caching, and rate limiting.

#### Key Python Libraries
- `numpy`, `scipy`, `ccxt`: Core trading and mathematical operations.
- `google-generativeai`, `openai`: AI model integration.
- `python-telegram-bot`: Telegram integration.
- `psycopg` (v3), `redis`: Database drivers.
- `requests`, `websockets`, `aiohttp`, `httpx`: HTTP and WebSocket communication.
- `pypqc`: Post-quantum cryptography implementation.
- `pandas`, `plotly`, `kaleido`, `reportlab`, `PyPDF2`: Professional testing and reporting.