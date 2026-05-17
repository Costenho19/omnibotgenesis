/**
 * OMNIX Cross-Language Conformance Check — Node.js
 * ==================================================
 * Document ID : OMNIX-SDK-CONFORMANCE-NODE-1.0
 * Invariants  : FVP-INV-007 · ATF-INV-006
 *
 * Validates the Node.js SDK fingerprint and canonical JSON implementations
 * against the canonical cross-language conformance vectors defined in
 * sdk/conformance_vectors.json.
 *
 * Run:
 *   npx tsx sdk/node/conformance_check.ts
 *   # or from sdk/node/: npx tsx conformance_check.ts
 *
 * A compliant implementation exits with code 0 (all pass) or 1 (any fail).
 */

import { createHash } from 'node:crypto'
import { readFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

// ---------------------------------------------------------------------------
// Local implementations (mirrors fingerprint.ts — self-contained for clarity)
// ---------------------------------------------------------------------------

function computeKeyFingerprint(keyB64: string): string {
  const raw = Buffer.from(keyB64, 'base64')
  return 'sha256:' + createHash('sha256').update(raw).digest('hex')
}

function canonicalJson(obj: unknown): string {
  return _serialize(obj)
}

function canonicalJsonSha256(obj: unknown): string {
  return createHash('sha256').update(canonicalJson(obj), 'utf8').digest('hex')
}

function _serialize(value: unknown): string {
  if (value === null)             return 'null'
  if (typeof value === 'boolean') return value ? 'true' : 'false'
  if (typeof value === 'number')  return JSON.stringify(value)
  if (typeof value === 'string')  return JSON.stringify(value)
  if (Array.isArray(value))       return '[' + value.map(_serialize).join(',') + ']'
  if (typeof value === 'object') {
    const o = value as Record<string, unknown>
    const keys = Object.keys(o).sort()
    return '{' + keys.map(k => JSON.stringify(k) + ':' + _serialize(o[k])).join(',') + '}'
  }
  return 'null'
}

// ---------------------------------------------------------------------------
// Load vectors
// ---------------------------------------------------------------------------

const __filename = fileURLToPath(import.meta.url)
const __dirname  = dirname(__filename)
const vectorsPath = resolve(__dirname, '..', 'conformance_vectors.json')

interface KFPVector {
  id: string
  description: string
  key_size_bytes: number
  input_key_b64: string
  expected_fingerprint: string
  algorithm: string
}

interface CJVector {
  id: string
  description: string
  input: unknown
  expected_canonical_json: string
  expected_sha256_hex: string
}

interface Vectors {
  schema: string
  version: string
  total_vectors: number
  vectors: {
    key_fingerprint: KFPVector[]
    canonical_json:  CJVector[]
  }
}

const data: Vectors = JSON.parse(readFileSync(vectorsPath, 'utf-8'))

// ---------------------------------------------------------------------------
// Test runner
// ---------------------------------------------------------------------------

let passed = 0
let failed = 0
const failures: string[] = []

function check(id: string, description: string, actual: string, expected: string): void {
  if (actual === expected) {
    console.log(`  ✅ ${id}  ${description}`)
    passed++
  } else {
    console.error(`  ❌ ${id}  ${description}`)
    console.error(`       expected: ${expected}`)
    console.error(`       got     : ${actual}`)
    failures.push(id)
    failed++
  }
}

// ---------------------------------------------------------------------------
// FVP-INV-007 — Key fingerprint vectors
// ---------------------------------------------------------------------------

console.log('\n=== FVP-INV-007 — Key Fingerprint Conformance ===\n')

for (const v of data.vectors.key_fingerprint) {
  const result = computeKeyFingerprint(v.input_key_b64)
  check(v.id, `${v.description} (${v.key_size_bytes}B)`, result, v.expected_fingerprint)
}

// ---------------------------------------------------------------------------
// ATF-INV-006 — Canonical JSON vectors
// ---------------------------------------------------------------------------

console.log('\n=== ATF-INV-006 — Canonical JSON Conformance ===\n')

for (const v of data.vectors.canonical_json) {
  // Test canonical JSON string
  const resultJson = canonicalJson(v.input)
  check(
    `${v.id}-json`,
    `${v.description} — JSON string`,
    resultJson,
    v.expected_canonical_json,
  )

  // Test SHA-256 hash of canonical JSON
  const resultHash = canonicalJsonSha256(v.input)
  check(
    `${v.id}-hash`,
    `${v.description} — SHA-256 hash`,
    resultHash,
    v.expected_sha256_hex,
  )
}

// ---------------------------------------------------------------------------
// Summary
// ---------------------------------------------------------------------------

const total = passed + failed
console.log('\n' + '─'.repeat(60))
console.log(`OMNIX Conformance Check — Node.js`)
console.log(`Schema   : ${data.schema} v${data.version}`)
console.log(`Vectors  : ${data.total_vectors} declared / ${total} run`)
console.log(`Result   : ${passed} passed / ${failed} failed`)
console.log('─'.repeat(60))

if (failed > 0) {
  console.error('\nFAILED vectors:', failures.join(', '))
  console.error('\nThis Node.js implementation is NOT conformant with the')
  console.error('OMNIX cross-language conformance specification.')
  console.error('See sdk/conformance_vectors.json for the canonical reference.')
  process.exit(1)
} else {
  console.log('\nAll vectors pass. Node.js SDK is conformant with FVP-INV-007 and ATF-INV-006.')
  process.exit(0)
}
