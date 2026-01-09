# ADR-001: Brutal Honesty Monitoring System

**Estado**: Aceptado  
**Fecha**: Enero 9, 2026  
**Autor**: OMNIX Team  
**Contexto**: Período de recalibración post-auditoría

---

## Contexto

Después de la auditoría de integridad de datos del 9 de enero de 2026, se identificó que el sistema necesita transparencia total sobre su estado real durante el período de recalibración de 30 días. Los inversores requieren honestidad sobre:

1. **Win rate real** (20.17%, no inflado)
2. **Kelly Criterion negativo** (significa NO operar matemáticamente)
3. **Costo de aprendizaje** (pérdidas durante calibración = inversión en I+D)
4. **Progreso hacia objetivos** (35% win rate target)

---

## Decisión

Implementar un **Daily Report Service** que:

1. Genera reportes diarios con métricas REALES de PostgreSQL
2. Muestra honestamente cuando Kelly es negativo ("Modo Aprendizaje")
3. Trackea el "costo de aprendizaje" como presupuesto de I+D ($20K máximo)
4. Visualiza progreso hacia objetivos con barras de progreso
5. Persiste reportes en PostgreSQL para historial de auditoría
6. Se envía automáticamente por Telegram a las 00:05 UTC

---

## Consecuencias

### Positivas

- **Transparencia institucional**: Los inversores ven exactamente el estado real
- **Narrativa de I+D**: Pérdidas reframed como "inversión en datos"
- **Auditoría completa**: Historial de reportes para due diligence
- **Early warning**: Alertas automáticas cuando métricas se degradan

### Negativas

- **Sin excusas**: No hay forma de ocultar mal rendimiento
- **Complejidad**: Nueva tabla y servicio para mantener

### Riesgos Mitigados

- **Discrepancias de datos**: Métricas vienen de una sola fuente (PostgreSQL)
- **Información desactualizada**: Reportes diarios automáticos
- **Expectativas infladas**: Honestidad sobre limitaciones actuales

---

## Alternativas Consideradas

1. **Dashboard solo**: Rechazado - no hay push notification, fácil de ignorar
2. **Reportes semanales**: Rechazado - demasiado espaciados para recalibración
3. **Sin tracking de "learning cost"**: Rechazado - inversores necesitan ver límite de pérdida

---

## Implementación

| Componente | Archivo |
|------------|---------|
| Service | `omnix_services/monitoring/daily_report_service.py` |
| Runbook | `docs/operations/runbooks/daily_monitor_report.md` |
| DB Table | `paper_trading_daily_reports` |
| Telegram | `/reporte_diario` command |

---

## Métricas de Éxito

El sistema es exitoso si:

1. Win rate sube de 20% a 35% en 30 días
2. Learning cost se mantiene bajo $20K
3. Cero reportes con datos falsos o inflados
4. 100% de días con reporte generado

---

## Referencias

- [DATA_INTEGRITY_AUDIT_JAN2026.md](../../compliance/audits/DATA_INTEGRITY_AUDIT_JAN2026.md)
- [TRADING_OPERATIONS.md](../../current/TRADING_OPERATIONS.md)
- [daily_monitor_report.md (Runbook)](../../operations/runbooks/daily_monitor_report.md)
