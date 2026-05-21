# ADR-177: OMNIX Formal Verification Suite (FVS)

**Status:** Accepted  
**Date:** May 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Registered:** England & Wales · 71-75 Shelton Street, Covent Garden, London WC2H 9JQ  
**Operational HQ:** Abu Dhabi, UAE  
**Supersedes:** None  
**Extends:** ADR-156 (ATF) · ADR-173 (DSPP) · ADR-174 (AGVP) · ADR-175 (SSD)  
**Related:** ADR-159 (RGC) · docs/formal/ATF-TLA-SPEC.tla · docs/formal/ATF-FORMAL-VERIFICATION.md  
**Implements:** `omnix_core/formal_verification/`  
**Priority Record:** OMNIX-PAR-2026-FVS-001 · May 2026

---

## Context

### Prior Verification State

Prior to this ADR, OMNIX invariant verification used two approaches:

| Approach | Coverage | Limitation |
|---|---|---|
| TLA+ model checking | MAR, Acyclicity, Chain Root Consistency, Immutability | State-machine safety; does not prove arithmetic correctness of metric formulas |
| Python test suite (245 pass) | All 67 invariants via behavioral testing | Covers specific inputs; does not constitute a formal mathematical proof |

### The Formal Proof Gap

The governance infrastructure literature recognizes a distinction between:

1. **Model-checked safety properties** (TLA+): verified across all finite state traces of a formal model.
2. **Behavioral test coverage**: verified for specific inputs under specific configurations.
3. **SMT-proved arithmetic invariants**: formally proved for all possible real-number inputs using a theorem prover — no discretization, no sampling, no enumeration.

OMNIX lacked the third category. This is significant because:

- CRSI is a continuous metric over ℝ. TLA+ operates over discrete state spaces.
- SDU is a weighted sum of three sub-metrics over [0,1]. Correctness of its bounds requires arithmetic proof, not sampling.
- The DSPP threshold partition (DSPP-INV-007) is a claim about the real-number line — that four ranges cover [0,1] completely with no gaps and no overlaps.

These properties require **Satisfiability Modulo Theories (SMT)** over linear arithmetic — exactly what the Z3 solver provides.

### The Competitive Context

Peer governance specification systems (notably VeriSigil VGS-001–011, Zenodo 10.5281/zenodo.20264923, May 2026) include Z3 SMT proofs for 4 critical invariants. This ADR establishes OMNIX's Z3 proof suite at **19 invariants across 4 protocol modules**, providing:

- Broader coverage (19 vs 4 invariants)
- Dual-methodology verification (TLA+ model checking + Z3 SMT arithmetic proofs)
- Machine-readable JSON proof reports
- Full test suite integration (pytest, CI-compatible)

---

## Decision

### Establish `omnix_core/formal_verification/` as a Permanent Protocol Artifact

ADR-177 establishes the **OMNIX Formal Verification Suite (FVS)** as a first-class protocol artifact at `omnix_core/formal_verification/`, governed under the same standards as the ATF implementation code.

The FVS is:
- **Machine-checkable**: any party with `z3-solver` installed can reproduce all proofs
- **Deterministic**: Z3 proofs over linear arithmetic always terminate with UNSAT or SAT
- **Platform-independent**: proofs do not depend on OMNIX runtime, database, or credentials
- **Versioned**: `SUITE_VERSION = "OMNIX-FVS-1.0"` tracks the proof suite revision

### Module Structure

```
omnix_core/formal_verification/
├── __init__.py              # Public API — all proof functions
├── atf_invariants_z3.py     # ATF-INV-001, ATF-INV-004, RGC-INV-004
├── agv_invariants_z3.py     # AGV-INV-001, -003, -004, -005, -006
├── ssd_invariants_z3.py     # CRSI-BOUND-LO/HI, CRSI-CLASS-TOT, SSD-INV-001, -003
├── dspp_invariants_z3.py    # SDU-BOUND-LO/HI, SDU-WSUM, DSPP-INV-005, -007a, -007b
└── run_all.py               # Unified runner → JSON proof report
```

### Proof Methodology

**Standard SMT negation refutation:**

```
1. Assert system preconditions (valid state constraints for the protocol)
2. Assert the NEGATION of the invariant under proof
3. Call Z3 Solver.check()
4. UNSAT → the negation is unsatisfiable → invariant is formally proved
5. SAT → Z3 returns a counterexample → invariant is falsifiable (failure mode)
```

This is the same methodology used in formal methods research and is equivalent to:
- *"It is impossible for the invariant to be violated under the stated preconditions"*

### Invariant Coverage

| Invariant | Name | Layer | Method |
|---|---|---|---|
| ATF-INV-001 | Monotonic Authority Reduction | ATF-L2 | Z3 + TLA+ |
| ATF-INV-004 | Budget Ceiling (inductive step) | ATF-L2 | Z3 + TLA+ |
| RGC-INV-004 | Trust Lattice Acyclicity (3-node) | ATF-L3 | Z3 + TLA+ |
| AGV-INV-001 | Anticipatory Authority Equivalence | AGVP | Z3 |
| AGV-INV-003 | Minimum Watchdog Interval | AGVP | Z3 |
| AGV-INV-004 | PVR Content Hash Commitment | AGVP | Z3 |
| AGV-INV-005 | No Veto Without Baseline | AGVP | Z3 |
| AGV-INV-006 | Auto-Recalibration Freeze | AGVP | Z3 |
| CRSI-BOUND-LO | CRSI Non-Negativity | SSD | Z3 |
| CRSI-BOUND-HI | CRSI Upper Bound | SSD | Z3 |
| CRSI-CLASS-TOT | CRSI Classification Totality | SSD | Z3 |
| SSD-INV-001 | Structural Shift Blocks Recalibration | SSD | Z3 |
| SSD-INV-003 | Minimum History for Verdict | SSD | Z3 |
| SDU-BOUND-LO | SDU Non-Negativity | DSPP | Z3 |
| SDU-BOUND-HI | SDU Upper Bound | DSPP | Z3 |
| SDU-WSUM | SDU Convex Combination | DSPP | Z3 |
| DSPP-INV-005 | RSA Verdict Determinism | DSPP | Z3 |
| DSPP-INV-007a | SDU Threshold Partition (Totality) | DSPP | Z3 |
| DSPP-INV-007b | SDU Threshold Exclusivity | DSPP | Z3 |

**Total: 19 Z3 SMT proofs · 3 also verified by TLA+ model checking**

### JSON Proof Report Format

```json
{
  "suite": "OMNIX-FVS-1.0",
  "generated_at": "2026-05-21T...",
  "solver": "Z3 4.x.x",
  "total": 19,
  "proved": 19,
  "failed": 0,
  "all_proved": true,
  "proofs": [
    {
      "invariant_id": "ATF-INV-001",
      "invariant_name": "Monotonic Authority Reduction (MAR)",
      "result": "UNSAT",
      "proved": true,
      "elapsed_ms": 4.2,
      "negation_asserted": "budget_granted > budget_delegator",
      "adr_reference": "ADR-156",
      "rfc_reference": "RFC-ATF-1 §5.1"
    },
    ...
  ]
}
```

---

## FVS-INV-001 — All Proofs Return UNSAT

The Formal Verification Suite MUST return `all_proved=True` (all 19 proofs UNSAT).
Any SAT result indicates a violation of the invariant under the stated preconditions
and constitutes a critical protocol failure requiring immediate investigation.

**Verification:** `tests/test_formal_verification.py::TestFullSuite::test_run_all_proofs_all_proved`

## FVS-INV-002 — No UNKNOWN Results

No proof may return `UNKNOWN` (Z3 solver timeout or incomplete theory coverage).
The Z3 linear arithmetic (LA) theory is decidable — UNKNOWN indicates a solver
configuration error, not a legitimate proof state.

**Verification:** `tests/test_formal_verification.py::TestFullSuite::test_no_unknown_results`

## FVS-INV-003 — Suite Completes Under 10 Seconds

The full 19-proof suite must complete in under 10 seconds on any standard hardware.
Z3 linear arithmetic proofs are polynomial-time decidable. A timeout indicates a
degenerate encoding.

**Verification:** `tests/test_formal_verification.py::TestFullSuite::test_run_all_proofs_completes_under_10s`

---

## Relationship to Existing Verification Infrastructure

### Complementary to TLA+ (docs/formal/ATF-TLA-SPEC.tla)

| Dimension | TLA+ | Z3 SMT |
|---|---|---|
| **Domain** | Discrete state machines | Real arithmetic (ℝ, ℤ, 𝔹) |
| **What it proves** | Safety properties across all finite traces | Arithmetic invariants for all real inputs |
| **Best for** | Protocol state transitions, ordering, acyclicity | Metric bounds, threshold correctness, weights |
| **OMNIX coverage** | MAR, Acyclicity, Immutability, Chain Root | CRSI ∈ [0,1], SDU ∈ [0,1], threshold partition |

The two methodologies are **strictly complementary**. Neither subsumes the other.
OMNIX is the only AI governance framework with dual-methodology formal verification.

### Extension Path for RFC-ATF-4 Publication

The FVS is the normative proof package for RFC-ATF-4 (Proactive Governance Layer).
When RFC-ATF-4 is submitted to Zenodo, the proof runner output (`run_all.py --json`)
constitutes the machine-readable conformance evidence package.

---

## Consequences

### Positive

- **Industry-leading formal verification depth**: 19 Z3 proofs + TLA+ model checking
  on the same invariants — no other AI governance framework publishes both.
- **Machine-reproducible evidence**: any auditor, regulator, or institutional buyer
  can reproduce all 19 proofs in under 10 seconds with a single command.
- **Publishable as part of RFC-ATF-4**: the proof suite becomes a citable artifact
  on Zenodo, establishing OMNIX as the reference implementation for formally
  verified AI governance infrastructure.
- **CI integration**: `tests/test_formal_verification.py` runs in the standard
  pytest suite — proofs are verified on every commit.

### Negative / Trade-offs

- **z3-solver dependency**: adds ~25MB to the dependency graph. Acceptable given
  the value of formal proofs; isolated to `omnix_core/formal_verification/`.
- **Z3 version sensitivity**: Z3 proof correctness is Z3-version-independent
  for linear arithmetic (decidable theory), but the exact timing may vary.

---

*ADR-177 — Harold Nunes — OMNIX QUANTUM LTD — May 2026*  
*Priority Record: OMNIX-PAR-2026-FVS-001*
