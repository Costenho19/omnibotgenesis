/**
 * OMNIX SDK — Node.js / TypeScript — Basic Usage Examples
 * =========================================================
 * npm install omnix-quantum
 * npx tsx examples/basic_usage.ts
 */

import {
  OmnixClient,
  OmnixGovernanceBlock,
  OmnixAuthError,
  evaluate,
} from '../src/index.js'

const API_KEY = 'OMNIX-your-key-here'
const client  = new OmnixClient({ apiKey: API_KEY })

// ── Example 1: Trading decision ───────────────────────────────────────────

const receipt = await client.evaluate({
  domain:  'trading',
  asset:   'BTC/USD',
  signals: { price: 94200, volume: 1.5, volatility: 0.18 },
})

console.log(receipt.toString())
// ✅ APPROVED | OMNIX-TRD-a3f8b2c1d4e5f6a7 | 11/11 gates passed | sig: Dilithium-3 (NIST FIPS 204)

console.log('Decision            :', receipt.decision)
console.log('Receipt ID          :', receipt.receiptId)
console.log('Content hash        :', receipt.contentHash)
console.log('Signature algorithm :', receipt.signatureAlgorithm)
console.log('Checkpoints passed  :', receipt.checkpointsPassed, '/ 11')
console.log('Approved?           :', receipt.approved)
console.log('Verify at           :', receipt.verifyUrl)

// ── Example 2: Islamic credit — one-liner ──────────────────────────────────

const credit = await evaluate({
  apiKey:  API_KEY,
  domain:  'islamic_credit',
  asset:   'SME-AE-001',
  signals: { debt_to_income: 32, collateral_ratio: 1.4, sharia_compliant: true },
})
console.log('\nCredit:', credit.toString())

// ── Example 3: Insurance ──────────────────────────────────────────────────

const insurance = await client.evaluate({
  domain:  'insurance',
  asset:   'AUTO-CLAIM-887',
  signals: { claim_amount: 12000, fraud_score: 0.12, policy_active: true },
})
console.log('\nInsurance:', insurance.toString())

// ── Example 4: Raise on block ─────────────────────────────────────────────

const strictClient = new OmnixClient({ apiKey: API_KEY, raiseOnBlock: true })

try {
  await strictClient.evaluate({
    domain:  'trading',
    asset:   'XMR/USD',
    signals: { price: 142, volume: 0.5, volatility: 0.95 },
  })
} catch (err) {
  if (err instanceof OmnixGovernanceBlock) {
    console.log('\nBLOCKED:', err.message)
    console.log('Veto chain:', err.receipt.veto_chain)
  } else {
    throw err
  }
}

// ── Example 5: Verify receipt independently ────────────────────────────────

const verification = await client.verify('OMNIX-TRD-a3f8b2c1d4e5f6a7')
console.log('\nVerification:')
console.log('  hash_valid      :', verification.hash_valid)
console.log('  signature_valid :', verification.signature_valid)
console.log('  overall_valid   :', verification.overall_valid)

// ── Example 6: Public endpoints (no auth) ─────────────────────────────────

const registry = await client.trustRegistry()
console.log('\nTrust registry issuers:', (registry.issuers as unknown[])?.length ?? 0)

const pub = await client.publicKey()
const key = pub.key as Record<string, string>
console.log('\nPublic key algorithm   :', key?.algorithm)
console.log('Key fingerprint sha256 :', key?.fingerprint_sha256)

// ── Example 7: TypeScript types ────────────────────────────────────────────

// GovernanceReceipt is fully typed — IDE autocomplete on all fields
const { receiptId, decision, checkpoints, vetoChain, jurisdiction } = receipt
console.log('\nTyped fields:')
console.log('  receiptId   :', receiptId)
console.log('  decision    :', decision)
console.log('  jurisdiction:', jurisdiction)
console.log('  vetoChain   :', vetoChain)
console.log('  gates       :', checkpoints.map(c => `${c.name}=${c.result}`))
