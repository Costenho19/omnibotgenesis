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
            <h2 className="text-3xl font-bold text-white mb-3">Six Verticals. Running Now.</h2>
            <p className="text-muted max-w-2xl mx-auto">Same 11-checkpoint governance pipeline. Six live domains. All operating 24/7.</p>
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

        {/* ── PRICING ── */}
        <section className="mb-24" id="pricing">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-white mb-4">Governance Access Plans</h2>
            <p className="text-muted max-w-xl mx-auto">Start with the free pilot. The difference between plans is not volume — it's authority. Advisory plans observe. Only Enterprise can stop a decision.</p>
          </div>

          <div className="grid md:grid-cols-4 gap-5">
            {/* Tier 1 — Shadow */}
            <div className="flex flex-col bg-[#0A1628]/80 border border-[#334155] rounded-2xl p-6">
              <div className="mb-4">
                <span className="text-xs font-bold text-emerald-400 uppercase tracking-widest">Shadow Mode</span>
                <div className="mt-3 flex items-end gap-1">
                  <span className="text-4xl font-bold text-white">Free</span>
                </div>
                <p className="text-xs text-muted mt-1">4-week pilot · No commitment</p>
              </div>
              <ul className="space-y-2 flex-1 mb-6">
                {['OMNIX runs alongside your system', 'No interventions — zero operational risk', 'Full report: what would have been blocked', 'Post-quantum signed receipts included'].map(f => (
                  <li key={f} className="flex items-start gap-2 text-sm text-muted">
                    <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                    {f}
                  </li>
                ))}
              </ul>
              <a href="https://wa.me/16505078293?text=I%27d%20like%20to%20start%20the%20Shadow%20Mode%20pilot" target="_blank" rel="noopener noreferrer"
                className="block text-center py-2.5 rounded-xl border border-emerald-500/50 text-emerald-400 text-sm font-semibold hover:bg-emerald-500/10 transition-colors">
                Start Free Pilot
              </a>
            </div>

            {/* Tier 2 — Advisory */}
            <div className="flex flex-col bg-[#0A1628]/80 border border-[#334155] rounded-2xl p-6">
              <div className="mb-4">
                <span className="text-xs font-bold text-[#06b6d4] uppercase tracking-widest">Advisory</span>
                <div className="mt-3 flex items-end gap-1">
                  <span className="text-4xl font-bold text-white">Contact Us</span>
                </div>
                <p className="text-xs text-muted mt-1">Observation tier · Contact us</p>
              </div>
              <ul className="space-y-2 flex-1 mb-6">
                {['OMNIX observes every decision in real time', 'Your team retains full authority — OMNIX advises', 'PQC-signed receipt per recommendation', '1 vertical (trading, credit, insurance, or robotics)'].map(f => (
                  <li key={f} className="flex items-start gap-2 text-sm text-muted">
                    <CheckCircle className="w-4 h-4 text-[#06b6d4] flex-shrink-0 mt-0.5" />
                    {f}
                  </li>
                ))}
              </ul>
              <a href="https://wa.me/16505078293?text=I%27m%20interested%20in%20the%20Advisory%20plan" target="_blank" rel="noopener noreferrer"
                className="block text-center py-2.5 rounded-xl border border-[#06b6d4]/50 text-[#06b6d4] text-sm font-semibold hover:bg-[#06b6d4]/10 transition-colors">
                Talk to Us
              </a>
            </div>

            {/* Tier 3 — Enterprise */}
            <div className="flex flex-col bg-[#0A1628]/80 border-2 border-[#C9A227] rounded-2xl p-6 relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                <span className="bg-[#C9A227] text-[#0a0f1a] text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wide">Most Popular</span>
              </div>
              <div className="mb-4">
                <span className="text-xs font-bold text-[#C9A227] uppercase tracking-widest">Enterprise</span>
                <div className="mt-3 flex items-end gap-1">
                  <span className="text-4xl font-bold text-white">Contact Us</span>
                </div>
                <p className="text-xs text-muted mt-1">Governance authority tier · Early enterprise partners</p>
              </div>
              <ul className="space-y-2 flex-1 mb-6">
                {['Full veto authority — fail-closed by default', 'Unlimited governed decisions', 'All verticals included', 'Complete audit trail for regulators', 'API integration + dedicated onboarding', 'SLA 99.9% uptime guarantee'].map(f => (
                  <li key={f} className="flex items-start gap-2 text-sm text-muted">
                    <CheckCircle className="w-4 h-4 text-[#C9A227] flex-shrink-0 mt-0.5" />
                    {f}
                  </li>
                ))}
              </ul>
              <a href="https://wa.me/16505078293?text=I%27m%20interested%20in%20the%20Enterprise%20plan" target="_blank" rel="noopener noreferrer"
                className="block text-center py-2.5 rounded-xl bg-[#C9A227] text-[#0a0f1a] text-sm font-bold hover:bg-[#F5D97A] transition-colors">
                Talk to Us
              </a>
            </div>

            {/* Tier 4 — Custom */}
            <div className="flex flex-col bg-[#0A1628]/80 border border-[#3b82f6]/50 rounded-2xl p-6">
              <div className="mb-4">
                <span className="text-xs font-bold text-[#3b82f6] uppercase tracking-widest">Custom</span>
                <div className="mt-3 flex items-end gap-1">
                  <span className="text-4xl font-bold text-white">Contact Us</span>
                </div>
                <p className="text-xs text-muted mt-1">For large-scale deployments</p>
              </div>
              <ul className="space-y-2 flex-1 mb-6">
                {['Multi-tenant infrastructure', 'White-label options', 'Revenue share model available', 'Custom vertical development', 'On-premise deployment', 'Dedicated governance architect'].map(f => (
                  <li key={f} className="flex items-start gap-2 text-sm text-muted">
                    <CheckCircle className="w-4 h-4 text-[#3b82f6] flex-shrink-0 mt-0.5" />
                    {f}
                  </li>
                ))}
              </ul>
              <a href="mailto:contacto@omnixquantum.net?subject=Custom%20Deployment%20Inquiry"
                className="block text-center py-2.5 rounded-xl border border-[#3b82f6]/60 text-[#3b82f6] text-sm font-semibold hover:bg-[#3b82f6]/10 hover:text-white transition-colors">
                Contact Us
              </a>
            </div>
          </div>

          <p className="text-center text-sm text-white/70 mt-10 font-medium">
            Advisory plans observe decisions. Only Enterprise has authority to stop them.
          </p>
          <p className="text-center text-xs text-muted mt-4">
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
          <div className="flex items-center gap-3">
            <img src="/logo.png" alt="OMNIX" className="w-10 h-10 object-contain" />
            <span className="text-muted text-sm">&copy; 2026 OMNIX QUANTUM. All rights reserved.</span>
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
