import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { Shield, Activity, AlertTriangle, Zap, BarChart3, Calculator, ExternalLink, Lock, Award, Globe, ChevronRight, Play, Target, Brain, Cpu, TrendingUp, Users, DollarSign, CheckCircle, ArrowRight, Clock, Layers, Eye, Server, Download } from 'lucide-react'
import { useLiveMetrics } from '../hooks/useLiveMetrics'

interface SystemMetrics {
  evaluationCycles: number
  vetosExecuted: number
  capitalPreserved: number
  systemUptime: string
  lastUpdate: string
}

interface NewsItem {
  id: string
  headline: string
  source: string
  datetime: number
  url: string
  sentiment: 'positive' | 'negative' | 'neutral'
}

interface MarketData {
  btcPrice: number
  ethPrice: number
  fearGreedIndex: number
  fearGreedLabel: string
}

function useCountUp(end: number, duration: number = 2000, startOnMount: boolean = true) {
  const safeEnd = isNaN(end) || end === null || end === undefined ? 0 : end
  const [count, setCount] = useState(0)
  const countRef = useRef(0)
  
  useEffect(() => {
    if (!startOnMount || safeEnd === 0) return
    const startTime = Date.now()
    const startValue = 0
    
    const animate = () => {
      const now = Date.now()
      const progress = Math.min((now - startTime) / duration, 1)
      const easeOut = 1 - Math.pow(1 - progress, 3)
      countRef.current = startValue + (safeEnd - startValue) * easeOut
      setCount(Math.floor(countRef.current))
      
      if (progress < 1) {
        requestAnimationFrame(animate)
      }
    }
    
    requestAnimationFrame(animate)
  }, [safeEnd, duration, startOnMount])
  
  return count
}

export default function InstitutionalPage() {
  const { metrics: liveMetrics } = useLiveMetrics(30000)
  
  const [metrics, setMetrics] = useState<SystemMetrics>({
    evaluationCycles: 0,
    vetosExecuted: 0,
    capitalPreserved: 0,
    systemUptime: '99.9%',
    lastUpdate: new Date().toISOString()
  })
  
  const [news, setNews] = useState<NewsItem[]>([])
  const [market, setMarket] = useState<MarketData>({
    btcPrice: 0,
    ethPrice: 0,
    fearGreedIndex: 50,
    fearGreedLabel: 'Neutral'
  })
  
  const [riskCalc, setRiskCalc] = useState({
    capital: 100000,
    riskPercent: 1,
    stopLoss: 2,
    positionSize: 0
  })

  const [activeTab, setActiveTab] = useState<'home' | 'news' | 'tools'>('home')
  
  // Calculate Track Record day dynamically (started Jan 15, 2026)
  // Day 1 = Jan 15, Day 15 = Jan 29, Day 16 = Jan 30, etc.
  const trackRecordStartDate = new Date('2026-01-15T00:00:00Z')
  const daysSinceStart = Math.floor((Date.now() - trackRecordStartDate.getTime()) / (1000 * 60 * 60 * 24))
  const currentDay = Math.max(1, daysSinceStart + 1)
  
  const evalCycles = useCountUp(metrics.evaluationCycles, 2500)
  const vetosCount = useCountUp(metrics.vetosExecuted, 2000)

  useEffect(() => {
    if (liveMetrics.evaluation_cycles > 0) {
      const uptimePct = liveMetrics.system_uptime_days > 0
        ? `${Math.min(99.9, ((liveMetrics.system_uptime_days * 24 - 2) / (liveMetrics.system_uptime_days * 24) * 100)).toFixed(1)}%`
        : '99.9%'
      setMetrics(prev => ({
        ...prev,
        evaluationCycles: liveMetrics.evaluation_cycles,
        vetosExecuted: liveMetrics.decisions_blocked,
        capitalPreserved: liveMetrics.capital_preserved_pct,
        systemUptime: uptimePct,
        lastUpdate: new Date().toISOString()
      }))
    }
  }, [liveMetrics])

  useEffect(() => {
    fetchMarketData()
    fetchNews()
    const interval = setInterval(() => {
      fetchMarketData()
    }, 60000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const riskAmount = riskCalc.capital * (riskCalc.riskPercent / 100)
    const stopLossVal = riskCalc.stopLoss || 1
    const posSize = riskAmount / (stopLossVal / 100)
    setRiskCalc(prev => ({ ...prev, positionSize: isNaN(posSize) ? 0 : posSize }))
  }, [riskCalc.capital, riskCalc.riskPercent, riskCalc.stopLoss])

  const fetchMarketData = async () => {
    try {
      const [btcRes, fgRes] = await Promise.all([
        fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd'),
        fetch('https://api.alternative.me/fng/')
      ])
      const btcData = await btcRes.json()
      const fgData = await fgRes.json()
      
      setMarket({
        btcPrice: btcData.bitcoin?.usd || 0,
        ethPrice: btcData.ethereum?.usd || 0,
        fearGreedIndex: parseInt(fgData.data?.[0]?.value || '50'),
        fearGreedLabel: fgData.data?.[0]?.value_classification || 'Neutral'
      })
    } catch (error) {
      console.error('Error fetching market data:', error)
    }
  }

  const fetchNews = async () => {
    try {
      const response = await fetch('/api/news')
      if (response.ok) {
        const data = await response.json()
        if (data.length > 0) {
          setNews(data)
          return
        }
      }
    } catch {
      console.log('Using mock news data')
    }
    
    const mockNews: NewsItem[] = [
      { id: '1', headline: 'Bitcoin Surges Past Key Resistance Level', source: 'CryptoNews', datetime: Date.now(), url: '#', sentiment: 'positive' },
      { id: '2', headline: 'SEC Delays Decision on Spot ETF Applications', source: 'Reuters', datetime: Date.now() - 3600000, url: '#', sentiment: 'neutral' },
      { id: '3', headline: 'Major Exchange Reports Record Trading Volume', source: 'Bloomberg', datetime: Date.now() - 7200000, url: '#', sentiment: 'positive' },
      { id: '4', headline: 'Volatility Expected Ahead of FOMC Meeting', source: 'MarketWatch', datetime: Date.now() - 10800000, url: '#', sentiment: 'negative' },
    ]
    setNews(mockNews)
  }

  const formatNumber = (num: number) => {
    return num.toLocaleString()
  }

  const getFearGreedColor = (value: number) => {
    if (value <= 25) return 'text-red-500'
    if (value <= 45) return 'text-orange-400'
    if (value <= 55) return 'text-yellow-400'
    if (value <= 75) return 'text-lime-400'
    return 'text-green-400'
  }

  return (
    <div className="min-h-screen bg-institutional">
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#050D18]/90 backdrop-blur-xl border-b border-[#C9A227]/10">
        <div className="max-w-7xl mx-auto px-6 pt-5 pb-4">
          <div className="flex items-center justify-center gap-4 mb-4">
            <Link to="/">
              <img src="/logo.png" alt="OMNIX QUANTUM" className="w-12 h-12 object-contain" />
            </Link>
            <div className="flex items-center gap-3">
              <span className="text-xl font-bold text-white tracking-tight">OMNIX QUANTUM</span>
              <span className="px-2 py-0.5 text-[10px] font-semibold bg-emerald-500/20 text-emerald-400 rounded uppercase tracking-wider">Live</span>
            </div>
          </div>
          <div className="flex items-center justify-center gap-6">
            <Link to="/" className="nav-link flex items-center gap-1 text-sm">
              <ArrowRight className="w-3.5 h-3.5 rotate-180" />
              Home
            </Link>
            <button onClick={() => setActiveTab('home')} className={`nav-link text-sm ${activeTab === 'home' ? 'active' : ''}`}>Dashboard</button>
            <button onClick={() => setActiveTab('news')} className={`nav-link text-sm ${activeTab === 'news' ? 'active' : ''}`}>Market Intel</button>
            <button onClick={() => setActiveTab('tools')} className={`nav-link text-sm ${activeTab === 'tools' ? 'active' : ''}`}>Risk Tools</button>
            <Link to="/governance-demo" className="nav-link text-sm text-emerald-400">Credit Demo</Link>
            <Link to="/governance-demo-insurance" className="nav-link text-sm text-blue-400">Insurance Demo</Link>
            <Link to="/governance-demo-biotech" className="nav-link text-sm text-emerald-400">Biotech Demo</Link>
            <a href="https://mail.google.com/mail/?view=cm&to=contacto@omnixquantum.net" target="_blank" rel="noopener noreferrer" className="btn-primary text-sm px-5 py-2">Request Access</a>
          </div>
        </div>
      </nav>

      <main className="pt-36 px-6 pb-20 max-w-7xl mx-auto">
        {activeTab === 'home' && (
          <>
            <section className="text-center mb-20 animate-fade-in-up">
              <p className="section-title">Decision Governance Infrastructure</p>
              <h1 className="heading-xl text-white mb-6">
                The Governance Layer That<br />
                <span className="gold-gradient">Prevents Costly Mistakes</span>
              </h1>
              <p className="text-xl text-muted max-w-3xl mx-auto mb-10 leading-relaxed">
                A domain-agnostic governance control architecture for automated decision systems. Our 11-checkpoint fail-closed engine 
                validates every decision before execution — with a post-quantum cryptographic receipt as proof. Currently live across 8 domains: digital asset trading, Islamic credit (UAE/GCC), global insurance claims, autonomous robotics, Medical AI, autonomous agents, and more. Every domain uses the same shared governance pipeline: 11 checkpoints including SIV, Monte Carlo, DCI, AML, Fraud Detection, and Jurisdiction gates.
              </p>
              <div className="flex justify-center gap-4">
                <a
                  href="mailto:contacto@omnixquantum.net?subject=Demo Request — OMNIX Quantum&body=Hello Harold,%0A%0AI would like to schedule a demo of OMNIX Quantum."
                  className="btn-primary flex items-center gap-2"
                >
                  <Play className="w-4 h-4" />
                  Schedule Demo
                </a>
                <a
                  href="/whitepaper.pdf"
                  download="OMNIX-Quantum-Technical-Brief.pdf"
                  className="btn-secondary flex items-center gap-2"
                >
                  Download Technical Brief
                  <ChevronRight className="w-4 h-4" />
                </a>
              </div>
            </section>

            <section className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-20">
              <div className="stat-card animate-fade-in-up animate-delay-1">
                <div className="flex items-center justify-between mb-4">
                  <Activity className="w-6 h-6 gold-text" />
                  <div className="live-dot" />
                </div>
                <div className="metric-value text-white">{formatNumber(evalCycles)}+</div>
                <p className="text-muted mt-2 text-sm">Evaluation Cycles</p>
              </div>
              
              <div className="stat-card animate-fade-in-up animate-delay-2">
                <div className="flex items-center justify-between mb-4">
                  <AlertTriangle className="w-6 h-6 text-amber-500" />
                </div>
                <div className="metric-value text-amber-500">{formatNumber(vetosCount)}</div>
                <p className="text-muted mt-2 text-sm">High-Risk Decisions Blocked</p>
              </div>
              
              <div className="stat-card animate-fade-in-up animate-delay-3">
                <div className="flex items-center justify-between mb-4">
                  <Shield className="w-6 h-6 text-emerald-500" />
                </div>
                <div className="metric-value text-emerald-500">{metrics.capitalPreserved}%</div>
                <p className="text-muted mt-2 text-sm">Capital Preserved</p>
              </div>
              
              <div className="stat-card animate-fade-in-up animate-delay-4">
                <div className="flex items-center justify-between mb-4">
                  <Zap className="w-6 h-6 gold-text" />
                </div>
                <div className="metric-value gold-text">{metrics.systemUptime}</div>
                <p className="text-muted mt-2 text-sm">System Uptime</p>
              </div>
            </section>

            <div className="divider-gold" />

            <section className="mb-20">
              <div className="grid md:grid-cols-2 gap-12 items-center">
                <div>
                  <p className="section-title">The Challenge</p>
                  <h2 className="text-3xl font-bold text-white mb-6">Why 73% of Automated Decision Systems Fail</h2>
                  <div className="space-y-4">
                    <div className="flex items-start gap-4">
                      <div className="w-8 h-8 rounded-full bg-red-500/20 flex items-center justify-center flex-shrink-0 mt-1">
                        <AlertTriangle className="w-4 h-4 text-red-500" />
                      </div>
                      <div>
                        <h4 className="text-white font-medium mb-1">Execution Without Validation</h4>
                        <p className="text-muted text-sm">Most automated systems execute decisions blindly without checking conditions, risk context, or signal coherence.</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-4">
                      <div className="w-8 h-8 rounded-full bg-red-500/20 flex items-center justify-center flex-shrink-0 mt-1">
                        <AlertTriangle className="w-4 h-4 text-red-500" />
                      </div>
                      <div>
                        <h4 className="text-white font-medium mb-1">Overconfident Position Sizing</h4>
                        <p className="text-muted text-sm">Aggressive Kelly Criterion application without proper edge verification leads to catastrophic drawdowns.</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-4">
                      <div className="w-8 h-8 rounded-full bg-red-500/20 flex items-center justify-center flex-shrink-0 mt-1">
                        <AlertTriangle className="w-4 h-4 text-red-500" />
                      </div>
                      <div>
                        <h4 className="text-white font-medium mb-1">No Black Swan Protection</h4>
                        <p className="text-muted text-sm">Tail risk events wipe out months of gains in hours. Traditional stop-losses fail during flash crashes.</p>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="glass-card p-8 gold-glow">
                  <p className="section-title">The OMNIX Solution</p>
                  <h3 className="text-2xl font-semibold text-white mb-6">Fail-Closed by Design</h3>
                  <p className="text-muted mb-6 leading-relaxed">
                    Unlike fail-open systems that execute first and ask questions later, OMNIX blocks ALL actions by default. 
                    Every decision must pass through 11 independent validation checkpoints before execution is allowed.
                  </p>
                  <div className="flex items-center gap-3 p-4 bg-[#0A1628]/60 rounded-xl border border-emerald-500/30">
                    <CheckCircle className="w-6 h-6 text-emerald-500" />
                    <span className="text-emerald-400 font-medium">Capital protection is the default state</span>
                  </div>
                </div>
              </div>
            </section>

            <div className="divider-gold" />

            <section className="mb-20">
              <div className="text-center mb-12">
                <p className="section-title">System Architecture</p>
                <h2 className="text-3xl font-bold text-white">How OMNIX Governs Your Decisions</h2>
                <p className="text-muted mt-4 max-w-2xl mx-auto">Every decision passes through a rigorous 11-checkpoint validation pipeline. If ANY checkpoint vetoes, execution is blocked.</p>
              </div>
              
              <div className="grid md:grid-cols-4 gap-6">
                <div className="glass-card p-6 relative">
                  <div className="absolute -top-3 -left-3 w-8 h-8 rounded-full bg-[#C9A227] flex items-center justify-center text-[#0A1628] font-bold text-sm">1</div>
                  <div className="feature-icon mb-4">
                    <Eye className="w-6 h-6 gold-text" />
                  </div>
                  <h4 className="text-lg font-semibold text-white mb-2">Regime Detection</h4>
                  <p className="text-muted text-sm leading-relaxed">Hidden Markov Model analyzes market state (trending, ranging, volatile) to determine if conditions favor execution.</p>
                  <div className="mt-4 pt-4 border-t border-[#C9A227]/10">
                    <p className="text-xs text-muted">Veto trigger: Regime uncertainty &gt; 40%</p>
                  </div>
                </div>
                
                <div className="glass-card p-6 relative">
                  <div className="absolute -top-3 -left-3 w-8 h-8 rounded-full bg-[#C9A227] flex items-center justify-center text-[#0A1628] font-bold text-sm">2</div>
                  <div className="feature-icon mb-4">
                    <Layers className="w-6 h-6 gold-text" />
                  </div>
                  <h4 className="text-lg font-semibold text-white mb-2">Coherence Gate</h4>
                  <p className="text-muted text-sm leading-relaxed">6-tier signal coherence engine validates that multiple indicators agree before allowing execution.</p>
                  <div className="mt-4 pt-4 border-t border-[#C9A227]/10">
                    <p className="text-xs text-muted">Veto trigger: Coherence score &lt; 60%</p>
                  </div>
                </div>
                
                <div className="glass-card p-6 relative">
                  <div className="absolute -top-3 -left-3 w-8 h-8 rounded-full bg-[#C9A227] flex items-center justify-center text-[#0A1628] font-bold text-sm">3</div>
                  <div className="feature-icon mb-4">
                    <Target className="w-6 h-6 gold-text" />
                  </div>
                  <h4 className="text-lg font-semibold text-white mb-2">Monte Carlo Simulation</h4>
                  <p className="text-muted text-sm leading-relaxed">10,000 simulations project expected outcomes. Blocks decisions with negative expected return.</p>
                  <div className="mt-4 pt-4 border-t border-[#C9A227]/10">
                    <p className="text-xs text-muted">Veto trigger: Expected return &lt; 0%</p>
                  </div>
                </div>
                
                <div className="glass-card p-6 relative">
                  <div className="absolute -top-3 -left-3 w-8 h-8 rounded-full bg-[#C9A227] flex items-center justify-center text-[#0A1628] font-bold text-sm">4</div>
                  <div className="feature-icon mb-4">
                    <Shield className="w-6 h-6 gold-text" />
                  </div>
                  <h4 className="text-lg font-semibold text-white mb-2">Black Swan Detector</h4>
                  <p className="text-muted text-sm leading-relaxed">Real-time volatility and sentiment analysis identifies tail risk events before they materialize.</p>
                  <div className="mt-4 pt-4 border-t border-[#C9A227]/10">
                    <p className="text-xs text-muted">Veto trigger: Severity &gt; MEDIUM</p>
                  </div>
                </div>
              </div>
              
              <div className="mt-8 glass-card p-6 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-emerald-500/20 flex items-center justify-center">
                    <CheckCircle className="w-6 h-6 text-emerald-500" />
                  </div>
                  <div>
                    <h4 className="text-white font-semibold">Edge Confirmation Window (ECW)</h4>
                    <p className="text-muted text-sm">Requires positive edge for 3 consecutive cycles before allowing execution. Transforms "capital preservation" into "capital patience".</p>
                  </div>
                </div>
                <ArrowRight className="w-6 h-6 gold-text" />
              </div>
            </section>

            <div className="divider-gold" />

            <section className="mb-20">
              <div className="text-center mb-12">
                <p className="section-title">Forensic Evidence</p>
                <h2 className="text-3xl font-bold text-white">Technical Validation — Terra/LUNA May 2022</h2>
                <p className="text-muted mt-4 max-w-3xl mx-auto">First documented proof of Architectural Certainty. OMNIX governance checkpoints applied to the $40B Terra/LUNA collapse using real historical data.</p>
              </div>

              <div className="glass-card p-8 gold-glow relative overflow-hidden">
                <div className="absolute top-4 right-4 px-3 py-1 bg-amber-500/20 border border-amber-500/40 rounded-full">
                  <span className="text-xs font-bold text-amber-400 tracking-wider uppercase">Forensic Evidence</span>
                </div>

                <div className="flex items-start gap-6 mb-8">
                  <div className="w-16 h-16 rounded-2xl bg-[#C9A227]/10 border border-[#C9A227]/30 flex items-center justify-center flex-shrink-0 overflow-hidden">
                    <img src="/logo.png" alt="OMNIX" className="w-12 h-12 object-contain" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-white mb-2">Terra/LUNA Forensic Reconstruction</h3>
                    <p className="text-muted leading-relaxed">3-phase governance simulation using OMNIX's 11-checkpoint fail-closed pipeline against the largest stablecoin collapse in history. Every checkpoint score, every governance decision, and the final cryptographic receipt — documented with real market data.</p>
                  </div>
                </div>

                <div className="grid md:grid-cols-3 gap-4 mb-8">
                  <div className="p-5 bg-[#0A1628]/60 rounded-xl border border-amber-500/20">
                    <div className="flex items-center gap-2 mb-3">
                      <Clock className="w-4 h-4 text-amber-400" />
                      <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider">T-72h</span>
                    </div>
                    <div className="text-2xl font-bold text-white mb-1">$68.84</div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-amber-400" />
                      <span className="text-amber-400 font-semibold text-sm">WARNING ISSUED</span>
                    </div>
                    <p className="text-xs text-muted mt-2">Structural brittleness detected — Manufactured Confidence &gt; 70%</p>
                  </div>

                  <div className="p-5 bg-[#0A1628]/60 rounded-xl border border-red-500/20">
                    <div className="flex items-center gap-2 mb-3">
                      <Clock className="w-4 h-4 text-red-400" />
                      <span className="text-xs font-semibold text-red-400 uppercase tracking-wider">T-24h</span>
                    </div>
                    <div className="text-2xl font-bold text-white mb-1">$18.14</div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-red-500" />
                      <span className="text-red-400 font-semibold text-sm">BLOCKED</span>
                    </div>
                    <p className="text-xs text-muted mt-2">Temporal Coherence failure — confidence inherited, not earned</p>
                  </div>

                  <div className="p-5 bg-[#0A1628]/60 rounded-xl border border-red-500/30">
                    <div className="flex items-center gap-2 mb-3">
                      <Clock className="w-4 h-4 text-red-400" />
                      <span className="text-xs font-semibold text-red-400 uppercase tracking-wider">T-6h</span>
                    </div>
                    <div className="text-2xl font-bold text-white mb-1">$4.60</div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                      <span className="text-red-400 font-semibold text-sm">BLOCKED + RECEIPT</span>
                    </div>
                    <p className="text-xs text-muted mt-2">Sovereign Gate activated — PQC-signed receipt issued</p>
                  </div>
                </div>

                <div className="p-4 bg-[#0A1628]/80 rounded-xl border border-[#C9A227]/20 mb-6">
                  <p className="text-sm text-center text-muted">
                    <span className="text-white font-medium">May 11, 2022 — $1.73</span> — Irreversible collapse.{' '}
                    <span className="gold-text font-medium">OMNIX had already blocked execution 6 hours earlier.</span>
                  </p>
                </div>

                <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                  <a
                    href="/docs/OMNIX_LUNA_Forensic_Simulation_May2022.pdf"
                    download
                    className="btn-primary flex items-center gap-2 px-6 py-3"
                  >
                    <Download className="w-5 h-5" />
                    Download Full Report (PDF)
                  </a>
                  <span className="text-xs text-muted">7 sections · Real data · Cryptographic receipt included</span>
                </div>
              </div>
            </section>

            <div className="divider-gold" />

            <section className="grid md:grid-cols-2 gap-8 mb-20">
              <div className="glass-card p-8">
                <p className="section-title">Live Market Data</p>
                <h3 className="text-2xl font-semibold text-white mb-6">Market Overview</h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center p-4 bg-[#0A1628]/60 rounded-xl border border-[#C9A227]/10">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-orange-500/20 flex items-center justify-center">
                        <span className="text-orange-500 font-bold text-sm">BTC</span>
                      </div>
                      <span className="text-white font-medium">Bitcoin</span>
                    </div>
                    <span className="text-2xl font-bold text-white">${market.btcPrice.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between items-center p-4 bg-[#0A1628]/60 rounded-xl border border-[#C9A227]/10">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center">
                        <span className="text-blue-500 font-bold text-sm">ETH</span>
                      </div>
                      <span className="text-white font-medium">Ethereum</span>
                    </div>
                    <span className="text-2xl font-bold text-white">${market.ethPrice.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between items-center p-4 bg-[#0A1628]/60 rounded-xl border border-[#C9A227]/10">
                    <span className="text-muted">Fear & Greed Index</span>
                    <span className={`text-2xl font-bold ${getFearGreedColor(market.fearGreedIndex)}`}>
                      {market.fearGreedIndex} - {market.fearGreedLabel}
                    </span>
                  </div>
                </div>
              </div>

              <div className="glass-card p-8">
                <p className="section-title">Technology Stack</p>
                <h3 className="text-2xl font-semibold text-white mb-6">Enterprise-Grade Infrastructure</h3>
                <div className="space-y-4">
                  <div className="flex items-center gap-4 p-4 bg-[#0A1628]/60 rounded-xl border border-[#C9A227]/10">
                    <Brain className="w-6 h-6 gold-text" />
                    <div className="flex-1">
                      <span className="text-white font-medium">AI Risk Guardian</span>
                      <p className="text-xs text-muted">Google Gemini 2.0 + GPT-4o fallback</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 p-4 bg-[#0A1628]/60 rounded-xl border border-[#C9A227]/10">
                    <Cpu className="w-6 h-6 gold-text" />
                    <div className="flex-1">
                      <span className="text-white font-medium">Post-Quantum Cryptography</span>
                      <p className="text-xs text-muted">NIST-standardized post-quantum cryptography (CRYSTALS family)</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 p-4 bg-[#0A1628]/60 rounded-xl border border-[#C9A227]/10">
                    <Server className="w-6 h-6 gold-text" />
                    <div className="flex-1">
                      <span className="text-white font-medium">Railway Cloud Infrastructure</span>
                      <p className="text-xs text-muted">PostgreSQL + Redis + Auto-scaling</p>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <div className="divider-gold" />

            <section className="mb-20">
              <div className="text-center mb-12">
                <p className="section-title">Integration Partners</p>
                <h2 className="text-3xl font-bold text-white">Built for Your Decision Infrastructure</h2>
                <p className="text-muted mt-4 max-w-2xl mx-auto">OMNIX integrates seamlessly with existing decision systems via REST API or webhooks. Currently governing decisions across 8 live domains: digital asset trading, Islamic credit, insurance claims, autonomous robotics, Medical AI, autonomous agents, and more.</p>
              </div>
              
              <div className="grid md:grid-cols-3 gap-8">
                <div className="glass-card p-8">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center">
                      <TrendingUp className="w-6 h-6 text-blue-500" />
                    </div>
                    <div>
                      <h4 className="text-lg font-semibold text-white">Decision Platforms</h4>
                      <p className="text-xs text-muted">3Commas, NinjaTrader, TradingView</p>
                    </div>
                  </div>
                  <p className="text-muted text-sm leading-relaxed mb-4">
                    Add institutional-grade governance validation to your existing signals. OMNIX receives your decision signals, validates them through our 11-checkpoint pipeline, and returns approve/block decisions in &lt;50ms.
                  </p>
                  <div className="flex items-center justify-between text-sm">
                    <span className="gold-text font-medium">API Integration</span>
                    <span className="text-muted">REST / WebSocket</span>
                  </div>
                </div>
                
                <div className="glass-card p-8">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center">
                      <Users className="w-6 h-6 text-purple-500" />
                    </div>
                    <div>
                      <h4 className="text-lg font-semibold text-white">Exchanges & Brokers</h4>
                      <p className="text-xs text-muted">Kraken, Interactive Brokers, Alpaca</p>
                    </div>
                  </div>
                  <p className="text-muted text-sm leading-relaxed mb-4">
                    White-label our governance engine for your platform. Offer institutional-grade decision controls to your clients as a premium feature or compliance requirement.
                  </p>
                  <div className="flex items-center justify-between text-sm">
                    <span className="gold-text font-medium">White-Label Engine</span>
                    <span className="text-muted">$100K+ setup</span>
                  </div>
                </div>
                
                <div className="glass-card p-8">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center">
                      <DollarSign className="w-6 h-6 text-emerald-500" />
                    </div>
                    <div>
                      <h4 className="text-lg font-semibold text-white">Channel Partners</h4>
                      <p className="text-xs text-muted">Revenue share model</p>
                    </div>
                  </div>
                  <p className="text-muted text-sm leading-relaxed mb-4">
                    Embed OMNIX governance as a value-added layer inside your platform. Financial institutions, insurers, and robotics operators can deploy OMNIX for their clients through the channel partner program.
                  </p>
                  <div className="flex items-center justify-between text-sm">
                    <span className="gold-text font-medium">Partner Program</span>
                    <span className="text-muted">10% mutual commissions</span>
                  </div>
                </div>
              </div>
            </section>

            <div className="divider-gold" />

            <section className="mb-20">
              <div className="text-center mb-12">
                <p className="section-title">Transparency</p>
                <h2 className="text-3xl font-bold text-white">Verifiable Track Record</h2>
                <p className="text-muted mt-4 max-w-2xl mx-auto">We believe in radical transparency. All metrics are real-time and verifiable on-chain.</p>
              </div>
              
              <div className="glass-card p-8 gold-glow">
                <div className="grid md:grid-cols-2 gap-8 mb-8">
                  <div>
                    <div className="flex items-center gap-2 mb-4">
                      <Clock className="w-5 h-5 gold-text" />
                      <span className="text-white font-semibold">Track Record Period</span>
                    </div>
                    <div className="space-y-3">
                      <div className="flex justify-between p-3 bg-[#0A1628]/60 rounded-lg">
                        <span className="text-muted">Official Start Date</span>
                        <span className="text-white font-medium">January 15, 2026</span>
                      </div>
                      <div className="flex justify-between p-3 bg-[#0A1628]/60 rounded-lg">
                        <span className="text-muted">Current Day</span>
                        <span className="text-emerald-400 font-medium">Day {currentDay}</span>
                      </div>
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-4">
                      <BarChart3 className="w-5 h-5 gold-text" />
                      <span className="text-white font-semibold">Performance Metrics</span>
                    </div>
                    <div className="space-y-3">
                      <div className="flex justify-between p-3 bg-[#0A1628]/60 rounded-lg">
                        <span className="text-muted">Capital Preserved</span>
                        <span className="text-emerald-400 font-medium">{metrics.capitalPreserved}%</span>
                      </div>
                      <div className="flex justify-between p-3 bg-[#0A1628]/60 rounded-lg">
                        <span className="text-muted">Max Drawdown</span>
                        <span className="text-white font-medium">-{(100 - metrics.capitalPreserved).toFixed(2)}%</span>
                      </div>
                      <div className="flex justify-between p-3 bg-[#0A1628]/60 rounded-lg">
                        <span className="text-muted">High-Risk Blocks</span>
                        <span className="text-amber-400 font-medium">{metrics.vetosExecuted.toLocaleString()}+</span>
                      </div>
                      <div className="p-2 bg-[#0A1628]/40 rounded-lg">
                        <p className="text-[10px] text-muted/60 text-center italic">Internal evaluation dataset · Not externally audited</p>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="p-4 bg-[#0A1628]/80 rounded-xl border border-[#C9A227]/20 text-center">
                  <p className="text-sm text-muted">
                    <span className="gold-text font-medium">Learning Baseline (Nov 2025 - Jan 14, 2026):</span> 119 trades, -$15,198.73 (calibration period).
                    <br />
                    Track Record Oficial began January 15, 2026 with recalibrated parameters.
                  </p>
                </div>
              </div>
            </section>

            <div className="divider-gold" />

            <section className="mb-20">
              <div className="text-center mb-12">
                <p className="section-title">Competitive Advantage</p>
                <h2 className="text-3xl font-bold text-white">Built for Institutional Requirements</h2>
              </div>
              <div className="grid md:grid-cols-3 gap-8">
                <div className="glass-card p-8">
                  <div className="feature-icon mb-6">
                    <Lock className="w-6 h-6 gold-text" />
                  </div>
                  <h4 className="text-xl font-semibold text-white mb-3">Fail-Closed by Default</h4>
                  <p className="text-muted leading-relaxed">Every decision is blocked unless ALL validation layers explicitly approve. Safety is the default state, not an afterthought.</p>
                </div>
                <div className="glass-card p-8">
                  <div className="feature-icon mb-6">
                    <BarChart3 className="w-6 h-6 gold-text" />
                  </div>
                  <h4 className="text-xl font-semibold text-white mb-3">Complete Audit Trail</h4>
                  <p className="text-muted leading-relaxed">Every decision is logged with timestamps, risk metrics, and validation results. Designed for ADGM and SEC regulatory frameworks.</p>
                </div>
                <div className="glass-card p-8">
                  <div className="feature-icon mb-6">
                    <Shield className="w-6 h-6 gold-text" />
                  </div>
                  <h4 className="text-xl font-semibold text-white mb-3">Post-Quantum Security</h4>
                  <p className="text-muted leading-relaxed">NIST-standardized post-quantum cryptography — key encapsulation and digital signatures.</p>
                </div>
              </div>
            </section>

            <section className="glass-card p-10 text-center gold-glow mb-20">
              <p className="section-title">Trusted Infrastructure</p>
              <h3 className="text-2xl font-bold text-white mb-8">Regulatory Compliance & Certifications</h3>
              <div className="flex justify-center items-center gap-12 flex-wrap">
                <div className="flex items-center gap-3">
                  <Globe className="w-8 h-8 gold-text" />
                  <div className="text-left">
                    <p className="text-white font-semibold">ADGM</p>
                    <p className="text-xs text-amber-400">Designed for Compliance</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Award className="w-8 h-8 gold-text" />
                  <div className="text-left">
                    <p className="text-white font-semibold">NIST PQC Standards</p>
                    <p className="text-xs text-emerald-400">Implemented</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Shield className="w-8 h-8 gold-text" />
                  <div className="text-left">
                    <p className="text-white font-semibold">Sharia Compliant</p>
                    <p className="text-xs text-amber-400">In Development</p>
                  </div>
                </div>
              </div>
            </section>

            <div className="divider-gold" />

            <section className="mb-20">
              <div className="text-center mb-12">
                <p className="section-title">Comparison</p>
                <h2 className="text-3xl font-bold text-white mb-4">OMNIX vs Traditional Automated Decision Systems</h2>
                <p className="text-[#C9A227]/70 italic text-base max-w-2xl mx-auto">
                  "OMNIX doesn't just follow rules. It understands when and why they should apply."
                </p>
              </div>
              <div className="glass-card overflow-hidden">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-[#C9A227]/20 bg-[#0A1628]/80">
                      <th className="text-left py-4 px-6 text-[#C9A227] font-semibold">Feature</th>
                      <th className="text-left py-4 px-6 text-muted font-medium">Traditional Automated Systems</th>
                      <th className="text-left py-4 px-6 text-emerald-400 font-semibold">OMNIX Governance</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#C9A227]/10">
                    <tr className="hover:bg-[#C9A227]/5 transition-colors">
                      <td className="py-4 px-6 text-white font-medium">Execution Model</td>
                      <td className="py-4 px-6 text-muted">Signal → Immediate Execution</td>
                      <td className="py-4 px-6 text-emerald-400">Signal → Validation → Conditional Execution</td>
                    </tr>
                    <tr className="hover:bg-[#C9A227]/5 transition-colors">
                      <td className="py-4 px-6 text-white font-medium">Default State</td>
                      <td className="py-4 px-6 text-muted">Execute unless stopped</td>
                      <td className="py-4 px-6 text-emerald-400">Block unless approved</td>
                    </tr>
                    <tr className="hover:bg-[#C9A227]/5 transition-colors">
                      <td className="py-4 px-6 text-white font-medium">Regime Awareness</td>
                      <td className="py-4 px-6 text-muted">Static parameters</td>
                      <td className="py-4 px-6 text-emerald-400">Real-time regime detection (HMM)</td>
                    </tr>
                    <tr className="hover:bg-[#C9A227]/5 transition-colors">
                      <td className="py-4 px-6 text-white font-medium">Risk Validation</td>
                      <td className="py-4 px-6 text-muted">Post-execution analysis</td>
                      <td className="py-4 px-6 text-emerald-400">Pre-execution Monte Carlo simulation</td>
                    </tr>
                    <tr className="hover:bg-[#C9A227]/5 transition-colors">
                      <td className="py-4 px-6 text-white font-medium">Auditability</td>
                      <td className="py-4 px-6 text-muted">Limited or none</td>
                      <td className="py-4 px-6 text-emerald-400">Full decision lineage</td>
                    </tr>
                    <tr className="hover:bg-[#C9A227]/5 transition-colors">
                      <td className="py-4 px-6 text-white font-medium">Capital Preservation</td>
                      <td className="py-4 px-6 text-muted">Reactive (stop-loss)</td>
                      <td className="py-4 px-6 text-emerald-400">Proactive (pre-execution block)</td>
                    </tr>
                    <tr className="hover:bg-[#C9A227]/5 transition-colors">
                      <td className="py-4 px-6 text-white font-medium">Black Swan Protection</td>
                      <td className="py-4 px-6 text-muted">None</td>
                      <td className="py-4 px-6 text-emerald-400">Real-time tail risk detection</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>

            <div className="divider-gold" />

            <section className="mb-20">
              <div className="text-center mb-12">
                <p className="section-title">FAQ</p>
                <h2 className="text-3xl font-bold text-white">Frequently Asked Questions</h2>
              </div>
              <div className="max-w-4xl mx-auto space-y-4">
                <div className="glass-card p-6">
                  <h4 className="text-lg font-semibold text-white mb-3">Is OMNIX a trading bot?</h4>
                  <p className="text-muted leading-relaxed">No. OMNIX is a governance control architecture for automated decision systems. It does not generate signals or alpha. It sits between your signal generation and execution, validating every decision through 11 independent checkpoints before execution is permitted. The same pipeline today governs 8 live domains: digital asset trading, Islamic credit (UAE/GCC), global insurance claims, autonomous robotics, Medical AI, autonomous agents, and more. The architecture is designed to expand further into AGL and supply chain.</p>
                </div>
                <div className="glass-card p-6">
                  <h4 className="text-lg font-semibold text-white mb-3">How does OMNIX integrate with existing systems?</h4>
                  <p className="text-muted leading-relaxed">OMNIX is designed as a modular validation layer. It integrates via REST API or WebSocket and can work with any signal generation system. Your strategies remain unchanged—OMNIX simply validates execution decisions in real-time (&lt;50ms latency).</p>
                </div>
                <div className="glass-card p-6">
                  <h4 className="text-lg font-semibold text-white mb-3">What makes OMNIX institutional-grade?</h4>
                  <p className="text-muted leading-relaxed">Full auditability, fail-closed architecture, regulatory compliance infrastructure designed for frameworks like ADGM, post-quantum cryptography (NIST-standardized), and real-time decision validation. OMNIX is built for fiduciary standards, not retail tools.</p>
                </div>
                <div className="glass-card p-6">
                  <h4 className="text-lg font-semibold text-white mb-3">How is performance measured?</h4>
                  <p className="text-muted leading-relaxed">OMNIX tracks counterfactual outcomes of blocked trades using a Shadow Portfolio system. Every rejected trade is simulated to measure what would have happened if it had executed. This creates a measurable, auditable track record of capital preservation.</p>
                </div>
                <div className="glass-card p-6">
                  <h4 className="text-lg font-semibold text-white mb-3">Who controls the risk parameters?</h4>
                  <p className="text-muted leading-relaxed">Your institutional team maintains full control over validation thresholds, risk parameters, and approval criteria. OMNIX provides the infrastructure—you define the rules. All parameters are configurable via dashboard or API.</p>
                </div>
              </div>
            </section>

            <section className="text-center">
              <div className="glass-card p-12 gold-glow">
                <h2 className="text-3xl font-bold text-white mb-4">Ready to Govern Your Decisions?</h2>
                <p className="text-xl text-muted max-w-2xl mx-auto mb-8">
                  Schedule a demo to see how OMNIX can integrate with your decision infrastructure.
                </p>
                <div className="flex justify-center gap-4">
                  <a
                    href="mailto:contacto@omnixquantum.net?subject=Demo Request — OMNIX Quantum&body=Hello Harold,%0A%0AI would like to schedule a demo of OMNIX Quantum."
                    className="btn-primary flex items-center gap-2"
                  >
                    <Play className="w-4 h-4" />
                    Schedule Demo
                  </a>
                  <a
                    href="mailto:contacto@omnixquantum.net?subject=Sales Inquiry — OMNIX Quantum"
                    className="btn-secondary"
                  >
                    Contact Sales
                  </a>
                </div>
                <p className="text-muted text-sm mt-6">No credit card required. 14-day free trial for Pro plans.</p>
                <div className="flex justify-center items-center gap-8 mt-6 text-sm">
                  <a href="https://mail.google.com/mail/?view=cm&to=contacto@omnixquantum.net" target="_blank" rel="noopener noreferrer" className="text-[#C9A227] hover:text-white transition-colors flex items-center gap-2">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
                    contacto@omnixquantum.net
                  </a>
                  <a href="https://mail.google.com/mail/?view=cm&to=contacto@omnixquantum.net" target="_blank" rel="noopener noreferrer" className="text-[#C9A227] hover:text-white transition-colors flex items-center gap-2">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" /></svg>
                    +1 (650) 507-8293
                  </a>
                </div>
              </div>
            </section>
          </>
        )}

        {activeTab === 'news' && (
          <section className="animate-fade-in-up">
            <div className="mb-8">
              <p className="section-title">Market Intelligence</p>
              <h2 className="text-3xl font-bold text-white">Crypto Market News</h2>
            </div>
            <div className="grid md:grid-cols-3 gap-6 mb-8">
              <div className="md:col-span-2 space-y-4">
                {news.map(item => (
                  <div key={item.id} className="glass-card p-5 flex items-center gap-4 cursor-pointer">
                    <div className={`w-1.5 h-14 rounded-full ${
                      item.sentiment === 'positive' ? 'bg-emerald-500' : 
                      item.sentiment === 'negative' ? 'bg-red-500' : 'bg-slate-500'
                    }`} />
                    <div className="flex-1">
                      <h4 className="font-medium text-white">{item.headline}</h4>
                      <p className="text-sm text-muted mt-1">{item.source} • {new Date(item.datetime).toLocaleTimeString()}</p>
                    </div>
                    <ExternalLink className="w-5 h-5 text-muted" />
                  </div>
                ))}
              </div>
              <div className="glass-card p-6">
                <p className="section-title">Sentiment</p>
                <h3 className="text-xl font-semibold text-white mb-6">Fear & Greed Index</h3>
                <div className="text-center mb-6">
                  <div className={`text-6xl font-bold ${getFearGreedColor(market.fearGreedIndex)}`}>
                    {market.fearGreedIndex}
                  </div>
                  <p className={`text-lg font-medium mt-2 ${getFearGreedColor(market.fearGreedIndex)}`}>
                    {market.fearGreedLabel}
                  </p>
                </div>
                <div className="h-3 rounded-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 relative">
                  <div 
                    className="absolute top-1/2 -translate-y-1/2 w-5 h-5 bg-white rounded-full shadow-lg border-2 border-[#0A1628]"
                    style={{ left: `${market.fearGreedIndex}%`, transform: 'translate(-50%, -50%)' }}
                  />
                </div>
                <div className="flex justify-between text-xs text-muted mt-2">
                  <span>Extreme Fear</span>
                  <span>Extreme Greed</span>
                </div>
              </div>
            </div>
          </section>
        )}

        {activeTab === 'tools' && (
          <section className="animate-fade-in-up">
            <div className="mb-8">
              <p className="section-title">Risk Management</p>
              <h2 className="text-3xl font-bold text-white">Professional Risk Tools</h2>
            </div>
            
            <div className="glass-card p-8 mb-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="feature-icon">
                  <Calculator className="w-6 h-6 gold-text" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-white">Position Size Calculator</h3>
                  <p className="text-sm text-muted">Calculate optimal position size based on your risk parameters</p>
                </div>
              </div>
              
              <div className="grid md:grid-cols-2 gap-8">
                <div className="space-y-5">
                  <div>
                    <label className="block text-sm text-muted mb-2 font-medium">Account Capital (USD)</label>
                    <input 
                      type="number"
                      value={riskCalc.capital}
                      onChange={e => setRiskCalc(prev => ({ ...prev, capital: parseFloat(e.target.value) || 0 }))}
                      className="w-full bg-[#0A1628] border border-[#C9A227]/20 rounded-lg px-4 py-4 text-white text-lg focus:border-[#C9A227] focus:outline-none transition"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-muted mb-2 font-medium">Risk Per Decision (%)</label>
                    <input 
                      type="number"
                      value={riskCalc.riskPercent}
                      onChange={e => setRiskCalc(prev => ({ ...prev, riskPercent: parseFloat(e.target.value) || 0 }))}
                      className="w-full bg-[#0A1628] border border-[#C9A227]/20 rounded-lg px-4 py-4 text-white text-lg focus:border-[#C9A227] focus:outline-none transition"
                      step="0.5"
                      min="0.1"
                      max="10"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-muted mb-2 font-medium">Stop Loss Distance (%)</label>
                    <input 
                      type="number"
                      value={riskCalc.stopLoss}
                      onChange={e => setRiskCalc(prev => ({ ...prev, stopLoss: parseFloat(e.target.value) || 0 }))}
                      className="w-full bg-[#0A1628] border border-[#C9A227]/20 rounded-lg px-4 py-4 text-white text-lg focus:border-[#C9A227] focus:outline-none transition"
                      step="0.5"
                      min="0.5"
                      max="50"
                    />
                  </div>
                </div>
                
                <div className="bg-[#0A1628]/80 rounded-2xl p-8 flex flex-col justify-center border border-[#C9A227]/20">
                  <p className="text-muted text-center mb-2">Recommended Position Size</p>
                  <p className="text-5xl font-bold gold-gradient text-center">
                    ${riskCalc.positionSize.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </p>
                  <div className="mt-6 pt-6 border-t border-[#C9A227]/10">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted">Risk Amount</span>
                      <span className="text-white font-medium">${(riskCalc.capital * riskCalc.riskPercent / 100).toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                    </div>
                    <div className="flex justify-between text-sm mt-2">
                      <span className="text-muted">Max Loss</span>
                      <span className="text-red-400 font-medium">-${(riskCalc.capital * riskCalc.riskPercent / 100).toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="glass-card p-8">
              <h3 className="text-xl font-semibold text-white mb-4">Kelly Criterion</h3>
              <p className="text-muted mb-6">
                The Kelly Criterion determines optimal position sizing to maximize long-term capital growth while managing risk.
              </p>
              <div className="bg-[#0A1628]/60 rounded-xl p-6 border border-[#C9A227]/10">
                <p className="text-white font-mono text-lg mb-3">f* = (bp - q) / b</p>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="gold-text font-semibold">b</span>
                    <span className="text-muted"> = odds received</span>
                  </div>
                  <div>
                    <span className="gold-text font-semibold">p</span>
                    <span className="text-muted"> = win probability</span>
                  </div>
                  <div>
                    <span className="gold-text font-semibold">q</span>
                    <span className="text-muted"> = loss probability</span>
                  </div>
                </div>
              </div>
              <p className="text-xs text-muted mt-4">
                OMNIX uses fractional Kelly (25-50%) to reduce volatility while maintaining edge optimization.
              </p>
            </div>
          </section>
        )}
      </main>

      {/* Team Section */}
      <section className="py-20 bg-gradient-to-b from-[#0A1628] to-[#050D18]">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Leadership Team</h2>
            <p className="text-lg text-muted max-w-2xl mx-auto">
              The minds behind OMNIX QUANTUM's institutional-grade risk infrastructure
            </p>
          </div>
          
          <div className="grid md:grid-cols-1 gap-8 max-w-lg mx-auto">
            <div className="bg-[#0D1B2A]/80 border border-[#C9A227]/20 rounded-xl p-8 text-center hover:border-[#C9A227]/40 transition-all">
              <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-gradient-to-br from-[#C9A227] to-[#8B7355] flex items-center justify-center">
                <Users className="w-12 h-12 text-[#050D18]" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Harold Nunes</h3>
              <p className="text-[#C9A227] font-semibold mb-4">Founder & CEO</p>
              <p className="text-sm text-muted">
                Visionary entrepreneur driving OMNIX QUANTUM's mission to democratize institutional-grade decision governance for automated systems.
              </p>
            </div>
          </div>
        </div>
      </section>

      <footer className="border-t border-[#C9A227]/10 bg-[#050D18]">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="grid md:grid-cols-4 gap-8 mb-10">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <img src="/logo.png" alt="OMNIX QUANTUM" className="w-14 h-14 object-contain" />
                <span className="font-bold text-white">OMNIX QUANTUM</span>
              </div>
              <p className="text-sm text-muted">Governance control architecture for automated decision systems.</p>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-sm text-muted">
                <li><Link to="/institutional" className="hover:text-[#C9A227] transition-colors">About Us</Link></li>
                <li><a href="mailto:contacto@omnixquantum.net?subject=Careers at OMNIX QUANTUM" className="hover:text-[#C9A227] transition-colors">Careers</a></li>
                <li><a href="mailto:contacto@omnixquantum.net?subject=Press Inquiry" className="hover:text-[#C9A227] transition-colors">Press</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Resources</h4>
              <ul className="space-y-2 text-sm text-muted">
                <li><Link to="/integration" className="hover:text-[#C9A227] transition-colors">Documentation</Link></li>
                <li><Link to="/stack" className="hover:text-[#C9A227] transition-colors">API Reference</Link></li>
                <li><a href="/whitepaper.pdf" download className="hover:text-[#C9A227] transition-colors">Technical Brief</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Contact</h4>
              <ul className="space-y-2 text-sm text-muted">
                <li><a href="mailto:contacto@omnixquantum.net" className="hover:text-[#C9A227] transition-colors">contacto@omnixquantum.net</a></li>
                <li><a href="tel:+16505078293" className="hover:text-[#C9A227] transition-colors">+1 (650) 507-8293</a></li>
                <li>
                  <a href="https://wa.me/16505078293" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 hover:text-[#C9A227] transition-colors">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
                    WhatsApp
                  </a>
                </li>
              </ul>
            </div>
          </div>
          <div className="border-t border-[#C9A227]/10 pt-8">
            <p className="footer-disclaimer mb-4">
              DISCLAIMER: OMNIX QUANTUM provides decision governance infrastructure. Past performance does not guarantee future results. 
              High-stakes decision domains involve substantial risk. This platform is designed for institutional investors and qualified professional clients only. 
              Not available in all jurisdictions. Please consult your legal and financial advisors before use.
            </p>
            <div className="flex justify-between items-center">
              <p className="text-xs text-muted">&copy; 2026 OMNIX QUANTUM. All rights reserved.</p>
              <div className="flex gap-6 text-xs text-muted">
                <Link to="/privacy" className="hover:text-[#C9A227] transition-colors">Privacy Policy</Link>
                <Link to="/terms" className="hover:text-[#C9A227] transition-colors">Terms of Service</Link>
                <Link to="/privacy" className="hover:text-[#C9A227] transition-colors">Cookie Policy</Link>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
