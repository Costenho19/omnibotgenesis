#!/usr/bin/env python3
"""
OMNIX Oversight Surface Engine (OSE) — Unit Tests (ADR-124).

Tests cover:
  1. Framing score assessment
  2. EQS computation and labels
  3. Session creation (mocked DB)
  4. Deliberation window enforcement
  5. Override friction validation
  6. Session serialization
  7. Expiry logic

Run with:
  TESTING=true TELEGRAM_BOT_TOKEN=test-token python -m pytest tests/test_oversight_surface.py -v
"""

import json
import sys
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch, call

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from omnix_core.governance.oversight_surface import (
    OversightSurfaceEngine,
    DELIBERATION_WINDOW_SECONDS,
    OVERRIDE_MIN_JUSTIFICATION_CHARS,
    SESSION_EXPIRY_HOURS,
    FRAMING_REQUIRED_FIELDS,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _ose() -> OversightSurfaceEngine:
    return OversightSurfaceEngine()


def _full_snapshot() -> dict:
    """Decision snapshot with all required framing fields."""
    return {
        "risk_score": 0.87,
        "domain": "trading",
        "original_decision": "BLOCKED",
        "block_reason": "MC_NEG_ER: expected return < 0 after fees",
        "confidence": 0.92,
        "asset": "BTC/USDT",
    }


def _mock_conn(row: dict | None = None, rows: list | None = None):
    """Build a psycopg2-like mock connection."""
    cur = MagicMock()
    cur.fetchone.return_value = row
    cur.fetchall.return_value = rows or []
    cur.rowcount = 1
    cur.__enter__ = lambda s: s
    cur.__exit__ = MagicMock(return_value=False)

    conn = MagicMock()
    conn.cursor.return_value = cur
    conn.__enter__ = lambda s: s
    conn.__exit__ = MagicMock(return_value=False)
    return conn, cur


# ── 1. Framing Assessment ──────────────────────────────────────────────────────

class TestFramingAssessment:
    def test_full_snapshot_scores_1(self):
        ose = _ose()
        score = ose._assess_framing(_full_snapshot())
        assert score == 1.0

    def test_empty_snapshot_scores_0(self):
        ose = _ose()
        assert ose._assess_framing({}) == 0.0

    def test_none_snapshot_scores_0(self):
        ose = _ose()
        assert ose._assess_framing(None) == 0.0

    def test_partial_snapshot_scores_correctly(self):
        ose = _ose()
        snapshot = {"risk_score": 0.5, "domain": "medical"}
        score = ose._assess_framing(snapshot)
        assert score == round(2 / len(FRAMING_REQUIRED_FIELDS), 4)

    def test_missing_fields_listed(self):
        ose = _ose()
        snapshot = {"risk_score": 0.5}
        missing = ose._missing_framing_fields(snapshot)
        assert "risk_score" not in missing
        assert "domain" in missing
        assert "original_decision" in missing
        assert "block_reason" in missing

    def test_all_fields_present_no_missing(self):
        ose = _ose()
        missing = ose._missing_framing_fields(_full_snapshot())
        assert missing == []

    def test_none_value_counts_as_missing(self):
        ose = _ose()
        snapshot = {"risk_score": None, "domain": "energy",
                    "original_decision": "BLOCKED", "block_reason": "test"}
        missing = ose._missing_framing_fields(snapshot)
        assert "risk_score" in missing

    def test_empty_string_counts_as_missing(self):
        ose = _ose()
        snapshot = {"risk_score": 0.5, "domain": "",
                    "original_decision": "BLOCKED", "block_reason": "test"}
        missing = ose._missing_framing_fields(snapshot)
        assert "domain" in missing


# ── 2. EQS Computation ────────────────────────────────────────────────────────

class TestEQSComputation:
    def test_perfect_conditions_score_near_1(self):
        ose = _ose()
        eqs = ose._compute_eqs(
            deliberation_seconds=DELIBERATION_WINDOW_SECONDS * 3,
            framing_score=1.0,
            action="CONFIRMED",
            justification="",
        )
        assert eqs >= 0.95

    def test_minimal_conditions_score_low(self):
        ose = _ose()
        eqs = ose._compute_eqs(
            deliberation_seconds=DELIBERATION_WINDOW_SECONDS,
            framing_score=0.0,
            action="CONFIRMED",
            justification="",
        )
        assert eqs <= 0.50

    def test_override_with_long_justification_improves_score(self):
        ose = _ose()
        short_eqs = ose._compute_eqs(
            deliberation_seconds=DELIBERATION_WINDOW_SECONDS * 2,
            framing_score=1.0,
            action="OVERRIDDEN",
            justification="x" * 50,
        )
        long_eqs = ose._compute_eqs(
            deliberation_seconds=DELIBERATION_WINDOW_SECONDS * 2,
            framing_score=1.0,
            action="OVERRIDDEN",
            justification="x" * 200,
        )
        assert long_eqs > short_eqs

    def test_override_without_justification_penalizes_score(self):
        ose = _ose()
        confirmed_eqs = ose._compute_eqs(
            deliberation_seconds=60,
            framing_score=1.0,
            action="CONFIRMED",
            justification="",
        )
        overridden_eqs = ose._compute_eqs(
            deliberation_seconds=60,
            framing_score=1.0,
            action="OVERRIDDEN",
            justification="",
        )
        assert confirmed_eqs > overridden_eqs

    def test_eqs_bounded_between_0_and_1(self):
        ose = _ose()
        for deliberation in [0, 1, 30, 300, 3600]:
            for framing in [0.0, 0.5, 1.0]:
                eqs = ose._compute_eqs(deliberation, framing, "CONFIRMED", "")
                assert 0.0 <= eqs <= 1.0, f"EQS={eqs} out of bounds for delib={deliberation} framing={framing}"

    def test_time_score_saturates_at_double_window(self):
        ose = _ose()
        eqs_2x = ose._compute_eqs(
            deliberation_seconds=DELIBERATION_WINDOW_SECONDS * 2,
            framing_score=1.0,
            action="CONFIRMED",
            justification="",
        )
        eqs_10x = ose._compute_eqs(
            deliberation_seconds=DELIBERATION_WINDOW_SECONDS * 10,
            framing_score=1.0,
            action="CONFIRMED",
            justification="",
        )
        assert eqs_2x == eqs_10x


# ── 3. EQS Labels ─────────────────────────────────────────────────────────────

class TestEQSLabels:
    def test_high_label(self):
        assert OversightSurfaceEngine._eqs_label(0.85) == "HIGH"
        assert OversightSurfaceEngine._eqs_label(1.0) == "HIGH"

    def test_medium_label(self):
        assert OversightSurfaceEngine._eqs_label(0.60) == "MEDIUM"
        assert OversightSurfaceEngine._eqs_label(0.84) == "MEDIUM"

    def test_low_label(self):
        assert OversightSurfaceEngine._eqs_label(0.35) == "LOW"
        assert OversightSurfaceEngine._eqs_label(0.59) == "LOW"

    def test_minimal_label(self):
        assert OversightSurfaceEngine._eqs_label(0.0) == "MINIMAL"
        assert OversightSurfaceEngine._eqs_label(0.34) == "MINIMAL"


# ── 4. Session Creation (mocked DB) ───────────────────────────────────────────

class TestCreateSession:
    def test_create_session_returns_session_id(self):
        ose = _ose()
        conn, cur = _mock_conn()
        with patch("omnix_core.governance.oversight_surface._get_conn", return_value=conn):
            result = ose.create_session(
                decision_id="OMNIX-TEST-001",
                domain="trading",
                original_decision="BLOCKED",
                decision_snapshot=_full_snapshot(),
            )
        assert "session_id" in result
        assert result["session_id"].startswith("OSE-")
        assert result["status"] == "PENDING"
        assert result["framing_score"] == 1.0

    def test_create_session_missing_decision_id_raises(self):
        ose = _ose()
        with pytest.raises(ValueError, match="decision_id"):
            ose.create_session(decision_id="", domain="trading", original_decision="BLOCKED")

    def test_create_session_missing_domain_raises(self):
        ose = _ose()
        with pytest.raises(ValueError, match="domain"):
            ose.create_session(decision_id="X", domain="", original_decision="BLOCKED")

    def test_create_session_missing_original_decision_raises(self):
        ose = _ose()
        with pytest.raises(ValueError, match="original_decision"):
            ose.create_session(decision_id="X", domain="trading", original_decision="")

    def test_create_session_reports_missing_framing_fields(self):
        ose = _ose()
        conn, cur = _mock_conn()
        with patch("omnix_core.governance.oversight_surface._get_conn", return_value=conn):
            result = ose.create_session(
                decision_id="OMNIX-TEST-002",
                domain="medical",
                original_decision="BLOCKED",
                decision_snapshot={"risk_score": 0.9},
            )
        assert "framing_missing" in result
        assert "domain" in result["framing_missing"]
        assert result["framing_score"] < 1.0


# ── 5. Deliberation Window ────────────────────────────────────────────────────

class TestDeliberationWindow:
    def _make_open_session(self, presented_delta_seconds: float) -> dict:
        """Return a fake OPEN session with presented_at offset by delta."""
        now = datetime.now(timezone.utc)
        presented_at = now - timedelta(seconds=presented_delta_seconds)
        return {
            "session_id": "OSE-TEST0001",
            "status": "OPEN",
            "presented_at": presented_at,
            "created_at": now - timedelta(seconds=presented_delta_seconds + 5),
            "framing_score": 1.0,
            "decision_snapshot": json.dumps(_full_snapshot()),
        }

    def test_submit_before_window_raises(self):
        ose = _ose()
        session = self._make_open_session(presented_delta_seconds=5)
        conn, cur = _mock_conn()
        with patch("omnix_core.governance.oversight_surface._get_conn", return_value=conn):
            with patch.object(ose, "_load_session", return_value=session):
                with patch.object(ose, "_check_expiry"):
                    with pytest.raises(ValueError, match="Deliberation window not met"):
                        ose.submit_review(
                            session_id="OSE-TEST0001",
                            reviewer_id="reviewer-001",
                            action="CONFIRMED",
                        )

    def test_submit_after_window_succeeds(self):
        ose = _ose()
        session = self._make_open_session(
            presented_delta_seconds=DELIBERATION_WINDOW_SECONDS + 10
        )
        conn, cur = _mock_conn()
        with patch("omnix_core.governance.oversight_surface._get_conn", return_value=conn):
            with patch.object(ose, "_load_session", return_value=session):
                with patch.object(ose, "_check_expiry"):
                    result = ose.submit_review(
                        session_id="OSE-TEST0001",
                        reviewer_id="reviewer-001",
                        action="CONFIRMED",
                    )
        assert result["action"] == "CONFIRMED"
        assert result["status"] == "SUBMITTED"
        assert result["deliberation_seconds"] >= DELIBERATION_WINDOW_SECONDS

    def test_submit_requires_open_status(self):
        ose = _ose()
        session = {
            "session_id": "OSE-TEST0002",
            "status": "PENDING",
            "presented_at": None,
            "created_at": datetime.now(timezone.utc),
            "framing_score": 1.0,
            "decision_snapshot": "{}",
        }
        with patch.object(ose, "_load_session", return_value=session):
            with patch.object(ose, "_check_expiry"):
                with pytest.raises(ValueError, match="not OPEN"):
                    ose.submit_review("OSE-TEST0002", "r1", "CONFIRMED")


# ── 6. Override Friction ───────────────────────────────────────────────────────

class TestOverrideFriction:
    def _open_session(self, presented_delta_seconds: float) -> dict:
        now = datetime.now(timezone.utc)
        return {
            "session_id": "OSE-OVR001",
            "status": "OPEN",
            "presented_at": now - timedelta(seconds=presented_delta_seconds),
            "created_at": now - timedelta(seconds=presented_delta_seconds + 5),
            "framing_score": 1.0,
            "decision_snapshot": json.dumps(_full_snapshot()),
        }

    def test_overridden_without_justification_raises(self):
        ose = _ose()
        session = self._open_session(DELIBERATION_WINDOW_SECONDS + 10)
        conn, cur = _mock_conn()
        with patch("omnix_core.governance.oversight_surface._get_conn", return_value=conn):
            with patch.object(ose, "_load_session", return_value=session):
                with patch.object(ose, "_check_expiry"):
                    with pytest.raises(ValueError, match="justification"):
                        ose.submit_review("OSE-OVR001", "r1", "OVERRIDDEN", justification="short")

    def test_overridden_with_sufficient_justification_succeeds(self):
        ose = _ose()
        session = self._open_session(DELIBERATION_WINDOW_SECONDS + 10)
        conn, cur = _mock_conn()
        with patch("omnix_core.governance.oversight_surface._get_conn", return_value=conn):
            with patch.object(ose, "_load_session", return_value=session):
                with patch.object(ose, "_check_expiry"):
                    result = ose.submit_review(
                        "OSE-OVR001",
                        "r1",
                        "OVERRIDDEN",
                        justification="x" * OVERRIDE_MIN_JUSTIFICATION_CHARS,
                    )
        assert result["action"] == "OVERRIDDEN"
        assert result["status"] == "SUBMITTED"

    def test_confirmed_needs_no_justification(self):
        ose = _ose()
        session = self._open_session(DELIBERATION_WINDOW_SECONDS + 10)
        conn, cur = _mock_conn()
        with patch("omnix_core.governance.oversight_surface._get_conn", return_value=conn):
            with patch.object(ose, "_load_session", return_value=session):
                with patch.object(ose, "_check_expiry"):
                    result = ose.submit_review("OSE-OVR001", "r1", "CONFIRMED")
        assert result["action"] == "CONFIRMED"

    def test_invalid_action_raises(self):
        ose = _ose()
        session = self._open_session(DELIBERATION_WINDOW_SECONDS + 10)
        with patch.object(ose, "_load_session", return_value=session):
            with patch.object(ose, "_check_expiry"):
                with pytest.raises(ValueError, match="action must be"):
                    ose.submit_review("OSE-OVR001", "r1", "RUBBER_STAMP")

    def test_missing_reviewer_id_raises(self):
        ose = _ose()
        session = self._open_session(DELIBERATION_WINDOW_SECONDS + 10)
        with patch.object(ose, "_load_session", return_value=session):
            with patch.object(ose, "_check_expiry"):
                with pytest.raises(ValueError, match="reviewer_id"):
                    ose.submit_review("OSE-OVR001", "", "CONFIRMED")


# ── 7. Serialization ──────────────────────────────────────────────────────────

class TestSerialization:
    def test_datetime_fields_serialized_to_isoformat(self):
        ose = _ose()
        now = datetime.now(timezone.utc)
        row = {
            "session_id": "OSE-SER001",
            "created_at": now,
            "presented_at": now,
            "submitted_at": None,
            "status": "OPEN",
            "eqs_score": 0.75,
            "framing_score": 1.0,
            "decision_snapshot": _full_snapshot(),
        }
        result = ose._serialize_session(row)
        assert isinstance(result["created_at"], str)
        assert "T" in result["created_at"]
        assert "eqs_label" in result
        assert result["eqs_label"] == "MEDIUM"

    def test_eqs_label_added_on_serialize(self):
        ose = _ose()
        row = {
            "session_id": "OSE-SER002",
            "eqs_score": 0.90,
            "framing_score": 1.0,
            "decision_snapshot": _full_snapshot(),
        }
        result = ose._serialize_session(row)
        assert result["eqs_label"] == "HIGH"


# ── 8. Constants ──────────────────────────────────────────────────────────────

class TestConstants:
    def test_deliberation_window_positive(self):
        assert DELIBERATION_WINDOW_SECONDS > 0

    def test_override_justification_positive(self):
        assert OVERRIDE_MIN_JUSTIFICATION_CHARS > 0

    def test_session_expiry_positive(self):
        assert SESSION_EXPIRY_HOURS > 0

    def test_framing_fields_not_empty(self):
        assert len(FRAMING_REQUIRED_FIELDS) >= 3

    def test_framing_fields_are_strings(self):
        for f in FRAMING_REQUIRED_FIELDS:
            assert isinstance(f, str), f"field {f!r} is not a string"
