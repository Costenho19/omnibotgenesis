import { useNavigate } from 'react-router-dom'

const GOLD = '#C9A227'
const GOLD_DIM = 'rgba(201,162,39,0.15)'
const NAVY = '#060F1E'
const NAVY2 = '#080E1C'
const SURFACE = 'rgba(255,255,255,0.03)'
const BORDER = 'rgba(201,162,39,0.18)'

const layers = [
  {
    id: 'L1',
    title: 'Post-Quantum Cryptography',
    subtitle: 'Dilithium-3 (ML-DSA-65) + Kyber-768 (ML-KEM-768)',
    color: '#C9A227',
    detail: [
      'Every governance receipt is signed with Dilithium-3 — the NIST post-quantum standard at security level 3.',
      'The verification public key is embedded in the receipt. No server dependency required to verify.',
      'Kyber-768 for key encapsulation. Attacking the system requires breaking classical AND post-quantum cryptography simultaneously.',
      'Operational in production since November 2025 — not a roadmap item.',
    ],
    spec: 'NIST FIPS 204 (ML-DSA) · NIST FIPS 203 (ML-KEM) · Level 3 (~192-bit classical security equivalent)',
  },
  {
    id: 'L2',
    title: 'Fail-Closed Architecture',
    subtitle: 'ADR-116 · No override path',
    color: '#ef4444',
    detail: [
      'If any gate in the governance pipeline fails, the decision is blocked. No graceful degradation.',
      'No administrative override path exists in production. AVM_AUTO_APPROVE=true is prohibited.',
      'Fail-closed also applies to database failures (AVM_FAIL_CLOSED=true option).',
      'A BLOCKED outcome produces a signed receipt — even rejections are auditable.',
    ],
    spec: 'ADR-116 · 11 checkpoints · BLOCKED receipt with Dilithium-3 signature',
  },
  {
    id: 'L3',
    title: 'Anti-Replay Protection',
    subtitle: 'Redis-backed · Mode: strict',
    color: '#6366f1',
    detail: [
      'Every receipt has a unique ID. Presenting the same receipt twice to the verification API is detected and rejected.',
      'Strict mode: Redis required. Without Redis, the API rejects all requests.',
      'Best-effort mode: graceful fallback — explicitly documented as a security gap (FMR-004).',
      'In production: OMNIX_ANTI_REPLAY_MODE=strict.',
    ],
    spec: 'RFC 3161-style timestamps · Redis anti-replay · Cross-dyno protection',
  },
  {
    id: 'L4',
    title: 'Transparency Chain & WAL',
    subtitle: 'ADR-044 · ISR-013',
    color: '#10b981',
    detail: [
      'Every receipt is linked to the previous one via SHA-256 hash chain — modifying a receipt invalidates the entire subsequent chain.',
      'Write-Ahead Log (WAL) guarantees no receipt is lost in the event of network or database failure.',
      'Chain Completeness Score (CCS) computes in real time how complete the audit trail is: COMPLETE / DEGRADED / PARTIAL / COMPROMISED.',
      'The chain is publicly verifiable without access to the internal database.',
    ],
    spec: 'SHA-256 Merkle chain · WAL persistent · CCS score 0–100',
  },
  {
    id: 'L5',
    title: 'LLM Isolation Boundary',
    subtitle: 'ADR-148 · 22 approved signal keys',
    color: '#f59e0b',
    detail: [
      'AI models may only pass signals through 22 explicitly approved signal keys.',
      'Any attempt to pass data outside the boundary is recorded in the crossing log.',
      'Input sanitizer (ISR-017) prevents prompt injection before it reaches the LLM.',
      'Strict mode available: rejects any unapproved signal rather than silently ignoring it.',
    ],
    spec: 'ADR-148 · 22 approved signal keys · Crossing log · Strict mode',
  },
  {
    id: 'L6',
    title: 'Adaptive Veto Machine',
    subtitle: 'ADR-074 / ADR-120 · Per-vertical baselines',
    color: '#06b6d4',
    detail: [
      'The AVM calibrates baselines per domain (trading, credit, insurance, etc.) independently.',
      'Drift detection: if the operational context changes beyond the configured threshold, formal re-approval is triggered.',
      'Tamper detection: modifying the calibration database is detected on the next cycle.',
      'AVM_MAX_CUMULATIVE_DRIFT_PCT never exceeds 50% in production — treated as a security parameter.',
    ],
    spec: 'ADR-074 · ADR-120 · Per-vertical · 72h calibration cycle · Tamper detection',
  },
]

const verifiableLinks = [
  {
    label: 'Production Study — SSRN',
    sub: '693,890 cycles · 27,449 Dilithium-3 receipts',
    href: 'https://ssrn.com/abstract=6321298',
  },
  {
    label: 'Technical Whitepaper — SSRN',
    sub: 'Full architecture · EU AI Act · NIST AI RMF',
    href: 'https://ssrn.com/abstract=6507559',
  },
  {
    label: 'Production Dataset — Zenodo',
    sub: '82,569 decisions · DOI: 10.5281/zenodo.19056919',
    href: 'https://doi.org/10.5281/zenodo.19056919',
  },
  {
    label: 'Whitepaper — Zenodo',
    sub: 'DOI: 10.5281/zenodo.19375792',
    href: 'https://doi.org/10.5281/zenodo.19375792',
  },
]

export default function SecurityPage() {
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
            OMNIX QUANTUM · SECURITY ARCHITECTURE
          </span>
        </div>

        <h1
          style={{
            fontSize: 44,
            fontWeight: 800,
            lineHeight: 1.15,
            margin: '0 0 20px 0',
            letterSpacing: '-0.02em',
          }}
        >
          Security you can verify
          <br />
          <span style={{ color: GOLD }}>without trusting us.</span>
        </h1>

        <p
          style={{
            fontSize: 16,
            color: '#94a3b8',
            maxWidth: 620,
            lineHeight: 1.8,
            margin: '0 0 16px 0',
          }}
        >
          OMNIX does not ask you to trust its security posture. Every receipt contains
          its own cryptographic proof. Every paper on SSRN and Zenodo carries a verifiable timestamp.
          The architecture is public. The ADRs are public. Verify it yourself.
        </p>

        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 64 }}>
          {[
            { label: 'Dilithium-3 · NIST FIPS 204', color: '#C9A227' },
            { label: 'Fail-closed · Sin override', color: '#ef4444' },
            { label: 'Anti-replay · Mode strict', color: '#6366f1' },
            { label: 'WAL · Zero receipt loss', color: '#10b981' },
            { label: 'LLM Boundary · 22 keys', color: '#f59e0b' },
            { label: 'AVM · Per-vertical', color: '#06b6d4' },
          ].map((b) => (
            <div
              key={b.label}
              style={{
                fontSize: 11,
                fontWeight: 600,
                color: b.color,
                background: `${b.color}12`,
                border: `1px solid ${b.color}30`,
                padding: '5px 12px',
                borderRadius: 6,
                letterSpacing: '0.04em',
              }}
            >
              {b.label}
            </div>
          ))}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 2, marginBottom: 80 }}>
          {layers.map((l, i) => (
            <div
              key={l.id}
              style={{
                background: SURFACE,
                border: `1px solid ${BORDER}`,
                borderRadius: i === 0 ? '16px 16px 4px 4px' : i === layers.length - 1 ? '4px 4px 16px 16px' : 4,
                padding: '28px 32px',
              }}
            >
              <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start' }}>
                <div
                  style={{
                    fontSize: 10,
                    fontWeight: 800,
                    color: l.color,
                    background: `${l.color}15`,
                    border: `1px solid ${l.color}35`,
                    padding: '6px 10px',
                    borderRadius: 6,
                    letterSpacing: '0.08em',
                    flexShrink: 0,
                    marginTop: 2,
                  }}
                >
                  {l.id}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 6 }}>
                    <h3 style={{ fontSize: 16, fontWeight: 700, color: '#fff', margin: 0 }}>
                      {l.title}
                    </h3>
                    <span style={{ fontSize: 11, color: '#475569' }}>{l.subtitle}</span>
                  </div>
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: '1fr 1fr',
                      gap: '6px 32px',
                      marginBottom: 16,
                    }}
                  >
                    {l.detail.map((d, j) => (
                      <div
                        key={j}
                        style={{
                          fontSize: 13,
                          color: '#64748b',
                          lineHeight: 1.6,
                          display: 'flex',
                          gap: 8,
                          alignItems: 'flex-start',
                        }}
                      >
                        <span style={{ color: l.color, marginTop: 2, flexShrink: 0 }}>·</span>
                        {d}
                      </div>
                    ))}
                  </div>
                  <div
                    style={{
                      fontSize: 11,
                      color: '#334155',
                      fontFamily: 'monospace',
                      background: 'rgba(0,0,0,0.3)',
                      padding: '6px 12px',
                      borderRadius: 6,
                      border: '1px solid rgba(255,255,255,0.05)',
                    }}
                  >
                    {l.spec}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div style={{ marginBottom: 80 }}>
          <div
            style={{
              fontSize: 10,
              fontWeight: 700,
              letterSpacing: '0.2em',
              color: '#475569',
              marginBottom: 24,
            }}
          >
            VERIFIABLE PUBLIC EVIDENCE
          </div>
          <div
            style={{
              background: 'rgba(0,0,0,0.3)',
              border: `1px solid ${BORDER}`,
              borderRadius: 16,
              overflow: 'hidden',
            }}
          >
            {verifiableLinks.map((v, i) => (
              <a
                key={v.label}
                href={v.href}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '20px 28px',
                  borderBottom: i < verifiableLinks.length - 1 ? `1px solid rgba(255,255,255,0.04)` : 'none',
                  textDecoration: 'none',
                  transition: 'background 0.15s',
                  gap: 16,
                }}
                onMouseEnter={e => (e.currentTarget.style.background = 'rgba(201,162,39,0.04)')}
                onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
              >
                <div>
                  <div style={{ fontSize: 14, color: '#e2e8f0', fontWeight: 600 }}>{v.label}</div>
                  <div style={{ fontSize: 12, color: '#475569', marginTop: 3 }}>{v.sub}</div>
                </div>
                <span style={{ color: GOLD, fontSize: 16, flexShrink: 0 }}>↗</span>
              </a>
            ))}
          </div>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 16,
            marginBottom: 80,
          }}
        >
          <div
            style={{
              background: SURFACE,
              border: `1px solid ${BORDER}`,
              borderRadius: 16,
              padding: '28px 28px',
            }}
          >
            <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.15em', color: '#475569', marginBottom: 16 }}>
              INDEPENDENT VERIFICATION
            </div>
            <p style={{ fontSize: 13, color: '#64748b', lineHeight: 1.75, margin: '0 0 20px 0' }}>
              Any OMNIX receipt can be verified without accessing any internal system.
              The receipt contains the signature, payload, and public key — everything required.
            </p>
            <button
              onClick={() => navigate('/verify-independently')}
              style={{
                background: 'transparent',
                color: GOLD,
                border: `1px solid ${BORDER}`,
                padding: '9px 18px',
                borderRadius: 8,
                fontSize: 12,
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Verify a receipt →
            </button>
          </div>
          <div
            style={{
              background: SURFACE,
              border: `1px solid ${BORDER}`,
              borderRadius: 16,
              padding: '28px 28px',
            }}
          >
            <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.15em', color: '#475569', marginBottom: 16 }}>
              SECURITY ARCHITECTURE DECISIONS
            </div>
            <p style={{ fontSize: 13, color: '#64748b', lineHeight: 1.75, margin: '0 0 20px 0' }}>
              ADR-022 (PQC), ADR-042 (Hybrid KEM), ADR-044 (Transparency Chain), ADR-116 (Fail-Closed),
              ADR-148 (LLM Boundary) — available in Zenodo deposits.
            </p>
            <a
              href="https://doi.org/10.5281/zenodo.19056919"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'inline-block',
                background: 'transparent',
                color: GOLD,
                border: `1px solid ${BORDER}`,
                padding: '9px 18px',
                borderRadius: 8,
                fontSize: 12,
                fontWeight: 600,
                cursor: 'pointer',
                textDecoration: 'none',
              }}
            >
              View ADRs on Zenodo →
            </a>
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
              Have a specific security question?
            </h2>
            <p style={{ fontSize: 14, color: '#64748b', margin: 0, maxWidth: 440 }}>
              CISOs, auditors, and regulators — technical questions have direct, documented answers.
            </p>
          </div>
          <button
            onClick={() => navigate('/book')}
            style={{
              background: GOLD,
              color: '#000',
              fontWeight: 700,
              fontSize: 13,
              padding: '12px 28px',
              borderRadius: 10,
              border: 'none',
              cursor: 'pointer',
              flexShrink: 0,
            }}
          >
            Contact →
          </button>
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
            OMNIX QUANTUM · Dilithium-3 (ML-DSA-65) · NIST FIPS 204
          </div>
          <div style={{ fontSize: 12, color: '#334155' }}>
            6 security layers · 202 ADRs · In production since Nov 2025
          </div>
        </div>
      </div>
    </div>
  )
}
