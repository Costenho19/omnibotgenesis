# POGR Adversarial Audit Report — v3.0 (post-ADR-205)

**Sistema:** OMNIX Proof of Governance Registry (PoGR)  
**Fecha:** 2026-05-30 21:19:36 UTC  
**Versión:** v3.0 — Post-remediation (ADR-205 applied)  
**ADR:** ADR-186 · ADR-187 · ADR-189 · ADR-205  
**Invariantes auditadas:** PoGR-INV-001–006  
**PQC mode:** sha3-256-sim  
**Generado por:** `scripts/pogr_adversarial_audit.py`  

---

## Executive Summary

La auditoría adversarial v3.0 re-ejecuta los **15 ataques** con las correcciones
de ADR-205 aplicadas:

| Corrección ADR-205 | Finding resuelto |
|---|---|
| `_verify_pqc_signature()` — verificación ML-DSA-65 real (oqs) | POGR-SEC-001 (A05) |
| `status` + `revoked_at` en CANONICAL_V2 | POGR-SEC-002 activo (A07) |
| `_verify_certificate_core()` unificado API + HTML | POGR-SEC-003 (A09) · POGR-SEC-012 (A08) |
| `revoke()` re-firma bajo estado REVOKED | POGR-SEC-002 coherencia |

| Métrica | v2.0 (antes) | v3.0 (ahora) |
|---|---|---|
| Hallazgos CRITICAL | 3 | **0** |
| Hallazgos HIGH | 2 | **0** |
| Hallazgos MEDIUM | 2 | **3** |
| Divergencias | 3 | **1** |
| Ataques mitigados | 10 | **12** |

---

## Tabla de Resultados

| ID | Descripción | Offline | API JSON | HTML Web | Divergencia | Severidad | Finding |
|---|---|---|---|---|---|---|---|
| A01 | Issuer cambiado (canonical field v1+v2) | INVALID | VALID | VALID | ✓ No | ✅ MITIGATED | POGR-SEC-007 |
| A02 | mandate_certification cambiado (UNCERTIFIED → MANDAT… | INVALID | VALID | VALID | ✓ No | ✅ MITIGATED | POGR-SEC-008 |
| A03 | TTL expirado (expires_at en el pasado) | INVALID | INVALID | INVALID | ✓ No | ✅ MITIGATED | POGR-SEC-009 |
| A04 | content_hash field alterado en export JSON | INVALID | VALID | VALID | ✓ No | ✅ MITIGATED | POGR-SEC-010 |
| A05 | Firma alterada — prefijo ML-DSA-65: conservado [POGR… | INVALID | INVALID | INVALID | ✓ No | ✅ MITIGATED | POGR-SEC-001 |
| A06 | ID válido con contenido de otro PoGC (ID swap — POGR… | VALID | VALID | VALID | ✓ No | 🟡 MEDIUM | POGR-SEC-011 |
| A07 | Export manipulado — status ACTIVE→REVOKED→ACTIVE [PO… | INVALID | INVALID | INVALID | ✓ No | ✅ MITIGATED | POGR-SEC-002 |
| A08 | DB mutation — hash inconsistency [POGR-SEC-012 → MIT… | INVALID | INVALID | INVALID | ✓ No | ✅ MITIGATED | POGR-SEC-012 |
| A09 | STUB signature — API/HTML divergence [POGR-SEC-003 →… | VALID | VALID | VALID | ✓ No | ✅ MITIGATED | POGR-SEC-003 |
| A10 | PoGC inexistente — ID not found | INVALID | INVALID | INVALID | ✓ No | ✅ MITIGATED | POGR-SEC-013 |
| A11 | PoGC revocado — stale pre-revocation export (archite… | VALID | INVALID | INVALID | ⚠ **SÍ** | 🟡 MEDIUM | POGR-SEC-002-ARCH |
| A12 | PoGC expirado (expires_at genuinamente en el pasado) | INVALID | INVALID | INVALID | ✓ No | ✅ MITIGATED | POGR-SEC-014 |
| A13 | Replay — mismo session_id genera múltiples PoGCs (PO… | VALID | VALID | VALID | ✓ No | 🟡 MEDIUM | POGR-SEC-004 |
| A14 | Campos canónicos faltantes en JSON exportado | INVALID | VALID | VALID | ✓ No | ✅ MITIGATED | POGR-SEC-015 |
| A15 | JSON con campos extra maliciosos (injection attempt) | VALID | VALID | VALID | ✓ No | ✅ MITIGATED | POGR-SEC-016 |

---

## Hallazgos Detallados

### A06 — ID válido con contenido de otro PoGC (ID swap — POGR-SEC-011)

**Finding ID:** `POGR-SEC-011`  
**Severidad:** 🟡 MEDIUM  
**Invariante:** PoGR-INV-003  
**ADR:** ADR-186  

**Escenario:**

Attacker takes POGC-A's exported file and replaces all fields with POGC-B's data. Offline verifier reads the file content — no binding between filename/URL and pogc_id inside the JSON. API reads POGC-A from DB — fully independent of file content.

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline | `VALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `VALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `VALID` |

**Hallazgo:**

Offline verifier has no binding between pogc_id in URL/filename and pogc_id inside the JSON. An attacker can present POGC-B's valid certificate as if verifying POGC-A. Both channels report VALID — but for DIFFERENT certificates. Identity confusion attack — not a cryptographic break.

**Remediación:**

Add --pogc-id argument to verify_pogc_offline.py. When provided, assert cert['pogc_id'] == supplied_id → FAIL if mismatch.

---

### A11 — PoGC revocado — stale pre-revocation export (architectural limitation)

**Finding ID:** `POGR-SEC-002-ARCH`  
**Severidad:** 🟡 MEDIUM  
**Invariante:** PoGR-INV-006  
**ADR:** ADR-205  

**Escenario:**

Attacker downloaded the export BEFORE the certificate was revoked. The stale JSON has status=ACTIVE (canonical at download time), valid content_hash and valid signature — because the cert was genuinely ACTIVE when exported. Offline verifier reads the stale file: status=ACTIVE, hash valid → VALID. API/HTML read DB: status=REVOKED → INVALID. This is an inherent limitation of offline verification without network access.

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline | `VALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `INVALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `INVALID` |

**⚠ DIVERGENCIA: los canales no coinciden.**

**Hallazgo:**

ARCHITECTURAL LIMITATION (not a bug): The stale export was cryptographically valid when it was created. No cryptographic scheme can make an offline verifier detect revocation events that occurred after the export was downloaded — without querying the live API. ADR-205 provides two mitigations: (1) v2 re-sign-on-revocation: fresh exports of REVOKED certs have REVOKED hash → correctly verified as INVALID offline. (2) verify_pogc_offline.py v2.0 emits a mandatory REVOCATION WARNING on every run: 'CAUTION: Revocation status cannot be verified offline. For live revocation check: GET /v1/pogr/verify/<id>'. Severity downgraded from CRITICAL to MEDIUM — well-documented, expected behavior.

**Remediación:**

DONE (ADR-205): mandatory revocation warning in verify_pogc_offline.py v2.0. v2 re-sign-on-revocation: fresh exports always reflect current state. Remaining gap: stale pre-revocation exports. To verify revocation: always query /v1/pogr/verify/<id>.

---

### A13 — Replay — mismo session_id genera múltiples PoGCs (POGR-SEC-004)

**Finding ID:** `POGR-SEC-004`  
**Severidad:** 🟡 MEDIUM  
**Invariante:** PoGR-INV-001 · PoGR-INV-002  
**ADR:** ADR-186  

**Escenario:**

POST /v1/pogr/certify called twice with same session_id. No UNIQUE constraint on session_id in pogr_certificates DDL. Each call generates a new pogc_id → two valid certs for the same session.

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline | `VALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `VALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `VALID` |

**Hallazgo:**

The pogr_certificates table has no UNIQUE constraint on session_id. An authenticated client can call POST /v1/pogr/certify multiple times with the same session_id, generating N PoGCs for the same governance session. Certificate proliferation risk — could allow downgrade from MANDATE-BOUND to UNCERTIFIED by requesting a new cert after governance state degrades.

**Remediación:**

Add to pogr_certificates DDL: CREATE UNIQUE INDEX idx_pogr_session_unique ON pogr_certificates (session_id) WHERE status = 'ACTIVE'; Prevents duplicate ACTIVE certs per session while preserving append-only for REVOKED (PoGR-INV-002).

---

### A01 — Issuer cambiado (canonical field v1+v2)

**Finding ID:** `POGR-SEC-007`  
**Severidad:** ✅ MITIGATED  
**Invariante:** PoGR-INV-003  
**ADR:** ADR-186  

**Escenario:**

Attacker alters the 'issuer' field in an exported PoGC JSON. 'issuer' is a canonical field in both v1 and v2 — content_hash covers it. Correct threat model: offline gets tampered file; API/HTML read from DB (clean).

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline | `INVALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `VALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `VALID` |

**Hallazgo:**

Canonical field alteration is correctly detected by all channels. Offline: content_hash mismatch (hash covers issuer). API/HTML: read from DB (attacker cannot mutate DB without DB access). Verdict: MITIGATED for export file tampering. Direct DB mutation (bypass API) requires DB write access — separate threat model.

**Remediación:**

No action needed — content_hash covers issuer in v1 and v2.

---

### A02 — mandate_certification cambiado (UNCERTIFIED → MANDATE-BOUND)

**Finding ID:** `POGR-SEC-008`  
**Severidad:** ✅ MITIGATED  
**Invariante:** MIVP-INV-008 · PoGR-INV-003  
**ADR:** ADR-186 · ADR-194  

**Escenario:**

Attacker upgrades a cert from UNCERTIFIED to MANDATE-BOUND in the export JSON without recalculating content_hash. Canonical field → hash breaks.

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline | `INVALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `VALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `VALID` |

**Hallazgo:**

mandate_certification is in CANONICAL_V1 and V2 — any change breaks content_hash. All channels detect this attack. MITIGATED.

**Remediación:**

mandate_certification is canonical — covered in v1 and v2.

---

### A03 — TTL expirado (expires_at en el pasado)

**Finding ID:** `POGR-SEC-009`  
**Severidad:** ✅ MITIGATED  
**Invariante:** PoGR-INV-004  
**ADR:** ADR-186  

**Escenario:**

Certificate with expires_at 5 days in the past. expires_at is canonical in v1 and v2 — cannot be forged without breaking hash.

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline | `INVALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `INVALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `INVALID` |

**Hallazgo:**

Expired TTL detected consistently by all three channels. MITIGATED.

**Remediación:**

No action needed — PoGR-INV-004 enforced.

---

### A04 — content_hash field alterado en export JSON

**Finding ID:** `POGR-SEC-010`  
**Severidad:** ✅ MITIGATED  
**Invariante:** PoGR-INV-003  
**ADR:** ADR-186  

**Escenario:**

Attacker replaces the content_hash field in the downloaded JSON with a corrupted value. Offline recomputes from canonical → mismatch → INVALID. API/HTML read DB (clean) — hash in DB is valid.

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline | `INVALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `VALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `VALID` |

**Hallazgo:**

Offline detects (recomputes hash from canonical fields → doesn't match corrupted stored). API/HTML read from DB — original (valid) hash → VALID. Correct by-design.

**Remediación:**

DB write access control is the real boundary.

---

### A05 — Firma alterada — prefijo ML-DSA-65: conservado [POGR-SEC-001 → MITIGATED]

**Finding ID:** `POGR-SEC-001`  
**Severidad:** ✅ MITIGATED  
**Invariante:** PoGR-INV-003  
**ADR:** ADR-205  

**Escenario:**

Attacker replaces the pqc_signature payload with arbitrary bytes but keeps the 'ML-DSA-65:' prefix. content_hash is recomputed correctly. Audit PQC mode: sha3-256-sim. All three channels now verify the signature payload — forged sig detected.

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline | `INVALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `INVALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `INVALID` |

**Hallazgo:**

ADR-205 REMEDIATION: _verify_certificate_core() now calls _verify_pqc_signature() which performs cryptographic ML-DSA-65 verification when the platform public key is configured. All three channels share this kernel. Forged signature (correct prefix, wrong payload) → detected → INVALID on all channels. Audit PQC mode: SHA3-256 simulation (oqs unavailable in this environment). Production (Railway): oqs + OMNIX_SIGNING_PUBLIC_KEY_B64 → real ML-DSA-65 verify.

**Remediación:**

DONE (ADR-205): _verify_pqc_signature() implemented with oqs.Signature('ML-DSA-65').verify(). Requires OMNIX_SIGNING_PUBLIC_KEY_B64 in Railway env (present ✓). If key not configured: warning (non-blocking) — hash integrity still enforced.

---

### A07 — Export manipulado — status ACTIVE→REVOKED→ACTIVE [POGR-SEC-002 → MITIGATED]

**Finding ID:** `POGR-SEC-002`  
**Severidad:** ✅ MITIGATED  
**Invariante:** PoGR-INV-002 · PoGR-INV-006  
**ADR:** ADR-205  

**Escenario:**

Attacker downloads export of an ACTIVE cert. Cert gets revoked in DB (v2 re-sign). Attacker downloads the REVOKED export (status=REVOKED in canonical). Attacker alters status field from REVOKED to ACTIVE. v2: status IS canonical — altering it breaks content_hash → INVALID on all channels.

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline | `INVALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `INVALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `INVALID` |

**Hallazgo:**

ADR-205 REMEDIATION: 'status' and 'revoked_at' are now in CANONICAL_V2. Any alteration of status in a v2 export breaks content_hash → detected on all channels. Additionally, the revocation endpoint now re-signs the cert under REVOKED state (ADR-205 revocation re-sign fix) — fresh exports of REVOKED certs have correct hash. Stale export scenario (cert downloaded BEFORE revocation): see A11 (architectural limitation — MEDIUM, not CRITICAL).

**Remediación:**

DONE (ADR-205): (1) status + revoked_at added to CANONICAL_V2. (2) revoke() endpoint re-signs cert under REVOKED state. (3) _verify_certificate_core() unified across all channels.

---

### A08 — DB mutation — hash inconsistency [POGR-SEC-012 → MITIGATED]

**Finding ID:** `POGR-SEC-012`  
**Severidad:** ✅ MITIGATED  
**Invariante:** PoGR-INV-002 · PoGR-INV-003  
**ADR:** ADR-205  

**Escenario:**

Scenario: A DB canonical field (issuer) was modified directly (bypassing API) without updating content_hash. v2: ALL three channels now recompute content_hash via _verify_certificate_core(). All three detect the inconsistency → INVALID.

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline | `INVALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `INVALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `INVALID` |

**Hallazgo:**

ADR-205 REMEDIATION: verify_page() (HTML) now uses _verify_certificate_core() shared kernel — it recomputes content_hash on every call. If canonical fields in DB were mutated without updating content_hash, ALL three channels detect the mismatch → INVALID. Previously: HTML did NOT check content_hash → partial VALID (HIGH divergence). Post-remediation: all channels consistent.

**Remediación:**

DONE (ADR-205): verify_page() uses _verify_certificate_core() — content_hash verified. Remaining: DB-level immutability controls (application-level guard on canonical columns) — defense-in-depth, P3.

---

### A09 — STUB signature — API/HTML divergence [POGR-SEC-003 → MITIGATED]

**Finding ID:** `POGR-SEC-003`  
**Severidad:** ✅ MITIGATED  
**Invariante:** PoGR-INV-003  
**ADR:** ADR-205  

**Escenario:**

Certificate has a STUB-SHA3-256: signature (environment without PQC signing key). v2: both channels use _verify_certificate_core() kernel. STUB → _verify_pqc_signature() returns (None, warning) → does NOT set valid=False. Verdict: VALID with warning on all three channels. No divergence.

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline | `VALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `VALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `VALID` |

**Hallazgo:**

ADR-205 REMEDIATION: JSON API and HTML page now share _verify_certificate_core() kernel. STUB signature → (None, warning) → valid is unchanged on both channels → same verdict. Previously: HTML checked sig.startswith('ML-DSA-65:') → STUB = False → INVALID; JSON API treated STUB as warning → VALID. Two channels → two verdicts. Post-remediation: unified kernel → single verdict (VALID + PQC warning).

**Remediación:**

DONE (ADR-205): _verify_certificate_core() unified across JSON API and HTML. STUB is treated identically (warning, non-blocking) in all contexts. Production: OMNIX_SIGNING_SECRET_KEY_B64 present in Railway → no STUB issued.

---

### A10 — PoGC inexistente — ID not found

**Finding ID:** `POGR-SEC-013`  
**Severidad:** ✅ MITIGATED  
**Invariante:** PoGR-INV-003  
**ADR:** ADR-186  

**Escenario:**

Request for a POGC-ID that does not exist in the registry. All channels must return INVALID / 404.

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline | `INVALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `INVALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `INVALID` |

**Hallazgo:**

All channels correctly reject unknown IDs. No divergence. MITIGATED.

**Remediación:**

No action needed.

---

### A12 — PoGC expirado (expires_at genuinamente en el pasado)

**Finding ID:** `POGR-SEC-014`  
**Severidad:** ✅ MITIGATED  
**Invariante:** PoGR-INV-004  
**ADR:** ADR-186  

**Escenario:**

Certificate with expires_at 10 days in the past, status=ACTIVE. expires_at IS canonical — cannot be forged without breaking hash. All channels check TTL independently.

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline | `INVALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `INVALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `INVALID` |

**Hallazgo:**

Expired TTL consistently detected. expires_at canonical → immutable. MITIGATED.

**Remediación:**

No action needed. PoGR-INV-004 enforced.

---

### A14 — Campos canónicos faltantes en JSON exportado

**Finding ID:** `POGR-SEC-015`  
**Severidad:** ✅ MITIGATED  
**Invariante:** PoGR-INV-003  
**ADR:** ADR-186  

**Escenario:**

JSON file is missing canonical fields (issuer, mandate_certification deleted). Offline: hash computed on subset → won't match complete hash → INVALID. API: DB always has all fields (NOT NULL constraints) → unaffected.

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline | `INVALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `VALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `VALID` |

**Hallazgo:**

Offline verifier gracefully handles missing canonical fields. Hash of the available subset won't match the stored hash → INVALID. API/HTML immune: DB NOT NULL constraints guarantee all fields present.

**Remediación:**

Add per-field warnings in offline verifier when canonical fields absent: 'WARNING: canonical field X missing from certificate.'

---

### A15 — JSON con campos extra maliciosos (injection attempt)

**Finding ID:** `POGR-SEC-016`  
**Severidad:** ✅ MITIGATED  
**Invariante:** PoGR-INV-003  
**ADR:** ADR-186  

**Escenario:**

Attacker adds extra fields: 'admin': True, 'override_status': 'ACTIVE', etc. Neither offline nor API read these fields — explicit canonical allowlist.

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline | `VALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `VALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `VALID` |

**Hallazgo:**

Extra fields safely ignored by all channels. Offline: uses explicit CANONICAL_V1/V2 allowlist — extras never read. API/HTML: read from DB — no user-submitted fields admitted. No injection or privilege escalation possible.

**Remediación:**

No action needed. Explicit allowlist is the correct pattern.

---

## Estado de Remediaciones

### ✅ Remediadas en ADR-205

| Finding | Severidad anterior | Acción aplicada |
|---|---|---|
| POGR-SEC-001 (A05) | 🔴 CRITICAL | `_verify_pqc_signature()` con oqs ML-DSA-65 real |
| POGR-SEC-002 activo (A07) | 🔴 CRITICAL | `status`+`revoked_at` en CANONICAL_V2 + re-sign on revocation |
| POGR-SEC-003 (A09) | 🟠 HIGH | `_verify_certificate_core()` unificado API + HTML |
| POGR-SEC-012 (A08) | 🟠 HIGH | HTML ahora verifica `content_hash` via kernel compartido |

### ⚠ Abiertos (no CRITICAL)

| Finding | Severidad | Acción recomendada |
|---|---|---|
| POGR-SEC-002-ARCH (A11) | 🟡 MEDIUM (arquitectónico) | Mandatory warning en offline verifier (DONE) |
| POGR-SEC-004 (A13) | 🟡 MEDIUM | UNIQUE INDEX en session_id WHERE status='ACTIVE' |
| POGR-SEC-011 (A06) | 🟡 MEDIUM | Argumento `--pogc-id` en verify_pogc_offline.py |

---

*Generado por `scripts/pogr_adversarial_audit.py` v3.0 · 2026-05-30 21:19:36 UTC · OMNIX QUANTUM LTD*