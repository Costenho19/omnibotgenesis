import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { Shield, ArrowRight, AlertTriangle, CheckCircle, XCircle, Clock, Building2, TrendingUp, BarChart3, Zap, Activity, Layers, Target, Brain, Umbrella } from 'lucide-react'
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

interface PolicyApplication {
  policyType: string
  applicantAge: number
  coverageAmount: number
  claimsHistory: number
  geographicZone: string
  marketCondition: string
}

const POLICY_TYPES = [
  { value: 'property', label: 'Property Insurance', baseRisk: 0.12, avgCoverage: 350000 },
  { value: 'health', label: 'Health Insurance', baseRisk: 0.18, avgCoverage: 200000 },
  { value: 'auto', label: 'Auto Insurance', baseRisk: 0.15, avgCoverage: 50000 },
  { value: 'life', label: 'Life Insurance', baseRisk: 0.08, avgCoverage: 500000 },
  { value: 'commercial', label: 'Commercial Liability', baseRisk: 0.22, avgCoverage: 500000 },
  { value: 'cyber', label: 'Cyber Insurance', baseRisk: 0.28, avgCoverage: 250000 },
]

const GEOGRAPHIC_ZONES = [
  { value: 'low_risk', label: 'Low Risk Zone (Urban, Stable)', factor: 0.90 },
  { value: 'moderate', label: 'Moderate Risk Zone (Suburban)', factor: 0.70 },
  { value: 'elevated', label: 'Elevated Risk Zone (Coastal, Seismic)', factor: 0.45 },
  { value: 'high_risk', label: 'High Risk Zone (Flood/Hurricane Prone)', factor: 0.25 },
]

const MARKET_CONDITIONS = [
  { value: 'soft', label: 'Soft Market (Buyer Favorable)', factor: 0.85 },
  { value: 'stable', label: 'Stable Market', factor: 0.75 },
  { value: 'hardening', label: 'Hardening Market (Rising Premiums)', factor: 0.50 },
  { value: 'hard', label: 'Hard Market (Capacity Constrained)', factor: 0.30 },
]

function evaluateCheckpoints(app: PolicyApplication): CheckpointResult[] {
  const policyData = POLICY_TYPES.find(p => p.value === app.policyType) || POLICY_TYPES[0]
  const geoData = GEOGRAPHIC_ZONES.find(g => g.value === app.geographicZone) || GEOGRAPHIC_ZONES[0]
  const marketData = MARKET_CONDITIONS.find(m => m.value === app.marketCondition) || MARKET_CONDITIONS[0]

  const ageFactor = app.applicantAge < 25 ? 0.55 : app.applicantAge < 35 ? 0.90 : app.applicantAge < 50 ? 0.85 : app.applicantAge < 65 ? 0.65 : app.applicantAge < 75 ? 0.45 : 0.25
  const claimsPenalty = app.claimsHistory <= 1 ? app.claimsHistory * 0.10 : app.claimsHistory <= 3 ? 0.10 + (app.claimsHistory - 1) * 0.15 : 0.40 + (app.claimsHistory - 3) * 0.20
  const coverageRatio = app.coverageAmount / policyData.avgCoverage
  const baseClaimProb = policyData.baseRisk + claimsPenalty + (1 - ageFactor) * 0.15
  const adjustedClaimProb = Math.min(0.98, Math.max(0.02, baseClaimProb * (1 + Math.max(0, coverageRatio - 1) * 0.2)))
  const probabilityScore = Math.round((1 - adjustedClaimProb) * 100)

  const coverageExposure = Math.min(100, Math.round(coverageRatio * 40))
  const geoExposure = Math.round((1 - geoData.factor) * 60)
  const claimsExposure = Math.min(40, app.claimsHistory * 10)
  const concentrationRisk = Math.min(100, Math.round((coverageExposure + geoExposure + claimsExposure) * 0.7))
  const riskScore = Math.max(0, 100 - concentrationRisk)

  const ageSignal = Math.round(ageFactor * 100)
  const claimsSignal = Math.max(0, Math.round((1 - app.claimsHistory * 0.25) * 100))
  const geoSignal = Math.round(geoData.factor * 100)
  const coherenceScore = Math.round(ageSignal * 0.25 + claimsSignal * 0.50 + geoSignal * 0.25)

  const claimsTrend = app.claimsHistory === 0 ? 95 : app.claimsHistory === 1 ? 70 : app.claimsHistory === 2 ? 45 : app.claimsHistory === 3 ? 25 : app.claimsHistory === 4 ? 12 : 5
  const trendScore = Math.round(claimsTrend * (ageFactor * 0.6 + geoData.factor * 0.4))

  const marketStress = marketData.factor
  const claimsStress = Math.max(0, 1 - app.claimsHistory * 0.15)
  const stressScore = Math.round(marketStress * 60 + claimsStress * 40)

  const signals = [probabilityScore, riskScore, coherenceScore, trendScore, stressScore]
  const avg = signals.reduce((a, b) => a + b, 0) / signals.length
  const variance = signals.reduce((a, b) => a + Math.pow(b - avg, 2), 0) / signals.length
  const divergence = Math.sqrt(variance)
  const logicScore = Math.round(Math.max(0, Math.min(100, 100 - divergence * 2.0)))

  return [
    {
      name: 'Claim Probability',
      genericName: 'CP-1: Is this likely to succeed?',
      icon: <Target className="w-5 h-5" />,
      status: 'pending',
      score: probabilityScore,
      threshold: 65,
      reasoning: probabilityScore >= 65
        ? `Estimated claim probability ${(adjustedClaimProb * 100).toFixed(1)}% is within acceptable underwriting range`
        : `Estimated claim probability ${(adjustedClaimProb * 100).toFixed(1)}% exceeds acceptable risk for this policy type`,
      detail: `Age factor: ${(ageFactor * 100).toFixed(0)}% | Claims penalty: +${(claimsPenalty * 100).toFixed(0)}% | Coverage ratio: ${coverageRatio.toFixed(1)}x avg | P(no claim) = ${probabilityScore}%`
    },
    {
      name: 'Exposure Limits',
      genericName: 'CP-2: Would this exceed safe exposure?',
      icon: <Shield className="w-5 h-5" />,
      status: 'pending',
      score: riskScore,
      threshold: 50,
      reasoning: riskScore >= 50
        ? `Coverage exposure within portfolio concentration limits`
        : `Excessive exposure — $${(app.coverageAmount / 1000).toFixed(0)}K coverage in ${geoData.label} creates concentration risk`,
      detail: `Coverage exposure: ${coverageExposure}% | Geo risk: ${geoExposure}% | Claims exposure: ${claimsExposure}% | Concentration: ${concentrationRisk}% | Risk score: ${riskScore}/100`
    },
    {
      name: 'Underwriting Coherence',
      genericName: 'CP-3: Do multiple models agree?',
      icon: <Layers className="w-5 h-5" />,
      status: 'pending',
      score: coherenceScore,
      threshold: 50,
      reasoning: coherenceScore >= 50
        ? `Age profile, claims history, and geographic factors show sufficient agreement (${coherenceScore}%)`
        : `Conflicting signals — age profile suggests ${ageSignal >= 70 ? 'approve' : 'caution'} but claims history (${app.claimsHistory} prior claims) and ${geoData.label} diverge`,
      detail: `Age signal: ${ageSignal} | Claims signal: ${claimsSignal} | Geo signal: ${geoSignal} → Coherence: ${coherenceScore}%`
    },
    {
      name: 'Claims Trend',
      genericName: 'CP-4: Is this sustained, not noise?',
      icon: <TrendingUp className="w-5 h-5" />,
      status: 'pending',
      score: trendScore,
      threshold: 35,
      reasoning: trendScore >= 45
        ? `Claims history trend (${app.claimsHistory} prior claims) confirms acceptable risk trajectory`
        : `Claims history trend (${app.claimsHistory} prior claims) indicates deteriorating risk profile`,
      detail: `Prior claims impact: ${claimsTrend}% | Age-adjusted trend: ${trendScore}/100 | ${app.claimsHistory === 0 ? 'CLEAN RECORD' : app.claimsHistory <= 2 ? 'MODERATE HISTORY' : 'HIGH FREQUENCY'}`
    },
    {
      name: 'Catastrophe Stress Test',
      genericName: 'CP-5: What if conditions deteriorate?',
      icon: <AlertTriangle className="w-5 h-5" />,
      status: 'pending',
      score: stressScore,
      threshold: 40,
      reasoning: stressScore >= 40
        ? `Market conditions (${marketData.label}) suggest adequate capacity and reserves under stress`
        : `Market conditions (${marketData.label}) indicate constrained capacity — elevated reinsurance costs and reduced margins`,
      detail: `Market condition factor: ${(marketData.factor * 100).toFixed(0)}% → Stress resilience: ${stressScore}/100`
    },
    {
      name: 'Signal Contradiction',
      genericName: 'CP-6: Are signals contradicting each other?',
      icon: <Brain className="w-5 h-5" />,
      status: 'pending',
      score: logicScore,
      threshold: 45,
      reasoning: logicScore >= 45
        ? `Internal signal divergence is low — underwriting signals are consistent (${logicScore}%)`
        : `High internal contradiction detected — divergence score ${divergence.toFixed(1)} indicates conflicting risk assessment across checkpoints`,
      detail: `Signal variance: ${divergence.toFixed(1)} | Consistency: ${logicScore}% | ${logicScore < 45 ? 'CONTRADICTORY' : logicScore < 65 ? 'TENSIONED' : 'ALIGNED'}`
    },
  ]
}

export default function InsuranceGovernanceDemo() {
  const { metrics: liveMetrics, isLive, formatNumberFull } = useLiveMetrics()
  const [application, setApplication] = useState<PolicyApplication>({
    policyType: 'property',
    applicantAge: 40,
    coverageAmount: 250000,
    claimsHistory: 0,
    geographicZone: 'low_risk',
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

    if (blocked.length >= 2) return { decision: 'DECLINE', color: 'text-red-500', bg: 'bg-red-500/10 border-red-500/30', reason: `${blocked.length} checkpoints blocked. Underwriting recommendation: DECLINE this policy — risk profile exceeds acceptable thresholds.`, passed: passed.length + warned.length }
    if (blocked.length === 1) return { decision: 'REFER', color: 'text-amber-500', bg: 'bg-amber-500/10 border-amber-500/30', reason: `1 checkpoint blocked (${blocked[0].name}). Underwriting recommendation: REFER to senior underwriter for manual review of ${blocked[0].name.toLowerCase()}.`, passed: passed.length + warned.length }
    if (warned.length >= 3) return { decision: 'REFER', color: 'text-amber-500', bg: 'bg-amber-500/10 border-amber-500/30', reason: `${warned.length} checkpoints at marginal levels. Underwriting recommendation: REFER — cumulative marginal risk requires senior review and possible premium adjustment.`, passed: passed.length + warned.length }
    return { decision: 'BIND', color: 'text-emerald-500', bg: 'bg-emerald-500/10 border-emerald-500/30', reason: 'All checkpoints passed. Underwriting recommendation: BIND — policy meets all governance thresholds for automated approval.', passed: passed.length + warned.length }
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
              <span className="ml-3 px-2 py-0.5 text-[10px] font-semibold bg-blue-500/20 text-blue-400 rounded uppercase tracking-wider">Insurance Demo</span>
            </div>
          </div>
          <div className="flex items-center gap-8">
            <Link to="/" className="nav-link">Home</Link>
            <Link to="/governance-demo" className="nav-link">Credit Demo</Link>
            <Link to="/governance-demo-energy" className="nav-link">Energy Demo</Link>
            <Link to="/governance-demo-biotech" className="nav-link">Biotech Demo</Link>
            <Link to="/institutional" className="nav-link">Technical Details</Link>
            <a href="https://wa.me/16505078293?text=Hi%2C%20I%27m%20interested%20in%20OMNIX%20Governance" target="_blank" rel="noopener noreferrer" className="btn-primary text-sm px-5 py-2">Talk to Us</a>
          </div>
        </div>
      </nav>

      <main className="pt-32 px-6 pb-20 max-w-7xl mx-auto">
        <section className="text-center mb-16 animate-fade-in-up">
          <p className="section-title">Insurance Underwriting Governance</p>
          <h1 className="heading-xl text-white mb-6">
            Govern Every Policy.<br />
            <span className="gold-gradient">Before It Binds.</span>
          </h1>
          <p className="text-xl text-muted max-w-3xl mx-auto mb-4 leading-relaxed">
            This interactive demo shows how OMNIX's 11-checkpoint governance architecture
            applies to insurance underwriting decisions — the same pattern validated across {formatNumberFull(liveMetrics.evaluation_cycles)}
            evaluation cycles in digital asset trading (internal dataset).
          </p>
          <p className="text-sm text-[#64748B] max-w-2xl mx-auto">
            Adjust the policy parameters below and run the governance evaluation to see each checkpoint assess the risk.
          </p>
        </section>

        <div className="grid lg:grid-cols-5 gap-8 mb-12">
          <div className="lg:col-span-2">
            <div className="glass-card p-8 sticky top-32">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center">
                  <Umbrella className="w-5 h-5 text-blue-400" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">Policy Application</h3>
                  <p className="text-xs text-muted">Adjust parameters to test governance</p>
                </div>
              </div>

              <div className="space-y-5">
                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Policy Type</label>
                  <select
                    value={application.policyType}
                    onChange={(e) => { resetEvaluation(); setApplication(prev => ({ ...prev, policyType: e.target.value })) }}
                    className="w-full bg-[#0A1628] border border-[#C9A227]/20 rounded-lg px-4 py-3 text-white text-sm focus:border-[#C9A227] focus:outline-none"
                  >
                    {POLICY_TYPES.map(p => <option key={p.value} value={p.value}>{p.label} (Base Risk: {(p.baseRisk * 100).toFixed(0)}%)</option>)}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Applicant Age</label>
                  <div className="flex items-center gap-3">
                    <input
                      type="range"
                      min={18}
                      max={80}
                      step={1}
                      value={application.applicantAge}
                      onChange={(e) => { resetEvaluation(); setApplication(prev => ({ ...prev, applicantAge: parseInt(e.target.value) })) }}
                      className="flex-1 accent-[#C9A227]"
                    />
                    <span className={`font-semibold text-sm w-16 text-right ${application.applicantAge >= 25 && application.applicantAge < 55 ? 'text-emerald-400' : application.applicantAge < 70 ? 'text-amber-400' : 'text-red-400'}`}>{application.applicantAge} yrs</span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Coverage Amount</label>
                  <div className="flex items-center gap-3">
                    <input
                      type="range"
                      min={10000}
                      max={2000000}
                      step={10000}
                      value={application.coverageAmount}
                      onChange={(e) => { resetEvaluation(); setApplication(prev => ({ ...prev, coverageAmount: parseInt(e.target.value) })) }}
                      className="flex-1 accent-[#C9A227]"
                    />
                    <span className="text-white font-semibold text-sm w-24 text-right">${(application.coverageAmount / 1000).toFixed(0)}K</span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Prior Claims (Last 5 Years)</label>
                  <div className="flex items-center gap-3">
                    <input
                      type="range"
                      min={0}
                      max={6}
                      step={1}
                      value={application.claimsHistory}
                      onChange={(e) => { resetEvaluation(); setApplication(prev => ({ ...prev, claimsHistory: parseInt(e.target.value) })) }}
                      className="flex-1 accent-[#C9A227]"
                    />
                    <span className={`font-semibold text-sm w-16 text-right ${application.claimsHistory === 0 ? 'text-emerald-400' : application.claimsHistory <= 2 ? 'text-amber-400' : 'text-red-400'}`}>{application.claimsHistory} claims</span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Geographic Zone</label>
                  <select
                    value={application.geographicZone}
                    onChange={(e) => { resetEvaluation(); setApplication(prev => ({ ...prev, geographicZone: e.target.value })) }}
                    className="w-full bg-[#0A1628] border border-[#C9A227]/20 rounded-lg px-4 py-3 text-white text-sm focus:border-[#C9A227] focus:outline-none"
                  >
                    {GEOGRAPHIC_ZONES.map(g => <option key={g.value} value={g.value}>{g.label}</option>)}
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
                      Run Underwriting Governance
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          <div className="lg:col-span-3 space-y-4">
            {checkpoints.length === 0 ? (
              <div className="glass-card p-12 text-center">
                <div className="w-20 h-20 rounded-full bg-blue-500/10 flex items-center justify-center mx-auto mb-6">
                  <Umbrella className="w-10 h-10 text-blue-400" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">8-Checkpoint Underwriting Engine</h3>
                <p className="text-muted max-w-md mx-auto mb-8">
                  Configure the policy application parameters and click "Run Underwriting Governance" to see each checkpoint evaluate the risk in real time.
                </p>
                <div className="grid grid-cols-3 gap-4 max-w-lg mx-auto">
                  {[
                    { icon: <Target className="w-4 h-4" />, label: 'Claim Prob.' },
                    { icon: <Shield className="w-4 h-4" />, label: 'Exposure' },
                    { icon: <Layers className="w-4 h-4" />, label: 'Coherence' },
                    { icon: <TrendingUp className="w-4 h-4" />, label: 'Claims Trend' },
                    { icon: <AlertTriangle className="w-4 h-4" />, label: 'Catastrophe' },
                    { icon: <Brain className="w-4 h-4" />, label: 'Contradiction' },
                  ].map((cp, i) => (
                    <div key={i} className="flex flex-col items-center gap-2 p-3 rounded-lg bg-[#0A1628]/40 border border-blue-500/10">
                      <div className="text-blue-400">{cp.icon}</div>
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
                      cp.status === 'evaluating' ? 'border-blue-500/60 shadow-lg shadow-blue-500/10' :
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
                          cp.status === 'evaluating' ? 'bg-blue-500/20 text-blue-400 animate-pulse' :
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
                          <span className="text-xs text-blue-400 font-medium uppercase tracking-wider animate-pulse">Evaluating...</span>
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
                                'bg-blue-500'
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
                          {decision.decision === 'BIND' ? <CheckCircle className={`w-6 h-6 ${decision.color}`} /> :
                           decision.decision === 'REFER' ? <Clock className={`w-6 h-6 ${decision.color}`} /> :
                           <XCircle className={`w-6 h-6 ${decision.color}`} />}
                        </div>
                        <div>
                          <p className="text-xs text-muted uppercase tracking-wider">Underwriting Decision</p>
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
                        Decision Trace ID: GOV-INS-{Date.now().toString(36).toUpperCase()} | Architecture: 8-Checkpoint Fail-Closed | Engine: OMNIX Governance Core v1.0
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
              <div className="space-y-2 text-sm text-muted">
                <p><span className="text-white">CP-1:</span> Monte Carlo simulation (10K paths)</p>
                <p><span className="text-white">CP-2:</span> VaR95, per-trade limits, max drawdown</p>
                <p><span className="text-white">CP-3:</span> EMA + HMM + Kalman + NM coherence</p>
                <p><span className="text-white">CP-4:</span> Edge Confirmation Window (2+ cycles)</p>
                <p><span className="text-white">CP-5:</span> Black Swan tail risk detector</p>
                <p><span className="text-white">CP-6:</span> Decision Contradiction Index</p>
              </div>
              <div className="mt-4 pt-4 border-t border-[#C9A227]/10">
                <p className="text-xs text-emerald-400">{isLive ? '🟢' : '⏳'} {formatNumberFull(liveMetrics.evaluation_cycles)} evaluation cycles | {liveMetrics.capital_preserved_pct}% capital preserved (internal dataset)</p>
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

            <div className="glass-card p-6 border-blue-500/30">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center">
                  <Umbrella className="w-5 h-5 text-blue-400" />
                </div>
                <div>
                  <h4 className="text-white font-medium">Insurance Underwriting</h4>
                  <span className="text-xs text-blue-400 font-medium">DEMO ABOVE</span>
                </div>
              </div>
              <div className="space-y-2 text-sm text-muted">
                <p><span className="text-white">CP-1:</span> Claim probability model</p>
                <p><span className="text-white">CP-2:</span> Coverage exposure and concentration</p>
                <p><span className="text-white">CP-3:</span> Age + claims + geographic coherence</p>
                <p><span className="text-white">CP-4:</span> Claims frequency trend analysis</p>
                <p><span className="text-white">CP-5:</span> Catastrophe / hard market stress test</p>
                <p><span className="text-white">CP-6:</span> Signal contradiction detection</p>
              </div>
              <div className="mt-4 pt-4 border-t border-blue-500/20">
                <p className="text-xs text-blue-400">Interactive demo — underwriting governance in action</p>
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

        <section className="glass-card p-10 text-center mb-16" style={{ borderColor: 'rgba(59, 130, 246, 0.3)' }}>
          <h2 className="text-2xl font-bold text-white mb-4">Four Verticals. One Governance Engine.</h2>
          <p className="text-muted max-w-2xl mx-auto mb-6">
            OMNIX now demonstrates governance across four distinct domains — trading, credit, insurance, and energy.
            Each uses the same 11-checkpoint fail-closed architecture with domain-specific signals.
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
              <div className="text-2xl font-bold text-orange-500">{liveMetrics.verticals_demo}</div>
              <div className="text-xs text-muted">Verticals</div>
            </div>
          </div>
          <a href="https://wa.me/16505078293?text=Hi%2C%20I%20saw%20the%20insurance%20governance%20demo%20and%20I%27m%20interested" target="_blank" rel="noopener noreferrer" className="btn-primary inline-flex items-center gap-2">
            Talk to Us About Multi-Vertical Governance
            <ArrowRight className="w-4 h-4" />
          </a>
        </section>

        <div className="text-center">
          <p className="text-xs text-[#475569] max-w-2xl mx-auto leading-relaxed">
            This is a governance architecture demonstration. The insurance evaluation shown uses simplified actuarial models
            for illustrative purposes. Production insurance governance would integrate with real actuarial tables,
            claims databases, reinsurance systems, and regulatory frameworks. OMNIX's core 11-checkpoint architecture is
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
            <Link to="/governance-demo-energy" className="text-muted hover:text-white text-sm transition-colors">Energy Demo</Link>
            <Link to="/institutional" className="text-muted hover:text-white text-sm transition-colors">Technical Details</Link>
            <a href="https://wa.me/16505078293" target="_blank" rel="noopener noreferrer" className="text-muted hover:text-white text-sm transition-colors">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  )
}
