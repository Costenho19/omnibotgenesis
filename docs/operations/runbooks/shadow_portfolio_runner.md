# Runbook: Shadow Portfolio Runner

**Fecha**: 9 de Enero 2026  
**Riesgo**: BAJO  
**Frecuencia**: Diaria (05:00 UTC)

---

## Resumen

El Shadow Portfolio Runner analiza trades bloqueados (vetoed) para determinar si los filtros de riesgo fueron correctos o demasiado conservadores. Esto permite calibrar los umbrales de veto basándose en datos reales.

---

## Pre-requisitos

### 1. Migración V007 ejecutada

```sql
SELECT COUNT(*) FROM shadow_trade_events;
SELECT COUNT(*) FROM shadow_trade_outcomes;
SELECT COUNT(*) FROM filter_calibration_metrics;
```

**Resultado esperado**: Las tablas existen (pueden tener 0 registros inicialmente).

### 2. Vetos siendo capturados

El bot debe estar instrumentado para guardar vetos en `shadow_trade_events`. Verificar:

```sql
SELECT COUNT(*), veto_type 
FROM shadow_trade_events 
GROUP BY veto_type;
```

### 3. DATABASE_URL configurado

```bash
echo $DATABASE_URL
# Debe mostrar la URL de PostgreSQL
```

---

## Ejecución Manual

### Opción 1: Dry Run (sin persistir)

```bash
python -m omnix_services.database_service.shadow_portfolio_runner \
  --min-age 24 \
  --max-events 100 \
  --dry-run \
  --verbose
```

### Opción 2: Ejecución completa

```bash
python -m omnix_services.database_service.shadow_portfolio_runner \
  --min-age 24 \
  --max-events 250
```

### Opción 3: Filtrar por símbolo

```bash
python -m omnix_services.database_service.shadow_portfolio_runner \
  --symbol BTC \
  --min-age 48
```

---

## Configuración Railway Cron

### Paso 1: Crear el cron job

En Railway Dashboard → tu proyecto → Settings → Cron Jobs:

| Campo | Valor |
|-------|-------|
| Name | `shadow-portfolio-runner` |
| Schedule | `0 5 * * *` (05:00 UTC diario) |
| Command | `bash scripts/operations/run_shadow_portfolio.sh` |

**O via CLI:**

```bash
railway cron create \
  --schedule "0 5 * * *" \
  --command "bash scripts/operations/run_shadow_portfolio.sh"
```

### Paso 2: Variables de entorno opcionales

| Variable | Default | Descripción |
|----------|---------|-------------|
| `SHADOW_MIN_AGE_HOURS` | 24 | Edad mínima de vetos a analizar |
| `SHADOW_MAX_EVENTS` | 250 | Máximo de eventos por ejecución |
| `SHADOW_SYMBOL` | (vacío) | Filtrar por símbolo específico |

### Paso 3: Verificar ejecución

```bash
railway cron run shadow-portfolio-runner
```

---

## Logs Esperados

### Ejecución exitosa

```
2026-01-09 05:00:01 UTC [SHADOW_PORTFOLIO] INFO: Starting Shadow Portfolio Analysis
2026-01-09 05:00:01 UTC [SHADOW_PORTFOLIO] INFO: Running: python -m omnix_services...
╔══════════════════════════════════════════════════════════════════════════════╗
║  SHADOW PORTFOLIO RUNNER V007                                                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Min Age:     24 hours                                                         ║
║  Max Events:  250                                                              ║
║  Dry Run:     No                                                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
🔍 Starting Shadow Portfolio analysis (min_age=24h, max=250, dry_run=False)
📊 Found 45 pending events to analyze
✅ Analyzed 45 events: 32 correct vetos, 13 incorrect (28.9% missed opportunities)
```

### Sin eventos para analizar

```
📊 Found 0 pending events to analyze
✅ Analysis complete - no events required processing
```

---

## Interpretación de Resultados

### Tabla: shadow_trade_outcomes

```sql
SELECT 
    veto_type,
    COUNT(*) as total,
    SUM(CASE WHEN veto_was_correct THEN 1 ELSE 0 END) as correct,
    ROUND(100.0 * SUM(CASE WHEN veto_was_correct THEN 1 ELSE 0 END) / COUNT(*), 1) as accuracy_pct
FROM shadow_trade_outcomes
GROUP BY veto_type
ORDER BY total DESC;
```

| veto_type | Accuracy óptima | Acción si < umbral |
|-----------|-----------------|-------------------|
| COHERENCE_GATE | > 60% | Revisar umbral de coherencia |
| MONTE_CARLO | > 70% | Revisar ER threshold |
| BLACK_SWAN | > 80% | Mantener (mejor sobre-proteger) |
| RMS | > 75% | Revisar circuit breakers |

### Tabla: filter_calibration_metrics

```sql
SELECT 
    filter_name,
    current_threshold,
    recommended_action,
    trades_analyzed,
    updated_at
FROM filter_calibration_metrics
ORDER BY updated_at DESC
LIMIT 10;
```

---

## Troubleshooting

| Error | Causa | Solución |
|-------|-------|----------|
| `Lock file exists` | Ejecución anterior no terminó | `rm /tmp/shadow_portfolio.lock` |
| `DATABASE_URL not set` | Variable faltante | Verificar Railway Variables |
| `No events to analyze` | Sin vetos recientes o todos ya analizados | Normal - esperar más datos |
| `Kraken API error` | Rate limit o API down | Reintentar en 15 min |

---

## Rollback

Si el runner genera datos incorrectos:

```sql
DELETE FROM shadow_trade_outcomes 
WHERE analyzed_at > NOW() - INTERVAL '1 hour';

UPDATE shadow_trade_events 
SET status = 'PENDING'
WHERE id IN (
    SELECT event_id FROM shadow_trade_outcomes 
    WHERE analyzed_at > NOW() - INTERVAL '1 hour'
);
```

---

## Métricas de Monitoreo

### Dashboard Streamlit

El widget "Shadow Portfolio Analysis" muestra:
- Accuracy por tipo de veto
- Top trades que el sistema bloqueó incorrectamente
- Recomendaciones de calibración

### Queries de monitoreo

```sql
SELECT 
    DATE(analyzed_at) as date,
    COUNT(*) as events_analyzed,
    ROUND(100.0 * SUM(CASE WHEN veto_was_correct THEN 1 ELSE 0 END) / COUNT(*), 1) as accuracy_pct
FROM shadow_trade_outcomes
GROUP BY DATE(analyzed_at)
ORDER BY date DESC
LIMIT 7;
```

---

## Referencias

- [REAL_SYSTEM_STATUS.md](../../REAL_SYSTEM_STATUS.md) - Estado del sistema
- [TRADING_OPERATIONS.md](../../current/TRADING_OPERATIONS.md) - Operaciones de trading
- [shadow_portfolio_runner.py](../../../omnix_services/database_service/shadow_portfolio_runner.py) - Código fuente

---

*OMNIX V6.5.4d INSTITUTIONAL+ - Shadow Portfolio Learning Engine*
