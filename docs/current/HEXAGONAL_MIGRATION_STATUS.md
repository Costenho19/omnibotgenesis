# OMNIX V7.0 - Estado de Migración Hexagonal

**Fecha**: 18 de Diciembre 2025  
**Patrón**: Strangler Fig  
**Estado**: ESTRUCTURA 100% | ACTIVACIÓN 0%

---

## Resumen Ejecutivo

La arquitectura hexagonal V7.0 está **completamente implementada** en `src/omnix/`. El sistema legacy sigue operando 24/7 en Railway. **Ningún port está activo en producción** - todos los feature flags están en `false`.

| Métrica | Valor |
|---------|-------|
| Driven Ports | **15** |
| Driver Ports | **2** |
| Adapters | **19** |
| Ports activos en producción | **0 (0%)** |
| Tests pasando | **120/120** |

---

## Inventario de Ports

### Driven Ports (15 - Salida hacia infraestructura)

| Port | Adapter | Feature Flag | Runbook |
|------|---------|--------------|---------|
| ai_inference_port | gemini_adapter | (incluido en AI) | - |
| ai_text_gateway_port | ai_gateway_shim | `USE_AI_PORT=false` | - |
| ai_voice_port | voice_adapter | `USE_VOICE_PORT=false` | - |
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
| trading_port | trading_adapter | `USE_TRADING_PORT=false` | - |

### Driver Ports (2 - Entrada desde interfaces)

| Port | Adapter | Feature Flag |
|------|---------|--------------|
| telegram_port | telegram_adapter | `USE_TELEGRAM_PORT=false` |
| rest_api_port | Flask Blueprints | `USE_APP_LAYER=false` |

---

## Inventario de Adapters (19)

| Adapter | Ubicación | Servicio Legacy Wrapped |
|---------|-----------|------------------------|
| ai_gateway_shim | `adapters/ai_gateway_shim.py` | AIModelsManager |
| cache_adapter | `adapters/cache_adapter.py` | RedisCache |
| coherence_adapter | `adapters/coherence_adapter.py` | CoherenceEngine |
| database_adapter | `adapters/database_adapter.py` | DatabaseGateway |
| derivatives_adapter | `adapters/derivatives_adapter.py` | DerivativesManager |
| execution_adapter | `adapters/execution_adapter.py` | ExecutionProtocol |
| gemini_adapter | `adapters/gemini_adapter.py` | GeminiAIGateway |
| kraken_adapter | `adapters/kraken_adapter.py` | KrakenClient |
| market_intel_adapter | `adapters/market_intel_adapter.py` | FearGreedService, AlphaVantage, Finnhub |
| notification_adapter | `adapters/notification_adapter.py` | Telegram messaging |
| onchain_adapter | `adapters/onchain/onchain_adapter.py` | Blockchain.info API |
| optimization_adapter | `adapters/optimization_adapter.py` | AutoOptimizer, AdaptiveWeights |
| portfolio_adapter | `adapters/portfolio_adapter.py` | PortfolioEngine |
| risk_adapter | `adapters/risk_adapter.py` | RiskGuardian |
| risk_control_adapter | `adapters/risk_control_adapter.py` | CircuitBreakerManager |
| telegram_adapter | `adapters/telegram_adapter.py` | EnterpriseBot |
| trading_adapter | `adapters/trading_adapter.py` | TradingService |
| voice_adapter | `adapters/voice_adapter.py` | VoiceController |
| blockchain_info_provider | `adapters/onchain/blockchain_info_provider.py` | Blockchain.info REST |

---

## Feature Flags (Todos en FALSE)

```bash
# Estado actual en Railway (18 Dic 2025)
USE_AI_PORT=false              # Próximo a activar
USE_VOICE_PORT=false
USE_CACHE_PORT=false
USE_DATABASE_PORT=false
USE_TRADING_PORT=false
USE_NOTIFICATION_PORT=false
USE_TELEGRAM_PORT=false
USE_ONCHAIN_PORT=false
USE_MARKET_INTEL_PORT=false
USE_EXECUTION_PORT=false
USE_RISK_CONTROL_PORT=false
USE_DERIVATIVES_PORT=false
USE_PORTFOLIO_PORT=false
USE_OPTIMIZATION_PORT=false
USE_APP_LAYER=false
```

---

## Plan de Activación (12 Pasos)

| Paso | Flag | Riesgo | Dependencias |
|------|------|--------|--------------|
| 1 | `USE_AI_PORT=true` | BAJO | Ninguna - tiene fallback 5min cooldown |
| 2 | `USE_VOICE_PORT=true` | BAJO | AI Port |
| 3 | `USE_MARKET_INTEL_PORT=true` | BAJO | Ninguna |
| 4 | `USE_EXECUTION_PORT=true` | MEDIO | Trading Port (recomendado) |
| 5 | `USE_RISK_CONTROL_PORT=true` | MEDIO | Ninguna |
| 6 | `USE_DERIVATIVES_PORT=true` | ALTO | Risk Control Port |
| 7 | `USE_PORTFOLIO_PORT=true` | MEDIO | Risk Control Port |
| 8 | `USE_OPTIMIZATION_PORT=true` | MEDIO | Portfolio Port |
| 9 | `USE_CACHE_PORT=true` | BAJO | Ninguna |
| 10 | `USE_DATABASE_PORT=true` | MEDIO | Cache Port (recomendado) |
| 11 | `USE_TELEGRAM_PORT=true` | MEDIO | AI, Voice Ports |
| 12 | `USE_APP_LAYER=true` | ALTO | Todos los anteriores |

**Protocolo por paso:**
1. Activar flag en Railway
2. Monitorear 48h
3. Verificar health checks
4. Si falla → rollback automático (flag=false)
5. Si OK → siguiente paso

---

## Estructura de Código V7.0

```
src/omnix/
├── ports/                    # 17 protocols
│   ├── driven/              # 15 ports de salida
│   └── driver/              # 2 ports de entrada
├── infrastructure/
│   └── adapters/            # 19 adapters
│       └── onchain/         # 2 adapters blockchain
├── domain/                   # Lógica de negocio pura
│   ├── trading/             # Entities, VOs, 10 strategies
│   ├── risk/                # RiskGuardian, entities
│   └── onchain/             # On-chain analytics
├── application/             # 5 use cases
│   ├── trading/
│   └── risk/
└── bootstrap/
    └── container.py         # DI Container (535+ líneas)
```

---

## Timeline de Implementación

| Fase | Descripción | Completado |
|------|-------------|------------|
| 0 | Foundation | 11 Dic 2025 |
| 1 | Bootstrap & Config | 12 Dic 2025 |
| 2 | Domain & Application | 12 Dic 2025 |
| 3 | Infrastructure Adapters | 12 Dic 2025 |
| 3b | Flask Factory & Telegram | 13 Dic 2025 |
| 4 | Cleanup & Organization | 13 Dic 2025 |
| 5A | AI/Voice Port Integration | 16 Dic 2025 |
| 5B | Market Intel/Execution/Risk Control | 17 Dic 2025 |
| 5C | Derivatives/Portfolio/Optimization | 17 Dic 2025 |
| 6 | OnChain Data Port | 17 Dic 2025 |

---

## Documentos Relacionados

- [MIGRATION_STATUS.md](../MIGRATION_STATUS.md) - Estado consolidado
- [COMPLETE_FUNCTIONALITY_MAP.md](COMPLETE_FUNCTIONALITY_MAP.md) - Referencia sistema legacy
- [TRACEABILITY_MATRIX.md](../reference/TRACEABILITY_MATRIX.md) - Mapeo de componentes
- [ADR-001-hexagonal.md](../reference/adr/ADR-001-hexagonal.md) - Decisión arquitectónica

---

*Última actualización: 18 de Diciembre 2025*
