import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { Shield, ArrowRight, AlertTriangle, CheckCircle, XCircle, Clock, Building2, TrendingUp, BarChart3, Activity, Layers, Target, Brain, Zap, Umbrella } from 'lucide-react'
import { useLiveMetrics } from '../hooks/useLiveMetrics'

interface CheckpointResult {
  name: string
  genericName: string
  icon: React.ReactNode
  status: 'pending' | 'evaluating' | 'pass' | 'warn' | 'block'
  score: number
  threshold: number
  reasoning: string
  detail: string
}

interface EnergyTrade {
  energySource: string
  contractSize: number
  deliveryWindow: string
  gridCondition: string
  weatherOutlook: string
  regulatoryEnv: string
}

const ENERGY_SOURCES = [
  { value: 'natural_gas', label: 'Natural Gas (Henry Hub)', baseVol: 0.18, avgPrice: 2.85, unit: 'MMBtu', emoji: '🔥' },
  { value: 'crude_oil', label: 'Crude Oil (WTI)', baseVol: 0.22, avgPrice: 78.50, unit: 'barrel', emoji: '🛢️' },
  { value: 'solar', label: 'Solar PPA (Utility-Scale)', baseVol: 0.12, avgPrice: 45.00, unit: 'MWh', emoji: '☀️' },
  { value: 'wind', label: 'Wind Power (Onshore)', baseVol: 0.25, avgPrice: 38.00, unit: 'MWh', emoji: '💨' },
  { value: 'lng', label: 'LNG Spot (Asia-Pacific)', baseVol: 0.32, avgPrice: 12.40, unit: 'MMBtu', emoji: '🚢' },
  { value: 'electricity', label: 'Electricity (Day-Ahead)', baseVol: 0.35, avgPrice: 55.00, unit: 'MWh', emoji: '⚡' },
]

const DELIVERY_WINDOWS = [
  { value: 'spot', label: 'Spot / Same-Day', risk: 0.35, premium: 1.15 },
  { value: 'week_ahead', label: 'Week-Ahead', risk: 0.22, premium: 1.05 },
  { value: 'month_ahead', label: 'Month-Ahead', risk: 0.15, premium: 1.00 },
  { value: 'quarter', label: 'Quarterly Forward', risk: 0.10, premium: 0.95 },
  { value: 'annual', label: 'Annual Contract', risk: 0.08, premium: 0.90 },
]

const GRID_CONDITIONS = [
  { value: 'stable', label: 'Stable Grid (Normal Load)', factor: 0.90 },
  { value: 'peak', label: 'Peak Demand (High Load)', factor: 0.55 },
  { value: 'off_peak', label: 'Off-Peak (Low Demand)', factor: 0.85 },
  { value: 'congestion', label: 'Transmission Congestion', factor: 0.35 },
  { value: 'emergency', label: 'Grid Emergency / Rolling Blackouts', factor: 0.10 },
]

const WEATHER_OUTLOOK = [
  { value: 'favorable', label: 'Favorable (Mild, Predictable)', factor: 0.90 },
  { value: 'seasonal', label: 'Seasonal Normal', factor: 0.75 },
  { value: 'volatile', label: 'Volatile (Storm Watch)', factor: 0.40 },
  { value: 'extreme', label: 'Extreme Event (Hurricane / Polar Vortex)', factor: 0.15 },
]

const REGULATORY_ENV = [
  { value: 'stable', label: 'Stable Regulatory Framework', factor: 0.90 },
  { value: 'transitioning', label: 'Energy Transition Policy (IRA/EU Green Deal)', factor: 0.70 },
  { value: 'uncertain', label: 'Regulatory Uncertainty', factor: 0.45 },
  { value: 'hostile', label: 'Adverse Regulation (Carbon Tax / Price Caps)', factor: 0.20 },
]

function evaluateCheckpoints(trade: EnergyTrade): CheckpointResult[] {
  const sourceData = ENERGY_SOURCES.find(s => s.value === trade.energySource) || ENERGY_SOURCES[0]
  const deliveryData = DELIVERY_WINDOWS.find(d => d.value === trade.deliveryWindow) || DELIVERY_WINDOWS[0]
  const gridData = GRID_CONDITIONS.find(g => g.value === trade.gridCondition) || GRID_CONDITIONS[0]
  const weatherData = WEATHER_OUTLOOK.find(w => w.value === trade.weatherOutlook) || WEATHER_OUTLOOK[0]
  const regData = REGULATORY_ENV.find(r => r.value === trade.regulatoryEnv) || REGULATORY_ENV[0]

  const baseConfidence = (1 - sourceData.baseVol) * 0.4 + gridData.factor * 0.3 + weatherData.factor * 0.3
  const deliveryAdjust = deliveryData.risk * 0.25
  const adjustedConfidence = Math.min(0.98, Math.max(0.05, baseConfidence - deliveryAdjust))
  const forecastScore = Math.round(adjustedConfidence * 100)

  const sizeRatio = trade.contractSize / 500
  const sourceExposure = sourceData.baseVol * 80
  const deliveryExposure = deliveryData.risk * 60
  const concentrationRisk = Math.min(100, Math.round((sizeRatio * 25 + sourceExposure + deliveryExposure) * 0.5))
  const exposureScore = Math.max(0, 100 - concentrationRisk)

  const gridSignal = Math.round(gridData.factor * 100)
  const weatherSignal = Math.round(weatherData.factor * 100)
  const deliverySignal = Math.max(0, Math.round((1 - deliveryData.risk) * 100))
  const supplyDemandCoherence = Math.round(gridSignal * 0.35 + weatherSignal * 0.35 + deliverySignal * 0.30)

  const gridTrend = gridData.factor >= 0.8 ? 85 : gridData.factor >= 0.5 ? 60 : gridData.factor >= 0.3 ? 35 : 15
  const weatherTrend = weatherData.factor >= 0.7 ? 80 : weatherData.factor >= 0.4 ? 50 : 20
  const trendScore = Math.round(gridTrend * 0.5 + weatherTrend * 0.3 + (1 - sourceData.baseVol) * 100 * 0.2)

  const regStress = regData.factor
  const weatherStress = weatherData.factor
  const gridStress = gridData.factor
  const stressScore = Math.round(regStress * 40 + weatherStress * 35 + gridStress * 25)

  const signals = [forecastScore, exposureScore, supplyDemandCoherence, trendScore, stressScore]
  const avg = signals.reduce((a, b) => a + b, 0) / signals.length
  const variance = signals.reduce((a, b) => a + Math.pow(b - avg, 2), 0) / signals.length
  const divergence = Math.sqrt(variance)
  const logicScore = Math.round(Math.max(0, Math.min(100, 100 - divergence * 2.2)))

  return [
    {
      name: 'Price Forecast Confidence',
      genericName: 'CP-1: Is this likely to succeed?',
      icon: <Target className="w-5 h-5" />,
      status: 'pending',
      score: forecastScore,
      threshold: 55,
      reasoning: forecastScore >= 55
        ? `Price forecast confidence at ${forecastScore}% — ${sourceData.label} volatility ${(sourceData.baseVol * 100).toFixed(0)}% with ${deliveryData.label} delivery supports execution`
        : `Price forecast confidence only ${forecastScore}% — ${sourceData.label} volatility ${(sourceData.baseVol * 100).toFixed(0)}% combined with ${deliveryData.label} delivery creates excessive uncertainty`,
      detail: `Source vol: ${(sourceData.baseVol * 100).toFixed(0)}% | Grid factor: ${(gridData.factor * 100).toFixed(0)}% | Weather: ${(weatherData.factor * 100).toFixed(0)}% | Delivery risk: ${(deliveryData.risk * 100).toFixed(0)}% → Confidence: ${forecastScore}%`
    },
    {
      name: 'Grid Exposure Limits',
      genericName: 'CP-2: Would this exceed safe exposure?',
      icon: <Shield className="w-5 h-5" />,
      status: 'pending',
      score: exposureScore,
      threshold: 45,
      reasoning: exposureScore >= 45
        ? `Portfolio exposure within grid capacity limits — ${trade.contractSize} ${sourceData.unit} contract within concentration thresholds`
        : `Excessive grid exposure — ${trade.contractSize} ${sourceData.unit} contract creates ${concentrationRisk}% concentration risk in ${sourceData.label}`,
      detail: `Size ratio: ${sizeRatio.toFixed(1)}x | Source exposure: ${sourceExposure.toFixed(0)}% | Delivery exposure: ${deliveryExposure.toFixed(0)}% | Concentration: ${concentrationRisk}% → Score: ${exposureScore}/100`
    },
    {
      name: 'Supply-Demand Coherence',
      genericName: 'CP-3: Do multiple models agree?',
      icon: <Layers className="w-5 h-5" />,
      status: 'pending',
      score: supplyDemandCoherence,
      threshold: 50,
      reasoning: supplyDemandCoherence >= 50
        ? `Grid conditions, weather outlook, and delivery window signals align (${supplyDemandCoherence}% coherence)`
        : `Conflicting signals — grid ${gridData.label.toLowerCase()} suggests ${gridSignal >= 60 ? 'execute' : 'hold'} but weather (${weatherData.label.toLowerCase()}) and delivery window diverge`,
      detail: `Grid signal: ${gridSignal} | Weather signal: ${weatherSignal} | Delivery signal: ${deliverySignal} → Coherence: ${supplyDemandCoherence}%`
    },
    {
      name: 'Price Trend Persistence',
      genericName: 'CP-4: Is this sustained, not noise?',
      icon: <TrendingUp className="w-5 h-5" />,
      status: 'pending',
      score: trendScore,
      threshold: 40,
      reasoning: trendScore >= 40
        ? `Grid and weather trends confirm sustained conditions — not transient volatility spike`
        : `Current conditions appear transient — insufficient trend persistence for confident execution`,
      detail: `Grid trend: ${gridTrend} | Weather trend: ${weatherTrend} | Vol stability: ${((1 - sourceData.baseVol) * 100).toFixed(0)}% → Persistence: ${trendScore}/100`
    },
    {
      name: 'Regulatory & Climate Stress',
      genericName: 'CP-5: What if conditions deteriorate?',
      icon: <AlertTriangle className="w-5 h-5" />,
      status: 'pending',
      score: stressScore,
      threshold: 35,
      reasoning: stressScore >= 35
        ? `Regulatory environment (${regData.label.toLowerCase()}) and climate outlook provide adequate margin under stress scenarios`
        : `Stress test failed — ${regData.label.toLowerCase()} regulation combined with ${weatherData.label.toLowerCase()} weather creates unacceptable tail risk`,
      detail: `Regulatory: ${(regStress * 100).toFixed(0)}% | Weather stress: ${(weatherStress * 100).toFixed(0)}% | Grid stress: ${(gridStress * 100).toFixed(0)}% → Resilience: ${stressScore}/100`
    },
    {
      name: 'Signal Contradiction',
      genericName: 'CP-6: Are signals contradicting each other?',
      icon: <Brain className="w-5 h-5" />,
      status: 'pending',
      score: logicScore,
      threshold: 40,
      reasoning: logicScore >= 40
        ? `Internal signal divergence is low — energy market signals are consistent (${logicScore}%)`
        : `High internal contradiction detected — divergence score ${divergence.toFixed(1)} indicates conflicting risk assessment across checkpoints`,
      detail: `Signal variance: ${divergence.toFixed(1)} | Consistency: ${logicScore}% | ${logicScore < 40 ? 'CONTRADICTORY' : logicScore < 60 ? 'TENSIONED' : 'ALIGNED'}`
    },
  ]
}

export default function EnergyGovernanceDemo() {
  const { metrics: liveMetrics, isLive, formatNumberFull } = useLiveMetrics()
  const [trade, setTrade] = useState<EnergyTrade>({
    energySource: 'natural_gas',
    contractSize: 250,
    deliveryWindow: 'month_ahead',
    gridCondition: 'stable',
    weatherOutlook: 'seasonal',
    regulatoryEnv: 'stable',
  })

  const [checkpoints, setCheckpoints] = useState<CheckpointResult[]>([])
  const [isEvaluating, setIsEvaluating] = useState(false)
  const [evaluationComplete, setEvaluationComplete] = useState(false)
  const [_currentCheckpoint, setCurrentCheckpoint] = useState(-1)
  const evaluationRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const currentSource = ENERGY_SOURCES.find(s => s.value === trade.energySource) || ENERGY_SOURCES[0]

  const runGovernanceEvaluation = () => {
    const results = evaluateCheckpoints(trade)
    const finalResults = results.map(cp => {
      const passed = cp.score >= cp.threshold
      const finalStatus: 'pass' | 'warn' | 'block' = passed ? (cp.score >= cp.threshold + 15 ? 'pass' : 'warn') : 'block'
      return { ...cp, finalStatus }
    })

    setCheckpoints(results)
    setIsEvaluating(true)
    setEvaluationComplete(false)
    setCurrentCheckpoint(0)

    let step = 0
    const animate = () => {
      if (step < finalResults.length) {
        setCheckpoints(prev => prev.map((cp, i) => {
          if (i === step) return { ...cp, status: 'evaluating' as const }
          return cp
        }))

        setTimeout(() => {
          const finalStatus = finalResults[step].finalStatus
          setCheckpoints(prev => prev.map((cp, i) => {
            if (i === step) return { ...cp, status: finalStatus }
            return cp
          }))
          setCurrentCheckpoint(step + 1)
          step++
          evaluationRef.current = setTimeout(animate, 600)
        }, 800)
      } else {
        setCheckpoints(finalResults.map(fr => ({ ...fr, status: fr.finalStatus })))
        setIsEvaluating(false)
        setEvaluationComplete(true)
      }
    }

    evaluationRef.current = setTimeout(animate, 400)
  }

  useEffect(() => {
    return () => {
      if (evaluationRef.current) clearTimeout(evaluationRef.current)
    }
  }, [])

  const getGovernanceDecision = () => {
    if (!evaluationComplete || checkpoints.length === 0) return null
    const blocked = checkpoints.filter(cp => cp.status === 'block')
    const warned = checkpoints.filter(cp => cp.status === 'warn')
    const passed = checkpoints.filter(cp => cp.status === 'pass')

    if (blocked.length >= 2) return { decision: 'BLOCK', color: 'text-red-500', bg: 'bg-red-500/10 border-red-500/30', reason: `${blocked.length} checkpoints blocked. Governance recommendation: BLOCK this energy trade — risk profile exceeds acceptable thresholds for automated execution.`, passed: passed.length + warned.length }
    if (blocked.length === 1) return { decision: 'HOLD', color: 'text-amber-500', bg: 'bg-amber-500/10 border-amber-500/30', reason: `1 checkpoint blocked (${blocked[0].name}). Governance recommendation: HOLD — escalate to senior energy trader for manual review of ${blocked[0].name.toLowerCase()}.`, passed: passed.length + warned.length }
    if (warned.length >= 3) return { decision: 'HOLD', color: 'text-amber-500', bg: 'bg-amber-500/10 border-amber-500/30', reason: `${warned.length} checkpoints at marginal levels. Governance recommendation: HOLD — cumulative marginal risk requires human validation and hedging strategy review.`, passed: passed.length + warned.length }
    return { decision: 'EXECUTE', color: 'text-emerald-500', bg: 'bg-emerald-500/10 border-emerald-500/30', reason: 'All checkpoints passed. Governance recommendation: EXECUTE — trade meets all governance thresholds for automated execution.', passed: passed.length + warned.length }
  }

  const decision = getGovernanceDecision()

  const resetEvaluation = () => {
    setCheckpoints([])
    setEvaluationComplete(false)
    setCurrentCheckpoint(-1)
    setIsEvaluating(false)
    if (evaluationRef.current) clearTimeout(evaluationRef.current)
  }

  return (
    <div className="min-h-screen bg-institutional">
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#050D18]/90 backdrop-blur-xl border-b border-[#C9A227]/10">
        <div className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/">
              <img src="/logo.png" alt="OMNIX QUANTUM" className="w-12 h-12 object-contain" />
            </Link>
            <div>
              <span className="text-lg font-bold text-white tracking-tight">OMNIX QUANTUM</span>
              <span className="ml-3 px-2 py-0.5 text-[10px] font-semibold bg-orange-500/20 text-orange-400 rounded uppercase tracking-wider">Energy Demo</span>
            </div>
          </div>
          <div className="flex items-center gap-8">
            <Link to="/" className="nav-link">Home</Link>
            <Link to="/governance-demo" className="nav-link">Credit Demo</Link>
            <Link to="/governance-demo-insurance" className="nav-link">Insurance Demo</Link>
            <Link to="/governance-demo-biotech" className="nav-link">Biotech Demo</Link>
            <Link to="/institutional" className="nav-link">Technical Details</Link>
            <a href="https://wa.me/16505078293?text=Hi%2C%20I%27m%20interested%20in%20OMNIX%20Energy%20Governance" target="_blank" rel="noopener noreferrer" className="btn-primary text-sm px-5 py-2">Talk to Us</a>
          </div>
        </div>
      </nav>

      <main className="pt-32 px-6 pb-20 max-w-7xl mx-auto">
        <section className="text-center mb-16 animate-fade-in-up">
          <p className="section-title">Energy Trading Governance</p>
          <h1 className="heading-xl text-white mb-6">
            Govern Every Megawatt.<br />
            <span className="gold-gradient">Before It Trades.</span>
          </h1>
          <p className="text-xl text-muted max-w-3xl mx-auto mb-4 leading-relaxed">
            This interactive demo shows how OMNIX's governance architecture
            applies to energy trading decisions — the same pattern validated across {formatNumberFull(liveMetrics.evaluation_cycles)}
            evaluation cycles in digital asset trading (internal dataset). All verticals run through the same 8-checkpoint fail-closed governance engine.
          </p>
          <p className="text-sm text-[#64748B] max-w-2xl mx-auto">
            Adjust energy trade parameters and run the governance evaluation to see each checkpoint assess the risk in real time.
          </p>
        </section>

        <div className="grid lg:grid-cols-5 gap-8 mb-12">
          <div className="lg:col-span-2">
            <div className="glass-card p-8 sticky top-32">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-full bg-orange-500/20 flex items-center justify-center">
                  <Zap className="w-5 h-5 text-orange-400" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">Energy Trade Setup</h3>
                  <p className="text-xs text-muted">Configure trade parameters</p>
                </div>
              </div>

              <div className="space-y-5">
                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Energy Source</label>
                  <select
                    value={trade.energySource}
                    onChange={(e) => { resetEvaluation(); setTrade(prev => ({ ...prev, energySource: e.target.value })) }}
                    className="w-full bg-[#0A1628] border border-[#C9A227]/20 rounded-lg px-4 py-3 text-white text-sm focus:border-[#C9A227] focus:outline-none"
                  >
                    {ENERGY_SOURCES.map(s => <option key={s.value} value={s.value}>{s.emoji} {s.label} (Vol: {(s.baseVol * 100).toFixed(0)}%)</option>)}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Contract Size ({currentSource.unit})</label>
                  <div className="flex items-center gap-3">
                    <input
                      type="range"
                      min={10}
                      max={2000}
                      step={10}
                      value={trade.contractSize}
                      onChange={(e) => { resetEvaluation(); setTrade(prev => ({ ...prev, contractSize: parseInt(e.target.value) })) }}
                      className="flex-1 accent-[#C9A227]"
                    />
                    <span className="text-white font-semibold text-sm w-24 text-right">{trade.contractSize} {currentSource.unit}</span>
                  </div>
                  <p className="text-xs text-[#64748B] mt-1">Est. value: ${(trade.contractSize * currentSource.avgPrice).toLocaleString()}</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Delivery Window</label>
                  <select
                    value={trade.deliveryWindow}
                    onChange={(e) => { resetEvaluation(); setTrade(prev => ({ ...prev, deliveryWindow: e.target.value })) }}
                    className="w-full bg-[#0A1628] border border-[#C9A227]/20 rounded-lg px-4 py-3 text-white text-sm focus:border-[#C9A227] focus:outline-none"
                  >
                    {DELIVERY_WINDOWS.map(d => <option key={d.value} value={d.value}>{d.label}</option>)}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Grid Condition</label>
                  <select
                    value={trade.gridCondition}
                    onChange={(e) => { resetEvaluation(); setTrade(prev => ({ ...prev, gridCondition: e.target.value })) }}
                    className="w-full bg-[#0A1628] border border-[#C9A227]/20 rounded-lg px-4 py-3 text-white text-sm focus:border-[#C9A227] focus:outline-none"
                  >
                    {GRID_CONDITIONS.map(g => <option key={g.value} value={g.value}>{g.label}</option>)}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Weather Outlook</label>
                  <select
                    value={trade.weatherOutlook}
                    onChange={(e) => { resetEvaluation(); setTrade(prev => ({ ...prev, weatherOutlook: e.target.value })) }}
                    className="w-full bg-[#0A1628] border border-[#C9A227]/20 rounded-lg px-4 py-3 text-white text-sm focus:border-[#C9A227] focus:outline-none"
                  >
                    {WEATHER_OUTLOOK.map(w => <option key={w.value} value={w.value}>{w.label}</option>)}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Regulatory Environment</label>
                  <select
                    value={trade.regulatoryEnv}
                    onChange={(e) => { resetEvaluation(); setTrade(prev => ({ ...prev, regulatoryEnv: e.target.value })) }}
                    className="w-full bg-[#0A1628] border border-[#C9A227]/20 rounded-lg px-4 py-3 text-white text-sm focus:border-[#C9A227] focus:outline-none"
                  >
                    {REGULATORY_ENV.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
                  </select>
                </div>

                <button
                  onClick={runGovernanceEvaluation}
                  disabled={isEvaluating}
                  className={`w-full btn-primary flex items-center justify-center gap-2 py-4 ${isEvaluating ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {isEvaluating ? (
                    <>
                      <Activity className="w-5 h-5 animate-spin" />
                      Evaluating...
                    </>
                  ) : (
                    <>
                      <Zap className="w-5 h-5" />
                      Run Energy Governance
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          <div className="lg:col-span-3 space-y-4">
            {checkpoints.length === 0 ? (
              <div className="glass-card p-12 text-center">
                <div className="w-20 h-20 rounded-full bg-orange-500/10 flex items-center justify-center mx-auto mb-6">
                  <Zap className="w-10 h-10 text-orange-400" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">8-Checkpoint Energy Governance Engine</h3>
                <p className="text-muted max-w-md mx-auto mb-8">
                  Configure energy trade parameters and click "Run Energy Governance" to see each checkpoint evaluate the risk in real time.
                </p>
                <div className="grid grid-cols-3 gap-4 max-w-lg mx-auto">
                  {[
                    { icon: <Target className="w-4 h-4" />, label: 'Forecast' },
                    { icon: <Shield className="w-4 h-4" />, label: 'Exposure' },
                    { icon: <Layers className="w-4 h-4" />, label: 'Coherence' },
                    { icon: <TrendingUp className="w-4 h-4" />, label: 'Trend' },
                    { icon: <AlertTriangle className="w-4 h-4" />, label: 'Stress Test' },
                    { icon: <Brain className="w-4 h-4" />, label: 'Contradiction' },
                  ].map((cp, i) => (
                    <div key={i} className="flex flex-col items-center gap-2 p-3 rounded-lg bg-[#0A1628]/40 border border-orange-500/10">
                      <div className="text-orange-400">{cp.icon}</div>
                      <span className="text-xs text-muted">{cp.label}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <>
                {checkpoints.map((cp, index) => (
                  <div
                    key={index}
                    className={`glass-card p-6 transition-all duration-500 ${
                      cp.status === 'evaluating' ? 'border-orange-500/60 shadow-lg shadow-orange-500/10' :
                      cp.status === 'pass' ? 'border-emerald-500/30' :
                      cp.status === 'warn' ? 'border-amber-500/30' :
                      cp.status === 'block' ? 'border-red-500/30' :
                      'opacity-40'
                    }`}
                    style={{ animationDelay: `${index * 0.1}s` }}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                          cp.status === 'evaluating' ? 'bg-orange-500/20 text-orange-400 animate-pulse' :
                          cp.status === 'pass' ? 'bg-emerald-500/20 text-emerald-400' :
                          cp.status === 'warn' ? 'bg-amber-500/20 text-amber-400' :
                          cp.status === 'block' ? 'bg-red-500/20 text-red-400' :
                          'bg-[#1E293B] text-[#64748B]'
                        }`}>
                          {cp.icon}
                        </div>
                        <div>
                          <h4 className="text-white font-medium">{cp.name}</h4>
                          <p className="text-xs text-muted">{cp.genericName}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {cp.status === 'evaluating' && (
                          <span className="text-xs text-orange-400 font-medium uppercase tracking-wider animate-pulse">Evaluating...</span>
                        )}
                        {cp.status === 'pass' && (
                          <span className="flex items-center gap-1 text-xs text-emerald-400 font-medium uppercase tracking-wider">
                            <CheckCircle className="w-4 h-4" /> PASS
                          </span>
                        )}
                        {cp.status === 'warn' && (
                          <span className="flex items-center gap-1 text-xs text-amber-400 font-medium uppercase tracking-wider">
                            <Clock className="w-4 h-4" /> MARGINAL
                          </span>
                        )}
                        {cp.status === 'block' && (
                          <span className="flex items-center gap-1 text-xs text-red-400 font-medium uppercase tracking-wider">
                            <XCircle className="w-4 h-4" /> BLOCKED
                          </span>
                        )}
                      </div>
                    </div>

                    {cp.status !== 'pending' && (
                      <div className="mt-3 space-y-2 animate-fade-in-up" style={{ animationDuration: '0.4s' }}>
                        <div className="flex items-center gap-3">
                          <div className="flex-1 h-2 bg-[#0A1628] rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all duration-1000 ${
                                cp.status === 'pass' ? 'bg-emerald-500' :
                                cp.status === 'warn' ? 'bg-amber-500' :
                                cp.status === 'block' ? 'bg-red-500' :
                                'bg-orange-500'
                              }`}
                              style={{ width: cp.status === 'evaluating' ? '60%' : (cp.status === 'pass' || cp.status === 'warn') ? '100%' : '22%' }}
                            />
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}

                {decision && evaluationComplete && (
                  <div className={`glass-card p-8 border ${decision.bg} mt-6`}>
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className={`w-12 h-12 rounded-full flex items-center justify-center ${decision.bg}`}>
                          {decision.decision === 'EXECUTE' ? <CheckCircle className={`w-6 h-6 ${decision.color}`} /> :
                           decision.decision === 'HOLD' ? <Clock className={`w-6 h-6 ${decision.color}`} /> :
                           <XCircle className={`w-6 h-6 ${decision.color}`} />}
                        </div>
                        <div>
                          <p className="text-xs text-muted uppercase tracking-wider">Governance Decision</p>
                          <h3 className={`text-2xl font-bold ${decision.color}`}>{decision.decision}</h3>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-muted">Checkpoints Passed</p>
                        <p className="text-white font-semibold">
                          {decision.passed}/6
                        </p>
                      </div>
                    </div>
                    <p className="text-muted text-sm">{decision.reason}</p>
                    <div className="mt-4 pt-4 border-t border-[#C9A227]/10">
                      <p className="text-xs text-[#64748B]">
                        Decision Trace ID: GOV-NRG-{Date.now().toString(36).toUpperCase()} | Architecture: 8-Checkpoint Fail-Closed | Engine: OMNIX Governance Core v1.0
                      </p>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        <div className="divider-gold" />

        <section className="mb-16">
          <div className="text-center mb-12">
            <p className="section-title">Multi-Vertical Governance</p>
            <h2 className="text-3xl font-bold text-white">Same 8 Checkpoints. Every Domain.</h2>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="glass-card p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center">
                  <BarChart3 className="w-5 h-5 text-emerald-400" />
                </div>
                <div>
                  <h4 className="text-white font-medium">Digital Asset Trading</h4>
                  <span className="text-xs text-emerald-400 font-medium">VALIDATED</span>
                </div>
              </div>
              <div className="space-y-1.5 text-sm text-muted">
                <p><span className="text-white">CP-1:</span> Monte Carlo (10K paths)</p>
                <p><span className="text-white">CP-2:</span> VaR95 + max drawdown</p>
                <p><span className="text-white">CP-3:</span> EMA + HMM + Kalman</p>
                <p><span className="text-white">CP-4:</span> Edge Confirmation</p>
                <p><span className="text-white">CP-5:</span> Black Swan detector</p>
                <p><span className="text-white">CP-6:</span> Contradiction Index</p>
              </div>
              <div className="mt-4 pt-3 border-t border-emerald-500/10">
                <p className="text-xs text-emerald-400">{isLive ? '🟢' : '⏳'} {formatNumberFull(liveMetrics.evaluation_cycles)} cycles | {liveMetrics.capital_preserved_pct}% preserved</p>
              </div>
            </div>

            <div className="glass-card p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-[#C9A227]/20 flex items-center justify-center">
                  <Building2 className="w-5 h-5 gold-text" />
                </div>
                <div>
                  <h4 className="text-white font-medium">Credit / Lending</h4>
                  <Link to="/governance-demo" className="text-xs text-[#C9A227] font-medium hover:text-white transition-colors">VIEW DEMO →</Link>
                </div>
              </div>
              <div className="space-y-1.5 text-sm text-muted">
                <p><span className="text-white">CP-1:</span> Default probability</p>
                <p><span className="text-white">CP-2:</span> Exposure limits</p>
                <p><span className="text-white">CP-3:</span> Credit + DTI coherence</p>
                <p><span className="text-white">CP-4:</span> Income persistence</p>
                <p><span className="text-white">CP-5:</span> Recession stress</p>
                <p><span className="text-white">CP-6:</span> Contradiction check</p>
              </div>
              <div className="mt-4 pt-3 border-t border-[#C9A227]/10">
                <p className="text-xs text-[#C9A227]">Interactive demo available</p>
              </div>
            </div>

            <div className="glass-card p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center">
                  <Umbrella className="w-5 h-5 text-blue-400" />
                </div>
                <div>
                  <h4 className="text-white font-medium">Insurance</h4>
                  <Link to="/governance-demo-insurance" className="text-xs text-blue-400 font-medium hover:text-white transition-colors">VIEW DEMO →</Link>
                </div>
              </div>
              <div className="space-y-1.5 text-sm text-muted">
                <p><span className="text-white">CP-1:</span> Claim probability</p>
                <p><span className="text-white">CP-2:</span> Coverage exposure</p>
                <p><span className="text-white">CP-3:</span> Underwriting coherence</p>
                <p><span className="text-white">CP-4:</span> Claims trend</p>
                <p><span className="text-white">CP-5:</span> Catastrophe stress</p>
                <p><span className="text-white">CP-6:</span> Contradiction check</p>
              </div>
              <div className="mt-4 pt-3 border-t border-blue-500/10">
                <p className="text-xs text-blue-400">Interactive demo available</p>
              </div>
            </div>

            <div className="glass-card p-6 border-orange-500/30">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-orange-500/20 flex items-center justify-center">
                  <Zap className="w-5 h-5 text-orange-400" />
                </div>
                <div>
                  <h4 className="text-white font-medium">Energy Trading</h4>
                  <span className="text-xs text-orange-400 font-medium">DEMO ABOVE</span>
                </div>
              </div>
              <div className="space-y-1.5 text-sm text-muted">
                <p><span className="text-white">CP-1:</span> Price forecast</p>
                <p><span className="text-white">CP-2:</span> Grid exposure</p>
                <p><span className="text-white">CP-3:</span> Supply-demand coherence</p>
                <p><span className="text-white">CP-4:</span> Price persistence</p>
                <p><span className="text-white">CP-5:</span> Regulatory stress</p>
                <p><span className="text-white">CP-6:</span> Contradiction check</p>
              </div>
              <div className="mt-4 pt-3 border-t border-orange-500/10">
                <p className="text-xs text-orange-400">Interactive demo — energy governance</p>
              </div>
            </div>
          </div>
        </section>

        <section className="glass-card p-10 text-center mb-16" style={{ borderColor: 'rgba(249, 115, 22, 0.3)' }}>
          <h2 className="text-2xl font-bold text-white mb-4">Four Verticals. One Governance Engine.</h2>
          <p className="text-muted max-w-2xl mx-auto mb-6">
            OMNIX demonstrates governance across four distinct domains — trading, credit, insurance, and energy.
            Each uses the same 8-checkpoint fail-closed governance architecture with domain-specific signals.
            The core engine is validated across {formatNumberFull(liveMetrics.evaluation_cycles)} evaluation cycles.
          </p>
          <div className="grid grid-cols-4 gap-6 max-w-xl mx-auto mb-8">
            <div>
              <div className="text-2xl font-bold text-white">{formatNumberFull(liveMetrics.evaluation_cycles)}</div>
              <div className="text-xs text-muted">Evaluation Cycles {isLive && '🟢'}</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-emerald-400">{liveMetrics.capital_preserved_pct}%</div>
              <div className="text-xs text-muted">Capital Preserved*</div>
            </div>
            <div>
              <div className="text-2xl font-bold gold-text">8</div>
              <div className="text-xs text-muted">Checkpoints</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-orange-400">{liveMetrics.verticals_demo}</div>
              <div className="text-xs text-muted">Verticals</div>
            </div>
          </div>
          <a href="https://wa.me/16505078293?text=Hi%2C%20I%20saw%20the%20energy%20governance%20demo%20and%20I%27m%20interested" target="_blank" rel="noopener noreferrer" className="btn-primary inline-flex items-center gap-2">
            Talk to Us About Multi-Vertical Governance
            <ArrowRight className="w-4 h-4" />
          </a>
        </section>

        <div className="text-center">
          <p className="text-xs text-[#475569] max-w-2xl mx-auto leading-relaxed">
            This is a governance architecture demonstration. The energy evaluation shown uses simplified market models
            for illustrative purposes. Production energy governance would integrate with real-time grid data (CAISO, ERCOT, PJM),
            weather APIs, commodity exchanges, and regulatory compliance frameworks. OMNIX's core 8-checkpoint architecture is
            validated in digital asset trading across {formatNumberFull(liveMetrics.evaluation_cycles)} evaluation cycles (internal dataset, not externally audited).
            See ADR-026 for technical architecture details.
          </p>
        </div>
      </main>

      <footer className="border-t border-[#C9A227]/10 py-12 px-6">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-3">
            <img src="/logo.png" alt="OMNIX" className="w-10 h-10 object-contain" />
            <span className="text-muted text-sm">&copy; 2026 OMNIX QUANTUM. All rights reserved.</span>
          </div>
          <div className="flex items-center gap-6">
            <Link to="/" className="text-muted hover:text-white text-sm transition-colors">Home</Link>
            <Link to="/governance-demo" className="text-muted hover:text-white text-sm transition-colors">Credit Demo</Link>
            <Link to="/governance-demo-insurance" className="text-muted hover:text-white text-sm transition-colors">Insurance Demo</Link>
            <Link to="/institutional" className="text-muted hover:text-white text-sm transition-colors">Technical Details</Link>
            <a href="https://wa.me/16505078293" target="_blank" rel="noopener noreferrer" className="text-muted hover:text-white text-sm transition-colors">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  )
}
