import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield, CheckCircle, XCircle, AlertTriangle, Activity,
  Clock, Target, Eye, Radio, Lock, Scale, Users, Layers,
  Brain, Zap, ArrowRight,
} from 'lucide-react'

// ── Brand colors ──────────────────────────────────────────────────────────────
const DEF_BLUE   = '#0EA5E9'
const DEF_LIGHT  = '#38BDF8'
const DEF_DARK   = '#0A0F1C'
const DEF_BORDER = '#0EA5E933'

// ── Domain data ───────────────────────────────────────────────────────────────
const DECISION_TYPES = [
  { value: 'mission_authorization',      label: 'Mission Authorization',         emoji: '🎯', lethal: true },
  { value: 'target_validation',          label: 'AI Target ID Validation',       emoji: '🔍', lethal: true },
  { value: 'autonomous_action_approval', label: 'Autonomous Action Approval',    emoji: '⚡', lethal: true },
  { value: 'rules_of_engagement_check',  label: 'ROE Compliance Verification',   emoji: '📋', lethal: false },
  { value: 'escalation_review',          label: 'Escalation to Command',         emoji: '🔺', lethal: false },
]

const PLATFORM_TYPES = [
  { value: 'Autonomous_UAS',         label: 'Autonomous UAS (Fixed-Wing Drone)', emoji: '✈️',  riskFactor: 1.15 },
  { value: 'Ground_Robot_UGV',       label: 'Ground Robot (UGV)',                emoji: '🤖',  riskFactor: 1.10 },
  { value: 'Maritime_USV',           label: 'Maritime USV (Unmanned Surface)',   emoji: '🚢',  riskFactor: 1.08 },
  { value: 'Directed_Energy_System', label: 'Directed Energy System (DEW)',      emoji: '⚡',  riskFactor: 1.20 },
  { value: 'ISR_Surveillance',       label: 'ISR / Surveillance Platform',       emoji: '👁️',  riskFactor: 1.00 },
  { value: 'Counter_UAS',            label: 'Counter-UAS (EW / Kinetic)',        emoji: '🛡️',  riskFactor: 1.12 },
]

const THEATERS = [
  { value: 'Contested_Airspace',      label: 'Contested Airspace',               emoji: '🌐',  strictness: 1.18 },
  { value: 'Urban_COIN',              label: 'Urban COIN (MOUT)',                 emoji: '🏙️',  strictness: 1.22 },
  { value: 'Maritime_Patrol',         label: 'Maritime Patrol (High Seas)',       emoji: '⚓',  strictness: 1.10 },
  { value: 'Border_Security',         label: 'Border Security',                  emoji: '🚧',  strictness: 1.08 },
  { value: 'Critical_Infrastructure', label: 'Critical Infrastructure Defense',  emoji: '🏭',  strictness: 1.15 },
  { value: 'Cyber_Physical',          label: 'Cyber-Physical Domain',            emoji: '💻',  strictness: 1.12 },
]

const ROE_TYPES = [
  { value: 'weapons_hold',    label: 'Weapons Hold (fire only if fired upon)',   factor: 0.92, emoji: '🟢' },
  { value: 'weapons_tight',   label: 'Weapons Tight (positive ID required)',     factor: 0.78, emoji: '🟡' },
  { value: 'weapons_free',    label: 'Weapons Free (engage all identified threats)', factor: 0.55, emoji: '🔴' },
  { value: 'non_lethal_only', label: 'Non-Lethal Measures Only',                factor: 0.90, emoji: '🟢' },
]

const COLLATERAL_LEVELS = [
  { value: 'minimal', label: 'Minimal — zero civilian presence',       factor: 0.97, ihlRisk: false },
  { value: 'low',     label: 'Low — remote area, <5 civilians',        factor: 0.80, ihlRisk: false },
  { value: 'moderate',label: 'Moderate — mixed environment',           factor: 0.52, ihlRisk: false },
  { value: 'high',    label: 'High Risk — urban, civilian proximity',  factor: 0.15, ihlRisk: true  },
]

const COMMS_STATUS = [
  { value: 'secure',   label: 'Secure Link — encrypted, auth verified', factor: 0.96 },
  { value: 'degraded', label: 'Degraded — partial encryption',           factor: 0.64 },
  { value: 'emcon',    label: 'EMCON — emissions control (silent)',      factor: 0.44 },
  { value: 'denied',   label: 'Comms Denied — jammed / spoofed',        factor: 0.10 },
]

const HUMAN_OVERRIDE = [
  { value: 'available',   label: 'Commander Available — <5s response', factor: 0.96 },
  { value: 'delayed',     label: 'Delayed — 15-60s loop latency',      factor: 0.65 },
  { value: 'limited',     label: 'Limited — bandwidth constrained',    factor: 0.44 },
  { value: 'unavailable', label: 'Unavailable — full autonomy mode',   factor: 0.18 },
]

// ── Scenario presets ──────────────────────────────────────────────────────────
const PRESETS = [
  {
    label: 'Urban COIN — Standard',
    emoji: '🏙️',
    s: { decisionType: 'rules_of_engagement_check', platformType: 'Autonomous_UAS', theater: 'Urban_COIN',
         targetConfidence: 74, iffConfidence: 68, roeType: 'weapons_tight', collateralLevel: 'low',
         commsStatus: 'secure', humanOverride: 'available' },
  },
  {
    label: 'ISR — Contested Airspace',
    emoji: '✈️',
    s: { decisionType: 'mission_authorization', platformType: 'ISR_Surveillance', theater: 'Contested_Airspace',
         targetConfidence: 82, iffConfidence: 79, roeType: 'weapons_hold', collateralLevel: 'minimal',
         commsStatus: 'degraded', humanOverride: 'delayed' },
  },
  {
    label: 'Counter-UAS Intercept',
    emoji: '🛡️',
    s: { decisionType: 'autonomous_action_approval', platformType: 'Counter_UAS', theater: 'Border_Security',
         targetConfidence: 88, iffConfidence: 84, roeType: 'weapons_tight', collateralLevel: 'low',
         commsStatus: 'secure', humanOverride: 'available' },
  },
  {
    label: 'High Collateral — Block Test',
    emoji: '⚠️',
    s: { decisionType: 'target_validation', platformType: 'Directed_Energy_System', theater: 'Urban_COIN',
         targetConfidence: 61, iffConfidence: 44, roeType: 'weapons_free', collateralLevel: 'high',
         commsStatus: 'denied', humanOverride: 'unavailable' },
  },
  {
    label: 'Maritime Patrol — Routine',
    emoji: '⚓',
    s: { decisionType: 'mission_authorization', platformType: 'Maritime_USV', theater: 'Maritime_Patrol',
         targetConfidence: 79, iffConfidence: 77, roeType: 'weapons_hold', collateralLevel: 'minimal',
         commsStatus: 'secure', humanOverride: 'available' },
  },
]

// ── Types ────────────────────────────────────────────────────────────────────
interface Scenario {
  decisionType:    string
  platformType:    string
  theater:         string
  targetConfidence: number
  iffConfidence:    number
  roeType:         string
  collateralLevel: string
  commsStatus:     string
  humanOverride:   string
}

interface CheckpointResult {
  name:        string
  generic:     string
  icon:        React.ReactNode
  status:      'pending' | 'evaluating' | 'pass' | 'warn' | 'block'
  score:       number
  threshold:   number
  reasoning:   string
  detail:      string
}

// ── Score bar ─────────────────────────────────────────────────────────────────
function ScoreBar({ score, threshold, color }: { score: number; threshold: number; color: string }) {
  return (
    <div style={{ position: 'relative', height: 6, background: '#0F1E35', borderRadius: 3, overflow: 'visible' }}>
      <div style={{ position: 'absolute', left: `${threshold}%`, top: -3, width: 2, height: 12,
        background: '#F59E0B', borderRadius: 1, zIndex: 2 }} />
      <div style={{ height: '100%', width: `${Math.min(score, 100)}%`,
        background: color, borderRadius: 3, transition: 'width 0.9s ease' }} />
    </div>
  )
}

// ── Checkpoint builder ────────────────────────────────────────────────────────
function buildCheckpoints(s: Scenario): CheckpointResult[] {
  const dt      = DECISION_TYPES.find(d => d.value === s.decisionType) || DECISION_TYPES[0]
  const plat    = PLATFORM_TYPES.find(p => p.value === s.platformType) || PLATFORM_TYPES[0]
  const theater = THEATERS.find(t => t.value === s.theater) || THEATERS[0]
  const roe     = ROE_TYPES.find(r => r.value === s.roeType) || ROE_TYPES[0]
  const coll    = COLLATERAL_LEVELS.find(c => c.value === s.collateralLevel) || COLLATERAL_LEVELS[0]
  const comms   = COMMS_STATUS.find(c => c.value === s.commsStatus) || COMMS_STATUS[0]
  const human   = HUMAN_OVERRIDE.find(h => h.value === s.humanOverride) || HUMAN_OVERRIDE[0]

  const tc = s.targetConfidence / 100
  const ic = s.iffConfidence / 100
  const rf = plat.riskFactor * theater.strictness

  const sivScore        = Math.round(Math.min(95, (tc * 35 + roe.factor * 28 + comms.factor * 22 + coll.factor * 15) * 100 / rf))
  const discriminScore  = Math.round(Math.min(95, (tc * 48 + ic * 32 + coll.factor * 20) * 100))
  const roeScore        = Math.round(Math.min(95, roe.factor * 100 * (comms.factor >= 0.64 ? 1.0 : 0.72)))
  const collateralScore = Math.round(Math.min(95, coll.factor * 100))
  const commsScore      = Math.round(Math.min(95, comms.factor * 100))
  const necessityScore  = Math.round(Math.min(95, (tc * 33 + roe.factor * 37 + (1 - theater.strictness * 0.5 + 0.6) * 30) * 100 * 0.01))

  const sigs = [sivScore, discriminScore, roeScore, collateralScore, commsScore, necessityScore]
  const avg   = sigs.reduce((a, b) => a + b, 0) / sigs.length
  const vari  = sigs.reduce((a, b) => a + Math.pow(b - avg, 2), 0) / sigs.length
  const div   = Math.sqrt(vari)
  const contraScore  = Math.round(Math.max(0, Math.min(95, 100 - div * 2.0)))
  const temporalScore = Math.round(Math.min(95, roeScore * 0.44 + necessityScore * 0.36 + commsScore * 0.20))
  const edgeScore     = Math.round(sivScore * 0.54 + contraScore * 0.46)
  const legalScore    = Math.round(Math.min(95, roe.factor * 40 + coll.factor * 35 + human.factor * 25))
  const humanScore    = Math.round(Math.min(95, human.factor * 100))

  return [
    {
      name: 'Sensor Fusion Integrity',
      generic: 'CP-1: Are all targeting signals valid?',
      icon: <Eye size={15} />,
      status: 'pending', score: sivScore, threshold: 58,
      reasoning: sivScore >= 58
        ? `Sensor fusion integrity verified — target conf ${s.targetConfidence}%, ${roe.label.split('(')[0].trim()}, ${comms.label.split('(')[0].trim()} | Theater risk factor: ${theater.strictness}×`
        : `Fusion integrity failed — degraded sensor picture below autonomous engagement threshold at ${theater.strictness}× theater strictness`,
      detail: `TC:${s.targetConfidence}% ×0.35 + ROE:${(roe.factor*100).toFixed(0)}% ×0.28 + Comms:${(comms.factor*100).toFixed(0)}% ×0.22 + Coll:${(coll.factor*100).toFixed(0)}% ×0.15 = ${sivScore} ÷ ${rf.toFixed(2)}×`,
    },
    {
      name: 'Target Discrimination Accuracy',
      generic: 'CP-2: Positive combatant ID — IHL Article 57(2)(a)?',
      icon: <Target size={15} />,
      status: 'pending', score: discriminScore, threshold: 62,
      reasoning: discriminScore >= 62
        ? `Target discrimination at ${discriminScore}% — positive combatant ID above IHL Article 57(2)(a) precautionary threshold | IFF: ${s.iffConfidence}%`
        : `Discrimination failure — TC:${s.targetConfidence}% + IFF:${s.iffConfidence}% below IHL standard for ${theater.label} environment`,
      detail: `TC:${s.targetConfidence}% ×0.48 + IFF:${s.iffConfidence}% ×0.32 + Coll env:${(coll.factor*100).toFixed(0)}% ×0.20 = ${discriminScore}/100`,
    },
    {
      name: 'ROE Compliance Gate',
      generic: 'CP-3: Does this comply with Rules of Engagement?',
      icon: <Scale size={15} />,
      status: 'pending', score: roeScore, threshold: 52,
      reasoning: roeScore >= 52
        ? `ROE compliance verified — ${roe.label} with ${comms.label.split('(')[0].trim()} satisfies theater ROE framework`
        : `ROE non-compliant — ${roe.label} under ${comms.label.split('(')[0].trim()} fails engagement authorization standard`,
      detail: `ROE base: ${(roe.factor*100).toFixed(0)}% | Comms penalty: ${comms.factor < 0.64 ? `×0.72` : '×1.00'} | ROE score: ${roeScore}/100`,
    },
    {
      name: 'Collateral Damage Assessment',
      generic: 'CP-4: Proportionality test — IHL Article 51(5)(b)?',
      icon: <Users size={15} />,
      status: 'pending', score: collateralScore, threshold: 42,
      reasoning: collateralScore >= 42
        ? `Proportionality test passed — ${coll.label.split('—')[1].trim()} environment clears IHL Article 51(5)(b) incidental civilian harm threshold`
        : `IHL PROPORTIONALITY FAILURE — ${coll.label.split('—')[1].trim()} creates excessive incidental civilian harm under IHL Article 51(5)(b)`,
      detail: `Collateral env: ${coll.label.split('—')[0].trim()} | IHL factor: ${(coll.factor*100).toFixed(0)}% | IHL test: ${collateralScore >= 42 ? 'PASS' : 'FAIL'} | Score: ${collateralScore}/100`,
    },
    {
      name: 'Command Link Integrity',
      generic: 'CP-5: Secure authenticated command link verified?',
      icon: <Radio size={15} />,
      status: 'pending', score: commsScore, threshold: 38,
      reasoning: commsScore >= 38
        ? `Command link authenticated — ${comms.label} confirms valid control chain over ${plat.label}`
        : `Authentication gap — ${comms.label.split('(')[0].trim()} creates unacceptable control gap for autonomous ${dt.lethal ? 'lethal' : 'non-lethal'} system`,
      detail: `Link: ${comms.label.split('—')[0].trim()} | Auth factor: ${(comms.factor*100).toFixed(0)}% | Auth verified: ${commsScore >= 38 ? 'YES' : 'NO'} | Score: ${commsScore}/100`,
    },
    {
      name: 'Mission Necessity & Proportionality',
      generic: 'CP-6: IHL Article 57(2)(b) necessity test?',
      icon: <Shield size={15} />,
      status: 'pending', score: necessityScore, threshold: 40,
      reasoning: necessityScore >= 40
        ? `Military necessity confirmed — TC:${s.targetConfidence}%, ${roe.label.split('(')[0].trim()}, and theater conditions satisfy IHL precautionary principles`
        : `Necessity test failed — insufficient targeting confidence + ROE combination for IHL compliance in ${theater.label}`,
      detail: `TC×0.33: ${(tc*33).toFixed(0)} + ROE×0.37: ${(roe.factor*37).toFixed(0)} + Theater×0.30 = ${necessityScore}/100`,
    },
    {
      name: 'Multi-Sensor Signal Contradiction',
      generic: 'CP-7: Do all sensor channels agree on target?',
      icon: <Brain size={15} />,
      status: 'pending', score: contraScore, threshold: 40,
      reasoning: contraScore >= 40
        ? `Multi-sensor agreement confirmed — internal signal divergence ${div.toFixed(1)} across 6 governance channels is within acceptable bounds`
        : `High contradiction — signal divergence ${div.toFixed(1)} indicates conflicting sensor assessment; autonomous engagement unreliable`,
      detail: `Signal variance: ${vari.toFixed(1)} | Divergence: ${div.toFixed(1)} | Cross-sensor alignment: ${contraScore}% | ${contraScore < 40 ? 'CONTRADICTORY' : contraScore < 55 ? 'TENSIONED' : 'COHERENT'}`,
    },
    {
      name: 'Situational Temporal Coherence',
      generic: 'CP-8: Is the situational picture stable over time?',
      icon: <Activity size={15} />,
      status: 'pending', score: temporalScore, threshold: 38,
      reasoning: temporalScore >= 38
        ? `Situational stability confirmed — ROE validity, mission necessity, and comms integrity consistent across engagement window`
        : `Temporal instability — current conditions appear transient or degrading; window too narrow for confident autonomous action`,
      detail: `ROE stability×0.44: ${(roeScore*0.44).toFixed(0)} + Necessity×0.36: ${(necessityScore*0.36).toFixed(0)} + Comms×0.20: ${(commsScore*0.20).toFixed(0)} = ${temporalScore}/100`,
    },
    {
      name: 'Edge Confirmation (ECG)',
      generic: 'CP-9: Decision boundary convergence verified?',
      icon: <Layers size={15} />,
      status: 'pending', score: edgeScore, threshold: 48,
      reasoning: edgeScore >= 48
        ? `Governance boundary confirmed — sensor fusion integrity and cross-sensor alignment converge at decision edge (${edgeScore}%)`
        : `Weak boundary — SIV and contradiction signals do not reinforce; escalate to human commander`,
      detail: `SIV×0.54: ${(sivScore*0.54).toFixed(0)} + Contradiction×0.46: ${(contraScore*0.46).toFixed(0)} = ${edgeScore}/100 | Boundary: ${edgeScore >= 48 ? 'CONFIRMED' : 'WEAK'}`,
    },
    {
      name: 'Legal Authorization Gate',
      generic: 'CP-10: Command authority + legal auth verified?',
      icon: <Lock size={15} />,
      status: 'pending', score: legalScore, threshold: 56,
      reasoning: legalScore >= 56
        ? `Legal authorization confirmed — ROE framework, collateral assessment, and command chain validate authority for this ${dt.lethal ? 'lethal' : 'non-lethal'} action`
        : `Legal authorization insufficient — ROE, collateral risk, or command chain below legal threshold for autonomous ${dt.lethal ? 'lethal' : 'non-lethal'} action`,
      detail: `ROE auth:${(roe.factor*100).toFixed(0)}%×0.40 + Coll IHL:${(coll.factor*100).toFixed(0)}%×0.35 + Cmd chain:${(human.factor*100).toFixed(0)}%×0.25 = ${legalScore}/100`,
    },
    {
      name: 'Human Override Availability',
      generic: 'CP-11: Meaningful human control — LAWS framework?',
      icon: <Users size={15} />,
      status: 'pending', score: humanScore, threshold: 33,
      reasoning: humanScore >= 33
        ? `HITL confirmed — ${human.label.split('—')[0].trim()} satisfies LAWS (Lethal Autonomous Weapons Systems) meaningful human control requirement`
        : `LAWS accountability gap — ${human.label.split('—')[0].trim()} creates unacceptable human control deficit under LAWS governance framework`,
      detail: `Override: ${human.label.split('—')[0].trim()} | HITL factor: ${(human.factor*100).toFixed(0)}% | LAWS compliance: ${humanScore >= 33 ? 'SATISFIED' : 'VIOLATED'} | Score: ${humanScore}/100`,
    },
  ]
}

function buildReceiptId() {
  const hex = Array.from({ length: 12 }, () => Math.floor(Math.random() * 16).toString(16).toUpperCase()).join('')
  return `OMNIX-DEF-${hex}`
}

// ── Main component ────────────────────────────────────────────────────────────
export default function DefenseGovernanceDemo() {
  const [scenario, setScenario] = useState<Scenario>({
    decisionType:    'mission_authorization',
    platformType:    'Autonomous_UAS',
    theater:         'Contested_Airspace',
    targetConfidence: 74,
    iffConfidence:    72,
    roeType:         'weapons_tight',
    collateralLevel: 'low',
    commsStatus:     'secure',
    humanOverride:   'available',
  })
  const [checkpoints, setCheckpoints] = useState<CheckpointResult[]>([])
  const [currentCp,   setCurrentCp]   = useState(-1)
  const [finalResult, setFinalResult] = useState<string | null>(null)
  const [receiptId,   setReceiptId]   = useState<string | null>(null)
  const [isRunning,   setIsRunning]   = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const dt      = DECISION_TYPES.find(d => d.value === scenario.decisionType) || DECISION_TYPES[0]
  const plat    = PLATFORM_TYPES.find(p => p.value === scenario.platformType) || PLATFORM_TYPES[0]
  const theater = THEATERS.find(t => t.value === scenario.theater) || THEATERS[0]
  const roe     = ROE_TYPES.find(r => r.value === scenario.roeType) || ROE_TYPES[0]
  const coll    = COLLATERAL_LEVELS.find(c => c.value === scenario.collateralLevel) || COLLATERAL_LEVELS[0]
  const comms   = COMMS_STATUS.find(c => c.value === scenario.commsStatus) || COMMS_STATUS[0]
  const human   = HUMAN_OVERRIDE.find(h => h.value === scenario.humanOverride) || HUMAN_OVERRIDE[0]

  // Hard block detection (real-time, before evaluation)
  const hb_civilian  = coll.ihlRisk && dt.lethal
  const hb_comms     = scenario.commsStatus === 'denied' && dt.lethal
  const hb_iff       = scenario.iffConfidence < 35 && dt.lethal
  const hb_hitl      = scenario.humanOverride === 'unavailable' && scenario.roeType === 'weapons_free'
  const hb_target    = scenario.targetConfidence < 35 && dt.lethal
  const anyHardBlock = hb_civilian || hb_comms || hb_iff || hb_hitl || hb_target

  function applyPreset(preset: typeof PRESETS[0]) {
    setScenario(prev => ({ ...prev, ...preset.s }))
    setCheckpoints([]); setFinalResult(null); setReceiptId(null); setCurrentCp(-1)
  }

  function runEvaluation() {
    if (isRunning) return
    const cps = buildCheckpoints(scenario)
    setCheckpoints(cps.map(c => ({ ...c, status: 'pending' })))
    setCurrentCp(-1); setFinalResult(null); setReceiptId(null); setIsRunning(true)

    cps.forEach((_, i) => {
      if (timerRef.current) clearTimeout(timerRef.current)
      timerRef.current = setTimeout(() => {
        setCurrentCp(i)
        setCheckpoints(prev => prev.map((c, idx) =>
          idx < i
            ? { ...c, status: (c.score >= c.threshold ? 'pass' : c.score >= c.threshold * 0.72 ? 'warn' : 'block') as CheckpointResult['status'] }
            : idx === i ? { ...c, status: 'evaluating' as CheckpointResult['status'] }
            : c
        ))
        if (i === cps.length - 1) {
          setTimeout(() => {
            const finalCps: CheckpointResult[] = cps.map(c => ({
              ...c, status: (c.score >= c.threshold ? 'pass' : c.score >= c.threshold * 0.72 ? 'warn' : 'block') as CheckpointResult['status']
            }))
            const hardBlocks = finalCps.filter(c => c.score < c.threshold * 0.5).length
            const blocks     = finalCps.filter(c => c.score < c.threshold).length
            let verdict: string
            if (anyHardBlock || hardBlocks > 0) verdict = 'HARD_BLOCK'
            else if (blocks >= 3)               verdict = 'BLOCKED'
            else if (blocks > 0)               verdict = 'HOLD'
            else                               verdict = 'AUTHORIZED'
            setCheckpoints(finalCps); setCurrentCp(-1); setFinalResult(verdict)
            if (verdict === 'AUTHORIZED') setReceiptId(buildReceiptId())
            setIsRunning(false)
          }, 380)
        }
      }, i * 300)
    })
  }

  useEffect(() => () => { if (timerRef.current) clearTimeout(timerRef.current) }, [])

  const statusIcon = (s: CheckpointResult['status']) => {
    if (s === 'pending')    return <Clock    size={15} style={{ color: '#334155' }} />
    if (s === 'evaluating') return <Activity size={15} style={{ color: DEF_BLUE,  animation: 'pulse 0.8s ease-in-out infinite' }} />
    if (s === 'pass')       return <CheckCircle size={15} style={{ color: '#10B981' }} />
    if (s === 'warn')       return <AlertTriangle size={15} style={{ color: '#F59E0B' }} />
    return <XCircle size={15} style={{ color: '#EF4444' }} />
  }
  const statusColor = (s: CheckpointResult['status']) => {
    if (s === 'pass')       return '#10B981'
    if (s === 'warn')       return '#F59E0B'
    if (s === 'block')      return '#EF4444'
    if (s === 'evaluating') return DEF_BLUE
    return '#334155'
  }
  const verdictColor = (v: string | null) => {
    if (v === 'AUTHORIZED')  return '#10B981'
    if (v === 'HOLD')        return '#F59E0B'
    return '#EF4444'
  }
  const verdictBg = (v: string | null) => {
    if (v === 'AUTHORIZED')  return 'rgba(16,185,129,0.10)'
    if (v === 'HOLD')        return 'rgba(245,158,11,0.10)'
    return 'rgba(239,68,68,0.10)'
  }
  const verdictBorder = (v: string | null) => {
    if (v === 'AUTHORIZED')  return '#10B98133'
    if (v === 'HOLD')        return '#F59E0B33'
    return '#EF444433'
  }

  const inputStyle: React.CSSProperties = {
    background: '#06111E', border: '1px solid #1E3A5F', borderRadius: 7,
    color: '#CBD5E1', padding: '9px 12px', fontSize: 13, width: '100%',
    outline: 'none', cursor: 'pointer',
  }
  const labelStyle: React.CSSProperties = {
    fontSize: 10, color: '#64748B', marginBottom: 5, display: 'block',
    fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em',
  }
  const sliderStyle: React.CSSProperties = { width: '100%', accentColor: DEF_BLUE, cursor: 'pointer', height: 4 }

  return (
    <div style={{
      minHeight: '100vh',
      background: `linear-gradient(160deg, ${DEF_DARK} 0%, #0A1525 50%, #080E1C 100%)`,
      color: '#E2E8F0', fontFamily: "'Inter', sans-serif", padding: '24px',
    }}>
      <style>{`
        @keyframes pulse { 0%,100%{opacity:1}50%{opacity:0.25} }
        @keyframes spin  { from{transform:rotate(0deg)}to{transform:rotate(360deg)} }
        * { box-sizing:border-box }
        select option { background: #06111E }
        input[type=range]::-webkit-slider-thumb { background: ${DEF_BLUE} }
      `}</style>

      <div style={{ maxWidth: 1320, margin: '0 auto' }}>

        {/* ── Header ─────────────────────────────────────────────────────────── */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
            <Link to="/" style={{ color: '#475569', fontSize: 12, textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 4 }}>
              ← Home
            </Link>
            <span style={{ color: '#334155', fontSize: 12 }}>/</span>
            <span style={{ color: '#64748B', fontSize: 12 }}>Autonomous Defense Governance</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
              <div style={{
                width: 50, height: 50, borderRadius: 12, display: 'flex', alignItems: 'center',
                justifyContent: 'center', fontSize: 24,
                background: `${DEF_BLUE}18`, border: `1px solid ${DEF_BLUE}44`,
              }}>🛡️</div>
              <div>
                <div style={{ fontSize: 22, fontWeight: 800, letterSpacing: '-0.02em', color: '#F1F5F9' }}>
                  Autonomous Defense Governance — Interactive Demo
                </div>
                <div style={{ fontSize: 12, color: '#475569', marginTop: 3 }}>
                  ADR-DEF-001 · 11-Checkpoint Fail-Closed Pipeline · IHL + LAWS Framework ·
                  {' '}<span style={{ color: DEF_LIGHT, fontFamily: 'monospace' }}>OMNIX-DEF-{'{12HEX}'}</span>
                  {' '}PQC Receipts
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 6 }}>
              {['IHL Article 51', 'ROE Compliant', 'LAWS Framework', 'CCW Protocol'].map(b => (
                <span key={b} style={{
                  padding: '4px 10px', fontSize: 10, fontWeight: 700, borderRadius: 5,
                  background: `${DEF_BLUE}14`, border: `1px solid ${DEF_BLUE}33`, color: DEF_LIGHT,
                  textTransform: 'uppercase', letterSpacing: '0.04em',
                }}>{b}</span>
              ))}
            </div>
          </div>
        </div>

        {/* ── Scenario Presets ────────────────────────────────────────────────── */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 10, color: '#475569', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', alignSelf: 'center', marginRight: 4 }}>
            Quick Load
          </span>
          {PRESETS.map(p => (
            <button key={p.label} onClick={() => applyPreset(p)} style={{
              padding: '6px 14px', fontSize: 12, borderRadius: 7, cursor: 'pointer',
              background: `${DEF_BLUE}10`, border: `1px solid ${DEF_BLUE}28`,
              color: '#94A3B8', fontWeight: 600, transition: 'all 0.15s',
              display: 'flex', alignItems: 'center', gap: 5,
            }}
              onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = DEF_BLUE; (e.currentTarget as HTMLElement).style.color = DEF_LIGHT }}
              onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = `${DEF_BLUE}28`; (e.currentTarget as HTMLElement).style.color = '#94A3B8' }}
            >{p.emoji} {p.label}</button>
          ))}
        </div>

        {/* ── Main Two-Column Layout ──────────────────────────────────────────── */}
        <div style={{ display: 'grid', gridTemplateColumns: '390px 1fr', gap: 18, alignItems: 'start' }}>

          {/* ── LEFT: Config Panel ──────────────────────────────────────────── */}
          <div>
            <div style={{
              background: 'rgba(10,20,36,0.95)', borderRadius: 14, padding: 22,
              border: `1px solid ${DEF_BORDER}`, marginBottom: 14,
            }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: DEF_LIGHT, marginBottom: 18, display: 'flex', alignItems: 'center', gap: 7 }}>
                <Shield size={14} color={DEF_BLUE} />
                Engagement Scenario Configuration
              </div>

              {/* Decision Type */}
              <div style={{ marginBottom: 13 }}>
                <label style={labelStyle}>Decision Type</label>
                <select style={inputStyle} value={scenario.decisionType}
                  onChange={e => { setScenario(p => ({ ...p, decisionType: e.target.value })); setCheckpoints([]); setFinalResult(null) }}>
                  {DECISION_TYPES.map(d => <option key={d.value} value={d.value}>{d.emoji} {d.label} {d.lethal ? '· LETHAL' : ''}</option>)}
                </select>
                <div style={{ fontSize: 10, color: dt.lethal ? '#EF4444' : '#10B981', marginTop: 4, fontWeight: 600 }}>
                  {dt.lethal ? '⚠ Lethal action — full 11-checkpoint evaluation required' : '✓ Non-lethal — standard governance pipeline'}
                </div>
              </div>

              {/* Platform */}
              <div style={{ marginBottom: 13 }}>
                <label style={labelStyle}>Platform Type</label>
                <select style={inputStyle} value={scenario.platformType}
                  onChange={e => { setScenario(p => ({ ...p, platformType: e.target.value })); setCheckpoints([]); setFinalResult(null) }}>
                  {PLATFORM_TYPES.map(p => <option key={p.value} value={p.value}>{p.emoji} {p.label}</option>)}
                </select>
                <div style={{ fontSize: 10, color: '#64748B', marginTop: 4 }}>
                  Risk factor: {plat.riskFactor}× · Theater strictness: {theater.strictness}×
                </div>
              </div>

              {/* Operational Theater */}
              <div style={{ marginBottom: 18 }}>
                <label style={labelStyle}>Operational Theater</label>
                <select style={inputStyle} value={scenario.theater}
                  onChange={e => { setScenario(p => ({ ...p, theater: e.target.value })); setCheckpoints([]); setFinalResult(null) }}>
                  {THEATERS.map(t => <option key={t.value} value={t.value}>{t.emoji} {t.label}</option>)}
                </select>
              </div>

              {/* Target Confidence */}
              <div style={{ marginBottom: 13 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                  <label style={{ ...labelStyle, marginBottom: 0 }}>Target Confidence</label>
                  <span style={{ fontSize: 13, fontWeight: 700, color: hb_target ? '#EF4444' : scenario.targetConfidence < 55 ? '#F59E0B' : '#10B981' }}>
                    {scenario.targetConfidence}%{hb_target && ' ⚠ HARD BLOCK'}
                  </span>
                </div>
                <input type="range" min={10} max={99} step={1} style={sliderStyle}
                  value={scenario.targetConfidence}
                  onChange={e => { setScenario(p => ({ ...p, targetConfidence: parseInt(e.target.value) })); setCheckpoints([]); setFinalResult(null) }} />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#334155', marginTop: 2 }}>
                  <span style={{ color: '#EF4444' }}>10% Uncertain</span>
                  <span style={{ color: '#F59E0B' }}>55% Marginal</span>
                  <span style={{ color: '#10B981' }}>85%+ Positive ID</span>
                </div>
              </div>

              {/* IFF Confidence */}
              <div style={{ marginBottom: 13 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                  <label style={{ ...labelStyle, marginBottom: 0 }}>IFF Confidence (Identify Friend or Foe)</label>
                  <span style={{ fontSize: 13, fontWeight: 700, color: hb_iff ? '#EF4444' : scenario.iffConfidence < 50 ? '#F59E0B' : '#10B981' }}>
                    {scenario.iffConfidence}%{hb_iff && ' ⚠ HARD BLOCK'}
                  </span>
                </div>
                <input type="range" min={10} max={99} step={1} style={sliderStyle}
                  value={scenario.iffConfidence}
                  onChange={e => { setScenario(p => ({ ...p, iffConfidence: parseInt(e.target.value) })); setCheckpoints([]); setFinalResult(null) }} />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#334155', marginTop: 2 }}>
                  <span style={{ color: '#EF4444' }}>&lt;35% Fratricide Risk</span><span style={{ color: '#10B981' }}>80%+ Confirmed</span>
                </div>
              </div>

              {/* ROE */}
              <div style={{ marginBottom: 13 }}>
                <label style={labelStyle}>Rules of Engagement Classification</label>
                <select style={inputStyle} value={scenario.roeType}
                  onChange={e => { setScenario(p => ({ ...p, roeType: e.target.value })); setCheckpoints([]); setFinalResult(null) }}>
                  {ROE_TYPES.map(r => <option key={r.value} value={r.value}>{r.emoji} {r.label}</option>)}
                </select>
              </div>

              {/* Collateral */}
              <div style={{ marginBottom: 13 }}>
                <label style={labelStyle}>Collateral Damage Estimate</label>
                <select style={inputStyle} value={scenario.collateralLevel}
                  onChange={e => { setScenario(p => ({ ...p, collateralLevel: e.target.value })); setCheckpoints([]); setFinalResult(null) }}>
                  {COLLATERAL_LEVELS.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                </select>
                {hb_civilian && (
                  <div style={{ fontSize: 10, color: '#EF4444', marginTop: 4, fontWeight: 700 }}>
                    ⚠ HARD BLOCK — IHL Article 51(4) civilian proximity + lethal action
                  </div>
                )}
              </div>

              {/* Comms */}
              <div style={{ marginBottom: 13 }}>
                <label style={labelStyle}>Communications Status</label>
                <select style={inputStyle} value={scenario.commsStatus}
                  onChange={e => { setScenario(p => ({ ...p, commsStatus: e.target.value })); setCheckpoints([]); setFinalResult(null) }}>
                  {COMMS_STATUS.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                </select>
                {hb_comms && (
                  <div style={{ fontSize: 10, color: '#EF4444', marginTop: 4, fontWeight: 700 }}>
                    ⚠ HARD BLOCK — comms denied, no command auth for lethal action
                  </div>
                )}
              </div>

              {/* Human Override */}
              <div style={{ marginBottom: 20 }}>
                <label style={labelStyle}>Human Override Availability (LAWS)</label>
                <select style={inputStyle} value={scenario.humanOverride}
                  onChange={e => { setScenario(p => ({ ...p, humanOverride: e.target.value })); setCheckpoints([]); setFinalResult(null) }}>
                  {HUMAN_OVERRIDE.map(h => <option key={h.value} value={h.value}>{h.label}</option>)}
                </select>
                {hb_hitl && (
                  <div style={{ fontSize: 10, color: '#EF4444', marginTop: 4, fontWeight: 700 }}>
                    ⚠ HARD BLOCK — no HITL + Weapons Free = LAWS accountability gap
                  </div>
                )}
              </div>

              {/* Active hard block summary */}
              {anyHardBlock && (
                <div style={{
                  background: 'rgba(239,68,68,0.08)', border: '1px solid #EF444430',
                  borderRadius: 8, padding: '10px 14px', marginBottom: 16,
                }}>
                  <div style={{ color: '#EF4444', fontWeight: 700, fontSize: 11, marginBottom: 6 }}>⚠ Hard Block Conditions Active — Will BLOCK before evaluation</div>
                  {hb_civilian && <div style={{ color: '#FCA5A5', fontSize: 11, marginBottom: 3 }}>• IHL Article 51(4) — civilian proximity + lethal action</div>}
                  {hb_comms   && <div style={{ color: '#FCA5A5', fontSize: 11, marginBottom: 3 }}>• Command auth failure — comms denied, lethal action prohibited</div>}
                  {hb_iff     && <div style={{ color: '#FCA5A5', fontSize: 11, marginBottom: 3 }}>• IFF &lt;35% — fratricide risk, engagement suspended</div>}
                  {hb_hitl    && <div style={{ color: '#FCA5A5', fontSize: 11, marginBottom: 3 }}>• LAWS accountability gap — Weapons Free + no HITL</div>}
                  {hb_target  && <div style={{ color: '#FCA5A5', fontSize: 11 }}>• Target ID &lt;35% — discrimination failure for lethal action</div>}
                </div>
              )}

              <button onClick={runEvaluation} disabled={isRunning} style={{
                width: '100%', padding: '13px 20px', borderRadius: 10, border: 'none',
                background: isRunning ? '#1E293B' : `linear-gradient(135deg, #1D4ED8, ${DEF_BLUE})`,
                color: isRunning ? '#475569' : '#FFF', fontWeight: 700, fontSize: 14,
                cursor: isRunning ? 'not-allowed' : 'pointer', transition: 'all 0.2s',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              }}>
                <Shield size={15} />
                {isRunning ? 'Evaluating Autonomous Engagement…' : 'Run 11-Checkpoint Defense Governance'}
                {!isRunning && <ArrowRight size={15} />}
              </button>
            </div>

            {/* Scenario Summary */}
            <div style={{
              background: 'rgba(10,20,36,0.95)', borderRadius: 12, padding: 16,
              border: '1px solid #1E3A5F', fontSize: 12,
            }}>
              <div style={{ color: '#475569', fontWeight: 700, marginBottom: 10, fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                Current Scenario
              </div>
              {[
                ['Decision',   `${dt.emoji} ${dt.label}`],
                ['Platform',   `${plat.emoji} ${plat.label.split('(')[0].trim()}`],
                ['Theater',    `${theater.emoji} ${theater.label}`],
                ['Target Conf',`${scenario.targetConfidence}%`],
                ['IFF',        `${scenario.iffConfidence}%`],
                ['ROE',        `${roe.emoji} ${roe.label.split('(')[0].trim()}`],
                ['Collateral', coll.label.split('—')[0].trim()],
                ['Comms',      comms.label.split('—')[0].trim()],
                ['HITL',       human.label.split('—')[0].trim()],
              ].map(([k, v]) => (
                <div key={k as string} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5, paddingBottom: 5, borderBottom: '1px solid #0A1625' }}>
                  <span style={{ color: '#334155' }}>{k}</span>
                  <span style={{ color: '#94A3B8', fontWeight: 600, maxWidth: 200, textAlign: 'right' }}>{v}</span>
                </div>
              ))}
              <div style={{ marginTop: 8, paddingTop: 8, borderTop: '1px solid #0A1625' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#334155', fontSize: 10 }}>Combined Risk Factor</span>
                  <span style={{ color: plat.riskFactor * theater.strictness > 1.30 ? '#EF4444' : '#F59E0B', fontWeight: 700, fontFamily: 'monospace', fontSize: 11 }}>
                    {(plat.riskFactor * theater.strictness).toFixed(2)}×
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* ── RIGHT: Checkpoint Results ───────────────────────────────────── */}
          <div>
            {checkpoints.length === 0 ? (
              <div style={{
                background: 'rgba(10,20,36,0.95)', borderRadius: 14, padding: 52,
                border: `1px solid ${DEF_BORDER}`, textAlign: 'center',
              }}>
                <div style={{ fontSize: 52, marginBottom: 18 }}>🛡️</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: DEF_LIGHT, marginBottom: 10 }}>
                  Autonomous Defense Governance Pipeline
                </div>
                <div style={{ color: '#475569', fontSize: 13, maxWidth: 460, margin: '0 auto', lineHeight: 1.7 }}>
                  Configure an autonomous engagement scenario on the left — select platform, theater, target confidence, ROE classification, comms status, and human override availability.
                  Run the 11-checkpoint IHL/LAWS governance pipeline. Every authorized decision generates a PQC-signed{' '}
                  <span style={{ color: DEF_LIGHT, fontFamily: 'monospace' }}>OMNIX-DEF</span> receipt.
                </div>
                <div style={{ marginTop: 28, display: 'flex', justifyContent: 'center', gap: 10, flexWrap: 'wrap' }}>
                  {['Sensor Fusion Integrity', 'IHL Article 51/57', 'ROE Gate', 'LAWS HITL Check', 'PQC-Signed Receipt'].map(s => (
                    <span key={s} style={{
                      background: `${DEF_BLUE}12`, border: `1px solid ${DEF_BORDER}`,
                      borderRadius: 6, padding: '5px 12px', fontSize: 11, color: DEF_LIGHT, fontWeight: 500,
                    }}>{s}</span>
                  ))}
                </div>
                <div style={{ marginTop: 28, display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, maxWidth: 480, margin: '28px auto 0' }}>
                  {[
                    { icon: <Zap size={14} />, label: 'Sub-second evaluation' },
                    { icon: <Shield size={14} />, label: '6 hard block conditions' },
                    { icon: <Lock size={14} />, label: 'Dilithium-3 PQC receipt' },
                  ].map((item, i) => (
                    <div key={i} style={{ background: '#06111E', border: '1px solid #1E3A5F', borderRadius: 8, padding: '12px 10px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
                      <div style={{ color: DEF_BLUE }}>{item.icon}</div>
                      <div style={{ fontSize: 10, color: '#64748B', textAlign: 'center' }}>{item.label}</div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div>
                {/* Final Result Banner */}
                {finalResult && (
                  <div style={{
                    borderRadius: 12, padding: '16px 20px', marginBottom: 14,
                    background: verdictBg(finalResult),
                    border: `1px solid ${verdictBorder(finalResult)}`,
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12,
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      {finalResult === 'AUTHORIZED' ? <CheckCircle size={22} style={{ color: '#10B981' }} />
                       : finalResult === 'HOLD'      ? <AlertTriangle size={22} style={{ color: '#F59E0B' }} />
                       : <XCircle size={22} style={{ color: '#EF4444' }} />}
                      <div>
                        <div style={{ fontWeight: 800, fontSize: 17, color: verdictColor(finalResult) }}>
                          {finalResult === 'AUTHORIZED' ? 'ENGAGEMENT AUTHORIZED' :
                           finalResult === 'HOLD'        ? 'HOLD — ESCALATE TO COMMANDER' :
                           finalResult === 'HARD_BLOCK'  ? 'HARD BLOCK — ENGAGEMENT SUSPENDED' :
                           'BLOCKED — GOVERNANCE THRESHOLD BREACH'}
                        </div>
                        {receiptId && (
                          <div style={{ fontSize: 11, color: '#10B981', fontFamily: 'monospace', marginTop: 3 }}>
                            Receipt: {receiptId} · Dilithium-3 signed · ADR-DEF-001
                          </div>
                        )}
                        {!receiptId && finalResult !== 'AUTHORIZED' && (
                          <div style={{ fontSize: 11, color: '#EF4444', marginTop: 3 }}>
                            No receipt issued — action blocked by OMNIX Defense Governance pipeline
                          </div>
                        )}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right', fontSize: 11, color: '#475569' }}>
                      <div>{dt.emoji} {dt.label}</div>
                      <div>{plat.emoji} {plat.label.split('(')[0].trim()}</div>
                      <div>{theater.emoji} {theater.label}</div>
                    </div>
                  </div>
                )}

                {/* Checkpoints */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 9 }}>
                  {checkpoints.map((cp, i) => {
                    const isActive   = currentCp === i
                    const borderClr  = cp.status === 'evaluating' ? DEF_BLUE
                      : cp.status === 'pass'  ? '#10B981'
                      : cp.status === 'warn'  ? '#F59E0B'
                      : cp.status === 'block' ? '#EF4444'
                      : '#1E293B'
                    const barClr     = cp.status === 'pass' ? '#10B981'
                      : cp.status === 'warn'  ? '#F59E0B'
                      : cp.status === 'block' ? '#EF4444'
                      : DEF_BLUE
                    return (
                      <div key={i} style={{
                        background: isActive ? `${DEF_BLUE}08` : 'rgba(10,20,36,0.92)',
                        borderRadius: 10, padding: '13px 15px',
                        border: `1px solid ${borderClr}44`,
                        transition: 'all 0.3s',
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1 }}>
                            {statusIcon(cp.status)}
                            <div>
                              <div style={{ fontSize: 13, fontWeight: 700, color: '#E2E8F0' }}>{cp.name}</div>
                              <div style={{ fontSize: 10, color: '#475569' }}>{cp.generic}</div>
                            </div>
                          </div>
                          <div style={{ textAlign: 'right', flexShrink: 0, marginLeft: 12 }}>
                            <div style={{ fontSize: 20, fontWeight: 800, color: statusColor(cp.status), lineHeight: 1 }}>{cp.score}</div>
                            <div style={{ fontSize: 10, color: '#334155' }}>min {cp.threshold}</div>
                          </div>
                        </div>

                        <ScoreBar score={cp.score} threshold={cp.threshold} color={barClr} />

                        {cp.status !== 'pending' && (
                          <div style={{ marginTop: 10 }}>
                            <div style={{ fontSize: 12, color: '#94A3B8', lineHeight: 1.55, marginBottom: 6 }}>{cp.reasoning}</div>
                            <div style={{
                              fontSize: 10, color: '#475569', fontFamily: 'monospace',
                              background: '#06111E', padding: '6px 10px', borderRadius: 5,
                            }}>{cp.detail}</div>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ── Footer ─────────────────────────────────────────────────────────── */}
        <div style={{ marginTop: 28, textAlign: 'center', color: '#1E3A5F', fontSize: 11 }}>
          OMNIX Quantum · Autonomous Defense Governance · ADR-DEF-001 · 11-Checkpoint Fail-Closed Pipeline
          &nbsp;·&nbsp; IHL Articles 51/57 · CCW LAWS Protocol · Dilithium-3 (ML-DSA-65) PQC · Receipts: OMNIX-DEF-&#123;12HEX&#125;
          &nbsp;·&nbsp; <Link to="/try" style={{ color: DEF_BLUE, textDecoration: 'none' }}>Public Sandbox →</Link>
          &nbsp;·&nbsp; <Link to="/" style={{ color: DEF_BLUE, textDecoration: 'none' }}>Back to Platform →</Link>
        </div>
      </div>
    </div>
  )
}
