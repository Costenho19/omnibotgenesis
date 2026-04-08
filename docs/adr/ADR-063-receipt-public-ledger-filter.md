# ADR-063 — Public Ledger Receipt Filter

| Field            | Value                                               |
|------------------|-----------------------------------------------------|
| **Status**       | Accepted                                            |
| **Date**         | 2026-04-07                                          |
| **Author**       | Harold Nunes — Eureka GCC Dubai 2026 Semifinalist   |
| **Scope**        | `omnix_dashboard/blueprints/verification.py`        |
|                  | `omnix_dashboard/templates/verify.html`             |
| **Linked ROAD**  | ROAD-008                                            |
| **Replaces**     | —                                                   |

---

## Context

The OMNIX Decision Governance Infrastructure maintains a public `/verify` page where investors,
auditors, and channel partners (e.g. Velos — Naimat Khan) can independently confirm governance
receipts using post-quantum cryptographic signatures (Dilithium-3 / ML-DSA-65).

The "Recent Governance Receipts" section on this page called `/api/verify/recent` and returned
**all** rows from `decision_receipts` with no filter. This exposed:

- **Unsigned receipts** — rows where `signature_algorithm = 'NONE'` (generated during
  unit-test runs and sandbox evaluations where PQC signing is disabled).
- **Invalid test assets** — rows where `asset` contains arbitrary strings such as
  `jdj-UNINTELLIGIBLE-SCENARIO`, produced by automated evaluation harnesses.

Any visitor — including a Series-A investor or auditor during due diligence — seeing these
entries would reasonably conclude that the governance ledger is unreliable.

---

## Decision

### Layer 1 — Database (source of truth)

Modify the SQL query in `/api/verify/recent` to include explicit predicates:

```sql
WHERE signature_algorithm IS NOT NULL
  AND signature_algorithm <> 'NONE'
  AND asset IS NOT NULL
  AND asset ~ '^[A-Z0-9]+/[A-Z]+$'
ORDER BY created_at DESC
LIMIT %s
```

**Rationale for each clause:**

| Clause | Purpose |
|--------|---------|
| `signature_algorithm IS NOT NULL` | NULL guard; deterministic predicate evaluation |
| `signature_algorithm <> 'NONE'` | Excludes unsigned/test receipts |
| `asset IS NOT NULL` | NULL guard; prevents regex match on NULL |
| `asset ~ '^[A-Z0-9]+/[A-Z]+$'` | Allows only canonical trading-pair format (e.g. `BTC/USD`, `XRP/USDT`); rejects garbage strings |

The response field `signed` is set to `True` unconditionally for all returned rows since the
WHERE clause already guarantees it.

### Layer 2 — Frontend (belt-and-suspenders)

Add a client-side filter in `loadRecent()` using the same invariants:

```javascript
const VALID_ASSET = /^[A-Z0-9]+\/[A-Z]+$/;
const receipts = (data.receipts || []).filter(r =>
    r.signed === true && VALID_ASSET.test(r.asset)
);
```

This provides a second line of defence against any future regression in the backend filter,
with zero cost at runtime.

---

## Consequences

### Positive
- Investors and auditors see only cryptographically signed receipts with valid production assets.
- Public ledger integrity is restored — the page now reflects the governance system's true
  production track record.
- Both filtering layers are self-documenting via code comments referencing this ADR.

### Neutral
- Test receipts and unsigned sandbox receipts remain in the database (not deleted). Individual
  lookup via `/api/verify/<receipt_id>` continues to work for any receipt ID.
- The "Recent" section may show fewer or zero rows if all historical entries are test data.
  This is acceptable; an empty-state message is displayed.

### Out of scope
- Domain-based allowlist (`trading / credit / insurance / robotics`). Deferred to a future
  ADR if a confirmed client use case requires it — the current regex covers all four domains.
- Physical deletion of test rows from `decision_receipts`.
- Changes to the public web app's `/verify` route (`omnix_web/src/pages/PublicDecisionVerify.tsx`),
  which does not display a "recent receipts" list.

---

## Alternatives Considered

| Alternative | Reason rejected |
|-------------|----------------|
| Delete test rows from DB | Breaks hash chain integrity; out of scope |
| Frontend-only filter | Single point of failure; server still leaks data to API consumers |
| Domain allowlist instead of regex | Risk of false negatives; robot/insurance assets validated separately |
| Per-row WARNING log on filter | Noisy; deferred to a metrics counter if volume warrants it |

---

## Acceptance Criteria

- [ ] `/api/verify/recent` returns 0 rows with `signed = false`
- [ ] `/api/verify/recent` returns 0 rows with `asset` containing non-alphanumeric/slash chars
- [ ] A valid signed receipt (e.g. `BTC/USD`, decision `APPROVED`) appears in the list
- [ ] Individual lookup `/api/verify/<receipt_id>` remains unaffected for any receipt ID
- [ ] "Recent Governance Receipts" section shows "PQC Signed" label for every visible row
