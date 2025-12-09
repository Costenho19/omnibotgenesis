# OMNIX V6.5.4 INSTITUTIONAL+ - Automated Trading System

## Overview

OMNIX V6.5.4 INSTITUTIONAL+ is an enterprise-grade automated cryptocurrency and stock trading system designed for 24/7 operation with multi-user support. Its primary purpose is paper trading to build a credible track record for investor presentations, targeting $1M seed funding at $11.5M pre-money valuation. Key capabilities include AI integration, post-quantum cryptography, real-time market analysis, Non-Markovian Temporal Memory with On-Chain Data Intelligence, adaptive parameter calibration, institutional portfolio optimization, derivatives trading, and dual-market support for Kraken (crypto) and Alpaca (stocks). The system aims for 20-50 trades/day with a 55%+ win rate, multi-crypto scanning, and tiered signal strengths.

## User Preferences

**Communication**: Simple, everyday language (Spanish primary).

### Deployment Policy (CRITICAL)
| Environment | Purpose | Status |
|-------------|---------|--------|
| **Railway** | PRODUCTION (24/7) | Bot runs permanently |
| **Replit** | DEVELOPMENT | Code editing and tests only |

**NEVER run the bot on Replit and Railway simultaneously** - Telegram allows only ONE active connection per token.

### Workflow for Debugging
1. **Railway Logs**: User provides logs directly for debugging
2. **DO NOT start bot locally** - Use Railway logs provided
3. **Code sync**: GitHub -> Railway auto-deploy from main branch
4. **After testing on Replit**: ALWAYS stop workflow before ending session

### Bot Testing Protocol (MANDATORY)
> **REGLA OBLIGATORIA**: Cada vez que se active el bot en Replit para testing:
> 1. Realizar las pruebas necesarias
> 2. **APAGAR el workflow del bot ANTES de terminar la sesion**
> 3. Verificar que el workflow este detenido
>
> **Razon**: Telegram solo permite UNA conexion activa por token. Si el bot corre en Replit y Railway al mismo tiempo, habra conflictos y errores de conexion.

## System Architecture

### Core Engines

-   **AutoTradingBot V6.5.4 INSTITUTIONAL+**: Multi-crypto scanning, tiered signal strength, ramp-up system, HMM quality filter, drawdown protection, position limit early-check.
-   **Non-Markovian Memory Kernel V6.5**: Detects regime transitions, recognizes cyclical patterns, performs memory coherence scoring, and integrates on-chain signals.
-   **Coherence Engine V6.5 ULTRA**: 6-Tier Veto System for validating strategy agreement, maintaining consistent thresholds for trade quality and win rate > 55%.
-   **Multi-Crypto Scanner V6.5**: Scans 11 crypto pairs.
-   **AI Risk Guardian V5.4**: Monitors for overtrading, drawdown, and prevents revenge trading, with a hard cap of $20K max trade size.
-   **Portfolio Management V6.4 INSTITUTIONAL+**: Goldman-Sachs level optimization using Markowitz and Black-Litterman models, with dynamic position sizing.
-   **Derivatives Trading Module**: Supports paper/real trading modes, including MarginEngine, KrakenFuturesClient, and HedgingService.
-   **Stock Trading Premium V6.3 ULTRA**: Incorporates 9 institutional modules including Monte Carlo, Kalman Filter, HMM, ARES-STOCK, Non-Markovian Memory, Coherence Engine, Risk Guardian, Gap Protection, and Earnings Protector.
-   **Adaptive Parameter Engine V6.5 ULTRA**: Auto-calibrates ARES strategies based on market regime.
-   **CAES V6.5.4 (Confidence-Adaptive Entry System)**: Dynamic position sizing based on Non-Markovian Kernel confidence using a sigmoid aggression function.
-   **On-Chain Data Intelligence V6.5**: Institutional-grade blockchain analytics using free APIs.
-   **Fear & Greed Contrarian Strategy V6.5.4**: Applies in both paper and real modes with appropriate boosts.
-   **Web Search Service V6.5.4**: Real-time internet search via Tavily API with Redis caching and rate limiting.
-   **Execution Protocol V6.5.4 INSTITUTIONAL+ PREMIUM**: 4-layer institutional-grade trade execution system (Citadel/Jump Trading level) including LiquidityAnalyzer, MicroVolatilityEngine, CrossAssetCorrelationEngine, and an ExecutionProtocol orchestrator for dynamic decision-making.
-   **InstitutionalDecisionLogger V6.5.4**: Investor-grade audit trail logging for all trade decisions, emitting structured JSON events for various trade lifecycle stages.
-   **Volatility-Based SL/TP Classification V6.5.4**: Differentiates Stop Loss/Take Profit percentages based on crypto pair volatility.
-   **InstitutionalMetricsCalculator V6.5.4 PREMIUM**: Calculates Sharpe, Sortino, and Calmar ratios per-pair and portfolio-wide for investor presentations.
-   **InstitutionalReportGenerator V6.5.4 PREMIUM**: Generates professional PDF reports for investors.
-   **Streamlit Dashboard V6.5.4 PREMIUM**: Interactive investor dashboard with Plotly charts, real-time metrics, and performance grading.

### Multi-User Architecture V6.5.4

-   Supports 100,000+ simultaneous users with isolated trading sessions.
-   Uses Redis for fast state management and PostgreSQL for persistence.
-   Employs ThreadPoolExecutor for parallel processing and per-user locks.

### Dashboard Architecture (V6.5.4 PREMIUM)

-   **Flask Dashboard** (port 5000): Primary API and web terminal, providing endpoints for metrics, reports, system calibration, and standard market data.
-   **Streamlit Dashboard** (port 8080): Interactive investor visualization consuming the Flask API, featuring a dark theme, Plotly charts, performance grades, and per-pair analysis.
-   **API Client**: Service-to-service communication via `OmnixAPIClient`, configurable by environment variable.

### Trading Profiles System

-   Configurable profiles (INSTITUTIONAL, PAPER_AGGRESSIVE, BALANCED, PAPER_OPTIMIZED, WIN_RATE_OPTIMIZED, PRODUCTION_STABLE) to adjust trading parameters like Coherence Engine veto, Ramp-Up System, Score Thresholds, HMM VETO, and Regime Change VETO.
-   **WIN_RATE_OPTIMIZED V2 PREMIUM**: Institutional-grade profile with per-pair calibration for specific cryptocurrencies, differentiated SL/TP, max position sizing, portfolio weights, and per-pair daily drawdown circuit breakers.
-   **PRODUCTION_STABLE V6.5.4**: Investor-ready profile using only proven strategies (QuantumMomentum, Monte Carlo, Kelly Criterion, Black Swan, HMM, Kalman, Non-Markovian Kernel, Coherence Engine, Risk Guardian). ARES V1/V2 disabled for track record consistency. Metrics match strategies in production.

### Strategy Separation (V6.5.4)

-   **Production Strategies**: QuantumMomentum, Monte Carlo, Kelly Criterion, Black Swan, HMM, Kalman Filter, Non-Markovian Kernel, Coherence Engine, Risk Guardian.
-   **Experimental Strategies** (in `docs/experimental/`): ARES V1 (Swing), ARES V2 (Scalping) - under calibration, not included in investor metrics.

### Migration Tools (V6.5.4 Premium)

-   **Migration Watchdog**: Closes orphan positions in excluded symbols before profile switches.
-   **Migration Test Suite**: Automated verification of profile configurations.
-   **Symbol Filter**: Blocks trades in non-allowed symbols.
-   **Premium Observability**: Structured JSON logs for SL/TP triggers with Prometheus metrics.

### Database Migration System (V6.5.4)

The `omnix_services/database_service/migrations/` module provides versioned database migrations:
-   **MigrationRunner**: Executes migrations with advisory locks, transactions, and rollback on failure.
-   **MigrationRegistry**: Maintains ordered list of migrations with version tracking.
-   **Auto-upgrade**: Handles legacy `schema_migrations` tables from Railway.
-   **Migrations run automatically** in main.py after cache cleanup, before service initialization.
-   **Pattern**: Each migration returns True/False; must be idempotent (ADD COLUMN IF NOT EXISTS, etc.).

### AI Service Architecture (SOLID + Dependency Injection)

The `omnix_services/ai_service/` module is refactored with SOLID principles and dependency injection, supporting multiple AI providers via a unified interface, ensuring type safety and modularity.

### Web Search Service Architecture

The `omnix_services/web_search_service/` is structured with an `IntentDetector` (SRP), `SearchManager` (orchestration), and `TavilySearch` client. The `IntentDetector` identifies if a message requires a web search based on keywords.

### Video Analyzer Utilities

-   **parse_vision_json()**: Centralized JSON parsing for Vision API responses, handling markdown code blocks.
-   **CHART_ANALYSIS_PROMPT**: Shared prompt constant for chart analysis across Vision APIs.

## External Dependencies

### APIs and Services

-   **Kraken Exchange**: Primary crypto data and order execution.
-   **Alpaca**: Stock data and historical bars.
-   **Google Gemini (2.0 Flash)**: Primary AI model.
-   **OpenAI (GPT-4o, Whisper)**: AI services and transcription.
-   **Anthropic Claude**: AI fallback.
-   **CoinGecko**: Backup crypto prices.
-   **Alternative.me**: Fear and Greed Index.
-   **Finnhub**: Market news and sentiment.
-   **Alpha Vantage**: Technical indicators.
-   **Tavily**: Real-time web search for AI responses.
-   **ANU QRNG**: Quantum random numbers.

### Redis Cache System (V6.5.4)

The `omnix_core/cache/redis_cache.py` module provides enterprise-grade caching:
-   **RedisCache**: Singleton class with automatic connection management
-   **get_redis_client()**: Returns raw Redis client for direct access (used by WebSearchManager)
-   **get_redis_cache()**: Returns the RedisCache wrapper instance
-   **reconnect()**: Lazy recovery method when Redis connection is lost
-   **cache_result decorator**: Function caching with normalized SHA256-hashed keys for security
-   **Key normalization**: Deterministic cache keys even with dict/list/set arguments

### Databases

-   **PostgreSQL (Railway)**: Main persistence for trades, analysis, conversations, balance history, derivatives, community intelligence, risk management, adaptive engine data, and user settings.
-   **Redis (Railway)**: Caching, state management, and rate limiting.