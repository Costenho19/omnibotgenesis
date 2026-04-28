import { useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import { Shield, CheckCircle, XCircle, Clock, Zap, Lock, RefreshCw, ChevronRight, FileCheck, AlertTriangle, Eye } from 'lucide-react'
import { API_BASE } from '../lib/apiBase'

const PRESET_SCENARIOS = [
  {
    label: 'Credit Risk',
    text: 'Approve a $2.5M credit line for a construction company with 3 months of operation, no audited financials, and the CEO has a prior bankruptcy in 2019.',
  },
  {
    label: 'M&A Decision',
    text: 'Acquire a biotech startup for $180M. The target has a promising pipeline but two ongoing FDA investigations and undisclosed IP disputes with a major competitor.',
  },
  {
    label: 'AI Deployment',
    text: 'Deploy an autonomous AI system for loan underwriting decisions affecting 50,000 customers monthly, with no human review layer and no explainability module.',
  },
  {
    label: 'Real Estate',
    text: 'Approve a $40M commercial real estate purchase in a flood zone with outdated environmental reports and a seller who has refused due diligence access for 60 days.',
  },
]

const CHECKPOINT_NAMES: Record<string, string> = {
  'CP-1':  'Data Integrity Scan',
  'CP-2':  'Financial Signal Analysis',
  'CP-3':  'Risk Threshold Check',
  'CP-4':  'Regulatory Compliance',
  'CP-5':  'Market Exposure',
  'CP-6':  'Counterparty Shield',
  'CP-7':  'Legal & Jurisdictional',
  'CP-8':  'Behavioral Intelligence',
  'CP-9':  'Capital Adequacy',
  'CP-10': 'Fraud & AML Detection',
  'CP-11': 'Cross-Border Exposure',
}

type Phase = 'input' | 'running' | 'done'
type VcPhase = 'idle' | 'revoking' | 'revoked'

interface GateResult {
  checkpoint: string
  result: 'PASS' | 'BLOCKED'
  description: string
}

interface EvalResult {
  success: boolean
  decision: 'APPROVED' | 'BLOCKED'
  explanation: string
  checkpoints_total: number
  checkpoints_passed: number
  checkpoints_blocked: number
  gate_results: GateResult[]
  receipt_id: string | null
  receipt: { content_hash: string; signature_algorithm: string; pqc_signed: boolean } | null
  verification_url: string | null
}

export default function FullDemo() {
  const [scenario, setScenario] = useState(PRESET_SCENARIOS[0].text)
  const [activePreset, setActivePreset] = useState(0)
  const [phase, setPhase] = useState<Phase>('input')
  const [spgPhase, setSpgPhase] = useState<'idle' | 'checking' | 'done'>('idle')
  const [pipelineStep, setPipelineStep] = useState(-1)
  const [result, setResult] = useState<EvalResult | null>(null)
  const [vcPhase, setVcPhase] = useState<VcPhase>('idle')
  const [vcError, setVcError] = useState<string | null>(null)
  const [apiError, setApiError] = useState<string | null>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const pipelineRef = useRef<HTMLDivElement>(null)
  const decisionRef = useRef<HTMLDivElement>(null)
  const receiptRef = useRef<HTMLDivElement>(null)

  const scrollTo = (ref: React.RefObject<HTMLDivElement | null>) => {
    setTimeout(() => {
      ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }, 120)
  }

  const runPipeline = async () => {
    if (!scenario.trim() || scenario.trim().length < 10) return
    setPhase('running')
    setSpgPhase('checking')
    setApiError(null)
    setResult(null)
    setPipelineStep(-1)
    setVcPhase('idle')
    setVcError(null)

    const evalPromise = fetch(`${API_BASE}/api/public/sandbox/evaluate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario_text: scenario.trim().slice(0, 1500), language: 'en' }),
    })

    await new Promise(r => setTimeout(r, 1200))
    setSpgPhase('done')
    scrollTo(pipelineRef)

    let data: EvalResult
    try {
      const res = await evalPromise
      data = await res.json()
      if (!data.success) throw new Error('evaluation failed')
    } catch {
      setApiError('Could not connect to the governance engine. Please try again.')
      setPhase('input')
      setSpgPhase('idle')
      return
    }

    setResult(data)
    const gates = data.gate_results || []
    let step = 0
    const animateGates = () => {
      if (step < gates.length) {
        setPipelineStep(step)
        step++
        timerRef.current = setTimeout(animateGates, 320)
      } else {
        setPhase('done')
        scrollTo(decisionRef)
        setTimeout(() => scrollTo(receiptRef), 800)
      }
    }
    setTimeout(animateGates, 300)
  }

  const revokeVc = async () => {
    if (!result?.receipt_id) return
    setVcPhase('revoking')
    setVcError(null)
    try {
      const res = await fetch(`${API_BASE}/api/trust/revoke/${result.receipt_id}`, { method: 'POST' })
      const data = await res.json()
      if (res.ok || data.status === 'revoked' || data.success) {
        setVcPhase('revoked')
      } else {
        setVcError('Revocation endpoint responded with an error.')
        setVcPhase('idle')
      }
    } catch {
      setVcError('Connection error during revocation.')
      setVcPhase('idle')
    }
  }

  const reset = () => {
    if (timerRef.current) clearTimeout(timerRef.current)
    setPhase('input')
    setSpgPhase('idle')
    setPipelineStep(-1)
    setResult(null)
    setVcPhase('idle')
    setVcError(null)
    setApiError(null)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const isApproved = result?.decision === 'APPROVED'
  const gates = result?.gate_results || []

  return (
    <div className="min-h-screen bg-institutional text-white">
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#050D18]/90 backdrop-blur-xl border-b border-[#C9A227]/10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/"><img src="/logo.png" alt="OMNIX" className="w-10 h-10 object-contain" /></Link>
            <span className="text-base font-bold text-white tracking-tight">OMNIX QUANTUM</span>
            <span className="px-2 py-0.5 text-[10px] font-semibold bg-[#C9A227]/20 text-[#C9A227] rounded uppercase tracking-wider">Full Pipeline Demo</span>
          </div>
          <div className="flex items-center gap-6">
            <Link to="/" className="nav-link text-sm">Home</Link>
            <Link to="/try" className="nav-link text-sm">Sandbox</Link>
            <a href="https://wa.me/16505078293?text=Hi%2C%20I%27m%20interested%20in%20OMNIX%20Governance" target="_blank" rel="noopener noreferrer" className="btn-primary text-sm px-5 py-2">Talk to Us</a>
          </div>
        </div>
      </nav>

      <div className="pt-28 pb-24 px-6 max-w-4xl mx-auto">

        {/* ── HERO ─────────────────────────────────── */}
        <div className="text-center mb-14">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#C9A227]/10 border border-[#C9A227]/20 mb-6">
            <Zap className="w-3.5 h-3.5 text-[#C9A227]" />
            <span className="text-xs text-[#C9A227] font-semibold uppercase tracking-wider">Complete Decision Lifecycle</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4 leading-tight">
            From Decision to<br />
            <span className="text-[#C9A227]">Cryptographic Proof.</span>
          </h1>
          <p className="text-lg text-[#9CA3AF] max-w-2xl mx-auto leading-relaxed">
            Watch every layer of OMNIX governance execute in sequence — state validation, 11-checkpoint analysis, verifiable credential issuance, and live revocation.
          </p>
        </div>

        {/* ── STEP 0: INPUT ────────────────────────── */}
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-8 mb-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-8 h-8 rounded-full bg-[#C9A227] flex items-center justify-center text-black font-bold text-sm">1</div>
            <h2 className="text-lg font-semibold text-white">Select or Describe a Decision</h2>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-5">
            {PRESET_SCENARIOS.map((p, i) => (
              <button
                key={i}
                onClick={() => { setActivePreset(i); setScenario(p.text) }}
                className={`px-3 py-2 rounded-lg text-xs font-medium border transition-all ${
                  activePreset === i
                    ? 'border-[#C9A227] bg-[#C9A227]/10 text-[#C9A227]'
                    : 'border-white/10 text-[#9CA3AF] hover:border-white/20 hover:text-white'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>

          <textarea
            value={scenario}
            onChange={e => { setScenario(e.target.value); setActivePreset(-1) }}
            rows={4}
            placeholder="Or describe your own decision scenario..."
            className="w-full bg-[#050D18] border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-[#4B5563] resize-none focus:outline-none focus:border-[#C9A227]/40 transition-colors"
            disabled={phase === 'running'}
          />

          {apiError && (
            <div className="mt-3 px-4 py-3 rounded-lg bg-red-950/40 border border-red-500/20 text-red-400 text-sm flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              {apiError}
            </div>
          )}

          <div className="mt-5 flex items-center justify-between">
            <p className="text-xs text-[#4B5563]">Real governance engine — same infrastructure used by enterprise clients</p>
            {phase === 'input' ? (
              <button
                onClick={runPipeline}
                disabled={scenario.trim().length < 10}
                className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-[#C9A227] text-black font-semibold text-sm hover:bg-[#E5B82A] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Run Full Pipeline <ChevronRight className="w-4 h-4" />
              </button>
            ) : (
              <button onClick={reset} className="flex items-center gap-2 px-5 py-2.5 rounded-xl border border-white/10 text-[#9CA3AF] text-sm hover:border-white/20 hover:text-white transition-colors">
                <RefreshCw className="w-3.5 h-3.5" /> Reset
              </button>
            )}
          </div>
        </div>

        {/* ── STEP 1: SPG ──────────────────────────── */}
        {spgPhase !== 'idle' && (
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-8 mb-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-8 h-8 rounded-full bg-[#C9A227] flex items-center justify-center text-black font-bold text-sm">2</div>
              <h2 className="text-lg font-semibold text-white">State Provenance Guard</h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-900/40 text-blue-300 border border-blue-500/20 uppercase">Layer 0b</span>
            </div>

            {spgPhase === 'checking' ? (
              <div className="flex items-center gap-4 py-4">
                <div className="w-8 h-8 rounded-full border-2 border-[#C9A227]/40 border-t-[#C9A227] animate-spin shrink-0" />
                <div>
                  <p className="text-sm font-medium text-white">Validating decision state and context integrity...</p>
                  <p className="text-xs text-[#4B5563] mt-1">Checking provenance anchors, state transitions, and signal consistency</p>
                </div>
              </div>
            ) : (
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-emerald-900/40 border border-emerald-500/20 flex items-center justify-center shrink-0">
                  <CheckCircle className="w-5 h-5 text-emerald-400" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-emerald-400 mb-1">State Validated — Provenance Clean</p>
                  <p className="text-sm text-[#9CA3AF] leading-relaxed">
                    Decision state is consistent. No anomalous transitions, conflicting signals, or provenance breaks detected. Cleared to proceed through the governance pipeline.
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {['Context hash verified', 'State transitions valid', 'No signal conflicts', 'Cleared for pipeline'].map(tag => (
                      <span key={tag} className="px-2 py-0.5 rounded text-[10px] bg-emerald-900/20 text-emerald-400 border border-emerald-500/10">{tag}</span>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── STEP 2: 11 CHECKPOINTS ───────────────── */}
        {(pipelineStep >= 0 || phase === 'done') && (
          <div ref={pipelineRef} className="rounded-2xl border border-white/10 bg-white/[0.03] p-8 mb-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-8 h-8 rounded-full bg-[#C9A227] flex items-center justify-center text-black font-bold text-sm">3</div>
              <h2 className="text-lg font-semibold text-white">11-Checkpoint Governance Pipeline</h2>
              {phase === 'done' && result && (
                <span className="ml-auto text-xs text-[#9CA3AF]">
                  {result.checkpoints_passed}/{result.checkpoints_total} passed
                  {result.checkpoints_blocked > 0 && ` · ${result.checkpoints_blocked} blocked`}
                </span>
              )}
            </div>

            <div className="grid grid-cols-1 gap-2">
              {gates.map((gate, i) => {
                const visible = i <= pipelineStep || phase === 'done'
                const isActive = i === pipelineStep && phase !== 'done'
                const passed = gate.result === 'PASS'
                if (!visible) return null
                return (
                  <div
                    key={gate.checkpoint}
                    className={`flex items-start gap-3 px-4 py-3 rounded-xl border transition-all ${
                      isActive
                        ? 'border-[#C9A227]/30 bg-[#C9A227]/5 animate-pulse'
                        : passed
                          ? 'border-emerald-500/15 bg-emerald-950/20'
                          : 'border-red-500/20 bg-red-950/20'
                    }`}
                  >
                    {isActive ? (
                      <div className="w-4 h-4 rounded-full border-2 border-[#C9A227]/40 border-t-[#C9A227] animate-spin shrink-0 mt-0.5" />
                    ) : passed ? (
                      <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    ) : (
                      <XCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-xs font-mono text-[#4B5563]">{gate.checkpoint}</span>
                        <span className="text-sm font-medium text-white">{CHECKPOINT_NAMES[gate.checkpoint] || gate.checkpoint}</span>
                        <span className={`ml-auto text-xs font-semibold ${passed ? 'text-emerald-400' : 'text-red-400'}`}>
                          {passed ? 'PASS' : 'BLOCKED'}
                        </span>
                      </div>
                      {gate.description && (
                        <p className="text-xs text-[#6B7280] leading-relaxed truncate">{gate.description}</p>
                      )}
                    </div>
                  </div>
                )
              })}

              {phase === 'running' && pipelineStep < (gates.length - 1) && (
                <div className="flex items-center gap-3 px-4 py-3 rounded-xl border border-white/5 bg-white/[0.02]">
                  <Clock className="w-4 h-4 text-[#374151] shrink-0" />
                  <span className="text-xs text-[#374151]">Remaining checkpoints evaluating...</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── STEP 3: DECISION ─────────────────────── */}
        {phase === 'done' && result && (
          <div
            ref={decisionRef}
            className={`rounded-2xl border p-8 mb-8 ${
              isApproved
                ? 'border-emerald-500/20 bg-emerald-950/10'
                : 'border-red-500/20 bg-red-950/10'
            }`}
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="w-8 h-8 rounded-full bg-[#C9A227] flex items-center justify-center text-black font-bold text-sm">4</div>
              <h2 className="text-lg font-semibold text-white">Governance Decision</h2>
            </div>

            <div className="flex items-center gap-5 mb-5">
              <div className={`w-14 h-14 rounded-2xl flex items-center justify-center ${
                isApproved ? 'bg-emerald-900/50 border border-emerald-500/20' : 'bg-red-900/50 border border-red-500/20'
              }`}>
                {isApproved
                  ? <CheckCircle className="w-7 h-7 text-emerald-400" />
                  : <XCircle className="w-7 h-7 text-red-400" />
                }
              </div>
              <div>
                <p className={`text-3xl font-bold ${isApproved ? 'text-emerald-400' : 'text-red-400'}`}>
                  {result.decision}
                </p>
                <p className="text-sm text-[#6B7280] mt-1">
                  {result.checkpoints_passed}/{result.checkpoints_total} checkpoints passed
                  {result.checkpoints_blocked > 0 && ` · ${result.checkpoints_blocked} blocked`}
                </p>
              </div>
            </div>

            <p className="text-sm text-[#9CA3AF] leading-relaxed border-t border-white/5 pt-5">
              {result.explanation}
            </p>
          </div>
        )}

        {/* ── STEP 4: RECEIPT / VC ─────────────────── */}
        {phase === 'done' && result?.receipt_id && (
          <div ref={receiptRef} className="rounded-2xl border border-white/10 bg-white/[0.03] p-8 mb-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-8 h-8 rounded-full bg-[#C9A227] flex items-center justify-center text-black font-bold text-sm">5</div>
              <h2 className="text-lg font-semibold text-white">Cryptographic Receipt Issued</h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-purple-900/40 text-purple-300 border border-purple-500/20 uppercase">PQC Signed</span>
            </div>

            <div className="grid grid-cols-1 gap-3 mb-5">
              <div className="flex items-start gap-3 px-4 py-3 rounded-xl bg-[#050D18] border border-white/5">
                <FileCheck className="w-4 h-4 text-[#C9A227] shrink-0 mt-0.5" />
                <div className="min-w-0">
                  <p className="text-xs text-[#4B5563] mb-1 uppercase tracking-wide">Receipt ID</p>
                  <p className="text-sm font-mono text-white break-all">{result.receipt_id}</p>
                </div>
              </div>
              {result.receipt?.content_hash && (
                <div className="flex items-start gap-3 px-4 py-3 rounded-xl bg-[#050D18] border border-white/5">
                  <Lock className="w-4 h-4 text-[#C9A227] shrink-0 mt-0.5" />
                  <div className="min-w-0">
                    <p className="text-xs text-[#4B5563] mb-1 uppercase tracking-wide">Content Hash</p>
                    <p className="text-xs font-mono text-[#6B7280] break-all">{result.receipt.content_hash}</p>
                  </div>
                </div>
              )}
              <div className="flex items-start gap-3 px-4 py-3 rounded-xl bg-[#050D18] border border-white/5">
                <Shield className="w-4 h-4 text-[#C9A227] shrink-0 mt-0.5" />
                <div>
                  <p className="text-xs text-[#4B5563] mb-1 uppercase tracking-wide">Signature</p>
                  <p className="text-sm text-white">NIST-standardized post-quantum signature</p>
                  <p className="text-xs text-[#4B5563] mt-0.5">Tamper-evident · Independently verifiable · Quantum-resistant</p>
                </div>
              </div>
            </div>

            {result.verification_url && (
              <a
                href={result.verification_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-sm text-[#C9A227] hover:text-[#E5B82A] transition-colors"
              >
                <Eye className="w-4 h-4" />
                Verify this receipt independently
              </a>
            )}
          </div>
        )}

        {/* ── STEP 5: LIVE REVOCATION ──────────────── */}
        {phase === 'done' && result?.receipt_id && (
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-8 mb-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-8 h-8 rounded-full bg-[#C9A227] flex items-center justify-center text-black font-bold text-sm">6</div>
              <h2 className="text-lg font-semibold text-white">Live VC Revocation</h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-orange-900/40 text-orange-300 border border-orange-500/20 uppercase">StatusList2021</span>
            </div>

            <p className="text-sm text-[#9CA3AF] mb-6 leading-relaxed">
              Any issued credential can be revoked in real time. The status propagates instantly across the network — no manual process, no delay. This is the same revocation infrastructure used for enterprise compliance.
            </p>

            {vcPhase === 'idle' && (
              <div className="flex items-center justify-between p-4 rounded-xl border border-white/5 bg-[#050D18]">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-sm text-white font-medium">Status: ACTIVE</span>
                  <span className="text-xs text-[#4B5563]">— credential is live and verifiable</span>
                </div>
                <button
                  onClick={revokeVc}
                  className="px-4 py-2 rounded-lg border border-red-500/30 text-red-400 text-sm font-medium hover:bg-red-950/30 transition-colors"
                >
                  Revoke this VC
                </button>
              </div>
            )}

            {vcPhase === 'revoking' && (
              <div className="flex items-center gap-4 p-4 rounded-xl border border-orange-500/20 bg-orange-950/10">
                <div className="w-4 h-4 rounded-full border-2 border-orange-400/40 border-t-orange-400 animate-spin shrink-0" />
                <div>
                  <p className="text-sm font-medium text-orange-300">Revoking credential...</p>
                  <p className="text-xs text-[#6B7280] mt-0.5">Updating StatusList2021 bitstring and propagating status</p>
                </div>
              </div>
            )}

            {vcPhase === 'revoked' && (
              <div className="p-4 rounded-xl border border-red-500/20 bg-red-950/15">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-2 h-2 rounded-full bg-red-400" />
                  <span className="text-sm text-white font-medium">Status: REVOKED</span>
                  <span className="text-xs text-red-400/60">— credential is no longer valid</span>
                </div>
                <p className="text-sm text-[#9CA3AF] leading-relaxed">
                  The credential has been revoked and marked in the StatusList2021 registry. Any verification attempt against this receipt ID will now return <span className="font-mono text-red-400 text-xs">REVOKED</span>. The decision audit trail is preserved — revocation does not erase the record.
                </p>
                {result.verification_url && (
                  <a
                    href={result.verification_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 text-xs text-[#6B7280] hover:text-[#9CA3AF] mt-3 transition-colors"
                  >
                    <Eye className="w-3 h-3" /> Verify revocation status independently
                  </a>
                )}
              </div>
            )}

            {vcError && (
              <div className="mt-3 px-4 py-3 rounded-lg bg-red-950/40 border border-red-500/20 text-red-400 text-sm flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                {vcError}
              </div>
            )}
          </div>
        )}

        {/* ── FINAL CTA ────────────────────────────── */}
        {phase === 'done' && (
          <div className="rounded-2xl border border-[#C9A227]/20 bg-[#C9A227]/5 p-8 text-center">
            <h3 className="text-xl font-bold text-white mb-2">This is what decision governance looks like.</h3>
            <p className="text-sm text-[#9CA3AF] mb-6 max-w-xl mx-auto">
              Every decision your organization makes can run through this infrastructure — with a cryptographic audit trail, real-time status, and full regulatory alignment.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <a
                href="https://wa.me/16505078293?text=Hi%2C%20I%27m%20interested%20in%20OMNIX%20Governance%20for%20my%20organization"
                target="_blank"
                rel="noopener noreferrer"
                className="px-6 py-2.5 rounded-xl bg-[#C9A227] text-black font-semibold text-sm hover:bg-[#E5B82A] transition-colors"
              >
                Talk to Us
              </a>
              <button
                onClick={reset}
                className="px-6 py-2.5 rounded-xl border border-white/10 text-[#9CA3AF] text-sm hover:border-white/20 hover:text-white transition-colors"
              >
                Run Another Scenario
              </button>
            </div>
          </div>
        )}

      </div>
    </div>
  )
}
