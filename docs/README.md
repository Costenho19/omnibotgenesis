# OMNIX V6.5.4d - Documentación

**Versión**: V6.5.4d INSTITUTIONAL+  
**Actualizado**: 18 de Diciembre 2025  
**Estado**: Producción 24/7 en Railway (100% Legacy)

---

## Navegación Rápida

### Estado Actual
| Documento | Descripción |
|-----------|-------------|
| [Migración V7.0](MIGRATION_STATUS.md) | Estado de arquitectura hexagonal (17 ports, 19 adapters, 0% activación) |
| [Hexagonal Status](current/HEXAGONAL_MIGRATION_STATUS.md) | Detalle técnico de ports y adapters |
| [Mapa Funcional](current/COMPLETE_FUNCTIONALITY_MAP.md) | Sistema legacy (11 dominios, 346 archivos) |

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
├── MIGRATION_STATUS.md       <- Estado V7.0 consolidado (fuente de verdad)
│
├── current/                  <- Documentos "vivos" (estado actual)
│   ├── HEXAGONAL_MIGRATION_STATUS.md  <- Ports/Adapters detallado
│   ├── COMPLETE_FUNCTIONALITY_MAP.md  <- Referencia sistema legacy
│   ├── TECHNICAL_DEBT.md              <- Issues conocidos
│   └── TRADING_OPERATIONS.md          <- Operaciones de trading
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
│  ├── 15 Driven Ports + 2 Driver Ports = 17 ports                │
│  ├── 19 Adapters implementados                                  │
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

*OMNIX V6.5.4d INSTITUTIONAL+ - Última actualización: 18 Dic 2025*
