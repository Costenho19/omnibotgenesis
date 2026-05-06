import { useEffect, useState } from 'react'

interface Lead {
  id: number
  ts: string
  name: string
  company: string
  email: string
}

const NAVY = '#0A1628'
const GOLD = '#C9A227'
const BLUE = '#2E86C1'
const GREEN = '#27AE60'

export default function BookLeadsDashboard() {
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')

  async function load() {
    try {
      const res = await fetch('/api/book-leads-admin')
      const data = await res.json()
      setLeads(data.leads || [])
    } catch {
      setError('Error cargando leads')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    const t = setInterval(load, 30000)
    return () => clearInterval(t)
  }, [])

  const today = new Date().toISOString().split('T')[0]
  const todayCount = leads.filter(l => l.ts?.startsWith(today)).length
  const companies = new Set(leads.map(l => (l.company || '').toLowerCase().trim()).filter(Boolean)).size

  const filtered = leads.filter(l =>
    !search || [l.name, l.company, l.email].some(v => v?.toLowerCase().includes(search.toLowerCase()))
  )

  function downloadCSV() {
    if (!filtered.length) return
    const header = ['id', 'fecha', 'nombre', 'empresa', 'correo']
    const rows = filtered.map(l => [l.id, l.ts, l.name, l.company, l.email])
    const csv = [header, ...rows].map(r =>
      r.map(v => `"${(v ?? '').toString().replace(/"/g, '""')}"`).join(',')
    ).join('\n')
    const a = document.createElement('a')
    a.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv)
    a.download = 'ghost_compliance_leads.csv'
    a.click()
  }

  return (
    <div style={{ fontFamily: 'Inter, Arial, sans-serif', background: NAVY, minHeight: '100vh' }}>

      {/* NAV */}
      <nav style={{ background: NAVY, borderBottom: `3px solid ${GOLD}`, padding: '12px 32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <a href="/" style={{ color: GOLD, fontWeight: 800, fontSize: 18, textDecoration: 'none', letterSpacing: 2 }}>OMNIX QUANTUM</a>
          <span style={{ color: '#3A5A7A', fontSize: 12 }}>Book Leads — Ghost Compliance</span>
        </div>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
          <a href="/book" target="_blank" style={{ color: BLUE, fontSize: 12, textDecoration: 'none' }}>← Ver página del libro</a>
          <button onClick={load} style={{ background: 'transparent', border: `1px solid ${GOLD}`, color: GOLD, borderRadius: 4, padding: '4px 12px', fontSize: 11, cursor: 'pointer' }}>↻ Actualizar</button>
        </div>
      </nav>

      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '36px 24px' }}>

        {/* STATS */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 16, marginBottom: 28 }}>
          {[
            { label: 'Total Leads', value: leads.length, color: GOLD },
            { label: 'Hoy', value: todayCount, color: BLUE },
            { label: 'Empresas únicas', value: companies, color: GREEN },
          ].map(s => (
            <div key={s.label} style={{ background: '#0F1F35', border: `1px solid ${s.color}33`, borderRadius: 8, padding: '20px', textAlign: 'center' }}>
              <div style={{ color: s.color, fontSize: 40, fontWeight: 800 }}>{loading ? '—' : s.value}</div>
              <div style={{ color: '#AAC4D8', fontSize: 11, marginTop: 4, textTransform: 'uppercase', letterSpacing: 2 }}>{s.label}</div>
            </div>
          ))}
        </div>

        {/* TABLE */}
        <div style={{ background: '#0F1F35', border: '1px solid #1E3A5F', borderRadius: 8, overflow: 'hidden' }}>
          <div style={{ padding: '14px 20px', borderBottom: '1px solid #1E3A5F', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <span style={{ color: GOLD, fontWeight: 700, fontSize: 13, letterSpacing: 1 }}>LEADS REGISTRADOS</span>
            <div style={{ display: 'flex', gap: 10 }}>
              <input
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Buscar por nombre, empresa o correo..."
                style={{ padding: '6px 12px', borderRadius: 4, border: '1px solid #2E4A6A', background: '#0A1628', color: '#FFF', fontSize: 12, width: 240, outline: 'none' }}
              />
              <button onClick={downloadCSV} style={{ background: GOLD, color: NAVY, border: 'none', borderRadius: 4, padding: '6px 14px', fontSize: 12, fontWeight: 700, cursor: 'pointer' }}>
                ⬇ CSV
              </button>
            </div>
          </div>

          {error && <div style={{ padding: 24, color: '#E74C3C', textAlign: 'center', fontSize: 13 }}>{error}</div>}

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ background: '#0A1628' }}>
                  {['#', 'Fecha', 'Nombre', 'Empresa', 'Correo', 'Acción'].map(h => (
                    <th key={h} style={{ padding: '10px 16px', textAlign: 'left', color: '#6A8A9A', fontWeight: 600, fontSize: 11, letterSpacing: 1, textTransform: 'uppercase', borderBottom: '1px solid #1E3A5F' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={6} style={{ padding: 40, textAlign: 'center', color: '#6A8A9A' }}>Cargando...</td></tr>
                ) : filtered.length === 0 ? (
                  <tr><td colSpan={6} style={{ padding: 40, textAlign: 'center', color: '#6A8A9A' }}>
                    {search ? 'Sin resultados para esa búsqueda' : 'Sin leads todavía — comparte omnixquantum.net/book'}
                  </td></tr>
                ) : filtered.map((l, i) => {
                  const dt = l.ts ? new Date(l.ts).toLocaleString('es-US', { dateStyle: 'short', timeStyle: 'short' }) : '—'
                  return (
                    <tr key={l.id} style={{ borderBottom: '1px solid #1E3A5F', background: i % 2 === 0 ? '#0F1F35' : '#0A1D30' }}>
                      <td style={{ padding: '11px 16px', color: '#6A8A9A' }}>{l.id}</td>
                      <td style={{ padding: '11px 16px', color: '#7FB3D3', fontSize: 12 }}>{dt}</td>
                      <td style={{ padding: '11px 16px', color: '#FFFFFF', fontWeight: 500 }}>{l.name || '—'}</td>
                      <td style={{ padding: '11px 16px', color: GOLD }}>{l.company || '—'}</td>
                      <td style={{ padding: '11px 16px', color: '#AAC4D8' }}>{l.email || '—'}</td>
                      <td style={{ padding: '11px 16px' }}>
                        <a href={`mailto:${l.email}`} style={{ color: BLUE, fontSize: 12, textDecoration: 'none', fontWeight: 600 }}>Contactar →</a>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>

        <p style={{ color: '#3A5A7A', fontSize: 11, marginTop: 14, textAlign: 'center' }}>
          Datos guardados en PostgreSQL · Se actualiza cada 30 segundos
        </p>
      </div>
    </div>
  )
}
