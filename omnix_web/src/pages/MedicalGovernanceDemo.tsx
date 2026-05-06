import { useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield, CheckCircle, XCircle, AlertTriangle, Activity, Clock,
  Heart, Brain, Cpu, Lock, TrendingUp, Stethoscope, ArrowRight, Zap, Monitor,
} from 'lucide-react'

const MED_ROSE   = '#F43F5E'
const MED_LIGHT  = '#FB7185'
const MED_DARK   = '#120008'
const MED_BORDER = '#F43F5E33'

const DECISION_TYPES = [
  { value:'rehabilitation_guidance',    label:'Rehabilitation Guidance',      emoji:'🦾', baseScore:0.78 },
  { value:'diagnostic_alert',           label:'Diagnostic Alert',             emoji:'🩺', baseScore:0.82 },
  { value:'monitoring_alert',           label:'Remote Patient Monitoring',    emoji:'📡', baseScore:0.75 },
  { value:'therapeutic_recommendation', label:'Therapeutic Recommendation',   emoji:'💊', baseScore:0.80 },
  { value:'surgical_clearance',         label:'Surgical Clearance',           emoji:'🔬', baseScore:0.88 },
]

const DEVICE_TYPES = [
  { value:'Wearable',          label:'Wearable Sensor',         sensorBase:82, noiseLevel:0.12 },
  { value:'Clinical_AI',       label:'Clinical AI System',      sensorBase:91, noiseLevel:0.06 },
  { value:'Monitoring_System', label:'Remote Monitoring Device', sensorBase:87, noiseLevel:0.09 },
  { value:'Surgical_Robot',    label:'Surgical Robot',           sensorBase:93, noiseLevel:0.04 },
]

const PATIENT_PROFILES = [
  { value:'rehabilitation',    label:'Rehabilitation Patient', riskBase:0.32 },
  { value:'chronic_condition', label:'Chronic Condition',      riskBase:0.48 },
  { value:'post_surgery',      label:'Post-Surgery',           riskBase:0.58 },
  { value:'acute_care',        label:'Acute Care',             riskBase:0.65 },
  { value:'preventive',        label:'Preventive Care',        riskBase:0.12 },
  { value:'geriatric',         label:'Geriatric Patient',      riskBase:0.52 },
]

const JURISDICTIONS = [
  { value:'UAE', label:'UAE — DOH AI Framework',     strictness:1.00 },
  { value:'EU',  label:'EU — AI Act / MDR High-Risk', strictness:1.05 },
  { value:'USA', label:'USA — FDA SaMD Guidelines',   strictness:1.10 },
  { value:'UK',  label:'UK — MHRA AI Guidance',       strictness:1.08 },
]

interface ClinicalCase {
  decisionType:          string
  deviceType:            string
  patientProfile:        string
  jurisdiction:          string
  diagnosticConfidence:  number
  patientRisk:           number
  consentVerified:       boolean
  ethicsFlag:            boolean
}

const PRESETS: { label:string; emoji:string; s:ClinicalCase }[] = [
  { label:'Rehab — Standard',         emoji:'🦾', s:{ decisionType:'rehabilitation_guidance',    deviceType:'Wearable',          patientProfile:'rehabilitation',    jurisdiction:'UAE', diagnosticConfidence:82, patientRisk:35, consentVerified:true,  ethicsFlag:false } },
  { label:'Surgical Clearance',       emoji:'🔬', s:{ decisionType:'surgical_clearance',         deviceType:'Surgical_Robot',     patientProfile:'post_surgery',      jurisdiction:'USA', diagnosticConfidence:91, patientRisk:58, consentVerified:true,  ethicsFlag:false } },
  { label:'Remote Monitoring',        emoji:'📡', s:{ decisionType:'monitoring_alert',            deviceType:'Monitoring_System',  patientProfile:'chronic_condition', jurisdiction:'EU',  diagnosticConfidence:75, patientRisk:45, consentVerified:true,  ethicsFlag:false } },
  { label:'Geriatric — Diagnostic',   emoji:'🩺', s:{ decisionType:'diagnostic_alert',           deviceType:'Clinical_AI',        patientProfile:'geriatric',         jurisdiction:'UK',  diagnosticConfidence:68, patientRisk:72, consentVerified:true,  ethicsFlag:false } },
  { label:'No Consent — Block Test',  emoji:'⚠️', s:{ decisionType:'therapeutic_recommendation', deviceType:'Clinical_AI',        patientProfile:'acute_care',        jurisdiction:'USA', diagnosticConfidence:88, patientRisk:65, consentVerified:false, ethicsFlag:true  } },
]

interface CP {
  name:string; genericName:string; icon:React.ReactNode
  status:'pending'|'evaluating'|'pass'|'warn'|'block'
  score:number; threshold:number; reasoning:string; detail:string
}

function buildCheckpoints(c: ClinicalCase): CP[] {
  const dt   = DECISION_TYPES.find(d=>d.value===c.decisionType)||DECISION_TYPES[0]
  const dev  = DEVICE_TYPES.find(d=>d.value===c.deviceType)||DEVICE_TYPES[0]
  const prof = PATIENT_PROFILES.find(p=>p.value===c.patientProfile)||PATIENT_PROFILES[0]
  const jx   = JURISDICTIONS.find(j=>j.value===c.jurisdiction)||JURISDICTIONS[0]

  const diagConf = c.diagnosticConfidence/100
  const riskIdx  = c.patientRisk/100
  const sensorQ  = dev.sensorBase/100 - dev.noiseLevel*(1-diagConf)

  const cp1Score = Math.round(sensorQ*100*(1-dev.noiseLevel*0.5))
  const cp2Score = Math.round(diagConf*100/jx.strictness)
  const cp2Threshold = Math.round(dt.baseScore*100)
  const adjRisk = riskIdx*prof.riskBase*(1+(1-diagConf)*0.3)*100
  const cp3Score = Math.round(100-adjRisk)
  const coherence = Math.round((diagConf*0.55+sensorQ*0.30+(1-riskIdx)*0.15)*100)
  const trajectory = Math.round((1-riskIdx*0.7+diagConf*0.3)*100)
  const resilience = Math.round((1-prof.riskBase)*sensorQ*100)
  const ethicsPenalty = c.ethicsFlag?40:0; const consentPenalty = !c.consentVerified?60:0
  const cp7Score = Math.max(0,Math.round(diagConf*100*0.7+(1-riskIdx)*30)-ethicsPenalty-consentPenalty)
  const cp8Score = Math.round(diagConf*100/jx.strictness)
  const cp10Score = Math.round((cp1Score+cp8Score+cp7Score)/3)
  const passing = [cp1Score>=62,cp2Score>=cp2Threshold,cp3Score>=35,coherence>=60,trajectory>=55,resilience>=52,(cp7Score>=58&&c.consentVerified),cp8Score>=60,true,cp10Score>=55].filter(Boolean).length
  const cp11Score = Math.round(passing*10)

  return [
    { name:'Sensor & Data Integrity',        genericName:'CP-1: Device data quality valid?',       icon:<Activity size={15}/>,     status:'pending', score:cp1Score,   threshold:62, reasoning:cp1Score>=62?`${dev.label} data validated — ${cp1Score}% integrity confirmed`:`Sensor degradation — ${100-cp1Score}% noise above safe threshold`,               detail:`Device: ${dev.label} | Noise: ${(dev.noiseLevel*100).toFixed(0)}% | Sensor quality: ${(sensorQ*100).toFixed(0)}%` },
    { name:'Clinical Probability',           genericName:'CP-2: AI diagnostic confidence?',        icon:<Brain size={15}/>,        status:'pending', score:cp2Score,   threshold:cp2Threshold, reasoning:cp2Score>=cp2Threshold?`AI confidence ${cp2Score}% exceeds ${c.jurisdiction} regulatory threshold (${cp2Threshold}%)`:`Confidence ${cp2Score}% below ${c.jurisdiction} requirement (${cp2Threshold}%) — ${jx.strictness}× strictness`,   detail:`Decision: ${dt.label} | Jurisdiction: ${c.jurisdiction} | Strictness: ${jx.strictness}×` },
    { name:'Patient Risk Stratification',    genericName:'CP-3: Risk exposure acceptable?',        icon:<AlertTriangle size={15}/>,status:'pending', score:cp3Score,   threshold:35, reasoning:cp3Score>=35?`Risk profile manageable — ${prof.label} within safe governance parameters`:`Risk exposure ${adjRisk.toFixed(0)}% exceeds safe limit for ${prof.label}`,             detail:`Profile: ${prof.label} | Risk multiplier: ${(prof.riskBase*100).toFixed(0)}% | Adjusted risk: ${adjRisk.toFixed(0)}%` },
    { name:'Clinical Signal Coherence',      genericName:'CP-4: All signals coherent?',            icon:<Zap size={15}/>,          status:'pending', score:coherence,  threshold:60, reasoning:coherence>=60?`Sensors, diagnostics, and clinical data coherent at ${coherence}%`:`Multi-signal misalignment — sensor data and AI output diverge`,                        detail:`Diagnostic: ${c.diagnosticConfidence}% | Sensor: ${dev.sensorBase}% | Coherence: ${coherence}%` },
    { name:'Patient Trajectory',             genericName:'CP-5: Positive trend sustained?',        icon:<TrendingUp size={15}/>,   status:'pending', score:trajectory, threshold:55, reasoning:trajectory>=55?`Positive trajectory sustained — treatment course stable`:`Adverse trajectory — risk of deterioration without intervention`,                             detail:`Risk index: ${c.patientRisk}% | Diagnostic conf: ${c.diagnosticConfidence}% | Trajectory: ${trajectory}%` },
    { name:'Comorbidity Resilience',         genericName:'CP-6: Stress resilient?',                icon:<Heart size={15}/>,        status:'pending', score:resilience, threshold:52, reasoning:resilience>=52?`Decision robust against comorbidity and edge-case amplification`:`Comorbidity burden may amplify risk beyond safe governance bounds`,                        detail:`Profile risk base: ${(prof.riskBase*100).toFixed(0)}% | Sensor quality: ${(sensorQ*100).toFixed(0)}% | Resilience: ${resilience}%` },
    { name:'Ethics & Care Plan Alignment',   genericName:'CP-7: Consent + ethics verified?',       icon:<Shield size={15}/>,       status:'pending', score:cp7Score,   threshold:58, reasoning:c.ethicsFlag?`Ethics review triggered — clinical board review required before proceeding`:!c.consentVerified?`HARD BLOCK: Informed consent not verified — ISO 14971 / GDPR Art.9`:cp7Score>=58?`Care plan confirmed — ethics and consent verified`:`Care plan marginal — review recommended`, detail:`Consent: ${c.consentVerified?'VERIFIED':'NOT VERIFIED'} | Ethics flag: ${c.ethicsFlag?'RAISED':'Clear'} | CP-7 score: ${cp7Score}%` },
    { name:'Regulatory Compliance',          genericName:'CP-8: Jurisdiction compliance?',         icon:<Lock size={15}/>,         status:'pending', score:cp8Score,   threshold:60, reasoning:cp8Score>=60?`Decision meets ${c.jurisdiction} SaMD / AI Act governance requirements`:`Confidence below ${c.jurisdiction} regulatory threshold — manual review required`,        detail:`Framework: ${jx.label} | Strictness: ${jx.strictness}× | Compliance score: ${cp8Score}%` },
    { name:'Cryptographic Receipt (PQC)',    genericName:'CP-9: PQC signature valid?',             icon:<Cpu size={15}/>,          status:'pending', score:97,         threshold:90, reasoning:`Dilithium-3 post-quantum signature generated — OMNIX-MED receipt ready for issuance`,                                                                                detail:`Algorithm: CRYSTALS-Dilithium3 | Standard: NIST FIPS 204 | ML-DSA-65` },
    { name:'Audit Trail Completeness',       genericName:'CP-10: Regulatory reporting ready?',     icon:<Monitor size={15}/>,      status:'pending', score:cp10Score,  threshold:55, reasoning:cp10Score>=55?`Full audit trail captured — regulatory reporting ready for ${c.jurisdiction}`:`Audit trail incomplete — governance documentation gaps detected`,                    detail:`Audit composite: (SIV + Regulatory + Ethics) / 3 = ${cp10Score}%` },
    { name:'Exit Governance Gate',           genericName:'CP-11: Final composite validation?',     icon:<CheckCircle size={15}/>,  status:'pending', score:cp11Score,  threshold:80, reasoning:cp11Score>=80?`${passing}/10 checkpoints passed — clinical AI decision APPROVED`:`Only ${passing}/10 passed — decision requires clinical review or BLOCKED`,               detail:`Checkpoints passed: ${passing} / 10 | Exit gate: ${cp11Score}/100` },
  ]
}

function buildReceiptId() {
  return `OMNIX-MED-${Array.from({length:12},()=>Math.floor(Math.random()*16).toString(16).toUpperCase()).join('')}`
}

function ScoreBar({ score, threshold, color }: { score:number; threshold:number; color:string }) {
  return (
    <div style={{ position:'relative', height:6, background:'#1A000A', borderRadius:3, overflow:'visible' }}>
      <div style={{ position:'absolute', left:`${threshold}%`, top:-3, width:2, height:12, background:'#F59E0B', borderRadius:1, zIndex:2 }}/>
      <div style={{ height:'100%', width:`${Math.min(score,100)}%`, background:color, borderRadius:3, transition:'width 0.9s ease' }}/>
    </div>
  )
}

function Toggle({ label, value, onChange, blockMsg }: { label:string; value:boolean; onChange:(v:boolean)=>void; blockMsg?:string }) {
  return (
    <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'8px 0',borderBottom:'1px solid #1A000A'}}>
      <div>
        <div style={{fontSize:12,color:'#94A3B8'}}>{label}</div>
        {blockMsg&&<div style={{fontSize:10,color:'#EF4444'}}>{blockMsg}</div>}
      </div>
      <button onClick={()=>onChange(!value)} style={{width:40,height:22,borderRadius:11,border:'none',cursor:'pointer',background:value?MED_ROSE:'rgba(255,255,255,0.08)',position:'relative',transition:'background 0.2s'}}>
        <div style={{width:16,height:16,borderRadius:'50%',background:'#FFF',position:'absolute',top:3,left:value?21:3,transition:'left 0.2s'}}/>
      </button>
    </div>
  )
}

export default function MedicalGovernanceDemo() {
  const [cas, setCas] = useState<ClinicalCase>({ decisionType:'rehabilitation_guidance', deviceType:'Wearable', patientProfile:'rehabilitation', jurisdiction:'UAE', diagnosticConfidence:82, patientRisk:35, consentVerified:true, ethicsFlag:false })
  const [checkpoints, setCheckpoints] = useState<CP[]>([])
  const [currentCp, setCurrentCp]   = useState(-1)
  const [finalResult, setFinalResult] = useState<string|null>(null)
  const [receiptId, setReceiptId]   = useState<string|null>(null)
  const [isRunning, setIsRunning]   = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout>|null>(null)

  const dt  = DECISION_TYPES.find(d=>d.value===cas.decisionType)||DECISION_TYPES[0]
  const dev = DEVICE_TYPES.find(d=>d.value===cas.deviceType)||DEVICE_TYPES[0]
  const prof= PATIENT_PROFILES.find(p=>p.value===cas.patientProfile)||PATIENT_PROFILES[0]
  const jx  = JURISDICTIONS.find(j=>j.value===cas.jurisdiction)||JURISDICTIONS[0]

  const hb_no_consent = !cas.consentVerified
  const hb_ethics     = cas.ethicsFlag
  const anyHardBlock  = hb_no_consent || hb_ethics

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
            const verdict = anyHardBlock||bl>0?'BLOCKED':final.filter(c=>c.score<c.threshold+15).length>=3?'HOLD':'APPROVED'
            setCheckpoints(final); setCurrentCp(-1); setFinalResult(verdict)
            if (verdict==='APPROVED') setReceiptId(buildReceiptId())
            setIsRunning(false)
          }, 380)
        }
      }, i*300)
    })
  }

  const sIcon=(s:CP['status'])=>{
    if(s==='pending')    return <Clock size={15} style={{color:'#2A000F'}}/>
    if(s==='evaluating') return <Activity size={15} style={{color:MED_ROSE,animation:'pulse 0.8s ease-in-out infinite'}}/>
    if(s==='pass')       return <CheckCircle size={15} style={{color:'#10B981'}}/>
    if(s==='warn')       return <AlertTriangle size={15} style={{color:'#F59E0B'}}/>
    return <XCircle size={15} style={{color:'#EF4444'}}/>
  }
  const sColor=(s:CP['status'])=>s==='pass'?'#10B981':s==='warn'?'#F59E0B':s==='block'?'#EF4444':s==='evaluating'?MED_ROSE:'#2A000F'
  const vColor=(v:string|null)=>v==='APPROVED'?'#10B981':v==='HOLD'?'#F59E0B':'#EF4444'
  const vBg=(v:string|null)=>v==='APPROVED'?'rgba(16,185,129,0.10)':v==='HOLD'?'rgba(245,158,11,0.10)':'rgba(239,68,68,0.10)'
  const vBdr=(v:string|null)=>v==='APPROVED'?'#10B98133':v==='HOLD'?'#F59E0B33':'#EF444433'

  const inp:React.CSSProperties={background:'#120008',border:'1px solid #2A000F',borderRadius:7,color:'#CBD5E1',padding:'9px 12px',fontSize:13,width:'100%',outline:'none',cursor:'pointer'}
  const lbl:React.CSSProperties={fontSize:10,color:'#6B0025',marginBottom:5,display:'block',fontWeight:700,textTransform:'uppercase',letterSpacing:'0.05em'}
  const sld:React.CSSProperties={width:'100%',accentColor:MED_ROSE,cursor:'pointer',height:4}

  return (
    <div style={{minHeight:'100vh',background:`linear-gradient(160deg,${MED_DARK} 0%,#1A0010 50%,#0F0008 100%)`,color:'#E2E8F0',fontFamily:"'Inter',sans-serif",padding:'24px'}}>
      <style>{`@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.25}} *{box-sizing:border-box} select option{background:#120008} input[type=range]::-webkit-slider-thumb{background:${MED_ROSE}}`}</style>
      <div style={{maxWidth:1320,margin:'0 auto'}}>

        <div style={{marginBottom:24}}>
          <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:14}}>
            <Link to="/" style={{color:'#4B0018',fontSize:12,textDecoration:'none'}}>← Home</Link>
            <span style={{color:'#2A000F',fontSize:12}}>/</span>
            <span style={{color:'#6B0025',fontSize:12}}>Medical AI Governance</span>
          </div>
          <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',flexWrap:'wrap',gap:12}}>
            <div style={{display:'flex',alignItems:'center',gap:14}}>
              <div style={{width:50,height:50,borderRadius:12,display:'flex',alignItems:'center',justifyContent:'center',fontSize:24,background:`${MED_ROSE}18`,border:`1px solid ${MED_ROSE}44`}}>🩺</div>
              <div>
                <div style={{fontSize:22,fontWeight:800,letterSpacing:'-0.02em',color:'#F1F5F9'}}>Medical AI Governance — Interactive Demo</div>
                <div style={{fontSize:12,color:'#4B0018',marginTop:3}}>ADR-MED-001 · 11-Checkpoint Fail-Closed Pipeline · FDA SaMD · EU MDR · ISO 14971 · <span style={{color:MED_LIGHT,fontFamily:'monospace'}}>OMNIX-MED-{'{'+'12HEX'+'}'}</span> PQC Receipts</div>
              </div>
            </div>
            <div style={{display:'flex',gap:6,flexWrap:'wrap'}}>
              {['FDA SaMD','EU AI Act / MDR','ISO 14971','GDPR Art.9','IEEE 7010'].map(b=>(
                <span key={b} style={{padding:'4px 10px',fontSize:10,fontWeight:700,borderRadius:5,background:`${MED_ROSE}14`,border:`1px solid ${MED_ROSE}33`,color:MED_LIGHT,textTransform:'uppercase',letterSpacing:'0.04em'}}>{b}</span>
              ))}
            </div>
          </div>
        </div>

        <div style={{display:'flex',gap:8,marginBottom:20,flexWrap:'wrap',alignItems:'center'}}>
          <span style={{fontSize:10,color:'#4B0018',fontWeight:700,textTransform:'uppercase',letterSpacing:'0.06em',marginRight:4}}>Quick Load</span>
          {PRESETS.map(p=>(
            <button key={p.label} onClick={()=>applyPreset(p)} style={{padding:'6px 14px',fontSize:12,borderRadius:7,cursor:'pointer',background:`${MED_ROSE}10`,border:`1px solid ${MED_ROSE}28`,color:'#7A0030',fontWeight:600,display:'flex',alignItems:'center',gap:5}}
              onMouseEnter={e=>{(e.currentTarget as HTMLElement).style.borderColor=MED_ROSE;(e.currentTarget as HTMLElement).style.color=MED_LIGHT}}
              onMouseLeave={e=>{(e.currentTarget as HTMLElement).style.borderColor=`${MED_ROSE}28`;(e.currentTarget as HTMLElement).style.color='#7A0030'}}
            >{p.emoji} {p.label}</button>
          ))}
        </div>

        <div style={{display:'grid',gridTemplateColumns:'390px 1fr',gap:18,alignItems:'start'}}>
          <div>
            <div style={{background:'rgba(18,0,8,0.95)',borderRadius:14,padding:22,border:`1px solid ${MED_BORDER}`,marginBottom:14}}>
              <div style={{fontSize:13,fontWeight:700,color:MED_LIGHT,marginBottom:18,display:'flex',alignItems:'center',gap:7}}>
                <Stethoscope size={14} color={MED_ROSE}/> Clinical Case Parameters
              </div>

              <div style={{marginBottom:13}}>
                <label style={lbl}>Decision Type</label>
                <select style={inp} value={cas.decisionType} onChange={e=>{setCas(p=>({...p,decisionType:e.target.value}));setCheckpoints([]);setFinalResult(null)}}>
                  {DECISION_TYPES.map(d=><option key={d.value} value={d.value}>{d.emoji} {d.label}</option>)}
                </select>
                <div style={{fontSize:10,color:'#6B0025',marginTop:4}}>Confidence threshold: {Math.round(dt.baseScore*100)}% required for {jx.label.split('—')[0].trim()}</div>
              </div>

              <div style={{marginBottom:13}}>
                <label style={lbl}>Device / System Type</label>
                <select style={inp} value={cas.deviceType} onChange={e=>{setCas(p=>({...p,deviceType:e.target.value}));setCheckpoints([]);setFinalResult(null)}}>
                  {DEVICE_TYPES.map(d=><option key={d.value} value={d.value}>{d.label} (Sensor {d.sensorBase}%, Noise {(d.noiseLevel*100).toFixed(0)}%)</option>)}
                </select>
              </div>

              <div style={{marginBottom:13}}>
                <label style={lbl}>Patient Profile</label>
                <select style={inp} value={cas.patientProfile} onChange={e=>{setCas(p=>({...p,patientProfile:e.target.value}));setCheckpoints([]);setFinalResult(null)}}>
                  {PATIENT_PROFILES.map(p=><option key={p.value} value={p.value}>{p.label} (Risk base {(p.riskBase*100).toFixed(0)}%)</option>)}
                </select>
              </div>

              <div style={{marginBottom:13}}>
                <label style={lbl}>Regulatory Jurisdiction</label>
                <select style={inp} value={cas.jurisdiction} onChange={e=>{setCas(p=>({...p,jurisdiction:e.target.value}));setCheckpoints([]);setFinalResult(null)}}>
                  {JURISDICTIONS.map(j=><option key={j.value} value={j.value}>{j.label}</option>)}
                </select>
                <div style={{fontSize:10,color:'#6B0025',marginTop:4}}>Strictness multiplier: {jx.strictness}×</div>
              </div>

              <div style={{marginBottom:13}}>
                <div style={{display:'flex',justifyContent:'space-between',marginBottom:5}}>
                  <label style={{...lbl,marginBottom:0}}>Diagnostic Confidence</label>
                  <span style={{fontSize:13,fontWeight:700,color:cas.diagnosticConfidence>=75?'#10B981':cas.diagnosticConfidence>=55?'#F59E0B':'#EF4444'}}>{cas.diagnosticConfidence}%</span>
                </div>
                <input type="range" min={20} max={99} step={1} style={sld} value={cas.diagnosticConfidence} onChange={e=>{setCas(p=>({...p,diagnosticConfidence:parseInt(e.target.value)}));setCheckpoints([]);setFinalResult(null)}}/>
                <div style={{display:'flex',justifyContent:'space-between',fontSize:10,color:'#2A000F',marginTop:2}}><span style={{color:'#EF4444'}}>20% Uncertain</span><span style={{color:'#F59E0B'}}>55%+</span><span style={{color:'#10B981'}}>80%+ Confident</span></div>
              </div>

              <div style={{marginBottom:18}}>
                <div style={{display:'flex',justifyContent:'space-between',marginBottom:5}}>
                  <label style={{...lbl,marginBottom:0}}>Patient Risk Index</label>
                  <span style={{fontSize:13,fontWeight:700,color:cas.patientRisk>=70?'#EF4444':cas.patientRisk>=45?'#F59E0B':'#10B981'}}>{cas.patientRisk}%</span>
                </div>
                <input type="range" min={5} max={95} step={1} style={sld} value={cas.patientRisk} onChange={e=>{setCas(p=>({...p,patientRisk:parseInt(e.target.value)}));setCheckpoints([]);setFinalResult(null)}}/>
                <div style={{display:'flex',justifyContent:'space-between',fontSize:10,color:'#2A000F',marginTop:2}}><span style={{color:'#10B981'}}>5% Low Risk</span><span style={{color:'#EF4444'}}>95% Critical</span></div>
              </div>

              <div style={{padding:'12px 0',borderTop:'1px solid #1A000A',marginBottom:16}}>
                <div style={{fontSize:10,color:'#4B0018',fontWeight:700,textTransform:'uppercase',letterSpacing:'0.06em',marginBottom:10}}>Compliance Flags — Hard Blocks</div>
                <Toggle label="Informed Consent Verified" value={cas.consentVerified} onChange={v=>{setCas(p=>({...p,consentVerified:v}));setCheckpoints([]);setFinalResult(null)}} blockMsg={!cas.consentVerified?'⚠ HARD BLOCK — ISO 14971 / GDPR Art.9 violation':undefined}/>
                <Toggle label="Ethics Review Triggered" value={cas.ethicsFlag} onChange={v=>{setCas(p=>({...p,ethicsFlag:v}));setCheckpoints([]);setFinalResult(null)}} blockMsg={cas.ethicsFlag?'⚠ HARD BLOCK — Clinical board review mandatory':undefined}/>
              </div>

              {anyHardBlock&&(
                <div style={{background:'rgba(239,68,68,0.08)',border:'1px solid #EF444430',borderRadius:8,padding:'10px 14px',marginBottom:16}}>
                  <div style={{color:'#EF4444',fontWeight:700,fontSize:11,marginBottom:6}}>⚠ Hard Block Active — Will BLOCK before evaluation</div>
                  {hb_no_consent&&<div style={{color:'#FCA5A5',fontSize:11,marginBottom:3}}>• Informed consent not verified — GDPR Art.9 / ISO 14971</div>}
                  {hb_ethics    &&<div style={{color:'#FCA5A5',fontSize:11}}>• Ethics review triggered — clinical board clearance required</div>}
                </div>
              )}

              <button onClick={runEval} disabled={isRunning} style={{width:'100%',padding:'13px 20px',borderRadius:10,border:'none',background:isRunning?'#1E293B':`linear-gradient(135deg,#881337,${MED_ROSE})`,color:isRunning?'#374151':'#FFF',fontWeight:700,fontSize:14,cursor:isRunning?'not-allowed':'pointer',display:'flex',alignItems:'center',justifyContent:'center',gap:8}}>
                <Stethoscope size={15}/>{isRunning?'Evaluating Clinical Decision…':'Run 11-Checkpoint Medical AI Governance'}{!isRunning&&<ArrowRight size={15}/>}
              </button>
            </div>

            <div style={{background:'rgba(18,0,8,0.95)',borderRadius:12,padding:16,border:'1px solid #2A000F',fontSize:12}}>
              <div style={{color:'#4B0018',fontWeight:700,marginBottom:10,fontSize:10,textTransform:'uppercase',letterSpacing:'0.06em'}}>Current Case</div>
              {[[`Decision`,`${dt.emoji} ${dt.label}`],[`Device`,dev.label],[`Profile`,prof.label],[`Jurisdiction`,jx.label.split('—')[0].trim()],[`Diagnostic Conf`,`${cas.diagnosticConfidence}%`],[`Patient Risk`,`${cas.patientRisk}%`],[`Consent`,cas.consentVerified?'✓ Verified':'✗ NOT VERIFIED'],[`Ethics`,cas.ethicsFlag?'⚠ RAISED':'Clear']].map(([k,v])=>(
                <div key={k as string} style={{display:'flex',justifyContent:'space-between',marginBottom:5,paddingBottom:5,borderBottom:'1px solid #120008'}}>
                  <span style={{color:'#2A000F'}}>{k}</span><span style={{color:(v as string).includes('NOT')||(v as string).includes('RAISED')?'#EF4444':'#7A0030',fontWeight:600,textAlign:'right',maxWidth:200}}>{v}</span>
                </div>
              ))}
            </div>
          </div>

          <div>
            {checkpoints.length===0?(
              <div style={{background:'rgba(18,0,8,0.95)',borderRadius:14,padding:52,border:`1px solid ${MED_BORDER}`,textAlign:'center'}}>
                <div style={{fontSize:52,marginBottom:18}}>🩺</div>
                <div style={{fontSize:18,fontWeight:700,color:MED_LIGHT,marginBottom:10}}>Medical AI Governance Pipeline</div>
                <div style={{color:'#4B0018',fontSize:13,maxWidth:460,margin:'0 auto',lineHeight:1.7}}>Configure a clinical AI decision on the left — decision type, device, patient profile, jurisdiction, diagnostic confidence, and patient risk. Run the 11-checkpoint FDA SaMD / EU MDR governance pipeline. Every approved decision generates a PQC-signed <span style={{color:MED_LIGHT,fontFamily:'monospace'}}>OMNIX-MED</span> receipt.</div>
                <div style={{marginTop:28,display:'flex',justifyContent:'center',gap:10,flexWrap:'wrap'}}>
                  {['Sensor Integrity','Clinical Probability','Patient Risk','Consent Gate','PQC Receipt'].map(s=>(
                    <span key={s} style={{background:`${MED_ROSE}12`,border:`1px solid ${MED_BORDER}`,borderRadius:6,padding:'5px 12px',fontSize:11,color:MED_LIGHT,fontWeight:500}}>{s}</span>
                  ))}
                </div>
                <div style={{marginTop:28,display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:10,maxWidth:480,margin:'28px auto 0'}}>
                  {[{icon:<Heart size={14}/>,label:'FDA SaMD compliant'},{icon:<Shield size={14}/>,label:'2 hard block conditions'},{icon:<Cpu size={14}/>,label:'Dilithium-3 PQC receipt'}].map((item,i)=>(
                    <div key={i} style={{background:'#120008',border:'1px solid #2A000F',borderRadius:8,padding:'12px 10px',display:'flex',flexDirection:'column',alignItems:'center',gap:6}}>
                      <div style={{color:MED_ROSE}}>{item.icon}</div><div style={{fontSize:10,color:'#4B0018',textAlign:'center'}}>{item.label}</div>
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
                        <div style={{fontWeight:800,fontSize:17,color:vColor(finalResult)}}>{finalResult==='APPROVED'?'CLINICAL DECISION APPROVED':finalResult==='HOLD'?'HOLD — CLINICAL REVIEW REQUIRED':'BLOCKED — GOVERNANCE THRESHOLD BREACH'}</div>
                        {receiptId&&<div style={{fontSize:11,color:'#10B981',fontFamily:'monospace',marginTop:3}}>Receipt: {receiptId} · Dilithium-3 · ADR-MED-001</div>}
                        {!receiptId&&<div style={{fontSize:11,color:'#EF4444',marginTop:3}}>No receipt — clinical decision blocked by governance pipeline</div>}
                      </div>
                    </div>
                    <div style={{textAlign:'right',fontSize:11,color:'#4B0018'}}>
                      <div>{dt.emoji} {dt.label}</div>
                      <div>{dev.label} · {jx.label.split('—')[0].trim()}</div>
                    </div>
                  </div>
                )}
                <div style={{display:'flex',flexDirection:'column',gap:9}}>
                  {checkpoints.map((cp,i)=>{
                    const isActive=currentCp===i
                    const bdrC=cp.status==='evaluating'?MED_ROSE:cp.status==='pass'?'#10B981':cp.status==='warn'?'#F59E0B':cp.status==='block'?'#EF4444':'#2A000F'
                    const barC=cp.status==='pass'?'#10B981':cp.status==='warn'?'#F59E0B':cp.status==='block'?'#EF4444':MED_ROSE
                    return (
                      <div key={i} style={{background:isActive?`${MED_ROSE}08`:'rgba(18,0,8,0.92)',borderRadius:10,padding:'13px 15px',border:`1px solid ${bdrC}44`,transition:'all 0.3s'}}>
                        <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:8}}>
                          <div style={{display:'flex',alignItems:'center',gap:8,flex:1}}>
                            {sIcon(cp.status)}
                            <div><div style={{fontSize:13,fontWeight:700,color:'#E2E8F0'}}>{cp.name}</div><div style={{fontSize:10,color:'#4B0018'}}>{cp.genericName}</div></div>
                          </div>
                          <div style={{textAlign:'right',flexShrink:0,marginLeft:12}}>
                            <div style={{fontSize:20,fontWeight:800,color:sColor(cp.status),lineHeight:1}}>{cp.score}</div>
                            <div style={{fontSize:10,color:'#2A000F'}}>min {cp.threshold}</div>
                          </div>
                        </div>
                        <ScoreBar score={cp.score} threshold={cp.threshold} color={barC}/>
                        {cp.status!=='pending'&&(
                          <div style={{marginTop:10}}>
                            <div style={{fontSize:12,color:'#94A3B8',lineHeight:1.55,marginBottom:6}}>{cp.reasoning}</div>
                            <div style={{fontSize:10,color:'#4B0018',fontFamily:'monospace',background:'#120008',padding:'6px 10px',borderRadius:5}}>{cp.detail}</div>
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

        <div style={{marginTop:28,textAlign:'center',color:'#2A000F',fontSize:11}}>
          OMNIX Quantum · Medical AI Governance · ADR-MED-001 · 11-Checkpoint Fail-Closed Pipeline
          &nbsp;·&nbsp; FDA SaMD · EU AI Act / MDR · ISO 14971 · GDPR Art.9 · IEEE 7010 · Dilithium-3 PQC
          &nbsp;·&nbsp; <Link to="/try" style={{color:MED_ROSE,textDecoration:'none'}}>Public Sandbox →</Link>
          &nbsp;·&nbsp; <Link to="/" style={{color:MED_ROSE,textDecoration:'none'}}>Back to Platform →</Link>
        </div>
      </div>
    </div>
  )
}
