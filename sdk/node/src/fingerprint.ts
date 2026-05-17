/**
 * OMNIX Cross-Language Fingerprint Utilities
 * ===========================================
 * Document ID : OMNIX-SDK-FINGERPRINT-NODE-1.0
 * Invariants  : FVP-INV-007 · ATF-INV-006
 * ADR refs    : ADR-167 §2.1 · RFC-ATF-3 · ADR-157 rev.2
 *
 * Implements the canonical fingerprint and JSON serialization algorithms
 * that every OMNIX SDK must reproduce identically regardless of language.
 *
 * These utilities are validated against sdk/conformance_vectors.json.
 * Any modification that changes output for existing vectors is a
 * PROTOCOL VIOLATION — update the vectors file and rev the schema version.
 *
 * Usage:
 *   import { computeKeyFingerprint, canonicalJson, canonicalJsonSha256 } from 'omnix-quantum/fingerprint'
 */

import { createHash } from 'node:crypto'

// ---------------------------------------------------------------------------
// FVP-INV-007 — Key fingerprint algorithm
// ---------------------------------------------------------------------------

/**
 * Compute the OMNIX canonical public-key fingerprint.
 *
 * Algorithm (identical to Python forensic_blueprint.py L154):
 *   fingerprint = "sha256:" + sha256(base64decode(keyB64)).hexdigest()
 *
 * @param keyB64 - Base64-encoded raw public key bytes (standard or URL-safe encoding)
 * @returns Fingerprint string of the form "sha256:<64-char-lowercase-hex>"
 *
 * @example
 * // Dilithium-3 platform key fingerprint
 * const fp = computeKeyFingerprint(platformKeyB64)
 * // => "sha256:66f8cec4c8e9282bb2e275822eacd0ef3b6ad7579f6da80d7bc935226dffbe8b"
 */
export function computeKeyFingerprint(keyB64: string): string {
  const rawBytes = Buffer.from(keyB64, 'base64')
  const hexDigest = createHash('sha256').update(rawBytes).digest('hex')
  return `sha256:${hexDigest}`
}

// ---------------------------------------------------------------------------
// ATF-INV-006 — Canonical JSON serialization
// ---------------------------------------------------------------------------

/**
 * Serialize an object to canonical JSON.
 *
 * Rules (must match Python json.dumps exactly):
 *   1. Object keys sorted A→Z at every nesting level (recursive)
 *   2. No whitespace around `:` or `,`  (compact separators)
 *   3. Unicode characters preserved as-is, NOT escaped as \uXXXX
 *   4. Arrays preserve insertion order (no sorting of array elements)
 *
 * @param obj - Any JSON-serializable value
 * @returns Canonical JSON string
 *
 * @example
 * canonicalJson({ z: 1, a: 2 })  // => '{"a":2,"z":1}'
 * canonicalJson({ files: { b: 'h2', a: 'h1' } })  // => '{"files":{"a":"h1","b":"h2"}}'
 */
export function canonicalJson(obj: unknown): string {
  return _serialize(obj)
}

/**
 * Compute SHA-256 hex digest of the canonical JSON UTF-8 encoding of obj.
 *
 * This is the hash used for OEP manifest integrity (ATF-INV-006).
 *
 * @param obj - Any JSON-serializable value
 * @returns Lowercase SHA-256 hex string (64 chars, no prefix)
 */
export function canonicalJsonSha256(obj: unknown): string {
  const canonical = canonicalJson(obj)
  return createHash('sha256').update(canonical, 'utf8').digest('hex')
}

// ---------------------------------------------------------------------------
// Internal recursive serializer
// ---------------------------------------------------------------------------

function _serialize(value: unknown): string {
  if (value === null)             return 'null'
  if (typeof value === 'boolean') return value ? 'true' : 'false'
  if (typeof value === 'number')  return JSON.stringify(value)
  if (typeof value === 'string')  return _encodeString(value)

  if (Array.isArray(value)) {
    return '[' + value.map(_serialize).join(',') + ']'
  }

  if (typeof value === 'object') {
    const obj = value as Record<string, unknown>
    const sortedKeys = Object.keys(obj).sort()
    const pairs = sortedKeys.map(k => _encodeString(k) + ':' + _serialize(obj[k]))
    return '{' + pairs.join(',') + '}'
  }

  // Fallback for undefined, functions, symbols — JSON spec excludes these
  return 'null'
}

/**
 * Encode a string value with Unicode preservation (ensure_ascii=False equivalent).
 *
 * JSON.stringify in Node.js naturally preserves non-ASCII characters without
 * escaping them to \uXXXX sequences, matching Python's ensure_ascii=False.
 * This is tested by CJ-004 (em-dash in "OMNIX QUANTUM LTD — UAE").
 */
function _encodeString(s: string): string {
  return JSON.stringify(s)
}

// ---------------------------------------------------------------------------
// Fingerprint verification utilities
// ---------------------------------------------------------------------------

/**
 * Verify that a provided fingerprint matches the expected fingerprint for a key.
 *
 * @param keyB64        - Base64-encoded raw public key bytes
 * @param fingerprint   - Expected fingerprint string ("sha256:<hex>")
 * @returns true if the fingerprint matches, false otherwise
 */
export function verifyKeyFingerprint(keyB64: string, fingerprint: string): boolean {
  return computeKeyFingerprint(keyB64) === fingerprint
}

/**
 * Parse a "sha256:<hex>" fingerprint string into its components.
 *
 * @param fingerprint - Full fingerprint string
 * @returns { algorithm: string, hex: string } or null if malformed
 */
export function parseFingerprint(
  fingerprint: string
): { algorithm: string; hex: string } | null {
  const match = fingerprint.match(/^(sha256):([0-9a-f]{64})$/)
  if (!match) return null
  return { algorithm: match[1], hex: match[2] }
}
