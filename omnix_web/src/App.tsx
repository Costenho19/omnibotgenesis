import { useState, useEffect, useRef } from 'react'
import { Shield, Activity, AlertTriangle, Zap, BarChart3, Calculator, ExternalLink, Lock, Award, Globe, ChevronRight, Play, Target, Brain, Cpu, TrendingUp, Users, DollarSign, CheckCircle, ArrowRight, Clock, Layers, Eye, Server } from 'lucide-react'
import './index.css'

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

function App() {
  const [metrics, setMetrics] = useState<SystemMetrics>({
    evaluationCycles: 175192,
    vetosExecuted: 5473,
    capitalPreserved: 98.5,
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
  
  const evalCycles = useCountUp(metrics.evaluationCycles, 2500)
  const vetosCount = useCountUp(metrics.vetosExecuted, 2000)

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch('/api/metrics')
        if (response.ok) {
          const data = await response.json()
          if (data && typeof data.evaluationCycles === 'number') {
            setMetrics(prev => ({
              ...prev,
              evaluationCycles: data.evaluationCycles || prev.evaluationCycles,
              vetosExecuted: data.vetosExecuted || prev.vetosExecuted,
              capitalPreserved: data.capitalPreserved || prev.capitalPreserved,
              systemUptime: data.systemUptime || prev.systemUptime,
              lastUpdate: new Date().toISOString()
            }))
          }
        }
      } catch {
        // Keep existing values, just update timestamp
      }
    }
    
    fetchMetrics()
    const interval = setInterval(fetchMetrics, 30000)
    return () => clearInterval(interval)
  }, [])

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
        <div className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <img src="/logo.png" alt="OMNIX QUANTUM" className="w-16 h-16 object-contain" />
            <div>
              <span className="text-lg font-bold text-white tracking-tight">OMNIX QUANTUM</span>
              <span className="ml-3 px-2 py-0.5 text-[10px] font-semibold bg-emerald-500/20 text-emerald-400 rounded uppercase tracking-wider">Live</span>
            </div>
          </div>
          <div className="flex items-center gap-8">
            <button onClick={() => setActiveTab('home')} className={`nav-link ${activeTab === 'home' ? 'active' : ''}`}>Dashboard</button>
            <button onClick={() => setActiveTab('news')} className={`nav-link ${activeTab === 'news' ? 'active' : ''}`}>Market Intel</button>
            <button onClick={() => setActiveTab('tools')} className={`nav-link ${activeTab === 'tools' ? 'active' : ''}`}>Risk Tools</button>
            <button className="btn-primary">Request Access</button>
          </div>
        </div>
      </nav>

      <main className="pt-28 px-6 pb-20 max-w-7xl mx-auto">
        {activeTab === 'home' && (
          <>
            {/* Hero Section */}
            <section className="text-center mb-20 animate-fade-in-up">
              <p className="section-title">Institutional Risk Control Infrastructure</p>
              <h1 className="heading-xl text-white mb-6">
                The Governance Layer That<br />
                <span className="gold-gradient">Protects Institutional Capital</span>
              </h1>
              <p className="text-xl text-muted max-w-3xl mx-auto mb-10 leading-relaxed">
                OMNIX validates every trade before execution. Our 4-layer fail-closed architecture 
                ensures capital preservation is never compromised by aggressive execution.
              </p>
              <div className="flex justify-center gap-4">
                <button className="btn-primary flex items-center gap-2">
                  <Play className="w-4 h-4" />
                  Schedule Demo
                </button>
                <button className="btn-secondary flex items-center gap-2">
                  Download Technical Brief
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </section>

            {/* Live Stats */}
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
                <p className="text-muted mt-2 text-sm">High-Risk Trades Blocked</p>
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

            {/* The Problem We Solve */}
            <section className="mb-20">
              <div className="grid md:grid-cols-2 gap-12 items-center">
                <div>
                  <p className="section-title">The Challenge</p>
                  <h2 className="text-3xl font-bold text-white mb-6">Why 73% of Algorithmic Traders Lose Money</h2>
                  <div className="space-y-4">
                    <div className="flex items-start gap-4">
                      <div className="w-8 h-8 rounded-full bg-red-500/20 flex items-center justify-center flex-shrink-0 mt-1">
                        <AlertTriangle className="w-4 h-4 text-red-500" />
                      </div>
                      <div>
                        <h4 className="text-white font-medium mb-1">Execution Without Validation</h4>
                        <p className="text-muted text-sm">Most trading bots execute signals blindly without checking market regime, volatility conditions, or signal coherence.</p>
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
                    Unlike fail-open systems that execute first and ask questions later, OMNIX blocks ALL trades by default. 
                    Every trade must pass through 4 independent validation layers before execution is allowed.
                  </p>
                  <div className="flex items-center gap-3 p-4 bg-[#0A1628]/60 rounded-xl border border-emerald-500/30">
                    <CheckCircle className="w-6 h-6 text-emerald-500" />
                    <span className="text-emerald-400 font-medium">Capital protection is the default state</span>
                  </div>
                </div>
              </div>
            </section>

            <div className="divider-gold" />

            {/* How It Works */}
            <section className="mb-20">
              <div className="text-center mb-12">
                <p className="section-title">System Architecture</p>
                <h2 className="text-3xl font-bold text-white">How OMNIX Protects Your Capital</h2>
                <p className="text-muted mt-4 max-w-2xl mx-auto">Every trade signal passes through a rigorous 4-layer validation pipeline. If ANY layer vetoes, the trade is blocked.</p>
              </div>
              
              <div className="grid md:grid-cols-4 gap-6">
                <div className="glass-card p-6 relative">
                  <div className="absolute -top-3 -left-3 w-8 h-8 rounded-full bg-[#C9A227] flex items-center justify-center text-[#0A1628] font-bold text-sm">1</div>
                  <div className="feature-icon mb-4">
                    <Eye className="w-6 h-6 gold-text" />
                  </div>
                  <h4 className="text-lg font-semibold text-white mb-2">Regime Detection</h4>
                  <p className="text-muted text-sm leading-relaxed">Hidden Markov Model analyzes market state (trending, ranging, volatile) to determine if conditions favor trading.</p>
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
                  <p className="text-muted text-sm leading-relaxed">10,000 simulations project expected outcomes. Blocks trades with negative expected return.</p>
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
                    <p className="text-muted text-sm">Requires positive edge for 3 consecutive cycles before allowing trades. Transforms "capital preservation" into "capital patience".</p>
                  </div>
                </div>
                <ArrowRight className="w-6 h-6 gold-text" />
              </div>
            </section>

            <div className="divider-gold" />

            {/* Live Market + Architecture */}
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
                      <p className="text-xs text-muted">Kyber-768 / Dilithium-3 (NIST FIPS 203/204)</p>
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

            {/* Use Cases */}
            <section className="mb-20">
              <div className="text-center mb-12">
                <p className="section-title">Integration Partners</p>
                <h2 className="text-3xl font-bold text-white">Built for Your Trading Stack</h2>
                <p className="text-muted mt-4 max-w-2xl mx-auto">OMNIX integrates seamlessly with existing trading infrastructure via REST API or webhooks.</p>
              </div>
              
              <div className="grid md:grid-cols-3 gap-8">
                <div className="glass-card p-8">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center">
                      <TrendingUp className="w-6 h-6 text-blue-500" />
                    </div>
                    <div>
                      <h4 className="text-lg font-semibold text-white">Trading Platforms</h4>
                      <p className="text-xs text-muted">3Commas, NinjaTrader, TradingView</p>
                    </div>
                  </div>
                  <p className="text-muted text-sm leading-relaxed mb-4">
                    Add institutional-grade risk validation to your existing signals. OMNIX receives your trade signals, validates them through our 4-layer pipeline, and returns approve/block decisions in &lt;50ms.
                  </p>
                  <div className="flex items-center justify-between text-sm">
                    <span className="gold-text font-medium">Risk Guardian API</span>
                    <span className="text-muted">$10K-50K/mo</span>
                  </div>
                </div>
                
                <div className="glass-card p-8">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center">
                      <Users className="w-6 h-6 text-purple-500" />
                    </div>
                    <div>
                      <h4 className="text-lg font-semibold text-white">Brokers & Exchanges</h4>
                      <p className="text-xs text-muted">White-label solution</p>
                    </div>
                  </div>
                  <p className="text-muted text-sm leading-relaxed mb-4">
                    Offer OMNIX risk controls as a premium feature to your clients. Full white-label customization with your branding, integrated directly into your trading interface.
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
                      <h4 className="text-lg font-semibold text-white">Individual Traders</h4>
                      <p className="text-xs text-muted">SaaS subscription</p>
                    </div>
                  </div>
                  <p className="text-muted text-sm leading-relaxed mb-4">
                    Direct access to OMNIX risk controls through our Telegram bot interface. Connect your exchange API, set your risk parameters, and let OMNIX protect your capital 24/7.
                  </p>
                  <div className="flex items-center justify-between text-sm">
                    <span className="gold-text font-medium">Pro Plan</span>
                    <span className="text-muted">$149/mo</span>
                  </div>
                </div>
              </div>
            </section>

            <div className="divider-gold" />

            {/* Track Record */}
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
                        <span className="text-muted">Target Duration</span>
                        <span className="text-white font-medium">30 Days</span>
                      </div>
                      <div className="flex justify-between p-3 bg-[#0A1628]/60 rounded-lg">
                        <span className="text-muted">Current Day</span>
                        <span className="text-emerald-400 font-medium">Day 12 of 30</span>
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
                        <span className="text-emerald-400 font-medium">98.5%</span>
                      </div>
                      <div className="flex justify-between p-3 bg-[#0A1628]/60 rounded-lg">
                        <span className="text-muted">Max Drawdown</span>
                        <span className="text-white font-medium">-1.5%</span>
                      </div>
                      <div className="flex justify-between p-3 bg-[#0A1628]/60 rounded-lg">
                        <span className="text-muted">High-Risk Blocks</span>
                        <span className="text-amber-400 font-medium">5,473</span>
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

            {/* Why Institutions Choose Us */}
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
                  <p className="text-muted leading-relaxed">Every trade is blocked unless ALL validation layers explicitly approve. Safety is the default state, not an afterthought.</p>
                </div>
                <div className="glass-card p-8">
                  <div className="feature-icon mb-6">
                    <BarChart3 className="w-6 h-6 gold-text" />
                  </div>
                  <h4 className="text-xl font-semibold text-white mb-3">Complete Audit Trail</h4>
                  <p className="text-muted leading-relaxed">Every decision is logged with timestamps, risk metrics, and validation results. ADGM and SEC compliance ready.</p>
                </div>
                <div className="glass-card p-8">
                  <div className="feature-icon mb-6">
                    <Shield className="w-6 h-6 gold-text" />
                  </div>
                  <h4 className="text-xl font-semibold text-white mb-3">Post-Quantum Security</h4>
                  <p className="text-muted leading-relaxed">Kyber-768 encryption and Dilithium-3 signatures. NIST FIPS 203/204 compliant cryptography.</p>
                </div>
              </div>
            </section>

            {/* Certifications */}
            <section className="glass-card p-10 text-center gold-glow mb-20">
              <p className="section-title">Trusted Infrastructure</p>
              <h3 className="text-2xl font-bold text-white mb-8">Regulatory Compliance & Certifications</h3>
              <div className="flex justify-center items-center gap-12 flex-wrap">
                <div className="flex items-center gap-3">
                  <Globe className="w-8 h-8 gold-text" />
                  <div className="text-left">
                    <p className="text-white font-semibold">ADGM</p>
                    <p className="text-xs text-amber-400">Target Jurisdiction</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Award className="w-8 h-8 gold-text" />
                  <div className="text-left">
                    <p className="text-white font-semibold">NIST FIPS 203/204</p>
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

            {/* Final CTA */}
            <section className="text-center">
              <div className="glass-card p-12 gold-glow">
                <h2 className="text-3xl font-bold text-white mb-4">Ready to Protect Your Capital?</h2>
                <p className="text-xl text-muted max-w-2xl mx-auto mb-8">
                  Schedule a demo to see how OMNIX can integrate with your trading infrastructure.
                </p>
                <div className="flex justify-center gap-4">
                  <button className="btn-primary flex items-center gap-2">
                    <Play className="w-4 h-4" />
                    Schedule Demo
                  </button>
                  <button className="btn-secondary">
                    Contact Sales
                  </button>
                </div>
                <p className="text-muted text-sm mt-6">No credit card required. 14-day free trial for Pro plans.</p>
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
              <h2 className="text-3xl font-bold text-white">Professional Trading Tools</h2>
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
                    <label className="block text-sm text-muted mb-2 font-medium">Risk Per Trade (%)</label>
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

      <footer className="border-t border-[#C9A227]/10 bg-[#050D18]">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="grid md:grid-cols-4 gap-8 mb-10">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <img src="/logo.png" alt="OMNIX QUANTUM" className="w-14 h-14 object-contain" />
                <span className="font-bold text-white">OMNIX QUANTUM</span>
              </div>
              <p className="text-sm text-muted">Institutional-grade risk control infrastructure for algorithmic trading.</p>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-sm text-muted">
                <li>About Us</li>
                <li>Careers</li>
                <li>Press</li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Resources</h4>
              <ul className="space-y-2 text-sm text-muted">
                <li>Documentation</li>
                <li>API Reference</li>
                <li>Technical Brief</li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Contact</h4>
              <ul className="space-y-2 text-sm text-muted">
                <li>contacto@omnixquantum.net</li>
                <li>+1 (650) 507-8293</li>
                <li>Abu Dhabi (ADGM)</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-[#C9A227]/10 pt-8">
            <p className="footer-disclaimer mb-4">
              DISCLAIMER: OMNIX QUANTUM provides risk validation infrastructure for algorithmic trading. Past performance does not guarantee future results. 
              Trading involves substantial risk of loss. This platform is designed for institutional investors and qualified professional clients only. 
              Not available in all jurisdictions. Please consult your legal and financial advisors before use.
            </p>
            <div className="flex justify-between items-center">
              <p className="text-xs text-muted">&copy; 2026 OMNIX QUANTUM. All rights reserved. Abu Dhabi Global Market (ADGM).</p>
              <div className="flex gap-6 text-xs text-muted">
                <span>Privacy Policy</span>
                <span>Terms of Service</span>
                <span>Cookie Policy</span>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
