# ADR-158: Cross-Domain Trust Portability

**Status:** Accepted  
**Date:** May 12, 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Supersedes:** None  
**Related:** ADR-156 (Agent Trust Fabric), ADR-157 (Temporal Authority)

---

## Context

ADR-156 established domain-scoped agent identities and delegation chains.
An agent registered in the FINANCE domain has an AID-FINANCE-... identifier
and holds authority specifically within that domain.

Enterprise AI systems, however, are increasingly **cross-domain**. Consider:

- A healthcare AI that needs to access financial claims data to process
  insurance reimbursements
- A financial risk agent that needs to consult energy market data
- A defense autonomous system that requires medical protocol authorization
  for medical logistics decisions

Under ADR-156, these scenarios have no governed path. The agent either:
a) Acts without authorization in the target domain (untraceable), or
b) Requires a full new registration and delegation chain in the target domain
   (impractical for ephemeral cross-domain tasks)

This creates an accountability gap exactly at domain boundaries — precisely
where regulatory scrutiny is highest (e.g., cross-sector data sharing under
DORA and GDPR, MiCA cross-asset governance).

ADR-158 closes this gap by defining the **Domain Translation Receipt (DTR)**
— a PQC-signed proof that authority from one governance domain was explicitly
translated and scoped for use in another domain, subject to a defined discount
policy that ensures authority only decreases across domain boundaries.

---

## Decision

### Domain Translation Receipt (DTR)

When an agent with authority in domain A needs to act in domain B, the
`CrossDomainBridge` issues a **DTR** that:

1. References the source Delegation Receipt (from domain A)
2. Declares the target domain, target agent AID, and target task scope
3. Applies a **translation discount** — reducing the authority budget by a
   domain-pair-specific percentage (minimum 15%, default 20%)
4. Is PQC-signed by the platform key (Dilithium-3)
5. Remains immutable once issued

### DTR Identifier

Format: `ATFDTR-{16HEX}`  
Example: `ATFDTR-A1B2C3D4E5F6A7B8`

### Translation Discount Policies

The authority budget is reduced by a domain-pair-specific discount:

| Source Domain | Target Domain | Discount | Rationale |
|---|---|---|---|
| HEALTHCARE | INSURANCE | 15% | Adjacent domains, high overlap |
| HEALTHCARE | FINANCE | 30% | Significant domain shift |
| FINANCE | INSURANCE | 15% | Adjacent domains |
| FINANCE | ENERGY | 25% | Moderate domain shift |
| FINANCE | DEFENSE | 50% | High-risk domain shift |
| DEFENSE | HEALTHCARE | 40% | Significant domain shift |
| ENERGY | FINANCE | 20% | Standard default |
| INSURANCE | HEALTHCARE | 15% | Adjacent domains |
| Any → Any | (default) | 20% | Conservative default |

The translated budget formula:

```
translated_budget = source_budget × (1 - discount)
```

**CDTP-INV-001:** translated_budget MUST be ≤ source_budget × (1 - discount).
This is enforced before any signing or persistence occurs.

### Example

A FINANCE agent with authority_budget=80 translates to HEALTHCARE domain:

```
source_budget    = 80.0
discount         = 0.30  (FINANCE→HEALTHCARE policy)
translated_budget = 80.0 × 0.70 = 56.0
```

The resulting DTR in HEALTHCARE has translated_budget=56.0 — the agent has
less authority in the target domain than it had in its home domain.

### Invariants

| ID | Invariant | Enforcement |
|---|---|---|
| CDTP-INV-001 | translated_budget ≤ source × (1 - discount) | Enforced before DTR issuance |
| CDTP-INV-002 | All DTRs are PQC-signed | Dilithium-3 over content_hash |
| CDTP-INV-003 | DTR embeds source_delegation_id | Field required, not nullable |
| CDTP-INV-004 | DTRs are domain-scoped | target_domain is immutable |
| CDTP-INV-005 | DTRs are immutable once issued | No UPDATE path in DDL |
| CDTP-INV-006 | Same-domain translation is rejected | Bridge checks src == tgt |

---

## DTR Fields

| Field | Type | Description |
|---|---|---|
| `dtr_id` | string | `ATFDTR-{16HEX}` |
| `source_delegation_id` | string | Source DR reference |
| `source_domain` | string | Origin governance domain |
| `target_domain` | string | Target governance domain |
| `source_agent_id` | string | AID in source domain |
| `target_agent_id` | string | AID in target domain |
| `source_authority_budget` | float | Authority in source domain |
| `translated_budget` | float | Authority granted in target domain |
| `translation_discount` | float | Discount rate applied (0.0-1.0) |
| `translation_policy` | string | Policy identifier |
| `task_scope` | object | Authorized scope in target domain |
| `chain_root_id` | string | chain_root_id of source DR |
| `content_hash` | string | SHA-256 of all fields except sig |
| `pqc_signature` | string? | Dilithium-3 sig |
| `pqc_algorithm` | string? | `"dilithium3"` |
| `status` | string | `ACTIVE` \| `REVOKED` \| `EXPIRED` |
| `expires_at` | string? | Max = source DR expiry |
| `issued_at` | string | ISO UTC timestamp |
| `issued_by` | string | AID or system issuing the DTR |
| `metadata` | object | Extension dict |

---

## Full Trust Chain with DTR

```
Human Tier-1 (FINANCE)
    │  Delegation Receipt (ATFDR-...)
    ▼
FINANCE Agent (AID-FINANCE-...)  [authority_budget=80]
    │  Domain Translation Receipt (ATFDTR-...)
    │  source_domain=FINANCE, target_domain=HEALTHCARE
    │  discount=30%, translated_budget=56.0
    ▼
HEALTHCARE Agent (AID-HEALTHCARE-...)  [authority_budget=56]
    │  (optional) Sub-delegation in HEALTHCARE domain
    ▼
HEALTHCARE Sub-Agent  [authority_budget ≤ 56]
```

Every step is cryptographically signed. The chain is verifiable from the
leaf HEALTHCARE agent back to the human Tier-1 operator, across domains,
by any party with the root public key.

---

## Database

Table: `atf_domain_bridges` — auto-created idempotently on first request.

Indices:
- `(source_delegation_id)` — all DTRs for a source DR
- `(target_agent_id, target_domain, status)` — active DTRs per agent
- `(source_domain, target_domain)` — cross-domain analytics

---

## API

New endpoints added to `agent_blueprint.py`:

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/atf/translate` | Issue a DTR |
| `GET` | `/api/atf/translate/<dtr_id>` | Get a DTR |
| `POST` | `/api/atf/translate/verify` | Verify a DTR |
| `GET` | `/api/atf/translate/policy` | Get discount for domain pair |

---

## Consequences

**Positive:**
- Enterprise cross-sector AI deployments become fully auditable
- Every cross-domain action traces to its human origin across domain boundaries
- Authority always decreases at domain crossings (CDTP-INV-001)
- Regulatory compliance for cross-sector operations (DORA, MiCA, GDPR)
- Enables "Interoperable AI Authority Infrastructure" — a new market category

**Negative:**
- Cross-domain coordination requires an additional DTR issuance step
- Policy table must be maintained as new domain pairs are added

**Mitigations:**
- DTR issuance is non-blocking for the calling agent
- Policy table defaults to 20% for any unspecified domain pair
- Custom policies can be injected via `discount_override` parameter

---

## Future Extensions

- **DTR Chains:** DTR → sub-DTR → sub-sub-DTR for multi-hop cross-domain
- **Domain Federation:** Two OMNIX instances sharing a trust anchor, enabling
  cross-organization cross-domain authority portability
- **Smart Contract DTRs:** On-chain DTR issuance for DeFi × TradFi governance
