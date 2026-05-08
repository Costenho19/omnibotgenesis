# ADR-089 — RBAC Enforcement Layer

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-16 |
| **Author** | Harold Nunes — OMNIX QUANTUM LTD |
| **Scope** | `omnix_web/api/gov_blueprint.py` · `omnix_web/api/omnix_engine/b2b_auth.py` |
| **Replaces** | — |

---

## Context

The B2B API authentication model (ADR-028) verified API key validity but did not enforce role-based access control. All authenticated clients had identical access to all endpoints, including admin endpoints that should be restricted to OMNIX operators.

Three access tiers needed formal enforcement:

1. **READ** — query receipts, verify signatures, access analytics
2. **WRITE** — submit governance evaluation requests
3. **ADMIN** — manage clients, rotate keys, configure webhooks, access raw audit logs

## Decision

Implement an RBAC decorator applied at route definition:

```python
@governance_bp.route("/api/governance/admin/clients", methods=["GET"])
@require_role("ADMIN")
def list_clients():
    ...

@governance_bp.route("/api/governance/evaluate", methods=["POST"])
@require_role("WRITE")
def evaluate():
    ...
```

### Role assignment

Roles are stored in the `b2b_clients` table:

```sql
ALTER TABLE b2b_clients ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'WRITE'
    CHECK (role IN ('READ', 'WRITE', 'ADMIN'));
```

OMNIX internal service accounts use `ADMIN`. External B2B clients default to `WRITE`. Read-only partners (auditors, compliance teams) are provisioned as `READ`.

### Error response on insufficient role

```json
{
  "status": "FORBIDDEN",
  "required_role": "ADMIN",
  "client_role": "WRITE",
  "adr": "ADR-089"
}
```

HTTP 403 returned. The specific route is not disclosed in the error response.

## Consequences

**Positive:**
- Admin endpoints are inaccessible to external clients regardless of key validity.
- Role changes take effect immediately without key rotation.
- RBAC violations are logged with client ID and attempted route.

**Negative:**
- Existing clients default to WRITE; a manual audit is required to downgrade any clients who should be READ-only.

## Related

- ADR-028: External Signal Evaluation API
- ADR-088: API Key Rotation Policy
- ADR-123: External API Security Hardening
