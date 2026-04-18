# OMNIX Node.js SDK

Official client library for the OMNIX Decision Governance API.

## Installation

Copy `index.js` into your project. An npm package is coming soon.

## Quick Start

```javascript
const OmnixClient = require('./omnix_sdk');

const client = new OmnixClient({ apiKey: 'OMNIX-your-key-here' });

const result = await client.evaluate({
  signal_integrity: 75,
  probability_score: 68,
  risk_exposure: 42,
  signal_coherence: 60,
  trend_persistence: 55,
  stress_resilience: 48,
  logic_consistency: 65,
  temporal_coherence: 58,
  domain: 'trading',
  asset: 'BTC/USD',
  scenario: 'Long position pre-execution — 2% capital'
});

console.log(result.decision);           // 'APPROVED' | 'BLOCKED' | 'HOLD'
console.log(result.receipt_id);         // 'OMNIX-a3f8e2...'
console.log(result.pqc_signed);         // true
console.log(result.checkpoints_passed); // 11
```

## Signal Reference

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `signal_integrity` | number | 0–100 | Input data quality score |
| `probability_score` | number | 0–100 | Confidence in the decision |
| `risk_exposure` | number | 0–100 | Risk level — **lower is safer** |
| `signal_coherence` | number | 0–100 | Internal signal consistency |
| `trend_persistence` | number | 0–100 | Trend alignment score |
| `stress_resilience` | number | 0–100 | Resilience under stress |
| `logic_consistency` | number | 0–100 | Logical coherence |
| `temporal_coherence` | number | 0–100 | Time-context validity |
| `domain` | string | — | `trading`, `credit`, `insurance`, `robotics` |
| `asset` | string | — | Asset or entity identifier |
| `scenario` | string | — | Human-readable description |

## Methods

```javascript
// Evaluate a decision
await client.evaluate(signals)

// Get a specific receipt
await client.getReceipt(receiptId)

// List your receipts (paginated)
await client.listReceipts(page = 1, perPage = 20)

// Due diligence report
await client.getDueDiligenceReport('json')
await client.getDueDiligenceReport('pdf')

// Regulatory frameworks catalog
await client.getRegulatoryFrameworks()
```

## Error Handling

```javascript
const { OmnixAuthError, OmnixRateLimitError, OmnixAPIError } = OmnixClient;

try {
  const result = await client.evaluate(signals);
} catch (err) {
  if (err instanceof OmnixAuthError) {
    console.error('Invalid or expired API key');
  } else if (err instanceof OmnixRateLimitError) {
    console.error('Rate limit — retry after 60s');
  } else if (err instanceof OmnixAPIError) {
    console.error(`API error ${err.statusCode}: ${err.message}`);
  }
}
```

## Webhook Integration

Register a webhook to receive decision events in real time:

```bash
curl -X PUT https://omnixquantum.net/api/governance/admin/clients/your-client-id/webhook \
  -H "X-API-Key: OMNIX-your-admin-key" \
  -H "Content-Type: application/json" \
  -d '{"webhook_url": "https://your-system.com/omnix-events", "webhook_secret": "your-secret"}'
```

Each event is HMAC-SHA256 signed in the `X-OMNIX-Signature` header.

## Contact

- Web: https://omnixquantum.net
- Email: contacto@omnixquantum.net
