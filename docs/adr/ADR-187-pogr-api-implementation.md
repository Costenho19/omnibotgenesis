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
5. Read mandate_certification_tier from atf_mbr_seals (ADR-194)
   → MANDATE-BOUND | MANDATE-ALIGNED | UNCERTIFIED
6. Compute content_hash (SHA3-256 over canonical fields including mandate_certification)
7. Sign with platform ML-DSA-65 key
8. INSERT INTO pogr_certificates (append-only, PoGR-INV-002)
9. Return PoGC JSON + badge URL + mandate_certification + invariants_satisfied
```

### Canonical fields (content_hash + PQC signature scope)

```json
{
  "pogc_id":               "POGC-...",
  "session_id":            "OGR-...",
  "ctchc_seal_hash":       "sha3-256:...",
  "issuer":                "OMNIX QUANTUM LTD",
  "subject_org":           "...",
  "agent_id":              "...",
  "compliance_tier":       "ATF-BEV-Compliant",
  "mandate_certification": "MANDATE-BOUND | MANDATE-ALIGNED | UNCERTIFIED",
  "issued_at":             "...",
  "expires_at":            "..."
}
```

### Verify flow (PoGR-INV-003 — zero auth)

```
1. SELECT from pogr_certificates WHERE pogc_id = ?
2. Recompute content_hash (includes mandate_certification) and compare
3. Return { valid: bool, certificate: {...}, verification_notes: [...] }
```

### Implementation notes

- Append-only enforced at DB level: no DELETE, no UPDATE on core fields
- `expires_at` auto-set to `issued_at + 365 days` (PoGR-INV-004)
- `mandate_certification` read from `atf_mbr_seals` (ADR-194 MIVP) — non-blocking, defaults to UNCERTIFIED if MBR not found
- `mandate_certification` is part of canonical fields and PQC-signed — tamper-evident
- `MIVP-INV-008` added to `invariants_satisfied` when MANDATE-BOUND; `MIVP-INV-009` when MANDATE-ALIGNED
- Badge SVG dynamically includes mandate tier strip when MANDATE-BOUND or MANDATE-ALIGNED
- Platform public key in `/v1/pogr/manifest` mirrors `/api/forensic/platform-key`
- Badge SVG self-contained — no external resources (offline-embeddable)
- Public page URL: `/pogr/verify/{pogc_id}` (ADR-189 PoGRVerifyPage — zero-context, regulator-grade)

### GENESIS certificate

`scripts/issue_first_pogc.py` — standalone script to issue the first PoGC in the registry.
Creates a GENESIS OGR session, issues POGC-GENESIS-{HEX8} with MANDATE-BOUND tier.
Requires `DATABASE_URL`. Run via `railway run python scripts/issue_first_pogc.py`.

---

*ADR-187 · OMNIX QUANTUM LTD · Harold Nunes · May 2026*
