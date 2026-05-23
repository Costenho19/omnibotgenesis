"""
Phase 3 — Filter Calibration Metrics Tests (ADR-127)

Tests cover:
  - FilterCalibrationEvent dataclass defaults
  - extract_event_from_result (gate extraction, DCI, coherence, BS, escalation)
  - FilterCalibrationMetricsService.record() non-blocking
  - FilterCalibrationMetricsService.flush() writes to DB
  - FilterCalibrationMetricsService.ensure_schema() idempotency
  - Query methods with mock psycopg2 connections
  - FilterCalibrationDaemon lifecycle
  - get_global_service() singleton
"""

import queue
import threading
import unittest
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch, call

from omnix_core.governance.filter_calibration_metrics import (
    GATES,
    OUTCOME_BLOCK,
    OUTCOME_HOLD,
    OUTCOME_PASS,
    OUTCOME_SKIP,
    BS_HIGH,
    BS_LOW,
    BS_NONE,
    FilterCalibrationDaemon,
    FilterCalibrationEvent,
    FilterCalibrationMetricsService,
    _extract_black_swan_level,
    _outcome_from_result_str,
    _scan_gate_results,
    _scan_trace,
    extract_event_from_result,
    get_global_service,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────

def _make_result(
    decision:       str  = "APPROVED",
    gate_results:   List = None,
    decision_trace: List = None,
    veto_chain:     List = None,
    scores:         Dict = None,
    layer_0:        Dict = None,
) -> Dict[str, Any]:
    return {
        "decision":       decision,
        "gate_results":   gate_results   or [],
        "decision_trace": decision_trace or [],
        "veto_chain":     veto_chain     or [],
        "scores":         scores         or {},
        "layer_0":        layer_0,
        "compliance_blocks": {},
        "checkpoints_total":  5,
        "checkpoints_passed": 5,
    }


def _make_gate_entry(checkpoint: str, name: str, signal: str, result: str) -> Dict:
    return {
        "checkpoint": checkpoint,
        "name":       name,
        "signal":     signal,
        "score":      75.0,
        "result":     result,
    }


def _make_mock_conn(rows: List):
    """Build a mock psycopg2 connection that returns given rows."""
    mock_cur  = MagicMock()
    mock_cur.fetchone.return_value = rows[0] if rows else None
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    return mock_conn, mock_cur


# ── TestOutcomeFromResultStr ───────────────────────────────────────────────────

class TestOutcomeFromResultStr(unittest.TestCase):

    def test_pass_variants(self):
        for v in ("PASS", "PASSED", "OK", "APPROVED", "ADMISSIBLE"):
            self.assertEqual(_outcome_from_result_str(v), OUTCOME_PASS, v)

    def test_block_variants(self):
        for v in ("BLOCKED", "BLOCK", "VETO", "REJECTED", "FAILED",
                  "INADMISSIBLE", "AML_INTERNAL_ERROR"):
            self.assertEqual(_outcome_from_result_str(v), OUTCOME_BLOCK, v)

    def test_hold_variant(self):
        self.assertEqual(_outcome_from_result_str("HOLD"), OUTCOME_HOLD)

    def test_unknown_is_skip(self):
        self.assertEqual(_outcome_from_result_str("UNKNOWN"), OUTCOME_SKIP)
        self.assertEqual(_outcome_from_result_str(""),        OUTCOME_SKIP)
        self.assertEqual(_outcome_from_result_str(None),      OUTCOME_SKIP)

    def test_case_insensitive(self):
        self.assertEqual(_outcome_from_result_str("pass"),    OUTCOME_PASS)
        self.assertEqual(_outcome_from_result_str("Blocked"), OUTCOME_BLOCK)


# ── TestScanGateResults ────────────────────────────────────────────────────────

class TestScanGateResults(unittest.TestCase):

    def test_finds_by_signal(self):
        gate_results = [_make_gate_entry("CP-2", "Coherence", "signal_coherence", "PASS")]
        self.assertEqual(
            _scan_gate_results(gate_results, ("signal_coherence",)),
            OUTCOME_PASS,
        )

    def test_finds_blocked(self):
        gate_results = [_make_gate_entry("CP-7", "Coherence", "signal_coherence", "BLOCKED")]
        self.assertEqual(
            _scan_gate_results(gate_results, ("coherence",)),
            OUTCOME_BLOCK,
        )

    def test_returns_skip_when_not_found(self):
        gate_results = [_make_gate_entry("CP-9", "AML", "aml_score", "PASS")]
        self.assertEqual(
            _scan_gate_results(gate_results, ("fraud",)),
            OUTCOME_SKIP,
        )

    def test_empty_list_returns_skip(self):
        self.assertEqual(_scan_gate_results([], ("coherence",)), OUTCOME_SKIP)


# ── TestScanTrace ──────────────────────────────────────────────────────────────

class TestScanTrace(unittest.TestCase):

    def test_detects_pass(self):
        trace = ["CP-9 AML_PASS: score=85/100"]
        result = _scan_trace(trace, ("CP-9 AML_PASS",), ("AML_VETO",))
        self.assertEqual(result, OUTCOME_PASS)

    def test_detects_block(self):
        trace = ["CP-9 AML_VETO: structuring detected"]
        result = _scan_trace(trace, ("AML_PASS",), ("AML_VETO",))
        self.assertEqual(result, OUTCOME_BLOCK)

    def test_block_takes_precedence_over_pass(self):
        trace = ["CP-9 AML_PASS: score=50", "CP-9 AML_VETO: override"]
        result = _scan_trace(trace, ("AML_PASS",), ("AML_VETO",))
        self.assertEqual(result, OUTCOME_BLOCK)

    def test_empty_trace_returns_skip(self):
        result = _scan_trace([], ("PASS",), ("BLOCK",))
        self.assertEqual(result, OUTCOME_SKIP)

    def test_no_match_returns_skip(self):
        trace = ["CAG_PASS: session OK"]
        result = _scan_trace(trace, ("AML_PASS",), ("AML_VETO",))
        self.assertEqual(result, OUTCOME_SKIP)


# ── TestExtractBlackSwanLevel ──────────────────────────────────────────────────

class TestExtractBlackSwanLevel(unittest.TestCase):

    def test_from_scores_high(self):
        level = _extract_black_swan_level([], [], {"black_swan": "HIGH"})
        self.assertEqual(level, BS_HIGH)

    def test_from_scores_low(self):
        level = _extract_black_swan_level([], [], {"black_swan_risk": "LOW"})
        self.assertEqual(level, BS_LOW)

    def test_from_trace_high(self):
        level = _extract_black_swan_level(["BS HIGH escalation triggered"], [], {})
        self.assertEqual(level, BS_HIGH)

    def test_from_trace_low(self):
        level = _extract_black_swan_level(["BLACK_SWAN LOW risk"], [], {})
        self.assertEqual(level, BS_LOW)

    def test_from_trace_none(self):
        level = _extract_black_swan_level(["BS NONE detected"], [], {})
        self.assertEqual(level, BS_NONE)

    def test_returns_none_when_no_data(self):
        level = _extract_black_swan_level([], [], {})
        self.assertIsNone(level)


# ── TestExtractEventFromResult ─────────────────────────────────────────────────

class TestExtractEventFromResult(unittest.TestCase):

    def test_basic_approved_decision(self):
        result = _make_result(decision="APPROVED")
        event  = extract_event_from_result(result, domain="trading", asset="BTC")
        self.assertEqual(event.final_decision, "APPROVED")
        self.assertEqual(event.domain, "trading")
        self.assertEqual(event.asset, "BTC")

    def test_dci_score_computed_from_logic_consistency(self):
        result = _make_result(scores={"logic_consistency": 30.0})
        event  = extract_event_from_result(result)
        self.assertIsNotNone(event.dci_score)
        self.assertAlmostEqual(event.dci_score, 70.0)

    def test_dci_score_none_when_missing(self):
        result = _make_result(scores={})
        event  = extract_event_from_result(result)
        self.assertIsNone(event.dci_score)

    def test_dci_clamped_to_0_100(self):
        result = _make_result(scores={"logic_consistency": 120.0})
        event  = extract_event_from_result(result)
        self.assertEqual(event.dci_score, 0.0)

    def test_coherence_score_from_signal_coherence(self):
        result = _make_result(scores={"signal_coherence": 82.5})
        event  = extract_event_from_result(result)
        self.assertEqual(event.coherence_score, 82.5)

    def test_coherence_score_fallback_to_temporal(self):
        result = _make_result(scores={"temporal_coherence": 60.0})
        event  = extract_event_from_result(result)
        self.assertEqual(event.coherence_score, 60.0)

    def test_coherence_score_none_when_missing(self):
        result = _make_result(scores={})
        event  = extract_event_from_result(result)
        self.assertIsNone(event.coherence_score)

    def test_escalation_from_trace(self):
        result = _make_result(
            decision_trace=["BS_HIGH_COHERENCE_ESCALATION: critical=50% normal=65%"]
        )
        event = extract_event_from_result(result)
        self.assertTrue(event.escalation_triggered)

    def test_escalation_false_when_not_in_trace(self):
        result = _make_result(decision_trace=["CAG_PASS", "CP-9 AML_PASS: score=90"])
        event  = extract_event_from_result(result)
        self.assertFalse(event.escalation_triggered)

    def test_aml_gate_from_trace_pass(self):
        result = _make_result(decision_trace=["CP-9 AML_PASS: score=90/100"])
        event  = extract_event_from_result(result)
        self.assertEqual(event.gate_aml, OUTCOME_PASS)

    def test_aml_gate_from_trace_block(self):
        result = _make_result(decision_trace=["CP-9 AML_VETO: structuring"])
        event  = extract_event_from_result(result)
        self.assertEqual(event.gate_aml, OUTCOME_BLOCK)

    def test_fraud_gate_from_trace_pass(self):
        result = _make_result(decision_trace=["CP-10 FRAUD_PASS: integrity=95"])
        event  = extract_event_from_result(result)
        self.assertEqual(event.gate_fraud, OUTCOME_PASS)

    def test_fraud_gate_from_trace_block(self):
        result = _make_result(decision_trace=["CP-10 FRAUD_VETO: manipulation"])
        event  = extract_event_from_result(result)
        self.assertEqual(event.gate_fraud, OUTCOME_BLOCK)

    def test_jurisdiction_gate_from_trace_block(self):
        result = _make_result(decision_trace=["CP-11 JURISDICTION_VETO: UAE restricted"])
        event  = extract_event_from_result(result)
        self.assertEqual(event.gate_jurisdiction, OUTCOME_BLOCK)

    def test_coherence_gate_from_gate_results(self):
        gr     = [_make_gate_entry("CP-7", "Coherence Gate", "signal_coherence", "PASS")]
        result = _make_result(gate_results=gr)
        event  = extract_event_from_result(result)
        self.assertEqual(event.gate_coherence, OUTCOME_PASS)

    def test_layer0_block_from_result_layer_field(self):
        result = _make_result(decision="BLOCKED")
        result["layer"] = "LAYER_0_STRUCTURAL_ADMISSIBILITY"
        event = extract_event_from_result(result)
        self.assertEqual(event.gate_layer0, OUTCOME_BLOCK)

    def test_black_swan_high_from_trace(self):
        result = _make_result(decision_trace=["BS HIGH — tail risk detected"])
        event  = extract_event_from_result(result)
        self.assertEqual(event.black_swan_level, BS_HIGH)

    def test_never_raises_on_empty_result(self):
        event = extract_event_from_result({})
        self.assertIsInstance(event, FilterCalibrationEvent)
        self.assertEqual(event.final_decision, "BLOCKED")

    def test_processing_time_passed_through(self):
        result = _make_result()
        event  = extract_event_from_result(result, processing_time_ms=42)
        self.assertEqual(event.processing_time_ms, 42)

    def test_all_gate_defaults_to_skip_on_empty_result(self):
        event = extract_event_from_result({})
        for gate in GATES:
            val = getattr(event, f"gate_{gate}")
            self.assertEqual(val, OUTCOME_SKIP, f"gate_{gate} should be SKIP on empty result")


# ── TestFilterCalibrationEvent ─────────────────────────────────────────────────

class TestFilterCalibrationEvent(unittest.TestCase):

    def test_default_values(self):
        ev = FilterCalibrationEvent()
        self.assertEqual(ev.domain,         "trading")
        self.assertEqual(ev.final_decision, "BLOCKED")
        self.assertFalse(ev.escalation_triggered)
        for gate in GATES:
            self.assertEqual(getattr(ev, f"gate_{gate}"), OUTCOME_SKIP)

    def test_custom_values(self):
        ev = FilterCalibrationEvent(
            domain="credit", asset="LOAN_001", final_decision="APPROVED",
            gate_aml=OUTCOME_PASS, dci_score=25.0,
        )
        self.assertEqual(ev.domain,   "credit")
        self.assertEqual(ev.gate_aml, OUTCOME_PASS)
        self.assertEqual(ev.dci_score, 25.0)


# ── TestFilterCalibrationMetricsService ───────────────────────────────────────

class TestFilterCalibrationMetricsService(unittest.TestCase):

    def _svc(self, db_url: str = "postgresql://test") -> FilterCalibrationMetricsService:
        return FilterCalibrationMetricsService(db_url=db_url, flush_interval_s=999)

    def test_record_is_nonblocking_and_enqueues(self):
        svc = self._svc()
        ev  = FilterCalibrationEvent(domain="trading", final_decision="APPROVED")
        svc.record(ev)
        self.assertEqual(svc.pending_count(), 1)

    def test_record_multiple_events(self):
        svc = self._svc()
        for i in range(5):
            svc.record(FilterCalibrationEvent(final_decision="APPROVED"))
        self.assertEqual(svc.pending_count(), 5)

    def test_record_drops_when_queue_full(self):
        svc = FilterCalibrationMetricsService(db_url="x", max_queue_size=2)
        svc.record(FilterCalibrationEvent())
        svc.record(FilterCalibrationEvent())
        svc.record(FilterCalibrationEvent())  # should be silently dropped
        self.assertEqual(svc.pending_count(), 2)

    def test_flush_drains_queue(self):
        svc = self._svc()
        for _ in range(3):
            svc.record(FilterCalibrationEvent())

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = MagicMock()

        written = svc.flush(conn=mock_conn)
        self.assertEqual(written, 3)
        self.assertEqual(svc.pending_count(), 0)

    def test_flush_empty_queue_returns_zero(self):
        svc     = self._svc()
        written = svc.flush(conn=MagicMock())
        self.assertEqual(written, 0)

    def test_flush_with_no_db_url_returns_zero(self):
        import os
        from unittest.mock import patch
        with patch.dict(os.environ, {"DATABASE_URL": "", "OMNIX_DB_URL": ""}):
            svc = FilterCalibrationMetricsService(db_url=None)
        svc.record(FilterCalibrationEvent())
        written = svc.flush()
        self.assertEqual(written, 0)

    def test_ensure_schema_calls_execute(self):
        svc = self._svc()
        mock_conn = MagicMock()
        mock_cur  = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        result = svc.ensure_schema(conn=mock_conn)
        self.assertTrue(result)
        self.assertTrue(mock_cur.execute.called)
        mock_conn.commit.assert_called()

    def test_ensure_schema_handles_error(self):
        svc = self._svc()
        mock_conn = MagicMock()
        mock_conn.cursor.side_effect = Exception("DB error")
        result = svc.ensure_schema(conn=mock_conn)
        self.assertFalse(result)

    def test_query_gate_stats_valid_gate(self):
        svc  = self._svc()
        row  = (40, 10, 0, 50, 100)  # pass, block, hold, skip, total
        mock_conn, mock_cur = _make_mock_conn([row])
        stats = svc.query_gate_stats("coherence", window="1d", conn=mock_conn)
        self.assertEqual(stats["gate"],        "coherence")
        self.assertEqual(stats["pass_count"],  40)
        self.assertEqual(stats["block_count"], 10)
        self.assertEqual(stats["skip_count"],  50)
        self.assertAlmostEqual(stats["pass_rate"], 40 / 50)

    def test_query_gate_stats_invalid_gate_raises(self):
        svc = self._svc()
        with self.assertRaises(ValueError):
            svc.query_gate_stats("nonexistent_gate", conn=MagicMock())

    def test_query_dci_distribution_returns_bands(self):
        svc = self._svc()
        # total_with_dci, avg, min, max, p50, p90, aligned, tensioned, contradictory
        row = (100, 45.5, 5.0, 95.0, 44.0, 82.0, 30, 50, 20)
        mock_conn, _ = _make_mock_conn([row])
        dist = svc.query_dci_distribution(window="1d", conn=mock_conn)
        self.assertEqual(dist["total_with_dci"],  100)
        self.assertEqual(dist["aligned_count"],    30)
        self.assertEqual(dist["tensioned_count"],  50)
        self.assertEqual(dist["contradictory_count"], 20)
        self.assertAlmostEqual(dist["aligned_rate"], 0.3)

    def test_query_black_swan_frequency(self):
        svc = self._svc()
        row = (100, 60, 25, 10, 5)  # total, none, low, high, unknown
        mock_conn, _ = _make_mock_conn([row])
        bs = svc.query_black_swan_frequency(window="1d", conn=mock_conn)
        self.assertEqual(bs["total"],      100)
        self.assertEqual(bs["high_count"], 10)
        self.assertAlmostEqual(bs["high_rate"], 0.10)

    def test_query_escalation_events(self):
        svc = self._svc()
        row = (1000, 30, 25, 5)  # total, escalation_count, blocked, approved
        mock_conn, _ = _make_mock_conn([row])
        esc = svc.query_escalation_events(window="1d", conn=mock_conn)
        self.assertEqual(esc["total"],             1000)
        self.assertEqual(esc["escalation_count"],  30)
        self.assertEqual(esc["escalation_blocked"], 25)
        self.assertEqual(esc["escalation_approved"], 5)
        self.assertAlmostEqual(esc["escalation_rate"], 0.03)

    def test_zero_total_rates_are_zero_not_div_by_zero(self):
        svc = self._svc()
        row = (0, 0, 0, 0, 0)
        mock_conn, _ = _make_mock_conn([row])
        stats = svc.query_gate_stats("aml", window="1h", conn=mock_conn)
        self.assertEqual(stats["pass_rate"],  0.0)
        self.assertEqual(stats["block_rate"], 0.0)

    def test_pending_count_reflects_queue(self):
        svc = self._svc()
        self.assertEqual(svc.pending_count(), 0)
        svc.record(FilterCalibrationEvent())
        self.assertEqual(svc.pending_count(), 1)


# ── TestFilterCalibrationDaemon ───────────────────────────────────────────────

class TestFilterCalibrationDaemon(unittest.TestCase):

    def test_start_creates_daemon_thread(self):
        svc    = FilterCalibrationMetricsService(db_url=None)
        daemon = FilterCalibrationDaemon(svc, flush_interval_s=999, warmup_s=0.01)
        daemon.start()
        self.assertTrue(daemon._thread.is_alive())
        daemon.stop()

    def test_start_idempotent(self):
        svc    = FilterCalibrationMetricsService(db_url=None)
        daemon = FilterCalibrationDaemon(svc, warmup_s=0.01)
        daemon.start()
        t1 = daemon._thread
        daemon.start()  # should not create another thread
        self.assertIs(daemon._thread, t1)
        daemon.stop()


# ── TestGetGlobalService ───────────────────────────────────────────────────────

class TestGetGlobalService(unittest.TestCase):

    def test_returns_same_instance(self):
        import omnix_core.governance.filter_calibration_metrics as fcm_mod
        fcm_mod._global_svc    = None
        fcm_mod._global_daemon = None
        with patch.object(FilterCalibrationMetricsService, "ensure_schema", return_value=True):
            svc1 = get_global_service()
            svc2 = get_global_service()
        self.assertIs(svc1, svc2)
        # Reset
        fcm_mod._global_svc    = None
        fcm_mod._global_daemon = None

    def test_returns_service_instance(self):
        import omnix_core.governance.filter_calibration_metrics as fcm_mod
        fcm_mod._global_svc    = None
        fcm_mod._global_daemon = None
        with patch.object(FilterCalibrationMetricsService, "ensure_schema", return_value=True):
            svc = get_global_service()
        self.assertIsInstance(svc, FilterCalibrationMetricsService)
        fcm_mod._global_svc    = None
        fcm_mod._global_daemon = None


# ── GATES constant ─────────────────────────────────────────────────────────────

class TestGatesConstant(unittest.TestCase):

    def test_all_gates_present(self):
        expected = {"layer0", "cag", "coherence", "mc", "black_swan",
                    "ecw", "sharia", "aml", "fraud", "jurisdiction"}
        self.assertEqual(set(GATES), expected)

    def test_event_has_column_for_each_gate(self):
        ev = FilterCalibrationEvent()
        for gate in GATES:
            self.assertTrue(hasattr(ev, f"gate_{gate}"), f"Missing gate_{gate} on event")


if __name__ == "__main__":
    unittest.main()
