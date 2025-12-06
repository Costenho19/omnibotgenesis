# OMNIX V6.5.4 INSTITUTIONAL+ - Automated Trading System

## Overview

OMNIX V6.5.4 INSTITUTIONAL+ is an enterprise-grade automated cryptocurrency and stock trading system designed for 24/7 operation with multi-user support. Its primary purpose is paper trading to build a credible track record for investor presentations, targeting $400K seed funding at $2.5M valuation. Key capabilities include AI integration, post-quantum cryptography, real-time market analysis, Non-Markovian Temporal Memory with On-Chain Data Intelligence, adaptive parameter calibration, institutional portfolio optimization, derivatives trading, and dual-market support for Kraken (crypto) and Alpaca (stocks). The system aims for 20-50 trades/day with a 55%+ win rate, multi-crypto scanning, and tiered signal strengths.

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

-   **AutoTradingBot V6.5.4 INSTITUTIONAL+**: Multi-crypto scanning, tiered signal strength, ramp-up system, HMM quality filter, drawdown protection, V6.5.4 position limit early-check.
-   **Non-Markovian Memory Kernel V6.5**: Detects regime transitions, recognizes cyclical patterns, performs memory coherence scoring, and integrates on-chain signals.
-   **Coherence Engine V6.5 ULTRA**: 6-Tier Veto System for validating strategy agreement, maintaining consistent thresholds (30%/45%) for trade quality and win rate > 55%.
-   **Multi-Crypto Scanner V6.5**: Scans 11 crypto pairs with proper Kraken symbol mapping.
-   **AI Risk Guardian V5.4**: Monitors for overtrading, drawdown, and prevents revenge trading.
-   **Portfolio Management V6.4 INSTITUTIONAL+**: Goldman-Sachs level optimization, Markowitz and Black-Litterman models, dynamic position sizing.
-   **Derivatives Trading Module**: Paper/real trading modes, MarginEngine, KrakenFuturesClient, HedgingService.
-   **Stock Trading Premium V6.3 ULTRA**: 9 active institutional modules: Monte Carlo, Kalman Filter, HMM, ARES-STOCK, Non-Markovian Memory, Coherence Engine, Risk Guardian, Gap Protection, Earnings Protector.
-   **Adaptive Parameter Engine V6.5 ULTRA**: Auto-calibration for ARES strategies based on market regime.
-   **CAES V6.5.4 (Confidence-Adaptive Entry System)**: Dynamic position sizing based on Non-Markovian Kernel confidence using sigmoid aggression function. Caps: 0.5x-3.0x multiplier with safety limits. V6.5.4: No artificial bias applied.
-   **On-Chain Data Intelligence V6.5**: Institutional-grade blockchain analytics using free APIs.
-   **Fear & Greed Contrarian Strategy V6.5.4**: Applies in both paper and real modes with appropriate contrarian and extreme fear boosts.
-   **AI Risk Guardian V6.5.4 Hard Cap**: $20K max trade size absolute limit. min(size, MAX_LIMIT) without exceptions.
-   **Web Search Service V6.5.4**: Real-time internet search via Tavily API. Auto-detects queries about news/events/current data. Redis cache (15min TTL), rate limiting (30/min).

### Multi-User Architecture V6.5.2

-   Supports 100,000+ simultaneous users with isolated trading sessions.
-   Utilizes Redis for fast state management and PostgreSQL for persistence.
-   Employs ThreadPoolExecutor for parallel processing and per-user locks for thread safety.

### Dashboard API Endpoints

-   Provides various API endpoints for system health, trading performance, paper trade history, open positions, real-time prices, market sentiment, database diagnostics, and adaptive engine telemetry.

### Trading Profiles System

-   Configurable profiles (INSTITUTIONAL, PAPER_AGGRESSIVE, BALANCED) to switch between conservative and aggressive settings for trading parameters like Coherence Engine veto, Ramp-Up System, Score Thresholds, HMM VETO, and Regime Change VETO.

### Architecture Modernization V7.0 (Planned)

-   Planned refactoring to Hexagonal Architecture with Ports & Adapters, SOLID Principles, and Dependency Injection using `dependency-injector` for a more modular and maintainable codebase.

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
-   **Tavily**: Real-time web search for AI responses (1,000 free/month).
-   **ANU QRNG**: Quantum random numbers.

### Databases

-   **PostgreSQL (Railway)**: Main persistence for trades, analysis, conversations, balance history, derivatives, community intelligence, risk management, adaptive engine data, and user settings.
-   **Redis (Railway)**: Caching, state management, and rate limiting.

### Key Python Libraries

-   **Core Trading**: numpy, scipy, ccxt, pandas
-   **AI/ML**: google-generativeai, openai, anthropic
-   **Telegram**: python-telegram-bot
-   **Database**: psycopg (v3), redis
-   **HTTP**: requests, aiohttp, httpx, websockets
-   **Security**: pypqc (post-quantum)
-   **Reporting**: plotly, kaleido, reportlab, PyPDF2

## Technical Documentation

**Location:** `docs/core/`

| Document | Purpose |
|----------|---------|
| `Omnix_TECHNICAL_REFERENCE.md` | Complete system architecture reference (V3.0) |
| `OMNIX_MODULE_CATALOG.md` | Exhaustive module inventory (~95,000 lines cataloged) |
| `TRADING_FLOW_ARCHITECTURE.md` | Trading execution flow with ASCII diagrams |
| `DATABASE_AUDIT_REPORT.md` | Database schema and FK constraints (42 tables) |
| `DASHBOARD_TECHNICAL_REFERENCE.md` | Flask dashboard documentation |

### Documentation Policy (MANDATORY - HIGH PRIORITY)

> **REGLA OBLIGATORIA - CICLO COMPLETO**: Todo flujo de trabajo en OMNIX:
> 
> ## INICIO → Consultar documentación
> **ANTES** de cualquier modificación o desarrollo, el agente DEBE consultar `docs/core/`:
> - `OMNIX_MODULE_CATALOG.md` → Inventario de módulos y ubicaciones
> - `Omnix_TECHNICAL_REFERENCE.md` → Arquitectura y patrones
> - `TRADING_FLOW_ARCHITECTURE.md` → Flujo de ejecución de trades
> - `DATABASE_AUDIT_REPORT.md` → Schema de BD y constraints
> - `DASHBOARD_TECHNICAL_REFERENCE.md` → APIs, seguridad y frontend del dashboard
>
> ## FIN → Actualizar documentación
> **DESPUÉS** de completar cualquier cambio, el agente DEBE actualizar `docs/core/`:
> - Nuevos módulos o servicios
> - Cambios en flujos de trading
> - Modificaciones de schema de BD
> - Nuevos endpoints de API
> - Cambios de versión o configuración
>
> ## Verificación
> El código y la documentación deben estar en **TOTAL CONCORDANCIA** antes de cerrar cualquier tarea.
>
> **Razón**: Esta política garantiza que el agente tenga contexto completo del sistema (~95,000 líneas de código) y mantenga la coherencia entre código y documentación para presentaciones a inversores.

## Codebase Statistics (December 6, 2025)

| Package | Modules | Lines |
|---------|---------|-------|
| omnix_core | 20 | ~20,131 |
| omnix_services | 150+ | ~62,613 |
| omnix_dashboard | 40+ | ~9,037 |
| **Total** | **160+** | **~95,000** |

## Version Control (SINGLE SOURCE OF TRUTH)

**Location:** `omnix_config/settings.py`

```python
VERSION = "6.5.4"
VERSION_NAME = "INSTITUTIONAL+"
VERSION_BANNER = f"V{VERSION} {VERSION_NAME}"
```

**Usage in any module:**
```python
from omnix_config import VERSION_BANNER
logger.info(f"[{VERSION_BANNER}] Sistema iniciado...")
```

> **REGLA**: Para cambiar la versión del sistema, solo modifica `omnix_config/settings.py`. Todos los logs y mensajes usarán automáticamente la nueva versión.

## Recent Changes

- **Dec 6, 2025**: Web Search Integration - New `web_search_service/` module with Tavily API. Bot auto-searches internet for news/events queries. Redis cache + rate limiting.
- **Dec 6, 2025**: Runtime Bug Fixes (Phase 4.6) - 3 fixes from expert log analysis:
  - FIX 1: tuple.get() error in session restore (psycopg3 returns tuples)
  - FIX 2: Monte Carlo win_rate 0.5% → 50% formatting (decimal normalization)
  - FIX 3: QRNG fallback log spam reduced (WARNING → INFO)
- **Dec 6, 2025**: Defensive Migrations (Phase 4.5) - FK/CHECK/Cleanup skip missing columns
- **Dec 6, 2025**: Centralized Version Control - Single source of truth in `omnix_config/settings.py`. Removed ~300 hardcoded V6.5.x references across codebase.
- **Dec 6, 2025**: V6.5.4 Institutional Fixes - 4 critical corrections:
  - FIX 1: Position limits checked at START of cycle (saves CPU)
  - FIX 2: Hard cap absoluto en Risk Guardian ($20K max)
  - FIX 3: Coherencia sin bypass para paper mode (track record replicable)
  - FIX 4: Eliminado FLOOR_RESCUE/RECOVERY bias (era revenge trading)
- **Dec 6, 2025**: Complete module audit and documentation update to V6.5.3
- **Dec 5, 2025**: Gemini 2.0 SDK migration (google-genai)
- **Dec 4, 2025**: Database audit - 42 tables, 38 FKs (90% coverage)