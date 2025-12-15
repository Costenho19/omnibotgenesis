# OMNIX V6.5.4d INSTITUTIONAL+

## Overview
OMNIX V6.5.4d INSTITUTIONAL+ is an enterprise-grade automated cryptocurrency and stock trading system designed for 24/7 operation with multi-user support. Its primary purpose is paper trading to build a credible track record for investor presentations, targeting $1M seed funding at an $11.5M pre-money valuation. Key capabilities include AI integration, post-quantum cryptography, real-time market analysis, Non-Markovian Temporal Memory, adaptive parameter calibration, institutional portfolio optimization, derivatives trading, and dual-market support for Kraken (crypto) and Alpaca (stocks). The system targets 3-5 trades/day with a 55%+ win rate, multi-crypto scanning, and tiered signal strengths.

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
The system integrates several core engines: AutoTradingBot V6.5.4 INSTITUTIONAL+, Non-Markovian Memory Kernel V6.5, Coherence Engine V6.5 ULTRA (6-Tier Veto System), AI Risk Guardian V5.4, Portfolio Management V6.4 INSTITUTIONAL+, CAES V6.5.4 (Confidence-Adaptive Entry System), On-Chain Data Intelligence V6.5, Execution Protocol V6.5.4c INSTITUTIONAL+ PREMIUM, InstitutionalDecisionLogger, and InstitutionalMetricsCalculator.

### Multi-User Architecture
Supports 100,000+ simultaneous users with isolated trading sessions using Redis for state management and PostgreSQL for persistence, ThreadPoolExecutor for parallel processing, and per-user locks.

### Dashboard Architecture
Includes a Flask Dashboard (primary API and web terminal) and a Streamlit Dashboard (interactive investor visualization) that consumes the Flask API via `OmnixAPIClient`.

### Trading Profiles System
Configurable profiles (e.g., INSTITUTIONAL, PAPER_AGGRESSIVE, PRODUCTION_STABLE) adjust trading parameters. `PRODUCTION_STABLE V6.5.4c` is the active profile.

### Hexagonal Architecture
The system employs a hexagonal architecture, with completed phases including Bootstrap & Config (centralized settings, DI Container), Domain & Application (entities, value objects, use cases, infrastructure adapters), and Infrastructure Adapters (KrakenAdapter, GeminiAdapter). Protocol interfaces are defined in `src/omnix/ports/` for driven and driver interfaces. A feature flag `USE_APP_LAYER=false` controls the gradual rollout of the new application layer.

### AI Service Architecture
Refactored with SOLID principles and dependency injection, integrating interfaces, providers (Gemini, OpenAI, Anthropic), a video learning module, and a DI container.

### Web Search Service Architecture
Structured with an `IntentDetector`, `SearchManager`, and `TavilySearch` client for intent-based web searches.

## External Dependencies

### APIs and Services
-   **Kraken Exchange**: Primary crypto data and order execution.
-   **Alpaca**: Stock data and historical bars.
-   **Google Gemini (2.0 Flash)**: Primary AI model.
-   **OpenAI (GPT-4o, Whisper)**: AI services.
-   **Anthropic Claude**: AI fallback.
-   **CoinGecko**: Backup crypto prices.
-   **Alternative.me**: Fear and Greed Index.
-   **Finnhub**: Market news and sentiment.
-   **Alpha Vantage**: Technical indicators.
-   **Tavily**: Real-time web search for AI responses.
-   **ANU QRNG**: Quantum random numbers with resilience protocol.

### Redis Cache System
The `omnix_core/cache/redis_cache.py` module provides enterprise-grade caching with a singleton `RedisCache`.

### Databases
-   **PostgreSQL (Railway)**: Main persistence for trades, analysis, conversations, balance history, derivatives, community intelligence, risk management, adaptive engine data, and user settings.
-   **Redis (Railway)**: Caching, state management, and rate limiting.

## V7.0 Migration Progress

### Phase 6: Folder Audit & Cleanup (COMPLETE - Dec 13, 2025)

**Dead Code Removed:**
- `omnix_reports/` - 0 external imports
- `reports/` - PDF moved to docs/history/
- `omnix_risk/` - Only self-references (dead code)
- `omnix/` - Legacy ports location

**Migrated:**
- `omnix/ports/` → `src/omnix/ports/` (test imports updated)

**Current Structure:**
```
OMNIX/
├── src/omnix/           <- Hexagonal V7.0 (ports, domain, etc.)
├── omnix_core/          <- Legacy runtime (essential)
├── omnix_services/      <- Legacy services (essential)
├── omnix_config/        <- Configuration (essential)
├── omnix_dashboard/     <- Dashboard (essential)
├── omnix_api/           <- API (essential)
├── omnix_testing/       <- Dev/backtesting tools
├── docs/                <- Documentation
├── tests/               <- Test suite
├── scripts/             <- Utility scripts
└── sql/                 <- Migrations
```

See `docs/current/FOLDER_AUDIT_PHASE6.md` for full audit details.

### Codebase Audit (Dec 15, 2025)
Full code vs documentation audit completed. Results: 100% verification of Trading System, AI Service, User Settings, and Telegram Bot. Hexagonal migration at 37.5% (3/8 ports integrated). See `docs/current/CODEBASE_AUDIT_REPORT.md` for complete analysis.