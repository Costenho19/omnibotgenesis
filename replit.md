# OMNIX V6.5.4d INSTITUTIONAL+

## Overview
OMNIX V6.5.4d INSTITUTIONAL+ is an enterprise-grade automated cryptocurrency and stock trading system designed for paper trading to build a credible track record for investor presentations. Its core capabilities include AI integration, post-quantum cryptography, real-time market analysis, Non-Markovian Temporal Memory, adaptive parameter calibration, institutional portfolio optimization, derivatives trading, and dual-market support for Kraken (crypto) and Alpaca (stocks). The system targets 3-5 trades/day with a 55%+ win rate and focuses on an "Investor-Ready" presentation to secure seed funding.

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

### Core Components and Design Patterns
The system integrates several core engines: AutoTradingBot, Non-Markovian Memory Kernel, Coherence Engine (6-Tier Veto System), AI Risk Guardian, Portfolio Management, CAES (Confidence-Adaptive Entry System), On-Chain Data Intelligence, Execution Protocol, InstitutionalDecisionLogger, and InstitutionalMetricsCalculator. It supports multi-user modes with granular role-based permissions and features Flask and Streamlit dashboards for API access, web terminal, and interactive visualization. Key features include an Asset Quarantine System, Real-Time Latency Monitor, Price Stale Detection System, and Admin Alerts. The UI is designed for an "Investor-Ready" presentation, and Investor-Grade Automated Responses use institutional language. The Decision Engine incorporates an EMA Regime Signal as the primary driver, a Monte Carlo VETO Engine for risk enforcement, and robust RMS Enforcement. All decisions are fully auditable via a `decision_trace`. Defensive hardening includes Position Size Factor Clamping and Veto Sentinel Logs. The system is designed with a hexagonal architecture (V7.0) with planned activation via the Strangler Fig pattern, coexisting with legacy components.

### AI Architecture and Enforcement
The AI service is refactored with SOLID principles and dependency injection, supporting multiple AI providers. It features an AI-first command detection, a Multilingual Prompt Architecture with dynamic language detection, and a Chain-of-Thought Framework. A critical AI Institutional Language Enforcement system ensures responses use approved institutional phrasing, blocking blacklisted terms and enforcing a "founder controlling risk" narrative. An AI Self-Knowledge System, driven by `system_state_manifest.json`, prevents AI "hallucinations" about system status.

### Hierarchical Veto Flow
The execution order is: 1. MC VETO → 2. RMS VETO → 3. **COHERENCE GATE** → 4. Scoring → 5. Decision. Coherence now blocks low-quality signals BEFORE scoring computation, with critical thresholds reducing false positives.

### Scoring Logic
Scoring is based on 5 core inputs: EMA Regime Signal (40 pts, PRIMARY DRIVER), HMM Regime (25 pts), Kalman Filter (15 pts), Non-Markovian Memory (15 pts), and Kelly Criterion (10 pts, modifier). A separate Veto/Penalty layer includes Monte Carlo, Black Swan, Sentiment, and Quantum Momentum, which only apply penalties and no additive scoring.

### TRACK_RECORD_MODE
A temporary `TRACK_RECORD_MODE` is implemented to build historical data under controlled risk, active during low-volatility markets. It caps score and size, enables `WEAK_TREND` scoring, and uses reduced thresholds. It auto-deactivates when `total_trades >= 100` AND `win_rate >= 45%`, ensuring guardrails like RMS, MC Veto, and Coherence remain active.

### Error Handling
An `ai_error_handler.py` provides an `ErrorClassifier` with 8 categories, SDK-specific error detection, intelligent retry/failover with exponential backoff, and structured logging.

### Web Search Service
Includes an `IntentDetector`, `SearchManager`, and `TavilySearch` client for intent-based web searches.

## External Dependencies

### APIs and Services (15 integrations)
-   **Kraken Exchange**: Crypto data and order execution. [OPERATIONAL]
-   **Alpaca**: Stock data and historical bars. [DISABLED - no secrets]
-   **Google Gemini (2.0 Flash)**: Primary AI model. [OPERATIONAL]
-   **OpenAI (GPT-4o, Whisper)**: AI services. [OPERATIONAL]
-   **Anthropic Claude**: AI fallback. [DISABLED - no secrets]
-   **ElevenLabs**: Text-to-speech, voice generation. [OPERATIONAL]
-   **CoinGecko**: Backup crypto prices. [OPERATIONAL]
-   **Alternative.me**: Fear and Greed Index. [OPERATIONAL]
-   **Finnhub**: Market news and sentiment. [OPERATIONAL]
-   **Alpha Vantage**: Technical indicators. [OPERATIONAL]
-   **Tavily**: Real-time web search for AI responses. [OPERATIONAL]
-   **Stripe**: Payment processing. [UNCONFIGURED - placeholder Price IDs]
-   **ANU QRNG**: Quantum random numbers. [OPERATIONAL]

### Databases
-   **PostgreSQL (Railway)**: Main persistence for trading data, analysis, conversations, balance history, derivatives, community intelligence, risk management, adaptive engine data, and user settings.
-   **Redis (Railway)**: Caching, state management, and rate limiting.

## Recent Changes (Dec 27, 2025)

### DualKalmanTrendFilter Fix
- **Problem**: `'DualKalmanTrendFilter' object has no attribute 'filter_and_predict'` error in production logs
- **Root Cause**: `auto_trading_bot.py` line 2185 calls `.filter_and_predict(prices)` but class only had `update()` and `filter_series()`
- **Solution**: Added `filter_and_predict()` method to `DualKalmanTrendFilter` in `omnix_services/trading_service/kalman_filter.py`
- **Files Modified**: `omnix_services/trading_service/kalman_filter.py` (lines 273-347)
- **Status**: FIXED - method returns filtered_price, predicted_price, trend, trend_strength, crossover, confidence, fast, slow

### BlackSwanDetector Fix
- **Problem**: `'BlackSwanDetector' object has no attribute 'analyze'` error in production logs
- **Root Cause**: `auto_trading_bot.py` calls `.analyze()` but local class only had `detect_extreme_events()`
- **Solution**: Added canonical `analyze()` method to `BlackSwanDetector` in `omnix_services/trading_service/advanced_features.py`
- **Files Modified**: `omnix_services/trading_service/advanced_features.py` (lines 254-402)
- **Status**: FIXED - method now returns full canonical payload (detected, severity, indicators, statistics, risk_metrics, recommendations)

### Comprehensive Type Safety Fix (Dec 27-28, 2025)
- **Problem**: `'>=' not supported between str and int` errors causing score=0 and blocking valid trades
- **Root Cause**: Config values and external signal metrics sometimes arrive as strings instead of floats
- **Solution**: Added `safe_float()` helper function with logging, applied across 20+ decision flow paths:
  - Config initialization (min_trade_usd, max_position_pct, stop_loss_pct, etc.)
  - Rollback guardrails (daily_loss_limit, min_win_rate, trades_window)
  - Monte Carlo metrics and mc_veto_config thresholds
  - Black Swan crash_prob, Sentiment scores, Quantum signal
  - Kalman trend_strength, HMM regime_confidence
  - Coherence Gate pre-score thresholds
  - Kelly scoring and sizing
  - Non-Markovian confidence (with param_name for diagnostics)
  - Ramp-up trades/factors, HMM position_multiplier, CAES max_position_pct
- **Files Modified**: `omnix_core/bot/auto_trading_bot.py` (safe_float function + 20+ application sites)
- **Status**: FIXED - All external numeric signals now normalized before comparison/arithmetic

### Conversational Brain Type Safety Fix (Dec 28, 2025)
- **Problem**: `bad operand type for abs(): 'str'` error in trade reasoning generation
- **Root Cause**: Signal values (quantum momentum, kalman, monte carlo, kelly) arrive as strings
- **Solution**: Added `safe_float()` function to `omnix_services/ai_service/conversational_brain.py`
- **Files Modified**: `omnix_services/ai_service/conversational_brain.py` (safe_float + 11 application sites)
- **Coverage**: generate_trade_reasoning(), _generate_decision_graph(), generate_post_trade_evaluation()
- **Status**: FIXED - All signal values normalized before abs() and comparisons

### Coherence Engine Type Safety Fix (Dec 28, 2025)
- **Problem**: `'>=' not supported between instances of 'str' and 'int'` error in Coherence Engine V5.4
- **Root Cause**: win_rate and confidence values arrive as strings from external data
- **Solution**: Added `safe_float()` function to `omnix_services/coherence_service/coherence_engine.py`
- **Files Modified**: `omnix_services/coherence_service/coherence_engine.py` (safe_float + 2 application sites)
- **Coverage**: monte_carlo win_rate, validate_trade_coherence confidence
- **Status**: FIXED - All external numeric inputs normalized before comparison

### User Settings Schema Fix (Dec 28, 2025)
- **Problem**: `column "total_trades" of relation "user_settings" does not exist`
- **Root Cause**: Missing columns in database schema
- **Solution**: ALTER TABLE to add missing columns
- **Columns Added**: `total_trades INTEGER DEFAULT 0`, `winning_trades INTEGER DEFAULT 0`
- **Status**: FIXED - Applied to development database
- **Railway Action Required**: `ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS total_trades INTEGER DEFAULT 0; ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS winning_trades INTEGER DEFAULT 0;`

### Comprehensive Codebase Audit (Dec 29, 2025)
- **Scope**: 10-phase audit covering 448+ files (378 Python + 70 Markdown)
- **Code Audit**: omnix_core/ (29), omnix_services/ (189), src/omnix/ (99), omnix_dashboard/omnix_api/tests (61)
- **Doc Audit**: All 70 docs across 7 directories verified for cross-references
- **Key Findings**:
  - ARES V1/V2: Confirmed REMOVED Dec 24, 2025 (updated TRACEABILITY_MATRIX.md)
  - V7 Architecture: 20 Protocol ports, 22 adapters, 156 tests passing
  - Integrations: 15 external APIs (12 operational, 2 disabled, 1 unconfigured)
  - Stripe: Placeholder Price IDs need configuration before monetization
- **Audit Reports**: See `docs/compliance/audits/` (10 reports with descriptive names)
- **Status**: COMPLETE

## Current System State (Dec 29, 2025)

### Track Record
| Metric | Current | Target |
|--------|---------|--------|
| Trades | 109 | 500+ |
| Win Rate | 22% | 55%+ |
| P&L | -$14,942.94 | Positive |

### Architecture Metrics
| Component | Count |
|-----------|-------|
| Protocol Ports | 20 |
| Adapters | 22 |
| Tests Passing | 156 |
| External Integrations | 15 |

### Critical Blockers for Production
1. **Railway DB Migration**: user_settings columns (see above SQL)
2. **Stripe Configuration**: Replace placeholder Price IDs, add webhook verification

## Test Environment Configuration (Dec 29, 2025)

### Problem Solved
Tests were failing because `TELEGRAM_BOT_TOKEN` was intentionally removed from Replit Secrets to prevent dual-execution conflicts (Railway + Replit simultaneously = Telegram connection errors).

### Solution Implemented
1. **env_manager.py**: Modified `get_required()` and `_validate_value()` to detect test mode via `TESTING=true` or `PYTEST_CURRENT_TEST` environment variable, bypassing strict token validation
2. **tests/conftest.py**: Sets `TESTING=true` and mock token BEFORE any imports
3. **Workflow Command**: `TESTING=true TELEGRAM_BOT_TOKEN=test-token python -m pytest ...`
4. **pyproject.toml**: Added pytest-env configuration with mock token

### Files Modified
- `omnix_config/env_manager.py` (test mode detection in validation)
- `tests/conftest.py` (early environment setup)
- `pyproject.toml` (pytest-env configuration)

### How to Run Tests
```bash
cd /home/runner/workspace && TESTING=true TELEGRAM_BOT_TOKEN=test-token python -m pytest tests/ -v
```

### Current Test Status
- **10/10 tests passing** (Code Verification workflow)
- V7 hexagonal architecture: 156 tests passing