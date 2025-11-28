# OMNIX V6.0 ULTRA - Automated Trading System

### Overview
OMNIX V6.0 ULTRA is an enterprise-grade automated cryptocurrency trading system designed for 24/7 operation on the Kraken Exchange. It operates in paper trading mode with $1,000,000 virtual capital (spot) + $100,000 (derivatives), employing institutional-grade position sizing to build a credible track record for investor presentations. The system integrates AI, post-quantum cryptography, and real-time market analysis, featuring advanced strategy modules like ARES V1 and V2, and multi-exchange arbitrage. The project aims to secure seed funding by demonstrating robust performance and a professional backtesting infrastructure, including new modules for institutional compliance, derivatives trading, and enhanced investor reporting.

### Recent Changes (November 28, 2025)
- **Quantum Physics Validator V6.0 - PhD+ Formulas (Nov 28, 2025)**: Ampliación del validador de física cuántica de 24→28 fórmulas verificadas. Nuevas fórmulas avanzadas: (1) Capacidad Private para Amplitude Damping Térmico (Qₚ, g₁(N), g₂(N)) - 32 keywords, (2) Ratio de Sharpe Cuántico con umbral de no-clonación √2 (S_q, conexión CHSH) - 31 keywords, (3) Criticalidad Cuántica con exponentes críticos (ξ divergencia, gap espectral Δ, fidelidad de Bures) - 41 keywords. Total: 140+ keywords para detección automática de temas cuánticos avanzados. Responde al feedback del evaluador que asignó 4.2/10 por evasión de cálculos fundamentales.
- **Code Cleanup Phase 2 - Core Modules (Nov 28, 2025)**: Limpieza completa de imports en archivos principales - eliminados 4 imports sin uso: asyncio + threading de enterprise_bot.py (5455 líneas), json de conversational_brain.py (624 líneas), asyncio de auto_trading_bot.py (2196 líneas). Total limpieza: 11 imports eliminados (Fase 1: main.py 7 imports, Fase 2: core modules 4 imports). Sistema verificado operacional después de reinicio completo - WebSocket Kraken conectado, Telegram polling activo, 28 tablas PostgreSQL, Redis, IA + voz funcionando. Arquitecto validó: sin regressions, threading se usa localmente donde se necesita, sistema 100% operacional. TODAS las features preservadas (ARES, derivatives, quantum, arbitrage, stock trading, auto-learning, RMS).
- **Conservative Code Cleanup (Nov 28, 2025)**: Limpieza conservadora completada en main.py - eliminados 5 imports sin uso (Flask utilities, lru_cache, multiprocessing.Pool, concurrent.futures, collections.deque) y imports duplicados (sys, os). Simplificado output verboso de cache cleanup. TODAS las features de diferenciación preservadas (ARES V1/V2, derivatives, quantum, arbitrage, stock trading, auto-learning, RMS). Sistema verificado operacional - 28 tablas activas, IA conversacional + voz funcionando, Telegram polling activo. Arquitecto validó: sin downstream dependencies rotas, sin security issues, sistema arrancó normalmente.
- **User Registration Bug Fixed (Nov 28, 2025)**: Implementado auto-registro de usuarios con UPSERT pattern (INSERT...ON CONFLICT DO UPDATE) en método `ensure_user_exists()`. Llamadas agregadas en `handle_message()` y `handle_voice_message()` para registrar/actualizar usuarios ANTES de cualquier DB write. Previene violaciones FK constraint en 13 tablas (conversations, trades, analysis, balance_history, paper_trading_trades, trade_reasonings, trade_evaluations, community_signals, signal_executions, signal_votes, alpha_leaderboard, risk_guardian_events, user_contacts). Método idempotente, thread-safe, actualiza username/metadata si usuario ya existe.
- **Aggressive Database Cleanup (Nov 28, 2025)**: Migración agresiva completada - eliminadas 5 tablas legacy sin uso activo (whatsapp_messages, detected_patterns, improvement_proposals, monitoring_metrics, ai_alerts), migrados contactos WhatsApp de users.whatsapp_number → user_contacts, backups automáticos creados. Schema reducido de 33→28 tablas activas (20 core + 7 risk/monitoring + 6 derivatives). Migración idempotente con transacciones, advisory locks y rollback automático.
- **Redis Cache Integration Complete**: Connected to Railway Redis via TCP proxy (shinkansen.proxy.rlwy.net:32595), persistent cache now active for conversations, market data, and rate limiting. All operations verified (SET/GET/INCREMENT/TTL/DELETE).
- **AI Token Limits Increased**: Response truncation fixed - GPT-4o (1500→4000 tokens), Gemini (4000→8000), Claude (1500→4000), +300-400% capacity for institutional-grade analyses.
- **Derivatives Module Integrated**: DerivativesManager now initializes in main.py with $100K paper trading balance
- **Kelly Criterion Fixed**: Corrected from Quarter Kelly (0.25) to Half Kelly (0.50), range enforced 4-20%
- **LSP Errors Resolved**: Fixed None-check guards in ai_prompts.py, conversational_brain.py, monte_carlo.py
- **AI Honesty Rules**: Updated prompts to never invent data, Kelly always 4-20%, D-Wave marked as pending

### User Preferences
User Communication Preference: Simple, everyday language (Spanish primary).

### Deployment Policy (CRITICAL)
**⚠️ TELEGRAM TOKEN CONFLICT WARNING:**
- **Railway = PRODUCTION (24/7)** - Bot corre permanentemente aquí
- **Replit = DEVELOPMENT ONLY** - Solo para editar código y pruebas puntuales
- **NUNCA correr el bot en Replit y Railway simultáneamente** - Telegram solo permite UNA conexión activa por token. Dos instancias causan: mensajes perdidos, conflictos de polling, desconexiones.
- **Después de testear en Replit**: Siempre parar el workflow antes de terminar la sesión.
- El código se sincroniza con GitHub; Railway hace deploy automático desde `main` branch.

**Flujo de Trabajo para Debugging:**
- **Logs de Railway**: El usuario proporcionará logs directamente cuando se necesiten para debugging.
- **NO arrancar bot localmente** para obtener logs - usar los logs de Railway proporcionados por el usuario.
- **Solo editar código aquí** - las pruebas se validan en Railway después del deploy automático.
- **Si se arranca para test/control**: Una vez confirmado todo, PARAR AUTOMÁTICAMENTE el workflow antes de terminar.

### Recent Changes (November 28, 2025) - Message Splitting
- **Telegram Message Splitting V2 (Nov 28, 2025)**: Implementada división inteligente de mensajes >4096 caracteres para evitar truncamiento. Nuevo método `split_text_smart()` divide respetando estructura (párrafos→líneas→palabras). Handler async `handle_message()` usa await para división compatible con event loop. Handler sync `handle_direct_message()` usa `send_telegram_text_safe()`. Header "(1/N)" añadido a mensajes divididos. Delay 0.3s entre partes para evitar rate limits. Arquitecto validó: flujo async preservado, sin bloqueo de event loop.

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
- **Quantum Physics Validation System**: PhD+ level scientific accuracy with 28 verified formulas (V6.0), 140+ detection keywords, and quantum credibility scoring, including a Quantum Testing Framework and Response Confidence System. Advanced formulas include: Capacidad Private para Amplitude Damping Térmico, Ratio de Sharpe Cuántico, Criticalidad Cuántica (exponentes críticos).
- **Risk Management & Protection**:
    - **Coherence Engine V5.4 ULTRA**: Validates agreement between trading strategies using a 6-Tier Veto System.
    - **AI Risk Guardian V5.4**: Real-time risk supervision (Overtrading, Drawdown, Revenge Trading Detection, Capital Protection).
    - **Risk Management System (RMS) V6.0**: Institutional-grade risk control with LimitsEngine, PositionMonitor, CircuitBreaker, AlertDispatcher, and RiskDashboard.
    - **Auto-Optimization Engine**: Continuously improves strategies via Genetic Algorithm, A/B Testing, and Auto-Adjustment.
    - **Multi-Exchange Arbitrage V6.0**: Institutional arbitrage across 8 exchanges.
    - **Institutional Compliance Suite**: Includes InstitutionalStressSuite for scenario testing, InstitutionalAuditLogger for immutable trails, and a DeadManSwitch for proactive monitoring and automatic halts.
    - **Premium Institutional Upgrade**: Features an Institutional Response Formatter, Reactivation Engine, and Portfolio Summary.
    - **Institutional Market Infrastructure**: Includes USD Risk Calculator, Exchange Latency Monitor, Orderbook Depth Analyzer, and Liquidity Monitor.
    - **Institutional Optimization Suite**: Features Cascade Protection, Adaptive Regime Switcher, and Pitch Deck Generator.
- **Derivatives Trading Module**: Central orchestrator (`DerivativesManager`) for perpetuals trading with paper/real modes, `MarginEngine` for conservative margin management, `KrakenFuturesClient`, `HedgingService` for spot↔perpetual hedging, `FundingArbitrageAnalyzer`, and Telegram integration.
- **Trading Modes**: Paper Trading ($1M virtual), Real Trading (with post-quantum signed orders), and Backtesting.
- **Quantum Enhancements**: ANU QRNG for true quantum randomness and D-Wave Leap for real quantum annealing for portfolio optimization, with classical fallback.
- **Community Intelligence**: Signal contribution, community feedback, and reward system.

#### System Design Choices
- **Modular Architecture**: 75+ specialized Python modules organized into `omnix_core/`, `omnix_services/`, `omnix_testing/`.
- **Centralized Database Layer**: All database logic in `omnix_services/database_service/` with 28 active tables (20 core + 7 risk/monitoring + 6 derivatives) and 22+ DAL methods. Schema migrations managed via transactional methods with advisory locks and automatic rollback.
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
- **PostgreSQL (Neon/Railway)**: Main relational database with 28 active tables categorized as:
  - **20 Core Tables**: users, user_contacts, trades, analysis, conversations, sharia_validations, balance_history, paper_trading_balances, paper_trading_trades, trade_reasonings, trade_evaluations, pending_evaluations, community_feedback, strategy_votes, user_contributions, community_signals, signal_executions, signal_votes, alpha_leaderboard, schema_migrations
  - **7 Risk/Monitoring Tables**: risk_guardian_events, risk_limits, risk_limit_breaches, risk_metrics_snapshots, circuit_breaker_status (plus 2 legacy monitoring tables removed Nov 28, 2025)
  - **6 Derivatives Tables**: derivatives_balances, derivatives_trades, derivatives_positions, derivatives_funding_log, derivatives_hedges, derivatives_funding_opportunities
  - **Legacy Tables Removed (Nov 28, 2025)**: whatsapp_messages, detected_patterns, improvement_proposals, monitoring_metrics, ai_alerts (backups created as omnix_backup_<table>_YYYYMMDD)
  - Fully operational with all foreign keys, indices, check constraints, and transactional migrations configured.
- **Redis (Railway)**: External in-memory cache connected via TCP proxy for persistent state management, conversation history, market data caching, and rate limiting. Connection: shinkansen.proxy.rlwy.net:32595 (public proxy for Replit→Railway). For Railway deployment, use internal private network: `REDIS_URL=${{Redis.REDIS_URL}}`.

#### Key Python Libraries
- `numpy`, `scipy`, `ccxt`: Core trading and mathematical operations.
- `google-generativeai`, `openai`: AI model integration.
- `python-telegram-bot`: Telegram integration.
- `psycopg2-binary`, `redis`: Database drivers.
- `requests`, `websockets`, `aiohttp`, `httpx`: HTTP and WebSocket communication.
- `pypqc`: Post-quantum cryptography implementation.
- `pandas`, `plotly`, `kaleido`, `reportlab`, `PyPDF2`: Professional testing and reporting.