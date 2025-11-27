# OMNIX V6.0 ULTRA - Automated Trading System

## Overview
OMNIX V6.0 ULTRA is an enterprise-grade automated cryptocurrency trading system for 24/7 operation on Kraken Exchange. It operates in paper trading mode with $1,000,000 virtual capital, using institutional-grade position sizing to build a credible track record for investor presentations. The system integrates AI, post-quantum cryptography, and real-time market analysis, featuring advanced strategy modules like ARES V1 and V2, and multi-exchange arbitrage. The project aims to secure seed funding by demonstrating robust performance and a professional backtesting infrastructure.

## User Preferences
User Communication Preference: Simple, everyday language (Spanish primary).

## System Architecture
OMNIX V6.0 ULTRA is built around a robust, modular architecture designed for high performance, security, and intelligent automation, undergoing significant refactoring to an enterprise-grade structure.

### UI/UX Decisions
- **Market Dashboard**: Institutional-grade dashboard with real-time Kraken data for 6 cryptocurrencies, market sentiment, top gainers/losers, 24h volumes, and visual trends.
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
- **Risk Management System (RMS) V6.0**: Institutional-grade risk control system with LimitsEngine (pre-trade validation), PositionMonitor (real-time exposure), CircuitBreaker (automatic trading halt), AlertDispatcher (multi-channel notifications), and RiskDashboard (investor-ready reports).
- **Auto-Optimization Engine**: Continuously improves strategies via Genetic Algorithm, A/B Testing, and Auto-Adjustment.
- **Professional Testing & Validation System (V6.0)**: Includes Historical Events Validator, Strategy Comparator, and a Premium Validation Suite for investor-ready reports.
- **Multi-Exchange Arbitrage V6.0**: Institutional arbitrage across 8 exchanges.

### Feature Specifications
- **Trading Modes**: Paper Trading, Real Trading (with post-quantum signed orders), and Backtesting.
- **Quantum Enhancements**:
  - **ANU QRNG (Quantum Random Number Generator)**: Utilizes true quantum randomness from Australian National University for Monte Carlo simulations.
  - **QAOA (Quantum Approximate Optimization Algorithm)**: Classical simulation for portfolio optimization, ready for D-Wave Leap integration.
  - **Quantum Physics Validator V4.0 INVENCIBLE**: PhD+ level scientific accuracy module with 24 verified formulas, 75+ detection keywords, response validation, and a quantum credibility score.
  - **Quantum Testing Framework**: Validates AI responses for mathematical correctness across 24 test cases.
  - **Response Confidence System**: Provides transparency metadata for investor-facing responses with confidence levels and automatic caveats.
- **Community Intelligence**: Features signal contribution, community feedback, and a reward system.

### System Design Choices
- **Modular Architecture**: Transformed from a monolith to a modular system with 75+ specialized Python modules.
- **Centralized Database Layer**: All database logic consolidated in `omnix_services/database_service/` with 23 tables and 22 DAL methods, ensuring a single source of truth and reducing duplicate code.
- **Database Migration to ORM (Planned)**: Comprehensive migration plan from psycopg2 to SQLModel + Alembic + Flask API REST with a 7-phase roadmap, zero downtime strategy, and extensive parity testing.
- **Database Schema Modernization FASE 1**: Conservative improvements to the `users` table (3NF normalization, `email`, `is_active`, `updated_at`, `NUMERIC` precision for profit) and a new `user_contacts` table for multi-channel contact management.
- **Database Optimization: Integridad & Escalabilidad**: Implemented 13 FK Constraints with `ON DELETE CASCADE`, 20 performance indices, 7 `CHECK` constraints, and a TTL Cleanup system for 11 tables to prevent infinite growth.
- **Unified Configuration**: Centralized `env_manager.py` handles environment variables with precedence, type validation, and secure logging.
- **Deployment**: Designed for 24/7 operation on Railway (Production) and Replit (Development).
- **Root Directory Cleanup**: Reduced Python files in the root from 24 to 2.

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
- **PostgreSQL (Neon)**: Main relational database with 26 tables, accessed via `omnix_services/database_service/database_service.py`. Includes tables for Core System, Paper Trading, Conversational Brain, Community Intelligence, Signal Contribution, Risk Guardian, and Risk Management System.
- **Redis**: In-memory data store for state management, conversation history, caching.

### Key Python Libraries
- `numpy`, `scipy`, `ccxt`: Core trading and mathematical operations.
- `google-generativeai`, `openai`: AI model integration.
- `python-telegram-bot`: Telegram integration.
- `psycopg2-binary`, `redis`: Database drivers.
- `requests`, `websockets`, `aiohttp`, `httpx`: HTTP and WebSocket communication.
- `pypqc`: Post-quantum cryptography implementation.
- `pandas`, `plotly`, `kaleido`, `reportlab`, `PyPDF2`: Professional testing and reporting.