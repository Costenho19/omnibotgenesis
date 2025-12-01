# OMNIX V6.4 INSTITUTIONAL+ - Automated Trading System

### Overview
OMNIX V6.4 INSTITUTIONAL+ is an enterprise-grade automated cryptocurrency and stock trading system for 24/7 operation. It focuses on paper trading to build a credible track record for investor presentations targeting $400K seed funding at $2.5M valuation. Key features include AI integration, post-quantum cryptography, real-time market analysis, Non-Markovian temporal memory, Memory-Enhanced Risk Management, and institutional-grade portfolio optimization (Markowitz + Black-Litterman). The project supports 50+ cryptocurrencies and 100+ stocks with modules for institutional compliance and derivatives trading.

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
- **Market Dashboard**: Institutional-grade dashboard with real-time Kraken data, market sentiment, top gainers/losers, 24h volumes, and visual trends for 6 cryptocurrencies.
- **Reporting**: Generates professional, investor-ready PDF reports (25-35 pages) with executive summaries, methodology, results, risk analysis, and trade logs, utilizing Plotly for 5 institutional-quality visualizations.

#### Technical Implementations
- **Core Strategies**: Includes Monte Carlo Simulations, Black Swan Detection, Kelly Criterion, HMM Regime Detection, Dual Kalman Filter, Quantum Momentum, ARES V1/V2, Non-Markovian Kernel, and Order Book Analysis.
- **Non-Markovian Memory Kernel V6.1**: Captures temporal dependencies to detect regime transitions, cyclical patterns, and memory coherence.
- **ARES Institutional Protocols**: ARES V1 (Swing Trading) and ARES V2 (Scalping M1) with target win rates and multi-layer Kill-Switch Protection.
- **AutoTradingBot V6.4 PREMIUM**: Optimized for 20-50 trades/day with 55%+ win rate:
    - **Multi-Crypto Scanning**: Rotates through 3 pairs (BTC, ETH, SOL) every 25 seconds.
    - **Tiered Signal Strength**: VERY_STRONG (100%), STRONG (75%), MODERATE (50%) position sizing.
    - **Ramp-Up System**: Conservative start (30% size) scaling to 100% after 50 successful trades with DB persistence.
    - **HMM Quality Filter**: Enhanced regime detection with confidence-weighted decisions.
    - **Coherence Engine V6.4**: Balanced veto system (45% threshold) with signal-strength bypass for VERY_STRONG.
    - **Drawdown Protection**: Auto-reduces position size on losing days ($200+ loss = 75%, $500+ = 50%).
    - **State Persistence**: Trade counters and metrics persist across restarts via PostgreSQL.
- **Notification Services V6.4 PREMIUM**: Real-time trade alerts and daily summaries:
    - **TradeNotificationService**: Instant Telegram alerts when trades execute (BUY/SELL with P&L).
    - **DailySummaryService**: Automated daily summary at 20:00 UTC with institutional metrics.
    - **Benchmark Comparison**: Shows OMNIX performance vs Bitcoin HODL with alpha calculation.
    - **Telegram Command**: `/resumen` for on-demand daily summary generation.
- **Professional Testing & Validation System**: Features Walk-Forward Analysis, Monte Carlo Stress Testing, Market Regime Testing, Realistic Cost Modeling, and Investor Report Generation.
- **AI & Machine Learning**: Conversational AI ("Cerebro Conversacional") for self-explaining AI reasoning and an Auto-Learning System for strategy parameter optimization.
- **Quantum Physics Validation System**: PhD+ level scientific accuracy with 31 verified formulas and quantum credibility scoring.
- **Risk Management & Protection**:
    - **Coherence Engine V5.4 ULTRA**: Validates agreement between trading strategies using a 6-Tier Veto System.
    - **AI Risk Guardian V5.4**: Real-time risk supervision (Overtrading, Drawdown, Revenge Trading Detection, Capital Protection).
    - **Risk Management System (RMS) V6.2 MEMORY-ENHANCED**: Institutional-grade risk control with predictive risk assessment using Non-Markovian temporal patterns.
    - **Auto-Optimization Engine**: Continuously improves strategies via Genetic Algorithm, A/B Testing, and Auto-Adjustment.
    - **Multi-Exchange Arbitrage V6.0**: Institutional arbitrage across 8 exchanges.
    - **Institutional Compliance Suite**: Includes InstitutionalStressSuite, InstitutionalAuditLogger, and a DeadManSwitch.
- **Derivatives Trading Module**: Orchestrates perpetuals trading with paper/real modes, `MarginEngine`, `KrakenFuturesClient`, `HedgingService`, `FundingArbitrageAnalyzer`, and Telegram integration.
- **Trading Modes**: Paper Trading, Real Trading (with post-quantum signed orders), and Backtesting.
- **Quantum Enhancements**: ANU QRNG for true quantum randomness.
- **Strategic Honesty System**: Provides CEO-style, data-driven responses, avoiding raw limitations.
- **Leverage Validation**: Automatically detects and rejects leverage requests exceeding 5x.
- **Multi-Crypto Support**: Supports 50+ cryptocurrencies with primary Kraken and fallback CoinGecko data sources.
- **Robust Market Data System**: Uses 3-source fallback (Kraken Auth → Kraken Public → CoinGecko) with JSON validation and timeouts.
- **Real Data Integration V6.4**: Portfolio commands now fetch REAL historical data:
    - **Kraken OHLC**: Auto-detects response keys (handles `XXBTZUSD` vs `XBTUSD` mapping)
    - **Alpaca Bars API**: 60-day historical bars for stocks (AAPL, MSFT, GOOGL, etc.)
    - **Data Quality Tracking**: Logs which assets use real vs synthetic fallback data
- **Stock Trading Premium V6.3 ULTRA**: 100% institutional-grade stock trading with 9 active modules: Monte Carlo, Kalman Filter, HMM, ARES-STOCK, Non-Markovian Memory, Coherence Engine, Risk Guardian, Gap Protection, and Earnings Protector.
- **YouTube Video Analysis**: Enhanced with OpenAI Whisper as an ultimate fallback for transcript generation, including caching for efficiency.
- **Portfolio Management V6.4 INSTITUTIONAL+**: Goldman-Sachs level portfolio optimization with 5 institutional modules:
    - **RiskModelEngine**: Covariance matrix, correlation analysis, beta calculations with Ledoit-Wolf shrinkage.
    - **PortfolioOptimizer**: Markowitz Mean-Variance + Black-Litterman views integration from OMNIX signals (HMM, ARES, Monte Carlo).
    - **VolatilityTargetingEngine**: Dynamic position sizing to maintain target volatility (Conservative 5%, Moderate 10%, Aggressive 15%, Institutional 12%).
    - **ExposureManager**: Sector/asset/beta limits, net/gross exposure compliance, institutional mandates.
    - **ClusteringRiskDetector**: Hidden concentration risk detection via correlation clustering, effective-N calculation.
    - **OmnixPortfolioEngine**: Unified orchestration layer combining all modules.
- **Performance Dashboard V6.4 REAL DATA**: Premium 2025-style web dashboard connected directly to PostgreSQL. Features:
    - **Real-time data** from `paper_trading_trades` and `balance_history` tables
    - **Live Data indicator** (green dot) when database connected
    - **Professional empty state** ("No trading data yet") instead of fake demo data
    - **Automatic production data** - Shows real trades when deployed to Railway
    - **Real-time Clock**: Auto-detects user's local timezone, updates every second (responsive on all devices)
    - API endpoints: `/api/metrics`, `/api/trades`, `/api/equity-curve`, `/api/portfolio`, `/api/health`
    - **Railway Deployment**: Can run as separate service using `start_dashboard.py` (see `RAILWAY_DASHBOARD_SETUP.md`)
- **OMNIX Personal Assistant Premium V6.4** - Sistema de configuración personalizada por usuario vía Telegram:
    - **UserSettingsService**: Gestión de preferencias de trading por usuario con persistencia en PostgreSQL.
    - **5 Perfiles de Riesgo**: ultra_conservative, conservative, moderate, aggressive, institutional (Goldman-Sachs style).
    - **Límites Personalizados**: min/max trade USD, límite diario, máximo posiciones, % máx del portfolio.
    - **Comandos Telegram Premium**: `/miconfig`, `/perfil`, `/limites`, `/proteccion`, `/estrategias`, `/cryptos`, `/autotrading`, `/pausar`, `/reanudar`, `/onboarding`.
    - **Procesamiento Lenguaje Natural**: Entiende peticiones como "quiero ser más agresivo", "máximo $500 por trade", "pausa el trading".
    - **Auto-Protección**: Pausa automática al alcanzar límite de pérdida diaria (configurable).
    - **Integración PaperTradingManager**: Valida trades contra límites del usuario antes de ejecutar.
    - **Tabla**: `user_settings` en PostgreSQL con JSON para configuración flexible.

#### System Design Choices
- **Modular Architecture**: 75+ specialized Python modules organized into `omnix_core/`, `omnix_services/`, `omnix_testing/`.
- **Centralized Database Layer**: All database logic in `omnix_services/database_service/` with 33 code-managed tables and 22+ DAL methods. Schema migrations managed transactionally.
- **Unified Configuration**: Centralized `env_manager.py` for environment variables.
- **Deployment**: 24/7 operation on Railway (Production) and Replit (Development).

### External Dependencies

#### APIs & Services
- **Kraken Exchange**: Primary for market data, account info, order execution.
- **Google Gemini**: Gemini 2.0 Flash (primary AI model).
- **OpenAI**: GPT-4o, Whisper (for AI services).
- **Anthropic Claude**: Optional AI fallback.
- **Stripe**: Payment processing.
- **CoinGecko API**: Backup price data.
- **ANU QRNG API**: For true quantum randomness.

#### Databases
- **PostgreSQL (Railway)**: Main relational database hosted on Railway with 33 code-managed tables for core operations, risk, derivatives, community, signals, and video transcript caching. Uses `psycopg3` driver with SSL.
- **Redis (Railway)**: External in-memory cache for persistent state management, conversation history, market data caching, and rate limiting.

#### Key Python Libraries
- `numpy`, `scipy`, `ccxt`: Core trading and mathematical operations.
- `google-generativeai`, `openai`: AI model integration.
- `python-telegram-bot`: Telegram integration.
- `psycopg` (v3), `redis`: Database drivers.
- `requests`, `websockets`, `aiohttp`, `httpx`: HTTP and WebSocket communication.
- `pypqc`: Post-quantum cryptography implementation.
- `pandas`, `plotly`, `kaleido`, `reportlab`, `PyPDF2`: Professional testing and reporting.