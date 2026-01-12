# OMNIX V6.5.4d INSTITUTIONAL+

## Overview
OMNIX V6.5.4d INSTITUTIONAL+ is institutional-grade risk control infrastructure for cryptocurrency trading, designed to prevent capital loss through multi-layer veto architecture. Its core capabilities include post-quantum cryptography (Kyber-768, Dilithium-3), real-time market analysis, Non-Markovian Temporal Memory, Coherence Engine (6-tier veto system), Monte Carlo validation, Black Swan detection, and Kelly Criterion sizing. The system prioritizes capital preservation (98.5% maintained) over trade volume, with 695 high-risk operations automatically blocked. Current phase: extended validation with focus on building a credible track record for institutional investor presentations. Strategic targets (40%+ win rate, 3-5 trades/day) are secondary to preservation and system integrity.

## Official Identity & Positioning (ADR-003)

**Last Updated:** January 10, 2026

### What OMNIX Is

**Official Definition:**
> OMNIX is **institutional-grade risk control infrastructure** for cryptocurrency trading, designed to prevent capital loss through multi-layer veto architecture.

**NOT:**
- "Trading bot" (implies profit focus, we focus on risk)
- "AI trader" (too generic, misses our differentiation)
- "Automated money-maker" (misleading overpromise)

**IS:**
- Risk control infrastructure
- Capital preservation system
- Multi-layer veto architecture
- Institutional-grade decision framework

### Primary KPIs (In Order)

1. **Capital Preservation:** 98.5% of initial capital maintained
2. **Risk Events Blocked:** 695 high-risk operations vetoed
3. **System Integrity:** Zero data inconsistencies, complete audit trail
4. **Win Rate (Dual Metric Framework - Jan 12, 2026):**
   - Directional: 37.82% (system correctly predicted price direction)
   - Net: 20.17% (profitable after Kraken fees)
   - Fee-eroded: 21 trades won in direction but lost to fees
   - Mitigation: $1,000 hard cap implemented
5. **Position Sizing (ADR-004 - Jan 12, 2026):**
   - Kelly max_position: 20% → 2% ($62,500 → $20,000 max)
   - Justification: Trades <$1K = 55% WR, trades >$10K = 31% WR
   - Reference: `docs/reference/adr/ADR-004-position-sizing-hotfix.md`

**Critical:** We lead with preservation and risk control, NOT with win rate.

### Two Response Modes

**MODE 1 - Positioning (Default):**
- For general inquiries and presentations
- Emphasizes architecture, safety, capital preservation
- Example: "OMNIX is risk control infrastructure with 98.5% capital preservation..."

**MODE 2 - Honest Metrics (On Request):**
- When user explicitly asks for performance data
- Shows everything: win rate, P&L, days inactive, etc.
- Always with context: "20.17% win rate (target 40%+, system in protective mode)"

Both modes are **100% truthful**, just different emphasis.

### Approved Language

**Always Use:**
- "institutional-grade risk control infrastructure"
- "multi-layer veto architecture"
- "capital preservation system"
- "X% preserved" / "Y operations blocked"
- "prioritizes preservation over volume"

**Never Use:**
- "AI bot that makes money" (misleading)
- "automated profit generation" (overpromise)
- "beat the market" (unproven claim)
- "guaranteed returns" (illegal in most jurisdictions)

### Reference Documents

- **Full Guide:** `docs/reference/omnix_official_language.md`
- **Decision Record:** `docs/reference/adr/ADR-003-official-positioning.md`
- **Honest Framing:** `docs/reference/adr/ADR-002-honest-framing-over-censorship.md`
- **Position Sizing:** `docs/reference/adr/ADR-004-position-sizing-hotfix.md`

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
The AI service is refactored with SOLID principles and dependency injection, supporting multiple AI providers. It features an AI-first command detection, a Multilingual Prompt Architecture with dynamic language detection, and a Chain-of-Thought Framework. An AI Self-Knowledge System, driven by `system_state_manifest.json`, prevents AI "hallucinations" about system status. OMNIX Identity Prompt and Investor Response Rules enhance AI behavior and communication. The Performance Honesty Guard provides honest metrics only when queried, adapting its responses based on the system's current phase (learning vs. optimizing).

### Honest Framing Policy (Jan 10, 2026)
**CRITICAL ETHICAL DECISION**: The system uses "Honest Framing" instead of data censorship for investor communications.

| Principle | Implementation |
|-----------|----------------|
| **Transparency** | NEVER hide negative metrics (WR, P&L) from potential investors |
| **On-Request Only** | Detailed metrics shown ONLY when user specifically asks |
| **Truthful Context** | Add positive context that is TRUE (e.g., "98.5% capital preserved") |
| **No Euphemisms** | Don't use misleading terms ("capital deployment" to hide losses) |

**Reference**: ADR-002-honest-framing-over-censorship.md

**Example Honest Framing**:
- "Win Rate: 20.17% (objetivo: 40%+)" - Shows real data with context
- "P&L: -$15,198 (98.5% capital preservado)" - Negative shown with positive truth
- "695 operaciones de alto riesgo bloqueadas" - Protection system IS the story

### Hierarchical Veto Flow
The execution order is: 1. MC VETO → 2. RMS VETO → 3. **ADAPTIVE COHERENCE GATE** → 4. Scoring → 5. Decision. The Adaptive Coherence Gate (V010) blocks low-quality signals BEFORE scoring computation with dynamic thresholds based on EMA score + Black Swan severity.

### Scoring Logic
Scoring is based on 5 core inputs: EMA Regime Signal (40 pts, PRIMARY DRIVER), HMM Regime (25 pts), Kalman Filter (15 pts), Non-Markovian Memory (15 pts), and Kelly Criterion (10 pts, modifier). A separate Veto/Penalty layer includes Monte Carlo, Black Swan, Sentiment, and Quantum Momentum, which only apply penalties and no additive scoring.

### Kalman Filter Optimization (Jan 10, 2026)
DualKalmanTrendFilter includes log suppression (`suppress_log=True`) in `filter_series()` to eliminate 4 initialization logs per analysis cycle. The `reset_state=True` default preserves correct behavior (state reset on each call), while `suppress_log` prevents log spam from AdaptiveKalmanFilter reinitializations. Class-level `_pair_cache` and `get_cached_filter(pair)` available for advanced use cases requiring incremental filtering.

### TRACK_RECORD_MODE
`TRACK_RECORD_MODE` and `LOW_VOL_MODE` are controlled by environment variables with `false` as default. When active, `TRACK_RECORD_MODE` caps score, reduces sizing, and enables `WEAK_TREND` scoring, while maintaining all guardrails. It auto-deactivates under specific conditions (`total_trades >= 100` AND `win_rate >= 45%`).

### Error Handling
An `ai_error_handler.py` provides an `ErrorClassifier` with 8 categories, SDK-specific error detection, intelligent retry/failover with exponential backoff, and structured logging.

### Web Search Service
Includes an `IntentDetector`, `SearchManager`, and `TavilySearch` client for intent-based web searches.

### Type Safety
Defensive type normalization is implemented to prevent `str` vs `int` comparison errors, particularly within the Coherence Engine and `AutoTradingBot._build_strategy_signals()`, using `normalize_signal()`, `normalize_strategy_signal()`, and `safe_float()`.

### Telegram Interaction
Improvements include increased timeouts for HTTPXRequest and all `requests.post()` calls (30s), retry mechanisms with exponential backoff for message sending, immediate ACK for user messages ("🧠 Procesando tu mensaje..."), and sending AI responses as new messages to prevent timeout issues. Voice responses are optimized for latency, sending text immediately and generating voice asynchronously. Voice is enabled for all users, with structured logging, retry mechanisms for gTTS, and skipping voice for very short texts.

### Operación Lucidez - Segmented Expectancy
This system analyzes segmented expectancy by categorizing trades based on `HMM_REGIME` and `COHERENCE_BUCKET` to calculate profitability (`E = (Win% × AvgWin) - (Loss% × |AvgLoss|)`) per market condition. It leverages data from `paper_trading_trades` and provides an API endpoint and a Streamlit dashboard widget for visualization.

### Modo Sniper - Precision Entry System
This system focuses on precision trade entries. It includes: ATR-Based Sizing (stop loss at `ATR × 2.5`, position sized to risk max 0.5% of balance), Volume Veto (blocks trades if 5-minute volume < 1-hour average), and Strategy Mode Tracking (tags trades as 'SNIPER' or 'STANDARD').

### Veto Tracking System
This system provides real-time capital protection tracking with PostgreSQL persistence for accurate investor reporting. It logs veto events from COHERENCE_GATE, MC, BLACK_SWAN, and RMS, with deduplication to prevent inflated reporting.

### Shadow Portfolio + Learning Engine
A counterfactual analysis system that tracks vetoed trades with full context to learn which filters need calibration. It analyzes price movement, calculates "would-have-won" scenarios, determines veto correctness, and provides filter threshold recommendations based on accuracy and potential profitability.

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