import { useState } from 'react'

const NAVY   = '#0A1628'
const GOLD   = '#C9A227'
const BLUE   = '#2E86C1'
const LIGHT  = '#F4F6F8'

export default function BookLanding() {
  const [form, setForm]       = useState({ name: '', company: '', email: '' })
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading]   = useState(false)
  const [error, setError]     = useState('')
  const [lang, setLang]       = useState<'en' | 'es'>('en')

  const t = {
    en: {
      badge:    'NEW RELEASE — 2026',
      title:    'Ghost Compliance',
      subtitle: "Why governance systems fail \u2014 and how to build ones that don't.",
      desc:     'Terra. FTX. SVB. LTCM. Four collapses. Four governance systems fully operational when they failed. This 322-page institutional analysis documents the exact failure mechanism — and the architecture built to stop the next one.',
      cases:    '$340B+ in documented governance failures across four case studies.',
      f_name:   'Your name',
      f_co:     'Company / Institution',
      f_email:  'Work email',
      cta:      'Get the Book — Free',
      note:     'No spam. One email with your download link.',
      dl_en:    '⬇  Download — English Edition (322 pages)',
      dl_es:    '⬇  Download — Spanish Edition (287 pages)',
      thanks:   'Your copy is ready.',
      thanks2:  'Choose your language below.',
      demo:     'See OMNIX in action →',
      chapters: 'WHAT\'S INSIDE',
      ch: [
        'The Photograph Problem — why snapshots fail',
        'Terra / FTX / SVB / LTCM — the exact failure mechanism',
        'The 6-Signal AVM — continuous admissibility monitoring',
        'The 11-Checkpoint Pipeline — decision governance architecture',
        'Post-Quantum Cryptographic receipts — W3C Verifiable Credentials',
        'MiCA, VARA, EU AI Act — what regulation actually requires',
        'Trading, Credit, Insurance, Medical AI, Robotics, Energy, Stablecoins',
      ],
    },
    es: {
      badge:    'NUEVO — 2026',
      title:    'Ghost Compliance',
      subtitle: 'Por qué fallan los sistemas de gobernanza — y cómo construir los que no fallan.',
      desc:     'Terra. FTX. SVB. LTCM. Cuatro colapsos. Cuatro sistemas de gobernanza completamente operativos cuando fallaron. Este análisis institucional de 287 páginas documenta el mecanismo exacto del fallo — y la arquitectura construida para detener el próximo.',
      cases:    'Más de $340B en fallos de gobernanza documentados en cuatro casos de estudio.',
      f_name:   'Tu nombre',
      f_co:     'Empresa / Institución',
      f_email:  'Correo corporativo',
      cta:      'Obtener el libro — Gratis',
      note:     'Sin spam. Un correo con tu enlace de descarga.',
      dl_en:    '⬇  Descargar — Edición en Inglés (322 páginas)',
      dl_es:    '⬇  Descargar — Edición en Español (287 páginas)',
      thanks:   'Tu copia está lista.',
      thanks2:  'Elige tu idioma abajo.',
      demo:     'Ver OMNIX en acción →',
      chapters: 'QUÉ ENCONTRARÁS',
      ch: [
        'El Problema de la Fotografía — por qué fallan los snapshots',
        'Terra / FTX / SVB / LTCM — el mecanismo exacto del fallo',
        'El AVM de 6 Señales — monitoreo continuo de admisibilidad',
        'El Pipeline de 11 Checkpoints — arquitectura de gobernanza de decisiones',
        'Recibos criptográficos post-cuánticos — Credenciales Verificables W3C',
        'MiCA, VARA, Ley de IA de la UE — lo que la regulación realmente requiere',
        'Trading, Crédito, Seguros, IA Médica, Robótica, Energía, Stablecoins',
      ],
    },
  }[lang]

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.name || !form.company || !form.email) {
      setError('Please fill in all fields.')
      return
    }
    setLoading(true)
    setError('')
    try {
      await fetch('/api/book-lead', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, ts: new Date().toISOString() }),
      }).catch(() => null)
      localStorage.setItem('gc_lead', JSON.stringify({ ...form, ts: Date.now() }))
    } catch (_) {}
    setLoading(false)
    setSubmitted(true)
  }

  return (
    <div style={{ fontFamily: 'Georgia, serif', background: LIGHT, minHeight: '100vh' }}>

      {/* TOP NAV */}
      <nav style={{ background: NAVY, borderBottom: `3px solid ${GOLD}`, padding: '12px 32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <a href="/" style={{ color: GOLD, fontWeight: 'bold', fontSize: 18, textDecoration: 'none', letterSpacing: 2 }}>OMNIX QUANTUM</a>
        <div style={{ display: 'flex', gap: 12 }}>
          <button onClick={() => setLang('en')} style={{ background: lang === 'en' ? GOLD : 'transparent', color: lang === 'en' ? NAVY : GOLD, border: `1px solid ${GOLD}`, borderRadius: 4, padding: '4px 14px', cursor: 'pointer', fontWeight: 'bold', fontSize: 12 }}>EN</button>
          <button onClick={() => setLang('es')} style={{ background: lang === 'es' ? GOLD : 'transparent', color: lang === 'es' ? NAVY : GOLD, border: `1px solid ${GOLD}`, borderRadius: 4, padding: '4px 14px', cursor: 'pointer', fontWeight: 'bold', fontSize: 12 }}>ES</button>
        </div>
      </nav>

      {/* HERO */}
      <div style={{ background: NAVY, padding: '60px 24px 50px', textAlign: 'center' }}>
        <div style={{ display: 'inline-block', background: GOLD, color: NAVY, fontSize: 11, fontWeight: 'bold', letterSpacing: 3, padding: '4px 16px', borderRadius: 2, marginBottom: 20, fontFamily: 'Arial, sans-serif' }}>{t.badge}</div>

        <div style={{ display: 'flex', justifyContent: 'center', gap: 48, alignItems: 'flex-start', flexWrap: 'wrap', maxWidth: 960, margin: '0 auto' }}>

          {/* COVER */}
          <div style={{ flexShrink: 0 }}>
            <img src="/book_cover_en.png" alt="Ghost Compliance Cover"
              style={{ width: 200, borderRadius: 4, boxShadow: '0 8px 32px rgba(0,0,0,0.5)', border: `2px solid ${GOLD}` }} />
          </div>

          {/* TITLE + FORM */}
          <div style={{ flex: 1, minWidth: 280, textAlign: 'left' }}>
            <h1 style={{ color: GOLD, fontSize: 42, fontWeight: 'bold', margin: '0 0 8px', letterSpacing: 1 }}>{t.title}</h1>
            <p style={{ color: '#FFFFFF', fontSize: 18, margin: '0 0 16px', lineHeight: 1.4 }}>{t.subtitle}</p>
            <p style={{ color: '#AAC4D8', fontSize: 14, margin: '0 0 8px', lineHeight: 1.6 }}>{t.desc}</p>
            <p style={{ color: GOLD, fontSize: 13, fontFamily: 'Arial, sans-serif', fontStyle: 'italic', margin: '0 0 24px' }}>{t.cases}</p>

            {/* FORM or DOWNLOAD */}
            {!submitted ? (
              <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 10, maxWidth: 380 }}>
                <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })}
                  placeholder={t.f_name} required
                  style={{ padding: '10px 14px', borderRadius: 4, border: `1px solid ${GOLD}`, background: '#0F1F35', color: '#FFF', fontSize: 14, outline: 'none' }} />
                <input value={form.company} onChange={e => setForm({ ...form, company: e.target.value })}
                  placeholder={t.f_co} required
                  style={{ padding: '10px 14px', borderRadius: 4, border: '1px solid #2E4A6A', background: '#0F1F35', color: '#FFF', fontSize: 14, outline: 'none' }} />
                <input value={form.email} onChange={e => setForm({ ...form, email: e.target.value })}
                  placeholder={t.f_email} type="email" required
                  style={{ padding: '10px 14px', borderRadius: 4, border: '1px solid #2E4A6A', background: '#0F1F35', color: '#FFF', fontSize: 14, outline: 'none' }} />
                {error && <p style={{ color: '#E74C3C', fontSize: 12, margin: 0 }}>{error}</p>}
                <button type="submit" disabled={loading}
                  style={{ padding: '13px 24px', background: loading ? '#8a7010' : GOLD, color: NAVY, border: 'none', borderRadius: 4, fontSize: 15, fontWeight: 'bold', cursor: loading ? 'default' : 'pointer', letterSpacing: 0.5 }}>
                  {loading ? '...' : t.cta}
                </button>
                <p style={{ color: '#6A8A9A', fontSize: 11, margin: 0, fontFamily: 'Arial, sans-serif' }}>{t.note}</p>
              </form>
            ) : (
              <div style={{ background: '#0F1F35', border: `1px solid ${GOLD}`, borderRadius: 6, padding: '24px 20px', maxWidth: 380 }}>
                <p style={{ color: GOLD, fontWeight: 'bold', fontSize: 16, margin: '0 0 4px' }}>{t.thanks}</p>
                <p style={{ color: '#AAC4D8', fontSize: 13, margin: '0 0 18px' }}>{t.thanks2}</p>
                <a href="/Ghost_Compliance_EN.pdf" download
                  style={{ display: 'block', background: NAVY, color: GOLD, border: `1px solid ${GOLD}`, borderRadius: 4, padding: '11px 16px', textDecoration: 'none', fontSize: 13, fontWeight: 'bold', marginBottom: 10, textAlign: 'center' }}>
                  {t.dl_en}
                </a>
                <a href="/Ghost_Compliance_ES.pdf" download
                  style={{ display: 'block', background: NAVY, color: '#AAC4D8', border: '1px solid #2E4A6A', borderRadius: 4, padding: '11px 16px', textDecoration: 'none', fontSize: 13, fontWeight: 'bold', textAlign: 'center' }}>
                  {t.dl_es}
                </a>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* DIVIDER */}
      <div style={{ height: 4, background: `linear-gradient(90deg, ${GOLD}, ${BLUE}, ${GOLD})` }} />

      {/* CHAPTERS */}
      <div style={{ maxWidth: 800, margin: '0 auto', padding: '56px 24px' }}>
        <h2 style={{ color: NAVY, fontSize: 13, letterSpacing: 3, fontFamily: 'Arial, sans-serif', fontWeight: 'bold', marginBottom: 28 }}>{t.chapters}</h2>
        <div style={{ display: 'grid', gap: 12 }}>
          {t.ch.map((c, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 16, background: '#FFF', borderRadius: 4, padding: '14px 18px', boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}>
              <span style={{ color: GOLD, fontWeight: 'bold', fontSize: 13, minWidth: 22, fontFamily: 'Arial, sans-serif' }}>{String(i + 1).padStart(2, '0')}</span>
              <span style={{ color: '#333', fontSize: 14, lineHeight: 1.5 }}>{c}</span>
            </div>
          ))}
        </div>
      </div>

      {/* CASE STUDIES BANNER */}
      <div style={{ background: NAVY, padding: '36px 24px', textAlign: 'center' }}>
        <p style={{ color: '#AAC4D8', fontSize: 12, letterSpacing: 3, fontFamily: 'Arial, sans-serif', marginBottom: 16 }}>CASE STUDIES</p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: 40, flexWrap: 'wrap' }}>
          {[['Terra / Luna', '$40B', '9 days'], ['FTX', '$8B', 'customer funds'], ['SVB', '$209B', '48 hours'], ['LTCM', '$100B', 'systemic risk']].map(([name, amount, note]) => (
            <div key={name} style={{ textAlign: 'center' }}>
              <div style={{ color: GOLD, fontSize: 20, fontWeight: 'bold' }}>{amount}</div>
              <div style={{ color: '#FFF', fontSize: 14, fontWeight: 'bold' }}>{name}</div>
              <div style={{ color: '#6A8A9A', fontSize: 11, fontFamily: 'Arial, sans-serif' }}>{note}</div>
            </div>
          ))}
        </div>
      </div>

      {/* CTA FOOTER */}
      <div style={{ background: LIGHT, padding: '48px 24px', textAlign: 'center' }}>
        <p style={{ color: '#666', fontSize: 14, marginBottom: 6 }}>Built on the OMNIX Quantum governance architecture.</p>
        <a href="/try" style={{ color: BLUE, fontSize: 15, fontWeight: 'bold', textDecoration: 'none' }}>{t.demo}</a>
        <p style={{ color: '#AAA', fontSize: 11, marginTop: 32, fontFamily: 'Arial, sans-serif' }}>
          © 2026 Harold Nunes / OMNIX Quantum · <a href="mailto:contact@omnixquantum.net" style={{ color: '#AAA' }}>contact@omnixquantum.net</a>
        </p>
      </div>
    </div>
  )
}
