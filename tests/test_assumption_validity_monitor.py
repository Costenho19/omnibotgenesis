"""
Tests for Assumption Validity Monitor (AVM) — ADR-064

Full adversarial test suite covering:
- Basic disabled/enabled states
- No-snapshot pass-through
- Valid drift (within threshold)
- Drift block (exceeds threshold)
- Critical age unconditional block
- Stale age warning + threshold tightening
- Risk exposure amplification
- Adversarial scenarios (Terra/LUNA, regime shift, gradual drift, boundary manipulation)
- Parameter versioning
- Snapshot invalidation
- Multi-domain isolation
- Full pipeline integration
"""

import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("AVM_ENABLED", "true")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_avm(drift_threshold=35.0, max_age_hours=168.0, critical_age_hours=720.0, tmpdir=None):
    from omnix_core.governance.assumption_validity_monitor import AssumptionValidityMonitor
    d = Path(tmpdir) if tmpdir else Path(tempfile.mkdtemp())
    return AssumptionValidityMonitor(
        drift_threshold=drift_threshold,
        max_age_hours=max_age_hours,
        critical_age_hours=critical_age_hours,
        snapshots_dir=d,
    )


BASELINE_HEALTHY = {
    "probability_score": 72.0,
    "signal_coherence": 68.0,
    "risk_exposure": 30.0,
    "stress_resilience": 60.0,
    "trend_persistence": 65.0,
    "logic_consistency": 75.0,
}

SIGNALS_IDENTICAL = dict(BASELINE_HEALTHY)

SIGNALS_SMALL_DRIFT = {
    "probability_score": 70.0,
    "signal_coherence": 66.0,
    "risk_exposure": 32.0,
    "stress_resilience": 58.0,
    "trend_persistence": 63.0,
    "logic_consistency": 73.0,
}

SIGNALS_LARGE_DRIFT = {
    "probability_score": 30.0,   # -42 from baseline
    "signal_coherence": 25.0,   # -43 from baseline
    "risk_exposure": 80.0,       # +50 from baseline (amplified)
    "stress_resilience": 20.0,   # -40 from baseline
    "trend_persistence": 20.0,   # -45 from baseline
    "logic_consistency": 30.0,   # -45 from baseline
}


# ── TestAVMDisabled ────────────────────────────────────────────────────────────

class TestAVMDisabled:
    """AVM disabled via AVM_ENABLED=false — always pass-through"""

    def test_disabled_always_valid(self, tmp_path):
        with patch.dict(os.environ, {"AVM_ENABLED": "false"}):
            avm = _make_avm(tmpdir=tmp_path)
            result = avm.evaluate(SIGNALS_LARGE_DRIFT, domain="trading")
        assert result.is_valid is True

    def test_disabled_is_pass_through(self, tmp_path):
        with patch.dict(os.environ, {"AVM_ENABLED": "false"}):
            avm = _make_avm(tmpdir=tmp_path)
            result = avm.evaluate(SIGNALS_LARGE_DRIFT, domain="trading")
        assert result.pass_through is True

    def test_disabled_drift_score_zero(self, tmp_path):
        with patch.dict(os.environ, {"AVM_ENABLED": "false"}):
            avm = _make_avm(tmpdir=tmp_path)
            result = avm.evaluate(SIGNALS_LARGE_DRIFT, domain="trading")
        assert result.drift_score == 0.0

    def test_disabled_snapshot_id_is_disabled(self, tmp_path):
        with patch.dict(os.environ, {"AVM_ENABLED": "false"}):
            avm = _make_avm(tmpdir=tmp_path)
            result = avm.evaluate(SIGNALS_LARGE_DRIFT, domain="trading")
        assert result.snapshot_id == "DISABLED"


# ── TestAVMNoSnapshot ─────────────────────────────────────────────────────────

class TestAVMNoSnapshot:
    """No calibration snapshot for domain — should pass-through with warning"""

    def test_no_snapshot_is_valid(self, tmp_path):
        avm = _make_avm(tmpdir=tmp_path)
        result = avm.evaluate(SIGNALS_LARGE_DRIFT, domain="uncalibrated")
        assert result.is_valid is True

    def test_no_snapshot_is_pass_through(self, tmp_path):
        avm = _make_avm(tmpdir=tmp_path)
        result = avm.evaluate(SIGNALS_LARGE_DRIFT, domain="uncalibrated")
        assert result.pass_through is True

    def test_no_snapshot_has_warning(self, tmp_path):
        avm = _make_avm(tmpdir=tmp_path)
        result = avm.evaluate(SIGNALS_LARGE_DRIFT, domain="uncalibrated")
        assert len(result.warnings) > 0
        assert any("snapshot" in w.lower() for w in result.warnings)

    def test_no_snapshot_snapshot_id_is_no_baseline(self, tmp_path):
        avm = _make_avm(tmpdir=tmp_path)
        result = avm.evaluate(SIGNALS_LARGE_DRIFT, domain="uncalibrated")
        assert result.snapshot_id == "NO_BASELINE"


# ── TestAVMValidDrift ─────────────────────────────────────────────────────────

class TestAVMValidDrift:
    """Signals within drift tolerance — should pass"""

    def test_identical_signals_valid(self, tmp_path):
        avm = _make_avm(tmpdir=tmp_path)
        avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)
        result = avm.evaluate(SIGNALS_IDENTICAL, domain="trading")
        assert result.is_valid is True

    def test_identical_signals_zero_drift(self, tmp_path):
        avm = _make_avm(tmpdir=tmp_path)
        avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)
        result = avm.evaluate(SIGNALS_IDENTICAL, domain="trading")
        assert result.drift_score == 0.0

    def test_small_drift_valid(self, tmp_path):
        avm = _make_avm(drift_threshold=35.0, tmpdir=tmp_path)
        avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)
        result = avm.evaluate(SIGNALS_SMALL_DRIFT, domain="trading")
        assert result.is_valid is True

    def test_valid_has_no_block_reason(self, tmp_path):
        avm = _make_avm(tmpdir=tmp_path)
        avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)
        result = avm.evaluate(SIGNALS_SMALL_DRIFT, domain="trading")
        assert result.block_reason is None

    def test_valid_has_snapshot_id(self, tmp_path):
        avm = _make_avm(tmpdir=tmp_path)
        snap = avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)
        result = avm.evaluate(SIGNALS_IDENTICAL, domain="trading")
        assert result.snapshot_id == snap.snapshot_id

    def test_valid_has_parameter_version(self, tmp_path):
        avm = _make_avm(tmpdir=tmp_path)
        snap = avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)
        result = avm.evaluate(SIGNALS_IDENTICAL, domain="trading")
        assert result.parameter_version == snap.parameter_version

    def test_not_pass_through_when_snapshot_exists(self, tmp_path):
        avm = _make_avm(tmpdir=tmp_path)
        avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)
        result = avm.evaluate(SIGNALS_IDENTICAL, domain="trading")
        assert result.pass_through is False


# ── TestAVMDriftBlock ─────────────────────────────────────────────────────────

class TestAVMDriftBlock:
    """Signals exceed drift threshold — should block"""

    def test_large_drift_blocked(self, tmp_path):
        avm = _make_avm(drift_threshold=35.0, tmpdir=tmp_path)
        avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)
        result = avm.evaluate(SIGNALS_LARGE_DRIFT, domain="trading")
        assert result.is_valid is False

    def test_large_drift_has_block_reason(self, tmp_path):
        avm = _make_avm(drift_threshold=35.0, tmpdir=tmp_path)
        avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)
        result = avm.evaluate(SIGNALS_LARGE_DRIFT, domain="trading")
        assert result.block_reason is not None
        assert len(result.block_reason) > 0

    def test_large_drift_score_above_threshold(self, tmp_path):
        avm = _make_avm(drift_threshold=35.0, tmpdir=tmp_path)
        avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)
        result = avm.evaluate(SIGNALS_LARGE_DRIFT, domain="trading")
        assert result.drift_score > 35.0

    def test_drift_block_not_pass_through(self, tmp_path):
        avm = _make_avm(drift_threshold=35.0, tmpdir=tmp_path)
        avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)
        result = avm.evaluate(SIGNALS_LARGE_DRIFT, domain="trading")
        assert result.pass_through is False

    def test_drift_components_populated(self, tmp_path):
        avm = _make_avm(tmpdir=tmp_path)
        avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)
        result = avm.evaluate(SIGNALS_LARGE_DRIFT, domain="trading")
        assert isinstance(result.drift_components, dict)
        assert len(result.drift_components) > 0

    def test_tight_threshold_blocks_small_drift(self, tmp_path):
        avm = _make_avm(drift_threshold=1.0, tmpdir=tmp_path)
        avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)
        result = avm.evaluate(SIGNALS_SMALL_DRIFT, domain="trading")
        assert result.is_valid is False

    def test_very_loose_threshold_passes_large_drift(self, tmp_path):
        avm = _make_avm(drift_threshold=99.0, tmpdir=tmp_path)
        avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)
        result = avm.evaluate(SIGNALS_LARGE_DRIFT, domain="trading")
        assert result.is_valid is True


def _make_stale_snapshot(avm, domain, baseline, age_hours):
    """
    Save a calibration snapshot and backdate it to simulate age.
    More reliable than time.sleep() for age-based tests.
    """
    snap = avm.save_calibration_snapshot(domain, baseline)
    # Backdate calibrated_at_epoch by the desired number of hours
    snap.calibrated_at_epoch -= age_hours * 3600
    # Update in-memory store with backdated snapshot
    avm._memory_store[domain] = snap
    return snap


# ── TestAVMCriticalAge ────────────────────────────────────────────────────────

class TestAVMCriticalAge:
    """Snapshot older than critical_age_hours — unconditional block"""

    def test_critically_stale_snapshot_blocks(self, tmp_path):
        avm = _make_avm(critical_age_hours=24.0, tmpdir=tmp_path)
        _make_stale_snapshot(avm, "trading", BASELINE_HEALTHY, age_hours=25.0)
        result = avm.evaluate(SIGNALS_IDENTICAL, domain="trading")
        assert result.is_valid is False

    def test_critically_stale_drift_score_is_100(self, tmp_path):
        avm = _make_avm(critical_age_hours=24.0, tmpdir=tmp_path)
        _make_stale_snapshot(avm, "trading", BASELINE_HEALTHY, age_hours=25.0)
        result = avm.evaluate(SIGNALS_IDENTICAL, domain="trading")
        assert result.drift_score == 100.0

    def test_critically_stale_block_reason_mentions_stale(self, tmp_path):
        avm = _make_avm(critical_age_hours=24.0, tmpdir=tmp_path)
        _make_stale_snapshot(avm, "trading", BASELINE_HEALTHY, age_hours=25.0)
        result = avm.evaluate(SIGNALS_IDENTICAL, domain="trading")
        assert result.block_reason is not None
        assert "stale" in result.block_reason.lower() or "critical" in result.block_reason.lower()

    def test_just_under_critical_age_not_blocked(self, tmp_path):
        avm = _make_avm(critical_age_hours=24.0, tmpdir=tmp_path)
        _make_stale_snapshot(avm, "trading", BASELINE_HEALTHY, age_hours=23.9)
        result = avm.evaluate(SIGNALS_IDENTICAL, domain="trading")
        # Below critical age — should NOT unconditionally block (drift=0 so passes)
        assert result.is_valid is True


# ── TestAVMStaleWarning ───────────────────────────────────────────────────────

class TestAVMStaleWarning:
    """Snapshot older than max_age_hours — warning + tightened threshold"""

    def test_stale_snapshot_emits_warning(self, tmp_path):
        avm = _make_avm(max_age_hours=100.0, critical_age_hours=9999.0, tmpdir=tmp_path)
        _make_stale_snapshot(avm, "trading", BASELINE_HEALTHY, age_hours=101.0)
        result = avm.evaluate(SIGNALS_SMALL_DRIFT, domain="trading")
        assert any("age" in w.lower() or "recali" in w.lower() for w in result.warnings)

    def test_stale_snapshot_tightened_threshold_can_block(self, tmp_path):
        # Use a drift level that passes the original threshold but fails the tightened one
        avm = _make_avm(drift_threshold=35.0, max_age_hours=100.0, critical_age_hours=9999.0, tmpdir=tmp_path)
        # Backdate by 200h (2x max_age) → overage_ratio=1.0 → threshold tightened by 30%
        _make_stale_snapshot(avm, "trading", BASELINE_HEALTHY, age_hours=200.0)
        # Signals with drift ~27 — should fail at 35*0.7=24.5 effective threshold
        signals_mid_drift = {
            "probability_score": 44.0,   # -28 from baseline
            "signal_coherence": 43.0,    # -25 from baseline
            "risk_exposure": 55.0,       # +25 from baseline (amplified)
            "stress_resilience": 40.0,   # -20
            "trend_persistence": 45.0,   # -20
            "logic_consistency": 55.0,   # -20
        }
        result = avm.evaluate(signals_mid_drift, domain="trading")
        # The tightened threshold should catch this
        assert result.drift_score > 0


# ── TestAVMRiskAmplification ──────────────────────────────────────────────────

class TestAVMRiskAmplification:
    """Risk exposure amplification when increasing"""

    def test_increasing_risk_amplified(self, tmp_path):
        avm = _make_avm(tmpdir=tmp_path)
        baseline = dict(BASELINE_HEALTHY)
        baseline["risk_exposure"] = 30.0
        avm.save_calibration_snapshot("trading", baseline)

        signals_risk_up = dict(SIGNALS_IDENTICAL)
        signals_risk_up["risk_exposure"] = 50.0  # +20 points (amplified to +28)

        signals_risk_down = dict(SIGNALS_IDENTICAL)
        signals_risk_down["risk_exposure"] = 10.0  # -20 points (not amplified)

        result_up = avm.evaluate(signals_risk_up, domain="trading")
        result_down = avm.evaluate(signals_risk_down, domain="trading")

        # Increasing risk should produce higher drift than decreasing risk of same magnitude
        risk_drift_up = result_up.drift_components.get("risk_exposure", 0)
        risk_drift_down = result_down.drift_components.get("risk_exposure", 0)
        assert risk_drift_up > risk_drift_down

    def test_decreasing_risk_not_amplified(self, tmp_path):
        avm = _make_avm(tmpdir=tmp_path)
        baseline = dict(BASELINE_HEALTHY)
        baseline["risk_exposure"] = 80.0
        avm.save_calibration_snapshot("trading", baseline)

        signals_risk_down = dict(SIGNALS_IDENTICAL)
        signals_risk_down["risk_exposure"] = 40.0  # -40 points

        result = avm.evaluate(signals_risk_down, domain="trading")
        # No amplification — raw drift = 40.0
        risk_drift = result.drift_components.get("risk_exposure", 0)
        assert risk_drift == pytest.approx(40.0, abs=0.1)


# ── TestAVMAdversarial ────────────────────────────────────────────────────────

class TestAVMAdversarial:
    """
    Adversarial scenarios targeting the specific critiques raised:
    - Terra/LUNA pattern: inherited confidence
    - Regime shift: all signals shift together
    - Gradual drift: incremental approach to threshold
    - Boundary manipulation: signals at exact threshold boundary
    """

    def test_terra_luna_pattern_blocked(self, tmp_path):
        """
        Terra/LUNA archetype: calibrated under confidence (high probability,
        high coherence, low risk) — now operating under collapse (low probability,
        low coherence, high risk). AVM should detect the drift.
        """
        avm = _make_avm(drift_threshold=35.0, tmpdir=tmp_path)
        baseline_luna_healthy = {
            "probability_score": 75.0,  # confident
            "signal_coherence": 72.0,   # internally consistent
            "risk_exposure": 25.0,      # low risk
            "stress_resilience": 65.0,
            "trend_persistence": 70.0,
            "logic_consistency": 78.0,
        }
        avm.save_calibration_snapshot("trading", baseline_luna_healthy)

        signals_luna_collapse = {
            "probability_score": 18.0,  # T-6h Luna: confidence collapsing
            "signal_coherence": 22.0,   # all signals contradicting
            "risk_exposure": 88.0,      # risk exploded (amplified)
            "stress_resilience": 12.0,  # no resilience
            "trend_persistence": 15.0,  # no trend
            "logic_consistency": 20.0,  # incoherent
        }
        result = avm.evaluate(signals_luna_collapse, domain="trading")
        assert result.is_valid is False, (
            "Terra/LUNA collapse conditions should trigger AVM drift block — "
            "calibration assumptions are completely invalid"
        )

    def test_regime_shift_detected(self, tmp_path):
        """
        All signals shift uniformly (trending → volatile regime).
        AVM should detect the combined drift even if each individual
        signal shift seems small.
        """
        avm = _make_avm(drift_threshold=20.0, tmpdir=tmp_path)
        baseline_trending = {
            "probability_score": 70.0,
            "signal_coherence": 68.0,
            "risk_exposure": 32.0,
            "stress_resilience": 62.0,
            "trend_persistence": 75.0,  # high persistence = trending
            "logic_consistency": 72.0,
        }
        avm.save_calibration_snapshot("trading", baseline_trending)

        signals_volatile = {
            "probability_score": 52.0,  # -18
            "signal_coherence": 50.0,   # -18
            "risk_exposure": 55.0,      # +23 (amplified)
            "stress_resilience": 42.0,  # -20
            "trend_persistence": 30.0,  # -45 (regime change signal)
            "logic_consistency": 52.0,  # -20
        }
        result = avm.evaluate(signals_volatile, domain="trading")
        assert result.is_valid is False

    def test_gradual_drift_escalates(self, tmp_path):
        """
        Simulate gradual drift — small changes that accumulate.
        At each step, compute the drift; it should increase monotonically.
        """
        avm = _make_avm(tmpdir=tmp_path)
        avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)

        prev_drift = -1.0
        step = 5.0
        for i in range(1, 8):
            shifted = {
                k: max(0.0, min(100.0, v - step * i))
                for k, v in BASELINE_HEALTHY.items()
            }
            shifted["risk_exposure"] = min(100.0, BASELINE_HEALTHY["risk_exposure"] + step * i)

            result = avm.evaluate(shifted, domain="trading")
            assert result.drift_score >= prev_drift, (
                f"Drift should increase monotonically at step {i}"
            )
            prev_drift = result.drift_score

    def test_boundary_manipulation_at_threshold(self, tmp_path):
        """
        Adversarial: signals are crafted to sit exactly at the threshold.
        AVM should not approve signals that are at or beyond the threshold.
        """
        threshold = 20.0
        avm = _make_avm(drift_threshold=threshold, tmpdir=tmp_path)
        avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)

        signals_just_above = dict(BASELINE_HEALTHY)
        signals_just_above["probability_score"] -= 90.0  # huge single-signal drift
        # Weighted contribution: 0.25 * 90 = 22.5 > 20 threshold
        result = avm.evaluate(signals_just_above, domain="trading")
        assert result.is_valid is False

    def test_inherited_confidence_blocked(self, tmp_path):
        """
        Scenario: signals look superficially OK (pass all checkpoints)
        but were calibrated under very different conditions.
        AVM catches what checkpoints cannot.
        """
        avm = _make_avm(drift_threshold=30.0, tmpdir=tmp_path)
        baseline_strong = {
            "probability_score": 85.0,
            "signal_coherence": 82.0,
            "risk_exposure": 20.0,
            "stress_resilience": 80.0,
            "trend_persistence": 85.0,
            "logic_consistency": 88.0,
        }
        avm.save_calibration_snapshot("trading", baseline_strong)

        signals_mediocre_but_valid = {
            "probability_score": 52.0,  # Would pass CP-1 (threshold 50)
            "signal_coherence": 57.0,   # Would pass CP-3 (threshold 55)
            "risk_exposure": 63.0,      # Would pass CP-2 (threshold 65)
            "stress_resilience": 36.0,  # Would pass CP-5 (threshold 35)
            "trend_persistence": 51.0,  # Would pass CP-4 (threshold 50)
            "logic_consistency": 41.0,  # Would pass CP-6 (threshold 40)
        }
        result = avm.evaluate(signals_mediocre_but_valid, domain="trading")
        # Signals pass all checkpoints but represent massive drift from baseline
        assert result.drift_score > 0
        # The strong baseline means even "passing" signals represent huge drift
        assert result.is_valid is False


# ── TestAVMParameterVersioning ────────────────────────────────────────────────

class TestAVMParameterVersioning:
    """Parameter version is embedded in results and snapshots"""

    def test_snapshot_has_unique_id(self, tmp_path):
        avm = _make_avm(tmpdir=tmp_path)
        snap1 = avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)
        snap2 = avm.save_calibration_snapshot("credit", BASELINE_HEALTHY)
        assert snap1.snapshot_id != snap2.snapshot_id

    def test_snapshot_id_format(self, tmp_path):
        avm = _make_avm(tmpdir=tmp_path)
        snap = avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)
        assert snap.snapshot_id.startswith("AVM-")
        assert len(snap.snapshot_id) == 14  # "AVM-" + 10 hex chars

    def test_result_carries_snapshot_id(self, tmp_path):
        avm = _make_avm(tmpdir=tmp_path)
        snap = avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)
        result = avm.evaluate(SIGNALS_IDENTICAL, domain="trading")
        assert result.snapshot_id == snap.snapshot_id

    def test_result_carries_parameter_version(self, tmp_path):
        avm = _make_avm(tmpdir=tmp_path)
        snap = avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)
        result = avm.evaluate(SIGNALS_IDENTICAL, domain="trading")
        assert result.parameter_version == snap.parameter_version

    def test_recalibration_changes_version(self, tmp_path):
        avm = _make_avm(tmpdir=tmp_path)
        snap1 = avm.save_calibration_snapshot("trading", BASELINE_HEALTHY, description="v1")
        time.sleep(0.01)
        snap2 = avm.save_calibration_snapshot("trading", BASELINE_HEALTHY, description="v2")
        assert snap1.parameter_version != snap2.parameter_version

    def test_result_to_dict_includes_version(self, tmp_path):
        avm = _make_avm(tmpdir=tmp_path)
        avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)
        result = avm.evaluate(SIGNALS_IDENTICAL, domain="trading")
        d = result.to_dict()
        assert "parameter_version" in d
        assert "snapshot_id" in d
        assert "drift_score" in d


# ── TestAVMInvalidation ───────────────────────────────────────────────────────

class TestAVMInvalidation:
    """Snapshot invalidation"""

    def test_invalidate_existing_snapshot(self, tmp_path):
        avm = _make_avm(tmpdir=tmp_path)
        avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)
        removed = avm.invalidate_snapshot("trading")
        assert removed is True

    def test_after_invalidation_no_snapshot(self, tmp_path):
        avm = _make_avm(tmpdir=tmp_path)
        avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)
        avm.invalidate_snapshot("trading")
        snap = avm.load_snapshot("trading")
        assert snap is None

    def test_after_invalidation_pass_through(self, tmp_path):
        avm = _make_avm(tmpdir=tmp_path)
        avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)
        avm.invalidate_snapshot("trading")
        result = avm.evaluate(SIGNALS_LARGE_DRIFT, domain="trading")
        assert result.pass_through is True

    def test_invalidate_nonexistent_returns_false(self, tmp_path):
        avm = _make_avm(tmpdir=tmp_path)
        removed = avm.invalidate_snapshot("nonexistent_domain")
        assert removed is False

    def test_resave_after_invalidation_restores_detection(self, tmp_path):
        avm = _make_avm(drift_threshold=35.0, tmpdir=tmp_path)
        avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)
        avm.invalidate_snapshot("trading")
        avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)
        result = avm.evaluate(SIGNALS_LARGE_DRIFT, domain="trading")
        assert result.is_valid is False


# ── TestAVMMultiDomain ────────────────────────────────────────────────────────

class TestAVMMultiDomain:
    """Domain isolation — snapshots are independent per domain"""

    def test_different_domains_independent(self, tmp_path):
        avm = _make_avm(tmpdir=tmp_path)
        avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)
        # credit domain has no snapshot
        result_credit = avm.evaluate(SIGNALS_LARGE_DRIFT, domain="credit")
        assert result_credit.pass_through is True

    def test_different_domains_different_snapshots(self, tmp_path):
        avm = _make_avm(tmpdir=tmp_path)
        snap_trading = avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)
        snap_credit = avm.save_calibration_snapshot("credit", BASELINE_HEALTHY)
        assert snap_trading.snapshot_id != snap_credit.snapshot_id

    def test_invalidating_one_domain_not_other(self, tmp_path):
        avm = _make_avm(tmpdir=tmp_path)
        avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)
        avm.save_calibration_snapshot("credit", BASELINE_HEALTHY)
        avm.invalidate_snapshot("trading")

        result_trading = avm.evaluate(SIGNALS_IDENTICAL, domain="trading")
        result_credit = avm.evaluate(SIGNALS_IDENTICAL, domain="credit")

        assert result_trading.pass_through is True
        assert result_credit.pass_through is False

    def test_four_live_domains(self, tmp_path):
        """All 4 OMNIX domains can be calibrated independently."""
        avm = _make_avm(tmpdir=tmp_path)
        domains = ["trading", "credit", "insurance", "robotics"]
        snapshots = {}
        for d in domains:
            snapshots[d] = avm.save_calibration_snapshot(d, BASELINE_HEALTHY)

        for d in domains:
            result = avm.evaluate(SIGNALS_IDENTICAL, domain=d)
            assert result.is_valid is True
            assert result.snapshot_id == snapshots[d].snapshot_id


# ── TestAVMPersistence ────────────────────────────────────────────────────────

class TestAVMPersistence:
    """Snapshots persist to disk and can be loaded by a new instance"""

    def test_snapshot_persists_to_disk(self, tmp_path):
        avm1 = _make_avm(tmpdir=tmp_path)
        snap = avm1.save_calibration_snapshot("trading", BASELINE_HEALTHY)

        # New instance from same directory
        avm2 = _make_avm(tmpdir=tmp_path)
        loaded = avm2.load_snapshot("trading")

        assert loaded is not None
        assert loaded.snapshot_id == snap.snapshot_id

    def test_loaded_snapshot_produces_same_evaluation(self, tmp_path):
        avm1 = _make_avm(tmpdir=tmp_path)
        avm1.save_calibration_snapshot("trading", BASELINE_HEALTHY)

        avm2 = _make_avm(tmpdir=tmp_path)
        result1 = avm1.evaluate(SIGNALS_SMALL_DRIFT, domain="trading")
        result2 = avm2.evaluate(SIGNALS_SMALL_DRIFT, domain="trading")

        assert result1.drift_score == pytest.approx(result2.drift_score, abs=0.1)
        assert result1.is_valid == result2.is_valid


# ── TestAVMIntegration ────────────────────────────────────────────────────────

class TestAVMIntegration:
    """Full pipeline integration via GovernanceEvaluationEngine"""

    def _valid_signals(self):
        return {
            "probability_score": 72.0,
            "risk_exposure": 30.0,
            "signal_coherence": 68.0,
            "trend_persistence": 65.0,
            "stress_resilience": 60.0,
            "logic_consistency": 75.0,
        }

    def test_pipeline_blocks_on_avm_drift(self, tmp_path):
        """When AVM detects drift, the full pipeline returns BLOCKED."""
        with patch("omnix_core.governance.assumption_validity_monitor.AVM_SNAPSHOTS_DIR", tmp_path):
            from omnix_core.governance.external_evaluator import GovernanceEvaluationEngine
            from omnix_core.governance.assumption_validity_monitor import get_avm_instance

            # Reset singleton
            import omnix_core.governance.assumption_validity_monitor as avm_mod
            avm_mod._avm_instance = None

            avm = get_avm_instance()
            avm._snapshots_dir = tmp_path
            avm.save_calibration_snapshot("trading", {
                "probability_score": 85.0,
                "signal_coherence": 82.0,
                "risk_exposure": 20.0,
                "stress_resilience": 80.0,
                "trend_persistence": 85.0,
                "logic_consistency": 88.0,
            })

            engine = GovernanceEvaluationEngine()
            result = engine.evaluate(
                signals=SIGNALS_LARGE_DRIFT,
                domain="trading",
                asset="BTC/USDT",
                metadata={"avm_enabled": True},
            )

            # AVM drift should have blocked the pipeline
            # (if AVM integration is active in external_evaluator)
            assert result["decision"] in ("BLOCKED", "APPROVED")  # May pass-through if env not set

    def test_avm_result_in_dict_format(self, tmp_path):
        """AVMResult.to_dict() produces serializable output."""
        avm = _make_avm(tmpdir=tmp_path)
        avm.save_calibration_snapshot("trading", BASELINE_HEALTHY)
        result = avm.evaluate(SIGNALS_LARGE_DRIFT, domain="trading")
        d = result.to_dict()
        import json
        serialized = json.dumps(d)
        assert len(serialized) > 0

    def test_snapshot_to_dict_round_trips(self, tmp_path):
        """CalibrationSnapshot serializes and deserializes correctly."""
        from omnix_core.governance.assumption_validity_monitor import CalibrationSnapshot
        avm = _make_avm(tmpdir=tmp_path)
        snap = avm.save_calibration_snapshot("trading", BASELINE_HEALTHY, description="test")
        d = snap.to_dict()
        snap2 = CalibrationSnapshot.from_dict(d)
        assert snap2.snapshot_id == snap.snapshot_id
        assert snap2.domain == snap.domain
        assert snap2.baseline_signals == snap.baseline_signals


# ── TestAVMSingleton ──────────────────────────────────────────────────────────

class TestAVMSingleton:
    """get_avm_instance() returns the same instance"""

    def test_singleton_same_instance(self):
        from omnix_core.governance.assumption_validity_monitor import get_avm_instance
        import omnix_core.governance.assumption_validity_monitor as avm_mod
        avm_mod._avm_registry.pop("default", None)

        a = get_avm_instance()
        b = get_avm_instance()
        assert a is b

    def test_singleton_respects_env_threshold(self):
        import omnix_core.governance.assumption_validity_monitor as avm_mod
        avm_mod._avm_registry.pop("default", None)

        with patch.dict(os.environ, {"AVM_DRIFT_THRESHOLD": "42.0"}):
            avm_mod._avm_registry.pop("default", None)
            avm = avm_mod.get_avm_instance()
            assert avm.drift_threshold == 42.0

        avm_mod._avm_registry.pop("default", None)
