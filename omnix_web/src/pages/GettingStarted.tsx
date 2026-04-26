import { useState } from 'react'
import { Link } from 'react-router-dom'

const GOLD = '#C9A227'

const domains = [
  { id: 'trading',        label: 'Trading',        color: '#C9A227', example: { asset: 'BTC/USD',       signals: { price: 94200, volume: 1.5, volatility: 0.18 } } },
  { id: 'islamic_credit', label: 'Islamic Credit',  color: '#a78bfa', example: { asset: 'SME-AE-001',    signals: { debt_to_income: 32, collateral_ratio: 1.4, sharia_compliant: true } } },
  { id: 'insurance',      label: 'Insurance',       color: '#60a5fa', example: { asset: 'AUTO-CLAIM-887', signals: { claim_amount: 12000, fraud_score: 0.12, policy_active: true } } },
  { id: 'energy',         label: 'Energy',          color: '#34d399', example: { asset: 'SOLAR-GRID-07',  signals: { capacity_mw: 240, grid_stability: 0.95, carbon_offset: 840 } } },
]

const sampleResponse = {
  receipt_id: 'OMNIX-CRD-a3f8b2c1d4e5f6a7',
  decision: 'APPROVED',
  timestamp: '2026-04-26T10:31:00.000Z',
  checkpoints_passed: 11,
  checkpoints_blocked: 0,
  policy_version: '6.5.4e',
  jurisdiction: 'UAE',
  content_hash: 'sha256:3a7f1b2c4d8e9f0a…',
  signature_algorithm: 'Dilithium-3 (NIST FIPS 204)',
  veto_chain: [],
  verify_url: 'https://omnixquantum.net/verify/OMNIX-CRD-a3f8b2c1d4e5f6a7',
}

const steps = [
  {
    num: '01',
    title: 'A decision arrives',
    body: 'Your system sends a request to OMNIX with the domain, asset, and signals. It could be a trade, a loan, an insurance claim, an energy dispatch — anything that requires governance.',
    color: '#a78bfa',
  },
  {
    num: '02',
    title: 'OMNIX runs 11 checkpoints',
    body: 'The request passes through 11 independent gates: context admission, structural admissibility, AML, jurisdiction, coherence, sharia (if applicable), fraud, physics validation, and more. Every gate fires in sequence.',
    color: GOLD,
  },
  {
    num: '03',
    title: 'You get a signed receipt',
    body: 'The decision arrives with a cryptographic receipt: SHA-256 hash + Dilithium-3 signature (NIST FIPS 204). The receipt is immutable, independently verifiable, and retained for 5 years (MiFID II).',
    color: '#34d399',
  },
]

export default function GettingStarted() {
  const [active, setActive] = useState(0)
  const [copied, setCopied] = useState<string | null>(null)

  const copy = (text: string, key: string) => {
    navigator.clipboard.writeText(text)
    setCopied(key)
    setTimeout(() => setCopied(null), 2000)
  }

  const dom = domains[active]
  const curlExample = `curl -X POST https://omnixquantum.net/api/governance/evaluate \\
  -H "X-API-Key: OMNIX-xxxx…" \\
  -H "Content-Type: application/json" \\
  -d '{
    "domain":  "${dom.id}",
    "asset":   "${dom.example.asset}",
    "signals": ${JSON.stringify(dom.example.signals, null, 4).split('\n').join('\n    ')}
  }'`

  return (
    <div className="min-h-screen bg-[#050D18] text-white font-sans">

      {/* Nav */}
      <div className="border-b border-[#C9A227]/10 px-6 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3">
          <img src="/logo.png" alt="OMNIX" className="w-10 h-10 object-contain" />
          <span className="text-sm text-gray-400 hover:text-white transition-colors">← omnixquantum.net</span>
        </Link>
        <div className="flex items-center gap-6 text-sm">
          <Link to="/try" className="text-[#C9A227] hover:text-white transition-colors font-medium">Try it live →</Link>
          <Link to="/integration" className="text-gray-500 hover:text-gray-300 transition-colors">Full API Reference</Link>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-16">

        {/* Hero */}
        <div className="mb-20">
          <div className="text-xs text-[#C9A227] tracking-widest mb-4 font-mono">GETTING STARTED</div>
          <h1 className="text-5xl font-bold text-white mb-6 leading-tight">
            What OMNIX does.<br />
            <span className="text-[#C9A227]">In two minutes.</span>
          </h1>
          <p className="text-gray-400 text-xl max-w-2xl leading-relaxed">
            OMNIX is a governance layer for automated decisions. Before a decision executes,
            OMNIX validates it — and issues a cryptographic proof of whether it was admissible.
            That proof is verifiable by anyone, forever.
          </p>
        </div>

        {/* One-liner */}
        <div className="mb-20 border border-[#C9A227]/20 bg-[#C9A227]/5 rounded-xl p-8 text-center">
          <p className="text-2xl font-bold text-white leading-relaxed">
            Every system checks if a decision <em className="text-[#C9A227]">can</em> be executed.<br />
            OMNIX checks if it <em className="text-white underline decoration-[#C9A227]">should exist at all</em>.
          </p>
        </div>

        {/* How it works */}
        <div className="mb-20">
          <div className="text-xs text-gray-500 tracking-widest mb-10 font-mono">HOW IT WORKS</div>
          <div className="space-y-6">
            {steps.map((step) => (
              <div key={step.num} className="flex gap-6 group">
                <div className="text-5xl font-black font-mono w-14 flex-shrink-0 pt-1"
                  style={{ color: step.color, opacity: 0.3 }}>
                  {step.num}
                </div>
                <div className="flex-1 border border-gray-800 rounded-xl p-6 hover:border-gray-700 transition-colors">
                  <div className="text-white font-bold text-lg mb-2">{step.title}</div>
                  <div className="text-gray-400 leading-relaxed">{step.body}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Live example */}
        <div className="mb-20">
          <div className="text-xs text-gray-500 tracking-widest mb-6 font-mono">REAL EXAMPLE — PICK A DOMAIN</div>

          {/* Domain tabs */}
          <div className="flex gap-2 flex-wrap mb-6">
            {domains.map((d, i) => (
              <button
                key={d.id}
                onClick={() => setActive(i)}
                className="px-4 py-2 rounded-lg text-sm font-medium transition-all"
                style={{
                  background: active === i ? `${d.color}15` : 'transparent',
                  border: `1px solid ${active === i ? d.color : '#1e293b'}`,
                  color: active === i ? d.color : '#64748b',
                }}
              >
                {d.label}
              </button>
            ))}
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            {/* Request */}
            <div className="border border-gray-800 rounded-xl overflow-hidden">
              <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800 bg-[#0a0f1a]">
                <span className="text-xs text-gray-500 font-mono">REQUEST</span>
                <button
                  onClick={() => copy(curlExample, 'curl')}
                  className="text-xs text-gray-600 hover:text-gray-400 transition-colors"
                >
                  {copied === 'curl' ? 'copied ✓' : 'copy'}
                </button>
              </div>
              <div className="p-4 bg-[#060b14]">
                <pre className="text-xs text-green-400 overflow-x-auto whitespace-pre leading-relaxed">
                  {curlExample}
                </pre>
              </div>
            </div>

            {/* Response */}
            <div className="border border-gray-800 rounded-xl overflow-hidden">
              <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800 bg-[#0a0f1a]">
                <span className="text-xs text-gray-500 font-mono">RESPONSE</span>
                <span className="text-xs px-2 py-0.5 rounded font-mono bg-emerald-950 text-emerald-400 border border-emerald-800">
                  APPROVED
                </span>
              </div>
              <div className="p-4 bg-[#060b14]">
                <pre className="text-xs text-gray-300 overflow-x-auto whitespace-pre leading-relaxed">
                  {JSON.stringify(sampleResponse, null, 2)}
                </pre>
              </div>
            </div>
          </div>

          <div className="mt-4 text-xs text-gray-600 text-center">
            Every field in the response is verifiable independently.{' '}
            <Link to="/verify-independently" className="text-emerald-600 hover:text-emerald-400 transition-colors underline">
              Verify a receipt →
            </Link>
          </div>
        </div>

        {/* What you get */}
        <div className="mb-20">
          <div className="text-xs text-gray-500 tracking-widest mb-8 font-mono">WHAT EVERY RECEIPT CONTAINS</div>
          <div className="grid md:grid-cols-2 gap-4">
            {[
              { label: 'Decision', val: 'APPROVED · BLOCKED · HOLD', desc: 'The governance verdict.' },
              { label: 'Checkpoint results', val: '11 gates, each scored', desc: 'Every rule that fired, with threshold and result.' },
              { label: 'Policy version', val: 'Exact version at T=0', desc: 'Which rules were active when the decision was made.' },
              { label: 'Jurisdiction', val: 'UAE · EU · UK · US · SG', desc: 'The regulatory framework that applied.' },
              { label: 'Content hash', val: 'SHA-256', desc: 'Tamper-proof fingerprint of the payload.' },
              { label: 'PQC Signature', val: 'Dilithium-3 / NIST FIPS 204', desc: 'Post-quantum cryptographic proof of authenticity.' },
              { label: 'Hash chain', val: 'prev_hash link', desc: 'Links to the previous receipt — transparency ledger.' },
              { label: 'Retention', val: '5 years (MiFID II)', desc: 'HOT → WARM → COLD archival, immutable.' },
            ].map((item) => (
              <div key={item.label} className="border border-gray-800 rounded-lg p-4 hover:border-gray-700 transition-colors">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-white text-sm font-semibold">{item.label}</span>
                  <span className="text-xs text-[#C9A227] font-mono">{item.val}</span>
                </div>
                <div className="text-gray-500 text-xs">{item.desc}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Domains */}
        <div className="mb-20">
          <div className="text-xs text-gray-500 tracking-widest mb-8 font-mono">LIVE ACROSS 9 DOMAINS</div>
          <div className="grid grid-cols-3 md:grid-cols-5 gap-3">
            {[
              { name: 'Trading',       color: '#C9A227', link: '/governance-demo' },
              { name: 'Islamic Credit',color: '#a78bfa', link: '/governance-demo' },
              { name: 'Insurance',     color: '#60a5fa', link: '/governance-demo-insurance' },
              { name: 'Robotics',      color: '#34d399', link: '/robotics' },
              { name: 'Medical AI',    color: '#f472b6', link: '/medical' },
              { name: 'Energy',        color: '#34d399', link: '/energy' },
              { name: 'Real Estate',   color: '#fb923c', link: '/real-estate' },
              { name: 'Agents',        color: '#f59e0b', link: '/agents' },
              { name: 'Stablecoin',    color: '#818cf8', link: '/stablecoin' },
            ].map((d) => (
              <Link
                key={d.name}
                to={d.link}
                className="border rounded-lg p-3 text-center text-xs font-medium hover:opacity-80 transition-opacity"
                style={{ border: `1px solid ${d.color}30`, color: d.color, background: `${d.color}08` }}
              >
                {d.name}
              </Link>
            ))}
          </div>
        </div>

        {/* CTAs */}
        <div className="border border-gray-800 rounded-xl p-8">
          <div className="text-xs text-gray-500 tracking-widest mb-6 font-mono text-center">NEXT STEPS</div>
          <div className="grid md:grid-cols-3 gap-4">
            <Link to="/try" className="block border border-[#C9A227]/30 bg-[#C9A227]/05 rounded-xl p-6 hover:border-[#C9A227]/60 transition-colors group">
              <div className="text-[#C9A227] font-bold mb-2 group-hover:underline">Try it live →</div>
              <div className="text-gray-500 text-sm">Run a real governance decision through OMNIX in the sandbox. No account needed.</div>
            </Link>
            <Link to="/integration" className="block border border-gray-700 rounded-xl p-6 hover:border-gray-500 transition-colors group">
              <div className="text-white font-bold mb-2 group-hover:underline">Full API reference →</div>
              <div className="text-gray-500 text-sm">Python, Node.js, cURL examples. Authentication, endpoints, response schema.</div>
            </Link>
            <Link to="/verify-independently" className="block border border-emerald-800/40 bg-emerald-950/10 rounded-xl p-6 hover:border-emerald-600/40 transition-colors group">
              <div className="text-emerald-400 font-bold mb-2 group-hover:underline">Verify a receipt →</div>
              <div className="text-gray-500 text-sm">Download the verification script. Works offline. No OMNIX server needed.</div>
            </Link>
          </div>
          <div className="text-center mt-6">
            <a
              href="https://wa.me/16505078293?text=Hi%2C%20I%27m%20interested%20in%20OMNIX"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-8 py-3 rounded-lg font-bold text-sm transition-colors"
              style={{ background: '#C9A227', color: '#000' }}
            >
              Talk to us — get your API key
            </a>
          </div>
        </div>

      </div>

      {/* Footer */}
      <div className="border-t border-gray-900 py-8 text-center">
        <div className="text-xs text-gray-700">
          OMNIX Quantum Ltd · did:web:omnixquantum.net · 71-75 Shelton Street, London WC2H 9JQ
        </div>
      </div>

    </div>
  )
}
