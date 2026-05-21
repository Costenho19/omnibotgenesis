"""
Tests — OMNIX Formal Verification Suite (ADR-177)
==================================================
Verifies that all Z3 SMT proofs in omnix_core/formal_verification/ return UNSAT,
confirming that the stated invariants are formally proved.

This test suite is machine-checkable, deterministic, and platform-independent.
Running it on any machine with z3-solver installed will reproduce the same proofs.

Reference: ADR-177 — OMNIX Formal Verification Suite
"""

import pytest

from omnix_core.formal_verification.atf_invariants_z3 import (
    prove_acyclicity_three_node,
    prove_budget_ceiling,
    prove_mar_invariant,
)
from omnix_core.formal_verification.agv_invariants_z3 import (
    prove_agv_inv001_authority_equivalence,
    prove_agv_inv003_minimum_interval,
    prove_agv_inv004_hash_commitment,
    prove_agv_inv005_no_veto_without_baseline,
    prove_agv_inv006_recalibration_freeze,
)
from omnix_core.formal_verification.ssd_invariants_z3 import (
    prove_crsi_classification_totality,
    prove_crsi_lower_bound,
    prove_crsi_upper_bound,
    prove_ssd_inv001_shift_blocks_recalibration,
    prove_ssd_inv003_minimum_history,
)
from omnix_core.formal_verification.dspp_invariants_z3 import (
    prove_dspp_inv005_rsa_determinism,
    prove_dspp_inv007_threshold_exclusivity,
    prove_dspp_inv007_threshold_partition,
    prove_sdu_lower_bound,
    prove_sdu_upper_bound,
    prove_sdu_weighted_sum_bounds,
)
from omnix_core.formal_verification.run_all import run_all_proofs


# ===========================================================================
# ATF Core Invariants (RFC-ATF-1 / RFC-ATF-2)
# ===========================================================================

class TestATFInvariants:
    """Z3 proofs for ATF delegation protocol invariants."""

    def test_atf_inv001_mar_is_proved(self):
        """ATF-INV-001: Monotonic Authority Reduction is formally proved."""
        record = prove_mar_invariant()
        assert record.proved, (
            f"ATF-INV-001 proof failed. Z3 result: {record.result}. "
            f"Counterexample: {record.model_counterexample}"
        )
        assert record.result == "UNSAT"
        assert record.invariant_id == "ATF-INV-001"

    def test_atf_inv001_completes_fast(self):
        """ATF-INV-001 proof completes in under 500ms."""
        record = prove_mar_invariant()
        assert record.elapsed_ms < 500, f"Proof too slow: {record.elapsed_ms}ms"

    def test_atf_inv004_budget_ceiling_is_proved(self):
        """ATF-INV-004: Budget Ceiling inductive step is formally proved."""
        record = prove_budget_ceiling()
        assert record.proved, (
            f"ATF-INV-004 proof failed. Z3 result: {record.result}. "
            f"Counterexample: {record.model_counterexample}"
        )
        assert record.result == "UNSAT"
        assert record.invariant_id == "ATF-INV-004"

    def test_rgc_inv004_acyclicity_is_proved(self):
        """RGC-INV-004: Trust Lattice Acyclicity (three-node) is formally proved."""
        record = prove_acyclicity_three_node()
        assert record.proved, (
            f"RGC-INV-004 proof failed. Z3 result: {record.result}. "
            f"Counterexample: {record.model_counterexample}"
        )
        assert record.result == "UNSAT"
        assert record.invariant_id == "RGC-INV-004"

    def test_atf_proofs_have_correct_references(self):
        """All ATF proof records have non-empty ADR and RFC references."""
        for fn in [prove_mar_invariant, prove_budget_ceiling, prove_acyclicity_three_node]:
            record = fn()
            assert record.adr_reference, f"{record.invariant_id} missing adr_reference"
            assert record.rfc_reference, f"{record.invariant_id} missing rfc_reference"
            assert record.description, f"{record.invariant_id} missing description"
            assert record.negation_asserted, f"{record.invariant_id} missing negation_asserted"


# ===========================================================================
# AGVP Invariants (RFC-ATF-4 §4)
# ===========================================================================

class TestAGVPInvariants:
    """Z3 proofs for Anticipatory Governance Veto Protocol invariants."""

    def test_agv_inv001_authority_equivalence_is_proved(self):
        """AGV-INV-001: PVR block has same authority as reactive block."""
        record = prove_agv_inv001_authority_equivalence()
        assert record.proved, f"AGV-INV-001 failed: {record.model_counterexample}"
        assert record.result == "UNSAT"

    def test_agv_inv003_minimum_interval_is_proved(self):
        """AGV-INV-003: Watchdog interval cannot be below 30 seconds."""
        record = prove_agv_inv003_minimum_interval()
        assert record.proved, f"AGV-INV-003 failed: {record.model_counterexample}"
        assert record.result == "UNSAT"

    def test_agv_inv004_hash_commitment_is_proved(self):
        """AGV-INV-004: PVR content hash is deterministic over its fields."""
        record = prove_agv_inv004_hash_commitment()
        assert record.proved, f"AGV-INV-004 failed: {record.model_counterexample}"
        assert record.result == "UNSAT"

    def test_agv_inv005_no_veto_without_baseline_is_proved(self):
        """AGV-INV-005: No PVR emitted for uncalibrated domains."""
        record = prove_agv_inv005_no_veto_without_baseline()
        assert record.proved, f"AGV-INV-005 failed: {record.model_counterexample}"
        assert record.result == "UNSAT"

    def test_agv_inv006_recalibration_freeze_is_proved(self):
        """AGV-INV-006: Active PVR blocks auto-recalibration."""
        record = prove_agv_inv006_recalibration_freeze()
        assert record.proved, f"AGV-INV-006 failed: {record.model_counterexample}"
        assert record.result == "UNSAT"

    def test_all_agv_proofs_proved(self):
        """All 5 AGVP invariants are proved."""
        proofs = [
            prove_agv_inv001_authority_equivalence(),
            prove_agv_inv003_minimum_interval(),
            prove_agv_inv004_hash_commitment(),
            prove_agv_inv005_no_veto_without_baseline(),
            prove_agv_inv006_recalibration_freeze(),
        ]
        failed = [p for p in proofs if not p.proved]
        assert not failed, f"AGVP proofs failed: {[p.invariant_id for p in failed]}"


# ===========================================================================
# SSD Invariants (RFC-ATF-4 §5)
# ===========================================================================

class TestSSDInvariants:
    """Z3 proofs for Structural Shift Detector and CRSI metric invariants."""

    def test_crsi_lower_bound_is_proved(self):
        """CRSI ≥ 0 for all valid inputs."""
        record = prove_crsi_lower_bound()
        assert record.proved, f"CRSI-BOUND-LO failed: {record.model_counterexample}"
        assert record.result == "UNSAT"

    def test_crsi_upper_bound_is_proved(self):
        """CRSI ≤ 1 for all valid inputs."""
        record = prove_crsi_upper_bound()
        assert record.proved, f"CRSI-BOUND-HI failed: {record.model_counterexample}"
        assert record.result == "UNSAT"

    def test_crsi_classification_totality_is_proved(self):
        """Every CRSI ∈ [0,1] maps to exactly one classification class."""
        record = prove_crsi_classification_totality()
        assert record.proved, f"CRSI-CLASS-TOT failed: {record.model_counterexample}"
        assert record.result == "UNSAT"

    def test_ssd_inv001_shift_blocks_recalibration_is_proved(self):
        """SSD-INV-001: STRUCTURAL_SHIFT blocks auto-recalibration."""
        record = prove_ssd_inv001_shift_blocks_recalibration()
        assert record.proved, f"SSD-INV-001 failed: {record.model_counterexample}"
        assert record.result == "UNSAT"

    def test_ssd_inv003_minimum_history_is_proved(self):
        """SSD-INV-003: < 5 history cycles cannot produce STRUCTURAL_SHIFT verdict."""
        record = prove_ssd_inv003_minimum_history()
        assert record.proved, f"SSD-INV-003 failed: {record.model_counterexample}"
        assert record.result == "UNSAT"

    def test_all_ssd_proofs_proved(self):
        """All 5 SSD/CRSI invariants are proved."""
        proofs = [
            prove_crsi_lower_bound(),
            prove_crsi_upper_bound(),
            prove_crsi_classification_totality(),
            prove_ssd_inv001_shift_blocks_recalibration(),
            prove_ssd_inv003_minimum_history(),
        ]
        failed = [p for p in proofs if not p.proved]
        assert not failed, f"SSD proofs failed: {[p.invariant_id for p in failed]}"


# ===========================================================================
# DSPP Invariants (RFC-ATF-4 §6)
# ===========================================================================

class TestDSPPInvariants:
    """Z3 proofs for Dynamic Semantic Portability Protocol and SDU metric invariants."""

    def test_sdu_lower_bound_is_proved(self):
        """SDU ≥ 0 for all valid sub-metric inputs."""
        record = prove_sdu_lower_bound()
        assert record.proved, f"SDU-BOUND-LO failed: {record.model_counterexample}"
        assert record.result == "UNSAT"

    def test_sdu_upper_bound_is_proved(self):
        """SDU ≤ 1 for all valid sub-metric inputs (weights sum to 1.0)."""
        record = prove_sdu_upper_bound()
        assert record.proved, f"SDU-BOUND-HI failed: {record.model_counterexample}"
        assert record.result == "UNSAT"

    def test_sdu_weighted_sum_is_convex_combination(self):
        """SDU weights (0.40 + 0.35 + 0.25) sum to exactly 1.0."""
        record = prove_sdu_weighted_sum_bounds()
        assert record.proved, f"SDU-WSUM failed: {record.model_counterexample}"
        assert record.result == "UNSAT"

    def test_dspp_inv005_rsa_determinism_is_proved(self):
        """DSPP-INV-005: RSA verdict is deterministic for identical inputs."""
        record = prove_dspp_inv005_rsa_determinism()
        assert record.proved, f"DSPP-INV-005 failed: {record.model_counterexample}"
        assert record.result == "UNSAT"

    def test_dspp_inv007_threshold_partition_is_proved(self):
        """DSPP-INV-007a: SDU verdict classes are exhaustive (totality)."""
        record = prove_dspp_inv007_threshold_partition()
        assert record.proved, f"DSPP-INV-007a failed: {record.model_counterexample}"
        assert record.result == "UNSAT"

    def test_dspp_inv007_threshold_exclusivity_is_proved(self):
        """DSPP-INV-007b: SDU verdict classes are non-overlapping (exclusivity)."""
        record = prove_dspp_inv007_threshold_exclusivity()
        assert record.proved, f"DSPP-INV-007b failed: {record.model_counterexample}"
        assert record.result == "UNSAT"

    def test_all_dspp_proofs_proved(self):
        """All 6 DSPP/SDU invariants are proved."""
        proofs = [
            prove_sdu_lower_bound(),
            prove_sdu_upper_bound(),
            prove_sdu_weighted_sum_bounds(),
            prove_dspp_inv005_rsa_determinism(),
            prove_dspp_inv007_threshold_partition(),
            prove_dspp_inv007_threshold_exclusivity(),
        ]
        failed = [p for p in proofs if not p.proved]
        assert not failed, f"DSPP proofs failed: {[p.invariant_id for p in failed]}"


# ===========================================================================
# Full Suite Integration
# ===========================================================================

class TestFullSuite:
    """Integration tests for the complete formal verification suite."""

    def test_run_all_proofs_all_proved(self):
        """run_all_proofs() reports all_proved=True with 19/19 invariants."""
        report = run_all_proofs()
        assert report["all_proved"], (
            f"Not all proofs passed: {report['proved']}/{report['total']} proved. "
            f"Failures: {[p['invariant_id'] for p in report['proofs'] if not p['proved']]}"
        )

    def test_run_all_proofs_count(self):
        """run_all_proofs() covers exactly 19 invariants."""
        report = run_all_proofs()
        assert report["total"] == 19, f"Expected 19 proofs, got {report['total']}"

    def test_run_all_proofs_schema(self):
        """run_all_proofs() output has all required fields."""
        report = run_all_proofs()
        required_keys = [
            "suite", "generated_at", "solver", "protocol", "methodology",
            "total", "proved", "failed", "unknown", "all_proved",
            "total_elapsed_ms", "modules", "proofs",
        ]
        for key in required_keys:
            assert key in report, f"Missing key in report: {key}"

    def test_run_all_proofs_proof_records_schema(self):
        """Each proof record in run_all_proofs() has required fields."""
        report = run_all_proofs()
        required_proof_keys = [
            "invariant_id", "invariant_name", "result", "proved",
            "elapsed_ms", "description", "negation_asserted",
            "adr_reference", "rfc_reference",
        ]
        for proof in report["proofs"]:
            for key in required_proof_keys:
                assert key in proof, f"Proof record missing key '{key}': {proof.get('invariant_id')}"

    def test_run_all_proofs_completes_under_10s(self):
        """Full suite of 19 Z3 proofs completes in under 10 seconds."""
        report = run_all_proofs()
        assert report["total_elapsed_ms"] < 10_000, (
            f"Suite too slow: {report['total_elapsed_ms']}ms"
        )

    def test_suite_version_constant(self):
        """Suite version string is present and follows expected format."""
        report = run_all_proofs()
        assert report["suite"].startswith("OMNIX-FVS-"), f"Unexpected suite version: {report['suite']}"

    def test_no_unknown_results(self):
        """No proof returns UNKNOWN (Z3 solver timeout or incomplete theory)."""
        report = run_all_proofs()
        unknown = [p["invariant_id"] for p in report["proofs"] if p["result"] == "UNKNOWN"]
        assert not unknown, f"Z3 returned UNKNOWN for: {unknown}"
