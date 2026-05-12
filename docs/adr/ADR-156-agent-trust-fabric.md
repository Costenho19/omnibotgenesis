# ADR-156 — Agent Trust Fabric (ATF)

**Status:** Accepted  
**Date:** May 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Tags:** agents, delegation, trust, pqc, authority, differentiator, protocol

---

## Context

OMNIX currently governs decisions along the **human → AI** axis: a human operator
or automated Tier-2 module triggers governance evaluation, OMNIX evaluates it
through an 11-checkpoint pipeline, and issues a PQC-signed receipt.

The enterprise AI landscape is evolving toward **AI → AI → AI** pipelines:
autonomous agents that spawn sub-agents, delegate sub-tasks, and execute
multi-step workflows across organisational and system boundaries — often without
any synchronous human in the loop.

This introduces a governance gap that no existing infrastructure addresses:

| Question | Current OMNIX (pre-ATF) | Industry average |
|---|---|---|
| Did this agent have authority to act? | ✅ Verified at intake | ❌ Implicit / policy-only |
| Who delegated authority to it? | ❌ Not tracked | ❌ Not tracked |
| Is there cryptographic proof of the full delegation chain? | ❌ | ❌ |
| Can a regulator verify the chain without platform access? | ❌ | ❌ |
| Was authority ever expanded mid-chain (a rogue step)? | ❌ | ❌ |
| What was the authority budget at the moment of action? | ❌ | ❌ |

The **Agent Trust Fabric (ATF)** closes this gap permanently. It extends OMNIX's
existing PQC receipt infrastructure to cover agent-to-agent delegation, producing
a cryptographically verifiable, independently auditable trust lattice for every
autonomous agent action.

### Why this is architecturally unique

Every existing agent framework (LangChain, AutoGPT, CrewAI, Microsoft AutoGen,
Semantic Kernel) delegates authority implicitly through environment variables,
API keys, or runtime role assignments. These are:

- Not signed by the delegator
- Not independently verifiable
- Not traceable back to a human origin
- Not enforceable as formal authority constraints

ATF makes delegation a **first-class cryptographic event** — as auditable as
the governance receipt itself.

---

## Decision

Implement the **Agent Trust Fabric** as a new module at `omnix_core/agents/atf/`
with three core components, one API blueprint, one React page, and a test suite.

### Core Concepts

#### 1. Agent Identity (AID)

Every AI agent that participates in an OMNIX-governed environment is registered
with a unique cryptographic identity:

```
AID-{DOMAIN}-{16HEX}     e.g. AID-FINANCE-A3F9C12B44E7001D
```

- A Dilithium-3 key pair is generated at registration.
- The agent's public key is its unforgeable trust anchor.
- Registration is signed by the registering authority's private key.
- Authority budget (0.0–100.0) is assigned at registration and can only
  decrease through delegation.
- The registration record is **immutable** — status transitions (ACTIVE →
  SUSPENDED → REVOKED) are append-only.

#### 2. Delegation Receipt (DR)

When an agent (or human Tier-1 operator) delegates a task to a sub-agent,
a **Delegation Receipt** is produced:

```
ATFDR-{16HEX}     e.g. ATFDR-7B2E094A1CF83D55
```

The DR contains:
- `delegator_id` — AID (or human operator ID) of the delegating party
- `delegate_id` — AID of the receiving agent
- `task_scope` — explicit description of what is authorized
- `authority_budget_delegator` — budget held by the delegator at time of delegation
- `authority_budget_granted` — budget granted to delegate (invariant: ≤ delegator's)
- `parent_delegation_id` — ID of the delegation that gave the delegator its authority
- `chain_root_id` — the originating delegation receipt (always traceable to Tier 1)
- `delegation_depth` — 0 = human origin, 1 = first agent, N = Nth level sub-agent
- `delegator_public_key` — embedded for self-contained independent verification
- `content_hash` — SHA-256 of all fields excluding signature
- `pqc_signature` — Dilithium-3 signature over content_hash using delegator's key

**Monotonic Authority Reduction (MAR) — Core Invariant:**

```
authority_budget_granted ≤ authority_budget_delegator
```

This is enforced at the protocol level, not policy level. Any delegation
attempt that violates MAR raises `AuthorityExpansionViolation` and is
rejected — no receipt is issued.

#### 3. Trust Lattice

The Trust Lattice is a **directed acyclic graph (DAG)** where:

- **Nodes** are Agent Identities (AIDs)
- **Edges** are Delegation Receipts (DRs)
- **Root** is always a human Tier-1 operator or a Tier-2 module acting
  under explicit Tier-1 authorization
- **Leaves** are the sub-agents currently executing tasks

The lattice guarantees:
- No cycles (delegation_depth strictly increases along every path)
- Full traceability from any leaf to the human root
- Authority budget monotonically decreases from root to leaf
- Any DR can be independently verified with only its own content
  (delegator_public_key is embedded)

#### 4. Agent Execution Binding

Every governance receipt produced by an agent action carries ATF metadata:

```json
{
  "atf": {
    "agent_id": "AID-FINANCE-A3F9C12B44E7001D",
    "delegation_id": "ATFDR-7B2E094A1CF83D55",
    "delegation_depth": 2,
    "authority_budget": 45.0,
    "chain_root_id": "ATFDR-ROOT-000000000001",
    "chain_verified": true
  }
}
```

This binds the governance decision irreversibly to the agent's delegation
context at the moment of action.

#### 5. Independent Verification Protocol

Given only a Delegation Receipt (no platform access required):

```
1. Extract content_hash — verify by recomputing SHA-256 over all fields
2. Extract delegator_public_key from the receipt itself
3. Verify pqc_signature(content_hash, delegator_public_key) → PASS/FAIL
4. Inspect authority_budget_granted ≤ authority_budget_delegator → MAR check
5. If parent_delegation_id is not None: obtain parent receipt and recurse
6. At root: delegation_depth == 0 AND parent_delegation_id is None
7. Emit VerificationResult with full chain path and authority budget trace
```

This is the same independent verifiability guarantee OMNIX provides for
governance receipts — now extended to the agent delegation layer.

---

## Architecture Position

```
┌─────────────────────────────────────────────────────────────────────┐
│                    OMNIX AGENT TRUST FABRIC                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  TIER 1 HUMAN OPERATOR  (authority_budget = 100.0)                  │
│       │                                                               │
│       │  DelegationReceipt [ATFDR-ROOT] depth=0                      │
│       ▼                                                               │
│  ORCHESTRATOR AGENT     (authority_budget = 80.0)                   │
│       │                                                               │
│       │  DelegationReceipt [ATFDR-L1] depth=1                        │
│       ├──────────────────────────────┐                               │
│       ▼                              ▼                                │
│  ANALYSIS AGENT (50.0)    EXECUTION AGENT (40.0)                    │
│       │                              │                               │
│       │  DelegationReceipt depth=2   │  DelegationReceipt depth=2   │
│       ▼                              ▼                                │
│  DATA AGENT (25.0)        WRITE AGENT (20.0)                        │
│                                      │                               │
│                         Each action → DecisionReceipt                │
│                                      +  ATF metadata embedded        │
│                                         (agent_id, delegation_id,    │
│                                          budget, chain_root_id)      │
│                                                                       │
│  INDEPENDENT VERIFICATION: any party can verify the full chain       │
│  from WRITE AGENT → EXECUTION AGENT → ORCHESTRATOR → HUMAN ROOT     │
│  using only the embedded delegation receipts — no platform access.  │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Implementation

| Component | Path | Purpose |
|---|---|---|
| Agent Identity Engine | `omnix_core/agents/atf/agent_identity.py` | Register/manage agent identities |
| Delegation Receipt Engine | `omnix_core/agents/atf/delegation_receipt.py` | Issue/verify delegation receipts |
| Trust Lattice | `omnix_core/agents/atf/trust_lattice.py` | DAG + chain verification |
| Flask API | `omnix_web/api/agent_blueprint.py` (extended) | REST endpoints |
| React Page | `omnix_web/src/pages/AgentTrustFabricPage.tsx` | `/agent-trust-fabric` |
| Tests | `tests/test_agent_trust_fabric.py` | ≥40 assertions |

### DB Tables

```sql
-- Agent Identity Registry
CREATE TABLE IF NOT EXISTS atf_agent_registry (
    agent_id            VARCHAR(64)   PRIMARY KEY,
    display_name        VARCHAR(128)  NOT NULL,
    domain              VARCHAR(64)   NOT NULL,
    vertical            VARCHAR(64)   NOT NULL DEFAULT 'general',
    authority_budget    FLOAT         NOT NULL CHECK (authority_budget BETWEEN 0 AND 100),
    registered_by       VARCHAR(128)  NOT NULL,
    registration_tier   INTEGER       NOT NULL CHECK (registration_tier BETWEEN 1 AND 4),
    public_key_b64      TEXT          NOT NULL,
    registration_hash   VARCHAR(64)   NOT NULL,
    pqc_signature       TEXT          DEFAULT NULL,
    pqc_algorithm       VARCHAR(32)   DEFAULT NULL,
    status              VARCHAR(16)   NOT NULL DEFAULT 'ACTIVE'
                                      CHECK (status IN ('ACTIVE','SUSPENDED','REVOKED')),
    capabilities        JSONB         NOT NULL DEFAULT '[]',
    registered_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    metadata            JSONB         NOT NULL DEFAULT '{}'
);

-- Delegation Receipt Store
CREATE TABLE IF NOT EXISTS atf_delegation_receipts (
    delegation_id               VARCHAR(64)   PRIMARY KEY,
    delegator_id                VARCHAR(128)  NOT NULL,
    delegate_id                 VARCHAR(64)   NOT NULL
                                REFERENCES atf_agent_registry(agent_id),
    task_scope                  JSONB         NOT NULL,
    authority_budget_delegator  FLOAT         NOT NULL,
    authority_budget_granted    FLOAT         NOT NULL,
    parent_delegation_id        VARCHAR(64)   DEFAULT NULL,
    chain_root_id               VARCHAR(64)   NOT NULL,
    delegation_depth            INTEGER       NOT NULL CHECK (delegation_depth >= 0),
    delegator_public_key        TEXT          NOT NULL,
    content_hash                VARCHAR(64)   NOT NULL,
    pqc_signature               TEXT          DEFAULT NULL,
    pqc_algorithm               VARCHAR(32)   DEFAULT NULL,
    expires_at                  TIMESTAMPTZ   DEFAULT NULL,
    status                      VARCHAR(16)   NOT NULL DEFAULT 'ACTIVE'
                                              CHECK (status IN ('ACTIVE','EXPIRED','REVOKED')),
    created_at                  TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    metadata                    JSONB         NOT NULL DEFAULT '{}'
);
```

---

## New Invariants

| ID | Invariant | Enforcement |
|---|---|---|
| ATF-INV-001 | Authority budget never expands through delegation | `AuthorityExpansionViolation` at protocol level |
| ATF-INV-002 | Every delegation receipt is PQC-signed by the delegator | Enforced at issuance; degraded mode uses SHA-256 |
| ATF-INV-003 | Every delegation chain traces to a root with depth=0 | `chain_root_id` + `delegation_depth` tracked at issuance |
| ATF-INV-004 | A delegator cannot grant authority it does not hold | Budget check at `create_delegation()` |
| ATF-INV-005 | Delegation receipts are immutable once issued | No UPDATE path on core fields |
| ATF-INV-006 | Independent verification requires no platform access | `delegator_public_key` embedded in every DR |

---

## Consequences

### Positive

- **Closes the AI→AI governance gap** — the only infrastructure in the
  market that cryptographically proves the full delegation chain behind
  every agent action.
- **Extends existing PQC trust anchor** — reuses Dilithium-3 key
  infrastructure already in production (ADR-085, ADR-078).
- **Independently verifiable** — a regulator with the leaf DR can
  reconstruct the full chain with zero platform dependency.
- **Monotonic Authority Reduction (MAR)** — formally prevents
  privilege escalation in agent chains, a critical attack vector
  in multi-agent systems.
- **Board-level accountability** — every automated action is traceable
  to a specific human authorization event, satisfying EU AI Act Art. 14
  human oversight requirements.
- **ATF as a protocol** — the data format is self-describing and
  implementation-agnostic. Third-party systems can issue ATF-compatible
  delegation receipts and integrate into the OMNIX trust lattice.

### Negative / Trade-offs

- Adds per-delegation PQC signing latency (~1-5ms per delegation event).
- In-memory TrustLattice is process-scoped; multi-process deployments
  must use DB-backed lattice reads. DB tables provide persistence.
- Agent private keys must be protected with the same rigor as
  OMNIX_SIGNING_SECRET_KEY_B64.

---

## Regulatory Alignment

| Framework | Requirement | ATF Implementation |
|---|---|---|
| EU AI Act Art. 14 | Human oversight of high-risk AI | Every chain traces to Tier-1 human root |
| EU AI Act Art. 9 | AI risk management | MAR invariant + delegation audit trail |
| NIST AI RMF GV-4.2 | AI accountability mechanisms | Full chain verifiability |
| OSFI E-23 | AI model governance | Agent authority documented at issuance |
| ISO/IEC 42001 §8.4 | AI system design | Trust lattice as formal governance artifact |

---

## Authority Matrix Update (ADR-146 extension)

| Action | Tier 1 | Tier 2 | Tier 3 | Tier 4 |
|---|---|---|---|---|
| Register new agent (budget ≤ 100) | ✅ | ✅ (≤ 80) | ❌ | ❌ |
| Create delegation receipt | ✅ | ✅ (own budget only) | ✅ (own budget only) | ❌ |
| Revoke delegation | ✅ Any | ✅ Own delegations | ❌ | ❌ |
| Revoke agent (hard) | ✅ Only Tier 1 | ❌ | ❌ | ❌ |
| Verify any delegation chain | ✅ | ✅ | ✅ | ✅ Public |
| Read trust lattice state | ✅ | ✅ | ✅ Own agents | ✅ Public |

---

## Invariant Impact

| Existing Invariant | Impact |
|---|---|
| INV-001 (Fail-Closed) | ATF rejects invalid delegations at protocol level — fail-closed |
| INV-002 (Receipt per Decision) | Agent actions produce receipts with ATF binding — extended |
| INV-006 (Transparency Chain) | Delegation receipts append to chain — extended |
| ATF-INV-001 through ATF-INV-006 | New invariants defined above |

---

## Pointers

- Implementation: `omnix_core/agents/atf/`
- API: `omnix_web/api/agent_blueprint.py` (ATF section)
- Page: `/agent-trust-fabric`
- Tests: `tests/test_agent_trust_fabric.py`

---

*OMNIX-ATF-001 | ADR-156 | May 2026*
