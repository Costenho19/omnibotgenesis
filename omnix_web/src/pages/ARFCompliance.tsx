import { useState } from 'react'
import { Link } from 'react-router-dom'

const GOLD = '#C9A227'

const ENDPOINTS = [
  { method: 'GET',  path: '/.well-known/did.json',                    label: 'DID Document',            desc: 'did:web:omnixquantum.net resolution' },
  { method: 'GET',  path: '/.well-known/omnix-public-key.json',       label: 'Public Key (RFC 8615)',    desc: 'Active Dilithium-3 signing key' },
  { method: 'GET',  path: '/.well-known/openid-credential-issuer',    label: 'OpenID4VCI Metadata',      desc: 'EUDI Wallet discovery endpoint (ARF required)' },
  { method: 'GET',  path: '/.well-known/omnix-arf-profile.json',      label: 'ARF Credential Profile',   desc: 'OmnixGovernanceCredential schema + trust chain' },
  { method: 'GET',  path: '/schemas/omnix-receipt-v1.jsonld',         label: 'JSON-LD Context',          desc: 'W3C VC JSON-LD context (JSON-LD 1.1)' },
  { method: 'GET',  path: '/schemas/omnix-receipt-schema-v6.5.4e.json', label: 'JSON Schema',            desc: 'Receipt validation schema' },
  { method: 'POST', path: '/api/governance/receipt/vc',               label: 'VC Issuer Endpoint',       desc: 'Convert receipt → W3C VC (OpenID4VCI)' },
  { method: 'POST', path: '/api/trust/verify',                        label: 'Independent Verifier',     desc: 'Verify receipt or VC — no DB, purely cryptographic' },
  { method: 'GET',  path: '/api/trust/registry',                      label: 'Trust Registry',           desc: 'Live issuer record + active public key' },
]

const FRAMEWORKS = [
  { key: 'EU AI Act',       ref: 'Regulation (EU) 2024/1689',       region: 'Europe',       color: '#60a5fa' },
  { key: 'GDPR',            ref: 'Regulation (EU) 2016/679 Art.22', region: 'Europe',       color: '#60a5fa' },
  { key: 'DORA',            ref: 'Regulation (EU) 2022/2554',       region: 'Europe',       color: '#60a5fa' },
  { key: 'FATF',            ref: 'R.10, R.16, R.20, R.29 (2023)',   region: 'Global',       color: '#a78bfa' },
  { key: 'UK FCA / SM&CR',  ref: 'FCA COBS 11.2 · SYSC 9.1',       region: 'UK',           color: '#34d399' },
  { key: 'US SEC 15c3-5',   ref: '17 CFR §240.15c3-5',              region: 'US',           color: '#f472b6' },
  { key: 'MAS Singapore',   ref: 'FEAT Principles v2 (2020)',        region: 'Asia-Pacific', color: '#fb923c' },
  { key: 'UAE CBUAE',       ref: 'AI Governance Framework 2024',     region: 'Middle East',  color: GOLD },
  { key: 'SAMA Saudi',      ref: 'Responsible AI Principles (2023)', region: 'Middle East',  color: GOLD },
  { key: 'FSB G20',         ref: 'AI/ML in Fin. Services (2023)',    region: 'Global',       color: '#a78bfa' },
]

const EVALUATE_EXAMPLE = `curl -X POST https://omnixquantum.net/api/governance/evaluate \\
  -H "X-API-Key: OMNIX-..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "domain":      "trading",
    "asset":       "BTC/USD",
    "signals":     { "price": 94200, "volume": 1.5, "volatility": 0.18 },
    "include_vc":  true
  }'`

const VC_EXAMPLE = `{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://omnixquantum.net/schemas/omnix-receipt-v1.jsonld"
  ],
  "id": "https://omnixquantum.net/receipts/OMNIX-TRD-a3f8b2c1d4e5f6a7",
  "type": ["VerifiableCredential", "OmnixGovernanceCredential"],
  "issuer": {
    "id":   "did:web:omnixquantum.net",
    "name": "OMNIX Quantum Ltd"
  },
  "issuanceDate":   "2026-04-26T10:31:00+00:00",
  "expirationDate": "2027-04-26T10:31:00+00:00",
  "credentialSubject": {
    "receipt_id":     "OMNIX-TRD-a3f8b2c1d4e5f6a7",
    "decision":       "APPROVED",
    "domain":         "trading",
    "asset":          "BTC/USD",
    "content_hash":   "sha256:3a7f1b2c4d8e9f0a...",
    "policy_version": "6.5.4e",
    "veto_chain":     []
  },
  "proof": {
    "type":               "Dilithium2021",
    "created":            "2026-04-26T10:31:00+00:00",
    "verificationMethod": "did:web:omnixquantum.net#pqc-key-1",
    "proofPurpose":       "assertionMethod",
    "proofValue":         "<Dilithium-3 signature base64>",
    "signatureAlgorithm": "Dilithium-3 (NIST FIPS 204)",
    "nist_note":          "Post-quantum signature (NIST-standardized algorithm)"
  }
}`

export default function ARFCompliance() {
  const [copied, setCopied] = useState<string | null>(null)

  const copy = (text: string, key: string) => {
    navigator.clipboard.writeText(text)
    setCopied(key)
    setTimeout(() => setCopied(null), 2000)
  }

  return (
    <div className="min-h-screen bg-[#050D18] text-white font-sans">

      {/* Nav */}
      <div className="border-b border-[#C9A227]/10 px-6 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3">
          <img src="/logo.png" alt="OMNIX" className="w-10 h-10 object-contain" />
          <span className="text-sm text-gray-400 hover:text-white transition-colors">← omnixquantum.net</span>
        </Link>
        <div className="flex items-center gap-6 text-sm">
          <Link to="/docs" className="text-gray-500 hover:text-gray-300 transition-colors">Docs</Link>
          <Link to="/verify-independently" className="text-emerald-400 hover:text-white transition-colors font-medium">Verify →</Link>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-16">

        {/* Hero */}
        <div className="mb-16">
          <div className="flex items-center gap-3 mb-4">
            <div className="text-xs text-[#C9A227] tracking-widest font-mono">eIDAS 2.0 · ARF 1.4 · OpenID4VCI</div>
            <div className="px-2 py-0.5 rounded text-xs font-mono bg-blue-950 text-blue-400 border border-blue-800">
              FASE C
            </div>
          </div>
          <h1 className="text-5xl font-bold text-white mb-6 leading-tight">
            OMNIX receipts are<br />
            <span className="text-[#C9A227]">W3C Verifiable Credentials.</span>
          </h1>
          <p className="text-gray-400 text-xl max-w-2xl leading-relaxed">
            Every governance decision issued by OMNIX can be wrapped as a W3C VC
            and presented to any EUDI Wallet or OpenID4VCI verifier.
            The existing Dilithium-3 signature becomes the VC proof block.
            No re-signing. No conversion loss.
          </p>
        </div>

        {/* What changed */}
        <div className="mb-16 grid md:grid-cols-3 gap-4">
          {[
            {
              label: 'eIDAS 2.0 / ARF 1.4',
              desc:  '/.well-known/openid-credential-issuer — machine-readable discovery. EUDI Wallets find OMNIX automatically.',
              color: '#60a5fa',
            },
            {
              label: 'W3C VC 1.1 + JSON-LD',
              desc:  'Any OMNIX receipt becomes a VerifiableCredential via POST /api/governance/receipt/vc. Same hash, same signature.',
              color: GOLD,
            },
            {
              label: 'include_vc=true',
              desc:  'Add "include_vc": true to any /evaluate call and the response includes the full W3C VC alongside the receipt.',
              color: '#34d399',
            },
          ].map(item => (
            <div key={item.label} className="border border-gray-800 rounded-xl p-6 hover:border-gray-700 transition-colors">
              <div className="text-sm font-bold mb-2" style={{ color: item.color }}>{item.label}</div>
              <div className="text-gray-400 text-sm leading-relaxed">{item.desc}</div>
            </div>
          ))}
        </div>

        {/* Live example */}
        <div className="mb-16">
          <div className="text-xs text-gray-500 tracking-widest mb-6 font-mono">GET A VC IN ONE CALL</div>
          <div className="border border-gray-800 rounded-xl overflow-hidden mb-4">
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800 bg-[#0a0f1a]">
              <span className="text-xs text-gray-500 font-mono">REQUEST — include_vc: true</span>
              <button
                onClick={() => copy(EVALUATE_EXAMPLE, 'eval')}
                className="text-xs text-gray-600 hover:text-gray-400 transition-colors"
              >
                {copied === 'eval' ? 'copied ✓' : 'copy'}
              </button>
            </div>
            <pre className="p-4 bg-[#060b14] text-xs text-green-400 overflow-x-auto leading-relaxed">
              {EVALUATE_EXAMPLE}
            </pre>
          </div>
          <div className="border border-gray-800 rounded-xl overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800 bg-[#0a0f1a]">
              <span className="text-xs text-gray-500 font-mono">RESPONSE — verifiable_credential block</span>
              <button
                onClick={() => copy(VC_EXAMPLE, 'vc')}
                className="text-xs text-gray-600 hover:text-gray-400 transition-colors"
              >
                {copied === 'vc' ? 'copied ✓' : 'copy'}
              </button>
            </div>
            <pre className="p-4 bg-[#060b14] text-xs text-gray-300 overflow-x-auto leading-relaxed">
              {VC_EXAMPLE}
            </pre>
          </div>
        </div>

        {/* Trust anchor endpoints */}
        <div className="mb-16">
          <div className="text-xs text-gray-500 tracking-widest mb-6 font-mono">TRUST ANCHOR ENDPOINTS — ALL PUBLIC</div>
          <div className="space-y-2">
            {ENDPOINTS.map(ep => (
              <a
                key={ep.path}
                href={`https://omnixquantum.net${ep.path}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-4 border border-gray-800 rounded-lg px-4 py-3 hover:border-gray-600 transition-colors group"
              >
                <span
                  className="text-xs font-mono px-2 py-0.5 rounded flex-shrink-0"
                  style={{
                    background: ep.method === 'GET' ? '#052e16' : '#1c1917',
                    color:      ep.method === 'GET' ? '#4ade80'  : '#fb923c',
                    border:     `1px solid ${ep.method === 'GET' ? '#166534' : '#44403c'}`,
                  }}
                >
                  {ep.method}
                </span>
                <span className="text-gray-300 text-sm font-mono flex-shrink-0 group-hover:text-white transition-colors">
                  {ep.path}
                </span>
                <span className="text-gray-600 text-xs ml-auto hidden md:block">{ep.desc}</span>
              </a>
            ))}
          </div>
        </div>

        {/* 10 frameworks */}
        <div className="mb-16">
          <div className="text-xs text-gray-500 tracking-widest mb-6 font-mono">10 REGULATORY FRAMEWORKS IN EVERY VC</div>
          <p className="text-gray-500 text-sm mb-6">
            The <code className="text-gray-400 text-xs bg-gray-900 px-1 rounded">jurisdiction_semantics</code> block in each VC explains
            what the governance decision means under each framework — in plain language, with the exact article cited.
          </p>
          <div className="grid md:grid-cols-2 gap-3">
            {FRAMEWORKS.map(fw => (
              <div key={fw.key} className="flex items-start gap-3 border border-gray-800 rounded-lg p-4 hover:border-gray-700 transition-colors">
                <div className="w-2 h-2 rounded-full mt-1.5 flex-shrink-0" style={{ background: fw.color }} />
                <div className="flex-1 min-w-0">
                  <div className="text-white text-sm font-semibold">{fw.key}</div>
                  <div className="text-gray-500 text-xs mt-0.5">{fw.ref}</div>
                </div>
                <div className="text-xs text-gray-600 flex-shrink-0">{fw.region}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Proof scope */}
        <div className="mb-16 border border-gray-800 rounded-xl p-8">
          <div className="text-xs text-gray-500 tracking-widest mb-6 font-mono">PROOF SCOPE — WHAT OMNIX CERTIFIES AND WHAT IT DOESN'T</div>
          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <div className="text-emerald-400 text-sm font-bold mb-3">What this credential proves</div>
              <ul className="space-y-2">
                {[
                  'The decision was evaluated at the stated timestamp',
                  'The veto chain is cryptographically bound to the credential',
                  'The credential has not been altered since signing',
                  'The issuer controlled the Dilithium-3 key at issuance',
                  'Each regulatory mapping reflects OMNIX\'s interpretation',
                ].map(item => (
                  <li key={item} className="text-gray-400 text-sm flex items-start gap-2">
                    <span className="text-emerald-500 flex-shrink-0">✓</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <div className="text-red-400 text-sm font-bold mb-3">What this credential does not claim</div>
              <ul className="space-y-2">
                {[
                  'Authoritative regulatory approval from any supervisory body',
                  'Guaranteed cross-border enforceability without local counsel',
                  'Semantic equivalence across all named jurisdictions',
                  'Substitution for jurisdiction-specific compliance certification',
                ].map(item => (
                  <li key={item} className="text-gray-400 text-sm flex items-start gap-2">
                    <span className="text-red-500 flex-shrink-0">—</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* CTAs */}
        <div className="grid md:grid-cols-3 gap-4">
          <a
            href="https://omnixquantum.net/.well-known/openid-credential-issuer"
            target="_blank"
            rel="noopener noreferrer"
            className="block border border-blue-800/40 bg-blue-950/10 rounded-xl p-6 hover:border-blue-600/40 transition-colors"
          >
            <div className="text-blue-400 font-bold mb-2">OpenID4VCI metadata →</div>
            <div className="text-gray-500 text-sm">Machine-readable credential issuer config for wallets and verifiers.</div>
          </a>
          <a
            href="https://omnixquantum.net/.well-known/omnix-arf-profile.json"
            target="_blank"
            rel="noopener noreferrer"
            className="block border border-[#C9A227]/30 bg-[#C9A227]/05 rounded-xl p-6 hover:border-[#C9A227]/60 transition-colors"
          >
            <div className="text-[#C9A227] font-bold mb-2">ARF profile →</div>
            <div className="text-gray-500 text-sm">Full schema, trust chain, jurisdiction mappings, lifecycle policy.</div>
          </a>
          <Link
            to="/verify-independently"
            className="block border border-emerald-800/40 bg-emerald-950/10 rounded-xl p-6 hover:border-emerald-600/40 transition-colors"
          >
            <div className="text-emerald-400 font-bold mb-2">Verify a credential →</div>
            <div className="text-gray-500 text-sm">Offline. No OMNIX server needed during verification.</div>
          </Link>
        </div>

      </div>

      <div className="border-t border-gray-900 py-8 text-center">
        <div className="text-xs text-gray-700">
          OMNIX Quantum Ltd · did:web:omnixquantum.net · eIDAS 2.0 ARF 1.4 · W3C VC 1.1 · OpenID4VCI draft-13
        </div>
      </div>

    </div>
  )
}
