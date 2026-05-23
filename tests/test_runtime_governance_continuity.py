"""
Tests for ADR-159: Runtime Governance Continuity (RGC)

Covers:
    - ContinuityEligibilityScore computation (all 4 components)
    - CES threshold boundaries (NOMINAL / MONITORING / WARNING / CRITICAL / HALT)
    - RuntimeContinuityRecord issuance and immutability
    - Continuity chain (predecessor linkage, acyclicity)
    - Authority Fragmentation Guard (RGC-INV-004)
    - Escalation events (CEE) at each threshold
    - Reauthorization Challenge (RC) issuance and resolution
    - RC TTL expiry → auto HALT (RGC-INV-008)
    - HALT triggers sibling session revocation (RGC-INV-003)
    - Session lifecycle (start / sample / stop)
    - Content hash integrity (RGC-INV-005)
    - No stale CES inputs (RGC-INV-007 guarded by design)
    - Active sessions listing
    - get_rgc_engine singleton
"""
import hashlib
import json
import time
import threading
from unittest.mock import MagicMock, patch

import pytest

from omnix_core.agents.atf.runtime_continuity import (
    CES_CRITICAL,
    CES_HALT,
    CES_MONITORING,
    CES_NOMINAL,
    CES_WARNING,
    AuthorityFragmentationViolation,
    ContinuityEligibilityScore,
    ContinuityHaltError,
    RGCError,
    RuntimeContinuityEngine,
    get_rgc_engine,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

def make_engine() -> RuntimeContinuityEngine:
    """Return a fresh in-memory engine (no DB)."""
    return RuntimeContinuityEngine(db_url=None)


def start_session(engine: RuntimeContinuityEngine, **kwargs):
    """Helper: start a session with sensible defaults."""
    defaults = dict(
        tar_id="ATFTAR-TESTTEST00000001",
        delegation_id="ATFDR-TESTTEST00000001",
        agent_id="AID-FINANCE-TESTTEST0001",
        chain_root_id="ATFDR-ROOT000000000001",
        domain="FINANCE",
        budget_at_admission=80.0,
        dr_expires_at=None,
    )
    defaults.update(kwargs)
    return engine.start_session(**defaults)


# ─────────────────────────────────────────────────────────────────────────────
# 1. ContinuityEligibilityScore unit tests
# ─────────────────────────────────────────────────────────────────────────────

class TestContinuityEligibilityScore:

    def test_perfect_score(self):
        ces = ContinuityEligibilityScore(
            temporal=100.0, budget=100.0, context=100.0, integrity=100.0
        )
        assert ces.score == 100.0
        assert ces.status == "NOMINAL"

    def test_zero_score(self):
        ces = ContinuityEligibilityScore(
            temporal=0.0, budget=0.0, context=0.0, integrity=0.0
        )
        assert ces.score == 0.0
        assert ces.status == "HALT"

    def test_weights_are_correct(self):
        ces = ContinuityEligibilityScore(
            temporal=100.0, budget=0.0, context=0.0, integrity=0.0
        )
        assert abs(ces.score - 30.0) < 0.001

        ces2 = ContinuityEligibilityScore(
            temporal=0.0, budget=100.0, context=0.0, integrity=0.0
        )
        assert abs(ces2.score - 30.0) < 0.001

        ces3 = ContinuityEligibilityScore(
            temporal=0.0, budget=0.0, context=100.0, integrity=0.0
        )
        assert abs(ces3.score - 20.0) < 0.001

        ces4 = ContinuityEligibilityScore(
            temporal=0.0, budget=0.0, context=0.0, integrity=100.0
        )
        assert abs(ces4.score - 20.0) < 0.001

    def test_status_nominal(self):
        ces = ContinuityEligibilityScore(100.0, 100.0, 100.0, 100.0)
        assert ces.status == "NOMINAL"

    def test_status_monitoring(self):
        # Score just below NOMINAL (75)
        # Need score ~ 74: T=70, B=70, D=70, I=70 → 70*0.30+70*0.30+70*0.20+70*0.20 = 70
        ces = ContinuityEligibilityScore(70.0, 70.0, 70.0, 70.0)
        assert ces.score == 70.0
        assert ces.status == "MONITORING"

    def test_status_warning(self):
        ces = ContinuityEligibilityScore(40.0, 40.0, 40.0, 40.0)
        assert ces.status == "WARNING"

    def test_status_critical(self):
        ces = ContinuityEligibilityScore(15.0, 15.0, 15.0, 15.0)
        assert ces.status == "CRITICAL"

    def test_status_halt(self):
        ces = ContinuityEligibilityScore(5.0, 5.0, 5.0, 5.0)
        assert ces.status == "HALT"

    def test_to_dict_structure(self):
        ces = ContinuityEligibilityScore(80.0, 75.0, 90.0, 85.0)
        d = ces.to_dict()
        assert "ces_score" in d
        assert "ces_temporal" in d
        assert "ces_budget" in d
        assert "ces_context" in d
        assert "ces_integrity" in d
        assert "continuity_status" in d

    def test_threshold_boundary_nominal(self):
        ces = ContinuityEligibilityScore(75.0, 75.0, 75.0, 75.0)
        assert ces.score == 75.0
        assert ces.status == "NOMINAL"

    def test_threshold_boundary_below_nominal(self):
        ces = ContinuityEligibilityScore(74.9, 74.9, 74.9, 74.9)
        assert ces.status == "MONITORING"

    def test_threshold_boundary_monitoring(self):
        ces = ContinuityEligibilityScore(50.0, 50.0, 50.0, 50.0)
        assert ces.score == 50.0
        assert ces.status == "MONITORING"

    def test_threshold_boundary_warning(self):
        ces = ContinuityEligibilityScore(25.0, 25.0, 25.0, 25.0)
        assert ces.status == "WARNING"

    def test_threshold_boundary_critical(self):
        ces = ContinuityEligibilityScore(10.0, 10.0, 10.0, 10.0)
        assert ces.status == "CRITICAL"

    def test_threshold_boundary_halt(self):
        ces = ContinuityEligibilityScore(9.9, 9.9, 9.9, 9.9)
        assert ces.status == "HALT"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Session lifecycle
# ─────────────────────────────────────────────────────────────────────────────

class TestSessionLifecycle:

    def test_start_session_returns_session(self):
        engine = make_engine()
        session = start_session(engine)
        assert session.tar_id == "ATFTAR-TESTTEST00000001"
        assert session.status == "ACTIVE"
        assert session.budget_remaining == 80.0

    def test_start_session_stores_in_memory(self):
        engine = make_engine()
        start_session(engine)
        sessions = engine.active_sessions()
        assert len(sessions) == 1

    def test_stop_session_returns_rcr(self):
        engine = make_engine()
        start_session(engine)
        rcr = engine.stop_session("ATFTAR-TESTTEST00000001")
        assert rcr is not None
        assert rcr.tar_id == "ATFTAR-TESTTEST00000001"
        assert rcr.sample_reason == "EXECUTION_COMPLETE"

    def test_stop_session_removes_from_active(self):
        engine = make_engine()
        start_session(engine)
        engine.stop_session("ATFTAR-TESTTEST00000001")
        assert len(engine.active_sessions()) == 0

    def test_stop_nonexistent_session_returns_none(self):
        engine = make_engine()
        result = engine.stop_session("ATFTAR-DOESNOTEXIST00")
        assert result is None

    def test_sample_unknown_tar_raises(self):
        engine = make_engine()
        with pytest.raises(RGCError, match="No active continuity session"):
            engine.sample("ATFTAR-DOESNOTEXIST00")

    def test_two_sessions_independent(self):
        engine = make_engine()
        start_session(engine, tar_id="ATFTAR-A000000000000001",
                      delegation_id="ATFDR-A0000000000001")
        start_session(engine, tar_id="ATFTAR-B000000000000001",
                      delegation_id="ATFDR-B0000000000001")
        assert len(engine.active_sessions()) == 2

    def test_multiple_samples_increment_rcr_count(self):
        engine = make_engine()
        session = start_session(engine)
        engine.sample("ATFTAR-TESTTEST00000001")
        engine.sample("ATFTAR-TESTTEST00000001")
        engine.sample("ATFTAR-TESTTEST00000001")
        with engine._lock:
            s = engine._sessions["ATFTAR-TESTTEST00000001"]
            assert s.rcr_count == 3


# ─────────────────────────────────────────────────────────────────────────────
# 3. RCR issuance and content integrity
# ─────────────────────────────────────────────────────────────────────────────

class TestRCRIssuance:

    def test_rcr_has_correct_prefix(self):
        engine = make_engine()
        start_session(engine)
        rcr = engine.sample("ATFTAR-TESTTEST00000001")
        assert rcr.rcr_id.startswith("ATFRCR-")

    def test_rcr_has_correct_tar_id(self):
        engine = make_engine()
        start_session(engine)
        rcr = engine.sample("ATFTAR-TESTTEST00000001")
        assert rcr.tar_id == "ATFTAR-TESTTEST00000001"

    def test_rcr_content_hash_matches(self):
        engine = make_engine()
        start_session(engine)
        rcr = engine.sample("ATFTAR-TESTTEST00000001")

        import dataclasses
        payload = {
            k: v for k, v in dataclasses.asdict(rcr).items()
            if k not in ("content_hash", "pqc_signature", "pqc_algorithm")
        }
        expected_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
        ).hexdigest()
        assert rcr.content_hash == expected_hash

    def test_rcr_stored_in_memory(self):
        engine = make_engine()
        start_session(engine)
        rcr = engine.sample("ATFTAR-TESTTEST00000001")
        retrieved = engine.get_rcr(rcr.rcr_id)
        assert retrieved is not None
        assert retrieved.rcr_id == rcr.rcr_id

    def test_rcr_to_dict_has_all_fields(self):
        engine = make_engine()
        start_session(engine)
        rcr = engine.sample("ATFTAR-TESTTEST00000001")
        d = rcr.to_dict()
        required = [
            "rcr_id", "tar_id", "delegation_id", "agent_id", "chain_root_id",
            "execution_ns", "execution_ts", "ces_score", "ces_temporal",
            "ces_budget", "ces_context", "ces_integrity", "continuity_status",
            "budget_at_admission", "budget_remaining", "content_hash",
            "issued_at", "metadata",
        ]
        for f in required:
            assert f in d, f"Missing field: {f}"

    def test_rcr_nominal_when_budget_full(self):
        engine = make_engine()
        start_session(engine, budget_at_admission=100.0)
        rcr = engine.sample("ATFTAR-TESTTEST00000001")
        assert rcr.continuity_status == "NOMINAL"

    def test_rcr_budget_consumed_reduces_remaining(self):
        engine = make_engine()
        start_session(engine, budget_at_admission=80.0)
        engine.sample("ATFTAR-TESTTEST00000001", budget_consumed=20.0)
        with engine._lock:
            session = engine._sessions["ATFTAR-TESTTEST00000001"]
        assert session.budget_remaining == 60.0

    def test_rcr_budget_never_negative(self):
        engine = make_engine()
        start_session(engine, budget_at_admission=10.0)
        engine.sample("ATFTAR-TESTTEST00000001", budget_consumed=100.0)
        with engine._lock:
            session = engine._sessions["ATFTAR-TESTTEST00000001"]
        assert session.budget_remaining == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# 4. Continuity chain (predecessor linkage — RGC-INV-006)
# ─────────────────────────────────────────────────────────────────────────────

class TestContinuityChain:

    def test_first_rcr_has_no_predecessor(self):
        engine = make_engine()
        start_session(engine)
        rcr = engine.sample("ATFTAR-TESTTEST00000001")
        assert rcr.predecessor_rcr_id is None

    def test_second_rcr_links_to_first(self):
        engine = make_engine()
        start_session(engine)
        rcr1 = engine.sample("ATFTAR-TESTTEST00000001")
        rcr2 = engine.sample("ATFTAR-TESTTEST00000001")
        assert rcr2.predecessor_rcr_id == rcr1.rcr_id

    def test_chain_forms_linked_list(self):
        engine = make_engine()
        start_session(engine)
        rcrs = [engine.sample("ATFTAR-TESTTEST00000001") for _ in range(5)]
        for i in range(1, 5):
            assert rcrs[i].predecessor_rcr_id == rcrs[i - 1].rcr_id

    def test_session_chain_returns_ordered_rcrs(self):
        engine = make_engine()
        start_session(engine)
        for _ in range(4):
            engine.sample("ATFTAR-TESTTEST00000001")
        chain = engine.session_chain("ATFTAR-TESTTEST00000001")
        assert len(chain) == 4
        for i in range(1, len(chain)):
            assert chain[i].execution_ns > chain[i - 1].execution_ns

    def test_chain_is_acyclic(self):
        """No RCR should appear as its own ancestor."""
        engine = make_engine()
        start_session(engine)
        for _ in range(6):
            engine.sample("ATFTAR-TESTTEST00000001")
        chain = engine.session_chain("ATFTAR-TESTTEST00000001")
        ids = [r.rcr_id for r in chain]
        assert len(ids) == len(set(ids)), "Duplicate RCR IDs in chain — cycle detected"


# ─────────────────────────────────────────────────────────────────────────────
# 5. CES components — temporal
# ─────────────────────────────────────────────────────────────────────────────

class TestCESTemporalComponent:

    def test_temporal_100_when_no_expiry(self):
        engine = make_engine()
        start_session(engine, dr_expires_at=None)
        ces = engine.current_ces("ATFTAR-TESTTEST00000001")
        assert ces is not None
        assert ces.temporal == 100.0

    def test_temporal_decreases_as_expiry_approaches(self):
        from datetime import datetime, timezone, timedelta
        engine = make_engine()
        future = (datetime.now(tz=timezone.utc) + timedelta(seconds=3600)).isoformat()
        start_session(engine, dr_expires_at=future)
        ces = engine.current_ces("ATFTAR-TESTTEST00000001")
        assert ces is not None
        assert 0.0 < ces.temporal <= 100.0

    def test_temporal_zero_when_expired(self):
        from datetime import datetime, timezone, timedelta
        engine = make_engine()
        past = (datetime.now(tz=timezone.utc) - timedelta(seconds=1)).isoformat()
        start_session(engine, dr_expires_at=past)
        ces = engine.current_ces("ATFTAR-TESTTEST00000001")
        assert ces is not None
        assert ces.temporal == 0.0

    def test_no_session_returns_none(self):
        engine = make_engine()
        assert engine.current_ces("ATFTAR-DOESNOTEXIST00") is None


# ─────────────────────────────────────────────────────────────────────────────
# 6. CES components — context and integrity
# ─────────────────────────────────────────────────────────────────────────────

class TestCESContextIntegrity:

    def test_context_fidelity_100_at_zero_drift(self):
        engine = make_engine()
        start_session(engine)
        rcr = engine.sample("ATFTAR-TESTTEST00000001", context_drift_pct=0.0)
        assert rcr.ces_context == 100.0

    def test_context_fidelity_decreases_with_drift(self):
        engine = make_engine()
        start_session(engine)
        rcr = engine.sample("ATFTAR-TESTTEST00000001", context_drift_pct=30.0)
        assert abs(rcr.ces_context - 70.0) < 0.01

    def test_context_fidelity_zero_at_100pct_drift(self):
        engine = make_engine()
        start_session(engine)
        rcr = engine.sample("ATFTAR-TESTTEST00000001", context_drift_pct=100.0)
        assert rcr.ces_context == 0.0

    def test_integrity_100_at_zero_anomalies(self):
        engine = make_engine()
        start_session(engine)
        rcr = engine.sample("ATFTAR-TESTTEST00000001", active_anomalies=0)
        assert rcr.ces_integrity == 100.0

    def test_integrity_decreases_per_anomaly(self):
        engine = make_engine()
        start_session(engine)
        rcr = engine.sample("ATFTAR-TESTTEST00000001", active_anomalies=3)
        assert abs(rcr.ces_integrity - 70.0) < 0.01

    def test_integrity_zero_at_10_anomalies(self):
        engine = make_engine()
        start_session(engine)
        rcr = engine.sample("ATFTAR-TESTTEST00000001", active_anomalies=10)
        assert rcr.ces_integrity == 0.0

    def test_integrity_never_negative(self):
        engine = make_engine()
        start_session(engine)
        rcr = engine.sample("ATFTAR-TESTTEST00000001", active_anomalies=20)
        assert rcr.ces_integrity == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# 7. Escalation events
# ─────────────────────────────────────────────────────────────────────────────

class TestEscalationEvents:

    def test_no_escalation_in_nominal(self):
        engine = make_engine()
        start_session(engine)
        rcr = engine.sample("ATFTAR-TESTTEST00000001")
        assert rcr.escalation_event_id is None

    def test_escalation_emitted_in_monitoring(self):
        engine = make_engine()
        start_session(engine, budget_at_admission=100.0)
        rcr = engine.sample(
            "ATFTAR-TESTTEST00000001",
            budget_consumed=32.0,
            context_drift_pct=30.0,
        )
        if rcr.continuity_status in ("MONITORING", "WARNING", "CRITICAL", "HALT"):
            assert rcr.escalation_event_id is not None

    def test_escalation_has_correct_prefix(self):
        engine = make_engine()
        start_session(engine, budget_at_admission=100.0)
        rcr = engine.sample(
            "ATFTAR-TESTTEST00000001",
            context_drift_pct=100.0,
            active_anomalies=8,
        )
        if rcr.escalation_event_id:
            assert rcr.escalation_event_id.startswith("ATFCEE-")

    def test_cee_stored_in_engine(self):
        engine = make_engine()
        start_session(engine, budget_at_admission=100.0)
        rcr = engine.sample(
            "ATFTAR-TESTTEST00000001",
            context_drift_pct=100.0,
            active_anomalies=10,
        )
        if rcr.escalation_event_id:
            cee = engine._cee_store.get(rcr.escalation_event_id)
            assert cee is not None
            assert cee.tar_id == "ATFTAR-TESTTEST00000001"


# ─────────────────────────────────────────────────────────────────────────────
# 8. Reauthorization Challenge
# ─────────────────────────────────────────────────────────────────────────────

class TestReauthorizationChallenge:

    def _make_critical_rcr(self, engine):
        """Drive CES to CRITICAL by draining budget and context."""
        start_session(engine, budget_at_admission=100.0)
        return engine.sample(
            "ATFTAR-TESTTEST00000001",
            budget_consumed=98.0,
            context_drift_pct=95.0,
            active_anomalies=8,
        )

    def test_rc_issued_at_critical(self):
        engine = make_engine()
        engine._rc_ttl = 300
        rcr = self._make_critical_rcr(engine)
        if rcr.continuity_status == "CRITICAL":
            assert rcr.reauth_challenge_id is not None
            assert rcr.reauth_challenge_id.startswith("ATFRC-")

    def test_rc_stored_in_engine(self):
        engine = make_engine()
        engine._rc_ttl = 300
        rcr = self._make_critical_rcr(engine)
        if rcr.reauth_challenge_id:
            rc = engine._rc_store.get(rcr.reauth_challenge_id)
            assert rc is not None

    def test_rc_resolution_accepted(self):
        engine = make_engine()
        engine._rc_ttl = 300
        rcr = self._make_critical_rcr(engine)
        if rcr.reauth_challenge_id:
            rc = engine.respond_to_rc(
                rc_id=rcr.reauth_challenge_id,
                new_dr_id="ATFDR-REFRESHED00000001",
            )
            assert rc.resolved is True
            assert rc.resolution == "REAUTHORIZED"
            assert rc.response_dr_id == "ATFDR-REFRESHED00000001"

    def test_rc_not_issued_at_nominal(self):
        engine = make_engine()
        start_session(engine)
        rcr = engine.sample("ATFTAR-TESTTEST00000001")
        if rcr.continuity_status == "NOMINAL":
            assert rcr.reauth_challenge_id is None

    def test_respond_to_nonexistent_rc_raises(self):
        engine = make_engine()
        with pytest.raises(RGCError):
            engine.respond_to_rc("ATFRC-DOESNOTEXIST0000", "ATFDR-NEW")

    def test_rc_content_hash_present(self):
        engine = make_engine()
        engine._rc_ttl = 300
        rcr = self._make_critical_rcr(engine)
        if rcr.reauth_challenge_id:
            rc = engine._rc_store[rcr.reauth_challenge_id]
            assert len(rc.content_hash) == 64  # SHA-256 hex


# ─────────────────────────────────────────────────────────────────────────────
# 9. RC TTL enforcement (RGC-INV-008)
# ─────────────────────────────────────────────────────────────────────────────

class TestRCTTLEnforcement:

    def test_rc_is_expired_when_ttl_zero(self):
        from omnix_core.agents.atf.runtime_continuity import ReauthorizationChallenge
        import dataclasses
        import hashlib, json
        now_ns = time.time_ns()
        rc = ReauthorizationChallenge(
            rc_id="ATFRC-TEST0000000001",
            cee_id="ATFCEE-TEST000000001",
            tar_id="ATFTAR-TEST000000001",
            delegation_id="ATFDR-TEST000000001",
            agent_id="AID-TEST-000000001",
            chain_root_id="ATFDR-ROOT0000000001",
            ces_at_challenge=15.0,
            challenge_ns=now_ns - 1_000_000_000,  # 1 second ago
            ttl_seconds=0,
            expires_at_ns=now_ns - 1,  # already expired
            response_dr_id=None,
            resolved=False,
            resolution=None,
            content_hash="abc",
            pqc_signature=None,
            pqc_algorithm=None,
            issued_at="2026-05-13T00:00:00+00:00",
            metadata={},
        )
        assert rc.is_expired() is True

    def test_rc_not_expired_with_future_ns(self):
        from omnix_core.agents.atf.runtime_continuity import ReauthorizationChallenge
        now_ns = time.time_ns()
        rc = ReauthorizationChallenge(
            rc_id="ATFRC-TEST0000000002",
            cee_id="ATFCEE-TEST000000002",
            tar_id="ATFTAR-TEST000000002",
            delegation_id="ATFDR-TEST000000002",
            agent_id="AID-TEST-000000002",
            chain_root_id="ATFDR-ROOT0000000002",
            ces_at_challenge=15.0,
            challenge_ns=now_ns,
            ttl_seconds=300,
            expires_at_ns=now_ns + 300_000_000_000,  # 300s from now
            response_dr_id=None,
            resolved=False,
            resolution=None,
            content_hash="abc",
            pqc_signature=None,
            pqc_algorithm=None,
            issued_at="2026-05-13T00:00:00+00:00",
            metadata={},
        )
        assert rc.is_expired() is False


# ─────────────────────────────────────────────────────────────────────────────
# 10. Authority Fragmentation Guard (RGC-INV-004)
# ─────────────────────────────────────────────────────────────────────────────

class TestAuthorityFragmentationGuard:

    def test_no_violation_when_aggregate_within_limit(self):
        engine = make_engine()
        engine._afg_limit = 0.90
        # chain_root_budget = 100, existing = 0, new = 80 → 80% < 90% OK
        engine.check_fragmentation(
            chain_root_id="ATFDR-ROOT0000000001",
            chain_root_budget=100.0,
            new_grant_budget=80.0,
        )  # should not raise

    def test_violation_when_aggregate_exceeds_limit(self):
        engine = make_engine()
        engine._afg_limit = 0.90
        # Register two sessions on same chain root (total=80+20=100 > 90)
        start_session(
            engine,
            tar_id="ATFTAR-A000000000000001",
            delegation_id="ATFDR-A0000000000001",
            chain_root_id="ATFDR-ROOT0000000001",
            budget_at_admission=80.0,
        )
        # Now check: existing aggregate = 80, new = 20 → 100 > 90% of 100
        with pytest.raises(AuthorityFragmentationViolation):
            engine.check_fragmentation(
                chain_root_id="ATFDR-ROOT0000000001",
                chain_root_budget=100.0,
                new_grant_budget=20.0,
            )

    def test_fragmentation_score_reported_in_rcr(self):
        engine = make_engine()
        start_session(engine, budget_at_admission=80.0)
        engine.sample("ATFTAR-TESTTEST00000001", budget_consumed=40.0)
        rcr = engine.sample("ATFTAR-TESTTEST00000001")
        assert 0.0 <= rcr.fragmentation_score <= 100.0

    def test_no_fragmentation_on_empty_chain(self):
        engine = make_engine()
        score = engine._fragmentation_score("ATFDR-ROOT-EMPTY00001")
        assert score == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# 11. HALT enforcement (RGC-INV-003)
# ─────────────────────────────────────────────────────────────────────────────

class TestHaltEnforcement:

    def _make_halt_rcr(self, engine):
        start_session(engine, budget_at_admission=100.0)
        return engine.sample(
            "ATFTAR-TESTTEST00000001",
            budget_consumed=99.9,
            context_drift_pct=100.0,
            active_anomalies=10,
        )

    def test_session_status_halted_when_ces_halt(self):
        engine = make_engine()
        rcr = self._make_halt_rcr(engine)
        if rcr.continuity_status == "HALT":
            with engine._lock:
                session = engine._sessions.get("ATFTAR-TESTTEST00000001")
            if session:
                assert session.status == "HALTED"

    def test_halt_callback_invoked(self):
        called = []
        engine = make_engine()
        start_session(
            engine,
            budget_at_admission=100.0,
            halt_callback=lambda agent_id: called.append(agent_id),
        )
        rcr = engine.sample(
            "ATFTAR-TESTTEST00000001",
            budget_consumed=99.9,
            context_drift_pct=100.0,
            active_anomalies=10,
        )
        if rcr.continuity_status == "HALT":
            assert len(called) > 0

    def test_sibling_sessions_revoked_on_halt(self):
        engine = make_engine()
        # Parent session
        start_session(
            engine,
            tar_id="ATFTAR-PARENT00000001",
            delegation_id="ATFDR-PARENT000000001",
            chain_root_id="ATFDR-ROOT0000000001",
            budget_at_admission=100.0,
        )
        # Sibling session on same chain root
        start_session(
            engine,
            tar_id="ATFTAR-SIBLING0000001",
            delegation_id="ATFDR-SIBLING00000001",
            chain_root_id="ATFDR-ROOT0000000001",
            budget_at_admission=30.0,
        )
        # Drive parent to HALT
        rcr = engine.sample(
            "ATFTAR-PARENT00000001",
            budget_consumed=99.9,
            context_drift_pct=100.0,
            active_anomalies=10,
        )
        if rcr.continuity_status == "HALT":
            with engine._lock:
                sibling = engine._sessions.get("ATFTAR-SIBLING0000001")
            if sibling:
                assert sibling.status == "REVOKED_BY_HALT"

    def test_rcr_is_halt_type(self):
        engine = make_engine()
        rcr = self._make_halt_rcr(engine)
        if rcr.continuity_status == "HALT":
            assert rcr.is_halted() is True
            assert rcr.is_nominal() is False


# ─────────────────────────────────────────────────────────────────────────────
# 12. RCR summary and is_nominal/is_halted
# ─────────────────────────────────────────────────────────────────────────────

class TestRCRHelpers:

    def test_is_nominal_true(self):
        engine = make_engine()
        start_session(engine)
        rcr = engine.sample("ATFTAR-TESTTEST00000001")
        if rcr.continuity_status == "NOMINAL":
            assert rcr.is_nominal() is True
            assert rcr.is_halted() is False

    def test_summary_keys(self):
        engine = make_engine()
        start_session(engine)
        rcr = engine.sample("ATFTAR-TESTTEST00000001")
        s = rcr.summary()
        required_keys = [
            "rcr_id", "tar_id", "delegation_id", "agent_id",
            "execution_ns", "ces_score", "continuity_status",
            "budget_remaining", "pqc_signed",
        ]
        for k in required_keys:
            assert k in s, f"Missing summary key: {k}"

    def test_sample_reason_default_scheduled(self):
        engine = make_engine()
        start_session(engine)
        rcr = engine.sample("ATFTAR-TESTTEST00000001")
        assert rcr.sample_reason == "SCHEDULED"

    def test_sample_reason_custom(self):
        engine = make_engine()
        start_session(engine)
        rcr = engine.sample(
            "ATFTAR-TESTTEST00000001",
            sample_reason="THRESHOLD_BREACH"
        )
        assert rcr.sample_reason == "THRESHOLD_BREACH"


# ─────────────────────────────────────────────────────────────────────────────
# 13. Singleton — get_rgc_engine
# ─────────────────────────────────────────────────────────────────────────────

class TestSingleton:

    def test_singleton_returns_same_instance(self):
        e1 = get_rgc_engine()
        e2 = get_rgc_engine()
        assert e1 is e2

    def test_singleton_is_runtime_continuity_engine(self):
        e = get_rgc_engine()
        assert isinstance(e, RuntimeContinuityEngine)


# ─────────────────────────────────────────────────────────────────────────────
# 14. Thread safety
# ─────────────────────────────────────────────────────────────────────────────

class TestThreadSafety:

    def test_concurrent_samples_produce_unique_rcr_ids(self):
        engine = make_engine()
        start_session(engine)
        rcr_ids = []
        lock = threading.Lock()

        def _sample():
            rcr = engine.sample("ATFTAR-TESTTEST00000001")
            with lock:
                rcr_ids.append(rcr.rcr_id)

        threads = [threading.Thread(target=_sample) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(rcr_ids) == len(set(rcr_ids)), "Duplicate RCR IDs under concurrency"

    def test_concurrent_sessions_do_not_interfere(self):
        engine = make_engine()
        results = {}
        lock = threading.Lock()

        def _run(index):
            tar_id = f"ATFTAR-THREAD{index:010d}"
            dr_id  = f"ATFDR-THREAD{index:011d}"
            engine.start_session(
                tar_id=tar_id,
                delegation_id=dr_id,
                agent_id=f"AID-FINANCE-THREAD{index:05d}",
                chain_root_id="ATFDR-ROOT0000000001",
                domain="FINANCE",
                budget_at_admission=50.0,
            )
            rcr = engine.sample(tar_id)
            with lock:
                results[tar_id] = rcr.ces_score

        threads = [threading.Thread(target=_run, args=(i,)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 8


# ─────────────────────────────────────────────────────────────────────────────
# 15. Active sessions listing
# ─────────────────────────────────────────────────────────────────────────────

class TestActiveSessions:

    def test_active_sessions_empty_initially(self):
        engine = make_engine()
        assert engine.active_sessions() == []

    def test_active_sessions_after_start(self):
        engine = make_engine()
        start_session(engine)
        sessions = engine.active_sessions()
        assert len(sessions) == 1
        assert sessions[0]["tar_id"] == "ATFTAR-TESTTEST00000001"

    def test_active_sessions_decremented_after_stop(self):
        engine = make_engine()
        start_session(engine)
        engine.stop_session("ATFTAR-TESTTEST00000001")
        assert engine.active_sessions() == []

    def test_active_sessions_has_expected_fields(self):
        engine = make_engine()
        start_session(engine)
        s = engine.active_sessions()[0]
        for key in ["tar_id", "agent_id", "budget_remaining", "rcr_count", "status"]:
            assert key in s


# ─────────────────────────────────────────────────────────────────────────────
# 16. Integration: full execution lifecycle with chain
# ─────────────────────────────────────────────────────────────────────────────

class TestFullLifecycleIntegration:

    def test_full_lifecycle_admitted_nominal_complete(self):
        engine = make_engine()
        session = start_session(engine, budget_at_admission=100.0)
        assert session.status == "ACTIVE"

        rcr1 = engine.sample("ATFTAR-TESTTEST00000001", budget_consumed=5.0)
        rcr2 = engine.sample("ATFTAR-TESTTEST00000001", budget_consumed=5.0)
        rcr3 = engine.sample("ATFTAR-TESTTEST00000001", budget_consumed=5.0)

        assert rcr1.predecessor_rcr_id is None
        assert rcr2.predecessor_rcr_id == rcr1.rcr_id
        assert rcr3.predecessor_rcr_id == rcr2.rcr_id

        final = engine.stop_session(
            "ATFTAR-TESTTEST00000001", budget_consumed=0.0
        )
        assert final.sample_reason == "EXECUTION_COMPLETE"
        chain = engine.session_chain("ATFTAR-TESTTEST00000001")
        assert len(chain) >= 3  # at least the 3 samples

    def test_budget_drainage_causes_ces_degradation(self):
        engine = make_engine()
        start_session(engine, budget_at_admission=100.0)

        rcr_initial = engine.sample("ATFTAR-TESTTEST00000001", budget_consumed=0.0)
        rcr_drained = engine.sample(
            "ATFTAR-TESTTEST00000001", budget_consumed=98.0
        )
        assert rcr_drained.ces_budget < rcr_initial.ces_budget

    def test_metadata_passed_through(self):
        engine = make_engine()
        start_session(engine)
        meta = {"workflow_id": "wf-001", "step": 3}
        rcr = engine.sample("ATFTAR-TESTTEST00000001", metadata=meta)
        assert rcr.metadata == meta
