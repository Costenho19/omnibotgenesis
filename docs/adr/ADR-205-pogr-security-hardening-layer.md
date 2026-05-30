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

## Post-Remediation Audit — v3.0

La auditoría adversarial v3.0 (`scripts/pogr_adversarial_audit.py`) re-ejecutó los
15 ataques con las correcciones aplicadas. Resultados:

| Finding | Severidad antes | Severidad ahora | Veredicto |
|---|---|---|---|
| POGR-SEC-001 (A05) | 🔴 CRITICAL | ✅ MITIGATED | Firma forjada detectada — INVALID en los 3 canales |
| POGR-SEC-002 activo (A07) | 🔴 CRITICAL | ✅ MITIGATED | status canónico — alteración → hash mismatch |
| POGR-SEC-003 (A09) | 🟠 HIGH | ✅ MITIGATED | Kernel unificado — mismo veredicto en API y HTML |
| POGR-SEC-012 (A08) | 🟠 HIGH | ✅ MITIGATED | HTML verifica content_hash — mutación detectada |

**Hallazgos CRITICAL:** 0  
**Hallazgos HIGH:** 0  
**Divergencias críticas:** 0  

**Abiertos (no críticos):**

| Finding | Severidad | Descripción |
|---|---|---|
| POGR-SEC-002-ARCH (A11) | 🟡 MEDIUM | Stale pre-revocation export — arquitectónico · documentado con mandatory warning |
| POGR-SEC-004 (A13) | 🟡 MEDIUM | Sin UNIQUE INDEX en `session_id WHERE status='ACTIVE'` |
| POGR-SEC-011 (A06) | 🟡 MEDIUM | Sin argumento `--pogc-id` en offline verifier para binding ID↔contenido |

---

## Archivos Modificados

| Archivo | Cambio |
|---|---|
| `omnix_web/api/pogr_blueprint.py` | C1: CANONICAL_V2 · C2: `_verify_pqc_signature()` · C3: `_verify_certificate_core()` · C4: `revoke()` re-sign |
| `scripts/verify_pogc_offline.py` | v2.0: soporte canonical_version 1/2 · PQC real (`--platform-key`) · revocation warning |
| `scripts/pogr_adversarial_audit.py` | v3.0: 15 ataques con kernel unificado · severidades actualizadas |

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
