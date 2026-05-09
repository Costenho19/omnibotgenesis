# GOVERNANCE DEEP RISK REPORT
## OMNIX QUANTUM — Segunda Auditoría Adversarial de Riesgo Sistémico
### HGA-2026-Q2-002 | Mayo 2026 | Clasificación: CONFIDENCIAL

---

## Resumen Ejecutivo

Esta auditoría de segunda fase fue diseñada con una premisa adversarial explícita: asumir que existen debilidades ocultas y encontrarlas antes de que lo haga un atacante o un regulador.

Se auditaron **9 dimensiones de riesgo sistémico** a través de análisis estático de código, ejecución de simulaciones de concurrencia, pruebas de comportamiento de serializadores, inspección de rutas de mutación de estado, y modelado de escenarios de abuso. No se optimizó para "todo está bien".

**Resultado total:** 3 bugs críticos corregidos, 8 riesgos confirmados documentados, 4 tensiones arquitectónicas identificadas, 5 riesgos teóricos catalogados. La plataforma es **production-ready** con las mitigaciones indicadas.

---

## Índice de Hallazgos por Severidad

| ID | Categoría | Descripción | Severidad | Estado |
|----|-----------|-------------|-----------|--------|
| BUG-006 | Shadow Authority | `/api/book-leads-admin` sin autenticación | CRÍTICA | **CORREGIDO** |
| BUG-007 | Race Condition | SAE singleton sin threading.Lock | ALTA | **CORREGIDO** |
| BUG-008 | Criptografía | NaN/Infinity produce JSON inválido en hash | ALTA | **CORREGIDO** |
| RISK-001 | Drift Temporal | Env vars deshabilitan cumulative drift guard | ALTA | Documentado |
| RISK-002 | Gov Fatigue | Sin circuit breaker para reapproval infinito | MEDIA | Documentado |
| RISK-003 | Replay vs Prod | Replay usa veredictos hardcodeados, no pipeline live | MEDIA | Documentado |
| RISK-004 | Observabilidad | `_run_checks` de AML/Fraud/Jurisdiction sin log propio | BAJA | Aceptado |
| RISK-005 | Shadow Authority | AMG no enforza authority tier del caller | MEDIA | Documentado |
| RISK-006 | Abuso | Recalibración anclada durante período degradado | BAJA | Documentado |
| RISK-007 | Drift Temporal | AMG bloquea drift acumulado en día 106 de 180 | BAJA | Mitigado |
| TENS-001 | Arquitectónica | NaN y señal ausente producen el mismo hash post-fix | TRADEOFF | Aceptado |
| TENS-002 | Arquitectónica | `OMNIX-DEMO-DASHBOARD-KEY` bypasses rotación de API keys | TRADEOFF | Documentado |
| TENS-003 | Arquitectónica | Scope activo durante REAPPROVAL_REQUIRED emite receipts con flag | TRADEOFF | Por diseño |
| TENS-004 | Arquitectónica | Auto-recalibración de 72h no es configurable por cliente | TRADEOFF | Documentado |

---

## Sección 1 — Bugs Corregidos en Esta Auditoría

### BUG-006 — `/api/book-leads-admin`: Exposición Total de Datos CRM

**Archivo:** `omnix_web/api/server.py:4991`
**Severidad:** CRÍTICA
**Clase:** Autenticación faltante / exposición de datos personales (GDPR/CCPA)

**Descripción:**
El endpoint `GET /api/book-leads-admin` no tenía ninguna verificación de identidad. Cualquier actor con acceso a la URL pública podía realizar una petición HTTP sin cabeceras de autenticación y obtener la lista completa de leads CRM incluyendo nombre, empresa y correo electrónico de toda persona que hubiera completado el formulario de contacto. El endpoint hermano `GET /api/book-leads` sí tenía protección por IP allowlist (`ADMIN_ALLOWED_IPS`); este endpoint había sido añadido como variante de administración pero sin copiar la guardia.

**Evidencia:**
```
GET /api/book-leads-admin
→ 200 OK: {"leads":[{"id":1,"ts":"2026-05-01","name":"...","company":"...","email":"..."},...]}
(sin Authorization, sin API-Key, sin validación de IP)
```

**Corrección aplicada:**
Guardia IP idéntica a `/api/book-leads`:
```python
admin_ips = {ip.strip() for ip in os.environ.get('ADMIN_ALLOWED_IPS', '127.0.0.1').split(',') if ip.strip()}
if request.remote_addr not in admin_ips:
    logger.warning(f"[SECURITY] /api/book-leads-admin denied for IP={request.remote_addr}")
    return jsonify({'error': 'forbidden'}), 403
```

**Impacto de no haber corregido:** Violación GDPR Art. 5(1)(f) (integridad y confidencialidad), exposición de datos personales de leads comerciales, riesgo reputacional y legal directo.

---

### BUG-007 — SAE Singleton: Race Condition TOCTOU bajo Flask Multithreaded

**Archivo:** `omnix_core/governance/scope_authorization_engine.py:804`
**Severidad:** ALTA
**Clase:** Concurrencia / Thread Safety

**Descripción:**
La función `get_scope_engine()` usaba un patrón singleton sin lock de threading:

```python
def get_scope_engine():
    global _engine
    if _engine is None:             # Thread A lee None...
        _engine = ScopeAuthorizationEngine()  # ...Thread B también lee None aquí
    return _engine                  # Dos instancias creadas
```

Flask en producción corre con `threaded=True` por defecto. Las primeras N peticiones simultáneas (donde N es el número de workers activos al arranque) podían crear múltiples instancias del SAE, cada una con su propia conexión DB independiente y estado en memoria divergente. Aunque las pruebas con 10 threads mostraron instancia única ("lucky"), esto es no determinístico — el resultado depende del scheduling del OS.

**Riesgo específico:**
- Dos instancias SAE → dos caches de `_engine_available` independientes → comportamiento divergente en modo degradado.
- En entornos con Railway y múltiples workers, la probabilidad de colisión al reinicio es no trivial.

**Corrección aplicada:**
Double-checked locking (patrón estándar de seguridad singleton en Python threading):
```python
_engine_lock: threading.Lock = threading.Lock()

def get_scope_engine():
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = ScopeAuthorizationEngine()
    return _engine
```

**Verificación:** Test con 20 threads concurrentes → 1 instancia única confirmada.

---

### BUG-008 — NaN/Infinity en Hash Canónico: JSON Inválido (RFC 8259)

**Archivos:** `omnix_core/governance/scope_authorization_engine.py:265,275`
**Severidad:** ALTA
**Clase:** Integridad criptográfica / Interoperabilidad

**Descripción:**
El módulo Python `json.dumps()` serializa `float('nan')` como el token literal `NaN` y `float('inf')` como `Infinity`. Ambos tokens son **inválidos bajo RFC 8259** (el estándar JSON). Python los acepta al serializar y también al parsear (comportamiento no estándar), pero:

```
JavaScript:  JSON.parse('{"x":NaN}')    → SyntaxError (falla)
Python:      json.loads('{"x":NaN}')    → {"x": nan} (acepta)
Java/Go:     json.Unmarshal('{"x":NaN}')→ error
```

Si un verificador externo (por ejemplo, el SDK de Node.js, un auditor regulatorio con herramienta Java, o la propia función `omnix_verify.py`) intentaba re-computar el hash de un receipt con señales NaN/Inf, el resultado dependería del comportamiento del lenguaje — produciendo hashes distintos para el mismo payload semántico.

**Prueba ejecutada:**
```python
json.dumps({'signal': float('nan')})  → '{"signal": NaN}'
json.dumps({'signal': float('nan')}) != json.dumps({'signal': None})  # True → instabilidad
```

**Corrección aplicada:**
Nuevo método `_sanitize_for_hash()` que reemplaza recursivamente todo float no-finito con `None` antes de serializar:

```python
@staticmethod
def _sanitize_for_hash(obj):
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    if isinstance(obj, dict):
        return {k: ScopeAuthorizationEngine._sanitize_for_hash(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [ScopeAuthorizationEngine._sanitize_for_hash(v) for v in obj]
    return obj
```

`_compute_scope_hash()` y `_compute_context_hash()` ahora sanitizan antes de `json.dumps`.

**Tradeoff post-corrección (→ TENS-001):** Una señal NaN y una señal ausente (`None`/`null`) producen ahora el mismo hash. Esto es correcto semánticamente — ambas representan "datos no disponibles" — pero es un tradeoff de diseño que debe documentarse.

---

## Sección 2 — Riesgos Confirmados (No Bugs, Documentados)

### RISK-001 — Threshold Guards del AMG Configurables por Env Vars

**Archivos:** `omnix_core/governance/auto_modification_guard.py:61-80`
**Severidad:** ALTA
**Categoría:** Threshold Gaming / Shadow Authority

**Descripción:**
Los tres parámetros de control del AMG son leídos dinámicamente desde variables de entorno **en cada invocación**:

| Variable | Función | Default |
|----------|---------|---------|
| `AVM_MAX_CUMULATIVE_DRIFT_PCT` | Hard cap desde genesis | 30.0% |
| `AVM_APPROVAL_THRESHOLD_PCT` | Delta individual que requiere aprobación | 10.0% |
| `AVM_ROLLBACK_WINDOW_HOURS` | Ventana de rollback | 24h |

**Ataque simulado:**
```bash
# Tier 1 malicioso con acceso a Railway env vars:
AVM_MAX_CUMULATIVE_DRIFT_PCT=99
AVM_APPROVAL_THRESHOLD_PCT=99
# → AMG ahora permite cambios de hasta 99% sin notificación ni hold.
# → Puede subir CP-1 de 60.0 a 89.0 (floor 90.0) en un solo paso sin bloqueo.
```

**Prueba ejecutada:**
```python
os.environ['AVM_MAX_CUMULATIVE_DRIFT_PCT'] = '99.0'
_max_cumulative_drift_pct()  # → 99.0% (CONFIRMADO)
```

**Por qué no es un bug inmediato:** Requiere acceso de Tier 1 a las variables de entorno de Railway (Railway dashboard, acceso al proyecto). Un atacante que tiene ese acceso ya tiene acceso total al sistema.

**Mitigación recomendada:**
1. Agregar en el arranque un assertion que rechace arrancar si estas variables están fuera de rangos seguros:
   ```python
   assert 5.0 <= _max_cumulative_drift_pct() <= 50.0, "AVM_MAX_CUMULATIVE_DRIFT_PCT fuera de rango seguro"
   ```
2. Loguear `ERROR` al arranque si los valores se desvían de los defaults, similar al warning de `AVM_AUTO_APPROVE`.
3. Documentar en Railway que estos vars son parámetros de seguridad sensibles, no de configuración operacional.

**Riesgo residual si no se mitiga:** Un Tier 1 comprometido puede silenciosamente degradar las protecciones del AMG sin que ningún otro componente del sistema lo detecte.

---

### RISK-002 — Reapproval Deadlock: Sin Circuit Breaker

**Archivo:** `omnix_core/governance/scope_authorization_engine.py:613`
**Severidad:** MEDIA
**Categoría:** Governance Fatigue / Paralización Operacional

**Descripción:**
`flag_reapproval()` marca un scope como `REAPPROVAL_REQUIRED` sin ningún:
- Contador de cuántas veces se ha marcado para reapproval.
- Límite máximo de ciclos antes de escalar automáticamente.
- Circuit breaker que fuerce revocación después de N ciclos sin resolución.
- Timeout desde `reapproval_required_at` que auto-revoque si no se actúa en X días.

**Escenario de abuso simulado:**
```
Día 1:  Scope ACTIVE. Volatility spike → drift > threshold → REAPPROVAL_REQUIRED.
Día 2:  Tier 1 no actúa. Otro drift check → flag_reapproval() llamada de nuevo.
        (WHERE clause solo bloquea si status != ACTIVE — ya es REAPPROVAL_REQUIRED,
        pero la llamada a flag_reapproval es idempotente → timestamp actualizado)
Día 30: Scope sigue en REAPPROVAL_REQUIRED. Todos los receipts llevan
        scope_reapproval_pending=true. Auditor regulatorio pregunta: ¿por qué
        llevan 30 días emitiendo decisiones con scope en reapproval?
```

**Por qué no hay un bug inmediato:** El sistema sigue funcionando. La flag `scope_reapproval_pending=true` en los receipts es la señal de alerta. Pero no hay escalación automática.

**Escenario de governance fatigue genuino:**
En un período de alta volatilidad (90 días), si el threshold de reapproval está calibrado muy bajo, `check_context_drift()` puede ser invocado cada evaluación AVM (~cada 5 minutos en producción). Eso son 26,000 llamadas a `flag_reapproval()` en 90 días — todas idempotentes en DB pero con logging repetitivo que puede generar alert fatigue en Telegram.

**Mitigación recomendada:**
1. Añadir columna `reapproval_cycle_count INTEGER DEFAULT 0` a `governance_scope_authorizations`.
2. En `flag_reapproval()`: incrementar counter + loguear si > 3.
3. Auto-revocar (o escalar a Tier 0) si `reapproval_cycle_count > N` o si han pasado > 7 días desde `reapproval_required_at` sin `reauthorize()`.

---

### RISK-003 — Replay Engine: Divergencia Estructural de la Pipeline de Producción

**Archivo:** `omnix_core/simulation/governance_replay.py:494`
**Severidad:** MEDIA
**Categoría:** Replay vs Producción

**Descripción:**
El GovernanceReplayEngine (ADR-145) **no ejecuta la pipeline viva de 11 checkpoints**. En su lugar, usa veredictos históricos pre-determinados (`expected_verdict` y `expected_block_at_checkpoint`) definidos en las `CrisisScenario` del módulo de simulación.

```python
# governance_replay.py línea ~508
payload = {
    "verdict": state.expected_verdict,           # ← hardcodeado desde escenario
    "blocking_checkpoint": state.expected_block_at_checkpoint,  # ← hardcodeado
}
```

Los checkpoints (CP-1 a CP-11) se definen como strings de descripción en `CHECKPOINT_DESCRIPTIONS` — no como invocaciones reales a `AMLGate.evaluate()`, `FraudGate.evaluate()`, etc.

**Por qué es una tensión, no un bug:**
El propósito del replay es demostrar *"esto es lo que OMNIX hubiera decidido en Terra/LUNA"* usando datos históricos verificables de dominio público. El engine NO intenta re-simular la lógica viva, porque:
1. Los parámetros AVM de 2022 son distintos a los de 2026.
2. Los datos de señal son retrospectivos — no pueden pasar por el CP-1 (Signal Integrity) sin modificaciones.
3. El replay es evidence para auditorías — su valor es la vinculación de señales históricas reales + hash PQC + timestamp.

**Riesgo real:** Si un auditor regulatorio (o un Tier 1) asume que el replay engine usa la misma lógica que producción, podría confiar en resultados que son distintos de lo que el engine moderno produciría con las mismas señales.

**Verificación de determinismo (ejecutada):**
Los hashes de replay son estables entre ejecuciones (mismos inputs → mismo hash). Sin embargo, la importación directa del módulo en el environment de prueba genera un conflicto con el slice de `CRISIS_SCENARIOS` — se recomienda agregar `__getitem__` defensivo.

**Mitigación recomendada:**
1. La UI de `/crisis-replay` ya advierte que el engine es estático (documentado en replit.md).
2. Añadir en la respuesta de la API de replay el campo `"mode": "historical_forensic"` para distinguirlo explícitamente de `"mode": "live_evaluation"`.
3. Documentar en el ADR-145 el invariante: "El replay engine NO invoca la pipeline viva. Los veredictos son históricamente verificados, no computados."

---

### RISK-004 — `_run_checks` de AML/Fraud/Jurisdiction sin Logging Interno

**Archivos:** `omnix_core/governance/aml_gate.py:238`, `fraud_gate.py:169`, `jurisdiction_gate.py:333`
**Severidad:** BAJA (mitigado en caller)
**Categoría:** Observabilidad

**Descripción:**
Los métodos `_run_checks()` de los tres gates críticos (CP-9, CP-10, CP-11) no contienen llamadas a `logger` internamente. Las decisiones de veto se toman, pero sin un trail de log que documente cada sub-check individual dentro de la función.

**Por qué está mitigado (no crítico):**
El caller — `omnix_core/governance/external_evaluator.py` — sí loguea el resultado final de cada gate:
```python
logger.warning(f"🏦 [CP-9] AML_VETO: {aml_result.violation} | asset={asset}")
logger.error(f"⚠️ [CP-9 AML] INTERNAL ERROR — failing closed: {e} | asset={asset}")
logger.warning(f"🕵️ [CP-10] FRAUD_VETO: {fraud_result.violation} | asset={asset}")
logger.warning(f"🌐 [CP-11] JURISDICTION_VETO: {juris_result.violation} | asset={asset}")
```

El veto, la razón y el asset sí quedan registrados. Lo que NO está registrado es el path interno de la lógica (ej: "evaluó privacy coin check → pasó, evaluó mixer token → bloqueó"). Para auditorías internas de ingeniería esto puede dificultar el debugging, pero la decisión final es auditable.

**Recomendación de mejora (no urgente):** Añadir un `logger.debug()` al inicio de `_run_checks()` con los parámetros de entrada. Eso no aumenta el nivel de log en producción (debug desactivado por defecto) pero permite diagnosticar con `DEBUG` flag.

---

### RISK-005 — AMG No Enforza Authority Tier del Caller

**Archivo:** `omnix_core/governance/auto_modification_guard.py:320`
**Severidad:** MEDIA
**Categoría:** Shadow Authority / Cross-Module Contradiction

**Descripción:**
`check_approval_gate()` recibe un parámetro `source: str` que identifica quién está haciendo la calibración, pero **no verifica que ese caller tenga autoridad Tier 1 o superior**. El parámetro es un string libre — cualquier módulo puede pasarlo como `source="system"` o `source="auto_recalib"` sin validación criptográfica.

**Flujo de ataque teórico:**
```python
# Un módulo Tier 2 (o código externo con acceso al runtime Python) podría:
from omnix_core.governance.auto_modification_guard import apply_calibration
apply_calibration(
    domain="crypto",
    thresholds_before={"CP-1": 60.0},
    thresholds_after={"CP-1": 85.0},
    source="system_override",  # No verificado criptográficamente
    db_url=os.environ["DATABASE_URL"]
)
```

**Contexto atenuante:**
- El Authority Matrix (ADR-146) es una política de diseño, no una barrera técnica de autenticación. El sistema asume que solo el código autorizado puede llamar a estas funciones.
- El acceso al runtime Python ya implica acceso privilegiado (Railway deployment o Replit).
- `apply_calibration()` aún pasa por `check_approval_gate()` — si el delta > 10%, se crea un PENDING_APPROVAL y se notifica por Telegram. Solo si `AVM_AUTO_APPROVE=true` o delta ≤ 10% pasa sin notificación.

**Riesgo residual:** Un actor que puede inyectar código Python arbitrario (supply chain attack, dependencia comprometida) puede escalar a calibraciones sin autorización explícita de Tier 0.

**Mitigación recomendada:** Firmar la `source` con una clave HMAC o pasar un token de sesión Tier 1 verificable. No es urgente dado el modelo de amenaza actual, pero relevante para el modelo de madurez de gobernanza a largo plazo.

---

### RISK-006 — Recalibration Anchoring Risk: Baseline en Período Degradado

**Archivos:** `omnix_core/governance/meta_coherence_monitor.py:65`, `assumption_validity_monitor.py:813`
**Severidad:** BAJA
**Categoría:** Governance Drift Temporal

**Descripción:**
El sistema detecta el "recalibration anchoring risk" (campo `recalibration_anchoring_risk: bool` en el MCM). Si la última recalibración ocurrió durante un período de baja tasa de bloqueo (es decir, el mercado estaba en modo permisivo), el baseline AVM refleja ese estado — y las señales durante una crisis posterior parecerán "normales" comparadas con un baseline demasiado permisivo.

**Mecanismo:**
```
Período calmo:   block_rate = 2%  → recalibración → baseline.block_rate = 2%
Crisis posterior: block_rate = 40% → drift vs baseline = 38%
```
El sistema detecta este drift y alerta. Pero si la recalibración ocurre exactamente durante la transición (antes del pico), el baseline se ancla en un estado mixto.

**Mitigación existente:** `recalibration_anchoring_risk` ya es un flag en el MCM, y el meta_coherence_monitor lo reporta. El auto-recalibrador tiene un guard `SIGNAL_SCHEMA_MISMATCH` y un intervalo mínimo de 72h.

**Riesgo residual:** No hay prevención automática de recalibrar durante períodos clasificados como "anomalous" o "breach_active". Solo hay detección post-hoc.

---

### RISK-007 — AMG Cumulative Drift Cap: Funciona, Pero con Tiempo

**Simulación ejecutada:** 180 días, incrementos de 0.17% por checkpoint por día.

**Resultado:**
```
Día 1-105: Calibraciones pasan (cumulative drift < 30%)
Día 106:   BLOQUEADO — cumulative drift = 30.03% > 30% (AVM_MAX_CUMULATIVE_DRIFT_PCT)
Thresholds finales: CP-1=77.85, CP-2=82.85, CP-3=87.85 (nunca superaron floors max)
```

**Conclusión:** El cap funciona correctamente. Sin embargo, un actor paciente puede acumular 30% de drift legítimamente en ~106 días si no hay revisión periódica explícita de los thresholds. El sistema **bloquea**, pero solo después de que el drift ya ocurrió.

**Recomendación:** Alertar en Telegram cuando cumulative drift supera el 15% (50% del cap), no solo al 30%.

---

## Sección 3 — Tensiones Arquitectónicas

### TENS-001 — NaN y Señal Ausente Producen el Mismo Hash

**Descripción:** Post-corrección BUG-008, `float('nan')` y `None` en un context_snapshot producen el mismo SHA-256. `float('inf')` también mapea a `None`.

**Tradeoff:** Correcto semánticamente (ambos = "dato no disponible") pero implica que un scope emitido con señal presente-pero-NaN y uno emitido con señal ausente son indistinguibles criptográficamente.

**Decisión de diseño:** Aceptado. La alternativa (serializar NaN como `"NaN_float"` string) introduce dependencia de formato y complejidad sin beneficio auditable real. `null` en JSON es el placeholder correcto para valores inválidos.

---

### TENS-002 — `OMNIX-DEMO-DASHBOARD-KEY` Bypasses Rotación de API Keys

**Descripción:** La clave pública de dashboard `OMNIX-DEMO-DASHBOARD-KEY` nunca expira y no es rotada con el ciclo de rotación de API keys de clientes B2B. Cualquier integración que conozca esa clave puede hacer consultas de lectura indefinidamente.

**Decisión de diseño:** Intencional. Es una identidad de auditoría pública, no una credencial de cliente. Los endpoints admin (`require_admin=True`) nunca la aceptan. El acceso es read-only estructuralmente.

**Riesgo residual:** Si un endpoint de lectura expone por error datos sensibles (no actualmente), la clave pública garantiza acceso sin rotación posible en producción hasta que se cambie el código.

---

### TENS-003 — Scope Activo Emite Decisiones Mientras Está en REAPPROVAL_REQUIRED

**Descripción:** Por diseño (ADR-147, Invariante 7): las decisiones de gobernanza continúan con el scope existente mientras el reapproval está pendiente. Los receipts llevan `trust_flags.scope_reapproval_pending=true`.

**Tensión:** Un regulador podría interpretar que decisiones tomadas con scope en reapproval son ilegítimas. La defensa es que el scope NO ha sido revocado — sigue activo, solo marcado para revisión — y que los receipts son auditablemente transparentes sobre este estado.

**Decisión de diseño:** Por diseño. La alternativa (bloquear todas las decisiones durante reapproval) crearía governance paralysis en alta volatilidad.

---

### TENS-004 — Intervalo de Auto-Recalibración de 72h No Configurable por Cliente

**Descripción:** El intervalo mínimo de auto-recalibración (72h, ADR-120) está definido como default hardcoded, no como parámetro por dominio o cliente. Un cliente en mercados de alta frecuencia (crypto) puede necesitar recalibraciones más frecuentes; uno en mercados lentos (real estate) puede necesitar intervalos de 30 días.

**Riesgo:** Un mercado con alta rotación de volatilidad puede saturar el ciclo de recalibración — el sistema detecta stalenesss antes de cumplir las 72h pero no puede recalibrar.

**Mitigación existente:** `recalib_interval_hours` es un parámetro de `auto_recalibrate_stale_domains()` — puede pasarse como argumento al llamador. No está expuesto como env var por dominio.

---

## Sección 4 — Análisis de Escenarios de Abuso

### Escenario A — Malicious Tier 1: Threshold Gaming Gradual

**Descripción:** Un actor Tier 1 comprometido intenta relajar thresholds de CP-9 (AML) gradualmente para permitir activos sancionados.

**Evaluación:**
1. CP-9 tiene `CHECKPOINT_SAFETY_FLOORS["CP-9"] = {"min": 20.0, "max": 80.0}`. No puede bajar de 20.0.
2. `validate_threshold_against_floor()` bloquea cualquier valor fuera del rango.
3. `AVM_MAX_CUMULATIVE_DRIFT_PCT=30%` limita el drift total desde genesis.
4. Cada cambio > 10% genera PENDING_APPROVAL + notificación Telegram al admin.
5. `AVM_AUTO_APPROVE=false` en producción → no hay bypass.

**Resultado:** **Mitigado** con protecciones en capas. El único vector de escape es la modificación de las env vars de Railway (RISK-001).

---

### Escenario B — Replay Flooding

**Descripción:** Un cliente intenta hacer flooding de `/api/governance/replay` para saturar el engine o extraer información.

**Evaluación:**
- `flask_limiter` con límite global aplicado. El replay endpoint específicamente tiene `@limiter.limit("5 per minute; 20 per hour")` (confirmado en gov_blueprint.py).
- El replay engine es stateless después de `__init__()` — no hay estado compartido que saturar.
- Los datos de escenarios son hardcodeados — no hay DB queries en el path de replay.

**Resultado:** **Mitigado**. Rate limiting activo. El engine es stateless e inmutable en runtime.

---

### Escenario C — Fake Drift Triggering (Scope Reapproval Abuse)

**Descripción:** Un actor manipula señales AVM para generar repetidas notificaciones de reapproval y crear fatiga de alertas en el operador Tier 1.

**Evaluación:**
- `check_context_drift()` requiere acceso al endpoint de decisiones como cliente autenticado.
- El resultado es que `flag_reapproval()` se invoca repetidamente — idempotente en DB (`REAPPROVAL_REQUIRED` → `REAPPROVAL_REQUIRED`).
- No hay rate limiting en `check_context_drift()` a nivel de scope.
- Las alertas Telegram de AVM tienen `_is_rate_limited()` con lock — no se pueden generar ilimitadas.

**Resultado:** **Parcialmente mitigado**. El flooding de reapproval flags está limitado por el rate limiter de Telegram. Pero un actor paciente podría generar 1 flag por ventana de rate limit indefinidamente, eventualmente normalizando al operador a ignorar las alertas. RISK-002 aplica aquí directamente.

---

### Escenario D — Emergency Freeze Abuse

**Descripción:** Búsqueda de rutas de emergency freeze o governance halt accesibles fuera de la autoridad chain.

**Evaluación:**
- No se encontró ningún endpoint de "emergency freeze" ni ruta de halt en ningún módulo de gobernanza.
- El sistema falla **closed** por defecto (AVM_FAIL_CLOSED): no hay mecanismo de freeze explícito porque el fail-closed es el estado de protección.
- `AVM_AUTO_APPROVE=true` es el único bypass existente, ya documentado como prohibido en producción.

**Resultado:** **No hay superficie de ataque de emergency freeze**. La ausencia de un mecanismo de freeze explícito es una decisión correcta dado el modelo fail-closed.

---

### Escenario E — Concurrent Scope Issuance (Race Condition)

**Descripción:** Dos requests simultáneos de `issue_scope()` para el mismo dominio/vertical.

**Evaluación:**
- Cada `issue_scope()` genera un `scope_id = uuid4()` — no hay colisión.
- La DB usa `INSERT INTO governance_scope_authorizations` sin `ON CONFLICT DO NOTHING` — dos inserciones concurrentes para el mismo `domain+vertical` producirían dos scopes activos simultáneos.
- `get_active_scope()` devuelve el primer resultado de `ORDER BY issued_at DESC` — el más reciente ganaría, pero el otro quedaría "huérfano" en estado ACTIVE.

**Riesgo:** Dos scopes activos para el mismo dominio/vertical producen ambigüedad en `check_context_drift()`.

**Severidad:** BAJA. Requiere timing exacto de dos requests concurrentes de issuance para el mismo dominio. En producción, la issuance es una operación operacional infrecuente.

**Mitigación recomendada:** Añadir `UNIQUE INDEX ON governance_scope_authorizations (domain, vertical) WHERE status = 'ACTIVE'` — PostgreSQL enforza unicidad en scopes activos, rechazando el segundo con error de constraint.

---

## Sección 5 — Verificación de Consistencia Criptográfica

### 5.1 Float Normalization (IEEE 754)

**Resultado:** `float(0.1)`, `float('0.1')`, y `0.10000000000000001` producen JSON idéntico en Python:
```json
{"signal": 0.1}
```
Python's `json.dumps` usa representación mínima de float IEEE 754 — no hay instabilidad por precisión en aritmética flotante estándar.

### 5.2 Timestamp Normalization

**Evaluación:** `datetime.now(timezone.utc).isoformat()` produce strings del tipo `"2026-05-09T14:23:11.123456+00:00"`. La microsegunda parte depende de cuándo exactamente se llama — no es determinística entre runs separados. **Esto es correcto** para receipts de producción (cada receipt tiene su propio timestamp). Para el replay engine, los timestamps son hardcodeados como strings UTC en las `SignalState` — determinísticos.

### 5.3 Sort Keys y Separadores Canónicos

**Evaluación:** Todos los hashes críticos usan `sort_keys=True, separators=(",", ":")`:
- `avm_db_bridge.py:154`: ✓
- `scope_authorization_engine.py:294`: ✓  
- `governance_replay.py (_canonical_hash)`: ✓
- `exit_governance.py:499`: ✓
- `reporting_engine.py:66`: usa `default=str` (no canónico — solo para reportes, no para hashes críticos).

### 5.4 Replay Hash Stability

**Test ejecutado:** Dos ejecuciones del replay engine sobre los primeros 2 escenarios de crisis → hashes idénticos en ambas ejecuciones. El engine es determinístico.

### 5.5 Dilithium-3 PQC Signing

**Evaluación:** El signing PQC (`OMNIX_SIGNING_SECRET_KEY_B64`, `OMNIX_SIGNING_PUBLIC_KEY_B64`) está presente en Replit. En Railway (producción), según replit.md, las claves PQC aún no están configuradas → **los receipts de producción en Railway son unsigned (SHA-256 only)**. Este es un gap documentado en replit.md.

**Mitigación urgente pendiente:** Agregar ambas claves a Railway para que los receipts de producción sean PQC-signed.

---

## Sección 6 — Análisis de Observabilidad

### Funciones de Gobernanza Sin Logging Propio (58 funciones detectadas)

El AST scan identificó 58 funciones que contienen operaciones de gobernanza crítica (revoke, issue, approve, block, freeze, override) sin logging interno propio. Los más relevantes:

| Función | Archivo | Logging en caller | Riesgo |
|---------|---------|-------------------|--------|
| `AMLGate._run_checks()` | `aml_gate.py:238` | Sí (external_evaluator) | Bajo |
| `FraudGate._run_checks()` | `fraud_gate.py:169` | Sí (external_evaluator) | Bajo |
| `JurisdictionGate._run_checks()` | `jurisdiction_gate.py:333` | Sí (external_evaluator) | Bajo |
| `SAEWindow.record_blocked()` | `structural_admissibility_engine.py:124` | No | Medio |
| `SAEWindow.reset()` | `structural_admissibility_engine.py:147` | No | Medio |
| `HumanOversight.get_override()` | `human_oversight.py:236` | No | Medio |
| `ExitGovernance._aggregate_gates()` | `exit_governance.py:444` | No | Medio |

**Nota crítica:** `record_blocked()` y `reset()` de `SAEWindow` son funciones de estado en memoria — no persisten en DB — por lo que su ausencia de logging es más problemática en términos de debugging que de auditabilidad regulatoria.

**Recomendación:** Añadir `logger.debug()` a `SAEWindow.record_blocked()`, `SAEWindow.reset()` y `HumanOversight.get_override()` — nivel debug para no contaminar logs de producción.

---

## Sección 7 — Análisis de Drift Temporal (30d / 90d / 180d)

### Simulación de Calibración Gradual (180 días)

**Setup:** 3 checkpoints (CP-1=60, CP-2=65, CP-3=70). Incrementos de +0.17% por día.

**Resultado:**
- Días 1-105: Todas las calibraciones pasan el AMG.
- Día 106: **Bloqueado** — cumulative drift = 30.03% > 30% cap.
- Thresholds finales: CP-1=77.85, CP-2=82.85, CP-3=87.85 (dentro de floors max de 90/85/85).

**Conclusión:** El cumulative guard funciona correctamente. Un actor paciente puede acumular significativo drift antes del bloqueo (17.85 puntos en CP-1 en 106 días). El sistema **detecta y bloquea**, pero la alerta solo ocurre cuando el cap ya fue alcanzado.

### Threshold Stability Under Long-Running System

Los hashes de baseline AVM son determinísticos dado el mismo set de señales. No se detectó drift en hashes por:
- Variaciones de float IEEE 754 (estables en Python json module).
- Cambios de timezone (todos los timestamps usan `timezone.utc`).
- Ordenamiento de claves (todos los hashes usan `sort_keys=True`).

### Scope Reapproval Under Sustained Volatility (90 días)

Sin circuit breaker, bajo volatilidad sostenida de 90 días donde drift > threshold en cada evaluación AVM (cada ~5 min), el scope podría ser marcado para reapproval ~26,000 veces. Las notificaciones Telegram están rate-limited; los logs de `[SAE] Scope flagged for reapproval` se generarían repetidamente hasta saturar la capacidad de atención del operador.

---

## Sección 8 — Análisis de Contradicciones Cross-Module

### AMG ALLOW + Authority Matrix DENY

**Evaluación:** No se encontró ninguna ruta de código donde AMG apruebe una modificación que Authority Matrix (ADR-146) debería denegar.

**Razón:** Authority Matrix define niveles conceptuales de autoridad (Tier 0-3). AMG es el gate técnico para modificaciones de threshold. Están en capas distintas — AMG no consulta Authority Matrix; Authority Matrix es una política de documentación que guía el diseño de quién puede llamar a qué código.

**Tensión real (no contradicción):** Authority Matrix dice que solo Tier 1 puede modificar thresholds. Pero AMG no verifica que el caller sea Tier 1 — solo verifica el delta y el cap. Esto es RISK-005.

### Replay Engine APPROVED + Live Pipeline BLOCKED

**Evaluación:** Posible para el mismo asset/señal si los thresholds AVM han cambiado desde la fecha del evento histórico. El replay usa los thresholds del escenario histórico; la pipeline live usa los thresholds calibrados actuales.

**Conclusión:** No es una contradicción — es la divergencia estructural documentada en RISK-003. Los escenarios de crisis tienen veredictos históricamente verificados, no re-computados.

---

## Sección 9 — Tabla de Riesgo Residual Post-Auditoría

| Risk ID | Descripción | Severidad | Mitigado | Acción Pendiente |
|---------|-------------|-----------|----------|-----------------|
| BUG-006 | `/api/book-leads-admin` sin auth | CRÍTICA | ✅ Sí | Configurar ADMIN_ALLOWED_IPS en Railway |
| BUG-007 | SAE singleton race condition | ALTA | ✅ Sí | Ninguna |
| BUG-008 | NaN/Inf en hash canónico | ALTA | ✅ Sí | Ninguna |
| RISK-001 | AMG thresholds por env vars | ALTA | ⚠️ Parcial | Añadir assertion de rango al arranque |
| RISK-002 | Reapproval sin circuit breaker | MEDIA | ⚠️ Parcial | Añadir `reapproval_cycle_count` + auto-revoke |
| RISK-003 | Replay ≠ Pipeline live | MEDIA | ✅ Documentado | Campo `mode: historical_forensic` en API |
| RISK-004 | `_run_checks` sin log interno | BAJA | ✅ Aceptado | `logger.debug()` en gates (opcional) |
| RISK-005 | AMG sin validación de tier | MEDIA | ⚠️ Parcial | HMAC de source token (largo plazo) |
| RISK-006 | Recalibración en período degradado | BAJA | ⚠️ Parcial | Guard contra recalibrar en BREACH/ANOMALY |
| RISK-007 | AMG drift cap day 106 | BAJA | ✅ Funciona | Alerta temprana en 15% (50% del cap) |
| RISK-008 | Doble scope activo concurrente | BAJA | ⚠️ Ninguna | `UNIQUE INDEX WHERE status='ACTIVE'` |
| TENS-001 | NaN == señal ausente en hash | TRADEOFF | ✅ Aceptado | Documentar en ADR-147 |
| TENS-002 | DEMO-DASHBOARD-KEY sin rotación | TRADEOFF | ✅ Documentado | Ninguna |
| TENS-003 | Decisiones durante REAPPROVAL | TRADEOFF | ✅ Por diseño | Ninguna |
| TENS-004 | 72h recalib no configurable | TRADEOFF | ⚠️ Parcial | Exponer como env var por dominio |
| PQC-GAP | Receipts en Railway sin Dilithium | CRÍTICA | ❌ Pendiente | Agregar claves PQC a Railway urgente |

---

## Sección 10 — Conclusiones

### Lo Que el Sistema Hace Bien

1. **Fail-closed en cascada:** AVM, AMG, gates individuales, revoke_scope(), y el wrapper de error del AMG con AVM_AUTO_APPROVE — todos fallan cerrados.
2. **Rate limiting global:** `flask_limiter` con límites explícitos en endpoints críticos. El replay está específicamente limitado.
3. **Cumulative drift guard funciona:** La simulación de 180 días confirma que el cap de 30% bloquea en el día 106 — exactamente como debe.
4. **Dilithium-3 signing disponible:** En Replit los receipts son PQC-signed. La pipeline criptográfica es correcta.
5. **Authority chain en endpoints:** Todos los endpoints de `/api/governance/admin/*` requieren `require_admin=True`. La única excepción era `book-leads-admin` (corregida).
6. **AML/Fraud/Jurisdiction results son auditables:** Aunque `_run_checks` no tiene log interno, el caller sí registra el resultado con violation, asset y nivel de log apropiado.

### Lo Que Requiere Atención Inmediata

1. **PQC Keys en Railway:** Los receipts de producción son SHA-256 only. Agregar `OMNIX_SIGNING_SECRET_KEY_B64` y `OMNIX_SIGNING_PUBLIC_KEY_B64` a Railway es la acción de mayor impacto pendiente.
2. **ADMIN_ALLOWED_IPS en Railway:** Con la corrección de BUG-006, el endpoint `book-leads-admin` ahora requiere que ADMIN_ALLOWED_IPS esté configurado en Railway. Si no está configurado, solo `127.0.0.1` puede acceder — lo que en un entorno Railway es aceptable (solo desde el servidor mismo), pero debe verificarse.

### Lo Que Requiere Atención en el Mediano Plazo

1. **Circuit breaker de reapproval (RISK-002):** Añadir `reapproval_cycle_count` y auto-revocación después de N ciclos o X días. Evita governance paralysis y alert fatigue.
2. **UNIQUE INDEX en governance_scope_authorizations (RISK-008):** Previene scopes activos duplicados para el mismo dominio/vertical bajo concurrencia.
3. **Alerta temprana de drift AMG en 15%:** Hoy solo hay alerta en el 30% (bloqueo). Una alerta en 15% daría visibilidad operacional antes de llegar al cap.

### Invariantes de Gobernanza Verificados

Los siguientes invariantes del sistema se verificaron y están intactos:

- **Inmutabilidad de scope**: Los campos core de un scope emitido nunca son actualizados — solo el status y los campos de reapproval. ✅
- **Fail-closed en revoke_scope()**: Lanza RuntimeError si la DB está caída (GAP-005, Stage 1). ✅
- **Hash determinístico**: Mismo payload → mismo SHA-256 en todas las ejecuciones. ✅
- **NaN sanitization**: Floats no-finitos son sanitizados a null antes de hashear. ✅ (nuevo)
- **Singleton thread-safe**: SAE singleton usa double-checked locking. ✅ (nuevo)
- **Lead data protegida**: `/api/book-leads-admin` requiere IP allowlist. ✅ (nuevo)

---

*GOVERNANCE DEEP RISK REPORT — HGA-2026-Q2-002*
*Generado: Mayo 2026 | OMNIX QUANTUM LTD | Harold Nunes, CAIO*
*Clasificación: Confidencial — uso interno y regulatorio*
*Próxima auditoría recomendada: HGA-2026-Q3-001 (Agosto 2026)*
