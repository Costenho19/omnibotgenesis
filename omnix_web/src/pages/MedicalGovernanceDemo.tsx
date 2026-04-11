import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield, CheckCircle, XCircle, Clock, Activity, Brain,
  AlertTriangle, Zap, ArrowRight, Heart, Stethoscope,
  Monitor, Cpu, Lock, TrendingUp, Users
} from 'lucide-react'
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

interface ClinicalCase {
  decisionType: string
  deviceType: string
  patientProfile: string
  jurisdiction: string
  diagnosticConfidence: number
  patientRisk: number
  consentVerified: boolean
  ethicsFlag: boolean
}

const DECISION_TYPES = [
  { value: 'rehabilitation_guidance', label: 'Rehabilitation Guidance', icon: '🦾', baseScore: 0.78 },
  { value: 'diagnostic_alert', label: 'Diagnostic Alert', icon: '🩺', baseScore: 0.82 },
  { value: 'monitoring_alert', label: 'Remote Patient Monitoring', icon: '📡', baseScore: 0.75 },
  { value: 'therapeutic_recommendation', label: 'Therapeutic Recommendation', icon: '💊', baseScore: 0.80 },
  { value: 'surgical_clearance', label: 'Surgical Clearance', icon: '🔬', baseScore: 0.88 },
]

const DEVICE_TYPES = [
  { value: 'Wearable', label: 'Wearable Sensor', sensorBase: 82, noiseLevel: 0.12 },
  { value: 'Clinical_AI', label: 'Clinical AI System', sensorBase: 91, noiseLevel: 0.06 },
  { value: 'Monitoring_System', label: 'Remote Monitoring Device', sensorBase: 87, noiseLevel: 0.09 },
  { value: 'Surgical_Robot', label: 'Surgical Robot', sensorBase: 93, noiseLevel: 0.04 },
]

const PATIENT_PROFILES = [
  { value: 'rehabilitation', label: 'Rehabilitation Patient', riskBase: 0.32 },
  { value: 'chronic_condition', label: 'Chronic Condition', riskBase: 0.48 },
  { value: 'post_surgery', label: 'Post-Surgery', riskBase: 0.58 },
  { value: 'acute_care', label: 'Acute Care', riskBase: 0.65 },
  { value: 'preventive', label: 'Preventive Care', riskBase: 0.12 },
  { value: 'geriatric', label: 'Geriatric Patient', riskBase: 0.52 },
]

const JURISDICTIONS = [
  { value: 'UAE', label: 'UAE — DOH AI Framework', strictness: 1.00 },
  { value: 'EU', label: 'EU — AI Act / MDR High-Risk', strictness: 1.05 },
  { value: 'USA', label: 'USA — FDA SaMD Guidelines', strictness: 1.10 },
  { value: 'UK', label: 'UK — MHRA AI Guidance', strictness: 1.08 },
]

function evaluateMedicalCheckpoints(c: ClinicalCase): CheckpointResult[] {
  const decisionData = DECISION_TYPES.find(d => d.value === c.decisionType) || DECISION_TYPES[0]
  const deviceData = DEVICE_TYPES.find(d => d.value === c.deviceType) || DEVICE_TYPES[0]
  const profileData = PATIENT_PROFILES.find(p => p.value === c.patientProfile) || PATIENT_PROFILES[0]
  const jxData = JURISDICTIONS.find(j => j.value === c.jurisdiction) || JURISDICTIONS[0]

  const diagConf = c.diagnosticConfidence / 100
  const riskIdx = c.patientRisk / 100
  const sensorQ = deviceData.sensorBase / 100 - deviceData.noiseLevel * (1 - diagConf)
  const confThreshold = decisionData.baseScore

  // CP-1: Data Integrity & Sensor Validation
  const cp1Score = Math.round(sensorQ * 100 * (1 - deviceData.noiseLevel * 0.5))
  const cp1Pass = cp1Score >= 62

  // CP-2: Clinical Probability Assessment
  const cp2Score = Math.round(diagConf * 100 / jxData.strictness)
  const cp2Pass = cp2Score >= Math.round(confThreshold * 100)

  // CP-3: Patient Risk Stratification
  const adjustedRisk = riskIdx * profileData.riskBase * (1 + (1 - diagConf) * 0.3) * 100
  const cp3Score = Math.round(100 - adjustedRisk)
  const cp3Pass = cp3Score >= 35

  // CP-4: Multi-Signal Clinical Coherence
  const coherence = Math.round((diagConf * 0.55 + sensorQ * 0.30 + (1 - riskIdx) * 0.15) * 100)
  const cp4Pass = coherence >= 60

  // CP-5: Adverse Trajectory Detection
  const trajectory = Math.round((1 - riskIdx * 0.7 + diagConf * 0.3) * 100)
  const cp5Pass = trajectory >= 55

  // CP-6: Edge-Case & Comorbidity Resilience
  const resilience = Math.round((1 - profileData.riskBase) * sensorQ * 100)
  const cp6Pass = resilience >= 52

  // CP-7: Ethics & Care Plan Alignment
  const ethicsPenalty = c.ethicsFlag ? 40 : 0
  const consentPenalty = !c.consentVerified ? 60 : 0
  const cp7Score = Math.max(0, Math.round(diagConf * 100 * 0.7 + (1 - riskIdx) * 30) - ethicsPenalty - consentPenalty)
  const cp7Pass = cp7Score >= 58 && c.consentVerified

  // CP-8: Regulatory Jurisdiction Compliance
  const cp8Score = Math.round(diagConf * 100 / jxData.strictness)
  const cp8Pass = cp8Score >= 60

  // CP-9: Receipt Integrity (cryptographic — always passes in simulation)
  const cp9Pass = true

  // CP-10: Governance Audit Trail
  const cp10Score = Math.round((cp1Score + cp8Score + cp7Score) / 3)
  const cp10Pass = cp10Score >= 55

  // CP-11: Exit Gate (composite)
  const passingCount = [cp1Pass, cp2Pass, cp3Pass, cp4Pass, cp5Pass, cp6Pass, cp7Pass, cp8Pass, cp9Pass, cp10Pass].filter(Boolean).length
  const cp11Score = Math.round(passingCount * 10)
  const cp11Pass = passingCount >= 8

  return [
    {
      name: 'Sensor & Data Integrity',
      genericName: 'Signal Validation',
      icon: <Activity size={12} />,
      status: cp1Pass ? 'pass' : cp1Score >= 45 ? 'warn' : 'block',
      score: cp1Score, threshold: 62,
      reasoning: cp1Pass
        ? `${deviceData.label} data quality validated — ${cp1Score}% integrity`
        : `Sensor degradation detected — ${100 - cp1Score}% noise above safe threshold`,
      detail: `Device: ${deviceData.label} | Noise level: ${(deviceData.noiseLevel * 100).toFixed(0)}%`,
    },
    {
      name: 'Clinical Probability',
      genericName: 'Probability Score',
      icon: <Brain size={12} />,
      status: cp2Pass ? 'pass' : cp2Score >= 50 ? 'warn' : 'block',
      score: cp2Score, threshold: Math.round(confThreshold * 100),
      reasoning: cp2Pass
        ? `AI diagnostic confidence ${cp2Score}% exceeds ${c.jurisdiction} threshold`
        : `Confidence ${cp2Score}% below ${c.jurisdiction} regulatory requirement (${Math.round(confThreshold * 100)}%)`,
      detail: `Decision type: ${decisionData.label} | Jurisdiction: ${c.jurisdiction}`,
    },
    {
      name: 'Patient Risk Stratification',
      genericName: 'Risk Exposure',
      icon: <AlertTriangle size={12} />,
      status: cp3Pass ? 'pass' : cp3Score >= 25 ? 'warn' : 'block',
      score: cp3Score, threshold: 35,
      reasoning: cp3Pass
        ? `Risk profile manageable — ${profileData.label} within safe parameters`
        : `Risk exposure ${adjustedRisk.toFixed(0)}% exceeds safe governance limit for ${profileData.label}`,
      detail: `Profile: ${profileData.label} | Risk multiplier: ${(profileData.riskBase * 100).toFixed(0)}%`,
    },
    {
      name: 'Clinical Signal Coherence',
      genericName: 'Signal Coherence',
      icon: <Zap size={12} />,
      status: coherence >= 60 ? 'pass' : coherence >= 45 ? 'warn' : 'block',
      score: coherence, threshold: 60,
      reasoning: coherence >= 60
        ? `Sensors, diagnostics, and clinical data are coherent`
        : `Multi-signal misalignment — sensor data and AI output diverge`,
      detail: `Diagnostic: ${c.diagnosticConfidence}% | Sensor: ${deviceData.sensorBase}%`,
    },
    {
      name: 'Patient Trajectory',
      genericName: 'Trend Persistence',
      icon: <TrendingUp size={12} />,
      status: cp5Pass ? 'pass' : trajectory >= 40 ? 'warn' : 'block',
      score: trajectory, threshold: 55,
      reasoning: cp5Pass
        ? `Positive patient trajectory sustained — treatment course stable`
        : `Adverse trajectory detected — risk of deterioration without intervention`,
      detail: `Profile trajectory for ${profileData.label}`,
    },
    {
      name: 'Comorbidity Resilience',
      genericName: 'Stress Resilience',
      icon: <Heart size={12} />,
      status: cp6Pass ? 'pass' : resilience >= 38 ? 'warn' : 'block',
      score: resilience, threshold: 52,
      reasoning: cp6Pass
        ? `Decision robust against comorbidity and edge-case amplification`
        : `Comorbidity burden may amplify risk beyond safe bounds`,
      detail: `Resilience score: ${resilience}% vs threshold: 52%`,
    },
    {
      name: 'Ethics & Care Plan Alignment',
      genericName: 'Logic Consistency',
      icon: <Shield size={12} />,
      status: c.ethicsFlag ? 'block' : !c.consentVerified ? 'block' : cp7Pass ? 'pass' : 'warn',
      score: cp7Score, threshold: 58,
      reasoning: c.ethicsFlag
        ? `Ethics review triggered — clinical board review required before proceed`
        : !c.consentVerified
        ? `BLOCKED: Informed consent not verified — ISO 14971 / GDPR Art.9`
        : cp7Pass
        ? `Care plan alignment confirmed — ethics and consent verified`
        : `Care plan alignment marginal — review recommended`,
      detail: `Consent: ${c.consentVerified ? 'Verified' : 'NOT VERIFIED'} | Ethics flag: ${c.ethicsFlag ? 'YES' : 'No'}`,
    },
    {
      name: 'Regulatory Compliance',
      genericName: 'Jurisdiction Compliance',
      icon: <Lock size={12} />,
      status: cp8Pass ? 'pass' : cp8Score >= 45 ? 'warn' : 'block',
      score: cp8Score, threshold: 60,
      reasoning: cp8Pass
        ? `Decision meets ${c.jurisdiction} SaMD/AI Act governance requirements`
        : `Confidence below ${c.jurisdiction} regulatory threshold — manual review required`,
      detail: `Regulatory framework: ${jxData.label}`,
    },
    {
      name: 'Cryptographic Receipt (PQC)',
      genericName: 'Receipt Integrity',
      icon: <Cpu size={12} />,
      status: 'pass',
      score: 97, threshold: 90,
      reasoning: `Dilithium-3 post-quantum signature generated — OMNIX-MED receipt issued`,
      detail: `Algorithm: CRYSTALS-Dilithium3 | Standard: NIST FIPS 204`,
    },
    {
      name: 'Audit Trail Completeness',
      genericName: 'Governance Audit',
      icon: <Monitor size={12} />,
      status: cp10Pass ? 'pass' : cp10Score >= 42 ? 'warn' : 'block',
      score: cp10Score, threshold: 55,
      reasoning: cp10Pass
        ? `Full audit trail captured — regulatory reporting ready`
        : `Audit trail incomplete — governance documentation gaps detected`,
      detail: `Audit composite: ${cp10Score}% vs threshold: 55%`,
    },
    {
      name: 'Exit Governance Gate',
      genericName: 'Final Validation',
      icon: <CheckCircle size={12} />,
      status: cp11Pass ? 'pass' : passingCount >= 6 ? 'warn' : 'block',
      score: cp11Score, threshold: 80,
      reasoning: cp11Pass
        ? `${passingCount}/10 checkpoints passed — clinical AI decision APPROVED`
        : `Only ${passingCount}/10 checkpoints passed — decision requires clinical review or BLOCKED`,
      detail: `Checkpoints passed: ${passingCount} / 10`,
    },
  ]
}

function statusCfg(status: CheckpointResult['status']) {
  return {
    pending: { bg: 'bg-white/[0.03]', border: 'border-white/[0.06]', dot: 'bg-white/20', text: 'text-white/30', label: 'PENDING' },
    evaluating: { bg: 'bg-blue-500/[0.06]', border: 'border-blue-500/20', dot: 'bg-blue-400 animate-pulse', text: 'text-blue-400', label: 'EVALUATING' },
    pass: { bg: 'bg-emerald-500/[0.06]', border: 'border-emerald-500/20', dot: 'bg-emerald-400', text: 'text-emerald-400', label: 'PASS' },
    warn: { bg: 'bg-amber-500/[0.06]', border: 'border-amber-500/20', dot: 'bg-amber-400', text: 'text-amber-400', label: 'HOLD' },
    block: { bg: 'bg-red-500/[0.06]', border: 'border-red-500/20', dot: 'bg-red-500', text: 'text-red-400', label: 'BLOCK' },
  }[status]
}

export default function MedicalGovernanceDemo() {
  const [clinicalCase, setClinicalCase] = useState<ClinicalCase>({
    decisionType: 'rehabilitation_guidance',
    deviceType: 'Wearable',
    patientProfile: 'rehabilitation',
    jurisdiction: 'UAE',
    diagnosticConfidence: 82,
    patientRisk: 35,
    consentVerified: true,
    ethicsFlag: false,
  })

  const [checkpoints, setCheckpoints] = useState<CheckpointResult[]>([])
  const [evaluating, setEvaluating] = useState(false)
  const [currentStep, setCurrentStep] = useState(-1)
  const [finalDecision, setFinalDecision] = useState<'APPROVED' | 'HOLD' | 'BLOCKED' | null>(null)
  const abortRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const { metrics: liveMetrics } = useLiveMetrics()

  const runSimulation = () => {
    if (abortRef.current) clearTimeout(abortRef.current)
    const results = evaluateMedicalCheckpoints(clinicalCase)
    setCheckpoints(results.map(r => ({ ...r, status: 'pending' })))
    setEvaluating(true)
    setCurrentStep(0)
    setFinalDecision(null)

    results.forEach((_, i) => {
      abortRef.current = setTimeout(() => {
        setCurrentStep(i)
        setCheckpoints(prev => prev.map((cp, idx) => {
          if (idx < i) return results[idx]
          if (idx === i) return { ...results[idx], status: 'evaluating' }
          return { ...cp, status: 'pending' }
        }))
        if (i === results.length - 1) {
          setTimeout(() => {
            setCheckpoints(results)
            const blocked = results.filter(r => r.status === 'block').length
            const warns = results.filter(r => r.status === 'warn').length
            setFinalDecision(blocked > 0 ? 'BLOCKED' : warns >= 3 ? 'HOLD' : 'APPROVED')
            setEvaluating(false)
            setCurrentStep(-1)
          }, 600)
        }
      }, i * 350 + 300)
    })
  }

  useEffect(() => {
    setCheckpoints(Array(11).fill(null).map((_, i) => ({
      name: `Checkpoint ${i + 1}`, genericName: '', icon: null,
      status: 'pending', score: 0, threshold: 0, reasoning: '', detail: '',
    })))
  }, [])

  const passCount = checkpoints.filter(c => c.status === 'pass').length
  const blockCount = checkpoints.filter(c => c.status === 'block').length

  return (
    <div className="min-h-screen bg-[#0a0b0f] text-white font-sans">
      {/* Header */}
      <div className="border-b border-white/[0.06] bg-[#0a0b0f]/95 sticky top-0 z-50 backdrop-blur">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/" className="flex items-center gap-2 text-white/40 hover:text-white/70 transition-colors text-sm">
              <Shield size={16} />
              <span>OMNIX</span>
            </Link>
            <span className="text-white/20">/</span>
            <div className="flex items-center gap-2">
              <Heart size={15} className="text-rose-400" />
              <span className="text-sm text-white/70">Medical AI Governance</span>
            </div>
          </div>
          <Link
            to="/medical"
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 hover:bg-rose-500/15 transition-all text-sm"
          >
            Live Dashboard <ArrowRight size={14} />
          </Link>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-10 space-y-10">

        {/* Hero */}
        <div className="text-center space-y-4 max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-rose-500/20 bg-rose-500/[0.06] text-rose-400 text-xs font-medium tracking-wide uppercase">
            <Heart size={11} /> OMNIX-MED · Medical AI Governance · AGL Vertical
          </div>
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-b from-white to-white/60 bg-clip-text text-transparent">
            Clinical AI Decision Governance
          </h1>
          <p className="text-white/45 text-base leading-relaxed">
            Same 11-checkpoint pipeline that governs trading, insurance, and robotics —
            now adapted for <span className="text-white/70">clinical AI decisions</span>.
            Post-quantum receipts (Dilithium-3) on every medical AI output.
          </p>
          <div className="flex items-center justify-center gap-6 pt-2">
            {[
              { icon: <Stethoscope size={13} />, label: 'FDA SaMD · EU MDR · DOH', color: 'text-rose-400' },
              { icon: <Lock size={13} />, label: 'CRYSTALS-Dilithium3 PQC', color: 'text-violet-400' },
              { icon: <Shield size={13} />, label: 'ISO 14971 · IEEE 7010', color: 'text-blue-400' },
            ].map((item, i) => (
              <div key={i} className={`flex items-center gap-1.5 text-xs ${item.color}`}>
                {item.icon} <span className="text-white/40">{item.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Live counter strip */}
        {liveMetrics && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: 'Evaluation Cycles', value: (liveMetrics.evaluation_cycles ?? 0).toLocaleString(), color: 'text-white' },
              { label: 'PQC Receipts Issued', value: (liveMetrics.pqc_signed_receipts ?? 0).toLocaleString(), color: 'text-emerald-400' },
              { label: 'Verticals Active', value: liveMetrics.verticals_demo ?? 7, color: 'text-violet-400' },
              { label: 'System Uptime (Days)', value: liveMetrics.system_uptime_days ?? '—', color: 'text-blue-400' },
            ].map((m, i) => (
              <div key={i} className="rounded-xl border border-white/[0.06] bg-white/[0.02] px-4 py-3 text-center">
                <div className={`text-lg font-bold ${m.color}`}>{m.value}</div>
                <div className="text-[10px] text-white/35 mt-0.5">{m.label}</div>
              </div>
            ))}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Controls */}
          <div className="lg:col-span-4 space-y-4">
            <div className="rounded-2xl border border-white/[0.07] bg-white/[0.025] p-6 space-y-5">
              <div className="flex items-center gap-2 mb-1">
                <Stethoscope size={15} className="text-rose-400" />
                <h2 className="text-sm font-semibold text-white/80">Clinical Case Parameters</h2>
              </div>

              <div className="space-y-1">
                <label className="text-[11px] text-white/40 uppercase tracking-wide">Decision Type</label>
                <select
                  value={clinicalCase.decisionType}
                  onChange={e => setClinicalCase(p => ({ ...p, decisionType: e.target.value }))}
                  className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 py-2 text-sm text-white/80 focus:outline-none focus:border-rose-500/40"
                >
                  {DECISION_TYPES.map(d => (
                    <option key={d.value} value={d.value}>{d.icon} {d.label}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[11px] text-white/40 uppercase tracking-wide">Device Type</label>
                <select
                  value={clinicalCase.deviceType}
                  onChange={e => setClinicalCase(p => ({ ...p, deviceType: e.target.value }))}
                  className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 py-2 text-sm text-white/80 focus:outline-none focus:border-rose-500/40"
                >
                  {DEVICE_TYPES.map(d => (
                    <option key={d.value} value={d.value}>{d.label}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[11px] text-white/40 uppercase tracking-wide">Patient Profile</label>
                <select
                  value={clinicalCase.patientProfile}
                  onChange={e => setClinicalCase(p => ({ ...p, patientProfile: e.target.value }))}
                  className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 py-2 text-sm text-white/80 focus:outline-none focus:border-rose-500/40"
                >
                  {PATIENT_PROFILES.map(p => (
                    <option key={p.value} value={p.value}>{p.label}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[11px] text-white/40 uppercase tracking-wide">Jurisdiction</label>
                <select
                  value={clinicalCase.jurisdiction}
                  onChange={e => setClinicalCase(p => ({ ...p, jurisdiction: e.target.value }))}
                  className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 py-2 text-sm text-white/80 focus:outline-none focus:border-rose-500/40"
                >
                  {JURISDICTIONS.map(j => (
                    <option key={j.value} value={j.value}>{j.label}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-[11px]">
                  <span className="text-white/40 uppercase tracking-wide">Diagnostic Confidence</span>
                  <span className="text-white/70 font-medium">{clinicalCase.diagnosticConfidence}%</span>
                </div>
                <input
                  type="range" min={20} max={99} value={clinicalCase.diagnosticConfidence}
                  onChange={e => setClinicalCase(p => ({ ...p, diagnosticConfidence: +e.target.value }))}
                  className="w-full accent-rose-500 h-1.5 rounded-full cursor-pointer"
                />
                <div className="flex justify-between text-[9px] text-white/25">
                  <span>20% (uncertain)</span><span>99% (high confidence)</span>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-[11px]">
                  <span className="text-white/40 uppercase tracking-wide">Patient Risk Index</span>
                  <span className="text-white/70 font-medium">{clinicalCase.patientRisk}%</span>
                </div>
                <input
                  type="range" min={5} max={95} value={clinicalCase.patientRisk}
                  onChange={e => setClinicalCase(p => ({ ...p, patientRisk: +e.target.value }))}
                  className="w-full accent-rose-500 h-1.5 rounded-full cursor-pointer"
                />
                <div className="flex justify-between text-[9px] text-white/25">
                  <span>5% (low risk)</span><span>95% (critical)</span>
                </div>
              </div>

              {/* Flags */}
              <div className="space-y-3 pt-2 border-t border-white/[0.05]">
                <p className="text-[11px] text-white/30 uppercase tracking-wide">Compliance Flags</p>
                {[
                  { key: 'consentVerified', label: 'Informed Consent Verified', color: 'emerald', warning: 'Hard block if unchecked' },
                  { key: 'ethicsFlag', label: 'Ethics Review Triggered', color: 'amber', warning: 'Forces clinical board review' },
                ].map(({ key, label, color, warning }) => (
                  <label key={key} className="flex items-start gap-3 cursor-pointer group">
                    <div className="relative mt-0.5">
                      <input
                        type="checkbox"
                        checked={(clinicalCase as any)[key] as boolean}
                        onChange={e => setClinicalCase(p => ({ ...p, [key]: e.target.checked }))}
                        className="sr-only"
                      />
                      <div className={`w-4 h-4 rounded border transition-all ${(clinicalCase as any)[key]
                        ? `bg-${color}-500/30 border-${color}-400`
                        : 'bg-white/[0.04] border-white/20'}`}>
                        {(clinicalCase as any)[key] && (
                          <CheckCircle size={14} className={`text-${color}-400`} />
                        )}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-white/65">{label}</div>
                      <div className="text-[10px] text-white/30">{warning}</div>
                    </div>
                  </label>
                ))}
              </div>

              <button
                onClick={runSimulation}
                disabled={evaluating}
                className="w-full py-3 rounded-xl bg-rose-500/15 border border-rose-500/25 text-rose-400 hover:bg-rose-500/20 hover:border-rose-500/40 transition-all text-sm font-semibold disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {evaluating ? (
                  <><Activity size={14} className="animate-pulse" /> Evaluating Clinical Case...</>
                ) : (
                  <><Shield size={14} /> Run Governance Pipeline</>
                )}
              </button>
            </div>

            {/* Vertical compliance tags */}
            <div className="rounded-xl border border-white/[0.07] bg-white/[0.02] p-4 space-y-2">
              <p className="text-[10px] text-white/30 uppercase tracking-wide mb-3">Regulatory Coverage</p>
              {[
                { tag: 'FDA 21 CFR Part 820', scope: 'SaMD quality system' },
                { tag: 'EU AI Act', scope: 'High-risk AI system' },
                { tag: 'ISO 14971:2019', scope: 'Medical device risk mgmt' },
                { tag: 'IEEE 7010', scope: 'AI wellbeing ethics standard' },
                { tag: 'UAE DOH AI Framework', scope: 'Regional health AI' },
                { tag: 'GDPR Art.9', scope: 'Health data special category' },
              ].map(({ tag, scope }) => (
                <div key={tag} className="flex items-center justify-between">
                  <span className="text-[10px] text-rose-400/80 font-medium">{tag}</span>
                  <span className="text-[10px] text-white/25">{scope}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Checkpoint Pipeline */}
          <div className="lg:col-span-8 space-y-4">
            {/* Decision result banner */}
            {finalDecision && (
              <div className={`rounded-2xl border p-5 flex items-center justify-between ${
                finalDecision === 'APPROVED' ? 'border-emerald-500/25 bg-emerald-500/[0.06]' :
                finalDecision === 'BLOCKED' ? 'border-red-500/25 bg-red-500/[0.06]' :
                'border-amber-500/25 bg-amber-500/[0.06]'
              }`}>
                <div className="flex items-center gap-4">
                  {finalDecision === 'APPROVED' && <CheckCircle size={28} className="text-emerald-400" />}
                  {finalDecision === 'BLOCKED' && <XCircle size={28} className="text-red-400" />}
                  {finalDecision === 'HOLD' && <Clock size={28} className="text-amber-400" />}
                  <div>
                    <div className={`text-xl font-bold ${
                      finalDecision === 'APPROVED' ? 'text-emerald-400' :
                      finalDecision === 'BLOCKED' ? 'text-red-400' : 'text-amber-400'
                    }`}>{finalDecision}</div>
                    <div className="text-xs text-white/40 mt-0.5">
                      {passCount} checkpoints passed · {blockCount} blocked · PQC receipt issued
                    </div>
                  </div>
                </div>
                <div className="text-right hidden sm:block">
                  <div className="text-[10px] text-white/30">OMNIX-MED Receipt</div>
                  <div className="text-[10px] font-mono text-white/40 mt-0.5">
                    Dilithium-3 · {new Date().toISOString().slice(0, 19)}Z
                  </div>
                </div>
              </div>
            )}

            {/* Checkpoint list */}
            <div className="rounded-2xl border border-white/[0.07] bg-white/[0.02] overflow-hidden">
              <div className="px-5 py-4 border-b border-white/[0.05] flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Shield size={14} className="text-white/40" />
                  <span className="text-sm font-semibold text-white/70">11-Checkpoint Governance Pipeline</span>
                </div>
                <span className="text-[10px] text-white/30 font-mono">OMNIX-MED · v6.6.0</span>
              </div>
              <div className="divide-y divide-white/[0.04]">
                {checkpoints.map((cp, i) => {
                  const cfg = statusCfg(cp.status)
                  const isActive = currentStep === i
                  return (
                    <div
                      key={i}
                      className={`px-5 py-3.5 transition-all duration-500 ${cfg.bg} ${isActive ? 'ring-1 ring-inset ring-blue-500/20' : ''}`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex items-center gap-2 w-6 shrink-0">
                          <div className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-1.5">
                              <span className="text-[10px] text-white/25 font-mono">CP-{String(i + 1).padStart(2, '0')}</span>
                              <span className="text-xs font-medium text-white/70 truncate">{cp.name || `Checkpoint ${i + 1}`}</span>
                            </div>
                            <div className="flex items-center gap-2 shrink-0">
                              {cp.status !== 'pending' && cp.score > 0 && (
                                <span className="text-[10px] font-mono text-white/40">{cp.score}<span className="text-white/20">/100</span></span>
                              )}
                              <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full border ${cfg.border} ${cfg.text} tracking-widest`}>
                                {cfg.label}
                              </span>
                            </div>
                          </div>
                          {cp.reasoning && cp.status !== 'pending' && (
                            <p className="text-[10px] text-white/35 mt-0.5 leading-relaxed">{cp.reasoning}</p>
                          )}
                          {cp.detail && cp.status !== 'pending' && (
                            <p className="text-[9px] text-white/20 mt-0.5 font-mono">{cp.detail}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* CTA */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Link to="/medical" className="rounded-xl border border-rose-500/20 bg-rose-500/[0.05] p-4 hover:border-rose-500/35 transition-all group">
                <div className="flex items-center justify-between mb-2">
                  <Heart size={16} className="text-rose-400" />
                  <ArrowRight size={14} className="text-white/25 group-hover:text-rose-400 transition-colors" />
                </div>
                <div className="text-sm font-semibold text-white/80">Live Medical Dashboard</div>
                <div className="text-[11px] text-white/35 mt-0.5">Real-time 24/7 simulation data</div>
              </Link>
              <Link to="/governance-demo" className="rounded-xl border border-white/[0.07] bg-white/[0.02] p-4 hover:border-white/[0.12] transition-all group">
                <div className="flex items-center justify-between mb-2">
                  <Users size={16} className="text-blue-400" />
                  <ArrowRight size={14} className="text-white/25 group-hover:text-blue-400 transition-colors" />
                </div>
                <div className="text-sm font-semibold text-white/80">Trading Governance</div>
                <div className="text-[11px] text-white/35 mt-0.5">Same engine, different domain</div>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
