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

  // ── Oscillation Insight Engine (ADR-134) ─────────────────────────────────

  /**
   * Fetch governance oscillation analytics for a domain.
   * No authentication required — public analytics endpoint.
   *
   * @param domain    Governance domain (trading | insurance | energy | …)
   * @param view      "full" | "profile" | "phases" | "asymmetry" | "dampening"
   * @param numWeeks  Analysis window 1–26 weeks (default 12)
   * ADR-134.
   */
  async oscillation(
    domain:   string,
    view     = 'full',
    numWeeks = 12,
  ): Promise<Record<string, unknown>> {
    return this.get(
      `/api/analytics/oscillation?domain=${domain}&view=${view}&num_weeks=${numWeeks}`,
      false,
    )
  }

  // ── Anomaly Response Engine (ADR-129) ────────────────────────────────────

  /**
   * Run a full anomaly detection and response cycle for a domain.
   * ADR-129.
   */
  async anomalyResponse(domain: string): Promise<Record<string, unknown>> {
    return this.post('/api/governance/anomaly/response', { domain })
  }

  /**
   * List all ACTIVE anomaly recommendations.
   * ADR-129.
   */
  async anomalyActive(domain?: string): Promise<Record<string, unknown>> {
    const q = domain ? `?domain=${domain}` : ''
    return this.get(`/api/governance/anomaly/active${q}`)
  }

  /**
   * Summary of anomaly recommendations by status and action code.
   * ADR-129.
   */
  async anomalySummary(domain?: string): Promise<Record<string, unknown>> {
    const q = domain ? `?domain=${domain}` : ''
    return this.get(`/api/governance/anomaly/summary${q}`)
  }

  /**
   * Acknowledge an active anomaly recommendation.
   * ADR-129.
   */
  async anomalyAcknowledge(recId: string, note = ''): Promise<Record<string, unknown>> {
    return this.post(`/api/governance/anomaly/${recId}/acknowledge`, { acknowledge_note: note })
  }

  /**
   * Resolve an active or acknowledged anomaly recommendation.
   * ADR-129.
   */
  async anomalyResolve(recId: string, note = ''): Promise<Record<string, unknown>> {
    return this.post(`/api/governance/anomaly/${recId}/resolve`, { resolution_note: note })
  }

  // ── Execution Integrity Layer (ADR-131) ──────────────────────────────────

  /**
   * Capture execution intent BEFORE placing a trade.
   *
   * If this call fails (503), the trade must NOT proceed.
   * This is an ADR-131 hard invariant.
   * ADR-131.
   */
  async executionIntent(opts: {
    orderId:           string
    decisionReceiptId: string
    asset:             string
    domain:            string
    direction:         string
    sizeUsd:           number
  }): Promise<Record<string, unknown>> {
    return this.post('/api/governance/execution/intent', {
      order_id:            opts.orderId,
      decision_receipt_id: opts.decisionReceiptId,
      asset:               opts.asset,
      domain:              opts.domain,
      direction:           opts.direction,
      size_usd:            opts.sizeUsd,
    })
  }

  /**
   * List execution receipts.
   * ADR-131.
   */
  async executionReceipts(opts: {
    decisionReceiptId?: string
    status?:            string
    limit?:             number
    offset?:            number
  } = {}): Promise<Record<string, unknown>> {
    const p = new URLSearchParams()
    p.set('limit',  String(opts.limit  ?? 20))
    p.set('offset', String(opts.offset ?? 0))
    if (opts.decisionReceiptId) p.set('decision_receipt_id', opts.decisionReceiptId)
    if (opts.status)            p.set('status', opts.status)
    return this.get(`/api/governance/execution/receipts?${p}`)
  }

  /**
   * Fetch a single execution receipt by order ID.
   * ADR-131.
   */
  async executionReceipt(orderId: string): Promise<Record<string, unknown>> {
    return this.get(`/api/governance/execution/receipts/${orderId}`)
  }

  // ── Breach Containment Engine (ADR-142) ──────────────────────────────────

  /**
   * Get current containment status.
   * No authentication required. Fail-closed: DB error → is_contained=true.
   * ADR-142.
   */
  async breachStatus(): Promise<Record<string, unknown>> {
    return this.get('/api/governance/breach/status', false)
  }

  /**
   * Activate breach containment. Blocks ALL governance decisions immediately.
   *
   * WARNING: After activation, all governance decisions return BLOCKED
   * until breachRelease() is called with human authorization.
   *
   * @param triggerCode MANUAL_OPERATOR | TIMING_ANOMALY | CHECKSUM_MISMATCH |
   *                    PROCESS_ANOMALY | REPEATED_AUTH_FAILURE | API_TRIGGERED
   * @param severity    CRITICAL | HIGH | MEDIUM
   * @param summary     Human-readable description of the threat
   * @param triggeredBy Operator/system identifier
   * @param detail      Optional extra context
   * ADR-142.
   */
  async breachActivate(opts: {
    triggerCode:  string
    severity:     string
    summary:      string
    triggeredBy?: string
    detail?:      Record<string, unknown>
  }): Promise<Record<string, unknown>> {
    return this.post('/api/governance/breach/activate', {
      trigger_code:  opts.triggerCode,
      severity:      opts.severity,
      summary:       opts.summary,
      triggered_by:  opts.triggeredBy ?? 'node-sdk',
      detail:        opts.detail ?? {},
    })
  }

  /**
   * Release an active containment event. Requires human authorization.
   * ADR-142.
   */
  async breachRelease(opts: {
    eventId:      string
    authorizedBy: string
    releaseNote:  string
  }): Promise<Record<string, unknown>> {
    return this.post('/api/governance/breach/release', {
      event_id:      opts.eventId,
      authorized_by: opts.authorizedBy,
      release_note:  opts.releaseNote,
    })
  }

  /**
   * Run automated threat assessment. Does NOT auto-activate containment.
   * If result.recommended_action === 'ACTIVATE_CONTAINMENT', call breachActivate().
   * ADR-142.
   */
  async breachAssess(opts: {
    latencyMs?:          number
    expectedLatencyMs?:  number
    latencySigma?:       number
    avmSnapshotHash?:    string
    expectedHash?:       string
    authFailureCount?:   number
    authFailureWindow?:  number
  } = {}): Promise<Record<string, unknown>> {
    return this.post('/api/governance/breach/assess', {
      latency_ms:           opts.latencyMs,
      expected_latency_ms:  opts.expectedLatencyMs,
      latency_sigma:        opts.latencySigma,
      avm_snapshot_hash:    opts.avmSnapshotHash,
      expected_hash:        opts.expectedHash,
      auth_failure_count:   opts.authFailureCount ?? 0,
      auth_failure_window:  opts.authFailureWindow ?? 300,
    })
  }

  /**
   * Return paginated breach event history.
   * ADR-142.
   */
  async breachHistory(opts: {
    status?: string
    limit?:  number
    offset?: number
  } = {}): Promise<Record<string, unknown>> {
    const p = new URLSearchParams()
    p.set('limit',  String(opts.limit  ?? 20))
    p.set('offset', String(opts.offset ?? 0))
    if (opts.status) p.set('status', opts.status)
    return this.get(`/api/governance/breach/history?${p}`)
  }

  // ── Multi-Domain Risk Governance (ADR-143) ───────────────────────────────

  /**
   * Evaluate multi-domain risk for a subject.
   *
   * @param subject      Entity or deployment identifier
   * @param riskSignals  Per-vector signals: financial, technical, legal, human
   * @param weights      Optional custom weights (normalized to sum to 1.0)
   * @param clientDomain Client's operational domain context
   * @param assessedBy   Operator/system identifier
   *
   * Decision logic:
   *   composite ≥ 80 → BLOCKED | 60–79 → REVIEW | < 60 → APPROVED
   *   Any single vector ≥ 95 → BLOCKED regardless of composite.
   * ADR-143.
   */
  async riskEvaluate(opts: {
    subject:       string
    riskSignals:   Record<string, Record<string, number>>
    weights?:      Record<string, number>
    clientDomain?: string
    assessedBy?:   string
  }): Promise<Record<string, unknown>> {
    const body: Record<string, unknown> = {
      subject:      opts.subject,
      risk_signals: opts.riskSignals,
      assessed_by:  opts.assessedBy ?? 'node-sdk',
    }
    if (opts.weights)      body.weights       = opts.weights
    if (opts.clientDomain) body.client_domain = opts.clientDomain
    return this.post('/api/governance/risk/evaluate', body)
  }

  /**
   * Fetch supported risk vectors, signal definitions, and thresholds.
   * No authentication required — public endpoint.
   * ADR-143.
   */
  async riskCatalog(): Promise<Record<string, unknown>> {
    return this.get('/api/governance/risk/catalog', false)
  }

  /**
   * Return paginated risk assessment history.
   * ADR-143.
   */
  async riskHistory(opts: {
    subject?:       string
    clientDomain?:  string
    decision?:      string
    limit?:         number
    offset?:        number
  } = {}): Promise<Record<string, unknown>> {
    const p = new URLSearchParams()
    p.set('limit',  String(opts.limit  ?? 20))
    p.set('offset', String(opts.offset ?? 0))
    if (opts.subject)      p.set('subject',       opts.subject)
    if (opts.clientDomain) p.set('client_domain',  opts.clientDomain)
    if (opts.decision)     p.set('decision',       opts.decision)
    return this.get(`/api/governance/risk/history?${p}`)
  }

  /**
   * Aggregate statistics across all risk assessments.
   * ADR-143.
   */
  async riskSummary(clientDomain?: string): Promise<Record<string, unknown>> {
    const q = clientDomain ? `?client_domain=${clientDomain}` : ''
    return this.get(`/api/governance/risk/summary${q}`)
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
