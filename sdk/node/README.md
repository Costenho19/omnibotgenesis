# OMNIX Quantum — Node.js / TypeScript SDK

Decision governance infrastructure with post-quantum cryptographic proof.

```bash
npm install omnix-quantum
```

```typescript
import { OmnixClient } from 'omnix-quantum'

const client = new OmnixClient({ apiKey: 'OMNIX-...' })

const receipt = await client.evaluate({
  domain:  'trading',
  asset:   'BTC/USD',
  signals: { price: 94200, volume: 1.5, volatility: 0.18 },
})

console.log(receipt.toString())
// ✅ APPROVED | OMNIX-TRD-a3f8b2c1d4e5f6a7 | 11/11 gates passed | sig: Dilithium-3 (NIST FIPS 204)

console.log(receipt.approved)           // true
console.log(receipt.receiptId)          // "OMNIX-TRD-a3f8b2c1d4e5f6a7"
console.log(receipt.contentHash)        // "sha256:..."
console.log(receipt.signatureAlgorithm) // "Dilithium-3 (NIST FIPS 204)"
```

---

## What OMNIX does

Before a decision executes, OMNIX validates it through 11 independent governance checkpoints — and issues a cryptographically signed receipt as proof.

- **Governance verdict**: APPROVED · BLOCKED · HOLD
- **Cryptographic proof**: SHA-256 hash + Dilithium-3 signature (NIST FIPS 204)
- **Independently verifiable**: anyone can verify the receipt offline, without OMNIX
- **5-year retention**: MiFID II compliant
- **9 domains live**: trading, Islamic credit, insurance, robotics, medical AI, energy, real estate, agents, stablecoin

---

## Installation

```bash
npm install omnix-quantum
# or
yarn add omnix-quantum
# or
pnpm add omnix-quantum
```

No runtime dependencies. Requires Node.js ≥ 16.

---

## Quick start

### ESM (TypeScript / modern Node)

```typescript
import { OmnixClient } from 'omnix-quantum'

const client = new OmnixClient({ apiKey: 'OMNIX-...' })

const receipt = await client.evaluate({
  domain:  'islamic_credit',
  asset:   'SME-AE-001',
  signals: {
    debt_to_income:   32,
    collateral_ratio: 1.4,
    sharia_compliant: true,
  },
})

console.log(receipt.decision)    // 'APPROVED'
console.log(receipt.receiptId)   // 'OMNIX-CRD-...'
console.log(receipt.approved)    // true
```

### CommonJS

```javascript
const { OmnixClient } = require('omnix-quantum')

const client = new OmnixClient({ apiKey: 'OMNIX-...' })

client.evaluate({
  domain: 'trading', asset: 'BTC/USD',
  signals: { price: 94200, volume: 1.5, volatility: 0.18 },
}).then(receipt => console.log(receipt.toString()))
```

### One-liner convenience

```typescript
import { evaluate } from 'omnix-quantum'

const receipt = await evaluate({
  apiKey:  'OMNIX-...',
  domain:  'energy',
  asset:   'SOLAR-GRID-07',
  signals: { capacity_mw: 240, grid_stability: 0.95, carbon_offset: 840 },
})
```

### Raise on block

```typescript
import { OmnixClient, OmnixGovernanceBlock } from 'omnix-quantum'

const client = new OmnixClient({ apiKey: 'OMNIX-...', raiseOnBlock: true })

try {
  await client.evaluate({
    domain: 'trading', asset: 'XMR/USD',
    signals: { price: 142, volume: 0.5, volatility: 0.95 },
  })
} catch (err) {
  if (err instanceof OmnixGovernanceBlock) {
    console.log('Blocked by:', err.receipt.veto_chain)
  }
}
```

---

## GovernanceReceipt — full type reference

```typescript
receipt.receiptId           // string  — "OMNIX-TRD-a3f8b2c1d4e5f6a7"
receipt.decision            // string  — "APPROVED" | "BLOCKED" | "HOLD"
receipt.approved            // boolean
receipt.blocked             // boolean
receipt.held                // boolean
receipt.timestamp           // string  — ISO 8601
receipt.domain              // string  — "trading"
receipt.asset               // string  — "BTC/USD"
receipt.policyVersion       // string  — "6.5.4e"
receipt.contentHash         // string  — "sha256:3a7f1b2c..."
receipt.signature           // string | null — Dilithium-3 PQC signature (base64)
receipt.signatureAlgorithm  // string | null — "Dilithium-3 (NIST FIPS 204)"
receipt.publicKey           // string | null
receipt.jurisdiction        // string | null — "UAE" | "EU" | "UK" | ...
receipt.checkpointsPassed   // number — 11
receipt.checkpointsBlocked  // number — 0
receipt.vetoChain           // string[] — [] or ["AML_GATE: VETO", ...]
receipt.checkpoints         // CheckpointResult[]
receipt.verifyUrl           // string | null
receipt.raw                 // GovernanceReceiptData — full raw response
receipt.toString()          // "✅ APPROVED | OMNIX-TRD-... | 11/11 gates | ..."
receipt.toJSON()            // GovernanceReceiptData
```

---

## Supported domains

| Domain | Example asset |
|--------|--------------|
| `trading` | `BTC/USD`, `ETH/USD` |
| `islamic_credit` | `SME-AE-001`, `RETAIL-KSA-042` |
| `insurance` | `AUTO-CLAIM-887`, `HEALTH-UK-221` |
| `energy` | `SOLAR-GRID-07`, `WIND-FARM-12` |
| `robotics` | `ARM-UNIT-33`, `AGV-FLEET-07` |
| `medical` | `DRUG-APPROVAL-91`, `SURGERY-PLAN-04` |
| `real_estate` | `PROP-UAE-1042`, `REIT-UK-05` |
| `agents` | `AI-AGENT-FINANCE-01` |
| `stablecoin` | `USDC-REDEMPTION-887` |

---

## All methods

```typescript
// Evaluate a decision
await client.evaluate({ domain, asset, signals, context? })

// Verify a receipt by ID (cryptographic, no DB)
await client.verify('OMNIX-TRD-...')

// Fetch a receipt by ID
await client.getReceipt('OMNIX-TRD-...')

// Public trust registry (no auth)
await client.trustRegistry()

// Current signing public key — RFC 8615 well-known (no auth)
await client.publicKey()
```

---

## Error handling

```typescript
import {
  OmnixAuthError,        // Invalid API key
  OmnixValidationError,  // Malformed request — check .errors[]
  OmnixGovernanceBlock,  // Decision BLOCKED (raiseOnBlock=true only) — check .receipt
  OmnixRateLimitError,   // Too many requests — check .retryAfter
  OmnixServerError,      // Server error — check .statusCode
  OmnixNetworkError,     // Cannot reach OMNIX
} from 'omnix-quantum'

try {
  const receipt = await client.evaluate({ ... })
} catch (err) {
  if (err instanceof OmnixAuthError)       { /* check API key */ }
  if (err instanceof OmnixValidationError) { console.log(err.errors) }
  if (err instanceof OmnixRateLimitError)  { console.log(err.retryAfter) }
  if (err instanceof OmnixServerError)     { console.log(err.statusCode) }
  if (err instanceof OmnixNetworkError)    { /* connectivity issue */ }
}
```

---

## Build from source

```bash
cd sdk/node
npm install
npm run build     # outputs dist/ (ESM + CJS + types)
npm run typecheck
npm run example   # runs examples/basic_usage.ts
```

---

## Publish to npm

```bash
cd sdk/node
npm install
npm run build
npm publish --access public
```

---

## Links

- **Docs**: [omnixquantum.net/docs](https://omnixquantum.net/docs)
- **API reference**: [omnixquantum.net/integration](https://omnixquantum.net/integration)
- **Try it live**: [omnixquantum.net/try](https://omnixquantum.net/try)
- **Independent verification**: [omnixquantum.net/verify-independently](https://omnixquantum.net/verify-independently)
- **Python SDK**: `pip install omnix-quantum`
- **DID document**: `did:web:omnixquantum.net`

---

## License

MIT — OMNIX Quantum Ltd · omnixquantum.net
