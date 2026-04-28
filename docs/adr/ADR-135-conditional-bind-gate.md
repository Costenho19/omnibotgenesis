# ADR-135 — Conditional Bind Gate (CBG)

**Status:** ACCEPTED (v1.0)
**Date:** 2026-04-28
**Author:** OMNIX Quantum Ltd — Harold Alberto Nunes Rodelo
**Scope:** `omnix_core/governance/conditional_bind_gate.py` · `omnix_web/api/server.py`

---

## Changelog

| Version | Date | Summary |
|---|---|---|
| v1.0 | 2026-04-28 | Initial implementation — ConditionalBindGate, 4 gate states, 35 tests, API endpoints |

---

## 1. Context and Problem Statement

ADR-133 (State Provenance Guard) answers Eduardo Monteiro's pre-bind formation question:

> *"Can this state be explained by more than one plausible lineage before consequence is bound to it?"*

The SPG surfaces lineage ambiguity as **advisory** — the evaluation proceeds to bind
regardless of the verdict. Eduardo identified the remaining gap:

> *"Detection alone exposes the condition — but doesn't necessarily change the outcome."*
>
> *"Once ambiguity is detected, how (or whether) the system resolves it before consequence is allowed."*

ADR-135 closes this gap.

When SPG returns `AMBIGUOUS` verdict above a configurable severity threshold, the
**Conditional Bind Gate** blocks the bind and requires explicit human attestation
before consequence is allowed to proceed. The human who approves bind despite the
detected ambiguity is cryptographically bound to the outcome — the accountability
gap that previously existed is eliminated.

---

## 2. Decision

Implement a **Conditional Bind Gate (CBG)** as Layer 0c in the OMNIX evaluation pipeline.

### Architecture position

```
ProposedRequest
    → SAE     (Layer 0)   — Structural Admissibility
    → SPG     (Layer 0b)  — State Provenance Guard        (ADR-133)
    → CBG     (Layer 0c)  — Conditional Bind Gate         ← THIS ADR
    → CAG     (Layer 1a)  — Context Admissibility Gate
    → CP-0…11 (Layer 1)   — 11-Checkpoint Pipeline
    → TIE     (Layer 2)   — Trajectory Invariant Engine
    → Receipt (Layer 3)   — PQC Evidence & Audit Trail    (ADR-130/131)
```

### 2.1 Design constraints

**Constraint 1: Fail-safe**
Any CBG engine exception returns `bind_allowed=True` with `gate_required=False`.
The gate layer itself must never become a failure point for governance decisions.
A malfunctioning CBG is worse than no CBG — silent gate failures silently block
real decisions.

**Constraint 2: Additive**
CBG does not modify `decision_receipts`, `governance_overrides`, or any existing table.
`bind_gate_records` is a standalone audit table. Zero regressions.

**Constraint 3: Idempotent**
`evaluate()` with the same `spg_id` returns the existing gate status without
creating a duplicate. Clients may safely retry.

**Constraint 4: Terminal attestation**
`BLOCKED` and `ATTESTED` are terminal states. They cannot be reversed.
A new evaluation is required to re-open the question.

**Constraint 5: Optional integration**
The CBG is additive and opt-in. Existing evaluation endpoints continue to function
with SPG ADVISORY mode. CBG integration is enabled explicitly by clients that
require full conditional bind enforcement.

---

## 3. Gate Lifecycle

```
evaluate() called with AMBIGUOUS SPG result
    ↓
Gate trigger threshold met?
    No  → PASS (bind allowed, no gate created)
    Yes → GATE_CREATED (bind blocked)
              ↓
         PENDING ──── attest() ──→ ATTESTED (bind allowed)
                 ╲─── block()  ──→ BLOCKED  (bind permanently rejected)
                 ╲─── timeout  ──→ EXPIRED  (auto-blocked)
```

### Gate trigger conditions (either is sufficient)

| Condition | Threshold | Rationale |
|---|---|---|
| `lineage_singularity` | < 50.0 | SPG AMBIGUOUS band (score < 50) |
| `contradiction_count` | ≥ 2 | Two or more internal signal contradictions |

Both conditions require `spg_verdict == "AMBIGUOUS"`. SINGULAR and INDETERMINATE
states always produce PASS without a gate.

**Why 50?** The SPG AMBIGUOUS band is 0–49. A score of exactly 49 means the system
is operating just below the threshold where one causal origin dominates. This is the
correct severity level for requiring explicit human attestation.

**Why 2 contradictions?** A single contradiction can be noise. Two or more internal
signal contradictions indicate systematic multi-source formation that cannot be
resolved by a single additional signal.

---

## 4. Configuration Constants

| Constant | Default | Description |
|---|---|---|
| `GATE_TIMEOUT_MINUTES` | 60 | PENDING gates auto-expire after this. Window is chosen to be operationally realistic (a human reviewer can respond within 1 hour) while preventing indefinitely-open gates from accumulating. |
| `ATTEST_MIN_JUSTIFICATION_CHARS` | 80 | Minimum attestation justification length. Stricter than OSE's 50 (ADR-124) — the attester is explicitly taking ownership of consequence over a detected provenance ambiguity. |
| `AMBIGUITY_SCORE_THRESHOLD` | 50.0 | lineage_singularity below this triggers gate |
| `AMBIGUITY_CONTRADICTION_THRESHOLD` | 2 | contradiction_count at or above this triggers gate |

---

## 5. Data Structures

### BindGateResult

Returned by `evaluate()`. Tells the caller whether bind is allowed immediately.

```json
{
  "gate_required":       true,
  "bind_allowed":        false,
  "verdict":             "GATE_CREATED",
  "reason":              "Lineage ambiguity gate created. lineage_singularity=28.0 contradictions=3. Bind is blocked until explicit attestation. Gate expires in 60 minutes.",
  "gate_id":             "CBG-A3F2B1C9D0E4F5A6",
  "lineage_singularity": 28.0,
  "contradiction_count": 3,
  "spg_verdict":         "AMBIGUOUS",
  "gate_record":         { ... },
  "adr_reference":       "ADR-135"
}
```

### BindGateRecord

Persisted in `bind_gate_records`. Full audit record of every gate and its resolution.

```json
{
  "gate_id":              "CBG-A3F2B1C9D0E4F5A6",
  "spg_id":               "SPG-A3F2B1C9",
  "decision_id":          "receipt-trading-001",
  "domain":               "trading",
  "lineage_singularity":  28.0,
  "contradiction_count":  3,
  "spg_verdict":          "AMBIGUOUS",
  "gate_status":          "ATTESTED",
  "bind_allowed":         true,
  "attester_id":          "harold@omnixquantum.net",
  "justification":        "Reviewed contradictions — market data confirms BULLISH formation despite cross-signal noise. Consequence approved.",
  "block_reason":         null,
  "created_at":           "2026-04-28T10:00:00+00:00",
  "expires_at":           "2026-04-28T11:00:00+00:00",
  "attested_at":          "2026-04-28T10:12:34+00:00",
  "blocked_at":           null,
  "oversight_session_id": null,
  "gate_hash":            "sha256:...",
  "adr_reference":        "ADR-135"
}
```

---

## 6. Database

### bind_gate_records

```sql
CREATE TABLE IF NOT EXISTS bind_gate_records (
    gate_id               VARCHAR(64)   PRIMARY KEY,
    spg_id                VARCHAR(64)   NOT NULL,
    decision_id           VARCHAR(128)  NOT NULL,
    domain                VARCHAR(64),
    lineage_singularity   FLOAT         NOT NULL,
    contradiction_count   INTEGER       NOT NULL DEFAULT 0,
    spg_verdict           VARCHAR(20)   NOT NULL,
    gate_status           VARCHAR(20)   NOT NULL DEFAULT 'PENDING',
    bind_allowed          BOOLEAN       NOT NULL DEFAULT FALSE,
    attester_id           VARCHAR(128),
    justification         TEXT,
    block_reason          TEXT,
    created_at            TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    expires_at            TIMESTAMPTZ   NOT NULL,
    attested_at           TIMESTAMPTZ,
    blocked_at            TIMESTAMPTZ,
    oversight_session_id  VARCHAR(64),
    gate_hash             VARCHAR(80)   NOT NULL,
    metadata              JSONB
);
```

### Indexes

| Index | Column(s) | Purpose |
|---|---|---|
| `idx_cbg_spg_id` | `spg_id` | Idempotency lookup — find existing gate by SPG evaluation |
| `idx_cbg_decision_id` | `decision_id` | Find all gates for a given decision |
| `idx_cbg_status` | `gate_status` | Filter by status for admin/expiry queries |
| `idx_cbg_expires_at` | `expires_at` | Efficient stale gate expiry |
| `idx_cbg_domain` | `domain` | Domain-scoped analytics |

---

## 7. API Endpoints

All endpoints require `X-API-Key` authentication (B2B RBAC — same as `/api/governance/*`).

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/governance/bind-gate/evaluate` | standard | Evaluate whether a gate is required for an SPG result |
| GET | `/api/governance/bind-gate/<gate_id>` | standard | Query current gate status |
| POST | `/api/governance/bind-gate/<gate_id>/attest` | standard | Attest bind — explicitly approve consequence |
| POST | `/api/governance/bind-gate/<gate_id>/block` | standard | Permanently block bind |
| POST | `/api/governance/bind-gate/expire` | **admin** | Expire stale PENDING gates |

### POST /api/governance/bind-gate/evaluate

Request body:
```json
{
  "spg_id":              "SPG-A3F2B1C9",
  "spg_verdict":         "AMBIGUOUS",
  "lineage_singularity": 28.0,
  "contradiction_count": 3,
  "decision_id":         "receipt-trading-001",
  "domain":              "trading"
}
```

Response (gate created):
```json
{
  "success": true,
  "bind_allowed": false,
  "gate_id": "CBG-A3F2B1C9D0E4F5A6",
  "verdict": "GATE_CREATED",
  "result": { ... },
  "adr": "ADR-135"
}
```

### POST /api/governance/bind-gate/<gate_id>/attest

Request body:
```json
{
  "attester_id":  "harold@omnixquantum.net",
  "justification": "Reviewed contradictions — market data confirms BULLISH formation despite cross-signal noise. Consequence approved by risk officer."
}
```

Response:
```json
{
  "success": true,
  "bind_allowed": true,
  "gate_status": "ATTESTED",
  "gate": { ... },
  "adr": "ADR-135"
}
```

---

## 8. Relationship to Other ADRs

### ADR-133 — State Provenance Guard (upstream)

CBG consumes the SPG result. SPG produces the `spg_id`, `spg_verdict`,
`lineage_singularity`, and `contradiction_count` that CBG evaluates.

```
SPGResult.verdict == "AMBIGUOUS" → CBG.evaluate() may create gate
SPGResult.verdict == "SINGULAR"  → CBG.evaluate() returns PASS immediately
```

### ADR-124 — Oversight Surface Engine (complementary)

OSE governs the quality of human oversight *moments*. CBG governs whether
bind is allowed to occur at all. They are complementary:
- CBG creates the gate and blocks bind
- OSE (if integrated) governs the deliberation quality of the attestation that releases the gate
- `oversight_session_id` in `BindGateRecord` stores the OSE session ID when linked

### ADR-130 — VC Trust & Revocation Registry (downstream)

When attestation is granted, the `attester_id` and `gate_id` become part of the
`humanSigner` block in the downstream VC receipt. The attester is cryptographically
bound to the consequence they allowed to proceed.

### ADR-116 — Fail-Closed Enforcement Policy

CBG is fail-open by design (engine errors → bind allowed). This is an intentional
deviation from ADR-116's fail-closed principle, justified by the constraint that
the gate layer itself must never become a governance bottleneck. The risk of a
malfunctioning gate silently blocking legitimate decisions exceeds the risk of a
malfunctioning gate silently allowing ambiguous ones — since ambiguous states still
pass through the full 11-checkpoint pipeline (Layers 1–3).

---

## 9. Compliance Checklist

| Requirement | Status |
|---|---|
| Fail-safe on engine error | ✅ Returns `bind_allowed=True`, gate not required |
| Zero modification of existing tables | ✅ New table only: `bind_gate_records` |
| Idempotent evaluate() | ✅ Returns existing gate if spg_id already processed |
| Justification required for attestation | ✅ ≥ 80 chars — stricter than OSE (50 chars) |
| Terminal state transitions | ✅ ATTESTED and BLOCKED cannot be reversed |
| Auto-expiry of stale gates | ✅ PENDING gates auto-expire at query/evaluate time |
| Full audit trail | ✅ Every state transition timestamped in bind_gate_records |
| Thread-safe | ✅ DB is source of truth; no shared mutable state |
| TESTING mode safe | ✅ No background threads; lazy DB imports |
| Regulatory alignment | ✅ EU AI Act Art. 14(4)(c), Art. 9; NIST AI RMF |
| Zero regressions | ✅ Additive — no existing endpoint modified |

---

## 10. Test Coverage

`tests/test_conditional_bind_gate.py` — 35 tests

| Group | Tests | Coverage |
|---|---|---|
| T01–T05 | Import, constants, enums, singleton | Module structure |
| T06–T10 | `evaluate()` PASS path | SINGULAR, INDETERMINATE, below-threshold AMBIGUOUS |
| T11–T15 | `evaluate()` GATE_CREATED | Score < 50, contradictions ≥ 2, reason text, to_dict() |
| T16–T20 | `evaluate()` idempotency | GATE_EXISTS, ATTESTED, BLOCKED, EXPIRED, auto-expire |
| T21–T25 | `attest()` validation | Justification length, gate not found, DB level |
| T26–T30 | `block()` / `query()` + reason text | All statuses |
| T31–T35 | Serialization + fail-safe | to_dict(), DB error → fail-safe, gate_hash determinism |

---

## 11. Files

| File | Role |
|---|---|
| `omnix_core/governance/conditional_bind_gate.py` | Core module |
| `tests/test_conditional_bind_gate.py` | 35-test suite |
| `docs/adr/ADR-135-conditional-bind-gate.md` | This document |
| `bind_gate_records` (DB table) | Persistent gate audit trail |
| `omnix_web/api/server.py` | 5 API endpoints |
