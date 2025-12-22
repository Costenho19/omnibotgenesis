# OMNIX V7.0 - Estado REAL del Sistema

**Fecha**: 20 de Diciembre 2025  
**Estado**: ESTRUCTURA 100% | ACTIVACIÓN 0% | MULTI-USER FASE 1 COMPLETADA

> **FUENTE DE VERDAD**: Este documento refleja el estado real de producción en Railway.

---

## Cambios Recientes (Dec 20, 2025)

### Multi-Usuario Fase 1 COMPLETADA
- **UserSessionManager EXISTE**: 562 líneas funcionales en `omnix_core/sessions/user_session_manager.py`
- **Funciones parametrizadas**: `_check_open_positions_tp_sl`, `_execute_smart_trade`, `_check_position_limit_early` ahora aceptan `user_id` opcional con fallback legacy
- **_process_user_trading_cycle**: Implementado con lógica real y persistencia de sesión
- **Integración Hexagonal**: `UserSessionPort` + `UserSessionAdapter` creados
- **Compatibilidad 100%**: Flujo legacy sin cambios

### Nuevos Componentes (Dec 20, 2025)
| Componente | Ubicación | Estado |
|------------|-----------|--------|
| `UserSessionPort` | `src/omnix/ports/driven/user_session_port.py` | ✅ CREADO |
| `UserSessionAdapter` | `src/omnix/infrastructure/adapters/user_session_adapter.py` | ✅ CREADO |
| Export actualizado | `src/omnix/ports/driven/__init__.py` | ✅ ACTUALIZADO |

### Language Detection AI-First Refactor (Dec 22, 2025)
**Arquitectura AI-First Verdadera**:
- **ELIMINADOS** diccionarios hardcodeados de detección de idioma (código basura)
- **INSTALADO** `fast-langdetect` (FastText-based, 80x más rápido que langdetect)
- **FLUJO AI-First**:
  - Textos largos (≥50 chars): fast-langdetect (FastText, muy preciso)
  - Textos cortos (<50 chars): Gemini AI (`gemini-2.0-flash-lite`, temp=0, max_tokens=5)
  - Fallback: fast-langdetect → langdetect → 'en'
- **OPTIMIZACIÓN**: Cliente Gemini singleton para reducir latencia
- **RESULTADO**: 12/12 tests pasando (9 cortos + 3 largos)
- **MAPEO gTTS**: ISO codes a códigos gTTS válidos (ej: zh → zh-CN)
- **Ubicación**: `omnix_services/ai_service/prompt_templates.py`, `omnix_services/voice_service/voice_controller.py`

### AI-First Multilingual Concurrency (Dec 19, 2025)
- **Implementado**: Detección de idioma thread-safe + persistencia Redis por usuario

---

## Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| Driven Ports | **16** (incluyendo UserSessionPort) |
| Driver Ports | **2** |
| **Total Ports** | **18** |
| Adapters | **20** (incluyendo UserSessionAdapter) |
| Ports activos | **0 (0%)** |
| Multi-User | **Fase 1 COMPLETADA** |
| Sistema en producción | **100% Legacy** |

El sistema legacy opera 24/7 en Railway. La arquitectura hexagonal V7.0 está completamente implementada pero **ningún port está activo**. Multi-usuario habilitado a nivel de código (Fase 2 pendiente para producción).

---

## Inventario Actual

### Driven Ports (16)

| Port | Adapter | Feature Flag |
|------|---------|--------------|
| ai_inference_port | gemini_adapter | (en AI) |
| ai_text_gateway_port | ai_gateway_shim | `USE_AI_PORT=false` |
| ai_voice_port | voice_adapter | `USE_VOICE_PORT=false` |
| cache_port | cache_adapter | `USE_CACHE_PORT=false` |
| database_port | database_adapter | `USE_DATABASE_PORT=false` |
| derivatives_port | derivatives_adapter | `USE_DERIVATIVES_PORT=false` |
| execution_port | execution_adapter | `USE_EXECUTION_PORT=false` |
| market_data_port | kraken_adapter | (en Trading) |
| market_intel_port | market_intel_adapter | `USE_MARKET_INTEL_PORT=false` |
| notification_port | notification_adapter | `USE_NOTIFICATION_PORT=false` |
| onchain_data_port | onchain_adapter | `USE_ONCHAIN_PORT=false` |
| optimization_port | optimization_adapter | `USE_OPTIMIZATION_PORT=false` |
| portfolio_port | portfolio_adapter | `USE_PORTFOLIO_PORT=false` |
| risk_control_port | risk_control_adapter | `USE_RISK_CONTROL_PORT=false` |
| trading_port | trading_adapter | `USE_TRADING_PORT=false` |
| **user_session_port** | **user_session_adapter** | **NUEVO (Dec 20)** |

### Driver Ports (2)

| Port | Adapter | Feature Flag |
|------|---------|--------------|
| telegram_port | telegram_adapter | `USE_TELEGRAM_PORT=false` |
| rest_api_port | Flask Blueprints | `USE_APP_LAYER=false` |

### Adapters (20)

```
ai_gateway_shim      cache_adapter       coherence_adapter
database_adapter     derivatives_adapter  execution_adapter
gemini_adapter       kraken_adapter      market_intel_adapter
notification_adapter onchain_adapter     optimization_adapter
portfolio_adapter    risk_adapter        risk_control_adapter
telegram_adapter     trading_adapter     voice_adapter
blockchain_info_provider  user_session_adapter (NUEVO)
```

---

## Flujo de Ejecución Actual

```
main.py
    │
    ├─[TRY]→ src/omnix/bootstrap/main_entry.run_omnix()
    │            │
    │            ├─ USE_APP_LAYER = false (default)
    │            │
    │            └─ initialize_services_legacy()
    │                    │
    │                    ├─ Importa omnix_services/* directamente
    │                    ├─ NO usa DI Container
    │                    └─ NO usa adapters V7
    │
    └─[CATCH]→ Fallback: EnterpriseTelegramBot() directamente
```

---

## Plan de Activación (12 Pasos)

| Paso | Flag | Riesgo | Estado |
|------|------|--------|--------|
| 1 | `USE_AI_PORT=true` | BAJO | PRÓXIMO |
| 2 | `USE_VOICE_PORT=true` | BAJO | Pendiente |
| 3 | `USE_MARKET_INTEL_PORT=true` | BAJO | Pendiente |
| 4 | `USE_EXECUTION_PORT=true` | MEDIO | Pendiente |
| 5 | `USE_RISK_CONTROL_PORT=true` | MEDIO | Pendiente |
| 6 | `USE_DERIVATIVES_PORT=true` | ALTO | Pendiente |
| 7 | `USE_PORTFOLIO_PORT=true` | MEDIO | Pendiente |
| 8 | `USE_OPTIMIZATION_PORT=true` | MEDIO | Pendiente |
| 9 | `USE_CACHE_PORT=true` | BAJO | Pendiente |
| 10 | `USE_DATABASE_PORT=true` | MEDIO | Pendiente |
| 11 | `USE_TELEGRAM_PORT=true` | MEDIO | Pendiente |
| 12 | `USE_APP_LAYER=true` | ALTO | Pendiente |

---

## Documentos Relacionados

- [MIGRATION_STATUS.md](MIGRATION_STATUS.md) - Estado consolidado V7.0
- [HEXAGONAL_MIGRATION_STATUS.md](current/HEXAGONAL_MIGRATION_STATUS.md) - Detalle de ports/adapters
- [README.md](README.md) - Índice de documentación

---

*Última actualización: 19 de Diciembre 2025*
