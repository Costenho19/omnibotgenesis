# ADR-131 — Execution Integrity Layer

**Status:** ACCEPTED (v1)
**Date:** 2026-04-27
**Author:** OMNIX Quantum Ltd — Harold Alberto Nunes Rodelo
**Context:** Extending OMNIX from Decision Governance → Execution Governance

---

## Changelog

| Version | Date | Summary |
|---|---|---|
| v1 | 2026-04-27 | Initial implementation — ExecutionReceipt, ExecutionGuard, VC binding, full test suite |

---

## 1. Context and Problem Statement

OMNIX already governs *decisions* — every evaluation produces a tamper-evident
`decision_receipt` with PQC signature, W3C VC envelope, and audit trail (ADR-096,
ADR-084, ADR-130). The system knows **what was decided and why**.

However, governance stops at the boundary of the exchange. Once a trade order
leaves OMNIX, there is no verifiable record of:

- **What was intended** before the order was sent (pre-execution state)
- **What actually happened** (fill price, quantity, latency, slippage)
- **Whether intent matched outcome** (fill_ratio, slippage_bps)
- **Whether the execution can be linked** to the governance decision that authorised it

This creates a structural audit gap. A regulator, auditor, or investor examining
a sequence of decisions and trades cannot establish that the execution was:
1. Authorised by a specific governance decision
2. Captured accurately (not retrofitted or adjusted post-hoc)
3. Auditable under the same standards as the decision itself

### Why this matters at the institutional level

In regulated trading environments (MiFID II, SEC Rule 17a-4, CFTC audit trail
requirements), the audit chain must be continuous from **signal → decision →
execution → settlement**. Gaps in this chain are not just operational risks — they
are compliance failures.

OMNIX's competitive position as a governance infrastructure provider depends on
being able to close this chain completely.

---

## 2. Decision

Implement an **Execution Integrity Layer** that governs execution with the same
rigour that OMNIX applies to decisions.

The layer introduces three non-negotiable invariants:

**Invariant 1: No silent execution**
Every execution path — success, partial fill, failure, timeout, exception —
must produce a verifiable `ExecutionReceipt`. There is no code path that exits
an execution attempt without a receipt.

**Invariant 2: Pre-intent captured**
The `ExecutionIntent` (what OMNIX *intended* to execute) is logged to the database
*before* the order is sent to the exchange. If the database write fails, the trade
does not proceed (fail-closed). This ensures the intent record cannot be
retrofitted after the fact.

**Invariant 3: Decision binding**
Every `ExecutionReceipt` carries a mandatory `decision_receipt_id` field that
links it to the governance decision that authorised the trade. This closes the
decision→execution audit chain.

---

## 3. Architecture

### 3.1 Data Models

```
ExecutionIntent (pre-execution)
  order_id             — exchange order reference (assigned by OMNIX pre-send)
  decision_receipt_id  — governance chain link (mandatory)
  symbol               — instrument (e.g. "BTC/USDT")
  side                 — BUY | SELL
  size_usd             — notional value of the intent
  execution_style      — MARKET / LIMIT / TWAP / VWAP / ICEBERG / POV / IS
  requested_price      — limit price if applicable (None for MARKET)
  requested_quantity   — units to trade
  intent_timestamp     — UTC datetime (nanosecond precision via time.time_ns())
  intent_timestamp_ns  — raw nanoseconds (tamper-evident)
```

```
ExecutionReceipt (post-execution, seals the record)
  receipt_id           — OMNIX unique identifier (UUID4 hex)
  [all ExecutionIntent fields]
  result_timestamp     — UTC datetime of exchange response
  result_timestamp_ns  — nanosecond-precision result time
  latency_ms           — (result_ns - intent_ns) / 1_000_000
  slippage_bps         — ((executed_price - requested_price) / requested_price) × 10,000
  executed_price       — actual fill price from exchange
  filled_quantity      — units actually filled
  fill_ratio           — filled_quantity / requested_quantity (0.0–1.0)
  exchange_response    — raw exchange response (JSONB, preserved verbatim)
  final_status         — FILLED | PARTIAL | FAILED | PENDING
  failure_reason       — cause string if FAILED (never empty on FAILED status)
  receipt_hash         — SHA-256 of canonical payload (tamper-evident seal)
  vc_issued            — boolean, True if a W3C VC has been issued
  audit_trail          — JSONB append-only list of state transitions
```

### 3.2 ExecutionStatus Lifecycle

```
                   log_intent()
                       │
                    PENDING ──────────────────────────────┐
                       │                                   │
              exchange responds                    exception raised
                       │                            (any reason)
              ┌────────┴────────┐                         │
           FILLED           PARTIAL                     FAILED
        (fill_ratio=1)   (0 < ratio < 1)         (failure_reason set)
```

### 3.3 ExecutionGuard — Fail-safe Context Manager

The `ExecutionGuard` class enforces all three invariants at the call site:

```python
with execution_guard(
    decision_receipt_id = governance_receipt["receipt_id"],
    order_id            = "ORD-001",
    symbol              = "BTC/USDT",
    side                = "BUY",
    size_usd            = 10_000.0,
    execution_style     = "MARKET",
) as guard:
    response = exchange.create_order(symbol="BTC/USDT", side="buy", amount=0.15)
    guard.succeed(
        executed_price    = response["average"],
        filled_quantity   = response["filled"],
        exchange_response = response,
    )
# If exchange.create_order() raises → FAILED receipt is written automatically
# guard.receipt_id is available for downstream reference
```

**Guarantee**: `__exit__` always calls `log_result()`. If `guard.succeed()` was
never called (exchange raised, timeout, etc.), a `FAILED` receipt is written with
`failure_reason = f"{ExcType}: {exc_val}"`.

### 3.4 Slippage Calculation

```
slippage_bps = ((executed_price − requested_price) / requested_price) × 10,000
```

- Positive slippage_bps → bought higher / sold lower than intended (adverse)
- Negative slippage_bps → bought lower / sold higher than intended (favorable)
- `slippage_acceptable` → |slippage_bps| < 50 (0.5% threshold)
- MARKET orders with no `requested_price` → `slippage_bps = None`

### 3.5 Latency Measurement

```
latency_ms = (result_timestamp_ns − intent_timestamp_ns) / 1,000,000
```

Both timestamps use `time.time_ns()` (nanosecond wall-clock, monotonic within
the same process). Nanosecond precision is preserved in the database as BIGINT.
This is consistent with `proof_layer.py` nanosecond precision (ADR-096).

### 3.6 Receipt Hash

The `receipt_hash` seals the execution record against post-hoc modification:

```python
SHA-256({
    receipt_id, order_id, decision_receipt_id,
    symbol, side, size_usd, execution_style,
    requested_price, requested_quantity,
    intent_timestamp_ns, result_timestamp_ns,
    executed_price, filled_quantity, final_status
})
```

Fields excluded from hash: `receipt_hash` itself, `audit_trail`, `exchange_response`
(exchange responses may contain non-deterministic fields like rate limits,
server timestamps, etc.).

### 3.7 W3C Verifiable Credential Binding (Optional)

`ExecutionReceipt.to_vc_payload()` produces a W3C VC compatible with the OMNIX
VC infrastructure (ADR-084). The VC:

- type: `["VerifiableCredential", "OmnixExecutionReceipt"]`
- issuer: `did:web:omnixquantum.net`
- credentialSubject: execution fields (symbol, side, status, prices, quantities)
- credentialStatus: `OmnixExecutionIntegrityStatus` with `receiptHash` anchor
- proof: `OmnixReceiptHash` with `receiptHash` and `integrityLayer: "ADR-131"`

The issued VC can be tracked via `mark_vc_issued()` and `vc_issued` field.

---

## 4. Database Schema

```sql
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
```

**Indexes:**
- `idx_execution_receipts_order_id` — lookup by exchange order reference
- `idx_execution_receipts_decision_receipt_id` — governance chain traversal
- `idx_execution_receipts_final_status` — aggregate queries by status
- `idx_execution_receipts_created_at DESC` — time-ordered audit queries

**Design decisions:**
- `receipt_id` is UUID4 hex — not a serial integer (consistent with ADR-074)
- `audit_trail` is JSONB append-only — state transitions are never deleted
- `exchange_response` is JSONB verbatim — no transformation of exchange data
- `failure_reason` is NOT NULL DEFAULT '' — no silent NULLs on failure

---

## 5. Consequences

### Positive

- **Full audit chain**: decision_receipt_id → execution_receipt_id closes the
  governance-to-execution gap. Regulators can trace from signal to settlement.
- **Tamper evidence**: receipt_hash detects post-hoc modification of any
  execution record. Consistent with existing PQC-signed decision receipts.
- **Fail-closed intent logging**: if the pre-execution write fails, the trade
  does not proceed. Prevents ghost trades (executed but unrecorded).
- **Zero silent failures**: ExecutionGuard guarantees a FAILED receipt on any
  exception. Execution failures are always visible in the audit trail.
- **Minimal performance impact**: log_intent() and log_result() each do a
  single synchronous DB write. Total overhead ~0.1ms on Railway PostgreSQL.
- **VC-ready**: to_vc_payload() enables immediate integration with the W3C VC
  issuance pipeline (ADR-084) without schema changes.
- **Nanosecond precision**: consistent with proof_layer.py (time.time_ns()),
  enabling sub-millisecond latency analysis.

### Negative / Trade-offs

- **Two synchronous DB writes per execution**: log_intent() (before) and
  log_result() (after). This is intentional — async writes would create a
  window where the intent is unrecorded.
- **OMNIX_DB_URL required at execution time**: if the DB is unavailable,
  log_intent() raises and the trade does not proceed. This is the desired
  fail-closed behaviour, but requires DB availability as a hard dependency.
- **exchange_response stored verbatim**: JSONB storage of full exchange
  responses may include sensitive rate-limit headers or server metadata.
  Callers should sanitise responses before passing to log_result() if
  security policy requires it.

---

## 6. Compliance References

| Standard | Requirement | ADR-131 Response |
|---|---|---|
| MiFID II Art. 25 | Transaction reporting with precise timestamps | `intent_timestamp_ns` + `result_timestamp_ns` (nanosecond) |
| MiFID II Art. 17 | Algorithmic trading: pre- and post-trade records | `ExecutionIntent` (pre) + `ExecutionReceipt` (post) |
| SEC Rule 17a-4 | Immutable audit records | append-only `audit_trail` JSONB + `receipt_hash` |
| CFTC Rule 1.35 | Complete and accurate records of all orders | `exchange_response` verbatim + `failure_reason` mandatory |
| eIDAS 2.0 / EUDI ARF | Verifiable evidence of automated decisions | `to_vc_payload()` W3C VC binding |

---

## 7. Files

| File | Purpose |
|---|---|
| `omnix_web/api/omnix_engine/execution_receipt.py` | Core module — all models, registry, guard |
| `tests/test_execution_receipt.py` | Full test suite |
| `docs/adr/ADR-131-execution-integrity-layer.md` | This document |
