export interface CheckpointResultData {
  id?: string
  name?: string
  result?: string
  score?: number | null
  threshold?: number | null
  condition?: string | null
}

export class CheckpointResult {
  readonly id: string
  readonly name: string
  readonly result: string
  readonly score: number | null
  readonly threshold: number | null
  readonly condition: string | null

  constructor(data: CheckpointResultData) {
    this.id        = String(data.id ?? '')
    this.name      = data.name ?? ''
    this.result    = data.result ?? ''
    this.score     = data.score ?? null
    this.threshold = data.threshold ?? null
    this.condition = data.condition ?? null
  }

  get passed(): boolean {
    return this.result === 'PASS' || this.result === 'PASSED'
  }
}

// ─────────────────────────────────────────────────────────────────────────────

export interface GovernanceReceiptData {
  receipt_id?: string
  decision?: string
  timestamp?: string
  domain?: string
  asset?: string
  policy_version?: string
  content_hash?: string
  signature?: string | null
  signature_algorithm?: string | null
  integrity?: { algorithm?: string }
  public_key?: string | null
  jurisdiction?: string | null
  authority_binding?: { jurisdiction?: string }
  checkpoints_passed?: number
  checkpoints_blocked?: number
  veto_chain?: string[]
  checkpoint_proof?: CheckpointResultData[]
  checkpoints?: CheckpointResultData[]
  verify_url?: string | null
  [key: string]: unknown
}

/**
 * Cryptographically signed governance receipt issued by OMNIX.
 *
 * Every field is part of the canonical hash — any modification
 * invalidates the SHA-256 content_hash and the PQC signature.
 *
 * Verify offline:
 *   python omnix_verify.py receipt.json
 *   https://omnixquantum.net/verify-independently
 */
export class GovernanceReceipt {
  readonly receiptId: string
  readonly decision: 'APPROVED' | 'BLOCKED' | 'HOLD' | string
  readonly timestamp: string
  readonly domain: string
  readonly asset: string
  readonly policyVersion: string
  readonly contentHash: string
  readonly signature: string | null
  readonly signatureAlgorithm: string | null
  readonly publicKey: string | null
  readonly jurisdiction: string | null
  readonly checkpointsPassed: number
  readonly checkpointsBlocked: number
  readonly vetoChain: string[]
  readonly checkpoints: CheckpointResult[]
  readonly verifyUrl: string | null
  readonly raw: GovernanceReceiptData

  constructor(data: GovernanceReceiptData) {
    const cpRaw = data.checkpoint_proof ?? data.checkpoints ?? []
    const cps   = cpRaw.map(cp => new CheckpointResult(cp))

    this.receiptId          = data.receipt_id ?? ''
    this.decision           = data.decision ?? ''
    this.timestamp          = data.timestamp ?? ''
    this.domain             = data.domain ?? ''
    this.asset              = data.asset ?? ''
    this.policyVersion      = data.policy_version ?? ''
    this.contentHash        = data.content_hash ?? ''
    this.signature          = data.signature ?? null
    this.signatureAlgorithm = data.signature_algorithm ?? data.integrity?.algorithm ?? null
    this.publicKey          = data.public_key ?? null
    this.jurisdiction       = data.jurisdiction ?? data.authority_binding?.jurisdiction ?? null
    this.checkpointsPassed  = data.checkpoints_passed ?? cps.filter(c => c.passed).length
    this.checkpointsBlocked = data.checkpoints_blocked ?? cps.filter(c => !c.passed).length
    this.vetoChain          = data.veto_chain ?? []
    this.checkpoints        = cps
    this.verifyUrl          = data.verify_url ?? null
    this.raw                = data
  }

  get approved(): boolean { return this.decision === 'APPROVED' }
  get blocked(): boolean  { return this.decision === 'BLOCKED'  }
  get held(): boolean     { return this.decision === 'HOLD'     }

  toString(): string {
    const icon = this.approved ? '✅' : this.blocked ? '🚫' : '⏸️'
    return (
      `${icon} ${this.decision} | ${this.receiptId} | ` +
      `${this.checkpointsPassed}/11 gates passed | ` +
      `sig: ${this.signatureAlgorithm ?? 'N/A'}`
    )
  }

  toJSON(): GovernanceReceiptData {
    return this.raw
  }
}
