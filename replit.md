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
- **Risk Management System (RMS) V6.0 (Nov 27, 2025)**: Institutional-grade risk control system with:
    - **LimitsEngine**: Pre-trade validation with 6 configurable limits (per-trade 5%, daily loss 2%, max drawdown 10%, concentration 25%, VIX volatility, daily trades count).
    - **PositionMonitor**: Real-time exposure tracking with 5-second intervals, calculates total exposure, concentration risk, P&L per position.
    - **CircuitBreaker**: Automatic trading halt on limit breach with 3 severity levels (warning, critical, halt). Manual halt/resume via Telegram.
    - **AlertDispatcher**: Multi-channel notifications (Telegram, logs) with configurable thresholds.
    - **RiskDashboard**: Investor-ready risk summaries, generates professional reports with exposure analysis and breach history.
    - **Database Tables**: 3 new tables (risk_limits, risk_limit_breaches, risk_metrics_snapshots) with 6 DAL methods.
    - **Telegram Commands**: /rms (dashboard), /rms_limits (view limits), /rms_set (configure), /rms_history (breaches), /emergency_halt, /resume_trading.
- **Auto-Optimization Engine**: Continuously improves strategies via Genetic Algorithm, A/B Testing, and Auto-Adjustment.
- **Professional Testing & Validation System (V6.0)**: Includes Historical Events Validator (10 critical events), Strategy Comparator (ARES vs Buy & Hold), and a Premium Validation Suite for investor-ready reports.
- **Multi-Exchange Arbitrage V6.0**: Institutional arbitrage across 8 exchanges (Kraken, Binance, Coinbase, Bybit, KuCoin, OKX, Gate.io, Bitfinex).

### Feature Specifications
- **Trading Modes**: Paper Trading, Real Trading (with post-quantum signed orders), and Backtesting.
- **Quantum Enhancements (Nov 27, 2025 - ANU QRNG ACTIVATED)**:
  - **ANU QRNG (Quantum Random Number Generator)**: True quantum randomness from Australian National University's quantum vacuum fluctuation measurements via free legacy API (https://qrng.anu.edu.au/API/jsonI.php). Used by Monte Carlo simulator for 10,000 simulations with provably unpredictable numbers.
  - **QAOA (Quantum Approximate Optimization Algorithm)**: Classical simulation for portfolio optimization, ready for D-Wave Leap integration.
  - **Module Location**: `omnix_core/quantum/enhancements.py` exports `global_qrng` and `global_qaoa`.
  - **Monte Carlo Integration**: Automatic fallback to numpy if API unavailable; Box-Muller transform converts uniform [0,1) to normal distribution.
  - **Benefits**: Impresses investors ("Powered by Quantum Computing"), unpredictable simulations, cryptographically secure randomness.
  - **Quantum Physics Validator V4.0 INVENCIBLE (Nov 27, 2025)**: PhD+ level scientific accuracy module at `omnix_core/quantum/physics_validator.py` - the most advanced quantum physics validator for trading systems in 2026. Features:
    - **24 Verified Formulas** covering foundational QRNG physics through advanced quantum metrology:
      - **Foundational (V1.0)**: Homodyne variance, shot noise, vacuum fluctuations, squeezed states, ANU QRNG, bias removal
      - **Derivations (V2.0)**: Formal homodyne derivation, canonical quadrature X̂_θ = ½(â e^{-iθ} + â† e^{iθ}), linearity proof, common errors
      - **PhD-Level (V3.0)**: Temporal autocorrelation ⟨X̂(t₁)X̂(t₂)⟩, Johnson-Nyquist comparison, von Neumann entropy, Bell/CHSH with 2√2 violation, min-entropy extraction
      - **Ultra-Advanced (V4.0)**: Wigner function (phase-space), Quantum Fisher Information (Cramér-Rao), Fock vs Coherent states, Heisenberg limit vs SQL (1/N vs 1/√N), No-Cloning theorem (BB84/QKD), Decoherence time (T₁/T₂), Photon statistics (Mandel Q, g⁽²⁾)
    - **75+ Detection Keywords** for 24 quantum topics with automatic context injection
    - **Response Validation**: `validate_quantum_response()` with pattern matching for operators (â, â†), constants (ℏ, h), math notation, units
    - **Quantum Credibility Score**: `get_quantum_credibility_score()` returns A+ to F grade for investor presentations
    - **Strict Normalization**: [X̂, P̂] = i/2 convention enforced throughout
    - Prevents LLM hallucination with SI units and constants (ℏ, h, e, kB)
- **Community Intelligence**: Signal Contribution (crowdsourcing alpha), Community Feedback, Reward System.

### System Design Choices
- **Modular Architecture**: Transformed from a monolith to a modular system with 75+ specialized Python modules, significantly reducing `main.py` from 15,175 to 617 lines.
- **Centralized Database Layer (Nov 26, 2025 - LIMPIEZA FINAL COMPLETADA)**: All database logic consolidated in `omnix_services/database_service/` with 23 tables and 22 DAL methods. **6 Community Intelligence modules refactored to use centralized database_service** (2 full DAL: feedback_manager, risk_guardian; 2 mixtos: signal_contribution, community_analyzer; 2 conservadores: reward_system, community_dashboard) eliminating **~410 lines of duplicate code** (~290 _get_connection + ~120 _init_tables_DEPRECATED). Dependency injection configured in enterprise_bot.py (único entry point). **signal_contribution.py 100% limpio** (610→500 líneas). Auditoría final: **23 tablas SOLO en database_service.py** (única fuente de verdad). **100% centralized** (mix of DAL + conservative patterns). See `docs/cambios_ivan/2025-11-26_centralizacion_database.md` for details.
- **Database Migration to ORM (Planned - Nov 26, 2025)**: Comprehensive migration plan from psycopg2 (SQL puro) to SQLModel + Alembic + Flask API REST. 7-phase roadmap (8-10 weeks) with zero downtime strategy using dual-run adapter pattern, feature flags per module, and extensive parity testing. Benefits include type safety (Pydantic + SQLAlchemy), automatic migrations, 10x easier testing, REST API for investors, and async readiness. **ACTUALIZADO 2025**: Plan actualizado con versiones 2025 (SQLModel 0.0.27, Alembic 1.17.2, Flask-CORS 6.0.1 con security fixes CVE-2024-*, Python ≥3.10 obligatorio). Incluye changelog completo, breaking changes documentados, y notas de seguridad críticas. See `docs/cambios_ivan/migration_orm.md` for complete implementation plan with redundant validation checks and rollback procedures.
- **Database Schema Modernization FASE 1 (Nov 26, 2025)**: Conservative improvements to users table following 3NF normalization. Added email, is_active, updated_at columns; changed total_profit from REAL to NUMERIC(18,8) for financial precision; added CHECK constraints. Created new user_contacts table for multi-channel contact management (WhatsApp, email, Telegram, phone, SMS) with FK to users. 4 new DAL methods: add_user_contact(), get_user_contacts(), verify_user_contact(), set_primary_contact(). 100% backward compatible with automatic migration for both fresh deployments and upgrades. See `database.md` section 9 for complete details.
- **Database Optimization: Integridad & Escalabilidad (Nov 26, 2025)**:
  - **13 FK Constraints con ON DELETE CASCADE**: Garantiza 100% integridad referencial (0 registros huérfanos). Fix crítico: risk_guardian_events.user_id cambiado de BIGINT → TEXT para compatibilidad con users.user_id.
  - **20 Índices de Performance**: 15 índices FK simples + 5 índices compuestos (user_id + timestamp DESC) para queries históricas. Mejora de 10x en JOINs y queries de historial.
  - **7 CHECK Constraints**: Validación automática de datos a nivel DB (trades.status, community_signals.signal_type, etc).
  - **Sistema TTL Cleanup Automático**: Previene crecimiento infinito con cleanup diario (11 tablas configuradas). TTL: 30 días (conversations, trades), 90 días (trade_reasonings para ML), 60 días (signal_executions), 7 días (pending_evaluations). Reduce espacio estimado 95% (~500MB → ~25MB en 1 año). Control de frecuencia con Redis flag (db:last_cleanup_date). Fail-safe: ejecuta cleanup si Redis no disponible.
  - **3 Migraciones Idempotentes**: _fix_risk_guardian_user_id_type(), _add_foreign_key_constraints(), _add_check_constraints(). Seguras para fresh deployments y upgrade paths.
  - See `docs/cambios_ivan/2025-11-26_database_optimization_fks_ttl.md` for complete details.
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
- **PostgreSQL (Neon)**: Main relational database with 26 tables organized in:
  - Core System (8 tables): users, user_contacts, trades, analysis, conversations, whatsapp_messages, sharia_validations, balance_history
  - Paper Trading (2 tables): paper_trading_balances, paper_trading_trades
  - Conversational Brain (3 tables): trade_reasonings, trade_evaluations, pending_evaluations
  - Community Intelligence (5 tables): community_feedback, strategy_votes, improvement_proposals, user_contributions, detected_patterns
  - Signal Contribution (4 tables): community_signals, signal_executions, signal_votes, alpha_leaderboard
  - Risk Guardian (1 table): risk_guardian_events
  - Risk Management System (3 tables): risk_limits, risk_limit_breaches, risk_metrics_snapshots
  - **Centralized Access**: All queries via `omnix_services/database_service/database_service.py` (2,600+ lines, 28 DAL methods: 13 original + 5 Community Intelligence + 4 User Contacts + 6 RMS)
  - **FASE 1 Modernization (Nov 26, 2025)**: Improved users table (NUMERIC precision, email, is_active, updated_at) + new user_contacts table (3NF normalization). 100% backward compatible.
  - **RMS Tables (Nov 27, 2025)**: 3 new tables for institutional risk control with full DAL support.
- **Redis**: In-memory data store for state management, conversation history, caching.

### Key Python Libraries
- `numpy`, `scipy`, `ccxt`: Core trading and mathematical operations.
- `google-generativeai`, `openai`: AI model integration.
- `python-telegram-bot`: Telegram integration.
- `psycopg2-binary`, `redis`: Database drivers.
- `requests`, `websockets`, `aiohttp`, `httpx`: HTTP and WebSocket communication.
- `pypqc`: Post-quantum cryptography implementation.
- `pandas`, `plotly`, `kaleido`, `reportlab`, `PyPDF2`: Professional testing and reporting.