# OMNIX V6.5.4d INSTITUTIONAL+

## Overview
OMNIX V6.5.4d INSTITUTIONAL+ is an enterprise-grade automated cryptocurrency and stock trading system designed for paper trading to build a credible track record for investor presentations. Its core capabilities include AI integration, post-quantum cryptography, real-time market analysis, Non-Markovian Temporal Memory, adaptive parameter calibration, institutional portfolio optimization, derivatives trading, and dual-market support for Kraken (crypto) and Alpaca (stocks). The system targets 3-5 trades/day with a 55%+ win rate and focuses on an "Investor-Ready" presentation to secure seed funding. The project's ambition is to secure seed funding by presenting a credible track record.

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
The AI service is refactored with SOLID principles and dependency injection, supporting multiple AI providers. It features an AI-first command detection, a Multilingual Prompt Architecture with dynamic language detection, and a Chain-of-Thought Framework. A critical AI Institutional Language Enforcement system ensures responses use approved institutional phrasing, blocking blacklisted terms and enforcing a "founder controlling risk" narrative. An AI Self-Knowledge System, driven by `system_state_manifest.json`, prevents AI "hallucinations" about system status. OMNIX Identity Prompt and Investor Response Rules enhance AI behavior and communication.

### Hierarchical Veto Flow
The execution order is: 1. MC VETO → 2. RMS VETO → 3. **COHERENCE GATE** → 4. Scoring → 5. Decision. Coherence now blocks low-quality signals BEFORE scoring computation, with critical thresholds reducing false positives.

### Scoring Logic
Scoring is based on 5 core inputs: EMA Regime Signal (40 pts, PRIMARY DRIVER), HMM Regime (25 pts), Kalman Filter (15 pts), Non-Markovian Memory (15 pts), and Kelly Criterion (10 pts, modifier). A separate Veto/Penalty layer includes Monte Carlo, Black Swan, Sentiment, and Quantum Momentum, which only apply penalties and no additive scoring.

### TRACK_RECORD_MODE
`TRACK_RECORD_MODE` and `LOW_VOL_MODE` are controlled by environment variables with `false` as default. When active, `TRACK_RECORD_MODE` caps score, reduces sizing, and enables `WEAK_TREND` scoring, while maintaining all guardrails. It auto-deactivates under specific conditions (`total_trades >= 100` AND `win_rate >= 45%`).

### Error Handling
An `ai_error_handler.py` provides an `ErrorClassifier` with 8 categories, SDK-specific error detection, intelligent retry/failover with exponential backoff, and structured logging.

### Web Search Service
Includes an `IntentDetector`, `SearchManager`, and `TavilySearch` client for intent-based web searches.

### Type Safety
Defensive type normalization is implemented to prevent `str` vs `int` comparison errors, particularly within the Coherence Engine and `AutoTradingBot._build_strategy_signals()`, using `normalize_signal()`, `normalize_strategy_signal()`, and `safe_float()`.

### Telegram Interaction
Improvements include increased timeouts for HTTPXRequest and all `requests.post()` calls (30s), retry mechanisms with exponential backoff for message sending, immediate ACK for user messages ("🧠 Procesando tu mensaje..."), and sending AI responses as new messages to prevent timeout issues.

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

## Investor Response Rules Enhancement (Jan 1, 2026)
Sistema completo de respuestas institucionales con 13 reglas:

**Reglas en MASTER_SYSTEM_PROMPT (13 total):**
1. **NO UNVERIFIABLE CLAIMS / NO INVENTED CAPABILITIES** - No afirmar datos sin evidencia, NO inventar integraciones (WhaleTracker, Arkham, etc.)
2. **NO PERCENTAGE WITHOUT SOURCE** - No dar % sin fuente auditable
3. **NEVER SAY "REFINANDO"** - Usar "el mercado habilita"
4. **CLOSE INACTIVITY RISK** - Frases letales para objeciones
5. **FOUNDER CONTROLS, MARKET ENABLES** - Narrativa correcta
6. **ACCEPT LIMITATIONS WITHOUT JUSTIFICATION** - Sin spin defensivo
7. **PROTECT EDGE WITHOUT CONCEDING DEFEAT** - Frase protectora
8. **DATA NOT AVAILABLE FORMAT** - Formato ultra-seco para métricas faltantes
9. **NO SELF-FLAGELLATION** - Sin autoinculpación excesiva
10. **NO FUTURE PROMISES** - Solo estado factual presente
11. **NO IRRELEVANT DATA BLOCKS** - Sin bloques de precios como relleno
12. **ESCENARIOS TRAMPA (TÉCNICOS Y ÉTICOS)** - Responder en 3-5 líneas, NO inventar capacidades
13. **TECHNICAL DIAGNOSTIC MODE [HARD OVERRIDE]** - ANULA reglas narrativas. PROHIBIDO: justificar diseño, defender sistema, "edge", "según diseño", "protegiendo capital", "en teoría". OBLIGATORIO: métrica única (Expectancy por hmm_regime × coherence_state) + query SQL. Actitud: auditor frío. Máx 20 líneas. **Mejoras (Jan 2, 2026):** (1) HYPOTHETICAL DETECTION - detecta "supón que", "assume", etiqueta escenarios como HIPOTÉTICO vs datos reales; (2) FORMAT ENFORCEMENT - fallback si excede formato; (3) BLACKLIST SELF-CHECK - auto-verificación de frases prohibidas ("mejora notable", "signo positivo", "el sistema está aprendiendo").

**Frase Protectora Obligatoria:**
> "La ausencia de este reporte hoy no invalida el sistema; significa que el edge aún no está cuantificado de forma falsable."

**Tipos de Respuesta:**
- `NEGATIVE_PNL`, `LOW_WIN_RATE`, `HOLD_STRATEGY`, `SYSTEM_VALIDATION`, `RISK_MANAGEMENT`, `TRACK_RECORD`
- `SYSTEM_INACTIVITY`: "Pocas ventanas buenas > muchas mediocres"
- `OVER_FILTERING`: "Type II errors > Type I errors"
- `WHY_NOT_BUY_BTC`: "Asymmetric optionality vs passive holding"
- `DATA_NOT_AVAILABLE`: Formato seco para métricas pendientes
- `FALSIFIABLE_REPORT`: Respuesta cuando piden script reproducible
- `RISK_OFF_BOT`: "Control de riesgo demostrado + edge pendiente"
- `HYPOTHETICAL_SCENARIO`: Escenarios técnicos ficticios (3-5 líneas)
- `ETHICAL_SCENARIO`: Escenarios éticos ficticios (3-5 líneas)
- `TECHNICAL_DIAGNOSTIC`: Respuesta sin narrativa (máx 15 líneas + query SQL)

**Archivos Clave:**
- `omnix_services/ai_service/prompt_templates.py` (MASTER_SYSTEM_PROMPT + 13 reglas)
- `omnix_services/ai_service/investor_responses.py` (15 tipos de respuesta)
- `omnix_config/system_state_manifest.json` (capacidades documentadas)

## Operación Lucidez - Segmented Expectancy (Jan 1, 2026)

Sistema de análisis de expectancy segmentada para identificar DÓNDE gana el sistema.

**Concepto:** Segmentar trades por (HMM_REGIME × COHERENCE_BUCKET) para calcular expectancy por condición de mercado.

**Fórmula:** `E = (Win% × AvgWin) - (Loss% × |AvgLoss|)`

**Implementación:**
- Migration V005: Añadió columnas `hmm_regime`, `coherence_score`, `ema_regime_signal`, `strategy_confidence` a `paper_trading_trades`
- Telemetry capture: AutoTradingBot extrae métricas del análisis y las pasa a execute_paper_trade()
- Query: `get_segmented_expectancy()` en `omnix_dashboard/utils/queries.py`
- API: `/api/metrics/expectancy` en Flask dashboard
- Widget: "Expectancy" en Streamlit dashboard con heatmap de segmentos

**Valor para Inversores:**
- Demuestra entendimiento cuantitativo de DÓNDE tiene edge el sistema
- Métricas falsables con mínimo de 5 trades por segmento
- Permite filtrado por régimen para concentrar trading en condiciones rentables

**Documentación:** `docs/operations/OPERACION_LUCIDEZ.md`