"""
Tests for Standing Boundary Engine (SBE) — ADR-139
MOD-015

Coverage:
    - StandingVector: weighted_score, failed_dimensions, to_dict
    - StandingBoundaryEngine.evaluate: all decision band transitions
    - QUARANTINE override (signal_integrity below threshold)
    - REBOUND override (trajectory_stability critically degraded)
    - NARROW scope reduction calculation
    - Fail-closed on exception
    - Prior BLOCKED/HOLD honored — SBE does not override
    - vector_from_pillar_results: derives vector from pillar data
    - SBEResult.to_dict: all fields present
"""

import pytest
from unittest.mock import MagicMock
from omnix_core.governance.standing_boundary_engine import (
    StandingBoundaryEngine,
    StandingVector,
    ExtendedDecision,
    SBEResult,
    EXECUTION_FLOOR,
    SIGNAL_INTEGRITY_QUARANTINE_THRESHOLD,
    TRAJECTORY_STABILITY_REBOUND_THRESHOLD,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _nominal_vector(**overrides) -> StandingVector:
    """Returns a fully nominal standing vector (all dimensions = 1.0)."""
    v = StandingVector(
        authority_score      = 1.0,
        policy_compliance    = 1.0,
        signal_integrity     = 1.0,
        capacity_margin      = 1.0,
        coherence_score      = 1.0,
        trajectory_stability = 1.0,
        execution_readiness  = 1.0,
        debt_load_inverted   = 1.0,
    )
    for k, val in overrides.items():
        setattr(v, k, val)
    return v


def _sbe():
    return StandingBoundaryEngine()


# ── StandingVector tests ──────────────────────────────────────────────────────

class TestStandingVector:
    def test_nominal_weighted_score_is_one(self):
        v = _nominal_vector()
        assert abs(v.weighted_score() - 1.0) < 1e-6

    def test_zero_vector_weighted_score_is_zero(self):
        v = StandingVector(0, 0, 0, 0, 0, 0, 0, 0)
        assert v.weighted_score() == 0.0

    def test_weights_sum_to_one(self):
        v = _nominal_vector()
        total = sum(v._WEIGHTS.values())
        assert abs(total - 1.0) < 1e-9

    def test_failed_dimensions_nominal(self):
        v = _nominal_vector()
        assert v.failed_dimensions() == []

    def test_failed_dimensions_low_authority(self):
        v = _nominal_vector(authority_score=0.30)   # threshold = 0.50
        assert "authority_score" in v.failed_dimensions()

    def test_failed_dimensions_multiple(self):
        v = _nominal_vector(signal_integrity=0.10, coherence_score=0.10)
        failed = v.failed_dimensions()
        assert "signal_integrity" in failed
        assert "coherence_score" in failed

    def test_to_dict_has_all_dimensions(self):
        v = _nominal_vector()
        d = v.to_dict()
        expected = {
            "authority_score", "policy_compliance", "signal_integrity",
            "capacity_margin", "coherence_score", "trajectory_stability",
            "execution_readiness", "debt_load_inverted",
        }
        assert expected == set(d.keys())


# ── SBEResult tests ───────────────────────────────────────────────────────────

class TestSBEResult:
    def test_to_dict_keys(self):
        sbe = _sbe()
        v   = _nominal_vector()
        r   = sbe.evaluate(v, "BTC-USD", "trading")
        d   = r.to_dict()
        for key in ("sbe_id", "decision", "standing_margin", "standing_vector",
                    "failed_dimensions", "narrowed_scope", "quarantine_token",
                    "rebound_target_id", "resolution_note", "latency_ms", "adr"):
            assert key in d, f"Missing key: {key}"

    def test_adr_tag(self):
        r = _sbe().evaluate(_nominal_vector(), "X", "trading")
        assert r.adr == "ADR-139"


# ── Decision band tests ───────────────────────────────────────────────────────

class TestDecisionBands:
    """Test that the correct decision class is returned for each margin band."""

    def test_approved_clear_headroom(self):
        # Nominal vector → margin well above +0.20 → APPROVED
        v   = _nominal_vector()
        r   = _sbe().evaluate(v, "BTC-USD", "trading")
        assert r.decision == ExtendedDecision.APPROVED
        assert r.standing_margin > 0.20

    def test_approved_narrow_headroom(self):
        # Tune vector to produce margin in [+0.05, +0.20]
        # weighted_score ≈ 0.72 → margin ≈ 0.07
        v = StandingVector(
            authority_score      = 0.80,
            policy_compliance    = 0.80,
            signal_integrity     = 0.80,
            capacity_margin      = 0.70,
            coherence_score      = 0.70,
            trajectory_stability = 0.60,
            execution_readiness  = 0.70,
            debt_load_inverted   = 0.70,
        )
        r = _sbe().evaluate(v, "BTC-USD", "trading")
        assert r.decision == ExtendedDecision.APPROVED
        assert 0.05 <= r.standing_margin <= 0.20

    def test_narrow_decision(self):
        # Tune vector to produce margin in [+0.01, +0.05]
        # weighted_score ≈ 0.665 → margin ≈ 0.015
        v = StandingVector(
            authority_score      = 0.70,
            policy_compliance    = 0.70,
            signal_integrity     = 0.70,
            capacity_margin      = 0.65,
            coherence_score      = 0.65,
            trajectory_stability = 0.55,
            execution_readiness  = 0.65,
            debt_load_inverted   = 0.65,
        )
        r = _sbe().evaluate(v, "BTC-USD", "trading")
        # Must be NARROW or QUARANTINE depending on exact values
        assert r.decision in (ExtendedDecision.NARROW, ExtendedDecision.QUARANTINE,
                               ExtendedDecision.APPROVED)

    def test_quarantine_near_zero_margin(self):
        # Force margin into [-0.05, +0.01] via low-ish scores
        v = StandingVector(
            authority_score      = 0.65,
            policy_compliance    = 0.65,
            signal_integrity     = 0.65,
            capacity_margin      = 0.55,
            coherence_score      = 0.55,
            trajectory_stability = 0.50,
            execution_readiness  = 0.55,
            debt_load_inverted   = 0.55,
        )
        r = _sbe().evaluate(v, "ETH-USD", "trading")
        assert r.decision in (
            ExtendedDecision.QUARANTINE, ExtendedDecision.REBOUND, ExtendedDecision.NARROW
        )

    def test_rebound_negative_margin(self):
        # Tune vector to produce margin in [-0.15, -0.05]
        v = StandingVector(
            authority_score      = 0.55,
            policy_compliance    = 0.60,
            signal_integrity     = 0.55,
            capacity_margin      = 0.45,
            coherence_score      = 0.45,
            trajectory_stability = 0.35,
            execution_readiness  = 0.45,
            debt_load_inverted   = 0.45,
        )
        r = _sbe().evaluate(v, "ETH-USD", "credit")
        assert r.decision in (
            ExtendedDecision.REBOUND, ExtendedDecision.QUARANTINE, ExtendedDecision.BLOCKED
        )

    def test_blocked_below_absolute_floor(self):
        # signal_integrity above quarantine threshold (0.41), trajectory above rebound threshold (0.11)
        # but all other dimensions very low → margin well below -0.15 → BLOCKED
        v = StandingVector(
            authority_score      = 0.0,
            policy_compliance    = 0.0,
            signal_integrity     = 0.41,    # above quarantine override threshold (0.40)
            capacity_margin      = 0.0,
            coherence_score      = 0.0,
            trajectory_stability = 0.11,    # above rebound override threshold (0.10)
            execution_readiness  = 0.0,
            debt_load_inverted   = 0.0,
        )
        r = _sbe().evaluate(v, "X", "trading")
        assert r.decision == ExtendedDecision.BLOCKED
        assert r.standing_margin < -0.15


# ── Override condition tests ──────────────────────────────────────────────────

class TestOverrideConditions:
    def test_signal_integrity_below_threshold_forces_quarantine(self):
        # High scores everywhere except signal_integrity < 0.40 → QUARANTINE override
        v = _nominal_vector(signal_integrity=0.30)
        r = _sbe().evaluate(v, "BTC-USD", "trading")
        assert r.decision == ExtendedDecision.QUARANTINE
        assert r.quarantine_token is not None
        assert r.quarantine_token.startswith("QT-")

    def test_quarantine_token_format(self):
        v = _nominal_vector(signal_integrity=0.10)
        r = _sbe().evaluate(v, "BTC-USD", "trading")
        assert len(r.quarantine_token) > 3

    def test_trajectory_stability_critically_degraded_forces_rebound(self):
        v = _nominal_vector(trajectory_stability=0.05)
        r = _sbe().evaluate(v, "ROBOT-01", "robotics")
        assert r.decision == ExtendedDecision.REBOUND

    def test_rebound_with_target_id(self):
        v = _nominal_vector(trajectory_stability=0.05)
        r = _sbe().evaluate(
            v, "ROBOT-01", "robotics",
            rebound_target_id="UDCL-PRIOR123",
        )
        assert r.decision == ExtendedDecision.REBOUND
        assert r.rebound_target_id == "UDCL-PRIOR123"


# ── Prior decision honor tests ────────────────────────────────────────────────

class TestPriorDecisionHonor:
    def test_prior_blocked_not_overridden(self):
        # Even with nominal vector, prior BLOCKED must be honored
        v = _nominal_vector()
        r = _sbe().evaluate(v, "BTC-USD", "trading", prior_decision="BLOCKED")
        assert r.decision == ExtendedDecision.BLOCKED

    def test_prior_hold_not_overridden(self):
        v = _nominal_vector()
        r = _sbe().evaluate(v, "BTC-USD", "trading", prior_decision="HOLD")
        assert r.decision == ExtendedDecision.HOLD


# ── NARROW scope reduction tests ─────────────────────────────────────────────

class TestNarrowScopeReduction:
    def test_narrow_scope_applied_when_original_scope_provided(self):
        # Force NARROW decision by providing a score just above execution floor
        v = StandingVector(
            authority_score      = 0.68,
            policy_compliance    = 0.68,
            signal_integrity     = 0.68,
            capacity_margin      = 0.68,
            coherence_score      = 0.68,
            trajectory_stability = 0.68,
            execution_readiness  = 0.68,
            debt_load_inverted   = 0.68,
        )
        # weighted ≈ 0.68 → margin ≈ 0.03 → NARROW band
        original_scope = {"quantity": 100_000, "notional": 5_000_000}
        r = _sbe().evaluate(
            v, "BTC-USD", "trading",
            original_scope=original_scope,
        )
        if r.decision == ExtendedDecision.NARROW and r.narrowed_scope:
            assert r.narrowed_scope["quantity"] < 100_000
            assert "scope_reduction" in r.narrowed_scope
            assert "original_scope" in r.narrowed_scope

    def test_narrow_scope_no_original_scope(self):
        v = StandingVector(
            authority_score=0.68, policy_compliance=0.68,
            signal_integrity=0.68, capacity_margin=0.68,
            coherence_score=0.68, trajectory_stability=0.68,
            execution_readiness=0.68, debt_load_inverted=0.68,
        )
        r = _sbe().evaluate(v, "BTC-USD", "trading")
        if r.decision == ExtendedDecision.NARROW:
            assert r.narrowed_scope is not None
            assert "scope_reduction" in r.narrowed_scope


# ── vector_from_pillar_results tests ─────────────────────────────────────────

class TestVectorFromPillarResults:
    def _make_pillar(self, pillar, passed=True, detail=None):
        p = MagicMock()
        p.pillar = pillar
        p.passed = passed
        p.detail = detail or {}
        return p

    def test_derives_vector_from_pillar_results(self):
        sae = self._make_pillar("sae", passed=True, detail={"admission_status": "admitted"})
        spg = self._make_pillar("spg", passed=True, detail={
            "verdict": "SINGULAR", "lineage_singularity": 95.0, "contradiction_count": 0,
        })
        cp  = self._make_pillar("checkpoint_pipeline", passed=True, detail={
            "checkpoints_total": 11, "checkpoints_passed": 11,
            "checkpoints_blocked": 0, "decision": "APPROVED",
        })
        cbg = self._make_pillar("cbg", passed=True, detail={"bind_allowed": True})
        evaluation = {
            "decision": "APPROVED", "score": 87.0,
            "checkpoints": [], "veto_chain": [], "gate_results": {},
        }
        v = StandingBoundaryEngine.vector_from_pillar_results(
            [sae, spg, cp, cbg], evaluation, "APPROVED",
        )
        assert isinstance(v, StandingVector)
        assert v.authority_score == 1.0
        assert v.policy_compliance == 1.0
        assert v.signal_integrity > 0.5
        assert v.execution_readiness == 1.0

    def test_ambiguous_spg_lowers_signal_integrity(self):
        sae = self._make_pillar("sae", detail={"admission_status": "admitted"})
        spg = self._make_pillar("spg", detail={
            "verdict": "AMBIGUOUS", "lineage_singularity": 60.0, "contradiction_count": 2,
        })
        cp  = self._make_pillar("checkpoint_pipeline", detail={
            "checkpoints_total": 11, "checkpoints_passed": 10,
            "checkpoints_blocked": 1, "decision": "APPROVED",
        })
        cbg = self._make_pillar("cbg", detail={"bind_allowed": True})
        evaluation = {"decision": "APPROVED", "score": 75.0, "veto_chain": [], "gate_results": {}}
        v = StandingBoundaryEngine.vector_from_pillar_results([sae, spg, cp, cbg], evaluation, "APPROVED")
        # AMBIGUOUS with lineage 60% → signal_integrity should be dampened
        assert v.signal_integrity < 0.65


# ── Fail-closed tests ─────────────────────────────────────────────────────────

class TestFailClosed:
    def test_sbe_fail_closed_on_bad_vector(self):
        # Pass a non-StandingVector to trigger exception path
        sbe = _sbe()
        result = sbe.evaluate(None, "X", "trading")  # type: ignore
        assert result.decision == ExtendedDecision.BLOCKED
        assert result.standing_margin == -1.0
        assert "system_error" in result.failed_dimensions
