# OMNIX V6.5.4e INSTITUTIONAL+

## Overview
OMNIX V6.5.4e INSTITUTIONAL+ is an institutional-grade risk control infrastructure for cryptocurrency trading. Its primary purpose is capital preservation through a multi-layer veto architecture, incorporating post-quantum cryptography, real-time market analysis, Non-Markovian Temporal Memory, a 6-tier Coherence Engine, Monte Carlo validation, Black Swan detection, and Kelly Criterion sizing. The system prioritizes capital preservation (98.5% maintained) over trade volume and has successfully blocked numerous high-risk operations. The current focus is on extended validation to build a credible track record for institutional investor presentations. V6.5.4e includes ADR-007 Phase 1 calibration for improved trade throughput while maintaining capital protection.

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
The system integrates an AutoTradingBot, Non-Markovian Memory Kernel, 6-Tier Veto System (Coherence Engine), AI Risk Guardian, Portfolio Management, Confidence-Adaptive Entry System (CAES), On-Chain Data Intelligence, and an Execution Protocol. It supports multi-user roles, features Flask and Streamlit dashboards, an Asset Quarantine System, Real-Time Latency Monitor, Price Stale Detection, and Admin Alerts. The UI is designed for an "Investor-Ready" presentation. The Decision Engine uses an EMA Regime Signal as the primary driver, a Monte Carlo VETO Engine, and robust RMS Enforcement. All decisions are fully auditable via a `decision_trace`. Defensive hardening includes Position Size Factor Clamping and Veto Sentinel Logs. The system is designed with a hexagonal architecture (V7.0) with planned activation via the Strangler Fig pattern.

### AI Architecture and Enforcement
The AI service adheres to SOLID principles and dependency injection, supporting multiple AI providers. It features AI-first command detection, a Multilingual Prompt Architecture with dynamic language detection, and a Chain-of-Thought Framework. An AI Self-Knowledge System, driven by `system_state_manifest.json`, prevents AI "hallucinations." OMNIX Identity Prompt and Investor Response Rules enhance AI behavior and communication. The Performance Honesty Guard provides honest metrics and contextual truth for investor communications.

### Hierarchical Veto Flow
The execution order is: 1. MC VETO → 2. RMS VETO → 3. **ADAPTIVE COHERENCE GATE** → 4. Scoring → 5. Decision. The Adaptive Coherence Gate blocks low-quality signals BEFORE scoring computation with dynamic thresholds based on EMA score + Black Swan severity.

### Scoring Logic
Scoring is based on 5 core inputs: EMA Regime Signal (40 pts, PRIMARY DRIVER), HMM Regime (25 pts), Kalman Filter (15 pts), Non-Markovian Memory (15 pts), and Kelly Criterion (10 pts, modifier). A separate Veto/Penalty layer includes Monte Carlo, Black Swan, Sentiment, and Quantum Momentum, applying only penalties.

### TRACK_RECORD_MODE
`TRACK_RECORD_MODE` and `LOW_VOL_MODE` are controlled by environment variables. When active, `TRACK_RECORD_MODE` caps score, reduces sizing, enables `WEAK_TREND` scoring, and maintains all guardrails. It auto-deactivates under specific conditions (`total_trades >= 100` AND `win_rate >= 45%`).

### Error Handling
An `ai_error_handler.py` provides an `ErrorClassifier` with 8 categories, SDK-specific error detection, intelligent retry/failover with exponential backoff, and structured logging.

### Web Search Service
Includes an `IntentDetector`, `SearchManager`, and `TavilySearch` client for intent-based web searches.

### Type Safety
Defensive type normalization prevents `str` vs `int` comparison errors, particularly within the Coherence Engine and `AutoTradingBot._build_strategy_signals()`, using `normalize_signal()`, `normalize_strategy_signal()`, and `safe_float()`.

### Telegram Interaction
Improvements include increased timeouts for HTTPXRequest and all `requests.post()` calls (30s), retry mechanisms with exponential backoff, immediate ACK for user messages, and sending AI responses as new messages to prevent timeout issues. Voice responses are optimized for latency, sending text immediately and generating voice asynchronously.

### Operación Lucidez - Segmented Expectancy
This system analyzes segmented expectancy by categorizing trades based on `HMM_REGIME` and `COHERENCE_BUCKET` to calculate profitability per market condition. It leverages data from `paper_trading_trades` and provides an API endpoint and a Streamlit dashboard widget for visualization.

### Modo Sniper - Precision Entry System
This system focuses on precision trade entries with ATR-Based Sizing (stop loss at `ATR × 2.5`, position sized to risk max 0.5% of balance), Volume Veto (blocks trades if 5-minute volume < 1-hour average), and Strategy Mode Tracking (tags trades as 'SNIPER' or 'STANDARD').

### Veto Tracking System
This system provides real-time capital protection tracking with PostgreSQL persistence for accurate investor reporting. It logs veto events from COHERENCE_GATE, MC, BLACK_SWAN, and RMS, with deduplication.

### Shadow Portfolio + Learning Engine
A counterfactual analysis system that tracks vetoed trades with full context to learn which filters need calibration. It analyzes price movement, calculates "would-have-won" scenarios, determines veto correctness, and provides filter threshold recommendations.

### Dashboard Features
The dashboard displays a Dual Win Rate Framework (directional precision vs. profitable net), enriched AI context with granular breakdowns (symbol, regime, coherence, fee impact, timing patterns), and critical UX improvements such as a System Health Score (0-100), Live Status widget, Quick Insights (auto-generated actionable insights), Calibration Progress (4-phase tracker), and Recommended Actions (priority-based suggestions). All 5 P1 features completed as of Jan 13, 2026.

## Recent Changes

### Jan 14, 2026: ADR-008 Opportunity Tracker (FEAT-011 Enhanced)
- **FRAMEWORK**: Day 30 review sin cambiar thresholds ahora
- **MÉTRICAS**: Missed Opportunities vs Losses Avoided vs Net Opportunity
- **CRITERIO**: Si missed > 20 AND profit > $3K → Test threshold 35% con $500
- **FECHA REVISIÓN**: 13 de Febrero 2026
- **REFERENCIA**: `docs/reference/adr/ADR-008-opportunity-tracker.md`
- **WIDGET DASHBOARD**: Balance visual 💎 Missed vs ✅ Avoided con ⚖️ - Day 1/30 tracking
- **API**: `/api/learning/insights` → `opportunity_tracker` payload con missed/avoided/net/recommendation
- **DATABASE**: Usa `black_swan_prob` (numeric 0-1), NO `black_swan_severity`
- **ESTADO ACTUAL**: 0 missed, 479 avoided, NET -$239.5K = PROTECTING ✅

### Jan 14, 2026: ADR-007 Coherence Threshold Calibration (V6.5.4e)
- **DIAGNOSIS**: System over-protective, blocking 48,937 trades in 7 days ($978.7M blocked)
- **ROOT CAUSE**: COHERENCE_GATE avg 26.3% coherence, BLACK_SWAN blocking 21,402 signals
- **SOLUTION Phase 1**: 5-point threshold reduction across all levels
  - Adaptive thresholds: LOW 30% (was 35%), MEDIUM 40% (was 45%), HIGH 50% (was 55%), EXTREME 60% (was 65%)
  - EMA trigger: 20 (was 25)
- **Files Modified**: `coherence_engine.py`, `memory_risk_adapter.py`
- **Expected Impact**: Veto rate -15-20%, Win rate 37.8% → 42-45%, Profit factor 0.13 → 0.8-1.2
- **Guardrails**: Rollback if drawdown > 3% in 48h
- **Reference**: `docs/reference/adr/ADR-007-coherence-threshold-calibration.md`

### Jan 14, 2026: FEAT-006, FEAT-007, FEAT-008, FEAT-009, FEAT-010, FEAT-011 Dashboard Widgets
- **FEAT-006 Comparative Metrics**: API `/api/metrics/comparative` with period-aligned BTC benchmarking
- **FEAT-007 P&L Breakdown**: API `/api/metrics/pnl-breakdown` with symbol/cause analysis
  - By Symbol: horizontal bars showing P&L per asset
  - Trade Outcomes: Pure Wins (20.2%), Fee Eroded (17.6%), Pure Losses (62.2%)
  - Directional Accuracy: 37.8% (matches header Precisión metric)
- **FEAT-008 Correlation Heatmap**: API `/api/metrics/correlation` with hourly P&L correlation
  - Per-symbol performance metrics (trades, win rate, P&L, volatility)
  - Correlation matrix using hourly buckets for statistical validity
  - Diversification score (0-100) based on average correlation
- **FEAT-009 Time Heatmap**: API `/api/metrics/time-heatmap` with P&L by hour/day
  - 7x24 heatmap grid showing optimal trading times
  - Best/worst time identification with P&L
- **FEAT-010 Regime Detection Dashboard**: API `/api/regime/dashboard` with regime analysis
  - Current Regime: BULLISH/BEARISH/RANGING inferred from EMA signals
  - Confidence & Coherence metrics
  - Veto activity summary (24h) with capital protected
  - Signal distribution visualization
  - System status message explaining behavior (DEFENSIVE/ANALYZING/PROTECTIVE/MONITORING)
  - Data source: 48K+ shadow_trade_events since Jan 9
- **FEAT-011 Learning Engine Insights**: API `/api/learning/insights` with Shadow Portfolio analysis
  - Veto effectiveness by type (BLACK_SWAN, COHERENCE_GATE, MC, RMS)
  - Threshold analysis with avg EMA/coherence scores
  - Top vetoed symbols
  - Calibration recommendations
- Reference: `docs/DASHBOARD_IMPROVEMENT_BACKLOG.md`
- **Dashboard now has 23/23 widgets operational** (P0: 3/3, P1: 5/5, P2: 6/6)

### Jan 13, 2026: ADR-003 Identity Alignment
- **SYSTEM IDENTITY** in `ai_prompts.py` updated to "risk control infrastructure" (was "algorithmic trading system")
- **BLACKLISTED PHRASES** added: "generar rendimientos", "rendimientos consistentes", "sistema de trading", "bot de trading"
- **MASTER_SYSTEM_PROMPT** ROLE changed from "trading advisor" to "risk management advisor"
- **Template response** for "¿Qué es OMNIX?" added in Spanish/English following Mode 1 Positioning
- Reference: `docs/reference/adr/ADR-003-official-positioning.md`, `docs/reference/omnix_official_language.md`

## External Dependencies

### APIs and Services
-   **Kraken Exchange**: Crypto data and order execution.
-   **Alpaca**: Stock data and historical bars.
-   **Google Gemini (2.0 Flash)**: Primary AI model.
-   **OpenAI (GPT-4o, Whisper)**: AI services.
-   **Anthropic Claude**: AI fallback.
-   **ElevenLabs**: Text-to-speech, voice generation.
-   **CoinGecko**: Backup crypto prices.
-   **Alternative.me**: Fear and Greed Index.
-   **Finnhub**: Market news and sentiment.
-   **Alpha Vantage**: Technical indicators.
-   **Tavily**: Real-time web search for AI responses.
-   **Stripe**: Payment processing.
-   **ANU QRNG**: Quantum random numbers.

### Databases
-   **PostgreSQL (Railway)**: Main persistence for trading data, analysis, conversations, balance history, derivatives, community intelligence, risk management, adaptive engine data, and user settings.
-   **Redis (Railway)**: Caching, state management, and rate limiting.