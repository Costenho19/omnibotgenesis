import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  CheckCircle, XCircle, Clock, Activity,
  AlertTriangle, TrendingUp, Landmark, RefreshCw, ArrowLeft
} from 'lucide-react'

const API = import.meta.env.VITE_API_URL || ''

interface Metrics {
  total_decisions: number
  decisions_approved: number
  decisions_blocked: number
  decisions_held: number
  approval_rate: number
  block_rate: number
  avg_avm_confidence: number
  avg_ltv_ratio: number
  avg_decision_score: number
  avg_trajectory_score: number
  decisions_last_24h: number
  property_types_active: number
  aml_blocks: number
  compliance_blocks: number
  simulation_cycles: number
}

interface LiveDecision {
  decision_id: string
  property_id: string
  decision_type: string
  property_type: string
  market_segment: string
  jurisdiction: string
  financing_mode: string
  model_accuracy: number
  ltv_ratio: number
  aml_risk_score: number
  aml_flag: boolean
  decision: string
  decision_score: number
  block_reason: string | null
  receipt_id: string
  trajectory_score: number
  created_at: string
}

interface ByType {
  decision_type: string
  total: number
  approved: number
  blocked: number
  avg_avm_confidence: number
  avg_decision_score: number
  approval_rate: number
}

interface ByProperty {
  property_type: string
  total: number
  approved: number
  blocked: number
  avg_avm_confidence: number
  avg_ltv_ratio: number
  approval_rate: number
}

interface ByJurisdiction {
  jurisdiction: string
  total: number
  approved: number
  blocked: number
  avg_aml_risk: number
  avg_score: number
  approval_rate: number
}

const DECISION_TYPE_LABELS: Record<string, string> = {
  property_valuation: 'Property Valuation (AVM)',
  mortgage_approval:  'Mortgage Underwriting',
  tenant_screening:   'Tenant Screening',
  aml_transaction:    'AML Transaction Screen',
  rental_pricing:     'Algorithmic Rental Pricing',
}

const DECISION_TYPE_ICONS: Record<string, string> = {
  property_valuation: '🏠',
  mortgage_approval:  '🏦',
  tenant_screening:   '👤',
  aml_transaction:    '🔍',
  rental_pricing:     '💰',
}

const PROPERTY_TYPE_ICONS: Record<string, string> = {
  Residential: '🏠',
  Commercial:  '🏢',
  Industrial:  '🏭',
  Mixed_Use:   '🏙️',
  Land:        '🌍',
}

const JURISDICTION_FLAGS: Record<string, string> = {
  UAE:    '🇦🇪',
  GCC:    '🌙',
  UK:     '🇬🇧',
  EU:     '🇪🇺',
  GLOBAL: '🌐',
}

const SIGNAL_LABELS: Record<string, string> = {
  probability_score: 'AVM Confidence',
  risk_exposure:     'Transaction Risk',
  signal_coherence:  'Data Alignment',
  trend_persistence: 'Market Trajectory',
  stress_resilience: 'Stress Resilience',
  logic_consistency: 'Regulatory Compliance',
}

const SIGNAL_COLORS: Record<string, string> = {
  probability_score: '#38bdf8',
  risk_exposure:     '#f87171',
  signal_coherence:  '#a3e635',
  trend_persistence: '#34d399',
  stress_resilience: '#fb923c',
  logic_consistency: '#c084fc',
}

const FINANCING_LABELS: Record<string, string> = {
  Conventional: 'Conventional',
  Murabaha:     'Murabaha (Islamic)',
  Ijarah:       'Ijarah (Islamic)',
  Musharaka:    'Musharaka (Islamic)',
}

function ScoreBar({ value, color, inverted = false }: { value: number; color: string; inverted?: boolean }) {
  const display = inverted ? 100 - value : value
  const pct = Math.max(0, Math.min(100, display))
  const barColor = inverted
    ? value > 70 ? '#f87171' : value > 45 ? '#fbbf24' : '#34d399'
    : color
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{
        flex: 1, height: 6, background: 'rgba(255,255,255,0.08)',
        borderRadius: 3, overflow: 'hidden'
      }}>
        <div style={{
          width: `${pct}%`, height: '100%',
          background: barColor,
          borderRadius: 3,
          transition: 'width 0.8s ease',
          boxShadow: `0 0 8px ${barColor}60`,
        }} />
      </div>
      <span style={{ fontSize: 11, color: '#94a3b8', minWidth: 32, textAlign: 'right' }}>
        {Math.round(pct)}
      </span>
    </div>
  )
}

function KpiCard({
  label, value, sub, icon, color
}: {
  label: string; value: string | number; sub?: string;
  icon: React.ReactNode; color: string; trend?: 'up' | 'down' | 'neutral'
}) {
  return (
    <div style={{
      background: 'rgba(255,255,255,0.04)',
      border: `1px solid ${color}30`,
      borderRadius: 14,
      padding: '18px 20px',
      position: 'relative',
      overflow: 'hidden',
    }}>
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: 2,
        background: color, opacity: 0.6,
      }} />
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 }}>
            {label}
          </div>
          <div style={{ fontSize: 26, fontWeight: 700, color, letterSpacing: -0.5 }}>
            {value}
          </div>
          {sub && <div style={{ fontSize: 11, color: '#64748b', marginTop: 4 }}>{sub}</div>}
        </div>
        <div style={{
          width: 40, height: 40, borderRadius: 10,
          background: `${color}18`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color,
        }}>
          {icon}
        </div>
      </div>
    </div>
  )
}

function DecisionBadge({ decision }: { decision: string }) {
  const map: Record<string, { bg: string; color: string; label: string }> = {
    APPROVED: { bg: 'rgba(52,211,153,0.12)', color: '#34d399', label: 'APPROVED' },
    BLOCKED:  { bg: 'rgba(248,113,113,0.12)', color: '#f87171', label: 'BLOCKED' },
    HOLD:     { bg: 'rgba(251,191,36,0.12)',  color: '#fbbf24', label: 'HOLD' },
  }
  const style = map[decision] || { bg: 'rgba(148,163,184,0.1)', color: '#94a3b8', label: decision }
  return (
    <span style={{
      padding: '2px 8px', borderRadius: 6, fontSize: 10, fontWeight: 700,
      background: style.bg, color: style.color, letterSpacing: 0.5,
    }}>
      {style.label}
    </span>
  )
}

export default function RealEstateDashboard() {
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [liveDecisions, setLiveDecisions] = useState<LiveDecision[]>([])
  const [byType, setByType] = useState<ByType[]>([])
  const [byProperty, setByProperty] = useState<ByProperty[]>([])
  const [byJurisdiction, setByJurisdiction] = useState<ByJurisdiction[]>([])
  const [avgSignals, setAvgSignals] = useState<Record<string, number> | null>(null)
  const [loading, setLoading] = useState(true)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())
  const [tab, setTab] = useState<'type' | 'property' | 'jurisdiction'>('type')

  const fetchAll = async () => {
    try {
      const [mRes, fRes, tRes, pRes, jRes] = await Promise.all([
        fetch(`${API}/api/real-estate/metrics`),
        fetch(`${API}/api/real-estate/live-feed`),
        fetch(`${API}/api/real-estate/by-type`),
        fetch(`${API}/api/real-estate/by-property`),
        fetch(`${API}/api/real-estate/by-jurisdiction`),
      ])
      const [mData, fData, tData, pData, jData] = await Promise.all([
        mRes.json(), fRes.json(), tRes.json(), pRes.json(), jRes.json(),
      ])
      if (mData.success) setMetrics(mData.metrics)
      if (fData.success) {
        setLiveDecisions(fData.decisions)
        if (fData.decisions.length > 0) {
          const signals = ['probability_score','risk_exposure','signal_coherence','trend_persistence','stress_resilience','logic_consistency']
          const avgs: Record<string, number> = {}
          for (const sig of signals) {
            const vals = fData.decisions.filter((d: any) => d[sig] != null).map((d: any) => Number(d[sig]))
            avgs[sig] = vals.length ? vals.reduce((a: number, b: number) => a + b, 0) / vals.length : 0
          }
          setAvgSignals(avgs)
        }
      }
      if (tData.success) setByType(tData.by_type)
      if (pData.success) setByProperty(pData.by_property)
      if (jData.success) setByJurisdiction(jData.by_jurisdiction)
      setLastRefresh(new Date())
    } catch (e) {
      console.error('RealEstateDashboard fetch error:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAll()
    const interval = setInterval(fetchAll, 30_000)
    return () => clearInterval(interval)
  }, [])

  const fmtPct = (v: number) => `${(v * 100).toFixed(1)}%`
  const fmtNum = (v: number) => v.toLocaleString()

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh', background: '#0B0F1A',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: '#38bdf8', fontSize: 16, gap: 12,
      }}>
        <RefreshCw size={20} style={{ animation: 'spin 1s linear infinite' }} />
        Loading Real Estate Governance Engine...
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100vh', background: '#0B0F1A', color: '#e2e8f0', fontFamily: 'system-ui, sans-serif' }}>
      <style>{`@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } } @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }`}</style>

      {/* ── Header ── */}
      <div style={{
        background: 'rgba(56,189,248,0.06)',
        borderBottom: '1px solid rgba(56,189,248,0.15)',
        padding: '20px 32px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <Link to="/" style={{ color: '#64748b', display: 'flex', alignItems: 'center', gap: 6, textDecoration: 'none', fontSize: 13 }}>
            <ArrowLeft size={14} /> Back
          </Link>
          <div style={{ width: 1, height: 20, background: '#1e293b' }} />
          <div style={{
            width: 42, height: 42, borderRadius: 12,
            background: 'rgba(56,189,248,0.15)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 22,
          }}>🏢</div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 18, color: '#f1f5f9' }}>
              Real Estate Governance
            </div>
            <div style={{ fontSize: 12, color: '#38bdf8' }}>
              Property · AVM · AML · Islamic Finance · RERA Compliance
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#34d399', animation: 'pulse 2s infinite' }} />
            <span style={{ color: '#34d399', fontWeight: 600 }}>LIVE</span>
          </div>
          <Link
            to="/governance-demo-real-estate"
            style={{
              padding: '8px 16px', borderRadius: 8,
              background: 'rgba(56,189,248,0.12)',
              border: '1px solid rgba(56,189,248,0.25)',
              color: '#38bdf8', textDecoration: 'none', fontSize: 13, fontWeight: 600,
            }}
          >
            Try Interactive Demo →
          </Link>
        </div>
      </div>

      <div style={{ padding: '28px 32px', maxWidth: 1400, margin: '0 auto' }}>

        {/* ── KPI Grid ── */}
        {metrics && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 28 }}>
            <KpiCard
              label="Total Decisions"
              value={fmtNum(metrics.total_decisions)}
              sub={`${metrics.decisions_last_24h} in last 24h`}
              icon={<Activity size={18} />}
              color="#38bdf8"
            />
            <KpiCard
              label="Approved"
              value={fmtNum(metrics.decisions_approved)}
              sub={`${fmtPct(metrics.approval_rate)} approval rate`}
              icon={<CheckCircle size={18} />}
              color="#34d399"
            />
            <KpiCard
              label="Blocked"
              value={fmtNum(metrics.decisions_blocked)}
              sub={`${fmtPct(metrics.block_rate)} block rate`}
              icon={<XCircle size={18} />}
              color="#f87171"
            />
            <KpiCard
              label="Under Review"
              value={fmtNum(metrics.decisions_held)}
              sub="Compliance review queue"
              icon={<Clock size={18} />}
              color="#fbbf24"
            />
            <KpiCard
              label="Avg AVM Confidence"
              value={`${metrics.avg_avm_confidence.toFixed(1)}`}
              sub="Model accuracy score (0-100)"
              icon={<TrendingUp size={18} />}
              color="#a78bfa"
            />
            <KpiCard
              label="Avg LTV Ratio"
              value={`${metrics.avg_ltv_ratio.toFixed(1)}%`}
              sub="Loan-to-Value (mortgage decisions)"
              icon={<Landmark size={18} />}
              color="#fb923c"
            />
            <KpiCard
              label="AML Blocks"
              value={fmtNum(metrics.aml_blocks)}
              sub="FATF / anti-money laundering halts"
              icon={<AlertTriangle size={18} />}
              color="#f43f5e"
            />
            <KpiCard
              label="Simulation Cycles"
              value={fmtNum(metrics.simulation_cycles)}
              sub={`${metrics.property_types_active} property types active`}
              icon={<RefreshCw size={18} />}
              color="#38bdf8"
            />
          </div>
        )}

        {/* ── Signal Health Strip ── */}
        {avgSignals && (
          <div style={{
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: 14,
            padding: '18px 22px',
            marginBottom: 24,
          }}>
            <div style={{ fontSize: 12, color: '#64748b', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 14 }}>
              Average Signal Health — last 10 decisions
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px 32px' }}>
              {Object.entries(SIGNAL_LABELS).map(([key, label]) => (
                <div key={key}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontSize: 12, color: '#94a3b8' }}>{label}</span>
                    <span style={{ fontSize: 12, color: SIGNAL_COLORS[key], fontWeight: 600 }}>
                      {avgSignals[key]?.toFixed(1) ?? '—'}
                    </span>
                  </div>
                  <ScoreBar
                    value={avgSignals[key] ?? 0}
                    color={SIGNAL_COLORS[key]}
                    inverted={key === 'risk_exposure'}
                  />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Breakdown Tabs + Live Feed ── */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>

          {/* Left: Breakdown */}
          <div style={{
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: 14,
            overflow: 'hidden',
          }}>
            <div style={{ display: 'flex', borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
              {(['type', 'property', 'jurisdiction'] as const).map((t) => {
                const labels = { type: 'Decision Type', property: 'Property Type', jurisdiction: 'Jurisdiction' }
                return (
                  <button
                    key={t}
                    onClick={() => setTab(t)}
                    style={{
                      flex: 1, padding: '12px 8px',
                      background: tab === t ? 'rgba(56,189,248,0.1)' : 'transparent',
                      border: 'none', cursor: 'pointer',
                      color: tab === t ? '#38bdf8' : '#64748b',
                      fontSize: 11, fontWeight: 600,
                      letterSpacing: 0.5, textTransform: 'uppercase',
                      borderBottom: tab === t ? '2px solid #38bdf8' : '2px solid transparent',
                    }}
                  >
                    {labels[t]}
                  </button>
                )
              })}
            </div>
            <div style={{ padding: '14px 18px' }}>
              {tab === 'type' && byType.map(row => (
                <div key={row.decision_type} style={{
                  display: 'flex', alignItems: 'center',
                  gap: 10, padding: '8px 0',
                  borderBottom: '1px solid rgba(255,255,255,0.05)',
                }}>
                  <span style={{ fontSize: 16 }}>{DECISION_TYPE_ICONS[row.decision_type] || '🏠'}</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, color: '#e2e8f0', fontWeight: 500, marginBottom: 2 }}>
                      {DECISION_TYPE_LABELS[row.decision_type] || row.decision_type}
                    </div>
                    <div style={{ fontSize: 10, color: '#64748b' }}>
                      {row.total.toLocaleString()} decisions · {(row.approval_rate * 100).toFixed(1)}% approved
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: 13, color: '#34d399', fontWeight: 600 }}>{row.approved}</div>
                    <div style={{ fontSize: 10, color: '#f87171' }}>{row.blocked} blocked</div>
                  </div>
                </div>
              ))}
              {tab === 'property' && byProperty.map(row => (
                <div key={row.property_type} style={{
                  display: 'flex', alignItems: 'center',
                  gap: 10, padding: '8px 0',
                  borderBottom: '1px solid rgba(255,255,255,0.05)',
                }}>
                  <span style={{ fontSize: 16 }}>{PROPERTY_TYPE_ICONS[row.property_type] || '🏠'}</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, color: '#e2e8f0', fontWeight: 500, marginBottom: 2 }}>
                      {row.property_type}
                    </div>
                    <div style={{ fontSize: 10, color: '#64748b' }}>
                      {row.total.toLocaleString()} decisions · AVM {row.avg_avm_confidence?.toFixed(1) ?? '—'}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: 13, color: '#38bdf8', fontWeight: 600 }}>
                      {(row.approval_rate * 100).toFixed(1)}%
                    </div>
                    <div style={{ fontSize: 10, color: '#64748b' }}>approval rate</div>
                  </div>
                </div>
              ))}
              {tab === 'jurisdiction' && byJurisdiction.map(row => (
                <div key={row.jurisdiction} style={{
                  display: 'flex', alignItems: 'center',
                  gap: 10, padding: '8px 0',
                  borderBottom: '1px solid rgba(255,255,255,0.05)',
                }}>
                  <span style={{ fontSize: 18 }}>{JURISDICTION_FLAGS[row.jurisdiction] || '🌐'}</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, color: '#e2e8f0', fontWeight: 500, marginBottom: 2 }}>
                      {row.jurisdiction}
                    </div>
                    <div style={{ fontSize: 10, color: '#64748b' }}>
                      {row.total.toLocaleString()} decisions · AML risk {row.avg_aml_risk?.toFixed(1) ?? '—'}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: 13, color: '#a78bfa', fontWeight: 600 }}>
                      {(row.approval_rate * 100).toFixed(1)}%
                    </div>
                    <div style={{ fontSize: 10, color: '#64748b' }}>approval rate</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right: Live Feed */}
          <div style={{
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: 14,
            overflow: 'hidden',
          }}>
            <div style={{
              padding: '14px 18px',
              borderBottom: '1px solid rgba(255,255,255,0.07)',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            }}>
              <div style={{ fontSize: 12, color: '#64748b', textTransform: 'uppercase', letterSpacing: 1, fontWeight: 600 }}>
                Live Decision Feed
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: '#34d399' }}>
                <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#34d399', animation: 'pulse 2s infinite' }} />
                auto-refresh 30s
              </div>
            </div>
            <div style={{ padding: '8px 0', maxHeight: 400, overflowY: 'auto' }}>
              {liveDecisions.map(d => (
                <div key={d.decision_id} style={{
                  padding: '10px 18px',
                  borderBottom: '1px solid rgba(255,255,255,0.04)',
                  display: 'flex', alignItems: 'flex-start', gap: 10,
                }}>
                  <span style={{ fontSize: 16, marginTop: 1 }}>
                    {PROPERTY_TYPE_ICONS[d.property_type] || '🏠'}
                  </span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
                      <span style={{ fontSize: 11, color: '#e2e8f0', fontWeight: 500 }}>
                        {DECISION_TYPE_LABELS[d.decision_type] || d.decision_type}
                      </span>
                      <DecisionBadge decision={d.decision} />
                      {d.aml_flag && (
                        <span style={{
                          padding: '1px 5px', borderRadius: 4, fontSize: 9, fontWeight: 700,
                          background: 'rgba(244,63,94,0.15)', color: '#f43f5e',
                        }}>AML</span>
                      )}
                    </div>
                    <div style={{ fontSize: 10, color: '#64748b' }}>
                      {JURISDICTION_FLAGS[d.jurisdiction]} {d.jurisdiction} · {d.market_segment} · {FINANCING_LABELS[d.financing_mode] || d.financing_mode}
                    </div>
                    <div style={{ fontSize: 9, color: '#475569', marginTop: 2, fontFamily: 'monospace' }}>
                      {d.receipt_id}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right', fontSize: 11, color: '#94a3b8' }}>
                    {d.decision_score.toFixed(1)}
                  </div>
                </div>
              ))}
              {liveDecisions.length === 0 && (
                <div style={{ padding: '24px 18px', textAlign: 'center', color: '#475569', fontSize: 13 }}>
                  Simulator initializing — first decisions arriving shortly…
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ── Feature Callouts ── */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14 }}>
          {[
            {
              icon: '🔐',
              title: 'Post-Quantum Receipts',
              body: 'Every property decision — AVM valuation, mortgage underwriting, AML screen — is sealed with a CRYSTALS-Dilithium3 receipt. Prefix OMNIX-REP.',
              color: '#38bdf8',
            },
            {
              icon: '🕌',
              title: 'Islamic Finance Governance',
              body: 'Murabaha, Ijarah, and Musharaka decisions pass a dedicated Sharia parameter screening layer before reaching CP-7 compliance validation.',
              color: '#a78bfa',
            },
            {
              icon: '🔍',
              title: 'FATF AML Compliance',
              body: 'Real estate is a primary vehicle for money laundering. OMNIX applies FATF-aligned AML risk scoring with hard block on flagged transactions.',
              color: '#f43f5e',
            },
          ].map(card => (
            <div key={card.title} style={{
              background: 'rgba(255,255,255,0.03)',
              border: `1px solid ${card.color}20`,
              borderRadius: 14,
              padding: '18px 20px',
            }}>
              <div style={{ fontSize: 24, marginBottom: 10 }}>{card.icon}</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: card.color, marginBottom: 6 }}>
                {card.title}
              </div>
              <div style={{ fontSize: 12, color: '#64748b', lineHeight: 1.6 }}>
                {card.body}
              </div>
            </div>
          ))}
        </div>

        {/* ── Footer ── */}
        <div style={{
          marginTop: 28, paddingTop: 20,
          borderTop: '1px solid rgba(255,255,255,0.06)',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <div style={{ fontSize: 11, color: '#334155' }}>
            OMNIX Real Estate Governance Engine · ADR-RES-001 · PQC: CRYSTALS-Dilithium3 (NIST FIPS 204) · Receipt prefix: OMNIX-REP
          </div>
          <div style={{ fontSize: 11, color: '#334155' }}>
            Last refresh: {lastRefresh.toLocaleTimeString()}
          </div>
        </div>
      </div>
    </div>
  )
}
