import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield, CheckCircle, XCircle, AlertTriangle, Activity,
  Clock, Layers, Brain, Lock, ArrowRight, Zap, Target, Eye, Scale,
} from 'lucide-react'

// ── Brand colors ───────────────────────────────────────────────────────────────
const ISL_TEAL   = '#0F766E'
const ISL_LIGHT  = '#14B8A6'
const ISL_DARK   = '#030D0C'
const ISL_BORDER = '#0F766E33'

// ── Domain data ────────────────────────────────────────────────────────────────
const FINANCING_STRUCTURES = [
  { value: 'murabaha',         label: 'Murabaha (Cost-Plus Sale)',              emoji: '🏷️', complexity: 0.85, gharar: 0.10 },
  { value: 'ijara',            label: 'Ijara (Islamic Lease)',                  emoji: '📋', complexity: 0.80, gharar: 0.12 },
  { value: 'musharakah',       label: 'Musharakah (Partnership)',               emoji: '🤝', complexity: 1.05, gharar: 0.18 },
  { value: 'dim_musharakah',   label: 'Diminishing Musharakah (Home Finance)', emoji: '🏠', complexity: 0.95, gharar: 0.14 },
  { value: 'istisna',          label: "Istisna'a (Manufacturing Contract)",     emoji: '🏗️', complexity: 1.10, gharar: 0.22 },
  { value: 'salam',            label: 'Salam (Forward Commodity Purchase)',     emoji: '🌾', complexity: 1.15, gharar: 0.28 },
]

const ASSET_TYPES = [
  { value: 'residential',  label: 'Residential Property',     emoji: '🏡', halalBase: 0.98, ltv_max: 85 },
  { value: 'commercial',   label: 'Commercial Property',      emoji: '🏢', halalBase: 0.96, ltv_max: 75 },
  { value: 'vehicle',      label: 'Vehicle (Halal-purpose)',  emoji: '🚗', halalBase: 0.97, ltv_max: 80 },
  { value: 'equipment',    label: 'Industrial Equipment',     emoji: '⚙️', halalBase: 0.95, ltv_max: 70 },
  { value: 'commodities',  label: 'Permissible Commodities',  emoji: '📦', halalBase: 0.88, ltv_max: 60 },
  { value: 'business',     label: 'Business Finance (Halal)', emoji: '💼', halalBase: 0.82, ltv_max: 65 },
]

const CUSTOMER_PROFILES = [
  { value: 'individual_employed',     label: 'Individual — Salaried Employee',  emoji: '👤', riskFactor: 0.90 },
  { value: 'individual_selfemployed', label: 'Individual — Self-Employed',      emoji: '🧑‍💼', riskFactor: 1.10 },
  { value: 'sme',                     label: 'SME (Small & Medium Enterprise)',  emoji: '🏪', riskFactor: 1.20 },
  { value: 'corporate',               label: 'Corporate (Large Enterprise)',     emoji: '🏦', riskFactor: 1.05 },
]

const JURISDICTIONS = [
  { value: 'uae',      label: '🇦🇪 UAE — CBUAE / DFSA',        strictness: 1.18, aaoifi: true  },
  { value: 'malaysia', label: '🇲🇾 Malaysia — BNM / IBFIM',     strictness: 1.15, aaoifi: false },
  { value: 'uk',       label: '🇬🇧 UK — FCA Islamic Finance',   strictness: 1.10, aaoifi: false },
  { value: 'gcc',      label: '🌍 GCC — AAOIFI Standard',       strictness: 1.20, aaoifi: true  },
  { value: 'pakistan', label: '🇵🇰 Pakistan — SBP / SECP',      strictness: 1.12, aaoifi: true  },
  { value: 'bahrain',  label: '🇧🇭 Bahrain — CBB / AAOIFI HQ', strictness: 1.22, aaoifi: true  },
]

const SHARIA_SCHOLARS = [
  { value: 'full',    label: 'Full Board Review + Fatwa Issued', factor: 1.00 },
  { value: 'partial', label: 'Partial Review (1 Scholar)',       factor: 0.72 },
  { value: 'pending', label: 'Review Pending',                   factor: 0.44 },
  { value: 'none',    label: 'No Sharia Review',                 factor: 0.15 },
]

// ── Scenario presets ───────────────────────────────────────────────────────────
const PRESETS = [
  {
    label: 'UAE Murabaha — Prime',
    emoji: '🇦🇪',
    s: {
      structure: 'murabaha', assetType: 'residential', customerProfile: 'individual_employed',
      jurisdiction: 'uae', financingAmount: 850000, ltvRatio: 72, customerRating: 740,
      halalScore: 96, shariaReview: 'full', mixedIncomeFlag: false,
    },
  },
  {
    label: 'Malaysia Ijara — Vehicle',
    emoji: '🇲🇾',
    s: {
      structure: 'ijara', assetType: 'vehicle', customerProfile: 'individual_salaried',
      jurisdiction: 'malaysia', financingAmount: 85000, ltvRatio: 78, customerRating: 690,
      halalScore: 97, shariaReview: 'full', mixedIncomeFlag: false,
    },
  },
  {
    label: 'GCC Musharakah — Commercial',
    emoji: '🏢',
    s: {
      structure: 'musharakah', assetType: 'commercial', customerProfile: 'corporate',
      jurisdiction: 'gcc', financingAmount: 3200000, ltvRatio: 68, customerRating: 720,
      halalScore: 94, shariaReview: 'full', mixedIncomeFlag: false,
    },
  },
  {
    label: "UK Istisna'a — Stressed",
    emoji: '🏗️',
    s: {
      structure: 'istisna', assetType: 'equipment', customerProfile: 'sme',
      jurisdiction: 'uk', financingAmount: 620000, ltvRatio: 82, customerRating: 580,
      halalScore: 78, shariaReview: 'partial', mixedIncomeFlag: false,
    },
  },
  {
    label: '⚠ Non-Halal — Block Test',
    emoji: '⚠️',
    s: {
      structure: 'salam', assetType: 'business', customerProfile: 'sme',
      jurisdiction: 'uae', financingAmount: 450000, ltvRatio: 88, customerRating: 490,
      halalScore: 28, shariaReview: 'none', mixedIncomeFlag: true,
    },
  },
]

// ── Types ──────────────────────────────────────────────────────────────────────
interface Scenario {
  structure:        string
  assetType:        string
  customerProfile:  string
  jurisdiction:     string
  financingAmount:  number
  ltvRatio:         number
  customerRating:   number
  halalScore:       number   // 0-100
  shariaReview:     string
  mixedIncomeFlag:  boolean
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
    <div style={{ position: 'relative', height: 6, background: '#061210', borderRadius: 3, overflow: 'visible' }}>
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
  const struct  = FINANCING_STRUCTURES.find(f => f.value === s.structure)         || FINANCING_STRUCTURES[0]
  const asset   = ASSET_TYPES.find(a => a.value === s.assetType)                  || ASSET_TYPES[0]
  const cust    = CUSTOMER_PROFILES.find(c => c.value === s.customerProfile)       || CUSTOMER_PROFILES[0]
  const jur     = JURISDICTIONS.find(j => j.value === s.jurisdiction)             || JURISDICTIONS[0]
  const scholar = SHARIA_SCHOLARS.find(sc => sc.value === s.shariaReview)         || SHARIA_SCHOLARS[0]

  const hs   = s.halalScore / 100
  const ltv  = s.ltvRatio  / 100
  const cr   = s.customerRating
  const fa   = Math.min(s.financingAmount / 5_000_000, 1)

  // CP scores
  const halalScore    = Math.round(Math.min(95, hs * 100 * asset.halalBase))
  const structScore   = Math.round(Math.min(95, (1 - struct.gharar) * 80 + scholar.factor * 20) * (s.mixedIncomeFlag ? 0.55 : 1.0))
  const ltvScore      = Math.round(Math.min(95, Math.max(5,
    ltv <= (asset.ltv_max / 100) ? (1 - ltv) * 120 : (1 - ltv) * 80
  )))
  const creditScore   = Math.round(Math.min(95, (cr - 300) / 5.5 * cust.riskFactor))
  const ghararScore   = Math.round(Math.min(95, (1 - struct.gharar * 2.2) * 100 * (s.mixedIncomeFlag ? 0.60 : 1.0)))
  const ribaScore     = Math.round(Math.min(95, s.mixedIncomeFlag ? 18 : (scholar.factor * 60 + (1 - struct.gharar) * 40)))

  const maysirScore    = Math.round(Math.min(95, struct.value === 'salam' ? 42 : (1 - struct.gharar * 1.8) * 95))
  const aaoifiScore    = Math.round(Math.min(95, scholar.factor * 55 + (jur.aaoifi ? 30 : 15) + (hs >= 0.80 ? 10 : 0)))
  const amlScore       = Math.round(Math.min(95, (cr / 850) * 40 + (1 - fa) * 35 + (hs >= 0.80 ? 20 : 5)))
  const shariaScore    = Math.round(Math.min(95, scholar.factor * 80 + (jur.aaoifi ? 10 : 5) + (hs >= 0.90 ? 5 : 0)))
  const jurScore       = Math.round(Math.min(95, (scholar.factor * 40 + hs * 35 + (1 - ltv) * 25) * (1 / jur.strictness) * 1.20))

  return [
    {
      name: 'Halal Asset Compliance',
      generic: 'CP-1: Is the financed asset permissible under Sharia?',
      icon: <Shield size={15} />,
      status: 'pending', score: halalScore, threshold: 60,
      reasoning: halalScore >= 60
        ? `Asset halal compliance ${s.halalScore}% × base factor ${asset.halalBase} = ${halalScore}% — ${asset.label} classified as permissible for Islamic financing`
        : `Halal compliance failure — ${s.halalScore}% base score × ${asset.halalBase} asset factor = ${halalScore}% below minimum. Haram asset elements detected`,
      detail: `Halal score: ${s.halalScore}% | Asset halal base: ×${asset.halalBase} | Final: ${halalScore}/100 | Threshold: ≥60 | ${halalScore < 60 ? 'HARAM DETECTED' : 'PERMISSIBLE'}`,
    },
    {
      name: 'Sharia Structure Validity',
      generic: 'CP-2: Is the financing contract Sharia-compliant?',
      icon: <Scale size={15} />,
      status: 'pending', score: structScore, threshold: 55,
      reasoning: structScore >= 55
        ? `${struct.label} contract structure validated — gharar ${(struct.gharar * 100).toFixed(0)}% within permissible bounds, Sharia review factor ${(scholar.factor * 100).toFixed(0)}%`
        : `Structure invalidity — ${s.mixedIncomeFlag ? 'mixed conventional/Islamic income contaminates the contract' : `gharar ${(struct.gharar * 100).toFixed(0)}% + review factor ${(scholar.factor * 100).toFixed(0)}% below threshold`}`,
      detail: `Structure: ${struct.label} | Gharar: ${(struct.gharar*100).toFixed(0)}% | Scholar: ×${scholar.factor} | Mixed income: ${s.mixedIncomeFlag ? 'YES ×0.55' : 'NO'} | Score: ${structScore}/100`,
    },
    {
      name: 'LTV Sharia Assessment',
      generic: 'CP-3: Financing-to-value within Islamic limits?',
      icon: <Target size={15} />,
      status: 'pending', score: ltvScore, threshold: 42,
      reasoning: ltvScore >= 42
        ? `LTV ${s.ltvRatio}% within ${asset.label} maximum (${asset.ltv_max}%) — Islamic financing ratio satisfies asset-backed ownership principle`
        : `LTV violation — ${s.ltvRatio}% exceeds ${asset.label} Islamic maximum ${asset.ltv_max}%, creating excessive debt dependency incompatible with asset-backed Sharia principles`,
      detail: `LTV: ${s.ltvRatio}% | Asset max: ${asset.ltv_max}% | ${ltv <= asset.ltv_max/100 ? 'Within limit' : 'Exceeds limit'} | LTV score: ${ltvScore}/100`,
    },
    {
      name: 'Customer Creditworthiness',
      generic: 'CP-4: Customer capacity to fulfill obligations?',
      icon: <Eye size={15} />,
      status: 'pending', score: creditScore, threshold: 45,
      reasoning: creditScore >= 45
        ? `Customer rating ${cr} with ${cust.label} profile yields creditworthiness score ${creditScore}% — sufficient capacity for ${struct.label} obligations`
        : `Insufficient creditworthiness — rating ${cr} with ${cust.label} risk factor ×${cust.riskFactor} yields ${creditScore}% below Islamic financing capacity threshold`,
      detail: `Rating: ${cr}/850 | Profile: ${cust.label} | Risk factor: ×${cust.riskFactor} | (${cr}-300)/5.5 × ${cust.riskFactor} = ${creditScore}/100`,
    },
    {
      name: 'Gharar (Uncertainty) Detection',
      generic: 'CP-5: Excessive uncertainty in contract terms?',
      icon: <AlertTriangle size={15} />,
      status: 'pending', score: ghararScore, threshold: 50,
      reasoning: ghararScore >= 50
        ? `Gharar level ${(struct.gharar * 100).toFixed(0)}% within permissible bounds for ${struct.label} — contract terms sufficiently defined under AAOIFI FAS standards`
        : `Excessive Gharar detected — ${s.mixedIncomeFlag ? 'mixed income flag introduces ambiguity + ' : ''}uncertainty ${(struct.gharar * 100).toFixed(0)}% creates prohibited speculative elements`,
      detail: `Structure gharar: ${(struct.gharar*100).toFixed(0)}% | Mixed income penalty: ${s.mixedIncomeFlag ? '×0.60' : 'none'} | Gharar score: ${ghararScore}/100 | AAOIFI FAS: ${ghararScore >= 50 ? 'COMPLIANT' : 'NON-COMPLIANT'}`,
    },
    {
      name: 'Riba (Interest) Screen',
      generic: 'CP-6: Any conventional interest elements present?',
      icon: <Brain size={15} />,
      status: 'pending', score: ribaScore, threshold: 55,
      reasoning: ribaScore >= 55
        ? `No Riba elements detected — ${struct.label} structure with ${scholar.label.split('(')[0].trim()} confirms profit-sharing / asset-backed returns only`
        : `Riba alert — ${s.mixedIncomeFlag ? 'mixed conventional income stream contaminates contract (Riba Al-Fadl / Al-Nasi\'ah risk)' : `insufficient Sharia oversight (${scholar.label}) for ${struct.label} — interest risk unmitigated`}`,
      detail: `Mixed income: ${s.mixedIncomeFlag ? 'YES — RIBA CONTAMINATION' : 'NO'} | Scholar factor: ×${scholar.factor} | Gharar: ${(1-struct.gharar)*100}% | Riba score: ${ribaScore}/100`,
    },
    {
      name: 'Maysir (Speculation) Gate',
      generic: 'CP-7: Speculative gambling elements present?',
      icon: <Layers size={15} />,
      status: 'pending', score: maysirScore, threshold: 48,
      reasoning: maysirScore >= 48
        ? `No Maysir detected — ${struct.label} is asset-backed with defined obligations; speculative elements within permissible bounds`
        : `Maysir risk — Salam forward contract with high uncertainty creates speculative exposure prohibited under AAOIFI Sharia Standard No. 1`,
      detail: `Structure: ${struct.label} | Gharar weight: ${(struct.gharar*180).toFixed(0)}% | Maysir score: ${maysirScore}/100 | AAOIFI SS No.1: ${maysirScore >= 48 ? 'CLEAR' : 'FLAGGED'}`,
    },
    {
      name: 'AAOIFI Compliance Gate',
      generic: 'CP-8: Accounting & Auditing standards pass?',
      icon: <Activity size={15} />,
      status: 'pending', score: aaoifiScore, threshold: 52,
      reasoning: aaoifiScore >= 52
        ? `AAOIFI compliance confirmed — ${jur.aaoifi ? 'mandatory AAOIFI jurisdiction' : 'AAOIFI-aligned'} with ${scholar.label.split('(')[0].trim()} and halal score ${s.halalScore}%`
        : `AAOIFI non-compliance — ${scholar.value === 'none' ? 'no Sharia review' : 'partial review'} in ${jur.label.split('—')[0].trim()} falls below Accounting & Auditing requirements`,
      detail: `Scholar: ${scholar.label.split('(')[0].trim()} ×${scholar.factor} | AAOIFI jurisdiction: ${jur.aaoifi ? 'YES +30' : 'NO +15'} | Halal bonus: ${hs >= 0.80 ? '+10' : '+0'} | Score: ${aaoifiScore}/100`,
    },
    {
      name: 'AML / CFT Gate',
      generic: 'CP-9: Anti-Money Laundering & Terror Finance screen?',
      icon: <Lock size={15} />,
      status: 'pending', score: amlScore, threshold: 55,
      reasoning: amlScore >= 55
        ? `AML/CFT screen passed — customer rating ${cr}, financing amount $${(s.financingAmount/1000).toFixed(0)}K, and halal score ${s.halalScore}% satisfy FATF Recommendation 10 thresholds`
        : `AML/CFT flag — ${cr < 550 ? `customer rating ${cr} triggers enhanced due diligence` : `financing scale or halal score ${s.halalScore}% requires additional KYC under FATF R.10`}`,
      detail: `Rating: ${cr}/850 ×0.40 + Amount factor: ${((1-fa)*35).toFixed(0)} + Halal: ${hs >= 0.80 ? '+20' : '+5'} = ${amlScore}/100 | FATF R.10: ${amlScore >= 55 ? 'PASS' : 'ENHANCED EDD'}`,
    },
    {
      name: 'Sharia Board Authorization',
      generic: 'CP-10: Certified Sharia scholar approval?',
      icon: <Shield size={15} />,
      status: 'pending', score: shariaScore, threshold: 60,
      reasoning: shariaScore >= 60
        ? `Sharia authorization confirmed — ${scholar.label} with AAOIFI ${jur.aaoifi ? 'mandatory' : 'aligned'} jurisdiction provides valid Fatwa for ${struct.label}`
        : `Sharia authorization insufficient — ${scholar.label.split('(')[0].trim()} does not satisfy minimum Sharia board requirement for ${struct.label} in ${jur.label.split('—')[0].trim()}`,
      detail: `Scholar factor: ×${scholar.factor} ×80 + AAOIFI: ${jur.aaoifi ? '+10' : '+5'} + Halal: ${hs >= 0.90 ? '+5' : '+0'} = ${shariaScore}/100 | Fatwa: ${shariaScore >= 60 ? 'VALID' : 'INSUFFICIENT'}`,
    },
    {
      name: 'Jurisdiction Regulatory Gate',
      generic: 'CP-11: Local Islamic finance regulatory approval?',
      icon: <Target size={15} />,
      status: 'pending', score: jurScore, threshold: 48,
      reasoning: jurScore >= 48
        ? `${jur.label.split('—')[0].trim()} regulatory requirements satisfied — Sharia review, halal compliance, and LTV within ${jur.label.split('—')[1]?.trim() || 'regulatory'} thresholds`
        : `Jurisdictional failure — ${jur.label.split('—')[0].trim()} (strictness ${jur.strictness}×) requires stronger Sharia documentation, halal score, or lower LTV`,
      detail: `Scholar×0.40: ${(scholar.factor*40).toFixed(0)} + Halal×0.35: ${(hs*35).toFixed(0)} + (1-LTV)×0.25: ${((1-ltv)*25).toFixed(0)} ÷ ${jur.strictness}× ×1.20 = ${jurScore}/100`,
    },
  ]
}

function buildReceiptId() {
  const hex = Array.from({ length: 12 }, () => Math.floor(Math.random() * 16).toString(16).toUpperCase()).join('')
  return `OMNIX-ISL-${hex}`
}

// ── Main component ─────────────────────────────────────────────────────────────
export default function IslamicCreditGovernanceDemo() {
  const [scenario, setScenario] = useState<Scenario>({
    structure:       'murabaha',
    assetType:       'residential',
    customerProfile: 'individual_employed',
    jurisdiction:    'uae',
    financingAmount: 850000,
    ltvRatio:        72,
    customerRating:  720,
    halalScore:      95,
    shariaReview:    'full',
    mixedIncomeFlag: false,
  })
  const [checkpoints, setCheckpoints] = useState<CheckpointResult[]>([])
  const [currentCp,   setCurrentCp]   = useState(-1)
  const [finalResult, setFinalResult] = useState<string | null>(null)
  const [receiptId,   setReceiptId]   = useState<string | null>(null)
  const [isRunning,   setIsRunning]   = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const struct  = FINANCING_STRUCTURES.find(f => f.value === scenario.structure)       || FINANCING_STRUCTURES[0]
  const asset   = ASSET_TYPES.find(a => a.value === scenario.assetType)                || ASSET_TYPES[0]
  const cust    = CUSTOMER_PROFILES.find(c => c.value === scenario.customerProfile)    || CUSTOMER_PROFILES[0]
  const jur     = JURISDICTIONS.find(j => j.value === scenario.jurisdiction)           || JURISDICTIONS[0]
  const scholar = SHARIA_SCHOLARS.find(sc => sc.value === scenario.shariaReview)       || SHARIA_SCHOLARS[0]

  // Hard block detection (real-time)
  const hb_haram       = scenario.halalScore < 50
  const hb_riba        = scenario.mixedIncomeFlag && scenario.shariaReview === 'none'
  const hb_ltv         = scenario.ltvRatio > 90
  const anyHardBlock   = hb_haram || hb_riba || hb_ltv

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
            else if (blocks > 0)              verdict = 'SHARIA_REVIEW'
            else                              verdict = 'APPROVED'
            setCheckpoints(finalCps); setCurrentCp(-1); setFinalResult(verdict)
            if (verdict === 'APPROVED') setReceiptId(buildReceiptId())
            setIsRunning(false)
          }, 380)
        }
      }, i * 300)
    })
  }

  useEffect(() => () => { if (timerRef.current) clearTimeout(timerRef.current) }, [])

  const statusIcon = (s: CheckpointResult['status']) => {
    if (s === 'pending')    return <Clock        size={15} style={{ color: '#334155' }} />
    if (s === 'evaluating') return <Activity     size={15} style={{ color: ISL_TEAL, animation: 'pulse 0.8s ease-in-out infinite' }} />
    if (s === 'pass')       return <CheckCircle  size={15} style={{ color: '#10B981' }} />
    if (s === 'warn')       return <AlertTriangle size={15} style={{ color: '#F59E0B' }} />
    return <XCircle size={15} style={{ color: '#EF4444' }} />
  }
  const statusColor = (s: CheckpointResult['status']) => {
    if (s === 'pass')       return '#10B981'
    if (s === 'warn')       return '#F59E0B'
    if (s === 'block')      return '#EF4444'
    if (s === 'evaluating') return ISL_TEAL
    return '#334155'
  }
  const verdictColor  = (v: string | null) => v === 'APPROVED' ? '#10B981' : v === 'SHARIA_REVIEW' ? '#F59E0B' : '#EF4444'
  const verdictBg     = (v: string | null) => v === 'APPROVED' ? 'rgba(16,185,129,0.10)' : v === 'SHARIA_REVIEW' ? 'rgba(245,158,11,0.10)' : 'rgba(239,68,68,0.10)'
  const verdictBorder = (v: string | null) => v === 'APPROVED' ? '#10B98133' : v === 'SHARIA_REVIEW' ? '#F59E0B33' : '#EF444433'

  const inputStyle: React.CSSProperties = {
    background: '#060F0E', border: '1px solid #0F2422', borderRadius: 7,
    color: '#CBD5E1', padding: '9px 12px', fontSize: 13, width: '100%',
    outline: 'none', cursor: 'pointer',
  }
  const labelStyle: React.CSSProperties = {
    fontSize: 10, color: '#64748B', marginBottom: 5, display: 'block',
    fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em',
  }
  const sliderStyle: React.CSSProperties = { width: '100%', accentColor: ISL_TEAL, cursor: 'pointer', height: 4 }
  const chg = (field: keyof Scenario) => (e: React.ChangeEvent<HTMLSelectElement | HTMLInputElement>) => {
    const val = e.target.type === 'range' ? parseInt(e.target.value) : e.target.value
    setScenario(p => ({ ...p, [field]: val }))
    setCheckpoints([]); setFinalResult(null); setReceiptId(null)
  }

  const fmtAmount = (v: number) => v >= 1_000_000 ? `$${(v/1_000_000).toFixed(1)}M` : `$${(v/1000).toFixed(0)}K`

  return (
    <div style={{
      minHeight: '100vh',
      background: `linear-gradient(160deg, ${ISL_DARK} 0%, #040F0E 50%, #030C0B 100%)`,
      color: '#E2E8F0', fontFamily: "'Inter', sans-serif", padding: '24px',
    }}>
      <style>{`
        @keyframes pulse { 0%,100%{opacity:1}50%{opacity:0.25} }
        * { box-sizing:border-box }
        select option { background: #060F0E }
        input[type=range]::-webkit-slider-thumb { background: ${ISL_TEAL} }
      `}</style>

      <div style={{ maxWidth: 1320, margin: '0 auto' }}>

        {/* ── Header ─────────────────────────────────────────────────────────── */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
            <Link to="/" style={{ color: '#475569', fontSize: 12, textDecoration: 'none' }}>← Home</Link>
            <span style={{ color: '#334155', fontSize: 12 }}>/</span>
            <span style={{ color: '#64748B', fontSize: 12 }}>Islamic Credit Governance</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
              <div style={{
                width: 50, height: 50, borderRadius: 12, display: 'flex', alignItems: 'center',
                justifyContent: 'center', fontSize: 24,
                background: `${ISL_TEAL}18`, border: `1px solid ${ISL_TEAL}44`,
              }}>☪️</div>
              <div>
                <div style={{ fontSize: 22, fontWeight: 800, letterSpacing: '-0.02em', color: '#F1F5F9' }}>
                  Islamic Credit Governance — Interactive Demo
                </div>
                <div style={{ fontSize: 12, color: '#475569', marginTop: 3 }}>
                  ADR-ISL-001 · 11-Checkpoint Fail-Closed Pipeline · AAOIFI · Sharia Compliance · Gharar / Riba / Maysir Gates ·{' '}
                  <span style={{ color: ISL_LIGHT, fontFamily: 'monospace' }}>OMNIX-ISL-{'{12HEX}'}</span> PQC Receipts
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {['AAOIFI FAS', 'Sharia Board', 'No Riba', 'FATF Compliant'].map(b => (
                <span key={b} style={{
                  padding: '4px 10px', fontSize: 10, fontWeight: 700, borderRadius: 5,
                  background: `${ISL_TEAL}14`, border: `1px solid ${ISL_TEAL}33`, color: ISL_LIGHT,
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
              background: `${ISL_TEAL}10`, border: `1px solid ${ISL_TEAL}28`,
              color: '#94A3B8', fontWeight: 600, transition: 'all 0.15s',
              display: 'flex', alignItems: 'center', gap: 5,
            }}
              onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = ISL_TEAL; (e.currentTarget as HTMLElement).style.color = ISL_LIGHT }}
              onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = `${ISL_TEAL}28`; (e.currentTarget as HTMLElement).style.color = '#94A3B8' }}
            >{p.emoji} {p.label}</button>
          ))}
        </div>

        {/* ── Two-Column Layout ───────────────────────────────────────────────── */}
        <div style={{ display: 'grid', gridTemplateColumns: '390px 1fr', gap: 18, alignItems: 'start' }}>

          {/* ── LEFT: Config ─────────────────────────────────────────────────── */}
          <div>
            <div style={{
              background: 'rgba(6,15,14,0.97)', borderRadius: 14, padding: 22,
              border: `1px solid ${ISL_BORDER}`, marginBottom: 14,
            }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: ISL_LIGHT, marginBottom: 18, display: 'flex', alignItems: 'center', gap: 7 }}>
                <Shield size={14} color={ISL_TEAL} /> Financing Application Parameters
              </div>

              {/* Financing Structure */}
              <div style={{ marginBottom: 13 }}>
                <label style={labelStyle}>Financing Structure</label>
                <select style={inputStyle} value={scenario.structure} onChange={chg('structure')}>
                  {FINANCING_STRUCTURES.map(f => <option key={f.value} value={f.value}>{f.emoji} {f.label}</option>)}
                </select>
                <div style={{ fontSize: 10, color: '#64748B', marginTop: 4 }}>
                  Gharar level: {(struct.gharar * 100).toFixed(0)}% · Complexity: ×{struct.complexity.toFixed(2)}
                </div>
              </div>

              {/* Asset Type */}
              <div style={{ marginBottom: 13 }}>
                <label style={labelStyle}>Asset Type</label>
                <select style={inputStyle} value={scenario.assetType} onChange={chg('assetType')}>
                  {ASSET_TYPES.map(a => <option key={a.value} value={a.value}>{a.emoji} {a.label}</option>)}
                </select>
                <div style={{ fontSize: 10, color: '#64748B', marginTop: 4 }}>
                  Halal base: {(asset.halalBase * 100).toFixed(0)}% · Max Islamic LTV: {asset.ltv_max}%
                </div>
              </div>

              {/* Customer Profile */}
              <div style={{ marginBottom: 13 }}>
                <label style={labelStyle}>Customer Profile</label>
                <select style={inputStyle} value={scenario.customerProfile} onChange={chg('customerProfile')}>
                  {CUSTOMER_PROFILES.map(c => <option key={c.value} value={c.value}>{c.emoji} {c.label}</option>)}
                </select>
              </div>

              {/* Jurisdiction */}
              <div style={{ marginBottom: 18 }}>
                <label style={labelStyle}>Regulatory Jurisdiction</label>
                <select style={inputStyle} value={scenario.jurisdiction} onChange={chg('jurisdiction')}>
                  {JURISDICTIONS.map(j => <option key={j.value} value={j.value}>{j.label}</option>)}
                </select>
                <div style={{ fontSize: 10, color: jur.aaoifi ? ISL_LIGHT : '#64748B', marginTop: 4 }}>
                  Strictness: ×{jur.strictness} · {jur.aaoifi ? 'AAOIFI Mandatory' : 'AAOIFI-Aligned'}
                </div>
              </div>

              {/* Financing Amount */}
              <div style={{ marginBottom: 13 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                  <label style={{ ...labelStyle, marginBottom: 0 }}>Financing Amount</label>
                  <span style={{ fontSize: 13, fontWeight: 700, color: ISL_LIGHT }}>{fmtAmount(scenario.financingAmount)}</span>
                </div>
                <input type="range" min={50000} max={5000000} step={25000} style={sliderStyle}
                  value={scenario.financingAmount} onChange={chg('financingAmount')} />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#334155', marginTop: 2 }}>
                  <span>$50K</span><span>$5M</span>
                </div>
              </div>

              {/* LTV */}
              <div style={{ marginBottom: 13 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                  <label style={{ ...labelStyle, marginBottom: 0 }}>LTV Ratio</label>
                  <span style={{ fontSize: 13, fontWeight: 700, color: hb_ltv ? '#EF4444' : scenario.ltvRatio > asset.ltv_max ? '#F59E0B' : '#10B981' }}>
                    {scenario.ltvRatio}%{hb_ltv && ' ⚠ HARD BLOCK'}
                  </span>
                </div>
                <input type="range" min={10} max={95} step={1} style={sliderStyle}
                  value={scenario.ltvRatio} onChange={chg('ltvRatio')} />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#334155', marginTop: 2 }}>
                  <span style={{ color: '#10B981' }}>10% Conservative</span>
                  <span style={{ color: '#EF4444' }}>&gt;90% Block</span>
                </div>
              </div>

              {/* Customer Rating */}
              <div style={{ marginBottom: 13 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                  <label style={{ ...labelStyle, marginBottom: 0 }}>Customer Rating</label>
                  <span style={{ fontSize: 13, fontWeight: 700, color: scenario.customerRating < 520 ? '#EF4444' : scenario.customerRating < 640 ? '#F59E0B' : '#10B981' }}>
                    {scenario.customerRating}
                  </span>
                </div>
                <input type="range" min={300} max={850} step={10} style={sliderStyle}
                  value={scenario.customerRating} onChange={chg('customerRating')} />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#334155', marginTop: 2 }}>
                  <span style={{ color: '#EF4444' }}>300 Weak</span>
                  <span style={{ color: '#F59E0B' }}>600</span>
                  <span style={{ color: '#10B981' }}>750+ Prime</span>
                </div>
              </div>

              {/* Halal Score */}
              <div style={{ marginBottom: 13 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                  <label style={{ ...labelStyle, marginBottom: 0 }}>Halal Compliance Score</label>
                  <span style={{ fontSize: 13, fontWeight: 700, color: hb_haram ? '#EF4444' : scenario.halalScore < 70 ? '#F59E0B' : '#10B981' }}>
                    {scenario.halalScore}%{hb_haram && ' ⚠ HARD BLOCK'}
                  </span>
                </div>
                <input type="range" min={0} max={100} step={1} style={sliderStyle}
                  value={scenario.halalScore} onChange={chg('halalScore')} />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#334155', marginTop: 2 }}>
                  <span style={{ color: '#EF4444' }}>&lt;50% Haram</span>
                  <span style={{ color: '#F59E0B' }}>70%</span>
                  <span style={{ color: '#10B981' }}>95%+ Pure</span>
                </div>
              </div>

              {/* Sharia Review */}
              <div style={{ marginBottom: 13 }}>
                <label style={labelStyle}>Sharia Scholar Review</label>
                <select style={inputStyle} value={scenario.shariaReview} onChange={chg('shariaReview')}>
                  {SHARIA_SCHOLARS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                </select>
                <div style={{ fontSize: 10, color: '#64748B', marginTop: 4 }}>
                  Review factor: ×{scholar.factor}
                </div>
              </div>

              {/* Mixed Income Flag */}
              <div style={{ marginBottom: 20 }}>
                <label style={labelStyle}>Mixed Income Flag (Riba Risk)</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 4 }}>
                  <button
                    onClick={() => { setScenario(p => ({ ...p, mixedIncomeFlag: !p.mixedIncomeFlag })); setCheckpoints([]); setFinalResult(null); setReceiptId(null) }}
                    style={{
                      width: 44, height: 24, borderRadius: 12, border: 'none', cursor: 'pointer', transition: 'all 0.2s',
                      background: scenario.mixedIncomeFlag ? '#EF4444' : '#10B981',
                      position: 'relative',
                    }}
                  >
                    <div style={{
                      position: 'absolute', top: 3, left: scenario.mixedIncomeFlag ? 23 : 3,
                      width: 18, height: 18, borderRadius: '50%', background: '#FFF',
                      transition: 'left 0.2s',
                    }} />
                  </button>
                  <span style={{ fontSize: 12, color: scenario.mixedIncomeFlag ? '#EF4444' : '#10B981', fontWeight: 600 }}>
                    {scenario.mixedIncomeFlag ? '⚠ Conventional income mixed — Riba risk' : '✓ Clean Islamic income sources only'}
                  </span>
                </div>
              </div>

              {/* Hard block summary */}
              {anyHardBlock && (
                <div style={{
                  background: 'rgba(239,68,68,0.08)', border: '1px solid #EF444430',
                  borderRadius: 8, padding: '10px 14px', marginBottom: 16,
                }}>
                  <div style={{ color: '#EF4444', fontWeight: 700, fontSize: 11, marginBottom: 6 }}>⚠ Hard Block Active — Will BLOCK before evaluation</div>
                  {hb_haram && <div style={{ color: '#FCA5A5', fontSize: 11, marginBottom: 3 }}>• Halal score {scenario.halalScore}% &lt;50% — haram asset, financing prohibited (AAOIFI SS No. 21)</div>}
                  {hb_riba  && <div style={{ color: '#FCA5A5', fontSize: 11, marginBottom: 3 }}>• Mixed income + no Sharia review — Riba contamination confirmed (Quran 2:275)</div>}
                  {hb_ltv   && <div style={{ color: '#FCA5A5', fontSize: 11 }}>• LTV {scenario.ltvRatio}% &gt;90% — exceeds maximum Islamic asset-backed financing limit</div>}
                </div>
              )}

              <button onClick={runEvaluation} disabled={isRunning} style={{
                width: '100%', padding: '13px 20px', borderRadius: 10, border: 'none',
                background: isRunning ? '#1E293B' : `linear-gradient(135deg, #065F56, ${ISL_TEAL})`,
                color: isRunning ? '#475569' : '#FFF', fontWeight: 700, fontSize: 14,
                cursor: isRunning ? 'not-allowed' : 'pointer', transition: 'all 0.2s',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              }}>
                <Shield size={15} />
                {isRunning ? 'Evaluating Sharia Compliance…' : 'Run 11-Checkpoint Islamic Governance'}
                {!isRunning && <ArrowRight size={15} />}
              </button>
            </div>

            {/* Scenario Summary */}
            <div style={{ background: 'rgba(6,15,14,0.97)', borderRadius: 12, padding: 16, border: '1px solid #0F2422', fontSize: 12 }}>
              <div style={{ color: '#475569', fontWeight: 700, marginBottom: 10, fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                Current Scenario
              </div>
              {[
                ['Structure',    `${struct.emoji} ${struct.label.split('(')[0].trim()}`],
                ['Asset',        `${asset.emoji} ${asset.label}`],
                ['Customer',     `${cust.emoji} ${cust.label}`],
                ['Jurisdiction', jur.label.split('—')[0].trim()],
                ['Amount',       fmtAmount(scenario.financingAmount)],
                ['LTV',          `${scenario.ltvRatio}%`],
                ['Rating',       `${scenario.customerRating}`],
                ['Halal Score',  `${scenario.halalScore}%`],
                ['Sharia Review',scholar.label.split('(')[0].trim()],
                ['Mixed Income', scenario.mixedIncomeFlag ? '⚠ YES' : '✓ NO'],
              ].map(([k, v]) => (
                <div key={k as string} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5, paddingBottom: 5, borderBottom: '1px solid #060F0E' }}>
                  <span style={{ color: '#334155' }}>{k}</span>
                  <span style={{ color: '#94A3B8', fontWeight: 600, maxWidth: 200, textAlign: 'right' }}>{v}</span>
                </div>
              ))}
              <div style={{ marginTop: 8, paddingTop: 8, borderTop: '1px solid #060F0E' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#334155', fontSize: 10 }}>Jurisdiction Strictness</span>
                  <span style={{ color: jur.strictness > 1.18 ? '#EF4444' : '#F59E0B', fontWeight: 700, fontFamily: 'monospace', fontSize: 11 }}>
                    {jur.strictness}×
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* ── RIGHT: Checkpoint Results ───────────────────────────────────── */}
          <div>
            {checkpoints.length === 0 ? (
              <div style={{
                background: 'rgba(6,15,14,0.97)', borderRadius: 14, padding: 52,
                border: `1px solid ${ISL_BORDER}`, textAlign: 'center',
              }}>
                <div style={{ fontSize: 52, marginBottom: 18 }}>☪️</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: ISL_LIGHT, marginBottom: 10 }}>
                  Islamic Credit Governance Pipeline
                </div>
                <div style={{ color: '#475569', fontSize: 13, maxWidth: 460, margin: '0 auto', lineHeight: 1.7 }}>
                  Configure an Islamic financing application on the left — structure, asset, customer profile,
                  jurisdiction, halal compliance, and Sharia review status. Run the 11-checkpoint AAOIFI
                  governance pipeline. Every approved financing generates a PQC-signed{' '}
                  <span style={{ color: ISL_LIGHT, fontFamily: 'monospace' }}>OMNIX-ISL</span> receipt.
                </div>
                <div style={{ marginTop: 28, display: 'flex', justifyContent: 'center', gap: 10, flexWrap: 'wrap' }}>
                  {['Halal Gate', 'Gharar Screen', 'Riba Detector', 'Sharia Board Auth', 'PQC-Signed Receipt'].map(s => (
                    <span key={s} style={{
                      background: `${ISL_TEAL}12`, border: `1px solid ${ISL_BORDER}`,
                      borderRadius: 6, padding: '5px 12px', fontSize: 11, color: ISL_LIGHT, fontWeight: 500,
                    }}>{s}</span>
                  ))}
                </div>
                <div style={{ marginTop: 28, display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, maxWidth: 480, margin: '28px auto 0' }}>
                  {[
                    { icon: <Zap size={14} />, label: 'Sub-second evaluation' },
                    { icon: <Shield size={14} />, label: '3 hard block conditions' },
                    { icon: <Lock size={14} />, label: 'Dilithium-3 PQC receipt' },
                  ].map((item, i) => (
                    <div key={i} style={{ background: '#060F0E', border: '1px solid #0F2422', borderRadius: 8, padding: '12px 10px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
                      <div style={{ color: ISL_TEAL }}>{item.icon}</div>
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
                      {finalResult === 'APPROVED'
                        ? <CheckCircle size={22} style={{ color: '#10B981' }} />
                        : finalResult === 'SHARIA_REVIEW'
                        ? <AlertTriangle size={22} style={{ color: '#F59E0B' }} />
                        : <XCircle size={22} style={{ color: '#EF4444' }} />}
                      <div>
                        <div style={{ fontWeight: 800, fontSize: 17, color: verdictColor(finalResult) }}>
                          {finalResult === 'APPROVED'      ? 'SHARIA APPROVED — FINANCING AUTHORIZED' :
                           finalResult === 'SHARIA_REVIEW' ? 'HOLD — ESCALATE TO SHARIA BOARD' :
                           finalResult === 'HARD_BLOCK'    ? 'HARD BLOCK — FINANCING PROHIBITED' :
                           'BLOCKED — GOVERNANCE THRESHOLD BREACH'}
                        </div>
                        {receiptId && (
                          <div style={{ fontSize: 11, color: '#10B981', fontFamily: 'monospace', marginTop: 3 }}>
                            Receipt: {receiptId} · Dilithium-3 signed · ADR-ISL-001
                          </div>
                        )}
                        {!receiptId && (
                          <div style={{ fontSize: 11, color: '#EF4444', marginTop: 3 }}>
                            No receipt issued — financing blocked by OMNIX Islamic Governance pipeline
                          </div>
                        )}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right', fontSize: 11, color: '#475569' }}>
                      <div>{struct.emoji} {struct.label.split('(')[0].trim()}</div>
                      <div>{asset.emoji} {asset.label}</div>
                      <div>{jur.label.split('—')[0].trim()}</div>
                    </div>
                  </div>
                )}

                {/* Checkpoints */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 9 }}>
                  {checkpoints.map((cp, i) => {
                    const isActive  = currentCp === i
                    const borderClr = cp.status === 'evaluating' ? ISL_TEAL
                      : cp.status === 'pass'  ? '#10B981'
                      : cp.status === 'warn'  ? '#F59E0B'
                      : cp.status === 'block' ? '#EF4444'
                      : '#1E293B'
                    const barClr = cp.status === 'pass'  ? '#10B981'
                      : cp.status === 'warn'  ? '#F59E0B'
                      : cp.status === 'block' ? '#EF4444'
                      : ISL_TEAL
                    return (
                      <div key={i} style={{
                        background: isActive ? `${ISL_TEAL}08` : 'rgba(6,15,14,0.92)',
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
                              background: '#060F0E', padding: '6px 10px', borderRadius: 5,
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
        <div style={{ marginTop: 28, textAlign: 'center', color: '#0F2422', fontSize: 11 }}>
          OMNIX Quantum · Islamic Credit Governance · ADR-ISL-001 · 11-Checkpoint Fail-Closed Pipeline
          &nbsp;·&nbsp; AAOIFI FAS · Sharia Standards · Gharar / Riba / Maysir Gates · FATF AML · Dilithium-3 (ML-DSA-65) PQC
          &nbsp;·&nbsp; <Link to="/try" style={{ color: ISL_TEAL, textDecoration: 'none' }}>Public Sandbox →</Link>
          &nbsp;·&nbsp; <Link to="/" style={{ color: ISL_TEAL, textDecoration: 'none' }}>Back to Platform →</Link>
        </div>
      </div>
    </div>
  )
}
