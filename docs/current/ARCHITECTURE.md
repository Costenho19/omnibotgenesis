# OMNIX V6.5.4d - Arquitectura

**Versión**: V6.5.4d INSTITUTIONAL+  
**Actualizado**: 20 de Diciembre 2025  
**Estado**: Producción 24/7

---

## Visión General

```
┌─────────────────────────────────────────────────────────────────┐
│                    OMNIX V6.5.4d INSTITUTIONAL+                  │
├─────────────────────────────────────────────────────────────────┤
│  INTERFACES                                                      │
│  ├── Telegram Bot (enterprise_bot.py)                           │
│  ├── Flask Dashboard (puerto 5000)                              │
│  └── Streamlit Dashboard (puerto 8080)                          │
├─────────────────────────────────────────────────────────────────┤
│  CORE ENGINES                                                    │
│  ├── AutoTradingBot V6.5.4d - Multi-crypto scanner              │
│  ├── CoherenceEngine V6.5 ULTRA - 6-tier veto                   │
│  ├── Non-Markovian Kernel V6.5 - Memoria temporal               │
│  ├── Risk Guardian V5.4 - Protección drawdown                   │
│  └── ARES V1/V2 - Track record generation                       │
├─────────────────────────────────────────────────────────────────┤
│  DATA LAYER                                                      │
│  ├── PostgreSQL (42 tablas, 90% FK coverage)                    │
│  ├── Redis (cache + state management)                           │
│  └── DatabaseGateway (connection pool)                          │
├─────────────────────────────────────────────────────────────────┤
│  EXTERNAL APIs                                                   │
│  ├── Kraken - Crypto data + ejecución                           │
│  ├── Gemini 2.0 Flash - AI primario                             │
│  └── Tavily - Web search                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## AI-First Multilingual Concurrency (Dec 19, 2025)

| Componente | Archivo | Función |
|------------|---------|---------|
| LanguageContextManager | `omnix_services/ai_service/prompt_templates.py` | Detección de idioma + Redis persistence |
| threading.Lock | `prompt_templates.py` | Serialización sync para langdetect |
| asyncio.to_thread() | `prompt_templates.py` | Serialización async para langdetect |
| Redis Language Cache | `omnix:user_language:{chat_id}` | 24h TTL por usuario |

**Flujo**:
```
Usuario → detect_language() [Lock] → Redis persist → System Prompt inject → Gemini → Response
```

**Política**: NO diccionarios multilingües hardcodeados. AI genera todo el contenido localizado.

---

## 1. Core Trading Engines

| Módulo | Ubicación | Propósito |
|--------|-----------|-----------|
| AutoTradingBot V6.5.4d | `omnix_core/bot/auto_trading_bot.py` | Scanner multi-crypto, señales tiered, emergency SL |
| TradingSystem V6.5 | `omnix_core/trading_system.py` | Orquestador de ejecución |
| CoherenceEngine V6.5 | `omnix_services/coherence_service/coherence_engine.py` | 6-tier veto system |
| Non-Markovian Kernel | `omnix_core/strategies/non_markovian_kernel.py` | Memoria temporal |
| Risk Guardian V5.4 | `omnix_services/monitoring/risk_guardian.py` | Protección overtrading |

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

### ARES Strategies

| Estrategia | Min Confidence | Propósito |
|------------|---------------|-----------|
| ARES V1 (Swing) | 70% | Posiciones multi-día |
| ARES V2 (Scalping) | 75% | Trades intraday |

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

### Driver Ports (Entrada) - 0/2 Activos

| Port | Adapter | Estado |
|------|---------|--------|
| TelegramPort | TelegramBotAdapter | ⬜ No activo (legacy en uso) |
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

### PostgreSQL (42+ tablas)

| Categoría | Tablas | FK Coverage |
|-----------|--------|-------------|
| Core User | 4 | 100% |
| Trading | 5 | 100% |
| Risk Management | 8 | 100% |
| Derivatives | 6 | 100% |
| Community | 5 | 100% |
| Snapshots/Analytics | 6 | 100% |
| System | 8 | N/A |

### Redis Cache

| Namespace | TTL | Propósito |
|-----------|-----|-----------|
| `market:` | 60s | Precios |
| `user:` | 5min | Estado usuario |
| `conv:` | 1hr | Conversaciones |
| `omnix:heartbeat:trading_loop` | 10min | Liveness monitoring (V6.5.4d) |
| `omnix:user_language:{chat_id}` | 24hr | User language detection |

---

## 6. Event Bridge: UserSettings → AutoTradingBot (V6.5.4d)

### Problema Resuelto
Antes de V6.5.4d, los comandos `/pausar` y `/reanudar` solo actualizaban la DB pero NO notificaban al `AutoTradingBot`. Esto causaba que el trading no se reiniciara hasta el próximo redeploy de Railway.

### Arquitectura de Integración Completa

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    FLUJO COMPLETO DE TRADING V6.5.4d                      │
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
    │              🔗 EVENT BRIDGE V6.5.4d                         │
    │  enterprise_bot.py:                                          │
    │  ├── Detecta comando /pausar o /reanudar                    │
    │  ├── Llama UserSettingsService (persistencia DB)            │
    │  └── Llama AutoTradingBot.start() o .stop() (ejecución)     │
    └─────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
    ┌─────────────────────────────────────────────────────────────┐
    │              CAPA DE EJECUCIÓN DE TRADING                    │
    │  AutoTradingBot V6.5.4d:                                     │
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
    │  5. _make_v52_decision() → scoring ponderado                │
    │  6. Coherence Engine → 6-tier veto                          │
    │  7. _execute_smart_trade() → Paper o Real                   │
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
    └── 🔗 EVENT BRIDGE (nuevo V6.5.4d)
            │
            └── AutoTradingBot.start(user_id)  ← Reinicia loop en caliente
                    │
                    └── Thread: _trading_loop() activo inmediatamente
```

### Thread Safety (V6.5.4d)

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

## 7. Cambios V6.5.4d

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

### Prompt Specification Layer V6.5.4d

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

## Documentos Relacionados

- [Mapa Funcional Completo](COMPLETE_FUNCTIONALITY_MAP.md) - 11 dominios detallados
- [Migración V7.0](../MIGRATION_STATUS.md) - Estado de arquitectura hexagonal
- [Deuda Técnica](TECHNICAL_DEBT.md) - Issues conocidos
- [Trazabilidad](../reference/TRACEABILITY_MATRIX.md) - 123 componentes mapeados
- [Auditoría de Código](CODEBASE_AUDIT_REPORT.md) - Verificación código vs docs

---

*OMNIX V6.5.4d INSTITUTIONAL+*
