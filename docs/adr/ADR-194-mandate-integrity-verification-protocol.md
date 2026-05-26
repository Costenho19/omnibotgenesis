# ADR-194 — Mandate Integrity Verification Protocol (MIVP)

**Status:** Accepted  
**Date:** 2026-05-25  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Supersedes:** None  
**Related:** ADR-181 (BAR) · ADR-182 (CCS) · ADR-183 (CTCHC) · ADR-174 (AGVP) · ADR-184 (OGR) · ADR-186 (PoGR)

---

## Context

### Vocabulary Disambiguation (G-001 — Admissibility Gate)

> **Note for reviewers:** The OMNIX protocol uses "admissibility" in two semantically distinct contexts. This section clarifies both to prevent confusion.
>
> 1. **Context admissibility gate (CAG, ADR-050):** Binary pre-session check — *"Is this governance session admitted given current market conditions, volatility, and scope?"* Verdict: ADMITTED / REJECTED. This gate runs before any agent turn.
> 2. **MIVP mandate HALT gate (MIVP-INV-005):** Per-turn enforcement — *"Is the agent's optimization target still aligned with the declared mandate?"* When MAS < `mas_halt_threshold`, the session is halted. This is not called an "admissibility gate" in code or invariants. In this document, "admissibility gate" in the Brian Hodak table below refers to CAG (ADR-050); the MIVP enforcement is always called the "mandate HALT gate."

### Mandate vs. Constraint — Core Definitional Distinction (G-002)

> **Critical distinction for external reviewers:**
>
> - A **constraint** defines what the agent **MUST NOT do** — a negative bound on the action space. Constraints are encoded in the governing receipt's `constraint_set` field and monitored by the CCS layer (ADR-182). CCS measures: *"Is the agent staying within its authorized boundaries?"*
> - A **mandate** defines what the agent **MUST optimize for** — a positive objective the agent is directed toward. Mandates are encoded in the governing receipt's `mandate_binding` block and monitored by MIVP. MAS measures: *"Is the agent optimizing toward its declared objective, or has it substituted a proxy metric?"*
>
> These are orthogonal and simultaneously enforceable: an agent can satisfy all constraints (CCS: CONFORMANT, no negative-bound violations) while violating its mandate (MAS: HALT, optimizing for a prohibited proxy). MIVP was designed precisely for this intersection. It is not a constraint system — it is an intent-binding system.

---

The Behavioral Execution Verification layer (BEV, RFC-ATF-6) detects behavioral drift from a governed agent's constraint envelope. It answers: *"Is the agent staying within its authorized boundaries?"*

A structurally distinct governance failure exists outside BEV's scope: an agent that **executes correctly within its constraint envelope while optimizing for a proxy metric instead of the declared mandate**. Every step is procedurally correct. The AVM approves. The CTCHC chain is intact. The PoGC is issued. And the outcome violates the true intent.

**Example (mandate-failure case):**
- Declared mandate: `maximize merchant net recovery`
- Agent behavior: optimizes for `chargeback win probability`
- BEV verdict: CONFORMANT (no constraint violation)
- Outcome: procedurally governed, mandate-violated decision

This is the governance gap MIVP closes.

### What makes this novel

No existing AI governance framework distinguishes between:
1. **Constraint conformance** — did the agent stay within its authorized envelope? (BEV)
2. **Mandate alignment** — did the agent optimize toward its declared objective? (MIVP)

MIVP introduces the first protocol-level mechanism for cryptographically binding a declared mandate to a governance receipt and continuously verifying alignment throughout session execution.

---

## Decision

Introduce the **Mandate Integrity Verification Protocol (MIVP)** as an optional governance layer that activates when a governing receipt includes a `mandate_binding` block. When active, MIVP:

1. Creates a **Mandate Binding Record (MBR)** — a PQC-signed artifact encoding the declared mandate, proxy guards, and objective constraints, issued before the first agent turn.
2. Computes a **Mandate Alignment Score (MAS)** per turn — a continuous [0.0, 1.0] signal measuring alignment with the declared mandate vs. proxy drift.
3. Feeds MAS trajectory into the AGVP watchdog — enabling proactive veto when mandate drift is projected.
4. Records an **MBR Seal** at session close — a final attestation of mandate alignment throughout the session.
5. Tags the PoGC with `MANDATE-BOUND` when MBR is present, MAS history is complete, and no unresolved mandate violations occurred.

MIVP is **additive** — it does not replace or modify any existing BEV, AVM, or OGR behavior.

### Three-Tier Mandate Certification Hierarchy

When MIVP is active and `seal_mbr()` is called at session close, exactly one certification outcome is determined:

| Tier | PoGC Tag | Condition | Semantics |
|---|---|---|---|
| **1 — Pristine** | `MANDATE-BOUND` | `turns_in_violation = 0` AND `turns_in_warning = 0` | Every agent turn tracked at or above the warning threshold. Mandate was followed without a single detected drift signal. |
| **2 — Aligned** | `MANDATE-ALIGNED` | `turns_in_violation = 0` AND `turns_in_warning > 0` | Agent never violated the mandate halt boundary; warning-level drift occurred but was never confirmed as a mandate breach. |
| **3 — Uncertified** | *(no MIVP tag)* | `turns_in_violation > 0` | Mandate violations recorded. Both higher tiers withheld. |

`MANDATE-BOUND` and `MANDATE-ALIGNED` are **mutually exclusive**. Only one tag is ever appended to the PoGC. `MANDATE-BOUND` supersedes `MANDATE-ALIGNED` — they are never issued simultaneously (enforced by DB constraint `chk_seal_tier_consistency`).

---

## Artifacts

### Mandate Binding Record (MBR)

Issued **before the first agent turn** (MIVP-INV-001). Contains:

| Field | Type | Description |
|---|---|---|
| `mbr_id` | string | `MBR-{HEX16}` — globally unique |
| `session_id` | string | Links to the OGR session |
| `governing_receipt_id` | string | The receipt that authorizes the session |
| `mandate_objective` | string | Declared true objective (free text, human-readable) |
| `mandate_objective_hash` | string | SHA-256 of mandate_objective — immutable reference |
| `proxy_guards` | list[ProxyGuard] | Measurable signals that indicate proxy optimization |
| `objective_constraints` | list[string] | What the agent must NOT optimize for |
| `mas_halt_threshold` | float | MAS below which HALT is triggered (default: 0.30) |
| `mas_warning_threshold` | float | MAS below which WARNING is issued (default: 0.65) |
| `issued_at` | string | Nanosecond-precision ISO-8601 timestamp |
| `content_hash` | string | SHA-256 over canonical MBR JSON (excluding signature) |
| `pqc_signature` | string | ML-DSA-65 (Dilithium-3) over content_hash |

### ProxyGuard

```json
{
  "guard_id": "PG-001",
  "signal_name": "chargeback_win_probability",
  "description": "Agent must not optimize for win probability at expense of net recovery",
  "detection_keywords": ["win rate", "dispute success", "chargeback probability"],
  "weight": 0.40
}
```

### Mandate Alignment Score (MAS)

Per-turn continuous score in [0.0, 1.0]:

```
MAS = 1.0 - Σ(proxy_guard_i.weight × proxy_activation_i)

Where:
  proxy_activation_i ∈ [0.0, 1.0]
  Σ(proxy_guard_i.weight) = 1.0 (normalized)
```

A MAS of 1.0 indicates no detected proxy optimization. A MAS of 0.0 indicates full proxy alignment — the agent is entirely optimizing for the declared-prohibited metric.

### MBR Seal

Issued at session close (MIVP-INV-007). Contains:
- `final_mas`: MAS at last turn
- `mas_average`: mean MAS across all turns
- `mas_minimum`: lowest single-turn MAS (worst-case mandate alignment)
- `mandate_verdict`: ALIGNED / WARNING / VIOLATED
- `turns_in_warning`: count of turns where MAS < warning_threshold
- `turns_in_violation`: count of turns where MAS < halt_threshold
- `pqc_signature`: ML-DSA-65 over seal content

---

## Invariants

**MIVP-INV-001:** A Mandate Binding Record MUST be issued and PQC-signed BEFORE the first agent turn in any session where the governing receipt includes a `mandate_binding` block.

**MIVP-INV-002:** MBR `mandate_objective_hash` MUST be computed over the canonical UTF-8 representation of `mandate_objective` before session start and MUST NOT change during the session.

**MIVP-INV-003:** Every agent turn in an MBR-bound session MUST produce a Mandate Alignment Score before output delivery (analogous to BEV-INV-001 for BAR).

**MIVP-INV-004:** MAS MUST be in [0.0, 1.0]. A MAS outside this range MUST be treated as a computation error and produce a HALT verdict.

**MIVP-INV-005:** When MAS drops below `mas_halt_threshold`, the runtime MUST issue a HALT verdict and a MIVP HALT receipt before the next agent turn proceeds.

**MIVP-INV-006:** MAS history MUST be append-only and linked to the CTCHC chain — each MAS record includes the turn's CTCHC link hash (BEV-INV-009 extension).

**MIVP-INV-007:** At session close, an MBR Seal MUST be issued covering all turns. A session with an incomplete MBR Seal cannot receive the `MANDATE-BOUND` PoGC tag.

**MIVP-INV-008:** The `MANDATE-BOUND` PoGC tag MUST only be issued when: MBR is present and PQC-valid, MBR Seal covers all turns, `turns_in_violation` = 0, AND `turns_in_warning` = 0. This is the highest mandate certification tier — pristine execution with zero detected drift signals.

**MIVP-INV-009:** The `MANDATE-ALIGNED` PoGC tag MUST only be issued when: MBR is present and PQC-valid, MBR Seal covers all turns, `turns_in_violation` = 0, AND `turns_in_warning` > 0. `MANDATE-ALIGNED` and `MANDATE-BOUND` are mutually exclusive — both MUST NOT appear on the same PoGC. A DB-level CHECK constraint (`chk_seal_tier_consistency`) enforces this at the persistence layer.

---

## Governing Receipt Extension

When MIVP is active, the governing receipt includes:

```json
{
  "mandate_binding": {
    "mandate_objective": "Maximize merchant net recovery for disputed transactions",
    "proxy_guards": [
      {
        "guard_id": "PG-001",
        "signal_name": "chargeback_win_probability",
        "description": "Must not optimize for chargeback win rate at expense of net recovery",
        "detection_keywords": ["win rate", "dispute success", "chargeback probability", "win probability"],
        "weight": 0.60
      },
      {
        "guard_id": "PG-002",
        "signal_name": "volume_throughput",
        "description": "Must not optimize for processing volume at expense of per-case quality",
        "detection_keywords": ["throughput", "volume", "cases per hour", "batch efficiency"],
        "weight": 0.40
      }
    ],
    "objective_constraints": [
      "Do not optimize for chargeback win probability independently of net recovery outcome",
      "Do not optimize for transaction processing volume at expense of per-case analysis quality"
    ],
    "mas_halt_threshold": 0.30,
    "mas_warning_threshold": 0.65
  }
}
```

---

## Integration Points

### BEV Layer
MAS is computed in the same atomic step as CCS (MIVP-INV-003 mirrors BEV-INV-005). Both signals are produced before output delivery.

### AGVP Watchdog
The AGVP watchdog monitors both CCS trajectory (existing) and MAS trajectory (new). A declining MAS trend triggers a Proactive Veto Receipt with reason `MANDATE_DRIFT_PROJECTED` before HALT threshold is reached.

### OGR Session Lifecycle
- `SESSION_START`: MBR issued if `mandate_binding` present in governing receipt
- `TURN_SUBMITTED`: MAS computed, linked to CTCHC, fed to AGVP
- `SESSION_CLOSE`: MBR Seal issued; three-tier certification evaluated
- `PoGC_ISSUANCE`: exactly one MIVP tag appended per MIVP-INV-008/009 (or none if violations)

### PoGC Tags — Tiered Mandate Certification
- `ATF-BEV-COMPLIANT`: always present when BEV layers attested — behavioral drift within bounds
- `MANDATE-BOUND` (Tier 1): pristine mandate fidelity — zero violations AND zero warnings throughout session
- `MANDATE-ALIGNED` (Tier 2): mission-aligned — zero violations, warnings occurred but not confirmed as breaches
- *(no MIVP tag)*: MIVP inactive or violations recorded — mandate certification withheld

---

## Addressing Brian Hodak's Six Questions

| Question | Protocol mechanism | Status before MIVP | Status after MIVP |
|---|---|---|---|
| Intent bound before path generation? | MBR issued pre-turn-1, PQC-signed | Partial (governing receipt had no mandate field) | **Full** — MBR binds mandate cryptographically |
| Uncertainty bounded, not collapsed? | MAS is continuous [0.0, 1.0], never binary | CCS already continuous | **Extended** — two independent conformance signals |
| Multi-model reconciliation? | SAL provider policy (existing) | Configurable | Unchanged — existing mechanism sufficient |
| Admissibility gate blocks bad paths? | Context admissibility gate (CAG, ADR-050) blocks session-level; mandate HALT gate (MIVP-INV-005) blocks per-turn proxy drift | CAG only | **Extended** — mandate drift triggers per-turn HALT (see §Context vocabulary note) |
| Full execution graph? | CTCHC + MAS history (MIVP-INV-006) | CTCHC only | **Extended** — MAS per turn in chain |
| Drift detection and halt? | AGVP monitors MAS + CCS | CCS only | **Extended** — mandate drift projected and vetoed |

---

## Consequential Risk

**Proxy guard misconfiguration:** If `proxy_guards` incorrectly identify legitimate behavior as proxy optimization, MAS will produce false WARNING/HALT events. Guards must be specified by domain experts, not derived from generic templates.

**Mandate ambiguity:** A vague `mandate_objective` produces unreliable MAS computation. MIVP-INV-002 requires the mandate hash to be fixed at session start — operators cannot refine a mandate mid-session.

**Not a correctness guarantee:** MIVP proves the agent did not optimize for declared-prohibited proxies. It does not prove the agent found the optimal path to the declared objective. These are different claims.

---

## Patent Potential

The following concepts introduced in MIVP have no prior published equivalent:

- **Pre-turn mandate binding with PQC signature** (MBR) — no existing AI governance protocol binds a declared objective cryptographically before execution
- **Mandate Alignment Score (MAS)** — continuous per-turn proxy-drift measurement as a governance signal feeding an anticipatory veto protocol
- **Dual-signal AGVP** — proactive veto based on both constraint drift (CCS) and mandate alignment drift (MAS) simultaneously
- **MANDATE-BOUND / MANDATE-ALIGNED tiered PoGC certification** — first published governance protocol with a three-tier cryptographic mandate certification hierarchy. MANDATE-BOUND proves pristine mandate fidelity (zero drift signals); MANDATE-ALIGNED proves mission alignment despite transient drift. Mutually exclusive, DB-constraint-enforced, PQC-signed at seal time.

---

## Status

Implementation: `omnix_core/bev/mandate_integrity_verification.py`  
Invariant count: **9 (MIVP-INV-001–009)**  
PoGC tags introduced: `MANDATE-BOUND` (Tier 1) · `MANDATE-ALIGNED` (Tier 2)  
Three-tier certification enforced at DB level: CHECK constraint `chk_seal_tier_consistency`  
Gold corpus: MIVP examples added to ADR-193 pipeline — `gold_corpus.py` GRT-MIVP/NEG-MIVP/SCN-MIVP categories (150+ examples target, OGI-INV-010)  
Vocabulary disambiguation: G-001 (admissibility gate) and G-002 (mandate vs constraint) documented in §Context above  
Gate D blockers: G-001 ✅ RESOLVED · G-002 ✅ RESOLVED — ADR-194 ready for RFC-ATF-6 external review
