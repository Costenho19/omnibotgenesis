---
name: Replit secrets vs autoscale deployments
description: Replit secrets (panel de Secrets) NO se inyectan en autoscale deployments; shared env vars sí. Patrón de dual-lookup para compatibilidad.
---

## Regla

Los **Replit secrets** (configurados via panel Secrets en la UI de Replit) están disponibles
en el entorno de *desarrollo* pero **NO se inyectan automáticamente en Replit autoscale
deployments** (producción). Únicamente las **shared env vars** (configuradas via
`setEnvVars({environment: "shared"})`) están disponibles en producción.

**Why:** La arquitectura de autoscale de Replit aísla el entorno de producción. Los secrets
son solo para el contexto dev interactivo.

## Consecuencia práctica

Si un secret existe en Replit Secrets (`POGR_ADMIN_RESIGN_SECRET`), no se puede duplicar
como shared env var con el mismo nombre — `setEnvVars` falla con:
> "already set up as secrets and setting them may cause conflicts"

## Solución probada (PoGR S05, 2026-05-31)

Usar un nombre de variable diferente para el shared env var (`POGR_RESIGN_TOKEN`),
con dual-lookup en el código:

```python
resign_secret = (
    os.environ.get("POGR_RESIGN_TOKEN")       # shared env var → producción
    or os.environ.get("POGR_ADMIN_RESIGN_SECRET", "")  # fallback → dev/legacy
)
```

1. `setEnvVars({"POGR_RESIGN_TOKEN": valor}, "shared")` — configura sin conflicto
2. El código funciona en ambos entornos sin cambios de comportamiento
3. Documentar en el ADR correspondiente (addendum con fecha)

## Cómo detectar el problema

- Endpoint retorna 503 en producción cuando en dev retorna 403/200
- `os.environ.get("SECRET_NAME", "")` devuelve `""` en producción
- Health check no muestra el secret como env var en `/api/health`
