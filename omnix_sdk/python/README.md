# OMNIX Python SDK — v2.0.0

Official client library for the **OMNIX Decision Governance API**.

Covers the complete decision→governance→execution audit chain:
`evaluate()` → `execute()` → `verify()` → `get_vc()` → `revoke()`

**Production endpoint:** `https://omnixquantum.net`  
**Zero external dependencies.** Python 3.8+.

---

## Installation

Copy `omnix_sdk.py` into your project. A pip package is coming.

```bash
cp omnix_sdk.py ./your_project/
```

---

## Quick Start

```python
from omnix_sdk import OmnixClient

client = OmnixClient(api_key="OMNIX-your-key-here")

# 1. Govern a decision
receipt = client.evaluate({
    "signal_integrity"  : 75,
    "probability_score" : 68,
    "risk_exposure"     : 35,
    "signal_coherence"  : 72,
    "trend_persistence" : 60,
    "stress_resilience" : 55,
    "logic_consistency" : 70,
    "temporal_coherence": 65,
    "domain"  : "trading",
    "asset"   : "BTC/USD",
    "scenario": "Long position — 2% capital",
})

print(receipt["decision"])            # APPROVED | BLOCKED | HOLD
print(receipt["receipt_id"])          # OMNIX-a3f8e2...
print(receipt["pqc_signed"])          # True
print(receipt["checkpoints_passed"])  # 11

if receipt["decision"] == "APPROVED":

    # 2. Place order (your exchange code)
    order = exchange.create_order("BTC/USD", "market", "buy", 0.15)

    # 3. Log the execution — seals the audit chain
    exec_receipt = client.execute(
        decision_receipt_id = receipt["receipt_id"],
        order_id            = order["id"],
        symbol              = "BTC/USD",
        side                = "BUY",
        size_usd            = 10_000.0,
        final_status        = "FILLED",
        executed_price      = order["average"],
        filled_quantity     = order["filled"],
        exchange_response   = order,
    )
    print(exec_receipt["receipt_hash"])    # SHA-256 tamper-evident seal
    print(exec_receipt["latency_ms"])      # round-trip latency
    print(exec_receipt["slippage_bps"])    # price drift in basis points
```

---

## Authentication

Your API key format: `OMNIX-<40 alphanumeric characters>`

```python
# Option A — constructor
client = OmnixClient(api_key="OMNIX-your-key-here")

# Option B — environment variable (recommended for production)
import os
os.environ["OMNIX_API_KEY"] = "OMNIX-your-key-here"
client = OmnixClient()

# Option C — context manager
with OmnixClient(api_key="OMNIX-your-key-here") as client:
    result = client.evaluate(signals)
```

---

## Signal Reference

All 8 numeric signals are **required**. Range: `0–100`.

| Field | Description | Notes |
|-------|-------------|-------|
| `signal_integrity` | Input data quality | Is the data clean and complete? |
| `probability_score` | Decision confidence | How confident is the model? |
| `risk_exposure` | Risk level | **Lower = safer.** 0 = no risk, 100 = maximum risk |
| `signal_coherence` | Internal consistency | Do signals agree with each other? |
| `trend_persistence` | Trend alignment | Is the decision aligned with the prevailing trend? |
| `stress_resilience` | Stress tolerance | Does the decision hold under adverse conditions? |
| `logic_consistency` | Logical coherence | Is the decision scenario internally coherent? |
| `temporal_coherence` | Time-context validity | Is the context still valid at this moment? |

**Optional fields:**

| Field | Type | Values |
|-------|------|--------|
| `domain` | str | `trading` · `credit` · `insurance` · `robotics` · `medical` · `energy` · `real_estate` · `stablecoin` · `agents` |
| `asset` | str | Any identifier — `"BTC/USD"`, `"customer-8821"`, `"claim-447"` |
| `scenario` | str | Human-readable description of the decision |

---

## Full API Reference

### `evaluate(signals)` → dict

Submit a decision for governance evaluation. Returns a PQC-signed (Dilithium-3) receipt.

```python
receipt = client.evaluate({
    "signal_integrity": 80, "probability_score": 75,
    "risk_exposure": 30,    "signal_coherence": 70,
    "trend_persistence": 65,"stress_resilience": 60,
    "logic_consistency": 72,"temporal_coherence": 68,
    "domain": "credit", "asset": "customer-8821",
    "scenario": "Credit line increase — 12-month history review",
})
```

**Response keys:**
- `decision` — `"APPROVED"` | `"BLOCKED"` | `"HOLD"`
- `receipt_id` — `"OMNIX-a3f8e2..."` (unique identifier)
- `pqc_signed` — `True` if post-quantum signature is present
- `checkpoints_passed` — int (typically 11/11 for APPROVED)
- `checkpoints_total` — int
- `summary` — executive summary
- `regulatory_alignment` — regulatory frameworks evaluated
- `timestamp` — ISO 8601 UTC

---

### `execute(...)` → dict

Log the result of a trade execution. Seals the decision→execution audit chain (ADR-131).

```python
exec_receipt = client.execute(
    decision_receipt_id = "OMNIX-a3f8e2...",
    order_id            = "ORD-001",
    symbol              = "BTC/USD",
    side                = "BUY",
    size_usd            = 10_000.0,
    final_status        = "FILLED",       # FILLED | PARTIAL | FAILED
    executed_price      = 65_100.0,
    filled_quantity     = 0.15,
    requested_quantity  = 0.15,           # optional — used for fill_ratio
    execution_style     = "MARKET",       # optional
    exchange_response   = {"id": "..."},  # optional — stored verbatim
)
```

**`final_status` rules:**
- `"FILLED"` or `"PARTIAL"` → `executed_price` is **required**
- `"FAILED"` → `failure_reason` is **required**

**Response keys:**
- `receipt_id` — execution receipt identifier
- `decision_receipt_id` — linked governance receipt
- `final_status` — `FILLED` | `PARTIAL` | `FAILED`
- `latency_ms` — round-trip execution latency in milliseconds
- `slippage_bps` — price drift from requested to executed (basis points)
- `fill_ratio` — portion of order filled (0.0–1.0)
- `receipt_hash` — SHA-256 tamper-evident seal

---

### `get_execution_receipt(receipt_id)` → dict

Retrieve a previously logged execution receipt.

```python
receipt = client.get_execution_receipt("exec-abc123...")
```

---

### `verify(receipt_id)` → dict

Cryptographically verify a governance receipt (PQC Dilithium-3 + SHA-256).

```python
result = client.verify("OMNIX-a3f8e2...")

if not result["valid"]:
    raise Exception("Receipt integrity compromised")

print(result["signature_valid"])  # PQC signature check
print(result["hash_valid"])       # Content hash integrity
print(result["tamper_detected"])  # True if tampering found
```

---

### `get_vc(receipt_id, human_signer=None)` → dict

Issue a W3C Verifiable Credential for a governance receipt.

```python
# Basic VC
vc = client.get_vc("OMNIX-a3f8e2...")
print(vc["proof"]["type"])          # "Dilithium3Signature2024"
print(vc["credentialStatus"])       # StatusList2021 revocation entry

# With human accountability binding (ADR-130 §7)
vc = client.get_vc(
    receipt_id   = "OMNIX-a3f8e2...",
    human_signer = {
        "reviewer_id": "alice@firm.com",
        "attested_at": "2026-04-27T14:32:00Z",
        "eqs_score"  : 0.93,
    },
)
```

---

### `get_vc_status(receipt_id)` → dict

Check the live revocation status of a VC.

```python
status = client.get_vc_status("OMNIX-a3f8e2...")
print(status["status"])     # "active" | "revoked" | "suspended"
```

---

### `get_status_list()` → dict

Retrieve the W3C StatusList2021 revocation bitstring.

```python
sl = client.get_status_list()
print(sl["encodedList"])    # base64url(gzip(bitstring))
print(sl["total_revoked"])  # number of revoked credentials
```

---

### `revoke(receipt_id, reason)` → dict   _(admin only)_

```python
client.revoke(
    receipt_id = "OMNIX-a3f8e2...",
    reason     = "AVM detected assumption drift — domain suspended per ADR-129",
)
```

---

### `reinstate(receipt_id, reason)` → dict   _(admin only)_

```python
client.reinstate(
    receipt_id = "OMNIX-a3f8e2...",
    reason     = "Reinstatement approved after compliance review — all conditions cleared",
)
```

---

### `list_receipts(page, per_page, domain, asset, decision)` → dict

```python
receipts = client.list_receipts(
    page     = 1,
    per_page = 50,
    domain   = "trading",
    decision = "APPROVED",
)
for r in receipts["receipts"]:
    print(r["receipt_id"], r["decision"])
```

---

### `get_receipt(receipt_id)` → dict

```python
receipt = client.get_receipt("OMNIX-a3f8e2...")
```

---

### `health()` → dict

```python
h = client.health()
print(h["status"])      # "healthy" | "degraded" | "down"
print(h["components"])  # per-component status
```

---

### `get_schema()` → dict

Signal schema documentation with field descriptions and valid ranges.

---

### `get_regulatory_frameworks()` → dict

Full catalog of regulatory frameworks covered: MiFID II, Basel IV, GDPR, DORA, EU AI Act, ISO 13849, HIPAA, eIDAS 2.0, Dodd-Frank, Solvency II, and more.

---

### `get_due_diligence_report(format="json")` → dict

Generate a governance due diligence report. Suitable for M&A, investor review, and regulatory audits.

```python
report = client.get_due_diligence_report(format="json")
report = client.get_due_diligence_report(format="pdf")  # returns download_url
```

---

## Error Handling

```python
from omnix_sdk import (
    OmnixClient,
    OmnixError,           # Base class for all OMNIX errors
    OmnixAuthError,       # 401 / 403 — invalid or insufficient API key
    OmnixNotFoundError,   # 404 — receipt not found or not owned by your key
    OmnixValidationError, # 422 — missing/invalid fields in request
    OmnixRateLimitError,  # 429 — rate limit exceeded
    OmnixTimeoutError,    # 408 — request timed out
    OmnixServerError,     # 5xx — unexpected server-side error
    OmnixAPIError,        # catch-all for other API errors
)

try:
    receipt = client.evaluate(signals)

except OmnixAuthError:
    print("Invalid or expired API key — check OMNIX_API_KEY")

except OmnixValidationError as e:
    print(f"Validation error: {e}")

except OmnixRateLimitError as e:
    print(f"Rate limit — retry after {e.retry_after}s")

except OmnixTimeoutError:
    print("Request timed out — check your network or increase timeout")

except OmnixNotFoundError:
    print("Receipt not found")

except OmnixServerError as e:
    print(f"OMNIX server error {e.status_code} — team has been notified")

except OmnixAPIError as e:
    print(f"Unexpected error: {e}")
```

---

## Retry & Timeout

The client automatically retries on `429 Rate Limit` and `503 Service Unavailable` with exponential backoff.

```python
client = OmnixClient(
    api_key       = "OMNIX-your-key-here",
    timeout       = 30,      # seconds per request (default: 30)
    max_retries   = 3,       # auto-retries on transient errors (default: 3)
    retry_backoff = 1.0,     # base backoff in seconds (default: 1.0)
)
```

To disable retries:

```python
client = OmnixClient(api_key="OMNIX-...", max_retries=0)
```

---

## Custom Base URL

For sandbox or self-hosted deployments:

```python
client = OmnixClient(
    api_key  = "OMNIX-your-key-here",
    base_url = "https://sandbox.omnixquantum.net",
)
```

Or via environment variable:

```bash
export OMNIX_BASE_URL="https://sandbox.omnixquantum.net"
```

---

## Complete Example: Trading Governance Loop

```python
import os
from omnix_sdk import OmnixClient, OmnixAuthError

client = OmnixClient()  # reads OMNIX_API_KEY from env

def governed_trade(symbol: str, side: str, size_usd: float, signals: dict):
    # 1. Govern the decision
    receipt = client.evaluate({**signals, "domain": "trading", "asset": symbol})

    if receipt["decision"] != "APPROVED":
        print(f"Trade blocked by governance: {receipt['summary']}")
        return None

    # 2. Execute (your exchange code)
    try:
        order = exchange.create_order(symbol, "market", side.lower(), size_usd / signals.get("price", 1))
        final_status  = "FILLED"
        executed_price = order["average"]
        filled_qty    = order["filled"]
        exchange_resp = order
    except Exception as e:
        final_status  = "FAILED"
        executed_price = None
        filled_qty    = None
        exchange_resp = {}
        failure_reason = str(e)

    # 3. Seal the audit chain
    exec_receipt = client.execute(
        decision_receipt_id = receipt["receipt_id"],
        order_id            = order.get("id", "failed"),
        symbol              = symbol,
        side                = side,
        size_usd            = size_usd,
        final_status        = final_status,
        executed_price      = executed_price,
        filled_quantity     = filled_qty,
        exchange_response   = exchange_resp,
        failure_reason      = "" if final_status != "FAILED" else failure_reason,
    )

    return {
        "governance_receipt": receipt["receipt_id"],
        "execution_receipt" : exec_receipt["receipt_id"],
        "decision"          : receipt["decision"],
        "final_status"      : exec_receipt["final_status"],
        "slippage_bps"      : exec_receipt.get("slippage_bps"),
        "latency_ms"        : exec_receipt.get("latency_ms"),
    }
```

---

## Contact

- Web: [omnixquantum.net](https://omnixquantum.net)
- Email: contacto@omnixquantum.net
- Author: Harold Alberto Nunes Rodelo — OMNIX Quantum Ltd, UK

**Spec:** ADR-132 — SDK Public API Surface  
**Version:** 2.0.0
