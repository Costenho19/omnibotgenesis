# OMNIX V6.5.4e INSTITUTIONAL+

## Overview
OMNIX V6.5.4e INSTITUTIONAL+ is an institutional-grade risk control infrastructure for cryptocurrency trading. Its core purpose is capital preservation through a multi-layer veto architecture, integrating post-quantum cryptography, real-time market analysis, Non-Markovian Temporal Memory, a 6-tier Coherence Engine, Monte Carlo validation, Black Swan detection, and Kelly Criterion sizing. The system prioritizes safeguarding capital to build a credible track record for institutional investors. It offers a dual revenue model: B2C SaaS for direct users and B2B Enterprise Licensing for platforms, brokers, and exchanges.

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

> **CRÍTICO PQC**: Post-Quantum Cryptography YA ESTÁ IMPLEMENTADO desde Nov 2025. La IA NO debe decir "PQC planificado para Q3 2026". Las órdenes de trading se firman con Dilithium-3. Ver ADR-022.

### Investor Challenge Response Framework (ADR-024)

Cuando un inversor pregunte sobre trade-offs comparativos (opportunity cost, risk avoided, buy & hold vs, justify), el bot DEBE responder con estructura:

1. **NUMBER FIRST**: Abrir con cuantificación (ej: "Opportunity Cost: $847. Risk Avoided: $2,340. Net EV: +$1,493")
2. **FRAMEWORK SECOND**: Explicar cómo se calculó (fórmulas ADR-020, data freshness)
3. **POSITIONING THIRD**: Clarificar qué es OMNIX ("governance infrastructure, not BTC hold competitor")

**PROHIBIDO en investor_challenge:**
- "Estamos en fase de aprendizaje" (suena a "confía sin datos")
- "Es difícil cuantificar" sin dar fórmula
- "No es una comparación justa" sin explicar por qué

Ver ADR-024 para keywords de detección y ejemplos.

### Track Record Period Disclosure (OBLIGATORIO)

| Período | Fechas | Trades | P&L | Propósito |
|---------|--------|--------|-----|-----------|
| **Learning Baseline** | Nov 2025 - 14 Ene 2026 | 119 | -$15,198.73 | Calibración |
| **Track Record Oficial** | 15 Ene 2026 - presente | 0 | $0 | Validación recalibrada |

### Dashboard Investor Credibility

| Métrica | Comportamiento |
|---------|----------------|
| **Max DD** | Siempre ≤ 0% (normalizado) |
| **Win Rate** | N/A cuando 0 trades en Track Record |
| **Header P&L** | Etiquetado "(Baseline)" para evitar confusión |
| **Est. Loss Avoided** | Capped a $100K con footnote explicativo |

**Fórmula Est. Loss Avoided:**
```
Est. Loss = Cycles × $20K × 2.5% = capped at $100K
```

> **REGLA**: Cuando la IA reporte métricas (P&L, win rate, trades, losses), DEBE agregar al final:
> 
> **Nota de Período**: Estos datos corresponden al Learning Baseline (Nov-Dic 2025), fase de calibración. Desde el 15 de enero 2026, el sistema opera con parámetros recalibrados en el Track Record Oficial.

**NO aplica para**: saludos, comandos, preguntas técnicas sin métricas. Ver ADR-023.

## System Architecture

### Core Components and Design Patterns
OMNIX incorporates an AutoTradingBot, Non-Markovian Memory Kernel, a 6-Tier Veto System (Coherence Engine), AI Risk Guardian, Portfolio Management, Confidence-Adaptive Entry System (CAES), On-Chain Data Intelligence, and an Execution Protocol. It supports multi-user roles, Flask and Streamlit dashboards, an Asset Quarantine System, Real-Time Latency Monitor, Price Stale Detection, and Admin Alerts. The UI is designed for an "Investor-Ready" presentation. The Decision Engine uses an EMA Regime Signal, a Monte Carlo VETO Engine, and RMS Enforcement, with all decisions auditable via `decision_trace`. Defensive hardening includes Position Size Factor Clamping and Veto Sentinel Logs. The system is designed with a hexagonal architecture (V7.0) with activation via the Strangler Fig pattern.

### AI Architecture and Enforcement
The AI service adheres to SOLID principles and dependency injection, supporting multiple AI providers. It includes AI-first command detection, a Multilingual Prompt Architecture, and a Chain-of-Thought Framework. An AI Self-Knowledge System, driven by `system_state_manifest.json`, prevents "hallucinations." OMNIX Identity Prompt and Investor Response Rules enhance AI behavior. A Performance Honesty Guard provides honest metrics. AI responses are adaptively detailed based on user requests, with comprehensive responses for investor queries. An Anti-Servile Post-Processing Filter removes servile phrases after AI generation.

### Hierarchical Veto Flow
The execution order is: 1. MC VETO → 2. RMS VETO → 3. **ADAPTIVE COHERENCE GATE** → 4. **ECW GATE** → 5. Scoring → 6. Decision. The Adaptive Coherence Gate dynamically blocks low-quality signals. The Edge Confirmation Window (ECW) requires edge persistence before allowing trades, ensuring "capital patience."

### ECW Configuration (v1.1 - Jan 29, 2026)
| Parameter | Value | ENV Variable |
|-----------|-------|--------------|
| **MC Win Rate Min** | 50% | `ECW_MC_WR_MIN` |
| **MC Expected Return Min** | > 0% | `ECW_MC_ER_MIN` |
| **Consecutive Cycles** | 3 | `ECW_CYCLES_REQUIRED` |
| **Black Swan Max** | MEDIUM | Hardcoded |

**Rollback to v1.0**: Set `ECW_MC_WR_MIN=52` in Railway Variables + restart service.

### Scoring Logic
Scoring is based on 5 core inputs: EMA Regime Signal (40 pts), HMM Regime (25 pts), Kalman Filter (15 pts), Non-Markovian Memory (15 pts), and Kelly Criterion (10 pts). A separate Veto/Penalty layer (Monte Carlo, Black Swan, Sentiment, Quantum Momentum) applies only penalties.

### TRACK_RECORD_MODE
This mode caps scores, reduces sizing, enables `WEAK_TREND` scoring, and maintains guardrails. It auto-deactivates when `total_trades >= 100` AND `win_rate >= 45%`.

### Shadow Portfolio + Learning Engine
A counterfactual analysis system tracks vetoed trades to learn filter calibration. It analyzes price movement, determines veto correctness, and provides filter threshold recommendations. An Opportunity Tracker analyzes Missed Opportunities vs Losses Avoided vs Net Opportunity. The system is currently active with over 192,000 shadow trade events captured.

### Decision Contradiction Index (DCI)
A shadow observational metric measuring internal signal divergence to explain HOLDs. High DCI (≥70) indicates high internal contradiction between signals, mandating a HOLD. Realistic execution thresholds require MC WR > 50%, MC ER > 0%, Coherence > 50%, and DCI < 70.

### Dashboard Features
The dashboard displays a Dual Win Rate Framework, enriched AI context, a System Health Score, Live Status, Quick Insights, Calibration Progress, and Recommended Actions. Credibility improvements include clarifying "Est. Loss Avoided" vs "Notional Blocked" and distinguishing "Market Trend" from "Trading Regime." Additional widgets include Comparative Metrics, P&L Breakdown, Correlation Heatmap, Time Heatmap, Regime Detection Dashboard, and Learning Engine Insights. An `InvestorDataProvider` facilitates read-only SQL queries for segmented metrics.

### Web Infrastructure
The project utilizes a multi-port architecture:
-   **OMNIX Web (Port 3000)**: React + Vite public landing pages. Features Commercial Landing (/) and Institutional Page (/institutional) with animated statistics, 4-Layer Validation Architecture, FAQ section, comparison table (OMNIX vs Traditional Trading), live market data, risk calculator, and multi-tier pricing. Automatic redirects from /terminal and unknown routes to /.
-   **Flask Dashboard (Port 5000)**: Flask + Jinja2 internal dashboard for demos and investor metrics. Main webview port.

### Custom Domain Configuration
| Domain | Purpose | Platform |
|--------|---------|----------|
| **www.omnixquantum.net** | Commercial Landing (Published) | Replit Static Deployment |
| **omnixquantum.net** | Dashboard/Bot (Production) | Railway |

**DNS Configuration (Cloudflare):**
- A record: www → 34.111.179.208 (Solo DNS)
- TXT record: www → replit-verify=c554b789-9f74-4d37-8420-c740ae31b663

### Contact Information
| Channel | Contact |
|---------|---------|
| **Email** | contacto@omnixquantum.net |
| **Phone** | +1 (650) 507-8293 |
| **WhatsApp** | +1 (650) 481-5494 |

### Recent Changes (Feb 7, 2026)
- **CRITICAL FIX - Gemini Model Update**: Google deprecated `gemini-2.0-flash-exp` (retirement March 31, 2026)
  - Updated ALL instances across 6 files to `gemini-2.5-flash` (stable GA model)
  - Files: settings.py, ai_models.py, conversational_ai_adapter.py, community_analyzer.py, advanced_intelligence.py, enterprise_bot.py
  - AI fallback chain: Gemini 2.5 Flash (primary) → GPT-4o → Claude Sonnet 4
- **OpenAI Key Validator Fix**: Relaxed from `startswith('sk-') and len > 40` to `len > 20` to support new key formats
- **AI Startup Diagnostics**: Added summary log showing available models and fallback chain at initialization
- **Response Time Optimization (~20s → ~10-14s)**:
  - Message aggregation delay: 1.5s → 0.5s (saves ~1s per message)
  - AI model max retries: 3 → 2 (avoids unnecessary retry loops)
  - Response validation retries: 2 → 1 (first response is usually good enough)
  - Market data timeouts: async 5s → 3s, sync 10s → 5s (faster failure/fallback)
  - Expanded simple query detection: threshold 20 → 30 chars, more patterns (GPT-4o-mini 3x faster)

### Recent Changes (Jan 30, 2026)
- **AI Response Speed Optimization**: 
  - Increased AI timeouts from 15s to 30s for OpenAI, Gemini, Anthropic
  - Added GPT-4o-mini fast path for simple queries (greetings, short messages)
  - Smart model selection: simple queries → GPT-4o-mini (3x faster), complex → GPT-4o
  - Relaxed validation for simple responses (MIN_RESPONSE_LENGTH_SIMPLE=10 vs 50)

### Recent Changes (Jan 29, 2026)
- **ECW Calibration v1.1**: Reduced MC_WR_MIN from 52% to 50% (ENV-configurable for rollback)
- Configured custom domain www.omnixquantum.net for commercial landing
- Added separate Phone and WhatsApp contact options to landing pages
- Removed Streamlit Dashboard (port 8080) - had proxy issues with Replit
- Simplified to 2 workflows: Flask Dashboard (5000) + OMNIX Web (3000)
- Full session logs: `docs/history/2026-01/2026-01-29-ecw-calibration.md`, `docs/history/2026-01/2026-01-29-domain-setup.md`

### Recent Changes (Jan 28, 2026)
- Added automatic redirect from `/terminal` to `/` in OMNIX Web to prevent navigation issues
- Added comparison table "OMNIX vs Traditional Trading" to Institutional Page
- Added FAQ section with 5 investor-focused questions
- Full session log: `docs/history/2026-01/2026-01-28-landing-improvements.md`

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