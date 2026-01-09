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
The execution order is: 1. MC VETO → 2. RMS VETO → 3. **ADAPTIVE COHERENCE GATE** → 4. Scoring → 5. Decision. The Adaptive Coherence Gate (V010) blocks low-quality signals BEFORE scoring computation with dynamic thresholds based on EMA score + Black Swan severity. See "Adaptive Coherence Gate" section below for threshold matrix.

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

### Operación Lucidez - Segmented Expectancy
This system analyzes segmented expectancy by categorizing trades based on `HMM_REGIME` and `COHERENCE_BUCKET` to calculate profitability (`E = (Win% × AvgWin) - (Loss% × |AvgLoss|)`) per market condition. It leverages data from `paper_trading_trades` and provides an API endpoint and a Streamlit dashboard widget for visualization.

### Modo Sniper - Precision Entry System
This system focuses on precision trade entries. It includes:
1.  **ATR-Based Sizing**: Stop loss set at `ATR × 2.5`, with position sized to risk a maximum of 0.5% of balance.
2.  **Volume Veto**: Blocks trades if 5-minute volume is less than the 1-hour average to avoid manipulation.
3.  **Strategy Mode Tracking**: Tags trades as 'SNIPER' or 'STANDARD' for performance comparison.

### Voice TTS Natural Reading
This feature improves the natural reading of formatted messages in voice responses by converting numbers (e.g., `*1.`) to spoken text ("Punto uno,") and preserving content while removing formatting symbols (e.g., `*Title*` becomes "Title").

### Voice Response Async Optimization (V007 - Jan 4, 2026)
Optimizes latency for voice responses by sending text immediately to the user, then generating and delivering the voice message asynchronously in the background.

**V007 Improvements:**
- Voice enabled for ALL users (no plan restriction)
- Structured logging with chat_id/user_id tracking
- Retry with backoff for gTTS (3 attempts, 2s/4s delays)
- Safe wrapper `_process_and_send_voice_safe()` captures ALL thread exceptions
- Skip voice for text < 20 chars (prevents noise)

### Adaptive Coherence Gate (V010 - Jan 9, 2026)
Dynamic coherence thresholds based on EMA score + Black Swan severity. **Centralized architecture** with all logic in CoherenceEngine (domain service).

**Threshold Matrix:**
| EMA Score | Black Swan | Coherence Min |
|-----------|------------|---------------|
| ≥ 25 pts | LOW | 35% |
| ≥ 25 pts | MEDIUM | 45% |
| ≥ 25 pts | HIGH/EXTREME | 55-65% |
| < 25 pts | any | 10%/30% (paper/real default) |

**Architecture (V010):**
- **AdaptiveGateDecision**: DTO with decision + thresholds
- **evaluate_pre_scoring_gate()**: Public API in CoherenceEngine
- Bot delegates to CoherenceEngine instead of using hardcoded profile values

**Verification in Railway Logs:**
```json
{"event": "ADAPTIVE_GATE_DECISION", "block_threshold": 35, "adaptive_gate_active": true}
```

**Investor Language:** "OMNIX dynamically calibrates coherence filters based on market regime severity, maximizing opportunity capture while maintaining institutional discipline."

### Veto Tracking System (V008 - Jan 7-8, 2026)
Real-time capital protection tracking with PostgreSQL persistence for accurate investor reporting.

**Components:**
- **VetoRepository** (`omnix_services/database_service/veto_repository.py`): Singleton with `log_veto()` and aggregations
- **Migration V006**: Table `trading_veto_log` with 14 columns
- **Bot Instrumentation**: `_log_veto()` calls at COHERENCE_GATE, MC, BLACK_SWAN, RMS veto points
- **API Endpoint**: `/api/system/quarantine` returns capital protected (48h/7d breakdown)
- **Dashboard Widget**: `quarantine.js` displays veto breakdown by type

**Veto Types Tracked:**
| Type | Trigger |
|------|---------|
| COHERENCE_GATE | coherence_score < 45% |
| MC_NEG_ER | Monte Carlo ER < 0 |
| BLACK_SWAN | crash_prob > 30% |
| RMS | CircuitBreaker or LimitsEngine |

**Deduplication (V008b - Jan 8, 2026):**
- Cache de 15 minutos por (veto_type, symbol) evita registros duplicados
- Previene inflación de números ($105M → $940K realista)
- Logs: `⏭️ [VETO_SKIPPED]` cuando se detecta duplicado

**psycopg v3 Compatibility:** Uses `psycopg` (v3) with fallback to `psycopg2`, JSON serialization via `json.dumps()`.

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

## Performance Honesty Guard (Jan 3-4, 2026)

Sistema contextual que da respuestas honestas sobre métricas SOLO cuando el usuario pregunta.

**Estrategia de 2 Fases:**
- **Fase 1 (Anti-Pérdida)**: Sistema aprende a NO perder. Pérdidas = datos de entrenamiento.
- **Fase 2 (Optimización)**: Una vez que evita pérdidas, se optimiza para ganar.

**Comportamiento:**
- En conversación normal: Bot se comporta igual que antes
- Cuando preguntas sobre métricas/rendimiento: Activa contexto honesto sin drama

**Detección de intención:** Patrones como "profit factor", "como vamos", "win rate", "funciona", "track record"

**Fases del sistema:**
- `phase1_early`: PF < 0.5, WR < 25% → "Identificando patrones de pérdida"
- `phase1_progress`: PF 0.5-0.8, WR 25-35% → "Documentando y bloqueando pérdidas"
- `phase1_ready`: PF > 0.8, WR > 35% → "Cerca de transición a Fase 2"
- `phase2`: PF > 0.8, WR > 35%, >200 trades → "Optimización de ganancias"

**Criterios de transición Fase 1 → Fase 2:**
- Mínimo 200 trades
- Profit Factor >= 0.8
- Win Rate >= 35%

**Ejemplo de respuesta en Fase 1:**
> "Fase Actual: Aprendizaje Anti-Pérdida (Fase 1). Métricas: Profit Factor 0.20, Win Rate 20% en 119 trades. Contexto: El sistema está identificando patrones que causan pérdidas. Estos resultados son datos de entrenamiento, no rendimiento final."

**Archivos clave:**
- `omnix_services/ai_service/honesty_guard.py` (PerformanceHonestyGuard class)
- `omnix_services/ai_service/prompt_templates.py` (integración en build_complete_prompt)