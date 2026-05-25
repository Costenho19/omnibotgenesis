import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Shield, Lock, CheckCircle, ArrowRight, ExternalLink, Terminal, Layers, Globe, FileCheck, Cpu, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react'

// ── Design System ──────────────────────────────────────────────────────────────
const GOLD        = '#C9A227'
const GOLD_DIM    = 'rgba(201,162,39,0.10)'
const GOLD_BORDER = 'rgba(201,162,39,0.22)'
const NAVY        = '#060F1E'
const NAVY2       = '#0A1628'
const NAVY3       = '#0D1E38'
const GREEN       = '#22c55e'
const GREEN_DIM   = 'rgba(34,197,94,0.08)'
const GREEN_BORDER= 'rgba(34,197,94,0.22)'
const BLUE        = '#3b82f6'
const BLUE_DIM    = 'rgba(59,130,246,0.09)'
const BLUE_BORDER = 'rgba(59,130,246,0.22)'
const AMBER       = '#f59e0b'
const AMBER_DIM   = 'rgba(245,158,11,0.09)'
const PURPLE      = '#a855f7'
const PURPLE_DIM  = 'rgba(168,85,247,0.09)'
const PURPLE_BORDER='rgba(168,85,247,0.22)'
const TEXT        = '#e2e8f0'
const MUTED       = '#94a3b8'
const DIMMED      = '#64748b'

// ── Receipt animation ──────────────────────────────────────────────────────────
const RECEIPT_FIELDS = [
  { key: 'receipt_id',           value: 'ATFDR-8F2A1C4E9B7D3F6A',   label: 'Receipt ID',           color: GOLD },
  { key: 'receipt_type',         value: 'DR',                         label: 'Type',                 color: BLUE },
  { key: 'issuer',               value: 'OMNIX-PRINCIPAL-001',        label: 'Issuer',               color: TEXT },
  { key: 'delegate',             value: 'AGENT-EXECUTOR-7F2',         label: 'Delegate',             color: TEXT },
  { key: 'authority_budget',     value: '42.0',                       label: 'Authority Budget',     color: AMBER },
  { key: 'task_scope',           value: 'EXECUTE:TRADE:BTC:LONG',     label: 'Task Scope',           color: TEXT },
  { key: 'delegation_depth',     value: '2',                          label: 'Depth',                color: TEXT },
  { key: 'temporal_bound_utc',   value: '2026-05-20T19:30:00Z',       label: 'Temporal Bound',       color: AMBER },
  { key: 'content_hash',         value: 'sha256:a3f8c2d1...e7b4',     label: 'Content Hash',         color: GOLD },
  { key: 'pqc_algorithm',        value: 'ML-DSA-65 (FIPS 204)',       label: 'PQC Algorithm',        color: GREEN },
  { key: 'signature',            value: 'Dilithium3:3e9f1a2b...d4c8', label: 'Signature',            color: GREEN },
  { key: 'invariants_verified',  value: 'ATF-INV-001–006 ✓',         label: 'Invariants',           color: GREEN },
  { key: 'admission_status',     value: 'ADMITTED',                   label: 'Status',               color: GREEN },
]

const DIFFERENTIATORS = [
  {
    icon: <Lock size={22} />,
    color: GOLD,
    dim: GOLD_DIM,
    border: GOLD_BORDER,
    title: 'Post-Quantum Cryptography',
    subtitle: 'ML-DSA-65 · FIPS 204 · Dilithium-3',
    body: 'Every receipt is signed with Dilithium-3 at issuance. Verifiable against any future quantum-capable adversary. 3–5 year technical moat with no equivalent in current RegTech.',
  },
  {
    icon: <Globe size={22} />,
    color: BLUE,
    dim: BLUE_DIM,
    border: BLUE_BORDER,
    title: 'Runtime-Independent Verification',
    subtitle: 'ATF-INV-006 · ATORS Schema',
    body: 'Receipts are verifiable offline using the standalone CLI. No OMNIX runtime required. A forensic examiner, regulator, or third-party auditor can verify any receipt in isolation — without access to your infrastructure.',
  },
  {
    icon: <Layers size={22} />,
    color: PURPLE,
    dim: PURPLE_DIM,
    border: PURPLE_BORDER,
    title: '67 Formally Specified Invariants',
    subtitle: '3 Published RFCs · Zenodo · Figshare',
    body: 'ATF invariants are not assertions in a test file. They are formally published specifications with permanent academic DOIs. RFC-ATF-1/2/3 are citable records, not marketing claims.',
  },
  {
    icon: <FileCheck size={22} />,
    color: GREEN,
    dim: GREEN_DIM,
    border: GREEN_BORDER,
    title: 'Open Receipt Schema',
    subtitle: 'ATORS · ADR-172 · Machine-Readable',
    body: 'The ATF Open Receipt Schema is published, versioned, and language-agnostic. Any system that speaks JSON Schema can parse, validate, and semantically interpret OMNIX receipts without integration.',
  },
  {
    icon: <Cpu size={22} />,
    color: AMBER,
    dim: AMBER_DIM,
    border: 'rgba(245,158,11,0.22)',
    title: 'Cross-Runtime Interoperability',
    subtitle: 'SGIP · ADR-171 · CRGC',
    body: 'Two runtimes — different jurisdictions, different regulatory frameworks — can establish a bilaterally signed Cross-Runtime Governance Contract. Semantic divergence surfaces are exposed, not hidden.',
  },
  {
    icon: <Shield size={22} />,
    color: TEXT,
    dim: 'rgba(226,232,240,0.06)',
    border: 'rgba(226,232,240,0.14)',
    title: 'Structural Shift Detection',
    subtitle: 'SSD · ADR-175 · CRSI Algorithm',
    body: 'Continuous monitoring distinguishes incremental assumption drift from structural regime change. The CRSI (Cumulative Regime Shift Index) detects when a governance assumption boundary has been crossed — not just that drift occurred.',
  },
]

const PRICING = [
  {
    tier: 'VERIFIER',
    price: 'Free',
    period: 'Open',
    color: DIMMED,
    border: 'rgba(100,116,139,0.22)',
    dim: 'rgba(100,116,139,0.06)',
    badge: 'Open Source',
    badgeColor: DIMMED,
    target: 'Researchers · Auditors · Regulators',
    features: [
      'Standalone offline verifier (zero dependencies)',
      'ATF Open Receipt Schema (ATORS)',
      'Public RFC documentation',
      'Receipt verification UI (/atf-verify)',
      'Conformance vectors for self-testing',
    ],
    cta: 'Download Verifier',
    ctaLink: '/atf-verify',
    ctaStyle: 'secondary',
  },
  {
    tier: 'BUILDER',
    price: '$500',
    period: '/month',
    color: BLUE,
    border: BLUE_BORDER,
    dim: BLUE_DIM,
    badge: 'Most Accessible',
    badgeColor: BLUE,
    target: 'Fintech Builders · AI Developers · Startups',
    features: [
      '1,000 signed governance receipts/month',
      'DR + TAR receipt types (ATF L1–L2)',
      'API key via B2B provisioning',
      'Audit dashboard access',
      'ATORS-compliant receipts',
      'Email support · 48h SLA',
    ],
    cta: 'Request Access',
    ctaLink: '/institutional',
    ctaStyle: 'primary',
  },
  {
    tier: 'PROFESSIONAL',
    price: '$2,000',
    period: '/month',
    color: GOLD,
    border: GOLD_BORDER,
    dim: GOLD_DIM,
    badge: 'Recommended',
    badgeColor: GOLD,
    target: 'Asset Managers · Regulated Fintechs · Trading Firms',
    features: [
      '10,000 signed governance receipts/month',
      'Full ATF stack: DR + TAR + RCR + SAC',
      'SGIP cross-runtime interoperability',
      'Forensic export packages (OEP)',
      'AGVP proactive veto receipts',
      'SSD structural shift reports',
      'Priority support · 24h SLA',
    ],
    cta: 'Contact Sales',
    ctaLink: '/institutional',
    ctaStyle: 'gold',
  },
  {
    tier: 'ENTERPRISE',
    price: 'Custom',
    period: 'from $10,000/mo',
    color: PURPLE,
    border: PURPLE_BORDER,
    dim: PURPLE_DIM,
    badge: 'Institutional',
    badgeColor: PURPLE,
    target: 'Banks · Sovereign Funds · Regulatory Bodies',
    features: [
      'Unlimited receipt issuance',
      'Dedicated deployment (on-premise / private cloud)',
      'Full ATF + SGIP + DSPP stack',
      'Custom CRGC negotiation',
      'Compliance documentation package',
      'EU AI Act · ADGM · MiFID-II alignment',
      'Dedicated governance engineer · onboarding',
      '99.9% SLA · 4h response',
    ],
    cta: 'Schedule Review',
    ctaLink: '/institutional',
    ctaStyle: 'purple',
  },
]

const ENDPOINTS = [
  { method: 'POST', path: '/api/governance/evaluate',         desc: 'Submit signals for governance evaluation. Returns PQC-signed receipt.' },
  { method: 'GET',  path: '/api/governance/receipts',         desc: 'List receipts for authenticated client. Paginated.' },
  { method: 'GET',  path: '/api/governance/receipts/:id',     desc: 'Retrieve a specific receipt by ID.' },
  { method: 'POST', path: '/api/forensic/verify',             desc: 'Verify a receipt (L1–L5). No runtime dependency required.' },
  { method: 'GET',  path: '/api/forensic/export',             desc: 'Generate OEP forensic export package for auditors.' },
  { method: 'GET',  path: '/api/governance/schema',           desc: 'Retrieve current ATORS schema version.' },
]

const FAQ = [
  {
    q: 'Is OMNIX a financial advisory service?',
    a: 'No. OMNIX Governance API is decision governance infrastructure — RegTech SaaS. OMNIX does not provide financial advice, investment recommendations, trading signals, or asset management of any kind. OMNIX provides the cryptographic infrastructure to prove that a governance process was followed. What you decide is yours. OMNIX proves how you decided.',
  },
  {
    q: 'Can receipts be verified without OMNIX infrastructure?',
    a: 'Yes. ATF-INV-006 (Independent Verifiability) is a core invariant: verification must be possible using only the receipt and the root public key — no OMNIX runtime, no live database, no API call. The standalone verifier (sdk/python/omnix_atf_verify.py) implements this with zero dependencies.',
  },
  {
    q: 'What regulations does OMNIX help with?',
    a: 'OMNIX receipts are designed to support audit trail requirements under EU AI Act (Article 9 risk management), ADGM AI Governance Framework, MiFID-II explainability obligations, and US Executive Order 14110. OMNIX does not provide legal advice — clients should verify specific regulatory applicability with qualified legal counsel.',
  },
  {
    q: 'What is the difference between BUILDER and PROFESSIONAL?',
    a: 'BUILDER provides the core DR + TAR receipt types — sufficient for basic delegation and temporal authority governance. PROFESSIONAL adds the full ATF stack including Runtime Continuity Records (RCR), Semantic Alignment Certificates (SAC), cross-runtime interoperability (SGIP), forensic export packages (OEP), and structural shift detection (SSD). Regulated entities typically require PROFESSIONAL or above.',
  },
  {
    q: 'How does cross-runtime interoperability work?',
    a: 'Two runtimes can establish a Cross-Runtime Governance Contract (CRGC) under SGIP (ADR-171). The CRGC is a bilaterally signed document that aligns numerical governance parameters and exposes semantic divergence surfaces — the points where the two systems hold different operational definitions of authority, admissibility, or legitimacy. This makes cross-system governance decisions transparent and auditable.',
  },
]

// ── Component ──────────────────────────────────────────────────────────────────
export default function GovernanceAPIPage() {
  const [visibleFields, setVisibleFields] = useState(0)
  const [openFaq, setOpenFaq] = useState<number | null>(null)

  useEffect(() => {
    if (visibleFields >= RECEIPT_FIELDS.length) return
    const t = setTimeout(() => setVisibleFields(v => v + 1), 90)
    return () => clearTimeout(t)
  }, [visibleFields])

  return (
    <div style={{ background: NAVY, color: TEXT, fontFamily: "'Inter', system-ui, sans-serif", minHeight: '100vh' }}>

      {/* ── NAV ──────────────────────────────────────────────────────────────── */}
      <nav style={{
        position: 'sticky', top: 0, zIndex: 100,
        background: 'rgba(6,15,30,0.96)', backdropFilter: 'blur(12px)',
        borderBottom: `1px solid ${GOLD_BORDER}`,
        padding: '0 2rem', height: 60,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 10 }}>
          <Shield size={20} color={GOLD} />
          <span style={{ color: GOLD, fontWeight: 700, fontSize: 15, letterSpacing: '0.05em' }}>OMNIX QUANTUM</span>
        </Link>
        <div style={{ display: 'flex', gap: 24, alignItems: 'center' }}>
          <Link to="/trust-infrastructure" style={{ color: MUTED, textDecoration: 'none', fontSize: 13 }}>Architecture</Link>
          <Link to="/atf-standard" style={{ color: MUTED, textDecoration: 'none', fontSize: 13 }}>Standards</Link>
          <Link to="/institutional" style={{
            background: GOLD_DIM, border: `1px solid ${GOLD_BORDER}`,
            color: GOLD, padding: '6px 14px', borderRadius: 6,
            textDecoration: 'none', fontSize: 13, fontWeight: 600,
          }}>Contact Sales</Link>
        </div>
      </nav>

      {/* ── HERO ─────────────────────────────────────────────────────────────── */}
      <section style={{ padding: '100px 2rem 80px', maxWidth: 1100, margin: '0 auto' }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          background: GOLD_DIM, border: `1px solid ${GOLD_BORDER}`,
          borderRadius: 20, padding: '5px 14px', marginBottom: 28,
        }}>
          <div style={{ width: 7, height: 7, borderRadius: '50%', background: GREEN, boxShadow: `0 0 6px ${GREEN}` }} />
          <span style={{ fontSize: 11, color: GOLD, fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
            ADR-176 · OMNIX-PRODUCT-GOV-API-001
          </span>
        </div>

        <h1 style={{
          fontSize: 'clamp(2.2rem, 5vw, 3.8rem)', fontWeight: 800,
          lineHeight: 1.1, marginBottom: 24, letterSpacing: '-0.02em',
        }}>
          Decision governance<br />
          <span style={{ color: GOLD }}>infrastructure.</span><br />
          Post-quantum. Auditable.<br />
          Runtime-independent.
        </h1>

        <p style={{ fontSize: 18, color: MUTED, maxWidth: 600, lineHeight: 1.7, marginBottom: 40 }}>
          OMNIX issues cryptographically signed governance receipts for every AI decision.
          Formally specified. 67 invariants. 4 published RFCs. Verifiable by any auditor
          without OMNIX infrastructure.
        </p>

        <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap' }}>
          <Link to="/institutional" style={{
            background: GOLD, color: NAVY, padding: '13px 28px', borderRadius: 8,
            textDecoration: 'none', fontWeight: 700, fontSize: 15,
            display: 'flex', alignItems: 'center', gap: 8,
          }}>
            Request Access <ArrowRight size={16} />
          </Link>
          <Link to="/atf-verify" style={{
            background: 'transparent', color: TEXT,
            border: `1px solid rgba(226,232,240,0.2)`,
            padding: '13px 28px', borderRadius: 8,
            textDecoration: 'none', fontWeight: 600, fontSize: 15,
            display: 'flex', alignItems: 'center', gap: 8,
          }}>
            <Terminal size={16} /> Verify a Receipt
          </Link>
        </div>

        <div style={{ display: 'flex', gap: 32, marginTop: 56, flexWrap: 'wrap' }}>
          {[
            { v: '67', l: 'Formal Invariants' },
            { v: '3', l: 'Published RFCs' },
            { v: '245+', l: 'Institutional Tests' },
            { v: 'FIPS 204', l: 'PQC Standard' },
            { v: '175', l: 'Architecture Decisions' },
          ].map(s => (
            <div key={s.v}>
              <div style={{ fontSize: 26, fontWeight: 800, color: GOLD }}>{s.v}</div>
              <div style={{ fontSize: 12, color: MUTED, marginTop: 2 }}>{s.l}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── RECEIPT ANATOMY ──────────────────────────────────────────────────── */}
      <section style={{ padding: '80px 2rem', background: NAVY2 }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) minmax(0,1fr)', gap: 60, alignItems: 'center' }}>

            <div>
              <div style={{ fontSize: 11, color: GOLD, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 12, fontWeight: 600 }}>
                The Governance Receipt
              </div>
              <h2 style={{ fontSize: 32, fontWeight: 800, marginBottom: 16, lineHeight: 1.2 }}>
                Not a log entry.<br />A cryptographic contract.
              </h2>
              <p style={{ color: MUTED, lineHeight: 1.7, marginBottom: 20 }}>
                Every governance decision OMNIX processes produces a signed receipt.
                The receipt binds together identity, delegation scope, temporal authority,
                and the full execution context — signed with Dilithium-3 at the nanosecond
                of issuance.
              </p>
              <p style={{ color: MUTED, lineHeight: 1.7, marginBottom: 28 }}>
                Retroactive falsification is cryptographically impossible. Independent
                verification requires only the receipt and the platform public key —
                no OMNIX server, no live database.
              </p>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                {['ATF-INV-001', 'ATF-INV-005', 'ATF-INV-006'].map(inv => (
                  <span key={inv} style={{
                    background: GOLD_DIM, border: `1px solid ${GOLD_BORDER}`,
                    color: GOLD, fontSize: 11, padding: '4px 10px', borderRadius: 4,
                    fontFamily: 'monospace', fontWeight: 600,
                  }}>{inv}</span>
                ))}
              </div>
            </div>

            <div style={{
              background: '#040c1a', border: `1px solid ${GOLD_BORDER}`,
              borderRadius: 12, padding: '20px 24px', fontFamily: 'monospace', fontSize: 12.5,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16, paddingBottom: 12, borderBottom: `1px solid rgba(201,162,39,0.12)` }}>
                <div style={{ width: 8, height: 8, borderRadius: '50%', background: GREEN, boxShadow: `0 0 5px ${GREEN}` }} />
                <span style={{ color: MUTED, fontSize: 11 }}>ATF Delegation Receipt — ATORS v1.0</span>
              </div>
              <div style={{ lineHeight: 2 }}>
                {RECEIPT_FIELDS.slice(0, visibleFields).map(f => (
                  <div key={f.key} style={{ display: 'flex', gap: 12 }}>
                    <span style={{ color: DIMMED, minWidth: 160 }}>{f.key}:</span>
                    <span style={{ color: f.color }}>{f.value}</span>
                  </div>
                ))}
                {visibleFields < RECEIPT_FIELDS.length && (
                  <span style={{ color: GOLD, opacity: 0.6 }}>▋</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── DIFFERENTIATORS ──────────────────────────────────────────────────── */}
      <section style={{ padding: '80px 2rem' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 56 }}>
            <div style={{ fontSize: 11, color: GOLD, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 10, fontWeight: 600 }}>
              Technical Differentiation
            </div>
            <h2 style={{ fontSize: 32, fontWeight: 800 }}>
              What no RegTech competitor currently provides
            </h2>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 20 }}>
            {DIFFERENTIATORS.map(d => (
              <div key={d.title} style={{
                background: d.dim, border: `1px solid ${d.border}`,
                borderRadius: 10, padding: '24px 24px',
              }}>
                <div style={{
                  width: 40, height: 40, borderRadius: 8,
                  background: `${d.dim}`, border: `1px solid ${d.border}`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: d.color, marginBottom: 14,
                }}>
                  {d.icon}
                </div>
                <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 4, color: TEXT }}>{d.title}</div>
                <div style={{ fontSize: 11, color: d.color, marginBottom: 12, fontFamily: 'monospace', letterSpacing: '0.04em' }}>{d.subtitle}</div>
                <p style={{ color: MUTED, fontSize: 13.5, lineHeight: 1.65 }}>{d.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── LEGAL POSITIONING BANNER ─────────────────────────────────────────── */}
      <section style={{ padding: '0 2rem 60px' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <div style={{
            background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.22)',
            borderRadius: 10, padding: '20px 28px',
            display: 'flex', alignItems: 'flex-start', gap: 14,
          }}>
            <AlertTriangle size={20} color="#ef4444" style={{ flexShrink: 0, marginTop: 2 }} />
            <div>
              <div style={{ fontWeight: 700, fontSize: 13, color: '#ef4444', marginBottom: 6 }}>
                REGULATORY POSITIONING — IMPORTANT
              </div>
              <p style={{ color: MUTED, fontSize: 13, lineHeight: 1.6, margin: 0 }}>
                OMNIX Governance API is <strong style={{ color: TEXT }}>decision governance infrastructure software (RegTech SaaS)</strong>.
                OMNIX does not provide financial advice, investment recommendations, trading signals, asset management,
                or any regulated financial service. OMNIX provides cryptographic proof that a governance process was
                followed. Clients remain solely responsible for their decisions and their regulatory compliance.
                Verify applicability to your regulatory jurisdiction with qualified legal counsel.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── PRICING ──────────────────────────────────────────────────────────── */}
      <section style={{ padding: '80px 2rem', background: NAVY2 }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 56 }}>
            <div style={{ fontSize: 11, color: GOLD, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 10, fontWeight: 600 }}>
              Pricing
            </div>
            <h2 style={{ fontSize: 32, fontWeight: 800 }}>
              From open verification to institutional deployment
            </h2>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 16 }}>
            {PRICING.map(p => (
              <div key={p.tier} style={{
                background: p.dim, border: `1px solid ${p.border}`,
                borderRadius: 12, padding: '28px 24px',
                display: 'flex', flexDirection: 'column', gap: 0,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                  <span style={{
                    fontSize: 11, fontWeight: 700, letterSpacing: '0.08em',
                    color: p.color, textTransform: 'uppercase',
                  }}>{p.tier}</span>
                  <span style={{
                    fontSize: 10, background: `${p.dim}`, border: `1px solid ${p.border}`,
                    color: p.color, padding: '3px 8px', borderRadius: 10, fontWeight: 600,
                  }}>{p.badge}</span>
                </div>

                <div style={{ marginBottom: 4 }}>
                  <span style={{ fontSize: 32, fontWeight: 800, color: TEXT }}>{p.price}</span>
                  <span style={{ fontSize: 13, color: MUTED, marginLeft: 4 }}>{p.period}</span>
                </div>
                <div style={{ fontSize: 12, color: DIMMED, marginBottom: 24 }}>{p.target}</div>

                <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 28px 0', display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {p.features.map(f => (
                    <li key={f} style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                      <CheckCircle size={13} color={p.color} style={{ flexShrink: 0, marginTop: 2 }} />
                      <span style={{ fontSize: 12.5, color: MUTED, lineHeight: 1.5 }}>{f}</span>
                    </li>
                  ))}
                </ul>

                <Link to={p.ctaLink} style={{
                  display: 'block', textAlign: 'center', padding: '10px 0',
                  borderRadius: 7, textDecoration: 'none', fontWeight: 700, fontSize: 13,
                  marginTop: 'auto',
                  ...(p.ctaStyle === 'gold'
                    ? { background: GOLD, color: NAVY }
                    : p.ctaStyle === 'primary'
                    ? { background: BLUE, color: '#fff' }
                    : p.ctaStyle === 'purple'
                    ? { background: PURPLE, color: '#fff' }
                    : { background: 'transparent', border: `1px solid rgba(100,116,139,0.4)`, color: MUTED }),
                }}>
                  {p.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── API REFERENCE ────────────────────────────────────────────────────── */}
      <section style={{ padding: '80px 2rem' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 60, alignItems: 'start' }}>
            <div>
              <div style={{ fontSize: 11, color: GOLD, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 12, fontWeight: 600 }}>
                API Reference
              </div>
              <h2 style={{ fontSize: 28, fontWeight: 800, marginBottom: 16 }}>
                REST API. SDKs for Python and Node.js.
              </h2>
              <p style={{ color: MUTED, lineHeight: 1.7, marginBottom: 24 }}>
                Authenticate with an API key. Issue receipts. Verify them offline.
                Export forensic packages for regulators. The standalone verifier
                requires no network access and no OMNIX runtime.
              </p>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <Link to="/getting-started" style={{
                  background: GOLD_DIM, border: `1px solid ${GOLD_BORDER}`,
                  color: GOLD, padding: '9px 18px', borderRadius: 7,
                  textDecoration: 'none', fontSize: 13, fontWeight: 600,
                  display: 'flex', alignItems: 'center', gap: 6,
                }}>
                  Integration Guide <ArrowRight size={13} />
                </Link>
                <Link to="/atf-standard" style={{
                  color: MUTED, padding: '9px 18px', borderRadius: 7,
                  textDecoration: 'none', fontSize: 13,
                  border: '1px solid rgba(226,232,240,0.12)',
                  display: 'flex', alignItems: 'center', gap: 6,
                }}>
                  ATF Standard <ExternalLink size={13} />
                </Link>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {ENDPOINTS.map(e => (
                <div key={e.path} style={{
                  background: NAVY3, border: `1px solid rgba(226,232,240,0.07)`,
                  borderRadius: 8, padding: '12px 16px',
                  display: 'flex', gap: 14, alignItems: 'flex-start',
                }}>
                  <span style={{
                    fontFamily: 'monospace', fontSize: 10, fontWeight: 700,
                    padding: '3px 7px', borderRadius: 4, flexShrink: 0,
                    ...(e.method === 'POST'
                      ? { background: BLUE_DIM, color: BLUE, border: `1px solid ${BLUE_BORDER}` }
                      : { background: GREEN_DIM, color: GREEN, border: `1px solid ${GREEN_BORDER}` }),
                  }}>{e.method}</span>
                  <div>
                    <div style={{ fontFamily: 'monospace', fontSize: 12, color: TEXT, marginBottom: 3 }}>{e.path}</div>
                    <div style={{ fontSize: 12, color: DIMMED }}>{e.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── VERIFIER BLOCK ───────────────────────────────────────────────────── */}
      <section style={{ padding: '0 2rem 80px' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <div style={{
            background: '#040c1a', border: `1px solid ${GREEN_BORDER}`,
            borderRadius: 12, padding: '28px 32px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
              <Terminal size={16} color={GREEN} />
              <span style={{ color: GREEN, fontSize: 12, fontWeight: 600 }}>Standalone Offline Verifier — sdk/python/omnix_atf_verify.py</span>
            </div>
            <pre style={{ fontFamily: 'monospace', fontSize: 12.5, color: TEXT, margin: 0, lineHeight: 1.8, overflow: 'auto' }}>
{`$ python omnix_atf_verify.py receipt.json --pubkey platform_pubkey.pem

OMNIX ATF Standalone Verifier v1.2.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Receipt:     ATFDR-8F2A1C4E9B7D3F6A
Type:        DR (Delegation Receipt)
ATORS:       v1.0.0

L1 Structural check    ✓  All required fields present
L2 Hash verification   ✓  SHA-256 canonical match
L3 Invariant check     ✓  ATF-INV-001–006 all pass
L4 PQC signature       ✓  ML-DSA-65 valid (FIPS 204)

VERIFICATION: FULL  ✓  No OMNIX runtime required.`}
            </pre>
          </div>
        </div>
      </section>

      {/* ── FAQ ──────────────────────────────────────────────────────────────── */}
      <section style={{ padding: '80px 2rem', background: NAVY2 }}>
        <div style={{ maxWidth: 760, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 48 }}>
            <h2 style={{ fontSize: 28, fontWeight: 800 }}>Frequently asked questions</h2>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {FAQ.map((f, i) => (
              <div key={i} style={{
                background: openFaq === i ? NAVY3 : 'transparent',
                border: `1px solid ${openFaq === i ? GOLD_BORDER : 'rgba(226,232,240,0.08)'}`,
                borderRadius: 8, overflow: 'hidden',
              }}>
                <button
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  style={{
                    width: '100%', background: 'none', border: 'none', cursor: 'pointer',
                    padding: '18px 20px', display: 'flex', justifyContent: 'space-between',
                    alignItems: 'center', gap: 16, textAlign: 'left',
                  }}
                >
                  <span style={{ color: TEXT, fontWeight: 600, fontSize: 14 }}>{f.q}</span>
                  {openFaq === i
                    ? <ChevronUp size={16} color={GOLD} />
                    : <ChevronDown size={16} color={DIMMED} />}
                </button>
                {openFaq === i && (
                  <div style={{ padding: '0 20px 18px', color: MUTED, fontSize: 13.5, lineHeight: 1.7 }}>
                    {f.a}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────────────────────────── */}
      <section style={{ padding: '100px 2rem' }}>
        <div style={{ maxWidth: 700, margin: '0 auto', textAlign: 'center' }}>
          <div style={{
            width: 60, height: 60, borderRadius: 14, background: GOLD_DIM,
            border: `1px solid ${GOLD_BORDER}`, display: 'flex', alignItems: 'center',
            justifyContent: 'center', margin: '0 auto 28px',
          }}>
            <Shield size={26} color={GOLD} />
          </div>
          <h2 style={{ fontSize: 36, fontWeight: 800, marginBottom: 16 }}>
            Your decisions deserve a governance receipt.
          </h2>
          <p style={{ color: MUTED, fontSize: 16, lineHeight: 1.7, marginBottom: 40 }}>
            Start with the free verifier. When you're ready to issue, the API is there.
            OMNIX handles the governance infrastructure so you can focus on the decisions.
          </p>
          <div style={{ display: 'flex', gap: 14, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link to="/institutional" style={{
              background: GOLD, color: NAVY, padding: '14px 32px', borderRadius: 8,
              textDecoration: 'none', fontWeight: 700, fontSize: 15,
              display: 'flex', alignItems: 'center', gap: 8,
            }}>
              Request Access <ArrowRight size={16} />
            </Link>
            <Link to="/atf-verify" style={{
              background: 'transparent', color: TEXT,
              border: `1px solid rgba(226,232,240,0.2)`,
              padding: '14px 32px', borderRadius: 8,
              textDecoration: 'none', fontWeight: 600, fontSize: 15,
              display: 'flex', alignItems: 'center', gap: 8,
            }}>
              <Terminal size={16} /> Free Verifier
            </Link>
          </div>
        </div>
      </section>

      {/* ── FOOTER ───────────────────────────────────────────────────────────── */}
      <footer style={{
        borderTop: `1px solid rgba(226,232,240,0.08)`,
        padding: '32px 2rem', background: NAVY,
      }}>
        <div style={{ maxWidth: 1100, margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Shield size={16} color={GOLD} />
            <span style={{ color: MUTED, fontSize: 13 }}>OMNIX QUANTUM LTD · England & Wales · United Kingdom</span>
          </div>
          <div style={{ display: 'flex', gap: 20 }}>
            <Link to="/terms" style={{ color: DIMMED, fontSize: 12, textDecoration: 'none' }}>Terms</Link>
            <Link to="/privacy" style={{ color: DIMMED, fontSize: 12, textDecoration: 'none' }}>Privacy</Link>
            <Link to="/security" style={{ color: DIMMED, fontSize: 12, textDecoration: 'none' }}>Security</Link>
            <Link to="/trust-infrastructure" style={{ color: DIMMED, fontSize: 12, textDecoration: 'none' }}>Architecture</Link>
          </div>
        </div>
      </footer>

    </div>
  )
}
