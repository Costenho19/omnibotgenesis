import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield, TrendingUp, TrendingDown, AlertTriangle, CheckCircle, XCircle,
  Activity, BarChart3, DollarSign, Clock, RefreshCw, ExternalLink,
  Building2, Landmark, Globe, Zap, Lock, ChevronRight, Info,
  ArrowUpRight, ArrowDownRight, Layers, FileCheck
} from 'lucide-react'

const API_BASE = ''
const REFRESH_INTERVAL = 30_000

interface Metrics {
  total_applications: number
  total_approved: number
  total_blocked: number
  total_hold: number
  approval_rate: number
  total_amount_evaluated_aed: number
  total_amount_approved_aed: number
  total_amount_blocked_aed: number
  capital_protected_estimate_aed: number
  avg_probability_score: number
  avg_risk_exposure: number
  sharia_compliance_rate: number
  sharia_violations: number
  simulation_cycles: number
  last_evaluation: string
}

interface MacroData {
  credit_index: number
  stress_level: string
  fed_funds_rate: number
  volatility: number
}

interface Activity24h {
  applications: number
  approved: number
  blocked: number
}

interface Application {
  application_id: string
  submitted_at: string
  applicant_type: string
  sector: string
  requested_amount: number
  currency: string
  tenor_months: number
  financing_type: string
  credit_score: number
  debt_service_ratio: number
  sharia_compliant: boolean
  decision: string
  receipt_id: string
  blocked_at_checkpoint: string
  block_reason: string
  checkpoints_passed: number
  checkpoints_total: number
  signal_probability_score: number
  signal_risk_exposure: number
}

interface SectorData {
  sector: string
  total: number
  approved: number
  blocked: number
  approval_rate: number
  total_amount_aed: number
  avg_probability: number
}

function formatAED(amount: number): string {
  if (amount >= 1_000_000_000) return `AED ${(amount / 1_000_000_000).toFixed(1)}B`
  if (amount >= 1_000_000) return `AED ${(amount / 1_000_000).toFixed(1)}M`
  if (amount >= 1_000) return `AED ${(amount / 1_000).toFixed(0)}K`
  return `AED ${amount.toFixed(0)}`
}

function timeAgo(isoStr: string): string {
  if (!isoStr) return '—'
  const diff = Date.now() - new Date(isoStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

function StressLevelBadge({ level }: { level: string }) {
  const configs: Record<string, { color: string; bg: string }> = {
    LOW: { color: 'text-emerald-400', bg: 'bg-emerald-400/10 border-emerald-400/30' },
    MODERATE: { color: 'text-amber-400', bg: 'bg-amber-400/10 border-amber-400/30' },
    HIGH: { color: 'text-orange-400', bg: 'bg-orange-400/10 border-orange-400/30' },
    EXTREME: { color: 'text-red-400', bg: 'bg-red-400/10 border-red-400/30' },
  }
  const cfg = configs[level] || configs.MODERATE
  return (
    <span className={`px-2 py-0.5 rounded border text-xs font-semibold ${cfg.bg} ${cfg.color}`}>
      {level}
    </span>
  )
}

function DecisionBadge({ decision }: { decision: string }) {
  if (decision === 'APPROVED') return (
    <span className="flex items-center gap-1 text-emerald-400 font-semibold text-xs">
      <CheckCircle size={12} /> APPROVED
    </span>
  )
  if (decision === 'BLOCKED') return (
    <span className="flex items-center gap-1 text-red-400 font-semibold text-xs">
      <XCircle size={12} /> BLOCKED
    </span>
  )
  return (
    <span className="flex items-center gap-1 text-amber-400 font-semibold text-xs">
      <AlertTriangle size={12} /> HOLD
    </span>
  )
}

function ScoreBar({ value, max = 100, color = 'bg-amber-400' }: { value: number; max?: number; color?: string }) {
  const pct = Math.min(100, (value / max) * 100)
  return (
    <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
      <div className={`h-full rounded-full transition-all duration-500 ${color}`} style={{ width: `${pct}%` }} />
    </div>
  )
}

function KPICard({
  label, value, sub, icon: Icon, trend, color = 'text-amber-400'
}: {
  label: string; value: string; sub?: string; icon: React.ElementType;
  trend?: 'up' | 'down' | 'neutral'; color?: string
}) {
  return (
    <div className="bg-white/[0.03] border border-white/10 rounded-xl p-5 hover:border-amber-400/30 transition-all">
      <div className="flex items-start justify-between mb-3">
        <div className={`p-2 rounded-lg bg-white/5 ${color}`}>
          <Icon size={16} />
        </div>
        {trend && (
          <div className={`flex items-center gap-1 text-xs ${
            trend === 'up' ? 'text-emerald-400' :
            trend === 'down' ? 'text-red-400' : 'text-white/40'
          }`}>
            {trend === 'up' ? <ArrowUpRight size={12} /> :
             trend === 'down' ? <ArrowDownRight size={12} /> : null}
          </div>
        )}
      </div>
      <div className={`text-2xl font-bold mb-1 ${color}`}>{value}</div>
      <div className="text-xs text-white/50 font-medium">{label}</div>
      {sub && <div className="text-xs text-white/30 mt-1">{sub}</div>}
    </div>
  )
}

export default function CreditLiveDashboard() {
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [macro, setMacro] = useState<MacroData | null>(null)
  const [activity, setActivity] = useState<Activity24h | null>(null)
  const [applications, setApplications] = useState<Application[]>([])
  const [sectors, setSectors] = useState<SectorData[]>([])
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)

  const fetchAll = useCallback(async () => {
    setRefreshing(true)
    try {
      const [metricsRes, appsRes, sectorsRes] = await Promise.all([
        fetch(`${API_BASE}/api/credit/metrics`),
        fetch(`${API_BASE}/api/credit/applications?limit=25`),
        fetch(`${API_BASE}/api/credit/sectors`),
      ])

      if (metricsRes.ok) {
        const d = await metricsRes.json()
        if (d.status === 'ok') {
          setMetrics(d.metrics)
          setMacro(d.macro)
          setActivity(d.activity_24h)
        }
      }
      if (appsRes.ok) {
        const d = await appsRes.json()
        if (d.status === 'ok') setApplications(d.applications)
      }
      if (sectorsRes.ok) {
        const d = await sectorsRes.json()
        if (d.status === 'ok') setSectors(d.sectors)
      }

      setLastRefresh(new Date())
      setError(null)
    } catch (e) {
      setError('Unable to connect to governance engine')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    fetchAll()
    const interval = setInterval(fetchAll, REFRESH_INTERVAL)
    return () => clearInterval(interval)
  }, [fetchAll])

  const hasData = metrics && metrics.total_applications > 0

  return (
    <div className="min-h-screen bg-[#050508] text-white">
      {/* Header */}
      <div className="border-b border-white/[0.06]">
        <div className="max-w-7xl mx-auto px-6 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link to="/" className="text-white/30 hover:text-white/60 transition-colors">
                <Shield size={20} className="text-amber-400" />
              </Link>
              <div className="w-px h-5 bg-white/10" />
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="text-lg font-bold text-white">
                    Islamic Credit Governance
                  </h1>
                  <span className="px-2 py-0.5 rounded text-xs font-semibold bg-amber-400/15 text-amber-400 border border-amber-400/20">
                    LIVE
                  </span>
                  <span className="px-2 py-0.5 rounded text-xs text-white/30 bg-white/5 border border-white/10">
                    ADR-052
                  </span>
                </div>
                <p className="text-xs text-white/40 mt-0.5">
                  OMNIX Decision Governance Infrastructure — Islamic Finance Vertical
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-xs text-white/30">Last refresh</div>
                <div className="text-xs text-white/60 font-mono">
                  {lastRefresh.toLocaleTimeString()}
                </div>
              </div>
              <button
                onClick={fetchAll}
                disabled={refreshing}
                className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white/60 hover:text-white hover:border-amber-400/40 transition-all text-sm disabled:opacity-40"
              >
                <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
                Refresh
              </button>
              <Link
                to="/"
                className="text-xs text-white/40 hover:text-white/70 transition-colors"
              >
                ← Back
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">

        {/* Error Banner */}
        {error && (
          <div className="flex items-center gap-3 p-4 rounded-xl bg-red-400/10 border border-red-400/30 text-red-400 text-sm">
            <AlertTriangle size={16} />
            <span>{error}</span>
            <span className="text-red-400/60 ml-auto text-xs">Engine may be starting up — auto-retrying</span>
          </div>
        )}

        {/* Macro Conditions Strip */}
        {macro && (
          <div className="flex items-center gap-6 p-4 rounded-xl bg-white/[0.02] border border-white/[0.06]">
            <div className="flex items-center gap-2 text-xs text-white/50">
              <Globe size={13} className="text-amber-400/60" />
              <span>Macro Conditions</span>
            </div>
            <div className="w-px h-4 bg-white/10" />
            <div className="flex items-center gap-1 text-xs">
              <span className="text-white/40">Fed Funds Rate</span>
              <span className="text-white/80 font-mono font-semibold ml-1">
                {macro.fed_funds_rate?.toFixed(2)}%
              </span>
            </div>
            <div className="flex items-center gap-1 text-xs">
              <span className="text-white/40">Credit Index</span>
              <span className="text-white/80 font-mono font-semibold ml-1">
                {macro.credit_index?.toFixed(1)}/100
              </span>
            </div>
            <div className="flex items-center gap-1 text-xs">
              <span className="text-white/40">Volatility</span>
              <span className="text-white/80 font-mono font-semibold ml-1">
                {macro.volatility?.toFixed(1)}
              </span>
            </div>
            <div className="flex items-center gap-2 text-xs ml-auto">
              <span className="text-white/40">Market Stress</span>
              <StressLevelBadge level={macro.stress_level || 'MODERATE'} />
            </div>
          </div>
        )}

        {/* KPI Grid */}
        <div>
          <h2 className="text-sm font-semibold text-white/50 uppercase tracking-wider mb-4">
            Governance KPIs — Live Engine Metrics
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KPICard
              label="Total Applications"
              value={loading ? '—' : (metrics?.total_applications ?? 0).toLocaleString()}
              sub={`${activity?.applications ?? 0} in last 24h`}
              icon={FileCheck}
              color="text-amber-400"
            />
            <KPICard
              label="Approval Rate"
              value={loading ? '—' : `${metrics?.approval_rate?.toFixed(1) ?? 0}%`}
              sub={`${metrics?.total_approved ?? 0} approved`}
              icon={CheckCircle}
              color="text-emerald-400"
            />
            <KPICard
              label="Capital Protected"
              value={loading ? '—' : formatAED(metrics?.capital_protected_estimate_aed ?? 0)}
              sub="Est. default risk avoided"
              icon={Lock}
              color="text-blue-400"
            />
            <KPICard
              label="Sharia Compliance"
              value={loading ? '—' : `${metrics?.sharia_compliance_rate?.toFixed(1) ?? 100}%`}
              sub="Islamic finance screening"
              icon={Landmark}
              color="text-purple-400"
            />
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
            <KPICard
              label="Amount Evaluated"
              value={loading ? '—' : formatAED(metrics?.total_amount_evaluated_aed ?? 0)}
              sub="Total financing reviewed"
              icon={DollarSign}
              color="text-amber-400"
            />
            <KPICard
              label="Amount Approved"
              value={loading ? '—' : formatAED(metrics?.total_amount_approved_aed ?? 0)}
              sub="Financing authorized"
              icon={TrendingUp}
              color="text-emerald-400"
            />
            <KPICard
              label="Amount Blocked"
              value={loading ? '—' : formatAED(metrics?.total_amount_blocked_aed ?? 0)}
              sub="High-risk financing vetoed"
              icon={TrendingDown}
              color="text-red-400"
            />
            <KPICard
              label="Simulation Cycles"
              value={loading ? '—' : (metrics?.simulation_cycles ?? 0).toLocaleString()}
              sub="Every 5 min, 24/7"
              icon={Activity}
              color="text-cyan-400"
            />
          </div>
        </div>

        {/* 2-column: Pipeline Visual + Sector Breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* 8-Checkpoint Pipeline */}
          <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-6">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h3 className="font-semibold text-white">8-Checkpoint Pipeline</h3>
                <p className="text-xs text-white/40 mt-0.5">Same engine as trading vertical</p>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                <span className="text-xs text-white/40">Active</span>
              </div>
            </div>

            <div className="space-y-2.5">
              {[
                { id: 'CP-0', name: 'Signal Integrity', icon: Shield, desc: 'Data quality & completeness', credit: 'Application completeness score' },
                { id: 'CP-1', name: 'Probability Check', icon: BarChart3, desc: 'Creditworthiness probability ≥ 50', credit: 'Credit score + DSR + collateral' },
                { id: 'CP-2', name: 'Risk Limits', icon: AlertTriangle, desc: 'Default risk exposure ≤ 65', credit: 'PD × LGD calculation' },
                { id: 'CP-3', name: 'Signal Coherence', icon: Layers, desc: 'Indicator agreement ≥ 55', credit: 'Credit signals consistency' },
                { id: 'CP-4', name: 'Trend Persistence', icon: TrendingUp, desc: 'Macro stability ≥ 50', credit: 'FFR + credit spread stability' },
                { id: 'CP-5', name: 'Stress Resilience', icon: Zap, desc: 'Income shock test ≥ 35', credit: '-20% income scenario' },
                { id: 'CP-6', name: 'Sharia Compliance', icon: Landmark, desc: 'Islamic finance principles', credit: 'Halal + no Riba + Gharar limit' },
                { id: 'CP-7', name: 'Temporal Coherence', icon: Clock, desc: 'Macro freshness ≥ 45', credit: 'Data recency & consistency' },
              ].map((cp, i) => (
                <div key={cp.id} className="flex items-center gap-3 p-3 rounded-lg bg-white/[0.03] border border-white/[0.05] hover:border-amber-400/20 transition-all group">
                  <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-amber-400/10 text-amber-400 flex-shrink-0">
                    <cp.icon size={14} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-white/30">{cp.id}</span>
                      <span className="text-sm font-medium text-white/80">{cp.name}</span>
                    </div>
                    <div className="text-xs text-white/40 truncate">{cp.credit}</div>
                  </div>
                  <div className="flex-shrink-0">
                    <div className="w-2 h-2 rounded-full bg-emerald-400/60" />
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-4 p-3 rounded-lg bg-amber-400/5 border border-amber-400/15">
              <div className="flex items-start gap-2">
                <Info size={12} className="text-amber-400/70 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-white/40 leading-relaxed">
                  Same governance engine as the trading vertical — CP-6 Sharia Gate is unique to this
                  Islamic finance domain. Every decision generates a PQC-signed receipt verifiable
                  at omnixquantum.net/verify
                </p>
              </div>
            </div>
          </div>

          {/* Sector Breakdown */}
          <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-6">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h3 className="font-semibold text-white">Sector Analysis</h3>
                <p className="text-xs text-white/40 mt-0.5">Governance decisions by industry</p>
              </div>
              <Building2 size={16} className="text-white/20" />
            </div>

            {sectors.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-48 text-white/20">
                <Activity size={24} className="mb-2" />
                <p className="text-sm">Collecting sector data...</p>
                <p className="text-xs mt-1">Engine cycles every 5 minutes</p>
              </div>
            ) : (
              <div className="space-y-3">
                {sectors.slice(0, 8).map((s) => (
                  <div key={s.sector} className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-white/70 capitalize font-medium">
                        {s.sector.replace(/_/g, ' ')}
                      </span>
                      <div className="flex items-center gap-3">
                        <span className="text-white/40">{s.total} apps</span>
                        <span className={`font-semibold ${
                          s.approval_rate >= 60 ? 'text-emerald-400' :
                          s.approval_rate >= 40 ? 'text-amber-400' : 'text-red-400'
                        }`}>
                          {s.approval_rate?.toFixed(0)}%
                        </span>
                      </div>
                    </div>
                    <div className="flex gap-1 h-2">
                      <div
                        className="bg-emerald-400/60 rounded-l"
                        style={{ width: `${s.total > 0 ? (s.approved / s.total) * 100 : 0}%` }}
                      />
                      <div
                        className="bg-red-400/60 rounded-r"
                        style={{ width: `${s.total > 0 ? (s.blocked / s.total) * 100 : 0}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-xs text-white/25">
                      <span>{formatAED(s.total_amount_aed)}</span>
                      <span>avg prob. {s.avg_probability?.toFixed(0)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Live Application Feed */}
        <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="font-semibold text-white">Live Application Feed</h3>
              <p className="text-xs text-white/40 mt-0.5">
                Real governance decisions — each receipt cryptographically signed
              </p>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs text-white/40">
                {applications.length} loaded
              </span>
            </div>
          </div>

          {applications.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-32 text-white/20">
              <Clock size={24} className="mb-2" />
              <p className="text-sm">Waiting for engine cycles...</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-white/30 border-b border-white/[0.06]">
                    <th className="text-left pb-3 pr-4 font-medium">Application ID</th>
                    <th className="text-left pb-3 pr-4 font-medium">Type</th>
                    <th className="text-left pb-3 pr-4 font-medium">Sector</th>
                    <th className="text-right pb-3 pr-4 font-medium">Amount</th>
                    <th className="text-center pb-3 pr-4 font-medium">Credit</th>
                    <th className="text-center pb-3 pr-4 font-medium">Sharia</th>
                    <th className="text-center pb-3 pr-4 font-medium">CP Pass</th>
                    <th className="text-center pb-3 pr-4 font-medium">Decision</th>
                    <th className="text-left pb-3 font-medium">Time</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.04]">
                  {applications.map((app) => (
                    <tr key={app.application_id} className="hover:bg-white/[0.02] transition-colors group">
                      <td className="py-3 pr-4">
                        <div className="font-mono text-white/50 group-hover:text-white/80 transition-colors">
                          {app.application_id.split('-').slice(0, 2).join('-')}
                        </div>
                        {app.receipt_id && (
                          <Link
                            to={`/verify/${app.receipt_id}`}
                            className="flex items-center gap-1 text-amber-400/50 hover:text-amber-400 transition-colors mt-0.5"
                          >
                            <span className="font-mono text-[10px]">View Receipt</span>
                            <ExternalLink size={9} />
                          </Link>
                        )}
                      </td>
                      <td className="py-3 pr-4 text-white/60 capitalize">{app.applicant_type}</td>
                      <td className="py-3 pr-4 text-white/60 capitalize">
                        {app.sector?.replace(/_/g, ' ')}
                      </td>
                      <td className="py-3 pr-4 text-right font-mono text-white/70 whitespace-nowrap">
                        {formatAED(app.requested_amount)}
                      </td>
                      <td className="py-3 pr-4 text-center">
                        <span className={`font-semibold ${
                          app.credit_score >= 700 ? 'text-emerald-400' :
                          app.credit_score >= 600 ? 'text-amber-400' : 'text-red-400'
                        }`}>
                          {app.credit_score?.toFixed(0)}
                        </span>
                      </td>
                      <td className="py-3 pr-4 text-center">
                        {app.sharia_compliant
                          ? <CheckCircle size={13} className="text-emerald-400 mx-auto" />
                          : <XCircle size={13} className="text-red-400 mx-auto" />
                        }
                      </td>
                      <td className="py-3 pr-4 text-center">
                        <span className={`font-mono font-semibold ${
                          (app.checkpoints_passed || 0) >= 7 ? 'text-emerald-400' :
                          (app.checkpoints_passed || 0) >= 5 ? 'text-amber-400' : 'text-red-400'
                        }`}>
                          {app.checkpoints_passed ?? '—'}/{app.checkpoints_total ?? 8}
                        </span>
                      </td>
                      <td className="py-3 pr-4 text-center">
                        <DecisionBadge decision={app.decision} />
                      </td>
                      <td className="py-3 text-white/30">
                        {timeAgo(app.submitted_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Footer — Transparency */}
        <div className="flex items-start gap-4 p-5 rounded-xl bg-white/[0.02] border border-white/[0.05]">
          <Info size={14} className="text-white/30 mt-0.5 flex-shrink-0" />
          <div className="space-y-1.5">
            <p className="text-xs text-white/40 leading-relaxed">
              <span className="text-white/60 font-semibold">Simulation Transparency:</span>{' '}
              This engine generates synthetic Islamic finance applications calibrated to UAE/GCC market
              parameters (credit scores, DSR ratios, collateral types, financing amounts). Macroeconomic
              signals (Federal Funds Rate, credit spreads) are sourced from real APIs. The governance
              pipeline, all 8 checkpoints, and every PQC-signed receipt are fully real and production-grade.
            </p>
            <p className="text-xs text-white/30 leading-relaxed">
              This vertical demonstrates how the same OMNIX Decision Governance Infrastructure adapts
              to any domain. Transition from simulation to live bank applications requires only a
              data source swap — the governance engine is unchanged.
            </p>
          </div>
        </div>

      </div>
    </div>
  )
}
