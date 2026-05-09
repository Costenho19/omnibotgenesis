# OMNIX — Arquitectura

**Internal Build Reference**: 6.5.4e  
**Actualizado**: 15 de Abril 2026  
**Estado**: Producción 24/7 — 11-checkpoint pipeline + EBIP + TIE + 10 Verticals activos  
**Último Cambio**: Scope Authorization Record (ADR-147) — May 9, 2026

---

## Visión General

```
┌─────────────────────────────────────────────────────────────────────┐
│                    OMNIX — Decision Governance Infrastructure         │
├─────────────────────────────────────────────────────────────────────┤
│  INTERFACES                                                          │
│  ├── Telegram Bot (enterprise_bot.py)                               │
│  ├── Flask Dashboard (puerto 5000) — B2B API + Demos                │
│  ├── React Web (puerto 3000) — Landing + /try sandbox + /verify     │
│  └── Verification Server (puerto 8000, aiohttp)                     │
├─────────────────────────────────────────────────────────────────────┤
│  GOVERNANCE PIPELINE (domain-agnostic, multi-vertical)              │
│                                                                      │
│  Signals → CAG (ADR-050) → EBIP·ACV (ADR-045) → 8 Checkpoints      │
│         → TIE (ADR-053) → PQC Receipt (Dilithium-3)                 │
│                                                                      │
│  Verticals:                                                          │
│  ├── Trading (ADR-028) — BTC/ETH/AVAX/USD 24/7                     │
│  └── Islamic Credit (ADR-052) — UAE SME/Individual/Corporate 24/7   │
├─────────────────────────────────────────────────────────────────────┤
│  CORE ENGINES                                                        │
│  ├── AutoTradingBot V6.5.4e - Multi-crypto scanner                  │
│  ├── CoherenceEngine V6.5 ULTRA - 6-tier veto + TCV (7th)           │
│  ├── Non-Markovian Kernel V6.5 - Memoria temporal                   │
│  ├── TrajectoryInvariantEngine (TIE) - Bounded evolution (ADR-053)  │
│  └── Risk Guardian V5.4 - Protección drawdown                       │
├─────────────────────────────────────────────────────────────────────┤
│  DATA LAYER                                                          │
│  ├── PostgreSQL (44+ tablas, 90% FK coverage)                       │
│  │   ├── trajectory_states (TIE history per asset/domain)           │
│  │   ├── credit_applications (Islamic Credit vertical)              │
│  │   └── credit_cycle_metrics (cycle aggregates)                    │
│  ├── Redis (cache + state management)                               │
│  └── DatabaseGateway (connection pool)                              │
├─────────────────────────────────────────────────────────────────────┤
│  EXTERNAL APIs                                                       │
│  ├── Kraken - Crypto data + ejecución                               │
│  ├── Gemini 2.5 Flash - AI primario                                 │
│  └── Tavily - Web search                                            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## AI-First Multilingual Architecture (Dec 22, 2025)

| Componente | Archivo | Función |
|------------|---------|---------|
| LanguageContextManager | `omnix_services/ai_service/prompt_templates.py` | Detección AI-first + Redis persistence |
| Gemini AI Detection | `gemini-2.5-flash` | Detección de textos cortos (<50 chars) |
| fast-langdetect | FastText-based | Detección de textos largos (≥50 chars) |
| Redis Language Cache | `omnix:user_language:{chat_id}` | 24h TTL por usuario |

**Flujo AI-First**:
```
Usuario escribe texto
    ↓
¿Texto ≥50 chars?
    SI → fast-langdetect (FastText, muy preciso)
    NO → Gemini AI (gemini-2.5-flash, temp=0)
    ↓
Fallback chain: fast-langdetect → langdetect → 'en'
    ↓
Resultado persistido en Redis → Prompt injection
    ↓
TTS: gTTS con mapeo ISO→gTTS (zh → zh-CN)
```

**Arquitectura de Detección**:
```python
def detect_language(text):
    # 1. Textos largos: FastText (rápido y preciso)
    if len(text) >= 50:
        result = fast_langdetect.detect(text)
        if result: return result
    
    # 2. Textos cortos: Gemini AI (singleton client)
    result = gemini.generate_content(
        model="gemini-2.5-flash",
        prompt=f"Detect language, return ISO code only: {text}",
        temperature=0.0, max_tokens=5
    )
    if result: return result
    
    # 3. Fallbacks
    return fast_langdetect(text) or langdetect(text) or 'en'
```

**Política**: 
- NO diccionarios multilingües hardcodeados
- Gemini AI para textos cortos (100% precisión)
- FastText para textos largos (eficiencia)
- TTS mapea ISO codes a gTTS (ej: zh → zh-CN)

---

## Investor Data Provider - ADR-013 (Jan 16, 2026)

| Componente | Archivo | Función |
|------------|---------|---------|
| InvestorDataProvider | `omnix_services/ai_service/providers/investor_data_provider.py` | Queries SQL reales para due diligence |
| _fetch_investor_data() | `conversational_ai_adapter.py` | Integración con flujo AI |

**Propósito:**
Proporcionar datos SQL reales verificables cuando inversores hacen preguntas de due diligence. Se activa automáticamente para preguntas con keywords de inversor, múltiples preguntas numeradas (3+), o preguntas largas (80+ palabras).

**Métricas Disponibles:**
| Métrica | Query | Propósito |
|---------|-------|-----------|
| Segmented Expectancy | BY hmm_regime, coherence_bucket | ¿DÓNDE gana el sistema? |
| Fee Breakdown | Kraken 0.26%, break-even | Impacto de comisiones |
| Pre/Post Hotfix | BY opened_at <> ADR-007 date | Efecto de calibración |
| Trade Size Analysis | BY size bucket | ADR-004 insights |
| Data Quality | BY telemetry_source | Transparencia REAL vs LEGACY |

**Triggers:**
- Keywords: "family office", "AUM", "seed", "due diligence", "expectancy", "fee breakdown"
- Estructura: 3+ preguntas numeradas
- Longitud: 80+ palabras

**Output:**
Texto Markdown formateado listo para inyección en prompt AI, incluyendo tablas y cálculos verificables.

**ADR:** `docs/reference/adr/ADR-013-investor-data-provider.md`

---

## Daily Report Service - Brutal Honesty Monitoring (Jan 9, 2026)

| Componente | Archivo | Función |
|------------|---------|---------|
| DailyReportService | `omnix_services/monitoring/daily_report_service.py` | Genera reportes diarios con métricas reales |
| DailyMetrics | `daily_report_service.py` | Dataclass con métricas del día |
| paper_trading_daily_reports | PostgreSQL | Historial de reportes para auditoría |

**Propósito:**
Sistema de monitoreo diario con honestidad brutal durante el período de recalibración (30 días). Conecta con PostgreSQL para métricas REALES y trackea progreso hacia objetivos.

**Métricas Monitoreadas:**
| Métrica | Target | Fuente |
|---------|--------|--------|
| Win Rate | > 35% | `paper_trading_balances` |
| ROI | > +2% | Calculado |
| Sharpe Ratio | > 0.5 | Estimado |
| Max Drawdown | < 3% | Calculado |
| Learning Cost | < $20K | P&L negativo |

**Kelly Criterion Honesto:**
- Kelly > 0: Operación matemáticamente favorable
- Kelly < 0: "Modo Aprendizaje" - pérdidas = inversión en I+D con presupuesto limitado

**Integración:**
- Telegram: `/reporte_diario`
- Cron: `scripts/operations/run_daily_report.sh` (00:05 UTC)
- ADR: `docs/reference/adr/ADR-001-brutal-honesty-monitoring.md`

---

## Performance Honesty Guard (Jan 3-4, 2026)

| Componente | Archivo | Función |
|------------|---------|---------|
| PerformanceHonestyGuard | `omnix_services/ai_service/honesty_guard.py` | Evalúa métricas y genera contexto por fases |
| detect_performance_intent() | `honesty_guard.py` | Detecta si usuario pregunta sobre rendimiento |
| determine_phase() | `honesty_guard.py` | Determina fase actual (phase1_early/progress/ready, phase2) |
| generate_prompt_injection() | `honesty_guard.py` | Texto para inyectar en prompts AI |

**Estrategia de 2 Fases:**
- **Fase 1 (Anti-Pérdida)**: Sistema aprende a NO perder. Pérdidas = datos de entrenamiento.
- **Fase 2 (Optimización)**: Una vez que evita pérdidas, se optimiza para ganar.

**Comportamiento:**
- En conversación normal: Bot se comporta igual que antes
- Cuando preguntan sobre métricas/rendimiento: Activa contexto honesto sin drama

**Fases del Sistema:**
| Fase | Profit Factor | Win Rate | Descripción |
|------|---------------|----------|-------------|
| phase1_early | < 0.5 | < 25% | Identificando patrones de pérdida |
| phase1_progress | 0.5-0.8 | 25-35% | Documentando y bloqueando pérdidas |
| phase1_ready | > 0.8 | > 35% | Cerca de transición a Fase 2 |
| phase2 | > 0.8 | > 35% + 200 trades | Optimización de ganancias |

**Criterios de Transición Fase 1 → Fase 2:**
- Mínimo 200 trades
- Profit Factor >= 0.8
- Win Rate >= 35%

**Detección de Intención:** Patrones regex como "profit factor", "como vamos", "win rate", "funciona", "track record"

**Flujo de Integración:**
```
Usuario envía mensaje
    ↓
detect_performance_intent(user_message) ← ¿Pregunta sobre rendimiento?
    ↓
SI: HonestyGuard consulta métricas de BD (paper_trading_trades)
    ↓
determine_phase() → phase1_early/progress/ready o phase2
    ↓
Inyecta CONTEXTUAL_STATEMENTS (datos + contexto de fase)
    ↓
NO: Comportamiento normal del bot
```

**Mínimo de Trades:** 50 trades antes de aplicar juicio (insufficient_data si < 50)

---

## Voice Service Async Architecture (V007 - Jan 4, 2026)

| Componente | Archivo | Función |
|------------|---------|---------|
| VoiceEngine | `omnix_services/voice_service/voice_controller.py` | Adapter para gTTS/ElevenLabs |
| schedule_voice_response | `voice_controller.py` | Programa voz con logging estructurado |
| _process_and_send_voice_safe | `voice_controller.py` | Wrapper seguro que captura excepciones |
| _process_and_send_voice | `voice_controller.py` | Genera y envía audio (interno) |

**Mejoras V007 (Jan 4, 2026)**:
- Voz habilitada para TODOS los usuarios (sin restricción por plan)
- Logging estructurado con chat_id/user_id en cada paso
- Retry con backoff para gTTS (3 intentos)
- Captura completa de errores en hilos daemon
- Wrapper `_process_and_send_voice_safe` para evitar errores silenciosos

**Flujo V007 (Texto-primero, Voz-después)**:
```
Usuario envía mensaje
    ↓
Bot procesa y genera respuesta texto
    ↓
Texto enviado inmediatamente a Telegram ← Usuario ve respuesta rápido
    ↓
schedule_voice_response() verifica condiciones
    ↓
SI texto < 20 chars → LOG "SALTADO: Texto muy corto"
    ↓
SI VoiceEngine no activo → LOG "SALTADO: VoiceEngine no activo"
    ↓
Lanza hilo daemon con wrapper seguro
    ↓
_process_and_send_voice_safe() → Captura TODAS las excepciones
    ↓
Hilo: limpieza texto → detección idioma → gTTS (con retry) → envío Telegram
    ↓
LOG: "✅ Voz enviada exitosamente" o "❌ Error detallado"
```

**Retry en gTTS (V007)**:
```python
def text_to_speech(self, text, language='es', max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            tts = gTTS(text=text, lang=language, slow=False)
            tts.save(temp_path)
            return temp_path
        except Exception as e:
            if attempt < max_retries:
                backoff = attempt * 2  # 2s, 4s
                time.sleep(backoff)
            else:
                return None
```

**Limpieza de Texto para TTS**:
- Números de lista: `*1.` → "Punto uno, "
- Asteriscos: `*Título*` → "Título" (preserva contenido)
- Flechas: `→` → ", " (pausa natural)
- Emojis: Removidos completamente

---

## Adaptive Coherence Gate V6.5.4e (ADR-007 Calibrated)

| Componente | Archivo | Función |
|------------|---------|---------|
| AdaptiveGateDecision | `coherence_engine.py` | DTO con decisión de veto + thresholds |
| evaluate_pre_scoring_gate() | `coherence_engine.py` | API pública para evaluar gate |
| _calculate_adaptive_threshold() | `coherence_engine.py` | Helper interno para calcular umbrales |

**Arquitectura Centralizada:**

El Adaptive Gate centraliza toda la lógica de thresholds en CoherenceEngine (servicio de dominio), alineándose con la arquitectura hexagonal V7.0. El bot delega la decisión al CoherenceEngine en lugar de usar valores hardcodeados del perfil.

**Flujo de Decisión:**
```
AutoTradingBot._make_v52_decision()
    ↓
Construye strategy_signals + adaptive_gate_data
    ↓
coherence_engine.evaluate_pre_scoring_gate(signals, data, paper_mode)
    ↓
_calculate_adaptive_threshold() calcula block/warn thresholds
    ↓
Retorna AdaptiveGateDecision DTO
    ↓
Bot usa should_block para decidir early return
```

**AdaptiveGateDecision DTO:**
```python
@dataclass
class AdaptiveGateDecision:
    should_block: bool              # True = block trade
    veto_type: Optional[str]        # COHERENCE_GATE_CRITICAL o COHERENCE_GATE_LOW
    coherence_score: float          # Score actual (0-100)
    block_threshold: float          # Threshold usado para bloqueo
    warn_threshold: float           # Threshold para warning
    adaptive_gate_active: bool      # Si se usaron thresholds adaptativos
    ema_score: Optional[float]      # EMA score que activó el gate
    black_swan_severity: Optional[str]  # Nivel de Black Swan
    reason: str                     # Explicación legible
    gate_info: Dict                 # Info diagnóstica completa
```

**Matriz de Umbrales Adaptativos:**

| EMA Score | Black Swan | Block Threshold | Lógica |
|-----------|------------|-----------------|--------|
| ≥ 25 pts | LOW | 35% | Señal fuerte + bajo riesgo → más permisivo |
| ≥ 25 pts | MEDIUM | 45% | Señal fuerte + riesgo medio → moderado |
| ≥ 25 pts | HIGH | 55% | Señal fuerte + alto riesgo → estricto |
| ≥ 25 pts | EXTREME | 65% | Señal fuerte + riesgo extremo → muy estricto |
| < 25 pts | cualquiera | 10%/30% | Default (paper/real) |

**EMA Score Buckets:**
| EMA Confidence | Score (pts) |
|----------------|-------------|
| ≥ 70% | 40 pts (strong) |
| ≥ 50% | 25 pts (moderate) |
| > 0% | 12 pts (weak) |
| 0% | 0 pts (none) |

**Logging Estructurado:**
```json
{
  "event": "ADAPTIVE_GATE_DECISION",
  "should_block": false,
  "veto_type": null,
  "coherence_score": 60.8,
  "block_threshold": 35,
  "adaptive_gate_active": true,
  "ema_score": 25,
  "black_swan_severity": "LOW",
  "paper_mode": true
}
```

**Investor-Facing Language:**
> "OMNIX calibra dinámicamente sus filtros de coherencia según la severidad del régimen de mercado, maximizando capturas en condiciones favorables mientras mantiene disciplina institucional."

---

## 1. Core Trading Engines

| Módulo | Ubicación | Propósito |
|--------|-----------|-----------|
| AutoTradingBot V6.5.4e | `omnix_core/bot/auto_trading_bot.py` | Scanner multi-crypto, señales tiered, emergency SL |
| TradingSystem V6.5 | `omnix_core/trading_system.py` | Orquestador de ejecución |
| CoherenceEngine V6.5.4e | `omnix_services/coherence_service/coherence_engine.py` | 6-tier veto, FAIL-CLOSED, type-safe + ADR-007 calibrated |
| **SignalIntegrityValidator** | `omnix_core/data/signal_integrity_validator.py` | **Checkpoint 0 (SIV, ADR-033)** — data quality gate before analysis (Mar 2026) |
| TemporalCoherenceValidator | `omnix_core/temporal/coherence_validator.py` | **Checkpoint 7 (TCV, ADR-032)** — backward trajectory consistency gate (Mar 2026) |
| **ForwardTrajectoryImplicator** | `omnix_core/temporal/forward_trajectory.py` | **Checkpoint 7b (FTI, ADR-034)** — forward implication gate (Mar 2026) |
| **RegimeConditionedKelly** | `omnix_core/sizing/regime_conditioned_kelly.py` | **ADR-035** — regime-segmented Kelly inputs with 3-level fallback (Mar 2026) |
| **ExitGovernanceEngine** | `omnix_core/governance/exit_governance.py` | **ADR-036** — 3-gate exit pipeline + PQC-signed receipts (Mar 2026) |
| **ExecutionBoundaryIntegrityProtocol** | `omnix_services/governance_service/execution_integrity.py` | **ADR-045** — 4-component pre/post-evaluation integrity layer (Mar 2026) |
| **ShariaGate** | `omnix_core/governance/sharia_gate.py` | **CP-6 (ADR-046)** — Islamic finance compliance gate: halal/haram, gharar, debt ratio (Mar 2026) |
| **AMLGate** | `omnix_core/governance/aml_gate.py` | **CP-9 (ADR-047)** — Anti-Money Laundering gate: privacy coins, volume, structuring (Mar 2026) |
| **FraudGate** | `omnix_core/governance/fraud_gate.py` | **CP-10 (ADR-048)** — Fraud/manipulation detection: DCI, signal divergence, reversals (Mar 2026) |
| **JurisdictionGate** | `omnix_core/governance/jurisdiction_gate.py` | **CP-11 (ADR-049)** — Jurisdictional compliance: UAE/EU/US/GCC asset & operation rules (Mar 2026) |
| Non-Markovian Kernel | `omnix_core/strategies/non_markovian_kernel.py` | Memoria temporal |
| Risk Guardian V5.4 | `omnix_services/monitoring/risk_guardian.py` | Protección overtrading |

> **CoherenceEngine Type Safety (Dec 30, 2025)**: Incluye `normalize_signal()`, `normalize_strategy_signal()` y `safe_float()` para prevenir errores `str vs int`. Ver [TYPE_SAFETY_HOTFIX_DEC30_2025.md](../history/2025-12/TYPE_SAFETY_HOTFIX_DEC30_2025.md).

> **Adaptive Coherence Gate V6.5.4e (ADR-007)**: Sistema de umbrales dinámicos calibrados: LOW 30%, MEDIUM 40%, HIGH 50%, EXTREME 60%, EMA trigger 20 pts. Ver sección "Adaptive Coherence Gate" más arriba.

---

## 2. Estrategias de Señales

| Estrategia | Ubicación | Tipo |
|------------|-----------|------|
| QuantumMomentum | `omnix_services/trading_service/quantum_momentum.py` | Direccional primario |
| Monte Carlo | `omnix_services/trading_service/monte_carlo.py` | Validación probabilística |
| Kelly Criterion | `omnix_services/trading_service/kelly_criterion.py` | Position sizing |
| Black Swan | `omnix_services/trading_service/black_swan.py` | Veto (riesgo extremo) |
| HMM Regime | `omnix_services/trading_service/hmm_regime.py` | Contexto de mercado |
| Kalman Filter | `omnix_services/trading_service/kalman_filter.py` | Reducción de ruido |

---

## 3. Hexagonal Ports

> **NOTA**: Todos los ports V7.0 están implementados pero NO activos en producción.
> El sistema opera 100% con código legacy. Ver [REAL_SYSTEM_STATUS.md](../REAL_SYSTEM_STATUS.md).

### Driven Ports (Salida) - 0/15 Activos

| Port | Adapter | Estado |
|------|---------|--------|
| TradingPort | KrakenAdapter | ⬜ No activo (legacy en uso) |
| MarketDataPort | KrakenAdapter | ⬜ No activo (legacy en uso) |
| AIInferencePort | GeminiAdapter | ⬜ No activo (legacy en uso) |
| DatabasePort | DatabaseAdapter | ⬜ No activo |
| CachePort | CacheAdapter | ⬜ No activo |
| NotificationPort | NotificationAdapter | ⬜ No activo |

### Driver Ports (Entrada) - 1/2 Activos

| Port | Adapter | Estado |
|------|---------|--------|
| TelegramPort | TelegramBotAdapter | ✅ **ACTIVO** — `run_polling()` delega a `enterprise_bot.start_polling()` (fix 15-Apr-2026: todos los handlers registrados antes del inicio del polling) |
| RestApiPort | Flask Blueprints | ⬜ No activo |

Ver [REAL_SYSTEM_STATUS.md](../REAL_SYSTEM_STATUS.md) para estado real de producción.

---

## 4. Servicios

### Servicios Principales (24 paquetes)

| Servicio | Ubicación | Propósito |
|----------|-----------|-----------|
| TradingService | `omnix_services/trading_service/` | Estrategias y órdenes |
| AIService | `omnix_services/ai_service/` | IA conversacional (SOLID) |
| DatabaseService | `omnix_services/database_service/` | Gateway PostgreSQL |
| TelegramService | `omnix_services/telegram_service/` | Bot interface |
| CoherenceService | `omnix_services/coherence_service/` | 6-tier veto |
| ExecutionService | `omnix_services/execution_service/` | Protocolo institucional |
| MonitoringService | `omnix_services/monitoring/` | Risk Guardian |
| AdaptiveEngine | `omnix_services/adaptive_engine/` | Auto-calibración |

---

## 5. Data Layer

### PostgreSQL (43+ tablas)

| Categoría | Tablas | FK Coverage |
|-----------|--------|-------------|
| Core User | 4 | 100% |
| Trading | 5 | 100% |
| Risk Management | 8 | 100% |
| Derivatives | 6 | 100% |
| Community | 5 | 100% |
| Snapshots/Analytics | 6 | 100% |
| System | 8 | N/A |
| B2B Governance | 3 (`b2b_clients`, `decision_receipts`, `client_thresholds`) | 100% |

**`client_thresholds`** (added Mar 11, 2026 — ADR-037): stores per-client checkpoint threshold overrides. Row-per-checkpoint design with `UNIQUE(client_id, checkpoint_id)`, CHECK constraints 0–100, and `ON DELETE CASCADE` to `b2b_clients`.

### Redis Cache

| Namespace | TTL | Propósito |
|-----------|-----|-----------|
| `market:` | 60s | Precios |
| `user:` | 5min | Estado usuario |
| `conv:` | 1hr | Conversaciones |
| `omnix:heartbeat:trading_loop` | 10min | Liveness monitoring |
| `omnix:user_language:{chat_id}` | 24hr | User language detection |

---

## 6. Event Bridge: UserSettings → AutoTradingBot

### Problema Resuelto (Historical: V6.5.4d Dec 2025)
Antes de V6.5.4d, los comandos `/pausar` y `/reanudar` solo actualizaban la DB pero NO notificaban al `AutoTradingBot`. Esto causaba que el trading no se reiniciara hasta el próximo redeploy de Railway.

### Arquitectura de Integración Completa

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    FLUJO COMPLETO DE TRADING V6.5.4e                      │
└──────────────────────────────────────────────────────────────────────────┘

         CAPA DE INTERFAZ                    CAPA DE CONTROL
    ┌─────────────────────┐            ┌─────────────────────────┐
    │   Telegram Bot      │───────────▶│   UserSettingsService   │
    │  (enterprise_bot)   │            │   (user_settings_svc)   │
    └─────────────────────┘            └───────────┬─────────────┘
              │                                    │
              │ /pausar, /reanudar                 │ PostgreSQL
              │                                    │ is_paused = true/false
              ▼                                    ▼
    ┌─────────────────────────────────────────────────────────────┐
    │              🔗 EVENT BRIDGE                                 │
    │  enterprise_bot.py:                                          │
    │  ├── Detecta comando /pausar o /reanudar                    │
    │  ├── Llama UserSettingsService (persistencia DB)            │
    │  └── Llama AutoTradingBot.start() o .stop() (ejecución)     │
    └─────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
    ┌─────────────────────────────────────────────────────────────┐
    │              CAPA DE EJECUCIÓN DE TRADING                    │
    │  AutoTradingBot V6.5.4e:                                     │
    │  ├── _start_stop_lock (threading.Lock)                      │
    │  ├── _thread (referencia al Thread activo)                  │
    │  ├── start() → Inicia _trading_loop en Thread               │
    │  ├── stop() → Detiene loop, join(timeout=5s)                │
    │  └── _write_heartbeat() → Redis cada 5 min                  │
    └─────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                 TRADING LOOP (_trading_loop)                 │
    │  Ciclo cada 25 segundos:                                     │
    │  1. Verificar emergency_stop                                 │
    │  2. Heartbeat cada 12 ciclos (~5min) → Redis                │
    │  3. Rotar par (BTC→ETH→SOL...)                              │
    │  4. _analyze_market() → 10 estrategias                      │
    │  5. _make_v52_decision():                                    │
    │     ├── [CP-0]  SIV → data integrity (ADR-033)              │
    │     ├── [CP-1]  Monte Carlo VETO → probabilistic gate       │
    │     ├── [CP-2]  RMS VETO → risk management                  │
    │     ├── [CP-3]  VETO Early Return                           │
    │     ├── [CP-4]  Coherence Engine → 6-tier veto              │
    │     ├── [CP-5]  Adaptive Coherence Gate (ADR-007)           │
    │     ├── [CP-6]  Sharia Governance Gate (ADR-046) [opt-in]   │
    │     ├── [CP-7]  TCV → backward trajectory (ADR-032)         │
    │     ├── [CP-7b] FTI → forward implication (ADR-034)         │
    │     ├── [CP-8]  ECW Gate → edge persistence (ADR-019)       │
    │     └── [SCORE] Weighted scoring → final decision           │
    │  6. _execute_smart_trade() → Paper o Real                   │
    │  7. _check_open_positions_tp_sl():                          │
    │     └── EGL → 3-gate exit governance (ADR-036)              │
    └─────────────────────────────────────────────────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
    ┌────────────────┐  ┌────────────────────┐  ┌────────────────────┐
    │   PostgreSQL   │  │      Redis         │  │    Kraken API      │
    │ - user_settings│  │ - heartbeat        │  │ - precios          │
    │ - paper_trades │  │ - cache            │  │ - órdenes          │
    │ - balance_hist │  │ - user_language    │  │ - historial        │
    └────────────────┘  └────────────────────┘  └────────────────────┘
```

> **Nota de numeración CP-X**: Los números de checkpoint reflejan el orden de introducción
> arquitectural (por ADR), no posición secuencial. CP-7 fue el séptimo gate introducido
> (ADR-032, TCV, Mar 2026). CP-0 (SIV, ADR-033) fue insertado al frente del pipeline
> posteriormente. CP-6 fue asignado en Mar 2026 al **Sharia Governance Gate** (ADR-046)
> — posicionado entre CP-5 (Adaptive Coherence Gate) y CP-7 (TCV). Habilitado por variable
> de entorno `SHARIA_GATE_ENABLED`. Por defecto deshabilitado (pass-through) para todos
> los clientes existentes. El pipeline de checkpoints CP-0 a CP-8 ahora está completo.

### Flujo del Event Bridge

```
Usuario: /reanudar
    │
    ▼
enterprise_bot.py (línea 3069-3084)
    │
    ├── UserSettingsService.resume_trading()
    │       └── PostgreSQL: is_paused = false ✓
    │
    └── 🔗 EVENT BRIDGE
            │
            └── AutoTradingBot.start(user_id)  ← Reinicia loop en caliente
                    │
                    └── Thread: _trading_loop() activo inmediatamente
```

### Thread Safety

Para prevenir race conditions cuando el usuario ejecuta `/pausar` y `/reanudar` rápidamente:

| Componente | Ubicación | Propósito |
|------------|-----------|-----------|
| `_start_stop_lock` | `auto_trading_bot.py:490` | Lock exclusivo para start()/stop() |
| `_thread` | `auto_trading_bot.py:491` | Referencia al Thread del trading loop |

**Validaciones en start()**:
1. Adquirir `_start_stop_lock` (context manager)
2. Verificar `self.state['running'] == False`
3. Verificar `self._thread is None or not self._thread.is_alive()`
4. Si ambas pasan, crear nuevo Thread y ejecutar

**Validaciones en stop()**:
1. Adquirir `_start_stop_lock`
2. Setear `self.state['running'] = False`
3. `self._thread.join(timeout=5.0)` - esperar terminación
4. Log warning si el thread no termina en 5 segundos

### Heartbeat Monitoring

| Componente | Clave Redis | Intervalo | TTL |
|------------|-------------|-----------|-----|
| Trading Loop | `omnix:heartbeat:trading_loop` | 12 ciclos (~5min) | 10min |

**Datos del heartbeat**:
```json
{
  "timestamp": "2025-12-20T06:45:00Z",
  "cycle": 120,
  "running": true,
  "total_trades": 45,
  "paper_mode": true
}
```

**Monitoreo**: Si la clave expira (TTL 10min), el loop está muerto.

### Dependencias entre Componentes

| Componente Origen | Depende De | Tipo de Dependencia |
|-------------------|------------|---------------------|
| enterprise_bot.py | UserSettingsService | Persistencia de estado |
| enterprise_bot.py | AutoTradingBot | Ejecución de trading |
| AutoTradingBot.start() | Redis (cache.py) | Heartbeat write |
| AutoTradingBot._trading_loop() | 10 Estrategias | Señales de trading |
| _trading_loop() | CoherenceEngine | Validación 6-tier |
| _trading_loop() | PaperTradingManager | Ejecución paper trades |
| UserSettingsService | PostgreSQL | Estado is_paused |

---

## 7. Cambios Históricos (V6.5.4d - Dec 2025)

| Parámetro | Valor | Efecto |
|-----------|-------|--------|
| EMERGENCY_SL_PCT | 2% | Max loss por posición |
| score_moderate | 12 | Solo STRONG/VERY_STRONG |
| ADA/USD | EXCLUDED | 0% win rate |
| Kalman BEARISH | -15 pts | Veto macro trend |

---

## 8. APIs Externas

| API | Servicio | Rate Limit |
|-----|----------|------------|
| Kraken REST | market_data | 15 req/min |
| Kraken WS | market_data | Streaming |
| Gemini 2.0 | ai_service | 60 RPM |
| Finnhub | market_intelligence | 60 req/min |
| Alpha Vantage | market_intelligence | 5 req/min |
| Tavily | web_search | Per API key |

---

## 9. Dominios Funcionales

El sistema se organiza en 11 dominios funcionales:

| # | Dominio | Estado | Paquetes |
|---|---------|--------|----------|
| 1 | Trading Signal Fabric | CORE | trading_service, coherence_service |
| 2 | Market & Data Ingestion | CORE | market_data, market_intelligence |
| 3 | Execution & Brokerage | CORE | execution_service, trading_system |
| 4 | Risk & Protection | CORE | risk_management, monitoring |
| 5 | AI & Communication | CORE | ai_service, web_search_service |
| 6 | User Interfaces | INTERFACE | telegram_service, dashboard |
| 7 | Persistence & Analytics | INFRA | database_service, cache |
| 8 | Security & Quantum | CORE | security, quantum |
| 9 | Portfolio Optimization | SUPPORT | portfolio_management |
| 10 | B2C SaaS | STRATEGIC | omnix_api, user_settings |
| 11 | Legacy/Dormant | LEGACY | alerts, concurrency |

Ver [Mapa Funcional Completo](COMPLETE_FUNCTIONALITY_MAP.md) para detalles de cada dominio.

---

## 10. AI-First Multilingual Prompt Architecture (Dec 19, 2025)

### Prompt Specification Layer V6.5.4e

Modern prompt engineering architecture with language-neutral base prompts:

```
┌─────────────────────────────────────────────────────────────────┐
│  PROMPT SPECIFICATION LAYER                                      │
├─────────────────────────────────────────────────────────────────┤
│  Master Template (prompt_templates.py)                           │
│  ├── Role Definition (English-neutral)                          │
│  ├── Mission Statement                                           │
│  ├── Language Policy [CRITICAL]                                 │
│  ├── Core Capabilities                                          │
│  └── Output Format Guidelines                                   │
├─────────────────────────────────────────────────────────────────┤
│  Language Context Manager                                        │
│  ├── langdetect integration                                     │
│  ├── Dynamic language directive injection                       │
│  └── Fallback handling                                          │
├─────────────────────────────────────────────────────────────────┤
│  Chain-of-Thought Framework                                      │
│  └── Analysis steps for complex queries                         │
└─────────────────────────────────────────────────────────────────┘
```

| Component | Purpose | File |
|-----------|---------|------|
| Master Template | Language-neutral base prompt | prompt_templates.py |
| LanguageContextManager | Detects user language, injects directives | prompt_templates.py |
| PromptBuilder | Assembles complete prompts | prompt_templates.py |
| CoT Framework | Chain-of-Thought for analytical queries | ai_models.py |

**Key Principles:**
- All system prompts written in English (language-neutral)
- Language Policy section with explicit rules: "ALWAYS respond in the SAME language the user writes"
- Dynamic language detection via `langdetect` library
- `language_code='auto'` as DB default
- `trading_terms` dictionaries for intent detection only (not language restriction)
- TTS audio generated in detected response language

---

## MOD-014: Unified Decision Control Layer — ADR-138 (May 6, 2026)

Capa de orquestación B2B que coordina todos los pilares de gobernanza en secuencia estricta.
Fail-closed: cualquier pilar obligatorio no-advisory que falle → BLOCKED.
Retorna `ControlReceipt` con visibilidad por pilar, latency breakdown y sello SHA-256 tamper-evident.

```
POST /api/governance/control/evaluate
    │
    ├── [Layer 0]   SAE  — Structural Admissibility Engine        ADR-092
    ├── [Layer 0b]  SPG  — State Provenance Guard [advisory]      ADR-133
    ├── [Layer 0c]  CBG  — Conditional Bind Gate [opt-in]         ADR-135
    ├── [Layer 1-2] CP   — 11-Checkpoint Pipeline + TIE           ADR-028/053
    └── [Layer 3]   PQC  — Cryptographic Receipt (Dilithium-3)    ADR-096
```

| Componente | Clase / Archivo | Función |
|------------|-----------------|---------|
| **UnifiedDecisionControlLayer** | `omnix_core/governance/unified_control_layer.py` | Orquestador — 5 pillars en secuencia |
| **PillarResult** | `unified_control_layer.py` | DTO por pilar: passed, advisory, latency_ms, detail |
| **ControlReceipt** | `unified_control_layer.py` | Resultado final: control_id, decision, blocking_pillar, control_hash |
| **UDCL API** | `omnix_web/api/gov_blueprint.py` | 5 endpoints /control/\* |
| **udcl_control_receipts** | PostgreSQL | Tabla audit trail (creada lazy, 3 índices) |

**Endpoints:**

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET  | `/api/governance/control/schema`                 | Público  | Catálogo de pilares, invariants, schema |
| GET  | `/api/governance/control/health`                 | Cliente  | Estado en tiempo real de cada pilar |
| POST | `/api/governance/control/evaluate`               | Cliente  | Evaluación multi-pilar completa |
| GET  | `/api/governance/control/receipts/<control_id>`  | Cliente  | Fetch receipt por ID |
| GET  | `/api/governance/control/receipts`               | Cliente  | Lista paginada de receipts del cliente |

**ControlReceipt fields:**
- `control_id`: UDCL-{16 hex} — identificador único de la evaluación
- `blocking_pillar`: nombre del primer pilar que bloqueó, o null
- `control_hash`: SHA-256 de `control_id + decision + pillar outcomes` (tamper-evident)
- `pillar_latency_ms`: desglose de latencia por pilar

**Invariants de diseño:**
- Todos los resultados por pilar se retornan incluso en BLOCKED — transparencia total
- SPG (Layer 0b) es advisory — AMBIGUOUS avisa pero no bloquea solo
- CBG (Layer 0c) es opt-in — activar con `cbg_enabled=true` en el body
- PQC receipt se genera para TODAS las decisiones, incluyendo BLOCKED
- Exception en pilar mandatorio → BLOCKED con `blocking_pillar="system_error"`

---

## Execution Boundary Integrity Protocol — ADR-045 (Mar 24, 2026)

Capa de 4 componentes que opera en la frontera de ejecución del pipeline de gobernanza.

| Componente | Clase | Función |
|------------|-------|---------|
| **ACV** | `AdmissibilityConsistencyValidator` | Detecta señales internamente contradictorias antes de que corran los checkpoints |
| **ECP** | `ExecutionCommitmentProtocol` | Commitment criptográfico a los criterios ANTES de evaluar — prueba que los criterios no cambiaron |
| **NPM** | `NavigationPatternMonitor` | Monitorea distribución de decisiones — detecta concentración y path-dependency |
| **CP** | `ConcentrationPredictor` | Predice riesgo de concentración ANTES de que emerja |

**Tablas DB**: `navigation_patterns`, `admissibility_violations`  
**API**: `GET /api/governance/execution-integrity` (sin auth — lectura pública)  
**Ubicación**: `omnix_services/governance_service/execution_integrity.py`  

**Diseño fail-safe**: EBIP falla de forma silenciosa — nunca bloquea el pipeline principal.

---

## Auto-Modification Guard — ADR-144 (May 8, 2026)

Capa de meta-gobernanza obligatoria que envuelve **toda** modificación automática de umbrales AVM.

### Problema que resuelve

ADR-118 y ADR-120 introdujeron auto-remediación y auto-recalibración. Sin control, esto crea tres riesgos:

| Riesgo | Descripción |
|---|---|
| Deriva cumulativa silenciosa | Cambios del +10% compuestos 10 veces → +159% respecto al baseline original |
| Bucle MCM→MCM | MCM detecta BLOCK_RATE_COLLAPSE → tightening → más bloqueos → MCM detecta de nuevo |
| Confianza degradada sin aviso | Contrapartes reciben receipts producidos bajo umbrales auto-modificados sin saberlo |

### Los 6 invariantes (omnix_core/governance/auto_modification_guard.py)

| # | Invariant | Variable de entorno | Default |
|---|---|---|---|
| 1 | **Cap de deriva cumulativa** desde genesis | `AVM_MAX_CUMULATIVE_DRIFT_PCT` | 30% |
| 2 | **Rollback automático** si performance degradó en T+24h | `AVM_ROLLBACK_WINDOW_HOURS` | 24h |
| 3 | **Signed diff proof** SHA-256 + Dilithium-3 opcional | — | siempre activo |
| 4 | **Approval gate**: delta > 10% requiere aprobación humana por Telegram | `AVM_APPROVAL_THRESHOLD_PCT` | 10% |
| 5 | **AUTO_MODIFIED trust flag** en todos los receipts post-modificación | — | siempre activo |
| 6 | **Anti-loop guard**: bloquea MCM→MCM si ≥2 remediaciones en 24h | `AVM_ANTI_LOOP_WINDOW_HOURS` | 24h |

### Tabla de base de datos

```
avm_modification_registry
  ├── modification_id    — AMG-{DOMAIN}-{8hex} (índice único)
  ├── thresholds_before  — JSONB snapshot pre-cambio
  ├── thresholds_after   — JSONB snapshot post-cambio
  ├── diff_proof         — AMG-DIFF-v1:{sha256}:{algo}
  ├── cumulative_drift_pct
  ├── status             — DEPLOYED | PENDING_APPROVAL | ROLLED_BACK | REJECTED
  └── performance_check_at — timestamp para verificación T+24h
```

### Flujo de llamadas

```
AVM Phase 3 optimización
    → deploy_optimized_thresholds()
        → AMG.run_guard()                   # 6 safeguards
            → avm_modification_registry     # registro permanente
            → Telegram (si approval needed)
        → _apply_thresholds_to_snapshot()   # solo si AMG aprueba

MCM auto_remediate() TIGHTEN
    → AMG.is_auto_loop()                    # anti-loop primero
    → deploy_optimized_thresholds(source=MCM_AUTO_TIGHTEN)
        → AMG.run_guard()                   # mismos 6 safeguards
```

**Ubicación**: `omnix_core/governance/auto_modification_guard.py`  
**DB tabla**: `avm_modification_registry`  
**ADR**: ADR-144

---

## Validación Forense — AMG (Mayo 2026)

**Reporte completo**: `docs/FORENSIC_VALIDATION_REPORT.md` — FVR-AMG-2026-001

Auditoría de 7 puntos realizada post-implementación. Resultado: todos los puntos pasan. Se corrigieron 3 defectos.

### Resumen ejecutivo de hallazgos

| Punto | Descripción | Veredicto |
|---|---|---|
| P1 | `run_guard()` se ejecuta antes de todo write a `checkpoint_thresholds` | PASS |
| P2 | Sin rutas de bypass para modificación de thresholds | PASS (ver §4.1 para baseline recalib) |
| P3 | Lógica de rollback segura — conservadora en datos insuficientes | PASS |
| P4 | Trust flag `AUTO_MODIFIED_SNAPSHOT` aparece correctamente en receipts | PASS |
| P5 | Bucle MCM→recalib→MCM bloqueado en el 2° intento (24h) | PASS |
| P6 | DDLs Railway idempotentes, separados, en orden correcto | PASS (DEF-002 corregido) |
| P7 | Invariant report completo con garantías documentadas | PASS |

### Defectos encontrados y corregidos

**DEF-001 (HIGH)** — Env vars leídas en tiempo de importación del módulo:  
`AVM_AUTO_APPROVE`, `AVM_MAX_CUMULATIVE_DRIFT_PCT`, etc. eran constantes de módulo. Un override vía Railway o tests no tenía efecto hasta reiniciar el proceso.  
**Fix**: Reemplazadas por funciones accessor dinámicas `_auto_approve()`, `_approval_threshold_pct()`, etc. — se leen en cada llamada.

**DEF-002 (MEDIUM)** — DDL multi-sentencia en un solo `cur.execute()`:  
`AMG_REGISTRY_DDL` contenía `CREATE TABLE` + `CREATE INDEX` separados por `;`. psycopg2 puede omitir la segunda sentencia silenciosamente.  
**Fix**: Separados en `AMG_REGISTRY_DDL` e `AMG_INDEX_DDL`, ejecutados como dos llamadas independientes.

**DEF-003 (LOW)** — `auto_recalibrate_stale_domains()` sin documentación sobre por qué no pasa por AMG:  
Un auditor futuro podría reportarlo como bypass. Se añadió la sección `AMG SCOPE BOUNDARY (ADR-144 §4)` al docstring.

### Frontera de alcance del AMG

El AMG protege modificaciones de `checkpoint_thresholds`. No protege recalibraciones de `baseline_signals`, que tienen sus propios safeguards (cap 80%, intervalo 72h, guard de schema).

```
MODIFICACIÓN DE THRESHOLDS    → run_guard() OBLIGATORIO
  deploy_optimized_thresholds()
  MCM TIGHTEN

RECALIBRACIÓN DE BASELINE     → FUERA DEL ALCANCE AMG (por diseño)
  auto_recalibrate_stale_domains()
  MCM FORCE_AVM_RECALIBRATION
```

---

## Governance Replay Engine — ADR-145 (Mayo 2026)

Motor programático para reproducir eventos de crisis históricos a través del pipeline de gobernanza OMNIX. Produce receipts independientemente verificables en formato de producción idéntico.

**Propósito comercial**: *"OMNIX habría bloqueado FTX el 7 de noviembre 2022 en Checkpoint 6 (Counterparty Risk), con este receipt."* — respaldado por hash SHA-256 canónico y verificable en omnixquantum.net.

### Los Cinco Escenarios de Crisis

| # | Escenario | Período | Pérdida Total | Primer Bloque OMNIX | Checkpoint |
|---|---|---|---|---|---|
| 1 | Terra/LUNA Collapse | May 7–13 2022 | $60B | T-24h (May 10 00:00 UTC) | CP-4 |
| 2 | FTX Exchange Collapse | Nov 2–11 2022 | $8B+ | T-4d (Nov 7 2022) | CP-6 |
| 3 | Silicon Valley Bank | Mar 8–10 2023 | $20B | T-48h (Mar 8 16:00 UTC) | CP-2 |
| 4 | COVID Flash Crash | Mar 12–13 2020 | $93B crypto | T+0 peak (Mar 12 13:24 UTC) | CAG |
| 5 | OFAC Tornado Cash | Aug 8 2022 | $75K+ frozen | T+0 SDN feed (Aug 8 16:04 UTC) | CP-9 |

### Alineación con Documentos Forenses Existentes

| Documento existente | Escenario | Relación |
|---|---|---|
| `docs/business/investor/TECHNICAL_VALIDATION_LUNA_2022.md` | CRISIS-001 | Timestamps y veredictos alineados |
| `docs/business/pdf/OMNIX_Forensic_FTX_November2022.pdf` | CRISIS-002 | SIV=14.2, Coherence=11.8, TCV=9.4 alineados |
| `docs/business/pdf/OMNIX_Forensic_SVB_March2023.pdf` | CRISIS-003 | 48h advance, CP-2 alineado |

El engine es la **fuente de verdad programática**. Los PDFs siguen siendo válidos para presentaciones.

### Arquitectura

```
omnix_core/simulation/
├── __init__.py              — API pública del módulo
├── crisis_scenarios.py      — CrisisScenario + SignalState (5 escenarios)
└── governance_replay.py     — GovernanceReplayEngine + clases de resultado

Flujo:
CrisisScenario → SignalState[]
    → GovernanceReplayEngine._evaluate()
        → SignedReplayReceipt (receipt_id + canonical_hash + pqc_note)
            → ScenarioReplayResult.to_markdown()
                → FullReplayReport.to_dict() | .to_markdown()
```

### Formato del Receipt de Replay

```python
{
  "receipt_id":           "OMNIX-RPL-{16hex}",    # determinístico por scenario+timestamp
  "scenario_id":          "CRISIS-002-FTX-2022",
  "timestamp_utc":        "2022-11-07T00:00:00Z",
  "verdict":              "BLOCKED",
  "blocking_checkpoint":  "CP-6",
  "trust_flags":          ["HARD_BLOCK", "CIRCULAR_COLLATERAL_CONFIRMED", ...],
  "canonical_hash":       "sha256:{64hex}",       # sella el payload completo
  "replay_mode":          true,                   # distingue de receipts de producción
  "pqc_note":             "Dilithium-3 (ML-DSA-65) — verify at omnixquantum.net"
}
```

### Verificación

```bash
# API pública (online)
curl https://omnixquantum.net/api/trust/verify \
  -d '{"receipt_id": "OMNIX-RPL-...", "mode": "replay"}'

# Herramienta standalone (offline)
python omnix_verify.py --receipt-id OMNIX-RPL-... --mode replay
```

**Ubicación**: `omnix_core/simulation/`  
**ADR**: ADR-145

---

## Runtime Authority Matrix — ADR-146 (Mayo 2026)

Define quién tiene autoridad final sobre cada acción de gobernanza en runtime. Responde explícitamente la pregunta de todo auditor institucional: *"¿Quién controla el sistema cuando el sistema se auto-modifica?"*

**Documento canónico**: `docs/AUTHORITY_MATRIX.md`

### Los Cuatro Niveles de Autoridad

```
TIER 1 — PLATFORM OWNER (Harold Nunes, OMNIX QUANTUM LTD)
  Autoridad final. El único que puede liberar freeze de emergencia BCE,
  modificar arquitectura (ADRs), o hacer override de cualquier decisión.

TIER 2 — SYSTEM AUTOMATED (Módulos de Gobernanza OMNIX)
  Autoridad pre-autorizada dentro de límites definidos por Tier 1.
  AVM · MCM · AMG · BCE · CAG · CBG · SPG · TIE · SBE · CTAG

TIER 3 — CLIENT OPERATOR (Clientes B2B Enterprise)
  API key + RBAC: READ / WRITE / ADMIN sobre sus propios recursos.

TIER 4 — EXTERNAL AUDITOR (Solo Lectura, Público)
  Verificación de receipts sin autenticación. Acceso permanente y abierto.
```

### Resumen de Autoridades Críticas

| Acción | Tier 1 | Tier 2 | ADR |
|---|---|---|---|
| Bloquear decisión de gobernanza | ✅ Override | ✅ **Autónomo** | ADR-116 |
| Emergency freeze (BCE activar) | ✅ Manual | ✅ Auto (compromiso detectado) | ADR-142 |
| **Liberar freeze BCE** | ✅ **Solo Tier 1** | ❌ | ADR-142 |
| Modificar thresholds ≤ 10% | ✅ | ✅ Auto + receipt | ADR-144 |
| Modificar thresholds > 10% | ✅ **Aprobación requerida** | 🔄 Gate → Tier 1 Telegram | ADR-144 |
| Cuarentena de dominio (48h) | ✅ Manual | ✅ CAG autónomo (vol > 150%) | ADR-050 |
| Rollback de thresholds | ✅ Manual en cualquier momento | ✅ Auto T+24h check | ADR-144 |
| Cambio arquitectural (nuevo ADR) | ✅ **Solo Tier 1** | ❌ | Todos los ADRs |
| Genesis snapshot | ✅ **Solo Tier 1** | ❌ **Inmutable** | ADR-144 |
| Receipts emitidos (contenido) | ❌ **Inmutable para todos** | ❌ **Inmutable** | ADR-096 |

### Protocolo de Emergencia (Resumen)

```
FREEZE:   BCE.activate_containment() → todas las decisiones BLOCKED
RELEASE:  BCE.release_containment(operator_id) — Solo Tier 1
ROLLBACK: AMG.check_rollback_condition() T+24h — o Tier 1 manual
OVERRIDE: Tier 1 únicamente — 0 overrides ejercidos en producción (Mayo 2026)
```

**Ubicación**: `docs/AUTHORITY_MATRIX.md`  
**ADR**: ADR-146

---

## Scope Authorization Record — ADR-147 (Mayo 2026)

Responde la pregunta del CAIO de Rehan Kausar: *"¿Fue el scope en sí mismo defensible?"*

Antes de ADR-147, OMNIX podía demostrar que una decisión individual fue gobernada correctamente, pero no podía demostrar que el *scope operacional* bajo el que funcionaba fue autorizado explícitamente, documentado, y no había derivado de sus condiciones originales. ADR-147 cierra este gap mediante un registro criptográficamente firmado que se emite en el momento de la autorización de scope.

**Documento canónico**: `omnix_core/governance/scope_authorization_engine.py`  
**Tabla**: `governance_scope_authorizations`

### Los 5 Componentes de Defensibilidad

Cada `ScopeAuthorizationRecord` embebe y sella criptográficamente los 5 componentes:

| Componente | Campo en Record | Qué responde |
|---|---|---|
| Qué está autorizado | `scope_definition` (JSONB) | Límites operacionales explícitos |
| Por qué es defensible | `defensibility_criteria` (JSONB) | Fundamento regulatorio y de negocio |
| Quién lo autorizó | `authorized_by` + `authority_tier` | Actor e identidad de autoridad |
| En qué contexto | `context_snapshot` + `context_hash` | Estado AVM en el momento de issuance |
| Prueba criptográfica | `scope_hash` + `pqc_signature` | Dilithium-3 (ML-DSA-65) + SHA-256 |

### Hashes Canónicos (Evidencia Real — Mayo 2026)

```
scope_hash     = sha256(json.dumps({"scope_definition": {...}, "defensibility_criteria": {...}},
                                   sort_keys=True, separators=(',',':')))
               = 0c6ee2e16947a1bce2775d2997eea5d05dc818c894184727045769d777813a3d

context_hash   = sha256(json.dumps(context_snapshot, sort_keys=True, separators=(',',':')))
               = 58721139dadc10755cd44e0b0c4ea75576b39744a5c804b72dc167514fd76b67

pqc_algorithm  = Dilithium-3 (ML-DSA-65)
sign_payload   = b"OMNIX-SAR-v1|scope_hash=<scope_hash>|context_hash=<context_hash>"
```

### Ciclo de Vida del Scope

```
issue_scope()
     │
     ▼
  ACTIVE ──── AVM drift check (cada governance cycle)
     │               │
     │        drift > threshold
     │               │
     ▼               ▼
REVOKED ←── REAPPROVAL_REQUIRED
                     │
              reauthorize()
                     │
                     ▼
               SUPERSEDED (old) → ACTIVE (nuevo scope)
```

### Detección de Deriva Contextual (Invariante 2)

```python
# AVM signal weights (ADR-076)
SIGNAL_WEIGHTS = {
    "probability_score":  0.25,
    "signal_coherence":   0.25,
    "risk_exposure":      0.20,
    "stress_resilience":  0.15,
    "trend_persistence":  0.10,
    "logic_consistency":  0.05,
}  # sum = 1.00

drift_pct = sum(
    weight * abs(current[s] - baseline[s]) / max(baseline[s], 0.01)
    for s, weight in SIGNAL_WEIGHTS.items()
) * 100  # en porcentaje

# Umbral por defecto: 25.0%
# Si drift_pct > threshold → status = REAPPROVAL_REQUIRED
# trust_flags().scope_reapproval_pending = True → no puede continuar silenciosamente
```

### API Endpoints (6 endpoints en gov_blueprint.py)

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| `POST` | `/api/governance/scope/authorize` | Admin (Tier 1) | Emitir nuevo scope PQC-firmado |
| `GET` | `/api/governance/scope/<domain>/active` | API key (Tier 3+) | Scope activo para el dominio/vertical |
| `GET` | `/api/governance/scope/<domain>/history` | Admin (Tier 1) | Historial completo inmutable del dominio |
| `POST` | `/api/governance/scope/<scope_id>/reauthorize` | Admin (Tier 1) | Nuevo scope que supersede al anterior |
| `POST` | `/api/governance/scope/<scope_id>/revoke` | Admin (Tier 1) | Revocar permanentemente (Tier 1 only) |
| `GET` | `/api/governance/scope/<scope_id>/drift` | API key (Tier 3+) | Calcular drift contextual AVM del scope |

### Los 6 Invariantes de Gobernanza (Validados — 124/124 tests)

| # | Invariante | Mecanismo |
|---|---|---|
| I-1 | Fail-Closed | `ValueError` antes de cualquier DB en inputs inválidos |
| I-2 | Bounded Adaptation | Drift ≥ 25% → REAPPROVAL_REQUIRED, no silencioso |
| I-3 | Authority Separation | `revoke_scope()` → `PermissionError` para Tier 2/3/4 |
| I-4 | Replay Determinism | `scope_hash` estable × 5 runs, hash idempotency PASS |
| I-5 | Signed Scope Defensibility | 5 componentes siempre presentes, SHA-256 hex 64 chars |
| I-6 | Anti-Drift Reapproval | `scope_reapproval_pending=True` bloquea continuación silenciosa |

### Validación Institucional (Mayo 2026)

```
Tests        : 124/124 PASS (tests/test_governance_integrity.py)
Dimensiones  : 9 (V-01 a V-09)
Evidencia    : docs/GOVERNANCE_INTEGRITY_REPORT.md
Run time     : 9.98s
Invariantes  : 6/6 VERIFIED
Hash idempotency : PASS (3 runs independientes)
PQC Signed   : Dilithium-3 (ML-DSA-65)
```

**Ubicación**: `omnix_core/governance/scope_authorization_engine.py`  
**ADR**: ADR-147

---

## Governance Monitoring Layer — ADR-129 · ADR-131 · ADR-142 · ADR-143 (Mayo 2026)

Cinco dashboards de auditoría con APIs reales respaldadas por tablas PostgreSQL. Todos los endpoints siguen el patrón de fail-open con fallback a array vacío — nunca devuelven 5xx al dashboard.

### Dashboards y Rutas API

| Dashboard | Ruta frontend | Endpoints Flask | ADR |
|---|---|---|---|
| Anomaly Response Engine | `/anomaly` | `GET /api/governance/anomaly/active` · `/summary` | ADR-129 |
| Breach Containment Engine | `/breach` | `GET /api/governance/breach/status` · `/history` | ADR-142 |
| Execution Integrity Layer | `/execution` | `GET /api/governance/execution/receipts` | ADR-131 |
| Multi-Domain Risk Governance | `/risk` | `GET /api/governance/risk/history` · `/summary` · `/catalog` | ADR-143 |
| Oscillation Insight Engine | `/oscillation` | `GET /api/analytics/oscillation` | ADR-134 |

### Tablas de Base de Datos

```sql
-- ADR-129: Anomaly Response Engine
anomaly_recommendations (
    rec_id TEXT PK, domain TEXT, action_code TEXT,
    severity TEXT, urgency TEXT, status TEXT,
    summary TEXT, detail TEXT,
    created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ, ack_at TIMESTAMPTZ, resolution_note TEXT
)

-- ADR-142: Breach Containment Engine
breach_events (
    event_id TEXT PK, status TEXT, trigger_code TEXT, severity TEXT,
    summary TEXT, triggered_by TEXT, released_by TEXT, release_note TEXT,
    triggered_at TIMESTAMPTZ, released_at TIMESTAMPTZ, is_active BOOLEAN
)

-- ADR-143: Multi-Domain Risk Governance
risk_assessments (
    assessment_id TEXT PK, subject TEXT, client_domain TEXT, decision TEXT,
    composite_score FLOAT, financial_score FLOAT, technical_score FLOAT,
    legal_score FLOAT, human_score FLOAT,
    hard_block_vector TEXT, assessed_by TEXT, assessed_at TIMESTAMPTZ
)

-- ADR-131: Execution Integrity Layer (shared with SDK write path)
execution_receipts (
    receipt_id TEXT PK, decision_receipt_id TEXT, order_id TEXT,
    asset TEXT, domain TEXT, direction TEXT, size_usd FLOAT,
    final_status TEXT, intent_captured_at TIMESTAMPTZ, filled_at TIMESTAMPTZ,
    fill_price_usd FLOAT, fill_pct FLOAT, slippage_bps FLOAT,
    rejection_code TEXT, rejection_detail TEXT,
    audit_trail JSONB, created_at TIMESTAMPTZ
)
```

Todas las tablas se crean con `CREATE TABLE IF NOT EXISTS` en el primer request — no requieren migración manual.

### Risk Vector Catalog (ADR-143)

```json
{
  "vectors":         ["financial", "technical", "legal", "human"],
  "default_weights": {"financial": 0.35, "technical": 0.25, "legal": 0.25, "human": 0.15},
  "thresholds":      {"blocked": 75, "review": 55, "hard_block_per_vector": 90},
  "decision_logic":  "BLOCKED if composite ≥ 75 or any single vector ≥ 90. REVIEW if composite ≥ 55."
}
```

### Breach Containment Invariant (ADR-142)

```
FREEZE:   breach_events INSERT + is_active = TRUE → todas las decisiones BLOCKED
RELEASE:  Solo Tier-1 (Harold Nunes). BCE.release_containment() requiere attestación humana.
HISTORY:  Inmutable — cada evento queda registrado con triggered_by + released_by.
```

---

## Variables de Entorno — Estado de Producción (Mayo 2026)

### Presentes en Railway ✓

`DATABASE_URL` · `REDIS_URL` · `GEMINI_API_KEY` · `TELEGRAM_BOT_TOKEN` · `OMNIX_WEB_URL` · `OPENAI_API_KEY` · `SESSION_SECRET` · `PAYLOAD_ENCRYPTION_KEY` · `FINNHUB_API_KEY` · `ALPHA_VANTAGE_API_KEY` · `KRAKEN_API_KEY` · `KRAKEN_API_SECRET` · `COINBASE_API_KEY` · `COINBASE_PASSPHRASE` · `COINBASE_SECRET` · `DASHBOARD_API_KEY` · `PAPER_MODE` · `TRADING_MODE` · `TRADING_PROFILE`

### Ausentes en Railway — Acción Requerida ⚠️

| Variable | Impacto | Acción |
|---|---|---|
| `OMNIX_SIGNING_SECRET_KEY_B64` | Receipts en producción sin firma PQC (Dilithium-3) | Copiar de Replit Secrets → Railway |
| `OMNIX_SIGNING_PUBLIC_KEY_B64` | Verificación PQC deshabilitada en producción | Copiar de Replit Secrets → Railway |
| `TELEGRAM_ADMIN_USER_ID` | Comandos admin del bot deshabilitados | Obtener via @userinfobot → añadir en Railway y Replit |

### Nombres Canónicos (importantes — confusión frecuente)

| Lo que se lee en el código | NO usar |
|---|---|
| `SESSION_SECRET` (Flask Dashboard) | ~~`SECRET_KEY`~~ |
| `PAYLOAD_ENCRYPTION_KEY` (Fernet webhooks) | ~~`WEBHOOK_ENCRYPTION_KEY`~~ |

---

## Trust Anchor Validation Layer — ETA-001 (Mayo 2026)

**Archivo central:** `omnix_core/evidence/trust_anchor.py`

Capa de validación de emisor que cierra el ataque de "keypair adversarial": un atacante genera su propio keypair Dilithium-3, firma un recibo falso con él, y el verificador anterior aceptaba la firma como válida. Con ETA-001, el verificador ahora distingue **quién firmó** del mero hecho de que la firma es matemáticamente válida.

### Cinco Códigos de Estado de Trust (Exhaustivos y Mutuamente Excluyentes)

| Código | Significado | `overall_valid` |
|---|---|---|
| `VALID_OMNIX_ISSUED` | Firma PQC válida + fingerprint de clave coincide con el anchor OMNIX | `True` |
| `VALID_SIGNATURE_UNTRUSTED_ISSUER` | Firma PQC válida matemáticamente, pero la clave NO es del anchor OMNIX | `False` |
| `INVALID_SIGNATURE` | Firma PQC presente pero matemáticamente inválida / recibo alterado | `False` |
| `UNKNOWN_KEY` | Firma presente pero no hay clave pública disponible | `False` |
| `DOWNGRADED_SHA_ONLY` | Sin firma PQC — solo integridad SHA-256 | `True` (solo si hash válido) |

### Fingerprint de Clave

```
fingerprint = SHA-256(base64decode(public_key_b64)).hexdigest()  # 64 hex chars
```

### Fuentes del Anchor de Confianza (prioridad descendente)

1. `OMNIX_TRUSTED_KEY_FINGERPRINT` env var (fingerprint hex pre-computado — máxima prioridad)
2. `OMNIX_SIGNING_PUBLIC_KEY_B64` env var (clave pública — fingerprint calculado en runtime)
3. Fetch desde `/.well-known/omnix-public-key.json` (opcional, red requerida)

### Puntos de Integración

| Módulo | Qué hace |
|---|---|
| `omnix_core/evidence/trust_anchor.py` | Registro central: `classify_receipt()`, `build_trust_anchor_block()`, `load_trusted_omnix_fingerprint()` |
| `omnix_core/evidence/verification_server.py` | Trust anchor en `_verify_receipt_crypto()` + badges en HTML |
| `omnix_web/api/server.py` | `_build_integrity_block()` + campo `public_key` en query DB + respuesta `/api/verify/receipt/{id}` |
| `omnix_web/api/omnix_engine/federated_trust.py` | Clasificación en `independent_verify()` |
| `omnix_web/public/omnix_verify.py` | CLI independiente con `--trusted-fingerprint` + sección TRUST ANCHOR en output |
| `omnix_web/src/pages/PublicDecisionVerify.tsx` | Badge de trust status + panel de fingerprint en UI |

### Tests Adversariales

`tests/test_trust_anchor.py` — 24 tests incluyendo:
- Keypair de atacante con firma PQC válida → rechazado como `VALID_SIGNATURE_UNTRUSTED_ISSUER`
- Recibo alterado → `INVALID_SIGNATURE`
- Sin clave pública → `UNKNOWN_KEY`
- Clave OMNIX real en env → `VALID_OMNIX_ISSUED`
- Sin firma PQC → `DOWNGRADED_SHA_ONLY`
- Prioridad de fuentes del anchor
- `OMNIX_TRUSTED_KEY_FINGERPRINT` invalido ignorado

**Status:** IMPLEMENTADO · 24/24 tests pasando · ETA-001 RESOLVED

---

## Documentos Relacionados

- [Mapa Funcional Completo](COMPLETE_FUNCTIONALITY_MAP.md) - 11 dominios detallados
- [Migración V7.0](../MIGRATION_STATUS.md) - Estado de arquitectura hexagonal
- [Deuda Técnica](TECHNICAL_DEBT.md) - Issues conocidos
- [Trazabilidad](../reference/TRACEABILITY_MATRIX.md) - 123 componentes mapeados
- [Auditoría de Código](CODEBASE_AUDIT_REPORT.md) - Verificación código vs docs
- [ADR-010 Capital Protection Metrics](../reference/adr/ADR-010-capital-protection-metric-standard.md) - Standard para métricas de protección
- [Governance Replay Engine](../../omnix_core/simulation/) - Motor de replay de crisis históricas (ADR-145)
- [Runtime Authority Matrix](../AUTHORITY_MATRIX.md) - Matriz de autoridad en runtime (ADR-146)
- [ADR-145 Governance Replay Engine](../adr/ADR-145-governance-replay-engine.md)
- [ADR-146 Runtime Authority Matrix](../adr/ADR-146-runtime-authority-matrix.md)
- [ADR-147 Scope Authorization Record](../adr/ADR-147-scope-authorization-record.md)
- [Crisis Replay Page](/crisis-replay) - 5 crisis históricas con receipts verificables (ADR-145)
- [Governance Integrity Report](../GOVERNANCE_INTEGRITY_REPORT.md) - GIR-2026-Q2-001 — 124/124 tests (ADR-147)

---

*OMNIX — Decision Governance Infrastructure*
