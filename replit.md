# OMNIX V6.5.4e INSTITUTIONAL+

## Overview
OMNIX V6.5.4e INSTITUTIONAL+ is an institutional-grade risk control infrastructure for cryptocurrency trading focused on capital preservation (98.5% maintained). It employs a multi-layer veto architecture, incorporating post-quantum cryptography, real-time market analysis, Non-Markovian Temporal Memory, a 6-tier Coherence Engine, Monte Carlo validation, Black Swan detection, and Kelly Criterion sizing. The system prioritizes capital preservation over trade volume and aims to build a credible track record for institutional investor presentations. V6.5.4e includes ADR-007 Phase 1 calibration for improved trade throughput while maintaining capital protection.

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
The AI service adheres to SOLID principles and dependency injection, supporting multiple AI providers. It features AI-first command detection, a Multilingual Prompt Architecture with dynamic language detection, and a Chain-of-Thought Framework. An AI Self-Knowledge System, driven by `system_state_manifest.json`, prevents AI "hallucinations." OMNIX Identity Prompt and Investor Response Rules enhance AI behavior and communication. The Performance Honesty Guard provides honest metrics and contextual truth for investor communications. AI responses are subject to adaptive detail based on user requests. For due diligence, investor queries trigger comprehensive responses without brevity limits.

### Anti-Servile Post-Processing Filter (Jan 19, 2026)
A safety-net filter in `conversational_ai_adapter.py` removes servile/prohibited phrases AFTER AI generation. Filtered patterns include: "Agradezco la perspicacia", "me comprometo a ofrecer", numbered section headers (*1. Análisis Inmediato*, etc.). The filter removes complete servile sentences while preserving valuable content. See ADR-009 for full documentation.

### Async Market Data Fetching (Jan 19, 2026)
`_fetch_real_market_data_async()` runs 7 data sources in parallel via `asyncio.gather()`: Kraken auth, Kraken public, CoinGecko, specific crypto, trade performance, veto data, investor data. Reduces latency from ~20s (sequential) to ~3-5s (parallel). HTTP timeouts reduced from 10s to 5s for faster failure recovery.

### Hierarchical Veto Flow
The execution order is: 1. MC VETO → 2. RMS VETO → 3. **ADAPTIVE COHERENCE GATE** → 4. **ECW GATE** → 5. Scoring → 6. Decision. The Adaptive Coherence Gate blocks low-quality signals BEFORE scoring computation with dynamic thresholds based on EMA score + Black Swan severity. Calibration for Coherence Thresholds (ADR-007 Phase 1) involves threshold reduction and EMA trigger adjustment to improve trade throughput.

### Edge Confirmation Window (ECW) - ADR-019 (Jan 21, 2026)
Gate that requires edge persistence before allowing trades. Transforms "capital preservation" into "capital patience".

**Thresholds:** MC_WR ≥ 52%, MC_ER > 0%, Black Swan ≤ MEDIUM, for 3 consecutive cycles.

**Behavior:**
- Conditions met → Counter increments in Redis
- Any condition fails → Counter resets to 0
- Counter ≥ 3 → Trade window OPEN

**ECW_PROGRESS Tracking (decision_trace):**
- `ecw_progress_current`: Current cycle count (0, 1, 2, 3)
- `ecw_progress_required`: Always 3
- `ecw_progress_previous`: Previous cycle count before this evaluation

**ECW_RESET_REASON Enum:**
| Reason | Trigger |
|--------|---------|
| `BLACK_SWAN_HIGH` | Black Swan severity EXTREME or HIGH |
| `BLACK_SWAN_ELEVATED` | Black Swan severity ELEVATED |
| `MC_EDGE_DEGRADED` | Win Rate dropped below 52% |
| `MC_ER_NEGATIVE` | Expected Return became negative |
| `SIGNAL_FLIP` | EMA signal changed from BUY to SELL/HOLD |
| `CONDITIONS_FAILED` | Multiple conditions failed simultaneously |

**Signal Normalization (for SIGNAL_FLIP detection):**
- LONG/BUY/BULLISH/STRONG_BUY/UPTREND → BUY
- SHORT/SELL/BEARISH/STRONG_SELL/DOWNTREND → SELL
- All others → HOLD

**Logging:** `⏳ [ECW_GATE] BTC/USD | 2/3 cycles → Waiting` or `✅ [ECW_GATE] BTC/USD | 3/3 cycles → OPEN`

**Files:** `omnix_core/bot/auto_trading_bot.py`, `docs/reference/adr/ADR-019-edge-confirmation-window.md`

### Scoring Logic
Scoring is based on 5 core inputs: EMA Regime Signal (40 pts, PRIMARY DRIVER), HMM Regime (25 pts), Kalman Filter (15 pts), Non-Markovian Memory (15 pts), and Kelly Criterion (10 pts, modifier). A separate Veto/Penalty layer includes Monte Carlo, Black Swan, Sentiment, and Quantum Momentum, applying only penalties.

### TRACK_RECORD_MODE
When active, `TRACK_RECORD_MODE` caps score, reduces sizing, enables `WEAK_TREND` scoring, and maintains all guardrails. It auto-deactivates under specific conditions (`total_trades >= 100` AND `win_rate >= 45%`).

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
A counterfactual analysis system that tracks vetoed trades with full context to learn which filters need calibration. It analyzes price movement, calculates "would-have-won" scenarios, determines veto correctness, and provides filter threshold recommendations. An Opportunity Tracker (ADR-008) analyzes Missed Opportunities vs Losses Avoided vs Net Opportunity, with a dashboard widget for visual balance.

### Decision Contradiction Index (DCI) - ADR-018 (Jan 21, 2026)
Shadow observational metric measuring internal signal divergence to explain HOLDs. **CRITICAL RULE: DCI ALTO = NO OPERAR.** A high DCI indicates high internal contradiction between signals. NEVER use high DCI as entry condition.

**Components (0-100 total):**
- Local Signal Strength (0-40): avg(NM%, EMA%) × 0.4
- Global Edge Penalty (0-30): Inverse of MC_ER/WR
- Regime Penalty (0-15): VOLATILE=15, RANGING=10, BEARISH=5
- Risk Overlay (0-15): Black Swan severity

**Levels:** ALIGNED (<35) = can trade | TENSIONED (35-69) = caution | CONTRADICTORY (≥70) = HOLD mandatory

**Realistic Thresholds for Execution:** MC WR > 50%, MC ER > 0%, Coherence > 50%, DCI < 70. NEVER claim "WR > 60%" or "ER > 5%" (fantasy).

**Loss Avoidance Formula:** `Position_Size × max(VaR95, Historical_Avg_Loss)`. NEVER say "difficult to quantify".

**Files:** `omnix_core/bot/auto_trading_bot.py`, `omnix_config/system_state_manifest.json`

### Dashboard Features
The dashboard displays a Dual Win Rate Framework, enriched AI context with granular breakdowns, a System Health Score (0-100), Live Status widget, Quick Insights, Calibration Progress (4-phase tracker), and Recommended Actions. Key dashboard credibility improvements include clarifying "Est. Loss Avoided" vs "Notional Blocked", distinguishing "Market Trend" from "Trading Regime", and providing a timeline for Calibration Progress. Additional widgets include Comparative Metrics, P&L Breakdown, Correlation Heatmap, Time Heatmap, Regime Detection Dashboard, and Learning Engine Insights. The `InvestorDataProvider` facilitates read-only SQL queries for segmented metrics, fee breakdowns, and trade analysis to investors, triggered by specific keywords or complex questions. Capital protection metrics are standardized to "Est. Loss Avoided*" (Notional × 0.6%) as primary and "Notional Blocked" as secondary.

### Analytical VIEW: v_shadow_trade_metrics (ADR-021, Jan 22, 2026)
PostgreSQL VIEW for parsing `decision_trace` JSONB from `shadow_trade_events` table. Enables retroactive DCI analysis and investor demos.

**Extracted Metrics:** `mc_win_rate`, `mc_expected_return`, `coherence_score`, `ecw_cycles`, `ecw_status`, `black_swan_severity`, `approx_dci`

**Design:** VIEW (not physical table) - zero risk, 100% reversible with `DROP VIEW`. Regex are intentionally permissive for forward compatibility.

**Usage:**
```sql
-- Capital protected by ECW
SELECT SUM(blocked_capital) FROM v_shadow_trade_metrics WHERE ecw_status = 'WAITING';
-- DCI distribution
SELECT CASE WHEN approx_dci >= 70 THEN 'CONTRADICTORY' ELSE 'ALIGNED' END, COUNT(*) FROM v_shadow_trade_metrics GROUP BY 1;
```

**Reference:** `docs/reference/adr/ADR-021-shadow-trade-metrics-view.md`

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