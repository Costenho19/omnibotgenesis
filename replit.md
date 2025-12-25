# OMNIX V6.5.4d INSTITUTIONAL+

## Overview
OMNIX V6.5.4d INSTITUTIONAL+ is an enterprise-grade automated cryptocurrency and stock trading system designed for paper trading to build a credible track record for investor presentations, aiming for $1M seed funding at an $11.5M pre-money valuation. Its core capabilities include AI integration, post-quantum cryptography, real-time market analysis, Non-Markovian Temporal Memory, adaptive parameter calibration, institutional portfolio optimization, derivatives trading, and dual-market support for Kraken (crypto) and Alpaca (stocks). The system targets 3-5 trades/day with a 55%+ win rate, multi-crypto scanning, and tiered signal strengths, focusing on an "Investor-Ready" presentation.

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
The system integrates several core engines: AutoTradingBot, Non-Markovian Memory Kernel, Coherence Engine (6-Tier Veto System), AI Risk Guardian, Portfolio Management, CAES (Confidence-Adaptive Entry System), On-Chain Data Intelligence, Execution Protocol, InstitutionalDecisionLogger, and InstitutionalMetricsCalculator. It supports multi-user modes with granular role-based permissions (FREE, BASIC, PRO, PREMIUM, OWNER) and features Flask and Streamlit dashboards for API access, web terminal, and interactive visualization. Key features include an Asset Quarantine System, Real-Time Latency Monitor, Price Stale Detection System, and Admin Alerts. The UI is designed for an "Investor-Ready" presentation, and Investor-Grade Automated Responses use institutional language. The Decision Engine incorporates an EMA Regime Signal as the primary driver, a Monte Carlo VETO Engine for risk enforcement, and robust RMS Enforcement. All decisions are fully auditable via a `decision_trace`. Defensive hardening includes Position Size Factor Clamping and Veto Sentinel Logs.

### AI Architecture and Enforcement
The AI service is refactored with SOLID principles and dependency injection, supporting multiple AI providers. It features an AI-first command detection and a Multilingual Prompt Architecture with dynamic language detection and a Chain-of-Thought Framework. A critical AI Institutional Language Enforcement system ensures responses use approved institutional phrasing, blocking blacklisted terms and enforcing a "founder controlling risk" narrative. An AI Self-Knowledge System, driven by `system_state_manifest.json`, prevents AI "hallucinations" about system status. EMA Regime Signal is the sole primary driver (40 points).

### Hierarchical Veto Flow (Dec 24, 2025)
Implemented Coherence Pre-Gate BEFORE scoring. New execution order:
1. MC VETO → 2. RMS VETO → 3. **COHERENCE GATE** → 4. Scoring → 5. Decision
- Coherence now blocks low-quality signals BEFORE scoring computation
- Thresholds: veto_critical < **35%**, veto_normal < **50%**
- New trace states: `COHERENCE_GATE_CRITICAL`, `COHERENCE_GATE_LOW`
- **Result**: Reduces false positives and overtrading

### ARES Deprecation (Dec 24, 2025)
**ARES V1/V2 strategies have been completely removed** from the active codebase:
- Archived to `archive/deprecated_ares/` (strategies, testing, stock modules, docs)
- All runtime references eliminated from omnix_core/, omnix_services/, src/omnix/
- Kill-switch code removed from auto_trading_bot.py (~100 lines)
- Adaptive engine now uses QUANTUM_MOMENTUM/HMM_REGIME baselines
- User settings updated to show V6.5.4d strategies

### Scoring Simplification (Dec 24, 2025)
5 core inputs per GPT Expert recommendation:
- **EMA Regime Signal**: 40 pts (PRIMARY DRIVER)
- **HMM Regime**: 25 pts (up from 15)
- **Kalman Filter**: 15 pts
- **Non-Markovian Memory**: 15 pts (up from 12)
- **Kelly Criterion**: 10 pts (modifier)

Veto/Penalty layer (NO additive scoring):
- Monte Carlo, Black Swan, Sentiment, Quantum Momentum → penalty only
- Full documentation: `docs/current/DECISION_CONTRACT.md`

### Bug Fixes (Dec 25, 2025)

#### EC-A1: Auto-Start Authorization Fix
**Problem**: Unauthorized user 6429738143 was incorrectly passing permission checks during auto-start.
**Root Cause**: Permission check was using wrong operation name `'persistent_auto_start_fallback'` (resolves to `READ_MARKET_DATA`) instead of `'auto_trading'` (resolves to `PAPER_AUTO_TRADING`).
**Fix**: 
- Added fallback permission check in `_auto_start_if_persistent()` with correct `'auto_trading'` operation
- Added `_find_authorized_auto_trading_user()` method to search for authorized users in DB
- Persisted fallback user_id before calling `start()`
**Files**: `omnix_core/bot/auto_trading_bot.py` (lines 805-888)

#### Multi-User Trading Loop Fix
**Problem**: Error "unhashable type: 'dict'" occurring every 30 seconds in trading loop.
**Root Cause**: `get_active_sessions()` returns `List[Dict]` but code was iterating directly and using dicts as dictionary keys.
**Fix**: Added type checking to extract `user_id` string from dict entries before using as keys.
**Files**: `omnix_core/bot/auto_trading_bot.py` (lines 1127-1134)

### Monte Carlo Threshold Relaxation (Dec 25, 2025)
**Problem**: Bot was too conservative - Monte Carlo veto blocking all trades with expected return < 0%, resulting in no trades for 13+ days.
**Change**: Relaxed `min_expected_return` threshold from **0.0** to **-0.001** (-0.1%).
**Effect**: Trades with expected return between -0.1% and 0% are now allowed, enabling the system to build a track record for investor presentations.
**Files**: `omnix_core/bot/auto_trading_bot.py` (lines 792-803, 2350-2358)

### EMA Signal Seasonal Adjustment (Dec 25, 2025)
**Problem**: EMA Regime Signal was generating NONE direction for all assets due to low market volatility during Christmas holidays.
**Root Cause**: Hardcoded `trend_strength > 0.3` and `min_confidence >= 0.50` thresholds too strict for low-liquidity regimes.
**Changes**:
- `min_trend_strength`: 0.30 → 0.15
- `min_confidence`: 0.50 → 0.35
**Risk Control**: Monte Carlo VETO and Coherence Gate remain active as downstream safeguards.
**Note**: This is a Seasonal Parameter Adjustment - review after market normalizes.
**Files**: `omnix_core/strategies/ema_regime_signal.py` (lines 66-85, 247-262)

### Correction Plan Implementation (Dec 25, 2025 - Evening)
Implemented 5-phase correction plan to transition from ALPHA conceptual to ALPHA operativa:

#### FASE 1: LOW_VOL_MODE
- Added `LOW_VOL_MODE = True` flag for Christmas-January low-liquidity markets
- `min_confidence`: 0.35 → 0.30 when LOW_VOL_MODE active
- TODO marker added: revert when ATR(14) normalizes or post-January
- **Files**: `omnix_core/strategies/ema_regime_signal.py` (lines 69-92)

#### FASE 2: Kelly Conditional
- Kelly Criterion now CONDITIONAL on Monte Carlo win_rate
- Rule: `if mc_win_rate >= 0.52: use kelly_size else: base_size * 0.5`
- Added `mc_win_rate` parameter to `_calculate_position_size_v52()`
- Logs show "KELLY CONDITIONAL: MC win_rate=X% >= 52% → Kelly ACTIVE"
- **Files**: `omnix_core/bot/auto_trading_bot.py` (lines 4187-4312)

#### FASE 3: Module Status Registry
- Created `ModuleStatus` enum with 6 states:
  - CORE_ACTIVE (EMA, MC Veto, RMS, Coherence, HMM, Kalman, Non-Markovian)
  - CONDITIONAL_ACTIVE (Kelly Criterion)
  - OBSERVATIONAL_ONLY (Black Swan, Sentiment)
  - EXPERIMENTAL_ONLY (Quantum QRNG, QAOA, Post-Quantum Crypto)
  - LIVE_MODE_ONLY (TWAP, VWAP, ICEBERG)
  - FROZEN_UNTIL_EDGE (CAES)
- Added `MODULE_STATUS_REGISTRY` dict for transparency
- **Files**: `omnix_core/config/trading_profiles.py` (lines 61-114)

#### FASE 4: Track Record (Active)
- 50-100 trades target with allowed pairs (BTC/USD, XRP/USD)
- Minimum 10 days before parameter evaluation
- Win rate target: ≥ 45%

#### FASE 5: Narrative Separation
- CORE ENGINE: EMA, MC, RMS, Coherence (decisional)
- EXPERIMENTAL LAB: Quantum, Black Swan (observational)
- ROADMAP: TWAP/VWAP, real trading (future)

### Trading Profiles
The system uses configurable trading profiles (e.g., INSTITUTIONAL, PAPER_AGGRESSIVE, PRODUCTION_STABLE) to adjust parameters, with `PRODUCTION_STABLE V6.5.4d` being the active profile.

### Hexagonal Architecture (V7.0)
The system is structured around a hexagonal architecture with 20 ports and 22 adapters, currently operating with legacy code, with planned activation via the Strangler Fig pattern. The project structure includes `src/omnix/` for the hexagonal V7.0 and `omnix_core/`, `omnix_services/`, etc., for legacy components.

### Error Handling
An `ai_error_handler.py` provides an `ErrorClassifier` with 8 categories, SDK-specific error detection, intelligent retry/failover with exponential backoff, and structured logging.

### Web Search Service
Includes an `IntentDetector`, `SearchManager`, and `TavilySearch` client for intent-based web searches.

## External Dependencies

### APIs and Services
-   **Kraken Exchange**: Crypto data and order execution.
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
-   **PostgreSQL (Railway)**: Main persistence for trading data, analysis, conversations, balance history, derivatives, community intelligence, risk management, adaptive engine data, and user settings.
-   **Redis (Railway)**: Caching, state management, and rate limiting.