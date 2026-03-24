import React, { useState } from 'react'
import { Shield, ArrowRight, CheckCircle, Lock, Zap, Phone, Mail, Send, Loader2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useLiveMetrics } from '../hooks/useLiveMetrics'

const liveStatStyle = (animKey: number): React.CSSProperties => ({
  animation: animKey > 0 ? 'omnixStatReveal 0.6s ease both' : 'none',
})

const REFERRAL_OPTIONS = [
  'Facebook', 'WhatsApp', 'Instagram', 'Telegram',
  'LinkedIn', 'Google', 'Recomendación', 'Otro'
]

export default function CommercialLanding() {
  const { metrics, isLive, formatNumber, formatNumberFull, animKey } = useLiveMetrics()
  const [formData, setFormData] = useState({
    name: '', company: '', email: '', referral_source: '', message: ''
  })
  const [formStatus, setFormStatus] = useState<'idle' | 'sending' | 'success' | 'error'>('idle')
  const [formError, setFormError] = useState('')

  const handleFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }))
  }

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormStatus('sending')
    setFormError('')

    try {
      const res = await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })
      const data = await res.json()

      if (data.success) {
        setFormStatus('success')
        setFormData({ name: '', company: '', email: '', referral_source: '', message: '' })
      } else {
        setFormStatus('error')
        if (data.fallback_email) {
          setFormError(`Could not save your information. Please email us at ${data.fallback_email}`)
        } else {
          setFormError(data.error || 'Something went wrong. Please try again.')
        }
      }
    } catch {
      setFormStatus('error')
      setFormError('Connection error. Please email us at contacto@omnixquantum.net')
    }
  }
  
  return (
    <div className="min-h-screen bg-institutional">
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#050D18]/90 backdrop-blur-xl border-b border-[#C9A227]/10">
        <div className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <img src="/logo.png" alt="OMNIX QUANTUM" className="w-16 h-16 object-contain" />
            <div>
              <span className="text-lg font-bold text-white tracking-tight">OMNIX QUANTUM</span>
            </div>
          </div>
          <div className="flex items-center gap-8">
            <Link to="/try" className="nav-link font-semibold text-[#C9A227]">Try OMNIX</Link>
            <Link to="/institutional" className="nav-link">Technical Details</Link>
            <a href="https://wa.me/16504815494?text=Hi%2C%20I%27m%20interested%20in%20OMNIX" target="_blank" rel="noopener noreferrer" className="btn-primary">Talk to Us</a>
          </div>
        </div>
      </nav>

      <main className="pt-32 px-6 pb-20 max-w-6xl mx-auto">
        <section className="text-center mb-24 animate-fade-in-up">
          <h1 className="heading-xl text-white mb-8 leading-tight">
            Stop Costly Mistakes <br />
            <span className="gold-gradient">Before They Happen</span>
          </h1>
          <p className="text-2xl text-muted max-w-3xl mx-auto mb-6 leading-relaxed">
            OMNIX is a governance control architecture for automated decision systems. It blocks high-risk decisions before they cause damage. First validated in digital asset trading. Future verticals (Year 2-3+): robotics, biotech, supply chain, lending, and insurance.
          </p>
          <p className="text-base italic text-[#C9A227]/80 max-w-2xl mx-auto mb-12 pl-4 border-l-2 border-[#C9A227]/40">
            "OMNIX doesn't just follow rules. It understands when and why they should apply."
          </p>
          <div className="flex justify-center gap-4 flex-wrap">
            <Link to="/try" className="btn-primary text-lg px-8 py-4 flex items-center gap-2">
              Try OMNIX Live
              <ArrowRight className="w-5 h-5" />
            </Link>
            <a href="https://wa.me/16504815494?text=Hi%2C%20I%27m%20interested%20in%20OMNIX" target="_blank" rel="noopener noreferrer" className="btn-secondary text-lg px-8 py-4 flex items-center gap-2">
              <Phone className="w-5 h-5" />
              Talk to Us
            </a>
          </div>
        </section>

        <section className="mb-24">
          <div className="grid md:grid-cols-3 gap-8">
            <div className="glass-card p-8 text-center">
              <div className="w-16 h-16 rounded-full bg-[#C9A227]/20 flex items-center justify-center mx-auto mb-6">
                <Shield className="w-8 h-8 gold-text" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-4">Decision Governance</h3>
              <p className="text-muted leading-relaxed">
                Every high-stakes decision is validated through 8 independent checkpoints before execution.
              </p>
            </div>

            <div className="glass-card p-8 text-center">
              <div className="w-16 h-16 rounded-full bg-[#C9A227]/20 flex items-center justify-center mx-auto mb-6">
                <Zap className="w-8 h-8 gold-text" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-4">Works with Your Tools</h3>
              <p className="text-muted leading-relaxed">
                Connects to your existing decision infrastructure. No need to change how you operate.
              </p>
            </div>

            <div className="glass-card p-8 text-center">
              <div className="w-16 h-16 rounded-full bg-[#C9A227]/20 flex items-center justify-center mx-auto mb-6">
                <Lock className="w-8 h-8 gold-text" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-4">Bank-Grade Security</h3>
              <p className="text-muted leading-relaxed">
                Your data is protected with the same cryptography used by financial institutions.
              </p>
            </div>
          </div>
        </section>

        <section className="mb-24">
          <div className="glass-card p-12 gold-glow">
            <h2 className="text-3xl font-bold text-white text-center mb-8">How It Works</h2>
            <div className="grid md:grid-cols-4 gap-8">
              <div className="text-center">
                <div className="w-12 h-12 rounded-full bg-[#C9A227] text-[#0A1628] font-bold text-xl flex items-center justify-center mx-auto mb-4">1</div>
                <p className="text-white font-medium">You face a high-stakes decision</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 rounded-full bg-[#C9A227] text-[#0A1628] font-bold text-xl flex items-center justify-center mx-auto mb-4">2</div>
                <p className="text-white font-medium">OMNIX validates it through 8 checkpoints</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 rounded-full bg-[#C9A227] text-[#0A1628] font-bold text-xl flex items-center justify-center mx-auto mb-4">3</div>
                <p className="text-white font-medium">Risky actions get blocked</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 rounded-full bg-[#C9A227] text-[#0A1628] font-bold text-xl flex items-center justify-center mx-auto mb-4">4</div>
                <p className="text-white font-medium">Only validated decisions proceed</p>
              </div>
            </div>
          </div>
        </section>

        <style>{`
          @keyframes omnixStatReveal {
            from { opacity: 0; transform: translateY(10px); }
            to   { opacity: 1; transform: translateY(0); }
          }
          @keyframes omnixPulse {
            0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(34,197,94,0.4); }
            50%       { opacity: 0.8; box-shadow: 0 0 0 5px rgba(34,197,94,0); }
          }
          .omnix-live-dot {
            width: 8px; height: 8px; border-radius: 50%;
            background: #22c55e;
            display: inline-block;
            margin-right: 6px;
            animation: omnixPulse 2s infinite;
          }
        `}</style>

        <section className="mb-24">
          <div className="glass-card p-12">
            <div className="flex items-center justify-center gap-3 mb-2">
              <h2 className="text-3xl font-bold text-white">Live Production Data</h2>
              {isLive && (
                <span className="flex items-center gap-1.5 text-xs font-semibold text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 px-2.5 py-1 rounded-full">
                  <span className="omnix-live-dot" />
                  LIVE
                </span>
              )}
            </div>
            <p className="text-sm text-center text-muted mb-8">Internal dataset, not externally audited</p>

            <div key={animKey} className="grid grid-cols-2 md:grid-cols-3 gap-8 text-center mb-6">
              <div style={liveStatStyle(animKey)}>
                <div className="text-3xl font-bold gold-text">{formatNumberFull(metrics.evaluation_cycles)}</div>
                <div className="text-sm text-muted mt-1">Evaluation Cycles</div>
              </div>
              <div style={{ ...liveStatStyle(animKey), animationDelay: '0.08s' }}>
                <div className="text-3xl font-bold text-emerald-400">{formatNumber(metrics.pqc_signed_receipts)}</div>
                <div className="text-sm text-muted mt-1">PQC-Signed Receipts</div>
              </div>
              <div style={{ ...liveStatStyle(animKey), animationDelay: '0.16s' }}>
                <div className="text-3xl font-bold text-white">{metrics.capital_preserved_pct}%</div>
                <div className="text-sm text-muted mt-1">Capital Preserved</div>
              </div>
              <div style={{ ...liveStatStyle(animKey), animationDelay: '0.24s' }}>
                <div className="text-3xl font-bold gold-text">{metrics.verticals_demo}</div>
                <div className="text-sm text-muted mt-1">Vertical Demos</div>
              </div>
              <div style={{ ...liveStatStyle(animKey), animationDelay: '0.32s' }} className="md:col-span-2">
                <div className="flex items-center justify-center gap-2">
                  <div className="text-3xl font-bold text-violet-400">{metrics.ebip_score}</div>
                  <div className="text-lg font-bold text-muted/60">/ 100</div>
                </div>
                <div className="text-sm text-muted mt-1">Execution Integrity Score</div>
                <div className="text-xs text-muted/40 mt-0.5">EBIP · ADR-045</div>
              </div>
            </div>

            <div className="flex items-center justify-center gap-2 text-xs text-muted/60">
              {isLive ? (
                <>
                  <span className="omnix-live-dot" style={{ width: '6px', height: '6px' }} />
                  <span>Live from PostgreSQL</span>
                </>
              ) : (
                <span>⏳ Connecting...</span>
              )}
              <span className="text-muted/30">·</span>
              <span>Running 24/7 since November 2025{metrics.system_uptime_days > 0 ? ` (${metrics.system_uptime_days} days)` : ''}</span>
            </div>
          </div>
        </section>

        <section className="mb-24">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-white mb-4">What Makes OMNIX Different</h2>
          </div>
          <div className="space-y-4 max-w-2xl mx-auto">
            <div className="flex items-start gap-4 p-4 bg-[#0A1628]/60 rounded-xl border border-[#C9A227]/20">
              <CheckCircle className="w-6 h-6 text-emerald-500 flex-shrink-0 mt-0.5" />
              <p className="text-muted"><span className="text-white font-medium">Blocks first, asks questions later.</span> We stop risky decisions before they cost you money.</p>
            </div>
            <div className="flex items-start gap-4 p-4 bg-[#0A1628]/60 rounded-xl border border-[#C9A227]/20">
              <CheckCircle className="w-6 h-6 text-emerald-500 flex-shrink-0 mt-0.5" />
              <p className="text-muted"><span className="text-white font-medium">Real-time context analysis.</span> We evaluate conditions before every decision.</p>
            </div>
            <div className="flex items-start gap-4 p-4 bg-[#0A1628]/60 rounded-xl border border-[#C9A227]/20">
              <CheckCircle className="w-6 h-6 text-emerald-500 flex-shrink-0 mt-0.5" />
              <p className="text-muted"><span className="text-white font-medium">No false promises.</span> We don't guarantee outcomes. We help prevent costly mistakes.</p>
            </div>
            <div className="flex items-start gap-4 p-4 bg-[#C9A227]/5 rounded-xl border border-[#C9A227]/30">
              <CheckCircle className="w-6 h-6 text-[#C9A227] flex-shrink-0 mt-0.5" />
              <p className="text-muted"><span className="text-[#C9A227] font-medium">Understands context, not just conditions.</span> Other systems follow rules. OMNIX understands when and why they should apply — with full context, memory, and cryptographic proof.</p>
            </div>
          </div>
        </section>

        <section className="glass-card p-12 gold-glow">
          <h2 className="text-3xl font-bold text-white text-center mb-4">Ready to Govern Your Decisions?</h2>
          <p className="text-xl text-muted max-w-2xl mx-auto mb-10 text-center">
            Let's talk about how OMNIX can help govern high-stakes decisions for your organization.
          </p>

          {formStatus === 'success' ? (
            <div className="text-center py-8">
              <div className="w-16 h-16 rounded-full bg-emerald-500/20 flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-8 h-8 text-emerald-400" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Thank you for reaching out!</h3>
              <p className="text-muted mb-6">We'll get back to you shortly.</p>
              <button
                onClick={() => setFormStatus('idle')}
                className="text-[#C9A227] hover:text-white transition-colors text-sm"
              >
                Send another message
              </button>
            </div>
          ) : (
            <form onSubmit={handleFormSubmit} className="max-w-xl mx-auto space-y-5">
              <div className="grid md:grid-cols-2 gap-5">
                <div>
                  <label htmlFor="contact-name" className="block text-sm font-medium text-muted mb-1.5">Name *</label>
                  <input
                    id="contact-name"
                    name="name"
                    type="text"
                    required
                    value={formData.name}
                    onChange={handleFormChange}
                    className="w-full px-4 py-3 rounded-xl bg-[#0A1628]/80 border border-[#C9A227]/20 text-white placeholder-gray-500 focus:outline-none focus:border-[#C9A227]/60 transition-colors"
                    placeholder="Your name"
                  />
                </div>
                <div>
                  <label htmlFor="contact-company" className="block text-sm font-medium text-muted mb-1.5">Company</label>
                  <input
                    id="contact-company"
                    name="company"
                    type="text"
                    value={formData.company}
                    onChange={handleFormChange}
                    className="w-full px-4 py-3 rounded-xl bg-[#0A1628]/80 border border-[#C9A227]/20 text-white placeholder-gray-500 focus:outline-none focus:border-[#C9A227]/60 transition-colors"
                    placeholder="Your company"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="contact-email" className="block text-sm font-medium text-muted mb-1.5">Email *</label>
                <input
                  id="contact-email"
                  name="email"
                  type="email"
                  required
                  value={formData.email}
                  onChange={handleFormChange}
                  className="w-full px-4 py-3 rounded-xl bg-[#0A1628]/80 border border-[#C9A227]/20 text-white placeholder-gray-500 focus:outline-none focus:border-[#C9A227]/60 transition-colors"
                  placeholder="you@company.com"
                />
              </div>

              <div>
                <label htmlFor="contact-referral" className="block text-sm font-medium text-muted mb-1.5">How did you find us? *</label>
                <select
                  id="contact-referral"
                  name="referral_source"
                  required
                  value={formData.referral_source}
                  onChange={handleFormChange}
                  className="w-full px-4 py-3 rounded-xl bg-[#0A1628]/80 border border-[#C9A227]/20 text-white focus:outline-none focus:border-[#C9A227]/60 transition-colors appearance-none"
                >
                  <option value="" disabled className="text-gray-500">Select an option</option>
                  {REFERRAL_OPTIONS.map(opt => (
                    <option key={opt} value={opt} className="bg-[#0A1628] text-white">{opt}</option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="contact-message" className="block text-sm font-medium text-muted mb-1.5">Message (optional)</label>
                <textarea
                  id="contact-message"
                  name="message"
                  rows={3}
                  value={formData.message}
                  onChange={handleFormChange}
                  className="w-full px-4 py-3 rounded-xl bg-[#0A1628]/80 border border-[#C9A227]/20 text-white placeholder-gray-500 focus:outline-none focus:border-[#C9A227]/60 transition-colors resize-none"
                  placeholder="Tell us about your needs..."
                />
              </div>

              {formStatus === 'error' && (
                <div className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3">
                  {formError}
                </div>
              )}

              <button
                type="submit"
                disabled={formStatus === 'sending'}
                className="btn-primary w-full flex items-center justify-center gap-2 py-3 disabled:opacity-60"
              >
                {formStatus === 'sending' ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Sending...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    Send Message
                  </>
                )}
              </button>
            </form>
          )}

          <div className="flex flex-col items-center gap-3 text-sm mt-8 pt-8 border-t border-[#C9A227]/10">
            <a href="mailto:contacto@omnixquantum.net" className="text-[#C9A227] hover:text-white transition-colors flex items-center gap-2">
              <Mail className="w-4 h-4" />
              contacto@omnixquantum.net
            </a>
            <a href="tel:+16505078293" className="text-[#10b981] hover:text-white transition-colors flex items-center gap-2">
              <Phone className="w-4 h-4" />
              Phone: +1 (650) 507-8293
            </a>
            <a href="https://wa.me/16504815494?text=Hi%2C%20I%27m%20interested%20in%20OMNIX" target="_blank" rel="noopener noreferrer" className="text-[#10b981] hover:text-white transition-colors flex items-center gap-2">
              <span className="text-lg">💬</span>
              WhatsApp: +1 (650) 481-5494
            </a>
          </div>
        </section>

        <div className="mt-12 text-center space-y-3">
          <Link to="/governance-demo" className="text-emerald-400 hover:text-white transition-colors flex items-center justify-center gap-2">
            See our multi-vertical governance demo in action
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link to="/institutional" className="text-[#C9A227] hover:text-white transition-colors flex items-center justify-center gap-2">
            Looking for technical details? View our Institutional page
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </main>

      <footer className="border-t border-[#C9A227]/10 py-12 px-6">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-3">
            <img src="/logo.png" alt="OMNIX" className="w-10 h-10 object-contain" />
            <span className="text-muted text-sm">&copy; 2026 OMNIX QUANTUM. All rights reserved.</span>
          </div>
          <div className="flex items-center gap-6">
            <Link to="/try" className="text-[#C9A227] hover:text-white text-sm transition-colors font-medium">
              Try OMNIX
            </Link>
            <Link to="/governance-demo" className="text-muted hover:text-white text-sm transition-colors">
              Credit Demo
            </Link>
            <Link to="/governance-demo-insurance" className="text-muted hover:text-white text-sm transition-colors">
              Insurance Demo
            </Link>
            <Link to="/governance-demo-energy" className="text-muted hover:text-white text-sm transition-colors">
              Energy Demo
            </Link>
            <Link to="/governance-demo-biotech" className="text-muted hover:text-white text-sm transition-colors">
              Biotech Demo
            </Link>
            <Link to="/institutional" className="text-muted hover:text-white text-sm transition-colors">
              Technical Details
            </Link>
            <a href="https://wa.me/16504815494?text=Hi%2C%20I%27m%20interested%20in%20OMNIX" target="_blank" rel="noopener noreferrer" className="text-muted hover:text-white text-sm transition-colors">
              Contact
            </a>
            <Link to="/terms" className="text-muted hover:text-white text-sm transition-colors">
              Terms
            </Link>
            <Link to="/privacy" className="text-muted hover:text-white text-sm transition-colors">
              Privacy
            </Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
