/**
 * OMNIX Node.js SDK — v2.0.0
 * ===========================
 *
 * Official client library for the OMNIX Decision Governance API.
 * Production endpoint: https://omnixquantum.net
 *
 * Zero external dependencies. Node.js 14+.
 *
 * @example
 * const OmnixClient = require('./omnix_sdk');
 *
 * const client = new OmnixClient({ apiKey: 'OMNIX-your-key-here' });
 *
 * // 1. Govern a decision
 * const receipt = await client.evaluate({
 *   signal_integrity: 75, probability_score: 68,
 *   risk_exposure: 35,    signal_coherence: 72,
 *   trend_persistence: 60,stress_resilience: 55,
 *   logic_consistency: 70,temporal_coherence: 65,
 *   domain: 'trading', asset: 'BTC/USD',
 *   scenario: 'Long position — 2% capital',
 * });
 * console.log(receipt.decision);   // APPROVED | BLOCKED | HOLD
 * console.log(receipt.receipt_id); // OMNIX-a3f8e2...
 *
 * // 2. Log the execution result
 * const execReceipt = await client.execute({
 *   decisionReceiptId: receipt.receipt_id,
 *   orderId:           'ORD-001',
 *   symbol:            'BTC/USD',
 *   side:              'BUY',
 *   sizeUsd:           10_000,
 *   finalStatus:       'FILLED',
 *   executedPrice:     65_100,
 *   filledQuantity:    0.15,
 * });
 *
 * // 3. Verify receipt integrity (PQC)
 * const verified = await client.verify(receipt.receipt_id);
 *
 * // 4. Issue a W3C Verifiable Credential
 * const vc = await client.getVc(receipt.receipt_id);
 *
 * // 5. Revoke (admin only)
 * await client.revoke(receipt.receipt_id, 'Assumption invalidated by AVM');
 *
 * @module omnix-sdk
 * @version 2.0.0
 * @author OMNIX Quantum Ltd — Harold Alberto Nunes Rodelo
 * @see ADR-132 — SDK Public API Surface
 */

'use strict';

const https = require('https');
const http  = require('http');
const { URL } = require('url');

const SDK_VERSION = '2.0.0';

const REQUIRED_SIGNALS = [
  'signal_integrity', 'probability_score', 'risk_exposure',
  'signal_coherence', 'trend_persistence', 'stress_resilience',
  'logic_consistency', 'temporal_coherence',
];

const EXECUTION_STATUSES  = ['FILLED', 'PARTIAL', 'FAILED'];
const SUPPORTED_DOMAINS   = [
  'trading', 'credit', 'insurance', 'robotics',
  'medical', 'energy', 'real_estate', 'stablecoin', 'agents',
];

// ── Exception hierarchy ──────────────────────────────────────────────────────

class OmnixError extends Error {
  constructor(message, statusCode = null) {
    super(message);
    this.name       = 'OmnixError';
    this.statusCode = statusCode;
  }
}

class OmnixAuthError extends OmnixError {
  constructor(message) {
    super(message, 401);
    this.name = 'OmnixAuthError';
  }
}

class OmnixNotFoundError extends OmnixError {
  constructor(message) {
    super(message, 404);
    this.name = 'OmnixNotFoundError';
  }
}

class OmnixValidationError extends OmnixError {
  constructor(message) {
    super(message, 422);
    this.name = 'OmnixValidationError';
  }
}

class OmnixRateLimitError extends OmnixError {
  constructor(message, retryAfter = 60) {
    super(message, 429);
    this.name       = 'OmnixRateLimitError';
    this.retryAfter = retryAfter;
  }
}

class OmnixTimeoutError extends OmnixError {
  constructor(message = 'Request timed out') {
    super(message, 408);
    this.name = 'OmnixTimeoutError';
  }
}

class OmnixServerError extends OmnixError {
  constructor(message, statusCode = 500) {
    super(message, statusCode);
    this.name = 'OmnixServerError';
  }
}

class OmnixAPIError extends OmnixError {
  constructor(message, statusCode = null) {
    super(message, statusCode);
    this.name = 'OmnixAPIError';
  }
}

// ── Client ────────────────────────────────────────────────────────────────────

class OmnixClient {
  /**
   * Create an OMNIX API client.
   *
   * @param {object}  options
   * @param {string}  [options.apiKey]       - API key (OMNIX-<40 chars>).
   *                                          Falls back to OMNIX_API_KEY env var.
   * @param {string}  [options.baseUrl]      - API base URL. Default: https://omnixquantum.net.
   *                                          Override via OMNIX_BASE_URL env var.
   * @param {number}  [options.timeout]      - Per-request timeout in ms. Default: 30000.
   * @param {number}  [options.maxRetries]   - Max retries on transient errors. Default: 3.
   * @param {number}  [options.retryBackoff] - Base backoff in ms (exponential). Default: 1000.
   *
   * @throws {OmnixAuthError}      If no API key is found.
   * @throws {OmnixValidationError} If API key format is invalid.
   *
   * @example
   * // Via constructor
   * const client = new OmnixClient({ apiKey: 'OMNIX-your-key-here' });
   *
   * // Via environment variable
   * process.env.OMNIX_API_KEY = 'OMNIX-your-key-here';
   * const client = new OmnixClient();
   */
  constructor({
    apiKey       = process.env.OMNIX_API_KEY || '',
    baseUrl      = process.env.OMNIX_BASE_URL || 'https://omnixquantum.net',
    timeout      = 30_000,
    maxRetries   = 3,
    retryBackoff = 1_000,
  } = {}) {
    if (!apiKey) {
      throw new OmnixAuthError(
        'No API key provided. Pass apiKey option or set the OMNIX_API_KEY environment variable.'
      );
    }
    if (!apiKey.startsWith('OMNIX-')) {
      throw new OmnixValidationError(
        `Invalid API key format. Expected OMNIX-<key>, got: ${apiKey.slice(0, 10)}...`
      );
    }
    this._apiKey       = apiKey;
    this._baseUrl      = baseUrl.replace(/\/$/, '');
    this._timeout      = timeout;
    this._maxRetries   = maxRetries;
    this._retryBackoff = retryBackoff;
  }

  toString() {
    const preview = this._apiKey.slice(0, 12) + '...';
    return `OmnixClient(apiKey=${preview}, baseUrl=${this._baseUrl})`;
  }

  // ── Internal HTTP layer ────────────────────────────────────────────────────

  /**
   * Execute an authenticated HTTP request with automatic retry.
   *
   * @private
   * @param {string}  method
   * @param {string}  path
   * @param {object}  [body=null]
   * @param {object}  [params=null]
   * @returns {Promise<object>}
   */
  _request(method, path, body = null, params = null) {
    const makeAttempt = (attempt) => new Promise((resolve, reject) => {
      let query = '';
      if (params) {
        const qs = Object.entries(params)
          .filter(([, v]) => v !== null && v !== undefined)
          .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
          .join('&');
        if (qs) query = '?' + qs;
      }

      const url      = new URL(`${this._baseUrl}${path}${query}`);
      const isHttps  = url.protocol === 'https:';
      const lib      = isHttps ? https : http;
      const payload  = body ? JSON.stringify(body) : null;

      const options = {
        hostname : url.hostname,
        port     : url.port || (isHttps ? 443 : 80),
        path     : url.pathname + url.search,
        method,
        headers  : {
          'X-API-Key'   : this._apiKey,
          'Content-Type': 'application/json',
          'Accept'      : 'application/json',
          'User-Agent'  : `omnix-node-sdk/${SDK_VERSION}`,
          ...(payload ? { 'Content-Length': Buffer.byteLength(payload) } : {}),
        },
        timeout: this._timeout,
      };

      const req = lib.request(options, (res) => {
        let data = '';
        res.on('data', (chunk) => { data += chunk; });
        res.on('end', () => {
          let parsed;
          try { parsed = JSON.parse(data); } catch { parsed = { raw: data }; }

          const status = res.statusCode;

          if (status === 401 || status === 403) {
            return reject(new OmnixAuthError(
              `Authentication failed (${status}): ${parsed.error || 'Invalid API key'}`
            ));
          }
          if (status === 404) {
            return reject(new OmnixNotFoundError(
              `Not found: ${parsed.error || 'Resource does not exist'}`
            ));
          }
          if (status === 422) {
            return reject(new OmnixValidationError(
              `Validation error: ${parsed.error || 'Invalid request body'}`
            ));
          }
          if (status === 429) {
            const retryAfter = parseInt(res.headers['retry-after'] || '60', 10);
            if (attempt < this._maxRetries) {
              const delay = Math.min(retryAfter * 1000, this._retryBackoff * Math.pow(2, attempt));
              return setTimeout(() => makeAttempt(attempt + 1).then(resolve).catch(reject), delay);
            }
            return reject(new OmnixRateLimitError(
              `Rate limit exceeded. Retry after ${retryAfter}s.`, retryAfter
            ));
          }
          if (status === 503 && attempt < this._maxRetries) {
            const delay = this._retryBackoff * Math.pow(2, attempt);
            return setTimeout(() => makeAttempt(attempt + 1).then(resolve).catch(reject), delay);
          }
          if (status >= 500) {
            return reject(new OmnixServerError(
              `Server error ${status}: ${parsed.error || 'Unexpected error'}`, status
            ));
          }
          if (status >= 400) {
            return reject(new OmnixAPIError(
              `API error ${status}: ${parsed.error || 'Unknown error'}`, status
            ));
          }
          resolve(parsed);
        });
      });

      req.on('timeout', () => {
        req.destroy();
        reject(new OmnixTimeoutError(`Request timed out after ${this._timeout}ms`));
      });

      req.on('error', (err) => {
        if (attempt < this._maxRetries) {
          const delay = this._retryBackoff * Math.pow(2, attempt);
          return setTimeout(() => makeAttempt(attempt + 1).then(resolve).catch(reject), delay);
        }
        reject(new OmnixAPIError(`Network error: ${err.message}`));
      });

      if (payload) req.write(payload);
      req.end();
    });

    return makeAttempt(0);
  }

  // ── 1. Governance — evaluate ───────────────────────────────────────────────

  /**
   * Submit a decision for governance evaluation.
   *
   * OMNIX runs the decision through 11 sequential checkpoints covering
   * epistemic validity, coherence, regulatory compliance, and risk limits.
   * The result is a PQC-signed (Dilithium-3) governance receipt.
   *
   * @param {object}  signals                  - Decision signals
   * @param {number}  signals.signal_integrity  - Input data quality (0-100)
   * @param {number}  signals.probability_score - Decision confidence (0-100)
   * @param {number}  signals.risk_exposure     - Risk level — lower is safer (0-100)
   * @param {number}  signals.signal_coherence  - Internal consistency (0-100)
   * @param {number}  signals.trend_persistence - Trend alignment (0-100)
   * @param {number}  signals.stress_resilience - Stress resilience (0-100)
   * @param {number}  signals.logic_consistency - Logical coherence (0-100)
   * @param {number}  signals.temporal_coherence- Time-context validity (0-100)
   * @param {string}  [signals.domain]          - 'trading'|'credit'|'insurance'|etc.
   * @param {string}  [signals.asset]           - Asset/entity identifier
   * @param {string}  [signals.scenario]        - Human-readable description
   *
   * @returns {Promise<object>} Receipt with decision, receipt_id, pqc_signed
   * @throws  {OmnixValidationError} If required signal fields are missing
   *
   * @example
   * const receipt = await client.evaluate({
   *   signal_integrity: 75, probability_score: 68,
   *   risk_exposure: 35,    signal_coherence: 72,
   *   trend_persistence: 60,stress_resilience: 55,
   *   logic_consistency: 70,temporal_coherence: 65,
   *   domain: 'trading', asset: 'ETH/USD',
   *   scenario: 'Long position on breakout — 1.5% capital',
   * });
   * if (receipt.decision === 'APPROVED') {
   *   await placeOrder(receipt.receipt_id);
   * }
   */
  evaluate(signals) {
    const missing = REQUIRED_SIGNALS.filter((f) => !(f in signals));
    if (missing.length > 0) {
      return Promise.reject(new OmnixValidationError(
        `Missing required signal fields: ${missing.join(', ')}. ` +
        'All 8 numeric fields (0–100) are required.'
      ));
    }
    return this._request('POST', '/api/governance/evaluate', signals);
  }

  // ── 2. Execution integrity ─────────────────────────────────────────────────

  /**
   * Log the result of a trade execution and bind it to a governance decision.
   *
   * Seals the decision→execution audit chain (ADR-131).
   * OMNIX computes latency_ms, slippage_bps, fill_ratio, and receipt_hash.
   *
   * @param {object}  options
   * @param {string}  options.decisionReceiptId - receipt_id from evaluate()
   * @param {string}  options.orderId           - Exchange order reference
   * @param {string}  options.symbol            - Instrument (e.g. 'BTC/USD')
   * @param {string}  options.side              - 'BUY' or 'SELL'
   * @param {number}  options.sizeUsd           - Notional value in USD
   * @param {string}  options.finalStatus       - 'FILLED' | 'PARTIAL' | 'FAILED'
   * @param {number}  [options.executedPrice]   - Actual fill price
   * @param {number}  [options.filledQuantity]  - Units filled
   * @param {number}  [options.requestedPrice]  - Limit price (omit for MARKET)
   * @param {number}  [options.requestedQuantity] - Units requested
   * @param {string}  [options.executionStyle]  - 'MARKET'|'LIMIT'|'TWAP'|etc.
   * @param {object}  [options.exchangeResponse]- Raw exchange response
   * @param {string}  [options.failureReason]   - Required if finalStatus='FAILED'
   *
   * @returns {Promise<object>} Sealed execution receipt
   * @throws  {OmnixValidationError} If finalStatus is invalid or required fields are missing
   *
   * @example
   * const receipt  = await client.evaluate(signals);
   * const response = await exchange.createOrder('BTC/USD', 'market', 'buy', 0.15);
   * const exec = await client.execute({
   *   decisionReceiptId: receipt.receipt_id,
   *   orderId:           response.id,
   *   symbol:            'BTC/USD',
   *   side:              'BUY',
   *   sizeUsd:           10_000,
   *   finalStatus:       'FILLED',
   *   executedPrice:     response.average,
   *   filledQuantity:    response.filled,
   *   exchangeResponse:  response,
   * });
   */
  execute({
    decisionReceiptId,
    orderId,
    symbol,
    side,
    sizeUsd,
    finalStatus,
    executedPrice     = null,
    filledQuantity    = null,
    requestedPrice    = null,
    requestedQuantity = null,
    executionStyle    = 'MARKET',
    exchangeResponse  = {},
    failureReason     = '',
  }) {
    if (!EXECUTION_STATUSES.includes(finalStatus)) {
      return Promise.reject(new OmnixValidationError(
        `Invalid finalStatus: '${finalStatus}'. Must be one of: ${EXECUTION_STATUSES.join(', ')}`
      ));
    }
    if (finalStatus === 'FAILED' && !failureReason) {
      return Promise.reject(new OmnixValidationError(
        "failureReason is required when finalStatus is 'FAILED'."
      ));
    }
    if (['FILLED', 'PARTIAL'].includes(finalStatus) && executedPrice === null) {
      return Promise.reject(new OmnixValidationError(
        "executedPrice is required when finalStatus is 'FILLED' or 'PARTIAL'."
      ));
    }
    return this._request('POST', '/api/execution/receipts', {
      decision_receipt_id : decisionReceiptId,
      order_id            : orderId,
      symbol,
      side                : side.toUpperCase(),
      size_usd            : sizeUsd,
      final_status        : finalStatus,
      executed_price      : executedPrice,
      filled_quantity     : filledQuantity,
      requested_price     : requestedPrice,
      requested_quantity  : requestedQuantity,
      execution_style     : executionStyle,
      exchange_response   : exchangeResponse,
      failure_reason      : failureReason,
    });
  }

  /**
   * Retrieve a specific execution receipt by its ID.
   *
   * @param {string} receiptId - Execution receipt ID returned by execute()
   * @returns {Promise<object>} Full execution receipt with latency, slippage, audit_trail
   */
  getExecutionReceipt(receiptId) {
    return this._request('GET', `/api/execution/receipts/${receiptId}`);
  }

  // ── 3. Receipts ────────────────────────────────────────────────────────────

  /**
   * Retrieve a specific governance receipt by ID.
   *
   * @param {string} receiptId - Receipt ID from evaluate()
   * @returns {Promise<object>} Full receipt with checkpoints and PQC signature
   * @throws  {OmnixNotFoundError} If receipt not found or not owned by your key
   */
  getReceipt(receiptId) {
    return this._request('GET', `/api/governance/receipts/${receiptId}`);
  }

  /**
   * List your governance receipts (paginated, most recent first).
   *
   * @param {object} [options]
   * @param {number} [options.page=1]       - Page number (1-indexed)
   * @param {number} [options.perPage=20]   - Results per page (max 100)
   * @param {string} [options.domain]       - Filter by domain
   * @param {string} [options.asset]        - Filter by asset
   * @param {string} [options.decision]     - Filter: 'APPROVED'|'BLOCKED'|'HOLD'
   * @returns {Promise<object>} { receipts, total, page, per_page }
   */
  listReceipts({ page = 1, perPage = 20, domain = null, asset = null, decision = null } = {}) {
    return this._request('GET', '/api/governance/receipts', null, {
      page, per_page: perPage, domain, asset, decision,
    });
  }

  // ── 4. Verification ────────────────────────────────────────────────────────

  /**
   * Cryptographically verify a governance receipt (PQC Dilithium-3).
   *
   * @param {string} receiptId - Receipt to verify
   * @returns {Promise<object>} { valid, signature_valid, hash_valid, tamper_detected, checks }
   *
   * @example
   * const result = await client.verify('OMNIX-a3f8e2...');
   * if (!result.valid) throw new Error('Receipt integrity compromised');
   */
  verify(receiptId) {
    return this._request('POST', '/api/trust/verify', { receipt_id: receiptId });
  }

  // ── 5. Verifiable Credentials ──────────────────────────────────────────────

  /**
   * Issue a W3C Verifiable Credential for a governance receipt.
   *
   * Compatible with EUDI wallets, eIDAS 2.0, and any W3C VC verifier.
   *
   * @param {string}  receiptId             - Governance receipt to wrap in a VC
   * @param {object}  [humanSigner=null]    - Human accountability block (ADR-130 §7)
   * @returns {Promise<object>} W3C Verifiable Credential (JSON-LD)
   *
   * @example
   * const vc = await client.getVc(receipt.receipt_id);
   * console.log(vc.proof.type);         // 'Dilithium3Signature2024'
   * console.log(vc.credentialStatus);   // StatusList2021 revocation entry
   */
  getVc(receiptId, humanSigner = null) {
    const body = { receipt_id: receiptId };
    if (humanSigner) body.human_signer = humanSigner;
    return this._request('POST', '/api/governance/receipt/vc', body);
  }

  /**
   * Check the current trust status of a Verifiable Credential.
   *
   * @param {string} receiptId
   * @returns {Promise<object>} { status, receipt_id, revoked_at?, reason? }
   */
  getVcStatus(receiptId) {
    return this._request('GET', `/api/trust/vc-status/${receiptId}`);
  }

  /**
   * Retrieve the W3C StatusList2021 revocation bitstring.
   *
   * @returns {Promise<object>} { encodedList, type, statusPurpose, total_revoked }
   */
  getStatusList() {
    return this._request('GET', '/api/trust/status-list');
  }

  // ── 6. Revocation (admin only) ─────────────────────────────────────────────

  /**
   * Revoke a Verifiable Credential permanently. Admin API key required.
   *
   * @param {string} receiptId - Receipt whose VC to revoke
   * @param {string} reason    - Revocation reason (minimum 10 characters)
   * @returns {Promise<object>} { revoked, receipt_id, revoked_at }
   * @throws  {OmnixAuthError}      If your key lacks admin permissions
   * @throws  {OmnixValidationError} If reason is < 10 characters
   *
   * @example
   * await client.revoke(
   *   'OMNIX-a3f8e2...',
   *   'AVM detected assumption drift — domain suspended'
   * );
   */
  revoke(receiptId, reason) {
    if (!reason || reason.length < 10) {
      return Promise.reject(new OmnixValidationError(
        'Revocation reason must be at least 10 characters.'
      ));
    }
    return this._request('POST', `/api/trust/revoke/${receiptId}`, { reason });
  }

  /**
   * Reinstate a revoked or suspended VC. Admin API key required.
   *
   * @param {string} receiptId - Receipt to reinstate
   * @param {string} reason    - Reinstatement justification (minimum 20 characters)
   * @returns {Promise<object>} { reinstated, receipt_id, reinstated_at }
   * @throws  {OmnixValidationError} If reason is < 20 characters
   */
  reinstate(receiptId, reason) {
    if (!reason || reason.length < 20) {
      return Promise.reject(new OmnixValidationError(
        'Reinstatement reason must be at least 20 characters.'
      ));
    }
    return this._request('POST', `/api/trust/reinstate/${receiptId}`, { reason });
  }

  // ── 7. Utility ─────────────────────────────────────────────────────────────

  /**
   * Check the health of the OMNIX API and its components.
   *
   * @returns {Promise<object>} { status, components, version, timestamp }
   */
  health() {
    return this._request('GET', '/api/health');
  }

  /**
   * Return the governance signal schema documentation.
   *
   * @returns {Promise<object>} Schema with field descriptions, types, and ranges
   */
  getSchema() {
    return this._request('GET', '/api/governance/schema');
  }

  /**
   * Return the full regulatory frameworks catalog.
   *
   * @returns {Promise<object>} Frameworks grouped by domain and compliance level
   */
  getRegulatoryFrameworks() {
    return this._request('GET', '/api/governance/regulatory/catalog');
  }

  /**
   * Generate a governance due diligence report.
   *
   * @param {string} [format='json'] - 'json' or 'pdf'
   * @returns {Promise<object>} Governance statistics, regulatory alignment, receipt samples
   * @throws  {OmnixValidationError} If format is not 'json' or 'pdf'
   */
  getDueDiligenceReport(format = 'json') {
    if (!['json', 'pdf'].includes(format)) {
      return Promise.reject(new OmnixValidationError(
        `Invalid format: '${format}'. Must be 'json' or 'pdf'.`
      ));
    }
    return this._request('GET', '/api/governance/due-diligence-report', null, { format });
  }
}

// ── Exports ───────────────────────────────────────────────────────────────────

OmnixClient.OmnixError          = OmnixError;
OmnixClient.OmnixAuthError      = OmnixAuthError;
OmnixClient.OmnixNotFoundError  = OmnixNotFoundError;
OmnixClient.OmnixValidationError = OmnixValidationError;
OmnixClient.OmnixRateLimitError = OmnixRateLimitError;
OmnixClient.OmnixTimeoutError   = OmnixTimeoutError;
OmnixClient.OmnixServerError    = OmnixServerError;
OmnixClient.OmnixAPIError       = OmnixAPIError;
OmnixClient.SDK_VERSION         = SDK_VERSION;
OmnixClient.REQUIRED_SIGNALS    = REQUIRED_SIGNALS;
OmnixClient.SUPPORTED_DOMAINS   = SUPPORTED_DOMAINS;

module.exports = OmnixClient;
