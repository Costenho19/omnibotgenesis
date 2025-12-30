# OMNIX V6.5.4d - Documentación

**Versión**: V6.5.4d INSTITUTIONAL+  
**Actualizado**: 30 de Diciembre 2025  
**Estado**: Producción 24/7 en Railway (100% Legacy)

---

## PROTOCOLO OBLIGATORIO

> **ANTES de hacer cambios de código**: Revisar esta documentación para entender el estado actual del sistema.
>
> **DESPUÉS de cambios significativos**: Actualizar la documentación correspondiente.

Ver `replit.md` para el checklist completo de prioridades de revisión.

---

## Cambios Recientes

### Type Safety Hotfix - Coherence Engine (Dec 30, 2025)
- **ERROR CORREGIDO**: `">= not supported between instances of 'str' and 'int'"` en Coherence Gate
- **NUEVAS FUNCIONES**:
  - `normalize_signal()` - Convierte strings "BUY"/"SELL" a Enum Signal
  - `normalize_strategy_signal()` - Normaliza StrategySignal completo (signal→Enum, confidence→float)
- **BLINDAJE safe_float()** en todas las comparaciones >= de CoherenceEngine
- **16 tests nuevos** en `tests/test_coherence_type_safety.py`
- **Total tests Dec 30**: 43 (27 críticos + 16 type safety)
- Ver [TYPE_SAFETY_HOTFIX_DEC30_2025.md](history/2025-12/TYPE_SAFETY_HOTFIX_DEC30_2025.md) para detalles

### Critical Audit Fixes + ENV Control (Dec 30, 2025)
- **AUDITORÍA CRÍTICA COMPLETADA**: 4 fixes de seguridad implementados
  - Coherence Gate ahora FAIL-CLOSED (excepciones → BLOCKED)
  - MC Veto semántica corregida: ER<0% → BLOCKED, WR<50% → SIZE_REDUCE
  - DecisionPayload extendido con campos de auditoría
- **TRACK_RECORD_MODE controlado por ENV** (default=false)
  - Rollback sin redeploy: `TRACK_RECORD_MODE=true` en Railway Variables
- **27/27 tests pasando** incluyendo verificación de código fuente
- **Campos de auditoría** en cada decisión: `track_record_mode`, `low_vol_mode`
- Ver [REAL_SYSTEM_STATUS.md](REAL_SYSTEM_STATUS.md) para detalles completos

### V1.0.5 - OHLC Data Fix (Dec 26, 2025)
- **CRÍTICO**: `generate_signal()` nunca se ejecutaba porque `prices=0`
- **Root Cause**: `TradingServiceEnterprise` faltaba método `get_ohlc()` delegado
- **Fix**: Añadido método delegado que reenvía a `self.kraken.get_ohlc()`
- **Resultado**: EMA Signal ahora puede generar señales reales
- Ver [REAL_SYSTEM_STATUS.md](REAL_SYSTEM_STATUS.md) para detalles completos

### Multi-User Phase 3b COMPLETADA (Dec 22, 2025)
- **AuthorizationService INTEGRADO** en 5 archivos con RBAC completo
- **17 hardcoded checks reemplazados** con verificación de permisos
- **5 roles B2C SaaS**: FREE < BASIC < PRO < PREMIUM < OWNER
- **15 permisos granulares** para trading, análisis, alertas
- **Harold = OWNER** en BD con paper trading activo
- **39/39 authorization tests passing**
- **Documento**: [MULTI_USER_ARCHITECTURE.md](current/MULTI_USER_ARCHITECTURE.md) - Guía completa de uso

### Language Detection AI-First (Dec 22, 2025)
- **ELIMINADOS** diccionarios hardcodeados de detección de idioma
- **INSTALADO** `fast-langdetect` (FastText-based, 80x más rápido)
- **FLUJO**: Textos largos (≥50 chars) → FastText | Textos cortos (<50 chars) → Gemini AI
- **MAPEO gTTS**: ISO codes a códigos gTTS válidos (ej: zh → zh-CN)
- **12/12 tests pasando**

### Nuevos Componentes Hexagonales (Dec 22, 2025)
| Componente | Ubicación |
|------------|-----------|
| `AuthorizationPort` | `src/omnix/ports/driven/authorization_port.py` |
| `AuthorizationAdapter` | `src/omnix/infrastructure/adapters/authorization_adapter.py` |
| `UserSessionPort` | `src/omnix/ports/driven/user_session_port.py` |
| `UserSessionAdapter` | `src/omnix/infrastructure/adapters/user_session_adapter.py` |

### AI-First Multilingual Concurrency (Dec 19, 2025)
- **Detección de idioma segura para concurrencia**: `threading.Lock` + `asyncio.to_thread()`
- **Persistencia Redis por usuario**: `omnix:user_language:{chat_id}` con TTL 24h
- **Placeholders universales en inglés**: AI genera respuestas localizadas

---

## Navegación Rápida

### Estado Actual
| Documento | Descripción |
|-----------|-------------|
| [Migración V7.0](MIGRATION_STATUS.md) | Estado de arquitectura hexagonal (20 ports, 22 adapters, 0% activación) |
| [Estado REAL](REAL_SYSTEM_STATUS.md) | **FUENTE DE VERDAD** - Estado de producción Railway |
| [Hexagonal Status](current/HEXAGONAL_MIGRATION_STATUS.md) | Detalle técnico de ports y adapters |
| [Mapa Funcional](current/COMPLETE_FUNCTIONALITY_MAP.md) | Sistema legacy (11 dominios, 346 archivos) |
| [Multi-Usuario](current/MULTI_USER_ARCHITECTURE.md) | **CRÍTICO** - Auditoría y plan multi-tenant |

### Operaciones
| Documento | Descripción |
|-----------|-------------|
| [Deployment](operations/DEPLOYMENT.md) | Guía Railway |
| [Runbooks](operations/) | Runbooks de activación de ports |
| [Trading Operations](current/TRADING_OPERATIONS.md) | Perfiles y risk management |

### Inversores
| Documento | Descripción |
|-----------|-------------|
| [One Pager](business/investor/one_pager.md) | Resumen ejecutivo |
| [Proyecciones](business/investor/financial_projections.md) | Forecast financiero |
| [Pitch Deck](business/investor/pitch_deck.html) | Presentación |

### Referencia Técnica
| Documento | Descripción |
|-----------|-------------|
| [Trazabilidad](reference/TRACEABILITY_MATRIX.md) | 123 componentes mapeados |
| [ADR-001](reference/adr/ADR-001-hexagonal.md) | Decisión hexagonal |
| [Deuda Técnica](current/TECHNICAL_DEBT.md) | Issues conocidos |

---

## Estructura de Carpetas

```
docs/
├── README.md                 <- Este archivo (índice)
├── REAL_SYSTEM_STATUS.md     <- Estado REAL de producción (fuente de verdad)
├── MIGRATION_STATUS.md       <- Estado V7.0 consolidado (arquitectura)
│
├── current/                  <- Documentos "vivos" (estado actual)
│   ├── HEXAGONAL_MIGRATION_STATUS.md  <- Ports/Adapters detallado
│   ├── COMPLETE_FUNCTIONALITY_MAP.md  <- Referencia sistema legacy
│   ├── TECHNICAL_DEBT.md              <- Issues conocidos
│   ├── TRADING_OPERATIONS.md          <- Operaciones de trading
│   └── MULTI_USER_ARCHITECTURE.md     <- Auditoría multi-tenant
│
├── operations/               <- Runbooks y guías operativas
│   ├── DEPLOYMENT.md
│   ├── RUNBOOK_*_ACTIVATION.md        <- Runbooks por port
│   └── CONFIGURACION_OPTIMIZADA.md
│
├── reference/                <- Referencia técnica estática
│   ├── TRACEABILITY_MATRIX.md
│   └── adr/                           <- Architecture Decision Records
│
├── business/                 <- Documentos de negocio
│   └── investor/                      <- Pitch deck, proyecciones
│
├── compliance/               <- Auditorías (solo actuales)
│   └── audits/
│
└── history/                  <- Archivo histórico (congelado)
    ├── 2025-11/                       <- Noviembre 2025
    └── 2025-12/                       <- Diciembre 2025
```

---

## Estado del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                    OMNIX V6.5.4d INSTITUTIONAL+                  │
├─────────────────────────────────────────────────────────────────┤
│  PRODUCCIÓN (Railway)                                            │
│  ├── 100% código legacy operando 24/7                           │
│  ├── 0% arquitectura hexagonal activa                           │
│  └── Feature flags: TODOS en false                              │
├─────────────────────────────────────────────────────────────────┤
│  ARQUITECTURA V7.0 (Implementada, no activa)                    │
│  ├── 17 Driven Ports + 3 Driver Ports = 20 ports                │
│  ├── 22 Adapters implementados                                  │
│  ├── 164 tests totales (10 críticos en CI workflow)             │
│  └── Patrón: Strangler Fig (activación gradual)                 │
├─────────────────────────────────────────────────────────────────┤
│  INTERFACES                                                      │
│  ├── Telegram Bot (enterprise_bot.py)                           │
│  ├── Flask Dashboard (puerto 5000)                              │
│  └── Streamlit Dashboard (puerto 8080)                          │
├─────────────────────────────────────────────────────────────────┤
│  DATA LAYER                                                      │
│  ├── PostgreSQL (42+ tablas)                                    │
│  ├── Redis (cache + estado)                                     │
│  └── DatabaseGateway (connection pool)                          │
├─────────────────────────────────────────────────────────────────┤
│  EXTERNAL APIs                                                   │
│  ├── Kraken (crypto)                                            │
│  ├── Gemini 2.0 Flash (AI)                                      │
│  └── Tavily (web search)                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Próximo Paso: Activación de Ports

| Paso | Flag | Estado |
|------|------|--------|
| 1 | `USE_AI_PORT=true` | PRÓXIMO - Riesgo bajo, tiene fallback |
| 2-12 | Resto de ports | Pendiente (ver MIGRATION_STATUS.md) |

Ver [MIGRATION_STATUS.md](MIGRATION_STATUS.md) para plan completo de activación.

---

## Track Record

| Métrica | Actual | Objetivo |
|---------|--------|----------|
| Trades | 109 | 500+ |
| Win Rate | 22% | 55%+ |
| P&L | -$14,942.94 | Positive |
| Timeline | - | 8-9 semanas |

**Meta**: Track record para $1M seed @ $11.5M pre-money.

---

*OMNIX V6.5.4d INSTITUTIONAL+ - Última actualización: 29 Dic 2025*
