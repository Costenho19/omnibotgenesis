"""
Tests — ADR-130 v2: Event-driven AVM domain suspension.

Validates that when the GovernanceEvaluationEngine fires a STALE_BLOCK,
fire_avm_domain_suspension() is dispatched immediately (not in 24h cycle)
and _suspend_domain_vcs() correctly suspends all active VCs for the domain.

Dr. Todd M. Price requirement (item 4):
  'Assumption tracking must be active and time-sensitive, capable of
  invalidating decisions when conditions change.'
"""

import os
import threading
import time
from unittest.mock import MagicMock, call, patch

import pytest

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _import_fire():
    from omnix_web.api.omnix_engine.vc_revocation import fire_avm_domain_suspension
    return fire_avm_domain_suspension


def _import_suspend():
    from omnix_web.api.omnix_engine.vc_revocation import _suspend_domain_vcs
    return _suspend_domain_vcs


# ── T1: fire_avm_domain_suspension starts a daemon thread ─────────────────────

class TestFireAvmDomainSuspensionDispatch:

    def test_dispatches_daemon_thread(self):
        """fire_avm_domain_suspension() must return immediately and start a daemon thread."""
        fire = _import_fire()

        started_threads: list[threading.Thread] = []

        _real_Thread = threading.Thread
        def _fake_Thread(*args, **kwargs):
            t = _real_Thread(*args, **kwargs)
            started_threads.append(t)
            return t

        with patch("omnix_web.api.omnix_engine.vc_revocation.threading.Thread", _fake_Thread):
            t0 = time.monotonic()
            fire(domain="trading", drift_score=52.3, snapshot_id="snap-abc", asset="BTC")
            elapsed = time.monotonic() - t0

        assert elapsed < 0.1, "fire_avm_domain_suspension must return in < 100ms"
        assert len(started_threads) == 1
        assert started_threads[0].daemon is True
        assert "AVM-EventSuspension" in started_threads[0].name

    def test_thread_name_includes_domain(self):
        """Thread name must carry the domain for observability."""
        fire = _import_fire()
        started = []

        _real_Thread = threading.Thread
        def _capture(*args, **kwargs):
            t = _real_Thread(*args, **kwargs)
            started.append(t)
            return t

        with patch("omnix_web.api.omnix_engine.vc_revocation.threading.Thread", _capture):
            fire(domain="insurance", drift_score=40.0, snapshot_id="snap-xyz")

        assert "insurance" in started[0].name


# ── T2: _suspend_domain_vcs — no active VCs → no revocation ───────────────────

class TestSuspendDomainVcsNoVCs:

    def test_empty_result_skips_revocation(self):
        """When DB returns no rows, VCRevocationRegistry.revoke must NOT be called."""
        suspend = _import_suspend()

        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = []

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        with patch("omnix_web.api.omnix_engine.vc_revocation._get_db_conn", return_value=mock_conn), \
             patch("omnix_web.api.omnix_engine.vc_revocation.VCRevocationRegistry") as MockRegistry:

            suspend(domain="trading", drift_score=55.0, snapshot_id="snap-001")

            MockRegistry.return_value.revoke.assert_not_called()

    def test_db_error_does_not_raise(self):
        """DB failure must be caught silently — never propagate."""
        suspend = _import_suspend()

        with patch("omnix_web.api.omnix_engine.vc_revocation._get_db_conn",
                   side_effect=Exception("DB connection refused")):
            # Must NOT raise
            suspend(domain="trading", drift_score=55.0, snapshot_id="snap-001")


# ── T3: _suspend_domain_vcs — active VCs → suspended with system:avm ──────────

class TestSuspendDomainVcsWithActiveVCs:

    def _make_db_mock(self, receipt_ids: list[str]):
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = [(rid,) for rid in receipt_ids]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        return mock_conn

    def test_single_vc_suspended_with_correct_actor(self):
        """One active VC → revoke called with revoked_by='system:avm' and status='suspended'."""
        suspend = _import_suspend()
        conn = self._make_db_mock(["RECEIPT-001"])

        with patch("omnix_web.api.omnix_engine.vc_revocation._get_db_conn", return_value=conn), \
             patch("omnix_web.api.omnix_engine.vc_revocation.VCRevocationRegistry") as MockReg:

            suspend(
                domain="trading",
                drift_score=62.5,
                snapshot_id="snap-trading-v3",
                asset="ETH",
            )

            MockReg.return_value.revoke.assert_called_once()
            call_kwargs = MockReg.return_value.revoke.call_args
            assert call_kwargs.kwargs["receipt_id"] == "RECEIPT-001"
            assert call_kwargs.kwargs["revoked_by"] == "system:avm"
            assert call_kwargs.kwargs["status"] == "suspended"
            assert "drift" in call_kwargs.kwargs["reason"].lower()

    def test_multiple_vcs_all_suspended(self):
        """Multiple active VCs → all suspended in single invocation."""
        suspend = _import_suspend()
        receipt_ids = [f"RECEIPT-{i:03d}" for i in range(5)]
        conn = self._make_db_mock(receipt_ids)

        with patch("omnix_web.api.omnix_engine.vc_revocation._get_db_conn", return_value=conn), \
             patch("omnix_web.api.omnix_engine.vc_revocation.VCRevocationRegistry") as MockReg:

            suspend(domain="insurance", drift_score=78.1, snapshot_id="snap-ins-001")

            assert MockReg.return_value.revoke.call_count == 5

            for i, rid in enumerate(receipt_ids):
                c = MockReg.return_value.revoke.call_args_list[i]
                assert c.kwargs["receipt_id"] == rid
                assert c.kwargs["status"] == "suspended"

    def test_context_block_includes_adr_and_trigger(self):
        """Context passed to revoke must document ADR-130 and event-driven trigger."""
        suspend = _import_suspend()
        conn = self._make_db_mock(["RECEIPT-A"])

        with patch("omnix_web.api.omnix_engine.vc_revocation._get_db_conn", return_value=conn), \
             patch("omnix_web.api.omnix_engine.vc_revocation.VCRevocationRegistry") as MockReg:

            suspend(domain="trading", drift_score=44.0, snapshot_id="snap-x", asset="SOL")

            ctx = MockReg.return_value.revoke.call_args.kwargs["context"]
            assert ctx["adr"] == "ADR-130"
            assert "STALE_BLOCK" in ctx["trigger"]
            assert ctx["domain"] == "trading"
            assert ctx["asset"] == "SOL"
            assert abs(ctx["drift_score"] - 44.0) < 0.01

    def test_already_revoked_vc_is_skipped_gracefully(self):
        """ValueError from revoke (already suspended) must not abort the loop."""
        suspend = _import_suspend()
        conn = self._make_db_mock(["R-ALREADY", "R-ACTIVE"])

        mock_reg = MagicMock()
        mock_reg.revoke.side_effect = [ValueError("already suspended"), None]

        with patch("omnix_web.api.omnix_engine.vc_revocation._get_db_conn", return_value=conn), \
             patch("omnix_web.api.omnix_engine.vc_revocation.VCRevocationRegistry",
                   return_value=mock_reg):

            suspend(domain="trading", drift_score=50.0, snapshot_id="snap-2")

            assert mock_reg.revoke.call_count == 2
            assert mock_reg.revoke.call_args_list[1].kwargs["receipt_id"] == "R-ACTIVE"


# ── T4: DB query shape — domain filter, 24h window ────────────────────────────

class TestSuspendDomainVcsQueryShape:

    def test_query_filters_by_domain(self):
        """DB query must pass the domain as a parameter."""
        suspend = _import_suspend()

        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = []
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        with patch("omnix_web.api.omnix_engine.vc_revocation._get_db_conn",
                   return_value=mock_conn), \
             patch("omnix_web.api.omnix_engine.vc_revocation.VCRevocationRegistry"):

            suspend(domain="derivatives", drift_score=40.0, snapshot_id="snap-d")

            sql_call = mock_cur.execute.call_args
            params = sql_call[0][1] if sql_call[0] else sql_call.args[1]
            assert "derivatives" in params

    def test_query_includes_24h_window(self):
        """SQL must include a 24-hour recency filter."""
        suspend = _import_suspend()

        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = []
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        with patch("omnix_web.api.omnix_engine.vc_revocation._get_db_conn",
                   return_value=mock_conn), \
             patch("omnix_web.api.omnix_engine.vc_revocation.VCRevocationRegistry"):

            suspend(domain="trading", drift_score=40.0, snapshot_id="snap-t")

            sql_text = mock_cur.execute.call_args[0][0]
            assert "24 hours" in sql_text or "INTERVAL" in sql_text


# ── T5: Integration — external_evaluator triggers suspension on STALE_BLOCK ───

class TestExternalEvaluatorFiresHookOnStaleBlock:
    """
    Confirms that GovernanceEvaluationEngine.evaluate() calls
    fire_avm_domain_suspension when AVM returns is_valid=False.

    Uses sys.modules injection so the lazy import inside external_evaluator.py
    resolves to our mock regardless of which import path fires (api.* or omnix_engine.*).
    """

    def _make_stale_avm_result(self, drift_score=60.0, snapshot_id="snap-test"):
        result = MagicMock()
        result.is_valid = False
        result.pass_through = False
        result.drift_score = drift_score
        result.drift_threshold = 35.0
        result.snapshot_id = snapshot_id
        result.parameter_version = "v1"
        result.block_reason = "Drift exceeded threshold"
        result.age_hours = 48.0
        result.warnings = []
        result.to_dict.return_value = {
            "is_valid": False,
            "drift_score": drift_score,
            "snapshot_id": snapshot_id,
        }
        return result

    def _inject_api_mock(self, mock_fire_fn) -> dict:
        """
        Injects fake 'api.omnix_engine.vc_revocation' into sys.modules so the
        lazy import in external_evaluator.py resolves during the test.
        Returns a dict of injected keys for cleanup.
        """
        import sys
        import types

        fake_vc_mod = types.ModuleType("api.omnix_engine.vc_revocation")
        fake_vc_mod.fire_avm_domain_suspension = mock_fire_fn

        fake_omnix_mod = types.ModuleType("api.omnix_engine")
        fake_omnix_mod.vc_revocation = fake_vc_mod

        fake_api_mod = types.ModuleType("api")
        fake_api_mod.omnix_engine = fake_omnix_mod

        injected = {
            "api": fake_api_mod,
            "api.omnix_engine": fake_omnix_mod,
            "api.omnix_engine.vc_revocation": fake_vc_mod,
        }
        sys.modules.update(injected)
        return injected

    def _cleanup_api_mock(self, injected: dict) -> None:
        import sys
        for key in injected:
            sys.modules.pop(key, None)

    def test_stale_block_calls_fire_avm_domain_suspension(self):
        """STALE_BLOCK path must call fire_avm_domain_suspension before returning."""
        import sys

        try:
            from omnix_core.governance.external_evaluator import GovernanceEvaluationEngine
        except ImportError:
            pytest.skip("external_evaluator not importable in this environment")

        mock_fire = MagicMock()
        injected = self._inject_api_mock(mock_fire)

        # Also patch the omnix_engine path in case that one fires first
        also_patch = "omnix_web.api.omnix_engine.vc_revocation"

        stale_result = self._make_stale_avm_result()
        mock_avm = MagicMock()
        mock_avm.evaluate.return_value = stale_result

        try:
            with patch("omnix_core.governance.external_evaluator._AVM_AVAILABLE", True), \
                 patch("omnix_core.governance.external_evaluator.get_avm_instance",
                       return_value=mock_avm), \
                 patch("omnix_core.governance.external_evaluator._SAE_AVAILABLE", False):

                engine = GovernanceEvaluationEngine()
                signals = {
                    "probability_score": 0.7,
                    "risk_exposure": 0.4,
                    "signal_coherence": 0.8,
                    "volatility_regime": 0.5,
                    "liquidity_score": 0.6,
                    "drawdown_risk": 0.3,
                }
                result = engine.evaluate(
                    signals=signals,
                    asset="BTC",
                    domain="trading",
                )
        finally:
            self._cleanup_api_mock(injected)

        assert result["decision"] == "BLOCKED"
        any_stale = any(
            v.get("result") == "STALE_BLOCK"
            for v in result.get("veto_chain", [])
        )
        assert any_stale, "veto_chain must contain STALE_BLOCK"
        # fire must have been called with correct kwargs
        mock_fire.assert_called_once_with(
            domain="trading",
            drift_score=stale_result.drift_score,
            snapshot_id=str(stale_result.snapshot_id),
            asset="BTC",
        )

    def test_valid_avm_does_not_trigger_suspension(self):
        """When AVM passes (is_valid=True), fire_avm_domain_suspension must NOT be called."""
        try:
            from omnix_core.governance.external_evaluator import GovernanceEvaluationEngine
        except ImportError:
            pytest.skip("external_evaluator not importable in this environment")

        mock_fire = MagicMock()
        injected = self._inject_api_mock(mock_fire)

        valid_result = MagicMock()
        valid_result.is_valid = True
        valid_result.pass_through = False
        valid_result.drift_score = 12.0
        valid_result.drift_threshold = 35.0
        valid_result.snapshot_id = "snap-valid"
        valid_result.warnings = []
        valid_result.to_dict.return_value = {"is_valid": True}

        mock_avm = MagicMock()
        mock_avm.evaluate.return_value = valid_result

        try:
            with patch("omnix_core.governance.external_evaluator._AVM_AVAILABLE", True), \
                 patch("omnix_core.governance.external_evaluator.get_avm_instance",
                       return_value=mock_avm), \
                 patch("omnix_core.governance.external_evaluator._SAE_AVAILABLE", False):

                engine = GovernanceEvaluationEngine()
                signals = {
                    "probability_score": 0.7,
                    "risk_exposure": 0.4,
                    "signal_coherence": 0.8,
                    "volatility_regime": 0.5,
                    "liquidity_score": 0.6,
                    "drawdown_risk": 0.3,
                }
                engine.evaluate(
                    signals=signals,
                    asset="ETH",
                    domain="trading",
                )
        finally:
            self._cleanup_api_mock(injected)

        mock_fire.assert_not_called()
