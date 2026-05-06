import { useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield, CheckCircle, XCircle, AlertTriangle, Activity, Clock,
  Building2, CreditCard, TrendingUp, Layers, Target, Brain, ArrowRight, Zap, Lock,
} from 'lucide-react'

const CRD_GREEN  = '#10B981'
const CRD_LIGHT  = '#34D399'
const CRD_DARK   = '#080F0A'
const CRD_BORDER = '#10B98133'

const SECTORS = [
  { value: 'technology',     label: 'Technology',      emoji: '💻', risk: 0.12 },
  { value: 'healthcare',     label: 'Healthcare',      emoji: '🏥', risk: 0.08 },
  { value: 'retail',         label: 'Retail',          emoji: '🛍️', risk: 0.22 },
  { value: 'real_estate',    label: 'Real Estate',     emoji: '🏠', risk: 0.18 },
  { value: 'energy',         label: 'Energy',          emoji: '⚡', risk: 0.25 },
  { value: 'manufacturing',  label: 'Manufacturing',   emoji: '🏭', risk: 0.15 },
]

const INCOME_STABILITY = [
  { value: 'stable_growing', label: 'Stable & Growing (2+ years)', factor: 0.95 },
  { value: 'stable',         label: 'Stable (1-2 years)',          factor: 0.80 },
  { value: 'variable',       label: 'Variable / Contract',         factor: 0.55 },
  { value: 'declining',      label: 'Declining Trend',             factor: 0.30 },
]

const MARKET_CONDITIONS = [
  { value: 'expansion',    label: 'Economic Expansion',      factor: 0.90 },
  { value: 'stable',       label: 'Stable / Neutral',        factor: 0.75 },
  { value: 'uncertainty',  label: 'Elevated Uncertainty',    factor: 0.45 },
  { value: 'contraction',  label: 'Contraction / Recession', factor: 0.20 },
]

interface LoanApp {
  loanAmount:       number
  creditScore:      number
  dtiRatio:         number
  sector:           string
  incomeStability:  string
  marketCondition:  string
}

const PRESETS: { label: string; emoji: string; s: LoanApp }[] = [
  { label: 'Tech Startup — Prime',      emoji: '💻', s: { loanAmount: 150000, creditScore: 760, dtiRatio: 28, sector: 'technology',    incomeStability: 'stable_growing', marketCondition: 'expansion'   } },
  { label: 'Healthcare Professional',   emoji: '🏥', s: { loanAmount: 350000, creditScore: 730, dtiRatio: 35, sector: 'healthcare',     incomeStability: 'stable',         marketCondition: 'stable'      } },
  { label: 'Retail SME — Stressed',     emoji: '🛍️', s: { loanAmount: 200000, creditScore: 610, dtiRatio: 48, sector: 'retail',         incomeStability: 'variable',       marketCondition: 'uncertainty' } },
  { label: 'Real Estate Investor',      emoji: '🏠', s: { loanAmount: 750000, creditScore: 690, dtiRatio: 42, sector: 'real_estate',    incomeStability: 'stable',         marketCondition: 'stable'      } },
  { label: 'Manufacturing — Block Test',emoji: '⚠️', s: { loanAmount: 900000, creditScore: 490, dtiRatio: 58, sector: 'energy',         incomeStability: 'declining',      marketCondition: 'contraction' } },
]

interface CP {
  name: string; genericName: string; icon: React.ReactNode
  status: 'pending'|'evaluating'|'pass'|'warn'|'block'
  score: number; threshold: number; reasoning: string; detail: string
}

function buildCheckpoints(app: LoanApp): CP[] {
  const sec  = SECTORS.find(s => s.value === app.sector) || SECTORS[0]
  const inc  = INCOME_STABILITY.find(i => i.value === app.incomeStability) || INCOME_STABILITY[0]
  const mkt  = MARKET_CONDITIONS.find(m => m.value === app.marketCondition) || MARKET_CONDITIONS[0]
  const baseDefaultProb = (1 - (app.creditScore - 300) / 550) * 0.3
  const dtiPenalty = app.dtiRatio > 43 ? (app.dtiRatio - 43) * 0.008 : 0
  const adjustedDefault = Math.min(0.95, Math.max(0.01, baseDefaultProb + sec.risk * 0.3 + dtiPenalty))
  const probabilityScore = Math.round((1 - adjustedDefault) * 100)
  const loanToIncome = app.loanAmount / 80000
  const sectorExposure = sec.risk * 100
  const concentrationRisk = Math.min(100, Math.round(loanToIncome * 20 + sectorExposure * 1.5))
  const riskScore = 100 - concentrationRisk
  const creditSignal = app.creditScore >= 700 ? 90 : app.creditScore >= 650 ? 70 : app.creditScore >= 580 ? 50 : 30
  const dtiSignal = app.dtiRatio <= 30 ? 90 : app.dtiRatio <= 43 ? 65 : app.dtiRatio <= 50 ? 40 : 20
  const sectorSignal = (1 - sec.risk) * 100
  const coherenceScore = Math.round(creditSignal * 0.35 + dtiSignal * 0.30 + sectorSignal * 0.35)
  const trendScore = Math.round(inc.factor * 100)
  const stressScore = Math.round(mkt.factor * 100)
  const signals = [probabilityScore, riskScore, coherenceScore, trendScore, stressScore]
  const avg = signals.reduce((a, b) => a + b, 0) / signals.length
  const variance = signals.reduce((a, b) => a + Math.pow(b - avg, 2), 0) / signals.length
  const divergence = Math.sqrt(variance)
  const logicScore = Math.round(Math.max(0, Math.min(100, 100 - divergence * 1.8)))
  const sivScore = Math.min(95, Math.round(70 + (app.creditScore - 300) / 550 * 20))
  const temporalScore = Math.min(95, Math.round(inc.factor * 70 + mkt.factor * 30))
  const edgeScore = Math.round(probabilityScore * 0.55 + logicScore * 0.45)
  const amlScore = Math.min(95, Math.round(90 - Math.max(0, (app.loanAmount - 300000) / 200000 * 20)))
  const fraudScore = Math.min(95, Math.round(65 + coherenceScore * 0.30))
  return [
    { name:'Signal Integrity Validation', genericName:'CP-1: All input signals valid?', icon:<Shield size={15}/>, status:'pending', score:sivScore, threshold:60, reasoning:sivScore>=60?`Signals validated — credit score, DTI, sector, income, market inputs internally consistent`:`Validation failed — one or more parameters outside governance bounds`, detail:`6/6 signals valid | Credit range factor: ${Math.round((app.creditScore-300)/550*100)}% | SIV: ${sivScore}/100` },
    { name:'Default Probability',          genericName:'CP-2: Likelihood of repayment?',  icon:<Target size={15}/>,  status:'pending', score:probabilityScore, threshold:70, reasoning:probabilityScore>=70?`P(default) = ${(adjustedDefault*100).toFixed(1)}% — within acceptable risk range`:`P(default) = ${(adjustedDefault*100).toFixed(1)}% exceeds approved risk threshold`, detail:`FICO ${app.creditScore} + sector risk ${(sec.risk*100).toFixed(0)}% + DTI impact → P(repay)=${probabilityScore}%` },
    { name:'Portfolio Exposure Limits',    genericName:'CP-3: Concentration risk safe?',  icon:<Shield size={15}/>,  status:'pending', score:riskScore, threshold:55, reasoning:riskScore>=55?`Exposure within concentration limits`:`Concentration risk elevated — ${sec.label} at ${(sec.risk*100).toFixed(0)}% sector weight`, detail:`Loan/income: ${loanToIncome.toFixed(1)}× | Sector exposure: ${sectorExposure.toFixed(0)}% | Risk: ${riskScore}/100` },
    { name:'Multi-Signal Coherence',       genericName:'CP-4: Do models agree?',          icon:<Layers size={15}/>,  status:'pending', score:coherenceScore, threshold:50, reasoning:coherenceScore>=50?`Credit, DTI, sector signals agree at ${coherenceScore}%`:`Conflicting signals — credit ${creditSignal>=70?'OK':'WEAK'} / DTI ${app.dtiRatio}% / sector diverge`, detail:`Credit: ${creditSignal} | DTI: ${dtiSignal} | Sector: ${Math.round(sectorSignal)} → Coherence: ${coherenceScore}%` },
    { name:'Income Trend Persistence',     genericName:'CP-5: Sustained trend, not noise?',icon:<TrendingUp size={15}/>,status:'pending', score:trendScore, threshold:50, reasoning:trendScore>=50?`Income trend (${inc.label}) confirms borrower stability`:`Income trend (${inc.label}) doesn't confirm sustained repayment capacity`, detail:`Stability factor: ${(inc.factor*100).toFixed(0)}% → Trend persistence: ${trendScore}/100` },
    { name:'Macro Stress Test',            genericName:'CP-6: Resilient to deterioration?',icon:<AlertTriangle size={15}/>,status:'pending', score:stressScore, threshold:40, reasoning:stressScore>=40?`Market conditions (${mkt.label}) — adequate resilience under stress`:`Market (${mkt.label}) — high vulnerability to deterioration`, detail:`Market factor: ${(mkt.factor*100).toFixed(0)}% → Stress resilience: ${stressScore}/100` },
    { name:'Signal Contradiction (SCG)',   genericName:'CP-7: Contradicting signals?',    icon:<Brain size={15}/>,   status:'pending', score:logicScore, threshold:45, reasoning:logicScore>=45?`Internal divergence low — signals consistent (${logicScore}%)`:`High contradiction — divergence ${divergence.toFixed(1)} signals conflicting risk assessment`, detail:`Variance: ${divergence.toFixed(1)} | Consistency: ${logicScore}% | ${logicScore<45?'CONTRADICTORY':logicScore<65?'TENSIONED':'ALIGNED'}` },
    { name:'Temporal Coherence',           genericName:'CP-8: Holds across time?',        icon:<Activity size={15}/>, status:'pending', score:temporalScore, threshold:45, reasoning:temporalScore>=45?`Historical income and market patterns support temporal consistency`:`Pattern inconsistency — current conditions may be transient`, detail:`Income stability: ${(inc.factor*100).toFixed(0)}% | Market: ${(mkt.factor*100).toFixed(0)}% | Temporal: ${temporalScore}/100` },
    { name:'Edge Confirmation (ECW)',      genericName:'CP-9: Decision converges at boundary?',icon:<Target size={15}/>,status:'pending', score:edgeScore, threshold:48, reasoning:edgeScore>=48?`Boundary confirmed — probability and logic converge at governance edge (${edgeScore}%)`:`Weak boundary — signals don't reinforce at decision threshold`, detail:`Probability×0.55: ${(probabilityScore*0.55).toFixed(0)} | Logic×0.45: ${(logicScore*0.45).toFixed(0)} | Edge: ${edgeScore}/100` },
    { name:'AML Compliance Gate',          genericName:'CP-10: Passes AML screening?',    icon:<Building2 size={15}/>,status:'pending', score:amlScore, threshold:60, reasoning:amlScore>=60?`AML screen passed — loan size and sector show no anomalous patterns`:`AML flag — loan size/sector requires enhanced due diligence`, detail:`Loan: $${(app.loanAmount/1000).toFixed(0)}K | Sector flag: ${sec.risk>0.20?'ELEVATED':'NORMAL'} | AML: ${amlScore}/100` },
    { name:'Fraud Detection Gate',         genericName:'CP-11: Anomalous signal patterns?',icon:<AlertTriangle size={15}/>,status:'pending', score:fraudScore, threshold:55, reasoning:fraudScore>=55?`Fraud screen passed — no anomalous behavioral patterns`:`Fraud pattern detected — low coherence indicates possible misrepresentation`, detail:`Coherence base: ${coherenceScore} | Fraud score: ${fraudScore}/100 | ${fraudScore<55?'ELEVATED — manual review':'CLEAN PROFILE'}` },
  ]
}

function buildReceiptId() {
  return `OMNIX-CRD-${Array.from({length:12},()=>Math.floor(Math.random()*16).toString(16).toUpperCase()).join('')}`
}

function ScoreBar({ score, threshold, color }: { score:number; threshold:number; color:string }) {
  return (
    <div style={{ position:'relative', height:6, background:'#0F1E0F', borderRadius:3, overflow:'visible' }}>
      <div style={{ position:'absolute', left:`${threshold}%`, top:-3, width:2, height:12, background:'#F59E0B', borderRadius:1, zIndex:2 }}/>
      <div style={{ height:'100%', width:`${Math.min(score,100)}%`, background:color, borderRadius:3, transition:'width 0.9s ease' }}/>
    </div>
  )
}

export default function CreditGovernanceDemo() {
  const [app, setApp] = useState<LoanApp>({ loanAmount:200000, creditScore:720, dtiRatio:35, sector:'technology', incomeStability:'stable_growing', marketCondition:'stable' })
  const [checkpoints, setCheckpoints] = useState<CP[]>([])
  const [currentCp, setCurrentCp]   = useState(-1)
  const [finalResult, setFinalResult] = useState<string|null>(null)
  const [receiptId, setReceiptId]   = useState<string|null>(null)
  const [isRunning, setIsRunning]   = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout>|null>(null)

  const sec = SECTORS.find(s=>s.value===app.sector)||SECTORS[0]
  const inc = INCOME_STABILITY.find(i=>i.value===app.incomeStability)||INCOME_STABILITY[0]
  const mkt = MARKET_CONDITIONS.find(m=>m.value===app.marketCondition)||MARKET_CONDITIONS[0]

  const hb_subprime    = app.creditScore < 500
  const hb_dti_extreme = app.dtiRatio > 55
  const hb_crisis      = app.marketCondition === 'contraction' && app.incomeStability === 'declining'
  const anyHardBlock   = hb_subprime || hb_dti_extreme || hb_crisis

  function applyPreset(p: typeof PRESETS[0]) { setApp({...p.s}); setCheckpoints([]); setFinalResult(null); setReceiptId(null); setCurrentCp(-1) }

  function runEval() {
    if (isRunning) return
    const cps = buildCheckpoints(app)
    setCheckpoints(cps.map(c=>({...c,status:'pending'})))
    setCurrentCp(-1); setFinalResult(null); setReceiptId(null); setIsRunning(true)
    cps.forEach((_,i)=>{
      if (timerRef.current) clearTimeout(timerRef.current)
      timerRef.current = setTimeout(()=>{
        setCurrentCp(i)
        setCheckpoints(prev=>prev.map((c,idx)=>idx<i?{...c,status:(c.score>=c.threshold?'pass':c.score>=c.threshold*0.72?'warn':'block') as CP['status']}:idx===i?{...c,status:'evaluating' as CP['status']}:c))
        if (i===cps.length-1) {
          setTimeout(()=>{
            const final:CP[]=cps.map(c=>({...c,status:(c.score>=c.threshold?'pass':c.score>=c.threshold*0.72?'warn':'block') as CP['status']}))
            const hb=final.filter(c=>c.score<c.threshold*0.5).length
            const bl=final.filter(c=>c.score<c.threshold).length
            let verdict = anyHardBlock||hb>0?'BLOCKED':bl>=3?'BLOCKED':bl>0?'HOLD':'APPROVED'
            setCheckpoints(final); setCurrentCp(-1); setFinalResult(verdict)
            if (verdict==='APPROVED') setReceiptId(buildReceiptId())
            setIsRunning(false)
          }, 380)
        }
      }, i*300)
    })
  }

  const sIcon=(s:CP['status'])=>{
    if(s==='pending')    return <Clock size={15} style={{color:'#1E3A1E'}}/>
    if(s==='evaluating') return <Activity size={15} style={{color:CRD_GREEN,animation:'pulse 0.8s ease-in-out infinite'}}/>
    if(s==='pass')       return <CheckCircle size={15} style={{color:'#10B981'}}/>
    if(s==='warn')       return <AlertTriangle size={15} style={{color:'#F59E0B'}}/>
    return <XCircle size={15} style={{color:'#EF4444'}}/>
  }
  const sColor=(s:CP['status'])=>s==='pass'?'#10B981':s==='warn'?'#F59E0B':s==='block'?'#EF4444':s==='evaluating'?CRD_GREEN:'#1E3A1E'
  const vColor=(v:string|null)=>v==='APPROVED'?'#10B981':v==='HOLD'?'#F59E0B':'#EF4444'
  const vBg=(v:string|null)=>v==='APPROVED'?'rgba(16,185,129,0.10)':v==='HOLD'?'rgba(245,158,11,0.10)':'rgba(239,68,68,0.10)'
  const vBdr=(v:string|null)=>v==='APPROVED'?'#10B98133':v==='HOLD'?'#F59E0B33':'#EF444433'

  const inp:React.CSSProperties={background:'#061008',border:'1px solid #1E3A1E',borderRadius:7,color:'#CBD5E1',padding:'9px 12px',fontSize:13,width:'100%',outline:'none',cursor:'pointer'}
  const lbl:React.CSSProperties={fontSize:10,color:'#4B5563',marginBottom:5,display:'block',fontWeight:700,textTransform:'uppercase',letterSpacing:'0.05em'}
  const sld:React.CSSProperties={width:'100%',accentColor:CRD_GREEN,cursor:'pointer',height:4}

  return (
    <div style={{minHeight:'100vh',background:`linear-gradient(160deg,${CRD_DARK} 0%,#071410 50%,#050C05 100%)`,color:'#E2E8F0',fontFamily:"'Inter',sans-serif",padding:'24px'}}>
      <style>{`@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.25}} *{box-sizing:border-box} select option{background:#061008} input[type=range]::-webkit-slider-thumb{background:${CRD_GREEN}}`}</style>
      <div style={{maxWidth:1320,margin:'0 auto'}}>

        {/* Header */}
        <div style={{marginBottom:24}}>
          <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:14}}>
            <Link to="/" style={{color:'#374151',fontSize:12,textDecoration:'none'}}>← Home</Link>
            <span style={{color:'#1E3A1E',fontSize:12}}>/</span>
            <span style={{color:'#4B5563',fontSize:12}}>Credit & Lending Governance</span>
          </div>
          <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',flexWrap:'wrap',gap:12}}>
            <div style={{display:'flex',alignItems:'center',gap:14}}>
              <div style={{width:50,height:50,borderRadius:12,display:'flex',alignItems:'center',justifyContent:'center',fontSize:24,background:`${CRD_GREEN}18`,border:`1px solid ${CRD_GREEN}44`}}>💳</div>
              <div>
                <div style={{fontSize:22,fontWeight:800,letterSpacing:'-0.02em',color:'#F1F5F9'}}>Credit & Lending Governance — Interactive Demo</div>
                <div style={{fontSize:12,color:'#374151',marginTop:3}}>ADR-CREDIT-001 · 11-Checkpoint Fail-Closed Pipeline · Basel III · CECL Framework · <span style={{color:CRD_LIGHT,fontFamily:'monospace'}}>OMNIX-CRD-{'{'+'12HEX'+'}'}</span> PQC Receipts</div>
              </div>
            </div>
            <div style={{display:'flex',gap:6,flexWrap:'wrap'}}>
              {['Basel III','CECL / IFRS9','AML / KYC','Fair Lending'].map(b=>(
                <span key={b} style={{padding:'4px 10px',fontSize:10,fontWeight:700,borderRadius:5,background:`${CRD_GREEN}14`,border:`1px solid ${CRD_GREEN}33`,color:CRD_LIGHT,textTransform:'uppercase',letterSpacing:'0.04em'}}>{b}</span>
              ))}
            </div>
          </div>
        </div>

        {/* Presets */}
        <div style={{display:'flex',gap:8,marginBottom:20,flexWrap:'wrap',alignItems:'center'}}>
          <span style={{fontSize:10,color:'#374151',fontWeight:700,textTransform:'uppercase',letterSpacing:'0.06em',marginRight:4}}>Quick Load</span>
          {PRESETS.map(p=>(
            <button key={p.label} onClick={()=>applyPreset(p)} style={{padding:'6px 14px',fontSize:12,borderRadius:7,cursor:'pointer',background:`${CRD_GREEN}10`,border:`1px solid ${CRD_GREEN}28`,color:'#6B7280',fontWeight:600,display:'flex',alignItems:'center',gap:5}}
              onMouseEnter={e=>{(e.currentTarget as HTMLElement).style.borderColor=CRD_GREEN;(e.currentTarget as HTMLElement).style.color=CRD_LIGHT}}
              onMouseLeave={e=>{(e.currentTarget as HTMLElement).style.borderColor=`${CRD_GREEN}28`;(e.currentTarget as HTMLElement).style.color='#6B7280'}}
            >{p.emoji} {p.label}</button>
          ))}
        </div>

        {/* Two-column layout */}
        <div style={{display:'grid',gridTemplateColumns:'390px 1fr',gap:18,alignItems:'start'}}>

          {/* LEFT */}
          <div>
            <div style={{background:'rgba(6,16,8,0.95)',borderRadius:14,padding:22,border:`1px solid ${CRD_BORDER}`,marginBottom:14}}>
              <div style={{fontSize:13,fontWeight:700,color:CRD_LIGHT,marginBottom:18,display:'flex',alignItems:'center',gap:7}}>
                <CreditCard size={14} color={CRD_GREEN}/> Loan Application Parameters
              </div>

              {/* Loan Amount */}
              <div style={{marginBottom:13}}>
                <div style={{display:'flex',justifyContent:'space-between',marginBottom:5}}>
                  <label style={{...lbl,marginBottom:0}}>Loan Amount</label>
                  <span style={{fontSize:13,fontWeight:700,color:app.loanAmount>500000?'#F59E0B':CRD_GREEN}}>${(app.loanAmount/1000).toFixed(0)}K</span>
                </div>
                <input type="range" min={25000} max={1000000} step={25000} style={sld} value={app.loanAmount} onChange={e=>{setApp(p=>({...p,loanAmount:parseInt(e.target.value)}));setCheckpoints([]);setFinalResult(null)}}/>
                <div style={{display:'flex',justifyContent:'space-between',fontSize:10,color:'#1E3A1E',marginTop:2}}><span>$25K</span><span>$1M</span></div>
              </div>

              {/* Credit Score */}
              <div style={{marginBottom:13}}>
                <div style={{display:'flex',justifyContent:'space-between',marginBottom:5}}>
                  <label style={{...lbl,marginBottom:0}}>Credit Score (FICO)</label>
                  <span style={{fontSize:13,fontWeight:700,color:hb_subprime?'#EF4444':app.creditScore>=700?CRD_GREEN:app.creditScore>=580?'#F59E0B':'#EF4444'}}>{app.creditScore}{hb_subprime?' ⚠ HARD BLOCK':''}</span>
                </div>
                <input type="range" min={300} max={850} step={10} style={sld} value={app.creditScore} onChange={e=>{setApp(p=>({...p,creditScore:parseInt(e.target.value)}));setCheckpoints([]);setFinalResult(null)}}/>
                <div style={{display:'flex',justifyContent:'space-between',fontSize:10,color:'#1E3A1E',marginTop:2}}><span style={{color:'#EF4444'}}>300 Subprime</span><span style={{color:'#F59E0B'}}>580+</span><span style={{color:CRD_GREEN}}>700+ Prime</span></div>
                {hb_subprime&&<div style={{fontSize:10,color:'#EF4444',marginTop:4,fontWeight:700}}>⚠ HARD BLOCK — FICO &lt;500 subprime threshold exceeded</div>}
              </div>

              {/* DTI */}
              <div style={{marginBottom:13}}>
                <div style={{display:'flex',justifyContent:'space-between',marginBottom:5}}>
                  <label style={{...lbl,marginBottom:0}}>Debt-to-Income Ratio</label>
                  <span style={{fontSize:13,fontWeight:700,color:hb_dti_extreme?'#EF4444':app.dtiRatio<=30?CRD_GREEN:app.dtiRatio<=43?'#F59E0B':'#EF4444'}}>{app.dtiRatio}%{hb_dti_extreme?' ⚠ HARD BLOCK':''}</span>
                </div>
                <input type="range" min={5} max={65} step={1} style={sld} value={app.dtiRatio} onChange={e=>{setApp(p=>({...p,dtiRatio:parseInt(e.target.value)}));setCheckpoints([]);setFinalResult(null)}}/>
                <div style={{display:'flex',justifyContent:'space-between',fontSize:10,color:'#1E3A1E',marginTop:2}}><span style={{color:CRD_GREEN}}>5% Ideal</span><span style={{color:'#F59E0B'}}>43% Max</span><span style={{color:'#EF4444'}}>65% Extreme</span></div>
                {hb_dti_extreme&&<div style={{fontSize:10,color:'#EF4444',marginTop:4,fontWeight:700}}>⚠ HARD BLOCK — DTI &gt;55% exceeds maximum underwriting threshold</div>}
              </div>

              {/* Sector */}
              <div style={{marginBottom:13}}>
                <label style={lbl}>Industry Sector</label>
                <select style={inp} value={app.sector} onChange={e=>{setApp(p=>({...p,sector:e.target.value}));setCheckpoints([]);setFinalResult(null)}}>
                  {SECTORS.map(s=><option key={s.value} value={s.value}>{s.emoji} {s.label} — Base risk {(s.risk*100).toFixed(0)}%</option>)}
                </select>
              </div>

              {/* Income Stability */}
              <div style={{marginBottom:13}}>
                <label style={lbl}>Income Stability</label>
                <select style={inp} value={app.incomeStability} onChange={e=>{setApp(p=>({...p,incomeStability:e.target.value}));setCheckpoints([]);setFinalResult(null)}}>
                  {INCOME_STABILITY.map(i=><option key={i.value} value={i.value}>{i.label}</option>)}
                </select>
              </div>

              {/* Market Conditions */}
              <div style={{marginBottom:18}}>
                <label style={lbl}>Market Conditions</label>
                <select style={inp} value={app.marketCondition} onChange={e=>{setApp(p=>({...p,marketCondition:e.target.value}));setCheckpoints([]);setFinalResult(null)}}>
                  {MARKET_CONDITIONS.map(m=><option key={m.value} value={m.value}>{m.label}</option>)}
                </select>
                {hb_crisis&&<div style={{fontSize:10,color:'#EF4444',marginTop:4,fontWeight:700}}>⚠ HARD BLOCK — Recession + declining income = automatic decline</div>}
              </div>

              {anyHardBlock&&(
                <div style={{background:'rgba(239,68,68,0.08)',border:'1px solid #EF444430',borderRadius:8,padding:'10px 14px',marginBottom:16}}>
                  <div style={{color:'#EF4444',fontWeight:700,fontSize:11,marginBottom:6}}>⚠ Hard Block Conditions Active</div>
                  {hb_subprime   &&<div style={{color:'#FCA5A5',fontSize:11,marginBottom:3}}>• FICO &lt;500 — subprime automatic decline</div>}
                  {hb_dti_extreme&&<div style={{color:'#FCA5A5',fontSize:11,marginBottom:3}}>• DTI &gt;55% — exceeds Basel III underwriting limit</div>}
                  {hb_crisis     &&<div style={{color:'#FCA5A5',fontSize:11}}>• Recession + declining income — loss risk unacceptable</div>}
                </div>
              )}

              <button onClick={runEval} disabled={isRunning} style={{width:'100%',padding:'13px 20px',borderRadius:10,border:'none',background:isRunning?'#1E293B':`linear-gradient(135deg,#065F46,${CRD_GREEN})`,color:isRunning?'#374151':'#FFF',fontWeight:700,fontSize:14,cursor:isRunning?'not-allowed':'pointer',display:'flex',alignItems:'center',justifyContent:'center',gap:8}}>
                <Shield size={15}/>{isRunning?'Evaluating Credit Decision…':'Run 11-Checkpoint Credit Governance'}{!isRunning&&<ArrowRight size={15}/>}
              </button>
            </div>

            {/* Summary */}
            <div style={{background:'rgba(6,16,8,0.95)',borderRadius:12,padding:16,border:'1px solid #1E3A1E',fontSize:12}}>
              <div style={{color:'#374151',fontWeight:700,marginBottom:10,fontSize:10,textTransform:'uppercase',letterSpacing:'0.06em'}}>Current Application</div>
              {[['Loan Amount',`$${(app.loanAmount/1000).toFixed(0)}K`],['FICO Score',`${app.creditScore} (${app.creditScore>=700?'Prime':app.creditScore>=580?'Near-prime':'Subprime'})`],['DTI Ratio',`${app.dtiRatio}% (${app.dtiRatio<=30?'Excellent':app.dtiRatio<=43?'Acceptable':'Elevated'})`],['Sector',`${sec.emoji} ${sec.label}`],['Income',inc.label.split('(')[0].trim()],['Market',mkt.label]].map(([k,v])=>(
                <div key={k as string} style={{display:'flex',justifyContent:'space-between',marginBottom:5,paddingBottom:5,borderBottom:'1px solid #061008'}}>
                  <span style={{color:'#1E3A1E'}}>{k}</span><span style={{color:'#6B7280',fontWeight:600,textAlign:'right',maxWidth:200}}>{v}</span>
                </div>
              ))}
            </div>
          </div>

          {/* RIGHT */}
          <div>
            {checkpoints.length===0?(
              <div style={{background:'rgba(6,16,8,0.95)',borderRadius:14,padding:52,border:`1px solid ${CRD_BORDER}`,textAlign:'center'}}>
                <div style={{fontSize:52,marginBottom:18}}>💳</div>
                <div style={{fontSize:18,fontWeight:700,color:CRD_LIGHT,marginBottom:10}}>Credit & Lending Governance Pipeline</div>
                <div style={{color:'#374151',fontSize:13,maxWidth:460,margin:'0 auto',lineHeight:1.7}}>Configure a loan application on the left — credit score, DTI ratio, sector exposure, income stability, and market conditions. Run the 11-checkpoint Basel III / CECL governance pipeline. Every approved decision generates a PQC-signed <span style={{color:CRD_LIGHT,fontFamily:'monospace'}}>OMNIX-CRD</span> receipt.</div>
                <div style={{marginTop:28,display:'flex',justifyContent:'center',gap:10,flexWrap:'wrap'}}>
                  {['Default Probability','Concentration Risk','AML Gate','Fraud Detection','PQC Receipt'].map(s=>(
                    <span key={s} style={{background:`${CRD_GREEN}12`,border:`1px solid ${CRD_BORDER}`,borderRadius:6,padding:'5px 12px',fontSize:11,color:CRD_LIGHT,fontWeight:500}}>{s}</span>
                  ))}
                </div>
                <div style={{marginTop:28,display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:10,maxWidth:480,margin:'28px auto 0'}}>
                  {[{icon:<Zap size={14}/>,label:'Sub-second evaluation'},{icon:<Shield size={14}/>,label:'3 hard block conditions'},{icon:<Lock size={14}/>,label:'Dilithium-3 PQC receipt'}].map((item,i)=>(
                    <div key={i} style={{background:'#061008',border:'1px solid #1E3A1E',borderRadius:8,padding:'12px 10px',display:'flex',flexDirection:'column',alignItems:'center',gap:6}}>
                      <div style={{color:CRD_GREEN}}>{item.icon}</div><div style={{fontSize:10,color:'#374151',textAlign:'center'}}>{item.label}</div>
                    </div>
                  ))}
                </div>
              </div>
            ):(
              <div>
                {finalResult&&(
                  <div style={{borderRadius:12,padding:'16px 20px',marginBottom:14,background:vBg(finalResult),border:`1px solid ${vBdr(finalResult)}`,display:'flex',justifyContent:'space-between',alignItems:'center',flexWrap:'wrap',gap:12}}>
                    <div style={{display:'flex',alignItems:'center',gap:12}}>
                      {finalResult==='APPROVED'?<CheckCircle size={22} style={{color:'#10B981'}}/>:finalResult==='HOLD'?<AlertTriangle size={22} style={{color:'#F59E0B'}}/>:<XCircle size={22} style={{color:'#EF4444'}}/>}
                      <div>
                        <div style={{fontWeight:800,fontSize:17,color:vColor(finalResult)}}>{finalResult==='APPROVED'?'LOAN APPROVED':finalResult==='HOLD'?'HOLD — SENIOR UNDERWRITER REVIEW':'DECLINED — GOVERNANCE THRESHOLD BREACH'}</div>
                        {receiptId&&<div style={{fontSize:11,color:'#10B981',fontFamily:'monospace',marginTop:3}}>Receipt: {receiptId} · Dilithium-3 · ADR-CREDIT-001</div>}
                        {!receiptId&&<div style={{fontSize:11,color:'#EF4444',marginTop:3}}>No receipt issued — decision declined by governance pipeline</div>}
                      </div>
                    </div>
                    <div style={{textAlign:'right',fontSize:11,color:'#374151'}}>
                      <div>FICO {app.creditScore} · DTI {app.dtiRatio}%</div>
                      <div>${(app.loanAmount/1000).toFixed(0)}K · {sec.emoji} {sec.label}</div>
                    </div>
                  </div>
                )}
                <div style={{display:'flex',flexDirection:'column',gap:9}}>
                  {checkpoints.map((cp,i)=>{
                    const isActive=currentCp===i
                    const bdrC=cp.status==='evaluating'?CRD_GREEN:cp.status==='pass'?'#10B981':cp.status==='warn'?'#F59E0B':cp.status==='block'?'#EF4444':'#1E3A1E'
                    const barC=cp.status==='pass'?'#10B981':cp.status==='warn'?'#F59E0B':cp.status==='block'?'#EF4444':CRD_GREEN
                    return (
                      <div key={i} style={{background:isActive?`${CRD_GREEN}08`:'rgba(6,16,8,0.92)',borderRadius:10,padding:'13px 15px',border:`1px solid ${bdrC}44`,transition:'all 0.3s'}}>
                        <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:8}}>
                          <div style={{display:'flex',alignItems:'center',gap:8,flex:1}}>
                            {sIcon(cp.status)}
                            <div><div style={{fontSize:13,fontWeight:700,color:'#E2E8F0'}}>{cp.name}</div><div style={{fontSize:10,color:'#374151'}}>{cp.genericName}</div></div>
                          </div>
                          <div style={{textAlign:'right',flexShrink:0,marginLeft:12}}>
                            <div style={{fontSize:20,fontWeight:800,color:sColor(cp.status),lineHeight:1}}>{cp.score}</div>
                            <div style={{fontSize:10,color:'#1E3A1E'}}>min {cp.threshold}</div>
                          </div>
                        </div>
                        <ScoreBar score={cp.score} threshold={cp.threshold} color={barC}/>
                        {cp.status!=='pending'&&(
                          <div style={{marginTop:10}}>
                            <div style={{fontSize:12,color:'#94A3B8',lineHeight:1.55,marginBottom:6}}>{cp.reasoning}</div>
                            <div style={{fontSize:10,color:'#374151',fontFamily:'monospace',background:'#061008',padding:'6px 10px',borderRadius:5}}>{cp.detail}</div>
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

        <div style={{marginTop:28,textAlign:'center',color:'#1E3A1E',fontSize:11}}>
          OMNIX Quantum · Credit & Lending Governance · ADR-CREDIT-001 · 11-Checkpoint Fail-Closed Pipeline
          &nbsp;·&nbsp; Basel III · CECL / IFRS 9 · AML / KYC · Fair Lending Act · Dilithium-3 PQC
          &nbsp;·&nbsp; <Link to="/try" style={{color:CRD_GREEN,textDecoration:'none'}}>Public Sandbox →</Link>
          &nbsp;·&nbsp; <Link to="/" style={{color:CRD_GREEN,textDecoration:'none'}}>Back to Platform →</Link>
        </div>
      </div>
    </div>
  )
}
