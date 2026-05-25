import { useNavigate } from 'react-router-dom'

const GOLD = '#C9A227'
const GOLD_DIM = 'rgba(201,162,39,0.15)'
const NAVY = '#060F1E'
const NAVY2 = '#080E1C'
const SURFACE = 'rgba(255,255,255,0.03)'
const BORDER = 'rgba(201,162,39,0.18)'

const timeline = [
  {
    year: 'Nov 2025',
    event: 'Dilithium-3 in production',
    detail: 'First operational deployment of ML-DSA-65 for governance receipts. Not a roadmap item — live production.',
    color: '#C9A227',
  },
  {
    year: 'Feb 2026',
    event: 'First paper published',
    detail: 'Production study published on SSRN: 693,890 cycles, 27,449 signed receipts, verifiable hash chain.',
    color: '#10b981',
  },
  {
    year: 'Mar 2026',
    event: 'Zenodo deposit',
    detail: 'Complete dataset of 82,569 real decisions deposited on Zenodo with permanent DOI.',
    color: '#6366f1',
  },
  {
    year: 'Apr 2026',
    event: 'Technical whitepaper + 171 ADRs',
    detail: 'Full architecture documented: 11-checkpoint pipeline, AVM, LLM isolation, Execution Integrity Layer.',
    color: '#f59e0b',
  },
  {
    year: 'May 2026',
    event: 'Governance baseline',
    detail: 'GOVERNANCE_BASELINE-2026-Q2-001: 47 formal invariants, 171 ADRs, 184+ tests. Architecture freeze.',
    color: '#06b6d4',
  },
  {
    year: 'May 2026',
    event: 'RFC-ATF-3 + GECR formalized',
    detail: 'RFC-ATF-3: 26 invariants across 6 families (GPIL, ELR, EAP, OEP, FEA, FVP) — PQC forensic verification. ADR-157 rev.2 + ADR-170 add 7 further invariants. Cumulative total: 47 invariants across 9 families. Published on Zenodo + Figshare.',
    color: '#a855f7',
  },
]

const principles = [
  {
    title: 'Evidence before assertion',
    body: 'Any system can declare it has governance. OMNIX produces a cryptographically signed record before the action occurs. The difference is not philosophical — it is technical and legally defensible.',
    icon: '◈',
    color: '#C9A227',
  },
  {
    title: 'Fail-closed as default posture',
    body: 'When a system cannot verify that a decision is safe, the correct response is to halt — not to degrade gracefully. OMNIX blocks. Always. No override path.',
    icon: '⬡',
    color: '#ef4444',
  },
  {
    title: 'Verifiable without internal access',
    body: 'An OMNIX receipt contains everything needed to verify its integrity without accessing the system that produced it. Regulators, auditors, and clients can verify independently — no vendor dependency.',
    icon: '◇',
    color: '#10b981',
  },
  {
    title: 'Architecture first, product second',
    body: '171 ADRs document every design decision with context, alternatives, and consequences. No function in OMNIX exists without its architectural justification on record.',
    icon: '△',
    color: '#6366f1',
  },
]

export default function AboutPage() {
  const navigate = useNavigate()

  return (
    <div
      style={{
        minHeight: '100vh',
        background: `linear-gradient(160deg, ${NAVY} 0%, ${NAVY2} 60%, #050A14 100%)`,
        fontFamily: "'Inter', system-ui, sans-serif",
        color: '#fff',
        position: 'relative',
      }}
    >
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 1,
          background: `linear-gradient(90deg, transparent, ${GOLD}, transparent)`,
        }}
      />

      <div style={{ maxWidth: 960, margin: '0 auto', padding: '60px 40px 100px' }}>

        <div style={{ marginBottom: 20 }}>
          <span
            style={{
              fontSize: 10,
              fontWeight: 700,
              letterSpacing: '0.2em',
              color: GOLD,
              background: GOLD_DIM,
              border: `1px solid ${BORDER}`,
              padding: '4px 14px',
              borderRadius: 4,
            }}
          >
            OMNIX QUANTUM · FOUNDATION
          </span>
        </div>

        <h1
          style={{
            fontSize: 44,
            fontWeight: 800,
            lineHeight: 1.15,
            margin: '0 0 24px 0',
            letterSpacing: '-0.02em',
          }}
        >
          Built from first principles
          <br />
          <span style={{ color: GOLD }}>for a problem no one had solved.</span>
        </h1>

        <p
          style={{
            fontSize: 16,
            color: '#94a3b8',
            maxWidth: 640,
            lineHeight: 1.8,
            margin: '0 0 72px 0',
          }}
        >
          Existing governance platforms produce reports. They produce dashboards.
          They produce documentation. None produced cryptographic evidence that a decision
          was made under valid conditions — before the action occurred.
          OMNIX exists to close that gap.
        </p>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 1,
            background: BORDER,
            borderRadius: 20,
            overflow: 'hidden',
            marginBottom: 80,
          }}
        >
          <div
            style={{
              background: NAVY,
              padding: '48px 44px',
            }}
          >
            <div
              style={{
                width: 56,
                height: 56,
                borderRadius: 14,
                background: GOLD_DIM,
                border: `1px solid ${BORDER}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 24,
                marginBottom: 28,
              }}
            >
              ◈
            </div>
            <h2
              style={{
                fontSize: 22,
                fontWeight: 700,
                margin: '0 0 16px 0',
                color: '#fff',
                lineHeight: 1.3,
              }}
            >
              Harold Nunes
            </h2>
            <p
              style={{
                fontSize: 13,
                color: GOLD,
                fontWeight: 600,
                letterSpacing: '0.08em',
                margin: '0 0 20px 0',
              }}
            >
              FOUNDER & CEO · ABU DHABI, UAE
            </p>
            <p
              style={{
                fontSize: 14,
                color: '#94a3b8',
                lineHeight: 1.8,
                margin: '0 0 20px 0',
              }}
            >
              I founded OMNIX from Abu Dhabi after observing a consistent pattern in automated
              decision systems: governance always arrived after the fact — as a retrospective audit,
              as a post-incident report, as an explanation to a regulator.
            </p>
            <p
              style={{
                fontSize: 14,
                color: '#64748b',
                lineHeight: 1.8,
                margin: 0,
              }}
            >
              The question OMNIX answers is different: can you prove that governance
              was active at the exact moment the decision was bound to consequences?
            </p>
          </div>

          <div
            style={{
              background: '#050B18',
              padding: '48px 44px',
            }}
          >
            <div style={{ marginBottom: 32 }}>
              <div
                style={{
                  fontSize: 10,
                  fontWeight: 700,
                  letterSpacing: '0.15em',
                  color: '#475569',
                  marginBottom: 20,
                }}
              >
                ACADEMIC PUBLICATIONS
              </div>
              {[
                {
                  label: 'RFC-ATF-4: Proactive Governance Layer · 19 Z3 Proofs · Dual Z3+TLA+',
                  sub: 'Zenodo: 10.5281/zenodo.20368895 · Figshare: 10.6084/m9.figshare.32394192 · May 2026',
                  link: 'https://doi.org/10.5281/zenodo.20368895',
                },
                {
                  label: 'RFC-ATF-3: Forensic Verification Protocol · 40 Invariants',
                  sub: 'Zenodo: 10.5281/zenodo.20247342 · Figshare: 10.6084/m9.figshare.32308119 · May 2026',
                  link: 'https://doi.org/10.5281/zenodo.20247342',
                },
                {
                  label: 'RFC-ATF-2: Runtime Governance Continuity',
                  sub: 'SSRN 6763978 · Zenodo: 10.5281/zenodo.20241344 · Figshare: 10.6084/m9.figshare.32308095 · May 2026',
                  link: 'https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6763978',
                },
                {
                  label: 'RFC-ATF-1: Agent Trust Fabric Delegation Protocol',
                  sub: 'Zenodo: 10.5281/zenodo.20155016 · SSRN 6757339 · Figshare: 10.6084/m9.figshare.32308077',
                  link: 'https://doi.org/10.5281/zenodo.20155016',
                },
                {
                  label: 'Production Study',
                  sub: 'SSRN 6321298 · Feb 27, 2026',
                  link: 'https://ssrn.com/abstract=6321298',
                },
                {
                  label: 'Technical Whitepaper',
                  sub: 'SSRN 6507559 · Zenodo: 10.5281/zenodo.19375792 · Apr 2026',
                  link: 'https://ssrn.com/abstract=6507559',
                },
                {
                  label: 'Production Dataset (82,569 decisions)',
                  sub: 'Zenodo DOI: 10.5281/zenodo.19056919 · Mar 2026',
                  link: 'https://doi.org/10.5281/zenodo.19056919',
                },
              ].map((p) => (
                <a
                  key={p.label}
                  href={p.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 0',
                    borderBottom: `1px solid rgba(255,255,255,0.04)`,
                    textDecoration: 'none',
                    gap: 12,
                  }}
                >
                  <div>
                    <div style={{ fontSize: 13, color: '#e2e8f0', fontWeight: 500 }}>{p.label}</div>
                    <div style={{ fontSize: 11, color: '#475569', marginTop: 2 }}>{p.sub}</div>
                  </div>
                  <span style={{ color: GOLD, fontSize: 12 }}>↗</span>
                </a>
              ))}
            </div>
          </div>
        </div>

        <div style={{ marginBottom: 80 }}>
          <div
            style={{
              fontSize: 10,
              fontWeight: 700,
              letterSpacing: '0.2em',
              color: '#475569',
              marginBottom: 40,
            }}
          >
            DESIGN PRINCIPLES
          </div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 16,
            }}
          >
            {principles.map((p) => (
              <div
                key={p.title}
                style={{
                  background: SURFACE,
                  border: `1px solid ${BORDER}`,
                  borderRadius: 16,
                  padding: '28px 28px',
                }}
              >
                <div
                  style={{
                    fontSize: 22,
                    color: p.color,
                    marginBottom: 16,
                  }}
                >
                  {p.icon}
                </div>
                <h3
                  style={{
                    fontSize: 15,
                    fontWeight: 700,
                    color: '#fff',
                    margin: '0 0 12px 0',
                    lineHeight: 1.4,
                  }}
                >
                  {p.title}
                </h3>
                <p
                  style={{
                    fontSize: 13,
                    color: '#64748b',
                    margin: 0,
                    lineHeight: 1.75,
                  }}
                >
                  {p.body}
                </p>
              </div>
            ))}
          </div>
        </div>

        <div style={{ marginBottom: 80 }}>
          <div
            style={{
              fontSize: 10,
              fontWeight: 700,
              letterSpacing: '0.2em',
              color: '#475569',
              marginBottom: 40,
            }}
          >
            TIMELINE
          </div>
          <div style={{ position: 'relative', paddingLeft: 32 }}>
            <div
              style={{
                position: 'absolute',
                left: 8,
                top: 8,
                bottom: 8,
                width: 1,
                background: `linear-gradient(to bottom, ${GOLD}60, transparent)`,
              }}
            />
            {timeline.map((t, i) => (
              <div
                key={i}
                style={{
                  position: 'relative',
                  marginBottom: 36,
                  paddingLeft: 24,
                }}
              >
                <div
                  style={{
                    position: 'absolute',
                    left: -28,
                    top: 6,
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    background: t.color,
                    boxShadow: `0 0 8px ${t.color}`,
                  }}
                />
                <div
                  style={{
                    fontSize: 10,
                    fontWeight: 700,
                    letterSpacing: '0.12em',
                    color: t.color,
                    marginBottom: 6,
                  }}
                >
                  {t.year}
                </div>
                <div
                  style={{
                    fontSize: 15,
                    fontWeight: 700,
                    color: '#e2e8f0',
                    marginBottom: 6,
                  }}
                >
                  {t.event}
                </div>
                <div style={{ fontSize: 13, color: '#475569', lineHeight: 1.65 }}>
                  {t.detail}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div
          style={{
            background: `linear-gradient(135deg, rgba(201,162,39,0.08) 0%, rgba(201,162,39,0.03) 100%)`,
            border: `1px solid ${BORDER}`,
            borderRadius: 20,
            padding: '40px 44px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 32,
          }}
        >
          <div>
            <h2 style={{ fontSize: 20, fontWeight: 700, margin: '0 0 10px 0' }}>
              Have a technical question?
            </h2>
            <p style={{ fontSize: 14, color: '#64748b', margin: 0, maxWidth: 440 }}>
              OMNIX is serious infrastructure. Serious questions deserve direct answers.
            </p>
          </div>
          <div style={{ display: 'flex', gap: 12, flexShrink: 0 }}>
            <button
              onClick={() => navigate('/book')}
              style={{
                background: GOLD,
                color: '#000',
                fontWeight: 700,
                fontSize: 13,
                padding: '12px 24px',
                borderRadius: 10,
                border: 'none',
                cursor: 'pointer',
              }}
            >
              Contact →
            </button>
            <button
              onClick={() => navigate('/stack')}
              style={{
                background: 'transparent',
                color: GOLD,
                fontWeight: 600,
                fontSize: 13,
                padding: '12px 24px',
                borderRadius: 10,
                border: `1px solid ${BORDER}`,
                cursor: 'pointer',
              }}
            >
              Technical Stack
            </button>
          </div>
        </div>

        <div
          style={{
            marginTop: 40,
            paddingTop: 32,
            borderTop: `1px solid ${BORDER}`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div style={{ fontSize: 12, color: '#334155' }}>
            OMNIX QUANTUM · United Kingdom · Founded 2025
          </div>
          <div style={{ fontSize: 12, color: '#334155' }}>
            171 ADRs · 184+ tests · GOVERNANCE_BASELINE-2026-Q2-001
          </div>
        </div>
      </div>
    </div>
  )
}
