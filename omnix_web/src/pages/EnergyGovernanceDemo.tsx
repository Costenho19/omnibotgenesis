import { useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield, CheckCircle, XCircle, AlertTriangle, Activity, Clock,
  Building2, TrendingUp, Layers, Target, Brain, ArrowRight, Zap, Lock,
} from 'lucide-react'

const ENR_ORANGE = '#F97316'
const ENR_LIGHT  = '#FB923C'
const ENR_DARK   = '#120700'
const ENR_BORDER = '#F9731633'

const ENERGY_SOURCES = [
  { value:'natural_gas', label:'Natural Gas (Henry Hub)', emoji:'🔥', baseVol:0.18, avgPrice:2.85,  unit:'MMBtu'  },
  { value:'crude_oil',   label:'Crude Oil (WTI)',         emoji:'🛢️', baseVol:0.22, avgPrice:78.50, unit:'barrel' },
  { value:'solar',       label:'Solar PPA (Utility)',     emoji:'☀️', baseVol:0.12, avgPrice:45.00, unit:'MWh'   },
  { value:'wind',        label:'Wind Power (Onshore)',    emoji:'💨', baseVol:0.25, avgPrice:38.00, unit:'MWh'   },
  { value:'lng',         label:'LNG Spot (Asia-Pacific)', emoji:'🚢', baseVol:0.32, avgPrice:12.40, unit:'MMBtu'  },
  { value:'electricity', label:'Electricity (Day-Ahead)', emoji:'⚡', baseVol:0.35, avgPrice:55.00, unit:'MWh'   },
]

const DELIVERY_WINDOWS = [
  { value:'spot',        label:'Spot / Same-Day',       risk:0.35, premium:1.15 },
  { value:'week_ahead',  label:'Week-Ahead',            risk:0.22, premium:1.05 },
  { value:'month_ahead', label:'Month-Ahead',           risk:0.15, premium:1.00 },
  { value:'quarter',     label:'Quarterly Forward',     risk:0.10, premium:0.95 },
  { value:'annual',      label:'Annual Contract',       risk:0.08, premium:0.90 },
]

const GRID_CONDITIONS = [
  { value:'stable',     label:'Stable Grid (Normal Load)',           factor:0.90 },
  { value:'peak',       label:'Peak Demand (High Load)',             factor:0.55 },
  { value:'off_peak',   label:'Off-Peak (Low Demand)',               factor:0.85 },
  { value:'congestion', label:'Transmission Congestion',             factor:0.35 },
  { value:'emergency',  label:'Grid Emergency / Rolling Blackouts',  factor:0.10 },
]

const WEATHER_OUTLOOK = [
  { value:'favorable', label:'Favorable (Mild, Predictable)',         factor:0.90 },
  { value:'seasonal',  label:'Seasonal Normal',                       factor:0.75 },
  { value:'volatile',  label:'Volatile (Storm Watch)',                factor:0.40 },
  { value:'extreme',   label:'Extreme Event (Hurricane / Polar Vortex)',factor:0.15 },
]

const REGULATORY_ENV = [
  { value:'stable',         label:'Stable Regulatory Framework',             factor:0.90 },
  { value:'transitioning',  label:'Energy Transition (IRA / EU Green Deal)', factor:0.70 },
  { value:'uncertain',      label:'Regulatory Uncertainty',                  factor:0.45 },
  { value:'hostile',        label:'Adverse Regulation (Carbon Tax / Caps)',   factor:0.20 },
]

interface EnergyTrade {
  energySource:   string
  contractSize:   number
  deliveryWindow: string
  gridCondition:  string
  weatherOutlook: string
  regulatoryEnv:  string
}

const PRESETS: { label:string; emoji:string; s:EnergyTrade }[] = [
  { label:'Natural Gas — Month Ahead', emoji:'🔥', s:{ energySource:'natural_gas', contractSize:250, deliveryWindow:'month_ahead', gridCondition:'stable',     weatherOutlook:'seasonal',  regulatoryEnv:'stable'        } },
  { label:'Solar PPA — Stable',        emoji:'☀️', s:{ energySource:'solar',       contractSize:100, deliveryWindow:'annual',      gridCondition:'stable',     weatherOutlook:'favorable', regulatoryEnv:'transitioning' } },
  { label:'LNG Spot — High Vol',       emoji:'🚢', s:{ energySource:'lng',         contractSize:400, deliveryWindow:'spot',        gridCondition:'peak',       weatherOutlook:'volatile',  regulatoryEnv:'uncertain'     } },
  { label:'Wind Power — Standard',     emoji:'💨', s:{ energySource:'wind',        contractSize:200, deliveryWindow:'quarter',     gridCondition:'off_peak',   weatherOutlook:'seasonal',  regulatoryEnv:'transitioning' } },
  { label:'Grid Emergency — Block',    emoji:'⚠️', s:{ energySource:'electricity', contractSize:800, deliveryWindow:'spot',        gridCondition:'emergency',  weatherOutlook:'extreme',   regulatoryEnv:'hostile'       } },
]

interface CP {
  name:string; genericName:string; icon:React.ReactNode
  status:'pending'|'evaluating'|'pass'|'warn'|'block'
  score:number; threshold:number; reasoning:string; detail:string
}

function buildCheckpoints(trade: EnergyTrade): CP[] {
  const src  = ENERGY_SOURCES.find(s=>s.value===trade.energySource)||ENERGY_SOURCES[0]
  const del_ = DELIVERY_WINDOWS.find(d=>d.value===trade.deliveryWindow)||DELIVERY_WINDOWS[0]
  const grid = GRID_CONDITIONS.find(g=>g.value===trade.gridCondition)||GRID_CONDITIONS[0]
  const wx   = WEATHER_OUTLOOK.find(w=>w.value===trade.weatherOutlook)||WEATHER_OUTLOOK[0]
  const reg  = REGULATORY_ENV.find(r=>r.value===trade.regulatoryEnv)||REGULATORY_ENV[0]

  const baseConf = (1-src.baseVol)*0.4+grid.factor*0.3+wx.factor*0.3
  const delAdj = del_.risk*0.25
  const adjConf = Math.min(0.98,Math.max(0.05,baseConf-delAdj))
  const forecastScore = Math.round(adjConf*100)
  const sizeRatio = trade.contractSize/500
  const srcExp = src.baseVol*80; const delExp = del_.risk*60
  const concRisk = Math.min(100,Math.round((sizeRatio*25+srcExp+delExp)*0.5))
  const exposureScore = Math.max(0,100-concRisk)
  const gridSig = Math.round(grid.factor*100); const wxSig = Math.round(wx.factor*100); const delSig = Math.max(0,Math.round((1-del_.risk)*100))
  const sdCoherence = Math.round(gridSig*0.35+wxSig*0.35+delSig*0.30)
  const gridTrend = grid.factor>=0.8?85:grid.factor>=0.5?60:grid.factor>=0.3?35:15
  const wxTrend = wx.factor>=0.7?80:wx.factor>=0.4?50:20
  const trendScore = Math.round(gridTrend*0.5+wxTrend*0.3+(1-src.baseVol)*100*0.2)
  const stressScore = Math.round(reg.factor*40+wx.factor*35+grid.factor*25)
  const signals = [forecastScore,exposureScore,sdCoherence,trendScore,stressScore]
  const avg = signals.reduce((a,b)=>a+b,0)/signals.length
  const variance = signals.reduce((a,b)=>a+Math.pow(b-avg,2),0)/signals.length
  const divergence = Math.sqrt(variance)
  const logicScore = Math.round(Math.max(0,Math.min(100,100-divergence*2.2)))
  const sivScore = Math.min(95,Math.round(70+grid.factor*15+wx.factor*10))
  const temporalScore = Math.min(95,Math.round(trendScore*0.70+(del_.risk<0.3?20:8)))
  const edgeScore = Math.round(forecastScore*0.55+logicScore*0.45)
  const amlScore = Math.min(95,Math.round(88-Math.max(0,(trade.contractSize-500)/200*8)))
  const fraudScore = Math.min(95,Math.round(62+sdCoherence*0.33))

  return [
    { name:'Signal Integrity Validation',  genericName:'CP-1: All energy signals valid?',       icon:<Shield size={15}/>,       status:'pending', score:sivScore,      threshold:60, reasoning:sivScore>=60?`All signals validated — source, grid, weather, delivery, regulatory inputs consistent`:`Validation failed — energy trade parameters outside governance bounds`,                                                               detail:`5/5 valid | Grid: ${(grid.factor*100).toFixed(0)}% | Weather: ${(wx.factor*100).toFixed(0)}% | SIV: ${sivScore}/100` },
    { name:'Price Forecast Confidence',    genericName:'CP-2: Execution confidence?',            icon:<Target size={15}/>,       status:'pending', score:forecastScore, threshold:55, reasoning:forecastScore>=55?`Forecast ${forecastScore}% — ${src.label} vol ${(src.baseVol*100).toFixed(0)}% with ${del_.label} delivery supports execution`:`Forecast ${forecastScore}% — ${src.label} volatility + ${del_.label} creates excessive uncertainty`, detail:`Vol: ${(src.baseVol*100).toFixed(0)}% | Grid: ${(grid.factor*100).toFixed(0)}% | Weather: ${(wx.factor*100).toFixed(0)}% | Delivery risk: ${(del_.risk*100).toFixed(0)}% → ${forecastScore}%` },
    { name:'Grid Exposure Limits',         genericName:'CP-3: Portfolio concentration safe?',    icon:<Shield size={15}/>,       status:'pending', score:exposureScore, threshold:45, reasoning:exposureScore>=45?`Exposure within grid capacity limits — ${trade.contractSize} ${src.unit} within concentration thresholds`:`Excessive exposure — ${trade.contractSize} ${src.unit} creates ${concRisk}% concentration risk`,                                       detail:`Size ratio: ${sizeRatio.toFixed(1)}× | Source: ${srcExp.toFixed(0)}% | Delivery: ${delExp.toFixed(0)}% | Conc: ${concRisk}% → ${exposureScore}/100` },
    { name:'Supply-Demand Coherence',      genericName:'CP-4: Grid / weather / delivery agree?', icon:<Layers size={15}/>,       status:'pending', score:sdCoherence,   threshold:50, reasoning:sdCoherence>=50?`Grid, weather, and delivery signals aligned (${sdCoherence}% coherence)`:`Conflicting — grid ${grid.label.split('(')[0].trim()} vs weather ${wx.label.split('(')[0].trim()} and delivery diverge`,                                      detail:`Grid: ${gridSig} | Weather: ${wxSig} | Delivery: ${delSig} → Coherence: ${sdCoherence}%` },
    { name:'Price Trend Persistence',      genericName:'CP-5: Sustained conditions, not noise?', icon:<TrendingUp size={15}/>,   status:'pending', score:trendScore,    threshold:40, reasoning:trendScore>=40?`Grid and weather trends confirm sustained conditions — not transient volatility spike`:`Conditions appear transient — insufficient trend persistence for confident execution`,                                                              detail:`Grid trend: ${gridTrend} | Weather trend: ${wxTrend} | Vol stability: ${((1-src.baseVol)*100).toFixed(0)}% → ${trendScore}/100` },
    { name:'Regulatory & Climate Stress',  genericName:'CP-6: Resilient to adverse conditions?', icon:<AlertTriangle size={15}/>, status:'pending', score:stressScore,   threshold:35, reasoning:stressScore>=35?`Regulatory (${reg.label.split('(')[0].trim()}) and climate outlook adequate under stress`:`Stress test failed — ${reg.label.split('(')[0].trim()} regulation + ${wx.label.split('(')[0].trim()} creates unacceptable tail risk`,          detail:`Regulatory: ${(reg.factor*100).toFixed(0)}% | Weather stress: ${(wx.factor*100).toFixed(0)}% | Grid stress: ${(grid.factor*100).toFixed(0)}% → ${stressScore}/100` },
    { name:'Signal Contradiction (SCG)',   genericName:'CP-7: Contradicting signals?',           icon:<Brain size={15}/>,        status:'pending', score:logicScore,    threshold:40, reasoning:logicScore>=40?`Internal divergence low — energy signals consistent (${logicScore}%)`:`High contradiction — divergence ${divergence.toFixed(1)} indicates conflicting risk assessment`,                                                                 detail:`Variance: ${divergence.toFixed(1)} | Consistency: ${logicScore}% | ${logicScore<40?'CONTRADICTORY':logicScore<60?'TENSIONED':'ALIGNED'}` },
    { name:'Temporal Coherence',           genericName:'CP-8: Conditions stable over time?',    icon:<Activity size={15}/>,     status:'pending', score:temporalScore, threshold:40, reasoning:temporalScore>=40?`Price trend and delivery window confirm temporal consistency of energy trade`:`Temporal instability — grid and weather may be transient conditions`,                                                                                     detail:`Trend base: ${trendScore} | Delivery risk: ${(del_.risk*100).toFixed(0)}% | Temporal: ${temporalScore}/100` },
    { name:'Edge Confirmation (ECW)',      genericName:'CP-9: Decision converges at boundary?',  icon:<Target size={15}/>,       status:'pending', score:edgeScore,     threshold:48, reasoning:edgeScore>=48?`Boundary confirmed — forecast and logic converge at governance edge (${edgeScore}%)`:`Weak boundary — forecast and consistency don't reinforce each other`,                                                                                  detail:`Forecast×0.55: ${(forecastScore*0.55).toFixed(0)} | Logic×0.45: ${(logicScore*0.45).toFixed(0)} | Edge: ${edgeScore}/100` },
    { name:'AML Compliance Gate',          genericName:'CP-10: Passes AML/compliance screen?',  icon:<Building2 size={15}/>,    status:'pending', score:amlScore,      threshold:60, reasoning:amlScore>=60?`AML screen passed — contract size and regulatory environment show no anomalous patterns`:`AML flag — contract size and regulatory complexity require enhanced compliance review`,                                                              detail:`Contract: ${trade.contractSize} ${src.unit} | Reg env: ${reg.label.split('(')[0].trim()} | AML: ${amlScore}/100` },
    { name:'Fraud Detection Gate',         genericName:'CP-11: Anomalous price signal patterns?',icon:<AlertTriangle size={15}/>, status:'pending', score:fraudScore,   threshold:55, reasoning:fraudScore>=55?`Fraud screen passed — supply-demand coherence shows no price manipulation patterns`:`Fraud flag — unusual coherence patterns may indicate price signal manipulation`,                                                                      detail:`Coherence base: ${sdCoherence} | Fraud: ${fraudScore}/100 | ${fraudScore<55?'ELEVATED — compliance review':'CLEAN PROFILE'}` },
  ]
}

function buildReceiptId() {
  return `OMNIX-ENR-${Array.from({length:12},()=>Math.floor(Math.random()*16).toString(16).toUpperCase()).join('')}`
}

function ScoreBar({ score, threshold, color }: { score:number; threshold:number; color:string }) {
  return (
    <div style={{ position:'relative', height:6, background:'#1A0E00', borderRadius:3, overflow:'visible' }}>
      <div style={{ position:'absolute', left:`${threshold}%`, top:-3, width:2, height:12, background:'#F59E0B', borderRadius:1, zIndex:2 }}/>
      <div style={{ height:'100%', width:`${Math.min(score,100)}%`, background:color, borderRadius:3, transition:'width 0.9s ease' }}/>
    </div>
  )
}

export default function EnergyGovernanceDemo() {
  const [trade, setTrade] = useState<EnergyTrade>({ energySource:'natural_gas', contractSize:250, deliveryWindow:'month_ahead', gridCondition:'stable', weatherOutlook:'seasonal', regulatoryEnv:'stable' })
  const [checkpoints, setCheckpoints] = useState<CP[]>([])
  const [currentCp, setCurrentCp]   = useState(-1)
  const [finalResult, setFinalResult] = useState<string|null>(null)
  const [receiptId, setReceiptId]   = useState<string|null>(null)
  const [isRunning, setIsRunning]   = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout>|null>(null)

  const src  = ENERGY_SOURCES.find(s=>s.value===trade.energySource)||ENERGY_SOURCES[0]
  const del_ = DELIVERY_WINDOWS.find(d=>d.value===trade.deliveryWindow)||DELIVERY_WINDOWS[0]
  const grid = GRID_CONDITIONS.find(g=>g.value===trade.gridCondition)||GRID_CONDITIONS[0]
  const wx   = WEATHER_OUTLOOK.find(w=>w.value===trade.weatherOutlook)||WEATHER_OUTLOOK[0]

  const hb_grid_emergency = trade.gridCondition === 'emergency'
  const hb_extreme_spot   = trade.weatherOutlook === 'extreme' && trade.deliveryWindow === 'spot'
  const anyHardBlock = hb_grid_emergency || hb_extreme_spot

  function applyPreset(p: typeof PRESETS[0]) { setTrade({...p.s}); setCheckpoints([]); setFinalResult(null); setReceiptId(null); setCurrentCp(-1) }

  function runEval() {
    if (isRunning) return
    const cps = buildCheckpoints(trade)
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
            const verdict = anyHardBlock||hb>0?'BLOCKED':bl>=3?'BLOCKED':bl>0?'HOLD':'EXECUTE'
            setCheckpoints(final); setCurrentCp(-1); setFinalResult(verdict)
            if (verdict==='EXECUTE') setReceiptId(buildReceiptId())
            setIsRunning(false)
          }, 380)
        }
      }, i*300)
    })
  }

  const sIcon=(s:CP['status'])=>{
    if(s==='pending')    return <Clock size={15} style={{color:'#2A1200'}}/>
    if(s==='evaluating') return <Activity size={15} style={{color:ENR_ORANGE,animation:'pulse 0.8s ease-in-out infinite'}}/>
    if(s==='pass')       return <CheckCircle size={15} style={{color:'#10B981'}}/>
    if(s==='warn')       return <AlertTriangle size={15} style={{color:'#F59E0B'}}/>
    return <XCircle size={15} style={{color:'#EF4444'}}/>
  }
  const sColor=(s:CP['status'])=>s==='pass'?'#10B981':s==='warn'?'#F59E0B':s==='block'?'#EF4444':s==='evaluating'?ENR_ORANGE:'#2A1200'
  const vColor=(v:string|null)=>v==='EXECUTE'?'#10B981':v==='HOLD'?'#F59E0B':'#EF4444'
  const vBg=(v:string|null)=>v==='EXECUTE'?'rgba(16,185,129,0.10)':v==='HOLD'?'rgba(245,158,11,0.10)':'rgba(239,68,68,0.10)'
  const vBdr=(v:string|null)=>v==='EXECUTE'?'#10B98133':v==='HOLD'?'#F59E0B33':'#EF444433'

  const inp:React.CSSProperties={background:'#120700',border:'1px solid #2A1200',borderRadius:7,color:'#CBD5E1',padding:'9px 12px',fontSize:13,width:'100%',outline:'none',cursor:'pointer'}
  const lbl:React.CSSProperties={fontSize:10,color:'#6B3500',marginBottom:5,display:'block',fontWeight:700,textTransform:'uppercase',letterSpacing:'0.05em'}
  const sld:React.CSSProperties={width:'100%',accentColor:ENR_ORANGE,cursor:'pointer',height:4}

  return (
    <div style={{minHeight:'100vh',background:`linear-gradient(160deg,${ENR_DARK} 0%,#1A0E00 50%,#0F0700 100%)`,color:'#E2E8F0',fontFamily:"'Inter',sans-serif",padding:'24px'}}>
      <style>{`@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.25}} *{box-sizing:border-box} select option{background:#120700} input[type=range]::-webkit-slider-thumb{background:${ENR_ORANGE}}`}</style>
      <div style={{maxWidth:1320,margin:'0 auto'}}>

        <div style={{marginBottom:24}}>
          <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:14}}>
            <Link to="/" style={{color:'#4B2200',fontSize:12,textDecoration:'none'}}>← Home</Link>
            <span style={{color:'#2A1200',fontSize:12}}>/</span>
            <span style={{color:'#6B3500',fontSize:12}}>Energy Trading Governance</span>
          </div>
          <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',flexWrap:'wrap',gap:12}}>
            <div style={{display:'flex',alignItems:'center',gap:14}}>
              <div style={{width:50,height:50,borderRadius:12,display:'flex',alignItems:'center',justifyContent:'center',fontSize:24,background:`${ENR_ORANGE}18`,border:`1px solid ${ENR_ORANGE}44`}}>⚡</div>
              <div>
                <div style={{fontSize:22,fontWeight:800,letterSpacing:'-0.02em',color:'#F1F5F9'}}>Energy Trading Governance — Interactive Demo</div>
                <div style={{fontSize:12,color:'#4B2200',marginTop:3}}>ADR-ENR-001 · 11-Checkpoint Fail-Closed Pipeline · FERC · EU ETS · <span style={{color:ENR_LIGHT,fontFamily:'monospace'}}>OMNIX-ENR-{'{'+'12HEX'+'}'}</span> PQC Receipts</div>
              </div>
            </div>
            <div style={{display:'flex',gap:6,flexWrap:'wrap'}}>
              {['FERC Compliant','EU ETS / IRA','Grid Risk Gate','Cat Weather Stress'].map(b=>(
                <span key={b} style={{padding:'4px 10px',fontSize:10,fontWeight:700,borderRadius:5,background:`${ENR_ORANGE}14`,border:`1px solid ${ENR_ORANGE}33`,color:ENR_LIGHT,textTransform:'uppercase',letterSpacing:'0.04em'}}>{b}</span>
              ))}
            </div>
          </div>
        </div>

        <div style={{display:'flex',gap:8,marginBottom:20,flexWrap:'wrap',alignItems:'center'}}>
          <span style={{fontSize:10,color:'#4B2200',fontWeight:700,textTransform:'uppercase',letterSpacing:'0.06em',marginRight:4}}>Quick Load</span>
          {PRESETS.map(p=>(
            <button key={p.label} onClick={()=>applyPreset(p)} style={{padding:'6px 14px',fontSize:12,borderRadius:7,cursor:'pointer',background:`${ENR_ORANGE}10`,border:`1px solid ${ENR_ORANGE}28`,color:'#7A3B00',fontWeight:600,display:'flex',alignItems:'center',gap:5}}
              onMouseEnter={e=>{(e.currentTarget as HTMLElement).style.borderColor=ENR_ORANGE;(e.currentTarget as HTMLElement).style.color=ENR_LIGHT}}
              onMouseLeave={e=>{(e.currentTarget as HTMLElement).style.borderColor=`${ENR_ORANGE}28`;(e.currentTarget as HTMLElement).style.color='#7A3B00'}}
            >{p.emoji} {p.label}</button>
          ))}
        </div>

        <div style={{display:'grid',gridTemplateColumns:'390px 1fr',gap:18,alignItems:'start'}}>
          <div>
            <div style={{background:'rgba(18,7,0,0.95)',borderRadius:14,padding:22,border:`1px solid ${ENR_BORDER}`,marginBottom:14}}>
              <div style={{fontSize:13,fontWeight:700,color:ENR_LIGHT,marginBottom:18,display:'flex',alignItems:'center',gap:7}}>
                <Zap size={14} color={ENR_ORANGE}/> Energy Trade Configuration
              </div>

              <div style={{marginBottom:13}}>
                <label style={lbl}>Energy Source</label>
                <select style={inp} value={trade.energySource} onChange={e=>{setTrade(p=>({...p,energySource:e.target.value}));setCheckpoints([]);setFinalResult(null)}}>
                  {ENERGY_SOURCES.map(s=><option key={s.value} value={s.value}>{s.emoji} {s.label} (Vol: {(s.baseVol*100).toFixed(0)}%)</option>)}
                </select>
                <div style={{fontSize:10,color:'#6B3500',marginTop:4}}>Avg price: ${src.avgPrice.toFixed(2)}/{src.unit} · Base vol: {(src.baseVol*100).toFixed(0)}%</div>
              </div>

              <div style={{marginBottom:13}}>
                <div style={{display:'flex',justifyContent:'space-between',marginBottom:5}}>
                  <label style={{...lbl,marginBottom:0}}>Contract Size ({src.unit})</label>
                  <span style={{fontSize:13,fontWeight:700,color:trade.contractSize>500?'#F59E0B':ENR_LIGHT}}>{trade.contractSize} {src.unit}</span>
                </div>
                <input type="range" min={10} max={2000} step={10} style={sld} value={trade.contractSize} onChange={e=>{setTrade(p=>({...p,contractSize:parseInt(e.target.value)}));setCheckpoints([]);setFinalResult(null)}}/>
                <div style={{fontSize:10,color:'#2A1200',marginTop:2}}>Est. value: ${(trade.contractSize*src.avgPrice).toLocaleString()}</div>
              </div>

              <div style={{marginBottom:13}}>
                <label style={lbl}>Delivery Window</label>
                <select style={inp} value={trade.deliveryWindow} onChange={e=>{setTrade(p=>({...p,deliveryWindow:e.target.value}));setCheckpoints([]);setFinalResult(null)}}>
                  {DELIVERY_WINDOWS.map(d=><option key={d.value} value={d.value}>{d.label}</option>)}
                </select>
                <div style={{fontSize:10,color:'#6B3500',marginTop:4}}>Delivery risk: {(del_.risk*100).toFixed(0)}%</div>
              </div>

              <div style={{marginBottom:13}}>
                <label style={lbl}>Grid Condition</label>
                <select style={inp} value={trade.gridCondition} onChange={e=>{setTrade(p=>({...p,gridCondition:e.target.value}));setCheckpoints([]);setFinalResult(null)}}>
                  {GRID_CONDITIONS.map(g=><option key={g.value} value={g.value}>{g.label}</option>)}
                </select>
                {hb_grid_emergency&&<div style={{fontSize:10,color:'#EF4444',marginTop:4,fontWeight:700}}>⚠ HARD BLOCK — Grid emergency conditions prohibit autonomous trade execution</div>}
              </div>

              <div style={{marginBottom:13}}>
                <label style={lbl}>Weather Outlook</label>
                <select style={inp} value={trade.weatherOutlook} onChange={e=>{setTrade(p=>({...p,weatherOutlook:e.target.value}));setCheckpoints([]);setFinalResult(null)}}>
                  {WEATHER_OUTLOOK.map(w=><option key={w.value} value={w.value}>{w.label}</option>)}
                </select>
                {hb_extreme_spot&&<div style={{fontSize:10,color:'#EF4444',marginTop:4,fontWeight:700}}>⚠ HARD BLOCK — Extreme weather + spot delivery = price signal unreliable</div>}
              </div>

              <div style={{marginBottom:18}}>
                <label style={lbl}>Regulatory Environment</label>
                <select style={inp} value={trade.regulatoryEnv} onChange={e=>{setTrade(p=>({...p,regulatoryEnv:e.target.value}));setCheckpoints([]);setFinalResult(null)}}>
                  {REGULATORY_ENV.map(r=><option key={r.value} value={r.value}>{r.label}</option>)}
                </select>
              </div>

              {anyHardBlock&&(
                <div style={{background:'rgba(239,68,68,0.08)',border:'1px solid #EF444430',borderRadius:8,padding:'10px 14px',marginBottom:16}}>
                  <div style={{color:'#EF4444',fontWeight:700,fontSize:11,marginBottom:6}}>⚠ Hard Block Conditions Active</div>
                  {hb_grid_emergency&&<div style={{color:'#FCA5A5',fontSize:11,marginBottom:3}}>• Grid emergency — autonomous execution suspended</div>}
                  {hb_extreme_spot  &&<div style={{color:'#FCA5A5',fontSize:11}}>• Extreme weather + spot delivery — price signal integrity compromised</div>}
                </div>
              )}

              <button onClick={runEval} disabled={isRunning} style={{width:'100%',padding:'13px 20px',borderRadius:10,border:'none',background:isRunning?'#1E293B':`linear-gradient(135deg,#7C2D12,${ENR_ORANGE})`,color:isRunning?'#374151':'#FFF',fontWeight:700,fontSize:14,cursor:isRunning?'not-allowed':'pointer',display:'flex',alignItems:'center',justifyContent:'center',gap:8}}>
                <Zap size={15}/>{isRunning?'Evaluating Trade…':'Run 11-Checkpoint Energy Governance'}{!isRunning&&<ArrowRight size={15}/>}
              </button>
            </div>

            <div style={{background:'rgba(18,7,0,0.95)',borderRadius:12,padding:16,border:'1px solid #2A1200',fontSize:12}}>
              <div style={{color:'#4B2200',fontWeight:700,marginBottom:10,fontSize:10,textTransform:'uppercase',letterSpacing:'0.06em'}}>Current Trade</div>
              {[[`Source`,`${src.emoji} ${src.label}`],[`Contract`,`${trade.contractSize} ${src.unit} (~$${(trade.contractSize*src.avgPrice/1000).toFixed(0)}K)`],[`Delivery`,del_.label],[`Grid`,grid.label.split('(')[0].trim()],[`Weather`,wx.label.split('(')[0].trim()]].map(([k,v])=>(
                <div key={k as string} style={{display:'flex',justifyContent:'space-between',marginBottom:5,paddingBottom:5,borderBottom:'1px solid #120700'}}>
                  <span style={{color:'#2A1200'}}>{k}</span><span style={{color:'#7A3B00',fontWeight:600,textAlign:'right',maxWidth:200}}>{v}</span>
                </div>
              ))}
            </div>
          </div>

          <div>
            {checkpoints.length===0?(
              <div style={{background:'rgba(18,7,0,0.95)',borderRadius:14,padding:52,border:`1px solid ${ENR_BORDER}`,textAlign:'center'}}>
                <div style={{fontSize:52,marginBottom:18}}>⚡</div>
                <div style={{fontSize:18,fontWeight:700,color:ENR_LIGHT,marginBottom:10}}>Energy Trading Governance Pipeline</div>
                <div style={{color:'#4B2200',fontSize:13,maxWidth:460,margin:'0 auto',lineHeight:1.7}}>Configure an energy trade on the left — source, contract size, delivery window, grid condition, weather outlook, and regulatory environment. Run the 11-checkpoint FERC / EU ETS governance pipeline. Every executed trade generates a PQC-signed <span style={{color:ENR_LIGHT,fontFamily:'monospace'}}>OMNIX-ENR</span> receipt.</div>
                <div style={{marginTop:28,display:'flex',justifyContent:'center',gap:10,flexWrap:'wrap'}}>
                  {['Price Forecast','Grid Exposure','Supply-Demand Coherence','Cat Stress Test','PQC Receipt'].map(s=>(
                    <span key={s} style={{background:`${ENR_ORANGE}12`,border:`1px solid ${ENR_BORDER}`,borderRadius:6,padding:'5px 12px',fontSize:11,color:ENR_LIGHT,fontWeight:500}}>{s}</span>
                  ))}
                </div>
                <div style={{marginTop:28,display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:10,maxWidth:480,margin:'28px auto 0'}}>
                  {[{icon:<Zap size={14}/>,label:'Sub-second evaluation'},{icon:<Shield size={14}/>,label:'2 hard block conditions'},{icon:<Lock size={14}/>,label:'Dilithium-3 PQC receipt'}].map((item,i)=>(
                    <div key={i} style={{background:'#120700',border:'1px solid #2A1200',borderRadius:8,padding:'12px 10px',display:'flex',flexDirection:'column',alignItems:'center',gap:6}}>
                      <div style={{color:ENR_ORANGE}}>{item.icon}</div><div style={{fontSize:10,color:'#4B2200',textAlign:'center'}}>{item.label}</div>
                    </div>
                  ))}
                </div>
              </div>
            ):(
              <div>
                {finalResult&&(
                  <div style={{borderRadius:12,padding:'16px 20px',marginBottom:14,background:vBg(finalResult),border:`1px solid ${vBdr(finalResult)}`,display:'flex',justifyContent:'space-between',alignItems:'center',flexWrap:'wrap',gap:12}}>
                    <div style={{display:'flex',alignItems:'center',gap:12}}>
                      {finalResult==='EXECUTE'?<CheckCircle size={22} style={{color:'#10B981'}}/>:finalResult==='HOLD'?<AlertTriangle size={22} style={{color:'#F59E0B'}}/>:<XCircle size={22} style={{color:'#EF4444'}}/>}
                      <div>
                        <div style={{fontWeight:800,fontSize:17,color:vColor(finalResult)}}>{finalResult==='EXECUTE'?'TRADE AUTHORIZED — EXECUTE':finalResult==='HOLD'?'HOLD — SENIOR TRADER REVIEW':'BLOCKED — GOVERNANCE THRESHOLD BREACH'}</div>
                        {receiptId&&<div style={{fontSize:11,color:'#10B981',fontFamily:'monospace',marginTop:3}}>Receipt: {receiptId} · Dilithium-3 · ADR-ENR-001</div>}
                        {!receiptId&&<div style={{fontSize:11,color:'#EF4444',marginTop:3}}>No receipt — trade blocked by energy governance pipeline</div>}
                      </div>
                    </div>
                    <div style={{textAlign:'right',fontSize:11,color:'#4B2200'}}>
                      <div>{src.emoji} {src.label}</div>
                      <div>{trade.contractSize} {src.unit} · {del_.label}</div>
                    </div>
                  </div>
                )}
                <div style={{display:'flex',flexDirection:'column',gap:9}}>
                  {checkpoints.map((cp,i)=>{
                    const isActive=currentCp===i
                    const bdrC=cp.status==='evaluating'?ENR_ORANGE:cp.status==='pass'?'#10B981':cp.status==='warn'?'#F59E0B':cp.status==='block'?'#EF4444':'#2A1200'
                    const barC=cp.status==='pass'?'#10B981':cp.status==='warn'?'#F59E0B':cp.status==='block'?'#EF4444':ENR_ORANGE
                    return (
                      <div key={i} style={{background:isActive?`${ENR_ORANGE}08`:'rgba(18,7,0,0.92)',borderRadius:10,padding:'13px 15px',border:`1px solid ${bdrC}44`,transition:'all 0.3s'}}>
                        <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:8}}>
                          <div style={{display:'flex',alignItems:'center',gap:8,flex:1}}>
                            {sIcon(cp.status)}
                            <div><div style={{fontSize:13,fontWeight:700,color:'#E2E8F0'}}>{cp.name}</div><div style={{fontSize:10,color:'#4B2200'}}>{cp.genericName}</div></div>
                          </div>
                          <div style={{textAlign:'right',flexShrink:0,marginLeft:12}}>
                            <div style={{fontSize:20,fontWeight:800,color:sColor(cp.status),lineHeight:1}}>{cp.score}</div>
                            <div style={{fontSize:10,color:'#2A1200'}}>min {cp.threshold}</div>
                          </div>
                        </div>
                        <ScoreBar score={cp.score} threshold={cp.threshold} color={barC}/>
                        {cp.status!=='pending'&&(
                          <div style={{marginTop:10}}>
                            <div style={{fontSize:12,color:'#94A3B8',lineHeight:1.55,marginBottom:6}}>{cp.reasoning}</div>
                            <div style={{fontSize:10,color:'#4B2200',fontFamily:'monospace',background:'#120700',padding:'6px 10px',borderRadius:5}}>{cp.detail}</div>
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

        <div style={{marginTop:28,textAlign:'center',color:'#2A1200',fontSize:11}}>
          OMNIX Quantum · Energy Trading Governance · ADR-ENR-001 · 11-Checkpoint Fail-Closed Pipeline
          &nbsp;·&nbsp; FERC Compliant · EU ETS / IRA · Grid Risk · Dilithium-3 PQC
          &nbsp;·&nbsp; <Link to="/try" style={{color:ENR_ORANGE,textDecoration:'none'}}>Public Sandbox →</Link>
          &nbsp;·&nbsp; <Link to="/" style={{color:ENR_ORANGE,textDecoration:'none'}}>Back to Platform →</Link>
        </div>
      </div>
    </div>
  )
}
