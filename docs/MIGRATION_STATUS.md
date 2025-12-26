# OMNIX V7.0 - Estado de Migración

**Fecha**: 22 de Diciembre 2025  
**Patrón**: Strangler Fig  
**Estado**: ESTRUCTURA 100% | ACTIVACIÓN 0% | ✅ MULTI-USER FASE 3b COMPLETADA

> **NOTA**: Este documento describe la arquitectura V7.0 implementada.
> Ver [REAL_SYSTEM_STATUS.md](REAL_SYSTEM_STATUS.md) para el estado real de producción.

> **Sistema en producción**: 100% código legacy operando 24/7 en Railway
> - **0/20 ports activados** - Todos los feature flags en `false`
> - `USE_APP_LAYER=false` - Legacy en operación
> - Arquitectura V7.0 lista pero no activada
> - **Multi-Usuario Fase 3b COMPLETADA**: RBAC implementado, 39/39 authorization tests passing

---

## Cambios Recientes

### EMA Regime Signal V1.0.5 - OHLC Fix (Dec 26, 2025)
- **ROOT CAUSE FOUND**: `_get_price_history()` returning `prices=0` because `TradingServiceEnterprise` lacked `get_ohlc()` method
- **V1.0.5 FIX**: Added delegating `get_ohlc()` method to `TradingServiceEnterprise` that forwards to `self.kraken.get_ohlc()`
- **Previous debug logging**: V1.0.2-V1.0.4b (retained for verification)
- **Files modified**: `omnix_services/trading_service/trading_service.py`
- **Expected outcome**: `prices` should now contain 100+ candles, enabling `generate_signal()` to be called

### Multi-User Phase 3b COMPLETED (Dec 22, 2025)
- **AuthorizationPort + AuthorizationAdapter** implementados y funcionando
- **17 hardcoded checks reemplazados** con RBAC en 5 archivos:
  - `omnix_core/trading_system.py` (2 guards)
  - `omnix_services/telegram_service/enterprise_bot.py` (7 guards)
  - `omnix_core/bot/auto_trading_bot.py` (5 guards)
  - `omnix_services/optimization/performance_optimizer.py` (1 guard)
  - `omnix_services/ai_service/conversational_ai_adapter.py` (1 guard)
- **5 roles definidos**: FREE < BASIC < PRO < PREMIUM < OWNER
- **15 permisos granulares** implementados
- **Harold = OWNER** en base de datos (is_admin=true, subscription_tier='owner')
- **39/39 authorization tests passing** en `tests/test_authorization.py`
- **Paper trading activo** para Harold

### Multi-User Phase 2 Complete (Dec 22, 2025)
- **9/11 issues corregidos** - Auditoría profunda completada
- **AutoTradingBot refactorizado** con `_get_effective_user_id()`
- **PostgreSQL RLS habilitado** en 3 tablas críticas (Migration V004)
- **UserSessionManager integrado** con bot init/start/stop
- **PaperTradingRepository + DatabaseService** - user_id ahora obligatorio
- **21 tests de aislamiento** pasando (incluyendo persistencia Redis)

### Language Detection AI-First (Dec 22, 2025)
- **ELIMINADOS** diccionarios hardcodeados de detección de idioma
- **INSTALADO** `fast-langdetect` (FastText-based, 80x más rápido)
- **FLUJO**: Textos largos → FastText | Textos cortos → Gemini AI
- **12/12 tests pasando**

### Multi-User Phase 1 (Dec 20, 2025)
- **UserSessionManager verificado**: 562 líneas funcionales
- **Funciones parametrizadas con user_id**: Compatible hacia atrás
- **Nuevo port**: `UserSessionPort` + `UserSessionAdapter`
- **Compatibilidad 100%**: Flujo legacy sin cambios

---

## Resumen Ejecutivo

La arquitectura hexagonal V7.0 está **completamente implementada** en `src/omnix/`. El sistema legacy sigue operando 24/7 en Railway mientras se activan gradualmente los nuevos componentes via feature flags.

| Métrica | Estado |
|---------|--------|
| Driven Ports | **17 ✅** (incluyendo AuthorizationPort, UserSessionPort) |
| Driver Ports | **3 ✅** (telegram, rest_api, intent_classification) |
| **Total Ports** | **20** |
| Adapters | **22 ✅** (incluyendo AuthorizationAdapter) |
| Ports activos en producción | **0/20 (0%)** - Legacy en uso |
| USE_APP_LAYER | **false** - No activado |
| Multi-User | ✅ **Fase 3b COMPLETADA** |
| Tests nuevos ports | **156/156 ✅** (120 ports + 36 authorization) |

---

## Arquitectura Objetivo

```
┌─────────────────────────────────────────────────────────────────┐
│                    src/omnix/ (V7.0 Hexagonal)                   │
├─────────────────────────────────────────────────────────────────┤
│  PORTS (19 protocols)                                            │
│  ├── Driven (16): Trading, MarketData, AI (3), Database, Cache,│
│  │   Notify, OnChain, MarketIntel, Execution, RiskControl,      │
│  │   Derivatives, Portfolio, Optimization, UserSession          │
│  └── Driver (3): Telegram, RestApi, IntentClassification        │
├─────────────────────────────────────────────────────────────────┤
│  ADAPTERS (21 implementaciones)                                  │
│  ├── Core: KrakenAdapter, GeminiAdapter, TradingAdapter         │
│  ├── Data: DatabaseAdapter, CacheAdapter, NotificationAdapter   │
│  ├── AI: AIGatewayShim, VoiceAdapter, IntentClassificationAdapter│
│  ├── Risk: RiskAdapter, RiskControlAdapter, CoherenceAdapter    │
│  ├── Trading: ExecutionAdapter, DerivativesAdapter              │
│  ├── Portfolio: PortfolioAdapter, OptimizationAdapter           │
│  ├── Intel: MarketIntelAdapter, OnChainAdapter, BlockchainInfo  │
│  ├── Session: UserSessionAdapter                                │
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

### Driven Ports (16 - Salida)

| Port | Adapter | Listo | Activo | Feature Flag |
|------|---------|-------|--------|--------------|
| TradingPort | TradingAdapter, KrakenAdapter | ✅ | ❌ | (incluido en App Layer) |
| MarketDataPort | KrakenAdapter | ✅ | ❌ | (incluido en TradingPort) |
| AIInferencePort | GeminiAdapter | ✅ | ❌ | (incluido en AI Port) |
| AITextGatewayPort | AIGatewayShim | ✅ | ❌ | `USE_AI_PORT=false` |
| AIVoicePort | VoiceServiceAdapter | ✅ | ❌ | `USE_VOICE_PORT=false` |
| DatabasePort | DatabaseAdapter | ✅ | ❌ | `USE_DATABASE_PORT=false` |
| CachePort | CacheAdapter | ✅ | ❌ | `USE_CACHE_PORT=false` |
| NotificationPort | NotificationAdapter | ✅ | ❌ | `USE_NOTIFICATION_PORT=false` |
| OnChainDataPort | OnChainDataAdapter | ✅ | ❌ | `USE_ONCHAIN_PORT=false` |
| MarketIntelPort | MarketIntelAdapter | ✅ | ❌ | `USE_MARKET_INTEL_PORT=false` |
| ExecutionPort | ExecutionAdapter | ✅ | ❌ | `USE_EXECUTION_PORT=false` |
| RiskControlPort | RiskControlAdapter | ✅ | ❌ | `USE_RISK_CONTROL_PORT=false` |
| DerivativesPort | DerivativesAdapter | ✅ | ❌ | `USE_DERIVATIVES_PORT=false` |
| PortfolioPort | PortfolioAdapter | ✅ | ❌ | `USE_PORTFOLIO_PORT=false` |
| OptimizationPort | OptimizationAdapter | ✅ | ❌ | `USE_OPTIMIZATION_PORT=false` |
| UserSessionPort | UserSessionAdapter | ✅ | ❌ | **NUEVO** (Dec 20) |

### Driver Ports (3 - Entrada)

| Port | Adapter | Listo | Activo | Feature Flag |
|------|---------|-------|--------|--------------|
| TelegramPort | TelegramBotAdapter | ✅ | ❌ | `USE_TELEGRAM_PORT=false` |
| RestApiPort | Flask Blueprints | ✅ | ❌ | `USE_APP_LAYER=false` |
| IntentClassificationPort | IntentClassificationAdapter | ✅ | ❌ | (incluido en AI) |

---

## Feature Flags - Estado Actual

**Estado en Railway (22 Dic 2025): TODOS EN FALSE (0% activación)**

Los feature flags están implementados en `src/omnix/config/settings.py` con defaults en `false`. El sistema opera 100% con código legacy.

### Lista de Feature Flags (Todos = false)

| Variable | Qué hace | Default |
|----------|----------|---------|
| `USE_AI_PORT` | Usa AIGatewayShim en lugar del legacy AI service | `false` |
| `USE_UNIFIED_GATEWAY` | Enruta todas las llamadas AI por gateway único | `false` |
| `USE_VOICE_PORT` | Usa VoiceServiceAdapter para TTS/STT | `false` |
| `USE_CACHE_PORT` | CacheAdapter (Redis) | `false` |
| `USE_DATABASE_PORT` | DatabaseAdapter (PostgreSQL) | `false` |
| `USE_NOTIFICATION_PORT` | Notificaciones centralizadas | `false` |
| `USE_TELEGRAM_PORT` | TelegramAdapter | `false` |
| `USE_ONCHAIN_PORT` | OnChainDataAdapter | `false` |
| `USE_MARKET_INTEL_PORT` | MarketIntelAdapter | `false` |
| `USE_EXECUTION_PORT` | ExecutionAdapter | `false` |
| `USE_RISK_CONTROL_PORT` | RiskControlAdapter | `false` |
| `USE_DERIVATIVES_PORT` | DerivativesAdapter | `false` |
| `USE_PORTFOLIO_PORT` | PortfolioAdapter | `false` |
| `USE_OPTIMIZATION_PORT` | OptimizationAdapter | `false` |
| `USE_APP_LAYER` | 5 Use Cases V7 | `false` |

### Plan de Activación (Priorizado)

| Paso | Flag | Riesgo | Rollback | Runbook | Validación |
|------|------|--------|----------|---------|------------|
| **1** | `USE_AI_PORT=true` | **BAJO** | ✅ 5min cooldown → legacy | N/A | 24h, Gemini→OpenAI failover |
| 2 | `USE_VOICE_PORT=true` | BAJO | ✅ Legacy voice_controller | N/A | /voz después de AI estable |
| 3 | `USE_MARKET_INTEL_PORT=true` | BAJO | ✅ Legacy services | [RUNBOOK](operations/RUNBOOK_MARKET_INTEL_PORT_ACTIVATION.md) | Sentiment health check |
| 4 | `USE_EXECUTION_PORT=true` | MEDIO | ✅ ExecutionProtocol | [RUNBOOK](operations/RUNBOOK_EXECUTION_PORT_ACTIVATION.md) | Order routing test |
| 5 | `USE_RISK_CONTROL_PORT=true` | MEDIO | ✅ AIRiskGuardian | [RUNBOOK](operations/RUNBOOK_RISK_CONTROL_PORT_ACTIVATION.md) | Circuit breaker test |
| 6 | `USE_DERIVATIVES_PORT=true` | **ALTO** | ✅ DerivativesManager | [RUNBOOK](operations/RUNBOOK_DERIVATIVES_PORT_ACTIVATION.md) | Paper position test |
| 7 | `USE_PORTFOLIO_PORT=true` | MEDIO | ✅ PortfolioEngine | [RUNBOOK](operations/RUNBOOK_PORTFOLIO_PORT_ACTIVATION.md) | Allocation health |
| 8 | `USE_OPTIMIZATION_PORT=true` | MEDIO | ✅ AutoOptimizer | [RUNBOOK](operations/RUNBOOK_OPTIMIZATION_PORT_ACTIVATION.md) | Weight update test |
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
| 7 | 6 Trading Ports (Phase 5) | Dec 17, 2025 |
| 8 | Multi-User Fase 1 | Dec 20, 2025 |
| 9 | Language Detection AI-First | Dec 22, 2025 |

---

## Documentos Relacionados

- `docs/current/HEXAGONAL_MIGRATION_STATUS.md` - Detalle técnico de adapters
- `docs/reference/TRACEABILITY_MATRIX.md` - Mapeo de 123 componentes
- `docs/reference/adr/ADR-001-hexagonal.md` - Decisión arquitectónica

---

*Última actualización: 22 de Diciembre 2025*
