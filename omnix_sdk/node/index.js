/**
 * OMNIX Node.js SDK
 * Official client library for the OMNIX Decision Governance API.
 *
 * Install: copy this file into your project or install via npm (coming soon).
 *
 * Usage:
 *   const OmnixClient = require('./omnix_sdk');
 *
 *   const client = new OmnixClient({ apiKey: 'OMNIX-your-key-here' });
 *
 *   const result = await client.evaluate({
 *     signal_integrity: 75,
 *     probability_score: 68,
 *     risk_exposure: 42,
 *     signal_coherence: 60,
 *     trend_persistence: 55,
 *     stress_resilience: 48,
 *     logic_consistency: 65,
 *     temporal_coherence: 58,
 *     domain: 'trading',
 *     asset: 'BTC/USD',
 *     scenario: 'Long position pre-execution'
 *   });
 *
 *   console.log(result.decision);    // 'APPROVED' | 'BLOCKED' | 'HOLD'
 *   console.log(result.receipt_id);  // 'OMNIX-XXXXXXXXXXXXXXXX'
 *   console.log(result.pqc_signed);  // true
 */

'use strict';

const https = require('https');
const http = require('http');
const { URL } = require('url');

class OmnixAuthError extends Error {
  constructor(message) {
    super(message);
    this.name = 'OmnixAuthError';
  }
}

class OmnixRateLimitError extends Error {
  constructor(message) {
    super(message);
    this.name = 'OmnixRateLimitError';
  }
}

class OmnixAPIError extends Error {
  constructor(message, statusCode) {
    super(message);
    this.name = 'OmnixAPIError';
    this.statusCode = statusCode;
  }
}

class OmnixClient {
  /**
   * @param {object} options
   * @param {string} options.apiKey - Your OMNIX API key (OMNIX-<40 chars>)
   * @param {string} [options.baseUrl] - API base URL. Default: https://omnixquantum.net
   * @param {number} [options.timeout] - Timeout in ms. Default: 30000
   */
  constructor({ apiKey, baseUrl = 'https://omnixquantum.net', timeout = 30000 } = {}) {
    if (!apiKey || !apiKey.startsWith('OMNIX-')) {
      throw new Error('Invalid API key format. Expected: OMNIX-<key>');
    }
    this._apiKey = apiKey;
    this._baseUrl = baseUrl.replace(/\/$/, '');
    this._timeout = timeout;
  }

  _request(method, path, body = null) {
    return new Promise((resolve, reject) => {
      const url = new URL(`${this._baseUrl}${path}`);
      const isHttps = url.protocol === 'https:';
      const lib = isHttps ? https : http;
      const payload = body ? JSON.stringify(body) : null;

      const options = {
        hostname: url.hostname,
        port: url.port || (isHttps ? 443 : 80),
        path: url.pathname + url.search,
        method,
        headers: {
          'X-API-Key': this._apiKey,
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'User-Agent': 'omnix-node-sdk/1.0',
          ...(payload ? { 'Content-Length': Buffer.byteLength(payload) } : {}),
        },
        timeout: this._timeout,
      };

      const req = lib.request(options, (res) => {
        let data = '';
        res.on('data', (chunk) => { data += chunk; });
        res.on('end', () => {
          let parsed;
          try { parsed = JSON.parse(data); } catch { parsed = { error: data }; }
          if (res.statusCode === 401) {
            return reject(new OmnixAuthError(`Authentication failed: ${parsed.error || 'Invalid API key'}`));
          }
          if (res.statusCode === 429) {
            return reject(new OmnixRateLimitError('Rate limit exceeded. Retry after 60s.'));
          }
          if (res.statusCode >= 400) {
            return reject(new OmnixAPIError(`API error ${res.statusCode}: ${parsed.error || 'Unknown error'}`, res.statusCode));
          }
          resolve(parsed);
        });
      });

      req.on('timeout', () => {
        req.destroy();
        reject(new OmnixAPIError('Request timed out', 408));
      });

      req.on('error', (err) => {
        reject(new OmnixAPIError(`Network error: ${err.message}`));
      });

      if (payload) req.write(payload);
      req.end();
    });
  }

  /**
   * Submit a decision for governance evaluation.
   *
   * @param {object} signals - Decision signals object
   * @param {number} signals.signal_integrity - Input data quality (0-100)
   * @param {number} signals.probability_score - Decision confidence (0-100)
   * @param {number} signals.risk_exposure - Risk level — lower is safer (0-100)
   * @param {number} signals.signal_coherence - Internal consistency (0-100)
   * @param {number} signals.trend_persistence - Trend alignment (0-100)
   * @param {number} signals.stress_resilience - Stress resilience (0-100)
   * @param {number} signals.logic_consistency - Logical coherence (0-100)
   * @param {number} signals.temporal_coherence - Time-context validity (0-100)
   * @param {string} [signals.domain] - "trading" | "credit" | "insurance" | "robotics"
   * @param {string} [signals.asset] - Asset/entity identifier
   * @param {string} [signals.scenario] - Human-readable decision description
   * @returns {Promise<object>} Governance receipt with decision, receipt_id, pqc_signed
   */
  evaluate(signals) {
    const required = [
      'signal_integrity', 'probability_score', 'risk_exposure',
      'signal_coherence', 'trend_persistence', 'stress_resilience',
      'logic_consistency', 'temporal_coherence',
    ];
    const missing = required.filter((f) => !(f in signals));
    if (missing.length > 0) {
      return Promise.reject(new Error(`Missing required signal fields: ${missing.join(', ')}`));
    }
    return this._request('POST', '/api/governance/evaluate', signals);
  }

  /**
   * Retrieve a specific governance receipt by ID.
   * @param {string} receiptId - Receipt identifier (OMNIX-<hex>)
   * @returns {Promise<object>} Full receipt with checkpoint results and PQC signature
   */
  getReceipt(receiptId) {
    return this._request('GET', `/api/governance/receipts/${receiptId}`);
  }

  /**
   * List your governance receipts (paginated, most recent first).
   * @param {number} [page=1]
   * @param {number} [perPage=20]
   * @returns {Promise<object>} { receipts, total, page, per_page }
   */
  listReceipts(page = 1, perPage = 20) {
    return this._request('GET', `/api/governance/receipts?page=${page}&per_page=${perPage}`);
  }

  /**
   * Return the signal schema documentation.
   * @returns {Promise<object>}
   */
  getSchema() {
    return this._request('GET', '/api/governance/schema');
  }

  /**
   * Return the full regulatory framework catalog covered by OMNIX.
   * @returns {Promise<object>}
   */
  getRegulatoryFrameworks() {
    return this._request('GET', '/api/governance/regulatory/catalog');
  }

  /**
   * Generate a governance due diligence report.
   * @param {string} [format='json'] - 'json' or 'pdf'
   * @returns {Promise<object>} Governance statistics, regulatory alignment, receipt samples
   */
  getDueDiligenceReport(format = 'json') {
    return this._request('GET', `/api/governance/due-diligence-report?format=${format}`);
  }
}

OmnixClient.OmnixAuthError = OmnixAuthError;
OmnixClient.OmnixRateLimitError = OmnixRateLimitError;
OmnixClient.OmnixAPIError = OmnixAPIError;

module.exports = OmnixClient;
