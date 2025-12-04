# OMNIX V6.5.2 INSTITUTIONAL+ - Automated Trading System

## Overview

OMNIX V6.5.2 INSTITUTIONAL+ is an enterprise-grade automated cryptocurrency and stock trading system designed for 24/7 operation with multi-user support for 100,000+ simultaneous users. Its primary purpose is paper trading to build a credible track record for investor presentations, targeting $400K seed funding at $2.5M valuation. Key capabilities include AI integration, post-quantum cryptography, real-time market analysis, Non-Markovian Temporal Memory with On-Chain Data Intelligence, adaptive parameter calibration, institutional portfolio optimization, derivatives trading, and dual-market support for Kraken (crypto) and Alpaca (stocks). The system aims for 20-50 trades/day with a 55%+ win rate, multi-crypto scanning, and tiered signal strengths.

## Recent Changes (Changelog)

### December 2025 - Phase 5: Database Service Unification (In Progress)

**Phase 1 (Discovery & Freeze) - Dec 3, 2025**
| Task | Status | Description |
|------|--------|-------------|
| Call Site Mapping | Done | 14 consumers documented (6 Dashboard + 8 Enterprise) |
| Feature Flag | Done | `DISABLE_AUTO_MIGRATIONS=true` skips 8 auto-migrations |
| Pool Telemetry | Done | Background thread logs stats every 5min with PID |
| Diagnostics Endpoint | Done | `/api/db-diagnostics` shows real-time pool health |

**Phase 2 (Build Unified Gateway) - IMPLEMENTED Dec 3, 2025**:
- `database_gateway.py` created with fork-safe singleton, dual interfaces
- `auto_trading_bot.py` dict-style bugs fixed (lines 787, 839, 908, 2050) to tuple access
- Feature flag `USE_UNIFIED_GATEWAY` added to `database.py` (defaults false)
- Gunicorn `post_fork` hook configured in `gunicorn.conf.py`
- Dashboard consumers auto-migrated via `get_db_connection()` abstraction
- Smoke test passed: 7 real trades, 11/11 widgets OK with gateway enabled

**System Contract**: All modules use tuple-based rows `row[n]` (psycopg3 default), NOT dict access.

**Canary Deployment Ready** (Railway):
1. Set `USE_UNIFIED_GATEWAY=true` on single worker
2. Monitor telemetry for 48h
3. Optimize pool sizing based on metrics
4. Expand to all workers if stable

**Schema Fix: pending_evaluations - Dec 4, 2025**
| Change | Description |
|--------|-------------|
| Added `trade_id` | INTEGER column for trade reference |
| Added `due_time` | TIMESTAMP with default NOW() for scheduling |
| Added `conditions` | JSONB with default '{}' for evaluation conditions |
| Added `status` | VARCHAR(50) with default 'pending' for workflow state |
| Created Index | `idx_pending_evaluations_status_due_time` for query optimization |
| Backfill Logic | `entity_id` to `trade_id` where `entity_type='trade'`, `metadata` to `conditions` |

This fix resolves the error: `column "trade_id" does not exist` in `DatabaseManager.get_due_evaluations()`.

**DATABASE_AUDIT_REPORT.md Reorganization - Dec 4, 2025**
| Change | Description |
|--------|-------------|
| Reduced Size | 2699 → ~600 lines (73% reduction) |
| Added Dashboard | Section 2 shows quick status, phase progress, blockers |
| Consolidated Integrity | Section 3 with full 34-table FK list in 3.1.3 |
| Created Playbooks | Section 5 with SQL templates for each phase |
| Added Appendix | Schema reference with 45-table catalog |
| Added Revision History | Version tracking from 1.0 to 3.0 |

Reference document: `docs/core/DATABASE_AUDIT_REPORT.md`

**Technical Reference Document Created - Dec 4, 2025**
| Metric | Value | Source |
|--------|-------|--------|
| Total Python Files | 220+ | Measured via find/wc |
| omnix_core Lines | 20,131 | Verified |
| omnix_services Lines | 62,613 | Verified |
| omnix_dashboard Lines | 9,037 | Verified |
| Total Codebase | ~100,000 lines | Measured |

Comprehensive technical reference created from exhaustive code analysis of all packages:
- Complete module inventory with verified line counts
- Database-to-code mapping
- Dependency matrix (internal/external)
- Architecture contracts documented
- Legacy code identified

Reference document: `docs/core/Omnix_TECHNICAL_REFERENCE.md`

**Phase 3 (Data Integrity Hardening) - COMPLETED Dec 4, 2025**
| Task | Status | Description |
|------|--------|-------------|
| Orphan Scan | Done | 34/34 tables scanned, 33 clean, 1 resolved |
| System User | Done | Created `user_id='system'` for orphan resolution |
| FK Batch 1-3 | Done | 34 new FKs added (analytics, risk, trading) |
| Total FKs | Done | 41 FKs (91% coverage), exceeded 40% target |
| Dashboard | Done | 11/11 widgets OK, 7 real trades verified |

All FK constraints use `DEFERRABLE INITIALLY DEFERRED` for transaction safety.

**Dependency Update - Dec 4, 2025**
| Package | Old Version | New Version | Impact |
|---------|-------------|-------------|--------|
| anthropic | 0.51.0 | 0.75.0 | Model name changes future-proofed |
| python-telegram-bot | 20.7 | 21.9 | No breaking changes (no deprecated APIs used) |
| psycopg | 3.2.4 | 3.3.1 | Tuple-based row access preserved |
| pandas | 2.2.2 | 2.2.3 | Bug fixes only |
| scipy | 1.14.0 | 1.14.1 | Security fix, no API changes used |
| ccxt | 4.4.35 | 4.5.24 | Exchange updates, API stable |
| httpx | 0.27.0 | 0.27.2 | Required by PTB 21.9 |

**Verification Completed**:
- Dashboard: 11/11 widgets OK
- Database: 7 real trades confirmed (psycopg 3.3.1)
- Imports: All critical modules verified
- Contract: Tuple-based `row[n]` access preserved

**Legacy Code Cleanup - Dec 4, 2025**
| Action | Location | Result |
|--------|----------|--------|
| DELETED | `omnix_core/models/` | Empty folder removed (0 imports) |
| DELETED | `omnix_core/queue/` | Empty folder removed (0 imports) |
| DELETED | `omnix_services/trading_service/pqc_security.py` | 162-line duplicate removed (0 imports) |
| FIXED | `omnix_core/strategies/__init__.py` | Added exports for AresProtocolV1, V2, NonMarkovianKernel |
| FIXED | `omnix_core/security/__init__.py` | Added exports for PostQuantumSecurity |
| FIXED | `omnix_services/__init__.py` | Added exports for NewsScraperService, SymbolClassifier |

**Note**: Paper trading modules (`omnix_core/bot/paper_trading.py` and `omnix_services/.../paper_trading_manager.py`) were kept - both are actively used by different bot components.

Reference document: `docs/core/Omnix_TECHNICAL_REFERENCE.md` (Section 9)

**Table Consolidation - Dec 4, 2025**
| Action | Table Dropped | Reason |
|--------|---------------|--------|
| DROPPED | `circuit_breaker_states` | 0 rows, 0 code refs, duplicate of `circuit_breaker_status` |
| DROPPED | `risk_guardian_logs` | 0 rows, 0 code refs, duplicate of `risk_guardian_events` |
| DROPPED | `trading_history` | 0 rows, 0 code refs, duplicate of `paper_trading_trades` |

**Results:**
- Tables: 45 → 42 (3 redundant dropped)
- FKs: 41 → 38 (adjusted after consolidation, 90% coverage)
- Dashboard: 11/11 widgets verified OK

Reference document: `docs/core/DATABASE_AUDIT_REPORT.md` (Section 3.2, Phase 3.7)

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

-   **AutoTradingBot V6.4 PREMIUM**: Multi-crypto scanning, tiered signal strength, ramp-up system, HMM quality filter, drawdown protection.
-   **Non-Markovian Memory Kernel V6.5**: Detects regime transitions, recognizes cyclical patterns, performs memory coherence scoring, and integrates on-chain signals.
-   **Coherence Engine V6.5 ULTRA**: 6-Tier Veto System for validating strategy agreement, maintaining consistent thresholds (30%/45%) for trade quality and win rate > 55%.
-   **Multi-Crypto Scanner V6.5**: Scans 11 crypto pairs with proper Kraken symbol mapping.
-   **AI Risk Guardian V5.4**: Monitors for overtrading, drawdown, and prevents revenge trading.
-   **Portfolio Management V6.4 INSTITUTIONAL+**: Goldman-Sachs level optimization, Markowitz and Black-Litterman models, dynamic position sizing.
-   **Derivatives Trading Module**: Paper/real trading modes, MarginEngine, KrakenFuturesClient, HedgingService.
-   **Stock Trading Premium V6.3 ULTRA**: 9 active institutional modules: Monte Carlo, Kalman Filter, HMM, ARES-STOCK, Non-Markovian Memory, Coherence Engine, Risk Guardian, Gap Protection, Earnings Protector.
-   **Adaptive Parameter Engine V6.5 ULTRA**: Auto-calibration for ARES strategies based on market regime.
-   **On-Chain Data Intelligence V6.5**: Institutional-grade blockchain analytics using free APIs.

### Multi-User Architecture V6.5.2

-   Supports 100,000+ simultaneous users with isolated trading sessions.
-   Redis for fast state management and PostgreSQL for persistence.
-   ThreadPoolExecutor for parallel processing, per-user locks for thread safety.

### Dashboard API Endpoints

| Endpoint | Purpose | Response Format |
|----------|---------|-----------------|
| `/api/health` | System health check | `{status, version, db_connected, db_error, pool, architecture, timestamp}` |
| `/api/metrics` | Trading performance | `{success, metrics, error, db_connected}` |
| `/api/trades` | Paper trade history | `{success, trades, error, db_connected}` |
| `/api/positions` | Open positions with live prices | `{success, positions, summary, price_source, db_connected}` |
| `/api/ticker` | Real-time crypto prices | `{prices, source, timestamp}` |
| `/api/fear-greed` | Market sentiment index | `{value, classification, timestamp}` |

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
