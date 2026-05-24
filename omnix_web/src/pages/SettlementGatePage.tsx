import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

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
const BLUE         = '#3b82f6'
const AMBER        = '#f59e0b'
const SLATE        = '#64748b'
const TEXT         = '#e2e8f0'
const MUTED        = '#94a3b8'
const PURPLE       = '#a78bfa'

const API = (import.meta.env.VITE_RAILWAY_API_URL || '').replace(/\/$/, '')

// ── Types ─────────────────────────────────────────────────────────────────────

interface ManifestData {
  module: string
  product_id: string
  invariants: Record<string, string>
  supported_ledgers: string[]
  registry_stats: {
    total: number
    approved: number
    rejected: number
    orgs: number
  }
  upstream_components: string[]
}

// ── Shared components ─────────────────────────────────────────────────────────
function GateIcon({ size = 36 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 36 36">
      <rect x="2" y="8" width="32" height="20" rx="4" fill={GOLD_DIM} stroke={GOLD} strokeWidth="1.5" />
      <rect x="14" y="8" width="8" height="20" fill={GOLD_DIM} stroke={GOLD} strokeWidth="1" />
      <circle cx="18" cy="18" r="3" fill={GOLD} />
      <line x1="2" y1="18" x2="10" y2="18" stroke={GOLD} strokeWidth="2" />
      <line x1="26" y1="18" x2="34" y2="18" stroke={GOLD} strokeWidth="2" />
    </svg>
  )
}


function InvariantChip({ id, desc }: { id: string; desc: string }) {
  return (
    <div style={{
      background: GOLD_DIM, border: `1px solid ${GOLD_BORDER}`,
      borderRadius: 8, padding: '10px 14px',
    }}>
      <div style={{ fontFamily: 'monospace', fontSize: 10, color: GOLD, fontWeight: 700 }}>{id}</div>
      <div style={{ fontSize: 11, color: MUTED, marginTop: 3 }}>{desc}</div>
    </div>
  )
}

function StatBox({ icon, label, value, sub }: { icon: string; label: string; value: string; sub?: string }) {
  return (
    <div style={{
      background: NAVY2, border: `1px solid ${GOLD_BORDER}`,
      borderRadius: 10, padding: '16px 18px', flex: 1, minWidth: 130,
    }}>
      <div style={{ fontSize: 20, marginBottom: 6 }}>{icon}</div>
      <div style={{ fontSize: 22, fontWeight: 700, color: GOLD, fontFamily: 'monospace' }}>{value}</div>
      <div style={{ fontSize: 11, color: TEXT, marginTop: 2 }}>{label}</div>
      {sub && <div style={{ fontSize: 10, color: SLATE, marginTop: 3 }}>{sub}</div>}
    </div>
  )
}


// ── Validate demo panel ───────────────────────────────────────────────────────
function ValidatePanel() {
  const [pogcId,   setPogcId]   = useState('')
  const [ledger,   setLedger]   = useState('XRPL')
  const [currency, setCurrency] = useState('RLUSD')
  const [amount,   setAmount]   = useState('')
  const [apiKey,   setApiKey]   = useState('')
  const [loading,  setLoading]  = useState(false)
  const [result,   setResult]   = useState<any>(null)
  const [error,    setError]    = useState('')

  async function run() {
    if (!pogcId.trim()) { setError('POGC-ID is required'); return }
    if (!apiKey.trim()) { setError('API key required'); return }
    setLoading(true); setError(''); setResult(null)
    try {
      const body: any = {
        pogc_id: pogcId.trim(),
        settlement_ledger: ledger,
        settlement_currency: currency,
      }
      if (amount) body.settlement_amount = parseFloat(amount)
      const r = await fetch(`${API}/v1/osg/validate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-API-Key': apiKey },
        body: JSON.stringify(body),
      })
      setResult(await r.json())
    } catch { setError('Gateway unreachable — try again') }
    finally { setLoading(false) }
  }

  const vr = result?.validation_receipt
  const approved = result?.status === 'APPROVED'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Inputs */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 5, gridColumn: '1/-1' }}>
          <label style={{ fontSize: 11, color: MUTED }}>POGC-ID</label>
          <input value={pogcId} onChange={e => setPogcId(e.target.value)}
            placeholder="POGC-A3F2B1C4D5E6F7A8"
            style={{ padding: '10px 14px', background: NAVY3, border: `1px solid ${GOLD_BORDER}`, borderRadius: 8, color: TEXT, fontSize: 12, fontFamily: 'monospace', outline: 'none' }} />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
          <label style={{ fontSize: 11, color: MUTED }}>Settlement Ledger</label>
          <select value={ledger} onChange={e => setLedger(e.target.value)}
            style={{ padding: '10px 14px', background: NAVY3, border: `1px solid ${GOLD_BORDER}`, borderRadius: 8, color: TEXT, fontSize: 12, outline: 'none' }}>
            {['XRPL','ETH','SWIFT','FIX','OTHER'].map(l => <option key={l}>{l}</option>)}
          </select>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
          <label style={{ fontSize: 11, color: MUTED }}>Currency</label>
          <input value={currency} onChange={e => setCurrency(e.target.value.toUpperCase())}
            placeholder="RLUSD"
            style={{ padding: '10px 14px', background: NAVY3, border: `1px solid ${GOLD_BORDER}`, borderRadius: 8, color: TEXT, fontSize: 12, fontFamily: 'monospace', outline: 'none' }} />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
          <label style={{ fontSize: 11, color: MUTED }}>Amount (optional)</label>
          <input value={amount} onChange={e => setAmount(e.target.value)} type="number"
            placeholder="125000"
            style={{ padding: '10px 14px', background: NAVY3, border: `1px solid ${GOLD_BORDER}`, borderRadius: 8, color: TEXT, fontSize: 12, fontFamily: 'monospace', outline: 'none' }} />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 5, gridColumn: '1/-1' }}>
          <label style={{ fontSize: 11, color: MUTED }}>API Key</label>
          <input value={apiKey} onChange={e => setApiKey(e.target.value)} type="password"
            placeholder="Your OMNIX B2B API key"
            style={{ padding: '10px 14px', background: NAVY3, border: `1px solid ${GOLD_BORDER}`, borderRadius: 8, color: TEXT, fontSize: 12, fontFamily: 'monospace', outline: 'none' }} />
        </div>
      </div>

      {error && <div style={{ padding: '10px 14px', background: RED_DIM, border: `1px solid ${RED_BORDER}`, borderRadius: 8, fontSize: 12, color: RED }}>{error}</div>}

      <button onClick={run} disabled={loading} style={{
        padding: '12px', background: loading ? GOLD_DIM : GOLD,
        color: loading ? GOLD : NAVY, border: 'none', borderRadius: 8,
        fontSize: 13, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer',
      }}>
        {loading ? 'Validating…' : 'Validate Settlement →'}
      </button>

      {result && vr && (
        <div style={{
          background: approved ? GREEN_DIM : RED_DIM,
          border: `1.5px solid ${approved ? GREEN_BORDER : RED_BORDER}`,
          borderRadius: 12, padding: 22,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
            <span style={{ fontSize: 28 }}>{approved ? '✅' : '❌'}</span>
            <div>
              <div style={{ fontSize: 16, fontWeight: 700, color: approved ? GREEN : RED }}>
                {approved ? 'Settlement APPROVED' : 'Settlement REJECTED'}
              </div>
              <div style={{ fontFamily: 'monospace', fontSize: 11, color: SLATE }}>{vr.vr_id}</div>
            </div>
          </div>
          {!approved && vr.reject_reason && (
            <div style={{ marginBottom: 14, padding: '8px 12px', background: 'rgba(0,0,0,0.2)', borderRadius: 7, fontSize: 12, color: RED, fontFamily: 'monospace' }}>
              {vr.reject_reason} · {vr.reject_invariant}
            </div>
          )}
          {approved && vr.invariants_checked && (
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 14 }}>
              {vr.invariants_checked.map((i: string) => (
                <span key={i} style={{ fontSize: 10, fontFamily: 'monospace', color: GREEN, background: GREEN_DIM, border: `1px solid ${GREEN_BORDER}`, borderRadius: 4, padding: '2px 8px' }}>{i} ✓</span>
              ))}
            </div>
          )}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 8, padding: '10px 14px' }}>
              <div style={{ fontSize: 9, color: SLATE, marginBottom: 4 }}>Content Hash (SHA3-256)</div>
              <div style={{ fontFamily: 'monospace', fontSize: 10, color: MUTED, wordBreak: 'break-all' }}>{vr.content_hash}</div>
            </div>
            {approved && (
              <div style={{ fontSize: 11, color: MUTED, textAlign: 'right' }}>
                Include <span style={{ color: GOLD, fontFamily: 'monospace' }}>{vr.vr_id}</span> in your settlement transaction metadata
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function SettlementGatePage() {
  const navigate = useNavigate()
  const [tab, setTab] = useState<'overview'|'validate'|'flow'|'compare'>('overview')
  const [manifest, setManifest] = useState<ManifestData | null>(null)

  useEffect(() => {
    fetch(`${API}/v1/osg/manifest`).then(r => r.json()).then(setManifest).catch(() => {})
  }, [])

  const tabStyle = (active: boolean) => ({
    padding: '8px 20px', borderRadius: 8,
    background: active ? GOLD_DIM : 'transparent',
    border: `1px solid ${active ? GOLD_BORDER : 'transparent'}`,
    color: active ? GOLD : SLATE,
    fontSize: 13, fontWeight: active ? 600 : 400,
    cursor: 'pointer', transition: 'all 0.15s',
  })

  return (
    <div style={{ minHeight: '100vh', background: NAVY, color: TEXT, fontFamily: 'system-ui, sans-serif' }}>
      {/* Nav */}
      <div style={{
        borderBottom: `1px solid ${GOLD_BORDER}`, background: `${NAVY}ee`,
        position: 'sticky', top: 0, zIndex: 100, backdropFilter: 'blur(12px)',
      }}>
        <div style={{ maxWidth: 1100, margin: '0 auto', padding: '0 24px', display: 'flex', alignItems: 'center', height: 60, gap: 14 }}>
          <button onClick={() => navigate('/')} style={{ background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 10 }}>
            <GateIcon size={24} />
            <span style={{ fontFamily: 'monospace', fontSize: 13, color: GOLD, fontWeight: 700 }}>OMNIX QUANTUM</span>
          </button>
          <span style={{ color: GOLD_BORDER, fontSize: 18 }}>›</span>
          <span style={{ fontSize: 13, color: MUTED }}>Settlement Gate</span>
          <div style={{ flex: 1 }} />
          {manifest?.registry_stats && (
            <div style={{ display: 'flex', gap: 16, fontSize: 11, fontFamily: 'monospace', color: SLATE }}>
              <span style={{ color: GREEN }}>{manifest.registry_stats.approved} approved</span>
              <span>{manifest.registry_stats.total} total</span>
            </div>
          )}
          <button onClick={() => navigate('/proof-of-governance')} style={{
            padding: '6px 14px', background: GOLD_DIM, border: `1px solid ${GOLD_BORDER}`,
            borderRadius: 7, color: GOLD, fontSize: 11, fontFamily: 'monospace', cursor: 'pointer',
          }}>PoGR Registry →</button>
        </div>
      </div>

      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '40px 24px' }}>

        {/* Hero */}
        <div style={{ textAlign: 'center', marginBottom: 44 }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 18 }}>
            <GateIcon size={56} />
          </div>
          <h1 style={{ fontSize: 'clamp(28px,5vw,42px)', fontWeight: 800, color: TEXT, margin: 0, lineHeight: 1.15, letterSpacing: '-0.02em' }}>
            OMNIX Settlement Gate
          </h1>
          <p style={{ fontSize: 16, color: MUTED, marginTop: 12, maxWidth: 580, margin: '12px auto 0', lineHeight: 1.6 }}>
            The world's first commitment-time enforcement layer for AI governance.
            No PoGC, no settlement — on any ledger.
          </p>

          {/* Pills */}
          <div style={{ display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap', marginTop: 22 }}>
            {[
              ['⚡', 'Fail-Closed · OSG-INV-001'],
              ['⬡', 'ML-DSA-65 · FIPS 204'],
              ['🌐', 'XRPL · ETH · SWIFT · FIX'],
              ['🔗', 'Intent → Governance → Settlement'],
            ].map(([icon, label]) => (
              <div key={label} style={{
                display: 'flex', alignItems: 'center', gap: 7,
                background: NAVY2, border: `1px solid ${GOLD_BORDER}`,
                borderRadius: 20, padding: '6px 14px', fontSize: 11.5, color: TEXT,
              }}>
                <span>{icon}</span>
                <span style={{ fontFamily: 'monospace' }}>{label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Stats */}
        {manifest && (
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 40 }}>
            <StatBox icon="✅" label="Approved" value={String(manifest.registry_stats.approved)} sub="Settlements cleared" />
            <StatBox icon="🌐" label="Ledgers" value={String(manifest.supported_ledgers.length)} sub="XRPL · ETH · SWIFT · FIX" />
            <StatBox icon="🏢" label="Organizations" value={String(manifest.registry_stats.orgs)} sub="Integrated" />
            <StatBox icon="🔗" label="Upstream Stack" value={String(manifest.upstream_components.length)} sub="ATF · OGR · PoGR" />
          </div>
        )}

        {/* Tabs */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 28, flexWrap: 'wrap' }}>
          <button style={tabStyle(tab === 'overview')}  onClick={() => setTab('overview')}>Overview</button>
          <button style={tabStyle(tab === 'validate')}  onClick={() => setTab('validate')}>Validate Settlement</button>
          <button style={tabStyle(tab === 'flow')}      onClick={() => setTab('flow')}>How It Works</button>
          <button style={tabStyle(tab === 'compare')}   onClick={() => setTab('compare')}>vs. Competition</button>
        </div>

        {/* ── Overview ── */}
        {tab === 'overview' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

            {/* What */}
            <div style={{ background: NAVY2, border: `1px solid ${GOLD_BORDER}`, borderRadius: 12, padding: 28 }}>
              <h2 style={{ fontSize: 17, fontWeight: 700, color: GOLD, margin: '0 0 14px' }}>
                The Commitment-Time Enforcement Problem
              </h2>
              <p style={{ fontSize: 14, color: MUTED, lineHeight: 1.75, margin: 0 }}>
                OMNIX already proves <em>who had authority</em> (ATF), <em>what the agent did</em> (OGR + BEV),
                and <em>that governance was correct</em> (PoGR). The missing piece:
                enforcing that the downstream consequence — a financial settlement, a contract execution,
                a liquidity commitment — cannot happen unless that proof exists.
              </p>
              <p style={{ fontSize: 14, color: MUTED, lineHeight: 1.75, marginTop: 12, marginBottom: 0 }}>
                The Settlement Gate is that enforcement point. It sits between your governance proof
                and your ledger. No PoGC means the gate rejects — fail-closed, every time, on any ledger.
              </p>
            </div>

            {/* Invariants */}
            <div>
              <h2 style={{ fontSize: 16, fontWeight: 700, color: TEXT, margin: '0 0 14px' }}>Six Formal Invariants</h2>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px,1fr))', gap: 10 }}>
                {manifest?.invariants
                  ? Object.entries(manifest.invariants).map(([id, desc]) => <InvariantChip key={id} id={id} desc={desc} />)
                  : [
                    ['OSG-INV-001', 'Fail-closed — absence of valid PoGC = REJECTED, never silently approved'],
                    ['OSG-INV-002', 'Append-only ValidationReceipts — no DELETE, no UPDATE on core fields'],
                    ['OSG-INV-003', 'Offline verifiability — VR + public key only, zero platform access required'],
                    ['OSG-INV-004', 'TTL coverage — PoGC must not expire before settlement_deadline'],
                    ['OSG-INV-005', 'Ledger agnosticism — XRPL · ETH · SWIFT · FIX · OTHER'],
                    ['OSG-INV-006', 'Complete audit chain — intent → governance → proof → settlement'],
                  ].map(([id, desc]) => <InvariantChip key={id} id={id} desc={desc as string} />)
                }
              </div>
            </div>

            {/* API reference */}
            <div style={{ background: NAVY2, border: `1px solid ${GOLD_BORDER}`, borderRadius: 12, padding: 28 }}>
              <h2 style={{ fontSize: 16, fontWeight: 700, color: TEXT, margin: '0 0 16px' }}>API Reference</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {[
                  ['POST', '/v1/osg/validate',              '🔒', 'Main gate — validate settlement against PoGC'],
                  ['POST', '/v1/osg/anchor',                '🔒', 'Pre-anchor settlement to PoGC before execution'],
                  ['GET',  '/v1/osg/validation/{vr_id}',   '🌐', 'Public VR retrieval — OSG-INV-003 zero-auth'],
                  ['GET',  '/v1/osg/settlement/{tx_hash}', '🔒', 'Look up VR by settlement transaction hash'],
                  ['GET',  '/v1/osg/organization/{id}',    '🔒', 'Validation history for your organization'],
                  ['GET',  '/v1/osg/manifest',             '🌐', 'Module manifest + registry stats'],
                ].map(([method, path, auth, desc]) => (
                  <div key={path} style={{ display: 'flex', gap: 12, alignItems: 'center', background: NAVY3, borderRadius: 8, padding: '10px 14px' }}>
                    <span style={{ fontFamily: 'monospace', fontSize: 10, color: method === 'POST' ? AMBER : BLUE, minWidth: 36 }}>{method}</span>
                    <span style={{ fontFamily: 'monospace', fontSize: 11, color: TEXT, flex: 1 }}>{path}</span>
                    <span style={{ fontSize: 13 }}>{auth}</span>
                    <span style={{ fontSize: 11, color: SLATE }}>{desc}</span>
                  </div>
                ))}
              </div>
              <div style={{ fontSize: 11, color: SLATE, marginTop: 12 }}>🔒 API Key · 🌐 Public (PoGR-INV-003 / OSG-INV-003)</div>
            </div>

            {/* CTA */}
            <div style={{ background: GOLD_DIM, border: `1.5px solid ${GOLD_BORDER}`, borderRadius: 12, padding: 28, textAlign: 'center' }}>
              <div style={{ fontSize: 17, fontWeight: 700, color: GOLD, marginBottom: 8 }}>Complete the chain</div>
              <div style={{ fontSize: 13, color: MUTED, marginBottom: 20, maxWidth: 440, margin: '8px auto 20px' }}>
                Govern a session with OGR → issue a PoGC → validate every settlement through the Gate.
                One immutable audit trail from human intent to on-chain consequence.
              </div>
              <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
                <button onClick={() => setTab('validate')} style={{ background: GOLD, color: NAVY, border: 'none', borderRadius: 8, padding: '11px 24px', fontSize: 13, fontWeight: 700, cursor: 'pointer' }}>
                  Try Validate →
                </button>
                <button onClick={() => navigate('/governance-api')} style={{ background: 'transparent', color: GOLD, border: `1px solid ${GOLD_BORDER}`, borderRadius: 8, padding: '11px 24px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>
                  Governance API
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── Validate ── */}
        {tab === 'validate' && (
          <div style={{ maxWidth: 640 }}>
            <div style={{ background: NAVY2, border: `1px solid ${GOLD_BORDER}`, borderRadius: 12, padding: 28 }}>
              <h2 style={{ fontSize: 16, fontWeight: 700, color: TEXT, margin: '0 0 6px' }}>Validate a Settlement</h2>
              <div style={{ fontSize: 12, color: SLATE, marginBottom: 20 }}>
                OSG-INV-001 — fail-closed. If the PoGC is missing, invalid, or expired: REJECTED.
              </div>
              <ValidatePanel />
            </div>
          </div>
        )}

        {/* ── How It Works ── */}
        {tab === 'flow' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

            {/* Flow diagram */}
            <div style={{ background: NAVY2, border: `1px solid ${GOLD_BORDER}`, borderRadius: 12, padding: 28 }}>
              <h2 style={{ fontSize: 16, fontWeight: 700, color: TEXT, margin: '0 0 22px' }}>
                From Human Intent to Settlement — One Chain
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
                {[
                  { step: '01', color: BLUE,   icon: '👤', title: 'Human Delegation',        desc: 'Human principal delegates to AI agent — ATF DR issued, signed ML-DSA-65. A_child ≤ A_parent enforced.', tag: 'ATF · ADR-156' },
                  { step: '02', color: PURPLE, icon: '🤖', title: 'Governed Execution',       desc: 'Agent executes under OGR session. Every turn produces BAR + CCS. Hash chain links all turns (CTCHC).', tag: 'OGR · ADR-184' },
                  { step: '03', color: AMBER,  icon: '🔒', title: 'Session Sealed',           desc: 'OGR session closes and seals. CTCHC seal hash computed. Session status → SEALED.', tag: 'OGR · ADR-183' },
                  { step: '04', color: GOLD,   icon: '⬡',  title: 'PoGC Issued',             desc: 'POST /v1/pogr/certify — PoG Certificate emitted. Publicly verifiable. Registered in append-only ledger.', tag: 'PoGR · ADR-186' },
                  { step: '05', color: GREEN,  icon: '⚡', title: 'Settlement Gate',           desc: 'POST /v1/osg/validate — gate checks PoGC validity. APPROVED → VR issued. REJECTED → settlement blocked.', tag: 'OSG · ADR-188' },
                  { step: '06', color: GREEN,  icon: '🏦', title: 'Settlement Executed',      desc: 'Settlement includes vr_id in transaction metadata. Counterparty/ledger can verify VR offline.', tag: 'Ledger · XRPL · ETH · SWIFT' },
                ].map((item, i, arr) => (
                  <div key={item.step} style={{ display: 'flex', gap: 0 }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginRight: 18 }}>
                      <div style={{
                        width: 36, height: 36, borderRadius: '50%',
                        background: `${item.color}18`, border: `1.5px solid ${item.color}`,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: 14, flexShrink: 0,
                      }}>{item.icon}</div>
                      {i < arr.length - 1 && <div style={{ width: 2, flex: 1, background: GOLD_BORDER, minHeight: 24, margin: '4px 0' }} />}
                    </div>
                    <div style={{ paddingBottom: i < arr.length - 1 ? 20 : 0 }}>
                      <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 4 }}>
                        <span style={{ fontFamily: 'monospace', fontSize: 10, color: item.color, fontWeight: 700 }}>{item.step}</span>
                        <span style={{ fontSize: 13, fontWeight: 600, color: TEXT }}>{item.title}</span>
                        <span style={{ fontSize: 9, fontFamily: 'monospace', color: SLATE, background: NAVY3, borderRadius: 4, padding: '2px 7px' }}>{item.tag}</span>
                      </div>
                      <div style={{ fontSize: 12, color: SLATE, lineHeight: 1.65 }}>{item.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Anchor flow */}
            <div style={{ background: NAVY2, border: `1px solid ${GOLD_BORDER}`, borderRadius: 12, padding: 28 }}>
              <h2 style={{ fontSize: 16, fontWeight: 700, color: TEXT, margin: '0 0 14px' }}>
                Pre-Anchor Flow — For High-Value Settlements
              </h2>
              <p style={{ fontSize: 13, color: MUTED, lineHeight: 1.7, margin: 0 }}>
                For high-value or time-sensitive settlements, use <span style={{ fontFamily: 'monospace', color: GOLD }}>POST /v1/osg/anchor</span> before
                submitting to the ledger. The VR is issued immediately — include the <span style={{ fontFamily: 'monospace', color: TEXT }}>vr_id</span> in
                the transaction metadata. Post-execution, call <span style={{ fontFamily: 'monospace', color: GOLD }}>GET /v1/osg/settlement/{'{tx_hash}'}</span> to
                close the loop and confirm the VR matches the on-chain transaction.
              </p>
            </div>
          </div>
        )}

        {/* ── Compare ── */}
        {tab === 'compare' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div style={{ background: NAVY2, border: `1px solid ${GOLD_BORDER}`, borderRadius: 12, padding: 28 }}>
              <h2 style={{ fontSize: 16, fontWeight: 700, color: TEXT, margin: '0 0 20px' }}>
                OMNIX OSG vs. Commitment-Time Alternatives
              </h2>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                  <thead>
                    <tr>
                      {['Dimension', 'Third-Party Settlement Layer', 'OMNIX Settlement Gate'].map((h, i) => (
                        <th key={h} style={{
                          padding: '10px 14px', textAlign: 'left',
                          borderBottom: `1px solid ${GOLD_BORDER}`,
                          color: i === 2 ? GOLD : MUTED, fontWeight: i === 2 ? 700 : 500,
                          fontSize: 12,
                        }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      ['Upstream governance layer',  '❌ Starts at commitment',             '✅ ATF → OGR → PoGC → Gate'],
                      ['Supported ledgers',          'XRPL only',                          '✅ XRPL · ETH · SWIFT · FIX · Any'],
                      ['Settlement currency',        'RLUSD',                              '✅ Any (currency-agnostic)'],
                      ['Offline verifiability',      '❓ Unknown',                          '✅ OSG-INV-003 — VR + public key only'],
                      ['Post-quantum signing',       '❓ Unknown',                          '✅ ML-DSA-65 · FIPS 204'],
                      ['Public registry',            '❓ Unknown',                          '✅ PoGR + VR public append-only'],
                      ['Full audit chain',           'Settlement → cert',                  '✅ Intent → governance → proof → settlement'],
                      ['Published standards',        '❌ None',                             '✅ RFC-ATF-1/2/3 · 6 permanent DOIs'],
                      ['Formal invariants',          '❌ None published',                   '✅ OSG-INV-001–006 (ADR-188)'],
                      ['Fail-closed enforcement',    '❓ Unknown',                          '✅ OSG-INV-001 — no silent approvals'],
                    ].map(([dim, other, omnix]) => (
                      <tr key={dim} style={{ borderBottom: `1px solid rgba(201,162,39,0.07)` }}>
                        <td style={{ padding: '10px 14px', color: TEXT, fontWeight: 600 }}>{dim}</td>
                        <td style={{ padding: '10px 14px', color: SLATE }}>{other}</td>
                        <td style={{ padding: '10px 14px', color: TEXT }}>{omnix}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div style={{ background: GOLD_DIM, border: `1.5px solid ${GOLD_BORDER}`, borderRadius: 12, padding: 24, textAlign: 'center' }}>
              <div style={{ fontSize: 14, color: GOLD, fontWeight: 700, marginBottom: 6 }}>
                Own the complete chain. Not just a piece of it.
              </div>
              <div style={{ fontSize: 12, color: MUTED }}>
                Composing with a third-party settlement layer severs the forensic chain at the most critical juncture —
                the point where governance binds consequence. OMNIX OSG closes that gap.
              </div>
            </div>
          </div>
        )}

      </div>

      {/* Footer */}
      <div style={{ borderTop: `1px solid ${GOLD_BORDER}`, marginTop: 60, padding: 24, textAlign: 'center' }}>
        <div style={{ fontSize: 11, color: SLATE, fontFamily: 'monospace' }}>
          OMNIX QUANTUM LTD · ADR-188 · OMNIX-OSG-2026-001 ·
          {' '}<span style={{ color: GREEN }}>OSG-INV-001–006 active</span>
          {' '}· Upstream: ATF · OGR · PoGR
        </div>
      </div>
    </div>
  )
}
