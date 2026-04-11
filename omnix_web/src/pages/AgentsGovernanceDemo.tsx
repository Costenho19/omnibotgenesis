import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield, CheckCircle, XCircle, Clock, Activity, Brain,
  AlertTriangle, Zap, ArrowRight, Bot, Database, Globe,
  Lock, TrendingUp, Users, Server, Code
} from 'lucide-react'
import { useLiveMetrics } from '../hooks/useLiveMetrics'

interface CheckpointResult {
  name: string
  icon: React.ReactNode
  status: 'pending' | 'evaluating' | 'pass' | 'warn' | 'block'
  score: number
  threshold: number
  reasoning: string
  detail: string
}

interface AgentCase {
  decisionType: string
  agentType: string
  environment: string
  reversibility: string
  taskComplexity: number
  scopeBlastRadius: number
  contextCompleteness: number
  goalAlignment: number
  safetyFlag: boolean
  humanApprovalRequired: boolean
  humanApproved: boolean
  crossBoundary: boolean
  dataSensitivity: string
}

const DECISION_TYPES = [
  { value: 'task_delegation', label: 'Task Delegation', icon: '🤖', baseScore: 0.68 },
  { value: 'data_access', label: 'Data Access Request', icon: '🗄️', baseScore: 0.72 },
  { value: 'external_api_call', label: 'External API Call', icon: '🌐', baseScore: 0.75 },
  { value: 'resource_allocation', label: 'Resource Allocation', icon: '⚡', baseScore: 0.78 },
  { value: 'state_modification', label: 'State Modification', icon: '✏️', baseScore: 0.82 },
]

const AGENT_TYPES = [
  { value: 'Financial_Agent', label: 'Financial Agent', riskBase: 1.30 },
  { value: 'Enterprise_Agent', label: 'Enterprise Agent', riskBase: 1.15 },
  { value: 'Logistics_Agent', label: 'Logistics Agent', riskBase: 1.10 },
  { value: 'Infrastructure_Agent', label: 'Infrastructure Agent', riskBase: 1.25 },
  { value: 'Research_Agent', label: 'Research Agent', riskBase: 0.90 },
]

const ENVIRONMENTS = [
  { value: 'production', label: 'Production', strictness: 1.45 },
  { value: 'staging', label: 'Staging', strictness: 1.15 },
  { value: 'development', label: 'Development', strictness: 0.90 },
  { value: 'sandbox', label: 'Sandbox', strictness: 0.75 },
]

const REVERSIBILITIES = [
  { value: 'fully_reversible', label: 'Fully Reversible', factor: 0.80 },
  { value: 'partially_reversible', label: 'Partially Reversible', factor: 1.10 },
  { value: 'irreversible', label: 'Irreversible', factor: 1.45 },
  { value: 'unknown', label: 'Unknown Reversibility', factor: 1.30 },
]

const DATA_SENSITIVITIES = [
  { value: 'low', label: 'Low Sensitivity', penalty: 0 },
  { value: 'medium', label: 'Medium Sensitivity', penalty: 8 },
  { value: 'high', label: 'High Sensitivity', penalty: 18 },
  { value: 'pii', label: 'PII (Personal Data)', penalty: 28 },
  { value: 'phi', label: 'PHI (Health Data)', penalty: 35 },
]

function evaluateAgentCheckpoints(c: AgentCase): CheckpointResult[] {
  const decisionData = DECISION_TYPES.find(d => d.value === c.decisionType) || DECISION_TYPES[0]
  const agentData = AGENT_TYPES.find(a => a.value === c.agentType) || AGENT_TYPES[0]
  const envData = ENVIRONMENTS.find(e => e.value === c.environment) || ENVIRONMENTS[0]
  const revData = REVERSIBILITIES.find(r => r.value === c.reversibility) || REVERSIBILITIES[0]
  const senData = DATA_SENSITIVITIES.find(s => s.value === c.dataSensitivity) || DATA_SENSITIVITIES[0]

  const complexity = c.taskComplexity / 100
  const blast = c.scopeBlastRadius / 100
  const context = c.contextCompleteness / 100
  const goal = c.goalAlignment / 100

  // CP-1: Input Validation
  const cp1Score = Math.round(context * 100 * (1 - complexity * 0.2))
  const cp1Pass = cp1Score >= 60

  // CP-2: Task Viability Probability
  const viability = ((1 - complexity) * 0.45 + (1 - blast * 0.5) * 0.30 + context * 0.25) * 100
  const cp2Score = Math.round(viability / envData.strictness)
  const cp2Pass = cp2Score >= Math.round(decisionData.baseScore * 100)

  // CP-3: Blast Radius / Risk Exposure
  const adjustedRisk = blast * revData.factor * agentData.riskBase * 100
  const cp3Score = Math.round(100 - adjustedRisk)
  const cp3Pass = cp3Score >= 32

  // CP-4: Context-Task Coherence
  const coherence = Math.round((context * 0.40 + goal * 0.35 + (1 - blast * 0.5) * 0.15 - blast * 0.10) * 100)
  const cp4Pass = coherence >= 58

  // CP-5: Goal Trajectory
  const trajectory = Math.round((goal * 0.55 + context * 0.30 + (1 - complexity) * 0.15) * 100)
  const cp5Pass = trajectory >= 52

  // CP-6: Failure Mode Resilience (fallback assumed from context)
  const resilience = Math.round((context * 0.55 + (1 - blast) * 0.30 + (1 - complexity * 0.5) * 0.15) * 100)
  const cp6Pass = resilience >= 52

  // CP-7: Authorization & Safety
  const safetyPenalty = c.safetyFlag ? 50 : 0
  const authPenalty = (c.humanApprovalRequired && !c.humanApproved) ? 45 : 0
  const boundaryPenalty = c.crossBoundary ? 20 : 0
  const senPenalty = senData.penalty * 0.3
  const cp7Score = Math.max(0, Math.round((goal * 0.45 + context * 0.25) * 100 - safetyPenalty - authPenalty - boundaryPenalty - senPenalty))
  const cp7Pass = cp7Score >= 58 && !c.safetyFlag && !(c.humanApprovalRequired && !c.humanApproved)

  // CP-8: Regulatory / Environment Compliance
  const cp8Score = Math.round(viability / envData.strictness)
  const cp8Pass = cp8Score >= 55

  // CP-9: PQC Receipt (always passes in demo)

  // CP-10: Audit Trail
  const cp10Score = Math.round((cp1Score + coherence + cp7Score) / 3)
  const cp10Pass = cp10Score >= 52

  // CP-11: Exit Gate
  const passing = [cp1Pass, cp2Pass, cp3Pass, cp4Pass, cp5Pass, cp6Pass, cp7Pass, cp8Pass, true, cp10Pass].filter(Boolean).length
  const cp11Score = passing * 10

  return [
    {
      name: 'Payload & Context Validation',
      icon: <Code size={12} />,
      status: cp1Pass ? 'pass' : cp1Score >= 42 ? 'warn' : 'block',
      score: cp1Score, threshold: 60,
      reasoning: cp1Pass
        ? `Agent context complete and validated — ${cp1Score}% integrity`
        : `Context incomplete — agent may be operating with insufficient instruction state`,
      detail: `Context completeness: ${c.contextCompleteness}% | Complexity: ${c.taskComplexity}%`,
    },
    {
      name: 'Task Viability Probability',
      icon: <Brain size={12} />,
      status: cp2Pass ? 'pass' : cp2Score >= 45 ? 'warn' : 'block',
      score: cp2Score, threshold: Math.round(decisionData.baseScore * 100),
      reasoning: cp2Pass
        ? `Task viability ${cp2Score}% meets ${c.environment} threshold`
        : `Task viability too low for ${c.environment} — complexity/blast radius too high`,
      detail: `Decision: ${decisionData.label} | Environment: ${c.environment}`,
    },
    {
      name: 'Action Blast Radius',
      icon: <AlertTriangle size={12} />,
      status: cp3Pass ? 'pass' : cp3Score >= 20 ? 'warn' : 'block',
      score: Math.max(0, cp3Score), threshold: 32,
      reasoning: cp3Pass
        ? `Blast radius within safe bounds — impact scope contained`
        : `Action blast radius ${(adjustedRisk).toFixed(0)}% exceeds safe governance limit`,
      detail: `Reversibility: ${revData.label} | Agent risk factor: ${agentData.riskBase}×`,
    },
    {
      name: 'Context-Task Coherence',
      icon: <Zap size={12} />,
      status: coherence >= 58 ? 'pass' : coherence >= 40 ? 'warn' : 'block',
      score: Math.max(0, coherence), threshold: 58,
      reasoning: coherence >= 58
        ? `Task, context, and goal state are coherent and aligned`
        : `Misalignment between task parameters, context, and stated goal`,
      detail: `Context: ${c.contextCompleteness}% | Goal alignment: ${c.goalAlignment}%`,
    },
    {
      name: 'Goal Trajectory Stability',
      icon: <TrendingUp size={12} />,
      status: cp5Pass ? 'pass' : trajectory >= 38 ? 'warn' : 'block',
      score: trajectory, threshold: 52,
      reasoning: cp5Pass
        ? `Agent goal trajectory stable — converging toward objective`
        : `Goal trajectory diverging — risk of task drift or unintended state`,
      detail: `Goal alignment: ${c.goalAlignment}% | Context: ${c.contextCompleteness}%`,
    },
    {
      name: 'Failure Mode Resilience',
      icon: <Server size={12} />,
      status: cp6Pass ? 'pass' : resilience >= 38 ? 'warn' : 'block',
      score: resilience, threshold: 52,
      reasoning: cp6Pass
        ? `Fallback paths adequate — agent can recover from failure modes`
        : `Insufficient fallback coverage for dependency failures or edge cases`,
      detail: `Blast radius: ${c.scopeBlastRadius}% | Complexity: ${c.taskComplexity}%`,
    },
    {
      name: 'Authorization & Safety Gate',
      icon: <Shield size={12} />,
      status: c.safetyFlag ? 'block' : (c.humanApprovalRequired && !c.humanApproved) ? 'block' : cp7Pass ? 'pass' : 'warn',
      score: cp7Score, threshold: 58,
      reasoning: c.safetyFlag
        ? `HARD BLOCK: Safety-critical flag — human review mandatory before any execution`
        : (c.humanApprovalRequired && !c.humanApproved)
        ? `HARD BLOCK: Human authorization required but not granted`
        : cp7Pass
        ? `Authorization chain verified — principal hierarchy respected`
        : `Authorization marginal — review principal scope before execution`,
      detail: `Safety flag: ${c.safetyFlag ? 'YES' : 'No'} | Approval: ${c.humanApprovalRequired ? (c.humanApproved ? 'Granted' : 'NOT GRANTED') : 'Not required'}`,
    },
    {
      name: 'Environment Compliance',
      icon: <Globe size={12} />,
      status: cp8Pass ? 'pass' : cp8Score >= 42 ? 'warn' : 'block',
      score: cp8Score, threshold: 55,
      reasoning: cp8Pass
        ? `Action meets ${c.environment} environment governance requirements`
        : `Task parameters do not satisfy ${c.environment} strictness threshold`,
      detail: `Environment strictness: ${envData.strictness}× | Data: ${senData.label}`,
    },
    {
      name: 'Cryptographic Receipt (PQC)',
      icon: <Lock size={12} />,
      status: 'pass',
      score: 97, threshold: 90,
      reasoning: `CRYSTALS-Dilithium3 receipt generated — OMNIX-AGT receipt issued`,
      detail: `Algorithm: CRYSTALS-Dilithium3 | Standard: NIST FIPS 204`,
    },
    {
      name: 'Audit Trail Completeness',
      icon: <Database size={12} />,
      status: cp10Pass ? 'pass' : cp10Score >= 40 ? 'warn' : 'block',
      score: cp10Score, threshold: 52,
      reasoning: cp10Pass
        ? `Complete audit trail captured — principal attribution traceable`
        : `Audit trail gaps — agent action may not be fully attributable`,
      detail: `Audit composite: ${cp10Score}% vs threshold: 52%`,
    },
    {
      name: 'Exit Governance Gate',
      icon: <CheckCircle size={12} />,
      status: passing >= 9 ? 'pass' : passing >= 7 ? 'warn' : 'block',
      score: cp11Score, threshold: 80,
      reasoning: passing >= 9
        ? `${passing}/10 checkpoints passed — agent action APPROVED`
        : `Only ${passing}/10 checkpoints passed — action requires review or BLOCKED`,
      detail: `Checkpoints passed: ${passing} / 10`,
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

export default function AgentsGovernanceDemo() {
  const [agentCase, setAgentCase] = useState<AgentCase>({
    decisionType: 'task_delegation',
    agentType: 'Enterprise_Agent',
    environment: 'production',
    reversibility: 'partially_reversible',
    taskComplexity: 45,
    scopeBlastRadius: 35,
    contextCompleteness: 82,
    goalAlignment: 80,
    safetyFlag: false,
    humanApprovalRequired: false,
    humanApproved: false,
    crossBoundary: false,
    dataSensitivity: 'low',
  })

  const [checkpoints, setCheckpoints] = useState<CheckpointResult[]>([])
  const [evaluating, setEvaluating] = useState(false)
  const [currentStep, setCurrentStep] = useState(-1)
  const [finalDecision, setFinalDecision] = useState<'APPROVED' | 'HOLD' | 'BLOCKED' | null>(null)
  const abortRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const { metrics: liveMetrics } = useLiveMetrics()

  const runSimulation = () => {
    if (abortRef.current) clearTimeout(abortRef.current)
    const results = evaluateAgentCheckpoints(agentCase)
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
      }, i * 320 + 200)
    })
  }

  useEffect(() => {
    setCheckpoints(Array(11).fill(null).map((_, i) => ({
      name: `Checkpoint ${i + 1}`, icon: null,
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
              <Shield size={16} /><span>OMNIX</span>
            </Link>
            <span className="text-white/20">/</span>
            <div className="flex items-center gap-2">
              <Bot size={15} className="text-violet-400" />
              <span className="text-sm text-white/70">Autonomous Agent Governance</span>
            </div>
          </div>
          <Link
            to="/agents"
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-violet-500/10 border border-violet-500/20 text-violet-400 hover:bg-violet-500/15 transition-all text-sm"
          >
            Live Dashboard <ArrowRight size={14} />
          </Link>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-10 space-y-10">
        {/* Hero */}
        <div className="text-center space-y-4 max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-violet-500/20 bg-violet-500/[0.06] text-violet-400 text-xs font-medium tracking-wide uppercase">
            <Bot size={11} /> OMNIX-AGT · Autonomous Agent Governance · AGL Vertical
          </div>
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-b from-white to-white/60 bg-clip-text text-transparent">
            Autonomous Agent Decision Governance
          </h1>
          <p className="text-white/45 text-base leading-relaxed">
            Same 11-checkpoint pipeline — now governing <span className="text-white/70">AI agents</span> executing tasks
            without real-time human intervention. From financial agents to infrastructure bots.
            Post-quantum receipts (Dilithium-3) on every agent action.
          </p>
          <div className="flex items-center justify-center gap-6 pt-2">
            {[
              { icon: <Bot size={13} />, label: 'Principal Hierarchy Enforcement', color: 'text-violet-400' },
              { icon: <Lock size={13} />, label: 'CRYSTALS-Dilithium3 PQC', color: 'text-rose-400' },
              { icon: <Shield size={13} />, label: 'EU AI Act · NIST AI RMF', color: 'text-blue-400' },
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
              { label: 'Verticals Live', value: liveMetrics.verticals_demo ?? 7, color: 'text-violet-400' },
              { label: 'Uptime (Days)', value: liveMetrics.system_uptime_days ?? '—', color: 'text-blue-400' },
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
                <Bot size={15} className="text-violet-400" />
                <h2 className="text-sm font-semibold text-white/80">Agent Decision Parameters</h2>
              </div>

              {[
                { label: 'Decision Type', key: 'decisionType', options: DECISION_TYPES, valKey: 'value', labelKey: 'label' },
                { label: 'Agent Type', key: 'agentType', options: AGENT_TYPES, valKey: 'value', labelKey: 'label' },
                { label: 'Environment', key: 'environment', options: ENVIRONMENTS, valKey: 'value', labelKey: 'label' },
                { label: 'Reversibility', key: 'reversibility', options: REVERSIBILITIES, valKey: 'value', labelKey: 'label' },
                { label: 'Data Sensitivity', key: 'dataSensitivity', options: DATA_SENSITIVITIES, valKey: 'value', labelKey: 'label' },
              ].map(({ label, key, options, valKey, labelKey }) => (
                <div key={key} className="space-y-1">
                  <label className="text-[11px] text-white/40 uppercase tracking-wide">{label}</label>
                  <select
                    value={(agentCase as any)[key]}
                    onChange={e => setAgentCase(p => ({ ...p, [key]: e.target.value }))}
                    className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 py-2 text-sm text-white/80 focus:outline-none focus:border-violet-500/40"
                  >
                    {(options as any[]).map((o: any) => (
                      <option key={o[valKey]} value={o[valKey]}>{o[labelKey]}</option>
                    ))}
                  </select>
                </div>
              ))}

              {[
                { label: 'Task Complexity', key: 'taskComplexity', min: 5, max: 95, low: 'Low complexity', high: 'High complexity' },
                { label: 'Scope / Blast Radius', key: 'scopeBlastRadius', min: 5, max: 95, low: 'Contained scope', high: 'Broad impact' },
                { label: 'Context Completeness', key: 'contextCompleteness', min: 20, max: 99, low: 'Incomplete', high: 'Full context' },
                { label: 'Goal Alignment', key: 'goalAlignment', min: 20, max: 99, low: 'Misaligned', high: 'Fully aligned' },
              ].map(({ label, key, min, max, low, high }) => (
                <div key={key} className="space-y-2">
                  <div className="flex justify-between text-[11px]">
                    <span className="text-white/40 uppercase tracking-wide">{label}</span>
                    <span className="text-white/70 font-medium">{(agentCase as any)[key]}%</span>
                  </div>
                  <input
                    type="range" min={min} max={max} value={(agentCase as any)[key]}
                    onChange={e => setAgentCase(p => ({ ...p, [key]: +e.target.value }))}
                    className="w-full accent-violet-500 h-1.5 rounded-full cursor-pointer"
                  />
                  <div className="flex justify-between text-[9px] text-white/25">
                    <span>{low}</span><span>{high}</span>
                  </div>
                </div>
              ))}

              {/* Flags */}
              <div className="space-y-3 pt-2 border-t border-white/[0.05]">
                <p className="text-[11px] text-white/30 uppercase tracking-wide">Safety & Authorization</p>
                {[
                  { key: 'safetyFlag', label: 'Safety-Critical Flag', color: 'red', warning: 'Hard block — human review mandatory' },
                  { key: 'humanApprovalRequired', label: 'Human Approval Required', color: 'amber', warning: 'Must also toggle Approved below' },
                  { key: 'humanApproved', label: 'Human Approved', color: 'emerald', warning: 'Only applies when approval required' },
                  { key: 'crossBoundary', label: 'Cross Trust Boundary', color: 'amber', warning: 'Increases blast radius' },
                ].map(({ key, label, color, warning }) => (
                  <label key={key} className="flex items-start gap-3 cursor-pointer">
                    <div className="relative mt-0.5">
                      <input type="checkbox" checked={(agentCase as any)[key]} onChange={e => setAgentCase(p => ({ ...p, [key]: e.target.checked }))} className="sr-only" />
                      <div className={`w-4 h-4 rounded border transition-all ${(agentCase as any)[key] ? `bg-${color}-500/30 border-${color}-400` : 'bg-white/[0.04] border-white/20'}`}>
                        {(agentCase as any)[key] && <CheckCircle size={14} className={`text-${color}-400`} />}
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
                className="w-full py-3 rounded-xl bg-violet-500/15 border border-violet-500/25 text-violet-400 hover:bg-violet-500/20 hover:border-violet-500/40 transition-all text-sm font-semibold disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {evaluating ? (
                  <><Activity size={14} className="animate-pulse" /> Evaluating Agent Decision...</>
                ) : (
                  <><Shield size={14} /> Run Governance Pipeline</>
                )}
              </button>
            </div>

            <div className="rounded-xl border border-white/[0.07] bg-white/[0.02] p-4 space-y-2">
              <p className="text-[10px] text-white/30 uppercase tracking-wide mb-3">Use Case Coverage</p>
              {[
                { tag: 'Financial Agents', scope: 'Trade execution, payment routing' },
                { tag: 'Enterprise Agents', scope: 'Workflow automation, data ops' },
                { tag: 'Logistics Agents', scope: 'Supply chain, fleet routing' },
                { tag: 'Infrastructure Agents', scope: 'DevOps, cloud provisioning' },
                { tag: 'Research Agents', scope: 'Data collection, analysis' },
                { tag: 'Cross-Border Payments', scope: 'Multi-jurisdiction compliance' },
              ].map(({ tag, scope }) => (
                <div key={tag} className="flex items-center justify-between">
                  <span className="text-[10px] text-violet-400/80 font-medium">{tag}</span>
                  <span className="text-[10px] text-white/25">{scope}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Checkpoint Pipeline */}
          <div className="lg:col-span-8 space-y-4">
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
                    <div className={`text-xl font-bold ${finalDecision === 'APPROVED' ? 'text-emerald-400' : finalDecision === 'BLOCKED' ? 'text-red-400' : 'text-amber-400'}`}>{finalDecision}</div>
                    <div className="text-xs text-white/40 mt-0.5">{passCount} passed · {blockCount} blocked · OMNIX-AGT receipt issued</div>
                  </div>
                </div>
                <div className="text-right hidden sm:block">
                  <div className="text-[10px] text-white/30">OMNIX-AGT Receipt</div>
                  <div className="text-[10px] font-mono text-white/40 mt-0.5">Dilithium-3 · {new Date().toISOString().slice(0, 19)}Z</div>
                </div>
              </div>
            )}

            <div className="rounded-2xl border border-white/[0.07] bg-white/[0.02] overflow-hidden">
              <div className="px-5 py-4 border-b border-white/[0.05] flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Shield size={14} className="text-white/40" />
                  <span className="text-sm font-semibold text-white/70">11-Checkpoint Agent Governance Pipeline</span>
                </div>
                <span className="text-[10px] text-white/30 font-mono">OMNIX-AGT · v6.6.0</span>
              </div>
              <div className="divide-y divide-white/[0.04]">
                {checkpoints.map((cp, i) => {
                  const cfg = statusCfg(cp.status)
                  const isActive = currentStep === i
                  return (
                    <div key={i} className={`px-5 py-3.5 transition-all duration-500 ${cfg.bg} ${isActive ? 'ring-1 ring-inset ring-blue-500/20' : ''}`}>
                      <div className="flex items-center gap-3">
                        <div className="w-6 shrink-0">
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
                              <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full border ${cfg.border} ${cfg.text} tracking-widest`}>{cfg.label}</span>
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

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Link to="/agents" className="rounded-xl border border-violet-500/20 bg-violet-500/[0.05] p-4 hover:border-violet-500/35 transition-all group">
                <div className="flex items-center justify-between mb-2">
                  <Bot size={16} className="text-violet-400" />
                  <ArrowRight size={14} className="text-white/25 group-hover:text-violet-400 transition-colors" />
                </div>
                <div className="text-sm font-semibold text-white/80">Live Agents Dashboard</div>
                <div className="text-[11px] text-white/35 mt-0.5">Real-time 24/7 simulation data</div>
              </Link>
              <Link to="/governance-demo-medical" className="rounded-xl border border-white/[0.07] bg-white/[0.02] p-4 hover:border-white/[0.12] transition-all group">
                <div className="flex items-center justify-between mb-2">
                  <Users size={16} className="text-rose-400" />
                  <ArrowRight size={14} className="text-white/25 group-hover:text-rose-400 transition-colors" />
                </div>
                <div className="text-sm font-semibold text-white/80">Medical AI Governance</div>
                <div className="text-[11px] text-white/35 mt-0.5">Same engine, clinical domain</div>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
