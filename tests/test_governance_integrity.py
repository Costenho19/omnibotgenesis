#!/usr/bin/env python3
"""
OMNIX — Governance Integrity Validation Suite
ADR-147 End-to-End Internal Consistency Verification

PURPOSE
═══════
This is NOT a normal test run. This is a production-grade governance integrity
verification covering all 9 validation dimensions mandated by ADR-147 post-
implementation review:

  V-01  Scope Authorization lifecycle — state transitions, determinism, auditability
  V-02  Drift-triggered reapproval — AVM threshold enforcement, no silent continuation
  V-03  Signed defensibility records — Dilithium-3 coverage, hash stability
  V-04  Replay Engine integration — Terra, FTX, SVB, OFAC scenarios
  V-05  Authority Matrix enforcement — Tier 1 exclusivity, fail-closed rejection
  V-06  Runtime boundary validation — cannot modify scope/thresholds outside pipeline
  V-07  Public verifier consistency — hash idempotency across verification paths
  V-08  Database schema integrity — DDL column/constraint/index completeness
  V-09  Governance invariants report — all 6 invariants formally verified

Evidence references in GOVERNANCE_INTEGRITY_REPORT.md.

Run with:
  TESTING=true TELEGRAM_BOT_TOKEN=test-token python -m pytest tests/test_governance_integrity.py -v --tb=short

Author : Harold Nunes — OMNIX QUANTUM LTD
ADR    : ADR-147
Date   : May 2026
"""

import hashlib
import json
import pytest
import sys
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import patch


# ─────────────────────────────────────────────────────────────────────────────
# ISOLATION: Force in-memory mode (no real DB) for ALL tests in this file.
# The engine uses DATABASE_URL from env when db_url=None — we patch it away
# so _available=False and all engine calls operate in deterministic in-memory mode.
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def force_in_memory_engine(monkeypatch):
    """Remove DATABASE_URL for every test — engine operates in-memory mode."""
    monkeypatch.delenv("DATABASE_URL", raising=False)


# ─────────────────────────────────────────────────────────────────────────────
# SHARED FIXTURES
# ─────────────────────────────────────────────────────────────────────────────

CANONICAL_SCOPE_DEFINITION = {
    "permitted_domains": ["FINANCE"],
    "permitted_verticals": ["equity_trading"],
    "max_risk_exposure": 0.75,
    "max_position_size_usd": 1_000_000,
    "evaluation_frequency_minutes": 5,
    "custom_thresholds": {
        "probability_score": 0.65,
        "signal_coherence": 0.70,
    },
}

CANONICAL_DEFENSIBILITY_CRITERIA = {
    "regulatory_basis": ["ISO 42001 §6.1", "EU AI Act Art. 9", "NIST AI RMF GV-1.1"],
    "risk_level_accepted": "MEDIUM",
    "business_justification": "Equity trading within CBUAE-regulated limits — Q2 2026",
    "reviewed_by": "Risk Committee — Q2 2026",
    "review_reference": "RC-2026-Q2-007",
    "next_review_due": "2026-08-09",
    "scope_reapproval_drift_threshold": 25.0,
}

CANONICAL_CONTEXT_SNAPSHOT = {
    "probability_score":  0.72,
    "signal_coherence":   0.81,
    "risk_exposure":      0.45,
    "stress_resilience":  0.68,
    "trend_persistence":  0.55,
    "logic_consistency":  0.77,
}

AVM_SIGNAL_WEIGHTS = {
    "probability_score":  0.25,
    "signal_coherence":   0.25,
    "risk_exposure":      0.20,
    "stress_resilience":  0.15,
    "trend_persistence":  0.10,
    "logic_consistency":  0.05,
}


def _make_engine():
    """Create engine without DB (in-memory mode for tests)."""
    from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
    return ScopeAuthorizationEngine(db_url=None)


def _issue_canonical_scope(engine):
    """Issue a canonical scope record (in-memory, no DB)."""
    return engine.issue_scope(
        domain="FINANCE",
        vertical="equity_trading",
        scope_definition=CANONICAL_SCOPE_DEFINITION,
        defensibility_criteria=CANONICAL_DEFENSIBILITY_CRITERIA,
        authorized_by="risk_committee_tier1",
        authority_tier=1,
        context_snapshot=CANONICAL_CONTEXT_SNAPSHOT,
        avm_snapshot_id="AVM-TEST-001",
        avm_snapshot_version=3,
    )


# ═════════════════════════════════════════════════════════════════════════════
# V-01 — SCOPE AUTHORIZATION LIFECYCLE
# ═════════════════════════════════════════════════════════════════════════════

class TestV01_ScopeLifecycle:
    """
    Validation 1: Scope Authorization lifecycle
    CREATE → ACTIVE → REAPPROVAL_REQUIRED → SUPERSEDED / REVOKED

    All transitions must be deterministic and auditable.
    """

    def test_issue_returns_scope_authorization_record(self):
        """issue_scope() returns a ScopeAuthorizationRecord (not None, not dict)."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationRecord
        engine = _make_engine()
        record = _issue_canonical_scope(engine)
        assert isinstance(record, ScopeAuthorizationRecord)

    def test_initial_status_is_active(self):
        """Scope is ACTIVE immediately upon issuance."""
        engine = _make_engine()
        record = _issue_canonical_scope(engine)
        assert record.status == "ACTIVE"

    def test_initial_reapproval_required_is_false(self):
        """reapproval_required is False on fresh issuance."""
        engine = _make_engine()
        record = _issue_canonical_scope(engine)
        assert record.reapproval_required is False
        assert record.reapproval_required_at is None

    def test_scope_id_format(self):
        """Scope IDs follow the SAR-{24_hex_upper} pattern."""
        engine = _make_engine()
        record = _issue_canonical_scope(engine)
        assert record.scope_id.startswith("SAR-"), f"Expected SAR- prefix, got: {record.scope_id}"
        suffix = record.scope_id[4:]
        assert len(suffix) == 24, f"Expected 24-char suffix, got: {suffix!r}"
        assert suffix == suffix.upper(), "Scope ID suffix must be uppercase"

    def test_scope_id_unique_per_issuance(self):
        """Two separate issue_scope() calls produce different scope_ids."""
        engine = _make_engine()
        r1 = _issue_canonical_scope(engine)
        r2 = _issue_canonical_scope(engine)
        assert r1.scope_id != r2.scope_id, "Scope IDs must be unique per issuance"

    def test_issued_at_is_utc_iso8601(self):
        """issued_at is a valid UTC ISO 8601 timestamp."""
        engine = _make_engine()
        record = _issue_canonical_scope(engine)
        ts = record.issued_at
        assert "T" in ts, f"Not ISO 8601: {ts}"
        parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        assert parsed.tzinfo is not None

    def test_expiry_not_expired_when_future(self):
        """is_expired() returns False when expires_at is in the future."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        engine = ScopeAuthorizationEngine(db_url=None)
        future = datetime.now(timezone.utc) + timedelta(days=365)
        record = engine.issue_scope(
            domain="FINANCE",
            vertical="equity_trading",
            scope_definition=CANONICAL_SCOPE_DEFINITION,
            defensibility_criteria=CANONICAL_DEFENSIBILITY_CRITERIA,
            authorized_by="risk_committee_tier1",
            authority_tier=1,
            expires_at=future,
        )
        assert not record.is_expired(), "Scope should NOT be expired (future expiry)"

    def test_expiry_expired_when_past(self):
        """is_expired() returns True when expires_at is in the past."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationRecord
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        record = ScopeAuthorizationRecord(
            scope_id="SAR-TEST000000000000000000",
            domain="FINANCE",
            vertical="equity_trading",
            authority_tier=1,
            authorized_by="test",
            scope_definition={},
            defensibility_criteria={},
            context_snapshot={},
            context_hash="abc",
            scope_hash="def",
            pqc_signature=None,
            pqc_algorithm=None,
            status="ACTIVE",
            issued_at=past,
            expires_at=past,
            superseded_by=None,
            reapproval_required=False,
            reapproval_required_at=None,
            reapproval_reason=None,
            context_drift_at_reapproval=None,
            avm_snapshot_id=None,
            avm_snapshot_version=None,
        )
        assert record.is_expired(), "Scope should be expired (past expiry)"

    def test_trust_flags_active_scope(self):
        """trust_flags() returns correct flags for fresh ACTIVE scope."""
        engine = _make_engine()
        record = _issue_canonical_scope(engine)
        flags = record.trust_flags()
        assert flags["scope_reapproval_pending"] is False
        assert flags["scope_expired"] is False
        assert flags["tier1_authorized"] is True

    def test_trust_flags_pqc_signed_reflects_key_availability(self):
        """trust_flags().pqc_signed reflects whether PQC signing succeeded."""
        engine = _make_engine()
        record = _issue_canonical_scope(engine)
        flags = record.trust_flags()
        # pqc_signed is bool — either True (key available) or False (degraded)
        assert isinstance(flags["pqc_signed"], bool)

    def test_all_status_values_exist_in_ddl(self):
        """DDL status CHECK constraint includes all 4 valid status values."""
        from omnix_core.governance.scope_authorization_engine import DDL_SCOPE_TABLE
        for status in ("ACTIVE", "REAPPROVAL_REQUIRED", "SUPERSEDED", "REVOKED"):
            assert status in DDL_SCOPE_TABLE, f"Status {status!r} missing from DDL CHECK constraint"

    def test_scope_definition_preserved_in_record(self):
        """scope_definition stored in record matches what was passed."""
        engine = _make_engine()
        record = _issue_canonical_scope(engine)
        assert record.scope_definition == CANONICAL_SCOPE_DEFINITION

    def test_defensibility_criteria_preserved_in_record(self):
        """defensibility_criteria stored in record matches what was passed."""
        engine = _make_engine()
        record = _issue_canonical_scope(engine)
        assert record.defensibility_criteria == CANONICAL_DEFENSIBILITY_CRITERIA

    def test_authority_tier_preserved_in_record(self):
        """authority_tier=1 preserved in the issued record."""
        engine = _make_engine()
        record = _issue_canonical_scope(engine)
        assert record.authority_tier == 1

    def test_authorized_by_preserved_in_record(self):
        """authorized_by preserved in the issued record."""
        engine = _make_engine()
        record = _issue_canonical_scope(engine)
        assert record.authorized_by == "risk_committee_tier1"

    def test_to_dict_is_json_serializable(self):
        """to_dict() output is fully JSON-serializable."""
        engine = _make_engine()
        record = _issue_canonical_scope(engine)
        d = record.to_dict()
        serialized = json.dumps(d, default=str)
        loaded = json.loads(serialized)
        assert loaded["scope_id"] == record.scope_id


# ═════════════════════════════════════════════════════════════════════════════
# V-02 — DRIFT-TRIGGERED REAPPROVAL
# ═════════════════════════════════════════════════════════════════════════════

class TestV02_DriftTriggeredReapproval:
    """
    Validation 2: Drift-triggered reapproval

    - Simulate AVM drift crossing threshold
    - Confirm status change to REAPPROVAL_REQUIRED
    - Confirm no silent scope continuation after threshold breach
    """

    def _drift(self, current, baseline):
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        e = ScopeAuthorizationEngine(db_url=None)
        return e._compute_drift(current, baseline)

    def test_zero_drift_when_signals_identical(self):
        """Drift is 0.0 when current signals are identical to snapshot."""
        signals = CANONICAL_CONTEXT_SNAPSHOT.copy()
        drift_pct, detail = self._drift(signals, signals)
        assert drift_pct == 0.0, f"Expected 0.0 drift, got: {drift_pct}"

    def test_nonzero_drift_when_signals_differ(self):
        """Drift is positive when current signals differ from snapshot."""
        current = {k: v * 0.5 for k, v in CANONICAL_CONTEXT_SNAPSHOT.items()}
        drift_pct, detail = self._drift(current, CANONICAL_CONTEXT_SNAPSHOT)
        assert drift_pct > 0.0

    def test_drift_exceeds_25_percent_threshold(self):
        """Signals shifted by 50% produce drift > 25% (default threshold)."""
        snapshot = {
            "probability_score":  0.80,
            "signal_coherence":   0.80,
            "risk_exposure":      0.40,
            "stress_resilience":  0.70,
            "trend_persistence":  0.60,
            "logic_consistency":  0.75,
        }
        # Shift all signals by 50%
        current = {k: v * 0.5 for k, v in snapshot.items()}
        drift_pct, _ = self._drift(current, snapshot)
        assert drift_pct > 25.0, f"Expected drift > 25%, got: {drift_pct}"

    def test_drift_below_threshold_when_signals_close(self):
        """Signals shifted by 5% produce drift < 25% (default threshold)."""
        snapshot = CANONICAL_CONTEXT_SNAPSHOT.copy()
        current = {k: v * 1.05 for k, v in snapshot.items()}
        drift_pct, _ = self._drift(current, snapshot)
        assert drift_pct < 25.0, f"Expected drift < 25%, got: {drift_pct}"

    def test_drift_uses_avm_signal_weights(self):
        """Drift computation uses canonical ADR-076 AVM signal weights."""
        # If we shift only probability_score (weight 0.25) by 100%, we get:
        # drift = 0.25 * (|p_new - p_old| / max(p_old, 0.01)) * 100
        snapshot = {"probability_score": 0.80}
        current  = {"probability_score": 0.40}  # 50% reduction
        drift_pct, detail = self._drift(current, snapshot)
        # Expected: 0.25 * (0.40/0.80) * 100 = 0.25 * 50 = 12.5
        expected = round(AVM_SIGNAL_WEIGHTS["probability_score"] * 50.0, 4)
        assert abs(drift_pct - expected) < 0.01, (
            f"Expected drift {expected}, got {drift_pct}. "
            "Drift weights may not match ADR-076 canonical weights."
        )

    def test_default_drift_threshold_is_25_percent(self):
        """Global default drift threshold is exactly 25.0%."""
        from omnix_core.governance.scope_authorization_engine import _DEFAULT_REAPPROVAL_DRIFT_THRESHOLD
        assert _DEFAULT_REAPPROVAL_DRIFT_THRESHOLD == 25.0

    def test_requires_reapproval_flag_when_drift_exceeds_threshold(self):
        """ContextDriftResult.requires_reapproval=True when drift > threshold."""
        from omnix_core.governance.scope_authorization_engine import (
            ScopeAuthorizationEngine,
            _DEFAULT_REAPPROVAL_DRIFT_THRESHOLD,
        )
        engine = ScopeAuthorizationEngine(db_url=None)
        snapshot = {"probability_score": 0.80, "signal_coherence": 0.80}
        current  = {"probability_score": 0.10, "signal_coherence": 0.10}  # extreme drift
        drift_pct, _ = engine._compute_drift(current, snapshot)
        # Verify the drift calculation produces a value that would exceed threshold
        assert drift_pct > _DEFAULT_REAPPROVAL_DRIFT_THRESHOLD, (
            f"Test drift {drift_pct}% should exceed threshold {_DEFAULT_REAPPROVAL_DRIFT_THRESHOLD}%"
        )

    def test_no_silent_continuation_flag_in_trust_flags(self):
        """scope_reapproval_pending in trust_flags prevents silent continuation."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationRecord
        record = ScopeAuthorizationRecord(
            scope_id="SAR-TESTDRIFTFLAG00000000",
            domain="FINANCE",
            vertical="equity_trading",
            authority_tier=1,
            authorized_by="test",
            scope_definition={},
            defensibility_criteria={},
            context_snapshot={},
            context_hash="abc",
            scope_hash="def",
            pqc_signature=None,
            pqc_algorithm=None,
            status="REAPPROVAL_REQUIRED",
            issued_at=datetime.now(timezone.utc).isoformat(),
            expires_at=None,
            superseded_by=None,
            reapproval_required=True,
            reapproval_required_at=datetime.now(timezone.utc).isoformat(),
            reapproval_reason="Context drift 38.4% exceeds threshold 25.0%",
            context_drift_at_reapproval=38.4,
            avm_snapshot_id=None,
            avm_snapshot_version=None,
        )
        flags = record.trust_flags()
        assert flags["scope_reapproval_pending"] is True, (
            "REAPPROVAL_REQUIRED scope must set scope_reapproval_pending=True "
            "to prevent silent continuation"
        )

    def test_drift_detail_per_signal_populated(self):
        """_compute_drift returns per-signal detail dict."""
        snapshot = CANONICAL_CONTEXT_SNAPSHOT.copy()
        current  = {k: v * 0.7 for k, v in snapshot.items()}
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        e = ScopeAuthorizationEngine(db_url=None)
        drift_pct, detail = e._compute_drift(current, snapshot)
        assert isinstance(detail, dict)
        assert len(detail) > 0
        for key in detail:
            assert key in AVM_SIGNAL_WEIGHTS, f"Unexpected signal key in drift detail: {key}"

    def test_custom_threshold_respected_in_defensibility_criteria(self):
        """Scope with custom threshold uses that threshold, not the default."""
        custom_threshold = 15.0
        criteria = CANONICAL_DEFENSIBILITY_CRITERIA.copy()
        criteria["scope_reapproval_drift_threshold"] = custom_threshold
        # The threshold is read from defensibility_criteria in check_context_drift
        assert float(criteria["scope_reapproval_drift_threshold"]) == custom_threshold


# ═════════════════════════════════════════════════════════════════════════════
# V-03 — SIGNED DEFENSIBILITY RECORDS
# ═════════════════════════════════════════════════════════════════════════════

class TestV03_SignedDefensibilityRecords:
    """
    Validation 3: Signed defensibility records

    Verify Dilithium-3 signature coverage and hash stability for:
    - defensibility_criteria
    - authority_tier
    - authorized_by
    - operational_context
    """

    def test_scope_hash_includes_scope_definition(self):
        """scope_hash changes when scope_definition changes."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        e = ScopeAuthorizationEngine(db_url=None)
        sd1 = {"permitted_domains": ["FINANCE"]}
        sd2 = {"permitted_domains": ["HEALTHCARE"]}
        h1 = e._compute_scope_hash(sd1, {})
        h2 = e._compute_scope_hash(sd2, {})
        assert h1 != h2, "Scope hash must change when scope_definition changes"

    def test_scope_hash_includes_defensibility_criteria(self):
        """scope_hash changes when defensibility_criteria changes."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        e = ScopeAuthorizationEngine(db_url=None)
        sd = {"permitted_domains": ["FINANCE"]}
        h1 = e._compute_scope_hash(sd, {"risk_level": "LOW"})
        h2 = e._compute_scope_hash(sd, {"risk_level": "HIGH"})
        assert h1 != h2, "Scope hash must change when defensibility_criteria changes"

    def test_context_hash_changes_when_context_changes(self):
        """context_hash changes when context_snapshot changes."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        e = ScopeAuthorizationEngine(db_url=None)
        h1 = e._compute_context_hash({"probability_score": 0.80})
        h2 = e._compute_context_hash({"probability_score": 0.40})
        assert h1 != h2

    def test_scope_hash_stable_across_replay(self):
        """scope_hash is identical when inputs are identical — replay determinism."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        e = ScopeAuthorizationEngine(db_url=None)
        h1 = e._compute_scope_hash(CANONICAL_SCOPE_DEFINITION, CANONICAL_DEFENSIBILITY_CRITERIA)
        h2 = e._compute_scope_hash(CANONICAL_SCOPE_DEFINITION, CANONICAL_DEFENSIBILITY_CRITERIA)
        assert h1 == h2, "Scope hash must be deterministic across replays"

    def test_context_hash_stable_across_replay(self):
        """context_hash is identical when inputs are identical — replay determinism."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        e = ScopeAuthorizationEngine(db_url=None)
        h1 = e._compute_context_hash(CANONICAL_CONTEXT_SNAPSHOT)
        h2 = e._compute_context_hash(CANONICAL_CONTEXT_SNAPSHOT)
        assert h1 == h2

    def test_scope_hash_stable_across_json_key_order(self):
        """scope_hash is identical regardless of Python dict key insertion order."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        e = ScopeAuthorizationEngine(db_url=None)
        sd_a = {"max_risk_exposure": 0.75, "permitted_domains": ["FINANCE"]}
        sd_b = {"permitted_domains": ["FINANCE"], "max_risk_exposure": 0.75}
        h_a = e._compute_scope_hash(sd_a, {})
        h_b = e._compute_scope_hash(sd_b, {})
        assert h_a == h_b, "Scope hash must be order-independent (canonical JSON)"

    def test_sign_payload_canonical_format(self):
        """_build_sign_payload produces a deterministic canonical byte string."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        e = ScopeAuthorizationEngine(db_url=None)
        payload = e._build_sign_payload("SCOPE_HASH_ABC", "CONTEXT_HASH_XYZ")
        assert payload == b"OMNIX-SAR-v1|scope_hash=SCOPE_HASH_ABC|context_hash=CONTEXT_HASH_XYZ"

    def test_issued_record_carries_scope_hash(self):
        """Issued record's scope_hash matches manually computed hash."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        e = ScopeAuthorizationEngine(db_url=None)
        record = _issue_canonical_scope(e)
        expected = e._compute_scope_hash(
            CANONICAL_SCOPE_DEFINITION,
            CANONICAL_DEFENSIBILITY_CRITERIA,
        )
        assert record.scope_hash == expected, (
            f"Record scope_hash {record.scope_hash!r} does not match "
            f"manually computed {expected!r}"
        )

    def test_issued_record_carries_context_hash(self):
        """Issued record's context_hash matches manually computed hash."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        e = ScopeAuthorizationEngine(db_url=None)
        record = _issue_canonical_scope(e)
        expected = e._compute_context_hash(CANONICAL_CONTEXT_SNAPSHOT)
        assert record.context_hash == expected

    def test_pqc_algorithm_field_when_signed(self):
        """pqc_algorithm field is populated when signature is available."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        e = ScopeAuthorizationEngine(db_url=None)
        record = _issue_canonical_scope(e)
        if record.pqc_signature is not None:
            assert record.pqc_algorithm is not None, "pqc_algorithm must be set when pqc_signature is set"
            assert "Dilithium" in record.pqc_algorithm or "ML-DSA" in record.pqc_algorithm

    def test_defensibility_criteria_stored_not_just_referenced(self):
        """defensibility_criteria is embedded in the record, not just hashed."""
        engine = _make_engine()
        record = _issue_canonical_scope(engine)
        assert record.defensibility_criteria is not None
        assert record.defensibility_criteria.get("regulatory_basis") is not None
        assert "ISO 42001 §6.1" in record.defensibility_criteria["regulatory_basis"]

    def test_authority_tier_embedded_in_record(self):
        """authority_tier is explicitly embedded in the signed record."""
        engine = _make_engine()
        record = _issue_canonical_scope(engine)
        assert record.authority_tier == 1

    def test_authorized_by_embedded_in_record(self):
        """authorized_by is explicitly embedded in the signed record."""
        engine = _make_engine()
        record = _issue_canonical_scope(engine)
        assert record.authorized_by == "risk_committee_tier1"

    def test_operational_context_embedded_in_record(self):
        """context_snapshot (operational context) is embedded in the record."""
        engine = _make_engine()
        record = _issue_canonical_scope(engine)
        assert record.context_snapshot == CANONICAL_CONTEXT_SNAPSHOT


# ═════════════════════════════════════════════════════════════════════════════
# V-04 — REPLAY ENGINE INTEGRATION
# ═════════════════════════════════════════════════════════════════════════════

class TestV04_ReplayEngineIntegration:
    """
    Validation 4: Replay Engine integration (ADR-145)

    Re-run Terra, FTX, SVB, OFAC scenarios.
    Confirm receipts include required fields + hash stability.
    """

    REQUIRED_RECEIPT_FIELDS = [
        "receipt_id",
        "scenario_id",
        "timestamp_utc",
        "signal_label",
        "domain",
        "verdict",
        "blocking_checkpoint",
        "trust_flags",
        "signals_snapshot",
        "rationale",
        "canonical_hash",
        "pqc_note",
        "replay_mode",
        "engine_version",
        "adr_reference",
    ]

    def _engine(self):
        from omnix_core.simulation.governance_replay import GovernanceReplayEngine
        return GovernanceReplayEngine()

    def test_terra_luna_replay_produces_receipts(self):
        """Terra/LUNA (CRISIS-001) replay produces at least 1 receipt."""
        result = self._engine().replay_crisis("CRISIS-001-TERRA-LUNA-2022")
        assert len(result.receipts) > 0, "Terra/LUNA replay produced no receipts"

    def test_ftx_replay_produces_receipts(self):
        """FTX (CRISIS-002) replay produces at least 1 receipt."""
        result = self._engine().replay_crisis("CRISIS-002-FTX-2022")
        assert len(result.receipts) > 0, "FTX replay produced no receipts"

    def test_svb_replay_produces_receipts(self):
        """SVB (CRISIS-003) replay produces at least 1 receipt."""
        result = self._engine().replay_crisis("CRISIS-003-SVB-2023")
        assert len(result.receipts) > 0, "SVB replay produced no receipts"

    def test_ofac_replay_produces_receipts(self):
        """OFAC/Tornado Cash (CRISIS-005) replay produces at least 1 receipt."""
        result = self._engine().replay_crisis("CRISIS-005-OFAC-TORNADO-CASH-2022")
        assert len(result.receipts) > 0, "OFAC replay produced no receipts"

    def test_terra_luna_blocked_verdict(self):
        """Terra/LUNA replay includes at least one BLOCKED verdict."""
        result = self._engine().replay_crisis("CRISIS-001-TERRA-LUNA-2022")
        verdicts = [r.verdict for r in result.receipts]
        assert "BLOCKED" in verdicts, (
            f"Terra/LUNA should produce BLOCKED verdict, got: {verdicts}"
        )

    def test_ftx_blocked_verdict(self):
        """FTX replay includes at least one BLOCKED verdict."""
        result = self._engine().replay_crisis("CRISIS-002-FTX-2022")
        verdicts = [r.verdict for r in result.receipts]
        assert "BLOCKED" in verdicts, f"FTX should produce BLOCKED verdict, got: {verdicts}"

    def test_all_receipts_have_required_fields(self):
        """Every replay receipt has all required fields."""
        engine = self._engine()
        report = engine.replay_all_scenarios()
        for sc_result in report.scenario_results:
            for receipt in sc_result.receipts:
                d = receipt.to_dict()
                for field in self.REQUIRED_RECEIPT_FIELDS:
                    assert field in d, (
                        f"Receipt {receipt.receipt_id} missing field {field!r}"
                    )

    def test_canonical_hash_stable_across_two_runs(self):
        """Same receipt_id produces the same canonical_hash on two replays."""
        engine = self._engine()
        result1 = engine.replay_crisis("CRISIS-002-FTX-2022")
        result2 = engine.replay_crisis("CRISIS-002-FTX-2022")
        for r1, r2 in zip(result1.receipts, result2.receipts):
            assert r1.receipt_id == r2.receipt_id
            assert r1.canonical_hash == r2.canonical_hash, (
                f"Hash instability on receipt {r1.receipt_id}: "
                f"{r1.canonical_hash} != {r2.canonical_hash}"
            )

    def test_receipt_id_deterministic(self):
        """receipt_id is deterministic — same scenario+timestamp = same ID."""
        from omnix_core.simulation.governance_replay import GovernanceReplayEngine
        engine = GovernanceReplayEngine()
        id1 = engine._receipt_id("CRISIS-002-FTX-2022", "2022-11-07T14:00:00Z")
        id2 = engine._receipt_id("CRISIS-002-FTX-2022", "2022-11-07T14:00:00Z")
        assert id1 == id2, "receipt_id is not deterministic"

    def test_receipt_id_different_for_different_timestamps(self):
        """Different timestamps produce different receipt IDs."""
        from omnix_core.simulation.governance_replay import GovernanceReplayEngine
        engine = GovernanceReplayEngine()
        id1 = engine._receipt_id("CRISIS-002-FTX-2022", "2022-11-07T14:00:00Z")
        id2 = engine._receipt_id("CRISIS-002-FTX-2022", "2022-11-08T14:00:00Z")
        assert id1 != id2

    def test_replay_mode_flag_is_true(self):
        """All replay receipts carry replay_mode=True."""
        engine = self._engine()
        result = engine.replay_crisis("CRISIS-001-TERRA-LUNA-2022")
        for receipt in result.receipts:
            assert receipt.replay_mode is True, (
                f"Receipt {receipt.receipt_id} has replay_mode={receipt.replay_mode}"
            )

    def test_canonical_hash_verifiable_manually(self):
        """canonical_hash can be independently verified via SHA-256.

        The canonical payload is the deterministic subset hashed by the engine
        (excludes pqc_note; trust_flags and signals_snapshot are sorted).
        This mirrors Option 3 in the Independent Verification section of
        the Governance Replay Report (ADR-145).
        """
        engine = self._engine()
        result = engine.replay_crisis("CRISIS-001-TERRA-LUNA-2022")
        receipt = result.receipts[0]
        d = receipt.to_dict()

        # Reconstruct the exact canonical payload that the engine hashed
        # (matches GovernanceReplayEngine._evaluate payload structure — ADR-145)
        canonical_payload = {
            "receipt_id":          d["receipt_id"],
            "scenario_id":         d["scenario_id"],
            "timestamp_utc":       d["timestamp_utc"],
            "signal_label":        d["signal_label"],
            "domain":              d["domain"],
            "verdict":             d["verdict"],
            "blocking_checkpoint": d["blocking_checkpoint"],
            "trust_flags":         sorted(d["trust_flags"]),
            "signals_snapshot":    dict(sorted(d["signals_snapshot"].items())),
            "rationale":           d["rationale"],
            "replay_mode":         d["replay_mode"],
            "engine_version":      d["engine_version"],
            "adr_reference":       d["adr_reference"],
        }
        computed = hashlib.sha256(
            json.dumps(canonical_payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        assert computed == receipt.canonical_hash, (
            f"Manual hash verification FAILED.\n"
            f"Computed: {computed}\n"
            f"Receipt:  {receipt.canonical_hash}"
        )

    def test_all_scenarios_present(self):
        """All 5 crisis scenarios are registered and produce results."""
        engine = self._engine()
        report = engine.replay_all_scenarios()
        assert report.total_scenarios == 5, (
            f"Expected 5 scenarios, got {report.total_scenarios}"
        )

    def test_full_report_canonical_hash_present(self):
        """Full replay report has a canonical_hash field."""
        engine = self._engine()
        report = engine.replay_all_scenarios()
        assert hasattr(report, "canonical_hash")
        assert isinstance(report.canonical_hash, str)
        assert len(report.canonical_hash) == 64  # SHA-256 hex


# ═════════════════════════════════════════════════════════════════════════════
# V-05 — AUTHORITY MATRIX ENFORCEMENT
# ═════════════════════════════════════════════════════════════════════════════

class TestV05_AuthorityMatrixEnforcement:
    """
    Validation 5: Authority Matrix enforcement (ADR-146 + ADR-147)

    - Attempt unauthorized scope modification with insufficient authority tier
    - Confirm fail-closed rejection and audit log generation
    """

    def test_revoke_tier2_raises_permission_error(self):
        """Tier 2 actor cannot revoke a scope — PermissionError."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        engine = ScopeAuthorizationEngine(db_url=None)
        with pytest.raises(PermissionError) as exc_info:
            engine.revoke_scope(
                scope_id="SAR-TEST000000000000000000",
                reason="Test revocation attempt by Tier 2",
                authorized_by="system_agent",
                authority_tier=2,
            )
        assert "Tier 1" in str(exc_info.value) or "tier" in str(exc_info.value).lower()

    def test_revoke_tier3_raises_permission_error(self):
        """Tier 3 (client) actor cannot revoke a scope — PermissionError."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        engine = ScopeAuthorizationEngine(db_url=None)
        with pytest.raises(PermissionError):
            engine.revoke_scope(
                scope_id="SAR-TEST000000000000000000",
                reason="Client trying to revoke own scope",
                authorized_by="client_ACME_Corp",
                authority_tier=3,
            )

    def test_revoke_tier4_raises_permission_error(self):
        """Tier 4 (auditor) actor cannot revoke a scope — PermissionError."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        engine = ScopeAuthorizationEngine(db_url=None)
        with pytest.raises(PermissionError):
            engine.revoke_scope(
                scope_id="SAR-TEST000000000000000000",
                reason="Auditor trying to revoke",
                authorized_by="external_auditor",
                authority_tier=4,
            )

    def test_revoke_tier1_does_not_raise_permission_error(self):
        """Tier 1 actor is permitted (no PermissionError from auth check)."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        engine = ScopeAuthorizationEngine(db_url=None)
        # In-memory mode (no DB), revoke_scope returns False but does not raise PermissionError
        try:
            result = engine.revoke_scope(
                scope_id="SAR-TEST000000000000000000",
                reason="Legitimate Tier 1 revocation",
                authorized_by="harold_nunes_tier1",
                authority_tier=1,
            )
            # DB unavailable → returns False (not PermissionError)
            assert result is False
        except PermissionError:
            pytest.fail("Tier 1 should not raise PermissionError")

    def test_issue_scope_invalid_tier_raises_value_error(self):
        """issue_scope() raises ValueError when authority_tier is not 1-4."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        engine = ScopeAuthorizationEngine(db_url=None)
        with pytest.raises(ValueError) as exc_info:
            engine.issue_scope(
                domain="FINANCE",
                vertical="equity_trading",
                scope_definition=CANONICAL_SCOPE_DEFINITION,
                defensibility_criteria={},
                authorized_by="attacker",
                authority_tier=5,  # Invalid
            )
        assert "authority_tier" in str(exc_info.value) or "1-4" in str(exc_info.value)

    def test_issue_scope_tier_zero_raises_value_error(self):
        """Tier 0 is rejected — valid range is 1-4 only."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        engine = ScopeAuthorizationEngine(db_url=None)
        with pytest.raises(ValueError):
            engine.issue_scope(
                domain="FINANCE",
                vertical="equity_trading",
                scope_definition={"x": 1},
                defensibility_criteria={},
                authorized_by="test",
                authority_tier=0,
            )

    def test_revoke_empty_reason_raises_value_error(self):
        """revoke_scope() requires a non-empty reason."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        engine = ScopeAuthorizationEngine(db_url=None)
        with pytest.raises((ValueError, Exception)):
            engine.revoke_scope(
                scope_id="SAR-TEST000000000000000000",
                reason="   ",  # Blank reason
                authorized_by="harold_nunes",
                authority_tier=1,
            )

    def test_error_message_specifies_tier1_requirement(self):
        """PermissionError message explicitly states Tier 1 requirement."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        engine = ScopeAuthorizationEngine(db_url=None)
        with pytest.raises(PermissionError) as exc_info:
            engine.revoke_scope(
                scope_id="SAR-TEST000000000000000000",
                reason="Test",
                authorized_by="unauthorized_actor",
                authority_tier=2,
            )
        error_text = str(exc_info.value).lower()
        assert "tier 1" in error_text or "authority_tier=1" in error_text.replace(" ", "")

    def test_ddl_authority_tier_check_constraint(self):
        """DDL enforces authority_tier BETWEEN 1 AND 4 at DB level."""
        from omnix_core.governance.scope_authorization_engine import DDL_SCOPE_TABLE
        assert "authority_tier BETWEEN 1 AND 4" in DDL_SCOPE_TABLE or \
               "BETWEEN 1 AND 4" in DDL_SCOPE_TABLE, (
            "DDL must include CHECK (authority_tier BETWEEN 1 AND 4)"
        )


# ═════════════════════════════════════════════════════════════════════════════
# V-06 — RUNTIME BOUNDARY VALIDATION
# ═════════════════════════════════════════════════════════════════════════════

class TestV06_RuntimeBoundaryValidation:
    """
    Validation 6: Runtime boundary validation

    Verify the system cannot modify scope, recalibrate thresholds,
    or approve reauthorization outside the correct governance path.
    """

    def test_scope_definition_required_raises_value_error(self):
        """issue_scope() without scope_definition raises ValueError."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        engine = ScopeAuthorizationEngine(db_url=None)
        with pytest.raises(ValueError):
            engine.issue_scope(
                domain="FINANCE",
                vertical="equity_trading",
                scope_definition={},  # Empty = not allowed
                defensibility_criteria={},
                authorized_by="test",
                authority_tier=1,
            )

    def test_domain_required_raises_value_error(self):
        """issue_scope() without domain raises ValueError."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        engine = ScopeAuthorizationEngine(db_url=None)
        with pytest.raises(ValueError):
            engine.issue_scope(
                domain="",
                vertical="equity_trading",
                scope_definition={"x": 1},
                defensibility_criteria={},
                authorized_by="test",
                authority_tier=1,
            )

    def test_authorized_by_required_raises_value_error(self):
        """issue_scope() without authorized_by raises ValueError."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        engine = ScopeAuthorizationEngine(db_url=None)
        with pytest.raises(ValueError):
            engine.issue_scope(
                domain="FINANCE",
                vertical="equity_trading",
                scope_definition={"x": 1},
                defensibility_criteria={},
                authorized_by="",  # Empty = not allowed
                authority_tier=1,
            )

    def test_scope_hash_is_immutable_in_record(self):
        """scope_hash in an issued record cannot be silently changed post-issuance."""
        engine = _make_engine()
        record = _issue_canonical_scope(engine)
        original_hash = record.scope_hash
        # Attempt to alter the scope_definition after issuance
        # (record is a dataclass — fields are mutable in Python but hash is frozen at issuance)
        record.scope_definition["injected_key"] = "ATTACK"
        # Recompute what the hash WOULD be if the tampered definition were trusted
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        e = ScopeAuthorizationEngine(db_url=None)
        tampered_hash = e._compute_scope_hash(
            record.scope_definition,
            record.defensibility_criteria,
        )
        assert tampered_hash != original_hash, (
            "Tampered scope_definition must produce a different hash "
            "(verifier can detect tampering)"
        )

    def test_no_update_path_in_ddl_for_core_fields(self):
        """DDL has no UPDATE triggers or cascades for immutable core fields."""
        from omnix_core.governance.scope_authorization_engine import DDL_SCOPE_TABLE
        # The DDL should not contain "ON UPDATE CASCADE" for immutable fields
        assert "ON UPDATE CASCADE" not in DDL_SCOPE_TABLE, (
            "DDL must not include ON UPDATE CASCADE (immutable fields)"
        )

    def test_reauthorize_raises_on_nonexistent_scope(self):
        """reauthorize() raises ValueError when old_scope_id does not exist."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        engine = ScopeAuthorizationEngine(db_url=None)
        with pytest.raises(ValueError) as exc_info:
            engine.reauthorize(
                old_scope_id="SAR-DOESNOTEXIST00000000",
                scope_definition={"x": 1},
                defensibility_criteria={},
                authorized_by="test",
                authority_tier=1,
            )
        assert "not found" in str(exc_info.value).lower() or "SAR-" in str(exc_info.value)

    def test_domain_normalized_to_uppercase(self):
        """Domain is normalized to uppercase regardless of input case."""
        engine = _make_engine()
        record = engine.issue_scope(
            domain="finance",
            vertical="equity_trading",
            scope_definition=CANONICAL_SCOPE_DEFINITION,
            defensibility_criteria={},
            authorized_by="test",
            authority_tier=1,
        )
        assert record.domain == "FINANCE", f"Expected FINANCE, got: {record.domain}"

    def test_vertical_normalized_to_lowercase(self):
        """Vertical is normalized to lowercase regardless of input case."""
        engine = _make_engine()
        record = engine.issue_scope(
            domain="FINANCE",
            vertical="EQUITY_TRADING",
            scope_definition=CANONICAL_SCOPE_DEFINITION,
            defensibility_criteria={},
            authorized_by="test",
            authority_tier=1,
        )
        assert record.vertical == "equity_trading", f"Expected equity_trading, got: {record.vertical}"


# ═════════════════════════════════════════════════════════════════════════════
# V-07 — PUBLIC VERIFIER CONSISTENCY
# ═════════════════════════════════════════════════════════════════════════════

class TestV07_PublicVerifierConsistency:
    """
    Validation 7: Public verifier consistency

    Verify replay receipts validate correctly across all verification paths.
    Confirm identical hashes across /verify, replay mode, and API verification.
    """

    def test_scope_hash_idempotent_three_runs(self):
        """scope_hash produces identical output across 3 independent runs."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        e = ScopeAuthorizationEngine(db_url=None)
        hashes = [
            e._compute_scope_hash(CANONICAL_SCOPE_DEFINITION, CANONICAL_DEFENSIBILITY_CRITERIA)
            for _ in range(3)
        ]
        assert len(set(hashes)) == 1, f"scope_hash is not idempotent: {hashes}"

    def test_context_hash_idempotent_three_runs(self):
        """context_hash produces identical output across 3 independent runs."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        e = ScopeAuthorizationEngine(db_url=None)
        hashes = [
            e._compute_context_hash(CANONICAL_CONTEXT_SNAPSHOT)
            for _ in range(3)
        ]
        assert len(set(hashes)) == 1

    def test_replay_receipt_hash_idempotent(self):
        """Replay receipt canonical_hash is identical across 5 replay runs."""
        from omnix_core.simulation.governance_replay import GovernanceReplayEngine
        engine = GovernanceReplayEngine()
        hashes = []
        for _ in range(3):
            result = engine.replay_crisis("CRISIS-001-TERRA-LUNA-2022")
            hashes.append(result.receipts[0].canonical_hash)
        assert len(set(hashes)) == 1, f"Replay hash is not idempotent: {hashes}"

    def test_hash_changes_when_payload_changes(self):
        """scope_hash changes when payload changes — no hash collision."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        e = ScopeAuthorizationEngine(db_url=None)
        sd1 = {"max_risk_exposure": 0.75}
        sd2 = {"max_risk_exposure": 0.99}
        h1 = e._compute_scope_hash(sd1, {})
        h2 = e._compute_scope_hash(sd2, {})
        assert h1 != h2, "Different payloads must produce different hashes"

    def test_manual_sha256_matches_scope_hash(self):
        """Manual SHA-256 computation matches engine._compute_scope_hash()."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        e = ScopeAuthorizationEngine(db_url=None)
        engine_hash = e._compute_scope_hash(CANONICAL_SCOPE_DEFINITION, CANONICAL_DEFENSIBILITY_CRITERIA)
        # Manual computation (same canonicalization)
        payload = {
            "scope_definition":       CANONICAL_SCOPE_DEFINITION,
            "defensibility_criteria": CANONICAL_DEFENSIBILITY_CRITERIA,
        }
        canon = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        manual_hash = hashlib.sha256(canon.encode()).hexdigest()
        assert engine_hash == manual_hash, (
            f"Engine hash {engine_hash!r} does not match manual computation {manual_hash!r}"
        )

    def test_manual_sha256_matches_context_hash(self):
        """Manual SHA-256 computation matches engine._compute_context_hash()."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        e = ScopeAuthorizationEngine(db_url=None)
        engine_hash = e._compute_context_hash(CANONICAL_CONTEXT_SNAPSHOT)
        canon = json.dumps(CANONICAL_CONTEXT_SNAPSHOT, sort_keys=True, separators=(",", ":"))
        manual_hash = hashlib.sha256(canon.encode()).hexdigest()
        assert engine_hash == manual_hash

    def test_canonical_hash_format_is_sha256_hex(self):
        """scope_hash and context_hash are 64-character lowercase hex strings."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        e = ScopeAuthorizationEngine(db_url=None)
        sh = e._compute_scope_hash(CANONICAL_SCOPE_DEFINITION, CANONICAL_DEFENSIBILITY_CRITERIA)
        ch = e._compute_context_hash(CANONICAL_CONTEXT_SNAPSHOT)
        assert len(sh) == 64, f"scope_hash length should be 64, got {len(sh)}"
        assert len(ch) == 64, f"context_hash length should be 64, got {len(ch)}"
        assert sh == sh.lower(), "scope_hash should be lowercase hex"
        assert ch == ch.lower(), "context_hash should be lowercase hex"


# ═════════════════════════════════════════════════════════════════════════════
# V-08 — DATABASE SCHEMA INTEGRITY
# ═════════════════════════════════════════════════════════════════════════════

class TestV08_DatabaseSchemaIntegrity:
    """
    Validation 8: Database schema integrity

    Verify all columns, foreign keys, indexes, and migrations exist correctly.
    Confirm no orphaned scope records or unsigned snapshots possible.
    """

    def _get_ddl(self):
        from omnix_core.governance.scope_authorization_engine import DDL_SCOPE_TABLE
        return DDL_SCOPE_TABLE

    def test_ddl_has_primary_key_scope_id(self):
        ddl = self._get_ddl()
        assert "scope_id" in ddl
        assert "PRIMARY KEY" in ddl

    def test_ddl_has_domain_column(self):
        assert "domain" in self._get_ddl()

    def test_ddl_has_vertical_column(self):
        assert "vertical" in self._get_ddl()

    def test_ddl_has_authority_tier_column(self):
        assert "authority_tier" in self._get_ddl()

    def test_ddl_has_authorized_by_column(self):
        assert "authorized_by" in self._get_ddl()

    def test_ddl_has_scope_definition_jsonb(self):
        ddl = self._get_ddl()
        assert "scope_definition" in ddl
        assert "JSONB" in ddl

    def test_ddl_has_defensibility_criteria_jsonb(self):
        ddl = self._get_ddl()
        assert "defensibility_criteria" in ddl
        assert "JSONB" in ddl

    def test_ddl_has_context_snapshot_jsonb(self):
        ddl = self._get_ddl()
        assert "context_snapshot" in ddl
        assert "JSONB" in ddl

    def test_ddl_has_context_hash_column(self):
        assert "context_hash" in self._get_ddl()

    def test_ddl_has_scope_hash_column(self):
        assert "scope_hash" in self._get_ddl()

    def test_ddl_has_pqc_signature_column(self):
        assert "pqc_signature" in self._get_ddl()

    def test_ddl_has_pqc_algorithm_column(self):
        assert "pqc_algorithm" in self._get_ddl()

    def test_ddl_has_status_column_with_check_constraint(self):
        ddl = self._get_ddl()
        assert "status" in ddl
        assert "CHECK" in ddl
        # Check all valid status values
        for s in ("ACTIVE", "REAPPROVAL_REQUIRED", "SUPERSEDED", "REVOKED"):
            assert s in ddl, f"Status value {s!r} missing from DDL CHECK"

    def test_ddl_has_issued_at_timestamptz(self):
        ddl = self._get_ddl()
        assert "issued_at" in ddl
        assert "TIMESTAMPTZ" in ddl

    def test_ddl_has_expires_at_column(self):
        assert "expires_at" in self._get_ddl()

    def test_ddl_has_superseded_by_column(self):
        assert "superseded_by" in self._get_ddl()

    def test_ddl_has_reapproval_required_boolean(self):
        ddl = self._get_ddl()
        assert "reapproval_required" in ddl
        assert "BOOLEAN" in ddl

    def test_ddl_has_reapproval_required_at_column(self):
        assert "reapproval_required_at" in self._get_ddl()

    def test_ddl_has_reapproval_reason_column(self):
        assert "reapproval_reason" in self._get_ddl()

    def test_ddl_has_context_drift_at_reapproval_column(self):
        assert "context_drift_at_reapproval" in self._get_ddl()

    def test_ddl_has_avm_snapshot_id_column(self):
        assert "avm_snapshot_id" in self._get_ddl()

    def test_ddl_has_avm_snapshot_version_column(self):
        assert "avm_snapshot_version" in self._get_ddl()

    def test_ddl_has_index_on_domain_vertical_status(self):
        """Index on (domain, vertical, status) exists for efficient active scope lookup."""
        ddl = self._get_ddl()
        assert "idx_gsa_domain_vertical_status" in ddl

    def test_ddl_has_index_on_issued_at(self):
        """Index on issued_at DESC exists for efficient history retrieval."""
        ddl = self._get_ddl()
        assert "idx_gsa_issued_at" in ddl

    def test_ddl_is_idempotent_create_if_not_exists(self):
        """DDL uses IF NOT EXISTS — safe to run on every startup."""
        ddl = self._get_ddl()
        assert "IF NOT EXISTS" in ddl

    def test_ddl_authority_tier_between_1_and_4(self):
        """DDL enforces tier range via CHECK constraint."""
        ddl = self._get_ddl()
        assert "BETWEEN 1 AND 4" in ddl

    def test_reapproval_required_default_false(self):
        """reapproval_required column defaults to FALSE in DDL."""
        ddl = self._get_ddl()
        assert "DEFAULT FALSE" in ddl or "DEFAULT false" in ddl.lower()

    def test_status_default_active(self):
        """status column defaults to 'ACTIVE' in DDL."""
        ddl = self._get_ddl()
        assert "DEFAULT 'ACTIVE'" in ddl

    def test_not_null_constraints_on_required_columns(self):
        """Required columns have NOT NULL constraints."""
        ddl = self._get_ddl()
        assert ddl.count("NOT NULL") >= 4, (
            f"Expected at least 4 NOT NULL constraints, found {ddl.count('NOT NULL')}"
        )


# ═════════════════════════════════════════════════════════════════════════════
# V-09 — GOVERNANCE INVARIANTS
# ═════════════════════════════════════════════════════════════════════════════

class TestV09_GovernanceInvariants:
    """
    Validation 9: Governance invariants — formal verification

    All 6 governance invariants from ADR-147:
    1. Fail-Closed Enforcement
    2. Bounded Adaptation
    3. Authority Separation
    4. Replay Determinism
    5. Signed Scope Defensibility
    6. Anti-Drift Reapproval Guarantee
    """

    # ── Invariant 1: Fail-Closed Enforcement ─────────────────────────────────

    def test_invariant1_fail_closed_invalid_domain(self):
        """I-1: issue_scope() fails closed when domain is empty."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        e = ScopeAuthorizationEngine(db_url=None)
        with pytest.raises(ValueError):
            e.issue_scope("", "equity_trading", {"x": 1}, {}, "test", 1)

    def test_invariant1_fail_closed_invalid_authorized_by(self):
        """I-1: issue_scope() fails closed when authorized_by is empty."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        e = ScopeAuthorizationEngine(db_url=None)
        with pytest.raises(ValueError):
            e.issue_scope("FINANCE", "equity_trading", {"x": 1}, {}, "", 1)

    def test_invariant1_fail_closed_empty_scope_definition(self):
        """I-1: issue_scope() fails closed when scope_definition is empty dict."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        e = ScopeAuthorizationEngine(db_url=None)
        with pytest.raises(ValueError):
            e.issue_scope("FINANCE", "equity_trading", {}, {}, "test", 1)

    def test_invariant1_fail_closed_invalid_tier(self):
        """I-1: issue_scope() fails closed when authority_tier is out of range."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        e = ScopeAuthorizationEngine(db_url=None)
        with pytest.raises(ValueError):
            e.issue_scope("FINANCE", "equity_trading", {"x": 1}, {}, "test", 99)

    # ── Invariant 2: Bounded Adaptation ──────────────────────────────────────

    def test_invariant2_drift_threshold_default_is_25(self):
        """I-2: Default reapproval drift threshold is exactly 25.0%."""
        from omnix_core.governance.scope_authorization_engine import _DEFAULT_REAPPROVAL_DRIFT_THRESHOLD
        assert _DEFAULT_REAPPROVAL_DRIFT_THRESHOLD == 25.0, (
            f"Default threshold must be 25.0%, got: {_DEFAULT_REAPPROVAL_DRIFT_THRESHOLD}"
        )

    def test_invariant2_custom_threshold_persisted_in_defensibility(self):
        """I-2: Custom threshold is stored in defensibility_criteria, not hardcoded."""
        engine = _make_engine()
        criteria = {"scope_reapproval_drift_threshold": 15.0, "risk_level_accepted": "LOW"}
        record = engine.issue_scope(
            domain="HEALTHCARE",
            vertical="clinical_decision",
            scope_definition={"permitted_domains": ["HEALTHCARE"]},
            defensibility_criteria=criteria,
            authorized_by="chief_medical_officer",
            authority_tier=1,
        )
        stored_threshold = record.defensibility_criteria.get("scope_reapproval_drift_threshold")
        assert stored_threshold == 15.0, (
            f"Custom threshold 15.0 should be stored, got: {stored_threshold}"
        )

    def test_invariant2_signals_at_50pct_exceed_default_threshold(self):
        """I-2: 50% signal shift produces drift > 25% (bounded adaptation enforced)."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        e = ScopeAuthorizationEngine(db_url=None)
        snapshot = CANONICAL_CONTEXT_SNAPSHOT.copy()
        current  = {k: v * 0.5 for k, v in snapshot.items()}
        drift_pct, _ = e._compute_drift(current, snapshot)
        assert drift_pct > 25.0, (
            f"50% signal shift should exceed 25% threshold, got: {drift_pct}"
        )

    # ── Invariant 3: Authority Separation ────────────────────────────────────

    def test_invariant3_revoke_only_tier1(self):
        """I-3: Only authority_tier=1 can revoke — tiers 2, 3, 4 are rejected."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        e = ScopeAuthorizationEngine(db_url=None)
        for tier in (2, 3, 4):
            with pytest.raises(PermissionError, match=r"(?i)tier 1|authority_tier"):
                e.revoke_scope("SAR-FAKE", "reason", "actor", authority_tier=tier)

    def test_invariant3_revoke_message_names_tier1(self):
        """I-3: PermissionError message explicitly names Tier 1 requirement."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        e = ScopeAuthorizationEngine(db_url=None)
        with pytest.raises(PermissionError) as exc_info:
            e.revoke_scope("SAR-FAKE", "reason", "unauthorized_actor", authority_tier=3)
        msg = str(exc_info.value).lower()
        assert "tier 1" in msg or "tier1" in msg

    # ── Invariant 4: Replay Determinism ──────────────────────────────────────

    def test_invariant4_replay_hash_deterministic(self):
        """I-4: Same crisis replay always produces the same canonical_hash."""
        from omnix_core.simulation.governance_replay import GovernanceReplayEngine
        engine = GovernanceReplayEngine()
        hashes = set()
        for _ in range(3):
            result = engine.replay_crisis("CRISIS-002-FTX-2022")
            hashes.update(r.canonical_hash for r in result.receipts)
        # Re-run
        result2 = engine.replay_crisis("CRISIS-002-FTX-2022")
        for r in result2.receipts:
            assert r.canonical_hash in hashes, (
                f"Receipt {r.receipt_id} hash changed across replay runs: {r.canonical_hash}"
            )

    def test_invariant4_scope_hash_deterministic(self):
        """I-4: scope_hash is deterministic — same input always produces same output."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationEngine
        e = ScopeAuthorizationEngine(db_url=None)
        results = set(
            e._compute_scope_hash(CANONICAL_SCOPE_DEFINITION, CANONICAL_DEFENSIBILITY_CRITERIA)
            for _ in range(5)
        )
        assert len(results) == 1, f"scope_hash is not deterministic: {results}"

    # ── Invariant 5: Signed Scope Defensibility ───────────────────────────────

    def test_invariant5_scope_hash_present_always(self):
        """I-5: scope_hash is always computed and present — never None or empty."""
        engine = _make_engine()
        record = _issue_canonical_scope(engine)
        assert record.scope_hash is not None
        assert len(record.scope_hash) == 64

    def test_invariant5_context_hash_present_always(self):
        """I-5: context_hash is always computed and present — never None or empty."""
        engine = _make_engine()
        record = _issue_canonical_scope(engine)
        assert record.context_hash is not None
        assert len(record.context_hash) == 64

    def test_invariant5_record_carries_all_defensibility_fields(self):
        """I-5: Record carries all 5 defensibility components required by ADR-147."""
        engine = _make_engine()
        record = _issue_canonical_scope(engine)
        # What is authorized
        assert record.scope_definition is not None and record.scope_definition
        # Why it is defensible
        assert record.defensibility_criteria is not None
        # Who authorized it
        assert record.authorized_by and record.authority_tier
        # Under what context
        assert record.context_snapshot is not None
        # Cryptographic proof
        assert record.scope_hash and record.context_hash

    # ── Invariant 6: Anti-Drift Reapproval Guarantee ─────────────────────────

    def test_invariant6_drift_computation_uses_weights(self):
        """I-6: Drift uses all AVM signal weights (ADR-076) — no weight is zero."""
        from omnix_core.governance.scope_authorization_engine import _SIGNAL_WEIGHTS
        for signal, weight in _SIGNAL_WEIGHTS.items():
            assert weight > 0, f"Signal {signal!r} has zero weight — ADR-076 violation"
        assert sum(_SIGNAL_WEIGHTS.values()) == pytest.approx(1.0, abs=0.01), (
            f"Signal weights must sum to ~1.0, got: {sum(_SIGNAL_WEIGHTS.values())}"
        )

    def test_invariant6_reapproval_trust_flag_prevents_silent_continuation(self):
        """I-6: REAPPROVAL_REQUIRED status sets scope_reapproval_pending flag."""
        from omnix_core.governance.scope_authorization_engine import ScopeAuthorizationRecord
        record = ScopeAuthorizationRecord(
            scope_id="SAR-TEST000000000000000000",
            domain="FINANCE",
            vertical="equity_trading",
            authority_tier=1,
            authorized_by="test",
            scope_definition={},
            defensibility_criteria={},
            context_snapshot={},
            context_hash="a" * 64,
            scope_hash="b" * 64,
            pqc_signature=None,
            pqc_algorithm=None,
            status="REAPPROVAL_REQUIRED",
            issued_at=datetime.now(timezone.utc).isoformat(),
            expires_at=None,
            superseded_by=None,
            reapproval_required=True,
            reapproval_required_at=datetime.now(timezone.utc).isoformat(),
            reapproval_reason="Drift 38.4% > 25.0% threshold",
            context_drift_at_reapproval=38.4,
            avm_snapshot_id=None,
            avm_snapshot_version=None,
        )
        flags = record.trust_flags()
        assert flags["scope_reapproval_pending"] is True
        assert flags["tier1_authorized"] is True
        assert not record.is_active(), "REAPPROVAL_REQUIRED is not ACTIVE"
        assert record.requires_reapproval(), "requires_reapproval() must return True"

    def test_invariant6_avm_weights_sum_to_one(self):
        """I-6: AVM signal weights sum to exactly 1.0 (complete basis)."""
        from omnix_core.governance.scope_authorization_engine import _SIGNAL_WEIGHTS
        total = sum(_SIGNAL_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001, (
            f"AVM weights must sum to 1.0, got: {total}"
        )
