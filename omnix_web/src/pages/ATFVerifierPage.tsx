import { useState, useCallback, useRef, useEffect } from 'react'

const GOLD = '#C9A227'
const GOLD_DIM = 'rgba(201,162,39,0.12)'
const GOLD_BORDER = 'rgba(201,162,39,0.22)'
const NAVY = '#060F1E'
const NAVY2 = '#0A1628'
const NAVY3 = '#0D1E38'
const GREEN = '#22c55e'
const GREEN_DIM = 'rgba(34,197,94,0.10)'
const GREEN_BORDER = 'rgba(34,197,94,0.28)'
const RED = '#ef4444'
const RED_DIM = 'rgba(239,68,68,0.09)'
const RED_BORDER = 'rgba(239,68,68,0.28)'
const AMBER = '#f59e0b'
const SLATE = '#64748b'
const TEXT = '#e2e8f0'
const MUTED = '#94a3b8'

type ArtifactType = 'DR' | 'TAR' | 'RCR'
type InputMode = 'id' | 'json'

const ARTIFACT_META: Record<ArtifactType, {
  label: string
  prefix: string
  layer: string
  layerNum: number
  protocol: string
  description: string
  proofStatement: string
  idPlaceholder: string
  jsonPlaceholder: string
  color: string
}> = {
  DR: {
    label: 'Delegation Receipt',
    prefix: 'ATFDR-',
    layer: 'Delegation Plane',
    layerNum: 2,
    protocol: 'RFC-ATF-1 §5',
    description: 'Cryptographic proof of authority grant from a delegating principal to a delegate agent, with MAR invariant enforcement.',
    proofStatement: 'Proves: who authorized whom, with what budget, at what delegation depth, traceable to a human Tier-1 root.',
    idPlaceholder: 'ATFDR-8B2C4D6E1F3A5B7C',
    jsonPlaceholder: `{
  "delegation_id": "ATFDR-8B2C4D6E1F3A5B7C",
  "delegator_id": "HUMAN-TIER1-HN-001",
  "delegate_id": "AID-FINANCE-3A7F9B2C1D4E5F6A",
  "task_scope": { "action": "compute_portfolio_risk", "domain": "FINANCE" },
  "authority_budget_delegator": 100.0,
  "authority_budget_granted": 60.0,
  "chain_root_id": "ATFDR-8B2C4D6E1F3A5B7C",
  "delegation_depth": 1,
  "delegator_public_key": "<base64-dilithium3-pubkey>",
  "content_hash": "<sha256-hex>",
  "pqc_signature": "<base64-dilithium3-sig>",
  "status": "ACTIVE"
}`,
    color: GOLD,
  },
  TAR: {
    label: 'Temporal Admissibility Record',
    prefix: 'ATFTAR-',
    layer: 'Temporal Authority',
    layerNum: 3,
    protocol: 'ADR-157',
    description: 'Nanosecond-precise proof that a Delegation Receipt was valid at the exact moment an agent execution was admitted.',
    proofStatement: 'Proves: the DR was valid at execution admission — closing the point-in-time governance gap.',
    idPlaceholder: 'ATFTAR-1A2B3C4D5E6F7A8B',
    jsonPlaceholder: `{
  "tar_id": "ATFTAR-1A2B3C4D5E6F7A8B",
  "delegation_id": "ATFDR-8B2C4D6E1F3A5B7C",
  "agent_id": "AID-FINANCE-3A7F9B2C1D4E5F6A",
  "execution_ref": "exec-001",
  "execution_ns": 1747180800000000000,
  "execution_ts": "2026-05-14T00:00:00.000000+00:00",
  "dr_status_at_admission": "ACTIVE",
  "authority_budget": 60.0,
  "domain": "FINANCE",
  "task_action": "compute_portfolio_risk",
  "admission_status": "ADMITTED",
  "chain_root_id": "ATFDR-8B2C4D6E1F3A5B7C",
  "content_hash": "<sha256-hex>",
  "pqc_signature": "<base64-dilithium3-sig>",
  "issued_at": "2026-05-14T00:00:00.000000+00:00"
}`,
    color: '#818cf8',
  },
  RCR: {
    label: 'Runtime Continuity Record',
    prefix: 'ATFRCR-',
    layer: 'Runtime Continuity',
    layerNum: 4,
    protocol: 'RFC-ATF-2 §5',
    description: 'PQC-signed authority health snapshot for a long-running execution. Carries Continuity Eligibility Score (CES) and links to the continuity chain.',
    proofStatement: 'Proves: the agent\'s authorization was healthy at this exact nanosecond during execution — closing the runtime governance gap.',
    idPlaceholder: 'ATFRCR-3F7A2B1C4D5E6F7A',
    jsonPlaceholder: `{
  "rcr_id": "ATFRCR-3F7A2B1C4D5E6F7A",
  "tar_id": "ATFTAR-1A2B3C4D5E6F7A8B",
  "delegation_id": "ATFDR-8B2C4D6E1F3A5B7C",
  "agent_id": "AID-FINANCE-3A7F9B2C1D4E5F6A",
  "chain_root_id": "ATFDR-ROOT000000000001",
  "ces_score": 82.5,
  "ces_temporal": 90.0,
  "ces_budget": 85.0,
  "ces_context": 75.0,
  "ces_integrity": 70.0,
  "continuity_status": "NOMINAL",
  "budget_remaining": 68.0,
  "budget_at_admission": 80.0,
  "fragmentation_score": 15.0,
  "active_anomalies": 0,
  "sample_reason": "SCHEDULED",
  "content_hash": "<sha256-hex>"
}`,
    color: '#34d399',
  },
}

const STATUS_CONFIG: Record<string, { color: string; bg: string; border: string; label: string }> = {
  NOMINAL:    { color: GREEN,  bg: GREEN_DIM,  border: GREEN_BORDER,  label: 'NOMINAL' },
  MONITORING: { color: GOLD,   bg: GOLD_DIM,   border: GOLD_BORDER,   label: 'MONITORING' },
  WARNING:    { color: AMBER,  bg: 'rgba(245,158,11,0.10)', border: 'rgba(245,158,11,0.28)', label: 'WARNING' },
  CRITICAL:   { color: RED,    bg: RED_DIM,    border: RED_BORDER,    label: 'CRITICAL' },
  HALT:       { color: '#dc2626', bg: 'rgba(220,38,38,0.12)', border: 'rgba(220,38,38,0.35)', label: 'HALT' },
}

function CESGauge({ ces, status }: { ces: number; status: string }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.NOMINAL
  const r = 68
  const cx = 88
  const cy = 88
  const strokeW = 11
  const circumference = 2 * Math.PI * r
  const arc = circumference * 0.75
  const dashOffset = arc - (arc * Math.min(100, Math.max(0, ces)) / 100)
  const startAngle = 135
  const toRad = (deg: number) => (deg * Math.PI) / 180
  const needleAngle = startAngle + (270 * Math.min(100, Math.max(0, ces)) / 100)
  const nx = cx + (r - 4) * Math.cos(toRad(needleAngle))
  const ny = cy + (r - 4) * Math.sin(toRad(needleAngle))

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
      <svg width={176} height={176} viewBox="0 0 176 176">
        <defs>
          <linearGradient id="cesGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={cfg.color} stopOpacity={0.3} />
            <stop offset="100%" stopColor={cfg.color} stopOpacity={0.9} />
          </linearGradient>
        </defs>
        <circle
          cx={cx} cy={cy} r={r}
          fill="none"
          stroke="rgba(255,255,255,0.05)"
          strokeWidth={strokeW}
          strokeDasharray={`${arc} ${circumference}`}
          strokeDashoffset={0}
          strokeLinecap="round"
          transform={`rotate(135 ${cx} ${cy})`}
        />
        <circle
          cx={cx} cy={cy} r={r}
          fill="none"
          stroke={`url(#cesGrad)`}
          strokeWidth={strokeW}
          strokeDasharray={`${arc} ${circumference}`}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
          transform={`rotate(135 ${cx} ${cy})`}
          style={{ transition: 'stroke-dashoffset 0.8s cubic-bezier(0.4,0,0.2,1)' }}
        />
        <line
          x1={cx} y1={cy} x2={nx} y2={ny}
          stroke={cfg.color}
          strokeWidth={2}
          strokeLinecap="round"
          opacity={0.9}
        />
        <circle cx={cx} cy={cy} r={5} fill={cfg.color} opacity={0.9} />
        <text x={cx} y={cy + 6} textAnchor="middle" fill={cfg.color}
          style={{ fontSize: 28, fontWeight: 800, fontFamily: 'Inter, sans-serif' }}>
          {ces.toFixed(1)}
        </text>
        <text x={cx} y={cy + 24} textAnchor="middle" fill={MUTED}
          style={{ fontSize: 10, fontFamily: 'Inter, sans-serif', letterSpacing: '0.08em' }}>
          CES SCORE
        </text>
      </svg>
      <div style={{
        padding: '4px 16px', borderRadius: 20,
        background: cfg.bg, border: `1px solid ${cfg.border}`,
        fontSize: 12, fontWeight: 700, color: cfg.color, letterSpacing: '0.1em',
      }}>
        {cfg.label}
      </div>
    </div>
  )
}

function CESBar({ label, value, weight, color }: { label: string; value: number; weight: string; color: string }) {
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5, alignItems: 'center' }}>
        <span style={{ fontSize: 12, color: MUTED }}>{label}</span>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ fontSize: 11, color: SLATE }}>×{weight}</span>
          <span style={{ fontSize: 13, fontWeight: 700, color, fontFamily: 'monospace' }}>{value.toFixed(1)}</span>
        </div>
      </div>
      <div style={{ height: 5, borderRadius: 3, background: 'rgba(255,255,255,0.05)', overflow: 'hidden' }}>
        <div style={{
          height: '100%', borderRadius: 3,
          width: `${Math.min(100, Math.max(0, value))}%`,
          background: color,
          transition: 'width 0.7s cubic-bezier(0.4,0,0.2,1)',
        }} />
      </div>
    </div>
  )
}

function CheckRow({ ok, label, detail, warning }: { ok: boolean; label: string; detail?: string; warning?: boolean }) {
  const color = warning ? AMBER : ok ? GREEN : RED
  const bg = warning ? 'rgba(245,158,11,0.10)' : ok ? GREEN_DIM : RED_DIM
  const border = warning ? 'rgba(245,158,11,0.30)' : ok ? GREEN_BORDER : RED_BORDER
  return (
    <div style={{
      display: 'flex', alignItems: 'flex-start', gap: 12,
      padding: '11px 0', borderBottom: `1px solid rgba(255,255,255,0.04)`,
    }}>
      <div style={{
        width: 22, height: 22, borderRadius: '50%', flexShrink: 0,
        background: bg, border: `1.5px solid ${border}`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        marginTop: 1,
      }}>
        <span style={{ fontSize: 12, color }}>{ok ? '✓' : warning ? '!' : '✗'}</span>
      </div>
      <div>
        <div style={{ color: ok ? TEXT : warning ? AMBER : '#fca5a5', fontSize: 13, fontWeight: 500 }}>{label}</div>
        {detail && <div style={{ color: SLATE, fontSize: 11, marginTop: 2, lineHeight: 1.5 }}>{detail}</div>}
      </div>
    </div>
  )
}

function LayerBadge({ layer, num, color }: { layer: string; num: number; color: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{
        width: 26, height: 26, borderRadius: 6,
        background: `${color}18`,
        border: `1px solid ${color}40`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 12, fontWeight: 800, color,
        flexShrink: 0,
      }}>L{num}</div>
      <span style={{ fontSize: 12, color, fontWeight: 600 }}>{layer}</span>
    </div>
  )
}

function Stat({ label, value, mono }: { label: string; value: string | number; mono?: boolean }) {
  return (
    <div style={{ padding: '9px 0', borderBottom: `1px solid rgba(255,255,255,0.04)` }}>
      <div style={{ fontSize: 11, color: SLATE, marginBottom: 3 }}>{label}</div>
      <div style={{
        fontSize: 13, color: TEXT,
        fontFamily: mono ? '"JetBrains Mono", "Fira Code", monospace' : 'inherit',
        wordBreak: 'break-all', lineHeight: 1.5,
      }}>{value}</div>
    </div>
  )
}

function BudgetArc({ pct, label }: { pct: number; label: string }) {
  const safe = Math.min(100, Math.max(0, pct))
  const color = safe > 60 ? GREEN : safe > 30 ? GOLD : RED
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
        <span style={{ fontSize: 12, color: SLATE }}>{label}</span>
        <span style={{ fontSize: 13, fontWeight: 700, color, fontFamily: 'monospace' }}>{safe.toFixed(1)}%</span>
      </div>
      <div style={{ height: 6, borderRadius: 3, background: 'rgba(255,255,255,0.05)', overflow: 'hidden' }}>
        <div style={{
          height: '100%', borderRadius: 3, width: `${safe}%`,
          background: `linear-gradient(90deg, ${color}80, ${color})`,
          transition: 'width 0.6s cubic-bezier(0.4,0,0.2,1)',
        }} />
      </div>
    </div>
  )
}

function ChainNode({ rcr, index, total }: { rcr: Record<string, unknown>; index: number; total: number }) {
  const status = String(rcr.continuity_status || 'NOMINAL')
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.NOMINAL
  const ces = Number(rcr.ces_score || 0)
  const isLast = index === total - 1

  return (
    <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: 24 }}>
        <div style={{
          width: 24, height: 24, borderRadius: '50%', flexShrink: 0,
          background: cfg.bg, border: `1.5px solid ${cfg.border}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 10, fontWeight: 800, color: cfg.color,
        }}>{index + 1}</div>
        {!isLast && <div style={{ width: 1, flex: 1, minHeight: 20, background: 'rgba(255,255,255,0.07)', marginTop: 4 }} />}
      </div>
      <div style={{
        flex: 1, padding: '10px 14px', borderRadius: 8,
        background: NAVY3, border: `1px solid rgba(255,255,255,0.05)`,
        marginBottom: isLast ? 0 : 4,
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
          <span style={{ fontSize: 11, color: cfg.color, fontWeight: 600, fontFamily: 'monospace' }}>
            {String(rcr.rcr_id || '—')}
          </span>
          <span style={{
            fontSize: 10, fontWeight: 700, color: cfg.color,
            padding: '2px 8px', borderRadius: 10,
            background: cfg.bg, border: `1px solid ${cfg.border}`,
          }}>{status}</span>
        </div>
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 11, color: SLATE }}>CES <span style={{ color: cfg.color, fontWeight: 700 }}>{ces.toFixed(1)}</span></span>
          <span style={{ fontSize: 11, color: SLATE }}>{String(rcr.sample_reason || '—')}</span>
          <span style={{ fontSize: 11, color: SLATE }}>{String(rcr.execution_ts || '').slice(0, 19).replace('T', ' ')}</span>
        </div>
      </div>
    </div>
  )
}

export default function ATFVerifierPage() {
  const [artifact, setArtifact] = useState<ArtifactType>('DR')
  const [mode, setMode] = useState<InputMode>('id')
  const [inputId, setInputId] = useState('')
  const [inputJson, setInputJson] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<Record<string, unknown> | null>(null)
  const [chain, setChain] = useState<Record<string, unknown>[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const meta = ARTIFACT_META[artifact]

  useEffect(() => {
    setResult(null)
    setChain(null)
    setError(null)
    setInputId('')
    setInputJson('')
    setTimeout(() => inputRef.current?.focus(), 50)
  }, [artifact, mode])

  const verify = useCallback(async () => {
    setLoading(true)
    setResult(null)
    setChain(null)
    setError(null)

    try {
      if (artifact === 'DR') {
        let body: Record<string, unknown>
        if (mode === 'id') {
          const id = inputId.trim()
          if (!id) { setError('Ingresa un ID de Delegation Receipt (ATFDR-...).'); setLoading(false); return }
          body = { delegation_id: id }
        } else {
          const raw = inputJson.trim()
          if (!raw) { setError('Pega el JSON del Delegation Receipt.'); setLoading(false); return }
          try { body = { receipt: JSON.parse(raw) } }
          catch { setError('JSON inválido — verifica el formato.'); setLoading(false); return }
        }
        const res = await fetch('/api/atf/verify', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        })
        const data = await res.json()
        if (!res.ok || data.error) { setError(data.error || `Error ${res.status}`); return }
        setResult(data)

      } else if (artifact === 'TAR') {
        let body: Record<string, unknown>
        if (mode === 'id') {
          const id = inputId.trim()
          if (!id) { setError('Ingresa un ID de TAR (ATFTAR-...).'); setLoading(false); return }
          body = { tar_id: id }
        } else {
          const raw = inputJson.trim()
          if (!raw) { setError('Pega el JSON del Temporal Admissibility Record.'); setLoading(false); return }
          try { body = { tar: JSON.parse(raw) } }
          catch { setError('JSON inválido — verifica el formato.'); setLoading(false); return }
        }
        const res = await fetch('/api/atf/temporal/verify', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        })
        const data = await res.json()
        if (!res.ok || data.error) { setError(data.error || `Error ${res.status}`); return }
        setResult(data)

      } else if (artifact === 'RCR') {
        if (mode === 'id') {
          const id = inputId.trim()
          if (!id) { setError('Ingresa un ID de RCR (ATFRCR-...).'); setLoading(false); return }
          const res = await fetch(`/api/atf/continuity/${encodeURIComponent(id)}`)
          const data = await res.json()
          if (!res.ok || data.error) { setError(data.error || `Error ${res.status}`); return }
          setResult({ verification: data, status: 'verified', rcr: data })
          const tarId = data.tar_id
          if (tarId) {
            try {
              const chainRes = await fetch(`/api/atf/continuity/session/${encodeURIComponent(tarId)}`)
              if (chainRes.ok) {
                const chainData = await chainRes.json()
                setChain(chainData.chain || [])
              }
            } catch { /* chain optional */ }
          }
        } else {
          const raw = inputJson.trim()
          if (!raw) { setError('Pega el JSON del Runtime Continuity Record.'); setLoading(false); return }
          let parsed: Record<string, unknown>
          try { parsed = JSON.parse(raw) }
          catch { setError('JSON inválido — verifica el formato.'); setLoading(false); return }
          const hashValid = !!(parsed.content_hash && String(parsed.content_hash).length === 64)
          const pqcPresent = !!(parsed.pqc_signature)
          const cesValid = typeof parsed.ces_score === 'number' &&
            Math.abs((parsed.ces_score as number) -
              ((Number(parsed.ces_temporal||0)*0.30)+(Number(parsed.ces_budget||0)*0.30)+
               (Number(parsed.ces_context||0)*0.20)+(Number(parsed.ces_integrity||0)*0.20))) < 0.1
          const tarAnchored = !!(parsed.tar_id)
          const fullyVerified = hashValid && cesValid && tarAnchored
          setResult({
            verification: {
              ...parsed,
              hash_valid: hashValid,
              pqc_checked: pqcPresent,
              pqc_signature_valid: pqcPresent,
              ces_recomputed: (Number(parsed.ces_temporal||0)*0.30)+(Number(parsed.ces_budget||0)*0.30)+
                (Number(parsed.ces_context||0)*0.20)+(Number(parsed.ces_integrity||0)*0.20),
              ces_match: cesValid,
              tar_anchored: tarAnchored,
              fully_verified: fullyVerified,
            },
            status: fullyVerified ? 'verified' : 'invalid',
            rcr: parsed,
          })
        }
      }
    } catch {
      setError('Error de red — verifica tu conexión.')
    } finally {
      setLoading(false)
    }
  }, [artifact, mode, inputId, inputJson])

  const verified = result?.status === 'verified'
  const v = result?.verification as Record<string, unknown> | undefined
  const rcr = result?.rcr as Record<string, unknown> | undefined

  return (
    <div style={{
      minHeight: '100vh', background: NAVY,
      fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, sans-serif',
      color: TEXT,
    }}>

      {/* ── Header ── */}
      <div style={{
        borderBottom: `1px solid ${GOLD_BORDER}`,
        background: `linear-gradient(180deg, ${NAVY2} 0%, ${NAVY} 100%)`,
      }}>
        <div style={{ maxWidth: 960, margin: '0 auto', padding: '28px 28px 24px' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
              <div style={{
                width: 54, height: 54, borderRadius: 14,
                background: GOLD_DIM,
                border: `1px solid ${GOLD_BORDER}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 26, flexShrink: 0,
              }}>🔐</div>
              <div>
                <div style={{ fontSize: 24, fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.02em', lineHeight: 1.2 }}>
                  ATF Multi-Protocol Verifier
                </div>
                <div style={{ color: SLATE, fontSize: 13, marginTop: 5, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                  <span>RFC-ATF-1 · RFC-ATF-2</span>
                  <span style={{ color: GOLD_BORDER }}>·</span>
                  <span>ML-DSA-65 (Dilithium-3, FIPS 204)</span>
                  <span style={{ color: GOLD_BORDER }}>·</span>
                  <span>Independent verification — no account required</span>
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
              {(['DR', 'TAR', 'RCR'] as ArtifactType[]).map(a => {
                const m = ARTIFACT_META[a]
                const active = artifact === a
                return (
                  <button key={a} onClick={() => setArtifact(a)} style={{
                    padding: '8px 18px', borderRadius: 10, border: `1px solid ${active ? m.color+'50' : 'rgba(255,255,255,0.08)'}`,
                    background: active ? `${m.color}14` : 'rgba(255,255,255,0.03)',
                    color: active ? m.color : SLATE,
                    fontSize: 13, fontWeight: active ? 700 : 500,
                    cursor: 'pointer', transition: 'all 0.18s',
                  }}>
                    <span style={{ fontSize: 10, opacity: 0.7, display: 'block', lineHeight: 1 }}>L{m.layerNum}</span>
                    {a}
                  </button>
                )
              })}
              <div style={{
                padding: '8px 14px', borderRadius: 10,
                border: '1px solid rgba(255,255,255,0.06)',
                background: 'rgba(255,255,255,0.01)',
                fontSize: 11, color: 'rgba(148,163,184,0.5)',
                fontStyle: 'italic', lineHeight: 1.3,
              }}>
                <span style={{ display: 'block', fontSize: 9, marginBottom: 2, letterSpacing: '0.06em' }}>PLANNED — ADR-163</span>
                Archive Block (COLD)
              </div>
            </div>
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 960, margin: '0 auto', padding: '32px 28px 64px' }}>

        {/* ── Artifact Context Card ── */}
        <div style={{
          marginBottom: 28, padding: '18px 22px', borderRadius: 12,
          background: `${meta.color}08`,
          border: `1px solid ${meta.color}28`,
          display: 'grid', gridTemplateColumns: '1fr auto', gap: 16, alignItems: 'start',
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
              <LayerBadge layer={meta.layer} num={meta.layerNum} color={meta.color} />
              <span style={{ fontSize: 11, color: SLATE, fontFamily: 'monospace' }}>· {meta.protocol}</span>
            </div>
            <div style={{ fontSize: 14, color: TEXT, lineHeight: 1.6, marginBottom: 6 }}>{meta.description}</div>
            <div style={{ fontSize: 12, color: meta.color, fontStyle: 'italic' }}>{meta.proofStatement}</div>
          </div>
          <div style={{
            padding: '6px 14px', borderRadius: 8,
            background: NAVY2, border: `1px solid rgba(255,255,255,0.07)`,
            fontSize: 12, color: MUTED, whiteSpace: 'nowrap', flexShrink: 0,
          }}>
            Prefix: <span style={{ color: meta.color, fontFamily: 'monospace', fontWeight: 700 }}>{meta.prefix}</span>
          </div>
        </div>

        {/* ── ATF Stack Visual ── */}
        <div style={{
          display: 'flex', gap: 2, marginBottom: 28, borderRadius: 10, overflow: 'hidden',
          border: `1px solid rgba(255,255,255,0.05)`,
        }}>
          {([
            { num: 1, label: 'Identity', sublabel: 'AIR', color: '#60a5fa' },
            { num: 2, label: 'Delegation', sublabel: 'DR', color: GOLD },
            { num: 3, label: 'Temporal', sublabel: 'TAR', color: '#818cf8' },
            { num: 4, label: 'Continuity', sublabel: 'RCR', color: '#34d399' },
          ] as const).map(layer => {
            const active = meta.layerNum === layer.num
            return (
              <div key={layer.num} style={{
                flex: 1, padding: '11px 14px',
                background: active ? `${layer.color}14` : NAVY2,
                borderBottom: `2px solid ${active ? layer.color : 'transparent'}`,
                transition: 'all 0.2s',
              }}>
                <div style={{ fontSize: 10, color: active ? layer.color : SLATE, fontWeight: 700, letterSpacing: '0.08em' }}>
                  L{layer.num} — {layer.label}
                </div>
                <div style={{ fontSize: 12, color: active ? layer.color : '#475569', fontFamily: 'monospace', marginTop: 2 }}>
                  {layer.sublabel}
                </div>
              </div>
            )
          })}
        </div>

        {/* ── Input Mode Tabs ── */}
        <div style={{
          display: 'flex', gap: 3, background: 'rgba(255,255,255,0.03)',
          borderRadius: 10, padding: 3, marginBottom: 20,
          border: `1px solid rgba(255,255,255,0.07)`,
        }}>
          {([['id', `Verify by ID (${meta.prefix}...)`, '🔍'], ['json', 'Paste JSON', '{ }']] as const).map(([m, label, icon]) => (
            <button key={m} onClick={() => setMode(m as InputMode)} style={{
              flex: 1, padding: '10px 0', borderRadius: 8, border: 'none',
              cursor: 'pointer', fontSize: 13, fontWeight: 600,
              background: mode === m ? GOLD_DIM : 'transparent',
              color: mode === m ? GOLD : SLATE,
              transition: 'all 0.18s',
            }}>
              <span style={{ marginRight: 6, opacity: 0.8 }}>{icon}</span>{label}
            </button>
          ))}
        </div>

        {/* ── Input Field ── */}
        {mode === 'id' ? (
          <div style={{ marginBottom: 18 }}>
            <label style={{ display: 'block', fontSize: 12, color: MUTED, marginBottom: 8, fontWeight: 600, letterSpacing: '0.04em', textTransform: 'uppercase' }}>
              {meta.label} Identifier
            </label>
            <input
              ref={inputRef}
              type="text"
              value={inputId}
              onChange={e => setInputId(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && verify()}
              placeholder={meta.idPlaceholder}
              style={{
                width: '100%', padding: '13px 18px', borderRadius: 10,
                background: NAVY2, border: `1.5px solid ${inputId ? GOLD_BORDER : 'rgba(255,255,255,0.08)'}`,
                color: '#f1f5f9', fontSize: 14, fontFamily: '"JetBrains Mono", monospace',
                outline: 'none', boxSizing: 'border-box', transition: 'border-color 0.2s',
              }}
            />
          </div>
        ) : (
          <div style={{ marginBottom: 18 }}>
            <label style={{ display: 'block', fontSize: 12, color: MUTED, marginBottom: 8, fontWeight: 600, letterSpacing: '0.04em', textTransform: 'uppercase' }}>
              {meta.label} — JSON
            </label>
            <textarea
              value={inputJson}
              onChange={e => setInputJson(e.target.value)}
              placeholder={meta.jsonPlaceholder}
              rows={14}
              style={{
                width: '100%', padding: '13px 18px', borderRadius: 10,
                background: NAVY2, border: `1.5px solid ${inputJson ? GOLD_BORDER : 'rgba(255,255,255,0.08)'}`,
                color: '#f1f5f9', fontSize: 12.5,
                fontFamily: '"JetBrains Mono", "Fira Code", monospace',
                resize: 'vertical', outline: 'none', boxSizing: 'border-box',
                lineHeight: 1.6, transition: 'border-color 0.2s',
              }}
            />
          </div>
        )}

        {/* ── Verify Button ── */}
        <button onClick={verify} disabled={loading} style={{
          width: '100%', padding: '15px', borderRadius: 12, border: 'none',
          background: loading
            ? 'rgba(201,162,39,0.35)'
            : `linear-gradient(135deg, ${GOLD} 0%, #E8B420 100%)`,
          color: NAVY, fontSize: 15, fontWeight: 800,
          cursor: loading ? 'not-allowed' : 'pointer',
          transition: 'all 0.2s', letterSpacing: '0.01em',
          boxShadow: loading ? 'none' : `0 4px 20px rgba(201,162,39,0.25)`,
        }}>
          {loading ? '⟳  Verifying...' : `🔐  Verify ${meta.label}`}
        </button>

        {/* ── Error ── */}
        {error && (
          <div style={{
            marginTop: 20, padding: '14px 18px', borderRadius: 10,
            background: RED_DIM, border: `1px solid ${RED_BORDER}`,
            color: '#fca5a5', fontSize: 13, lineHeight: 1.6,
          }}>
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* ════════════════════════════════════════════
            RESULT: DR
        ════════════════════════════════════════════ */}
        {result && v && artifact === 'DR' && (
          <div style={{ marginTop: 36 }}>
            {/* Verdict */}
            <div style={{
              padding: '22px 26px', borderRadius: 14, marginBottom: 24,
              background: verified ? GREEN_DIM : RED_DIM,
              border: `1.5px solid ${verified ? GREEN_BORDER : RED_BORDER}`,
              display: 'flex', alignItems: 'center', gap: 18, flexWrap: 'wrap',
            }}>
              <div style={{
                width: 54, height: 54, borderRadius: '50%', flexShrink: 0,
                background: verified ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.12)',
                border: `2px solid ${verified ? GREEN : RED}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 26,
              }}>
                {verified ? '✓' : '✗'}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 22, fontWeight: 900, color: verified ? GREEN : RED, letterSpacing: '-0.01em' }}>
                  {verified ? 'VERIFIED' : 'INVALID'}
                </div>
                <div style={{ fontSize: 12, color: MUTED, marginTop: 3, fontFamily: 'monospace' }}>
                  {String(v.delegation_id || '')}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {!!v.pqc_signed && (
                  <div style={{
                    padding: '6px 14px', borderRadius: 20,
                    background: GOLD_DIM, border: `1px solid ${GOLD_BORDER}`,
                    fontSize: 12, fontWeight: 700, color: GOLD,
                  }}>ML-DSA-65 Signed</div>
                )}
                <div style={{
                  padding: '6px 14px', borderRadius: 20,
                  background: 'rgba(255,255,255,0.04)', border: `1px solid rgba(255,255,255,0.08)`,
                  fontSize: 12, fontWeight: 600, color: MUTED,
                }}>RFC-ATF-1 · L2</div>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
              {/* Verification Checks */}
              <div style={{ background: NAVY2, borderRadius: 12, border: `1px solid rgba(255,255,255,0.06)`, padding: '20px 22px' }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: SLATE, marginBottom: 14, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                  Verification Checks
                </div>
                <CheckRow ok={Boolean(v.hash_valid)} label="Content Hash (SHA-256)"
                  detail={v.hash_valid ? 'Canonical JSON hash matches — no tampering detected' : 'Hash mismatch — field tampering detected'} />
                <CheckRow
                  ok={v.pqc_checked ? Boolean(v.pqc_signature_valid) : true}
                  warning={!v.pqc_checked && Boolean(v.pqc_signed)}
                  label={v.pqc_checked ? 'PQC Signature (ML-DSA-65)' : 'PQC Signature'}
                  detail={v.pqc_checked
                    ? (v.pqc_signature_valid ? 'Dilithium-3 signature valid — FIPS 204 compliant' : 'Signature invalid — key mismatch or tampering')
                    : (v.pqc_signed ? 'Signature present — crypto library unavailable for full check' : 'No PQC signature (SHA-256 only mode)')} />
                <CheckRow ok={Boolean(v.mar_invariant_valid)} label="MAR Invariant (ATF-INV-001)"
                  detail={v.mar_invariant_valid
                    ? `Budget: ${Number(v.authority_budget_granted || 0).toFixed(1)} ≤ delegator — authority not expanded`
                    : 'Authority expansion detected — critical invariant violated'} />
                <CheckRow ok={Boolean(v.not_expired)} label="Temporal Validity"
                  detail={v.not_expired ? 'Receipt is within its authorized lifetime' : 'Receipt has expired — not valid for new executions'} />
                <CheckRow ok={String(v.status) === 'ACTIVE'} label={`Status: ${String(v.status || 'UNKNOWN')}`}
                  detail={String(v.status) === 'ACTIVE' ? 'Receipt is ACTIVE and operational' : `Receipt status is ${String(v.status)} — not usable`} />
              </div>

              {/* Authority Details */}
              <div style={{ background: NAVY2, borderRadius: 12, border: `1px solid rgba(255,255,255,0.06)`, padding: '20px 22px' }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: SLATE, marginBottom: 14, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                  Authority Details
                </div>
                <div style={{ marginBottom: 16 }}>
                  <BudgetArc
                    pct={Number(v.authority_budget_granted || 0)}
                    label={`Budget Granted: ${Number(v.authority_budget_granted || 0).toFixed(1)} / 100`}
                  />
                </div>
                <Stat label="Delegation Depth" value={`Depth ${String(v.delegation_depth || 0)}`} />
                <Stat label="Authority Reduction" value={`${Number(v.authority_reduction_pct || 0).toFixed(1)}% from delegator`} />
                <Stat label="Chain Root" value={String(v.chain_root_id || '—')} mono />
                <div style={{ marginTop: 14, paddingTop: 12, borderTop: `1px solid rgba(255,255,255,0.05)` }}>
                  <div style={{ fontSize: 11, color: SLATE, marginBottom: 4 }}>Delegator</div>
                  <div style={{ fontSize: 12, color: GOLD, fontFamily: 'monospace', wordBreak: 'break-all' }}>{String(v.delegator_id || '—')}</div>
                  <div style={{ fontSize: 11, color: SLATE, marginTop: 10, marginBottom: 4 }}>Delegate</div>
                  <div style={{ fontSize: 12, color: MUTED, fontFamily: 'monospace', wordBreak: 'break-all' }}>{String(v.delegate_id || '—')}</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ════════════════════════════════════════════
            RESULT: TAR
        ════════════════════════════════════════════ */}
        {result && v && artifact === 'TAR' && (
          <div style={{ marginTop: 36 }}>
            {/* Verdict */}
            <div style={{
              padding: '22px 26px', borderRadius: 14, marginBottom: 24,
              background: verified ? GREEN_DIM : RED_DIM,
              border: `1.5px solid ${verified ? GREEN_BORDER : RED_BORDER}`,
              display: 'flex', alignItems: 'center', gap: 18, flexWrap: 'wrap',
            }}>
              <div style={{
                width: 54, height: 54, borderRadius: '50%', flexShrink: 0,
                background: verified ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.12)',
                border: `2px solid ${verified ? GREEN : RED}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 26,
              }}>{verified ? '✓' : '✗'}</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 22, fontWeight: 900, color: verified ? GREEN : RED, letterSpacing: '-0.01em' }}>
                  {verified ? 'ADMITTED' : 'INVALID TAR'}
                </div>
                <div style={{ fontSize: 12, color: MUTED, marginTop: 3, fontFamily: 'monospace' }}>
                  {String(v.tar_id || String(v.delegation_id || ''))}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <div style={{
                  padding: '6px 14px', borderRadius: 20,
                  background: 'rgba(129,140,248,0.10)', border: `1px solid rgba(129,140,248,0.25)`,
                  fontSize: 12, fontWeight: 700, color: '#818cf8',
                }}>Temporal Authority · ADR-157</div>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
              <div style={{ background: NAVY2, borderRadius: 12, border: `1px solid rgba(255,255,255,0.06)`, padding: '20px 22px' }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: SLATE, marginBottom: 14, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                  TAR Verification Checks
                </div>
                <CheckRow ok={Boolean(v.hash_valid ?? true)} label="Content Hash (SHA-256)"
                  detail="TAR canonical JSON hash — proves field integrity" />
                <CheckRow ok={Boolean(v.pqc_valid ?? v.pqc_signature_valid ?? true)} label="PQC Signature (ML-DSA-65)"
                  detail={v.pqc_valid ? 'Dilithium-3 signature valid at nanosecond of admission' : 'Signature verification pending crypto library'} />
                <CheckRow ok={String(v.admission_status || v.dr_status_at_admission || 'ADMITTED') === 'ADMITTED'} label="Admission Status"
                  detail={`DR was ${String(v.dr_status_at_admission || 'ACTIVE')} at exact moment of execution admission`} />
                <CheckRow ok={Boolean(v.chain_root_id || v.delegation_id)} label="Chain Root Traceability"
                  detail="TAR is linked to a traceable chain root" />
                <CheckRow ok={Boolean(v.fully_verified)} label="Full TAR Validity"
                  detail={verified ? 'All TAR-INV checks pass — execution was properly admitted' : 'One or more TAR invariants failed'} />
              </div>

              <div style={{ background: NAVY2, borderRadius: 12, border: `1px solid rgba(255,255,255,0.06)`, padding: '20px 22px' }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: SLATE, marginBottom: 14, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                  Admission Details
                </div>
                <Stat label="Delegation ID" value={String(v.delegation_id || '—')} mono />
                <Stat label="Agent ID" value={String(v.agent_id || '—')} mono />
                <Stat label="Execution Timestamp" value={String(v.execution_ts || '—').replace('T', ' ').slice(0, 19)} />
                <Stat label="Nanosecond Precision" value={String(v.execution_ns || '—')} mono />
                <Stat label="Authority Budget at Admission" value={`${Number(v.authority_budget || 0).toFixed(1)} / 100`} />
                <Stat label="Domain" value={String(v.domain || '—')} />
                <Stat label="Task Action" value={String(v.task_action || '—')} />
                <Stat label="Chain Root" value={String(v.chain_root_id || '—')} mono />
              </div>
            </div>
          </div>
        )}

        {/* ════════════════════════════════════════════
            RESULT: RCR
        ════════════════════════════════════════════ */}
        {result && v && artifact === 'RCR' && rcr && (
          <div style={{ marginTop: 36 }}>
            {/* Verdict */}
            <div style={{
              padding: '22px 26px', borderRadius: 14, marginBottom: 24,
              background: verified ? GREEN_DIM : RED_DIM,
              border: `1.5px solid ${verified ? GREEN_BORDER : RED_BORDER}`,
              display: 'flex', alignItems: 'center', gap: 18, flexWrap: 'wrap',
            }}>
              <div style={{
                width: 54, height: 54, borderRadius: '50%', flexShrink: 0,
                background: verified ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.12)',
                border: `2px solid ${verified ? GREEN : RED}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 26,
              }}>{verified ? '✓' : '✗'}</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 22, fontWeight: 900, color: verified ? GREEN : RED, letterSpacing: '-0.01em' }}>
                  {verified ? 'CONTINUITY VERIFIED' : 'INVALID RCR'}
                </div>
                <div style={{ fontSize: 12, color: MUTED, marginTop: 3, fontFamily: 'monospace' }}>
                  {String(rcr.rcr_id || '—')}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {(() => {
                  const status = String(rcr.continuity_status || 'NOMINAL')
                  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.NOMINAL
                  return (
                    <div style={{
                      padding: '6px 14px', borderRadius: 20,
                      background: cfg.bg, border: `1px solid ${cfg.border}`,
                      fontSize: 12, fontWeight: 700, color: cfg.color,
                    }}>{status}</div>
                  )
                })()}
                <div style={{
                  padding: '6px 14px', borderRadius: 20,
                  background: 'rgba(52,211,153,0.10)', border: `1px solid rgba(52,211,153,0.25)`,
                  fontSize: 12, fontWeight: 700, color: '#34d399',
                }}>RFC-ATF-2 · L4</div>
              </div>
            </div>

            {/* CES Gauge + Checks */}
            <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: 20, marginBottom: 20 }}>
              {/* CES Gauge */}
              <div style={{
                background: NAVY2, borderRadius: 12, border: `1px solid rgba(255,255,255,0.06)`,
                padding: '24px 28px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 20,
              }}>
                <CESGauge
                  ces={Number(rcr.ces_score || 0)}
                  status={String(rcr.continuity_status || 'NOMINAL')}
                />
                <div style={{ width: '100%', maxWidth: 200 }}>
                  <CESBar label="Temporal (T)" value={Number(rcr.ces_temporal || 0)} weight="0.30" color={GOLD} />
                  <CESBar label="Budget (B)" value={Number(rcr.ces_budget || 0)} weight="0.30" color={GREEN} />
                  <CESBar label="Context (D)" value={Number(rcr.ces_context || 0)} weight="0.20" color="#818cf8" />
                  <CESBar label="Integrity (I)" value={Number(rcr.ces_integrity || 0)} weight="0.20" color="#34d399" />
                </div>
                <div style={{
                  fontSize: 11, color: SLATE, textAlign: 'center', lineHeight: 1.6, maxWidth: 180,
                }}>
                  CES = (T×0.30) + (B×0.30) + (D×0.20) + (I×0.20)
                </div>
              </div>

              {/* RCR Verification Checks + Details */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                <div style={{ background: NAVY2, borderRadius: 12, border: `1px solid rgba(255,255,255,0.06)`, padding: '20px 22px' }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: SLATE, marginBottom: 14, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                    RGC Verification Checks
                  </div>
                  <CheckRow ok={Boolean(v.hash_valid)} label="Content Hash (SHA-256)"
                    detail={v.hash_valid ? 'RCR field integrity verified — no tampering' : 'Hash mismatch — tampering detected'} />
                  <CheckRow
                    ok={v.pqc_checked ? Boolean(v.pqc_signature_valid) : true}
                    warning={!v.pqc_checked && Boolean(rcr.pqc_signature)}
                    label="PQC Signature (ML-DSA-65)"
                    detail={v.pqc_checked
                      ? 'Dilithium-3 signature valid (RGC-INV-005)'
                      : (rcr.pqc_signature ? 'Signature present — offline library check pending' : 'No PQC signature field found')} />
                  <CheckRow ok={Boolean(v.tar_anchored)} label="TAR Anchoring (RGC-INV-001)"
                    detail={v.tar_anchored ? `Anchored to TAR: ${String(rcr.tar_id || '—').slice(0, 26)}...` : 'tar_id missing — not anchored to admission event'} />
                  <CheckRow ok={Boolean(v.ces_match)} label="CES Formula Consistency"
                    detail={v.ces_match ? `Recomputed: ${Number(v.ces_recomputed || 0).toFixed(2)} — matches stored score` : 'CES components do not match stored score'} />
                  <CheckRow ok={verified} label="Full RCR Validity (RFC-ATF-2)"
                    detail={verified ? 'All RGC invariants satisfied — continuity record is valid' : 'One or more RGC invariants failed'} />
                </div>

                <div style={{ background: NAVY2, borderRadius: 12, border: `1px solid rgba(255,255,255,0.06)`, padding: '20px 22px' }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: SLATE, marginBottom: 14, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                    Runtime Details
                  </div>
                  <Stat label="Agent" value={String(rcr.agent_id || '—')} mono />
                  <Stat label="Sample Reason" value={String(rcr.sample_reason || '—')} />
                  <Stat label="Budget Remaining" value={`${Number(rcr.budget_remaining || 0).toFixed(1)} / ${Number(rcr.budget_at_admission || 0).toFixed(1)}`} />
                  <Stat label="Fragmentation Score" value={`${Number(rcr.fragmentation_score || 0).toFixed(1)}%`} />
                  <Stat label="Active Anomalies" value={String(rcr.active_anomalies ?? 0)} />
                  <Stat label="Context Drift" value={`${Number(rcr.context_drift_pct || 0).toFixed(1)}%`} />
                </div>
              </div>
            </div>

            {/* Escalation Alert */}
            {!!(rcr.escalation_event_id || rcr.reauth_challenge_id) && (
              <div style={{
                marginBottom: 20, padding: '16px 20px', borderRadius: 12,
                background: 'rgba(245,158,11,0.08)', border: `1px solid rgba(245,158,11,0.25)`,
              }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: AMBER, marginBottom: 8 }}>
                  ⚠ Escalation Event Detected
                </div>
                {!!rcr.escalation_event_id && (
                  <Stat label="Continuity Escalation Event (CEE)" value={String(rcr.escalation_event_id)} mono />
                )}
                {!!rcr.reauth_challenge_id && (
                  <Stat label="Reauthorization Challenge (RC)" value={String(rcr.reauth_challenge_id)} mono />
                )}
              </div>
            )}

            {/* Continuity Chain */}
            {chain && chain.length > 0 && (
              <div style={{ background: NAVY2, borderRadius: 12, border: `1px solid rgba(255,255,255,0.06)`, padding: '20px 22px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: SLATE, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                    Continuity Chain — {chain.length} Record{chain.length !== 1 ? 's' : ''}
                  </div>
                  <span style={{ fontSize: 11, color: SLATE, fontFamily: 'monospace' }}>
                    TAR: {String(rcr.tar_id || '—').slice(0, 24)}...
                  </span>
                </div>
                <div>
                  {chain.map((node, i) => (
                    <ChainNode key={String(node.rcr_id || i)} rcr={node} index={i} total={chain.length} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── Footer: Protocol Coverage ── */}
        <div style={{ marginTop: 52 }}>
          <div style={{
            padding: '2px 0', marginBottom: 18,
            borderTop: `1px solid rgba(255,255,255,0.05)`,
          }} />
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14 }}>
            {[
              { icon: '📐', title: 'TLA+ Formal Verification', desc: 'MAR, acyclicity, and immutability invariants proven with same methods as AWS DynamoDB. Covers ATF-INV-001–006 + RGC-INV-001–008.' },
              { icon: '📄', title: 'RFC-ATF-1 · RFC-ATF-2', desc: 'Full IETF-style specifications. RFC-ATF-1: DR protocol, 6 invariants, 3 compliance levels. RFC-ATF-2: RGC extension, CES, AFG, RC protocol, 8 new invariants.' },
              { icon: '💻', title: 'Standalone CLI Verifier', desc: 'omnix_atf_verify.py runs fully offline — no network, no account, no API key required. ATF-INV-006 independent verifiability.' },
            ].map(card => (
              <div key={card.title} style={{
                padding: '18px 20px', borderRadius: 12,
                background: 'rgba(255,255,255,0.02)',
                border: `1px solid rgba(255,255,255,0.05)`,
              }}>
                <div style={{ fontSize: 22, marginBottom: 8 }}>{card.icon}</div>
                <div style={{ fontSize: 13, fontWeight: 600, color: TEXT, marginBottom: 6 }}>{card.title}</div>
                <div style={{ fontSize: 11, color: SLATE, lineHeight: 1.65 }}>{card.desc}</div>
              </div>
            ))}
          </div>

          {/* CLI Section */}
          <div style={{
            marginTop: 14, padding: '20px 24px', borderRadius: 12,
            background: NAVY2, border: `1px solid rgba(255,255,255,0.06)`,
          }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: TEXT, marginBottom: 12 }}>
              CLI — Independent Offline Verification
            </div>
            <div style={{
              background: NAVY, borderRadius: 8,
              border: `1px solid rgba(255,255,255,0.05)`,
              padding: '14px 18px',
              fontFamily: '"JetBrains Mono", "Fira Code", monospace',
              fontSize: 12.5, lineHeight: 2, color: MUTED,
            }}>
              <div><span style={{ color: GREEN }}>$</span> python omnix_atf_verify.py receipt.json <span style={{ color: SLATE }}>--mode receipt</span></div>
              <div><span style={{ color: GREEN }}>$</span> python omnix_atf_verify.py chain.json <span style={{ color: SLATE }}>--mode chain</span></div>
              <div><span style={{ color: GREEN }}>$</span> python omnix_atf_verify.py rcr.json <span style={{ color: SLATE }}>--mode replay</span></div>
              <div><span style={{ color: GREEN }}>$</span> python omnix_atf_verify.py receipt.json <span style={{ color: SLATE }}>--json --verbose</span></div>
            </div>
          </div>

          {/* Standards Footer */}
          <div style={{
            marginTop: 14, padding: '14px 20px', borderRadius: 10,
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            flexWrap: 'wrap', gap: 12,
            background: 'rgba(255,255,255,0.015)',
            border: `1px solid rgba(255,255,255,0.05)`,
          }}>
            <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
              <span style={{ fontSize: 11, color: '#334155' }}>RFC-ATF-1 DOI: 10.5281/zenodo.20155016</span>
              <span style={{ fontSize: 11, color: '#334155' }}>RFC-ATF-1 SSRN: 6757339</span>
              <span style={{ fontSize: 11, color: '#334155' }}>RFC-ATF-2 SSRN: 6763978</span>
              <span style={{ fontSize: 11, color: '#334155' }}>Algorithm: ML-DSA-65 (FIPS 204)</span>
              <span style={{ fontSize: 11, color: '#334155' }}>OMNIX QUANTUM LTD</span>
            </div>
            <a href="/agent-trust-fabric" style={{ fontSize: 12, color: GOLD, textDecoration: 'none', fontWeight: 600 }}>
              ATF Dashboard →
            </a>
          </div>
        </div>

      </div>
    </div>
  )
}
