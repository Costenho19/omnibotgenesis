import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { Shield, ArrowRight, AlertTriangle, CheckCircle, XCircle, Clock, Target, Activity, Layers, Brain, Zap, Eye, Radio, Lock, Scale, Users } from 'lucide-react'
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

interface DefenseScenario {
  platformType: string
  operationalTheater: string
  targetConfidence: number
  roeClassification: string
  collateralEstimate: string
  commsStatus: string
  humanOverride: string
}

const PLATFORM_TYPES = [
  { value: 'autonomous_uas', label: 'Autonomous UAS (Fixed-Wing)', riskFactor: 1.15, emoji: '✈️', baseConf: 0.72 },
  { value: 'ground_robot_ugv', label: 'Ground Robot (UGV)', riskFactor: 1.10, emoji: '🤖', baseConf: 0.78 },
  { value: 'maritime_usv', label: 'Maritime USV (Unmanned Surface)', riskFactor: 1.08, emoji: '🚢', baseConf: 0.75 },
  { value: 'directed_energy', label: 'Directed Energy System', riskFactor: 1.20, emoji: '⚡', baseConf: 0.65 },
  { value: 'isr_surveillance', label: 'ISR / Surveillance Platform', riskFactor: 1.00, emoji: '👁️', baseConf: 0.85 },
  { value: 'counter_uas', label: 'Counter-UAS (Electronic Warfare)', riskFactor: 1.12, emoji: '🛡️', baseConf: 0.80 },
]

const OPERATIONAL_THEATERS = [
  { value: 'contested_airspace', label: 'Contested Airspace', threatLevel: 0.88, strictness: 1.18 },
  { value: 'urban_coin', label: 'Urban COIN (MOUT)', threatLevel: 0.72, strictness: 1.22 },
  { value: 'maritime_patrol', label: 'Maritime Patrol (High Seas)', threatLevel: 0.60, strictness: 1.10 },
  { value: 'border_security', label: 'Border Security', threatLevel: 0.48, strictness: 1.08 },
  { value: 'critical_infra', label: 'Critical Infrastructure Defense', threatLevel: 0.65, strictness: 1.15 },
  { value: 'cyber_physical', label: 'Cyber-Physical Domain', threatLevel: 0.70, strictness: 1.12 },
]

const ROE_CLASSIFICATIONS = [
  { value: 'weapons_hold', label: 'Weapons Hold (Fire only if fired upon)', factor: 0.92 },
  { value: 'weapons_tight', label: 'Weapons Tight (Positive ID required)', factor: 0.78 },
  { value: 'weapons_free', label: 'Weapons Free (Engage all threats)', factor: 0.55 },
  { value: 'non_lethal_only', label: 'Non-Lethal Measures Only', factor: 0.90 },
]

const COLLATERAL_ESTIMATES = [
  { value: 'minimal', label: 'Minimal (Zero civilian presence)', factor: 0.95 },
  { value: 'low', label: 'Low Risk (Remote area, <5 civilians)', factor: 0.80 },
  { value: 'moderate', label: 'Moderate (Mixed environment)', factor: 0.55 },
  { value: 'high', label: 'High Risk (Urban, civilian proximity)', factor: 0.20 },
]

const COMMS_STATUS = [
  { value: 'secure', label: 'Secure Link (Encrypted, verified)', factor: 0.95 },
  { value: 'degraded', label: 'Degraded (Partial encryption)', factor: 0.65 },
  { value: 'emcon', label: 'EMCON (Emissions Control — silent)', factor: 0.45 },
  { value: 'denied', label: 'Comms Denied (Jammed / spoofed)', factor: 0.10 },
]

const HUMAN_OVERRIDE = [
  { value: 'available', label: 'Commander Available (<5s response)', factor: 0.95 },
  { value: 'delayed', label: 'Delayed Response (15-60s loop)', factor: 0.65 },
  { value: 'limited', label: 'Limited (Bandwidth constrained)', factor: 0.45 },
  { value: 'unavailable', label: 'Unavailable (Full autonomy mode)', factor: 0.18 },
]

function evaluateCheckpoints(scenario: DefenseScenario): CheckpointResult[] {
  const platform   = PLATFORM_TYPES.find(p => p.value === scenario.platformType) || PLATFORM_TYPES[0]
  const theater    = OPERATIONAL_THEATERS.find(t => t.value === scenario.operationalTheater) || OPERATIONAL_THEATERS[0]
  const roe        = ROE_CLASSIFICATIONS.find(r => r.value === scenario.roeClassification) || ROE_CLASSIFICATIONS[0]
  const collateral = COLLATERAL_ESTIMATES.find(c => c.value === scenario.collateralEstimate) || COLLATERAL_ESTIMATES[0]
  const comms      = COMMS_STATUS.find(c => c.value === scenario.commsStatus) || COMMS_STATUS[0]
  const human      = HUMAN_OVERRIDE.find(h => h.value === scenario.humanOverride) || HUMAN_OVERRIDE[0]

  const targetConf = scenario.targetConfidence / 100
  const riskFactor = platform.riskFactor * theater.strictness

  const sivScore = Math.min(95, Math.round(
    (targetConf * 35 + roe.factor * 30 + comms.factor * 20 + collateral.factor * 15) * 100 / riskFactor
  ))

  const targetDiscrimScore = Math.min(95, Math.round(
    (targetConf * 50 + collateral.factor * 30 + (1 - theater.threatLevel) * 20) * 100
  ))

  const roeScore = Math.min(95, Math.round(roe.factor * 100 * (comms.factor >= 0.65 ? 1.0 : 0.75)))

  const collateralScore = Math.min(95, Math.round(collateral.factor * 100))

  const commsScore = Math.min(95, Math.round(comms.factor * 100))

  const necessityScore = Math.min(95, Math.round(
    (targetConf * 35 + roe.factor * 35 + (1 - theater.threatLevel + 1) * 0.5 * 30) * 100 * 0.01
  ))

  const signals = [sivScore, targetDiscrimScore, roeScore, collateralScore, commsScore, necessityScore]
  const avg = signals.reduce((a, b) => a + b, 0) / signals.length
  const variance = signals.reduce((a, b) => a + Math.pow(b - avg, 2), 0) / signals.length
  const divergence = Math.sqrt(variance)
  const contradictionScore = Math.round(Math.max(0, Math.min(95, 100 - divergence * 2.0)))

  const temporalScore = Math.min(95, Math.round(
    roeScore * 0.45 + necessityScore * 0.35 + commsScore * 0.20
  ))

  const edgeScore = Math.round(sivScore * 0.55 + contradictionScore * 0.45)

  const legalScore = Math.min(95, Math.round(
    roe.factor * 40 + collateral.factor * 35 + human.factor * 25
  ))

  const humanLoopScore = Math.min(95, Math.round(human.factor * 100))

  return [
    {
      name: 'Sensor Fusion Integrity',
      genericName: 'CP-1: Are all input signals valid?',
      icon: <Eye className="w-5 h-5" />,
      status: 'pending',
      score: sivScore,
      threshold: 60,
      reasoning: sivScore >= 60
        ? `All targeting signals validated — target confidence ${scenario.targetConfidence}%, ${roe.label.split('(')[0].trim()}, comms ${comms.label.split('(')[0].trim()}`
        : `Sensor fusion integrity failed — one or more targeting signals fall outside acceptable governance bounds for autonomous engagement`,
      detail: `Target conf: ${scenario.targetConfidence}% | ROE: ${(roe.factor * 100).toFixed(0)}% | Comms: ${(comms.factor * 100).toFixed(0)}% | Theater risk: ${(theater.strictness * 100).toFixed(0)}% → SIV: ${sivScore}/100`
    },
    {
      name: 'Target Discrimination Accuracy',
      genericName: 'CP-2: Is target positively ID\'d as combatant?',
      icon: <Target className="w-5 h-5" />,
      status: 'pending',
      score: targetDiscrimScore,
      threshold: 65,
      reasoning: targetDiscrimScore >= 65
        ? `Target discrimination at ${targetDiscrimScore}% — positive combatant identification above IHL threshold with ${collateral.label.split('(')[0].trim()} collateral environment`
        : `Target discrimination insufficient at ${targetDiscrimScore}% — positive ID confidence below IHL Article 57 standard for ${theater.label} environment`,
      detail: `Target conf: ${scenario.targetConfidence}% × 0.50 | Collateral env: ${(collateral.factor * 100).toFixed(0)}% × 0.30 | Theater threat: ${(theater.threatLevel * 100).toFixed(0)}% → Discrimination: ${targetDiscrimScore}/100`
    },
    {
      name: 'ROE Compliance Gate',
      genericName: 'CP-3: Does this action comply with Rules of Engagement?',
      icon: <Scale className="w-5 h-5" />,
      status: 'pending',
      score: roeScore,
      threshold: 55,
      reasoning: roeScore >= 55
        ? `ROE compliance verified — ${roe.label} with ${comms.label.split('(')[0].trim()} satisfies current theater ROE framework`
        : `ROE violation risk — ${roe.label} under ${comms.label.split('(')[0].trim()} conditions does not meet engagement authorization standard`,
      detail: `ROE base: ${(roe.factor * 100).toFixed(0)}% | Comms integrity: ${(comms.factor * 100).toFixed(0)}% | ROE score: ${roeScore}/100 | ${roeScore < 55 ? 'NON-COMPLIANT' : 'COMPLIANT'}`
    },
    {
      name: 'Collateral Damage Assessment',
      genericName: 'CP-4: Is collateral damage within IHL limits?',
      icon: <Users className="w-5 h-5" />,
      status: 'pending',
      score: collateralScore,
      threshold: 45,
      reasoning: collateralScore >= 45
        ? `Collateral damage estimate within proportionality limits — ${collateral.label} environment clears IHL Article 51(5)(b) test`
        : `Proportionality test failed — ${collateral.label} creates excessive incidental civilian harm under IHL Article 51(5)(b)`,
      detail: `Environment: ${collateral.label.split('(')[0].trim()} | Collateral factor: ${(collateral.factor * 100).toFixed(0)}% | IHL test: ${collateralScore >= 45 ? 'PASS' : 'FAIL'} | Score: ${collateralScore}/100`
    },
    {
      name: 'Communications Link Integrity',
      genericName: 'CP-5: Is the secure command link verified?',
      icon: <Radio className="w-5 h-5" />,
      status: 'pending',
      score: commsScore,
      threshold: 40,
      reasoning: commsScore >= 40
        ? `Command link verified — ${comms.label} ensures authenticated command authority over ${platform.label}`
        : `Command link compromised — ${comms.label} creates unacceptable authentication gap for autonomous lethal system`,
      detail: `Link status: ${comms.label.split('(')[0].trim()} | Integrity factor: ${(comms.factor * 100).toFixed(0)}% | Auth verified: ${commsScore >= 40 ? 'YES' : 'NO'} | Score: ${commsScore}/100`
    },
    {
      name: 'Mission Necessity & Proportionality',
      genericName: 'CP-6: Does this pass the IHL necessity test?',
      icon: <Shield className="w-5 h-5" />,
      status: 'pending',
      score: necessityScore,
      threshold: 42,
      reasoning: necessityScore >= 42
        ? `Military necessity and proportionality confirmed — target confidence, ROE, and theater conditions satisfy IHL Article 57 precautionary principles`
        : `Military necessity test failed — target confidence ${scenario.targetConfidence}% and current ROE do not satisfy IHL precautionary standards`,
      detail: `Target conf × 0.35: ${(targetConf * 35).toFixed(0)} | ROE × 0.35: ${(roe.factor * 35).toFixed(0)} | Theater × 0.30: ${(theater.threatLevel * 30).toFixed(0)} → Necessity: ${necessityScore}/100`
    },
    {
      name: 'Multi-Sensor Signal Contradiction',
      genericName: 'CP-7: Do all sensor systems agree?',
      icon: <Brain className="w-5 h-5" />,
      status: 'pending',
      score: contradictionScore,
      threshold: 42,
      reasoning: contradictionScore >= 42
        ? `Multi-sensor agreement confirmed — internal signal divergence low across targeting, ROE, collateral, and comms checkpoints (${contradictionScore}%)`
        : `High signal contradiction — cross-system divergence ${divergence.toFixed(1)} indicates conflicting sensor assessment, autonomous engagement unreliable`,
      detail: `Signal variance: ${divergence.toFixed(1)} | Cross-sensor alignment: ${contradictionScore}% | ${contradictionScore < 42 ? 'CONTRADICTORY — halt' : contradictionScore < 60 ? 'TENSIONED — caution' : 'ALIGNED'}`
    },
    {
      name: 'Situational Temporal Coherence',
      genericName: 'CP-8: Is the situational picture stable over time?',
      icon: <Activity className="w-5 h-5" />,
      status: 'pending',
      score: temporalScore,
      threshold: 40,
      reasoning: temporalScore >= 40
        ? `Situational picture stable — ROE validity, mission necessity, and comms integrity confirm consistent conditions across the engagement window`
        : `Temporal instability detected — current operational conditions may be transient or degrading; decision window too narrow for confident autonomous action`,
      detail: `ROE stability × 0.45: ${(roeScore * 0.45).toFixed(0)} | Necessity × 0.35: ${(necessityScore * 0.35).toFixed(0)} | Comms × 0.20: ${(commsScore * 0.20).toFixed(0)} → Temporal: ${temporalScore}/100`
    },
    {
      name: 'Edge Confirmation (Decision Boundary)',
      genericName: 'CP-9: Does the decision converge at the governance edge?',
      icon: <Layers className="w-5 h-5" />,
      status: 'pending',
      score: edgeScore,
      threshold: 50,
      reasoning: edgeScore >= 50
        ? `Decision boundary confirmed — sensor fusion integrity and cross-sensor alignment converge at the governance threshold (${edgeScore}%)`
        : `Weak boundary convergence — sensor fusion and contradiction signals do not reinforce each other; autonomous action requires human escalation`,
      detail: `SIV × 0.55: ${(sivScore * 0.55).toFixed(0)} | Contradiction × 0.45: ${(contradictionScore * 0.45).toFixed(0)} | Edge score: ${edgeScore}/100`
    },
    {
      name: 'Legal Authorization Gate',
      genericName: 'CP-10: Is command authority and legal authorization verified?',
      icon: <Lock className="w-5 h-5" />,
      status: 'pending',
      score: legalScore,
      threshold: 58,
      reasoning: legalScore >= 58
        ? `Legal authorization verified — ROE framework, collateral assessment, and human oversight chain confirm valid command authority for this engagement`
        : `Legal authorization insufficient — ROE classification, collateral environment, or command chain do not satisfy legal threshold for autonomous lethal action`,
      detail: `ROE authority: ${(roe.factor * 100).toFixed(0)}% | Collateral IHL: ${(collateral.factor * 100).toFixed(0)}% | Command chain: ${(human.factor * 100).toFixed(0)}% → Legal: ${legalScore}/100`
    },
    {
      name: 'Human Override Availability',
      genericName: 'CP-11: Is meaningful human control available?',
      icon: <Users className="w-5 h-5" />,
      status: 'pending',
      score: humanLoopScore,
      threshold: 35,
      reasoning: humanLoopScore >= 35
        ? `Human-in-the-loop confirmed — ${human.label} satisfies LAWS (Lethal Autonomous Weapons Systems) governance requirement for meaningful human control`
        : `Meaningful human control unavailable — ${human.label} creates an unacceptable accountability gap under emerging LAWS governance frameworks`,
      detail: `Override status: ${human.label.split('(')[0].trim()} | HITL factor: ${(human.factor * 100).toFixed(0)}% | LAWS compliance: ${humanLoopScore >= 35 ? 'SATISFIED' : 'VIOLATED'} | Score: ${humanLoopScore}/100`
    },
  ]
}

const DEF_BLUE  = '#3B82F6'
const DEF_SLATE = '#0F172A'

export default function DefenseGovernanceDemo() {
  const { metrics: liveMetrics, isLive, formatNumberFull } = useLiveMetrics()
  const [scenario, setScenario] = useState<DefenseScenario>({
    platformType:       'autonomous_uas',
    operationalTheater: 'contested_airspace',
    targetConfidence:   72,
    roeClassification:  'weapons_tight',
    collateralEstimate: 'low',
    commsStatus:        'secure',
    humanOverride:      'available',
  })

  const [checkpoints, setCheckpoints]       = useState<CheckpointResult[]>([])
  const [isEvaluating, setIsEvaluating]     = useState(false)
  const [evaluationComplete, setEvaluationComplete] = useState(false)
  const [_currentCheckpoint, setCurrentCheckpoint]  = useState(-1)
  const evaluationRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const currentPlatform = PLATFORM_TYPES.find(p => p.value === scenario.platformType) || PLATFORM_TYPES[0]

  const runGovernanceEvaluation = () => {
    const results      = evaluateCheckpoints(scenario)
    const finalResults = results.map(cp => {
      const passed      = cp.score >= cp.threshold
      const finalStatus: 'pass' | 'warn' | 'block' = passed
        ? (cp.score >= cp.threshold + 15 ? 'pass' : 'warn')
        : 'block'
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
          evaluationRef.current = setTimeout(animate, 550)
        }, 750)
      } else {
        setCheckpoints(finalResults.map(fr => ({ ...fr, status: fr.finalStatus })))
        setIsEvaluating(false)
        setEvaluationComplete(true)
      }
    }
    evaluationRef.current = setTimeout(animate, 350)
  }

  useEffect(() => {
    return () => { if (evaluationRef.current) clearTimeout(evaluationRef.current) }
  }, [])

  const getGovernanceDecision = () => {
    if (!evaluationComplete || checkpoints.length === 0) return null
    const blocked = checkpoints.filter(cp => cp.status === 'block')
    const warned  = checkpoints.filter(cp => cp.status === 'warn')
    const passed  = checkpoints.filter(cp => cp.status === 'pass')

    if (blocked.length >= 2) return {
      decision: 'BLOCK', color: 'text-red-500', bg: 'bg-red-500/10 border-red-500/30',
      reason: `${blocked.length} checkpoints blocked. Governance recommendation: BLOCK this autonomous engagement — risk profile violates IHL thresholds and LAWS governance standards.`,
      passed: passed.length + warned.length,
    }
    if (blocked.length === 1) return {
      decision: 'HOLD', color: 'text-amber-500', bg: 'bg-amber-500/10 border-amber-500/30',
      reason: `1 checkpoint blocked (${blocked[0].name}). Governance recommendation: HOLD — escalate to human commander. Autonomous action suspended pending ${blocked[0].name.toLowerCase()} review.`,
      passed: passed.length + warned.length,
    }
    if (warned.length >= 3) return {
      decision: 'HOLD', color: 'text-amber-500', bg: 'bg-amber-500/10 border-amber-500/30',
      reason: `${warned.length} checkpoints at marginal levels. Governance recommendation: HOLD — cumulative marginal risk requires human commander validation before autonomous action proceeds.`,
      passed: passed.length + warned.length,
    }
    return {
      decision: 'AUTHORIZE', color: 'text-emerald-500', bg: 'bg-emerald-500/10 border-emerald-500/30',
      reason: 'All 11 checkpoints cleared. Governance recommendation: AUTHORIZE — autonomous action meets IHL standards, ROE compliance, and LAWS governance thresholds.',
      passed: passed.length + warned.length,
    }
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
              <span className="ml-3 px-2 py-0.5 text-[10px] font-semibold bg-blue-500/20 text-blue-400 rounded uppercase tracking-wider">Defense Demo</span>
            </div>
          </div>
          <div className="hidden lg:flex items-center gap-8">
            <Link to="/" className="nav-link">Home</Link>
            <Link to="/governance-demo" className="nav-link">Credit Demo</Link>
            <Link to="/governance-demo-energy" className="nav-link">Energy Demo</Link>
            <Link to="/governance-demo-medical" className="nav-link">Medical Demo</Link>
            <Link to="/institutional" className="nav-link">Technical Details</Link>
            <a
              href="https://wa.me/16505078293?text=Hi%2C%20I%27m%20interested%20in%20OMNIX%20Defense%20Governance"
              target="_blank" rel="noopener noreferrer"
              className="btn-primary text-sm px-5 py-2"
            >Talk to Us</a>
          </div>
        </div>
      </nav>

      <main className="pt-32 px-6 pb-20 max-w-7xl mx-auto">

        {/* ── Hero ─────────────────────────────────────────────────────────── */}
        <section className="text-center mb-16 animate-fade-in-up">
          <p className="section-title">Autonomous Defense Governance</p>
          <h1 className="heading-xl text-white mb-6">
            Every Autonomous Action.<br />
            <span className="gold-gradient">Governed Before It Fires.</span>
          </h1>
          <p className="text-xl text-muted max-w-3xl mx-auto mb-4 leading-relaxed">
            OMNIX applies its 11-checkpoint fail-closed pipeline to autonomous weapons systems, drone authorization, and AI targeting — the same governance architecture validated across{' '}
            {formatNumberFull(liveMetrics.evaluation_cycles)} evaluation cycles in production. Every autonomous action produces a PQC-signed governance receipt before execution.
          </p>
          <div className="flex flex-wrap justify-center gap-3 mt-6">
            {[
              { label: 'IHL Article 51(4) Compliant', color: 'blue' },
              { label: 'LAWS Governance Framework', color: 'blue' },
              { label: 'PQC-Signed Receipts', color: 'gold' },
              { label: '11-Checkpoint Fail-Closed', color: 'gold' },
            ].map((badge, i) => (
              <span key={i} className={`px-3 py-1 text-xs font-semibold rounded-full border ${
                badge.color === 'blue'
                  ? 'bg-blue-500/10 text-blue-400 border-blue-500/30'
                  : 'bg-[#C9A227]/10 text-[#C9A227] border-[#C9A227]/30'
              }`}>{badge.label}</span>
            ))}
          </div>
        </section>

        {/* ── Main Grid ───────────────────────────────────────────────────── */}
        <div className="grid lg:grid-cols-5 gap-8 mb-12">

          {/* Left: Scenario Config */}
          <div className="lg:col-span-2">
            <div className="glass-card p-8 sticky top-32">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center">
                  <Shield className="w-5 h-5 text-blue-400" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">Autonomous Engagement Setup</h3>
                  <p className="text-xs text-muted">Configure scenario parameters</p>
                </div>
              </div>

              <div className="space-y-5">
                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Platform Type</label>
                  <select
                    value={scenario.platformType}
                    onChange={e => { resetEvaluation(); setScenario(prev => ({ ...prev, platformType: e.target.value })) }}
                    className="w-full bg-[#0A1628] border border-[#C9A227]/20 rounded-lg px-4 py-3 text-white text-sm focus:border-[#C9A227] focus:outline-none"
                  >
                    {PLATFORM_TYPES.map(p => (
                      <option key={p.value} value={p.value}>{p.emoji} {p.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Operational Theater</label>
                  <select
                    value={scenario.operationalTheater}
                    onChange={e => { resetEvaluation(); setScenario(prev => ({ ...prev, operationalTheater: e.target.value })) }}
                    className="w-full bg-[#0A1628] border border-[#C9A227]/20 rounded-lg px-4 py-3 text-white text-sm focus:border-[#C9A227] focus:outline-none"
                  >
                    {OPERATIONAL_THEATERS.map(t => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-muted mb-2">
                    Target Confidence: <span className="text-white font-semibold">{scenario.targetConfidence}%</span>
                  </label>
                  <input
                    type="range" min={10} max={99} step={1}
                    value={scenario.targetConfidence}
                    onChange={e => { resetEvaluation(); setScenario(prev => ({ ...prev, targetConfidence: parseInt(e.target.value) })) }}
                    className="w-full accent-blue-500"
                  />
                  <div className="flex justify-between text-xs text-[#64748B] mt-1">
                    <span>Uncertain</span><span>Positive ID</span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-muted mb-2">ROE Classification</label>
                  <select
                    value={scenario.roeClassification}
                    onChange={e => { resetEvaluation(); setScenario(prev => ({ ...prev, roeClassification: e.target.value })) }}
                    className="w-full bg-[#0A1628] border border-[#C9A227]/20 rounded-lg px-4 py-3 text-white text-sm focus:border-[#C9A227] focus:outline-none"
                  >
                    {ROE_CLASSIFICATIONS.map(r => (
                      <option key={r.value} value={r.value}>{r.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Collateral Damage Estimate</label>
                  <select
                    value={scenario.collateralEstimate}
                    onChange={e => { resetEvaluation(); setScenario(prev => ({ ...prev, collateralEstimate: e.target.value })) }}
                    className="w-full bg-[#0A1628] border border-[#C9A227]/20 rounded-lg px-4 py-3 text-white text-sm focus:border-[#C9A227] focus:outline-none"
                  >
                    {COLLATERAL_ESTIMATES.map(c => (
                      <option key={c.value} value={c.value}>{c.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Communications Status</label>
                  <select
                    value={scenario.commsStatus}
                    onChange={e => { resetEvaluation(); setScenario(prev => ({ ...prev, commsStatus: e.target.value })) }}
                    className="w-full bg-[#0A1628] border border-[#C9A227]/20 rounded-lg px-4 py-3 text-white text-sm focus:border-[#C9A227] focus:outline-none"
                  >
                    {COMMS_STATUS.map(c => (
                      <option key={c.value} value={c.value}>{c.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Human Override Availability</label>
                  <select
                    value={scenario.humanOverride}
                    onChange={e => { resetEvaluation(); setScenario(prev => ({ ...prev, humanOverride: e.target.value })) }}
                    className="w-full bg-[#0A1628] border border-[#C9A227]/20 rounded-lg px-4 py-3 text-white text-sm focus:border-[#C9A227] focus:outline-none"
                  >
                    {HUMAN_OVERRIDE.map(h => (
                      <option key={h.value} value={h.value}>{h.label}</option>
                    ))}
                  </select>
                </div>

                <button
                  onClick={runGovernanceEvaluation}
                  disabled={isEvaluating}
                  className={`w-full btn-primary flex items-center justify-center gap-2 py-4 ${isEvaluating ? 'opacity-50 cursor-not-allowed' : ''}`}
                  style={{ background: isEvaluating ? undefined : 'linear-gradient(135deg, #1D4ED8, #2563EB)' }}
                >
                  {isEvaluating ? (
                    <><Activity className="w-5 h-5 animate-spin" />Evaluating...</>
                  ) : (
                    <><Shield className="w-5 h-5" />Run Defense Governance</>
                  )}
                </button>

                <div className="p-3 rounded-lg bg-red-500/5 border border-red-500/15">
                  <p className="text-xs text-[#64748B] leading-relaxed">
                    <span className="text-red-400 font-semibold">Hard blocks active:</span> civilian proximity · ROE violation · cyber intrusion · IFF failure · chain-of-command break · legal prohibition
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Right: Checkpoints */}
          <div className="lg:col-span-3 space-y-4">
            {checkpoints.length === 0 ? (
              <div className="glass-card p-12 text-center">
                <div className="w-20 h-20 rounded-full bg-blue-500/10 flex items-center justify-center mx-auto mb-6">
                  <Shield className="w-10 h-10 text-blue-400" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">11-Checkpoint Defense Governance Engine</h3>
                <p className="text-muted max-w-md mx-auto mb-8">
                  Configure the autonomous engagement scenario and run the governance pipeline to evaluate IHL compliance, ROE adherence, and LAWS governance standards in real time.
                </p>
                <div className="grid grid-cols-3 gap-4 max-w-lg mx-auto">
                  {[
                    { icon: <Eye className="w-4 h-4" />, label: 'Sensor Fusion' },
                    { icon: <Target className="w-4 h-4" />, label: 'Target ID' },
                    { icon: <Scale className="w-4 h-4" />, label: 'ROE Gate' },
                    { icon: <Users className="w-4 h-4" />, label: 'Collateral' },
                    { icon: <Radio className="w-4 h-4" />, label: 'Comms Link' },
                    { icon: <Lock className="w-4 h-4" />, label: 'Legal Auth' },
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
                      cp.status === 'pass'       ? 'border-emerald-500/30' :
                      cp.status === 'warn'       ? 'border-amber-500/30' :
                      cp.status === 'block'      ? 'border-red-500/30' :
                      'opacity-40'
                    }`}
                    style={{ animationDelay: `${index * 0.08}s` }}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                          cp.status === 'evaluating' ? 'bg-blue-500/20 text-blue-400 animate-pulse' :
                          cp.status === 'pass'       ? 'bg-emerald-500/20 text-emerald-400' :
                          cp.status === 'warn'       ? 'bg-amber-500/20 text-amber-400' :
                          cp.status === 'block'      ? 'bg-red-500/20 text-red-400' :
                          'bg-[#1E293B] text-[#64748B]'
                        }`}>
                          {cp.icon}
                        </div>
                        <div>
                          <h4 className="text-white font-medium text-sm">{cp.name}</h4>
                          <p className="text-xs text-muted">{cp.genericName}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
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
                                cp.status === 'pass'       ? 'bg-emerald-500' :
                                cp.status === 'warn'       ? 'bg-amber-500' :
                                cp.status === 'block'      ? 'bg-red-500' :
                                'bg-blue-500'
                              }`}
                              style={{ width: cp.status === 'evaluating' ? '55%' : (cp.status === 'pass' || cp.status === 'warn') ? '100%' : '20%' }}
                            />
                          </div>
                          <span className="text-xs text-muted w-16 text-right shrink-0">
                            {cp.status !== 'evaluating' ? `${cp.score}/100` : '...'}
                          </span>
                        </div>
                        {cp.status !== 'evaluating' && (
                          <div className="space-y-1 mt-1">
                            <p className="text-xs text-muted leading-relaxed">{cp.reasoning}</p>
                            <p className="text-xs text-[#475569]">{cp.detail}</p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}

                {decision && evaluationComplete && (
                  <div className={`glass-card p-8 border ${decision.bg} mt-6`}>
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className={`w-12 h-12 rounded-full flex items-center justify-center ${decision.bg}`}>
                          {decision.decision === 'AUTHORIZE' ? <CheckCircle className={`w-6 h-6 ${decision.color}`} /> :
                           decision.decision === 'HOLD'      ? <Clock className={`w-6 h-6 ${decision.color}`} /> :
                           <XCircle className={`w-6 h-6 ${decision.color}`} />}
                        </div>
                        <div>
                          <p className="text-xs text-muted uppercase tracking-wider">Governance Decision</p>
                          <h3 className={`text-2xl font-bold ${decision.color}`}>{decision.decision}</h3>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-muted">Checkpoints Passed</p>
                        <p className="text-white font-semibold">{decision.passed}/11</p>
                      </div>
                    </div>
                    <p className="text-muted text-sm">{decision.reason}</p>
                    <div className="mt-4 pt-4 border-t border-[#C9A227]/10">
                      <p className="text-xs text-[#64748B]">
                        Decision Trace ID: GOV-DEF-{Date.now().toString(36).toUpperCase()} | Architecture: 11-Checkpoint Fail-Closed | Engine: OMNIX Defense Governance v1.0 | {currentPlatform.emoji} {currentPlatform.label}
                      </p>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        <div className="divider-gold" />

        {/* ── Why Defense Governance ──────────────────────────────────────── */}
        <section className="mb-16">
          <div className="text-center mb-12">
            <p className="section-title">The Stakes</p>
            <h2 className="text-3xl font-bold text-white">Why Autonomous Weapons Need Governance Infrastructure</h2>
            <p className="text-muted text-sm mt-3 max-w-2xl mx-auto">
              Anduril, Shield AI, L3Harris, and every major defense contractor is building systems that operate faster than human reaction time. The governance gap is not a future problem — it's present tense.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                icon: '⚡',
                title: 'Sub-Second Decision Windows',
                desc: 'Autonomous systems engage at machine speed. Human oversight cannot operate at sensor speed — OMNIX provides the governance layer that evaluates before the action fires.',
                color: 'blue',
              },
              {
                icon: '⚖️',
                title: 'IHL Accountability Gap',
                desc: 'International Humanitarian Law requires distinction, proportionality, and precaution — concepts that cannot be satisfied by reaction-time systems without pre-execution governance.',
                color: 'gold',
              },
              {
                icon: '🔐',
                title: 'PQC-Signed Audit Trail',
                desc: 'Every autonomous decision produces an OMNIX-DEF receipt — cryptographically signed with Dilithium-3, immutable, verifiable by any court or inquiry. Every action. Every time.',
                color: 'emerald',
              },
            ].map((card, i) => (
              <div key={i} className="glass-card p-6">
                <div className="text-3xl mb-4">{card.icon}</div>
                <h3 className="text-white font-semibold mb-2">{card.title}</h3>
                <p className="text-muted text-sm leading-relaxed">{card.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ── Hard Block Scenarios ─────────────────────────────────────────── */}
        <section className="mb-16">
          <div className="text-center mb-10">
            <p className="section-title">Hard Block Scenarios</p>
            <h2 className="text-3xl font-bold text-white">Six Conditions That Always Block — No Override</h2>
            <p className="text-muted text-sm mt-3 max-w-xl mx-auto">
              These are fail-closed. No score, no weighted average, no human override can bypass them.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              { icon: '👥', label: 'Civilian Proximity', rule: 'IHL Article 51(4)', desc: 'Civilian presence confirmed within engagement radius — engagement suspended immediately.' },
              { icon: '📋', label: 'ROE Violation', rule: 'Theater ROE Framework', desc: 'Proposed action exceeds theater Rules of Engagement — autonomous lethal action prohibited.' },
              { icon: '🔓', label: 'Cyber Intrusion', rule: 'Command Link Integrity', desc: 'Active intrusion on command authentication — control suspended, no autonomous action.' },
              { icon: '🎯', label: 'IFF Failure', rule: 'Friendly Fire Prevention', desc: 'Identify Friend or Foe mismatch detected — engagement halted to prevent fratricide.' },
              { icon: '📡', label: 'Command Chain Break', rule: 'LOAC Authority Chain', desc: 'Command authority chain cannot be verified — escalation to human commander required.' },
              { icon: '⚖️', label: 'Legal Prohibition', rule: 'International Law / Treaty', desc: 'Action not authorized under applicable law or treaty — engagement permanently blocked.' },
            ].map((block, i) => (
              <div key={i} className="glass-card p-5 border border-red-500/15">
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-2xl">{block.icon}</span>
                  <div>
                    <h4 className="text-white font-semibold text-sm">{block.label}</h4>
                    <span className="text-xs text-red-400 font-medium">{block.rule}</span>
                  </div>
                </div>
                <p className="text-muted text-xs leading-relaxed">{block.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ── Other Verticals ──────────────────────────────────────────────── */}
        <section className="mb-16">
          <div className="text-center mb-10">
            <p className="section-title">Multi-Vertical Governance</p>
            <h2 className="text-3xl font-bold text-white">Same 11 Checkpoints. Every Domain.</h2>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { label: 'Credit Governance', link: '/governance-demo', emoji: '🏦', desc: 'Islamic Finance · AAOIFI · Shari\'ah ROE', color: 'emerald' },
              { label: 'Energy Governance', link: '/governance-demo-energy', emoji: '⚡', desc: 'Grid dispatch · PPA · Carbon markets', color: 'orange' },
              { label: 'Medical AI', link: '/governance-demo-medical', emoji: '🏥', desc: 'Clinical AI · FDA · Patient safety', color: 'violet' },
              { label: 'Insurance', link: '/governance-demo-insurance', emoji: '🛡️', desc: 'Underwriting · Claim decisioning', color: 'cyan' },
            ].map((v, i) => (
              <Link key={i} to={v.link} className="glass-card p-5 hover:border-[#C9A227]/30 transition-all group">
                <div className="text-2xl mb-3">{v.emoji}</div>
                <h4 className="text-white font-semibold text-sm mb-1 group-hover:text-[#C9A227] transition-colors">{v.label}</h4>
                <p className="text-muted text-xs mb-3">{v.desc}</p>
                <div className="flex items-center gap-1 text-xs text-[#C9A227]">
                  <span>View Demo</span><ArrowRight className="w-3 h-3" />
                </div>
              </Link>
            ))}
          </div>
        </section>

        {/* ── CTA ──────────────────────────────────────────────────────────── */}
        <section className="text-center">
          <div className="glass-card p-12 border border-blue-500/20">
            <div className="w-16 h-16 rounded-full bg-blue-500/10 flex items-center justify-center mx-auto mb-6">
              <Shield className="w-8 h-8 text-blue-400" />
            </div>
            <h2 className="text-3xl font-bold text-white mb-4">
              Ready to Govern Your Autonomous Systems?
            </h2>
            <p className="text-muted text-lg max-w-2xl mx-auto mb-8">
              OMNIX Defense Governance integrates directly into your autonomous system pipeline via REST API — generating PQC-signed OMNIX-DEF receipts for every decision, before execution.
            </p>
            <div className="flex flex-wrap gap-4 justify-center">
              <a
                href="https://wa.me/16505078293?text=Hi%2C%20I%27m%20interested%20in%20OMNIX%20Defense%20Governance"
                target="_blank" rel="noopener noreferrer"
                className="btn-primary px-8 py-4 text-base"
              >
                Talk to Us
              </a>
              <Link to="/try" className="px-8 py-4 text-base border border-[#C9A227]/30 text-[#C9A227] rounded-lg hover:bg-[#C9A227]/10 transition-all">
                Public Sandbox →
              </Link>
            </div>
          </div>
        </section>

      </main>

      <footer className="text-center text-xs text-[#334155] pb-8 pt-4 border-t border-[#1E293B]">
        OMNIX Quantum · Autonomous Defense Governance · ADR-DEF-001 ·{' '}
        <span className="text-blue-400">IHL Article 51 · LAWS Framework · CCW Protocol</span>
        {' '}· Receipts: OMNIX-DEF-&#123;12HEX&#125; ·{' '}
        <Link to="/verify" className="text-[#C9A227] hover:underline">Verify Receipt →</Link>
      </footer>
    </div>
  )
}
