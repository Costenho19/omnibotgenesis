import { useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield, CheckCircle, XCircle, AlertTriangle, Activity, Clock,
  Building2, Umbrella, TrendingUp, Layers, Target, Brain, ArrowRight, Zap, Lock,
} from 'lucide-react'

const INS_AMBER  = '#F59E0B'
const INS_LIGHT  = '#FCD34D'
const INS_DARK   = '#150F00'
const INS_BORDER = '#F59E0B33'

const POLICY_TYPES = [
  { value: 'property',    label: 'Property Insurance',       emoji: '🏠', baseRisk: 0.12, avgCoverage: 350000 },
  { value: 'health',      label: 'Health Insurance',         emoji: '🏥', baseRisk: 0.18, avgCoverage: 200000 },
  { value: 'auto',        label: 'Auto Insurance',           emoji: '🚗', baseRisk: 0.15, avgCoverage: 50000  },
  { value: 'life',        label: 'Life Insurance',           emoji: '💼', baseRisk: 0.08, avgCoverage: 500000 },
  { value: 'commercial',  label: 'Commercial Liability',     emoji: '🏢', baseRisk: 0.22, avgCoverage: 500000 },
  { value: 'cyber',       label: 'Cyber Insurance',          emoji: '💻', baseRisk: 0.28, avgCoverage: 250000 },
]

const GEOGRAPHIC_ZONES = [
  { value: 'low_risk',  label: 'Low Risk Zone (Urban, Stable)',          factor: 0.90 },
  { value: 'moderate',  label: 'Moderate Risk (Suburban)',               factor: 0.70 },
  { value: 'elevated',  label: 'Elevated Risk (Coastal, Seismic)',       factor: 0.45 },
  { value: 'high_risk', label: 'High Risk Zone (Flood / Hurricane)',     factor: 0.25 },
]

const MARKET_CONDITIONS = [
  { value: 'soft',       label: 'Soft Market (Buyer Favorable)',         factor: 0.85 },
  { value: 'stable',     label: 'Stable Market',                         factor: 0.75 },
  { value: 'hardening',  label: 'Hardening Market (Rising Premiums)',    factor: 0.50 },
  { value: 'hard',       label: 'Hard Market (Capacity Constrained)',    factor: 0.30 },
]

interface PolicyApp {
  policyType:       string
  applicantAge:     number
  coverageAmount:   number
  claimsHistory:    number
  geographicZone:   string
  marketCondition:  string
}

const PRESETS: { label: string; emoji: string; s: PolicyApp }[] = [
  { label: 'Property — Low Risk',       emoji: '🏠', s: { policyType:'property',   applicantAge:38, coverageAmount:250000,  claimsHistory:0, geographicZone:'low_risk',  marketCondition:'stable'    } },
  { label: 'Life Insurance — Mid-Age',  emoji: '💼', s: { policyType:'life',        applicantAge:42, coverageAmount:500000,  claimsHistory:0, geographicZone:'low_risk',  marketCondition:'soft'      } },
  { label: 'Cyber — High Risk',         emoji: '💻', s: { policyType:'cyber',       applicantAge:35, coverageAmount:1000000, claimsHistory:2, geographicZone:'moderate',  marketCondition:'hardening' } },
  { label: 'Commercial (Coastal)',       emoji: '🏢', s: { policyType:'commercial',  applicantAge:50, coverageAmount:750000,  claimsHistory:1, geographicZone:'elevated',  marketCondition:'hard'      } },
  { label: 'High Claims — Block Test',  emoji: '⚠️', s: { policyType:'health',      applicantAge:72, coverageAmount:500000,  claimsHistory:5, geographicZone:'high_risk', marketCondition:'hard'      } },
]

interface CP {
  name: string; genericName: string; icon: React.ReactNode
  status: 'pending'|'evaluating'|'pass'|'warn'|'block'
  score: number; threshold: number; reasoning: string; detail: string
}

function buildCheckpoints(app: PolicyApp): CP[] {
  const pol  = POLICY_TYPES.find(p=>p.value===app.policyType)||POLICY_TYPES[0]
  const geo  = GEOGRAPHIC_ZONES.find(g=>g.value===app.geographicZone)||GEOGRAPHIC_ZONES[0]
  const mkt  = MARKET_CONDITIONS.find(m=>m.value===app.marketCondition)||MARKET_CONDITIONS[0]
  const ageFactor = app.applicantAge<25?0.55:app.applicantAge<35?0.90:app.applicantAge<50?0.85:app.applicantAge<65?0.65:app.applicantAge<75?0.45:0.25
  const claimsPenalty = app.claimsHistory<=1?app.claimsHistory*0.10:app.claimsHistory<=3?0.10+(app.claimsHistory-1)*0.15:0.40+(app.claimsHistory-3)*0.20
  const coverageRatio = app.coverageAmount/pol.avgCoverage
  const baseClaimProb = pol.baseRisk+claimsPenalty+(1-ageFactor)*0.15
  const adjustedClaimProb = Math.min(0.98,Math.max(0.02,baseClaimProb*(1+Math.max(0,coverageRatio-1)*0.2)))
  const probabilityScore = Math.round((1-adjustedClaimProb)*100)
  const coverageExposure = Math.min(100,Math.round(coverageRatio*40))
  const geoExposure = Math.round((1-geo.factor)*60)
  const claimsExposure = Math.min(40,app.claimsHistory*10)
  const concentrationRisk = Math.min(100,Math.round((coverageExposure+geoExposure+claimsExposure)*0.7))
  const riskScore = Math.max(0,100-concentrationRisk)
  const ageSignal = Math.round(ageFactor*100)
  const claimsSignal = Math.max(0,Math.round((1-app.claimsHistory*0.25)*100))
  const geoSignal = Math.round(geo.factor*100)
  const coherenceScore = Math.round(ageSignal*0.25+claimsSignal*0.50+geoSignal*0.25)
  const claimsTrend = app.claimsHistory===0?95:app.claimsHistory===1?70:app.claimsHistory===2?45:app.claimsHistory===3?25:app.claimsHistory===4?12:5
  const trendScore = Math.round(claimsTrend*(ageFactor*0.6+geo.factor*0.4))
  const stressScore = Math.round(mkt.factor*60+(Math.max(0,1-app.claimsHistory*0.15))*40)
  const signals = [probabilityScore,riskScore,coherenceScore,trendScore,stressScore]
  const avg = signals.reduce((a,b)=>a+b,0)/signals.length
  const variance = signals.reduce((a,b)=>a+Math.pow(b-avg,2),0)/signals.length
  const divergence = Math.sqrt(variance)
  const logicScore = Math.round(Math.max(0,Math.min(100,100-divergence*2.0)))
  const sivScore = Math.min(95,Math.round(75+ageFactor*15+(app.claimsHistory===0?5:0)))
  const temporalScore = Math.min(95,Math.round(claimsTrend*0.60+geo.factor*100*0.40))
  const edgeScore = Math.round(probabilityScore*0.55+logicScore*0.45)
  const amlScore = Math.min(95,Math.round(88-Math.max(0,(app.coverageAmount-500000)/100000*5)))
  const fraudScore = Math.min(95,Math.round(60+coherenceScore*0.35))
  return [
    { name:'Signal Integrity Validation', genericName:'CP-1: All underwriting signals valid?', icon:<Shield size={15}/>, status:'pending', score:sivScore, threshold:60, reasoning:sivScore>=60?`Underwriting signals validated — age, claims, coverage, geo zone inputs are consistent`:`Signal validation failed — one or more underwriting parameters outside governance bounds`, detail:`5/5 signals valid | Age factor: ${(ageFactor*100).toFixed(0)}% | Claims clean: ${app.claimsHistory===0?'YES':'NO'} | SIV: ${sivScore}/100` },
    { name:'Claim Probability Assessment', genericName:'CP-2: Likelihood of claims?',          icon:<Target size={15}/>, status:'pending', score:probabilityScore, threshold:65, reasoning:probabilityScore>=65?`Claim probability ${(adjustedClaimProb*100).toFixed(1)}% — within acceptable underwriting range`:`Claim probability ${(adjustedClaimProb*100).toFixed(1)}% exceeds acceptable risk for ${pol.label}`, detail:`Age factor: ${(ageFactor*100).toFixed(0)}% | Claims penalty: +${(claimsPenalty*100).toFixed(0)}% | Coverage ratio: ${coverageRatio.toFixed(1)}× avg | P(no claim)=${probabilityScore}%` },
    { name:'Portfolio Exposure Limits',    genericName:'CP-3: Concentration risk safe?',       icon:<Shield size={15}/>, status:'pending', score:riskScore, threshold:50, reasoning:riskScore>=50?`Coverage exposure within portfolio concentration limits`:`Excessive exposure — $${(app.coverageAmount/1000).toFixed(0)}K in ${geo.label} creates concentration risk`, detail:`Coverage: ${coverageExposure}% | Geo risk: ${geoExposure}% | Claims: ${claimsExposure}% | Conc: ${concentrationRisk}% | Score: ${riskScore}/100` },
    { name:'Underwriting Coherence',       genericName:'CP-4: Multi-signal agreement?',        icon:<Layers size={15}/>, status:'pending', score:coherenceScore, threshold:50, reasoning:coherenceScore>=50?`Age, claims, geo factors show sufficient agreement (${coherenceScore}%)`:`Conflicting signals — age ${ageSignal>=70?'OK':'WEAK'} / ${app.claimsHistory} prior claims / ${geo.label} diverge`, detail:`Age: ${ageSignal} | Claims: ${claimsSignal} | Geo: ${geoSignal} → Coherence: ${coherenceScore}%` },
    { name:'Claims Trend Persistence',     genericName:'CP-5: Sustained pattern, not noise?',  icon:<TrendingUp size={15}/>, status:'pending', score:trendScore, threshold:35, reasoning:trendScore>=45?`Claims history (${app.claimsHistory} prior) confirms acceptable risk trajectory`:`Claims history (${app.claimsHistory} prior claims) indicates deteriorating risk profile`, detail:`Prior claims impact: ${claimsTrend}% | Age-adjusted trend: ${trendScore}/100 | ${app.claimsHistory===0?'CLEAN RECORD':app.claimsHistory<=2?'MODERATE HISTORY':'HIGH FREQUENCY'}` },
    { name:'Catastrophe Stress Test',      genericName:'CP-6: Resilient to market stress?',    icon:<AlertTriangle size={15}/>, status:'pending', score:stressScore, threshold:40, reasoning:stressScore>=40?`Market (${mkt.label}) — adequate capacity and reserves under stress`:`Market (${mkt.label}) — constrained capacity, elevated reinsurance costs, reduced margins`, detail:`Market factor: ${(mkt.factor*100).toFixed(0)}% → Stress resilience: ${stressScore}/100` },
    { name:'Signal Contradiction (SCG)',   genericName:'CP-7: Contradicting signals?',         icon:<Brain size={15}/>, status:'pending', score:logicScore, threshold:45, reasoning:logicScore>=45?`Internal divergence low — underwriting signals consistent (${logicScore}%)`:`High contradiction — divergence ${divergence.toFixed(1)} indicates conflicting risk assessment`, detail:`Variance: ${divergence.toFixed(1)} | Consistency: ${logicScore}% | ${logicScore<45?'CONTRADICTORY':logicScore<65?'TENSIONED':'ALIGNED'}` },
    { name:'Temporal Coherence',           genericName:'CP-8: Pattern holds across time?',     icon:<Activity size={15}/>, status:'pending', score:temporalScore, threshold:40, reasoning:temporalScore>=40?`Historical claims and geo patterns support temporal consistency`:`Pattern inconsistency — claims trajectory may be worsening`, detail:`Claims trend: ${claimsTrend}% | Geo: ${(geo.factor*100).toFixed(0)}% | Temporal: ${temporalScore}/100` },
    { name:'Edge Confirmation (ECW)',      genericName:'CP-9: Decision converges at boundary?',icon:<Target size={15}/>, status:'pending', score:edgeScore, threshold:45, reasoning:edgeScore>=45?`Boundary confirmed — claim probability and logic converge at governance edge (${edgeScore}%)`:`Weak boundary — probability and coherence don't reinforce at threshold`, detail:`Probability×0.55: ${(probabilityScore*0.55).toFixed(0)} | Logic×0.45: ${(logicScore*0.45).toFixed(0)} | Edge: ${edgeScore}/100` },
    { name:'AML Compliance Gate',          genericName:'CP-10: Passes AML/financial screening?',icon:<Building2 size={15}/>, status:'pending', score:amlScore, threshold:60, reasoning:amlScore>=60?`AML screen passed — coverage and policy show no anomalous financial patterns`:`AML flag — coverage level requires enhanced due diligence`, detail:`Coverage: $${(app.coverageAmount/1000).toFixed(0)}K | Policy: ${pol.label} | AML: ${amlScore}/100` },
    { name:'Fraud Detection Gate',         genericName:'CP-11: Anomalous signal patterns?',    icon:<AlertTriangle size={15}/>, status:'pending', score:fraudScore, threshold:55, reasoning:fraudScore>=55?`Fraud screen passed — claims history and coherence show no anomalous patterns`:`Fraud flag — signal inconsistency indicates possible misrepresentation`, detail:`Coherence base: ${coherenceScore} | Claims: ${app.claimsHistory} prior | Fraud: ${fraudScore}/100 | ${fraudScore<55?'ELEVATED — manual review':'CLEAN PROFILE'}` },
  ]
}

function buildReceiptId() {
  return `OMNIX-INS-${Array.from({length:12},()=>Math.floor(Math.random()*16).toString(16).toUpperCase()).join('')}`
}

function ScoreBar({ score, threshold, color }: { score:number; threshold:number; color:string }) {
  return (
    <div style={{ position:'relative', height:6, background:'#1A1200', borderRadius:3, overflow:'visible' }}>
      <div style={{ position:'absolute', left:`${threshold}%`, top:-3, width:2, height:12, background:'#F59E0B', borderRadius:1, zIndex:2 }}/>
      <div style={{ height:'100%', width:`${Math.min(score,100)}%`, background:color, borderRadius:3, transition:'width 0.9s ease' }}/>
    </div>
  )
}

export default function InsuranceGovernanceDemo() {
  const [app, setApp] = useState<PolicyApp>({ policyType:'property', applicantAge:40, coverageAmount:250000, claimsHistory:0, geographicZone:'low_risk', marketCondition:'stable' })
  const [checkpoints, setCheckpoints] = useState<CP[]>([])
  const [currentCp, setCurrentCp]   = useState(-1)
  const [finalResult, setFinalResult] = useState<string|null>(null)
  const [receiptId, setReceiptId]   = useState<string|null>(null)
  const [isRunning, setIsRunning]   = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout>|null>(null)

  const pol = POLICY_TYPES.find(p=>p.value===app.policyType)||POLICY_TYPES[0]
  const geo = GEOGRAPHIC_ZONES.find(g=>g.value===app.geographicZone)||GEOGRAPHIC_ZONES[0]
  const mkt = MARKET_CONDITIONS.find(m=>m.value===app.marketCondition)||MARKET_CONDITIONS[0]

  const hb_high_claims = app.claimsHistory >= 5
  const hb_catastrophe = geo.value === 'high_risk' && app.coverageAmount > 1000000
  const hb_hard_market = app.marketCondition === 'hard' && app.claimsHistory >= 3
  const anyHardBlock   = hb_high_claims || hb_catastrophe || hb_hard_market

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
            const verdict = anyHardBlock||hb>0?'DECLINED':bl>=3?'DECLINED':bl>0?'REFER':'BIND'
            setCheckpoints(final); setCurrentCp(-1); setFinalResult(verdict)
            if (verdict==='BIND') setReceiptId(buildReceiptId())
            setIsRunning(false)
          }, 380)
        }
      }, i*300)
    })
  }

  const sIcon=(s:CP['status'])=>{
    if(s==='pending')    return <Clock size={15} style={{color:'#2A1F00'}}/>
    if(s==='evaluating') return <Activity size={15} style={{color:INS_AMBER,animation:'pulse 0.8s ease-in-out infinite'}}/>
    if(s==='pass')       return <CheckCircle size={15} style={{color:'#10B981'}}/>
    if(s==='warn')       return <AlertTriangle size={15} style={{color:'#F59E0B'}}/>
    return <XCircle size={15} style={{color:'#EF4444'}}/>
  }
  const sColor=(s:CP['status'])=>s==='pass'?'#10B981':s==='warn'?'#F59E0B':s==='block'?'#EF4444':s==='evaluating'?INS_AMBER:'#2A1F00'
  const vColor=(v:string|null)=>v==='BIND'?'#10B981':v==='REFER'?'#F59E0B':'#EF4444'
  const vBg=(v:string|null)=>v==='BIND'?'rgba(16,185,129,0.10)':v==='REFER'?'rgba(245,158,11,0.10)':'rgba(239,68,68,0.10)'
  const vBdr=(v:string|null)=>v==='BIND'?'#10B98133':v==='REFER'?'#F59E0B33':'#EF444433'

  const inp:React.CSSProperties={background:'#150F00',border:'1px solid #2A1F00',borderRadius:7,color:'#CBD5E1',padding:'9px 12px',fontSize:13,width:'100%',outline:'none',cursor:'pointer'}
  const lbl:React.CSSProperties={fontSize:10,color:'#6B5500',marginBottom:5,display:'block',fontWeight:700,textTransform:'uppercase',letterSpacing:'0.05em'}
  const sld:React.CSSProperties={width:'100%',accentColor:INS_AMBER,cursor:'pointer',height:4}

  return (
    <div style={{minHeight:'100vh',background:`linear-gradient(160deg,${INS_DARK} 0%,#1A1400 50%,#0F0A00 100%)`,color:'#E2E8F0',fontFamily:"'Inter',sans-serif",padding:'24px'}}>
      <style>{`@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.25}} *{box-sizing:border-box} select option{background:#150F00} input[type=range]::-webkit-slider-thumb{background:${INS_AMBER}}`}</style>
      <div style={{maxWidth:1320,margin:'0 auto'}}>

        <div style={{marginBottom:24}}>
          <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:14}}>
            <Link to="/" style={{color:'#4B3800',fontSize:12,textDecoration:'none'}}>← Home</Link>
            <span style={{color:'#2A1F00',fontSize:12}}>/</span>
            <span style={{color:'#6B5500',fontSize:12}}>Insurance Underwriting Governance</span>
          </div>
          <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',flexWrap:'wrap',gap:12}}>
            <div style={{display:'flex',alignItems:'center',gap:14}}>
              <div style={{width:50,height:50,borderRadius:12,display:'flex',alignItems:'center',justifyContent:'center',fontSize:24,background:`${INS_AMBER}18`,border:`1px solid ${INS_AMBER}44`}}>☂️</div>
              <div>
                <div style={{fontSize:22,fontWeight:800,letterSpacing:'-0.02em',color:'#F1F5F9'}}>Insurance Underwriting Governance — Interactive Demo</div>
                <div style={{fontSize:12,color:'#4B3800',marginTop:3}}>ADR-INS-001 · 11-Checkpoint Fail-Closed Pipeline · Solvency II · NAIC Framework · <span style={{color:INS_LIGHT,fontFamily:'monospace'}}>OMNIX-INS-{'{'+'12HEX'+'}'}</span> PQC Receipts</div>
              </div>
            </div>
            <div style={{display:'flex',gap:6,flexWrap:'wrap'}}>
              {['Solvency II','NAIC Standards','AML Gate','Cat Stress Test'].map(b=>(
                <span key={b} style={{padding:'4px 10px',fontSize:10,fontWeight:700,borderRadius:5,background:`${INS_AMBER}14`,border:`1px solid ${INS_AMBER}33`,color:INS_LIGHT,textTransform:'uppercase',letterSpacing:'0.04em'}}>{b}</span>
              ))}
            </div>
          </div>
        </div>

        <div style={{display:'flex',gap:8,marginBottom:20,flexWrap:'wrap',alignItems:'center'}}>
          <span style={{fontSize:10,color:'#4B3800',fontWeight:700,textTransform:'uppercase',letterSpacing:'0.06em',marginRight:4}}>Quick Load</span>
          {PRESETS.map(p=>(
            <button key={p.label} onClick={()=>applyPreset(p)} style={{padding:'6px 14px',fontSize:12,borderRadius:7,cursor:'pointer',background:`${INS_AMBER}10`,border:`1px solid ${INS_AMBER}28`,color:'#78600A',fontWeight:600,display:'flex',alignItems:'center',gap:5}}
              onMouseEnter={e=>{(e.currentTarget as HTMLElement).style.borderColor=INS_AMBER;(e.currentTarget as HTMLElement).style.color=INS_LIGHT}}
              onMouseLeave={e=>{(e.currentTarget as HTMLElement).style.borderColor=`${INS_AMBER}28`;(e.currentTarget as HTMLElement).style.color='#78600A'}}
            >{p.emoji} {p.label}</button>
          ))}
        </div>

        <div style={{display:'grid',gridTemplateColumns:'390px 1fr',gap:18,alignItems:'start'}}>
          <div>
            <div style={{background:'rgba(21,15,0,0.95)',borderRadius:14,padding:22,border:`1px solid ${INS_BORDER}`,marginBottom:14}}>
              <div style={{fontSize:13,fontWeight:700,color:INS_LIGHT,marginBottom:18,display:'flex',alignItems:'center',gap:7}}>
                <Umbrella size={14} color={INS_AMBER}/> Policy Application Parameters
              </div>

              <div style={{marginBottom:13}}>
                <label style={lbl}>Policy Type</label>
                <select style={inp} value={app.policyType} onChange={e=>{setApp(p=>({...p,policyType:e.target.value}));setCheckpoints([]);setFinalResult(null)}}>
                  {POLICY_TYPES.map(p=><option key={p.value} value={p.value}>{p.emoji} {p.label} — Base risk {(p.baseRisk*100).toFixed(0)}%</option>)}
                </select>
                <div style={{fontSize:10,color:'#6B5500',marginTop:4}}>Avg coverage: ${(pol.avgCoverage/1000).toFixed(0)}K · Base claim risk: {(pol.baseRisk*100).toFixed(0)}%</div>
              </div>

              <div style={{marginBottom:13}}>
                <div style={{display:'flex',justifyContent:'space-between',marginBottom:5}}>
                  <label style={{...lbl,marginBottom:0}}>Applicant Age</label>
                  <span style={{fontSize:13,fontWeight:700,color:app.applicantAge>=25&&app.applicantAge<55?'#10B981':app.applicantAge<75?'#F59E0B':'#EF4444'}}>{app.applicantAge} yrs</span>
                </div>
                <input type="range" min={18} max={80} step={1} style={sld} value={app.applicantAge} onChange={e=>{setApp(p=>({...p,applicantAge:parseInt(e.target.value)}));setCheckpoints([]);setFinalResult(null)}}/>
                <div style={{display:'flex',justifyContent:'space-between',fontSize:10,color:'#2A1F00',marginTop:2}}><span style={{color:'#F59E0B'}}>18 Young</span><span style={{color:'#10B981'}}>25-54 Prime</span><span style={{color:'#EF4444'}}>75+ Senior</span></div>
              </div>

              <div style={{marginBottom:13}}>
                <div style={{display:'flex',justifyContent:'space-between',marginBottom:5}}>
                  <label style={{...lbl,marginBottom:0}}>Coverage Amount</label>
                  <span style={{fontSize:13,fontWeight:700,color:app.coverageAmount>1000000?'#F59E0B':INS_LIGHT}}>${(app.coverageAmount/1000).toFixed(0)}K</span>
                </div>
                <input type="range" min={10000} max={2000000} step={10000} style={sld} value={app.coverageAmount} onChange={e=>{setApp(p=>({...p,coverageAmount:parseInt(e.target.value)}));setCheckpoints([]);setFinalResult(null)}}/>
                <div style={{display:'flex',justifyContent:'space-between',fontSize:10,color:'#2A1F00',marginTop:2}}><span>$10K</span><span>$2M</span></div>
              </div>

              <div style={{marginBottom:13}}>
                <div style={{display:'flex',justifyContent:'space-between',marginBottom:5}}>
                  <label style={{...lbl,marginBottom:0}}>Prior Claims (Last 5 Years)</label>
                  <span style={{fontSize:13,fontWeight:700,color:hb_high_claims?'#EF4444':app.claimsHistory===0?'#10B981':app.claimsHistory<=2?'#F59E0B':'#EF4444'}}>{app.claimsHistory} claims{hb_high_claims?' ⚠ HARD BLOCK':''}</span>
                </div>
                <input type="range" min={0} max={6} step={1} style={sld} value={app.claimsHistory} onChange={e=>{setApp(p=>({...p,claimsHistory:parseInt(e.target.value)}));setCheckpoints([]);setFinalResult(null)}}/>
                <div style={{display:'flex',justifyContent:'space-between',fontSize:10,color:'#2A1F00',marginTop:2}}><span style={{color:'#10B981'}}>0 Clean</span><span style={{color:'#F59E0B'}}>1-2 Moderate</span><span style={{color:'#EF4444'}}>5+ Block</span></div>
                {hb_high_claims&&<div style={{fontSize:10,color:'#EF4444',marginTop:4,fontWeight:700}}>⚠ HARD BLOCK — 5+ prior claims exceed underwriting acceptance threshold</div>}
              </div>

              <div style={{marginBottom:13}}>
                <label style={lbl}>Geographic Zone</label>
                <select style={inp} value={app.geographicZone} onChange={e=>{setApp(p=>({...p,geographicZone:e.target.value}));setCheckpoints([]);setFinalResult(null)}}>
                  {GEOGRAPHIC_ZONES.map(g=><option key={g.value} value={g.value}>{g.label}</option>)}
                </select>
                {hb_catastrophe&&<div style={{fontSize:10,color:'#EF4444',marginTop:4,fontWeight:700}}>⚠ HARD BLOCK — High-risk zone + $1M+ coverage = catastrophe exposure</div>}
              </div>

              <div style={{marginBottom:18}}>
                <label style={lbl}>Market Conditions</label>
                <select style={inp} value={app.marketCondition} onChange={e=>{setApp(p=>({...p,marketCondition:e.target.value}));setCheckpoints([]);setFinalResult(null)}}>
                  {MARKET_CONDITIONS.map(m=><option key={m.value} value={m.value}>{m.label}</option>)}
                </select>
                {hb_hard_market&&<div style={{fontSize:10,color:'#EF4444',marginTop:4,fontWeight:700}}>⚠ HARD BLOCK — Hard market + 3+ prior claims = capacity breach</div>}
              </div>

              {anyHardBlock&&(
                <div style={{background:'rgba(239,68,68,0.08)',border:'1px solid #EF444430',borderRadius:8,padding:'10px 14px',marginBottom:16}}>
                  <div style={{color:'#EF4444',fontWeight:700,fontSize:11,marginBottom:6}}>⚠ Hard Block Conditions Active</div>
                  {hb_high_claims   &&<div style={{color:'#FCA5A5',fontSize:11,marginBottom:3}}>• 5+ prior claims — automatic decline threshold</div>}
                  {hb_catastrophe   &&<div style={{color:'#FCA5A5',fontSize:11,marginBottom:3}}>• High-risk zone + $1M+ coverage — catastrophe exposure</div>}
                  {hb_hard_market   &&<div style={{color:'#FCA5A5',fontSize:11}}>• Hard market + 3+ claims — capacity unavailable</div>}
                </div>
              )}

              <button onClick={runEval} disabled={isRunning} style={{width:'100%',padding:'13px 20px',borderRadius:10,border:'none',background:isRunning?'#1E293B':`linear-gradient(135deg,#78350F,${INS_AMBER})`,color:isRunning?'#374151':'#000',fontWeight:700,fontSize:14,cursor:isRunning?'not-allowed':'pointer',display:'flex',alignItems:'center',justifyContent:'center',gap:8}}>
                <Shield size={15}/>{isRunning?'Evaluating Policy…':'Run 11-Checkpoint Underwriting Governance'}{!isRunning&&<ArrowRight size={15}/>}
              </button>
            </div>

            <div style={{background:'rgba(21,15,0,0.95)',borderRadius:12,padding:16,border:'1px solid #2A1F00',fontSize:12}}>
              <div style={{color:'#4B3800',fontWeight:700,marginBottom:10,fontSize:10,textTransform:'uppercase',letterSpacing:'0.06em'}}>Current Policy</div>
              {[['Policy Type',`${pol.emoji} ${pol.label}`],['Applicant Age',`${app.applicantAge} yrs`],['Coverage',`$${(app.coverageAmount/1000).toFixed(0)}K`],['Prior Claims',`${app.claimsHistory} claims (${app.claimsHistory===0?'Clean':app.claimsHistory<=2?'Moderate':'High'})`],['Geo Zone',geo.label.split('(')[0].trim()],['Market',mkt.label]].map(([k,v])=>(
                <div key={k as string} style={{display:'flex',justifyContent:'space-between',marginBottom:5,paddingBottom:5,borderBottom:'1px solid #150F00'}}>
                  <span style={{color:'#2A1F00'}}>{k}</span><span style={{color:'#78600A',fontWeight:600,textAlign:'right',maxWidth:200}}>{v}</span>
                </div>
              ))}
            </div>
          </div>

          <div>
            {checkpoints.length===0?(
              <div style={{background:'rgba(21,15,0,0.95)',borderRadius:14,padding:52,border:`1px solid ${INS_BORDER}`,textAlign:'center'}}>
                <div style={{fontSize:52,marginBottom:18}}>☂️</div>
                <div style={{fontSize:18,fontWeight:700,color:INS_LIGHT,marginBottom:10}}>Insurance Underwriting Governance Pipeline</div>
                <div style={{color:'#4B3800',fontSize:13,maxWidth:460,margin:'0 auto',lineHeight:1.7}}>Configure a policy application on the left — type, age, coverage, claims history, geographic zone, and market conditions. Run the 11-checkpoint Solvency II / NAIC governance pipeline. Every bound policy generates a PQC-signed <span style={{color:INS_LIGHT,fontFamily:'monospace'}}>OMNIX-INS</span> receipt.</div>
                <div style={{marginTop:28,display:'flex',justifyContent:'center',gap:10,flexWrap:'wrap'}}>
                  {['Claim Probability','Catastrophe Stress','AML Gate','Fraud Detection','PQC Receipt'].map(s=>(
                    <span key={s} style={{background:`${INS_AMBER}12`,border:`1px solid ${INS_BORDER}`,borderRadius:6,padding:'5px 12px',fontSize:11,color:INS_LIGHT,fontWeight:500}}>{s}</span>
                  ))}
                </div>
                <div style={{marginTop:28,display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:10,maxWidth:480,margin:'28px auto 0'}}>
                  {[{icon:<Zap size={14}/>,label:'Sub-second evaluation'},{icon:<Shield size={14}/>,label:'3 hard block conditions'},{icon:<Lock size={14}/>,label:'Dilithium-3 PQC receipt'}].map((item,i)=>(
                    <div key={i} style={{background:'#150F00',border:'1px solid #2A1F00',borderRadius:8,padding:'12px 10px',display:'flex',flexDirection:'column',alignItems:'center',gap:6}}>
                      <div style={{color:INS_AMBER}}>{item.icon}</div><div style={{fontSize:10,color:'#4B3800',textAlign:'center'}}>{item.label}</div>
                    </div>
                  ))}
                </div>
              </div>
            ):(
              <div>
                {finalResult&&(
                  <div style={{borderRadius:12,padding:'16px 20px',marginBottom:14,background:vBg(finalResult),border:`1px solid ${vBdr(finalResult)}`,display:'flex',justifyContent:'space-between',alignItems:'center',flexWrap:'wrap',gap:12}}>
                    <div style={{display:'flex',alignItems:'center',gap:12}}>
                      {finalResult==='BIND'?<CheckCircle size={22} style={{color:'#10B981'}}/>:finalResult==='REFER'?<AlertTriangle size={22} style={{color:'#F59E0B'}}/>:<XCircle size={22} style={{color:'#EF4444'}}/>}
                      <div>
                        <div style={{fontWeight:800,fontSize:17,color:vColor(finalResult)}}>{finalResult==='BIND'?'POLICY BOUND':finalResult==='REFER'?'REFER — SENIOR UNDERWRITER REVIEW':'DECLINED — GOVERNANCE THRESHOLD BREACH'}</div>
                        {receiptId&&<div style={{fontSize:11,color:'#10B981',fontFamily:'monospace',marginTop:3}}>Receipt: {receiptId} · Dilithium-3 · ADR-INS-001</div>}
                        {!receiptId&&<div style={{fontSize:11,color:'#EF4444',marginTop:3}}>No receipt issued — policy declined by underwriting governance</div>}
                      </div>
                    </div>
                    <div style={{textAlign:'right',fontSize:11,color:'#4B3800'}}>
                      <div>{pol.emoji} {pol.label}</div>
                      <div>${(app.coverageAmount/1000).toFixed(0)}K · Age {app.applicantAge}</div>
                    </div>
                  </div>
                )}
                <div style={{display:'flex',flexDirection:'column',gap:9}}>
                  {checkpoints.map((cp,i)=>{
                    const isActive=currentCp===i
                    const bdrC=cp.status==='evaluating'?INS_AMBER:cp.status==='pass'?'#10B981':cp.status==='warn'?'#F59E0B':cp.status==='block'?'#EF4444':'#2A1F00'
                    const barC=cp.status==='pass'?'#10B981':cp.status==='warn'?'#F59E0B':cp.status==='block'?'#EF4444':INS_AMBER
                    return (
                      <div key={i} style={{background:isActive?`${INS_AMBER}08`:'rgba(21,15,0,0.92)',borderRadius:10,padding:'13px 15px',border:`1px solid ${bdrC}44`,transition:'all 0.3s'}}>
                        <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:8}}>
                          <div style={{display:'flex',alignItems:'center',gap:8,flex:1}}>
                            {sIcon(cp.status)}
                            <div><div style={{fontSize:13,fontWeight:700,color:'#E2E8F0'}}>{cp.name}</div><div style={{fontSize:10,color:'#4B3800'}}>{cp.genericName}</div></div>
                          </div>
                          <div style={{textAlign:'right',flexShrink:0,marginLeft:12}}>
                            <div style={{fontSize:20,fontWeight:800,color:sColor(cp.status),lineHeight:1}}>{cp.score}</div>
                            <div style={{fontSize:10,color:'#2A1F00'}}>min {cp.threshold}</div>
                          </div>
                        </div>
                        <ScoreBar score={cp.score} threshold={cp.threshold} color={barC}/>
                        {cp.status!=='pending'&&(
                          <div style={{marginTop:10}}>
                            <div style={{fontSize:12,color:'#94A3B8',lineHeight:1.55,marginBottom:6}}>{cp.reasoning}</div>
                            <div style={{fontSize:10,color:'#4B3800',fontFamily:'monospace',background:'#150F00',padding:'6px 10px',borderRadius:5}}>{cp.detail}</div>
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

        <div style={{marginTop:28,textAlign:'center',color:'#2A1F00',fontSize:11}}>
          OMNIX Quantum · Insurance Underwriting Governance · ADR-INS-001 · 11-Checkpoint Fail-Closed Pipeline
          &nbsp;·&nbsp; Solvency II · NAIC Standards · AML / KYC · Dilithium-3 PQC
          &nbsp;·&nbsp; <Link to="/try" style={{color:INS_AMBER,textDecoration:'none'}}>Public Sandbox →</Link>
          &nbsp;·&nbsp; <Link to="/" style={{color:INS_AMBER,textDecoration:'none'}}>Back to Platform →</Link>
        </div>
      </div>
    </div>
  )
}
