import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield, ArrowRight, AlertTriangle, CheckCircle, XCircle,
  Clock, TrendingUp, BarChart3, Activity, Layers, Target,
  Brain, Lock, Globe
} from 'lucide-react'

const SRG_VIOLET = '#8B5CF6'
const SRG_LIGHT  = '#A78BFA'

interface CheckpointResult {
  name:        string
  genericName: string
  icon:        React.ReactNode
  status:      'pending' | 'evaluating' | 'pass' | 'warn' | 'block'
  score:       number
  threshold:   number
  reasoning:   string
  detail:      string
}

interface ReserveScenario {
  decisionType:   string
  reserveAsset:   string
  jurisdiction:   string
  pegDeviation:   number
  reserveCoverage: number
  liquidRatio:    number
  cryptoExposure: number
  redemptionSize: number
}

const DECISION_TYPES = [
  { value: 'reserve_rebalancing',   label: 'Reserve Rebalancing',    risk: 0.15, emoji: '⚖️' },
  { value: 'redemption_processing', label: 'Redemption Processing',  risk: 0.20, emoji: '💸' },
  { value: 'collateral_adjustment', label: 'Collateral Adjustment',  risk: 0.25, emoji: '🔧' },
  { value: 'peg_defense',           label: 'Peg Defense Intervention',risk: 0.40, emoji: '🛡️' },
  { value: 'yield_optimization',    label: 'Yield Optimization',     risk: 0.30, emoji: '📈' },
]

const RESERVE_ASSETS = [
  { value: 'US_Treasury_Bills',   label: 'US Treasury Bills (T-Bills)',    riskScore: 2,   liquid: true,  emoji: '🏛️' },
  { value: 'Repo_Agreements',     label: 'Repo Agreements (Overnight)',    riskScore: 5,   liquid: true,  emoji: '🔄' },
  { value: 'Money_Market_Funds',  label: 'Money Market Funds (Regulated)', riskScore: 8,   liquid: true,  emoji: '💰' },
  { value: 'US_Treasury_Notes',   label: 'US Treasury Notes (2–10yr)',     riskScore: 10,  liquid: true,  emoji: '📋' },
  { value: 'USDC',                label: 'USDC (Circle — Digital Dollar)', riskScore: 12,  liquid: true,  emoji: '💵' },
  { value: 'Commercial_Paper',    label: 'Commercial Paper (A-1/P-1)',     riskScore: 28,  liquid: false, emoji: '📄' },
  { value: 'ETH_Staked',          label: 'ETH Staked (DeFi — Lido)',       riskScore: 55,  liquid: false, emoji: '⟠'  },
  { value: 'BTC',                 label: 'Bitcoin (BTC)',                  riskScore: 70,  liquid: false, emoji: '₿'  },
]

const JURISDICTIONS = [
  { value: 'EU_MiCA',   label: 'EU — MiCA (Art. 36)',         strictness: 1.18, liquidMin: 60, emoji: '🇪🇺' },
  { value: 'US_NYDFS',  label: 'US — NYDFS BitLicense',       strictness: 1.12, liquidMin: 50, emoji: '🇺🇸' },
  { value: 'UK_FCA',    label: 'UK — FCA Crypto Regime',       strictness: 1.10, liquidMin: 50, emoji: '🇬🇧' },
  { value: 'SG_MAS',    label: 'Singapore — MAS PSA',         strictness: 1.08, liquidMin: 45, emoji: '🇸🇬' },
  { value: 'UAE_VARA',  label: 'UAE Dubai — VARA',            strictness: 1.06, liquidMin: 40, emoji: '🇦🇪' },
  { value: 'GCC',       label: 'GCC — Gulf Region (Emerging)',strictness: 1.04, liquidMin: 35, emoji: '🌍' },
]

function computeCheckpoints(s: ReserveScenario): CheckpointResult[] {
  const dtData   = DECISION_TYPES.find(d => d.value === s.decisionType)  || DECISION_TYPES[0]
  const assetData = RESERVE_ASSETS.find(a => a.value === s.reserveAsset) || RESERVE_ASSETS[0]
  const jurisData = JURISDICTIONS.find(j => j.value === s.jurisdiction)  || JURISDICTIONS[0]

  const isHardBlock_peg      = s.pegDeviation > 2.0
  const isHardBlock_coverage = s.reserveCoverage < 100.0
  const isHardBlock_liquid   = s.liquidRatio < jurisData.liquidMin

  // ── Signal computations ────────────────────────────────────────────────────
  // Signal 1: Reserve Stability (probability)
  const pegScore      = Math.max(0, Math.min(100, 100 - s.pegDeviation * 40))
  const coverageScore = Math.max(0, Math.min(100, (s.reserveCoverage - 100) * 2 + 70))
  const liquidScore   = Math.min(100, s.liquidRatio * (100 / 80))
  const stabilityScore = Math.round((pegScore * 0.40 + coverageScore * 0.35 + liquidScore * 0.25) / jurisData.strictness)

  // Signal 2: Collateral Risk (exposure)
  const cryptoRisk   = s.cryptoExposure * 0.35
  const assetRisk    = assetData.riskScore * 0.30
  const dtRisk       = dtData.risk * 80 * 0.20
  const sizeRisk     = Math.min(30, (s.redemptionSize / 50_000_000) * 30) * 0.15
  const exposureScore = Math.min(100, Math.round(cryptoRisk + assetRisk + dtRisk + sizeRisk))

  // Signal 3: Peg Coherence
  const pegCoherence  = Math.max(0, Math.min(100, 100 - s.pegDeviation * 30))
  const coherenceScore = Math.round(pegCoherence * (assetData.liquid ? 1.0 : 0.85))

  // Signal 4: Reserve Flow Stability
  const trendBase  = 75 - dtData.risk * 50
  const trendScore = Math.max(0, Math.min(100, Math.round(trendBase + (s.reserveCoverage - 100) * 0.8)))

  // Signal 5: Stress Resilience
  const liquidBonus    = assetData.liquid ? 8 : 0
  const bufferScore    = Math.max(0, Math.min(100, (s.liquidRatio / jurisData.liquidMin) * 70 + liquidBonus))
  const stressScore    = Math.round(bufferScore * (1 - dtData.risk * 0.3))

  // Signal 6: Regulatory Compliance
  const micaBase       = s.liquidRatio >= jurisData.liquidMin ? 85 : 30
  const logicScore     = Math.round(Math.max(0, Math.min(100, (micaBase + (assetData.liquid ? 10 : -15)) / jurisData.strictness)))

  const signals = [stabilityScore, 100 - exposureScore, coherenceScore, trendScore, stressScore, logicScore]
  const avgSignal = signals.reduce((a, b) => a + b, 0) / signals.length
  const variance  = signals.reduce((a, b) => a + Math.pow(b - avgSignal, 2), 0) / signals.length
  const divergence = Math.sqrt(variance)

  // Additional checkpoint scores
  const sivScore = Math.min(95, Math.round(stabilityScore * 0.6 + coherenceScore * 0.4))
  const amlScore = Math.min(95, Math.round(90 - (s.cryptoExposure > 30 ? (s.cryptoExposure - 30) * 0.5 : 0)))
  const temporalScore = Math.min(95, Math.round(trendScore * 0.70 + (s.pegDeviation < 0.3 ? 20 : 5)))
  const edgeScore  = Math.round(stabilityScore * 0.55 + logicScore * 0.45)
  const fraudScore = Math.min(95, Math.round(65 + coherenceScore * 0.30))

  return [
    {
      name: 'Signal Integrity Validation',
      genericName: 'CP-1: Are all input signals valid?',
      icon: <Shield className="w-5 h-5" />,
      status: 'pending', score: sivScore, threshold: 60,
      reasoning: sivScore >= 60
        ? `All reserve governance signals validated — peg deviation (${s.pegDeviation.toFixed(3)}%), coverage (${s.reserveCoverage.toFixed(1)}%), liquidity (${s.liquidRatio.toFixed(1)}%), and asset classification inputs are consistent`
        : `Signal validation failed — reserve governance parameters indicate a distressed reserve state requiring immediate escalation`,
      detail: `Stability: ${stabilityScore}/100 | Coherence: ${coherenceScore}/100 | Compliance base: ${logicScore}/100 → SIV: ${sivScore}/100`,
    },
    {
      name: 'Reserve Stability Score',
      genericName: 'CP-1: Is the reserve position stable?',
      icon: <TrendingUp className="w-5 h-5" />,
      status: 'pending', score: stabilityScore, threshold: 55,
      reasoning: isHardBlock_peg
        ? `HARD BLOCK — peg deviation ${s.pegDeviation.toFixed(2)}% exceeds 2% emergency threshold. Depeg protocol must be activated before any reserve action`
        : isHardBlock_coverage
        ? `HARD BLOCK — reserve coverage ${s.reserveCoverage.toFixed(1)}% below 100% minimum. Stablecoin is undercollateralized — systemic solvency risk`
        : stabilityScore >= 55
        ? `Reserve stability confirmed — peg deviation ${s.pegDeviation.toFixed(3)}% within safe range, coverage ${s.reserveCoverage.toFixed(1)}%, liquid ratio ${s.liquidRatio.toFixed(1)}%`
        : `Reserve stability degraded — peg deviation or coverage levels require compliance officer review before proceeding`,
      detail: `Peg score: ${pegScore}/100 | Coverage score: ${coverageScore}/100 | Liquid score: ${liquidScore}/100 → Stability (÷${jurisData.strictness}): ${stabilityScore}/100`,
    },
    {
      name: 'Collateral Risk Exposure',
      genericName: 'CP-2: Would this exceed safe exposure?',
      icon: <Shield className="w-5 h-5" />,
      status: 'pending', score: 100 - exposureScore, threshold: 45,
      reasoning: exposureScore >= 70
        ? `High collateral risk — crypto exposure ${s.cryptoExposure.toFixed(0)}% combined with ${assetData.label} creates excessive concentration risk at this transaction size`
        : exposureScore <= 30
        ? `Collateral risk within safe bounds — ${assetData.label} (risk score: ${assetData.riskScore}/100) diversifies reserve adequately`
        : `Moderate collateral risk — monitor ${assetData.label} position against portfolio concentration limits`,
      detail: `Asset risk: ${assetData.riskScore}/100 | Crypto exposure: ${s.cryptoExposure.toFixed(0)}% | Decision type risk: ${(dtData.risk * 100).toFixed(0)}% | Exposure: ${exposureScore}/100`,
    },
    {
      name: 'Peg Coherence Check',
      genericName: 'CP-3: Do multiple models agree?',
      icon: <Layers className="w-5 h-5" />,
      status: 'pending', score: coherenceScore, threshold: 50,
      reasoning: coherenceScore >= 50
        ? `On-chain and off-chain peg signals are coherent — oracle feeds and exchange prices align within acceptable tolerance (${s.pegDeviation.toFixed(3)}% deviation)`
        : `Peg coherence failure — significant divergence between on-chain price (oracle) and off-chain attestation. Possible manipulation or oracle attack`,
      detail: `Peg deviation: ${s.pegDeviation.toFixed(3)}% | MiCA liquid classification: ${assetData.liquid ? 'YES' : 'NO'} | Coherence: ${coherenceScore}/100`,
    },
    {
      name: 'Reserve Flow Persistence',
      genericName: 'CP-4: Is this sustained, not noise?',
      icon: <Activity className="w-5 h-5" />,
      status: 'pending', score: trendScore, threshold: 40,
      reasoning: trendScore >= 40
        ? `Reserve flow trends confirm sustained stability — not a transient stress spike. Coverage ratio ${s.reserveCoverage.toFixed(1)}% is structurally supported`
        : `Reserve flows show instability — ${dtData.label.toLowerCase()} under current market conditions may be reacting to temporary stress, not structural issue`,
      detail: `Base trend: ${Math.max(0, 75 - dtData.risk * 50).toFixed(0)} | Coverage bonus: ${((s.reserveCoverage - 100) * 0.8).toFixed(0)} → Persistence: ${trendScore}/100`,
    },
    {
      name: 'Stress Test Resilience',
      genericName: 'CP-5: What if conditions deteriorate?',
      icon: <AlertTriangle className="w-5 h-5" />,
      status: 'pending', score: stressScore, threshold: 35,
      reasoning: isHardBlock_liquid
        ? `HARD BLOCK — liquid reserve ratio ${s.liquidRatio.toFixed(1)}% below ${jurisData.label} minimum of ${jurisData.liquidMin}%. ${jurisData.value === 'EU_MiCA' ? 'MiCA Art. 36' : 'Regulatory'} hard block triggered`
        : stressScore >= 35
        ? `Stress test passed — liquid ratio ${s.liquidRatio.toFixed(1)}% provides ${(s.liquidRatio - jurisData.liquidMin).toFixed(1)}pp buffer above ${jurisData.label} minimum (${jurisData.liquidMin}%)`
        : `Stress test marginal — liquid reserves insufficient for simulated bank-run scenario under ${jurisData.label} jurisdiction requirements`,
      detail: `Liquid ratio: ${s.liquidRatio.toFixed(1)}% | Jurisdiction min: ${jurisData.liquidMin}% | MiCA liquid asset: ${assetData.liquid ? 'YES' : 'NO'} → Resilience: ${stressScore}/100`,
    },
    {
      name: 'Signal Contradiction Check',
      genericName: 'CP-6: Are signals contradicting each other?',
      icon: <Brain className="w-5 h-5" />,
      status: 'pending', score: Math.round(Math.max(0, Math.min(100, 100 - divergence * 2.2))), threshold: 40,
      reasoning: divergence < 20
        ? `Signal consistency confirmed — all governance signals are mutually reinforcing (divergence: ${divergence.toFixed(1)})`
        : `High signal divergence (${divergence.toFixed(1)}) — some indicators suggest approval while others suggest block. Manual review required`,
      detail: `Signal avg: ${avgSignal.toFixed(1)} | Std deviation: ${divergence.toFixed(1)} | ${divergence < 15 ? 'ALIGNED' : divergence < 25 ? 'TENSIONED' : 'CONTRADICTORY'}`,
    },
    {
      name: 'Temporal Coherence',
      genericName: 'CP-7: Does this hold across time?',
      icon: <Clock className="w-5 h-5" />,
      status: 'pending', score: temporalScore, threshold: 40,
      reasoning: temporalScore >= 40
        ? `Reserve condition persistence confirmed — peg deviation and flow stability metrics are consistent over the observation window`
        : `Temporal analysis reveals transient conditions — current reserve stress may be a short-term spike not warranting structural action`,
      detail: `Trend base: ${trendScore} | Peg stability: ${s.pegDeviation < 0.3 ? 'HIGH' : s.pegDeviation < 1.0 ? 'MEDIUM' : 'LOW'} | Temporal: ${temporalScore}/100`,
    },
    {
      name: 'Edge Confirmation (ECW)',
      genericName: 'CP-8: Does the decision converge at the boundary?',
      icon: <Target className="w-5 h-5" />,
      status: 'pending', score: edgeScore, threshold: 48,
      reasoning: edgeScore >= 48
        ? `Decision boundary confirmed — stability and compliance signals converge at governance edge (${edgeScore}%)`
        : `Weak boundary convergence — stability score and compliance signals do not mutually reinforce governance decision`,
      detail: `Stability ×0.55: ${(stabilityScore * 0.55).toFixed(0)} | Compliance ×0.45: ${(logicScore * 0.45).toFixed(0)} | Edge: ${edgeScore}/100`,
    },
    {
      name: 'AML & Sanctions Gate',
      genericName: 'CP-9: Does this pass compliance screening?',
      icon: <Lock className="w-5 h-5" />,
      status: 'pending', score: amlScore, threshold: 60,
      reasoning: amlScore >= 60
        ? `AML/Sanctions screening passed — transaction amount and reserve asset show no anomalous financial crime patterns`
        : `AML flag — crypto exposure ${s.cryptoExposure.toFixed(0)}% above 30% triggers enhanced due diligence under ${jurisData.label} framework`,
      detail: `Crypto exposure: ${s.cryptoExposure.toFixed(0)}% | Redemption: $${(s.redemptionSize / 1_000_000).toFixed(1)}M | AML score: ${amlScore}/100`,
    },
    {
      name: 'Fraud & Manipulation Detection',
      genericName: 'CP-10: Is this genuine market activity?',
      icon: <BarChart3 className="w-5 h-5" />,
      status: 'pending', score: fraudScore, threshold: 55,
      reasoning: fraudScore >= 55
        ? `No manipulation patterns detected — peg deviation and redemption size are consistent with normal reserve operations`
        : `Anomaly detected — transaction pattern may indicate coordinated peg attack or wash redemption activity`,
      detail: `Peg coherence: ${coherenceScore}/100 | Reserve flow consistency → Fraud score: ${fraudScore}/100`,
    },
    {
      name: 'Regulatory Compliance Gate',
      genericName: 'CP-11: Does this satisfy all regulatory requirements?',
      icon: <Globe className="w-5 h-5" />,
      status: 'pending', score: logicScore, threshold: 50,
      reasoning: isHardBlock_liquid
        ? `COMPLIANCE HARD BLOCK — ${jurisData.label} requires minimum ${jurisData.liquidMin}% liquid reserves. Current ratio ${s.liquidRatio.toFixed(1)}% is non-compliant`
        : logicScore >= 50
        ? `${jurisData.label} compliance satisfied — liquid ratio ${s.liquidRatio.toFixed(1)}% ≥ ${jurisData.liquidMin}% minimum, asset classification compliant (${assetData.liquid ? 'MiCA liquid' : 'MiCA non-liquid'})`
        : `Compliance deficit — ${jurisData.label} requirements not met. Governance strictness factor: ${jurisData.strictness}×`,
      detail: `Jurisdiction: ${jurisData.label} | Min liquid: ${jurisData.liquidMin}% | Actual: ${s.liquidRatio.toFixed(1)}% | Strictness: ${jurisData.strictness}× | Compliance: ${logicScore}/100`,
    },
  ]
}

function ScoreBar({ score, threshold, color }: { score: number; threshold: number; color: string }) {
  return (
    <div style={{ position: 'relative', height: 8, background: '#1E293B', borderRadius: 4, overflow: 'visible' }}>
      <div style={{ position: 'absolute', left: `${threshold}%`, top: -3, width: 2, height: 14, background: '#F59E0B', borderRadius: 1, zIndex: 2 }} />
      <div style={{ height: '100%', width: `${score}%`, background: color, borderRadius: 4, transition: 'width 0.8s ease' }} />
    </div>
  )
}

export default function StablecoinGovernanceDemo() {
  const [scenario, setScenario] = useState<ReserveScenario>({
    decisionType:    'reserve_rebalancing',
    reserveAsset:    'US_Treasury_Bills',
    jurisdiction:    'EU_MiCA',
    pegDeviation:    0.08,
    reserveCoverage: 107.5,
    liquidRatio:     82.0,
    cryptoExposure:  4.0,
    redemptionSize:  2_000_000,
  })
  const [checkpoints, setCheckpoints]   = useState<CheckpointResult[]>([])
  const [currentCp,   setCurrentCp]     = useState(-1)
  const [finalResult, setFinalResult]   = useState<string | null>(null)
  const [isRunning,   setIsRunning]     = useState(false)
  const [receiptId,   setReceiptId]     = useState<string | null>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  function buildReceiptId() {
    const hex = Array.from({ length: 12 }, () => Math.floor(Math.random() * 16).toString(16).toUpperCase()).join('')
    return `OMNIX-SRG-${hex}`
  }

  function runGovernance() {
    if (isRunning) return
    const cps = computeCheckpoints(scenario)
    setCheckpoints(cps.map(c => ({ ...c, status: 'pending' })))
    setCurrentCp(-1)
    setFinalResult(null)
    setReceiptId(null)
    setIsRunning(true)

    cps.forEach((_, i) => {
      timerRef.current = setTimeout(() => {
        setCurrentCp(i)
        setCheckpoints(prev => prev.map((c, idx) =>
          idx < i  ? { ...c, status: (c.score >= c.threshold ? 'pass' : c.score >= c.threshold * 0.7 ? 'warn' : 'block') as CheckpointResult['status'] }
          : idx === i ? { ...c, status: 'evaluating' as CheckpointResult['status'] }
          : c
        ))
        if (i === cps.length - 1) {
          setTimeout(() => {
            const final = cps.map(c => c.status !== 'pending' ? c : { ...c, status: (c.score >= c.threshold ? 'pass' : 'block') as CheckpointResult['status'] })
            const hardBlocks = cps.filter(c => c.score < c.threshold * 0.5).length
            const blocks     = cps.filter(c => c.score < c.threshold).length
            let verdict: string
            if (hardBlocks > 0 || scenario.pegDeviation > 2.0 || scenario.reserveCoverage < 100.0) {
              verdict = 'HARD_BLOCK'
            } else if (blocks > 2) {
              verdict = 'BLOCKED'
            } else if (blocks > 0) {
              verdict = 'HOLD'
            } else {
              verdict = 'APPROVED'
            }
            const finalCps: CheckpointResult[] = final.map(c => ({ ...c, status: (c.score >= c.threshold ? 'pass' : c.score >= c.threshold * 0.7 ? 'warn' : 'block') as CheckpointResult['status'] }))
            setCheckpoints(finalCps)
            setCurrentCp(-1)
            setFinalResult(verdict)
            if (verdict === 'APPROVED') setReceiptId(buildReceiptId())
            setIsRunning(false)
          }, 400)
        }
      }, i * 280)
    })
  }

  useEffect(() => () => { if (timerRef.current) clearTimeout(timerRef.current) }, [])

  const statusIcon = (s: CheckpointResult['status']) => {
    if (s === 'pending')    return <Clock    size={16} style={{ color: '#475569' }} />
    if (s === 'evaluating') return <Activity size={16} style={{ color: SRG_VIOLET, animation: 'pulse 0.8s ease-in-out infinite' }} />
    if (s === 'pass')       return <CheckCircle size={16} style={{ color: '#10B981' }} />
    if (s === 'warn')       return <AlertTriangle size={16} style={{ color: '#F59E0B' }} />
    return <XCircle size={16} style={{ color: '#EF4444' }} />
  }

  const statusColor = (s: CheckpointResult['status']) => {
    if (s === 'pass') return '#10B981'
    if (s === 'warn') return '#F59E0B'
    if (s === 'block') return '#EF4444'
    if (s === 'evaluating') return SRG_VIOLET
    return '#475569'
  }

  const dtData    = DECISION_TYPES.find(d => d.value === scenario.decisionType) || DECISION_TYPES[0]
  const assetData = RESERVE_ASSETS.find(a => a.value === scenario.reserveAsset) || RESERVE_ASSETS[0]
  const jurisData = JURISDICTIONS.find(j => j.value === scenario.jurisdiction)  || JURISDICTIONS[0]
  const hardBlockPeg      = scenario.pegDeviation > 2.0
  const hardBlockCoverage = scenario.reserveCoverage < 100.0
  const hardBlockLiquid   = scenario.liquidRatio < jurisData.liquidMin

  const inputStyle: React.CSSProperties = {
    background: '#0F172A', border: '1px solid #334155', borderRadius: 8,
    color: '#E2E8F0', padding: '9px 12px', fontSize: 13, width: '100%',
    outline: 'none', cursor: 'pointer',
  }
  const labelStyle: React.CSSProperties = { fontSize: 11, color: '#94A3B8', marginBottom: 5, display: 'block', fontWeight: 600 }
  const sliderStyle: React.CSSProperties = {
    width: '100%', accentColor: SRG_VIOLET, cursor: 'pointer', height: 4,
  }

  return (
    <div style={{
      minHeight: '100vh', background: 'linear-gradient(135deg, #0A0B14 0%, #0D1117 60%, #0A0E1A 100%)',
      color: '#E2E8F0', fontFamily: "'Inter', sans-serif", padding: '28px 24px',
    }}>
      <style>{`
        @keyframes pulse { 0%,100%{opacity:1}50%{opacity:0.3} }
        @keyframes spin  { from{transform:rotate(0deg)}to{transform:rotate(360deg)} }
        * { box-sizing: border-box }
        select option { background: #0F172A }
      `}</style>

      <div style={{ maxWidth: 1280, margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: 28 }}>
          <Link to="/stablecoin" style={{ color: '#64748B', fontSize: 12, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 4, marginBottom: 12 }}>
            ← Stablecoin Reserve Dashboard
          </Link>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{
              width: 48, height: 48, borderRadius: 12, background: `${SRG_VIOLET}22`,
              border: `1px solid ${SRG_VIOLET}44`, display: 'flex', alignItems: 'center',
              justifyContent: 'center', fontSize: 24,
            }}>🪙</div>
            <div>
              <div style={{ fontSize: 22, fontWeight: 800, letterSpacing: '-0.02em' }}>
                Stablecoin Reserve Governance — Interactive Demo
              </div>
              <div style={{ fontSize: 12, color: '#64748B', marginTop: 3 }}>
                ADR-SRG-001 · 11-Checkpoint MiCA-Compliant Pipeline · OMNIX-SRG PQC Receipts
              </div>
            </div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: 20 }}>
          {/* Left Panel — Scenario Configuration */}
          <div>
            <div style={{
              background: 'rgba(17,24,39,0.9)', borderRadius: 14, padding: 22,
              border: `1px solid ${SRG_VIOLET}33`, marginBottom: 16,
            }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: SRG_LIGHT, marginBottom: 18 }}>
                Reserve Scenario Configuration
              </div>

              {/* Decision Type */}
              <div style={{ marginBottom: 14 }}>
                <label style={labelStyle}>Decision Type</label>
                <select style={inputStyle} value={scenario.decisionType}
                  onChange={e => setScenario(p => ({ ...p, decisionType: e.target.value }))}>
                  {DECISION_TYPES.map(d => <option key={d.value} value={d.value}>{d.emoji} {d.label}</option>)}
                </select>
              </div>

              {/* Reserve Asset */}
              <div style={{ marginBottom: 14 }}>
                <label style={labelStyle}>Reserve Asset Being Deployed</label>
                <select style={inputStyle} value={scenario.reserveAsset}
                  onChange={e => setScenario(p => ({ ...p, reserveAsset: e.target.value }))}>
                  {RESERVE_ASSETS.map(a => <option key={a.value} value={a.value}>{a.emoji} {a.label}</option>)}
                </select>
                <div style={{ fontSize: 10, color: assetData.liquid ? '#10B981' : '#EF4444', marginTop: 4 }}>
                  {assetData.liquid ? '✓ MiCA Liquid Reserve Eligible' : '✗ NOT MiCA Liquid Reserve Eligible'}
                </div>
              </div>

              {/* Jurisdiction */}
              <div style={{ marginBottom: 18 }}>
                <label style={labelStyle}>Regulatory Jurisdiction</label>
                <select style={inputStyle} value={scenario.jurisdiction}
                  onChange={e => setScenario(p => ({ ...p, jurisdiction: e.target.value }))}>
                  {JURISDICTIONS.map(j => <option key={j.value} value={j.value}>{j.emoji} {j.label}</option>)}
                </select>
                <div style={{ fontSize: 10, color: '#94A3B8', marginTop: 4 }}>
                  Strictness: {jurisData.strictness}× · Min liquid: {jurisData.liquidMin}%
                </div>
              </div>

              {/* Peg Deviation */}
              <div style={{ marginBottom: 14 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                  <label style={{ ...labelStyle, marginBottom: 0 }}>Peg Deviation</label>
                  <span style={{ fontSize: 13, fontWeight: 700, color: hardBlockPeg ? '#EF4444' : scenario.pegDeviation > 0.5 ? '#F59E0B' : '#10B981' }}>
                    {scenario.pegDeviation.toFixed(3)}%
                    {hardBlockPeg && ' ⚠️ HARD BLOCK'}
                  </span>
                </div>
                <input type="range" min={0} max={4} step={0.01} style={sliderStyle}
                  value={scenario.pegDeviation}
                  onChange={e => setScenario(p => ({ ...p, pegDeviation: parseFloat(e.target.value) }))} />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#475569', marginTop: 2 }}>
                  <span>0% Perfect</span><span style={{ color: '#F59E0B' }}>1% Warning</span><span style={{ color: '#EF4444' }}>2%+ HARD BLOCK</span>
                </div>
              </div>

              {/* Reserve Coverage */}
              <div style={{ marginBottom: 14 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                  <label style={{ ...labelStyle, marginBottom: 0 }}>Reserve Coverage Ratio</label>
                  <span style={{ fontSize: 13, fontWeight: 700, color: hardBlockCoverage ? '#EF4444' : scenario.reserveCoverage < 102 ? '#F59E0B' : '#10B981' }}>
                    {scenario.reserveCoverage.toFixed(1)}%
                    {hardBlockCoverage && ' ⚠️ HARD BLOCK'}
                  </span>
                </div>
                <input type="range" min={85} max={130} step={0.5} style={sliderStyle}
                  value={scenario.reserveCoverage}
                  onChange={e => setScenario(p => ({ ...p, reserveCoverage: parseFloat(e.target.value) }))} />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#475569', marginTop: 2 }}>
                  <span style={{ color: '#EF4444' }}>&lt;100% BLOCK</span><span>100% Min</span><span style={{ color: '#10B981' }}>130% Safe</span>
                </div>
              </div>

              {/* Liquid Reserve Ratio */}
              <div style={{ marginBottom: 14 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                  <label style={{ ...labelStyle, marginBottom: 0 }}>Liquid Reserve Ratio</label>
                  <span style={{ fontSize: 13, fontWeight: 700, color: hardBlockLiquid ? '#EF4444' : scenario.liquidRatio < jurisData.liquidMin + 10 ? '#F59E0B' : '#10B981' }}>
                    {scenario.liquidRatio.toFixed(1)}%
                    {hardBlockLiquid && ` ⚠️ <${jurisData.liquidMin}%`}
                  </span>
                </div>
                <input type="range" min={20} max={100} step={0.5} style={sliderStyle}
                  value={scenario.liquidRatio}
                  onChange={e => setScenario(p => ({ ...p, liquidRatio: parseFloat(e.target.value) }))} />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#475569', marginTop: 2 }}>
                  <span style={{ color: '#EF4444' }}>20%</span><span style={{ color: '#F59E0B' }}>{jurisData.liquidMin}% {jurisData.value} min</span><span style={{ color: '#10B981' }}>100%</span>
                </div>
              </div>

              {/* Crypto Exposure */}
              <div style={{ marginBottom: 14 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                  <label style={{ ...labelStyle, marginBottom: 0 }}>Crypto Reserve Exposure</label>
                  <span style={{ fontSize: 13, fontWeight: 700, color: scenario.cryptoExposure > 30 ? '#EF4444' : scenario.cryptoExposure > 15 ? '#F59E0B' : '#10B981' }}>
                    {scenario.cryptoExposure.toFixed(0)}%
                  </span>
                </div>
                <input type="range" min={0} max={80} step={1} style={sliderStyle}
                  value={scenario.cryptoExposure}
                  onChange={e => setScenario(p => ({ ...p, cryptoExposure: parseFloat(e.target.value) }))} />
              </div>

              {/* Redemption Size */}
              <div style={{ marginBottom: 20 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                  <label style={{ ...labelStyle, marginBottom: 0 }}>Redemption / Transaction Size</label>
                  <span style={{ fontSize: 13, fontWeight: 700, color: SRG_LIGHT }}>
                    ${(scenario.redemptionSize / 1_000_000).toFixed(1)}M
                  </span>
                </div>
                <input type="range" min={100_000} max={100_000_000} step={100_000} style={sliderStyle}
                  value={scenario.redemptionSize}
                  onChange={e => setScenario(p => ({ ...p, redemptionSize: parseFloat(e.target.value) }))} />
              </div>

              {/* Hard block warnings */}
              {(hardBlockPeg || hardBlockCoverage || hardBlockLiquid) && (
                <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid #EF444433', borderRadius: 8, padding: 12, marginBottom: 16 }}>
                  <div style={{ color: '#EF4444', fontWeight: 700, fontSize: 12, marginBottom: 6 }}>⚠️ Hard Block Conditions Active</div>
                  {hardBlockPeg      && <div style={{ color: '#FCA5A5', fontSize: 11, marginBottom: 3 }}>• Peg deviation {scenario.pegDeviation.toFixed(2)}% &gt; 2% threshold</div>}
                  {hardBlockCoverage && <div style={{ color: '#FCA5A5', fontSize: 11, marginBottom: 3 }}>• Reserve coverage {scenario.reserveCoverage.toFixed(1)}% &lt; 100% minimum</div>}
                  {hardBlockLiquid   && <div style={{ color: '#FCA5A5', fontSize: 11 }}>• Liquid ratio {scenario.liquidRatio.toFixed(1)}% &lt; {jurisData.liquidMin}% ({jurisData.value} minimum)</div>}
                </div>
              )}

              <button
                onClick={runGovernance}
                disabled={isRunning}
                style={{
                  width: '100%', padding: '13px 20px', borderRadius: 10, border: 'none',
                  background: isRunning ? '#1E293B' : `linear-gradient(135deg, ${SRG_VIOLET}, #7C3AED)`,
                  color: isRunning ? '#475569' : '#FFF', fontWeight: 700, fontSize: 14,
                  cursor: isRunning ? 'not-allowed' : 'pointer', transition: 'all 0.2s',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                }}>
                <Shield size={16} />
                {isRunning ? 'Evaluating Reserve Decision…' : 'Run 11-Checkpoint Governance Pipeline'}
                {!isRunning && <ArrowRight size={16} />}
              </button>
            </div>

            {/* Scenario Summary */}
            <div style={{
              background: 'rgba(17,24,39,0.9)', borderRadius: 12, padding: 16,
              border: `1px solid #1E293B`, fontSize: 12,
            }}>
              <div style={{ color: '#64748B', fontWeight: 600, marginBottom: 10, fontSize: 11 }}>CURRENT SCENARIO</div>
              {[
                ['Type', `${dtData.emoji} ${dtData.label}`],
                ['Asset', `${assetData.emoji} ${assetData.label.split(' (')[0]}`],
                ['Jurisdiction', `${jurisData.emoji} ${jurisData.label.split(' (')[0]}`],
                ['Peg Deviation', `${scenario.pegDeviation.toFixed(3)}%`],
                ['Coverage', `${scenario.reserveCoverage.toFixed(1)}%`],
                ['Liquidity', `${scenario.liquidRatio.toFixed(1)}%`],
              ].map(([k, v]) => (
                <div key={k as string} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, paddingBottom: 6, borderBottom: '1px solid #0F172A' }}>
                  <span style={{ color: '#475569' }}>{k}</span>
                  <span style={{ color: '#CBD5E1', fontWeight: 600 }}>{v}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Right Panel — 11 Checkpoints */}
          <div>
            {checkpoints.length === 0 ? (
              <div style={{
                background: 'rgba(17,24,39,0.85)', borderRadius: 14, padding: 48,
                border: `1px solid ${SRG_VIOLET}22`, textAlign: 'center',
              }}>
                <div style={{ fontSize: 48, marginBottom: 16 }}>🪙</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: SRG_LIGHT, marginBottom: 8 }}>
                  Stablecoin Reserve Governance Pipeline
                </div>
                <div style={{ color: '#64748B', fontSize: 13, maxWidth: 420, margin: '0 auto', lineHeight: 1.6 }}>
                  Configure a reserve scenario on the left and run the 11-checkpoint MiCA-compliant governance pipeline.
                  Each decision generates a PQC-signed OMNIX-SRG receipt for regulatory audit.
                </div>
                <div style={{ marginTop: 24, display: 'flex', justifyContent: 'center', gap: 12, flexWrap: 'wrap' }}>
                  {['Peg Defense', 'MiCA Liquid Breach', 'Reserve Rebalancing'].map(s => (
                    <span key={s} style={{ background: `${SRG_VIOLET}15`, border: `1px solid ${SRG_VIOLET}33`, borderRadius: 6, padding: '4px 12px', fontSize: 11, color: SRG_LIGHT }}>
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            ) : (
              <div>
                {/* Final Result Banner */}
                {finalResult && (
                  <div style={{
                    borderRadius: 12, padding: '16px 20px', marginBottom: 16,
                    background: finalResult === 'APPROVED'   ? 'rgba(16,185,129,0.12)'
                               : finalResult === 'HOLD'      ? 'rgba(245,158,11,0.12)'
                               : 'rgba(239,68,68,0.12)',
                    border: `1px solid ${finalResult === 'APPROVED' ? '#10B981' : finalResult === 'HOLD' ? '#F59E0B' : '#EF4444'}44`,
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      {finalResult === 'APPROVED' ? <CheckCircle size={22} style={{ color: '#10B981' }} />
                       : finalResult === 'HOLD'    ? <AlertTriangle size={22} style={{ color: '#F59E0B' }} />
                       : <XCircle size={22} style={{ color: '#EF4444' }} />}
                      <div>
                        <div style={{ fontWeight: 800, fontSize: 16,
                          color: finalResult === 'APPROVED' ? '#10B981' : finalResult === 'HOLD' ? '#F59E0B' : '#EF4444' }}>
                          RESERVE ACTION: {finalResult}
                        </div>
                        {receiptId && <div style={{ fontSize: 11, color: '#10B981', fontFamily: 'monospace', marginTop: 2 }}>Receipt: {receiptId}</div>}
                        {!receiptId && finalResult !== 'APPROVED' && <div style={{ fontSize: 11, color: '#EF4444', marginTop: 2 }}>No receipt — action blocked by governance</div>}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right', fontSize: 11, color: '#475569' }}>
                      <div>{dtData.emoji} {dtData.label}</div>
                      <div>{assetData.emoji} {assetData.label.split(' (')[0]}</div>
                      <div>{jurisData.emoji} {jurisData.label.split(' (')[0]}</div>
                    </div>
                  </div>
                )}

                {/* Checkpoint List */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {checkpoints.map((cp, i) => {
                    const isActive = currentCp === i
                    const borderColor = cp.status === 'evaluating' ? SRG_VIOLET
                      : cp.status === 'pass'   ? '#10B981'
                      : cp.status === 'warn'   ? '#F59E0B'
                      : cp.status === 'block'  ? '#EF4444'
                      : '#1E293B'
                    const barColor = cp.status === 'pass' ? '#10B981'
                      : cp.status === 'warn'  ? '#F59E0B'
                      : cp.status === 'block' ? '#EF4444'
                      : SRG_VIOLET
                    return (
                      <div key={i} style={{
                        background: isActive ? 'rgba(139,92,246,0.08)' : 'rgba(17,24,39,0.85)',
                        borderRadius: 10, padding: '14px 16px',
                        border: `1px solid ${borderColor}44`,
                        transition: 'all 0.3s',
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            {statusIcon(cp.status)}
                            <div>
                              <div style={{ fontSize: 13, fontWeight: 700, color: '#E2E8F0' }}>{cp.name}</div>
                              <div style={{ fontSize: 10, color: '#64748B' }}>{cp.genericName}</div>
                            </div>
                          </div>
                          <div style={{ textAlign: 'right', flexShrink: 0, marginLeft: 10 }}>
                            <div style={{ fontSize: 18, fontWeight: 800, color: statusColor(cp.status) }}>{cp.score}</div>
                            <div style={{ fontSize: 10, color: '#475569' }}>min {cp.threshold}</div>
                          </div>
                        </div>

                        <ScoreBar score={cp.score} threshold={cp.threshold} color={barColor} />

                        {cp.status !== 'pending' && (
                          <div style={{ marginTop: 10 }}>
                            <div style={{ fontSize: 12, color: '#94A3B8', lineHeight: 1.5, marginBottom: 6 }}>{cp.reasoning}</div>
                            <div style={{ fontSize: 10, color: '#475569', fontFamily: 'monospace', background: '#0F172A', padding: '6px 10px', borderRadius: 6 }}>
                              {cp.detail}
                            </div>
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

        {/* Footer */}
        <div style={{ marginTop: 28, textAlign: 'center', color: '#334155', fontSize: 11 }}>
          OMNIX Stablecoin Reserve Governance · ADR-SRG-001 · 11-Checkpoint Fail-Closed Pipeline
          &nbsp;·&nbsp; MiCA Art. 36 · VARA · MAS · NYDFS · FCA · Receipts: OMNIX-SRG-{'{12HEX}'}
          &nbsp;·&nbsp; <Link to="/stablecoin" style={{ color: SRG_VIOLET, textDecoration: 'none' }}>Live Dashboard →</Link>
          &nbsp;·&nbsp; <Link to="/try" style={{ color: SRG_VIOLET, textDecoration: 'none' }}>Public Sandbox →</Link>
        </div>
      </div>
    </div>
  )
}
