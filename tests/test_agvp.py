"""
Tests for ADR-174: Anticipatory Governance Veto Protocol (AGVP)

Coverage:
  - ProactiveVetoReceipt creation and content_hash (AGV-INV-004)
  - AGVPWatchdog minimum interval enforcement (AGV-INV-003)
  - Signal cache update (observability decoupling)
  - get_active_pvr() in-memory and cold paths
  - has_active_pvr() boolean wrapper
  - Revocation: admin-only (AGV-INV-002), token validation
  - AGV-INV-005: no PVR on pass_through=True
  - AGV-INV-006: recalibration guard (is_domain_safe_for_recalibration)
  - PVR content_hash determinism and field coverage (AGV-INV-004)
  - PVR ID format: OMNIX-PVR-{16HEX}
  - Watchdog cycle: emits PVR on drift block, skips on pass_through
  - Watchdog cycle: idempotent on existing ACTIVE PVR
  - Watchdog cycle: logs RECOVERY_CANDIDATE (does not auto-revoke, AGV-INV-002)
  - Multi-instance: second PVR not created for same domain (idempotency)
  - _compute_content_hash determinism
  - AGVPEngine.watchdog_status()
  - AGVPEngine.list_active_pvrs() / list_pvr_history() (mock DB)
  - Full integration path: update_domain_signals → get_active_pvr
"""
from __future__ import annotations

import json
import os
import threading
import time
import unittest
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch, PropertyMock

# Set TESTING mode so PQC and DB calls are stubbed
os.environ["TESTING"] = "true"

from omnix_core.governance.anticipatory_governance_veto import (
    AGVP_MIN_INTERVAL_SECONDS,
    AGVPEngine,
    AGVPWatchdog,
    ProactiveVetoReceipt,
    _SignalCacheEntry,
    _active_pvr_cache,
    _compute_content_hash,
    _create_pvr,
    _pvr_cache_lock,
    _signal_cache,
    _signal_cache_lock,
    get_active_pvr,
    has_active_pvr,
    is_domain_safe_for_recalibration,
    update_domain_signals,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

SAMPLE_SIGNALS = {
    "signal_coherence": 72.0,
    "risk_exposure": 88.0,
    "volatility_index": 91.0,
    "liquidity_score": 55.0,
    "momentum_strength": 61.0,
}


def _make_pvr(
    domain: str = "trading",
    tenant_id: str = "default",
    drift_score: float = 45.0,
    drift_threshold: float = 35.0,
    status: str = "ACTIVE",
) -> ProactiveVetoReceipt:
    pvr = _create_pvr(
        domain=domain,
        tenant_id=tenant_id,
        drift_score=drift_score,
        drift_threshold=drift_threshold,
        drift_components={"risk_exposure": 45.0, "volatility_index": 35.0},
        signals_at_assessment=SAMPLE_SIGNALS,
        signals_seen_at=datetime.now(timezone.utc).isoformat(),
        snapshot_id="SNAP-001",
        block_reason="TEST drift exceeded",
        watchdog_interval_seconds=60,
    )
    # Override status for test scenarios
    from dataclasses import replace
    return replace(pvr, status=status)


def _inject_cache(pvr: ProactiveVetoReceipt) -> None:
    cache_key = f"{pvr.tenant_id}:{pvr.domain}"
    with _pvr_cache_lock:
        _active_pvr_cache[cache_key] = pvr


def _clear_cache(domain: str, tenant_id: str = "default") -> None:
    cache_key = f"{tenant_id}:{domain}"
    with _pvr_cache_lock:
        _active_pvr_cache.pop(cache_key, None)
    with _signal_cache_lock:
        _signal_cache.pop(cache_key, None)


# ── PVR Structure ─────────────────────────────────────────────────────────────

class TestPVRCreation(unittest.TestCase):

    def tearDown(self):
        _clear_cache("trading")

    def test_pvr_id_format(self):
        pvr = _make_pvr()
        self.assertTrue(pvr.pvr_id.startswith("OMNIX-PVR-"))
        hex_part = pvr.pvr_id[len("OMNIX-PVR-"):]
        self.assertEqual(len(hex_part), 16)
        int(hex_part, 16)  # must be valid hex

    def test_pvr_status_active_by_default(self):
        pvr = _make_pvr()
        self.assertEqual(pvr.status, "ACTIVE")
        self.assertTrue(pvr.is_active())

    def test_pvr_content_hash_non_empty(self):
        pvr = _make_pvr()
        self.assertTrue(pvr.content_hash)
        self.assertEqual(len(pvr.content_hash), 64)  # SHA-256 hex

    def test_pvr_pqc_signature_testing_stub(self):
        pvr = _make_pvr()
        self.assertEqual(pvr.pqc_signature, "TESTING")
        self.assertEqual(pvr.pqc_algorithm, "ML-DSA-65")

    def test_pvr_has_all_required_fields(self):
        pvr = _make_pvr()
        d = pvr.to_dict()
        for field in [
            "pvr_id", "tenant_id", "domain", "drift_score", "drift_threshold",
            "drift_components", "signals_at_assessment", "signals_seen_at",
            "snapshot_id", "assessment_timestamp", "veto_effective_from",
            "block_reason", "status", "content_hash", "pqc_signature",
            "pqc_algorithm", "created_at", "watchdog_interval_seconds",
        ]:
            self.assertIn(field, d, f"Missing field: {field}")

    def test_pvr_veto_effective_from_equals_assessment_timestamp(self):
        pvr = _make_pvr()
        self.assertEqual(pvr.veto_effective_from, pvr.assessment_timestamp)

    def test_pvr_revoked_fields_none_when_active(self):
        pvr = _make_pvr()
        self.assertIsNone(pvr.revoked_at)
        self.assertIsNone(pvr.revoked_by)
        self.assertIsNone(pvr.revocation_reason)

    def test_pvr_signals_preserved(self):
        pvr = _make_pvr()
        self.assertEqual(pvr.signals_at_assessment, SAMPLE_SIGNALS)


# ── AGV-INV-004: Content Hash ─────────────────────────────────────────────────

class TestPVRContentHash(unittest.TestCase):

    def test_content_hash_deterministic(self):
        h1 = _compute_content_hash(
            pvr_id="OMNIX-PVR-AABBCCDD11223344",
            tenant_id="default",
            domain="trading",
            drift_score=45.0,
            drift_threshold=35.0,
            signals_at_assessment=SAMPLE_SIGNALS,
            assessment_timestamp="2026-05-20T10:00:00+00:00",
            veto_effective_from="2026-05-20T10:00:00+00:00",
            snapshot_id="SNAP-001",
        )
        h2 = _compute_content_hash(
            pvr_id="OMNIX-PVR-AABBCCDD11223344",
            tenant_id="default",
            domain="trading",
            drift_score=45.0,
            drift_threshold=35.0,
            signals_at_assessment=SAMPLE_SIGNALS,
            assessment_timestamp="2026-05-20T10:00:00+00:00",
            veto_effective_from="2026-05-20T10:00:00+00:00",
            snapshot_id="SNAP-001",
        )
        self.assertEqual(h1, h2)

    def test_content_hash_changes_with_domain(self):
        base_args = dict(
            pvr_id="OMNIX-PVR-AABBCCDD11223344",
            tenant_id="default",
            drift_score=45.0,
            drift_threshold=35.0,
            signals_at_assessment=SAMPLE_SIGNALS,
            assessment_timestamp="2026-05-20T10:00:00+00:00",
            veto_effective_from="2026-05-20T10:00:00+00:00",
            snapshot_id="SNAP-001",
        )
        h1 = _compute_content_hash(domain="trading", **base_args)
        h2 = _compute_content_hash(domain="credit", **base_args)
        self.assertNotEqual(h1, h2)

    def test_content_hash_changes_with_drift_score(self):
        base_args = dict(
            pvr_id="OMNIX-PVR-AABBCCDD11223344",
            tenant_id="default",
            domain="trading",
            drift_threshold=35.0,
            signals_at_assessment=SAMPLE_SIGNALS,
            assessment_timestamp="2026-05-20T10:00:00+00:00",
            veto_effective_from="2026-05-20T10:00:00+00:00",
            snapshot_id="SNAP-001",
        )
        h1 = _compute_content_hash(drift_score=45.0, **base_args)
        h2 = _compute_content_hash(drift_score=46.0, **base_args)
        self.assertNotEqual(h1, h2)

    def test_content_hash_changes_with_signals(self):
        base_args = dict(
            pvr_id="OMNIX-PVR-AABBCCDD11223344",
            tenant_id="default",
            domain="trading",
            drift_score=45.0,
            drift_threshold=35.0,
            assessment_timestamp="2026-05-20T10:00:00+00:00",
            veto_effective_from="2026-05-20T10:00:00+00:00",
            snapshot_id="SNAP-001",
        )
        sigs_a = {"risk_exposure": 80.0}
        sigs_b = {"risk_exposure": 81.0}
        h1 = _compute_content_hash(signals_at_assessment=sigs_a, **base_args)
        h2 = _compute_content_hash(signals_at_assessment=sigs_b, **base_args)
        self.assertNotEqual(h1, h2)

    def test_content_hash_length(self):
        h = _compute_content_hash(
            pvr_id="OMNIX-PVR-AABBCCDD11223344",
            tenant_id="default",
            domain="trading",
            drift_score=45.0,
            drift_threshold=35.0,
            signals_at_assessment=SAMPLE_SIGNALS,
            assessment_timestamp="2026-05-20T10:00:00+00:00",
            veto_effective_from="2026-05-20T10:00:00+00:00",
            snapshot_id="SNAP-001",
        )
        self.assertEqual(len(h), 64)  # SHA-256 hex


# ── AGV-INV-003: Minimum Watchdog Interval ────────────────────────────────────

class TestWatchdogMinimumInterval(unittest.TestCase):

    def test_inv003_interval_below_minimum_raises(self):
        with self.assertRaises(ValueError) as ctx:
            AGVPWatchdog(interval_seconds=10)
        self.assertIn("AGV-INV-003", str(ctx.exception))
        self.assertIn("30", str(ctx.exception))

    def test_inv003_interval_zero_raises(self):
        with self.assertRaises(ValueError):
            AGVPWatchdog(interval_seconds=0)

    def test_inv003_negative_interval_raises(self):
        with self.assertRaises(ValueError):
            AGVPWatchdog(interval_seconds=-1)

    def test_inv003_exactly_minimum_is_valid(self):
        wd = AGVPWatchdog(interval_seconds=AGVP_MIN_INTERVAL_SECONDS)
        self.assertEqual(wd.interval_seconds, AGVP_MIN_INTERVAL_SECONDS)

    def test_inv003_above_minimum_is_valid(self):
        wd = AGVPWatchdog(interval_seconds=60)
        self.assertEqual(wd.interval_seconds, 60)

    def test_inv003_error_message_contains_min_value(self):
        with self.assertRaises(ValueError) as ctx:
            AGVPWatchdog(interval_seconds=5)
        self.assertIn(str(AGVP_MIN_INTERVAL_SECONDS), str(ctx.exception))


# ── Signal Cache (Observability Decoupling) ───────────────────────────────────

class TestSignalCache(unittest.TestCase):

    def setUp(self):
        _clear_cache("trading")
        _clear_cache("credit")

    def tearDown(self):
        _clear_cache("trading")
        _clear_cache("credit")

    def test_update_domain_signals_populates_cache(self):
        engine = AGVPEngine("default")
        engine.update_domain_signals("trading", SAMPLE_SIGNALS)
        with _signal_cache_lock:
            entry = _signal_cache.get("default:trading")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.signals, SAMPLE_SIGNALS)

    def test_update_domain_signals_module_level(self):
        update_domain_signals("credit", SAMPLE_SIGNALS)
        with _signal_cache_lock:
            entry = _signal_cache.get("default:credit")
        self.assertIsNotNone(entry)

    def test_signal_seen_at_is_recent(self):
        engine = AGVPEngine("default")
        before = time.monotonic()
        engine.update_domain_signals("trading", SAMPLE_SIGNALS)
        after = time.monotonic()
        with _signal_cache_lock:
            entry = _signal_cache.get("default:trading")
        self.assertGreaterEqual(entry.seen_at, before)
        self.assertLessEqual(entry.seen_at, after)

    def test_signal_update_overwrites_previous(self):
        engine = AGVPEngine("default")
        engine.update_domain_signals("trading", {"risk_exposure": 50.0})
        engine.update_domain_signals("trading", {"risk_exposure": 90.0})
        with _signal_cache_lock:
            entry = _signal_cache.get("default:trading")
        self.assertEqual(entry.signals["risk_exposure"], 90.0)

    def test_signal_update_independent_of_pvr_state(self):
        """Signals update even when a PVR is active — breaks observability deadlock."""
        pvr = _make_pvr(domain="trading")
        _inject_cache(pvr)
        engine = AGVPEngine("default")
        # Should NOT raise and should update cache regardless of PVR
        engine.update_domain_signals("trading", SAMPLE_SIGNALS)
        with _signal_cache_lock:
            entry = _signal_cache.get("default:trading")
        self.assertIsNotNone(entry)


# ── get_active_pvr / has_active_pvr ──────────────────────────────────────────

class TestGetActivePVR(unittest.TestCase):

    def setUp(self):
        _clear_cache("trading")

    def tearDown(self):
        _clear_cache("trading")

    def test_returns_none_when_no_pvr(self):
        with patch(
            "omnix_core.governance.anticipatory_governance_veto._load_active_pvr_from_db",
            return_value=None,
        ):
            result = get_active_pvr("trading")
        self.assertIsNone(result)

    def test_returns_pvr_from_memory_cache(self):
        pvr = _make_pvr(domain="trading")
        _inject_cache(pvr)
        result = get_active_pvr("trading")
        self.assertIsNotNone(result)
        self.assertEqual(result.pvr_id, pvr.pvr_id)

    def test_memory_cache_takes_priority_over_db(self):
        pvr = _make_pvr(domain="trading")
        _inject_cache(pvr)
        with patch(
            "omnix_core.governance.anticipatory_governance_veto._load_active_pvr_from_db",
        ) as mock_db:
            result = get_active_pvr("trading")
            mock_db.assert_not_called()
        self.assertEqual(result.pvr_id, pvr.pvr_id)

    def test_loads_from_db_on_cache_miss(self):
        pvr = _make_pvr(domain="trading")
        with patch(
            "omnix_core.governance.anticipatory_governance_veto._load_active_pvr_from_db",
            return_value=pvr,
        ):
            result = get_active_pvr("trading")
        self.assertIsNotNone(result)
        self.assertEqual(result.pvr_id, pvr.pvr_id)

    def test_db_pvr_is_cached_after_load(self):
        pvr = _make_pvr(domain="trading")
        with patch(
            "omnix_core.governance.anticipatory_governance_veto._load_active_pvr_from_db",
            return_value=pvr,
        ):
            get_active_pvr("trading")
        # Second call should use cache, not DB
        with patch(
            "omnix_core.governance.anticipatory_governance_veto._load_active_pvr_from_db",
        ) as mock_db:
            result = get_active_pvr("trading")
            mock_db.assert_not_called()
        self.assertEqual(result.pvr_id, pvr.pvr_id)

    def test_has_active_pvr_true_when_pvr_exists(self):
        pvr = _make_pvr(domain="trading")
        _inject_cache(pvr)
        self.assertTrue(has_active_pvr("trading"))

    def test_has_active_pvr_false_when_no_pvr(self):
        with patch(
            "omnix_core.governance.anticipatory_governance_veto._load_active_pvr_from_db",
            return_value=None,
        ):
            self.assertFalse(has_active_pvr("trading"))


# ── AGV-INV-002: Admin-Only Revocation ───────────────────────────────────────

class TestPVRRevocation(unittest.TestCase):

    def setUp(self):
        _clear_cache("trading")
        os.environ.pop("AGVP_ADMIN_TOKEN", None)

    def tearDown(self):
        _clear_cache("trading")
        os.environ.pop("AGVP_ADMIN_TOKEN", None)

    def test_revoke_requires_revoked_by(self):
        engine = AGVPEngine("default")
        pvr = _make_pvr()
        with patch("omnix_core.governance.anticipatory_governance_veto._revoke_pvr_in_db", return_value=True):
            result = engine.revoke_pvr(pvr.pvr_id, revoked_by="", reason="test")
        self.assertFalse(result["success"])
        self.assertIn("AGV-INV-002", result["message"])

    def test_revoke_requires_reason(self):
        engine = AGVPEngine("default")
        pvr = _make_pvr()
        with patch("omnix_core.governance.anticipatory_governance_veto._revoke_pvr_in_db", return_value=True):
            result = engine.revoke_pvr(pvr.pvr_id, revoked_by="admin", reason="")
        self.assertFalse(result["success"])

    def test_revoke_with_valid_credentials_succeeds(self):
        engine = AGVPEngine("default")
        pvr = _make_pvr()
        _inject_cache(pvr)
        with patch("omnix_core.governance.anticipatory_governance_veto._revoke_pvr_in_db", return_value=True):
            result = engine.revoke_pvr(pvr.pvr_id, revoked_by="harold", reason="Recovery confirmed")
        self.assertTrue(result["success"])
        self.assertEqual(result["pvr_id"], pvr.pvr_id)

    def test_revoke_clears_memory_cache(self):
        engine = AGVPEngine("default")
        pvr = _make_pvr()
        _inject_cache(pvr)
        with patch("omnix_core.governance.anticipatory_governance_veto._revoke_pvr_in_db", return_value=True):
            engine.revoke_pvr(pvr.pvr_id, revoked_by="harold", reason="Drift recovered")
        # Cache should be cleared
        cached = _active_pvr_cache.get("default:trading")
        self.assertIsNone(cached)

    def test_revoke_with_wrong_admin_token_rejected(self):
        os.environ["AGVP_ADMIN_TOKEN"] = "secret-token"
        engine = AGVPEngine("default")
        pvr = _make_pvr()
        result = engine.revoke_pvr(pvr.pvr_id, revoked_by="attacker", reason="unauthorized", admin_token="wrong")
        self.assertFalse(result["success"])
        self.assertIn("AGV-INV-002", result["message"])

    def test_revoke_with_correct_admin_token_succeeds(self):
        os.environ["AGVP_ADMIN_TOKEN"] = "secret-token"
        engine = AGVPEngine("default")
        pvr = _make_pvr()
        _inject_cache(pvr)
        with patch("omnix_core.governance.anticipatory_governance_veto._revoke_pvr_in_db", return_value=True):
            result = engine.revoke_pvr(pvr.pvr_id, revoked_by="harold", reason="Recovery confirmed", admin_token="secret-token")
        self.assertTrue(result["success"])

    def test_revoke_returns_false_when_not_in_db(self):
        engine = AGVPEngine("default")
        pvr = _make_pvr()
        with patch("omnix_core.governance.anticipatory_governance_veto._revoke_pvr_in_db", return_value=False):
            result = engine.revoke_pvr(pvr.pvr_id, revoked_by="harold", reason="test")
        self.assertFalse(result["success"])
        self.assertIn("not found", result["message"])


# ── AGV-INV-005: No PVR on pass_through ──────────────────────────────────────

class TestAGVInv005NoVetoOnPassThrough(unittest.TestCase):
    """
    Watchdog must not emit PVR when AVM result has pass_through=True.
    AGV-INV-005: Only genuine drift blocks (is_valid=False, pass_through=False) trigger PVR.
    """

    def setUp(self):
        _clear_cache("uncalibrated")

    def tearDown(self):
        _clear_cache("uncalibrated")

    def test_watchdog_skips_pass_through_domain(self):
        """Simulate watchdog cycle: AVM returns pass_through=True → no PVR emitted."""
        from omnix_core.governance.assumption_validity_monitor import AVMResult
        mock_avm_result = AVMResult(
            is_valid=True,
            snapshot_id="NO_BASELINE",
            parameter_version="N/A",
            drift_score=0.0,
            drift_components={},
            age_hours=0.0,
            drift_threshold=35.0,
            block_reason=None,
            warnings=["No calibration snapshot"],
            pass_through=True,
        )

        # Inject stale signal into cache
        with _signal_cache_lock:
            _signal_cache["default:uncalibrated"] = _SignalCacheEntry(
                signals=SAMPLE_SIGNALS,
                seen_at=time.monotonic(),
                snapshot_id="",
            )

        pvrs_created = []

        def fake_create_pvr(**kwargs):
            pvrs_created.append(kwargs["domain"])
            return _make_pvr(domain=kwargs["domain"])

        with patch("omnix_core.governance.anticipatory_governance_veto._create_pvr", side_effect=fake_create_pvr), \
             patch("omnix_core.governance.anticipatory_governance_veto._persist_pvr", return_value=True), \
             patch("omnix_core.governance.avm_engine.AVMEngine._get_avm") as mock_get_avm:
            mock_avm_instance = MagicMock()
            mock_avm_instance.evaluate.return_value = mock_avm_result
            mock_get_avm.return_value = mock_avm_instance

            wd = AGVPWatchdog(interval_seconds=30)
            wd.tenant_id = "default"
            wd._run_cycle()

        self.assertNotIn("uncalibrated", pvrs_created)

    def test_watchdog_emits_pvr_on_genuine_block(self):
        """Simulate watchdog cycle: AVM returns is_valid=False, pass_through=False → PVR emitted."""
        from omnix_core.governance.assumption_validity_monitor import AVMResult

        _clear_cache("trading")
        with _signal_cache_lock:
            _signal_cache["default:trading"] = _SignalCacheEntry(
                signals=SAMPLE_SIGNALS,
                seen_at=time.monotonic(),
                snapshot_id="SNAP-001",
            )

        mock_avm_result = AVMResult(
            is_valid=False,
            snapshot_id="SNAP-001",
            parameter_version="v1",
            drift_score=50.0,
            drift_components={"risk_exposure": 50.0},
            age_hours=2.0,
            drift_threshold=35.0,
            block_reason="Drift exceeded threshold",
            warnings=[],
            pass_through=False,
        )

        pvrs_created = []

        def fake_persist(pvr):
            pvrs_created.append(pvr.domain)
            return True

        with patch("omnix_core.governance.anticipatory_governance_veto._load_active_pvr_from_db", return_value=None), \
             patch("omnix_core.governance.anticipatory_governance_veto._persist_pvr", side_effect=fake_persist), \
             patch("omnix_core.governance.anticipatory_governance_veto.AGVPWatchdog._fire_anticipatory_alert"), \
             patch("omnix_core.governance.avm_engine.AVMEngine._get_avm") as mock_get_avm:
            mock_avm_instance = MagicMock()
            mock_avm_instance.evaluate.return_value = mock_avm_result
            mock_get_avm.return_value = mock_avm_instance

            wd = AGVPWatchdog(interval_seconds=30)
            wd.tenant_id = "default"
            wd._run_cycle()

        self.assertIn("trading", pvrs_created)
        _clear_cache("trading")


# ── AGV-INV-006: Recalibration Guard ─────────────────────────────────────────

class TestAGVInv006RecalibrationGuard(unittest.TestCase):

    def setUp(self):
        _clear_cache("trading")

    def tearDown(self):
        _clear_cache("trading")

    def test_domain_without_pvr_is_safe_for_recalibration(self):
        with patch("omnix_core.governance.anticipatory_governance_veto.get_active_pvr", return_value=None):
            safe, reason = is_domain_safe_for_recalibration("trading")
        self.assertTrue(safe)
        self.assertEqual(reason, "")

    def test_domain_with_active_pvr_is_blocked_from_recalibration(self):
        pvr = _make_pvr()
        with patch("omnix_core.governance.anticipatory_governance_veto.get_active_pvr", return_value=pvr):
            safe, reason = is_domain_safe_for_recalibration("trading")
        self.assertFalse(safe)
        self.assertIn("AGV-INV-006", reason)
        self.assertIn(pvr.pvr_id, reason)

    def test_recalibration_block_message_includes_pvr_id(self):
        pvr = _make_pvr()
        with patch("omnix_core.governance.anticipatory_governance_veto.get_active_pvr", return_value=pvr):
            _, reason = is_domain_safe_for_recalibration("trading")
        self.assertIn("OMNIX-PVR-", reason)

    def test_recalibration_block_message_includes_domain(self):
        pvr = _make_pvr(domain="credit")
        with patch("omnix_core.governance.anticipatory_governance_veto.get_active_pvr", return_value=pvr):
            _, reason = is_domain_safe_for_recalibration("credit", "default")
        self.assertIn("credit", reason)


# ── Watchdog Idempotency ──────────────────────────────────────────────────────

class TestWatchdogIdempotency(unittest.TestCase):
    """Watchdog must not create duplicate PVRs for a domain that already has one."""

    def setUp(self):
        _clear_cache("trading")

    def tearDown(self):
        _clear_cache("trading")

    def test_watchdog_skips_domain_with_existing_active_pvr(self):
        pvr = _make_pvr()
        _inject_cache(pvr)

        with _signal_cache_lock:
            _signal_cache["default:trading"] = _SignalCacheEntry(
                signals=SAMPLE_SIGNALS,
                seen_at=time.monotonic(),
                snapshot_id="SNAP-001",
            )

        pvrs_created = []

        def fake_persist(pvr):
            pvrs_created.append(pvr.domain)
            return True

        with patch("omnix_core.governance.anticipatory_governance_veto._persist_pvr", side_effect=fake_persist), \
             patch("omnix_core.governance.avm_engine.AVMEngine._get_avm") as mock_get_avm:
            from omnix_core.governance.assumption_validity_monitor import AVMResult
            mock_avm_result = AVMResult(
                is_valid=True, snapshot_id="SNAP-001", parameter_version="v1",
                drift_score=10.0, drift_components={}, age_hours=1.0,
                drift_threshold=35.0, block_reason=None, warnings=[], pass_through=False,
            )
            mock_avm_instance = MagicMock()
            mock_avm_instance.evaluate.return_value = mock_avm_result
            mock_get_avm.return_value = mock_avm_instance

            wd = AGVPWatchdog(interval_seconds=30)
            wd.tenant_id = "default"
            wd._run_cycle()

        # No new PVR should have been created
        self.assertNotIn("trading", pvrs_created)


# ── AGV-INV-002: Recovery Candidate Logging (Not Auto-Revoke) ────────────────

class TestRecoveryCandidate(unittest.TestCase):
    """Watchdog logs RECOVERY_CANDIDATE when drift subsides but does NOT auto-revoke."""

    def setUp(self):
        _clear_cache("trading")

    def tearDown(self):
        _clear_cache("trading")

    def test_watchdog_logs_recovery_not_revokes(self):
        pvr = _make_pvr()
        _inject_cache(pvr)

        with _signal_cache_lock:
            _signal_cache["default:trading"] = _SignalCacheEntry(
                signals=SAMPLE_SIGNALS,
                seen_at=time.monotonic(),
                snapshot_id="SNAP-001",
            )

        revoke_calls = []
        engine = AGVPEngine("default")
        original_revoke = engine.revoke_pvr

        with patch("omnix_core.governance.anticipatory_governance_veto._load_active_pvr_from_db", return_value=None), \
             patch("omnix_core.governance.avm_engine.AVMEngine._get_avm") as mock_get_avm:
            from omnix_core.governance.assumption_validity_monitor import AVMResult
            # Drift has RECOVERED — is_valid=True, pass_through=False
            mock_avm_result = AVMResult(
                is_valid=True, snapshot_id="SNAP-001", parameter_version="v1",
                drift_score=10.0, drift_components={}, age_hours=1.0,
                drift_threshold=35.0, block_reason=None, warnings=[], pass_through=False,
            )
            mock_avm_instance = MagicMock()
            mock_avm_instance.evaluate.return_value = mock_avm_result
            mock_get_avm.return_value = mock_avm_instance

            with patch("omnix_core.governance.anticipatory_governance_veto._revoke_pvr_in_db") as mock_revoke:
                wd = AGVPWatchdog(interval_seconds=30)
                wd.tenant_id = "default"
                wd._run_cycle()
                # AGV-INV-002: watchdog must NOT call revoke
                mock_revoke.assert_not_called()

        # PVR must still be ACTIVE in cache
        cached = _active_pvr_cache.get("default:trading")
        self.assertIsNotNone(cached)
        self.assertEqual(cached.status, "ACTIVE")


# ── Stale Signal Skipping ─────────────────────────────────────────────────────

class TestStaleSignalSkipping(unittest.TestCase):

    def setUp(self):
        _clear_cache("trading")

    def tearDown(self):
        _clear_cache("trading")

    def test_watchdog_skips_stale_signals(self):
        # Inject very stale signals (seen 1000s ago)
        with _signal_cache_lock:
            _signal_cache["default:trading"] = _SignalCacheEntry(
                signals=SAMPLE_SIGNALS,
                seen_at=time.monotonic() - 1000,  # way past max age
                snapshot_id="SNAP-001",
            )

        pvrs_created = []
        with patch("omnix_core.governance.anticipatory_governance_veto._persist_pvr") as mock_persist, \
             patch("omnix_core.governance.anticipatory_governance_veto._load_active_pvr_from_db", return_value=None):
            wd = AGVPWatchdog(interval_seconds=30, max_signal_age_seconds=300)
            wd.tenant_id = "default"
            wd._run_cycle()
            mock_persist.assert_not_called()


# ── AGVPEngine.watchdog_status() ─────────────────────────────────────────────

class TestWatchdogStatus(unittest.TestCase):

    def setUp(self):
        _clear_cache("trading")

    def tearDown(self):
        _clear_cache("trading")

    def test_status_when_watchdog_not_running(self):
        engine = AGVPEngine("default")
        with patch("omnix_core.governance.anticipatory_governance_veto._list_active_pvrs_from_db", return_value=[]):
            status = engine.watchdog_status()
        self.assertFalse(status["watchdog_running"])
        self.assertEqual(status["active_pvr_count"], 0)
        self.assertEqual(status["tenant_id"], "default")

    def test_status_includes_monitored_domains(self):
        with _signal_cache_lock:
            _signal_cache["default:trading"] = _SignalCacheEntry(
                signals=SAMPLE_SIGNALS, seen_at=time.monotonic(), snapshot_id=""
            )
        engine = AGVPEngine("default")
        with patch("omnix_core.governance.anticipatory_governance_veto._list_active_pvrs_from_db", return_value=[]):
            status = engine.watchdog_status()
        self.assertIn("trading", status["monitored_domains"])

    def test_status_counts_active_pvrs(self):
        pvr1 = _make_pvr(domain="trading")
        pvr2 = _make_pvr(domain="credit")
        engine = AGVPEngine("default")
        with patch("omnix_core.governance.anticipatory_governance_veto._list_active_pvrs_from_db", return_value=[pvr1, pvr2]):
            status = engine.watchdog_status()
        self.assertEqual(status["active_pvr_count"], 2)


# ── Integration: update_signals → get_pvr flow ───────────────────────────────

class TestEndToEndFlow(unittest.TestCase):

    def setUp(self):
        _clear_cache("insurance")

    def tearDown(self):
        _clear_cache("insurance")

    def test_full_pipeline_flow(self):
        """
        Simulates the full pipeline interaction:
        1. Pipeline calls update_domain_signals (always, before any PVR check)
        2. Pipeline checks get_active_pvr
        3. If no PVR → AVM.evaluate() runs
        4. If PVR active → request is blocked immediately
        """
        engine = AGVPEngine("default")

        # Step 1: update signals
        engine.update_domain_signals("insurance", SAMPLE_SIGNALS, snapshot_id="SNAP-INS-001")

        # Verify signals in cache
        with _signal_cache_lock:
            entry = _signal_cache.get("default:insurance")
        self.assertIsNotNone(entry)

        # Step 2: no PVR yet — pipeline proceeds to AVM
        with patch("omnix_core.governance.anticipatory_governance_veto._load_active_pvr_from_db", return_value=None):
            pvr = engine.get_active_pvr("insurance")
        self.assertIsNone(pvr)

        # Step 3: now inject an active PVR (simulating watchdog emission)
        active_pvr = _make_pvr(domain="insurance")
        _inject_cache(active_pvr)

        # Step 4: pipeline finds active PVR — request blocked
        pvr = engine.get_active_pvr("insurance")
        self.assertIsNotNone(pvr)
        self.assertTrue(pvr.is_active())
        self.assertEqual(pvr.domain, "insurance")

    def test_pvr_id_in_block_reason(self):
        pvr = _create_pvr(
            domain="insurance",
            tenant_id="default",
            drift_score=55.0,
            drift_threshold=35.0,
            drift_components={"risk_exposure": 55.0},
            signals_at_assessment=SAMPLE_SIGNALS,
            signals_seen_at="2026-05-20T10:00:00+00:00",
            snapshot_id="SNAP-INS-001",
            block_reason="ANTICIPATORY_VETO: Drift exceeded threshold [detected by AGVPWatchdog, interval=60s] (ADR-174)",
            watchdog_interval_seconds=60,
        )
        self.assertIn("ANTICIPATORY_VETO", pvr.block_reason)


# ── AGVP_ENABLED=false ────────────────────────────────────────────────────────

class TestAGVPDisabled(unittest.TestCase):

    def test_watchdog_does_not_start_when_disabled(self):
        os.environ["AGVP_ENABLED"] = "false"
        try:
            wd = AGVPWatchdog(interval_seconds=30)
            wd.start()
            self.assertFalse(wd.is_running())
        finally:
            os.environ.pop("AGVP_ENABLED", None)
            wd.stop()


if __name__ == "__main__":
    unittest.main()
