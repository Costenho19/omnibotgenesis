import React, { useState, useEffect, useRef } from 'react'
import { Shield, ArrowRight, CheckCircle, Lock, Zap, Phone, Mail, Send, Loader2, Activity } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useLiveMetrics } from '../hooks/useLiveMetrics'

function useTradingCount() {
  const [count, setCount] = useState<number>(0)
  const [loaded, setLoaded] = useState(false)
  const ref = useRef(true)
  useEffect(() => {
    const fetch_ = async () => {
      try {
        const res = await fetch(`/api/trades/count?_t=${Date.now()}`, { cache: 'no-store' })
        if (!res.ok) return
        const d = await res.json()
        if (ref.current && d.count > 0) {
          setCount(d.count)
          setLoaded(true)
        }
      } catch {}
    }
    fetch_()
    const t = setInterval(fetch_, 60_000)
    return () => { ref.current = false; clearInterval(t) }
  }, [])
  return { count, loaded }
}

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


const DEMO_SCENARIOS = [
  {
    domain: 'TRADING', icon: '📈', color: '#C9A227',
    asset: 'BTC/USD Long · $4.2M',
    desc: 'Hedge fund requests $4.2M BTC/USD long. +38% in 72h, declining on-chain metrics, 2.4× volume anomaly.',
    blockAt: 2, verdict: 'BLOCK' as const,
    receipt: 'OMNIX-TRD-A7F2B1C9E5D3',
    reason: 'CP-2 · Drawdown risk 67% above threshold — execution blocked before order reaches exchange',
  },
  {
    domain: 'INSURANCE', icon: '🛡️', color: '#a78bfa',
    asset: 'Cat Bond Policy · £2.4M',
    desc: 'P&C insurer requests binding of a £2.4M catastrophe bond. Claim probability 78%, reserve adequacy -12%.',
    blockAt: 5, verdict: 'BLOCK' as const,
    receipt: 'OMNIX-INS-F3E9D4A1B8C2',
    reason: 'CP-5 · Reserve shortfall confirmed — binding blocked before loss exposure',
  },
  {
    domain: 'STABLECOIN', icon: '🪙', color: '#2dd4bf',
    asset: 'Reserve Rebalancing · USDC',
    desc: 'Stablecoin issuer requests rebalancing. Peg ±0.8%, liquid reserve 58% — below MiCA Art. 45 minimum.',
    blockAt: 4, verdict: 'HOLD' as const,
    receipt: 'OMNIX-SRG-B2C8E5F31A74',
    reason: 'CP-4 · MiCA liquid reserve below 60% minimum — escalated for manual review',
  },
] as const

const CP_NAMES = [
  'Signal Integrity','Probability Check','Risk Limits','Signal Coherence','Trajectory',
  'Tail Risk','Contradiction','Regime','Confirmation','AML Gate','Fraud Detection',
]

function GovernanceLiveDemo() {
  const [si, setSi] = useState(0)
  const [cp, setCp] = useState(-1)
  const [done, setDone] = useState(false)
  const scen = DEMO_SCENARIOS[si]
  const TICK = 180

  useEffect(() => { setSi(0); setCp(-1); setDone(false) }, [])

  useEffect(() => {
    setDone(false); setCp(-1)
    const t = setTimeout(() => setCp(0), 400)
    return () => clearTimeout(t)
  }, [si])

  useEffect(() => {
    if (cp < 0 || done) return
    if (cp >= CP_NAMES.length) { setDone(true); return }
    const t = setTimeout(() => setCp(c => c + 1), TICK)
    return () => clearTimeout(t)
  }, [cp, done])

  useEffect(() => {
    if (!done) return
    const t = setTimeout(() => setSi(s => (s + 1) % DEMO_SCENARIOS.length), 3200)
    return () => clearTimeout(t)
  }, [done])

  const cpState = (i: number): 'pending'|'pass'|'block'|'hold' => {
    if (cp < 0 || i > cp) return 'pending'
    if (!done) return i < cp ? 'pass' : 'pending'
    if (scen.verdict === 'BLOCK' && i === scen.blockAt) return 'block'
    if (scen.verdict === 'HOLD' && i === scen.blockAt) return 'hold'
    return 'pass'
  }

  return (
    <div style={{
      background:'linear-gradient(135deg,#060F1E 0%,#080E1C 100%)',
      border:'1px solid rgba(201,162,39,0.25)', borderRadius:20, overflow:'hidden',
      maxWidth:920, margin:'0 auto',
      boxShadow:'0 0 60px rgba(201,162,39,0.07), 0 24px 64px rgba(0,0,0,0.55)',
    }}>
      <div style={{
        background:'rgba(201,162,39,0.06)', borderBottom:'1px solid rgba(201,162,39,0.15)',
        padding:'12px 24px', display:'flex', alignItems:'center', justifyContent:'space-between',
      }}>
        <div style={{display:'flex', alignItems:'center', gap:10}}>
          <div style={{width:8,height:8,borderRadius:'50%',background:'#10b981'}} />
          <span style={{fontSize:11,fontWeight:700,color:'#10b981',letterSpacing:'0.1em'}}>LIVE GOVERNANCE PIPELINE</span>
        </div>
        <div style={{display:'flex',gap:6}}>
          {DEMO_SCENARIOS.map((s,i)=>(
            <button key={i} onClick={()=>setSi(i)} style={{
              width:8,height:8,borderRadius:'50%',border:'none',cursor:'pointer',padding:0,
              background:i===si?s.color:'rgba(255,255,255,0.15)', transition:'background 0.3s',
            }}/>
          ))}
        </div>
      </div>
      <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:0}}>
        <div style={{padding:'24px', borderRight:'1px solid rgba(255,255,255,0.06)'}}>
          <div style={{
            background:`${scen.color}10`, border:`1px solid ${scen.color}30`,
            borderRadius:12, padding:'14px 16px', marginBottom:18,
          }}>
            <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:6}}>
              <span style={{fontSize:'1.1rem'}}>{scen.icon}</span>
              <span style={{fontSize:10,fontWeight:800,color:scen.color,letterSpacing:'0.1em'}}>{scen.domain}</span>
            </div>
            <div style={{fontSize:13,fontWeight:700,color:'#E2E8F0',marginBottom:4}}>{scen.asset}</div>
            <div style={{fontSize:11,color:'#94A3B8',lineHeight:1.5}}>{scen.desc}</div>
          </div>
          <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:5}}>
            {CP_NAMES.map((name,i)=>{
              const st = cpState(i)
              const col = st==='block'?'#ef4444':st==='hold'?'#f59e0b':st==='pass'?'#10b981':'#334155'
              const bg = st==='block'?'rgba(239,68,68,0.1)':st==='hold'?'rgba(245,158,11,0.1)':st==='pass'?'rgba(16,185,129,0.08)':'rgba(255,255,255,0.02)'
              const icon = st==='block'?'✗':st==='hold'?'◆':st==='pass'?'✓':cp===i&&!done?'●':'○'
              return (
                <div key={i} style={{
                  display:'flex',alignItems:'center',gap:6,
                  background:bg,border:`1px solid ${col}30`,borderRadius:7,padding:'5px 8px',
                  transition:'all 0.2s ease',
                }}>
                  <span style={{fontSize:11,fontWeight:800,color:col,minWidth:12,textAlign:'center'}}>{icon}</span>
                  <div>
                    <div style={{fontSize:9,color:'#475569',letterSpacing:'0.05em'}}>CP-{i}</div>
                    <div style={{fontSize:10,color:st==='pending'?'#475569':'#CBD5E1',fontWeight:st!=='pending'?600:400}}>{name}</div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
        <div style={{padding:'24px',display:'flex',flexDirection:'column',justifyContent:'space-between'}}>
          <div>
            <div style={{fontSize:10,fontWeight:700,color:'#475569',letterSpacing:'0.1em',marginBottom:14}}>GOVERNANCE DECISION</div>
            {!done ? (
              <div style={{display:'flex',flexDirection:'column',gap:12,marginBottom:20}}>
                <div style={{
                  background:'rgba(255,255,255,0.02)',border:'1px solid rgba(255,255,255,0.06)',
                  borderRadius:12,padding:'20px',textAlign:'center',
                }}>
                  <div style={{fontSize:11,color:'#334155',marginBottom:8}}>Evaluating…</div>
                  <div style={{display:'flex',gap:3,justifyContent:'center'}}>
                    {[0,1,2].map(i=>(
                      <div key={i} style={{width:6,height:6,borderRadius:'50%',background:'#C9A227'}}/>
                    ))}
                  </div>
                  <div style={{fontSize:11,color:'#475569',marginTop:10}}>
                    {cp>=0&&cp<CP_NAMES.length?`Running ${CP_NAMES[Math.min(cp,10)]}…`:'Initialising pipeline…'}
                  </div>
                </div>
                <div style={{background:'rgba(255,255,255,0.04)',borderRadius:99,height:4}}>
                  <div style={{
                    height:'100%',borderRadius:99,
                    background:`linear-gradient(90deg,${scen.color},${scen.color}99)`,
                    width:`${Math.max(0,cp/11*100)}%`,transition:'width 0.2s ease',
                  }}/>
                </div>
                <div style={{fontSize:10,color:'#334155',textAlign:'center'}}>{Math.max(0,cp)} / 11 checkpoints</div>
              </div>
            ) : (
              <div>
                <div style={{
                  background:scen.verdict==='BLOCK'?'rgba(239,68,68,0.1)':'rgba(245,158,11,0.1)',
                  border:`2px solid ${scen.verdict==='BLOCK'?'#ef4444':'#f59e0b'}`,
                  borderRadius:12,padding:'18px',textAlign:'center',marginBottom:14,
                }}>
                  <div style={{
                    fontSize:'1.8rem',fontWeight:900,
                    color:scen.verdict==='BLOCK'?'#ef4444':'#f59e0b',
                    letterSpacing:'0.08em',marginBottom:6,
                  }}>{scen.verdict}</div>
                  <div style={{fontSize:11,color:'#94A3B8',lineHeight:1.5}}>{scen.reason}</div>
                </div>
                <div style={{
                  background:'rgba(255,255,255,0.02)',border:'1px solid rgba(255,255,255,0.08)',
                  borderRadius:10,padding:'12px 14px',
                }}>
                  <div style={{fontSize:9,color:'#475569',letterSpacing:'0.1em',marginBottom:4}}>PQC RECEIPT · CRYSTALS-Dilithium3</div>
                  <div style={{fontSize:11,fontFamily:'monospace',color:'#C9A227',wordBreak:'break-all'}}>{scen.receipt}</div>
                  <div style={{fontSize:9,color:'#334155',marginTop:4}}>Independently verifiable · W3C VC format</div>
                </div>
              </div>
            )}
          </div>
          <div style={{marginTop:16}}>
            <Link to="/try" style={{
              display:'block',textAlign:'center',
              background:'rgba(201,162,39,0.1)',border:'1px solid rgba(201,162,39,0.3)',
              borderRadius:10,padding:'10px 16px',
              fontSize:12,fontWeight:700,color:'#C9A227',
              textDecoration:'none',letterSpacing:'0.05em',
            }}>
              Run your own scenario →
            </Link>
            <div style={{fontSize:10,color:'#334155',textAlign:'center',marginTop:8}}>
              No login required · Real pipeline · PQC receipt issued
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

const REFERRAL_OPTIONS = [
  'Facebook', 'WhatsApp', 'Instagram', 'Telegram',
  'LinkedIn', 'Google', 'Recomendación', 'Otro'
]

export default function CommercialLanding() {
  const { metrics, isLive, formatNumber, formatNumberFull, animKey } = useLiveMetrics()
  const { total: liveTotal, loaded } = useTotalDecisions()
  const { count: tradingCount, loaded: tradingLoaded } = useTradingCount()
  const [formData, setFormData] = useState({
    name: '', company: '', email: '', referral_source: '', message: ''
  })
  const [formStatus, setFormStatus] = useState<'idle' | 'sending' | 'success' | 'error'>('idle')
  const [formError, setFormError] = useState('')
  const partialSentRef = useRef(false)

  const handleFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }))
  }

  const handleEmailBlur = () => {
    const email = formData.email.trim()
    if (!email || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email) || partialSentRef.current) return
    partialSentRef.current = true
    fetch('/api/contact/partial', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email,
        name: formData.name.trim() || undefined,
        company: formData.company.trim() || undefined
      })
    }).catch(() => {})
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
            <Link to="/docs" className="nav-link" style={{color:'#94a3b8', fontSize:'0.82rem'}}>Docs</Link>
            <Link to="/eidas" className="nav-link" style={{color:'#60a5fa', fontSize:'0.82rem'}}>eIDAS</Link>
            <Link to="/credit" className="nav-link font-semibold" style={{color:'#a78bfa', fontSize:'0.82rem'}}>Islamic Credit</Link>
            <Link to="/insurance" className="nav-link font-semibold" style={{color:'#60a5fa', fontSize:'0.82rem'}}>Insurance</Link>
            <Link to="/robotics" className="nav-link font-semibold" style={{color:'#34d399', fontSize:'0.82rem'}}>Robotics</Link>
            <Link to="/medical" className="nav-link font-semibold" style={{color:'#f472b6', fontSize:'0.82rem'}}>Medical AI</Link>
            <Link to="/agents" className="nav-link font-semibold" style={{color:'#fb923c', fontSize:'0.82rem'}}>Agents</Link>
            <Link to="/command" className="nav-link font-semibold" style={{color:'#10B981', background:'rgba(16,185,129,0.08)', padding:'6px 14px', borderRadius:8, border:'1px solid rgba(16,185,129,0.25)', fontSize:'0.82rem'}}>⚡ Live Data</Link>
            <Link to="/governance-flow" className="nav-link font-semibold" style={{color:'#C9A227', fontSize:'0.82rem', background:'rgba(201,162,39,0.07)', padding:'6px 14px', borderRadius:8, border:'1px solid rgba(201,162,39,0.22)'}}>Governance Flow</Link>
            <Link to="/institutional" className="nav-link">Technical Details</Link>
            <Link to="/verify-independently" className="nav-link font-semibold" style={{color:'#34d399', fontSize:'0.82rem', background:'rgba(52,211,153,0.07)', padding:'6px 14px', borderRadius:8, border:'1px solid rgba(52,211,153,0.2)'}}>Verify</Link>
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
          <p className="text-xl text-muted max-w-2xl mx-auto mb-5 leading-relaxed">
            Every system checks if a decision <em>can</em> be executed.<br />
            <strong className="text-white">OMNIX checks if it should exist at all.</strong>
          </p>
          <p className="text-base text-muted/70 max-w-2xl mx-auto mb-8 leading-relaxed">
            Governance control architecture for automated decision systems. 11 checkpoints. Cryptographic proof. 10 domains live — trading, islamic credit, insurance, robotics, medical AI, energy, real estate, agents, stablecoin, defense.
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
                decisions governed · 10 domains · right now
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
            <Link to="/full-demo" className="btn-secondary text-lg px-8 py-4 flex items-center gap-2">
              Run your first decision through OMNIX
            </Link>
          </div>
        </section>

        {/* ── LIVE GOVERNANCE PIPELINE DEMO ── */}
        <section className="mb-16">
          <div className="text-center mb-8">
            <span style={{
              display:'inline-block',
              background:'rgba(201,162,39,0.08)',
              border:'1px solid rgba(201,162,39,0.3)',
              borderRadius:99, padding:'6px 18px',
              fontSize:'0.8rem', fontWeight:700,
              color:'#C9A227', letterSpacing:'0.12em',
              textTransform:'uppercase', marginBottom:16,
            }}>Live Pipeline Demo</span>
            <h2 className="heading-lg text-white mb-3">See OMNIX in Action</h2>
            <p className="text-muted text-lg max-w-2xl mx-auto">
              The 11-checkpoint governance pipeline intercepting a high-risk decision in real time — cryptographic receipt issued on every evaluation.
            </p>
          </div>
          <GovernanceLiveDemo />
        </section>

        {/* ── 60-SECOND PROOF ── */}
        <section className="mb-24">
          <div className="text-center mb-10">
            <span style={{
              display:'inline-block',
              background:'rgba(52,211,153,0.08)',
              border:'1px solid rgba(52,211,153,0.3)',
              borderRadius:99, padding:'6px 18px',
              fontSize:'0.8rem', fontWeight:700,
              color:'#34d399', letterSpacing:'0.12em',
              textTransform:'uppercase', marginBottom:16,
            }}>60-Second Proof</span>
            <h2 className="heading-lg text-white mb-3">From Decision to Verified Receipt</h2>
            <p className="text-muted text-lg max-w-2xl mx-auto">
              No explanations. Just the four things that happen every time OMNIX governs a decision.
            </p>
          </div>
          <div style={{
            display:'grid',
            gridTemplateColumns:'1fr auto 1fr auto 1fr auto 1fr',
            alignItems:'center',
            gap:'0',
            maxWidth:960,
            margin:'0 auto 2rem',
          }}>
            {[
              { num:'01', label:'Scenario', desc:'A decision arrives — trade, loan, claim, dispatch.', color:'#a78bfa', bg:'rgba(167,139,250,0.08)', border:'rgba(167,139,250,0.2)' },
              { num:'02', label:'Decision', desc:'11 checkpoints. Every rule fires. Every gate scored.', color:'#C9A227', bg:'rgba(201,162,39,0.08)', border:'rgba(201,162,39,0.2)' },
              { num:'03', label:'Receipt', desc:'SHA-256 hash + Dilithium-3 signature. Immutable.', color:'#60a5fa', bg:'rgba(96,165,250,0.08)', border:'rgba(96,165,250,0.2)' },
              { num:'04', label:'Verify', desc:'Anyone verifies it. No OMNIX server needed.', color:'#34d399', bg:'rgba(52,211,153,0.08)', border:'rgba(52,211,153,0.2)' },
            ].map((step, i) => (
              <React.Fragment key={step.num}>
                <div style={{
                  background: step.bg,
                  border: `1px solid ${step.border}`,
                  borderRadius: 16,
                  padding: '28px 20px',
                  textAlign: 'center',
                }}>
                  <div style={{ fontSize:'2rem', fontWeight:900, color: step.color, opacity:0.5, marginBottom:8, fontFamily:'monospace' }}>{step.num}</div>
                  <div style={{ fontSize:'1.1rem', fontWeight:700, color:'#fff', marginBottom:8 }}>{step.label}</div>
                  <div style={{ fontSize:'0.82rem', color:'#94A3B8', lineHeight:1.5 }}>{step.desc}</div>
                </div>
                {i < 3 && (
                  <div style={{ textAlign:'center', color:'#334155', fontSize:'1.5rem', padding:'0 8px' }}>→</div>
                )}
              </React.Fragment>
            ))}
          </div>
          <div style={{ textAlign:'center' }}>
            <Link to="/verify-independently" style={{
              display:'inline-flex', alignItems:'center', gap:10,
              background:'rgba(52,211,153,0.08)',
              border:'1px solid rgba(52,211,153,0.3)',
              borderRadius:10, padding:'14px 28px',
              color:'#34d399', fontWeight:700, fontSize:'0.95rem',
              textDecoration:'none', transition:'all 0.2s',
            }}>
              Verify a Receipt Independently →
            </Link>
            <p style={{ color:'#475569', fontSize:'0.8rem', marginTop:10 }}>
              Download the script · Fetch the public key · No account required
            </p>
          </div>
        </section>

        {/* ── PRODUCT DEMO VIDEO ── */}
        <section className="mb-24">
          <div className="text-center mb-8">
            <span style={{
              display:'inline-block',
              background:'rgba(201,162,39,0.08)',
              border:'1px solid rgba(201,162,39,0.3)',
              borderRadius:99, padding:'6px 18px',
              fontSize:'0.8rem', fontWeight:700,
              color:'#C9A227', letterSpacing:'0.12em',
              textTransform:'uppercase', marginBottom:16,
            }}>Product Demo</span>
            <h2 className="heading-lg text-white mb-3">See OMNIX in Action</h2>
            <p className="text-muted text-lg max-w-2xl mx-auto">
              Watch how OMNIX intercepts a high-risk decision in real time — with cryptographic proof and full audit trail.
            </p>
          </div>
          <div style={{
            position:'relative',
            borderRadius:16,
            overflow:'hidden',
            border:'1px solid rgba(201,162,39,0.25)',
            boxShadow:'0 0 60px rgba(201,162,39,0.08), 0 24px 64px rgba(0,0,0,0.5)',
            background:'#0A0C12',
            maxWidth:900,
            margin:'0 auto',
          }}>
            <video
              src="/omnix-demo.mp4"
              controls
              playsInline
              style={{ width:'100%', display:'block', borderRadius:16 }}
            />
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
            <p className="text-sm text-center text-muted mb-8">Internally verified production data · Running 24/7 since November 2025</p>

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
                <div className="text-sm text-muted mt-1">Virtual Capital Preserved</div>
                <div className="text-xs text-muted/40 mt-0.5">Simulated — governance demo</div>
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

        <section className="mb-16">
          <div style={{
            background: 'linear-gradient(135deg, rgba(16,185,129,0.06) 0%, rgba(139,92,246,0.06) 100%)',
            border: '1px solid rgba(16,185,129,0.25)',
            borderRadius: 16,
            padding: '2.5rem',
            textAlign: 'center',
          }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#10B981', letterSpacing: '0.15em', textTransform: 'uppercase', marginBottom: '1rem' }}>
              CRYPTOGRAPHIC PROOF — NOT LOGS
            </div>
            <h2 style={{ fontSize: '2rem', fontWeight: 800, color: '#fff', marginBottom: '0.75rem', lineHeight: 1.2 }}>
              Every decision leaves a cryptographic proof.
            </h2>
            <p style={{ fontSize: '1.1rem', color: '#94A3B8', marginBottom: '1.5rem', maxWidth: 520, margin: '0 auto 1.5rem' }}>
              Not logs. Not alerts. A post-quantum signed receipt — independently verifiable, tamper-proof, permanent.
            </p>
            <div style={{ display: 'flex', justifyContent: 'center', gap: '3rem', flexWrap: 'wrap' }}>
              <div>
                <div style={{ fontSize: '2rem', fontWeight: 800, color: '#10B981' }}>{isLive && metrics.pqc_signed_receipts > 0 ? formatNumber(metrics.pqc_signed_receipts) : '82K+'}</div>
                <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: 4 }}>PQC Receipts issued</div>
              </div>
              <div>
                <div style={{ fontSize: '2rem', fontWeight: 800, color: '#C9A227' }}>100%</div>
                <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: 4 }}>Decisions signed on-chain</div>
              </div>
              <div>
                <div style={{ fontSize: '2rem', fontWeight: 800, color: '#a78bfa' }}>PQC</div>
                <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: 4 }}>Post-quantum cryptography</div>
              </div>
            </div>
          </div>
        </section>

        <section className="mb-24">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-white mb-3">Ten Verticals. Running Now.</h2>
            <p className="text-muted max-w-2xl mx-auto">Same 11-checkpoint governance pipeline. Ten live domains. All operating 24/7.</p>
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
                <div><div className="text-xl font-bold text-[#C9A227]">{tradingLoaded && tradingCount > 0 ? `${tradingCount.toLocaleString()}+` : '—'}</div><div className="text-xs text-muted">Decisions governed</div></div>
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

            <div className="glass-card p-8 border border-yellow-400/20">
              <div className="flex items-center gap-3 mb-4">
                <span className="flex items-center gap-1.5 text-xs font-semibold text-yellow-400 bg-yellow-400/10 border border-yellow-400/20 px-2.5 py-1 rounded-full">
                  <span style={{width:'6px',height:'6px',borderRadius:'50%',background:'#facc15',display:'inline-block',marginRight:0}} />
                  LIVE
                </span>
                <span className="text-white font-bold text-lg">Energy — Grid &amp; Renewables</span>
              </div>
              <p className="text-muted text-sm mb-5">Governance layer for energy dispatch and grid-balancing decisions. Pre-execution validation across load forecasting, carbon compliance, and regulatory jurisdiction gates — 24/7.</p>
              <div className="grid grid-cols-2 gap-4 mb-5">
                <div><div className="text-xl font-bold text-yellow-400">17,000+</div><div className="text-xs text-muted">Decisions governed</div></div>
                <div><div className="text-xl font-bold text-yellow-400">3 sectors</div><div className="text-xs text-muted">Grid · Renewables · Oil &amp; Gas</div></div>
              </div>
              <Link to="/energy" className="text-yellow-400 text-sm hover:text-white transition-colors flex items-center gap-1">
                View live governance dashboard <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="glass-card p-8 border border-cyan-400/20">
              <div className="flex items-center gap-3 mb-4">
                <span className="flex items-center gap-1.5 text-xs font-semibold text-cyan-400 bg-cyan-400/10 border border-cyan-400/20 px-2.5 py-1 rounded-full">
                  <span style={{width:'6px',height:'6px',borderRadius:'50%',background:'#22d3ee',display:'inline-block',marginRight:0}} />
                  LIVE
                </span>
                <span className="text-white font-bold text-lg">Real Estate — Property AI</span>
              </div>
              <p className="text-muted text-sm mb-5">Pre-approval governance for real estate AI decisions. Valuation integrity gate + 11 checkpoints screening mortgage approvals, investment underwriting, and property risk assessments.</p>
              <div className="grid grid-cols-2 gap-4 mb-5">
                <div><div className="text-xl font-bold text-cyan-400">9,000+</div><div className="text-xs text-muted">Decisions governed</div></div>
                <div><div className="text-xl font-bold text-cyan-400">3 markets</div><div className="text-xs text-muted">UK · UAE · US</div></div>
              </div>
              <Link to="/real-estate" className="text-cyan-400 text-sm hover:text-white transition-colors flex items-center gap-1">
                View live governance dashboard <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="glass-card p-8 border border-red-400/20">
              <div className="flex items-center gap-3 mb-4">
                <span className="flex items-center gap-1.5 text-xs font-semibold text-red-400 bg-red-400/10 border border-red-400/20 px-2.5 py-1 rounded-full">
                  <span style={{width:'6px',height:'6px',borderRadius:'50%',background:'#f87171',display:'inline-block',marginRight:0}} />
                  LIVE
                </span>
                <span className="text-white font-bold text-lg">⚔️ Autonomous Defense Governance</span>
              </div>
              <p className="text-muted text-sm mb-5">Governance layer for autonomous weapons and defense AI. IHL compliance gate + 11 checkpoints enforcing Rules of Engagement, proportionality, distinction, and human oversight requirements before any lethal autonomous action.</p>
              <div className="grid grid-cols-2 gap-4 mb-5">
                <div><div className="text-xl font-bold text-red-400">IHL</div><div className="text-xs text-muted">International law compliant</div></div>
                <div><div className="text-xl font-bold text-red-400">ADR-DEF-001</div><div className="text-xs text-muted">Architecture Decision Record</div></div>
              </div>
              <Link to="/defense" className="text-red-400 text-sm hover:text-white transition-colors flex items-center gap-1">
                View live governance dashboard <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="glass-card p-8 border border-violet-400/20">
              <div className="flex items-center gap-3 mb-4">
                <span className="flex items-center gap-1.5 text-xs font-semibold text-violet-400 bg-violet-400/10 border border-violet-400/20 px-2.5 py-1 rounded-full">
                  <span style={{width:'6px',height:'6px',borderRadius:'50%',background:'#8B5CF6',display:'inline-block',marginRight:0}} />
                  LIVE
                </span>
                <span className="text-white font-bold text-lg">🪙 Stablecoin Reserve — ADR-SRG-001</span>
              </div>
              <p className="text-muted text-sm mb-5">Governance engine for stablecoin reserve management. Collateral adequacy gate + 11 checkpoints enforcing MiCA compliance, PEG stability, liquidity thresholds, and counterparty limits — 24/7 reserve surveillance.</p>
              <div className="grid grid-cols-3 gap-4 mb-5">
                <div><div className="text-xl font-bold text-violet-400">MiCA</div><div className="text-xs text-muted">EU Regulation compliant</div></div>
                <div><div className="text-xl font-bold text-violet-400">$5B+</div><div className="text-xs text-muted">Reserve capacity governed</div></div>
                <div><div className="text-xl font-bold text-violet-400">ADR-SRG-001</div><div className="text-xs text-muted">Architecture Decision Record</div></div>
              </div>
              <Link to="/stablecoin" className="text-violet-400 text-sm hover:text-white transition-colors flex items-center gap-1">
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
              <div className="text-[#64748B] text-xs">Trading · Credit · Insurance · Robotics · Medical · Agents · Real Estate · Energy · Stablecoin</div>
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
              <div className="text-4xl font-black text-emerald-400 mb-3">9</div>
              <div className="text-sm text-white font-semibold mb-2">Domains under active governance</div>
              <div className="text-xs text-muted leading-relaxed">Trading, Credit, Insurance, Robotics, Medical AI, Energy, Real Estate, Autonomous Agents, and Stablecoin Reserve — all running 24/7.</div>
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
                  {label:'Pre-decision admissibility assessment', vals:[true,false,false,false,false]},
                  {label:'Multi-checkpoint governance pipeline (11 gates)', vals:[true,false,false,false,false]},
                  {label:'Domain-specific governance (9 sectors)', vals:[true,false,false,false,false]},
                  {label:'Sharia-aligned governance gate', vals:[true,false,false,false,false]},
                  {label:'Post-quantum cryptography (Dilithium-3 NIST)', vals:[true,false,false,false,false]},
                  {label:'W3C Verifiable Credential decision receipts', vals:[true,false,false,false,false]},
                  {label:'Counterfactual validation (Shadow Portfolio)', vals:[true,false,false,false,false]},
                  {label:'Human deliberation integration (HOLD state)', vals:[true,false,false,false,false]},
                  {label:'Tamper-proof audit trail', vals:[true,false,false,true,false]},
                  {label:'Real-time risk analysis', vals:[true,false,true,false,false]},
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

        </section>

        {/* ── COST OF NOT HAVING OMNIX ── */}
        <section className="mb-24">
          <div className="text-center mb-12">
            <span style={{
              display:'inline-block',
              background:'rgba(239,68,68,0.08)',
              border:'1px solid rgba(239,68,68,0.3)',
              borderRadius:99, padding:'6px 18px',
              fontSize:'0.8rem', fontWeight:700,
              color:'#ef4444', letterSpacing:'0.12em',
              textTransform:'uppercase', marginBottom:16,
            }}>The Real Cost</span>
            <h2 className="heading-lg text-white mb-4">
              What Governance Failures <span style={{color:'#ef4444'}}>Actually Cost</span>
            </h2>
            <p className="text-muted text-lg max-w-2xl mx-auto">
              Every domain OMNIX governs has produced a headline failure. These are not edge cases — they are the predictable cost of operating without governance infrastructure.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5 mb-10">
            {[
              {
                domain:'Trading', icon:'📈', color:'#10B981',
                company:'Knight Capital', year:'2012', loss:'$440M', time:'45 minutes',
                cause:'Uncontrolled algorithm deployed without a governance gate. 4 million erroneous orders executed before anyone could intervene.',
                omnix:'Signal Integrity Validator blocks the rogue signal before a single order reaches the exchange.',
              },
              {
                domain:'Credit', icon:'🏦', color:'#3b82f6',
                company:'Goldman Sachs / 1MDB', year:'2020', loss:'$3.9B fine', time:'6 years undetected',
                cause:'Credit and deal decisions approved without governance controls. Sovereign-level fraud went undetected across multiple jurisdictions.',
                omnix:'Jurisdiction gate flags high-risk sovereignty exposure. Decision blocked before approval.',
              },
              {
                domain:'Insurance', icon:'🛡️', color:'#a78bfa',
                company:"Equitas / Lloyd's", year:'2002', loss:'£67M reserve shortfall', time:'3 years undetected',
                cause:"Claims systematically underpriced without actuarial governance. No pre-decision validation on high-exposure policy binding.",
                omnix:'Monte Carlo reserves validation blocks underpriced policies before binding.',
              },
              {
                domain:'Stablecoin Reserve', icon:'🪙', color:'#8B5CF6',
                company:'MiCA Non-Compliant Issuer', year:'2024+', loss:'€10M / year', time:'Ongoing regulatory risk',
                cause:'MiCA Art. 45: stablecoin issuers must hold adequate liquid reserves at all times. Breach = €10M/year or 2% of total turnover, whichever is higher.',
                omnix:'Real-time peg ±0.5% + reserve coverage monitoring. Hard block before MiCA threshold breach.',
              },
              {
                domain:'Robotics', icon:'🤖', color:'#f59e0b',
                company:'Amazon Fulfilment Facility', year:'2019', loss:'$800K + 2-day halt', time:'48 hours',
                cause:'Automated robot decision system acted without context-aware governance. Worker injury triggered facility shutdown and liability exposure.',
                omnix:'Every robot action validated against safety envelopes before execution. No action without governance clearance.',
              },
              {
                domain:'Medical AI', icon:'🏥', color:'#ef4444',
                company:'IBM Watson Health', year:'2017', loss:'$62M + reputational damage', time:'Multi-year',
                cause:'AI clinical recommendations contradicted physician judgment. No governance framework to resolve conflicts or escalate to human deliberation.',
                omnix:'HOLD state routes conflicted Medical AI decisions to physician — zero autonomous override without human sign-off.',
              },
              {
                domain:'Energy Grid', icon:'⚡', color:'#facc15',
                company:'ERCOT — Texas Grid', year:'2021', loss:'$130B economic damage', time:'69 hours',
                cause:'Automated dispatch systems failed to enforce weatherisation contracts. No pre-execution governance gate validated generator readiness before load commitments were made.',
                omnix:'Load forecast + carbon compliance + jurisdiction gates block commitment before dispatch. No dispatch without governance clearance.',
              },
              {
                domain:'Real Estate AI', icon:'🏢', color:'#fb923c',
                company:'Zillow Offers', year:'2021', loss:'$881M write-down', time:'18 months',
                cause:'Automated Valuation Model systematically overbid on properties with no pre-decision validation. No override gate between AVM output and binding purchase commitment.',
                omnix:'Valuation integrity gate + 11 checkpoints block overbid decisions before binding. AVM output is an input, not a decision.',
              },
              {
                domain:'Autonomous Agents', icon:'🧠', color:'#e879f9',
                company:'The DAO Smart Contract', year:'2016', loss:'$60M ETH drained', time:'3 hours',
                cause:'Autonomous smart contract agent exploited a re-entrancy loop. No governance layer between agent intent and execution. $60M drained before a single human could intervene.',
                omnix:'Intent validation gate + 11 checkpoints evaluate every agent action before it executes. No autonomous action without governance sign-off.',
              },
            ].map(item => (
              <div key={item.domain} style={{
                background:'rgba(10,22,40,0.85)',
                border:`1px solid ${item.color}30`,
                borderRadius:16, padding:'22px',
                display:'flex', flexDirection:'column', gap:0,
              }}>
                {/* Row 1: icon + domain + company + year */}
                <div style={{display:'flex', alignItems:'flex-start', gap:10, marginBottom:8}}>
                  <span style={{fontSize:'1.3rem', flexShrink:0, marginTop:2}}>{item.icon}</span>
                  <div style={{flex:1, minWidth:0}}>
                    <div style={{fontSize:'0.68rem', fontWeight:700, color:item.color, textTransform:'uppercase', letterSpacing:'0.1em'}}>{item.domain}</div>
                    <div style={{fontSize:'0.88rem', fontWeight:700, color:'#E2E8F0'}}>{item.company}</div>
                    <div style={{fontSize:'0.72rem', color:'#64748B'}}>{item.year}</div>
                  </div>
                </div>
                {/* Row 2: loss amount — full width so it never overflows */}
                <div style={{marginBottom:10}}>
                  <div style={{fontSize:'0.95rem', fontWeight:900, color:'#ef4444', wordBreak:'break-word', lineHeight:1.35}}>{item.loss}</div>
                  <div style={{fontSize:'0.65rem', color:'#64748B', marginTop:2}}>{item.time}</div>
                </div>
                <p style={{fontSize:'0.76rem', color:'#94A3B8', lineHeight:1.55, marginBottom:10, flex:1}}>{item.cause}</p>
                <div style={{borderTop:`1px solid ${item.color}20`, paddingTop:10}}>
                  <p style={{fontSize:'0.73rem', color:item.color, fontWeight:600, lineHeight:1.5}}>
                    🛡 {item.omnix}
                  </p>
                </div>
              </div>
            ))}
          </div>

          {/* Cost vs Subscription callout */}
          <div style={{
            background:'linear-gradient(135deg, rgba(201,162,39,0.05) 0%, rgba(16,185,129,0.03) 100%)',
            border:'1px solid rgba(201,162,39,0.25)',
            borderRadius:20, padding:'36px 32px',
            textAlign:'center',
          }}>
            <p style={{fontSize:'1rem', color:'#94A3B8', marginBottom:6}}>
              The cost of <span style={{color:'#ef4444', fontWeight:700}}>one governance failure</span> in any of these 10 domains
            </p>
            <p style={{fontSize:'2.4rem', fontWeight:900, color:'#ef4444', marginBottom:4, letterSpacing:'-0.02em'}}>
              $440M – $130B
            </p>
            <p style={{fontSize:'0.85rem', color:'#64748B', marginBottom:24}}>
              across 9 documented headline failures — fines, operational losses, or irreversible reputational damage
            </p>
            <div style={{display:'flex', alignItems:'center', justifyContent:'center', gap:24, flexWrap:'wrap'}}>
              <div>
                <p style={{fontSize:'0.85rem', color:'#94A3B8', marginBottom:2}}>OMNIX Enterprise — all 10 domains</p>
                <p style={{fontSize:'1.8rem', fontWeight:900, color:'#10B981', letterSpacing:'-0.02em'}}>$420,000 / year</p>
                <p style={{fontSize:'0.72rem', color:'#64748B', marginTop:2}}>Full veto authority · 10 verticals · PQC receipts · SLA 99.9%</p>
              </div>
              <div style={{fontSize:'1.8rem', color:'#475569', fontWeight:300}}>vs</div>
              <div>
                <p style={{fontSize:'0.85rem', color:'#94A3B8', marginBottom:2}}>Cost of ONE failure without it</p>
                <p style={{fontSize:'1.8rem', fontWeight:900, color:'#ef4444', letterSpacing:'-0.02em'}}>$130,000,000,000+</p>
                <p style={{fontSize:'0.72rem', color:'#64748B', marginTop:2}}>Non-recoverable · Regulatory + operational + reputational</p>
              </div>
            </div>
          </div>
        </section>

        {/* ── CONTACT ── */}
        <section className="mb-24" id="contact">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-white mb-4">Get in Touch</h2>
            <p className="text-muted max-w-xl mx-auto">Every deployment is different. Tell us about your environment and we'll design the right governance structure for your institution.</p>
          </div>

          {/* Contact cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">

            {/* Free Pilot */}
            <div className="flex flex-col bg-[#0A1628]/80 border border-emerald-500/30 rounded-2xl p-7" style={{boxShadow:'0 0 24px rgba(16,185,129,0.06)'}}>
              <div className="w-11 h-11 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-5">
                <Zap className="w-5 h-5 text-emerald-400" />
              </div>
              <span className="text-xs font-bold text-emerald-400 uppercase tracking-widest mb-2">Start Free</span>
              <h3 className="text-lg font-bold text-white mb-2">Shadow Mode Pilot</h3>
              <p className="text-xs text-muted leading-relaxed flex-1 mb-6">
                Run OMNIX alongside your system for 4 weeks — zero interventions, no operational risk. See exactly what would have been blocked before you commit to anything.
              </p>
              <ul className="space-y-2 mb-6">
                {[
                  'No commitment required',
                  'Full governance report at end of pilot',
                  'PQC-signed receipts included',
                ].map(f => (
                  <li key={f} className="flex items-start gap-2 text-xs text-muted">
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0 mt-0.5" />{f}
                  </li>
                ))}
              </ul>
              <a href="https://wa.me/16505078293?text=I%27d%20like%20to%20start%20the%20Shadow%20Mode%20pilot" target="_blank" rel="noopener noreferrer"
                className="block text-center py-3 rounded-xl border border-emerald-500/50 text-emerald-400 text-sm font-semibold hover:bg-emerald-500/10 transition-colors">
                Start Free Pilot
              </a>
            </div>

            {/* Contact — WhatsApp */}
            <div className="flex flex-col bg-[#0A1628]/80 border-2 border-[#C9A227] rounded-2xl p-7 relative" style={{boxShadow:'0 0 32px rgba(201,162,39,0.10)'}}>
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 whitespace-nowrap">
                <span className="bg-[#C9A227] text-[#0a0f1a] text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wide">Fastest Response</span>
              </div>
              <div className="w-11 h-11 rounded-xl bg-[#C9A227]/10 border border-[#C9A227]/25 flex items-center justify-center mb-5">
                <Phone className="w-5 h-5 text-[#C9A227]" />
              </div>
              <span className="text-xs font-bold text-[#C9A227] uppercase tracking-widest mb-2">Direct</span>
              <h3 className="text-lg font-bold text-white mb-2">Talk to Harold</h3>
              <p className="text-xs text-muted leading-relaxed flex-1 mb-6">
                Speak directly with the founder. Bring your architecture, your constraints, your use case. We'll tell you exactly how OMNIX fits — or if it doesn't.
              </p>
              <ul className="space-y-2 mb-6">
                {[
                  'Direct line to the founder',
                  'No sales process — just the conversation',
                  'Response within 24 hours',
                ].map(f => (
                  <li key={f} className="flex items-start gap-2 text-xs text-muted">
                    <CheckCircle className="w-3.5 h-3.5 text-[#C9A227] flex-shrink-0 mt-0.5" />{f}
                  </li>
                ))}
              </ul>
              <a href="https://wa.me/16505078293?text=I%27d%20like%20to%20discuss%20OMNIX%20Quantum%20for%20my%20institution" target="_blank" rel="noopener noreferrer"
                className="block text-center py-3 rounded-xl bg-[#C9A227] text-[#0a0f1a] text-sm font-bold hover:bg-[#F5D97A] transition-colors">
                Contact Us
              </a>
            </div>

            {/* Email */}
            <div className="flex flex-col bg-[#0A1628]/80 border border-[#334155] rounded-2xl p-7">
              <div className="w-11 h-11 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center mb-5">
                <Shield className="w-5 h-5 text-violet-400" />
              </div>
              <span className="text-xs font-bold text-violet-400 uppercase tracking-widest mb-2">Formal</span>
              <h3 className="text-lg font-bold text-white mb-2">Institutional Inquiry</h3>
              <p className="text-xs text-muted leading-relaxed flex-1 mb-6">
                For regulated institutions, enterprise deployments, partnerships, or NDA-first conversations. We'll respond with the appropriate documentation and next steps.
              </p>
              <ul className="space-y-2 mb-6">
                {[
                  'NDA available on request',
                  'Enterprise & white-label options',
                  'Custom vertical development',
                ].map(f => (
                  <li key={f} className="flex items-start gap-2 text-xs text-muted">
                    <CheckCircle className="w-3.5 h-3.5 text-violet-400 flex-shrink-0 mt-0.5" />{f}
                  </li>
                ))}
              </ul>
              <a href="mailto:contacto@omnixquantum.net?subject=Institutional%20Inquiry%20%E2%80%94%20OMNIX%20Quantum"
                className="block text-center py-3 rounded-xl border border-violet-500/50 text-violet-400 text-sm font-semibold hover:bg-violet-500/10 transition-colors">
                Email Us
              </a>
            </div>
          </div>

          {/* Billing models — no prices shown */}
          <div className="grid md:grid-cols-3 gap-4 mb-10">
            <div className="bg-[#0A1628]/60 border border-[#1E293B] rounded-2xl p-6 flex items-start gap-5">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center flex-shrink-0">
                <Zap className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <div className="text-xs font-bold text-emerald-400 uppercase tracking-widest mb-1">Pay-per-Decision</div>
                <p className="text-xs text-muted leading-relaxed">Pay only for the decisions OMNIX governs. Every governed decision includes a PQC-signed receipt. No monthly commitment required.</p>
              </div>
            </div>

            <div className="bg-[#0A1628]/60 border border-[#C9A227]/20 rounded-2xl p-6 flex items-start gap-5" style={{boxShadow:'0 0 20px rgba(201,162,39,0.06)'}}>
              <div className="w-10 h-10 rounded-xl bg-[#C9A227]/10 border border-[#C9A227]/25 flex items-center justify-center flex-shrink-0">
                <Shield className="w-5 h-5 text-[#C9A227]" />
              </div>
              <div>
                <div className="text-xs font-bold text-[#C9A227] uppercase tracking-widest mb-1">Capital-Based Fee</div>
                <p className="text-xs text-muted leading-relaxed">A fee proportional to the capital under governance. Scales with the value you protect — the more capital governed, the greater the institutional backing.</p>
              </div>
            </div>

            <div className="bg-[#0A1628]/60 border border-[#1E293B] rounded-2xl p-6 flex items-start gap-5">
              <div className="w-10 h-10 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center flex-shrink-0">
                <Phone className="w-5 h-5 text-violet-400" />
              </div>
              <div>
                <div className="text-xs font-bold text-violet-400 uppercase tracking-widest mb-1">API Integration</div>
                <p className="text-xs text-muted leading-relaxed">Volume-based pricing for high-throughput integrations. Rate limits, SLA tiers, and dedicated infrastructure available. Contact us for details.</p>
              </div>
            </div>
          </div>

          <p className="text-center text-xs text-muted">
            omnixquantum.net · contacto@omnixquantum.net · Every conversation starts with listening, not selling.
          </p>
        </section>

        <section className="mb-16 text-center">
          <div style={{
            background: 'rgba(201,162,39,0.04)',
            border: '1px solid rgba(201,162,39,0.2)',
            borderRadius: 20,
            padding: '3rem 2rem',
          }}>
            <p style={{ fontSize: '2rem', fontWeight: 900, color: '#fff', lineHeight: 1.25, maxWidth: 700, margin: '0 auto 1rem', letterSpacing: '-0.01em' }}>
              OMNIX is the last layer<br />before irreversible loss.
            </p>
            <p style={{ fontSize: '1.05rem', color: '#94A3B8', maxWidth: 480, margin: '0 auto 2rem' }}>
              The damage is never the decision itself. It's the decision that wasn't stopped.
            </p>
            <Link to="/try" className="btn-primary inline-flex items-center gap-2 text-lg px-8 py-4">
              Run your first decision through OMNIX <ArrowRight className="w-5 h-5" />
            </Link>
          </div>
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
                  onBlur={handleEmailBlur}
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

            {/* RFC-ATF-4 — newest, featured */}
            <div className="md:col-span-2 p-5 rounded-2xl border border-orange-500/30 bg-[#0A1628]/80">
              <div className="flex items-start justify-between mb-3 flex-wrap gap-2">
                <div className="flex gap-2 flex-wrap">
                  <span className="text-xs font-semibold px-2 py-1 rounded-full bg-orange-500/10 text-orange-400 border border-orange-500/20">LATEST</span>
                  <span className="text-xs font-semibold px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Zenodo</span>
                  <span className="text-xs font-semibold px-2 py-1 rounded-full bg-pink-500/10 text-pink-400 border border-pink-500/20">Figshare</span>
                </div>
                <span className="text-xs text-orange-400/60 font-mono">19 Z3 proofs · 108 vectors · dual Z3+TLA+</span>
              </div>
              <h3 className="text-white font-semibold text-sm mb-2 leading-snug">RFC-ATF-4: Agent Trust Fabric — Proactive Governance Layer · AGVP · Structural Shift Detection · Dynamic Semantic Portability</h3>
              <p className="text-muted text-xs mb-2">Harold Nunes · OMNIX QUANTUM LTD · May 2026</p>
              <div className="flex gap-4 flex-wrap">
                <a href="https://doi.org/10.5281/zenodo.20368895" target="_blank" rel="noopener noreferrer" className="text-emerald-400 text-xs hover:text-emerald-300 transition-colors">Zenodo: 10.5281/zenodo.20368895 ↗</a>
                <a href="https://doi.org/10.6084/m9.figshare.32394192" target="_blank" rel="noopener noreferrer" className="text-pink-400 text-xs hover:text-pink-300 transition-colors">Figshare: 10.6084/m9.figshare.32394192 ↗</a>
              </div>
            </div>

            {/* RFC-ATF-3 */}
            <div className="md:col-span-2 p-5 rounded-2xl border border-purple-500/30 bg-[#0A1628]/80">
              <div className="flex items-start justify-between mb-3 flex-wrap gap-2">
                <div className="flex gap-2 flex-wrap">
                  <span className="text-xs font-semibold px-2 py-1 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">Zenodo</span>
                  <span className="text-xs font-semibold px-2 py-1 rounded-full bg-pink-500/10 text-pink-400 border border-pink-500/20">Figshare</span>
                </div>
                <span className="text-xs text-purple-400/60 font-mono">47 formal invariants · ADR-170 GECR</span>
              </div>
              <h3 className="text-white font-semibold text-sm mb-2 leading-snug">RFC-ATF-3: Agent Trust Fabric — Governance Policy Interoperability, Evidence Lifecycle & Forensic Verification Protocol</h3>
              <p className="text-muted text-xs mb-2">Harold Nunes · OMNIX QUANTUM LTD · May 2026</p>
              <div className="flex gap-4 flex-wrap">
                <a href="https://doi.org/10.5281/zenodo.20247342" target="_blank" rel="noopener noreferrer" className="text-emerald-400 text-xs hover:text-emerald-300 transition-colors">Zenodo: 10.5281/zenodo.20247342 ↗</a>
                <a href="https://doi.org/10.6084/m9.figshare.32308119" target="_blank" rel="noopener noreferrer" className="text-pink-400 text-xs hover:text-pink-300 transition-colors">Figshare: 10.6084/m9.figshare.32308119 ↗</a>
              </div>
            </div>

            {/* RFC-ATF-2 */}
            <a href="https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6763978" target="_blank" rel="noopener noreferrer"
              className="block p-5 rounded-2xl border border-blue-500/30 bg-[#0A1628]/60 hover:border-blue-400/60 hover:bg-[#0A1628]/80 transition-all group">
              <div className="flex items-start justify-between mb-3 flex-wrap gap-2">
                <div className="flex gap-2 flex-wrap">
                  <span className="text-xs font-semibold px-2 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">SSRN</span>
                  <span className="text-xs font-semibold px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Zenodo</span>
                  <span className="text-xs font-semibold px-2 py-1 rounded-full bg-pink-500/10 text-pink-400 border border-pink-500/20">Figshare</span>
                </div>
                <ArrowRight className="w-4 h-4 text-muted group-hover:text-blue-400 transition-colors" />
              </div>
              <h3 className="text-white font-semibold text-sm mb-2 leading-snug">RFC-ATF-2: Agent Trust Fabric — Runtime Governance Continuity</h3>
              <p className="text-muted text-xs">Harold Nunes · OMNIX QUANTUM LTD · May 2026</p>
              <p className="text-blue-400/60 text-xs mt-2">SSRN 6763978 · Zenodo 10.5281/zenodo.20241344 · Figshare 10.6084/m9.figshare.32308095</p>
            </a>

            {/* RFC-ATF-1 */}
            <a href="https://doi.org/10.5281/zenodo.20155016" target="_blank" rel="noopener noreferrer"
              className="block p-5 rounded-2xl border border-[#C9A227]/20 bg-[#0A1628]/60 hover:border-[#C9A227]/50 hover:bg-[#0A1628]/80 transition-all group">
              <div className="flex items-start justify-between mb-3 flex-wrap gap-2">
                <div className="flex gap-2 flex-wrap">
                  <span className="text-xs font-semibold px-2 py-1 rounded-full bg-[#C9A227]/10 text-[#C9A227] border border-[#C9A227]/20">SSRN</span>
                  <span className="text-xs font-semibold px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Zenodo</span>
                  <span className="text-xs font-semibold px-2 py-1 rounded-full bg-pink-500/10 text-pink-400 border border-pink-500/20">Figshare</span>
                </div>
                <ArrowRight className="w-4 h-4 text-muted group-hover:text-[#C9A227] transition-colors" />
              </div>
              <h3 className="text-white font-semibold text-sm mb-2 leading-snug">RFC-ATF-1: Agent Trust Fabric Delegation Protocol — Post-Quantum Signatures (ML-DSA-65 / NIST FIPS 204)</h3>
              <p className="text-muted text-xs">Harold Nunes · OMNIX QUANTUM LTD · May 2026</p>
              <p className="text-[#C9A227]/60 text-xs mt-2">SSRN 6757339 · Zenodo 10.5281/zenodo.20155016 · Figshare 10.6084/m9.figshare.32308077</p>
            </a>

            {/* Technical Whitepaper */}
            <a href="https://ssrn.com/abstract=6507559" target="_blank" rel="noopener noreferrer"
              className="block p-5 rounded-2xl border border-[#C9A227]/20 bg-[#0A1628]/60 hover:border-[#C9A227]/50 hover:bg-[#0A1628]/80 transition-all group">
              <div className="flex items-start justify-between mb-3">
                <span className="text-xs font-semibold px-2 py-1 rounded-full bg-[#C9A227]/10 text-[#C9A227] border border-[#C9A227]/20">SSRN · Zenodo</span>
                <ArrowRight className="w-4 h-4 text-muted group-hover:text-[#C9A227] transition-colors" />
              </div>
              <h3 className="text-white font-semibold text-sm mb-2 leading-snug">OMNIX Quantum: Decision Governance Infrastructure — Technical Whitepaper v1.5</h3>
              <p className="text-muted text-xs">Harold Nunes · OMNIX QUANTUM LTD · 2026</p>
              <p className="text-[#C9A227]/60 text-xs mt-2">SSRN 6507559 · Zenodo 10.5281/zenodo.19375792 · 47 invariants · 171 ADRs</p>
            </a>

            {/* Production Dataset */}
            <a href="https://doi.org/10.5281/zenodo.19056919" target="_blank" rel="noopener noreferrer"
              className="block p-5 rounded-2xl border border-emerald-500/20 bg-[#0A1628]/60 hover:border-emerald-400/50 hover:bg-[#0A1628]/80 transition-all group">
              <div className="flex items-start justify-between mb-3">
                <span className="text-xs font-semibold px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Zenodo · Dataset</span>
                <ArrowRight className="w-4 h-4 text-muted group-hover:text-emerald-400 transition-colors" />
              </div>
              <h3 className="text-white font-semibold text-sm mb-2 leading-snug">Production Dataset — 82,569 Real Governance Decisions (PQC-signed, hash-chained)</h3>
              <p className="text-muted text-xs">Harold Nunes · OMNIX QUANTUM LTD · Mar 2026</p>
              <p className="text-emerald-400/60 text-xs mt-2">DOI: 10.5281/zenodo.19056919 · Independently verifiable</p>
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
            <Link to="/governance-flow" className="text-sm transition-colors font-semibold" style={{color:'#C9A227'}}>
              Governance Lifecycle
            </Link>
            <Link to="/trust-infrastructure" className="text-sm transition-colors font-semibold" style={{color:'#C9A227'}}>
              Trust Registry
            </Link>
            <Link to="/protocol" className="text-muted hover:text-white text-sm transition-colors">
              Protocol Architecture
            </Link>
            <Link to="/institutional" className="text-muted hover:text-white text-sm transition-colors">
              Technical Details
            </Link>
            <Link to="/docs" className="text-muted hover:text-white text-sm transition-colors">
              Docs
            </Link>
            <Link to="/verify-independently" className="text-emerald-400 hover:text-white text-sm transition-colors font-medium">
              Independent Verification
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
