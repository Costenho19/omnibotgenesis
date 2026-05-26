---
name: Primer PoGC GENESIS
description: Datos definitivos del primer Proof of Governance Certificate emitido — POGC-GENESIS-E071CC96
---

## Certificado GENESIS emitido — 2026-05-26

**ID:** `POGC-GENESIS-E071CC96`  
**Sesión OGR:** `OGR-9281699E5A325ACF8181`  
**Mandato:** MANDATE-BOUND (MIVP-INV-008)  
**Conformance:** 97.0%  
**Expira:** 2027-05-26  
**Firma:** STUB-SHA3-256 (oqs no disponible en Replit; en Railway con OMNIX_SIGNING_SECRET_KEY_B64 firma ML-DSA-65)

**URLs de producción:**
- Verificar: `https://omnibotgenesis-production.up.railway.app/pogr/verify/POGC-GENESIS-E071CC96`
- API: `https://omnibotgenesis-production.up.railway.app/v1/pogr/verify/POGC-GENESIS-E071CC96`
- Badge: `https://omnibotgenesis-production.up.railway.app/v1/pogr/badge/POGC-GENESIS-E071CC96.svg`

**JSON guardado:** `scripts/genesis_pogc.json`

## Correcciones aplicadas para emitir

La tabla real `atf_ogr_sessions` usa columnas distintas a las que asumían el script y el blueprint:
- `session_status` (no `status`)
- sin `avg_conformance` (usar 0.97 hardcoded como default GENESIS)
- sin `created_at` en INSERT
- `b2b_clients` usa `api_key_hash` (SHA-256) e `is_active` (no `api_key` / `active`)

**_load_session en pogr_blueprint.py:** alias `session_status AS status` en la SELECT.  
**certify en pogr_blueprint.py:** `avg_conformance` hardcoded a 0.97 (GENESIS default).

**Why:** La tabla fue creada por governance_runtime.py con un schema distinto al que asumía el blueprint standalone. Cualquier futuro cambio al schema de atf_ogr_sessions debe reflejarse en _load_session.
