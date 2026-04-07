import { useState } from 'react'
import { CheckCircle, Copy, Terminal, Zap, Key, FileText, Shield, ArrowRight, Cpu } from 'lucide-react'

const GOLD = '#C9A227'
const DARK = '#0A1628'

const pythonSnippet = `from omnix_sdk import OmnixClient

client = OmnixClient(api_key="OMNIX-your-key-here")

result = client.evaluate(
    domain="trading",
    asset="BTC/USD",
    signals={"price": 94200, "volume": 1.5}
)

print(result["decision"])        # "APPROVED"
print(result["receipt_id"])      # "OMNIX-abc123..."
print(result["regulatory_alignment"]["frameworks_covered"])  # 8`

const nodeSnippet = `const OmnixClient = require('./omnix_sdk/node')

const client = new OmnixClient({ apiKey: 'OMNIX-your-key-here' })

const result = await client.evaluate({
  domain: 'trading',
  asset: 'BTC/USD',
  signals: { price: 94200, volume: 1.5 }
})

console.log(result.decision)        // "APPROVED"
console.log(result.receipt_id)      // "OMNIX-abc123..."
console.log(result.regulatory_alignment.frameworks_covered)  // 8`

const curlSnippet = `curl -X POST https://your-deployment.railway.app/api/governance/evaluate \\
  -H "X-API-Key: OMNIX-your-key-here" \\
  -H "Content-Type: application/json" \\
  -d '{
    "domain": "trading",
    "asset": "BTC/USD",
    "signals": { "price": 94200, "volume": 1.5 }
  }'`

const responseSnippet = `{
  "decision": "APPROVED",
  "receipt_id": "OMNIX-a3f8b2c1d4e5...",
  "checkpoints_passed": 11,
  "checkpoints_blocked": 0,
  "regulatory_alignment": {
    "frameworks_covered": 8,
    "frameworks": [
      { "id": "EU_AI_ACT",    "full_name": "EU Artificial Intelligence Act" },
      { "id": "NIST_AI_RMF", "full_name": "NIST AI Risk Management Framework 1.0" },
      { "id": "DORA",        "full_name": "Digital Operational Resilience Act" },
      { "id": "FATF",        "full_name": "Financial Action Task Force Recommendations" },
      ...
    ],
    "attestation_note": "Cryptographically signed. Post-quantum sealed."
  },
  "signature": "pq_kyber_v1:...",
  "timestamp": "2026-04-07T12:00:00Z"
}`

const steps = [
  {
    n: '01',
    icon: <Key size={18} color={GOLD} />,
    title: 'Get your API key',
    desc: 'Your key has format OMNIX-XXXX (44 characters). Provided upon contract signature.',
    note: 'Keys are scoped per client. Rate limit: 120 req/min. Never expose in client-side code.',
  },
  {
    n: '02',
    icon: <Terminal size={18} color={GOLD} />,
    title: 'Copy the SDK — no install required',
    desc: 'The SDK is a single stdlib-only file. No pip install, no npm install. Just copy it.',
    note: 'Python: omnix_sdk.py (requires Python 3.7+)  |  Node.js: index.js (requires Node 14+)',
  },
  {
    n: '03',
    icon: <Zap size={18} color={GOLD} />,
    title: 'Call evaluate()',
    desc: 'Every call runs through the 11-checkpoint pipeline and returns a signed receipt with regulatory alignment.',
    note: 'Domains: trading · credit · insurance · robotics · Any custom domain string accepted.',
  },
  {
    n: '04',
    icon: <Shield size={18} color={GOLD} />,
    title: 'Store the receipt_id',
    desc: 'The receipt_id is your cryptographic proof that the decision was governance-certified. Verify it anytime at /verify.',
    note: 'Receipts are permanent. Post-quantum signed. Chain-linked to the OMNIX Transparency Chain.',
  },
  {
    n: '05',
    icon: <FileText size={18} color={GOLD} />,
    title: 'Download due diligence PDF on demand',
    desc: 'One API call generates a branded governance report covering all decisions in a time window. Ready for LP or regulatory review.',
    note: 'GET /api/governance/due-diligence-report?format=pdf&days=30 · Header: X-API-Key',
  },
]

function CodeBlock({ code, lang }: { code: string, lang: string }) {
  const [copied, setCopied] = useState(false)
  const copy = () => {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <div style={{ background: '#060F1E', border: `1px solid ${GOLD}22`, borderRadius: 12, overflow: 'hidden' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 16px', borderBottom: `1px solid #ffffff08` }}>
        <span style={{ fontSize: 11, color: '#555', fontFamily: 'monospace', letterSpacing: '0.06em' }}>{lang}</span>
        <button onClick={copy} style={{ display: 'flex', alignItems: 'center', gap: 5, background: 'none', border: `1px solid ${GOLD}33`, borderRadius: 6, padding: '4px 10px', color: copied ? '#4ade80' : GOLD, fontSize: 11, cursor: 'pointer', fontWeight: 600 }}>
          <Copy size={11} /> {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <pre style={{ margin: 0, padding: '18px 20px', fontSize: 12, lineHeight: 1.7, color: '#cdd', overflowX: 'auto', fontFamily: "'Fira Code', 'Courier New', monospace" }}>
        <code>{code}</code>
      </pre>
    </div>
  )
}

export default function IntegrationGuide() {
  const [tab, setTab] = useState<'python' | 'node' | 'curl'>('python')

  return (
    <div style={{ background: DARK, minHeight: '100vh', color: '#F7F9FC', fontFamily: "'Inter', sans-serif" }}>

      {/* Header */}
      <div style={{ borderBottom: `1px solid ${GOLD}22`, padding: '28px 40px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Cpu size={22} color={GOLD} />
          <span style={{ fontWeight: 800, fontSize: 18, color: GOLD, letterSpacing: '0.08em' }}>OMNIX</span>
          <span style={{ color: '#444466', margin: '0 8px' }}>|</span>
          <span style={{ fontSize: 14, color: '#999' }}>Integration Guide</span>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <a href="/stack" style={{ fontSize: 12, color: GOLD, border: `1px solid ${GOLD}44`, borderRadius: 8, padding: '6px 14px', textDecoration: 'none' }}>Technical Stack</a>
          <a href="/try" style={{ fontSize: 12, background: GOLD, color: DARK, borderRadius: 8, padding: '6px 14px', textDecoration: 'none', fontWeight: 700 }}>Live Demo</a>
        </div>
      </div>

      <div style={{ maxWidth: 900, margin: '0 auto', padding: '60px 40px' }}>

        {/* Hero */}
        <div style={{ marginBottom: 60 }}>
          <div style={{ display: 'inline-block', background: `${GOLD}18`, border: `1px solid ${GOLD}44`, borderRadius: 20, padding: '6px 18px', fontSize: 12, color: GOLD, fontWeight: 700, letterSpacing: '0.1em', marginBottom: 20 }}>
            10-MINUTE INTEGRATION
          </div>
          <h1 style={{ fontSize: 'clamp(26px, 4vw, 42px)', fontWeight: 900, lineHeight: 1.1, margin: '0 0 16px', letterSpacing: '-0.02em' }}>
            Integrate OMNIX in 10 lines of code
          </h1>
          <p style={{ fontSize: 15, color: '#888', lineHeight: 1.7, maxWidth: 580 }}>
            No dependencies. No infrastructure. Copy one file, add your API key,
            and every decision you make is governance-certified with post-quantum receipts
            aligned to 8 regulatory frameworks.
          </p>
        </div>

        {/* Steps */}
        <section style={{ marginBottom: 64 }}>
          <h2 style={{ fontSize: 13, fontWeight: 700, color: '#555', letterSpacing: '0.12em', marginBottom: 28 }}>INTEGRATION FLOW</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {steps.map((step, i) => (
              <div key={step.n} style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>
                <div style={{ flexShrink: 0, width: 44, height: 44, borderRadius: 12, background: `${GOLD}15`, border: `1px solid ${GOLD}33`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>
                  <span style={{ fontSize: 10, color: GOLD, fontWeight: 800, letterSpacing: '0.06em' }}>{step.n}</span>
                </div>
                <div style={{ flex: 1, background: '#0D1E35', border: `1px solid #ffffff0a`, borderRadius: 14, padding: '18px 22px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                    {step.icon}
                    <span style={{ fontWeight: 700, fontSize: 14 }}>{step.title}</span>
                  </div>
                  <p style={{ fontSize: 13, color: '#888', lineHeight: 1.6, margin: '0 0 8px' }}>{step.desc}</p>
                  <p style={{ fontSize: 11, color: '#555', fontFamily: 'monospace', margin: 0 }}>{step.note}</p>
                </div>
                {i < steps.length - 1 && (
                  <div style={{ position: 'absolute', left: 22, marginTop: 60, width: 1, height: 16, background: `${GOLD}22` }} />
                )}
              </div>
            ))}
          </div>
        </section>

        {/* Code tabs */}
        <section style={{ marginBottom: 64 }}>
          <h2 style={{ fontSize: 13, fontWeight: 700, color: '#555', letterSpacing: '0.12em', marginBottom: 20 }}>QUICKSTART CODE</h2>
          <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
            {(['python', 'node', 'curl'] as const).map(t => (
              <button key={t} onClick={() => setTab(t)} style={{ padding: '8px 18px', borderRadius: 8, border: `1px solid ${tab === t ? GOLD : '#ffffff18'}`, background: tab === t ? `${GOLD}18` : 'transparent', color: tab === t ? GOLD : '#666', fontSize: 12, fontWeight: 700, cursor: 'pointer', letterSpacing: '0.05em' }}>
                {t === 'python' ? 'Python' : t === 'node' ? 'Node.js' : 'cURL'}
              </button>
            ))}
          </div>
          <CodeBlock
            code={tab === 'python' ? pythonSnippet : tab === 'node' ? nodeSnippet : curlSnippet}
            lang={tab === 'python' ? 'python · omnix_sdk.py' : tab === 'node' ? 'javascript · node/index.js' : 'bash · REST API'}
          />
        </section>

        {/* Response */}
        <section style={{ marginBottom: 64 }}>
          <h2 style={{ fontSize: 13, fontWeight: 700, color: '#555', letterSpacing: '0.12em', marginBottom: 20 }}>RESPONSE STRUCTURE</h2>
          <CodeBlock code={responseSnippet} lang="json · every evaluate() response" />
          <div style={{ marginTop: 16, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            {[
              'decision — APPROVED / BLOCKED / HOLD',
              'receipt_id — unique per evaluation',
              'regulatory_alignment — 8 frameworks',
              'signature — post-quantum sealed',
            ].map(item => (
              <div key={item} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#888' }}>
                <CheckCircle size={12} color={GOLD} />
                {item}
              </div>
            ))}
          </div>
        </section>

        {/* Endpoints */}
        <section style={{ marginBottom: 64 }}>
          <h2 style={{ fontSize: 13, fontWeight: 700, color: '#555', letterSpacing: '0.12em', marginBottom: 20 }}>KEY ENDPOINTS</h2>
          <div style={{ background: '#0D1E35', border: `1px solid ${GOLD}18`, borderRadius: 16, overflow: 'hidden' }}>
            {[
              { method: 'POST', path: '/api/governance/evaluate', auth: true,  desc: 'Evaluate a decision through the 11-checkpoint pipeline' },
              { method: 'GET',  path: '/api/governance/receipt/:id', auth: true,  desc: 'Retrieve a signed receipt by ID' },
              { method: 'GET',  path: '/api/governance/receipts', auth: true,  desc: 'List receipts with filters (domain, date, decision)' },
              { method: 'GET',  path: '/api/governance/due-diligence-report', auth: true,  desc: 'Generate governance report — JSON or PDF' },
              { method: 'GET',  path: '/api/governance/regulatory/catalog', auth: false, desc: 'Public — all 8 frameworks and checkpoint mapping' },
              { method: 'GET',  path: '/verify/:receipt_id', auth: false, desc: 'Public — verify any receipt independently' },
            ].map((ep, i, arr) => (
              <div key={ep.path} style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '14px 20px', borderBottom: i < arr.length - 1 ? `1px solid #ffffff06` : 'none' }}>
                <span style={{ fontFamily: 'monospace', fontSize: 11, fontWeight: 800, color: ep.method === 'POST' ? '#F59E0B' : GOLD, minWidth: 36 }}>{ep.method}</span>
                <span style={{ fontFamily: 'monospace', fontSize: 12, color: '#ccc', flex: 1 }}>{ep.path}</span>
                <span style={{ fontSize: 11, color: ep.auth ? '#8B5CF6' : '#10B981', background: ep.auth ? '#8B5CF620' : '#10B98120', border: `1px solid ${ep.auth ? '#8B5CF6' : '#10B981'}33`, borderRadius: 5, padding: '2px 8px', whiteSpace: 'nowrap' }}>
                  {ep.auth ? 'X-API-Key' : 'Public'}
                </span>
                <span style={{ fontSize: 12, color: '#666', display: 'none' }}>{ep.desc}</span>
              </div>
            ))}
          </div>
        </section>

        {/* CTA */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16 }}>
          <a href="/try" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: `${GOLD}15`, border: `1px solid ${GOLD}44`, borderRadius: 14, padding: '22px 24px', textDecoration: 'none' }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: GOLD, marginBottom: 4 }}>Try the live sandbox</div>
              <div style={{ fontSize: 12, color: '#888' }}>No API key needed</div>
            </div>
            <ArrowRight size={18} color={GOLD} />
          </a>
          <a href="/client" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#0D1E35', border: `1px solid #ffffff18`, borderRadius: 14, padding: '22px 24px', textDecoration: 'none' }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#ddd', marginBottom: 4 }}>Client Portal</div>
              <div style={{ fontSize: 12, color: '#888' }}>KPIs + PDF download</div>
            </div>
            <ArrowRight size={18} color='#888' />
          </a>
          <a href="/stack" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#0D1E35', border: `1px solid #ffffff18`, borderRadius: 14, padding: '22px 24px', textDecoration: 'none' }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#ddd', marginBottom: 4 }}>Technical Stack</div>
              <div style={{ fontSize: 12, color: '#888' }}>Full architecture overview</div>
            </div>
            <ArrowRight size={18} color='#888' />
          </a>
        </div>

      </div>

      <footer style={{ borderTop: `1px solid ${GOLD}15`, padding: '24px 40px', textAlign: 'center' }}>
        <p style={{ fontSize: 12, color: '#444466' }}>© 2026 OMNIX Quantum · harold@omnixquantum.net</p>
      </footer>
    </div>
  )
}
