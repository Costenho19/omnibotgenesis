import { useState, useEffect, useCallback, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield, AlertTriangle, CheckCircle, XCircle, Activity,
  RefreshCw, ArrowLeft, TrendingUp, DollarSign, Lock,
  Globe, Percent, BarChart3, Layers
} from 'lucide-react'

const REFRESH_INTERVAL = 10_000
const RETRY_INTERVAL   = 6_000

/* ─── Types ─────────────────────────────────────────────────────────────────── */
interface Metrics {
  total_decisions:         number
  decisions_approved:      number
  decisions_blocked:       number
  decisions_held:          number
  approval_rate:           number
  block_rate:              number
  total_volume_usd:        number
  approved_volume_usd:     number
  blocked_volume_usd:      number
  avg_peg_deviation:       number
  avg_reserve_coverage:    number
  avg_liquid_ratio:        number
  avg_crypto_exposure:     number
  avg_decision_score:      number
  avg_transaction_risk:    number
  hard_blocks:             number
  decisions_last_24h:      number
  assets_active:           number
  jurisdictions_active:    number
  simulation_cycles:       number
}

interface Decision {
  decision_id:            string
  decision_type:          string
  reserve_asset:          string
  jurisdiction:           string
  transaction_amount_usd: number
  total_supply_usd:       number
  peg_deviation_pct:      number
  reserve_coverage_ratio: number
  liquid_reserve_ratio:   number
  crypto_exposure_pct:    number
  decision:               string
  decision_score:         number
  block_reason:           string | null
  hard_block_reason:      string | null
  transaction_risk_usd:   number
  receipt_id:             string | null
  probability_score:      number
  risk_exposure:          number
  signal_coherence:       number
  trajectory_score:       number
  created_at:             string
}

interface ByType {
  decision_type:    string
  total:            number
  approved:         number
  blocked:          number
  total_volume_usd: number
  avg_score:        number
  approval_rate:    number
}

interface ByAsset {
  reserve_asset:       string
  total:               number
  approved:            number
  blocked:             number
  total_volume_usd:    number
  avg_coverage:        number
  avg_liquid_ratio:    number
  avg_crypto_exposure: number
  approval_rate:       number
}

interface ByJurisdiction {
  jurisdiction:      string
  total:             number
  approved:          number
  blocked:           number
  total_volume_usd:  number
  avg_coverage:      number
  avg_peg_deviation: number
  approval_rate:     number
}

/* ─── Constants ──────────────────────────────────────────────────────────── */
const SRG_VIOLET  = '#8B5CF6'
const SRG_LIGHT   = '#A78BFA'
const SRG_GREEN   = '#10B981'
const SRG_AMBER   = '#F59E0B'
const SRG_RED     = '#EF4444'

const ASSET_COLORS: Record<string, string> = {
  US_Treasury_Bills:  '#10B981',
  US_Treasury_Notes:  '#34D399',
  Repo_Agreements:    '#06B6D4',
  Money_Market_Funds: '#60A5FA',
  USDC:               '#3B82F6',
  Commercial_Paper:   '#F59E0B',
  ETH_Staked:         '#8B5CF6',
  BTC:                '#F97316',
}

const ASSET_ICONS: Record<string, string> = {
  US_Treasury_Bills:  '🏛️',
  US_Treasury_Notes:  '📜',
  Repo_Agreements:    '🔄',
  Money_Market_Funds: '💰',
  USDC:               '🪙',
  Commercial_Paper:   '📋',
  ETH_Staked:         '⟠',
  BTC:                '₿',
}

const JURISDICTION_FLAGS: Record<string, string> = {
  EU_MiCA:  '🇪🇺',
  US_NYDFS: '🇺🇸',
  UAE_VARA: '🇦🇪',
  SG_MAS:   '🇸🇬',
  UK_FCA:   '🇬🇧',
  GCC:      '🌍',
}

const TYPE_LABELS: Record<string, string> = {
  reserve_rebalancing:  'Reserve Rebalancing',
  redemption_processing:'Redemption Processing',
  collateral_adjustment:'Collateral Adjustment',
  peg_defense:          'Peg Defense',
  yield_optimization:   'Yield Optimization',
}

/* ─── Helpers ──────────────────────────────────────────────────────────────── */
function num(v: unknown): number {
  const n = Number(v)
  return isNaN(n) ? 0 : n
}

/* Normalizes a rate that may be decimal (0-1) or percentage (0-100) to percentage */
function pct(v: unknown): number {
  const n = num(v)
  return n > 0 && n <= 1 ? n * 100 : n
}

function fmtUSD(n: number) {
  if (n >= 1_000_000_000) return `$${(n / 1_000_000_000).toFixed(2)}B`
  if (n >= 1_000_000)     return `$${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000)         return `$${(n / 1_000).toFixed(0)}K`
  return `$${n.toFixed(0)}`
}

function tsAgo(iso: string) {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000
  if (diff < 60)    return `${Math.round(diff)}s ago`
  if (diff < 3600)  return `${Math.round(diff / 60)}m ago`
  return `${Math.round(diff / 3600)}h ago`
}

/* ─── Sub-components ─────────────────────────────────────────────────────── */
function DecisionBadge({ decision, hardBlock }: { decision: string; hardBlock?: boolean }) {
  if (hardBlock) return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold border bg-red-700/20 border-red-600/40 text-red-300">
      <Lock size={10} /> HARD_BLOCK
    </span>
  )
  const cfg = {
    APPROVED: { cls: 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400', icon: <CheckCircle   size={10} /> },
    BLOCKED:  { cls: 'bg-red-500/15 border-red-500/30 text-red-400',             icon: <XCircle       size={10} /> },
    HOLD:     { cls: 'bg-amber-500/15 border-amber-500/30 text-amber-400',        icon: <AlertTriangle size={10} /> },
  }[decision] ?? { cls: 'bg-slate-500/15 border-slate-500/30 text-slate-400', icon: null }
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold border ${cfg.cls}`}>
      {cfg.icon}{decision}
    </span>
  )
}

/* Peg Stability Gauge */
function PegGauge({ deviation }: { deviation: number }) {
  const safe  = deviation < 0.5
  const warn  = deviation >= 0.5 && deviation < 2.0
  const color = safe ? SRG_GREEN : warn ? SRG_AMBER : SRG_RED
  const pct   = Math.min(100, (deviation / 8.0) * 100)
  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-28 h-14 overflow-hidden">
        <svg viewBox="0 0 112 60" className="w-full h-full">
          <path d="M8 56 A48 48 0 0 1 104 56" fill="none" stroke="#0f1e35" strokeWidth="10" strokeLinecap="round" />
          <path
            d="M8 56 A48 48 0 0 1 104 56"
            fill="none" stroke={color} strokeWidth="10" strokeLinecap="round"
            strokeDasharray={`${pct * 1.507} 999`}
            style={{ transition: 'stroke-dasharray 1s ease, stroke 0.5s ease' }}
          />
          <circle cx="56" cy="56" r="4" fill={color} style={{ transition: 'fill 0.5s ease' }} />
        </svg>
      </div>
      <div className="text-center">
        <div className="font-mono text-xl font-bold" style={{ color, fontVariantNumeric: 'tabular-nums' }}>
          ±{deviation.toFixed(3)}%
        </div>
        <div className="text-[10px] mt-0.5" style={{ color }}>
          {safe ? 'STABLE' : warn ? 'WATCH' : 'PEG BREAK'}
        </div>
      </div>
    </div>
  )
}

/* Reserve Coverage bar */
function CoverageMeter({ coverage }: { coverage: number }) {
  const color = coverage >= 105 ? SRG_GREEN : coverage >= 100 ? SRG_AMBER : SRG_RED
  const pct   = Math.min(100, Math.max(0, (coverage - 80) / 50 * 100))
  return (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between items-center">
        <span className="text-[10px] text-slate-400">Reserve Coverage</span>
        <span className="font-mono text-sm font-bold" style={{ color }}>{coverage.toFixed(1)}%</span>
      </div>
      <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pct}%`, background: color }} />
      </div>
      <div className="flex justify-between text-[9px] text-slate-600">
        <span>80%</span><span className="text-amber-500">100% MiCA</span><span>130%</span>
      </div>
    </div>
  )
}

/* Signal health strip */
function SignalStrip({ label, value }: { label: string; value: number }) {
  const color = value >= 70 ? SRG_GREEN : value >= 50 ? SRG_VIOLET : value >= 35 ? SRG_AMBER : SRG_RED
  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] text-slate-400 w-24 truncate">{label}</span>
      <div className="flex-1 h-1.5 rounded-full bg-slate-800 overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${Math.max(2, value)}%`, background: color }} />
      </div>
      <span className="text-[10px] font-mono font-semibold w-8 text-right" style={{ color }}>{value.toFixed(0)}</span>
    </div>
  )
}

/* Asset mini-bar */
function AssetBar({ asset, pct, color, count }: { asset: string; pct: number; color: string; count: number }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] w-4">{ASSET_ICONS[asset] ?? '🔷'}</span>
      <span className="text-[10px] text-slate-400 w-24 truncate">{asset.replace(/_/g, ' ')}</span>
      <div className="flex-1 h-1.5 rounded-full bg-slate-800 overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${Math.max(2, pct)}%`, background: color }} />
      </div>
      <span className="text-[10px] font-mono text-slate-400 w-6 text-right">{count}</span>
    </div>
  )
}

/* ─── Main Component ──────────────────────────────────────────────────────── */
export default function StablecoinDashboard() {
  const [metrics,        setMetrics]        = useState<Metrics | null>(null)
  const [feed,           setFeed]           = useState<Decision[]>([])
  const [byType,         setByType]         = useState<ByType[]>([])
  const [byAsset,        setByAsset]        = useState<ByAsset[]>([])
  const [byJurisdiction, setByJurisdiction] = useState<ByJurisdiction[]>([])
  const [loading,        setLoading]        = useState(true)
  const [lastRefresh,    setLastRefresh]    = useState<Date | null>(null)
  const [error,          setError]          = useState<string | null>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchAll = useCallback(async () => {
    try {
      const [mRes, fRes, tRes, aRes, jRes] = await Promise.all([
        fetch('/api/stablecoin/metrics'),
        fetch('/api/stablecoin/live-feed'),
        fetch('/api/stablecoin/by-type'),
        fetch('/api/stablecoin/by-asset'),
        fetch('/api/stablecoin/by-jurisdiction'),
      ])
      const [mData, fData, tData, aData, jData] = await Promise.all([
        mRes.json(), fRes.json(), tRes.json(), aRes.json(), jRes.json(),
      ])
      if (mData.success) { setMetrics(mData.metrics); setError(null) }
      else setError(mData.error ?? 'API error')
      if (fData.success) setFeed(fData.decisions || [])
      if (tData.success) setByType(tData.by_type || [])
      if (aData.success) setByAsset(aData.by_asset || [])
      if (jData.success) setByJurisdiction(jData.by_jurisdiction || [])
      setLastRefresh(new Date())
      setLoading(false)
    } catch {
      setError('Connection error — retrying')
      setTimeout(fetchAll, RETRY_INTERVAL)
    }
  }, [])

  useEffect(() => {
    fetchAll()
    timerRef.current = setInterval(fetchAll, REFRESH_INTERVAL)
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [fetchAll])

  const m = metrics
  const totalAssets    = byAsset.reduce((a, s) => a + s.total, 0) || 1
  const hardBlockFeed  = feed.filter(d => d.hard_block_reason)

  return (
    <div className="min-h-screen" style={{ background: '#030810', color: '#E2E8F0' }}>

      {/* ── Header ─────────────────────────────────────────────────────── */}
      <header
        className="sticky top-0 z-50 border-b"
        style={{ background: 'rgba(3,8,16,0.96)', backdropFilter: 'blur(20px)', borderColor: `${SRG_VIOLET}20` }}
      >
        <div className="max-w-screen-xl mx-auto px-6 py-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <Link to="/"><img src="/omnix_logo.png" alt="OMNIX" className="w-9 h-9 object-contain" /></Link>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold tracking-tight" style={{ color: '#F1F5F9' }}>
                  🪙 Stablecoin Reserve Governance
                </span>
                <span
                  className="px-1.5 py-0.5 text-[9px] font-bold rounded uppercase tracking-widest animate-pulse"
                  style={{ background: `${SRG_GREEN}20`, color: SRG_GREEN, border: `1px solid ${SRG_GREEN}40` }}
                >LIVE</span>
                <span
                  className="px-1.5 py-0.5 text-[9px] font-semibold rounded uppercase tracking-wider"
                  style={{ background: `${SRG_VIOLET}15`, color: SRG_VIOLET, border: `1px solid ${SRG_VIOLET}30` }}
                >ADR-SRG-001</span>
                <span
                  className="px-1.5 py-0.5 text-[9px] font-semibold rounded uppercase tracking-wider"
                  style={{ background: '#06B6D415', color: '#06B6D4', border: '1px solid #06B6D430' }}
                >MiCA</span>
              </div>
              <div className="text-[10px] text-slate-500 mt-0.5">
                {lastRefresh ? `Last refresh: ${lastRefresh.toLocaleTimeString()}` : 'Connecting…'}
                {m && ` · ${m.simulation_cycles} cycles · ${m.assets_active} assets · ${m.jurisdictions_active} jurisdictions`}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link
              to="/governance-demo-stablecoin"
              className="px-3 py-1.5 rounded text-xs font-medium transition-all"
              style={{ background: `${SRG_VIOLET}20`, color: SRG_LIGHT, border: `1px solid ${SRG_VIOLET}40` }}
            >Run Demo</Link>
            <button
              onClick={fetchAll}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium"
              style={{ background: `${SRG_VIOLET}15`, color: SRG_VIOLET, border: `1px solid ${SRG_VIOLET}30` }}
            >
              <RefreshCw size={12} /> Refresh
            </button>
            <Link
              to="/"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium text-slate-400 border border-slate-700 hover:border-slate-500 transition-all"
            >
              <ArrowLeft size={12} /> Back
            </Link>
          </div>
        </div>
      </header>

      {error && (
        <div className="bg-red-900/30 border-b border-red-700/40 px-6 py-2 text-xs text-red-300 flex items-center gap-2">
          <AlertTriangle size={12} /> {error}
        </div>
      )}

      <main className="max-w-screen-xl mx-auto px-6 py-8 space-y-8">

        {loading && (
          <div className="flex items-center justify-center h-40 text-slate-500 text-sm gap-3">
            <Activity size={18} className="animate-pulse" style={{ color: SRG_VIOLET }} />
            Loading stablecoin governance data…
          </div>
        )}

        {!loading && m && (<>

        {/* ── KPI Grid ─────────────────────────────────────────────────── */}
        <section>
          <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8 gap-3">
            {([
              {
                label: 'Volume Governed',
                value: fmtUSD(m.total_volume_usd),
                sub: `${m.total_decisions.toLocaleString()} decisions`,
                icon: <DollarSign size={16} style={{ color: SRG_VIOLET }} />,
                accent: SRG_VIOLET,
              },
              {
                label: 'Approved Volume',
                value: fmtUSD(m.approved_volume_usd),
                sub: `${(m.approval_rate * 100).toFixed(1)}% approval`,
                icon: <CheckCircle size={16} style={{ color: SRG_GREEN }} />,
                accent: SRG_GREEN,
              },
              {
                label: 'Decisions / 24h',
                value: m.decisions_last_24h.toLocaleString(),
                sub: `${m.simulation_cycles} cycles`,
                icon: <Activity size={16} style={{ color: SRG_VIOLET }} />,
                accent: SRG_VIOLET,
              },
              {
                label: 'Peg Deviation',
                value: `${m.avg_peg_deviation.toFixed(3)}%`,
                sub: m.avg_peg_deviation < 0.5 ? 'Stable' : m.avg_peg_deviation < 2 ? '⚠ Watch' : '🚨 Critical',
                icon: <Percent size={16} style={{ color: m.avg_peg_deviation < 0.5 ? SRG_GREEN : SRG_AMBER }} />,
                accent: m.avg_peg_deviation < 0.5 ? SRG_GREEN : m.avg_peg_deviation < 2 ? SRG_AMBER : SRG_RED,
              },
              {
                label: 'Reserve Coverage',
                value: `${m.avg_reserve_coverage.toFixed(1)}%`,
                sub: m.avg_reserve_coverage >= 100 ? 'MiCA compliant' : '⚠ Below 100%',
                icon: <Shield size={16} style={{ color: m.avg_reserve_coverage >= 100 ? SRG_GREEN : SRG_RED }} />,
                accent: m.avg_reserve_coverage >= 100 ? SRG_GREEN : SRG_RED,
              },
              {
                label: 'Liquid Reserves',
                value: `${m.avg_liquid_ratio.toFixed(1)}%`,
                sub: m.avg_liquid_ratio >= 60 ? 'MiCA OK' : '⚠ Below 60%',
                icon: <Layers size={16} style={{ color: m.avg_liquid_ratio >= 60 ? SRG_GREEN : SRG_AMBER }} />,
                accent: m.avg_liquid_ratio >= 60 ? SRG_GREEN : SRG_AMBER,
              },
              {
                label: 'Hard Blocks',
                value: m.hard_blocks.toLocaleString(),
                sub: 'MiCA / AML / peg stops',
                icon: <XCircle size={16} style={{ color: SRG_RED }} />,
                accent: SRG_RED,
              },
              {
                label: 'Gov Score',
                value: `${pct(m.avg_decision_score).toFixed(1)}`,
                sub: 'avg pipeline score',
                icon: <TrendingUp size={16} style={{ color: SRG_LIGHT }} />,
                accent: SRG_LIGHT,
              },
            ] as const).map((kpi) => (
              <div
                key={kpi.label}
                className="rounded-xl p-4 border"
                style={{ background: `${kpi.accent}08`, borderColor: `${kpi.accent}25` }}
              >
                <div className="flex items-center gap-2 mb-2">
                  {kpi.icon}
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider">{kpi.label}</span>
                </div>
                <div className="font-mono text-lg font-bold leading-tight" style={{ color: kpi.accent }}>
                  {kpi.value}
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">{kpi.sub}</div>
              </div>
            ))}
          </div>
        </section>

        {/* ── Row 2: Peg Gauge + Reserve Health + Signal Health ────────── */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6">

          {/* Peg Stability Gauge */}
          <div className="rounded-xl p-5 border flex flex-col gap-4"
            style={{ background: '#060D1A', borderColor: `${SRG_VIOLET}20` }}>
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                <Percent size={14} style={{ color: SRG_VIOLET }} /> Peg Stability
              </h3>
              <span className="text-[9px] px-1.5 py-0.5 rounded"
                style={{ background: '#06B6D415', color: '#06B6D4', border: '1px solid #06B6D430' }}>
                Hard Block @2%
              </span>
            </div>
            <div className="flex justify-center">
              <PegGauge deviation={m.avg_peg_deviation} />
            </div>
            <div className="grid grid-cols-3 gap-2 text-center">
              {([
                { label: 'Stable', range: '< 0.5%', color: SRG_GREEN },
                { label: 'Watch',  range: '0.5–2%', color: SRG_AMBER },
                { label: 'Block',  range: '> 2%',   color: SRG_RED },
              ] as const).map(z => (
                <div key={z.label} className="rounded p-2"
                  style={{ background: `${z.color}10`, border: `1px solid ${z.color}25` }}>
                  <div className="text-[9px]" style={{ color: z.color }}>{z.label}</div>
                  <div className="text-[10px] font-mono text-slate-400">{z.range}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Reserve Health */}
          <div className="rounded-xl p-5 border flex flex-col gap-4"
            style={{ background: '#060D1A', borderColor: `${SRG_VIOLET}20` }}>
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
              <Shield size={14} style={{ color: SRG_GREEN }} /> Reserve Health
            </h3>
            <CoverageMeter coverage={m.avg_reserve_coverage} />
            <div className="flex flex-col gap-1 mt-1">
              <div className="flex justify-between items-center">
                <span className="text-[10px] text-slate-400">Liquid Reserve Ratio</span>
                <span className="font-mono text-sm font-bold" style={{ color: m.avg_liquid_ratio >= 60 ? SRG_GREEN : SRG_RED }}>
                  {m.avg_liquid_ratio.toFixed(1)}%
                </span>
              </div>
              <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                <div className="h-full rounded-full transition-all duration-700"
                  style={{ width: `${Math.min(100, m.avg_liquid_ratio)}%`, background: m.avg_liquid_ratio >= 60 ? SRG_GREEN : SRG_RED }} />
              </div>
              <div className="flex justify-between text-[9px] text-slate-600">
                <span>0%</span><span className="text-amber-500">60% MiCA</span><span>100%</span>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2 mt-auto">
              <div className="rounded p-2 text-center" style={{ background: '#10B98110', border: '1px solid #10B98125' }}>
                <div className="text-[9px] text-slate-400">Crypto Exposure</div>
                <div className="text-sm font-mono font-bold"
                  style={{ color: m.avg_crypto_exposure < 20 ? SRG_GREEN : SRG_AMBER }}>
                  {m.avg_crypto_exposure.toFixed(1)}%
                </div>
              </div>
              <div className="rounded p-2 text-center" style={{ background: '#EF444410', border: '1px solid #EF444425' }}>
                <div className="text-[9px] text-slate-400">Blocked Volume</div>
                <div className="text-sm font-mono font-bold" style={{ color: SRG_RED }}>
                  {fmtUSD(m.blocked_volume_usd)}
                </div>
              </div>
            </div>
          </div>

          {/* Pipeline Health */}
          <div className="rounded-xl p-5 border flex flex-col gap-3"
            style={{ background: '#060D1A', borderColor: `${SRG_VIOLET}20` }}>
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
              <BarChart3 size={14} style={{ color: SRG_VIOLET }} /> Pipeline Health
            </h3>
            {feed.length > 0 ? (() => {
              const last = feed[0]
              return (
                <div className="flex flex-col gap-2">
                  <SignalStrip label="Probability"    value={(last.probability_score ?? 0) * 100} />
                  <SignalStrip label="Risk Control"   value={100 - (last.risk_exposure ?? 0) * 100} />
                  <SignalStrip label="Sig. Coherence" value={(last.signal_coherence ?? 0) * 100} />
                  <SignalStrip label="Trajectory"     value={(last.trajectory_score ?? 0) * 100} />
                </div>
              )
            })() : (
              <div className="text-xs text-slate-500 text-center py-4">Awaiting first cycle…</div>
            )}
            <div className="mt-auto pt-3 border-t border-slate-800">
              <div className="grid grid-cols-3 gap-1 text-center">
                <div>
                  <div className="text-[9px] text-slate-500">Approved</div>
                  <div className="text-sm font-mono font-bold text-emerald-400">{m.decisions_approved}</div>
                </div>
                <div>
                  <div className="text-[9px] text-slate-500">Blocked</div>
                  <div className="text-sm font-mono font-bold text-red-400">{m.decisions_blocked}</div>
                </div>
                <div>
                  <div className="text-[9px] text-slate-500">Held</div>
                  <div className="text-sm font-mono font-bold text-amber-400">{m.decisions_held}</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── Row 3: Asset + Jurisdiction Breakdowns ───────────────────── */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-6">

          {/* By Asset */}
          <div className="rounded-xl p-5 border"
            style={{ background: '#060D1A', borderColor: `${SRG_VIOLET}20` }}>
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Layers size={14} style={{ color: SRG_VIOLET }} /> Reserve Asset Breakdown
            </h3>
            {byAsset.length === 0
              ? <div className="text-xs text-slate-500 text-center py-6">Awaiting data…</div>
              : (
                <div className="space-y-3">
                  {byAsset.map(a => (
                    <div key={a.reserve_asset} className="space-y-1">
                      <AssetBar
                        asset={a.reserve_asset}
                        pct={a.total / totalAssets * 100}
                        color={ASSET_COLORS[a.reserve_asset] ?? SRG_VIOLET}
                        count={a.total}
                      />
                      <div className="flex gap-3 pl-7 text-[9px] text-slate-500">
                        <span className="text-emerald-400">{a.approved} ✓</span>
                        <span className="text-red-400">{a.blocked} ✗</span>
                        <span>{pct(a.approval_rate).toFixed(0)}% rate</span>
                        <span>{num(a.avg_coverage).toFixed(1)}% cov.</span>
                        <span className="ml-auto">{fmtUSD(num(a.total_volume_usd))}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )
            }
          </div>

          {/* By Jurisdiction */}
          <div className="rounded-xl p-5 border"
            style={{ background: '#060D1A', borderColor: `${SRG_VIOLET}20` }}>
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Globe size={14} style={{ color: SRG_VIOLET }} /> Jurisdiction Breakdown
            </h3>
            {byJurisdiction.length === 0
              ? <div className="text-xs text-slate-500 text-center py-6">Awaiting data…</div>
              : (
                <div className="space-y-2">
                  {byJurisdiction.map(j => {
                    const ar = pct(j.approval_rate)
                    const rc = ar >= 80 ? SRG_GREEN : ar >= 60 ? SRG_AMBER : SRG_RED
                    return (
                      <div key={j.jurisdiction}
                        className="flex items-center gap-3 p-2 rounded-lg"
                        style={{ background: '#0A1628' }}>
                        <span className="text-base">{JURISDICTION_FLAGS[j.jurisdiction] ?? '🌐'}</span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-semibold text-slate-200">{j.jurisdiction}</span>
                            <span className="text-[10px] font-mono" style={{ color: rc }}>
                              {ar.toFixed(1)}%
                            </span>
                          </div>
                          <div className="mt-1 h-1 rounded-full bg-slate-800 overflow-hidden">
                            <div className="h-full rounded-full" style={{ width: `${ar}%`, background: rc }} />
                          </div>
                          <div className="flex gap-3 mt-1 text-[9px] text-slate-500">
                            <span>{j.total} decisions</span>
                            <span className="text-emerald-400">{j.approved} ✓</span>
                            <span className="text-red-400">{j.blocked} ✗</span>
                            <span className="ml-auto">{fmtUSD(num(j.total_volume_usd))}</span>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )
            }
          </div>
        </section>

        {/* ── Row 4: Decision Type Performance ────────────────────────── */}
        <section>
          <div className="rounded-xl p-5 border"
            style={{ background: '#060D1A', borderColor: `${SRG_VIOLET}20` }}>
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
              <BarChart3 size={14} style={{ color: SRG_VIOLET }} /> Decision Type Performance
            </h3>
            {byType.length === 0
              ? <div className="text-xs text-slate-500 text-center py-6">Awaiting data…</div>
              : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {byType.map(t => {
                    const at = pct(t.approval_rate)
                    const ac = at >= 80 ? SRG_GREEN : at >= 60 ? SRG_AMBER : SRG_RED
                    return (
                      <div key={t.decision_type} className="rounded-lg p-3 border"
                        style={{ background: '#0A1628', borderColor: `${SRG_VIOLET}15` }}>
                        <div className="text-[10px] font-semibold text-slate-300 mb-2">
                          {TYPE_LABELS[t.decision_type] ?? t.decision_type.replace(/_/g, ' ')}
                        </div>
                        <div className="h-1 rounded-full bg-slate-800 overflow-hidden mb-2">
                          <div className="h-full rounded-full" style={{ width: `${at}%`, background: ac }} />
                        </div>
                        <div className="grid grid-cols-3 gap-1 text-center">
                          <div>
                            <div className="text-[9px] text-slate-500">Total</div>
                            <div className="text-xs font-mono font-bold text-slate-200">{t.total}</div>
                          </div>
                          <div>
                            <div className="text-[9px] text-slate-500">Rate</div>
                            <div className="text-xs font-mono font-bold" style={{ color: ac }}>
                              {at.toFixed(1)}%
                            </div>
                          </div>
                          <div>
                            <div className="text-[9px] text-slate-500">Volume</div>
                            <div className="text-xs font-mono font-bold text-slate-300">
                              {fmtUSD(num(t.total_volume_usd))}
                            </div>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )
            }
          </div>
        </section>

        {/* ── Hard Block Alerts ─────────────────────────────────────────── */}
        {hardBlockFeed.length > 0 && (
          <section>
            <div className="rounded-xl p-5 border"
              style={{ background: '#1A060A', borderColor: '#EF444430' }}>
              <h3 className="text-xs font-semibold text-red-300 uppercase tracking-wider mb-4 flex items-center gap-2">
                <Lock size={14} className="text-red-400" />
                Hard Blocks — MiCA / AML / Sanctions ({hardBlockFeed.length} recent)
              </h3>
              <div className="space-y-2">
                {hardBlockFeed.slice(0, 5).map(d => (
                  <div key={d.decision_id}
                    className="flex items-start gap-3 p-3 rounded-lg border"
                    style={{ background: '#0A0308', borderColor: '#EF444420' }}>
                    <Lock size={14} className="text-red-400 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-[10px] font-mono text-red-300">{d.decision_id}</span>
                        <span className="text-[9px] px-1.5 py-0.5 rounded text-slate-400 border border-slate-700">
                          {ASSET_ICONS[d.reserve_asset] ?? '🔷'} {d.reserve_asset?.replace(/_/g, ' ')}
                        </span>
                        <span className="text-[9px] text-slate-500">
                          {JURISDICTION_FLAGS[d.jurisdiction] ?? ''} {d.jurisdiction}
                        </span>
                      </div>
                      <div className="text-[10px] text-red-300 mt-1">{d.hard_block_reason}</div>
                      <div className="text-[9px] text-slate-500 mt-0.5">
                        {fmtUSD(d.transaction_amount_usd)} · Peg ±{(d.peg_deviation_pct ?? 0).toFixed(3)}%
                        · Coverage {(d.reserve_coverage_ratio ?? 0).toFixed(1)}% · {tsAgo(d.created_at)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* ── Live Decision Feed ─────────────────────────────────────────── */}
        <section>
          <div className="rounded-xl border overflow-hidden"
            style={{ background: '#060D1A', borderColor: `${SRG_VIOLET}20` }}>
            <div className="px-5 py-4 border-b flex items-center justify-between"
              style={{ borderColor: `${SRG_VIOLET}15` }}>
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                <Activity size={14} style={{ color: SRG_VIOLET }} /> Live Decision Feed
                <span className="text-[9px] px-1.5 py-0.5 rounded animate-pulse"
                  style={{ background: `${SRG_GREEN}20`, color: SRG_GREEN, border: `1px solid ${SRG_GREEN}30` }}>
                  {feed.length} decisions
                </span>
              </h3>
              <div className="text-[10px] text-slate-500">Auto-refresh every {REFRESH_INTERVAL / 1000}s</div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-[11px]">
                <thead>
                  <tr className="border-b" style={{ borderColor: `${SRG_VIOLET}15` }}>
                    {['Decision ID', 'Type', 'Asset', 'Juris.', 'Amount', 'Peg', 'Coverage', 'Liquid', 'Score', 'Verdict', 'Receipt', 'Time'].map(h => (
                      <th key={h} className="px-3 py-2 text-left text-[9px] uppercase tracking-wider text-slate-500 font-semibold whitespace-nowrap">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {feed.slice(0, 30).map((d, i) => (
                    <tr key={d.decision_id}
                      className="border-b transition-colors hover:bg-white/[0.02]"
                      style={{ borderColor: `${SRG_VIOLET}10`, background: i === 0 ? `${SRG_VIOLET}05` : 'transparent' }}>
                      <td className="px-3 py-2 font-mono text-slate-400 whitespace-nowrap">
                        {d.decision_id?.slice(0, 14)}…
                      </td>
                      <td className="px-3 py-2 text-slate-300 whitespace-nowrap">
                        {TYPE_LABELS[d.decision_type] ?? d.decision_type?.replace(/_/g, ' ')}
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap">
                        <span style={{ color: ASSET_COLORS[d.reserve_asset] ?? SRG_LIGHT }}>
                          {ASSET_ICONS[d.reserve_asset] ?? '🔷'} {d.reserve_asset?.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-slate-300 whitespace-nowrap">
                        {JURISDICTION_FLAGS[d.jurisdiction] ?? ''} {d.jurisdiction}
                      </td>
                      <td className="px-3 py-2 font-mono text-slate-300 whitespace-nowrap">{fmtUSD(d.transaction_amount_usd)}</td>
                      <td className="px-3 py-2 font-mono whitespace-nowrap">
                        <span style={{ color: (d.peg_deviation_pct ?? 0) < 0.5 ? SRG_GREEN : (d.peg_deviation_pct ?? 0) < 2 ? SRG_AMBER : SRG_RED }}>
                          ±{(d.peg_deviation_pct ?? 0).toFixed(3)}%
                        </span>
                      </td>
                      <td className="px-3 py-2 font-mono whitespace-nowrap">
                        <span style={{ color: (d.reserve_coverage_ratio ?? 0) >= 100 ? SRG_GREEN : SRG_RED }}>
                          {(d.reserve_coverage_ratio ?? 0).toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-3 py-2 font-mono whitespace-nowrap">
                        <span style={{ color: (d.liquid_reserve_ratio ?? 0) >= 60 ? SRG_GREEN : SRG_AMBER }}>
                          {(d.liquid_reserve_ratio ?? 0).toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-3 py-2 font-mono whitespace-nowrap">
                        <span style={{ color: (d.decision_score ?? 0) >= 0.7 ? SRG_GREEN : (d.decision_score ?? 0) >= 0.5 ? SRG_AMBER : SRG_RED }}>
                          {((d.decision_score ?? 0) * 100).toFixed(1)}
                        </span>
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap">
                        <DecisionBadge decision={d.decision} hardBlock={!!d.hard_block_reason} />
                      </td>
                      <td className="px-3 py-2 font-mono text-[9px] whitespace-nowrap">
                        {d.receipt_id
                          ? <span style={{ color: SRG_LIGHT }}>{d.receipt_id.slice(0, 18)}…</span>
                          : <span className="text-slate-600">—</span>}
                      </td>
                      <td className="px-3 py-2 text-slate-500 whitespace-nowrap">{tsAgo(d.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {feed.length === 0 && (
                <div className="text-center py-8 text-slate-500 text-xs">Waiting for first simulation cycle…</div>
              )}
            </div>
          </div>
        </section>

        {/* ── Footer ─────────────────────────────────────────────────────── */}
        <footer className="text-center text-[10px] text-slate-600 pb-4 space-y-1">
          <div>
            OMNIX Quantum · Stablecoin Reserve Governance · ADR-SRG-001 ·{' '}
            <span style={{ color: '#06B6D4' }}>MiCA Article 36/37 compliant</span>
          </div>
          <div>
            Hard blocks: peg &gt;2% · reserve &lt;100% · liquid &lt;60% · AML · sanctions · counterparty default
          </div>
        </footer>

        </>)}
      </main>
    </div>
  )
}
