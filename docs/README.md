# OMNIX V6.5.4d - Documentación

**Versión**: V6.5.4d INSTITUTIONAL+  
**Actualizado**: 16 de Diciembre 2025  
**Estado**: Producción 24/7 en Railway

---

## Navegación Rápida

### Desarrollo
| Documento | Descripción |
|-----------|-------------|
| [Arquitectura](current/ARCHITECTURE.md) | Sistema actual V6.5.4d |
| [Migración V7.0](MIGRATION_STATUS.md) | Estado de arquitectura hexagonal |
| [Deuda Técnica](current/TECHNICAL_DEBT.md) | Issues conocidos |

### Operaciones
| Documento | Descripción |
|-----------|-------------|
| [Deployment](operations/DEPLOYMENT.md) | Guía Railway |
| [Trading Operations](current/TRADING_OPERATIONS.md) | Perfiles y risk management |
| [Configuración](operations/CONFIGURACION_OPTIMIZADA.md) | Parámetros optimizados |

### Inversores
| Documento | Descripción |
|-----------|-------------|
| [One Pager](business/investor/one_pager.md) | Resumen ejecutivo |
| [Proyecciones](business/investor/financial_projections.md) | Forecast financiero |
| [Pitch Deck](business/investor/pitch_deck.html) | Presentación |

### Referencia Técnica
| Documento | Descripción |
|-----------|-------------|
| [Mapa Funcional](current/COMPLETE_FUNCTIONALITY_MAP.md) | 11 dominios, 346 archivos |
| [Trazabilidad](reference/TRACEABILITY_MATRIX.md) | 123 componentes mapeados |
| [ADR-001](reference/adr/ADR-001-hexagonal.md) | Decisión hexagonal |

---

## Estructura de Carpetas

```
docs/
├── README.md                 ← Este archivo
├── MIGRATION_STATUS.md       ← Estado V7.0
│
├── current/                  ← Estado actual V6.5.4d
│   ├── ARCHITECTURE.md       
│   ├── TECHNICAL_DEBT.md     
│   └── TRADING_OPERATIONS.md 
│
├── operations/               ← Guías operativas
│   ├── DEPLOYMENT.md         
│   └── CONFIGURACION_OPTIMIZADA.md
│
├── business/                 ← Documentos de negocio
│   ├── investor/             
│   └── B2C_SAAS_PLAN.md      
│
├── reference/                ← Referencia técnica
│   ├── TRACEABILITY_MATRIX.md
│   └── adr/                  
│
├── compliance/               ← Auditorías
│   └── audits/               
│
└── history/                  ← Archivo histórico
    ├── 2025-11/              
    └── 2025-12/              
```

---

## Estado del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                    OMNIX V6.5.4d INSTITUTIONAL+                  │
├─────────────────────────────────────────────────────────────────┤
│  INTERFACES                                                      │
│  ├── Telegram Bot (enterprise_bot.py)                           │
│  ├── Flask Dashboard (puerto 5000)                              │
│  └── Streamlit Dashboard (puerto 8080)                          │
├─────────────────────────────────────────────────────────────────┤
│  CORE ENGINES                                                    │
│  ├── AutoTradingBot V6.5.4d (multi-crypto scanner)              │
│  ├── CoherenceEngine V6.5 ULTRA (6-tier veto)                   │
│  ├── Risk Guardian V5.4 (drawdown protection)                   │
│  └── ARES V1/V2 (Swing + Scalping)                              │
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

## Migración V7.0

| Métrica | Estado |
|---------|--------|
| Estructura hexagonal | 100% ✅ |
| Ports definidos | 8/8 ✅ |
| Adapters implementados | 9/9 ✅ |
| Activación producción | 37.5% (3/8 ports) |

Ver [MIGRATION_STATUS.md](MIGRATION_STATUS.md) para detalles.

---

## Track Record

| Métrica | Actual | Objetivo |
|---------|--------|----------|
| Trades | ~30 | 500+ |
| Win Rate | TBD | 55%+ |
| Timeline | - | 8-9 semanas |

**Meta**: Track record para $1M seed @ $11.5M pre-money.

---

*OMNIX V6.5.4d INSTITUTIONAL+*
