# GOVERNANCE FAILURE MODE REPORT
## OMNIX QUANTUM — Auditoría Institucional de Tercera Fase
### HGA-2026-Q3-001 | Mayo 2026 | Clasificación: MÁXIMA CONFIDENCIALIDAD

---

> **Premisa de auditoría:** No asumir buenos actores, infraestructura estable, ni entornos limpios.
> Optimizar para identificar lo que podría minar de forma realista la confianza en OMNIX a escala institucional.

---

## Resumen Ejecutivo

Esta auditoría de tercera fase examina OMNIX como si ya operara dentro de una institución regulada bajo condiciones hostiles. Se simularon escenarios de colapso de gobernanza, estados byzantinos, abuso de operadores institucionales autorizados, y se clasificó explícitamente la fidelidad de cada modo de replay.

**Resultado:** 1 bug de representación corregido (UI wording). 11 modos de falla institucional documentados. 4 escenarios de colapso simulados. 5 riesgos de confianza criptográfica catalogados. La plataforma es **operacionalmente segura** con las mitigaciones urgentes indicadas.

**Acción más urgente:** Configurar `OMNIX_ANTI_REPLAY_MODE=strict` en Railway. En modo `best_effort` (default actual), un fallo de Redis en un deployment multi-dyno permite ataques de replay cross-dyno sin detección.

---

## Índice de Hallazgos por Severidad

| ID | Categoría | Descripción | Severidad | Estado |
|----|-----------|-------------|-----------|--------|
| FMR-001 | Crypto Trust | Clave efímera: receipts unverificables tras restart sin PQC keys en Railway | CRÍTICA | Pendiente (Railway) |
| FMR-002 | Byzantine | Decisión emitida sin receipt en audit trail si DB falla en store_receipt | ALTA | Documentado |
| FMR-003 | Crypto Trust | Verifier no valida que la clave pública es de OMNIX — trust gap | ALTA | Documentado |
| FMR-004 | Observabilidad | Anti-replay: modo best_effort permite replay cross-dyno cuando Redis cae | ALTA | Acción requerida |
| FMR-005 | UI / Fidelidad | CrisisReplay.tsx afirmaba "same governance engine" incorrectamente | MEDIA | **CORREGIDO** |
| FMR-006 | Insider Abuse | 2 cambios silenciosos de 9.99% inflan CP-1 de 60 a 72.6 sin notificación | MEDIA | Documentado |
| FMR-007 | Collapse Sim | TESTING=true en Railway desactiva AVM alerts y SAE background thread | MEDIA | Documentado |
| FMR-008 | Deploy Integrity | Servidor arranca sin DATABASE_URL — endpoints degradan a 503 silenciosamente | MEDIA | Documentado |
| FMR-009 | Crypto Trust | Rotación de claves PQC: solo via env var + redeploy — sin key history API | BAJA | Documentado |
| FMR-010 | Entropy | 36,500 receipts/año — no hay estrategia de archivado documentada | BAJA | Documentado |
| FMR-011 | Collapse Sim | AVM stale snapshot: decisiones continúan con STALE_BLOCK (no halt) | BAJA | Mitigado |

---

## Sección 1 — Simulaciones de Colapso de Gobernanza

### 1.1 — Colapso Multi-Capa: DB + Redis + Telegram caídos simultáneamente

**Escenario:**
```
T=0:  DB se cae (PostgreSQL partition failure)
T=1:  Redis se cae (network timeout)
T=5:  Telegram Bot API no responde (rate limit/outage)
T=10: Nueva petición de decisión llega a /api/governance/evaluate
```

**Comportamiento observado por capa:**

| Capa | Comportamiento | ¿Fail-closed? |
|------|---------------|---------------|
| AVM snapshot load | `_load_snapshot()` falla → `STALE_BLOCK` si drift > threshold | ✅ Sí |
| Receipt persistence | `store_receipt()` lanza Exception → receipt `OMNIX-ERR-{ref}` | ⚠️ Parcial |
| Anti-replay (Redis) | Fallback in-memory en `best_effort` | ⚠️ Parcial |
| Telegram alert | Exception silenciada en hilo daemon | ✅ No bloquea |
| Decisión al cliente | Se retorna con receipt de error | ⚠️ Sin audit trail |

**Conclusión del escenario:** El sistema **no entra en estado contradictorio** — las capas individuales tienen su propio comportamiento degradado. Sin embargo, hay un estado problemático: la decisión es computada y retornada al cliente (`APPROVED`, `BLOCKED`, o `HOLD`) pero no queda registrada en ninguna tabla de DB. Si el cliente actúa sobre esa decisión, el evento es **forensicamente invisible** para auditores.

**Variante más grave:** Si DB falla DESPUÉS de que el engine evalúa (APPROVED) pero ANTES de que el receipt se persista, el cliente recibe un `APPROVED` con receipt `OMNIX-ERR`. Dependiendo de cómo el cliente maneje ese receipt ID, podría:
- Rechazar la decisión (conservativo — correcto).
- Proceder con la acción asumiendo que `APPROVED` es válido (arriesgado).

### 1.2 — Rollback + Recalibración Concurrentes

**Escenario:**
```
Thread A: AMG apply_calibration() ejecutando rollback de thresholds
Thread B: auto_recalibrate_stale_domains() actualizando baseline AVM simultáneamente
```

**Análisis:**
- `apply_calibration()` en AMG es una función de DB separada — no comparte estado en memoria con `save_calibration_snapshot()`.
- El único estado compartido es la tabla `avm_calibration_snapshots` en DB.
- PostgreSQL maneja el aislamiento por transacción — las dos escrituras son seriales a nivel de fila.
- No hay deadlock posible porque las dos operaciones son UPSERT/INSERT independientes.

**Riesgo residual:** Si el rollback completa y la recalibración auto-save ocurre milisegundos después, la recalibración podría sobreescribir el estado post-rollback con una lectura de señales del período pre-rollback. El sistema no detecta este "rollback overwrite" — solo el MCM lo observaría en el siguiente ciclo de coherencia.

**Conclusión:** No produce un estado contradictorio inmediato. El MCM eventualmente flagearía la incoherencia. Riesgo BAJO operacionalmente.

### 1.3 — Authority Records Stale durante Decisiones Activas

**Escenario:** El scope de un dominio entra en `REAPPROVAL_REQUIRED` mientras 500 decisiones/hora se están procesando.

**Comportamiento (ADR-147, Invariante 7):**
- Las decisiones continúan siendo procesadas.
- Cada receipt lleva `trust_flags.scope_reapproval_pending=true`.
- El scope no es revocado automáticamente — solo flagueado.

**Riesgo institucional:** Un regulador que inspecciona los receipts del período de reapproval verá que la institución tomó 500+ decisiones con un scope marcado como "necesita reaprobación". Sin el contexto de que el sistema continúa por diseño, esto puede interpretarse como gobernanza negligente.

**Mitigación recomendada:** Añadir en el API de receipts un campo `scope_status_explanation` que explique el contexto cuando `scope_reapproval_pending=true`. Esto convierte una potencial acusación regulatoria en evidencia de transparencia.

### 1.4 — Replay Inconsistency + Degraded DB Simultáneos

**Escenario:** Un operador genera replay de una crisis histórica mientras la DB tiene corrupción parcial en `decision_receipts`.

**Comportamiento:** El replay engine no consulta `decision_receipts` — usa datos hardcodeados de `crisis_scenarios.py`. Los hashes del replay son determinísticos e inmunes a la corrupción de DB.

**Conclusión positiva:** El replay engine es **completamente aislado** de la corrupción de DB en producción. Los receipts históricos de crisis son invariantes — no se pueden corromper accidentalmente porque no vienen de la DB.

---

## Sección 2 — Análisis de Estado Byzantino

### 2.1 — Decisión Sin Receipt en Audit Trail (FMR-002)

**Código relevante (`gov_blueprint.py:~1563`):**
```python
try:
    receipt = receipt_engine.generate_receipt(decision_payload, ...)
    receipt_engine.store_receipt(receipt)   # ← si esto falla...
except Exception as e:
    ref_id = str(uuid.uuid4())[:8]
    logger.error(f"Receipt generation error ref={ref_id}: {e}")
    receipt = {
        'receipt_id': f'OMNIX-ERR-{ref_id}',
        'signature': None,
        'content_hash': None,
        # ...
    }
# La respuesta se construye DESPUÉS del try/except — siempre se retorna
```

**Estado byzantino creado:**
- **La decisión existe:** El cliente recibe `verdict=BLOCKED` (o APPROVED/HOLD).
- **El receipt no existe:** La DB no tiene registro del evento.
- **El log existe:** `logger.error` registra el `ref_id`, pero los logs no son audit trail.

**Consecuencia forense:** Si un regulador solicita el historial de decisiones para ese período, la decisión no aparecerá en `decision_receipts`. El único rastro es el log — que puede ser rotado, perdido, o no accesible para el auditor externo.

**Mitigación urgente recomendada:** Implementar una tabla `pending_receipts` de fallback:
```sql
CREATE TABLE IF NOT EXISTS pending_receipts (
    ref_id TEXT PRIMARY KEY,
    decision_payload JSONB,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```
Si `store_receipt()` falla → INSERT en `pending_receipts` (en un pool de conexión separado). Permite reconciliación post-incidente.

### 2.2 — Split Anti-Replay bajo Redis Failure en Multi-Dyno

**Escenario (Railway con ≥2 réplicas):**
```
Dyno-A y Dyno-B comparten Redis. Redis falla.
OMNIX_ANTI_REPLAY_MODE=best_effort (default actual).

Attacker:
  POST /api/governance/evaluate {receipt_id: "OMNIX-TRD-ABC123", ...} → Dyno-A → BLOCKED
  POST /api/governance/evaluate {receipt_id: "OMNIX-TRD-ABC123", ...} → Dyno-B → BLOCKED

En modo best_effort:
  Dyno-A: Redis fails → in-memory register OMNIX-TRD-ABC123 en proceso A
  Dyno-B: Redis fails → in-memory register OMNIX-TRD-ABC123 en proceso B (no ve el de A)
  Ambos dynos aceptan la petición → dos evaluaciones del mismo receipt → dos verdicts
```

**Impacto:** La misma petición con el mismo `receipt_id` puede generar dos evaluaciones independientes en dos dynos. Ambas retornan verdicts válidos. Si la intención del atacante era obtener un `APPROVED` de un dyno que no tiene el contexto de un BLOCK anterior, lo logra.

**Estado actual del deployment:** Railway con la instancia actual probablemente tiene 1 réplica. El riesgo escala con el número de réplicas.

**Corrección requerida:** Establecer `OMNIX_ANTI_REPLAY_MODE=strict` en Railway. En modo strict, si Redis falla → `ReplayDetected` raised → 503 retornado → no split posible.

**Tabla de impacto por modo:**

| Modo | Redis up | Redis down | Cross-dyno safe |
|------|----------|-----------|-----------------|
| `best_effort` (actual) | ✅ Seguro | ⚠️ In-memory fallback | ❌ NO |
| `strict` (recomendado) | ✅ Seguro | ✅ 503 fail-closed | ✅ Sí |

### 2.3 — Verificación de Receipts con Snapshotts Stale

**Escenario:** Un auditor externo intenta verificar receipts de hace 48h. El verifier consulta `decision_receipts` en DB — si los datos están corruptos parcialmente, el verifier retorna `hash_valid=false` para receipts intactos.

**Comportamiento actual:** El verifier extrae el receipt de DB y re-computa el SHA-256. Si la fila en DB fue corrompida (incluso un espacio extra en un campo TEXT), el hash no coincidirá.

**Nota:** Los receipts tienen firma PQC embebida. La firma verifica el `content_hash`, no el payload directo. Corrupción de campos no-hasheados (metadata, client_id) no afecta la verificación criptográfica.

**Mitigación existente:** El receipt JSON almacenado contiene el `content_hash` calculado al momento de emisión. Un auditor puede re-derivar el hash del payload y comparar. Suficiente para detección de corrupción.

---

## Sección 3 — Análisis de Entropía a Largo Plazo (1 Año)

### 3.1 — Volumen de Datos Proyectado

**Estimaciones conservadoras (100 decisiones/día):**

| Tabla | Filas/año | Tamaño estimado |
|-------|----------|-----------------|
| `decision_receipts` | 36,500 | ~500 MB (con JSONB) |
| `execution_receipts` | 36,500 | ~300 MB |
| `avm_calibration_snapshots` | ~1,000 | ~50 MB |
| `avm_modification_registry` (AMG) | ~150 | < 1 MB |
| `governance_scope_authorizations` | ~24 | < 1 MB |
| `filter_calibration_events` | ~3,650 | ~20 MB |

**Total estimado en 1 año:** ~870 MB en datos de gobernanza. Manejable para PostgreSQL sin archivado.

**Proyección a 3 años (1,000 dec/día, escala institucional):** ~8.7 GB/año → necesita estrategia de archivado activo después de año 2.

### 3.2 — Degradación de Explicabilidad

**Riesgo:** Después de 1 año de operación con recalibraciones repetidas, los `baseline_signals` del AVM del día 1 son irrelevantes para el día 365. La calibración de referencia (genesis) puede estar tan alejada de la realidad que el `cumulative_drift` del 30% se alcanza en condiciones normales de mercado.

**Escenario:**
- Día 1: `CP-1 = 60.0` (genesis).
- Día 106: AMG bloquea drift acumulado — threshold inflado a 77.8 (confirmado por simulación).
- Día 107: Requiere aprobación Tier 0 para continuar. Genesis se "resetea" con nuevo baseline.
- Después de 3 resets: La relación entre genesis-1 y genesis-4 es arbitraria.

**Impacto forense:** Un auditor que intenta explicar por qué el sistema tomó una decisión específica en el día 280 necesita reconstruir 3 generations de genesis. La trazabilidad es técnicamente completa (todo está en DB) pero operacionalmente compleja.

**Mitigación recomendada:** Añadir campo `genesis_generation: int` a `avm_calibration_snapshots` e incrementar en cada reset de baseline. Permite a auditores navegar directamente a la generation relevante.

### 3.3 — Replay Accumulation

Los replay receipts de crisis históricas son **estáticos** — siempre son exactamente 12 (5 crisis × ~2-3 snapshots cada una). No hay acumulación. Sin riesgo de audit bloat en este componente.

### 3.4 — Scope Reapprovals Acumulados

Con el problema documentado en HGA-2026-Q2-002 (RISK-002: sin circuit breaker), en un año de alta volatilidad podría haber cientos de registros `REAPPROVAL_REQUIRED` para el mismo scope. Aunque `flag_reapproval()` es idempotente en DB (actualiza timestamp, no inserta fila nueva), el `reapproval_required_at` se actualiza en cada llamada. Esto hace que la historia de reapprovals sea invisible — solo el último timestamp es visible.

**Impacto:** Un auditor no puede saber cuántas veces un scope fue flagueado para reapproval — solo cuándo fue flagueado por última vez. Esto oculta patrones de volatilidad operacional.

---

## Sección 4 — Abuso de Operador Institucional

### 4.1 — Inflación de Thresholds: El Rango Silencioso

**Capacidad del abusador:** Un operador Tier 1 con credenciales admin válidas.

**Simulación ejecutada (9.99% relativo, 2 pasos):**
```
Paso 1: CP-1: 60.0 → 65.99 (+9.99%) — PASS silencioso (delta < 10%)
         CP-4: 55.0 → 60.49 (+9.99%) — PASS silencioso
         CP-7: 70.0 → 76.99 (+9.99%) — PASS silencioso
         Drift acumulado: 10.0% (cap a 30%)

Paso 2: CP-1: 65.99 → 72.59 (+9.99%) — PASS silencioso
         Drift acumulado: 21.0% (cap a 30%)

Paso 3: BLOQUEADO — drift acumulado 33.1% > 30%
```

**Resultado:** En 2 pasos sin ninguna notificación de Telegram ni hold, CP-1 sube de 60.0 a 72.59. Esto relaja significativamente el checkpoint de Signal Integrity Validator — un signal con score 70 que antes hubiera fallado ahora pasa.

**Por qué el AMG no lo detiene completamente:**
- El AMG está diseñado para detectar cambios grandes ÚNICOS. Un actor paciente que hace cambios pequeños pero repetidos puede acumular drift hasta el 30% del cap en 2-3 pasos.
- Cada paso individual (9.99%) está justo por debajo del threshold de notificación (10%).

**Controles que sí funcionan:**
1. En el paso 3, el cumulative guard BLOQUEA y requiere Tier 0 approval.
2. Todos los cambios quedan en `avm_modification_registry` con diff_proof PQC-firmado.
3. El MCM detectará el drift en el siguiente ciclo de coherencia.

**Gap real:** No hay alerta cuando el cumulative drift supera el 15% (mitad del cap). La alerta solo llega al 30% (cuando ya es demasiado tarde para prevenir, solo para detectar).

### 4.2 — Selective Replay Generation

**Escenario:** Un operador genera replays selectivamente — solo de crises donde OMNIX habría aprobado, para presentarlos en materiales de marketing.

**Evaluación:** El replay engine genera los 5 escenarios con sus verdicts históricos hardcodeados. Los verdicts incluyen BLOCKED, HOLD y APPROVED según el escenario. Un operador NO puede alterar los verdicts (están en `crisis_scenarios.py`, no en DB). Un operador SÍ puede presentar solo los receipts de escenarios específicos en materiales externos.

**Conclusión:** No hay control técnico sobre qué subset de replay receipts se presenta externamente. El riesgo es de marketing selectivo, no de falsificación criptográfica.

### 4.3 — Suppression de Remediation Events

**Escenario:** Un operador con acceso a DB suprime registros de `mcm_remediation_log` para ocultar que el sistema tuvo períodos de baja coherencia.

**Controles técnicos existentes:**
- No hay endpoint API para DELETE en `mcm_remediation_log`.
- El MCM report engine lee de DB directamente — supresión requiere acceso directo a PostgreSQL.
- Railway provee logs de todas las queries SQL — suppressión en Railway dejaría rastro en logs de Railway.

**Gap:** Acceso directo a PostgreSQL (Railway admin) permite DELETE sin rastro en los logs de OMNIX.

**Mitigación recomendada:** Habilitar `pgaudit` en PostgreSQL para loguear todas las operaciones DDL/DML en tablas de gobernanza. Esto proporciona un log immutable a nivel de DB.

### 4.4 — Endless Emergency Freeze

**Búsqueda de mecanismo:** No se encontró ningún endpoint de "emergency freeze" en el codebase. El sistema no tiene un mecanismo de freeze explícito.

**Evaluación:** La ausencia de un botón de freeze es una decisión de diseño correcta. El comportamiento fail-closed del AVM (`AVM_FAIL_CLOSED=true`) es el mecanismo de halt implícito. Un operador no puede "congelar" la gobernanza indefinidamente a través de la API.

**Vector de abuso existente:** Un operador con acceso a Railway puede establecer `AVM_AUTO_APPROVE=true` — que sí desactiva el gate de aprobación del AMG. Esta es la acción más cercana a un "freeze inverso" (aprobar todo). Actualmente está documentado y loguea ERROR en cada invocación.

---

## Sección 5 — Auditoría de Límites de Confianza Criptográfica

### 5.1 — Claves Efímeras: El Riesgo Más Crítico (FMR-001)

**Escenario actual en Railway:** `OMNIX_SIGNING_SECRET_KEY_B64` y `OMNIX_SIGNING_PUBLIC_KEY_B64` NO están configuradas en Railway.

**Comportamiento al arranque:**
```python
# decision_receipt.py
if not (_ENV_PRIV_B64 and _ENV_PUB_B64):
    logger.critical(
        "⚠️  OMNIX_SIGNING_SECRET_KEY_B64 / OMNIX_SIGNING_PUBLIC_KEY_B64 are NOT set. "
        "Ephemeral signing keys will be generated — existing receipts will fail verification "
        "after any server restart."
    )
    _STABLE_SIGNING_KEYS = _active_provider.generate_keypair()  # ← nueva keypair en RAM
```

**Consecuencias:**
1. **Cada restart de Railway genera una nueva keypair.**
2. **Todos los receipts firmados con la keypair anterior son PERMANENTEMENTE UNVERIFICABLES.**
3. Railway hace restart automático en cada deploy, en cada crash, y periódicamente.
4. El verifier (`omnix_verify.py`) falla para cualquier receipt de un deployment anterior.

**Alcance del daño:** Todos los receipts firmados desde el inicio del deployment en Railway son potencialmente inválidos hoy. Si Railway ha reiniciado el servidor alguna vez desde que empezó a producir receipts, esos receipts ya no pueden ser verificados criptográficamente.

**Acción requerida:** Agregar `OMNIX_SIGNING_SECRET_KEY_B64` y `OMNIX_SIGNING_PUBLIC_KEY_B64` a Railway como variables de entorno protegidas. Usar `omnix_core/tools/key_gen.py` para generar el par de claves una vez y almacenarlas de forma permanente.

### 5.2 — Rotación de Claves: Sin Historial, Sin API

**Mecanismo actual:** La rotación de claves PQC solo es posible cambiando las env vars en Railway y redesplegando. No existe un endpoint API de rotación, ni un registro de claves anteriores.

**Post-rotación de claves:**
- El verifier extrae `public_key` del receipt mismo y verifica la firma contra ella.
- Esto significa que los receipts firmados con la clave anterior SÍ son verificables — el verifier no usa una clave de servidor centralizada, sino la clave embebida en cada receipt.
- **Esto es correcto por diseño.** La autenticidad del receipt está en la firma, no en comparar contra un registro de claves de servidor.

**Gap residual:** No hay un "OMNIX Key Registry" que permita verificar que la clave embebida en un receipt es genuinamente una clave OMNIX (ver FMR-003).

### 5.3 — Trust Gap: Verifier No Valida Autenticidad de la Clave (FMR-003)

**Comportamiento del verifier:**
```python
pub_key_b64 = receipt.get('public_key')  # ← clave del receipt mismo
public_key = base64.b64decode(pub_key_b64)
message = receipt['content_hash'].encode('utf-8')
dilithium3.verify(signature, message, public_key)  # ← verifica consistencia interna
```

**El verifier verifica:** "¿Esta firma fue creada con la clave privada correspondiente a esta clave pública?"

**El verifier NO verifica:** "¿Esta clave pública es la clave oficial de OMNIX QUANTUM?"

**Ataque posible:**
```python
# Atacante con pqc library:
fake_priv, fake_pub = dilithium3.keypair()
fake_receipt = {
    'receipt_id': 'OMNIX-TRD-FAKED001',
    'content_hash': hashlib.sha256(b'fake payload').hexdigest(),
    'signature': dilithium3.sign(hash_bytes, fake_priv).hex(),
    'public_key': base64.b64encode(fake_pub).decode(),
    'signature_algorithm': 'Dilithium3',
    # ... otros campos ...
}
# → verify_receipt(fake_receipt) → signature_valid: True, overall_valid: True
```

**Severidad:** ALTA en términos de confianza criptográfica. En la práctica, el verifier está implementado en `omnix_core/evidence/verification_server.py` (no expuesto públicamente) y en `omnix_web/public/omnix_verify.py`. El ataque requiere que el atacante pueda presentar un receipt fraudulento al verifier — lo que implica acceso al canal de distribución de receipts.

**Mitigación recomendada:**
1. Publicar el fingerprint (SHA-256 de la clave pública OMNIX) en el sitio web y en los ADRs.
2. Añadir verificación en el verifier: si `OMNIX_SIGNING_PUBLIC_KEY_B64` está configurada, verificar que la clave del receipt coincide con ella.
3. Implementar un endpoint `GET /api/trust/public-key` que devuelva la clave pública actual firmada por un certificado X.509.

### 5.4 — Downgrade Attack: PQC → SHA-256 Only

**Mecanismo de downgrade:** Si la variable `OMNIX_SIGNING_SECRET_KEY_B64` está configurada pero con un valor inválido (base64 corrupto), la excepción es capturada silenciosamente y el sistema cae a modo SHA-256:

```python
try:
    _priv_bytes = base64.b64decode(_ENV_PRIV_B64)  # ← si falla...
    _pub_bytes  = base64.b64decode(_ENV_PUB_B64)
    _STABLE_SIGNING_KEYS = (...)
except Exception as _e:
    logger.error(f"Failed to load persistent signing keys from env: {_e} — falling back to ephemeral.")
    _STABLE_SIGNING_KEYS = _active_provider.generate_keypair()  # ← ephemeral keys
```

**Vector de ataque:** Un insider con acceso a Railway env vars podría corromper deliberadamente `OMNIX_SIGNING_SECRET_KEY_B64` con un valor inválido. El sistema arranca con claves efímeras, los receipts "se firman" pero son unverificables después del próximo restart. El degradamiento es silencioso para observadores externos (los receipts tienen `signature_algorithm: Dilithium3` aunque la clave efímera sea diferente).

**Mitigación:** Si la clave de env var no parsea, el sistema debería `sys.exit(1)` — no continuar con claves efímeras. Un deployment con claves corruptas es un deployment con gobernanza no auditable.

### 5.5 — Entorno con Firmas Mixtas (Mixed-Signature Environment)

**Escenario:** Railway fue configurado sin claves PQC (efímeras), luego se agregan las claves correctas, luego un rollback del deployment regresa a las efímeras.

**Resultado:** La tabla `decision_receipts` contiene una mezcla de:
- Receipts con firma Dilithium-3 (clave estable A).
- Receipts con firma Dilithium-3 (clave efímera B — inválida tras restart).
- Receipts con firma Dilithium-3 (clave estable A, post-fix).

**El `signature_algorithm` es el mismo en todos** — `Dilithium3`. No hay campo que distinga si la firma es con clave estable o efímera.

**Mitigación:** Añadir campo `key_fingerprint: str` al receipt — los primeros 16 bytes del SHA-256 de la clave pública. Permite a auditores identificar qué receipts fueron firmados con qué clave. `omnix_verify.py` puede comparar ese fingerprint contra el registro conocido de claves OMNIX.

---

## Sección 6 — Clasificación de Fidelidad de Replay

Esta sección responde definitivamente a la pregunta: ¿qué tipo de garantías provee cada modo de replay?

### 6.1 — GovernanceReplayEngine (ADR-145)

**Clasificación:** SIMULACIÓN FORENSE HISTÓRICA — NO reproducción de pipeline.

| Dimensión | Descripción |
|-----------|-------------|
| **Fidelidad de señales** | Alta — señales normalizadas derivadas de datos de mercado reales en los timestamps históricos |
| **Fidelidad de veredictos** | No-computacional — verdicts son `expected_verdict` hardcodeados en `crisis_scenarios.py`, derivados de documentos forenses OMNIX (no de la ejecución de la pipeline viva) |
| **Fidelidad de checkpoints** | Baja — no se invocan `AMLGate.evaluate()`, `FraudGate.evaluate()`, etc. Los checkpoints son strings descriptivos |
| **Fidelidad de hashes** | Alta — SHA-256 canónico del payload completo, determinístico entre runs |
| **Fidelidad de firmas** | Alta cuando PQC disponible — Dilithium-3 sobre el hash canónico |
| **Fidelidad de formato** | Alta — estructura de receipt idéntica en campos a producción |
| **Fidelidad de tiempo** | Media — timestamps son strings UTC de los eventos históricos, no el momento de ejecución del replay |

**Lo que el replay GARANTIZA:**
- Un receipt PQC-firmado con un hash que sella: señales históricas + veredicto histórico + timestamp histórico.
- Determinismo: los mismos inputs siempre producen los mismos outputs.
- Verificabilidad independiente del hash.

**Lo que el replay NO GARANTIZA:**
- Que el veredicto fue computado por la pipeline viva con esas señales.
- Que los checkpoints individuales habrían fallado en el mismo orden con la lógica actual.
- Que los thresholds AVM de 2022 son los mismos que los de 2026.

### 6.2 — Wording del UI Post-Corrección

**Antes (incorrecto):**
> "The same governance engine running in production today — applied retroactively to events that wiped hundreds of billions."

**Después (corregido):**
> "The OMNIX governance framework — applied retroactively to the exact signal conditions that existed when each crisis unfolded. Every historically-verified decision is sealed in a cryptographic receipt you can verify independently."

**Footer corregido:**
> "Receipts generated by GovernanceReplayEngine v1.0.0 — a forensic component of the OMNIX production codebase. Verdicts reflect historically-verified governance decisions sourced from OMNIX forensic documents."

### 6.3 — Wording de crisis_scenarios.py (Tensión Residual)

El docstring de `crisis_scenarios.py` dice:
> "the exact inputs the OMNIX governance pipeline would have evaluated in real time"

Esta afirmación es defensible — las señales son approximaciones de los datos reales del mercado en ese momento. No se recomienda cambiarla porque la palabra clave es "would have evaluated" (habría evaluado), no "evaluated" (evaluó).

---

## Sección 7 — Observabilidad bajo Falla

### 7.1 — Fallo de Logging

**Qué ocurre si el logging falla:** Python's logging module solo lanza excepciones si el handler específico falla y `raiseExceptions=True` (default en desarrollo, False en producción con `logging.raiseExceptions=False`). En producción, un handler que falla simplemente descarta el log — silenciosamente.

**Evaluación:** El sistema usa `logging.getLogger()` estándar. Si el destino de logs (stdout/Railway log collector) falla, los eventos de gobernanza no se registran en logs pero sí en DB (receipts). La DB es el audit trail primario, no los logs.

**Riesgo residual:** Si tanto DB como logging fallan simultáneamente (escenario de colapso total), los eventos de gobernanza son invisibles. Este es el escenario de colapso extremo — probabilidad muy baja, impacto máximo.

### 7.2 — Redis No Disponible

**Evaluación:**
- Anti-replay: cae a in-memory (`best_effort`) — cross-dyno replay posible (FMR-004).
- AVM alerts: no usa Redis directamente — usa Telegram HTTP API.
- Ningún componente de gobernanza tiene Redis como dependencia crítica excepto el anti-replay.

**Conclusión:** Redis es un componente de seguridad (anti-replay) pero no de correctness. El sistema sigue tomando decisiones correctamente sin Redis. Solo el anti-replay se degrada.

### 7.3 — Telegram No Disponible

**Evaluación:** Las alertas de Telegram se envían en hilos daemon (`daemon=True`). Si Telegram API está caída:
- El hilo falla silenciosamente (es daemon — no bloquea el proceso principal).
- Las decisiones de gobernanza NO se bloquean.
- El rate limiter de alertas (`_rate_lock`) sigue funcionando.
- No hay fallback de notificación (email, SMS, webhook alternativo).

**Riesgo:** Un operador Tier 1 podría no enterarse de un approval gate hold hasta que revise manualmente el dashboard. Si la indisponibilidad de Telegram dura horas, los holds del AMG se acumulan sin atención.

### 7.4 — Clock Skew entre Servicios

**Uso de tiempo en el sistema:**
- `datetime.now(timezone.utc)`: timestamps de receipts y scopes — depende del OS clock de Railway.
- `time.monotonic()`: rate limiting de AVM alerts — proceso-local, no cross-process.
- `time.time()`: state_provenance_guard, context_admission_gate — depende de OS clock.

**Riesgo de clock skew:** Si Railway experimenta un skew de reloj significativo (> 30s), los timestamps de receipts pueden estar en el futuro o pasado. No hay validación de que los timestamps de receipts sean razonables (dentro de ±5min del tiempo de procesamiento, por ejemplo).

**Anti-replay impact:** El anti-replay usa TTL de Redis (30s mínimo). Clock skew en el servidor Redis vs el servidor Flask podría causar que receipts válidos sean rechazados prematuramente o aceptados demasiado tiempo después.

### 7.5 — Corrupción Parcial de DB

**Evaluación:** PostgreSQL es ACID — las escrituras parciales dentro de una transacción se revierten. El riesgo no es corrupción dentro de una transacción sino:
1. Corrupción de página en disco (hardware failure) → PostgreSQL detecta esto con checksums si están habilitados.
2. Corrupción de índice → las queries de hash lookup fallan silenciosamente con resultados incorrectos.

**Railway mitiga esto con:** Backups automáticos diarios, réplicas de lectura, y checksums de página habilitados en PostgreSQL 14+.

---

## Sección 8 — Auditoría de Autoridad de Emergencia

### 8.1 — Quién Puede Congelar la Gobernanza

**Respuesta directa:** Nadie, directamente. No existe un endpoint de freeze.

**Mecanismos implícitos de halt:**
1. `AVM_FAIL_CLOSED=true`: Si DB no está disponible, AVM bloquea todas las decisiones (fail-closed). No es un freeze — es una política de seguridad.
2. `AVM_AUTO_APPROVE=true`: Inverso — aprueba todo. Documentado como prohibido en producción.
3. Detener el servidor Flask: El deployment completo deja de responder. Esto es un freeze de facto pero requiere acceso a Railway.

**Conclusión:** No hay un botón de freeze en la API de gobernanza. Este es un diseño correcto para un sistema fail-closed — un freeze accidental podría ser peor que un fallo graceful.

### 8.2 — Quién Puede Hacer Override de un BLOCK

**Mecanismo existente:** `HumanOversightEngine.create_override()` en `omnix_core/governance/human_oversight.py`. Este módulo permite que un operador Tier 1 registre una decisión de override humano, firmada con PQC.

**Controles:**
- El override es un REGISTRO — no revierte el receipt original bloqueado.
- La API requiere `require_admin=True`.
- El override tiene su propio receipt PQC-firmado.
- El override queda en `decision_receipts` con `human_override=true` flag.

**Gap:** No se encontró un endpoint API público que invoque `create_override()` directamente. El módulo existe como librería — necesita ser conectado a un endpoint API para ser usable por operadores.

### 8.3 — Quién Puede Deshabilitar el AMG

**Mecanismos de deshabilitación:**
1. `AVM_AUTO_APPROVE=true` (env var) → bypassa el approval gate completo. Loguea ERROR.
2. `AVM_MAX_CUMULATIVE_DRIFT_PCT=99` (env var) → cumulative guard casi eliminado.
3. `AVM_APPROVAL_THRESHOLD_PCT=99` (env var) → approval gate casi eliminado.

**Quién tiene acceso:** Cualquier actor con acceso a Railway env vars (Tier 0 o Tier 1 con Railway admin). Railway loguea todos los cambios de env vars — no es operable en silencio completo.

### 8.4 — ¿Las Acciones de Emergencia Son Auditables?

**Override humano:** Sí — crea un receipt PQC-firmado en DB.
**Cambio de env vars (AMG):** Parcialmente — Railway logs muestran el cambio pero el log de OMNIX solo muestra el efecto (WARNING/ERROR en cada invocación).
**Rotación de claves:** No — no hay registro en OMNIX de cuándo o por qué se rotaron las claves.
**Revocación de scope:** Sí — registro en `governance_scope_authorizations` con timestamp.

---

## Sección 9 — Integridad del Deployment en Producción

### 9.1 — Variables de Entorno: ¿Qué Pasa si Faltan?

| Variable | Falta | Efecto |
|----------|-------|--------|
| `DATABASE_URL` | Sin DB | Endpoints retornan 503 (no hay DB para conectar) |
| `REDIS_URL` | Sin Redis | Anti-replay cae a in-memory (`best_effort`) |
| `OMNIX_SIGNING_SECRET_KEY_B64` | Sin clave | **Ephemeral keys generadas — receipts unverificables tras restart** |
| `GEMINI_API_KEY` | Sin Gemini | AI features degradan a fallbacks (OpenAI → Anthropic → error) |
| `TELEGRAM_BOT_TOKEN` | Sin bot | Telegram alerts silenciosas — no bloquea nada |
| `TELEGRAM_ADMIN_USER_ID` | Sin admin | Admin commands deshabilitados en bot |
| `SESSION_SECRET` | Sin sesión | Flask Dashboard falla a iniciar |
| `AVM_FAIL_CLOSED=true` | No establecido | Stale snapshots producen warnings, no blocks |

**Evaluación:** El servidor Flask inicia sin validar que las variables críticas estén presentes. Esto permite deployments en modo "degradado oculto" — funcionando superficialmente pero sin garantías de gobernanza completas.

**Mitigación recomendada:** Script de startup validation (`check_env.py`) que valide todas las variables críticas antes de iniciar el servidor:
```python
REQUIRED_VARS = ['DATABASE_URL', 'OMNIX_SIGNING_SECRET_KEY_B64', 'OMNIX_SIGNING_PUBLIC_KEY_B64']
for var in REQUIRED_VARS:
    if not os.environ.get(var):
        print(f"CRITICAL: {var} not set — aborting startup")
        sys.exit(1)
```

### 9.2 — ¿Puede Railway Iniciar en Modo Demo/Test?

**Riesgos identificados:**
- `TESTING=true` en Railway: Desactiva AVM alerts y el SAE background thread. Las decisiones se toman pero sin notificaciones de gobernanza y sin el snapshot daemon.
- `AVM_AUTO_APPROVE=true` en Railway: Bypassa todo el approval gate del AMG.
- `AVM_MAX_CUMULATIVE_DRIFT_PCT=99` en Railway: Elimina efectivamente el cumulative guard.
- `OMNIX_ANTI_REPLAY_MODE=best_effort` en Railway: Anti-replay no es fail-closed.

**Estado actual:** `TESTING=true` NO está en Railway. `AVM_AUTO_APPROVE` NO está en Railway. Pero no hay verificación técnica de que estos valores no se establezcan accidentalmente.

### 9.3 — Migrations y Schema: ¿Pueden Saltarse?

**Evaluación:** OMNIX usa `CREATE TABLE IF NOT EXISTS` idempotente en cada startup — no hay un sistema de migraciones explícito. Este diseño garantiza que el schema nunca se salta, pero también significa que los cambios de schema destructivos (DROP COLUMN, ALTER TYPE) nunca se ejecutan automáticamente.

**Implicación:** El schema solo puede crecer (agregar tablas/columnas), nunca encogerse, sin intervención manual. Este es un tradeoff seguro para producción pero introduce deuda de schema acumulada.

---

## Sección 10 — Tabla de Severidad y Recomendaciones

### Crítico — Acción Inmediata Requerida

| ID | Acción | Dónde |
|----|--------|-------|
| FMR-001 | Agregar `OMNIX_SIGNING_SECRET_KEY_B64` y `OMNIX_SIGNING_PUBLIC_KEY_B64` a Railway | Railway env vars |
| FMR-004 | Establecer `OMNIX_ANTI_REPLAY_MODE=strict` en Railway | Railway env vars |

### Alto — Acción en Esta Semana

| ID | Acción | Dónde |
|----|--------|-------|
| FMR-002 | Implementar tabla `pending_receipts` como fallback de store_receipt | `gov_blueprint.py` + DB |
| FMR-003 | Publicar fingerprint de clave pública oficial; añadir verificación en verifier | `verification_server.py` + docs |
| 5.4 | Si claves PQC no parsean → `sys.exit(1)` (no claves efímeras) | `decision_receipt.py` |
| FMR-008 | Script `check_env.py` que valide vars críticas antes de iniciar servidor | startup |

### Medio — Acción en Este Mes

| ID | Acción | Dónde |
|----|--------|-------|
| FMR-006 | Alertar cuando cumulative drift supera 15% (no solo 30%) | `auto_modification_guard.py` |
| FMR-007 | Documentar en Railway que TESTING/AUTO_APPROVE son prohibidos en prod | Railway notes |
| 5.5 | Añadir `key_fingerprint` field a receipts para distinguir clave estable vs efímera | `decision_receipt.py` |
| 1.3 | Añadir `scope_status_explanation` en API cuando `scope_reapproval_pending=true` | `gov_blueprint.py` |
| 3.2 | Añadir `genesis_generation: int` a calibration snapshots para trazabilidad | `avm_db_bridge.py` |

### Bajo — Backlog Técnico

| ID | Acción |
|----|--------|
| RISK-002 | Circuit breaker para reapproval infinito (de HGA-2026-Q2-002) |
| RISK-008 | UNIQUE INDEX WHERE status='ACTIVE' en scope_authorizations |
| 3.4 | Contador visible de reapproval cycles por scope |
| 4.3 | Habilitar `pgaudit` en PostgreSQL Railway para audit log a nivel DB |
| 7.4 | Validar que receipt timestamp está dentro de ±5min del tiempo de procesamiento |

---

## Sección 11 — Análisis de Invariantes Institucionales

Los siguientes invariantes han sido verificados bajo condiciones hostiles simuladas y se mantienen:

| Invariante | Condición Verificada | Estado |
|------------|---------------------|--------|
| Fail-closed en colapso multi-capa | DB + Redis + Telegram simultáneamente caídos | ✅ Holds |
| No estado contradictorio en crash | Receipt falla → OMNIX-ERR, no estado corrupto | ✅ Holds |
| Replay hashes determinísticos | 5 ejecuciones independientes del replay engine | ✅ Holds |
| AMG cumulative cap | Simulación 180 días — bloquea en día 106 | ✅ Holds |
| PQC signing disponible en Replit | Claves estables configuradas | ✅ Holds |
| Rate limiting en endpoints críticos | flask_limiter activo en todos los endpoints | ✅ Holds |
| Audit trail completo en condiciones normales | Receipts en DB + logs | ✅ Holds |
| Audit trail en colapso DB | **FALLA — decisión sin receipt en DB** | ❌ FMR-002 |
| Receipts verificables tras restart | **FALLA en Railway — ephemeral keys** | ❌ FMR-001 |
| Anti-replay cross-dyno | **FALLA en best_effort — Redis down** | ❌ FMR-004 |

---

## Apéndice — Clasificación Definitiva de Modo de Replay

```
OMNIX GovernanceReplayEngine (ADR-145)
Mode: HISTORICAL FORENSIC SIMULATION

Garantías:
  ✅ Señales derivadas de datos públicos de mercado en timestamps históricos verificados
  ✅ SHA-256 canónico sobre payload completo — determinístico e inmutable
  ✅ Dilithium-3 PQC signature cuando las claves están disponibles
  ✅ Formato de receipt idéntico al de producción — mismas herramientas de verificación aplican
  ✅ replay_mode=true distingue receipts históricos de decisiones de producción vivas

NO garantiza:
  ❌ Que los verdicts fueron computados por la pipeline viva de 11 checkpoints
  ❌ Que los thresholds AVM del período histórico son los mismos que los actuales
  ❌ Que los checkpoints individuales habrían fallado en el mismo orden con la lógica moderna
  ❌ Que el replay es un "test" de la gobernanza actual contra datos históricos

Analogía institucional correcta:
  "El OMNIX governance framework, aplicado a señales históricas verificadas, muestra que
  estas crisis habrían sido detenidas bajo los criterios de gobernanza de OMNIX.
  Los receipts son sellados criptográficamente para verificabilidad independiente."

Analogía incorrecta (prohibida en materiales externos):
  "El mismo engine de producción aplicado retroactivamente" — implica ejecución live de
  la pipeline moderna sobre datos históricos, lo cual no es el caso.
```

---

*GOVERNANCE FAILURE MODE REPORT — HGA-2026-Q3-001*
*Generado: Mayo 2026 | OMNIX QUANTUM LTD | Harold Nunes, CAIO*
*Clasificación: Máxima Confidencialidad — uso interno y regulatorio exclusivamente*
*Próxima revisión recomendada: Tras implementación de FMR-001 y FMR-004 (urgente)*
