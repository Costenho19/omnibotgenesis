import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

// ── Design tokens ──────────────────────────────────────────────────────────────
const C = {
  navy:        '#060F1E',
  navy2:       '#0A1628',
  navy3:       '#0D1E38',
  gold:        '#C9A227',
  goldDim:     'rgba(201,162,39,0.10)',
  goldBorder:  'rgba(201,162,39,0.22)',
  green:       '#22c55e',
  greenDim:    'rgba(34,197,94,0.07)',
  greenBorder: 'rgba(34,197,94,0.22)',
  amber:       '#f59e0b',
  amberDim:    'rgba(245,158,11,0.08)',
  amberBorder: 'rgba(245,158,11,0.25)',
  red:         '#ef4444',
  redDim:      'rgba(239,68,68,0.07)',
  redBorder:   'rgba(239,68,68,0.28)',
  blue:        '#3b82f6',
  blueDim:     'rgba(59,130,246,0.07)',
  blueBorder:  'rgba(59,130,246,0.22)',
  text:        '#e2e8f0',
  muted:       '#94a3b8',
  subtle:      '#64748b',
  white:       '#ffffff',
}

const CSS = `
  @keyframes pulse-green {
    0%,100% { opacity:1; }
    50% { opacity:0.5; }
  }
  @keyframes count-up {
    from { opacity:0; transform:translateY(6px); }
    to   { opacity:1; transform:translateY(0); }
  }
  @keyframes fade-in {
    from { opacity:0; transform:translateY(12px); }
    to   { opacity:1; transform:translateY(0); }
  }
  .ev-card {
    background: ${C.navy2};
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 24px;
    transition: border-color 0.2s, transform 0.2s;
  }
  .ev-card:hover {
    border-color: rgba(201,162,39,0.18);
    transform: translateY(-1px);
  }
  .ev-metric-card {
    background: ${C.navy2};
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 20px 24px;
    animation: count-up 0.4s ease both;
  }
  .ev-action-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 20px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    border: none;
    letter-spacing: 0.02em;
  }
  .ev-action-btn:hover { transform: translateY(-1px); filter: brightness(1.1); }
  .ev-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }
  .section-fade {
    animation: fade-in 0.5s ease both;
  }
  .live-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: ${C.green};
    animation: pulse-green 2s ease-in-out infinite;
  }
`

// ── Demo data (illustrative — real data via API key integration) ───────────────
const DEMO = {
  health:           98,
  decisions_today:  247,
  active_agents:    12,
  vetoed_today:     3,
  compliance_score: 99.2,
  risk_level:       'LOW' as 'LOW' | 'MEDIUM' | 'HIGH',
  uptime:           '99.97%',
  receipts_total:   104_832,
  last_veto_reason: 'Risk exposure exceeded threshold in real-estate valuation agent',
  last_veto_time:   '14:23 UTC',
  verticals_active: 10,
  narrative: [
    { time: '09:02', event: 'Credit scoring agent started a new governance session.' },
    { time: '11:15', event: '84 loan decisions reviewed. All approved within policy bounds.' },
    { time: '12:47', event: 'Medical AI agent flagged for elevated drift — monitoring escalated.' },
    { time: '14:23', event: 'Real estate valuation agent vetoed. Risk threshold exceeded. Agent paused automatically.' },
    { time: '16:05', event: 'All 12 active agents operating within defined authority limits.' },
  ],
  alerts: [
    { level: 'WATCH', text: 'Medical AI agent: behavioral drift at 31% — approaching 35% threshold.' },
  ],
  frameworks: ['EU AI Act', 'SAMA', 'CBUAE', 'Basel III', 'HIPAA', 'OHADA', 'SYSCOHADA'],
}

function HealthRing({ score }: { score: number }) {
  const r = 52
  const circ = 2 * Math.PI * r
  const pct = circ - (score / 100) * circ
  const color = score >= 95 ? C.green : score >= 80 ? C.amber : C.red

  return (
    <div style={{ position:'relative', width:128, height:128, flexShrink:0 }}>
      <svg width={128} height={128} style={{ transform:'rotate(-90deg)' }}>
        <circle cx={64} cy={64} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={10} />
        <circle
          cx={64} cy={64} r={r}
          fill="none"
          stroke={color}
          strokeWidth={10}
          strokeDasharray={circ}
          strokeDashoffset={pct}
          strokeLinecap="round"
          style={{ transition:'stroke-dashoffset 1s ease', filter:`drop-shadow(0 0 6px ${color})` }}
        />
      </svg>
      <div style={{
        position:'absolute', inset:0,
        display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center',
      }}>
        <span style={{ fontSize:26, fontWeight:800, color, lineHeight:1 }}>{score}%</span>
        <span style={{ fontSize:10, color:C.muted, letterSpacing:'0.08em', marginTop:2 }}>HEALTH</span>
      </div>
    </div>
  )
}

function MetricCard({
  label, value, sub, color, delay = 0
}: { label:string; value:string|number; sub?:string; color:string; delay?:number }) {
  return (
    <div className="ev-metric-card" style={{ animationDelay:`${delay}ms` }}>
      <div style={{ fontSize:11, color:C.subtle, letterSpacing:'0.08em', textTransform:'uppercase', marginBottom:8 }}>
        {label}
      </div>
      <div style={{ fontSize:32, fontWeight:800, color, lineHeight:1, marginBottom:4 }}>
        {typeof value === 'number' ? value.toLocaleString() : value}
      </div>
      {sub && <div style={{ fontSize:12, color:C.muted }}>{sub}</div>}
    </div>
  )
}

function RiskBadge({ level }: { level: 'LOW'|'MEDIUM'|'HIGH' }) {
  const map = {
    LOW:    { bg: C.greenDim, border: C.greenBorder, color: C.green,   label: '● LOW RISK' },
    MEDIUM: { bg: C.amberDim, border: C.amberBorder, color: C.amber,   label: '● MEDIUM RISK' },
    HIGH:   { bg: C.redDim,   border: C.redBorder,   color: C.red,     label: '● HIGH RISK' },
  }
  const s = map[level]
  return (
    <span className="ev-badge" style={{ background:s.bg, border:`1px solid ${s.border}`, color:s.color }}>
      {s.label}
    </span>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────────
export default function ExecutiveViewPage() {
  const [time, setTime] = useState(new Date())
  const [expanded, setExpanded] = useState<string|null>(null)

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(t)
  }, [])

  const timeStr = time.toLocaleTimeString('en-GB', { hour:'2-digit', minute:'2-digit', second:'2-digit', timeZone:'UTC' }) + ' UTC'

  return (
    <div style={{ minHeight:'100vh', background:C.navy, color:C.text, fontFamily:"'Inter',system-ui,sans-serif" }}>
      <style>{CSS}</style>

      {/* ── Top bar ── */}
      <div style={{
        borderBottom:`1px solid rgba(255,255,255,0.06)`,
        background:C.navy2,
        padding:'0 32px',
        display:'flex', alignItems:'center', justifyContent:'space-between',
        height:56, position:'sticky', top:0, zIndex:50,
      }}>
        <div style={{ display:'flex', alignItems:'center', gap:16 }}>
          <Link to="/" style={{ textDecoration:'none' }}>
            <span style={{ fontWeight:800, fontSize:15, color:C.gold, letterSpacing:'0.06em' }}>OMNIX</span>
            <span style={{ fontWeight:400, fontSize:13, color:C.muted, marginLeft:8 }}>Executive View</span>
          </Link>
          <div style={{ display:'flex', alignItems:'center', gap:6 }}>
            <div className="live-dot" />
            <span style={{ fontSize:11, color:C.green, fontWeight:600, letterSpacing:'0.06em' }}>LIVE</span>
          </div>
        </div>
        <div style={{ display:'flex', alignItems:'center', gap:20 }}>
          <span style={{ fontSize:12, color:C.subtle, fontFamily:'monospace' }}>{timeStr}</span>
          <RiskBadge level={DEMO.risk_level} />
        </div>
      </div>

      <div style={{ maxWidth:1200, margin:'0 auto', padding:'40px 24px' }}>

        {/* ── Hero: Health + Summary ── */}
        <div className="section-fade" style={{
          display:'flex', alignItems:'center', gap:40, flexWrap:'wrap',
          background:C.navy2, border:`1px solid ${C.goldBorder}`,
          borderRadius:16, padding:'32px 40px', marginBottom:32,
        }}>
          <HealthRing score={DEMO.health} />
          <div style={{ flex:1, minWidth:240 }}>
            <div style={{ fontSize:11, color:C.gold, letterSpacing:'0.10em', textTransform:'uppercase', marginBottom:8 }}>
              Governance Status
            </div>
            <div style={{ fontSize:28, fontWeight:800, color:C.white, marginBottom:8, lineHeight:1.2 }}>
              Your AI is operating within policy.
            </div>
            <div style={{ fontSize:14, color:C.muted, lineHeight:1.6, maxWidth:480 }}>
              {DEMO.active_agents} agents active across {DEMO.verticals_active} business verticals.{' '}
              Every decision is cryptographically signed and independently verifiable.
              {DEMO.vetoed_today > 0 && ` ${DEMO.vetoed_today} actions were stopped automatically today before reaching execution.`}
            </div>
          </div>
          <div style={{ display:'flex', flexDirection:'column', gap:8, alignItems:'flex-end' }}>
            <Link to="/try">
              <button className="ev-action-btn" style={{ background:C.gold, color:C.navy }}>
                ▶ Run Governance Test
              </button>
            </Link>
            <Link to="/proof-of-governance">
              <button className="ev-action-btn" style={{ background:C.goldDim, color:C.gold, border:`1px solid ${C.goldBorder}` }}>
                Get Your Certificate
              </button>
            </Link>
          </div>
        </div>

        {/* ── Metric grid ── */}
        <div style={{
          display:'grid',
          gridTemplateColumns:'repeat(auto-fit, minmax(160px,1fr))',
          gap:16, marginBottom:32,
        }}>
          <MetricCard label="Decisions Today"  value={DEMO.decisions_today} sub="All evaluated in real time"    color={C.gold}  delay={0}   />
          <MetricCard label="Active Agents"    value={DEMO.active_agents}   sub="Across 10 verticals"           color={C.blue}  delay={60}  />
          <MetricCard label="Stopped Today"    value={DEMO.vetoed_today}    sub="Before reaching execution"     color={C.amber} delay={120} />
          <MetricCard label="Compliance Score" value={`${DEMO.compliance_score}%`} sub="Policy conformance rate" color={C.green} delay={180} />
          <MetricCard label="System Uptime"    value={DEMO.uptime}          sub="Last 30 days"                  color={C.green} delay={240} />
          <MetricCard label="Total Receipts"   value={DEMO.receipts_total}  sub="Issued & verifiable offline"   color={C.muted} delay={300} />
        </div>

        {/* ── Two column: Activity + Alerts ── */}
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:24, marginBottom:32 }}>

          {/* Activity timeline */}
          <div className="ev-card section-fade">
            <div style={{ fontSize:11, color:C.subtle, letterSpacing:'0.08em', textTransform:'uppercase', marginBottom:20 }}>
              What Happened Today
            </div>
            <div style={{ display:'flex', flexDirection:'column', gap:0 }}>
              {DEMO.narrative.map((n, i) => (
                <div key={i} style={{
                  display:'flex', gap:16, paddingBottom:16,
                  borderLeft:`2px solid rgba(255,255,255,0.06)`,
                  marginLeft:8, paddingLeft:20, position:'relative',
                }}>
                  <div style={{
                    position:'absolute', left:-5, top:4,
                    width:8, height:8, borderRadius:'50%',
                    background: i === DEMO.narrative.length-1 ? C.green : 'rgba(255,255,255,0.15)',
                  }} />
                  <span style={{ fontSize:11, color:C.subtle, fontFamily:'monospace', flexShrink:0, paddingTop:2 }}>
                    {n.time}
                  </span>
                  <span style={{ fontSize:13, color:C.muted, lineHeight:1.5 }}>{n.event}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Alerts + frameworks */}
          <div style={{ display:'flex', flexDirection:'column', gap:16 }}>

            {/* Alerts */}
            <div className="ev-card section-fade">
              <div style={{ fontSize:11, color:C.subtle, letterSpacing:'0.08em', textTransform:'uppercase', marginBottom:16 }}>
                Requires Your Attention
              </div>
              {DEMO.alerts.length === 0 ? (
                <div style={{ display:'flex', alignItems:'center', gap:10 }}>
                  <span style={{ fontSize:18 }}>✓</span>
                  <span style={{ fontSize:13, color:C.green }}>Nothing requires your attention right now.</span>
                </div>
              ) : (
                DEMO.alerts.map((a, i) => (
                  <div key={i} style={{
                    background: C.amberDim, border:`1px solid ${C.amberBorder}`,
                    borderRadius:8, padding:'12px 16px', marginBottom:8,
                  }}>
                    <span className="ev-badge" style={{
                      background:'transparent', border:'none',
                      color:C.amber, padding:0, marginBottom:6, display:'block',
                    }}>
                      {a.level}
                    </span>
                    <div style={{ fontSize:13, color:C.text, lineHeight:1.5 }}>{a.text}</div>
                  </div>
                ))
              )}
            </div>

            {/* Last veto */}
            <div className="ev-card section-fade" style={{ borderColor:C.amberBorder }}>
              <div style={{ fontSize:11, color:C.subtle, letterSpacing:'0.08em', textTransform:'uppercase', marginBottom:12 }}>
                Last Automatic Stop
              </div>
              <div style={{ fontSize:13, color:C.text, lineHeight:1.5, marginBottom:8 }}>
                {DEMO.last_veto_reason}
              </div>
              <div style={{ fontSize:11, color:C.subtle }}>{DEMO.last_veto_time}</div>
            </div>

            {/* Regulatory coverage */}
            <div className="ev-card section-fade">
              <div style={{ fontSize:11, color:C.subtle, letterSpacing:'0.08em', textTransform:'uppercase', marginBottom:14 }}>
                Regulatory Coverage Active
              </div>
              <div style={{ display:'flex', flexWrap:'wrap', gap:6 }}>
                {DEMO.frameworks.map(f => (
                  <span key={f} className="ev-badge" style={{
                    background:C.blueDim, border:`1px solid ${C.blueBorder}`,
                    color:C.blue,
                  }}>{f}</span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* ── Proof of Governance strip ── */}
        <div className="section-fade" style={{
          background: `linear-gradient(135deg, rgba(201,162,39,0.08) 0%, rgba(59,130,246,0.05) 100%)`,
          border:`1px solid ${C.goldBorder}`,
          borderRadius:16, padding:'28px 36px',
          display:'flex', alignItems:'center', justifyContent:'space-between', flexWrap:'wrap', gap:20,
          marginBottom:32,
        }}>
          <div>
            <div style={{ fontSize:11, color:C.gold, letterSpacing:'0.10em', textTransform:'uppercase', marginBottom:8 }}>
              Proof of Governance Certificate (PoGC)
            </div>
            <div style={{ fontSize:18, fontWeight:700, color:C.white, marginBottom:6 }}>
              The SSL for AI decisions.
            </div>
            <div style={{ fontSize:13, color:C.muted, maxWidth:480, lineHeight:1.6 }}>
              A cryptographically signed, machine-readable record proving your AI governance
              was active at execution time. Verifiable offline. Independent of OMNIX.
            </div>
          </div>
          <div style={{ display:'flex', flexDirection:'column', gap:10, alignItems:'flex-end' }}>
            <Link to="/proof-of-governance">
              <button className="ev-action-btn" style={{ background:C.gold, color:C.navy, padding:'12px 28px', fontSize:14 }}>
                Request Your Certificate →
              </button>
            </Link>
            <span style={{ fontSize:11, color:C.subtle }}>First certificates in the world now issuing</span>
          </div>
        </div>

        {/* ── FAQ toggles ── */}
        <div className="section-fade" style={{ marginBottom:40 }}>
          <div style={{ fontSize:11, color:C.subtle, letterSpacing:'0.08em', textTransform:'uppercase', marginBottom:20 }}>
            Common Questions
          </div>
          {[
            {
              q: 'What does OMNIX actually do?',
              a: 'OMNIX sits between your AI agents and execution. Before any agent takes a consequential action — approving a loan, making a trade, changing a patient record — OMNIX evaluates it against your defined policy and either approves or vetoes it. Every decision gets a cryptographically signed receipt, verifiable without OMNIX.'
            },
            {
              q: 'What happens when an agent is stopped?',
              a: 'The agent receives a HALT verdict and cannot proceed. The action is logged with the reason, the timestamp, and a signed record. Your team is notified. No action reaches execution without governance approval.'
            },
            {
              q: 'Who can verify the governance records?',
              a: 'Anyone, without contacting OMNIX. Every receipt can be verified offline using the public key published at omnixquantum.net. Regulators, auditors, and counterparties can check independently.'
            },
            {
              q: 'What is a Proof of Governance Certificate?',
              a: 'A PoGC is a signed artifact proving that a specific AI system operated under active governance during a defined period. Think of it as an SSL certificate for AI decisions — it can be presented to regulators, clients, or board members as evidence of compliant AI operation.'
            },
          ].map(({ q, a }) => (
            <div key={q} style={{ borderBottom:`1px solid rgba(255,255,255,0.06)` }}>
              <button
                onClick={() => setExpanded(expanded === q ? null : q)}
                style={{
                  width:'100%', background:'none', border:'none', cursor:'pointer',
                  padding:'16px 0', display:'flex', justifyContent:'space-between', alignItems:'center',
                  color:C.text, fontSize:14, fontWeight:600, textAlign:'left',
                }}
              >
                {q}
                <span style={{ color:C.subtle, fontSize:18, flexShrink:0 }}>{expanded === q ? '−' : '+'}</span>
              </button>
              {expanded === q && (
                <div style={{
                  fontSize:13, color:C.muted, lineHeight:1.7, paddingBottom:16, maxWidth:680,
                  animation:'fade-in 0.2s ease both',
                }}>
                  {a}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* ── Footer CTA ── */}
        <div style={{
          textAlign:'center', paddingTop:24,
          borderTop:`1px solid rgba(255,255,255,0.06)`,
        }}>
          <div style={{ fontSize:13, color:C.subtle, marginBottom:16 }}>
            Ready to integrate governance into your AI system?
          </div>
          <div style={{ display:'flex', gap:12, justifyContent:'center', flexWrap:'wrap' }}>
            <Link to="/try">
              <button className="ev-action-btn" style={{ background:C.gold, color:C.navy, padding:'12px 28px' }}>
                Try the Protocol
              </button>
            </Link>
            <Link to="/docs">
              <button className="ev-action-btn" style={{
                background:'transparent', color:C.gold,
                border:`1px solid ${C.goldBorder}`, padding:'12px 28px',
              }}>
                Integration Docs
              </button>
            </Link>
          </div>
          <div style={{ fontSize:11, color:C.subtle, marginTop:24 }}>
            OMNIX QUANTUM LTD · London, UK · omnixquantum.net
          </div>
        </div>
      </div>
    </div>
  )
}
