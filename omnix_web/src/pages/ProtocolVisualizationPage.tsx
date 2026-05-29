import { useState } from 'react'

// ─── Design System ────────────────────────────────────────────────────────────
const C = {
  bg:       '#05070B',
  surface:  '#080D14',
  card:     '#0B1220',
  border:   'rgba(0,229,255,0.10)',
  borderGold: 'rgba(245,185,66,0.20)',
  cyan:     '#00E5FF',
  gold:     '#F5B942',
  red:      '#FF4D4D',
  green:    '#3CFF8F',
  purple:   '#A78BFA',
  blue:     '#38BDF8',
  gray:     '#475569',
  muted:    '#94A3B8',
  text:     '#E2E8F0',
}

// ─── Shared primitives ────────────────────────────────────────────────────────
function Pill({ label, color = C.cyan }: { label: string; color?: string }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center',
      padding: '2px 10px', borderRadius: 20,
      fontSize: 10, fontWeight: 700, letterSpacing: '0.08em',
      color, background: color + '18', border: `1px solid ${color}33`,
    }}>{label}</span>
  )
}

function ADRBadge({ adr }: { adr: string }) {
  return <Pill label={adr} color={C.gold} />
}

function GlowDot({ color }: { color: string }) {
  return (
    <div style={{
      width: 8, height: 8, borderRadius: '50%', background: color, flexShrink: 0,
      boxShadow: `0 0 8px ${color}88`,
    }} />
  )
}

// ─── Diagram 1: Runtime Legitimacy Stack ─────────────────────────────────────
const STACK_LAYERS = [
  {
    id: 'L0', label: 'Human Authority Root',
    sub: 'ML-DSA-65 Root Key · Sovereign Operator · Trust Anchor',
    color: C.gold, adrs: ['RFC-ATF-1'], tag: 'LAYER 0 — HUMAN AUTHORITY',
    artifacts: ['Root Identity', 'Root Signature', 'Key Governance'],
    icon: '◈',
  },
  {
    id: 'L1', label: 'Agent Trust Fabric (ATF)',
    sub: 'Delegation Receipt chain · MAR enforcement · Authority budget propagation · Cross-domain bridges',
    color: C.cyan, adrs: ['ADR-156', 'ADR-157', 'ADR-158'], tag: 'LAYER 1 — DELEGATION',
    artifacts: ['DR', 'TAR', 'DTR', 'CRGC'],
    icon: '⬡',
  },
  {
    id: 'L2', label: 'Temporal Admissibility',
    sub: 'Nanosecond execution timestamps · Authority validity window · Pre-execution admissibility gate',
    color: C.purple, adrs: ['ADR-157'], tag: 'LAYER 2 — TEMPORAL',
    artifacts: ['TAR', 'execution_ns', 'dr_expires_at', 'T-component'],
    icon: '◷',
  },
  {
    id: 'L3', label: 'Runtime Governance Continuity (RGC)',
    sub: 'CES scoring · AFG enforcement · RC issuance · Escalation engine · Sibling revocation',
    color: C.green, adrs: ['ADR-159', 'ADR-160', 'ADR-161'], tag: 'LAYER 3 — CONTINUITY',
    artifacts: ['RCR', 'CES', 'RC', 'AFG', 'CRGC'],
    icon: '⟳',
  },
  {
    id: 'L4', label: 'Governance Execution Gate',
    sub: 'GovernanceReceipt issuance · ALLOW / HALT / ESCALATE verdict · Execution legitimacy proof',
    color: C.gold, adrs: ['ADR-131', 'ADR-138', 'ADR-147'], tag: 'LAYER 4 — EXECUTION',
    artifacts: ['GovernanceReceipt', 'ALLOW', 'HALT', 'ESCALATE'],
    icon: '⬟',
  },
  {
    id: 'L5', label: 'Immutable Evidence Lifecycle',
    sub: 'HOT/WARM/COLD tiers · Evidence classification · PQC archive · Offline verifiability',
    color: C.blue, adrs: ['ADR-162', 'ADR-163'], tag: 'LAYER 5 — EVIDENCE',
    artifacts: ['Evidence Classes', 'Block Archive', 'Custody Log', 'Verifier'],
    icon: '▣',
  },
]

function DiagramStack() {
  const [active, setActive] = useState<string | null>(null)
  return (
    <div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 3, position: 'relative' }}>
        {/* Vertical spine */}
        <div style={{
          position: 'absolute', left: 28, top: 24, bottom: 24, width: 2,
          background: `linear-gradient(to bottom, ${C.gold}44, ${C.cyan}44, ${C.purple}44, ${C.green}44, ${C.gold}44, ${C.blue}44)`,
          zIndex: 0,
        }} />

        {STACK_LAYERS.map((layer, i) => {
          const isActive = active === layer.id
          return (
            <div
              key={layer.id}
              onClick={() => setActive(isActive ? null : layer.id)}
              style={{
                display: 'flex', gap: 16, alignItems: 'flex-start',
                padding: '16px 20px', borderRadius: 10, cursor: 'pointer',
                border: `1px solid ${isActive ? layer.color + '55' : layer.color + '1A'}`,
                background: isActive ? layer.color + '0C' : C.card,
                transition: 'all 0.18s', position: 'relative', zIndex: 1,
              }}
            >
              {/* Layer indicator */}
              <div style={{
                width: 40, height: 40, borderRadius: 8, flexShrink: 0,
                background: layer.color + '18', border: `1px solid ${layer.color}44`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 18, color: layer.color,
              }}>{layer.icon}</div>

              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 4 }}>
                  <span style={{ fontSize: 10, fontWeight: 700, color: layer.color, letterSpacing: '0.1em' }}>{layer.tag}</span>
                  {layer.adrs.map(a => <ADRBadge key={a} adr={a} />)}
                </div>
                <div style={{ fontSize: 15, fontWeight: 700, color: C.text, marginBottom: 4,
                  fontFamily: "'Space Grotesk', 'Inter', sans-serif" }}>{layer.label}</div>
                {isActive && (
                  <>
                    <p style={{ fontSize: 13, color: C.muted, lineHeight: 1.6, marginBottom: 10 }}>{layer.sub}</p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {layer.artifacts.map(a => (
                        <span key={a} style={{
                          fontSize: 11, fontWeight: 600, padding: '2px 8px', borderRadius: 6,
                          background: layer.color + '18', color: layer.color,
                          fontFamily: 'monospace', border: `1px solid ${layer.color}33`,
                        }}>{a}</span>
                      ))}
                    </div>
                  </>
                )}
              </div>

              {/* Layer number */}
              <div style={{
                fontSize: 11, fontWeight: 800, color: layer.color + '66',
                fontFamily: 'monospace', flexShrink: 0,
              }}>L{i}</div>
            </div>
          )
        })}
      </div>

      {/* Bottom signal flow */}
      <div style={{
        marginTop: 20, padding: '12px 16px', borderRadius: 8,
        background: 'rgba(0,229,255,0.04)', border: `1px solid ${C.cyan}22`,
        display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap',
      }}>
        <GlowDot color={C.gold} />
        <span style={{ fontSize: 11, color: C.muted }}>
          Every execution path traverses L0 → L5. Authority budget propagates downward.
          Evidence flows upward to immutable custody.
        </span>
        <span style={{ fontSize: 11, fontWeight: 700, color: C.cyan, marginLeft: 'auto' }}>47 active invariants · 9 governance families</span>
      </div>
    </div>
  )
}

// ─── Diagram 2: Execution Legitimacy Chain ────────────────────────────────────
const CHAIN_STEPS = [
  {
    id: 'ROOT', label: 'Human Authority',
    artifact: 'Root Identity',
    fields: ['root_key_id', 'ML-DSA-65 root signature', 'operator_identity'],
    color: C.gold, desc: 'The trust anchor. All authority traces back to a human-controlled root key.',
  },
  {
    id: 'DR', label: 'Delegation Receipt',
    artifact: 'DR',
    fields: ['delegation_id', 'authority_budget', 'chain_root_id', 'pqc_signature'],
    color: C.cyan, desc: 'MAR-enforced delegation. Authority budget is explicitly bounded. ML-DSA-65 signed.',
  },
  {
    id: 'TAR', label: 'Temporal Admissibility Record',
    artifact: 'TAR',
    fields: ['tar_id', 'execution_ns', 'dr_expires_at_ns', 'T-component'],
    color: C.purple, desc: 'Authority validity at nanosecond resolution. T=0 when DR expires — admissibility becomes indeterminate.',
  },
  {
    id: 'RCR', label: 'Runtime Continuity Record',
    artifact: 'RCR',
    fields: ['rcr_id', 'ces_score', 'continuity_status', 'content_hash'],
    color: C.green, desc: 'Live CES score: T×0.30 + B×0.30 + D×0.20 + I×0.20. Status: NOMINAL→MONITORING→WARNING→CRITICAL→HALT.',
  },
  {
    id: 'GR', label: 'Governance Receipt',
    artifact: 'GovernanceReceipt',
    fields: ['receipt_id', 'verdict', 'pqc_signature', 'checkpoint_results'],
    color: C.gold, desc: 'Execution verdict: ALLOW / HALT / ESCALATE. PQC-signed. Independently verifiable without OMNIX runtime.',
  },
  {
    id: 'ARCHIVE', label: 'Immutable Archive',
    artifact: 'COLD Block',
    fields: ['block_id', 'canonical_hash', 'predecessor_block_hash', 'ML-DSA-65 signature'],
    color: C.blue, desc: 'Append-only COLD block. Hash-chained to predecessor. Offline verifiable. Evidence custody preserved permanently.',
  },
]

function DiagramChain() {
  const [active, setActive] = useState<string>('DR')
  const step = CHAIN_STEPS.find(s => s.id === active)!
  return (
    <div>
      {/* Flow row */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 0,
        overflowX: 'auto', paddingBottom: 8, marginBottom: 24,
      }}>
        {CHAIN_STEPS.map((s, i) => (
          <div key={s.id} style={{ display: 'flex', alignItems: 'center', flexShrink: 0 }}>
            <button
              onClick={() => setActive(s.id)}
              style={{
                display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6,
                padding: '12px 14px', borderRadius: 10, cursor: 'pointer',
                border: `1px solid ${active === s.id ? s.color + '88' : s.color + '22'}`,
                background: active === s.id ? s.color + '14' : C.card,
                transition: 'all 0.15s',
              }}
            >
              <div style={{
                width: 36, height: 36, borderRadius: 8,
                background: s.color + '22', border: `1px solid ${s.color}55`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 11, fontWeight: 800, color: s.color, fontFamily: 'monospace',
              }}>{s.id}</div>
              <span style={{ fontSize: 10, fontWeight: 700, color: active === s.id ? s.color : C.muted, letterSpacing: '0.04em', whiteSpace: 'nowrap' }}>
                {s.artifact}
              </span>
            </button>
            {i < CHAIN_STEPS.length - 1 && (
              <div style={{ display: 'flex', alignItems: 'center', padding: '0 4px' }}>
                <svg width={24} height={12} viewBox="0 0 24 12">
                  <defs>
                    <linearGradient id={`arr${i}`} x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor={CHAIN_STEPS[i].color} />
                      <stop offset="100%" stopColor={CHAIN_STEPS[i+1].color} />
                    </linearGradient>
                  </defs>
                  <line x1="0" y1="6" x2="20" y2="6" stroke={`url(#arr${i})`} strokeWidth="1.5" />
                  <polygon points="20,3 24,6 20,9" fill={CHAIN_STEPS[i+1].color} />
                </svg>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Detail panel */}
      <div style={{
        padding: 24, borderRadius: 12,
        border: `1px solid ${step.color}33`, background: step.color + '08',
      }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16 }}>
          <div style={{
            width: 48, height: 48, borderRadius: 10, flexShrink: 0,
            background: step.color + '22', border: `1px solid ${step.color}55`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 13, fontWeight: 800, color: step.color, fontFamily: 'monospace',
          }}>{step.id}</div>
          <div>
            <div style={{ fontSize: 18, fontWeight: 800, color: C.text, marginBottom: 4,
              fontFamily: "'Space Grotesk', 'Inter', sans-serif" }}>{step.label}</div>
            <p style={{ fontSize: 13, color: C.muted, lineHeight: 1.7, marginBottom: 14 }}>{step.desc}</p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {step.fields.map(f => (
                <span key={f} style={{
                  fontSize: 11, fontWeight: 600, padding: '3px 10px', borderRadius: 6,
                  background: step.color + '18', color: step.color,
                  fontFamily: 'monospace', border: `1px solid ${step.color}33`,
                }}>{f}</span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Invariant bar */}
      <div style={{
        marginTop: 16, padding: '10px 14px', borderRadius: 8,
        background: 'rgba(245,185,66,0.04)', border: `1px solid ${C.gold}22`,
        fontSize: 11, color: C.muted,
      }}>
        <span style={{ color: C.gold, fontWeight: 700 }}>ATF-INV-006 · EAP-INV-001–005:</span>
        {' '}Each artifact is independently verifiable at every stage — no OMNIX runtime required for offline verification.
      </div>
    </div>
  )
}

// ─── Diagram 3: Sovereign Runtime Divergence (GPIL) ──────────────────────────
const RUNTIMES = [
  {
    id: 'A', name: 'Runtime A', label: 'Strict',
    afg: 0.70, ttl: 120, sampling: 'DENSE', risk: 'LOW',
    color: C.cyan,
    verdict: 'REJECT', verdictColor: C.red,
    desc: 'High sensitivity, short TTL, dense sampling. Rejects decisions that Runtime C approves.',
  },
  {
    id: 'B', name: 'Runtime B', label: 'Balanced',
    afg: 0.85, ttl: 300, sampling: 'STANDARD', risk: 'MEDIUM',
    color: C.purple,
    verdict: 'ESCALATE', verdictColor: C.gold,
    desc: 'Default policy parameters. Escalates to human review when runtimes A and C diverge.',
  },
  {
    id: 'C', name: 'Runtime C', label: 'Throughput',
    afg: 0.95, ttl: 600, sampling: 'SPARSE', risk: 'HIGH',
    color: C.green,
    verdict: 'APPROVE', verdictColor: C.green,
    desc: 'Optimized for throughput. Approves decisions that strict runtimes reject.',
  },
]

const DIVERGENCE_SURFACE = [
  { param: 'afg_fragmentation_limit', desc: 'Authority fragmentation ceiling', values: ['0.70', '0.85', '0.95'] },
  { param: 'rc_ttl_seconds', desc: 'Reauthorization challenge TTL', values: ['120s', '300s', '600s'] },
  { param: 'sampling_profile', desc: 'CES sampling density', values: ['DENSE', 'STANDARD', 'SPARSE'] },
  { param: 'anomaly_counting_method', desc: 'Anomaly count methodology', values: ['STRICT', 'STANDARD', 'RELAXED'] },
  { param: 'context_drift_methodology', desc: 'Context drift measurement', values: ['DELTA_STRICT', 'EWMA', 'SLIDING'] },
]

function DiagramGPIL() {
  const [showSurface, setShowSurface] = useState(false)
  return (
    <div>
      {/* Three runtimes */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 20 }}>
        {RUNTIMES.map(rt => (
          <div key={rt.id} style={{
            padding: '20px 16px', borderRadius: 12,
            border: `1px solid ${rt.color}33`, background: rt.color + '08',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 800, color: rt.color,
                  fontFamily: "'Space Grotesk', 'Inter', sans-serif" }}>{rt.name}</div>
                <div style={{ fontSize: 10, color: C.muted, marginTop: 2 }}>{rt.label}</div>
              </div>
              <div style={{
                padding: '4px 10px', borderRadius: 20, fontSize: 10, fontWeight: 800,
                color: rt.verdictColor, background: rt.verdictColor + '18',
                border: `1px solid ${rt.verdictColor}44`, letterSpacing: '0.08em',
              }}>{rt.verdict}</div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 5, marginBottom: 12 }}>
              {[
                { k: 'AFG limit', v: rt.afg },
                { k: 'RC TTL', v: rt.ttl + 's' },
                { k: 'Sampling', v: rt.sampling },
              ].map(({ k, v }) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
                  <span style={{ color: C.muted }}>{k}</span>
                  <span style={{ color: rt.color, fontWeight: 700, fontFamily: 'monospace' }}>{v}</span>
                </div>
              ))}
            </div>

            <p style={{ fontSize: 11, color: C.muted, lineHeight: 1.5 }}>{rt.desc}</p>
          </div>
        ))}
      </div>

      {/* Shared compliance layer */}
      <div style={{
        padding: '14px 16px', borderRadius: 10, marginBottom: 12,
        border: `1px solid ${C.gold}33`, background: C.gold + '06',
        display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap',
      }}>
        <span style={{ fontSize: 11, fontWeight: 800, color: C.gold }}>SHARED — ALL RUNTIMES</span>
        {['CI: ATF-INV-001–006', 'PI: RGC-INV-001–008', 'ML-DSA-65 verification', 'Offline verifiability'].map(item => (
          <span key={item} style={{
            fontSize: 11, color: C.text, padding: '2px 8px', borderRadius: 6,
            background: C.gold + '12', border: `1px solid ${C.gold}33`,
          }}>{item}</span>
        ))}
      </div>

      {/* Key insight */}
      <div style={{
        padding: '12px 16px', borderRadius: 8,
        background: 'rgba(167,139,250,0.06)', border: `1px solid ${C.purple}33`,
        fontSize: 12, color: C.muted, lineHeight: 1.6,
      }}>
        <span style={{ color: C.purple, fontWeight: 700 }}>ADR-161 — GPIL:</span>
        {' '}Runtime divergence is not a protocol failure — it is a formally specified property.
        Runtimes that diverge on policy remain cryptographically interoperable and independently verifiable.
        <button
          onClick={() => setShowSurface(!showSurface)}
          style={{
            marginLeft: 10, fontSize: 11, color: C.cyan, background: 'transparent',
            border: `1px solid ${C.cyan}33`, borderRadius: 6, padding: '1px 8px', cursor: 'pointer',
          }}
        >{showSurface ? '▲ Hide' : '▼ Divergence surface'}</button>
      </div>

      {showSurface && (
        <div style={{ marginTop: 10 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: C.muted, marginBottom: 8, letterSpacing: '0.08em' }}>
            POLICY DIVERGENCE SURFACE — 5 PARAMETERS
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {DIVERGENCE_SURFACE.map((row, i) => (
              <div key={row.param} style={{
                display: 'grid', gridTemplateColumns: '220px 1fr 1fr 1fr 1fr', gap: 8,
                padding: '8px 12px', borderRadius: 6, alignItems: 'center',
                background: i % 2 === 0 ? C.card : 'transparent',
              }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: C.cyan, fontFamily: 'monospace' }}>{row.param}</span>
                <span style={{ fontSize: 10, color: C.muted }}>{row.desc}</span>
                {row.values.map((v, j) => (
                  <span key={v} style={{
                    fontSize: 11, fontWeight: 700, textAlign: 'center',
                    color: [C.cyan, C.purple, C.green][j], fontFamily: 'monospace',
                  }}>{v}</span>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Diagram 4: Runtime Authority Degradation ─────────────────────────────────
const DEGRADATION_EVENTS = [
  {
    t: 'T₀', label: 'TAR Admitted', ces: 100, status: 'NOMINAL', color: C.green,
    events: ['DR valid', 'TAR issued', 'CES = 100.0', 'authority_budget = 100%'],
    desc: 'Agent admitted. Full authority. CES components: T=100 B=100 D=100 I=100.',
  },
  {
    t: 'T₁', label: 'Budget Consumption', ces: 74, status: 'MONITORING', color: C.blue,
    events: ['budget_consumed = 60%', 'B-component → 40', 'CES → 74.0', 'RC issued'],
    desc: 'Authority budget depleted. B-component falls. RC (Reauthorization Challenge) emitted.',
  },
  {
    t: 'T₂', label: 'DR Expiry Approaching', ces: 48, status: 'WARNING', color: C.gold,
    events: ['DR nearing expiry', 'T-component → 30', 'context_drift = 40%', 'CES → 48.0'],
    desc: 'DR temporal window closing. T-component degrades. Temporal admissibility drifting.',
  },
  {
    t: 'T₃', label: 'Fragmentation Event', ces: 19, status: 'CRITICAL', color: '#FF8C00',
    events: ['AFG threshold exceeded', 'sibling spawning suspended', 'REAUTHORIZE action', 'CES → 19.0'],
    desc: 'Authority fragmentation detected. RGC-INV-004 at boundary. REAUTHORIZE action issued.',
  },
  {
    t: 'T₄', label: 'HALT Executed', ces: 0, status: 'HALT', color: C.red,
    events: ['CES < 10', 'HALT triggered', 'sibling sessions REVOKED', 'GovernanceReceipt DENIED'],
    desc: 'RGC-INV-003: HALT propagates. All sibling sessions on the chain root are revoked. Evidence archived.',
  },
]

function DiagramDegradation() {
  const [active, setActive] = useState(0)
  const ev = DEGRADATION_EVENTS[active]

  // Compute bar width for CES gauge
  const barWidth = (ces: number) => `${ces}%`
  const barColor = (ces: number) => ces >= 75 ? C.green : ces >= 50 ? C.blue : ces >= 25 ? C.gold : ces >= 10 ? '#FF8C00' : C.red

  return (
    <div>
      {/* Timeline navigation */}
      <div style={{ display: 'flex', gap: 0, marginBottom: 24, background: C.card, borderRadius: 10, padding: 6, border: `1px solid ${C.border}` }}>
        {DEGRADATION_EVENTS.map((e, i) => (
          <button
            key={e.t}
            onClick={() => setActive(i)}
            style={{
              flex: 1, padding: '10px 8px', borderRadius: 8, cursor: 'pointer',
              border: `1px solid ${active === i ? e.color + '66' : 'transparent'}`,
              background: active === i ? e.color + '14' : 'transparent',
              transition: 'all 0.15s',
            }}
          >
            <div style={{ fontSize: 12, fontWeight: 800, color: active === i ? e.color : C.muted, fontFamily: 'monospace' }}>{e.t}</div>
            <div style={{ fontSize: 9, color: active === i ? e.color + 'AA' : C.gray, marginTop: 2, letterSpacing: '0.04em' }}>{e.status}</div>
          </button>
        ))}
      </div>

      {/* CES gauge */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
          <span style={{ fontSize: 11, color: C.muted }}>Continuity Eligibility Score (CES)</span>
          <span style={{ fontSize: 20, fontWeight: 800, color: barColor(ev.ces), fontFamily: 'monospace' }}>{ev.ces}.0</span>
        </div>
        <div style={{ height: 12, borderRadius: 6, background: 'rgba(255,255,255,0.06)', overflow: 'hidden', position: 'relative' }}>
          {/* Threshold markers */}
          {[10, 25, 50, 75].map(t => (
            <div key={t} style={{
              position: 'absolute', top: 0, bottom: 0, left: `${t}%`, width: 1,
              background: 'rgba(255,255,255,0.15)',
            }} />
          ))}
          <div style={{
            height: '100%', borderRadius: 6, transition: 'all 0.4s',
            width: barWidth(ev.ces),
            background: `linear-gradient(to right, ${barColor(ev.ces)}66, ${barColor(ev.ces)})`,
            boxShadow: `0 0 12px ${barColor(ev.ces)}44`,
          }} />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
          {['HALT', 'CRITICAL', 'WARNING', 'MONITORING', 'NOMINAL'].map((s, i) => {
            const colors = [C.red, '#FF8C00', C.gold, C.blue, C.green]
            return (
              <span key={s} style={{
                fontSize: 9, fontWeight: 700, color: ev.status === s ? colors[i] : C.gray,
                letterSpacing: '0.04em',
              }}>{s}</span>
            )
          })}
        </div>
      </div>

      {/* Event detail */}
      <div style={{
        display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12,
      }}>
        <div style={{ padding: '16px', borderRadius: 10, border: `1px solid ${ev.color}33`, background: ev.color + '08' }}>
          <div style={{ fontSize: 13, fontWeight: 800, color: ev.color, marginBottom: 8,
            fontFamily: "'Space Grotesk', 'Inter', sans-serif" }}>{ev.t} — {ev.label}</div>
          <p style={{ fontSize: 12, color: C.muted, lineHeight: 1.6, marginBottom: 10 }}>{ev.desc}</p>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            padding: '4px 12px', borderRadius: 20,
            background: ev.color + '18', border: `1px solid ${ev.color}44`,
          }}>
            <GlowDot color={ev.color} />
            <span style={{ fontSize: 11, fontWeight: 800, color: ev.color, letterSpacing: '0.08em' }}>{ev.status}</span>
          </div>
        </div>

        <div style={{ padding: '16px', borderRadius: 10, border: `1px solid ${C.border}`, background: C.card }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: C.muted, marginBottom: 8, letterSpacing: '0.08em' }}>EVENTS</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {ev.events.map(e => (
              <div key={e} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
                <div style={{ width: 4, height: 4, borderRadius: '50%', background: ev.color, flexShrink: 0 }} />
                <span style={{ color: C.text, fontFamily: 'monospace' }}>{e}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* RGC invariant annotation */}
      {active === 4 && (
        <div style={{
          marginTop: 12, padding: '10px 14px', borderRadius: 8,
          background: C.red + '08', border: `1px solid ${C.red}33`,
          fontSize: 11, color: C.muted,
        }}>
          <span style={{ color: C.red, fontWeight: 700 }}>RGC-INV-003 — HALT Propagation:</span>
          {' '}HALT on any session revokes all sibling sessions sharing the same chain_root_id.
          All artifacts from the halted chain are immediately promoted to COLD evidence tier (ADR-163 §4 — EMERGENCY_COLD).
        </div>
      )}
    </div>
  )
}

// ─── Diagram 5: Evidence Custody Lifecycle ────────────────────────────────────
const EVIDENCE_CLASSES = [
  { code: 'LEGAL',         color: C.gold,   label: 'Legal Evidence',           hot: '∞', warm: '—', cold: '∞ immutable', examples: 'decision_receipts, execution_receipts, udcl_control_receipts' },
  { code: 'PQC',           color: C.cyan,   label: 'PQC Chain',                hot: '∞', warm: '—', cold: '∞ immutable', examples: 'atf_delegations, atf_temporal_records, atf_domain_bridges' },
  { code: 'CONTRACT',      color: C.purple, label: 'Cross-Runtime Contract',   hot: '∞', warm: '—', cold: '∞ immutable', examples: 'CRGCs, governance_scope_authorizations' },
  { code: 'EXCEPTION',     color: C.red,    label: 'Exception Event',          hot: '∞', warm: '—', cold: '∞ immutable', examples: 'RCRs: HALT/CRITICAL/FRAGMENTATION, atf_continuity_escalations' },
  { code: 'TELEMETRY',     color: C.blue,   label: 'Runtime Telemetry',        hot: '90d', warm: '90–365d', cold: 'Aggregated', examples: 'RCRs: NOMINAL/MONITORING, avm_calibration_snapshots' },
  { code: 'SAMPLE',        color: '#6EE7B7', label: 'Continuity Sample',       hot: '30d', warm: 'Hourly agg', cold: 'Compressed', examples: 'atf_runtime_continuity NOMINAL/HEALTHY rows' },
  { code: 'SHADOW_NOMINAL',color: C.muted,  label: 'Shadow Nominal Event',     hot: '30d', warm: 'Hash only', cold: 'Compressed', examples: 'shadow_trade_events without veto/anomaly' },
  { code: 'OPS',           color: C.gray,   label: 'Operational Data',         hot: 'Active', warm: '90–365d', cold: 'Optional', examples: 'b2b_clients, book_leads, paper_trading_balances' },
]

const TIERS = [
  {
    id: 'HOT', label: 'HOT Tier', range: '0–90 days', color: C.green,
    storage: 'PostgreSQL (Railway)', access: 'Full read/write', indexes: 'Complete',
    desc: 'Active governance data. All evidence classes resident here during admission window.',
  },
  {
    id: 'WARM', label: 'WARM Tier', range: '90–365 days', color: C.gold,
    storage: 'PostgreSQL compressed', access: 'Read-only', indexes: 'Audit + hash lookup',
    desc: 'Compressed telemetry aggregates. Immutable classes never enter WARM.',
  },
  {
    id: 'COLD', label: 'COLD Tier', range: '365+ days / permanent', color: C.blue,
    storage: 'Object storage (Parquet)', access: 'Archival / offline', indexes: 'Hash-addressed',
    desc: 'Immutable append-only blocks. SHA-256 block chain. ML-DSA-65 signed. Offline verifiable.',
  },
]

function DiagramEvidenceLifecycle() {
  const [activeClass, setActiveClass] = useState<string | null>(null)

  return (
    <div>
      {/* Tier cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 24 }}>
        {TIERS.map(tier => (
          <div key={tier.id} style={{
            padding: '18px 16px', borderRadius: 12,
            border: `1px solid ${tier.color}33`, background: tier.color + '07',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
              <span style={{ fontSize: 14, fontWeight: 800, color: tier.color,
                fontFamily: "'Space Grotesk', 'Inter', sans-serif" }}>{tier.label}</span>
              <span style={{
                fontSize: 10, padding: '2px 8px', borderRadius: 10,
                background: tier.color + '18', color: tier.color, border: `1px solid ${tier.color}44`,
                fontWeight: 700,
              }}>{tier.range}</span>
            </div>
            <p style={{ fontSize: 11, color: C.muted, lineHeight: 1.5, marginBottom: 10 }}>{tier.desc}</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {[['Storage', tier.storage], ['Access', tier.access], ['Indexes', tier.indexes]].map(([k, v]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10 }}>
                  <span style={{ color: C.gray }}>{k}</span>
                  <span style={{ color: C.text, fontWeight: 600 }}>{v}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Evidence class table */}
      <div style={{ borderRadius: 10, border: `1px solid ${C.border}`, overflow: 'hidden' }}>
        {/* Header */}
        <div style={{
          display: 'grid', gridTemplateColumns: '140px 1fr 80px 100px 120px',
          padding: '8px 14px', background: C.surface,
          borderBottom: `1px solid ${C.border}`,
          fontSize: 10, fontWeight: 700, color: C.muted, letterSpacing: '0.08em',
        }}>
          <span>CLASS</span><span>EXAMPLES</span><span>HOT</span><span>WARM</span><span>COLD</span>
        </div>

        {EVIDENCE_CLASSES.map((ec, i) => (
          <div
            key={ec.code}
            onClick={() => setActiveClass(activeClass === ec.code ? null : ec.code)}
            style={{
              display: 'grid', gridTemplateColumns: '140px 1fr 80px 100px 120px',
              padding: '10px 14px', cursor: 'pointer',
              background: activeClass === ec.code ? ec.color + '0C' : i % 2 === 0 ? C.card : 'transparent',
              borderBottom: `1px solid ${C.border}22`,
              transition: 'background 0.12s', alignItems: 'center',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <GlowDot color={ec.color} />
              <span style={{ fontSize: 11, fontWeight: 700, color: ec.color, fontFamily: 'monospace' }}>{ec.code}</span>
            </div>
            <span style={{ fontSize: 11, color: C.muted, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{ec.examples}</span>
            <span style={{ fontSize: 11, fontWeight: 700, color: C.green, fontFamily: 'monospace' }}>{ec.hot}</span>
            <span style={{ fontSize: 11, fontWeight: ec.warm === '—' ? 400 : 700, color: ec.warm === '—' ? C.gray : C.gold, fontFamily: 'monospace' }}>{ec.warm}</span>
            <span style={{ fontSize: 11, fontWeight: 700, color: ec.cold.includes('immutable') ? C.cyan : C.blue, fontFamily: 'monospace' }}>{ec.cold}</span>
          </div>
        ))}
      </div>

      {/* ELR/EAP invariant bar */}
      <div style={{
        marginTop: 14, padding: '10px 14px', borderRadius: 8,
        background: 'rgba(0,229,255,0.04)', border: `1px solid ${C.cyan}22`,
        display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center',
      }}>
        {['ELR-INV-001', 'ELR-INV-002', 'ELR-INV-003', 'ELR-INV-004', 'EAP-INV-001–006'].map(inv => (
          <Pill key={inv} label={inv} color={C.cyan} />
        ))}
        <span style={{ fontSize: 11, color: C.muted }}>
          ATF-INV-006 preserved through all tier transitions.
        </span>
      </div>
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────
const DIAGRAMS = [
  {
    id: 'stack',     label: 'Runtime Legitimacy Stack',       adrs: ['ADR-156–163', 'RFC-ATF-1', 'RFC-ATF-2', 'RFC-ATF-3'],
    desc: 'Six-layer governance architecture. Every autonomous execution path traverses all layers.',
  },
  {
    id: 'chain',     label: 'Execution Legitimacy Chain',     adrs: ['ADR-028', 'ADR-157', 'ADR-159', 'ADR-163'],
    desc: 'How runtime legitimacy is constructed: from human authority root to immutable archive.',
  },
  {
    id: 'gpil',      label: 'Sovereign Runtime Divergence',   adrs: ['ADR-161'],
    desc: 'How sovereign runtimes maintain cryptographic interoperability while diverging on policy.',
  },
  {
    id: 'degradation', label: 'Runtime Authority Degradation', adrs: ['ADR-159', 'RFC-ATF-2'],
    desc: 'CES degradation timeline: from nominal authority to HALT and evidence archival.',
  },
  {
    id: 'evidence',  label: 'Evidence Custody Lifecycle',     adrs: ['ADR-162', 'ADR-163'],
    desc: 'Eight evidence classes across HOT/WARM/COLD tiers with immutability guarantees.',
  },
]

export default function ProtocolVisualizationPage() {
  const [active, setActive] = useState('stack')
  const current = DIAGRAMS.find(d => d.id === active)!

  return (
    <div style={{
      background: C.bg, minHeight: '100vh', color: C.text,
      fontFamily: "'Inter', -apple-system, sans-serif",
    }}>
      {/* Header */}
      <div style={{
        borderBottom: `1px solid ${C.border}`,
        padding: '18px clamp(16px, 4vw, 48px)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        position: 'sticky', top: 0, zIndex: 50,
        background: C.bg + 'E8',
        backdropFilter: 'blur(12px)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <a href="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 8 }}>
            <img src="/logo.png" alt="OMNIX" style={{ width: 26, height: 26, borderRadius: 4, objectFit: 'contain' }} />
            <span style={{ fontWeight: 800, fontSize: 16, color: C.gold, letterSpacing: '0.08em',
              fontFamily: "'Space Grotesk', 'Inter', sans-serif" }}>OMNIX</span>
          </a>
          <span style={{ color: C.gray }}>|</span>
          <span style={{ fontSize: 13, color: C.muted }}>Protocol Architecture</span>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <a href="/atf-standard" style={{
            fontSize: 12, color: C.cyan, border: `1px solid ${C.cyan}33`,
            borderRadius: 8, padding: '5px 14px', textDecoration: 'none',
          }}>ATF Standard</a>
          <a href="/atf-verify" style={{
            fontSize: 12, background: C.gold, color: '#05070B', fontWeight: 700,
            borderRadius: 8, padding: '5px 14px', textDecoration: 'none',
          }}>Verify Receipt</a>
        </div>
      </div>

      <div style={{ maxWidth: 1140, margin: '0 auto', padding: 'clamp(32px,5vw,64px) clamp(16px,4vw,48px)' }}>

        {/* Hero */}
        <div style={{ textAlign: 'center', marginBottom: 56 }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            background: C.cyan + '0E', border: `1px solid ${C.cyan}33`,
            borderRadius: 20, padding: '6px 16px', marginBottom: 24,
          }}>
            <GlowDot color={C.cyan} />
            <span style={{ fontSize: 11, fontWeight: 700, color: C.cyan, letterSpacing: '0.12em' }}>
              RUNTIME GOVERNANCE INFRASTRUCTURE
            </span>
          </div>

          <h1 style={{
            fontSize: 'clamp(28px, 5vw, 52px)', fontWeight: 900,
            letterSpacing: '-0.03em', lineHeight: 1.1, margin: '0 0 20px',
            fontFamily: "'Space Grotesk', 'Inter', sans-serif",
          }}>
            <span style={{ color: C.text }}>Protocol </span>
            <span style={{ color: C.cyan }}>Architecture</span>
          </h1>

          <p style={{ fontSize: 16, color: C.muted, maxWidth: 580, margin: '0 auto 28px', lineHeight: 1.7 }}>
            OMNIX is not an AI platform. It is runtime legitimacy infrastructure —
            a cryptographically verifiable authority layer for autonomous systems,
            operating at the exact moment execution occurs.
          </p>

          <div style={{ display: 'flex', justifyContent: 'center', gap: 8, flexWrap: 'wrap' }}>
            {[
              { label: '202 ADRs', color: C.gold },
              { label: '169 invariants', color: C.cyan },
              { label: 'ML-DSA-65 (FIPS 204)', color: C.purple },
              { label: 'Offline verifiable', color: C.green },
            ].map(({ label, color }) => <Pill key={label} label={label} color={color} />)}
          </div>
        </div>

        {/* Diagram selector */}
        <div style={{
          display: 'flex', gap: 8, marginBottom: 40, overflowX: 'auto', paddingBottom: 4,
        }}>
          {DIAGRAMS.map((d, i) => (
            <button
              key={d.id}
              onClick={() => setActive(d.id)}
              style={{
                flexShrink: 0, padding: '10px 16px', borderRadius: 10, cursor: 'pointer',
                border: `1px solid ${active === d.id ? C.cyan + '66' : C.border}`,
                background: active === d.id ? C.cyan + '0E' : C.card,
                transition: 'all 0.15s', textAlign: 'left',
              }}
            >
              <div style={{ fontSize: 10, fontWeight: 700, color: active === d.id ? C.cyan : C.gray,
                letterSpacing: '0.08em', marginBottom: 4 }}>DIAGRAM {i + 1}</div>
              <div style={{ fontSize: 13, fontWeight: 700, color: active === d.id ? C.text : C.muted,
                fontFamily: "'Space Grotesk', 'Inter', sans-serif", whiteSpace: 'nowrap' }}>{d.label}</div>
            </button>
          ))}
        </div>

        {/* Active diagram panel */}
        <div style={{
          borderRadius: 16, border: `1px solid ${C.border}`,
          background: C.surface, overflow: 'hidden',
        }}>
          {/* Panel header */}
          <div style={{
            padding: '20px 28px',
            borderBottom: `1px solid ${C.border}`,
            display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap',
          }}>
            <div>
              <div style={{ fontSize: 11, fontWeight: 700, color: C.muted, letterSpacing: '0.10em', marginBottom: 6 }}>
                DIAGRAM {DIAGRAMS.findIndex(d => d.id === active) + 1} OF 5
              </div>
              <h2 style={{
                fontSize: 'clamp(18px, 3vw, 26px)', fontWeight: 800, margin: 0,
                color: C.text, letterSpacing: '-0.02em',
                fontFamily: "'Space Grotesk', 'Inter', sans-serif",
              }}>{current.label}</h2>
              <p style={{ fontSize: 13, color: C.muted, marginTop: 6, lineHeight: 1.5 }}>{current.desc}</p>
            </div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', flexShrink: 0 }}>
              {current.adrs.map(a => <ADRBadge key={a} adr={a} />)}
            </div>
          </div>

          {/* Diagram content */}
          <div style={{ padding: 'clamp(20px, 3vw, 32px)' }}>
            {active === 'stack'       && <DiagramStack />}
            {active === 'chain'       && <DiagramChain />}
            {active === 'gpil'        && <DiagramGPIL />}
            {active === 'degradation' && <DiagramDegradation />}
            {active === 'evidence'    && <DiagramEvidenceLifecycle />}
          </div>
        </div>

        {/* Architectural References — RFC + ADR stacks separated */}
        <div style={{ marginTop: 48, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>

          {/* Foundational RFC Stack */}
          <div>
            <div style={{ fontSize: 10, fontWeight: 700, color: C.gold, letterSpacing: '0.12em', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ display: 'inline-block', width: 16, height: 1, background: C.gold, verticalAlign: 'middle' }} />
              FOUNDATIONAL RFC STACK
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                { adr: 'RFC-ATF-1', title: 'Agent Trust Fabric · ATF-INV-001–006', sub: 'Identity, delegation, MAR, PQC signing', color: C.gold },
                { adr: 'RFC-ATF-2', title: 'Runtime Governance Continuity · RGC-INV-001–008', sub: 'CES, temporal admissibility, RCR lifecycle', color: C.cyan },
                { adr: 'RFC-ATF-3', title: 'Forensic Evidence & Interoperability', sub: 'EAP, OEP, FEA, FVP · cross-runtime verification', color: C.purple },
              ].map(ref => (
                <div key={ref.adr} style={{
                  display: 'flex', alignItems: 'flex-start', gap: 12,
                  padding: '12px 14px', borderRadius: 8,
                  border: `1px solid ${ref.color}28`, background: ref.color + '07',
                }}>
                  <span style={{
                    fontSize: 10, fontWeight: 800, color: ref.color, fontFamily: 'monospace',
                    background: ref.color + '18', padding: '3px 8px', borderRadius: 6,
                    border: `1px solid ${ref.color}44`, flexShrink: 0, marginTop: 1,
                  }}>{ref.adr}</span>
                  <div>
                    <div style={{ fontSize: 12, color: C.text, fontWeight: 600, marginBottom: 2 }}>{ref.title}</div>
                    <div style={{ fontSize: 10, color: C.muted }}>{ref.sub}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Governance ADR Stack */}
          <div>
            <div style={{ fontSize: 10, fontWeight: 700, color: C.cyan, letterSpacing: '0.12em', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ display: 'inline-block', width: 16, height: 1, background: C.cyan, verticalAlign: 'middle' }} />
              GOVERNANCE ADR STACK
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                { adr: 'ADR-156', title: 'Agent Trust Fabric', color: C.cyan },
                { adr: 'ADR-157', title: 'Temporal Authority Admissibility', color: C.purple },
                { adr: 'ADR-158', title: 'Cross-Domain Trust Portability', color: C.blue },
                { adr: 'ADR-159', title: 'Runtime Governance Continuity', color: C.green },
                { adr: 'ADR-160', title: 'RCR Performance & Observability', color: C.cyan },
                { adr: 'ADR-161', title: 'Governance Policy Interoperability', color: C.purple },
                { adr: 'ADR-162', title: 'Evidence Lifecycle & Immutable Retention', color: C.gold },
                { adr: 'ADR-163', title: 'Immutable Evidence Archive Pipeline', color: C.blue },
              ].map(ref => (
                <div key={ref.adr} style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  padding: '9px 14px', borderRadius: 8,
                  border: `1px solid ${ref.color}18`, background: ref.color + '05',
                }}>
                  <span style={{
                    fontSize: 10, fontWeight: 800, color: ref.color, fontFamily: 'monospace',
                    background: ref.color + '14', padding: '2px 8px', borderRadius: 6,
                    border: `1px solid ${ref.color}30`, flexShrink: 0,
                  }}>{ref.adr}</span>
                  <span style={{ fontSize: 12, color: C.muted }}>{ref.title}</span>
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* Positioning footer */}
        <div style={{
          marginTop: 56, padding: '28px 32px', borderRadius: 16,
          border: `1px solid ${C.gold}22`,
          background: `linear-gradient(135deg, ${C.gold}06 0%, transparent 60%)`,
          textAlign: 'center',
        }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: C.gold, letterSpacing: '0.12em', marginBottom: 12 }}>
            OMNIX IS
          </div>
          <p style={{
            fontSize: 'clamp(15px, 2.5vw, 20px)', color: C.text, fontWeight: 600,
            lineHeight: 1.6, maxWidth: 680, margin: '0 auto 20px',
            fontFamily: "'Space Grotesk', 'Inter', sans-serif",
          }}>
            Runtime legitimacy infrastructure for autonomous systems.
            Not after execution. Not reconstructed later.
            At the exact moment authority is exercised —
            and preserved immutably afterward.
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: 10, flexWrap: 'wrap' }}>
            <a href="/atf-verify" style={{
              padding: '10px 24px', borderRadius: 10, fontSize: 13, fontWeight: 700,
              background: C.gold, color: '#05070B', textDecoration: 'none',
            }}>Verify a Receipt</a>
            <a href="/try" style={{
              padding: '10px 24px', borderRadius: 10, fontSize: 13, fontWeight: 700,
              border: `1px solid ${C.cyan}44`, color: C.cyan, textDecoration: 'none',
            }}>Live Sandbox</a>
            <a href="/atf-standard" style={{
              padding: '10px 24px', borderRadius: 10, fontSize: 13, fontWeight: 700,
              border: `1px solid ${C.border}`, color: C.muted, textDecoration: 'none',
            }}>ATF Standard</a>
          </div>
        </div>

      </div>
    </div>
  )
}
