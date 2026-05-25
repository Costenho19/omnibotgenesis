import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

// ── Design tokens ──────────────────────────────────────────────────────────────
const C = {
  navy:         '#060F1E',
  navy2:        '#0A1628',
  navy3:        '#0D1E38',
  navy4:        '#111f36',
  gold:         '#C9A227',
  goldDim:      'rgba(201,162,39,0.10)',
  goldBorder:   'rgba(201,162,39,0.22)',
  goldGlow:     'rgba(201,162,39,0.08)',
  blue:         '#3b82f6',
  blueDim:      'rgba(59,130,246,0.08)',
  blueBorder:   'rgba(59,130,246,0.28)',
  green:        '#22c55e',
  greenDim:     'rgba(34,197,94,0.07)',
  greenBorder:  'rgba(34,197,94,0.25)',
  amber:        '#f59e0b',
  amberDim:     'rgba(245,158,11,0.08)',
  amberBorder:  'rgba(245,158,11,0.28)',
  red:          '#ef4444',
  redDim:       'rgba(239,68,68,0.09)',
  redBorder:    'rgba(239,68,68,0.32)',
  redGlow:      'rgba(239,68,68,0.12)',
  text:         '#e2e8f0',
  muted:        '#94a3b8',
  subtle:       '#64748b',
  dim:          '#334155',
  white:        '#ffffff',
}

// ── CSS Keyframes ──────────────────────────────────────────────────────────────
const CSS = `
  @keyframes halt-pulse {
    0%,100% { box-shadow: 0 0 0 1px rgba(239,68,68,0.32), 0 0 40px rgba(239,68,68,0.12); }
    50%      { box-shadow: 0 0 0 1px rgba(239,68,68,0.55), 0 0 60px rgba(239,68,68,0.20); }
  }
  @keyframes stream-down {
    0%   { transform: translateY(-100%); opacity: 0; }
    30%  { opacity: 1; }
    70%  { opacity: 1; }
    100% { transform: translateY(100%); opacity: 0; }
  }
  @keyframes fade-up {
    from { opacity:0; transform:translateY(20px); }
    to   { opacity:1; transform:translateY(0); }
  }
  @keyframes ces-bar {
    from { width: 0%; }
    to   { width: var(--ces-pct); }
  }
  @keyframes scan-line {
    0%   { top: 0%; opacity: 0; }
    5%   { opacity: 0.4; }
    95%  { opacity: 0.4; }
    100% { top: 100%; opacity: 0; }
  }
  @keyframes dot-fade {
    0%,100% { opacity: 0.15; }
    50%      { opacity: 0.40; }
  }
`

// ── Utilities ──────────────────────────────────────────────────────────────────
function Tag({ label, color, bg, border }: { label: string; color: string; bg: string; border: string }) {
  return (
    <span style={{
      fontFamily: 'monospace', fontSize: 9, color,
      background: bg, border: `1px solid ${border}`,
      padding: '2px 7px', borderRadius: 2, letterSpacing: '0.07em',
      whiteSpace: 'nowrap',
    }}>
      {label}
    </span>
  )
}

// ── Animated connector ─────────────────────────────────────────────────────────
function Connector({ topColor, bottomColor, label }: { topColor: string; bottomColor: string; label?: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', position: 'relative', zIndex: 2, margin: '0 auto', width: '100%' }}>
      {label && (
        <div style={{
          position: 'absolute', left: '50%', top: '50%',
          transform: 'translateX(40px) translateY(-50%)',
          fontFamily: 'monospace', fontSize: 9, color: bottomColor,
          letterSpacing: '0.12em', opacity: 0.70, whiteSpace: 'nowrap',
        }}>
          ▼ {label}
        </div>
      )}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 2, position: 'relative' }}>
        {/* Connector body */}
        <div style={{ width: 1, height: 28, background: `linear-gradient(to bottom, ${topColor}40, ${bottomColor}40)`, position: 'relative', overflow: 'hidden' }}>
          <div style={{ position: 'absolute', width: '100%', height: '40%', background: `linear-gradient(to bottom, transparent, ${bottomColor}80, transparent)`, animation: 'stream-down 2.5s ease-in-out infinite' }} />
        </div>
        <div style={{ width: 5, height: 5, borderRadius: '50%', background: bottomColor, boxShadow: `0 0 8px ${bottomColor}`, flexShrink: 0 }} />
        <div style={{ width: 1, height: 28, background: `linear-gradient(to bottom, ${bottomColor}40, transparent)` }} />
      </div>
    </div>
  )
}

// ── CES bar visual ─────────────────────────────────────────────────────────────
function CESBar({ score, label, status }: { score: number; label: string; status: string }) {
  const color = score >= 75 ? C.green : score >= 50 ? C.amber : score >= 25 ? C.red : '#7f1d1d'
  const pct = `${score}%`
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontFamily: 'monospace', fontSize: 10, color: C.subtle }}>{label}</span>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ fontFamily: 'monospace', fontSize: 10, color }}>{score.toFixed(2)}</span>
          <span style={{ fontFamily: 'monospace', fontSize: 9, color, background: `${color}15`, border: `1px solid ${color}40`, padding: '1px 6px', borderRadius: 2 }}>{status}</span>
        </div>
      </div>
      <div style={{ height: 3, background: C.navy2, borderRadius: 2, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: pct, background: `linear-gradient(to right, ${color}60, ${color})`, borderRadius: 2, transition: 'width 1s ease' } as React.CSSProperties} />
      </div>
    </div>
  )
}

// ── DataCard ───────────────────────────────────────────────────────────────────
function DataCard({ label, value, mono: isMono = true }: { label: string; value: string; mono?: boolean }) {
  return (
    <div style={{ background: C.navy2, border: `1px solid ${C.dim}30`, borderRadius: 3, padding: '8px 12px' }}>
      <div style={{ fontFamily: 'monospace', fontSize: 9, color: C.subtle, letterSpacing: '0.09em', marginBottom: 3 }}>{label.toUpperCase()}</div>
      <div style={{ fontFamily: isMono ? 'monospace' : 'inherit', fontSize: 11, color: C.text, lineHeight: 1.4 }}>{value}</div>
    </div>
  )
}

// ── Node Section ───────────────────────────────────────────────────────────────
interface NodeProps { visible: boolean }

function NodeHumanAuthority({ visible }: NodeProps) {
  return (
    <div style={{ animation: visible ? 'fade-up 0.55s ease both' : 'none', opacity: visible ? 1 : 0 }}>
      <div style={{ border: `1px solid ${C.goldBorder}`, borderRadius: 5, background: C.navy3, overflow: 'hidden', position: 'relative' }}>
        {/* Left accent bar */}
        <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 3, background: `linear-gradient(to bottom, ${C.gold}, ${C.gold}60)` }} />
        <div style={{ padding: '22px 26px 22px 30px' }}>
          {/* Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                <div style={{ fontFamily: 'monospace', fontSize: 9, color: C.gold, letterSpacing: '0.14em' }}>L1 · IDENTITY LAYER</div>
                <div style={{ width: 20, height: 1, background: `${C.gold}40` }} />
                <div style={{ fontFamily: 'monospace', fontSize: 9, color: C.subtle }}>ADR-156</div>
              </div>
              <h3 style={{ margin: 0, fontSize: 18, fontWeight: 600, color: C.white, letterSpacing: '-0.01em' }}>Human Authority</h3>
              <div style={{ fontSize: 12, color: C.muted, marginTop: 3 }}>Delegation Receipt Issuance · ML-DSA-65</div>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, justifyContent: 'flex-end', maxWidth: 220 }}>
              {['ATF-INV-001','ATF-INV-002','ATF-INV-003','ATF-INV-006'].map(t => (
                <Tag key={t} label={t} color={C.gold} bg={C.goldDim} border={C.goldBorder} />
              ))}
            </div>
          </div>
          {/* Data grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 7, marginBottom: 14 }}>
            <DataCard label="delegation_id" value="ATFDR-7F3A9B2C1E4D8F6A" />
            <DataCard label="Signature algorithm" value="ML-DSA-65 (FIPS 204 · NIST Level 3)" />
            <DataCard label="Authority budget rule" value="granted (72.00) ≤ delegator (85.00) ✓" />
            <DataCard label="PQC key size" value="Public: 1312 bytes · Signature: 3293 bytes" />
            <DataCard label="content_hash" value="SHA-256 over canonical JSON — sort_keys=True" />
            <DataCard label="chain_root_id" value="ATFDR-7F3A9B2C1E4D8F6A → human origin" />
          </div>
          {/* Principle */}
          <div style={{ borderTop: `1px solid ${C.dim}40`, paddingTop: 12, display: 'flex', gap: 10, alignItems: 'flex-start' }}>
            <div style={{ width: 3, height: 3, borderRadius: '50%', background: C.gold, marginTop: 5, flexShrink: 0 }} />
            <p style={{ margin: 0, fontSize: 12, color: C.muted, fontStyle: 'italic', lineHeight: 1.55 }}>
              Every downstream decision traces back to this PQC-signed root. No chain — no execution. Attempting to grant more authority than the delegator holds raises <span style={{ fontFamily: 'monospace', color: C.red, fontSize: 11 }}>AuthorityExpansionViolation</span> — no signature is issued.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

function NodeRuntimeGovernance({ visible }: NodeProps) {
  const [played, setPlayed] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!visible || played) return
    const t = setTimeout(() => setPlayed(true), 400)
    return () => clearTimeout(t)
  }, [visible, played])

  return (
    <div style={{ animation: visible ? 'fade-up 0.55s 0.05s ease both' : 'none', opacity: visible ? 1 : 0 }}>
      <div style={{ border: `1px solid ${C.blueBorder}`, borderRadius: 5, background: C.navy3, overflow: 'hidden', position: 'relative' }}>
        <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 3, background: `linear-gradient(to bottom, ${C.blue}, ${C.blue}60)` }} />
        <div style={{ padding: '22px 26px 22px 30px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                <div style={{ fontFamily: 'monospace', fontSize: 9, color: C.blue, letterSpacing: '0.14em' }}>L2 · MONITORING LAYER</div>
                <div style={{ width: 20, height: 1, background: `${C.blue}40` }} />
                <div style={{ fontFamily: 'monospace', fontSize: 9, color: C.subtle }}>ADR-159</div>
              </div>
              <h3 style={{ margin: 0, fontSize: 18, fontWeight: 600, color: C.white, letterSpacing: '-0.01em' }}>Runtime Governance</h3>
              <div style={{ fontSize: 12, color: C.muted, marginTop: 3 }}>11 Continuity Checkpoints · RCR write-once</div>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, justifyContent: 'flex-end', maxWidth: 220 }}>
              {['RGC-INV-001','RGC-INV-002','RGC-INV-006','RGC-INV-007'].map(t => (
                <Tag key={t} label={t} color={C.blue} bg={C.blueDim} border={C.blueBorder} />
              ))}
            </div>
          </div>

          {/* CES formula */}
          <div style={{ background: C.navy2, border: `1px solid ${C.dim}40`, borderRadius: 4, padding: '12px 14px', marginBottom: 12, fontFamily: 'monospace' }}>
            <div style={{ fontSize: 9, color: C.subtle, letterSpacing: '0.1em', marginBottom: 7 }}>CES FORMULA — RFC-ATF-2 §4</div>
            <div style={{ fontSize: 12, color: C.blue }}>CES = (T×0.30) + (B×0.30) + (D×0.20) + (I×0.20)</div>
            <div style={{ marginTop: 8, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4 }}>
              {[
                ['T — Temporal Health',   'time_remaining / DR_lifetime × 100'],
                ['B — Budget Health',     'budget_remaining / budget_at_admission × 100'],
                ['D — Context Fidelity',  '100.0 − context_drift_pct'],
                ['I — Integrity Score',   '100.0 − (active_anomalies × 10)'],
              ].map(([k, v]) => (
                <div key={k} style={{ fontSize: 10, color: C.subtle }}>
                  <span style={{ color: C.blue }}>{k}</span>
                  <span style={{ color: C.dim }}> → </span>
                  <span style={{ color: C.muted }}>{v}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Live CES progression — real values from walkthrough */}
          <div ref={ref} style={{ marginBottom: 14 }}>
            <div style={{ fontSize: 9, fontFamily: 'monospace', color: C.subtle, letterSpacing: '0.1em', marginBottom: 8 }}>OBSERVED CES TRAJECTORY — ATFDR-7F3A9B2C1E4D8F6A</div>
            <CESBar score={played ? 95.16 : 0} label="t+08min · RCR-1 · ATFRCR-9A2B4C1D7E3F8B2A" status="NOMINAL" />
            <CESBar score={played ? 83.16 : 0} label="t+22min · RCR-2 · 1 anomaly · drift 11.7%" status="NOMINAL" />
            <CESBar score={played ? 49.47 : 0} label="t+41min · RCR-3 · 7 anomalies · drift 51.2%" status="WARNING" />
            <CESBar score={played ? 8.33  : 0} label="t+HALT  · CEE issued · RC TTL expired" status="HALT" />
          </div>

          <div style={{ borderTop: `1px solid ${C.dim}40`, paddingTop: 12, display: 'flex', gap: 10, alignItems: 'flex-start' }}>
            <div style={{ width: 3, height: 3, borderRadius: '50%', background: C.blue, marginTop: 5, flexShrink: 0 }} />
            <p style={{ margin: 0, fontSize: 12, color: C.muted, fontStyle: 'italic', lineHeight: 1.55 }}>
              CES inputs must not be older than 5s in CRITICAL state (RGC-INV-007). Every RCR is write-once. Stale inputs force WARNING classification regardless of computed value.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

function NodeGovernanceEvent({ visible }: NodeProps) {
  return (
    <div style={{ animation: visible ? 'fade-up 0.55s 0.05s ease both' : 'none', opacity: visible ? 1 : 0 }}>
      <div style={{ border: `1px solid ${C.amberBorder}`, borderRadius: 5, background: C.navy3, overflow: 'hidden', position: 'relative' }}>
        <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 3, background: `linear-gradient(to bottom, ${C.amber}, ${C.amber}60)` }} />
        <div style={{ padding: '22px 26px 22px 30px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                <div style={{ fontFamily: 'monospace', fontSize: 9, color: C.amber, letterSpacing: '0.14em' }}>L3 · EVALUATION LAYER</div>
                <div style={{ width: 20, height: 1, background: `${C.amber}40` }} />
                <div style={{ fontFamily: 'monospace', fontSize: 9, color: C.subtle }}>ADR-159 · ADR-140</div>
              </div>
              <h3 style={{ margin: 0, fontSize: 18, fontWeight: 600, color: C.white, letterSpacing: '-0.01em' }}>Governance Event</h3>
              <div style={{ fontSize: 12, color: C.muted, marginTop: 3 }}>Context Drift Breach · Reauthorization Challenge · CTAG</div>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, justifyContent: 'flex-end', maxWidth: 220 }}>
              {['RGC-INV-004','RGC-INV-008','EAP-INV-005'].map(t => (
                <Tag key={t} label={t} color={C.amber} bg={C.amberDim} border={C.amberBorder} />
              ))}
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 7, marginBottom: 14 }}>
            <DataCard label="Reauthorization Challenge" value="ATFRC-8B2C4D1A9E3F7C2D" />
            <DataCard label="CES at challenge" value="49.47 → WARNING threshold crossed" />
            <DataCard label="RC issued at" value="2026-05-18T15:28:00Z" />
            <DataCard label="RC expires at" value="2026-05-18T15:33:00Z · TTL 300s" />
            <DataCard label="CTAG drift_delta" value="-0.16 (threshold: -0.15) → REVOKED" />
            <DataCard label="CTAG verdict" value="CTAG-9F3A2B1C8D4E · commit_authorized: false" />
          </div>
          <div style={{ background: C.navy2, border: `1px solid ${C.amberBorder}`, borderRadius: 4, padding: '11px 14px', marginBottom: 14, fontFamily: 'monospace', fontSize: 11 }}>
            <div style={{ fontSize: 9, color: C.amber, letterSpacing: '0.1em', marginBottom: 6 }}>CTAG COMPUTATION — commit_time_gate.py / ADR-140</div>
            <div style={{ color: C.text }}>drift_delta = current_margin (0.02) − original_margin (0.18)</div>
            <div style={{ color: C.amber, marginTop: 3 }}>−0.16 &lt; −REVOCATION_THRESHOLD (−0.15) → <span style={{ color: C.red }}>REVOKED</span></div>
          </div>
          <div style={{ borderTop: `1px solid ${C.dim}40`, paddingTop: 12, display: 'flex', gap: 10, alignItems: 'flex-start' }}>
            <div style={{ width: 3, height: 3, borderRadius: '50%', background: C.amber, marginTop: 5, flexShrink: 0 }} />
            <p style={{ margin: 0, fontSize: 12, color: C.muted, fontStyle: 'italic', lineHeight: 1.55 }}>
              The protocol does not wait for an operator to notice degradation. The challenge is issued automatically. The Tier-1 principal has exactly 300 seconds to respond with a fresh short-lifetime DR. No response — no execution.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

function NodeEnforcement({ visible }: NodeProps) {
  return (
    <div style={{ animation: visible ? 'fade-up 0.55s 0.05s ease both' : 'none', opacity: visible ? 1 : 0 }}>
      <div style={{
        border: `1px solid ${C.redBorder}`,
        borderRadius: 6,
        background: 'rgba(12,6,16,0.98)',
        overflow: 'hidden',
        position: 'relative',
        animation: 'halt-pulse 4.5s ease-in-out infinite',
      }}>
        {/* Grid texture */}
        <div style={{
          position: 'absolute', inset: 0, borderRadius: 6,
          backgroundImage: `linear-gradient(rgba(239,68,68,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(239,68,68,0.035) 1px, transparent 1px)`,
          backgroundSize: '28px 28px',
          pointerEvents: 'none',
        }} />
        {/* Top scan line */}
        <div style={{ position: 'absolute', left: 0, right: 0, height: 1, background: `linear-gradient(to right, transparent, ${C.red}50, transparent)`, animation: 'scan-line 6s ease-in-out infinite', pointerEvents: 'none' }} />
        {/* Left accent — thicker for gate */}
        <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 4, background: `linear-gradient(to bottom, ${C.red}, ${C.red}80)` }} />

        <div style={{ padding: '28px 30px 28px 36px', position: 'relative' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 18 }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                <div style={{ fontFamily: 'monospace', fontSize: 9, color: C.red, letterSpacing: '0.18em', opacity: 0.9 }}>⬡ PROTOCOL ENFORCEMENT GATE</div>
              </div>
              <h3 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: C.white, letterSpacing: '-0.02em' }}>Execution Admissibility</h3>
              <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.55)', marginTop: 4 }}>
                The protocol decides whether this execution is admitted. Not an AI. Not a dashboard. Not an operator.
              </div>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, justifyContent: 'flex-end', maxWidth: 200 }}>
              {['RGC-INV-003','RGC-INV-008','ATF-INV-001'].map(t => (
                <Tag key={t} label={t} color={C.red} bg={C.redDim} border={C.redBorder} />
              ))}
            </div>
          </div>

          {/* Three gate outcomes */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10, marginBottom: 20 }}>
            {/* HALT — the one that fired */}
            <div style={{ border: `1px solid ${C.redBorder}`, background: C.redDim, borderRadius: 4, padding: '14px 16px', position: 'relative' }}>
              <div style={{ position: 'absolute', top: 8, right: 10, fontFamily: 'monospace', fontSize: 8, color: C.red, letterSpacing: '0.1em' }}>FIRED</div>
              <div style={{ fontFamily: 'monospace', fontSize: 14, fontWeight: 700, color: C.red, marginBottom: 6 }}>HALT</div>
              <div style={{ fontSize: 10, color: C.muted, lineHeight: 1.5 }}>
                RC TTL expired at <span style={{ color: 'rgba(255,255,255,0.7)', fontFamily: 'monospace' }}>15:33:01Z</span><br/>
                All sub-tasks revoked<br/>
                COLD seal triggered
              </div>
            </div>
            <div style={{ border: `1px solid ${C.dim}50`, background: 'rgba(255,255,255,0.02)', borderRadius: 4, padding: '14px 16px', opacity: 0.5 }}>
              <div style={{ fontFamily: 'monospace', fontSize: 14, fontWeight: 700, color: C.amber, marginBottom: 6 }}>ESCALATE</div>
              <div style={{ fontSize: 10, color: C.muted, lineHeight: 1.5 }}>
                Operator notified<br/>
                Clock running<br/>
                Monitoring intensified
              </div>
            </div>
            <div style={{ border: `1px solid ${C.dim}50`, background: 'rgba(255,255,255,0.02)', borderRadius: 4, padding: '14px 16px', opacity: 0.5 }}>
              <div style={{ fontFamily: 'monospace', fontSize: 14, fontWeight: 700, color: C.green, marginBottom: 6 }}>ALLOW</div>
              <div style={{ fontSize: 10, color: C.muted, lineHeight: 1.5 }}>
                CES within bounds<br/>
                RC resolved<br/>
                Execution continues
              </div>
            </div>
          </div>

          {/* HALT event data */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 7, marginBottom: 16 }}>
            <DataCard label="CEE escalation id" value="ATFCEE-2D4F8A1B9C3E7D4A" />
            <DataCard label="CES at escalation" value="8.33 — AUTO_HALT_TTL_EXPIRED" />
            <DataCard label="HALT timestamp" value="2026-05-18T15:33:01Z" />
            <DataCard label="Response TTL remaining" value="0 seconds — no override possible" />
          </div>

          {/* HALT sequence */}
          <div style={{ background: 'rgba(255,255,255,0.025)', border: `1px solid ${C.redBorder}`, borderRadius: 4, padding: '12px 14px', marginBottom: 16 }}>
            <div style={{ fontFamily: 'monospace', fontSize: 9, color: C.red, letterSpacing: '0.12em', marginBottom: 8 }}>HALT EXECUTION SEQUENCE — RuntimeContinuityEngine</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {[
                '1.  continuity_status → HALT (immutable)',
                '2.  execution_ns recorded',
                '3.  All in-flight sub-tasks → REVOKED',
                '4.  CEE issued and PQC-signed',
                '5.  seal_trigger = "halt_event" → ColdBlockSealer',
                '6.  Emergency COLD block seal initiated',
                '7.  Telegram alert → TELEGRAM_ADMIN_USER_ID',
              ].map((step, i) => (
                <div key={i} style={{ fontFamily: 'monospace', fontSize: 10, color: i <= 2 ? C.red : C.muted }}>{step}</div>
              ))}
            </div>
          </div>

          <div style={{ borderTop: `1px solid ${C.redBorder}30`, paddingTop: 14 }}>
            <div style={{ fontFamily: 'monospace', fontSize: 9, color: C.red, letterSpacing: '0.12em', marginBottom: 6 }}>DESIGN PRINCIPLE — RFC-ATF-2 §6.4</div>
            <p style={{ margin: 0, fontSize: 13, color: 'rgba(255,255,255,0.72)', lineHeight: 1.6 }}>
              The protocol blocked execution. No human instruction was needed. No manual override was possible. The authority delegation expired cryptographically — and the system enforced that expiry exactly as specified.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

function NodeEvidenceLifecycle({ visible }: NodeProps) {
  return (
    <div style={{ animation: visible ? 'fade-up 0.55s 0.05s ease both' : 'none', opacity: visible ? 1 : 0 }}>
      <div style={{ border: `1px solid ${C.greenBorder}`, borderRadius: 5, background: C.navy3, overflow: 'hidden', position: 'relative' }}>
        <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 3, background: `linear-gradient(to bottom, ${C.green}, ${C.green}60)` }} />
        <div style={{ padding: '22px 26px 22px 30px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                <div style={{ fontFamily: 'monospace', fontSize: 9, color: C.green, letterSpacing: '0.14em' }}>L4 · ARCHIVAL LAYER</div>
                <div style={{ width: 20, height: 1, background: `${C.green}40` }} />
                <div style={{ fontFamily: 'monospace', fontSize: 9, color: C.subtle }}>ADR-163 · ADR-126</div>
              </div>
              <h3 style={{ margin: 0, fontSize: 18, fontWeight: 600, color: C.white, letterSpacing: '-0.01em' }}>Evidence Lifecycle</h3>
              <div style={{ fontSize: 12, color: C.muted, marginTop: 3 }}>HOT → WARM → COLD · 9-step migration · MiFID II Art.25</div>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, justifyContent: 'flex-end', maxWidth: 220 }}>
              {['EAP-INV-001','EAP-INV-002','EAP-INV-003','EAP-INV-004'].map(t => (
                <Tag key={t} label={t} color={C.green} bg={C.greenDim} border={C.greenBorder} />
              ))}
            </div>
          </div>

          {/* Tier pipeline */}
          <div style={{ display: 'flex', gap: 0, marginBottom: 14, background: C.navy2, borderRadius: 4, overflow: 'hidden', border: `1px solid ${C.dim}40` }}>
            {[
              { label: 'HOT', duration: '0–30 days', store: 'PostgreSQL live', color: C.red },
              { label: 'WARM', duration: '30d–12mo', store: 'PostgreSQL archive', color: C.amber },
              { label: 'COLD', duration: '12mo–5yr', store: 'S3 / R2 immutable', color: C.blue },
            ].map((tier, i) => (
              <div key={tier.label} style={{ flex: 1, padding: '10px 12px', borderLeft: i > 0 ? `1px solid ${C.dim}40` : 'none' }}>
                <div style={{ fontFamily: 'monospace', fontSize: 11, fontWeight: 700, color: tier.color, marginBottom: 3 }}>{tier.label}</div>
                <div style={{ fontSize: 10, color: C.muted }}>{tier.duration}</div>
                <div style={{ fontSize: 9, color: C.subtle, marginTop: 2, fontFamily: 'monospace' }}>{tier.store}</div>
              </div>
            ))}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 7, marginBottom: 14 }}>
            <DataCard label="Block ID" value="OMNIX-BLOCK-20260518-000147" />
            <DataCard label="Sealed at" value="2026-05-18T15:33:02Z (halt_event)" />
            <DataCard label="Merkle root" value="sha256:d4f8b2c1a9e37f4d..." />
            <DataCard label="Artifact count" value="5 · EXCEPTION · LEGAL · PQC · TELEMETRY" />
            <DataCard label="predecessor_block_hash" value="sha256:a2e9c4b7f1d3a8c..." />
            <DataCard label="canonical_hash" value="sha256:a8f3c24d1b9e7a2c..." />
          </div>

          {/* 9-step protocol */}
          <div style={{ background: C.navy2, border: `1px solid ${C.dim}40`, borderRadius: 4, padding: '12px 14px', marginBottom: 14 }}>
            <div style={{ fontFamily: 'monospace', fontSize: 9, color: C.green, letterSpacing: '0.1em', marginBottom: 7 }}>9-STEP MIGRATION PROTOCOL — receipt_archival.py</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '3px 14px' }}>
              {[
                'Check archival index — idempotent',
                'Mark status=COPYING',
                'Copy to target tier',
                'Re-fetch + verify content_hash',
                'Verify PQC signature',
                'Mark status=VERIFIED',
                'Update tier + storage_location',
                'Delete from source tier',
                'Mark status=ARCHIVED',
              ].map((s, i) => (
                <div key={i} style={{ fontFamily: 'monospace', fontSize: 10, color: C.muted }}>
                  <span style={{ color: C.green, marginRight: 6 }}>Step {i + 1}</span>{s}
                </div>
              ))}
            </div>
          </div>

          <div style={{ borderTop: `1px solid ${C.dim}40`, paddingTop: 12, display: 'flex', gap: 10, alignItems: 'flex-start' }}>
            <div style={{ width: 3, height: 3, borderRadius: '50%', background: C.green, marginTop: 5, flexShrink: 0 }} />
            <p style={{ margin: 0, fontSize: 12, color: C.muted, fontStyle: 'italic', lineHeight: 1.55 }}>
              If step 4 or 5 fails, <span style={{ fontFamily: 'monospace', color: C.red, fontSize: 11 }}>ArchivalIntegrityError</span> is raised. No silent migration. No partial state. The chain of custody is mathematically unbroken.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

function NodeOEPExport({ visible }: NodeProps) {
  return (
    <div style={{ animation: visible ? 'fade-up 0.55s 0.05s ease both' : 'none', opacity: visible ? 1 : 0 }}>
      <div style={{ border: `1px solid ${C.blueBorder}`, borderRadius: 5, background: C.navy3, overflow: 'hidden', position: 'relative' }}>
        <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 3, background: `linear-gradient(to bottom, ${C.blue}, ${C.blue}60)` }} />
        <div style={{ padding: '22px 26px 22px 30px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                <div style={{ fontFamily: 'monospace', fontSize: 9, color: C.blue, letterSpacing: '0.14em' }}>L5 · EXPORT LAYER</div>
                <div style={{ width: 20, height: 1, background: `${C.blue}40` }} />
                <div style={{ fontFamily: 'monospace', fontSize: 9, color: C.subtle }}>ADR-165 · ADR-166</div>
              </div>
              <h3 style={{ margin: 0, fontSize: 18, fontWeight: 600, color: C.white, letterSpacing: '-0.01em' }}>OEP Export</h3>
              <div style={{ fontSize: 12, color: C.muted, marginTop: 3 }}>Sealed Forensic Package · Two-phase ML-DSA-65 signature</div>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, justifyContent: 'flex-end', maxWidth: 220 }}>
              {['FEA-INV-001','FEA-INV-002','FEA-INV-003','OEP-INV-001'].map(t => (
                <Tag key={t} label={t} color={C.blue} bg={C.blueDim} border={C.blueBorder} />
              ))}
            </div>
          </div>

          {/* Package structure tree */}
          <div style={{ background: C.navy2, border: `1px solid ${C.dim}40`, borderRadius: 4, padding: '12px 14px', marginBottom: 14, fontFamily: 'monospace', fontSize: 11 }}>
            <div style={{ fontSize: 9, color: C.blue, letterSpacing: '0.1em', marginBottom: 8 }}>PACKAGE STRUCTURE — OMNIX-PACKAGE-20260518-A3F8C241.oep</div>
            {[
              { path: 'BLOCKS/OMNIX-BLOCK-20260518-000147.json', desc: 'sealed COLD block' },
              { path: 'BLOCKS/chain_index.json',                 desc: 'block order by chain' },
              { path: 'KEYS/public_key.b64',                     desc: 'ML-DSA-65 platform key (1312 bytes)' },
              { path: 'VERIFY/omnix_atf_verify.py',              desc: 'embedded verifier — no install needed' },
              { path: 'VERIFY/verify_all.sh',                    desc: 'full chain verification script' },
              { path: 'META/manifest.json',                      desc: 'SHA-256 of every content file' },
              { path: 'SIGNATURE/package_signature.json',        desc: 'ML-DSA-65 over manifest hash' },
            ].map(f => (
              <div key={f.path} style={{ display: 'flex', gap: 12, marginBottom: 4 }}>
                <span style={{ color: C.blue, minWidth: 300 }}>{f.path}</span>
                <span style={{ color: C.subtle }}>← {f.desc}</span>
              </div>
            ))}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 7, marginBottom: 14 }}>
            <DataCard label="Package ID" value="OEP-20260518-A3F8C241" />
            <DataCard label="canonical_manifest_hash" value="sha256:f1c9b4e2a7d3..." />
            <DataCard label="Signing algorithm" value="ML-DSA-65 (FIPS 204) · signature 3293 bytes" />
            <DataCard label="Two-phase design" value="Phase 1: content → Phase 2: manifest_hash signed" />
          </div>

          <div style={{ borderTop: `1px solid ${C.dim}40`, paddingTop: 12, display: 'flex', gap: 10, alignItems: 'flex-start' }}>
            <div style={{ width: 3, height: 3, borderRadius: '50%', background: C.blue, marginTop: 5, flexShrink: 0 }} />
            <p style={{ margin: 0, fontSize: 12, color: C.muted, fontStyle: 'italic', lineHeight: 1.55 }}>
              The signature covers the content manifest — what was signed cannot include a self-reference to the signature file. This is by design, not a limitation. The embedded verifier requires only Python 3.10+ and <span style={{ fontFamily: 'monospace', color: C.blue, fontSize: 11 }}>pypqc</span>.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

function NodeOfflineVerification({ visible }: NodeProps) {
  const [activeCmd, setActiveCmd] = useState(0)
  const cmds = [
    { id: '7.2', label: 'Verify package signature', cmd: 'python3 verify_manifest.py', result: 'Manifest hash: OK\nPackage signature: VALID\nAlgorithm: ML-DSA-65 (FIPS 204)\nPackage ID: OEP-20260518-A3F8C241' },
    { id: '7.3', label: 'Verify COLD block', cmd: 'python3 omnix_atf_verify.py --mode block', result: '"block_id": "OMNIX-BLOCK-20260518-000147"\n"hash_valid": true\n"pqc_valid": true\n"verdict": "PASS"' },
    { id: '7.4', label: 'Verify chain linkage', cmd: 'python3 omnix_atf_verify.py --verify-chain', result: '"chain_link_valid": true\n"predecessor_hash_matches": true\n"verdict": "PASS"' },
    { id: '7.5', label: 'Full chain verification', cmd: 'bash VERIFY/verify_all.sh', result: 'PASS  OMNIX-BLOCK-20260518-000146\nPASS  OMNIX-BLOCK-20260518-000147\nResult: 2 passed, 0 failed\nSTATUS: ALL BLOCKS PASS' },
    { id: '7.6', label: 'Verify platform key identity', cmd: 'python3 verify_key_identity.py', result: 'Package key fingerprint: sha256:3c7f1a9b...\nCompare: HTTP · DNS · Zenodo\nTrust level: OMNIX_PLATFORM' },
  ]
  return (
    <div style={{ animation: visible ? 'fade-up 0.55s 0.05s ease both' : 'none', opacity: visible ? 1 : 0 }}>
      <div style={{ border: `1px solid ${C.goldBorder}`, borderRadius: 5, background: C.navy3, overflow: 'hidden', position: 'relative' }}>
        <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 3, background: `linear-gradient(to bottom, ${C.gold}, ${C.gold}60)` }} />
        <div style={{ padding: '22px 26px 22px 30px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                <div style={{ fontFamily: 'monospace', fontSize: 9, color: C.gold, letterSpacing: '0.14em' }}>L6 · VERIFICATION LAYER</div>
                <div style={{ width: 20, height: 1, background: `${C.gold}40` }} />
                <div style={{ fontFamily: 'monospace', fontSize: 9, color: C.subtle }}>ADR-164 · ADR-167</div>
              </div>
              <h3 style={{ margin: 0, fontSize: 18, fontWeight: 600, color: C.white, letterSpacing: '-0.01em' }}>Offline Verification</h3>
              <div style={{ fontSize: 12, color: C.muted, marginTop: 3 }}>Zero platform access · Python 3.10+ · pip install pypqc</div>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, justifyContent: 'flex-end', maxWidth: 220 }}>
              {['FVP-INV-007','ATF-INV-006','EAP-INV-005'].map(t => (
                <Tag key={t} label={t} color={C.gold} bg={C.goldDim} border={C.goldBorder} />
              ))}
            </div>
          </div>

          {/* Interactive terminal tabs */}
          <div style={{ marginBottom: 14 }}>
            <div style={{ display: 'flex', gap: 4, marginBottom: 0, flexWrap: 'wrap' }}>
              {cmds.map((c, i) => (
                <button key={c.id} onClick={() => setActiveCmd(i)} style={{
                  fontFamily: 'monospace', fontSize: 9, padding: '5px 10px', borderRadius: '3px 3px 0 0',
                  border: `1px solid ${i === activeCmd ? C.goldBorder : C.dim + '50'}`,
                  borderBottom: i === activeCmd ? `1px solid ${C.navy2}` : undefined,
                  background: i === activeCmd ? C.navy2 : 'transparent',
                  color: i === activeCmd ? C.gold : C.subtle,
                  cursor: 'pointer', letterSpacing: '0.06em',
                }}>
                  §{c.id}
                </button>
              ))}
            </div>
            <div style={{ background: C.navy2, border: `1px solid ${C.goldBorder}`, borderRadius: '0 3px 3px 3px', padding: '14px 16px' }}>
              <div style={{ fontFamily: 'monospace', fontSize: 10, color: C.subtle, marginBottom: 8 }}>{cmds[activeCmd].label}</div>
              <div style={{ fontFamily: 'monospace', fontSize: 11, color: C.green, marginBottom: 10 }}>
                <span style={{ color: C.subtle }}>$ </span>{cmds[activeCmd].cmd}
              </div>
              <pre style={{ margin: 0, fontFamily: 'monospace', fontSize: 11, color: C.text, lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                {cmds[activeCmd].result}
              </pre>
            </div>
          </div>

          {/* Verification matrix */}
          <div style={{ marginBottom: 14 }}>
            <div style={{ fontFamily: 'monospace', fontSize: 9, color: C.gold, letterSpacing: '0.1em', marginBottom: 8 }}>WHAT AN AUDITOR CAN VERIFY OFFLINE</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {[
                ['Package integrity (no tampering)',  '§7.2 — manifest hash + ML-DSA-65'],
                ['Block internal integrity',          '§7.3 — canonical hash + PQC signature'],
                ['Chain continuity',                  '§7.4 — predecessor_block_hash linkage'],
                ['Full chain pass',                   '§7.5 — bash verify_all.sh'],
                ['Platform key identity',             '§7.6 — fingerprint vs DNS/HTTP/Zenodo'],
              ].map(([what, how]) => (
                <div key={what} style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                  <span style={{ color: C.green, fontFamily: 'monospace', fontSize: 11 }}>✓</span>
                  <span style={{ fontSize: 11, color: C.muted, flex: 1 }}>{what}</span>
                  <span style={{ fontFamily: 'monospace', fontSize: 10, color: C.subtle }}>{how}</span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ background: C.goldDim, border: `1px solid ${C.goldBorder}`, borderRadius: 4, padding: '12px 16px' }}>
            <div style={{ fontFamily: 'monospace', fontSize: 10, color: C.gold, letterSpacing: '0.1em', marginBottom: 5 }}>ZERO PLATFORM DEPENDENCY</div>
            <p style={{ margin: 0, fontSize: 12, color: C.text, lineHeight: 1.55 }}>
              The OMNIX platform is needed to <em>produce</em> governance receipts. It is never needed to <em>verify</em> them. An auditor with no OMNIX account, in any jurisdiction, can verify the entire chain from the sealed package alone.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────────
export default function GovernanceFlowPage() {
  const navigate = useNavigate()
  const nodeRefs = useRef<(HTMLDivElement | null)[]>([])
  const [visible, setVisible] = useState<boolean[]>(Array(7).fill(false))

  useEffect(() => {
    const observers: IntersectionObserver[] = []
    nodeRefs.current.forEach((el, i) => {
      if (!el) return
      const obs = new IntersectionObserver(
        ([entry]) => { if (entry.isIntersecting) { setVisible(prev => { const n = [...prev]; n[i] = true; return n }); obs.disconnect() } },
        { threshold: 0.12 }
      )
      obs.observe(el)
      observers.push(obs)
    })
    return () => observers.forEach(o => o.disconnect())
  }, [])

  const nodeComponents = [
    <NodeHumanAuthority visible={visible[0]} />,
    <NodeRuntimeGovernance visible={visible[1]} />,
    <NodeGovernanceEvent visible={visible[2]} />,
    <NodeEnforcement visible={visible[3]} />,
    <NodeEvidenceLifecycle visible={visible[4]} />,
    <NodeOEPExport visible={visible[5]} />,
    <NodeOfflineVerification visible={visible[6]} />,
  ]

  const connectors = [
    { top: C.gold,  bottom: C.blue,  label: undefined },
    { top: C.blue,  bottom: C.amber, label: undefined },
    { top: C.amber, bottom: C.red,   label: 'ADMISSIBILITY GATE' },
    { top: C.red,   bottom: C.green, label: undefined },
    { top: C.green, bottom: C.blue,  label: undefined },
    { top: C.blue,  bottom: C.gold,  label: undefined },
  ]

  return (
    <>
      <style>{CSS}</style>
      <div style={{ minHeight: '100vh', background: C.navy, color: C.text, fontFamily: "'Inter', system-ui, sans-serif" }}>

        {/* ── Dot grid background ── */}
        <div style={{
          position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 0,
          backgroundImage: `radial-gradient(circle, rgba(201,162,39,0.07) 1px, transparent 1px)`,
          backgroundSize: '36px 36px',
        }} />

        {/* ── Nav ── */}
        <div style={{
          position: 'sticky', top: 0, zIndex: 100,
          background: 'rgba(6,15,30,0.94)', backdropFilter: 'blur(14px)',
          borderBottom: `1px solid rgba(201,162,39,0.10)`,
          padding: '0 32px', height: 50,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <span onClick={() => navigate('/')} style={{ fontFamily: 'monospace', fontSize: 11, color: C.gold, letterSpacing: '0.12em', cursor: 'pointer', opacity: 0.9 }}>OMNIX QUANTUM LTD</span>
            <span style={{ color: C.dim, fontSize: 11 }}>│</span>
            <span style={{ fontSize: 11, color: C.subtle, letterSpacing: '0.06em' }}>GOVERNANCE LIFECYCLE · OMNIX-WALK-001</span>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            {[
              ['Forensic Demos', '/forensic-operations'],
              ['Trust Registry', '/trust-infrastructure'],
              ['Live Verifier',  '/archive-verify'],
            ].map(([l, p]) => (
              <button key={p} onClick={() => navigate(p)} style={{
                background: 'none', border: `1px solid ${C.goldBorder}`, borderRadius: 3,
                padding: '4px 12px', fontSize: 10, color: C.gold, cursor: 'pointer',
                fontFamily: 'monospace', letterSpacing: '0.06em',
              }}>{l} ↗</button>
            ))}
          </div>
        </div>

        {/* ── Hero ── */}
        <div style={{ position: 'relative', zIndex: 1, maxWidth: 900, margin: '0 auto', padding: '68px 32px 40px', textAlign: 'center' }}>
          {/* Tags row */}
          <div style={{ display: 'flex', gap: 7, justifyContent: 'center', marginBottom: 28, flexWrap: 'wrap' }}>
            {[
              { l: 'RFC-ATF-1', href: 'https://doi.org/10.5281/zenodo.20155016' },
              { l: 'RFC-ATF-2', href: 'https://doi.org/10.5281/zenodo.20241344' },
              { l: 'RFC-ATF-3', href: 'https://doi.org/10.5281/zenodo.20247342' },
              { l: 'RFC-ATF-4', href: 'https://doi.org/10.5281/zenodo.20368895' },
            ].map(r => (
              <a key={r.l} href={r.href} target="_blank" rel="noreferrer" style={{
                fontFamily: 'monospace', fontSize: 9, color: C.gold,
                background: C.goldDim, border: `1px solid ${C.goldBorder}`,
                padding: '3px 10px', borderRadius: 2, letterSpacing: '0.10em', textDecoration: 'none',
              }}>{r.l} · DOI ↗</a>
            ))}
            {['67 INVARIANTS · 9 FAMILIES', '184 ADRs', 'ML-DSA-65 · FIPS 204', 'OMNIX-WALK-001'].map(b => (
              <span key={b} style={{ fontFamily: 'monospace', fontSize: 9, color: C.subtle, background: `rgba(255,255,255,0.03)`, border: `1px solid ${C.dim}50`, padding: '3px 10px', borderRadius: 2, letterSpacing: '0.08em' }}>{b}</span>
            ))}
          </div>

          <h1 style={{ fontSize: 42, fontWeight: 700, margin: '0 0 14px', color: C.white, letterSpacing: '-0.03em', lineHeight: 1.12 }}>
            Governance Lifecycle
          </h1>
          <p style={{ fontSize: 15, color: C.muted, maxWidth: 580, margin: '0 auto 24px', lineHeight: 1.65 }}>
            From human-signed delegation to cryptographic proof of every enforcement decision —
            sealed for offline verification by any auditor, anywhere, without platform access.
          </p>

          {/* Core principle banner */}
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 12,
            background: C.redDim, border: `1px solid ${C.redBorder}`,
            borderRadius: 4, padding: '10px 22px',
          }}>
            <div style={{ width: 6, height: 6, borderRadius: '50%', background: C.red, boxShadow: `0 0 10px ${C.red}`, flexShrink: 0, animation: 'dot-fade 2.5s ease-in-out infinite' }} />
            <span style={{ fontFamily: 'monospace', fontSize: 11, color: C.red, letterSpacing: '0.09em' }}>
              THE PROTOCOL DECIDES WHETHER EXECUTION IS ADMITTED
            </span>
          </div>

          {/* Stats strip */}
          <div style={{
            display: 'flex', justifyContent: 'center', gap: 0, marginTop: 32,
            background: C.navy2, border: `1px solid ${C.dim}40`, borderRadius: 5, overflow: 'hidden', maxWidth: 700, marginLeft: 'auto', marginRight: 'auto',
          }}>
            {[
              { v: '67', l: 'Active Invariants', c: C.gold },
              { v: '9',  l: 'Invariant Families', c: C.gold },
              { v: '4',  l: 'Published RFCs',    c: C.green },
              { v: '184', l: 'ADRs',             c: C.blue },
              { v: '245+', l: 'Tests passing',   c: C.green },
            ].map((s, i) => (
              <div key={s.l} style={{
                flex: 1, padding: '14px 10px', textAlign: 'center',
                borderLeft: i > 0 ? `1px solid ${C.dim}40` : 'none',
              }}>
                <div style={{ fontSize: 20, fontWeight: 700, color: s.c, fontFamily: 'monospace' }}>{s.v}</div>
                <div style={{ fontSize: 9, color: C.subtle, marginTop: 3, letterSpacing: '0.06em' }}>{s.l}</div>
              </div>
            ))}
          </div>
        </div>

        {/* ── Flow ── */}
        <div style={{ position: 'relative', zIndex: 1, maxWidth: 800, margin: '0 auto', padding: '0 32px 80px' }}>
          {/* Layer legend rail */}
          <div style={{
            position: 'absolute', left: 0, top: 20, bottom: 20, width: 28,
            display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0,
          }}>
            {[
              { label: 'L1', color: C.gold },
              { label: 'L2', color: C.blue },
              { label: 'L3', color: C.amber },
              { label: '⬡',  color: C.red },
              { label: 'L4', color: C.green },
              { label: 'L5', color: C.blue },
              { label: 'L6', color: C.gold },
            ].map((l, i) => (
              <div key={i} style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{
                  width: 22, height: 22,
                  border: `1px solid ${l.color}50`, borderRadius: 3,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  background: `${l.color}08`,
                  fontFamily: 'monospace', fontSize: l.label === '⬡' ? 11 : 10,
                  color: l.color, fontWeight: 600,
                }}>
                  {l.label}
                </div>
              </div>
            ))}
          </div>

          {nodeComponents.map((node, i) => (
            <div key={i}>
              <div ref={el => { nodeRefs.current[i] = el }}>
                {node}
              </div>
              {i < nodeComponents.length - 1 && (
                <Connector
                  topColor={connectors[i].top}
                  bottomColor={connectors[i].bottom}
                  label={connectors[i].label}
                />
              )}
            </div>
          ))}
        </div>

        {/* ── RFC DOI strip ── */}
        <div style={{ position: 'relative', zIndex: 1, borderTop: `1px solid ${C.dim}40`, background: C.navy2, padding: '28px 32px' }}>
          <div style={{ maxWidth: 800, margin: '0 auto' }}>
            <div style={{ fontFamily: 'monospace', fontSize: 9, color: C.gold, letterSpacing: '0.12em', marginBottom: 14 }}>PUBLISHED RFC STACK — PERMANENT DOI RECORD</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 10 }}>
              {[
                { rfc: 'RFC-ATF-1', title: 'Delegation Protocol with PQC (ML-DSA-65 / FIPS 204)', zenodo: 'https://doi.org/10.5281/zenodo.20155016', fig: 'https://doi.org/10.6084/m9.figshare.32308077' },
                { rfc: 'RFC-ATF-2', title: 'Runtime Governance Continuity',                       zenodo: 'https://doi.org/10.5281/zenodo.20241344', fig: 'https://doi.org/10.6084/m9.figshare.32308095' },
                { rfc: 'RFC-ATF-3', title: 'GPIL · Evidence Lifecycle · Forensic Verification',   zenodo: 'https://doi.org/10.5281/zenodo.20247342', fig: 'https://doi.org/10.6084/m9.figshare.32308119' },
                { rfc: 'RFC-ATF-4', title: 'Proactive Governance · AGVP · SSD · DSPP · 19 Z3 Proofs', zenodo: 'https://doi.org/10.5281/zenodo.20368895', fig: 'https://doi.org/10.6084/m9.figshare.32394192' },
              ].map(r => (
                <div key={r.rfc} style={{ background: C.navy3, border: `1px solid ${C.goldBorder}`, borderRadius: 4, padding: '12px 14px' }}>
                  <div style={{ fontFamily: 'monospace', fontSize: 11, fontWeight: 700, color: C.gold, marginBottom: 5 }}>{r.rfc}</div>
                  <div style={{ fontSize: 11, color: C.muted, lineHeight: 1.45, marginBottom: 8 }}>{r.title}</div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <a href={r.zenodo} target="_blank" rel="noreferrer" style={{ fontFamily: 'monospace', fontSize: 9, color: C.blue, textDecoration: 'none', letterSpacing: '0.06em' }}>Zenodo ↗</a>
                    <a href={r.fig}    target="_blank" rel="noreferrer" style={{ fontFamily: 'monospace', fontSize: 9, color: C.blue, textDecoration: 'none', letterSpacing: '0.06em' }}>Figshare ↗</a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Footer ── */}
        <div style={{ position: 'relative', zIndex: 1, borderTop: `1px solid ${C.dim}40`, padding: '22px 32px' }}>
          <div style={{ maxWidth: 800, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 14 }}>
            <div>
              <div style={{ fontFamily: 'monospace', fontSize: 10, color: C.gold, letterSpacing: '0.10em', marginBottom: 3 }}>OMNIX QUANTUM LTD · OMNIX-WALK-001 · ATF BASELINE 2026.05</div>
              <div style={{ fontSize: 11, color: C.subtle }}>Every field, formula, ID and command derives from production source code. Nothing in this diagram is illustrative.</div>
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {[
                ['Forensic Demos',    '/forensic-operations'],
                ['Live Verifier',     '/archive-verify'],
                ['Trust Registry',    '/trust-infrastructure'],
                ['Protocol',         '/protocol'],
              ].map(([l, p]) => (
                <button key={p} onClick={() => navigate(p)} style={{
                  background: C.goldDim, border: `1px solid ${C.goldBorder}`, borderRadius: 3,
                  padding: '6px 14px', fontSize: 11, color: C.gold, cursor: 'pointer', fontFamily: 'monospace',
                }}>{l}</button>
              ))}
            </div>
          </div>
        </div>

      </div>
    </>
  )
}
