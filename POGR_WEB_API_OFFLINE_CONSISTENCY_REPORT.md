# POGR Web / API / Offline Consistency Report

**Sistema:** OMNIX Proof of Governance Registry (PoGR)  
**Fecha:** 2026-05-30 20:33:11 UTC  
**Metodología:** Cada ataque ejecutado independientemente sobre tres canales.
Un certificado es **SEGURO** solo si los tres canales producen el mismo veredicto.

---

## Vista Completa de Consistencia

| Ataque | Descripción | Offline | API JSON | HTML Web | Consistente |
|---|---|---|---|---|---|
| A01 | Issuer cambiado | INVALID | VALID | VALID | ✅ Sí |
| A02 | mandate_certification cambiado (UNCERTIFIED → MA… | INVALID | VALID | VALID | ✅ Sí |
| A03 | TTL expirado (expires_at en el pasado) | INVALID | INVALID | INVALID | ✅ Sí |
| A04 | content_hash field alterado en export JSON | INVALID | VALID | VALID | ❌ **No** |
| A05 | Firma alterada — prefijo ML-DSA-65: conservado (… | VALID | VALID | VALID | ✅ Sí |
| A06 | ID válido con contenido de otro PoGC (ID swap) | VALID | VALID | VALID | ✅ Sí |
| A07 | Export manipulado — status cambiado REVOKED→ACTI… | VALID | INVALID | INVALID | ❌ **No** |
| A08 | Offline=VALID, Web/API=INVALID — inconsistencia … | VALID | INVALID | VALID | ❌ **No** |
| A09 | API (JSON)=VALID, HTML=INVALID — firma STUB (POG… | VALID | VALID | INVALID | ❌ **No** |
| A10 | PoGC inexistente — ID not found | INVALID | INVALID | INVALID | ✅ Sí |
| A11 | PoGC revocado — stale export divergence (POGR-SE… | VALID | INVALID | INVALID | ❌ **No** |
| A12 | PoGC expirado (expires_at genuinamente en el pas… | INVALID | INVALID | INVALID | ✅ Sí |
| A13 | Replay — mismo session_id genera múltiples PoGCs… | VALID | VALID | VALID | ✅ Sí |
| A14 | Campos canónicos faltantes en JSON exportado | INVALID | VALID | VALID | ✅ Sí |
| A15 | JSON con campos extra maliciosos (injection atte… | VALID | VALID | VALID | ✅ Sí |

**Resumen:** 5 divergencia(s) detectada(s) de 15 ataques.

---

## Divergencias Confirmadas

### DIV-001 — A04: content_hash field alterado en export JSON

**Finding:** `POGR-SEC-010` | **Severidad:** MITIGATED (offline) / DESIGN-BOUNDARY (API)

| Canal | Veredicto | Lógica de verificación |
|---|---|---|
| Offline | `INVALID` | content_hash ✓ · status (archivo) · TTL · sig prefix · issuer |
| API JSON | `VALID` | content_hash ✓ · status (DB) · TTL · sig prefix |
| HTML Web | `VALID` | status (DB) · TTL · sig prefix · **❌ NO content_hash** |

**Causa raíz:**

Offline always detects (recomputes hash from canonical fields → doesn't match the corrupted stored hash). API/HTML read from DB — if DB was not touched, they see the original (valid) hash and compare against recomputed canonical → match → VALID. This is the correct threat model: offline verifies a file, API verifies from DB.

**Remediación:**

DB write access control is the real boundary. The offline verifier correctly detects hash tampering in files.

---

### DIV-002 — A07: Export manipulado — status cambiado REVOKED→ACTIVE (POGR-SEC-002)

**Finding:** `POGR-SEC-002` | **Severidad:** CRITICAL

| Canal | Veredicto | Lógica de verificación |
|---|---|---|
| Offline | `VALID` | content_hash ✓ · status (archivo) · TTL · sig prefix · issuer |
| API JSON | `INVALID` | content_hash ✓ · status (DB) · TTL · sig prefix |
| HTML Web | `INVALID` | status (DB) · TTL · sig prefix · **❌ NO content_hash** |

**Causa raíz:**

CRITICAL DIVERGENCE: 'status' is excluded from canonical_fields. An attacker can alter status in an exported JSON without breaking content_hash. The offline verifier checks the 'status' field from the file → sees ACTIVE → VALID. The API and HTML page read from DB → see REVOKED → INVALID. This creates a real, exploitable Web/API ≠ Offline divergence.

**Remediación:**

Option A (preferred): Add 'status' and 'revoked_at' to canonical_fields. Requires re-signing all existing certificates. Option B (interim): Add prominent warning in verify_pogc_offline.py: 'WARNING: Revocation status is NOT cryptographically bound. For revocation verification, query the live API.' Option B is a documentation fix, not a cryptographic fix.

---

### DIV-003 — A08: Offline=VALID, Web/API=INVALID — inconsistencia hash en DB

**Finding:** `POGR-SEC-012` | **Severidad:** HIGH

| Canal | Veredicto | Lógica de verificación |
|---|---|---|
| Offline | `VALID` | content_hash ✓ · status (archivo) · TTL · sig prefix · issuer |
| API JSON | `INVALID` | content_hash ✓ · status (DB) · TTL · sig prefix |
| HTML Web | `VALID` | status (DB) · TTL · sig prefix · **❌ NO content_hash** |

**Causa raíz:**

If the DB is mutated directly (bypassing the API), the stored content_hash becomes inconsistent with the canonical fields. The JSON API detects this (recomputes hash on every /verify call → mismatch → INVALID). The HTML page does NOT detect this (no hash recomputation in verify_page()). A stale offline export from before the mutation passes the offline check. This creates a three-way divergence: Offline=VALID · API JSON=INVALID · HTML Web=VALID.

**Remediación:**

1. Add content_hash recomputation to verify_page() — the HTML /pogr/verify endpoint must mirror the JSON API hash verification. 2. Apply DB-level immutability controls (no UPDATE on canonical columns). 3. Add DB trigger or application-level guard: UPDATE on canonical columns must also recompute and update content_hash.

---

### DIV-004 — A09: API (JSON)=VALID, HTML=INVALID — firma STUB (POGR-SEC-003)

**Finding:** `POGR-SEC-003` | **Severidad:** HIGH

| Canal | Veredicto | Lógica de verificación |
|---|---|---|
| Offline | `VALID` | content_hash ✓ · status (archivo) · TTL · sig prefix · issuer |
| API JSON | `VALID` | content_hash ✓ · status (DB) · TTL · sig prefix |
| HTML Web | `INVALID` | status (DB) · TTL · sig prefix · **❌ NO content_hash** |

**Causa raíz:**

DIVERGENCE CONFIRMED: JSON API and HTML page treat STUB signature differently. JSON API (verify()): STUB → pqc_signature check = None (warning) → valid=True. HTML page (verify_page()): checks sig.startswith('ML-DSA-65:') → False → valid=False → displays 'FIRMA EN PROCESO'. React SPA /proof-of-governance calls JSON API → says VALID. Visiting /pogr/verify/<id> directly → says INVALID. Same certificate, same DB, three access channels → three different verdicts.

**Remediación:**

Unify signature validation logic across JSON API and HTML page. Decision required: Option A — STUB is INVALID everywhere:   Set valid=False in JSON API when sig starts with STUB-. Option B — STUB is VALID in dev (acceptable):   HTML page must also treat STUB as a warning, not as INVALID. Either way: the two renderers must produce identical verdicts. Recommended: Option A (STUB = INVALID) for produ

---

### DIV-005 — A11: PoGC revocado — stale export divergence (POGR-SEC-002)

**Finding:** `POGR-SEC-002` | **Severidad:** CRITICAL

| Canal | Veredicto | Lógica de verificación |
|---|---|---|
| Offline | `VALID` | content_hash ✓ · status (archivo) · TTL · sig prefix · issuer |
| API JSON | `INVALID` | content_hash ✓ · status (DB) · TTL · sig prefix |
| HTML Web | `INVALID` | status (DB) · TTL · sig prefix · **❌ NO content_hash** |

**Causa raíz:**

Same root cause as A07: 'status' is not in canonical_fields. The offline verifier trusts the status field in the JSON file. If the file was downloaded before revocation, it still reads ACTIVE. Revocation is an out-of-band event relative to the offline export. The offline channel fundamentally cannot detect post-export revocation without querying the live API — this is an architectural limitation, not a bug in the verifier logic.

**Remediación:**

Same as A07: add 'status' to canonical_fields OR add a clear mandatory warning in verify_pogc_offline.py output: 'CAUTION: This verifier cannot detect revocation that occurred after export. To verify revocation status, call GET /v1/pogr/verify/<id>.' This warning must be present on EVERY execution, not just on detection.

---

## Análisis de Raíces Comunes

Las divergencias tienen tres raíces independientes:

### Raíz 1 — `status` excluido de `content_hash` (POGR-SEC-002)

Los 10 canonical_fields no incluyen `status` ni `revoked_at`. Un archivo exportado
antes de una revocación presenta el estado anterior (ACTIVE) con hash válido.
El offline verifier confía en el campo `status` del archivo — no puede consultar DB.

**Impacto:** Offline=VALID, API/HTML=INVALID para certificados revocados con export previo.
**Ataques afectados:** A07, A11

### Raíz 2 — HTML page omite `content_hash` (POGR-SEC-003 / POGR-SEC-012)

El endpoint `/pogr/verify/<id>` (Jinja2) usa:
```python
valid = status_db == 'ACTIVE' and not expired and sig.startswith('ML-DSA-65:')
```
El endpoint `/v1/pogr/verify/<id>` (JSON) recomputa el hash en cada llamada.
El componente React en `/proof-of-governance` llama al JSON API.

**Impacto:** HTML=VALID, API/React=INVALID si content_hash en DB es incorrecto.
**Ataques afectados:** A08

### Raíz 3 — STUB signature tratada distinto por canal (POGR-SEC-003)

```
JSON API:   STUB → Warning (None) → overall_valid = True  → VALID
HTML page:  STUB → sig.startswith('ML-DSA-65:') = False → valid = False → INVALID
Offline:    STUB → Warning (None) → overall_valid = True  → VALID
```

**Impacto:** API/Offline=VALID, HTML=INVALID para certs con firma STUB.
**Ataques afectados:** A09

---

## Nivel de Confianza por Canal

| Canal | Nivel de Confianza | Verificación PQC | Revocación en tiempo real | Content hash |
|---|---|---|---|---|
| Offline | ⚠ CONDICIONAL | ❌ Solo prefijo | ❌ No (depende del archivo) | ✅ Sí |
| API JSON | ✅ ALTO | ❌ Solo prefijo | ✅ Sí (DB) | ✅ Sí |
| HTML Web | 🔴 BAJO | ❌ Solo prefijo | ✅ Sí (DB) | ❌ **No** |

**Recomendación:** Para verificación en producción, usar el API JSON
(`GET /v1/pogr/verify/<id>`) como canal primario.
El canal HTML debe ser reforzado para igualar la lógica del JSON API.
El canal offline es adecuado para verificación de integridad de campos canónicos
pero **NO para verificación de revocación**.

---

*Generado por `scripts/pogr_adversarial_audit.py` · 2026-05-30 20:33:11 UTC · OMNIX QUANTUM LTD*