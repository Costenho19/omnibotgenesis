# ADR-147 — Scope Authorization Record: Defensible Scope Issuance & Context-Aware Reapproval

| Field | Value |
|---|---|
| **Status** | Accepted — Implemented May 2026 |
| **Date** | 2026-05-09 |
| **Author** | Harold Nunes — OMNIX QUANTUM LTD |
| **Scope** | `omnix_core/governance/scope_authorization_engine.py` (new) · `omnix_web/api/gov_blueprint.py` · `docs/AUTHORITY_MATRIX.md` |
| **Extends** | ADR-146 (Runtime Authority Matrix) · ADR-144 (Auto-Modification Guard) · ADR-064 (AVM) · ADR-022 (PQC) |
| **Replaces** | — |

---

## 1. Problem Statement

OMNIX's 11-checkpoint governance pipeline answers a precise question:

> *"Did the AI agent stay within its authorized scope during this decision?"*

The cryptographic receipt (Dilithium-3 signed, W3C Verifiable Credential compatible) proves the agent did not exceed the scope it was given. But it does not answer the next question — the one that Rehan Kausar (Chief AI Officer) articulated on May 9, 2026:

> *"The CAIO question is separate — was the scope itself defensible, who signed off on it, and how does it adapt as operational context shifts?"*

**Three structural gaps this ADR addresses:**

### 1.1 — No signed record of scope issuance

Before this ADR, governance scopes (checkpoint thresholds, permitted domains, per-client configuration) were set via API or configuration without a dedicated signed artifact proving:
- Who authorized this scope (authority tier + actor identity)
- Why this scope was considered defensible at the time (regulatory basis, risk assessment, business justification)
- What operational context existed when the scope was granted

A receipt proving "agent stayed within scope" is incomplete if there is no receipt proving "scope was legitimately issued."

### 1.2 — No mechanism for scope defensibility attestation

ISO 42001, EU AI Act Art. 9, and NIST AI RMF GV-1.1 require that the *basis* for governance parameters be documented and auditable — not just the parameters themselves. An auditor should be able to verify:

- The regulatory frameworks that justified the scope boundary
- The risk level accepted at authorization time
- Who at what authority tier reviewed and approved it
- Whether it has been superseded or is still active

### 1.3 — No formal reapproval flow when operational context shifts

The AVM detects when current conditions have drifted from calibration conditions. But there was no mechanism to detect when current conditions have drifted from the conditions that existed *when the scope was authorized*. These are different:

- AVM drift → re-calibrate the baseline
- Scope context drift → reauthorize the scope itself (who can do what, up to what limits)

When a financial services client's risk profile changes materially, their governance scope should require explicit reapproval — not silently continue under parameters set months earlier.

---

## 2. Decision

Implement a **Scope Authorization Record** system (`ScopeAuthorizationEngine`) that:

1. Issues a PQC-signed `ScopeAuthorizationRecord` whenever a governance scope is established or modified
2. Records the authority tier, actor, defensibility criteria, and operational context snapshot at authorization time
3. Integrates with the AVM to detect context drift between current conditions and scope-authorization conditions
4. Flags scope for formal reapproval when context drift exceeds a configurable threshold
5. Maintains a complete, immutable history of scope authorizations per domain

---

## 3. Architecture

```
omnix_core/governance/
└── scope_authorization_engine.py    — ScopeAuthorizationEngine + data classes

omnix_web/api/gov_blueprint.py       — 6 new API endpoints (scope namespace)

Database:
└── governance_scope_authorizations  — New table (see §4)
```

### 3.1 Data Flow

```
Operator / System
    │
    ▼
ScopeAuthorizationEngine.issue_scope(
    domain, vertical,
    scope_definition,          ← what is authorized
    defensibility_criteria,    ← why it is defensible
    authorized_by,             ← who authorized it
    authority_tier,            ← tier 1-4
    context_snapshot           ← AVM signals at authorization time
)
    │
    ├── SHA-256 hash of scope_definition + defensibility_criteria → scope_hash
    ├── SHA-256 hash of context_snapshot → context_hash
    ├── Dilithium-3 sign(scope_hash + context_hash) → pqc_signature
    └── Persist to governance_scope_authorizations
    │
    ▼
ScopeAuthorizationRecord (returned + stored)

Later, at each AVM evaluation:
    │
    ▼
ScopeAuthorizationEngine.check_context_drift(domain, vertical, current_signals)
    │
    ├── Load active scope's context_snapshot
    ├── Compute weighted drift against current AVM signals
    └── If drift > SCOPE_REAPPROVAL_DRIFT_THRESHOLD → flag_reapproval()
            │
            └── scope.status = REAPPROVAL_REQUIRED
                scope.reapproval_required = TRUE
                scope.reapproval_reason = drift detail
```

### 3.2 Scope Status Lifecycle

```
ACTIVE → REAPPROVAL_REQUIRED → ACTIVE (after reauthorize)
ACTIVE → SUPERSEDED (when replaced by new scope)
ACTIVE → REVOKED (Tier 1 manual only)
```

---

## 4. Database Schema

```sql
CREATE TABLE governance_scope_authorizations (
    scope_id                   VARCHAR(64)   PRIMARY KEY,
    domain                     VARCHAR(64)   NOT NULL,
    vertical                   VARCHAR(64)   NOT NULL DEFAULT 'general',
    authority_tier             INTEGER       NOT NULL CHECK (authority_tier BETWEEN 1 AND 4),
    authorized_by              VARCHAR(128)  NOT NULL,
    scope_definition           JSONB         NOT NULL,
    defensibility_criteria     JSONB         NOT NULL DEFAULT '{}',
    context_snapshot           JSONB         NOT NULL DEFAULT '{}',
    context_hash               VARCHAR(64)   NOT NULL,
    scope_hash                 VARCHAR(64)   NOT NULL,
    pqc_signature              TEXT          DEFAULT NULL,
    pqc_algorithm              VARCHAR(32)   DEFAULT NULL,
    status                     VARCHAR(32)   NOT NULL DEFAULT 'ACTIVE',
    issued_at                  TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    expires_at                 TIMESTAMPTZ   DEFAULT NULL,
    superseded_by              VARCHAR(64)   DEFAULT NULL,
    reapproval_required        BOOLEAN       NOT NULL DEFAULT FALSE,
    reapproval_required_at     TIMESTAMPTZ   DEFAULT NULL,
    reapproval_reason          TEXT          DEFAULT NULL,
    context_drift_at_reapproval FLOAT        DEFAULT NULL,
    avm_snapshot_id            VARCHAR(32)   DEFAULT NULL,
    avm_snapshot_version       INTEGER       DEFAULT NULL
);
```

---

## 5. `scope_definition` Schema

```json
{
  "permitted_domains": ["FINANCE", "HEALTHCARE"],
  "permitted_verticals": ["equity_trading", "credit_scoring"],
  "max_risk_exposure": 0.75,
  "max_position_size_usd": 1000000,
  "permitted_checkpoints": ["CP-1", "CP-2", "CP-3", "CP-9"],
  "blocked_actions": ["WIRE_TRANSFER_INTERNATIONAL"],
  "evaluation_frequency_minutes": 5,
  "custom_thresholds": {
    "probability_score": 0.65,
    "signal_coherence": 0.70
  }
}
```

---

## 6. `defensibility_criteria` Schema

```json
{
  "regulatory_basis": ["ISO 42001 §6.1", "EU AI Act Art. 9", "NIST AI RMF GV-1.1"],
  "risk_level_accepted": "MEDIUM",
  "business_justification": "Equity trading vertical within CBUAE-regulated limits",
  "reviewed_by": "Risk Committee — Q2 2026",
  "review_reference": "RC-2026-Q2-007",
  "next_review_due": "2026-08-09",
  "scope_reapproval_drift_threshold": 25.0
}
```

---

## 7. Authority Matrix — Scope Actions

| Action | Tier 1 (Human) | Tier 2 (System) | Tier 3 (Client) | Tier 4 (Auditor) |
|---|---|---|---|---|
| Issue scope authorization | ✅ **Only Tier 1** | ❌ | ❌ | ❌ |
| Flag scope for reapproval | ✅ Any time | ✅ Auto (context drift) | ❌ | ❌ |
| Reauthorize scope (after reapproval) | ✅ **Only Tier 1** | ❌ | ❌ | ❌ |
| Revoke scope | ✅ **Only Tier 1** | ❌ | ❌ | ❌ |
| Read active scope | ✅ | ✅ | ✅ Own domain | ✅ |
| Read scope history | ✅ | ✅ | ❌ | ✅ |
| Verify scope signature | ✅ | ✅ | ✅ | ✅ **Public** |

---

## 8. API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/governance/scope/authorize` | Admin | Issue new scope authorization |
| `GET` | `/api/governance/scope/<domain>/active` | API key | Get active scope for domain |
| `GET` | `/api/governance/scope/<domain>/history` | Admin | Full scope authorization history |
| `POST` | `/api/governance/scope/<scope_id>/reauthorize` | Admin | Create new scope superseding old |
| `POST` | `/api/governance/scope/<scope_id>/revoke` | Admin | Revoke active scope |
| `GET` | `/api/governance/scope/<scope_id>/drift` | API key | Check context drift for active scope |

---

## 9. Context Drift Detection

Context drift is computed as the weighted Euclidean distance between current AVM signals and the AVM signals captured in the scope's `context_snapshot` at authorization time, using the canonical AVM signal weights (ADR-076):

```
drift_pct = Σ (weight_i × |current_i − snapshot_i| / max(snapshot_i, 0.01)) × 100
```

When `drift_pct > defensibility_criteria.scope_reapproval_drift_threshold` (default 25%):
- Scope status → `REAPPROVAL_REQUIRED`
- `reapproval_required_at` stamped
- `reapproval_reason` populated with per-signal drift detail
- Existing governance decisions continue under current scope (no retroactive change)
- New scope evaluations are flagged with `trust_flags.scope_reapproval_pending = true`

---

## 10. Immutability Guarantees

| Property | Modifiable | Reason |
|---|---|---|
| Issued scope records | ❌ **Immutable** | PQC-signed at issuance |
| `scope_hash` | ❌ | Tamper-evident |
| `context_hash` | ❌ | Tamper-evident |
| `pqc_signature` | ❌ | Dilithium-3 signed |
| `superseded_by` pointer | ✅ Set once on supersession | Append-only |

---

## 11. Regulatory Alignment

| Framework | Requirement | This ADR |
|---|---|---|
| ISO 42001 §6.1 | Actions to address AI risks — documented basis | `defensibility_criteria` field |
| ISO 42001 §8.4 | AI system lifecycle — scope documentation | Scope record with full lifecycle |
| EU AI Act Art. 9 | Risk management — human oversight | Tier 1-only scope issuance + reapproval |
| EU AI Act Art. 14 | Human control — scope adaptation | Context drift → forced reapproval |
| NIST AI RMF GV-1.1 | AI governance policies documented | Signed scope record as governance artifact |
| NIST AI RMF MS-2.5 | Context monitoring | AVM-integrated drift detection |

---

## 12. Related

| Document | Relation |
|---|---|
| `docs/AUTHORITY_MATRIX.md` | Extended with §2.7 Scope Authorization Actions |
| ADR-146 — Runtime Authority Matrix | Parent authority framework |
| ADR-144 — Auto-Modification Guard | Pattern reference for signed modification receipts |
| ADR-064 — Assumption Validity Monitor | Context snapshot source + drift computation |
| ADR-022 — PQC Cryptography | Dilithium-3 signing of scope records |
| ADR-089 — RBAC | Tier 3 client scope access control |
