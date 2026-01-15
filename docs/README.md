# OMNIX V6.5.4e - Documentación

**Versión**: V6.5.4e INSTITUTIONAL+  
**Actualizado**: 15 de Enero 2026  
**Estado**: Producción 24/7 en Railway (100% Legacy)

---

## PROTOCOLO OBLIGATORIO

> **ANTES de hacer cambios de código**: Revisar esta documentación para entender el estado actual del sistema.
>
> **DESPUÉS de cambios significativos**: Actualizar la documentación correspondiente.

Ver `replit.md` para el checklist completo de prioridades de revisión.

---

## Cambios Recientes

### ADR-012: Learning Baseline Freeze & Official Day 1 (Jan 15, 2026)
- **ESTADO**: ✅ ADOPTADO - Day 1 oficial declarado
- **DECLARACIÓN**: 15 de Enero 2026 = Day 1 del track record oficial
- **LEARNING BASELINE**: Nov 2025 - Jan 14, 2026 (119 trades, LEGACY_ESTIMATED)
- **TRACK RECORD OFICIAL**: Jan 15, 2026+ (telemetría REAL)
- **MÉTRICAS RESET**: Trade count, win rate, profit factor (desde Day 1)
- **MÉTRICAS CARRY-OVER**: Balance ($984K), capital preservation (98.5%), config
- **DAY 30 REVIEW**: 13 de Febrero 2026 (meta: 100 trades, WR >45%)
- **REFERENCIA**: `docs/reference/adr/ADR-012-learning-baseline-freeze.md`

### ADR-011: Legacy Telemetry Backfill (Jan 15, 2026)
- **ESTADO**: ✅ IMPLEMENTADO - Data Quality corregido
- **PROBLEMA**: 119 trades sin coherence_score ni hmm_regime (pre-telemetría)
- **SOLUCIÓN**:
  - Track A: Backfill estimado basado en profit_pct/profit_loss
  - Track B: Columna `telemetry_source` (LEGACY_ESTIMATED vs REAL)
  - Track C: Métrica segmentada en Health Score
- **RESULTADO**: Data Quality 25% → 100% (con telemetría estimada marcada)
- **REFERENCIA**: `docs/reference/adr/ADR-011-legacy-telemetry-backfill.md`

### ADR-010: Capital Protection Metric Standard (Jan 15, 2026)
- **ESTADO**: ✅ IMPLEMENTADO - Métricas unificadas
- **PROBLEMA**: Inconsistencia entre "$1.2B Protected" vs "$267K Avoided"
- **SOLUCIÓN**: Sistema de dos métricas:
  - Primaria: "Est. Loss Avoided*" = Notional × 0.6%
  - Secundaria: "Notional Blocked" (transparencia)
- **WIDGETS ACTUALIZADOS**: quarantine.js, learninginsights.js, regimedetection.js, streamlit_app.py
- **REFERENCIA**: `docs/reference/adr/ADR-010-capital-protection-metric-standard.md`

### ADR-008: Opportunity Tracker (Jan 14, 2026)
- **ESTADO**: ✅ ADOPTADO - Framework de validación Day 30
- **PROPÓSITO**: Documentar oportunidades perdidas vs pérdidas evitadas sin cambiar thresholds
- **MÉTRICAS**:
  - Missed Opportunities: Trades bloqueados con buenas condiciones (Coh >50%, RANGING)
  - Losses Avoided: Trades correctamente bloqueados (Coh <30%, VOLATILE)
  - Net Opportunity: Balance diario para decisión data-driven
- **CRITERIO DAY 30**: Si missed > 20 AND profit > $3K → Test threshold 35%
- **FECHA REVISIÓN**: 13 de Febrero 2026
- **REFERENCIA**: `docs/reference/adr/ADR-008-opportunity-tracker.md`

### ADR-007: Coherence Threshold Calibration (Jan 14, 2026)
- **ESTADO**: ✅ IMPLEMENTADO - V6.5.4e
- **DIAGNÓSTICO**: Sistema sobre-protector bloqueando 48,937 trades en 7 días ($978.7M bloqueados)
- **CAUSA RAÍZ**: COHERENCE_GATE promedio 26.3% coherencia, BLACK_SWAN bloqueando 21,402 señales
- **SOLUCIÓN Phase 1**: Reducción de 5 puntos en umbrales adaptativos
  - LOW: 35% → 30%, MEDIUM: 45% → 40%, HIGH: 55% → 50%, EXTREME: 65% → 60%
  - EMA trigger: 25 → 20 puntos
- **IMPACTO ESPERADO**: Tasa de veto -15-20%, Win rate 37.8% → 42-45%
- **GUARDRAIL**: Rollback si drawdown > 3% en 48h
- **REFERENCIA**: `docs/reference/adr/ADR-007-coherence-threshold-calibration.md`

### ADR-006: Dashboard Improvement Proposals (Jan 13, 2026)
- **ESTADO**: Documentado, pendiente implementación
- **ANÁLISIS EXTERNO**: Dashboard evaluado en 7.5/10, objetivo 9.5/10
- **BUGS CRÍTICOS IDENTIFICADOS**:
  - WR Dir muestra 0.0% en Trade History (debería ser 37.8%)
  - Fee Eroded muestra 0 (debería ser 21)
  - "Protected" es métrica engañosa (renombrar a "Notional Blocked")
- **MEJORAS UX PROPUESTAS**:
  - System Health Score (indicador visual 0-100)
  - Live Status (qué hace el sistema ahora)
  - Quick Insights (insights auto-generados)
  - Calibration Progress (barra de progreso)
- **DOCUMENTACIÓN**:
  - ADR: `docs/reference/adr/ADR-006-dashboard-improvement-proposals.md`
  - Backlog: `docs/DASHBOARD_IMPROVEMENT_BACKLOG.md`
  - Auditoría: `docs/compliance/audits/DASHBOARD_UX_AUDIT_JAN13_2026.md`

### ADR-004: Position Sizing Hotfix (Jan 12, 2026)
- **ESTADO**: ✅ IMPLEMENTADO (27 tests pasados)
- **PROBLEMA DETECTADO**: Kelly operaba con max_position=20% ($62,500), cayendo en rango de trades que pierden
- **EVIDENCIA EMPÍRICA**:
  - Trades <$1K: **55.56% WR** → RENTABLES
  - Trades >$10K: **31% WR** → PIERDEN
- **HOTFIXES PROPUESTOS**:
  - Kelly max_position: 20% → **2%** ($62,500 → $20,000)
  - Position Hard Cap: **$20,000** máximo por trade
  - Spread mínimo: 5 bps → 25 bps
- **REFERENCIA**: `docs/reference/adr/ADR-004-position-sizing-hotfix.md`

### Dual Win Rate Framework - Dashboard UI Update (Jan 12, 2026)
- **INVESTIGACIÓN**: Descubierto que 21 trades ganaron en dirección pero perdieron por fees de Kraken (~0.26%)
- **DOS MÉTRICAS**:
  - **Precisión (37.82%)**: % de trades donde el precio se movió en la dirección predicha (pnl_percent > 0)
  - **Rentable (20.17%)**: % de trades rentables después de comisiones (profit_loss > 0)
- **UI ACTUALIZADA**:
  - Terminal Header: Muestra "Precisión" y "Rentable" con tooltips explicativos en español
  - Trade History Widget: Muestra ambos win rates + contador de "Fee Eroded" trades
  - Streamlit Overview: 5 columnas con ambas métricas y tooltips explicativos
- **FEE EROSION**: 21 trades identificados que acertaron dirección pero perdieron a fees
- **MITIGACIÓN**: Cap de $1,000 implementado para reducir impacto de fees en trades pequeños
- **ALINEACIÓN ADR-002**: Ambas métricas visibles con contexto claro (Honest Framing)
- **DOCUMENTACIÓN**: Ver `docs/investigations/TRADE_INVESTIGATION_JAN2026.md` para análisis completo

### Official Positioning & Language Guide (Jan 10, 2026)
- **ADR-003**: OMNIX officially positioned as "institutional-grade risk control infrastructure"
- **NEW DOCUMENT**: `docs/reference/omnix_official_language.md` - Complete language guide
- **TWO RESPONSE MODES**: 
  - Mode 1 (Positioning): Lead with architecture/preservation for general inquiries
  - Mode 2 (Honest Metrics): Show all data when specifically asked
- **KPI HIERARCHY**: Capital Preservation > Risk Events Blocked > System Integrity > Win Rate
- **Combined with ADR-002**: Honest Framing ensures transparency when metrics requested

### Daily Report Service - Brutal Honesty Monitoring (Jan 9, 2026)
- **NUEVO SERVICIO**: `DailyReportService` para monitoreo diario con honestidad brutal
- **MÉTRICAS REALES**: Conectado a PostgreSQL para win rate, balance, P&L reales
- **TABLA**: `paper_trading_daily_reports` para historial de auditoría
- **TELEGRAM**: Comando `/reporte_diario` para generar reporte
- **KELLY HONESTO**: Muestra "Modo Aprendizaje" cuando Kelly es negativo con tracking de costo
- **ADR**: `docs/reference/adr/ADR-001-brutal-honesty-monitoring.md`
- **RUNBOOK**: `docs/operations/runbooks/daily_monitor_report.md`

### Balance Precision Correction (Jan 10, 2026)
- **BALANCE CORREGIDO**: $984,188.74 → $984,801.27 (+$612.53 precisión)
- **P&L CORREGIDO**: -$19,848.65 → -$15,198.73 (suma real de 119 trades)
- **ROI CORREGIDO**: -1.98% → -1.52%
- **VERIFICADO**: Balance = $1M + P&L = $984,801.27 (diferencia $0.00)
- **AUDIT LOG**: Registrado en `balance_history` y `DATA_INTEGRITY_AUDIT_JAN2026.md`

### Data Integrity Audit Remediation (Jan 9, 2026)
- **BALANCE CORREGIDO**: $880,918 → $984,188.74 (gap de $103K resuelto)
- **WIN RATE CORREGIDO**: 37.8% → 20.17% (criterio: profit_loss > 0)
- **COHERENCE GATE FIX**: Removida condición CRITICAL que bloqueaba trades válidos
- **AUDIT REPORT**: `docs/compliance/audits/DATA_INTEGRITY_AUDIT_JAN2026.md`

### Shadow Portfolio + Cron Job + Dashboard Widget (Jan 9, 2026)
- **SHADOW PORTFOLIO COMPLETE**: Sistema de análisis contrafactual de trades bloqueados
- **CRON JOB**: `scripts/operations/run_shadow_portfolio.sh` para Railway (05:00 UTC diario)
- **DASHBOARD WIDGET**: Nueva pestaña "Shadow Portfolio" en Streamlit con:
  - Accuracy por tipo de veto (gráfico de barras)
  - Top missed opportunities (trades rentables bloqueados)
  - Recomendaciones de calibración de filtros
- **RUNBOOK**: `docs/operations/runbooks/shadow_portfolio_runner.md`
- Ver [REAL_SYSTEM_STATUS.md](REAL_SYSTEM_STATUS.md) para detalles

### Veto Tracking System + psycopg v3 Fix (Jan 7, 2026)
- **SISTEMA VETO TRACKING**: Persistencia real de capital protegido en PostgreSQL
- **FIX psycopg v3**: VetoRepository ahora compatible con `psycopg[binary]` (v3) y fallback a psycopg2
- **Dashboard Metrics Fix**: Panel superior ahora muestra ALL trades (119), no solo últimos 30 días
- Ver [REAL_SYSTEM_STATUS.md](REAL_SYSTEM_STATUS.md) para detalles completos

### Telegram Voice Service Fix (Dec 31, 2025)
- **ERROR CORREGIDO**: `UnboundLocalError: cannot access local variable 'asyncio'`
- **CAUSA RAÍZ**: Imports condicionales de `asyncio` dentro de `if`/`try` causaban conflictos de scope
- **FIX**: Eliminados 3 imports redundantes (líneas 3545, 4835, 6489) de `enterprise_bot.py`
- **REGLA**: Solo un `import asyncio` global (línea 10) - nunca imports condicionales
- Ver [REAL_SYSTEM_STATUS.md](REAL_SYSTEM_STATUS.md) para detalles

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
| [ADR-004](reference/adr/ADR-004-position-sizing-hotfix.md) | Position sizing hotfix |
| [ADR-007](reference/adr/ADR-007-coherence-threshold-calibration.md) | Coherence threshold calibration |
| [ADR-008](reference/adr/ADR-008-opportunity-tracker.md) | Opportunity Tracker (Day 30 Review) |
| [ADR-009](reference/adr/ADR-009-brevity-first-policy.md) | Brevity First - Respuestas directas |
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
| Trades | 119 | 500+ |
| Win Rate | 20.17% | 55%+ |
| P&L | -$15,811.26 | Positive |
| Timeline | - | 8-9 semanas |

**Meta**: Track record para $1M seed @ $11.5M pre-money.

---

*OMNIX V6.5.4d INSTITUTIONAL+ - Última actualización: 9 Enero 2026*
