import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield, CheckCircle, XCircle, AlertTriangle, Activity,
  Clock, Cpu, Radio, Battery, Zap, Lock, ArrowRight, Eye, Target, Layers, Brain,
} from 'lucide-react'

// ── Brand colors ───────────────────────────────────────────────────────────────
const ROB_INDIGO  = '#6366F1'
const ROB_LIGHT   = '#818CF8'
const ROB_DARK    = '#07080F'
const ROB_BORDER  = '#6366F133'

// ── Domain data ────────────────────────────────────────────────────────────────
const ROBOT_TYPES = [
  { value: 'industrial_arm', label: 'Industrial Arm (6-DOF)',           emoji: '🦾', riskFactor: 1.10 },
  { value: 'amr',            label: 'AMR — Autonomous Mobile Robot',    emoji: '🤖', riskFactor: 1.08 },
  { value: 'cobot',          label: 'Cobot — Collaborative Robot',      emoji: '🦿', riskFactor: 1.22 },
  { value: 'drone',          label: 'Industrial Drone (UAV)',            emoji: '🚁', riskFactor: 1.15 },
  { value: 'agv',            label: 'AGV — Automated Guided Vehicle',   emoji: '🚛', riskFactor: 1.05 },
  { value: 'humanoid',       label: 'Humanoid Service Robot',           emoji: '🧑‍🤝‍🧑', riskFactor: 1.30 },
]

const INDUSTRIES = [
  { value: 'automotive',    label: 'Automotive Manufacturing',  emoji: '🚗', strictness: 1.12 },
  { value: 'electronics',   label: 'Electronics Assembly',      emoji: '🔌', strictness: 1.05 },
  { value: 'logistics',     label: 'Logistics & Warehousing',   emoji: '📦', strictness: 1.00 },
  { value: 'pharma',        label: 'Pharmaceutical / GMP',      emoji: '💊', strictness: 1.20 },
  { value: 'food',          label: 'Food & Beverage',           emoji: '🍽️', strictness: 1.08 },
  { value: 'construction',  label: 'Construction & Civil',      emoji: '🏗️', strictness: 1.18 },
  { value: 'healthcare',    label: 'Healthcare / Clinical',     emoji: '🏥', strictness: 1.35 },
]

const ACTION_TYPES = [
  { value: 'pick_place',     label: 'Pick & Place Operation',       emoji: '📋', complexity: 0.80 },
  { value: 'navigate',       label: 'Navigate Aisle / Zone',        emoji: '🗺️', complexity: 0.70 },
  { value: 'weld',           label: 'Welding / Joining',            emoji: '⚡', complexity: 0.95 },
  { value: 'human_handoff',  label: 'Human Handoff (Collaboration)',emoji: '🤝', complexity: 1.10 },
  { value: 'lift_heavy',     label: 'Heavy Load Lift (>50kg)',      emoji: '⬆️', complexity: 1.05 },
  { value: 'inspect',        label: 'Precision Inspection',         emoji: '🔍', complexity: 0.85 },
]

const ENVIRONMENTS = [
  { value: 'fully_auto',  label: 'Fully Automated Zone (no humans)',  emoji: '🔒', humanFactor: 0.95 },
  { value: 'semi_auto',   label: 'Semi-Automated (occasional entry)', emoji: '⚠️', humanFactor: 0.72 },
  { value: 'human_zone',  label: 'Human-Present Zone (ISO/TS 15066)',emoji: '👷', humanFactor: 0.40 },
  { value: 'outdoor',     label: 'Outdoor / Variable Conditions',     emoji: '🌤️', humanFactor: 0.60 },
]

// ── Scenario presets ───────────────────────────────────────────────────────────
const PRESETS = [
  {
    label: 'Industrial Arm — Weld',
    emoji: '🦾',
    s: {
      robotType: 'industrial_arm', industry: 'automotive', actionType: 'weld',
      environment: 'fully_auto', sensorConfidence: 88, collisionRisk: 12,
      batteryPct: 94, proximityM: 380, speedMs: 1.2,
    },
  },
  {
    label: 'AMR — Logistics Run',
    emoji: '🤖',
    s: {
      robotType: 'amr', industry: 'logistics', actionType: 'navigate',
      environment: 'semi_auto', sensorConfidence: 82, collisionRisk: 22,
      batteryPct: 78, proximityM: 210, speedMs: 0.8,
    },
  },
  {
    label: 'Cobot — Human Handoff',
    emoji: '🦿',
    s: {
      robotType: 'cobot', industry: 'electronics', actionType: 'human_handoff',
      environment: 'human_zone', sensorConfidence: 76, collisionRisk: 18,
      batteryPct: 88, proximityM: 95, speedMs: 0.3,
    },
  },
  {
    label: 'Drone — Pharma Inspect',
    emoji: '🚁',
    s: {
      robotType: 'drone', industry: 'pharma', actionType: 'inspect',
      environment: 'semi_auto', sensorConfidence: 79, collisionRisk: 28,
      batteryPct: 71, proximityM: 150, speedMs: 0.6,
    },
  },
  {
    label: '⚠ Near Collision — Block Test',
    emoji: '⚠️',
    s: {
      robotType: 'humanoid', industry: 'healthcare', actionType: 'human_handoff',
      environment: 'human_zone', sensorConfidence: 31, collisionRisk: 88,
      batteryPct: 22, proximityM: 28, speedMs: 2.1,
    },
  },
]

// ── Types ──────────────────────────────────────────────────────────────────────
interface Scenario {
  robotType:        string
  industry:         string
  actionType:       string
  environment:      string
  sensorConfidence: number
  collisionRisk:    number
  batteryPct:       number
  proximityM:       number   // cm
  speedMs:          number   // m/s
}

interface CheckpointResult {
  name:      string
  generic:   string
  icon:      React.ReactNode
  status:    'pending' | 'evaluating' | 'pass' | 'warn' | 'block'
  score:     number
  threshold: number
  reasoning: string
  detail:    string
}

// ── Score bar ──────────────────────────────────────────────────────────────────
function ScoreBar({ score, threshold, color }: { score: number; threshold: number; color: string }) {
  return (
    <div style={{ position: 'relative', height: 6, background: '#0D0E1A', borderRadius: 3, overflow: 'visible' }}>
      <div style={{
        position: 'absolute', left: `${threshold}%`, top: -3, width: 2, height: 12,
        background: '#F59E0B', borderRadius: 1, zIndex: 2,
      }} />
      <div style={{
        height: '100%', width: `${Math.min(score, 100)}%`,
        background: color, borderRadius: 3, transition: 'width 0.9s ease',
      }} />
    </div>
  )
}

// ── Checkpoint builder ─────────────────────────────────────────────────────────
function buildCheckpoints(s: Scenario): CheckpointResult[] {
  const robot  = ROBOT_TYPES.find(r => r.value === s.robotType)    || ROBOT_TYPES[0]
  const ind    = INDUSTRIES.find(i => i.value === s.industry)       || INDUSTRIES[0]
  const action = ACTION_TYPES.find(a => a.value === s.actionType)   || ACTION_TYPES[0]
  const env    = ENVIRONMENTS.find(e => e.value === s.environment)  || ENVIRONMENTS[0]

  const sc  = s.sensorConfidence / 100
  const cr  = s.collisionRisk    / 100
  const bat = s.batteryPct       / 100
  const prx = s.proximityM       // cm
  const spd = s.speedMs          // m/s
  const rf  = robot.riskFactor * ind.strictness

  // CP scores
  const sensorScore     = Math.round(Math.min(95, (sc * 55 + (1 - cr) * 28 + env.humanFactor * 17) * 100 / rf))
  const collisionScore  = Math.round(Math.min(95, (1 - cr) * 100 * (sc >= 0.65 ? 1.0 : 0.75)))
  const proximityScore  = Math.round(Math.min(95,
    prx >= 300 ? 92 : prx >= 150 ? 80 : prx >= 80 ? 62 : prx >= 50 ? 44 : 20
  ) * env.humanFactor + 5)
  const batteryScore    = Math.round(Math.min(95, bat * 85 + (bat >= 0.40 ? 10 : 0)))
  const feasibilityScore = Math.round(Math.min(95, (sc * 42 + (1 - action.complexity * 0.50) * 38 + bat * 20) * 100))
  const envScore        = Math.round(Math.min(95, env.humanFactor * 100 * (1 / ind.strictness) * 1.15))

  const sigs  = [sensorScore, collisionScore, proximityScore, batteryScore, feasibilityScore, envScore]
  const avg   = sigs.reduce((a, b) => a + b, 0) / sigs.length
  const vari  = sigs.reduce((a, b) => a + Math.pow(b - avg, 2), 0) / sigs.length
  const div   = Math.sqrt(vari)
  const contraScore    = Math.round(Math.max(0, Math.min(95, 100 - div * 1.8)))
  const temporalScore  = Math.round(Math.min(95, sensorScore * 0.45 + feasibilityScore * 0.35 + batteryScore * 0.20))
  const edgeScore      = Math.round(sensorScore * 0.55 + contraScore * 0.45)
  const complianceScore = Math.round(Math.min(95, (1 - cr) * 35 + env.humanFactor * 38 + (sc >= 0.70 ? 20 : 10) + (bat >= 0.30 ? 7 : 0)))
  const eStopScore     = Math.round(Math.min(95,
    env.value === 'fully_auto' ? 92 :
    env.value === 'semi_auto'  ? 78 :
    env.value === 'human_zone' ? 65 : 55
  ))

  return [
    {
      name: 'Sensor Fusion Integrity',
      generic: 'CP-1: Are all robot sensors valid and fused?',
      icon: <Eye size={15} />,
      status: 'pending', score: sensorScore, threshold: 55,
      reasoning: sensorScore >= 55
        ? `Sensor fusion verified — confidence ${s.sensorConfidence}%, collision risk ${s.collisionRisk}%, environment factor ${env.humanFactor}× | Robot+industry risk: ${rf.toFixed(2)}×`
        : `Sensor fusion insufficient — ${s.sensorConfidence}% sensor confidence below safe threshold for ${robot.label} in ${ind.label}`,
      detail: `SC:${s.sensorConfidence}%×0.55 + Clear:${(100-s.collisionRisk)}%×0.28 + EnvF:${(env.humanFactor*100).toFixed(0)}%×0.17 = ${sensorScore} ÷ RF:${rf.toFixed(2)}×`,
    },
    {
      name: 'Collision Risk Assessment',
      generic: 'CP-2: Is the path clear? ISO 10218-1 §5.4',
      icon: <Target size={15} />,
      status: 'pending', score: collisionScore, threshold: 60,
      reasoning: collisionScore >= 60
        ? `Collision risk ${s.collisionRisk}% within acceptable bounds — sensor coverage ${s.sensorConfidence}% provides adequate obstacle awareness`
        : `Collision risk ${s.collisionRisk}% exceeds safe threshold — ${s.sensorConfidence < 65 ? 'degraded sensor coverage amplifies risk' : 'path clearance insufficient'} under ISO 10218-1`,
      detail: `Clear factor: ${(100-s.collisionRisk)}% | Sensor penalty: ${sc >= 0.65 ? '×1.00' : '×0.75'} | Collision score: ${collisionScore}/100 | Threshold: ≥60`,
    },
    {
      name: 'Human Proximity Gate',
      generic: 'CP-3: Safe separation — ISO/TS 15066 §5.5?',
      icon: <Shield size={15} />,
      status: 'pending', score: proximityScore, threshold: 50,
      reasoning: proximityScore >= 50
        ? `Human separation ${s.proximityM}cm satisfies ISO/TS 15066 power-and-force limiting requirements for ${env.label}`
        : `Proximity violation — ${s.proximityM}cm is below minimum safe separation for ${env.label} under ISO/TS 15066 §5.5 at speed ${spd.toFixed(1)} m/s`,
      detail: `Proximity: ${s.proximityM}cm | Env factor: ×${env.humanFactor} | Speed: ${spd.toFixed(1)} m/s | ISO/TS 15066: ${proximityScore >= 50 ? 'PASS' : 'FAIL'} | Score: ${proximityScore}/100`,
    },
    {
      name: 'Battery & Power Sufficiency',
      generic: 'CP-4: Adequate power to complete action safely?',
      icon: <Battery size={15} />,
      status: 'pending', score: batteryScore, threshold: 38,
      reasoning: batteryScore >= 38
        ? `Battery ${s.batteryPct}% provides sufficient power for ${action.label} — safe completion margin confirmed`
        : `Battery ${s.batteryPct}% insufficient — mid-action power failure risk for ${action.label} creates uncontrolled stop hazard (IEC 61508 §7.4)`,
      detail: `Battery: ${s.batteryPct}% | Reserve bonus: ${bat >= 0.40 ? '+10' : '+0'} | Power score: ${batteryScore}/100 | IEC 61508 min: ≥38`,
    },
    {
      name: 'Action Feasibility Check',
      generic: 'CP-5: Can the robot execute this action safely?',
      icon: <Cpu size={15} />,
      status: 'pending', score: feasibilityScore, threshold: 45,
      reasoning: feasibilityScore >= 45
        ? `${action.label} is feasible — sensor coverage ${s.sensorConfidence}% and battery ${s.batteryPct}% support safe execution at complexity ×${action.complexity}`
        : `Action infeasible — sensor ${s.sensorConfidence}% or battery ${s.batteryPct}% insufficient for ${action.label} at complexity ×${action.complexity}`,
      detail: `SC×0.42: ${(sc*42).toFixed(0)} + (1-Cx)×0.38: ${((1-action.complexity*0.5)*38).toFixed(0)} + Bat×0.20: ${(bat*20).toFixed(0)} = ${feasibilityScore}/100`,
    },
    {
      name: 'Environment Classification',
      generic: 'CP-6: Is this environment suitable? RIA R15.06',
      icon: <Radio size={15} />,
      status: 'pending', score: envScore, threshold: 40,
      reasoning: envScore >= 40
        ? `${env.label} environment classified as suitable for ${robot.label} — RIA R15.06 risk category within bounds`
        : `Environment mismatch — ${env.label} (factor ${env.humanFactor}×) creates unacceptable risk for ${robot.label} in ${ind.label} (strictness ${ind.strictness}×)`,
      detail: `Env factor: ${(env.humanFactor*100).toFixed(0)}% | Industry strictness: ${ind.strictness}× | Env score: ${envScore}/100 | RIA R15.06: ${envScore >= 40 ? 'PASS' : 'FAIL'}`,
    },
    {
      name: 'Multi-Sensor Signal Contradiction',
      generic: 'CP-7: Do all sensor channels agree?',
      icon: <Brain size={15} />,
      status: 'pending', score: contraScore, threshold: 40,
      reasoning: contraScore >= 40
        ? `Cross-sensor agreement confirmed — internal divergence ${div.toFixed(1)} across 6 governance channels within acceptable bounds`
        : `High signal contradiction — divergence ${div.toFixed(1)} indicates conflicting sensor data; autonomous action unreliable`,
      detail: `Signal variance: ${vari.toFixed(1)} | Divergence: ${div.toFixed(1)} | Cross-sensor: ${contraScore}% | ${contraScore < 40 ? 'CONTRADICTORY' : contraScore < 58 ? 'TENSIONED' : 'COHERENT'}`,
    },
    {
      name: 'Temporal Operational Coherence',
      generic: 'CP-8: Is the operational state stable over time?',
      icon: <Activity size={15} />,
      status: 'pending', score: temporalScore, threshold: 38,
      reasoning: temporalScore >= 38
        ? `Operational stability confirmed — sensor integrity, action feasibility, and battery margin consistent across decision window`
        : `Temporal instability — current sensor or battery conditions may degrade before action completion`,
      detail: `Sensor×0.45: ${(sensorScore*0.45).toFixed(0)} + Feasibility×0.35: ${(feasibilityScore*0.35).toFixed(0)} + Battery×0.20: ${(batteryScore*0.20).toFixed(0)} = ${temporalScore}/100`,
    },
    {
      name: 'Edge Confirmation (ECR)',
      generic: 'CP-9: Safety boundary convergence verified?',
      icon: <Layers size={15} />,
      status: 'pending', score: edgeScore, threshold: 48,
      reasoning: edgeScore >= 48
        ? `Safety boundary confirmed — sensor fusion integrity and cross-sensor alignment converge at governance edge (${edgeScore}%)`
        : `Weak boundary — sensor fusion and signal consistency do not reinforce; escalate to safety supervisor`,
      detail: `Sensor×0.55: ${(sensorScore*0.55).toFixed(0)} + Contradiction×0.45: ${(contraScore*0.45).toFixed(0)} = ${edgeScore}/100 | ECR: ${edgeScore >= 48 ? 'CONFIRMED' : 'WEAK'}`,
    },
    {
      name: 'Compliance Gate',
      generic: 'CP-10: IEC 61508 / RIA R15.06 regulatory pass?',
      icon: <Lock size={15} />,
      status: 'pending', score: complianceScore, threshold: 55,
      reasoning: complianceScore >= 55
        ? `Regulatory compliance confirmed — collision, environment, sensor, and battery criteria satisfy IEC 61508 SIL-2 and RIA R15.06 for ${robot.label}`
        : `Regulatory non-compliance — one or more IEC 61508 SIL-2 criteria failed for ${robot.label} in ${ind.label}`,
      detail: `Clear×0.35: ${((1-cr)*35).toFixed(0)} + Env×0.38: ${(env.humanFactor*38).toFixed(0)} + Sensor: ${sc >= 0.70 ? '20' : '10'} + Battery: ${bat >= 0.30 ? '7' : '0'} = ${complianceScore}/100`,
    },
    {
      name: 'E-Stop Accessibility',
      generic: 'CP-11: Emergency stop accessible? ISO 13850',
      icon: <Zap size={15} />,
      status: 'pending', score: eStopScore, threshold: 45,
      reasoning: eStopScore >= 45
        ? `Emergency stop confirmed accessible — ${env.label} configuration satisfies ISO 13850 stop category 0/1 requirements`
        : `E-Stop accessibility risk — ${env.label} environment does not guarantee ISO 13850 Category 0 stop access within required time`,
      detail: `Zone: ${env.label.split('(')[0].trim()} | E-Stop score: ${eStopScore}/100 | ISO 13850 Cat 0: ${eStopScore >= 45 ? 'ACCESSIBLE' : 'AT RISK'}`,
    },
  ]
}

function buildReceiptId() {
  const hex = Array.from({ length: 12 }, () => Math.floor(Math.random() * 16).toString(16).toUpperCase()).join('')
  return `OMNIX-ROB-${hex}`
}

// ── Main component ─────────────────────────────────────────────────────────────
export default function RoboticsGovernanceDemo() {
  const [scenario, setScenario] = useState<Scenario>({
    robotType:        'industrial_arm',
    industry:         'automotive',
    actionType:       'pick_place',
    environment:      'fully_auto',
    sensorConfidence: 85,
    collisionRisk:    15,
    batteryPct:       90,
    proximityM:       350,
    speedMs:          1.0,
  })
  const [checkpoints, setCheckpoints] = useState<CheckpointResult[]>([])
  const [currentCp,   setCurrentCp]   = useState(-1)
  const [finalResult, setFinalResult] = useState<string | null>(null)
  const [receiptId,   setReceiptId]   = useState<string | null>(null)
  const [isRunning,   setIsRunning]   = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const robot  = ROBOT_TYPES.find(r => r.value === scenario.robotType)   || ROBOT_TYPES[0]
  const ind    = INDUSTRIES.find(i => i.value === scenario.industry)      || INDUSTRIES[0]
  const action = ACTION_TYPES.find(a => a.value === scenario.actionType)  || ACTION_TYPES[0]
  const env    = ENVIRONMENTS.find(e => e.value === scenario.environment) || ENVIRONMENTS[0]

  // Hard block detection (real-time)
  const hb_collision = scenario.collisionRisk > 85
  const hb_sensor    = scenario.sensorConfidence < 20
  const hb_proximity = scenario.proximityM < 50 && scenario.speedMs > 1.5
  const anyHardBlock = hb_collision || hb_sensor || hb_proximity

  function applyPreset(p: typeof PRESETS[0]) {
    setScenario(prev => ({ ...prev, ...p.s }))
    setCheckpoints([]); setFinalResult(null); setReceiptId(null); setCurrentCp(-1)
  }

  function runEvaluation() {
    if (isRunning) return
    const cps = buildCheckpoints(scenario)
    setCheckpoints(cps.map(c => ({ ...c, status: 'pending' })))
    setCurrentCp(-1); setFinalResult(null); setReceiptId(null); setIsRunning(true)

    cps.forEach((_, i) => {
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
              ...c,
              status: (c.score >= c.threshold ? 'pass' : c.score >= c.threshold * 0.72 ? 'warn' : 'block') as CheckpointResult['status'],
            }))
            const hardFails = finalCps.filter(c => c.score < c.threshold * 0.5).length
            const blocks    = finalCps.filter(c => c.score < c.threshold).length
            let verdict: string
            if (anyHardBlock || hardFails > 0) verdict = 'HARD_BLOCK'
            else if (blocks >= 3)              verdict = 'BLOCKED'
            else if (blocks > 0)              verdict = 'HOLD'
            else                              verdict = 'EXECUTE'
            setCheckpoints(finalCps); setCurrentCp(-1); setFinalResult(verdict)
            if (verdict === 'EXECUTE') setReceiptId(buildReceiptId())
            setIsRunning(false)
          }, 380)
        }
      }, i * 300)
    })
  }

  useEffect(() => () => { if (timerRef.current) clearTimeout(timerRef.current) }, [])

  const statusIcon = (s: CheckpointResult['status']) => {
    if (s === 'pending')    return <Clock       size={15} style={{ color: '#334155' }} />
    if (s === 'evaluating') return <Activity    size={15} style={{ color: ROB_INDIGO, animation: 'pulse 0.8s ease-in-out infinite' }} />
    if (s === 'pass')       return <CheckCircle size={15} style={{ color: '#10B981' }} />
    if (s === 'warn')       return <AlertTriangle size={15} style={{ color: '#F59E0B' }} />
    return <XCircle size={15} style={{ color: '#EF4444' }} />
  }
  const statusColor = (s: CheckpointResult['status']) => {
    if (s === 'pass')       return '#10B981'
    if (s === 'warn')       return '#F59E0B'
    if (s === 'block')      return '#EF4444'
    if (s === 'evaluating') return ROB_INDIGO
    return '#334155'
  }
  const verdictColor  = (v: string | null) => v === 'EXECUTE' ? '#10B981' : v === 'HOLD' ? '#F59E0B' : '#EF4444'
  const verdictBg     = (v: string | null) => v === 'EXECUTE' ? 'rgba(16,185,129,0.10)' : v === 'HOLD' ? 'rgba(245,158,11,0.10)' : 'rgba(239,68,68,0.10)'
  const verdictBorder = (v: string | null) => v === 'EXECUTE' ? '#10B98133' : v === 'HOLD' ? '#F59E0B33' : '#EF444433'

  const inputStyle: React.CSSProperties = {
    background: '#0C0D1A', border: '1px solid #1E1F3A', borderRadius: 7,
    color: '#CBD5E1', padding: '9px 12px', fontSize: 13, width: '100%',
    outline: 'none', cursor: 'pointer',
  }
  const labelStyle: React.CSSProperties = {
    fontSize: 10, color: '#64748B', marginBottom: 5, display: 'block',
    fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em',
  }
  const sliderStyle: React.CSSProperties = { width: '100%', accentColor: ROB_INDIGO, cursor: 'pointer', height: 4 }
  const chg = (field: keyof Scenario) => (e: React.ChangeEvent<HTMLSelectElement | HTMLInputElement>) => {
    const val = e.target.type === 'range'
      ? field === 'speedMs' ? parseFloat(e.target.value) : parseInt(e.target.value)
      : e.target.value
    setScenario(p => ({ ...p, [field]: val }))
    setCheckpoints([]); setFinalResult(null); setReceiptId(null)
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: `linear-gradient(160deg, ${ROB_DARK} 0%, #0B0C1A 50%, #080910 100%)`,
      color: '#E2E8F0', fontFamily: "'Inter', sans-serif", padding: '24px',
    }}>
      <style>{`
        @keyframes pulse { 0%,100%{opacity:1}50%{opacity:0.25} }
        * { box-sizing:border-box }
        select option { background: #0C0D1A }
        input[type=range]::-webkit-slider-thumb { background: ${ROB_INDIGO} }
      `}</style>

      <div style={{ maxWidth: 1320, margin: '0 auto' }}>

        {/* ── Header ─────────────────────────────────────────────────────────── */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
            <Link to="/" style={{ color: '#475569', fontSize: 12, textDecoration: 'none' }}>← Home</Link>
            <span style={{ color: '#334155', fontSize: 12 }}>/</span>
            <span style={{ color: '#64748B', fontSize: 12 }}>Industrial Robotics Governance</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
              <div style={{
                width: 50, height: 50, borderRadius: 12, display: 'flex', alignItems: 'center',
                justifyContent: 'center', fontSize: 24,
                background: `${ROB_INDIGO}18`, border: `1px solid ${ROB_INDIGO}44`,
              }}>🤖</div>
              <div>
                <div style={{ fontSize: 22, fontWeight: 800, letterSpacing: '-0.02em', color: '#F1F5F9' }}>
                  Industrial Robotics Governance — Interactive Demo
                </div>
                <div style={{ fontSize: 12, color: '#475569', marginTop: 3 }}>
                  ADR-ROB-001 · 11-Checkpoint Fail-Closed Pipeline · ISO 10218 · IEC 61508 · ISO/TS 15066 ·{' '}
                  <span style={{ color: ROB_LIGHT, fontFamily: 'monospace' }}>OMNIX-ROB-{'{12HEX}'}</span> PQC Receipts
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {['ISO 10218', 'IEC 61508', 'RIA R15.06', 'ISO/TS 15066'].map(b => (
                <span key={b} style={{
                  padding: '4px 10px', fontSize: 10, fontWeight: 700, borderRadius: 5,
                  background: `${ROB_INDIGO}14`, border: `1px solid ${ROB_INDIGO}33`, color: ROB_LIGHT,
                  textTransform: 'uppercase', letterSpacing: '0.04em',
                }}>{b}</span>
              ))}
            </div>
          </div>
        </div>

        {/* ── Presets ─────────────────────────────────────────────────────────── */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ fontSize: 10, color: '#475569', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', marginRight: 4 }}>
            Quick Load
          </span>
          {PRESETS.map(p => (
            <button key={p.label} onClick={() => applyPreset(p)} style={{
              padding: '6px 14px', fontSize: 12, borderRadius: 7, cursor: 'pointer',
              background: `${ROB_INDIGO}10`, border: `1px solid ${ROB_INDIGO}28`,
              color: '#94A3B8', fontWeight: 600, transition: 'all 0.15s',
              display: 'flex', alignItems: 'center', gap: 5,
            }}
              onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = ROB_INDIGO; (e.currentTarget as HTMLElement).style.color = ROB_LIGHT }}
              onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = `${ROB_INDIGO}28`; (e.currentTarget as HTMLElement).style.color = '#94A3B8' }}
            >{p.emoji} {p.label}</button>
          ))}
        </div>

        {/* ── Two-Column Layout ───────────────────────────────────────────────── */}
        <div style={{ display: 'grid', gridTemplateColumns: '390px 1fr', gap: 18, alignItems: 'start' }}>

          {/* ── LEFT: Config ─────────────────────────────────────────────────── */}
          <div>
            <div style={{
              background: 'rgba(11,12,26,0.97)', borderRadius: 14, padding: 22,
              border: `1px solid ${ROB_BORDER}`, marginBottom: 14,
            }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: ROB_LIGHT, marginBottom: 18, display: 'flex', alignItems: 'center', gap: 7 }}>
                <Cpu size={14} color={ROB_INDIGO} /> Robot Action Parameters
              </div>

              {/* Robot Type */}
              <div style={{ marginBottom: 13 }}>
                <label style={labelStyle}>Robot Type</label>
                <select style={inputStyle} value={scenario.robotType} onChange={chg('robotType')}>
                  {ROBOT_TYPES.map(r => <option key={r.value} value={r.value}>{r.emoji} {r.label}</option>)}
                </select>
                <div style={{ fontSize: 10, color: '#64748B', marginTop: 4 }}>
                  Risk factor: {robot.riskFactor}× · Industry strictness: {ind.strictness}×
                </div>
              </div>

              {/* Industry */}
              <div style={{ marginBottom: 13 }}>
                <label style={labelStyle}>Industry Sector</label>
                <select style={inputStyle} value={scenario.industry} onChange={chg('industry')}>
                  {INDUSTRIES.map(i => <option key={i.value} value={i.value}>{i.emoji} {i.label}</option>)}
                </select>
              </div>

              {/* Action Type */}
              <div style={{ marginBottom: 13 }}>
                <label style={labelStyle}>Action Type</label>
                <select style={inputStyle} value={scenario.actionType} onChange={chg('actionType')}>
                  {ACTION_TYPES.map(a => <option key={a.value} value={a.value}>{a.emoji} {a.label}</option>)}
                </select>
                <div style={{ fontSize: 10, color: '#64748B', marginTop: 4 }}>
                  Complexity factor: ×{action.complexity.toFixed(2)}
                </div>
              </div>

              {/* Environment */}
              <div style={{ marginBottom: 18 }}>
                <label style={labelStyle}>Operational Environment</label>
                <select style={inputStyle} value={scenario.environment} onChange={chg('environment')}>
                  {ENVIRONMENTS.map(e => <option key={e.value} value={e.value}>{e.emoji} {e.label}</option>)}
                </select>
              </div>

              {/* Sensor Confidence */}
              <div style={{ marginBottom: 13 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                  <label style={{ ...labelStyle, marginBottom: 0 }}>Sensor Confidence</label>
                  <span style={{ fontSize: 13, fontWeight: 700, color: hb_sensor ? '#EF4444' : scenario.sensorConfidence < 50 ? '#F59E0B' : '#10B981' }}>
                    {scenario.sensorConfidence}%{hb_sensor && ' ⚠ HARD BLOCK'}
                  </span>
                </div>
                <input type="range" min={10} max={99} step={1} style={sliderStyle}
                  value={scenario.sensorConfidence} onChange={chg('sensorConfidence')} />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#334155', marginTop: 2 }}>
                  <span style={{ color: '#EF4444' }}>&lt;20% Blind</span>
                  <span style={{ color: '#F59E0B' }}>50% Marginal</span>
                  <span style={{ color: '#10B981' }}>85%+ Reliable</span>
                </div>
              </div>

              {/* Collision Risk */}
              <div style={{ marginBottom: 13 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                  <label style={{ ...labelStyle, marginBottom: 0 }}>Collision Risk</label>
                  <span style={{ fontSize: 13, fontWeight: 700, color: hb_collision ? '#EF4444' : scenario.collisionRisk > 55 ? '#F59E0B' : '#10B981' }}>
                    {scenario.collisionRisk}%{hb_collision && ' ⚠ HARD BLOCK'}
                  </span>
                </div>
                <input type="range" min={0} max={99} step={1} style={sliderStyle}
                  value={scenario.collisionRisk} onChange={chg('collisionRisk')} />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#334155', marginTop: 2 }}>
                  <span style={{ color: '#10B981' }}>0% Clear</span>
                  <span style={{ color: '#F59E0B' }}>55% High</span>
                  <span style={{ color: '#EF4444' }}>&gt;85% Block</span>
                </div>
              </div>

              {/* Battery */}
              <div style={{ marginBottom: 13 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                  <label style={{ ...labelStyle, marginBottom: 0 }}>Battery Level</label>
                  <span style={{ fontSize: 13, fontWeight: 700, color: scenario.batteryPct < 20 ? '#EF4444' : scenario.batteryPct < 40 ? '#F59E0B' : '#10B981' }}>
                    {scenario.batteryPct}%
                  </span>
                </div>
                <input type="range" min={5} max={100} step={1} style={sliderStyle}
                  value={scenario.batteryPct} onChange={chg('batteryPct')} />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#334155', marginTop: 2 }}>
                  <span style={{ color: '#EF4444' }}>5% Critical</span>
                  <span style={{ color: '#F59E0B' }}>40% Low</span>
                  <span style={{ color: '#10B981' }}>80%+ Optimal</span>
                </div>
              </div>

              {/* Proximity */}
              <div style={{ marginBottom: 13 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                  <label style={{ ...labelStyle, marginBottom: 0 }}>Human Proximity (cm)</label>
                  <span style={{ fontSize: 13, fontWeight: 700, color: scenario.proximityM < 50 ? '#EF4444' : scenario.proximityM < 120 ? '#F59E0B' : '#10B981' }}>
                    {scenario.proximityM}cm
                  </span>
                </div>
                <input type="range" min={10} max={500} step={5} style={sliderStyle}
                  value={scenario.proximityM} onChange={chg('proximityM')} />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#334155', marginTop: 2 }}>
                  <span style={{ color: '#EF4444' }}>10cm Touch</span>
                  <span style={{ color: '#F59E0B' }}>120cm Min</span>
                  <span style={{ color: '#10B981' }}>300cm+ Safe</span>
                </div>
              </div>

              {/* Speed */}
              <div style={{ marginBottom: 20 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                  <label style={{ ...labelStyle, marginBottom: 0 }}>Speed (m/s)</label>
                  <span style={{ fontSize: 13, fontWeight: 700, color: hb_proximity ? '#EF4444' : scenario.speedMs > 1.8 ? '#F59E0B' : '#10B981' }}>
                    {scenario.speedMs.toFixed(1)} m/s{hb_proximity && ' ⚠ HARD BLOCK'}
                  </span>
                </div>
                <input type="range" min={0.1} max={3.0} step={0.1} style={sliderStyle}
                  value={scenario.speedMs} onChange={chg('speedMs')} />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#334155', marginTop: 2 }}>
                  <span style={{ color: '#10B981' }}>0.1 Creep</span>
                  <span style={{ color: '#F59E0B' }}>1.5 Fast</span>
                  <span style={{ color: '#EF4444' }}>3.0 Max</span>
                </div>
              </div>

              {/* Hard block summary */}
              {anyHardBlock && (
                <div style={{
                  background: 'rgba(239,68,68,0.08)', border: '1px solid #EF444430',
                  borderRadius: 8, padding: '10px 14px', marginBottom: 16,
                }}>
                  <div style={{ color: '#EF4444', fontWeight: 700, fontSize: 11, marginBottom: 6 }}>⚠ Hard Block Active — Will BLOCK before evaluation</div>
                  {hb_collision  && <div style={{ color: '#FCA5A5', fontSize: 11, marginBottom: 3 }}>• Collision risk {scenario.collisionRisk}% &gt;85% — imminent collision, action suspended (ISO 10218-1 §5.4)</div>}
                  {hb_sensor     && <div style={{ color: '#FCA5A5', fontSize: 11, marginBottom: 3 }}>• Sensor confidence {scenario.sensorConfidence}% &lt;20% — blind operation prohibited (IEC 61508 §7)</div>}
                  {hb_proximity  && <div style={{ color: '#FCA5A5', fontSize: 11 }}>• Human at {scenario.proximityM}cm + speed {scenario.speedMs.toFixed(1)} m/s — ISO/TS 15066 separation violation</div>}
                </div>
              )}

              <button onClick={runEvaluation} disabled={isRunning} style={{
                width: '100%', padding: '13px 20px', borderRadius: 10, border: 'none',
                background: isRunning ? '#1E293B' : `linear-gradient(135deg, #4338CA, ${ROB_INDIGO})`,
                color: isRunning ? '#475569' : '#FFF', fontWeight: 700, fontSize: 14,
                cursor: isRunning ? 'not-allowed' : 'pointer', transition: 'all 0.2s',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              }}>
                <Cpu size={15} />
                {isRunning ? 'Evaluating Robot Action…' : 'Run 11-Checkpoint Robotics Governance'}
                {!isRunning && <ArrowRight size={15} />}
              </button>
            </div>

            {/* Scenario Summary */}
            <div style={{ background: 'rgba(11,12,26,0.97)', borderRadius: 12, padding: 16, border: '1px solid #1E1F3A', fontSize: 12 }}>
              <div style={{ color: '#475569', fontWeight: 700, marginBottom: 10, fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                Current Scenario
              </div>
              {[
                ['Robot',      `${robot.emoji} ${robot.label.split('(')[0].trim()}`],
                ['Industry',   `${ind.emoji} ${ind.label}`],
                ['Action',     `${action.emoji} ${action.label}`],
                ['Zone',       `${env.emoji} ${env.label.split('(')[0].trim()}`],
                ['Sensor',     `${scenario.sensorConfidence}%`],
                ['Collision',  `${scenario.collisionRisk}%`],
                ['Battery',    `${scenario.batteryPct}%`],
                ['Proximity',  `${scenario.proximityM}cm`],
                ['Speed',      `${scenario.speedMs.toFixed(1)} m/s`],
              ].map(([k, v]) => (
                <div key={k as string} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5, paddingBottom: 5, borderBottom: '1px solid #0D0E1C' }}>
                  <span style={{ color: '#334155' }}>{k}</span>
                  <span style={{ color: '#94A3B8', fontWeight: 600, maxWidth: 200, textAlign: 'right' }}>{v}</span>
                </div>
              ))}
              <div style={{ marginTop: 8, paddingTop: 8, borderTop: '1px solid #0D0E1C' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#334155', fontSize: 10 }}>Combined Risk Factor</span>
                  <span style={{ color: robot.riskFactor * ind.strictness > 1.35 ? '#EF4444' : '#F59E0B', fontWeight: 700, fontFamily: 'monospace', fontSize: 11 }}>
                    {(robot.riskFactor * ind.strictness).toFixed(2)}×
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* ── RIGHT: Checkpoint Results ───────────────────────────────────── */}
          <div>
            {checkpoints.length === 0 ? (
              <div style={{
                background: 'rgba(11,12,26,0.97)', borderRadius: 14, padding: 52,
                border: `1px solid ${ROB_BORDER}`, textAlign: 'center',
              }}>
                <div style={{ fontSize: 52, marginBottom: 18 }}>🤖</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: ROB_LIGHT, marginBottom: 10 }}>
                  Industrial Robotics Governance Pipeline
                </div>
                <div style={{ color: '#475569', fontSize: 13, maxWidth: 460, margin: '0 auto', lineHeight: 1.7 }}>
                  Configure a robot action on the left — type, industry, action, environment, sensor confidence,
                  collision risk, battery, proximity, and speed. Run the 11-checkpoint ISO 10218 / IEC 61508
                  governance pipeline. Every approved action generates a PQC-signed{' '}
                  <span style={{ color: ROB_LIGHT, fontFamily: 'monospace' }}>OMNIX-ROB</span> receipt.
                </div>
                <div style={{ marginTop: 28, display: 'flex', justifyContent: 'center', gap: 10, flexWrap: 'wrap' }}>
                  {['Sensor Fusion', 'Collision Gate', 'ISO/TS 15066', 'IEC 61508 SIL-2', 'PQC-Signed Receipt'].map(s => (
                    <span key={s} style={{
                      background: `${ROB_INDIGO}12`, border: `1px solid ${ROB_BORDER}`,
                      borderRadius: 6, padding: '5px 12px', fontSize: 11, color: ROB_LIGHT, fontWeight: 500,
                    }}>{s}</span>
                  ))}
                </div>
                <div style={{ marginTop: 28, display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, maxWidth: 480, margin: '28px auto 0' }}>
                  {[
                    { icon: <Zap size={14} />, label: 'Sub-second evaluation' },
                    { icon: <Shield size={14} />, label: '3 hard block conditions' },
                    { icon: <Lock size={14} />, label: 'Dilithium-3 PQC receipt' },
                  ].map((item, i) => (
                    <div key={i} style={{ background: '#0C0D1A', border: '1px solid #1E1F3A', borderRadius: 8, padding: '12px 10px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
                      <div style={{ color: ROB_INDIGO }}>{item.icon}</div>
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
                      {finalResult === 'EXECUTE'
                        ? <CheckCircle size={22} style={{ color: '#10B981' }} />
                        : finalResult === 'HOLD'
                        ? <AlertTriangle size={22} style={{ color: '#F59E0B' }} />
                        : <XCircle size={22} style={{ color: '#EF4444' }} />}
                      <div>
                        <div style={{ fontWeight: 800, fontSize: 17, color: verdictColor(finalResult) }}>
                          {finalResult === 'EXECUTE'    ? 'ACTION AUTHORIZED — EXECUTE' :
                           finalResult === 'HOLD'        ? 'HOLD — ESCALATE TO SAFETY SUPERVISOR' :
                           finalResult === 'HARD_BLOCK'  ? 'HARD BLOCK — ACTION SUSPENDED' :
                           'BLOCKED — GOVERNANCE THRESHOLD BREACH'}
                        </div>
                        {receiptId && (
                          <div style={{ fontSize: 11, color: '#10B981', fontFamily: 'monospace', marginTop: 3 }}>
                            Receipt: {receiptId} · Dilithium-3 signed · ADR-ROB-001
                          </div>
                        )}
                        {!receiptId && (
                          <div style={{ fontSize: 11, color: '#EF4444', marginTop: 3 }}>
                            No receipt issued — action blocked by OMNIX Robotics Governance pipeline
                          </div>
                        )}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right', fontSize: 11, color: '#475569' }}>
                      <div>{robot.emoji} {robot.label.split('(')[0].trim()}</div>
                      <div>{action.emoji} {action.label}</div>
                      <div>{ind.emoji} {ind.label}</div>
                    </div>
                  </div>
                )}

                {/* Checkpoints */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 9 }}>
                  {checkpoints.map((cp, i) => {
                    const isActive  = currentCp === i
                    const borderClr = cp.status === 'evaluating' ? ROB_INDIGO
                      : cp.status === 'pass'  ? '#10B981'
                      : cp.status === 'warn'  ? '#F59E0B'
                      : cp.status === 'block' ? '#EF4444'
                      : '#1E293B'
                    const barClr = cp.status === 'pass'  ? '#10B981'
                      : cp.status === 'warn'  ? '#F59E0B'
                      : cp.status === 'block' ? '#EF4444'
                      : ROB_INDIGO
                    return (
                      <div key={i} style={{
                        background: isActive ? `${ROB_INDIGO}08` : 'rgba(11,12,26,0.92)',
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
                              background: '#0C0D1A', padding: '6px 10px', borderRadius: 5,
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
        <div style={{ marginTop: 28, textAlign: 'center', color: '#1E293B', fontSize: 11 }}>
          OMNIX Quantum · Industrial Robotics Governance · ADR-ROB-001 · 11-Checkpoint Fail-Closed Pipeline
          &nbsp;·&nbsp; ISO 10218-1/2 · IEC 61508 SIL-2 · RIA R15.06 · ISO/TS 15066 · Dilithium-3 (ML-DSA-65) PQC
          &nbsp;·&nbsp; <Link to="/try" style={{ color: ROB_INDIGO, textDecoration: 'none' }}>Public Sandbox →</Link>
          &nbsp;·&nbsp; <Link to="/" style={{ color: ROB_INDIGO, textDecoration: 'none' }}>Back to Platform →</Link>
        </div>
      </div>
    </div>
  )
}
