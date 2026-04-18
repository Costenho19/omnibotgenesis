# OMNIX V7.0 - Activación de Feature Flags

**Fecha**: 22 de Diciembre 2025  
**Estado**: Listo para activación gradual

---

## Resumen

Los adapters hexagonales están 100% implementados pero **0% activos** en producción. El sistema opera 100% con código legacy en Railway. Este documento describe el procedimiento para activar cada feature flag de forma segura.

**Actualización Dec 22, 2025**: Se agregaron 2 nuevos ports (AuthorizationPort, UserSessionPort). Total: 20 ports, 22 adapters.

---

## Orden de Activación

| Paso | Feature Flag | Riesgo | Tiempo Validación |
|------|--------------|--------|-------------------|
| 1 | `USE_CACHE_PORT=true` | BAJO | 24-48h |
| 2 | `USE_DATABASE_PORT=true` | MEDIO | 48-72h |
| 3 | `USE_NOTIFICATION_PORT=true` | BAJO | 24h |
| 4 | `USE_TELEGRAM_PORT=true` | MEDIO | 48h |
| 5 | `USE_APP_LAYER=true` | ALTO | 72h+ |

---

## 1. USE_CACHE_PORT

### Pre-requisitos
- [x] CacheAdapter implementa CachePort
- [x] Tests de shadow mode pasando (26/26)
- [x] Health check funcional
- [x] Redis conectado en Railway

### Script de Validación

```bash
# Desde Replit
PYTHONPATH=/home/runner/workspace python -c "
from src.omnix.infrastructure.adapters.cache_adapter import CacheAdapter
from src.omnix.ports.driven.cache_port import CachePort

adapter = CacheAdapter()
print(f'Implements CachePort: {isinstance(adapter, CachePort)}')
print(f'Connected: {adapter.is_connected()}')
print(f'Health: {adapter.health_check()}')
"
```

### Activación en Railway

1. **Railway Dashboard** > Variables
2. Añadir: `USE_CACHE_PORT=true`
3. Redeploy automático
4. Monitorear logs por 24-48h

### Rollback

1. **Railway Dashboard** > Variables
2. Cambiar a: `USE_CACHE_PORT=false`
3. Redeploy automático (< 2 minutos)

### Qué Monitorear

```
# Logs positivos esperados
CacheAdapter: RedisCache loaded
health_check: {'healthy': True, ...}

# Logs de error (requieren rollback)
CacheAdapter: Failed to load RedisCache
CacheAdapter: get error
error_count > 0
```

---

## 2. USE_DATABASE_PORT

### Pre-requisitos
- [ ] DatabaseAdapter implementa DatabasePort
- [ ] Tests de query comparison pasando
- [ ] Schema migration `V7_001` ejecutada

### Validación

```bash
# Ejecutar en Railway CLI
python -c "
from src.omnix.infrastructure.adapters.database_adapter import DatabaseAdapter
adapter = DatabaseAdapter()
print(f'Connected: {adapter.health_check()}')
"
```

### Migración Requerida

```sql
-- Ejecutar ANTES de activar
-- sql/migrations/V7_001_fix_schema_discrepancies.sql
```

---

## 3. USE_NOTIFICATION_PORT

### Pre-requisitos
- [ ] NotificationAdapter implementa NotificationPort
- [ ] Test message enviado correctamente

### Validación

```bash
python -c "
from src.omnix.infrastructure.adapters.notification_adapter import NotificationAdapter
adapter = NotificationAdapter()
# adapter.send_test_message(chat_id=YOUR_ID)
"
```

---

## 4. USE_TELEGRAM_PORT

### Pre-requisitos
- [ ] TelegramBotAdapter implementa TelegramPort
- [ ] Comandos básicos funcionando

### IMPORTANTE
Solo activar cuando NO haya otro bot corriendo con el mismo token.

---

## 5. USE_APP_LAYER

### Pre-requisitos
- [ ] Todos los ports anteriores activos
- [ ] E2E tests pasando
- [ ] Performance benchmarks OK

### Riesgo
Este flag activa toda la capa de aplicación. Es el cambio más significativo.

---

## Monitoreo General

### Métricas a Observar
- Error rate < 0.1%
- Latencia p99 < 500ms
- Cache hit rate > 80%
- Zero trade execution failures

### Alertas Críticas
- Cualquier error en trade execution → Rollback inmediato
- Error rate > 1% → Investigar
- Latencia > 2s → Investigar

---

## Rollback de Emergencia

```bash
# En Railway Dashboard, revertir cualquier flag a false:
USE_CACHE_PORT=false
USE_DATABASE_PORT=false
USE_NOTIFICATION_PORT=false
USE_TELEGRAM_PORT=false
USE_APP_LAYER=false
```

El sistema legacy sigue funcionando en paralelo hasta que se elimine explícitamente.

---

## Documentos Relacionados

- [MIGRATION_STATUS.md](../MIGRATION_STATUS.md) - Estado general
- [HEXAGONAL_MIGRATION_STATUS.md](../current/HEXAGONAL_MIGRATION_STATUS.md) - Detalle técnico
- [DEPLOYMENT.md](DEPLOYMENT.md) - Guía Railway
