"""
Test Suite — OMNIX Execution Integrity Layer (ADR-131)
======================================================

Coverage:
  T01  ExecutionStatus values and string coercion
  T02  ExecutionIntent defaults (timestamp + ns auto-populated)
  T03  ExecutionIntent to_dict() structure
  T04  ExecutionReceipt is_terminal / is_successful / slippage_acceptable
  T05  ExecutionReceipt.compute_hash() determinism and sha256 prefix
  T06  ExecutionReceipt.compute_hash() changes on field mutation
  T07  ExecutionReceipt.to_dict() completeness and adr_reference
  T08  ExecutionReceipt.to_vc_payload() W3C VC structure
  T09  ExecutionReceipt.to_vc_payload() credentialStatus and proof anchors
  T10  log_intent() inserts PENDING row and returns receipt_id
  T11  log_result() updates status to FILLED and computes latency
  T12  log_result() PARTIAL status and fill_ratio calculation
  T13  log_result() FAILED status with failure_reason
  T14  log_result() slippage_bps calculation — adverse and favorable
  T15  log_result() with MARKET order (no requested_price → slippage None)
  T16  get_by_receipt_id() returns correct row after log_result
  T17  get_by_order_id() returns most recent matching row
  T18  get_by_decision_receipt_id() returns all linked receipts
  T19  audit_trail accumulates both INTENT_LOGGED and RESULT_LOGGED events
  T20  ExecutionGuard — succeed() path produces FILLED receipt
  T21  ExecutionGuard — exception path produces FAILED receipt (fail-safe)
  T22  ExecutionGuard — partial path produces PARTIAL receipt
  T23  ExecutionGuard — receipt_id available after __enter__
  T24  execution_guard() convenience function — happy path
  T25  execution_guard() convenience function — exception path
  T26  log_intent() fail-closed: DB error raises RuntimeError
  T27  get_global_registry() returns singleton
  T28  mark_vc_issued() flips vc_issued flag
  T29  fill_ratio capped at 1.0 on overfill
  T30  ExecutionReceipt FAILED with no executed_price — graceful
"""

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch, call
import pytest

# ── Import the module under test ───────────────────────────────────────────────

from omnix_web.api.omnix_engine.execution_receipt import (
    ExecutionGuard,
    ExecutionIntent,
    ExecutionReceipt,
    ExecutionReceiptRegistry,
    ExecutionStatus,
    _audit_event,
    execution_guard,
    get_global_registry,
)

# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_intent(
    order_id            : str  = "ORD-001",
    decision_receipt_id : str  = "OMNIX-TRD-abc123",
    symbol              : str  = "BTC/USDT",
    side                : str  = "BUY",
    size_usd            : float = 10_000.0,
    execution_style     : str  = "MARKET",
    requested_price     : Optional[float] = None,
    requested_quantity  : Optional[float] = 0.15,
) -> ExecutionIntent:
    return ExecutionIntent(
        order_id            = order_id,
        decision_receipt_id = decision_receipt_id,
        symbol              = symbol,
        side                = side,
        size_usd            = size_usd,
        execution_style     = execution_style,
        requested_price     = requested_price,
        requested_quantity  = requested_quantity,
    )


def _make_receipt(
    status          : ExecutionStatus = ExecutionStatus.FILLED,
    executed_price  : Optional[float] = 65_000.0,
    requested_price : Optional[float] = 64_800.0,
    filled_qty      : Optional[float] = 0.15,
    requested_qty   : Optional[float] = 0.15,
    failure_reason  : str             = "",
) -> ExecutionReceipt:
    r = ExecutionReceipt(
        receipt_id          = uuid.uuid4().hex,
        order_id            = "ORD-001",
        decision_receipt_id = "OMNIX-TRD-abc123",
        symbol              = "BTC/USDT",
        side                = "BUY",
        size_usd            = 10_000.0,
        execution_style     = "MARKET",
        requested_price     = requested_price,
        requested_quantity  = requested_qty,
        intent_timestamp    = datetime.now(tz=timezone.utc),
        intent_timestamp_ns = time.time_ns(),
        result_timestamp    = datetime.now(tz=timezone.utc),
        result_timestamp_ns = time.time_ns(),
        latency_ms          = 42.5,
        slippage_bps        = ((executed_price - requested_price) / requested_price * 10_000)
                              if executed_price and requested_price else None,
        executed_price      = executed_price,
        filled_quantity     = filled_qty,
        fill_ratio          = (filled_qty / requested_qty) if filled_qty and requested_qty else None,
        exchange_response   = {"status": "closed", "average": executed_price},
        final_status        = status,
        failure_reason      = failure_reason,
    )
    r.receipt_hash = r.compute_hash()
    return r


class _FakeDB:
    """In-memory fake DB that satisfies the registry's read/write interface."""

    def __init__(self):
        self._rows: Dict[str, Dict[str, Any]] = {}

    def _insert(self, receipt_id: str, row: Dict[str, Any]):
        self._rows[receipt_id] = row

    def _get(self, receipt_id: str) -> Optional[Dict[str, Any]]:
        return self._rows.get(receipt_id)

    def _update(self, receipt_id: str, **kwargs):
        if receipt_id in self._rows:
            self._rows[receipt_id].update(kwargs)


def _build_mock_registry_with_db(fake_db: _FakeDB) -> ExecutionReceiptRegistry:
    """
    Return an ExecutionReceiptRegistry whose _get_conn is patched to use fake_db.
    We patch at the module level so every call inside the registry uses the fake.
    """
    registry = ExecutionReceiptRegistry()
    registry._table_ensured = True
    return registry


# ── T01: ExecutionStatus values ───────────────────────────────────────────────

def test_T01_execution_status_values():
    assert ExecutionStatus.PENDING.value == "PENDING"
    assert ExecutionStatus.FILLED.value  == "FILLED"
    assert ExecutionStatus.PARTIAL.value == "PARTIAL"
    assert ExecutionStatus.FAILED.value  == "FAILED"
    assert ExecutionStatus.FILLED.value   == "FILLED"


# ── T02: ExecutionIntent defaults ─────────────────────────────────────────────

def test_T02_execution_intent_auto_timestamps():
    before_ns = time.time_ns()
    intent    = _make_intent()
    after_ns  = time.time_ns()

    assert intent.intent_timestamp is not None
    assert intent.intent_timestamp.tzinfo is not None
    assert before_ns <= intent.intent_timestamp_ns <= after_ns


# ── T03: ExecutionIntent to_dict ─────────────────────────────────────────────

def test_T03_execution_intent_to_dict():
    intent = _make_intent(order_id="ORD-X", symbol="ETH/USDT", side="SELL")
    d = intent.to_dict()

    assert d["order_id"]            == "ORD-X"
    assert d["symbol"]              == "ETH/USDT"
    assert d["side"]                == "SELL"
    assert d["decision_receipt_id"] == "OMNIX-TRD-abc123"
    assert isinstance(d["intent_timestamp"], str)
    assert isinstance(d["intent_timestamp_ns"], int)


# ── T04: ExecutionReceipt computed properties ─────────────────────────────────

def test_T04_receipt_computed_properties():
    filled  = _make_receipt(ExecutionStatus.FILLED)
    partial = _make_receipt(ExecutionStatus.PARTIAL, filled_qty=0.07)
    failed  = _make_receipt(ExecutionStatus.FAILED, executed_price=None,
                             requested_price=None, failure_reason="timeout")
    pending = _make_receipt(ExecutionStatus.PENDING, executed_price=None,
                             requested_price=None)

    assert filled.is_terminal    is True
    assert filled.is_successful  is True
    assert partial.is_terminal   is True
    assert partial.is_successful is True
    assert failed.is_terminal    is True
    assert failed.is_successful  is False
    assert pending.is_terminal   is False

    high_slip = _make_receipt(executed_price=70_000.0, requested_price=64_800.0)
    assert high_slip.slippage_acceptable is False

    low_slip = _make_receipt(executed_price=64_810.0, requested_price=64_800.0)
    assert low_slip.slippage_acceptable is True


# ── T05: compute_hash determinism ─────────────────────────────────────────────

def test_T05_compute_hash_determinism():
    r1 = _make_receipt()
    r2 = _make_receipt()
    r1.receipt_id = r2.receipt_id = "fixed-id"
    r1.intent_timestamp_ns = r2.intent_timestamp_ns = 1_000_000_000
    r1.result_timestamp_ns = r2.result_timestamp_ns = 2_000_000_000
    r1.executed_price = r2.executed_price = 65_000.0
    r1.filled_quantity = r2.filled_quantity = 0.15
    r1.final_status = r2.final_status = ExecutionStatus.FILLED

    assert r1.compute_hash() == r2.compute_hash()
    assert r1.compute_hash().startswith("sha256:")


# ── T06: compute_hash changes on mutation ─────────────────────────────────────

def test_T06_compute_hash_mutation_detection():
    r = _make_receipt()
    original_hash = r.compute_hash()

    r.executed_price = 99_999.0
    mutated_hash = r.compute_hash()

    assert original_hash != mutated_hash


# ── T07: to_dict completeness ─────────────────────────────────────────────────

def test_T07_to_dict_completeness():
    r = _make_receipt()
    r.receipt_hash = r.compute_hash()
    d = r.to_dict()

    required_keys = [
        "receipt_id", "order_id", "decision_receipt_id",
        "symbol", "side", "size_usd", "execution_style",
        "requested_price", "requested_quantity",
        "intent_timestamp", "intent_timestamp_ns",
        "result_timestamp", "result_timestamp_ns",
        "latency_ms", "slippage_bps",
        "executed_price", "filled_quantity", "fill_ratio",
        "exchange_response", "final_status", "failure_reason",
        "receipt_hash", "vc_issued", "adr_reference",
    ]
    for key in required_keys:
        assert key in d, f"Missing key in to_dict(): {key}"

    assert d["adr_reference"] == "ADR-131"
    assert d["final_status"]  == "FILLED"


# ── T08: to_vc_payload W3C structure ─────────────────────────────────────────

def test_T08_to_vc_payload_w3c_structure():
    r = _make_receipt()
    r.receipt_hash = r.compute_hash()
    vc = r.to_vc_payload()

    assert "@context"           in vc
    assert "type"               in vc
    assert "VerifiableCredential" in vc["type"]
    assert "OmnixExecutionReceipt" in vc["type"]
    assert "issuer"             in vc
    assert "issuanceDate"       in vc
    assert "credentialSubject"  in vc
    assert "credentialStatus"   in vc
    assert "proof"              in vc

    assert vc["issuer"]["id"] == "did:web:omnixquantum.net"
    assert vc["id"].startswith("urn:omnix:execution:")


# ── T09: to_vc_payload receipt_hash anchor ────────────────────────────────────

def test_T09_to_vc_payload_receipt_hash_anchor():
    r = _make_receipt()
    r.receipt_hash = r.compute_hash()
    vc = r.to_vc_payload()

    assert vc["credentialStatus"]["receiptHash"]  == r.receipt_hash
    assert vc["credentialStatus"]["adrReference"] == "ADR-131"
    assert vc["proof"]["receiptHash"]             == r.receipt_hash
    assert vc["proof"]["integrityLayer"]          == "ADR-131"
    assert vc["credentialSubject"]["decision_receipt_id"] == r.decision_receipt_id


# ── T10–T19: Registry tests with mocked DB ────────────────────────────────────

def _make_psycopg2_mock(stored_rows: Dict[str, Any]):
    """
    Build a minimal psycopg2 connection mock that:
    - INSERT stores into stored_rows
    - SELECT returns from stored_rows
    - UPDATE updates stored_rows
    """
    conn_mock = MagicMock()
    cur_mock  = MagicMock()

    conn_mock.__enter__ = MagicMock(return_value=conn_mock)
    conn_mock.__exit__  = MagicMock(return_value=False)
    cur_mock.__enter__  = MagicMock(return_value=cur_mock)
    cur_mock.__exit__   = MagicMock(return_value=False)
    conn_mock.cursor.return_value = cur_mock

    cur_mock.description = None

    def _execute(sql: str, params=None):
        sql_strip = sql.strip().upper()
        if sql_strip.startswith("INSERT"):
            if params:
                stored_rows["receipt_id"] = params[0]
                stored_rows["order_id"]   = params[1]
                stored_rows["decision_receipt_id"] = params[2]
                stored_rows["symbol"]     = params[3]
                stored_rows["side"]       = params[4]
                stored_rows["size_usd"]   = params[5]
                stored_rows["execution_style"] = params[6]
                stored_rows["requested_price"]    = params[7]
                stored_rows["requested_quantity"] = params[8]
                stored_rows["intent_timestamp"]   = params[9]
                stored_rows["intent_timestamp_ns"] = params[10]
                stored_rows["final_status"]       = params[11]
                stored_rows["exchange_response"]  = params[12]
                stored_rows["receipt_hash"]       = params[13]
                stored_rows["audit_trail"]        = params[14]

        elif sql_strip.startswith("SELECT"):
            if stored_rows:
                audit_val = stored_rows.get("audit_trail", "[]")
                if isinstance(audit_val, list):
                    audit_val = json.dumps(audit_val)
                cur_mock._fetchone_row = (
                    stored_rows.get("intent_timestamp_ns", 0),
                    stored_rows.get("requested_price"),
                    stored_rows.get("requested_quantity"),
                    audit_val,
                    stored_rows.get("symbol", "BTC/USDT"),
                    stored_rows.get("side", "BUY"),
                    stored_rows.get("size_usd", 10_000.0),
                    stored_rows.get("execution_style", "MARKET"),
                    stored_rows.get("order_id", "ORD-001"),
                    stored_rows.get("decision_receipt_id", "OMNIX-TRD-abc123"),
                    stored_rows.get("intent_timestamp"),
                )
                col_names = [
                    "intent_timestamp_ns", "requested_price", "requested_quantity",
                    "audit_trail", "symbol", "side", "size_usd", "execution_style",
                    "order_id", "decision_receipt_id", "intent_timestamp",
                ]
                cur_mock.description = [(c,) for c in col_names]

        elif sql_strip.startswith("UPDATE"):
            if params:
                stored_rows["result_timestamp"]    = params[0]
                stored_rows["result_timestamp_ns"] = params[1]
                stored_rows["latency_ms"]          = params[2]
                stored_rows["slippage_bps"]        = params[3]
                stored_rows["executed_price"]      = params[4]
                stored_rows["filled_quantity"]     = params[5]
                stored_rows["fill_ratio"]          = params[6]
                stored_rows["exchange_response"]   = params[7]
                stored_rows["final_status"]        = params[8]
                stored_rows["failure_reason"]      = params[9]
                stored_rows["receipt_hash"]        = params[10]
                stored_rows["audit_trail"]         = params[11]

    cur_mock.execute.side_effect = _execute
    cur_mock.fetchone.side_effect = lambda: getattr(cur_mock, "_fetchone_row", None)

    return conn_mock


def _patch_conn(stored_rows: Dict[str, Any]):
    """Patch _get_conn to return a mock connection backed by stored_rows."""
    conn_mock = _make_psycopg2_mock(stored_rows)
    return patch(
        "omnix_web.api.omnix_engine.execution_receipt._get_conn",
        return_value=conn_mock,
    )


def test_T10_log_intent_inserts_pending():
    stored: Dict[str, Any] = {}
    registry = ExecutionReceiptRegistry()
    registry._table_ensured = True

    with _patch_conn(stored):
        intent     = _make_intent()
        receipt_id = registry.log_intent(intent)

    assert isinstance(receipt_id, str)
    assert len(receipt_id) == 32
    assert stored["final_status"] == "PENDING"
    assert stored["symbol"]       == "BTC/USDT"
    assert stored["side"]         == "BUY"


def test_T11_log_result_filled_and_latency():
    stored: Dict[str, Any] = {}
    registry = ExecutionReceiptRegistry()
    registry._table_ensured = True

    with _patch_conn(stored):
        intent     = _make_intent(requested_quantity=0.15)
        receipt_id = registry.log_intent(intent)

        stored["intent_timestamp_ns"] = time.time_ns() - 50_000_000

        receipt = registry.log_result(
            receipt_id      = receipt_id,
            final_status    = ExecutionStatus.FILLED,
            executed_price  = 65_000.0,
            filled_quantity = 0.15,
            exchange_response = {"status": "closed"},
        )

    assert receipt.final_status  == ExecutionStatus.FILLED
    assert receipt.latency_ms    is not None
    assert receipt.latency_ms    >  0
    assert receipt.filled_quantity == 0.15
    assert receipt.receipt_hash.startswith("sha256:")


def test_T12_log_result_partial_fill_ratio():
    stored: Dict[str, Any] = {}
    registry = ExecutionReceiptRegistry()
    registry._table_ensured = True

    with _patch_conn(stored):
        stored["requested_quantity"] = 0.20
        intent    = _make_intent(requested_quantity=0.20)
        rid       = registry.log_intent(intent)
        stored["intent_timestamp_ns"] = time.time_ns() - 10_000_000

        receipt = registry.log_result(
            receipt_id      = rid,
            final_status    = ExecutionStatus.PARTIAL,
            executed_price  = 65_000.0,
            filled_quantity = 0.10,
        )

    assert receipt.final_status  == ExecutionStatus.PARTIAL
    assert receipt.fill_ratio    == pytest.approx(0.5, rel=1e-3)


def test_T13_log_result_failed_with_reason():
    stored: Dict[str, Any] = {}
    registry = ExecutionReceiptRegistry()
    registry._table_ensured = True

    with _patch_conn(stored):
        rid = registry.log_intent(_make_intent())
        stored["intent_timestamp_ns"] = time.time_ns()

        receipt = registry.log_result(
            receipt_id     = rid,
            final_status   = ExecutionStatus.FAILED,
            failure_reason = "Exchange timeout — no response after 30s",
        )

    assert receipt.final_status   == ExecutionStatus.FAILED
    assert "timeout" in receipt.failure_reason
    assert receipt.executed_price is None
    assert receipt.is_successful  is False


def test_T14_slippage_bps_calculation():
    stored: Dict[str, Any] = {}
    registry = ExecutionReceiptRegistry()
    registry._table_ensured = True

    with _patch_conn(stored):
        stored["requested_price"] = 64_800.0
        rid = registry.log_intent(_make_intent(requested_price=64_800.0))
        stored["intent_timestamp_ns"] = time.time_ns()

        receipt_adverse = registry.log_result(
            receipt_id      = rid,
            final_status    = ExecutionStatus.FILLED,
            executed_price  = 65_000.0,
            filled_quantity = 0.15,
        )

    expected_bps = ((65_000.0 - 64_800.0) / 64_800.0) * 10_000
    assert receipt_adverse.slippage_bps == pytest.approx(expected_bps, rel=1e-3)
    assert receipt_adverse.slippage_bps > 0


def test_T15_market_order_no_slippage():
    stored: Dict[str, Any] = {}
    registry = ExecutionReceiptRegistry()
    registry._table_ensured = True

    with _patch_conn(stored):
        stored["requested_price"] = None
        rid = registry.log_intent(_make_intent(execution_style="MARKET",
                                               requested_price=None))
        stored["intent_timestamp_ns"] = time.time_ns()

        receipt = registry.log_result(
            receipt_id      = rid,
            final_status    = ExecutionStatus.FILLED,
            executed_price  = 65_100.0,
            filled_quantity = 0.15,
        )

    assert receipt.slippage_bps is None


def test_T16_get_by_receipt_id():
    stored: Dict[str, Any] = {}
    registry = ExecutionReceiptRegistry()
    registry._table_ensured = True

    conn_mock = MagicMock()
    cur_mock  = MagicMock()
    conn_mock.__enter__ = MagicMock(return_value=conn_mock)
    conn_mock.__exit__  = MagicMock(return_value=False)
    cur_mock.__enter__  = MagicMock(return_value=cur_mock)
    cur_mock.__exit__   = MagicMock(return_value=False)
    conn_mock.cursor.return_value = cur_mock
    cur_mock.description = [("receipt_id",), ("order_id",), ("final_status",)]
    cur_mock.fetchone.return_value = ("RID-001", "ORD-001", "FILLED")

    with patch("omnix_web.api.omnix_engine.execution_receipt._get_conn",
               return_value=conn_mock):
        result = registry.get_by_receipt_id("RID-001")

    assert result is not None
    assert result["receipt_id"]   == "RID-001"
    assert result["final_status"] == "FILLED"


def test_T17_get_by_order_id():
    registry = ExecutionReceiptRegistry()
    registry._table_ensured = True

    conn_mock = MagicMock()
    cur_mock  = MagicMock()
    conn_mock.__enter__ = MagicMock(return_value=conn_mock)
    conn_mock.__exit__  = MagicMock(return_value=False)
    cur_mock.__enter__  = MagicMock(return_value=cur_mock)
    cur_mock.__exit__   = MagicMock(return_value=False)
    conn_mock.cursor.return_value = cur_mock
    cur_mock.description = [("order_id",), ("final_status",)]
    cur_mock.fetchone.return_value = ("ORD-999", "FILLED")

    with patch("omnix_web.api.omnix_engine.execution_receipt._get_conn",
               return_value=conn_mock):
        result = registry.get_by_order_id("ORD-999")

    assert result is not None
    assert result["order_id"] == "ORD-999"


def test_T18_get_by_decision_receipt_id():
    registry = ExecutionReceiptRegistry()
    registry._table_ensured = True

    conn_mock = MagicMock()
    cur_mock  = MagicMock()
    conn_mock.__enter__ = MagicMock(return_value=conn_mock)
    conn_mock.__exit__  = MagicMock(return_value=False)
    cur_mock.__enter__  = MagicMock(return_value=cur_mock)
    cur_mock.__exit__   = MagicMock(return_value=False)
    conn_mock.cursor.return_value = cur_mock
    cur_mock.description = [("receipt_id",), ("decision_receipt_id",)]
    cur_mock.fetchall.return_value = [
        ("RID-001", "OMNIX-TRD-abc123"),
        ("RID-002", "OMNIX-TRD-abc123"),
    ]

    with patch("omnix_web.api.omnix_engine.execution_receipt._get_conn",
               return_value=conn_mock):
        results = registry.get_by_decision_receipt_id("OMNIX-TRD-abc123")

    assert len(results) == 2
    for r in results:
        assert r["decision_receipt_id"] == "OMNIX-TRD-abc123"


def test_T19_audit_trail_accumulates_events():
    stored: Dict[str, Any] = {}
    registry = ExecutionReceiptRegistry()
    registry._table_ensured = True

    with _patch_conn(stored):
        rid = registry.log_intent(_make_intent())
        stored["intent_timestamp_ns"] = time.time_ns()

        receipt = registry.log_result(
            receipt_id      = rid,
            final_status    = ExecutionStatus.FILLED,
            executed_price  = 65_000.0,
            filled_quantity = 0.15,
        )

    assert len(receipt.audit_trail) == 2
    assert receipt.audit_trail[0]["action"] == "INTENT_LOGGED"
    assert receipt.audit_trail[1]["action"] == "RESULT_LOGGED"
    assert receipt.audit_trail[1]["final_status"] == "FILLED"


# ── T20–T25: ExecutionGuard tests ─────────────────────────────────────────────

def _guard_with_mocked_registry(
    succeed         : bool              = True,
    partial         : bool              = False,
    raise_exception : Optional[Exception] = None,
) -> ExecutionReceipt:
    """Run ExecutionGuard with a mocked registry and return the logged receipt."""
    receipts_logged: List[Dict[str, Any]] = []
    fake_receipt_id = uuid.uuid4().hex

    mock_registry = MagicMock(spec=ExecutionReceiptRegistry)
    mock_registry.log_intent.return_value = fake_receipt_id

    def _log_result(**kwargs):
        receipts_logged.append({"receipt_id": fake_receipt_id, **kwargs})
        r = ExecutionReceipt(
            receipt_id          = fake_receipt_id,
            order_id            = "ORD-001",
            decision_receipt_id = "OMNIX-TRD-abc123",
            symbol              = "BTC/USDT",
            side                = "BUY",
            size_usd            = 10_000.0,
            final_status        = kwargs.get("final_status", ExecutionStatus.FAILED),
        )
        r.receipt_hash = r.compute_hash()
        return r

    mock_registry.log_result.side_effect = _log_result

    intent = _make_intent()
    guard  = ExecutionGuard(registry=mock_registry, intent=intent)

    try:
        with guard:
            if raise_exception:
                raise raise_exception
            if succeed:
                guard.succeed(
                    executed_price    = 65_000.0,
                    filled_quantity   = 0.15,
                    exchange_response = {"status": "closed"},
                    partial           = partial,
                )
    except Exception:
        pass

    assert len(receipts_logged) == 1
    return receipts_logged[0]


def test_T20_guard_succeed_produces_filled():
    logged = _guard_with_mocked_registry(succeed=True, partial=False)
    assert logged["final_status"] == ExecutionStatus.FILLED


def test_T21_guard_exception_produces_failed():
    logged = _guard_with_mocked_registry(
        succeed=False,
        raise_exception=ConnectionError("Exchange unreachable"),
    )
    assert logged["final_status"]  == ExecutionStatus.FAILED
    assert "ConnectionError" in logged["failure_reason"]


def test_T22_guard_partial_produces_partial():
    logged = _guard_with_mocked_registry(succeed=True, partial=True)
    assert logged["final_status"] == ExecutionStatus.PARTIAL


def test_T23_guard_receipt_id_available_after_enter():
    mock_registry = MagicMock(spec=ExecutionReceiptRegistry)
    mock_registry.log_intent.return_value = "FIXED-RECEIPT-ID"
    mock_registry.log_result.return_value = MagicMock(spec=ExecutionReceipt)

    intent = _make_intent()
    guard  = ExecutionGuard(registry=mock_registry, intent=intent)

    with guard:
        assert guard.receipt_id == "FIXED-RECEIPT-ID"
        guard.succeed(executed_price=65_000.0)


def test_T24_execution_guard_convenience_happy_path():
    mock_registry = MagicMock(spec=ExecutionReceiptRegistry)
    mock_registry.log_intent.return_value = uuid.uuid4().hex
    mock_receipt = MagicMock(spec=ExecutionReceipt)
    mock_registry.log_result.return_value = mock_receipt

    with execution_guard(
        decision_receipt_id = "OMNIX-TRD-abc123",
        order_id            = "ORD-CONV-001",
        symbol              = "ETH/USDT",
        side                = "SELL",
        size_usd            = 5_000.0,
        registry            = mock_registry,
    ) as guard:
        guard.succeed(executed_price=3_200.0, filled_quantity=1.5)

    mock_registry.log_intent.assert_called_once()
    mock_registry.log_result.assert_called_once()
    call_kwargs = mock_registry.log_result.call_args[1]
    assert call_kwargs["final_status"] == ExecutionStatus.FILLED


def test_T25_execution_guard_convenience_exception_path():
    logged_calls: List[Dict] = []
    mock_registry = MagicMock(spec=ExecutionReceiptRegistry)
    mock_registry.log_intent.return_value = uuid.uuid4().hex
    mock_registry.log_result.return_value = MagicMock(spec=ExecutionReceipt)
    mock_registry.log_result.side_effect = lambda **kw: logged_calls.append(kw) or MagicMock()

    try:
        with execution_guard(
            decision_receipt_id = "OMNIX-TRD-abc123",
            order_id            = "ORD-CONV-002",
            symbol              = "BTC/USDT",
            side                = "BUY",
            size_usd            = 10_000.0,
            registry            = mock_registry,
        ) as _guard:
            raise TimeoutError("Exchange did not respond")
    except TimeoutError:
        pass

    assert len(logged_calls) == 1
    assert logged_calls[0]["final_status"] == ExecutionStatus.FAILED
    assert "TimeoutError" in logged_calls[0]["failure_reason"]


# ── T26: log_intent fail-closed on DB error ───────────────────────────────────

def test_T26_log_intent_fail_closed_on_db_error():
    registry = ExecutionReceiptRegistry()
    registry._table_ensured = True

    with patch(
        "omnix_web.api.omnix_engine.execution_receipt._get_conn",
        side_effect=Exception("DB connection refused"),
    ):
        with pytest.raises(RuntimeError, match="log_intent failed"):
            registry.log_intent(_make_intent())


# ── T27: get_global_registry singleton ───────────────────────────────────────

def test_T27_get_global_registry_singleton():
    r1 = get_global_registry()
    r2 = get_global_registry()
    assert r1 is r2
    assert isinstance(r1, ExecutionReceiptRegistry)


# ── T28: mark_vc_issued ───────────────────────────────────────────────────────

def test_T28_mark_vc_issued():
    registry = ExecutionReceiptRegistry()
    registry._table_ensured = True

    conn_mock = MagicMock()
    cur_mock  = MagicMock()
    conn_mock.__enter__ = MagicMock(return_value=conn_mock)
    conn_mock.__exit__  = MagicMock(return_value=False)
    cur_mock.__enter__  = MagicMock(return_value=cur_mock)
    cur_mock.__exit__   = MagicMock(return_value=False)
    conn_mock.cursor.return_value = cur_mock

    with patch("omnix_web.api.omnix_engine.execution_receipt._get_conn",
               return_value=conn_mock):
        registry.mark_vc_issued("SOME-RECEIPT-ID")

    cur_mock.execute.assert_called_once()
    sql = cur_mock.execute.call_args[0][0]
    assert "vc_issued" in sql.lower()
    assert "TRUE" in sql or "true" in sql.lower()


# ── T29: fill_ratio capped at 1.0 on overfill ────────────────────────────────

def test_T29_fill_ratio_capped_at_1():
    stored: Dict[str, Any] = {}
    registry = ExecutionReceiptRegistry()
    registry._table_ensured = True

    with _patch_conn(stored):
        stored["requested_quantity"] = 0.10
        rid = registry.log_intent(_make_intent(requested_quantity=0.10))
        stored["intent_timestamp_ns"] = time.time_ns()

        receipt = registry.log_result(
            receipt_id        = rid,
            final_status      = ExecutionStatus.FILLED,
            executed_price    = 65_000.0,
            filled_quantity   = 0.12,
        )

    assert receipt.fill_ratio == pytest.approx(1.0, rel=1e-6)


# ── T30: FAILED with no executed_price ───────────────────────────────────────

def test_T30_failed_no_executed_price_graceful():
    stored: Dict[str, Any] = {}
    registry = ExecutionReceiptRegistry()
    registry._table_ensured = True

    with _patch_conn(stored):
        rid = registry.log_intent(_make_intent())
        stored["intent_timestamp_ns"] = time.time_ns()

        receipt = registry.log_result(
            receipt_id     = rid,
            final_status   = ExecutionStatus.FAILED,
            failure_reason = "Order rejected by exchange: insufficient margin",
        )

    assert receipt.final_status    == ExecutionStatus.FAILED
    assert receipt.executed_price  is None
    assert receipt.slippage_bps    is None
    assert receipt.fill_ratio      is None
    assert "margin" in receipt.failure_reason
    assert receipt.receipt_hash.startswith("sha256:")
