import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { Shield, AlertTriangle, CheckCircle, XCircle, Clock, TrendingUp, BarChart3, Activity, Layers, Target, Brain, Microscope, FlaskConical, FileCheck, ExternalLink, ChevronRight } from 'lucide-react'
import { useLiveMetrics } from '../hooks/useLiveMetrics'

interface CheckpointResult {
  name: string
  genericName: string
  icon: React.ReactNode
  status: 'pending' | 'evaluating' | 'pass' | 'warn' | 'block'
  score: number
  threshold: number
  thresholdType: 'min' | 'max'
  reasoning: string
  detail: string
}

interface TrialApplication {
  phase: string
  therapeuticArea: string
  adverseEventSeverity: number
  preclinicalAlignment: number
  enrollmentRate: number
  regulatoryDesignation: string
}

const TRIAL_PHASES = [
  { value: 'phase1', label: 'Phase I — Safety & Dosing', successRate: 0.52, baseProbability: 45 },
  { value: 'phase2', label: 'Phase II — Efficacy Signal', successRate: 0.28, baseProbability: 58 },
  { value: 'phase3', label: 'Phase III — Pivotal Trial', successRate: 0.57, baseProbability: 72 },
  { value: 'phase3b', label: 'Phase III-B — Confirmatory', successRate: 0.71, baseProbability: 80 },
]

const THERAPEUTIC_AREAS = [
  { value: 'oncology', label: 'Oncology', historicalRate: 0.40, riskFactor: 1.15 },
  { value: 'cns', label: 'CNS / Neurology', historicalRate: 0.20, riskFactor: 1.30 },
  { value: 'cardiology', label: 'Cardiology', historicalRate: 0.55, riskFactor: 1.00 },
  { value: 'rare_disease', label: 'Rare Disease', historicalRate: 0.68, riskFactor: 0.85 },
  { value: 'infectious', label: 'Infectious Disease', historicalRate: 0.62, riskFactor: 0.90 },
]

const REGULATORY_DESIGNATIONS = [
  { value: 'none', label: 'Standard Review', strengthScore: 35, factor: 0.60 },
  { value: 'fast_track', label: 'FDA Fast Track', strengthScore: 55, factor: 0.75 },
  { value: 'breakthrough', label: 'FDA Breakthrough Therapy', strengthScore: 75, factor: 0.90 },
  { value: 'priority_review', label: 'FDA Priority Review', strengthScore: 68, factor: 0.85 },
  { value: 'rmat', label: 'RMAT Designation', strengthScore: 80, factor: 0.92 },
]

const REAL_VALIDATED_SCENARIOS = [
  {
    nct: 'NCT02362594',
    name: 'KEYNOTE-054',
    shortName: 'Pembrolizumab — Melanoma',
    sponsor: 'Merck Sharp & Dohme LLC',
    phase: 'Phase III',
    condition: 'Melanoma',
    enrollment: 1019,
    receiptId: 'OMNIX-E712B49AB172',
    decision: 'ADVANCE',
    checkpointsPassed: 6,
    checkpointsTotal: 6,
    signals: { probability_score: 79, risk_exposure: 48, signal_coherence: 81, trend_persistence: 75, stress_resilience: 72, logic_consistency: 78 },
    context: 'Phase II → III advancement decision. Established PD-1 mechanism, strong prior KEYNOTE-006 data, FDA Breakthrough designation.',
  },
  {
    nct: 'NCT00938652',
    name: 'BSI-201 / Iniparib',
    shortName: 'Iniparib — Triple-Negative Breast Cancer',
    sponsor: 'Sanofi',
    phase: 'Phase III',
    condition: 'Triple-Negative Breast Cancer',
    enrollment: 519,
    receiptId: 'OMNIX-BBD288AE7131',
    decision: 'HALT',
    checkpointsPassed: 0,
    checkpointsTotal: 6,
    signals: { probability_score: 38, risk_exposure: 74, signal_coherence: 31, trend_persistence: 44, stress_resilience: 28, logic_consistency: 35 },
    context: 'Phase II → III advancement decision. Mechanism as PARP inhibitor not validated; Phase II benefit not replicated; high AE burden in combination therapy.',
  },
  {
    nct: 'NCT03367403',
    name: 'TRAILBLAZER-ALZ',
    shortName: 'Donanemab — Alzheimer\'s Disease',
    sponsor: 'Eli Lilly and Company',
    phase: 'Phase II',
    condition: "Alzheimer's Disease",
    enrollment: 272,
    receiptId: 'OMNIX-5DC087FE47B6',
    decision: 'SCIENTIFIC REVIEW',
    checkpointsPassed: 5,
    checkpointsTotal: 6,
    signals: { probability_score: 57, risk_exposure: 59, signal_coherence: 48, trend_persistence: 54, stress_resilience: 61, logic_consistency: 52 },
    context: 'Phase II interim review. Strong amyloid clearance (biomarker), but CP-3 flagged: preclinical-clinical alignment below threshold. ARIA-E signals at higher doses require senior scientific review.',
  },
]

function evaluateCheckpoints(app: TrialApplication): CheckpointResult[] {
  const phaseData = TRIAL_PHASES.find(p => p.value === app.phase) || TRIAL_PHASES[1]
  const areaData = THERAPEUTIC_AREAS.find(a => a.value === app.therapeuticArea) || THERAPEUTIC_AREAS[0]
  const regData = REGULATORY_DESIGNATIONS.find(r => r.value === app.regulatoryDesignation) || REGULATORY_DESIGNATIONS[0]

  const alignmentFactor = app.preclinicalAlignment / 100
  const aeFactor = Math.max(0, 1 - app.adverseEventSeverity * 0.18)
  const baseProb = phaseData.baseProbability
  const adjustedProb = Math.round(baseProb * alignmentFactor * 0.40 + baseProb * areaData.historicalRate * 0.35 + baseProb * aeFactor * 0.25)
  const probabilityScore = Math.min(95, Math.max(15, adjustedProb))

  const aeExposure = Math.min(95, app.adverseEventSeverity * 16 + (1 - areaData.historicalRate) * 30)
  const riskExposureScore = Math.round(aeExposure * areaData.riskFactor)

  const alignmentSignal = app.preclinicalAlignment
  const phaseCoherence = phaseData.value === 'phase1' ? 50 : phaseData.value === 'phase2' ? 65 : 80
  const coherenceScore = Math.round(alignmentSignal * 0.60 + phaseCoherence * 0.25 + (100 - app.adverseEventSeverity * 15) * 0.15)

  const enrollmentSignal = app.enrollmentRate
  const aeTrend = Math.max(0, 100 - app.adverseEventSeverity * 18)
  const trendScore = Math.round(enrollmentSignal * 0.65 + aeTrend * 0.35)

  const stressScore = Math.round(regData.strengthScore * regData.factor + (phaseData.successRate * 30))

  const signals = [probabilityScore, Math.max(0, 100 - riskExposureScore), coherenceScore, trendScore, stressScore]
  const avg = signals.reduce((a, b) => a + b, 0) / signals.length
  const variance = signals.reduce((a, b) => a + Math.pow(b - avg, 2), 0) / signals.length
  const divergence = Math.sqrt(variance)
  const logicScore = Math.round(Math.max(0, Math.min(100, 100 - divergence * 1.8)))

  return [
    {
      name: 'Trial Success Probability',
      genericName: 'CP-1: Is this likely to succeed?',
      icon: <Target className="w-5 h-5" />,
      status: 'pending',
      score: probabilityScore,
      threshold: 50,
      thresholdType: 'min',
      reasoning: probabilityScore >= 50
        ? `Estimated success probability ${probabilityScore}% meets threshold for ${phaseData.label}`
        : `Estimated success probability ${probabilityScore}% is below minimum. Historical ${areaData.label} ${phaseData.label} rate: ${(phaseData.successRate * 100).toFixed(0)}%`,
      detail: `Phase base: ${phaseData.baseProbability}% | Area rate: ${(areaData.historicalRate * 100).toFixed(0)}% | Alignment weight: ${app.preclinicalAlignment}% | AE penalty: -${((1 - aeFactor) * 100).toFixed(0)}% | Final: ${probabilityScore}%`,
    },
    {
      name: 'Adverse Event Exposure',
      genericName: 'CP-2: Would this exceed safe exposure?',
      icon: <AlertTriangle className="w-5 h-5" />,
      status: 'pending',
      score: riskExposureScore,
      threshold: 65,
      thresholdType: 'max',
      reasoning: riskExposureScore <= 65
        ? `Adverse event profile (severity: ${app.adverseEventSeverity}/5) within acceptable safety bounds for ${areaData.label}`
        : `AE exposure ${riskExposureScore}/100 exceeds safe threshold. Severity ${app.adverseEventSeverity}/5 in ${areaData.label} creates an unacceptable safety signal`,
      detail: `AE severity: ${app.adverseEventSeverity}/5 | Area risk factor: ×${areaData.riskFactor.toFixed(2)} | Exposure score: ${riskExposureScore}/100 | Threshold: ≤65`,
    },
    {
      name: 'Preclinical-Clinical Alignment',
      genericName: 'CP-3: Do multiple data sources agree?',
      icon: <Layers className="w-5 h-5" />,
      status: 'pending',
      score: coherenceScore,
      threshold: 55,
      thresholdType: 'min',
      reasoning: coherenceScore >= 55
        ? `Preclinical and clinical signals show adequate alignment (${coherenceScore}%) — mechanistic hypothesis supported`
        : `Low coherence (${coherenceScore}%) — preclinical data does not sufficiently translate to clinical signals at ${phaseData.label} level`,
      detail: `Preclinical alignment: ${alignmentSignal}% | Phase coherence baseline: ${phaseCoherence} | AE coherence penalty: -${app.adverseEventSeverity * 15}% | Coherence: ${coherenceScore}%`,
    },
    {
      name: 'Enrollment Momentum',
      genericName: 'CP-4: Is this trend sustained?',
      icon: <TrendingUp className="w-5 h-5" />,
      status: 'pending',
      score: trendScore,
      threshold: 50,
      thresholdType: 'min',
      reasoning: trendScore >= 50
        ? `Enrollment trajectory (${app.enrollmentRate}%) and safety trend support continued trial momentum`
        : `Enrollment momentum below threshold — ${app.enrollmentRate < 50 ? `enrollment rate ${app.enrollmentRate}% suggests recruitment challenges` : `AE signals may be causing dropout`}`,
      detail: `Enrollment rate: ${app.enrollmentRate}% | AE trend impact: ${aeTrend.toFixed(0)} | Combined trend: ${trendScore}/100`,
    },
    {
      name: 'Regulatory Pathway Strength',
      genericName: 'CP-5: What if conditions deteriorate?',
      icon: <FileCheck className="w-5 h-5" />,
      status: 'pending',
      score: stressScore,
      threshold: 35,
      thresholdType: 'min',
      reasoning: stressScore >= 35
        ? `${regData.label} pathway provides adequate regulatory resilience (${stressScore}%) under adverse review conditions`
        : `Standard review pathway without designation creates regulatory fragility — insufficient resilience if primary endpoint is marginal`,
      detail: `Designation: ${regData.label} (strength: ${regData.strengthScore}) | Factor: ×${regData.factor} | Phase success history: +${(phaseData.successRate * 30).toFixed(0)} | Total: ${stressScore}/100`,
    },
    {
      name: 'Signal Contradiction Index',
      genericName: 'CP-6: Are signals contradicting each other?',
      icon: <Brain className="w-5 h-5" />,
      status: 'pending',
      score: logicScore,
      threshold: 40,
      thresholdType: 'min',
      reasoning: logicScore >= 40
        ? `Internal signal consistency acceptable (${logicScore}%) — trial profile is internally coherent`
        : `High signal contradiction detected — divergence score ${divergence.toFixed(1)} indicates conflicting risk and efficacy signals across checkpoints`,
      detail: `Signal variance: ${divergence.toFixed(1)} | Consistency: ${logicScore}% | ${logicScore < 40 ? 'CONTRADICTORY — escalate' : logicScore < 60 ? 'TENSIONED — monitor' : 'ALIGNED'}`,
    },
  ]
}

export default function BiotechGovernanceDemo() {
  const { metrics: liveMetrics, formatNumberFull } = useLiveMetrics()
  const [application, setApplication] = useState<TrialApplication>({
    phase: 'phase3',
    therapeuticArea: 'oncology',
    adverseEventSeverity: 1,
    preclinicalAlignment: 75,
    enrollmentRate: 70,
    regulatoryDesignation: 'breakthrough',
  })
  const [checkpoints, setCheckpoints] = useState<CheckpointResult[]>([])
  const [isEvaluating, setIsEvaluating] = useState(false)
  const [evaluationComplete, setEvaluationComplete] = useState(false)
  const [_currentCheckpoint, setCurrentCheckpoint] = useState(-1)
  const [selectedScenario, setSelectedScenario] = useState<number | null>(null)
  const evaluationRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const runGovernanceEvaluation = () => {
    const results = evaluateCheckpoints(application)
    const finalResults = results.map(cp => {
      const passed = cp.thresholdType === 'min' ? cp.score >= cp.threshold : cp.score <= cp.threshold
      const margin = cp.thresholdType === 'min' ? cp.score - cp.threshold : cp.threshold - cp.score
      const finalStatus: 'pass' | 'warn' | 'block' = !passed ? 'block' : (margin >= 15 ? 'pass' : 'warn')
      return { ...cp, finalStatus }
    })

    setCheckpoints(results)
    setIsEvaluating(true)
    setEvaluationComplete(false)
    setCurrentCheckpoint(0)

    let step = 0
    const animate = () => {
      if (step < finalResults.length) {
        setCheckpoints(prev => prev.map((cp, i) => i === step ? { ...cp, status: 'evaluating' as const } : cp))
        setTimeout(() => {
          setCheckpoints(prev => prev.map((cp, i) => i === step ? { ...cp, status: finalResults[step].finalStatus } : cp))
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
    return () => { if (evaluationRef.current) clearTimeout(evaluationRef.current) }
  }, [])

  const resetEvaluation = () => {
    setCheckpoints([])
    setEvaluationComplete(false)
    setCurrentCheckpoint(-1)
    setIsEvaluating(false)
    setSelectedScenario(null)
    if (evaluationRef.current) clearTimeout(evaluationRef.current)
  }

  const getGovernanceDecision = () => {
    if (!evaluationComplete || checkpoints.length === 0) return null
    const blocked = checkpoints.filter(cp => cp.status === 'block')
    const warned = checkpoints.filter(cp => cp.status === 'warn')
    const passed = checkpoints.filter(cp => cp.status === 'pass')
    if (blocked.length >= 2) return { decision: 'HALT', color: 'text-red-500', bg: 'bg-red-500/10 border-red-500/30', reason: `${blocked.length} checkpoints blocked. Recommendation: HALT advancement — risk profile exceeds governance thresholds. Blocked: ${blocked.map(b => b.name).join(', ')}.`, passed: passed.length + warned.length }
    if (blocked.length === 1) return { decision: 'SCIENTIFIC REVIEW', color: 'text-amber-500', bg: 'bg-amber-500/10 border-amber-500/30', reason: `1 checkpoint blocked (${blocked[0].name}). Recommendation: Escalate to Data Safety Monitoring Board. The ${blocked[0].name.toLowerCase()} signal requires senior scientific review before advancement.`, passed: passed.length + warned.length }
    if (warned.length >= 3) return { decision: 'SCIENTIFIC REVIEW', color: 'text-amber-500', bg: 'bg-amber-500/10 border-amber-500/30', reason: `${warned.length} checkpoints at marginal levels. Recommendation: DSMB review — cumulative marginal signals require protocol amendment assessment.`, passed: passed.length + warned.length }
    return { decision: 'ADVANCE', color: 'text-emerald-500', bg: 'bg-emerald-500/10 border-emerald-500/30', reason: `All ${passed.length + warned.length} checkpoints passed. Recommendation: ADVANCE — trial profile meets all governance thresholds for next phase progression.`, passed: passed.length + warned.length }
  }

  const decision = getGovernanceDecision()

  const loadScenario = (idx: number) => {
    resetEvaluation()
    setSelectedScenario(idx)
    const sc = REAL_VALIDATED_SCENARIOS[idx]
    const phaseMap: Record<string, string> = { 'Phase I': 'phase1', 'Phase II': 'phase2', 'Phase III': 'phase3', 'Phase III-B': 'phase3b' }
    const areaMap: Record<string, string> = { 'Melanoma': 'oncology', "Triple-Negative Breast Cancer": 'oncology', "Alzheimer's Disease": 'cns' }
    const regMap: Record<string, string> = { 'KEYNOTE-054': 'breakthrough', 'BSI-201 / Iniparib': 'none', 'TRAILBLAZER-ALZ': 'fast_track' }
    const aeMap: Record<string, number> = { 'KEYNOTE-054': 1, 'BSI-201 / Iniparib': 4, 'TRAILBLAZER-ALZ': 2 }
    setApplication({
      phase: phaseMap[sc.phase] || 'phase3',
      therapeuticArea: areaMap[sc.condition] || 'oncology',
      adverseEventSeverity: aeMap[sc.name] || 2,
      preclinicalAlignment: Math.round(sc.signals.signal_coherence),
      enrollmentRate: Math.round(sc.signals.trend_persistence),
      regulatoryDesignation: regMap[sc.name] || 'none',
    })
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
              <span className="ml-3 px-2 py-0.5 text-[10px] font-semibold bg-emerald-500/20 text-emerald-400 rounded uppercase tracking-wider">Biotech Demo</span>
            </div>
          </div>
          <div className="flex items-center gap-6">
            <Link to="/" className="nav-link">Home</Link>
            <Link to="/governance-demo" className="nav-link">Credit Demo</Link>
            <Link to="/governance-demo-insurance" className="nav-link">Insurance Demo</Link>
            <Link to="/institutional" className="nav-link">Technical Details</Link>
            <a href="https://wa.me/16504815494?text=Hi%2C%20I%27m%20interested%20in%20OMNIX%20Governance%20for%20Biotech" target="_blank" rel="noopener noreferrer" className="btn-primary text-sm px-5 py-2">Talk to Us</a>
          </div>
        </div>
      </nav>

      <main className="pt-32 px-6 pb-20 max-w-7xl mx-auto">
        <section className="text-center mb-14 animate-fade-in-up">
          <p className="section-title">Clinical Trial Governance</p>
          <h1 className="heading-xl text-white mb-6">
            Govern Every Trial Decision.<br />
            <span className="gold-gradient">Before It Advances.</span>
          </h1>
          <p className="text-xl text-muted max-w-3xl mx-auto mb-4 leading-relaxed">
            The same governance engine that has processed {formatNumberFull(liveMetrics.evaluation_cycles)} evaluation cycles
            in digital asset trading — applied to clinical trial advancement decisions.
            Real data from ClinicalTrials.gov. Real PQC-signed receipts. Domain adapters evaluate 6 normalized signals per vertical; the trading pipeline includes a 7th checkpoint (Temporal Coherence Validation, Mar 2026).
          </p>
          <p className="text-sm text-[#64748B] max-w-2xl mx-auto">
            Three pre-validated scenarios use real NCT trial data. Or configure your own parameters below.
          </p>
        </section>

        {/* Real Validated Scenarios */}
        <section className="mb-12">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-2 h-2 rounded-full bg-[#C9A227]" />
            <h2 className="text-sm font-semibold text-[#C9A227] uppercase tracking-widest">Real Validated Scenarios — ClinicalTrials.gov Data</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-4">
            {REAL_VALIDATED_SCENARIOS.map((sc, idx) => (
              <button
                key={sc.nct}
                onClick={() => loadScenario(idx)}
                className={`glass-card p-5 text-left transition-all duration-300 hover:border-[#C9A227]/40 group ${selectedScenario === idx ? 'border-[#C9A227]/60 bg-[#C9A227]/5' : ''}`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                    sc.decision === 'ADVANCE' ? 'bg-emerald-500/20 text-emerald-400' :
                    sc.decision === 'HALT' ? 'bg-red-500/20 text-red-400' :
                    'bg-amber-500/20 text-amber-400'
                  }`}>{sc.decision}</div>
                  <span className="text-xs text-[#64748B] font-mono">{sc.nct}</span>
                </div>
                <h3 className="text-sm font-semibold text-white mb-1">{sc.name}</h3>
                <p className="text-xs text-muted mb-3">{sc.shortName}</p>
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-xs text-[#64748B]">{sc.phase}</span>
                  <span className="text-[#64748B]">·</span>
                  <span className="text-xs text-[#64748B]">{sc.enrollment.toLocaleString()} patients</span>
                  <span className="text-[#64748B]">·</span>
                  <span className="text-xs text-[#64748B]">{sc.sponsor.split(' ')[0]}</span>
                </div>
                <div className="flex items-center gap-2 p-2 rounded bg-[#0A1628]/60 border border-[#C9A227]/10">
                  <Shield className="w-3 h-3 text-[#C9A227] flex-shrink-0" />
                  <span className="text-[10px] font-mono text-[#C9A227]/80">{sc.receiptId}</span>
                  <a href={`https://omnibotgenesis-production.up.railway.app/verify/${sc.receiptId}`} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()} className="ml-auto text-[#64748B] hover:text-[#C9A227]">
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
                <p className="text-xs text-muted mt-2 leading-relaxed">{sc.context}</p>
                <div className="mt-3 flex items-center gap-1 text-xs text-[#C9A227] group-hover:gap-2 transition-all">
                  <span>Load this scenario</span>
                  <ChevronRight className="w-3 h-3" />
                </div>
              </button>
            ))}
          </div>
        </section>

        <div className="grid lg:grid-cols-5 gap-8 mb-12">
          {/* Left panel — parameters */}
          <div className="lg:col-span-2">
            <div className="glass-card p-8 sticky top-32">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center">
                  <FlaskConical className="w-5 h-5 text-emerald-400" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">Trial Profile</h3>
                  <p className="text-xs text-muted">Configure parameters or load a real scenario above</p>
                </div>
              </div>

              <div className="space-y-5">
                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Trial Phase</label>
                  <select
                    value={application.phase}
                    onChange={e => { resetEvaluation(); setApplication(prev => ({ ...prev, phase: e.target.value })) }}
                    className="w-full bg-[#0A1628] border border-[#C9A227]/20 rounded-lg px-4 py-3 text-white text-sm focus:border-[#C9A227] focus:outline-none"
                  >
                    {TRIAL_PHASES.map(p => <option key={p.value} value={p.value}>{p.label} (hist. {(p.successRate * 100).toFixed(0)}%)</option>)}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Therapeutic Area</label>
                  <select
                    value={application.therapeuticArea}
                    onChange={e => { resetEvaluation(); setApplication(prev => ({ ...prev, therapeuticArea: e.target.value })) }}
                    className="w-full bg-[#0A1628] border border-[#C9A227]/20 rounded-lg px-4 py-3 text-white text-sm focus:border-[#C9A227] focus:outline-none"
                  >
                    {THERAPEUTIC_AREAS.map(a => <option key={a.value} value={a.value}>{a.label} (success: {(a.historicalRate * 100).toFixed(0)}%)</option>)}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Preclinical-Clinical Alignment</label>
                  <div className="flex items-center gap-3">
                    <input
                      type="range" min={0} max={100} step={5}
                      value={application.preclinicalAlignment}
                      onChange={e => { resetEvaluation(); setApplication(prev => ({ ...prev, preclinicalAlignment: parseInt(e.target.value) })) }}
                      className="flex-1 accent-[#C9A227]"
                    />
                    <span className={`font-semibold text-sm w-16 text-right ${application.preclinicalAlignment >= 70 ? 'text-emerald-400' : application.preclinicalAlignment >= 50 ? 'text-amber-400' : 'text-red-400'}`}>
                      {application.preclinicalAlignment}%
                    </span>
                  </div>
                  <p className="text-xs text-[#64748B] mt-1">How well preclinical data translates to clinical signals</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Adverse Event Severity</label>
                  <div className="flex items-center gap-3">
                    <input
                      type="range" min={0} max={5} step={1}
                      value={application.adverseEventSeverity}
                      onChange={e => { resetEvaluation(); setApplication(prev => ({ ...prev, adverseEventSeverity: parseInt(e.target.value) })) }}
                      className="flex-1 accent-[#C9A227]"
                    />
                    <span className={`font-semibold text-sm w-24 text-right ${application.adverseEventSeverity <= 1 ? 'text-emerald-400' : application.adverseEventSeverity <= 3 ? 'text-amber-400' : 'text-red-400'}`}>
                      {['None', 'Mild', 'Moderate', 'Moderate-Severe', 'Severe', 'Life-Threatening'][application.adverseEventSeverity]}
                    </span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Patient Enrollment Rate</label>
                  <div className="flex items-center gap-3">
                    <input
                      type="range" min={0} max={100} step={5}
                      value={application.enrollmentRate}
                      onChange={e => { resetEvaluation(); setApplication(prev => ({ ...prev, enrollmentRate: parseInt(e.target.value) })) }}
                      className="flex-1 accent-[#C9A227]"
                    />
                    <span className={`font-semibold text-sm w-16 text-right ${application.enrollmentRate >= 70 ? 'text-emerald-400' : application.enrollmentRate >= 45 ? 'text-amber-400' : 'text-red-400'}`}>
                      {application.enrollmentRate}%
                    </span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Regulatory Designation</label>
                  <select
                    value={application.regulatoryDesignation}
                    onChange={e => { resetEvaluation(); setApplication(prev => ({ ...prev, regulatoryDesignation: e.target.value })) }}
                    className="w-full bg-[#0A1628] border border-[#C9A227]/20 rounded-lg px-4 py-3 text-white text-sm focus:border-[#C9A227] focus:outline-none"
                  >
                    {REGULATORY_DESIGNATIONS.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
                  </select>
                </div>

                <button
                  onClick={runGovernanceEvaluation}
                  disabled={isEvaluating}
                  className={`w-full btn-primary flex items-center justify-center gap-2 py-4 ${isEvaluating ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {isEvaluating ? (
                    <><Activity className="w-5 h-5 animate-spin" />Evaluating...</>
                  ) : (
                    <><Shield className="w-5 h-5" />Run Governance Evaluation</>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Right panel — checkpoints */}
          <div className="lg:col-span-3 space-y-4">
            {checkpoints.length === 0 ? (
              <div className="glass-card p-12 text-center">
                <div className="w-20 h-20 rounded-full bg-emerald-500/10 flex items-center justify-center mx-auto mb-6">
                  <Microscope className="w-10 h-10 text-emerald-400" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">6-Checkpoint Clinical Governance Engine</h3>
                <p className="text-muted max-w-md mx-auto mb-8">
                  Select a real validated scenario above or configure a custom trial profile. Click "Run Governance Evaluation" to see each checkpoint evaluate in real time.
                </p>
                <div className="grid grid-cols-3 gap-4 max-w-lg mx-auto">
                  {[
                    { icon: <Target className="w-4 h-4" />, label: 'Success Prob.' },
                    { icon: <AlertTriangle className="w-4 h-4" />, label: 'AE Exposure' },
                    { icon: <Layers className="w-4 h-4" />, label: 'Preclin. Align.' },
                    { icon: <TrendingUp className="w-4 h-4" />, label: 'Enrollment' },
                    { icon: <FileCheck className="w-4 h-4" />, label: 'Regulatory' },
                    { icon: <Brain className="w-4 h-4" />, label: 'Signal Contrad.' },
                  ].map((cp, i) => (
                    <div key={i} className="flex flex-col items-center gap-2 p-3 rounded-lg bg-[#0A1628]/40 border border-emerald-500/10">
                      <div className="text-emerald-400">{cp.icon}</div>
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
                          <p className="text-xs text-[#64748B] font-mono">CP-{index + 1}</p>
                          <h4 className="text-sm font-semibold text-white">{cp.name}</h4>
                          <p className="text-xs text-muted">{cp.genericName}</p>
                        </div>
                      </div>
                      <div className="text-right flex-shrink-0">
                        {cp.status === 'evaluating' ? (
                          <div className="flex items-center gap-2 text-blue-400">
                            <Clock className="w-4 h-4 animate-pulse" />
                            <span className="text-sm">Evaluating...</span>
                          </div>
                        ) : cp.status !== 'pending' ? (
                          <div className="flex flex-col items-end gap-1">
                            <div className="flex items-center gap-1">
                              {cp.status === 'pass' ? <CheckCircle className="w-5 h-5 text-emerald-400" /> :
                               cp.status === 'warn' ? <AlertTriangle className="w-5 h-5 text-amber-400" /> :
                               <XCircle className="w-5 h-5 text-red-400" />}
                              <span className={`text-sm font-bold ${cp.status === 'pass' ? 'text-emerald-400' : cp.status === 'warn' ? 'text-amber-400' : 'text-red-400'}`}>
                                {cp.status === 'pass' ? 'PASS' : cp.status === 'warn' ? 'MARGINAL' : 'BLOCKED'}
                              </span>
                            </div>
                            <span className="text-xs text-[#64748B]">
                              Score: <span className="text-white font-mono">{cp.score}</span>
                              <span className="mx-1">{cp.thresholdType === 'min' ? '≥' : '≤'}</span>
                              <span className="text-white font-mono">{cp.threshold}</span>
                            </span>
                          </div>
                        ) : (
                          <span className="text-xs text-[#64748B]">Pending</span>
                        )}
                      </div>
                    </div>

                    {cp.status !== 'pending' && cp.status !== 'evaluating' && (
                      <div className="mt-3 space-y-2">
                        <div className="w-full bg-[#0A1628] rounded-full h-2">
                          <div
                            className={`h-2 rounded-full transition-all duration-1000 ${cp.status === 'pass' ? 'bg-emerald-500' : cp.status === 'warn' ? 'bg-amber-500' : 'bg-red-500'}`}
                            style={{ width: `${Math.min(100, cp.score)}%` }}
                          />
                        </div>
                        <p className="text-xs text-muted leading-relaxed">{cp.reasoning}</p>
                        <p className="text-xs text-[#475569] font-mono bg-[#0A1628]/40 px-3 py-2 rounded">{cp.detail}</p>
                      </div>
                    )}
                  </div>
                ))}

                {evaluationComplete && decision && (
                  <div className={`glass-card p-6 border ${decision.bg}`}>
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        {decision.decision === 'ADVANCE' ? <CheckCircle className={`w-7 h-7 ${decision.color}`} /> :
                         decision.decision === 'HALT' ? <XCircle className={`w-7 h-7 ${decision.color}`} /> :
                         <AlertTriangle className={`w-7 h-7 ${decision.color}`} />}
                        <div>
                          <p className="text-xs text-[#64748B] uppercase tracking-wider">Governance Decision</p>
                          <h3 className={`text-2xl font-bold ${decision.color}`}>{decision.decision}</h3>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-muted">Checkpoints Cleared</p>
                        <p className="text-xl font-bold text-white">{decision.passed} / 6</p>
                      </div>
                    </div>
                    <p className="text-sm text-muted leading-relaxed">{decision.reason}</p>
                    {selectedScenario !== null && (
                      <div className="mt-4 p-3 rounded-lg bg-[#0A1628]/60 border border-[#C9A227]/10">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-xs text-[#64748B] mb-1">Real PQC-Signed Receipt — {REAL_VALIDATED_SCENARIOS[selectedScenario].nct}</p>
                            <p className="text-sm font-mono text-[#C9A227]">{REAL_VALIDATED_SCENARIOS[selectedScenario].receiptId}</p>
                          </div>
                          <a
                            href={`https://omnibotgenesis-production.up.railway.app/verify/${REAL_VALIDATED_SCENARIOS[selectedScenario].receiptId}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-2 text-xs text-[#C9A227] hover:text-white transition-colors"
                          >
                            Verify on-chain <ExternalLink className="w-3 h-3" />
                          </a>
                        </div>
                        <p className="text-xs text-[#64748B] mt-1">Signed with Dilithium-3 (NIST-standardized algorithm) · Immutable audit record</p>
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        {/* Domain Adapter Explanation */}
        <section className="glass-card p-8 mb-12">
          <div className="flex items-center gap-3 mb-6">
            <BarChart3 className="w-6 h-6 text-[#C9A227]" />
            <h2 className="text-lg font-semibold text-white">How the Same Engine Applies to Clinical Trials</h2>
          </div>
          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-sm font-semibold text-[#C9A227] uppercase tracking-wider mb-4">6-Checkpoint Signal Mapping</h3>
              <div className="space-y-3">
                {[
                  { cp: 'CP-1', trading: 'Expected win probability', biotech: 'Trial success probability (phase + area historical rate)' },
                  { cp: 'CP-2', trading: 'Risk exposure limits', biotech: 'Adverse event severity (lower is safer, threshold ≤65)' },
                  { cp: 'CP-3', trading: 'Multi-model signal coherence', biotech: 'Preclinical-to-clinical alignment score' },
                  { cp: 'CP-4', trading: 'Trend temporal persistence', biotech: 'Patient enrollment momentum trajectory' },
                  { cp: 'CP-5', trading: 'Stress scenario resilience', biotech: 'Regulatory pathway strength (FDA designation)' },
                  { cp: 'CP-6', trading: 'Internal signal contradiction', biotech: 'Cross-signal contradiction index (DCI equivalent)' },
                ].map(row => (
                  <div key={row.cp} className="grid grid-cols-3 gap-3 text-xs">
                    <span className="font-mono text-[#C9A227] font-semibold">{row.cp}</span>
                    <span className="text-[#64748B]">{row.trading}</span>
                    <span className="text-white">{row.biotech}</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-[#C9A227] uppercase tracking-wider mb-4">Architecture — Domain Adapter Pattern</h3>
              <p className="text-sm text-muted leading-relaxed mb-4">
                The core governance engine is domain-agnostic. It accepts 6 normalized signals (0–100)
                and applies the same fail-closed 8-checkpoint evaluation, regardless of domain.
                The <strong className="text-white">Domain Adapter</strong> translates domain-specific data
                (clinical signals, AE reports, enrollment data) into those 6 normalized inputs.
              </p>
              <p className="text-sm text-muted leading-relaxed">
                The 3 scenarios above are real ClinicalTrials.gov trials with real NCT IDs. Their signals
                were computed from published trial characteristics and submitted through the live governance API,
                generating verifiable PQC-signed receipts on the OMNIX production infrastructure.
              </p>
              <div className="mt-4 grid grid-cols-3 gap-3 text-center">
                <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                  <p className="text-lg font-bold text-emerald-400">ADVANCE</p>
                  <p className="text-xs text-muted">All 6 passed</p>
                </div>
                <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                  <p className="text-lg font-bold text-amber-400">REVIEW</p>
                  <p className="text-xs text-muted">1 blocked</p>
                </div>
                <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                  <p className="text-lg font-bold text-red-400">HALT</p>
                  <p className="text-xs text-muted">2+ blocked</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Receipt verification strip */}
        <section className="glass-card p-6">
          <div className="flex items-center gap-3 mb-4">
            <Shield className="w-5 h-5 text-[#C9A227]" />
            <h2 className="text-sm font-semibold text-white uppercase tracking-wider">Real Production Receipts — Verifiable Now</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-4">
            {REAL_VALIDATED_SCENARIOS.map(sc => (
              <a
                key={sc.receiptId}
                href={`https://omnibotgenesis-production.up.railway.app/verify/${sc.receiptId}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-3 rounded-lg bg-[#0A1628]/60 border border-[#C9A227]/10 hover:border-[#C9A227]/40 transition-all group"
              >
                <div>
                  <p className="text-xs text-[#64748B] mb-0.5">{sc.name} · {sc.nct}</p>
                  <p className="text-xs font-mono text-[#C9A227]">{sc.receiptId}</p>
                  <p className={`text-[10px] font-bold mt-1 ${sc.decision === 'ADVANCE' ? 'text-emerald-400' : sc.decision === 'HALT' ? 'text-red-400' : 'text-amber-400'}`}>
                    {sc.decision} · {sc.checkpointsPassed}/{sc.checkpointsTotal} checkpoints
                  </p>
                </div>
                <ExternalLink className="w-4 h-4 text-[#64748B] group-hover:text-[#C9A227] transition-colors" />
              </a>
            ))}
          </div>
          <p className="text-xs text-[#64748B] mt-4">
            Each receipt is signed with Dilithium-3 (NIST-standardized post-quantum algorithm) and stored immutably on the OMNIX governance infrastructure.
            NCT data sourced from ClinicalTrials.gov (U.S. National Library of Medicine).
          </p>
        </section>
      </main>
    </div>
  )
}
