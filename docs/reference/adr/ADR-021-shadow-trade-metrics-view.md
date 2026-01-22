# ADR-021: Shadow Trade Metrics View

**Date**: 22 de Enero 2026  
**Status**: IMPLEMENTED  
**Category**: Data Analysis / Investor Demo

---

## Context

Para el análisis retroactivo del DCI (Decision Contradiction Index) y otras métricas de trading, necesitamos extraer datos parseados del campo `decision_trace` (JSONB array) en la tabla `shadow_trade_events`.

**Problema:**
- `decision_trace` contiene strings de texto con métricas embebidas
- No hay columnas separadas para MC_WR, MC_ER, ECW status, etc.
- Necesitamos análisis multi-threshold para validar DCI como métrica predictiva

**Ejemplos de decision_trace:**
```
"MC_SIZE_REDUCE: Win rate 49.4% → size_multiplier=50% reason=MC_WR_BELOW_50"
"COHERENCE_GATE: Coherence 40.1% >= 30% (PASSED)"
"ECW_GATE: WAITING - ECW: 0/3 cycles (WR=49.4%✗, ER=-0.00%✗, BS=medium✓)"
"BLACK_SWAN_VETO: MEDIUM, CrashProb=50.0%"
```

---

## Decision

Crear una **VIEW** (no tabla física) que parsea decision_trace con regex y extrae métricas estructuradas.

### Justificación:
1. **Zero Risk**: VIEW es 100% reversible con `DROP VIEW`
2. **No Migration**: No cambia schema de producción
3. **Demo-Ready**: Usable en queries y dashboard sin modificar datos
4. **Eficiente**: PostgreSQL regex en 76k+ rows es rápido

---

## Implementation

### VIEW: `v_shadow_trade_metrics`

**Columnas extraídas:**

| Columna | Tipo | Descripción | Patrón Regex |
|---------|------|-------------|--------------|
| `mc_win_rate` | numeric | Monte Carlo Win Rate % | `Win rate ([0-9.]+)%` o `WR=([0-9.]+)%` |
| `mc_expected_return` | numeric | Monte Carlo Expected Return % | `ER=([-0-9.]+)%` |
| `coherence_score` | numeric | Coherence Engine Score % | `Coherence ([0-9.]+)%` |
| `ecw_cycles` | integer | ECW cycles completados (0-3) | `ECW: ([0-9]+)/3` |
| `ecw_status` | varchar | WAITING / OPEN | Pattern match |
| `black_swan_severity` | varchar | LOW / MEDIUM / HIGH / EXTREME | `BLACK_SWAN_VETO: ([A-Za-z]+)` |
| `crash_probability` | numeric | Black Swan crash probability % | `CrashProb=([0-9.]+)%` |
| `approx_dci` | numeric | DCI aproximado (0-100) | Calculated |

### SQL Definition:

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
    MAX(CASE 
      WHEN trace_line LIKE 'MC_SIZE_REDUCE%' 
      THEN (regexp_match(trace_line, 'Win rate ([0-9.]+)%'))[1]::numeric
      WHEN trace_line LIKE 'ECW_GATE%'
      THEN (regexp_match(trace_line, 'WR=([0-9.]+)%'))[1]::numeric
    END) as mc_win_rate,
    MAX(CASE 
      WHEN trace_line LIKE 'ECW_GATE%'
      THEN (regexp_match(trace_line, 'ER=([-0-9.]+)%'))[1]::numeric
    END) as mc_expected_return,
    MAX(CASE 
      WHEN trace_line LIKE 'COHERENCE_GATE%'
      THEN (regexp_match(trace_line, 'Coherence ([0-9.]+)%'))[1]::numeric
    END) as coherence_score,
    MAX(CASE 
      WHEN trace_line LIKE 'ECW_GATE%'
      THEN (regexp_match(trace_line, 'ECW: ([0-9]+)/3'))[1]::integer
    END) as ecw_cycles,
    MAX(CASE 
      WHEN trace_line LIKE 'ECW_GATE: WAITING%' THEN 'WAITING'
      WHEN trace_line LIKE 'ECW_GATE: OPEN%' THEN 'OPEN'
    END) as ecw_status,
    MAX(CASE 
      WHEN trace_line LIKE '%BLACK_SWAN%'
      THEN UPPER((regexp_match(trace_line, 'BLACK_SWAN_VETO: ([A-Za-z]+)'))[1])
    END) as black_swan_severity,
    MAX(CASE 
      WHEN trace_line LIKE '%CrashProb%'
      THEN (regexp_match(trace_line, 'CrashProb=([0-9.]+)%'))[1]::numeric
    END) as crash_probability
  FROM trace_expanded
  GROUP BY id, created_at, symbol, intended_action, intended_position_size_usd,
           blocked_capital, veto_type, veto_reason, ema_score, ema_signal
)
SELECT 
  *,
  -- Approximate DCI calculation
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

## Usage Examples

### 1. DCI Distribution Analysis
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
GROUP BY 1;
```

### 2. ECW Gate Analysis
```sql
SELECT 
  ecw_status,
  ecw_cycles,
  COUNT(*) as events,
  ROUND(AVG(mc_win_rate), 1) as avg_wr,
  ROUND(AVG(mc_expected_return), 4) as avg_er
FROM v_shadow_trade_metrics
WHERE ecw_status IS NOT NULL
GROUP BY 1, 2
ORDER BY 1, 2;
```

### 3. Symbol Performance
```sql
SELECT 
  symbol,
  COUNT(*) as events,
  ROUND(AVG(coherence_score), 1) as avg_coherence,
  ROUND(AVG(approx_dci), 1) as avg_dci
FROM v_shadow_trade_metrics
GROUP BY symbol
ORDER BY avg_dci DESC;
```

---

## Results (Initial Analysis - Jan 22, 2026)

### DCI Distribution:
| Bucket | Events | Avg WR | Avg Coherence |
|--------|--------|--------|---------------|
| ALIGNED (<35) | 76,789 | 49.8% | 43.2% |
| TENSIONED (35-49) | 121 | 48.6% | 33.0% |

### By Symbol:
| Symbol | Events | Avg DCI | Avg Coherence |
|--------|--------|---------|---------------|
| AVAX/USD | 25,632 | 31.0 | 40.5% |
| BTC/USD | 25,645 | 29.8 | 43.6% |
| XRP/USD | 25,635 | 29.1 | 45.4% |

---

## Next Steps

1. **Multi-Threshold Validation**: Test DCI thresholds (60, 65, 70, 75) against trade outcomes
2. **Correlation Analysis**: Calculate r between DCI and actual P&L
3. **GO/ARCHIVE Decision**: Based on statistical validation (r ≥ 0.6 = GO)

---

## References

- ADR-018: Decision Contradiction Index
- ADR-019: Edge Confirmation Window
- docs/REAL_SYSTEM_STATUS.md
