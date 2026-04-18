# Runbook: Activación USE_AI_PORT=true en Railway

**Fecha**: 17 de Diciembre 2025  
**Riesgo**: BAJO  
**Rollback**: Automático (cooldown 5min) o manual (flag → false)

---

## Resumen

Este runbook documenta el proceso para activar `USE_AI_PORT=true` en Railway, habilitando el `AIGatewayShim` de V7.0 con su sistema de fallback robusto.

---

## Pre-requisitos

### 1. Verificar que los tests pasan

```bash
cd /home/runner/workspace
python -m pytest tests/test_v7_services_integration.py -v
```

**Resultado esperado**: 31/31 tests pasando

### 2. Verificar API keys configuradas

En Railway Dashboard → Variables, confirmar que existen:

| Secret | Requerido | Uso |
|--------|-----------|-----|
| `GEMINI_API_KEY` | ✅ | Provider primario |
| `OPENAI_API_KEY` | ✅ | Fallback 1 |
| `ANTHROPIC_API_KEY` | ⬜ Opcional | Fallback 2 |

**Nota**: Si falta alguna key, el failover saltará ese provider.

### 3. Verificar que el shim tiene fallback configurado

En `omnix_services/ai_service/container.py`:

```python
def _is_v7_shim_in_cooldown(self) -> bool:
    """Check if V7 shim is in 5-minute cooldown after failure."""
    if self._v7_shim_failed_at is None:
        return False
    elapsed = time.time() - self._v7_shim_failed_at
    return elapsed < 300  # 5 minutes
```

---

## Proceso de Activación

### Paso 1: Preparar el cambio

En Railway Dashboard:
1. Ir a **Variables** del proyecto OMNIX
2. Localizar o crear `USE_AI_PORT`
3. Valor actual: `false` (o no existe)

### Paso 2: Activar el flag

```
USE_AI_PORT=true
```

**Nota**: Railway hará redeploy automático.

### Paso 3: Monitorear los primeros 10 minutos

Buscar en logs de Railway:

```
✅ AIGatewayShim: Successfully initialized with AIModelsManager
✅ V7 AI Port: Using AIGatewayShim with full failover chain
```

**O si hay fallback** (también aceptable):

```
⚠️ V7 shim failed, falling back to legacy RoutingAIGateway
🕐 V7 shim in cooldown for 5 minutes
```

### Paso 4: Probar funcionalidad

En Telegram, enviar:
```
/ayuda
```

**Verificar**: El bot responde con texto generado por AI (no error).

### Paso 5: Validación 24 horas

Monitorear durante 24h los siguientes indicadores:

| Indicador | Esperado | Acción si falla |
|-----------|----------|-----------------|
| Respuestas AI | Funcionando | Verificar logs |
| Cooldown triggers | <3/día | Investigar causa |
| Fallback a legacy | 0-5 veces | Aceptable |
| Errores 500 | 0 | Rollback inmediato |

---

## Rollback

### Opción 1: Rollback Automático (preferido)

El sistema ya tiene rollback automático:
- Si `AIGatewayShim` falla → cooldown 5 min → usa `RoutingAIGateway` legacy
- No requiere intervención manual

### Opción 2: Rollback Manual

En Railway Dashboard:
```
USE_AI_PORT=false
```

Railway hará redeploy y volverá a código legacy.

---

## Comportamiento Esperado

### Con USE_AI_PORT=true

```
Request → container.get_ai_service()
    ├── AIGatewayShim disponible?
    │   └── SÍ → AIGatewayShim.generate_text()
    │           └── AIModelsManager (Gemini → OpenAI → Anthropic)
    │   └── NO (cooldown) → RoutingAIGateway (legacy)
    └── AIGatewayShim falla?
        └── _reset_v7_shim() → marca timestamp → fallback legacy
```

### Flujo de failover dentro del shim

```
AIGatewayShim.generate_text()
    ├── AIModelsManager.generate()
    │   ├── Gemini (timeout 20s)
    │   │   └── falla → continúa
    │   ├── OpenAI (timeout 15s)
    │   │   └── falla → continúa
    │   └── Anthropic (timeout 15s)
    │       └── falla → propaga error
    └── Si todos fallan → container._reset_v7_shim()
```

---

## Logs de Referencia

### Éxito

```
2025-12-17 10:00:00 [INFO] AIServiceContainer: Creating V7 AIGatewayShim
2025-12-17 10:00:00 [INFO] AIGatewayShim: Initialized with AIModelsManager
2025-12-17 10:00:01 [INFO] AIModelsManager: Gemini responded in 1.2s
```

### Fallback (aceptable)

```
2025-12-17 10:00:00 [WARN] AIModelsManager: Gemini timeout after 20s
2025-12-17 10:00:00 [INFO] AIModelsManager: Falling back to OpenAI
2025-12-17 10:00:01 [INFO] AIModelsManager: OpenAI responded in 0.8s
```

### Degradación a legacy (aceptable)

```
2025-12-17 10:00:00 [ERROR] AIGatewayShim: All providers failed
2025-12-17 10:00:00 [WARN] Container: V7 shim failed, cooldown 5min
2025-12-17 10:00:00 [INFO] Container: Using legacy RoutingAIGateway
```

### Error crítico (requiere investigación)

```
2025-12-17 10:00:00 [ERROR] Container: get_ai_service() failed completely
2025-12-17 10:00:00 [ERROR] No AI service available
```

---

## Métricas de Éxito

| Métrica | Objetivo |
|---------|----------|
| Disponibilidad AI | >99% |
| Tiempo respuesta p50 | <2s |
| Fallbacks a legacy | <5/día |
| Cooldown triggers | <3/día |
| Errores no recuperables | 0 |

---

## Contacto

- **Responsable**: Harold (Founder)
- **Rollback inmediato**: Cualquiera puede cambiar flag a false

---

*Última actualización: 17 de Diciembre 2025*
