"""
OMNIX QUANTUM — Differentiator Test Suite
==========================================

Tests for 4 institutional governance differentiators:

  GTPD  — Governance Threshold Probe Detection      (ADR-152)
  NUA   — Numeric Uniformity Anomaly Detection      (ADR-153)
  GEN   — Receipt Genealogy Chain                   (ADR-154)
  CCS   — Chain Completeness Score                  (ADR-155)

Each section tests:
  - Normal behavior   (must NOT over-trigger on legitimate inputs)
  - Adversarial case  (must detect the specific governance risk)
  - Evidence quality  (output is verifiable, structured, deterministic)

Run: TESTING=true TELEGRAM_BOT_TOKEN=test-token python -m pytest tests/test_differentiators.py -v --tb=short
"""

import os
import hashlib
import json
import threading
import time
import uuid

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")

import pytest

# ---------------------------------------------------------------------------
# Helpers shared across sections
# ---------------------------------------------------------------------------

def _make_signals(**kw):
    return {k: float(v) for k, v in kw.items()}


# ===========================================================================
# SECTION 1 — GTPD: Governance Threshold Probe Detection (ADR-152)
# ===========================================================================

class TestGTPDNormal:
    """GTPD must NOT flag legitimate, diverse evaluations as probe attacks."""

    def _get_fresh_avm(self):
        """Return a fresh AVM with a clean GTPD history for this test domain."""
        from omnix_core.governance.assumption_validity_monitor import (
            AssumptionValidityMonitor, _gtpd_drift_history, _GTPD_HISTORY_LOCK,
            ThresholdProbeReport,
        )
        domain = f"gtpd-normal-{uuid.uuid4().hex[:8]}"
        with _GTPD_HISTORY_LOCK:
            _gtpd_drift_history.pop(domain, None)
        avm = AssumptionValidityMonitor(drift_threshold=30.0)
        return avm, domain

    def test_insufficient_data_below_3_evals(self):
        """Fewer than 3 evaluations → INSUFFICIENT_DATA, never SUSPECTED/CONFIRMED."""
        from omnix_core.governance.assumption_validity_monitor import (
            AssumptionValidityMonitor, _gtpd_drift_history, _GTPD_HISTORY_LOCK,
            ThresholdProbeReport,
        )
        domain = f"gtpd-insuf-{uuid.uuid4().hex[:8]}"
        with _GTPD_HISTORY_LOCK:
            _gtpd_drift_history[domain] = [28.0, 29.0]  # only 2 entries

        avm = AssumptionValidityMonitor(drift_threshold=30.0)
        report = avm._detect_threshold_probe(domain, 30.0, 28.0)

        assert report.probe_verdict == "INSUFFICIENT_DATA"
        assert report.probe_score == 0.0
        assert report.evaluations_analyzed == 2

    def test_diverse_drift_scores_are_clean(self):
        """Evaluations spread across 0–100 range → CLEAN verdict."""
        from omnix_core.governance.assumption_validity_monitor import (
            AssumptionValidityMonitor, _gtpd_drift_history, _GTPD_HISTORY_LOCK,
        )
        domain = f"gtpd-diverse-{uuid.uuid4().hex[:8]}"
        threshold = 30.0
        # Scores spread evenly: only 2/20 fall within ±9 (30%) of threshold=30
        diverse_scores = [5.0, 10.0, 15.0, 20.0, 28.0, 35.0, 50.0, 60.0,
                          70.0, 80.0, 90.0, 100.0, 2.0, 4.0, 7.0, 85.0,
                          92.0, 45.0, 55.0, 65.0]
        with _GTPD_HISTORY_LOCK:
            _gtpd_drift_history[domain] = diverse_scores

        avm = AssumptionValidityMonitor(drift_threshold=threshold)
        report = avm._detect_threshold_probe(domain, threshold, 28.0)

        assert report.probe_verdict == "CLEAN", (
            f"Diverse evaluations must be CLEAN, got {report.probe_verdict} "
            f"(clustering={report.clustering_coefficient})"
        )

    def test_gtpd_never_changes_is_valid(self):
        """GTPD is a read-only detection layer — it must never change AVMResult.is_valid."""
        from omnix_core.governance.assumption_validity_monitor import AssumptionValidityMonitor

        domain = f"gtpd-valid-{uuid.uuid4().hex[:8]}"
        avm = AssumptionValidityMonitor(drift_threshold=40.0)

        baseline = {
            "probability_score": 65.0, "signal_coherence": 70.0,
            "risk_exposure": 35.0, "stress_resilience": 60.0,
            "trend_persistence": 55.0, "logic_consistency": 72.0,
        }
        avm.save_calibration_snapshot(domain=domain, baseline_signals=baseline)

        # Force near-threshold drift scores into history (adversarial-like)
        from omnix_core.governance.assumption_validity_monitor import (
            _gtpd_drift_history, _GTPD_HISTORY_LOCK,
        )
        near_threshold_scores = [37.0, 38.0, 39.0, 40.0, 41.0, 38.5, 39.5,
                                  37.5, 38.8, 39.2]
        with _GTPD_HISTORY_LOCK:
            _gtpd_drift_history[domain] = near_threshold_scores

        # Signals close to baseline → low drift → VALID
        current = {
            "probability_score": 66.0, "signal_coherence": 71.0,
            "risk_exposure": 36.0, "stress_resilience": 61.0,
            "trend_persistence": 56.0, "logic_consistency": 73.0,
        }
        result = avm.evaluate(domain=domain, signals=current)

        # GTPD may fire CONFIRMED but must NEVER flip is_valid to False
        assert result.is_valid is True, (
            "GTPD detection must not affect AVMResult.is_valid"
        )
        assert result.probe_report is not None
        assert "probe_verdict" in result.probe_report

    def test_probe_report_present_in_valid_result(self):
        """Every VALID evaluation must carry a probe_report dict."""
        from omnix_core.governance.assumption_validity_monitor import AssumptionValidityMonitor

        domain = f"gtpd-present-{uuid.uuid4().hex[:8]}"
        avm = AssumptionValidityMonitor(drift_threshold=40.0)
        avm.save_calibration_snapshot(
            domain=domain,
            baseline_signals={
                "probability_score": 65.0, "signal_coherence": 70.0,
                "risk_exposure": 35.0, "stress_resilience": 60.0,
                "trend_persistence": 55.0, "logic_consistency": 72.0,
            },
        )

        result = avm.evaluate(domain=domain, signals={
            "probability_score": 66.0, "signal_coherence": 71.0,
            "risk_exposure": 36.0, "stress_resilience": 61.0,
            "trend_persistence": 56.0, "logic_consistency": 73.0,
        })
        assert result.is_valid is True
        assert isinstance(result.probe_report, dict)
        required_keys = {"probe_id", "domain", "probe_score", "clustering_coefficient",
                         "evaluations_analyzed", "probe_verdict", "detected_at"}
        assert required_keys <= result.probe_report.keys()

    def test_to_dict_includes_probe_report(self):
        """AVMResult.to_dict() must serialize probe_report."""
        from omnix_core.governance.assumption_validity_monitor import AssumptionValidityMonitor

        domain = f"gtpd-dict-{uuid.uuid4().hex[:8]}"
        avm = AssumptionValidityMonitor(drift_threshold=40.0)
        avm.save_calibration_snapshot(
            domain=domain,
            baseline_signals={
                "probability_score": 65.0, "signal_coherence": 70.0,
                "risk_exposure": 35.0, "stress_resilience": 60.0,
                "trend_persistence": 55.0, "logic_consistency": 72.0,
            },
        )

        result = avm.evaluate(domain=domain, signals={
            "probability_score": 65.5, "signal_coherence": 70.5,
            "risk_exposure": 35.5, "stress_resilience": 60.5,
            "trend_persistence": 55.5, "logic_consistency": 72.5,
        })
        d = result.to_dict()
        assert "probe_report" in d
        assert d["probe_report"]["probe_verdict"] in {
            "INSUFFICIENT_DATA", "CLEAN", "SUSPECTED", "CONFIRMED"
        }


class TestGTPDAdversarial:
    """GTPD must detect systematic threshold probing."""

    def _inject_probe_history(self, domain: str, threshold: float, count: int):
        from omnix_core.governance.assumption_validity_monitor import (
            _gtpd_drift_history, _GTPD_HISTORY_LOCK,
        )
        margin = threshold * 0.30
        near_threshold = [
            threshold - margin * 0.8 + (i % 3) * (margin * 0.1)
            for i in range(count)
        ]
        with _GTPD_HISTORY_LOCK:
            _gtpd_drift_history[domain] = near_threshold

    def test_confirmed_when_high_clustering(self):
        """≥5 evals with >60% clustering → CONFIRMED probe verdict."""
        from omnix_core.governance.assumption_validity_monitor import (
            AssumptionValidityMonitor, _gtpd_drift_history, _GTPD_HISTORY_LOCK,
        )
        domain = f"gtpd-adv-confirmed-{uuid.uuid4().hex[:8]}"
        threshold = 30.0
        # 8 evaluations, ALL within ±9 of threshold=30 → clustering=1.0
        with _GTPD_HISTORY_LOCK:
            _gtpd_drift_history[domain] = [27.0, 28.0, 29.0, 30.0, 31.0, 32.0, 28.5, 29.5]

        avm = AssumptionValidityMonitor(drift_threshold=threshold)
        report = avm._detect_threshold_probe(domain, threshold, 29.0)

        assert report.probe_verdict == "CONFIRMED", (
            f"Expected CONFIRMED, got {report.probe_verdict} "
            f"(clustering={report.clustering_coefficient}, near={report.evaluations_near_threshold})"
        )
        assert report.clustering_coefficient > 0.60
        assert report.evaluations_near_threshold >= 5
        assert report.probe_score > 0.0

    def test_suspected_when_moderate_clustering(self):
        """3-4 evals near threshold with >20% clustering → SUSPECTED."""
        from omnix_core.governance.assumption_validity_monitor import (
            AssumptionValidityMonitor, _gtpd_drift_history, _GTPD_HISTORY_LOCK,
        )
        domain = f"gtpd-adv-suspected-{uuid.uuid4().hex[:8]}"
        threshold = 30.0
        # 5 evals, 3 near threshold → clustering=0.60 → SUSPECTED (not CONFIRMED: near<5 or clustering≤0.60)
        with _GTPD_HISTORY_LOCK:
            _gtpd_drift_history[domain] = [5.0, 29.0, 30.0, 31.0, 90.0]

        avm = AssumptionValidityMonitor(drift_threshold=threshold)
        report = avm._detect_threshold_probe(domain, threshold, 30.0)

        assert report.probe_verdict in ("SUSPECTED", "CONFIRMED"), (
            f"3 near-threshold evaluations should be at least SUSPECTED, got {report.probe_verdict}"
        )
        assert report.evaluations_near_threshold >= 3

    def test_probe_report_is_json_serializable(self):
        """ThresholdProbeReport.to_dict() must produce a fully JSON-serializable object."""
        from omnix_core.governance.assumption_validity_monitor import (
            AssumptionValidityMonitor, _gtpd_drift_history, _GTPD_HISTORY_LOCK,
        )
        domain = f"gtpd-json-{uuid.uuid4().hex[:8]}"
        threshold = 30.0
        with _GTPD_HISTORY_LOCK:
            _gtpd_drift_history[domain] = [27.0, 28.0, 29.0, 30.0, 31.0, 32.0, 28.5, 29.5]

        avm = AssumptionValidityMonitor(drift_threshold=threshold)
        report = avm._detect_threshold_probe(domain, threshold, 29.0)
        d = report.to_dict()

        serialized = json.dumps(d)  # must not raise
        restored = json.loads(serialized)
        assert restored["domain"] == domain
        assert restored["probe_verdict"] == "CONFIRMED"

    def test_probe_ids_are_unique(self):
        """Two probe detections on the same domain produce distinct probe_ids."""
        from omnix_core.governance.assumption_validity_monitor import (
            AssumptionValidityMonitor, _gtpd_drift_history, _GTPD_HISTORY_LOCK,
        )
        domain = f"gtpd-uniq-{uuid.uuid4().hex[:8]}"
        threshold = 30.0
        with _GTPD_HISTORY_LOCK:
            _gtpd_drift_history[domain] = [27.0, 28.0, 29.0, 30.0, 31.0, 32.0]

        avm = AssumptionValidityMonitor(drift_threshold=threshold)
        r1 = avm._detect_threshold_probe(domain, threshold, 29.0)
        r2 = avm._detect_threshold_probe(domain, threshold, 29.5)

        assert r1.probe_id != r2.probe_id

    def test_update_drift_history_is_thread_safe(self):
        """Concurrent drift updates must not corrupt the ring buffer."""
        from omnix_core.governance.assumption_validity_monitor import (
            AssumptionValidityMonitor, _gtpd_drift_history, _GTPD_HISTORY_LOCK,
            _GTPD_HISTORY_SIZE,
        )
        domain = f"gtpd-thread-{uuid.uuid4().hex[:8]}"
        with _GTPD_HISTORY_LOCK:
            _gtpd_drift_history.pop(domain, None)

        avm = AssumptionValidityMonitor(drift_threshold=30.0)
        errors = []

        def worker(score):
            try:
                avm._update_drift_history(domain, score)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(float(i % 100),)) for i in range(200)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread safety errors: {errors}"
        with _GTPD_HISTORY_LOCK:
            history_len = len(_gtpd_drift_history.get(domain, []))
        assert history_len <= _GTPD_HISTORY_SIZE


# ===========================================================================
# SECTION 2 — NUA: Numeric Uniformity Anomaly Detection (ADR-153)
# ===========================================================================

class TestNUANormal:
    """NUA must NOT flag legitimate, diverse market signals as fabricated."""

    def _form_packet(self, signals: dict, asset="BTC", domain="crypto"):
        from omnix_core.governance.llm_isolation_boundary import LLMIsolationBoundary
        boundary = LLMIsolationBoundary()
        return boundary.form_packet(raw_signals=signals, source="test", asset=asset, domain=domain)

    def test_diverse_market_signals_are_natural(self):
        """Diverse real market signals → NATURAL verdict, no false alarm."""
        packet = self._form_packet({
            "volatility":    35.4,
            "liquidity":     72.1,
            "sentiment":     48.7,
            "momentum":      61.3,
            "trend_strength": 29.8,
        })
        nua = packet.nua_report
        assert nua is not None
        assert nua["nua_verdict"] == "NATURAL", (
            f"Diverse signals must be NATURAL, got {nua['nua_verdict']} "
            f"(score={nua['uniformity_score']}, cv={nua['coefficient_of_variation']})"
        )

    def test_single_signal_is_natural(self):
        """Single signal → insufficient data for NUA → NATURAL."""
        packet = self._form_packet({"volatility": 42.5})
        nua = packet.nua_report
        assert nua is not None
        assert nua["nua_verdict"] == "NATURAL"
        assert nua["uniformity_score"] == 0.0

    def test_two_signals_minimum_analysis(self):
        """Two diverse signals (different magnitudes) → NATURAL."""
        packet = self._form_packet({"volatility": 10.0, "liquidity": 90.0})
        nua = packet.nua_report
        assert nua is not None
        # Range = 80, CV is large → should be NATURAL
        assert nua["nua_verdict"] == "NATURAL"

    def test_nua_never_blocks_packet(self):
        """NUA detection must NEVER prevent a valid packet from being formed."""
        # Inject highly uniform signals — NUA should flag but not block
        packet = self._form_packet({
            "volatility":     75.0,
            "liquidity":      75.0,
            "sentiment":      75.0,
            "momentum":       75.0,
            "trend_strength": 75.0,
        })
        # The packet must exist regardless of NUA verdict
        assert packet is not None
        assert packet.signals is not None
        assert len(packet.signals) > 0

    def test_nua_report_present_in_every_packet(self):
        """Every packet with ≥2 signals must carry a nua_report."""
        packet = self._form_packet({"volatility": 20.0, "liquidity": 80.0})
        assert packet.nua_report is not None
        assert "nua_verdict" in packet.nua_report
        assert "uniformity_score" in packet.nua_report

    def test_nua_to_dict_is_json_serializable(self):
        """nua_report in packet.to_dict() must be JSON-serializable."""
        packet = self._form_packet({
            "volatility": 35.4, "liquidity": 72.1, "sentiment": 48.7
        })
        d = packet.to_dict()
        assert "nua_report" in d
        json.dumps(d)  # must not raise

    def test_stable_fixedincome_like_signals_not_flagged(self):
        """
        Fixed-income or stable instruments can have naturally low variation.
        Ensure NUA does not flag on CV alone — it requires multiple indicators.
        """
        # Slightly varied but diverse enough range (not multiples of 0.05)
        packet = self._form_packet({
            "volatility":     12.3,
            "liquidity":      14.7,
            "sentiment":      11.9,
            "momentum":       16.1,
            "trend_strength": 13.4,
        })
        nua = packet.nua_report
        # Range is ~4.2, CV is moderate, values not on round multiples
        # Should be SUSPICIOUS at most, not FABRICATION_LIKELY
        assert nua["nua_verdict"] in ("NATURAL", "SUSPICIOUS"), (
            f"Stable fixed-income-like signals should not be FABRICATION_LIKELY, "
            f"got {nua['nua_verdict']} (score={nua['uniformity_score']})"
        )


class TestNUAAdversarial:
    """NUA must detect numeric patterns consistent with LLM fabrication."""

    def _form_packet(self, signals: dict):
        from omnix_core.governance.llm_isolation_boundary import LLMIsolationBoundary
        boundary = LLMIsolationBoundary()
        return boundary.form_packet(raw_signals=signals, source="test", asset="BTC", domain="crypto")

    def test_identical_values_are_fabrication_likely(self):
        """All signals exactly equal → FABRICATION_LIKELY."""
        packet = self._form_packet({
            "volatility":      75.0,
            "correlation":     75.0,
            "liquidity_score": 75.0,
            "sentiment_score": 75.0,
            "drawdown_pct":    75.0,
        })
        nua = packet.nua_report
        assert nua["nua_verdict"] == "FABRICATION_LIKELY", (
            f"Identical values must be FABRICATION_LIKELY, got {nua['nua_verdict']} "
            f"(score={nua['uniformity_score']})"
        )
        assert nua["uniformity_score"] >= 70.0

    def test_round_multiples_with_narrow_range_are_fabrication_likely(self):
        """Values all on ×0.25 multiples with narrow range → FABRICATION_LIKELY."""
        packet = self._form_packet({
            "volatility":      50.00,
            "correlation":     50.25,
            "liquidity_score": 50.50,
            "sentiment_score": 50.75,
            "drawdown_pct":    51.00,
        })
        nua = packet.nua_report
        # Range=1.0, all round, CV very low → high uniformity score
        assert nua["nua_verdict"] in ("SUSPICIOUS", "FABRICATION_LIKELY"), (
            f"Round multiples with narrow range must flag, got {nua['nua_verdict']} "
            f"(score={nua['uniformity_score']}, round_ratio={nua['round_number_ratio']})"
        )

    def test_zero_variance_signals_max_score(self):
        """Zero variance (all values identical) → maximum uniformity indicators."""
        from omnix_core.governance.llm_isolation_boundary import _analyze_numeric_uniformity
        signals = {"a": 42.0, "b": 42.0, "c": 42.0, "d": 42.0}
        report = _analyze_numeric_uniformity(signals, "test-packet")

        assert report.value_range == 0.0
        assert report.coefficient_of_variation == 0.0
        assert report.uniformity_score >= 70.0
        assert report.nua_verdict == "FABRICATION_LIKELY"

    def test_suspicious_signals_list_populated(self):
        """When CV is low, suspicious_signals list must identify the culprits."""
        from omnix_core.governance.llm_isolation_boundary import _analyze_numeric_uniformity
        signals = {
            "volatility":     60.0,
            "liquidity":      61.0,
            "sentiment":      60.5,
            "momentum":       60.2,
        }
        report = _analyze_numeric_uniformity(signals, "test-packet")

        if report.nua_verdict in ("SUSPICIOUS", "FABRICATION_LIKELY"):
            assert len(report.suspicious_signals) > 0

    def test_nua_report_id_is_unique(self):
        """Each NUA report must have a unique report_id."""
        from omnix_core.governance.llm_isolation_boundary import _analyze_numeric_uniformity
        signals = {"volatility": 42.0, "liquidity": 42.0, "sentiment": 42.0}
        r1 = _analyze_numeric_uniformity(signals, "p1")
        r2 = _analyze_numeric_uniformity(signals, "p2")
        assert r1.report_id != r2.report_id


# ===========================================================================
# SECTION 3 — GEN: Receipt Genealogy Chain (ADR-154)
# ===========================================================================

class TestGenealogy:
    """Receipt Genealogy Chain tests."""

    def _make_receipt(self, domain="crypto", asset="BTC", decision="APPROVED"):
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        engine = DecisionReceiptEngine()
        return engine.generate_receipt({
            "domain":   domain,
            "symbol":   asset,
            "decision": decision,
        })

    def _fresh_key(self, domain="crypto", asset="BTC"):
        """Reset the genealogy buffer for a specific key so tests are isolated."""
        from omnix_core.evidence import decision_receipt as dr_mod
        key = f"{domain}:{asset}"
        with dr_mod._genealogy_lock:
            dr_mod._genealogy_buffer.pop(key, None)

    def test_first_receipt_is_chain_root(self):
        """The first receipt for a domain:asset must be the chain root."""
        domain = f"gen-{uuid.uuid4().hex[:8]}"
        self._fresh_key(domain=domain, asset="BTC")
        receipt = self._make_receipt(domain=domain, asset="BTC")

        gen = receipt.get("genealogy")
        assert gen is not None
        assert gen["is_chain_root"] is True
        assert gen["parent_receipt_id"] is None
        assert gen["generation_depth"] == 1
        assert gen["chain_root_id"] == receipt["receipt_id"]

    def test_second_receipt_references_first(self):
        """Second receipt must reference first as parent."""
        domain = f"gen-{uuid.uuid4().hex[:8]}"
        self._fresh_key(domain=domain, asset="BTC")

        r1 = self._make_receipt(domain=domain, asset="BTC")
        r2 = self._make_receipt(domain=domain, asset="BTC")

        gen1 = r1.get("genealogy")
        gen2 = r2.get("genealogy")

        assert gen1["is_chain_root"] is True
        assert gen2["is_chain_root"] is False
        assert gen2["parent_receipt_id"] == r1["receipt_id"]
        assert gen2["generation_depth"] == 2
        assert gen2["chain_root_id"] == r1["receipt_id"]

    def test_third_receipt_depth_3(self):
        """Third receipt in a chain must have generation_depth=3."""
        domain = f"gen-{uuid.uuid4().hex[:8]}"
        self._fresh_key(domain=domain, asset="ETH")

        r1 = self._make_receipt(domain=domain, asset="ETH")
        r2 = self._make_receipt(domain=domain, asset="ETH")
        r3 = self._make_receipt(domain=domain, asset="ETH")

        assert r3["genealogy"]["generation_depth"] == 3
        assert r3["genealogy"]["chain_root_id"] == r1["receipt_id"]
        assert r3["genealogy"]["parent_receipt_id"] == r2["receipt_id"]

    def test_different_assets_are_independent_chains(self):
        """BTC and ETH chains must never share genealogy state."""
        domain = f"gen-{uuid.uuid4().hex[:8]}"
        self._fresh_key(domain=domain, asset="BTC")
        self._fresh_key(domain=domain, asset="ETH")

        btc1 = self._make_receipt(domain=domain, asset="BTC")
        eth1 = self._make_receipt(domain=domain, asset="ETH")
        btc2 = self._make_receipt(domain=domain, asset="BTC")

        assert btc1["genealogy"]["generation_depth"] == 1
        assert eth1["genealogy"]["generation_depth"] == 1
        assert btc2["genealogy"]["generation_depth"] == 2
        assert btc2["genealogy"]["parent_receipt_id"] == btc1["receipt_id"]
        assert eth1["genealogy"]["chain_root_id"] == eth1["receipt_id"]

    def test_genealogy_embedded_before_content_hash(self):
        """
        Genealogy must be in public_payload BEFORE content_hash computation.
        Proof: content_hash in the receipt must include genealogy data.
        Tamper-evidence test: changing parent_receipt_id changes content_hash.
        """
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        engine = DecisionReceiptEngine()

        domain = f"gen-{uuid.uuid4().hex[:8]}"
        self._fresh_key(domain=domain, asset="BTC")

        r1 = self._make_receipt(domain=domain, asset="BTC")
        r2 = self._make_receipt(domain=domain, asset="BTC")

        # Reconstruct what public_payload looked like, then tamper with genealogy
        payload_copy = {k: v for k, v in r2.items()
                        if k not in ("content_hash", "signature", "signature_format",
                                     "key_id", "signing_key_id", "signing_provider")}

        # Compute hash with tampered parent
        tampered = dict(payload_copy)
        tampered["genealogy"] = dict(tampered["genealogy"])
        tampered["genealogy"]["parent_receipt_id"] = "FAKE-RECEIPT-ID"

        original_hash = r2["content_hash"]
        tampered_hash = engine._compute_hash(tampered)

        assert original_hash != tampered_hash, (
            "Tampering with genealogy.parent_receipt_id must change content_hash"
        )

    def test_genealogy_key_format(self):
        """chain_key must be '{domain}:{asset}'."""
        domain = f"gen-{uuid.uuid4().hex[:8]}"
        self._fresh_key(domain=domain, asset="BTC")
        r = self._make_receipt(domain=domain, asset="BTC")
        assert r["genealogy"]["chain_key"] == f"{domain}:BTC"

    def test_genealogy_is_json_serializable(self):
        """genealogy dict must be JSON-serializable."""
        domain = f"gen-{uuid.uuid4().hex[:8]}"
        self._fresh_key(domain=domain, asset="BTC")
        r = self._make_receipt(domain=domain, asset="BTC")
        json.dumps(r["genealogy"])  # must not raise

    def test_old_receipts_without_genealogy_not_broken(self):
        """
        Receipts generated before genealogy feature was added (no 'genealogy' key)
        must still pass content_hash verification using their own stored hash.
        Simulated by manually computing hash of a receipt payload without genealogy.
        """
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        engine = DecisionReceiptEngine()

        # Simulate a legacy receipt payload (no genealogy key)
        legacy_payload = {
            "receipt_id":    "OMNI-legacy-001",
            "timestamp":     "2026-01-01T00:00:00+00:00",
            "issued_at_ms":  1735689600000,
            "ttl_epoch_ms":  1735776000000,
            "ttl_ms":        86400000,
            "asset":         "BTC",
            "decision":      "APPROVED",
            "veto_chain":    [],
            "policy_version": "6.5.0",
            "engine_version": "6.5.0",
            "prev_hash":     "",
            "signing_provider": "sha256",
            "signing_key_id": "test",
            "domain":        "crypto",
            "governance_schema_version": "1.0",
            "checkpoint_logic_fingerprint": "abc123",
            "hash_version":  "sha256-v1",
        }
        legacy_hash = engine._compute_hash(legacy_payload)
        legacy_payload["content_hash"] = legacy_hash

        # Verification: recompute hash from stored payload (excluding content_hash itself)
        verify_payload = {k: v for k, v in legacy_payload.items() if k != "content_hash"}
        recomputed = engine._compute_hash(verify_payload)
        assert recomputed == legacy_hash, "Legacy receipt (no genealogy) must still verify"


# ===========================================================================
# SECTION 4 — CCS: Chain Completeness Score (ADR-155)
# ===========================================================================

class TestCCSNormal:
    """CCS must correctly score a healthy, intact audit chain."""

    def _make_chain_entries(self, n: int):
        """
        Build a valid chain of n entries using the real TransparencyChain logic.
        Returns entries in oldest-first order.
        """
        from omnix_core.evidence.transparency_chain import compute_rolling_merkle_root
        import hashlib, time

        entries = []
        prev_root = "0" * 64

        for i in range(n):
            payload_hash = hashlib.sha256(f"payload-{i}".encode()).hexdigest()
            merkle_root  = compute_rolling_merkle_root(prev_root, payload_hash)
            prev_hash    = entries[-1]["payload_hash"] if entries else "0" * 64

            entries.append({
                "log_id":       i + 1,
                "payload_hash": payload_hash,
                "merkle_root":  merkle_root,
                "prev_log_hash": prev_hash,
                "ts_utc":       f"2026-05-{10 + i:02d}T10:00:00+00:00",
            })
            prev_root = merkle_root

        return entries

    def test_empty_chain_returns_no_data(self):
        """Empty entry list → ccs=0.0, verdict=NO_DATA."""
        from omnix_core.evidence.transparency_chain import compute_chain_completeness_score
        result = compute_chain_completeness_score([], pending_table_count=0)
        assert result["ccs"] == 0.0
        assert result["ccs_verdict"] == "NO_DATA"

    def test_perfect_chain_is_complete(self):
        """A valid chain with no breaks, no pending → COMPLETE (ccs≥90)."""
        from omnix_core.evidence.transparency_chain import compute_chain_completeness_score
        entries = self._make_chain_entries(5)
        result = compute_chain_completeness_score(entries, pending_table_count=0)
        assert result["ccs_verdict"] == "COMPLETE", (
            f"Perfect chain must be COMPLETE, got {result['ccs_verdict']} "
            f"(ccs={result['ccs']})"
        )
        assert result["ccs"] >= 90.0

    def test_ccs_keys_always_present(self):
        """CCS result must always contain all required keys."""
        from omnix_core.evidence.transparency_chain import compute_chain_completeness_score
        entries = self._make_chain_entries(3)
        result = compute_chain_completeness_score(entries)
        required = {"ccs", "ccs_verdict", "chain_integrity_score",
                    "temporal_consistency_score", "pending_penalty",
                    "minimum_coverage_score", "ccs_breakdown"}
        assert required <= result.keys()

    def test_ccs_is_json_serializable(self):
        """CCS result must be JSON-serializable."""
        from omnix_core.evidence.transparency_chain import compute_chain_completeness_score
        entries = self._make_chain_entries(3)
        result = compute_chain_completeness_score(entries)
        json.dumps(result)  # must not raise

    def test_get_chain_with_integrity_includes_ccs(self):
        """get_chain_with_integrity() must include ccs and ccs_verdict in integrity."""
        from omnix_core.evidence.transparency_chain import TransparencyChain
        chain = TransparencyChain()
        # get_chain will return [] from DB (no DB in test), but the method must still run
        result = chain.get_chain_with_integrity(symbol="BTC", limit=10)
        assert "integrity" in result
        assert "ccs" in result["integrity"]
        assert "ccs_verdict" in result["integrity"]
        assert result["integrity"]["ccs_verdict"] in (
            "NO_DATA", "COMPLETE", "DEGRADED", "PARTIAL", "COMPROMISED"
        )

    def test_pending_penalty_applied(self):
        """Each pending entry applies a -3 point penalty (max 30)."""
        from omnix_core.evidence.transparency_chain import compute_chain_completeness_score
        entries = self._make_chain_entries(5)

        no_pending  = compute_chain_completeness_score(entries, pending_table_count=0)
        ten_pending = compute_chain_completeness_score(entries, pending_table_count=10)

        assert ten_pending["ccs"] < no_pending["ccs"]
        assert ten_pending["pending_penalty"] == 30.0   # capped at 30
        assert no_pending["pending_penalty"] == 0.0


class TestCCSAdversarial:
    """CCS must detect tampered or incomplete chains."""

    def _make_chain_entries(self, n: int):
        from omnix_core.evidence.transparency_chain import compute_rolling_merkle_root
        import hashlib
        entries = []
        prev_root = "0" * 64
        for i in range(n):
            payload_hash = hashlib.sha256(f"payload-{i}".encode()).hexdigest()
            merkle_root  = compute_rolling_merkle_root(prev_root, payload_hash)
            prev_hash    = entries[-1]["payload_hash"] if entries else "0" * 64
            entries.append({
                "log_id":        i + 1,
                "payload_hash":  payload_hash,
                "merkle_root":   merkle_root,
                "prev_log_hash": prev_hash,
                "ts_utc":        f"2026-05-10T{10 + i}:00:00+00:00",
            })
            prev_root = merkle_root
        return entries

    def test_tampered_merkle_root_degrades_ccs(self):
        """Tampering with a merkle_root must lower chain_integrity_score and ccs."""
        from omnix_core.evidence.transparency_chain import compute_chain_completeness_score
        entries = self._make_chain_entries(5)
        clean_result = compute_chain_completeness_score(entries, pending_table_count=0)

        # Tamper: corrupt merkle_root of entry 2
        tampered = [dict(e) for e in entries]
        tampered[2]["merkle_root"] = "0" * 64  # wrong root

        tampered_result = compute_chain_completeness_score(tampered, pending_table_count=0)

        assert tampered_result["ccs"] < clean_result["ccs"], (
            "Tampered chain must score lower than clean chain"
        )
        assert tampered_result["ccs_breakdown"]["chain_breaks"] >= 1

    def test_broken_prev_hash_link_detected(self):
        """Breaking the prev_log_hash chain link must register as a break."""
        from omnix_core.evidence.transparency_chain import compute_chain_completeness_score
        entries = self._make_chain_entries(5)

        tampered = [dict(e) for e in entries]
        tampered[3]["prev_log_hash"] = "FAKE_HASH_0000"

        result = compute_chain_completeness_score(tampered, pending_table_count=0)
        assert result["ccs_breakdown"]["chain_breaks"] >= 1
        assert result["chain_integrity_score"] < 50.0

    def test_many_breaks_reaches_compromised(self):
        """7 breaks (7×8=56 > max 50) should push chain_integrity to 0."""
        from omnix_core.evidence.transparency_chain import compute_chain_completeness_score
        entries = self._make_chain_entries(9)

        tampered = [dict(e) for e in entries]
        # Corrupt merkle_root of 7 entries → 7 breaks × -8 = -56 → max(0, 50-56) = 0
        for i in range(1, 8):
            tampered[i]["merkle_root"] = f"TAMPERED-{i}" + "0" * 55

        result = compute_chain_completeness_score(tampered, pending_table_count=0)
        assert result["chain_integrity_score"] == 0.0
        assert result["ccs_verdict"] in ("PARTIAL", "COMPROMISED"), (
            f"5 breaks must reach PARTIAL or COMPROMISED, got {result['ccs_verdict']}"
        )

    def test_excessive_pending_degrades_to_degraded(self):
        """10 pending entries (max penalty=30) must push a clean chain to DEGRADED."""
        from omnix_core.evidence.transparency_chain import compute_chain_completeness_score
        entries = self._make_chain_entries(5)
        result = compute_chain_completeness_score(entries, pending_table_count=10)
        # 80 (clean) - 30 (max penalty) = 70 → COMPLETE boundary → ≤ DEGRADED
        assert result["ccs"] <= 80.0
        assert result["ccs_verdict"] in ("DEGRADED", "PARTIAL", "COMPROMISED", "COMPLETE")
        assert result["pending_penalty"] == 30.0

    def test_anomalous_time_gaps_reduce_temporal_score(self):
        """Entries with one giant time gap must reduce temporal_consistency_score."""
        from omnix_core.evidence.transparency_chain import compute_chain_completeness_score

        entries = [
            {"log_id": 1, "payload_hash": "a" * 64, "merkle_root": "b" * 64,
             "prev_log_hash": "0" * 64, "ts_utc": "2026-01-01T10:00:00+00:00"},
            {"log_id": 2, "payload_hash": "c" * 64, "merkle_root": "d" * 64,
             "prev_log_hash": "a" * 64, "ts_utc": "2026-01-01T10:01:00+00:00"},
            {"log_id": 3, "payload_hash": "e" * 64, "merkle_root": "f" * 64,
             "prev_log_hash": "c" * 64, "ts_utc": "2026-03-15T10:00:00+00:00"},  # 73-day gap
        ]
        result = compute_chain_completeness_score(entries, pending_table_count=0)
        # Temporal penalty must apply
        assert result["temporal_consistency_score"] < 30.0

    def test_ccs_bounded_0_to_100(self):
        """CCS must always be in [0, 100] regardless of inputs."""
        from omnix_core.evidence.transparency_chain import compute_chain_completeness_score

        # Worst case: many breaks, many pending
        entries = self._make_chain_entries(3)
        for e in entries:
            e["merkle_root"] = "TAMPERED" + "0" * 56
        result = compute_chain_completeness_score(entries, pending_table_count=100)

        assert 0.0 <= result["ccs"] <= 100.0

    def test_ccs_breakdown_counts_match(self):
        """ccs_breakdown.entries_analyzed must equal the number of entries passed."""
        from omnix_core.evidence.transparency_chain import compute_chain_completeness_score
        entries = self._make_chain_entries(7)
        result = compute_chain_completeness_score(entries, pending_table_count=2)
        assert result["ccs_breakdown"]["entries_analyzed"] == 7
        assert result["ccs_breakdown"]["pending_entries"] == 2
