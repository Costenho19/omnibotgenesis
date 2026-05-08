# ADR-088 — API Key Rotation Policy

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-15 |
| **Author** | Harold Nunes — OMNIX QUANTUM LTD |
| **Scope** | `omnix_web/api/gov_blueprint.py` · `omnix_web/api/omnix_engine/b2b_auth.py` |
| **Replaces** | — |

---

## Context

B2B API keys provisioned via `provision_b2b_client.py` had no expiration mechanism and could not be rotated without manual database intervention. For enterprise clients operating under ISO 27001 or SOC 2, this violated key management requirements that mandate:

- Maximum key lifetime of 90–365 days (depending on sensitivity tier)
- Ability to rotate keys without downtime (dual-key overlap window)
- Immediate revocation capability for suspected compromise

## Decision

### Key lifecycle model

Each API key has:
- `created_at`: provisioning timestamp
- `expires_at`: `created_at + max_age` (configurable per plan)
- `revoked_at`: set immediately on revocation; key rejected on next request
- `successor_id`: FK to the replacement key (rotation chain)

### Default expiration by tier

| Plan | Max Key Age |
|---|---|
| Sandbox | 30 days |
| Starter | 180 days |
| Professional | 365 days |
| Enterprise | Configurable (up to 2 years) |

### Rotation flow

1. Client calls `POST /api/governance/admin/clients/{id}/rotate-key`
2. New key generated; old key enters 24h overlap window (both valid)
3. After 24h, old key rejected with `KEY_ROTATED` error pointing to new key
4. Rotation event written to `b2b_audit_log`

### Revocation

`DELETE /api/governance/admin/clients/{id}/key` immediately invalidates the key. No overlap window. Used for suspected compromise.

## Consequences

**Positive:**
- Enterprise clients can meet ISO 27001 / SOC 2 key management requirements.
- 24h overlap window prevents downtime during planned rotations.
- Full audit trail of all key lifecycle events.

**Negative:**
- Clients using long-lived keys must implement key expiration handling.
- Rotation endpoint requires admin-level authentication.

## Related

- ADR-083: Enterprise Bot Security
- ADR-086: B2B API Load Stability
- ADR-123: External API Security Hardening
