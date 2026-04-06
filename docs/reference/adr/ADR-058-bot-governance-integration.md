# ADR-058: Bot Governance Integration

**Status:** Accepted  
**Date:** 2026-04-06  
**Author:** Harold Nunes  
**Reviewers:** Arquitecto OMNIX (subagent review)  
**Supersedes:** —  
**Related:** ADR-028 (External Signal Evaluation API), ADR-052 (Velos Gateway), ADR-057 (Critical Override Hybrid Expansion)

---

## Contexto

El bot de Telegram (`enterprise_bot.py`, V6.5.4e INSTITUTIONAL+) es el canal de interacción principal de Harold Nunes con el sistema OMNIX. Hasta ahora el bot solo exponía capacidades de trading (Kraken, Alpaca, Monte Carlo, análisis técnico), pero no tenía integración con el pipeline de gobernanza institucional de 11 checkpoints.

Con el Channel Partner Agreement con Naimat Khan (Velos) firmado y OMNIX en fase de recaudación pre-seed ($500K @ $3M), es crítico que el fundador pueda interactuar con el pipeline de gobernanza directamente desde el bot para:

1. Demostrar la plataforma a inversores en tiempo real.
2. Monitorear el estado del Velos gateway y los recibos PQC.
3. Evaluar escenarios ad-hoc de forma auditada.

El bot (`enterprise_bot.py`) tiene 8,729 líneas. Añadir los comandos directamente en el archivo principal violaría el principio de responsabilidad única y haría el mantenimiento inviable.

---

## Decisión

### Patrón de integración: módulo separado + monkeypatch post-clase

Se crea `omnix_services/telegram_service/commands/governance_commands.py` con los 4 handlers de gobernanza como funciones independientes (con `self` como primer argumento). Se enlazan al bot mediante asignación directa a la clase después de su definición:

```python
# enterprise_bot.py — después de class EnterpriseTelegramBot
if _GOVERNANCE_COMMANDS_AVAILABLE:
    EnterpriseTelegramBot.evaluar_command    = evaluar_command
    EnterpriseTelegramBot.gobernanza_command = gobernanza_command
    EnterpriseTelegramBot.velos_command      = velos_command
    EnterpriseTelegramBot.recibo_command     = recibo_command
```

**Alternativas descartadas:**

| Alternativa | Motivo de descarte |
|---|---|
| Import directo del módulo `sandbox.py` | Bot y web server son servicios Railway separados — imposible sin duplicar código |
| Añadir handlers directamente en `enterprise_bot.py` | Archivo ya tiene 8,729 líneas; viola SRP |
| API call autenticada con X-API-Key | Overhead innecesario para llamada interna; OMNIX_WEB_URL ya provee aislamiento |

### Comunicación con el Sandbox

`/evaluar` usa HTTP POST a la variable de entorno `OMNIX_WEB_URL` (default: `http://localhost:5000`):

```
POST {OMNIX_WEB_URL}/api/public/sandbox/evaluate
Content-Type: application/json

{
  "scenario": "<texto libre del usuario>",
  "entity_name": "Telegram Evaluation",
  "language": "auto"
}
```

**Timeout:** 60 segundos (el pipeline Gemini puede tardar 20-40s).  
**Rate limit interno:** 5 evaluaciones/hora por `user_id` de Telegram, gestionado en memoria (`_EVAL_RATE_LIMIT`).  
**Mensaje de espera:** enviado inmediatamente (`processing_msg`) y editado con el resultado — nunca deja al usuario sin feedback.

### Acceso admin-only: `/velos` y `/recibo`

Ambos comandos usan `_check_admin_permission()` (ya implementado en `enterprise_bot.py` línea ~373) para restringir el acceso.

La consulta va directa a PostgreSQL (`DATABASE_URL`) sin pasar por la API REST, porque:
- El bot ya tiene acceso a `DATABASE_URL` (servicio trusted en Railway).
- Evita la latencia de una segunda llamada HTTP.
- Las tablas consultadas (`velos_push_log`, `decision_receipts`) son de lectura.

### Resiliencia: stubs de fallback

Si `governance_commands.py` falla al importar (dependencia ausente, etc.), el bot no crashea. Se instalan stubs que responden con un mensaje de error controlado:

```python
else:
    async def _governance_stub(self, update, context):
        await update.message.reply_text("⚠️ Módulo de gobernanza no disponible.")
    EnterpriseTelegramBot.evaluar_command = _governance_stub
    # ...
```

---

## Comandos implementados

| Comando | Acceso | Descripción |
|---|---|---|
| `/evaluar [escenario]` | Público | Pipeline 11-checkpoint. HTTP → sandbox. Receipt ID en respuesta. |
| `/evaluate [scenario]` | Público | Alias inglés de `/evaluar` |
| `/gobernanza` | Público | Dashboard: Critical Override Layer (7 grupos), posición OMNIX, health ping |
| `/governance` | Público | Alias inglés de `/gobernanza` |
| `/velos` | Admin only | Log de pushes al gateway Velos: disposition, HTTP status, latencia |
| `/recibo [n]` | Admin only | Últimos N recibos PQC (default 3, max 10) |
| `/receipt [n]` | Admin only | Alias inglés de `/recibo` |

---

## Contrato de respuesta `/evaluar`

El bot espera que el sandbox devuelva el siguiente JSON:

```json
{
  "decision": "BLOCKED | APPROVED",
  "checkpoints_passed": 8,
  "checkpoints_blocked": 3,
  "checkpoints_total": 11,
  "receipt_id": "OMREC-2026-04-06T...",
  "explanation": "Texto explicativo del resultado..."
}
```

Si el campo `receipt_id` está presente, el bot lo muestra y añade el enlace `omnixquantum.net` para verificación pública.

---

## Configuración de entorno (Railway)

| Variable | Valor de ejemplo | Descripción |
|---|---|---|
| `OMNIX_WEB_URL` | `https://stellar-hope.railway.app` | URL del servicio web OMNIX en Railway. Default: `http://localhost:5000` para dev local. |
| `DATABASE_URL` | `postgresql://...` | PostgreSQL compartido. Ya configurado en el bot. |
| `ADMIN_ALLOWED_IPS` | `73.252.145.159` | IPs admin para la API REST (no afecta al bot directamente). |

> **CRÍTICO:** El bot y el web server son servicios Railway **separados**. En producción, `OMNIX_WEB_URL` debe apuntar a la URL pública del servicio `stellar-hope`, no a `localhost`.

---

## Seguridad

- **Errores internos nunca expuestos al usuario:** todos los `except` capturan la excepción, loguean el stack trace con `logger.error()` y responden al usuario con un mensaje amigable genérico.
- **Rate limit por user_id:** `/evaluar` limita a 5 llamadas/hora para evitar agotamiento de cuota Gemini.
- **Admin-only gates:** `/velos` y `/recibo` verifican `_check_admin_permission()` antes de ejecutar cualquier query.
- **Sin exposición de SQL ni credenciales:** las queries usan parámetros posicionales (`%s`).

---

## Consecuencias

**Positivas:**
- Harold puede demostrar OMNIX governance en tiempo real desde su teléfono ante cualquier inversor.
- El pipeline de 11 checkpoints tiene ahora un canal de interacción conversacional.
- Los comandos son extensibles sin tocar `enterprise_bot.py` (solo `governance_commands.py`).
- Fallback resiliente: el bot no crashea si governance_commands falla.

**Negativas / Riesgos:**
- Si `OMNIX_WEB_URL` no está configurado en Railway, `/evaluar` apunta a `localhost:5000` y falla en producción. **Mitigación:** Railway env var configurada antes del redeploy.
- El rate limit en memoria se pierde con cada restart del bot. **Mitigación:** aceptable en fase pre-seed; migrar a Redis si el bot escala a múltiples usuarios.

---

## Archivos afectados

```
omnix_services/telegram_service/
├── enterprise_bot.py                      # Import + binding + registro de handlers + /version, /start, /help
└── commands/
    ├── __init__.py                         # Paquete
    └── governance_commands.py             # 4 handlers de gobernanza (ADR-058)
```

---

## Aprobación

| Rol | Nombre | Fecha |
|---|---|---|
| Fundador / Autor | Harold Nunes | 2026-04-06 |
| Revisor arquitectónico | Subagent Architect (OMNIX) | 2026-04-06 |
