import { useState, useEffect, useCallback, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield, AlertTriangle, CheckCircle, XCircle, Activity,
  RefreshCw, ArrowLeft, TrendingUp, DollarSign, Lock,
  Globe, Percent
} from 'lucide-react'
import { API_BASE } from '../lib/apiBase'

const REFRESH_INTERVAL = 12_000
const RETRY_INTERVAL   = 7_000

/* ─── Types ─────────────────────────────────────────────────────────────────── */
interface Metrics {
  total_decisions:         number
  decisions_approved:      number
  decisions_blocked:       number
  decisions_held:          number
  approval_rate:           number
  block_rate:              number
  total_volume_usd:        number
  approved_volume_usd:     number
  blocked_volume_usd:      number
  avg_peg_deviation:       number
  avg_reserve_coverage:    number
  avg_liquid_ratio:        number
  avg_crypto_exposure:     number
  avg_decision_score:      number
  avg_transaction_risk:    number
  hard_blocks:             number
  decisions_last_24h:      number
  assets_active:           number
  jurisdictions_active:    number
  simulation_cycles:       number
}

interface Decision {
  decision_id:            string
  decision_type:          string
  reserve_asset:          string
  jurisdiction:           string
  transaction_amount_usd: number
  peg_deviation_pct:      number
  reserve_coverage_ratio: number
  liquid_reserve_ratio:   number
  decision:               string
  decision_score:         number
  block_reason:           string | null
  hard_block_reason:      string | null
  transaction_risk_usd:   number
  receipt_id:             string | null
  created_at:             string
}

interface ByType {
  decision_type:    string
  total:            number
  approved:         number
  blocked:          number
  total_volume_usd: number
  avg_score:        number
  approval_rate:    number
}

interface ByAsset {
  reserve_asset:      string
  total:              number
  approved:           number
  blocked:            number
  total_volume_usd:   number
  avg_coverage:       number
  avg_liquid_ratio:   number
  avg_crypto_exposure: number
  approval_rate:      number
}

interface ByJurisdiction {
  jurisdiction:      string
  total:             number
  approved:          number
  blocked:           number
  total_volume_usd:  number
  avg_coverage:      number
  avg_peg_deviation: number
  approval_rate:     number
}

/* ─── Constants ──────────────────────────────────────────────────────────── */
const SRG_VIOLET  = '#8B5CF6'
const SRG_LIGHT   = '#A78BFA'

const ASSET_COLORS: Record<string, string> = {
  US_Treasury_Bills:  '#10B981',
  US_Treasury_Notes:  '#34D399',
  Repo_Agreements:    '#06B6D4',
  Money_Market_Funds: '#60A5FA',
  USDC:               '#3B82F6',
  Commercial_Paper:   '#F59E0B',
  ETH_Staked:         '#8B5CF6',
  BTC:                '#F97316',
}

const ASSET_ICONS: Record<string, string> = {
  US_Treasury_Bills:  '🏛️',
  US_Treasury_Notes:  '📋',
  Repo_Agreements:    '🔄',
  Money_Market_Funds: '💰',
  USDC:               '💵',
  Commercial_Paper:   '📄',
  ETH_Staked:         '⟠',
  BTC:                '₿',
}

const JURISDICTION_FLAGS: Record<string, string> = {
  EU_MiCA:   '🇪🇺',
  US_NYDFS:  '🇺🇸',
  UAE_VARA:  '🇦🇪',
  SG_MAS:    '🇸🇬',
  UK_FCA:    '🇬🇧',
  GCC:       '🌍',
}

const DECISION_TYPE_LABELS: Record<string, string> = {
  reserve_rebalancing:  'Reserve Rebalancing',
  redemption_processing:'Redemption Processing',
  collateral_adjustment:'Collateral Adjustment',
  peg_defense:          'Peg Defense',
  yield_optimization:   'Yield Optimization',
}

function fmt_usd(n: number): string {
  if (n >= 1_000_000_000) return `$${(n / 1_000_000_000).toFixed(2)}B`
  if (n >= 1_000_000)     return `$${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000)         return `$${(n / 1_000).toFixed(0)}K`
  return `$${n.toFixed(0)}`
}

function DecisionBadge({ decision }: { decision: string }) {
  const map: Record<string, { bg: string; color: string }> = {
    APPROVED: { bg: 'rgba(16,185,129,0.15)',  color: '#10B981' },
    BLOCKED:  { bg: 'rgba(239,68,68,0.15)',   color: '#EF4444' },
    HOLD:     { bg: 'rgba(245,158,11,0.15)',  color: '#F59E0B' },
  }
  const s = map[decision] || map.HOLD
  return (
    <span style={{
      padding: '3px 10px', borderRadius: 20, fontSize: 11,
      fontWeight: 700, letterSpacing: '0.08em',
      background: s.bg, color: s.color, border: `1px solid ${s.color}33`,
    }}>{decision}</span>
  )
}

function KpiCard({ label, value, sub, accent, icon: Icon }: {
  label: string; value: string; sub?: string; accent: string
  icon: React.ComponentType<{ size?: number; color?: string }>
}) {
  return (
    <div style={{
      background: 'rgba(17,24,39,0.85)', border: `1px solid ${accent}33`,
      borderRadius: 12, padding: '18px 20px',
      display: 'flex', flexDirection: 'column', gap: 6,
      boxShadow: `0 0 18px ${accent}10`,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#94A3B8', fontSize: 12 }}>
        <Icon size={14} color={accent} />
        {label}
      </div>
      <div style={{ fontSize: 26, fontWeight: 800, color: '#F1F5F9', letterSpacing: '-0.02em' }}>{value}</div>
      {sub && <div style={{ fontSize: 11, color: '#64748B' }}>{sub}</div>}
    </div>
  )
}

function SectionHeader({ title, sub }: { title: string; sub?: string }) {
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ fontSize: 15, fontWeight: 700, color: '#E2E8F0', letterSpacing: '0.02em' }}>{title}</div>
      {sub && <div style={{ fontSize: 12, color: '#64748B', marginTop: 2 }}>{sub}</div>}
    </div>
  )
}

export default function StablecoinDashboard() {
  const [metrics,      setMetrics]      = useState<Metrics | null>(null)
  const [decisions,    setDecisions]    = useState<Decision[]>([])
  const [byType,       setByType]       = useState<ByType[]>([])
  const [byAsset,      setByAsset]      = useState<ByAsset[]>([])
  const [byJurisd,     setByJurisd]     = useState<ByJurisdiction[]>([])
  const [loading,      setLoading]      = useState(true)
  const [error,        setError]        = useState<string | null>(null)
  const [lastUpdated,  setLastUpdated]  = useState<Date | null>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const fetchAll = useCallback(async () => {
    try {
      const base = `${API_BASE}/api/stablecoin`
      const [mRes, dRes, tRes, aRes, jRes] = await Promise.all([
        fetch(`${base}/metrics`),
        fetch(`${base}/live-feed`),
        fetch(`${base}/by-type`),
        fetch(`${base}/by-asset`),
        fetch(`${base}/by-jurisdiction`),
      ])
      const [m, d, t, a, j] = await Promise.all([
        mRes.json(), dRes.json(), tRes.json(), aRes.json(), jRes.json(),
      ])
      if (m.success) setMetrics(m.metrics)
      if (d.success) setDecisions(d.decisions)
      if (t.success) setByType(t.by_type)
      if (a.success) setByAsset(a.by_asset)
      if (j.success) setByJurisd(j.by_jurisdiction)
      setError(null)
      setLastUpdated(new Date())
      setLoading(false)
      timerRef.current = setTimeout(fetchAll, REFRESH_INTERVAL)
    } catch (err) {
      setError('Connecting to reserve governance engine...')
      timerRef.current = setTimeout(fetchAll, RETRY_INTERVAL)
    }
  }, [])

  useEffect(() => { fetchAll(); return () => { if (timerRef.current) clearTimeout(timerRef.current) } }, [fetchAll])

  const pageStyle: React.CSSProperties = {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #0A0B14 0%, #0D1117 50%, #0A0E1A 100%)',
    color: '#E2E8F0', fontFamily: "'Inter', sans-serif", padding: '28px 24px',
  }

  if (loading) return (
    <div style={{ ...pageStyle, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: 40, marginBottom: 16 }}>🪙</div>
        <div style={{ fontSize: 18, fontWeight: 700, color: SRG_VIOLET }}>Stablecoin Reserve Governance</div>
        <div style={{ color: '#64748B', marginTop: 8, fontSize: 13 }}>Connecting to governance engine...</div>
        <div style={{ marginTop: 24 }}>
          <RefreshCw size={20} style={{ color: SRG_VIOLET, animation: 'spin 1s linear infinite' }} />
        </div>
      </div>
    </div>
  )

  const m = metrics!
  const maxTypeVol = Math.max(...byType.map(t => t.total), 1)
  const maxAssetVol = Math.max(...byAsset.map(a => Number(a.total_volume_usd) || 0), 1)

  return (
    <div style={pageStyle}>
      <style>{`
        @keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }
        @keyframes pulse { 0%,100% { opacity:1 } 50% { opacity:0.4 } }
        * { box-sizing: border-box }
        ::-webkit-scrollbar { width: 5px } ::-webkit-scrollbar-track { background: #0A0B14 }
        ::-webkit-scrollbar-thumb { background: ${SRG_VIOLET}55; border-radius: 4px }
      `}</style>

      {/* Header */}
      <div style={{ maxWidth: 1400, margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 32 }}>
          <div>
            <Link to="/command" style={{ color: '#64748B', fontSize: 12, textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 4, marginBottom: 10 }}>
              <ArrowLeft size={12} /> Command Center
            </Link>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
              <div style={{
                width: 48, height: 48, borderRadius: 12, background: `${SRG_VIOLET}22`,
                border: `1px solid ${SRG_VIOLET}44`, display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 24,
              }}>🪙</div>
              <div>
                <div style={{ fontSize: 22, fontWeight: 800, letterSpacing: '-0.02em' }}>
                  Stablecoin Reserve Governance
                </div>
                <div style={{ fontSize: 12, color: '#64748B', marginTop: 3 }}>
                  ADR-SRG-001 · MiCA-Compliant Reserve Decision Engine · OMNIX-SRG-{'{'}12HEX{'}'}
                </div>
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#10B981', animation: 'pulse 2s ease-in-out infinite', display: 'block' }} />
              <span style={{ fontSize: 12, color: '#10B981', fontWeight: 600 }}>LIVE · 4-min cycles</span>
            </div>
            {lastUpdated && <span style={{ fontSize: 11, color: '#475569' }}>Updated {lastUpdated.toLocaleTimeString()}</span>}
            {error && <span style={{ fontSize: 11, color: '#EF4444' }}>{error}</span>}
          </div>
        </div>

        {/* KPI Row 1 */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(175px, 1fr))', gap: 14, marginBottom: 14 }}>
          <KpiCard label="Total Decisions" value={m.total_decisions.toLocaleString()} sub={`${m.simulation_cycles} cycles`} accent={SRG_VIOLET} icon={Activity} />
          <KpiCard label="Approval Rate" value={`${(m.approval_rate * 100).toFixed(1)}%`} sub={`${m.decisions_approved.toLocaleString()} approved`} accent="#10B981" icon={CheckCircle} />
          <KpiCard label="Hard Blocks" value={m.hard_blocks.toLocaleString()} sub="Peg/MiCA/AML/Sanctions" accent="#EF4444" icon={XCircle} />
          <KpiCard label="Total Volume" value={fmt_usd(m.total_volume_usd)} sub={`${fmt_usd(m.approved_volume_usd)} approved`} accent={SRG_LIGHT} icon={DollarSign} />
          <KpiCard label="Avg Peg Deviation" value={`${m.avg_peg_deviation.toFixed(3)}%`} sub="< 0.5% = healthy" accent="#F59E0B" icon={TrendingUp} />
          <KpiCard label="Avg Reserve Coverage" value={`${m.avg_reserve_coverage.toFixed(1)}%`} sub="≥ 100% required" accent="#10B981" icon={Shield} />
          <KpiCard label="Avg Liquid Ratio" value={`${m.avg_liquid_ratio.toFixed(1)}%`} sub="MiCA ≥ 60%" accent="#06B6D4" icon={Percent} />
          <KpiCard label="Last 24h" value={m.decisions_last_24h.toLocaleString()} sub={`${m.jurisdictions_active} jurisdictions`} accent="#94A3B8" icon={Globe} />
        </div>

        {/* Main Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>

          {/* By Decision Type */}
          <div style={{ background: 'rgba(17,24,39,0.85)', borderRadius: 14, padding: 22, border: `1px solid ${SRG_VIOLET}22` }}>
            <SectionHeader title="By Decision Type" sub="Governance action breakdown" />
            {byType.length === 0
              ? <div style={{ color: '#475569', fontSize: 13, textAlign: 'center', padding: '30px 0' }}>Awaiting first simulation cycle…</div>
              : byType.map(row => (
              <div key={row.decision_type} style={{ marginBottom: 14 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <span style={{ fontSize: 12, color: '#CBD5E1', fontWeight: 600 }}>
                    {DECISION_TYPE_LABELS[row.decision_type] || row.decision_type}
                  </span>
                  <div style={{ display: 'flex', gap: 10, fontSize: 11, color: '#94A3B8' }}>
                    <span style={{ color: '#10B981' }}>{row.approved} ✓</span>
                    <span style={{ color: '#EF4444' }}>{row.blocked} ✗</span>
                    <span style={{ color: '#F59E0B' }}>{(row.approval_rate * 100).toFixed(0)}%</span>
                  </div>
                </div>
                <div style={{ background: '#1E293B', borderRadius: 6, height: 7, overflow: 'hidden' }}>
                  <div style={{ height: '100%', borderRadius: 6, background: `linear-gradient(90deg, ${SRG_VIOLET}, ${SRG_LIGHT})`, width: `${(row.total / maxTypeVol) * 100}%`, transition: 'width 0.6s ease' }} />
                </div>
                <div style={{ fontSize: 10, color: '#475569', marginTop: 3 }}>{row.total} decisions · {fmt_usd(Number(row.total_volume_usd) || 0)} volume</div>
              </div>
            ))}
          </div>

          {/* By Reserve Asset */}
          <div style={{ background: 'rgba(17,24,39,0.85)', borderRadius: 14, padding: 22, border: `1px solid ${SRG_VIOLET}22` }}>
            <SectionHeader title="By Reserve Asset" sub="MiCA risk classification" />
            {byAsset.length === 0
              ? <div style={{ color: '#475569', fontSize: 13, textAlign: 'center', padding: '30px 0' }}>Awaiting first simulation cycle…</div>
              : byAsset.map(row => {
              const assetColor = ASSET_COLORS[row.reserve_asset] || '#94A3B8'
              const icon = ASSET_ICONS[row.reserve_asset] || '💎'
              const vol = Number(row.total_volume_usd) || 0
              return (
                <div key={row.reserve_asset} style={{ marginBottom: 14 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <span style={{ fontSize: 12, color: '#CBD5E1', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 5 }}>
                      <span>{icon}</span>
                      <span style={{ color: assetColor }}>{row.reserve_asset.replace(/_/g, ' ')}</span>
                    </span>
                    <div style={{ display: 'flex', gap: 10, fontSize: 11, color: '#94A3B8' }}>
                      <span style={{ color: '#10B981' }}>{row.approved} ✓</span>
                      <span style={{ color: '#EF4444' }}>{row.blocked} ✗</span>
                    </div>
                  </div>
                  <div style={{ background: '#1E293B', borderRadius: 6, height: 7, overflow: 'hidden' }}>
                    <div style={{ height: '100%', borderRadius: 6, background: assetColor, width: `${(vol / maxAssetVol) * 100}%`, transition: 'width 0.6s ease', opacity: 0.85 }} />
                  </div>
                  <div style={{ fontSize: 10, color: '#475569', marginTop: 3 }}>
                    {row.total} decisions · {fmt_usd(vol)} · Cov {Number(row.avg_coverage).toFixed(1)}%
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* By Jurisdiction */}
        <div style={{ background: 'rgba(17,24,39,0.85)', borderRadius: 14, padding: 22, border: `1px solid ${SRG_VIOLET}22`, marginBottom: 16 }}>
          <SectionHeader title="By Regulatory Jurisdiction" sub="MiCA · NYDFS · VARA · MAS · FCA · GCC — strictness-adjusted governance" />
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
            {byJurisd.length === 0
              ? <div style={{ color: '#475569', fontSize: 13 }}>Awaiting first simulation cycle…</div>
              : byJurisd.map(row => {
              const flag = JURISDICTION_FLAGS[row.jurisdiction] || '🌐'
              const apRate = (Number(row.approval_rate) * 100).toFixed(0)
              const peg = Number(row.avg_peg_deviation).toFixed(4)
              return (
                <div key={row.jurisdiction} style={{
                  background: '#0F172A', borderRadius: 10, padding: '14px 16px',
                  border: `1px solid ${SRG_VIOLET}22`,
                }}>
                  <div style={{ fontSize: 18, marginBottom: 4 }}>{flag}</div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: SRG_LIGHT }}>{row.jurisdiction.replace(/_/g, ' ')}</div>
                  <div style={{ fontSize: 11, color: '#94A3B8', marginTop: 4 }}>{row.total} decisions</div>
                  <div style={{ display: 'flex', gap: 12, marginTop: 8, fontSize: 12 }}>
                    <div>
                      <div style={{ color: '#10B981', fontWeight: 700 }}>{apRate}%</div>
                      <div style={{ color: '#475569', fontSize: 10 }}>approval</div>
                    </div>
                    <div>
                      <div style={{ color: '#F59E0B', fontWeight: 700 }}>{peg}%</div>
                      <div style={{ color: '#475569', fontSize: 10 }}>avg peg dev</div>
                    </div>
                    <div>
                      <div style={{ color: SRG_LIGHT, fontWeight: 700 }}>{fmt_usd(Number(row.total_volume_usd) || 0)}</div>
                      <div style={{ color: '#475569', fontSize: 10 }}>volume</div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Live Decision Feed */}
        <div style={{ background: 'rgba(17,24,39,0.85)', borderRadius: 14, padding: 22, border: `1px solid ${SRG_VIOLET}22` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <SectionHeader title="Live Reserve Decision Feed" sub="Last 12 decisions · Auto-refresh every 12s" />
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <RefreshCw size={12} style={{ color: SRG_VIOLET, animation: 'spin 3s linear infinite' }} />
              <span style={{ fontSize: 11, color: '#475569' }}>LIVE</span>
            </div>
          </div>

          {decisions.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 0', color: '#475569' }}>
              <Lock size={28} style={{ margin: '0 auto 12px', color: SRG_VIOLET, opacity: 0.4 }} />
              <div>First cycle generating stablecoin reserve decisions…</div>
              <div style={{ fontSize: 12, marginTop: 4 }}>Cycle interval: 4 minutes</div>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #1E293B' }}>
                    {['Decision ID', 'Type', 'Asset', 'Jurisdiction', 'Amount', 'Peg Dev', 'Coverage', 'Verdict', 'Score', 'Receipt'].map(h => (
                      <th key={h} style={{ padding: '8px 10px', textAlign: 'left', color: '#64748B', fontWeight: 600, fontSize: 11, whiteSpace: 'nowrap' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {decisions.map(d => {
                    const assetColor = ASSET_COLORS[d.reserve_asset] || '#94A3B8'
                    const flag = JURISDICTION_FLAGS[d.jurisdiction] || '🌐'
                    const pegBad = d.peg_deviation_pct > 1.0
                    return (
                      <tr key={d.decision_id} style={{ borderBottom: '1px solid #0F172A', transition: 'background 0.15s' }}
                        onMouseEnter={e => (e.currentTarget.style.background = '#0F172A')}
                        onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                      >
                        <td style={{ padding: '9px 10px', color: '#94A3B8', fontFamily: 'monospace', fontSize: 10 }}>
                          {d.decision_id.slice(0, 18)}…
                        </td>
                        <td style={{ padding: '9px 10px' }}>
                          <span style={{ color: SRG_LIGHT, fontWeight: 600, fontSize: 11 }}>
                            {DECISION_TYPE_LABELS[d.decision_type] || d.decision_type}
                          </span>
                        </td>
                        <td style={{ padding: '9px 10px' }}>
                          <span style={{ color: assetColor, fontWeight: 600 }}>
                            {ASSET_ICONS[d.reserve_asset] || '💎'} {d.reserve_asset.replace(/_/g, ' ')}
                          </span>
                        </td>
                        <td style={{ padding: '9px 10px' }}>
                          {flag} <span style={{ color: '#94A3B8' }}>{d.jurisdiction.replace(/_/g, ' ')}</span>
                        </td>
                        <td style={{ padding: '9px 10px', color: '#E2E8F0', fontWeight: 600 }}>
                          {fmt_usd(d.transaction_amount_usd)}
                        </td>
                        <td style={{ padding: '9px 10px', color: pegBad ? '#EF4444' : '#10B981', fontWeight: 600 }}>
                          {d.peg_deviation_pct.toFixed(3)}%
                          {pegBad && <AlertTriangle size={11} style={{ marginLeft: 4, display: 'inline' }} />}
                        </td>
                        <td style={{ padding: '9px 10px', color: d.reserve_coverage_ratio < 102 ? '#F59E0B' : '#10B981', fontWeight: 600 }}>
                          {d.reserve_coverage_ratio.toFixed(1)}%
                        </td>
                        <td style={{ padding: '9px 10px' }}>
                          <DecisionBadge decision={d.decision} />
                        </td>
                        <td style={{ padding: '9px 10px', color: '#94A3B8' }}>
                          {(d.decision_score || 0).toFixed(1)}
                        </td>
                        <td style={{ padding: '9px 10px' }}>
                          {d.receipt_id ? (
                            <Link to={`/verify/${d.receipt_id}`} style={{ color: SRG_VIOLET, fontSize: 10, fontFamily: 'monospace', textDecoration: 'none' }}>
                              {d.receipt_id.slice(0, 16)}…
                            </Link>
                          ) : (
                            <span style={{ color: '#334155', fontSize: 10 }}>—</span>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* ADR Footer */}
        <div style={{ marginTop: 24, textAlign: 'center', color: '#334155', fontSize: 11 }}>
          OMNIX Stablecoin Reserve Governance · ADR-SRG-001 · Receipts: OMNIX-SRG-{'{12HEX}'}
          &nbsp;·&nbsp; MiCA Art. 36 Compliant · VARA · MAS · NYDFS · FCA
          &nbsp;·&nbsp; <Link to="/governance-demo-stablecoin" style={{ color: SRG_VIOLET, textDecoration: 'none' }}>Interactive Demo →</Link>
        </div>
      </div>
    </div>
  )
}
