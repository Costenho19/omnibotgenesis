import { useState, useEffect, useCallback, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield, AlertTriangle, CheckCircle, XCircle, Activity, BarChart3,
  Clock, RefreshCw, Globe, Zap, Lock, Bot,
  Database, Server, TrendingUp, Brain
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
  avg_task_complexity: number
  avg_scope_risk: number
  avg_decision_score: number
  avg_trajectory_score: number
  decisions_last_24h: number
  active_agents: number
  safety_blocks: number
  simulation_cycles: number
}

interface AgentDecision {
  decision_id: string
  agent_id: string
  agent_type: string
  decision_type: string
  environment: string
  reversibility: string
  data_sensitivity: string
  task_complexity: number
  scope_blast_radius: number
  decision: string
  decision_score: number
  block_reason: string | null
  receipt_id: string
  trajectory_score: number
  safety_critical_flag: boolean
  human_approval_required: boolean
  human_approved: boolean
  created_at: string
}

interface ByType {
  decision_type: string
  total: number
  approved: number
  blocked: number
  avg_complexity: number
  avg_scope_risk: number
  approval_rate: number
}

interface ByAgent {
  agent_type: string
  total: number
  approved: number
  blocked: number
  avg_complexity: number
  avg_decision_score: number
  agent_count: number
  approval_rate: number
}

interface ByEnvironment {
  environment: string
  total: number
  approved: number
  blocked: number
  avg_scope_risk: number
  avg_score: number
  approval_rate: number
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
        <div className={`h-full rounded-full transition-all duration-700 ${color}`} style={{ width: `${displayPct}%` }} />
      </div>
    </div>
  )
}

const AGENT_ICON: Record<string, React.ReactNode> = {
  Financial_Agent: <TrendingUp size={10} />,
  Enterprise_Agent: <Brain size={10} />,
  Logistics_Agent: <Globe size={10} />,
  Infrastructure_Agent: <Server size={10} />,
  Research_Agent: <Database size={10} />,
}

const DECISION_LABEL: Record<string, string> = {
  task_delegation: 'Task Delegation',
  data_access: 'Data Access',
  external_api_call: 'External API',
  resource_allocation: 'Resource Alloc.',
  state_modification: 'State Modify',
}

const ENV_COLOR: Record<string, string> = {
  production: 'text-red-400',
  staging: 'text-amber-400',
  development: 'text-blue-400',
  sandbox: 'text-emerald-400',
}

export default function AgentsDashboard() {
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [decisions, setDecisions] = useState<AgentDecision[]>([])
  const [byType, setByType] = useState<ByType[]>([])
  const [byAgent, setByAgent] = useState<ByAgent[]>([])
  const [byEnv, setByEnv] = useState<ByEnvironment[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)
  const [retrying, setRetrying] = useState(false)
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const fetchAll = useCallback(async () => {
    try {
      const [mRes, dRes, tRes, aRes, eRes] = await Promise.all([
        fetch(`${API_BASE}/api/agents/metrics`),
        fetch(`${API_BASE}/api/agents/decisions?limit=30`),
        fetch(`${API_BASE}/api/agents/by-type`),
        fetch(`${API_BASE}/api/agents/by-agent`),
        fetch(`${API_BASE}/api/agents/by-environment`),
      ])
      if (!mRes.ok || mRes.headers.get('content-type')?.includes('text/html')) {
        throw new Error(`HTTP ${mRes.status}`)
      }
      const [md, dd, td, ad, ed] = await Promise.all([
        mRes.json(), dRes.json(), tRes.json(), aRes.json(), eRes.json()
      ])
      if (md.success) { setMetrics(md.metrics); setError(null); setRetrying(false) }
      if (dd.success) setDecisions(dd.decisions || [])
      if (td.success) setByType(td.by_type || [])
      if (ad.success) setByAgent(ad.by_agent || [])
      if (ed.success) setByEnv(ed.by_environment || [])
      setLastRefresh(new Date())
      setLoading(false)
      if (retryRef.current) { clearTimeout(retryRef.current); retryRef.current = null }
    } catch (err: any) {
      setError('Connecting to Autonomous Agent Governance engine...')
      setLoading(false)
      setRetrying(true)
      retryRef.current = setTimeout(fetchAll, RETRY_INTERVAL)
    }
  }, [])

  useEffect(() => {
    fetchAll()
    const interval = setInterval(fetchAll, REFRESH_INTERVAL)
    return () => { clearInterval(interval); if (retryRef.current) clearTimeout(retryRef.current) }
  }, [fetchAll])

  return (
    <div className="min-h-screen bg-[#0a0b0f] text-white font-sans">
      {/* Header */}
      <div className="border-b border-white/[0.06] bg-[#0a0b0f]/95 sticky top-0 z-50 backdrop-blur">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/" className="flex items-center gap-2 text-white/40 hover:text-white/70 transition-colors text-sm">
              <Shield size={16} /><span>OMNIX</span>
            </Link>
            <span className="text-white/20">/</span>
            <div className="flex items-center gap-2">
              <Bot size={15} className="text-violet-400" />
              <span className="text-sm text-white/70">Autonomous Agents Dashboard</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {retrying && (
              <div className="flex items-center gap-1.5 text-[11px] text-amber-400">
                <RefreshCw size={11} className="animate-spin" /> Reconnecting
              </div>
            )}
            {lastRefresh && !retrying && <span className="text-[10px] text-white/25">{lastRefresh.toLocaleTimeString()}</span>}
            <Link to="/governance-demo-agents" className="flex items-center gap-2 px-4 py-2 rounded-lg bg-violet-500/10 border border-violet-500/20 text-violet-400 hover:bg-violet-500/15 transition-all text-sm">
              <Bot size={13} /> Interactive Demo
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-violet-500/10 border border-violet-500/20">
              <Bot size={18} className="text-violet-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white/90 tracking-tight">Autonomous Agent Governance</h1>
              <p className="text-[12px] text-white/35 mt-0.5">
                OMNIX-AGT · 11-Checkpoint Pipeline · Dilithium-3 PQC Receipts · 24/7 Live Simulation
              </p>
            </div>
          </div>
        </div>

        {error && (
          <div className="flex items-center gap-3 p-4 rounded-xl border border-amber-500/20 bg-amber-500/[0.05] text-amber-400 text-sm">
            <AlertTriangle size={16} /><span>{error}</span>
          </div>
        )}
        {loading && (
          <div className="flex items-center justify-center h-48 text-white/30 text-sm gap-3">
            <RefreshCw size={16} className="animate-spin" /> Initializing Agent Governance engine...
          </div>
        )}

        {metrics && (
          <>
            {/* KPI Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
              {[
                { label: 'Total Decisions', value: metrics.total_decisions.toLocaleString(), color: 'text-white', icon: <Shield size={14} className="text-white/20" /> },
                { label: 'Approved', value: metrics.decisions_approved.toLocaleString(), color: 'text-emerald-400', icon: <CheckCircle size={14} className="text-emerald-500/30" /> },
                { label: 'Blocked', value: metrics.decisions_blocked.toLocaleString(), color: 'text-red-400', icon: <XCircle size={14} className="text-red-500/30" /> },
                { label: 'Approval Rate', value: `${(metrics.approval_rate * 100).toFixed(1)}%`, color: 'text-emerald-400', icon: <TrendingUp size={14} className="text-emerald-500/30" /> },
                { label: 'Avg Complexity', value: `${metrics.avg_task_complexity.toFixed(1)}%`, color: 'text-violet-400', icon: <Brain size={14} className="text-violet-500/30" /> },
                { label: 'Active Agents', value: metrics.active_agents, color: 'text-blue-400', icon: <Bot size={14} className="text-blue-500/30" /> },
                { label: 'Safety Blocks', value: metrics.safety_blocks, color: 'text-rose-400', icon: <AlertTriangle size={14} className="text-rose-500/30" /> },
              ].map((m, i) => (
                <div key={i} className="rounded-xl border border-white/[0.06] bg-white/[0.025] px-4 py-4">
                  <div className="flex items-center justify-between mb-2">{m.icon}</div>
                  <div className={`text-xl font-bold ${m.color}`}>{m.value}</div>
                  <div className="text-[10px] text-white/30 mt-0.5">{m.label}</div>
                </div>
              ))}
            </div>

            {/* Signal health strip */}
            <div className="rounded-2xl border border-white/[0.07] bg-white/[0.02] p-5">
              <div className="flex items-center gap-2 mb-4">
                <Zap size={14} className="text-violet-400" />
                <h2 className="text-sm font-semibold text-white/70">Average Governance Signals</h2>
                <span className="text-[10px] text-white/25 ml-auto">6-signal OMNIX framework</span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
                {[
                  { label: 'Avg Complexity', value: metrics.avg_task_complexity, invert: true },
                  { label: 'Scope Risk', value: metrics.avg_scope_risk, invert: true },
                  { label: 'Decision Score', value: metrics.avg_decision_score, invert: false },
                  { label: 'Trajectory', value: metrics.avg_trajectory_score, invert: false },
                  { label: 'Approval Rate', value: metrics.approval_rate * 100, invert: false },
                  { label: 'Block Rate', value: metrics.block_rate * 100, invert: true },
                ].map((s, i) => (
                  <SignalBar key={i} label={s.label} value={s.value} invert={s.invert} />
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* By Decision Type */}
              <div className="rounded-2xl border border-white/[0.07] bg-white/[0.02] p-5">
                <div className="flex items-center gap-2 mb-4">
                  <Activity size={14} className="text-violet-400" />
                  <h2 className="text-sm font-semibold text-white/70">By Decision Type</h2>
                </div>
                <div className="space-y-3">
                  {byType.map(t => (
                    <div key={t.decision_type} className="space-y-1.5">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="text-white/55">{DECISION_LABEL[t.decision_type] || t.decision_type}</span>
                        <span className="text-white/40">{t.total.toLocaleString()}</span>
                      </div>
                      <div className="h-1.5 bg-white/[0.04] rounded-full overflow-hidden flex">
                        <div className="h-full bg-emerald-500/60 rounded-full" style={{ width: `${(t.approved / Math.max(t.total, 1)) * 100}%` }} />
                        <div className="h-full bg-red-500/50" style={{ width: `${(t.blocked / Math.max(t.total, 1)) * 100}%` }} />
                      </div>
                      <div className="flex justify-between text-[9px] text-white/25">
                        <span>Complexity: {t.avg_complexity?.toFixed(0)}%</span>
                        <span>{((t.approval_rate || 0) * 100).toFixed(0)}% approved</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* By Agent */}
              <div className="rounded-2xl border border-white/[0.07] bg-white/[0.02] p-5">
                <div className="flex items-center gap-2 mb-4">
                  <Bot size={14} className="text-blue-400" />
                  <h2 className="text-sm font-semibold text-white/70">By Agent Type</h2>
                </div>
                <div className="space-y-3">
                  {byAgent.map(a => (
                    <div key={a.agent_type} className="space-y-1">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1.5 text-[11px] text-white/55">
                          {AGENT_ICON[a.agent_type]}
                          <span>{a.agent_type.replace('_', ' ')}</span>
                        </div>
                        <span className="text-[10px] text-white/35">{a.agent_count} agents</span>
                      </div>
                      <div className="h-1.5 bg-white/[0.04] rounded-full overflow-hidden flex">
                        <div className="h-full bg-emerald-500/60 rounded-full" style={{ width: `${(a.approved / Math.max(a.total, 1)) * 100}%` }} />
                        <div className="h-full bg-red-500/50" style={{ width: `${(a.blocked / Math.max(a.total, 1)) * 100}%` }} />
                      </div>
                      <div className="flex justify-between text-[9px] text-white/25">
                        <span>Score: {a.avg_decision_score?.toFixed(1)}</span>
                        <span>{((a.approval_rate || 0) * 100).toFixed(0)}% approved</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* By Environment */}
              <div className="rounded-2xl border border-white/[0.07] bg-white/[0.02] p-5">
                <div className="flex items-center gap-2 mb-4">
                  <Server size={14} className="text-emerald-400" />
                  <h2 className="text-sm font-semibold text-white/70">By Environment</h2>
                </div>
                <div className="space-y-3">
                  {byEnv.map(e => (
                    <div key={e.environment} className="space-y-1.5">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className={`font-medium capitalize ${ENV_COLOR[e.environment] || 'text-white/55'}`}>{e.environment}</span>
                        <span className="text-white/35">{e.total.toLocaleString()}</span>
                      </div>
                      <div className="h-1.5 bg-white/[0.04] rounded-full overflow-hidden flex">
                        <div className="h-full bg-emerald-500/60 rounded-full" style={{ width: `${(e.approved / Math.max(e.total, 1)) * 100}%` }} />
                        <div className="h-full bg-red-500/50" style={{ width: `${(e.blocked / Math.max(e.total, 1)) * 100}%` }} />
                      </div>
                      <div className="flex justify-between text-[9px] text-white/25">
                        <span>Scope risk: {e.avg_scope_risk?.toFixed(0)}%</span>
                        <span>{((e.approval_rate || 0) * 100).toFixed(0)}% approved</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Live Decision Feed */}
            <div className="rounded-2xl border border-white/[0.07] bg-white/[0.02] overflow-hidden">
              <div className="px-5 py-4 border-b border-white/[0.05] flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Bot size={14} className="text-violet-400" />
                  <h2 className="text-sm font-semibold text-white/70">Live Agent Decision Feed</h2>
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse ml-1" />
                </div>
                <span className="text-[10px] text-white/25">Last 30 decisions · {REFRESH_INTERVAL / 1000}s refresh</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-[11px]">
                  <thead>
                    <tr className="border-b border-white/[0.04]">
                      {['Decision ID', 'Agent', 'Type', 'Env', 'Rev', 'Complexity', 'Scope Risk', 'Score', 'Outcome', 'Receipt'].map(h => (
                        <th key={h} className="px-4 py-2.5 text-left text-[10px] text-white/30 font-medium">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.03]">
                    {decisions.map(d => (
                      <tr key={d.decision_id} className="hover:bg-white/[0.015] transition-colors">
                        <td className="px-4 py-2.5 font-mono text-white/40 text-[10px]">{d.decision_id.slice(0, 14)}</td>
                        <td className="px-4 py-2.5">
                          <span className="flex items-center gap-1 text-white/55">
                            {AGENT_ICON[d.agent_type]}<span>{d.agent_type.replace('_', ' ')}</span>
                          </span>
                        </td>
                        <td className="px-4 py-2.5 text-white/50">{DECISION_LABEL[d.decision_type] || d.decision_type}</td>
                        <td className="px-4 py-2.5">
                          <span className={`text-[10px] font-semibold capitalize ${ENV_COLOR[d.environment] || 'text-white/40'}`}>{d.environment}</span>
                        </td>
                        <td className="px-4 py-2.5 text-white/35 text-[10px] capitalize">{d.reversibility?.replace('_', ' ')}</td>
                        <td className="px-4 py-2.5">
                          <span className={d.task_complexity <= 40 ? 'text-emerald-400' : d.task_complexity <= 65 ? 'text-amber-400' : 'text-red-400'}>
                            {d.task_complexity?.toFixed(0)}%
                          </span>
                        </td>
                        <td className="px-4 py-2.5">
                          <span className={d.scope_blast_radius <= 35 ? 'text-emerald-400' : d.scope_blast_radius <= 60 ? 'text-amber-400' : 'text-red-400'}>
                            {d.scope_blast_radius?.toFixed(0)}%
                          </span>
                        </td>
                        <td className="px-4 py-2.5 text-white/50">{d.decision_score?.toFixed(1)}</td>
                        <td className="px-4 py-2.5"><DecisionBadge decision={d.decision} /></td>
                        <td className="px-4 py-2.5 font-mono text-[9px] text-white/25">{d.receipt_id?.slice(-12)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {decisions.length === 0 && !loading && (
                  <div className="py-12 text-center text-white/30 text-sm">
                    <Bot size={24} className="mx-auto mb-3 text-white/15" />
                    Simulation warming up — first batch generates in ~3 minutes
                  </div>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {[
                { icon: <Lock size={16} className="text-violet-400" />, title: 'Post-Quantum Receipts', desc: 'Every agent action gets a CRYSTALS-Dilithium3 cryptographic receipt. Full audit trail, non-repudiable, quantum-resistant.' },
                { icon: <Shield size={16} className="text-rose-400" />, title: 'Hard Safety Blocks', desc: 'Safety-critical flag or missing human authorization → immediate BLOCK. No score override. No exceptions.' },
                { icon: <Globe size={16} className="text-blue-400" />, title: 'Principal Hierarchy', desc: 'EU AI Act, NIST AI RMF, ISO 42001 — authorization chain enforced at CP-7 across all environments.' },
              ].map((item, i) => (
                <div key={i} className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 space-y-2">
                  {item.icon}
                  <div className="text-sm font-semibold text-white/70">{item.title}</div>
                  <div className="text-[11px] text-white/35 leading-relaxed">{item.desc}</div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
