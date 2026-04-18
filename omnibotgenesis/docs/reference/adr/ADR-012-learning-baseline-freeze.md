# ADR-012: Learning Baseline Freeze & Official Day 1 Declaration

**Status**: ADOPTADO  
**Fecha**: 15 de Enero 2026  
**Autor**: OMNIX Team  
**Contexto**: Establecer separación formal entre período de aprendizaje y track record oficial

---

## Resumen Ejecutivo

Este ADR declara oficialmente el **15 de Enero 2026** como **Day 1** del track record oficial de OMNIX V6.5.4e INSTITUTIONAL+. El período previo (Nov 2025 - Jan 14, 2026) queda congelado como "Learning Baseline" - datos históricos de calibración que no forman parte del track record oficial para inversores.

---

## Problema

El sistema ha acumulado 119 trades durante Nov-Dic 2025, pero estos fueron ejecutados:
- Sin telemetría real (campos estimados via ADR-011)
- Antes de calibración de thresholds (ADR-007)
- Con métricas inconsistentes (pre-ADR-010)

Para presentar un track record creíble a inversores, necesitamos una separación clara entre:
1. **Período de aprendizaje**: Datos usados para calibrar el sistema
2. **Track record oficial**: Datos con metodología consistente y verificable

---

## Decisión

### Day 1 Oficial: 15 de Enero 2026

A partir de esta fecha, todos los trades forman parte del track record oficial con:

| Criterio | Estado |
|----------|--------|
| Telemetría real | ✅ `telemetry_source = 'REAL'` |
| Thresholds calibrados | ✅ ADR-007 Phase 1 activo |
| Métricas estandarizadas | ✅ ADR-010 implementado |
| Data Quality | ✅ 100% campos completos |

### Learning Baseline: Nov 2025 - Jan 14, 2026

Este período queda congelado como referencia histórica:

| Aspecto | Valor |
|---------|-------|
| Trades | 119 |
| Telemetry Source | LEGACY_ESTIMATED |
| Balance Final | $984,801.27 |
| Propósito | Calibración y aprendizaje |

---

## Métricas: Reset vs Carry-over

### Métricas que REINICIAN desde Day 1

| Métrica | Valor Day 0 | Nota |
|---------|-------------|------|
| Trade Count (oficial) | 0 | Nuevo conteo |
| Win Rate (oficial) | N/A | Calculado solo con trades Day 1+ |
| Profit Factor (oficial) | N/A | Calculado solo con trades Day 1+ |
| Directional Accuracy (oficial) | N/A | Calculado solo con trades Day 1+ |
| Data Quality (REAL) | 0% → crece con trades | Solo telemetría REAL |

### Métricas que CONTINÚAN (Carry-over)

| Métrica | Valor | Nota |
|---------|-------|------|
| Balance | $984,801.27 | Capital real del sistema |
| Capital Preservation | 98.5% | Track record de protección |
| System Configuration | V6.5.4e | Versión calibrada |
| Risk Controls | Todos activos | 6-tier veto, MC, RMS |
| Veto History | 48,937+ | Evidencia de protección |

---

## Disclosure para Inversores

### Lenguaje Recomendado

**Para Pre-Day 1 (Learning Period):**
> "Durante Nov 2025 - Ene 2026, el sistema operó en modo de calibración acumulando 119 trades. Este período fue utilizado para ajustar thresholds, validar la arquitectura de vetos, y establecer la metodología de telemetría. Los datos de este período están marcados como 'estimados' y no forman parte del track record oficial."

**Para Post-Day 1 (Official Track Record):**
> "A partir del 15 de Enero 2026, OMNIX opera con telemetría completa en tiempo real, thresholds calibrados, y métricas estandarizadas. Todos los trades desde esta fecha forman el track record oficial verificable."

### Timeline para Presentaciones

```
Nov-Dic 2025     │ Ene 15, 2026      │ Feb 13, 2026
─────────────────┼───────────────────┼──────────────────
LEARNING PERIOD  │ OFFICIAL DAY 1    │ DAY 30 REVIEW
119 trades       │ Track record      │ Meta: 100 trades
Calibración      │ oficial inicia    │ WR target: >45%
Telemetría est.  │ Telemetría REAL   │ Decisión threshold
```

---

## Justificación

### Por qué Day 1 es el 15 de Enero 2026

1. **ADR-007 Activo** (Jan 14): Thresholds calibrados, veto rate optimizado
2. **ADR-010 Implementado** (Jan 15): Métricas de capital unificadas
3. **ADR-011 Completado** (Jan 15): Datos legacy marcados, telemetría segmentada
4. **Dashboard Operativo**: 19/19 widgets funcionando con métricas honestas
5. **Infraestructura Lista**: Health Score, Data Quality, Learning Engine activos

### Beneficios para Inversores

| Aspecto | Sin ADR-012 | Con ADR-012 |
|---------|-------------|-------------|
| Track record | 119 trades mezclados | Separación clara |
| Data quality | "25% real" ambiguo | "100% desde Day 1" |
| Credibilidad | Cuestionable | Verificable |
| Due diligence | Difícil | Transparente |

---

## Implementación

### Base de Datos

La separación ya existe via `telemetry_source`:
```sql
-- Learning Baseline (Pre-Day 1)
SELECT COUNT(*) FROM paper_trading_trades 
WHERE telemetry_source = 'LEGACY_ESTIMATED';
-- Result: 119

-- Official Track Record (Post-Day 1)
SELECT COUNT(*) FROM paper_trading_trades 
WHERE telemetry_source = 'REAL';
-- Result: 0 (crece con nuevos trades)
```

### Dashboard

El sistema ya muestra:
- **Data Quality**: Segmentado por telemetry_source
- **Health Score**: Calcula completitud real
- **Trade History**: Puede filtrar por período

### Documentación

Este ADR establece el marco. Los siguientes documentos se actualizan:
- `docs/REAL_SYSTEM_STATUS.md`: Sección Day 1 prominente
- `docs/README.md`: Entrada en Cambios Recientes
- `replit.md`: Referencia rápida

---

## Alternativas Consideradas

1. **No declarar Day 1**: Rechazado - track record ambiguo para inversores
2. **Eliminar trades pre-calibración**: Rechazado - perdemos contexto histórico
3. **Day 1 después de 100 trades**: Rechazado - retrasa innecesariamente

---

## Riesgos y Mitigación

| Riesgo | Mitigación |
|--------|------------|
| Inversores preguntan por datos pre-Day 1 | Disclosure claro: "período de calibración" |
| Track record oficial vacío inicialmente | Day 30 Review con meta de 100 trades |
| Confusión entre métricas | Dashboard segmenta claramente |

---

## Criterios de Éxito

| Criterio | Meta | Fecha |
|----------|------|-------|
| Day 30 trades | ≥ 100 | Feb 13, 2026 |
| Win Rate (Directional) | ≥ 45% | Feb 13, 2026 |
| Data Quality (REAL) | 100% | Ongoing |
| Capital Preservation | ≥ 98% | Ongoing |

---

## Referencias

- ADR-007: Coherence Threshold Calibration
- ADR-008: Opportunity Tracker
- ADR-010: Capital Protection Metric Standard
- ADR-011: Legacy Telemetry Backfill
- `docs/REAL_SYSTEM_STATUS.md`: Estado actual del sistema
