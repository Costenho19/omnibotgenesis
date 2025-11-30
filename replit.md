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
- **Quantum Physics Validation System**: PhD+ level scientific accuracy with 31 verified formulas and quantum credibility scoring, including advanced formulas for Amplitude Damping, Quantum Sharpe Ratio, Quantum Criticality, Bures-Fisher Metrics, and Side-Channel Analysis.
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
- **Centralized Database Layer**: All database logic in `omnix_services/database_service/` with 33 code-managed tables (8 core + 6 risk + 6 derivatives + 7 community + 6 signals) and 22+ DAL methods. Schema migrations managed transactionally via `_init_tables()`.
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
- **PostgreSQL (Railway)**: Main relational database hosted on Railway with 33 code-managed tables:
  - **Core (8)**: users, trades, analysis, schema_migrations, conversations, user_contacts, balance_history, sharia_validations
  - **Risk (6)**: risk_limits, risk_limit_breaches, risk_metrics_snapshots, risk_guardian_events, circuit_breaker_status, paper_trading_balances
  - **Derivatives (6)**: derivatives_positions, derivatives_trades, derivatives_balances, derivatives_hedges, derivatives_funding_log, derivatives_funding_opportunities
  - **Community (7)**: community_feedback, strategy_votes, user_contributions, detected_patterns, improvement_proposals, trade_evaluations, pending_evaluations
  - **Signals (6)**: community_signals, signal_executions, signal_votes, alpha_leaderboard, paper_trading_trades, trade_reasonings
  - **Connection**: Uses `DATABASE_URL` environment variable with public URL (`interchange.proxy.rlwy.net` or `shuttle.proxy.rlwy.net`)
  - **Driver**: psycopg3 (native URL support, no parsing required)
  - **SSL**: Required (`sslmode=require` added automatically)
- **Redis (Railway)**: External in-memory cache for persistent state management, conversation history, market data caching, and rate limiting.
  - **Connection**: Uses `REDIS_URL` environment variable

#### Key Python Libraries
- `numpy`, `scipy`, `ccxt`: Core trading and mathematical operations.
- `google-generativeai`, `openai`: AI model integration.
- `python-telegram-bot`: Telegram integration.
- `psycopg` (v3), `redis`: Database drivers (psycopg3 for native PostgreSQL URL support).
- `requests`, `websockets`, `aiohttp`, `httpx`: HTTP and WebSocket communication.
- `pypqc`: Post-quantum cryptography implementation.
- `pandas`, `plotly`, `kaleido`, `reportlab`, `PyPDF2`: Professional testing and reporting.

### Recent Changes (Nov 29, 2025)

#### CRITICAL: Conversation Memory System Fix (Nov 29, 2025)
- **Problem**: Bot had no memory - couldn't remember previous conversations despite PostgreSQL/Redis storing data correctly
- **Root Cause**: All calls to `generate_response()` in `handle_direct_message` and `handle_message` were missing the `chat_id` and `user_id` parameters. The AI adapter defaulted to `chat_id=0`, causing history lookups to return empty results even though real conversations were saved with correct user IDs (e.g., 7014748854)
- **Solution**: 
  - Fixed ALL 6 calls to `self.ai.generate_response()` to pass named parameters: `chat_id=telegram_chat_id, user_id=user_id, trading_system=self.trading`
  - Added `telegram_chat_id = str(update.effective_chat.id)` at start of `handle_message` for proper chat identification
  - Fixed `self.ai_system` → `self.ai` (undefined variable bug)
  - Fixed `self.trading_system` → `self.trading` (undefined variable bug)
  - Added robust chat_id conversion in `conversational_ai_adapter.py` with error handling and logging
  - Added `last_activity` column migration for users table
- **Files Modified**:
  - `omnix_services/telegram_service/enterprise_bot.py` - handle_message and handle_direct_message handlers
  - `omnix_services/ai_service/conversational_ai_adapter.py` - Lines 103-118 (robust chat_id parsing)
  - `omnix_services/database_service/database_service.py` - Lines 1413-1431 (column migration)

#### YouTube Video Analysis Fix V5 - Whisper Audio Fallback (Nov 30, 2025 - Latest)
- **Problem**: YouTube blocking ALL subtitle download methods (youtube-transcript-api + yt-dlp) with 429 rate limit errors on Railway IP
- **Root Cause**: Railway's shared IP address is rate-blocked by YouTube for subtitle scraping
- **Solution**: Added OpenAI Whisper as ultimate fallback - downloads audio (which still works) and transcribes with AI
- **New Method `_get_transcript_whisper()`**:
  - Downloads lowest quality audio (saves bandwidth and time)
  - Sends to OpenAI Whisper API for transcription
  - **10-minute max duration** limit to control costs
  - **25MB max file size** limit for Whisper API
  - Caches successful transcriptions in PostgreSQL for 30 days
- **New Database Table `video_transcript_cache`**:
  - Stores video_id, transcript, source, duration, created_at, expires_at
  - Cache checked before any network request
  - Prevents repeated Whisper calls for same video
- **Enhanced Fallback Chain** (6 levels):
  1. PostgreSQL cache check (instant if cached)
  2. VideoAnalyzerUltra `get_transcript()` direct
  3. VideoAnalyzerUltra `list_transcripts()` fallback
  4. `_get_transcript_ytdlp()` with retries
  5. **NEW: `_get_transcript_whisper()`** - audio download + Whisper transcription
  6. Error message if all fail
- **Files Modified**:
  - `omnix_services/ai_service/video/analyzer.py` - Added `_get_transcript_whisper()`, cache integration, database_service parameter
  - `omnix_services/database_service/database_service.py` - Added `video_transcript_cache` table, `get_cached_transcript()`, `save_transcript_cache()` methods
  - `omnix_services/telegram_service/enterprise_bot.py` - Pass db_manager to VideoAnalyzerUltra

#### YouTube Video Analysis Fix V2 (Nov 29, 2025)
- **Problem**: Videos still showing "no puedo interactuar con videos" despite VideoAnalyzerUltra existing
- **Root Cause Multiple Issues**:
  1. `handle_direct_message` (sync handler) used old auto-learning path instead of VideoAnalyzerUltra
  2. `_get_transcript()` used `list_transcripts()` which can fail with XML parsing errors on some videos
  3. Fallback logic not executing properly when VideoAnalyzerUltra returned 0% confidence
  4. `last_activity` column missing in Railway database causing UPSERT failures
  5. `thinking_message_id` undefined error when video processing completed
- **Solution**:
  - **Separated VideoAnalyzerUltra initialization** into its own try-block (won't fail if VideoLearningIntegration fails)
  - **Rewrote handle_direct_message video handling** to use VideoAnalyzerUltra with proper fallback chain
  - **Added get_transcript() as primary method** (more robust than list_transcripts for problematic videos)
  - **Enhanced fallback chain**: VideoAnalyzerUltra → get_transcript() direct → list_transcripts() → error message
  - **Fixed ensure_user_exists** to check if `last_activity` column exists before using it
  - **Added early return** after video processing to avoid thinking_message_id error
  - **Added extensive logging** for debugging transcript extraction failures

#### Critical Architecture Fix: Trading System Instance
- **Problem**: `/balance` and other commands used undefined `global_trading_system` variable instead of the properly initialized `self.trading` instance
- **Root Cause**: `global_trading_system` is only set when `main()` from `omnix_core/trading_system.py` runs (which it doesn't in Railway's architecture)
- **Solution**: 
  - Replaced all 18 occurrences of `global_trading_system` with `self.trading` in `enterprise_bot.py`
  - Fixed `conversational_ai_adapter.py` to pass and use `trading_system` parameter instead of global variable
- **Files Modified**:
  - `omnix_services/telegram_service/enterprise_bot.py` - All trading commands now use correct instance
  - `omnix_services/ai_service/conversational_ai_adapter.py` - Legacy response generation fixed

#### Previous Fixes (Session)
- **Memory System**: Fixed conversation history using `timestamp` instead of correct `created_at` column
- **Kraken Prices**: Public client now always created for market data (no API keys required)
- **Balance Parsing**: Corrected extraction of 'free' values from dict structure in balance responses
- **Balance Architecture**: Changed `/balance` from undefined global to `self.trading`