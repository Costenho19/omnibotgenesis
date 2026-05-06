import { useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield, CheckCircle, XCircle, AlertTriangle, Activity, Clock,
  TrendingUp, Lock, ArrowRight, Zap,
} from 'lucide-react'

const REP_GOLD   = '#C9A227'
const REP_LIGHT  = '#D4B24E'
const REP_DARK   = '#120E00'
const REP_BORDER = '#C9A22733'

const DECISION_TYPES = [
  { value:'property_valuation', label:'Property Valuation (AVM)',    emoji:'🏠', baseScore:0.70 },
  { value:'mortgage_approval',  label:'Mortgage Underwriting',       emoji:'🏦', baseScore:0.75 },
  { value:'tenant_screening',   label:'Tenant Screening',            emoji:'👤', baseScore:0.65 },
  { value:'aml_transaction',    label:'AML Transaction Screen',      emoji:'🔍', baseScore:0.80 },
  { value:'rental_pricing',     label:'Algorithmic Rental Price',    emoji:'💰', baseScore:0.68 },
]
const PROPERTY_TYPES = [
  { value:'Residential', label:'Residential', riskMod:1.00 },
  { value:'Commercial',  label:'Commercial',  riskMod:1.15 },
  { value:'Industrial',  label:'Industrial',  riskMod:1.25 },
  { value:'Mixed_Use',   label:'Mixed-Use',   riskMod:1.10 },
  { value:'Land',        label:'Land',        riskMod:1.30 },
]
const MARKET_SEGMENTS = [
  { value:'Affordable', label:'Affordable', amlMod:0.85 },
  { value:'Mid_Market', label:'Mid-Market', amlMod:1.00 },
  { value:'Premium',    label:'Premium',    amlMod:1.15 },
  { value:'Luxury',     label:'Luxury',     amlMod:1.40 },
]
const JURISDICTIONS = [
  { value:'UAE',    label:'🇦🇪 UAE (RERA / DLD)',   strictness:1.08 },
  { value:'GCC',    label:'🌙 GCC (SAMA / QFMA)',    strictness:1.04 },
  { value:'UK',     label:'🇬🇧 UK (FCA / UKFI)',     strictness:1.10 },
  { value:'EU',     label:'🇪🇺 EU (MCD / AMLD6)',    strictness:1.06 },
  { value:'GLOBAL', label:'🌐 Global',               strictness:1.00 },
]
const FINANCING_MODES = [
  { value:'Conventional', label:'Conventional',       shariaRequired:false, ltvMax:90 },
  { value:'Murabaha',     label:'Murabaha (Islamic)', shariaRequired:true,  ltvMax:85 },
  { value:'Ijarah',       label:'Ijarah (Islamic)',   shariaRequired:true,  ltvMax:85 },
  { value:'Musharaka',    label:'Musharaka (Islamic)',shariaRequired:true,  ltvMax:80 },
]

interface PropertyCase {
  decisionType: string; propertyType: string; marketSegment: string
  jurisdiction: string; financingMode: string
  avmConfidence: number; priceDeviation: number; ltvRatio: number
  marketTrend: number; liquidityScore: number; amlRiskScore: number
  amlFlag: boolean; reraCompliant: boolean
  shariaScreeningPassed: boolean; beneficialOwnerVerified: boolean
}

const PRESETS: { label:string; emoji:string; s:PropertyCase }[] = [
  { label:'UAE Murabaha — Standard', emoji:'🏦', s:{ decisionType:'mortgage_approval',  propertyType:'Residential', marketSegment:'Mid_Market', jurisdiction:'UAE',    financingMode:'Murabaha',     avmConfidence:80, priceDeviation:8,  ltvRatio:76, marketTrend:68, liquidityScore:72, amlRiskScore:15, amlFlag:false, reraCompliant:true,  shariaScreeningPassed:true,  beneficialOwnerVerified:true  } },
  { label:'Dubai Luxury AVM',        emoji:'🏙️', s:{ decisionType:'property_valuation', propertyType:'Residential', marketSegment:'Luxury',     jurisdiction:'UAE',    financingMode:'Conventional', avmConfidence:85, priceDeviation:12, ltvRatio:65, marketTrend:75, liquidityScore:80, amlRiskScore:35, amlFlag:false, reraCompliant:true,  shariaScreeningPassed:true,  beneficialOwnerVerified:true  } },
  { label:'UK Mortgage — Prime',     emoji:'🇬🇧', s:{ decisionType:'mortgage_approval',  propertyType:'Residential', marketSegment:'Mid_Market', jurisdiction:'UK',     financingMode:'Conventional', avmConfidence:82, priceDeviation:6,  ltvRatio:80, marketTrend:62, liquidityScore:68, amlRiskScore:10, amlFlag:false, reraCompliant:true,  shariaScreeningPassed:true,  beneficialOwnerVerified:true  } },
  { label:'Commercial (EU)',         emoji:'🏢', s:{ decisionType:'mortgage_approval',  propertyType:'Commercial',  marketSegment:'Premium',    jurisdiction:'EU',     financingMode:'Conventional', avmConfidence:72, priceDeviation:15, ltvRatio:70, marketTrend:55, liquidityScore:58, amlRiskScore:22, amlFlag:false, reraCompliant:true,  shariaScreeningPassed:true,  beneficialOwnerVerified:true  } },
  { label:'AML Flag — Block Test',   emoji:'⚠️', s:{ decisionType:'aml_transaction',    propertyType:'Land',        marketSegment:'Luxury',     jurisdiction:'GLOBAL', financingMode:'Conventional', avmConfidence:60, priceDeviation:25, ltvRatio:88, marketTrend:40, liquidityScore:35, amlRiskScore:75, amlFlag:true,  reraCompliant:false, shariaScreeningPassed:false, beneficialOwnerVerified:false } },
]

interface CP {
  name:string; icon:React.ReactNode
  status:'pending'|'evaluating'|'pass'|'warn'|'block'
  score:number; threshold:number; reasoning:string; detail:string
}

function buildCheckpoints(c: PropertyCase): CP[] {
  const dt   = DECISION_TYPES.find(d=>d.value===c.decisionType)||DECISION_TYPES[0]
  const prop = PROPERTY_TYPES.find(p=>p.value===c.propertyType)||PROPERTY_TYPES[0]
  const jx   = JURISDICTIONS.find(j=>j.value===c.jurisdiction)||JURISDICTIONS[0]
  const fin  = FINANCING_MODES.find(f=>f.value===c.financingMode)||FINANCING_MODES[0]
  const seg  = MARKET_SEGMENTS.find(s=>s.value===c.marketSegment)||MARKET_SEGMENTS[0]

  const avm=c.avmConfidence/100, dev=c.priceDeviation/100, ltv=c.ltvRatio/100
  const trend=c.marketTrend/100, liq=c.liquidityScore/100, aml=c.amlRiskScore/100

  const cp1Score = Math.round((avm*0.6+(1-dev)*0.4)*100)
  const cp1Pass  = cp1Score>=55 && !c.amlFlag

  const baseConf = avm*0.55+(1-dev*0.5)*0.30+liq*0.15
  const cp2Score = Math.round((baseConf/jx.strictness)*100)
  const cp2Threshold = Math.round(dt.baseScore*100)
  const cp2Pass  = cp2Score>=cp2Threshold

  const ltvHardBlock = c.ltvRatio > fin.ltvMax
  const rawRisk = (ltv*0.40+dev*0.30+aml*0.20+(c.amlFlag?0.10:0))*seg.amlMod*prop.riskMod
  const cp3Score = Math.round((1-Math.min(rawRisk,1))*100)
  const cp3Pass  = !ltvHardBlock && cp3Score>=30

  const coherence = avm*0.40+(1-dev*0.6)*0.35+liq*0.25
  const cp4Score = Math.round(coherence*100); const cp4Pass = cp4Score>=58

  const traj = trend*0.55+liq*0.30+(1-dev*0.3)*0.15
  const cp5Score = Math.round(traj*100); const cp5Pass = cp5Score>=52

  const resil = liq*0.45+(1-aml*0.4)*0.30+(1-Math.max(0,ltv-0.7))*0.25
  const cp6Score = Math.round(resil*100); const cp6Pass = cp6Score>=50

  let comp = (1-aml*0.40)*100
  comp += c.reraCompliant?25:-40; comp += c.beneficialOwnerVerified?15:-25
  if (fin.shariaRequired) comp += c.shariaScreeningPassed?15:-50
  const cp7Score = Math.round(Math.max(0,Math.min(100,comp/jx.strictness)))
  const cp7Pass  = !c.amlFlag && c.reraCompliant && (!fin.shariaRequired||c.shariaScreeningPassed) && cp7Score>=65

  const sigs = [cp2Score,cp3Score,cp4Score,cp5Score,cp6Score,cp7Score]
  const cp8Score = Math.round(sigs.reduce((a,b)=>a+b,0)/sigs.length); const cp8Pass = cp8Score>=60&&!c.amlFlag

  const stressLoad = aml*0.4+(1-liq)*0.3+dev*0.3
  const cp9Score = Math.round((1-stressLoad)*cp8Score); const cp9Pass = cp9Score>=55

  const overall = cp1Pass&&cp2Pass&&cp3Pass&&cp4Pass&&cp5Pass&&cp6Pass&&cp7Pass&&cp8Pass&&cp9Pass
  const cp10Score = overall?Math.round(90+Math.random()*10):0; const cp10Pass = cp10Score>=85
  const cp11Score = cp10Pass?100:0; const cp11Pass = cp10Pass

  return [
    { name:'CP-1 · Input Validation',       icon:<Shield size={13}/>,        status:'pending', score:cp1Score,    threshold:55,          reasoning:c.amlFlag?`AML flag on input — hard block at intake`:cp1Pass?`AVM quality ${c.avmConfidence}% · deviation ${c.priceDeviation}% — inputs accepted`:`Insufficient AVM quality (${cp1Score}/55)`,                                                      detail:`AVM confidence: ${c.avmConfidence}% | Price deviation: ${c.priceDeviation}% | AML flag: ${c.amlFlag?'YES':'No'}` },
    { name:'CP-2 · AVM Confidence',         icon:<TrendingUp size={13}/>,    status:'pending', score:cp2Score,    threshold:cp2Threshold, reasoning:cp2Pass?`AVM confidence ${cp2Score} meets ${c.jurisdiction} threshold (${cp2Threshold})`:`AVM ${cp2Score} below ${c.jurisdiction} minimum ${cp2Threshold} — ${jx.strictness}× strictness`,                                                   detail:`${c.jurisdiction} strictness: ${jx.strictness}× | Decision: ${dt.label} | Threshold: ${cp2Threshold}` },
    { name:'CP-3 · Transaction Risk',       icon:<AlertTriangle size={13}/>, status:'pending', score:cp3Score,    threshold:30,           reasoning:ltvHardBlock?`HARD BLOCK: LTV ${c.ltvRatio}% > ${fin.label} max ${fin.ltvMax}% (AAOIFI)`:c.amlFlag?`HARD BLOCK: AML alert — transaction frozen`:cp3Pass?`Risk ${cp3Score} within safe limit`:`Risk too high (${cp3Score}/30)`,                detail:`LTV limit: ${fin.ltvMax}% (${fin.label}) | AML mod: ${seg.amlMod}× | Prop risk: ${prop.riskMod}×` },
    { name:'CP-4 · Data Coherence',         icon:<Activity size={13}/>,      status:'pending', score:cp4Score,    threshold:58,           reasoning:cp4Pass?`Multi-source alignment ${cp4Score} — AVM, comparables consistent`:`Signal incoherence (${cp4Score}/58) — deviation ${c.priceDeviation}% causing misalignment`,                                                                         detail:`AVM: ${c.avmConfidence}% | Deviation: ${c.priceDeviation}% | Liquidity: ${c.liquidityScore}%` },
    { name:'CP-5 · Market Trajectory',      icon:<TrendingUp size={13}/>,    status:'pending', score:cp5Score,    threshold:52,           reasoning:cp5Pass?`Market trajectory stable (${cp5Score}) — trend ${c.marketTrend}% · liquidity ${c.liquidityScore}`:`Adverse conditions (${cp5Score}/52) — declining demand or oversupply`,                                                              detail:`Market trend: ${c.marketTrend}% | Liquidity: ${c.liquidityScore}% | Deviation drag: -${(dev*0.3*100).toFixed(0)}%` },
    { name:'CP-6 · Stress Resilience',      icon:<Shield size={13}/>,        status:'pending', score:cp6Score,    threshold:50,           reasoning:cp6Pass?`Asset resilience ${cp6Score} — liquidity and rate sensitivity adequate`:`Stress insufficient (${cp6Score}/50) — illiquid with high rate sensitivity`,                                                                                  detail:`Liquidity: ${c.liquidityScore}% | AML score: ${c.amlRiskScore}% | LTV stress: ${Math.max(0,c.ltvRatio-70)}%` },
    { name:'CP-7 · Regulatory Compliance',  icon:<Lock size={13}/>,          status:'pending', score:cp7Score,    threshold:65,           reasoning:c.amlFlag?`HARD BLOCK: FATF AML violation`:!c.reraCompliant?`HARD BLOCK: RERA non-compliance`:(fin.shariaRequired&&!c.shariaScreeningPassed)?`HARD BLOCK: ${fin.label} — Sharia Board clearance required`:!c.beneficialOwnerVerified?`UBO verification incomplete`:`Regulatory ${cp7Score} — AML, ${c.jurisdiction}, ${fin.label} passed`, detail:`AML: ${c.amlRiskScore}% | RERA: ${c.reraCompliant?'✓':'✗'} | ${fin.shariaRequired?`Sharia: ${c.shariaScreeningPassed?'✓':'✗'} | `:''}UBO: ${c.beneficialOwnerVerified?'✓':'✗'}` },
    { name:'CP-8 · Governance Score',       icon:<Activity size={13}/>,      status:'pending', score:cp8Score,    threshold:60,           reasoning:cp8Pass?`Composite score ${cp8Score} — all signals cleared`:`Score ${cp8Score} below 60 — aggregate signal health insufficient`,                                                                                                              detail:`Avg of CP2-CP7 signals: ${cp8Score}/100` },
    { name:'CP-9 · Stress-Adjusted Score',  icon:<AlertTriangle size={13}/>, status:'pending', score:cp9Score,    threshold:55,           reasoning:cp9Pass?`Stress-adjusted ${cp9Score} — holds under adverse loading`:`Score degrades to ${cp9Score} under stress — resilience insufficient`,                                                                                                  detail:`AML stress: ${(aml*0.4*100).toFixed(0)}% | Liquidity risk: ${((1-liq)*0.3*100).toFixed(0)}% | Dev stress: ${(dev*0.3*100).toFixed(0)}%` },
    { name:'CP-10 · Receipt Authorization', icon:<CheckCircle size={13}/>,   status:'pending', score:cp10Score,   threshold:85,           reasoning:cp10Pass?`Receipt authorized — all 9 prior checkpoints passed (${cp10Score})`:`Receipt denied — one or more checkpoints failed`,                                                                                                             detail:`All CP-1 through CP-9 must pass for receipt authorization` },
    { name:'CP-11 · PQC Receipt Issuance',  icon:<Lock size={13}/>,          status:'pending', score:cp11Score,   threshold:100,          reasoning:cp11Pass?`OMNIX-REP receipt sealed · CRYSTALS-Dilithium3 (NIST FIPS 204)`:`Receipt not issued — governance pipeline blocked`,                                                                                                              detail:`Algorithm: CRYSTALS-Dilithium3 | Standard: NIST FIPS 204 | Prefix: OMNIX-REP` },
  ]
}

function buildReceiptId() {
  return `OMNIX-REP-${Array.from({length:12},()=>Math.floor(Math.random()*16).toString(16).toUpperCase()).join('')}`
}

function ScoreBar({ score, threshold, color }: { score:number; threshold:number; color:string }) {
  return (
    <div style={{ position:'relative', height:6, background:'#1A1400', borderRadius:3, overflow:'visible' }}>
      <div style={{ position:'absolute', left:`${threshold}%`, top:-3, width:2, height:12, background:'#F59E0B', borderRadius:1, zIndex:2 }}/>
      <div style={{ height:'100%', width:`${Math.min(score,100)}%`, background:color, borderRadius:3, transition:'width 0.9s ease' }}/>
    </div>
  )
}

function Toggle({ label, value, onChange, blockMsg }: { label:string; value:boolean; onChange:(v:boolean)=>void; blockMsg?:string }) {
  return (
    <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'8px 0',borderBottom:'1px solid #1A1400'}}>
      <div><div style={{fontSize:12,color:'#94A3B8'}}>{label}</div>{blockMsg&&<div style={{fontSize:10,color:'#EF4444'}}>{blockMsg}</div>}</div>
      <button onClick={()=>onChange(!value)} style={{width:40,height:22,borderRadius:11,border:'none',cursor:'pointer',background:value?REP_GOLD:'rgba(255,255,255,0.08)',position:'relative',transition:'background 0.2s'}}>
        <div style={{width:16,height:16,borderRadius:'50%',background:'#FFF',position:'absolute',top:3,left:value?21:3,transition:'left 0.2s'}}/>
      </button>
    </div>
  )
}

export default function RealEstateGovernanceDemo() {
  const [cas, setCas] = useState<PropertyCase>({ decisionType:'mortgage_approval', propertyType:'Residential', marketSegment:'Mid_Market', jurisdiction:'UAE', financingMode:'Murabaha', avmConfidence:80, priceDeviation:8, ltvRatio:76, marketTrend:68, liquidityScore:72, amlRiskScore:15, amlFlag:false, reraCompliant:true, shariaScreeningPassed:true, beneficialOwnerVerified:true })
  const [checkpoints, setCheckpoints] = useState<CP[]>([])
  const [currentCp, setCurrentCp]   = useState(-1)
  const [finalResult, setFinalResult] = useState<string|null>(null)
  const [receiptId, setReceiptId]   = useState<string|null>(null)
  const [isRunning, setIsRunning]   = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout>|null>(null)

  const dt  = DECISION_TYPES.find(d=>d.value===cas.decisionType)||DECISION_TYPES[0]
  const fin = FINANCING_MODES.find(f=>f.value===cas.financingMode)||FINANCING_MODES[0]
  const jx  = JURISDICTIONS.find(j=>j.value===cas.jurisdiction)||JURISDICTIONS[0]

  const hb_aml    = cas.amlFlag
  const hb_rera   = !cas.reraCompliant
  const hb_ltv    = cas.ltvRatio > fin.ltvMax
  const hb_sharia = fin.shariaRequired && !cas.shariaScreeningPassed
  const anyHardBlock = hb_aml || hb_rera || hb_ltv || hb_sharia

  function applyPreset(p: typeof PRESETS[0]) { setCas({...p.s}); setCheckpoints([]); setFinalResult(null); setReceiptId(null); setCurrentCp(-1) }

  function runEval() {
    if (isRunning) return
    const cps = buildCheckpoints(cas)
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
            const bl=final.filter(c=>c.score<c.threshold).length
            const verdict = anyHardBlock||bl>0?'BLOCKED':final.filter(c=>c.score<c.threshold+10).length>=2?'HOLD':'APPROVED'
            setCheckpoints(final); setCurrentCp(-1); setFinalResult(verdict)
            if (verdict==='APPROVED') setReceiptId(buildReceiptId())
            setIsRunning(false)
          }, 380)
        }
      }, i*300)
    })
  }

  const sIcon=(s:CP['status'])=>{
    if(s==='pending')    return <Clock size={15} style={{color:'#2A2200'}}/>
    if(s==='evaluating') return <Activity size={15} style={{color:REP_GOLD,animation:'pulse 0.8s ease-in-out infinite'}}/>
    if(s==='pass')       return <CheckCircle size={15} style={{color:'#10B981'}}/>
    if(s==='warn')       return <AlertTriangle size={15} style={{color:'#F59E0B'}}/>
    return <XCircle size={15} style={{color:'#EF4444'}}/>
  }
  const sColor=(s:CP['status'])=>s==='pass'?'#10B981':s==='warn'?'#F59E0B':s==='block'?'#EF4444':s==='evaluating'?REP_GOLD:'#2A2200'
  const vColor=(v:string|null)=>v==='APPROVED'?'#10B981':v==='HOLD'?'#F59E0B':'#EF4444'
  const vBg=(v:string|null)=>v==='APPROVED'?'rgba(16,185,129,0.10)':v==='HOLD'?'rgba(245,158,11,0.10)':'rgba(239,68,68,0.10)'
  const vBdr=(v:string|null)=>v==='APPROVED'?'#10B98133':v==='HOLD'?'#F59E0B33':'#EF444433'

  const inp:React.CSSProperties={background:'#120E00',border:'1px solid #2A2200',borderRadius:7,color:'#CBD5E1',padding:'9px 12px',fontSize:13,width:'100%',outline:'none',cursor:'pointer'}
  const lbl:React.CSSProperties={fontSize:10,color:'#5C4A00',marginBottom:5,display:'block',fontWeight:700,textTransform:'uppercase',letterSpacing:'0.05em'}
  const sld:React.CSSProperties={width:'100%',accentColor:REP_GOLD,cursor:'pointer',height:4}

  return (
    <div style={{minHeight:'100vh',background:`linear-gradient(160deg,${REP_DARK} 0%,#1A1700 50%,#0F0C00 100%)`,color:'#E2E8F0',fontFamily:"'Inter',sans-serif",padding:'24px'}}>
      <style>{`@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.25}} *{box-sizing:border-box} select option{background:#120E00} input[type=range]::-webkit-slider-thumb{background:${REP_GOLD}}`}</style>
      <div style={{maxWidth:1320,margin:'0 auto'}}>

        <div style={{marginBottom:24}}>
          <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:14}}>
            <Link to="/" style={{color:'#3D2E00',fontSize:12,textDecoration:'none'}}>← Home</Link>
            <span style={{color:'#2A2200',fontSize:12}}>/</span>
            <span style={{color:'#5C4A00',fontSize:12}}>Real Estate Governance</span>
          </div>
          <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',flexWrap:'wrap',gap:12}}>
            <div style={{display:'flex',alignItems:'center',gap:14}}>
              <div style={{width:50,height:50,borderRadius:12,display:'flex',alignItems:'center',justifyContent:'center',fontSize:24,background:`${REP_GOLD}18`,border:`1px solid ${REP_GOLD}44`}}>🏢</div>
              <div>
                <div style={{fontSize:22,fontWeight:800,letterSpacing:'-0.02em',color:'#F1F5F9'}}>Real Estate Governance — Interactive Demo</div>
                <div style={{fontSize:12,color:'#3D2E00',marginTop:3}}>ADR-REP-001 · 11-Checkpoint Pipeline · AVM · AML / FATF · Islamic Finance · RERA · <span style={{color:REP_LIGHT,fontFamily:'monospace'}}>OMNIX-REP-{'{'+'12HEX'+'}'}</span> PQC Receipts</div>
              </div>
            </div>
            <div style={{display:'flex',gap:6,flexWrap:'wrap'}}>
              {['RERA / DLD','FATF / AML','AAOIFI / Sharia','UBO Verification'].map(b=>(
                <span key={b} style={{padding:'4px 10px',fontSize:10,fontWeight:700,borderRadius:5,background:`${REP_GOLD}14`,border:`1px solid ${REP_GOLD}33`,color:REP_LIGHT,textTransform:'uppercase',letterSpacing:'0.04em'}}>{b}</span>
              ))}
            </div>
          </div>
        </div>

        <div style={{display:'flex',gap:8,marginBottom:20,flexWrap:'wrap',alignItems:'center'}}>
          <span style={{fontSize:10,color:'#3D2E00',fontWeight:700,textTransform:'uppercase',letterSpacing:'0.06em',marginRight:4}}>Quick Load</span>
          {PRESETS.map(p=>(
            <button key={p.label} onClick={()=>applyPreset(p)} style={{padding:'6px 14px',fontSize:12,borderRadius:7,cursor:'pointer',background:`${REP_GOLD}10`,border:`1px solid ${REP_GOLD}28`,color:'#7A6000',fontWeight:600,display:'flex',alignItems:'center',gap:5}}
              onMouseEnter={e=>{(e.currentTarget as HTMLElement).style.borderColor=REP_GOLD;(e.currentTarget as HTMLElement).style.color=REP_LIGHT}}
              onMouseLeave={e=>{(e.currentTarget as HTMLElement).style.borderColor=`${REP_GOLD}28`;(e.currentTarget as HTMLElement).style.color='#7A6000'}}
            >{p.emoji} {p.label}</button>
          ))}
        </div>

        <div style={{display:'grid',gridTemplateColumns:'390px 1fr',gap:18,alignItems:'start'}}>
          <div>
            <div style={{background:'rgba(18,14,0,0.95)',borderRadius:14,padding:22,border:`1px solid ${REP_BORDER}`,marginBottom:14}}>
              <div style={{fontSize:13,fontWeight:700,color:REP_LIGHT,marginBottom:18}}>🏢 Property Deal Parameters</div>

              {[['Decision Type','decisionType',DECISION_TYPES],['Property Type','propertyType',PROPERTY_TYPES],['Market Segment','marketSegment',MARKET_SEGMENTS],['Jurisdiction','jurisdiction',JURISDICTIONS],['Financing Mode','financingMode',FINANCING_MODES]].map(([lab,key,opts])=>(
                <div key={key as string} style={{marginBottom:13}}>
                  <label style={lbl}>{lab as string}</label>
                  <select style={inp} value={(cas as any)[key as string]} onChange={e=>{setCas(p=>({...p,[key as string]:e.target.value}));setCheckpoints([]);setFinalResult(null)}}>
                    {(opts as any[]).map((o:any)=><option key={o.value} value={o.value}>{o.emoji||''}{o.emoji?' ':''}{o.label}</option>)}
                  </select>
                </div>
              ))}

              {[['AVM Confidence %','avmConfidence',40,99,'Low','High'],['Price Deviation %','priceDeviation',0,40,'Stable','High'],['LTV Ratio %','ltvRatio',20,100,'Low','High'],['Market Trend %','marketTrend',10,99,'Declining','Strong'],['Liquidity Score','liquidityScore',10,99,'Illiquid','Liquid'],['AML Risk Score %','amlRiskScore',0,90,'Clean','High Risk']].map(([lab,key,min_,max_,low,high])=>(
                <div key={key as string} style={{marginBottom:11}}>
                  <div style={{display:'flex',justifyContent:'space-between',marginBottom:4}}>
                    <label style={{...lbl,marginBottom:0}}>{lab as string}</label>
                    <span style={{fontSize:13,fontWeight:700,color:REP_LIGHT}}>{(cas as any)[key as string]}%</span>
                  </div>
                  <input type="range" min={min_ as number} max={max_ as number} step={1} style={sld} value={(cas as any)[key as string]} onChange={e=>{setCas(p=>({...p,[key as string]:parseInt(e.target.value)}));setCheckpoints([]);setFinalResult(null)}}/>
                  <div style={{display:'flex',justifyContent:'space-between',fontSize:10,color:'#2A2200',marginTop:2}}><span>{low as string}</span><span>{high as string}</span></div>
                  {key==='ltvRatio'&&hb_ltv&&<div style={{fontSize:10,color:'#EF4444',marginTop:3,fontWeight:700}}>⚠ HARD BLOCK — LTV exceeds {fin.label} max ({fin.ltvMax}%)</div>}
                </div>
              ))}

              <div style={{padding:'12px 0',borderTop:'1px solid #1A1400',marginBottom:16}}>
                <div style={{fontSize:10,color:'#3D2E00',fontWeight:700,textTransform:'uppercase',letterSpacing:'0.06em',marginBottom:10}}>Compliance Flags</div>
                <Toggle label="AML Flag (FATF Alert)" value={cas.amlFlag} onChange={v=>{setCas(p=>({...p,amlFlag:v}));setCheckpoints([]);setFinalResult(null)}} blockMsg={cas.amlFlag?'⚠ HARD BLOCK — transaction frozen':undefined}/>
                <Toggle label="RERA / Regulatory Compliant" value={cas.reraCompliant} onChange={v=>{setCas(p=>({...p,reraCompliant:v}));setCheckpoints([]);setFinalResult(null)}} blockMsg={!cas.reraCompliant?'⚠ HARD BLOCK — non-compliance detected':undefined}/>
                {fin.shariaRequired&&<Toggle label="Sharia Screening Passed" value={cas.shariaScreeningPassed} onChange={v=>{setCas(p=>({...p,shariaScreeningPassed:v}));setCheckpoints([]);setFinalResult(null)}} blockMsg={!cas.shariaScreeningPassed?`⚠ HARD BLOCK — ${fin.label} requires Sharia Board clearance`:undefined}/>}
                <Toggle label="UBO (Beneficial Owner) Verified" value={cas.beneficialOwnerVerified} onChange={v=>{setCas(p=>({...p,beneficialOwnerVerified:v}));setCheckpoints([]);setFinalResult(null)}}/>
              </div>

              {anyHardBlock&&(
                <div style={{background:'rgba(239,68,68,0.08)',border:'1px solid #EF444430',borderRadius:8,padding:'10px 14px',marginBottom:16}}>
                  <div style={{color:'#EF4444',fontWeight:700,fontSize:11,marginBottom:6}}>⚠ Hard Block Active</div>
                  {hb_aml   &&<div style={{color:'#FCA5A5',fontSize:11,marginBottom:3}}>• AML flag — FATF compliance violation</div>}
                  {hb_rera  &&<div style={{color:'#FCA5A5',fontSize:11,marginBottom:3}}>• RERA non-compliance detected</div>}
                  {hb_ltv   &&<div style={{color:'#FCA5A5',fontSize:11,marginBottom:3}}>• LTV {cas.ltvRatio}% exceeds {fin.label} max {fin.ltvMax}%</div>}
                  {hb_sharia&&<div style={{color:'#FCA5A5',fontSize:11}}>• {fin.label} — Sharia Board clearance required</div>}
                </div>
              )}

              <button onClick={runEval} disabled={isRunning} style={{width:'100%',padding:'13px 20px',borderRadius:10,border:'none',background:isRunning?'#1E293B':`linear-gradient(135deg,#78550A,${REP_GOLD})`,color:isRunning?'#374151':'#000',fontWeight:700,fontSize:14,cursor:isRunning?'not-allowed':'pointer',display:'flex',alignItems:'center',justifyContent:'center',gap:8}}>
                🏢{isRunning?'Evaluating Property…':'Run 11-Checkpoint Real Estate Governance'}{!isRunning&&<ArrowRight size={15}/>}
              </button>
            </div>

            <div style={{background:'rgba(18,14,0,0.95)',borderRadius:12,padding:16,border:'1px solid #2A2200',fontSize:12}}>
              <div style={{color:'#3D2E00',fontWeight:700,marginBottom:10,fontSize:10,textTransform:'uppercase',letterSpacing:'0.06em'}}>Current Deal</div>
              {[[`Decision`,`${dt.emoji} ${dt.label}`],[`Financing`,fin.label],[`Jurisdiction`,jx.label.replace(/🇦🇪|🌙|🇬🇧|🇪🇺|🌐/g,'').trim()],[`LTV`,`${cas.ltvRatio}% (max ${fin.ltvMax}%)`],[`AVM`,`${cas.avmConfidence}% conf`],[`AML Score`,`${cas.amlRiskScore}%`],[`RERA`,cas.reraCompliant?'✓ Compliant':'✗ NOT COMPLIANT'],[`UBO`,cas.beneficialOwnerVerified?'✓ Verified':'✗ Not verified']].map(([k,v])=>(
                <div key={k as string} style={{display:'flex',justifyContent:'space-between',marginBottom:5,paddingBottom:5,borderBottom:'1px solid #120E00'}}>
                  <span style={{color:'#2A2200'}}>{k}</span><span style={{color:(v as string).includes('NOT')||(v as string).includes('✗')?'#EF4444':'#7A6000',fontWeight:600,textAlign:'right'}}>{v}</span>
                </div>
              ))}
            </div>
          </div>

          <div>
            {checkpoints.length===0?(
              <div style={{background:'rgba(18,14,0,0.95)',borderRadius:14,padding:52,border:`1px solid ${REP_BORDER}`,textAlign:'center'}}>
                <div style={{fontSize:52,marginBottom:18}}>🏢</div>
                <div style={{fontSize:18,fontWeight:700,color:REP_LIGHT,marginBottom:10}}>Real Estate Governance Pipeline</div>
                <div style={{color:'#3D2E00',fontSize:13,maxWidth:460,margin:'0 auto',lineHeight:1.7}}>Configure a property deal on the left — AVM confidence, LTV, AML score, RERA compliance, and financing mode. Run the 11-checkpoint pipeline. Every approved deal generates a PQC-signed <span style={{color:REP_LIGHT,fontFamily:'monospace'}}>OMNIX-REP</span> receipt.</div>
                <div style={{marginTop:28,display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:10,maxWidth:480,margin:'28px auto 0'}}>
                  {[{icon:<Zap size={14}/>,label:'AVM + AML + Sharia'},{icon:<Shield size={14}/>,label:'4 hard block conditions'},{icon:<Lock size={14}/>,label:'Dilithium-3 PQC receipt'}].map((item,i)=>(
                    <div key={i} style={{background:'#120E00',border:'1px solid #2A2200',borderRadius:8,padding:'12px 10px',display:'flex',flexDirection:'column',alignItems:'center',gap:6}}>
                      <div style={{color:REP_GOLD}}>{item.icon}</div><div style={{fontSize:10,color:'#3D2E00',textAlign:'center'}}>{item.label}</div>
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
                        <div style={{fontWeight:800,fontSize:17,color:vColor(finalResult)}}>{finalResult==='APPROVED'?'TRANSACTION APPROVED':finalResult==='HOLD'?'HOLD — COMPLIANCE REVIEW':'BLOCKED — GOVERNANCE THRESHOLD BREACH'}</div>
                        {receiptId&&<div style={{fontSize:11,color:'#10B981',fontFamily:'monospace',marginTop:3}}>Receipt: {receiptId} · Dilithium-3 · ADR-REP-001</div>}
                        {!receiptId&&<div style={{fontSize:11,color:'#EF4444',marginTop:3}}>No receipt — transaction blocked by real estate governance</div>}
                      </div>
                    </div>
                    <div style={{textAlign:'right',fontSize:11,color:'#3D2E00'}}>
                      <div>{dt.emoji} {dt.label}</div>
                      <div>{fin.label} · LTV {cas.ltvRatio}%</div>
                    </div>
                  </div>
                )}
                <div style={{display:'flex',flexDirection:'column',gap:9}}>
                  {checkpoints.map((cp,i)=>{
                    const isActive=currentCp===i
                    const bdrC=cp.status==='evaluating'?REP_GOLD:cp.status==='pass'?'#10B981':cp.status==='warn'?'#F59E0B':cp.status==='block'?'#EF4444':'#2A2200'
                    const barC=cp.status==='pass'?'#10B981':cp.status==='warn'?'#F59E0B':cp.status==='block'?'#EF4444':REP_GOLD
                    return (
                      <div key={i} style={{background:isActive?`${REP_GOLD}08`:'rgba(18,14,0,0.92)',borderRadius:10,padding:'13px 15px',border:`1px solid ${bdrC}44`,transition:'all 0.3s'}}>
                        <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:8}}>
                          <div style={{display:'flex',alignItems:'center',gap:8,flex:1}}>
                            {sIcon(cp.status)}
                            <div style={{fontSize:13,fontWeight:700,color:'#E2E8F0'}}>{cp.name}</div>
                          </div>
                          <div style={{textAlign:'right',flexShrink:0,marginLeft:12}}>
                            <div style={{fontSize:20,fontWeight:800,color:sColor(cp.status),lineHeight:1}}>{cp.score}</div>
                            <div style={{fontSize:10,color:'#2A2200'}}>min {cp.threshold}</div>
                          </div>
                        </div>
                        <ScoreBar score={cp.score} threshold={cp.threshold} color={barC}/>
                        {cp.status!=='pending'&&(
                          <div style={{marginTop:10}}>
                            <div style={{fontSize:12,color:'#94A3B8',lineHeight:1.55,marginBottom:6}}>{cp.reasoning}</div>
                            <div style={{fontSize:10,color:'#3D2E00',fontFamily:'monospace',background:'#120E00',padding:'6px 10px',borderRadius:5}}>{cp.detail}</div>
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

        <div style={{marginTop:28,textAlign:'center',color:'#2A2200',fontSize:11}}>
          OMNIX Quantum · Real Estate Governance · ADR-REP-001 · 11-Checkpoint Fail-Closed Pipeline
          &nbsp;·&nbsp; RERA / DLD · FATF AML · AAOIFI Sharia · UBO Verification · Dilithium-3 PQC
          &nbsp;·&nbsp; <Link to="/try" style={{color:REP_GOLD,textDecoration:'none'}}>Public Sandbox →</Link>
          &nbsp;·&nbsp; <Link to="/" style={{color:REP_GOLD,textDecoration:'none'}}>Back to Platform →</Link>
        </div>
      </div>
    </div>
  )
}
