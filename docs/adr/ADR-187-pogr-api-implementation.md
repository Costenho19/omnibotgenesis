# ADR-187 — Proof of Governance Registry: API Implementation

**Status:** Accepted  
**Author:** Harold Nunes  
**Date:** 2026-05-24  
**Supersedes:** —  
**Implements:** ADR-186 (Proof of Governance Public Registry)  
**Related:** ADR-184 (OGR) · ADR-176 (Governance API Product)  
**Blueprint:** `omnix_web/api/pogr_blueprint.py`

---

## Context

ADR-186 defined the Proof of Governance Registry (PoGR) architecture and its six invariants. This ADR specifies the concrete implementation: Flask blueprint, database integration, badge SVG generator, and public verification protocol.

---

## Decision

### Flask Blueprint: `pogr_blueprint.py`

Registered under no URL prefix — endpoints live at `/v1/pogr/*` by design.

| Endpoint | Auth | Rate Limit | Description |
|---|---|---|---|
| `POST /v1/pogr/certify` | API Key | 60/min | Issue certificate from sealed OGR session |
| `GET /v1/pogr/verify/<pogc_id>` | None | 300/min | Public certificate verification |
| `GET /v1/pogr/certificate/<pogc_id>` | None | 300/min | Full certificate JSON |
| `GET /v1/pogr/organization/<org_id>` | None | 60/min | All certs for an org |
| `GET /v1/pogr/manifest` | None | 120/min | Registry manifest + public key |
| `GET /v1/pogr/badge/<pogc_id>.svg` | None | 600/min | Embeddable SVG badge |
| `POST /v1/pogr/revoke/<pogc_id>` | API Key + PQC proof | 10/min | Revoke certificate |

### Certify flow (PoGR-INV-001)

```
1. Authenticate API key → resolve b2b_client
2. Load OGR session via GovernanceRuntime
3. Assert session.status == "SEALED" (PoGR-INV-001)
4. Assert session.chain_seal exists
5. Compute content_hash (SHA3-256 over canonical fields)
6. Sign with platform ML-DSA-65 key
7. INSERT INTO pogr_certificates (append-only, PoGR-INV-002)
8. Return PoGC JSON + badge URL
```

### Verify flow (PoGR-INV-003 — zero auth)

```
1. SELECT from pogr_certificates WHERE pogc_id = ?
2. Recompute content_hash and compare
3. Return { valid: bool, certificate: {...}, verification_notes: [...] }
```

### Implementation notes

- Append-only enforced at DB level: no DELETE, no UPDATE on core fields
- `expires_at` auto-set to `issued_at + 365 days` (PoGR-INV-004)
- Platform public key in `/v1/pogr/manifest` mirrors `/api/forensic/platform-key`
- Badge SVG self-contained — no external resources (offline-embeddable)

---

*ADR-187 · OMNIX QUANTUM LTD · Harold Nunes · May 2026*
