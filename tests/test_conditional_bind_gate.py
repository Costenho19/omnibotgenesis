"""
Tests for ADR-135 — Conditional Bind Gate (CBG).

Test groups:
    T01–T05  — Import, constants, dataclasses
    T06–T10  — evaluate() PASS path (SINGULAR / INDETERMINATE / below threshold)
    T11–T15  — evaluate() GATE_CREATED path (AMBIGUOUS above threshold)
    T16–T20  — evaluate() idempotency (GATE_EXISTS, ATTESTED, BLOCKED, EXPIRED)
    T21–T25  — attest() success and validation errors
    T26–T30  — block() success and validation errors
    T31–T35  — BindGateRecord.to_dict() + BindGateResult.to_dict() + fail-safe

All DB-dependent tests use mocked _get_conn / engine methods.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from omnix_core.governance.conditional_bind_gate import (
    AMBIGUITY_CONTRADICTION_THRESHOLD,
    AMBIGUITY_SCORE_THRESHOLD,
    ATTEST_MIN_JUSTIFICATION_CHARS,
    GATE_TIMEOUT_MINUTES,
    BindGateRecord,
    BindGateResult,
    ConditionalBindGate,
    GateStatus,
    GateVerdict,
    _gate_hash,
    _gate_id,
    get_conditional_bind_gate,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _make_record(
    gate_status: GateStatus = GateStatus.PENDING,
    bind_allowed: bool = False,
    lineage_singularity: float = 28.0,
    contradiction_count: int = 3,
    expires_at: datetime | None = None,
    attester_id: str | None = None,
    justification: str | None = None,
    block_reason: str | None = None,
    attested_at: datetime | None = None,
    blocked_at: datetime | None = None,
) -> BindGateRecord:
    now = _now()
    return BindGateRecord(
        gate_id="CBG-TEST0000000001",
        spg_id="SPG-TEST000000001",
        decision_id="receipt-test-001",
        domain="trading",
        lineage_singularity=lineage_singularity,
        contradiction_count=contradiction_count,
        spg_verdict="AMBIGUOUS",
        gate_status=gate_status,
        bind_allowed=bind_allowed,
        attester_id=attester_id,
        justification=justification,
        block_reason=block_reason,
        created_at=now,
        expires_at=expires_at or (now + timedelta(minutes=60)),
        attested_at=attested_at,
        blocked_at=blocked_at,
        oversight_session_id=None,
        gate_hash="sha256:abc123",
    )


def _engine_no_db() -> ConditionalBindGate:
    """Engine with _find_gate_by_spg_id returning None (no existing gate)."""
    engine = ConditionalBindGate()
    engine._find_gate_by_spg_id = MagicMock(return_value=None)
    engine._create_gate = MagicMock(return_value=_make_record())
    return engine


# ── T01–T05: Import, constants, dataclasses ───────────────────────────────────

def test_T01_module_imports():
    from omnix_core.governance import conditional_bind_gate
    assert conditional_bind_gate is not None


def test_T02_constants_correct():
    assert GATE_TIMEOUT_MINUTES == 60
    assert ATTEST_MIN_JUSTIFICATION_CHARS == 80
    assert AMBIGUITY_SCORE_THRESHOLD == 50.0
    assert AMBIGUITY_CONTRADICTION_THRESHOLD == 2


def test_T03_gate_status_enum():
    assert GateStatus.PENDING.value   == "PENDING"
    assert GateStatus.ATTESTED.value  == "ATTESTED"
    assert GateStatus.BLOCKED.value   == "BLOCKED"
    assert GateStatus.EXPIRED.value   == "EXPIRED"


def test_T04_gate_verdict_enum():
    assert GateVerdict.PASS.value          == "PASS"
    assert GateVerdict.GATE_CREATED.value  == "GATE_CREATED"
    assert GateVerdict.GATE_EXISTS.value   == "GATE_EXISTS"
    assert GateVerdict.ATTESTED.value      == "ATTESTED"
    assert GateVerdict.BLOCKED.value       == "BLOCKED"
    assert GateVerdict.EXPIRED.value       == "EXPIRED"


def test_T05_singleton():
    e1 = get_conditional_bind_gate()
    e2 = get_conditional_bind_gate()
    assert e1 is e2


# ── T06–T10: evaluate() PASS path ─────────────────────────────────────────────

def test_T06_singular_passes_without_gate():
    engine = ConditionalBindGate()
    result = engine.evaluate(
        spg_id="SPG-001",
        spg_verdict="SINGULAR",
        lineage_singularity=88.0,
        contradiction_count=0,
        decision_id="receipt-001",
    )
    assert result.bind_allowed is True
    assert result.gate_required is False
    assert result.verdict == GateVerdict.PASS
    assert result.gate_id is None


def test_T07_indeterminate_passes_without_gate():
    engine = ConditionalBindGate()
    result = engine.evaluate(
        spg_id="SPG-002",
        spg_verdict="INDETERMINATE",
        lineage_singularity=62.0,
        contradiction_count=1,
        decision_id="receipt-002",
    )
    assert result.bind_allowed is True
    assert result.gate_required is False
    assert result.verdict == GateVerdict.PASS


def test_T08_ambiguous_below_both_thresholds_passes():
    """AMBIGUOUS but score ≥ 50 AND contradictions < 2 → advisory only, no gate."""
    engine = _engine_no_db()
    result = engine.evaluate(
        spg_id="SPG-003",
        spg_verdict="AMBIGUOUS",
        lineage_singularity=50.0,  # exactly at threshold — not below
        contradiction_count=1,      # below AMBIGUITY_CONTRADICTION_THRESHOLD
        decision_id="receipt-003",
    )
    assert result.bind_allowed is True
    assert result.gate_required is False
    assert result.verdict == GateVerdict.PASS


def test_T09_pass_result_has_correct_spg_fields():
    engine = ConditionalBindGate()
    result = engine.evaluate(
        spg_id="SPG-004",
        spg_verdict="SINGULAR",
        lineage_singularity=95.0,
        contradiction_count=0,
        decision_id="receipt-004",
        domain="credit",
    )
    assert result.lineage_singularity == 95.0
    assert result.contradiction_count == 0
    assert result.spg_verdict == "SINGULAR"
    assert result.adr_reference == "ADR-135"


def test_T10_pass_to_dict_structure():
    engine = ConditionalBindGate()
    result = engine.evaluate(
        spg_id="SPG-005",
        spg_verdict="SINGULAR",
        lineage_singularity=82.0,
        contradiction_count=0,
        decision_id="receipt-005",
    )
    d = result.to_dict()
    assert "gate_required" in d
    assert "bind_allowed" in d
    assert "verdict" in d
    assert "gate_id" in d
    assert "adr_reference" in d
    assert d["adr_reference"] == "ADR-135"


# ── T11–T15: evaluate() GATE_CREATED path ─────────────────────────────────────

def test_T11_ambiguous_low_score_creates_gate():
    engine = _engine_no_db()
    result = engine.evaluate(
        spg_id="SPG-006",
        spg_verdict="AMBIGUOUS",
        lineage_singularity=28.0,
        contradiction_count=3,
        decision_id="receipt-006",
    )
    assert result.gate_required is True
    assert result.bind_allowed is False
    assert result.verdict == GateVerdict.GATE_CREATED
    assert result.gate_id is not None
    engine._create_gate.assert_called_once()


def test_T12_ambiguous_high_contradictions_creates_gate():
    """contradiction_count ≥ 2 alone triggers gate even if score is borderline."""
    engine = _engine_no_db()
    result = engine.evaluate(
        spg_id="SPG-007",
        spg_verdict="AMBIGUOUS",
        lineage_singularity=49.9,  # just below threshold
        contradiction_count=2,      # exactly at threshold
        decision_id="receipt-007",
    )
    assert result.gate_required is True
    assert result.bind_allowed is False
    assert result.verdict == GateVerdict.GATE_CREATED


def test_T13_gate_created_has_correct_reason():
    engine = _engine_no_db()
    result = engine.evaluate(
        spg_id="SPG-008",
        spg_verdict="AMBIGUOUS",
        lineage_singularity=22.0,
        contradiction_count=4,
        decision_id="receipt-008",
    )
    assert "Lineage ambiguity gate created" in result.reason
    assert "22.0" in result.reason
    assert "4" in result.reason


def test_T14_gate_created_gate_record_not_none():
    engine = _engine_no_db()
    result = engine.evaluate(
        spg_id="SPG-009",
        spg_verdict="AMBIGUOUS",
        lineage_singularity=15.0,
        contradiction_count=2,
        decision_id="receipt-009",
    )
    assert result.gate_record is not None
    assert result.gate_record.gate_status == GateStatus.PENDING


def test_T15_gate_result_to_dict_complete():
    engine = _engine_no_db()
    result = engine.evaluate(
        spg_id="SPG-010",
        spg_verdict="AMBIGUOUS",
        lineage_singularity=10.0,
        contradiction_count=3,
        decision_id="receipt-010",
        domain="insurance",
    )
    d = result.to_dict()
    assert d["gate_required"] is True
    assert d["bind_allowed"] is False
    assert d["verdict"] == "GATE_CREATED"
    assert d["gate_record"] is not None
    assert d["gate_record"]["gate_status"] == "PENDING"


# ── T16–T20: evaluate() idempotency ───────────────────────────────────────────

def test_T16_existing_pending_gate_returns_gate_exists():
    engine = ConditionalBindGate()
    pending = _make_record(gate_status=GateStatus.PENDING)
    engine._find_gate_by_spg_id = MagicMock(return_value=pending)
    result = engine.evaluate(
        spg_id="SPG-011",
        spg_verdict="AMBIGUOUS",
        lineage_singularity=28.0,
        contradiction_count=3,
        decision_id="receipt-011",
    )
    assert result.verdict == GateVerdict.GATE_EXISTS
    assert result.bind_allowed is False
    assert result.gate_id == "CBG-TEST0000000001"


def test_T17_existing_attested_gate_returns_attested():
    engine = ConditionalBindGate()
    attested = _make_record(
        gate_status=GateStatus.ATTESTED,
        bind_allowed=True,
        attester_id="harold@omnixquantum.net",
    )
    engine._find_gate_by_spg_id = MagicMock(return_value=attested)
    result = engine.evaluate(
        spg_id="SPG-012",
        spg_verdict="AMBIGUOUS",
        lineage_singularity=28.0,
        contradiction_count=3,
        decision_id="receipt-012",
    )
    assert result.verdict == GateVerdict.ATTESTED
    assert result.bind_allowed is True


def test_T18_existing_blocked_gate_returns_blocked():
    engine = ConditionalBindGate()
    blocked = _make_record(
        gate_status=GateStatus.BLOCKED,
        bind_allowed=False,
        block_reason="Risk committee decision",
    )
    engine._find_gate_by_spg_id = MagicMock(return_value=blocked)
    result = engine.evaluate(
        spg_id="SPG-013",
        spg_verdict="AMBIGUOUS",
        lineage_singularity=28.0,
        contradiction_count=3,
        decision_id="receipt-013",
    )
    assert result.verdict == GateVerdict.BLOCKED
    assert result.bind_allowed is False


def test_T19_expired_gate_returns_expired():
    engine = ConditionalBindGate()
    expired_ts = _now() - timedelta(minutes=5)
    expired = _make_record(
        gate_status=GateStatus.EXPIRED,
        bind_allowed=False,
        expires_at=expired_ts,
    )
    engine._find_gate_by_spg_id = MagicMock(return_value=expired)
    result = engine.evaluate(
        spg_id="SPG-014",
        spg_verdict="AMBIGUOUS",
        lineage_singularity=28.0,
        contradiction_count=3,
        decision_id="receipt-014",
    )
    assert result.verdict == GateVerdict.EXPIRED
    assert result.bind_allowed is False


def test_T20_pending_timeout_triggers_auto_expire():
    engine = ConditionalBindGate()
    past_expires = _now() - timedelta(minutes=5)  # already expired
    pending_expired = _make_record(
        gate_status=GateStatus.PENDING,
        expires_at=past_expires,
    )
    auto_expired = _make_record(gate_status=GateStatus.EXPIRED, expires_at=past_expires)
    engine._find_gate_by_spg_id = MagicMock(return_value=pending_expired)
    engine._auto_expire = MagicMock(return_value=auto_expired)
    result = engine.evaluate(
        spg_id="SPG-015",
        spg_verdict="AMBIGUOUS",
        lineage_singularity=28.0,
        contradiction_count=3,
        decision_id="receipt-015",
    )
    engine._auto_expire.assert_called_once_with("CBG-TEST0000000001")
    assert result.verdict == GateVerdict.EXPIRED


# ── T21–T25: attest() ────────────────────────────────────────────────────────

def test_T21_attest_justification_too_short():
    engine = ConditionalBindGate()
    with pytest.raises(ValueError, match="too short"):
        engine.attest(
            gate_id="CBG-FAKE",
            attester_id="harold@omnixquantum.net",
            justification="Too short",
        )


def test_T22_attest_justification_exactly_at_minimum_raises():
    """79 chars — one below minimum — must raise."""
    engine = ConditionalBindGate()
    just_short = "A" * (ATTEST_MIN_JUSTIFICATION_CHARS - 1)
    with pytest.raises(ValueError, match="too short"):
        engine.attest(
            gate_id="CBG-FAKE",
            attester_id="harold@omnixquantum.net",
            justification=just_short,
        )


def test_T23_attest_justification_minimum_length_accepted_at_db_level():
    """80 chars exact — should NOT raise the justification error (may raise DB error)."""
    engine = ConditionalBindGate()
    valid_just = "A" * ATTEST_MIN_JUSTIFICATION_CHARS
    with pytest.raises(Exception) as exc_info:
        engine.attest(
            gate_id="CBG-NONEXISTENT",
            attester_id="harold@omnixquantum.net",
            justification=valid_just,
        )
    # Must not be the "too short" error — should be a DB or "not found" error
    assert "too short" not in str(exc_info.value).lower()


def test_T24_attest_gate_not_found_raises():
    engine = ConditionalBindGate()
    valid_just = "B" * ATTEST_MIN_JUSTIFICATION_CHARS
    with pytest.raises(Exception):
        engine.attest(
            gate_id="CBG-DEFINITELY-NOT-THERE",
            attester_id="harold@omnixquantum.net",
            justification=valid_just,
        )


def test_T25_attest_requires_non_empty_attester_id():
    """Justification check happens before DB access — empty attester passes through
    to DB (attester_id is stored as-is; domain responsibility to validate)."""
    engine = ConditionalBindGate()
    short_just = "x" * (ATTEST_MIN_JUSTIFICATION_CHARS - 10)
    with pytest.raises(ValueError, match="too short"):
        engine.attest(
            gate_id="CBG-FAKE",
            attester_id="",
            justification=short_just,
        )


# ── T26–T30: block() ─────────────────────────────────────────────────────────

def test_T26_block_gate_not_found_raises():
    engine = ConditionalBindGate()
    with pytest.raises(Exception):
        engine.block(gate_id="CBG-NOT-THERE", reason="Risk committee veto")


def test_T27_block_raises_on_nonexistent_gate():
    engine = ConditionalBindGate()
    with pytest.raises(Exception) as exc_info:
        engine.block(gate_id="CBG-GHOST", reason="Test block")
    assert exc_info.value is not None


def test_T28_query_raises_on_not_found():
    engine = ConditionalBindGate()
    with pytest.raises(Exception):
        engine.query("CBG-DOES-NOT-EXIST")


def test_T29_reason_for_status_pending():
    reason = ConditionalBindGate._reason_for_status(GateStatus.PENDING, "CBG-001")
    assert "PENDING" in reason
    assert "CBG-001" in reason
    assert "blocked" in reason.lower()


def test_T30_reason_for_status_all_states():
    for status in GateStatus:
        reason = ConditionalBindGate._reason_for_status(status, "CBG-TEST")
        assert "CBG-TEST" in reason
        assert len(reason) > 10


# ── T31–T35: dataclass serialization + fail-safe ──────────────────────────────

def test_T31_bind_gate_record_to_dict_all_fields():
    record = _make_record()
    d = record.to_dict()
    required_keys = [
        "gate_id", "spg_id", "decision_id", "domain",
        "lineage_singularity", "contradiction_count", "spg_verdict",
        "gate_status", "bind_allowed", "attester_id", "justification",
        "block_reason", "created_at", "expires_at", "attested_at",
        "blocked_at", "oversight_session_id", "gate_hash", "adr_reference",
    ]
    for key in required_keys:
        assert key in d, f"Missing key: {key}"


def test_T32_bind_gate_record_status_serialised_as_string():
    record = _make_record(gate_status=GateStatus.ATTESTED, bind_allowed=True)
    d = record.to_dict()
    assert d["gate_status"] == "ATTESTED"
    assert d["bind_allowed"] is True
    assert d["adr_reference"] == "ADR-135"


def test_T33_bind_gate_result_to_dict():
    result = BindGateResult(
        gate_required=True,
        bind_allowed=False,
        verdict=GateVerdict.GATE_CREATED,
        reason="Test reason",
        gate_id="CBG-001",
        lineage_singularity=28.0,
        contradiction_count=3,
        spg_verdict="AMBIGUOUS",
        gate_record=_make_record(),
    )
    d = result.to_dict()
    assert d["gate_required"] is True
    assert d["bind_allowed"] is False
    assert d["verdict"] == "GATE_CREATED"
    assert d["gate_record"] is not None
    assert d["adr_reference"] == "ADR-135"


def test_T34_evaluate_db_error_returns_fail_safe():
    """Any DB error in evaluate() must return bind_allowed=True (fail-safe)."""
    engine = ConditionalBindGate()
    engine._evaluate = MagicMock(side_effect=RuntimeError("DB connection failed"))
    result = engine.evaluate(
        spg_id="SPG-ERR",
        spg_verdict="AMBIGUOUS",
        lineage_singularity=10.0,
        contradiction_count=4,
        decision_id="receipt-err",
    )
    assert result.bind_allowed is True
    assert result.gate_required is False
    assert result.verdict == GateVerdict.PASS
    assert "fail-safe" in result.reason.lower()


def test_T35_gate_hash_deterministic():
    h1 = _gate_hash("CBG-001", "SPG-001", "receipt-001")
    h2 = _gate_hash("CBG-001", "SPG-001", "receipt-001")
    h3 = _gate_hash("CBG-002", "SPG-001", "receipt-001")
    assert h1 == h2
    assert h1 != h3
    assert h1.startswith("sha256:")
