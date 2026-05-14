# POSTGRES STORAGE AUDIT — OMNIX QUANTUM

**Fecha:** 14 Mayo 2026  
**Base de datos:** Railway PostgreSQL 17.7  
**Ejecutado por:** Harold Nunes — OMNIX QUANTUM LTD  
**Tamaño total:** 5,240 MB (5.1 GB)  
**Total tablas:** 111 tablas públicas  

> **Política de auditoría:** Solo auditar. No se elimina ni modifica nada automáticamente.
> Toda acción recomendada requiere aprobación explícita antes de ejecutarse.

---

## 1. Resumen Ejecutivo

| Categoría | Valor |
|---|---|
| Tamaño total DB | **5,240 MB** |
| Top 4 tablas (% del total) | 4,277 MB — **81.6%** del total |
| Índices duplicados confirmados | **1** (`decision_receipts.receipt_id`) |
| Índices con 0 scans (candidatos a eliminar) | **8 índices** — 72 MB potencial ahorro |
| Tablas con dead rows > 50% del live count | **4** (requieren VACUUM urgente) |
| Tablas con 0 filas sin actividad > 60 días | **37** |
| Ciclos de métricas sin retention policy | **7 tablas** — ~130K filas acumuladas |
| Ahorro estimado conservador (sin borrar datos) | **~87 MB** (solo índices y vacuums) |
| Ahorro estimado con retention 90 días | **~1.2–2.1 GB** (estimado según tasa de inserción) |

---

## 2. Tablas por Tamaño — Mayor a Menor

### 2.1 Tier 1: Tablas Críticas (> 100 MB)

| # | Tabla | Total | Data | Índices | Filas vivas | Dead rows | Avg fila | Clasificación |
|---|---|---|---|---|---|---|---|---|
| 1 | `decision_receipts` | **1,745 MB** | 225 MB | 1,520 MB | 123,984 | 2,164 | 1,876 B | CRÍTICA |
| 2 | `governance_transparency_log` | **881 MB** | 49 MB | 832 MB | 151,661 | 0 | ~360 B | CRÍTICA |
| 3 | `decision_receipts_warm` | **879 MB** | 75 MB | 803 MB | 100,482 | 5 | 795 B | CRÍTICA — tier 2 |
| 4 | `shadow_trade_events` | **770 MB** | 456 MB | 314 MB | 88,792 | **12,548** | **5,407 B** | ALTA |
| 5 | `robot_actions` | **244 MB** | 227 MB | 17 MB | 136,654 | 13 | 1,816 B | ALTA |
| 6 | `insurance_claims` | **163 MB** | 152 MB | 11 MB | 92,052 | 16 | 1,762 B | MEDIA |
| 7 | `medical_decisions` | **141 MB** | 131 MB | 9.6 MB | 85,906 | 6 | 1,612 B | MEDIA |
| 8 | `agent_decisions` | **133 MB** | 123 MB | 9.3 MB | 80,401 | 9 | 1,657 B | MEDIA |

### 2.2 Tier 2: Tablas Significativas (10 MB – 100 MB)

| Tabla | Total | Filas | Avg fila | Nota |
|---|---|---|---|---|
| `property_decisions` | 83 MB | 53,986 | 1,602 B | |
| `energy_decisions` | 47 MB | 109,210 | 331 B | Mayor volumen de filas del grupo |
| `credit_applications` | 36 MB | 76,177 | 367 B | |
| `receipt_archival_index` | 34 MB | 100,482 | 278 B | **12,405 dead rows** — índice de archivado |
| `stablecoin_decisions` | 20 MB | 46,279 | 308 B | |
| `trading_veto_log` | 18 MB | 45,474 | 202 B | |

### 2.3 Tier 3: Tablas de Métricas de Ciclo

| Tabla | Total | Filas | Sin retention | Crecimiento estimado |
|---|---|---|---|---|
| `insurance_cycle_metrics` | 2.7 MB | 13,096 | Sí — indefinido | ~3K filas/semana |
| `robotics_cycle_metrics` | 2.7 MB | 13,035 | Sí — indefinido | ~3K filas/semana |
| `agent_cycle_metrics` | 2.6 MB | 14,606 | Sí — indefinido | ~1.4K filas/semana |
| `energy_cycle_metrics` | 2.5 MB | 15,614 | Sí — indefinido | ~2.3K filas/semana |
| `credit_cycle_metrics` | 2.4 MB | 14,081 | Sí — indefinido | ~1.2K filas/semana |
| `medical_cycle_metrics` | 2.1 MB | 12,249 | Sí — indefinido | ~2.4K filas/semana |
| `property_cycle_metrics` | 2.0 MB | 9,799 | Sí — indefinido | ~2.8K filas/semana |
| `stablecoin_cycle_metrics` | 1.6 MB | 9,379 | Sí — indefinido | ~2.4K filas/semana |
| `defense_cycle_metrics` | 0.5 MB | 2,923 | Sí — indefinido | ~0.3K filas/semana |

**Subtotal ciclos:** ~18 MB, ~104,782 filas, **ninguna tabla tiene retention policy**.  
A tasa actual, estas tablas llegarán a **~500 MB combinadas en 12 meses** sin limpiezas.

### 2.4 Tier 4: Tablas Vacías sin Actividad (0 filas, 0 inserts)

Las siguientes 37 tablas tienen 0 filas vivas y 0 inserts desde el último stats reset.
Reservan entre 8 kB y 64 kB cada una mayormente en overhead de índices.

Tablas relevantes del grupo:

| Tabla | Tamaño | Origen probable |
|---|---|---|
| `decision_receipts_cold` | 16 kB | Tier 3 archivado — nunca usado |
| `trades` | 16 kB | Trading legacy |
| `ai_interactions` | 16 kB | — |
| `conversation_memory` | 16 kB | — |
| `governance_reports` | 24 kB | — |
| `governance_metrics` | 24 kB | — |
| `bind_gate_records` | 56 kB | — |
| `breach_containment_events` | 48 kB | — |
| `anomaly_recommendations` | 48 kB | — |
| `multi_domain_risk_assessments` | 48 kB | — |
| `governance_risk_map` | 32 kB | — |
| `backtest_phase0_ohlcv` | 24 kB | Backtesting — sin datos OHLCV |
| `perpetual_positions` | 8 kB | Trading derivados |
| `hedge_positions` | 8 kB | Trading derivados |

Estas tablas son archivables o descartables, pero requieren verificación de referencias antes de cualquier acción.

---

## 3. Análisis Crítico: Índices

### 3.1 Índice Duplicado Confirmado

**TABLA:** `decision_receipts`

| Índice | Tamaño | Scans | Tipo | Problema |
|---|---|---|---|---|
| `decision_receipts_receipt_id_key` | 14 MB | 224,467 | UNIQUE constraint | Original — necesario |
| `idx_decision_receipts_receipt_id` | 14 MB | 100,602 | Índice explícito sobre mismo campo | **DUPLICADO** |

El constraint UNIQUE ya crea un índice B-tree implícito en `receipt_id`. El segundo índice
explícito es idéntico en estructura y función. **Ahorro potencial inmediato: 14 MB.**

### 3.2 Índices con 0 Scans (sin uso desde último stats reset)

Estos índices no han sido usados en ninguna consulta desde el último pg_stat_reset. Son
candidatos a eliminación después de verificar que no sean necesarios para constraints.

| Índice | Tabla | Tamaño | Scans | Recomendación |
|---|---|---|---|---|
| `idx_shadow_events_veto_type` | `shadow_trade_events` | **61 MB** | 1 | Eliminar — 1 scan en toda la vida de la tabla |
| `idx_veto_log_type_created` | `trading_veto_log` | 3.4 MB | 0 | Eliminar |
| `idx_veto_log_symbol_created` | `trading_veto_log` | 3.0 MB | 0 | Eliminar |
| `idx_warm_created_at` | `decision_receipts_warm` | 2.2 MB | 0 | Eliminar |
| `robot_actions.idx_robot_actions_type` | `robot_actions` | 1.0 MB | 0 | Eliminar |
| `idx_credit_apps_sector` | `credit_applications` | 880 kB | 0 | Eliminar |
| `idx_insurance_claims_type` | `insurance_claims` | 736 kB | 0 | Eliminar |
| `idx_defense_decisions_created` | `defense_decisions` | 648 kB | 0 | Revisar |
| `idx_stablecoin_decisions_type` | `stablecoin_decisions` | 520 kB | 0 | Eliminar |

**Ahorro potencial total si se eliminan los 9:** ~73 MB

### 3.3 Índices con Uso Mínimo (< 10 scans totales)

| Índice | Tabla | Tamaño | Scans | Tuples read | Diagnóstico |
|---|---|---|---|---|---|
| `idx_tl_symbol` | `governance_transparency_log` | 9.2 MB | 4 | 40 | Consultas manuales/debugging únicamente |
| `idx_tl_receipt` | `governance_transparency_log` | 8.0 MB | 1 | 1 | Casi nunca usado |
| `idx_archival_index_tier` | `receipt_archival_index` | 1.7 MB | 33 | 0 tuples | Scans sin resultado |
| `idx_archival_index_status` | `receipt_archival_index` | 1.3 MB | 2 | 36,342 | Marginal |
| `idx_warm_domain` | `decision_receipts_warm` | 808 kB | 2 | 22,232 | Marginal |

### 3.4 Índices de Alta Actividad (correctamente usados)

| Índice | Tabla | Tamaño | Scans | Diagnóstico |
|---|---|---|---|---|
| `shadow_trade_events_pkey` | `shadow_trade_events` | 19 MB | 1,566,951 | Altísimo uso — correcto |
| `idx_shadow_events_created` | `shadow_trade_events` | 33 MB | 830,852 | Alto — correcto |
| `idx_decision_receipts_created_at` | `decision_receipts` | 7.4 MB | 334,931 | Alto — correcto |
| `idx_decision_receipts_domain` | `decision_receipts` | 1.7 MB | 33,940 | Correcto |
| `receipt_archival_index_pkey` | `receipt_archival_index` | 5.1 MB | 402,025 | Correcto |

---

## 4. Anomalías de Acceso — Tablas con Comportamiento Inusual

### 4.1 Tablas con Seq Scans Excesivos para su Tamaño

| Tabla | Filas | Seq Scans | Diagnóstico | Impacto |
|---|---|---|---|---|
| `paper_trading_trades` | 178 | **1,265,663** | Tabla sin índice útil consultada masivamente | ALTO — cada scan lee ~169M tuples |
| `user_settings` | 4 | **343,523** | Tabla mínima sin índice por columna de búsqueda | MEDIO |
| `exit_governance_receipts` | 78 | **32,901** | Consultas repetidas sin índice en campo usado | MEDIO |
| `admissibility_violations` | 0 | **16,024** | Tabla vacía consultada continuamente | BAJO (tabla vacía) |

`paper_trading_trades` es el caso más crítico: 178 filas producen **1,265,663 seq scans**
que acumulan 169,087,545 tuple reads. Una sola consulta por rango de fecha podría resolver
esto con un índice en `created_at`.

### 4.2 Dead Rows Elevadas — VACUUM Urgente

| Tabla | Filas vivas | Dead rows | Ratio | Último autovacuum |
|---|---|---|---|---|
| `receipt_archival_index` | 100,482 | **12,405** | 12.3% | 2026-05-13 (ayer) |
| `shadow_trade_events` | 88,792 | **12,548** | 14.1% | 2026-05-09 (hace 5 días) |
| `paper_trading_trades` | 178 | 55 | 30.9% | 2026-02-24 (hace 79 días) |
| `avm_calibration_snapshots` | 11 | **18** | **163.6%** | Nunca (autovacuum no disparado) |
| `b2b_clients` | 5 | **12** | **240%** | Nunca |
| `conversations` | 57 | 52 | 91.2% | 2026-04-06 |
| `users` | 15 | 13 | 86.7% | Nunca |

`avm_calibration_snapshots` y `b2b_clients` tienen más dead rows que live rows — bloat
significativo para su tamaño. El autovacuum no se ha disparado porque el threshold absoluto
(50 rows default) no se alcanza en tablas tan pequeñas.

### 4.3 shadow_trade_events — Avg Row Size Anómalo

Con un avg de **5,407 bytes/fila** y 88,792 filas, esta tabla produce 480 MB de data bruta.
Para comparación, `decision_receipts` tiene 1,876 bytes/fila con filas más complejas.

Causas probables:
- Campos JSONB con payloads completos de eventos de trading embebidos
- Arrays o campos TEXT de longitud variable sin límite

A la tasa actual (18,410 inserts desde último vacuum, ~3,680/día estimado):
- **Crecimiento diario:** ~20 MB/día
- **Crecimiento mensual:** ~600 MB/mes
- **Sin retention policy → en 6 meses: ~4.3 GB solo esta tabla**

---

## 5. Crecimiento Estimado

### 5.1 Proyección a 30 / 90 / 180 días

Basado en la tasa de inserts totales registrados y filas actuales:

| Tabla | Tasa estimada | +30 días | +90 días | +180 días |
|---|---|---|---|---|
| `shadow_trade_events` | ~3,700 filas/día × 5.4 kB | **+600 MB** | +1.8 GB | +3.5 GB |
| `governance_transparency_log` | ~1,500 filas/día × 5.8 kB | **+261 MB** | +783 MB | +1.6 GB |
| `decision_receipts` | ~900 filas/día × 1.9 kB | **+51 MB** | +154 MB | +308 MB |
| `robot_actions` | ~700 filas/día × 1.8 kB | **+38 MB** | +113 MB | +226 MB |
| `insurance_claims` | ~800 filas/día × 1.8 kB | **+43 MB** | +130 MB | +259 MB |
| Ciclo metrics (todas) | ~1,200 filas/día × 140 B | **+5 MB** | +15 MB | +30 MB |

**Sin ninguna acción → DB en 90 días: ~8.1 GB (+2.9 GB)**  
**Sin ninguna acción → DB en 180 días: ~11.2 GB (+6.0 GB)**

Railway PostgreSQL: verificar límite de storage del plan activo.

### 5.2 Tablas de Archivado ya Implementadas

| Tabla | Filas | Estado |
|---|---|---|
| `decision_receipts_warm` | 100,482 | Tier 2 activo — recibe archivados de `decision_receipts` |
| `decision_receipts_cold` | 0 | Tier 3 creado pero nunca usado |

La arquitectura de tiering existe. El problema es que `_warm` tiene 879 MB y no hay
proceso de rotación hacia `_cold`, ni cleanup periódico de `_cold`.

---

## 6. Tablas Críticas de Gobernanza ATF

Las tablas ATF definidas en ADR-156/157/158/159 son pequeñas o inexistentes en esta DB
(probablemente vacías en este entorno dev/Railway):

| Tabla | ADR | Estado esperado |
|---|---|---|
| `execution_receipts` | ADR-131 | 5 filas — activo pero mínimo |
| `atf_runtime_continuity` | ADR-159 | No aparece — sin datos o no creada |
| `atf_continuity_escalations` | ADR-159 | No aparece — sin datos |
| `atf_delegations` | ADR-156 | No aparece |
| `atf_temporal_records` | ADR-157 | No aparece |
| `governance_scope_authorizations` | ADR-147 | No aparece |

Estas tablas de gobernanza ATF no representan riesgo de storage actualmente. Cuando
el sistema alcance producción plena, necesitarán retention policy con los mismos
criterios que `decision_receipts`.

---

## 7. Logs Redundantes y Datos Temporales

### 7.1 `governance_transparency_log` — 881 MB sin retention

Esta tabla es el segundo mayor consumidor de storage (881 MB). Con 151,661 filas y
un tamaño total que implica ~5.8 kB/fila (probablemente JSONB de payloads completos),
es el candidato más agresivo para una retention policy.

**Sin retention → crecerá a ~1.4 GB en 90 días.**

Propuesta de retention: registros > 180 días → mover a cold storage o comprimir.

### 7.2 `shadow_trade_events` — 12,548 dead rows sin cleanup

La tasa de deletes (n_tup_del implícito en dead_rows) sugiere que el proceso de
cleanup existe pero no se ejecuta con suficiente frecuencia. El autovacuum tardó
5 días en dispararse.

### 7.3 `shadow_trade_outcomes` — 50 dead rows, 0 filas vivas

Esta tabla tiene **50 dead rows y 0 filas vivas** — todos los registros fueron eliminados
pero VACUUM nunca corrió para liberar el espacio. Requiere VACUUM FULL o al menos VACUUM.

### 7.4 Tablas temporales de paper trading sin limpieza

| Tabla | Estado | Dead rows | Último vacuum |
|---|---|---|---|
| `paper_trading_trades` | 178 vivas | 55 | 2026-02-24 (79 días sin vacuum) |
| `paper_trading_balances` | 1 viva | 47 | 2026-04-17 |
| `paper_trading_daily_reports` | 0 vivas | 0 | — |

`paper_trading_balances` tiene 1 fila viva y 47 dead rows — ratio 4,700%. VACUUM urgente.

---

## 8. Recomendaciones — Agrupadas por Prioridad

> ⚠️ **AUDITORÍA SOLO.** Las siguientes recomendaciones NO se aplican automáticamente.
> Cada acción requiere aprobación explícita de Harold Nunes antes de ejecutarse.

### Prioridad ALTA — Sin riesgo de datos (solo índices/vacuum)

#### R-01: Eliminar índice duplicado en `decision_receipts`
```sql
-- SOLO ejecutar tras confirmación
DROP INDEX CONCURRENTLY idx_decision_receipts_receipt_id;
-- El constraint decision_receipts_receipt_id_key ya cubre este campo.
-- Ahorro: 14 MB
```

#### R-02: Eliminar `idx_shadow_events_veto_type` — 61 MB, 1 solo scan
```sql
DROP INDEX CONCURRENTLY idx_shadow_events_veto_type;
-- Ahorro: 61 MB
-- Verificar antes: ¿existe alguna query que use WHERE veto_type = ?
-- Si existe, evaluar si la query es lo suficientemente frecuente para justificar 61 MB.
```

#### R-03: Eliminar índices con 0 scans en `trading_veto_log`
```sql
DROP INDEX CONCURRENTLY idx_veto_log_type_created;
DROP INDEX CONCURRENTLY idx_veto_log_symbol_created;
-- Ahorro: 6.4 MB
```

#### R-04: Eliminar `idx_warm_created_at` en `decision_receipts_warm`
```sql
DROP INDEX CONCURRENTLY idx_warm_created_at;
-- Ahorro: 2.2 MB. 0 scans desde creación.
```

#### R-05: Eliminar índices con 0 scans en tablas de decisiones
```sql
DROP INDEX CONCURRENTLY idx_robot_actions_type;       -- 1 MB
DROP INDEX CONCURRENTLY idx_credit_apps_sector;       -- 880 kB
DROP INDEX CONCURRENTLY idx_insurance_claims_type;    -- 736 kB
DROP INDEX CONCURRENTLY idx_stablecoin_decisions_type; -- 520 kB
-- Ahorro total: ~3.1 MB
```

#### R-06: VACUUM urgente en tablas con dead row ratio crítico
```sql
VACUUM ANALYZE avm_calibration_snapshots;   -- 163% dead ratio
VACUUM ANALYZE b2b_clients;                 -- 240% dead ratio
VACUUM ANALYZE conversations;               -- 91% dead ratio
VACUUM ANALYZE users;                       -- 86% dead ratio
VACUUM ANALYZE paper_trading_balances;      -- 4700% dead ratio
VACUUM ANALYZE shadow_trade_outcomes;       -- Solo dead rows, 0 live
```

**Ahorro estimado R-01 a R-06: ~87 MB + reducción de bloat**

### Prioridad MEDIA — Retention y archivado

#### R-07: Índice en `paper_trading_trades` para eliminar 1.26M seq scans
```sql
CREATE INDEX CONCURRENTLY idx_paper_trades_created
  ON paper_trading_trades (created_at DESC);
-- Esta tabla recibe 1,265,663 seq scans con solo 178 filas.
-- El overhead de un índice (< 16 kB) es insignificante vs el costo de CPU.
```

#### R-08: Retention policy para `governance_transparency_log`
- Registros > 180 días: archivar a tabla `governance_transparency_log_archive` o exportar a S3
- Registros > 365 días: purga (solo tras confirmación legal/compliance)
- Estimación: podría liberar 600–700 MB si hay datos > 6 meses
- **Verificar primero:** `SELECT MIN(created_at), MAX(created_at) FROM governance_transparency_log;`

#### R-09: Activar rotación `decision_receipts_warm` → `_cold`
- `decision_receipts_cold` existe pero tiene 0 filas
- El proceso de archivado `_hot → _warm` funciona (100,482 filas en warm)
- Implementar: registros en `_warm` > 90 días → mover a `_cold`
- Estimación: podría liberar 500–600 MB de `_warm` según distribución de fechas

#### R-10: Retention policy para tablas `*_cycle_metrics`
- Propuesta: retener últimas 52 semanas (1 año) y purgar el resto
- O comprimir a granularidad diaria para registros > 30 días
- Actualmente crecen sin límite — en 12 meses: ~500 MB total

### Prioridad BAJA — Estructural

#### R-11: Revisar avg row size de `shadow_trade_events` (5,407 B)
- Identificar qué campos JSONB almacenan y si pueden ser normalizados o truncados
- Evaluar si el payload completo del evento necesita persistirse o solo un resumen
- A 5.4 kB/fila y tasa actual → el mayor riesgo de crecimiento a largo plazo

#### R-12: Habilitar pg_partman o particionado nativo para tablas > 500 MB
Las siguientes tablas son candidatas a particionado por rango de fecha:
- `governance_transparency_log` → particionar por mes
- `shadow_trade_events` → particionar por mes
- `decision_receipts` → ya tiene arquitectura tier, evaluar particionado por fecha de creación

Particionado permite `DETACH PARTITION` para archivar sin DELETE, más eficiente que
bulk deletes que generan dead rows.

#### R-13: Considerar compresión TOAST para JSONB en tablas grandes
PostgreSQL ya aplica TOAST automáticamente para campos > 2 kB. Verificar que
las columnas JSONB grandes usen `STORAGE EXTENDED` (default) y no `STORAGE PLAIN`.

---

## 9. Plan de Acción Sugerido (Por Orden de Ejecución)

| Paso | Acción | Riesgo | Ahorro estimado | Tiempo |
|---|---|---|---|---|
| 1 | R-06: VACUUM ANALYZE en 6 tablas | Ninguno | Bloat + rendimiento | 5 min |
| 2 | R-01: DROP duplicado receipt_id | Bajo | 14 MB | 2 min |
| 3 | R-02: DROP idx_shadow_events_veto_type | Bajo | 61 MB | 3 min |
| 4 | R-03/04/05: DROP 7 índices con 0 scans | Bajo | 12 MB | 5 min |
| 5 | R-07: CREATE INDEX paper_trading_trades | Ninguno | Mejora de rendimiento | 1 min |
| 6 | Consultar rangos de fechas en `governance_transparency_log` | Ninguno | Diagnóstico | 1 min |
| 7 | R-08: Implementar retention `governance_transparency_log` | Medio (requiere script) | 600–700 MB | 1 día |
| 8 | R-09: Activar rotación `_warm` → `_cold` | Medio | 500–600 MB | 1 día |
| 9 | R-10: Retention `*_cycle_metrics` | Bajo | 15–500 MB | 2 horas |
| 10 | R-11: Análisis `shadow_trade_events` row size | Análisis | Potencial 1–3 GB | 2 días |

---

## 10. Queries de Diagnóstico para Ejecutar Manualmente

Antes de ejecutar cualquier acción de retention, ejecutar estas queries:

```sql
-- Distribución de fechas en governance_transparency_log
SELECT
  DATE_TRUNC('month', created_at) AS mes,
  COUNT(*) AS filas,
  pg_size_pretty(SUM(pg_column_size(t.*))) AS size_approx
FROM governance_transparency_log t
GROUP BY 1 ORDER BY 1;

-- Distribución de fechas en shadow_trade_events
SELECT
  DATE_TRUNC('month', created_at) AS mes,
  COUNT(*) AS filas
FROM shadow_trade_events
GROUP BY 1 ORDER BY 1;

-- Distribución de fechas en decision_receipts_warm
SELECT
  DATE_TRUNC('month', archived_at) AS mes,
  COUNT(*) AS filas
FROM decision_receipts_warm
GROUP BY 1 ORDER BY 1;

-- Verificar campos más grandes de shadow_trade_events
SELECT
  AVG(pg_column_size(t.*)) AS avg_row,
  AVG(LENGTH(metadata::text)) AS avg_metadata_len,
  AVG(LENGTH(event_data::text)) AS avg_event_data_len
FROM shadow_trade_events t
LIMIT 1000;

-- Verificar si idx_shadow_events_veto_type tiene queries activas
SELECT query, calls, total_exec_time
FROM pg_stat_statements
WHERE query ILIKE '%veto_type%'
ORDER BY calls DESC;
```

---

## 11. Autovacuum — Configuración Recomendada para Tablas Pequeñas

Las tablas `avm_calibration_snapshots`, `b2b_clients`, `users` nunca disparan autovacuum
porque el threshold por defecto (50 filas o 20% del total) no se alcanza con < 20 filas.

```sql
-- Bajar threshold de autovacuum para tablas críticas pequeñas
ALTER TABLE avm_calibration_snapshots SET (
  autovacuum_vacuum_threshold = 5,
  autovacuum_analyze_threshold = 5
);
ALTER TABLE b2b_clients SET (
  autovacuum_vacuum_threshold = 2,
  autovacuum_analyze_threshold = 2
);
ALTER TABLE users SET (
  autovacuum_vacuum_threshold = 2,
  autovacuum_analyze_threshold = 2
);
```

---

## Apéndice A — Totales por Categoría

| Categoría | Tablas | Tamaño combinado | % del total |
|---|---|---|---|
| Decision receipts (hot + warm + index) | 3 | 2,658 MB | 50.7% |
| Governance / transparency log | 1 | 881 MB | 16.8% |
| Shadow trading | 2 | 770 MB | 14.7% |
| Domain decisions (robot/insurance/medical/agent/property/energy/credit/stablecoin/defense) | 9 | 993 MB | 18.9% |
| Cycle metrics | 9 | 18 MB | 0.3% |
| ATF / governance infrastructure | ~12 | < 1 MB | 0% (vacías) |
| Resto (trading, paper, backtest, etc.) | 76 | ~20 MB | 0.4% |

---

*Auditoría ejecutada el 14 de Mayo de 2026. No se modificó ni eliminó ningún dato.*  
*Para ejecutar cualquier acción correctiva, aprobar explícitamente cada paso con Harold Nunes.*
