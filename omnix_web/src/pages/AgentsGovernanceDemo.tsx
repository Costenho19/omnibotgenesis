import { useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield, CheckCircle, XCircle, AlertTriangle, Activity, Clock,
  Bot, Database, Globe, Lock, TrendingUp, Server, Code, Brain, ArrowRight, Zap,
} from 'lucide-react'

const AGT_VIOLET = '#8B5CF6'
const AGT_LIGHT  = '#A78BFA'
const AGT_DARK   = '#0D0815'
const AGT_BORDER = '#8B5CF633'

const DECISION_TYPES = [
  { value:'task_delegation',    label:'Task Delegation',       emoji:'🤖', baseScore:0.68 },
  { value:'data_access',        label:'Data Access Request',   emoji:'🗄️', baseScore:0.72 },
  { value:'external_api_call',  label:'External API Call',     emoji:'🌐', baseScore:0.75 },
  { value:'resource_allocation',label:'Resource Allocation',   emoji:'⚡', baseScore:0.78 },
  { value:'state_modification', label:'State Modification',    emoji:'✏️', baseScore:0.82 },
]

const AGENT_TYPES = [
  { value:'Financial_Agent',     label:'Financial Agent',      riskBase:1.30 },
  { value:'Enterprise_Agent',    label:'Enterprise Agent',     riskBase:1.15 },
  { value:'Logistics_Agent',     label:'Logistics Agent',      riskBase:1.10 },
  { value:'Infrastructure_Agent',label:'Infrastructure Agent', riskBase:1.25 },
  { value:'Research_Agent',      label:'Research Agent',       riskBase:0.90 },
]

const ENVIRONMENTS = [
  { value:'production', label:'Production', strictness:1.45 },
  { value:'staging',    label:'Staging',    strictness:1.15 },
  { value:'development',label:'Development',strictness:0.90 },
  { value:'sandbox',    label:'Sandbox',    strictness:0.75 },
]

const REVERSIBILITIES = [
  { value:'fully_reversible',     label:'Fully Reversible',      factor:0.80 },
  { value:'partially_reversible', label:'Partially Reversible',  factor:1.10 },
  { value:'irreversible',         label:'Irreversible',          factor:1.45 },
  { value:'unknown',              label:'Unknown Reversibility', factor:1.30 },
]

const DATA_SENSITIVITIES = [
  { value:'low',    label:'Low Sensitivity',     penalty:0  },
  { value:'medium', label:'Medium Sensitivity',  penalty:8  },
  { value:'high',   label:'High Sensitivity',    penalty:18 },
  { value:'pii',    label:'PII (Personal Data)', penalty:28 },
  { value:'phi',    label:'PHI (Health Data)',   penalty:35 },
]

interface AgentCase {
  decisionType:          string
  agentType:             string
  environment:           string
  reversibility:         string
  dataSensitivity:       string
  taskComplexity:        number
  scopeBlastRadius:      number
  contextCompleteness:   number
  goalAlignment:         number
  safetyFlag:            boolean
  humanApprovalRequired: boolean
  humanApproved:         boolean
  crossBoundary:         boolean
}

const PRESETS: { label:string; emoji:string; s:AgentCase }[] = [
  { label:'Enterprise Task — Standard', emoji:'🤖', s:{ decisionType:'task_delegation',    agentType:'Enterprise_Agent',     environment:'production', reversibility:'partially_reversible', dataSensitivity:'low',    taskComplexity:45, scopeBlastRadius:35, contextCompleteness:82, goalAlignment:80, safetyFlag:false, humanApprovalRequired:false, humanApproved:false, crossBoundary:false } },
  { label:'Financial Agent — Prod',     emoji:'💰', s:{ decisionType:'state_modification', agentType:'Financial_Agent',      environment:'production', reversibility:'irreversible',         dataSensitivity:'high',   taskComplexity:60, scopeBlastRadius:50, contextCompleteness:75, goalAlignment:72, safetyFlag:false, humanApprovalRequired:true,  humanApproved:true,  crossBoundary:false } },
  { label:'Infrastructure — Irrev.',    emoji:'🏗️', s:{ decisionType:'resource_allocation',agentType:'Infrastructure_Agent', environment:'production', reversibility:'irreversible',         dataSensitivity:'medium', taskComplexity:70, scopeBlastRadius:65, contextCompleteness:68, goalAlignment:65, safetyFlag:false, humanApprovalRequired:true,  humanApproved:true,  crossBoundary:true  } },
  { label:'Research Agent — Sandbox',   emoji:'🔬', s:{ decisionType:'data_access',        agentType:'Research_Agent',       environment:'sandbox',    reversibility:'fully_reversible',     dataSensitivity:'low',    taskComplexity:30, scopeBlastRadius:15, contextCompleteness:90, goalAlignment:90, safetyFlag:false, humanApprovalRequired:false, humanApproved:false, crossBoundary:false } },
  { label:'Safety Flag — Block Test',   emoji:'⚠️', s:{ decisionType:'external_api_call', agentType:'Financial_Agent',      environment:'production', reversibility:'unknown',              dataSensitivity:'pii',    taskComplexity:75, scopeBlastRadius:70, contextCompleteness:55, goalAlignment:50, safetyFlag:true,  humanApprovalRequired:true,  humanApproved:false, crossBoundary:true  } },
]

interface CP {
  name:string; genericName:string; icon:React.ReactNode
  status:'pending'|'evaluating'|'pass'|'warn'|'block'
  score:number; threshold:number; reasoning:string; detail:string
}

function buildCheckpoints(c: AgentCase): CP[] {
  const dt  = DECISION_TYPES.find(d=>d.value===c.decisionType)||DECISION_TYPES[0]
  const agt = AGENT_TYPES.find(a=>a.value===c.agentType)||AGENT_TYPES[0]
  const env = ENVIRONMENTS.find(e=>e.value===c.environment)||ENVIRONMENTS[0]
  const rev = REVERSIBILITIES.find(r=>r.value===c.reversibility)||REVERSIBILITIES[0]
  const sen = DATA_SENSITIVITIES.find(s=>s.value===c.dataSensitivity)||DATA_SENSITIVITIES[0]

  const complexity = c.taskComplexity/100
  const blast      = c.scopeBlastRadius/100
  const context    = c.contextCompleteness/100
  const goal       = c.goalAlignment/100

  const cp1Score = Math.round(context*100*(1-complexity*0.2))
  const viability = ((1-complexity)*0.45+(1-blast*0.5)*0.30+context*0.25)*100
  const cp2Score  = Math.round(viability/env.strictness)
  const cp2Threshold = Math.round(dt.baseScore*100)
  const adjustedRisk = blast*rev.factor*agt.riskBase*100
  const cp3Score = Math.round(100-adjustedRisk)
  const coherence = Math.round((context*0.40+goal*0.35+(1-blast*0.5)*0.15-blast*0.10)*100)
  const trajectory = Math.round((goal*0.55+context*0.30+(1-complexity)*0.15)*100)
  const resilience = Math.round((context*0.55+(1-blast)*0.30+(1-complexity*0.5)*0.15)*100)
  const safetyPenalty = c.safetyFlag?50:0
  const authPenalty   = (c.humanApprovalRequired&&!c.humanApproved)?45:0
  const bndPenalty    = c.crossBoundary?20:0
  const senPenalty    = sen.penalty*0.3
  const cp7Score = Math.max(0,Math.round((goal*0.45+context*0.25)*100-safetyPenalty-authPenalty-bndPenalty-senPenalty))
  const cp8Score = Math.round(viability/env.strictness)
  const cp10Score = Math.round((cp1Score+coherence+cp7Score)/3)
  const passing = [cp1Score>=60,cp2Score>=cp2Threshold,cp3Score>=32,coherence>=58,trajectory>=52,resilience>=52,(cp7Score>=58&&!c.safetyFlag&&!(c.humanApprovalRequired&&!c.humanApproved)),cp8Score>=55,true,cp10Score>=52].filter(Boolean).length
  const cp11Score = passing*10

  return [
    { name:'Payload & Context Validation', genericName:'CP-1: Agent context complete?',           icon:<Code size={15}/>,          status:'pending', score:cp1Score,    threshold:60,          reasoning:cp1Score>=60?`Agent context complete and validated — ${cp1Score}% integrity`:`Context incomplete — agent operating with insufficient instruction state`,                                                                                     detail:`Context: ${c.contextCompleteness}% | Complexity: ${c.taskComplexity}% | Adjusted: ${cp1Score}/100` },
    { name:'Task Viability Probability',   genericName:'CP-2: Task achievable in environment?',  icon:<Brain size={15}/>,         status:'pending', score:cp2Score,    threshold:cp2Threshold, reasoning:cp2Score>=cp2Threshold?`Viability ${cp2Score}% meets ${c.environment} threshold (${cp2Threshold}%)`:`Viability too low for ${c.environment} — complexity/blast too high (${env.strictness}× strictness)`,                              detail:`Decision: ${dt.label} | Env: ${c.environment} (${env.strictness}×) | Viability: ${cp2Score} vs min ${cp2Threshold}` },
    { name:'Action Blast Radius',          genericName:'CP-3: Scope impact within safe bounds?', icon:<AlertTriangle size={15}/>,  status:'pending', score:Math.max(0,cp3Score), threshold:32, reasoning:cp3Score>=32?`Blast radius within safe governance bounds — impact scope contained`:`Action blast radius ${adjustedRisk.toFixed(0)}% exceeds safe governance limit`,                                                                   detail:`Reversibility: ${rev.label} | Agent risk: ${agt.riskBase}× | Blast: ${adjustedRisk.toFixed(0)}% → ${Math.max(0,cp3Score)}/100` },
    { name:'Context-Task Coherence',       genericName:'CP-4: Goal, context, task aligned?',    icon:<Zap size={15}/>,           status:'pending', score:Math.max(0,coherence), threshold:58, reasoning:coherence>=58?`Task, context, and goal state coherent at ${coherence}%`:`Misalignment between task parameters, context, and stated goal`,                                                                                             detail:`Context: ${c.contextCompleteness}% | Goal: ${c.goalAlignment}% | Blast drag: -${(blast*10).toFixed(0)} → ${Math.max(0,coherence)}/100` },
    { name:'Goal Trajectory Stability',    genericName:'CP-5: Agent converging on objective?',  icon:<TrendingUp size={15}/>,    status:'pending', score:trajectory,  threshold:52,           reasoning:trajectory>=52?`Goal trajectory stable — agent converging toward objective`:`Goal trajectory diverging — risk of task drift or unintended state`,                                                                                        detail:`Goal: ${c.goalAlignment}% | Context: ${c.contextCompleteness}% | Complexity drag: ${(complexity*15).toFixed(0)}% → ${trajectory}/100` },
    { name:'Failure Mode Resilience',      genericName:'CP-6: Fallback paths adequate?',        icon:<Server size={15}/>,        status:'pending', score:resilience,  threshold:52,           reasoning:resilience>=52?`Fallback paths adequate — agent can recover from failure modes`:`Insufficient fallback coverage for dependency failures or edge cases`,                                                                                    detail:`Context: ${c.contextCompleteness}% | Blast: ${c.scopeBlastRadius}% | Complexity: ${c.taskComplexity}% → ${resilience}/100` },
    { name:'Authorization & Safety Gate',  genericName:'CP-7: Principal chain verified?',       icon:<Shield size={15}/>,        status:'pending', score:cp7Score,    threshold:58,           reasoning:c.safetyFlag?`HARD BLOCK: Safety-critical flag — human review mandatory before any execution`:(c.humanApprovalRequired&&!c.humanApproved)?`HARD BLOCK: Human authorization required but not granted`:cp7Score>=58?`Authorization chain verified — principal hierarchy respected`:`Authorization marginal — review principal scope before execution`, detail:`Safety: ${c.safetyFlag?'RAISED':'Clear'} | Approval: ${c.humanApprovalRequired?(c.humanApproved?'✓ Granted':'✗ NOT GRANTED'):'Not required'} | Cross-boundary: ${c.crossBoundary?'YES':'No'} | Data: ${sen.label}` },
    { name:'Environment Compliance',       genericName:'CP-8: Meets env. governance threshold?',icon:<Globe size={15}/>,         status:'pending', score:cp8Score,    threshold:55,           reasoning:cp8Score>=55?`Action meets ${c.environment} environment governance requirements`:`Task parameters don't satisfy ${c.environment} strictness threshold`,                                                                                    detail:`Env strictness: ${env.strictness}× | Data sensitivity: ${sen.label} (penalty: ${sen.penalty}) | Score: ${cp8Score}/100` },
    { name:'Cryptographic Receipt (PQC)',  genericName:'CP-9: PQC signature valid?',           icon:<Lock size={15}/>,          status:'pending', score:97,          threshold:90,           reasoning:`CRYSTALS-Dilithium3 post-quantum signature generated — OMNIX-AGT receipt ready for issuance`,                                                                                                                                             detail:`Algorithm: CRYSTALS-Dilithium3 | Standard: NIST FIPS 204 | ML-DSA-65` },
    { name:'Audit Trail Completeness',     genericName:'CP-10: Principal attribution traceable?',icon:<Database size={15}/>,     status:'pending', score:cp10Score,   threshold:52,           reasoning:cp10Score>=52?`Complete audit trail captured — principal attribution traceable`:`Audit trail gaps — agent action may not be fully attributable`,                                                                                             detail:`Audit composite: (Validation + Coherence + Safety) / 3 = ${cp10Score}%` },
    { name:'Exit Governance Gate',         genericName:'CP-11: Final composite valid?',         icon:<CheckCircle size={15}/>,   status:'pending', score:cp11Score,   threshold:80,           reasoning:cp11Score>=80?`${passing}/10 checkpoints passed — agent action AUTHORIZED`:`Only ${passing}/10 checkpoints passed — action requires review or BLOCKED`,                                                                                    detail:`Checkpoints passed: ${passing} / 10 | Exit gate: ${cp11Score}/100` },
  ]
}

function buildReceiptId() {
  return `OMNIX-AGT-${Array.from({length:12},()=>Math.floor(Math.random()*16).toString(16).toUpperCase()).join('')}`
}

function ScoreBar({ score, threshold, color }: { score:number; threshold:number; color:string }) {
  return (
    <div style={{ position:'relative', height:6, background:'#120A1E', borderRadius:3, overflow:'visible' }}>
      <div style={{ position:'absolute', left:`${threshold}%`, top:-3, width:2, height:12, background:'#F59E0B', borderRadius:1, zIndex:2 }}/>
      <div style={{ height:'100%', width:`${Math.min(score,100)}%`, background:color, borderRadius:3, transition:'width 0.9s ease' }}/>
    </div>
  )
}

function Toggle({ label, value, onChange, blockMsg }: { label:string; value:boolean; onChange:(v:boolean)=>void; blockMsg?:string }) {
  return (
    <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'8px 0',borderBottom:'1px solid #120A1E'}}>
      <div>
        <div style={{fontSize:12,color:'#94A3B8'}}>{label}</div>
        {blockMsg&&<div style={{fontSize:10,color:'#EF4444'}}>{blockMsg}</div>}
      </div>
      <button onClick={()=>onChange(!value)} style={{width:40,height:22,borderRadius:11,border:'none',cursor:'pointer',background:value?AGT_VIOLET:'rgba(255,255,255,0.08)',position:'relative',transition:'background 0.2s'}}>
        <div style={{width:16,height:16,borderRadius:'50%',background:'#FFF',position:'absolute',top:3,left:value?21:3,transition:'left 0.2s'}}/>
      </button>
    </div>
  )
}

export default function AgentsGovernanceDemo() {
  const [cas, setCas] = useState<AgentCase>({ decisionType:'task_delegation', agentType:'Enterprise_Agent', environment:'production', reversibility:'partially_reversible', dataSensitivity:'low', taskComplexity:45, scopeBlastRadius:35, contextCompleteness:82, goalAlignment:80, safetyFlag:false, humanApprovalRequired:false, humanApproved:false, crossBoundary:false })
  const [checkpoints, setCheckpoints] = useState<CP[]>([])
  const [currentCp, setCurrentCp]   = useState(-1)
  const [finalResult, setFinalResult] = useState<string|null>(null)
  const [receiptId, setReceiptId]   = useState<string|null>(null)
  const [isRunning, setIsRunning]   = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout>|null>(null)

  const dt  = DECISION_TYPES.find(d=>d.value===cas.decisionType)||DECISION_TYPES[0]
  const agt = AGENT_TYPES.find(a=>a.value===cas.agentType)||AGENT_TYPES[0]
  const env = ENVIRONMENTS.find(e=>e.value===cas.environment)||ENVIRONMENTS[0]
  const rev = REVERSIBILITIES.find(r=>r.value===cas.reversibility)||REVERSIBILITIES[0]
  const _sen = DATA_SENSITIVITIES.find(s=>s.value===cas.dataSensitivity)||DATA_SENSITIVITIES[0]; void _sen

  const hb_safety  = cas.safetyFlag
  const hb_auth    = cas.humanApprovalRequired && !cas.humanApproved
  const anyHardBlock = hb_safety || hb_auth

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
            const verdict = anyHardBlock||bl>0?'BLOCKED':final.filter(c=>c.score<c.threshold+12).length>=3?'HOLD':'AUTHORIZED'
            setCheckpoints(final); setCurrentCp(-1); setFinalResult(verdict)
            if (verdict==='AUTHORIZED') setReceiptId(buildReceiptId())
            setIsRunning(false)
          }, 380)
        }
      }, i*300)
    })
  }

  const sIcon=(s:CP['status'])=>{
    if(s==='pending')    return <Clock size={15} style={{color:'#1E1230'}}/>
    if(s==='evaluating') return <Activity size={15} style={{color:AGT_VIOLET,animation:'pulse 0.8s ease-in-out infinite'}}/>
    if(s==='pass')       return <CheckCircle size={15} style={{color:'#10B981'}}/>
    if(s==='warn')       return <AlertTriangle size={15} style={{color:'#F59E0B'}}/>
    return <XCircle size={15} style={{color:'#EF4444'}}/>
  }
  const sColor=(s:CP['status'])=>s==='pass'?'#10B981':s==='warn'?'#F59E0B':s==='block'?'#EF4444':s==='evaluating'?AGT_VIOLET:'#1E1230'
  const vColor=(v:string|null)=>v==='AUTHORIZED'?'#10B981':v==='HOLD'?'#F59E0B':'#EF4444'
  const vBg=(v:string|null)=>v==='AUTHORIZED'?'rgba(16,185,129,0.10)':v==='HOLD'?'rgba(245,158,11,0.10)':'rgba(239,68,68,0.10)'
  const vBdr=(v:string|null)=>v==='AUTHORIZED'?'#10B98133':v==='HOLD'?'#F59E0B33':'#EF444433'

  const inp:React.CSSProperties={background:'#0D0815',border:'1px solid #1E1230',borderRadius:7,color:'#CBD5E1',padding:'9px 12px',fontSize:13,width:'100%',outline:'none',cursor:'pointer'}
  const lbl:React.CSSProperties={fontSize:10,color:'#3D2B6B',marginBottom:5,display:'block',fontWeight:700,textTransform:'uppercase',letterSpacing:'0.05em'}
  const sld:React.CSSProperties={width:'100%',accentColor:AGT_VIOLET,cursor:'pointer',height:4}

  return (
    <div style={{minHeight:'100vh',background:`linear-gradient(160deg,${AGT_DARK} 0%,#160F28 50%,#0A0612 100%)`,color:'#E2E8F0',fontFamily:"'Inter',sans-serif",padding:'24px'}}>
      <style>{`@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.25}} *{box-sizing:border-box} select option{background:#0D0815} input[type=range]::-webkit-slider-thumb{background:${AGT_VIOLET}}`}</style>
      <div style={{maxWidth:1320,margin:'0 auto'}}>

        <div style={{marginBottom:24}}>
          <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:14}}>
            <Link to="/" style={{color:'#2D1F4A',fontSize:12,textDecoration:'none'}}>← Home</Link>
            <span style={{color:'#1E1230',fontSize:12}}>/</span>
            <span style={{color:'#3D2B6B',fontSize:12}}>Autonomous Agent Governance</span>
          </div>
          <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',flexWrap:'wrap',gap:12}}>
            <div style={{display:'flex',alignItems:'center',gap:14}}>
              <div style={{width:50,height:50,borderRadius:12,display:'flex',alignItems:'center',justifyContent:'center',fontSize:24,background:`${AGT_VIOLET}18`,border:`1px solid ${AGT_VIOLET}44`}}>🤖</div>
              <div>
                <div style={{fontSize:22,fontWeight:800,letterSpacing:'-0.02em',color:'#F1F5F9'}}>Autonomous Agent Governance — Interactive Demo</div>
                <div style={{fontSize:12,color:'#2D1F4A',marginTop:3}}>ADR-AGT-001 · 11-Checkpoint Fail-Closed Pipeline · EU AI Act · NIST AI RMF · <span style={{color:AGT_LIGHT,fontFamily:'monospace'}}>OMNIX-AGT-{'{'+'12HEX'+'}'}</span> PQC Receipts</div>
              </div>
            </div>
            <div style={{display:'flex',gap:6,flexWrap:'wrap'}}>
              {['EU AI Act','NIST AI RMF','Principal Hierarchy','Blast Radius Gate'].map(b=>(
                <span key={b} style={{padding:'4px 10px',fontSize:10,fontWeight:700,borderRadius:5,background:`${AGT_VIOLET}14`,border:`1px solid ${AGT_VIOLET}33`,color:AGT_LIGHT,textTransform:'uppercase',letterSpacing:'0.04em'}}>{b}</span>
              ))}
            </div>
          </div>
        </div>

        <div style={{display:'flex',gap:8,marginBottom:20,flexWrap:'wrap',alignItems:'center'}}>
          <span style={{fontSize:10,color:'#2D1F4A',fontWeight:700,textTransform:'uppercase',letterSpacing:'0.06em',marginRight:4}}>Quick Load</span>
          {PRESETS.map(p=>(
            <button key={p.label} onClick={()=>applyPreset(p)} style={{padding:'6px 14px',fontSize:12,borderRadius:7,cursor:'pointer',background:`${AGT_VIOLET}10`,border:`1px solid ${AGT_VIOLET}28`,color:'#5B3FA0',fontWeight:600,display:'flex',alignItems:'center',gap:5}}
              onMouseEnter={e=>{(e.currentTarget as HTMLElement).style.borderColor=AGT_VIOLET;(e.currentTarget as HTMLElement).style.color=AGT_LIGHT}}
              onMouseLeave={e=>{(e.currentTarget as HTMLElement).style.borderColor=`${AGT_VIOLET}28`;(e.currentTarget as HTMLElement).style.color='#5B3FA0'}}
            >{p.emoji} {p.label}</button>
          ))}
        </div>

        <div style={{display:'grid',gridTemplateColumns:'390px 1fr',gap:18,alignItems:'start'}}>
          <div>
            <div style={{background:'rgba(13,8,21,0.95)',borderRadius:14,padding:22,border:`1px solid ${AGT_BORDER}`,marginBottom:14}}>
              <div style={{fontSize:13,fontWeight:700,color:AGT_LIGHT,marginBottom:18,display:'flex',alignItems:'center',gap:7}}>
                <Bot size={14} color={AGT_VIOLET}/> Agent Decision Parameters
              </div>

              {[['Decision Type','decisionType',DECISION_TYPES],['Agent Type','agentType',AGENT_TYPES],['Environment','environment',ENVIRONMENTS],['Reversibility','reversibility',REVERSIBILITIES],['Data Sensitivity','dataSensitivity',DATA_SENSITIVITIES]].map(([lbl_,key,opts])=>(
                <div key={key as string} style={{marginBottom:13}}>
                  <label style={lbl}>{lbl_ as string}</label>
                  <select style={inp} value={(cas as any)[key as string]} onChange={e=>{setCas(p=>({...p,[key as string]:e.target.value}));setCheckpoints([]);setFinalResult(null)}}>
                    {(opts as any[]).map((o:any)=><option key={o.value} value={o.value}>{o.emoji?o.emoji+' ':''}{o.label}{o.riskBase?` (risk ${o.riskBase}×)`:''}{o.strictness?` (${o.strictness}× strict)`:''}{o.factor&&(opts as any[]).length===4?` (risk ${o.factor}×)`:''}{o.penalty!==undefined?` (penalty -${o.penalty})`:''}</option>)}
                  </select>
                </div>
              ))}

              {[['Task Complexity','taskComplexity',5,95,'Low','High'],['Scope / Blast Radius','scopeBlastRadius',5,95,'Contained','Broad'],['Context Completeness','contextCompleteness',20,99,'Incomplete','Full'],['Goal Alignment','goalAlignment',20,99,'Misaligned','Aligned']].map(([lbl_,key,min_,max_,low,high])=>(
                <div key={key as string} style={{marginBottom:13}}>
                  <div style={{display:'flex',justifyContent:'space-between',marginBottom:5}}>
                    <label style={{...lbl,marginBottom:0}}>{lbl_ as string}</label>
                    <span style={{fontSize:13,fontWeight:700,color:AGT_LIGHT}}>{(cas as any)[key as string]}%</span>
                  </div>
                  <input type="range" min={min_ as number} max={max_ as number} step={1} style={sld} value={(cas as any)[key as string]} onChange={e=>{setCas(p=>({...p,[key as string]:parseInt(e.target.value)}));setCheckpoints([]);setFinalResult(null)}}/>
                  <div style={{display:'flex',justifyContent:'space-between',fontSize:10,color:'#1E1230',marginTop:2}}><span>{low as string}</span><span>{high as string}</span></div>
                </div>
              ))}

              <div style={{padding:'12px 0',borderTop:'1px solid #120A1E',marginBottom:16}}>
                <div style={{fontSize:10,color:'#2D1F4A',fontWeight:700,textTransform:'uppercase',letterSpacing:'0.06em',marginBottom:10}}>Safety & Authorization Flags</div>
                <Toggle label="Safety-Critical Flag" value={cas.safetyFlag} onChange={v=>{setCas(p=>({...p,safetyFlag:v}));setCheckpoints([]);setFinalResult(null)}} blockMsg={cas.safetyFlag?'⚠ HARD BLOCK — human review mandatory':undefined}/>
                <Toggle label="Human Approval Required" value={cas.humanApprovalRequired} onChange={v=>{setCas(p=>({...p,humanApprovalRequired:v}));setCheckpoints([]);setFinalResult(null)}}/>
                <Toggle label="Human Approved" value={cas.humanApproved} onChange={v=>{setCas(p=>({...p,humanApproved:v}));setCheckpoints([]);setFinalResult(null)}} blockMsg={cas.humanApprovalRequired&&!cas.humanApproved?'⚠ HARD BLOCK — approval required but not granted':undefined}/>
                <Toggle label="Cross Trust Boundary" value={cas.crossBoundary} onChange={v=>{setCas(p=>({...p,crossBoundary:v}));setCheckpoints([]);setFinalResult(null)}}/>
              </div>

              {anyHardBlock&&(
                <div style={{background:'rgba(239,68,68,0.08)',border:'1px solid #EF444430',borderRadius:8,padding:'10px 14px',marginBottom:16}}>
                  <div style={{color:'#EF4444',fontWeight:700,fontSize:11,marginBottom:6}}>⚠ Hard Block Active — Will BLOCK before evaluation</div>
                  {hb_safety&&<div style={{color:'#FCA5A5',fontSize:11,marginBottom:3}}>• Safety-critical flag — autonomous execution suspended</div>}
                  {hb_auth  &&<div style={{color:'#FCA5A5',fontSize:11}}>• Human approval required but not granted — principal breach</div>}
                </div>
              )}

              <button onClick={runEval} disabled={isRunning} style={{width:'100%',padding:'13px 20px',borderRadius:10,border:'none',background:isRunning?'#1E293B':`linear-gradient(135deg,#3730A3,${AGT_VIOLET})`,color:isRunning?'#374151':'#FFF',fontWeight:700,fontSize:14,cursor:isRunning?'not-allowed':'pointer',display:'flex',alignItems:'center',justifyContent:'center',gap:8}}>
                <Bot size={15}/>{isRunning?'Evaluating Agent Action…':'Run 11-Checkpoint Agent Governance'}{!isRunning&&<ArrowRight size={15}/>}
              </button>
            </div>

            <div style={{background:'rgba(13,8,21,0.95)',borderRadius:12,padding:16,border:'1px solid #1E1230',fontSize:12}}>
              <div style={{color:'#2D1F4A',fontWeight:700,marginBottom:10,fontSize:10,textTransform:'uppercase',letterSpacing:'0.06em'}}>Current Action</div>
              {[[`Decision`,`${dt.emoji} ${dt.label}`],[`Agent`,agt.label],[`Environment`,`${env.label} (${env.strictness}× strict)`],[`Reversibility`,rev.label],[`Blast Radius`,`${cas.scopeBlastRadius}%`],[`Context`,`${cas.contextCompleteness}%`],[`Goal`,`${cas.goalAlignment}%`],[`Safety`,cas.safetyFlag?'⚠ RAISED':'Clear'],[`Approval`,cas.humanApprovalRequired?(cas.humanApproved?'✓ Granted':'✗ NOT GRANTED'):'Not required']].map(([k,v])=>(
                <div key={k as string} style={{display:'flex',justifyContent:'space-between',marginBottom:5,paddingBottom:5,borderBottom:'1px solid #0D0815'}}>
                  <span style={{color:'#1E1230'}}>{k}</span><span style={{color:(v as string).includes('RAISED')||(v as string).includes('NOT GRANTED')?'#EF4444':'#5B3FA0',fontWeight:600,textAlign:'right',maxWidth:200}}>{v}</span>
                </div>
              ))}
            </div>
          </div>

          <div>
            {checkpoints.length===0?(
              <div style={{background:'rgba(13,8,21,0.95)',borderRadius:14,padding:52,border:`1px solid ${AGT_BORDER}`,textAlign:'center'}}>
                <div style={{fontSize:52,marginBottom:18}}>🤖</div>
                <div style={{fontSize:18,fontWeight:700,color:AGT_LIGHT,marginBottom:10}}>Autonomous Agent Governance Pipeline</div>
                <div style={{color:'#2D1F4A',fontSize:13,maxWidth:460,margin:'0 auto',lineHeight:1.7}}>Configure an autonomous agent action on the left — decision type, agent class, environment, reversibility, blast radius, and authorization. Run the 11-checkpoint EU AI Act / NIST AI RMF governance pipeline. Every authorized action generates a PQC-signed <span style={{color:AGT_LIGHT,fontFamily:'monospace'}}>OMNIX-AGT</span> receipt.</div>
                <div style={{marginTop:28,display:'flex',justifyContent:'center',gap:10,flexWrap:'wrap'}}>
                  {['Task Viability','Blast Radius','Context Coherence','Principal Hierarchy','PQC Receipt'].map(s=>(
                    <span key={s} style={{background:`${AGT_VIOLET}12`,border:`1px solid ${AGT_BORDER}`,borderRadius:6,padding:'5px 12px',fontSize:11,color:AGT_LIGHT,fontWeight:500}}>{s}</span>
                  ))}
                </div>
                <div style={{marginTop:28,display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:10,maxWidth:480,margin:'28px auto 0'}}>
                  {[{icon:<Zap size={14}/>,label:'Sub-second evaluation'},{icon:<Shield size={14}/>,label:'2 hard block conditions'},{icon:<Lock size={14}/>,label:'Dilithium-3 PQC receipt'}].map((item,i)=>(
                    <div key={i} style={{background:'#0D0815',border:'1px solid #1E1230',borderRadius:8,padding:'12px 10px',display:'flex',flexDirection:'column',alignItems:'center',gap:6}}>
                      <div style={{color:AGT_VIOLET}}>{item.icon}</div><div style={{fontSize:10,color:'#2D1F4A',textAlign:'center'}}>{item.label}</div>
                    </div>
                  ))}
                </div>
              </div>
            ):(
              <div>
                {finalResult&&(
                  <div style={{borderRadius:12,padding:'16px 20px',marginBottom:14,background:vBg(finalResult),border:`1px solid ${vBdr(finalResult)}`,display:'flex',justifyContent:'space-between',alignItems:'center',flexWrap:'wrap',gap:12}}>
                    <div style={{display:'flex',alignItems:'center',gap:12}}>
                      {finalResult==='AUTHORIZED'?<CheckCircle size={22} style={{color:'#10B981'}}/>:finalResult==='HOLD'?<AlertTriangle size={22} style={{color:'#F59E0B'}}/>:<XCircle size={22} style={{color:'#EF4444'}}/>}
                      <div>
                        <div style={{fontWeight:800,fontSize:17,color:vColor(finalResult)}}>{finalResult==='AUTHORIZED'?'AGENT ACTION AUTHORIZED':finalResult==='HOLD'?'HOLD — HUMAN OVERSIGHT REQUIRED':'BLOCKED — GOVERNANCE THRESHOLD BREACH'}</div>
                        {receiptId&&<div style={{fontSize:11,color:'#10B981',fontFamily:'monospace',marginTop:3}}>Receipt: {receiptId} · Dilithium-3 · ADR-AGT-001</div>}
                        {!receiptId&&<div style={{fontSize:11,color:'#EF4444',marginTop:3}}>No receipt — agent action blocked by governance pipeline</div>}
                      </div>
                    </div>
                    <div style={{textAlign:'right',fontSize:11,color:'#2D1F4A'}}>
                      <div>{dt.emoji} {dt.label}</div>
                      <div>{agt.label} · {env.label}</div>
                    </div>
                  </div>
                )}
                <div style={{display:'flex',flexDirection:'column',gap:9}}>
                  {checkpoints.map((cp,i)=>{
                    const isActive=currentCp===i
                    const bdrC=cp.status==='evaluating'?AGT_VIOLET:cp.status==='pass'?'#10B981':cp.status==='warn'?'#F59E0B':cp.status==='block'?'#EF4444':'#1E1230'
                    const barC=cp.status==='pass'?'#10B981':cp.status==='warn'?'#F59E0B':cp.status==='block'?'#EF4444':AGT_VIOLET
                    return (
                      <div key={i} style={{background:isActive?`${AGT_VIOLET}08`:'rgba(13,8,21,0.92)',borderRadius:10,padding:'13px 15px',border:`1px solid ${bdrC}44`,transition:'all 0.3s'}}>
                        <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:8}}>
                          <div style={{display:'flex',alignItems:'center',gap:8,flex:1}}>
                            {sIcon(cp.status)}
                            <div><div style={{fontSize:13,fontWeight:700,color:'#E2E8F0'}}>{cp.name}</div><div style={{fontSize:10,color:'#2D1F4A'}}>{cp.genericName}</div></div>
                          </div>
                          <div style={{textAlign:'right',flexShrink:0,marginLeft:12}}>
                            <div style={{fontSize:20,fontWeight:800,color:sColor(cp.status),lineHeight:1}}>{cp.score}</div>
                            <div style={{fontSize:10,color:'#1E1230'}}>min {cp.threshold}</div>
                          </div>
                        </div>
                        <ScoreBar score={cp.score} threshold={cp.threshold} color={barC}/>
                        {cp.status!=='pending'&&(
                          <div style={{marginTop:10}}>
                            <div style={{fontSize:12,color:'#94A3B8',lineHeight:1.55,marginBottom:6}}>{cp.reasoning}</div>
                            <div style={{fontSize:10,color:'#2D1F4A',fontFamily:'monospace',background:'#0D0815',padding:'6px 10px',borderRadius:5}}>{cp.detail}</div>
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

        <div style={{marginTop:28,textAlign:'center',color:'#1E1230',fontSize:11}}>
          OMNIX Quantum · Autonomous Agent Governance · ADR-AGT-001 · 11-Checkpoint Fail-Closed Pipeline
          &nbsp;·&nbsp; EU AI Act · NIST AI RMF · Principal Hierarchy · Dilithium-3 PQC
          &nbsp;·&nbsp; <Link to="/try" style={{color:AGT_VIOLET,textDecoration:'none'}}>Public Sandbox →</Link>
          &nbsp;·&nbsp; <Link to="/" style={{color:AGT_VIOLET,textDecoration:'none'}}>Back to Platform →</Link>
        </div>
      </div>
    </div>
  )
}
