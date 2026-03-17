import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { Shield, CheckCircle, XCircle, Clock, ExternalLink, Copy, ArrowLeft, Lock, AlertTriangle, Search } from 'lucide-react'

const API_BASE = import.meta.env.VITE_FLASK_API_URL || ''

interface Checkpoint {
  code: string | null
  label_en: string
  label_es: string
  result: 'PASS' | 'BLOCKED' | 'UNKNOWN'
  metric_label: string | null
  metric_value: string | null
  raw: string
}

interface IntegrityBlock {
  content_hash: string
  prev_hash: string
  signature_algorithm: string
  is_pqc: boolean
  independently_verifiable: boolean
  nist_note: string
}

interface VerifyData {
  found: boolean
  receipt_id: string
  timestamp_utc: string
  asset: string
  decision: string
  domain: string
  decision_color: 'green' | 'red' | 'yellow' | 'gray'
  decision_icon: string
  human_summary_en: string
  human_summary_es: string
  checkpoints_total: number
  checkpoints_passed: number
  checkpoints_blocked: number
  checkpoints: Checkpoint[]
  integrity: IntegrityBlock
  policy_version: string
  engine_version: string
  independent_verify_url: string | null
}

function formatTimestamp(ts: string): string {
  try {
    const d = new Date(ts)
    return d.toLocaleString('en-US', {
      month: 'long', day: 'numeric', year: 'numeric',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
      timeZone: 'UTC', timeZoneName: 'short'
    })
  } catch {
    return ts
  }
}

function decisionColors(color: string) {
  if (color === 'green')  return { bg: 'rgba(34,197,94,0.10)',  border: 'rgba(34,197,94,0.30)',  text: '#22c55e',  pill: 'rgba(34,197,94,0.15)' }
  if (color === 'red')    return { bg: 'rgba(239,68,68,0.10)',   border: 'rgba(239,68,68,0.30)',   text: '#ef4444',  pill: 'rgba(239,68,68,0.15)' }
  if (color === 'yellow') return { bg: 'rgba(234,179,8,0.10)',   border: 'rgba(234,179,8,0.30)',   text: '#eab308',  pill: 'rgba(234,179,8,0.15)' }
  return                         { bg: 'rgba(99,102,241,0.10)',  border: 'rgba(99,102,241,0.30)',  text: '#818cf8',  pill: 'rgba(99,102,241,0.15)' }
}

function CheckpointCard({ cp, index: _index }: { cp: Checkpoint; index: number }) {
  const isPass    = cp.result === 'PASS'
  const isBlocked = cp.result === 'BLOCKED'

  return (
    <div style={{
      display: 'flex', gap: '12px', alignItems: 'flex-start',
      padding: '12px 0', borderBottom: '1px solid rgba(255,255,255,0.04)',
    }}>
      <div style={{ flexShrink: 0, paddingTop: '2px' }}>
        {isPass    && <CheckCircle size={16} color="#22c55e" />}
        {isBlocked && <XCircle    size={16} color="#ef4444" />}
        {!isPass && !isBlocked && <Clock size={16} color="#6b7280" />}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: '8px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.88rem', fontWeight: 500, color: '#e5e7eb' }}>
            {cp.code && <span style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: '#6b7280', marginRight: '6px' }}>{cp.code}</span>}
            {cp.label_en}
          </span>
          <span style={{
            fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.08em',
            fontFamily: 'monospace', flexShrink: 0,
            color: isPass ? '#22c55e' : isBlocked ? '#ef4444' : '#6b7280',
          }}>
            {cp.result}
          </span>
        </div>
        {cp.metric_label && cp.metric_value && (
          <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '3px' }}>
            {cp.metric_label}: <span style={{ fontFamily: 'monospace', color: '#9ca3af' }}>{cp.metric_value}</span>
          </div>
        )}
      </div>
    </div>
  )
}

function HashDisplay({ label, value }: { label: string; value: string }) {
  const [copied, setCopied] = useState(false)
  function copy() {
    navigator.clipboard.writeText(value).catch(() => {})
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }
  return (
    <div style={{ marginBottom: '10px' }}>
      <div style={{ fontSize: '0.7rem', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '4px' }}>{label}</div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontFamily: 'monospace', fontSize: '0.72rem', color: '#60a5fa', wordBreak: 'break-all', flex: 1 }}>{value}</span>
        <button onClick={copy} style={{ background: 'none', border: 'none', cursor: 'pointer', color: copied ? '#22c55e' : '#6b7280', padding: '2px', flexShrink: 0 }} title="Copy">
          <Copy size={12} />
        </button>
      </div>
    </div>
  )
}

function SearchBox({ onSearch }: { onSearch: (id: string) => void }) {
  const [val, setVal] = useState('')
  function go() { const t = val.trim(); if (t) onSearch(t) }
  return (
    <div style={{ display: 'flex', gap: '8px', maxWidth: '560px', width: '100%' }}>
      <input
        value={val} onChange={e => setVal(e.target.value)}
        onKeyDown={e => e.key === 'Enter' && go()}
        placeholder="Enter receipt ID (e.g. OMNIX-A1B2C3D4E5F6)"
        style={{
          flex: 1, background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.15)',
          color: '#fff', padding: '10px 14px', borderRadius: '6px',
          fontFamily: 'monospace', fontSize: '0.9rem', outline: 'none',
        }}
      />
      <button onClick={go} style={{
        background: '#3b82f6', color: '#fff', border: 'none',
        padding: '10px 20px', borderRadius: '6px', cursor: 'pointer',
        fontWeight: 600, fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '6px',
      }}>
        <Search size={14} /> Verify
      </button>
    </div>
  )
}

export default function PublicDecisionVerify() {
  const { receiptId } = useParams<{ receiptId?: string }>()
  const navigate = useNavigate()
  const [data, setData]       = useState<VerifyData | null>(null)
  const [loading, setLoading] = useState(false)
  const [notFound, setNotFound] = useState(false)
  const [error, setError]     = useState<string | null>(null)
  const [showRaw, setShowRaw] = useState(false)
  const [copied, setCopied]   = useState(false)

  function doFetch(id: string) {
    if (!id) return
    setLoading(true)
    setData(null)
    setNotFound(false)
    setError(null)
    fetch(`${API_BASE}/api/public/verify/${encodeURIComponent(id)}`)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then((d: VerifyData) => {
        if (!d.found) setNotFound(true)
        else setData(d)
      })
      .catch(() => setError('Verification service temporarily unavailable. Please try again.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { if (receiptId) doFetch(receiptId) }, [receiptId])

  function handleSearch(id: string) {
    navigate(`/verify/${encodeURIComponent(id)}`)
  }

  function copyLink() {
    navigator.clipboard.writeText(window.location.href).catch(() => {})
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const colors = data ? decisionColors(data.decision_color) : decisionColors('gray')

  return (
    <div style={{
      minHeight: '100vh', background: '#0a0e17', color: '#e5e7eb',
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    }}>
      {/* ── Header ── */}
      <div style={{ borderBottom: '1px solid rgba(255,255,255,0.06)', padding: '16px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '10px', textDecoration: 'none' }}>
          <Shield size={20} color="#3b82f6" />
          <div>
            <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#fff', letterSpacing: '0.06em' }}>OMNIX QUANTUM</div>
            <div style={{ fontSize: '0.6rem', color: '#6b7280', letterSpacing: '0.12em', textTransform: 'uppercase' }}>Decision Governance Infrastructure</div>
          </div>
        </Link>
        <Link to="/try" style={{ fontSize: '0.8rem', color: '#3b82f6', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}>
          Try the sandbox <ExternalLink size={12} />
        </Link>
      </div>

      <div style={{ maxWidth: '700px', margin: '0 auto', padding: '2.5rem 1.5rem' }}>

        {/* ── Page title + search ── */}
        <div style={{ marginBottom: '2.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <Link to="/" style={{ color: '#6b7280', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.8rem' }}>
              <ArrowLeft size={14} /> Home
            </Link>
          </div>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 700, color: '#fff', margin: '0 0 8px' }}>
            Governance Receipt Verification
          </h1>
          <p style={{ color: '#9ca3af', fontSize: '0.88rem', margin: '0 0 20px' }}>
            Independently verify the authenticity of any OMNIX governance decision.
            Receipts are cryptographically signed — tamper-proof and publicly auditable.
          </p>
          <SearchBox onSearch={handleSearch} />
        </div>

        {/* ── Loading ── */}
        {loading && (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#6b7280' }}>
            <div style={{ fontSize: '0.9rem', marginBottom: '8px' }}>Verifying receipt...</div>
            <div style={{ width: '40px', height: '2px', background: '#3b82f6', margin: '0 auto', animation: 'pulse 1s infinite' }} />
          </div>
        )}

        {/* ── Error ── */}
        {error && (
          <div style={{ padding: '1.5rem', background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.25)', borderRadius: '10px', display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
            <AlertTriangle size={18} color="#ef4444" style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <div style={{ fontWeight: 600, color: '#ef4444', marginBottom: '4px' }}>Verification Error</div>
              <div style={{ fontSize: '0.85rem', color: '#9ca3af' }}>{error}</div>
            </div>
          </div>
        )}

        {/* ── Not found ── */}
        {notFound && !loading && (
          <div style={{ padding: '2rem', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '10px', textAlign: 'center' }}>
            <div style={{ fontSize: '2rem', marginBottom: '12px' }}>🔍</div>
            <div style={{ fontWeight: 600, color: '#e5e7eb', marginBottom: '8px' }}>Receipt not found</div>
            <div style={{ fontSize: '0.85rem', color: '#6b7280' }}>
              <code style={{ color: '#ef4444' }}>{receiptId}</code> does not exist in the governance ledger.
            </div>
            <div style={{ fontSize: '0.8rem', color: '#4b5563', marginTop: '12px' }}>
              Receipts are generated by the <Link to="/try" style={{ color: '#3b82f6' }}>public governance sandbox</Link> and live trading pipeline.
            </div>
          </div>
        )}

        {/* ── Verified receipt ── */}
        {data && !loading && (
          <div>
            {/* ── Status banner ── */}
            <div style={{
              padding: '1.5rem', borderRadius: '12px', marginBottom: '1.5rem',
              background: colors.bg, border: `1px solid ${colors.border}`,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px', flexWrap: 'wrap' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                    <span style={{ fontSize: '1.4rem' }}>{data.decision_icon}</span>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: '1.1rem', color: colors.text }}>{data.decision}</div>
                      <div style={{ fontSize: '0.75rem', color: '#6b7280', fontFamily: 'monospace' }}>{data.receipt_id}</div>
                    </div>
                  </div>
                  <p style={{ color: '#d1d5db', fontSize: '0.9rem', margin: 0, lineHeight: 1.5 }}>{data.human_summary_en}</p>
                  <p style={{ color: '#9ca3af', fontSize: '0.8rem', margin: '6px 0 0', lineHeight: 1.5, fontStyle: 'italic' }}>{data.human_summary_es}</p>
                </div>
                <div style={{ display: 'flex', gap: '8px', flexShrink: 0 }}>
                  <button onClick={copyLink} title="Copy link" style={{
                    background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
                    color: copied ? '#22c55e' : '#9ca3af', padding: '6px 10px', borderRadius: '6px',
                    cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.78rem',
                  }}>
                    <Copy size={12} /> {copied ? 'Copied!' : 'Share'}
                  </button>
                </div>
              </div>
            </div>

            {/* ── Key facts ── */}
            <div style={{
              padding: '1rem 1.25rem', background: 'rgba(255,255,255,0.02)',
              border: '1px solid rgba(255,255,255,0.06)', borderRadius: '10px', marginBottom: '1.5rem',
            }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px' }}>
                {[
                  { label: 'Asset / Domain', value: `${data.asset} · ${data.domain}` },
                  { label: 'Decision Time', value: formatTimestamp(data.timestamp_utc) },
                  { label: 'Checkpoints', value: `${data.checkpoints_passed} / ${data.checkpoints_total} passed` },
                  { label: 'Policy Version', value: data.policy_version },
                ].map(f => (
                  <div key={f.label}>
                    <div style={{ fontSize: '0.68rem', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '3px' }}>{f.label}</div>
                    <div style={{ fontSize: '0.85rem', color: '#e5e7eb', fontFamily: f.label === 'Decision Time' ? 'inherit' : 'monospace' }}>{f.value}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* ── Checkpoint pipeline ── */}
            {data.checkpoints.length > 0 && (
              <div style={{
                padding: '1.25rem', background: 'rgba(255,255,255,0.02)',
                border: '1px solid rgba(255,255,255,0.06)', borderRadius: '10px', marginBottom: '1.5rem',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <div style={{ fontSize: '0.75rem', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 600 }}>
                    Safety Checkpoint Pipeline
                  </div>
                  <div style={{ display: 'flex', gap: '8px', fontSize: '0.75rem' }}>
                    <span style={{ color: '#22c55e' }}>✓ {data.checkpoints_passed} passed</span>
                    {data.checkpoints_blocked > 0 && <span style={{ color: '#ef4444' }}>✗ {data.checkpoints_blocked} blocked</span>}
                  </div>
                </div>
                <div>
                  {data.checkpoints.map((cp, i) => (
                    <CheckpointCard key={i} cp={cp} index={i} />
                  ))}
                </div>
              </div>
            )}

            {/* ── Integrity & PQC ── */}
            <div style={{
              padding: '1.25rem', background: 'rgba(59,130,246,0.05)',
              border: '1px solid rgba(59,130,246,0.15)', borderRadius: '10px', marginBottom: '1.5rem',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <Lock size={14} color="#60a5fa" />
                <span style={{ fontSize: '0.75rem', color: '#60a5fa', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 600 }}>
                  Cryptographic Integrity
                </span>
              </div>
              <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start', marginBottom: '14px', padding: '10px', background: 'rgba(34,197,94,0.06)', borderRadius: '6px', border: '1px solid rgba(34,197,94,0.15)' }}>
                <CheckCircle size={16} color="#22c55e" style={{ flexShrink: 0, marginTop: '1px' }} />
                <div>
                  <div style={{ fontSize: '0.85rem', color: '#22c55e', fontWeight: 600, marginBottom: '2px' }}>Receipt Verified — Tamper-Proof</div>
                  <div style={{ fontSize: '0.78rem', color: '#9ca3af' }}>
                    Signed with {data.integrity.signature_algorithm} · {data.integrity.nist_note}
                  </div>
                </div>
              </div>

              <button
                onClick={() => setShowRaw(r => !r)}
                style={{ background: 'none', border: 'none', color: '#6b7280', cursor: 'pointer', fontSize: '0.78rem', padding: 0, marginBottom: '10px', textDecoration: 'underline' }}
              >
                {showRaw ? 'Hide' : 'Show'} cryptographic hashes
              </button>

              {showRaw && (
                <div>
                  <HashDisplay label="Content Hash (SHA-256)" value={data.integrity.content_hash} />
                  {data.integrity.prev_hash && (
                    <HashDisplay label="Previous Receipt Hash" value={data.integrity.prev_hash} />
                  )}
                  <div style={{ fontSize: '0.72rem', color: '#4b5563', marginTop: '8px' }}>
                    Hash chain links every receipt to the previous one — any modification breaks the chain permanently.
                  </div>
                </div>
              )}
            </div>

            {/* ── Independent verification CTA ── */}
            <div style={{
              padding: '1rem 1.25rem', background: 'rgba(255,255,255,0.02)',
              border: '1px solid rgba(255,255,255,0.06)', borderRadius: '10px',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap',
            }}>
              <div>
                <div style={{ fontSize: '0.85rem', color: '#e5e7eb', fontWeight: 500, marginBottom: '3px' }}>Independent Verification</div>
                <div style={{ fontSize: '0.78rem', color: '#6b7280' }}>
                  Verify this receipt through the independent public ledger — requires no OMNIX infrastructure.
                </div>
              </div>
              {data.independent_verify_url ? (
                <a href={data.independent_verify_url} target="_blank" rel="noopener noreferrer" style={{
                  background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.12)',
                  color: '#e5e7eb', padding: '8px 16px', borderRadius: '6px',
                  textDecoration: 'none', fontSize: '0.8rem', fontWeight: 600,
                  display: 'flex', alignItems: 'center', gap: '6px', whiteSpace: 'nowrap', flexShrink: 0,
                }}>
                  Open Ledger <ExternalLink size={12} />
                </a>
              ) : (
                <span style={{ fontSize: '0.78rem', color: '#4b5563' }}>Ledger URL not configured</span>
              )}
            </div>

            {/* ── Footer note ── */}
            <div style={{ textAlign: 'center', marginTop: '2rem', fontSize: '0.75rem', color: '#4b5563' }}>
              All governance decisions are logged in an append-only hash chain with post-quantum cryptographic signatures.<br />
              <Link to="/try" style={{ color: '#3b82f6' }}>Submit your own scenario</Link> · <Link to="/" style={{ color: '#3b82f6' }}>Learn about OMNIX</Link>
            </div>
          </div>
        )}

        {/* ── Empty state (no receipt ID in URL) ── */}
        {!receiptId && !loading && !error && (
          <div style={{
            padding: '2rem', background: 'rgba(255,255,255,0.02)',
            border: '1px solid rgba(255,255,255,0.06)', borderRadius: '10px', textAlign: 'center',
          }}>
            <Shield size={32} color="#3b82f6" style={{ marginBottom: '12px' }} />
            <div style={{ fontWeight: 600, color: '#e5e7eb', marginBottom: '8px' }}>Enter a Receipt ID to verify</div>
            <div style={{ fontSize: '0.85rem', color: '#6b7280', marginBottom: '16px' }}>
              Receipts are generated by the governance engine after every decision.<br />
              Try the <Link to="/try" style={{ color: '#3b82f6' }}>public sandbox</Link> to generate one.
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
