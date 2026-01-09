# Runbook: Daily Monitor Report

**Versión**: 1.0  
**Creado**: Enero 9, 2026  
**Autor**: OMNIX System  
**Estado**: Activo

---

## Descripción

El **Daily Report Service** genera reportes diarios con honestidad brutal sobre el estado real del sistema durante el período de recalibración (30 días). Conecta con PostgreSQL para métricas reales y envía reportes por Telegram.

---

## Componentes

| Componente | Ubicación | Función |
|------------|-----------|---------|
| `DailyReportService` | `omnix_services/monitoring/daily_report_service.py` | Genera reportes con métricas reales |
| `DailyMetrics` | `omnix_services/monitoring/daily_report_service.py` | Dataclass con métricas del día |
| `paper_trading_daily_reports` | PostgreSQL | Tabla para historial de reportes |

---

## Ejecución Manual

### Desde Python

```python
from omnix_services.monitoring.daily_report_service import get_daily_report_service

service = get_daily_report_service()
metrics = service.fetch_real_metrics(user_id="harold_admin")
report = service.generate_report(metrics)
print(report)

service.save_report(metrics, report)
```

### Desde Telegram

```
/reporte_diario
```

---

## Ejecución Automática (Cron)

### Script: `scripts/operations/run_daily_report.sh`

```bash
#!/bin/bash
cd /home/runner/workspace
python -c "
from omnix_services.monitoring.daily_report_service import get_daily_report_service
service = get_daily_report_service()
metrics = service.fetch_real_metrics()
report = service.generate_report(metrics)
service.save_report(metrics, report)
print(report)
"
```

### Railway Cron (00:05 UTC diario)

```bash
0 5 * * * /bin/bash /app/scripts/operations/run_daily_report.sh >> /var/log/daily_report.log 2>&1
```

---

## Métricas Monitoreadas

| Métrica | Fuente | Target |
|---------|--------|--------|
| Win Rate | `paper_trading_balances` | > 35% |
| ROI | Calculado | > +2% |
| Sharpe Ratio | Estimado | > 0.5 |
| Max Drawdown | Calculado | < 3% |
| Coherencia Avg | `trade_coherence_logs` | > 55% |
| Trades | `paper_trading_trades` | 20-60 |
| Learning Cost | Calculado | < $20,000 |

---

## Alertas Automáticas

| Condición | Alerta |
|-----------|--------|
| Win rate < 25% con 10+ trades | 🚨 CRÍTICO |
| ROI < -1% | ⚠️ WARNING |
| Drawdown > 2% | ⚠️ WARNING |
| Coherencia < 45% | ⚠️ WARNING |
| Learning cost > 80% budget | 🚨 CRÍTICO |

---

## Troubleshooting

### Error: "DatabaseGateway not available"

**Causa**: No hay conexión a PostgreSQL  
**Solución**: Verificar `DATABASE_URL` en secrets

### Error: "Cannot save report"

**Causa**: Tabla `paper_trading_daily_reports` no existe  
**Solución**: Ejecutar migración:

```sql
CREATE TABLE paper_trading_daily_reports (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    report_date DATE NOT NULL,
    balance_usd NUMERIC(14,2),
    daily_pnl NUMERIC(14,2),
    period_pnl NUMERIC(14,2),
    roi_pct NUMERIC(6,3),
    win_rate_pct NUMERIC(5,2),
    sharpe_ratio NUMERIC(6,3),
    max_drawdown_pct NUMERIC(5,2),
    kelly_fraction NUMERIC(5,4),
    learning_budget_spent NUMERIC(14,2),
    trades_count INTEGER,
    coherence_avg NUMERIC(5,2),
    shadow_events INTEGER,
    raw_report TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, report_date)
);
```

---

## Historial de Cambios

| Fecha | Cambio |
|-------|--------|
| 2026-01-09 | Creación inicial |
