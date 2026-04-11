import { useState, useEffect, useCallback, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield, AlertTriangle, CheckCircle, XCircle, Activity, BarChart3,
  Clock, RefreshCw, Globe, Zap, Lock, Eye, ArrowLeft,
  Cpu, Radio, Thermometer, Battery, TrendingUp
} from 'lucide-react'
import { API_BASE } from '../lib/apiBase'

const REFRESH_INTERVAL = 10_000
const RETRY_INTERVAL = 6_000

interface Metrics {
  total_actions: number
  actions_approved: number
  actions_blocked: number
  actions_held: number
  approval_rate: number
  avg_sensor_confidence: number
  avg_collision_risk: number
  avg_decision_score: number
  avg_trajectory_score: number
  actions_last_24h: number
  active_robots: number
  safety_incidents_prevented: number
  simulation_cycles: number
}

interface RobotAction {
  action_id: string
  robot_id: string
  robot_type: string
  industry: string
  action_type: string
  environment: string
  sensor_confidence: number
  collision_risk: number
  sensor_fusion_agreement: number
  battery_pct: number
  temperature_c: number
  payload_kg: number
  speed_ms: number
  proximity_cm: number
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

interface ByIndustry {
  industry: string
  total: number
  approved: number
  blocked: number
  approval_rate: number
  avg_sensor_confidence: number
  avg_collision_risk: number
  safety_prevented: number
}

interface ByRobot {
  robot_type: string
  total: number
  approved: number
  blocked: number
  approval_rate: number
  avg_sensor_confidence: number
  avg_collision_risk: number
  robot_count: number
}

interface FleetRobot {
  robot_id: string
  robot_type: string
  industry: string
  action_type: string
  sensor_confidence: number
  collision_risk: number
  battery_pct: number
  temperature_c: number
  decision: string
  decision_score: number
  created_at: string
}

const INDUSTRY_COLORS: Record<string, string> = {
  Automotive: '#3B82F6',
  Electronics: '#8B5CF6',
  Logistics: '#F59E0B',
  Pharma: '#10B981',
  Food: '#EF4444',
  Construction: '#F97316',
  Healthcare: '#06B6D4',
  Defense: '#6B7280',
}

const ROBOT_ICONS: Record<string, string> = {
  Industrial_Arm: '🦾',
  AMR: '🤖',
  Cobot: '🦿',
  Drone: '🚁',
  AGV: '🚛',
  Humanoid: '🧑‍🤝‍🧑',
}

function fmt2(n: number) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`
  return n.toLocaleString()
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

function MetricPill({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div className="flex items-center justify-between px-3 py-2 rounded-lg bg-white/[0.02] border border-white/[0.04]">
      <span className="text-[11px] text-white/40">{label}</span>
      <span className={`text-xs font-semibold ${color}`}>{value}</span>
    </div>
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

function RobotStatusDot({ decision, confidence }: { decision: string; confidence: number }) {
  if (decision === 'BLOCKED') return <div className="w-2 h-2 rounded-full bg-red-500" title="Blocked" />
  if (confidence < 50) return <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" title="Degraded sensor" />
  return <div className="w-2 h-2 rounded-full bg-emerald-500" title="Operational" />
}

export default function RoboticsDashboard() {
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [actions, setActions] = useState<RobotAction[]>([])
  const [byIndustry, setByIndustry] = useState<ByIndustry[]>([])
  const [byRobot, setByRobot] = useState<ByRobot[]>([])
  const [fleet, setFleet] = useState<FleetRobot[]>([])
  const [, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)
  const [retrying, setRetrying] = useState(false)
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const fetchAll = useCallback(async () => {
    try {
      const [mRes, aRes, iRes, rRes, fRes] = await Promise.all([
        fetch(`${API_BASE}/api/robotics/metrics`),
        fetch(`${API_BASE}/api/robotics/actions?limit=30`),
        fetch(`${API_BASE}/api/robotics/by-industry`),
        fetch(`${API_BASE}/api/robotics/by-robot`),
        fetch(`${API_BASE}/api/robotics/fleet`),
      ])

      if (!mRes.ok || mRes.headers.get('content-type')?.includes('text/html')) {
        throw new Error(`HTTP ${mRes.status}`)
      }

      const [md, ad, id_, rd, fd] = await Promise.all([
        mRes.json(), aRes.json(), iRes.json(), rRes.json(), fRes.json()
      ])

      if (md.success) { setMetrics(md.metrics); setError(null); setRetrying(false) }
      if (ad.success) setActions(ad.actions || [])
      if (id_.success) setByIndustry(id_.by_industry || [])
      if (rd.success) setByRobot(rd.by_robot || [])
      if (fd.success) setFleet(fd.fleet?.slice(0, 20) || [])
      setLastRefresh(new Date())
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Connection error'
      setError(msg)
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
                <span className="text-sm font-semibold text-white">Robotics Governance</span>
                <span className="px-2 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/25 text-emerald-400 text-[10px] font-medium">LIVE</span>
                <span className="px-2 py-0.5 rounded bg-white/[0.05] border border-white/10 text-white/40 text-[10px]">ADR-055</span>
              </div>
              <p className="text-[11px] text-white/35 mt-0.5">OMNIX Decision Governance Infrastructure — Autonomous Systems Vertical</p>
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
              icon: <Cpu size={18} className="text-blue-400" />,
              label: 'Actions Evaluated', sub: `${m?.actions_last_24h ?? 0} in last 24h`,
              value: loading ? '—' : fmt2(m?.total_actions ?? 0),
            },
            {
              icon: <Shield size={18} className="text-emerald-400" />,
              label: 'Safety Events Prevented', sub: 'High-risk actions blocked',
              value: loading ? '—' : fmt2(m?.safety_incidents_prevented ?? 0),
              valueClass: 'text-emerald-400',
            },
            {
              icon: <Radio size={18} className="text-[#C9A227]" />,
              label: 'Avg Sensor Confidence', sub: 'LiDAR + Camera + IMU',
              value: loading ? '—' : `${Number(m?.avg_sensor_confidence ?? 0).toFixed(1)}%`,
              valueClass: 'text-[#C9A227]',
            },
            {
              icon: <AlertTriangle size={18} className="text-red-400" />,
              label: 'Avg Collision Risk', sub: `${m?.active_robots ?? 0} active robots`,
              value: loading ? '—' : `${Number(m?.avg_collision_risk ?? 0).toFixed(1)}`,
              valueClass: Number(m?.avg_collision_risk ?? 0) > 40 ? 'text-red-400' : 'text-white',
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
          <MetricPill label="Actions Approved" value={`${(Number(m?.approval_rate ?? 0) * 100).toFixed(1)}%`} color="text-emerald-400" />
          <MetricPill label="Actions Blocked" value={fmt2(m?.actions_blocked ?? 0)} color="text-red-400" />
          <MetricPill label="Avg Decision Score" value={`${Number(m?.avg_decision_score ?? 0).toFixed(1)}/100`} color="text-[#C9A227]" />
          <MetricPill label="Simulation Cycles" value={fmt2(m?.simulation_cycles ?? 0)} color="text-blue-400" />
        </div>

        {/* By Industry + By Robot Type */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* By Industry */}
          <div className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-6">
            <div className="flex items-center gap-2 mb-5">
              <BarChart3 size={15} className="text-[#C9A227]" />
              <span className="text-sm font-medium text-white/80">By Industry</span>
            </div>
            <div className="space-y-3">
              {byIndustry.length === 0 ? (
                <div className="text-center py-8 text-white/20 text-sm">Collecting data...</div>
              ) : byIndustry.map(ind => (
                <div key={ind.industry} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: INDUSTRY_COLORS[ind.industry] ?? '#666' }} />
                      <span className="text-white/70">{ind.industry}</span>
                      <span className="text-white/25">{ind.total}</span>
                    </div>
                    <div className="flex items-center gap-3 text-white/40">
                      <span className="text-emerald-400/80">{(Number(ind.approval_rate ?? 0) * 100).toFixed(0)}% pass</span>
                      <span className="text-amber-400/70">{ind.safety_prevented} prevented</span>
                    </div>
                  </div>
                  <div className="h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
                    <div className="h-full rounded-full transition-all duration-700"
                      style={{ width: `${Number(ind.approval_rate ?? 0) * 100}%`, backgroundColor: INDUSTRY_COLORS[ind.industry] ?? '#666', opacity: 0.7 }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* By Robot Type */}
          <div className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-6">
            <div className="flex items-center gap-2 mb-5">
              <Cpu size={15} className="text-blue-400" />
              <span className="text-sm font-medium text-white/80">By Robot Type</span>
            </div>
            <div className="space-y-2">
              {byRobot.length === 0 ? (
                <div className="text-center py-8 text-white/20 text-sm">Collecting data...</div>
              ) : byRobot.map(r => (
                <div key={r.robot_type} className="flex items-center gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                  <span className="text-xl">{ROBOT_ICONS[r.robot_type] ?? '🤖'}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-white/70">{r.robot_type.replace('_', ' ')}</span>
                      <span className="text-[10px] text-white/30">{r.robot_count} robots · {r.total} actions</span>
                    </div>
                    <div className="h-1 bg-white/[0.04] rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500/60 rounded-full"
                        style={{ width: `${Number(r.approval_rate ?? 0) * 100}%` }} />
                    </div>
                  </div>
                  <div className="text-right text-xs">
                    <div className="text-emerald-400/80">{(Number(r.approval_rate ?? 0) * 100).toFixed(0)}%</div>
                    <div className="text-white/25">pass</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Live Fleet Monitor */}
        {fleet.length > 0 && (
          <div className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-6">
            <div className="flex items-center justify-between mb-5">
              <div className="flex items-center gap-2">
                <Radio size={14} className="text-blue-400" />
                <span className="text-sm font-medium text-white/80">Live Fleet Monitor</span>
                <span className="text-[10px] text-white/30">Latest reading per robot</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                <span className="text-[10px] text-blue-400/70">{fleet.length} robots tracked</span>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
              {fleet.slice(0, 16).map(robot => (
                <div key={robot.robot_id}
                  className={`p-3 rounded-lg border transition-colors ${robot.decision === 'BLOCKED' ? 'bg-red-500/5 border-red-500/20' : 'bg-white/[0.02] border-white/[0.05]'}`}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-1.5">
                      <span className="text-base">{ROBOT_ICONS[robot.robot_type] ?? '🤖'}</span>
                      <div>
                        <div className="text-[10px] text-white/60 font-mono leading-tight">{robot.robot_id.slice(0, 12)}</div>
                        <div className="text-[9px] text-white/30">{robot.robot_type.replace('_', ' ')}</div>
                      </div>
                    </div>
                    <RobotStatusDot decision={robot.decision} confidence={robot.sensor_confidence} />
                  </div>
                  <div className="grid grid-cols-2 gap-1 text-[10px]">
                    <div className="flex items-center gap-1 text-white/40">
                      <Radio size={9} />
                      <span>{Number(robot.sensor_confidence ?? 0).toFixed(0)}%</span>
                    </div>
                    <div className="flex items-center gap-1 text-white/40">
                      <Battery size={9} />
                      <span className={Number(robot.battery_pct ?? 0) < 20 ? 'text-red-400' : ''}>{Number(robot.battery_pct ?? 0).toFixed(0)}%</span>
                    </div>
                    <div className="flex items-center gap-1 text-white/40">
                      <Thermometer size={9} />
                      <span className={Number(robot.temperature_c ?? 0) > 75 ? 'text-amber-400' : ''}>{Number(robot.temperature_c ?? 0).toFixed(0)}°C</span>
                    </div>
                    <div className="flex items-center gap-1 text-white/40">
                      <Shield size={9} />
                      <span>{Number(robot.collision_risk ?? 0).toFixed(0)}</span>
                    </div>
                  </div>
                  <div className="mt-2 pt-2 border-t border-white/[0.04]">
                    <DecisionBadge decision={robot.decision} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 11-Checkpoint Pipeline */}
        <div className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-6">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <Activity size={15} className="text-[#C9A227]" />
              <span className="text-sm font-medium text-white/80">11-Checkpoint Pre-Execution Pipeline</span>
              <span className="text-[10px] text-white/30">Every robot action evaluated before execution</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[10px] text-emerald-400/70">Active</span>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { id: 'CP-0', name: 'Signal Integrity', desc: 'Sensor data quality check', icon: <Zap size={12} /> },
              { id: 'CP-1', name: 'Success Probability', desc: 'Action success likelihood', icon: <TrendingUp size={12} /> },
              { id: 'CP-2', name: 'Collision Risk', desc: 'Proximity & damage risk', icon: <AlertTriangle size={12} /> },
              { id: 'CP-3', name: 'Sensor Coherence', desc: 'LiDAR + Camera + IMU fusion', icon: <Radio size={12} /> },
              { id: 'CP-4', name: 'Environment Stability', desc: 'Condition persistence score', icon: <Globe size={12} /> },
              { id: 'CP-5', name: 'Mechanical Stress', desc: 'Battery, temp, joint margin', icon: <Thermometer size={12} /> },
              { id: 'CP-7', name: 'Mission Logic', desc: 'Action-mission alignment', icon: <Eye size={12} /> },
              { id: 'CP-7b', name: 'FTI Trajectory', desc: 'Forward path implication', icon: <Activity size={12} /> },
              { id: 'CP-8', name: 'Fleet Exposure', desc: 'Concentration risk control', icon: <Cpu size={12} /> },
              { id: 'CP-10', name: 'Anomaly Detection', desc: 'Sensor spoofing detection', icon: <Lock size={12} /> },
              { id: 'CP-11', name: 'Safety Zone', desc: 'Jurisdiction & geofencing', icon: <Shield size={12} /> },
              { id: 'TIE', name: 'Trajectory Invariant', desc: 'Bounded decision evolution', icon: <BarChart3 size={12} /> },
            ].map(cp => (
              <div key={cp.id} className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.04] flex items-start gap-2.5">
                <div className="mt-0.5 text-[#C9A227]/60">{cp.icon}</div>
                <div className="min-w-0">
                  <div className="text-[9px] text-[#C9A227]/60 font-mono mb-0.5">{cp.id}</div>
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

        {/* Recent Actions Table */}
        <div className="rounded-xl bg-white/[0.02] border border-white/[0.06] overflow-hidden">
          <div className="p-5 border-b border-white/[0.05] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock size={14} className="text-white/40" />
              <span className="text-sm font-medium text-white/70">Recent Robot Actions</span>
            </div>
            <span className="text-xs text-white/30">{actions.length} shown</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-white/[0.04]">
                  {['Robot ID', 'Type', 'Industry', 'Action', 'Sensor %', 'Collision Risk', 'Battery', 'Decision', 'Receipt'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-[10px] text-white/30 font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {actions.length === 0 ? (
                  <tr><td colSpan={9} className="px-4 py-12 text-center text-white/20">Collecting actions data...</td></tr>
                ) : actions.map(a => (
                  <tr key={a.action_id} className={`border-b border-white/[0.03] transition-colors ${a.decision === 'BLOCKED' ? 'bg-red-500/3' : 'hover:bg-white/[0.01]'}`}>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5">
                        <RobotStatusDot decision={a.decision} confidence={a.sensor_confidence} />
                        <span className="font-mono text-[10px] text-white/50">{a.robot_id.slice(0, 14)}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-base" title={a.robot_type}>{ROBOT_ICONS[a.robot_type] ?? '🤖'}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-block px-1.5 py-0.5 rounded text-[10px]"
                        style={{ color: INDUSTRY_COLORS[a.industry] ?? '#888', backgroundColor: `${INDUSTRY_COLORS[a.industry] ?? '#888'}15` }}>
                        {a.industry}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-white/50 text-[10px]">{a.action_type?.replace(/_/g, ' ')}</td>
                    <td className="px-4 py-3">
                      <span className={Number(a.sensor_confidence ?? 0) < 50 ? 'text-amber-400' : 'text-white/60'}>
                        {Number(a.sensor_confidence ?? 0).toFixed(0)}%
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={Number(a.collision_risk ?? 0) > 65 ? 'text-red-400' : Number(a.collision_risk ?? 0) > 40 ? 'text-amber-400' : 'text-emerald-400'}>
                        {Number(a.collision_risk ?? 0).toFixed(1)}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={Number(a.battery_pct ?? 0) < 20 ? 'text-red-400' : 'text-white/50'}>
                        {Number(a.battery_pct ?? 0).toFixed(0)}%
                      </span>
                    </td>
                    <td className="px-4 py-3"><DecisionBadge decision={a.decision} /></td>
                    <td className="px-4 py-3 font-mono text-[10px] text-white/30">{a.receipt_id?.slice(0, 14) ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Signal breakdown of last blocked */}
        {actions.find(a => a.decision === 'BLOCKED') && (() => {
          const blocked = actions.find(a => a.decision === 'BLOCKED')!
          return (
            <div className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-6">
              <div className="flex items-center gap-2 mb-5">
                <XCircle size={14} className="text-red-400" />
                <span className="text-sm font-medium text-white/70">Latest Blocked Action — Signal Breakdown</span>
                <span className="text-[10px] text-white/30 ml-2 font-mono">{blocked.robot_id.slice(0, 14)}</span>
                <span className="text-[10px] text-white/20">· {blocked.action_type?.replace(/_/g, ' ')}</span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <SignalBar label="Success Probability" value={blocked.probability_score} />
                <SignalBar label="Collision Risk" value={blocked.risk_exposure} invert />
                <SignalBar label="Sensor Coherence" value={blocked.signal_coherence} />
                <SignalBar label="Environment Stability" value={blocked.trend_persistence} />
                <SignalBar label="Mechanical Margin" value={blocked.stress_resilience} />
                <SignalBar label="Mission Logic" value={blocked.logic_consistency} />
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
          <span>OMNIX Decision Governance Infrastructure — Robotics Vertical (ADR-055)</span>
          <span>Auto-refresh every 20s · PQC-signed receipts · Pre-execution governance</span>
        </div>
      </div>
    </div>
  )
}
