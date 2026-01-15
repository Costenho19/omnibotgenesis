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
The AI service adheres to SOLID principles and dependency injection, supporting multiple AI providers. It features AI-first command detection, a Multilingual Prompt Architecture with dynamic language detection, and a Chain-of-Thought Framework. An AI Self-Knowledge System, driven by `system_state_manifest.json`, prevents AI "hallucinations." OMNIX Identity Prompt and Investor Response Rules enhance AI behavior and communication. The Performance Honesty Guard provides honest metrics and contextual truth for investor communications. AI responses are subject to brevity policies with word limits and adaptive detail based on user requests.

### Hierarchical Veto Flow
The execution order is: 1. MC VETO → 2. RMS VETO → 3. **ADAPTIVE COHERENCE GATE** → 4. Scoring → 5. Decision. The Adaptive Coherence Gate blocks low-quality signals BEFORE scoring computation with dynamic thresholds based on EMA score + Black Swan severity. Calibration for Coherence Thresholds (ADR-007 Phase 1) involves a 5-point threshold reduction across all levels and an EMA trigger adjustment to improve trade throughput.

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
A counterfactual analysis system that tracks vetoed trades with full context to learn which filters need calibration. It analyzes price movement, calculates "would-have-won" scenarios, determines veto correctness, and provides filter threshold recommendations. An Opportunity Tracker (ADR-008) analyzes Missed Opportunities vs Losses Avoided vs Net Opportunity, with a dashboard widget for visual balance.

### Dashboard Features
The dashboard displays a Dual Win Rate Framework, enriched AI context with granular breakdowns, a System Health Score (0-100), Live Status widget, Quick Insights, Calibration Progress (4-phase tracker), and Recommended Actions. Key dashboard credibility improvements include clarifying "Est. Loss Avoided" vs "Notional Blocked", distinguishing "Market Trend" from "Trading Regime", and providing a timeline for Calibration Progress. Additional widgets include Comparative Metrics, P&L Breakdown, Correlation Heatmap, Time Heatmap, Regime Detection Dashboard, and Learning Engine Insights.

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