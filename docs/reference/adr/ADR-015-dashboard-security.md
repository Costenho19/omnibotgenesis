# ADR-015: Dashboard Security Enhancement

**Estado**: ✅ IMPLEMENTADO  
**Fecha**: 21 de Enero 2026  
**Autor**: Replit Agent  
**Prioridad**: BLOCKER (pre-demo a inversores)

---

## Contexto

La auditoría CTO/SRE/Security del 21 de Enero 2026 identificó que el dashboard Flask/Streamlit no tenía autenticación, permitiendo acceso público a métricas sensibles del sistema.

### Problema Identificado

```
grep "@login_required|require_auth|session\[" omnix_dashboard/ → 0 resultados
```

**Riesgo**: Cualquier persona con la URL de Railway podría ver métricas de trading, balances, y configuración del sistema.

**Calificación en Auditoría**: C+ en Seguridad (única área bajo B)

---

## Decisión

Implementar seguridad en capas para el dashboard:

1. **Basic HTTP Authentication** (env vars)
2. **Rate Limiting** por IP
3. **IP Allowlist** opcional (para demos controlados)
4. **Security Headers** en todas las respuestas

---

## Implementación

### Nuevo Archivo: `omnix_dashboard/utils/auth.py`

```python
from omnix_dashboard.utils.auth import init_security
init_security(app)
```

### Variables de Entorno

| Variable | Requerido | Default | Descripción |
|----------|-----------|---------|-------------|
| `DASHBOARD_USER` | Sí (prod) | - | Usuario para Basic Auth |
| `DASHBOARD_PASSWORD` | Sí (prod) | - | Contraseña para Basic Auth |
| `DASHBOARD_RATE_LIMIT` | No | 300 | Requests por minuto por IP |
| `DASHBOARD_IP_ALLOWLIST` | No | - | IPs permitidas (comma-separated) |
| `DASHBOARD_AUTH_OPTIONAL` | No | false | Si 'true', permite dashboard público en Railway |

### Endpoints Exentos

Los siguientes endpoints NO requieren autenticación:
- `/api/health` - Healthchecks de Railway
- `/health` - Healthchecks alternativos
- `/static/*` - Assets estáticos
- `/favicon.ico` - Favicon

### Comportamiento por Entorno

| Entorno | Auth Habilitado | Rate Limit | IP Allowlist |
|---------|-----------------|------------|--------------|
| **Development** (Replit) | Solo si env vars set | Activo | Activo si configurado |
| **Production** (Railway) | **OBLIGATORIO** (fail-closed) | Activo | Activo si configurado |

**FAIL-CLOSED en Producción**: Si `DASHBOARD_USER`/`PASSWORD` no están configurados en Railway, el dashboard retorna **503 Service Unavailable** en lugar de quedar público. Esto garantiza que nunca se exponga accidentalmente.

Para override (NO RECOMENDADO): Set `DASHBOARD_AUTH_OPTIONAL=true`

---

## Flujo de Seguridad

```
Request entrante
    │
    ├─→ ¿Path exento? (/health, /static) → ALLOW
    │
    ├─→ ¿IP en allowlist? (si configurado)
    │       NO → 403 Forbidden
    │
    ├─→ ¿Rate limit excedido?
    │       SI → 429 Too Many Requests (con Retry-After)
    │
    ├─→ ¿Auth habilitado?
    │       SI → ¿Basic Auth válido?
    │               NO → 401 Unauthorized (con WWW-Authenticate)
    │
    └─→ ALLOW + agregar security headers
```

---

## Security Headers Agregados

```
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
X-RateLimit-Limit: <configured limit>
```

---

## Configuración para Demo a Inversores

### Opción 1: Credenciales Compartidas

```bash
# Railway Variables
DASHBOARD_USER=omnix_investor
DASHBOARD_PASSWORD=<strong-random-password>
```

Compartir credenciales con inversores antes de la demo.

### Opción 2: IP Allowlist (Demo Controlado)

```bash
# Railway Variables
DASHBOARD_IP_ALLOWLIST=203.0.113.50,198.51.100.100
```

Solo IPs específicas pueden acceder (inversores deben proporcionar su IP).

### Opción 3: Combinado (Máxima Seguridad)

```bash
DASHBOARD_USER=omnix_investor
DASHBOARD_PASSWORD=SecureP@ss2026!
DASHBOARD_IP_ALLOWLIST=203.0.113.50
DASHBOARD_RATE_LIMIT=30
```

---

## Rollback

Si hay problemas con autenticación:

1. **Modo Fail-Closed (PREDETERMINADO)**: Sin `DASHBOARD_USER`/`PASSWORD`, el dashboard retorna 503 en Railway
2. **Para hacer público temporalmente** (NO RECOMENDADO): Set `DASHBOARD_AUTH_OPTIONAL=true` en Railway
3. El dashboard quedará público y funcional
4. **Restaurar seguridad**: Configurar `DASHBOARD_USER`/`PASSWORD` o remover `DASHBOARD_AUTH_OPTIONAL`

**IMPORTANTE**: El modo público (`DASHBOARD_AUTH_OPTIONAL=true`) debe usarse solo para diagnóstico temporal.

---

## Testing

### Manual (Replit)

```bash
# Sin credenciales → Acceso libre
curl http://localhost:5000/

# Con credenciales configuradas
export DASHBOARD_USER=admin
export DASHBOARD_PASSWORD=test123

# Verificar 401 sin auth
curl http://localhost:5000/ → 401 Unauthorized

# Verificar acceso con auth
curl -u admin:test123 http://localhost:5000/ → 200 OK

# Verificar rate limit (ejecutar >60 veces rápido)
for i in {1..65}; do curl -u admin:test123 http://localhost:5000/api/health; done
# Últimos requests → 429 Too Many Requests
```

---

## Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `omnix_dashboard/utils/auth.py` | NUEVO - Middleware de seguridad |
| `omnix_dashboard/app.py` | Integración con `init_security(app)` |
| `omnix_dashboard/utils/__init__.py` | Export de `init_security` |
| `docs/reference/adr/ADR-015-dashboard-security.md` | NUEVO - Este documento |

---

## Métricas de Éxito

| Métrica | Antes | Después |
|---------|-------|---------|
| Auth en dashboard | ❌ Ninguna | ✅ Basic Auth |
| Rate limiting | ❌ Ninguno | ✅ 60/min por IP |
| Security headers | ❌ Ninguno | ✅ 5 headers |
| Calificación Seguridad | C+ | A- (esperado) |

---

## Limitaciones Conocidas

### Rate Limiting In-Memory

El rate limiting actual usa almacenamiento en memoria por proceso:

| Limitación | Impacto | Mitigación |
|------------|---------|------------|
| Per-process storage | Bypassable en multi-worker | Railway usa single-worker en plan actual |
| No compartido entre instancias | Scale-out puede degradar protección | Documentar single-worker constraint |
| Memory growth | Puede crecer con muchas IPs | Cleanup automático a 10K IPs |

**Roadmap**: Migrar a Redis-backed rate limiting cuando se requiera scale-out.

### Healthcheck Exemption

Los endpoints `/api/health` y `/health` están exentos de autenticación para permitir healthchecks de Railway. Esto es intencional y no expone datos sensibles.

---

## Referencias

- [CTO_SRE_SECURITY_AUDIT_JAN21_2026.md](../../compliance/audits/CTO_SRE_SECURITY_AUDIT_JAN21_2026.md)
- [ARCHITECTURE.md](../../current/ARCHITECTURE.md)
- [DEPLOYMENT.md](../../operations/DEPLOYMENT.md)

---

*ADR-015 - Dashboard Security Enhancement - 21 de Enero 2026*
