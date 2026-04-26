import https from 'https'
import http from 'http'
import { URL } from 'url'
import {
  OmnixAuthError,
  OmnixGovernanceBlock,
  OmnixNetworkError,
  OmnixRateLimitError,
  OmnixServerError,
  OmnixValidationError,
} from './exceptions.js'
import { GovernanceReceipt, GovernanceReceiptData } from './models.js'

const SDK_VERSION     = '1.0.0'
const DEFAULT_BASE    = 'https://omnixquantum.net'
const DEFAULT_TIMEOUT = 30_000

export interface OmnixClientOptions {
  apiKey: string
  baseUrl?: string
  timeout?: number
  /**
   * If true, throw OmnixGovernanceBlock when decision === 'BLOCKED'.
   * Default: false — returns the receipt normally.
   */
  raiseOnBlock?: boolean
}

export interface EvaluateOptions {
  domain: string
  asset: string
  signals: Record<string, unknown>
  context?: Record<string, unknown>
}

/**
 * OMNIX Governance SDK — Node.js / TypeScript client.
 *
 * ```typescript
 * import { OmnixClient } from 'omnix-quantum'
 *
 * const client = new OmnixClient({ apiKey: 'OMNIX-...' })
 * const receipt = await client.evaluate({
 *   domain:  'trading',
 *   asset:   'BTC/USD',
 *   signals: { price: 94200, volume: 1.5, volatility: 0.18 },
 * })
 *
 * console.log(receipt.toString())
 * // ✅ APPROVED | OMNIX-TRD-... | 11/11 gates passed | sig: Dilithium-3 (NIST FIPS 204)
 * console.log(receipt.approved)           // true
 * console.log(receipt.contentHash)        // "sha256:..."
 * console.log(receipt.signatureAlgorithm) // "Dilithium-3 (NIST FIPS 204)"
 * ```
 */
export class OmnixClient {
  private readonly apiKey:       string
  private readonly baseUrl:      string
  private readonly timeout:      number
  private readonly raiseOnBlock: boolean

  constructor(opts: OmnixClientOptions) {
    if (!opts.apiKey || !opts.apiKey.startsWith('OMNIX-')) {
      throw new OmnixAuthError(
        'Invalid API key format. Expected: OMNIX-<key>. ' +
        'Get yours at omnixquantum.net.',
      )
    }
    this.apiKey       = opts.apiKey
    this.baseUrl      = (opts.baseUrl ?? DEFAULT_BASE).replace(/\/$/, '')
    this.timeout      = opts.timeout ?? DEFAULT_TIMEOUT
    this.raiseOnBlock = opts.raiseOnBlock ?? false
  }

  // ── Public API ─────────────────────────────────────────────────────────

  /**
   * Evaluate a governance decision through OMNIX.
   *
   * @param opts.domain  - Governance domain (trading | islamic_credit | insurance | ...)
   * @param opts.asset   - Asset or subject identifier
   * @param opts.signals - Domain-specific signals
   * @param opts.context - Optional extra context
   *
   * @returns GovernanceReceipt — signed, immutable governance receipt
   */
  async evaluate(opts: EvaluateOptions): Promise<GovernanceReceipt> {
    const body: Record<string, unknown> = {
      domain:  opts.domain,
      asset:   opts.asset,
      signals: opts.signals,
    }
    if (opts.context) body.context = opts.context

    const raw = await this.post<GovernanceReceiptData>('/api/governance/evaluate', body)
    const receipt = new GovernanceReceipt(raw)

    if (this.raiseOnBlock && receipt.blocked) {
      throw new OmnixGovernanceBlock(raw as Record<string, unknown>)
    }
    return receipt
  }

  /**
   * Verify a receipt by ID — purely cryptographic, no DB access required.
   */
  async verify(receiptId: string): Promise<Record<string, unknown>> {
    return this.get(`/api/trust/verify/${receiptId}`)
  }

  /**
   * Fetch a receipt by ID from the OMNIX explorer.
   */
  async getReceipt(receiptId: string): Promise<GovernanceReceipt> {
    const raw = await this.get<GovernanceReceiptData>(`/api/explorer/receipt/${receiptId}`)
    return new GovernanceReceipt(raw)
  }

  /**
   * Fetch the public OMNIX trust registry. No authentication required.
   */
  async trustRegistry(): Promise<Record<string, unknown>> {
    return this.get('/api/trust/registry', false)
  }

  /**
   * Fetch the current OMNIX signing public key (RFC 8615 well-known).
   * No authentication required.
   */
  async publicKey(): Promise<Record<string, unknown>> {
    return this.get('/.well-known/omnix-public-key.json', false)
  }

  // ── Internal ───────────────────────────────────────────────────────────

  private headers(authenticated = true): Record<string, string> {
    const h: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept':       'application/json',
      'User-Agent':   `omnix-node-sdk/${SDK_VERSION}`,
    }
    if (authenticated) h['X-API-Key'] = this.apiKey
    return h
  }

  private post<T>(path: string, body: Record<string, unknown>): Promise<T> {
    return this.request<T>('POST', path, body, true)
  }

  private get<T>(path: string, authenticated = true): Promise<T> {
    return this.request<T>('GET', path, undefined, authenticated)
  }

  private request<T>(
    method: 'GET' | 'POST',
    path: string,
    body: Record<string, unknown> | undefined,
    authenticated: boolean,
  ): Promise<T> {
    return new Promise((resolve, reject) => {
      const url       = new URL(`${this.baseUrl}${path}`)
      const isHttps   = url.protocol === 'https:'
      const transport = isHttps ? https : http
      const bodyStr   = body ? JSON.stringify(body) : undefined

      const reqOpts: https.RequestOptions = {
        hostname: url.hostname,
        port:     url.port || (isHttps ? 443 : 80),
        path:     url.pathname + url.search,
        method,
        headers: {
          ...this.headers(authenticated),
          ...(bodyStr ? { 'Content-Length': Buffer.byteLength(bodyStr) } : {}),
        },
      }

      const req = transport.request(reqOpts, res => {
        let data = ''
        res.on('data', (chunk: Buffer) => { data += chunk.toString() })
        res.on('end', () => {
          let parsed: Record<string, unknown> = {}
          try { parsed = JSON.parse(data) } catch { /**/ }

          const status = res.statusCode ?? 0
          if (status >= 200 && status < 300) {
            return resolve(parsed as T)
          }
          if (status === 401) return reject(new OmnixAuthError('Invalid API key. Check your OMNIX-... key.'))
          if (status === 422) {
            return reject(new OmnixValidationError(
              String(parsed.detail ?? 'Validation error'),
              (parsed.errors as unknown[]) ?? [],
            ))
          }
          if (status === 429) {
            const retryAfter = parseInt(String(res.headers['retry-after'] ?? '60'), 10)
            return reject(new OmnixRateLimitError(retryAfter))
          }
          return reject(new OmnixServerError(status, String(parsed.error ?? data)))
        })
      })

      req.setTimeout(this.timeout, () => {
        req.destroy()
        reject(new OmnixNetworkError(`Request timed out after ${this.timeout}ms.`))
      })

      req.on('error', (err: Error) => {
        reject(new OmnixNetworkError(`Cannot reach OMNIX at ${this.baseUrl}: ${err.message}`))
      })

      if (bodyStr) req.write(bodyStr)
      req.end()
    })
  }
}
