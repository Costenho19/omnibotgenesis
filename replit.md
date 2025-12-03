# OMNIX V6.5.2 INSTITUTIONAL+ - Automated Trading System

## Overview

OMNIX V6.5.2 INSTITUTIONAL+ is an enterprise-grade automated cryptocurrency and stock trading system designed for 24/7 operation with multi-user support for 100,000+ simultaneous users. Its primary purpose is paper trading to build a credible track record for investor presentations, targeting $400K seed funding at $2.5M valuation. Key capabilities include AI integration, post-quantum cryptography, real-time market analysis, Non-Markovian Temporal Memory with On-Chain Data Intelligence, adaptive parameter calibration, institutional portfolio optimization, derivatives trading, and dual-market support for Kraken (crypto) and Alpaca (stocks). The system aims for 20-50 trades/day with a 55%+ win rate, multi-crypto scanning, and tiered signal strengths.

## Recent Changes (Changelog)

### December 2025 - Phase 5: Database Service Unification (In Progress)

**Phase 1 (Discovery & Freeze) ✅ - Dec 3, 2025**
| Task | Status | Description |
|------|--------|-------------|
| Call Site Mapping | ✅ Done | 14 consumers documented (6 Dashboard + 8 Enterprise) |
| Feature Flag | ✅ Done | `DISABLE_AUTO_MIGRATIONS=true` skips 8 auto-migrations |
| Pool Telemetry | ✅ Done | Background thread logs stats every 5min with PID |
| Diagnostics Endpoint | ✅ Done | `/api/db-diagnostics` shows real-time pool health |
| Consumer Migration Order | ✅ Done | Priority sequence documented in DATABASE_AUDIT_REPORT.md |

**Key Files**
- `docs/core/DATABASE_AUDIT_REPORT.md` - Complete audit (~2,200 lines)
- `omnix_services/database_service/database_service.py` - Feature flag implementation
- `omnix_dashboard/utils/database.py` - Telemetry thread with proper shutdown
- `omnix_dashboard/blueprints/system.py` - `/api/db-diagnostics` endpoint

**Phase 2 (Build Unified Gateway) - DOCUMENTED Dec 3, 2025**
| Section | Content | Lines |
|---------|---------|-------|
| 15.1 Architecture | Single pool, dual interfaces | ~50 |
| 15.2-15.3 Gateway Code | Fork-safe singleton, execute_query() | ~200 |
| 15.4.1 Gunicorn Hook | post_fork reinit, Railway Procfile | ~50 |
| 15.4.2 Row Access Audit | 6 consumers checked, 1 needs fix | ~60 |
| 15.4.3 Import Validation | 4-step check, CI gating | ~40 |
| 15.5 Migration Order | 9 consumers prioritized | ~30 |
| 15.6 Task Checklist | 18 tasks with owner/risk | ~40 |
| 15.9 Railway Checklist | 18-step deployment guide | ~40 |

**COMPLETED Dec 3, 2025**:
- ✅ `database_gateway.py` created with fork-safe singleton, dual interfaces
- ✅ `auto_trading_bot.py` dict-style bugs fixed (lines 787, 839, 908, 2050) → tuple access

**Next Steps**:
1. User provides 48h Railway telemetry logs
2. Agent analyzes logs and determines optimal pool size
3. Migrate Dashboard consumers to use DatabaseGateway
4. Canary deployment with USE_UNIFIED_GATEWAY flag

### December 2025 - Phase 4: Frontend Optimization ✅

**Modular JavaScript Architecture**
| Module | Purpose | Key Features |
|--------|---------|--------------|
| `js/core/api.js` | API client | `fetchWithRetry()` with exponential backoff (3 retries, 1-10s delays) |
| `js/core/common.js` | Shared logic | `startAutoRefresh()`, `refreshWidgets()`, `updateTimestamp()` |
| `js/components/charts.js` | Chart management | `Plotly.react()` for delta updates, instance tracking |

**Frontend Issues Fixed**
| Issue | Problem | Solution | Impact |
|-------|---------|----------|--------|
| #12 | Full Plotly re-render (expensive) | `Plotly.react()` for delta updates | -70% CPU |
| #13 | No retry/backoff | Exponential backoff with jitter | Network resilience |
| #14 | Promise.all without granularity | Independent widget error handling | No cascade failures |
| #15 | Duplicated JS logic | Extracted to `common.js` | -165 lines code |

**Script Load Order (base.html)**
```
api.js → utils.js → clock.js → charts.js → common.js → [page scripts]
```

### December 2025 - Phase 3: Dashboard Data Reliability

**V6.5.2 Import Fix**
- Fixed `get_redis_cache` import error blocking auto-restore after Railway restarts
- Created function in `omnix_core/cache/redis_cache.py` and exported via `__init__.py`

**Dashboard Data Issues Fixed**
| Issue | Problem | Solution | Files Modified |
|-------|---------|----------|----------------|
| #8 | DB failures returned empty `[]` | `get_paper_trades(return_dict=True)` returns `{success, trades, error, db_connected}` | `queries.py`, `core.py` |
| #9 | Static status bar (hardcoded) | New `statusbar.js` polls `/api/health` every 15s, updates DOM dynamically | `statusbar.js`, `terminal.html`, `dashboard.html` |
| #10 | No Paper/Real mode indicator | Prominent orange "PAPER TRADING" badge in both dashboards | `terminal.html`, `dashboard.html` |
| #11 | No price fallback | `/api/positions` uses Kraken first, CoinGecko as automatic fallback | `core.py` |

**Auto-Trading Quality Focus**
- Coherence Engine maintains strict 45% threshold
- Prioritizes quality over quantity to maintain zero losses
- System rejects low-quality signals to protect capital

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
> 2. **APAGAR el workflow del bot ANTES de terminar la sesión**
> 3. Verificar que el workflow esté detenido
>
> **Razón**: Telegram solo permite UNA conexión activa por token. Si el bot corre en Replit y Railway al mismo tiempo, habrá conflictos y errores de conexión.

## System Architecture

### Core Engines

The system is built around several core engines:

-   **AutoTradingBot V6.4 PREMIUM**: Features multi-crypto scanning, tiered signal strength, a ramp-up system, HMM quality filter for confidence-weighted regime detection, and drawdown protection.
-   **Non-Markovian Memory Kernel V6.5**: Detects regime transitions, recognizes cyclical patterns, performs memory coherence scoring, and integrates on-chain signals.
-   **Coherence Engine V6.5 ULTRA**: Utilizes a 6-Tier Veto System for validating strategy agreement. Uses consistent thresholds (30%/45%) for both Paper and Real modes to maintain trade quality and win rate > 55%.
-   **Multi-Crypto Scanner V6.5**: Scans 11 crypto pairs (BTC, ETH, SOL, XRP, ADA, DOT, LINK, AVAX, MATIC, ATOM, LTC) with proper Kraken symbol mapping (BTC→XBT).
-   **AI Risk Guardian V5.4**: Monitors for overtrading, drawdown, and prevents revenge trading.
-   **Portfolio Management V6.4 INSTITUTIONAL+** implements Goldman-Sachs level optimization, including Markowitz and Black-Litterman models, dynamic position sizing, exposure management, and risk detection.
-   **Derivatives Trading Module**: Supports paper/real trading modes and includes a MarginEngine, KrakenFuturesClient, HedgingService, and FundingArbitrageAnalyzer.
-   **Stock Trading Premium V6.3 ULTRA**: Integrates 9 active institutional modules: Monte Carlo, Kalman Filter, HMM, ARES-STOCK, Non-Markovian Memory, Coherence Engine, Risk Guardian, Gap Protection, and Earnings Protector.
-   **Adaptive Parameter Engine V6.5 ULTRA**: An auto-calibration system for ARES strategies based on market regime. It includes a RegimeSignalProcessor, ParameterCalibrator, CooldownManager, MicrostructureAnalyzer, and safety features.
-   **On-Chain Data Intelligence V6.5**: Provides institutional-grade blockchain analytics using free APIs, featuring WhaleTracker, Arkham Intelligence Integration, ExchangeFlowAnalyzer, NetworkMetricsCollector, and SmartMoneySignal.

### Multi-User Architecture V6.5.2

-   Supports 100,000+ simultaneous users with isolated trading sessions.
-   Utilizes Redis for fast state management and PostgreSQL for persistence.
-   Employs a ThreadPoolExecutor for parallel processing of user sessions and per-user locks for thread safety.

### UI/UX Decisions

The system includes a web dashboard built with Flask, providing multiple views (main, terminal-style, classic) and a comprehensive set of API endpoints for performance metrics, trading data, market data, market intelligence, and system status. The frontend uses Modular CSS (BEM Methodology) and Modular JavaScript (IIFE Pattern), with Jinja2 template inheritance for a consistent user experience.

### Backend Architecture

The backend utilizes a Flask Blueprints architecture for modularity, with separate blueprints for views, core APIs, market data, intelligence, and system status. Key improvements include an application factory pattern, connection pooling for PostgreSQL, and modular route organization. ARES strategies are instantiated at the module level for correct initialization.

### Dashboard Data Handling (Phase 3 - Dec 2025)

- **Proper Error Responses**: `get_paper_trades()` now supports `return_dict=True` parameter returning `{success, trades, error, db_connected}` instead of empty arrays.
- **Dynamic Status Bar**: `statusbar.js` polls `/api/health` every 15s and updates BOT/DATABASE/KRAKEN status indicators in real-time.
- **PAPER TRADING Badge**: Prominent orange badge in both terminal.html and dashboard.html clearly indicates paper trading mode.
- **Price Fallback System**: `/api/positions` uses Kraken API first, with CoinGecko as automatic fallback when Kraken fails.

### Dashboard API Endpoints

| Endpoint | Purpose | Response Format |
|----------|---------|-----------------|
| `/api/health` | System health check | `{status, version, db_connected, db_error, pool, architecture, timestamp}` |
| `/api/metrics` | Trading performance | `{success, metrics, error, db_connected}` |
| `/api/trades` | Paper trade history | `{success, trades, error, db_connected}` |
| `/api/positions` | Open positions with live prices | `{success, positions, summary, price_source, db_connected}` |
| `/api/ticker` | Real-time crypto prices | `{prices, source, timestamp}` |
| `/api/fear-greed` | Market sentiment index | `{value, classification, timestamp}` |

### Dashboard Files Structure

```
omnix_dashboard/
├── blueprints/
│   └── core.py              # Main API routes (/api/*)
├── utils/
│   ├── database.py          # PostgreSQL connection pool
│   └── queries.py           # DB query functions
├── static/js/components/
│   ├── statusbar.js         # Dynamic status bar (polls /api/health)
│   ├── charts.js            # Trading charts
│   ├── ticker.js            # Price ticker
│   └── ...
└── templates/
    ├── terminal.html        # Bloomberg-style terminal view
    └── dashboard.html       # Main dashboard view
```

### Data Flow

Market Data (Kraken/Alpaca) feeds into the Non-Markovian Kernel, boosted by On-Chain Intelligence. This leads to Regime Detection and Signal Generation, feeding the Adaptive Parameter Engine. After Coherence Engine Validation and a Risk Guardian Check, trades are executed, persisted in PostgreSQL, and notifications are sent via Telegram.

### Project Structure

The project is organized into `omnix_core/` (core trading logic), `omnix_services/` (various system services), `omnix_dashboard/` (Flask web interface), `omnix_api/` (REST API), and `omnix_testing/` (validation suite).

## External Dependencies

### APIs and Services

-   **Kraken Exchange**: Primary crypto data and order execution.
-   **Alpaca**: Stock data and historical bars.
-   **Google Gemini (2.0 Flash)**: Primary AI model.
-   **OpenAI (GPT-4o, Whisper)**: AI services and transcription.
-   **Anthropic Claude**: AI fallback.
-   **CoinGecko**: Backup crypto prices.
-   **ClankApp**: Whale transaction tracking.
-   **Arkham Intelligence**: Wallet identity enrichment.
-   **Alternative.me**: Fear and Greed Index.
-   **Finnhub**: Market news and sentiment.
-   **Alpha Vantage**: Technical indicators.
-   **ANU QRNG**: Quantum random numbers.
-   **Stripe**: Payment processing.

### Databases

-   **PostgreSQL (Railway)**: Main persistence for trades, analysis, conversations, balance history, derivatives, community intelligence, risk management, adaptive engine data, and user settings.
-   **Redis (Railway)**: Used for caching, state management, and rate limiting.

### Key Python Libraries

-   **Core Trading**: numpy, scipy, ccxt, pandas
-   **AI/ML**: google-generativeai, openai, anthropic
-   **Telegram**: python-telegram-bot
-   **Database**: psycopg (v3), redis
-   **HTTP**: requests, aiohttp, httpx, websockets
-   **Security**: pypqc (post-quantum)
-   **Reporting**: plotly, kaleido, reportlab, PyPDF2