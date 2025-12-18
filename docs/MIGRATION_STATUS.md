# OMNIX V7.0 - Estado de Migración

**Fecha**: 18 de Diciembre 2025  
**Patrón**: Strangler Fig  
**Estado**: ESTRUCTURA 100% | ACTIVACIÓN 17.6% (3/17 ports)

> ✅ **UPDATE 18 Dic 2025:**
> - 3 ports activos en Railway: `USE_AI_PORT`, `USE_UNIFIED_GATEWAY`, `USE_VOICE_PORT`
> - 12 variables pendientes de activar (11 ports + USE_APP_LAYER)
> - Sistema usa mezcla V7 (AI/Voice) + Legacy (resto)

### Último Update (17 Dic 2025 - Session 5)

**Implementación de 6 Nuevos Driven Ports (Phase 5):**
- **MarketIntelPort**: Sentiment analysis, technical indicators, news aggregation
- **ExecutionPort**: Liquidity analysis, correlation, slippage prediction, order routing
- **RiskControlPort**: Circuit breakers, limits engine, position monitoring, alerts
- **DerivativesPort**: Futures contracts, hedging, margin management, funding analysis
- **PortfolioPort**: Portfolio view, rebalancing, exposure management, allocation plans
- **OptimizationPort**: Parameter optimization, adaptive weights, ML learning, forecasts

**Tests:** 120/120 pasando para los 6 nuevos ports

**Adapters Implementados:**
- MarketIntelAdapter (wraps FearGreedService, AlphaVantageService, FinnhubService)
- ExecutionAdapter (wraps ExecutionProtocol, LiquidityAnalyzer, CorrelationEngine)
- RiskControlAdapter (wraps CircuitBreakerManager, LimitsEngine, PositionMonitor)
- DerivativesAdapter (wraps DerivativesManager, KrakenFuturesClient, HedgingService)
- PortfolioAdapter (wraps PortfolioEngine, PortfolioOptimizer, ExposureManager)
- OptimizationAdapter (wraps AutoOptimizer, AdaptiveWeights, MLModule)

---

### Update (16 Dic 2025 - Session 3)

**Corrección Crítica de Integración V7 ↔ Legacy:**
- `ai_gateway_shim.py`: Refactorizado como PUENTE PURO que delega a `AIModelsManager`
- Ahora USE_AI_PORT=true usa el mismo failover que legacy: Gemini → OpenAI → Anthropic
- `container.py`: Inyecta `AIModelsManager` al crear `AIGatewayShim`
- `ai_error_handler.py`: Sistema de clasificación de errores con 8 categorías
- `ai_models.py`: Timeouts adaptivos (Gemini 20s, OpenAI 15s, Anthropic 15s)
- Skip inteligente para errores non-retryable (401, 403, 404)

**Fallback con Cooldown (Production-Ready):**
- `_is_v7_shim_in_cooldown()`: Previene hot-loops (5 min cooldown)
- `_reset_v7_shim()`: Limpia shim + manager + marca timestamp de fallo
- `fallback_to_legacy`: Flag que asegura fallback en mismo request
- Sin lazy-loading: Container tiene control total del ciclo de vida

**Antes (bug):**
```
USE_AI_PORT=true → AIGatewayShim → GeminiAdapter → Solo Gemini ❌
```

**Ahora (corregido):**
```
USE_AI_PORT=true → AIGatewayShim → AIModelsManager → Gemini/OpenAI/Anthropic ✅
Manager falla → Cooldown 5min → RoutingAIGateway (legacy) ✅
```

**Tests:** 31/31 pasando (incluyendo degradation, cooldown, y voice scenarios)

---

## Resumen Ejecutivo

La arquitectura hexagonal V7.0 está **completamente implementada** en `src/omnix/`. El sistema legacy sigue operando 24/7 en Railway mientras se activan gradualmente los nuevos componentes via feature flags.

| Métrica | Estado |
|---------|--------|
| Driven Ports definidos | **15 ✅** |
| Driver Ports definidos | **2 ✅** |
| Adapters implementados | **19 ✅** |
| Ports activos en producción | **3 (17.6%)** |
| Feature flags pendientes | 12 |
| Próximo a activar | `USE_CACHE_PORT=true` |
| Tests nuevos ports | **120/120 ✅** |

---

## Arquitectura Objetivo

```
┌─────────────────────────────────────────────────────────────────┐
│                    src/omnix/ (V7.0 Hexagonal)                   │
├─────────────────────────────────────────────────────────────────┤
│  PORTS (17 protocols)                                            │
│  ├── Driven (15): Trading, MarketData, AI, Database, Cache,     │
│  │   Notify, OnChain, MarketIntel, Execution, RiskControl,      │
│  │   Derivatives, Portfolio, Optimization, AIVoice, AIInference │
│  └── Driver (2): Telegram, RestApi                               │
├─────────────────────────────────────────────────────────────────┤
│  ADAPTERS (19 implementaciones)                                  │
│  ├── Core: KrakenAdapter, GeminiAdapter, TradingAdapter         │
│  ├── Data: DatabaseAdapter, CacheAdapter, NotificationAdapter   │
│  ├── AI: AIGatewayShim, VoiceAdapter                            │
│  ├── Risk: RiskAdapter, RiskControlAdapter, CoherenceAdapter    │
│  ├── Trading: ExecutionAdapter, DerivativesAdapter              │
│  ├── Portfolio: PortfolioAdapter, OptimizationAdapter           │
│  ├── Intel: MarketIntelAdapter, OnChainAdapter                  │
│  └── Interface: TelegramAdapter                                  │
├─────────────────────────────────────────────────────────────────┤
│  DOMAIN (lógica de negocio pura)                                │
│  ├── 10 estrategias de trading                                  │
│  ├── Risk Guardian, Coherence Engine                            │
│  └── Entities, Value Objects                                    │
├─────────────────────────────────────────────────────────────────┤
│  APPLICATION (use cases)                                         │
│  └── ExecuteTrade, ScanMarket, ManagePositions, EvaluateRisk    │
├─────────────────────────────────────────────────────────────────┤
│  BOOTSTRAP                                                       │
│  └── DI Container (535+ líneas), Settings (Pydantic)            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Estado de Ports y Adapters

### Driven Ports (Salida)

| Port | Adapter | Listo | Activo | Feature Flag |
|------|---------|-------|--------|--------------|
| TradingPort | TradingAdapter, KrakenAdapter | ✅ | ⬜ | `USE_TRADING_PORT=false` |
| MarketDataPort | KrakenAdapter | ✅ | ⬜ | (incluido en TradingPort) |
| AIInferencePort | GeminiAdapter | ✅ | ⬜ | (incluido en AI Port) |
| **AITextGatewayPort** | AIGatewayShim | ✅ | ✅ | `USE_AI_PORT=true` |
| AIVoicePort | VoiceServiceAdapter | ✅ | ✅ | `USE_VOICE_PORT=true` |
| DatabasePort | DatabaseAdapter | ✅ | ⬜ | `USE_DATABASE_PORT=false` |
| CachePort | CacheAdapter | ✅ | ⬜ | `USE_CACHE_PORT=false` |
| NotificationPort | NotificationAdapter | ✅ | ⬜ | `USE_NOTIFICATION_PORT=false` |
| **OnChainDataPort** | OnChainDataAdapter | ✅ | ⬜ | `USE_ONCHAIN_PORT=false` |
| **MarketIntelPort** | MarketIntelAdapter | ✅ | ⬜ | `USE_MARKET_INTEL_PORT=false` |
| **ExecutionPort** | ExecutionAdapter | ✅ | ⬜ | `USE_EXECUTION_PORT=false` |
| **RiskControlPort** | RiskControlAdapter | ✅ | ⬜ | `USE_RISK_CONTROL_PORT=false` |
| **DerivativesPort** | DerivativesAdapter | ✅ | ⬜ | `USE_DERIVATIVES_PORT=false` |
| **PortfolioPort** | PortfolioAdapter | ✅ | ⬜ | `USE_PORTFOLIO_PORT=false` |
| **OptimizationPort** | OptimizationAdapter | ✅ | ⬜ | `USE_OPTIMIZATION_PORT=false` |

### Driver Ports (Entrada)

| Port | Adapter | Listo | Activo | Feature Flag |
|------|---------|-------|--------|--------------|
| TelegramPort | TelegramBotAdapter | ✅ | ⬜ | `USE_TELEGRAM_PORT=false` |
| RestApiPort | Flask Blueprints | ✅ | ⬜ | `USE_APP_LAYER=false` |

---

## Feature Flags - Lista Completa Variables Strangler Fig

**Estado actual (18 Dic 2025)**

### 🟢 Ya activas en Railway (3):

| Variable | Qué hace |
|----------|----------|
| `USE_AI_PORT=true` | Usa AIGatewayShim en lugar del legacy AI service. Tiene fallback automático con cooldown de 5 min si falla |
| `USE_UNIFIED_GATEWAY=true` | Enruta todas las llamadas AI por un gateway único (Gemini → OpenAI → Anthropic) |
| `USE_VOICE_PORT=true` | Usa VoiceServiceAdapter para transcripción de audio (Whisper) y síntesis (ElevenLabs) |

### 🔴 Pendientes de activar (12):

**Infraestructura:**

| Variable | Qué hace |
|----------|----------|
| `USE_CACHE_PORT=true` | Usa CacheAdapter (Redis) en lugar de acceso directo. Maneja TTL, invalidación, health checks |
| `USE_DATABASE_PORT=true` | Usa DatabaseAdapter (PostgreSQL) con connection pooling, retry automático, transacciones |
| `USE_NOTIFICATION_PORT=true` | Centraliza notificaciones (Telegram, email futuro) con cola y rate limiting |
| `USE_TELEGRAM_PORT=true` | Usa TelegramAdapter para envío/recepción de mensajes con retry y formateo |
| `USE_ONCHAIN_PORT=true` | Usa OnChainDataAdapter para datos blockchain (whale alerts, liquidaciones, flujos) |

**Trading Core:**

| Variable | Qué hace |
|----------|----------|
| `USE_MARKET_INTEL_PORT=true` | Usa MarketIntelAdapter para datos de mercado unificados (Kraken, Alpaca, CoinGecko) |
| `USE_EXECUTION_PORT=true` | Usa ExecutionAdapter para órdenes. **Crítico**: controla ejecución real de trades |
| `USE_RISK_CONTROL_PORT=true` | Usa RiskControlAdapter para validación de posiciones, límites, stop-loss automático |
| `USE_DERIVATIVES_PORT=true` | Usa DerivativesAdapter para opciones y futuros (Greeks, pricing, hedging) |
| `USE_PORTFOLIO_PORT=true` | Usa PortfolioAdapter para gestión de cartera institucional, rebalanceo, allocations |
| `USE_OPTIMIZATION_PORT=true` | Usa OptimizationAdapter para calibración adaptativa de parámetros (CAES, pesos) |

**Capa de Aplicación:**

| Variable | Qué hace |
|----------|----------|
| `USE_APP_LAYER=true` | Activa los 5 Use Cases V7 completos (AnalyzeMarket, ExecuteTrade, etc.) en lugar del flujo legacy |

### 📋 Variables para copiar a Railway:

```bash
# Ya activas
USE_AI_PORT=true
USE_UNIFIED_GATEWAY=true
USE_VOICE_PORT=true

# Pendientes de activar (en orden recomendado)
USE_CACHE_PORT=true
USE_DATABASE_PORT=true
USE_NOTIFICATION_PORT=true
USE_TELEGRAM_PORT=true
USE_ONCHAIN_PORT=true
USE_MARKET_INTEL_PORT=true
USE_EXECUTION_PORT=true
USE_RISK_CONTROL_PORT=true
USE_DERIVATIVES_PORT=true
USE_PORTFOLIO_PORT=true
USE_OPTIMIZATION_PORT=true
USE_APP_LAYER=true
```

### Plan de Activación (Priorizado)

| Paso | Flag | Riesgo | Rollback | Runbook | Validación |
|------|------|--------|----------|---------|------------|
| **1** | `USE_AI_PORT=true` | **BAJO** | ✅ 5min cooldown → legacy | N/A | 24h, Gemini→OpenAI failover |
| 2 | `USE_VOICE_PORT=true` | BAJO | ✅ Legacy voice_controller | N/A | /voz después de AI estable |
| 3 | `USE_MARKET_INTEL_PORT=true` | BAJO | ✅ Legacy services | [RUNBOOK](RUNBOOK_MARKET_INTEL_PORT_ACTIVATION.md) | Sentiment health check |
| 4 | `USE_EXECUTION_PORT=true` | MEDIO | ✅ ExecutionProtocol | [RUNBOOK](RUNBOOK_EXECUTION_PORT_ACTIVATION.md) | Order routing test |
| 5 | `USE_RISK_CONTROL_PORT=true` | MEDIO | ✅ AIRiskGuardian | [RUNBOOK](RUNBOOK_RISK_CONTROL_PORT_ACTIVATION.md) | Circuit breaker test |
| 6 | `USE_DERIVATIVES_PORT=true` | **ALTO** | ✅ DerivativesManager | [RUNBOOK](RUNBOOK_DERIVATIVES_PORT_ACTIVATION.md) | Paper position test |
| 7 | `USE_PORTFOLIO_PORT=true` | MEDIO | ✅ PortfolioEngine | [RUNBOOK](RUNBOOK_PORTFOLIO_PORT_ACTIVATION.md) | Allocation health |
| 8 | `USE_OPTIMIZATION_PORT=true` | MEDIO | ✅ AutoOptimizer | [RUNBOOK](RUNBOOK_OPTIMIZATION_PORT_ACTIVATION.md) | Weight update test |
| 9 | `USE_CACHE_PORT=true` | BAJO | ✅ RedisCache directo | N/A | Health check Redis |
| 10 | `USE_DATABASE_PORT=true` | MEDIO | ✅ DatabaseGateway | N/A | Query comparison |
| 11 | `USE_TELEGRAM_PORT=true` | MEDIO | ✅ EnterpriseBot | N/A | Command testing |
| 12 | `USE_APP_LAYER=true` | **ALTO** | ✅ Múltiples fallbacks | N/A | Full E2E test 48h |

### ¿Por qué AI Port primero?

1. **Tiene fallback robusto**: Si falla, cooldown 5min → usa RoutingAIGateway legacy
2. **No tiene dependientes**: Puede fallar sin afectar otros servicios
3. **Voice depende de AI**: Activar AI primero prepara el camino
4. **Logging completo**: El shim registra todos los errores con categorización

---

## Timeline Completado

| Fase | Nombre | Completado |
|------|--------|------------|
| 0 | Foundation | Dec 11, 2025 |
| 1 | Bootstrap & Config | Dec 12, 2025 |
| 2 | Domain & Application | Dec 12, 2025 |
| 3 | Infrastructure Adapters | Dec 12, 2025 |
| 3b | Flask Factory & Telegram | Dec 13, 2025 |
| 4 | Cleanup & Organization | Dec 13, 2025 |
| 5 | Cache/DB Port Integration | Dec 16, 2025 |
| 6 | AI/Voice Port Integration | Dec 16, 2025 |

---

## Próximos Pasos

1. **Activar feature flags** en staging (Railway)
2. **Validar 48h** sin errores
3. **Activar en producción**
4. **Eliminar código legacy** una vez validado

---

## Documentos Relacionados

- `docs/current/HEXAGONAL_MIGRATION_STATUS.md` - Detalle técnico de adapters
- `docs/reference/TRACEABILITY_MATRIX.md` - Mapeo de 123 componentes
- `docs/reference/adr/ADR-001-hexagonal.md` - Decisión arquitectónica

---

*Última actualización: 18 de Diciembre 2025*
