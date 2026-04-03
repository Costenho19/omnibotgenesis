import { useState, useEffect, useRef } from 'react'
import QRCode from 'qrcode'
import { Link } from 'react-router-dom'
import { Shield, ArrowRight, CheckCircle, XCircle, Clock, Zap, Brain, Copy, ExternalLink, Sparkles, AlertTriangle, RefreshCw, ChevronDown, Download, Mail } from 'lucide-react'
import { useLiveMetrics } from '../hooks/useLiveMetrics'
import { API_BASE } from '../lib/apiBase'

interface GateResult {
  checkpoint: string
  name: string
  name_en: string
  name_es: string
  result: 'PASS' | 'BLOCKED'
  description: string
}

interface ReceiptData {
  receipt_id: string
  timestamp: string
  content_hash: string
  signature_algorithm: string
  pqc_signed: boolean
}

interface RealWorldImpact {
  potential_loss_pct_low: number
  potential_loss_pct_high: number
  liquidity_trap_risk: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  leverage_amplification_low: number
  leverage_amplification_high: number
  regulatory_breach: boolean
  capital_at_risk: number
  estimated_loss_avoided: number
  execution_prevented: boolean
}

interface EvaluationResult {
  success: boolean
  scenario_summary: string
  explanation: string
  language: string
  signals: Record<string, number>
  decision: 'APPROVED' | 'BLOCKED'
  asset: string
  domain: string
  checkpoints_total: number
  checkpoints_passed: number
  checkpoints_blocked: number
  gate_results: GateResult[]
  real_world_impact: RealWorldImpact | null
  receipt: ReceiptData | null
  receipt_id: string | null
  verification_url: string | null
}

interface ExampleScenario {
  text: string
  lang: string
  domain: string
  label?: string
}

const publicAlgorithmLabel = (alg?: string): string => {
  if (!alg) return 'NIST-standardized post-quantum signature'
  const a = alg.toLowerCase()
  if (a.includes('dilithium') || a.includes('kyber') || a.includes('ml-kem') || a.includes('ml-dsa')) {
    return 'NIST-standardized post-quantum signature'
  }
  return alg
}

const CHECKPOINT_ICONS: Record<string, string> = {
  'CP-1':  '🔍',
  'CP-2':  '📊',
  'CP-3':  '⚠️',
  'CP-4':  '🔗',
  'CP-5':  '📈',
  'CP-6':  '🛡️',
  'CP-7':  '⚖️',
  'CP-8':  '🧠',
  'CP-9':  '🏦',
  'CP-10': '🕵️',
  'CP-11': '🌐',
}

export default function PublicGovernanceSandbox() {
  const { metrics: liveMetrics, formatNumberFull } = useLiveMetrics()
  const [scenario, setScenario] = useState('')
  const [companyName, setCompanyName] = useState('')
  const [email, setEmail] = useState('')
  const [language, setLanguage] = useState<'auto' | 'en' | 'es'>('auto')
  const [isEvaluating, setIsEvaluating] = useState(false)
  const [result, setResult] = useState<EvaluationResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [currentCheckpoint, setCurrentCheckpoint] = useState(-1)
  const [animationComplete, setAnimationComplete] = useState(false)
  const [copied, setCopied] = useState(false)
  const [examples, setExamples] = useState<ExampleScenario[]>([])
  const [showExamples, setShowExamples] = useState(false)
  const [emailModalOpen, setEmailModalOpen] = useState(false)
  const [modalEmail, setModalEmail] = useState('')
  const [emailSending, setEmailSending] = useState(false)
  const [emailSent, setEmailSent] = useState(false)
  const [emailError, setEmailError] = useState<string | null>(null)
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
          scenario_text: scenario.trim().slice(0, 1500),
          ...(companyName ? { company_name: companyName } : {}),
          language: language === 'auto' ? 'en' : language,
          ...(email.trim() ? { email: email.trim() } : {}),
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
      ? `Acabo de probar OMNIX Decision Governance — ${result?.checkpoints_total} checkpoints evaluaron mi escenario y la decisión fue ${result?.decision}. Recibo firmado verificable: ${verifyUrl}\n\nPruébalo: `
      : `Just tried OMNIX Decision Governance — ${result?.checkpoints_total} checkpoints evaluated my scenario and the decision was ${result?.decision}. Signed verifiable receipt: ${verifyUrl}\n\nTry it: `
    const url = 'https://omnixquantum.net/try'
    window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}&summary=${encodeURIComponent(text)}`, '_blank')
  }

  const downloadPDF = async () => {
    if (!result) return
    const { jsPDF } = await import('jspdf')
    const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
    const W = 210
    const M = 15
    const CW = W - 2 * M
    const isApproved = result.decision === 'APPROVED'
    const isEs = result.language === 'es'
    const verifyUrl = result.verification_url || `https://omnixquantum.net/verify/${result.receipt_id}`
    let y = 0

    // ── HEADER ──────────────────────────────────────────────
    doc.setFillColor(5, 13, 24)
    doc.rect(0, 0, W, 34, 'F')

    // Logo OMNIX (569x379 px → ratio 1.502)
    const logoW = 28; const logoH = logoW / 1.502
    try {
      const logoResp = await fetch('/omnix_logo.png')
      const logoBlob = await logoResp.blob()
      const logoDataUrl = await new Promise<string>((resolve) => {
        const reader = new FileReader()
        reader.onload = () => resolve(reader.result as string)
        reader.readAsDataURL(logoBlob)
      })
      doc.addImage(logoDataUrl, 'PNG', M, (34 - logoH) / 2, logoW, logoH)
    } catch {
      // fallback: texto si el logo no carga
      doc.setTextColor(201, 162, 39); doc.setFont('helvetica', 'bold'); doc.setFontSize(20)
      doc.text('OMNIX', M, 15)
    }

    const textX = M + logoW + 5
    doc.setTextColor(180, 180, 180)
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(8)
    doc.text('DECISION GOVERNANCE INFRASTRUCTURE', textX, 14)
    doc.setTextColor(100, 100, 100)
    doc.setFontSize(6.5)
    doc.text('omnixquantum.net  |  contacto@omnixquantum.net', textX, 20)
    doc.setTextColor(130, 130, 130)
    doc.setFont('courier', 'normal')
    doc.setFontSize(6.5)
    doc.text(result.receipt_id || '', W - M, 14, { align: 'right' })
    doc.setFont('helvetica', 'normal')
    doc.text(new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }), W - M, 20, { align: 'right' })
    y = 34

    // ── DECISION BANNER ─────────────────────────────────────
    if (isApproved) {
      doc.setFillColor(6, 78, 59)
      doc.rect(0, y, W, 20, 'F')
      doc.setTextColor(52, 211, 153)
    } else {
      doc.setFillColor(69, 10, 10)
      doc.rect(0, y, W, 20, 'F')
      doc.setTextColor(252, 100, 100)
    }
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(20)
    doc.text(result.decision, W / 2, y + 9, { align: 'center' })
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(8)
    doc.setTextColor(isApproved ? 110 : 220, isApproved ? 200 : 120, isApproved ? 150 : 120)
    doc.text(
      `${result.checkpoints_passed}/${result.checkpoints_total} ${isEs ? 'checkpoints aprobados' : 'checkpoints passed'}${result.checkpoints_blocked > 0 ? `  —  ${result.checkpoints_blocked} ${isEs ? 'bloqueados' : 'blocked'}` : ''}`,
      W / 2, y + 15.5, { align: 'center' }
    )
    y += 25

    const sectionHeader = (title: string) => {
      doc.setFillColor(235, 236, 245)
      doc.rect(M, y, CW, 6.5, 'F')
      doc.setFont('helvetica', 'bold')
      doc.setFontSize(8.5)
      doc.setTextColor(30, 30, 60)
      doc.text(title, M + 2.5, y + 4.5)
      y += 9
    }

    const checkPage = (needed = 20) => {
      if (y + needed > 278) { doc.addPage(); y = 15 }
    }

    // ── GOVERNANCE ANALYSIS ──────────────────────────────────
    sectionHeader(isEs ? 'ANÁLISIS DE GOBERNANZA' : 'GOVERNANCE ANALYSIS')
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(8.5)
    doc.setTextColor(40, 40, 40)
    const explLines = doc.splitTextToSize(result.explanation || '', CW - 2)
    doc.text(explLines, M + 1, y)
    y += explLines.length * 4.8 + 7

    // ── EVALUATED SCENARIO ───────────────────────────────────
    if (scenario?.trim()) {
      checkPage(20)
      sectionHeader(isEs ? 'ESCENARIO EVALUADO' : 'EVALUATED SCENARIO')
      doc.setFont('helvetica', 'italic')
      doc.setFontSize(8)
      doc.setTextColor(70, 70, 90)
      const scLines = doc.splitTextToSize(`"${scenario.trim()}"`, CW - 4)
      doc.text(scLines, M + 2, y)
      y += scLines.length * 4.5 + 7
    }

    // ── 11-CHECKPOINT PIPELINE ───────────────────────────────
    checkPage(30)
    sectionHeader(isEs ? 'PIPELINE DE 11 CHECKPOINTS' : '11-CHECKPOINT PIPELINE')
    result.gate_results?.forEach((g: GateResult) => {
      checkPage(10)
      const passed = g.result === 'PASS'
      doc.setFillColor(passed ? 240 : 255, passed ? 253 : 242, passed ? 244 : 242)
      doc.rect(M, y - 1, CW, 7.5, 'F')
      doc.setFont('helvetica', 'bold')
      doc.setFontSize(7.5)
      doc.setTextColor(passed ? 5 : 153, passed ? 150 : 27, passed ? 58 : 27)
      doc.text(passed ? 'PASS' : 'FAIL', M + 2, y + 4)
      doc.setFont('helvetica', 'bold')
      doc.setFontSize(7.5)
      doc.setTextColor(60, 60, 90)
      doc.text(g.checkpoint, M + 16, y + 4)
      doc.setFont('helvetica', 'normal')
      doc.setTextColor(30, 30, 30)
      doc.text(g.name_en || g.name, M + 28, y + 4)
      y += 8
      if (g.description) {
        doc.setFont('helvetica', 'italic')
        doc.setFontSize(7)
        doc.setTextColor(100, 100, 120)
        const dLines = doc.splitTextToSize(g.description, CW - 22)
        doc.text(dLines, M + 20, y)
        y += dLines.length * 3.5 + 1.5
      }
    })
    y += 4

    // ── REAL-WORLD IMPACT ────────────────────────────────────
    if (result.real_world_impact) {
      const rwi = result.real_world_impact
      checkPage(45)
      sectionHeader(isEs ? 'IMPACTO ILUSTRATIVO (ESCENARIO HIPOTÉTICO)' : 'ILLUSTRATIVE IMPACT — HYPOTHETICAL SCENARIO')
      doc.setFontSize(8)
      const rows: [string, string][] = [
        [isEs ? 'Pérdida potencial de capital' : 'Potential capital loss', `${rwi.potential_loss_pct_low}% – ${rwi.potential_loss_pct_high}%`],
        [isEs ? 'Riesgo de trampa de liquidez' : 'Liquidity trap risk', rwi.liquidity_trap_risk],
        [isEs ? 'Amplificación por apalancamiento' : 'Leverage amplification', `${rwi.leverage_amplification_low}x – ${rwi.leverage_amplification_high}x`],
        [isEs ? 'Incumplimiento regulatorio' : 'Regulatory breach', rwi.regulatory_breach ? (isEs ? 'Sí' : 'Yes') : 'No'],
      ]
      rows.forEach(([label, value]) => {
        doc.setFont('helvetica', 'bold'); doc.setTextColor(80, 80, 100)
        doc.text(label + ':', M + 2, y)
        doc.setFont('helvetica', 'normal'); doc.setTextColor(20, 20, 20)
        doc.text(value, M + 90, y)
        y += 5.5
      })
      if (rwi.execution_prevented && rwi.estimated_loss_avoided > 0) {
        y += 2
        doc.setFillColor(92, 70, 10)
        doc.rect(M, y, CW, 16, 'F')
        doc.setFont('helvetica', 'bold'); doc.setFontSize(9); doc.setTextColor(251, 191, 36)
        doc.text(
          isEs ? `Pérdida ilustrativa evitada: $${rwi.estimated_loss_avoided.toLocaleString('en-US')}` : `Illustrative loss avoided: $${rwi.estimated_loss_avoided.toLocaleString('en-US')}`,
          W / 2, y + 6, { align: 'center' }
        )
        doc.setFont('helvetica', 'italic'); doc.setFontSize(6.5); doc.setTextColor(200, 170, 80)
        doc.text(
          isEs ? 'Estimación ilustrativa. No es una proyección financiera.' : 'Illustrative estimate based on hypothetical scenario inputs. Not a financial projection.',
          W / 2, y + 12, { align: 'center' }
        )
        y += 20
      } else {
        y += 3
      }
    }

    // ── CRYPTOGRAPHIC INTEGRITY ──────────────────────────────
    checkPage(55)
    sectionHeader(isEs ? 'INTEGRIDAD CRIPTOGRÁFICA' : 'CRYPTOGRAPHIC INTEGRITY')
    const cryptoRows: [string, string][] = [
      [isEs ? 'Algoritmo de firma' : 'Signature algorithm', publicAlgorithmLabel(result.receipt?.signature_algorithm)],
      [isEs ? 'Firmado PQC' : 'PQC signed', result.receipt?.pqc_signed ? (isEs ? 'Sí — resistente a computación cuántica' : 'Yes — quantum-resistant') : (isEs ? 'Modo sandbox — activo en producción' : 'Sandbox mode — active in production')],
      [isEs ? 'Hash del contenido' : 'Content hash', (result.receipt?.content_hash || '').slice(0, 32) + '...'],
    ]
    cryptoRows.forEach(([label, value]) => {
      doc.setFont('helvetica', 'bold'); doc.setFontSize(8); doc.setTextColor(80, 80, 100)
      doc.text(label + ':', M + 2, y)
      doc.setFont('courier', 'normal'); doc.setFontSize(7.5); doc.setTextColor(30, 30, 30)
      doc.text(value, M + 60, y)
      y += 5.5
    })
    y += 4

    // QR CODE — generate from verifyUrl using canvas (browser-safe)
    const QR_SIZE = 32  // mm in the PDF
    const TEXT_W = CW - QR_SIZE - 6  // text block width
    let qrDataUrl: string | null = null
    try {
      const canvas = document.createElement('canvas')
      await QRCode.toCanvas(canvas, verifyUrl, {
        width: 256, margin: 1,
        color: { dark: '#050D18', light: '#FFFFFF' }
      })
      qrDataUrl = canvas.toDataURL('image/png')
    } catch { /* fallback: no QR */ }

    // Dark verify box (left portion)
    doc.setFillColor(5, 13, 24)
    doc.rect(M, y, TEXT_W, 30, 'F')
    doc.setFont('helvetica', 'bold'); doc.setFontSize(7); doc.setTextColor(201, 162, 39)
    doc.text(isEs ? 'Verificar este recibo:' : 'Verify this receipt:', M + 3, y + 6)
    doc.setFont('courier', 'normal'); doc.setFontSize(6.5); doc.setTextColor(160, 170, 220)
    const urlLines = doc.splitTextToSize(verifyUrl, TEXT_W - 6)
    doc.text(urlLines, M + 3, y + 12)
    doc.setFont('helvetica', 'normal'); doc.setFontSize(6); doc.setTextColor(100, 110, 140)
    doc.text(isEs ? 'Escanea el QR o visita la URL para verificar' : 'Scan QR or visit URL to verify authenticity', M + 3, y + 25)

    // QR image (right portion)
    if (qrDataUrl) {
      doc.addImage(qrDataUrl, 'PNG', M + TEXT_W + 3, y - 1, QR_SIZE, QR_SIZE)
    }

    // Gold border around QR
    doc.setDrawColor(201, 162, 39); doc.setLineWidth(0.4)
    doc.rect(M + TEXT_W + 2, y - 2, QR_SIZE + 2, QR_SIZE + 2)
    y += QR_SIZE + 5

    // ── FOOTER ───────────────────────────────────────────────
    const footerY = 287
    doc.setDrawColor(201, 162, 39)
    doc.setLineWidth(0.3)
    doc.line(M, footerY, W - M, footerY)
    doc.setFont('helvetica', 'normal'); doc.setFontSize(6.5); doc.setTextColor(120, 120, 120)
    doc.text('OMNIX Decision Governance Infrastructure  |  omnixquantum.net  |  contacto@omnixquantum.net', W / 2, footerY + 4, { align: 'center' })
    doc.text(isEs ? `Generado: ${new Date().toLocaleString()}` : `Generated: ${new Date().toLocaleString()}`, W / 2, footerY + 8, { align: 'center' })

    doc.save(`OMNIX-Receipt-${result.receipt_id}.pdf`)
  }

  const openEmailModal = () => {
    if (!result) return
    setModalEmail(email.trim())
    setEmailSent(false)
    setEmailError(null)
    setEmailModalOpen(true)
  }

  const sendReceiptEmail = async () => {
    if (!result || !modalEmail.trim()) return
    setEmailSending(true)
    setEmailError(null)
    try {
      const res = await fetch(`${API_BASE}/api/public/send-receipt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recipient_email: modalEmail.trim(),
          receipt_id: result.receipt_id,
          decision: result.decision,
          explanation: result.explanation,
          scenario: scenario,
          language: result.language,
          gate_results: result.gate_results,
          receipt: result.receipt,
          checkpoints_passed: result.checkpoints_passed,
          checkpoints_total: result.checkpoints_total,
          checkpoints_blocked: result.checkpoints_blocked,
          verification_url: result.verification_url,
        }),
      })
      const data = await res.json()
      if (data.success) {
        setEmailSent(true)
      } else {
        setEmailError(data.error || 'Error sending email. Please try again.')
      }
    } catch {
      setEmailError('Connection error. Please try again.')
    } finally {
      setEmailSending(false)
    }
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
            <a href="https://wa.me/16505078293?text=Hi%2C%20I%27m%20interested%20in%20OMNIX%20Governance" target="_blank" rel="noopener noreferrer" className="btn-primary text-sm px-5 py-2">Talk to Us</a>
          </div>
        </div>
      </nav>

      <main className="pt-32 px-6 pb-20 max-w-5xl mx-auto">
        <section className="text-center mb-12 animate-fade-in-up">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#C9A227]/10 border border-[#C9A227]/20 mb-6">
            <Sparkles className="w-4 h-4 text-[#C9A227]" />
            <span className="text-sm text-[#C9A227] font-medium">Live Governance Pipeline</span>
          </div>
          <h1 className="heading-xl text-white mb-6">
            Watch the Governance Pipeline<br />
            <span className="gold-gradient">in Action.</span>
          </h1>
          <p className="text-xl text-muted max-w-3xl mx-auto mb-4 leading-relaxed">
            Select a real-world risk scenario. OMNIX evaluates it through its governance pipeline
            and determines one thing: should this decision be allowed to execute — or not?
          </p>
          <p className="text-base font-semibold text-white/80 max-w-2xl mx-auto mb-3">
            OMNIX does not optimize decisions. It prevents invalid ones from ever executing.
          </p>
          <p className="text-sm text-[#64748B] max-w-2xl mx-auto mb-1">
            Every result is returned as a cryptographically signed receipt, independently verifiable by anyone.
          </p>
          <p className="text-sm text-[#64748B] max-w-2xl mx-auto">
            {formatNumberFull(liveMetrics.evaluation_cycles)} evaluation cycles in production. No login required.
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
                      {ex.label && <span className="text-xs font-semibold text-white/80">{ex.label}</span>}
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
              rows={5}
              maxLength={1500}
              className="w-full bg-[#0A1628] border border-[#C9A227]/20 rounded-lg px-4 py-3 text-white text-sm focus:border-[#C9A227] focus:outline-none resize-none placeholder-gray-600 mb-4"
            />

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
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
                <label className="text-xs text-muted mb-1 block">Email — we'll follow up with your governance report</label>
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="e.g. you@company.com"
                  maxLength={254}
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
              <span className="text-xs text-muted">{scenario.length}/1500</span>
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
                {result.gate_results.length}-Checkpoint Pipeline
              </h3>
              <div className="space-y-3">
                {result.gate_results.map((gate, index) => {
                  const status = getCheckpointStatus(index)
                  const isPassed = gate.result === 'PASS'
                  return (
                    <div
                      key={index}
                      className={`glass-card p-5 transition-all duration-500 ${
                        status === 'animating' ? 'border-blue-500/60 shadow-lg shadow-blue-500/10' :
                        status === 'done' && isPassed ? 'border-emerald-500/30' :
                        status === 'done' && !isPassed ? 'border-red-500/30' :
                        'border-white/5'
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
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          {status === 'pending' ? (
                            <Clock className="w-5 h-5 text-gray-600" />
                          ) : status === 'animating' ? (
                            <RefreshCw className="w-5 h-5 text-blue-400 animate-spin" />
                          ) : isPassed ? (
                            <CheckCircle className="w-5 h-5 text-emerald-400" />
                          ) : (
                            <XCircle className="w-5 h-5 text-red-400" />
                          )}
                        </div>
                      </div>
                      {status !== 'pending' && (
                        <div className="mt-2 h-1.5 rounded-full bg-[#0A1628] overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-700 ${
                              isPassed ? 'bg-emerald-500' : 'bg-red-500'
                            }`}
                            style={{ width: isPassed ? '100%' : '22%' }}
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
                    {result.decision === 'BLOCKED' ? '🛡️ EXECUTION BLOCKED' : '✅ EXECUTION APPROVED'}
                  </h2>
                  <p className="text-muted mb-1">
                    {result.checkpoints_passed} checkpoints passed
                    {result.checkpoints_blocked > 0 && ` · ${result.checkpoints_blocked} blocked`}
                    {` · ${result.checkpoints_total} total evaluations`}
                  </p>
                  {result.decision === 'BLOCKED' && (
                    <p className="text-xs text-red-300/60 mb-3">
                      Final outcome: inadmissible decision state
                    </p>
                  )}
                  {result.decision === 'BLOCKED' && (
                    <div className="mt-2 mb-4 space-y-1">
                      <p className="text-sm text-red-300/80">
                        This decision was stopped before execution.
                      </p>
                      <p className="text-xs text-red-300/50">
                        The system detected structural inconsistency in the signal.
                      </p>
                      <p className="text-sm font-semibold text-white/90 mt-2">
                        No capital was committed. No risk was taken.
                      </p>
                      <p className="text-xs text-[#C9A227] font-medium italic">
                        This is how capital loss is prevented — before it happens.
                      </p>
                    </div>
                  )}
                  {result.explanation && (
                    <p className="text-sm text-gray-300 max-w-lg mx-auto mb-4 leading-relaxed italic">
                      {result.explanation}
                    </p>
                  )}

                  {result.real_world_impact && (
                    <div className="mt-6 text-left max-w-lg mx-auto">
                      <div className="rounded-xl border p-5 bg-amber-950/20 border-amber-500/30">

                        {/* Header */}
                        <div className="flex items-center gap-2 mb-3">
                          <AlertTriangle className="w-4 h-4 text-amber-400" />
                          <span className="text-sm font-bold tracking-wider text-white uppercase">
                            Illustrative Impact
                          </span>
                          <span className="ml-auto text-[9px] font-bold px-2 py-0.5 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30 tracking-widest uppercase">
                            Hypothetical Scenario
                          </span>
                        </div>

                        {/* Disclaimer top */}
                        <div className="mb-4 px-3 py-2 rounded-lg bg-amber-950/40 border border-amber-500/20">
                          <p className="text-[11px] text-amber-300/80 leading-relaxed">
                            <span className="font-semibold">Illustrative only.</span> These figures are generated from your hypothetical scenario text — not from live market data or real capital. Not a financial projection or investment advice.
                          </p>
                        </div>

                        <p className="text-xs text-gray-400 mb-3 italic">
                          Estimated consequence if this scenario were executed without governance:
                        </p>

                        <div className="space-y-2 mb-4">
                          <div className="flex items-center justify-between py-1.5 border-b border-white/5">
                            <span className="text-xs text-gray-400">Potential loss</span>
                            <span className="text-sm font-bold text-amber-400">
                              {result.real_world_impact.potential_loss_pct_low}%–{result.real_world_impact.potential_loss_pct_high}% of capital
                            </span>
                          </div>
                          <div className="flex items-center justify-between py-1.5 border-b border-white/5">
                            <span className="text-xs text-gray-400">Liquidity trap risk</span>
                            <span className={`text-sm font-bold ${
                              result.real_world_impact.liquidity_trap_risk === 'CRITICAL' ? 'text-red-400' :
                              result.real_world_impact.liquidity_trap_risk === 'HIGH' ? 'text-orange-400' :
                              result.real_world_impact.liquidity_trap_risk === 'MEDIUM' ? 'text-yellow-400' :
                              'text-emerald-400'
                            }`}>
                              {result.real_world_impact.liquidity_trap_risk}
                            </span>
                          </div>
                          <div className="flex items-center justify-between py-1.5 border-b border-white/5">
                            <span className="text-xs text-gray-400">Leverage amplification</span>
                            <span className="text-sm font-bold text-orange-400">
                              {result.real_world_impact.leverage_amplification_low}x–{result.real_world_impact.leverage_amplification_high}x downside
                            </span>
                          </div>
                          <div className="flex items-center justify-between py-1.5">
                            <span className="text-xs text-gray-400">Regulatory breach</span>
                            <span className={`text-sm font-bold ${result.real_world_impact.regulatory_breach ? 'text-red-400' : 'text-emerald-400'}`}>
                              {result.real_world_impact.regulatory_breach ? 'Internal limits violated' : 'Within bounds'}
                            </span>
                          </div>
                        </div>

                        <div className="rounded-lg p-4 bg-slate-900/60 border border-slate-600/30">
                          <p className="text-xs font-semibold text-slate-300 mb-2 tracking-wide uppercase">
                            Governance Outcome
                          </p>
                          <p className="text-xs text-gray-300 mb-2">
                            {result.real_world_impact.execution_prevented
                              ? '→ Governance pipeline would block execution before market exposure'
                              : '→ Scenario passes governance parameters'
                            }
                          </p>
                          {result.real_world_impact.execution_prevented && (
                            <>
                              <p className="text-base font-bold text-slate-200">
                                Illustrative loss avoided:{' '}
                                <span className="text-amber-400">
                                  ${result.real_world_impact.estimated_loss_avoided.toLocaleString('en-US')}
                                </span>
                              </p>
                              <p className="text-[10px] text-gray-500 mt-1.5 italic">
                                Illustrative estimate based on hypothetical scenario inputs. Not a financial projection.
                              </p>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

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
                          <span className="text-emerald-400">{publicAlgorithmLabel(result.receipt.signature_algorithm)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted">Hash</span>
                          <span className="text-white font-mono text-[10px]">{result.receipt.content_hash?.slice(0, 16)}...</span>
                        </div>
                      </div>
                      {result.receipt_id && (
                        <Link
                          to={`/verify/${result.receipt_id}`}
                          className="mt-3 flex items-center justify-center gap-1.5 text-xs font-semibold text-[#C9A227] hover:text-white transition-colors"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                          View Full Governance Report
                        </Link>
                      )}
                      {result.verification_url && (
                        <a
                          href={result.verification_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="mt-1.5 flex items-center justify-center gap-1.5 text-xs text-muted hover:text-white transition-colors"
                        >
                          <ExternalLink className="w-3 h-3" />
                          Independent ledger verification
                        </a>
                      )}
                    </div>
                  )}

                  <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
                    <button
                      onClick={downloadPDF}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 transition-colors text-sm border border-emerald-500/20"
                      title="Download governance report as PDF"
                    >
                      <Download className="w-4 h-4" />
                      Download PDF
                    </button>
                    <button
                      onClick={openEmailModal}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg bg-violet-500/10 text-violet-400 hover:bg-violet-500/20 transition-colors text-sm border border-violet-500/20"
                      title="Send receipt to your email"
                    >
                      <Mail className="w-4 h-4" />
                      Email Receipt
                    </button>
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
                      Try Another
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
                  <p className="text-xs text-muted">Same 11-checkpoint engine running 24/7 in production — not a simulation</p>
                </div>
                <div className="p-4 rounded-lg bg-[#0A1628]/40">
                  <ExternalLink className="w-6 h-6 text-[#C9A227] mx-auto mb-3" />
                  <h4 className="text-sm font-medium text-white mb-1">Verifiable Receipt</h4>
                  <p className="text-xs text-muted">Every evaluation generates a cryptographically signed receipt stored in PostgreSQL and verifiable publicly</p>
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

      {emailModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: 'rgba(0,0,0,0.7)' }}>
          <div className="bg-[#0D1B2E] border border-[#C9A227]/30 rounded-xl w-full max-w-md p-6 shadow-2xl">
            {!emailSent ? (
              <>
                <div className="flex items-center gap-3 mb-5">
                  <div className="w-9 h-9 rounded-lg bg-violet-500/20 flex items-center justify-center">
                    <Mail className="w-5 h-5 text-violet-400" />
                  </div>
                  <div>
                    <h3 className="text-white font-semibold text-base">
                      {result?.language === 'es' ? 'Enviar recibo por correo' : 'Send Receipt by Email'}
                    </h3>
                    <p className="text-muted text-xs mt-0.5">
                      {result?.language === 'es' ? 'Se enviará el reporte completo de gobernanza' : 'Full governance report will be sent'}
                    </p>
                  </div>
                </div>

                <label className="block text-sm text-[#A0AEC0] mb-1.5">
                  {result?.language === 'es' ? 'Dirección de correo electrónico' : 'Email address'}
                </label>
                <input
                  type="email"
                  value={modalEmail}
                  onChange={e => { setModalEmail(e.target.value); setEmailError(null) }}
                  placeholder="you@example.com"
                  className="w-full bg-[#0A1628] border border-[#1E3A5F] rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-[#C9A227] mb-4"
                  onKeyDown={e => { if (e.key === 'Enter' && !emailSending) sendReceiptEmail() }}
                  autoFocus
                />

                {emailError && (
                  <p className="text-red-400 text-xs mb-3 flex items-center gap-1">
                    <XCircle className="w-3.5 h-3.5" /> {emailError}
                  </p>
                )}

                <div className="flex gap-3">
                  <button
                    onClick={() => setEmailModalOpen(false)}
                    className="flex-1 px-4 py-2.5 rounded-lg border border-[#1E3A5F] text-[#A0AEC0] hover:text-white text-sm transition-colors"
                  >
                    {result?.language === 'es' ? 'Cancelar' : 'Cancel'}
                  </button>
                  <button
                    onClick={sendReceiptEmail}
                    disabled={emailSending || !modalEmail.trim()}
                    className="flex-1 px-4 py-2.5 rounded-lg bg-violet-600 hover:bg-violet-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium flex items-center justify-center gap-2 transition-colors"
                  >
                    {emailSending ? (
                      <><RefreshCw className="w-4 h-4 animate-spin" /> {result?.language === 'es' ? 'Enviando...' : 'Sending...'}</>
                    ) : (
                      <><Mail className="w-4 h-4" /> {result?.language === 'es' ? 'Enviar' : 'Send'}</>
                    )}
                  </button>
                </div>
              </>
            ) : (
              <div className="text-center py-4">
                <div className="w-14 h-14 rounded-full bg-emerald-500/20 flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="w-8 h-8 text-emerald-400" />
                </div>
                <h3 className="text-white font-semibold text-lg mb-2">
                  {result?.language === 'es' ? '¡Enviado!' : 'Sent!'}
                </h3>
                <p className="text-[#A0AEC0] text-sm mb-5">
                  {result?.language === 'es'
                    ? `El reporte fue enviado a ${modalEmail}`
                    : `Report sent to ${modalEmail}`}
                </p>
                <button
                  onClick={() => setEmailModalOpen(false)}
                  className="px-6 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium transition-colors"
                >
                  {result?.language === 'es' ? 'Cerrar' : 'Close'}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
