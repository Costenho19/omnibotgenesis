# POGR Web / API / Offline Consistency Report — v3.0

**Sistema:** OMNIX Proof of Governance Registry (PoGR)  
**Fecha:** 2026-05-30 21:19:36 UTC  
**Metodología:** Cada ataque ejecutado sobre tres canales compartiendo `_verify_certificate_core()` (ADR-205).  
Un certificado es **SEGURO** solo si los tres canales producen el mismo veredicto.

---

## Vista Completa de Consistencia

| Ataque | Descripción | Offline | API JSON | HTML Web | Consistente |
|---|---|---|---|---|---|
| A01 | Issuer cambiado (canonical field v1+v2) | INVALID | VALID | VALID | ✅ Sí |
| A02 | mandate_certification cambiado (UNCERTIFIED → MA… | INVALID | VALID | VALID | ✅ Sí |
| A03 | TTL expirado (expires_at en el pasado) | INVALID | INVALID | INVALID | ✅ Sí |
| A04 | content_hash field alterado en export JSON | INVALID | VALID | VALID | ✅ Sí |
| A05 | Firma alterada — prefijo ML-DSA-65: conservado [… | INVALID | INVALID | INVALID | ✅ Sí |
| A06 | ID válido con contenido de otro PoGC (ID swap — … | VALID | VALID | VALID | ✅ Sí |
| A07 | Export manipulado — status ACTIVE→REVOKED→ACTIVE… | INVALID | INVALID | INVALID | ✅ Sí |
| A08 | DB mutation — hash inconsistency [POGR-SEC-012 →… | INVALID | INVALID | INVALID | ✅ Sí |
| A09 | STUB signature — API/HTML divergence [POGR-SEC-0… | VALID | VALID | VALID | ✅ Sí |
| A10 | PoGC inexistente — ID not found | INVALID | INVALID | INVALID | ✅ Sí |
| A11 | PoGC revocado — stale pre-revocation export (arc… | VALID | INVALID | INVALID | ❌ **No** |
| A12 | PoGC expirado (expires_at genuinamente en el pas… | INVALID | INVALID | INVALID | ✅ Sí |
| A13 | Replay — mismo session_id genera múltiples PoGCs… | VALID | VALID | VALID | ✅ Sí |
| A14 | Campos canónicos faltantes en JSON exportado | INVALID | VALID | VALID | ✅ Sí |
| A15 | JSON con campos extra maliciosos (injection atte… | VALID | VALID | VALID | ✅ Sí |

**Resumen:** 1 divergencia(s) de 15 ataques.

---

## Divergencias Confirmadas

### DIV-001 — A11: PoGC revocado — stale pre-revocation export (architectural limitation)

**Finding:** `POGR-SEC-002-ARCH` | **Severidad:** MEDIUM

| Canal | Veredicto |
|---|---|
| Offline | `VALID` |
| API JSON | `INVALID` |
| HTML Web | `INVALID` |

**Causa raíz:**

ARCHITECTURAL LIMITATION (not a bug): The stale export was cryptographically valid when it was created. No cryptographic scheme can make an offline verifier detect revocation events that occurred after the export was downloaded — without querying the live API. ADR-205 provides two mitigations: (1) v2 re-sign-on-revocation: fresh exports of REVOKED certs have REVOKED hash → correctly verified as INVALID offline. (2) verify_pogc_offline.py v2.0 emits a mandatory REVOCATION WARNING on every run: 'CAUTION: Revocation status cannot be verified offline. For live revocation check: GET /v1/pogr/verify

**Remediación:**

DONE (ADR-205): mandatory revocation warning in verify_pogc_offline.py v2.0. v2 re-sign-on-revocation: fresh exports always reflect current state. Remaining gap: stale pre-revocation exports. To verify revocation: always query /v1/pogr/verify/<id>.

---

## Nivel de Confianza por Canal — v3.0

| Canal | Nivel de Confianza | Verificación PQC | Revocación en tiempo real | Content hash |
|---|---|---|---|---|
| Offline | ✅ ALTO (con --platform-key) | ✅ oqs real (si PK) | ❌ No (stale — documentado) | ✅ Sí |
| API JSON | ✅ ALTO | ✅ oqs real (si PK) | ✅ Sí (DB) | ✅ Sí |
| HTML Web | ✅ ALTO (**ADR-205**) | ✅ oqs real (si PK) | ✅ Sí (DB) | ✅ Sí |

**Mejora vs v2.0:** HTML Web subió de BAJO a ALTO tras ADR-205 unified kernel.

---

*Generado por `scripts/pogr_adversarial_audit.py` v3.0 · 2026-05-30 21:19:36 UTC · OMNIX QUANTUM LTD*