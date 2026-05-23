"""
Tests para validación de esquema AVM — ADR-076

Cubre los 5 comportamientos críticos añadidos:
  1. save_calibration_snapshot() lanza ValueError con claves incorrectas
  2. _validate_domain_baselines() falla si DOMAIN_BASELINES tiene claves incorrectas
  3. evaluate() emite AVM_SCHEMA_MATCH=FULL / PARTIAL / NONE
  4. load_snapshot() rechaza snapshots desde disco con claves incorrectas
  5. DOMAIN_BASELINES actual pasa la validación de schema (regresión)
"""
import io
import json
import logging
import os
import tempfile
from pathlib import Path

import pytest

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("AVM_ENABLED", "true")

from omnix_core.governance.assumption_validity_monitor import (
    AssumptionValidityMonitor,
    SIGNAL_SCHEMA,
    SIGNAL_WEIGHTS,
    _SIGNAL_SCHEMA_SET,
)


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _make_avm(tmpdir=None):
    d = Path(tmpdir) if tmpdir else Path(tempfile.mkdtemp())
    return AssumptionValidityMonitor(snapshots_dir=d)


VALID_SIGNALS = {k: 65.0 for k in SIGNAL_SCHEMA}

WRONG_SIGNALS = {
    "momentum_score":   50.0,
    "fraud_probability": 30.0,
    "safety_score":     80.0,
    "volatility_index": 20.0,
    "reserve_ratio":    75.0,
    "model_confidence": 60.0,
}

PARTIAL_SIGNALS = {
    "probability_score": 65.0,
    "signal_coherence":  70.0,
    "bad_key_one":       30.0,
    "bad_key_two":       40.0,
    "bad_key_three":     50.0,
    "bad_key_four":      60.0,
}


def _capture_avm_logs(level=logging.DEBUG):
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setLevel(level)
    avm_logger = logging.getLogger("OMNIX.AVM")
    avm_logger.setLevel(logging.DEBUG)
    avm_logger.addHandler(handler)
    avm_logger.propagate = False
    return buf, handler, avm_logger


def _release_log_capture(avm_logger, handler):
    avm_logger.removeHandler(handler)
    avm_logger.propagate = True


# ── 1. Schema constants ─────────────────────────────────────────────────────────

class TestSignalSchemaConstants:
    def test_signal_schema_has_six_keys(self):
        assert len(SIGNAL_SCHEMA) == 6, (
            f"SIGNAL_SCHEMA must have exactly 6 keys. "
            f"Got {len(SIGNAL_SCHEMA)}: {SIGNAL_SCHEMA}"
        )

    def test_signal_schema_matches_signal_weights(self):
        assert set(SIGNAL_SCHEMA) == set(SIGNAL_WEIGHTS.keys()), (
            "SIGNAL_SCHEMA and SIGNAL_WEIGHTS keys must be identical."
        )

    def test_frozenset_matches_schema(self):
        assert _SIGNAL_SCHEMA_SET == frozenset(SIGNAL_SCHEMA)

    def test_weights_sum_to_one(self):
        total = sum(SIGNAL_WEIGHTS.values())
        assert abs(total - 1.0) < 1e-9, f"SIGNAL_WEIGHTS must sum to 1.0, got {total}"

    def test_canonical_keys_present(self):
        required = {
            "probability_score", "signal_coherence", "risk_exposure",
            "stress_resilience", "trend_persistence", "logic_consistency",
        }
        assert required == set(SIGNAL_SCHEMA), (
            f"Canonical keys changed! Expected {required}, got {set(SIGNAL_SCHEMA)}"
        )


# ── 2. save_calibration_snapshot() validation ───────────────────────────────────

class TestSaveCalibrationSnapshotValidation:
    def test_raises_valueerror_with_wrong_keys(self):
        avm = _make_avm()
        with pytest.raises(ValueError, match="SCHEMA_VIOLATION"):
            avm.save_calibration_snapshot(
                domain="test",
                baseline_signals=WRONG_SIGNALS,
            )

    def test_raises_valueerror_with_missing_keys(self):
        avm = _make_avm()
        partial = {"probability_score": 60.0, "signal_coherence": 70.0}
        with pytest.raises(ValueError, match="Missing="):
            avm.save_calibration_snapshot(
                domain="test",
                baseline_signals=partial,
            )

    def test_raises_valueerror_with_extra_keys(self):
        avm = _make_avm()
        extra = {**VALID_SIGNALS, "extra_key": 99.0}
        with pytest.raises(ValueError, match="Extra="):
            avm.save_calibration_snapshot(
                domain="test",
                baseline_signals=extra,
            )

    def test_accepts_correct_keys(self):
        avm = _make_avm()
        snap = avm.save_calibration_snapshot(
            domain="test",
            baseline_signals=VALID_SIGNALS,
        )
        assert snap.snapshot_id.startswith("AVM-")
        assert set(snap.baseline_signals.keys()) == _SIGNAL_SCHEMA_SET

    def test_error_message_reports_missing_and_extra(self):
        avm = _make_avm()
        signals = {"probability_score": 50.0, "BAD_KEY": 30.0}
        with pytest.raises(ValueError) as exc_info:
            avm.save_calibration_snapshot(domain="test", baseline_signals=signals)
        msg = str(exc_info.value)
        assert "Missing=" in msg
        assert "Extra=" in msg


# ── 3. evaluate() — AVM_SCHEMA_MATCH logging ───────────────────────────────────

class TestEvaluateSchemaMatchLogging:
    def test_full_match_logged_with_valid_snapshot(self):
        avm = _make_avm()
        avm.save_calibration_snapshot(domain="dom", baseline_signals=VALID_SIGNALS)

        buf, handler, avm_logger = _capture_avm_logs()
        try:
            result = avm.evaluate(signals=VALID_SIGNALS, domain="dom")
        finally:
            _release_log_capture(avm_logger, handler)

        logs = buf.getvalue()
        assert "AVM_SCHEMA_MATCH=FULL" in logs
        assert result.is_valid is True

    def test_none_match_logged_when_baseline_has_wrong_keys(self):
        avm = _make_avm()
        # Bypass save validation by writing directly to memory store
        from omnix_core.governance.assumption_validity_monitor import CalibrationSnapshot
        import uuid
        from datetime import datetime, timezone
        snap = CalibrationSnapshot(
            snapshot_id="AVM-TEST001",
            parameter_version="1.test",
            domain="dom_none",
            calibrated_at=datetime.now(timezone.utc).isoformat(),
            calibrated_at_epoch=datetime.now(timezone.utc).timestamp(),
            baseline_signals=WRONG_SIGNALS,
            checkpoint_thresholds={},
            drift_threshold=35.0,
            max_age_hours=168.0,
            description="Test snapshot with wrong keys",
            tags=[],
        )
        avm._memory_store["dom_none"] = snap

        buf, handler, avm_logger = _capture_avm_logs()
        try:
            result = avm.evaluate(signals=VALID_SIGNALS, domain="dom_none")
        finally:
            _release_log_capture(avm_logger, handler)

        logs = buf.getvalue()
        assert "AVM_SCHEMA_MATCH=NONE" in logs
        assert "SCHEMA_ANOMALY" in logs
        assert any("AVM_SCHEMA_MATCH=NONE" in w for w in result.warnings)

    def test_partial_match_logged_when_some_keys_wrong(self):
        avm = _make_avm()
        from omnix_core.governance.assumption_validity_monitor import CalibrationSnapshot
        from datetime import datetime, timezone
        snap = CalibrationSnapshot(
            snapshot_id="AVM-TEST002",
            parameter_version="1.test",
            domain="dom_partial",
            calibrated_at=datetime.now(timezone.utc).isoformat(),
            calibrated_at_epoch=datetime.now(timezone.utc).timestamp(),
            baseline_signals=PARTIAL_SIGNALS,
            checkpoint_thresholds={},
            drift_threshold=35.0,
            max_age_hours=168.0,
            description="Test snapshot with partial keys",
            tags=[],
        )
        avm._memory_store["dom_partial"] = snap

        buf, handler, avm_logger = _capture_avm_logs()
        try:
            result = avm.evaluate(signals=VALID_SIGNALS, domain="dom_partial")
        finally:
            _release_log_capture(avm_logger, handler)

        logs = buf.getvalue()
        assert "PARTIAL" in logs
        assert "SCHEMA_ANOMALY" in logs

    def test_drift_anomaly_fired_when_drift_100_and_not_full(self):
        avm = _make_avm()
        from omnix_core.governance.assumption_validity_monitor import CalibrationSnapshot
        from datetime import datetime, timezone
        snap = CalibrationSnapshot(
            snapshot_id="AVM-TEST003",
            parameter_version="1.test",
            domain="dom_drift_anomaly",
            calibrated_at=datetime.now(timezone.utc).isoformat(),
            calibrated_at_epoch=datetime.now(timezone.utc).timestamp(),
            baseline_signals=PARTIAL_SIGNALS,
            checkpoint_thresholds={},
            drift_threshold=35.0,
            max_age_hours=168.0,
            description="Partial match with extreme drift",
            tags=[],
        )
        avm._memory_store["dom_drift_anomaly"] = snap

        buf, handler, avm_logger = _capture_avm_logs()
        try:
            result = avm.evaluate(signals=VALID_SIGNALS, domain="dom_drift_anomaly")
        finally:
            _release_log_capture(avm_logger, handler)

        logs = buf.getvalue()
        assert "DRIFT_ANOMALY" in logs or "SCHEMA_ANOMALY" in logs


# ── 4. load_snapshot() rejects corrupt disk snapshots ──────────────────────────

class TestLoadSnapshotDiskValidation:
    def test_rejects_snapshot_with_wrong_keys_from_disk(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            avm = _make_avm(tmpdir=tmpdir)

            # Write a corrupt snapshot directly to disk (bypassing API validation)
            from omnix_core.governance.assumption_validity_monitor import CalibrationSnapshot
            from datetime import datetime, timezone
            snap = CalibrationSnapshot(
                snapshot_id="AVM-CORRUPT",
                parameter_version="1.corrupt",
                domain="dom_corrupt",
                calibrated_at=datetime.now(timezone.utc).isoformat(),
                calibrated_at_epoch=datetime.now(timezone.utc).timestamp(),
                baseline_signals=WRONG_SIGNALS,
                checkpoint_thresholds={},
                drift_threshold=35.0,
                max_age_hours=168.0,
                description="Corrupt snapshot",
                tags=[],
            )
            snap_path = Path(tmpdir) / "dom_corrupt_calibration.json"
            snap_path.write_text(json.dumps(snap.to_dict()))

            buf, handler, avm_logger = _capture_avm_logs()
            try:
                result = avm.load_snapshot("dom_corrupt")
            finally:
                _release_log_capture(avm_logger, handler)

            assert result is None, "Corrupt snapshot must be rejected (return None)"
            logs = buf.getvalue()
            assert "SCHEMA_MISMATCH" in logs

    def test_accepts_valid_snapshot_from_disk(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            avm = _make_avm(tmpdir=tmpdir)
            avm.save_calibration_snapshot(
                domain="dom_valid",
                baseline_signals=VALID_SIGNALS,
            )
            # Clear memory store to force disk load
            avm._memory_store.clear()
            result = avm.load_snapshot("dom_valid")
            assert result is not None
            assert set(result.baseline_signals.keys()) == _SIGNAL_SCHEMA_SET


# ── 5. DOMAIN_BASELINES regression guard ───────────────────────────────────────

class TestDomainBaselinesRegression:
    def test_domain_baselines_all_use_signal_schema_keys(self):
        from scripts.initialize_avm_baselines import DOMAIN_BASELINES, _validate_domain_baselines
        _validate_domain_baselines()  # must not raise
        for domain, cfg in DOMAIN_BASELINES.items():
            provided = set(cfg["signals"].keys())
            assert provided == set(SIGNAL_SCHEMA), (
                f"domain='{domain}' in DOMAIN_BASELINES uses wrong keys: "
                f"{provided}. Expected: {set(SIGNAL_SCHEMA)}"
            )

    def test_domain_baselines_has_nine_domains(self):
        from scripts.initialize_avm_baselines import DOMAIN_BASELINES
        assert len(DOMAIN_BASELINES) == 10, (
            f"Expected 10 domains in DOMAIN_BASELINES, got {len(DOMAIN_BASELINES)}: "
            f"{list(DOMAIN_BASELINES.keys())}"
        )

    def test_all_signal_values_in_range(self):
        from scripts.initialize_avm_baselines import DOMAIN_BASELINES
        for domain, cfg in DOMAIN_BASELINES.items():
            for key, val in cfg["signals"].items():
                assert 0.0 <= val <= 100.0, (
                    f"domain='{domain}' signal '{key}'={val} is outside [0, 100]"
                )


# ── 6. Alert fallback and rate limiting ────────────────────────────────────────

class TestAVMAlerts:
    def setup_method(self):
        from omnix_core.governance import avm_alerts
        avm_alerts._rate_history.clear()

    def test_critical_log_emitted_when_channel_not_configured(self):
        import io, logging
        from unittest.mock import patch

        buf = io.StringIO()
        handler = logging.StreamHandler(buf)
        handler.setLevel(logging.CRITICAL)
        alert_logger = logging.getLogger("OMNIX.AVM.Alerts")
        alert_logger.setLevel(logging.DEBUG)
        alert_logger.addHandler(handler)
        alert_logger.propagate = False

        try:
            with patch.dict(os.environ, {
                "TESTING": "false",
                "TELEGRAM_BOT_TOKEN": "",
                "OMNIX_ADMIN_CHAT_ID": "",
            }):
                from omnix_core.governance.avm_alerts import fire_avm_alert
                fire_avm_alert(
                    event_type="SCHEMA_ANOMALY_NONE",
                    domain="test_domain",
                    detail="Canal no configurado",
                    snapshot_id="AVM-TEST",
                )
            logs = buf.getvalue()
            assert "ALERT_NOT_SENT" in logs or "CRITICAL" in logs.upper(), (
                "Debe emitir CRITICAL cuando no hay canal configurado"
            )
        finally:
            alert_logger.removeHandler(handler)
            alert_logger.propagate = True

    def test_rate_limit_suppresses_excess_alerts(self):
        import io, logging, time
        from unittest.mock import patch

        buf = io.StringIO()
        handler = logging.StreamHandler(buf)
        handler.setLevel(logging.WARNING)
        alert_logger = logging.getLogger("OMNIX.AVM.Alerts")
        alert_logger.setLevel(logging.DEBUG)
        alert_logger.addHandler(handler)
        alert_logger.propagate = False

        try:
            with patch.dict(os.environ, {
                "TESTING": "false",
                "TELEGRAM_BOT_TOKEN": "",
                "OMNIX_ADMIN_CHAT_ID": "",
                "AVM_ALERT_MAX_PER_MINUTE": "3",
                "AVM_ALERT_WINDOW_SECONDS": "60",
            }):
                from omnix_core.governance.avm_alerts import fire_avm_alert
                from omnix_core.governance import avm_alerts
                avm_alerts._rate_history.clear()

                for i in range(5):
                    fire_avm_alert(
                        event_type="DRIFT_ANOMALY",
                        domain="loop_domain",
                        detail=f"loop iter {i}",
                        snapshot_id="AVM-LOOP",
                    )

            logs = buf.getvalue()
            assert "RATE_LIMITED" in logs, (
                "Debe emitir RATE_LIMITED cuando se supera el límite por minuto"
            )
        finally:
            alert_logger.removeHandler(handler)
            alert_logger.propagate = True
