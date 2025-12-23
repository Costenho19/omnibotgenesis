# OMNIX V6.5.4d INSTITUTIONAL+

---
## MANDATORY PROTOCOL - READ FIRST
---

> **BEFORE making ANY code changes, you MUST review the documentation in `docs/` to understand the current system state.**
> 
> **AFTER making significant changes, you MUST update the relevant documentation.**
> 
> **Failure to follow this protocol leads to inconsistencies, bugs, and wasted effort.**

See [Protocolo de Contexto](#protocolo-de-contexto-obligatorio) below for the complete checklist.

---

## Overview
OMNIX V6.5.4d INSTITUTIONAL+ is an enterprise-grade automated cryptocurrency and stock trading system. Its primary purpose is paper trading to build a credible track record for investor presentations, targeting $1M seed funding at an $11.5M pre-money valuation. Key capabilities include AI integration, post-quantum cryptography, real-time market analysis, Non-Markovian Temporal Memory, adaptive parameter calibration, institutional portfolio optimization, derivatives trading, and dual-market support for Kraken (crypto) and Alpaca (stocks). The system aims for 3-5 trades/day with a 55%+ win rate, multi-crypto scanning, and tiered signal strengths.

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

### Protocolo de Contexto (OBLIGATORIO)

**Antes de ejecutar cualquier cambio**, revisar la documentación en `docs/` para enriquecer el contexto:

| Prioridad | Archivos | Propósito |
|-----------|----------|-----------|
| **1. Crítico** | `docs/README.md` | Índice principal de documentación |
| **2. Crítico** | `docs/MIGRATION_STATUS.md` | Estado consolidado V7.0 |
| **3. Crítico** | `docs/REAL_SYSTEM_STATUS.md` | Estado real del sistema |
| **4. Arquitectura** | `docs/current/` | ARCHITECTURE.md, HEXAGONAL_MIGRATION_STATUS.md, TECHNICAL_DEBT.md |
| **5. Auditorías** | `docs/compliance/audits/` | DATABASE_AUDIT_REPORT.md, INTERNAL_AUDIT_TRANSPARENCY.md |
| **6. Historial** | `docs/history/` | Decisiones previas, migraciones, contexto histórico |
| **7. Referencia** | `docs/reference/` | TRACEABILITY_MATRIX.md, ADRs |

**Después de cambios significativos**, actualizar la documentación relevante.

## System Architecture

### Core Engines
The system integrates AutoTradingBot, Non-Markovian Memory Kernel, Coherence Engine (6-Tier Veto System), AI Risk Guardian, Portfolio Management, CAES (Confidence-Adaptive Entry System), On-Chain Data Intelligence, Execution Protocol, InstitutionalDecisionLogger, and InstitutionalMetricsCalculator.

### Multi-User and Dashboard Architecture

> **ACTUALIZACIÓN (Dec 22, 2025):** Fase 3 + 3b de multi-usuario COMPLETADA - AuthorizationService integrado en AutoTradingBot.
> 
> **Progreso Fase 3 + 3b (AuthorizationService + AutoTradingBot):**
> - ✅ `AuthorizationPort` creado en `src/omnix/ports/driven/authorization_port.py`
> - ✅ `AuthorizationAdapter` con PostgreSQL + Redis cache (5 min TTL)
> - ✅ `UserRole` enum: FREE < BASIC < PRO < PREMIUM < OWNER
> - ✅ `Permission` enum con 15 permisos granulares
> - ✅ 17 hardcoded checks reemplazados en 5 archivos (trading_system, enterprise_bot, auto_trading_bot, performance_optimizer, conversational_ai_adapter)
> - ✅ `_require_trading_permission()` helper en AutoTradingBot
> - ✅ Harold actualizado en BD: `is_admin=true, subscription_tier='owner'`
> - ✅ 36/36 tests de autorización pasando
>
> **Documentación completa:** `docs/current/TECHNICAL_DEBT.md`

**Modo Single-User (Harold):** ✅ SEGURO - OWNER role con permisos completos  
**Modo Multi-Usuario:** ✅ LISTO - Arquitectura completa, activación via feature flag

Features a Flask Dashboard for API and web terminal, and a Streamlit Dashboard for interactive visualization.

#### Asset Quarantine System (Dec 22, 2025)
- **NEW API**: `/api/system/quarantine` - Returns blocked assets and avoided losses
- **Dashboard Integration**: New "Asset Quarantine" page in Streamlit dashboard + Flask header metric
- **Capital Protection**: Shows $6,213+ in avoided losses from blocking ADA, SOL, ETH, AVAX
- **Real Data**: Extracts loss amounts from `trading_profiles.py` EXCLUDED entries
- **Investor-Ready**: Visual display of risk management for pitch presentations

#### Real-Time Latency Monitor (Dec 22, 2025)
- **NEW API**: `/api/system/latency` - Measures actual database and cache response times
- **Dashboard Integration**: Header metric showing live latency in milliseconds
- **Real Measurements**: Uses `time.perf_counter()` for accurate timing of PostgreSQL and Redis
- **Status Indicator**: Green (<10ms optimal), White (normal), Red (>50ms high latency)

#### Price Stale Detection System (Dec 22, 2025)
- **NEW MODULE**: `omnix_services/market_data/validators.py` - Validates price freshness before trading
- **Thresholds**: 30s stale (blocks trading), 20s warning, configurable via `StaleCheckConfig`
- **Trading Integration**: AutoTradingBot blocks trades on stale prices with `PRICE_STALE_VETO`
- **Admin Alerts**: Triggers alerts to OWNER on stale price events via AlertDispatcher
- **Tests**: 12/12 tests passing in `tests/test_price_stale_detection.py`

#### Admin Alerts System (Dec 22, 2025)
- **NEW METHODS**: `AlertDispatcher.add_admin_chat_id()` and `send_admin_alert()` for OWNER-only alerts
- **Event Types**: price_stale, redis_down, api_failure, session_anomaly
- **Cooldown**: 60s per event type to prevent spam
- **Auto-Registration**: TELEGRAM_ADMIN_ID registered on bot startup
- **Location**: `omnix_services/risk_management/alert_dispatcher.py`

#### Investor Dashboard Widgets (Dec 22, 2025)
**Three new investor-facing metrics for pitch presentations:**

1. **Sessions Widget** (`/api/system/sessions`):
   - Shows active PostgreSQL sessions in real-time
   - Displays SaaS scalability capacity (100,000+ concurrent users)
   - Dashboard header metric with "Sessions" label
   - Location: `omnix_dashboard/static/js/components/sessions.js`

2. **Equity Comparison Widget** (`/api/system/equity`):
   - Compares OMNIX performance vs BTC Hold strategy
   - Calculates **Alpha** (outperformance metric): OMNIX return % - BTC return %
   - Shows cumulative P&L curves for both strategies
   - Investor-ready: Proves system adds value beyond passive holding
   - Location: `omnix_dashboard/static/js/components/equitycomparison.js`

3. **Main Driver Badge** (Adaptive Engine Enhancement):
   - Highlights strategy with ≥80% weight as "Main Driver"
   - Currently: **Quantum Momentum (85%)** with ANU QRNG description
   - Shows quantum technology differentiation for investors
   - Location: `omnix_dashboard/static/js/components/adaptive.js`

**Dashboard Integration:**
- 14/14 widgets operational with ~1.5s refresh cycle
- All data sourced from PostgreSQL (109 real trades)
- Zero mock data in production paths

#### Investor-Ready UI Refactor (Dec 23, 2025)
**Eliminated all phrases that could damage investor confidence:**
- **Replaced all `$0.00`, `0.00`, `0%`** placeholders with `--` (loading indicator)
- **Removed `N/A`, `unavailable`, `no disponible`** from all UI components
- **Error states show `Updating...`** instead of error messages
- **Files modified**: `terminal.html`, `dashboard.html`, `utils.js`, `riskguardian.js`, `feargreed.js`, `snapshots.js`, `system.py`, `market.py`, `streamlit_app.py`

**Investor-Safe UI Principle**: Dashboard NEVER shows "data unavailable" - only verified data or silent loading states.

#### Investor-Grade Automated Responses (Dec 23, 2025)
- **NEW MODULE**: `omnix_services/ai_service/investor_responses.py`
- **6 Response Types**: negative_pnl, low_win_rate, hold_strategy, system_validation, risk_management, track_record
- **Real Data**: All responses based on verified PostgreSQL data (109 trades, $7,337 avoided losses)
- **Pattern Detection**: Automatically detects investor questions and returns appropriate response
- **Presentation**: "Investor-grade automated responses" - not "AI creative"
- **Usage**: `investor_response_engine.process_investor_query(message)`

### Trading Profiles System
Configurable profiles (e.g., INSTITUTIONAL, PAPER_AGGRESSIVE, PRODUCTION_STABLE) adjust trading parameters. `PRODUCTION_STABLE V6.5.4c` is the active profile.

### Hexagonal Architecture (V7.0 - Structure Complete, Activation Pending)
The system has a complete hexagonal architecture with **20 ports** (17 driven + 3 driver) and **22 adapters** implemented in `src/omnix/`. New: `AuthorizationPort` + `AuthorizationAdapter` added Dec 22, 2025. **IMPORTANT**: All feature flags are currently `false` - the system operates 100% with legacy code in Railway. Activation is planned via Strangler Fig pattern.

### AI Service Architecture
Refactored with SOLID principles and dependency injection, integrating interfaces and providers (Gemini, OpenAI, Anthropic). Features include a voice service for dual text+audio responses (when `VOICE_SERVICE_AVAILABLE=true`) and AI-first command detection where only messages starting with `/` are treated as commands, otherwise text is sent to AI. The system uses an AI-First Multilingual Prompt Architecture with all system prompts rewritten in English, a Prompt Specification Layer, dynamic language detection, and a Chain-of-Thought Framework.

#### Language Detection AI-First Refactor (Dec 22, 2025)
- **ELIMINATED** hardcoded language detection dictionaries (low quality code)
- **INSTALLED** `fast-langdetect` (FastText-based, 80x faster than langdetect)
- **FLOW**: Long texts (≥50 chars) → FastText | Short texts (<50 chars) → Gemini AI (`gemini-2.0-flash-lite`)
- **TTS MAPPING**: ISO codes to gTTS codes (e.g., zh → zh-CN)
- **RESULT**: 12/12 tests passing

#### AI-First Multilingual Concurrency (Dec 19, 2025)
- **Concurrency-Safe Language Detection**: Uses `threading.Lock` for sync paths and `asyncio.to_thread()` for async paths to prevent language bleed between concurrent users
- **Redis Language Persistence**: Stores detected language per `chat_id` with 24h TTL for fallback scenarios (`omnix:user_language:{chat_id}`)
- **English Universal Placeholders**: All fallback/error messages are minimal English only - AI generates localized responses
- **NO Hardcoded Multilingual Dictionaries**: AI-first means Gemini generates all localized content based on system prompt directive

### Error Handling System
An `ai_error_handler.py` provides an `ErrorClassifier` with 8 categories, SDK-specific error detection, intelligent retry/failover with exponential backoff for retryable errors, and structured logging.

### Web Search Service Architecture
Structured with an `IntentDetector`, `SearchManager`, and `TavilySearch` client for intent-based web searches.

### Current Project Structure
The project is structured with `src/omnix/` containing the hexagonal V7.0 architecture (ports, infrastructure, domain, application, bootstrap), while `omnix_core/`, `omnix_services/`, `omnix_config/`, `omnix_dashboard/`, and `omnix_api/` contain essential legacy components.

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
-   **ANU QRNG**: Quantum random numbers.

### Databases
-   **PostgreSQL (Railway)**: Main persistence for trades, analysis, conversations, balance history, derivatives, community intelligence, risk management, adaptive engine data, and user settings.
-   **Redis (Railway)**: Caching, state management, and rate limiting.