import { useState } from 'react'

const BASE = 'https://omnixquantum.net'

const endpoints = [
  {
    label: 'Public Key (RFC 8615)',
    url: `${BASE}/.well-known/omnix-public-key.json`,
    badge: 'LIVE',
    desc: 'Active Dilithium-3 key. Any system can fetch it without authentication.',
  },
  {
    label: 'DID Document (W3C)',
    url: `${BASE}/.well-known/did.json`,
    badge: 'LIVE',
    desc: 'did:web:omnixquantum.net — resolvable by any DID resolver worldwide.',
  },
  {
    label: 'Trust Registry',
    url: `${BASE}/api/trust/registry`,
    badge: 'LIVE',
    desc: 'Public registry of trusted issuers, algorithms, and verification methods.',
  },
  {
    label: 'Verification API (stateless)',
    url: `${BASE}/api/trust/verify`,
    badge: 'POST',
    desc: 'Verification without DB access. Send a receipt, receive hash_valid + signature_valid.',
  },
]

const steps = [
  {
    num: '01',
    title: 'Fetch the public key',
    desc: 'Download the Dilithium-3 public key from the well-known endpoint. This key signs ALL governance receipts.',
    code: `curl https://omnixquantum.net/.well-known/omnix-public-key.json`,
    note: 'One network call. After that, everything runs locally.',
  },
  {
    num: '02',
    title: 'Recompute the SHA-256 hash',
    desc: 'The content_hash field in the receipt is a SHA-256 of the canonical payload. You can recompute it yourself and compare.',
    code: `python omnix_verify.py receipt.json`,
    note: 'The math does not depend on any OMNIX server.',
  },
  {
    num: '03',
    title: 'Verify the Dilithium-3 signature',
    desc: 'The PQC signature uses ML-DSA-65 (NIST FIPS 204). Any standard Dilithium-3 implementation can verify it.',
    code: `pip install pqcrypto\npython omnix_verify.py receipt.json`,
    note: '100% offline verification. No connection to OMNIX required.',
  },
]

const critique = {
  original: `"Everything you describe happens inside your own system: validation, monitoring, and traceability. That is internal governance. Not interoperability. Trust cannot depend on a system — it must depend on proofs that can be verified and understood by third parties."`,
  author: '— Antonio Socorro, LinkedIn',
  response: `The critique is correct and we took it seriously. That is why we built three layers of external verifiability: the math is public (NIST FIPS 204), the key is published at a standard endpoint (RFC 8615 + W3C DID), and the verification script is downloadable and runs without any OMNIX server. If governance exists, the proof must survive outside the system that produced it.`,
}

export default function IndependentVerification() {
  const [copied, setCopied] = useState<string | null>(null)

  const copy = (text: string, key: string) => {
    navigator.clipboard.writeText(text)
    setCopied(key)
    setTimeout(() => setCopied(null), 2000)
  }

  return (
    <div className="min-h-screen bg-black text-white font-mono">

      <div className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <a href="/" className="text-gray-400 hover:text-white text-sm transition-colors">← omnixquantum.net</a>
        <span className="text-xs text-gray-600">ADR-085 · eIDAS · ARF · NIST FIPS 204</span>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-16">

        <div className="mb-16">
          <div className="text-xs text-emerald-400 tracking-widest mb-4">INDEPENDENT VERIFICATION</div>
          <h1 className="text-4xl font-bold text-white mb-4 leading-tight">
            Verify any decision<br />
            <span className="text-emerald-400">without depending on OMNIX</span>
          </h1>
          <p className="text-gray-400 text-lg max-w-2xl leading-relaxed">
            Cryptographic signatures are mathematics. Mathematics has no server.
            Download the script, fetch the public key once, and verify offline forever.
          </p>
        </div>

        <div className="mb-16 border border-amber-800/40 bg-amber-950/20 rounded-lg p-6">
          <div className="text-xs text-amber-400 tracking-widest mb-3">CONTEXT — THE CRITIQUE THAT ORIGINATED THIS</div>
          <blockquote className="text-gray-300 text-sm leading-relaxed italic mb-3 border-l-2 border-amber-600 pl-4">
            {critique.original}
          </blockquote>
          <div className="text-xs text-amber-600 mb-4">{critique.author}</div>
          <div className="text-gray-400 text-sm leading-relaxed border-t border-amber-800/30 pt-4">
            <span className="text-emerald-400 font-bold">Response: </span>
            {critique.response}
          </div>
        </div>

        <div className="mb-16 border border-emerald-800/50 bg-emerald-950/20 rounded-lg p-8 text-center">
          <div className="text-xs text-emerald-400 tracking-widest mb-4">STEP 0 — DOWNLOAD THE VERIFIER</div>
          <h2 className="text-2xl font-bold text-white mb-3">omnix_verify.py</h2>
          <p className="text-gray-400 text-sm mb-6 max-w-lg mx-auto">
            Standalone Python script. Zero OMNIX dependencies. Requires Python 3.8+ only.
            For full PQC verification: <code className="text-emerald-400">pip install pqcrypto</code>
          </p>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <a
              href="/omnix_verify.py"
              download="omnix_verify.py"
              className="px-8 py-3 bg-emerald-600 hover:bg-emerald-500 text-black font-bold rounded transition-colors text-sm"
            >
              Download omnix_verify.py
            </a>
            <button
              onClick={() => copy('pip install pqcrypto', 'pip')}
              className="px-6 py-3 border border-emerald-800 hover:border-emerald-600 text-emerald-400 text-sm rounded transition-colors"
            >
              {copied === 'pip' ? 'Copied!' : 'pip install pqcrypto'}
            </button>
          </div>
          <div className="mt-4 text-xs text-gray-600">
            SHA-256 hash of the script available at{' '}
            <a href="/.well-known/omnix-public-key.json" className="text-gray-500 hover:text-gray-400 underline" target="_blank" rel="noreferrer">
              .well-known/omnix-public-key.json
            </a>
          </div>
        </div>

        <div className="mb-16">
          <div className="text-xs text-gray-500 tracking-widest mb-8">HOW IT WORKS</div>
          <div className="space-y-8">
            {steps.map((step) => (
              <div key={step.num} className="flex gap-6 group">
                <div className="text-4xl font-bold text-gray-800 group-hover:text-emerald-900 transition-colors w-12 flex-shrink-0 pt-1">
                  {step.num}
                </div>
                <div className="flex-1 border border-gray-800 rounded-lg p-6 hover:border-gray-700 transition-colors">
                  <div className="text-white font-bold mb-2">{step.title}</div>
                  <div className="text-gray-400 text-sm mb-4">{step.desc}</div>
                  <div className="flex items-center justify-between bg-gray-950 border border-gray-800 rounded px-4 py-3 mb-3">
                    <code className="text-emerald-400 text-xs whitespace-pre">{step.code}</code>
                    <button
                      onClick={() => copy(step.code, step.num)}
                      className="text-gray-600 hover:text-gray-400 text-xs ml-4 flex-shrink-0 transition-colors"
                    >
                      {copied === step.num ? 'copied' : 'copy'}
                    </button>
                  </div>
                  <div className="text-xs text-gray-600">{step.note}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="mb-16">
          <div className="text-xs text-gray-500 tracking-widest mb-8">PUBLIC ENDPOINTS — NO AUTHENTICATION REQUIRED</div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {endpoints.map((ep) => (
              <div key={ep.url} className="border border-gray-800 rounded-lg p-5 hover:border-gray-700 transition-colors">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-white text-sm font-bold">{ep.label}</span>
                  <span className={`text-xs px-2 py-0.5 rounded font-mono ${
                    ep.badge === 'POST'
                      ? 'bg-blue-950 text-blue-400 border border-blue-800'
                      : 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                  }`}>
                    {ep.badge}
                  </span>
                </div>
                <div className="text-gray-600 text-xs mb-3 font-mono break-all">{ep.url}</div>
                <div className="text-gray-500 text-xs">{ep.desc}</div>
                <a
                  href={ep.url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-3 inline-block text-xs text-emerald-600 hover:text-emerald-400 transition-colors"
                >
                  Open →
                </a>
              </div>
            ))}
          </div>
        </div>

        <div className="mb-16 border border-gray-800 rounded-lg p-8">
          <div className="text-xs text-gray-500 tracking-widest mb-6">WHAT THE MATH GUARANTEES</div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                icon: '🔒',
                title: 'Integrity',
                body: 'SHA-256 of the canonical payload. If any field was modified after the receipt was issued, the hash will not match. Detectable by anyone.',
              },
              {
                icon: '✍️',
                title: 'Authenticity',
                body: 'Dilithium-3 signature (NIST FIPS 204). Only the holder of the private key can sign. The private key never leaves the server.',
              },
              {
                icon: '🌐',
                title: 'Independence',
                body: 'Cryptographic verification does not require OMNIX to exist. A receipt can be verified in 2030 using only the script and the public key.',
              },
            ].map((item) => (
              <div key={item.title}>
                <div className="text-2xl mb-3">{item.icon}</div>
                <div className="text-white font-bold text-sm mb-2">{item.title}</div>
                <div className="text-gray-500 text-xs leading-relaxed">{item.body}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="mb-16 border border-gray-800 rounded-lg p-8">
          <div className="text-xs text-gray-500 tracking-widest mb-4">TECHNICAL HONESTY — WHAT THIS ALONE DOES NOT SOLVE</div>
          <div className="space-y-3 text-sm text-gray-400">
            <div className="flex gap-3">
              <span className="text-amber-500 flex-shrink-0">△</span>
              <span>
                <strong className="text-white">External trust anchor:</strong> The public key is published by OMNIX. For full eIDAS compliance, the next layer is anchoring it in a European QTSP (Qualified Trust Service Provider). On the roadmap.
              </span>
            </div>
            <div className="flex gap-3">
              <span className="text-amber-500 flex-shrink-0">△</span>
              <span>
                <strong className="text-white">Key rotation:</strong> If OMNIX rotates the key, older receipts remain verifiable with the key they were signed with (embedded in the receipt). Rotation policy is in ADR-043.
              </span>
            </div>
            <div className="flex gap-3">
              <span className="text-emerald-500 flex-shrink-0">✓</span>
              <span>
                <strong className="text-white">What this solves today:</strong> any third party can verify that a receipt was not tampered with and was issued by OMNIX — without trusting any OMNIX endpoint during verification.
              </span>
            </div>
          </div>
        </div>

        <div className="mb-16">
          <div className="text-xs text-gray-500 tracking-widest mb-6">VERIFICATION VIA API (no DB, stateless)</div>
          <div className="bg-gray-950 border border-gray-800 rounded-lg p-6">
            <div className="text-xs text-gray-600 mb-3">POST /api/trust/verify</div>
            <pre className="text-emerald-400 text-xs overflow-x-auto whitespace-pre-wrap">{`curl -X POST https://omnixquantum.net/api/trust/verify \\
  -H "Content-Type: application/json" \\
  -d '{
    "receipt": {
      "receipt_id": "REC-20260426-...",
      "decision": "APPROVED",
      "content_hash": "a3f1...",
      "signature": "base64...",
      "public_key": "base64...",
      ...
    }
  }'

// Response:
{
  "hash_valid": true,
  "signature_valid": true,
  "overall_valid": true,
  "independent": true,
  "db_required": false,
  "issuer_did": "did:web:omnixquantum.net"
}`}</pre>
          </div>
        </div>

        <div className="border-t border-gray-800 pt-8 text-center">
          <div className="text-xs text-gray-600 mb-2">
            OMNIX Quantum Ltd · did:web:omnixquantum.net · ADR-085
          </div>
          <div className="text-xs text-gray-700">
            eIDAS 2.0 · EU AI Act Art. 14 · ARF · NIST FIPS 204 · MiFID II
          </div>
          <div className="mt-4 flex justify-center gap-6 text-xs">
            <a href="/verify" className="text-gray-600 hover:text-gray-400 transition-colors">Verify receipt</a>
            <a href="/proof" className="text-gray-600 hover:text-gray-400 transition-colors">Proof Layer</a>
            <a href="/integration" className="text-gray-600 hover:text-gray-400 transition-colors">Integration Guide</a>
            <a href="/" className="text-gray-600 hover:text-gray-400 transition-colors">Home</a>
          </div>
        </div>

      </div>
    </div>
  )
}
