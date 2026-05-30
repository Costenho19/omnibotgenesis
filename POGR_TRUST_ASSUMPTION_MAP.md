# POGR Trust Assumption Map

**Sistema:** OMNIX Proof of Governance Registry (PoGR)  
**Fecha:** 2026-05-30 20:33:11 UTC  
**ADR:** ADR-186 · ADR-187 · ADR-189  

Este documento mapea las suposiciones de confianza de cada canal de verificación.
Una **suposición de confianza** es una condición que el canal asume verdadera sin verificar.

---

## Canal 1 — Offline Verifier (`verify_pogc_offline.py`)

### Qué verifica

| Check | Descripción | Resultado si falla |
|---|---|---|
| [1] content_hash | Recomputa SHA3-256 sobre canonical_fields → compara con stored | INVALID |
| [2] status | Lee campo `status` del JSON | INVALID si REVOKED/EXPIRED |
| [3] TTL | Compara `expires_at` con `now()` | INVALID si expirado |
| [4] pqc_signature | Verifica prefijo `ML-DSA-65:` o `STUB-` | Warning si STUB; INVALID si ausente |
| [5] issuer | Compara con hardcoded EXPECTED_ISSUER | INVALID si diferente |
| [6] mandate_certification | Detecta MANDATE-BOUND/ALIGNED/UNCERTIFIED | Warning si UNCERTIFIED |

### Suposiciones de confianza

| # | Suposición | Riesgo si falla | Mitigación actual |
|---|---|---|---|
| TA-01 | El archivo JSON fue descargado de una fuente confiable | Archivo manipulado pasa checks si no se alteran canonical fields | content_hash verifica integridad de los 10 campos canónicos |
| TA-02 | El campo `status` refleja el estado actual en DB | Cert revocado puede aparecer ACTIVE en archivo descargado antes de revocación | **SIN MITIGACIÓN** — POGR-SEC-002 |
| TA-03 | `pqc_signature` con prefijo `ML-DSA-65:` es criptográficamente válida | Firma forjada pasa el check | **SIN MITIGACIÓN** — POGR-SEC-001 |
| TA-04 | El `pogc_id` en el JSON corresponde al cert que el usuario quiere verificar | Cert de POGC-B presentado como POGC-A | Parcial — hash valida el contenido, no el mapeo ID→contenido (POGR-SEC-011) |
| TA-05 | Los campos canónicos están presentes y completos | Hash de subset → no coincide con hash completo | Mitigado — mismatch detectable (INVALID) |

### Límite de confianza

> **El offline verifier NO puede detectar revocación si el archivo fue descargado**
> **antes de la revocación.** El campo `status` no está firmado criptográficamente.
> **Para verificación de revocación, SIEMPRE consultar el API en tiempo real.**
> El offline verifier NO verifica la firma PQC criptográficamente.

---

## Canal 2 — JSON API (`GET /v1/pogr/verify/<pogc_id>`)

### Qué verifica

| Check | Descripción | Resultado si falla |
|---|---|---|
| [1] content_hash | Recomputa SHA3-256 desde DB → compara con stored content_hash | valid=False |
| [2] status | Lee status de DB en tiempo real | valid=False si REVOKED/EXPIRED |
| [3] TTL | Compara expires_at de DB con now() | valid=False si expirado |
| [4] pqc_signature | Verifica prefijo — STUB = Warning (no False) | Warning si STUB |

### Suposiciones de confianza

| # | Suposición | Riesgo si falla | Mitigación actual |
|---|---|---|---|
| TA-06 | La DB no ha sido mutada directamente (bypass API) | Campos canónicos cambiados en DB → hash mismatch → INVALID | Recomputa hash en cada /verify call ✓ |
| TA-07 | `pqc_signature` en DB fue generada correctamente al certify | Firma incorrecta pasa (solo verifica prefijo) | **SIN MITIGACIÓN** — POGR-SEC-001 |
| TA-08 | DB tiene integridad referencial y NOT NULL activos | Campos faltantes → 500 errors | DB DDL enforced ✓ |
| TA-09 | El resultado es consistente con el HTML page (/pogr/verify) | STUB sig → JSON API=VALID, HTML=INVALID | **ROTA** — POGR-SEC-003 |

### Límite de confianza

> El JSON API lee siempre de DB (tiempo real) — detecta revocación correctamente.
> NO verifica la firma PQC criptográficamente.
> La consistencia con el canal HTML **no está garantizada** (POGR-SEC-003).

---

## Canal 3 — HTML Web (`GET /pogr/verify/<pogc_id>`)

### Qué verifica

| Check | Descripción | Resultado si falla |
|---|---|---|
| [1] status | Lee status de DB en tiempo real | INVALID si REVOKED/EXPIRED |
| [2] TTL | Compara expires_at de DB con now() | INVALID si expirado |
| [3] pqc_signature | sig.startswith('ML-DSA-65:') — STUB = INVALID (no warning) | INVALID si STUB |
| ❌ [4] content_hash | **NO VERIFICADO** | **No aplica — no se verifica** |

### Suposiciones de confianza

| # | Suposición | Riesgo si falla | Mitigación actual |
|---|---|---|---|
| TA-10 | La lógica HTML es equivalente a la JSON API | **ROTA** — HTML no verifica content_hash | **SIN MITIGACIÓN** — POGR-SEC-003/POGR-SEC-012 |
| TA-11 | status=ACTIVE + sig ML-DSA-65: implica certificado íntegro | Firma forjada o hash corrupto pasan sin detección | **SIN MITIGACIÓN** — POGR-SEC-001/003 |
| TA-12 | STUB firma = inválida (no producción) | HTML dice INVALID; JSON API dice VALID | **ROTA** — POGR-SEC-003 (divergencia) |

### Límite de confianza

> **El canal HTML es el más débil:** no verifica content_hash.
> Un cert con content_hash corrupto pero status=ACTIVE y sig ML-DSA-65:
> **pasaría el HTML pero fallaría el JSON API.**
> El canal HTML no debe ser citado como prueba de verificación completa.

---

## Matriz de Verificación Cross-Canal

| Propiedad | Offline | API JSON | HTML Web |
|---|---|---|---|
| `content_hash` recomputado | ✅ Sí | ✅ Sí | ❌ **No** |
| `status` actual (tiempo real DB) | ❌ No (depende del archivo) | ✅ Sí | ✅ Sí |
| TTL (`expires_at`) | ✅ Sí | ✅ Sí | ✅ Sí |
| `issuer` explícito | ✅ Sí (hardcoded check [5]) | ❌ Solo por hash | ❌ Solo por hash |
| Firma PQC criptográfica | ❌ Solo prefijo | ❌ Solo prefijo | ❌ Solo prefijo |
| Revocación post-export | ❌ No puede detectar | ✅ Sí | ✅ Sí |
| Campos extra ignorados | ✅ Sí (allowlist) | ✅ Sí (DB) | ✅ Sí (DB) |
| Binding ID↔contenido | ⚠ Parcial | ✅ Sí (DB lookup) | ✅ Sí (DB lookup) |
| STUB firma → INVALID | ⚠ Solo si STUB prefix sin ML-DSA | ❌ STUB=Warning | ✅ Sí |

---

## Propiedades de Seguridad Garantizadas

1. **Integridad de campos canónicos** — cualquier alteración de los 10 campos
   canónicos rompe el `content_hash` y es detectada por Offline y API.
2. **Revocación en tiempo real** — API y HTML leen de DB → detectan revocación.
3. **TTL no falsificable** — `expires_at` es canónico → no se puede extender sin romper hash.
4. **Append-only** — DB no tiene DELETE en core fields (PoGR-INV-002).
5. **Campos extra inocuos** — todos los canales ignoran extras vía allowlist explícita.
6. **Issuer verificado explícitamente** — offline verifier tiene check hardcoded de EXPECTED_ISSUER.

## Propiedades de Seguridad NO Garantizadas (Gaps Activos)

1. **Verificación PQC** — ningún canal verifica la firma ML-DSA-65 criptográficamente (POGR-SEC-001).
2. **Revocación offline** — archivo previo a revocación pasa el offline verifier (POGR-SEC-002).
3. **Consistencia HTML/API** — HTML no verifica content_hash (POGR-SEC-003).
4. **Unicidad de sesión** — mismo session_id puede generar N PoGCs (POGR-SEC-004).
5. **Binding ID↔contenido en offline** — no hay validación que pogc_id en archivo == ID solicitado (POGR-SEC-011).

---

*Generado por `scripts/pogr_adversarial_audit.py` · 2026-05-30 20:33:11 UTC · OMNIX QUANTUM LTD*