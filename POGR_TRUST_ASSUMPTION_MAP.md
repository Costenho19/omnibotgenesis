# POGR Trust Assumption Map — v3.0 (post-ADR-205)

**Sistema:** OMNIX Proof of Governance Registry (PoGR)  
**Fecha:** 2026-05-30 21:19:36 UTC  
**ADR:** ADR-186 · ADR-187 · ADR-189 · ADR-205  

Este documento mapea las suposiciones de confianza de cada canal de verificación
tras las correcciones de ADR-205.

---

## Canal 1 — Offline Verifier (`verify_pogc_offline.py` v2.0)

### Qué verifica (v2.0)

| Check | Descripción | Resultado si falla |
|---|---|---|
| [1] content_hash (v1/v2) | SHA3-256 de CANONICAL_V1 o V2 según canonical_version | INVALID |
| [2] status | Lee campo `status` del JSON | INVALID si REVOKED/EXPIRED |
| [3] TTL | Compara `expires_at` con `now()` | INVALID si expirado |
| [4] PQC signature | ML-DSA-65 real si `--platform-key` provisto; prefijo-only si no | INVALID si falla cripto |
| [5] issuer | Compara con hardcoded EXPECTED_ISSUER | INVALID si diferente |
| [6] mandate_certification | BOUND/ALIGNED/UNCERTIFIED | Warning si UNCERTIFIED |
| [7] canonical_version warning | v1 → avisa que status no está firmado | Warning |

### Suposiciones de confianza

| # | Suposición | Riesgo si falla | Estado |
|---|---|---|---|
| TA-01 | El archivo JSON fue descargado de una fuente confiable | Archivo manipulado pasa checks si no se alteran campos canónicos | content_hash v2 cubre status+revoked_at ✓ |
| TA-02 | El campo `status` refleja el estado ACTUAL en DB | Cert revocado post-export aparece ACTIVE en stale file | CAVEAT documentado — ver A11 |
| TA-03 | `pqc_signature` es criptográficamente válida | Firma forjada | ✅ MITIGADO — oqs.verify() en blueprint; audit sim detecta forged |
| TA-04 | El `pogc_id` en JSON corresponde al cert solicitado | ID swap — POGC-B presentado como POGC-A | Parcial — MEDIUM (POGR-SEC-011) |
| TA-05 | Campos canónicos presentes y completos | Hash de subset → mismatch → INVALID | Mitigado ✓ |

### Límite de confianza

> **Offline verifier NO puede detectar revocación ocurrida DESPUÉS del export.**
> Para verificación de revocación en tiempo real: `GET /v1/pogr/verify/<id>`.
> PQC criptográfica verificada en producción (Railway) con `OMNIX_SIGNING_PUBLIC_KEY_B64`.

---

## Canal 2 — JSON API (`GET /v1/pogr/verify/<pogc_id>`)

### Qué verifica (v2.0 — shared kernel)

| Check | Descripción | Resultado si falla |
|---|---|---|
| [1] content_hash | SHA3-256 desde DB → compara stored | valid=False |
| [2] status | Lee status de DB en tiempo real | valid=False si REVOKED/EXPIRED |
| [3] TTL | Compara expires_at de DB con now() | valid=False si expirado |
| [4] PQC signature | oqs.verify() si OMNIX_SIGNING_PUBLIC_KEY_B64 configurada | valid=False si falla cripto |

### Suposiciones de confianza

| # | Suposición | Riesgo si falla | Estado |
|---|---|---|---|
| TA-06 | DB no mutada directamente (bypass API) | Campos canónicos cambiados → hash mismatch → INVALID | Hash recomputado en cada /verify ✓ |
| TA-07 | pqc_signature en DB fue generada correctamente | Firma incorrecta | ✅ MITIGADO — oqs.verify() activo si PK configurada |
| TA-08 | DB tiene integridad referencial | Campos faltantes → 500 | DDL enforced ✓ |
| TA-09 | Consistente con HTML canal | — | ✅ MITIGADO — kernel unificado ADR-205 |

---

## Canal 3 — HTML Web (`GET /pogr/verify/<pogc_id>`)

### Qué verifica (v2.0 — shared kernel, ADR-205)

| Check | Descripción | Resultado si falla |
|---|---|---|
| [1] content_hash | ✅ SHA3-256 desde DB (AÑADIDO — ADR-205) | INVALID |
| [2] status | Lee status de DB en tiempo real | INVALID si REVOKED/EXPIRED |
| [3] TTL | Compara expires_at de DB con now() | INVALID si expirado |
| [4] PQC signature | oqs.verify() si PK configurada | INVALID si falla cripto |

### Cambio ADR-205

> **ANTES:** `valid = status_db == 'ACTIVE' and not expired and sig.startswith('ML-DSA-65:')`
> — sin verificación de content_hash · STUB tratado diferente que JSON API.
>
> **AHORA:** `valid, notes, _ = _verify_certificate_core(cert)` — mismo kernel que JSON API.

---

## Matriz de Verificación Cross-Canal — v3.0

| Propiedad | Offline | API JSON | HTML Web |
|---|---|---|---|
| `content_hash` recomputado | ✅ Sí (v1/v2) | ✅ Sí | ✅ Sí (**ADR-205**) |
| `status` actual (DB) | ❌ No (archivo) | ✅ Sí | ✅ Sí |
| `status` canónico (firmado v2) | ✅ Sí si v2 | ✅ Sí si v2 | ✅ Sí si v2 |
| TTL (`expires_at`) | ✅ Sí | ✅ Sí | ✅ Sí |
| `issuer` explícito | ✅ Sí (hardcoded [5]) | ✅ Vía hash | ✅ Vía hash |
| Firma PQC criptográfica | ✅ Con --platform-key | ✅ Con PK env | ✅ Con PK env |
| Revocación post-export | ❌ No puede (stale) | ✅ Sí (DB) | ✅ Sí (DB) |
| Campos extra ignorados | ✅ Allowlist | ✅ DB | ✅ DB |
| Binding ID↔contenido | ⚠ Parcial (MEDIUM) | ✅ DB lookup | ✅ DB lookup |
| STUB firma → misma respuesta | ✅ Warning | ✅ Warning | ✅ Warning (**ADR-205**) |

---

## Gaps de Seguridad Cerrados (ADR-205)

1. **✅ Verificación PQC real** — oqs.Signature('ML-DSA-65').verify() activo.
2. **✅ status canónico** — firmado en CANONICAL_V2; alteración detectada.
3. **✅ Consistencia HTML/API** — kernel unificado; cero divergencia por STUB.
4. **✅ content_hash en HTML** — verify_page() usa _verify_certificate_core().

## Gaps Residuales

1. **Revocación offline (stale export)** — MEDIUM · arquitectónico · documentado (A11).
2. **Unicidad de sesión** — MEDIUM · DB index pendiente (A13).
3. **Binding ID↔contenido offline** — MEDIUM · --pogc-id pendiente (A06).

---

*Generado por `scripts/pogr_adversarial_audit.py` v3.0 · 2026-05-30 21:19:36 UTC · OMNIX QUANTUM LTD*