"""
OMNIX QUANTUM — Formal Verification Suite (FVS)
================================================
Z3 SMT proofs for all critical ATF protocol invariants.

Modules
-------
atf_invariants_z3   — ATF-INV-001 (MAR) · ATF-INV-004 (Budget Ceiling) · RGC-INV-004 (Acyclicity)
agv_invariants_z3   — AGV-INV-001 thru AGV-INV-006 (AGVP)
ssd_invariants_z3   — SSD-INV-001 thru SSD-INV-003 · CRSI metric bounds
dspp_invariants_z3  — DSPP-INV-005 (Determinism) · DSPP-INV-007 (Threshold Partition) · SDU bounds
run_all             — Unified runner → machine-readable JSON proof report

Proof Methodology
-----------------
Each invariant is proven via negation refutation (standard SMT methodology):
  1. Assert system preconditions (valid state constraints)
  2. Assert the negation of the invariant under proof
  3. Call Z3 Solver.check()
  4. UNSAT → invariant is formally proven (negation is impossible under preconditions)
  5. SAT → invariant is falsifiable (model returned shows the counterexample)

All invariants in this suite return UNSAT, constituting formal proofs.
These proofs are machine-checkable, deterministic, and platform-independent.

Reference: ADR-177 — OMNIX Formal Verification Suite
"""

from omnix_core.formal_verification.atf_invariants_z3 import (
    prove_mar_invariant,
    prove_budget_ceiling,
    prove_acyclicity_three_node,
    ATF_PROOF_MANIFEST,
)
from omnix_core.formal_verification.agv_invariants_z3 import (
    prove_agv_inv001_authority_equivalence,
    prove_agv_inv003_minimum_interval,
    prove_agv_inv004_hash_commitment,
    prove_agv_inv005_no_veto_without_baseline,
    prove_agv_inv006_recalibration_freeze,
    AGV_PROOF_MANIFEST,
)
from omnix_core.formal_verification.ssd_invariants_z3 import (
    prove_crsi_lower_bound,
    prove_crsi_upper_bound,
    prove_ssd_inv001_shift_blocks_recalibration,
    prove_ssd_inv003_minimum_history,
    prove_crsi_classification_totality,
    SSD_PROOF_MANIFEST,
)
from omnix_core.formal_verification.dspp_invariants_z3 import (
    prove_sdu_lower_bound,
    prove_sdu_upper_bound,
    prove_sdu_weighted_sum_bounds,
    prove_dspp_inv005_rsa_determinism,
    prove_dspp_inv007_threshold_partition,
    prove_dspp_inv007_threshold_exclusivity,
    DSPP_PROOF_MANIFEST,
)

__all__ = [
    "prove_mar_invariant",
    "prove_budget_ceiling",
    "prove_acyclicity_three_node",
    "prove_agv_inv001_authority_equivalence",
    "prove_agv_inv003_minimum_interval",
    "prove_agv_inv004_hash_commitment",
    "prove_agv_inv005_no_veto_without_baseline",
    "prove_agv_inv006_recalibration_freeze",
    "prove_crsi_lower_bound",
    "prove_crsi_upper_bound",
    "prove_ssd_inv001_shift_blocks_recalibration",
    "prove_ssd_inv003_minimum_history",
    "prove_crsi_classification_totality",
    "prove_sdu_lower_bound",
    "prove_sdu_upper_bound",
    "prove_sdu_weighted_sum_bounds",
    "prove_dspp_inv005_rsa_determinism",
    "prove_dspp_inv007_threshold_partition",
    "prove_dspp_inv007_threshold_exclusivity",
    "ATF_PROOF_MANIFEST",
    "AGV_PROOF_MANIFEST",
    "SSD_PROOF_MANIFEST",
    "DSPP_PROOF_MANIFEST",
]
