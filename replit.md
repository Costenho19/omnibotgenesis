# OMNIX V6.5.4d INSTITUTIONAL+

## Overview

OMNIX V6.5.4d INSTITUTIONAL+ is an enterprise-grade automated cryptocurrency and stock trading system designed for 24/7 operation with multi-user support. Its primary purpose is paper trading to build a credible track record for investor presentations, targeting $1M seed funding at an $11.5M pre-money valuation. Key capabilities include AI integration, post-quantum cryptography, real-time market analysis, Non-Markovian Temporal Memory with On-Chain Data Intelligence, adaptive parameter calibration, institutional portfolio optimization, derivatives trading, and dual-market support for Kraken (crypto) and Alpaca (stocks). The system targets 3-5 trades/day with a 55%+ win rate, multi-crypto scanning, and tiered signal strengths.

## Recent Changes (V6.5.4d - December 2024)

1. **Entry Thresholds Raised**: score_moderate=12 (same as score_strong), effectively disabling MODERATE signals - only STRONG (≥12) or VERY_STRONG (≥15) trades allowed
2. **Emergency Stop Loss**: 2% maximum absolute loss per position enforced as class-level constant BEFORE any TP/SL calibration checks
3. **ADA/USD Excluded**: Permanently blocked from trading (0% win rate over 12 trades)
4. **Macro Trend Veto**: Kalman BEARISH trend (strength >0.6) applies -15 penalty; HMM trending_bear applies -10 penalty - blocks trades in downtrends

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

The system integrates several core engines:
- **AutoTradingBot V6.5.4 INSTITUTIONAL+**: Multi-crypto scanning, tiered signal strength, HMM quality filter, drawdown protection.
- **Non-Markovian Memory Kernel V6.5**: Detects regime transitions, recognizes cyclical patterns, performs memory coherence scoring.
- **Coherence Engine V6.5 ULTRA**: 6-Tier Veto System with multi-layer consensus and veto gates. See `auto_trading_bot.py:2220-2300` for full gating logic.
- **AI Risk Guardian V5.4**: Daily loss circuit breaker (PRODUCTION_STABLE: 3%, system max: 8%), overtrading prevention, revenge trading detection, $20K max position cap.
- **Portfolio Management V6.4 INSTITUTIONAL+**: Markowitz and Black-Litterman optimization.
- **CAES V6.5.4**: Confidence-Adaptive Entry System. Aggression multiplier (0.5x-3x) based on Non-Markovian Kernel confidence; regime limits may allow up to 6% capital.
- **On-Chain Data Intelligence V6.5**: Institutional-grade blockchain analytics.
- **Execution Protocol V6.5.4c INSTITUTIONAL+ PREMIUM**: 4-layer institutional-grade trade execution with Data Integrity Block (blocks trades when liquidity or correlation data unavailable).
- **InstitutionalDecisionLogger**: Complete audit trail for regulatory compliance.
- **InstitutionalMetricsCalculator**: Sharpe, Sortino, Calmar ratios for investor reporting.

### Multi-User Architecture

Supports 100,000+ simultaneous users with isolated trading sessions using Redis for state management and PostgreSQL for persistence, ThreadPoolExecutor for parallel processing, and per-user locks.

### Dashboard Architecture

Includes a Flask Dashboard (primary API and web terminal) and a Streamlit Dashboard (interactive investor visualization) that consumes the Flask API via `OmnixAPIClient`.

### Trading Profiles System

Configurable profiles (e.g., INSTITUTIONAL, PAPER_AGGRESSIVE, PRODUCTION_STABLE) adjust trading parameters. `PRODUCTION_STABLE V6.5.4c` is the active profile, with ARES V1 (Swing) and ARES V2 (Scalping) strategies in production calibration for track record generation.

### Strategy Separation

Strategies are categorized into Production (e.g., QuantumMomentum, Monte Carlo, Black Swan) and Production Calibration (ARES V1 and V2), with the latter tracked separately.

### Hexagonal Architecture

**Phase 1 Complete**: Bootstrap & Config - Centralized Settings with Pydantic, DI Container, Bootstrap Runtime.

**Phase 2 Complete** (December 12, 2025):
- Wave 1: Domain entities (Trade, Position, Signal, RiskAlert), value objects (Money, Quantity, SymbolPair, ConfidenceScore), market support entities (MarketSnapshot, StrategyVote, CoherenceResult)
- Wave 2: Strategy wrappers re-exporting from legacy locations (ARES V1/V2, QuantumMomentum, etc.), Use cases (ExecuteTradeUseCase, ScanMarketUseCase, EvaluateRiskUseCase)
- Wave 3: Infrastructure adapters (TradingServiceAdapter, RiskGuardianAdapter, CoherenceEngineAdapter), Container updates with USE_APP_LAYER feature flag

**Phase 3 In Progress** (December 12, 2025):
- **KrakenAdapter**: Exchange adapter wrapping legacy KrakenAPIClient with retry logic (exponential backoff), telemetry, health checks. Implements TradingPort + MarketDataPort.
- **GeminiAdapter**: AI inference adapter with runtime fallback cascade (Gemini -> OpenAI -> Anthropic -> Legacy). Implements AIInferencePort.
- **Container Updates**: Added kraken_adapter and gemini_adapter properties with lazy initialization and health reporting.

**Feature Flag**: `USE_APP_LAYER=false` (default OFF) - Controls gradual rollout of new application layer.

Protocol interfaces defined in `src/omnix/ports/` for driven and driver interfaces, adhering to SOLID principles.

### AI Service Architecture

Refactored with SOLID principles and dependency injection, integrating interfaces, providers (Gemini, OpenAI, Anthropic), a video learning module, and a DI container. It includes a Quantum Physics Validator and fetches real trade data from PostgreSQL for truthful reporting.

### Web Search Service Architecture

Structured with an `IntentDetector`, `SearchManager`, and `TavilySearch` client for intent-based web searches.

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
-   **ANU QRNG**: Quantum random numbers with resilience protocol (falls back to `numpy.random` if unavailable).

### Redis Cache System

The `omnix_core/cache/redis_cache.py` module provides enterprise-grade caching with a singleton `RedisCache`, automatic connection management, and function caching.

### Databases

-   **PostgreSQL (Railway)**: Main persistence for trades, analysis, conversations, balance history, derivatives, community intelligence, risk management, adaptive engine data, and user settings.
-   **Redis (Railway)**: Caching, state management, and rate limiting.

## B2B Value Proposition (Prop Firms & Family Offices)

**Target Clients**: Mid-to-large Prop Firms and Family Offices seeking automated risk management.

### The 3-Day Risk Reduction Framework

| Day | Risk Axis | OMNIX Component | Client Impact |
|-----|-----------|-----------------|---------------|
| **Day 1** | Algorithmic Risk | Coherence Engine + Risk Guardian | Prevents catastrophic single-day losses via 6-Tier Veto System |
| **Day 2** | Volatility Risk | Adaptive Parameter Engine + CAES | Ensures consistency across changing market conditions |
| **Day 3** | Information Asymmetry | On-Chain Intelligence + Non-Markovian Kernel | Provides alpha edge over retail systems |

### Institutional-Grade Features

- **6-Tier Veto System**: Consensus shortfall (5/6 or 4/6 required) or score below veto_critical = immediate BLOCK
- **CAES Position Sizing**: Aggression multiplier 0.5x-3x based on kernel confidence; regime max up to 6% capital
- **Institutional Decision Logger**: Complete audit trail for regulatory compliance
- **InstitutionalMetricsCalculator**: Sharpe, Sortino, Calmar ratios for investor reporting

### Proof of Concept (PoC) Offering

> **30-Day PoC** (Commercial Proposal): Paper trading access with full transparency. Includes code review session with architects to demonstrate coherence between Risk Guardian and Institutional Decision Logger.

**License**: $15,000/year for institutional access with dedicated support.

## Documentation Structure (December 2025)

```
docs/
├── README.md                    <- Global index with role-based navigation
├── current/                     <- V6.5.4d System State
│   ├── ARCHITECTURE.md          <- Modules, ports, services, DB schema
│   ├── TRADING_OPERATIONS.md    <- Profiles, ARES, risk management
│   └── TECHNICAL_DEBT.md        <- Known issues, deferred work
├── transformation/              <- V7.0 Migration Plan
│   ├── ARCHITECTURE_AUDIT.md    <- Diagnostic, problems identified
│   ├── MIGRATION_PLAN.md        <- Strangler Fig phases, timeline
│   └── adr/                     <- Architecture Decision Records
├── business/                    <- B2C SaaS, investor docs
├── operations/                  <- Railway deployment, experimental
├── compliance/                  <- Audits, verification
└── history/                     <- Archived documentation
```

### Key Documents

| Document | Location | Purpose |
|----------|----------|---------|
| Architecture | `docs/current/ARCHITECTURE.md` | System modules, ports, services |
| Technical Debt | `docs/current/TECHNICAL_DEBT.md` | Known issues, refactoring backlog |
| Migration Plan | `docs/transformation/MIGRATION_PLAN.md` | V7.0 hexagonal roadmap |

## Refactoring Status (V7.0 Migration)

### Fase 0: Foundation ✅ COMPLETADA (Dec 11, 2025)

| Entregable | Ubicación |
|------------|-----------|
| Dependency Graph | `docs/architecture/phase0/DEPENDENCY_GRAPH.md` |
| ADR-001 | `docs/transformation/adr/ADR-001-hexagonal.md` |
| Module Catalog | Merged into `docs/current/ARCHITECTURE.md` |
| pyproject.toml | `/pyproject.toml` |
| src/omnix/ structure | `/src/omnix/` |
| Smoke tests | `tests/test_smoke.py` (13/13 pass) |

### Fase 1: Bootstrap & Config ✅ COMPLETADA (Dec 11, 2025)

| Entregable | Ubicación |
|------------|-----------|
| Centralized Settings | `src/omnix/config/settings.py` |
| DI Container | `src/omnix/bootstrap/container.py` |
| Bootstrap Runtime | `src/omnix/bootstrap/__init__.py` |
| Phase 1 Tests | `tests/test_phase1_bootstrap.py` (12/12 pass) |

### Fase 2: Domain & Application ✅ COMPLETADA (Dec 12, 2025)

| Entregable | Ubicación |
|------------|-----------|
| Domain Entities | `src/omnix/domain/trading/entities.py` |
| Value Objects | `src/omnix/domain/trading/value_objects.py`, `src/omnix/domain/support/market.py` |
| Use Cases | `src/omnix/application/trading/` (Execute, Scan, ManagePositions, CoherenceReport) |
| Infrastructure Adapters | `src/omnix/infrastructure/adapters/` (Trading, Risk, Coherence) |
| Parity Test Harness | `tests/test_parity_harness.py` |
| Integration Tests | `tests/test_integration_phase2.py` (97/97 pass) |

### Fase 3: Infrastructure Adapters 🔄 EN PROGRESO (Dec 12, 2025)

| Entregable | Ubicación | Estado |
|------------|-----------|--------|
| KrakenAdapter | `src/omnix/infrastructure/adapters/kraken_adapter.py` | ✅ Implementado |
| GeminiAdapter | `src/omnix/infrastructure/adapters/gemini_adapter.py` | ✅ Implementado |
| Container Updates | `src/omnix/bootstrap/container.py` | ✅ Actualizado |
| Retry Logic | KrakenAdapter._with_retry() | ✅ Exponential backoff |
| Runtime Fallback | GeminiAdapter._call_with_fallback() | ✅ Provider cascade |

**Feature Flag**: `USE_APP_LAYER=false` (default OFF) - Ready for gradual activation.

### Próxima Fase: 3b - Flask App Factory & Telegram Migration

Ver `docs/transformation/MIGRATION_PLAN.md` para plan completo.