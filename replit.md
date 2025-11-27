# OMNIX V6.0 ULTRA - Automated Trading System

## Overview
OMNIX V6.0 ULTRA is an enterprise-grade automated cryptocurrency trading system for 24/7 operation on Kraken Exchange. It operates in paper trading mode with $1,000,000 virtual capital, using institutional-grade position sizing to build a credible track record for investor presentations. The system integrates AI, post-quantum cryptography, and real-time market analysis, featuring advanced strategy modules like ARES V1 and V2, and multi-exchange arbitrage. The project aims to secure seed funding by demonstrating robust performance and a professional backtesting infrastructure.

## User Preferences
User Communication Preference: Simple, everyday language (Spanish primary).

## Recent Changes
- **2025-11-27**: Added Professional Validation Suite (`omnix_testing/professional_validator.py`) with Walk-Forward Analysis, Monte Carlo Stress Testing, Market Regime Testing, and Realistic Cost Modeling.
- **2025-11-27**: Created ARES Strategy Validation script (`omnix_testing/validate_ares_strategies.py`) for institutional-grade strategy backtesting.
- **2025-11-27**: Fixed LSP error in `omnix_core/strategies/ares_v1.py` (numpy float conversion).

## System Architecture
OMNIX V6.0 ULTRA is built around a robust, modular architecture designed for high performance, security, and intelligent automation, undergoing significant refactoring to an enterprise-grade structure.

### UI/UX Decisions
- **Market Dashboard**: Institutional-grade dashboard with real-time Kraken data for 6 cryptocurrencies, market sentiment, top gainers/losers, 24h volumes, and visual trends.
- **Reporting**: Generates professional, investor-ready PDF reports (25-35 pages) with executive summaries, methodology, results, risk analysis, and trade logs, utilizing Plotly for 5 institutional-quality visualizations (Equity Curve, Drawdown Chart, Trade Distribution, Monthly Returns Heatmap, Rolling Sharpe Ratio).

### Technical Implementations

#### Core Strategies
- 9 distinct modules including Monte Carlo Simulations, Black Swan Detection, Kelly Criterion Position Sizing, HMM Regime Detection, Dual Kalman Filter, Quantum Momentum Strategy, Sharia Compliance Filtering, Order Book Analysis, and Sentiment Analysis.

#### ARES Quantum Protocols
- **ARES V1 (Swing Trading)**: 74-82% win rate target using a 3-layer quantum architecture and 6 institutional indicators.
  - Capa 1: Quantum Structure Filter (QSF) - Noise filtering
  - Capa 2: Quantum Institutional Signals (QIS) - 6 professional signals
  - Capa 3: Quantum Execution Engine (QEX) - Hedge fund-style execution
- **ARES V2 (Scalping M1)**: 85% win rate target for 1-minute ultra-fast scalping with 5 precision indicators.
  - Ultra-tight stop loss (-0.28%)
  - Multi-level take profits (+0.85%, +1.70%, +2.90%)
  - Kill-switch protection after 3 consecutive losses
- **Kill-Switch Protection**: Multi-layer fail-safe for real trading, including critical fail-safes and signal-based blocking.

#### Professional Testing & Validation System (V6.0 - NEW)
Located in `omnix_testing/`:
- **Walk-Forward Analysis** (`professional_validator.py`): 5-iteration rolling validation preventing overfitting with In-Sample/Out-of-Sample splits.
- **Monte Carlo Stress Testing**: 100+ simulations with price perturbation (2-5%) to test robustness.
- **Market Regime Testing**: 5 market regimes (Bull Run, Bear Market, Sideways, High Volatility, Recovery).
- **Realistic Cost Modeling**: Kraken fees (maker 0.16%, taker 0.26%), 5bps slippage, 10bps spread.
- **Investor Report Generation**: Honest metrics with grade system (A+ to F) and automatic caveats.
- **ARES Validation Script** (`validate_ares_strategies.py`): Direct validation of ARES V1 and V2 strategies.

#### AI & Machine Learning
- **Conversational AI**: Uses Google Gemini 2.0 Flash (primary), GPT-4o, and Claude (fallbacks). Stateless, Redis-backed, maintains conversation memory. Provides natural, adaptive, context-aware responses and "Cerebro Conversacional" for self-explaining AI reasoning.
- **Auto-Learning System**: Processes external data (e.g., YouTube trading videos) to propose strategy parameter changes.

#### Quantum Physics Validation System
Located in `omnix_core/quantum/`:
- **Quantum Physics Validator V4.0** (`physics_validator.py`): PhD+ level scientific accuracy with 24 verified formulas, 75+ detection keywords, and quantum credibility scoring.
- **Quantum Testing Framework** (`testing_framework.py`): 24 test cases validating mathematical correctness across foundational, derivations, PhD-level, and ultra-advanced formulas.
- **Response Confidence System**: A+ to F grades, confidence levels (ALTA/MEDIA/BAJA), automatic caveats for investor transparency.

#### Risk Management & Protection
- **Coherence Engine V5.4 ULTRA**: Validates agreement between trading strategies using a 6-Tier Veto System.
- **AI Risk Guardian V5.4**: Real-time risk supervision with Overtrading Detection, Drawdown Protection, Revenge Trading Detection, and Capital Protection.
- **Risk Management System (RMS) V6.0**: Institutional-grade risk control with LimitsEngine (pre-trade validation), PositionMonitor (real-time exposure), CircuitBreaker (automatic trading halt), AlertDispatcher (multi-channel notifications), and RiskDashboard (investor-ready reports).
- **Auto-Optimization Engine**: Continuously improves strategies via Genetic Algorithm, A/B Testing, and Auto-Adjustment.
- **Multi-Exchange Arbitrage V6.0**: Institutional arbitrage across 8 exchanges.

### Feature Specifications
- **Trading Modes**: Paper Trading ($1M virtual), Real Trading (with post-quantum signed orders), and Backtesting.
- **Quantum Enhancements**:
  - **ANU QRNG**: True quantum randomness from Australian National University for Monte Carlo simulations.
  - **QAOA**: Classical simulation for portfolio optimization, ready for D-Wave Leap integration.
- **Community Intelligence**: Signal contribution, community feedback, and reward system.

### System Design Choices
- **Modular Architecture**: 75+ specialized Python modules organized in `omnix_core/`, `omnix_services/`, `omnix_testing/`.
- **Centralized Database Layer**: All database logic in `omnix_services/database_service/` with 23 tables and 22 DAL methods.
- **Unified Configuration**: Centralized `env_manager.py` handles environment variables with precedence, type validation, and secure logging.
- **Deployment**: 24/7 operation on Railway (Production) and Replit (Development).

## External Dependencies

### APIs & Services
- **Kraken Exchange**: Primary for market data, account info, order execution.
- **Google Gemini**: Gemini 2.0 Flash (primary AI model).
- **OpenAI**: GPT-4o, Whisper (for AI services).
- **Anthropic Claude**: Optional AI fallback.
- **Stripe**: Payment processing for subscriptions.
- **CoinGecko API**: Backup price data.
- **ANU QRNG API**: For true quantum randomness.

### Databases
- **PostgreSQL (Neon)**: Main relational database with 26 tables, accessed via `omnix_services/database_service/database_service.py`.
- **Redis**: In-memory data store for state management, conversation history, caching.

### Key Python Libraries
- `numpy`, `scipy`, `ccxt`: Core trading and mathematical operations.
- `google-generativeai`, `openai`: AI model integration.
- `python-telegram-bot`: Telegram integration.
- `psycopg2-binary`, `redis`: Database drivers.
- `requests`, `websockets`, `aiohttp`, `httpx`: HTTP and WebSocket communication.
- `pypqc`: Post-quantum cryptography implementation.
- `pandas`, `plotly`, `kaleido`, `reportlab`, `PyPDF2`: Professional testing and reporting.

## Key File Locations
- **Main Entry**: `main.py`
- **Strategies**: `omnix_core/strategies/ares_v1.py`, `omnix_core/strategies/ares_v2.py`
- **Quantum Validation**: `omnix_core/quantum/physics_validator.py`, `omnix_core/quantum/testing_framework.py`
- **Professional Testing**: `omnix_testing/professional_validator.py`, `omnix_testing/validate_ares_strategies.py`
- **Database Service**: `omnix_services/database_service/database_service.py`
- **Risk Management**: `omnix_services/risk_management/limits_engine.py`

## Roadmap Q1 2026 (Planned)
- Database Migration to SQLModel + Alembic + Flask API REST
- D-Wave Leap Integration for real quantum optimization
- NYSE/NASDAQ market integration (dual-market trading)
- Production deployment with real trading
- Mobile app for investor dashboard
