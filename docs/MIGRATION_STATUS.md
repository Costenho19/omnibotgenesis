# OMNIX V7.0 - Estado de Migración

**Fecha**: 17 de Diciembre 2025  
**Patrón**: Strangler Fig  
**Estado**: ESTRUCTURA 100% | ACTIVACIÓN 0%

> ⚠️ **REALIDAD vs DOCUMENTACIÓN (corregido 17 Dic 2025):**
> - La documentación anterior decía "37.5% activación (3/8 ports activos)"
> - La REALIDAD es **0% activación** - todos los feature flags están en `false`
> - El sistema sigue usando 100% código legacy en Railway
> - Los ports TradingPort, MarketDataPort, AIInferencePort tienen adapters pero **no están activos**

### Último Update (16 Dic 2025 - Session 3)

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
| Ports definidos | 9/9 ✅ |
| Adapters implementados | 10/10 ✅ |
| Ports activos en producción | **0/9 (0%)** |
| Feature flags pendientes | 9 (todos) |
| Próximo a activar | `USE_AI_PORT=true` |

---

## Arquitectura Objetivo

```
┌─────────────────────────────────────────────────────────────────┐
│                    src/omnix/ (V7.0 Hexagonal)                   │
├─────────────────────────────────────────────────────────────────┤
│  PORTS (9 protocols)                                             │
│  ├── Driven: Trading, MarketData, AI, Database, Cache, Notify   │
│  ├── Driven: OnChainData (NEW - 17 Dic 2025)                     │
│  └── Driver: Telegram, RestApi                                   │
├─────────────────────────────────────────────────────────────────┤
│  ADAPTERS (10 implementaciones)                                  │
│  ├── KrakenAdapter, GeminiAdapter, TradingAdapter               │
│  ├── DatabaseAdapter, CacheAdapter, NotificationAdapter         │
│  ├── OnChainDataAdapter (NEW - Blockchain.info provider)        │
│  └── TelegramBotAdapter, RiskAdapter, CoherenceAdapter          │
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
│  └── DI Container (509 líneas), Settings (Pydantic)             │
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
| **AITextGatewayPort** | AIGatewayShim | ✅ | ⬜ | `USE_AI_PORT=false` ← **PRÓXIMO** |
| AIVoicePort | VoiceServiceAdapter | ✅ | ⬜ | `USE_VOICE_PORT=false` |
| DatabasePort | DatabaseAdapter | ✅ | ⬜ | `USE_DATABASE_PORT=false` |
| CachePort | CacheAdapter | ✅ | ⬜ | `USE_CACHE_PORT=false` |
| NotificationPort | NotificationAdapter | ✅ | ⬜ | `USE_NOTIFICATION_PORT=false` |
| **OnChainDataPort** | OnChainDataAdapter | ✅ | ⬜ | `USE_ONCHAIN_PORT=false` |

### Driver Ports (Entrada)

| Port | Adapter | Listo | Activo | Feature Flag |
|------|---------|-------|--------|--------------|
| TelegramPort | TelegramBotAdapter | ✅ | ⬜ | `USE_TELEGRAM_PORT=false` |
| RestApiPort | Flask Blueprints | ✅ | ⬜ | `USE_APP_LAYER=false` |

---

## Feature Flags

**Estado actual (17 Dic 2025): TODOS EN FALSE**

```bash
# Todos desactivados - Sistema usa 100% legacy
USE_AI_PORT=false         # ← PRÓXIMO A ACTIVAR
USE_VOICE_PORT=false      # Depende de AI Port
USE_CACHE_PORT=false      
USE_DATABASE_PORT=false   
USE_TRADING_PORT=false
USE_NOTIFICATION_PORT=false
USE_TELEGRAM_PORT=false
USE_ONCHAIN_PORT=false    # NEW - On-chain blockchain data
USE_APP_LAYER=false       # Activa toda la capa de aplicación
```

### Plan de Activación (Priorizado)

| Paso | Flag | Riesgo | Rollback | Validación Requerida |
|------|------|--------|----------|----------------------|
| **1** | `USE_AI_PORT=true` | **BAJO** | ✅ 5min cooldown → legacy | Monitor 24h, verificar Gemini→OpenAI failover |
| 2 | `USE_VOICE_PORT=true` | BAJO | ✅ Legacy voice_controller | Probar /voz después de AI estable |
| 3 | `USE_CACHE_PORT=true` | BAJO | ✅ RedisCache directo | Health check Redis |
| 4 | `USE_DATABASE_PORT=true` | MEDIO | ✅ DatabaseGateway directo | Query comparison |
| 5 | `USE_NOTIFICATION_PORT=true` | BAJO | ✅ telegram_utils directo | Test message |
| 6 | `USE_TELEGRAM_PORT=true` | MEDIO | ✅ EnterpriseBot directo | Command testing |
| 7 | `USE_APP_LAYER=true` | **ALTO** | ✅ Múltiples fallbacks | Full E2E test 48h |

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

*Última actualización: 17 de Diciembre 2025*
