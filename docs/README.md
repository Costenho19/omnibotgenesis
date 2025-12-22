# OMNIX V6.5.4d - Documentación

**Versión**: V6.5.4d INSTITUTIONAL+  
**Actualizado**: 22 de Diciembre 2025  
**Estado**: Producción 24/7 en Railway (100% Legacy)

---

## PROTOCOLO OBLIGATORIO

> **ANTES de hacer cambios de código**: Revisar esta documentación para entender el estado actual del sistema.
>
> **DESPUÉS de cambios significativos**: Actualizar la documentación correspondiente.

Ver `replit.md` para el checklist completo de prioridades de revisión.

---

## Cambios Recientes

### Language Detection AI-First (Dec 22, 2025)
- **ELIMINADOS** diccionarios hardcodeados de detección de idioma
- **INSTALADO** `fast-langdetect` (FastText-based, 80x más rápido)
- **FLUJO**: Textos largos (≥50 chars) → FastText | Textos cortos (<50 chars) → Gemini AI
- **MAPEO gTTS**: ISO codes a códigos gTTS válidos (ej: zh → zh-CN)
- **12/12 tests pasando**

### Multi-Usuario Fase 1 COMPLETADA (Dec 20, 2025)
- **UserSessionManager EXISTE**: 562 líneas en `omnix_core/sessions/user_session_manager.py`
- **Funciones parametrizadas con user_id**: 6 funciones core ahora aceptan user_id opcional
- **Integración Hexagonal**: `UserSessionPort` y `UserSessionAdapter` creados
- **Compatibilidad 100%**: Flujo legacy sigue funcionando sin cambios
- **Pendiente Fase 2**: Desacoplar configuración por usuario, migrar protecciones ARP
- **Documento**: [MULTI_USER_ARCHITECTURE.md](current/MULTI_USER_ARCHITECTURE.md) (secciones 7.4 y 7.5)

### Nuevos Componentes Hexagonales (Dec 20, 2025)
| Componente | Ubicación |
|------------|-----------|
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
| [Migración V7.0](MIGRATION_STATUS.md) | Estado de arquitectura hexagonal (19 ports, 21 adapters, 0% activación) |
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
│  ├── 16 Driven Ports + 3 Driver Ports = 19 ports                │
│  ├── 21 Adapters implementados                                  │
│  ├── 120/120 tests pasando                                      │
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
| Trades | ~30 | 500+ |
| Win Rate | TBD | 55%+ |
| Timeline | - | 8-9 semanas |

**Meta**: Track record para $1M seed @ $11.5M pre-money.

---

*OMNIX V6.5.4d INSTITUTIONAL+ - Última actualización: 22 Dic 2025*
