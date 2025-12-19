# OMNIX V6.5.4d - Arquitectura

**Versión**: V6.5.4d INSTITUTIONAL+  
**Actualizado**: 19 de Diciembre 2025  
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

### Driven Ports (Salida)

| Port | Adapter | Estado |
|------|---------|--------|
| TradingPort | KrakenAdapter | ✅ Activo |
| MarketDataPort | KrakenAdapter | ✅ Activo |
| AIInferencePort | GeminiAdapter | ✅ Activo |
| DatabasePort | DatabaseAdapter | ⬜ Diferido |
| CachePort | CacheAdapter | ⬜ Diferido |
| NotificationPort | NotificationAdapter | ⬜ Diferido |

### Driver Ports (Entrada)

| Port | Adapter | Estado |
|------|---------|--------|
| TelegramPort | TelegramBotAdapter | ⬜ Diferido |
| RestApiPort | Flask Blueprints | ⬜ Diferido |

Ver [MIGRATION_STATUS.md](../MIGRATION_STATUS.md) para detalles de migración V7.0.

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

---

## 6. Cambios V6.5.4d

| Parámetro | Valor | Efecto |
|-----------|-------|--------|
| EMERGENCY_SL_PCT | 2% | Max loss por posición |
| score_moderate | 12 | Solo STRONG/VERY_STRONG |
| ADA/USD | EXCLUDED | 0% win rate |
| Kalman BEARISH | -15 pts | Veto macro trend |

---

## 7. APIs Externas

| API | Servicio | Rate Limit |
|-----|----------|------------|
| Kraken REST | market_data | 15 req/min |
| Kraken WS | market_data | Streaming |
| Gemini 2.0 | ai_service | 60 RPM |
| Finnhub | market_intelligence | 60 req/min |
| Alpha Vantage | market_intelligence | 5 req/min |
| Tavily | web_search | Per API key |

---

## 8. Dominios Funcionales

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

## 9. AI-First Multilingual (Dec 19, 2025)

El sistema responde automáticamente en el idioma del usuario usando AI auto-detection:

| Componente | Cambio | Archivo |
|------------|--------|---------|
| System Prompt | `Responde SIEMPRE en el mismo idioma que el usuario escriba su mensaje` | ai_prompts.py |
| Legacy Prompt | Igual instrucción AI-first | conversational_ai_adapter.py |
| Prompt Builder | Instrucción multilingüe | omnix_prompt_builder.py |
| User Settings | `language_code='auto'` como default | database_service.py |

**Principios:**
- Sin diccionarios de idiomas hardcodeados para respuestas
- AI auto-detection siempre activo
- `language_code='auto'` guardado en DB como respaldo
- Diccionarios de `trading_terms` solo para detección de intents (no restricción de idioma)

---

## Documentos Relacionados

- [Mapa Funcional Completo](COMPLETE_FUNCTIONALITY_MAP.md) - 11 dominios detallados
- [Migración V7.0](../MIGRATION_STATUS.md) - Estado de arquitectura hexagonal
- [Deuda Técnica](TECHNICAL_DEBT.md) - Issues conocidos
- [Trazabilidad](../reference/TRACEABILITY_MATRIX.md) - 123 componentes mapeados
- [Auditoría de Código](CODEBASE_AUDIT_REPORT.md) - Verificación código vs docs

---

*OMNIX V6.5.4d INSTITUTIONAL+*
