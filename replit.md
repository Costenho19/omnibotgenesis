# OMNIX V6.0 ULTRA - Automated Trading System

## Overview
OMNIX V6.0 ULTRA is an enterprise-grade automated cryptocurrency trading system designed for 24/7 operation on Kraken Exchange. It currently operates in PAPER TRADING mode with $1,000,000 virtual capital, employing institutional-grade position sizing to generate credible track records for investor presentations. The system integrates AI, post-quantum cryptography, and real-time market analysis to deliver sophisticated automated trading, featuring advanced strategy modules like ARES V1 and V2, and multi-exchange arbitrage. The project's primary goal is to secure seed funding ($400K at a $2.5M valuation) by demonstrating robust performance and a professional backtesting infrastructure.

## User Preferences
User Communication Preference: Simple, everyday language (Spanish primary).

## System Architecture
OMNIX V6.0 ULTRA is built around a robust, modular architecture designed for high performance, security, and intelligent automation, undergoing significant refactoring to an enterprise-grade structure.

### UI/UX Decisions
- **Market Dashboard**: Institutional-grade dashboard with real-time Kraken data for 6 cryptocurrencies (BTC, ETH, SOL, XRP, ADA, DOGE), market sentiment, top gainers/losers, 24h volumes, and visual trends.
- **Reporting**: Generates professional, investor-ready PDF reports (25-35 pages) with executive summaries, methodology, results, risk analysis, and trade logs, utilizing Plotly for 5 institutional-quality visualizations (Equity Curve, Drawdown Chart, Trade Distribution, Monthly Returns Heatmap, Rolling Sharpe Ratio).

### Technical Implementations
- **Core Strategies**: Utilizes 9 distinct modules including Monte Carlo Simulations, Black Swan Detection, Kelly Criterion Position Sizing, HMM Regime Detection, Dual Kalman Filter, Quantum Momentum Strategy, Sharia Compliance Filtering, Order Book Analysis, and Sentiment Analysis.
- **ARES Quantum Protocols**:
    - **ARES V1 (Swing Trading)**: 74-82% win rate using a 3-layer quantum architecture and 6 institutional indicators.
    - **ARES V2 (Scalping M1)**: 85% win rate for 1-minute ultra-fast scalping with 5 precision indicators.
    - **Kill-Switch Protection**: Multi-layer fail-safe for real trading, including critical fail-safes and signal-based blocking.
- **AI & Machine Learning**:
    - **Conversational AI**: Uses Google Gemini 2.0 Flash (primary), GPT-4o, and Claude (fallbacks). It's stateless, Redis-backed, and maintains conversation memory. Provides natural, adaptive, context-aware responses and "Cerebro Conversacional" for self-explaining AI reasoning.
    - **Auto-Learning System**: Processes external data (e.g., YouTube trading videos) to propose strategy parameter changes.
- **Coherence Engine V5.4 ULTRA**: Validates agreement between trading strategies using a 6-Tier Veto System.
- **AI Risk Guardian V5.4**: Real-time risk supervision with Overtrading Detection, Drawdown Protection, Revenge Trading Detection, and Capital Protection.
- **Auto-Optimization Engine**: Continuously improves strategies via Genetic Algorithm, A/B Testing, and Auto-Adjustment.
- **Professional Testing & Validation System (V6.0)**: Includes Historical Events Validator (10 critical events), Strategy Comparator (ARES vs Buy & Hold), and a Premium Validation Suite for investor-ready reports.
- **Multi-Exchange Arbitrage V6.0**: Institutional arbitrage across 8 exchanges (Kraken, Binance, Coinbase, Bybit, KuCoin, OKX, Gate.io, Bitfinex).

### Feature Specifications
- **Trading Modes**: Paper Trading, Real Trading (with post-quantum signed orders), and Backtesting.
- **Quantum Enhancements**: Integrates QRNG and QAOA for portfolio optimization.
- **Community Intelligence**: Signal Contribution (crowdsourcing alpha), Community Feedback, Reward System.

### System Design Choices
- **Modular Architecture**: Transformed from a monolith to a modular system with 75+ specialized Python modules, significantly reducing `main.py` from 15,175 to 617 lines.
- **Centralized Database Layer (Nov 26, 2025 - LIMPIEZA FINAL COMPLETADA)**: All database logic consolidated in `omnix_services/database_service/` with 24 tables and 22 DAL methods. **6 Community Intelligence modules refactored to use centralized database_service** (2 full DAL: feedback_manager, risk_guardian; 2 mixtos: signal_contribution, community_analyzer; 2 conservadores: reward_system, community_dashboard) eliminating **~410 lines of duplicate code** (~290 _get_connection + ~120 _init_tables_DEPRECATED). Dependency injection configured in enterprise_bot.py (único entry point). **signal_contribution.py 100% limpio** (610→500 líneas). Auditoría final: **24 tablas SOLO en database_service.py** (única fuente de verdad). **100% centralized** (mix of DAL + conservative patterns). See `docs/cambios_ivan/2025-11-26_centralizacion_database.md` for details.
- **Database Schema Modernization FASE 1 (Nov 26, 2025)**: Conservative improvements to users table following 3NF normalization. Added email, is_active, updated_at columns; changed total_profit from REAL to NUMERIC(18,8) for financial precision; added CHECK constraints. Created new user_contacts table for multi-channel contact management (WhatsApp, email, Telegram, phone, SMS) with FK to users. 4 new DAL methods: add_user_contact(), get_user_contacts(), verify_user_contact(), set_primary_contact(). 100% backward compatible with automatic migration for both fresh deployments and upgrades. See `database.md` section 9 for complete details.
- **Unified Configuration**: Centralized `env_manager.py` handles environment variables with precedence (Replit Secrets > .env.local > defaults), type validation, and secure logging.
- **Deployment**: Designed for 24/7 operation on Railway (Production) and Replit (Development) with a unified `python -u main.py` entry point.
- **Root Directory Cleanup**: Reduced Python files in the root from 24 to 2.

## External Dependencies

### APIs & Services
- **Kraken Exchange**: Primary for market data, account info, order execution.
- **Google Gemini**: Gemini 2.0 Flash (primary AI model).
- **OpenAI**: GPT-4o, Whisper (for AI services).
- **Anthropic Claude**: Optional AI fallback.
- **Stripe**: Payment processing for subscriptions.
- **CoinGecko API**: Backup price data.

### Databases
- **PostgreSQL (Neon)**: Main relational database with 24 tables organized in:
  - Core System (9 tables): users, user_contacts, prices, trades, analysis, conversations, whatsapp_messages, sharia_validations, balance_history
  - Paper Trading (2 tables): paper_trading_balances, paper_trading_trades
  - Conversational Brain (3 tables): trade_reasonings, trade_evaluations, pending_evaluations
  - Community Intelligence (5 tables): community_feedback, strategy_votes, improvement_proposals, user_contributions, detected_patterns
  - Signal Contribution (4 tables): community_signals, signal_executions, signal_votes, alpha_leaderboard
  - Risk Guardian (1 table): risk_guardian_events
  - **Centralized Access**: All queries via `omnix_services/database_service/database_service.py` (2,360 lines, 22 DAL methods: 13 original + 5 Community Intelligence + 4 User Contacts)
  - **FASE 1 Modernization (Nov 26, 2025)**: Improved users table (NUMERIC precision, email, is_active, updated_at) + new user_contacts table (3NF normalization). 100% backward compatible.
- **Redis**: In-memory data store for state management, conversation history, caching.

### Key Python Libraries
- `numpy`, `scipy`, `ccxt`: Core trading and mathematical operations.
- `google-generativeai`, `openai`: AI model integration.
- `python-telegram-bot`: Telegram integration.
- `psycopg2-binary`, `redis`: Database drivers.
- `requests`, `websockets`, `aiohttp`, `httpx`: HTTP and WebSocket communication.
- `pypqc`: Post-quantum cryptography implementation.
- `pandas`, `plotly`, `kaleido`, `reportlab`, `PyPDF2`: Professional testing and reporting.