/**
 * OMNIX Forensic Operations Demo — /forensic-operations
 * =======================================================
 * Five operational demos for institutional audiences:
 *   Demo A — Runtime Authority Degradation (CES simulation)
 *   Demo B — Cross-Runtime Governance Divergence (GPIL / ADR-161)
 *   Demo C — Immutable Archive Chain Verification (ADR-163)
 *   Demo D — Trust Anchor + EXTERNAL Issuer Verification (ADR-167)
 *   Demo E — Full Governance Replay: DR→TAR→RCR→Receipt→Archive (ADR-165)
 *
 * Harold Nunes — OMNIX QUANTUM LTD — May 2026
 */

import { useState, useRef, useCallback } from 'react'

// ─── Design system ────────────────────────────────────────────────────────────
const GOLD   = '#C9A227'
const NAVY   = '#060F1E'
const NAVY2  = '#0A1628'
const NAVY3  = '#0D1F35'
const BORDER = '#1a2d45'
const GREEN  = '#22c55e'
const RED    = '#ef4444'
const YELLOW = '#eab308'
const CYAN   = '#22d3ee'
const SLATE  = '#64748b'
const TEXT   = '#e2e8f0'
const MUTED  = '#94a3b8'

// ─── Shared atoms ─────────────────────────────────────────────────────────────
const Badge = ({ children, color = GOLD }: { children: React.ReactNode; color?: string }) => (
  <span style={{
    display: 'inline-block',
    padding: '2px 8px',
    borderRadius: 4,
    border: `1px solid ${color}40`,
    background: `${color}15`,
    color,
    fontSize: 11,
    fontFamily: 'monospace',
    fontWeight: 600,
    letterSpacing: '0.04em',
  }}>{children}</span>
)

const Tag = ({ label }: { label: string }) => (
  <span style={{
    padding: '2px 6px',
    borderRadius: 3,
    background: '#1e3a5f',
    color: MUTED,
    fontSize: 10,
    fontFamily: 'monospace',
  }}>{label}</span>
)

const Divider = () => (
  <div style={{ height: 1, background: BORDER, margin: '24px 0' }} />
)

const DemoShell = ({
  id, title, subtitle, adrs, children, running, onStart, onReset,
}: {
  id: string
  title: string
  subtitle: string
  adrs: string[]
  children: React.ReactNode
  running: boolean
  onStart: () => void
  onReset: () => void
}) => (
  <section id={id} style={{
    background: NAVY2,
    border: `1px solid ${BORDER}`,
    borderRadius: 12,
    overflow: 'hidden',
    marginBottom: 32,
  }}>
    {/* Header */}
    <div style={{
      background: NAVY3,
      borderBottom: `1px solid ${BORDER}`,
      padding: '20px 28px',
      display: 'flex',
      alignItems: 'flex-start',
      justifyContent: 'space-between',
      gap: 20,
      flexWrap: 'wrap',
    }}>
      <div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6 }}>
          <span style={{ color: GOLD, fontFamily: 'monospace', fontSize: 12, fontWeight: 700 }}>{id}</span>
          {adrs.map(a => <Tag key={a} label={a} />)}
        </div>
        <h3 style={{ margin: 0, color: TEXT, fontSize: 18, fontWeight: 700 }}>{title}</h3>
        <p style={{ margin: '4px 0 0', color: MUTED, fontSize: 13 }}>{subtitle}</p>
      </div>
      <div style={{ display: 'flex', gap: 10 }}>
        <button
          onClick={onReset}
          style={{
            padding: '8px 16px', borderRadius: 6,
            border: `1px solid ${BORDER}`, background: 'transparent',
            color: MUTED, fontSize: 13, cursor: 'pointer',
          }}
        >Reset</button>
        <button
          onClick={onStart}
          disabled={running}
          style={{
            padding: '8px 20px', borderRadius: 6,
            border: `1px solid ${running ? SLATE : GOLD}`,
            background: running ? `${SLATE}20` : `${GOLD}20`,
            color: running ? SLATE : GOLD,
            fontSize: 13, fontWeight: 600, cursor: running ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s',
          }}
        >{running ? '● Running…' : '▶ Run Demo'}</button>
      </div>
    </div>
    {/* Body */}
    <div style={{ padding: '24px 28px' }}>{children}</div>
  </section>
)

// ─── Demo A — Runtime Authority Degradation ───────────────────────────────────
type CESStage = 'NOMINAL' | 'MONITORING' | 'WARNING' | 'CRITICAL' | 'HALT'

interface CESSnapshot {
  time: number
  score: number
  stage: CESStage
  event: string
  temporal: number
  budget: number
  context: number
  integrity: number
}

const CES_COLOR: Record<CESStage, string> = {
  NOMINAL:    GREEN,
  MONITORING: CYAN,
  WARNING:    YELLOW,
  CRITICAL:   '#f97316',
  HALT:       RED,
}

const CES_THRESHOLDS = { NOMINAL: 75, MONITORING: 50, WARNING: 25, CRITICAL: 10, HALT: 0 }

function getCESStage(score: number): CESStage {
  if (score >= 75) return 'NOMINAL'
  if (score >= 50) return 'MONITORING'
  if (score >= 25) return 'WARNING'
  if (score >= 10) return 'CRITICAL'
  return 'HALT'
}

function computeCES(t: number, b: number, c: number, i: number) {
  return Math.max(0, Math.min(100, t * 0.3 + b * 0.3 + c * 0.2 + i * 0.2))
}

const DEMO_A_EVENTS: Array<{ at: number; event: string; delta: Partial<{ temporal: number; budget: number; context: number; integrity: number }> }> = [
  { at: 500,  event: 'Agent runtime initialized — CES NOMINAL', delta: {} },
  { at: 1500, event: 'Task batch started — budget consumption begins', delta: { budget: -8 } },
  { at: 2500, event: 'Temporal window 65% consumed', delta: { temporal: -12 } },
  { at: 3500, event: 'Context drift detected — CRGC divergence', delta: { context: -18 } },
  { at: 4500, event: 'Budget threshold breach → MONITORING', delta: { budget: -14 } },
  { at: 5500, event: 'Temporal authority reduced — TAR TTL expiring', delta: { temporal: -20 } },
  { at: 6200, event: 'AFG fragmentation elevated → WARNING', delta: { budget: -10, context: -8 } },
  { at: 7000, event: 'Integrity anomaly — receipt hash mismatch', delta: { integrity: -22 } },
  { at: 7800, event: 'CES → CRITICAL — authority degraded', delta: { temporal: -12, budget: -8 } },
  { at: 8500, event: 'RGC-INV-003: HALT triggered — emergency seal', delta: { temporal: -20, budget: -20 } },
]

function DemoA() {
  const [running, setRunning] = useState(false)
  const [snapshots, setSnapshots] = useState<CESSnapshot[]>([])
  const [current, setCurrent] = useState({ temporal: 95, budget: 95, context: 90, integrity: 92 })
  const timerRef = useRef<ReturnType<typeof setTimeout>[]>([])

  const reset = useCallback(() => {
    timerRef.current.forEach(clearTimeout)
    timerRef.current = []
    setRunning(false)
    setSnapshots([])
    setCurrent({ temporal: 95, budget: 95, context: 90, integrity: 92 })
  }, [])

  const start = useCallback(() => {
    if (running) return
    reset()
    setRunning(true)
    let state = { temporal: 95, budget: 95, context: 90, integrity: 92 }
    // Initial snapshot
    const initScore = computeCES(state.temporal, state.budget, state.context, state.integrity)
    setSnapshots([{ time: 0, score: initScore, stage: getCESStage(initScore), event: 'Runtime initialized', ...state }])
    DEMO_A_EVENTS.forEach(({ at, event, delta }, idx) => {
      const tid = setTimeout(() => {
        state = {
          temporal:  Math.max(0, state.temporal  + (delta.temporal  ?? 0)),
          budget:    Math.max(0, state.budget    + (delta.budget    ?? 0)),
          context:   Math.max(0, state.context   + (delta.context   ?? 0)),
          integrity: Math.max(0, state.integrity + (delta.integrity ?? 0)),
        }
        const score = computeCES(state.temporal, state.budget, state.context, state.integrity)
        const stage = getCESStage(score)
        setCurrent({ ...state })
        setSnapshots(prev => [...prev, { time: at, score, stage, event, ...state }])
        if (idx === DEMO_A_EVENTS.length - 1) setRunning(false)
      }, at)
      timerRef.current.push(tid)
    })
  }, [running, reset])

  const lastSnap = snapshots[snapshots.length - 1]
  const currentScore = lastSnap ? lastSnap.score : computeCES(current.temporal, current.budget, current.context, current.integrity)
  const currentStage = getCESStage(currentScore)
  const color = CES_COLOR[currentStage]

  const components = [
    { key: 'temporal',  label: 'Temporal',  value: current.temporal,  weight: 0.30 },
    { key: 'budget',    label: 'Budget',    value: current.budget,    weight: 0.30 },
    { key: 'context',   label: 'Context',   value: current.context,   weight: 0.20 },
    { key: 'integrity', label: 'Integrity', value: current.integrity, weight: 0.20 },
  ]

  return (
    <DemoShell
      id="DEMO-A"
      title="Runtime Authority Degradation"
      subtitle="Continuity Eligibility Score (CES) under simulated operational stress — RFC-ATF-2 §6"
      adrs={['ADR-159', 'RFC-ATF-2', 'RGC-INV-003']}
      running={running}
      onStart={start}
      onReset={reset}
    >
      {/* CES Gauge */}
      <div style={{ display: 'flex', gap: 28, flexWrap: 'wrap', marginBottom: 24 }}>
        <div style={{
          flex: '0 0 180px', display: 'flex', flexDirection: 'column', alignItems: 'center',
          background: NAVY3, border: `2px solid ${color}40`, borderRadius: 12, padding: '24px 16px',
        }}>
          <div style={{ fontSize: 11, color: MUTED, fontFamily: 'monospace', marginBottom: 12 }}>CES SCORE</div>
          <div style={{
            width: 100, height: 100, borderRadius: '50%',
            border: `4px solid ${color}`,
            background: `conic-gradient(${color} ${currentScore * 3.6}deg, #1a2d45 0deg)`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: `0 0 24px ${color}30`,
            transition: 'all 0.4s',
          }}>
            <div style={{ width: 80, height: 80, borderRadius: '50%', background: NAVY3, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span style={{ fontSize: 22, fontWeight: 700, color, fontFamily: 'monospace' }}>{currentScore.toFixed(0)}</span>
            </div>
          </div>
          <div style={{
            marginTop: 12, padding: '4px 12px', borderRadius: 6,
            background: `${color}20`, border: `1px solid ${color}50`,
            color, fontSize: 12, fontWeight: 700, fontFamily: 'monospace',
            transition: 'all 0.4s',
          }}>{currentStage}</div>
        </div>

        {/* Component bars */}
        <div style={{ flex: 1, minWidth: 240 }}>
          <div style={{ fontSize: 11, color: MUTED, fontFamily: 'monospace', marginBottom: 12 }}>
            CES FORMULA: T×0.3 + B×0.3 + C×0.2 + I×0.2
          </div>
          {components.map(c => {
            const barColor = c.value >= 75 ? GREEN : c.value >= 50 ? CYAN : c.value >= 25 ? YELLOW : RED
            return (
              <div key={c.key} style={{ marginBottom: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontSize: 12, color: MUTED, fontFamily: 'monospace' }}>{c.label} ({(c.weight * 100).toFixed(0)}%)</span>
                  <span style={{ fontSize: 12, color: barColor, fontFamily: 'monospace', fontWeight: 700 }}>{c.value.toFixed(0)}</span>
                </div>
                <div style={{ height: 8, background: '#1a2d45', borderRadius: 4, overflow: 'hidden' }}>
                  <div style={{
                    height: '100%', width: `${c.value}%`,
                    background: barColor, borderRadius: 4,
                    transition: 'width 0.4s ease, background 0.4s',
                  }} />
                </div>
              </div>
            )
          })}
          {/* Threshold ruler */}
          <div style={{ display: 'flex', gap: 6, marginTop: 12, flexWrap: 'wrap' }}>
            {Object.entries(CES_THRESHOLDS).map(([stage, val]) => (
              <span key={stage} style={{
                fontSize: 10, fontFamily: 'monospace', padding: '2px 6px', borderRadius: 3,
                background: `${CES_COLOR[stage as CESStage]}15`,
                border: `1px solid ${CES_COLOR[stage as CESStage]}30`,
                color: CES_COLOR[stage as CESStage],
              }}>{stage} ≥{val}</span>
            ))}
          </div>
        </div>
      </div>

      {/* Event log */}
      <div style={{
        background: NAVY, border: `1px solid ${BORDER}`, borderRadius: 8,
        padding: '12px 16px', maxHeight: 200, overflowY: 'auto',
        fontFamily: 'monospace', fontSize: 12,
      }}>
        <div style={{ color: MUTED, marginBottom: 8 }}>EVENT LOG — ADR-159 §4.2</div>
        {snapshots.length === 0 ? (
          <div style={{ color: SLATE }}>▸ Run demo to begin simulation</div>
        ) : [...snapshots].reverse().map((s, i) => (
          <div key={i} style={{
            display: 'flex', gap: 12, alignItems: 'center', marginBottom: 4,
            opacity: i === 0 ? 1 : 0.7,
          }}>
            <span style={{
              padding: '1px 6px', borderRadius: 3, fontSize: 10, fontWeight: 700,
              background: `${CES_COLOR[s.stage]}20`, color: CES_COLOR[s.stage],
              border: `1px solid ${CES_COLOR[s.stage]}40`, whiteSpace: 'nowrap',
            }}>{s.stage}</span>
            <span style={{ color: MUTED }}>{s.score.toFixed(1)}</span>
            <span style={{ color: TEXT, flex: 1 }}>{s.event}</span>
          </div>
        ))}
      </div>
    </DemoShell>
  )
}

// ─── Demo B — Cross-Runtime Governance Divergence ─────────────────────────────
interface RuntimeVerdict {
  runtime: string
  profile: string
  afg_limit: number
  ces_threshold: number
  drift_tolerance: number
  verdict: 'APPROVE' | 'CONDITIONAL' | 'REJECT'
  ces_score: number
  reason: string
  color: string
}

function DemoB() {
  const [running, setRunning] = useState(false)
  const [revealed, setRevealed] = useState<number>(0)
  const [receipt, setReceipt] = useState<null | { id: string; ces: number; drift: number; frag: number }>(null)

  const runtimes: RuntimeVerdict[] = [
    {
      runtime: 'RUNTIME-UAE',
      profile: 'STRICT',
      afg_limit: 0.70,
      ces_threshold: 80.0,
      drift_tolerance: 15,
      verdict: 'CONDITIONAL',
      ces_score: 77.4,
      reason: 'CES 77.4 < STRICT threshold 80.0 → CONDITIONAL with monitoring',
      color: YELLOW,
    },
    {
      runtime: 'RUNTIME-EU',
      profile: 'BALANCED',
      afg_limit: 0.80,
      ces_threshold: 75.0,
      drift_tolerance: 20,
      verdict: 'APPROVE',
      ces_score: 77.4,
      reason: 'CES 77.4 ≥ BALANCED threshold 75.0 → APPROVE',
      color: GREEN,
    },
    {
      runtime: 'RUNTIME-APAC',
      profile: 'THROUGHPUT',
      afg_limit: 0.88,
      ces_threshold: 60.0,
      drift_tolerance: 30,
      verdict: 'APPROVE',
      ces_score: 77.4,
      reason: 'CES 77.4 ≥ THROUGHPUT threshold 60.0 → APPROVE',
      color: GREEN,
    },
  ]

  const receiptData = {
    id: 'RCR-20260514-A7F3B2D1',
    ces: 77.4,
    drift: 17.2,
    frag: 0.78,
  }

  const reset = () => {
    setRunning(false)
    setRevealed(0)
    setReceipt(null)
  }

  const start = () => {
    if (running) return
    reset()
    setRunning(true)
    setTimeout(() => setReceipt(receiptData), 400)
    runtimes.forEach((_, i) => {
      setTimeout(() => {
        setRevealed(i + 1)
        if (i === runtimes.length - 1) setRunning(false)
      }, 900 + i * 800)
    })
  }

  const VERDICT_COLOR: Record<string, string> = { APPROVE: GREEN, CONDITIONAL: YELLOW, REJECT: RED }

  return (
    <DemoShell
      id="DEMO-B"
      title="Cross-Runtime Governance Divergence"
      subtitle="Same ML-DSA-65 receipt, cryptographically valid across all runtimes — different governance conclusions (ADR-161 §3)"
      adrs={['ADR-161', 'RFC-ATF-2 §21', 'GPIL']}
      running={running}
      onStart={start}
      onReset={reset}
    >
      {/* Receipt */}
      {receipt ? (
        <div style={{
          background: NAVY3, border: `1px solid ${GOLD}40`, borderRadius: 8,
          padding: '14px 18px', marginBottom: 24, fontFamily: 'monospace',
        }}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 8 }}>
            <Badge>RCR</Badge>
            <Badge color={GREEN}>PQC-VALID</Badge>
            <Badge color={CYAN}>ML-DSA-65 VERIFIED</Badge>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 10 }}>
            {[
              { l: 'Receipt ID', v: receipt.id },
              { l: 'CES Score', v: receipt.ces.toFixed(1) },
              { l: 'Context Drift', v: `${receipt.drift.toFixed(1)}%` },
              { l: 'AFG Fragmentation', v: receipt.frag.toFixed(2) },
            ].map(({ l, v }) => (
              <div key={l}>
                <div style={{ fontSize: 10, color: SLATE }}>{l}</div>
                <div style={{ fontSize: 13, color: TEXT, fontWeight: 600 }}>{v}</div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 10, fontSize: 11, color: MUTED }}>
            ↑ Cryptographic validity: IDENTICAL across all runtimes (ATF-INV-006)
          </div>
        </div>
      ) : (
        <div style={{
          background: NAVY3, border: `1px solid ${BORDER}`, borderRadius: 8,
          padding: '24px', textAlign: 'center', color: SLATE, fontFamily: 'monospace',
          marginBottom: 24, fontSize: 13,
        }}>▸ Run demo to broadcast receipt to sovereign runtimes</div>
      )}

      {/* Runtime verdicts */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 16 }}>
        {runtimes.map((rt, i) => {
          const isVisible = revealed > i
          const vColor = VERDICT_COLOR[rt.verdict] || MUTED
          return (
            <div key={rt.runtime} style={{
              background: NAVY3,
              border: `1px solid ${isVisible ? rt.color + '40' : BORDER}`,
              borderRadius: 10, padding: '18px',
              opacity: isVisible ? 1 : 0.3,
              transition: 'all 0.5s',
              transform: isVisible ? 'none' : 'translateY(8px)',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                <div>
                  <div style={{ fontSize: 12, fontWeight: 700, color: TEXT, fontFamily: 'monospace' }}>{rt.runtime}</div>
                  <div style={{ fontSize: 11, color: MUTED }}>{rt.profile} PROFILE</div>
                </div>
                {isVisible && (
                  <div style={{
                    padding: '4px 10px', borderRadius: 6, fontSize: 12, fontWeight: 700,
                    background: `${vColor}20`, border: `1px solid ${vColor}50`, color: vColor,
                    fontFamily: 'monospace', alignSelf: 'flex-start',
                  }}>{rt.verdict}</div>
                )}
              </div>
              <div style={{ fontSize: 11, fontFamily: 'monospace' }}>
                {[
                  { l: 'AFG Limit', v: rt.afg_limit.toFixed(2) },
                  { l: 'CES Threshold', v: rt.ces_threshold.toFixed(1) },
                  { l: 'Drift Tolerance', v: `${rt.drift_tolerance}%` },
                ].map(({ l, v }) => (
                  <div key={l} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ color: SLATE }}>{l}</span>
                    <span style={{ color: TEXT }}>{v}</span>
                  </div>
                ))}
              </div>
              {isVisible && (
                <div style={{
                  marginTop: 10, padding: '8px', borderRadius: 6,
                  background: `${vColor}10`, border: `1px solid ${vColor}20`,
                  fontSize: 11, color: MUTED, fontFamily: 'monospace', lineHeight: 1.5,
                }}>{rt.reason}</div>
              )}
            </div>
          )
        })}
      </div>
      {revealed === runtimes.length && (
        <div style={{
          marginTop: 20, padding: '12px 16px', background: `${CYAN}10`,
          border: `1px solid ${CYAN}30`, borderRadius: 8, fontSize: 13, color: MUTED,
        }}>
          <span style={{ color: CYAN, fontWeight: 700 }}>GPIL Conclusion: </span>
          Divergence is protocol-compliant. All runtimes verified the same ML-DSA-65 signature
          (cryptographic interoperability ✓). Policy divergence (governance interoperability) is
          an intended property of the sovereign runtime model — not a defect. <Badge color={CYAN}>ADR-161 §3</Badge>
        </div>
      )}
    </DemoShell>
  )
}

// ─── Demo C — Immutable Archive Chain Verification ────────────────────────────
interface ArchiveBlock {
  block_id: string
  predecessor_hash: string
  canonical_hash: string
  artifact_count: number
  classes: string[]
  tier: 'HOT' | 'WARM' | 'COLD'
  state: 'pending' | 'verifying' | 'verified' | 'error'
  seal_trigger: string
}

function DemoC() {
  const [running, setRunning] = useState(false)
  const [blocks, setBlocks] = useState<ArchiveBlock[]>([])
  const [ccs, setCcs] = useState<number | null>(null)
  const [verdict, setVerdict] = useState<string | null>(null)

  const chainData: ArchiveBlock[] = [
    {
      block_id: 'OMNIX-BLOCK-20260112-000001',
      predecessor_hash: '0'.repeat(64),
      canonical_hash: 'a3f7c2b9e4d1f8a6c5b3e9d7f2a8c4b6e1f9a3d7c2b5f8a1e4d6c9b2f5a8d3e6',
      artifact_count: 847,
      classes: ['LEGAL', 'PQC', 'CONTRACT'],
      tier: 'COLD',
      state: 'pending',
      seal_trigger: 'scheduler',
    },
    {
      block_id: 'OMNIX-BLOCK-20260213-000001',
      predecessor_hash: 'a3f7c2b9e4d1f8a6c5b3e9d7f2a8c4b6e1f9a3d7c2b5f8a1e4d6c9b2f5a8d3e6',
      canonical_hash: 'b8e2d4f6a1c9e3b7d5f2a8c6e4b1d9f3a7c5e8b2d6f4a9c3e1b5d7f9a2c8e4b6',
      artifact_count: 1203,
      classes: ['LEGAL', 'TELEMETRY', 'EXCEPTION'],
      tier: 'COLD',
      state: 'pending',
      seal_trigger: 'scheduler',
    },
    {
      block_id: 'OMNIX-BLOCK-20260314-000001',
      predecessor_hash: 'b8e2d4f6a1c9e3b7d5f2a8c6e4b1d9f3a7c5e8b2d6f4a9c3e1b5d7f9a2c8e4b6',
      canonical_hash: 'c9f3e7a2d5b8f1e4c7a3b9d6f2e8c4a7d1f5b3e9c6a2f8d4b7e1c5a9f3d7b2e6',
      artifact_count: 2011,
      classes: ['LEGAL', 'PQC', 'OPS'],
      tier: 'COLD',
      state: 'pending',
      seal_trigger: 'halt_event',
    },
    {
      block_id: 'OMNIX-BLOCK-20260415-000001',
      predecessor_hash: 'c9f3e7a2d5b8f1e4c7a3b9d6f2e8c4a7d1f5b3e9c6a2f8d4b7e1c5a9f3d7b2e6',
      canonical_hash: 'd2a8e4f9c1b5d7e3a9f6b2c8e5a1d4f8b6c3e7a2d9f1b5e8c4a7d3f6b9e2c5a8',
      artifact_count: 1587,
      classes: ['CONTRACT', 'TELEMETRY', 'SAMPLE'],
      tier: 'WARM',
      state: 'pending',
      seal_trigger: 'scheduler',
    },
  ]

  const reset = () => {
    setRunning(false)
    setBlocks([])
    setCcs(null)
    setVerdict(null)
  }

  const start = () => {
    if (running) return
    reset()
    setRunning(true)

    // Show blocks first
    setTimeout(() => setBlocks(chainData.map(b => ({ ...b, state: 'pending' }))), 200)

    // Verify each block sequentially
    chainData.forEach((_, i) => {
      setTimeout(() => {
        setBlocks(prev => prev.map((b, j) =>
          j === i ? { ...b, state: 'verifying' } : b
        ))
      }, 600 + i * 1000)

      setTimeout(() => {
        setBlocks(prev => prev.map((b, j) =>
          j === i ? { ...b, state: 'verified' } : b
        ))
        if (i === chainData.length - 1) {
          setCcs(98.7)
          setVerdict('PASS')
          setRunning(false)
        }
      }, 1000 + i * 1000)
    })
  }

  const TIER_COLOR: Record<string, string> = { HOT: RED, WARM: YELLOW, COLD: CYAN }
  const STATE_COLOR: Record<string, string> = {
    pending:   SLATE,
    verifying: YELLOW,
    verified:  GREEN,
    error:     RED,
  }

  return (
    <DemoShell
      id="DEMO-C"
      title="Immutable Archive Chain Verification"
      subtitle="COLD block chain reconstruction — predecessor hash linkage, Merkle root validation, PQC signature check (EAP-INV-001–006)"
      adrs={['ADR-163', 'ADR-165', 'EAP-INV-003']}
      running={running}
      onStart={start}
      onReset={reset}
    >
      {blocks.length === 0 ? (
        <div style={{
          textAlign: 'center', color: SLATE, fontFamily: 'monospace', fontSize: 13,
          padding: '24px', background: NAVY3, borderRadius: 8, border: `1px solid ${BORDER}`,
        }}>▸ Run demo to load and verify the COLD archive chain</div>
      ) : (
        <>
          {/* Chain visualization */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 20 }}>
            {blocks.map((b, i) => {
              const stColor = STATE_COLOR[b.state]
              const tierColor = TIER_COLOR[b.tier]
              return (
                <div key={b.block_id}>
                  {/* Predecessor link */}
                  {i > 0 && (
                    <div style={{
                      marginLeft: 24, height: 16, width: 2,
                      background: blocks[i - 1].state === 'verified' ? GREEN : BORDER,
                      transition: 'background 0.4s',
                    }} />
                  )}
                  <div style={{
                    background: NAVY3,
                    border: `1px solid ${stColor}40`,
                    borderRadius: 8, padding: '12px 16px',
                    transition: 'all 0.3s',
                    boxShadow: b.state === 'verifying' ? `0 0 12px ${YELLOW}20` : 'none',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
                      <div style={{ fontFamily: 'monospace' }}>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 4 }}>
                          <span style={{ color: TEXT, fontWeight: 600, fontSize: 13 }}>{b.block_id}</span>
                          {b.seal_trigger === 'halt_event' && <Badge color={RED}>HALT-TRIGGERED</Badge>}
                        </div>
                        <div style={{ fontSize: 11, color: MUTED }}>
                          Artifacts: {b.artifact_count.toLocaleString()} ·{' '}
                          {b.classes.map(c => (
                            <span key={c} style={{ marginRight: 4, color: IMMUTABLE_CLASS_COLOR(c) }}>{c}</span>
                          ))}
                        </div>
                        <div style={{ fontSize: 11, color: SLATE, fontFamily: 'monospace', marginTop: 4 }}>
                          {b.canonical_hash.substring(0, 20)}…{b.canonical_hash.slice(-12)}
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <span style={{
                          fontSize: 11, fontFamily: 'monospace', padding: '2px 8px', borderRadius: 4,
                          background: `${tierColor}15`, border: `1px solid ${tierColor}40`, color: tierColor,
                        }}>{b.tier}</span>
                        <span style={{
                          fontSize: 12, fontFamily: 'monospace', padding: '4px 10px', borderRadius: 6,
                          background: `${stColor}15`, border: `1px solid ${stColor}40`, color: stColor,
                          fontWeight: 700, transition: 'all 0.3s',
                          boxShadow: b.state === 'verifying' ? `0 0 8px ${stColor}40` : 'none',
                        }}>
                          {b.state === 'verifying' ? '⟳ VERIFYING' :
                           b.state === 'verified'  ? '✓ VERIFIED' :
                           b.state === 'error'     ? '✗ ERROR' : '○ PENDING'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Chain Completeness Score */}
          {ccs !== null && verdict && (
            <div style={{
              background: NAVY3, border: `2px solid ${GREEN}40`, borderRadius: 10,
              padding: '16px 20px', display: 'flex', gap: 20, alignItems: 'center', flexWrap: 'wrap',
            }}>
              <div style={{ textAlign: 'center', minWidth: 80 }}>
                <div style={{ fontSize: 28, fontWeight: 700, color: GREEN, fontFamily: 'monospace' }}>{ccs}</div>
                <div style={{ fontSize: 10, color: MUTED }}>CCS SCORE</div>
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', gap: 8, marginBottom: 6 }}>
                  <Badge color={GREEN}>VERDICT: {verdict}</Badge>
                  <Badge color={CYAN}>EAP-INV-003 ✓</Badge>
                  <Badge color={CYAN}>EAP-INV-005 ✓</Badge>
                </div>
                <div style={{ fontSize: 12, color: MUTED }}>
                  {blocks.length} blocks verified · {blocks.reduce((a, b) => a + b.artifact_count, 0).toLocaleString()} total artifacts ·
                  Hash chain intact · All predecessor links validated · PQC signature coverage checked
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </DemoShell>
  )
}

function IMMUTABLE_CLASS_COLOR(cls: string): string {
  const map: Record<string, string> = {
    LEGAL: GOLD, PQC: CYAN, CONTRACT: '#a78bfa', EXCEPTION: RED,
    TELEMETRY: MUTED, SAMPLE: SLATE, OPS: '#64748b', SHADOW_NOMINAL: SLATE,
  }
  return map[cls] || MUTED
}

// ─── Demo D — Trust Anchor + EXTERNAL Verification ────────────────────────────
interface VerificationChannel {
  name: string
  method: string
  result: 'OMNIX_PLATFORM' | 'EXTERNAL' | null
  fingerprint: string | null
  latency: number
  state: 'idle' | 'running' | 'done'
}

function DemoD() {
  const [running, setRunning] = useState(false)
  const [channels, setChannels] = useState<VerificationChannel[]>([])
  const [scenario, setScenario] = useState<'platform' | 'external'>('platform')

  const platformFP = 'sha256:3a8f2c7b9d4e1f6a5c8b2e9d7f4a1c6b8e3f7a2d5b9c4e8f1a6d3b7c2e5f9a4d'
  const externalFP = 'sha256:7f1d4b9c2e6a8f3d5b7e2c9a4f8d1b6e3a7c5f9b2d8e4a1f6c3b8d5e7f2a9c4'

  const buildChannels = (s: 'platform' | 'external'): VerificationChannel[] => {
    const fp = s === 'platform' ? platformFP : externalFP
    const result = s === 'platform' ? 'OMNIX_PLATFORM' as const : 'EXTERNAL' as const
    return [
      {
        name: 'HTTP — Platform Key Registry',
        method: 'GET /api/forensic/platform-key',
        result: null, fingerprint: null, latency: 0,
        state: 'idle',
      },
      {
        name: 'OEP Package — KEYS/public_key.b64',
        method: 'sha256(decode(KEYS/public_key.b64))',
        result: null, fingerprint: null, latency: 0,
        state: 'idle',
      },
      {
        name: 'DNS TXT — _omnix-key.omnixquantum.net',
        method: 'dig TXT _omnix-key.omnixquantum.net',
        result: null, fingerprint: null, latency: 0,
        state: 'idle',
      },
    ].map(c => ({ ...c, _fp: fp, _result: result })) as VerificationChannel[]
  }

  const reset = () => {
    setRunning(false)
    setChannels([])
  }

  const start = () => {
    if (running) return
    reset()
    setRunning(true)
    const base = buildChannels(scenario)
    setChannels(base.map(c => ({ ...c, state: 'idle' })))

    const latencies = [320, 180, 520]
    base.forEach((_c, i) => {
      setTimeout(() => {
        setChannels(prev => prev.map((ch, j) => j === i ? { ...ch, state: 'running' } : ch))
      }, 300 + i * 200)
      setTimeout(() => {
        setChannels(prev => prev.map((ch, j) => j === i ? {
          ...ch,
          state: 'done',
          result: scenario === 'platform' ? 'OMNIX_PLATFORM' : 'EXTERNAL',
          fingerprint: scenario === 'platform' ? platformFP : externalFP,
          latency: latencies[i],
        } : ch))
        if (i === base.length - 1) setRunning(false)
      }, 300 + i * 200 + latencies[i])
    })
  }

  const TRUST_COLOR: Record<string, string> = {
    OMNIX_PLATFORM: GREEN,
    EXTERNAL: YELLOW,
  }

  return (
    <DemoShell
      id="DEMO-D"
      title="Trust Anchor + EXTERNAL Issuer Verification"
      subtitle="Three-channel fingerprint comparison — OMNIX_PLATFORM vs EXTERNAL key classification (ADR-167 / FVP-INV-007)"
      adrs={['ADR-167', 'FVP-INV-007', 'FEA-INV-001']}
      running={running}
      onStart={start}
      onReset={reset}
    >
      {/* Scenario selector */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
        {(['platform', 'external'] as const).map(s => (
          <button
            key={s}
            onClick={() => { if (!running) { setScenario(s); reset() } }}
            disabled={running}
            style={{
              padding: '8px 16px', borderRadius: 8, cursor: running ? 'not-allowed' : 'pointer',
              border: `1px solid ${scenario === s ? GOLD : BORDER}`,
              background: scenario === s ? `${GOLD}20` : 'transparent',
              color: scenario === s ? GOLD : MUTED, fontSize: 13, fontWeight: 600,
            }}
          >
            {s === 'platform' ? 'OMNIX_PLATFORM key' : 'EXTERNAL key (different signer)'}
          </button>
        ))}
      </div>

      {channels.length === 0 ? (
        <div style={{
          textAlign: 'center', color: SLATE, fontFamily: 'monospace', fontSize: 13,
          padding: '24px', background: NAVY3, borderRadius: 8, border: `1px solid ${BORDER}`,
        }}>▸ Select scenario and run demo</div>
      ) : (
        <>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 20 }}>
            {channels.map((ch, i) => {
              const tc = ch.result ? TRUST_COLOR[ch.result] || MUTED : MUTED
              return (
                <div key={i} style={{
                  background: NAVY3, border: `1px solid ${ch.state === 'done' ? tc + '40' : BORDER}`,
                  borderRadius: 8, padding: '14px 18px',
                  transition: 'all 0.3s',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 700, color: TEXT, marginBottom: 4 }}>{ch.name}</div>
                      <div style={{ fontSize: 11, fontFamily: 'monospace', color: MUTED }}>{ch.method}</div>
                    </div>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      {ch.state === 'running' && (
                        <span style={{ fontSize: 11, color: YELLOW, fontFamily: 'monospace' }}>⟳ querying…</span>
                      )}
                      {ch.state === 'done' && ch.result && (
                        <>
                          <span style={{ fontSize: 10, color: MUTED }}>{ch.latency}ms</span>
                          <span style={{
                            padding: '4px 10px', borderRadius: 6, fontSize: 11, fontWeight: 700,
                            background: `${tc}20`, border: `1px solid ${tc}50`, color: tc,
                            fontFamily: 'monospace',
                          }}>{ch.result}</span>
                        </>
                      )}
                    </div>
                  </div>
                  {ch.state === 'done' && ch.fingerprint && (
                    <div style={{
                      marginTop: 10, fontSize: 11, fontFamily: 'monospace', color: SLATE,
                      background: NAVY, padding: '6px 10px', borderRadius: 4, wordBreak: 'break-all',
                    }}>{ch.fingerprint}</div>
                  )}
                </div>
              )
            })}
          </div>

          {channels.every(c => c.state === 'done') && (
            <div style={{
              background: NAVY3,
              border: `2px solid ${scenario === 'platform' ? GREEN : YELLOW}40`,
              borderRadius: 10, padding: '16px 20px',
            }}>
              <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                <Badge color={scenario === 'platform' ? GREEN : YELLOW}>
                  {scenario === 'platform' ? 'OMNIX_PLATFORM — Highest Trust' : 'EXTERNAL — Cryptographically Valid, Non-Platform'}
                </Badge>
              </div>
              <div style={{ fontSize: 12, color: MUTED, lineHeight: 1.6 }}>
                {scenario === 'platform'
                  ? 'All three channels return matching fingerprint. The OEP signing key is the official OMNIX QUANTUM LTD platform key. Highest institutional trust level — OMNIX_PLATFORM (ADR-167 §2).'
                  : 'OEP key fingerprint does not match the platform registry. The evidence package was signed by a third-party key. Cryptographic validity ✓ — platform endorsement ✗. Trust level: EXTERNAL (ADR-167 §3).'}
              </div>
            </div>
          )}
        </>
      )}
    </DemoShell>
  )
}

// ─── Demo E — Full Governance Replay ──────────────────────────────────────────
type ReplayStep = {
  id: string
  artifact: string
  description: string
  invariant: string
  fields: Array<{ k: string; v: string }>
  color: string
}

function DemoE() {
  const [running, setRunning] = useState(false)
  const [visibleSteps, setVisibleSteps] = useState(0)
  const [activeStep, setActiveStep] = useState<number | null>(null)

  const steps: ReplayStep[] = [
    {
      id: 'STEP-1',
      artifact: 'Agent Identity Receipt (AIR)',
      description: 'Human operator registers agent identity — root of the ATF chain',
      invariant: 'ATF-INV-006 (offline verifiability)',
      color: GOLD,
      fields: [
        { k: 'agent_id',   v: 'AGT-UAE-20260514-A7F3' },
        { k: 'tier',       v: 'TIER-2 (Autonomous)' },
        { k: 'issued_by',  v: 'HUMAN-ROOT-001' },
        { k: 'pqc_alg',   v: 'ML-DSA-65 (FIPS 204)' },
      ],
    },
    {
      id: 'STEP-2',
      artifact: 'Delegation Receipt (DR)',
      description: 'Authority delegated from human operator to agent — monotonic reduction enforced',
      invariant: 'ATF-INV-001 (authority never expands)',
      color: '#818cf8',
      fields: [
        { k: 'delegator',          v: 'HUMAN-ROOT-001' },
        { k: 'delegatee',          v: 'AGT-UAE-20260514-A7F3' },
        { k: 'authority_granted',  v: '0.65 (≤ delegator 1.0)' },
        { k: 'scope',              v: 'credit.approve, credit.monitor' },
      ],
    },
    {
      id: 'STEP-3',
      artifact: 'Temporal Admissibility Record (TAR)',
      description: 'Decision session bounded — temporal window and expiry enforced',
      invariant: 'TAR-INV-001 (no expired session executes)',
      color: CYAN,
      fields: [
        { k: 'session_id',       v: 'SES-20260514-B9C2' },
        { k: 'valid_from',       v: '2026-05-14T10:00:00Z' },
        { k: 'valid_until',      v: '2026-05-14T11:00:00Z' },
        { k: 'ttl_seconds',      v: '3600 (≤ RC_TTL_MAX)' },
      ],
    },
    {
      id: 'STEP-4',
      artifact: 'Runtime Continuity Record (RCR)',
      description: 'Runtime session scored — CES computed and recorded for forensic replay',
      invariant: 'RGC-INV-001 (CES monotonically bounded)',
      color: GREEN,
      fields: [
        { k: 'ces_score',     v: '83.2 (NOMINAL)' },
        { k: 'temporal_comp', v: '88.0 × 0.30' },
        { k: 'budget_comp',   v: '84.0 × 0.30' },
        { k: 'context_comp',  v: '78.0 × 0.20' },
        { k: 'integrity_comp',v: '75.0 × 0.20' },
      ],
    },
    {
      id: 'STEP-5',
      artifact: 'Governance Receipt (RC)',
      description: 'Final governance decision — PQC signed, content-hashed, written to HOT tier',
      invariant: 'RGC-INV-004 (every decision receipt-backed)',
      color: GOLD,
      fields: [
        { k: 'receipt_id',      v: 'OMNIX-FIN-B7C3A9F2D1E5' },
        { k: 'decision',        v: 'APPROVED' },
        { k: 'content_hash',    v: 'sha256:3a8f…d3e6' },
        { k: 'pqc_signature',   v: 'ML-DSA-65 (3293 bytes)' },
        { k: 'tier',            v: 'HOT (0-90 days)' },
      ],
    },
    {
      id: 'STEP-6',
      artifact: 'COLD Archive Block',
      description: 'Receipt sealed into immutable COLD block — chain link established, OEP generated',
      invariant: 'EAP-INV-003 (unbroken hash chain)',
      color: CYAN,
      fields: [
        { k: 'block_id',          v: 'OMNIX-BLOCK-20270115-000847' },
        { k: 'artifact_count',    v: '1,247' },
        { k: 'merkle_root',       v: 'sha256:b8e2…b6e4' },
        { k: 'predecessor_hash',  v: 'sha256:a3f7…e6d3' },
        { k: 'pqc_signature',     v: 'ML-DSA-65 — OMNIX_PLATFORM' },
      ],
    },
  ]

  const reset = () => {
    setRunning(false)
    setVisibleSteps(0)
    setActiveStep(null)
  }

  const start = () => {
    if (running) return
    reset()
    setRunning(true)
    steps.forEach((_, i) => {
      setTimeout(() => {
        setActiveStep(i)
        setVisibleSteps(i + 1)
        if (i === steps.length - 1) {
          setActiveStep(null)
          setRunning(false)
        }
      }, 400 + i * 900)
    })
  }

  return (
    <DemoShell
      id="DEMO-E"
      title="Full Governance Replay: DR → TAR → RCR → Receipt → Archive"
      subtitle="End-to-end pipeline replay from human authority root to immutable COLD block — every artifact PQC-signed and independently verifiable"
      adrs={['ADR-156', 'ADR-157', 'ADR-159', 'ADR-163', 'ADR-165']}
      running={running}
      onStart={start}
      onReset={reset}
    >
      {visibleSteps === 0 ? (
        <div style={{
          textAlign: 'center', color: SLATE, fontFamily: 'monospace', fontSize: 13,
          padding: '32px', background: NAVY3, borderRadius: 8, border: `1px solid ${BORDER}`,
        }}>▸ Run demo to replay the complete governance pipeline</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
          {steps.slice(0, visibleSteps).map((step, i) => (
            <div key={step.id} style={{ display: 'flex', gap: 0 }}>
              {/* Spine */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 48, flexShrink: 0 }}>
                <div style={{
                  width: 36, height: 36, borderRadius: '50%',
                  background: activeStep === i ? `${step.color}40` : `${step.color}20`,
                  border: `2px solid ${step.color}`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 12, fontWeight: 700, color: step.color, fontFamily: 'monospace',
                  boxShadow: activeStep === i ? `0 0 16px ${step.color}50` : 'none',
                  transition: 'all 0.3s', flexShrink: 0, marginTop: 10,
                }}>{i + 1}</div>
                {i < steps.length - 1 && (
                  <div style={{
                    flex: 1, width: 2, background: i < visibleSteps - 1 ? step.color + '60' : BORDER,
                    minHeight: 16, transition: 'background 0.4s',
                  }} />
                )}
              </div>
              {/* Card */}
              <div style={{
                flex: 1, marginBottom: 10, marginLeft: 12,
                background: NAVY3,
                border: `1px solid ${activeStep === i ? step.color + '50' : BORDER}`,
                borderRadius: 8, padding: '12px 16px',
                transition: 'all 0.3s',
                boxShadow: activeStep === i ? `0 0 12px ${step.color}20` : 'none',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, flexWrap: 'wrap', gap: 8 }}>
                  <div>
                    <span style={{ fontSize: 11, color: SLATE, fontFamily: 'monospace', marginRight: 8 }}>{step.id}</span>
                    <span style={{ fontSize: 14, fontWeight: 700, color: TEXT }}>{step.artifact}</span>
                  </div>
                  <Badge color={step.color}>{step.invariant}</Badge>
                </div>
                <div style={{ fontSize: 12, color: MUTED, marginBottom: 8 }}>{step.description}</div>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: '4px 16px',
                  fontFamily: 'monospace', fontSize: 11,
                }}>
                  {step.fields.map(({ k, v }) => (
                    <div key={k} style={{ display: 'flex', gap: 8 }}>
                      <span style={{ color: SLATE, minWidth: 120 }}>{k}</span>
                      <span style={{ color: TEXT }}>{v}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {visibleSteps === steps.length && (
        <div style={{
          marginTop: 16, padding: '16px 20px',
          background: `${GREEN}10`, border: `2px solid ${GREEN}40`, borderRadius: 10,
        }}>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 8 }}>
            <Badge color={GREEN}>PIPELINE COMPLETE</Badge>
            <Badge color={CYAN}>EAP-INV-005 ✓ Offline Reconstructable</Badge>
            <Badge color={GOLD}>ATF-INV-006 ✓ PQC Verifiable</Badge>
            <Badge color={GREEN}>RGC-INV-004 ✓ Receipt-Backed</Badge>
          </div>
          <div style={{ fontSize: 12, color: MUTED, lineHeight: 1.6 }}>
            Every artifact in this chain — AIR, DR, TAR, RCR, RC, COLD Block — carries an
            ML-DSA-65 (Dilithium-3, FIPS 204) signature. Any third party with the platform
            public key can verify the complete chain offline without OMNIX platform access,
            satisfying EAP-INV-005 and ATF-INV-006.
          </div>
        </div>
      )}
    </DemoShell>
  )
}

// ─── Navigation ───────────────────────────────────────────────────────────────
const NAV_DEMOS = [
  { id: 'DEMO-A', label: 'Runtime Degradation' },
  { id: 'DEMO-B', label: 'Cross-Runtime Divergence' },
  { id: 'DEMO-C', label: 'Archive Verification' },
  { id: 'DEMO-D', label: 'Trust Anchor' },
  { id: 'DEMO-E', label: 'Full Replay' },
]

// ─── Page ─────────────────────────────────────────────────────────────────────
export default function ForensicOperationsDemoPage() {
  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <div style={{ minHeight: '100vh', background: NAVY, color: TEXT }}>
      {/* Header */}
      <header style={{
        background: NAVY3,
        borderBottom: `1px solid ${BORDER}`,
        padding: '0 32px',
        position: 'sticky', top: 0, zIndex: 50,
      }}>
        <div style={{ maxWidth: 1100, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 56 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <span style={{ color: GOLD, fontFamily: 'monospace', fontWeight: 700, fontSize: 13 }}>OMNIX QUANTUM LTD</span>
            <span style={{ color: BORDER }}>|</span>
            <span style={{ color: MUTED, fontSize: 12 }}>FORENSIC OPERATIONS DEMO</span>
            <Badge>ADR-156–167</Badge>
          </div>
          <div style={{ display: 'flex', gap: 12 }}>
            <a href="/archive-verify" style={{ color: MUTED, textDecoration: 'none', fontSize: 12 }}>Verifier ↗</a>
            <a href="/trust-infrastructure" style={{ color: GOLD, textDecoration: 'none', fontSize: 12, fontWeight: 600 }}>Trust Registry ↗</a>
          </div>
        </div>
      </header>

      <main style={{ maxWidth: 1100, margin: '0 auto', padding: '40px 32px' }}>
        {/* Page title */}
        {/* Simulation disclaimer */}
        <div style={{
          background: '#1a1a0a',
          border: `1px solid ${YELLOW}40`,
          borderRadius: 8,
          padding: '12px 20px',
          marginBottom: 32,
          display: 'flex',
          gap: 12,
          alignItems: 'flex-start',
        }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ color: YELLOW, fontFamily: 'monospace', fontWeight: 700, fontSize: 12, whiteSpace: 'nowrap' }}>
                ⚠ SIMULATION BOUNDARY
              </span>
              <span style={{ color: MUTED, fontSize: 12 }}>
                These demos run locally in the browser — they are <strong style={{ color: TEXT }}>not connected to a live OMNIX runtime</strong>.
              </span>
            </div>
            <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 10, fontWeight: 700, color: YELLOW, fontFamily: 'monospace', background: `${YELLOW}15`, border: `1px solid ${YELLOW}30`, padding: '2px 8px', borderRadius: 4 }}>SIMULATION LAYER</span>
                <span style={{ fontSize: 11, color: MUTED, alignSelf: 'center' }}>UI deterministic replay · protocol-compliant data · RFC-ATF-1/2/3 invariants</span>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <span style={{ fontSize: 10, fontWeight: 700, color: '#22c55e', fontFamily: 'monospace', background: '#22c55e15', border: '1px solid #22c55e30', padding: '2px 8px', borderRadius: 4 }}>PRODUCTION ENGINE</span>
                <span style={{ fontSize: 11, color: MUTED, alignSelf: 'center' }}>
                  <code style={{ background: '#ffffff10', padding: '1px 5px', borderRadius: 3, fontSize: 10 }}>omnix_core.simulation.governance_replay</code>
                  {' '}— real PQC-signed artifacts
                </span>
              </div>
            </div>
          </div>
        </div>

        <div style={{ marginBottom: 40 }}>
          <div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap' }}>
            <Badge>PROTOCOL DEMOS</Badge>
            <Badge color={CYAN}>RFC-ATF-1 · RFC-ATF-2 · RFC-ATF-3</Badge>
            <Badge color={GREEN}>47 INVARIANTS</Badge>
          </div>
          <h1 style={{ margin: '0 0 12px', fontSize: 32, fontWeight: 800, color: TEXT, lineHeight: 1.2 }}>
            Forensic Operations — Protocol Simulation
          </h1>
          <p style={{ margin: 0, color: MUTED, fontSize: 16, maxWidth: 700, lineHeight: 1.6 }}>
            Five interactive demonstrations of OMNIX protocol mechanics: runtime authority
            degradation, sovereign policy divergence, immutable evidence chains, post-quantum
            trust anchoring, and complete governance replay from human root to COLD archive.
          </p>
        </div>

        {/* Demo quick-nav */}
        <div style={{
          background: NAVY2, border: `1px solid ${BORDER}`, borderRadius: 10,
          padding: '16px 20px', marginBottom: 40,
          display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center',
        }}>
          <span style={{ fontSize: 11, color: SLATE, fontFamily: 'monospace', marginRight: 4 }}>QUICK NAV:</span>
          {NAV_DEMOS.map(d => (
            <button
              key={d.id}
              onClick={() => scrollTo(d.id)}
              style={{
                padding: '6px 14px', borderRadius: 6,
                border: `1px solid ${BORDER}`, background: 'transparent',
                color: MUTED, fontSize: 12, cursor: 'pointer',
                transition: 'all 0.2s',
              }}
              onMouseEnter={e => { (e.target as HTMLButtonElement).style.borderColor = GOLD; (e.target as HTMLButtonElement).style.color = GOLD }}
              onMouseLeave={e => { (e.target as HTMLButtonElement).style.borderColor = BORDER; (e.target as HTMLButtonElement).style.color = MUTED }}
            >
              <span style={{ color: GOLD, fontFamily: 'monospace', marginRight: 6 }}>{d.id}</span>{d.label}
            </button>
          ))}
        </div>

        <Divider />

        {/* Demos */}
        <DemoA />
        <DemoB />
        <DemoC />
        <DemoD />
        <DemoE />

        {/* Export verification report */}
        <div style={{
          background: `linear-gradient(135deg, ${GOLD}08 0%, transparent 60%)`,
          border: `1px solid ${GOLD}22`,
          borderRadius: 10, padding: '20px 24px', marginBottom: 16,
          display: 'flex', alignItems: 'center', gap: 20, flexWrap: 'wrap',
        }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: TEXT, marginBottom: 4 }}>
              Export Demo Verification Report
            </div>
            <div style={{ fontSize: 11, color: MUTED }}>
              JSON artifact · OMNIX-WALK-001 reference data · simulation boundary declared · RFC-ATF-1/2/3 invariant index
            </div>
          </div>
          <button
            onClick={() => {
              const report = {
                report_id: `OMNIX-DEMO-RPT-${Date.now()}`,
                generated_at: new Date().toISOString(),
                simulation_boundary: {
                  layer: 'UI_DETERMINISTIC_REPLAY',
                  production_engine: 'omnix_core.simulation.governance_replay',
                  note: 'Not connected to a live OMNIX runtime. Production engine produces real PQC-signed artifacts.',
                },
                reference_walkthrough: 'OMNIX-WALK-001',
                rfc_stack: ['RFC-ATF-1 (zenodo.20155016)', 'RFC-ATF-2 (zenodo.20241344)', 'RFC-ATF-3 (zenodo.20247342)', 'RFC-ATF-4 (zenodo.20368895)'],
                invariant_coverage: { total: 47, families: 9, direct_tested: 41, structural: 6 },
                demos: [
                  { id: 'DEMO-A', title: 'Runtime Authority Degradation', adr: 'ADR-159', rfc: 'RFC-ATF-2', invariant: 'RGC-INV-003' },
                  { id: 'DEMO-B', title: 'Cross-Runtime Governance Divergence', adr: 'ADR-161', rfc: 'RFC-ATF-2', invariant: 'RGC-INV-003' },
                  { id: 'DEMO-C', title: 'Immutable Archive Chain Verification', adr: 'ADR-163', rfc: 'RFC-ATF-3', invariant: 'EAP-INV-005' },
                  { id: 'DEMO-D', title: 'Trust Anchor Verification', adr: 'ADR-167', rfc: 'RFC-ATF-1', invariant: 'ATF-INV-006' },
                  { id: 'DEMO-E', title: 'Full Governance Replay DR→TAR→RCR→Receipt→Archive', adr: 'ADR-165', rfc: 'RFC-ATF-1/2/3', invariant: 'ATF-INV-001–006 + RGC-INV-001–008' },
                ],
                key_artifacts: {
                  delegation_id: 'ATFDR-7F3A9B2C1E4D8F6A',
                  block_id: 'OMNIX-BLOCK-20260518-000147',
                  oep_export: 'OEP-20260518-A3F8C241',
                  algorithm: 'ML-DSA-65 (FIPS 204)',
                },
                issuer: 'OMNIX QUANTUM LTD · United Kingdom',
              }
              const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
              const url = URL.createObjectURL(blob)
              const a = document.createElement('a')
              a.href = url
              a.download = `OMNIX-DEMO-VERIFICATION-REPORT-${new Date().toISOString().slice(0,10)}.json`
              a.click()
              URL.revokeObjectURL(url)
            }}
            style={{
              padding: '10px 22px', borderRadius: 8,
              border: `1px solid ${GOLD}55`, background: `${GOLD}15`,
              color: GOLD, fontSize: 12, fontWeight: 700, cursor: 'pointer',
              fontFamily: 'monospace', letterSpacing: '0.04em', whiteSpace: 'nowrap',
            }}
          >
            ↓ Export Report (.json)
          </button>
        </div>

        {/* Footer */}
        <Divider />
        <div style={{
          background: NAVY2, border: `1px solid ${BORDER}`, borderRadius: 10,
          padding: '20px 24px', display: 'flex', gap: 24, flexWrap: 'wrap', alignItems: 'center',
        }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: TEXT, marginBottom: 4 }}>OMNIX QUANTUM LTD</div>
            <div style={{ fontSize: 11, color: MUTED }}>Decision Governance Infrastructure · Post-Quantum Cryptography</div>
          </div>
          <div style={{ flex: 1 }} />
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            {[
              { label: 'Archive Verifier', href: '/archive-verify' },
              { label: 'Trust Registry', href: '/trust-infrastructure' },
              { label: 'Protocol Spec', href: '/protocol' },
              { label: 'ATF Standard', href: '/atf-standard' },
              { label: 'ATF Verifier', href: '/atf-verify' },
            ].map(({ label, href }) => (
              <a key={href} href={href} style={{ color: MUTED, textDecoration: 'none', fontSize: 12 }}
                onMouseEnter={e => (e.target as HTMLElement).style.color = GOLD}
                onMouseLeave={e => (e.target as HTMLElement).style.color = MUTED}
              >{label} ↗</a>
            ))}
          </div>
        </div>
      </main>
    </div>
  )
}
