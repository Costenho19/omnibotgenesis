# OMNIX Shadow Portfolio Runner - Runbook

**Fecha**: 27 de Enero 2026  
**Version**: 1.0  
**Propósito**: Operación y mantenimiento del Shadow Portfolio (Counterfactual Analysis)

---

## Descripción

El Shadow Portfolio es un sistema de análisis contrafactual que:
1. **Captura** todos los trades vetados en `shadow_trade_events`
2. **Analiza** qué habría pasado si el trade se hubiera ejecutado
3. **Valida** si el veto fue correcto guardando en `shadow_trade_outcomes`
4. **Calibra** los filtros basándose en los resultados

---

## Tablas Involucradas

| Tabla | Propósito | Registros (Jan 27, 2026) |
|-------|-----------|--------------------------|
| `shadow_trade_events` | Eventos vetados (input) | 670,000+ |
| `shadow_trade_outcomes` | Resultados contrafactuales (output) | 50+ |

---

## Ejecución Manual

### Comando Básico
```bash
python -m omnix_services.database_service.shadow_portfolio_runner
```

### Opciones Disponibles

| Opción | Default | Descripción |
|--------|---------|-------------|
| `--min-age` | 24 | Horas mínimas de antigüedad del evento |
| `--max-events` | 100 | Máximo de eventos a procesar |
| `--symbol` | ALL | Filtrar por símbolo (BTC, ETH, etc.) |
| `--dry-run` | False | Simular sin guardar |

### Ejemplos

```bash
# Procesar 50 eventos (real)
python -m omnix_services.database_service.shadow_portfolio_runner --max-events 50

# Dry run para verificar
python -m omnix_services.database_service.shadow_portfolio_runner --max-events 10 --dry-run

# Solo BTC
python -m omnix_services.database_service.shadow_portfolio_runner --symbol BTC --max-events 100

# Procesar backlog grande
python -m omnix_services.database_service.shadow_portfolio_runner --max-events 1000
```

---

## Configuración en Railway (Cron Job)

### Opción 1: Railway Cron Service

1. Crear nuevo service en Railway: `shadow-portfolio-cron`
2. Configurar schedule: `0 0 * * *` (diario a medianoche UTC)
3. Comando:
```bash
python -m omnix_services.database_service.shadow_portfolio_runner --max-events 500
```

### Opción 2: Dentro del Bot Principal

Agregar cron job en el bot existente usando `apscheduler`:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour=0, minute=0)
async def run_shadow_analysis():
    from omnix_services.database_service.shadow_portfolio_runner import ShadowPortfolioRunner
    runner = ShadowPortfolioRunner()
    runner.run_analysis(max_events=500)

scheduler.start()
```

---

## Dependencias

| Paquete | Versión | Uso |
|---------|---------|-----|
| `psycopg[binary,pool]` | 3.3.1 | Conexión PostgreSQL |
| `requests` | 2.32.5 | API Kraken histórica |

---

## Monitoreo

### Verificar Progreso
```sql
-- Eventos pendientes
SELECT COUNT(*) as pending 
FROM shadow_trade_events 
WHERE outcome_calculated = FALSE 
AND created_at < NOW() - INTERVAL '24 hours';

-- Outcomes procesados
SELECT COUNT(*) as processed,
       SUM(CASE WHEN veto_was_correct THEN 1 ELSE 0 END) as correct,
       ROUND(AVG(CASE WHEN veto_was_correct THEN 1 ELSE 0 END) * 100, 2) as accuracy_pct
FROM shadow_trade_outcomes;
```

### Métricas por Tipo de Veto
```sql
SELECT 
    e.veto_type,
    COUNT(*) as total,
    SUM(CASE WHEN o.veto_was_correct THEN 1 ELSE 0 END) as correct,
    ROUND(AVG(CASE WHEN o.veto_was_correct THEN 1 ELSE 0 END) * 100, 2) as accuracy_pct
FROM shadow_trade_events e
JOIN shadow_trade_outcomes o ON e.id = o.shadow_event_id
GROUP BY e.veto_type
ORDER BY total DESC;
```

---

## Troubleshooting

### Error: "can't compare offset-naive and offset-aware datetimes"
**Solución**: Ya corregido en Jan 27, 2026. Usar `datetime.now(timezone.utc)` en lugar de `datetime.utcnow()`.

### Error: "DATABASE_URL not set"
**Solución**: Asegurar que la variable de entorno está configurada en Railway.

### Sin datos de precios históricos
**Causa**: Kraken API no tiene datos para el par o fecha.
**Solución**: El runner marca esos eventos con `verdict_reason = "No price data available"`.

---

## Output de Ejemplo

```
╔══════════════════════════════════════════════════════════════╗
║       OMNIX Shadow Portfolio Runner - Counterfactual         ║
║              Learning Engine Analysis Job                    ║
╠══════════════════════════════════════════════════════════════╣
║  Min Age:        24h                                         ║
║  Max Events:     50                                          ║
║  Symbol:        ALL                                          ║
║  Dry Run:        No                                          ║
╚══════════════════════════════════════════════════════════════╝

📊 Results Summary:
   Analyzed:        50
   Correct Vetoes:  50
   Incorrect Vetoes: 0
   Unknown Action:   0
   Errors:           0

   By Veto Type:
     BLACK_SWAN: 40 total, 100.0% accuracy
     COHERENCE_GATE: 10 total, 100.0% accuracy

   Overall Accuracy: 100.0%
```

---

## Archivos Relacionados

| Archivo | Propósito |
|---------|-----------|
| `omnix_services/database_service/shadow_portfolio_repository.py` | Repository pattern para DB |
| `omnix_services/database_service/shadow_portfolio_runner.py` | Job de análisis |
| `sql/optimization_tables.sql` | DDL de tablas |

---

## Changelog

| Fecha | Cambio |
|-------|--------|
| Jan 27, 2026 | Fix: timezone aware datetimes |
| Jan 9, 2026 | Initial implementation |
