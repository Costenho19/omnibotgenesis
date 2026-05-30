---
name: PoGR Adversarial Audit
description: Resultados de la auditoría adversarial v2.0 de PoGR — 15 ataques, 3 canales, hallazgos clave.
---

## Audit v2.0 — Resultados

**Script:** `scripts/pogr_adversarial_audit.py`  
**Reportes:** `POGR_ADVERSARIAL_AUDIT.md` · `POGR_TRUST_ASSUMPTION_MAP.md` · `POGR_WEB_API_OFFLINE_CONSISTENCY_REPORT.md`

## Resumen de hallazgos

| Métrica | Valor |
|---|---|
| Total ataques | 15 |
| Divergencias reales | 5 (A04, A07, A08, A09, A11) |
| CRITICAL | 3 |
| HIGH | 2 |
| MEDIUM | 2 |
| MITIGATED | 7 |

## Hallazgos CRITICAL

**POGR-SEC-001** — pqc_signature no se verifica criptográficamente. Todos los canales solo comprueban el prefijo `ML-DSA-65:`. Un atacante puede poner cualquier payload tras el prefijo y pasar todos los checks. Remediación: implementar `--platform-key` en `verify_pogc_offline.py` y verificación criptográfica real en la API.

**POGR-SEC-002** — `status` NO está en `canonical_fields`. Un export descargado antes de revocar el cert tiene `status=ACTIVE` con hash válido. Offline: VALID. API/HTML: INVALID. Esta es la divergencia más explotable. Afecta A07 y A11.

## Hallazgos HIGH

**POGR-SEC-003** — STUB signature tratada distinto: API JSON = VALID (warning), HTML page = INVALID ("FIRMA EN PROCESO"). React SPA (llama API) = VALID. Directamente en /pogr/verify = INVALID. Afecta A09.

**POGR-SEC-012** — HTML page `/pogr/verify/<id>` NO verifica `content_hash`. Solo verifica: `status_db == 'ACTIVE' and not expired and sig.startswith('ML-DSA-65:')`. Si el DB tiene hash incorrecto → API=INVALID, HTML=VALID. Afecta A08.

## Hallazgos MEDIUM

**POGR-SEC-004** — No hay UNIQUE constraint en `session_id` en `pogr_certificates`. Un mismo session puede generar N PoGCs. Remediación: `CREATE UNIQUE INDEX idx_pogr_session_unique ON pogr_certificates (session_id) WHERE status = 'ACTIVE'`.

**POGR-SEC-011** — Offline verifier no valida que el `pogc_id` en el archivo corresponda al ID solicitado. Un atacante puede presentar POGC-B como POGC-A. Remediación: argumento `--pogc-id` en el verifier.

## Canales — niveles de confianza

| Canal | Nivel | content_hash | Revocación RT | PQC |
|---|---|---|---|---|
| Offline | ⚠ CONDICIONAL | ✅ Sí | ❌ No | ❌ Solo prefijo |
| API JSON | ✅ ALTO | ✅ Sí | ✅ Sí | ❌ Solo prefijo |
| HTML Web | 🔴 BAJO | ❌ No | ✅ Sí | ❌ Solo prefijo |

## Divergencias por ataque

| Ataque | Offline | API | HTML | Root |
|---|---|---|---|---|
| A04 (hash en export) | INVALID | VALID | VALID | Expected (file vs DB) |
| A07 (status REVOKED→ACTIVE) | VALID | INVALID | INVALID | POGR-SEC-002 |
| A08 (DB mutation) | VALID | INVALID | VALID | POGR-SEC-012 |
| A09 (STUB sig) | VALID | VALID | INVALID | POGR-SEC-003 |
| A11 (stale export revoked) | VALID | INVALID | INVALID | POGR-SEC-002 |

**Why:** `status` no canónico + HTML sin hash check + STUB tratado distinto = tres fuentes independientes de divergencia.
