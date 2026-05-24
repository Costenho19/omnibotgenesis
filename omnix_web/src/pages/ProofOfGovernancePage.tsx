import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

// ── Design system ─────────────────────────────────────────────────────────────
const GOLD         = '#C9A227'
const GOLD_DIM     = 'rgba(201,162,39,0.10)'
const GOLD_BORDER  = 'rgba(201,162,39,0.22)'
const NAVY         = '#060F1E'
const NAVY2        = '#0A1628'
const NAVY3        = '#0D1E38'
const GREEN        = '#22c55e'
const GREEN_DIM    = 'rgba(34,197,94,0.08)'
const GREEN_BORDER = 'rgba(34,197,94,0.22)'
const RED          = '#ef4444'
const RED_DIM      = 'rgba(239,68,68,0.08)'
const RED_BORDER   = 'rgba(239,68,68,0.22)'
const AMBER        = '#f59e0b'
const AMBER_DIM    = 'rgba(245,158,11,0.08)'
const SLATE        = '#64748b'
const TEXT         = '#e2e8f0'
const MUTED        = '#94a3b8'
const BLUE         = '#3b82f6'
const BLUE_DIM     = 'rgba(59,130,246,0.08)'

// ── API ───────────────────────────────────────────────────────────────────────
const API = (import.meta.env.VITE_RAILWAY_API_URL || '').replace(/\/$/, '')

interface PoGCertificate {
  pogc_id: string
  session_id: string
  ctchc_seal_hash: string
  issuer: string
  subject_org: string
  compliance_tier: string
  turn_count: number
  avg_conformance: number
  issued_at: string
  expires_at: string
  regulatory_tags: string[]
  content_hash: string
  pqc_algorithm: string
  status: string
}

interface VerifyResult {
  valid: boolean
  pogc_id: string
  verification_notes: string[]
  certificate: PoGCertificate
  verified_at: string
}

interface RegistryEntry {
  pogc_id: string
  subject_org: string
  compliance_tier: string
  status: string
  issued_at: string
  expires_at: string
  avg_conformance: number
  turn_count: number
  regulatory_tags: string[]
}

interface ManifestData {
  registry: string
  product_id: string
  issuer: string
  invariants: string[]
  regulatory_tags: string[]
  platform_key: {
    configured: boolean
    fingerprint: string | null
    fingerprint_short: string | null
    algorithm: string
  }
  registry_stats: { total: number; active: number }
  days_until_enforcement: number
}

// ── Hex icon ──────────────────────────────────────────────────────────────────
function HexIcon({ size = 32, color = GOLD }: { size?: number; color?: string }) {
  const cx = size / 2, cy = size / 2, r = size * 0.42
  const pts = Array.from({ length: 6 }, (_, i) => {
    const a = (Math.PI / 3) * i - Math.PI / 6
    return `${cx + r * Math.cos(a)},${cy + r * Math.sin(a)}`
  }).join(' ')
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <polygon points={pts} fill={`${color}18`} stroke={color} strokeWidth="1.5" />
      <text x={cx} y={cy + 4} textAnchor="middle" fontSize={size * 0.28}
        fontFamily="monospace" fill={color} fontWeight="700">PoG</text>
    </svg>
  )
}

// ── Status badge ──────────────────────────────────────────────────────────────
function StatusPill({ status }: { status: string }) {
  const map: Record<string, [string, string, string]> = {
    ACTIVE:  [GREEN,  GREEN_DIM,  GREEN_BORDER],
    EXPIRED: [AMBER,  AMBER_DIM,  'rgba(245,158,11,0.22)'],
    REVOKED: [RED,    RED_DIM,    RED_BORDER],
    UNKNOWN: [SLATE,  'rgba(100,116,139,0.1)', 'rgba(100,116,139,0.3)'],
  }
  const [color, bg, border] = map[status] ?? map.UNKNOWN
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      padding: '3px 10px', borderRadius: 20,
      background: bg, border: `1px solid ${border}`,
      fontSize: 11, fontFamily: 'monospace', color, fontWeight: 700,
      letterSpacing: '0.06em',
    }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: color }} />
      {status}
    </span>
  )
}

// ── Invariant chip ────────────────────────────────────────────────────────────
function InvariantChip({ id, desc }: { id: string; desc: string }) {
  return (
    <div style={{
      background: GOLD_DIM, border: `1px solid ${GOLD_BORDER}`,
      borderRadius: 8, padding: '10px 14px', display: 'flex', flexDirection: 'column', gap: 3,
    }}>
      <span style={{ fontFamily: 'monospace', fontSize: 10, color: GOLD, fontWeight: 700 }}>{id}</span>
      <span style={{ fontSize: 11, color: MUTED }}>{desc}</span>
    </div>
  )
}

// ── Diff metric block ─────────────────────────────────────────────────────────
function DiffBlock({ icon, label, value, sub }: { icon: string; label: string; value: string; sub?: string }) {
  return (
    <div style={{
      background: NAVY2, border: `1px solid rgba(201,162,39,0.14)`,
      borderRadius: 10, padding: '16px 18px', flex: 1, minWidth: 140,
    }}>
      <div style={{ fontSize: 20, marginBottom: 6 }}>{icon}</div>
      <div style={{ fontSize: 22, fontWeight: 700, color: GOLD, fontFamily: 'monospace' }}>{value}</div>
      <div style={{ fontSize: 11, color: TEXT, marginTop: 2 }}>{label}</div>
      {sub && <div style={{ fontSize: 10, color: SLATE, marginTop: 4 }}>{sub}</div>}
    </div>
  )
}

// ── Certificate card ──────────────────────────────────────────────────────────
function CertCard({ cert, onSelect }: { cert: RegistryEntry; onSelect: (id: string) => void }) {
  const conformancePct = Math.round(cert.avg_conformance * 100)
  return (
    <div
      onClick={() => onSelect(cert.pogc_id)}
      style={{
        background: NAVY2, border: `1px solid ${GOLD_BORDER}`,
        borderRadius: 10, padding: '16px 18px', cursor: 'pointer',
        transition: 'border-color 0.15s, transform 0.1s',
        display: 'flex', flexDirection: 'column', gap: 10,
      }}
      onMouseEnter={e => {
        (e.currentTarget as HTMLElement).style.borderColor = GOLD
        ;(e.currentTarget as HTMLElement).style.transform = 'translateY(-1px)'
      }}
      onMouseLeave={e => {
        (e.currentTarget as HTMLElement).style.borderColor = GOLD_BORDER
        ;(e.currentTarget as HTMLElement).style.transform = 'translateY(0)'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 600, color: TEXT }}>{cert.subject_org}</div>
          <div style={{ fontFamily: 'monospace', fontSize: 10, color: SLATE, marginTop: 2 }}>{cert.pogc_id}</div>
        </div>
        <StatusPill status={cert.status} />
      </div>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <span style={{ fontSize: 10, color: MUTED, fontFamily: 'monospace' }}>
          Conformance: <span style={{ color: conformancePct >= 90 ? GREEN : conformancePct >= 70 ? AMBER : RED }}>{conformancePct}%</span>
        </span>
        <span style={{ fontSize: 10, color: MUTED, fontFamily: 'monospace' }}>
          Turns: {cert.turn_count}
        </span>
        <span style={{ fontSize: 10, color: MUTED }}>
          Issued: {new Date(cert.issued_at).toLocaleDateString()}
        </span>
      </div>
      {cert.regulatory_tags?.length > 0 && (
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {cert.regulatory_tags.slice(0, 4).map(tag => (
            <span key={tag} style={{
              fontSize: 9, fontFamily: 'monospace', color: BLUE,
              background: BLUE_DIM, border: `1px solid rgba(59,130,246,0.2)`,
              borderRadius: 4, padding: '2px 7px',
            }}>{tag}</span>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Verify panel ──────────────────────────────────────────────────────────────
function VerifyPanel({ result }: { result: VerifyResult }) {
  const cert = result.certificate
  const conformancePct = Math.round((cert?.avg_conformance ?? 0) * 100)
  return (
    <div style={{
      background: result.valid ? GREEN_DIM : RED_DIM,
      border: `1.5px solid ${result.valid ? GREEN_BORDER : RED_BORDER}`,
      borderRadius: 12, padding: 24,
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 20 }}>
        <div style={{ fontSize: 32 }}>{result.valid ? '✅' : '❌'}</div>
        <div>
          <div style={{ fontSize: 18, fontWeight: 700, color: result.valid ? GREEN : RED }}>
            {result.valid ? 'Certificate Valid' : 'Verification Failed'}
          </div>
          <div style={{ fontFamily: 'monospace', fontSize: 11, color: SLATE, marginTop: 2 }}>
            {result.pogc_id}
          </div>
        </div>
        {cert && <StatusPill status={cert.status} />}
      </div>

      {/* Verification notes */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 20 }}>
        {result.verification_notes.map((n, i) => (
          <div key={i} style={{
            fontFamily: 'monospace', fontSize: 12, color: TEXT,
            background: 'rgba(0,0,0,0.2)', borderRadius: 6,
            padding: '6px 12px',
          }}>{n}</div>
        ))}
      </div>

      {cert && (
        <>
          {/* Certificate fields */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12, marginBottom: 18 }}>
            {[
              ['Issuer',      cert.issuer],
              ['Organization', cert.subject_org],
              ['Tier',         cert.compliance_tier],
              ['Conformance',  `${conformancePct}%`],
              ['Turns',        String(cert.turn_count)],
              ['Algorithm',    cert.pqc_algorithm],
              ['Issued',       new Date(cert.issued_at).toLocaleDateString()],
              ['Expires',      new Date(cert.expires_at).toLocaleDateString()],
            ].map(([k, v]) => (
              <div key={k} style={{ background: 'rgba(0,0,0,0.15)', borderRadius: 8, padding: '10px 12px' }}>
                <div style={{ fontSize: 10, color: SLATE, marginBottom: 2 }}>{k}</div>
                <div style={{ fontSize: 12, color: TEXT, fontFamily: 'monospace' }}>{v}</div>
              </div>
            ))}
          </div>

          {/* Hashes */}
          <div style={{ background: 'rgba(0,0,0,0.25)', borderRadius: 8, padding: '12px 16px', marginBottom: 14 }}>
            <div style={{ fontSize: 10, color: SLATE, marginBottom: 6 }}>CTCHC Seal Hash</div>
            <div style={{ fontFamily: 'monospace', fontSize: 10, color: MUTED, wordBreak: 'break-all' }}>
              {cert.ctchc_seal_hash}
            </div>
          </div>
          <div style={{ background: 'rgba(0,0,0,0.25)', borderRadius: 8, padding: '12px 16px' }}>
            <div style={{ fontSize: 10, color: SLATE, marginBottom: 6 }}>Content Hash (SHA3-256)</div>
            <div style={{ fontFamily: 'monospace', fontSize: 10, color: MUTED, wordBreak: 'break-all' }}>
              {cert.content_hash}
            </div>
          </div>

          {/* Regulatory tags */}
          {cert.regulatory_tags?.length > 0 && (
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 14 }}>
              {cert.regulatory_tags.map(tag => (
                <span key={tag} style={{
                  fontSize: 10, fontFamily: 'monospace', color: BLUE,
                  background: BLUE_DIM, border: `1px solid rgba(59,130,246,0.25)`,
                  borderRadius: 5, padding: '3px 9px',
                }}>{tag}</span>
              ))}
            </div>
          )}
        </>
      )}

      <div style={{ fontSize: 10, color: SLATE, marginTop: 16, textAlign: 'right' }}>
        Verified at {result.verified_at ? new Date(result.verified_at).toLocaleString() : '—'} · PoGR-INV-003
      </div>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function ProofOfGovernancePage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const [tab, setTab]                   = useState<'registry'|'verify'|'about'>('registry')
  const [verifyInput, setVerifyInput]   = useState(searchParams.get('id') || '')
  const [verifyResult, setVerifyResult] = useState<VerifyResult | null>(null)
  const [verifying, setVerifying]       = useState(false)
  const [verifyError, setVerifyError]   = useState('')

  const [entries, setEntries]           = useState<RegistryEntry[]>([])
  const [registryTotal, setRegistryTotal] = useState(0)
  const [loadingRegistry, setLoadingRegistry] = useState(false)
  const [searchQ, setSearchQ]           = useState('')
  const [manifest, setManifest]         = useState<ManifestData | null>(null)

  // Auto-verify if ?id= param present
  useEffect(() => {
    const id = searchParams.get('id')
    if (id) {
      setTab('verify')
      setVerifyInput(id)
      handleVerify(id)
    }
  }, [])

  // Load manifest
  useEffect(() => {
    fetch(`${API}/v1/pogr/manifest`)
      .then(r => r.json())
      .then(setManifest)
      .catch(() => {})
  }, [])

  // Load registry
  useEffect(() => {
    if (tab !== 'registry') return
    setLoadingRegistry(true)
    const qs = searchQ ? `&q=${encodeURIComponent(searchQ)}` : ''
    fetch(`${API}/v1/pogr/registry?limit=20${qs}`)
      .then(r => r.json())
      .then(d => {
        setEntries(d.certificates || [])
        setRegistryTotal(d.total || 0)
      })
      .catch(() => {})
      .finally(() => setLoadingRegistry(false))
  }, [tab, searchQ])

  async function handleVerify(id?: string) {
    const target = (id || verifyInput).trim()
    if (!target) return
    setVerifying(true)
    setVerifyError('')
    setVerifyResult(null)
    try {
      const r = await fetch(`${API}/v1/pogr/verify/${encodeURIComponent(target)}`)
      const data = await r.json()
      if (r.status === 404) {
        setVerifyError('Certificate not found in registry.')
      } else {
        setVerifyResult(data)
      }
    } catch {
      setVerifyError('Registry unavailable — please try again.')
    } finally {
      setVerifying(false)
    }
  }

  const tabStyle = (active: boolean) => ({
    padding: '8px 20px',
    borderRadius: 8,
    background: active ? GOLD_DIM : 'transparent',
    border: `1px solid ${active ? GOLD_BORDER : 'transparent'}`,
    color: active ? GOLD : SLATE,
    fontSize: 13,
    fontWeight: active ? 600 : 400,
    cursor: 'pointer',
    transition: 'all 0.15s',
  })

  return (
    <div style={{ minHeight: '100vh', background: NAVY, color: TEXT, fontFamily: 'system-ui, sans-serif' }}>
      {/* Nav */}
      <div style={{
        borderBottom: `1px solid ${GOLD_BORDER}`, background: `${NAVY}ee`,
        position: 'sticky', top: 0, zIndex: 100, backdropFilter: 'blur(12px)',
      }}>
        <div style={{ maxWidth: 1100, margin: '0 auto', padding: '0 24px', display: 'flex', alignItems: 'center', height: 60, gap: 16 }}>
          <button onClick={() => navigate('/')} style={{
            background: 'none', border: 'none', cursor: 'pointer',
            display: 'flex', alignItems: 'center', gap: 10,
          }}>
            <HexIcon size={28} />
            <span style={{ fontFamily: 'monospace', fontSize: 13, color: GOLD, fontWeight: 700, letterSpacing: '0.05em' }}>
              OMNIX QUANTUM
            </span>
          </button>
          <span style={{ color: GOLD_BORDER, fontSize: 18 }}>›</span>
          <span style={{ fontSize: 13, color: MUTED }}>Proof of Governance Registry</span>
          <div style={{ flex: 1 }} />
          {manifest?.registry_stats && (
            <div style={{ display: 'flex', gap: 20, fontSize: 11, fontFamily: 'monospace', color: SLATE }}>
              <span>{manifest.registry_stats.total} total</span>
              <span style={{ color: GREEN }}>{manifest.registry_stats.active} active</span>
            </div>
          )}
        </div>
      </div>

      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '40px 24px' }}>

        {/* Hero */}
        <div style={{ textAlign: 'center', marginBottom: 48 }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 18 }}>
            <HexIcon size={56} />
          </div>
          <h1 style={{
            fontSize: 'clamp(28px, 5vw, 44px)', fontWeight: 800,
            color: TEXT, margin: 0, lineHeight: 1.15,
            letterSpacing: '-0.02em',
          }}>
            Proof of Governance Registry
          </h1>
          <p style={{ fontSize: 16, color: MUTED, marginTop: 14, maxWidth: 580, margin: '14px auto 0' }}>
            The world's first publicly verifiable, post-quantum-anchored registry of AI governance certificates.
            Verify any certificate — no account, no API key.
          </p>

          {/* Differentiators */}
          <div style={{
            display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap',
            marginTop: 24,
          }}>
            {[
              ['⬡', 'ML-DSA-65 / FIPS 204'],
              ['🔓', 'Zero-Trust Verification'],
              ['📋', 'Append-Only Ledger'],
              ['🇪🇺', 'EU AI Act Ready'],
            ].map(([icon, label]) => (
              <div key={label} style={{
                display: 'flex', alignItems: 'center', gap: 7,
                background: NAVY2, border: `1px solid ${GOLD_BORDER}`,
                borderRadius: 20, padding: '6px 14px',
                fontSize: 12, color: TEXT,
              }}>
                <span>{icon}</span>
                <span style={{ fontFamily: 'monospace' }}>{label}</span>
              </div>
            ))}
          </div>

          {/* EU AI Act countdown */}
          {manifest && (
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 10,
              background: AMBER_DIM, border: `1px solid rgba(245,158,11,0.25)`,
              borderRadius: 10, padding: '10px 20px', marginTop: 24,
            }}>
              <span style={{ fontSize: 18 }}>⚡</span>
              <div style={{ textAlign: 'left' }}>
                <div style={{ fontSize: 12, color: AMBER, fontWeight: 700 }}>
                  EU AI Act enforcement in {manifest.days_until_enforcement} days
                </div>
                <div style={{ fontSize: 11, color: SLATE }}>August 2, 2026 · Articles 9, 13 & 17</div>
              </div>
            </div>
          )}
        </div>

        {/* Stats row */}
        {manifest && (
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 40 }}>
            <DiffBlock icon="⬡" label="Total Certificates" value={String(manifest.registry_stats.total)} sub="All time" />
            <DiffBlock icon="✅" label="Active Certificates" value={String(manifest.registry_stats.active)} sub="Currently valid" />
            <DiffBlock icon="🔑" label="Signing Algorithm" value="ML-DSA-65" sub="FIPS 204 · Post-Quantum" />
            <DiffBlock icon="📐" label="Formal Invariants" value={String(manifest.invariants.length)} sub="PoGR-INV-001–006" />
          </div>
        )}

        {/* Tabs */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 28 }}>
          <button style={tabStyle(tab === 'registry')} onClick={() => setTab('registry')}>Public Registry</button>
          <button style={tabStyle(tab === 'verify')} onClick={() => setTab('verify')}>Verify Certificate</button>
          <button style={tabStyle(tab === 'about')} onClick={() => setTab('about')}>About PoGR</button>
        </div>

        {/* ── TAB: Registry ── */}
        {tab === 'registry' && (
          <div>
            <div style={{ display: 'flex', gap: 12, marginBottom: 20, alignItems: 'center' }}>
              <input
                value={searchQ}
                onChange={e => setSearchQ(e.target.value)}
                placeholder="Search by organization name or POGC-ID…"
                style={{
                  flex: 1, padding: '10px 16px',
                  background: NAVY2, border: `1px solid ${GOLD_BORDER}`,
                  borderRadius: 8, color: TEXT, fontSize: 13,
                  outline: 'none', fontFamily: 'monospace',
                }}
              />
              <span style={{ fontSize: 12, color: SLATE, whiteSpace: 'nowrap' }}>
                {registryTotal} certificate{registryTotal !== 1 ? 's' : ''}
              </span>
            </div>

            {loadingRegistry && (
              <div style={{ textAlign: 'center', padding: 40, color: SLATE, fontSize: 13 }}>
                Loading registry…
              </div>
            )}

            {!loadingRegistry && entries.length === 0 && (
              <div style={{
                background: NAVY2, border: `1px solid ${GOLD_BORDER}`,
                borderRadius: 12, padding: 48, textAlign: 'center',
              }}>
                <div style={{ fontSize: 40, marginBottom: 12 }}>⬡</div>
                <div style={{ fontSize: 16, color: MUTED, fontWeight: 600 }}>Registry is empty</div>
                <div style={{ fontSize: 13, color: SLATE, marginTop: 8 }}>
                  Be the first organization to publish a Proof of Governance Certificate.
                </div>
                <div style={{ marginTop: 20 }}>
                  <button
                    onClick={() => navigate('/governance-api')}
                    style={{
                      background: GOLD, color: NAVY, border: 'none',
                      borderRadius: 8, padding: '10px 22px',
                      fontSize: 13, fontWeight: 700, cursor: 'pointer',
                    }}
                  >
                    Get Started with OGR →
                  </button>
                </div>
              </div>
            )}

            {!loadingRegistry && entries.length > 0 && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 14 }}>
                {entries.map(cert => (
                  <CertCard
                    key={cert.pogc_id}
                    cert={cert}
                    onSelect={id => { setTab('verify'); setVerifyInput(id); handleVerify(id) }}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── TAB: Verify ── */}
        {tab === 'verify' && (
          <div>
            <div style={{
              background: NAVY2, border: `1px solid ${GOLD_BORDER}`,
              borderRadius: 12, padding: 28, marginBottom: 24,
            }}>
              <div style={{ fontSize: 14, color: TEXT, fontWeight: 600, marginBottom: 6 }}>
                Verify any PoG Certificate
              </div>
              <div style={{ fontSize: 12, color: SLATE, marginBottom: 16 }}>
                Enter a POGC-ID. No account required. PoGR-INV-003 — zero-trust verification.
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                <input
                  value={verifyInput}
                  onChange={e => setVerifyInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleVerify()}
                  placeholder="POGC-A3F2B1C4D5E6F7A8"
                  style={{
                    flex: 1, padding: '11px 16px',
                    background: NAVY3, border: `1px solid ${GOLD_BORDER}`,
                    borderRadius: 8, color: TEXT, fontSize: 13,
                    outline: 'none', fontFamily: 'monospace',
                  }}
                />
                <button
                  onClick={() => handleVerify()}
                  disabled={verifying || !verifyInput.trim()}
                  style={{
                    padding: '11px 24px',
                    background: verifying ? GOLD_DIM : GOLD,
                    color: verifying ? GOLD : NAVY,
                    border: 'none', borderRadius: 8,
                    fontSize: 13, fontWeight: 700, cursor: verifying ? 'not-allowed' : 'pointer',
                    transition: 'all 0.15s',
                  }}
                >
                  {verifying ? 'Verifying…' : 'Verify'}
                </button>
              </div>
              {verifyError && (
                <div style={{
                  marginTop: 12, padding: '10px 14px',
                  background: RED_DIM, border: `1px solid ${RED_BORDER}`,
                  borderRadius: 8, fontSize: 13, color: RED,
                }}>
                  {verifyError}
                </div>
              )}
            </div>

            {verifyResult && <VerifyPanel result={verifyResult} />}

            {!verifyResult && !verifyError && (
              <div style={{
                background: NAVY2, border: `1px solid ${GOLD_BORDER}`,
                borderRadius: 12, padding: 32, textAlign: 'center',
              }}>
                <HexIcon size={44} />
                <div style={{ fontSize: 14, color: MUTED, marginTop: 12 }}>
                  Enter a POGC-ID above to verify a certificate
                </div>
                <div style={{ fontSize: 12, color: SLATE, marginTop: 6 }}>
                  Or browse the Public Registry and click any certificate to verify it
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── TAB: About ── */}
        {tab === 'about' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>

            {/* What is PoGR */}
            <div style={{ background: NAVY2, border: `1px solid ${GOLD_BORDER}`, borderRadius: 12, padding: 28 }}>
              <h2 style={{ fontSize: 18, fontWeight: 700, color: GOLD, margin: '0 0 14px' }}>
                What is the Proof of Governance Registry?
              </h2>
              <p style={{ fontSize: 14, color: MUTED, lineHeight: 1.7, margin: 0 }}>
                The PoGR is a globally accessible, append-only public registry of AI governance certificates.
                It does for AI governance decisions what a certificate authority does for web security —
                except it requires no central trust anchor, because every certificate carries its own
                post-quantum cryptographic proof.
              </p>
              <p style={{ fontSize: 14, color: MUTED, lineHeight: 1.7, marginTop: 12, marginBottom: 0 }}>
                <strong style={{ color: TEXT }}>One sentence:</strong> An enterprise connects its AI agents
                to OMNIX, governs every decision through the OGR, and receives a publicly verifiable
                PoG Certificate that any regulator, customer, or court can verify in seconds —
                without any access to the enterprise's internal systems.
              </p>
            </div>

            {/* Invariants */}
            <div>
              <h2 style={{ fontSize: 16, fontWeight: 700, color: TEXT, margin: '0 0 14px' }}>
                Six Formal Invariants
              </h2>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 10 }}>
                {[
                  ['PoGR-INV-001', 'Session proof backing — every certificate is backed by a sealed OGR session'],
                  ['PoGR-INV-002', 'Append-only ledger — no certificate can be deleted from the registry'],
                  ['PoGR-INV-003', 'Zero-trust verification — no OMNIX account required to verify'],
                  ['PoGR-INV-004', 'Explicit TTL — certificates expire in 365 days; renewal requires new proof'],
                  ['PoGR-INV-005', 'Three-channel trust anchor — HTTP · DNS · Zenodo DOI'],
                  ['PoGR-INV-006', 'Issuer-only revocation — PQC proof required from original issuer'],
                ].map(([id, desc]) => <InvariantChip key={id} id={id} desc={desc} />)}
              </div>
            </div>

            {/* How it works */}
            <div style={{ background: NAVY2, border: `1px solid ${GOLD_BORDER}`, borderRadius: 12, padding: 28 }}>
              <h2 style={{ fontSize: 16, fontWeight: 700, color: TEXT, margin: '0 0 18px' }}>
                How It Works — Four Steps
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {[
                  ['1', 'Govern your agent sessions via OMNIX OGR', 'Every turn produces a Behavioral Anchor Record signed with ML-DSA-65. A Cross-Turn Coherence Hash Chain links all turns.'],
                  ['2', 'Request a PoG Certificate', 'POST /v1/pogr/certify with your sealed session ID. OMNIX verifies the session, signs the certificate, and publishes it to the public registry.'],
                  ['3', 'Receive your certificate + badge', 'Get a POGC-ID, a public verification URL, and an embeddable SVG badge for your product page and regulatory submissions.'],
                  ['4', 'Regulators verify in seconds', 'Anyone can call GET /v1/pogr/verify/{id} — or verify offline using the published platform public key. Zero OMNIX access required.'],
                ].map(([num, title, desc]) => (
                  <div key={num} style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
                    <div style={{
                      minWidth: 28, height: 28, borderRadius: '50%',
                      background: GOLD_DIM, border: `1px solid ${GOLD_BORDER}`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 12, fontWeight: 700, color: GOLD, fontFamily: 'monospace',
                    }}>{num}</div>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 600, color: TEXT }}>{title}</div>
                      <div style={{ fontSize: 12, color: SLATE, marginTop: 3, lineHeight: 1.6 }}>{desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Standards */}
            <div style={{ background: NAVY2, border: `1px solid ${GOLD_BORDER}`, borderRadius: 12, padding: 28 }}>
              <h2 style={{ fontSize: 16, fontWeight: 700, color: TEXT, margin: '0 0 14px' }}>
                Standards Foundation
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {[
                  ['RFC-ATF-1', '10.5281/zenodo.20155016', 'Identity · Delegation · PQC Signing'],
                  ['RFC-ATF-2', '10.5281/zenodo.20241344', 'Runtime Continuity · Authority Fragmentation Guard'],
                  ['RFC-ATF-3', '10.5281/zenodo.20247342', 'Evidence Lifecycle · Forensic Verification Protocol'],
                ].map(([rfc, doi, desc]) => (
                  <div key={rfc} style={{
                    display: 'flex', gap: 16, alignItems: 'center',
                    background: NAVY3, borderRadius: 8, padding: '10px 14px',
                  }}>
                    <span style={{ fontFamily: 'monospace', fontSize: 12, color: GOLD, minWidth: 80 }}>{rfc}</span>
                    <span style={{ fontFamily: 'monospace', fontSize: 10, color: BLUE, flex: 1 }}>{doi}</span>
                    <span style={{ fontSize: 11, color: SLATE }}>{desc}</span>
                  </div>
                ))}
              </div>
              <div style={{ fontSize: 11, color: SLATE, marginTop: 12 }}>
                Three published standards · Six permanent DOIs · Zenodo + Figshare · Prior art established
              </div>
            </div>

            {/* Platform key */}
            {manifest?.platform_key && (
              <div style={{ background: NAVY2, border: `1px solid ${GOLD_BORDER}`, borderRadius: 12, padding: 28 }}>
                <h2 style={{ fontSize: 16, fontWeight: 700, color: TEXT, margin: '0 0 14px' }}>
                  Platform Public Key — PoGR-INV-005
                </h2>
                <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                  {[
                    ['Algorithm',  manifest.platform_key.algorithm?.toUpperCase() || 'ML-DSA-65'],
                    ['Standard',   'FIPS 204'],
                    ['Configured', manifest.platform_key.configured ? 'YES' : 'NO'],
                    ['Fingerprint', manifest.platform_key.fingerprint_short || '—'],
                  ].map(([k, v]) => (
                    <div key={k} style={{
                      background: NAVY3, borderRadius: 8, padding: '10px 14px', flex: 1, minWidth: 130,
                    }}>
                      <div style={{ fontSize: 10, color: SLATE }}>{k}</div>
                      <div style={{ fontFamily: 'monospace', fontSize: 12, color: TEXT, marginTop: 3 }}>{v}</div>
                    </div>
                  ))}
                </div>
                <div style={{ fontSize: 11, color: SLATE, marginTop: 12 }}>
                  Channel 1: <span style={{ color: MUTED }}>GET /v1/pogr/manifest</span> ·
                  Channel 2: <span style={{ color: MUTED }}>DNS TXT _omnix-pogr.omnixquantum.net</span> ·
                  Channel 3: <span style={{ color: MUTED }}>Zenodo DOI snapshot (quarterly)</span>
                </div>
              </div>
            )}

            {/* CTA */}
            <div style={{
              background: GOLD_DIM, border: `1.5px solid ${GOLD_BORDER}`,
              borderRadius: 12, padding: 28, textAlign: 'center',
            }}>
              <HexIcon size={40} />
              <div style={{ fontSize: 18, fontWeight: 700, color: GOLD, marginTop: 12 }}>
                Issue your first PoG Certificate
              </div>
              <div style={{ fontSize: 13, color: MUTED, marginTop: 6, maxWidth: 460, margin: '6px auto 20px' }}>
                Connect your AI agents to the OMNIX Governance Runtime.
                Seal a session. Issue your certificate in one API call.
              </div>
              <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
                <button onClick={() => navigate('/governance-api')} style={{
                  background: GOLD, color: NAVY, border: 'none',
                  borderRadius: 8, padding: '11px 24px',
                  fontSize: 13, fontWeight: 700, cursor: 'pointer',
                }}>
                  Governance Runtime API →
                </button>
                <button onClick={() => navigate('/docs')} style={{
                  background: 'transparent', color: GOLD,
                  border: `1px solid ${GOLD_BORDER}`,
                  borderRadius: 8, padding: '11px 24px',
                  fontSize: 13, fontWeight: 600, cursor: 'pointer',
                }}>
                  Read the Docs
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div style={{
        borderTop: `1px solid ${GOLD_BORDER}`, marginTop: 60,
        padding: '24px', textAlign: 'center',
      }}>
        <div style={{ fontSize: 11, color: SLATE, fontFamily: 'monospace' }}>
          OMNIX QUANTUM LTD · ADR-186 · OMNIX-POGR-2026-001 · RFC-ATF-1/2/3 ·
          {' '}<span style={{ color: GREEN }}>PoGR-INV-001–006 active</span>
        </div>
      </div>
    </div>
  )
}
