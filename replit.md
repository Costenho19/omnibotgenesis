# OMNIX V6.2 ULTRA - Automated Trading System

### Overview
OMNIX V6.2 ULTRA is an enterprise-grade automated cryptocurrency trading system designed for 24/7 operation on the Kraken Exchange. It operates in paper trading mode with substantial virtual capital to build a credible track record for investor presentations. The system integrates AI, post-quantum cryptography, real-time market analysis, Non-Markovian temporal memory, and features Memory-Enhanced Risk Management—a predictive risk system that uses temporal memory patterns to anticipate regime transitions. The project aims to secure seed funding by demonstrating robust performance, including modules for institutional compliance, derivatives trading, and enhanced investor reporting, supporting over 50 cryptocurrencies.

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
- **Market Dashboard**: Institutional-grade dashboard with real-time Kraken data for 6 cryptocurrencies, market sentiment, top gainers/losers, 24h volumes, and visual trends.
- **Reporting**: Generates professional, investor-ready PDF reports (25-35 pages) with executive summaries, methodology, results, risk analysis, and trade logs, utilizing Plotly for 5 institutional-quality visualizations.

#### Technical Implementations
- **Core Strategies**: Includes Monte Carlo Simulations, Black Swan Detection, Kelly Criterion, HMM Regime Detection, Dual Kalman Filter, Quantum Momentum, ARES V1/V2, Non-Markovian Kernel, and Order Book Analysis.
- **Non-Markovian Memory Kernel V6.1**: Captures temporal dependencies with K(t-s) = exp(-|t-s|/τ)[1 + ε cos(Ω(t-s))], detecting regime transitions, cyclical patterns, and memory coherence.
- **ARES Institutional Protocols**: ARES V1 (Swing Trading) and ARES V2 (Scalping M1) with target win rates and multi-layer Kill-Switch Protection.
- **Professional Testing & Validation System**: Features Walk-Forward Analysis, Monte Carlo Stress Testing, Market Regime Testing, Realistic Cost Modeling, and Investor Report Generation.
- **AI & Machine Learning**: Conversational AI (Google Gemini 2.0 Flash primary, GPT-4o, Claude fallbacks) with "Cerebro Conversacional" for self-explaining AI reasoning and an Auto-Learning System for strategy parameter optimization.
- **Quantum Physics Validation System**: PhD+ level scientific accuracy with 24 verified formulas and quantum credibility scoring, including advanced formulas for Amplitude Damping, Quantum Sharpe Ratio, and Quantum Criticality.
- **Risk Management & Protection**:
    - **Coherence Engine V5.4 ULTRA**: Validates agreement between trading strategies using a 6-Tier Veto System.
    - **AI Risk Guardian V5.4**: Real-time risk supervision (Overtrading, Drawdown, Revenge Trading Detection, Capital Protection).
    - **Risk Management System (RMS) V6.2 MEMORY-ENHANCED**: Institutional-grade risk control with LimitsEngine, PositionMonitor, CircuitBreaker, AlertDispatcher, RiskDashboard, and MemoryRiskAdapter. Features predictive risk assessment using Non-Markovian temporal patterns (coherence, transition, divergence, cyclical risks).
    - **Auto-Optimization Engine**: Continuously improves strategies via Genetic Algorithm, A/B Testing, and Auto-Adjustment.
    - **Multi-Exchange Arbitrage V6.0**: Institutional arbitrage across 8 exchanges.
    - **Institutional Compliance Suite**: Includes InstitutionalStressSuite, InstitutionalAuditLogger, and a DeadManSwitch.
- **Derivatives Trading Module**: Orchestrates perpetuals trading with paper/real modes, `MarginEngine`, `KrakenFuturesClient`, `HedgingService`, `FundingArbitrageAnalyzer`, and Telegram integration.
- **Trading Modes**: Paper Trading, Real Trading (with post-quantum signed orders), and Backtesting.
- **Quantum Enhancements**: ANU QRNG for true quantum randomness.
- **Strategic Honesty System**: Provides CEO-style, data-driven responses, avoids exposing raw limitations, and reframes questions confidently.
- **Leverage Validation**: Automatically detects and rejects leverage requests exceeding 5x.
- **Multi-Crypto Support**: Supports 50+ cryptocurrencies with primary Kraken and fallback CoinGecko data sources.
- **Robust Market Data System**: Uses 3-source fallback (Kraken Auth → Kraken Public → CoinGecko) with JSON validation and timeouts.

#### System Design Choices
- **Modular Architecture**: 75+ specialized Python modules organized into `omnix_core/`, `omnix_services/`, `omnix_testing/`.
- **Centralized Database Layer**: All database logic in `omnix_services/database_service/` with 28 active tables and 22+ DAL methods. Schema migrations managed transactionally.
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
- **PostgreSQL (Neon/Railway)**: Main relational database with 28 active tables for core operations, risk/monitoring, and derivatives.
- **Redis (Railway)**: External in-memory cache for persistent state management, conversation history, market data caching, and rate limiting.

#### Key Python Libraries
- `numpy`, `scipy`, `ccxt`: Core trading and mathematical operations.
- `google-generativeai`, `openai`: AI model integration.
- `python-telegram-bot`: Telegram integration.
- `psycopg2-binary`, `redis`: Database drivers.
- `requests`, `websockets`, `aiohttp`, `httpx`: HTTP and WebSocket communication.
- `pypqc`: Post-quantum cryptography implementation.
- `pandas`, `plotly`, `kaleido`, `reportlab`, `PyPDF2`: Professional testing and reporting.