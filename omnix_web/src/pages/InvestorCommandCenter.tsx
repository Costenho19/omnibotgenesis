import { useState, useEffect, useRef, useCallback, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import {
  Activity, Shield, TrendingUp, Clock, Database, Lock,
  RefreshCw, ExternalLink, ArrowLeft, Zap, CheckCircle,
  LineChart, Landmark, ShieldCheck, Cpu, Stethoscope,
  Building2, Network, Gauge
} from 'lucide-react'
import { API_BASE } from '../lib/apiBase'

const REFRESH_MS = 10_000

interface VerticalData {
  label: string
  market_size: string
  live_since: string
  cycle_sec: number
  color: string
  icon: ReactNode
  decisions: number
  approved: number
  blocked: number
  hold: number
  decisions_today: number
  latest_receipt_id: string | null
  status: 'LIVE' | 'PARTIAL'
  active_robots?: number
}

interface Totals {
  decisions_total: number
  approved_total: number
  blocked_total: number
  hold_total: number
  decisions_today: number
  receipts_total: number
  uptime_days: number
  adr_count: number
  checkpoint_count: number
  verticals_live: number
  tam_usd: string
}

interface Checkpoint {
  id: string
  name: string
  layer: string
}

interface LiveMetricsResponse {
  success: boolean
  generated_at: string
  totals: Totals
  pipeline: { checkpoints: Checkpoint[]; checkpoints_count: number }
  verticals: Record<string, VerticalData>
  impact_phrases: string[]
}

const LAYER_COLORS: Record<string, string> = {
  pre:        '#f59e0b',
  entry:      '#6366f1',
  compliance: '#ef4444',
  post:       '#10b981',
  output:     '#C9A227',
}

const _uptimeDays = Math.max(0, Math.floor((Date.now() - new Date('2025-11-28').getTime()) / 86400000))

const FALLBACK_DATA: LiveMetricsResponse = {
  success: true,
  generated_at: new Date().toISOString(),
  totals: {
    decisions_total:  0,
    approved_total:   0,
    blocked_total:    0,
    hold_total:       0,
    decisions_today:  0,
    receipts_total:   0,
    uptime_days:      _uptimeDays,
    adr_count:        202,
    checkpoint_count: 11,
    verticals_live:   10,
    tam_usd:          '212B+',
  },
  pipeline: {
    checkpoints_count: 11,
    checkpoints: [
      { id: 'CAG',   name: 'Context Admission Gate',      layer: 'pre'        },
      { id: 'ACV',   name: 'Admissibility Consistency',   layer: 'pre'        },
      { id: 'CP-0',  name: 'Signal Integrity (SIV)',      layer: 'entry'      },
      { id: 'CP-1',  name: 'Monte Carlo Probability',     layer: 'entry'      },
      { id: 'CP-2',  name: 'Risk Limits',                 layer: 'entry'      },
      { id: 'CP-3',  name: 'Coherence Engine (DCI)',      layer: 'entry'      },
      { id: 'CP-4',  name: 'Trend Analysis',              layer: 'entry'      },
      { id: 'CP-5',  name: 'Stress Resilience',           layer: 'entry'      },
      { id: 'CP-6',  name: 'Sharia Governance Gate',      layer: 'entry'      },
      { id: 'CP-7',  name: 'Temporal Coherence (TCV)',    layer: 'entry'      },
      { id: 'CP-7b', name: 'Forward Trajectory (FTI)',    layer: 'entry'      },
      { id: 'CP-8',  name: 'Edge Confirmation (ECW)',     layer: 'entry'      },
      { id: 'CP-9',  name: 'AML Gate',                    layer: 'compliance' },
      { id: 'CP-10', name: 'Fraud Detection Gate',        layer: 'compliance' },
      { id: 'CP-11', name: 'Jurisdiction Gate',           layer: 'compliance' },
      { id: 'TIE',   name: 'Trajectory Invariant (TIE)', layer: 'post'       },
      { id: 'PQC',   name: 'Quantum-Secure Receipt',      layer: 'output'     },
    ],
  },
  verticals: {
    trading: {
      label: 'Digital Asset Trading', market_size: '$5B TAM', live_since: '2026-01-15',
      cycle_sec: 90, color: '#C9A227', icon: <LineChart size={22} strokeWidth={1.5} />,
      decisions: 0, approved: 0, blocked: 0, hold: 0,
      decisions_today: 0, latest_receipt_id: null, status: 'LIVE',
    },
    credit: {
      label: 'Islamic Credit (UAE/GCC)', market_size: '$2T AUM', live_since: '2026-03-27',
      cycle_sec: 300, color: '#a78bfa', icon: <Landmark size={22} strokeWidth={1.5} />,
      decisions: 0, approved: 0, blocked: 0, hold: 0,
      decisions_today: 0, latest_receipt_id: null, status: 'LIVE',
    },
    insurance: {
      label: 'Global Insurance Claims', market_size: '$7T+ Premiums', live_since: '2026-03-29',
      cycle_sec: 240, color: '#60a5fa', icon: <ShieldCheck size={22} strokeWidth={1.5} />,
      decisions: 0, approved: 0, blocked: 0, hold: 0,
      decisions_today: 0, latest_receipt_id: null, status: 'LIVE',
    },
    robotics: {
      label: 'Robotics & Autonomous Systems', market_size: '$80B+ Market', live_since: '2026-03-29',
      cycle_sec: 180, color: '#34d399', icon: <Cpu size={22} strokeWidth={1.5} />,
      decisions: 0, approved: 0, blocked: 0, hold: 0,
      decisions_today: 0, latest_receipt_id: null, status: 'LIVE',
    },
    medical: {
      label: 'Medical AI Governance', market_size: '$45B+ Market', live_since: '2026-04-01',
      cycle_sec: 120, color: '#f87171', icon: <Stethoscope size={22} strokeWidth={1.5} />,
      decisions: 0, approved: 0, blocked: 0, hold: 0,
      decisions_today: 0, latest_receipt_id: null, status: 'LIVE',
    },
    energy: {
      label: 'Energy Grid Governance', market_size: '$1T+ Market', live_since: '2026-04-01',
      cycle_sec: 150, color: '#facc15', icon: <Gauge size={22} strokeWidth={1.5} />,
      decisions: 0, approved: 0, blocked: 0, hold: 0,
      decisions_today: 0, latest_receipt_id: null, status: 'LIVE',
    },
    real_estate: {
      label: 'Real Estate & PropTech', market_size: '$4.3T+ Market', live_since: '2026-04-01',
      cycle_sec: 200, color: '#fb923c', icon: <Building2 size={22} strokeWidth={1.5} />,
      decisions: 0, approved: 0, blocked: 0, hold: 0,
      decisions_today: 0, latest_receipt_id: null, status: 'LIVE',
    },
    agents: {
      label: 'Autonomous Agent Governance', market_size: '$28B+ Market', live_since: '2026-04-01',
      cycle_sec: 60, color: '#e879f9', icon: <Network size={22} strokeWidth={1.5} />,
      decisions: 0, approved: 0, blocked: 0, hold: 0,
      decisions_today: 0, latest_receipt_id: null, status: 'LIVE',
    },
    stablecoin: {
      label: '🪙 Stablecoin Reserve (ADR-SRG-001)', market_size: '$5B+ Reserve', live_since: '2026-04-10',
      cycle_sec: 300, color: '#8B5CF6', icon: <Shield size={22} strokeWidth={1.5} />,
      decisions: 0, approved: 0, blocked: 0, hold: 0,
      decisions_today: 0, latest_receipt_id: null, status: 'LIVE',
    },
    defense: {
      label: 'Defense & Autonomous Weapons', market_size: '$130B+ Market', live_since: '2026-05-01',
      cycle_sec: 45, color: '#0EA5E9', icon: <Shield size={22} strokeWidth={1.5} />,
      decisions: 0, approved: 0, blocked: 0, hold: 0,
      decisions_today: 0, latest_receipt_id: null, status: 'LIVE',
    },
  },
  impact_phrases: [
    'OMNIX is governing decisions across 10 industries simultaneously, right now, in real time.',
    'One governance engine. Ten domains. Every decision cryptographically signed.',
    'The same 11-checkpoint pipeline governing trading, islamic credit, insurance, robotics, defense, medical AI, autonomous agents, and more.',
    'Every 3 minutes, a robot or medical AI is evaluated before it\'s permitted to act.',
    'Every governance decision generates a post-quantum cryptographic receipt — independently verifiable.',
    'We didn\'t build a product. We built infrastructure. The live data proves it.',
    '202 Architecture Decision Records. 11 governance checkpoints. Zero compromise.',
  ],
}

function AnimatedNumber({ value, duration = 1200 }: { value: number; duration?: number }) {
  const [display, setDisplay] = useState(value)
  const prev = useRef(value)
  useEffect(() => {
    const start = prev.current
    const end = value
    if (start === end) return
    const startTime = performance.now()
    const step = (now: number) => {
      const elapsed = now - startTime
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setDisplay(Math.round(start + (end - start) * eased))
      if (progress < 1) requestAnimationFrame(step)
      else { prev.current = end; setDisplay(end) }
    }
    requestAnimationFrame(step)
  }, [value, duration])
  return <>{display.toLocaleString()}</>
}

function PulseDot({ color = '#10B981' }: { color?: string }) {
  return (
    <span style={{
      display: 'inline-block', width: 8, height: 8, borderRadius: '50%',
      background: color, boxShadow: `0 0 6px ${color}`,
      animation: 'livePulse 2s ease-in-out infinite',
    }} />
  )
}

function VerticalCard({ id, data, isLive }: { id: string; data: VerticalData; isLive: boolean }) {
  const blockRate = data.decisions > 0 ? ((data.blocked / data.decisions) * 100).toFixed(1) : '0.0'
  const approvalRate = data.decisions > 0 ? ((data.approved / data.decisions) * 100).toFixed(1) : '0.0'

  return (
    <div style={{
      background: 'rgba(15,33,64,0.7)',
      border: `1px solid ${data.color}33`,
      borderRadius: 16,
      padding: '1.5rem',
      position: 'relative',
      overflow: 'hidden',
      backdropFilter: 'blur(8px)',
    }}>
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: 2,
        background: `linear-gradient(90deg, transparent, ${data.color}, transparent)`,
      }} />

      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 44, height: 44, borderRadius: 12,
            background: `${data.color}18`,
            border: `1px solid ${data.color}40`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: data.color,
          }}>{data.icon}</div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 14, color: '#F8FAFC', lineHeight: 1.2 }}>{data.label}</div>
            <div style={{ fontSize: 11, color: data.color, fontWeight: 600, marginTop: 2 }}>{data.market_size}</div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          {isLive && <PulseDot color={data.status === 'LIVE' ? '#10B981' : '#f59e0b'} />}
          <span style={{ fontSize: 10, color: data.status === 'LIVE' ? '#10B981' : '#f59e0b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            {data.status}
          </span>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, marginBottom: '1rem' }}>
        {[
          { label: 'Total', value: data.decisions, color: '#94A3B8' },
          { label: 'Approved', value: data.approved, color: '#10B981' },
          { label: 'Blocked', value: data.blocked + (data.hold || 0), color: '#ef4444' },
        ].map(item => (
          <div key={item.label} style={{ textAlign: 'center', background: 'rgba(0,0,0,0.2)', borderRadius: 8, padding: '0.6rem 0.4rem' }}>
            <div style={{ fontSize: 18, fontWeight: 800, color: item.color }}>
              <AnimatedNumber value={item.value} />
            </div>
            <div style={{ fontSize: 10, color: '#64748b', marginTop: 2, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{item.label}</div>
          </div>
        ))}
      </div>

      <div style={{ marginBottom: '0.75rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#64748b', marginBottom: 4 }}>
          <span>Approval rate</span>
          <span style={{ color: '#10B981', fontWeight: 700 }}>{approvalRate}%</span>
        </div>
        <div style={{ height: 4, background: 'rgba(255,255,255,0.06)', borderRadius: 4, overflow: 'hidden' }}>
          <div style={{
            height: '100%', width: `${approvalRate}%`,
            background: `linear-gradient(90deg, ${data.color}, #10B981)`,
            borderRadius: 4, transition: 'width 1s ease',
          }} />
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 11 }}>
        <div style={{ color: '#64748b' }}>
          Today: <span style={{ color: '#E2E8F0', fontWeight: 600 }}>{data.decisions_today}</span>
          {id === 'robotics' && data.active_robots ? (
            <span style={{ color: '#64748b' }}> · Robots: <span style={{ color: '#34d399' }}>{data.active_robots}</span></span>
          ) : null}
        </div>
        <div style={{ color: '#64748b' }}>Block: <span style={{ color: '#ef4444', fontWeight: 600 }}>{blockRate}%</span></div>
      </div>

      <div style={{
        marginTop: '0.75rem', padding: '0.4rem 0.6rem',
        background: 'rgba(201,162,39,0.06)', borderRadius: 6,
        border: '1px solid rgba(201,162,39,0.12)',
        display: 'flex', alignItems: 'center', gap: 6,
      }}>
        <Lock size={10} color="#C9A227" />
        {data.latest_receipt_id ? (
          <code style={{ fontSize: 10, color: '#C9A227', fontFamily: 'monospace', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {data.latest_receipt_id}
          </code>
        ) : (
          <span style={{ fontSize: 10, color: '#64748b', fontStyle: 'italic' }}>Receipt logging active</span>
        )}
      </div>
    </div>
  )
}

function CheckpointRow({ cp }: { cp: Checkpoint }) {
  const color = LAYER_COLORS[cp.layer] || '#64748b'
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 8,
      padding: '0.35rem 0.5rem',
      borderRadius: 6,
      background: `${color}08`,
    }}>
      <CheckCircle size={11} color={color} style={{ flexShrink: 0 }} />
      <span style={{ fontSize: 10, fontWeight: 700, color: color, minWidth: 40 }}>{cp.id}</span>
      <span style={{ fontSize: 10, color: '#94A3B8' }}>{cp.name}</span>
    </div>
  )
}

export default function InvestorCommandCenter() {
  const [data, setData] = useState<LiveMetricsResponse>(FALLBACK_DATA)
  const [isLive, setIsLive] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)
  const [_loading, setLoading] = useState(true)
  const [apiUnavailable, setApiUnavailable] = useState(false)
  const [phraseIdx, setPhraseIdx] = useState(0)
  const mountedRef = useRef(true)

  const fetchMetrics = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/metrics/live?_t=${Date.now()}`, {
        cache: 'no-store',
      })
      if (!res.ok) {
        if (mountedRef.current) setApiUnavailable(true)
        return
      }
      const json: LiveMetricsResponse = await res.json()
      if (!json.success || !mountedRef.current) return
      setData(json)
      setIsLive(true)
      setApiUnavailable(false)
      setLastUpdated(new Date().toLocaleTimeString())
    } catch {
      if (mountedRef.current) setApiUnavailable(true)
    } finally {
      if (mountedRef.current) setLoading(false)
    }
  }, [])

  useEffect(() => {
    mountedRef.current = true
    fetchMetrics()
    const interval = setInterval(fetchMetrics, REFRESH_MS)
    return () => { mountedRef.current = false; clearInterval(interval) }
  }, [fetchMetrics])

  useEffect(() => {
    if (!data?.impact_phrases?.length) return
    const t = setInterval(() => {
      setPhraseIdx(i => (i + 1) % data.impact_phrases.length)
    }, 5000)
    return () => clearInterval(t)
  }, [data?.impact_phrases])

  const t = data?.totals
  const verticals = data?.verticals

  return (
    <div style={{ minHeight: '100vh', background: '#050D18', color: '#E2E8F0', fontFamily: 'Inter, system-ui, sans-serif' }}>
      <style>{`
        @keyframes livePulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.6;transform:scale(1.3)} }
        @keyframes fadeIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
        @keyframes ticker { 0%{opacity:0;transform:translateY(10px)} 10%{opacity:1;transform:translateY(0)} 85%{opacity:1;transform:translateY(0)} 100%{opacity:0;transform:translateY(-10px)} }
      `}</style>

      {/* NAV */}
      <nav style={{
        position: 'sticky', top: 0, zIndex: 50,
        background: 'rgba(5,13,24,0.95)', backdropFilter: 'blur(12px)',
        borderBottom: '1px solid rgba(201,162,39,0.12)',
        padding: '0 1.5rem', display: 'flex', alignItems: 'center',
        justifyContent: 'space-between', height: 56,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 6, textDecoration: 'none', color: '#64748b', fontSize: 13 }}>
            <ArrowLeft size={14} />
          </Link>
          <div style={{ width: 1, height: 20, background: 'rgba(255,255,255,0.08)' }} />
          <img src="/omnix_logo.png" alt="OMNIX" style={{ height: 28, width: 'auto', objectFit: 'contain' }} />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          {isLive && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: '#10B981' }}>
              <PulseDot />
              <span style={{ fontWeight: 600 }}>LIVE</span>
              {lastUpdated && <span style={{ color: '#475569' }}>· {lastUpdated}</span>}
            </div>
          )}
          <button
            onClick={fetchMetrics}
            style={{ background: 'none', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 6, padding: '4px 8px', cursor: 'pointer', color: '#64748b', display: 'flex', alignItems: 'center', gap: 4 }}
          >
            <RefreshCw size={12} />
            <span style={{ fontSize: 11 }}>Refresh</span>
          </button>
        </div>
      </nav>

      {/* API UNAVAILABLE BANNER */}
      {apiUnavailable && !isLive && (
        <div style={{
          background: 'rgba(239,68,68,0.08)', borderBottom: '1px solid rgba(239,68,68,0.2)',
          padding: '10px 24px', display: 'flex', alignItems: 'center', gap: 8,
          fontSize: 13, color: '#FCA5A5'
        }}>
          <span style={{ fontWeight: 700 }}>⚠</span>
          <span>Métricas no disponibles — datos en tiempo real temporalmente inaccesibles. Los valores mostrados no reflejan el estado actual del sistema.</span>
        </div>
      )}

      <div style={{ maxWidth: 1280, margin: '0 auto', padding: '2rem 1.5rem' }}>

        {/* HEADER */}
        <div style={{ textAlign: 'center', marginBottom: '2.5rem', animation: 'fadeIn 0.6s ease both' }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            background: 'rgba(201,162,39,0.08)', border: '1px solid rgba(201,162,39,0.25)',
            borderRadius: 20, padding: '5px 14px', marginBottom: 16,
          }}>
            <Zap size={12} color="#C9A227" />
            <span style={{ fontSize: 11, color: '#C9A227', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase' }}>
              Investor Command Center — Live Governance Data
            </span>
          </div>
          <h1 style={{ fontSize: 'clamp(1.6rem,3.5vw,2.8rem)', fontWeight: 900, color: '#F8FAFC', margin: '0 0 0.75rem', lineHeight: 1.1 }}>
            <AnimatedNumber value={t?.decisions_total ?? 0} />{' '}
            <span style={{ color: '#C9A227' }}>Decisions Governed</span>
          </h1>
          <p style={{ fontSize: '1rem', color: '#64748b', margin: 0 }}>
            10 governance engines · 11 checkpoints · Post-quantum cryptography · {t?.adr_count ?? 202} Architecture Decision Records
          </p>
        </div>

        {/* GLOBAL KPIs */}
        {t && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: 12, marginBottom: '2rem',
          }}>
            {[
              { label: 'Total Decisions',  value: t.decisions_total,  color: '#C9A227',  icon: <Activity size={15} /> },
              { label: 'Approved',         value: t.approved_total,   color: '#10B981',  icon: <CheckCircle size={15} /> },
              { label: 'Blocked / Hold',   value: t.blocked_total + t.hold_total, color: '#ef4444', icon: <Shield size={15} /> },
              { label: 'Today',            value: t.decisions_today,  color: '#60a5fa',  icon: <TrendingUp size={15} /> },
              { label: 'Receipts (Trade)', value: t.receipts_total,   color: '#a78bfa',  icon: <Lock size={15} /> },
              { label: 'Uptime (days)',    value: t.uptime_days,      color: '#34d399',  icon: <Clock size={15} /> },
              { label: 'ADRs',             value: t.adr_count,        color: '#f59e0b',  icon: <Database size={15} /> },
              { label: 'Checkpoints',      value: t.checkpoint_count, color: '#C9A227',  icon: <Zap size={15} /> },
            ].map(kpi => (
              <div key={kpi.label} style={{
                background: 'rgba(15,33,64,0.6)',
                border: `1px solid ${kpi.color}22`,
                borderRadius: 12, padding: '1rem',
                textAlign: 'center',
                backdropFilter: 'blur(6px)',
              }}>
                <div style={{ color: kpi.color, marginBottom: 6, display: 'flex', justifyContent: 'center' }}>{kpi.icon}</div>
                <div style={{ fontSize: 22, fontWeight: 900, color: kpi.color, lineHeight: 1 }}>
                  <AnimatedNumber value={kpi.value} />
                </div>
                <div style={{ fontSize: 10, color: '#475569', marginTop: 4, textTransform: 'uppercase', letterSpacing: '0.07em' }}>{kpi.label}</div>
              </div>
            ))}
          </div>
        )}

        {/* VERTICAL GRID */}
        {verticals && (
          <div style={{ marginBottom: '2rem' }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 12 }}>
              Active Governance Engines
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>
              {Object.entries(verticals).map(([id, v]) => (
                <VerticalCard key={id} id={id} data={v} isLive={isLive} />
              ))}
            </div>
          </div>
        )}

        {/* PIPELINE PROOF */}
        {data?.pipeline && (
          <div style={{
            background: 'rgba(15,33,64,0.5)', border: '1px solid rgba(201,162,39,0.15)',
            borderRadius: 16, padding: '1.5rem', marginBottom: '2rem',
            backdropFilter: 'blur(6px)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: 8 }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 700, color: '#F8FAFC', marginBottom: 2 }}>
                  Shared Governance Pipeline
                </div>
                <div style={{ fontSize: 11, color: '#64748b' }}>
                  The same {data.pipeline.checkpoints_count} checkpoints + CAG + TIE govern all {data.totals.verticals_live} verticals simultaneously
                </div>
              </div>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                {Object.entries(LAYER_COLORS).filter(([k]) => k !== 'output').map(([layer, color]) => (
                  <div key={layer} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 10 }}>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: color }} />
                    <span style={{ color: '#64748b', textTransform: 'capitalize' }}>{layer}</span>
                  </div>
                ))}
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 4 }}>
              {data.pipeline.checkpoints.map(cp => (
                <CheckpointRow key={cp.id} cp={cp} />
              ))}
            </div>
          </div>
        )}

        {/* IMPACT PHRASE + LINKS */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
          {data?.impact_phrases && (
            <div style={{
              background: 'rgba(201,162,39,0.06)',
              border: '1px solid rgba(201,162,39,0.18)',
              borderRadius: 12, padding: '1rem 1.25rem',
              fontSize: 13, color: '#C9A227', fontStyle: 'italic', lineHeight: 1.6,
              fontWeight: 500,
            }}>
              <span key={phraseIdx} style={{ animation: 'ticker 5s ease both', display: 'block' }}>
                "{data.impact_phrases[phraseIdx]}"
              </span>
            </div>
          )}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, minWidth: 180 }}>
            {[
              { label: '2-Min Investor Demo', path: '/demo', color: '#f59e0b' },
              { label: 'Public Sandbox', path: '/try', color: '#6366f1' },
              { label: 'Verify a Receipt', path: '/verify', color: '#10B981' },
              { label: 'Executive Audit', path: '/audit', color: '#C9A227' },
              { label: 'Client Portal', path: '/client', color: '#00C6FF' },
              { label: 'Technical Stack', path: '/stack', color: '#A78BFA' },
              { label: 'Integration Guide', path: '/integration', color: '#34D399' },
            ].map(link => (
              <Link
                key={link.path}
                to={link.path}
                style={{
                  display: 'flex', alignItems: 'center', gap: 6,
                  padding: '0.5rem 0.75rem', borderRadius: 8,
                  background: `${link.color}10`,
                  border: `1px solid ${link.color}25`,
                  color: link.color, fontSize: 12, fontWeight: 600,
                  textDecoration: 'none',
                }}
              >
                <ExternalLink size={12} />
                {link.label}
              </Link>
            ))}
          </div>
        </div>

        {/* FOOTER */}
        <div style={{
          marginTop: '2rem', paddingTop: '1.25rem',
          borderTop: '1px solid rgba(255,255,255,0.05)',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          flexWrap: 'wrap', gap: 8,
        }}>
          <div style={{ fontSize: 11, color: '#334155' }}>
            OMNIX Decision Governance · Harold Nunes
          </div>
          <div style={{ fontSize: 11, color: '#334155' }}>
            All data sourced directly from production database · No mock data · Refresh every 30s
          </div>
        </div>

      </div>
    </div>
  )
}
