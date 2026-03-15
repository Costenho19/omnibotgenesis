import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { Shield, ArrowRight, CheckCircle, XCircle, Clock, Zap, Brain, Copy, ExternalLink, Sparkles, AlertTriangle, RefreshCw, ChevronDown } from 'lucide-react'
import { useLiveMetrics } from '../hooks/useLiveMetrics'

interface GateResult {
  checkpoint: string
  name: string
  name_en: string
  name_es: string
  score: number
  threshold: number
  result: 'PASS' | 'BLOCKED'
  description: string
  reasoning: string
}

interface ReceiptData {
  receipt_id: string
  timestamp: string
  content_hash: string
  signature_algorithm: string
  pqc_signed: boolean
}

interface EvaluationResult {
  success: boolean
  scenario_summary: string
  language: string
  signals: Record<string, number>
  decision: 'APPROVED' | 'BLOCKED'
  asset: string
  domain: string
  checkpoints_total: number
  checkpoints_passed: number
  checkpoints_blocked: number
  gate_results: GateResult[]
  receipt: ReceiptData | null
  receipt_id: string | null
  verification_url: string | null
}

interface ExampleScenario {
  text: string
  lang: string
  domain: string
}

const API_BASE = import.meta.env.VITE_FLASK_API_URL || ''

const CHECKPOINT_ICONS: Record<string, string> = {
  'CP-0': '🔍', 'CP-1': '📊', 'CP-2': '⚠️', 'CP-3': '🔗',
  'CP-4': '📈', 'CP-5': '🛡️', 'CP-6': '🧠', 'CP-7': '⏳',
}

export default function PublicGovernanceSandbox() {
  const { metrics: liveMetrics, formatNumberFull } = useLiveMetrics()
  const [scenario, setScenario] = useState('')
  const [companyName, setCompanyName] = useState('')
  const [language, setLanguage] = useState<'auto' | 'en' | 'es'>('auto')
  const [isEvaluating, setIsEvaluating] = useState(false)
  const [result, setResult] = useState<EvaluationResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [currentCheckpoint, setCurrentCheckpoint] = useState(-1)
  const [animationComplete, setAnimationComplete] = useState(false)
  const [copied, setCopied] = useState(false)
  const [examples, setExamples] = useState<ExampleScenario[]>([])
  const [showExamples, setShowExamples] = useState(false)
  const resultRef = useRef<HTMLDivElement>(null)
  const animTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    fetch(`${API_BASE}/api/public/sandbox/examples`)
      .then(r => r.json())
      .then(data => setExamples(data.examples || []))
      .catch(() => {})
  }, [])

  useEffect(() => {
    return () => {
      if (animTimerRef.current) clearTimeout(animTimerRef.current)
    }
  }, [])

  const runEvaluation = async () => {
    if (!scenario.trim() || scenario.trim().length < 10) return
    setIsEvaluating(true)
    setResult(null)
    setError(null)
    setCurrentCheckpoint(-1)
    setAnimationComplete(false)

    try {
      const res = await fetch(`${API_BASE}/api/public/sandbox/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario_text: scenario.trim().slice(0, 500),
          ...(companyName ? { company_name: companyName } : {}),
          ...(language !== 'auto' ? { language } : {}),
        }),
      })

      if (res.status === 429) {
        setError('Rate limit: max 5 per minute. Wait a moment and try again.\nLímite: máximo 5 por minuto. Espere un momento.')
        setIsEvaluating(false)
        return
      }

      const data = await res.json()
      if (!data.success) {
        setError(data.error || data.error_es || 'Evaluation failed')
        setIsEvaluating(false)
        return
      }

      setResult(data)
      setIsEvaluating(false)

      let step = 0
      const totalGates = data.gate_results?.length || 0
      const animate = () => {
        if (step < totalGates) {
          setCurrentCheckpoint(step)
          step++
          animTimerRef.current = setTimeout(animate, 350)
        } else {
          setAnimationComplete(true)
        }
      }
      animTimerRef.current = setTimeout(() => {
        animate()
        if (resultRef.current) {
          resultRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }
      }, 200)

    } catch {
      setError('Connection error. Please try again.\nError de conexión. Intente de nuevo.')
      setIsEvaluating(false)
    }
  }

  const copyReceiptId = () => {
    if (result?.receipt_id) {
      navigator.clipboard.writeText(result.receipt_id)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const shareOnLinkedIn = () => {
    const verifyUrl = result?.verification_url || ''
    const text = result?.language === 'es'
      ? `Acabo de probar OMNIX Decision Governance — ${result?.checkpoints_total} checkpoints evaluaron mi escenario y la decisión fue ${result?.decision}. Recibo PQC-firmado verificable: ${verifyUrl}\n\nPruébalo: `
      : `Just tried OMNIX Decision Governance — ${result?.checkpoints_total} checkpoints evaluated my scenario and the decision was ${result?.decision}. PQC-signed verifiable receipt: ${verifyUrl}\n\nTry it: `
    const url = 'https://omnixquantum.net/try'
    window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}&summary=${encodeURIComponent(text)}`, '_blank')
  }

  const useExample = (ex: ExampleScenario) => {
    setScenario(ex.text)
    setShowExamples(false)
    setResult(null)
    setError(null)
    setAnimationComplete(false)
    setCurrentCheckpoint(-1)
  }

  const getCheckpointStatus = (index: number): 'pending' | 'animating' | 'done' => {
    if (!result) return 'pending'
    if (index > currentCheckpoint) return 'pending'
    if (index === currentCheckpoint && !animationComplete) return 'animating'
    return 'done'
  }

  return (
    <div className="min-h-screen bg-institutional">
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#050D18]/90 backdrop-blur-xl border-b border-[#C9A227]/10">
        <div className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/">
              <img src="/logo.png" alt="OMNIX QUANTUM" className="w-12 h-12 object-contain" />
            </Link>
            <div>
              <span className="text-lg font-bold text-white tracking-tight">OMNIX QUANTUM</span>
              <span className="ml-3 px-2 py-0.5 text-[10px] font-semibold bg-[#C9A227]/20 text-[#C9A227] rounded uppercase tracking-wider">Try It Live</span>
            </div>
          </div>
          <div className="flex items-center gap-8">
            <Link to="/" className="nav-link">Home</Link>
            <Link to="/governance-demo" className="nav-link">Demos</Link>
            <Link to="/institutional" className="nav-link">Technical Details</Link>
            <a href="https://wa.me/16504815494?text=Hi%2C%20I%27m%20interested%20in%20OMNIX%20Governance" target="_blank" rel="noopener noreferrer" className="btn-primary text-sm px-5 py-2">Talk to Us</a>
          </div>
        </div>
      </nav>

      <main className="pt-32 px-6 pb-20 max-w-5xl mx-auto">
        <section className="text-center mb-12 animate-fade-in-up">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#C9A227]/10 border border-[#C9A227]/20 mb-6">
            <Sparkles className="w-4 h-4 text-[#C9A227]" />
            <span className="text-sm text-[#C9A227] font-medium">Public Governance Sandbox</span>
          </div>
          <h1 className="heading-xl text-white mb-6">
            Describe Any Decision.<br />
            <span className="gold-gradient">Watch 8 Checkpoints Judge It.</span>
          </h1>
          <p className="text-xl text-muted max-w-3xl mx-auto mb-2 leading-relaxed">
            Type any high-stakes scenario in plain English or Spanish. OMNIX's AI interprets it, runs it through
            the real 8-checkpoint governance pipeline, and generates a cryptographically signed, publicly verifiable receipt.
          </p>
          <p className="text-sm text-[#64748B] max-w-2xl mx-auto">
            Same engine validated across {formatNumberFull(liveMetrics.evaluation_cycles)} evaluation cycles. No login required.
          </p>
        </section>

        <section className="mb-12">
          <div className="glass-card p-8">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-[#C9A227]/20 flex items-center justify-center">
                  <Brain className="w-5 h-5 text-[#C9A227]" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">Your Scenario</h3>
                  <p className="text-xs text-muted">Describe any high-stakes decision in English or Spanish</p>
                </div>
              </div>
              {examples.length > 0 && (
                <button
                  onClick={() => setShowExamples(!showExamples)}
                  className="flex items-center gap-1.5 text-sm text-[#C9A227] hover:text-white transition-colors"
                >
                  Examples
                  <ChevronDown className={`w-4 h-4 transition-transform ${showExamples ? 'rotate-180' : ''}`} />
                </button>
              )}
            </div>

            {showExamples && (
              <div className="mb-4 space-y-2">
                {examples.map((ex, i) => (
                  <button
                    key={i}
                    onClick={() => useExample(ex)}
                    className="w-full text-left p-3 rounded-lg bg-[#0A1628]/60 border border-[#C9A227]/10 hover:border-[#C9A227]/30 transition-colors"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs px-2 py-0.5 rounded bg-[#C9A227]/10 text-[#C9A227] uppercase">{ex.domain}</span>
                      <span className="text-xs text-muted">{ex.lang === 'es' ? 'Español' : 'English'}</span>
                    </div>
                    <p className="text-sm text-muted line-clamp-2">{ex.text}</p>
                  </button>
                ))}
              </div>
            )}

            <textarea
              value={scenario}
              onChange={e => setScenario(e.target.value)}
              placeholder="Example: A hedge fund wants to open a $5M long position on a cryptocurrency that surged 40% in 24 hours with unusual volume but declining on-chain metrics..."
              rows={4}
              maxLength={500}
              className="w-full bg-[#0A1628] border border-[#C9A227]/20 rounded-lg px-4 py-3 text-white text-sm focus:border-[#C9A227] focus:outline-none resize-none placeholder-gray-600 mb-4"
            />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="text-xs text-muted mb-1 block">Company / Entity Name (optional)</label>
                <input
                  type="text"
                  value={companyName}
                  onChange={e => setCompanyName(e.target.value)}
                  placeholder="e.g. Acme Capital"
                  maxLength={100}
                  className="w-full bg-[#0A1628] border border-[#C9A227]/20 rounded-lg px-4 py-2.5 text-white text-sm focus:border-[#C9A227] focus:outline-none placeholder-gray-600"
                />
              </div>
              <div>
                <label className="text-xs text-muted mb-1 block">Language</label>
                <div className="flex gap-2">
                  {(['auto', 'en', 'es'] as const).map(lang => (
                    <button
                      key={lang}
                      onClick={() => setLanguage(lang)}
                      className={`px-4 py-2.5 rounded-lg text-sm border transition-colors ${language === lang ? 'bg-[#C9A227]/20 border-[#C9A227] text-[#C9A227]' : 'bg-[#0A1628] border-[#C9A227]/20 text-muted hover:border-[#C9A227]/40'}`}
                    >
                      {lang === 'auto' ? 'Auto-detect' : lang === 'en' ? 'English' : 'Español'}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-xs text-muted">{scenario.length}/500</span>
              <button
                onClick={runEvaluation}
                disabled={isEvaluating || scenario.trim().length < 10}
                className={`btn-primary flex items-center gap-2 px-8 py-3 ${isEvaluating || scenario.trim().length < 10 ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                {isEvaluating ? (
                  <>
                    <RefreshCw className="w-5 h-5 animate-spin" />
                    Analyzing with AI + Running Pipeline...
                  </>
                ) : (
                  <>
                    <Shield className="w-5 h-5" />
                    Run Governance Evaluation
                  </>
                )}
              </button>
            </div>
          </div>
        </section>

        {error && (
          <div className="mb-8 glass-card p-6 border-red-500/30">
            <div className="flex items-center gap-3 text-red-400">
              <AlertTriangle className="w-5 h-5 flex-shrink-0" />
              <p className="text-sm whitespace-pre-line">{error}</p>
            </div>
          </div>
        )}

        {result && (
          <div ref={resultRef}>
            {result.scenario_summary && (
              <div className="mb-6 glass-card p-6">
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles className="w-4 h-4 text-[#C9A227]" />
                  <span className="text-sm font-medium text-[#C9A227]">AI Interpretation</span>
                  <span className="text-xs px-2 py-0.5 rounded bg-[#0A1628] text-muted uppercase">{result.domain}</span>
                  <span className="text-xs px-2 py-0.5 rounded bg-[#0A1628] text-muted">{result.asset}</span>
                </div>
                <p className="text-muted text-sm">{result.scenario_summary}</p>
              </div>
            )}

            <div className="mb-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Shield className="w-5 h-5 text-[#C9A227]" />
                8-Checkpoint Pipeline
              </h3>
              <div className="space-y-3">
                {result.gate_results.map((gate, index) => {
                  const status = getCheckpointStatus(index)
                  const isPassed = gate.result === 'PASS'
                  return (
                    <div
                      key={index}
                      className={`glass-card p-5 transition-all duration-500 ${
                        status === 'pending' ? 'opacity-30' :
                        status === 'animating' ? 'border-blue-500/60 shadow-lg shadow-blue-500/10' :
                        isPassed ? 'border-emerald-500/30' : 'border-red-500/30'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-xl">{CHECKPOINT_ICONS[gate.checkpoint] || '🔷'}</span>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-mono text-[#C9A227]">{gate.checkpoint}</span>
                              <span className="text-sm font-medium text-white">
                                {result.language === 'es' ? gate.name_es : gate.name_en}
                              </span>
                            </div>
                            {status !== 'pending' && gate.reasoning && (
                              <p className="text-xs text-muted mt-1 max-w-xl">{gate.reasoning}</p>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          {status === 'pending' ? (
                            <Clock className="w-5 h-5 text-gray-600" />
                          ) : status === 'animating' ? (
                            <RefreshCw className="w-5 h-5 text-blue-400 animate-spin" />
                          ) : isPassed ? (
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-mono text-emerald-400">{gate.score.toFixed(0)} / {gate.threshold}</span>
                              <CheckCircle className="w-5 h-5 text-emerald-400" />
                            </div>
                          ) : (
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-mono text-red-400">{gate.score.toFixed(0)} / {gate.threshold}</span>
                              <XCircle className="w-5 h-5 text-red-400" />
                            </div>
                          )}
                        </div>
                      </div>
                      {status !== 'pending' && (
                        <div className="mt-2 h-1.5 rounded-full bg-[#0A1628] overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-700 ${
                              isPassed ? 'bg-emerald-500' : 'bg-red-500'
                            }`}
                            style={{ width: `${Math.min(100, gate.score)}%` }}
                          />
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>

            {animationComplete && (
              <div className="animate-fade-in-up">
                <div className={`glass-card p-8 mb-6 text-center ${
                  result.decision === 'APPROVED'
                    ? 'border-emerald-500/40 shadow-lg shadow-emerald-500/10'
                    : 'border-red-500/40 shadow-lg shadow-red-500/10'
                }`}>
                  <div className={`w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 ${
                    result.decision === 'APPROVED' ? 'bg-emerald-500/20' : 'bg-red-500/20'
                  }`}>
                    {result.decision === 'APPROVED'
                      ? <CheckCircle className="w-8 h-8 text-emerald-400" />
                      : <XCircle className="w-8 h-8 text-red-400" />
                    }
                  </div>
                  <h2 className={`text-3xl font-bold mb-2 ${
                    result.decision === 'APPROVED' ? 'text-emerald-400' : 'text-red-400'
                  }`}>
                    {result.decision}
                  </h2>
                  <p className="text-muted mb-4">
                    {result.checkpoints_passed}/{result.checkpoints_total} checkpoints passed
                    {result.checkpoints_blocked > 0 && ` — ${result.checkpoints_blocked} blocked`}
                  </p>

                  {result.receipt && (
                    <div className="mt-6 p-4 rounded-lg bg-[#0A1628]/60 border border-[#C9A227]/20 text-left max-w-md mx-auto">
                      <div className="flex items-center gap-2 mb-3">
                        <Shield className="w-4 h-4 text-[#C9A227]" />
                        <span className="text-sm font-medium text-[#C9A227]">
                          {result.receipt.pqc_signed ? 'PQC-Signed Receipt' : 'Governance Receipt'}
                        </span>
                      </div>
                      <div className="space-y-2 text-xs">
                        <div className="flex justify-between">
                          <span className="text-muted">Receipt ID</span>
                          <div className="flex items-center gap-1.5">
                            <span className="text-white font-mono">{result.receipt_id}</span>
                            <button onClick={copyReceiptId} className="text-[#C9A227] hover:text-white transition-colors">
                              {copied ? <CheckCircle className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                            </button>
                          </div>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted">Signature</span>
                          <span className="text-emerald-400">{result.receipt.signature_algorithm}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted">Hash</span>
                          <span className="text-white font-mono text-[10px]">{result.receipt.content_hash?.slice(0, 16)}...</span>
                        </div>
                      </div>
                      {result.verification_url && (
                        <a
                          href={result.verification_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="mt-3 flex items-center justify-center gap-1.5 text-xs text-[#C9A227] hover:text-white transition-colors"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                          Verify on Public Server
                        </a>
                      )}
                    </div>
                  )}

                  <div className="mt-6 flex items-center justify-center gap-4">
                    <button
                      onClick={shareOnLinkedIn}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#0A66C2]/20 text-[#0A66C2] hover:bg-[#0A66C2]/30 transition-colors text-sm"
                    >
                      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
                      Share on LinkedIn
                    </button>
                    <button
                      onClick={() => { setResult(null); setScenario(''); setAnimationComplete(false); setCurrentCheckpoint(-1) }}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#C9A227]/10 text-[#C9A227] hover:bg-[#C9A227]/20 transition-colors text-sm"
                    >
                      <RefreshCw className="w-4 h-4" />
                      Try Another Scenario
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {!result && !isEvaluating && (
          <section className="mt-16">
            <div className="glass-card p-8 text-center">
              <h3 className="text-lg font-semibold text-white mb-6">What Makes This Different from Our Other Demos</h3>
              <div className="grid md:grid-cols-3 gap-6">
                <div className="p-4 rounded-lg bg-[#0A1628]/40">
                  <Zap className="w-6 h-6 text-[#C9A227] mx-auto mb-3" />
                  <h4 className="text-sm font-medium text-white mb-1">Real AI Interpretation</h4>
                  <p className="text-xs text-muted">Gemini AI converts your plain-text scenario into structured governance signals</p>
                </div>
                <div className="p-4 rounded-lg bg-[#0A1628]/40">
                  <Shield className="w-6 h-6 text-[#C9A227] mx-auto mb-3" />
                  <h4 className="text-sm font-medium text-white mb-1">Real Pipeline</h4>
                  <p className="text-xs text-muted">Same 8-checkpoint engine running 24/7 in production — not a simulation</p>
                </div>
                <div className="p-4 rounded-lg bg-[#0A1628]/40">
                  <ExternalLink className="w-6 h-6 text-[#C9A227] mx-auto mb-3" />
                  <h4 className="text-sm font-medium text-white mb-1">Verifiable Receipt</h4>
                  <p className="text-xs text-muted">Every evaluation generates a PQC-signed receipt stored in PostgreSQL and verifiable publicly</p>
                </div>
              </div>
            </div>

            <div className="mt-12 text-center space-y-3">
              <Link to="/governance-demo" className="text-emerald-400 hover:text-white transition-colors flex items-center justify-center gap-2">
                See structured demos (Credit, Insurance, Energy, Biotech)
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link to="/institutional" className="text-[#C9A227] hover:text-white transition-colors flex items-center justify-center gap-2">
                Technical architecture details
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </section>
        )}
      </main>

      <footer className="border-t border-[#C9A227]/10 py-12 px-6">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-3">
            <img src="/logo.png" alt="OMNIX" className="w-10 h-10 object-contain" />
            <span className="text-muted text-sm">&copy; 2026 OMNIX QUANTUM. All rights reserved.</span>
          </div>
          <div className="flex items-center gap-6">
            <Link to="/" className="text-muted hover:text-white text-sm transition-colors">Home</Link>
            <Link to="/governance-demo" className="text-muted hover:text-white text-sm transition-colors">Credit Demo</Link>
            <Link to="/governance-demo-insurance" className="text-muted hover:text-white text-sm transition-colors">Insurance Demo</Link>
            <Link to="/governance-demo-energy" className="text-muted hover:text-white text-sm transition-colors">Energy Demo</Link>
            <Link to="/governance-demo-biotech" className="text-muted hover:text-white text-sm transition-colors">Biotech Demo</Link>
            <Link to="/institutional" className="text-muted hover:text-white text-sm transition-colors">Technical Details</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
