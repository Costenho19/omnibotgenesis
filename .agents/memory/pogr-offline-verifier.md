---
name: PoGR Offline Verifier
description: Scripts, bugs, and schema notes for the PoGR offline verification layer (ADR-189).
---

## Offline verifier script
`scripts/verify_pogc_offline.py` — Python 3.8+, stdlib only, no external deps.
- 6 checks: content hash, status, TTL, PQC signature, issuer, mandate certification
- Exit codes: 0=VALID, 1=INVALID/WARNING, 2=usage error
- `--json` flag for machine-readable output

## Export endpoint
`GET /v1/pogr/certificate/<pogc_id>/export` — returns certificate + `_offline_verification` block with canonical fields schema, Python snippet, verifier command. No auth required (PoGR-INV-003).

## Bug fixes applied
- `b2b_clients` column is `is_active`, NOT `active`. pogr_blueprint._auth_api_key had the wrong column name.
- `PoGRVerifyPage.tsx` share URL and navigate used `/verify/` instead of `/pogr/verify/`. Two locations fixed.

## Canonical fields (content_hash scope)
10 fields: pogc_id · session_id · ctchc_seal_hash · issuer · subject_org · agent_id · compliance_tier · mandate_certification · issued_at · expires_at

**Why:** Any party — regulator, auditor, court — must be able to verify a PoGC with zero OMNIX access. The 6-line Python snippet is the minimum viable proof of integrity.

**How to apply:** When the canonical fields list changes, update: (1) `_canonical_fields()` in pogr_blueprint.py, (2) `CANONICAL_FIELDS` in scripts/verify_pogc_offline.py, (3) `_offline_verification.canonical_fields_schema` in export endpoint, (4) ADR-189 §Canonical Fields Schema.
