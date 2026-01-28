import { Shield, ArrowRight, CheckCircle, Lock, Zap, Phone, Mail } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function CommercialLanding() {
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
            <Link to="/institutional" className="nav-link">Technical Details</Link>
            <a href="mailto:contacto@omnixquantum.net" className="btn-primary">Talk to Us</a>
          </div>
        </div>
      </nav>

      <main className="pt-32 px-6 pb-20 max-w-6xl mx-auto">
        <section className="text-center mb-24 animate-fade-in-up">
          <h1 className="heading-xl text-white mb-8 leading-tight">
            Stop Catastrophic <br />
            <span className="gold-gradient">Trading Losses</span>
          </h1>
          <p className="text-2xl text-muted max-w-3xl mx-auto mb-12 leading-relaxed">
            OMNIX helps prevent catastrophic trading losses by blocking high-risk executions before they happen.
          </p>
          <div className="flex justify-center gap-4 flex-wrap">
            <a href="mailto:contacto@omnixquantum.net" className="btn-primary text-lg px-8 py-4 flex items-center gap-2">
              Request Access
              <ArrowRight className="w-5 h-5" />
            </a>
            <a href="tel:+16505078293" className="btn-secondary text-lg px-8 py-4 flex items-center gap-2">
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
              <h3 className="text-xl font-semibold text-white mb-4">Capital Protection</h3>
              <p className="text-muted leading-relaxed">
                Every trade is validated before execution. Risky trades are blocked automatically.
              </p>
            </div>

            <div className="glass-card p-8 text-center">
              <div className="w-16 h-16 rounded-full bg-[#C9A227]/20 flex items-center justify-center mx-auto mb-6">
                <Zap className="w-8 h-8 gold-text" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-4">Works with Your Tools</h3>
              <p className="text-muted leading-relaxed">
                Connects to your existing trading platform. No need to change how you trade.
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
                <p className="text-white font-medium">You make a trade decision</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 rounded-full bg-[#C9A227] text-[#0A1628] font-bold text-xl flex items-center justify-center mx-auto mb-4">2</div>
                <p className="text-white font-medium">OMNIX checks if it's safe</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 rounded-full bg-[#C9A227] text-[#0A1628] font-bold text-xl flex items-center justify-center mx-auto mb-4">3</div>
                <p className="text-white font-medium">Bad trades get blocked</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 rounded-full bg-[#C9A227] text-[#0A1628] font-bold text-xl flex items-center justify-center mx-auto mb-4">4</div>
                <p className="text-white font-medium">Safe trades go through</p>
              </div>
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
              <p className="text-muted"><span className="text-white font-medium">Blocks first, asks questions later.</span> We stop risky trades before they cost you money.</p>
            </div>
            <div className="flex items-start gap-4 p-4 bg-[#0A1628]/60 rounded-xl border border-[#C9A227]/20">
              <CheckCircle className="w-6 h-6 text-emerald-500 flex-shrink-0 mt-0.5" />
              <p className="text-muted"><span className="text-white font-medium">Real-time market analysis.</span> We check market conditions before every trade.</p>
            </div>
            <div className="flex items-start gap-4 p-4 bg-[#0A1628]/60 rounded-xl border border-[#C9A227]/20">
              <CheckCircle className="w-6 h-6 text-emerald-500 flex-shrink-0 mt-0.5" />
              <p className="text-muted"><span className="text-white font-medium">No false promises.</span> We don't guarantee profits. We help prevent catastrophic losses.</p>
            </div>
          </div>
        </section>

        <section className="text-center glass-card p-12 gold-glow">
          <h2 className="text-3xl font-bold text-white mb-4">Ready to Protect Your Capital?</h2>
          <p className="text-xl text-muted max-w-2xl mx-auto mb-8">
            Let's talk about how OMNIX can help protect your trading portfolio.
          </p>
          <div className="flex justify-center gap-4 flex-wrap mb-8">
            <a href="mailto:contacto@omnixquantum.net" className="btn-primary flex items-center gap-2">
              <Mail className="w-4 h-4" />
              Request Access
            </a>
            <a href="tel:+16505078293" className="btn-secondary flex items-center gap-2">
              <Phone className="w-4 h-4" />
              Call Us
            </a>
          </div>
          <div className="flex justify-center items-center gap-8 text-sm">
            <a href="mailto:contacto@omnixquantum.net" className="text-[#C9A227] hover:text-white transition-colors">
              contacto@omnixquantum.net
            </a>
            <a href="tel:+16505078293" className="text-[#C9A227] hover:text-white transition-colors">
              +1 (650) 507-8293
            </a>
          </div>
        </section>

        <div className="mt-12 text-center">
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
            <Link to="/institutional" className="text-muted hover:text-white text-sm transition-colors">
              Technical Details
            </Link>
            <a href="mailto:contacto@omnixquantum.net" className="text-muted hover:text-white text-sm transition-colors">
              Contact
            </a>
          </div>
        </div>
      </footer>
    </div>
  )
}
