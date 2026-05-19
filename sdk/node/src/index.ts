/**
 * OMNIX Governance SDK — Node.js / TypeScript
 * =============================================
 *
 * Decision governance infrastructure for automated systems.
 * Cryptographic proof on every decision. 10 domains. Live.
 *
 * Quick start:
 *   npm install omnix-quantum
 *
 *   import { OmnixClient } from 'omnix-quantum'
 *
 *   const client = new OmnixClient({ apiKey: 'OMNIX-...' })
 *   const receipt = await client.evaluate({
 *     domain:  'trading',
 *     asset:   'BTC/USD',
 *     signals: { price: 94200, volume: 1.5, volatility: 0.18 },
 *   })
 *
 *   console.log(receipt.toString())   // ✅ APPROVED | OMNIX-TRD-... | 11/11 gates
 *   console.log(receipt.approved)     // true
 *   console.log(receipt.contentHash)  // sha256:...
 *
 * Docs:   https://omnixquantum.net/docs
 * Verify: https://omnixquantum.net/verify-independently
 * DID:    did:web:omnixquantum.net
 */

export { OmnixClient }          from './client.js'
export type { OmnixClientOptions, EvaluateOptions } from './client.js'

export {
  computeKeyFingerprint,
  canonicalJson,
  canonicalJsonSha256,
  verifyKeyFingerprint,
  parseFingerprint,
} from './fingerprint.js'

export { GovernanceReceipt, CheckpointResult } from './models.js'
export type { GovernanceReceiptData, CheckpointResultData } from './models.js'

export {
  OmnixError,
  OmnixAuthError,
  OmnixValidationError,
  OmnixGovernanceBlock,
  OmnixRateLimitError,
  OmnixServerError,
  OmnixNetworkError,
} from './exceptions.js'

/**
 * Convenience function — evaluate a governance decision.
 *
 * ```typescript
 * import { evaluate } from 'omnix-quantum'
 *
 * const receipt = await evaluate({
 *   apiKey:  'OMNIX-...',
 *   domain:  'islamic_credit',
 *   asset:   'SME-AE-001',
 *   signals: { debt_to_income: 32, collateral_ratio: 1.4, sharia_compliant: true },
 * })
 * console.log(receipt.decision) // 'APPROVED'
 * ```
 */
export async function evaluate(opts: {
  apiKey:   string
  domain:   string
  asset:    string
  signals:  Record<string, unknown>
  context?: Record<string, unknown>
  baseUrl?: string
  timeout?: number
}) {
  const { apiKey, domain, asset, signals, context, ...rest } = opts
  const { OmnixClient } = await import('./client.js')
  const client = new OmnixClient({ apiKey, ...rest })
  return client.evaluate({ domain, asset, signals, context })
}
