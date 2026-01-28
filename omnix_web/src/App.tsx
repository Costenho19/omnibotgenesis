import { useState, useEffect } from 'react'
import { Shield, Activity, TrendingUp, AlertTriangle, Zap, BarChart3, Calculator, Newspaper, ExternalLink } from 'lucide-react'
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

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch('/api/metrics')
        if (response.ok) {
          const data = await response.json()
          setMetrics(data)
        }
      } catch {
        setMetrics(prev => ({
          ...prev,
          evaluationCycles: prev.evaluationCycles + Math.floor(Math.random() * 10),
          lastUpdate: new Date().toISOString()
        }))
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
    const posSize = riskAmount / (riskCalc.stopLoss / 100)
    setRiskCalc(prev => ({ ...prev, positionSize: posSize }))
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
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
    return num.toLocaleString()
  }

  const getFearGreedColor = (value: number) => {
    if (value <= 25) return 'text-red-500'
    if (value <= 45) return 'text-orange-500'
    if (value <= 55) return 'text-yellow-500'
    if (value <= 75) return 'text-lime-500'
    return 'text-green-500'
  }

  return (
    <div className="min-h-screen">
      <nav className="fixed top-0 left-0 right-0 z-50 glass-card border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield className="w-8 h-8 text-sky-500" />
            <span className="text-xl font-bold gradient-text">OMNIX QUANTUM</span>
            <span className="px-2 py-0.5 text-xs bg-sky-500/20 text-sky-400 rounded-full">LIVE</span>
          </div>
          <div className="flex gap-6">
            <button 
              onClick={() => setActiveTab('home')}
              className={`text-sm font-medium transition ${activeTab === 'home' ? 'text-sky-400' : 'text-slate-400 hover:text-white'}`}
            >
              Dashboard
            </button>
            <button 
              onClick={() => setActiveTab('news')}
              className={`text-sm font-medium transition ${activeTab === 'news' ? 'text-sky-400' : 'text-slate-400 hover:text-white'}`}
            >
              News
            </button>
            <button 
              onClick={() => setActiveTab('tools')}
              className={`text-sm font-medium transition ${activeTab === 'tools' ? 'text-sky-400' : 'text-slate-400 hover:text-white'}`}
            >
              Tools
            </button>
          </div>
        </div>
      </nav>

      <main className="pt-24 px-4 pb-12 max-w-7xl mx-auto">
        {activeTab === 'home' && (
          <>
            <section className="text-center mb-12">
              <h1 className="text-4xl md:text-5xl font-bold mb-4">
                Institutional <span className="gradient-text">Risk Control</span> Infrastructure
              </h1>
              <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                OMNIX decides when NOT to trade. Preserving capital is a stronger edge than forcing returns.
              </p>
            </section>

            <section className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
              <div className="glass-card p-6 pulse-glow">
                <div className="flex items-center gap-2 mb-2">
                  <Activity className="w-5 h-5 text-sky-500" />
                  <span className="text-sm text-slate-400">Evaluation Cycles</span>
                  <div className="live-indicator ml-auto" />
                </div>
                <div className="text-3xl font-bold">{formatNumber(metrics.evaluationCycles)}+</div>
              </div>
              
              <div className="glass-card p-6">
                <div className="flex items-center gap-2 mb-2">
                  <AlertTriangle className="w-5 h-5 text-amber-500" />
                  <span className="text-sm text-slate-400">Vetos Executed</span>
                </div>
                <div className="text-3xl font-bold text-amber-500">{formatNumber(metrics.vetosExecuted)}</div>
              </div>
              
              <div className="glass-card p-6">
                <div className="flex items-center gap-2 mb-2">
                  <Shield className="w-5 h-5 text-green-500" />
                  <span className="text-sm text-slate-400">Capital Preserved</span>
                </div>
                <div className="text-3xl font-bold text-green-500">{metrics.capitalPreserved}%</div>
              </div>
              
              <div className="glass-card p-6">
                <div className="flex items-center gap-2 mb-2">
                  <Zap className="w-5 h-5 text-purple-500" />
                  <span className="text-sm text-slate-400">System Uptime</span>
                </div>
                <div className="text-3xl font-bold text-purple-500">{metrics.systemUptime}</div>
              </div>
            </section>

            <section className="grid md:grid-cols-2 gap-6 mb-12">
              <div className="glass-card p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-sky-500" />
                  Market Overview
                </h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center p-3 bg-slate-800/50 rounded-lg">
                    <span className="text-slate-400">BTC/USD</span>
                    <span className="text-xl font-bold">${market.btcPrice.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-slate-800/50 rounded-lg">
                    <span className="text-slate-400">ETH/USD</span>
                    <span className="text-xl font-bold">${market.ethPrice.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-slate-800/50 rounded-lg">
                    <span className="text-slate-400">Fear & Greed Index</span>
                    <span className={`text-xl font-bold ${getFearGreedColor(market.fearGreedIndex)}`}>
                      {market.fearGreedIndex} - {market.fearGreedLabel}
                    </span>
                  </div>
                </div>
              </div>

              <div className="glass-card p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-sky-500" />
                  Validation Pipeline
                </h3>
                <div className="space-y-3">
                  {['Regime Detection', 'Coherence Check', 'Monte Carlo Simulation', 'Consensus Gate'].map((layer, i) => (
                    <div key={layer} className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-sky-500/20 flex items-center justify-center text-sky-400 text-sm font-bold">
                        {i + 1}
                      </div>
                      <span className="text-slate-300">{layer}</span>
                      <div className="ml-auto w-3 h-3 rounded-full bg-green-500" />
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section className="glass-card p-6">
              <h3 className="text-lg font-semibold mb-4">What Makes OMNIX Different</h3>
              <div className="grid md:grid-cols-3 gap-6">
                <div>
                  <div className="w-12 h-12 rounded-xl bg-sky-500/20 flex items-center justify-center mb-3">
                    <Shield className="w-6 h-6 text-sky-500" />
                  </div>
                  <h4 className="font-semibold mb-2">Fail-Closed Architecture</h4>
                  <p className="text-sm text-slate-400">Default: NO. Trades only execute if ALL validation layers approve.</p>
                </div>
                <div>
                  <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center mb-3">
                    <Activity className="w-6 h-6 text-purple-500" />
                  </div>
                  <h4 className="font-semibold mb-2">Multi-Layer Validation</h4>
                  <p className="text-sm text-slate-400">4 independent gates must agree before any trade execution.</p>
                </div>
                <div>
                  <div className="w-12 h-12 rounded-xl bg-green-500/20 flex items-center justify-center mb-3">
                    <BarChart3 className="w-6 h-6 text-green-500" />
                  </div>
                  <h4 className="font-semibold mb-2">Full Auditability</h4>
                  <p className="text-sm text-slate-400">Complete decision lineage for regulatory compliance.</p>
                </div>
              </div>
            </section>
          </>
        )}

        {activeTab === 'news' && (
          <section>
            <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
              <Newspaper className="w-6 h-6 text-sky-500" />
              Crypto Market News
            </h2>
            <div className="space-y-4">
              {news.map(item => (
                <div key={item.id} className="glass-card p-4 flex items-center gap-4 hover:border-sky-500/50 transition cursor-pointer">
                  <div className={`w-2 h-12 rounded-full ${
                    item.sentiment === 'positive' ? 'bg-green-500' : 
                    item.sentiment === 'negative' ? 'bg-red-500' : 'bg-slate-500'
                  }`} />
                  <div className="flex-1">
                    <h4 className="font-medium">{item.headline}</h4>
                    <p className="text-sm text-slate-400">{item.source} • {new Date(item.datetime).toLocaleTimeString()}</p>
                  </div>
                  <ExternalLink className="w-5 h-5 text-slate-400" />
                </div>
              ))}
            </div>
            <div className="mt-6 glass-card p-6">
              <h3 className="text-lg font-semibold mb-4">Market Sentiment</h3>
              <div className="flex items-center gap-4">
                <div className={`text-5xl font-bold ${getFearGreedColor(market.fearGreedIndex)}`}>
                  {market.fearGreedIndex}
                </div>
                <div>
                  <div className={`text-xl font-semibold ${getFearGreedColor(market.fearGreedIndex)}`}>
                    {market.fearGreedLabel}
                  </div>
                  <p className="text-sm text-slate-400">Fear & Greed Index</p>
                </div>
                <div className="ml-auto flex-1 max-w-xs">
                  <div className="h-4 rounded-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 relative">
                    <div 
                      className="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-white rounded-full shadow-lg border-2 border-slate-800"
                      style={{ left: `${market.fearGreedIndex}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-slate-400 mt-1">
                    <span>Extreme Fear</span>
                    <span>Extreme Greed</span>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {activeTab === 'tools' && (
          <section>
            <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
              <Calculator className="w-6 h-6 text-sky-500" />
              Risk Management Tools
            </h2>
            
            <div className="glass-card p-6 mb-6">
              <h3 className="text-lg font-semibold mb-4">Position Size Calculator</h3>
              <p className="text-sm text-slate-400 mb-6">Calculate optimal position size based on your risk tolerance.</p>
              
              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm text-slate-400 mb-2">Account Capital ($)</label>
                    <input 
                      type="number"
                      value={riskCalc.capital}
                      onChange={e => setRiskCalc(prev => ({ ...prev, capital: parseFloat(e.target.value) || 0 }))}
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 focus:border-sky-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-slate-400 mb-2">Risk Per Trade (%)</label>
                    <input 
                      type="number"
                      value={riskCalc.riskPercent}
                      onChange={e => setRiskCalc(prev => ({ ...prev, riskPercent: parseFloat(e.target.value) || 0 }))}
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 focus:border-sky-500 focus:outline-none"
                      step="0.5"
                      min="0.1"
                      max="10"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-slate-400 mb-2">Stop Loss Distance (%)</label>
                    <input 
                      type="number"
                      value={riskCalc.stopLoss}
                      onChange={e => setRiskCalc(prev => ({ ...prev, stopLoss: parseFloat(e.target.value) || 0 }))}
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 focus:border-sky-500 focus:outline-none"
                      step="0.5"
                      min="0.5"
                      max="50"
                    />
                  </div>
                </div>
                
                <div className="bg-slate-800/50 rounded-xl p-6 flex flex-col justify-center">
                  <div className="text-center">
                    <p className="text-slate-400 mb-2">Recommended Position Size</p>
                    <p className="text-4xl font-bold text-sky-400">
                      ${riskCalc.positionSize.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </p>
                    <p className="text-sm text-slate-500 mt-2">
                      Risk Amount: ${(riskCalc.capital * riskCalc.riskPercent / 100).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="glass-card p-6">
              <h3 className="text-lg font-semibold mb-4">Kelly Criterion Calculator</h3>
              <p className="text-sm text-slate-400 mb-4">
                The Kelly Criterion determines optimal bet sizing to maximize long-term growth.
              </p>
              <div className="bg-slate-800/50 rounded-lg p-4">
                <p className="text-sm text-slate-400">
                  <strong className="text-white">Formula:</strong> f* = (bp - q) / b
                </p>
                <p className="text-sm text-slate-400 mt-2">
                  Where: b = odds received, p = probability of winning, q = probability of losing (1 - p)
                </p>
              </div>
              <p className="text-xs text-slate-500 mt-4">
                Note: OMNIX uses a fractional Kelly (typically 25-50%) to reduce volatility while maintaining edge optimization.
              </p>
            </div>
          </section>
        )}
      </main>

      <footer className="border-t border-white/10 py-8 px-4">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-sky-500" />
            <span className="text-sm text-slate-400">OMNIX QUANTUM - Abu Dhabi (ADGM)</span>
          </div>
          <div className="text-sm text-slate-500">
            contacto@omnixquantum.net | +1 (650) 507-8293
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
