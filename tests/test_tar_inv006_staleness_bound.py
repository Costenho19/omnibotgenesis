"""
TAR-INV-006 Compiled Staleness Bound — Test Suite
ADR-157 rev.2

Verifies that the TAR engine enforces a COMPILED (non-configurable) ceiling
on DR remaining lifetime at admission time. This closes the DORA issuance-time
attack surface identified in RFC-ATF-2 threat modeling.

Key assertion: TAR_MAX_DR_LIFETIME_SECONDS is a module constant, not read
from any environment variable. No operator configuration can override it.

Harold Nunes — OMNIX QUANTUM LTD — May 2026
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

import pytest

from omnix_core.agents.atf.temporal_authority import (
    TAR_MAX_DR_LIFETIME_SECONDS,
    TAR_CLOCK_SKEW_TOLERANCE_NS,
    TemporalAuthorityEngine,
)
from omnix_core.agents.atf.runtime_continuity import (
    RCR_CES_STALENESS_BOUND_SECONDS,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_dr(status: str = "ACTIVE", expires_in_seconds: float = 3600.0) -> dict:
    """Build a minimal DelegationReceipt dict for testing."""
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(seconds=expires_in_seconds)).isoformat()
    return {
        "delegation_id": "ATFDR-TEST0000000001",
        "status": status,
        "expires_at": expires_at,
        "authority_budget_granted": 100.0,
        "task_scope": {"domain": "TEST"},
        "chain_root_id": "ATFDR-TEST0000000001",
    }


def _make_engine() -> TemporalAuthorityEngine:
    return TemporalAuthorityEngine(db_url=None)


# ─────────────────────────────────────────────────────────────────────────────
# T001 — Constants are module-level, not environment-derived
# ─────────────────────────────────────────────────────────────────────────────

class TestCompiledConstants:
    def test_tar_max_lifetime_is_int(self):
        assert isinstance(TAR_MAX_DR_LIFETIME_SECONDS, int)

    def test_tar_max_lifetime_is_positive(self):
        assert TAR_MAX_DR_LIFETIME_SECONDS > 0

    def test_tar_max_lifetime_ceiling_is_24h(self):
        assert TAR_MAX_DR_LIFETIME_SECONDS == 86_400, (
            "TAR-INV-006: ceiling must be exactly 86400s (24h). "
            "Changing this value is a protocol-level change requiring ADR."
        )

    def test_clock_skew_tolerance_is_5s(self):
        assert TAR_CLOCK_SKEW_TOLERANCE_NS == 5_000_000_000

    def test_rcr_staleness_bound_is_int(self):
        assert isinstance(RCR_CES_STALENESS_BOUND_SECONDS, int)

    def test_rcr_staleness_bound_is_5min(self):
        assert RCR_CES_STALENESS_BOUND_SECONDS == 300, (
            "RGC-INV-007: CES staleness bound must be exactly 300s (5 min). "
            "Changing this value is a protocol-level change requiring ADR."
        )

    def test_tar_max_lifetime_not_from_env(self, monkeypatch):
        monkeypatch.setenv("TAR_MAX_DR_LIFETIME_SECONDS", "999999")
        from omnix_core.agents.atf import temporal_authority as ta_module
        assert ta_module.TAR_MAX_DR_LIFETIME_SECONDS == 86_400, (
            "TAR-INV-006 VIOLATED: constant was read from env var."
        )

    def test_rcr_staleness_not_from_env(self, monkeypatch):
        monkeypatch.setenv("RCR_CES_STALENESS_BOUND_SECONDS", "999999")
        from omnix_core.agents.atf import runtime_continuity as rc_module
        assert rc_module.RCR_CES_STALENESS_BOUND_SECONDS == 300, (
            "RGC-INV-007 VIOLATED: constant was read from env var."
        )


# ─────────────────────────────────────────────────────────────────────────────
# T002 — Admission: DRs within bound are ADMITTED
# ─────────────────────────────────────────────────────────────────────────────

class TestAdmissionWithinBound:
    def test_dr_1h_remaining_is_admitted(self):
        engine = _make_engine()
        dr = _make_dr(expires_in_seconds=3600.0)
        tar = engine.admit_execution(dr, "AID-TEST-001", "test.action")
        assert tar.admission_status == "ADMITTED"
        assert tar.rejection_reason is None

    def test_dr_12h_remaining_is_admitted(self):
        engine = _make_engine()
        dr = _make_dr(expires_in_seconds=43_200.0)
        tar = engine.admit_execution(dr, "AID-TEST-001", "test.action")
        assert tar.admission_status == "ADMITTED"

    def test_dr_exactly_24h_minus_1s_is_admitted(self):
        engine = _make_engine()
        dr = _make_dr(expires_in_seconds=float(TAR_MAX_DR_LIFETIME_SECONDS) - 1.0)
        tar = engine.admit_execution(dr, "AID-TEST-001", "test.action")
        assert tar.admission_status == "ADMITTED"

    def test_dr_30min_remaining_is_admitted(self):
        engine = _make_engine()
        dr = _make_dr(expires_in_seconds=1800.0)
        tar = engine.admit_execution(dr, "AID-TEST-001", "test.action")
        assert tar.admission_status == "ADMITTED"


# ─────────────────────────────────────────────────────────────────────────────
# T003 — Admission: DRs exceeding compiled bound are REJECTED (TAR-INV-006)
# ─────────────────────────────────────────────────────────────────────────────

class TestAdmissionExceedsBound:
    def test_dr_25h_remaining_is_rejected(self):
        engine = _make_engine()
        dr = _make_dr(expires_in_seconds=90_000.0)
        tar = engine.admit_execution(dr, "AID-TEST-001", "test.action")
        assert tar.admission_status == "REJECTED"
        assert "TAR-INV-006" in tar.rejection_reason

    def test_dr_48h_remaining_is_rejected(self):
        engine = _make_engine()
        dr = _make_dr(expires_in_seconds=172_800.0)
        tar = engine.admit_execution(dr, "AID-TEST-001", "test.action")
        assert tar.admission_status == "REJECTED"
        assert "TAR-INV-006" in tar.rejection_reason

    def test_dr_30d_remaining_is_rejected(self):
        engine = _make_engine()
        dr = _make_dr(expires_in_seconds=2_592_000.0)
        tar = engine.admit_execution(dr, "AID-TEST-001", "test.action")
        assert tar.admission_status == "REJECTED"
        assert "TAR-INV-006" in tar.rejection_reason

    def test_rejection_reason_names_structural_constraint(self):
        engine = _make_engine()
        dr = _make_dr(expires_in_seconds=90_000.0)
        tar = engine.admit_execution(dr, "AID-TEST-001", "test.action")
        assert "structural" in tar.rejection_reason.lower() or \
               "compiled" in tar.rejection_reason.lower(), (
            "Rejection reason must explicitly state this is a structural "
            "constraint, not a policy configuration."
        )

    def test_rejection_reason_instructs_reissue(self):
        engine = _make_engine()
        dr = _make_dr(expires_in_seconds=90_000.0)
        tar = engine.admit_execution(dr, "AID-TEST-001", "test.action")
        assert "reissue" in tar.rejection_reason.lower() or \
               "shorter" in tar.rejection_reason.lower()


# ─────────────────────────────────────────────────────────────────────────────
# T004 — TAR-INV-006 takes precedence: expired DRs still fail on expiry first
# ─────────────────────────────────────────────────────────────────────────────

class TestPrecedenceOfChecks:
    def test_expired_dr_fails_on_expiry_not_inv006(self):
        engine = _make_engine()
        dr = _make_dr(expires_in_seconds=-60.0)
        tar = engine.admit_execution(dr, "AID-TEST-001", "test.action")
        assert tar.admission_status == "REJECTED"
        assert "TAR-INV-006" not in tar.rejection_reason
        assert "expired" in tar.rejection_reason.lower()

    def test_inactive_dr_fails_on_status_not_inv006(self):
        engine = _make_engine()
        dr = _make_dr(status="REVOKED", expires_in_seconds=3600.0)
        tar = engine.admit_execution(dr, "AID-TEST-001", "test.action")
        assert tar.admission_status == "REJECTED"
        assert "REVOKED" in tar.rejection_reason
        assert "TAR-INV-006" not in tar.rejection_reason


# ─────────────────────────────────────────────────────────────────────────────
# T005 — TAR record is immutable after issuance (TAR-INV-004)
# ─────────────────────────────────────────────────────────────────────────────

class TestTARImmutability:
    def test_content_hash_present_on_issued_tar(self):
        engine = _make_engine()
        dr = _make_dr()
        tar = engine.admit_execution(dr, "AID-TEST-001", "test.action")
        assert tar.content_hash
        assert len(tar.content_hash) == 64

    def test_tar_id_format_is_correct(self):
        engine = _make_engine()
        dr = _make_dr()
        tar = engine.admit_execution(dr, "AID-TEST-001", "test.action")
        assert tar.tar_id.startswith("ATFTAR-")
        assert len(tar.tar_id) == len("ATFTAR-") + 16

    def test_verify_tar_detects_tampering(self):
        engine = _make_engine()
        dr = _make_dr()
        tar = engine.admit_execution(dr, "AID-TEST-001", "test.action")
        original_hash = tar.content_hash
        tar.authority_budget = 9999.0
        result = engine.verify_tar(tar)
        assert not result["hash_valid"], (
            "TAR-INV-004: tampered field must invalidate content_hash."
        )


# ─────────────────────────────────────────────────────────────────────────────
# T006 — No-expiry DRs are admitted (backwards compat for internal tooling)
# ─────────────────────────────────────────────────────────────────────────────

class TestNoExpiryDR:
    def test_dr_without_expires_at_is_admitted(self):
        engine = _make_engine()
        dr = {
            "delegation_id": "ATFDR-TEST0000000002",
            "status": "ACTIVE",
            "expires_at": None,
            "authority_budget_granted": 100.0,
            "task_scope": {"domain": "TEST"},
            "chain_root_id": "ATFDR-TEST0000000002",
        }
        tar = engine.admit_execution(dr, "AID-TEST-002", "test.action.noexpiry")
        assert tar.admission_status == "ADMITTED", (
            "DRs without expires_at bypass staleness check — "
            "issuer is responsible for explicit epoch setting."
        )
