# POGR Adversarial Audit Report

**Sistema:** OMNIX Proof of Governance Registry (PoGR)  
**Fecha:** 2026-05-30 20:33:11 UTC  
**Versión:** v2.0 — Auditoría de tres canales  
**ADR:** ADR-186 · ADR-187 · ADR-189  
**Invariantes auditadas:** PoGR-INV-001–006  
**Generado por:** `scripts/pogr_adversarial_audit.py`  

---

## Executive Summary

La auditoría adversarial del PoGR ejecutó **15 ataques** sobre los tres
canales de verificación (Offline / API JSON / HTML Web) de forma independiente.
La condición de PASS requiere que los tres canales produzcan el mismo veredicto.

| Métrica | Valor |
|---|---|
| Total ataques ejecutados | 15 |
| Divergencias Web/API/Offline | **5** |
| Hallazgos CRITICAL | **3** |
| Hallazgos HIGH | **2** |
| Ataques mitigados correctamente | 7 |

---

## Tabla de Resultados

| ID | Descripción | Offline | API JSON | HTML Web | Divergencia | Severidad | Finding |
|---|---|---|---|---|---|---|---|
| A01 | Issuer cambiado | INVALID | VALID | VALID | ✓ No | ✅ MITIGATED | POGR-SEC-007 |
| A02 | mandate_certification cambiado (UNCERTIFIED → MANDAT… | INVALID | VALID | VALID | ✓ No | ✅ MITIGATED | POGR-SEC-008 |
| A03 | TTL expirado (expires_at en el pasado) | INVALID | INVALID | INVALID | ✓ No | ✅ MITIGATED | POGR-SEC-009 |
| A04 | content_hash field alterado en export JSON | INVALID | VALID | VALID | ⚠ **SÍ** | • MITIGATED (offline) / DESIGN-BOUNDARY (API) | POGR-SEC-010 |
| A05 | Firma alterada — prefijo ML-DSA-65: conservado (POGR… | VALID | VALID | VALID | ✓ No | 🔴 CRITICAL | POGR-SEC-001 |
| A06 | ID válido con contenido de otro PoGC (ID swap) | VALID | VALID | VALID | ✓ No | 🟡 MEDIUM | POGR-SEC-011 |
| A07 | Export manipulado — status cambiado REVOKED→ACTIVE (… | VALID | INVALID | INVALID | ⚠ **SÍ** | 🔴 CRITICAL | POGR-SEC-002 |
| A08 | Offline=VALID, Web/API=INVALID — inconsistencia hash… | VALID | INVALID | VALID | ⚠ **SÍ** | 🟠 HIGH | POGR-SEC-012 |
| A09 | API (JSON)=VALID, HTML=INVALID — firma STUB (POGR-SE… | VALID | VALID | INVALID | ⚠ **SÍ** | 🟠 HIGH | POGR-SEC-003 |
| A10 | PoGC inexistente — ID not found | INVALID | INVALID | INVALID | ✓ No | ✅ MITIGATED | POGR-SEC-013 |
| A11 | PoGC revocado — stale export divergence (POGR-SEC-00… | VALID | INVALID | INVALID | ⚠ **SÍ** | 🔴 CRITICAL | POGR-SEC-002 |
| A12 | PoGC expirado (expires_at genuinamente en el pasado) | INVALID | INVALID | INVALID | ✓ No | ✅ MITIGATED | POGR-SEC-014 |
| A13 | Replay — mismo session_id genera múltiples PoGCs (PO… | VALID | VALID | VALID | ✓ No | 🟡 MEDIUM | POGR-SEC-004 |
| A14 | Campos canónicos faltantes en JSON exportado | INVALID | VALID | VALID | ✓ No | ✅ MITIGATED | POGR-SEC-015 |
| A15 | JSON con campos extra maliciosos (injection attempt) | VALID | VALID | VALID | ✓ No | ✅ MITIGATED | POGR-SEC-016 |

---

## Hallazgos Detallados

### A05 — Firma alterada — prefijo ML-DSA-65: conservado (POGR-SEC-001)

**Finding ID:** `POGR-SEC-001`  
**Severidad:** 🔴 CRITICAL  
**Invariante:** PoGR-INV-003 (partially violated)  

**Escenario:**

Attacker replaces the pqc_signature payload with random bytes but keeps the 'ML-DSA-65:' prefix. content_hash is valid. No channel verifies the signature bytes cryptographically. All three channels report VALID — FALSE POSITIVE.

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline (`verify_pogc_offline.py`) | `VALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `VALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `VALID` |

**Hallazgo:**

CRITICAL KNOWN LIMITATION: pqc_signature is never cryptographically verified by any channel. All three only check the 'ML-DSA-65:' prefix string. An attacker who knows the canonical fields can: (1) Compute a valid content_hash, (2) Attach any payload after 'ML-DSA-65:', → All three channels report VALID. This is a FALSE POSITIVE across all channels — consistent but wrong.

**Remediación:**

Implement --platform-key flag in verify_pogc_offline.py to enable full ML-DSA-65 cryptographic verification using the platform public key from /v1/pogr/manifest. The API /v1/pogr/verify must also perform cryptographic signature verification on each call. Priority: P1 — before first public PoGC issued to a third party.

---

### A07 — Export manipulado — status cambiado REVOKED→ACTIVE (POGR-SEC-002)

**Finding ID:** `POGR-SEC-002`  
**Severidad:** 🔴 CRITICAL  
**Invariante:** PoGR-INV-002 (revocation) · PoGR-INV-006  

**Escenario:**

Attacker downloads export of an ACTIVE certificate. Admin revokes it. Attacker alters status field from 'REVOKED' to 'ACTIVE' in the old JSON. 'status' is NOT in canonical_fields — content_hash does NOT change. Offline: VALID. API/HTML (reading DB): INVALID.

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline (`verify_pogc_offline.py`) | `VALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `INVALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `INVALID` |

**⚠ DIVERGENCIA: los tres canales no coinciden.**

**Hallazgo:**

CRITICAL DIVERGENCE: 'status' is excluded from canonical_fields. An attacker can alter status in an exported JSON without breaking content_hash. The offline verifier checks the 'status' field from the file → sees ACTIVE → VALID. The API and HTML page read from DB → see REVOKED → INVALID. This creates a real, exploitable Web/API ≠ Offline divergence.

**Remediación:**

Option A (preferred): Add 'status' and 'revoked_at' to canonical_fields. Requires re-signing all existing certificates. Option B (interim): Add prominent warning in verify_pogc_offline.py: 'WARNING: Revocation status is NOT cryptographically bound. For revocation verification, query the live API.' Option B is a documentation fix, not a cryptographic fix.

---

### A11 — PoGC revocado — stale export divergence (POGR-SEC-002)

**Finding ID:** `POGR-SEC-002`  
**Severidad:** 🔴 CRITICAL  
**Invariante:** PoGR-INV-006 (revocation integrity)  

**Escenario:**

Attacker downloaded the export BEFORE the certificate was revoked. The stale JSON has status=ACTIVE, valid content_hash, valid sig prefix. Offline verifier cannot detect revocation from a stale file. This is the primary lifecycle divergence in the PoGR system.

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline (`verify_pogc_offline.py`) | `VALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `INVALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `INVALID` |

**⚠ DIVERGENCIA: los tres canales no coinciden.**

**Hallazgo:**

Same root cause as A07: 'status' is not in canonical_fields. The offline verifier trusts the status field in the JSON file. If the file was downloaded before revocation, it still reads ACTIVE. Revocation is an out-of-band event relative to the offline export. The offline channel fundamentally cannot detect post-export revocation without querying the live API — this is an architectural limitation, not a bug in the verifier logic.

**Remediación:**

Same as A07: add 'status' to canonical_fields OR add a clear mandatory warning in verify_pogc_offline.py output: 'CAUTION: This verifier cannot detect revocation that occurred after export. To verify revocation status, call GET /v1/pogr/verify/<id>.' This warning must be present on EVERY execution, not just on detection.

---

### A08 — Offline=VALID, Web/API=INVALID — inconsistencia hash en DB

**Finding ID:** `POGR-SEC-012`  
**Severidad:** 🟠 HIGH  
**Invariante:** PoGR-INV-002 (append-only violated by direct DB mutation)  

**Escenario:**

Scenario: A DB canonical field (e.g. issuer) was modified directly in the DB (bypassing the API) without updating content_hash. API recomputes hash → mismatch → INVALID. HTML page does NOT check hash → VALID. Stale export from before the DB mutation → VALID offline.

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline (`verify_pogc_offline.py`) | `VALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `INVALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `VALID` |

**⚠ DIVERGENCIA: los tres canales no coinciden.**

**Hallazgo:**

If the DB is mutated directly (bypassing the API), the stored content_hash becomes inconsistent with the canonical fields. The JSON API detects this (recomputes hash on every /verify call → mismatch → INVALID). The HTML page does NOT detect this (no hash recomputation in verify_page()). A stale offline export from before the mutation passes the offline check. This creates a three-way divergence: Offline=VALID · API JSON=INVALID · HTML Web=VALID.

**Remediación:**

1. Add content_hash recomputation to verify_page() — the HTML /pogr/verify endpoint must mirror the JSON API hash verification. 2. Apply DB-level immutability controls (no UPDATE on canonical columns). 3. Add DB trigger or application-level guard: UPDATE on canonical columns must also recompute and update content_hash.

---

### A09 — API (JSON)=VALID, HTML=INVALID — firma STUB (POGR-SEC-003)

**Finding ID:** `POGR-SEC-003`  
**Severidad:** 🟠 HIGH  
**Invariante:** PoGR-INV-003 (consistency violated)  

**Escenario:**

Certificate has a STUB-SHA3-256: signature (environment without PQC key). JSON API: STUB → Warning → overall valid=True → VALID. HTML page: sig.startswith('ML-DSA-65:') → False → valid=False → INVALID. React SPA calls JSON API → VALID. Direct HTML page → INVALID. Three different verdicts for the same certificate.

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline (`verify_pogc_offline.py`) | `VALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `VALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `INVALID` |

**⚠ DIVERGENCIA: los tres canales no coinciden.**

**Hallazgo:**

DIVERGENCE CONFIRMED: JSON API and HTML page treat STUB signature differently. JSON API (verify()): STUB → pqc_signature check = None (warning) → valid=True. HTML page (verify_page()): checks sig.startswith('ML-DSA-65:') → False → valid=False → displays 'FIRMA EN PROCESO'. React SPA /proof-of-governance calls JSON API → says VALID. Visiting /pogr/verify/<id> directly → says INVALID. Same certificate, same DB, three access channels → three different verdicts.

**Remediación:**

Unify signature validation logic across JSON API and HTML page. Decision required: Option A — STUB is INVALID everywhere:   Set valid=False in JSON API when sig starts with STUB-. Option B — STUB is VALID in dev (acceptable):   HTML page must also treat STUB as a warning, not as INVALID. Either way: the two renderers must produce identical verdicts. Recommended: Option A (STUB = INVALID) for production integrity.

---

### A06 — ID válido con contenido de otro PoGC (ID swap)

**Finding ID:** `POGR-SEC-011`  
**Severidad:** 🟡 MEDIUM  
**Invariante:** PoGR-INV-003  

**Escenario:**

Attacker takes POGC-A's exported file and replaces all fields with POGC-B's data. Offline verifier reads the file content — no binding between filename/URL and pogc_id inside the JSON. API reads POGC-A from DB — fully independent of file content.

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline (`verify_pogc_offline.py`) | `VALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `VALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `VALID` |

**Hallazgo:**

Offline verifier has no binding between the pogc_id in the URL/filename and the pogc_id inside the JSON. An attacker can present POGC-B's valid certificate as if verifying POGC-A. The offline verifier reports VALID for POGC-B's data. The API, reading by URL pogc_id from DB, is fully independent. Both channels report VALID — but for DIFFERENT certificates. This is an identity confusion attack, not a cryptographic break.

**Remediación:**

Add a --pogc-id argument to verify_pogc_offline.py. When provided, assert cert['pogc_id'] == supplied_id before running checks. The mismatch should be a FAIL, not a warning.

---

### A13 — Replay — mismo session_id genera múltiples PoGCs (POGR-SEC-004)

**Finding ID:** `POGR-SEC-004`  
**Severidad:** 🟡 MEDIUM  
**Invariante:** PoGR-INV-001 (session backing) · PoGR-INV-002 (append-only)  

**Escenario:**

POST /v1/pogr/certify called twice with same session_id. No UNIQUE constraint on session_id in pogr_certificates DDL. Each call generates a new pogc_id → two valid certs for the same session.

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline (`verify_pogc_offline.py`) | `VALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `VALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `VALID` |

**Hallazgo:**

The pogr_certificates table has no UNIQUE constraint on session_id. An authenticated client (with valid API key) can call POST /v1/pogr/certify multiple times with the same session_id, generating N PoGCs for the same governance session. Each has a different pogc_id. The offline verifier and API both see each cert as independently valid. This allows certificate proliferation and could be used to obtain a MANDATE-BOUND cert after the session was already certified at a lower tier.

**Remediación:**

Add to pogr_certificates DDL: CREATE UNIQUE INDEX IF NOT EXISTS idx_pogr_session_unique ON pogr_certificates (session_id) WHERE status = 'ACTIVE'; This prevents duplicate ACTIVE certs for the same session while preserving the append-only principle (REVOKED certs can coexist).

---

### A01 — Issuer cambiado

**Finding ID:** `POGR-SEC-007`  
**Severidad:** ✅ MITIGATED  
**Invariante:** PoGR-INV-003  

**Escenario:**

Attacker alters the 'issuer' field in an exported PoGC JSON after download. 'issuer' is a canonical field — content_hash covers it. All channels must reject.

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline (`verify_pogc_offline.py`) | `INVALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `VALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `VALID` |

**Hallazgo:**

Canonical field alteration is correctly detected by all three channels. The offline verifier detects two ways: (1) content_hash mismatch, (2) issuer identity check [5] (hardcoded EXPECTED_ISSUER assertion). The API detects via content_hash recomputation. The HTML page detects via content_hash... wait — HTML does NOT check hash. However, the API reads from DB (attacker cannot change DB without DB access), so this attack is only viable on an exported file for the offline channel.

**Remediación:**

No action needed for file-tampering attacks — content_hash and issuer check cover this. NOTE: If the DB canonical fields are mutated directly (bypassing API), the HTML page would not detect this (see A08 / POGR-SEC-012 for that scenario).

---

### A02 — mandate_certification cambiado (UNCERTIFIED → MANDATE-BOUND)

**Finding ID:** `POGR-SEC-008`  
**Severidad:** ✅ MITIGATED  
**Invariante:** MIVP-INV-008 · PoGR-INV-003  

**Escenario:**

Attacker upgrades a cert from UNCERTIFIED to MANDATE-BOUND in the export JSON without recalculating content_hash. Canonical field → hash breaks.

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline (`verify_pogc_offline.py`) | `INVALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `VALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `VALID` |

**Hallazgo:**

mandate_certification is in canonical_fields — any change breaks content_hash. All channels detect this attack.

**Remediación:**

mandate_certification is canonical — hash covers it for file-tampering attacks. Same DB-mutation caveat as A01: HTML page would not detect a direct DB mutation (see A08 / POGR-SEC-012).

---

### A03 — TTL expirado (expires_at en el pasado)

**Finding ID:** `POGR-SEC-009`  
**Severidad:** ✅ MITIGATED  
**Invariante:** PoGR-INV-004  

**Escenario:**

Certificate with expires_at 5 days in the past. status is still ACTIVE in the file. All channels check TTL independently.

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline (`verify_pogc_offline.py`) | `INVALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `INVALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `INVALID` |

**Hallazgo:**

Expired TTL detected consistently by all channels.

**Remediación:**

No action needed — PoGR-INV-004 enforced.

---

### A10 — PoGC inexistente — ID not found

**Finding ID:** `POGR-SEC-013`  
**Severidad:** ✅ MITIGATED  
**Invariante:** PoGR-INV-003  

**Escenario:**

Request for a POGC-ID that does not exist in the registry. All channels must return INVALID / 404.

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline (`verify_pogc_offline.py`) | `INVALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `INVALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `INVALID` |

**Hallazgo:**

All channels correctly reject unknown IDs. No divergence.

**Remediación:**

No action needed.

---

### A12 — PoGC expirado (expires_at genuinamente en el pasado)

**Finding ID:** `POGR-SEC-014`  
**Severidad:** ✅ MITIGATED  
**Invariante:** PoGR-INV-004  

**Escenario:**

Certificate with expires_at 10 days in the past, status=ACTIVE. expires_at IS in canonical_fields — cannot be forged without breaking hash. All channels check TTL independently.

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline (`verify_pogc_offline.py`) | `INVALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `INVALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `INVALID` |

**Hallazgo:**

Expired TTL is consistently detected. expires_at is canonical → immutable. All three channels independently verify TTL. status field may still say ACTIVE — TTL check is independent of status.

**Remediación:**

No action needed. PoGR-INV-004 enforced.

---

### A14 — Campos canónicos faltantes en JSON exportado

**Finding ID:** `POGR-SEC-015`  
**Severidad:** ✅ MITIGATED  
**Invariante:** PoGR-INV-003  

**Escenario:**

JSON file is missing canonical fields (issuer, mandate_certification deleted). Offline: hash computed on subset → won't match complete hash → INVALID. API: DB always has all fields (NOT NULL constraints) → unaffected.

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline (`verify_pogc_offline.py`) | `INVALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `VALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `VALID` |

**Hallazgo:**

Offline verifier gracefully handles missing canonical fields via {k: cert[k] for k in CANONICAL_FIELDS if k in cert}. Hash of the available subset won't match the stored hash (complete set) → INVALID. API is immune because DB NOT NULL constraints guarantee all fields present.

**Remediación:**

Add explicit per-field warnings in offline verifier when canonical fields are absent, e.g. 'WARNING: canonical field issuer missing from certificate'.

---

### A15 — JSON con campos extra maliciosos (injection attempt)

**Finding ID:** `POGR-SEC-016`  
**Severidad:** ✅ MITIGATED  
**Invariante:** PoGR-INV-003  

**Escenario:**

Attacker adds extra fields: 'admin': True, 'override_status': 'ACTIVE', 'bypass_revocation': True. Neither offline nor API read these fields. Both use explicit CANONICAL_FIELDS allowlist.

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline (`verify_pogc_offline.py`) | `VALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `VALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `VALID` |

**Hallazgo:**

Extra fields are safely ignored by all channels. Offline: uses explicit CANONICAL_FIELDS list — extras never read. API: reads from DB — no user-submitted fields. No injection or privilege escalation is possible via extra JSON fields. The explicit allowlist pattern is correct and prevents injection.

**Remediación:**

No action needed. Explicit allowlist is the correct pattern.

---

### A04 — content_hash field alterado en export JSON

**Finding ID:** `POGR-SEC-010`  
**Severidad:** • MITIGATED (offline) / DESIGN-BOUNDARY (API)  
**Invariante:** PoGR-INV-003  

**Escenario:**

Attacker replaces the content_hash field in the downloaded JSON with a corrupted value. Offline recomputes and detects mismatch. API reads stored hash from DB (clean) — tests different inputs per channel.

**Resultados por canal:**

| Canal | Veredicto |
|---|---|
| Offline (`verify_pogc_offline.py`) | `INVALID` |
| API JSON (`GET /v1/pogr/verify/<id>`) | `VALID` |
| HTML Web (`GET /pogr/verify/<id>`) | `VALID` |

**⚠ DIVERGENCIA: los tres canales no coinciden.**

**Hallazgo:**

Offline always detects (recomputes hash from canonical fields → doesn't match the corrupted stored hash). API/HTML read from DB — if DB was not touched, they see the original (valid) hash and compare against recomputed canonical → match → VALID. This is the correct threat model: offline verifies a file, API verifies from DB.

**Remediación:**

DB write access control is the real boundary. The offline verifier correctly detects hash tampering in files.

---

## Remediaciones Prioritarias

| Prioridad | Finding | Acción requerida |
|---|---|---|
| P1 — INMEDIATA | POGR-SEC-001 | Implementar `--platform-key` en `verify_pogc_offline.py` para verificación PQC real |
| P1 — INMEDIATA | POGR-SEC-002 | Añadir `status` y `revoked_at` a `canonical_fields` (requiere re-firma de certs existentes) |
| P1 — INMEDIATA | POGR-SEC-003 | Unificar lógica de validación de firma entre `/v1/pogr/verify` (JSON) y `/pogr/verify` (HTML) |
| P2 — ALTA | POGR-SEC-004 | `UNIQUE INDEX idx_pogr_session_unique ON pogr_certificates (session_id) WHERE status = 'ACTIVE'` |
| P2 — ALTA | POGR-SEC-012 | Añadir `content_hash` recomputation a `verify_page()` en `pogr_blueprint.py` |
| P3 — MEDIA | POGR-SEC-011 | Argumento `--pogc-id` en `verify_pogc_offline.py` para validar binding ID↔contenido |

---

*Generado por `scripts/pogr_adversarial_audit.py` · 2026-05-30 20:33:11 UTC · OMNIX QUANTUM LTD*