import { useState, useEffect, useCallback, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield, AlertTriangle, CheckCircle, XCircle, Activity,
  Zap, Lock, RefreshCw, ArrowLeft, TrendingUp, Wind,
  Sun, Flame, Atom, Droplets, Battery, Globe
} from 'lucide-react'
import { API_BASE } from '../lib/apiBase'

const REFRESH_INTERVAL = 10_000
const RETRY_INTERVAL   = 6_000

/* ─── Types ────────────────────────────────────────────────────────────────── */
interface Metrics {
  total_decisions:       number
  decisions_approved:    number
  decisions_blocked:     number
  decisions_held:        number
  approval_rate:         number
  block_rate:            number
  total_mw_governed:     number
  approved_mw:           number
  blocked_mw:            number
  total_carbon_avoided:  number
  avg_decision_score:    number
  avg_capacity_margin:   number
  avg_frequency_deviation: number
  avg_settlement_risk:   number
  avg_lmp_confidence:    number
  avg_renewable_buffer:  number
  hard_blocks:           number
  decisions_last_24h:    number
  sources_active:        number
  regions_active:        number
  simulation_cycles:     number
}

interface Decision {
  decision_id:            string
  decision_type:          string
  energy_source:          string
  grid_region:            string
  contracted_mw:          number
  settlement_price_mwh:   number
  decision:               string
  decision_score:         number
  block_reason:           string | null
  hard_block_reason:      string | null
  carbon_avoided_tco2e:   number
  settlement_risk_usd:    number
  frequency_deviation_hz: number
  capacity_margin_pct:    number
  receipt_id:             string | null
  created_at:             string
}

interface ByType {
  decision_type:     string
  total:             number
  approved:          number
  blocked:           number
  total_mw:          number
  avg_score:         number
  approval_rate:     number
}

interface BySource {
  energy_source:        string
  total:                number
  approved:             number
  blocked:              number
  total_mw:             number
  avg_lmp_confidence:   number
  total_carbon_avoided: number
  avg_settlement_risk:  number
  approval_rate:        number
}

interface ByRegion {
  grid_region:          string
  total:                number
  approved:             number
  blocked:              number
  total_mw:             number
  avg_capacity_margin:  number
  avg_freq_deviation:   number
  total_carbon_avoided: number
  approval_rate:        number
}

/* ─── Constants ──────────────────────────────────────────────────────────── */
const E_BLUE  = '#00B4D8'
const E_GREEN = '#0AFF9D'

const SOURCE_ICONS: Record<string, React.ReactNode> = {
  Natural_Gas:    <Flame    size={12} className="inline" style={{ color: '#F97316' }} />,
  LNG:            <Flame    size={12} className="inline" style={{ color: '#EF4444' }} />,
  Coal:           <Flame    size={12} className="inline" style={{ color: '#6B7280' }} />,
  Wind_Onshore:   <Wind     size={12} className="inline" style={{ color: E_BLUE }} />,
  Wind_Offshore:  <Wind     size={12} className="inline" style={{ color: '#60A5FA' }} />,
  Solar_Utility:  <Sun      size={12} className="inline" style={{ color: '#FBBF24' }} />,
  Nuclear:        <Atom     size={12} className="inline" style={{ color: '#A78BFA' }} />,
  Hydro:          <Droplets size={12} className="inline" style={{ color: '#34D399' }} />,
  Battery_Storage:<Battery  size={12} className="inline" style={{ color: E_GREEN }} />,
}

const SOURCE_COLORS: Record<string, string> = {
  Natural_Gas:    '#F97316',
  LNG:            '#EF4444',
  Coal:           '#6B7280',
  Wind_Onshore:   E_BLUE,
  Wind_Offshore:  '#60A5FA',
  Solar_Utility:  '#FBBF24',
  Nuclear:        '#A78BFA',
  Hydro:          '#34D399',
  Battery_Storage: E_GREEN,
}

const REGION_FLAGS: Record<string, string> = {
  PJM:       '🇺🇸',
  ERCOT:     '🇺🇸',
  UK:        '🇬🇧',
  EU_ENTSO_E:'🇪🇺',
  AEMO:      '🇦🇺',
  GCC:       '🌍',
}

const TYPE_LABELS: Record<string, string> = {
  dispatch_order:    'Dispatch Order',
  curtailment_order: 'Curtailment Order',
  ppa_contract:      'PPA Contract',
  capacity_trade:    'Capacity Trade',
  carbon_credit:     'Carbon Credit',
  balancing_action:  'Balancing Action',
}

const RENEWABLE_SOURCES = new Set(['Wind_Onshore', 'Wind_Offshore', 'Solar_Utility', 'Hydro'])

/* ─── Helpers ────────────────────────────────────────────────────────────── */
function fmtMW(n: number) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)} TWh`
  if (n >= 1_000)     return `${(n / 1_000).toFixed(1)} GW`
  return `${n.toFixed(0)} MW`
}

function fmtUSD(n: number) {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000)     return `$${(n / 1_000).toFixed(0)}K`
  return `$${n.toFixed(0)}`
}

function fmtCO2(n: number) {
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)} MtCO₂e`
  return `${n.toFixed(1)} ktCO₂e`
}

function tsAgo(iso: string) {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000
  if (diff < 60)  return `${Math.round(diff)}s ago`
  if (diff < 3600) return `${Math.round(diff / 60)}m ago`
  return `${Math.round(diff / 3600)}h ago`
}

/* ─── Sub-components ─────────────────────────────────────────────────────── */
function DecisionBadge({ decision }: { decision: string }) {
  const cfg = {
    APPROVED: { cls: 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400', icon: <CheckCircle size={10} /> },
    BLOCKED:  { cls: 'bg-red-500/15 border-red-500/30 text-red-400',             icon: <XCircle     size={10} /> },
    HOLD:     { cls: 'bg-amber-500/15 border-amber-500/30 text-amber-400',        icon: <AlertTriangle size={10} /> },
  }[decision] ?? { cls: 'bg-slate-500/15 border-slate-500/30 text-slate-400', icon: null }
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold border ${cfg.cls}`}>
      {cfg.icon}{decision}
    </span>
  )
}

/* Grid Frequency Gauge — unique to Energy */
function FrequencyGauge({ hz }: { hz: number }) {
  const safe   = hz < 0.15
  const warn   = hz >= 0.15 && hz < 0.35
  const color  = safe ? E_GREEN : warn ? '#F59E0B' : '#EF4444'
  const pct    = Math.min(100, (hz / 0.5) * 100)

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-28 h-14 overflow-hidden">
        {/* Semicircle track */}
        <svg viewBox="0 0 112 60" className="w-full h-full">
          <path d="M8 56 A48 48 0 0 1 104 56" fill="none" stroke="#0f2030" strokeWidth="10" strokeLinecap="round" />
          <path
            d="M8 56 A48 48 0 0 1 104 56"
            fill="none"
            stroke={color}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={`${pct * 1.507} 999`}
            style={{ transition: 'stroke-dasharray 1s ease, stroke 0.5s ease' }}
          />
          <circle cx="56" cy="56" r="4" fill={color} style={{ transition: 'fill 0.5s ease' }} />
        </svg>
      </div>
      <div className="text-center">
        <div className="font-mono text-xl font-bold" style={{ color, fontVariantNumeric: 'tabular-nums' }}>
          ±{hz.toFixed(3)} Hz
        </div>
        <div className="text-[10px] mt-0.5" style={{ color: safe ? E_GREEN : warn ? '#F59E0B' : '#EF4444' }}>
          {safe ? 'NOMINAL' : warn ? 'CAUTION' : 'EMERGENCY'}
        </div>
      </div>
    </div>
  )
}

/* Signal health strip */
function SignalStrip({ label, value }: { label: string; value: number }) {
  const color = value >= 70 ? E_GREEN : value >= 50 ? E_BLUE : value >= 35 ? '#F59E0B' : '#EF4444'
  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] text-slate-400 w-20 truncate">{label}</span>
      <div className="flex-1 h-1.5 rounded-full bg-slate-800 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${Math.max(2, value)}%`, background: color }}
        />
      </div>
      <span className="text-[10px] font-mono font-semibold w-8 text-right" style={{ color }}>
        {value.toFixed(0)}
      </span>
    </div>
  )
}

/* ─── Main Component ──────────────────────────────────────────────────────── */
export default function EnergyDashboard() {
  const [metrics,   setMetrics]   = useState<Metrics | null>(null)
  const [feed,      setFeed]      = useState<Decision[]>([])
  const [byType,    setByType]    = useState<ByType[]>([])
  const [bySource,  setBySource]  = useState<BySource[]>([])
  const [byRegion,  setByRegion]  = useState<ByRegion[]>([])
  const [loading,   setLoading]   = useState(true)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)
  const [, setError] = useState<string | null>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchAll = useCallback(async () => {
    try {
      const [mRes, fRes, tRes, sRes, rRes] = await Promise.all([
        fetch(`${API_BASE}/api/energy/metrics`),
        fetch(`${API_BASE}/api/energy/live-feed`),
        fetch(`${API_BASE}/api/energy/by-type`),
        fetch(`${API_BASE}/api/energy/by-source`),
        fetch(`${API_BASE}/api/energy/by-region`),
      ])
      const [mData, fData, tData, sData, rData] = await Promise.all([
        mRes.json(), fRes.json(), tRes.json(), sRes.json(), rRes.json(),
      ])
      if (mData.success) { setMetrics(mData.metrics); setError(null) }
      if (fData.success) setFeed(fData.decisions || [])
      if (tData.success) setByType(tData.by_type || [])
      if (sData.success) setBySource(sData.by_source || [])
      if (rData.success) setByRegion(rData.by_region || [])
      setLastRefresh(new Date())
      setLoading(false)
    } catch (err) {
      setError('API connection error — retrying')
      setTimeout(fetchAll, RETRY_INTERVAL)
    }
  }, [])

  useEffect(() => {
    fetchAll()
    timerRef.current = setInterval(fetchAll, REFRESH_INTERVAL)
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [fetchAll])

  const m = metrics

  // Fuel mix for by-source
  const renewableMW  = bySource.filter(s => RENEWABLE_SOURCES.has(s.energy_source)).reduce((a, s) => a + (s.total_mw || 0), 0)
  const gasMW        = bySource.filter(s => ['Natural_Gas','LNG'].includes(s.energy_source)).reduce((a, s) => a + (s.total_mw || 0), 0)
  const nuclearMW    = bySource.filter(s => s.energy_source === 'Nuclear').reduce((a, s) => a + (s.total_mw || 0), 0)
  const coalMW       = bySource.filter(s => s.energy_source === 'Coal').reduce((a, s) => a + (s.total_mw || 0), 0)
  const batteryMW    = bySource.filter(s => s.energy_source === 'Battery_Storage').reduce((a, s) => a + (s.total_mw || 0), 0)
  const totalSrcMW   = renewableMW + gasMW + nuclearMW + coalMW + batteryMW || 1
  const renewPct     = Math.round(renewableMW / totalSrcMW * 100)

  return (
    <div className="min-h-screen" style={{ background: '#030810', color: '#E2E8F0' }}>

      {/* ── Header ─────────────────────────────────────────────────────── */}
      <header
        className="sticky top-0 z-50 border-b"
        style={{ background: 'rgba(3,8,16,0.96)', backdropFilter: 'blur(20px)', borderColor: `${E_BLUE}20` }}
      >
        <div className="max-w-screen-xl mx-auto px-6 py-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <Link to="/"><img src="/omnix_logo.png" alt="OMNIX" className="w-9 h-9 object-contain" /></Link>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold tracking-tight" style={{ color: '#F1F5F9' }}>
                  Energy Governance
                </span>
                <span
                  className="px-1.5 py-0.5 text-[9px] font-bold rounded uppercase tracking-widest animate-pulse"
                  style={{ background: `${E_GREEN}20`, color: E_GREEN, border: `1px solid ${E_GREEN}40` }}
                >
                  LIVE
                </span>
                <span
                  className="px-1.5 py-0.5 text-[9px] font-semibold rounded uppercase tracking-wider"
                  style={{ background: `${E_BLUE}15`, color: E_BLUE, border: `1px solid ${E_BLUE}30` }}
                >
                  ADR-112
                </span>
              </div>
              <div className="text-[10px] text-slate-500 mt-0.5">
                Last refresh: {lastRefresh ? lastRefresh.toLocaleTimeString() : '—'}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={fetchAll}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-all"
              style={{
                background: `${E_BLUE}15`, color: E_BLUE,
                border: `1px solid ${E_BLUE}30`,
              }}
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

      {/* ── Restricted Access Banner — ALWAYS visible ─────────────────── */}
      <div
        className="border-b"
        style={{ background: 'rgba(245,158,11,0.08)', borderColor: 'rgba(245,158,11,0.25)' }}
      >
        <div className="max-w-screen-xl mx-auto px-6 py-2.5 flex items-center gap-3">
          <Lock size={13} className="text-amber-400 shrink-0" />
          <span className="text-xs text-amber-300 font-medium">
            <strong>Restricted Access</strong> — Energy Governance vertical · Internal testing environment (ADR-ENG-001) · Not for public distribution
          </span>
        </div>
      </div>

      <main className="max-w-screen-xl mx-auto px-6 py-8 space-y-8">

        {/* ── KPI Grid ─────────────────────────────────────────────────── */}
        <section>
          <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8 gap-3">
            {[
              {
                label: 'MW Governed',
                value: m ? fmtMW(m.total_mw_governed) : '—',
                sub: m ? `${m.total_decisions.toLocaleString()} decisions` : '',
                icon: <Zap size={16} style={{ color: E_BLUE }} />,
                accent: E_BLUE,
              },
              {
                label: 'Approved MW',
                value: m ? fmtMW(m.approved_mw) : '—',
                sub: m ? `${(m.approval_rate * 100).toFixed(1)}% approval rate` : '',
                icon: <CheckCircle size={16} style={{ color: E_GREEN }} />,
                accent: E_GREEN,
              },
              {
                label: 'CO₂ Avoided',
                value: m ? fmtCO2(m.total_carbon_avoided) : '—',
                sub: 'vs coal baseline',
                icon: <Wind size={16} style={{ color: '#34D399' }} />,
                accent: '#34D399',
              },
              {
                label: 'Decisions / 24h',
                value: m ? m.decisions_last_24h.toLocaleString() : '—',
                sub: m ? `${m.simulation_cycles} cycles run` : '',
                icon: <Activity size={16} style={{ color: E_BLUE }} />,
                accent: E_BLUE,
              },
              {
                label: 'Grid Stability',
                value: m ? `${m.avg_lmp_confidence.toFixed(0)}%` : '—',
                sub: 'LMP forecast accuracy',
                icon: <TrendingUp size={16} style={{ color: '#818CF8' }} />,
                accent: '#818CF8',
              },
              {
                label: 'Capacity Margin',
                value: m ? `${m.avg_capacity_margin.toFixed(1)}%` : '—',
                sub: m && m.avg_capacity_margin < 10 ? '⚠ Low reserve' : 'reserve margin',
                icon: <Shield size={16} style={{ color: m && m.avg_capacity_margin < 10 ? '#EF4444' : '#F59E0B' }} />,
                accent: m && m.avg_capacity_margin < 10 ? '#EF4444' : '#F59E0B',
              },
              {
                label: 'Hard Blocks',
                value: m ? m.hard_blocks.toLocaleString() : '—',
                sub: 'emergency stops',
                icon: <XCircle size={16} style={{ color: '#EF4444' }} />,
                accent: '#EF4444',
              },
              {
                label: 'Settle. Risk',
                value: m ? fmtUSD(m.avg_settlement_risk) : '—',
                sub: 'avg per decision',
                icon: <Globe size={16} style={{ color: '#A78BFA' }} />,
                accent: '#A78BFA',
              },
            ].map((kpi) => (
              <div
                key={kpi.label}
                className="rounded-xl p-4 border transition-all hover:border-opacity-50"
                style={{
                  background: `${kpi.accent}06`,
                  border: `1px solid ${kpi.accent}18`,
                }}
              >
                <div className="flex items-start justify-between mb-2">
                  {kpi.icon}
                </div>
                <div
                  className="text-xl font-bold font-mono leading-none mb-1"
                  style={{ color: kpi.accent, fontVariantNumeric: 'tabular-nums' }}
                >
                  {kpi.value}
                </div>
                <div className="text-[10px] text-slate-500 leading-tight">{kpi.label}</div>
                {kpi.sub && <div className="text-[9px] text-slate-600 mt-0.5 truncate">{kpi.sub}</div>}
              </div>
            ))}
          </div>
        </section>

        {/* ── SCADA Control Panels Row ──────────────────────────────────── */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6">

          {/* Panel 1: Grid Frequency Monitor */}
          <div
            className="rounded-2xl p-6 border"
            style={{ background: '#070F1C', border: `1px solid ${E_BLUE}20` }}
          >
            <div className="flex items-center gap-2 mb-5">
              <div className="w-2 h-2 rounded-full animate-pulse" style={{ background: E_GREEN }} />
              <span className="text-xs font-semibold uppercase tracking-widest text-slate-400">
                Grid Frequency Monitor
              </span>
            </div>
            <div className="flex justify-center">
              <FrequencyGauge hz={m?.avg_frequency_deviation ?? 0.085} />
            </div>
            <div className="mt-5 space-y-2 text-[10px]">
              <div className="flex justify-between items-center">
                <span className="text-slate-500">Nominal (50/60 Hz)</span>
                <span className="font-mono" style={{ color: E_GREEN }}>±0.000 Hz</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500">Caution threshold</span>
                <span className="font-mono text-amber-400">±0.150 Hz</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500">Emergency block</span>
                <span className="font-mono text-red-400">±0.500 Hz</span>
              </div>
              <div className="flex justify-between items-center border-t border-slate-800 pt-2 mt-2">
                <span className="text-slate-400 font-medium">Current average</span>
                <span
                  className="font-mono font-bold"
                  style={{ color: (m?.avg_frequency_deviation ?? 0) < 0.15 ? E_GREEN : '#F59E0B' }}
                >
                  ±{(m?.avg_frequency_deviation ?? 0).toFixed(3)} Hz
                </span>
              </div>
            </div>
          </div>

          {/* Panel 2: Fuel Mix */}
          <div
            className="rounded-2xl p-6 border"
            style={{ background: '#070F1C', border: `1px solid ${E_BLUE}20` }}
          >
            <div className="flex items-center gap-2 mb-5">
              <div className="w-2 h-2 rounded-full animate-pulse" style={{ background: E_BLUE }} />
              <span className="text-xs font-semibold uppercase tracking-widest text-slate-400">
                Fuel Mix Governed
              </span>
            </div>

            {/* Stacked bar */}
            <div className="h-8 rounded-lg overflow-hidden flex mb-4">
              {[
                { label: 'Renewable', mw: renewableMW, color: E_GREEN },
                { label: 'Gas/LNG',   mw: gasMW,       color: '#F97316' },
                { label: 'Nuclear',   mw: nuclearMW,   color: '#A78BFA' },
                { label: 'Battery',   mw: batteryMW,   color: E_BLUE },
                { label: 'Coal',      mw: coalMW,      color: '#6B7280' },
              ].filter(s => s.mw > 0).map((seg) => (
                <div
                  key={seg.label}
                  style={{ width: `${(seg.mw / totalSrcMW) * 100}%`, background: seg.color }}
                  title={`${seg.label}: ${fmtMW(seg.mw)}`}
                  className="transition-all duration-1000"
                />
              ))}
            </div>

            <div className="space-y-1.5">
              {[
                { label: 'Renewable', mw: renewableMW, color: E_GREEN },
                { label: 'Gas / LNG', mw: gasMW,       color: '#F97316' },
                { label: 'Nuclear',   mw: nuclearMW,   color: '#A78BFA' },
                { label: 'Battery',   mw: batteryMW,   color: E_BLUE },
                { label: 'Coal',      mw: coalMW,      color: '#6B7280' },
              ].map((seg) => (
                <div key={seg.label} className="flex items-center justify-between text-[10px]">
                  <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-sm" style={{ background: seg.color }} />
                    <span className="text-slate-400">{seg.label}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-slate-300">{fmtMW(seg.mw)}</span>
                    <span className="text-slate-600 w-8 text-right">
                      {Math.round(seg.mw / totalSrcMW * 100)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>

            <div
              className="mt-4 rounded-lg p-2.5 text-center border"
              style={{ background: `${E_GREEN}08`, border: `1px solid ${E_GREEN}20` }}
            >
              <div className="text-2xl font-bold font-mono" style={{ color: E_GREEN }}>
                {renewPct}%
              </div>
              <div className="text-[10px] text-slate-500">Renewable penetration</div>
            </div>
          </div>

          {/* Panel 3: Governance Signals */}
          <div
            className="rounded-2xl p-6 border"
            style={{ background: '#070F1C', border: `1px solid ${E_BLUE}20` }}
          >
            <div className="flex items-center gap-2 mb-5">
              <div className="w-2 h-2 rounded-full animate-pulse" style={{ background: '#818CF8' }} />
              <span className="text-xs font-semibold uppercase tracking-widest text-slate-400">
                Signal Health · 11-Checkpoint
              </span>
            </div>

            <div className="space-y-3 mb-5">
              <SignalStrip label="Grid Stability"    value={m?.avg_lmp_confidence ?? 0} />
              <SignalStrip label="Price Alignment"   value={m ? 100 - (m.avg_settlement_risk / 200) : 0} />
              <SignalStrip label="Demand Trend"      value={m?.avg_renewable_buffer ?? 0} />
              <SignalStrip label="Grid Resilience"   value={m ? Math.min(100, m.avg_capacity_margin * 2.8) : 0} />
              <SignalStrip label="Reg. Compliance"   value={m ? (1 - m.block_rate) * 100 : 0} />
            </div>

            <div
              className="rounded-lg p-3 border space-y-2 text-[10px]"
              style={{ background: '#0A1525', border: `1px solid ${E_BLUE}15` }}
            >
              <div className="flex justify-between">
                <span className="text-slate-500">Avg governance score</span>
                <span className="font-mono font-bold" style={{ color: E_BLUE }}>
                  {m ? m.avg_decision_score.toFixed(1) : '—'}/100
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Sources active</span>
                <span className="font-mono text-slate-300">{m?.sources_active ?? '—'}/9</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Regions active</span>
                <span className="font-mono text-slate-300">{m?.regions_active ?? '—'}/6</span>
              </div>
            </div>
          </div>
        </section>

        {/* ── Decision Type + Region Grid ───────────────────────────────── */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* By Decision Type */}
          <div
            className="rounded-2xl border overflow-hidden"
            style={{ background: '#070F1C', border: `1px solid ${E_BLUE}18` }}
          >
            <div
              className="px-6 py-4 border-b flex items-center justify-between"
              style={{ borderColor: `${E_BLUE}15` }}
            >
              <span className="text-xs font-semibold uppercase tracking-widest text-slate-400">
                Decision Types
              </span>
              <span className="text-[10px] text-slate-600">{byType.reduce((a, t) => a + t.total, 0).toLocaleString()} total</span>
            </div>
            <div className="divide-y">
              {byType.length === 0
                ? <div className="px-6 py-8 text-center text-xs text-slate-600">Collecting data…</div>
                : byType.map((t) => {
                  const approvalPct = Math.round((t.approval_rate || 0) * 100)
                  const color = approvalPct >= 75 ? E_GREEN : approvalPct >= 55 ? E_BLUE : '#F59E0B'
                  return (
                    <div
                      key={t.decision_type}
                      className="px-6 py-3 flex items-center gap-4"
                      style={{ borderColor: `${E_BLUE}10` }}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="text-xs font-medium text-slate-200 truncate">
                          {TYPE_LABELS[t.decision_type] ?? t.decision_type}
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                          <div className="flex-1 h-1 rounded-full bg-slate-800 overflow-hidden">
                            <div
                              className="h-full rounded-full"
                              style={{ width: `${approvalPct}%`, background: color, transition: 'width 1s ease' }}
                            />
                          </div>
                        </div>
                      </div>
                      <div className="text-right shrink-0">
                        <div className="text-sm font-mono font-bold" style={{ color }}>
                          {approvalPct}%
                        </div>
                        <div className="text-[10px] text-slate-600">{t.total.toLocaleString()} decisions</div>
                      </div>
                      <div className="text-right shrink-0 hidden md:block">
                        <div className="text-xs font-mono text-slate-400">{fmtMW(t.total_mw || 0)}</div>
                        <div className="text-[10px] text-slate-600">MW</div>
                      </div>
                    </div>
                  )
                })}
            </div>
          </div>

          {/* By Grid Region */}
          <div
            className="rounded-2xl border overflow-hidden"
            style={{ background: '#070F1C', border: `1px solid ${E_BLUE}18` }}
          >
            <div
              className="px-6 py-4 border-b flex items-center justify-between"
              style={{ borderColor: `${E_BLUE}15` }}
            >
              <span className="text-xs font-semibold uppercase tracking-widest text-slate-400">
                Grid Regions
              </span>
              <span className="text-[10px] text-slate-600">{byRegion.length} markets active</span>
            </div>
            <div className="divide-y">
              {byRegion.length === 0
                ? <div className="px-6 py-8 text-center text-xs text-slate-600">Collecting data…</div>
                : byRegion.map((r) => {
                  const capOk  = (r.avg_capacity_margin ?? 20) >= 10
                  const freqOk = (r.avg_freq_deviation ?? 0.1) < 0.2
                  return (
                    <div
                      key={r.grid_region}
                      className="px-6 py-3 flex items-center gap-4"
                      style={{ borderColor: `${E_BLUE}10` }}
                    >
                      <div className="text-base">{REGION_FLAGS[r.grid_region] ?? '🌐'}</div>
                      <div className="flex-1 min-w-0">
                        <div className="text-xs font-semibold text-slate-200">
                          {r.grid_region.replace('_', '-')}
                        </div>
                        <div className="flex items-center gap-2 mt-0.5 text-[9px]">
                          <span style={{ color: capOk ? E_GREEN : '#EF4444' }}>
                            {(r.avg_capacity_margin ?? 0).toFixed(1)}% capacity
                          </span>
                          <span className="text-slate-700">·</span>
                          <span style={{ color: freqOk ? E_GREEN : '#F59E0B' }}>
                            ±{(r.avg_freq_deviation ?? 0).toFixed(3)} Hz
                          </span>
                        </div>
                      </div>
                      <div className="text-right shrink-0">
                        <div
                          className="text-sm font-mono font-bold"
                          style={{ color: Math.round((r.approval_rate || 0) * 100) >= 65 ? E_GREEN : '#F59E0B' }}
                        >
                          {Math.round((r.approval_rate || 0) * 100)}%
                        </div>
                        <div className="text-[10px] text-slate-600">{r.total.toLocaleString()} dec</div>
                      </div>
                      <div className="text-right shrink-0 hidden md:block">
                        <div className="text-xs font-mono text-slate-400">{fmtMW(r.total_mw || 0)}</div>
                        <div className="text-[10px] text-slate-600">governed</div>
                      </div>
                    </div>
                  )
                })}
            </div>
          </div>
        </section>

        {/* ── Energy Source Breakdown ───────────────────────────────────── */}
        <section
          className="rounded-2xl border overflow-hidden"
          style={{ background: '#070F1C', border: `1px solid ${E_BLUE}18` }}
        >
          <div
            className="px-6 py-4 border-b flex items-center justify-between"
            style={{ borderColor: `${E_BLUE}15` }}
          >
            <span className="text-xs font-semibold uppercase tracking-widest text-slate-400">
              Energy Source · Governance Breakdown
            </span>
            <span className="text-[10px] text-slate-600">by MW governed</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b" style={{ borderColor: `${E_BLUE}10` }}>
                  {['Source','Decisions','MW Governed','Approval','CO₂ Avoided','LMP Confidence','Settle. Risk'].map(h => (
                    <th key={h} className="px-5 py-3 text-left text-[10px] font-semibold text-slate-600 uppercase tracking-wider">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {bySource.length === 0
                  ? <tr><td colSpan={7} className="px-5 py-10 text-center text-slate-600">Collecting data…</td></tr>
                  : bySource.map((s) => {
                    const approvalPct = Math.round((s.approval_rate || 0) * 100)
                    const color = SOURCE_COLORS[s.energy_source] ?? E_BLUE
                    return (
                      <tr
                        key={s.energy_source}
                        className="border-b transition-colors hover:bg-slate-900/30"
                        style={{ borderColor: `${E_BLUE}08` }}
                      >
                        <td className="px-5 py-3">
                          <div className="flex items-center gap-2">
                            <span>{SOURCE_ICONS[s.energy_source]}</span>
                            <span className="font-medium text-slate-200" style={{ color }}>
                              {s.energy_source.replace('_', ' ')}
                            </span>
                          </div>
                        </td>
                        <td className="px-5 py-3 font-mono text-slate-300">{s.total.toLocaleString()}</td>
                        <td className="px-5 py-3 font-mono font-bold" style={{ color }}>
                          {fmtMW(s.total_mw || 0)}
                        </td>
                        <td className="px-5 py-3">
                          <div className="flex items-center gap-2">
                            <div className="w-12 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                              <div
                                className="h-full rounded-full"
                                style={{ width: `${approvalPct}%`, background: color }}
                              />
                            </div>
                            <span className="font-mono font-semibold" style={{ color }}>
                              {approvalPct}%
                            </span>
                          </div>
                        </td>
                        <td className="px-5 py-3 font-mono text-slate-400">
                          {fmtCO2(s.total_carbon_avoided || 0)}
                        </td>
                        <td className="px-5 py-3 font-mono text-slate-400">
                          {(s.avg_lmp_confidence || 0).toFixed(1)}%
                        </td>
                        <td className="px-5 py-3 font-mono text-slate-400">
                          {fmtUSD(s.avg_settlement_risk || 0)}
                        </td>
                      </tr>
                    )
                  })}
              </tbody>
            </table>
          </div>
        </section>

        {/* ── Live SCADA Decision Feed ──────────────────────────────────── */}
        <section
          className="rounded-2xl border overflow-hidden"
          style={{ background: '#070F1C', border: `1px solid ${E_BLUE}18` }}
        >
          <div
            className="px-6 py-4 border-b flex items-center gap-3"
            style={{ borderColor: `${E_BLUE}15` }}
          >
            <div className="w-2 h-2 rounded-full animate-pulse" style={{ background: E_GREEN }} />
            <span className="text-xs font-semibold uppercase tracking-widest text-slate-400">
              Live SCADA Feed · Energy Governance Decisions
            </span>
            {loading && <span className="text-[10px] text-slate-600 ml-auto">Loading…</span>}
          </div>

          <div className="divide-y" style={{ borderColor: `${E_BLUE}08` }}>
            {feed.length === 0
              ? (
                <div className="px-6 py-12 text-center">
                  <Activity size={28} className="mx-auto mb-3 text-slate-700" />
                  <p className="text-sm text-slate-600">Awaiting first governance cycle (180s interval)</p>
                </div>
              )
              : feed.map((d) => {
                const isBlock   = d.decision === 'BLOCKED'
                const isHold    = d.decision === 'HOLD'
                const isApprove = d.decision === 'APPROVED'
                const rowAccent = isBlock ? '#EF444420' : isHold ? '#F59E0B10' : `${E_GREEN}08`
                const srcColor  = SOURCE_COLORS[d.energy_source] ?? E_BLUE

                return (
                  <div
                    key={d.decision_id}
                    className="px-6 py-4 flex flex-col md:flex-row md:items-center gap-3 md:gap-6 transition-all"
                    style={{ background: rowAccent }}
                  >
                    {/* Decision badge */}
                    <div className="shrink-0">
                      <DecisionBadge decision={d.decision} />
                    </div>

                    {/* Source + region */}
                    <div className="flex items-center gap-2 shrink-0">
                      <span>{SOURCE_ICONS[d.energy_source]}</span>
                      <span className="text-xs font-semibold" style={{ color: srcColor }}>
                        {d.energy_source.replace('_', ' ')}
                      </span>
                      <span className="text-slate-700">·</span>
                      <span className="text-[11px] text-slate-400">
                        {REGION_FLAGS[d.grid_region] ?? '🌐'} {d.grid_region.replace('_', '-')}
                      </span>
                    </div>

                    {/* Type */}
                    <div className="shrink-0">
                      <span
                        className="text-[10px] px-2 py-0.5 rounded font-medium"
                        style={{ background: `${E_BLUE}12`, color: E_BLUE, border: `1px solid ${E_BLUE}25` }}
                      >
                        {TYPE_LABELS[d.decision_type] ?? d.decision_type}
                      </span>
                    </div>

                    {/* MW + Price */}
                    <div className="flex items-center gap-4 text-xs">
                      <div>
                        <span className="font-mono font-bold" style={{ color: isApprove ? E_GREEN : '#94A3B8' }}>
                          {fmtMW(d.contracted_mw)}
                        </span>
                        <span className="text-slate-600 ml-1">@</span>
                        <span className="font-mono text-slate-400 ml-1">${d.settlement_price_mwh.toFixed(0)}/MWh</span>
                      </div>
                    </div>

                    {/* Score + hard block */}
                    <div className="flex-1 min-w-0">
                      {d.hard_block_reason
                        ? (
                          <div className="flex items-start gap-1.5">
                            <AlertTriangle size={11} className="text-red-400 shrink-0 mt-0.5" />
                            <span className="text-[10px] text-red-300 truncate">{d.hard_block_reason}</span>
                          </div>
                        )
                        : d.block_reason
                          ? <span className="text-[10px] text-amber-400 truncate">{d.block_reason}</span>
                          : (
                            <div className="flex items-center gap-2 text-[10px] text-slate-600">
                              <span className="font-mono" style={{ color: E_GREEN }}>
                                {d.carbon_avoided_tco2e.toFixed(1)} ktCO₂e avoided
                              </span>
                              <span>·</span>
                              <span>Score: <span className="font-mono text-slate-400">{d.decision_score.toFixed(1)}</span></span>
                            </div>
                          )
                      }
                    </div>

                    {/* Grid telemetry */}
                    <div className="hidden xl:flex items-center gap-3 shrink-0 text-[9px]">
                      <div className="text-center">
                        <div
                          className="font-mono font-bold"
                          style={{ color: d.frequency_deviation_hz < 0.15 ? E_GREEN : '#F59E0B' }}
                        >
                          ±{d.frequency_deviation_hz.toFixed(3)} Hz
                        </div>
                        <div className="text-slate-600">freq.</div>
                      </div>
                      <div className="text-center">
                        <div
                          className="font-mono font-bold"
                          style={{ color: d.capacity_margin_pct >= 10 ? E_GREEN : '#EF4444' }}
                        >
                          {d.capacity_margin_pct.toFixed(1)}%
                        </div>
                        <div className="text-slate-600">cap.</div>
                      </div>
                    </div>

                    {/* Timestamp */}
                    <div className="shrink-0 text-right">
                      <div className="text-[10px] text-slate-600">{tsAgo(d.created_at)}</div>
                      {d.receipt_id && (
                        <div className="text-[9px] font-mono text-slate-700 truncate max-w-[90px]">
                          {d.receipt_id.slice(0, 14)}…
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
          </div>
        </section>

        {/* ── Footer ───────────────────────────────────────────────────── */}
        <footer className="text-center space-y-1 pb-6">
          <p className="text-[10px] text-slate-700">
            OMNIX Energy Governance · ADR-ENG-001 · Receipt prefix OMNIX-EGV · Internal environment — not for public distribution
          </p>
          <p className="text-[10px] text-slate-800">
            Decisions governed by 11-checkpoint fail-closed pipeline · PQC-signed with CRYSTALS-Dilithium3
          </p>
        </footer>

      </main>
    </div>
  )
}
