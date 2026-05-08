import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  AlertTriangle, ArrowLeft, RefreshCw, CheckCircle,
  XCircle, Clock, Shield, Activity, Filter, ChevronRight
} from 'lucide-react'
import { API_BASE } from '../lib/apiBase'

const REFRESH_MS = 12_000

interface Recommendation {
  rec_id:        string
  domain:        string
  action_code:   string
  severity:      string
  urgency:       string
  status:        string
  summary:       string
  detail:        string
  created_at:    string
  updated_at:    string
  resolved_at:   string | null
  ack_at:        string | null
  resolution_note: string | null
}

interface Summary {
  by_status:      Record<string, number>
  by_action_code: Record<string, number>
  total:          number
  generated_at:   string
}

const SEVERITY_STYLES: Record<string, string> = {
  CRITICAL: 'bg-red-900/40 border-red-500/40 text-red-300',
  HIGH:     'bg-orange-900/40 border-orange-500/40 text-orange-300',
  MEDIUM:   'bg-amber-900/40 border-amber-500/40 text-amber-300',
  LOW:      'bg-slate-700/40 border-slate-500/40 text-slate-300',
}

const STATUS_STYLES: Record<string, string> = {
  ACTIVE:       'bg-red-900/40 text-red-300',
  ACKNOWLEDGED: 'bg-amber-900/40 text-amber-300',
  RESOLVED:     'bg-emerald-900/40 text-emerald-300',
  EXPIRED:      'bg-slate-700/40 text-slate-400',
}

const API_KEY_HEADER = { 'X-API-Key': 'OMNIX-DEMO-DASHBOARD-KEY' }

export default function AnomalyDashboard() {
  const [active,   setActive]   = useState<Recommendation[]>([])
  const [summary,  setSummary]  = useState<Summary | null>(null)
  const [loading,  setLoading]  = useState(true)
  const [error,    setError]    = useState<string | null>(null)
  const [domain,   setDomain]   = useState('')
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const domainQ = domain ? `?domain=${domain}` : ''
      const [activeRes, summaryRes] = await Promise.all([
        fetch(`${API_BASE}/api/governance/anomaly/active${domainQ}`, { headers: API_KEY_HEADER }),
        fetch(`${API_BASE}/api/governance/anomaly/summary${domainQ}`, { headers: API_KEY_HEADER }),
      ])

      if (activeRes.ok) {
        const j = await activeRes.json()
        setActive(j.recommendations ?? [])
      }
      if (summaryRes.ok) {
        const j = await summaryRes.json()
        setSummary(j)
      }
      setLastRefresh(new Date())
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Connection error')
    } finally {
      setLoading(false)
    }
  }, [domain])

  useEffect(() => { fetchData() }, [fetchData])
  useEffect(() => {
    const t = setInterval(fetchData, REFRESH_MS)
    return () => clearInterval(t)
  }, [fetchData])

  const total        = summary?.total ?? 0
  const activeCount  = summary?.by_status?.ACTIVE ?? 0
  const resolvedCount = summary?.by_status?.RESOLVED ?? 0
  const ackCount     = summary?.by_status?.ACKNOWLEDGED ?? 0

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
              <div className="w-8 h-8 rounded-lg bg-orange-600/30 border border-orange-500/40 flex items-center justify-center">
                <AlertTriangle className="w-4 h-4 text-orange-400" />
              </div>
              <div>
                <h1 className="text-lg font-bold">Anomaly Response Engine</h1>
                <p className="text-xs text-slate-400">ADR-129 — Active Anomaly Recommendations</p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {activeCount > 0 && (
              <span className="px-2 py-1 bg-red-500/20 border border-red-500/40 rounded text-xs text-red-300 font-mono animate-pulse">
                {activeCount} ACTIVE
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
        {/* KPI Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Total Recommendations', value: total, accent: 'text-white' },
            { label: 'Active',     value: activeCount,  accent: activeCount > 0 ? 'text-red-400' : 'text-emerald-400' },
            { label: 'Acknowledged', value: ackCount,   accent: 'text-amber-400' },
            { label: 'Resolved',   value: resolvedCount, accent: 'text-emerald-400' },
          ].map(k => (
            <div key={k.label} className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4">
              <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">{k.label}</p>
              <p className={`text-3xl font-bold font-mono ${k.accent}`}>{k.value}</p>
            </div>
          ))}
        </div>

        {/* Filter */}
        <div className="flex items-center gap-3">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={domain}
            onChange={e => setDomain(e.target.value)}
            className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-orange-500"
          >
            <option value="">All domains</option>
            {['trading','insurance','energy','medical','robotics','real_estate','agents','stablecoin','defense','islamic_credit'].map(d => (
              <option key={d} value={d}>{d.replace('_', ' ').toUpperCase()}</option>
            ))}
          </select>
          {lastRefresh && (
            <p className="text-xs text-slate-500">
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

        {/* Action Code Breakdown */}
        {summary?.by_action_code && Object.keys(summary.by_action_code).length > 0 && (
          <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
              <Activity className="w-4 h-4 text-orange-400" />
              By Action Code
            </h2>
            <div className="flex flex-wrap gap-2">
              {Object.entries(summary.by_action_code).map(([code, count]) => (
                <div key={code} className="bg-slate-700/50 rounded-lg px-3 py-1.5 text-xs flex items-center gap-2">
                  <span className="font-mono text-orange-300">{code}</span>
                  <span className="bg-orange-900/40 text-orange-200 px-1.5 py-0.5 rounded font-bold">{count}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Active Recommendations */}
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
            <Shield className="w-4 h-4 text-orange-400" />
            Active Recommendations
          </h2>
          {loading && active.length === 0 ? (
            <div className="flex items-center justify-center py-16 text-slate-400">
              <RefreshCw className="w-5 h-5 animate-spin mr-2" />
              Loading…
            </div>
          ) : active.length === 0 ? (
            <div className="bg-emerald-900/20 border border-emerald-500/30 rounded-xl p-6 flex items-center gap-3">
              <CheckCircle className="w-6 h-6 text-emerald-400 shrink-0" />
              <div>
                <p className="font-semibold text-emerald-300">No active anomalies</p>
                <p className="text-xs text-slate-400 mt-1">
                  Governance is operating within normal parameters.
                  {domain && ` Domain filter: ${domain}.`}
                </p>
              </div>
            </div>
          ) : (
            active.map(rec => (
              <div
                key={rec.rec_id}
                className={`border rounded-xl p-5 space-y-3 ${SEVERITY_STYLES[rec.severity] ?? 'bg-slate-800/60 border-slate-700/50 text-slate-300'}`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <XCircle className="w-5 h-5 shrink-0 opacity-80" />
                    <div>
                      <p className="font-semibold text-sm font-mono">{rec.action_code}</p>
                      <p className="text-xs opacity-70 mt-0.5">{rec.domain?.toUpperCase()}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className={`px-2 py-0.5 rounded text-xs font-mono font-semibold ${STATUS_STYLES[rec.status] ?? ''}`}>
                      {rec.status}
                    </span>
                    <span className="text-xs opacity-60 font-mono">{rec.rec_id}</span>
                  </div>
                </div>
                <p className="text-sm opacity-90">{rec.summary}</p>
                <p className="text-xs opacity-60">{rec.detail}</p>
                <div className="flex items-center gap-4 text-xs opacity-60 pt-1">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(rec.created_at).toLocaleString()}
                  </span>
                  <span>Urgency: {rec.urgency}</span>
                  <span>Severity: {rec.severity}</span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center gap-2 text-xs text-slate-500 pt-2">
          <CheckCircle className="w-3.5 h-3.5 text-emerald-500" />
          <span>Anomaly Response Engine — ADR-129 — Non-destructive recommendations only</span>
          <ChevronRight className="w-3 h-3" />
          <Link to="/audit" className="hover:text-slate-300 transition-colors">Back to Audit</Link>
        </div>
      </div>
    </div>
  )
}
