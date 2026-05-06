import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowLeft, Shield, CheckCircle, XCircle, Lock,
  RefreshCw, ChevronRight, ChevronDown, Activity,
  AlertTriangle, Zap, Filter, Play, BarChart3,
} from 'lucide-react'
import { API_BASE } from '../lib/apiBase'

interface CheckpointOutcome {
  checkpoint_id: string
  label: string
  status: 'PASS' | 'BLOCKED'
  executive_reason: string
}

interface Integrity {
  signature_standard: string
  pqc_signed: boolean
  chain_linked: boolean
  policy_version: string | null
  engine_version: string | null
}

interface AuditItem {
  receipt_id: string
  timestamp_utc: string | null
  asset: string | null
  domain: string | null
  domain_label: string
  decision: string
  executive_summary: string
  checkpoint_outcomes: CheckpointOutcome[]
  integrity: Integrity
}

interface DomainKpi {
  domain: string
  label: string
  approved: number
  blocked: number
  total: number
}

interface AuditResponse {
  success: boolean
  demo?: boolean
  generated_at: string
  note?: string
  meta: { limit: number; offset: number; total: number; has_more: boolean }
  kpis: {
    total_decisions: number
    approved: number
    blocked: number
    approved_pct: number
    blocked_pct: number
    by_domain: DomainKpi[]
  }
  items: AuditItem[]
}

const DOMAIN_COLORS: Record<string, string> = {
  trading:           '#C9A227',
  credit:            '#a78bfa',
  insurance:         '#60a5fa',
  stablecoin:        '#8B5CF6',
  robotics:          '#6366F1',
  energy_governance: '#00B4D8',
  real_estate:       '#38bdf8',
  medical_ai:        '#f472b6',
  autonomous_agent:  '#fb923c',
  defense:           '#0EA5E9',
}

const DOMAIN_ICONS: Record<string, string> = {
  trading:           '📈',
  credit:            '🕌',
  insurance:         '🛡️',
  stablecoin:        '🪙',
  robotics:          '🤖',
  energy_governance: '⚡',
  real_estate:       '🏢',
  medical_ai:        '🏥',
  autonomous_agent:  '🧠',
  defense:           '🎯',
}

const DOMAIN_LABELS: Record<string, string> = {
  trading:           'Trading',
  credit:            'Islamic Credit',
  insurance:         'Insurance',
  stablecoin:        'Stablecoin',
  robotics:          'Robotics',
  energy_governance: 'Energy',
  real_estate:       'Real Estate',
  medical_ai:        'Medical AI',
  autonomous_agent:  'Agents',
  defense:           'Defense',
}

const DOMAIN_GROUPS: { label: string; emoji: string; color: string; domains: string[] }[] = [
  { label: 'Financial',  emoji: '💰', color: '#C9A227',  domains: ['trading', 'credit', 'insurance', 'stablecoin'] },
  { label: 'Physical',   emoji: '⚙️', color: '#34d399',  domains: ['robotics', 'energy_governance', 'real_estate', 'defense'] },
  { label: 'AI',         emoji: '🧠', color: '#f472b6',  domains: ['medical_ai', 'autonomous_agent'] },
]

const DEMO_SIGNALS = {
  signal_integrity: 78, probability_score: 71, risk_exposure: 32,
  signal_coherence: 74, trend_persistence: 68, stress_resilience: 62,
  logic_consistency: 76, temporal_coherence: 70,
  domain: 'trading', asset: 'BTC/USD',
  scenario: 'Live demo — OMNIX Executive Audit',
}

function PulseDot({ color = '#10B981' }: { color?: string }) {
  return (
    <span style={{
      display: 'inline-block', width: 8, height: 8, borderRadius: '50%',
      background: color, boxShadow: `0 0 6px ${color}`,
      animation: 'livePulse 2s ease-in-out infinite',
    }} />
  )
}

function DecisionBadge({ decision }: { decision: string }) {
  const approved = decision === 'APPROVED'
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      padding: '3px 8px', borderRadius: 20, fontSize: 10, fontWeight: 700,
      background: approved ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)',
      color: approved ? '#10B981' : '#ef4444',
      border: `1px solid ${approved ? '#10B98130' : '#ef444430'}`,
      textTransform: 'uppercase', letterSpacing: '0.06em',
    }}>
      {approved ? <CheckCircle size={9} /> : <XCircle size={9} />}
      {decision}
    </span>
  )
}

function IntegrityBadge({ integrity }: { integrity: Integrity }) {
  return (
    <div style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      padding: '3px 8px', borderRadius: 6,
      background: 'rgba(201,162,39,0.08)',
      border: '1px solid rgba(201,162,39,0.2)',
    }}>
      <Lock size={9} color="#C9A227" />
      <span style={{ fontSize: 9, color: '#C9A227', fontWeight: 700 }}>
        {integrity.pqc_signed ? 'PQC SIGNED' : 'SIGNED'}
      </span>
      {integrity.chain_linked && (
        <span style={{ fontSize: 9, color: '#C9A22780' }}>· CHAINED</span>
      )}
    </div>
  )
}

function CheckpointRow({ outcome, idx }: { outcome: CheckpointOutcome; idx: number }) {
  const pass = outcome.status === 'PASS'
  return (
    <div style={{
      display: 'flex', alignItems: 'flex-start', gap: 10,
      padding: '0.6rem 0.75rem', borderRadius: 8,
      background: pass ? 'rgba(16,185,129,0.04)' : 'rgba(239,68,68,0.06)',
      border: `1px solid ${pass ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.15)'}`,
      animation: `fadeIn 0.3s ease ${idx * 0.04}s both`,
    }}>
      <div style={{ flexShrink: 0, marginTop: 1 }}>
        {pass ? <CheckCircle size={13} color="#10B981" /> : <XCircle size={13} color="#ef4444" />}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
          <span style={{ fontSize: 10, fontWeight: 700, color: pass ? '#10B981' : '#ef4444', minWidth: 42 }}>
            {outcome.checkpoint_id}
          </span>
          <span style={{ fontSize: 11, fontWeight: 600, color: '#E2E8F0' }}>{outcome.label}</span>
        </div>
        <p style={{ margin: 0, fontSize: 11, color: '#64748b', lineHeight: 1.5 }}>
          {outcome.executive_reason}
        </p>
      </div>
    </div>
  )
}

function DecisionRow({ item, selected, onClick }: { item: AuditItem; selected: boolean; onClick: () => void }) {
  const domColor = DOMAIN_COLORS[item.domain || ''] || '#94A3B8'
  const icon = DOMAIN_ICONS[item.domain || ''] || '🔷'
  const ts = item.timestamp_utc
    ? new Date(item.timestamp_utc).toLocaleString('en-GB', { dateStyle: 'short', timeStyle: 'short' })
    : '—'

  return (
    <div onClick={onClick} style={{
      display: 'grid',
      gridTemplateColumns: '1fr 130px 110px 120px 30px',
      alignItems: 'center', gap: 12,
      padding: '0.75rem 1rem', borderRadius: 10, cursor: 'pointer',
      background: selected ? 'rgba(201,162,39,0.06)' : 'rgba(15,33,64,0.4)',
      border: `1px solid ${selected ? 'rgba(201,162,39,0.25)' : 'rgba(255,255,255,0.04)'}`,
      transition: 'all 0.15s ease',
    }}>
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
          <span style={{ fontSize: 12 }}>{icon}</span>
          <span style={{ fontSize: 12, fontWeight: 600, color: '#E2E8F0' }}>
            {item.asset || item.domain_label}
          </span>
        </div>
        <code style={{ fontSize: 10, color: '#475569', fontFamily: 'monospace' }}>
          {item.receipt_id}
        </code>
      </div>
      <div style={{ fontSize: 11, color: '#64748b' }}>{ts}</div>
      <div>
        <span style={{
          fontSize: 10, fontWeight: 600, color: domColor,
          background: `${domColor}15`, padding: '2px 7px', borderRadius: 20,
        }}>
          {DOMAIN_LABELS[item.domain || ''] || item.domain_label.split(' ')[0]}
        </span>
      </div>
      <DecisionBadge decision={item.decision} />
      <div style={{ color: selected ? '#C9A227' : '#475569' }}>
        {selected ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
      </div>
    </div>
  )
}

const AUDIT_REFRESH_MS = 60_000

export default function AuditDashboard() {
  const [data, setData] = useState<AuditResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [domainFilter, setDomainFilter] = useState('')
  const [decisionFilter, setDecisionFilter] = useState('')
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)

  const [revokedCount, setRevokedCount] = useState<number | null>(null)
  const [execSuccess, setExecSuccess] = useState<number | null>(null)

  const [demoRunning, setDemoRunning] = useState(false)
  const [demoResult, setDemoResult] = useState<{
    decision: string; receipt_id: string; checkpoints_passed: number; pqc_signed: boolean
  } | null>(null)

  const fetchData = useCallback(async (silent = false) => {
    if (!silent) setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()
      if (domainFilter) params.set('domain', domainFilter)
      if (decisionFilter) params.set('decision', decisionFilter)
      const url = `${API_BASE}/api/public/audit-live?${params}`
      const res = await fetch(url, { cache: 'no-store' })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json: AuditResponse = await res.json()
      if (!json.success) throw new Error(`API returned success=false`)
      setData(json)
      setLastRefresh(new Date())
    } catch (e: unknown) {
      if (!silent) setError('Unable to load audit data.')
    } finally {
      if (!silent) setLoading(false)
    }
  }, [domainFilter, decisionFilter])

  const fetchExtendedKpis = useCallback(async () => {
    try {
      const slRes = await fetch(`${API_BASE}/api/trust/status-list`, { cache: 'no-store' })
      if (slRes.ok) {
        const sl = await slRes.json()
        setRevokedCount(sl.total_revoked ?? 0)
      }
    } catch { /* best-effort */ }
    try {
      const exRes = await fetch(`${API_BASE}/api/execution/receipts?limit=200`, { cache: 'no-store' })
      if (exRes.ok) {
        const ex = await exRes.json()
        const receipts: { final_status: string }[] = ex.receipts ?? []
        if (receipts.length > 0) {
          const filled = receipts.filter(r => r.final_status === 'FILLED' || r.final_status === 'PARTIAL').length
          setExecSuccess(Math.round(filled / receipts.length * 100))
        }
      }
    } catch { /* best-effort */ }
  }, [])

  useEffect(() => {
    fetchData()
    fetchExtendedKpis()
    const interval = setInterval(() => fetchData(true), AUDIT_REFRESH_MS)
    return () => clearInterval(interval)
  }, [fetchData, fetchExtendedKpis])

  const runFullFlow = async () => {
    setDemoRunning(true)
    setDemoResult(null)
    try {
      const res = await fetch(`${API_BASE}/api/governance/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(DEMO_SIGNALS),
      })
      const json = await res.json()
      if (json.receipt_id || json.decision) {
        setDemoResult({
          decision: json.decision || 'APPROVED',
          receipt_id: json.receipt_id || '—',
          checkpoints_passed: json.checkpoints_passed ?? 11,
          pqc_signed: json.pqc_signed ?? true,
        })
        fetchData(true)
      }
    } catch {
      setDemoResult({ decision: 'ERROR', receipt_id: '—', checkpoints_passed: 0, pqc_signed: false })
    } finally {
      setDemoRunning(false)
    }
  }

  const selectedItem = data?.items.find(i => i.receipt_id === selectedId) || null
  const filtered = data?.items.filter(item => {
    if (decisionFilter && item.decision !== decisionFilter) return false
    if (domainFilter && item.domain !== domainFilter) return false
    return true
  }) ?? []

  const totalDecisions = data?.kpis.total_decisions ?? 0
  const blockedPct = data?.kpis.blocked_pct ?? null
  const revokedPct = revokedCount !== null && totalDecisions > 0
    ? (revokedCount / totalDecisions * 100).toFixed(1)
    : null

  const byDomainMap: Record<string, DomainKpi> = {}
  data?.kpis.by_domain.forEach(d => { byDomainMap[d.domain] = d })

  return (
    <div style={{ minHeight: '100vh', background: '#050D18', color: '#E2E8F0', fontFamily: 'Inter, system-ui, sans-serif' }}>
      <style>{`
        @keyframes livePulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.6;transform:scale(1.3)} }
        @keyframes fadeIn { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
        @keyframes slideIn { from{opacity:0;transform:translateY(-8px)} to{opacity:1;transform:translateY(0)} }
        @keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
        .domain-chip:hover { opacity:0.85; }
        .flow-btn:hover { background: rgba(201,162,39,0.18) !important; transform: translateY(-1px); }
        .flow-btn:active { transform: translateY(0); }
      `}</style>

      {/* NAV */}
      <nav style={{
        position: 'sticky', top: 0, zIndex: 50,
        background: 'rgba(5,13,24,0.96)', backdropFilter: 'blur(12px)',
        borderBottom: '1px solid rgba(201,162,39,0.12)',
        padding: '0 1.5rem', display: 'flex', alignItems: 'center',
        justifyContent: 'space-between', height: 56,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Link to="/command" style={{ display: 'flex', alignItems: 'center', gap: 6, textDecoration: 'none', color: '#64748b', fontSize: 13 }}>
            <ArrowLeft size={14} />
          </Link>
          <div style={{ width: 1, height: 20, background: 'rgba(255,255,255,0.08)' }} />
          <img src="/omnix_logo.png" alt="OMNIX" style={{ height: 28, width: 'auto', objectFit: 'contain' }} />
          <div style={{ width: 1, height: 20, background: 'rgba(255,255,255,0.08)' }} />
          <span style={{ fontSize: 12, fontWeight: 700, color: '#C9A227', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
            Executive Audit
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <PulseDot color="#10B981" />
            <span style={{ fontSize: 10, color: '#475569' }}>LIVE · 10 verticals</span>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {lastRefresh && (
            <span style={{ fontSize: 10, color: '#334155' }}>
              Updated {lastRefresh.toLocaleTimeString()} · auto 60s
            </span>
          )}
          <button
            onClick={() => fetchData(false)}
            style={{ background: 'none', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 6, padding: '4px 8px', cursor: 'pointer', color: '#64748b', display: 'flex', alignItems: 'center', gap: 4 }}
          >
            <RefreshCw size={12} />
            <span style={{ fontSize: 11 }}>Refresh</span>
          </button>
        </div>
      </nav>

      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '2rem 1.5rem' }}>

        {/* HEADER + RUN BUTTON */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16, marginBottom: '2rem', animation: 'fadeIn 0.5s ease both' }}>
          <div>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              background: 'rgba(201,162,39,0.08)', border: '1px solid rgba(201,162,39,0.2)',
              borderRadius: 20, padding: '5px 14px', marginBottom: 14,
            }}>
              <Shield size={12} color="#C9A227" />
              <span style={{ fontSize: 11, color: '#C9A227', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase' }}>
                Executive Audit Dashboard — ADR-059
              </span>
            </div>
            <h1 style={{ fontSize: 'clamp(1.5rem,3vw,2.2rem)', fontWeight: 900, color: '#F8FAFC', margin: '0 0 0.5rem', lineHeight: 1.1 }}>
              Governance Decision Audit
            </h1>
            <p style={{ fontSize: 13, color: '#475569', margin: 0 }}>
              Every governance decision translated to plain business language.
              Each record carries a NIST-standardized post-quantum cryptographic signature.
            </p>
          </div>

          {/* RUN FULL FLOW BUTTON */}
          <div style={{ flexShrink: 0, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 10 }}>
            <button
              className="flow-btn"
              onClick={runFullFlow}
              disabled={demoRunning}
              style={{
                display: 'flex', alignItems: 'center', gap: 10,
                background: 'rgba(201,162,39,0.10)',
                border: '1px solid rgba(201,162,39,0.35)',
                borderRadius: 12, padding: '12px 22px',
                cursor: demoRunning ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s ease',
                opacity: demoRunning ? 0.7 : 1,
              }}
            >
              <div style={{
                width: 32, height: 32, borderRadius: '50%',
                background: 'rgba(201,162,39,0.15)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                {demoRunning
                  ? <RefreshCw size={14} color="#C9A227" style={{ animation: 'spin 1s linear infinite' }} />
                  : <Play size={14} color="#C9A227" fill="#C9A227" />
                }
              </div>
              <div style={{ textAlign: 'left' }}>
                <div style={{ fontSize: 13, fontWeight: 800, color: '#C9A227' }}>
                  {demoRunning ? 'Running OMNIX flow…' : 'Run full OMNIX flow'}
                </div>
                <div style={{ fontSize: 10, color: '#64748b', marginTop: 1 }}>
                  evaluate → govern → receipt → PQC seal
                </div>
              </div>
            </button>

            {demoResult && (
              <div style={{
                animation: 'slideIn 0.3s ease both',
                background: demoResult.decision === 'APPROVED' ? 'rgba(16,185,129,0.08)' : 'rgba(239,68,68,0.08)',
                border: `1px solid ${demoResult.decision === 'APPROVED' ? 'rgba(16,185,129,0.25)' : 'rgba(239,68,68,0.25)'}`,
                borderRadius: 10, padding: '10px 16px', minWidth: 260,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                  <DecisionBadge decision={demoResult.decision} />
                  <span style={{ fontSize: 10, color: '#64748b' }}>{demoResult.checkpoints_passed}/11 checks</span>
                </div>
                <code style={{ fontSize: 10, color: '#475569', display: 'block', wordBreak: 'break-all' }}>
                  {demoResult.receipt_id}
                </code>
                {demoResult.pqc_signed && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 6 }}>
                    <Lock size={9} color="#C9A227" />
                    <span style={{ fontSize: 9, color: '#C9A227', fontWeight: 700 }}>PQC SIGNED · RECEIPT ISSUED</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* KPI BAR — 4 métricas clave */}
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 12, marginBottom: '1.75rem',
        }}>
          {[
            {
              label: 'Decisions Evaluated',
              value: totalDecisions > 0 ? totalDecisions.toLocaleString() : '—',
              color: '#C9A227', icon: <Activity size={15} />,
              sub: 'all 10 verticals',
            },
            {
              label: 'Blocked %',
              value: blockedPct !== null ? `${blockedPct}%` : '—',
              color: '#ef4444', icon: <XCircle size={15} />,
              sub: `${data?.kpis.blocked ?? '—'} decisions blocked`,
            },
            {
              label: 'Revoked %',
              value: revokedPct !== null ? `${revokedPct}%` : '—',
              color: '#f59e0b', icon: <AlertTriangle size={15} />,
              sub: revokedCount !== null ? `${revokedCount} VCs revoked` : 'VC trust registry',
            },
            {
              label: 'Execution Success',
              value: execSuccess !== null ? `${execSuccess}%` : '—',
              color: '#10B981', icon: <Zap size={15} />,
              sub: 'filled + partial orders',
            },
          ].map(kpi => (
            <div key={kpi.label} style={{
              background: 'rgba(15,33,64,0.6)',
              border: `1px solid ${kpi.color}22`,
              borderRadius: 12, padding: '1.1rem 1.25rem',
              backdropFilter: 'blur(6px)',
              display: 'flex', flexDirection: 'column', gap: 4,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ color: kpi.color, opacity: 0.8 }}>{kpi.icon}</div>
                <div style={{ fontSize: 10, color: '#334155', textTransform: 'uppercase', letterSpacing: '0.06em', textAlign: 'right' }}>
                  {kpi.label}
                </div>
              </div>
              <div style={{ fontSize: 28, fontWeight: 900, color: kpi.color, lineHeight: 1, letterSpacing: '-0.02em' }}>
                {kpi.value}
              </div>
              <div style={{ fontSize: 10, color: '#475569' }}>{kpi.sub}</div>
            </div>
          ))}
        </div>

        {/* DOMAIN BREAKDOWN — agrupado por categoría */}
        {data?.kpis?.by_domain && data.kpis.by_domain.length > 0 && (
          <div style={{ marginBottom: '1.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: '1rem' }}>
              <BarChart3 size={13} color="#475569" />
              <span style={{ fontSize: 11, fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                Domain Breakdown
              </span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {DOMAIN_GROUPS.map(group => {
                const groupDomains = group.domains
                  .map(d => byDomainMap[d])
                  .filter(Boolean)
                if (groupDomains.length === 0) return null
                return (
                  <div key={group.label}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                      <span style={{ fontSize: 13 }}>{group.emoji}</span>
                      <span style={{
                        fontSize: 10, fontWeight: 800, color: group.color,
                        textTransform: 'uppercase', letterSpacing: '0.12em',
                      }}>
                        {group.label}
                      </span>
                      <div style={{ flex: 1, height: 1, background: `${group.color}20`, marginLeft: 4 }} />
                    </div>
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: `repeat(${group.domains.length}, 1fr)`,
                      gap: 8,
                    }}>
                      {group.domains.map(domKey => {
                        const d = byDomainMap[domKey]
                        const color = DOMAIN_COLORS[domKey] || '#94A3B8'
                        const icon = DOMAIN_ICONS[domKey] || '🔷'
                        const label = DOMAIN_LABELS[domKey] || domKey
                        if (!d) {
                          return (
                            <div key={domKey} style={{
                              background: 'rgba(15,33,64,0.25)',
                              border: '1px solid rgba(255,255,255,0.04)',
                              borderRadius: 10, padding: '0.65rem 0.9rem',
                              opacity: 0.35,
                            }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: 6 }}>
                                <span style={{ fontSize: 13 }}>{icon}</span>
                                <span style={{ fontSize: 11, fontWeight: 700, color }}>{label}</span>
                              </div>
                              <div style={{ fontSize: 10, color: '#334155' }}>No data</div>
                            </div>
                          )
                        }
                        const pct = d.total > 0 ? Math.round(d.approved / d.total * 100) : 0
                        return (
                          <div key={domKey} style={{
                            background: 'rgba(15,33,64,0.5)',
                            border: `1px solid ${color}22`,
                            borderRadius: 10, padding: '0.65rem 0.9rem',
                            cursor: 'pointer',
                            transition: 'border-color 0.15s',
                          }}
                          onClick={() => setDomainFilter(domainFilter === domKey ? '' : domKey)}
                          >
                            <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: 6 }}>
                              <span style={{ fontSize: 13 }}>{icon}</span>
                              <span style={{ fontSize: 11, fontWeight: 700, color }}>{label}</span>
                              {domainFilter === domKey && (
                                <span style={{ marginLeft: 'auto', fontSize: 9, color, background: `${color}15`, padding: '1px 5px', borderRadius: 8 }}>
                                  ACTIVE
                                </span>
                              )}
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#64748b', marginBottom: 5 }}>
                              <span><span style={{ color: '#10B981', fontWeight: 700 }}>{d.approved}</span> ok</span>
                              <span><span style={{ color: '#ef4444', fontWeight: 700 }}>{d.blocked}</span> blocked</span>
                              <span style={{ color: '#94A3B8', fontWeight: 700 }}>{pct}%</span>
                            </div>
                            <div style={{ height: 3, background: 'rgba(255,255,255,0.06)', borderRadius: 3, overflow: 'hidden' }}>
                              <div style={{ height: '100%', width: `${pct}%`, background: `linear-gradient(90deg, ${color}, #10B981)`, borderRadius: 3, transition: 'width 0.5s ease' }} />
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* FILTERS */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8, marginBottom: '1rem',
          flexWrap: 'wrap', padding: '0.75rem 1rem',
          background: 'rgba(15,33,64,0.35)', borderRadius: 10,
          border: '1px solid rgba(255,255,255,0.04)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 5, color: '#475569', fontSize: 12 }}>
            <Filter size={12} />
          </div>

          {['', 'trading', 'credit', 'insurance', 'stablecoin', 'robotics', 'energy_governance', 'real_estate', 'medical_ai', 'autonomous_agent'].map(d => (
            <button
              key={d || 'all'}
              className="domain-chip"
              onClick={() => setDomainFilter(d)}
              style={{
                padding: '4px 11px', borderRadius: 20, fontSize: 11, fontWeight: 600,
                cursor: 'pointer', border: 'none', transition: 'all 0.15s',
                background: domainFilter === d ? 'rgba(201,162,39,0.15)' : 'rgba(255,255,255,0.04)',
                color: domainFilter === d ? '#C9A227' : '#475569',
                outline: domainFilter === d ? '1px solid rgba(201,162,39,0.3)' : 'none',
              }}
            >
              {d ? `${DOMAIN_ICONS[d]} ${DOMAIN_LABELS[d] || d}` : 'All'}
            </button>
          ))}

          <div style={{ width: 1, height: 18, background: 'rgba(255,255,255,0.08)', margin: '0 2px' }} />

          {[['', 'All decisions'], ['APPROVED', '✅ Approved'], ['BLOCKED', '❌ Blocked']].map(([v, l]) => (
            <button
              key={v}
              onClick={() => setDecisionFilter(v)}
              style={{
                padding: '4px 11px', borderRadius: 20, fontSize: 11, fontWeight: 600,
                cursor: 'pointer', border: 'none', transition: 'all 0.15s',
                background: decisionFilter === v
                  ? (v === 'APPROVED' ? 'rgba(16,185,129,0.12)' : v === 'BLOCKED' ? 'rgba(239,68,68,0.12)' : 'rgba(201,162,39,0.12)')
                  : 'rgba(255,255,255,0.04)',
                color: decisionFilter === v
                  ? (v === 'APPROVED' ? '#10B981' : v === 'BLOCKED' ? '#ef4444' : '#C9A227')
                  : '#475569',
              }}
            >
              {l}
            </button>
          ))}

          {(domainFilter || decisionFilter) && (
            <button
              onClick={() => { setDomainFilter(''); setDecisionFilter('') }}
              style={{
                padding: '4px 10px', borderRadius: 20, fontSize: 11,
                cursor: 'pointer', border: 'none',
                background: 'rgba(239,68,68,0.08)', color: '#ef4444',
              }}
            >
              Clear
            </button>
          )}
        </div>

        {/* MAIN CONTENT */}
        {loading && (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#475569', fontSize: 13 }}>
            Loading governance audit data…
          </div>
        )}
        {error && (
          <div style={{
            background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)',
            borderRadius: 10, padding: '1rem 1.25rem', color: '#ef4444', fontSize: 13,
          }}>
            {error}
          </div>
        )}

        {!loading && !error && (
          <div style={{ display: 'grid', gridTemplateColumns: selectedItem ? '1fr 380px' : '1fr', gap: 16, alignItems: 'start' }}>

            {/* DECISIONS TABLE */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {filtered.length === 0 && (
                <div style={{ textAlign: 'center', padding: '2rem', color: '#475569', fontSize: 13 }}>
                  No decisions match the selected filters.
                </div>
              )}
              {filtered.map(item => (
                <DecisionRow
                  key={item.receipt_id}
                  item={item}
                  selected={selectedId === item.receipt_id}
                  onClick={() => setSelectedId(selectedId === item.receipt_id ? null : item.receipt_id)}
                />
              ))}
            </div>

            {/* DETAIL PANEL */}
            {selectedItem && (
              <div style={{
                position: 'sticky', top: 72,
                background: 'rgba(15,33,64,0.7)', border: '1px solid rgba(201,162,39,0.18)',
                borderRadius: 16, padding: '1.5rem',
                backdropFilter: 'blur(8px)',
                animation: 'fadeIn 0.25s ease both',
              }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '1rem', gap: 8 }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 800, color: '#F8FAFC', marginBottom: 4 }}>
                      {selectedItem.asset || selectedItem.domain_label}
                    </div>
                    <code style={{ fontSize: 10, color: '#475569', fontFamily: 'monospace' }}>
                      {selectedItem.receipt_id}
                    </code>
                  </div>
                  <DecisionBadge decision={selectedItem.decision} />
                </div>

                <div style={{
                  background: selectedItem.decision === 'APPROVED' ? 'rgba(16,185,129,0.06)' : 'rgba(239,68,68,0.06)',
                  border: `1px solid ${selectedItem.decision === 'APPROVED' ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)'}`,
                  borderRadius: 10, padding: '0.75rem',
                  fontSize: 12, color: '#CBD5E1', lineHeight: 1.6,
                  marginBottom: '1rem',
                }}>
                  {selectedItem.executive_summary}
                </div>

                <div style={{ marginBottom: '1rem' }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>
                    Checkpoint Results
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {selectedItem.checkpoint_outcomes.map((o, i) => (
                      <CheckpointRow key={`${o.checkpoint_id}-${i}`} outcome={o} idx={i} />
                    ))}
                  </div>
                </div>

                <div style={{
                  background: 'rgba(201,162,39,0.04)', border: '1px solid rgba(201,162,39,0.12)',
                  borderRadius: 10, padding: '0.75rem',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                    <Lock size={11} color="#C9A227" />
                    <span style={{ fontSize: 11, fontWeight: 700, color: '#C9A227', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                      Cryptographic Integrity
                    </span>
                    <IntegrityBadge integrity={selectedItem.integrity} />
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    {[
                      ['Signature Standard', selectedItem.integrity.signature_standard],
                      ['PQC Signed',         selectedItem.integrity.pqc_signed ? '✅ Yes' : '⚠️ No'],
                      ['Chain Linked',       selectedItem.integrity.chain_linked ? '✅ Yes' : '—'],
                      ['Policy Version',     selectedItem.integrity.policy_version || '—'],
                    ].map(([k, v]) => (
                      <div key={k as string} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, gap: 8 }}>
                        <span style={{ color: '#475569' }}>{k}</span>
                        <span style={{ color: '#94A3B8', textAlign: 'right', maxWidth: 200 }}>{v}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* FOOTER */}
        <div style={{
          marginTop: '2.5rem', paddingTop: '1.5rem',
          borderTop: '1px solid rgba(255,255,255,0.04)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          flexWrap: 'wrap', gap: 8,
        }}>
          <span style={{ fontSize: 11, color: '#1e293b' }}>
            Live data · NIST post-quantum cryptography · 9 verticals · ADR-059
          </span>
          <div style={{ display: 'flex', gap: 12 }}>
            <Link to="/try" style={{ fontSize: 11, color: '#334155', textDecoration: 'none' }}>Try Sandbox</Link>
            <Link to="/verify" style={{ fontSize: 11, color: '#334155', textDecoration: 'none' }}>Verify Receipt</Link>
            <Link to="/getting-started" style={{ fontSize: 11, color: '#334155', textDecoration: 'none' }}>SDK Docs</Link>
          </div>
        </div>

      </div>
    </div>
  )
}
