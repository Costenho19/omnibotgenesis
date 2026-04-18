import { CheckCircle, Shield, Lock, FileText, ArrowRight, Link } from 'lucide-react'

const GOLD = '#C9A227'
const DARK = '#0A1628'

const checkpoints = [
  { id: 'CP-1',  name: 'Signal Integrity Validator',    frameworks: ['NIST AI RMF', 'EU AI Act', 'ISO 42001', 'CA SB 243'] },
  { id: 'CP-2',  name: 'Probability Assessment',         frameworks: ['NIST AI RMF', 'DORA', 'Basel III', 'EU AI Act'] },
  { id: 'CP-3',  name: 'Risk Evaluation',                frameworks: ['DORA', 'NIST AI RMF', 'Basel III', 'EU AI Act'] },
  { id: 'CP-4',  name: 'Coherence Engine',               frameworks: ['NIST AI RMF', 'ISO 42001', 'EU AI Act'] },
  { id: 'CP-5',  name: 'Trend Validator',                frameworks: ['NIST AI RMF', 'DORA', 'Basel III'] },
  { id: 'CP-6',  name: 'Stress Testing',                 frameworks: ['DORA', 'NIST AI RMF', 'Basel III', 'EU AI Act'] },
  { id: 'CP-7',  name: 'Ethics & Domain Gate',           frameworks: ['EU AI Act', 'NIST AI RMF', 'ISO 42001', 'CA SB 243'] },
  { id: 'CP-8',  name: 'Threshold & Context Validator',  frameworks: ['NIST AI RMF', 'DORA', 'ISO 42001'] },
  { id: 'CP-9',  name: 'AML Screening',                  frameworks: ['FATF', 'EU AI Act', 'DORA', 'CA SB 243'] },
  { id: 'CP-10', name: 'Fraud Detection',                frameworks: ['NIST AI RMF', 'EU AI Act', 'DORA', 'CA SB 243'] },
  { id: 'CP-11', name: 'Jurisdiction Compliance',        frameworks: ['EU AI Act', 'GDPR', 'DORA', 'CA SB 243', 'ISO 42001'] },
]

const frameworks = [
  { id: 'EU AI Act',    color: '#3B82F6' },
  { id: 'NIST AI RMF', color: GOLD },
  { id: 'DORA',        color: '#8B5CF6' },
  { id: 'ISO 42001',   color: '#10B981' },
  { id: 'CA SB 243',   color: '#F59E0B' },
  { id: 'GDPR',        color: '#06B6D4' },
  { id: 'FATF',        color: '#EF4444' },
  { id: 'Basel III',   color: '#EC4899' },
]

const layers = [
  {
    icon: <Shield size={22} color={GOLD} />,
    title: 'Governance Layer',
    status: 'Production-Ready',
    desc: '11-checkpoint sequential pipeline evaluates every decision before execution. Each checkpoint enforces ≥3 regulatory references. Cannot be bypassed.',
    items: ['11 sequential checkpoints', 'APPROVE / BLOCK / HOLD per domain', 'Immutable decision log', 'Post-quantum receipt per evaluation'],
  },
  {
    icon: <FileText size={22} color={GOLD} />,
    title: 'Audit Layer',
    status: 'Production-Ready',
    desc: 'Cryptographically signed receipts chain-linked to the OMNIX Transparency Chain. Every receipt is verifiable independently at /verify.',
    items: ['NIST-standardized post-quantum signatures', 'On-chain receipt anchoring', 'Public verification endpoint', 'Due diligence PDF on demand'],
  },
  {
    icon: <Link size={22} color={GOLD} />,
    title: 'Integration Interface',
    status: 'Production-Ready',
    desc: 'REST API + Python/Node.js SDKs. 10-line integration. Structured JSON receipts with regulatory alignment metadata included in every response.',
    items: ['REST API with RBAC + rate limits', 'Python SDK (stdlib-only)', 'Node.js SDK (stdlib-only)', 'regulatory_alignment in every receipt'],
  },
]

export default function TechnicalStack() {
  return (
    <div style={{ background: DARK, minHeight: '100vh', color: '#F7F9FC', fontFamily: "'Inter', sans-serif" }}>

      {/* Header */}
      <div style={{ borderBottom: `1px solid ${GOLD}22`, padding: '28px 40px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <img src="/logo.png" alt="OMNIX" style={{ width: 28, height: 28, borderRadius: 4, objectFit: 'contain' }} />
          <span style={{ fontWeight: 800, fontSize: 18, color: GOLD, letterSpacing: '0.08em' }}>OMNIX</span>
          <span style={{ color: '#444466', margin: '0 8px' }}>|</span>
          <span style={{ fontSize: 14, color: '#999' }}>Technical Stack Summary</span>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <a href="/try" style={{ fontSize: 12, color: GOLD, border: `1px solid ${GOLD}44`, borderRadius: 8, padding: '6px 14px', textDecoration: 'none' }}>Live Demo</a>
          <a href="/integration" style={{ fontSize: 12, background: GOLD, color: DARK, borderRadius: 8, padding: '6px 14px', textDecoration: 'none', fontWeight: 700 }}>Integration Guide</a>
        </div>
      </div>

      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '60px 40px' }}>

        {/* Hero */}
        <div style={{ textAlign: 'center', marginBottom: 64 }}>
          <div style={{ display: 'inline-block', background: `${GOLD}18`, border: `1px solid ${GOLD}44`, borderRadius: 20, padding: '6px 18px', fontSize: 12, color: GOLD, fontWeight: 700, letterSpacing: '0.1em', marginBottom: 24 }}>
            VALIDATED · APRIL 2026
          </div>
          <h1 style={{ fontSize: 'clamp(28px, 5vw, 48px)', fontWeight: 900, lineHeight: 1.1, margin: '0 0 20px', letterSpacing: '-0.02em' }}>
            Decision Governance Infrastructure
          </h1>
          <p style={{ fontSize: 16, color: '#888', maxWidth: 620, margin: '0 auto 32px', lineHeight: 1.7 }}>
            The full stack is validated — governance, audit layer, and integration interface
            are aligned and production-ready. Domain-agnostic. Post-quantum signed.
          </p>
          <div style={{ display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap' }}>
            {[
              { v: '11', l: 'Checkpoints' },
              { v: '8', l: 'Regulatory Frameworks' },
              { v: '9', l: 'Industry Domains' },
              { v: 'W3C VC', l: 'Receipt Format' },
            ].map(({ v, l }) => (
              <div key={l} style={{ background: '#111830', border: `1px solid ${GOLD}22`, borderRadius: 12, padding: '16px 24px', textAlign: 'center', minWidth: 100 }}>
                <div style={{ fontSize: 26, fontWeight: 900, color: GOLD }}>{v}</div>
                <div style={{ fontSize: 11, color: '#666', marginTop: 4, letterSpacing: '0.06em' }}>{l.toUpperCase()}</div>
              </div>
            ))}
          </div>
        </div>

        {/* 3 Layers */}
        <section style={{ marginBottom: 72 }}>
          <h2 style={{ fontSize: 13, fontWeight: 700, color: '#555', letterSpacing: '0.12em', marginBottom: 24 }}>ARCHITECTURE LAYERS</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 20 }}>
            {layers.map(layer => (
              <div key={layer.title} style={{ background: '#0D1E35', border: `1px solid ${GOLD}25`, borderRadius: 16, padding: 28, borderTop: `3px solid ${GOLD}` }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                  {layer.icon}
                  <span style={{ fontWeight: 800, fontSize: 15 }}>{layer.title}</span>
                </div>
                <div style={{ display: 'inline-block', background: '#0f2a1a', border: '1px solid #1a5c2a', borderRadius: 6, padding: '2px 10px', fontSize: 11, color: '#4ade80', fontWeight: 700, letterSpacing: '0.08em', marginBottom: 14 }}>
                  ✓ {layer.status}
                </div>
                <p style={{ fontSize: 13, color: '#888', lineHeight: 1.7, marginBottom: 16 }}>{layer.desc}</p>
                <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {layer.items.map(item => (
                    <li key={item} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: '#aaa' }}>
                      <CheckCircle size={12} color={GOLD} />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>

        {/* 11 Checkpoints table */}
        <section style={{ marginBottom: 72 }}>
          <h2 style={{ fontSize: 13, fontWeight: 700, color: '#555', letterSpacing: '0.12em', marginBottom: 24 }}>11-CHECKPOINT PIPELINE</h2>
          <div style={{ background: '#0D1E35', border: `1px solid ${GOLD}22`, borderRadius: 16, overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: `1px solid ${GOLD}22` }}>
                  <th style={{ textAlign: 'left', padding: '12px 20px', fontSize: 11, color: '#555', fontWeight: 700, letterSpacing: '0.08em', width: 70 }}>ID</th>
                  <th style={{ textAlign: 'left', padding: '12px 20px', fontSize: 11, color: '#555', fontWeight: 700, letterSpacing: '0.08em' }}>CHECKPOINT</th>
                  <th style={{ textAlign: 'left', padding: '12px 20px', fontSize: 11, color: '#555', fontWeight: 700, letterSpacing: '0.08em' }}>REGULATORY COVERAGE</th>
                </tr>
              </thead>
              <tbody>
                {checkpoints.map((cp, i) => (
                  <tr key={cp.id} style={{ borderBottom: i < checkpoints.length - 1 ? `1px solid #ffffff08` : 'none' }}>
                    <td style={{ padding: '10px 20px', fontSize: 12, color: GOLD, fontWeight: 700, fontFamily: 'monospace' }}>{cp.id}</td>
                    <td style={{ padding: '10px 20px', fontSize: 13, color: '#ddd', fontWeight: 600 }}>{cp.name}</td>
                    <td style={{ padding: '10px 20px' }}>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                        {cp.frameworks.map(fw => {
                          const fwMeta = frameworks.find(f => f.id === fw)
                          return (
                            <span key={fw} style={{ fontSize: 10, padding: '2px 7px', borderRadius: 4, background: `${fwMeta?.color || '#888'}18`, color: fwMeta?.color || '#888', border: `1px solid ${fwMeta?.color || '#888'}33`, fontWeight: 600, letterSpacing: '0.04em' }}>
                              {fw}
                            </span>
                          )
                        })}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* 8 Frameworks */}
        <section style={{ marginBottom: 72 }}>
          <h2 style={{ fontSize: 13, fontWeight: 700, color: '#555', letterSpacing: '0.12em', marginBottom: 24 }}>8 REGULATORY FRAMEWORKS</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 12 }}>
            {frameworks.map(fw => (
              <div key={fw.id} style={{ background: '#0D1E35', border: `1px solid ${fw.color}33`, borderRadius: 12, padding: '14px 18px', borderLeft: `3px solid ${fw.color}` }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: '#ddd' }}>{fw.id}</div>
              </div>
            ))}
          </div>
        </section>

        {/* Domains */}
        <section style={{ marginBottom: 72 }}>
          <h2 style={{ fontSize: 13, fontWeight: 700, color: '#555', letterSpacing: '0.12em', marginBottom: 24 }}>DOMAIN COVERAGE</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12 }}>
            {[
              { name: 'Algorithmic Trading', link: '/try' },
              { name: 'Islamic Credit', link: '/credit' },
              { name: 'Insurance', link: '/insurance' },
              { name: 'Industrial Robotics', link: '/robotics' },
              { name: 'Medical AI', link: '/medical' },
              { name: 'Autonomous Agents', link: '/agents' },
              { name: 'Energy Governance', link: '/energy' },
              { name: 'Real Estate & PropTech', link: '/real-estate' },
              { name: 'Stablecoin Reserve Governance', link: '/stablecoin' },
            ].map(d => (
              <a key={d.name} href={d.link} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#0D1E35', border: `1px solid ${GOLD}22`, borderRadius: 12, padding: '16px 18px', textDecoration: 'none' }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: '#ddd' }}>{d.name}</span>
                <ArrowRight size={14} color={GOLD} />
              </a>
            ))}
          </div>
        </section>

        {/* CTA */}
        <div style={{ background: `${GOLD}10`, border: `1px solid ${GOLD}33`, borderRadius: 20, padding: '40px', textAlign: 'center' }}>
          <Lock size={28} color={GOLD} style={{ marginBottom: 16 }} />
          <h3 style={{ fontSize: 22, fontWeight: 800, marginBottom: 12 }}>Ready for integration</h3>
          <p style={{ color: '#888', fontSize: 14, marginBottom: 28, maxWidth: 500, margin: '0 auto 28px' }}>
            Full REST API + Python/Node.js SDKs. Due diligence PDF on demand. Client portal included.
          </p>
          <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
            <a href="/try" style={{ background: GOLD, color: DARK, borderRadius: 10, padding: '12px 28px', textDecoration: 'none', fontWeight: 800, fontSize: 14 }}>
              Try Live Demo
            </a>
            <a href="/integration" style={{ border: `1px solid ${GOLD}44`, color: GOLD, borderRadius: 10, padding: '12px 28px', textDecoration: 'none', fontWeight: 700, fontSize: 14 }}>
              Integration Guide
            </a>
            <a href="/verify" style={{ border: `1px solid #ffffff22`, color: '#888', borderRadius: 10, padding: '12px 28px', textDecoration: 'none', fontWeight: 600, fontSize: 14 }}>
              Verify a Receipt
            </a>
          </div>
        </div>

      </div>

      <footer style={{ borderTop: `1px solid ${GOLD}15`, padding: '24px 40px', textAlign: 'center' }}>
        <p style={{ fontSize: 12, color: '#444466' }}>© 2026 OMNIX Quantum · Harold Nunes · omnixquantum.net</p>
      </footer>
    </div>
  )
}
