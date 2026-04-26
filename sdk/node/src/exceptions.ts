export class OmnixError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'OmnixError'
    Object.setPrototypeOf(this, new.target.prototype)
  }
}

export class OmnixAuthError extends OmnixError {
  constructor(message = 'Invalid or missing API key.') {
    super(message)
    this.name = 'OmnixAuthError'
  }
}

export class OmnixValidationError extends OmnixError {
  readonly errors: unknown[]
  constructor(message: string, errors: unknown[] = []) {
    super(message)
    this.name = 'OmnixValidationError'
    this.errors = errors
  }
}

/**
 * The decision was explicitly BLOCKED by OMNIX governance.
 * This is not an infrastructure error — it is a governance verdict.
 * Inspect `.receipt` for the full signed receipt and veto chain.
 */
export class OmnixGovernanceBlock extends OmnixError {
  readonly receipt: Record<string, unknown>
  constructor(receipt: Record<string, unknown>) {
    const vetoes = (receipt.veto_chain as string[]) ?? []
    super(
      `Decision BLOCKED by OMNIX governance. Veto chain: ${JSON.stringify(vetoes)}. Receipt: ${receipt.receipt_id}`,
    )
    this.name = 'OmnixGovernanceBlock'
    this.receipt = receipt
  }
}

export class OmnixRateLimitError extends OmnixError {
  readonly retryAfter: number
  constructor(retryAfter = 60) {
    super(`Rate limit exceeded. Retry after ${retryAfter}s.`)
    this.name = 'OmnixRateLimitError'
    this.retryAfter = retryAfter
  }
}

export class OmnixServerError extends OmnixError {
  readonly statusCode: number
  constructor(statusCode: number, message: string) {
    super(`Server error ${statusCode}: ${message}`)
    this.name = 'OmnixServerError'
    this.statusCode = statusCode
  }
}

export class OmnixNetworkError extends OmnixError {
  constructor(message: string) {
    super(message)
    this.name = 'OmnixNetworkError'
  }
}
