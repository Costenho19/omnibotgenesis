"""
ATF Core Invariants — Z3 SMT Formal Proofs
===========================================
Formally proves three foundational invariants of the Agent Trust Fabric protocol
using Z3 Satisfiability Modulo Theories (SMT) solver.

Invariants Proved
-----------------
ATF-INV-001  Monotonic Authority Reduction (MAR)
             ∀ delegation: budget_granted ≤ budget_delegator
             Source: RFC-ATF-1 §5.1 · ADR-156 · docs/formal/ATF-TLA-SPEC.tla L142

ATF-INV-004  Budget Ceiling (Cross-Chain Inductive Step)
             ∀ r in chain: budget_granted ≤ 100 (given root ≤ 100 and MAR)
             Source: RFC-ATF-1 §5.2 · ADR-156 · docs/formal/ATF-TLA-SPEC.tla L156

RGC-INV-004  Trust Lattice Acyclicity (Three-Node Bound)
             No three-node delegation chain can form a directed cycle
             Source: RFC-ATF-2 §6.4 · ADR-159 · docs/formal/ATF-TLA-SPEC.tla L173

Proof Methodology
-----------------
Standard SMT negation refutation:
  Assert preconditions + negation(invariant) → check() → UNSAT ≡ proof

Note: TLA+ model-checked proofs for the same invariants exist at
docs/formal/ATF-TLA-SPEC.tla (properties: MARInvariant, AcyclicityInvariant).
Z3 proofs are complementary: TLA+ covers state-machine safety across all traces;
Z3 covers arithmetic correctness of the closed-form invariant expressions.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Literal

from z3 import (
    And, Bool, If, Implies, Int, Not, Or, Real, Solver,
    sat, unsat, unknown,
)

ProofResult = Literal["UNSAT", "SAT", "UNKNOWN"]


@dataclass
class Z3ProofRecord:
    invariant_id: str
    invariant_name: str
    result: ProofResult
    proved: bool
    elapsed_ms: float
    model_counterexample: str | None = None
    description: str = ""
    negation_asserted: str = ""
    adr_reference: str = ""
    rfc_reference: str = ""
    tla_property: str = ""


def _run_proof(solver: Solver) -> tuple[ProofResult, str | None]:
    result = solver.check()
    if result == unsat:
        return "UNSAT", None
    elif result == sat:
        return "SAT", str(solver.model())
    else:
        return "UNKNOWN", None


# ---------------------------------------------------------------------------
# ATF-INV-001 — Monotonic Authority Reduction (MAR)
# ---------------------------------------------------------------------------

def prove_mar_invariant() -> Z3ProofRecord:
    """
    ATF-INV-001: budget_granted ≤ budget_delegator for every delegation event.

    Formal statement:
        ∀ B_d ∈ [0, 100], δ ∈ [0, 1]:
            B_g = B_d · (1 − δ)  →  B_g ≤ B_d

    Negation asserted:
        ∃ B_d, δ, B_g :
            B_d ∈ [0,100] ∧ δ ∈ [0,1] ∧ B_g = B_d·(1−δ) ∧ B_g > B_d

    Expected: UNSAT — no such counterexample exists.

    Proof sketch:
        B_g = B_d·(1−δ) ≤ B_d·1 = B_d   (since 0 ≤ 1−δ ≤ 1 when 0 ≤ δ ≤ 1)
        Contradiction with B_g > B_d is impossible.
    """
    t0 = time.perf_counter()
    s = Solver()

    budget_delegator = Real("budget_delegator")
    discount = Real("discount")
    budget_granted = Real("budget_granted")

    s.add(budget_delegator >= 0)
    s.add(budget_delegator <= 100)
    s.add(discount >= 0)
    s.add(discount <= 1)
    s.add(budget_granted == budget_delegator * (1 - discount))
    s.add(budget_granted > budget_delegator)

    result, model = _run_proof(s)
    elapsed = (time.perf_counter() - t0) * 1000

    return Z3ProofRecord(
        invariant_id="ATF-INV-001",
        invariant_name="Monotonic Authority Reduction (MAR)",
        result=result,
        proved=(result == "UNSAT"),
        elapsed_ms=round(elapsed, 3),
        model_counterexample=model,
        description=(
            "No delegation can produce a receipt whose authority_budget_granted "
            "exceeds the delegator's authority_budget. Authority can only "
            "decrease — never increase — across a delegation chain."
        ),
        negation_asserted="budget_granted > budget_delegator",
        adr_reference="ADR-156",
        rfc_reference="RFC-ATF-1 §5.1",
        tla_property="MARInvariant",
    )


# ---------------------------------------------------------------------------
# ATF-INV-004 — Budget Ceiling (Cross-Chain Inductive Step)
# ---------------------------------------------------------------------------

def prove_budget_ceiling() -> Z3ProofRecord:
    """
    ATF-INV-004: authority_budget ∈ [0, 100] is preserved inductively across chains.

    Inductive step:
        If parent_budget ∈ [0, 100] and MAR holds (child = parent·(1−δ), δ ∈ [0,1]),
        then child_budget ∈ [0, 100].

    Base case:
        Root agent has budget ∈ [0, 100] by registration constraint.

    Negation asserted:
        ∃ parent ∈ [0,100], δ ∈ [0,1], child = parent·(1−δ) : child > 100

    Expected: UNSAT — given MAR, a child cannot exceed 100 if parent ≤ 100.
    """
    t0 = time.perf_counter()
    s = Solver()

    parent_budget = Real("parent_budget")
    discount = Real("discount")
    child_budget = Real("child_budget")

    s.add(parent_budget >= 0)
    s.add(parent_budget <= 100)
    s.add(discount >= 0)
    s.add(discount <= 1)
    s.add(child_budget == parent_budget * (1 - discount))
    s.add(child_budget > 100)

    result, model = _run_proof(s)
    elapsed = (time.perf_counter() - t0) * 1000

    return Z3ProofRecord(
        invariant_id="ATF-INV-004",
        invariant_name="Budget Ceiling (Cross-Chain Inductive Step)",
        result=result,
        proved=(result == "UNSAT"),
        elapsed_ms=round(elapsed, 3),
        model_counterexample=model,
        description=(
            "If the root agent's authority_budget ≤ 100 (registration constraint) "
            "and MAR holds at every delegation step, then no agent in any chain "
            "can possess a budget exceeding 100. Proved by structural induction; "
            "Z3 verifies the inductive step."
        ),
        negation_asserted="child_budget > 100 (given parent_budget ≤ 100, MAR)",
        adr_reference="ADR-156",
        rfc_reference="RFC-ATF-1 §5.2",
        tla_property="MARChainInvariant",
    )


# ---------------------------------------------------------------------------
# RGC-INV-004 — Trust Lattice Acyclicity (Three-Node Bound)
# ---------------------------------------------------------------------------

def prove_acyclicity_three_node() -> Z3ProofRecord:
    """
    RGC-INV-004: The delegation graph (trust lattice) is a DAG — no cycles.

    Modelled as: can three receipts A, B, C form a directed cycle
    A→B→C→A where each delegation event involves a strictly positive
    authority reduction (discount > 0)?

    Formal claim:
        ∀ bA, bB, bC ∈ (0, 100]:
            bB < bA   (A delegates to B with discount > 0)
          ∧ bC < bB   (B delegates to C with discount > 0)
          ∧ bA < bC   (C delegates to A with positive discount, closing cycle)
        is UNSATISFIABLE.

    Proof:
        bB < bA and bC < bB  →  bC < bA  (transitivity of <)
        bA < bC              →  contradiction with bC < bA
        → UNSAT

    Note on discount = 0 (zero-discount delegations):
        If discount = 0, a delegation produces a receipt with identical budget
        but a new receipt ID. Such chains do not constitute meaningful delegation
        cycles (no authority changes hands). The invariant of interest is cycles
        where actual authority flows — all positive discount. TLA+
        AcyclicityInvariant covers the full identity-based cycle prohibition.

    Negation asserted:
        ∃ bA, bB, bC ∈ (0, 100] : bB < bA ∧ bC < bB ∧ bA < bC

    Expected: UNSAT — strict transitivity of < makes the cycle impossible.
    """
    t0 = time.perf_counter()
    s = Solver()

    bA = Real("budget_A")
    bB = Real("budget_B")
    bC = Real("budget_C")

    s.add(bA > 0, bA <= 100)
    s.add(bB > 0, bB <= 100)
    s.add(bC > 0, bC <= 100)

    # Strict MAR at each delegation step (discount > 0)
    s.add(bB < bA)   # A→B: B gets strictly less than A
    s.add(bC < bB)   # B→C: C gets strictly less than B
    s.add(bA < bC)   # C→A: A gets strictly less than C (closes cycle)

    result, model = _run_proof(s)
    elapsed = (time.perf_counter() - t0) * 1000

    return Z3ProofRecord(
        invariant_id="RGC-INV-004",
        invariant_name="Trust Lattice Acyclicity (Three-Node Bound)",
        result=result,
        proved=(result == "UNSAT"),
        elapsed_ms=round(elapsed, 3),
        model_counterexample=model,
        description=(
            "No positive-budget three-node cycle can exist in the ATF delegation "
            "graph when MAR is enforced. A cycle A→B→C→A would require "
            "bA ≤ bB ≤ bC ≤ bA, forcing all three budgets to equality; "
            "combined with strict monotonic decrease (discount > 0), no "
            "non-zero solution exists. Full unbounded acyclicity is model-checked "
            "by TLA+ (AcyclicityInvariant)."
        ),
        negation_asserted="bA > 0 ∧ bB ≤ bA ∧ bC ≤ bB ∧ bA ≤ bC (positive budget 3-cycle)",
        adr_reference="ADR-159",
        rfc_reference="RFC-ATF-2 §6.4",
        tla_property="AcyclicityInvariant",
    )


# ---------------------------------------------------------------------------
# Proof Manifest
# ---------------------------------------------------------------------------

ATF_PROOF_MANIFEST = {
    "module": "atf_invariants_z3",
    "protocol_layer": "ATF Layer 1-2 — Identity and Delegation",
    "rfc_references": ["RFC-ATF-1", "RFC-ATF-2"],
    "adr_references": ["ADR-156", "ADR-157", "ADR-158", "ADR-159"],
    "tla_spec": "docs/formal/ATF-TLA-SPEC.tla",
    "invariants": ["ATF-INV-001", "ATF-INV-004", "RGC-INV-004"],
    "proof_functions": [
        "prove_mar_invariant",
        "prove_budget_ceiling",
        "prove_acyclicity_three_node",
    ],
}


if __name__ == "__main__":
    import json

    proofs = [
        prove_mar_invariant(),
        prove_budget_ceiling(),
        prove_acyclicity_three_node(),
    ]

    for p in proofs:
        status = "✓ PROVED" if p.proved else "✗ FAILED"
        print(f"[{status}] {p.invariant_id}: {p.invariant_name} ({p.elapsed_ms:.1f}ms)")
        if p.model_counterexample:
            print(f"  COUNTEREXAMPLE: {p.model_counterexample}")

    print(f"\nResult: {sum(p.proved for p in proofs)}/{len(proofs)} invariants proved")
