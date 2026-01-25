# OMNIX V6.5.4e INSTITUTIONAL+

## Overview
OMNIX V6.5.4e INSTITUTIONAL+ is an institutional-grade risk control infrastructure for cryptocurrency trading. Its primary purpose is capital preservation (98.5% maintained) through a multi-layer veto architecture, incorporating advanced technologies like post-quantum cryptography, real-time market analysis, Non-Markovian Temporal Memory, a 6-tier Coherence Engine, Monte Carlo validation, Black Swan detection, and Kelly Criterion sizing. The system prioritizes safeguarding capital over trade volume, aiming to build a credible track record for institutional investors.

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
| **8. Seguridad** | `docs/reference/adr/ADR-022-post-quantum-cryptography.md` | PQC implementado Nov 2025 (Kyber-768/Dilithium-3) |

**Después de cambios significativos**, actualizar la documentación relevante.

> **CRÍTICO PQC (Jan 23, 2026)**: Post-Quantum Cryptography YA ESTÁ IMPLEMENTADO desde Nov 2025. La IA NO debe decir "PQC planificado para Q3 2026". Las órdenes de trading se firman con Dilithium-3. Ver ADR-022.

### Investor Challenge Response Framework (ADR-024 - Jan 25, 2026)

Cuando un inversor pregunte sobre trade-offs comparativos (opportunity cost, risk avoided, buy & hold vs, justify), el bot DEBE responder con estructura:

1. **NUMBER FIRST**: Abrir con cuantificación (ej: "Opportunity Cost: $847. Risk Avoided: $2,340. Net EV: +$1,493")
2. **FRAMEWORK SECOND**: Explicar cómo se calculó (fórmulas ADR-020, data freshness)
3. **POSITIONING THIRD**: Clarificar qué es OMNIX ("governance infrastructure, not BTC hold competitor")

**PROHIBIDO en investor_challenge:**
- "Estamos en fase de aprendizaje" (suena a "confía sin datos")
- "Es difícil cuantificar" sin dar fórmula
- "No es una comparación justa" sin explicar por qué

Ver ADR-024 para keywords de detección y ejemplos.

### Track Record Period Disclosure (OBLIGATORIO - Jan 24, 2026)

| Período | Fechas | Trades | P&L | Propósito |
|---------|--------|--------|-----|-----------|
| **Learning Baseline** | Nov 2025 - 14 Ene 2026 | 119 | -$15,198.73 | Calibración |
| **Track Record Oficial** | 15 Ene 2026 - presente | ~0 | $0 | Validación recalibrada |

> **REGLA**: Cuando la IA reporte métricas (P&L, win rate, trades, losses), DEBE agregar al final:
> 
> **Nota de Período**: Estos datos corresponden al Learning Baseline (Nov-Dic 2025), fase de calibración. Desde el 15 de enero 2026, el sistema opera con parámetros recalibrados en el Track Record Oficial.

**NO aplica para**: saludos, comandos, preguntas técnicas sin métricas. Ver ADR-023.

## System Architecture

### Core Components and Design Patterns
The system features an AutoTradingBot, Non-Markovian Memory Kernel, 6-Tier Veto System (Coherence Engine), AI Risk Guardian, Portfolio Management, Confidence-Adaptive Entry System (CAES), On-Chain Data Intelligence, and an Execution Protocol. It supports multi-user roles, Flask and Streamlit dashboards, an Asset Quarantine System, Real-Time Latency Monitor, Price Stale Detection, and Admin Alerts. The UI is designed for an "Investor-Ready" presentation. The Decision Engine uses an EMA Regime Signal, a Monte Carlo VETO Engine, and RMS Enforcement, with all decisions auditable via `decision_trace`. Defensive hardening includes Position Size Factor Clamping and Veto Sentinel Logs. The system is designed with a hexagonal architecture (V7.0) with activation via the Strangler Fig pattern.

### AI Architecture and Enforcement
The AI service adheres to SOLID principles and dependency injection, supporting multiple AI providers. It includes AI-first command detection, a Multilingual Prompt Architecture, and a Chain-of-Thought Framework. An AI Self-Knowledge System, driven by `system_state_manifest.json`, prevents "hallucinations." OMNIX Identity Prompt and Investor Response Rules enhance AI behavior. A Performance Honesty Guard provides honest metrics. AI responses are adaptively detailed based on user requests, with comprehensive responses for investor queries. An Anti-Servile Post-Processing Filter removes servile phrases after AI generation.

### Hierarchical Veto Flow
The execution order is: 1. MC VETO → 2. RMS VETO → 3. **ADAPTIVE COHERENCE GATE** → 4. **ECW GATE** → 5. Scoring → 6. Decision. The Adaptive Coherence Gate blocks low-quality signals dynamically. The Edge Confirmation Window (ECW) requires edge persistence (MC_WR ≥ 52%, MC_ER > 0%, Black Swan ≤ MEDIUM for 3 consecutive cycles) before allowing trades, effectively transforming "capital preservation" into "capital patience".

### Scoring Logic
Scoring is based on 5 core inputs: EMA Regime Signal (40 pts), HMM Regime (25 pts), Kalman Filter (15 pts), Non-Markovian Memory (15 pts), and Kelly Criterion (10 pts). A separate Veto/Penalty layer (Monte Carlo, Black Swan, Sentiment, Quantum Momentum) applies only penalties.

### TRACK_RECORD_MODE
This mode caps scores, reduces sizing, enables `WEAK_TREND` scoring, and maintains guardrails. It auto-deactivates when `total_trades >= 100` AND `win_rate >= 45%`.

### Operación Lucidez - Segmented Expectancy
Analyzes segmented expectancy by categorizing trades based on `HMM_REGIME` and `COHERENCE_BUCKET` to calculate profitability per market condition, leveraging `paper_trading_trades` data.

### Modo Sniper - Precision Entry System
Focuses on precision trade entries with ATR-Based Sizing (risk max 0.5% balance), Volume Veto (blocks trades if 5-min volume < 1-hour average), and Strategy Mode Tracking ('SNIPER' or 'STANDARD').

### Veto Tracking System
Provides real-time capital protection tracking with PostgreSQL persistence for investor reporting, logging and deduplicating veto events.

### Shadow Portfolio + Learning Engine
A counterfactual analysis system that tracks vetoed trades to learn filter calibration. It analyzes price movement, determines veto correctness, and provides filter threshold recommendations. An Opportunity Tracker analyzes Missed Opportunities vs Losses Avoided vs Net Opportunity.

### Decision Contradiction Index (DCI)
A shadow observational metric measuring internal signal divergence to explain HOLDs. High DCI (≥70) indicates high internal contradiction between signals, mandating a HOLD. Realistic execution thresholds require MC WR > 50%, MC ER > 0%, Coherence > 50%, and DCI < 70.

### Dashboard Features
The dashboard displays a Dual Win Rate Framework, enriched AI context, a System Health Score, Live Status, Quick Insights, Calibration Progress, and Recommended Actions. Credibility improvements include clarifying "Est. Loss Avoided" vs "Notional Blocked" and distinguishing "Market Trend" from "Trading Regime." Additional widgets include Comparative Metrics, P&L Breakdown, Correlation Heatmap, Time Heatmap, Regime Detection Dashboard, and Learning Engine Insights. An `InvestorDataProvider` facilitates read-only SQL queries for segmented metrics.

### Analytical VIEW: v_shadow_trade_metrics
A PostgreSQL VIEW parses `decision_trace` JSONB from `shadow_trade_events` to enable retroactive DCI analysis and investor demos. It extracts metrics like `mc_win_rate`, `mc_expected_return`, `coherence_score`, `ecw_cycles`, `ecw_status`, `black_swan_severity`, and `approx_dci`. The Streamlit Shadow Analytics Page answers "How does OMNIX decide and why does it NOT trade?" by displaying system overview, decision quality, and governance/risk metrics.

## External Dependencies

### APIs and Services
-   **Kraken Exchange**: Crypto data and order execution.
-   **Alpaca**: Stock data and historical bars.
-   **Google Gemini (2.0 Flash)**: Primary AI model.
-   **OpenAI (GPT-4o, Whisper)**: AI services.
-   **Anthropic Claude**: AI fallback.
-   **ElevenLabs**: Text-to-speech.
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