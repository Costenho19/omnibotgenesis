import { useState } from 'react'

const PERIODS = [
  { label: 'Q1 2026 (Jan – Mar)',  value: 'Q1-2026', from: '2026-01-01', to: '2026-03-31' },
  { label: 'Q2 2026 (Apr – Jun)',  value: 'Q2-2026', from: '2026-04-01', to: '2026-06-30' },
  { label: 'Last 30 days',         value: 'Last30',  from: '',           to: '' },
  { label: 'Last 90 days',         value: 'Last90',  from: '',           to: '' },
]

function getLast(days: number) {
  const to = new Date()
  const from = new Date()
  from.setDate(from.getDate() - days)
  const fmt = (d: Date) => d.toISOString().slice(0, 10)
  return { from: fmt(from), to: fmt(to) }
}

export default function ClientReportDownload() {
  const [apiKey, setApiKey] = useState('')
  const [period, setPeriod] = useState(PERIODS[0].value)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  async function handleDownload() {
    setError('')
    setSuccess(false)
    if (!apiKey.trim()) { setError('Please enter your API key.'); return }

    const sel = PERIODS.find(p => p.value === period)!
    let from = sel.from
    let to   = sel.to
    if (period === 'Last30') { const d = getLast(30); from = d.from; to = d.to }
    if (period === 'Last90') { const d = getLast(90); from = d.from; to = d.to }

    const url = `/api/governance/reports/pdf?period=${period}&from=${from}&to=${to}`
    setLoading(true)
    try {
      const res = await fetch(url, { headers: { 'X-API-Key': apiKey.trim() } })
      if (res.status === 401) { setError('Invalid or inactive API key. Check with your OMNIX account manager.'); return }
      if (!res.ok) { setError(`Server error (${res.status}). Please try again or contact support.`); return }
      const blob = await res.blob()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = `OMNIX-Report-${period}.pdf`
      a.click()
      URL.revokeObjectURL(a.href)
      setSuccess(true)
    } catch {
      setError('Connection error. Please check your internet and try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh', background: '#050D18',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontFamily: 'Helvetica Neue, Helvetica, Arial, sans-serif',
      padding: '24px',
    }}>
      <div style={{ width: '100%', maxWidth: 480 }}>

        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <img src="/omnix_logo.png" alt="OMNIX"
            style={{ width: 160, opacity: 0.95 }} />
        </div>

        {/* Card */}
        <div style={{
          background: '#0A1628', border: '1px solid #1E3050',
          borderRadius: 12, padding: '36px 32px',
          boxShadow: '0 8px 48px rgba(0,0,0,0.6)',
        }}>
          <div style={{ borderLeft: '3px solid #C9A227', paddingLeft: 14, marginBottom: 28 }}>
            <h1 style={{ color: '#fff', fontSize: 20, fontWeight: 700, margin: 0 }}>
              Download Governance Report
            </h1>
            <p style={{ color: '#7890B0', fontSize: 13, margin: '6px 0 0' }}>
              Enter your API key to generate and download your PDF report.
            </p>
          </div>

          {/* API Key */}
          <label style={{ display: 'block', color: '#9090A8', fontSize: 11,
            fontWeight: 600, letterSpacing: 1, marginBottom: 6 }}>
            YOUR API KEY
          </label>
          <input
            type="password"
            placeholder="OMNIX-xxxxxxxxxxxxxxxxxx"
            value={apiKey}
            onChange={e => { setApiKey(e.target.value); setError(''); setSuccess(false) }}
            style={{
              width: '100%', boxSizing: 'border-box',
              background: '#050D18', border: '1px solid #1E3050',
              borderRadius: 8, color: '#E0E8F8', fontSize: 14,
              padding: '11px 14px', marginBottom: 20, outline: 'none',
              fontFamily: 'monospace',
            }}
            onKeyDown={e => e.key === 'Enter' && handleDownload()}
          />

          {/* Period */}
          <label style={{ display: 'block', color: '#9090A8', fontSize: 11,
            fontWeight: 600, letterSpacing: 1, marginBottom: 6 }}>
            REPORTING PERIOD
          </label>
          <select
            value={period}
            onChange={e => setPeriod(e.target.value)}
            style={{
              width: '100%', background: '#050D18', border: '1px solid #1E3050',
              borderRadius: 8, color: '#E0E8F8', fontSize: 14,
              padding: '11px 14px', marginBottom: 28, outline: 'none',
              cursor: 'pointer',
            }}
          >
            {PERIODS.map(p => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>

          {/* Error */}
          {error && (
            <div style={{
              background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
              borderRadius: 8, padding: '10px 14px', marginBottom: 16,
              color: '#FCA5A5', fontSize: 13,
            }}>
              {error}
            </div>
          )}

          {/* Success */}
          {success && (
            <div style={{
              background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)',
              borderRadius: 8, padding: '10px 14px', marginBottom: 16,
              color: '#6EE7B7', fontSize: 13,
            }}>
              Report downloaded successfully. Check your Downloads folder.
            </div>
          )}

          {/* Download button */}
          <button
            onClick={handleDownload}
            disabled={loading}
            style={{
              width: '100%', background: loading ? '#3A4A2A' : '#C9A227',
              border: 'none', borderRadius: 8, color: loading ? '#8A9A6A' : '#050D18',
              fontSize: 15, fontWeight: 700, padding: '13px',
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
            }}
          >
            {loading ? (
              <>
                <span style={{
                  display: 'inline-block', width: 16, height: 16,
                  border: '2px solid #8A9A6A', borderTopColor: 'transparent',
                  borderRadius: '50%', animation: 'spin 0.8s linear infinite',
                }} />
                Generating your report…
              </>
            ) : (
              <>
                ↓ Download PDF Report
              </>
            )}
          </button>

          <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
        </div>

        {/* Footer */}
        <div style={{ textAlign: 'center', marginTop: 24, color: '#3A5070', fontSize: 12 }}>
          <p style={{ margin: 0 }}>
            Don't have an API key?{' '}
            <a href="mailto:contacto@omnixquantum.net"
              style={{ color: '#C9A227', textDecoration: 'none' }}>
              Contact us
            </a>
          </p>
          <p style={{ margin: '6px 0 0' }}>
            <a href="/" style={{ color: '#3A5070', textDecoration: 'none' }}>
              omnixquantum.net
            </a>
            {' '}·{' '}
            <a href="/verify" style={{ color: '#3A5070', textDecoration: 'none' }}>
              Verify a receipt
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}
