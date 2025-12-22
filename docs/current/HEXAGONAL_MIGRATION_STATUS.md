# OMNIX V7.0 - Estado de Migración Hexagonal

**Fecha**: 22 de Diciembre 2025  
**Patrón**: Strangler Fig  
**Estado**: ESTRUCTURA 100% | ACTIVACIÓN 0%

---

> **IMPORTANTE**: Este documento describe la arquitectura objetivo.
> Para el estado REAL de producción, ver [REAL_SYSTEM_STATUS.md](../REAL_SYSTEM_STATUS.md).

---

## Resumen Ejecutivo

**ARQUITECTURA IMPLEMENTADA** - La arquitectura hexagonal V7.0 está **100% implementada** en `src/omnix/`. Sin embargo, el sistema opera 100% con código legacy en Railway. Todos los feature flags están desactivados.

| Métrica | Valor |
|---------|-------|
| Driven Ports | **17** (incluyendo AuthorizationPort, UserSessionPort) |
| Driver Ports | **3** |
| **Total Ports** | **20** |
| Adapters | **22** (incluyendo AuthorizationAdapter) |
| Ports activos en producción | **0/20 (0%)** - Legacy en uso |
| USE_APP_LAYER | **false** - No activado |
| Tests pasando | **156/156** (120 ports + 36 authorization) |

---

## Inventario de Ports

> **Estado**: Todos los ports están IMPLEMENTADOS pero NO activos. 
> Los flags listados son el objetivo; actualmente todos = `false`.

### Driven Ports (17 - Salida hacia infraestructura)

| Port | Adapter | Feature Flag | Runbook |
|------|---------|--------------|---------|
| ai_inference_port | gemini_adapter | (incluido en AI) | - |
| ai_text_gateway_port | ai_gateway_shim | `USE_AI_PORT=false` | - |
| ai_voice_port | voice_adapter | `USE_VOICE_PORT=false` | - |
| **authorization_port** | **authorization_adapter** | **NUEVO (Dec 22)** | - |
| cache_port | cache_adapter | `USE_CACHE_PORT=false` | - |
| database_port | database_adapter | `USE_DATABASE_PORT=false` | - |
| derivatives_port | derivatives_adapter | `USE_DERIVATIVES_PORT=false` | [Runbook](../operations/RUNBOOK_DERIVATIVES_PORT_ACTIVATION.md) |
| execution_port | execution_adapter | `USE_EXECUTION_PORT=false` | [Runbook](../operations/RUNBOOK_EXECUTION_PORT_ACTIVATION.md) |
| market_data_port | kraken_adapter | (incluido en Trading) | - |
| market_intel_port | market_intel_adapter | `USE_MARKET_INTEL_PORT=false` | [Runbook](../operations/RUNBOOK_MARKET_INTEL_PORT_ACTIVATION.md) |
| notification_port | notification_adapter | `USE_NOTIFICATION_PORT=false` | - |
| onchain_data_port | onchain_adapter | `USE_ONCHAIN_PORT=false` | [Runbook](../operations/RUNBOOK_ONCHAIN_PORT_ACTIVATION.md) |
| optimization_port | optimization_adapter | `USE_OPTIMIZATION_PORT=false` | [Runbook](../operations/RUNBOOK_OPTIMIZATION_PORT_ACTIVATION.md) |
| portfolio_port | portfolio_adapter | `USE_PORTFOLIO_PORT=false` | [Runbook](../operations/RUNBOOK_PORTFOLIO_PORT_ACTIVATION.md) |
| risk_control_port | risk_control_adapter | `USE_RISK_CONTROL_PORT=false` | [Runbook](../operations/RUNBOOK_RISK_CONTROL_PORT_ACTIVATION.md) |
| trading_port | trading_adapter | (incluido en App Layer) | - |
| user_session_port | user_session_adapter | NUEVO (Dec 20) | - |

### Driver Ports (3 - Entrada desde interfaces)

| Port | Adapter | Feature Flag |
|------|---------|--------------|
| telegram_port | telegram_adapter | `USE_TELEGRAM_PORT=false` |
| rest_api_port | Flask Blueprints | `USE_APP_LAYER=false` |
| intent_classification_port | intent_classification_adapter | (incluido en AI) |

---

## Inventario de Adapters (22)

| Adapter | Ubicación | Servicio Legacy Wrapped |
|---------|-----------|------------------------|
| ai_gateway_shim | `adapters/ai_gateway_shim.py` | AIModelsManager |
| **authorization_adapter** | `adapters/authorization_adapter.py` | **RBAC + PostgreSQL + Redis** (Dec 22) |
| cache_adapter | `adapters/cache_adapter.py` | RedisCache |
| coherence_adapter | `adapters/coherence_adapter.py` | CoherenceEngine |
| database_adapter | `adapters/database_adapter.py` | DatabaseGateway |
| derivatives_adapter | `adapters/derivatives_adapter.py` | DerivativesManager |
| execution_adapter | `adapters/execution_adapter.py` | ExecutionProtocol |
| gemini_adapter | `adapters/gemini_adapter.py` | GeminiAIGateway |
| intent_classification_adapter | `adapters/intent_classification_adapter.py` | IntentDetector |
| kraken_adapter | `adapters/kraken_adapter.py` | KrakenClient |
| market_intel_adapter | `adapters/market_intel_adapter.py` | FearGreedService, AlphaVantage, Finnhub |
| notification_adapter | `adapters/notification_adapter.py` | Telegram messaging |
| onchain_adapter | `adapters/onchain/onchain_adapter.py` | BlockchainInfoProvider |
| optimization_adapter | `adapters/optimization_adapter.py` | AutoOptimizer, AdaptiveWeights |
| portfolio_adapter | `adapters/portfolio_adapter.py` | PortfolioEngine |
| risk_adapter | `adapters/risk_adapter.py` | RiskGuardian |
| risk_control_adapter | `adapters/risk_control_adapter.py` | CircuitBreakerManager |
| telegram_adapter | `adapters/telegram_adapter.py` | EnterpriseBot |
| trading_adapter | `adapters/trading_adapter.py` | TradingService |
| user_session_adapter | `adapters/user_session_adapter.py` | UserSessionManager |
| voice_adapter | `adapters/voice_adapter.py` | VoiceController |
| blockchain_info_provider | `adapters/onchain/blockchain_info_provider.py` | Blockchain.info REST |

---

## Feature Flags - Estado Actual

**Estado en Railway (22 Dic 2025): TODOS EN FALSE (0% activación)**

Los feature flags están implementados en `src/omnix/config/settings.py` con defaults en `false`.

### Lista de Feature Flags

| Variable | Qué hace | Estado |
|----------|----------|--------|
| `USE_AI_PORT` | Usa AIGatewayShim | `false` |
| `USE_UNIFIED_GATEWAY` | Gateway único AI | `false` |
| `USE_VOICE_PORT` | VoiceServiceAdapter | `false` |
| `USE_CACHE_PORT` | CacheAdapter (Redis) | `false` |
| `USE_DATABASE_PORT` | DatabaseAdapter | `false` |
| `USE_NOTIFICATION_PORT` | Notificaciones | `false` |
| `USE_TELEGRAM_PORT` | TelegramAdapter | `false` |
| `USE_ONCHAIN_PORT` | OnChainDataAdapter | `false` |
| `USE_MARKET_INTEL_PORT` | MarketIntelAdapter | `false` |
| `USE_EXECUTION_PORT` | ExecutionAdapter | `false` |
| `USE_RISK_CONTROL_PORT` | RiskControlAdapter | `false` |
| `USE_DERIVATIVES_PORT` | DerivativesAdapter | `false` |
| `USE_PORTFOLIO_PORT` | PortfolioAdapter | `false` |
| `USE_OPTIMIZATION_PORT` | OptimizationAdapter | `false` |
| `USE_APP_LAYER` | 5 Use Cases V7 | `false` |

---

## Plan de Activación (Priorizado)

| Paso | Flag | Riesgo | Rollback |
|------|------|--------|----------|
| **1** | `USE_AI_PORT=true` | **BAJO** | 5min cooldown → legacy |
| 2 | `USE_VOICE_PORT=true` | BAJO | Legacy voice_controller |
| 3 | `USE_MARKET_INTEL_PORT=true` | BAJO | Legacy services |
| 4 | `USE_EXECUTION_PORT=true` | MEDIO | ExecutionProtocol |
| 5 | `USE_RISK_CONTROL_PORT=true` | MEDIO | AIRiskGuardian |
| 6 | `USE_DERIVATIVES_PORT=true` | **ALTO** | DerivativesManager |
| 7 | `USE_PORTFOLIO_PORT=true` | MEDIO | PortfolioEngine |
| 8 | `USE_OPTIMIZATION_PORT=true` | MEDIO | AutoOptimizer |
| 9 | `USE_CACHE_PORT=true` | BAJO | RedisCache directo |
| 10 | `USE_DATABASE_PORT=true` | MEDIO | DatabaseGateway |
| 11 | `USE_TELEGRAM_PORT=true` | MEDIO | EnterpriseBot |
| 12 | `USE_APP_LAYER=true` | **ALTO** | Múltiples fallbacks |

---

## Documentos Relacionados

- [MIGRATION_STATUS.md](../MIGRATION_STATUS.md) - Estado consolidado V7.0
- [REAL_SYSTEM_STATUS.md](../REAL_SYSTEM_STATUS.md) - **FUENTE DE VERDAD**
- [TRACEABILITY_MATRIX.md](../reference/TRACEABILITY_MATRIX.md) - Mapeo de componentes

---

*Última actualización: 22 de Diciembre 2025*
