# ADR-205 — PoGR Security Hardening Layer

**Status:** ACCEPTED  
**Fecha:** 2026-05-30  
**Autor:** Harold Nunes — OMNIX QUANTUM LTD  
**Relates to:** ADR-186 (PoGR spec) · ADR-187 (endpoints) · ADR-189 (adversarial audit v1)

---

## Context

La auditoría adversarial v2.0 (`scripts/pogr_adversarial_audit.py`) ejecutó 15 ataques
sobre los tres canales de verificación del Proof of Governance Registry (PoGR):
Offline (`verify_pogc_offline.py`), JSON API (`GET /v1/pogr/verify/<id>`),
y HTML Web (`GET /pogr/verify/<id>`).

Los hallazgos identificados antes de este ADR:

| Finding | Severidad | Descripción |
|---|---|---|
| POGR-SEC-001 | 🔴 CRITICAL | `pqc_signature` nunca verificada criptográficamente — solo comprobación de prefijo |
| POGR-SEC-002 | 🔴 CRITICAL | `status` y `revoked_at` fuera de `canonical_fields` — un atacante puede alterar el estado en un export sin romper el `content_hash` |
| POGR-SEC-003 | 🟠 HIGH | JSON API y HTML page tratan la firma STUB de forma diferente → divergencia de veredicto |
| POGR-SEC-012 | 🟠 HIGH | La HTML page (`verify_page()`) no verifica `content_hash` → mutación de DB no detectada |

Hallazgos adicionales de menor severidad (no bloqueantes):
- POGR-SEC-004 (MEDIUM): sin UNIQUE index en `session_id`
- POGR-SEC-011 (MEDIUM): sin binding `pogc_id`↔contenido en offline verifier

---

## Decision

Implementar **PoGR Security Hardening Layer**: cuatro correcciones técnicas que eliminan
los tres hallazgos CRITICAL/HIGH y cierran la divergencia de verificación entre canales.

---

## Correcciones

### C1 — Canonical Version 2 (CANONICAL_V2)

**Problema:** `status` y `revoked_at` excluidos de `canonical_fields` → atacante puede
alterar `status` en un export sin romper `content_hash`.

**Solución:**

```python
_CANONICAL_V1 = [
    "pogc_id", "session_id", "ctchc_seal_hash",
    "issuer", "subject_org", "agent_id",
    "compliance_tier", "mandate_certification",
    "issued_at", "expires_at",
]
_CANONICAL_V2 = _CANONICAL_V1 + ["status", "revoked_at"]
CURRENT_CANONICAL_VERSION = 2
```

- Los nuevos PoGCs se emiten con `canonical_version=2`.
- `_canonical_fields(data, version)` selecciona V1 o V2 según `canonical_version` del cert.
- Los certs existentes (v1) mantienen backward compatibility con warning explícito.
- El `content_hash` y la firma PQC cubren ahora el estado de revocación completo.

**Nuevo campo en DDL:**

```sql
ALTER TABLE pogr_certificates ADD COLUMN IF NOT EXISTS
    canonical_version INTEGER NOT NULL DEFAULT 1;
```

### C2 — PQC Signature Verification Real (`_verify_pqc_signature`)

**Problema:** Todos los canales verificaban solo el prefijo `ML-DSA-65:` — sin verificación
criptográfica del payload. Una firma forjada (`ML-DSA-65:deadbeef...`) pasaba como válida.

**Solución:**

```python
def _verify_pqc_signature(sig_str: str, canonical: Dict[str, Any]) -> tuple:
    if not sig_str:
        return (False, "✗ PQC signature absent")
    if sig_str.startswith("STUB-"):
        return (None, "⚠ Development stub — not production ML-DSA-65")
    if not sig_str.startswith("ML-DSA-65:"):
        return (None, f"⚠ Unrecognised format")

    pk_b64 = os.environ.get("OMNIX_SIGNING_PUBLIC_KEY_B64")
    if not pk_b64:
        return (None, "⚠ Platform public key not configured — hash integrity still enforced")

    try:
        from oqs import Signature as OQSSignature
        pk_bytes  = base64.b64decode(pk_b64)
        payload   = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
        sig_bytes = bytes.fromhex(sig_str.removeprefix("ML-DSA-65:"))
        verifier  = OQSSignature("ML-DSA-65")
        verifier.verify(payload, sig_bytes, pk_bytes)
        return (True, "✓ ML-DSA-65 signature cryptographically verified (FIPS 204)")
    except Exception as exc:
        return (False, f"✗ ML-DSA-65 signature INVALID — {exc}")
```

- Usa `oqs.Signature("ML-DSA-65").verify()` — FIPS 204 / NIST 2024.
- Requiere `OMNIX_SIGNING_PUBLIC_KEY_B64` en el entorno (presente en Railway ✓).
- Si la clave no está configurada: warning no-bloqueante (development mode).
- Firma forjada con payload incorrecto → `verify()` raise → `(False, "✗ INVALID")` → veredicto INVALID.

### C3 — Unified Verification Kernel (`_verify_certificate_core`)

**Problema:** JSON API y HTML page tenían lógica de verificación divergente:
- API: verifica `content_hash` · STUB = warning (VALID)
- HTML: sin `content_hash` · STUB = INVALID · `valid = status_db == 'ACTIVE' and not expired and sig.startswith('ML-DSA-65:')`

Resultado: mismo certificado → dos veredictos distintos según el canal.

**Solución:** Kernel único compartido por ambos canales:

```python
def _verify_certificate_core(cert: Dict[str, Any]) -> tuple:
    """
    Single authoritative verification kernel — ADR-205.
    Returns: (valid: bool, notes: list[str], canon_version: int)
    """
    notes = []
    valid = True
    now   = datetime.now(timezone.utc)

    canon_version = int(cert.get("canonical_version") or 1)
    raw = {**cert, "issued_at": ..., "expires_at": ..., "revoked_at": ..., "status": ...}
    canonical = _canonical_fields(raw, version=canon_version)

    # [1] Content hash
    expected_hash = _content_hash(canonical)
    if expected_hash == cert.get("content_hash", ""):
        notes.append("✓ Content hash verified (SHA3-256)")
    else:
        notes.append("✗ Content hash mismatch")
        valid = False

    # [2] Status
    # [3] TTL
    # [4] PQC signature → _verify_pqc_signature()
    # [5] canonical_version warning (v1 legacy)

    return valid, notes, canon_version
```

- `verify()` (JSON API) → `valid, notes, _ = _verify_certificate_core(cert)` ✓
- `verify_page()` (HTML) → `valid, notes, canon_version = _verify_certificate_core(cert)` ✓
- Misma lógica → mismo veredicto → cero divergencia POGR-SEC-003 y POGR-SEC-012.

### C4 — Re-sign on Revocation (`revoke()` endpoint)

**Problema de diseño identificado durante ADR-205:** Al revocar un cert v2, el endpoint
hacía `UPDATE status='REVOKED', revoked_at=<ts>` sin actualizar `content_hash` ni
`pqc_signature`. Como `status` y `revoked_at` son ahora parte del canonical v2, el hash
almacenado quedaría inconsistente con los campos actuales, causando un falso "hash mismatch"
al verificar certs revocados.

**Solución:** Re-firma atómica bajo el nuevo estado REVOKED:

```python
# Dentro de revoke():
if canon_version >= 2:
    raw_revoked = {**dict(row),
                   "issued_at":  _dt_iso(row["issued_at"]),
                   "expires_at": _dt_iso(row["expires_at"]),
                   "revoked_at": now,
                   "status":     "REVOKED"}
    new_canonical = _canonical_fields(raw_revoked, version=2)
    new_hash = _content_hash(new_canonical)
    new_sig  = _sign_certificate(new_canonical)
    # UPDATE incluye content_hash y pqc_signature junto con status/revoked_at
```

**Beneficio:** Los exports de certs REVOCADOS tienen `content_hash` y `pqc_signature`
computados sobre el estado REVOKED. El offline verifier los verifica correctamente como
INVALID (status=REVOKED detectado via content_hash + status check).

---

## Invariantes PoGR

Los hallazgos CRITICAL/HIGH se relacionan con violaciones parciales de:

| Invariante | Enunciado | Estado post-ADR-205 |
|---|---|---|
| **PoGR-INV-003** | Content_hash + PQC signature garantizan integridad verificable offline | ✅ Enforced — hash cubre status v2 + PQC criptográfica activa |
| **PoGR-INV-002** | Append-only — revocación no elimina el cert; re-firma mantiene evidencia | ✅ Enforced — re-sign preserva trazabilidad |
| **PoGR-INV-006** | Solo el emisor original puede revocar; revocación incluye prueba PQC | ✅ Enforced — endpoint requiere `revocation_proof` |

---

## Impacto en Certs Existentes (Backward Compatibility)

Los certs emitidos antes de ADR-205 (`canonical_version=1`) mantienen backward compat:

- `_canonical_fields(data, version=1)` retorna los 10 campos originales.
- `_verify_certificate_core()` detecta `canonical_version=1` y añade warning explícito:
  ```
  ⚠ Canonical schema v1 — fields 'status' and 'revoked_at' are NOT
    cryptographically bound to this certificate's hash or signature.
    For real-time revocation status, verify at /v1/pogr/verify/<id>
  ```
- El veredicto sigue siendo VALID si el hash v1 es correcto (no se invalidan certs existentes).
- Los nuevos certs emitidos tras ADR-205 son siempre v2.

**Certs v1 en producción en el momento de este ADR:**
- `POGC-GENESIS-E071CC96` — primer PoGC (self-issued) — v1, backward compat ✓
- `POGC-EXT-A7F3C2B1D9E4F508` — VeriSigil AI external — v1, backward compat ✓

---

## Segunda Ola de Remediaciones — ADR-205 §6 (2026-05-31)

Auditoría adversarial V2 (`scripts/run_pogr_adversarial_audit_v2.py` — 19 ataques) identificó
4 bypasses adicionales no cubiertos por C1-C4. Implementadas remediaciones R-C1 a R-M3:

| ID | Severidad | Descripción | Remediación |
|---|---|---|---|
| X01 | 🔴 CRITICAL | `admin_resign` token derivable: SHA3("POGR-RESIGN:"+id) hardcoded en fuente | **R-C1**: HMAC-SHA3-256 con `POGR_ADMIN_RESIGN_SECRET` |
| X02 | 🟠 HIGH | PQC soft-fail: clave ausente → `valid=True` en API · `(False,...)` offline → divergencia | **R-H2**: `OMNIX_PQC_VERIFY_FAIL_CLOSED=true` en ambos canales |
| X03 | 🟠 HIGH | Offline sim-forgery: `AUDIT-PQC-SIM-V2:` aceptada por defecto → forgery path abierto | **R-H3**: `--allow-sim` opt-in requerido en `verify_pogc_offline.py v2.1` |
| X04 | 🟡 MEDIUM | `revocation_proof` no verificado — cualquier string de 1 char aceptado | **R-M1** Phase 1: validación estructural len≥64 + prefijo ML-DSA-65/JSON |

**Remediaciones adicionales aplicadas:**
- **R-H1** (MEDIUM): v1 cert hard-fail interim — `canonical_version=1` + `status≠ACTIVE` → check False
- **R-M2** (MEDIUM): POGC ID entropy aumentado a 128 bits (`secrets.token_hex(16)`)
- **R-M3** (LOW): Rate limiting Flask-Limiter: `60/min` en `/verify` · `20/min` en `/export`

### §6.1 — R-C1: HMAC-keyed admin_resign

```python
# Canonical env var for autoscale deployment (shared env var, no conflict with Replit secrets):
resign_secret = (
    os.environ.get("POGR_RESIGN_TOKEN")
    or os.environ.get("POGR_ADMIN_RESIGN_SECRET", "")
)
expected_token = hmac.new(
    resign_secret.encode(), f"POGR-RESIGN:{pogc_id}".encode(), hashlib.sha3_256
).hexdigest()
if not hmac.compare_digest(provided_token, expected_token):
    abort(403)
```

`admin_resign_page()` computa el HMAC server-side y lo inyecta en el template — el token
nunca es derivable desde fuente.

**Variable de entorno canónica:** `POGR_RESIGN_TOKEN` (shared env var — disponible en
Replit autoscale deploy). `POGR_ADMIN_RESIGN_SECRET` se mantiene como fallback para
entornos dev/legacy. Si ninguna está configurada, el endpoint retorna 503.

**Razón del dual-lookup (ADR-205 §6.1 addendum 2026-05-31):** Los Replit secrets no se
inyectan automáticamente en deployments autoscale; las shared env vars sí. Para evitar
503 en producción sin requerir acción manual de eliminación del secret existente, se usa
`POGR_RESIGN_TOKEN` como variable canónica con fallback a `POGR_ADMIN_RESIGN_SECRET`.

### §6.2 — R-M1 Phase 2 — IMPLEMENTADO (2026-05-31)

**Estado:** ✅ IMPLEMENTADO — X04 DETECTED

Verificación criptográfica completa de `revocation_proof` como firma ML-DSA-65.

**Cambios implementados:**

1. **DDL:** `ALTER TABLE pogr_certificates ADD COLUMN IF NOT EXISTS issuer_public_key TEXT;`
   — columna almacena la clave pública ML-DSA-65 del emisor en el momento de la emisión.

2. **`certify()`:** `issuer_public_key = os.environ.get("OMNIX_SIGNING_PUBLIC_KEY_B64", "")`
   persistido en INSERT junto al cert.

3. **`_verify_revocation_proof_phase2(proof, pogc_id, reason, cert_issued_at, issuer_public_key)`:**
   Función nueva que verifica el proof como ML-DSA-65 sobre el payload canónico:
   ```json
   {"action":"REVOKE","issued_at":<cert_issued_at>,"pogc_id":<id>,"revocation_reason":<reason>}
   ```
   Anti-replay: `issued_at` del cert liga el proof a una emisión específica.
   Fail-closed: `OMNIX_PQC_VERIFY_FAIL_CLOSED=true` → HTTP 403 si oqs no disponible.
   Legacy fallback: `OMNIX_REVOCATION_VERIFY_ALLOW_PHASE1_DEV=true` permite Phase 1
   para certs sin `issuer_public_key` (certs emitidos antes de esta corrección).

4. **`revoke()`:**
   - SELECT incluye `issuer_public_key`
   - Phase 2 call ejecutado antes del UPDATE
   - **TOCTOU guard:** `UPDATE ... WHERE pogc_id = %s AND status = 'ACTIVE' RETURNING pogc_id`
     previene race conditions en revocaciones concurrentes.

5. **`scripts/reissue_pogc_genesis_v2.py`:** Script premium para re-emitir
   POGC-GENESIS-E071CC96 como canonical_version=2. Genera execution trace JSON
   en `evidence_packages/` como evidencia auditable.

**Payload canónico del revocation_proof** (sort_keys=True, separators=(',',':')):
```python
json.dumps({
    "action":             "REVOKE",
    "issued_at":          cert_issued_at,   # ISO 8601 del cert
    "pogc_id":            pogc_id,
    "revocation_reason":  revocation_reason,
}, sort_keys=True, separators=(",", ":")).encode()
```

**Railway env vars necesarios:**
- `OMNIX_PQC_VERIFY_FAIL_CLOSED=true` — fail-closed para verificación PQC
- `OMNIX_REVOCATION_VERIFY_ALLOW_PHASE1_DEV=true` — solo para revocación de POGC-GENESIS-E071CC96 (legacy)

---

## Auditoría Adversarial V3 — Resultados Finales (2026-05-31)

Script: `scripts/run_pogr_adversarial_audit_v3.py` — 19 ataques  
Reporte completo: `docs/audits/pogr_v3/POGR_ADVERSARIAL_AUDIT_V3.md`

| ID | Ataque | Severidad | Veredicto |
|---|---|---|---|
| A01 | Modify `content_hash` after tamper | HIGH | ✅ DETECTED |
| A02 | Modify `issuer` field | HIGH | ✅ DETECTED |
| A03 | Modify `mandate_certification` | CRITICAL | ✅ DETECTED |
| A04 | Modify `compliance_tier` | CRITICAL | ✅ DETECTED |
| A05 | Modify `expires_at` to far future | CRITICAL | ✅ DETECTED |
| A06 | Replace `pqc_signature` with random hex | CRITICAL | ✅ DETECTED |
| A07 | Replay expired certificate | MEDIUM | ✅ DETECTED |
| A08 | Replay revoked v1/v2 cert (offline) | MEDIUM | ✅ **DETECTED** (A08 CLOSED) |
| A09 | Export JSON tamper + offline verify | CRITICAL | ✅ DETECTED |
| A10 | API vs Web inconsistency | LOW | ✅ DETECTED |
| A11 | API vs Offline inconsistency | LOW | ✅ DETECTED |
| A12 | Web vs Offline inconsistency | LOW | ✅ DETECTED |
| A13 | Missing mandatory fields | HIGH | ✅ DETECTED |
| A14 | Extra injected fields | LOW | ✅ DETECTED |
| A15 | POGC ID collision (entropy) | MEDIUM | ✅ DETECTED |
| X01 | admin_resign derivable token | CRITICAL | ✅ DETECTED (R-C1) |
| X02 | API PQC soft-fail (key absent) | HIGH | ✅ DETECTED (R-H2) |
| X03 | Offline sim-forgery default path | HIGH | ✅ DETECTED (R-H3) |
| X04 | revocation_proof ML-DSA-65 Phase 1+2 | MEDIUM | ✅ **DETECTED** (X04 CLOSED) |

**Resumen:**

| Métrica | Valor |
|---|---|
| Total ataques | 19 |
| Detected | **19** |
| Partial | **0** |
| Bypassed | **0** |
| CRITICAL bypassed | **0** |
| HIGH bypassed | **0** |
| Web = API = Offline | **✓ Consistentes** |

**Veredicto: PoGR PRODUCTION-READY — 19/19 DETECTED · 0 PARTIAL · 0 BYPASSED**

---

## Archivos Modificados

| Archivo | Cambio |
|---|---|
| `omnix_web/api/pogr_blueprint.py` | C1–C4 + R-C1 + R-H2 + R-H1 + R-M1 + R-M2 + R-M3 |
| `scripts/verify_pogc_offline.py` | v2.1.0: `--allow-sim` opt-in · R-H3 · R-H1 |
| `omnix_web/api/_rate_limits.py` | **Nuevo** — `pogr_limiter` instancia Flask-Limiter (R-M3) |
| `omnix_web/api/server.py` | `pogr_limiter.init_app(app)` — startup log confirmado |
| `scripts/run_pogr_adversarial_audit_v3.py` | **Nuevo** — 19 ataques post-remediation |

---

## Consequences

**Positivo:**
- 4 hallazgos CRITICAL/HIGH eliminados antes de la primera emisión pública de PoGCs.
- Los tres canales de verificación producen veredictos idénticos para el mismo input.
- La firma ML-DSA-65 ahora es criptográficamente verificable (no solo comprobación de prefijo).
- Los exports de certs revocados son verificables correctamente offline.
- Backward compatibility preservada para certs v1 existentes.

**Negativo / Trade-offs:**
- `OMNIX_SIGNING_PUBLIC_KEY_B64` requerido para verificación PQC completa (presente en Railway ✓).
- Certs v1 existentes no pueden ser "upgrades" a v2 sin re-emisión (por diseño — append-only).
- La revocación de certs v2 ahora requiere `_sign_certificate()` en el endpoint → latencia marginal.

---

## Related

- ADR-186 — PoGR spec · PoGR-INV-001–006
- ADR-187 — PoGR endpoints
- ADR-189 — Adversarial audit v1
- ADR-194 — MIVP · mandate_certification tier (canonical field v1)
- RFC-ATF-1 — ATF-INV-006 (offline-verifiable receipts)
