/**
 * OMNIX Reviewer Start Page — /start
 * ====================================
 * Entry point for external reviewers, technical evaluators, and institutional auditors.
 * Sequential path through the OMNIX ATF ecosystem.
 * Harold Nunes — OMNIX QUANTUM LTD — May 2026
 */

const GOLD   = '#C9A227'
const NAVY   = '#060F1E'
const NAVY2  = '#0A1628'
const NAVY3  = '#0D1F35'
const BORDER = '#1a2d45'
const TEXT   = '#e2e8f0'
const MUTED  = '#94a3b8'
const SLATE  = '#475569'
const CYAN   = '#22d3ee'
const GREEN  = '#22c55e'
const PURPLE = '#a855f7'
const RED    = '#ef4444'

const STEPS = [
  {
    n: '01',
    label: 'Institutional Brief',
    path: '/institutional-brief',
    time: '5 min read',
    color: GOLD,
    tag: 'START HERE',
    tagColor: GOLD,
    desc: 'The full protocol brief. Problem, architecture, RFC stack, conformance baseline, and offline verification. Designed for institutional reviewers.',
    what: ['What OMNIX ATF is', 'The governance lifecycle in full', 'RFC-ATF-1/2/3 with DOIs', '47 invariants · 9 families · 171 ADRs'],
  },
  {
    n: '02',
    label: 'Governance Lifecycle',
    path: '/governance-flow',
    time: '3–5 min',
    color: CYAN,
    tag: 'INTERACTIVE',
    tagColor: CYAN,
    desc: 'Live walkthrough of a real governance event: from human-signed delegation through runtime admissibility to HALT enforcement and COLD archive.',
    what: ['Delegation Receipt: ATFDR-7F3A9B2C1E4D8F6A', 'HALT fired at CES 8.33', 'Block sealed: OMNIX-BLOCK-20260518-000147', 'OEP export: OEP-20260518-A3F8C241'],
  },
  {
    n: '03',
    label: 'Forensic Operations Demo',
    path: '/forensic-operations',
    time: '5–10 min',
    color: PURPLE,
    tag: '5 DEMOS',
    tagColor: PURPLE,
    desc: 'Five protocol simulations: runtime authority degradation, sovereign divergence, archive verification, trust anchoring, and complete governance replay.',
    what: ['Demo-A: CES degradation under stress', 'Demo-B: Cross-runtime policy divergence', 'Demo-C: Archive verification pipeline', 'Demo-E: Full OMNIX-WALK-001 replay'],
  },
  {
    n: '04',
    label: 'ATF Walkthrough Video',
    path: '/video',
    time: '75 seconds',
    color: '#f59e0b',
    tag: 'VISUAL',
    tagColor: '#f59e0b',
    desc: 'Institutional systems walkthrough. Problem statement → Governance flow → CES degradation → HALT enforcement → Evidence lifecycle → Offline verification.',
    what: ['No narration — pure protocol demonstration', 'OMNIX-WALK-001 data throughout', 'Closing: "The protocol decides whether execution is admitted."'],
  },
  {
    n: '05',
    label: 'Protocol Architecture',
    path: '/protocol',
    time: '5 min',
    color: GREEN,
    tag: '5 DIAGRAMS',
    tagColor: GREEN,
    desc: 'Technical architecture. Five diagrams covering the runtime legitimacy stack, execution chain, sovereign divergence, authority degradation, and evidence custody.',
    what: ['171 ADRs · 47 invariants', 'Six-layer governance architecture', 'ML-DSA-65 · FIPS 204 · NIST Level 3', 'ADR-156 through ADR-171'],
  },
  {
    n: '06',
    label: 'RFC Stack',
    path: null,
    time: 'Reference',
    color: RED,
    tag: 'PUBLISHED',
    tagColor: RED,
    desc: 'Four published RFCs with DOI deposits on Zenodo and Figshare. Independent of any OMNIX runtime — verifiable by any party.',
    what: [
      'RFC-ATF-1 · zenodo.20155016 · figshare.32308077',
      'RFC-ATF-2 · zenodo.20241344 · figshare.32308095',
      'RFC-ATF-3 · zenodo.20247342 · figshare.32308119',
      'RFC-ATF-4 · zenodo.20368895 · figshare.32394192',
    ],
    rfcs: [
      { id: 'RFC-ATF-1', title: 'ATF Delegation Protocol', doi: 'https://doi.org/10.5281/zenodo.20155016', sub: 'ATF-INV-001–006 · Identity, delegation, PQC' },
      { id: 'RFC-ATF-2', title: 'Runtime Governance Continuity', doi: 'https://doi.org/10.5281/zenodo.20241344', sub: 'RGC-INV-001–008 · CES, HALT, RCR states' },
      { id: 'RFC-ATF-3', title: 'Forensic Evidence & Interoperability', doi: 'https://doi.org/10.5281/zenodo.20247342', sub: '26 invariants · EAP/OEP/FEA/FVP' },
      { id: 'RFC-ATF-4', title: 'Proactive Governance Layer', doi: 'https://doi.org/10.5281/zenodo.20368895', sub: '19 Z3 proofs · AGVP · SSD · DSPP · dual Z3+TLA+' },
    ],
  },
  {
    n: '07',
    label: 'Forensic Archive Verifier',
    path: '/archive-verify',
    time: 'Verify',
    color: '#3b82f6',
    tag: 'CRYPTOGRAPHIC',
    tagColor: '#3b82f6',
    desc: 'Verify any OMNIX receipt independently. Drop a block file and the platform public key — ML-DSA-65 PQC verification runs in three planes.',
    what: ['Plane 1: Browser · Merkle hash', 'Plane 2: Server · ML-DSA-65 PQC signature', 'Plane 3: Offline OEP · EAP-INV-005'],
  },
]

const FOOTER_LINKS = [
  { label: 'Platform Trust Registry', path: '/trust-infrastructure' },
  { label: 'ATF Standard', path: '/atf-standard' },
  { label: 'ATF Explained', path: '/atf-explained' },
  { label: 'Technical Stack', path: '/technical-stack' },
  { label: 'Security Model', path: '/security' },
  { label: 'About', path: '/about' },
]

export default function ReviewerStartPage() {
  return (
    <div style={{ minHeight: '100vh', background: NAVY, fontFamily: "'Inter', system-ui, sans-serif", color: TEXT }}>

      {/* Top bar */}
      <div style={{
        borderBottom: `1px solid ${BORDER}`,
        padding: '14px 40px', display: 'flex', alignItems: 'center', gap: 16,
        background: NAVY2,
      }}>
        <a href="/" style={{ color: GOLD, fontSize: 11, fontWeight: 700, fontFamily: 'monospace', textDecoration: 'none', letterSpacing: '0.12em' }}>
          OMNIX QUANTUM LTD
        </a>
        <span style={{ color: SLATE }}>|</span>
        <span style={{ color: MUTED, fontSize: 11, fontFamily: 'monospace' }}>REVIEWER PATH</span>
        <div style={{ flex: 1 }} />
        <span style={{ fontSize: 10, color: SLATE, fontFamily: 'monospace' }}>GOVERNANCE_BASELINE-2026-Q2-001</span>
      </div>

      <div style={{ maxWidth: 860, margin: '0 auto', padding: '60px 40px 80px' }}>

        {/* Header */}
        <div style={{ marginBottom: 56, borderBottom: `1px solid ${BORDER}`, paddingBottom: 48 }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: GOLD, letterSpacing: '0.20em', marginBottom: 16, fontFamily: 'monospace' }}>
            START HERE
          </div>
          <h1 style={{ fontSize: 'clamp(26px, 3.5vw, 40px)', fontWeight: 800, lineHeight: 1.2, margin: '0 0 16px', letterSpacing: '-0.02em' }}>
            OMNIX ATF<br />
            <span style={{ color: GOLD }}>Reviewer Path</span>
          </h1>
          <p style={{ fontSize: 14, color: MUTED, margin: '0 0 28px', lineHeight: 1.75, maxWidth: 600 }}>
            Seven sequential stops. Designed for technical reviewers, institutional evaluators, and governance auditors.
            Each stop is independent — but in order, they build a complete picture of the ATF runtime governance infrastructure.
          </p>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            {['~30 min total', '7 stops', 'RFC-ATF-1 · RFC-ATF-2 · RFC-ATF-3', 'No account required'].map(t => (
              <span key={t} style={{
                fontSize: 10, color: MUTED, background: NAVY3, border: `1px solid ${BORDER}`,
                padding: '4px 12px', borderRadius: 4, fontFamily: 'monospace',
              }}>{t}</span>
            ))}
          </div>
        </div>

        {/* Steps */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {STEPS.map((step, i) => (
            <StepCard key={step.n} step={step} isLast={i === STEPS.length - 1} />
          ))}
        </div>

        {/* Verification note */}
        <div style={{
          margin: '56px 0 0', padding: '24px 28px', borderRadius: 10,
          background: `${GREEN}07`, border: `1px solid ${GREEN}18`,
          display: 'flex', gap: 20, alignItems: 'flex-start',
        }}>
          <div style={{ fontSize: 20, flexShrink: 0, paddingTop: 2 }}>⬡</div>
          <div>
            <div style={{ fontSize: 11, fontWeight: 700, color: GREEN, marginBottom: 8, fontFamily: 'monospace' }}>
              INDEPENDENT VERIFICATION
            </div>
            <p style={{ fontSize: 13, color: MUTED, margin: 0, lineHeight: 1.7 }}>
              Every OMNIX governance receipt can be verified independently using only the receipt file and the platform public key.
              No OMNIX account. No platform access. The verifier is open — Step 07 demonstrates this end to end.
              RFC deposits on Zenodo and Figshare (Step 06) are permanent and independent of any OMNIX infrastructure.
            </p>
          </div>
        </div>

        {/* More resources */}
        <div style={{ marginTop: 48 }}>
          <div style={{ fontSize: 9, fontWeight: 700, color: SLATE, letterSpacing: '0.18em', marginBottom: 16, fontFamily: 'monospace' }}>
            MORE RESOURCES
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            {FOOTER_LINKS.map(l => (
              <a key={l.path} href={l.path} style={{
                fontSize: 11, color: MUTED, textDecoration: 'none',
                padding: '6px 14px', borderRadius: 6,
                border: `1px solid ${BORDER}`, background: NAVY2,
                fontFamily: 'monospace',
              }}
                onMouseEnter={e => {
                  (e.target as HTMLElement).style.color = GOLD;
                  (e.target as HTMLElement).style.borderColor = `${GOLD}44`;
                }}
                onMouseLeave={e => {
                  (e.target as HTMLElement).style.color = MUTED;
                  (e.target as HTMLElement).style.borderColor = BORDER;
                }}
              >{l.label} ↗</a>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div style={{
          marginTop: 48, paddingTop: 24, borderTop: `1px solid ${BORDER}`,
          display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8,
          fontSize: 11, color: SLATE, fontFamily: 'monospace',
        }}>
          <span>OMNIX QUANTUM LTD · omnixquantum.com</span>
          <span>169 invariants · 28 families · 199 ADRs · 6 RFCs published</span>
        </div>
      </div>
    </div>
  )
}

function StepCard({ step, isLast }: { step: typeof STEPS[0]; isLast: boolean }) {
  const content = (
    <div style={{
      padding: '24px 28px', borderRadius: 10,
      background: NAVY2, border: `1px solid ${BORDER}`,
      cursor: step.path ? 'pointer' : 'default',
      transition: 'border-color 0.15s, background 0.15s',
    }}
      onMouseEnter={e => {
        if (!step.path) return;
        const el = e.currentTarget as HTMLElement;
        el.style.borderColor = `${step.color}44`;
        el.style.background = `${step.color}06`;
      }}
      onMouseLeave={e => {
        const el = e.currentTarget as HTMLElement;
        el.style.borderColor = BORDER;
        el.style.background = NAVY2;
      }}
    >
      <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>

        {/* Step number + connector */}
        <div style={{ flexShrink: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0 }}>
          <div style={{
            width: 44, height: 44, borderRadius: 8,
            background: `${step.color}14`, border: `1px solid ${step.color}30`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 13, fontWeight: 800, color: step.color, fontFamily: 'monospace',
          }}>{step.n}</div>
          {!isLast && (
            <div style={{ width: 1, height: 20, background: BORDER, margin: '4px 0 -20px' }} />
          )}
        </div>

        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 15, fontWeight: 700, color: TEXT }}>{step.label}</span>
            <span style={{
              fontSize: 9, fontWeight: 700, color: step.tagColor,
              background: `${step.tagColor}15`, border: `1px solid ${step.tagColor}30`,
              padding: '2px 8px', borderRadius: 4, fontFamily: 'monospace',
            }}>{step.tag}</span>
            <span style={{ fontSize: 10, color: SLATE, fontFamily: 'monospace', marginLeft: 'auto' }}>{step.time}</span>
          </div>

          <p style={{ fontSize: 13, color: MUTED, margin: '0 0 14px', lineHeight: 1.65 }}>{step.desc}</p>

          {/* RFC links for step 06 */}
          {step.rfcs ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {step.rfcs.map(r => (
                <a key={r.id} href={r.doi} target="_blank" rel="noopener noreferrer" style={{
                  display: 'flex', alignItems: 'center', gap: 12, textDecoration: 'none',
                  padding: '10px 14px', borderRadius: 6,
                  background: NAVY3, border: `1px solid ${BORDER}`,
                }}>
                  <span style={{
                    fontSize: 10, fontWeight: 700, color: RED, fontFamily: 'monospace',
                    background: `${RED}15`, border: `1px solid ${RED}30`,
                    padding: '2px 8px', borderRadius: 4, flexShrink: 0,
                  }}>{r.id}</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: TEXT, marginBottom: 2 }}>{r.title}</div>
                    <div style={{ fontSize: 10, color: SLATE, fontFamily: 'monospace' }}>{r.sub}</div>
                  </div>
                  <span style={{ fontSize: 10, color: RED, fontFamily: 'monospace' }}>DOI ↗</span>
                </a>
              ))}
            </div>
          ) : (
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {step.what.map(w => (
                <span key={w} style={{
                  fontSize: 10, color: SLATE, fontFamily: 'monospace',
                  background: NAVY3, border: `1px solid ${BORDER}`,
                  padding: '3px 10px', borderRadius: 4,
                }}>{w}</span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )

  if (step.path) {
    return (
      <a href={step.path} style={{ textDecoration: 'none', display: 'block' }}>
        {content}
      </a>
    )
  }
  return content
}
