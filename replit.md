# OMNIX V6.0 ULTRA - Automated Trading System

### Overview
OMNIX V6.0 ULTRA is an enterprise-grade automated cryptocurrency trading system for 24/7 operation on the Kraken Exchange. It operates in paper trading mode with substantial virtual capital to build a credible track record for investor presentations. The system integrates AI, post-quantum cryptography, and real-time market analysis, featuring advanced strategy modules like ARES V1 and V2, and multi-exchange arbitrage. The project aims to secure seed funding by demonstrating robust performance, including modules for institutional compliance, derivatives trading, and enhanced investor reporting.

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
OMNIX V6.0 ULTRA is built around a robust, modular architecture designed for high performance, security, and intelligent automation.

#### UI/UX Decisions
- **Market Dashboard**: Institutional-grade dashboard with real-time Kraken data for 6 cryptocurrencies, market sentiment, top gainers/losers, 24h volumes, and visual trends.
- **Reporting**: Generates professional, investor-ready PDF reports (25-35 pages) with executive summaries, methodology, results, risk analysis, and trade logs, utilizing Plotly for 5 institutional-quality visualizations.

#### Technical Implementations
- **Core Strategies**: 9 distinct modules including Monte Carlo Simulations, Black Swan Detection, Kelly Criterion, HMM Regime Detection, Dual Kalman Filter, Adaptive Momentum, Sharia Compliance, Order Book Analysis, and Sentiment Analysis.
- **ARES Institutional Protocols**:
    - **ARES V1 (Swing Trading)**: 55-65% win rate target using a 3-layer institutional architecture and 6 professional indicators.
    - **ARES V2 (Scalping M1)**: 60-70% win rate target for 1-minute scalping with 5 precision indicators, ultra-tight stop loss, multi-level take profits, and kill-switch protection.
    - **Kill-Switch Protection**: Multi-layer fail-safe for real trading, including critical fail-safes and signal-based blocking.
- **Professional Testing & Validation System**: Includes Walk-Forward Analysis, Monte Carlo Stress Testing, Market Regime Testing, Realistic Cost Modeling, and Investor Report Generation with a grade system.
- **AI & Machine Learning**: Conversational AI (Google Gemini 2.0 Flash primary, GPT-4o, Claude fallbacks) with "Cerebro Conversacional" for self-explaining AI reasoning and an Auto-Learning System for strategy parameter optimization.
- **Quantum Physics Validation System**: PhD+ level scientific accuracy with 31 verified formulas and quantum credibility scoring, including advanced formulas for Amplitude Damping, Quantum Sharpe Ratio, and Quantum Criticality.
- **Risk Management & Protection**:
    - **Coherence Engine V5.4 ULTRA**: Validates agreement between trading strategies using a 6-Tier Veto System.
    - **AI Risk Guardian V5.4**: Real-time risk supervision (Overtrading, Drawdown, Revenge Trading Detection, Capital Protection).
    - **Risk Management System (RMS) V6.0**: Institutional-grade risk control with LimitsEngine, PositionMonitor, CircuitBreaker, AlertDispatcher, and RiskDashboard.
    - **Auto-Optimization Engine**: Continuously improves strategies via Genetic Algorithm, A/B Testing, and Auto-Adjustment.
    - **Multi-Exchange Arbitrage V6.0**: Institutional arbitrage across 8 exchanges.
    - **Institutional Compliance Suite**: Includes InstitutionalStressSuite, InstitutionalAuditLogger, and a DeadManSwitch.
    - **Premium Institutional Upgrade**: Features an Institutional Response Formatter, Reactivation Engine, and Portfolio Summary.
    - **Institutional Market Infrastructure**: Includes USD Risk Calculator, Exchange Latency Monitor, Orderbook Depth Analyzer, and Liquidity Monitor.
    - **Institutional Optimization Suite**: Features Cascade Protection, Adaptive Regime Switcher, and Pitch Deck Generator.
- **Derivatives Trading Module**: Central orchestrator (`DerivativesManager`) for perpetuals trading with paper/real modes, `MarginEngine`, `KrakenFuturesClient`, `HedgingService`, `FundingArbitrageAnalyzer`, and Telegram integration.
- **Trading Modes**: Paper Trading, Real Trading (with post-quantum signed orders), and Backtesting.
- **Quantum Enhancements**: ANU QRNG for true quantum randomness and D-Wave Leap for real quantum annealing for portfolio optimization, with classical fallback.
- **Community Intelligence**: Signal contribution, community feedback, and reward system.
- **Telegram Message Splitting**: Implemented intelligent message splitting for texts exceeding 4096 characters, respecting structure and adding "(1/N)" headers with a delay to avoid rate limits.

#### System Design Choices
- **Modular Architecture**: 75+ specialized Python modules organized into `omnix_core/`, `omnix_services/`, `omnix_testing/`.
- **Centralized Database Layer**: All database logic in `omnix_services/database_service/` with 28 active tables and 22+ DAL methods. Schema migrations managed transactionally with advisory locks and automatic rollback.
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
- **PostgreSQL (Neon/Railway)**: Main relational database with 28 active tables for core operations, risk/monitoring, and derivatives. Fully operational with foreign keys, indices, and transactional migrations. User auto-registration implemented with UPSERT pattern.
- **Redis (Railway)**: External in-memory cache connected via TCP proxy for persistent state management, conversation history, market data caching, and rate limiting.

#### Key Python Libraries
- `numpy`, `scipy`, `ccxt`: Core trading and mathematical operations.
- `google-generativeai`, `openai`: AI model integration.
- `python-telegram-bot`: Telegram integration.
- `psycopg2-binary`, `redis`: Database drivers.
- `requests`, `websockets`, `aiohttp`, `httpx`: HTTP and WebSocket communication.
- `pypqc`: Post-quantum cryptography implementation.
- `pandas`, `plotly`, `kaleido`, `reportlab`, `PyPDF2`: Professional testing and reporting.