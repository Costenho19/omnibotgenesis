# ADR-102 — B2B Client Portal v2

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-20 |
| **Author** | Harold Nunes — OMNIX QUANTUM LTD |
| **Scope** | `omnix_web/src/pages/ClientDashboard.tsx` · `omnix_web/api/gov_blueprint.py` |
| **Replaces** | ADR-062 (Premium Features / Client Portal v1) |

---

## Context

The Client Portal v1 (ADR-062) provided API key display and basic usage metrics. Enterprise clients onboarding in Q2 2026 required:

1. **Real-time quota visualization** — live view of daily/monthly quota consumption with projected burn rate.
2. **Per-domain governance breakdown** — which domains they're calling, APPROVED/BLOCKED/HOLD rates by domain.
3. **Webhook management UI** — register, test, and view delivery history without using the admin API directly.
4. **Threshold configuration UI** — adjust per-client governance sensitivity (ADR-037) without contacting OMNIX support.
5. **SDK download links** — direct download of the Python and Node.js SDKs with their client-specific API key pre-configured.

## Decision

Rebuild `ClientDashboard.tsx` as a full self-service portal:

### API endpoints added

| Endpoint | Purpose |
|---|---|
| `GET /api/governance/client/quota` | Real-time quota and burn rate |
| `GET /api/governance/client/analytics` | Per-domain breakdown (last 30 days) |
| `GET /api/governance/client/webhooks` | List registered webhooks |
| `POST /api/governance/client/webhooks/test` | Fire a test webhook event |
| `GET /api/governance/client/thresholds` | Current threshold configuration |
| `PATCH /api/governance/client/thresholds` | Update thresholds (within tier limits) |

### Quota burn rate visualization

```
Daily quota: 1,000 calls
Used today: 743 calls (74.3%)
Burn rate: 93 calls/hour → projected to hit limit at 16:42 UTC
```

## Consequences

**Positive:**
- Enterprise clients are self-sufficient; reduces OMNIX support burden.
- Threshold self-service reduces onboarding friction from 2 business days to minutes.

**Negative:**
- PATCH /thresholds requires careful authorization — clients must only modify their own thresholds.

## Related

- ADR-037: Per-Client Configurable Thresholds
- ADR-062: Premium Features (v1)
- ADR-081: Per-Client Quota Enforcement
- ADR-087: Webhook Delivery Hardening
