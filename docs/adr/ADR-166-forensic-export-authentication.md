# ADR-166 — Forensic Export Endpoint Authentication & Platform Key Pinning

**Status:** Accepted  
**Date:** 2026-05-15  
**Author:** Harold Nunes / OMNIX QUANTUM LTD  
**Supersedes:** Security note in ADR-165 §4 (previously deferred)  
**Related:** ADR-052 (B2B RBAC), ADR-164 (Forensic Portal), ADR-165 (OEP Format)

---

## Context

`POST /api/forensic/export` generates OMNIX Evidence Packages (OEP) signed with a
Dilithium-3 private key. The original implementation accepted any caller-provided key
(`secret_key_b64` in the JSON body), with no authentication gate. This created two
institutional risks:

1. **Impersonation:** Any unauthenticated caller could generate an OEP purportedly from
   OMNIX QUANTUM, using an arbitrary key not associated with the platform.

2. **Key exposure surface:** Callers providing their own private key transmitted it in an
   HTTP request body — an unnecessary exposure path.

The endpoint was documented as requiring "future auth + key-pinning" (ADR-165 security note).
This ADR closes that gap.

---

## Decision

### §1 — Authentication Gate

`POST /api/forensic/export` requires a valid `X-API-Key` header authenticated against
the `b2b_clients` table with `role = 'admin'`. Unauthenticated or `role = 'standard'`
requests receive `401 Unauthorized`.

`GET /api/forensic/status` and `POST /api/forensic/verify` remain public (read-only
operations; rate-limited per ADR-164 §4).

### §2 — Audit Logging

Every export call logs: `client_id`, `client_name`, `ip_address`, `package_id`,
`key_source` (`platform` | `caller`), `block_count`, `timestamp`. This creates a
non-repudiable chain of custody for who requested which OEP.

### §3 — Platform Key Resolution

The endpoint resolves keys in this order:

| Priority | Condition | Result |
|---|---|---|
| 1 | `FORENSIC_EXPORT_ALLOW_CALLER_KEYS=true` AND caller provides `secret_key_b64` | Use caller key (`key_source=caller`) |
| 2 | `OMNIX_SIGNING_SECRET_KEY_B64` present in env | Use platform key (`key_source=platform`) |
| 3 | Neither condition met | Return `503` — fail-closed (OEP-INV-003) |

`FORENSIC_EXPORT_ALLOW_CALLER_KEYS` defaults to `false`. It MUST NOT be set `true`
in production — it exists exclusively for local development and integration testing.

Similarly, `public_key_b64` falls back to `OMNIX_SIGNING_PUBLIC_KEY_B64` when absent.

### §4 — Key Isolation Invariant (FEA-INV-001)

> **FEA-INV-001:** The Dilithium-3 private key used for OEP signing MUST NOT be transmitted
> in HTTP request bodies in production. Platform key resolution (§3) enforces this
> invariant by reading the key from the server environment, never from the caller.

---

## Consequences

- All production OEPs carry the platform public key fingerprint (verifiable by third parties).
- OEP generation is auditable per authenticated client.
- Dev/test workflows using caller-provided keys require `FORENSIC_EXPORT_ALLOW_CALLER_KEYS=true`
  in the local environment — this is a deliberate friction to prevent production misconfiguration.
- `provision_b2b_client.py` is the provisioning path for `admin`-role keys granted to
  authorized forensic operators.

---

## Invariants

| ID | Statement |
|---|---|
| FEA-INV-001 | Platform private key never transmitted in HTTP request body in production |
| FEA-INV-002 | Every OEP export is logged with `client_id`, `ip`, `key_source`, `package_id` |
| FEA-INV-003 | `/export` returns 401 for missing/invalid/expired API key |
| FEA-INV-004 | `/export` returns 503 (fail-closed) when no signing key is available |
| FEA-INV-005 | `FORENSIC_EXPORT_ALLOW_CALLER_KEYS=true` is forbidden in production |

---

## Migration

Existing callers providing `secret_key_b64` directly must:
1. Obtain an `admin`-role API key via `provision_b2b_client.py`
2. Remove `secret_key_b64` from request body (platform key used automatically)
3. Add `X-API-Key: <key>` header

No database schema changes required. `b2b_clients` table already supports `role = 'admin'`.
