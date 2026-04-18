# ADR-011: Legacy Telemetry Backfill & Data Quality Segmentation

**Status**: ADOPTADO  
**Fecha**: 15 de Enero 2026  
**Autor**: OMNIX Team  
**Contexto**: Data Quality 25% debido a trades pre-telemetría

---

## Problema

El sistema reporta **Data Quality 25%** debido a que los 119 trades existentes (Nov-Dic 2025) carecen de campos de telemetría:
- `coherence_score`: NULL en 119/119 trades
- `hmm_regime`: NULL en 119/119 trades
- `ema_regime_signal`: NULL en 119/119 trades
- `strategy_confidence`: NULL en 119/119 trades

La funcionalidad de telemetría (V005 "Operación Lucidez") se implementó en **enero 2026**, después de que estos trades fueron ejecutados.

---

## Decisión

Implementar un plan de remediación de dos tracks:

### Track A: Backfill Estimado

Usar heurísticas determinísticas basadas en el resultado del trade para estimar valores de telemetría:

| Campo | Heurística |
|-------|------------|
| `coherence_score` | Basado en `profit_pct` y `profit_loss` |
| `hmm_regime` | Inferido de volatilidad del trade |
| `ema_regime_signal` | Derivado de `side` + resultado |
| `strategy_confidence` | Escalado por `abs(profit_pct)` |

**Reglas de Estimación:**

```
coherence_score_estimated:
  - profit_loss > 0 AND profit_pct > 0.5%  → 70-80
  - profit_loss > 0 AND profit_pct <= 0.5% → 55-65
  - profit_pct > 0 AND profit_loss <= 0    → 45-55 (fee eroded)
  - profit_pct <= 0                        → 20-35

hmm_regime_estimated:
  - abs(profit_pct) > 2%                   → BULLISH/BEARISH (según signo)
  - abs(profit_pct) 0.5-2%                 → RANGING
  - abs(profit_pct) < 0.5%                 → UNKNOWN

ema_regime_signal_estimated:
  - side=BUY AND profit_pct > 0            → BUY
  - side=SELL AND profit_pct > 0           → SELL
  - otherwise                              → HOLD

strategy_confidence_estimated:
  - MIN(100, MAX(15, abs(profit_pct) * 20 + 30))
```

### Track B: Marcado Legacy

Añadir columna `telemetry_source` para distinguir:
- `LEGACY_ESTIMATED`: Trades con telemetría estimada (Nov-Dic 2025)
- `REAL`: Trades con telemetría capturada en tiempo real (Ene 2026+)

### Track C: Métrica Segmentada

Actualizar el cálculo de Data Quality para mostrar:
- **Data Quality (Overall)**: Todos los trades con algún valor de telemetría
- **Data Quality (Post-Telemetry)**: Solo trades con `telemetry_source = 'REAL'`

---

## Justificación

1. **Honestidad**: Marcar claramente datos estimados vs reales
2. **Aprendizaje**: El Learning Engine necesita datos completos para segmentar
3. **Inversores**: Transparencia sobre limitaciones de datos históricos
4. **Pragmatismo**: Mejor tener estimaciones marcadas que campos vacíos

---

## Alternativas Consideradas

1. **Eliminar trades sin telemetría**: Rechazado - perderíamos track record
2. **Dejar vacíos**: Rechazado - Data Quality permanecería en 25%
3. **Backfill desde veto logs**: Imposible - no hay overlap de fechas

---

## Implementación

### 1. Añadir Columna
```sql
ALTER TABLE paper_trading_trades 
ADD COLUMN telemetry_source VARCHAR(20) DEFAULT 'REAL';
```

### 2. Backfill SQL
```sql
UPDATE paper_trading_trades
SET 
  coherence_score = CASE
    WHEN profit_loss > 0 AND profit_pct > 0.5 THEN 75
    WHEN profit_loss > 0 AND profit_pct <= 0.5 THEN 60
    WHEN profit_pct > 0 AND profit_loss <= 0 THEN 50
    ELSE 25
  END,
  hmm_regime = CASE
    WHEN ABS(profit_pct) > 2 AND profit_pct > 0 THEN 'BULLISH'
    WHEN ABS(profit_pct) > 2 AND profit_pct < 0 THEN 'BEARISH'
    WHEN ABS(profit_pct) BETWEEN 0.5 AND 2 THEN 'RANGING'
    ELSE 'UNKNOWN'
  END,
  ema_regime_signal = CASE
    WHEN side = 'buy' AND profit_pct > 0 THEN 'BUY'
    WHEN side = 'sell' AND profit_pct > 0 THEN 'SELL'
    ELSE 'HOLD'
  END,
  strategy_confidence = LEAST(100, GREATEST(15, ABS(profit_pct) * 20 + 30)),
  telemetry_source = 'LEGACY_ESTIMATED'
WHERE coherence_score IS NULL 
  AND opened_at < '2026-01-01';
```

### 3. Actualizar queries.py
```python
def get_data_quality_metrics():
    # Overall: cualquier campo no-NULL
    # Post-telemetry: solo source='REAL'
```

---

## Métricas Esperadas

| Métrica | Antes | Después |
|---------|-------|---------|
| Data Quality (Overall) | 25% | 100% |
| Data Quality (Real) | 0% | 0% (hasta nuevos trades) |
| Trades con telemetría | 0 | 119 (estimada) |

---

## Riesgos y Mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| Estimaciones incorrectas | Marcadas como LEGACY_ESTIMATED, no usadas para calibración |
| Confusión de inversores | Tooltip explicando "Estimated from trade outcomes" |
| Learning Engine distorsionado | Segmentar análisis por telemetry_source |

---

## Documentos Relacionados

- ADR-010: Capital Protection Metric Standard
- ADR-007: Coherence Threshold Calibration
- docs/REAL_SYSTEM_STATUS.md

---

*OMNIX — Decision Governance Infrastructure*
*Internal Build Reference: 6.5.4e*
