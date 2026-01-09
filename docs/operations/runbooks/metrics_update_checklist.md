# Checklist de Actualización de Métricas

## Propósito
Este runbook garantiza que las métricas de trading se actualicen de forma consistente en todos los documentos "vivos" cuando cambian los datos en PostgreSQL.

## Trigger
Ejecutar este checklist cuando:
- Se ejecutan nuevos trades (diario/semanal)
- Se realiza una auditoría de integridad de datos
- Se prepara una presentación a inversores

---

## Paso 1: Obtener Métricas Actuales de PostgreSQL

```sql
-- Ejecutar en Railway PostgreSQL
SELECT 
    COUNT(*) as total_trades,
    SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as winning_trades,
    SUM(CASE WHEN profit_loss <= 0 THEN 1 ELSE 0 END) as losing_trades,
    ROUND(100.0 * SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as win_rate,
    ROUND(SUM(profit_loss)::numeric, 2) as total_pnl
FROM paper_trading_trades 
WHERE LOWER(status) = 'closed';
```

---

## Paso 2: Documentos a Actualizar (VIVOS)

| # | Archivo | Sección | Métricas |
|---|---------|---------|----------|
| 1 | `docs/README.md` | Track Record table | Trades, Win Rate, P&L, Fecha |
| 2 | `docs/REAL_SYSTEM_STATUS.md` | Datos Verificados table | Trades, P&L, Win Rate |
| 3 | `docs/current/TRADING_OPERATIONS.md` | Appendix: Track Record | Trades |
| 4 | `docs/business/investor/current_metrics.md` | Paper Trading Performance | Todos |
| 5 | `docs/current/ARCHITECTURE.md` | Header fecha | Solo fecha |
| 6 | `docs/MIGRATION_STATUS.md` | Header fecha | Solo fecha |

---

## Paso 3: Documentos Históricos (NO MODIFICAR)

Los siguientes archivos son snapshots históricos y NO deben actualizarse:

| Archivo | Fecha Snapshot |
|---------|---------------|
| `docs/compliance/audits/*_DEC29_2025.md` | 29 Dic 2025 |
| `docs/history/investor_reports/*.md` | Fecha en nombre |
| `docs/history/2025-12/*.md` | Diciembre 2025 |
| `docs/history/2025-11/*.md` | Noviembre 2025 |

---

## Paso 4: Verificación

```bash
# Buscar métricas antiguas en docs vivos
grep -rn "METRIC_ANTIGUA" docs/ --include="*.md" | grep -v "history/" | grep -v "DEC29_2025\|DEC24_2025\|DEC27_2025"
```

Reemplazar `METRIC_ANTIGUA` con el valor anterior (ej: "109 trades").

---

## Paso 5: Criterio de Win Rate

**CRÍTICO**: El win rate se calcula con `profit_loss > 0` (USD), NO con `profit_pct > 0`.

Razón: 21 trades tienen ganancia porcentual positiva pero pérdida en USD debido a fees (0.26% por transacción).

---

## Paso 6: Registro de Actualización

Después de actualizar, añadir entrada a `DATA_INTEGRITY_AUDIT_JAN2026.md`:

```markdown
### Actualización [FECHA]
- Trades: X → Y
- Win Rate: X% → Y%
- P&L: $X → $Y
- Archivos actualizados: [lista]
```

---

## Responsable
CTO / Technical Lead

## Frecuencia
- Semanal durante período de calibración
- Antes de cualquier presentación a inversores

---

*Última actualización: 9 Enero 2026*
