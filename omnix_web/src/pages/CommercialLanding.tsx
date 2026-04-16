import React, { useState, useEffect, useRef } from 'react'
import { Shield, ArrowRight, CheckCircle, Lock, Zap, Phone, Mail, Send, Loader2, Activity } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useLiveMetrics } from '../hooks/useLiveMetrics'

function useTotalDecisions() {
  const [total, setTotal] = useState<number>(0)
  const [loaded, setLoaded] = useState(false)
  const ref = useRef(true)
  useEffect(() => {
    const fetch_ = async () => {
      try {
        const res = await fetch(`/api/live-metrics?_t=${Date.now()}`, { cache: 'no-store' })
        if (!res.ok) return
        const d = await res.json()
        if (ref.current && d.success && d.metrics?.evaluation_cycles > 0) {
          setTotal(d.metrics.evaluation_cycles)
          setLoaded(true)
        }
      } catch {}
    }
    fetch_()
    const t = setInterval(fetch_, 10_000)
    return () => { ref.current = false; clearInterval(t) }
  }, [])
  return { total, loaded }
}

const liveStatStyle = (animKey: number): React.CSSProperties => ({
  animation: animKey > 0 ? 'omnixStatReveal 0.6s ease both' : 'none',
})

const REFERRAL_OPTIONS = [
  'Facebook', 'WhatsApp', 'Instagram', 'Telegram',
  'LinkedIn', 'Google', 'Recomendación', 'Otro'
]

export default function CommercialLanding() {
  const { metrics, isLive, formatNumber, formatNumberFull, animKey } = useLiveMetrics()
  const { total: liveTotal, loaded } = useTotalDecisions()
  const [formData, setFormData] = useState({
    name: '', company: '', email: '', referral_source: '', message: ''
  })
  const [formStatus, setFormStatus] = useState<'idle' | 'sending' | 'success' | 'error'>('idle')
  const [formError, setFormError] = useState('')

  const handleFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }))
  }

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormStatus('sending')
    setFormError('')

    try {
      const res = await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })
      const data = await res.json()

      if (data.success) {
        setFormStatus('success')
        setFormData({ name: '', company: '', email: '', referral_source: '', message: '' })
      } else {
        setFormStatus('error')
        if (data.fallback_email) {
          setFormError(`Could not save your information. Please email us at ${data.fallback_email}`)
        } else {
          setFormError(data.error || 'Something went wrong. Please try again.')
        }
      }
    } catch {
      setFormStatus('error')
      setFormError('Connection error. Please email us at contacto@omnixquantum.net')
    }
  }
  
  return (
    <div className="min-h-screen bg-institutional">
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#050D18]/90 backdrop-blur-xl border-b border-[#C9A227]/10">
        <div className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <img src="/logo.png" alt="OMNIX QUANTUM" className="w-16 h-16 object-contain" />
            <div>
              <span className="text-lg font-bold text-white tracking-tight">OMNIX QUANTUM</span>
            </div>
          </div>
          <div className="flex items-center gap-8">
            <Link to="/try" className="nav-link font-semibold text-[#C9A227]">Try OMNIX</Link>
            <Link to="/credit" className="nav-link font-semibold" style={{color:'#a78bfa', fontSize:'0.82rem'}}>Islamic Credit</Link>
            <Link to="/insurance" className="nav-link font-semibold" style={{color:'#60a5fa', fontSize:'0.82rem'}}>Insurance</Link>
            <Link to="/robotics" className="nav-link font-semibold" style={{color:'#34d399', fontSize:'0.82rem'}}>Robotics</Link>
            <Link to="/medical" className="nav-link font-semibold" style={{color:'#f472b6', fontSize:'0.82rem'}}>Medical AI</Link>
            <Link to="/agents" className="nav-link font-semibold" style={{color:'#fb923c', fontSize:'0.82rem'}}>Agents</Link>
            <Link to="/command" className="nav-link font-semibold" style={{color:'#10B981', background:'rgba(16,185,129,0.08)', padding:'6px 14px', borderRadius:8, border:'1px solid rgba(16,185,129,0.25)', fontSize:'0.82rem'}}>⚡ Live Data</Link>
            <Link to="/institutional" className="nav-link">Technical Details</Link>
            <a href="https://wa.me/16505078293?text=Hi%2C%20I%27m%20interested%20in%20OMNIX" target="_blank" rel="noopener noreferrer" className="btn-primary">Talk to Us</a>
          </div>
        </div>
      </nav>

      <main className="pt-32 px-6 pb-20 max-w-6xl mx-auto">
        <section className="text-center mb-24 animate-fade-in-up">
          <h1 className="heading-xl text-white mb-8 leading-tight">
            Stop Costly Mistakes <br />
            <span className="gold-gradient">Before They Happen</span>
          </h1>
          <p className="text-2xl text-muted max-w-3xl mx-auto mb-6 leading-relaxed">
            OMNIX is a governance control architecture for automated decision systems. It blocks high-risk decisions before they cause damage — with cryptographic proof. Live across 8 domains: digital asset trading, Islamic credit, insurance, robotics, Medical AI, autonomous agents, and more.
          </p>
          <p className="text-base italic text-[#C9A227]/80 max-w-2xl mx-auto mb-8 pl-4 border-l-2 border-[#C9A227]/40">
            "OMNIX doesn't just follow rules. It understands when and why they should apply."
          </p>

          {/* LIVE COUNTER GLOBAL */}
          <div className="flex justify-center mb-6">
            <Link to="/command" style={{
              display:'inline-flex', alignItems:'center', gap:12,
              background:'rgba(201,162,39,0.06)',
              border:'1px solid rgba(201,162,39,0.3)',
              borderRadius:14, padding:'14px 28px',
              textDecoration:'none',
              transition:'all 0.2s',
            }}>
              <span style={{display:'inline-block',width:9,height:9,borderRadius:'50%',background:'#10B981',boxShadow:'0 0 8px #10B981',animation:'livePulse 2s ease-in-out infinite'}} />
              <span style={{fontSize:'1.45rem',fontWeight:900,color:'#C9A227',letterSpacing:'-0.01em'}}>
                {loaded && liveTotal > 0 ? `${liveTotal.toLocaleString()}+` : '—'}
              </span>
              <span style={{fontSize:'0.95rem',color:'#94A3B8',fontWeight:500}}>
                decisions governed · 8 domains · right now
              </span>
              <Activity style={{width:18,height:18,color:'#10B981'}} />
            </Link>
          </div>

          {/* CRITICAL PHRASE */}
          <p style={{
            fontSize:'1.05rem', fontWeight:600,
            color:'#E2E8F0', marginBottom:'2rem',
            letterSpacing:'0.01em',
          }}>
            This is not a simulation.{' '}
            <span style={{color:'#10B981'}}>This is a live governance system.</span>
          </p>

          <div className="flex justify-center gap-4 flex-wrap">
            <Link to="/command" className="text-lg px-8 py-4 flex items-center gap-2 font-bold rounded-lg" style={{background:'linear-gradient(135deg,#10B981,#059669)', color:'#fff'}}>
              <Activity className="w-5 h-5" />
              View Live System
            </Link>
            <Link to="/try" className="btn-secondary text-lg px-8 py-4 flex items-center gap-2">
              Try OMNIX Live
            </Link>
            <a href="https://wa.me/16505078293?text=Hi%2C%20I%27m%20interested%20in%20OMNIX" target="_blank" rel="noopener noreferrer" className="btn-secondary text-lg px-8 py-4 flex items-center gap-2">
              <Phone className="w-5 h-5" />
              Talk to Us
            </a>
          </div>
        </section>

        <section className="mb-24">
          <div className="grid md:grid-cols-3 gap-8">
            <div className="glass-card p-8 text-center">
              <div className="w-16 h-16 rounded-full bg-[#C9A227]/20 flex items-center justify-center mx-auto mb-6">
                <Shield className="w-8 h-8 gold-text" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-4">Decision Governance</h3>
              <p className="text-muted leading-relaxed">
                Every high-stakes decision is validated through 11 independent checkpoints before execution.
              </p>
            </div>

            <div className="glass-card p-8 text-center">
              <div className="w-16 h-16 rounded-full bg-[#C9A227]/20 flex items-center justify-center mx-auto mb-6">
                <Zap className="w-8 h-8 gold-text" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-4">Works with Your Tools</h3>
              <p className="text-muted leading-relaxed">
                Connects to your existing decision infrastructure. No need to change how you operate.
              </p>
            </div>

            <div className="glass-card p-8 text-center">
              <div className="w-16 h-16 rounded-full bg-[#C9A227]/20 flex items-center justify-center mx-auto mb-6">
                <Lock className="w-8 h-8 gold-text" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-4">Bank-Grade Security</h3>
              <p className="text-muted leading-relaxed">
                Your data is protected with the same cryptography used by financial institutions.
              </p>
            </div>
          </div>
        </section>

        <section className="mb-24">
          <div className="glass-card p-12 gold-glow">
            <h2 className="text-3xl font-bold text-white text-center mb-8">How It Works</h2>
            <div className="grid md:grid-cols-4 gap-8">
              <div className="text-center">
                <div className="w-12 h-12 rounded-full bg-[#C9A227] text-[#0A1628] font-bold text-xl flex items-center justify-center mx-auto mb-4">1</div>
                <p className="text-white font-medium">You face a high-stakes decision</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 rounded-full bg-[#C9A227] text-[#0A1628] font-bold text-xl flex items-center justify-center mx-auto mb-4">2</div>
                <p className="text-white font-medium">OMNIX validates it through 11 checkpoints</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 rounded-full bg-[#C9A227] text-[#0A1628] font-bold text-xl flex items-center justify-center mx-auto mb-4">3</div>
                <p className="text-white font-medium">Risky actions get blocked</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 rounded-full bg-[#C9A227] text-[#0A1628] font-bold text-xl flex items-center justify-center mx-auto mb-4">4</div>
                <p className="text-white font-medium">Only validated decisions proceed</p>
              </div>
            </div>
          </div>
        </section>

        <style>{`
          @keyframes omnixStatReveal {
            from { opacity: 0; transform: translateY(10px); }
            to   { opacity: 1; transform: translateY(0); }
          }
          @keyframes omnixPulse {
            0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(34,197,94,0.4); }
            50%       { opacity: 0.8; box-shadow: 0 0 0 5px rgba(34,197,94,0); }
          }
          .omnix-live-dot {
            width: 8px; height: 8px; border-radius: 50%;
            background: #22c55e;
            display: inline-block;
            margin-right: 6px;
            animation: omnixPulse 2s infinite;
          }
        `}</style>

        <section className="mb-24">
          <div className="glass-card p-12">
            <div className="flex items-center justify-center gap-3 mb-2">
              <h2 className="text-3xl font-bold text-white">Live Production Data</h2>
              {isLive && (
                <span className="flex items-center gap-1.5 text-xs font-semibold text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 px-2.5 py-1 rounded-full">
                  <span className="omnix-live-dot" />
                  LIVE
                </span>
              )}
            </div>
            <p className="text-sm text-center text-muted mb-8">Internal dataset, not externally audited</p>

            <div key={animKey} className="grid grid-cols-2 md:grid-cols-3 gap-8 text-center mb-6">
              <div style={liveStatStyle(animKey)}>
                <div className="text-3xl font-bold gold-text">{isLive && metrics.evaluation_cycles > 0 ? formatNumberFull(metrics.evaluation_cycles) : '—'}</div>
                <div className="text-sm text-muted mt-1">Evaluation Cycles</div>
              </div>
              <div style={{ ...liveStatStyle(animKey), animationDelay: '0.08s' }}>
                <div className="text-3xl font-bold text-emerald-400">{isLive && metrics.pqc_signed_receipts > 0 ? formatNumber(metrics.pqc_signed_receipts) : '—'}</div>
                <div className="text-sm text-muted mt-1">PQC-Signed Receipts</div>
              </div>
              <div style={{ ...liveStatStyle(animKey), animationDelay: '0.16s' }}>
                <div className="text-3xl font-bold text-white">{isLive && metrics.capital_preserved_pct > 0 ? `${metrics.capital_preserved_pct}%` : '—'}</div>
                <div className="text-sm text-muted mt-1">Capital Preserved</div>
              </div>
              <div style={{ ...liveStatStyle(animKey), animationDelay: '0.24s' }}>
                <div className="text-3xl font-bold gold-text">{metrics.verticals_demo}</div>
                <div className="text-sm text-muted mt-1">Vertical Demos</div>
              </div>
              <div style={{ ...liveStatStyle(animKey), animationDelay: '0.32s' }} className="md:col-span-2">
                <div className="flex items-center justify-center gap-2">
                  <div className="text-3xl font-bold text-violet-400">{isLive && metrics.ebip_score > 0 ? metrics.ebip_score : '—'}</div>
                  {isLive && metrics.ebip_score > 0 && <div className="text-lg font-bold text-muted/60">/ 100</div>}
                </div>
                <div className="text-sm text-muted mt-1">Execution Integrity Score</div>
                <div className="text-xs text-muted/40 mt-0.5">EBIP · ADR-045</div>
              </div>
            </div>

            <div className="flex items-center justify-center gap-2 text-xs text-muted/60">
              {isLive ? (
                <>
                  <span className="omnix-live-dot" style={{ width: '6px', height: '6px' }} />
                  <span>Live from PostgreSQL</span>
                </>
              ) : (
                <span>⏳ Connecting...</span>
              )}
              <span className="text-muted/30">·</span>
              <span>Running 24/7 since November 2025{metrics.system_uptime_days > 0 ? ` (${metrics.system_uptime_days} days)` : ''}</span>
            </div>
          </div>
        </section>

        <section className="mb-24">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-white mb-3">Eight Verticals. Running Now.</h2>
            <p className="text-muted max-w-2xl mx-auto">Same 11-checkpoint governance pipeline. Eight live domains. All operating 24/7.</p>
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="glass-card p-8 border border-emerald-400/20">
              <div className="flex items-center gap-3 mb-4">
                <span className="flex items-center gap-1.5 text-xs font-semibold text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 px-2.5 py-1 rounded-full">
                  <span className="omnix-live-dot" style={{width:'6px',height:'6px',marginRight:0}} />
                  LIVE
                </span>
                <span className="text-white font-bold text-lg">Digital Asset Trading</span>
              </div>
              <p className="text-muted text-sm mb-5">Governance layer for automated crypto trading. Every entry decision passes through 11 checkpoints + Trajectory Invariant Enforcement before execution.</p>
              <div className="grid grid-cols-2 gap-4 mb-5">
                <div><div className="text-xl font-bold text-[#C9A227]">119+</div><div className="text-xs text-muted">Decisions governed</div></div>
                <div><div className="text-xl font-bold text-emerald-400">100%</div><div className="text-xs text-muted">PQC-signed receipts</div></div>
              </div>
              <Link to="/try" className="text-[#C9A227] text-sm hover:text-white transition-colors flex items-center gap-1">
                Try the governance sandbox <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
            <div className="glass-card p-8 border border-violet-400/20">
              <div className="flex items-center gap-3 mb-4">
                <span className="flex items-center gap-1.5 text-xs font-semibold text-violet-400 bg-violet-400/10 border border-violet-400/20 px-2.5 py-1 rounded-full">
                  <span style={{width:'6px',height:'6px',borderRadius:'50%',background:'#a78bfa',display:'inline-block',marginRight:0}} />
                  LIVE
                </span>
                <span className="text-white font-bold text-lg">Islamic Credit — UAE</span>
              </div>
              <p className="text-muted text-sm mb-5">Governance engine for Islamic finance credit decisions. Sharia compliance gate + 11 checkpoints evaluating SME, individual, and corporate applications 24/7.</p>
              <div className="grid grid-cols-2 gap-4 mb-5">
                <div><div className="text-xl font-bold text-violet-400">18,811+</div><div className="text-xs text-muted">Applications evaluated</div></div>
                <div><div className="text-xl font-bold text-violet-400">AED 77.4B+</div><div className="text-xs text-muted">Financing governed</div></div>
              </div>
              <Link to="/credit" className="text-violet-400 text-sm hover:text-white transition-colors flex items-center gap-1">
                View live governance dashboard <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="glass-card p-8 border border-blue-400/20">
              <div className="flex items-center gap-3 mb-4">
                <span className="flex items-center gap-1.5 text-xs font-semibold text-blue-400 bg-blue-400/10 border border-blue-400/20 px-2.5 py-1 rounded-full">
                  <span style={{width:'6px',height:'6px',borderRadius:'50%',background:'#60a5fa',display:'inline-block',marginRight:0}} />
                  LIVE
                </span>
                <span className="text-white font-bold text-lg">Insurance — Global</span>
              </div>
              <p className="text-muted text-sm mb-5">Governance engine for insurance claim decisions. Fraud detection gate + 11 checkpoints screening Auto, Property, Cyber, and Liability claims across NA, EU, APAC, and MEA markets.</p>
              <div className="grid grid-cols-2 gap-4 mb-5">
                <div><div className="text-xl font-bold text-blue-400">Multi-region</div><div className="text-xs text-muted">NA · EU · APAC · MEA</div></div>
                <div><div className="text-xl font-bold text-blue-400">6 types</div><div className="text-xs text-muted">Auto · Property · Cyber · Life</div></div>
              </div>
              <Link to="/insurance" className="text-blue-400 text-sm hover:text-white transition-colors flex items-center gap-1">
                View live governance dashboard <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="glass-card p-8 border border-emerald-400/20">
              <div className="flex items-center gap-3 mb-4">
                <span className="flex items-center gap-1.5 text-xs font-semibold text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 px-2.5 py-1 rounded-full">
                  <span style={{width:'6px',height:'6px',borderRadius:'50%',background:'#34d399',display:'inline-block',marginRight:0}} />
                  LIVE
                </span>
                <span className="text-white font-bold text-lg">Robotics — Autonomous Systems</span>
              </div>
              <p className="text-muted text-sm mb-5">Pre-execution governance for robot actions. Every action evaluated through 11 checkpoints before it runs — sensor fusion validation, collision risk, mechanical margin, and mission logic consistency.</p>
              <div className="grid grid-cols-2 gap-4 mb-5">
                <div><div className="text-xl font-bold text-emerald-400">6 industries</div><div className="text-xs text-muted">Auto · Pharma · Logistics · Food</div></div>
                <div><div className="text-xl font-bold text-emerald-400">5 robot types</div><div className="text-xs text-muted">Arm · AMR · Cobot · Drone · AGV</div></div>
              </div>
              <Link to="/robotics" className="text-emerald-400 text-sm hover:text-white transition-colors flex items-center gap-1">
                View live governance dashboard <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="glass-card p-8 border border-pink-400/20">
              <div className="flex items-center gap-3 mb-4">
                <span className="flex items-center gap-1.5 text-xs font-semibold text-pink-400 bg-pink-400/10 border border-pink-400/20 px-2.5 py-1 rounded-full">
                  <span style={{width:'6px',height:'6px',borderRadius:'50%',background:'#f472b6',display:'inline-block',marginRight:0}} />
                  LIVE
                </span>
                <span className="text-white font-bold text-lg">Medical AI Governance</span>
              </div>
              <p className="text-muted text-sm mb-5">Pre-authorization governance for medical AI decisions. Bias detection gate + 11 checkpoints screening diagnostics, treatment recommendations, drug dosing, and imaging interpretations 24/7.</p>
              <div className="grid grid-cols-2 gap-4 mb-5">
                <div><div className="text-xl font-bold text-pink-400">4 AI types</div><div className="text-xs text-muted">Diagnostics · Treatment · Drug · Imaging</div></div>
                <div><div className="text-xl font-bold text-pink-400">240s cycles</div><div className="text-xs text-muted">Continuous evaluation</div></div>
              </div>
              <Link to="/medical" className="text-pink-400 text-sm hover:text-white transition-colors flex items-center gap-1">
                View live governance dashboard <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="glass-card p-8 border border-orange-400/20">
              <div className="flex items-center gap-3 mb-4">
                <span className="flex items-center gap-1.5 text-xs font-semibold text-orange-400 bg-orange-400/10 border border-orange-400/20 px-2.5 py-1 rounded-full">
                  <span style={{width:'6px',height:'6px',borderRadius:'50%',background:'#fb923c',display:'inline-block',marginRight:0}} />
                  LIVE
                </span>
                <span className="text-white font-bold text-lg">Autonomous Agent Governance</span>
              </div>
              <p className="text-muted text-sm mb-5">Pre-execution governance for AI agent actions. Intent validation gate + 11 checkpoints evaluating every agent decision before it executes — across trading, content, support, and research agents.</p>
              <div className="grid grid-cols-2 gap-4 mb-5">
                <div><div className="text-xl font-bold text-orange-400">4 agent types</div><div className="text-xs text-muted">Trading · Content · Support · Research</div></div>
                <div><div className="text-xl font-bold text-orange-400">200s cycles</div><div className="text-xs text-muted">Real-time evaluation</div></div>
              </div>
              <Link to="/agents" className="text-orange-400 text-sm hover:text-white transition-colors flex items-center gap-1">
                View live governance dashboard <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </section>

        <section className="mb-24">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-white mb-4">What Makes OMNIX Different</h2>
          </div>
          <div className="space-y-4 max-w-2xl mx-auto">
            <div className="flex items-start gap-4 p-4 bg-[#0A1628]/60 rounded-xl border border-[#C9A227]/20">
              <CheckCircle className="w-6 h-6 text-emerald-500 flex-shrink-0 mt-0.5" />
              <p className="text-muted"><span className="text-white font-medium">Blocks first, asks questions later.</span> We stop risky decisions before they cost you money.</p>
            </div>
            <div className="flex items-start gap-4 p-4 bg-[#0A1628]/60 rounded-xl border border-[#C9A227]/20">
              <CheckCircle className="w-6 h-6 text-emerald-500 flex-shrink-0 mt-0.5" />
              <p className="text-muted"><span className="text-white font-medium">Real-time context analysis.</span> We evaluate conditions before every decision.</p>
            </div>
            <div className="flex items-start gap-4 p-4 bg-[#0A1628]/60 rounded-xl border border-[#C9A227]/20">
              <CheckCircle className="w-6 h-6 text-emerald-500 flex-shrink-0 mt-0.5" />
              <p className="text-muted"><span className="text-white font-medium">No false promises.</span> We don't guarantee outcomes. We help prevent costly mistakes.</p>
            </div>
            <div className="flex items-start gap-4 p-4 bg-[#C9A227]/5 rounded-xl border border-[#C9A227]/30">
              <CheckCircle className="w-6 h-6 text-[#C9A227] flex-shrink-0 mt-0.5" />
              <p className="text-muted"><span className="text-[#C9A227] font-medium">Understands context, not just conditions.</span> Other systems follow rules. OMNIX understands when and why they should apply — with full context, memory, and cryptographic proof.</p>
            </div>
          </div>
        </section>

        {/* ── DECISION ADMISSIBILITY GAP ── */}
        <section className="mb-24">
          <div className="text-center mb-14">
            <span className="text-xs font-bold text-[#C9A227] uppercase tracking-widest mb-4 block">THE GAP NO ONE IS FILLING</span>
            <h2 className="text-4xl font-bold text-white mb-5 leading-tight">
              The <span className="gold-gradient">Decision Admissibility Gap</span>
            </h2>
            <p className="text-lg text-muted max-w-3xl mx-auto leading-relaxed">
              Every AI governance stack assumes the decision coming in is worth making. No one checks.
              That assumption is where catastrophic failures originate.
            </p>
          </div>

          <div className="max-w-2xl mx-auto mb-16">
            {['Orchestration & Pipelines', 'Tool Schemas & Routing', 'Permissions & Guardrails', 'Logging & Audit'].map((layer) => (
              <div key={layer} className="mb-1.5 rounded-lg px-6 py-3 text-center text-sm font-medium text-[#64748B] border border-[#1E293B] bg-[#0A1628]/40">
                {layer}
              </div>
            ))}

            <div className="my-3 rounded-xl border-2 border-red-500/40 bg-red-500/5 px-6 py-5 text-center relative overflow-hidden">
              <div className="absolute inset-0 pointer-events-none" style={{background:'radial-gradient(ellipse at center, rgba(239,68,68,0.06) 0%, transparent 70%)'}} />
              <div className="text-red-400 font-black text-lg tracking-widest mb-1.5 uppercase">Decision Admissibility Gap</div>
              <div className="text-red-300/60 text-sm">All upstream layers assume the incoming decision is valid. No system verifies it should be made at all.</div>
            </div>

            <div className="my-1.5 rounded-2xl border-2 border-[#C9A227] bg-[#C9A227]/5 px-6 py-7 text-center relative overflow-hidden" style={{boxShadow:'0 0 40px rgba(201,162,39,0.12)'}}>
              <div className="absolute top-0 left-0 right-0 h-px" style={{background:'linear-gradient(90deg, transparent, #C9A227, transparent)'}} />
              <div className="text-[#C9A227] font-black text-2xl tracking-tight mb-1">OMNIX</div>
              <div className="text-white/90 font-bold text-sm mb-4 tracking-wide uppercase">Pre-Decision Governance Layer</div>
              <div className="text-xs text-[#94A3B8] mb-4 font-mono">Evaluate → Gate → Certify → Proceed or Block</div>
              <div className="flex flex-wrap justify-center gap-2">
                {['Admissibility', 'Risk Analysis', 'Sharia Gate', 'Context Memory', 'Dilithium-3 PQC', 'Counterfactual Proof'].map(tag => (
                  <span key={tag} className="px-3 py-1 rounded-full text-xs font-semibold bg-[#C9A227]/10 border border-[#C9A227]/25 text-[#C9A227]/90">{tag}</span>
                ))}
              </div>
              <div className="absolute bottom-0 left-0 right-0 h-px" style={{background:'linear-gradient(90deg, transparent, #C9A227, transparent)'}} />
            </div>

            <div className="mt-1.5 rounded-lg border border-[#1E293B] bg-[#0A1628]/60 px-6 py-4 text-center">
              <div className="text-white font-bold text-sm mb-1">EXECUTION BOUNDARY</div>
              <div className="text-[#64748B] text-xs">Trading · Credit · Insurance · Robotics · Medical · Agents · Real Estate · Energy</div>
            </div>
          </div>

          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            <div className="glass-card p-7 text-center">
              <div className="text-4xl font-black text-red-400 mb-3">0</div>
              <div className="text-sm text-white font-semibold mb-2">Systems that verify decision admissibility</div>
              <div className="text-xs text-muted leading-relaxed">Before OMNIX, no production system asked whether a decision should be made at all — only whether it was technically executable.</div>
            </div>
            <div className="glass-card p-7 text-center" style={{borderColor:'rgba(201,162,39,0.3)'}}>
              <div className="text-4xl font-black text-[#C9A227] mb-3">11</div>
              <div className="text-sm text-white font-semibold mb-2">Independent governance checkpoints</div>
              <div className="text-xs text-muted leading-relaxed">Each checkpoint operates independently. Any single gate can veto a decision before it reaches any execution system.</div>
            </div>
            <div className="glass-card p-7 text-center">
              <div className="text-4xl font-black text-emerald-400 mb-3">8</div>
              <div className="text-sm text-white font-semibold mb-2">Domains under active governance</div>
              <div className="text-xs text-muted leading-relaxed">Trading, Credit, Insurance, Robotics, Medical AI, Autonomous Agents, Real Estate, and Energy — all running 24/7.</div>
            </div>
          </div>
        </section>

        {/* ── COMPETITIVE COMPARISON ── */}
        <section className="mb-24">
          <div className="text-center mb-12">
            <span className="text-xs font-bold text-[#C9A227] uppercase tracking-widest mb-4 block">LANDSCAPE ANALYSIS</span>
            <h2 className="text-4xl font-bold text-white mb-5">
              How OMNIX <span className="gold-gradient">Compares</span>
            </h2>
            <p className="text-muted max-w-2xl mx-auto">
              This table reflects which governance controls are built-in by default — not what teams could theoretically build themselves.
            </p>
          </div>

          <div className="overflow-x-auto rounded-2xl border border-[#1E293B]">
            <table style={{width:'100%',borderCollapse:'collapse'}}>
              <thead>
                <tr style={{background:'rgba(10,22,40,0.9)'}}>
                  <th className="text-left px-5 py-4 text-xs font-semibold text-muted uppercase tracking-wider border-b border-[#1E293B]" style={{minWidth:260}}>Governance Capability</th>
                  {[
                    {name:'OMNIX', color:'#C9A227'},
                    {name:'A2SPA', color:'#94A3B8'},
                    {name:'MCP', color:'#94A3B8'},
                    {name:'LangChain', color:'#94A3B8'},
                    {name:'AWS Bedrock', color:'#94A3B8'},
                    {name:'AutoGPT', color:'#94A3B8'},
                  ].map(({name,color}) => (
                    <th key={name} className="px-4 py-4 text-xs font-bold text-center uppercase tracking-wider border-b border-[#1E293B]" style={{color, minWidth:100}}>{name}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[
                  {label:'Pre-decision admissibility assessment', vals:[true,false,false,false,false,false]},
                  {label:'Multi-checkpoint governance pipeline (11 gates)', vals:[true,false,false,false,false,false]},
                  {label:'Domain-specific governance (8 sectors)', vals:[true,false,false,false,false,false]},
                  {label:'Sharia-aligned governance gate', vals:[true,false,false,false,false,false]},
                  {label:'Post-quantum cryptography (Dilithium-3 NIST)', vals:[true,false,false,false,false,false]},
                  {label:'W3C Verifiable Credential decision receipts', vals:[true,false,false,false,false,false]},
                  {label:'Counterfactual validation (Shadow Portfolio)', vals:[true,false,false,false,false,false]},
                  {label:'Human deliberation integration (HOLD state)', vals:[true,false,false,false,false,false]},
                  {label:'Execution payload signing', vals:[false,true,false,false,false,false]},
                  {label:'Tamper-proof audit trail', vals:[true,true,false,false,true,false]},
                  {label:'Real-time risk analysis', vals:[true,false,false,true,false,false]},
                ].map((row, i) => (
                  <tr key={i} style={{background: i%2===0 ? 'rgba(5,13,24,0.5)' : 'rgba(10,22,40,0.3)'}}>
                    <td className="px-5 py-3.5 text-sm text-[#CBD5E1]">{row.label}</td>
                    {row.vals.map((v, j) => (
                      <td key={j} className="px-4 py-3.5 text-center">
                        {v
                          ? <span style={{color: j===0 ? '#C9A227' : '#10B981', fontSize:'1.1rem', fontWeight:900}}>✓</span>
                          : <span style={{color:'rgba(239,68,68,0.45)', fontSize:'1rem', fontWeight:700}}>✗</span>
                        }
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-8 glass-card p-7 max-w-3xl mx-auto text-center" style={{borderColor:'rgba(201,162,39,0.2)'}}>
            <div className="text-xs font-bold text-[#C9A227] uppercase tracking-widest mb-3">Important context</div>
            <p className="text-sm text-muted leading-relaxed">
              <span className="text-white font-semibold">OMNIX and A2SPA solve different problems and are architecturally complementary.</span>
              {' '}OMNIX governs the admissibility of a decision before any execution system is involved.
              A2SPA signs the execution payload at the moment an agent acts. Together, they form a complete governance stack:
              {' '}<span className="text-[#C9A227]">pre-decision admissibility + execution-time authorization</span>.
            </p>
          </div>
        </section>

        {/* ── PRICING ── */}
        <section className="mb-24" id="pricing">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-white mb-4">Governance Access Plans</h2>
            <p className="text-muted max-w-xl mx-auto">Start with the free pilot. The difference between plans is not volume — it's authority. Advisory plans observe. Only Enterprise can stop a decision.</p>
          </div>

          {/* Subscription tiers */}
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4 mb-8">

            {/* Tier 1 — Shadow */}
            <div className="flex flex-col bg-[#0A1628]/80 border border-[#334155] rounded-2xl p-5">
              <div className="mb-4">
                <span className="text-xs font-bold text-emerald-400 uppercase tracking-widest">Shadow Mode</span>
                <div className="mt-3">
                  <span className="text-3xl font-black text-white">Free</span>
                </div>
                <p className="text-xs text-muted mt-1">4-week pilot · No commitment</p>
              </div>
              <ul className="space-y-2 flex-1 mb-5">
                {[
                  'Runs alongside your system',
                  'Zero interventions — no operational risk',
                  'Full report: what would have been blocked',
                  'PQC-signed receipts included',
                ].map(f => (
                  <li key={f} className="flex items-start gap-2 text-xs text-muted">
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0 mt-0.5" />{f}
                  </li>
                ))}
              </ul>
              <a href="https://wa.me/16505078293?text=I%27d%20like%20to%20start%20the%20Shadow%20Mode%20pilot" target="_blank" rel="noopener noreferrer"
                className="block text-center py-2 rounded-xl border border-emerald-500/50 text-emerald-400 text-xs font-semibold hover:bg-emerald-500/10 transition-colors">
                Start Free Pilot
              </a>
            </div>

            {/* Tier 2 — Advisory */}
            <div className="flex flex-col bg-[#0A1628]/80 border border-[#334155] rounded-2xl p-5">
              <div className="mb-4">
                <span className="text-xs font-bold text-[#06b6d4] uppercase tracking-widest">Advisory</span>
                <div className="mt-3 flex items-baseline gap-1">
                  <span className="text-3xl font-black text-white">$8K</span>
                  <span className="text-xs text-muted font-medium">/ month</span>
                </div>
                <p className="text-xs text-muted mt-1">Observation tier · 1 vertical</p>
              </div>
              <ul className="space-y-2 flex-1 mb-5">
                {[
                  'OMNIX observes every decision in real time',
                  'Your team retains full authority — OMNIX advises',
                  'PQC-signed receipt per recommendation',
                  '1 vertical of choice',
                  'Monthly governance report',
                ].map(f => (
                  <li key={f} className="flex items-start gap-2 text-xs text-muted">
                    <CheckCircle className="w-3.5 h-3.5 text-[#06b6d4] flex-shrink-0 mt-0.5" />{f}
                  </li>
                ))}
              </ul>
              <a href="https://wa.me/16505078293?text=I%27m%20interested%20in%20the%20Advisory%20plan" target="_blank" rel="noopener noreferrer"
                className="block text-center py-2 rounded-xl border border-[#06b6d4]/50 text-[#06b6d4] text-xs font-semibold hover:bg-[#06b6d4]/10 transition-colors">
                Talk to Us
              </a>
            </div>

            {/* Tier 3 — Professional */}
            <div className="flex flex-col bg-[#0A1628]/80 border border-[#a78bfa]/40 rounded-2xl p-5">
              <div className="mb-4">
                <span className="text-xs font-bold text-[#a78bfa] uppercase tracking-widest">Professional</span>
                <div className="mt-3 flex items-baseline gap-1">
                  <span className="text-3xl font-black text-white">$20K</span>
                  <span className="text-xs text-muted font-medium">/ month</span>
                </div>
                <p className="text-xs text-muted mt-1">Governance authority · Up to 4 verticals</p>
              </div>
              <ul className="space-y-2 flex-1 mb-5">
                {[
                  'HOLD state resolution included',
                  'Governance authority on selected verticals',
                  'Up to 4 verticals active simultaneously',
                  'Full audit trail + regulator export',
                  'API integration included',
                  'PQC-signed receipts on every decision',
                ].map(f => (
                  <li key={f} className="flex items-start gap-2 text-xs text-muted">
                    <CheckCircle className="w-3.5 h-3.5 text-[#a78bfa] flex-shrink-0 mt-0.5" />{f}
                  </li>
                ))}
              </ul>
              <a href="https://wa.me/16505078293?text=I%27m%20interested%20in%20the%20Professional%20plan" target="_blank" rel="noopener noreferrer"
                className="block text-center py-2 rounded-xl border border-[#a78bfa]/50 text-[#a78bfa] text-xs font-semibold hover:bg-[#a78bfa]/10 transition-colors">
                Talk to Us
              </a>
            </div>

            {/* Tier 4 — Enterprise */}
            <div className="flex flex-col bg-[#0A1628]/80 border-2 border-[#C9A227] rounded-2xl p-5 relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 whitespace-nowrap">
                <span className="bg-[#C9A227] text-[#0a0f1a] text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wide">Most Popular</span>
              </div>
              <div className="mb-4">
                <span className="text-xs font-bold text-[#C9A227] uppercase tracking-widest">Enterprise</span>
                <div className="mt-3 flex items-baseline gap-1">
                  <span className="text-3xl font-black text-white">$25K</span>
                  <span className="text-xs text-muted font-medium">/ month</span>
                </div>
                <p className="text-xs text-[#C9A227]/70 mt-0.5 font-medium">$300,000 / year · All 8 verticals</p>
              </div>
              <ul className="space-y-2 flex-1 mb-5">
                {[
                  'Full veto authority — fail-closed by default',
                  'All 8 verticals active',
                  'Unlimited governed decisions',
                  'Complete audit trail for regulators',
                  'Dedicated onboarding + SLA 99.9%',
                  'Sharia-aligned governance gate included',
                ].map(f => (
                  <li key={f} className="flex items-start gap-2 text-xs text-muted">
                    <CheckCircle className="w-3.5 h-3.5 text-[#C9A227] flex-shrink-0 mt-0.5" />{f}
                  </li>
                ))}
              </ul>
              <a href="https://wa.me/16505078293?text=I%27m%20interested%20in%20the%20Enterprise%20plan" target="_blank" rel="noopener noreferrer"
                className="block text-center py-2 rounded-xl bg-[#C9A227] text-[#0a0f1a] text-xs font-bold hover:bg-[#F5D97A] transition-colors">
                Talk to Us
              </a>
            </div>

            {/* Tier 5 — Custom */}
            <div className="flex flex-col bg-[#0A1628]/80 border border-[#3b82f6]/50 rounded-2xl p-5">
              <div className="mb-4">
                <span className="text-xs font-bold text-[#3b82f6] uppercase tracking-widest">Custom</span>
                <div className="mt-3">
                  <span className="text-3xl font-black text-white">Custom</span>
                </div>
                <p className="text-xs text-muted mt-1">Large-scale · White-label · On-premise</p>
              </div>
              <ul className="space-y-2 flex-1 mb-5">
                {[
                  'Multi-tenant infrastructure',
                  'White-label options available',
                  'Revenue share model available',
                  'Custom vertical development',
                  'On-premise deployment',
                  'Dedicated governance architect',
                ].map(f => (
                  <li key={f} className="flex items-start gap-2 text-xs text-muted">
                    <CheckCircle className="w-3.5 h-3.5 text-[#3b82f6] flex-shrink-0 mt-0.5" />{f}
                  </li>
                ))}
              </ul>
              <a href="mailto:contacto@omnixquantum.net?subject=Custom%20Deployment%20Inquiry"
                className="block text-center py-2 rounded-xl border border-[#3b82f6]/60 text-[#3b82f6] text-xs font-semibold hover:bg-[#3b82f6]/10 hover:text-white transition-colors">
                Contact Us
              </a>
            </div>
          </div>

          {/* Usage-based pricing */}
          <div className="grid md:grid-cols-2 gap-4 mb-10">
            <div className="bg-[#0A1628]/60 border border-[#1E293B] rounded-2xl p-6 flex items-start gap-5">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center flex-shrink-0">
                <Zap className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <div className="text-xs font-bold text-emerald-400 uppercase tracking-widest mb-1">Pay-per-Decision</div>
                <div className="flex items-baseline gap-1 mb-1">
                  <span className="text-2xl font-black text-white">$0.05</span>
                  <span className="text-sm text-muted">/ governed decision</span>
                </div>
                <p className="text-xs text-muted leading-relaxed">For organisations with variable decision volume. Every governed decision includes a PQC-signed receipt. No monthly commitment required.</p>
              </div>
            </div>
            <div className="bg-[#0A1628]/60 border border-[#1E293B] rounded-2xl p-6 flex items-start gap-5">
              <div className="w-10 h-10 rounded-xl bg-[#C9A227]/10 border border-[#C9A227]/20 flex items-center justify-center flex-shrink-0">
                <Phone className="w-5 h-5 text-[#C9A227]" />
              </div>
              <div>
                <div className="text-xs font-bold text-[#C9A227] uppercase tracking-widest mb-1">API Call Pricing</div>
                <div className="flex items-baseline gap-1 mb-1">
                  <span className="text-2xl font-black text-white">Contact Us</span>
                </div>
                <p className="text-xs text-muted leading-relaxed">Volume-based API pricing for high-throughput integrations. Rate limits, SLA tiers, and dedicated infrastructure available for enterprise API deployments.</p>
              </div>
            </div>
          </div>

          <p className="text-center text-sm text-white/70 font-medium mb-2">
            Advisory and Professional plans advise. Only Enterprise has full authority to stop a decision.
          </p>
          <p className="text-center text-xs text-muted">
            All plans include post-quantum cryptographic receipts (NIST-standardized) · No hidden fees · Start with the free pilot, no card required
          </p>
        </section>

        <section className="glass-card p-12 gold-glow">
          <h2 className="text-3xl font-bold text-white text-center mb-4">Ready to Govern Your Decisions?</h2>
          <p className="text-xl text-muted max-w-2xl mx-auto mb-10 text-center">
            Let's talk about how OMNIX can help govern high-stakes decisions for your organization.
          </p>

          {formStatus === 'success' ? (
            <div className="text-center py-8">
              <div className="w-16 h-16 rounded-full bg-emerald-500/20 flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-8 h-8 text-emerald-400" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Thank you for reaching out!</h3>
              <p className="text-muted mb-6">We'll get back to you shortly.</p>
              <button
                onClick={() => setFormStatus('idle')}
                className="text-[#C9A227] hover:text-white transition-colors text-sm"
              >
                Send another message
              </button>
            </div>
          ) : (
            <form onSubmit={handleFormSubmit} className="max-w-xl mx-auto space-y-5">
              <div className="grid md:grid-cols-2 gap-5">
                <div>
                  <label htmlFor="contact-name" className="block text-sm font-medium text-muted mb-1.5">Name *</label>
                  <input
                    id="contact-name"
                    name="name"
                    type="text"
                    required
                    value={formData.name}
                    onChange={handleFormChange}
                    className="w-full px-4 py-3 rounded-xl bg-[#0A1628]/80 border border-[#C9A227]/20 text-white placeholder-gray-500 focus:outline-none focus:border-[#C9A227]/60 transition-colors"
                    placeholder="Your name"
                  />
                </div>
                <div>
                  <label htmlFor="contact-company" className="block text-sm font-medium text-muted mb-1.5">Company</label>
                  <input
                    id="contact-company"
                    name="company"
                    type="text"
                    value={formData.company}
                    onChange={handleFormChange}
                    className="w-full px-4 py-3 rounded-xl bg-[#0A1628]/80 border border-[#C9A227]/20 text-white placeholder-gray-500 focus:outline-none focus:border-[#C9A227]/60 transition-colors"
                    placeholder="Your company"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="contact-email" className="block text-sm font-medium text-muted mb-1.5">Email *</label>
                <input
                  id="contact-email"
                  name="email"
                  type="email"
                  required
                  value={formData.email}
                  onChange={handleFormChange}
                  className="w-full px-4 py-3 rounded-xl bg-[#0A1628]/80 border border-[#C9A227]/20 text-white placeholder-gray-500 focus:outline-none focus:border-[#C9A227]/60 transition-colors"
                  placeholder="you@company.com"
                />
              </div>

              <div>
                <label htmlFor="contact-referral" className="block text-sm font-medium text-muted mb-1.5">How did you find us? *</label>
                <select
                  id="contact-referral"
                  name="referral_source"
                  required
                  value={formData.referral_source}
                  onChange={handleFormChange}
                  className="w-full px-4 py-3 rounded-xl bg-[#0A1628]/80 border border-[#C9A227]/20 text-white focus:outline-none focus:border-[#C9A227]/60 transition-colors appearance-none"
                >
                  <option value="" disabled className="text-gray-500">Select an option</option>
                  {REFERRAL_OPTIONS.map(opt => (
                    <option key={opt} value={opt} className="bg-[#0A1628] text-white">{opt}</option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="contact-message" className="block text-sm font-medium text-muted mb-1.5">Message (optional)</label>
                <textarea
                  id="contact-message"
                  name="message"
                  rows={3}
                  value={formData.message}
                  onChange={handleFormChange}
                  className="w-full px-4 py-3 rounded-xl bg-[#0A1628]/80 border border-[#C9A227]/20 text-white placeholder-gray-500 focus:outline-none focus:border-[#C9A227]/60 transition-colors resize-none"
                  placeholder="Tell us about your needs..."
                />
              </div>

              {formStatus === 'error' && (
                <div className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3">
                  {formError}
                </div>
              )}

              <button
                type="submit"
                disabled={formStatus === 'sending'}
                className="btn-primary w-full flex items-center justify-center gap-2 py-3 disabled:opacity-60"
              >
                {formStatus === 'sending' ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Sending...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    Send Message
                  </>
                )}
              </button>
            </form>
          )}

          <div className="flex flex-col items-center gap-3 text-sm mt-8 pt-8 border-t border-[#C9A227]/10">
            <a href="mailto:contacto@omnixquantum.net" className="text-[#C9A227] hover:text-white transition-colors flex items-center gap-2">
              <Mail className="w-4 h-4" />
              contacto@omnixquantum.net
            </a>
            <a href="tel:+16505078293" className="text-[#10b981] hover:text-white transition-colors flex items-center gap-2">
              <Phone className="w-4 h-4" />
              Phone: +1 (650) 507-8293
            </a>
            <a href="https://wa.me/16505078293?text=Hi%2C%20I%27m%20interested%20in%20OMNIX" target="_blank" rel="noopener noreferrer" className="text-[#10b981] hover:text-white transition-colors flex items-center gap-2">
              <span className="text-lg">💬</span>
              WhatsApp: +1 (650) 507-8293
            </a>
          </div>
        </section>

        <div className="mt-12 text-center space-y-3">
          <Link to="/governance-demo" className="text-emerald-400 hover:text-white transition-colors flex items-center justify-center gap-2">
            See our multi-vertical governance demo in action
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link to="/institutional" className="text-[#C9A227] hover:text-white transition-colors flex items-center justify-center gap-2">
            Looking for technical details? View our Institutional page
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        <section className="mt-20 max-w-4xl mx-auto px-4">
          <div className="text-center mb-10">
            <h2 className="text-2xl font-bold text-white mb-2">Research & Publications</h2>
            <p className="text-muted text-sm">Peer-indexed technical documentation available on independent academic repositories</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <a
              href="https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6507559"
              target="_blank"
              rel="noopener noreferrer"
              className="block p-5 rounded-2xl border border-[#C9A227]/20 bg-[#0A1628]/60 hover:border-[#C9A227]/50 hover:bg-[#0A1628]/80 transition-all group"
            >
              <div className="flex items-start justify-between mb-3">
                <span className="text-xs font-semibold px-2 py-1 rounded-full bg-[#C9A227]/10 text-[#C9A227] border border-[#C9A227]/20">SSRN</span>
                <ArrowRight className="w-4 h-4 text-muted group-hover:text-[#C9A227] transition-colors" />
              </div>
              <h3 className="text-white font-semibold text-sm mb-2 leading-snug">OMNIX Quantum: Decision Governance Infrastructure for Automated Systems — Technical Whitepaper</h3>
              <p className="text-muted text-xs">Harold Nunes · OMNIX Quantum · 2026</p>
              <p className="text-[#C9A227]/60 text-xs mt-2">Abstract ID: 6507559</p>
            </a>

            <a
              href="https://doi.org/10.5281/zenodo.19375792"
              target="_blank"
              rel="noopener noreferrer"
              className="block p-5 rounded-2xl border border-[#C9A227]/20 bg-[#0A1628]/60 hover:border-[#C9A227]/50 hover:bg-[#0A1628]/80 transition-all group"
            >
              <div className="flex items-start justify-between mb-3">
                <span className="text-xs font-semibold px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Zenodo</span>
                <ArrowRight className="w-4 h-4 text-muted group-hover:text-emerald-400 transition-colors" />
              </div>
              <h3 className="text-white font-semibold text-sm mb-2 leading-snug">OMNIX Quantum: Decision Governance Infrastructure for Automated Systems — Technical Whitepaper</h3>
              <p className="text-muted text-xs">Harold Nunes · OMNIX Quantum · 2026</p>
              <p className="text-emerald-400/60 text-xs mt-2">DOI: 10.5281/zenodo.19375792</p>
            </a>

            <a
              href="https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6321298"
              target="_blank"
              rel="noopener noreferrer"
              className="block p-5 rounded-2xl border border-[#C9A227]/20 bg-[#0A1628]/60 hover:border-[#C9A227]/50 hover:bg-[#0A1628]/80 transition-all group"
            >
              <div className="flex items-start justify-between mb-3">
                <span className="text-xs font-semibold px-2 py-1 rounded-full bg-[#C9A227]/10 text-[#C9A227] border border-[#C9A227]/20">SSRN</span>
                <ArrowRight className="w-4 h-4 text-muted group-hover:text-[#C9A227] transition-colors" />
              </div>
              <h3 className="text-white font-semibold text-sm mb-2 leading-snug">Post-Quantum Cryptographic Architecture for Decision Governance Systems — ADR-022</h3>
              <p className="text-muted text-xs">Harold Nunes · OMNIX Quantum · 2026</p>
              <p className="text-[#C9A227]/60 text-xs mt-2">Abstract ID: 6321298</p>
            </a>

            <a
              href="https://doi.org/10.5281/zenodo.19056919"
              target="_blank"
              rel="noopener noreferrer"
              className="block p-5 rounded-2xl border border-[#C9A227]/20 bg-[#0A1628]/60 hover:border-[#C9A227]/50 hover:bg-[#0A1628]/80 transition-all group"
            >
              <div className="flex items-start justify-between mb-3">
                <span className="text-xs font-semibold px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Zenodo</span>
                <ArrowRight className="w-4 h-4 text-muted group-hover:text-emerald-400 transition-colors" />
              </div>
              <h3 className="text-white font-semibold text-sm mb-2 leading-snug">Post-Quantum Cryptographic Architecture for Decision Governance Systems — ADR-022</h3>
              <p className="text-muted text-xs">Harold Nunes · OMNIX Quantum · 2026</p>
              <p className="text-emerald-400/60 text-xs mt-2">DOI: 10.5281/zenodo.19056919</p>
            </a>
          </div>
        </section>
      </main>

      <footer className="border-t border-[#C9A227]/10 py-12 px-6">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-3">
              <img src="/logo.png" alt="OMNIX" className="w-10 h-10 object-contain" />
              <span className="text-muted text-sm">&copy; 2026 OMNIX QUANTUM LTD. All rights reserved.</span>
            </div>
            <span className="text-muted text-xs opacity-60">Registered in England &amp; Wales &middot; 71-75 Shelton Street, Covent Garden, London, WC2H 9JQ</span>
          </div>
          <div className="flex items-center gap-6">
            <Link to="/try" className="text-[#C9A227] hover:text-white text-sm transition-colors font-medium">
              Try OMNIX
            </Link>
            <Link to="/governance-demo" className="text-muted hover:text-white text-sm transition-colors">
              Credit Demo
            </Link>
            <Link to="/governance-demo-insurance" className="text-muted hover:text-white text-sm transition-colors">
              Insurance Demo
            </Link>
            <Link to="/governance-demo-energy" className="text-muted hover:text-white text-sm transition-colors">
              Energy Demo
            </Link>
            <Link to="/governance-demo-biotech" className="text-muted hover:text-white text-sm transition-colors">
              Biotech Demo
            </Link>
            <Link to="/institutional" className="text-muted hover:text-white text-sm transition-colors">
              Technical Details
            </Link>
            <Link to="/my-report" className="text-muted hover:text-white text-sm transition-colors">
              Client Portal
            </Link>
            <a href="https://wa.me/16505078293?text=Hi%2C%20I%27m%20interested%20in%20OMNIX" target="_blank" rel="noopener noreferrer" className="text-muted hover:text-white text-sm transition-colors">
              Contact
            </a>
            <Link to="/terms" className="text-muted hover:text-white text-sm transition-colors">
              Terms
            </Link>
            <Link to="/privacy" className="text-muted hover:text-white text-sm transition-colors">
              Privacy
            </Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
