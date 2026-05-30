---
name: PoGR Security Hardening (ADR-205)
description: 4 correcciones críticas al PoGR blueprint tras audit adversarial. Lecciones de diseño para re-sign on revocation y unified kernel.
---

## Correcciones implementadas (ADR-205)

### C1 — CANONICAL_V2
`_CANONICAL_V2 = _CANONICAL_V1 + ["status", "revoked_at"]`
`CURRENT_CANONICAL_VERSION = 2`
Nuevos certs emitidos con `canonical_version=2`. Certs v1 (legacy) backward compat con warning.

### C2 — _verify_pqc_signature()
Usa `oqs.Signature("ML-DSA-65").verify()` real. Requiere `OMNIX_SIGNING_PUBLIC_KEY_B64`.
Si clave no configurada: warning no-bloqueante (None). Si falla verify(): `(False, "✗ INVALID")`.

### C3 — _verify_certificate_core() unificado
Kernel único compartido por JSON API (`verify()`) y HTML (`verify_page()`).
Antes: HTML no verificaba content_hash ni trataba STUB igual → divergencia.
Después: misma lógica → mismo veredicto en los 3 canales.

### C4 — revoke() re-firma bajo REVOKED
**Por qué es necesario:** status/revoked_at son canónicos en v2. Sin re-sign, el content_hash almacenado (firmado con ACTIVE) no coincide con el estado REVOKED al verificar → falso "hash mismatch" en vez de "REVOKED".

**Cómo:** El endpoint `revoke()` primero hace SELECT con todos los campos canónicos, luego computa canonical_v2 con status=REVOKED y re-firma antes del UPDATE. El UPDATE incluye `content_hash` y `pqc_signature` junto con status/revoked_at.

**Beneficio:** Fresh exports de certs REVOCADOS tienen hash correcto → verifican como INVALID (REVOKED) offline sin confusión de "hash mismatch".

## oqs en Replit — problema crítico
`import oqs` en Replit intenta compilar liboqs desde source (clona 48MB, necesita cmake).
**Solución:** Antes de `import oqs`, check `shutil.which("cmake")` → si None, skip y usar SHA3-256 sim.
En Railway (oqs ya instalado, cmake no necesario): el import funciona directamente.

## Audit v3.0 — SHA3-256 simulation
El audit script usa `AUDIT-PQC-SIM-V2: + payload` como clave de simulación.
`_sign_cert_audit` genera `ML-DSA-65:<sha3-256-of-payload>`.
`_verify_pqc_audit` recomputa el mismo hash y compara → detecta firmas forjadas (deadbeef != hash).
Esto permite confirmar que la lógica de verificación es correcta sin tener oqs disponible.

## A11 — Architectural limitation (MEDIUM, no CRITICAL)
Stale pre-revocation export: cert descargado ANTES de revocación sigue siendo VALID offline.
No es un bug: el cert era criptográficamente válido cuando se descargó.
Mitigación: (1) revoke() re-sign → fresh exports de REVOCADOS son INVALID offline.
(2) Mandatory revocation warning en verify_pogc_offline.py v2.0.
Severity: MEDIUM (documentado, esperado, inherente a verificación offline sin red).

## Audit exit condition
`sys.exit(0)` si 0 CRITICAL y 0 HIGH (A11 es MEDIUM → no bloquea exit 0).
v3.0 resultado: 0 CRITICAL, 0 HIGH, 12 MITIGATED, 1 divergencia arquitectónica (A11).

**Why:** El diseño canónico v2 es correcto para capturar estado de revocación en firma, pero requiere que el endpoint de revocación actualice el hash+sig atómicamente. Sin esto, los certs revocados muestran "hash mismatch" en vez de "REVOKED" — confuso para auditores.
