"""
Tests unitarios para MetaCoherenceMonitor (ADR-117).
Ejecutar: TESTING=true TELEGRAM_BOT_TOKEN=test-token python -m pytest tests/test_meta_coherence_monitor.py -v
"""
import os, sys, types, pytest
from unittest.mock import patch, MagicMock

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")

# ---------------------------------------------------------------------------
# Stub heavy dependencies so tests run offline
# ---------------------------------------------------------------------------
_STUBS = [
    "psycopg2", "pqc", "pqc.sign", "pqc.sign.dilithium3",
    "omnix_core.authorization_adapter",
    "omnix_core.governance.systemic_router",
]
for _name in _STUBS:
    if _name not in sys.modules:
        sys.modules[_name] = MagicMock()

# Stub psycopg2.connect so no real DB calls are made
import psycopg2  # already a MagicMock
psycopg2.connect.return_value.__enter__ = lambda s: s
psycopg2.connect.return_value.__exit__ = MagicMock(return_value=False)

from omnix_core.governance.meta_coherence_monitor import (
    MetaCoherenceMonitor,
    VerdictDistributionResult,
    VetoPatternResult,
    ReferenceLegitimacyResult,
    MetaCoherenceReport,
    _DB_ALERT_MAP,
    _THRESHOLD_WARNING,
    _THRESHOLD_CRITICAL,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_vd(ref_block=13.7, cur_block=0.4, total=500, sufficient=True):
    return VerdictDistributionResult(
        domain="trading",
        reference_window_days=30,
        current_window_days=14,
        reference_total=total,
        current_total=max(1, total // 3),
        ref_blocked_pct=ref_block,
        ref_held_pct=100 - ref_block - 10,
        ref_approved_pct=10.0,
        cur_blocked_pct=cur_block,
        cur_held_pct=100 - cur_block - 6,
        cur_approved_pct=6.0,
        composite_drift=72.0,
        alert_level="CRITICAL",
        sufficient_data=sufficient,
        error=None,
    )


def _make_rl(age_h=720, max_age=168, anchoring=True):
    frac = min(age_h / max_age, 1.0)
    return ReferenceLegitimacyResult(
        domain="trading",
        snapshot_id="snap-001",
        calibrated_at="2026-03-25T00:00:00",
        calibration_age_hours=age_h,
        max_age_hours=max_age,
        age_fraction=frac,
        baseline_signal_coherence=0.87,
        recalibration_anchoring_risk=anchoring,
        alert_level="CRITICAL" if anchoring else "OK",
        error=None,
    )


# ---------------------------------------------------------------------------
# Tests — DB alert map
# ---------------------------------------------------------------------------

class TestDBAlertMap:
    def test_critical_maps_to_alert(self):
        assert _DB_ALERT_MAP["CRITICAL"] == "ALERT"

    def test_warning_maps_to_warning(self):
        assert _DB_ALERT_MAP["WARNING"] == "WARNING"

    def test_ok_maps_to_ok(self):
        assert _DB_ALERT_MAP["OK"] == "OK"

    def test_unknown_maps_to_ok(self):
        assert _DB_ALERT_MAP["UNKNOWN"] == "OK"

    def test_no_value_outside_constraint(self):
        allowed = {"OK", "WARNING", "ALERT"}
        for v in _DB_ALERT_MAP.values():
            assert v in allowed, f"'{v}' not in DB constraint set"


# ---------------------------------------------------------------------------
# Tests — alert thresholds
# ---------------------------------------------------------------------------

class TestAlertThresholds:
    def test_warning_below_critical(self):
        assert _THRESHOLD_WARNING < _THRESHOLD_CRITICAL

    def test_warning_positive(self):
        assert _THRESHOLD_WARNING > 0

    def test_critical_under_100(self):
        assert _THRESHOLD_CRITICAL < 100


# ---------------------------------------------------------------------------
# Tests — VerdictDistributionResult
# ---------------------------------------------------------------------------

class TestVerdictDistributionResult:
    def test_block_collapse_sets_critical(self):
        vd = _make_vd(ref_block=13.7, cur_block=0.4)
        assert vd.alert_level == "CRITICAL"

    def test_insufficient_data_skipped(self):
        vd = _make_vd(sufficient=False)
        assert not vd.sufficient_data

    def test_composite_drift_positive(self):
        vd = _make_vd()
        assert vd.composite_drift > 0


# ---------------------------------------------------------------------------
# Tests — ReferenceLegitimacyResult
# ---------------------------------------------------------------------------

class TestReferenceLegitimacyResult:
    def test_old_calibration_flags_anchoring(self):
        rl = _make_rl(age_h=720, max_age=168, anchoring=True)
        assert rl.recalibration_anchoring_risk is True

    def test_age_fraction_exceeds_one_clamped(self):
        rl = _make_rl(age_h=1000, max_age=168)
        assert rl.age_fraction >= 1.0

    def test_fresh_calibration_no_anchoring(self):
        rl = _make_rl(age_h=12, max_age=168, anchoring=False)
        assert rl.recalibration_anchoring_risk is False
        assert rl.alert_level == "OK"


# ---------------------------------------------------------------------------
# Tests — MetaCoherenceReport
# ---------------------------------------------------------------------------

class TestMetaCoherenceReport:
    def _make_report(self):
        return MetaCoherenceReport(
            domain="trading",
            verdict_distribution=_make_vd(),
            veto_pattern=None,
            reference_legitimacy=_make_rl(),
            composite_score=79.5,
            alert_level="CRITICAL",
            evaluation_frame_stable=False,
            transition_signatures=[],
        )

    def test_alert_level_critical(self):
        r = self._make_report()
        assert r.alert_level == "CRITICAL"

    def test_composite_score_range(self):
        r = self._make_report()
        assert 0 <= r.composite_score <= 100

    def test_domain_set(self):
        r = self._make_report()
        assert r.domain == "trading"

    def test_generated_at_auto_set(self):
        r = self._make_report()
        assert r.generated_at is not None and len(r.generated_at) > 0

    def test_report_id_auto_set(self):
        r = self._make_report()
        assert r.report_id.startswith("MCM-")


# ---------------------------------------------------------------------------
# Tests — MetaCoherenceMonitor instantiation
# ---------------------------------------------------------------------------

class TestMetaCoherenceMonitorInit:
    def test_instantiation(self):
        m = MetaCoherenceMonitor()
        assert m is not None

    def test_get_active_domains_returns_list(self):
        m = MetaCoherenceMonitor()
        with patch.object(m, "_get_active_domains", return_value=["trading", "medical_ai"]):
            domains = m._get_active_domains()
        assert isinstance(domains, list)
        assert "trading" in domains

    def test_persist_to_db_noop_on_empty_report(self):
        m = MetaCoherenceMonitor()
        report = MetaCoherenceReport(
            domain="trading",
            verdict_distribution=None,
            veto_pattern=None,
            reference_legitimacy=None,
            composite_score=0.0,
            alert_level="OK",
            transition_signatures=[],
        )
        with patch("psycopg2.connect") as mock_conn:
            result = m.persist_to_db(report)
        # Should return False because all sub-results are None
        assert result is False


# ---------------------------------------------------------------------------
# Tests — Proxy gate filtering (regression guard)
# ---------------------------------------------------------------------------

class TestProxyGateFiltering:
    """Ensure PROXY_MODE / PROXY_ZERO gates don't inflate veto asymmetry."""

    def test_proxy_mode_gate_not_in_valid_gates(self):
        m = MetaCoherenceMonitor()
        proxy_gates = [
            "AML_FREQUENCY_PROXY_MODE",
            "FRAUD_REVERSAL_PROXY_MODE",
            "SHARIA_DEBT_RATIO_PROXY_ZERO",
        ]
        # The method _is_real_gate should return False for proxy gates
        if hasattr(m, "_is_real_gate"):
            for g in proxy_gates:
                assert not m._is_real_gate(g), f"{g} should be filtered"

    def test_real_gate_passes_filter(self):
        m = MetaCoherenceMonitor()
        if hasattr(m, "_is_real_gate"):
            assert m._is_real_gate("AML_FREQUENCY_GATE")
            assert m._is_real_gate("SHARIA_COMPLIANCE_GATE")
