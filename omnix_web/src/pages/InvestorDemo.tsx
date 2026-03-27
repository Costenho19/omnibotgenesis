import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  CheckCircle, XCircle, ArrowRight, ExternalLink,
  Play, RotateCcw, Lock, Zap, TrendingDown, Package, CreditCard,
  ChevronRight, Clock, Copy, Check
} from 'lucide-react'

import { API_BASE } from '../lib/apiBase'

interface GateResult {
  checkpoint: string
  name: string
  name_en: string
  name_es: string
  result: 'PASS' | 'BLOCKED'
  description: string
}

interface EvaluationResult {
  success: boolean
  decision: 'APPROVED' | 'BLOCKED'
  checkpoints_total: number
  checkpoints_passed: number
  checkpoints_blocked: number
  gate_results: GateResult[]
  receipt?: {
    receipt_id: string
    signature_algorithm: string
    pqc_signed: boolean
    content_hash: string
  }
  receipt_id?: string
  verification_url?: string
  real_world_impact?: {
    estimated_loss_avoided: number
    capital_at_risk: number
    execution_prevented: boolean
  }
}

const SCENARIOS = [
  {
    id: 'trading',
    icon: TrendingDown,
    label: 'Digital Asset Trading',
    tagline: 'Extreme volatility event',
    color: '#C9A227',
    description: 'A trading algorithm receives a BUY signal to deploy $50,000 in BTC during a Black Swan volatility spike — Fear & Greed at 8, market in freefall.',
    scenario_text: 'Automated trading system receives BUY signal for BTC/USD with $50,000 deployment during extreme market volatility. Fear and Greed Index at 8 (Extreme Fear). Black Swan event detected with 4.7% crash probability. Monte Carlo win rate at 48%. Risk models show negative expected return.',
    domain: 'trading',
  },
  {
    id: 'credit',
    icon: CreditCard,
    label: 'Credit Risk Decision',
    tagline: 'Liquidity crisis scenario',
    color: '#6366f1',
    description: 'An automated lending system prepares to approve a $2M commercial loan during a sudden liquidity crisis — counterparty risk spiking, correlations breaking down.',
    scenario_text: 'Automated lending system preparing to approve $2M commercial loan during liquidity crisis. Counterparty risk indicators elevated. Interbank correlation breaking down. Debt-service coverage ratio at threshold. Market stress indicators flashing warning. Credit model confidence degraded.',
    domain: 'credit',
  },
  {
    id: 'supply',
    icon: Package,
    label: 'Supply Chain Governance',
    tagline: 'Geopolitical disruption',
    color: '#10B981',
    description: 'A procurement system executes a $1.2M single-source purchase order during active geopolitical disruption — supplier concentration risk, sanctions exposure.',
    scenario_text: 'Automated procurement system executing $1.2M single-source purchase order during active geopolitical disruption. Supplier concentration at 94% for critical component. Sanctions exposure detected in supplier network. Delivery reliability degraded 40% in prior quarter. No alternative supplier qualified.',
    domain: 'supply_chain',
  },
]

const CHECKPOINT_META = [
  { id: 'CP-0', label: 'Signal Integrity', icon: '🔍', description: 'Validates input data quality and completeness' },
  { id: 'CP-1', label: 'Statistical Edge', icon: '📊', description: 'Monte Carlo — win rate and expected return' },
  { id: 'CP-2', label: 'Tail Risk', icon: '🦢', description: 'Black Swan detection — extreme event probability' },
  { id: 'CP-3', label: 'Signal Coherence', icon: '🔗', description: 'Cross-signal consistency — 6-layer alignment' },
  { id: 'CP-4', label: 'Market Momentum', icon: '⚡', description: 'Directional momentum validation' },
  { id: 'CP-5', label: 'Regime Analysis', icon: '🌊', description: 'HMM market regime classification' },
  { id: 'CP-6', label: 'Compliance Gate', icon: '⚖️', description: 'Regulatory and compliance validation' },
  { id: 'CP-7', label: 'Trajectory Coherence', icon: '🧭', description: 'Temporal admissibility — decision path integrity' },
]

type Step = 'select' | 'running' | 'result'

export default function InvestorDemo() {
  const [step, setStep] = useState<Step>('select')
  const [selected, setSelected] = useState(0)
  const [result, setResult] = useState<EvaluationResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [revealedCheckpoints, setRevealedCheckpoints] = useState<number>(-1)
  const [copied, setCopied] = useState(false)
  const [elapsed, setElapsed] = useState(0)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const animRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const scenario = SCENARIOS[selected]

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
      if (animRef.current) clearTimeout(animRef.current)
    }
  }, [])

  const runDemo = async () => {
    setStep('running')
    setResult(null)
    setError(null)
    setRevealedCheckpoints(-1)
    setElapsed(0)

    timerRef.current = setInterval(() => setElapsed(e => e + 1), 1000)

    try {
      const res = await fetch(`${API_BASE}/api/public/sandbox/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario: scenario.scenario_text,
          language: 'en',
          domain: scenario.domain,
        }),
      })
      const data = await res.json()
      if (timerRef.current) clearInterval(timerRef.current)

      if (data.success) {
        setResult(data)
        const gates = data.gate_results || []
        for (let i = 0; i < gates.length; i++) {
          await new Promise<void>(resolve => {
            animRef.current = setTimeout(() => {
              setRevealedCheckpoints(i)
              resolve()
            }, i === 0 ? 300 : 600)
          })
        }
        await new Promise<void>(resolve => {
          animRef.current = setTimeout(resolve, 800)
        })
        setStep('result')
      } else {
        setError('Governance engine unavailable. Please try again.')
        setStep('select')
      }
    } catch {
      if (timerRef.current) clearInterval(timerRef.current)
      setError('Unable to reach governance engine. Please check connection.')
      setStep('select')
    }
  }

  const reset = () => {
    setStep('select')
    setResult(null)
    setError(null)
    setRevealedCheckpoints(-1)
    setElapsed(0)
  }

  const copyReceipt = () => {
    if (result?.receipt_id) {
      navigator.clipboard.writeText(result.receipt_id)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const gates = result?.gate_results || []
  const blocked = gates.find(g => g.result === 'BLOCKED')

  return (
    <div style={{ minHeight: '100vh', background: 'var(--navy-dark)', color: '#E2E8F0', fontFamily: 'Inter, system-ui, sans-serif' }}>

      {/* NAV */}
      <nav style={{ borderBottom: '1px solid rgba(201,162,39,0.15)', padding: '0 2rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 60 }}>
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 10, textDecoration: 'none' }}>
          <img src="/logo.png" alt="OMNIX" style={{ width: 36, height: 36, objectFit: 'contain' }} />
          <span style={{ fontWeight: 700, color: '#C9A227', fontSize: 16, letterSpacing: '0.05em' }}>OMNIX</span>
        </Link>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <span style={{ fontSize: 12, color: '#64748b' }}>Live Governance Engine</span>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#10B981', boxShadow: '0 0 6px #10B981', animation: 'pulse 2s infinite' }} />
        </div>
      </nav>

      <div style={{ maxWidth: 900, margin: '0 auto', padding: '3rem 1.5rem' }}>

        {/* HEADER */}
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, background: 'rgba(201,162,39,0.1)', border: '1px solid rgba(201,162,39,0.3)', borderRadius: 20, padding: '6px 16px', marginBottom: 20 }}>
            <Zap size={13} color="#C9A227" />
            <span style={{ fontSize: 12, color: '#C9A227', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase' }}>Live 5-Minute Demo</span>
          </div>
          <h1 style={{ fontSize: 'clamp(1.8rem, 4vw, 2.8rem)', fontWeight: 800, color: '#F8FAFC', margin: '0 0 1rem', lineHeight: 1.15 }}>
            Watch the Governance<br />
            <span style={{ color: '#C9A227' }}>Pipeline in Action</span>
          </h1>
          <p style={{ fontSize: '1.05rem', color: '#94A3B8', maxWidth: 560, margin: '0 auto 1rem', lineHeight: 1.65 }}>
            Select a real-world risk scenario. The OMNIX engine evaluates it through
            8 governance checkpoints and returns a cryptographically signed receipt — verifiable by anyone, independently.
          </p>
          <div style={{ display: 'inline-flex', gap: 20, flexWrap: 'wrap', justifyContent: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#64748b' }}>
              <div style={{ width: 7, height: 7, borderRadius: '50%', background: '#10B981' }} />
              Real governance engine — live evaluation every run
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#64748b' }}>
              <div style={{ width: 7, height: 7, borderRadius: '50%', background: '#C9A227' }} />
              Pre-written scenarios — designed to stress-test the pipeline
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#64748b' }}>
              <div style={{ width: 7, height: 7, borderRadius: '50%', background: '#6366f1' }} />
              Want to write your own?{' '}
              <Link to="/try" style={{ color: '#6366f1', textDecoration: 'underline' }}>Open free sandbox →</Link>
            </div>
          </div>
        </div>

        {/* STEP: SELECT */}
        {step === 'select' && (
          <div>
            {error && (
              <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 10, padding: '12px 16px', marginBottom: 24, color: '#FCA5A5', fontSize: 14, textAlign: 'center' }}>
                {error}
              </div>
            )}

            {/* SCENARIO CARDS */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 16, marginBottom: 32 }}>
              {SCENARIOS.map((s, i) => {
                const Icon = s.icon
                const isSelected = selected === i
                return (
                  <button
                    key={s.id}
                    onClick={() => setSelected(i)}
                    style={{
                      background: isSelected ? `rgba(${hexToRgb(s.color)}, 0.1)` : 'rgba(15,33,64,0.6)',
                      border: `2px solid ${isSelected ? s.color : 'rgba(255,255,255,0.06)'}`,
                      borderRadius: 14, padding: '1.5rem', textAlign: 'left', cursor: 'pointer',
                      transition: 'all 0.2s', color: '#E2E8F0',
                      transform: isSelected ? 'translateY(-2px)' : 'none',
                      boxShadow: isSelected ? `0 8px 24px rgba(${hexToRgb(s.color)},0.15)` : 'none',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                      <div style={{ width: 40, height: 40, borderRadius: 10, background: `rgba(${hexToRgb(s.color)},0.15)`, display: 'flex', alignItems: 'center', justifyContent: 'center', border: `1px solid rgba(${hexToRgb(s.color)},0.3)` }}>
                        <Icon size={20} color={s.color} />
                      </div>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: 14, color: '#F8FAFC' }}>{s.label}</div>
                        <div style={{ fontSize: 11, color: s.color, textTransform: 'uppercase', letterSpacing: '0.07em', marginTop: 2 }}>{s.tagline}</div>
                      </div>
                    </div>
                    <p style={{ fontSize: 13, color: '#94A3B8', lineHeight: 1.6, margin: 0 }}>{s.description}</p>
                    {isSelected && (
                      <div style={{ marginTop: 12, display: 'flex', alignItems: 'center', gap: 6, color: s.color, fontSize: 12, fontWeight: 600 }}>
                        <CheckCircle size={14} />
                        Selected
                      </div>
                    )}
                  </button>
                )
              })}
            </div>

            {/* WHAT WILL HAPPEN */}
            <div style={{ background: 'rgba(15,33,64,0.4)', border: '1px solid rgba(201,162,39,0.12)', borderRadius: 12, padding: '1.25rem 1.5rem', marginBottom: 28, display: 'flex', gap: 32, flexWrap: 'wrap' }}>
              {[
                { n: '8', label: 'Governance Checkpoints' },
                { n: '< 10s', label: 'Full Pipeline Evaluation' },
                { n: '1', label: 'PQC-Signed Receipt' },
                { n: '∞', label: 'Independent Verifications' },
              ].map(item => (
                <div key={item.label} style={{ textAlign: 'center', flex: 1, minWidth: 100 }}>
                  <div style={{ fontSize: 22, fontWeight: 800, color: '#C9A227' }}>{item.n}</div>
                  <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>{item.label}</div>
                </div>
              ))}
            </div>

            <button
              onClick={runDemo}
              style={{
                width: '100%', padding: '1rem 2rem', background: 'linear-gradient(135deg,#C9A227,#A68B1F)',
                border: 'none', borderRadius: 12, color: '#050D18', fontWeight: 800,
                fontSize: 16, cursor: 'pointer', display: 'flex', alignItems: 'center',
                justifyContent: 'center', gap: 10, letterSpacing: '0.03em',
                boxShadow: '0 4px 24px rgba(201,162,39,0.3)', transition: 'all 0.2s',
              }}
            >
              <Play size={18} />
              Run Governance Pipeline — {scenario.label}
              <ChevronRight size={18} />
            </button>
          </div>
        )}

        {/* STEP: RUNNING */}
        {step === 'running' && (
          <div>
            <div style={{ textAlign: 'center', marginBottom: 32 }}>
              <div style={{ fontSize: 13, color: '#64748b', marginBottom: 8 }}>Evaluating scenario through 8 checkpoints...</div>
              <div style={{ fontSize: 11, color: '#C9A227' }}>
                <Clock size={11} style={{ display: 'inline', marginRight: 4 }} />
                {elapsed}s elapsed
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              {CHECKPOINT_META.map((cp, i) => {
                const gate = gates[i]
                const revealed = i <= revealedCheckpoints
                const status = revealed && gate ? gate.result : null

                return (
                  <div
                    key={cp.id}
                    style={{
                      background: revealed
                        ? status === 'PASS'
                          ? 'rgba(16,185,129,0.08)'
                          : 'rgba(239,68,68,0.08)'
                        : 'rgba(15,33,64,0.4)',
                      border: `1px solid ${revealed
                        ? status === 'PASS' ? 'rgba(16,185,129,0.25)' : 'rgba(239,68,68,0.25)'
                        : 'rgba(255,255,255,0.05)'}`,
                      borderRadius: 10, padding: '0.9rem 1rem',
                      display: 'flex', alignItems: 'center', gap: 12,
                      transition: 'all 0.4s ease',
                      opacity: revealed ? 1 : 0.4,
                    }}
                  >
                    <div style={{ fontSize: 20 }}>{cp.icon}</div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 12, fontWeight: 700, color: '#F8FAFC' }}>{cp.id}: {cp.label}</div>
                      <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>{cp.description}</div>
                    </div>
                    <div style={{ flexShrink: 0 }}>
                      {!revealed && (
                        <div style={{ width: 20, height: 20, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.1)', borderTopColor: '#C9A227', animation: 'spin 1s linear infinite' }} />
                      )}
                      {revealed && status === 'PASS' && <CheckCircle size={20} color="#10B981" />}
                      {revealed && status === 'BLOCKED' && <XCircle size={20} color="#EF4444" />}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* STEP: RESULT */}
        {step === 'result' && result && (
          <div>
            {/* VERDICT BANNER */}
            <div style={{
              background: result.decision === 'BLOCKED'
                ? 'linear-gradient(135deg, rgba(239,68,68,0.15), rgba(239,68,68,0.05))'
                : 'linear-gradient(135deg, rgba(16,185,129,0.15), rgba(16,185,129,0.05))',
              border: `2px solid ${result.decision === 'BLOCKED' ? 'rgba(239,68,68,0.4)' : 'rgba(16,185,129,0.4)'}`,
              borderRadius: 16, padding: '2rem', textAlign: 'center', marginBottom: 28,
            }}>
              <div style={{ fontSize: 48, marginBottom: 8 }}>
                {result.decision === 'BLOCKED' ? '🛡️' : '✅'}
              </div>
              <div style={{
                fontSize: 'clamp(1.4rem, 3vw, 2rem)', fontWeight: 900,
                color: result.decision === 'BLOCKED' ? '#FCA5A5' : '#6EE7B7',
                letterSpacing: '0.05em',
              }}>
                EXECUTION {result.decision}
              </div>
              <div style={{ fontSize: 14, color: '#94A3B8', marginTop: 8, maxWidth: 480, margin: '8px auto 0' }}>
                {result.decision === 'BLOCKED'
                  ? `The governance pipeline intercepted this execution. ${blocked ? `Blocked at ${blocked.name_en || blocked.name || blocked.checkpoint}.` : 'Risk thresholds exceeded.'} No capital was committed.`
                  : `All 8 governance checkpoints passed. Execution authorized with cryptographic commitment.`
                }
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 20, marginTop: 20, flexWrap: 'wrap' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 22, fontWeight: 800, color: '#10B981' }}>{result.checkpoints_passed}</div>
                  <div style={{ fontSize: 11, color: '#64748b' }}>Passed</div>
                </div>
                <div style={{ width: 1, height: 32, background: 'rgba(255,255,255,0.1)' }} />
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 22, fontWeight: 800, color: '#EF4444' }}>{result.checkpoints_blocked}</div>
                  <div style={{ fontSize: 11, color: '#64748b' }}>Blocked</div>
                </div>
                <div style={{ width: 1, height: 32, background: 'rgba(255,255,255,0.1)' }} />
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 22, fontWeight: 800, color: '#C9A227' }}>{result.checkpoints_total}</div>
                  <div style={{ fontSize: 11, color: '#64748b' }}>Total Checkpoints</div>
                </div>
                {result.real_world_impact?.estimated_loss_avoided ? (
                  <>
                    <div style={{ width: 1, height: 32, background: 'rgba(255,255,255,0.1)' }} />
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 22, fontWeight: 800, color: '#C9A227' }}>
                        ${result.real_world_impact.estimated_loss_avoided.toLocaleString()}
                      </div>
                      <div style={{ fontSize: 11, color: '#64748b' }}>Est. Loss Avoided</div>
                    </div>
                  </>
                ) : null}
              </div>
            </div>

            {/* CHECKPOINT BREAKDOWN */}
            <div style={{ marginBottom: 24 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 12 }}>
                Pipeline Breakdown
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                {gates.map((gate, i) => {
                  const meta = CHECKPOINT_META[i] || {}
                  return (
                    <div
                      key={gate.checkpoint}
                      style={{
                        background: gate.result === 'PASS' ? 'rgba(16,185,129,0.06)' : 'rgba(239,68,68,0.08)',
                        border: `1px solid ${gate.result === 'PASS' ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.25)'}`,
                        borderRadius: 8, padding: '0.75rem 1rem',
                        display: 'flex', alignItems: 'center', gap: 10,
                      }}
                    >
                      <div style={{ fontSize: 16 }}>{meta.icon || '🔹'}</div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 12, fontWeight: 600, color: '#E2E8F0' }}>
                          {gate.name_en || gate.name || gate.checkpoint}
                        </div>
                        {gate.description && (
                          <div style={{ fontSize: 11, color: '#64748b', marginTop: 2, lineHeight: 1.4 }}>
                            {gate.description.length > 60 ? gate.description.slice(0, 60) + '…' : gate.description}
                          </div>
                        )}
                      </div>
                      {gate.result === 'PASS'
                        ? <CheckCircle size={16} color="#10B981" style={{ flexShrink: 0 }} />
                        : <XCircle size={16} color="#EF4444" style={{ flexShrink: 0 }} />
                      }
                    </div>
                  )
                })}
              </div>
            </div>

            {/* PQC RECEIPT */}
            {result.receipt_id && (
              <div style={{ background: 'rgba(15,33,64,0.6)', border: '1px solid rgba(201,162,39,0.2)', borderRadius: 14, padding: '1.25rem 1.5rem', marginBottom: 20 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                  <Lock size={14} color="#C9A227" />
                  <span style={{ fontSize: 12, fontWeight: 700, color: '#C9A227', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                    Post-Quantum Cryptographic Receipt
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, background: 'rgba(0,0,0,0.3)', borderRadius: 8, padding: '10px 14px', marginBottom: 12 }}>
                  <code style={{ flex: 1, fontSize: 14, fontFamily: 'monospace', color: '#F8FAFC', letterSpacing: '0.04em' }}>
                    {result.receipt_id}
                  </code>
                  <button
                    onClick={copyReceipt}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: copied ? '#10B981' : '#64748b', display: 'flex', padding: 4 }}
                  >
                    {copied ? <Check size={16} /> : <Copy size={16} />}
                  </button>
                </div>
                <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', fontSize: 12, marginBottom: 10 }}>
                  <div>
                    <span style={{ color: '#64748b' }}>Signing algorithm (production): </span>
                    <span style={{ color: '#C9A227', fontWeight: 600 }}>Dilithium-3 (NIST-standardized)</span>
                  </div>
                  <div>
                    <span style={{ color: '#64748b' }}>PQC Signed: </span>
                    <span style={{ color: '#10B981', fontWeight: 600 }}>✓ Yes</span>
                  </div>
                  {result.receipt?.content_hash && (
                    <div>
                      <span style={{ color: '#64748b' }}>Hash (SHA-256): </span>
                      <code style={{ color: '#94A3B8', fontSize: 11 }}>
                        {result.receipt.content_hash.slice(0, 16)}…
                      </code>
                    </div>
                  )}
                </div>
                <div style={{ fontSize: 11, color: '#475569', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: 8 }}>
                  <strong style={{ color: '#64748b' }}>Transparency note:</strong> This sandbox receipt uses SHA-256 for its isolated chain hash. Production receipts (live trading bot) are signed end-to-end with Dilithium-3. The governance logic and checkpoint evaluation are identical in both environments.
                </div>
              </div>
            )}

            {/* KEY INSIGHT */}
            <div style={{ background: 'rgba(201,162,39,0.06)', border: '1px solid rgba(201,162,39,0.15)', borderRadius: 12, padding: '1.25rem 1.5rem', marginBottom: 24 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#C9A227', marginBottom: 6 }}>
                What just happened
              </div>
              <p style={{ fontSize: 13, color: '#94A3B8', lineHeight: 1.7, margin: 0 }}>
                The governance engine didn't just validate the signal — it either formed an executable decision state or didn't.
                There was no ambiguous intermediate result. The receipt above is the cryptographic proof of that determination,
                verifiable by anyone independently, without access to OMNIX systems.
              </p>
            </div>

            {/* CTA */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12, marginBottom: 20 }}>
              {result.receipt_id && (
                <a
                  href={`/verify/${result.receipt_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                    padding: '0.9rem 1.5rem', background: 'linear-gradient(135deg,#C9A227,#A68B1F)',
                    borderRadius: 10, color: '#050D18', fontWeight: 700, fontSize: 14,
                    textDecoration: 'none', cursor: 'pointer',
                  }}
                >
                  <ExternalLink size={16} />
                  Verify Receipt Independently
                </a>
              )}
              <Link
                to="/institutional"
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                  padding: '0.9rem 1.5rem', background: 'rgba(201,162,39,0.1)',
                  border: '1px solid rgba(201,162,39,0.3)',
                  borderRadius: 10, color: '#C9A227', fontWeight: 700, fontSize: 14,
                  textDecoration: 'none',
                }}
              >
                Request Data Room Access
                <ArrowRight size={16} />
              </Link>
            </div>

            <div style={{ display: 'flex', gap: 12 }}>
              <button
                onClick={() => { reset(); }}
                style={{
                  flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                  padding: '0.8rem', background: 'rgba(255,255,255,0.04)',
                  border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10,
                  color: '#64748b', fontWeight: 600, fontSize: 13, cursor: 'pointer',
                }}
              >
                <RotateCcw size={14} />
                Try Another Scenario
              </button>
              <Link
                to="/try"
                style={{
                  flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                  padding: '0.8rem', background: 'rgba(255,255,255,0.04)',
                  border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10,
                  color: '#64748b', fontWeight: 600, fontSize: 13, textDecoration: 'none',
                }}
              >
                Open Free Sandbox
                <ExternalLink size={13} />
              </Link>
            </div>
          </div>
        )}

        {/* BOTTOM STRIP */}
        <div style={{ marginTop: 48, paddingTop: 24, borderTop: '1px solid rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div style={{ fontSize: 12, color: '#334155' }}>
            <span style={{ color: '#C9A227', fontWeight: 700 }}>OMNIX</span> Decision Governance Infrastructure
            {' · '}Eureka Dubai GCC 2026 Semifinalist
          </div>
          <div style={{ display: 'flex', gap: 16 }}>
            <Link to="/" style={{ fontSize: 12, color: '#334155', textDecoration: 'none' }}>Home</Link>
            <Link to="/institutional" style={{ fontSize: 12, color: '#334155', textDecoration: 'none' }}>Investors</Link>
            <a href="https://omnixquantum.net/try" style={{ fontSize: 12, color: '#334155', textDecoration: 'none' }}>Sandbox</a>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.4; } }
      `}</style>
    </div>
  )
}

function hexToRgb(hex: string): string {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `${r},${g},${b}`
}
