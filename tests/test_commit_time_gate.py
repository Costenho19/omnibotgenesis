"""
Tests for Commit-Time Admissibility Gate (CTAG) — ADR-140
MOD-016

Coverage:
    - VALID verdict: drift within tolerance
    - DRIFTED verdict: drift above caution, within revocation
    - REVOKED verdict: drift exceeds revocation threshold
    - INDETERMINATE: no original control provided
    - Fail-closed: exception → REVOKED
    - Elapsed seconds computed correctly
    - commit_authorized flag for each verdict
    - CTAGResult.to_dict: all fields present
    - get_schema: returns correct ADR and design note
"""

import time
import pytest
from omnix_core.governance.commit_time_gate import (
    CommitTimeAdmissibilityGate,
    CommitVerdict,
    CTAGResult,
    REVOCATION_DRIFT_THRESHOLD,
    CAUTION_DRIFT_THRESHOLD,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ctag():
    return CommitTimeAdmissibilityGate()


def _original_control(margin: float = 0.18, decision: str = "APPROVED") -> dict:
    return {
        "control_id":      "UDCL-TEST123",
        "decision":        decision,
        "standing_margin": margin,
        "issued_at":       time.time() - 300,   # 5 minutes ago
    }


# ── Verdict tests ─────────────────────────────────────────────────────────────

class TestVerdicts:
    def test_valid_verdict_no_drift(self):
        r = _ctag().evaluate(
            current_margin   = 0.18,
            original_control = _original_control(0.18),
        )
        assert r.verdict == CommitVerdict.VALID
        assert r.commit_authorized is True
        assert r.drift_delta == pytest.approx(0.0, abs=1e-6)

    def test_valid_verdict_positive_drift(self):
        # Conditions improved — always VALID
        r = _ctag().evaluate(
            current_margin   = 0.25,
            original_control = _original_control(0.18),
        )
        assert r.verdict == CommitVerdict.VALID
        assert r.commit_authorized is True
        assert r.drift_delta > 0

    def test_valid_verdict_small_negative_drift(self):
        # drift_delta = -0.03 — below caution threshold, still VALID
        r = _ctag().evaluate(
            current_margin   = 0.15,
            original_control = _original_control(0.18),
        )
        assert r.verdict == CommitVerdict.VALID
        assert r.commit_authorized is True
        assert r.drift_delta == pytest.approx(-0.03, abs=1e-6)

    def test_drifted_verdict(self):
        # drift_delta = -0.10 → CAUTION threshold crossed, within revocation
        r = _ctag().evaluate(
            current_margin   = 0.08,
            original_control = _original_control(0.18),
        )
        assert r.verdict == CommitVerdict.DRIFTED
        assert r.commit_authorized is True
        assert r.drift_delta == pytest.approx(-0.10, abs=1e-6)

    def test_drifted_verdict_at_caution_boundary(self):
        # drift_delta = exactly -CAUTION_DRIFT_THRESHOLD → DRIFTED
        r = _ctag().evaluate(
            current_margin   = 0.18 - CAUTION_DRIFT_THRESHOLD - 0.001,
            original_control = _original_control(0.18),
        )
        assert r.verdict == CommitVerdict.DRIFTED

    def test_revoked_verdict(self):
        # drift_delta = -0.20 → exceeds revocation threshold
        r = _ctag().evaluate(
            current_margin   = -0.02,
            original_control = _original_control(0.18),
        )
        assert r.verdict == CommitVerdict.REVOKED
        assert r.commit_authorized is False

    def test_revoked_at_threshold_boundary(self):
        # drift_delta = exactly -REVOCATION_DRIFT_THRESHOLD - epsilon → REVOKED
        r = _ctag().evaluate(
            current_margin   = 0.18 - REVOCATION_DRIFT_THRESHOLD - 0.001,
            original_control = _original_control(0.18),
        )
        assert r.verdict == CommitVerdict.REVOKED
        assert r.commit_authorized is False

    def test_indeterminate_no_original_control(self):
        r = _ctag().evaluate(current_margin=0.15)
        assert r.verdict == CommitVerdict.INDETERMINATE
        assert r.commit_authorized is True
        assert r.original_margin is None
        assert r.drift_delta is None

    def test_indeterminate_original_control_none(self):
        r = _ctag().evaluate(current_margin=0.10, original_control=None)
        assert r.verdict == CommitVerdict.INDETERMINATE
        assert r.commit_authorized is True


# ── CTAGResult fields tests ───────────────────────────────────────────────────

class TestCTAGResultFields:
    def test_to_dict_has_all_keys(self):
        r = _ctag().evaluate(
            current_margin   = 0.18,
            original_control = _original_control(0.18),
        )
        d = r.to_dict()
        for key in ("ctag_id", "verdict", "commit_authorized", "original_margin",
                    "current_margin", "drift_delta", "original_decision",
                    "original_control_id", "elapsed_seconds", "resolution_note",
                    "latency_ms", "adr"):
            assert key in d, f"Missing key: {key}"

    def test_adr_tag(self):
        r = _ctag().evaluate(current_margin=0.10, original_control=_original_control())
        assert r.adr == "ADR-140"

    def test_ctag_id_format(self):
        r = _ctag().evaluate(current_margin=0.10, original_control=_original_control())
        assert r.ctag_id.startswith("CTAG-")

    def test_elapsed_seconds_positive(self):
        # original_control issued 300 seconds ago
        r = _ctag().evaluate(
            current_margin   = 0.18,
            original_control = _original_control(0.18),
        )
        assert r.elapsed_seconds > 0

    def test_original_control_id_preserved(self):
        r = _ctag().evaluate(
            current_margin   = 0.18,
            original_control = _original_control(0.18),
        )
        assert r.original_control_id == "UDCL-TEST123"

    def test_current_margin_in_result(self):
        r = _ctag().evaluate(
            current_margin   = 0.12,
            original_control = _original_control(0.18),
        )
        assert r.current_margin == pytest.approx(0.12, abs=1e-6)


# ── Fail-closed tests ─────────────────────────────────────────────────────────

class TestFailClosed:
    def test_fail_closed_on_invalid_original_control(self):
        # Pass a non-dict as original_control to trigger exception path
        r = _ctag().evaluate(
            current_margin   = 0.10,
            original_control = "not-a-dict",   # type: ignore
        )
        assert r.verdict == CommitVerdict.REVOKED
        assert r.commit_authorized is False


# ── Schema tests ──────────────────────────────────────────────────────────────

class TestSchema:
    def test_get_schema_keys(self):
        s = CommitTimeAdmissibilityGate.get_schema()
        for key in ("module", "adr", "version", "description", "verdicts",
                    "drift_thresholds", "design_note"):
            assert key in s, f"Missing schema key: {key}"

    def test_get_schema_adr(self):
        s = CommitTimeAdmissibilityGate.get_schema()
        assert s["adr"] == "ADR-140"

    def test_get_schema_module(self):
        s = CommitTimeAdmissibilityGate.get_schema()
        assert s["module"] == "MOD-016"

    def test_drift_thresholds_in_schema(self):
        s = CommitTimeAdmissibilityGate.get_schema()
        assert s["drift_thresholds"]["revocation"] == REVOCATION_DRIFT_THRESHOLD
        assert s["drift_thresholds"]["caution"] == CAUTION_DRIFT_THRESHOLD

    def test_design_note_mentions_both_layers(self):
        s = CommitTimeAdmissibilityGate.get_schema()
        note = s["design_note"]
        assert "point-in-time" in note
        assert "continuous" in note


# ── Threshold value tests ─────────────────────────────────────────────────────

class TestThresholds:
    def test_revocation_threshold_value(self):
        assert REVOCATION_DRIFT_THRESHOLD == 0.15

    def test_caution_threshold_value(self):
        assert CAUTION_DRIFT_THRESHOLD == 0.05

    def test_caution_is_less_than_revocation(self):
        assert CAUTION_DRIFT_THRESHOLD < REVOCATION_DRIFT_THRESHOLD
