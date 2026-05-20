"""
tests/test_ssd.py — ADR-175: Structural Shift Detector (SSD)

Tests for the Component Rank Stability Index (CRSI) algorithm, ring buffer
integrity, invariant enforcement, and AVMResult integration.

Signals: canonical 6 from ADR-076 (logic_consistency, probability_score,
risk_exposure, signal_coherence, stress_resilience, trend_persistence).

Topology design (signal VALUES passed to evaluate()):
  _TOPO_A  — top-3 by drift: risk_exposure(+50%), logic_consistency(+46%),
             probability_score(+35%). Other 3 near baseline (<2% each).
  _TOPO_B  — top-3 by drift: stress_resilience(+50%), trend_persistence(+38%),
             signal_coherence(+36%). Completely DISJOINT from TOPO_A top-3.
  _TOPO_MIX — top-3 by drift: logic_consistency(+46%), signal_coherence(+26%),
             risk_exposure(+20%). One signal in common with TOPO_A at rank-2.

Drift-component dicts (used for direct _detect_structural_shift calls, bypassing
GTPD probe contamination for precise algorithmic tests):
  _DC_TOPO_A  — drift values for TOPO_A top ordering
  _DC_TOPO_B  — drift values for TOPO_B top ordering (disjoint from A)
  _DC_TOPO_MIX — drift values giving CRSI=4/6=0.6667 vs TOPO_A history

Design principle for CRSI-sensitive tests: use _direct_detect() which populates
_component_history directly, bypassing evaluate() and GTPD probes that would add
extra history entries and shift the mean CRSI.

Invariants covered:
  SSD-INV-001  STRUCTURAL_SHIFT blocks auto_recalibrate_stale_domains()
  SSD-INV-002  Component history ring buffer is append-only
  SSD-INV-003  STRUCTURAL_SHIFT verdict requires >= SSD_MIN_CYCLES history
"""

import os
import sys
import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from omnix_core.governance.assumption_validity_monitor import (
    AssumptionValidityMonitor,
    StructuralShiftReport,
    SSD_TOP_K_COMPONENTS,
    SSD_MIN_CYCLES,
    SSD_STRUCTURAL_THRESHOLD,
    SSD_INSTABILITY_THRESHOLD,
    _SSD_HISTORY_SIZE,
    _component_history,
    _SSD_HISTORY_LOCK,
)

# ── Canonical signal VALUES (ADR-076) — passed to evaluate() ─────────────────
# Baseline (calibration): representative mid-range operational values
_CANON_BASELINE = {
    "logic_consistency": 65.0,
    "probability_score": 68.0,
    "risk_exposure":     60.0,
    "signal_coherence":  70.0,
    "stress_resilience": 62.0,
    "trend_persistence": 66.0,
}

# TOPO_A: top-3 by drift = {risk_exposure(50%), logic_consistency(46%), probability_score(35%)}
# Other 3 signals have drift < 2%.
_TOPO_A = {
    "logic_consistency": 95.0,   # (95-65)/65*100 = 46.2%
    "probability_score": 92.0,   # (92-68)/68*100 = 35.3%
    "risk_exposure":     90.0,   # (90-60)/60*100 = 50.0%   ← rank-1
    "signal_coherence":  71.0,   # (71-70)/70*100 =  1.4%
    "stress_resilience": 63.0,   # (63-62)/62*100 =  1.6%
    "trend_persistence": 67.0,   # (67-66)/66*100 =  1.5%
}

# TOPO_B: top-3 = {stress_resilience(50%), trend_persistence(38%), signal_coherence(36%)}
# Completely DISJOINT from TOPO_A top-3 → CRSI=0 when history is all TOPO_A.
_TOPO_B = {
    "logic_consistency": 66.0,   #  1.5% — near baseline
    "probability_score": 69.0,   #  1.5% — near baseline
    "risk_exposure":     61.0,   #  1.7% — near baseline
    "signal_coherence":  95.0,   # 35.7%   ← rank-3
    "stress_resilience": 93.0,   # 50.0%   ← rank-1
    "trend_persistence": 91.0,   # 37.9%   ← rank-2
}

# ── Drift-component dicts (used by _direct_detect) ───────────────────────────
# These are the DRIFT PERCENTAGES stored in _component_history entries.
# With TOPO_A signals and _CANON_BASELINE, AVM computes approx these drift vals:
_DC_TOPO_A = {
    "risk_exposure":     50.0,
    "logic_consistency": 46.2,
    "probability_score": 35.3,
    "signal_coherence":   1.4,
    "stress_resilience":  1.6,
    "trend_persistence":  1.5,
}
# → top-3: risk_exposure, logic_consistency, probability_score

_DC_TOPO_B = {
    "risk_exposure":      1.7,
    "logic_consistency":  1.5,
    "probability_score":  1.5,
    "signal_coherence":  35.7,
    "stress_resilience": 50.0,
    "trend_persistence": 37.9,
}
# → top-3: stress_resilience, trend_persistence, signal_coherence
# Completely disjoint from _DC_TOPO_A top-3 → CRSI=0.0

# TOPO_MIX current top-3: [logic_consistency(46.2), signal_coherence(25.7), risk_exposure(20.0)]
# vs TOPO_A hist set {risk_exposure, logic_consistency, probability_score}:
#   rank-0 logic_consistency (w=3): IN hist_set     → +3
#   rank-1 signal_coherence  (w=2): NOT in hist_set → +0
#   rank-2 risk_exposure     (w=1): IN hist_set     → +1
# CRSI per entry = 4/6 = 0.6667 → DRIFT_WITH_INSTABILITY (0.50 ≤ 0.6667 < 0.70)
_DC_TOPO_MIX = {
    "logic_consistency": 46.2,
    "signal_coherence":  25.7,
    "risk_exposure":     20.0,
    "probability_score":  1.5,
    "stress_resilience":  1.6,
    "trend_persistence":  1.5,
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_avm(drift_threshold: float = 20.0) -> AssumptionValidityMonitor:
    return AssumptionValidityMonitor(drift_threshold=drift_threshold)


def _calibrate(avm: AssumptionValidityMonitor, domain: str) -> None:
    avm.save_calibration_snapshot(
        domain=domain,
        baseline_signals=_CANON_BASELINE.copy(),
        description="SSD test baseline",
    )


def _evaluate(avm: AssumptionValidityMonitor, domain: str, signals: dict):
    return avm.evaluate(signals, domain)


def _fill_history(avm, domain, signals, n):
    """Run n evaluations to populate the component history ring buffer via evaluate()."""
    for _ in range(n):
        _evaluate(avm, domain, signals)


def _direct_detect(
    avm: AssumptionValidityMonitor,
    domain: str,
    history_entries: list[dict],
    current_drifts: dict,
) -> "StructuralShiftReport":
    """
    Directly populate _component_history and call _detect_structural_shift.
    Bypasses evaluate() and GTPD probes, giving precise algorithmic control.
    current_drifts is NOT pre-appended — caller controls history exactly.
    """
    with _SSD_HISTORY_LOCK:
        _component_history[domain] = [dict(e) for e in history_entries]
    return avm._detect_structural_shift(domain, current_drifts)


def _history_of(domain: str) -> list:
    """Read the current component history for a domain (module-level dict)."""
    with _SSD_HISTORY_LOCK:
        return list(_component_history.get(domain, []))


# ── Section 1: StructuralShiftReport dataclass ─────────────────────────────────

class TestStructuralShiftReportDataclass:
    def test_to_dict_contains_all_fields(self):
        report = StructuralShiftReport(
            ssd_id="SSD-ABCDEF1234",
            domain="market_risk",
            shift_class="STABLE",
            crsi=0.85,
            cycles_analyzed=5,
            dominant_components_current=["risk_exposure", "logic_consistency"],
            dominant_components_baseline=["risk_exposure", "logic_consistency"],
            emerged_components=[],
            receded_components=[],
            detected_at=datetime.now(timezone.utc).isoformat(),
        )
        d = report.to_dict()
        assert d["shift_class"] == "STABLE"
        assert d["crsi"] == 0.85
        assert d["cycles_analyzed"] == 5
        for key in ("ssd_id", "domain", "emerged_components", "receded_components",
                    "detected_at", "dominant_components_current", "dominant_components_baseline"):
            assert key in d, f"Missing key: {key}"

    def test_ssd_id_prefix(self):
        report = StructuralShiftReport(
            ssd_id="SSD-AB12CD34EF",
            domain="credit",
            shift_class="INSUFFICIENT_DATA",
            crsi=0.0,
            cycles_analyzed=0,
            dominant_components_current=[],
            dominant_components_baseline=[],
            emerged_components=[],
            receded_components=[],
            detected_at=datetime.now(timezone.utc).isoformat(),
        )
        assert report.ssd_id.startswith("SSD-")

    def test_all_shift_classes_valid(self):
        for cls in ("STABLE", "DRIFT_WITH_INSTABILITY", "STRUCTURAL_SHIFT", "INSUFFICIENT_DATA"):
            r = StructuralShiftReport(
                ssd_id="SSD-X", domain="d", shift_class=cls, crsi=0.5,
                cycles_analyzed=1, dominant_components_current=[],
                dominant_components_baseline=[], emerged_components=[],
                receded_components=[], detected_at="2026-01-01T00:00:00+00:00",
            )
            assert r.shift_class == cls


# ── Section 2: Cold start — INSUFFICIENT_DATA ─────────────────────────────────

class TestColdStart:
    def test_first_evaluate_gives_insufficient_data(self):
        avm = _make_avm()
        domain = f"cold_{uuid.uuid4().hex[:8]}"
        _calibrate(avm, domain)
        result = _evaluate(avm, domain, _TOPO_A.copy())
        ssd = result.structural_shift_report
        assert ssd["shift_class"] == "INSUFFICIENT_DATA"
        assert ssd["cycles_analyzed"] < SSD_MIN_CYCLES

    def test_fewer_than_min_cycles_always_insufficient(self):
        """Total SSD_MIN_CYCLES−1 evals → history still below threshold."""
        avm = _make_avm()
        domain = f"cold2_{uuid.uuid4().hex[:8]}"
        _calibrate(avm, domain)
        # SSD_MIN_CYCLES−2 fills + 1 final = SSD_MIN_CYCLES−1 total from evaluate().
        # GTPD probes also add entries — use direct detection for invariant verification.
        domain_d = f"cold2d_{uuid.uuid4().hex[:8]}"
        avm_d = _make_avm()
        n = SSD_MIN_CYCLES - 1
        hist = [_DC_TOPO_A.copy() for _ in range(n - 1)]
        report = _direct_detect(avm_d, domain_d, hist, _DC_TOPO_A.copy())
        assert report.shift_class == "INSUFFICIENT_DATA", (
            f"With {n-1} history entries (< {SSD_MIN_CYCLES}), "
            f"expected INSUFFICIENT_DATA, got {report.shift_class}"
        )

    def test_at_min_cycles_produces_non_insufficient(self):
        """Once history has >= SSD_MIN_CYCLES entries, a verdict is issued."""
        avm = _make_avm()
        domain = f"cold3_{uuid.uuid4().hex[:8]}"
        hist = [_DC_TOPO_A.copy() for _ in range(SSD_MIN_CYCLES)]
        report = _direct_detect(avm, domain, hist, _DC_TOPO_A.copy())
        assert report.shift_class != "INSUFFICIENT_DATA", (
            f"With {SSD_MIN_CYCLES} history entries, expected a real verdict"
        )

    def test_insufficient_data_has_empty_baseline_dominant(self):
        avm = _make_avm()
        domain = f"cold4_{uuid.uuid4().hex[:8]}"
        _calibrate(avm, domain)
        result = _evaluate(avm, domain, _TOPO_A.copy())
        assert result.structural_shift_report["dominant_components_baseline"] == []


# ── Section 3: STABLE classification ──────────────────────────────────────────

class TestStableClassification:
    def _stable_report(self, n_hist=None):
        """Direct detect: uniform TOPO_A history → STABLE."""
        n = n_hist or (SSD_MIN_CYCLES + 3)
        avm = _make_avm()
        domain = f"stable_{uuid.uuid4().hex[:8]}"
        hist = [_DC_TOPO_A.copy() for _ in range(n)]
        return _direct_detect(avm, domain, hist, _DC_TOPO_A.copy()), domain

    def test_consistent_topology_yields_stable(self):
        report, _ = self._stable_report()
        assert report.shift_class == "STABLE", (
            f"Expected STABLE, got {report.shift_class} (crsi={report.crsi:.4f})"
        )

    def test_stable_crsi_is_one(self):
        """Identical top-K every cycle → CRSI = 1.0."""
        report, _ = self._stable_report()
        assert report.crsi == 1.0, f"Expected CRSI=1.0, got {report.crsi:.4f}"

    def test_stable_has_empty_emerged_receded(self):
        report, _ = self._stable_report()
        assert report.emerged_components == []
        assert report.receded_components == []

    def test_stable_dominant_current_matches_topo_a_top3(self):
        """dominant_components_current should be the TOPO_A top-3 signals."""
        report, _ = self._stable_report()
        expected = {"risk_exposure", "logic_consistency", "probability_score"}
        actual = set(report.dominant_components_current)
        assert actual == expected, f"Expected top-3 {expected}, got {actual}"

    def test_stable_cycles_analyzed_equals_history_length(self):
        n = SSD_MIN_CYCLES + 4
        report, _ = self._stable_report(n_hist=n)
        assert report.cycles_analyzed == n


# ── Section 4: STRUCTURAL_SHIFT classification ────────────────────────────────

class TestStructuralShift:
    def _shift_report(self, n_hist=None):
        """Fill with TOPO_A history, current=TOPO_B → STRUCTURAL_SHIFT."""
        n = n_hist or (SSD_MIN_CYCLES + 3)
        avm = _make_avm()
        domain = f"shift_{uuid.uuid4().hex[:8]}"
        hist = [_DC_TOPO_A.copy() for _ in range(n)]
        return _direct_detect(avm, domain, hist, _DC_TOPO_B.copy()), domain

    def test_topology_change_yields_structural_shift(self):
        report, _ = self._shift_report()
        assert report.shift_class == "STRUCTURAL_SHIFT", (
            f"Expected STRUCTURAL_SHIFT, got {report.shift_class} "
            f"(crsi={report.crsi:.4f})"
        )

    def test_structural_shift_crsi_is_zero(self):
        """Disjoint top-3 (TOPO_A history vs TOPO_B current) → CRSI=0.0."""
        report, _ = self._shift_report()
        assert report.crsi == 0.0, (
            f"Expected CRSI=0.0 for disjoint topologies, got {report.crsi:.4f}"
        )

    def test_structural_shift_crsi_below_threshold(self):
        report, _ = self._shift_report()
        assert report.crsi < SSD_STRUCTURAL_THRESHOLD

    def test_structural_shift_reports_emerged_components(self):
        report, _ = self._shift_report()
        assert len(report.emerged_components) > 0

    def test_structural_shift_reports_receded_components(self):
        report, _ = self._shift_report()
        assert len(report.receded_components) > 0

    def test_structural_shift_cycles_analyzed_gte_min_cycles(self):
        report, _ = self._shift_report()
        assert report.cycles_analyzed >= SSD_MIN_CYCLES

    def test_topo_a_components_appear_in_receded(self):
        """Signals dominant in history (TOPO_A) must appear in receded list."""
        report, _ = self._shift_report()
        receded = set(report.receded_components)
        topo_a_top3 = {"risk_exposure", "logic_consistency", "probability_score"}
        assert len(receded & topo_a_top3) > 0, (
            f"Expected TOPO_A components in receded, got receded={receded}"
        )

    def test_topo_b_components_appear_in_emerged(self):
        """Signals dominant in current (TOPO_B) must appear in emerged list."""
        report, _ = self._shift_report()
        emerged = set(report.emerged_components)
        topo_b_top3 = {"stress_resilience", "trend_persistence", "signal_coherence"}
        assert len(emerged & topo_b_top3) > 0, (
            f"Expected TOPO_B components in emerged, got emerged={emerged}"
        )


# ── Section 5: DRIFT_WITH_INSTABILITY ─────────────────────────────────────────

class TestDriftWithInstability:
    def _instability_report(self, n_hist=None):
        """
        TOPO_A history + TOPO_MIX current → CRSI = 4/6 = 0.6667.
        Position-weighted overlap:
          rank-0 logic_consistency (w=3): IN hist_set  → +3
          rank-1 signal_coherence  (w=2): NOT in hist  → +0
          rank-2 risk_exposure     (w=1): IN hist_set  → +1
          Total = 4/6 = 0.6667 per entry → mean CRSI = 0.6667
        """
        n = n_hist or (SSD_MIN_CYCLES + 3)
        avm = _make_avm()
        domain = f"mix_{uuid.uuid4().hex[:8]}"
        hist = [_DC_TOPO_A.copy() for _ in range(n)]
        return _direct_detect(avm, domain, hist, _DC_TOPO_MIX.copy()), domain

    def test_partial_overlap_yields_drift_with_instability(self):
        report, _ = self._instability_report()
        assert report.shift_class == "DRIFT_WITH_INSTABILITY", (
            f"Expected DRIFT_WITH_INSTABILITY, got {report.shift_class} "
            f"(crsi={report.crsi:.4f}). "
            f"CRSI should be in [{SSD_STRUCTURAL_THRESHOLD}, {SSD_INSTABILITY_THRESHOLD})"
        )

    def test_instability_crsi_in_expected_range(self):
        report, _ = self._instability_report()
        assert SSD_STRUCTURAL_THRESHOLD <= report.crsi < SSD_INSTABILITY_THRESHOLD, (
            f"CRSI={report.crsi:.4f} not in "
            f"[{SSD_STRUCTURAL_THRESHOLD}, {SSD_INSTABILITY_THRESHOLD})"
        )

    def test_instability_crsi_exact_value(self):
        """CRSI must be exactly 4/6 = 0.6667 for TOPO_MIX vs uniform TOPO_A history."""
        report, _ = self._instability_report()
        expected = round(4.0 / 6.0, 4)
        assert report.crsi == expected, (
            f"Expected CRSI={expected}, got {report.crsi:.4f}"
        )


# ── Section 6: AVMResult integration ──────────────────────────────────────────

class TestAVMResultIntegration:
    def test_avm_result_always_has_structural_shift_report(self):
        avm = _make_avm()
        domain = f"intg_{uuid.uuid4().hex[:8]}"
        _calibrate(avm, domain)
        result = _evaluate(avm, domain, _TOPO_A.copy())
        assert result.structural_shift_report is not None
        assert isinstance(result.structural_shift_report, dict)

    def test_drift_block_result_includes_ssd_report(self):
        """DRIFT_BLOCK (is_valid=False) result must include structural_shift_report."""
        # drift_threshold=5 ensures TOPO_A's drift_score (~16%) triggers a block
        avm = _make_avm(drift_threshold=5.0)
        domain = f"block_{uuid.uuid4().hex[:8]}"
        _calibrate(avm, domain)
        result = _evaluate(avm, domain, _TOPO_A.copy())
        assert not result.is_valid, (
            f"Expected DRIFT_BLOCK but got is_valid=True "
            f"(drift_score={result.drift_score:.1f}, threshold={result.drift_threshold})"
        )
        assert result.structural_shift_report is not None
        assert "shift_class" in result.structural_shift_report

    def test_pass_result_includes_ssd_report(self):
        """PASS result (drift below threshold) must also include structural_shift_report."""
        avm = _make_avm(drift_threshold=50.0)  # high threshold → PASS
        domain = f"pass_{uuid.uuid4().hex[:8]}"
        _calibrate(avm, domain)
        result = _evaluate(avm, domain, _TOPO_A.copy())
        assert result.is_valid
        assert result.structural_shift_report is not None
        assert "shift_class" in result.structural_shift_report

    def test_ssd_report_has_all_required_keys(self):
        avm = _make_avm()
        domain = f"keys_{uuid.uuid4().hex[:8]}"
        _calibrate(avm, domain)
        result = _evaluate(avm, domain, _TOPO_A.copy())
        ssd = result.structural_shift_report
        required = {
            "ssd_id", "domain", "shift_class", "crsi", "cycles_analyzed",
            "dominant_components_current", "dominant_components_baseline",
            "emerged_components", "receded_components", "detected_at",
        }
        missing = required - set(ssd.keys())
        assert not missing, f"Missing keys: {missing}"

    def test_ssd_report_domain_matches_evaluated_domain(self):
        avm = _make_avm()
        domain = f"dom_{uuid.uuid4().hex[:8]}"
        _calibrate(avm, domain)
        result = _evaluate(avm, domain, _TOPO_A.copy())
        assert result.structural_shift_report["domain"] == domain

    def test_ssd_report_crsi_always_in_range(self):
        avm = _make_avm()
        domain = f"range_{uuid.uuid4().hex[:8]}"
        _calibrate(avm, domain)
        for signals in (_TOPO_A, _TOPO_B):
            result = _evaluate(avm, domain, signals.copy())
            ssd = result.structural_shift_report
            assert 0.0 <= ssd["crsi"] <= 1.0


# ── Section 7: SSD-INV-001 — STRUCTURAL_SHIFT blocks auto-recalibration ──────

class TestSSDInvariant001:
    def _force_structural_shift_domain(self, avm, domain):
        """Inject TOPO_A history then evaluate TOPO_B → STRUCTURAL_SHIFT via evaluate()."""
        _calibrate(avm, domain)
        _fill_history(avm, domain, _TOPO_A.copy(), SSD_MIN_CYCLES + 3)
        return _evaluate(avm, domain, _TOPO_B.copy())

    def test_ssd_inv001_blocks_auto_recalibration(self):
        """SSD-INV-001: auto_recalibrate must NOT call save_calibration_snapshot
        for any domain in STRUCTURAL_SHIFT state."""
        avm = _make_avm()
        domain = f"inv001_{uuid.uuid4().hex[:8]}"
        result = self._force_structural_shift_domain(avm, domain)
        ssd = result.structural_shift_report

        # Confirm precondition
        assert ssd["shift_class"] == "STRUCTURAL_SHIFT", (
            f"Precondition failed: expected STRUCTURAL_SHIFT, got {ssd['shift_class']} "
            f"(crsi={ssd['crsi']:.4f}). Cannot validate SSD-INV-001."
        )

        calls = []
        original_save = avm.save_calibration_snapshot

        def spy_save(*a, **kw):
            calls.append((a, kw))
            return original_save(*a, **kw)

        with patch.object(avm, "save_calibration_snapshot", side_effect=spy_save):
            avm.auto_recalibrate_stale_domains(recalib_interval_hours=0.0)

        assert len(calls) == 0, (
            f"SSD-INV-001 VIOLATED: auto_recalibrate_stale_domains called "
            f"save_calibration_snapshot {len(calls)} time(s) for domain in "
            f"STRUCTURAL_SHIFT state (crsi={ssd['crsi']:.4f})"
        )

    def test_ssd_inv001_log_contains_guard_identifier(self, caplog):
        """When SSD-INV-001 fires, the warning log must reference the invariant."""
        import logging
        avm = _make_avm()
        domain = f"inv001log_{uuid.uuid4().hex[:8]}"
        result = self._force_structural_shift_domain(avm, domain)
        if result.structural_shift_report["shift_class"] != "STRUCTURAL_SHIFT":
            pytest.skip("Could not force STRUCTURAL_SHIFT")

        with caplog.at_level(logging.WARNING):
            avm.auto_recalibrate_stale_domains(recalib_interval_hours=0.0)

        assert any("SSD-INV-001" in r.message for r in caplog.records), (
            "Expected SSD-INV-001 in warning log when auto-recalibration is blocked"
        )


# ── Section 8: SSD-INV-002 — Ring buffer append-only ─────────────────────────

class TestSSDInvariant002:
    def test_ring_buffer_grows_monotonically_to_cap(self):
        """Buffer size must grow monotonically and cap at _SSD_HISTORY_SIZE."""
        avm = _make_avm()
        domain = f"rb_{uuid.uuid4().hex[:8]}"
        _calibrate(avm, domain)

        sizes = []
        for _ in range(_SSD_HISTORY_SIZE + 5):
            _evaluate(avm, domain, _TOPO_A.copy())
            sizes.append(len(_history_of(domain)))

        # Monotonically non-decreasing up to cap
        for i in range(1, min(_SSD_HISTORY_SIZE, len(sizes))):
            assert sizes[i] >= sizes[i - 1], (
                f"Ring buffer decreased at index {i}: {sizes[i-1]} → {sizes[i]}"
            )

        # Never exceed cap
        assert max(sizes) <= _SSD_HISTORY_SIZE

    def test_ring_buffer_non_empty_after_first_eval(self):
        avm = _make_avm()
        domain = f"rb2_{uuid.uuid4().hex[:8]}"
        _calibrate(avm, domain)
        _evaluate(avm, domain, _TOPO_A.copy())
        assert len(_history_of(domain)) >= 1

    def test_ring_buffer_caps_at_history_size(self):
        """After _SSD_HISTORY_SIZE + N evals, history length stays at cap."""
        avm = _make_avm()
        domain = f"rb3_{uuid.uuid4().hex[:8]}"
        # Directly populate past the cap via _update_component_history
        with _SSD_HISTORY_LOCK:
            _component_history[domain] = [_DC_TOPO_A.copy() for _ in range(_SSD_HISTORY_SIZE + 5)]
            if len(_component_history[domain]) > _SSD_HISTORY_SIZE:
                _component_history[domain] = _component_history[domain][-_SSD_HISTORY_SIZE:]
        # Simulate one more append through the method
        extra_entry = _DC_TOPO_A.copy()
        avm_t = _make_avm()
        avm_t._update_component_history(domain, extra_entry)
        assert len(_history_of(domain)) == _SSD_HISTORY_SIZE

    def test_ring_buffer_evicts_oldest_entry(self):
        """When at cap, oldest entry is evicted (FIFO)."""
        avm = _make_avm()
        domain = f"rb4_{uuid.uuid4().hex[:8]}"
        # Fill to cap with TOPO_A entries
        with _SSD_HISTORY_LOCK:
            _component_history[domain] = [_DC_TOPO_A.copy() for _ in range(_SSD_HISTORY_SIZE)]
        # Append one TOPO_B entry
        avm._update_component_history(domain, _DC_TOPO_B.copy())
        history = _history_of(domain)
        assert len(history) == _SSD_HISTORY_SIZE
        # Last entry should be the TOPO_B entry (highest value: stress_resilience=50)
        last = history[-1]
        top_key = max(last, key=lambda k: last[k])
        assert top_key == "stress_resilience", (
            f"Last entry should reflect TOPO_B (stress_resilience dominant), got {top_key}"
        )


# ── Section 9: SSD-INV-003 — Min cycles before verdict ───────────────────────

class TestSSDInvariant003:
    def test_every_eval_below_min_cycles_gives_insufficient_data(self):
        """All evals with history < SSD_MIN_CYCLES must return INSUFFICIENT_DATA."""
        avm = _make_avm()
        domain = f"inv003_{uuid.uuid4().hex[:8]}"
        # Alternate disjoint topologies — maximum instability signal
        for i in range(SSD_MIN_CYCLES - 1):
            n_hist = i  # history has i entries when we call detect
            hist = [_DC_TOPO_A.copy() if j % 2 == 0 else _DC_TOPO_B.copy()
                    for j in range(n_hist)]
            report = _direct_detect(avm, domain, hist,
                                    _DC_TOPO_A.copy() if i % 2 == 0 else _DC_TOPO_B.copy())
            assert report.shift_class == "INSUFFICIENT_DATA", (
                f"SSD-INV-003 VIOLATED at history size {n_hist}: "
                f"expected INSUFFICIENT_DATA, got {report.shift_class}. "
                f"No verdict permitted until history has {SSD_MIN_CYCLES} entries."
            )

    def test_exactly_min_cycles_history_enables_verdict(self):
        """SSD_MIN_CYCLES entries in history → CRSI is computed (not INSUFFICIENT_DATA)."""
        avm = _make_avm()
        domain = f"inv003b_{uuid.uuid4().hex[:8]}"
        hist = [_DC_TOPO_A.copy() for _ in range(SSD_MIN_CYCLES)]
        report = _direct_detect(avm, domain, hist, _DC_TOPO_A.copy())
        assert report.shift_class != "INSUFFICIENT_DATA", (
            f"With history={SSD_MIN_CYCLES} entries, expected real verdict but got INSUFFICIENT_DATA"
        )

    def test_cycles_analyzed_equals_history_length(self):
        """cycles_analyzed must equal the number of history entries used."""
        avm = _make_avm()
        domain = f"inv003c_{uuid.uuid4().hex[:8]}"
        for n in range(1, SSD_MIN_CYCLES + 3):
            hist = [_DC_TOPO_A.copy() for _ in range(n)]
            report = _direct_detect(avm, domain, hist, _DC_TOPO_A.copy())
            assert report.cycles_analyzed == n, (
                f"cycles_analyzed={report.cycles_analyzed}, expected {n}"
            )


# ── Section 10: CRSI algorithm correctness ────────────────────────────────────

class TestCRSIAlgorithm:
    def test_crsi_always_in_zero_to_one(self):
        """CRSI is bounded in [0.0, 1.0] for any topology combination."""
        avm = _make_avm()
        domain = f"crsi_{uuid.uuid4().hex[:8]}"
        hist = [_DC_TOPO_A.copy() for _ in range(SSD_MIN_CYCLES + 2)]
        for current in (_DC_TOPO_A, _DC_TOPO_B, _DC_TOPO_MIX):
            report = _direct_detect(avm, domain, hist, current.copy())
            assert 0.0 <= report.crsi <= 1.0

    def test_perfect_consistency_crsi_is_one(self):
        """Identical top-K in every entry + current → CRSI = 1.0."""
        avm = _make_avm()
        domain = f"crsi_perfect_{uuid.uuid4().hex[:8]}"
        hist = [_DC_TOPO_A.copy() for _ in range(SSD_MIN_CYCLES + 5)]
        report = _direct_detect(avm, domain, hist, _DC_TOPO_A.copy())
        assert report.crsi == 1.0, f"Expected CRSI=1.0, got {report.crsi:.4f}"

    def test_total_disjoint_crsi_is_zero(self):
        """Completely disjoint top-K → CRSI = 0.0."""
        avm = _make_avm()
        domain = f"crsi_disjoint_{uuid.uuid4().hex[:8]}"
        hist = [_DC_TOPO_A.copy() for _ in range(SSD_MIN_CYCLES + 3)]
        report = _direct_detect(avm, domain, hist, _DC_TOPO_B.copy())
        assert report.crsi == 0.0, (
            f"Disjoint topologies should yield CRSI=0.0, got {report.crsi:.4f}"
        )

    def test_partial_overlap_exact_crsi(self):
        """TOPO_MIX vs TOPO_A history: position-weighted overlap = 4/6 = 0.6667."""
        avm = _make_avm()
        domain = f"crsi_partial_{uuid.uuid4().hex[:8]}"
        hist = [_DC_TOPO_A.copy() for _ in range(SSD_MIN_CYCLES + 4)]
        report = _direct_detect(avm, domain, hist, _DC_TOPO_MIX.copy())
        expected = round(4.0 / 6.0, 4)
        assert report.crsi == expected, (
            f"Expected CRSI={expected} for TOPO_MIX vs TOPO_A history, "
            f"got {report.crsi:.4f}"
        )

    def test_dominant_components_current_reflects_current_top3(self):
        """dominant_components_current must match top-K of current drift_components."""
        avm = _make_avm()
        domain = f"crsi_dom_{uuid.uuid4().hex[:8]}"
        hist = [_DC_TOPO_A.copy() for _ in range(3)]
        report = _direct_detect(avm, domain, hist, _DC_TOPO_A.copy())
        expected = {"risk_exposure", "logic_consistency", "probability_score"}
        actual = set(report.dominant_components_current)
        assert actual == expected, f"Expected {expected}, got {actual}"
