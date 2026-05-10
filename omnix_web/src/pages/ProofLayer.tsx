import { useState } from 'react'
import { Shield, CheckCircle, XCircle, ArrowRight, ExternalLink, Copy, RotateCcw, Lock, Hash, Link2 } from 'lucide-react'

const ASSETS = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT', 'LINK', 'BNB', 'USDC', 'XMR', 'DOGE', 'SHIB']
const JURISDICTIONS = ['US', 'UK', 'EU', 'SG', 'AU', 'CA', 'JP', 'UAE', 'BR', 'IN']
const ACTIONS = [
  { value: 'TRADE', label: 'Trade (Spot)' },
  { value: 'BUY',   label: 'Buy' },
  { value: 'SELL',  label: 'Sell' },
  { value: 'LEVERAGE', label: 'Leverage' },
  { value: 'SHORT', label: 'Short' },
]

interface EvaluateResult {
  status: string
  receipt_id: string
  reason: string
  layer0: string
  evaluated_at: string
  verify_url: string
  governance_summary: {
    checkpoints_passed: number
    checkpoints_total: number
    layer0_status: string
    jurisdiction: string
    asset: string
  }
}

interface VerifyResult {
  status: string
  source: string
  decision: string
  reason_code: string
  hash_valid: boolean | null
  signature_valid: boolean | null
  chain_valid: boolean | null
  timestamp_issued: string
  receipt_id: string
  validation_policy: {
    hash: string
    signature: string
    chain: string
  }
  issuer: string
  verify_url: string
}

type Step = 'form' | 'receipt' | 'verify'

function FieldBadge({ value, good, neutral }: { value: boolean | null | string; good?: boolean | null; neutral?: boolean }) {
  if (value === null || value === undefined) {
    return <span style={{ background: '#1E293B', color: '#94A3B8', padding: '2px 10px', borderRadius: 12, fontSize: 13, fontFamily: 'monospace' }}>null</span>
  }
  if (typeof value === 'boolean') {
    return (
      <span style={{
        background: value ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
        color: value ? '#10B981' : '#EF4444',
        padding: '2px 10px', borderRadius: 12, fontSize: 13, fontFamily: 'monospace',
        border: `1px solid ${value ? '#10B98133' : '#EF444433'}`
      }}>{String(value)}</span>
    )
  }
  if (neutral) {
    return <span style={{ background: '#1E293B', color: '#94A3B8', padding: '2px 10px', borderRadius: 12, fontSize: 13, fontFamily: 'monospace' }}>{value}</span>
  }
  const isGood = good ?? (value === 'VALID' || value === 'APPROVED' || value === 'GOVERNANCE_PASS')
  const isBad  = value === 'INVALID' || value === 'BLOCKED'
  const color  = isGood ? '#10B981' : isBad ? '#EF4444' : '#F59E0B'
  const bg     = isGood ? 'rgba(16,185,129,0.15)' : isBad ? 'rgba(239,68,68,0.15)' : 'rgba(245,158,11,0.15)'
  const border = isGood ? '#10B98133' : isBad ? '#EF444433' : '#F59E0B33'
  return (
    <span style={{ background: bg, color, padding: '2px 10px', borderRadius: 12, fontSize: 13, fontFamily: 'monospace', border: `1px solid ${border}` }}>
      {value}
    </span>
  )
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <button
      onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 1500) }}
      title="Copiar"
      style={{ background: 'none', border: 'none', cursor: 'pointer', color: copied ? '#10B981' : '#64748B', padding: '2px 4px', borderRadius: 4 }}
    >
      <Copy size={14} />
    </button>
  )
}

function StepIndicator({ current }: { current: Step }) {
  const steps: { key: Step; label: string }[] = [
    { key: 'form',    label: '1 — Submit Decision' },
    { key: 'receipt', label: '2 — Receipt Issued' },
    { key: 'verify',  label: '3 — Verify' },
  ]
  const idx = steps.findIndex(s => s.key === current)
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 32 }}>
      {steps.map((s, i) => (
        <div key={s.key} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            width: 28, height: 28, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 13, fontWeight: 700,
            background: i < idx ? '#10B981' : i === idx ? '#C9A227' : '#1E293B',
            color: i <= idx ? '#000' : '#64748B',
            border: i === idx ? '2px solid #C9A227' : 'none',
          }}>{i < idx ? '✓' : i + 1}</div>
          <span style={{ fontSize: 13, color: i === idx ? '#C9A227' : i < idx ? '#10B981' : '#475569', whiteSpace: 'nowrap' }}>
            {s.label}
          </span>
          {i < steps.length - 1 && <ArrowRight size={14} color="#334155" style={{ marginRight: 4 }} />}
        </div>
      ))}
    </div>
  )
}

export default function ProofLayer() {
  const [step, setStep]             = useState<Step>('form')
  const [asset, setAsset]           = useState('BTC')
  const [jurisdiction, setJur]      = useState('US')
  const [action, setAction]         = useState('TRADE')
  const [amount, setAmount]         = useState('5000')
  const [loading, setLoading]       = useState(false)
  const [error, setError]           = useState<string | null>(null)
  const [evaluate, setEvaluate]     = useState<EvaluateResult | null>(null)
  const [verify, setVerify]         = useState<VerifyResult | null>(null)

  const reset = () => { setStep('form'); setEvaluate(null); setVerify(null); setError(null) }

  const handleSubmit = async () => {
    setLoading(true); setError(null)
    try {
      const r = await fetch('/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, asset, amount: parseFloat(amount) || 1000, jurisdiction }),
      })
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      const d: EvaluateResult = await r.json()
      setEvaluate(d)
      setStep('receipt')
    } catch (e) {
      setError('Could not connect to the governance engine. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleVerify = async () => {
    if (!evaluate) return
    setLoading(true); setError(null)
    try {
      const r = await fetch(`/verify/${evaluate.receipt_id}`)
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      const d: VerifyResult = await r.json()
      setVerify(d)
      setStep('verify')
    } catch (e) {
      setError('Error verifying the receipt. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const isApproved = evaluate?.status === 'APPROVED'

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(180deg, #050D18 0%, #0A1628 60%, #0F2140 100%)',
      color: '#E2E8F0',
      fontFamily: "'Inter', system-ui, sans-serif",
      padding: '40px 20px',
    }}>
      <div style={{ maxWidth: 760, margin: '0 auto' }}>

        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 48 }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
            <Shield size={32} color="#C9A227" />
            <span style={{ fontSize: 11, letterSpacing: 4, color: '#C9A227', fontWeight: 700, textTransform: 'uppercase' }}>
              OMNIX QUANTUM
            </span>
          </div>
          <h1 style={{ fontSize: 28, fontWeight: 800, margin: '0 0 12px', color: '#F1F5F9', lineHeight: 1.2 }}>
            Proof Layer — Live Verification
          </h1>
          <p style={{ fontSize: 15, color: '#94A3B8', maxWidth: 520, margin: '0 auto', lineHeight: 1.6 }}>
            Submit a governance decision, receive a signed receipt, and verify its integrity independently.
            Every receipt is permanently recorded and auditable at any time.
          </p>
        </div>

        {/* Step Indicator */}
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <StepIndicator current={step} />
        </div>

        {/* Error */}
        {error && (
          <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid #EF444433', borderRadius: 8, padding: '12px 16px', marginBottom: 24, color: '#FCA5A5', fontSize: 14 }}>
            {error}
          </div>
        )}

        {/* STEP 1 — FORM */}
        {step === 'form' && (
          <div style={{ background: '#0F2140', border: '1px solid #1E3A5F', borderRadius: 12, padding: 32 }}>
            <h2 style={{ fontSize: 17, fontWeight: 700, marginTop: 0, marginBottom: 24, color: '#F1F5F9' }}>
              What decision do you want to evaluate?
            </h2>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
              <div>
                <label style={{ display: 'block', fontSize: 12, color: '#94A3B8', marginBottom: 6, letterSpacing: 1, textTransform: 'uppercase' }}>Asset</label>
                <select value={asset} onChange={e => setAsset(e.target.value)} style={selectStyle}>
                  {ASSETS.map(a => <option key={a} value={a}>{a}</option>)}
                </select>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 12, color: '#94A3B8', marginBottom: 6, letterSpacing: 1, textTransform: 'uppercase' }}>Jurisdiction</label>
                <select value={jurisdiction} onChange={e => setJur(e.target.value)} style={selectStyle}>
                  {JURISDICTIONS.map(j => <option key={j} value={j}>{j}</option>)}
                </select>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 12, color: '#94A3B8', marginBottom: 6, letterSpacing: 1, textTransform: 'uppercase' }}>Operation</label>
                <select value={action} onChange={e => setAction(e.target.value)} style={selectStyle}>
                  {ACTIONS.map(a => <option key={a.value} value={a.value}>{a.label}</option>)}
                </select>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 12, color: '#94A3B8', marginBottom: 6, letterSpacing: 1, textTransform: 'uppercase' }}>Amount (USD)</label>
                <input
                  type="number" value={amount} onChange={e => setAmount(e.target.value)}
                  min={100} max={10000000}
                  style={{ ...selectStyle, fontFamily: 'monospace' }}
                />
              </div>
            </div>

            <div style={{ background: '#1E293B', borderRadius: 8, padding: '12px 16px', marginBottom: 24, fontSize: 13, color: '#64748B', lineHeight: 1.6 }}>
              <strong style={{ color: '#94A3B8' }}>Tip:</strong> Try XMR + UAE to see a Layer 0 block (VARA regulatory restriction),
              or SHIB + UAE with a high amount to trigger a governance checkpoint block.
            </div>

            <button
              onClick={handleSubmit} disabled={loading}
              style={{
                width: '100%', padding: '14px 24px', borderRadius: 8, border: 'none',
                background: loading ? '#1E293B' : '#C9A227',
                color: loading ? '#475569' : '#000',
                fontSize: 15, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              }}
            >
              {loading ? 'Evaluating...' : <><Shield size={16} /> Evaluate and generate receipt</>}
            </button>
          </div>
        )}

        {/* STEP 2 — RECEIPT */}
        {step === 'receipt' && evaluate && (
          <div>
            <div style={{ background: '#0F2140', border: `1px solid ${isApproved ? '#10B98133' : '#EF444433'}`, borderRadius: 12, padding: 32, marginBottom: 20 }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 24 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  {isApproved
                    ? <CheckCircle size={32} color="#10B981" />
                    : <XCircle size={32} color="#EF4444" />
                  }
                  <div>
                    <div style={{ fontSize: 11, color: '#64748B', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 4 }}>Governance Decision</div>
                    <div style={{ fontSize: 22, fontWeight: 800, color: isApproved ? '#10B981' : '#EF4444' }}>
                      {isApproved ? 'APPROVED' : 'BLOCKED'}
                    </div>
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 11, color: '#64748B', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 4 }}>Layer 0</div>
                  <span style={{
                    fontSize: 13, fontWeight: 600, fontFamily: 'monospace',
                    color: evaluate.layer0 === 'BLOCKED' ? '#EF4444' : '#10B981',
                  }}>{evaluate.layer0}</span>
                </div>
              </div>

              {/* Receipt ID */}
              <div style={{ background: '#050D18', borderRadius: 8, padding: '12px 16px', marginBottom: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ fontSize: 11, color: '#64748B', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 4 }}>Receipt ID</div>
                  <code style={{ fontSize: 14, color: '#C9A227', fontFamily: 'monospace' }}>{evaluate.receipt_id}</code>
                </div>
                <CopyButton text={evaluate.receipt_id} />
              </div>

              {/* Reason */}
              <div style={{ background: '#050D18', borderRadius: 8, padding: '12px 16px', marginBottom: 16 }}>
                <div style={{ fontSize: 11, color: '#64748B', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 6 }}>Reason</div>
                <div style={{ fontSize: 13, color: '#CBD5E1', lineHeight: 1.6 }}>{evaluate.reason}</div>
              </div>

              {/* Summary */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginBottom: 20 }}>
                {[
                  { label: 'Asset', value: evaluate.governance_summary?.asset },
                  { label: 'Jurisdiction', value: evaluate.governance_summary?.jurisdiction },
                  { label: 'Checkpoints', value: `${evaluate.governance_summary?.checkpoints_passed ?? 0}/${evaluate.governance_summary?.checkpoints_total ?? 0}` },
                ].map(({ label, value }) => (
                  <div key={label} style={{ background: '#1E293B', borderRadius: 8, padding: '10px 14px' }}>
                    <div style={{ fontSize: 11, color: '#64748B', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 4 }}>{label}</div>
                    <div style={{ fontSize: 14, color: '#E2E8F0', fontFamily: 'monospace', fontWeight: 600 }}>{value}</div>
                  </div>
                ))}
              </div>

              <div style={{ fontSize: 12, color: '#475569', marginBottom: 20 }}>
                Issued: {new Date(evaluate.evaluated_at).toLocaleString()} UTC
              </div>

              <button
                onClick={handleVerify} disabled={loading}
                style={{
                  width: '100%', padding: '14px 24px', borderRadius: 8,
                  background: loading ? '#1E293B' : 'linear-gradient(135deg, #0F2140, #1E3A5F)',
                  color: loading ? '#475569' : '#C9A227',
                  fontSize: 15, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                  border: loading ? '1px solid #1E293B' : '1px solid #C9A22733',
                }}
              >
                {loading ? 'Verifying...' : <><Hash size={16} /> Verify receipt integrity</>}
              </button>
            </div>

            <button onClick={reset} style={ghostBtn}>
              <RotateCcw size={14} /> New evaluation
            </button>
          </div>
        )}

        {/* STEP 3 — VERIFY */}
        {step === 'verify' && verify && evaluate && (
          <div>
            <div style={{ background: '#0F2140', border: `1px solid ${verify.status === 'VALID' ? '#10B98133' : '#EF444433'}`, borderRadius: 12, padding: 32, marginBottom: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 28 }}>
                <Lock size={28} color={verify.status === 'VALID' ? '#10B981' : '#EF4444'} />
                <div>
                  <div style={{ fontSize: 11, color: '#64748B', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 4 }}>Independent Verification Result</div>
                  <div style={{ fontSize: 22, fontWeight: 800, color: verify.status === 'VALID' ? '#10B981' : '#EF4444' }}>
                    {verify.status === 'VALID' ? 'VALID RECEIPT' : 'INVALID RECEIPT'}
                  </div>
                </div>
              </div>

              {/* Integrity fields */}
              <div style={{ marginBottom: 20 }}>
                <div style={{ fontSize: 12, color: '#64748B', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 12 }}>Cryptographic Integrity</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {[
                    {
                      icon: <Hash size={14} />,
                      label: 'Content Hash',
                      value: verify.hash_valid,
                      policy: 'strict',
                      desc: verify.hash_valid === true ? 'The receipt has not been modified since issuance.' : verify.hash_valid === false ? 'ALERT: content altered after issuance.' : 'Hash not available (does not affect validity).'
                    },
                    {
                      icon: <Lock size={14} />,
                      label: 'Cryptographic Signature',
                      value: verify.signature_valid,
                      policy: 'optional',
                      desc: verify.signature_valid === true ? 'Signature verified.' : 'Not available — EVL receipts do not carry an individual signature (optional by design).'
                    },
                    {
                      icon: <Link2 size={14} />,
                      label: 'Continuity Chain',
                      value: verify.chain_valid,
                      policy: 'contextual',
                      desc: 'Autonomous receipt — EVL receipts have no chain. ADR-096 will implement chain verification.'
                    },
                  ].map(({ icon, label, value, policy, desc }) => (
                    <div key={label} style={{ background: '#050D18', borderRadius: 8, padding: '12px 16px', display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                      <div style={{ color: '#475569', marginTop: 2, flexShrink: 0 }}>{icon}</div>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                          <span style={{ fontSize: 13, color: '#CBD5E1', fontWeight: 600 }}>{label}</span>
                          <FieldBadge value={value} />
                          <span style={{ fontSize: 11, color: '#334155', fontFamily: 'monospace', background: '#1E293B', padding: '1px 6px', borderRadius: 4 }}>{policy}</span>
                        </div>
                        <div style={{ fontSize: 12, color: '#64748B', lineHeight: 1.5 }}>{desc}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Decision fields */}
              <div style={{ marginBottom: 20 }}>
                <div style={{ fontSize: 12, color: '#64748B', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 12 }}>Decision Traceability</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {[
                    { label: 'Recorded Decision', value: verify.decision },
                    { label: 'Reason code', value: verify.reason_code },
                    { label: 'Verification Source', value: verify.source, neutral: true },
                    { label: 'Issuer (DID)', value: verify.issuer, neutral: true },
                  ].map(({ label, value, neutral }) => (
                    <div key={label} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #1E293B' }}>
                      <span style={{ fontSize: 13, color: '#94A3B8' }}>{label}</span>
                      <FieldBadge value={value} neutral={neutral} />
                    </div>
                  ))}
                </div>
              </div>

              {/* Verify URL */}
              <div style={{ background: '#050D18', borderRadius: 8, padding: '12px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ fontSize: 11, color: '#64748B', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 4 }}>Public Verification URL</div>
                  <code style={{ fontSize: 12, color: '#7DD3FC', wordBreak: 'break-all' }}>{evaluate.verify_url}</code>
                </div>
                <div style={{ display: 'flex', gap: 8, flexShrink: 0, marginLeft: 12 }}>
                  <CopyButton text={evaluate.verify_url} />
                  <a href={evaluate.verify_url} target="_blank" rel="noopener noreferrer"
                    style={{ color: '#64748B', display: 'flex', alignItems: 'center' }}
                    title="Open at omnixquantum.net">
                    <ExternalLink size={14} />
                  </a>
                </div>
              </div>
            </div>

            {/* Policy explanation */}
            <div style={{ background: '#0A1628', border: '1px solid #1E293B', borderRadius: 8, padding: '16px 20px', marginBottom: 20 }}>
              <div style={{ fontSize: 12, color: '#64748B', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 10 }}>
                Validation Policy
              </div>
              <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
                {Object.entries(verify.validation_policy || {}).map(([k, v]) => (
                  <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: 13, color: '#E2E8F0', fontFamily: 'monospace' }}>{k}</span>
                    <span style={{ fontSize: 11, background: '#1E293B', color: '#94A3B8', padding: '2px 8px', borderRadius: 4, fontFamily: 'monospace' }}>{v}</span>
                  </div>
                ))}
              </div>
              <div style={{ fontSize: 12, color: '#475569', marginTop: 8 }}>
                <strong style={{ color: '#64748B' }}>strict</strong> = null invalidates · 
                <strong style={{ color: '#64748B' }}> optional</strong> = null does not invalidate · 
                <strong style={{ color: '#64748B' }}> contextual</strong> = null = autonomous receipt
              </div>
            </div>

            <button onClick={reset} style={ghostBtn}>
              <RotateCcw size={14} /> New evaluation
            </button>
          </div>
        )}

        {/* Footer */}
        <div style={{ textAlign: 'center', marginTop: 48, paddingTop: 24, borderTop: '1px solid #1E293B' }}>
          <p style={{ fontSize: 12, color: '#334155', lineHeight: 1.8 }}>
            OMNIX QUANTUM LTD · did:web:omnixquantum.net · Schema v6.6.0<br />
            15 provisional patents USPTO · OMNIX-PAT-2026-001 to 015<br />
            Inventor: Harold Alberto Nunes Rodelo
          </p>
        </div>

      </div>
    </div>
  )
}

const selectStyle: React.CSSProperties = {
  width: '100%', padding: '10px 12px', borderRadius: 8,
  background: '#050D18', border: '1px solid #1E3A5F',
  color: '#E2E8F0', fontSize: 14, outline: 'none',
  appearance: 'none' as const,
}

const ghostBtn: React.CSSProperties = {
  background: 'none', border: '1px solid #1E3A5F', borderRadius: 8,
  color: '#64748B', fontSize: 13, cursor: 'pointer', padding: '8px 16px',
  display: 'flex', alignItems: 'center', gap: 6,
}
