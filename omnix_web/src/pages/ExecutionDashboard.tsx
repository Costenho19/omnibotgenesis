import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  Zap, ArrowLeft, RefreshCw, CheckCircle, XCircle,
  AlertTriangle, Clock, Filter, Shield, ChevronRight, Activity
} from 'lucide-react'
import { API_BASE } from '../lib/apiBase'

const REFRESH_MS = 10_000

interface ExecutionReceipt {
  order_id:            string
  decision_receipt_id: string
  asset:               string
  domain:              string
  direction:           string
  size_usd:            number
  final_status:        string
  intent_captured_at:  string | null
  filled_at:           string | null
  fill_price_usd:      number | null
  fill_pct:            number | null
  slippage_bps:        number | null
  rejection_code:      string | null
  rejection_detail:    string | null
  audit_trail:         Record<string, unknown>
}

interface ReceiptListResponse {
  receipts: ExecutionReceipt[]
  total:    number
  limit:    number
  offset:   number
  has_more: boolean
}

const STATUS_STYLES: Record<string, string> = {
  FILLED:  'bg-emerald-900/40 text-emerald-300 border-emerald-500/40',
  PENDING: 'bg-amber-900/40 text-amber-300 border-amber-500/40',
  PARTIAL: 'bg-blue-900/40 text-blue-300 border-blue-500/40',
  FAILED:  'bg-red-900/40 text-red-300 border-red-500/40',
}

const DIR_STYLES: Record<string, string> = {
  BUY:  'text-emerald-400',
  SELL: 'text-red-400',
  LONG: 'text-emerald-400',
  SHORT:'text-red-400',
}

const API_KEY_HEADER = { 'X-API-Key': 'OMNIX-DEMO-DASHBOARD-KEY' }

function fmt(n: number | null | undefined, decimals = 2, prefix = '') {
  if (n == null) return '—'
  return prefix + n.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
}

export default function ExecutionDashboard() {
  const [receipts,  setReceipts]  = useState<ExecutionReceipt[]>([])
  const [total,     setTotal]     = useState(0)
  const [loading,   setLoading]   = useState(true)
  const [error,     setError]     = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState('')
  const [offset,    setOffset]    = useState(0)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)
  const LIMIT = 20

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({
        limit:  String(LIMIT),
        offset: String(offset),
      })
      if (statusFilter) params.set('status', statusFilter)

      const res = await fetch(
        `${API_BASE}/api/governance/execution/receipts?${params}`,
        { headers: API_KEY_HEADER }
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json: ReceiptListResponse = await res.json()
      setReceipts(json.receipts ?? [])
      setTotal(json.total ?? 0)
      setLastRefresh(new Date())
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Connection error')
    } finally {
      setLoading(false)
    }
  }, [statusFilter, offset])

  useEffect(() => { fetchData() }, [fetchData])
  useEffect(() => {
    const t = setInterval(fetchData, REFRESH_MS)
    return () => clearInterval(t)
  }, [fetchData])

  const filled  = receipts.filter(r => r.final_status === 'FILLED').length
  const pending = receipts.filter(r => r.final_status === 'PENDING').length
  const failed  = receipts.filter(r => r.final_status === 'FAILED').length

  const totalVolume = receipts.reduce((s, r) => s + (r.size_usd ?? 0), 0)
  const avgSlippage = receipts.filter(r => r.slippage_bps != null).length > 0
    ? receipts.filter(r => r.slippage_bps != null).reduce((s, r) => s + (r.slippage_bps ?? 0), 0) /
      receipts.filter(r => r.slippage_bps != null).length
    : null

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
              <div className="w-8 h-8 rounded-lg bg-blue-600/30 border border-blue-500/40 flex items-center justify-center">
                <Zap className="w-4 h-4 text-blue-400" />
              </div>
              <div>
                <h1 className="text-lg font-bold">Execution Integrity Layer</h1>
                <p className="text-xs text-slate-400">ADR-131 — Decision → Execution Audit Chain</p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
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
        {/* KPIs */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {[
            { label: 'Total Receipts', value: total, accent: 'text-white' },
            { label: 'Filled',  value: filled,  accent: 'text-emerald-400' },
            { label: 'Pending', value: pending, accent: 'text-amber-400' },
            { label: 'Failed',  value: failed,  accent: failed > 0 ? 'text-red-400' : 'text-slate-400' },
            { label: 'Avg Slippage', value: avgSlippage != null ? `${avgSlippage.toFixed(1)} bps` : '—', accent: 'text-blue-300' },
          ].map(k => (
            <div key={k.label} className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4">
              <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">{k.label}</p>
              <p className={`text-2xl font-bold font-mono ${k.accent}`}>{k.value}</p>
            </div>
          ))}
        </div>

        <div className="bg-slate-800/40 border border-slate-700/30 rounded-xl p-4 flex items-center gap-4 text-sm">
          <Activity className="w-4 h-4 text-blue-400 shrink-0" />
          <span className="text-slate-300">
            Total volume (page): <span className="font-mono font-semibold text-white">${totalVolume.toLocaleString()}</span>
          </span>
          {lastRefresh && (
            <span className="text-slate-500 text-xs ml-auto">
              Last refresh: {lastRefresh.toLocaleTimeString()}
            </span>
          )}
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={statusFilter}
            onChange={e => { setStatusFilter(e.target.value); setOffset(0) }}
            className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
          >
            <option value="">All statuses</option>
            {['FILLED', 'PENDING', 'PARTIAL', 'FAILED'].map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        {error && (
          <div className="bg-red-900/30 border border-red-500/40 rounded-xl p-4 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-400 shrink-0" />
            <p className="text-sm text-red-300">{error}</p>
          </div>
        )}

        {/* Receipt Table */}
        <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700/50 text-left">
                  {['Order ID', 'Asset', 'Domain', 'Dir', 'Size USD', 'Status', 'Slippage', 'Fill %', 'Intent Captured'].map(h => (
                    <th key={h} className="px-4 py-3 text-xs text-slate-400 font-medium uppercase tracking-wider whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {loading && receipts.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-12 text-center text-slate-400">
                      <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2" />
                      Loading execution receipts…
                    </td>
                  </tr>
                ) : receipts.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-12 text-center text-slate-400">
                      <Shield className="w-8 h-8 mx-auto mb-2 opacity-40" />
                      No execution receipts found
                    </td>
                  </tr>
                ) : (
                  receipts.map((r, i) => (
                    <tr
                      key={r.order_id}
                      className={`border-b border-slate-700/30 hover:bg-slate-700/30 transition-colors ${i % 2 === 0 ? '' : 'bg-slate-800/20'}`}
                    >
                      <td className="px-4 py-3 font-mono text-xs text-slate-300 whitespace-nowrap">
                        {r.order_id?.slice(0, 16)}…
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-white whitespace-nowrap">{r.asset}</td>
                      <td className="px-4 py-3 text-xs text-slate-400 whitespace-nowrap">
                        {r.domain?.toUpperCase()}
                      </td>
                      <td className={`px-4 py-3 font-semibold text-xs whitespace-nowrap ${DIR_STYLES[r.direction?.toUpperCase()] ?? 'text-white'}`}>
                        {r.direction}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-white whitespace-nowrap">
                        ${r.size_usd?.toLocaleString() ?? '—'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className={`px-2 py-0.5 rounded border text-xs font-semibold font-mono ${STATUS_STYLES[r.final_status] ?? 'bg-slate-700 text-slate-300 border-slate-600'}`}>
                          {r.final_status}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-slate-300 whitespace-nowrap">
                        {r.slippage_bps != null ? `${r.slippage_bps.toFixed(1)} bps` : '—'}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-slate-300 whitespace-nowrap">
                        {r.fill_pct != null ? `${r.fill_pct.toFixed(1)}%` : '—'}
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-400 whitespace-nowrap">
                        {r.intent_captured_at ? new Date(r.intent_captured_at).toLocaleTimeString() : '—'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {total > LIMIT && (
            <div className="px-4 py-3 border-t border-slate-700/50 flex items-center justify-between text-xs text-slate-400">
              <span>{offset + 1}–{Math.min(offset + LIMIT, total)} of {total}</span>
              <div className="flex gap-2">
                <button
                  onClick={() => setOffset(o => Math.max(0, o - LIMIT))}
                  disabled={offset === 0}
                  className="px-3 py-1 bg-slate-700 rounded disabled:opacity-40 hover:bg-slate-600 transition-colors"
                >
                  Prev
                </button>
                <button
                  onClick={() => setOffset(o => o + LIMIT)}
                  disabled={offset + LIMIT >= total}
                  className="px-3 py-1 bg-slate-700 rounded disabled:opacity-40 hover:bg-slate-600 transition-colors"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Design Invariant Note */}
        <div className="bg-blue-900/20 border border-blue-500/30 rounded-xl p-4 text-xs text-blue-300 space-y-1">
          <p className="font-semibold flex items-center gap-2">
            <Shield className="w-3.5 h-3.5" />
            ADR-131 Invariant
          </p>
          <p>
            Every governance decision that reaches execution must produce an ExecutionReceipt.
            Intent capture (pre-order) must succeed before trade is placed — failure returns 503 and the trade is halted.
            This table closes the decision → execution audit chain.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-500 pt-2">
          <CheckCircle className="w-3.5 h-3.5 text-emerald-500" />
          <span>Execution Integrity Layer — ADR-131</span>
          <ChevronRight className="w-3 h-3" />
          <Link to="/audit" className="hover:text-slate-300 transition-colors">Back to Audit</Link>
        </div>
      </div>
    </div>
  )
}
