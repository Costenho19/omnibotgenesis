import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { Shield, ArrowRight, AlertTriangle, CheckCircle, XCircle, Clock, Building2, CreditCard, TrendingUp, BarChart3, Zap, Activity, Layers, Target, Brain } from 'lucide-react'

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

interface LoanApplication {
  loanAmount: number
  creditScore: number
  dtiRatio: number
  sector: string
  incomeStability: string
  marketCondition: string
}

const SECTORS = [
  { value: 'technology', label: 'Technology', risk: 0.12 },
  { value: 'healthcare', label: 'Healthcare', risk: 0.08 },
  { value: 'retail', label: 'Retail', risk: 0.22 },
  { value: 'real_estate', label: 'Real Estate', risk: 0.18 },
  { value: 'energy', label: 'Energy', risk: 0.25 },
  { value: 'manufacturing', label: 'Manufacturing', risk: 0.15 },
]

const INCOME_STABILITY = [
  { value: 'stable_growing', label: 'Stable & Growing (2+ years)', factor: 0.95 },
  { value: 'stable', label: 'Stable (1-2 years)', factor: 0.80 },
  { value: 'variable', label: 'Variable / Contract', factor: 0.55 },
  { value: 'declining', label: 'Declining Trend', factor: 0.30 },
]

const MARKET_CONDITIONS = [
  { value: 'expansion', label: 'Economic Expansion', factor: 0.90 },
  { value: 'stable', label: 'Stable / Neutral', factor: 0.75 },
  { value: 'uncertainty', label: 'Elevated Uncertainty', factor: 0.45 },
  { value: 'contraction', label: 'Contraction / Recession', factor: 0.20 },
]

function evaluateCheckpoints(app: LoanApplication): CheckpointResult[] {
  const sectorData = SECTORS.find(s => s.value === app.sector) || SECTORS[0]
  const incomeData = INCOME_STABILITY.find(i => i.value === app.incomeStability) || INCOME_STABILITY[0]
  const marketData = MARKET_CONDITIONS.find(m => m.value === app.marketCondition) || MARKET_CONDITIONS[0]

  const baseDefaultProb = (1 - (app.creditScore - 300) / 550) * 0.3
  const dtiPenalty = app.dtiRatio > 43 ? (app.dtiRatio - 43) * 0.008 : 0
  const adjustedDefault = Math.min(0.95, Math.max(0.01, baseDefaultProb + sectorData.risk * 0.3 + dtiPenalty))
  const probabilityScore = Math.round((1 - adjustedDefault) * 100)

  const loanToIncome = app.loanAmount / 80000
  const sectorExposure = sectorData.risk * 100
  const concentrationRisk = Math.min(100, Math.round(loanToIncome * 20 + sectorExposure * 1.5))
  const riskScore = 100 - concentrationRisk

  const creditSignal = app.creditScore >= 700 ? 90 : app.creditScore >= 650 ? 70 : app.creditScore >= 580 ? 50 : 30
  const dtiSignal = app.dtiRatio <= 30 ? 90 : app.dtiRatio <= 43 ? 65 : app.dtiRatio <= 50 ? 40 : 20
  const sectorSignal = (1 - sectorData.risk) * 100
  const coherenceScore = Math.round((creditSignal * 0.35 + dtiSignal * 0.30 + sectorSignal * 0.35))

  const trendScore = Math.round(incomeData.factor * 100)

  const stressScore = Math.round(marketData.factor * 100)

  const signals = [probabilityScore, riskScore, coherenceScore, trendScore, stressScore]
  const avg = signals.reduce((a, b) => a + b, 0) / signals.length
  const variance = signals.reduce((a, b) => a + Math.pow(b - avg, 2), 0) / signals.length
  const divergence = Math.sqrt(variance)
  const logicScore = Math.round(Math.max(0, Math.min(100, 100 - divergence * 1.8)))

  return [
    {
      name: 'Probability Check',
      genericName: 'CP-1: Is this likely to succeed?',
      icon: <Target className="w-5 h-5" />,
      status: 'pending',
      score: probabilityScore,
      threshold: 70,
      reasoning: probabilityScore >= 70
        ? `Default probability ${(adjustedDefault * 100).toFixed(1)}% is within acceptable range`
        : `Default probability ${(adjustedDefault * 100).toFixed(1)}% exceeds risk threshold`,
      detail: `Credit score ${app.creditScore} + sector risk ${(sectorData.risk * 100).toFixed(0)}% + DTI impact → P(success) = ${probabilityScore}%`
    },
    {
      name: 'Risk Limits',
      genericName: 'CP-2: Would this exceed safe exposure?',
      icon: <Shield className="w-5 h-5" />,
      status: 'pending',
      score: riskScore,
      threshold: 55,
      reasoning: riskScore >= 55
        ? `Exposure within portfolio concentration limits`
        : `Concentration risk elevated — ${sectorData.label} sector at ${(sectorData.risk * 100).toFixed(0)}% risk weight`,
      detail: `Loan-to-income ratio: ${loanToIncome.toFixed(1)}x | Sector exposure: ${sectorExposure.toFixed(0)}% | Risk score: ${riskScore}/100`
    },
    {
      name: 'Signal Agreement',
      genericName: 'CP-3: Do multiple models agree?',
      icon: <Layers className="w-5 h-5" />,
      status: 'pending',
      score: coherenceScore,
      threshold: 50,
      reasoning: coherenceScore >= 50
        ? `Credit metrics, DTI, and sector outlook show sufficient agreement (${coherenceScore}%)`
        : `Conflicting signals — credit score suggests ${creditSignal >= 70 ? 'approve' : 'caution'} but DTI at ${app.dtiRatio}% and sector risk diverge`,
      detail: `Credit signal: ${creditSignal} | DTI signal: ${dtiSignal} | Sector signal: ${Math.round(sectorSignal)} → Coherence: ${coherenceScore}%`
    },
    {
      name: 'Trend Confirmation',
      genericName: 'CP-4: Is this sustained, not noise?',
      icon: <TrendingUp className="w-5 h-5" />,
      status: 'pending',
      score: trendScore,
      threshold: 50,
      reasoning: trendScore >= 50
        ? `Income trend (${incomeData.label}) confirms borrower stability`
        : `Income trend (${incomeData.label}) does not confirm sustained repayment capacity`,
      detail: `Income stability factor: ${(incomeData.factor * 100).toFixed(0)}% → Trend persistence score: ${trendScore}/100`
    },
    {
      name: 'Stress Test',
      genericName: 'CP-5: What if conditions deteriorate?',
      icon: <AlertTriangle className="w-5 h-5" />,
      status: 'pending',
      score: stressScore,
      threshold: 40,
      reasoning: stressScore >= 40
        ? `Market conditions (${marketData.label}) suggest adequate resilience under stress`
        : `Market conditions (${marketData.label}) indicate high vulnerability to deterioration`,
      detail: `Market condition factor: ${(marketData.factor * 100).toFixed(0)}% → Stress resilience: ${stressScore}/100`
    },
    {
      name: 'Logic Check',
      genericName: 'CP-6: Are signals contradicting each other?',
      icon: <Brain className="w-5 h-5" />,
      status: 'pending',
      score: logicScore,
      threshold: 45,
      reasoning: logicScore >= 45
        ? `Internal signal divergence is low — governance signals are consistent (${logicScore}%)`
        : `High internal contradiction detected between signals — divergence score ${(divergence).toFixed(1)} indicates conflicting risk assessment`,
      detail: `Signal variance: ${divergence.toFixed(1)} | Consistency: ${logicScore}% | ${logicScore < 45 ? 'CONTRADICTORY' : logicScore < 65 ? 'TENSIONED' : 'ALIGNED'}`
    },
  ]
}

export default function CreditGovernanceDemo() {
  const [application, setApplication] = useState<LoanApplication>({
    loanAmount: 200000,
    creditScore: 720,
    dtiRatio: 35,
    sector: 'technology',
    incomeStability: 'stable_growing',
    marketCondition: 'stable',
  })

  const [checkpoints, setCheckpoints] = useState<CheckpointResult[]>([])
  const [isEvaluating, setIsEvaluating] = useState(false)
  const [evaluationComplete, setEvaluationComplete] = useState(false)
  const [_currentCheckpoint, setCurrentCheckpoint] = useState(-1)
  const evaluationRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const runGovernanceEvaluation = () => {
    const results = evaluateCheckpoints(application)
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
            if (i === step) {
              return { ...cp, status: finalStatus }
            }
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

    if (blocked.length >= 2) return { decision: 'BLOCK', color: 'text-red-500', bg: 'bg-red-500/10 border-red-500/30', reason: `${blocked.length} checkpoints blocked. Governance recommendation: DO NOT APPROVE this loan until conditions improve.`, passed: passed.length + warned.length }
    if (blocked.length === 1) return { decision: 'HOLD', color: 'text-amber-500', bg: 'bg-amber-500/10 border-amber-500/30', reason: `1 checkpoint blocked (${blocked[0].name}). Governance recommendation: HOLD — review ${blocked[0].name.toLowerCase()} before proceeding.`, passed: passed.length + warned.length }
    if (warned.length >= 3) return { decision: 'HOLD', color: 'text-amber-500', bg: 'bg-amber-500/10 border-amber-500/30', reason: `${warned.length} checkpoints at marginal levels. Governance recommendation: HOLD — elevated cumulative risk requires additional review.`, passed: passed.length + warned.length }
    return { decision: 'APPROVE', color: 'text-emerald-500', bg: 'bg-emerald-500/10 border-emerald-500/30', reason: 'All checkpoints passed. Governance recommendation: APPROVE — decision meets all governance thresholds.', passed: passed.length + warned.length }
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
              <span className="ml-3 px-2 py-0.5 text-[10px] font-semibold bg-[#C9A227]/20 text-[#C9A227] rounded uppercase tracking-wider">Governance Demo</span>
            </div>
          </div>
          <div className="flex items-center gap-8">
            <Link to="/" className="nav-link">Home</Link>
            <Link to="/governance-demo-insurance" className="nav-link">Insurance Demo</Link>
            <Link to="/governance-demo-energy" className="nav-link">Energy Demo</Link>
            <Link to="/institutional" className="nav-link">Technical Details</Link>
            <a href="https://wa.me/16504815494?text=Hi%2C%20I%27m%20interested%20in%20OMNIX%20Governance" target="_blank" rel="noopener noreferrer" className="btn-primary text-sm px-5 py-2">Talk to Us</a>
          </div>
        </div>
      </nav>

      <main className="pt-32 px-6 pb-20 max-w-7xl mx-auto">
        <section className="text-center mb-16 animate-fade-in-up">
          <p className="section-title">Multi-Vertical Governance Architecture</p>
          <h1 className="heading-xl text-white mb-6">
            Same Engine.<br />
            <span className="gold-gradient">Different Domain.</span>
          </h1>
          <p className="text-xl text-muted max-w-3xl mx-auto mb-4 leading-relaxed">
            This interactive demo shows how OMNIX's 6-checkpoint governance architecture
            applies to credit/lending decisions — the same pattern validated across 1,600,000+
            evaluation cycles in digital asset trading (internal dataset).
          </p>
          <p className="text-sm text-[#64748B] max-w-2xl mx-auto">
            Adjust the loan parameters below and run the governance evaluation to see each checkpoint in action.
          </p>
        </section>

        <div className="grid lg:grid-cols-5 gap-8 mb-12">
          <div className="lg:col-span-2">
            <div className="glass-card p-8 sticky top-32">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-full bg-[#C9A227]/20 flex items-center justify-center">
                  <CreditCard className="w-5 h-5 gold-text" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">Loan Application</h3>
                  <p className="text-xs text-muted">Adjust parameters to test governance</p>
                </div>
              </div>

              <div className="space-y-5">
                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Loan Amount</label>
                  <div className="flex items-center gap-3">
                    <input
                      type="range"
                      min={25000}
                      max={1000000}
                      step={25000}
                      value={application.loanAmount}
                      onChange={(e) => { resetEvaluation(); setApplication(prev => ({ ...prev, loanAmount: parseInt(e.target.value) })) }}
                      className="flex-1 accent-[#C9A227]"
                    />
                    <span className="text-white font-semibold text-sm w-24 text-right">${(application.loanAmount / 1000).toFixed(0)}K</span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Credit Score (FICO)</label>
                  <div className="flex items-center gap-3">
                    <input
                      type="range"
                      min={300}
                      max={850}
                      step={10}
                      value={application.creditScore}
                      onChange={(e) => { resetEvaluation(); setApplication(prev => ({ ...prev, creditScore: parseInt(e.target.value) })) }}
                      className="flex-1 accent-[#C9A227]"
                    />
                    <span className={`font-semibold text-sm w-12 text-right ${application.creditScore >= 700 ? 'text-emerald-400' : application.creditScore >= 580 ? 'text-amber-400' : 'text-red-400'}`}>{application.creditScore}</span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Debt-to-Income Ratio</label>
                  <div className="flex items-center gap-3">
                    <input
                      type="range"
                      min={5}
                      max={65}
                      step={1}
                      value={application.dtiRatio}
                      onChange={(e) => { resetEvaluation(); setApplication(prev => ({ ...prev, dtiRatio: parseInt(e.target.value) })) }}
                      className="flex-1 accent-[#C9A227]"
                    />
                    <span className={`font-semibold text-sm w-12 text-right ${application.dtiRatio <= 30 ? 'text-emerald-400' : application.dtiRatio <= 43 ? 'text-amber-400' : 'text-red-400'}`}>{application.dtiRatio}%</span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Industry Sector</label>
                  <select
                    value={application.sector}
                    onChange={(e) => { resetEvaluation(); setApplication(prev => ({ ...prev, sector: e.target.value })) }}
                    className="w-full bg-[#0A1628] border border-[#C9A227]/20 rounded-lg px-4 py-3 text-white text-sm focus:border-[#C9A227] focus:outline-none"
                  >
                    {SECTORS.map(s => <option key={s.value} value={s.value}>{s.label} (Risk: {(s.risk * 100).toFixed(0)}%)</option>)}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Income Stability</label>
                  <select
                    value={application.incomeStability}
                    onChange={(e) => { resetEvaluation(); setApplication(prev => ({ ...prev, incomeStability: e.target.value })) }}
                    className="w-full bg-[#0A1628] border border-[#C9A227]/20 rounded-lg px-4 py-3 text-white text-sm focus:border-[#C9A227] focus:outline-none"
                  >
                    {INCOME_STABILITY.map(i => <option key={i.value} value={i.value}>{i.label}</option>)}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Market Conditions</label>
                  <select
                    value={application.marketCondition}
                    onChange={(e) => { resetEvaluation(); setApplication(prev => ({ ...prev, marketCondition: e.target.value })) }}
                    className="w-full bg-[#0A1628] border border-[#C9A227]/20 rounded-lg px-4 py-3 text-white text-sm focus:border-[#C9A227] focus:outline-none"
                  >
                    {MARKET_CONDITIONS.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
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
                      <Shield className="w-5 h-5" />
                      Run Governance Evaluation
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          <div className="lg:col-span-3 space-y-4">
            {checkpoints.length === 0 ? (
              <div className="glass-card p-12 text-center">
                <div className="w-20 h-20 rounded-full bg-[#C9A227]/10 flex items-center justify-center mx-auto mb-6">
                  <Layers className="w-10 h-10 gold-text" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">6-Checkpoint Governance Engine</h3>
                <p className="text-muted max-w-md mx-auto mb-8">
                  Configure the loan application parameters and click "Run Governance Evaluation" to see each checkpoint evaluate the decision in real time.
                </p>
                <div className="grid grid-cols-3 gap-4 max-w-lg mx-auto">
                  {[
                    { icon: <Target className="w-4 h-4" />, label: 'Probability' },
                    { icon: <Shield className="w-4 h-4" />, label: 'Risk Limits' },
                    { icon: <Layers className="w-4 h-4" />, label: 'Agreement' },
                    { icon: <TrendingUp className="w-4 h-4" />, label: 'Trend' },
                    { icon: <AlertTriangle className="w-4 h-4" />, label: 'Stress Test' },
                    { icon: <Brain className="w-4 h-4" />, label: 'Logic Check' },
                  ].map((cp, i) => (
                    <div key={i} className="flex flex-col items-center gap-2 p-3 rounded-lg bg-[#0A1628]/40 border border-[#C9A227]/10">
                      <div className="gold-text">{cp.icon}</div>
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
                      cp.status === 'evaluating' ? 'border-[#C9A227]/60 shadow-lg shadow-[#C9A227]/10' :
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
                          cp.status === 'evaluating' ? 'bg-[#C9A227]/20 text-[#C9A227] animate-pulse' :
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
                          <span className="text-xs text-[#C9A227] font-medium uppercase tracking-wider animate-pulse">Evaluating...</span>
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
                                'bg-[#C9A227]'
                              }`}
                              style={{ width: cp.status === 'evaluating' ? '60%' : `${cp.score}%` }}
                            />
                          </div>
                          <span className={`text-sm font-semibold w-16 text-right ${
                            cp.status === 'pass' ? 'text-emerald-400' :
                            cp.status === 'warn' ? 'text-amber-400' :
                            cp.status === 'block' ? 'text-red-400' :
                            'text-[#C9A227]'
                          }`}>
                            {cp.status === 'evaluating' ? '...' : `${cp.score}/100`}
                          </span>
                        </div>

                        {cp.status !== 'evaluating' && (
                          <>
                            <p className="text-sm text-muted">{cp.reasoning}</p>
                            <p className="text-xs text-[#64748B] font-mono">{cp.detail}</p>
                            <div className="text-xs text-[#475569]">Threshold: {cp.threshold}/100</div>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                ))}

                {decision && evaluationComplete && (
                  <div className={`glass-card p-8 border ${decision.bg} gold-glow mt-6`}>
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className={`w-12 h-12 rounded-full flex items-center justify-center ${decision.bg}`}>
                          {decision.decision === 'APPROVE' ? <CheckCircle className={`w-6 h-6 ${decision.color}`} /> :
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
                        Decision Trace ID: GOV-CREDIT-{Date.now().toString(36).toUpperCase()} | Architecture: 6-Checkpoint Fail-Closed | Engine: OMNIX Governance Core v1.0
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
            <p className="section-title">Architecture Comparison</p>
            <h2 className="text-3xl font-bold text-white">Same 6 Checkpoints. Every Domain.</h2>
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
              <div className="space-y-2 text-sm text-muted">
                <p><span className="text-white">CP-1:</span> Monte Carlo simulation (10K paths)</p>
                <p><span className="text-white">CP-2:</span> VaR95, per-trade limits, max drawdown</p>
                <p><span className="text-white">CP-3:</span> EMA + HMM + Kalman + NM coherence</p>
                <p><span className="text-white">CP-4:</span> Edge Confirmation Window (2+ cycles)</p>
                <p><span className="text-white">CP-5:</span> Black Swan tail risk detector</p>
                <p><span className="text-white">CP-6:</span> Decision Contradiction Index</p>
              </div>
              <div className="mt-4 pt-4 border-t border-[#C9A227]/10">
                <p className="text-xs text-emerald-400">1,600,000+ evaluation cycles | 98.5% capital preserved (internal dataset)</p>
              </div>
            </div>

            <div className="glass-card p-6 border-[#C9A227]/30">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-[#C9A227]/20 flex items-center justify-center">
                  <Building2 className="w-5 h-5 gold-text" />
                </div>
                <div>
                  <h4 className="text-white font-medium">Credit / Lending</h4>
                  <span className="text-xs text-[#C9A227] font-medium">DEMO ABOVE</span>
                </div>
              </div>
              <div className="space-y-2 text-sm text-muted">
                <p><span className="text-white">CP-1:</span> Default probability model</p>
                <p><span className="text-white">CP-2:</span> Concentration and exposure limits</p>
                <p><span className="text-white">CP-3:</span> Credit score + DTI + sector agreement</p>
                <p><span className="text-white">CP-4:</span> Income trend persistence (2+ quarters)</p>
                <p><span className="text-white">CP-5:</span> Recession / rate hike stress scenarios</p>
                <p><span className="text-white">CP-6:</span> Signal contradiction detection</p>
              </div>
              <div className="mt-4 pt-4 border-t border-[#C9A227]/10">
                <p className="text-xs text-[#C9A227]">Interactive demo — same architecture, different signals</p>
              </div>
            </div>

            <div className="glass-card p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center">
                  <Zap className="w-5 h-5 text-blue-400" />
                </div>
                <div>
                  <h4 className="text-white font-medium">Supply Chain</h4>
                  <span className="text-xs text-blue-400 font-medium">ROADMAP</span>
                </div>
              </div>
              <div className="space-y-2 text-sm text-muted">
                <p><span className="text-white">CP-1:</span> Price forecast model (commodity trends)</p>
                <p><span className="text-white">CP-2:</span> Supplier concentration, cash flow limits</p>
                <p><span className="text-white">CP-3:</span> Price + demand + reliability coherence</p>
                <p><span className="text-white">CP-4:</span> Procurement trend persistence (2+ periods)</p>
                <p><span className="text-white">CP-5:</span> Supply disruption stress scenarios</p>
                <p><span className="text-white">CP-6:</span> Demand vs. price contradiction check</p>
              </div>
              <div className="mt-4 pt-4 border-t border-[#C9A227]/10">
                <p className="text-xs text-blue-400">Year 2-3 roadmap — domain adapter in design</p>
              </div>
            </div>

            <div className="glass-card p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-orange-500/20 flex items-center justify-center">
                  <Zap className="w-5 h-5 text-orange-500" />
                </div>
                <div>
                  <h4 className="text-white font-medium">Energy Trading</h4>
                  <Link to="/governance-demo-energy" className="text-xs text-orange-500 font-medium hover:text-white transition-colors">VIEW DEMO →</Link>
                </div>
              </div>
              <div className="space-y-2 text-sm text-muted">
                <p><span className="text-white">CP-1:</span> Price forecast confidence</p>
                <p><span className="text-white">CP-2:</span> Grid exposure limits</p>
                <p><span className="text-white">CP-3:</span> Supply-demand coherence</p>
                <p><span className="text-white">CP-4:</span> Price trend persistence</p>
                <p><span className="text-white">CP-5:</span> Regulatory & climate stress</p>
                <p><span className="text-white">CP-6:</span> Signal contradiction detection</p>
              </div>
              <div className="mt-4 pt-4 border-t border-orange-500/20">
                <p className="text-xs text-orange-500">Interactive demo — energy governance in action</p>
              </div>
            </div>
          </div>
        </section>

        <section className="glass-card p-10 gold-glow text-center mb-16">
          <h2 className="text-2xl font-bold text-white mb-4">The Hardest Part Is Already Done</h2>
          <p className="text-muted max-w-2xl mx-auto mb-6">
            Building a robust, battle-tested governance engine is the hardest engineering challenge.
            OMNIX has already done this — validated across 1,600,000+ evaluation cycles. Expanding to new
            domains is an adapter problem, not a research problem.
          </p>
          <div className="grid grid-cols-4 gap-6 max-w-xl mx-auto mb-8">
            <div>
              <div className="text-2xl font-bold text-white">1.6M+</div>
              <div className="text-xs text-muted">Evaluation Cycles</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-emerald-400">98.5%</div>
              <div className="text-xs text-muted">Capital Preserved*</div>
            </div>
            <div>
              <div className="text-2xl font-bold gold-text">6</div>
              <div className="text-xs text-muted">Independent Checkpoints</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-orange-500">4</div>
              <div className="text-xs text-muted">Verticals</div>
            </div>
          </div>
          <a href="https://wa.me/16504815494?text=Hi%2C%20I%20saw%20the%20governance%20demo%20and%20I%27m%20interested" target="_blank" rel="noopener noreferrer" className="btn-primary inline-flex items-center gap-2">
            Talk to Us About Multi-Vertical Governance
            <ArrowRight className="w-4 h-4" />
          </a>
        </section>

        <div className="text-center">
          <p className="text-xs text-[#475569] max-w-2xl mx-auto leading-relaxed">
            This is a governance architecture demonstration. The credit evaluation shown uses simplified models
            for illustrative purposes. Production credit governance would integrate with real credit bureaus,
            financial data providers, and regulatory frameworks. OMNIX's core 6-checkpoint architecture is
            validated in digital asset trading across 1,600,000+ evaluation cycles (internal dataset, not externally audited).
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
            <Link to="/governance-demo-energy" className="text-muted hover:text-white text-sm transition-colors">Energy Demo</Link>
            <Link to="/institutional" className="text-muted hover:text-white text-sm transition-colors">Technical Details</Link>
            <a href="https://wa.me/16504815494" target="_blank" rel="noopener noreferrer" className="text-muted hover:text-white text-sm transition-colors">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  )
}
