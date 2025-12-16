# OMNIX V7.0 - Estado de Migración

**Fecha**: 16 de Diciembre 2025  
**Patrón**: Strangler Fig  
**Estado**: ESTRUCTURA 100% | ACTIVACIÓN 37.5%

---

## Resumen Ejecutivo

La arquitectura hexagonal V7.0 está **completamente implementada** en `src/omnix/`. El sistema legacy sigue operando 24/7 en Railway mientras se activan gradualmente los nuevos componentes via feature flags.

| Métrica | Estado |
|---------|--------|
| Ports definidos | 8/8 ✅ |
| Adapters implementados | 9/9 ✅ |
| Ports activos en producción | 3/8 (37.5%) |
| Feature flags pendientes | 5 |

---

## Arquitectura Objetivo

```
┌─────────────────────────────────────────────────────────────────┐
│                    src/omnix/ (V7.0 Hexagonal)                   │
├─────────────────────────────────────────────────────────────────┤
│  PORTS (8 protocols)                                             │
│  ├── Driven: Trading, MarketData, AI, Database, Cache, Notify   │
│  └── Driver: Telegram, RestApi                                   │
├─────────────────────────────────────────────────────────────────┤
│  ADAPTERS (9 implementaciones)                                   │
│  ├── KrakenAdapter, GeminiAdapter, TradingAdapter               │
│  ├── DatabaseAdapter, CacheAdapter, NotificationAdapter         │
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

| Port | Adapter | Activo | Feature Flag |
|------|---------|--------|--------------|
| TradingPort | TradingAdapter, KrakenAdapter | ✅ | - |
| MarketDataPort | KrakenAdapter | ✅ | - |
| AIInferencePort | GeminiAdapter | ✅ | - |
| AITextGatewayPort | AIGatewayShim | ⬜ | `USE_AI_PORT=false` |
| AIVoicePort | VoiceServiceAdapter | ⬜ | `USE_VOICE_PORT=false` |
| DatabasePort | DatabaseAdapter | ⬜ | `USE_DATABASE_PORT=false` |
| CachePort | CacheAdapter | ⬜ | `USE_CACHE_PORT=false` |
| NotificationPort | NotificationAdapter | ⬜ | `USE_NOTIFICATION_PORT=false` |

### Driver Ports (Entrada)

| Port | Adapter | Activo | Feature Flag |
|------|---------|--------|--------------|
| TelegramPort | TelegramBotAdapter | ⬜ | `USE_TELEGRAM_PORT=false` |
| RestApiPort | Flask Blueprints | ⬜ | `USE_APP_LAYER=false` |

---

## Feature Flags

```bash
# Activos
USE_UNIFIED_GATEWAY=true

# Listos para activar (16 Dic 2025)
USE_CACHE_PORT=false      # CacheAdapter - Tests pasando
USE_DATABASE_PORT=false   # DatabaseAdapter - Tests pasando
USE_AI_PORT=false         # AIGatewayShim - Health OK
USE_VOICE_PORT=false      # VoiceServiceAdapter - TTS disponible

# Pendientes de validación
USE_TRADING_PORT=false
USE_NOTIFICATION_PORT=false
USE_TELEGRAM_PORT=false
USE_APP_LAYER=false
```

### Plan de Activación

| Paso | Flag | Riesgo | Validación |
|------|------|--------|------------|
| 1 | `USE_CACHE_PORT=true` | BAJO | Health check Redis ✅ |
| 2 | `USE_DATABASE_PORT=true` | MEDIO | Query comparison ✅ |
| 3 | `USE_AI_PORT=true` | BAJO | AIGatewayShim health ✅ |
| 4 | `USE_VOICE_PORT=true` | BAJO | TTS/STT health ✅ |
| 5 | `USE_NOTIFICATION_PORT=true` | BAJO | Test message |
| 6 | `USE_TELEGRAM_PORT=true` | MEDIO | Command testing |
| 7 | `USE_APP_LAYER=true` | ALTO | Full E2E test |

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

*Última actualización: 16 de Diciembre 2025*
