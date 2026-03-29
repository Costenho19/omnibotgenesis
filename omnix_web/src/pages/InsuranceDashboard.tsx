import { useState, useEffect, useCallback, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield, AlertTriangle, CheckCircle, XCircle, Activity, BarChart3,
  DollarSign, Clock, RefreshCw, Globe, Zap, Lock,
  FileCheck, TrendingUp, Eye, ArrowLeft
} from 'lucide-react'
import { API_BASE } from '../lib/apiBase'

const REFRESH_INTERVAL = 10_000
const RETRY_INTERVAL = 6_000

interface Metrics {
  total_claims: number
  claims_approved: number
  claims_blocked: number
  claims_held: number
  approval_rate: number
  total_approved_usd: number
  total_blocked_usd: number
  avg_fraud_score: number
  avg_decision_score: number
  avg_trajectory_score: number
  claims_last_24h: number
  high_fraud_blocked: number
  simulation_cycles: number
  loss_avoided_usd: number
}

interface Claim {
  claim_id: string
  claimant_type: string
  insurance_type: string
  region: string
  claim_amount_usd: number
  coverage_ratio: number
  fraud_indicators: number
  evidence_completeness: number
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
  insurance_type: string
  total: number
  approved: number
  blocked: number
  approval_rate: number
  avg_claim_usd: number
  avg_fraud: number
  blocked_usd: number
}

interface ByRegion {
  region: string
  total: number
  approved: number
  blocked: number
  approval_rate: number
  approved_usd: number
  blocked_usd: number
}

const TYPE_COLORS: Record<string, string> = {
  Property: '#C9A227',
  Auto: '#3B82F6',
  Health: '#10B981',
  Liability: '#8B5CF6',
  Cyber: '#F59E0B',
  Life: '#EF4444',
  Marine: '#06B6D4',
  'D&O': '#6366F1',
}

const REGION_FLAGS: Record<string, string> = {
  NA: '🇺🇸', EU: '🇪🇺', APAC: '🌏', MEA: '🌍', LATAM: '🌎', GLOBAL: '🌐'
}

function fmt(n: number, decimals = 0) {
  if (n >= 1_000_000_000) return `$${(n / 1_000_000_000).toFixed(1)}B`
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`
  return `$${n.toFixed(decimals)}`
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

export default function InsuranceDashboard() {
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [claims, setClaims] = useState<Claim[]>([])
  const [byType, setByType] = useState<ByType[]>([])
  const [byRegion, setByRegion] = useState<ByRegion[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)
  const [retrying, setRetrying] = useState(false)
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const fetchAll = useCallback(async () => {
    try {
      const [mRes, cRes, tRes, rRes] = await Promise.all([
        fetch(`${API_BASE}/api/insurance/metrics`),
        fetch(`${API_BASE}/api/insurance/claims?limit=30`),
        fetch(`${API_BASE}/api/insurance/by-type`),
        fetch(`${API_BASE}/api/insurance/by-region`),
      ])

      if (!mRes.ok || mRes.headers.get('content-type')?.includes('text/html')) {
        throw new Error(`HTTP ${mRes.status}`)
      }

      const [md, cd, td, rd] = await Promise.all([
        mRes.json(), cRes.json(), tRes.json(), rRes.json()
      ])

      if (md.success) { setMetrics(md.metrics); setError(null); setRetrying(false) }
      if (cd.success) setClaims(cd.claims || [])
      if (td.success) setByType(td.by_type || [])
      if (rd.success) setByRegion(rd.by_region || [])
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
                <span className="text-sm font-semibold text-white">Insurance Governance</span>
                <span className="px-2 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/25 text-emerald-400 text-[10px] font-medium">LIVE</span>
                <span className="px-2 py-0.5 rounded bg-white/[0.05] border border-white/10 text-white/40 text-[10px]">ADR-054</span>
              </div>
              <p className="text-[11px] text-white/35 mt-0.5">OMNIX Decision Governance Infrastructure — Global Insurance Vertical</p>
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

        {/* Access Notice when API unavailable */}
        {error && (
          <div className="flex items-start gap-3 p-4 rounded-xl bg-amber-400/8 border border-amber-400/25 text-amber-300/80 text-sm">
            <AlertTriangle size={16} className="mt-0.5 flex-shrink-0 text-amber-400/70" />
            <div className="flex-1 min-w-0">
              <span className="font-medium text-amber-200/90">Insurance Governance — Restricted Access</span>
              <p className="text-amber-300/60 text-xs mt-1 leading-relaxed">
                This vertical is currently in private testing and not yet open for public access.
                Full launch planned following our institutional pilot phase.
                For early access or institutional inquiries, contact{' '}
                <a href="mailto:contacto@omnixquantum.net" className="underline underline-offset-2 hover:text-amber-200/80 transition-colors">
                  contacto@omnixquantum.net
                </a>
              </p>
            </div>
          </div>
        )}

        {/* KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            {
              icon: <FileCheck size={18} className="text-blue-400" />,
              label: 'Total Claims Evaluated', sub: `${m?.claims_last_24h ?? 0} in last 24h`,
              value: loading ? '—' : (m?.total_claims ?? 0).toLocaleString(),
            },
            {
              icon: <CheckCircle size={18} className="text-emerald-400" />,
              label: 'Approval Rate', sub: `${m?.claims_approved ?? 0} approved`,
              value: loading ? '—' : `${((m?.approval_rate ?? 0) * 100).toFixed(1)}%`,
              valueClass: 'text-emerald-400',
            },
            {
              icon: <Shield size={18} className="text-[#C9A227]" />,
              label: 'Loss Avoided', sub: 'Fraudulent claims blocked',
              value: loading ? '—' : fmt(m?.loss_avoided_usd ?? 0),
              valueClass: 'text-[#C9A227]',
            },
            {
              icon: <AlertTriangle size={18} className="text-red-400" />,
              label: 'Fraud Blocks', sub: `Avg fraud score ${(m?.avg_fraud_score ?? 0).toFixed(1)}`,
              value: loading ? '—' : (m?.high_fraud_blocked ?? 0).toLocaleString(),
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
            { label: 'Total Approved', value: fmt(m?.total_approved_usd ?? 0), color: 'text-emerald-400' },
            { label: 'Total Blocked', value: fmt(m?.total_blocked_usd ?? 0), color: 'text-red-400' },
            { label: 'Avg Decision Score', value: `${(m?.avg_decision_score ?? 0).toFixed(1)}/100`, color: 'text-[#C9A227]' },
            { label: 'Simulation Cycles', value: (m?.simulation_cycles ?? 0).toLocaleString(), color: 'text-blue-400' },
          ].map((item, i) => (
            <div key={i} className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-4 flex items-center justify-between">
              <span className="text-xs text-white/40">{item.label}</span>
              <span className={`text-sm font-semibold ${item.color}`}>{loading ? '—' : item.value}</span>
            </div>
          ))}
        </div>

        {/* By Type + By Region */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* By Insurance Type */}
          <div className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-6">
            <div className="flex items-center gap-2 mb-5">
              <BarChart3 size={15} className="text-[#C9A227]" />
              <span className="text-sm font-medium text-white/80">By Insurance Type</span>
            </div>
            <div className="space-y-3">
              {byType.length === 0 ? (
                <div className="text-center py-8 text-white/20 text-sm">Collecting data...</div>
              ) : byType.map(t => (
                <div key={t.insurance_type} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: TYPE_COLORS[t.insurance_type] ?? '#666' }} />
                      <span className="text-white/70">{t.insurance_type}</span>
                      <span className="text-white/25">{t.total}</span>
                    </div>
                    <div className="flex items-center gap-3 text-white/40">
                      <span className="text-emerald-400/80">{(t.approval_rate * 100).toFixed(0)}% pass</span>
                      <span>{fmt(t.avg_claim_usd)} avg</span>
                    </div>
                  </div>
                  <div className="h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
                    <div className="h-full rounded-full transition-all duration-700"
                      style={{ width: `${t.approval_rate * 100}%`, backgroundColor: TYPE_COLORS[t.insurance_type] ?? '#666', opacity: 0.7 }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* By Region */}
          <div className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-6">
            <div className="flex items-center gap-2 mb-5">
              <Globe size={15} className="text-blue-400" />
              <span className="text-sm font-medium text-white/80">By Region</span>
            </div>
            <div className="space-y-2">
              {byRegion.length === 0 ? (
                <div className="text-center py-8 text-white/20 text-sm">Collecting data...</div>
              ) : byRegion.map(r => (
                <div key={r.region} className="flex items-center gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                  <span className="text-lg">{REGION_FLAGS[r.region] ?? '🌐'}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-white/70">{r.region}</span>
                      <span className="text-xs text-white/40">{r.total} claims</span>
                    </div>
                    <div className="h-1 bg-white/[0.04] rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500/60 rounded-full"
                        style={{ width: `${r.approval_rate * 100}%` }} />
                    </div>
                  </div>
                  <div className="text-right text-xs">
                    <div className="text-emerald-400/80">{(r.approval_rate * 100).toFixed(0)}%</div>
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
              <Activity size={15} className="text-[#C9A227]" />
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
              { id: 'CP-0', name: 'Signal Integrity', desc: 'Data completeness & quality', icon: <Zap size={12} /> },
              { id: 'CP-1', name: 'Probability Check', desc: 'Claim legitimacy probability', icon: <Activity size={12} /> },
              { id: 'CP-2', name: 'Risk Assessment', desc: 'Loss severity & fraud risk', icon: <AlertTriangle size={12} /> },
              { id: 'CP-3', name: 'Coherence Engine', desc: 'Evidence consistency', icon: <Shield size={12} /> },
              { id: 'CP-4', name: 'Trend Analysis', desc: 'Loss ratio stability', icon: <TrendingUp size={12} /> },
              { id: 'CP-5', name: 'Stress Test', desc: 'Reserve adequacy', icon: <BarChart3 size={12} /> },
              { id: 'CP-7', name: 'Policy Alignment', desc: 'Policy-claim match check', icon: <FileCheck size={12} /> },
              { id: 'CP-7b', name: 'FTI Trajectory', desc: 'Forward risk implication', icon: <Eye size={12} /> },
              { id: 'CP-8', name: 'Exposure Control', desc: 'Portfolio concentration', icon: <DollarSign size={12} /> },
              { id: 'CP-9', name: 'AML Gate', desc: 'Financial crime screening', icon: <Lock size={12} /> },
              { id: 'CP-10', name: 'Fraud Detection', desc: 'Behavioral fraud patterns', icon: <AlertTriangle size={12} /> },
              { id: 'TIE', name: 'Trajectory Invariant', desc: 'Bounded decision evolution', icon: <Globe size={12} /> },
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

        {/* Recent Claims Table */}
        <div className="rounded-xl bg-white/[0.02] border border-white/[0.06] overflow-hidden">
          <div className="p-5 border-b border-white/[0.05] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock size={14} className="text-white/40" />
              <span className="text-sm font-medium text-white/70">Recent Claims</span>
            </div>
            <span className="text-xs text-white/30">{claims.length} shown</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-white/[0.04]">
                  {['Claim ID', 'Type', 'Region', 'Amount', 'Fraud Score', 'Decision Score', 'Decision', 'Receipt'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-[10px] text-white/30 font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {claims.length === 0 ? (
                  <tr><td colSpan={8} className="px-4 py-12 text-center text-white/20">Collecting claims data...</td></tr>
                ) : claims.map(c => (
                  <tr key={c.claim_id} className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors">
                    <td className="px-4 py-3 font-mono text-[10px] text-white/50">{c.claim_id}</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-white/[0.05] text-[10px]"
                        style={{ color: TYPE_COLORS[c.insurance_type] ?? '#888' }}>
                        {c.insurance_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-white/50">
                      {REGION_FLAGS[c.region] ?? ''} {c.region}
                    </td>
                    <td className="px-4 py-3 text-white/70 font-mono">{fmt(c.claim_amount_usd)}</td>
                    <td className="px-4 py-3">
                      <span className={c.fraud_indicators > 50 ? 'text-red-400' : c.fraud_indicators > 25 ? 'text-amber-400' : 'text-emerald-400'}>
                        {c.fraud_indicators?.toFixed(1) ?? '—'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-white/60">{c.decision_score?.toFixed(1) ?? '—'}</td>
                    <td className="px-4 py-3"><DecisionBadge decision={c.decision} /></td>
                    <td className="px-4 py-3 font-mono text-[10px] text-white/30">{c.receipt_id?.slice(0, 16) ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Governance signals breakdown of last blocked claim */}
        {claims.find(c => c.decision === 'BLOCKED') && (() => {
          const blocked = claims.find(c => c.decision === 'BLOCKED')!
          return (
            <div className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-6">
              <div className="flex items-center gap-2 mb-5">
                <XCircle size={14} className="text-red-400" />
                <span className="text-sm font-medium text-white/70">Latest Blocked Claim — Signal Breakdown</span>
                <span className="text-[10px] text-white/30 ml-2 font-mono">{blocked.claim_id}</span>
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
          <span>OMNIX Decision Governance Infrastructure — Insurance Vertical (ADR-054)</span>
          <span>Auto-refresh every 30s · PQC-signed receipts · 11-checkpoint pipeline</span>
        </div>
      </div>
    </div>
  )
}
