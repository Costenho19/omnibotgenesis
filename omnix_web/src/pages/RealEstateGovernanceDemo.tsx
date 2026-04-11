import { useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield, CheckCircle, XCircle, Clock, Activity,
  AlertTriangle, TrendingUp, Lock
} from 'lucide-react'

interface CheckpointResult {
  name: string
  icon: React.ReactNode
  status: 'pending' | 'evaluating' | 'pass' | 'warn' | 'block'
  score: number
  threshold: number
  reasoning: string
  detail: string
}

interface PropertyCase {
  decisionType: string
  propertyType: string
  marketSegment: string
  jurisdiction: string
  financingMode: string
  avmConfidence: number
  priceDeviation: number
  ltvRatio: number
  marketTrend: number
  liquidityScore: number
  amlRiskScore: number
  amlFlag: boolean
  reraCompliant: boolean
  shariaScreeningPassed: boolean
  beneficialOwnerVerified: boolean
}

const DECISION_TYPES = [
  { value: 'property_valuation', label: 'Property Valuation (AVM)', icon: '🏠', baseScore: 0.70 },
  { value: 'mortgage_approval',  label: 'Mortgage Underwriting',    icon: '🏦', baseScore: 0.75 },
  { value: 'tenant_screening',   label: 'Tenant Screening',         icon: '👤', baseScore: 0.65 },
  { value: 'aml_transaction',    label: 'AML Transaction Screen',   icon: '🔍', baseScore: 0.80 },
  { value: 'rental_pricing',     label: 'Algorithmic Rental Price', icon: '💰', baseScore: 0.68 },
]

const PROPERTY_TYPES = [
  { value: 'Residential', label: 'Residential', riskMod: 1.00 },
  { value: 'Commercial',  label: 'Commercial',  riskMod: 1.15 },
  { value: 'Industrial',  label: 'Industrial',  riskMod: 1.25 },
  { value: 'Mixed_Use',   label: 'Mixed-Use',   riskMod: 1.10 },
  { value: 'Land',        label: 'Land',        riskMod: 1.30 },
]

const MARKET_SEGMENTS = [
  { value: 'Affordable', label: 'Affordable',  amlMod: 0.85 },
  { value: 'Mid_Market', label: 'Mid-Market',  amlMod: 1.00 },
  { value: 'Premium',    label: 'Premium',     amlMod: 1.15 },
  { value: 'Luxury',     label: 'Luxury',      amlMod: 1.40 },
]

const JURISDICTIONS = [
  { value: 'UAE',    label: '🇦🇪 UAE (RERA / DLD)',         strictness: 1.08 },
  { value: 'GCC',    label: '🌙 GCC (SAMA / QFMA)',          strictness: 1.04 },
  { value: 'UK',     label: '🇬🇧 UK (FCA / UKFI)',           strictness: 1.10 },
  { value: 'EU',     label: '🇪🇺 EU (MCD / AMLD6)',          strictness: 1.06 },
  { value: 'GLOBAL', label: '🌐 Global',                     strictness: 1.00 },
]

const FINANCING_MODES = [
  { value: 'Conventional', label: 'Conventional',         shariaRequired: false, ltvMax: 90 },
  { value: 'Murabaha',     label: 'Murabaha (Islamic)',    shariaRequired: true,  ltvMax: 85 },
  { value: 'Ijarah',       label: 'Ijarah (Islamic)',      shariaRequired: true,  ltvMax: 85 },
  { value: 'Musharaka',    label: 'Musharaka (Islamic)',   shariaRequired: true,  ltvMax: 80 },
]

function evaluatePropertyCheckpoints(c: PropertyCase): CheckpointResult[] {
  const dtData   = DECISION_TYPES.find(d => d.value === c.decisionType) || DECISION_TYPES[0]
  const propData = PROPERTY_TYPES.find(p => p.value === c.propertyType) || PROPERTY_TYPES[0]
  const jxData   = JURISDICTIONS.find(j => j.value === c.jurisdiction) || JURISDICTIONS[0]
  const finData  = FINANCING_MODES.find(f => f.value === c.financingMode) || FINANCING_MODES[0]
  const segData  = MARKET_SEGMENTS.find(s => s.value === c.marketSegment) || MARKET_SEGMENTS[0]

  const avm     = c.avmConfidence / 100
  const dev     = c.priceDeviation / 100
  const ltv     = c.ltvRatio / 100
  const trend   = c.marketTrend / 100
  const liq     = c.liquidityScore / 100
  const aml     = c.amlRiskScore / 100

  // ── CP-1: Input Validation & Data Completeness ─────────────────────────
  const cp1Score = Math.round((avm * 0.6 + (1 - dev) * 0.4) * 100)
  const cp1Pass = cp1Score >= 55 && !c.amlFlag

  // ── CP-2: AVM Valuation Confidence ────────────────────────────────────
  const baseConf = avm * 0.55 + (1 - dev * 0.5) * 0.30 + liq * 0.15
  const cp2Score = Math.round((baseConf / jxData.strictness) * 100)
  const cp2Threshold = Math.round(dtData.baseScore * 100)
  const cp2Pass = cp2Score >= cp2Threshold

  // ── CP-3: Transaction Risk / LTV Exposure ─────────────────────────────
  const ltvMax = finData.ltvMax / 100
  const ltvHardBlock = c.ltvRatio > finData.ltvMax
  const rawRisk = (ltv * 0.40 + dev * 0.30 + aml * 0.20 + (c.amlFlag ? 0.10 : 0)) * segData.amlMod * propData.riskMod
  const cp3Score = Math.round((1 - Math.min(rawRisk, 1)) * 100)
  const cp3Pass = !ltvHardBlock && cp3Score >= 30

  // ── CP-4: Multi-Source Data Alignment (Coherence) ─────────────────────
  const coherence = avm * 0.40 + (1 - dev * 0.6) * 0.35 + liq * 0.25
  const cp4Score = Math.round(coherence * 100)
  const cp4Pass = cp4Score >= 58

  // ── CP-5: Market Trajectory Stability ─────────────────────────────────
  const trajectory = trend * 0.55 + liq * 0.30 + (1 - dev * 0.3) * 0.15
  const cp5Score = Math.round(trajectory * 100)
  const cp5Pass = cp5Score >= 52

  // ── CP-6: Portfolio Stress Resilience ─────────────────────────────────
  const resilience = liq * 0.45 + (1 - aml * 0.4) * 0.30 + (1 - Math.max(0, ltv - 0.7)) * 0.25
  const cp6Score = Math.round(resilience * 100)
  const cp6Pass = cp6Score >= 50

  // ── CP-7: Regulatory & Compliance Alignment ───────────────────────────
  let compliance = (1 - aml * 0.40) * 100
  compliance += c.reraCompliant ? 25 : -40
  compliance += c.beneficialOwnerVerified ? 15 : -25
  if (finData.shariaRequired) {
    compliance += c.shariaScreeningPassed ? 15 : -50
  }
  const cp7Score = Math.round(Math.max(0, Math.min(100, compliance / jxData.strictness)))
  const cp7Pass = !c.amlFlag && c.reraCompliant
    && (!finData.shariaRequired || c.shariaScreeningPassed)
    && cp7Score >= 65

  // ── CP-8: Governance Score Threshold ──────────────────────────────────
  const signals = [cp2Score, 100 - (100 - cp3Score), cp4Score, cp5Score, cp6Score, cp7Score]
  const cp8Score = Math.round(signals.reduce((a, b) => a + b, 0) / signals.length)
  const cp8Pass = cp8Score >= 60 && !c.amlFlag

  // ── CP-9: Probabilistic Risk Stress Test ──────────────────────────────
  const stressLoad = aml * 0.4 + (1 - liq) * 0.3 + dev * 0.3
  const cp9Score = Math.round((1 - stressLoad) * cp8Score)
  const cp9Pass = cp9Score >= 55

  // ── CP-10: Receipt Authorization ──────────────────────────────────────
  const cp10Score = (cp1Pass && cp2Pass && cp3Pass && cp4Pass && cp5Pass && cp6Pass && cp7Pass && cp8Pass && cp9Pass)
    ? Math.round(90 + Math.random() * 10) : 0
  const cp10Pass = cp10Score >= 85

  // ── CP-11: PQC Receipt Issuance ───────────────────────────────────────
  const cp11Score = cp10Pass ? 100 : 0
  const cp11Pass = cp10Pass

  const overall = cp1Pass && cp2Pass && cp3Pass && cp4Pass && cp5Pass && cp6Pass && cp7Pass && cp8Pass && cp9Pass

  return [
    {
      name: 'CP-1 · Input Validation',
      icon: <Shield size={14} />,
      status: !cp1Pass ? 'block' : cp1Score >= 75 ? 'pass' : 'warn',
      score: cp1Score, threshold: 55,
      reasoning: c.amlFlag
        ? 'AML flag raised on input — hard block at intake before any processing'
        : cp1Pass
          ? `AVM data completeness: ${c.avmConfidence}% confidence · Price deviation: ${c.priceDeviation}% — inputs accepted`
          : `Insufficient AVM data quality (${cp1Score}/55) — comparable sources inadequate`,
      detail: 'Validates data completeness, AVM source quality, and pre-screens for immediate disqualifiers',
    },
    {
      name: 'CP-2 · AVM Confidence',
      icon: <TrendingUp size={14} />,
      status: cp2Pass ? 'pass' : cp2Score >= cp2Threshold * 0.8 ? 'warn' : 'block',
      score: cp2Score, threshold: cp2Threshold,
      reasoning: cp2Pass
        ? `AVM confidence ${cp2Score}/100 meets ${c.jurisdiction} threshold (${cp2Threshold}) — valuation model validated`
        : `AVM confidence ${cp2Score} below ${c.jurisdiction} minimum ${cp2Threshold} — jurisdiction ${jxData.strictness}x strictness applied`,
      detail: `${c.jurisdiction} regulatory strictness: ${jxData.strictness}× · Threshold: ${cp2Threshold} for ${c.decisionType}`,
    },
    {
      name: 'CP-3 · Transaction Risk',
      icon: <AlertTriangle size={14} />,
      status: ltvHardBlock ? 'block' : c.amlFlag ? 'block' : cp3Pass ? (cp3Score >= 55 ? 'pass' : 'warn') : 'block',
      score: cp3Score, threshold: 30,
      reasoning: ltvHardBlock
        ? `HARD BLOCK: LTV ${c.ltvRatio}% exceeds ${finData.label} maximum of ${finData.ltvMax}% (AAOIFI standard)`
        : c.amlFlag
          ? 'HARD BLOCK: AML alert — transaction frozen pending compliance investigation'
          : cp3Pass
            ? `Transaction risk ${cp3Score}/100 within safe limit · ${c.marketSegment} segment factor applied`
            : `Transaction risk too high (${cp3Score}/30) · AML score: ${c.amlRiskScore}%`,
      detail: `LTV limit: ${finData.ltvMax}% (${finData.label}) · Segment AML multiplier: ${segData.amlMod}× · Property risk: ${propData.riskMod}×`,
    },
    {
      name: 'CP-4 · Data Coherence',
      icon: <Activity size={14} />,
      status: !overall ? 'block' : cp4Pass ? 'pass' : 'warn',
      score: cp4Score, threshold: 58,
      reasoning: cp4Pass
        ? `Multi-source alignment ${cp4Score}/100 — AVM, comparables, and market data consistent`
        : `Signal incoherence detected (${cp4Score}/58) — price deviation ${c.priceDeviation}% causing misalignment`,
      detail: 'Cross-references AVM output with comparable sales data, market indices, and appraiser estimates',
    },
    {
      name: 'CP-5 · Market Trajectory',
      icon: <TrendingUp size={14} />,
      status: !overall ? 'block' : cp5Pass ? 'pass' : 'warn',
      score: cp5Score, threshold: 52,
      reasoning: cp5Pass
        ? `Market trajectory stable (${cp5Score}/100) · Trend: ${c.marketTrend}% · Liquidity: ${c.liquidityScore}`
        : `Adverse market conditions (${cp5Score}/52) — declining demand or oversupply risk`,
      detail: 'Evaluates price trend direction, demand vs supply dynamics, and absorption rate stability',
    },
    {
      name: 'CP-6 · Stress Resilience',
      icon: <Shield size={14} />,
      status: !overall ? 'block' : cp6Pass ? 'pass' : 'warn',
      score: cp6Score, threshold: 50,
      reasoning: cp6Pass
        ? `Asset resilience ${cp6Score}/100 — liquidity ${c.liquidityScore}, rate sensitivity adequate`
        : `Stress resilience insufficient (${cp6Score}/50) — illiquid asset with high rate sensitivity`,
      detail: 'Portfolio stress test: interest rate shock scenarios, vacancy risk, and market liquidity in downside',
    },
    {
      name: 'CP-7 · Regulatory Compliance',
      icon: <Lock size={14} />,
      status: c.amlFlag ? 'block' : !c.reraCompliant ? 'block'
        : (finData.shariaRequired && !c.shariaScreeningPassed) ? 'block'
        : cp7Pass ? 'pass' : 'warn',
      score: cp7Score, threshold: 65,
      reasoning: c.amlFlag
        ? 'HARD BLOCK: AML alert — FATF compliance violation'
        : !c.reraCompliant
          ? 'HARD BLOCK: RERA / regulatory non-compliance detected'
          : finData.shariaRequired && !c.shariaScreeningPassed
            ? `HARD BLOCK: Sharia parameter screening failed for ${finData.label} — Sharia Board clearance required`
            : !c.beneficialOwnerVerified
              ? 'UBO (Ultimate Beneficial Owner) verification incomplete — compliance hold'
              : `Regulatory alignment ${cp7Score}/100 — AML, ${c.jurisdiction} compliance, and ${finData.label} governance passed`,
      detail: `AML: FATF risk score ${c.amlRiskScore}% · RERA: ${c.reraCompliant ? '✓' : '✗'} · ${finData.shariaRequired ? `Sharia: ${c.shariaScreeningPassed ? '✓' : '✗'} · ` : ''}UBO: ${c.beneficialOwnerVerified ? '✓' : '✗'}`,
    },
    {
      name: 'CP-8 · Governance Score',
      icon: <BarChart3 size={14} />,
      status: !overall ? 'block' : cp8Pass ? 'pass' : 'warn',
      score: cp8Score, threshold: 60,
      reasoning: cp8Pass
        ? `Composite governance score ${cp8Score}/100 — all signal thresholds cleared`
        : `Composite score ${cp8Score} below minimum 60 — aggregate signal health insufficient`,
      detail: 'Weighted composite of all 6 OMNIX signals · Computed by 11-checkpoint engine identically across all domains',
    },
    {
      name: 'CP-9 · Stress-Adjusted Score',
      icon: <Activity size={14} />,
      status: !overall ? 'block' : cp9Pass ? 'pass' : 'warn',
      score: cp9Score, threshold: 55,
      reasoning: cp9Pass
        ? `Stress-adjusted score ${cp9Score}/100 — decision holds under adverse scenario loading`
        : `Score degrades to ${cp9Score} under stress loading — resilience insufficient`,
      detail: 'Applies downside scenario multipliers (AML amplification, liquidity crunch, market correction) to the governance score',
    },
    {
      name: 'CP-10 · Receipt Authorization',
      icon: <CheckCircle size={14} />,
      status: cp10Pass ? 'pass' : 'block',
      score: cp10Score, threshold: 85,
      reasoning: cp10Pass
        ? `Receipt authorized — decision passed all 9 prior checkpoints · Authorization score: ${cp10Score}`
        : 'Receipt authorization denied — one or more checkpoints failed',
      detail: 'Internal authorization gate: only decisions passing CP-1 through CP-9 receive a cryptographic receipt',
    },
    {
      name: 'CP-11 · PQC Receipt Issuance',
      icon: <Lock size={14} />,
      status: cp11Pass ? 'pass' : 'block',
      score: cp11Score, threshold: 100,
      reasoning: cp11Pass
        ? 'OMNIX-REP receipt sealed · CRYSTALS-Dilithium3 (NIST FIPS 204) · Immutable audit trail created'
        : 'Receipt not issued — governance pipeline blocked',
      detail: 'Post-quantum cryptographic seal using CRYSTALS-Dilithium3. Receipt prefix: OMNIX-REP. Verifiable at /verify',
    },
  ]
}

function BarChart3({ size }: { size: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>
    </svg>
  )
}

function Slider({ label, value, onChange, min = 0, max = 100, color = '#38bdf8', hint }: {
  label: string; value: number; onChange: (v: number) => void;
  min?: number; max?: number; color?: string; hint?: string
}) {
  const pct = ((value - min) / (max - min)) * 100
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontSize: 12, color: '#94a3b8' }}>{label}</span>
        <span style={{ fontSize: 13, color, fontWeight: 600 }}>{value}{max > 1 ? (min === 0 && max === 100 ? '' : '') : ''}</span>
      </div>
      <input
        type="range" min={min} max={max} value={value}
        onChange={e => onChange(Number(e.target.value))}
        style={{
          width: '100%', appearance: 'none', height: 4,
          background: `linear-gradient(to right, ${color} ${pct}%, rgba(255,255,255,0.12) ${pct}%)`,
          borderRadius: 2, outline: 'none', cursor: 'pointer',
        }}
      />
      {hint && <div style={{ fontSize: 10, color: '#475569', marginTop: 2 }}>{hint}</div>}
    </div>
  )
}

function Toggle({ label, value, onChange, blockLabel }: {
  label: string; value: boolean; onChange: (v: boolean) => void; blockLabel?: string
}) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.05)',
    }}>
      <div>
        <div style={{ fontSize: 12, color: '#94a3b8' }}>{label}</div>
        {blockLabel && <div style={{ fontSize: 10, color: '#f87171' }}>{blockLabel}</div>}
      </div>
      <button
        onClick={() => onChange(!value)}
        style={{
          width: 40, height: 22, borderRadius: 11, border: 'none', cursor: 'pointer',
          background: value ? '#34d399' : 'rgba(255,255,255,0.1)',
          position: 'relative', transition: 'background 0.2s',
        }}
      >
        <div style={{
          width: 16, height: 16, borderRadius: '50%', background: '#fff',
          position: 'absolute', top: 3,
          left: value ? 21 : 3, transition: 'left 0.2s',
        }} />
      </button>
    </div>
  )
}

const CP_COLORS = {
  pending:    { bg: 'rgba(148,163,184,0.06)', border: 'rgba(148,163,184,0.15)', text: '#475569' },
  evaluating: { bg: 'rgba(56,189,248,0.08)',  border: 'rgba(56,189,248,0.3)',   text: '#38bdf8' },
  pass:       { bg: 'rgba(52,211,153,0.08)',  border: 'rgba(52,211,153,0.25)',  text: '#34d399' },
  warn:       { bg: 'rgba(251,191,36,0.08)',  border: 'rgba(251,191,36,0.25)',  text: '#fbbf24' },
  block:      { bg: 'rgba(248,113,113,0.08)', border: 'rgba(248,113,113,0.3)',  text: '#f87171' },
}

export default function RealEstateGovernanceDemo() {
  const [c, setC] = useState<PropertyCase>({
    decisionType: 'mortgage_approval',
    propertyType: 'Residential',
    marketSegment: 'Mid_Market',
    jurisdiction: 'UAE',
    financingMode: 'Murabaha',
    avmConfidence: 80,
    priceDeviation: 8,
    ltvRatio: 76,
    marketTrend: 68,
    liquidityScore: 72,
    amlRiskScore: 15,
    amlFlag: false,
    reraCompliant: true,
    shariaScreeningPassed: true,
    beneficialOwnerVerified: true,
  })

  const [checkpoints, setCheckpoints] = useState<CheckpointResult[]>(() =>
    evaluatePropertyCheckpoints({
      decisionType: 'mortgage_approval',
      propertyType: 'Residential',
      marketSegment: 'Mid_Market',
      jurisdiction: 'UAE',
      financingMode: 'Murabaha',
      avmConfidence: 80,
      priceDeviation: 8,
      ltvRatio: 76,
      marketTrend: 68,
      liquidityScore: 72,
      amlRiskScore: 15,
      amlFlag: false,
      reraCompliant: true,
      shariaScreeningPassed: true,
      beneficialOwnerVerified: true,
    }).map(cp => ({ ...cp, status: 'pending' as const }))
  )

  const [running, setRunning]         = useState(false)
  const [activeIdx, setActiveIdx]     = useState(-1)
  const [receiptId, setReceiptId]     = useState<string | null>(null)
  const [finalOutcome, setFinalOutcome] = useState<'APPROVED' | 'BLOCKED' | 'HOLD' | null>(null)
  const abortRef = useRef(false)

  const finData = FINANCING_MODES.find(f => f.value === c.financingMode) || FINANCING_MODES[0]

  const update = (patch: Partial<PropertyCase>) => {
    if (running) return
    setC(prev => ({ ...prev, ...patch }))
    setCheckpoints(evaluatePropertyCheckpoints({ ...c, ...patch }).map(cp => ({ ...cp, status: 'pending' as const })))
    setReceiptId(null)
    setFinalOutcome(null)
    setActiveIdx(-1)
  }

  const runPipeline = async () => {
    if (running) return
    setRunning(true)
    abortRef.current = false
    setReceiptId(null)
    setFinalOutcome(null)

    const results = evaluatePropertyCheckpoints(c)
    const statuses: CheckpointResult[] = results.map(cp => ({ ...cp, status: 'pending' as const }))
    setCheckpoints([...statuses])

    for (let i = 0; i < results.length; i++) {
      if (abortRef.current) break
      setActiveIdx(i)
      setCheckpoints(prev => {
        const copy = [...prev]
        copy[i] = { ...copy[i], status: 'evaluating' }
        return copy
      })
      await new Promise(r => setTimeout(r, 480 + Math.random() * 280))
      if (abortRef.current) break
      setCheckpoints(prev => {
        const copy = [...prev]
        copy[i] = { ...results[i] }
        return copy
      })
    }

    if (!abortRef.current) {
      const allPassed = results.every(r => r.status === 'pass' || r.status === 'warn')
      const anyBlock  = results.some(r => r.status === 'block')
      const finalStatus = anyBlock ? 'BLOCKED' : allPassed ? 'APPROVED' : 'HOLD'
      setFinalOutcome(finalStatus)

      if (finalStatus !== 'BLOCKED') {
        const hex = Array.from({ length: 12 }, () => '0123456789ABCDEF'[Math.floor(Math.random() * 16)]).join('')
        setReceiptId(`OMNIX-REP-${hex}`)
      }
    }
    setActiveIdx(-1)
    setRunning(false)
  }

  const resetPipeline = () => {
    abortRef.current = true
    setRunning(false)
    setActiveIdx(-1)
    setReceiptId(null)
    setFinalOutcome(null)
    setCheckpoints(evaluatePropertyCheckpoints(c).map(cp => ({ ...cp, status: 'pending' as const })))
  }

  const completedCount = checkpoints.filter(cp => cp.status !== 'pending' && cp.status !== 'evaluating').length
  const passCount      = checkpoints.filter(cp => cp.status === 'pass' || cp.status === 'warn').length
  const blockCount     = checkpoints.filter(cp => cp.status === 'block').length
  const progress       = (completedCount / checkpoints.length) * 100

  return (
    <div style={{ minHeight: '100vh', background: '#0B0F1A', color: '#e2e8f0', fontFamily: 'system-ui, sans-serif' }}>
      <style>{`
        input[type=range]::-webkit-slider-thumb { appearance: none; width: 14px; height: 14px; border-radius: 50%; background: #38bdf8; cursor: pointer; border: 2px solid #0B0F1A; box-shadow: 0 0 6px #38bdf840; }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
        @keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }
      `}</style>

      {/* ── Header ── */}
      <div style={{
        background: 'rgba(56,189,248,0.06)',
        borderBottom: '1px solid rgba(56,189,248,0.15)',
        padding: '20px 32px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <Link to="/real-estate" style={{ color: '#64748b', display: 'flex', alignItems: 'center', gap: 6, textDecoration: 'none', fontSize: 13 }}>
            ← Dashboard
          </Link>
          <div style={{ width: 1, height: 20, background: '#1e293b' }} />
          <span style={{ fontSize: 22 }}>🏢</span>
          <div>
            <div style={{ fontWeight: 700, fontSize: 17, color: '#f1f5f9' }}>
              Real Estate Governance — Interactive Demo
            </div>
            <div style={{ fontSize: 12, color: '#38bdf8' }}>
              11-Checkpoint Pipeline · AVM · AML · Islamic Finance · RERA · PQC Receipt
            </div>
          </div>
        </div>
        <Link to="/real-estate" style={{
          padding: '8px 14px', borderRadius: 8,
          background: 'rgba(56,189,248,0.1)', border: '1px solid rgba(56,189,248,0.2)',
          color: '#38bdf8', textDecoration: 'none', fontSize: 13,
        }}>
          Live Dashboard →
        </Link>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: 0, maxHeight: 'calc(100vh - 80px)', overflow: 'hidden' }}>

        {/* ── Left Panel: Configuration ── */}
        <div style={{
          background: 'rgba(255,255,255,0.02)',
          borderRight: '1px solid rgba(255,255,255,0.07)',
          overflowY: 'auto', padding: '20px 22px',
        }}>
          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
              Decision Type
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {DECISION_TYPES.map(dt => (
                <button
                  key={dt.value}
                  disabled={running}
                  onClick={() => update({ decisionType: dt.value })}
                  style={{
                    padding: '9px 12px', borderRadius: 8, border: 'none', cursor: 'pointer',
                    background: c.decisionType === dt.value ? 'rgba(56,189,248,0.15)' : 'rgba(255,255,255,0.04)',
                    color: c.decisionType === dt.value ? '#38bdf8' : '#94a3b8',
                    textAlign: 'left', fontSize: 12, fontWeight: c.decisionType === dt.value ? 600 : 400,
                    border: `1px solid ${c.decisionType === dt.value ? 'rgba(56,189,248,0.3)' : 'rgba(255,255,255,0.06)'}`,
                    display: 'flex', alignItems: 'center', gap: 8,
                  }}
                >
                  <span>{dt.icon}</span> {dt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Property Type */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
              Property Type
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
              {PROPERTY_TYPES.map(pt => (
                <button
                  key={pt.value}
                  disabled={running}
                  onClick={() => update({ propertyType: pt.value })}
                  style={{
                    padding: '7px 10px', borderRadius: 7, border: 'none', cursor: 'pointer',
                    background: c.propertyType === pt.value ? 'rgba(56,189,248,0.12)' : 'rgba(255,255,255,0.04)',
                    color: c.propertyType === pt.value ? '#38bdf8' : '#64748b',
                    fontSize: 11, fontWeight: c.propertyType === pt.value ? 600 : 400,
                    border: `1px solid ${c.propertyType === pt.value ? 'rgba(56,189,248,0.25)' : 'rgba(255,255,255,0.05)'}`,
                  }}
                >
                  {pt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Market Segment */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
              Market Segment
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
              {MARKET_SEGMENTS.map(seg => (
                <button
                  key={seg.value}
                  disabled={running}
                  onClick={() => update({ marketSegment: seg.value })}
                  style={{
                    padding: '7px 10px', borderRadius: 7, border: 'none', cursor: 'pointer',
                    background: c.marketSegment === seg.value ? 'rgba(167,139,250,0.12)' : 'rgba(255,255,255,0.04)',
                    color: c.marketSegment === seg.value ? '#a78bfa' : '#64748b',
                    fontSize: 11, fontWeight: c.marketSegment === seg.value ? 600 : 400,
                    border: `1px solid ${c.marketSegment === seg.value ? 'rgba(167,139,250,0.25)' : 'rgba(255,255,255,0.05)'}`,
                  }}
                >
                  {seg.label}
                </button>
              ))}
            </div>
          </div>

          {/* Jurisdiction */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
              Jurisdiction
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {JURISDICTIONS.map(jx => (
                <button
                  key={jx.value}
                  disabled={running}
                  onClick={() => update({ jurisdiction: jx.value })}
                  style={{
                    padding: '7px 10px', borderRadius: 7, border: 'none', cursor: 'pointer',
                    background: c.jurisdiction === jx.value ? 'rgba(251,191,36,0.1)' : 'rgba(255,255,255,0.03)',
                    color: c.jurisdiction === jx.value ? '#fbbf24' : '#64748b',
                    fontSize: 11, textAlign: 'left', fontWeight: c.jurisdiction === jx.value ? 600 : 400,
                    border: `1px solid ${c.jurisdiction === jx.value ? 'rgba(251,191,36,0.2)' : 'rgba(255,255,255,0.05)'}`,
                  }}
                >
                  {jx.label}
                </button>
              ))}
            </div>
          </div>

          {/* Financing Mode */}
          {c.decisionType === 'mortgage_approval' && (
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
                Financing Mode
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {FINANCING_MODES.map(fm => (
                  <button
                    key={fm.value}
                    disabled={running}
                    onClick={() => update({ financingMode: fm.value })}
                    style={{
                      padding: '7px 10px', borderRadius: 7, border: 'none', cursor: 'pointer',
                      background: c.financingMode === fm.value ? 'rgba(192,132,252,0.12)' : 'rgba(255,255,255,0.03)',
                      color: c.financingMode === fm.value ? '#c084fc' : '#64748b',
                      fontSize: 11, textAlign: 'left', fontWeight: c.financingMode === fm.value ? 600 : 400,
                      border: `1px solid ${c.financingMode === fm.value ? 'rgba(192,132,252,0.25)' : 'rgba(255,255,255,0.05)'}`,
                    }}
                  >
                    {fm.label}
                    {fm.shariaRequired && (
                      <span style={{ marginLeft: 6, fontSize: 9, color: '#c084fc' }}>Sharia</span>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Sliders */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>
              Signal Parameters
            </div>
            <Slider label="AVM Confidence" value={c.avmConfidence} onChange={v => update({ avmConfidence: v })} color="#38bdf8" hint="Model accuracy / comparable quality" />
            <Slider label={`Price Deviation from AVM  ${c.priceDeviation}%`} value={c.priceDeviation} onChange={v => update({ priceDeviation: v })} color="#fb923c" hint="% gap between asking price and AVM estimate" />
            {c.decisionType === 'mortgage_approval' && (
              <Slider label={`LTV Ratio  ${c.ltvRatio}% (max: ${finData.ltvMax}%)`} value={c.ltvRatio} onChange={v => update({ ltvRatio: v })} color={c.ltvRatio > finData.ltvMax ? '#f87171' : '#a78bfa'} hint={`Hard block if > ${finData.ltvMax}% for ${finData.label}`} />
            )}
            <Slider label="Market Trend Score" value={c.marketTrend} onChange={v => update({ marketTrend: v })} color="#34d399" hint="0 = declining · 100 = rising" />
            <Slider label="Liquidity Score" value={c.liquidityScore} onChange={v => update({ liquidityScore: v })} color="#38bdf8" hint="Ease of exit in downside scenario" />
            <Slider label={`AML Risk Score  ${c.amlRiskScore}%`} value={c.amlRiskScore} onChange={v => update({ amlRiskScore: v })} color={c.amlRiskScore > 70 ? '#f87171' : '#fbbf24'} hint="FATF composite risk — >75 triggers AML flag" />
          </div>

          {/* Compliance Flags */}
          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
              Compliance Flags
            </div>
            <Toggle
              label="AML Flag Raised"
              value={c.amlFlag}
              onChange={v => update({ amlFlag: v })}
              blockLabel="→ HARD BLOCK on all checkpoints"
            />
            <Toggle
              label="RERA / Regulatory Compliant"
              value={c.reraCompliant}
              onChange={v => update({ reraCompliant: v })}
              blockLabel={!c.reraCompliant ? '→ HARD BLOCK at CP-7' : undefined}
            />
            {finData.shariaRequired && (
              <Toggle
                label="Sharia Parameter Screening"
                value={c.shariaScreeningPassed}
                onChange={v => update({ shariaScreeningPassed: v })}
                blockLabel={!c.shariaScreeningPassed ? '→ HARD BLOCK (Islamic financing)' : undefined}
              />
            )}
            <Toggle
              label="Beneficial Owner Verified (UBO)"
              value={c.beneficialOwnerVerified}
              onChange={v => update({ beneficialOwnerVerified: v })}
            />
          </div>

          {/* Run Button */}
          <button
            onClick={running ? resetPipeline : runPipeline}
            style={{
              width: '100%', padding: '13px 0', borderRadius: 10, border: 'none',
              cursor: 'pointer', fontWeight: 700, fontSize: 14, letterSpacing: 0.5,
              background: running
                ? 'rgba(248,113,113,0.15)'
                : 'linear-gradient(135deg, #0ea5e9, #38bdf8)',
              color: running ? '#f87171' : '#0B0F1A',
              transition: 'all 0.2s',
            }}
          >
            {running ? '⬛ Reset Pipeline' : '▶ Run 11-Checkpoint Governance'}
          </button>
        </div>

        {/* ── Right Panel: Pipeline ── */}
        <div style={{ overflowY: 'auto', padding: '20px 28px' }}>

          {/* Progress Bar */}
          <div style={{ marginBottom: 20 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <div style={{ fontSize: 12, color: '#64748b' }}>
                {running ? `Evaluating checkpoint ${activeIdx + 1} of 11…` : finalOutcome ? 'Pipeline complete' : 'Configure parameters and run the pipeline'}
              </div>
              <div style={{ fontSize: 12, color: '#94a3b8' }}>
                {passCount} pass · {blockCount} block · {completedCount}/11 evaluated
              </div>
            </div>
            <div style={{ height: 4, background: 'rgba(255,255,255,0.08)', borderRadius: 2, overflow: 'hidden' }}>
              <div style={{
                height: '100%', borderRadius: 2, transition: 'width 0.4s ease',
                width: `${progress}%`,
                background: blockCount > 0 ? '#f87171' : finalOutcome === 'APPROVED' ? '#34d399' : '#38bdf8',
              }} />
            </div>
          </div>

          {/* Final Outcome Banner */}
          {finalOutcome && (
            <div style={{
              marginBottom: 20, padding: '16px 20px', borderRadius: 12,
              background: finalOutcome === 'APPROVED'
                ? 'rgba(52,211,153,0.1)'
                : finalOutcome === 'BLOCKED'
                  ? 'rgba(248,113,113,0.1)'
                  : 'rgba(251,191,36,0.1)',
              border: `1px solid ${finalOutcome === 'APPROVED' ? 'rgba(52,211,153,0.3)' : finalOutcome === 'BLOCKED' ? 'rgba(248,113,113,0.3)' : 'rgba(251,191,36,0.3)'}`,
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            }}>
              <div>
                <div style={{
                  fontSize: 16, fontWeight: 700,
                  color: finalOutcome === 'APPROVED' ? '#34d399' : finalOutcome === 'BLOCKED' ? '#f87171' : '#fbbf24',
                }}>
                  {finalOutcome === 'APPROVED' ? '✓ TRANSACTION APPROVED' : finalOutcome === 'BLOCKED' ? '✗ TRANSACTION BLOCKED' : '⏸ COMPLIANCE REVIEW'}
                </div>
                {receiptId && (
                  <div style={{ fontSize: 11, color: '#64748b', marginTop: 4, fontFamily: 'monospace' }}>
                    {receiptId} · CRYSTALS-Dilithium3 (NIST FIPS 204)
                  </div>
                )}
                {finalOutcome === 'BLOCKED' && (
                  <div style={{ fontSize: 11, color: '#f87171', marginTop: 4 }}>
                    {checkpoints.find(cp => cp.status === 'block')?.reasoning?.slice(0, 120)}
                  </div>
                )}
              </div>
              {finalOutcome === 'APPROVED' && (
                <div style={{
                  padding: '6px 14px', borderRadius: 8,
                  background: 'rgba(52,211,153,0.15)',
                  border: '1px solid rgba(52,211,153,0.3)',
                  color: '#34d399', fontSize: 12, fontWeight: 600,
                }}>
                  Receipt Issued
                </div>
              )}
            </div>
          )}

          {/* Checkpoints Grid */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {checkpoints.map((cp, idx) => {
              const style = CP_COLORS[cp.status]
              const isActive = idx === activeIdx
              return (
                <div
                  key={cp.name}
                  style={{
                    background: style.bg,
                    border: `1px solid ${style.border}`,
                    borderRadius: 10, padding: '12px 16px',
                    transition: 'all 0.3s',
                    boxShadow: isActive ? `0 0 16px ${style.border}` : 'none',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    {/* Status Icon */}
                    <div style={{
                      width: 28, height: 28, borderRadius: 8, flexShrink: 0,
                      background: `${style.border}30`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      color: style.text,
                    }}>
                      {cp.status === 'pending'    && <Clock size={13} />}
                      {cp.status === 'evaluating' && <div style={{ width: 13, height: 13, borderRadius: '50%', border: `2px solid ${style.text}`, borderTopColor: 'transparent', animation: 'spin 0.7s linear infinite' }} />}
                      {cp.status === 'pass'       && <CheckCircle size={13} />}
                      {cp.status === 'warn'       && <AlertTriangle size={13} />}
                      {cp.status === 'block'      && <XCircle size={13} />}
                    </div>

                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span style={{ fontSize: 12, fontWeight: 600, color: style.text }}>
                          {cp.name}
                        </span>
                        {cp.status !== 'pending' && cp.status !== 'evaluating' && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <div style={{
                              width: 64, height: 4, background: 'rgba(255,255,255,0.08)',
                              borderRadius: 2, overflow: 'hidden',
                            }}>
                              <div style={{
                                width: `${Math.min(100, cp.score)}%`, height: '100%',
                                background: style.text, borderRadius: 2,
                                transition: 'width 0.6s ease',
                              }} />
                            </div>
                            <span style={{ fontSize: 11, color: style.text, fontWeight: 600, minWidth: 28 }}>
                              {cp.score}
                            </span>
                            <span style={{ fontSize: 10, color: '#475569' }}>
                              /{cp.threshold}
                            </span>
                          </div>
                        )}
                      </div>

                      {cp.status !== 'pending' && (
                        <div style={{ fontSize: 11, color: '#64748b', marginTop: 4, lineHeight: 1.4 }}>
                          {cp.reasoning}
                        </div>
                      )}
                      {(cp.status === 'pass' || cp.status === 'warn' || cp.status === 'block') && cp.detail && (
                        <div style={{ fontSize: 10, color: '#334155', marginTop: 3, fontStyle: 'italic' }}>
                          {cp.detail}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Footer note */}
          <div style={{
            marginTop: 24, padding: '12px 16px', borderRadius: 10,
            background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)',
            fontSize: 11, color: '#334155', lineHeight: 1.6,
          }}>
            ADR-RES-001 · OMNIX Real Estate Governance Vertical · Same 11-checkpoint engine as Trading, Islamic Credit, Insurance, Robotics, Medical AI, and Autonomous Agents · Receipt prefix: OMNIX-REP · PQC: CRYSTALS-Dilithium3 (NIST FIPS 204)
          </div>
        </div>
      </div>
    </div>
  )
}
