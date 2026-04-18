import { useState, type ReactNode } from 'react'
import { CheckCircle, Copy, Terminal, Zap, Key, FileText, Shield, ArrowRight, Lock, Globe, AlertCircle, Clock } from 'lucide-react'

const GOLD = '#C9A227'
const DARK = '#0A1628'
const CARD = '#0D1E35'

const pythonSnippet = `import requests

API_KEY  = "OMNIX-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
BASE_URL = "https://omnixquantum.net"

def evaluate(domain: str, asset: str, signals: dict) -> dict:
    r = requests.post(
        f"{BASE_URL}/api/governance/evaluate",
        headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
        json={"domain": domain, "asset": asset, "signals": signals},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()

# Example — trading decision
result = evaluate(
    domain="trading",
    asset="BTC/USD",
    signals={"price": 94200, "volume": 1.5, "volatility": 0.18}
)

print(result["decision"])      # "APPROVED" | "BLOCKED" | "HOLD"
print(result["receipt_id"])    # "OMNIX-TRD-a3f8b2c1d4e5..."
print(result["checkpoints_passed"])   # 11
print(result["integrity"]["algorithm"])  # "Dilithium3 (NIST FIPS 204)"`

const nodeSnippet = `const https = require('https')

const API_KEY  = 'OMNIX-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
const BASE_URL = 'omnixquantum.net'

function evaluate(domain, asset, signals) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({ domain, asset, signals })
    const req  = https.request({
      hostname: BASE_URL,
      path:     '/api/governance/evaluate',
      method:   'POST',
      headers:  {
        'X-API-Key':      API_KEY,
        'Content-Type':   'application/json',
        'Content-Length': Buffer.byteLength(body),
      },
    }, res => {
      let data = ''
      res.on('data', chunk => data += chunk)
      res.on('end',  ()    => resolve(JSON.parse(data)))
    })
    req.on('error', reject)
    req.write(body)
    req.end()
  })
}

// Example — credit decision
const result = await evaluate('islamic_credit', 'SME-AE-001', {
  debt_to_income: 32, collateral_ratio: 1.4, sharia_compliant: true
})
console.log(result.decision)     // "APPROVED"
console.log(result.receipt_id)   // "OMNIX-CRD-..."
console.log(result.checkpoints_blocked)  // 0`

const curlSnippet = `# Trading decision evaluation
curl -X POST https://omnixquantum.net/api/governance/evaluate \\
  -H "X-API-Key: OMNIX-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" \\
  -H "Content-Type: application/json" \\
  -d '{
    "domain":  "trading",
    "asset":   "BTC/USD",
    "signals": { "price": 94200, "volume": 1.5, "volatility": 0.18 }
  }'

# Retrieve a signed receipt
curl https://omnixquantum.net/api/governance/receipt/OMNIX-TRD-a3f8b2c1 \\
  -H "X-API-Key: OMNIX-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Generate a due-diligence PDF (last 30 days)
curl "https://omnixquantum.net/api/governance/due-diligence-report?format=pdf&days=30" \\
  -H "X-API-Key: OMNIX-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" \\
  --output omnix_report.pdf`

const responseSnippet = `{
  "decision":           "APPROVED",
  "receipt_id":         "OMNIX-TRD-a3f8b2c1d4e5f678",
  "checkpoints_passed": 11,
  "checkpoints_blocked": 0,
  "timestamp_utc":      "2026-04-16T23:00:00.000Z",
  "asset":              "BTC/USD",
  "domain":             "trading",

  "integrity": {
    "algorithm":    "Dilithium3 (NIST FIPS 204)",
    "is_pqc":       true,
    "content_hash": "a3f8b2c1d4e5f678901234567890abcd...",
    "chain_linked":  true
  },

  "regulatory_alignment": {
    "frameworks_covered": 8,
    "frameworks": [
      { "id": "EU_AI_ACT",     "status": "COMPLIANT" },
      { "id": "NIST_AI_RMF",  "status": "COMPLIANT" },
      { "id": "DORA",          "status": "COMPLIANT" },
      { "id": "FATF",          "status": "COMPLIANT" },
      { "id": "BASEL_III",     "status": "COMPLIANT" },
      { "id": "MiCA",          "status": "COMPLIANT" },
      { "id": "ISO_42001",     "status": "COMPLIANT" },
      { "id": "AAOIFI",        "status": "COMPLIANT" }
    ]
  },

  "verify_url": "https://omnixquantum.net/verify/OMNIX-TRD-a3f8b2c1d4e5f678"
}`

const domainSignals: Record<string, { code: string; color: string; signals: string[] }> = {
  trading: {
    code: 'TRD', color: '#C9A227',
    signals: ['price', 'volume', 'volatility', 'drawdown', 'regime_score', 'coherence_index'],
  },
  islamic_credit: {
    code: 'CRD', color: '#06B6D4',
    signals: ['debt_to_income', 'collateral_ratio', 'sharia_compliant', 'default_probability', 'sector_risk', 'aml_score'],
  },
  insurance: {
    code: 'INS', color: '#8B5CF6',
    signals: ['claim_probability', 'fraud_score', 'exposure_amount', 'reinsurance_ratio', 'reserve_adequacy', 'regulatory_score'],
  },
  robotics: {
    code: 'RBT', color: '#10B981',
    signals: ['collision_probability', 'safety_margin', 'human_proximity', 'task_complexity', 'environment_risk', 'fallback_coverage'],
  },
  medical_ai: {
    code: 'MED', color: '#F472B6',
    signals: ['diagnostic_confidence', 'patient_risk', 'evidence_quality', 'consent_verified', 'clinical_urgency', 'contraindication_score'],
  },
  autonomous_agent: {
    code: 'AGT', color: '#FB923C',
    signals: ['task_complexity', 'blast_radius', 'context_completeness', 'goal_alignment', 'fallback_coverage', 'authorization_score'],
  },
  real_estate: {
    code: 'REP', color: '#38BDF8',
    signals: ['avm_confidence', 'transaction_risk', 'data_alignment', 'market_trajectory', 'stress_resilience', 'regulatory_compliance'],
  },
  energy_governance: {
    code: 'EGV', color: '#00B4D8',
    signals: ['lmp_confidence', 'mw_concentration', 'day_ahead_spread', 'load_accuracy', 'renewable_buffer', 'carbon_intensity'],
  },
  stablecoin_reserve: {
    code: 'SRG', color: '#2dd4bf',
    signals: ['peg_deviation', 'reserve_coverage', 'liquidity_ratio', 'redemption_risk', 'regulatory_compliance', 'market_depth'],
  },
}

const endpoints = [
  { method: 'POST', path: '/api/governance/evaluate',                auth: true,  desc: 'Evaluate a decision through the 11-checkpoint pipeline. Returns signed receipt.' },
  { method: 'GET',  path: '/api/governance/receipt/:id',             auth: true,  desc: 'Retrieve a specific signed receipt by ID.' },
  { method: 'GET',  path: '/api/governance/receipts',                auth: true,  desc: 'List receipts with filters: domain, date range, decision, asset.' },
  { method: 'GET',  path: '/api/governance/due-diligence-report',    auth: true,  desc: 'Generate governance report — JSON or PDF. Supports ?format=pdf&days=30.' },
  { method: 'GET',  path: '/api/governance/regulatory/catalog',      auth: false, desc: 'All regulatory frameworks and their checkpoint mapping across 9 domains.' },
  { method: 'GET',  path: '/api/receipts/public-key',                auth: false, desc: 'Active PQC public key — verify signatures independently.' },
  { method: 'POST', path: '/api/receipts/verify',                    auth: false, desc: 'Cryptographic signature verification (ADR-079).' },
  { method: 'GET',  path: '/verify/:receipt_id',                     auth: false, desc: 'Public human-readable receipt verification page.' },
]

const errorCodes = [
  { code: '400', label: 'Bad Request',   desc: 'Invalid input — check domain, asset, and signal ranges (0–100).' },
  { code: '401', label: 'Unauthorized',  desc: 'Missing or invalid X-API-Key header.' },
  { code: '429', label: 'Rate Limited',  desc: 'Quota exceeded. Contact support@omnixquantum.net for tier upgrades.' },
  { code: '503', label: 'Unavailable',   desc: 'Governance engine temporarily unavailable. Retry with exponential backoff.' },
]

function CodeBlock({ code, lang }: { code: string; lang: string }) {
  const [copied, setCopied] = useState(false)
  const copy = () => {
    navigator.clipboard.writeText(code).catch(() => {})
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <div style={{ background: '#060F1E', border: `1px solid ${GOLD}22`, borderRadius: 12, overflow: 'hidden' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 16px', borderBottom: '1px solid #ffffff08' }}>
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

function SectionTitle({ children }: { children: ReactNode }) {
  return (
    <h2 style={{ fontSize: 11, fontWeight: 800, color: '#444', letterSpacing: '0.15em', textTransform: 'uppercase', marginBottom: 24, display: 'flex', alignItems: 'center', gap: 10 }}>
      <span style={{ flex: 1, height: 1, background: '#ffffff08' }} />
      {children}
      <span style={{ flex: 1, height: 1, background: '#ffffff08' }} />
    </h2>
  )
}

export default function IntegrationGuide() {
  const [tab, setTab]       = useState<'python' | 'node' | 'curl'>('python')
  const [domain, setDomain] = useState<keyof typeof domainSignals>('trading')

  const domainKeys = Object.keys(domainSignals) as (keyof typeof domainSignals)[]
  const selected   = domainSignals[domain]

  return (
    <div style={{ background: DARK, minHeight: '100vh', color: '#F7F9FC', fontFamily: "'Inter', sans-serif" }}>

      {/* ── Header ── */}
      <div style={{ borderBottom: `1px solid ${GOLD}22`, padding: '20px 40px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', position: 'sticky', top: 0, background: DARK, zIndex: 50 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <img src="/omnix_logo.png" alt="OMNIX" style={{ height: 32, objectFit: 'contain' }} />
          <span style={{ color: '#334', margin: '0 8px' }}>|</span>
          <span style={{ fontSize: 14, color: '#888', fontWeight: 600 }}>Integration Guide</span>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <a href="/stack"  style={{ fontSize: 12, color: '#888', border: '1px solid #ffffff18', borderRadius: 8, padding: '6px 14px', textDecoration: 'none' }}>Technical Stack</a>
          <a href="/try"    style={{ fontSize: 12, background: GOLD, color: DARK, borderRadius: 8, padding: '6px 14px', textDecoration: 'none', fontWeight: 800 }}>Live Demo</a>
        </div>
      </div>

      <div style={{ maxWidth: 900, margin: '0 auto', padding: '60px 40px 100px' }}>

        {/* ── Hero ── */}
        <div style={{ marginBottom: 72 }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, background: `${GOLD}15`, border: `1px solid ${GOLD}40`, borderRadius: 20, padding: '6px 18px', fontSize: 11, color: GOLD, fontWeight: 800, letterSpacing: '0.12em', marginBottom: 24 }}>
            <Zap size={12} /> REST API · NO SDK REQUIRED
          </div>
          <h1 style={{ fontSize: 'clamp(28px, 4vw, 44px)', fontWeight: 900, lineHeight: 1.1, margin: '0 0 20px', letterSpacing: '-0.02em' }}>
            Integrate OMNIX in 10 lines of code
          </h1>
          <p style={{ fontSize: 15, color: '#888', lineHeight: 1.8, maxWidth: 620, margin: '0 0 32px' }}>
            One POST request. Every decision returns a post-quantum signed governance receipt
            aligned to 8 regulatory frameworks. No SDK, no dependencies — standard HTTPS.
          </p>

          {/* Quick stats */}
          <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
            {[
              { icon: <Globe size={13} />, label: 'Base URL', value: 'omnixquantum.net' },
              { icon: <Clock size={13} />, label: 'Latency',  value: 'p50 < 800ms' },
              { icon: <Shield size={13} />, label: 'Auth',    value: 'X-API-Key header' },
              { icon: <Lock size={13} />,  label: 'Signing',  value: 'Dilithium3 PQC' },
            ].map(s => (
              <div key={s.label} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
                <span style={{ color: GOLD }}>{s.icon}</span>
                <span style={{ color: '#555' }}>{s.label}:</span>
                <span style={{ color: '#ccc', fontFamily: 'monospace', fontWeight: 600 }}>{s.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* ── Authentication ── */}
        <section style={{ marginBottom: 64 }}>
          <SectionTitle>Authentication</SectionTitle>
          <div style={{ background: CARD, border: `1px solid ${GOLD}18`, borderRadius: 16, padding: '24px 28px' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16, marginBottom: 20 }}>
              <Key size={18} color={GOLD} style={{ flexShrink: 0, marginTop: 2 }} />
              <div>
                <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 6 }}>X-API-Key header — required on all authenticated endpoints</div>
                <div style={{ fontSize: 13, color: '#888', lineHeight: 1.7 }}>
                  Keys have the format <code style={{ background: '#ffffff10', padding: '1px 6px', borderRadius: 4, fontFamily: 'monospace', color: GOLD }}>OMNIX-{'x'.repeat(44)}</code> (48 characters total).
                  Keys are client-scoped, never shared, and revokable. Provided upon contract signature.
                </div>
              </div>
            </div>
            <div style={{ background: '#060F1E', border: `1px solid #ffffff0a`, borderRadius: 10, padding: '14px 18px', fontFamily: 'monospace', fontSize: 12, color: '#cdd' }}>
              curl -H <span style={{ color: GOLD }}>"X-API-Key: OMNIX-xxxx..."</span> https://omnixquantum.net/api/governance/evaluate
            </div>
            <div style={{ marginTop: 16, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
              {[
                { label: 'Rate limit',           value: '120 req / minute per key' },
                { label: 'Advisory quota',        value: '5,000 evaluations / month' },
                { label: 'Professional quota',    value: '50,000 evaluations / month' },
                { label: 'Enterprise',            value: 'Unlimited · all 9 verticals' },
              ].map(q => (
                <div key={q.label} style={{ background: '#ffffff04', border: '1px solid #ffffff08', borderRadius: 8, padding: '10px 14px' }}>
                  <div style={{ fontSize: 10, color: '#555', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 4 }}>{q.label}</div>
                  <div style={{ fontSize: 12, color: '#ccc', fontFamily: 'monospace' }}>{q.value}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Code tabs ── */}
        <section style={{ marginBottom: 64 }}>
          <SectionTitle>Quickstart Code</SectionTitle>
          <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
            {(['python', 'node', 'curl'] as const).map(t => (
              <button key={t} onClick={() => setTab(t)} style={{
                padding: '8px 18px', borderRadius: 8,
                border: `1px solid ${tab === t ? GOLD : '#ffffff18'}`,
                background: tab === t ? `${GOLD}18` : 'transparent',
                color: tab === t ? GOLD : '#666',
                fontSize: 12, fontWeight: 700, cursor: 'pointer', letterSpacing: '0.05em',
              }}>
                {t === 'python' ? 'Python' : t === 'node' ? 'Node.js' : 'cURL'}
              </button>
            ))}
          </div>
          <CodeBlock
            code={tab === 'python' ? pythonSnippet : tab === 'node' ? nodeSnippet : curlSnippet}
            lang={tab === 'python' ? 'python 3.7+ · stdlib requests only' : tab === 'node' ? 'node.js 14+ · stdlib https only' : 'bash · REST API'}
          />
        </section>

        {/* ── 9 Domains ── */}
        <section style={{ marginBottom: 64 }}>
          <SectionTitle>9 Governance Domains</SectionTitle>
          <p style={{ fontSize: 13, color: '#888', marginBottom: 24, lineHeight: 1.7 }}>
            Each domain maps your business signals to OMNIX's 6-signal governance schema.
            The engine applies the same 11-checkpoint pipeline regardless of domain.
          </p>

          {/* Domain selector */}
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 20 }}>
            {domainKeys.map(d => {
              const info = domainSignals[d]
              return (
                <button key={d} onClick={() => setDomain(d)} style={{
                  padding: '6px 14px', borderRadius: 20, fontSize: 11, fontWeight: 700,
                  border: `1px solid ${domain === d ? info.color : '#ffffff18'}`,
                  background: domain === d ? `${info.color}20` : 'transparent',
                  color: domain === d ? info.color : '#666',
                  cursor: 'pointer', letterSpacing: '0.04em',
                }}>
                  {info.code} · {d.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                </button>
              )
            })}
          </div>

          <div style={{ background: CARD, border: `1px solid ${selected.color}30`, borderRadius: 16, padding: '24px 28px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
              <span style={{ fontSize: 11, fontFamily: 'monospace', fontWeight: 800, color: selected.color, background: `${selected.color}20`, padding: '3px 8px', borderRadius: 5 }}>
                domain: "{domain}"
              </span>
              <span style={{ fontSize: 11, fontFamily: 'monospace', color: '#555' }}>receipt prefix: OMNIX-{selected.code}-</span>
            </div>
            <div style={{ fontSize: 13, color: '#888', marginBottom: 16 }}>Required signals for this domain:</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 8 }}>
              {selected.signals.map(sig => (
                <div key={sig} style={{ background: '#ffffff04', border: `1px solid ${selected.color}20`, borderRadius: 8, padding: '8px 12px', fontFamily: 'monospace', fontSize: 12 }}>
                  <span style={{ color: selected.color }}>"</span>
                  <span style={{ color: '#ccc' }}>{sig}</span>
                  <span style={{ color: selected.color }}>"</span>
                  <span style={{ color: '#555' }}>: 0–100</span>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 16, padding: '10px 14px', background: '#ffffff04', borderRadius: 8, fontSize: 11, color: '#555', fontFamily: 'monospace' }}>
              All signal values are normalized to 0–100. Higher = higher risk/confidence (domain-dependent).
              Unknown keys are rejected with HTTP 400 (ADR-080 strict input validation).
            </div>
          </div>
        </section>

        {/* ── Response ── */}
        <section style={{ marginBottom: 64 }}>
          <SectionTitle>Response Structure</SectionTitle>
          <CodeBlock code={responseSnippet} lang="json · every evaluate() response" />
          <div style={{ marginTop: 16, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 10 }}>
            {[
              { icon: <CheckCircle size={12} color={GOLD} />, text: 'decision — APPROVED / BLOCKED / HOLD' },
              { icon: <CheckCircle size={12} color={GOLD} />, text: 'receipt_id — unique, permanent, verifiable' },
              { icon: <CheckCircle size={12} color={GOLD} />, text: 'regulatory_alignment — 8 frameworks' },
              { icon: <CheckCircle size={12} color={GOLD} />, text: 'integrity — Dilithium3 PQC signature' },
              { icon: <CheckCircle size={12} color={GOLD} />, text: 'checkpoints_passed — out of 11' },
              { icon: <CheckCircle size={12} color={GOLD} />, text: 'verify_url — public independent check' },
            ].map(item => (
              <div key={item.text} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: '#888' }}>
                {item.icon} {item.text}
              </div>
            ))}
          </div>
        </section>

        {/* ── Endpoints ── */}
        <section style={{ marginBottom: 64 }}>
          <SectionTitle>API Endpoints</SectionTitle>
          <div style={{ background: CARD, border: `1px solid ${GOLD}18`, borderRadius: 16, overflow: 'hidden' }}>
            {endpoints.map((ep, i) => (
              <div key={ep.path} style={{ padding: '14px 20px', borderBottom: i < endpoints.length - 1 ? '1px solid #ffffff06' : 'none' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
                  <span style={{ fontFamily: 'monospace', fontSize: 11, fontWeight: 800, color: ep.method === 'POST' ? '#F59E0B' : GOLD, minWidth: 36 }}>
                    {ep.method}
                  </span>
                  <span style={{ fontFamily: 'monospace', fontSize: 12, color: '#ccc', flex: 1 }}>{ep.path}</span>
                  <span style={{
                    fontSize: 10, color: ep.auth ? '#8B5CF6' : '#10B981',
                    background: ep.auth ? '#8B5CF620' : '#10B98120',
                    border: `1px solid ${ep.auth ? '#8B5CF6' : '#10B981'}33`,
                    borderRadius: 5, padding: '2px 8px', whiteSpace: 'nowrap', fontWeight: 700,
                  }}>
                    {ep.auth ? 'X-API-Key' : 'Public'}
                  </span>
                </div>
                <div style={{ fontSize: 12, color: '#555', paddingLeft: 48 }}>{ep.desc}</div>
              </div>
            ))}
          </div>
        </section>

        {/* ── Error Codes ── */}
        <section style={{ marginBottom: 64 }}>
          <SectionTitle>Error Codes</SectionTitle>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {errorCodes.map(e => (
              <div key={e.code} style={{ display: 'flex', alignItems: 'flex-start', gap: 16, background: CARD, border: '1px solid #ffffff08', borderRadius: 12, padding: '14px 20px' }}>
                <AlertCircle size={14} color={e.code === '429' ? '#F59E0B' : e.code === '503' ? '#EF4444' : '#6B7280'} style={{ flexShrink: 0, marginTop: 1 }} />
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                    <span style={{ fontFamily: 'monospace', fontSize: 12, fontWeight: 800, color: '#ccc' }}>HTTP {e.code}</span>
                    <span style={{ fontSize: 11, color: '#555' }}>{e.label}</span>
                  </div>
                  <div style={{ fontSize: 12, color: '#888' }}>{e.desc}</div>
                </div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 16, padding: '14px 20px', background: `${GOLD}08`, border: `1px solid ${GOLD}20`, borderRadius: 12, fontSize: 12, color: '#888' }}>
            <strong style={{ color: GOLD }}>Retry policy:</strong> For 503 errors, use exponential backoff starting at 2s.
            For 429 errors, respect the <code style={{ fontFamily: 'monospace', color: GOLD }}>Retry-After</code> header.
            Contact <a href="mailto:support@omnixquantum.net" style={{ color: GOLD }}>support@omnixquantum.net</a> for quota upgrades.
          </div>
        </section>

        {/* ── SLA ── */}
        <section style={{ marginBottom: 64 }}>
          <SectionTitle>SLA & Guarantees</SectionTitle>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
            {[
              { label: 'Uptime SLA',        value: '99.9%', sub: 'Advisory+' },
              { label: 'Evaluation latency', value: 'p50 < 800ms', sub: 'p99 < 3s' },
              { label: 'Receipt retention',  value: 'Permanent', sub: 'append-only ledger' },
              { label: 'PQC signing',        value: 'Every receipt', sub: 'Dilithium3 FIPS 204' },
              { label: 'Audit trail',        value: 'Full chain', sub: 'hash-linked' },
              { label: 'Fail mode',          value: 'Fail-closed', sub: 'uncertainty → BLOCK' },
            ].map(s => (
              <div key={s.label} style={{ background: CARD, border: `1px solid #ffffff08`, borderRadius: 14, padding: '20px 18px', textAlign: 'center' }}>
                <div style={{ fontSize: 18, fontWeight: 900, fontFamily: 'monospace', color: GOLD, marginBottom: 4 }}>{s.value}</div>
                <div style={{ fontSize: 11, fontWeight: 700, color: '#ccc', marginBottom: 2 }}>{s.label}</div>
                <div style={{ fontSize: 10, color: '#555' }}>{s.sub}</div>
              </div>
            ))}
          </div>
        </section>

        {/* ── Integration Steps ── */}
        <section style={{ marginBottom: 64 }}>
          <SectionTitle>Integration Checklist</SectionTitle>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {[
              { n: '01', icon: <Key size={16} color={GOLD} />,      title: 'Get your API key', desc: 'Provided upon contract signature. Format: OMNIX-XXXX (48 chars). Scoped per client, revokable on demand.' },
              { n: '02', icon: <Terminal size={16} color={GOLD} />, title: 'Choose your domain', desc: 'Select one of 9 governance domains: trading, islamic_credit, insurance, robotics, medical_ai, autonomous_agent, real_estate, energy_governance, stablecoin_reserve.' },
              { n: '03', icon: <Zap size={16} color={GOLD} />,      title: 'POST to evaluate()', desc: 'Pass domain, asset name, and 6 normalized signals (0–100). Receive decision + PQC-signed receipt in < 800ms.' },
              { n: '04', icon: <Shield size={16} color={GOLD} />,   title: 'Store receipt_id', desc: 'The receipt_id is your cryptographic proof. Use it for regulatory reporting, LP due diligence, or internal audit.' },
              { n: '05', icon: <FileText size={16} color={GOLD} />, title: 'Download PDF report', desc: 'One API call generates a branded governance report for any time window — ready for regulatory review or LP presentation.' },
            ].map(step => (
              <div key={step.n} style={{ display: 'flex', gap: 16, alignItems: 'flex-start', background: CARD, border: '1px solid #ffffff08', borderRadius: 14, padding: '18px 22px' }}>
                <div style={{ flexShrink: 0, width: 40, height: 40, borderRadius: 10, background: `${GOLD}12`, border: `1px solid ${GOLD}30`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  {step.icon}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                    <span style={{ fontSize: 10, color: '#555', fontFamily: 'monospace', fontWeight: 700 }}>{step.n}</span>
                    <span style={{ fontWeight: 700, fontSize: 14 }}>{step.title}</span>
                  </div>
                  <p style={{ fontSize: 13, color: '#888', lineHeight: 1.65, margin: 0 }}>{step.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ── CTA ── */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 14 }}>
          <a href="/try" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: `${GOLD}12`, border: `1px solid ${GOLD}40`, borderRadius: 14, padding: '22px 24px', textDecoration: 'none' }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: GOLD, marginBottom: 4 }}>Try the live sandbox</div>
              <div style={{ fontSize: 12, color: '#888' }}>No API key needed · generates real receipts</div>
            </div>
            <ArrowRight size={18} color={GOLD} />
          </a>
          <a href="/verify" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: CARD, border: '1px solid #ffffff18', borderRadius: 14, padding: '22px 24px', textDecoration: 'none' }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#ddd', marginBottom: 4 }}>Verify a receipt</div>
              <div style={{ fontSize: 12, color: '#888' }}>Public · no login required</div>
            </div>
            <ArrowRight size={18} color='#888' />
          </a>
          <a href="mailto:support@omnixquantum.net?subject=API Key Request" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: CARD, border: '1px solid #ffffff18', borderRadius: 14, padding: '22px 24px', textDecoration: 'none' }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#ddd', marginBottom: 4 }}>Request API access</div>
              <div style={{ fontSize: 12, color: '#888' }}>support@omnixquantum.net</div>
            </div>
            <ArrowRight size={18} color='#888' />
          </a>
        </div>

      </div>

      <footer style={{ borderTop: `1px solid ${GOLD}15`, padding: '24px 40px', textAlign: 'center' }}>
        <p style={{ fontSize: 12, color: '#333355', margin: 0 }}>
          © 2026 OMNIX Quantum Ltd · 71-75 Shelton Street, Covent Garden, London WC2H 9JQ ·{' '}
          <a href="mailto:support@omnixquantum.net" style={{ color: GOLD, textDecoration: 'none' }}>support@omnixquantum.net</a>
        </p>
      </footer>
    </div>
  )
}
