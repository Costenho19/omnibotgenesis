import React, { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  Activity, ArrowLeft, RefreshCw, TrendingUp, TrendingDown,
  Minus, AlertTriangle, CheckCircle, BarChart3, Zap, Shield
} from 'lucide-react'
import { API_BASE } from '../lib/apiBase'

const REFRESH_MS = 15_000

interface OscillationPhase {
  phase: string
  description: string
  start_week: number | null
  end_week: number | null
  duration_weeks: number | null
}

interface OscillationData {
  domain: string
  view: string
  generated_at: string
  num_weeks: number
  adr: string
  oscillation_profile?: {
    dominant_phase: string
    phase_history: OscillationPhase[]
    weekly_series: Array<{
      week: string
      block_rate: number
      dci: number
      hold_rate: number
      decisions: number
    }>
  }
  asymmetry?: {
    block_rate_asymmetry: number
    dci_asymmetry: number
    interpretation: string
  }
  dampening?: {
    coefficient: number
    trend: string
    interpretation: string
  }
  hesitation_index?: number
  governance_quality_score?: number
  demo?: boolean
  note?: string
}

const DOMAINS = [
  'trading', 'insurance', 'energy', 'medical', 'robotics',
  'real_estate', 'agents', 'stablecoin', 'defense', 'islamic_credit',
]

const PHASE_COLORS: Record<string, string> = {
  CONTRACTION:  'text-red-400',
  EXPANSION:    'text-emerald-400',
  STABILIZING:  'text-blue-400',
  TRANSITIONAL: 'text-amber-400',
  NEUTRAL:      'text-slate-400',
}

const PHASE_ICONS: Record<string, React.ReactElement> = {
  CONTRACTION:  <TrendingDown className="w-4 h-4 text-red-400" />,
  EXPANSION:    <TrendingUp   className="w-4 h-4 text-emerald-400" />,
  STABILIZING:  <Minus        className="w-4 h-4 text-blue-400" />,
  TRANSITIONAL: <Activity     className="w-4 h-4 text-amber-400" />,
  NEUTRAL:      <Minus        className="w-4 h-4 text-slate-400" />,
}

function Pill({ text, color }: { text: string; color: string }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-semibold ${color}`}>
      {text}
    </span>
  )
}

function MetricCard({ label, value, sub, accent }: {
  label: string; value: string | number; sub?: string; accent?: string
}) {
  return (
    <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4">
      <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-2xl font-bold font-mono ${accent ?? 'text-white'}`}>{value}</p>
      {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
    </div>
  )
}

export default function OscillationDashboard() {
  const [domain,    setDomain]    = useState('trading')
  const [numWeeks,  setNumWeeks]  = useState(12)
  const [data,      setData]      = useState<OscillationData | null>(null)
  const [loading,   setLoading]   = useState(true)
  const [error,     setError]     = useState<string | null>(null)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(
        `${API_BASE}/api/analytics/oscillation?domain=${domain}&view=full&num_weeks=${numWeeks}`
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      setData(json)
      setLastRefresh(new Date())
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Connection error')
    } finally {
      setLoading(false)
    }
  }, [domain, numWeeks])

  useEffect(() => { fetchData() }, [fetchData])
  useEffect(() => {
    const t = setInterval(fetchData, REFRESH_MS)
    return () => clearInterval(t)
  }, [fetchData])

  // Fast retry on error (3 s) — recovers from startup race condition
  useEffect(() => {
    if (!error) return
    const t = setTimeout(fetchData, 3000)
    return () => clearTimeout(t)
  }, [error, fetchData])

  const profile   = data?.oscillation_profile
  const asymmetry = data?.asymmetry
  const dampening = data?.dampening
  const phase     = profile?.dominant_phase ?? 'NEUTRAL'
  const series    = profile?.weekly_series ?? []

  const maxBlockRate = series.length > 0 ? Math.max(...series.map(s => s.block_rate)) : 1

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100">
      {/* Header */}
      <div className="border-b border-slate-700/50 bg-slate-900/95 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/audit" className="text-slate-400 hover:text-white transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-purple-600/30 border border-purple-500/40 flex items-center justify-center">
                <Activity className="w-4 h-4 text-purple-400" />
              </div>
              <div>
                <h1 className="text-lg font-bold">Oscillation Insight Engine</h1>
                <p className="text-xs text-slate-400">ADR-134 — Governance Phase Analytics</p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {data?.demo && (
              <span className="px-2 py-1 bg-amber-500/20 border border-amber-500/40 rounded text-xs text-amber-300 font-mono">
                DEMO MODE
              </span>
            )}
            <button
              onClick={fetchData}
              disabled={loading}
              className="flex items-center gap-2 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Controls */}
        <div className="flex flex-wrap gap-4 items-center">
          <div>
            <label className="text-xs text-slate-400 block mb-1">Domain</label>
            <select
              value={domain}
              onChange={e => setDomain(e.target.value)}
              className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-purple-500"
            >
              {DOMAINS.map(d => (
                <option key={d} value={d}>{d.replace('_', ' ').toUpperCase()}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Window (weeks)</label>
            <select
              value={numWeeks}
              onChange={e => setNumWeeks(Number(e.target.value))}
              className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-purple-500"
            >
              {[4, 8, 12, 16, 26].map(w => (
                <option key={w} value={w}>{w} weeks</option>
              ))}
            </select>
          </div>
          {lastRefresh && (
            <p className="text-xs text-slate-500 self-end pb-2">
              Last refresh: {lastRefresh.toLocaleTimeString()}
            </p>
          )}
        </div>

        {error && (
          <div className="bg-red-900/30 border border-red-500/40 rounded-xl p-4 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-400 shrink-0" />
            <p className="text-sm text-red-300">{error}</p>
          </div>
        )}

        {data && (
          <>
            {/* KPI Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard
                label="Dominant Phase"
                value={phase}
                sub={`Last ${numWeeks} weeks`}
                accent={PHASE_COLORS[phase] ?? 'text-white'}
              />
              <MetricCard
                label="Hesitation Index"
                value={data.hesitation_index != null ? `${data.hesitation_index.toFixed(1)}%` : '—'}
                sub="Decision hesitation rate"
                accent={
                  (data.hesitation_index ?? 0) > 20 ? 'text-red-400'
                  : (data.hesitation_index ?? 0) > 10 ? 'text-amber-400'
                  : 'text-emerald-400'
                }
              />
              <MetricCard
                label="Governance Quality"
                value={data.governance_quality_score != null ? `${data.governance_quality_score.toFixed(0)}/100` : '—'}
                sub="Composite quality score"
                accent={
                  (data.governance_quality_score ?? 0) >= 80 ? 'text-emerald-400'
                  : (data.governance_quality_score ?? 0) >= 60 ? 'text-amber-400'
                  : 'text-red-400'
                }
              />
              <MetricCard
                label="Dampening Trend"
                value={dampening?.trend ?? '—'}
                sub={dampening?.interpretation ?? 'Oscillation dampening coefficient'}
                accent={
                  dampening?.trend === 'DECREASING' ? 'text-emerald-400'
                  : dampening?.trend === 'INCREASING' ? 'text-red-400'
                  : 'text-blue-400'
                }
              />
            </div>

            {/* Phase History */}
            {profile?.phase_history && profile.phase_history.length > 0 && (
              <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-6">
                <h2 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-purple-400" />
                  Phase History
                </h2>
                <div className="flex flex-wrap gap-2">
                  {profile.phase_history.map((ph, i) => (
                    <div key={i} className="bg-slate-700/50 rounded-lg px-3 py-2 text-xs space-y-1">
                      <div className="flex items-center gap-1.5">
                        {PHASE_ICONS[ph.phase] ?? <Minus className="w-4 h-4 text-slate-400" />}
                        <span className={`font-semibold ${PHASE_COLORS[ph.phase] ?? 'text-white'}`}>
                          {ph.phase}
                        </span>
                      </div>
                      {ph.duration_weeks && (
                        <p className="text-slate-400">{ph.duration_weeks}w</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Weekly Series Bar Chart */}
            {series.length > 0 && (
              <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-6">
                <h2 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-purple-400" />
                  Weekly Block Rate Series
                </h2>
                <div className="flex items-end gap-1 h-32">
                  {series.map((s, i) => {
                    const pct = maxBlockRate > 0 ? (s.block_rate / maxBlockRate) * 100 : 0
                    return (
                      <div key={i} className="flex-1 flex flex-col items-center gap-1 group relative">
                        <div
                          className="w-full bg-purple-500/70 hover:bg-purple-400/90 rounded-t transition-all cursor-pointer"
                          style={{ height: `${Math.max(pct, 2)}%` }}
                          title={`${s.week}: ${s.block_rate.toFixed(1)}% block rate`}
                        />
                        {i % Math.ceil(series.length / 6) === 0 && (
                          <span className="text-slate-500 text-[9px] rotate-45 origin-left">
                            {s.week?.slice(5) ?? ''}
                          </span>
                        )}
                      </div>
                    )
                  })}
                </div>
                <div className="flex justify-between text-xs text-slate-500 mt-6">
                  <span>{series[0]?.week}</span>
                  <span>Block Rate %</span>
                  <span>{series[series.length - 1]?.week}</span>
                </div>
              </div>
            )}

            {/* Asymmetry + Dampening Detail */}
            <div className="grid md:grid-cols-2 gap-4">
              {asymmetry && (
                <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5">
                  <h2 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
                    <Zap className="w-4 h-4 text-amber-400" />
                    Asymmetry Analysis
                  </h2>
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Block Rate Asymmetry</span>
                      <span className="font-mono text-white">{asymmetry.block_rate_asymmetry?.toFixed(3)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">DCI Asymmetry</span>
                      <span className="font-mono text-white">{asymmetry.dci_asymmetry?.toFixed(3)}</span>
                    </div>
                    <p className="text-xs text-slate-400 bg-slate-700/50 rounded p-2 mt-2">
                      {asymmetry.interpretation}
                    </p>
                  </div>
                </div>
              )}
              {dampening && (
                <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5">
                  <h2 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
                    <Shield className="w-4 h-4 text-blue-400" />
                    Dampening Coefficient
                  </h2>
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Coefficient</span>
                      <span className="font-mono text-white">{dampening.coefficient?.toFixed(4)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Trend</span>
                      <Pill
                        text={dampening.trend}
                        color={
                          dampening.trend === 'DECREASING' ? 'bg-emerald-900/40 text-emerald-300'
                          : dampening.trend === 'INCREASING' ? 'bg-red-900/40 text-red-300'
                          : 'bg-blue-900/40 text-blue-300'
                        }
                      />
                    </div>
                    <p className="text-xs text-slate-400 bg-slate-700/50 rounded p-2 mt-2">
                      {dampening.interpretation}
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center gap-2 text-xs text-slate-500 pt-2">
              <CheckCircle className="w-3.5 h-3.5 text-emerald-500" />
              <span>
                Oscillation Insight Engine — {data.adr} — {data.num_weeks}-week window —{' '}
                {new Date(data.generated_at).toLocaleString()}
              </span>
            </div>
          </>
        )}

        {loading && !data && (
          <div className="flex items-center justify-center py-24 text-slate-400">
            <RefreshCw className="w-6 h-6 animate-spin mr-3" />
            Loading oscillation data…
          </div>
        )}
      </div>
    </div>
  )
}
