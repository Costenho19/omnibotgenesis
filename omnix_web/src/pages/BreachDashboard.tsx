import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  ShieldOff, ArrowLeft, RefreshCw, CheckCircle, XCircle,
  AlertTriangle, Clock, Shield, Activity, Lock, Unlock
} from 'lucide-react'
import { API_BASE } from '../lib/apiBase'

const REFRESH_MS = 8_000

interface ContainmentStatus {
  is_contained:     boolean
  active_event_id:  string | null
  trigger_code:     string | null
  severity:         string | null
  summary:          string | null
  triggered_at:     string | null
  triggered_by:     string | null
  total_events:     number
  last_event_at:    string | null
  evaluated_at:     string
  adr:              string
  design_invariant: string
}

interface HistoryEvent {
  event_id:     string
  status:       string
  trigger_code: string
  severity:     string
  summary:      string
  triggered_by: string
  released_by:  string | null
  release_note: string | null
  triggered_at: string
  released_at:  string | null
  is_active:    boolean
}

const SEVERITY_BG: Record<string, string> = {
  CRITICAL: 'bg-red-900/50 border-red-500/50',
  HIGH:     'bg-orange-900/40 border-orange-500/40',
  MEDIUM:   'bg-amber-900/40 border-amber-500/40',
}

const API_KEY_HEADER = { 'X-API-Key': 'OMNIX-DEMO-DASHBOARD-KEY' }

export default function BreachDashboard() {
  const [status,   setStatus]   = useState<ContainmentStatus | null>(null)
  const [history,  setHistory]  = useState<HistoryEvent[]>([])
  const [loading,  setLoading]  = useState(true)
  const [error,    setError]    = useState<string | null>(null)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [statusRes, histRes] = await Promise.all([
        fetch(`${API_BASE}/api/governance/breach/status`),
        fetch(`${API_BASE}/api/governance/breach/history?limit=20`, { headers: API_KEY_HEADER }),
      ])
      if (statusRes.ok) setStatus(await statusRes.json())
      if (histRes.ok) {
        const j = await histRes.json()
        setHistory(j.events ?? [])
      }
      setLastRefresh(new Date())
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Connection error')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])
  useEffect(() => {
    const t = setInterval(fetchData, REFRESH_MS)
    return () => clearInterval(t)
  }, [fetchData])

  const contained = status?.is_contained ?? false

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100">
      {/* Header */}
      <div className={`border-b sticky top-0 z-10 ${contained ? 'border-red-500/60 bg-red-950/80' : 'border-slate-700/50 bg-slate-900/95'}`}>
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/audit" className="text-slate-400 hover:text-white transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div className="flex items-center gap-3">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${contained ? 'bg-red-600/50 border border-red-500/60' : 'bg-emerald-600/30 border border-emerald-500/40'}`}>
                {contained ? <ShieldOff className="w-4 h-4 text-red-400" /> : <Shield className="w-4 h-4 text-emerald-400" />}
              </div>
              <div>
                <h1 className="text-lg font-bold">Breach Containment Engine</h1>
                <p className="text-xs text-slate-400">ADR-142 — Execution Environment Security</p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {contained && (
              <span className="px-3 py-1 bg-red-600/30 border border-red-500/50 rounded text-sm text-red-300 font-bold animate-pulse flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5" />
                CONTAINED
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
        {/* Status Banner */}
        {status && (
          <div className={`rounded-xl p-6 border ${contained
            ? 'bg-red-900/30 border-red-500/50'
            : 'bg-emerald-900/20 border-emerald-500/30'
          }`}>
            <div className="flex items-start gap-4">
              <div className={`w-14 h-14 rounded-xl flex items-center justify-center shrink-0 ${contained ? 'bg-red-900/50' : 'bg-emerald-900/30'}`}>
                {contained
                  ? <ShieldOff className="w-8 h-8 text-red-400" />
                  : <Shield className="w-8 h-8 text-emerald-400" />
                }
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h2 className={`text-xl font-bold ${contained ? 'text-red-300' : 'text-emerald-300'}`}>
                    {contained ? '⛔ CONTAINMENT ACTIVE' : '✅ SYSTEM CLEAR'}
                  </h2>
                  {status.severity && (
                    <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold ${
                      status.severity === 'CRITICAL' ? 'bg-red-800 text-red-200'
                      : status.severity === 'HIGH' ? 'bg-orange-800 text-orange-200'
                      : 'bg-amber-800 text-amber-200'
                    }`}>
                      {status.severity}
                    </span>
                  )}
                </div>
                {contained && status.summary && (
                  <p className="text-sm text-red-200 mb-3">{status.summary}</p>
                )}
                {!contained && (
                  <p className="text-sm text-emerald-200/70">
                    No active breach events. Governance decisions are operating normally.
                  </p>
                )}
                <div className="flex flex-wrap gap-4 text-xs text-slate-400 mt-3">
                  {status.active_event_id && (
                    <span className="font-mono">Event: {status.active_event_id}</span>
                  )}
                  {status.trigger_code && (
                    <span>Trigger: <span className="text-white font-mono">{status.trigger_code}</span></span>
                  )}
                  {status.triggered_by && (
                    <span>By: <span className="text-white">{status.triggered_by}</span></span>
                  )}
                  {status.triggered_at && (
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(status.triggered_at).toLocaleString()}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* KPIs */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4">
            <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">Total Events</p>
            <p className="text-3xl font-bold font-mono text-white">{status?.total_events ?? 0}</p>
          </div>
          <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4">
            <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">Current Status</p>
            <p className={`text-xl font-bold font-mono ${contained ? 'text-red-400' : 'text-emerald-400'}`}>
              {contained ? 'CONTAINED' : 'CLEAR'}
            </p>
          </div>
          <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4">
            <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">Last Event</p>
            <p className="text-sm font-mono text-white">
              {status?.last_event_at ? new Date(status.last_event_at).toLocaleString() : 'None'}
            </p>
          </div>
        </div>

        {error && (
          <div className="bg-red-900/30 border border-red-500/40 rounded-xl p-4 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-400 shrink-0" />
            <p className="text-sm text-red-300">{error}</p>
          </div>
        )}

        {/* Event History */}
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
            <Activity className="w-4 h-4 text-red-400" />
            Event History
            {lastRefresh && (
              <span className="text-xs text-slate-500 font-normal ml-auto">
                Refreshed {lastRefresh.toLocaleTimeString()}
              </span>
            )}
          </h2>

          {history.length === 0 ? (
            <div className="bg-slate-800/40 border border-slate-700/40 rounded-xl p-8 text-center text-slate-400">
              <Shield className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p>No breach events on record. System has never been contained.</p>
            </div>
          ) : (
            history.map(ev => (
              <div
                key={ev.event_id}
                className={`border rounded-xl p-5 space-y-2 ${
                  ev.is_active
                    ? SEVERITY_BG[ev.severity] ?? 'bg-slate-800/60 border-slate-700/50'
                    : 'bg-slate-800/40 border-slate-700/30'
                }`}
              >
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    {ev.is_active
                      ? <Lock className="w-4 h-4 text-red-400 shrink-0" />
                      : <Unlock className="w-4 h-4 text-emerald-400 shrink-0" />
                    }
                    <span className="font-mono text-sm font-semibold">{ev.trigger_code}</span>
                    <span className={`px-2 py-0.5 rounded text-xs font-mono ${
                      ev.status === 'ACTIVE' ? 'bg-red-900/50 text-red-300'
                      : 'bg-emerald-900/40 text-emerald-300'
                    }`}>{ev.status}</span>
                  </div>
                  <span className="text-xs text-slate-400 font-mono">{ev.event_id}</span>
                </div>
                <p className="text-sm text-slate-200">{ev.summary}</p>
                <div className="flex flex-wrap gap-4 text-xs text-slate-400">
                  <span>Severity: <span className={`font-semibold ${
                    ev.severity === 'CRITICAL' ? 'text-red-300'
                    : ev.severity === 'HIGH' ? 'text-orange-300'
                    : 'text-amber-300'
                  }`}>{ev.severity}</span></span>
                  <span>By: <span className="text-white">{ev.triggered_by}</span></span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(ev.triggered_at).toLocaleString()}
                  </span>
                  {ev.released_at && (
                    <span className="text-emerald-400">
                      Released {new Date(ev.released_at).toLocaleString()} by {ev.released_by}
                    </span>
                  )}
                </div>
                {ev.release_note && (
                  <p className="text-xs text-slate-400 bg-slate-800/50 rounded p-2 italic">
                    Release note: {ev.release_note}
                  </p>
                )}
              </div>
            ))
          )}
        </div>

        {/* Invariant */}
        <div className="bg-slate-800/40 border border-slate-600/30 rounded-xl p-4 text-xs text-slate-400 space-y-1">
          <p className="font-semibold text-slate-300 flex items-center gap-2">
            <Shield className="w-3.5 h-3.5" />
            ADR-142 Design Invariant
          </p>
          {status?.design_invariant && <p>{status.design_invariant}</p>}
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-500 pt-2">
          <CheckCircle className="w-3.5 h-3.5 text-emerald-500" />
          <span>Breach Containment Engine — ADR-142</span>
        </div>
      </div>
    </div>
  )
}
