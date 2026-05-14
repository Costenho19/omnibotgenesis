# GitHub Release v1.1.0 — Texto completo listo para pegar

**Tag:** `v1.1.0`
**Target:** `main` → commit `59c740db`
**Title:** `v1.1.0 — Runtime Governance Continuity: The ATF Protocol Stack is Complete`

---

## BODY (pegar exactamente en GitHub)

---

```markdown
# v1.1.0 — Runtime Governance Continuity

## The problem nobody has solved yet

Every major AI agent framework — LangChain, AutoGen, CrewAI, Semantic Kernel —
answers the same governance question: *"does this agent have permission?"*

That question is answered at the moment of admission. Then execution begins.

A 90-minute multi-agent workflow admitted at T₀ with valid authority
can have completely different authority characteristics at T₀+47min
due to: temporal expiry, budget exhaustion across concurrent sub-agents,
scope drift beyond original authorization, and anomaly accumulation
on the delegation chain.

No framework detects this. No framework acts on it. The audit record
— if one exists — is retrospective.

**This release ships the runtime governance layer that closes that gap.**

---

## What shipped

### The complete ATF protocol stack (L1–L4)

```
L1  Agent Identity Record (AIR)
L2  Delegation Receipt (DR)            ← RFC-ATF-1 (published, DOI: 10.5281/zenodo.20155016)
L3  Temporal Admissibility Record (TAR)
L3  Domain Translation Receipt (DTR)
L4  Runtime Continuity Record (RCR)   ← RFC-ATF-2 (this release)
```

Every layer is cryptographically anchored to the one below it.
The chain from a Tier-1 human decision to a runtime sub-agent execution
is unbroken, PQC-signed, and independently verifiable.

---

### RFC-ATF-2: Runtime Governance Continuity

`docs/standards/RFC-ATF-2.md`

24-section IETF-style extension to RFC-ATF-1. 8 new formally
model-checkable invariants. 9 new API endpoints.

The core problem it formalizes: **the Runtime Governance Gap** —
the structural distance between boundary attestation (what TAR does)
and continuous governability supervision (what nothing did before).

---

### Runtime Continuity Record (RCR) — `omnix_core/agents/atf/runtime_continuity.py`

**1,385 lines.** The engine that makes continuous governance operational.

Every long-running execution produces a chain of RCRs:

```
ATFRCR-A3F1D7E2B9C04521  →  ATFRCR-8B2E90F1C3D74A16  →  ATFRCR-...
     T₀+0s                       T₀+30s                      T₀+60s
```

Each RCR carries a **Continuity Eligibility Score**:

```python
CES = (T × 0.30) + (B × 0.30) + (D × 0.20) + (I × 0.20)

# T — Temporal health:    fraction of DR lifetime remaining
# B — Budget health:      authority budget unconsumed across chain
# D — Context fidelity:   drift from original scope authorization
# I — Integrity signal:   anomaly-adjusted chain health
```

Five CES thresholds drive automatic state transitions:

```python
CES_NOMINAL     = 75.0   # continue, standard sampling
CES_MONITORING  = 50.0   # continue, increased sampling, flag outputs
CES_WARNING     = 25.0   # restrict sub-task spawning, Tier-1 alert
CES_CRITICAL    = 10.0   # suspend spawning, issue Reauthorization Challenge
CES_HALT        = 0.0    # terminate execution, revoke in-flight sub-tasks
```

---

### Authority Fragmentation Guard (AFG) — `RGC-INV-004`

This is the attack vector nobody talks about.

An agent with `authority_budget_granted = 90` can spawn 15 concurrent
sub-agents, each receiving a valid sub-delegation of 60. Every individual
grant satisfies the Monotonic Authority Reduction invariant. Aggregate
consumed: **900**. The chain root budget was 90.

Individual-level MAR cannot catch this. **AFG operates at chain root level:**

```python
AuthorityFragmentationViolation  # raised when:
# Σ budget_at_admission (all ACTIVE sessions on chain_root_id)
# exceeds chain_root_budget × AFG_FRAGMENTATION_LIMIT
```

Default `AFG_FRAGMENTATION_LIMIT = 0.90`. Values above 1.0 rejected.
10% of chain root budget is permanently reserved — it cannot be delegated.

---

### Reauthorization Challenge (RC) — `ATFRC-{16HEX}`

At CRITICAL threshold, execution does not halt immediately.
The engine issues a formal **Reauthorization Challenge**:

- Signed with ML-DSA-65 (Dilithium-3, FIPS 204)
- Delivered to the Tier-1 authority that opened the chain
- TTL: 300 seconds to respond with a new short-lifetime DR
- On TTL expiry without response: **automatic HALT**

```python
RC_TTL_CRITICAL_DEFAULT = 300  # seconds
RC_TTL_HALT_DEFAULT     = 0    # immediate — no TTL at HALT
```

This closes the gap between "authority is degrading" and "execution stops."

---

### Temporal Authority — `omnix_core/agents/atf/temporal_authority.py`

**580 lines.** Nanosecond-precise proof that a DR was valid at the exact
moment of execution admission — not just "recently valid."

```
ATFTAR-{16HEX}  anchored to  ATFDR-{16HEX}  signed at  T₀ (nanosecond)
```

Every RCR in the continuity chain is anchored to its admission TAR.
The cryptographic evidence chain from human decision to runtime moment
is complete.

---

### Cross-Domain Trust Portability — `omnix_core/agents/atf/domain_bridge.py`

**571 lines.** Domain Translation Receipts for cross-boundary authority transfer.

```
ATFDTR-{16HEX}  —  signed proof that authority was legitimately
                    translated across a domain boundary with the
                    applicable discount schedule applied
```

---

### 82 tests. Real ones.

`tests/test_runtime_governance_continuity.py`

```
TestContinuityEligibilityScore   — CES formula, weights, thresholds
TestSessionLifecycle             — start, sample, stop, independence
TestRCRIssuance                  — ID format, hash, PQC signature, fields
TestContinuityChain              — linked list, acyclicity, ordering
TestCESTemporalComponent         — expiry math, edge cases
TestCESContextIntegrity          — drift scoring, anomaly weighting
```

Selected test that proves acyclicity holds:

```python
def test_chain_is_acyclic(self):
    # Samples are emitted in chronological order.
    # A chain with a backward execution_ns reference
    # raises on insertion — RGC-INV-006 enforced.
```

82 tests. 82 passing.

---

### Multi-Protocol ATF Verifier — `/atf-verify`

Rebuilt from single-artifact to full-stack.

Verifies **DR** (RFC-ATF-1 · L2), **TAR** (ADR-157 · L3),
and **RCR** (RFC-ATF-2 · L4) with:

- ATF stack layer indicator (L1→L4) showing where the artifact lives
- Animated CES gauge with threshold color transitions
- Four CES component bars (T / B / D / I) with real-time scores
- Continuity chain visualization with status-colored nodes
- Escalation alert panel showing active CEEs

No account required. Independent verification is a protocol invariant
(ATF-INV-006): any party with the receipt and the root public key
can verify without platform access.

---

### 14 invariants. Two formal standards.

| Invariant | Standard | Description |
|---|---|---|
| ATF-INV-001 | RFC-ATF-1 | Monotonic Authority Reduction (MAR) |
| ATF-INV-002 | RFC-ATF-1 | All DRs signed by delegating principal |
| ATF-INV-003 | RFC-ATF-1 | Chain root traceability to Tier-1 |
| ATF-INV-004 | RFC-ATF-1 | Budget ceiling: no grant exceeds 100.0 |
| ATF-INV-005 | RFC-ATF-1 | Receipt immutability |
| ATF-INV-006 | RFC-ATF-1 | Independent verifiability without platform |
| RGC-INV-001 | RFC-ATF-2 | Every RCR anchored to a valid TAR |
| RGC-INV-002 | RFC-ATF-2 | CES computed from real-time values only |
| RGC-INV-003 | RFC-ATF-2 | HALT terminates and revokes sub-tasks |
| RGC-INV-004 | RFC-ATF-2 | Aggregate budget never exceeds AFG limit |
| RGC-INV-005 | RFC-ATF-2 | All RCRs PQC-signed and immutable |
| RGC-INV-006 | RFC-ATF-2 | Continuity chain is acyclic and monotonic |
| RGC-INV-007 | RFC-ATF-2 | CES inputs must be fresh (staleness enforced) |
| RGC-INV-008 | RFC-ATF-2 | RC TTL enforced — auto-HALT on expiry |

MAR, acyclicity, immutability, and chain root consistency are proven
in TLA+ using the same formal methods methodology as AWS DynamoDB.

---

### Published standards

| Document | Status | Where |
|---|---|---|
| RFC-ATF-1 | **Published** | DOI: 10.5281/zenodo.20155016 · SSRN: 6757339 |
| RFC-ATF-2 | Draft | `docs/standards/RFC-ATF-2.md` |

---

### 30 API endpoints across the ATF stack

**L2 — Delegation & Identity**
```
POST  /api/atf/agents/register
GET   /api/atf/agents
GET   /api/atf/agents/<agent_id>
POST  /api/atf/delegate
GET   /api/atf/delegations/<agent_id>
POST  /api/atf/verify
GET   /api/atf/verify/<agent_id>
GET   /api/atf/lattice
GET   /api/atf/ccs/<agent_id>
POST  /api/atf/demo/simulate
```

**L3 — Temporal Admissibility**
```
POST  /api/atf/temporal/admit
GET   /api/atf/temporal/<tar_id>
POST  /api/atf/temporal/verify
GET   /api/atf/temporal/report/<agent_id>
```

**L3 — Cross-Domain Trust**
```
POST  /api/atf/translate
GET   /api/atf/translate/<dtr_id>
POST  /api/atf/translate/verify
GET   /api/atf/translate/policy
```

**L4 — Runtime Continuity** *(new in this release)*
```
POST  /api/atf/continuity/start
POST  /api/atf/continuity/sample
POST  /api/atf/continuity/stop
GET   /api/atf/continuity/<rcr_id>
GET   /api/atf/continuity/session/<tar_id>
GET   /api/atf/continuity/chain/<rcr_id>
POST  /api/atf/continuity/reauth
GET   /api/atf/escalations/<rcr_id>
GET   /api/atf/escalations/session/<tar_id>
```

---

### Upgrade notes

**No breaking changes** to RFC-ATF-1 artifacts (DR, AIR, Trust Lattice).

New DB tables (auto-created on first request):
```sql
atf_runtime_continuity      -- RCRs
atf_continuity_escalations  -- CEEs
atf_temporal_records        -- TARs
atf_domain_bridges          -- DTRs
```

New optional environment variables:
```
RGC_SAMPLE_INTERVAL_SECONDS   — continuity sampling frequency
AFG_FRAGMENTATION_LIMIT       — default 0.90, max 0.95
RC_TTL_CRITICAL_SECONDS       — default 300
```

---

### Compliance surface

EU AI Act Art. 9, 13 · DORA Art. 9 · MiCA Recital 65 ·
SOC 2 CC6.1 · ISO 27001 A.9.4 · NIST AI RMF Govern 1.4/Manage 2.2

---

**OMNIX QUANTUM LTD** · Harold Nunes (Founder)
`docs/standards/` · `omnix_core/agents/atf/`
```

---

## Pasos en GitHub

1. Ir a `https://github.com/Costenho19/omnibotgenesis/releases/new`
2. **Choose a tag:** escribir `v1.1.0` → Create new tag
3. **Target:** `main`
4. **Release title:** `v1.1.0 — Runtime Governance Continuity: The ATF Protocol Stack is Complete`
5. Pegar el body de arriba (todo lo que está dentro del bloque de código markdown)
6. Adjuntar opcionalmente: PDF de RFC-ATF-2
7. ✅ Set as the latest release
8. **Publish release**
