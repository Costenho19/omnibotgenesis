# OMNIX Node.js SDK — v2.0.0

Official client library for the **OMNIX Decision Governance API**.

Covers the complete decision→governance→execution audit chain:
`evaluate()` → `execute()` → `verify()` → `getVc()` → `revoke()`

**Production endpoint:** `https://omnixquantum.net`  
**Zero external dependencies.** Node.js 14+.

---

## Installation

Copy `index.js` into your project. An npm package is coming.

```bash
cp index.js ./your_project/omnix_sdk.js
```

---

## Quick Start

```javascript
const OmnixClient = require('./omnix_sdk');

const client = new OmnixClient({ apiKey: 'OMNIX-your-key-here' });

// 1. Govern a decision
const receipt = await client.evaluate({
  signal_integrity  : 75,
  probability_score : 68,
  risk_exposure     : 35,
  signal_coherence  : 72,
  trend_persistence : 60,
  stress_resilience : 55,
  logic_consistency : 70,
  temporal_coherence: 65,
  domain  : 'trading',
  asset   : 'BTC/USD',
  scenario: 'Long position — 2% capital',
});

console.log(receipt.decision);           // APPROVED | BLOCKED | HOLD
console.log(receipt.receipt_id);         // OMNIX-a3f8e2...
console.log(receipt.pqc_signed);         // true
console.log(receipt.checkpoints_passed); // 11

if (receipt.decision === 'APPROVED') {

  // 2. Place order (your exchange code)
  const order = await exchange.createOrder('BTC/USD', 'market', 'buy', 0.15);

  // 3. Log the execution — seals the audit chain
  const execReceipt = await client.execute({
    decisionReceiptId: receipt.receipt_id,
    orderId          : order.id,
    symbol           : 'BTC/USD',
    side             : 'BUY',
    sizeUsd          : 10_000,
    finalStatus      : 'FILLED',
    executedPrice    : order.average,
    filledQuantity   : order.filled,
    exchangeResponse : order,
  });

  console.log(execReceipt.receipt_hash);  // SHA-256 tamper-evident seal
  console.log(execReceipt.latency_ms);    // round-trip latency in ms
  console.log(execReceipt.slippage_bps);  // price drift in basis points
}
```

---

## Authentication

Your API key format: `OMNIX-<40 alphanumeric characters>`

```javascript
// Option A — constructor
const client = new OmnixClient({ apiKey: 'OMNIX-your-key-here' });

// Option B — environment variable (recommended for production)
process.env.OMNIX_API_KEY = 'OMNIX-your-key-here';
const client = new OmnixClient();

// Option C — custom base URL for sandbox or self-hosted
const client = new OmnixClient({
  apiKey : 'OMNIX-your-key-here',
  baseUrl: 'https://sandbox.omnixquantum.net',
});

// Option D — via OMNIX_BASE_URL env var
process.env.OMNIX_BASE_URL = 'https://sandbox.omnixquantum.net';
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

| Field | Values |
|-------|--------|
| `domain` | `trading` · `credit` · `insurance` · `robotics` · `medical` · `energy` · `real_estate` · `stablecoin` · `agents` |
| `asset` | Any identifier — `"BTC/USD"`, `"customer-8821"`, `"claim-447"` |
| `scenario` | Human-readable description |

---

## Full API Reference

### `evaluate(signals)` → Promise\<object\>

Submit a decision for governance evaluation. Returns a PQC-signed (Dilithium-3) receipt.

```javascript
const receipt = await client.evaluate({
  signal_integrity: 80, probability_score: 75,
  risk_exposure: 30,    signal_coherence: 70,
  trend_persistence: 65,stress_resilience: 60,
  logic_consistency: 72,temporal_coherence: 68,
  domain: 'credit', asset: 'customer-8821',
  scenario: 'Credit line increase — 12-month history review',
});
```

**Response keys:** `decision`, `receipt_id`, `pqc_signed`, `checkpoints_passed`, `checkpoints_total`, `summary`, `regulatory_alignment`, `timestamp`

---

### `execute(options)` → Promise\<object\>

Log the result of a trade execution. Seals the decision→execution audit chain (ADR-131).

```javascript
const execReceipt = await client.execute({
  decisionReceiptId : 'OMNIX-a3f8e2...',
  orderId           : 'ORD-001',
  symbol            : 'BTC/USD',
  side              : 'BUY',
  sizeUsd           : 10_000,
  finalStatus       : 'FILLED',    // FILLED | PARTIAL | FAILED
  executedPrice     : 65_100,
  filledQuantity    : 0.15,
  requestedQuantity : 0.15,        // optional — used for fill_ratio
  executionStyle    : 'MARKET',    // optional
  exchangeResponse  : { id: '...' }, // optional
});
```

**`finalStatus` rules:**
- `"FILLED"` or `"PARTIAL"` → `executedPrice` is **required**
- `"FAILED"` → `failureReason` is **required**

**Response keys:** `receipt_id`, `decision_receipt_id`, `final_status`, `latency_ms`, `slippage_bps`, `fill_ratio`, `receipt_hash`

---

### `getExecutionReceipt(receiptId)` → Promise\<object\>

```javascript
const receipt = await client.getExecutionReceipt('exec-abc123...');
```

---

### `verify(receiptId)` → Promise\<object\>

Cryptographically verify a governance receipt.

```javascript
const result = await client.verify('OMNIX-a3f8e2...');
if (!result.valid) throw new Error('Receipt integrity compromised');
```

---

### `getVc(receiptId, humanSigner?)` → Promise\<object\>

Issue a W3C Verifiable Credential.

```javascript
const vc = await client.getVc('OMNIX-a3f8e2...');
console.log(vc.proof.type);       // 'Dilithium3Signature2024'
console.log(vc.credentialStatus); // StatusList2021 entry

// With human accountability binding
const vc = await client.getVc('OMNIX-a3f8e2...', {
  reviewer_id: 'alice@firm.com',
  attested_at: '2026-04-27T14:32:00Z',
  eqs_score  : 0.93,
});
```

---

### `getVcStatus(receiptId)` → Promise\<object\>

```javascript
const status = await client.getVcStatus('OMNIX-a3f8e2...');
console.log(status.status); // 'active' | 'revoked' | 'suspended'
```

---

### `getStatusList()` → Promise\<object\>

W3C StatusList2021 revocation bitstring.

```javascript
const sl = await client.getStatusList();
console.log(sl.encodedList);   // base64url(gzip(bitstring))
console.log(sl.total_revoked);
```

---

### `revoke(receiptId, reason)` → Promise\<object\>   _(admin only)_

```javascript
await client.revoke(
  'OMNIX-a3f8e2...',
  'AVM detected assumption drift — domain suspended per ADR-129'
);
```

---

### `reinstate(receiptId, reason)` → Promise\<object\>   _(admin only)_

```javascript
await client.reinstate(
  'OMNIX-a3f8e2...',
  'Reinstatement approved after compliance review — all conditions cleared'
);
```

---

### `listReceipts(options?)` → Promise\<object\>

```javascript
const result = await client.listReceipts({
  page: 1, perPage: 50, domain: 'trading', decision: 'APPROVED',
});
```

---

### `getReceipt(receiptId)` → Promise\<object\>

```javascript
const receipt = await client.getReceipt('OMNIX-a3f8e2...');
```

---

### `health()` → Promise\<object\>

```javascript
const h = await client.health();
console.log(h.status); // 'healthy' | 'degraded' | 'down'
```

---

### `getSchema()` / `getRegulatoryFrameworks()` / `getDueDiligenceReport(format?)` → Promise\<object\>

```javascript
const schema      = await client.getSchema();
const regulations = await client.getRegulatoryFrameworks();
const report      = await client.getDueDiligenceReport('json');
const pdf         = await client.getDueDiligenceReport('pdf'); // returns download_url
```

---

## Error Handling

```javascript
const {
  OmnixAuthError, OmnixNotFoundError, OmnixValidationError,
  OmnixRateLimitError, OmnixTimeoutError, OmnixServerError, OmnixAPIError,
} = OmnixClient;

try {
  const receipt = await client.evaluate(signals);

} catch (err) {
  if (err instanceof OmnixAuthError) {
    console.error('Invalid or expired API key');
  } else if (err instanceof OmnixValidationError) {
    console.error('Validation error:', err.message);
  } else if (err instanceof OmnixRateLimitError) {
    console.error(`Rate limit — retry after ${err.retryAfter}s`);
  } else if (err instanceof OmnixTimeoutError) {
    console.error('Request timed out');
  } else if (err instanceof OmnixNotFoundError) {
    console.error('Receipt not found');
  } else if (err instanceof OmnixServerError) {
    console.error(`Server error ${err.statusCode}`);
  } else if (err instanceof OmnixAPIError) {
    console.error('API error:', err.message);
  }
}
```

---

## Retry & Timeout

```javascript
const client = new OmnixClient({
  apiKey      : 'OMNIX-your-key-here',
  timeout     : 30_000,  // ms per request (default: 30000)
  maxRetries  : 3,       // retries on 429/503 (default: 3)
  retryBackoff: 1_000,   // base backoff in ms (default: 1000)
});
```

---

## Webhook Integration

Register a webhook to receive revocation events in real time.
Each event is HMAC-SHA256 signed in the `X-OMNIX-Signature` header.

```bash
curl -X PUT https://omnixquantum.net/api/governance/admin/clients/your-client-id/webhook \
  -H "X-API-Key: OMNIX-your-admin-key" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url"   : "https://your-system.com/omnix-events",
    "webhook_secret": "your-hmac-secret"
  }'
```

Verify incoming events on your server:

```javascript
const crypto = require('crypto');

function verifyWebhook(body, signature, secret) {
  const expected = 'sha256=' + crypto
    .createHmac('sha256', secret)
    .update(body)
    .digest('hex');
  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected));
}
```

---

## Contact

- Web: [omnixquantum.net](https://omnixquantum.net)
- Email: contacto@omnixquantum.net
- Author: Harold Alberto Nunes Rodelo — OMNIX Quantum Ltd, UK

**Spec:** ADR-132 — SDK Public API Surface  
**Version:** 2.0.0
