# OMNIX V6.5.4c INSTITUTIONAL+ - Automated Trading System

## Overview

OMNIX V6.5.4c INSTITUTIONAL+ is an enterprise-grade automated cryptocurrency and stock trading system designed for 24/7 operation with multi-user support. Its primary purpose is paper trading to build a credible track record for investor presentations, targeting $1M seed funding at $11.5M pre-money valuation. Key capabilities include AI integration, post-quantum cryptography, real-time market analysis, Non-Markovian Temporal Memory with On-Chain Data Intelligence, adaptive parameter calibration, institutional portfolio optimization, derivatives trading, and dual-market support for Kraken (crypto) and Alpaca (stocks). The system targets 3-5 trades/day with a 55%+ win rate, multi-crypto scanning, and tiered signal strengths.

## V6.5.4c Changes (December 10, 2025)

1. **ARES V1+V2 Activation**: Enabled in PRODUCTION_STABLE profile for track record generation
   - ARES V1 (Swing): 70% min confidence
   - ARES V2 (Scalping): 75% min confidence
   - Max 3 trades/day (shared)
   - Lateral markets allowed
2. **Drawdown Limit Increased**: 10% → 15% to allow trading during recovery
3. **AI Truthfulness Fix**: PaperTradingRepository ensures real PostgreSQL data in AI responses
4. **Hexagonal Architecture Phase 1**: 12 Protocol interfaces in `omnix/ports/`

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

The system features several core engines:
-   **AutoTradingBot V6.5.4 INSTITUTIONAL+**: Multi-crypto scanning, tiered signal strength, HMM quality filter, drawdown protection.
-   **Non-Markovian Memory Kernel V6.5**: Detects regime transitions, recognizes cyclical patterns, performs memory coherence scoring, and integrates on-chain signals.
-   **Coherence Engine V6.5 ULTRA**: 6-Tier Veto System for validating strategy agreement, maintaining consistent trade quality.
-   **AI Risk Guardian V5.4**: Monitors for overtrading, drawdown, and prevents revenge trading, with a hard cap of $20K max trade size.
-   **Portfolio Management V6.4 INSTITUTIONAL+**: Goldman-Sachs level optimization using Markowitz and Black-Litterman models.
-   **Derivatives Trading Module**: Supports paper/real trading modes, including MarginEngine, KrakenFuturesClient, and HedgingService.
-   **Stock Trading Premium V6.3 ULTRA**: Incorporates 9 institutional modules including Monte Carlo, Kalman Filter, HMM, ARES-STOCK, Non-Markovian Memory, Coherence Engine, Risk Guardian, Gap Protection, and Earnings Protector.
-   **Adaptive Parameter Engine V6.5 ULTRA**: Auto-calibrates ARES strategies based on market regime.
-   **CAES V6.5.4 (Confidence-Adaptive Entry System)**: Dynamic position sizing based on Non-Markovian Kernel confidence.
-   **On-Chain Data Intelligence V6.5**: Institutional-grade blockchain analytics using free APIs.
-   **Fear & Greed Contrarian Strategy V6.5.4**: Applies in both paper and real modes.
-   **Web Search Service V6.5.4**: Real-time internet search via Tavily API with Redis caching.
-   **Execution Protocol V6.5.4 INSTITUTIONAL+ PREMIUM**: 4-layer institutional-grade trade execution system (Citadel/Jump Trading level) including LiquidityAnalyzer, MicroVolatilityEngine, CrossAssetCorrelationEngine, and an ExecutionProtocol orchestrator.
-   **InstitutionalDecisionLogger V6.5.4**: Investor-grade audit trail logging for all trade decisions.
-   **Volatility-Based SL/TP Classification V6.5.4**: Differentiates Stop Loss/Take Profit percentages based on crypto pair volatility.
-   **InstitutionalMetricsCalculator V6.5.4 PREMIUM**: Calculates Sharpe, Sortino, and Calmar ratios per-pair and portfolio-wide for investor presentations.
-   **InstitutionalReportGenerator V6.5.4 PREMIUM**: Generates professional PDF reports for investors.
-   **Streamlit Dashboard V6.5.4 PREMIUM**: Interactive investor dashboard with Plotly charts, real-time metrics, and performance grading.

### Multi-User Architecture V6.5.4

Supports 100,000+ simultaneous users with isolated trading sessions using Redis for state management and PostgreSQL for persistence, employing ThreadPoolExecutor for parallel processing and per-user locks.

### Dashboard Architecture (V6.5.4 PREMIUM)

-   **Flask Dashboard** (port 5000): Primary API and web terminal, providing endpoints for metrics, reports, system calibration, and market data.
-   **Streamlit Dashboard** (port 8080): Interactive investor visualization consuming the Flask API.
-   **API Client**: Service-to-service communication via `OmnixAPIClient`.

### Trading Profiles System

Configurable profiles (INSTITUTIONAL, PAPER_AGGRESSIVE, BALANCED, PAPER_OPTIMIZED, WIN_RATE_OPTIMIZED, PRODUCTION_STABLE) adjust trading parameters. `PRODUCTION_STABLE V6.5.4c` is the active profile with ARES enabled for track record generation.

### Strategy Separation (V6.5.4c)

-   **Production Strategies (10)**: QuantumMomentum, Monte Carlo, Kelly Criterion, Black Swan, HMM, Kalman Filter, Non-Markovian Kernel, Coherence Engine, Risk Guardian, SentimentAnalysis.
-   **Experimental Strategies**: ARES V1 (Swing), ARES V2 (Scalping) - **ACTIVE** in PRODUCTION_STABLE but tracked separately from production metrics.

### Hexagonal Architecture (V7.0 Foundation)

Phase 1 completed with protocol ports defined in `omnix/ports/` for both driven (output) and driver (input) interfaces, adhering to SOLID principles.

### AI Service Architecture

The `omnix_services/ai_service/` module is refactored with SOLID principles and dependency injection, including interfaces, providers (Gemini, OpenAI, Anthropic), a video learning module, and a DI container. It integrates a Quantum Physics Validator for scientific accuracy in prompts and now fetches real trade data from PostgreSQL to ensure truthful reporting.

### Web Search Service Architecture

Structured with an `IntentDetector` (SRP), `SearchManager` (orchestration), and `TavilySearch` client to determine and execute web searches based on user intent.

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

The `omnix_core/cache/redis_cache.py` module provides enterprise-grade caching with a singleton `RedisCache`, automatic connection management, and function caching with SHA256-hashed keys.

### Databases

-   **PostgreSQL (Railway)**: Main persistence for trades, analysis, conversations, balance history, derivatives, community intelligence, risk management, adaptive engine data, and user settings.
-   **Redis (Railway)**: Caching, state management, and rate limiting.

## Documentation

**Consolidated December 10, 2025** - Organized into core, architecture, and audits.

| Document | Location | Purpose |
|----------|----------|---------|
| INDEX.md | `docs/core/` | Navigation hub |
| ARCHITECTURE_REFERENCE.md | `docs/core/` | Modules, ports, dashboard APIs |
| TRADING_OPERATIONS.md | `docs/core/` | Profiles, flow, operations |
| MODERNIZATION_ROADMAP.md | `docs/core/` | V7.0 plans (DEFERRED) |
| B2C_IMPLEMENTATION_PLAN.md | `docs/core/` | SaaS monetization roadmap |
| ARCHITECTURE_AUDIT_2025.md | `docs/architecture/` | Code audit, SOLID violations, target structure |
| MIGRATION_ROADMAP.md | `docs/architecture/` | Strangler Fig migration (5 phases) |
| DATABASE_AUDIT_REPORT.md | `docs/audits/` | DB integrity audit |
| INTERNAL_AUDIT_TRANSPARENCY.md | `docs/audits/` | Investor due diligence |

**Single Source of Truth:** Trading parameters are in `omnix_core/config/trading_profiles.py`. Documentation reflects code, not the other way around.

## Architecture Modernization (2025)

**Status:** PLANNED - See `docs/architecture/` for details

| Fase | Nombre | Objetivo | Estado |
|------|--------|----------|--------|
| 0 | Foundation | pyproject.toml, lint, types | Pendiente |
| 1 | Bootstrap | Config central, DI container | Pendiente |
| 2 | Domain/App | Clean architecture layers | Pendiente |
| 3 | Interfaces | Flask blueprints via ports | Pendiente |
| 4 | Cleanup | Eliminar legacy | Pendiente |

**Target Structure:** `src/omnix/` con domain/, application/, infrastructure/, interfaces/, config/, bootstrap/

## B2C Monetization Objectives

**Target Product:** OMNIX Asesor Personal IA

| Milestone | Users | MRR | Timeline |
|-----------|-------|-----|----------|
| MVP | 50 | $950 | Month 2 |
| Growth | 200 | $5,800 | Month 6 |
| Scale | 500+ | $24,500 | Month 12 |

**Pricing Plans:**
- Free: 3 análisis/día (lead generation)
- Basic ($19): 20 análisis/día + 5 señales
- Pro ($29): 100 análisis + portfolio advisor + voz
- Premium ($49): Ilimitado + on-chain + reportes PDF

**Implementation Status:** See `docs/core/B2C_IMPLEMENTATION_PLAN.md` for detailed roadmap.