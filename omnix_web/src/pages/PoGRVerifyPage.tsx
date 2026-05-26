/**
 * OMNIX Proof of Governance — Public Certificate Verifier
 * ADR-189 · OMNIX-POGR-2026-001
 *
 * Standalone public page — no account, no API key.
 * Designed for regulators, auditors, customers, courts.
 * Route: /verify/:pogcId  (also /verify with search input)
 *
 * PoGR-INV-003: zero-trust verification.
 * Harold Nunes — OMNIX QUANTUM LTD — May 2026
 */
import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'

// ── Design tokens ─────────────────────────────────────────────────────────────
const GOLD        = '#C9A227'
const GOLD_DIM    = 'rgba(201,162,39,0.10)'
const GOLD_BORDER = 'rgba(201,162,39,0.22)'
const NAVY        = '#060F1E'
const NAVY2       = '#0A1628'
const NAVY3       = '#0D1E38'
const GREEN       = '#22c55e'
const GREEN_DIM   = 'rgba(34,197,94,0.07)'
const GREEN_BORDER= 'rgba(34,197,94,0.20)'
const RED         = '#ef4444'
const RED_DIM     = 'rgba(239,68,68,0.07)'
const RED_BORDER  = 'rgba(239,68,68,0.20)'
const AMBER       = '#f59e0b'
const AMBER_DIM   = 'rgba(245,158,11,0.08)'
const SLATE       = '#64748b'
const TEXT        = '#e2e8f0'
const MUTED       = '#94a3b8'
const BLUE        = '#3b82f6'
const BLUE_DIM    = 'rgba(59,130,246,0.08)'

const API = (import.meta.env.VITE_RAILWAY_API_URL || '').replace(/\/$/, '')

// ── Types ─────────────────────────────────────────────────────────────────────
interface Certificate {
  pogc_id: string
  session_id: string
  ctchc_seal_hash: string
  issuer: string
  subject_org: string
  compliance_tier: string
  mandate_certification: string
  turn_count: number
  avg_conformance: number
  issued_at: string
  expires_at: string
  regulatory_tags: string[]
  content_hash: string
  pqc_algorithm: string
  pqc_signature_algorithm: string
  pqc_signature_present: boolean
  agent_id?: string
  status: string
  revocation_reason?: string
}

interface VerifyResult {
  valid: boolean
  pogc_id: string
  verification_notes: string[]
  certificate: Certificate
  verified_at: string
}

// ── Hex SVG ───────────────────────────────────────────────────────────────────
function HexLogo({ size = 40 }: { size?: number }) {
  const cx = size / 2, cy = size / 2, r = size * 0.42
  const pts = Array.from({ length: 6 }, (_, i) => {
    const a = (Math.PI / 3) * i - Math.PI / 6
    return `${cx + r * Math.cos(a)},${cy + r * Math.sin(a)}`
  }).join(' ')
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <polygon points={pts} fill={`${GOLD}18`} stroke={GOLD} strokeWidth="1.5" />
      <text x={cx} y={cy + 4} textAnchor="middle" fontSize={size * 0.26}
        fontFamily="monospace" fill={GOLD} fontWeight="700">PoG</text>
    </svg>
  )
}

// ── Conformance ring ──────────────────────────────────────────────────────────
function ConformanceRing({ value }: { value: number }) {
  const pct = Math.round(value * 100)
  const color = pct >= 90 ? GREEN : pct >= 70 ? AMBER : RED
  const r = 38, circ = 2 * Math.PI * r
  const dash = (pct / 100) * circ
  return (
    <div style={{ position: 'relative', width: 100, height: 100, flexShrink: 0 }}>
      <svg width={100} height={100} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={50} cy={50} r={r} fill="none" stroke={`${color}20`} strokeWidth={7} />
        <circle
          cx={50} cy={50} r={r} fill="none"
          stroke={color} strokeWidth={7}
          strokeDasharray={`${dash} ${circ}`}
          strokeLinecap="round"
          style={{ transition: 'stroke-dasharray 1s ease' }}
        />
      </svg>
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
      }}>
        <span style={{ fontSize: 22, fontWeight: 800, color, fontFamily: 'monospace', lineHeight: 1 }}>
          {pct}%
        </span>
        <span style={{ fontSize: 9, color: SLATE, marginTop: 2 }}>conformance</span>
      </div>
    </div>
  )
}

// ── Field row ─────────────────────────────────────────────────────────────────
function Field({ label, value, mono = false, wrap = false }: {
  label: string; value: string; mono?: boolean; wrap?: boolean
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <span style={{ fontSize: 10, color: SLATE, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '0.07em' }}>
        {label}
      </span>
      <span style={{
        fontSize: mono ? 11 : 13,
        color: TEXT,
        fontFamily: mono ? 'monospace' : 'system-ui, sans-serif',
        wordBreak: wrap ? 'break-all' : 'normal',
        lineHeight: 1.5,
      }}>
        {value}
      </span>
    </div>
  )
}

// ── Verification note ─────────────────────────────────────────────────────────
function VerificationNote({ note }: { note: string }) {
  const ok    = note.startsWith('✓')
  const warn  = note.startsWith('⚠')
  const color = ok ? GREEN : warn ? AMBER : RED
  const bg    = ok ? GREEN_DIM : warn ? AMBER_DIM : RED_DIM
  const border= ok ? GREEN_BORDER : warn ? 'rgba(245,158,11,0.2)' : RED_BORDER
  return (
    <div style={{
      display: 'flex', alignItems: 'flex-start', gap: 10,
      background: bg, border: `1px solid ${border}`,
      borderRadius: 7, padding: '8px 12px',
    }}>
      <span style={{ fontSize: 13, flexShrink: 0, color }}>{note[0]}</span>
      <span style={{ fontSize: 12, color: TEXT, fontFamily: 'monospace', lineHeight: 1.5 }}>
        {note.slice(2).trim()}
      </span>
    </div>
  )
}

// ── Copy button ───────────────────────────────────────────────────────────────
function CopyButton({ text, label = 'Copy' }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <button
      onClick={() => {
        navigator.clipboard.writeText(text).then(() => {
          setCopied(true)
          setTimeout(() => setCopied(false), 2000)
        })
      }}
      style={{
        background: copied ? GREEN_DIM : NAVY3,
        border: `1px solid ${copied ? GREEN_BORDER : GOLD_BORDER}`,
        color: copied ? GREEN : MUTED,
        borderRadius: 6, padding: '5px 12px',
        fontSize: 11, cursor: 'pointer',
        fontFamily: 'monospace', transition: 'all 0.2s',
        whiteSpace: 'nowrap',
      }}
    >
      {copied ? '✓ Copied' : label}
    </button>
  )
}

// ── Regulatory tag ────────────────────────────────────────────────────────────
function RegTag({ tag }: { tag: string }) {
  return (
    <span style={{
      fontSize: 10, fontFamily: 'monospace', color: BLUE,
      background: BLUE_DIM, border: `1px solid rgba(59,130,246,0.22)`,
      borderRadius: 4, padding: '3px 9px', fontWeight: 600,
    }}>{tag}</span>
  )
}

// ── Valid certificate display ─────────────────────────────────────────────────
function ValidCertDisplay({ result }: { result: VerifyResult }) {
  const cert = result.certificate
  const pageUrl = `${window.location.origin}/verify/${cert.pogc_id}`
  const isActive = cert.status === 'ACTIVE'
  const statusColor = isActive ? GREEN : cert.status === 'EXPIRED' ? AMBER : RED

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

      {/* ── Verdict banner ── */}
      <div style={{
        background: result.valid ? GREEN_DIM : RED_DIM,
        border: `1.5px solid ${result.valid ? GREEN_BORDER : RED_BORDER}`,
        borderRadius: 14, padding: '28px 32px',
        display: 'flex', alignItems: 'center', gap: 24, flexWrap: 'wrap',
      }}>
        <div style={{ fontSize: 56, lineHeight: 1 }}>{result.valid ? '✅' : '❌'}</div>
        <div style={{ flex: 1, minWidth: 200 }}>
          <div style={{
            fontSize: 28, fontWeight: 800,
            color: result.valid ? GREEN : RED,
            letterSpacing: '-0.02em', lineHeight: 1.1,
          }}>
            {result.valid ? 'Certificate Valid' : 'Verification Failed'}
          </div>
          <div style={{ fontSize: 14, color: MUTED, marginTop: 6 }}>
            {result.valid
              ? 'This governance certificate has been cryptographically verified. The AI session it references was governed correctly.'
              : 'This certificate failed one or more verification checks. See details below.'}
          </div>
        </div>
        {cert && (
          <ConformanceRing value={cert.avg_conformance ?? 0} />
        )}
      </div>

      {/* ── Certificate identity ── */}
      <div style={{
        background: NAVY2, border: `1px solid ${GOLD_BORDER}`,
        borderRadius: 12, padding: 28,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 24 }}>
          <HexLogo size={44} />
          <div>
            <div style={{ fontSize: 11, color: SLATE, fontFamily: 'monospace', letterSpacing: '0.06em' }}>
              PROOF OF GOVERNANCE CERTIFICATE
            </div>
            <div style={{
              fontFamily: 'monospace', fontSize: 18, color: GOLD,
              fontWeight: 700, marginTop: 3, letterSpacing: '0.04em',
            }}>
              {cert.pogc_id}
            </div>
          </div>
          <div style={{ marginLeft: 'auto' }}>
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              background: `${statusColor}15`,
              border: `1px solid ${statusColor}40`,
              borderRadius: 20, padding: '5px 14px',
              fontSize: 11, fontFamily: 'monospace',
              color: statusColor, fontWeight: 700,
            }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: statusColor }} />
              {cert.status}
            </span>
          </div>
        </div>

        {/* ── Mandate tier banner (MIVP-INV-008/009 — ADR-194) ── */}
        {cert.mandate_certification && cert.mandate_certification !== 'UNCERTIFIED' && (
          <div style={{
            background: cert.mandate_certification === 'MANDATE-BOUND'
              ? 'rgba(34,197,94,0.07)' : 'rgba(245,158,11,0.07)',
            border: `1px solid ${cert.mandate_certification === 'MANDATE-BOUND'
              ? 'rgba(34,197,94,0.25)' : 'rgba(245,158,11,0.25)'}`,
            borderRadius: 10, padding: '14px 20px', marginBottom: 8,
            display: 'flex', alignItems: 'center', gap: 14,
          }}>
            <span style={{ fontSize: 22, flexShrink: 0 }}>
              {cert.mandate_certification === 'MANDATE-BOUND' ? '🔒' : '✅'}
            </span>
            <div>
              <div style={{
                fontFamily: 'monospace', fontSize: 13, fontWeight: 700,
                color: cert.mandate_certification === 'MANDATE-BOUND' ? GREEN : AMBER,
                letterSpacing: '0.04em',
              }}>
                {cert.mandate_certification}
              </div>
              <div style={{ fontSize: 11, color: MUTED, marginTop: 3 }}>
                {cert.mandate_certification === 'MANDATE-BOUND'
                  ? 'Pristine mandate fidelity — zero violations, zero warnings · MIVP-INV-008 (ADR-194)'
                  : 'Mission-aligned — zero violations, warnings within tolerance · MIVP-INV-009 (ADR-194)'}
              </div>
            </div>
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px,1fr))', gap: 20 }}>
          <Field label="Issuer" value={cert.issuer} />
          <Field label="Organization" value={cert.subject_org} />
          <Field label="Compliance Tier" value={cert.compliance_tier} />
          <Field label="Mandate Certification" value={cert.mandate_certification || 'UNCERTIFIED'} mono />
          <Field label="Agent" value={cert.agent_id || '—'} mono />
          <Field label="Session Turns" value={String(cert.turn_count)} />
          <Field label="PQC Algorithm" value={(cert.pqc_algorithm || 'ml-dsa-65').toUpperCase()} mono />
          <Field label="Issued" value={new Date(cert.issued_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })} />
          <Field label="Expires" value={new Date(cert.expires_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })} />
        </div>

        {cert.regulatory_tags?.length > 0 && (
          <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap', marginTop: 20, paddingTop: 20, borderTop: `1px solid ${GOLD_BORDER}` }}>
            {cert.regulatory_tags.map(t => <RegTag key={t} tag={t} />)}
          </div>
        )}
      </div>

      {/* ── Verification checks ── */}
      <div>
        <div style={{ fontSize: 12, color: SLATE, fontFamily: 'monospace', marginBottom: 10,
          textTransform: 'uppercase', letterSpacing: '0.07em' }}>
          Verification Checks · PoGR-INV-003
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
          {result.verification_notes.map((n, i) => <VerificationNote key={i} note={n} />)}
        </div>
      </div>

      {/* ── Cryptographic proof ── */}
      <div style={{
        background: NAVY2, border: `1px solid ${GOLD_BORDER}`,
        borderRadius: 12, padding: 24,
      }}>
        <div style={{ fontSize: 12, color: SLATE, fontFamily: 'monospace', marginBottom: 16,
          textTransform: 'uppercase', letterSpacing: '0.07em' }}>
          Cryptographic Proof
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
            <Field label="Content Hash (SHA3-256)" value={cert.content_hash} mono wrap />
            <CopyButton text={cert.content_hash} label="Copy hash" />
          </div>
          <div style={{ height: 1, background: GOLD_BORDER }} />
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
            <Field label="CTCHC Seal Hash" value={cert.ctchc_seal_hash} mono wrap />
            <CopyButton text={cert.ctchc_seal_hash} label="Copy hash" />
          </div>
          <div style={{ height: 1, background: GOLD_BORDER }} />
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            <div style={{ background: NAVY3, borderRadius: 8, padding: '10px 14px', flex: 1, minWidth: 140 }}>
              <div style={{ fontSize: 10, color: SLATE }}>Signature Algorithm</div>
              <div style={{ fontFamily: 'monospace', fontSize: 12, color: GOLD, marginTop: 4 }}>
                {(cert.pqc_algorithm || 'ml-dsa-65').toUpperCase()} · FIPS 204
              </div>
            </div>
            <div style={{ background: NAVY3, borderRadius: 8, padding: '10px 14px', flex: 1, minWidth: 140 }}>
              <div style={{ fontSize: 10, color: SLATE }}>Signature Present</div>
              <div style={{ fontFamily: 'monospace', fontSize: 12, color: cert.pqc_signature_present ? GREEN : RED, marginTop: 4 }}>
                {cert.pqc_signature_present ? '✓ YES' : '✗ NO'}
              </div>
            </div>
            <div style={{ background: NAVY3, borderRadius: 8, padding: '10px 14px', flex: 1, minWidth: 140 }}>
              <div style={{ fontSize: 10, color: SLATE }}>Session Proof</div>
              <div style={{ fontFamily: 'monospace', fontSize: 12, color: TEXT, marginTop: 4 }}>
                {cert.session_id?.slice(0, 16)}…
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Share / actions ── */}
      <div style={{
        background: GOLD_DIM, border: `1px solid ${GOLD_BORDER}`,
        borderRadius: 12, padding: 20,
        display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap',
      }}>
        <div style={{ flex: 1, minWidth: 200 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: GOLD, marginBottom: 2 }}>
            Share this verification
          </div>
          <div style={{
            fontFamily: 'monospace', fontSize: 11, color: MUTED,
            wordBreak: 'break-all',
          }}>{pageUrl}</div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <CopyButton text={pageUrl} label="Copy link" />
          <CopyButton text={cert.pogc_id} label="Copy ID" />
        </div>
      </div>

      {/* ── Verified timestamp ── */}
      <div style={{ fontSize: 10, color: SLATE, textAlign: 'center', fontFamily: 'monospace' }}>
        Verified {result.verified_at ? new Date(result.verified_at).toUTCString() : '—'} · PoGR-INV-003 · Zero-trust verification
      </div>
    </div>
  )
}

// ── Search / empty state ──────────────────────────────────────────────────────
function SearchState({ onSearch }: { onSearch: (id: string) => void }) {
  const [input, setInput] = useState('')
  return (
    <div style={{
      background: NAVY2, border: `1px solid ${GOLD_BORDER}`,
      borderRadius: 14, padding: '48px 40px', textAlign: 'center',
      maxWidth: 560, margin: '0 auto',
    }}>
      <HexLogo size={52} />
      <h2 style={{ fontSize: 22, fontWeight: 700, color: TEXT, margin: '18px 0 8px', letterSpacing: '-0.02em' }}>
        Verify any PoG Certificate
      </h2>
      <p style={{ fontSize: 13, color: MUTED, margin: '0 0 28px', lineHeight: 1.65 }}>
        Enter a certificate ID to instantly verify that an AI governance session was conducted correctly.
        No account required. No OMNIX access required.
      </p>
      <div style={{ display: 'flex', gap: 10 }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && input.trim() && onSearch(input.trim())}
          placeholder="POGC-A3F2B1C4D5E6F7A8"
          style={{
            flex: 1, padding: '12px 16px',
            background: NAVY3, border: `1px solid ${GOLD_BORDER}`,
            borderRadius: 8, color: TEXT, fontSize: 13,
            outline: 'none', fontFamily: 'monospace',
          }}
          autoFocus
        />
        <button
          onClick={() => input.trim() && onSearch(input.trim())}
          disabled={!input.trim()}
          style={{
            padding: '12px 24px',
            background: input.trim() ? GOLD : GOLD_DIM,
            color: input.trim() ? NAVY : SLATE,
            border: 'none', borderRadius: 8,
            fontSize: 13, fontWeight: 700,
            cursor: input.trim() ? 'pointer' : 'not-allowed',
            transition: 'all 0.15s',
          }}
        >
          Verify
        </button>
      </div>
      <div style={{ marginTop: 24, fontSize: 11, color: SLATE }}>
        PoGR-INV-003 — Zero-trust verification · ML-DSA-65 / FIPS 204 · Append-only ledger
      </div>
    </div>
  )
}

// ── Not found state ───────────────────────────────────────────────────────────
function NotFoundState({ pogcId }: { pogcId: string }) {
  return (
    <div style={{
      background: RED_DIM, border: `1.5px solid ${RED_BORDER}`,
      borderRadius: 14, padding: '48px 40px', textAlign: 'center',
      maxWidth: 520, margin: '0 auto',
    }}>
      <div style={{ fontSize: 52 }}>❌</div>
      <h2 style={{ fontSize: 22, fontWeight: 700, color: RED, margin: '16px 0 8px' }}>
        Certificate Not Found
      </h2>
      <div style={{
        fontFamily: 'monospace', fontSize: 13, color: MUTED,
        background: 'rgba(0,0,0,0.2)', borderRadius: 8,
        padding: '10px 16px', margin: '12px 0',
        wordBreak: 'break-all',
      }}>
        {pogcId}
      </div>
      <p style={{ fontSize: 13, color: MUTED, lineHeight: 1.65 }}>
        No certificate with this ID exists in the Proof of Governance Registry.
        The certificate may never have been issued, or the ID may be incorrect.
      </p>
    </div>
  )
}

// ── Loading state ─────────────────────────────────────────────────────────────
function LoadingState({ pogcId }: { pogcId: string }) {
  return (
    <div style={{ textAlign: 'center', padding: '60px 24px' }}>
      <div style={{ marginBottom: 20 }}>
        <HexLogo size={52} />
      </div>
      <div style={{ fontSize: 14, color: MUTED, fontFamily: 'monospace', marginBottom: 8 }}>
        Verifying certificate…
      </div>
      <div style={{ fontFamily: 'monospace', fontSize: 11, color: SLATE }}>
        {pogcId}
      </div>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function PoGRVerifyPage() {
  const { pogcId } = useParams<{ pogcId?: string }>()
  const navigate   = useNavigate()
  const fetchedRef = useRef<string | null>(null)

  const [result,  setResult]  = useState<VerifyResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [notFound, setNotFound] = useState(false)
  const [error,   setError]   = useState('')
  const [activePogcId, setActivePogcId] = useState(pogcId || '')

  async function doVerify(id: string) {
    if (!id || fetchedRef.current === id) return
    fetchedRef.current = id
    setLoading(true)
    setResult(null)
    setNotFound(false)
    setError('')
    setActivePogcId(id)
    try {
      const r = await fetch(`${API}/v1/pogr/verify/${encodeURIComponent(id)}`)
      if (r.status === 404) { setNotFound(true); return }
      const data = await r.json()
      setResult(data)
    } catch {
      setError('Registry unavailable — please try again.')
      fetchedRef.current = null
    } finally {
      setLoading(false)
    }
  }

  function handleSearch(id: string) {
    fetchedRef.current = null
    navigate(`/verify/${encodeURIComponent(id)}`)
    doVerify(id)
  }

  useEffect(() => {
    if (pogcId) doVerify(pogcId)
  }, [pogcId])

  return (
    <div style={{ minHeight: '100vh', background: NAVY, color: TEXT, fontFamily: 'system-ui, sans-serif' }}>

      {/* ── Nav ── */}
      <div style={{
        borderBottom: `1px solid ${GOLD_BORDER}`, background: `${NAVY}ee`,
        position: 'sticky', top: 0, zIndex: 100, backdropFilter: 'blur(12px)',
      }}>
        <div style={{
          maxWidth: 900, margin: '0 auto', padding: '0 24px',
          display: 'flex', alignItems: 'center', height: 56, gap: 12,
        }}>
          <button
            onClick={() => navigate('/proof-of-governance')}
            style={{ background: 'none', border: 'none', cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: 8 }}
          >
            <HexLogo size={26} />
            <span style={{ fontFamily: 'monospace', fontSize: 12, color: GOLD,
              fontWeight: 700, letterSpacing: '0.05em' }}>
              OMNIX QUANTUM
            </span>
          </button>
          <span style={{ color: GOLD_BORDER, fontSize: 16 }}>›</span>
          <span style={{ fontSize: 12, color: SLATE }}>PoG Verifier</span>
          <div style={{ flex: 1 }} />
          <button
            onClick={() => navigate('/proof-of-governance')}
            style={{
              background: 'none', border: `1px solid ${GOLD_BORDER}`,
              color: GOLD, borderRadius: 6, padding: '5px 14px',
              fontSize: 11, cursor: 'pointer', fontFamily: 'monospace',
            }}
          >
            Registry →
          </button>
        </div>
      </div>

      {/* ── Content ── */}
      <div style={{ maxWidth: 900, margin: '0 auto', padding: '40px 24px 80px' }}>

        {/* ── Header strip ── */}
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <div style={{ fontSize: 12, color: SLATE, fontFamily: 'monospace',
            letterSpacing: '0.1em', marginBottom: 10 }}>
            OMNIX PROOF OF GOVERNANCE REGISTRY · PUBLIC VERIFIER
          </div>
          <h1 style={{
            fontSize: 'clamp(26px, 4vw, 38px)', fontWeight: 800,
            color: TEXT, margin: 0, letterSpacing: '-0.02em', lineHeight: 1.1,
          }}>
            AI Governance Certificate Verification
          </h1>
          <p style={{ fontSize: 14, color: MUTED, marginTop: 12, maxWidth: 520, margin: '12px auto 0', lineHeight: 1.65 }}>
            Cryptographically verify any PoG Certificate.
            No account. No API key. No trust required.
          </p>

          {/* Trust anchors */}
          <div style={{
            display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap', marginTop: 20,
          }}>
            {[
              ['⬡', 'ML-DSA-65 · FIPS 204'],
              ['🔓', 'Zero-Trust · PoGR-INV-003'],
              ['📋', 'Append-Only Ledger'],
              ['🇪🇺', 'EU AI Act Ready'],
            ].map(([icon, label]) => (
              <div key={label} style={{
                display: 'flex', alignItems: 'center', gap: 6,
                background: NAVY2, border: `1px solid ${GOLD_BORDER}`,
                borderRadius: 20, padding: '5px 12px',
                fontSize: 11, color: MUTED, fontFamily: 'monospace',
              }}>
                <span>{icon}</span><span>{label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* ── Search bar always visible when result is shown ── */}
        {result && (
          <div style={{
            background: NAVY2, border: `1px solid ${GOLD_BORDER}`,
            borderRadius: 10, padding: '16px 20px', marginBottom: 28,
            display: 'flex', gap: 10,
          }}>
            <input
              defaultValue={activePogcId}
              key={activePogcId}
              onKeyDown={e => {
                if (e.key === 'Enter') {
                  const v = (e.target as HTMLInputElement).value.trim()
                  if (v) handleSearch(v)
                }
              }}
              placeholder="POGC-…"
              style={{
                flex: 1, padding: '8px 14px',
                background: NAVY3, border: `1px solid ${GOLD_BORDER}`,
                borderRadius: 7, color: TEXT, fontSize: 12,
                outline: 'none', fontFamily: 'monospace',
              }}
            />
            <button
              onClick={e => {
                const inp = (e.currentTarget.parentElement!.querySelector('input') as HTMLInputElement).value.trim()
                if (inp) handleSearch(inp)
              }}
              style={{
                padding: '8px 20px', background: GOLD, color: NAVY,
                border: 'none', borderRadius: 7, fontSize: 12,
                fontWeight: 700, cursor: 'pointer',
              }}
            >
              Verify
            </button>
          </div>
        )}

        {/* ── States ── */}
        {loading  && <LoadingState pogcId={activePogcId} />}
        {!loading && !result && !notFound && !error && (
          <SearchState onSearch={handleSearch} />
        )}
        {!loading && notFound && (
          <>
            <NotFoundState pogcId={activePogcId} />
            <div style={{ textAlign: 'center', marginTop: 24 }}>
              <button
                onClick={() => { setNotFound(false); fetchedRef.current = null }}
                style={{
                  background: 'none', border: `1px solid ${GOLD_BORDER}`,
                  color: GOLD, borderRadius: 8, padding: '9px 22px',
                  fontSize: 12, cursor: 'pointer',
                }}
              >
                Try another ID
              </button>
            </div>
          </>
        )}
        {!loading && error && (
          <div style={{
            background: RED_DIM, border: `1px solid ${RED_BORDER}`,
            borderRadius: 10, padding: 20, textAlign: 'center',
            fontSize: 13, color: RED,
          }}>
            {error}
            <button
              onClick={() => { setError(''); fetchedRef.current = null; if (activePogcId) doVerify(activePogcId) }}
              style={{
                marginLeft: 12, background: 'none', border: `1px solid ${RED_BORDER}`,
                color: RED, borderRadius: 6, padding: '4px 12px',
                fontSize: 11, cursor: 'pointer',
              }}
            >
              Retry
            </button>
          </div>
        )}
        {!loading && result && <ValidCertDisplay result={result} />}

        {/* ── Footer note ── */}
        <div style={{
          marginTop: 60, paddingTop: 28, borderTop: `1px solid ${GOLD_BORDER}`,
          display: 'flex', gap: 24, justifyContent: 'center', flexWrap: 'wrap',
          fontSize: 11, color: SLATE, fontFamily: 'monospace',
        }}>
          <span>OMNIX QUANTUM LTD</span>
          <span>ADR-186 · ADR-187 · ADR-189</span>
          <span>RFC-ATF-1 through RFC-ATF-6</span>
          <span
            style={{ color: BLUE, cursor: 'pointer' }}
            onClick={() => navigate('/proof-of-governance')}
          >
            PoGR Registry →
          </span>
        </div>
      </div>
    </div>
  )
}
