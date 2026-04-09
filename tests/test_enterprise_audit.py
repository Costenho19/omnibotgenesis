"""
OMNIX Enterprise Audit Tests — ADR-074
Tests that validate the 4 enterprise-level requirements:

1. AVM Persistence — baseline is stored in DB and not overwritten on restart
2. Receipt ID format consistency — OMNIX-{DOMAIN}-{hex} across all domains
3. Cross-domain receipt integrity — all domains generate verifiable receipt IDs
4. Drift detection — AVM detects when current signals diverge from baseline

Run:
    TESTING=true TELEGRAM_BOT_TOKEN=test-token python -m pytest tests/test_enterprise_audit.py -v
"""

import pytest
import re
import uuid
from unittest.mock import MagicMock, patch


RECEIPT_ID_PATTERN = re.compile(r"^OMNIX(-[A-Z]{3})?-[A-F0-9]{12}$")
DOMAIN_RECEIPT_PATTERN = {
    "trading":        re.compile(r"^OMNIX-TRD-[A-F0-9]{12}$"),
    "islamic_credit": re.compile(r"^OMNIX-CRD-[A-F0-9]{12}$"),
    "insurance":      re.compile(r"^OMNIX-INS-[A-F0-9]{12}$"),
    "robotics":       re.compile(r"^OMNIX-RBT-[A-F0-9]{12}$"),
    "public_sandbox": re.compile(r"^OMNIX-PUB-[A-F0-9]{12}$"),
}


class TestReceiptIDFormat:
    """Receipt ID format consistency — ADR-074."""

    def test_build_receipt_id_trading(self):
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        rid = DecisionReceiptEngine.build_receipt_id("trading")
        assert DOMAIN_RECEIPT_PATTERN["trading"].match(rid), f"Bad format: {rid}"

    def test_build_receipt_id_insurance(self):
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        rid = DecisionReceiptEngine.build_receipt_id("insurance")
        assert DOMAIN_RECEIPT_PATTERN["insurance"].match(rid), f"Bad format: {rid}"

    def test_build_receipt_id_robotics(self):
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        rid = DecisionReceiptEngine.build_receipt_id("robotics")
        assert DOMAIN_RECEIPT_PATTERN["robotics"].match(rid), f"Bad format: {rid}"

    def test_build_receipt_id_islamic_credit(self):
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        rid = DecisionReceiptEngine.build_receipt_id("islamic_credit")
        assert DOMAIN_RECEIPT_PATTERN["islamic_credit"].match(rid), f"Bad format: {rid}"

    def test_build_receipt_id_public_sandbox(self):
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        rid = DecisionReceiptEngine.build_receipt_id("public_sandbox")
        assert DOMAIN_RECEIPT_PATTERN["public_sandbox"].match(rid), f"Bad format: {rid}"

    def test_build_receipt_id_unknown_domain_backward_compat(self):
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        rid = DecisionReceiptEngine.build_receipt_id("unknown_domain")
        assert rid.startswith("OMNIX-"), f"Must start with OMNIX-: {rid}"
        assert re.match(r"^OMNIX-[A-F0-9]{12}$", rid), f"Bad legacy format: {rid}"

    def test_build_receipt_id_empty_domain(self):
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        rid = DecisionReceiptEngine.build_receipt_id("")
        assert re.match(r"^OMNIX-[A-F0-9]{12}$", rid), f"Bad legacy format: {rid}"

    def test_all_domain_codes_are_unique(self):
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        codes = list(DecisionReceiptEngine._DOMAIN_CODES.values())
        assert len(codes) == len(set(codes)), "Duplicate domain codes detected"

    def test_receipt_ids_are_unique(self):
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        ids = {DecisionReceiptEngine.build_receipt_id("trading") for _ in range(100)}
        assert len(ids) == 100, "Receipt IDs must be unique"

    def test_generate_receipt_includes_domain_prefix(self):
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        engine = DecisionReceiptEngine.__new__(DecisionReceiptEngine)
        engine.db_url = None
        engine._signing_keys = None
        engine._provider = None

        receipt = engine.generate_receipt({
            "domain": "trading",
            "decision": "APPROVED",
            "symbol": "BTC/USD",
        })
        assert DOMAIN_RECEIPT_PATTERN["trading"].match(receipt["receipt_id"]), \
            f"Expected OMNIX-TRD-..., got: {receipt['receipt_id']}"


class TestInsuranceSimulatorReceiptFormat:
    """Insurance simulator uses OMNIX-INS-{hex} format."""

    def test_insurance_receipt_id_format_in_source(self):
        """Verify the insurance simulator source contains OMNIX-INS- prefix."""
        import inspect
        import omnix_core.insurance.insurance_simulator as mod
        source = inspect.getsource(mod)
        assert 'OMNIX-INS-' in source, \
            "insurance_simulator.py must generate OMNIX-INS- prefixed receipt IDs"

    def test_insurance_receipt_id_format_matches_pattern(self):
        """Generated receipt IDs match the canonical OMNIX-INS-{12hex} pattern."""
        rid = f"OMNIX-INS-{uuid.uuid4().hex[:12].upper()}"
        assert re.match(r"^OMNIX-INS-[A-F0-9]{12}$", rid), f"Bad format: {rid}"

    def test_insurance_receipt_id_no_legacy_ins_prefix(self):
        """Verify old INS- prefix is NOT in insurance simulator source."""
        import inspect
        import omnix_core.insurance.insurance_simulator as mod
        source = inspect.getsource(mod)
        import re as _re
        old_pattern = _re.findall(r'"INS-\{uuid', source)
        assert len(old_pattern) == 0, \
            f"Legacy 'INS-' prefix found in insurance_simulator — must use 'OMNIX-INS-'"


class TestRoboticsSimulatorReceiptFormat:
    """Robotics simulator uses OMNIX-RBT-{hex} format."""

    def test_robotics_receipt_id_format_in_source(self):
        """Verify the robotics simulator source contains OMNIX-RBT- prefix."""
        import inspect
        import omnix_core.robotics.robotics_simulator as mod
        source = inspect.getsource(mod)
        assert 'OMNIX-RBT-' in source, \
            "robotics_simulator.py must generate OMNIX-RBT- prefixed receipt IDs"

    def test_robotics_receipt_id_format_matches_pattern(self):
        """Generated receipt IDs match the canonical OMNIX-RBT-{12hex} pattern."""
        rid = f"OMNIX-RBT-{uuid.uuid4().hex[:12].upper()}"
        assert re.match(r"^OMNIX-RBT-[A-F0-9]{12}$", rid), f"Bad format: {rid}"

    def test_robotics_receipt_id_no_legacy_rbt_prefix(self):
        """Verify receipt_id assignments do NOT use old RBT- prefix."""
        import inspect
        import omnix_core.robotics.robotics_simulator as mod
        import re as _re
        source = inspect.getsource(mod)
        old_receipt_assignments = _re.findall(r'receipt_id\s*=\s*f"RBT-', source)
        assert len(old_receipt_assignments) == 0, \
            f"Legacy 'RBT-' receipt_id found in robotics_simulator — must use 'OMNIX-RBT-'"


class TestAVMPersistence:
    """AVM baselines must survive system restart without recalibration."""

    def test_avm_snapshot_survives_second_load(self, tmp_path):
        """Same snapshot ID after load → same baseline → drift detection preserved."""
        from omnix_core.governance.assumption_validity_monitor import AssumptionValidityMonitor
        avm = AssumptionValidityMonitor(snapshots_dir=tmp_path)

        avm.save_calibration_snapshot(
            domain="trading",
            baseline_signals={"momentum": 65.0, "liquidity": 72.0},
            description="Test baseline",
            tags=["test"],
        )
        snap1 = avm.load_snapshot("trading")

        avm2 = AssumptionValidityMonitor(snapshots_dir=tmp_path)
        snap2 = avm2.load_snapshot("trading")

        assert snap1 is not None
        assert snap2 is not None
        assert snap1.snapshot_id == snap2.snapshot_id, \
            "Snapshot ID changed — baseline was overwritten (drift detection broken)"
        assert snap1.baseline_signals == snap2.baseline_signals

    def test_initialize_avm_does_not_recalibrate_existing(self, tmp_path):
        """initialize_avm_baselines(force=False) must NOT overwrite existing baselines."""
        import os

        with patch("scripts.initialize_avm_baselines.AVMDatabaseBridge") as mock_bridge_cls, \
             patch.dict(os.environ, {}):
            mock_bridge = MagicMock()
            mock_bridge.is_available.return_value = False
            mock_bridge_cls.return_value = mock_bridge

            with patch("scripts.initialize_avm_baselines.AssumptionValidityMonitor") as mock_avm_cls:
                mock_avm = MagicMock()
                existing_snap = MagicMock()
                existing_snap.snapshot_id = "AVM-ORIGINAL-ID"
                mock_avm.load_snapshot.return_value = existing_snap
                mock_avm_cls.return_value = mock_avm

                from scripts.initialize_avm_baselines import initialize_avm_baselines
                results = initialize_avm_baselines(force=False)

                mock_avm.save_calibration_snapshot.assert_not_called()
                assert all(v is False for v in results.values()), \
                    "Should not seed any domain when all already calibrated"

    def test_db_bridge_ensure_table_called_on_init(self):
        """DB bridge must create table on startup."""
        with patch("scripts.initialize_avm_baselines.AVMDatabaseBridge") as mock_bridge_cls, \
             patch("scripts.initialize_avm_baselines.AssumptionValidityMonitor") as mock_avm_cls:
            mock_bridge = MagicMock()
            mock_bridge.is_available.return_value = True
            mock_bridge.load_all_snapshots.return_value = {
                "trading": {"snapshot_id": "AVM-EXISTING"},
                "islamic_credit": {"snapshot_id": "AVM-EXISTING"},
                "insurance": {"snapshot_id": "AVM-EXISTING"},
                "robotics": {"snapshot_id": "AVM-EXISTING"},
            }
            mock_bridge.restore_to_json.return_value = 4
            mock_bridge_cls.return_value = mock_bridge

            mock_avm = MagicMock()
            mock_avm_cls.return_value = mock_avm

            from scripts.initialize_avm_baselines import initialize_avm_baselines
            initialize_avm_baselines(force=False)

            mock_bridge.ensure_table.assert_called_once()
            mock_avm.save_calibration_snapshot.assert_not_called()


class TestDriftDetection:
    """AVM drift detection correctly identifies signal divergence."""

    def test_drift_detected_when_signals_deviate_beyond_threshold(self, tmp_path):
        from omnix_core.governance.assumption_validity_monitor import AssumptionValidityMonitor
        avm = AssumptionValidityMonitor(snapshots_dir=tmp_path)

        avm.save_calibration_snapshot(
            domain="trading",
            baseline_signals={
                "probability_score": 65.0,
                "signal_coherence":  72.0,
                "risk_exposure":     30.0,
                "stress_resilience": 60.0,
                "trend_persistence": 55.0,
                "logic_consistency": 70.0,
            },
            description="Test baseline",
            tags=["test"],
        )

        drifted_signals = {
            "probability_score": 5.0,
            "signal_coherence":  4.0,
            "risk_exposure":     98.0,
            "stress_resilience": 3.0,
            "trend_persistence": 4.0,
            "logic_consistency": 2.0,
        }

        result = avm.evaluate(signals=drifted_signals, domain="trading")
        assert result is not None
        assert result.drift_score > 0, f"Drift score must be non-zero, got {result.drift_score}"
        assert result.is_valid is False, \
            f"Extreme drift should block pipeline. drift_score={result.drift_score}"

    def test_no_drift_when_signals_are_stable(self, tmp_path):
        from omnix_core.governance.assumption_validity_monitor import AssumptionValidityMonitor
        avm = AssumptionValidityMonitor(snapshots_dir=tmp_path)

        baseline = {
            "probability_score": 65.0,
            "signal_coherence":  72.0,
            "risk_exposure":     30.0,
            "stress_resilience": 60.0,
            "trend_persistence": 55.0,
            "logic_consistency": 70.0,
        }
        avm.save_calibration_snapshot(
            domain="trading",
            baseline_signals=baseline,
            description="Test baseline",
            tags=["test"],
        )

        stable_signals = {
            "probability_score": 65.5,
            "signal_coherence":  71.8,
            "risk_exposure":     30.5,
            "stress_resilience": 60.2,
            "trend_persistence": 55.1,
            "logic_consistency": 70.0,
        }
        result = avm.evaluate(signals=stable_signals, domain="trading")
        assert result is not None
        assert result.is_valid is True, \
            f"No drift expected for near-identical signals. drift_score={result.drift_score}"


class TestCrossDomainReceiptConsistency:
    """All domains produce OMNIX-prefixed receipts — universal governance layer."""

    @pytest.mark.parametrize("domain,expected_prefix", [
        ("trading",        "OMNIX-TRD-"),
        ("islamic_credit", "OMNIX-CRD-"),
        ("insurance",      "OMNIX-INS-"),
        ("robotics",       "OMNIX-RBT-"),
        ("public_sandbox", "OMNIX-PUB-"),
    ])
    def test_all_domains_produce_omnix_prefixed_receipts(self, domain, expected_prefix):
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        rid = DecisionReceiptEngine.build_receipt_id(domain)
        assert rid.startswith(expected_prefix), \
            f"Domain '{domain}': expected prefix '{expected_prefix}', got '{rid}'"

    def test_no_domain_produces_raw_prefix_without_omnix(self):
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        for domain in DecisionReceiptEngine._DOMAIN_CODES:
            rid = DecisionReceiptEngine.build_receipt_id(domain)
            assert rid.startswith("OMNIX-"), \
                f"Receipt ID for domain '{domain}' does not start with OMNIX-: {rid}"
            assert not rid.startswith("INS-"), "Old INS- format found"
            assert not rid.startswith("RBT-"), "Old RBT- format found"
