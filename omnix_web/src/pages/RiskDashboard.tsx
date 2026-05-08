import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  BarChart3, ArrowLeft, RefreshCw, CheckCircle,
  AlertTriangle, Filter, Layers, ChevronRight
} from 'lucide-react'
import { API_BASE } from '../lib/apiBase'

const REFRESH_MS = 15_000

interface VectorScores {
  financial: number | null
  technical: number | null
  legal:     number | null
  human:     number | null
}

interface Assessment {
  assessment_id:    string
  subject:          string
  client_domain:    string | null
  decision:         string
  composite_score:  number | null
  vector_scores:    VectorScores
  hard_block_vector: string | null
  assessed_by:      string
  assessed_at:      string
}

interface Summary {
  total_assessments: number
  by_decision:       Record<string, number>
  averages: {
    composite:  number | null
    financial:  number | null
    technical:  number | null
    legal:      number | null
    human:      number | null
  }
}

interface Catalog {
  vectors:         string[]
  default_weights: Record<string, number>
  thresholds:      { blocked: number; review: number; hard_block_per_vector: number }
  decision_logic:  string
}

const DECISION_STYLES: Record<string, string> = {
  APPROVED: 'bg-emerald-900/40 text-emerald-300 border-emerald-500/40',
  REVIEW:   'bg-amber-900/40 text-amber-300 border-amber-500/40',
  BLOCKED:  'bg-red-900/40 text-red-300 border-red-500/40',
}

const SCORE_COLOR = (s: number | null) => {
  if (s == null) return 'text-slate-400'
  if (s >= 80) return 'text-red-400'
  if (s >= 60) return 'text-amber-400'
  return 'text-emerald-400'
}

const API_KEY_HEADER = { 'X-API-Key': 'OMNIX-DEMO-DASHBOARD-KEY' }

function ScoreBar({ score }: { score: number | null }) {
  if (score == null) return <span className="text-slate-500 text-xs">—</span>
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${
            score >= 80 ? 'bg-red-500' : score >= 60 ? 'bg-amber-500' : 'bg-emerald-500'
          }`}
          style={{ width: `${score}%` }}
        />
      </div>
      <span className={`text-xs font-mono font-semibold w-10 text-right ${SCORE_COLOR(score)}`}>
        {score.toFixed(0)}
      </span>
    </div>
  )
}

export default function RiskDashboard() {
  const [assessments, setAssessments] = useState<Assessment[]>([])
  const [summary,     setSummary]     = useState<Summary | null>(null)
  const [catalog,     setCatalog]     = useState<Catalog | null>(null)
  const [loading,     setLoading]     = useState(true)
  const [error,       setError]       = useState<string | null>(null)
  const [decisionFilter, setDecisionFilter] = useState('')
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({ limit: '30' })
      if (decisionFilter) params.set('decision', decisionFilter)

      const [histRes, sumRes, catRes] = await Promise.all([
        fetch(`${API_BASE}/api/governance/risk/history?${params}`, { headers: API_KEY_HEADER }),
        fetch(`${API_BASE}/api/governance/risk/summary`, { headers: API_KEY_HEADER }),
        fetch(`${API_BASE}/api/governance/risk/catalog`),
      ])

      if (histRes.ok) {
        const j = await histRes.json()
        setAssessments(j.assessments ?? [])
      }
      if (sumRes.ok)  setSummary(await sumRes.json())
      if (catRes.ok)  setCatalog(await catRes.json())
      setLastRefresh(new Date())
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Connection error')
    } finally {
      setLoading(false)
    }
  }, [decisionFilter])

  useEffect(() => { fetchData() }, [fetchData])
  useEffect(() => {
    const t = setInterval(fetchData, REFRESH_MS)
    return () => clearInterval(t)
  }, [fetchData])

  const total    = summary?.total_assessments ?? 0
  const approved = summary?.by_decision?.APPROVED ?? 0
  const review   = summary?.by_decision?.REVIEW ?? 0
  const blocked  = summary?.by_decision?.BLOCKED ?? 0

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
              <div className="w-8 h-8 rounded-lg bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center">
                <Layers className="w-4 h-4 text-indigo-400" />
              </div>
              <div>
                <h1 className="text-lg font-bold">Multi-Domain Risk Governance</h1>
                <p className="text-xs text-slate-400">ADR-143 — Financial · Technical · Legal · Human</p>
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
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Total Assessments', value: total,    accent: 'text-white' },
            { label: 'Approved',          value: approved, accent: 'text-emerald-400' },
            { label: 'Review',            value: review,   accent: 'text-amber-400' },
            { label: 'Blocked',           value: blocked,  accent: blocked > 0 ? 'text-red-400' : 'text-slate-400' },
          ].map(k => (
            <div key={k.label} className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4">
              <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">{k.label}</p>
              <p className={`text-3xl font-bold font-mono ${k.accent}`}>{k.value}</p>
            </div>
          ))}
        </div>

        {/* Average Vector Scores */}
        {summary?.averages && (
          <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-indigo-400" />
              Average Risk by Vector
            </h2>
            <div className="grid md:grid-cols-2 gap-4">
              {(['financial', 'technical', 'legal', 'human'] as const).map(v => (
                <div key={v}>
                  <div className="flex justify-between text-xs text-slate-400 mb-1">
                    <span className="capitalize font-medium">{v}</span>
                    <span className={`font-mono font-semibold ${SCORE_COLOR(summary.averages[v])}`}>
                      {summary.averages[v] != null ? summary.averages[v]!.toFixed(1) : '—'}
                    </span>
                  </div>
                  <ScoreBar score={summary.averages[v]} />
                </div>
              ))}
            </div>
            <div className="mt-4 pt-3 border-t border-slate-700/50">
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-300 font-semibold">Composite Average</span>
                <span className={`font-mono font-bold ${SCORE_COLOR(summary.averages.composite)}`}>
                  {summary.averages.composite != null ? summary.averages.composite.toFixed(1) : '—'}
                </span>
              </div>
              <ScoreBar score={summary.averages.composite} />
            </div>
          </div>
        )}

        {/* Thresholds Info */}
        {catalog && (
          <div className="bg-slate-800/40 border border-slate-700/30 rounded-xl p-4 flex flex-wrap gap-6 text-xs">
            <div>
              <span className="text-slate-400">Blocked at:</span>
              <span className="text-red-300 font-mono font-bold ml-2">≥ {catalog.thresholds.blocked}</span>
            </div>
            <div>
              <span className="text-slate-400">Review at:</span>
              <span className="text-amber-300 font-mono font-bold ml-2">≥ {catalog.thresholds.review}</span>
            </div>
            <div>
              <span className="text-slate-400">Hard block per vector:</span>
              <span className="text-red-300 font-mono font-bold ml-2">≥ {catalog.thresholds.hard_block_per_vector}</span>
            </div>
            <div className="text-slate-400 flex-1">{catalog.decision_logic}</div>
          </div>
        )}

        {/* Filters */}
        <div className="flex items-center gap-3">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={decisionFilter}
            onChange={e => setDecisionFilter(e.target.value)}
            className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
          >
            <option value="">All decisions</option>
            {['APPROVED', 'REVIEW', 'BLOCKED'].map(d => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
          {lastRefresh && (
            <p className="text-xs text-slate-500">Last refresh: {lastRefresh.toLocaleTimeString()}</p>
          )}
        </div>

        {error && (
          <div className="bg-red-900/30 border border-red-500/40 rounded-xl p-4 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-400 shrink-0" />
            <p className="text-sm text-red-300">{error}</p>
          </div>
        )}

        {/* Assessment Table */}
        <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700/50 text-left">
                  {['Subject', 'Decision', 'Composite', 'Financial', 'Technical', 'Legal', 'Human', 'Hard Block', 'Assessed At'].map(h => (
                    <th key={h} className="px-4 py-3 text-xs text-slate-400 font-medium uppercase tracking-wider whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {loading && assessments.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-12 text-center text-slate-400">
                      <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2" />
                      Loading risk assessments…
                    </td>
                  </tr>
                ) : assessments.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-12 text-center text-slate-400">
                      <Layers className="w-8 h-8 mx-auto mb-2 opacity-30" />
                      No assessments found
                    </td>
                  </tr>
                ) : (
                  assessments.map((a, i) => (
                    <tr
                      key={a.assessment_id}
                      className={`border-b border-slate-700/30 hover:bg-slate-700/30 transition-colors ${i % 2 === 0 ? '' : 'bg-slate-800/20'}`}
                    >
                      <td className="px-4 py-3 text-xs text-slate-200 font-medium max-w-xs truncate">
                        {a.subject}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className={`px-2 py-0.5 rounded border text-xs font-semibold font-mono ${DECISION_STYLES[a.decision] ?? 'bg-slate-700 text-slate-300 border-slate-600'}`}>
                          {a.decision}
                        </span>
                      </td>
                      <td className={`px-4 py-3 font-mono text-sm font-bold whitespace-nowrap ${SCORE_COLOR(a.composite_score)}`}>
                        {a.composite_score?.toFixed(1) ?? '—'}
                      </td>
                      {(['financial', 'technical', 'legal', 'human'] as const).map(v => (
                        <td key={v} className={`px-4 py-3 font-mono text-xs whitespace-nowrap ${SCORE_COLOR(a.vector_scores?.[v])}`}>
                          {a.vector_scores?.[v]?.toFixed(1) ?? '—'}
                        </td>
                      ))}
                      <td className="px-4 py-3 text-xs whitespace-nowrap">
                        {a.hard_block_vector
                          ? <span className="text-red-300 font-mono font-bold">{a.hard_block_vector}</span>
                          : <span className="text-slate-500">—</span>
                        }
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-400 whitespace-nowrap">
                        {new Date(a.assessed_at).toLocaleString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-500 pt-2">
          <CheckCircle className="w-3.5 h-3.5 text-emerald-500" />
          <span>Multi-Domain Risk Governance — ADR-143</span>
          <ChevronRight className="w-3 h-3" />
          <Link to="/audit" className="hover:text-slate-300 transition-colors">Back to Audit</Link>
        </div>
      </div>
    </div>
  )
}
