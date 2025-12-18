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

**Voice Service / Dual Response (Dec 18, 2025):**
- VoiceServiceAdapter integrated into DI Container with `USE_VOICE_PORT` flag
- All users receive dual response (text + audio) when voice service is available
- Uses `asyncio.to_thread` wrapper around legacy `send_telegram_response_with_voice` to prevent event loop blocking
- Voice generated for AI responses > 20 chars when `VOICE_SERVICE_AVAILABLE=true`

**AI-First Command Detection (Dec 18, 2025):**
- FIX CRÍTICO: NLP command detection ahora solo procesa mensajes que empiezan con `/`
- Previene falsos positivos donde preguntas complejas (ej: "resumen" → "resume") disparaban comandos
- Flujo AI-first: Todo texto libre va a la IA, solo comandos explícitos (`/pause`, `/resume`, etc) ejecutan acciones
- Cumple con TelegramPort protocol: `handle_message()` para texto → IA, `handle_command()` para `/comandos`
- IntentClassificationAdapter añadido al DI Container (Phase 6) con soporte para legacy NLP shim
- Componentes creados: IntentClassificationPort, IntentResolutionService, ConfirmActionUseCase (pendientes de integración completa)

**Error Handling System (Dec 16, 2025):**
- `ai_error_handler.py`: ErrorClassifier with 8 categories (AUTH_ERROR, RATE_LIMIT, SERVER_ERROR, TIMEOUT, etc.)
- SDK-specific error detection for Gemini, OpenAI, Anthropic exceptions
- Intelligent retry/failover: non-retryable (401, 403, 404) skip immediately to next model
- Retryable errors (429, 500, 503, timeout) use exponential backoff
- Timeouts: Gemini 20s, OpenAI 15s, Anthropic 15s
- Structured logging with diagnostic messages: `❌ PROVIDER [CODE] Message | Acción sugerida`

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

### Hexagonal Architecture Status (Dec 18, 2025)

**Estructura: 100% COMPLETA | Activación: 100% ✅**

| Métrica | Valor |
|---------|-------|
| Driven Ports | 15 |
| Driver Ports | 2 |
| **Total Ports** | **17** |
| Adapters | **19** |
| Tests pasando | 120/120 |
| Ports activos | **15/15 (100%) ✅** |

**🎉 MIGRACIÓN COMPLETADA - 18 Dic 2025**

Todas las variables de Strangler Fig están activas en Railway:

| Categoría | Variables |
|-----------|-----------|
| **AI & Voice** | `USE_AI_PORT`, `USE_UNIFIED_GATEWAY`, `USE_VOICE_PORT` |
| **Infraestructura** | `USE_CACHE_PORT`, `USE_DATABASE_PORT`, `USE_NOTIFICATION_PORT`, `USE_TELEGRAM_PORT`, `USE_ONCHAIN_PORT` |
| **Trading Core** | `USE_MARKET_INTEL_PORT`, `USE_EXECUTION_PORT`, `USE_RISK_CONTROL_PORT`, `USE_DERIVATIVES_PORT`, `USE_PORTFOLIO_PORT`, `USE_OPTIMIZATION_PORT` |
| **App Layer** | `USE_APP_LAYER=true` |

Ver `docs/MIGRATION_STATUS.md` para descripción completa de cada variable.

### Patrón de Migración V7: Shim como Puente Puro

**REGLA DE ORO**: El shim NO reimplementa lógica, solo traduce interfaces.

```
┌─────────────────────────────────────────────────────────────┐
│  ARQUITECTURA DE MIGRACIÓN (STRANGLER FIG)                  │
├─────────────────────────────────────────────────────────────┤
│  V7 Request → Shim → Legacy Service → Failover completo    │
│                ↓                                            │
│           Si falla → Cooldown 5min → Legacy Gateway         │
└─────────────────────────────────────────────────────────────┘
```

**Principios del Patrón:**
1. **Shim = Traductor puro** - Solo convierte Request/Response entre interfaces
2. **Container controla ciclo de vida** - Inyecta dependencias, maneja cooldowns
3. **Fallback automático** - Si V7 falla → legacy por 5 min → retry
4. **Sin lazy-loading** - Evita violación de cooldown
5. **Tests cubren 3 escenarios**: fallo inicial, degradación mid-operation, cooldown

**Archivos clave del patrón:**
```python
# Container (omnix_services/ai_service/container.py)
_is_v7_shim_in_cooldown()  # Previene hot-loops
_reset_v7_shim()            # Limpia shim + manager + timestamp
fallback_to_legacy = True   # Flag para mismo-request fallback

# Shim (src/omnix/infrastructure/adapters/ai_gateway_shim.py)
def _get_manager(self):
    return self._ai_models_manager  # NO lazy-load, solo injected
```

**Para aplicar a nuevos ports:**
1. Crear shim que SOLO traduzca interfaces
2. Usar container para inyectar servicio legacy
3. Implementar cooldown con `_reset_*_shim()` y `_is_*_in_cooldown()`
4. Tests: fallo inicial, degradación, cooldown

| Componente | Estado |
|------------|--------|
| 17/17 Ports definidos | ✅ Completo |
| 19/19 Adapters implementados | ✅ Completo |
| Domain Layer | ✅ Completo |
| Application Layer (5 Use Cases) | ✅ Completo |
| DI Container | ✅ 535+ líneas |

**Estado:**
- ✅ Todos los ports activos (100%)

Ver `docs/current/HEXAGONAL_MIGRATION_STATUS.md` para detalle completo.

### Current Structure
```
OMNIX/
├── src/omnix/           <- Hexagonal V7.0 (100% implementado)
│   ├── ports/           <- 17 protocols (15 driven + 2 driver)
│   ├── infrastructure/  <- 19 adapters
│   ├── domain/          <- Entities, VOs, 10 strategies
│   ├── application/     <- 5 use cases
│   └── bootstrap/       <- DI Container (535+ líneas)
├── omnix_core/          <- Legacy runtime (essential)
├── omnix_services/      <- Legacy services (essential)
├── omnix_config/        <- Configuration (essential)
├── omnix_dashboard/     <- Dashboard (essential)
├── omnix_api/           <- API (essential)
├── omnix_testing/       <- Dev/backtesting tools
├── docs/                <- Documentation (reorganizada 18 Dic)
├── tests/               <- Test suite (120/120 pasando)
├── scripts/             <- Utility scripts
└── sql/                 <- Migrations
```

### Documentation Structure (Updated Dec 16, 2025)
```
docs/
├── README.md                 <- Índice principal
├── MIGRATION_STATUS.md       <- Estado V7.0 consolidado
├── current/                  <- Arquitectura actual
├── operations/               <- DEPLOYMENT.md, configuración
├── reference/                <- TRACEABILITY_MATRIX.md, ADRs
├── business/investor/        <- Pitch deck, proyecciones
├── compliance/audits/        <- Reportes de auditoría
└── history/                  <- Archivados por mes (2025-11/, 2025-12/)
```

### Key Documents
- `docs/MIGRATION_STATUS.md` - Estado consolidado V7.0
- `docs/reference/TRACEABILITY_MATRIX.md` - 123 componentes mapeados
- `docs/current/COMPLETE_FUNCTIONALITY_MAP.md` - 11 dominios, 346 archivos