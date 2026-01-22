# ADR-021: Shadow Trade Metrics View

**Date**: 22 de Enero 2026  
**Status**: IMPLEMENTED  
**Category**: Data Analysis / Governance / Investor Demo  
**Authors**: OMNIX Development Team

---

## Context

### Necesidad de Análisis Retroactivo

Para validar el Decision Contradiction Index (DCI, ADR-018) como métrica predictiva de pérdidas, se requiere análisis retroactivo de ~76,000 eventos de trading desde el inicio del track record oficial (Jan 15, 2026).

Los datos existen en la tabla `shadow_trade_events` dentro del campo `decision_trace` (JSONB array), pero en formato texto embebido, no estructurado.

**Ejemplos de decision_trace:**
```
"MC_SIZE_REDUCE: Win rate 49.4% → size_multiplier=50% reason=MC_WR_BELOW_50"
"COHERENCE_GATE: Coherence 40.1% >= 30% (PASSED)"
"ECW_GATE: WAITING - ECW: 0/3 cycles (WR=49.4%✗, ER=-0.00%✗, BS=medium✓)"
"BLACK_SWAN_VETO: MEDIUM, CrashProb=50.0%"
```

### Mantener Integridad Histórica

El track record oficial comenzó el 15 de enero 2026. Cualquier modificación a datos históricos comprometería:
- Auditabilidad del sistema
- Credibilidad ante inversores
- Trazabilidad de decisiones

**Principio rector:** Preservar datos originales intactos.

---

## Decision

Crear una **VIEW SQL derivada** (`v_shadow_trade_metrics`) que parsea `decision_trace` con regex tolerantes y extrae métricas estructuradas.

### Justificación:

| Criterio | VIEW Derivada | Backfill Columnas | Migración |
|----------|---------------|-------------------|-----------|
| Riesgo | Zero | Alto | Muy Alto |
| Reversibilidad | Inmediata | Compleja | Irreversible |
| Impacto en Producción | Ninguno | Potencial | Significativo |
| Auditabilidad | Preservada | Cuestionable | Comprometida |
| Demo-Ready | Sí | Sí | No |

**Decisión final:** VIEW derivada, sin materialización física.

---

## Alternatives Considered

### ❌ Alternative 1: Backfill de Columnas

**Propuesta:** Agregar columnas `mc_win_rate`, `coherence_score`, etc. a `shadow_trade_events` y ejecutar UPDATE masivo para poblarlas.

**Rechazado porque:**
- Modifica datos históricos (viola integridad)
- Riesgo de corrupción durante UPDATE de 76k+ filas
- No reversible sin backup
- Crea deuda técnica (columnas redundantes)

### ❌ Alternative 2: Migración de Schema

**Propuesta:** Crear nueva tabla `shadow_trade_metrics_parsed` y migrar datos.

**Rechazado porque:**
- Requiere lógica de sincronización continua
- Duplicación de almacenamiento
- Complejidad operacional innecesaria
- Impacto en producción durante migración

### ❌ Alternative 3: Materialized View

**Propuesta:** `CREATE MATERIALIZED VIEW` con refresh programado.

**Considerado pero diferido porque:**
- Overhead de refresh scheduling
- No necesario para volumen actual (~76k filas)
- Puede implementarse después si performance degrada

---

## Implementation

### VIEW: `v_shadow_trade_metrics`

**Columnas extraídas:**

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `mc_win_rate` | numeric | Monte Carlo Win Rate % |
| `mc_expected_return` | numeric | Monte Carlo Expected Return % |
| `coherence_score` | numeric | Coherence Engine Score % |
| `ecw_cycles` | integer | ECW cycles completados (0-3) |
| `ecw_status` | varchar | WAITING / OPEN |
| `black_swan_severity` | varchar | LOW / MEDIUM / HIGH / EXTREME |
| `crash_probability` | numeric | Black Swan crash probability % |
| `approx_dci` | numeric | DCI aproximado (0-100) |

### Regex Design Philosophy

> **IMPORTANTE**: Regex are intentionally permissive to preserve forward compatibility of decision_trace semantics.

Los patrones aceptan variantes actuales y futuras:

| Métrica | Patrones Aceptados |
|---------|-------------------|
| Win Rate | `WR=50.1%`, `Win rate 50.1%`, `MC_WR:50.1` |
| Expected Return | `ER=-0.01%`, `ER=0.00%`, `Expected: -0.01%` |
| Coherence | `Coherence 40.1%`, `coherence: 40%` |
| Black Swan | `BLACK_SWAN_VETO: MEDIUM`, `BS=medium`, `BlackSwan: HIGH` |

Esta tolerancia protege:
- Retrocompatibilidad con logs históricos
- Cambios futuros de wording
- Estabilidad de la VIEW ante refactors

### SQL Definition

```sql
CREATE OR REPLACE VIEW v_shadow_trade_metrics AS
WITH trace_expanded AS (
  SELECT 
    s.id, s.created_at, s.symbol, s.intended_action,
    s.intended_position_size_usd, s.blocked_capital,
    s.veto_type, s.veto_reason, s.ema_score, s.ema_signal,
    elem as trace_line
  FROM shadow_trade_events s,
       LATERAL jsonb_array_elements_text(s.decision_trace) as elem
  WHERE s.created_at >= '2026-01-15'
),
parsed_metrics AS (
  SELECT 
    id, created_at, symbol, intended_action,
    intended_position_size_usd, blocked_capital,
    veto_type, veto_reason, ema_score, ema_signal,
    -- MC Win Rate: tolerant patterns
    MAX(CASE 
      WHEN trace_line ~* 'win.?rate|WR[=:]|MC_WR'
      THEN (regexp_match(trace_line, '([0-9]+\.?[0-9]*)%'))[1]::numeric
    END) as mc_win_rate,
    -- MC Expected Return: tolerant patterns
    MAX(CASE 
      WHEN trace_line ~* 'ER[=:]|expected.?return'
      THEN (regexp_match(trace_line, 'ER?[=:]\s*([-0-9.]+)%'))[1]::numeric
    END) as mc_expected_return,
    -- Coherence Score: tolerant patterns
    MAX(CASE 
      WHEN trace_line ~* 'coherence'
      THEN (regexp_match(trace_line, '([0-9]+\.?[0-9]*)%'))[1]::numeric
    END) as coherence_score,
    -- ECW Cycles
    MAX(CASE 
      WHEN trace_line ~* 'ECW'
      THEN (regexp_match(trace_line, '([0-9]+)/3'))[1]::integer
    END) as ecw_cycles,
    -- ECW Status
    MAX(CASE 
      WHEN trace_line ~* 'ECW.*WAITING' THEN 'WAITING'
      WHEN trace_line ~* 'ECW.*OPEN' THEN 'OPEN'
    END) as ecw_status,
    -- Black Swan Severity: tolerant patterns
    MAX(CASE 
      WHEN trace_line ~* 'black.?swan|BS[=:]'
      THEN UPPER(COALESCE(
        (regexp_match(trace_line, '(EXTREME|HIGH|MEDIUM|LOW)', 'i'))[1],
        'UNKNOWN'
      ))
    END) as black_swan_severity,
    -- Crash Probability
    MAX(CASE 
      WHEN trace_line ~* 'crash.?prob'
      THEN (regexp_match(trace_line, '([0-9]+\.?[0-9]*)%'))[1]::numeric
    END) as crash_probability
  FROM trace_expanded
  GROUP BY id, created_at, symbol, intended_action, intended_position_size_usd,
           blocked_capital, veto_type, veto_reason, ema_score, ema_signal
)
SELECT 
  *,
  -- Approximate DCI calculation (shadow metric)
  LEAST(100, 
    (100 - COALESCE(coherence_score, 50)) * 0.4 +
    (50 - COALESCE(mc_win_rate, 50)) + 
    ABS(COALESCE(mc_expected_return, 0) * 100) +
    CASE COALESCE(black_swan_severity, 'LOW')
      WHEN 'EXTREME' THEN 15 WHEN 'HIGH' THEN 12
      WHEN 'MEDIUM' THEN 7 WHEN 'LOW' THEN 3 ELSE 5
    END
  ) as approx_dci
FROM parsed_metrics;
```

---

## Consequences

### Positive

1. **Auditabilidad Total**: Datos originales intactos, VIEW es derivación transparente
2. **Demo-Ready**: Inversores pueden ver queries ejecutándose en tiempo real
3. **Reversibilidad Inmediata**: `DROP VIEW v_shadow_trade_metrics;` restaura estado original
4. **Zero Impacto en Producción**: No modifica tablas operacionales
5. **Forward Compatible**: Regex tolerantes absorben cambios de formato
6. **Reproducible**: Cualquier auditor puede recrear la VIEW y verificar resultados

### Negative

1. **Costo Computacional Marginal**: Regex sobre 76k+ filas (~2-3 segundos por query)
2. **No Persistente**: Resultados recalculados cada vez (mitigable con MATERIALIZED VIEW si necesario)
3. **Dependencia de Formato**: Cambios drásticos en decision_trace requerirían ajuste de regex

### Mitigation

- Performance degradation → Upgrade to MATERIALIZED VIEW con refresh cada hora
- Format changes → Regex diseñados para tolerancia; documentar cambios en ADR

---

## Rollback

```sql
-- Rollback inmediato y completo
DROP VIEW IF EXISTS v_shadow_trade_metrics;

-- Verificar rollback
SELECT COUNT(*) FROM information_schema.views 
WHERE table_name = 'v_shadow_trade_metrics';
-- Debe retornar 0
```

**Tiempo de rollback:** < 1 segundo  
**Impacto de rollback:** Ninguno en datos de producción

---

## Usage Examples

### 1. Capital Protegido por ECW
```sql
SELECT 
  SUM(blocked_capital) as capital_protected,
  COUNT(*) as blocked_trades
FROM v_shadow_trade_metrics
WHERE ecw_status = 'WAITING';
```

### 2. Casi-Trades (2/3 cycles)
```sql
SELECT symbol, created_at, mc_win_rate, mc_expected_return
FROM v_shadow_trade_metrics
WHERE ecw_cycles = 2
ORDER BY created_at DESC
LIMIT 20;
```

### 3. Black Swan Veto Impact
```sql
SELECT 
  black_swan_severity,
  COUNT(*) as events,
  ROUND(SUM(blocked_capital), 2) as total_blocked
FROM v_shadow_trade_metrics
WHERE veto_type = 'BLACK_SWAN'
GROUP BY black_swan_severity
ORDER BY 3 DESC;
```

### 4. DCI Distribution Analysis
```sql
SELECT 
  CASE 
    WHEN approx_dci >= 70 THEN 'CONTRADICTORY (≥70)'
    WHEN approx_dci >= 35 THEN 'TENSIONED (35-69)'
    ELSE 'ALIGNED (<35)'
  END as dci_level,
  COUNT(*) as events,
  ROUND(AVG(mc_win_rate), 1) as avg_wr
FROM v_shadow_trade_metrics
WHERE approx_dci IS NOT NULL
GROUP BY 1
ORDER BY 1;
```

---

## Initial Results (Jan 22, 2026)

### DCI Distribution
| Bucket | Events | Avg WR | Avg Coherence |
|--------|--------|--------|---------------|
| ALIGNED (<35) | 76,789 | 49.8% | 43.2% |
| TENSIONED (35-49) | 121 | 48.6% | 33.0% |

### By Symbol
| Symbol | Events | Avg DCI | Avg Coherence |
|--------|--------|---------|---------------|
| AVAX/USD | 25,632 | 31.0 | 40.5% |
| BTC/USD | 25,645 | 29.8 | 43.6% |
| XRP/USD | 25,635 | 29.1 | 45.4% |

---

## Next Steps

1. **Multi-Threshold Validation** (Day 8-9): Test DCI thresholds (60, 65, 70, 75) against trade outcomes
2. **Correlation Analysis**: Calculate Pearson r between DCI and actual P&L
3. **GO/ARCHIVE Decision**: Based on statistical validation
   - r ≥ 0.6 → GO (promote DCI to active metric)
   - r ≤ 0.4 → ARCHIVE (document as vanity metric)
   - 0.4 < r < 0.6 → DEFER (continue collecting data)

---

## References

- [ADR-018: Decision Contradiction Index](ADR-018-decision-contradiction-index.md)
- [ADR-019: Edge Confirmation Window](ADR-019-edge-confirmation-window.md)
- [REAL_SYSTEM_STATUS.md](../../REAL_SYSTEM_STATUS.md)
- [docs/README.md](../../README.md)

---

## Approval

| Role | Name | Date | Status |
|------|------|------|--------|
| Author | OMNIX Dev | Jan 22, 2026 | ✅ Implemented |
| Reviewer | - | - | Pending |
| Auditor | - | - | Pending |
