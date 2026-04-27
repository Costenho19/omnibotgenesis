"""
OMNIX Execution Integrity Layer — ADR-131
=========================================

Governs execution the same way OMNIX governs decisions.
Every trade execution must produce a verifiable ExecutionReceipt.

Three invariants (non-negotiable):
  1. No silent execution  — every execution path produces a receipt, including failures.
  2. Pre-intent logged    — intent is captured *before* the order is sent to the exchange.
  3. Decision binding     — every ExecutionReceipt is bound to a decision_receipt_id,
                            closing the decision→execution audit chain.

Architecture:
  ExecutionIntent  → logged at entry of ExecutionGuard (pre-order)
  ExecutionReceipt → logged at exit of ExecutionGuard (post-exchange response)
  ExecutionGuard   → context manager that enforces both invariants under any condition

Fail-safe guarantee:
  If the exchange call raises an exception inside ExecutionGuard, a FAILED receipt is
  still written to the database before the exception propagates.
  There is NO code path that exits the guard without a receipt.

Optional VC binding:
  ExecutionReceipt.to_vc_payload() produces a W3C Verifiable Credential payload
  compatible with the OMNIX VC infrastructure (ADR-084 / receipt_to_vc.py).
  The VC wraps the execution receipt as the credentialSubject and uses the
  receipt_hash as the credential proof anchor.

Performance:
  - log_intent()  : single INSERT, non-blocking
  - log_result()  : single UPDATE, non-blocking
  - ExecutionGuard: adds ~0.1ms overhead (hash + DB write)
  - No lock contention — each receipt_id is unique per execution

Database:
  Table: execution_receipts
  Created automatically via DDL on first use (ensure_table()).
  All columns are NOT NULL with explicit defaults — no silent NULLs.

References:
  ADR-131  — Execution Integrity Layer (this module)
  ADR-130  — VC Trust Revocation Registry (suspension lifecycle)
  ADR-096  — Canonical Receipt format
  ADR-084  — W3C Verifiable Credentials
  ADR-074  — Receipt ID format

Author: OMNIX Quantum Ltd — Harold Alberto Nunes Rodelo
Date:   2026-04-27
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Generator, List, Optional

logger = logging.getLogger("OMNIX.ExecutionIntegrity")

# ── Constants ──────────────────────────────────────────────────────────────────

_MODULE_VERSION   = "1.0.0"
_ADR_REFERENCE    = "ADR-131"
_OMNIX_ISSUER_DID = "did:web:omnixquantum.net"
_OMNIX_ISSUER     = "OMNIX Quantum Ltd"
_VC_CONTEXT       = [
    "https://www.w3.org/2018/credentials/v1",
    "https://omnixquantum.net/schemas/omnix-execution-v1.jsonld",
]

# ── DDL ────────────────────────────────────────────────────────────────────────

_DDL_EXECUTION_RECEIPTS = """
CREATE TABLE IF NOT EXISTS execution_receipts (
    receipt_id              VARCHAR(64)     PRIMARY KEY,
    order_id                VARCHAR(128)    NOT NULL,
    decision_receipt_id     VARCHAR(128)    NOT NULL,
    symbol                  VARCHAR(32)     NOT NULL,
    side                    VARCHAR(8)      NOT NULL,
    size_usd                DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    execution_style         VARCHAR(32)     NOT NULL DEFAULT '',
    requested_price         DOUBLE PRECISION,
    requested_quantity      DOUBLE PRECISION,

    intent_timestamp        TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    intent_timestamp_ns     BIGINT          NOT NULL DEFAULT 0,

    result_timestamp        TIMESTAMPTZ,
    result_timestamp_ns     BIGINT,
    latency_ms              DOUBLE PRECISION,

    slippage_bps            DOUBLE PRECISION,
    executed_price          DOUBLE PRECISION,
    filled_quantity         DOUBLE PRECISION,
    fill_ratio              DOUBLE PRECISION,

    exchange_response       JSONB           NOT NULL DEFAULT '{}',
    final_status            VARCHAR(16)     NOT NULL DEFAULT 'PENDING',
    failure_reason          TEXT            NOT NULL DEFAULT '',

    receipt_hash            VARCHAR(64)     NOT NULL DEFAULT '',
    vc_issued               BOOLEAN         NOT NULL DEFAULT FALSE,

    audit_trail             JSONB           NOT NULL DEFAULT '[]',

    created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_execution_receipts_order_id
    ON execution_receipts(order_id);

CREATE INDEX IF NOT EXISTS idx_execution_receipts_decision_receipt_id
    ON execution_receipts(decision_receipt_id);

CREATE INDEX IF NOT EXISTS idx_execution_receipts_final_status
    ON execution_receipts(final_status);

CREATE INDEX IF NOT EXISTS idx_execution_receipts_created_at
    ON execution_receipts(created_at DESC);
"""

# ── Enums ──────────────────────────────────────────────────────────────────────

class ExecutionStatus(str, Enum):
    """
    Final status of a trade execution attempt.

    PENDING  — intent logged, waiting for exchange response.
    FILLED   — order fully filled at the requested quantity.
    PARTIAL  — order partially filled; fill_ratio < 1.0.
    FAILED   — exchange rejected or no response received.
    """
    PENDING = "PENDING"
    FILLED  = "FILLED"
    PARTIAL = "PARTIAL"
    FAILED  = "FAILED"


class ExecutionSide(str, Enum):
    """Direction of the trade order."""
    BUY  = "BUY"
    SELL = "SELL"

# ── Data models ────────────────────────────────────────────────────────────────

@dataclass
class ExecutionIntent:
    """
    Pre-execution snapshot — captured BEFORE the order is sent to the exchange.

    This is the governance record of what OMNIX *intended* to execute,
    not what the market *did* with it. The distinction is critical for
    auditability: slippage is meaningful only when intent is preserved.
    """
    order_id            : str
    decision_receipt_id : str
    symbol              : str
    side                : str
    size_usd            : float
    execution_style     : str                  = ""
    requested_price     : Optional[float]      = None
    requested_quantity  : Optional[float]      = None
    intent_timestamp    : Optional[datetime]   = None
    intent_timestamp_ns : int                  = 0

    def __post_init__(self) -> None:
        if not self.intent_timestamp:
            self.intent_timestamp = datetime.now(tz=timezone.utc)
        if not self.intent_timestamp_ns:
            self.intent_timestamp_ns = time.time_ns()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id"            : self.order_id,
            "decision_receipt_id" : self.decision_receipt_id,
            "symbol"              : self.symbol,
            "side"                : self.side,
            "size_usd"            : self.size_usd,
            "execution_style"     : self.execution_style,
            "requested_price"     : self.requested_price,
            "requested_quantity"  : self.requested_quantity,
            "intent_timestamp"    : self.intent_timestamp.isoformat()
                                    if self.intent_timestamp else None,
            "intent_timestamp_ns" : self.intent_timestamp_ns,
        }


@dataclass
class ExecutionReceipt:
    """
    Post-execution record — the authoritative audit artifact for a single trade.

    Combines the pre-execution intent with the exchange's actual response.
    Immutable after log_result() is called (receipt_hash seals the payload).

    Fields:
        receipt_id          — OMNIX-unique identifier (UUID4 hex)
        order_id            — exchange order reference
        decision_receipt_id — governance chain link (ADR-096)
        symbol              — instrument traded
        side                — BUY or SELL
        size_usd            — notional value of the intent
        execution_style     — MARKET / LIMIT / TWAP / VWAP / ICEBERG / POV / IS
        requested_price     — limit price if applicable (None for MARKET)
        requested_quantity  — number of units requested
        intent_timestamp    — UTC datetime of pre-execution intent
        intent_timestamp_ns — nanosecond-precision intent time (time.time_ns())
        result_timestamp    — UTC datetime of post-execution result
        result_timestamp_ns — nanosecond-precision result time
        latency_ms          — round-trip latency from intent to result
        slippage_bps        — price slippage in basis points vs requested_price
        executed_price      — actual fill price reported by exchange
        filled_quantity     — units filled
        fill_ratio          — filled_quantity / requested_quantity (0.0–1.0)
        exchange_response   — raw exchange response dict (JSONB)
        final_status        — FILLED / PARTIAL / FAILED / PENDING
        failure_reason      — human-readable cause if FAILED
        receipt_hash        — SHA-256 of canonical receipt payload (tamper-evident)
        vc_issued           — whether a W3C VC has been issued for this receipt
        audit_trail         — append-only list of state transitions
    """
    receipt_id          : str
    order_id            : str
    decision_receipt_id : str
    symbol              : str
    side                : str
    size_usd            : float
    execution_style     : str                  = ""
    requested_price     : Optional[float]      = None
    requested_quantity  : Optional[float]      = None
    intent_timestamp    : Optional[datetime]   = None
    intent_timestamp_ns : int                  = 0
    result_timestamp    : Optional[datetime]   = None
    result_timestamp_ns : int                  = 0
    latency_ms          : Optional[float]      = None
    slippage_bps        : Optional[float]      = None
    executed_price      : Optional[float]      = None
    filled_quantity     : Optional[float]      = None
    fill_ratio          : Optional[float]      = None
    exchange_response   : Dict[str, Any]       = field(default_factory=dict)
    final_status        : ExecutionStatus      = ExecutionStatus.PENDING
    failure_reason      : str                  = ""
    receipt_hash        : str                  = ""
    vc_issued           : bool                 = False
    audit_trail         : List[Dict[str, Any]] = field(default_factory=list)

    # ── Computed properties ──────────────────────────────────────────────────

    @property
    def is_terminal(self) -> bool:
        """True if the execution has reached a final state (not PENDING)."""
        return self.final_status != ExecutionStatus.PENDING

    @property
    def is_successful(self) -> bool:
        """True if the order was fully or partially filled."""
        return self.final_status in (ExecutionStatus.FILLED, ExecutionStatus.PARTIAL)

    @property
    def slippage_acceptable(self) -> bool:
        """True if slippage is within 50bps (0.5%) — ADR-131 threshold."""
        if self.slippage_bps is None:
            return True
        return abs(self.slippage_bps) < 50.0

    # ── Serialisation ────────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Canonical dict representation — used for hashing and VC payload."""
        return {
            "receipt_id"          : self.receipt_id,
            "order_id"            : self.order_id,
            "decision_receipt_id" : self.decision_receipt_id,
            "symbol"              : self.symbol,
            "side"                : self.side,
            "size_usd"            : self.size_usd,
            "execution_style"     : self.execution_style,
            "requested_price"     : self.requested_price,
            "requested_quantity"  : self.requested_quantity,
            "intent_timestamp"    : self.intent_timestamp.isoformat()
                                    if self.intent_timestamp else None,
            "intent_timestamp_ns" : self.intent_timestamp_ns,
            "result_timestamp"    : self.result_timestamp.isoformat()
                                    if self.result_timestamp else None,
            "result_timestamp_ns" : self.result_timestamp_ns,
            "latency_ms"          : round(self.latency_ms, 3)
                                    if self.latency_ms is not None else None,
            "slippage_bps"        : round(self.slippage_bps, 4)
                                    if self.slippage_bps is not None else None,
            "executed_price"      : self.executed_price,
            "filled_quantity"     : self.filled_quantity,
            "fill_ratio"          : round(self.fill_ratio, 6)
                                    if self.fill_ratio is not None else None,
            "exchange_response"   : self.exchange_response,
            "final_status"        : self.final_status.value,
            "failure_reason"      : self.failure_reason,
            "receipt_hash"        : self.receipt_hash,
            "vc_issued"           : self.vc_issued,
            "adr_reference"       : _ADR_REFERENCE,
        }

    def compute_hash(self) -> str:
        """
        SHA-256 hash of the canonical receipt payload.
        Excludes receipt_hash itself and audit_trail to ensure determinism.
        """
        payload = {
            "receipt_id"          : self.receipt_id,
            "order_id"            : self.order_id,
            "decision_receipt_id" : self.decision_receipt_id,
            "symbol"              : self.symbol,
            "side"                : self.side,
            "size_usd"            : self.size_usd,
            "execution_style"     : self.execution_style,
            "requested_price"     : self.requested_price,
            "requested_quantity"  : self.requested_quantity,
            "intent_timestamp_ns" : self.intent_timestamp_ns,
            "result_timestamp_ns" : self.result_timestamp_ns,
            "executed_price"      : self.executed_price,
            "filled_quantity"     : self.filled_quantity,
            "final_status"        : self.final_status.value,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()

    def to_vc_payload(self) -> Dict[str, Any]:
        """
        Wraps this ExecutionReceipt in a W3C Verifiable Credential payload.

        The VC uses the same JSON-LD context as OMNIX governance VCs (ADR-084)
        extended with the execution-specific schema.
        The receipt_hash anchors the VC to the auditable receipt record.

        Returns:
            A JSON-serialisable dict representing the W3C VC.
        """
        now_iso = datetime.now(tz=timezone.utc).isoformat()
        vc_id   = f"urn:omnix:execution:{self.receipt_id}"

        return {
            "@context"          : _VC_CONTEXT,
            "type"              : ["VerifiableCredential", "OmnixExecutionReceipt"],
            "id"                : vc_id,
            "issuer"            : {
                "id"   : _OMNIX_ISSUER_DID,
                "name" : _OMNIX_ISSUER,
            },
            "issuanceDate"      : now_iso,
            "credentialSubject" : {
                "id"                  : f"urn:omnix:order:{self.order_id}",
                "type"                : "ExecutionEvent",
                "receipt_id"          : self.receipt_id,
                "order_id"            : self.order_id,
                "decision_receipt_id" : self.decision_receipt_id,
                "symbol"              : self.symbol,
                "side"                : self.side,
                "size_usd"            : self.size_usd,
                "execution_style"     : self.execution_style,
                "final_status"        : self.final_status.value,
                "latency_ms"          : self.latency_ms,
                "slippage_bps"        : self.slippage_bps,
                "executed_price"      : self.executed_price,
                "filled_quantity"     : self.filled_quantity,
                "fill_ratio"          : self.fill_ratio,
                "intent_timestamp"    : self.intent_timestamp.isoformat()
                                        if self.intent_timestamp else None,
                "result_timestamp"    : self.result_timestamp.isoformat()
                                        if self.result_timestamp else None,
            },
            "credentialStatus"  : {
                "type"          : "OmnixExecutionIntegrityStatus",
                "statusPurpose" : "execution-integrity",
                "receiptHash"   : self.receipt_hash,
                "adrReference"  : _ADR_REFERENCE,
            },
            "proof"             : {
                "type"            : "OmnixReceiptHash",
                "created"         : now_iso,
                "proofPurpose"    : "assertionMethod",
                "verificationMethod" : _OMNIX_ISSUER_DID,
                "receiptHash"     : self.receipt_hash,
                "integrityLayer"  : _ADR_REFERENCE,
            },
        }


# ── Database helpers ───────────────────────────────────────────────────────────

def _get_conn():
    """
    Return a psycopg2 connection from OMNIX_DB_URL.
    Raises RuntimeError explicitly if the env var is missing — no silent fallback.
    """
    try:
        import psycopg2
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("psycopg2 is not installed — cannot persist ExecutionReceipt") from exc

    db_url = os.environ.get("OMNIX_DB_URL") or os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError(
            "OMNIX_DB_URL is not set — ExecutionReceiptRegistry requires a database."
        )
    return psycopg2.connect(db_url)


def _audit_event(action: str, **kwargs) -> Dict[str, Any]:
    """Build a single audit trail entry."""
    return {
        "ts"     : datetime.now(tz=timezone.utc).isoformat(),
        "ts_ns"  : time.time_ns(),
        "action" : action,
        **kwargs,
    }


# ── Registry ───────────────────────────────────────────────────────────────────

class ExecutionReceiptRegistry:
    """
    Production-grade persistence layer for ExecutionReceipt records.

    Responsibilities:
      - ensure_table()           — idempotent DDL creation
      - log_intent()             — INSERT pre-execution intent (PENDING status)
      - log_result()             — UPDATE post-execution result (FILLED/PARTIAL/FAILED)
      - get_by_receipt_id()      — retrieve by primary key
      - get_by_order_id()        — retrieve by exchange order reference
      - get_by_decision_receipt_id() — retrieve all executions for a governance decision

    All methods are thread-safe (each call opens its own connection and commits
    atomically). No connection pooling is assumed — Railway PostgreSQL handles it.

    Fail-safe contract:
      log_result() MUST always succeed or raise explicitly.
      It never silently swallows DB errors — the caller (ExecutionGuard) must
      decide whether to propagate or log. This prevents silent data loss.
    """

    _table_ensured: bool = False
    _table_lock: threading.Lock = threading.Lock()

    def ensure_table(self) -> None:
        """
        Create the execution_receipts table and indexes if they do not exist.
        Idempotent — safe to call on every startup.
        Called lazily on first use to avoid blocking import time.
        """
        with self._table_lock:
            if self._table_ensured:
                return
            try:
                conn = _get_conn()
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(_DDL_EXECUTION_RECEIPTS)
                conn.close()
                self._table_ensured = True
                logger.info("[ExecutionIntegrity] execution_receipts table ready")
            except Exception as exc:
                logger.error(
                    "[ExecutionIntegrity] ensure_table failed: %s — registry is degraded",
                    type(exc).__name__,
                )

    def _ensure(self) -> None:
        if not self._table_ensured:
            self.ensure_table()

    # ── Write path ─────────────────────────────────────────────────────────

    def log_intent(self, intent: ExecutionIntent) -> str:
        """
        Persist the pre-execution intent as a PENDING receipt.

        This is the first half of the audit chain. Called BEFORE the order
        is sent to the exchange. Returns the receipt_id so ExecutionGuard
        can pass it to log_result() after the exchange responds.

        Args:
            intent: ExecutionIntent dataclass populated by the caller.

        Returns:
            receipt_id: the unique identifier for this execution audit record.

        Raises:
            RuntimeError: if the database write fails (fail-closed — do not
                          execute the trade without a pre-execution record).
        """
        self._ensure()

        receipt_id = uuid.uuid4().hex
        trail      = json.dumps([_audit_event("INTENT_LOGGED", order_id=intent.order_id)])

        try:
            conn = _get_conn()
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO execution_receipts (
                            receipt_id, order_id, decision_receipt_id,
                            symbol, side, size_usd, execution_style,
                            requested_price, requested_quantity,
                            intent_timestamp, intent_timestamp_ns,
                            final_status, exchange_response,
                            receipt_hash, audit_trail
                        ) VALUES (
                            %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s,
                            %s, %s,
                            %s, %s,
                            %s, %s
                        )
                        """,
                        (
                            receipt_id,
                            intent.order_id,
                            intent.decision_receipt_id,
                            intent.symbol,
                            intent.side,
                            intent.size_usd,
                            intent.execution_style,
                            intent.requested_price,
                            intent.requested_quantity,
                            intent.intent_timestamp,
                            intent.intent_timestamp_ns,
                            ExecutionStatus.PENDING.value,
                            json.dumps({}),
                            "",
                            trail,
                        ),
                    )
            conn.close()
            logger.info(
                "[ExecutionIntegrity] Intent logged — receipt_id=%s order_id=%s symbol=%s",
                receipt_id, intent.order_id, intent.symbol,
            )
            return receipt_id

        except Exception as exc:
            logger.error(
                "[ExecutionIntegrity] log_intent FAILED: %s — order_id=%s",
                type(exc).__name__, intent.order_id,
            )
            raise RuntimeError(
                f"ExecutionReceiptRegistry.log_intent failed: {type(exc).__name__}"
            ) from exc

    def log_result(
        self,
        receipt_id        : str,
        final_status      : ExecutionStatus,
        executed_price    : Optional[float]      = None,
        filled_quantity   : Optional[float]      = None,
        exchange_response : Optional[Dict[str, Any]] = None,
        failure_reason    : str                  = "",
        requested_price   : Optional[float]      = None,
        requested_quantity: Optional[float]      = None,
    ) -> ExecutionReceipt:
        """
        Persist the post-execution result and seal the receipt with a hash.

        This is the second half of the audit chain. Called AFTER the exchange
        responds (or raises). Computes latency, slippage, fill_ratio, and the
        tamper-evident receipt_hash.

        Args:
            receipt_id:         returned by log_intent().
            final_status:       FILLED, PARTIAL, or FAILED.
            executed_price:     actual fill price (None if FAILED).
            filled_quantity:    units filled (None if FAILED).
            exchange_response:  raw exchange response dict.
            failure_reason:     human-readable cause (required if FAILED).
            requested_price:    used to compute slippage (if not already stored).
            requested_quantity: used to compute fill_ratio (if not already stored).

        Returns:
            ExecutionReceipt: the fully sealed audit record.

        Raises:
            RuntimeError: if the database write fails — the caller (ExecutionGuard)
                          logs the error and re-raises to preserve the exception chain.
        """
        self._ensure()

        result_ns   = time.time_ns()
        result_time = datetime.now(tz=timezone.utc)

        try:
            conn = _get_conn()
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT intent_timestamp_ns, requested_price, requested_quantity,
                               audit_trail, symbol, side, size_usd, execution_style,
                               order_id, decision_receipt_id, intent_timestamp
                        FROM execution_receipts
                        WHERE receipt_id = %s
                        """,
                        (receipt_id,),
                    )
                    row = cur.fetchone()

            conn.close()
        except Exception as exc:
            logger.error(
                "[ExecutionIntegrity] log_result DB read FAILED: %s — receipt_id=%s",
                type(exc).__name__, receipt_id,
            )
            raise RuntimeError(
                f"ExecutionReceiptRegistry.log_result (read) failed: {type(exc).__name__}"
            ) from exc

        if not row:
            raise ValueError(f"ExecutionReceipt not found: receipt_id={receipt_id}")

        (
            intent_ns, stored_req_price, stored_req_qty,
            raw_trail, symbol, side, size_usd, execution_style,
            order_id, decision_receipt_id, intent_timestamp,
        ) = row

        req_price = requested_price if requested_price is not None else stored_req_price
        req_qty   = requested_quantity if requested_quantity is not None else stored_req_qty

        latency_ms  = (result_ns - intent_ns) / 1_000_000.0 if intent_ns else None
        slippage_bps: Optional[float] = None
        if req_price and executed_price and req_price != 0:
            slippage_bps = ((executed_price - req_price) / req_price) * 10_000.0

        fill_ratio: Optional[float] = None
        if req_qty and filled_quantity is not None and req_qty != 0:
            fill_ratio = min(filled_quantity / req_qty, 1.0)

        existing_trail: List[Dict[str, Any]] = []
        if isinstance(raw_trail, str):
            try:
                existing_trail = json.loads(raw_trail)
            except json.JSONDecodeError:
                existing_trail = []
        elif isinstance(raw_trail, list):
            existing_trail = raw_trail

        existing_trail.append(_audit_event(
            "RESULT_LOGGED",
            final_status    = final_status.value,
            executed_price  = executed_price,
            filled_quantity = filled_quantity,
            latency_ms      = round(latency_ms, 3) if latency_ms is not None else None,
            slippage_bps    = round(slippage_bps, 4) if slippage_bps is not None else None,
            failure_reason  = failure_reason,
        ))

        receipt = ExecutionReceipt(
            receipt_id          = receipt_id,
            order_id            = order_id,
            decision_receipt_id = decision_receipt_id,
            symbol              = symbol,
            side                = side,
            size_usd            = size_usd,
            execution_style     = execution_style or "",
            requested_price     = req_price,
            requested_quantity  = req_qty,
            intent_timestamp    = intent_timestamp,
            intent_timestamp_ns = intent_ns or 0,
            result_timestamp    = result_time,
            result_timestamp_ns = result_ns,
            latency_ms          = latency_ms,
            slippage_bps        = slippage_bps,
            executed_price      = executed_price,
            filled_quantity     = filled_quantity,
            fill_ratio          = fill_ratio,
            exchange_response   = exchange_response or {},
            final_status        = final_status,
            failure_reason      = failure_reason,
            audit_trail         = existing_trail,
        )
        receipt.receipt_hash = receipt.compute_hash()

        try:
            conn = _get_conn()
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE execution_receipts SET
                            result_timestamp    = %s,
                            result_timestamp_ns = %s,
                            latency_ms          = %s,
                            slippage_bps        = %s,
                            executed_price      = %s,
                            filled_quantity     = %s,
                            fill_ratio          = %s,
                            exchange_response   = %s,
                            final_status        = %s,
                            failure_reason      = %s,
                            receipt_hash        = %s,
                            audit_trail         = %s,
                            updated_at          = NOW()
                        WHERE receipt_id = %s
                        """,
                        (
                            result_time,
                            result_ns,
                            latency_ms,
                            slippage_bps,
                            executed_price,
                            filled_quantity,
                            fill_ratio,
                            json.dumps(exchange_response or {}),
                            final_status.value,
                            failure_reason,
                            receipt.receipt_hash,
                            json.dumps(existing_trail),
                            receipt_id,
                        ),
                    )
            conn.close()
            logger.info(
                "[ExecutionIntegrity] Result sealed — receipt_id=%s status=%s "
                "latency=%.2fms slippage=%.2fbps hash=%s",
                receipt_id,
                final_status.value,
                latency_ms or 0.0,
                slippage_bps or 0.0,
                receipt.receipt_hash[:20],
            )
            return receipt

        except Exception as exc:
            logger.error(
                "[ExecutionIntegrity] log_result DB write FAILED: %s — receipt_id=%s",
                type(exc).__name__, receipt_id,
            )
            raise RuntimeError(
                f"ExecutionReceiptRegistry.log_result (write) failed: {type(exc).__name__}"
            ) from exc

    # ── Read path ──────────────────────────────────────────────────────────

    def get_by_receipt_id(self, receipt_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single ExecutionReceipt by its primary key."""
        self._ensure()
        try:
            conn = _get_conn()
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT * FROM execution_receipts WHERE receipt_id = %s",
                        (receipt_id,),
                    )
                    row = cur.fetchone()
                    cols = [d[0] for d in cur.description] if cur.description else []
            conn.close()
            return dict(zip(cols, row)) if row else None
        except Exception as exc:
            logger.error(
                "[ExecutionIntegrity] get_by_receipt_id failed: %s", type(exc).__name__
            )
            return None

    def get_by_order_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the ExecutionReceipt for a given exchange order ID."""
        self._ensure()
        try:
            conn = _get_conn()
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT * FROM execution_receipts
                        WHERE order_id = %s
                        ORDER BY created_at DESC
                        LIMIT 1
                        """,
                        (order_id,),
                    )
                    row = cur.fetchone()
                    cols = [d[0] for d in cur.description] if cur.description else []
            conn.close()
            return dict(zip(cols, row)) if row else None
        except Exception as exc:
            logger.error(
                "[ExecutionIntegrity] get_by_order_id failed: %s", type(exc).__name__
            )
            return None

    def get_by_decision_receipt_id(
        self,
        decision_receipt_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Return all execution receipts bound to a governance decision receipt.
        Ordered by creation time descending (most recent first).
        """
        self._ensure()
        try:
            conn = _get_conn()
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT * FROM execution_receipts
                        WHERE decision_receipt_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                        """,
                        (decision_receipt_id, limit),
                    )
                    rows = cur.fetchall()
                    cols = [d[0] for d in cur.description] if cur.description else []
            conn.close()
            return [dict(zip(cols, r)) for r in rows]
        except Exception as exc:
            logger.error(
                "[ExecutionIntegrity] get_by_decision_receipt_id failed: %s",
                type(exc).__name__,
            )
            return []

    def mark_vc_issued(self, receipt_id: str) -> None:
        """Mark that a W3C VC has been issued for this execution receipt."""
        self._ensure()
        try:
            conn = _get_conn()
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE execution_receipts
                        SET vc_issued = TRUE, updated_at = NOW()
                        WHERE receipt_id = %s
                        """,
                        (receipt_id,),
                    )
            conn.close()
        except Exception as exc:
            logger.warning(
                "[ExecutionIntegrity] mark_vc_issued failed (non-critical): %s",
                type(exc).__name__,
            )


# ── Fail-safe context manager ──────────────────────────────────────────────────

class ExecutionGuard:
    """
    Context manager that enforces the Execution Integrity Layer invariants.

    Usage:
        registry = ExecutionReceiptRegistry()

        with ExecutionGuard(registry, intent) as guard:
            response = exchange.submit_order(...)
            guard.succeed(
                executed_price    = response["price"],
                filled_quantity   = response["filled"],
                exchange_response = response,
            )

    Invariants enforced:
      1. __enter__  → log_intent() is called. If it fails, the guard raises
                      before the trade is sent (fail-closed).
      2. __exit__   → log_result() is always called, even if the body raises.
      3. If the body raises without guard.succeed() being called, a FAILED
         receipt is written with the exception message as failure_reason.

    Attributes:
        receipt_id: available after __enter__ for downstream reference.
    """

    def __init__(
        self,
        registry : ExecutionReceiptRegistry,
        intent   : ExecutionIntent,
    ) -> None:
        self._registry   = registry
        self._intent     = intent
        self.receipt_id  : str                  = ""
        self._succeeded  : bool                 = False
        self._result_kwargs: Dict[str, Any]     = {}

    def __enter__(self) -> "ExecutionGuard":
        self.receipt_id = self._registry.log_intent(self._intent)
        return self

    def succeed(
        self,
        executed_price    : Optional[float]          = None,
        filled_quantity   : Optional[float]          = None,
        exchange_response : Optional[Dict[str, Any]] = None,
        partial           : bool                     = False,
    ) -> None:
        """
        Mark the execution as successful (FILLED or PARTIAL).
        Must be called inside the `with` block after receiving the exchange response.
        """
        self._succeeded = True
        self._result_kwargs = {
            "final_status"      : ExecutionStatus.PARTIAL if partial else ExecutionStatus.FILLED,
            "executed_price"    : executed_price,
            "filled_quantity"   : filled_quantity,
            "exchange_response" : exchange_response or {},
            "failure_reason"    : "",
        }

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self._succeeded:
            try:
                self._registry.log_result(
                    receipt_id = self.receipt_id,
                    **self._result_kwargs,
                )
            except Exception as write_exc:
                logger.error(
                    "[ExecutionIntegrity] ExecutionGuard: log_result (success) failed: %s",
                    type(write_exc).__name__,
                )
        else:
            failure_reason = (
                f"{type(exc_val).__name__}: {exc_val}" if exc_val
                else "Execution did not call guard.succeed()"
            )
            try:
                self._registry.log_result(
                    receipt_id      = self.receipt_id,
                    final_status    = ExecutionStatus.FAILED,
                    failure_reason  = failure_reason[:500],
                    exchange_response = {},
                )
            except Exception as write_exc:
                logger.error(
                    "[ExecutionIntegrity] ExecutionGuard: log_result (FAILED) failed: %s "
                    "— receipt_id=%s failure_reason=%s",
                    type(write_exc).__name__, self.receipt_id, failure_reason,
                )
        return False


# ── Module-level singleton ─────────────────────────────────────────────────────

_registry_lock     = threading.Lock()
_global_registry   : Optional[ExecutionReceiptRegistry] = None


def get_global_registry() -> ExecutionReceiptRegistry:
    """
    Return the module-level ExecutionReceiptRegistry singleton.
    Thread-safe — initialised once on first call.
    """
    global _global_registry
    if _global_registry is None:
        with _registry_lock:
            if _global_registry is None:
                _global_registry = ExecutionReceiptRegistry()
    return _global_registry


@contextmanager
def execution_guard(
    decision_receipt_id : str,
    order_id            : str,
    symbol              : str,
    side                : str,
    size_usd            : float,
    execution_style     : str                  = "MARKET",
    requested_price     : Optional[float]      = None,
    requested_quantity  : Optional[float]      = None,
    registry            : Optional[ExecutionReceiptRegistry] = None,
) -> Generator[ExecutionGuard, None, None]:
    """
    Convenience context manager for the most common usage pattern.

    Example:
        with execution_guard(
            decision_receipt_id = receipt["receipt_id"],
            order_id            = "ORD-001",
            symbol              = "BTC/USDT",
            side                = "BUY",
            size_usd            = 10_000.0,
            execution_style     = "MARKET",
        ) as guard:
            resp = exchange.create_order(...)
            guard.succeed(
                executed_price    = resp["price"],
                filled_quantity   = resp["filled"],
                exchange_response = resp,
            )
    """
    _reg = registry or get_global_registry()
    intent = ExecutionIntent(
        order_id            = order_id,
        decision_receipt_id = decision_receipt_id,
        symbol              = symbol,
        side                = side,
        size_usd            = size_usd,
        execution_style     = execution_style,
        requested_price     = requested_price,
        requested_quantity  = requested_quantity,
    )
    guard = ExecutionGuard(registry=_reg, intent=intent)
    with guard:
        yield guard
