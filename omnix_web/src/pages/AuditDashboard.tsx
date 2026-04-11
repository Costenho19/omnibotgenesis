import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowLeft, Shield, CheckCircle, XCircle, Lock,
  RefreshCw, ChevronRight, ChevronDown, Activity,
  AlertTriangle, Zap, Filter
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
  trading:          '#C9A227',
  credit:           '#a78bfa',
  insurance:        '#60a5fa',
  robotics:         '#34d399',
  medical_ai:       '#f472b6',
  autonomous_agent: '#fb923c',
}
const DOMAIN_ICONS: Record<string, string> = {
  trading:          '📈',
  credit:           '🕌',
  insurance:        '🛡️',
  robotics:         '🤖',
  medical_ai:       '🏥',
  autonomous_agent: '🧠',
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
        {pass
          ? <CheckCircle size={13} color="#10B981" />
          : <XCircle size={13} color="#ef4444" />
        }
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

function DecisionRow({
  item,
  selected,
  onClick,
}: {
  item: AuditItem
  selected: boolean
  onClick: () => void
}) {
  const domColor = DOMAIN_COLORS[item.domain || ''] || '#94A3B8'
  const icon = DOMAIN_ICONS[item.domain || ''] || '🔷'
  const ts = item.timestamp_utc
    ? new Date(item.timestamp_utc).toLocaleString('en-GB', { dateStyle: 'short', timeStyle: 'short' })
    : '—'

  return (
    <div
      onClick={onClick}
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr 130px 110px 120px 30px',
        alignItems: 'center',
        gap: 12,
        padding: '0.75rem 1rem',
        borderRadius: 10,
        cursor: 'pointer',
        background: selected ? 'rgba(201,162,39,0.06)' : 'rgba(15,33,64,0.4)',
        border: `1px solid ${selected ? 'rgba(201,162,39,0.25)' : 'rgba(255,255,255,0.04)'}`,
        transition: 'all 0.15s ease',
      }}
    >
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
          {item.domain_label.split(' ')[0]}
        </span>
      </div>

      <DecisionBadge decision={item.decision} />

      <div style={{ color: selected ? '#C9A227' : '#475569' }}>
        {selected ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
      </div>
    </div>
  )
}

export default function AuditDashboard() {
  const [data, setData] = useState<AuditResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [domainFilter, setDomainFilter] = useState('')
  const [decisionFilter, setDecisionFilter] = useState('')
  const [isDemo, setIsDemo] = useState(true)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()
      if (domainFilter) params.set('domain', domainFilter)
      if (decisionFilter) params.set('decision', decisionFilter)

      const url = isDemo
        ? `${API_BASE}/api/public/audit-demo`
        : `${API_BASE}/api/governance/audit/decisions?${params}`

      const res = await fetch(url, { cache: 'no-store' })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json: AuditResponse = await res.json()
      if (!json.success) throw new Error('API returned error')
      setData(json)
    } catch (e: unknown) {
      setError('Unable to load audit data.')
      console.error(e)
    } finally {
      setLoading(false)
    }
  }, [domainFilter, decisionFilter, isDemo])

  useEffect(() => { fetchData() }, [fetchData])

  const selectedItem = data?.items.find(i => i.receipt_id === selectedId) || null
  const filtered = data?.items.filter(item => {
    if (decisionFilter && item.decision !== decisionFilter) return false
    if (domainFilter && item.domain !== domainFilter) return false
    return true
  }) ?? []

  return (
    <div style={{ minHeight: '100vh', background: '#050D18', color: '#E2E8F0', fontFamily: 'Inter, system-ui, sans-serif' }}>
      <style>{`
        @keyframes livePulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.6;transform:scale(1.3)} }
        @keyframes fadeIn { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
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
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {isDemo && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: 5,
              background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.25)',
              borderRadius: 20, padding: '3px 10px',
            }}>
              <AlertTriangle size={10} color="#f59e0b" />
              <span style={{ fontSize: 10, color: '#f59e0b', fontWeight: 700 }}>DEMO DATA</span>
            </div>
          )}
          <button
            onClick={fetchData}
            style={{ background: 'none', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 6, padding: '4px 8px', cursor: 'pointer', color: '#64748b', display: 'flex', alignItems: 'center', gap: 4 }}
          >
            <RefreshCw size={12} />
            <span style={{ fontSize: 11 }}>Refresh</span>
          </button>
        </div>
      </nav>

      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '2rem 1.5rem' }}>

        {/* HEADER */}
        <div style={{ marginBottom: '2rem', animation: 'fadeIn 0.5s ease both' }}>
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
            Every governance decision translated to plain business language. No internal scores or thresholds exposed.
            Each record carries a NIST-standardized post-quantum cryptographic signature.
          </p>
        </div>

        {/* KPI BAR */}
        {data?.kpis && (
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
            gap: 12, marginBottom: '1.5rem',
          }}>
            {[
              { label: 'Total Decisions',  value: data.kpis.total_decisions, color: '#C9A227',  icon: <Activity size={14} /> },
              { label: 'Approved',         value: data.kpis.approved,        color: '#10B981',  icon: <CheckCircle size={14} /> },
              { label: 'Blocked / Hold',   value: data.kpis.blocked,         color: '#ef4444',  icon: <XCircle size={14} /> },
              { label: 'Approval Rate',    value: `${data.kpis.approved_pct}%`, color: '#6366f1', icon: <Zap size={14} />, raw: true },
            ].map(kpi => (
              <div key={kpi.label} style={{
                background: 'rgba(15,33,64,0.6)', border: `1px solid ${kpi.color}22`,
                borderRadius: 12, padding: '1rem', textAlign: 'center', backdropFilter: 'blur(6px)',
              }}>
                <div style={{ color: kpi.color, marginBottom: 5, display: 'flex', justifyContent: 'center' }}>{kpi.icon}</div>
                <div style={{ fontSize: 24, fontWeight: 900, color: kpi.color, lineHeight: 1 }}>
                  {kpi.raw ? kpi.value : (typeof kpi.value === 'number' ? kpi.value.toLocaleString() : kpi.value)}
                </div>
                <div style={{ fontSize: 10, color: '#475569', marginTop: 4, textTransform: 'uppercase', letterSpacing: '0.07em' }}>{kpi.label}</div>
              </div>
            ))}
          </div>
        )}

        {/* DOMAIN BREAKDOWN */}
        {data?.kpis?.by_domain && data.kpis.by_domain.length > 0 && (
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: 10, marginBottom: '1.5rem',
          }}>
            {data.kpis.by_domain.map(d => {
              const color = DOMAIN_COLORS[d.domain] || '#94A3B8'
              const icon = DOMAIN_ICONS[d.domain] || '🔷'
              const pct = d.total > 0 ? Math.round(d.approved / d.total * 100) : 0
              return (
                <div key={d.domain} style={{
                  background: 'rgba(15,33,64,0.5)', border: `1px solid ${color}22`,
                  borderRadius: 10, padding: '0.75rem 1rem',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                    <span style={{ fontSize: 14 }}>{icon}</span>
                    <span style={{ fontSize: 11, fontWeight: 700, color }}>
                      {d.label}
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#64748b', marginBottom: 5 }}>
                    <span>Approved: <strong style={{ color: '#10B981' }}>{d.approved}</strong></span>
                    <span>Blocked: <strong style={{ color: '#ef4444' }}>{d.blocked}</strong></span>
                  </div>
                  <div style={{ height: 3, background: 'rgba(255,255,255,0.06)', borderRadius: 3, overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${pct}%`, background: `linear-gradient(90deg, ${color}, #10B981)`, borderRadius: 3 }} />
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* FILTERS */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 10, marginBottom: '1rem',
          flexWrap: 'wrap',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 5, color: '#475569', fontSize: 12 }}>
            <Filter size={12} />
            <span>Filter:</span>
          </div>

          {['', 'trading', 'credit', 'insurance', 'robotics'].map(d => (
            <button
              key={d || 'all'}
              onClick={() => setDomainFilter(d)}
              style={{
                padding: '4px 12px', borderRadius: 20, fontSize: 11, fontWeight: 600,
                cursor: 'pointer', border: 'none',
                background: domainFilter === d ? 'rgba(201,162,39,0.15)' : 'rgba(255,255,255,0.05)',
                color: domainFilter === d ? '#C9A227' : '#64748b',
                outline: domainFilter === d ? '1px solid rgba(201,162,39,0.3)' : 'none',
              }}
            >
              {d ? DOMAIN_ICONS[d] + ' ' + d.charAt(0).toUpperCase() + d.slice(1) : 'All Domains'}
            </button>
          ))}

          <div style={{ width: 1, height: 20, background: 'rgba(255,255,255,0.08)' }} />

          {[['', 'All'], ['APPROVED', 'Approved'], ['BLOCKED', 'Blocked']].map(([v, l]) => (
            <button
              key={v}
              onClick={() => setDecisionFilter(v)}
              style={{
                padding: '4px 12px', borderRadius: 20, fontSize: 11, fontWeight: 600,
                cursor: 'pointer', border: 'none',
                background: decisionFilter === v
                  ? (v === 'APPROVED' ? 'rgba(16,185,129,0.12)' : v === 'BLOCKED' ? 'rgba(239,68,68,0.12)' : 'rgba(201,162,39,0.15)')
                  : 'rgba(255,255,255,0.05)',
                color: decisionFilter === v
                  ? (v === 'APPROVED' ? '#10B981' : v === 'BLOCKED' ? '#ef4444' : '#C9A227')
                  : '#64748b',
              }}
            >
              {l}
            </button>
          ))}
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

                {/* Executive Summary */}
                <div style={{
                  background: selectedItem.decision === 'APPROVED' ? 'rgba(16,185,129,0.06)' : 'rgba(239,68,68,0.06)',
                  border: `1px solid ${selectedItem.decision === 'APPROVED' ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)'}`,
                  borderRadius: 10, padding: '0.75rem',
                  fontSize: 12, color: '#CBD5E1', lineHeight: 1.6,
                  marginBottom: '1rem',
                }}>
                  {selectedItem.executive_summary}
                </div>

                {/* Checkpoint Outcomes */}
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

                {/* Integrity */}
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

                {/* Timestamp */}
                {selectedItem.timestamp_utc && (
                  <div style={{ marginTop: 10, fontSize: 10, color: '#334155', textAlign: 'right' }}>
                    {new Date(selectedItem.timestamp_utc).toLocaleString('en-GB', { dateStyle: 'long', timeStyle: 'medium' })}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* FOOTER */}
        <div style={{
          marginTop: '2rem', paddingTop: '1.25rem',
          borderTop: '1px solid rgba(255,255,255,0.05)',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          flexWrap: 'wrap', gap: 8,
        }}>
          <div style={{ fontSize: 11, color: '#334155' }}>
            OMNIX Decision Governance — Executive Audit · ADR-059
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {isDemo && (
              <button
                onClick={() => setIsDemo(false)}
                style={{ fontSize: 10, color: '#6366f1', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}
              >
                Connect real data (API key required)
              </button>
            )}
            <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 10, color: '#334155' }}>
              <PulseDot color="#C9A227" />
              <span>NIST-standardized post-quantum cryptography</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
