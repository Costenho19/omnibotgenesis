import { useState, useEffect, useCallback, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield, AlertTriangle, CheckCircle, XCircle, Activity,
  Clock, RefreshCw, Globe, Zap, Lock,
  Stethoscope, Brain, Monitor, Cpu, TrendingUp,
  ArrowLeft, FileCheck, Eye, BarChart3
} from 'lucide-react'
import { API_BASE } from '../lib/apiBase'

const REFRESH_INTERVAL = 10_000
const RETRY_INTERVAL = 6_000

interface Metrics {
  total_decisions: number
  decisions_approved: number
  decisions_blocked: number
  decisions_held: number
  approval_rate: number
  block_rate: number
  avg_diagnostic_confidence: number
  avg_patient_risk: number
  avg_decision_score: number
  avg_trajectory_score: number
  decisions_last_24h: number
  active_devices: number
  safety_blocks: number
  simulation_cycles: number
}

interface MedDecision {
  decision_id: string
  device_id: string
  device_type: string
  decision_type: string
  patient_profile: string
  jurisdiction: string
  sensor_confidence: number
  diagnostic_confidence: number
  patient_risk_score: number
  decision: string
  decision_score: number
  block_reason: string | null
  receipt_id: string
  probability_score: number
  risk_exposure: number
  signal_coherence: number
  trend_persistence: number
  stress_resilience: number
  logic_consistency: number
  trajectory_score: number
  created_at: string
}

interface ByType {
  decision_type: string
  total: number
  approved: number
  blocked: number
  avg_confidence: number
  avg_risk: number
  approval_rate: number
}

interface ByJurisdiction {
  jurisdiction: string
  total: number
  approved: number
  blocked: number
  avg_score: number
  approval_rate: number
}

const JX_FLAGS: Record<string, string> = {
  UAE: '🇦🇪', EU: '🇪🇺', USA: '🇺🇸', UK: '🇬🇧'
}

const DECISION_TYPE_LABEL: Record<string, string> = {
  rehabilitation_guidance: 'Rehab Guidance',
  diagnostic_alert: 'Diagnostic Alert',
  monitoring_alert: 'Monitoring Alert',
  therapeutic_recommendation: 'Therapeutic Rec.',
  surgical_clearance: 'Surgical Clearance',
}

const DEVICE_ICON: Record<string, React.ReactNode> = {
  Wearable: <Activity size={10} />,
  Clinical_AI: <Brain size={10} />,
  Monitoring_System: <Monitor size={10} />,
  Surgical_Robot: <Cpu size={10} />,
}

function DecisionBadge({ decision }: { decision: string }) {
  const cfg = {
    APPROVED: { bg: 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400', icon: <CheckCircle size={11} /> },
    BLOCKED: { bg: 'bg-red-500/15 border-red-500/30 text-red-400', icon: <XCircle size={11} /> },
    HOLD: { bg: 'bg-amber-500/15 border-amber-500/30 text-amber-400', icon: <Clock size={11} /> },
  }[decision] ?? { bg: 'bg-white/10 border-white/20 text-white/60', icon: null }
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-[10px] font-medium ${cfg.bg}`}>
      {cfg.icon}{decision}
    </span>
  )
}

function SignalBar({ label, value, invert = false }: { label: string; value: number; invert?: boolean }) {
  const pct = Math.max(0, Math.min(100, value))
  const displayPct = invert ? 100 - pct : pct
  const color = displayPct >= 70 ? 'bg-emerald-500' : displayPct >= 45 ? 'bg-amber-500' : 'bg-red-500'
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[10px] text-white/50">
        <span>{label}</span>
        <span className="text-white/70">{pct.toFixed(0)}</span>
      </div>
      <div className="h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-700 ${color}`}
          style={{ width: `${displayPct}%` }} />
      </div>
    </div>
  )
}

export default function MedicalDashboard() {
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [decisions, setDecisions] = useState<MedDecision[]>([])
  const [byType, setByType] = useState<ByType[]>([])
  const [byJurisdiction, setByJurisdiction] = useState<ByJurisdiction[]>([])
  const [loading, setLoading] = useState(true)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)
  const [retrying, setRetrying] = useState(false)
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const fetchAll = useCallback(async () => {
    try {
      const [mRes, dRes, tRes, jRes] = await Promise.all([
        fetch(`${API_BASE}/api/medical/metrics`),
        fetch(`${API_BASE}/api/medical/decisions?limit=30`),
        fetch(`${API_BASE}/api/medical/by-type`),
        fetch(`${API_BASE}/api/medical/by-jurisdiction`),
      ])

      if (!mRes.ok || mRes.headers.get('content-type')?.includes('text/html')) {
        throw new Error(`HTTP ${mRes.status}`)
      }

      const [md, dd, td, jd] = await Promise.all([
        mRes.json(), dRes.json(), tRes.json(), jRes.json()
      ])

      if (md.success) { setMetrics(md.metrics); setRetrying(false) }
      if (dd.success) setDecisions(dd.decisions || [])
      if (td.success) setByType(td.by_type || [])
      if (jd.success) setByJurisdiction(jd.by_jurisdiction || [])
      setLastRefresh(new Date())
    } catch (_e) {
      setRetrying(true)
      if (retryRef.current) clearTimeout(retryRef.current)
      retryRef.current = setTimeout(() => fetchAll(), RETRY_INTERVAL)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAll()
    const iv = setInterval(fetchAll, REFRESH_INTERVAL)
    return () => { clearInterval(iv); if (retryRef.current) clearTimeout(retryRef.current) }
  }, [fetchAll])

  const m = metrics

  return (
    <div className="min-h-screen bg-[#080B10] text-white font-sans">
      {/* Header */}
      <div className="border-b border-white/[0.06] bg-[#080B10]/95 backdrop-blur-sm sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <img src="/omnix_logo.png" alt="OMNIX" className="h-7 w-auto opacity-90" />
            <div className="w-px h-5 bg-white/10" />
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-white">Medical AI Governance</span>
                <span className="px-2 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/25 text-emerald-400 text-[10px] font-medium">LIVE</span>
                <span className="px-2 py-0.5 rounded bg-white/[0.05] border border-white/10 text-white/40 text-[10px]">ADR-078</span>
              </div>
              <p className="text-[11px] text-white/35 mt-0.5">OMNIX Decision Governance Infrastructure — Clinical AI Vertical</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right hidden sm:block">
              <div className="text-[10px] text-white/30">Last refresh</div>
              <div className="text-xs text-white/60 font-mono">
                {lastRefresh ? lastRefresh.toLocaleTimeString() : '--:--:--'}
              </div>
            </div>
            <button onClick={fetchAll}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/[0.04] border border-white/[0.08] hover:bg-white/[0.08] transition-colors text-xs text-white/60">
              <RefreshCw size={12} className={retrying ? 'animate-spin' : ''} />Refresh
            </button>
            <Link to="/"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/[0.04] border border-white/[0.08] hover:bg-white/[0.08] transition-colors text-xs text-white/60">
              <ArrowLeft size={12} />Back
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">


        {/* KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            {
              icon: <FileCheck size={18} className="text-rose-400" />,
              label: 'Total Decisions Evaluated', sub: `${m?.decisions_last_24h ?? 0} in last 24h`,
              value: loading ? '—' : (m?.total_decisions ?? 0).toLocaleString(),
            },
            {
              icon: <CheckCircle size={18} className="text-emerald-400" />,
              label: 'Approval Rate', sub: `${m?.decisions_approved ?? 0} approved`,
              value: loading ? '—' : `${((m?.approval_rate ?? 0) * 100).toFixed(1)}%`,
              valueClass: 'text-emerald-400',
            },
            {
              icon: <Brain size={18} className="text-violet-400" />,
              label: 'Avg Clinical Confidence', sub: 'Diagnostic AI confidence score',
              value: loading ? '—' : `${(m?.avg_diagnostic_confidence ?? 0).toFixed(1)}%`,
              valueClass: 'text-violet-400',
            },
            {
              icon: <AlertTriangle size={18} className="text-red-400" />,
              label: 'Safety Blocks', sub: `Avg fraud score ${(m?.avg_patient_risk ?? 0).toFixed(1)}`,
              value: loading ? '—' : (m?.safety_blocks ?? 0).toLocaleString(),
              valueClass: 'text-red-400',
            },
          ].map((card, i) => (
            <div key={i} className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-5">
              <div className="flex items-center gap-2 mb-3">
                {card.icon}
                <span className="text-xs text-white/40 font-medium">{card.label}</span>
              </div>
              <div className={`text-2xl font-bold tracking-tight ${card.valueClass ?? 'text-white'}`}>
                {card.value}
              </div>
              <div className="text-[11px] text-white/30 mt-1">{card.sub}</div>
            </div>
          ))}
        </div>

        {/* Secondary metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Total Approved', value: (m?.decisions_approved ?? 0).toLocaleString(), color: 'text-emerald-400' },
            { label: 'Total Blocked', value: (m?.decisions_blocked ?? 0).toLocaleString(), color: 'text-red-400' },
            { label: 'Avg Decision Score', value: `${(m?.avg_decision_score ?? 0).toFixed(1)}/100`, color: 'text-rose-400' },
            { label: 'Simulation Cycles', value: (m?.simulation_cycles ?? 0).toLocaleString(), color: 'text-blue-400' },
          ].map((item, i) => (
            <div key={i} className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-4 flex items-center justify-between">
              <span className="text-xs text-white/40">{item.label}</span>
              <span className={`text-sm font-semibold ${item.color}`}>{loading ? '—' : item.value}</span>
            </div>
          ))}
        </div>

        {/* By Decision Type + By Jurisdiction */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* By Decision Type */}
          <div className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-6">
            <div className="flex items-center gap-2 mb-5">
              <BarChart3 size={15} className="text-rose-400" />
              <span className="text-sm font-medium text-white/80">By Decision Type</span>
            </div>
            <div className="space-y-3">
              {byType.length === 0 ? (
                <div className="text-center py-8 text-white/20 text-sm">Collecting data...</div>
              ) : byType.map(t => (
                <div key={t.decision_type} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-rose-400/60" />
                      <span className="text-white/70">{DECISION_TYPE_LABEL[t.decision_type] || t.decision_type}</span>
                      <span className="text-white/25">{t.total}</span>
                    </div>
                    <div className="flex items-center gap-3 text-white/40">
                      <span className="text-emerald-400/80">{(Number(t.approval_rate) * 100).toFixed(0)}% pass</span>
                      <span>Conf: {Number(t.avg_confidence).toFixed(0)}%</span>
                    </div>
                  </div>
                  <div className="h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
                    <div className="h-full bg-rose-400/50 rounded-full transition-all duration-700"
                      style={{ width: `${Number(t.approval_rate) * 100}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* By Jurisdiction */}
          <div className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-6">
            <div className="flex items-center gap-2 mb-5">
              <Globe size={15} className="text-blue-400" />
              <span className="text-sm font-medium text-white/80">By Jurisdiction</span>
            </div>
            <div className="space-y-2">
              {byJurisdiction.length === 0 ? (
                <div className="text-center py-8 text-white/20 text-sm">Collecting data...</div>
              ) : byJurisdiction.map(j => (
                <div key={j.jurisdiction} className="flex items-center gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                  <span className="text-lg">{JX_FLAGS[j.jurisdiction] ?? '🌐'}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-white/70">{j.jurisdiction}</span>
                      <span className="text-xs text-white/40">{j.total} decisions</span>
                    </div>
                    <div className="h-1 bg-white/[0.04] rounded-full overflow-hidden">
                      <div className="h-full bg-rose-400/50 rounded-full"
                        style={{ width: `${Number(j.approval_rate) * 100}%` }} />
                    </div>
                  </div>
                  <div className="text-right text-xs">
                    <div className="text-emerald-400/80">{(Number(j.approval_rate) * 100).toFixed(0)}%</div>
                    <div className="text-white/25">pass</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 11-Checkpoint Pipeline */}
        <div className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-6">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <Activity size={15} className="text-rose-400" />
              <span className="text-sm font-medium text-white/80">11-Checkpoint Governance Pipeline</span>
              <span className="text-[10px] text-white/30">Same engine as trading vertical</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[10px] text-emerald-400/70">Active</span>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { id: 'CP-0', name: 'Signal Integrity', desc: 'Sensor data completeness & quality', icon: <Zap size={12} /> },
              { id: 'CP-1', name: 'Probability Check', desc: 'Clinical decision legitimacy', icon: <Activity size={12} /> },
              { id: 'CP-2', name: 'Risk Assessment', desc: 'Patient risk & contraindications', icon: <AlertTriangle size={12} /> },
              { id: 'CP-3', name: 'Coherence Engine', desc: 'Evidence & care plan alignment', icon: <Shield size={12} /> },
              { id: 'CP-4', name: 'Trend Analysis', desc: 'Recovery trajectory stability', icon: <TrendingUp size={12} /> },
              { id: 'CP-5', name: 'Stress Test', desc: 'Comorbidity stress scenarios', icon: <BarChart3 size={12} /> },
              { id: 'CP-7', name: 'Protocol Alignment', desc: 'Clinical guideline compliance', icon: <FileCheck size={12} /> },
              { id: 'CP-7b', name: 'FTI Trajectory', desc: 'Forward clinical implication', icon: <Eye size={12} /> },
              { id: 'CP-8', name: 'Exposure Control', desc: 'Safety threshold enforcement', icon: <Stethoscope size={12} /> },
              { id: 'CP-9', name: 'Consent Gate', desc: 'Informed consent verification', icon: <Lock size={12} /> },
              { id: 'CP-10', name: 'Ethics Check', desc: 'Ethical flag & bias screening', icon: <Brain size={12} /> },
              { id: 'TIE', name: 'Trajectory Invariant', desc: 'Bounded decision evolution', icon: <Globe size={12} /> },
            ].map(cp => (
              <div key={cp.id} className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.04] flex items-start gap-2.5">
                <div className="mt-0.5 text-rose-400/60">{cp.icon}</div>
                <div className="min-w-0">
                  <div className="text-[9px] text-rose-400/60 font-mono mb-0.5">{cp.id}</div>
                  <div className="text-xs font-medium text-white/70 leading-tight">{cp.name}</div>
                  <div className="text-[10px] text-white/30 mt-0.5 leading-tight">{cp.desc}</div>
                </div>
                <div className="ml-auto flex-shrink-0">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500/60" />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Decisions Table */}
        <div className="rounded-xl bg-white/[0.02] border border-white/[0.06] overflow-hidden">
          <div className="p-5 border-b border-white/[0.05] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock size={14} className="text-white/40" />
              <span className="text-sm font-medium text-white/70">Recent Clinical AI Decisions</span>
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse ml-1" />
            </div>
            <span className="text-xs text-white/30">{decisions.length} shown</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-white/[0.04]">
                  {['Decision ID', 'Device', 'Type', 'JX', 'Confidence', 'Risk', 'Score', 'Decision', 'Receipt'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-[10px] text-white/30 font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {decisions.length === 0 ? (
                  <tr><td colSpan={9} className="px-4 py-12 text-center text-white/20">Collecting decisions data...</td></tr>
                ) : decisions.map(d => (
                  <tr key={d.decision_id} className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors">
                    <td className="px-4 py-3 font-mono text-[10px] text-white/50">{d.decision_id.slice(0, 14)}</td>
                    <td className="px-4 py-3">
                      <span className="flex items-center gap-1 text-white/55">
                        {DEVICE_ICON[d.device_type]}
                        <span>{d.device_type.replace('_', ' ')}</span>
                      </span>
                    </td>
                    <td className="px-4 py-3 text-white/50">{DECISION_TYPE_LABEL[d.decision_type] || d.decision_type}</td>
                    <td className="px-4 py-3">
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-white/[0.05] text-white/50">
                        {d.jurisdiction}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={d.diagnostic_confidence >= 80 ? 'text-emerald-400' : d.diagnostic_confidence >= 65 ? 'text-amber-400' : 'text-red-400'}>
                        {d.diagnostic_confidence.toFixed(0)}%
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={d.patient_risk_score <= 40 ? 'text-emerald-400' : d.patient_risk_score <= 65 ? 'text-amber-400' : 'text-red-400'}>
                        {d.patient_risk_score.toFixed(0)}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-white/60">{d.decision_score != null ? Number(d.decision_score).toFixed(1) : '—'}</td>
                    <td className="px-4 py-3"><DecisionBadge decision={d.decision} /></td>
                    <td className="px-4 py-3 font-mono text-[10px] text-white/30">{d.receipt_id?.slice(0, 16) ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Latest Blocked Decision signal breakdown */}
        {decisions.find(d => d.decision === 'BLOCKED') && (() => {
          const blocked = decisions.find(d => d.decision === 'BLOCKED')!
          return (
            <div className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-6">
              <div className="flex items-center gap-2 mb-5">
                <XCircle size={14} className="text-red-400" />
                <span className="text-sm font-medium text-white/70">Latest Blocked Decision — Signal Breakdown</span>
                <span className="text-[10px] text-white/30 ml-2 font-mono">{blocked.decision_id}</span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <SignalBar label="Probability Score" value={blocked.probability_score} />
                <SignalBar label="Risk Exposure" value={blocked.risk_exposure} invert />
                <SignalBar label="Signal Coherence" value={blocked.signal_coherence} />
                <SignalBar label="Trend Persistence" value={blocked.trend_persistence} />
                <SignalBar label="Stress Resilience" value={blocked.stress_resilience} />
                <SignalBar label="Logic Consistency" value={blocked.logic_consistency} />
              </div>
              {blocked.block_reason && (
                <div className="mt-4 p-3 rounded-lg bg-red-500/8 border border-red-500/20 text-xs text-red-400/80">
                  Block reason: {blocked.block_reason}
                </div>
              )}
            </div>
          )
        })()}

        {/* Footer */}
        <div className="flex items-center justify-between pt-4 border-t border-white/[0.04] text-[10px] text-white/25">
          <span>OMNIX Decision Governance Infrastructure — Medical AI Vertical (ADR-078)</span>
          <span>Auto-refresh every 10s · PQC-signed receipts · 11-checkpoint pipeline</span>
        </div>
      </div>
    </div>
  )
}
