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
The AI service is refactored with SOLID principles and dependency injection, supporting multiple AI providers. It features an AI-first command detection, a Multilingual Prompt Architecture with dynamic language detection, and a Chain-of-Thought Framework. A critical AI Institutional Language Enforcement system ensures responses use approved institutional phrasing, blocking blacklisted terms and enforcing a "founder controlling risk" narrative. An AI Self-Knowledge System, driven by `system_state_manifest.json`, prevents AI "hallucinations" about system status.

### Hierarchical Veto Flow
The execution order is: 1. MC VETO → 2. RMS VETO → 3. **COHERENCE GATE** → 4. Scoring → 5. Decision. Coherence now blocks low-quality signals BEFORE scoring computation, with critical thresholds reducing false positives.

### Telegram Voice Service Fix (Dec 31, 2025)
Fixed `UnboundLocalError: cannot access local variable 'asyncio'` caused by conditional imports inside `if`/`try` blocks. Python marked `asyncio` as local variable for entire function scope, failing when conditional block didn't execute.

**Fix:** Removed 3 redundant `import asyncio` statements (lines 3545, 4835, 6489) from `enterprise_bot.py`. Only global import (line 10) remains.

**Rule:** Never use conditional imports for modules used elsewhere in the same function.

### SDK Telegram Timeout Fix (Dec 31, 2025)
Configurado HTTPXRequest con 30s timeout para el SDK de python-telegram-bot:
```python
request = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0, write_timeout=30.0, pool_timeout=30.0)
Application.builder().token(token).request(request).build()
```

### Quantum Momentum Type Fix (Dec 31, 2025)
Fixed `safe_float` warnings for quantum signals:
- `quantum['signal']` es STRING ("BUY"/"SELL"/"HOLD"), no número
- `quantum['score']` es NÚMERO (0-10)
- `quantum['confidence']` es STRING ("HIGH"/"MEDIUM"/"LOW")

Corregido `_build_strategy_signals()` y scoring para usar `score` y mapear `confidence` a números.

### Telegram Timeout & Voice Reliability Fix (Dec 31, 2025)
Fixed multiple issues causing "Debug: Timed out" errors and missing audio responses:

**Problema 1: Timeout de Telegram muy corto (10s)**
- Aumentado de 10s a 30s en todas las llamadas a `requests.post()` para envío de mensajes
- HTTPXRequest configurado con 30s para todas las operaciones del SDK

**Problema 2: VoiceEngine se perdía entre mensajes**
- VoiceEngine se sobrescribía con `VoiceServiceEnterprise()` directo (sin atributo `.active`)
- Fix: Siempre usar `VoiceEngine()` que envuelve el servicio enterprise correctamente

**Problema 3: Mensajes de debug visibles al usuario**
- Removido `⚠️ Debug: {error}` de mensajes de error
- Ahora muestra: "🤖 OMNIX procesando tu mensaje. Por favor espera un momento..."

**Problema 4: Trading loop no terminaba gracefully**
- Detectar "interpreter shutdown" o "cannot schedule new futures" y hacer `break`
- Previene loops infinitos de error durante redeploys de Railway

**FIX V2 (Dec 31, 2025): Retry con Backoff para Envío de Mensajes**
- Nuevas funciones `send_message_with_retry()` y `edit_message_with_retry()`
- 3 reintentos con backoff exponencial (2s, 4s, 6s)
- Manejo específico de TimedOut, NetworkError, RetryAfter
- Logging detallado: AI_CALL_START, AI_CALL_END para diagnóstico

**FIX FINAL (Dec 31, 2025): ACK Inmediato + Respuesta Nueva**
- ACK inmediato: `"🧠 Procesando tu mensaje..."` sale en <100ms
- IA procesa sin prisa (sin timeout pressure)
- Respuesta llega como mensaje NUEVO (no edit_text que puede fallar)
- Esto evita timeouts porque no hay edit operation que expire
- UX mejorada: bot parece "rápido" aunque la IA tarde

**Mejoras Futuras (Technical Debt):**
- Centralizar timeout de Telegram en configuración
- VoiceEngine singleton persistente entre llamadas

### OMNIX Identity Prompt (Dec 31, 2025)
Nuevo prompt de identidad core añadido a `prompt_templates.py` con 7 reglas comportamentales:
1. **Interpreta intención** - técnica/estratégica/credibilidad/inversión antes de responder
2. **Responde bien a la primera** - sin rodeos ni fragmentación
3. **Coherencia narrativa** - mantener línea clara, no contradecir
4. **Precisión > Defensa** - límites sin autodestruir narrativa
5. **Diferencia resultados de arquitectura** - performance vs estructura
6. **Tono** - seguro, técnico, sobrio
7. **Datos no disponibles** - formato seco sin disculpas

**Objetivo:** "No me está vendiendo humo, pero tampoco está perdido."

### Investor Response Rules Enhancement V2 (Dec 31, 2025)
Sistema completo de respuestas institucionales con 8 reglas y formatos ultra-secos:

**Reglas en MASTER_SYSTEM_PROMPT (8 total):**
1. **NO UNVERIFIABLE CLAIMS** - No afirmar datos sin evidencia
2. **NO PERCENTAGE WITHOUT SOURCE** - No dar % sin fuente auditable
3. **NEVER SAY "REFINANDO"** - Usar "el mercado habilita"
4. **CLOSE INACTIVITY RISK** - Frases letales para objeciones
5. **FOUNDER CONTROLS, MARKET ENABLES** - Narrativa correcta
6. **ACCEPT LIMITATIONS WITHOUT JUSTIFICATION** - Sin spin defensivo
7. **PROTECT EDGE WITHOUT CONCEDING DEFEAT** - Frase protectora obligatoria
8. **DATA NOT AVAILABLE FORMAT** - Formato ultra-seco para métricas faltantes
9. **NO SELF-FLAGELLATION** - Sin autoinculpación excesiva, una vez aceptado el fallo, pasar a "¿Qué sigue?"
10. **NO FUTURE PROMISES** - No "me comprometo", solo estado factual presente
11. **NO IRRELEVANT DATA BLOCKS** - Sin bloques de precios como relleno

**Frase Protectora Obligatoria:**
> "La ausencia de este reporte hoy no invalida el sistema; significa que el edge aún no está cuantificado de forma falsable."

**Nuevos Tipos de Respuesta:**
- `DATA_NOT_AVAILABLE`: Formato seco para métricas pendientes
- `FALSIFIABLE_REPORT`: Respuesta cuando piden script reproducible
- `SYSTEM_INACTIVITY`: "Pocas ventanas buenas > muchas mediocres"
- `OVER_FILTERING`: "Type II errors > Type I errors"
- `WHY_NOT_BUY_BTC`: "Asymmetric optionality vs passive holding"
- `RISK_OFF_BOT`: "Control de riesgo demostrado + edge pendiente de validación"

**Archivos Modificados:**
- `omnix_services/ai_service/prompt_templates.py` (11 reglas)
- `omnix_services/ai_service/investor_responses.py` (6 nuevos tipos)

### Type Safety - SCOPE EXPANDIDO (Dec 30, 2025)
Defensive type normalization to prevent `str vs int` comparison errors:

**Fase 1: Coherence Engine**
- `normalize_signal()` - Converts string "BUY"/"SELL" to Enum Signal
- `normalize_strategy_signal()` - Normalizes signal, confidence (0-1), strength

**Fase 2: AutoTradingBot._build_strategy_signals()**
- `safe_float()` - Applied to 7 strategies extracting numeric values from dictionaries
- Strategies: quantum_momentum, kalman_filter, monte_carlo, kelly_criterion, black_swan, sentiment, non_markovian
- safe_float now strips '%' from numeric strings and handles whitespace

**Tests:** 16 coherence + 28 auto_trading_bot type safety | **Total Dec 30:** ~71 tests

### Scoring Logic
Scoring is based on 5 core inputs: EMA Regime Signal (40 pts, PRIMARY DRIVER), HMM Regime (25 pts), Kalman Filter (15 pts), Non-Markovian Memory (15 pts), and Kelly Criterion (10 pts, modifier). A separate Veto/Penalty layer includes Monte Carlo, Black Swan, Sentiment, and Quantum Momentum, which only apply penalties and no additive scoring.

### TRACK_RECORD_MODE (Updated Dec 30, 2025)
`TRACK_RECORD_MODE` and `LOW_VOL_MODE` are now **controlled by environment variables** with `false` as default.

| Variable | Default | Purpose |
|----------|---------|---------|
| `TRACK_RECORD_MODE` | `false` | Reduces thresholds for trade generation |
| `LOW_VOL_MODE` | `false` | Adjusts for low-volatility markets |

**Rollback sin redeploy:**
```bash
# Railway: Settings → Variables → Add
TRACK_RECORD_MODE=true
# Then restart service
```

When active, TRACK_RECORD_MODE caps score (6/12), reduces sizing (0.35x max), enables `WEAK_TREND` scoring. All guardrails (RMS, MC Veto, Coherence) remain active. Auto-deactivates when `total_trades >= 100` AND `win_rate >= 45%`.

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