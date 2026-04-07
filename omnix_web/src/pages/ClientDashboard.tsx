import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield, CheckCircle, XCircle, Lock, RefreshCw,
  Download, Key, Activity, BarChart3, FileText,
  ChevronRight, AlertTriangle, Globe, Zap, Clock
} from 'lucide-react'
import { API_BASE } from '../lib/apiBase'

interface Receipt {
  receipt_id: string
  decision: string
  domain: string
  asset: string
  timestamp: string
}

interface Stats {
  total_decisions: number
  approved: number
  blocked: number
  hold: number
  approval_rate: number
  period_days: number
  by_domain: Record<string, { total: number; approved: number; blocked: number }>
}

interface Framework {
  id: string
  full_name: string
  status: string
  applies_to: string
}

interface ReportData {
  client_id: string
  client_name: string
  period_days: number
  generated_at: string
  governance_statistics: Stats
  regulatory_coverage: {
    frameworks_count: number
    checkpoints_mapped: number
    frameworks: string[]
  }
  recent_receipts: Receipt[]
  pdf_available: boolean
  pdf_download_url: string
  attestation: string
}

const DOMAIN_LABELS: Record<string, string> = {
  trading:   'Digital Asset Trading',
  credit:    'Islamic Credit',
  insurance: 'Insurance Underwriting',
  robotics:  'Robotics & Autonomous Systems',
}
const DOMAIN_ICONS: Record<string, string> = {
  trading: '📈', credit: '🕌', insurance: '🛡️', robotics: '🤖',
}
const DOMAIN_COLORS: Record<string, string> = {
  trading: '#C9A227', credit: '#a78bfa', insurance: '#60a5fa', robotics: '#34d399',
}
const FW_COLORS: Record<string, string> = {
  EU_AI_ACT: '#3B82F6', DORA: '#8B5CF6', NIST_AI_RMF: '#10B981',
  ISO_42001: '#F59E0B', CA_SB_243: '#EF4444', GDPR: '#6366F1',
  FATF: '#EC4899', BASEL_III: '#14B8A6',
}
const FW_SHORT: Record<string, string> = {
  EU_AI_ACT: 'EU AI Act', DORA: 'DORA', NIST_AI_RMF: 'NIST AI RMF',
  ISO_42001: 'ISO 42001', CA_SB_243: 'CA SB 243', GDPR: 'GDPR',
  FATF: 'FATF', BASEL_III: 'Basel III',
}

function DecisionBadge({ decision }: { decision: string }) {
  const map: Record<string, { bg: string; color: string; label: string }> = {
    APPROVED: { bg: 'rgba(16,185,129,0.15)', color: '#10B981', label: 'APPROVED' },
    BLOCKED:  { bg: 'rgba(239,68,68,0.15)',  color: '#EF4444', label: 'BLOCKED'  },
    HOLD:     { bg: 'rgba(245,158,11,0.15)', color: '#F59E0B', label: 'HOLD'     },
  }
  const s = map[decision] || map.HOLD
  return (
    <span style={{
      padding: '3px 10px', borderRadius: 20, fontSize: 11,
      fontWeight: 700, letterSpacing: '0.08em',
      background: s.bg, color: s.color,
      border: `1px solid ${s.color}33`,
    }}>{s.label}</span>
  )
}

function KpiCard({ label, value, sub, accent }: { label: string; value: string | number; sub: string; accent: string }) {
  return (
    <div style={{
      background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)',
      borderRadius: 12, padding: '20px 22px', flex: 1,
      borderTop: `3px solid ${accent}`,
    }}>
      <div style={{ fontSize: 28, fontWeight: 800, color: '#F7F9FC', lineHeight: 1 }}>{value}</div>
      <div style={{ fontSize: 11, fontWeight: 700, color: accent, letterSpacing: '0.1em', marginTop: 6 }}>{label.toUpperCase()}</div>
      <div style={{ fontSize: 11, color: '#666688', marginTop: 4 }}>{sub}</div>
    </div>
  )
}

export default function ClientDashboard() {
  const [apiKey, setApiKey]         = useState('')
  const [inputKey, setInputKey]     = useState('')
  const [loading, setLoading]       = useState(false)
  const [error, setError]           = useState('')
  const [data, setData]             = useState<ReportData | null>(null)
  const [fwData, setFwData]         = useState<Framework[]>([])
  const [pdfLoading, setPdfLoading] = useState(false)
  const [days, setDays]             = useState(30)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)

  const fetchReport = useCallback(async (key: string, d: number) => {
    setLoading(true)
    setError('')
    try {
      const res = await fetch(
        `${API_BASE}/api/governance/due-diligence-report?format=json&days=${d}`,
        { headers: { 'X-API-Key': key, 'Accept': 'application/json' } }
      )
      if (res.status === 401) { setError('Invalid or expired API key. Please check and try again.'); setApiKey(''); return }
      if (!res.ok) { const j = await res.json().catch(() => ({})); setError(j.error || `Error ${res.status}`); return }
      const json = await res.json()
      if (json.status !== 'ok') { setError(json.error || 'Unexpected response'); return }
      setData(json)
      setLastRefresh(new Date())
    } catch (e) {
      setError('Network error — please check your connection.')
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchFrameworks = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/governance/regulatory/catalog`)
      if (!res.ok) return
      const json = await res.json()
      const fws = json?.regulatory_catalog?.frameworks
      if (fws) {
        setFwData(Object.entries(fws).map(([id, meta]: [string, any]) => ({
          id, full_name: meta.full_name, status: meta.status, applies_to: meta.applies_to,
        })))
      }
    } catch { /* non-critical */ }
  }, [])

  useEffect(() => { fetchFrameworks() }, [fetchFrameworks])

  const handleConnect = (e: React.FormEvent) => {
    e.preventDefault()
    const k = inputKey.trim()
    if (!k.startsWith('OMNIX-')) { setError('API key must start with OMNIX-'); return }
    setApiKey(k)
    fetchReport(k, days)
  }

  const handleRefresh = () => { if (apiKey) fetchReport(apiKey, days) }

  const handleDaysChange = (d: number) => { setDays(d); if (apiKey) fetchReport(apiKey, d) }

  const handlePdfDownload = async () => {
    if (!apiKey) return
    setPdfLoading(true)
    try {
      const res = await fetch(
        `${API_BASE}/api/governance/due-diligence-report?format=pdf&days=${days}`,
        { headers: { 'X-API-Key': apiKey } }
      )
      if (!res.ok) { setError('PDF generation failed.'); return }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `OMNIX_GovernanceReport_${data?.client_id || 'client'}_${new Date().toISOString().slice(0,10)}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch { setError('PDF download failed.') }
    finally { setPdfLoading(false) }
  }

  if (!apiKey) {
    return (
      <div style={{
        minHeight: '100vh', background: '#0A0A0F',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontFamily: "'Inter', -apple-system, sans-serif",
      }}>
        <div style={{ width: '100%', maxWidth: 440, padding: '0 20px' }}>
          <div style={{ textAlign: 'center', marginBottom: 40 }}>
            <div style={{
              width: 56, height: 56, borderRadius: 16,
              background: 'linear-gradient(135deg, #00C6FF22, #7B2FFF33)',
              border: '1px solid #00C6FF44',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              margin: '0 auto 20px',
            }}>
              <Shield size={26} color="#00C6FF" />
            </div>
            <h1 style={{ color: '#F7F9FC', fontSize: 24, fontWeight: 800, margin: '0 0 8px' }}>
              Client Portal
            </h1>
            <p style={{ color: '#666688', fontSize: 14, margin: 0 }}>
              OMNIX Decision Governance Infrastructure
            </p>
          </div>

          <div style={{
            background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.10)',
            borderRadius: 16, padding: 32,
          }}>
            <form onSubmit={handleConnect}>
              <label style={{ display: 'block', color: '#AAB0CC', fontSize: 12, fontWeight: 600, letterSpacing: '0.08em', marginBottom: 8 }}>
                API KEY
              </label>
              <div style={{ position: 'relative', marginBottom: 20 }}>
                <Key size={16} color="#666688" style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)' }} />
                <input
                  type="password"
                  value={inputKey}
                  onChange={e => { setInputKey(e.target.value); setError('') }}
                  placeholder="OMNIX-••••••••••••••••"
                  autoComplete="off"
                  style={{
                    width: '100%', padding: '12px 14px 12px 40px',
                    background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)',
                    borderRadius: 10, color: '#F7F9FC', fontSize: 14,
                    outline: 'none', boxSizing: 'border-box',
                    fontFamily: 'monospace',
                  }}
                />
              </div>

              {error && (
                <div style={{
                  background: 'rgba(239,68,68,0.10)', border: '1px solid #EF444433',
                  borderRadius: 8, padding: '10px 14px', marginBottom: 16,
                  color: '#EF4444', fontSize: 13, display: 'flex', gap: 8, alignItems: 'center',
                }}>
                  <AlertTriangle size={14} /> {error}
                </div>
              )}

              <button
                type="submit"
                disabled={!inputKey || loading}
                style={{
                  width: '100%', padding: '12px 0', borderRadius: 10,
                  background: 'linear-gradient(135deg, #00C6FF, #7B2FFF)',
                  border: 'none', color: '#fff', fontWeight: 700, fontSize: 14,
                  cursor: inputKey ? 'pointer' : 'not-allowed',
                  opacity: inputKey ? 1 : 0.5, letterSpacing: '0.04em',
                  transition: 'all 0.2s',
                }}
              >
                {loading ? 'Connecting…' : 'Access Portal'}
              </button>
            </form>

            <div style={{ marginTop: 24, padding: '16px', background: 'rgba(0,198,255,0.05)', borderRadius: 10, border: '1px solid rgba(0,198,255,0.12)' }}>
              <p style={{ color: '#666688', fontSize: 12, margin: 0, lineHeight: 1.6 }}>
                Your API key was provided at onboarding. Contact{' '}
                <a href="mailto:contacto@omnixquantum.net" style={{ color: '#00C6FF', textDecoration: 'none' }}>
                  contacto@omnixquantum.net
                </a>{' '}
                if you need to rotate or recover it.
              </p>
            </div>
          </div>

          <div style={{ textAlign: 'center', marginTop: 24 }}>
            <Link to="/" style={{ color: '#444466', fontSize: 12, textDecoration: 'none' }}>
              ← Back to omnixquantum.net
            </Link>
          </div>
        </div>
      </div>
    )
  }

  const stats = data?.governance_statistics
  const receipts = data?.recent_receipts || []
  const domains = stats?.by_domain ? Object.entries(stats.by_domain) : []

  return (
    <div style={{
      minHeight: '100vh', background: '#0A0A0F',
      fontFamily: "'Inter', -apple-system, sans-serif",
      color: '#F7F9FC',
    }}>
      {/* TOP BAR */}
      <div style={{
        borderBottom: '1px solid rgba(255,255,255,0.07)',
        background: 'rgba(10,10,15,0.95)', backdropFilter: 'blur(12px)',
        position: 'sticky', top: 0, zIndex: 100,
      }}>
        <div style={{
          maxWidth: 1200, margin: '0 auto', padding: '0 28px',
          height: 60, display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Shield size={20} color="#00C6FF" />
            <span style={{ fontWeight: 800, fontSize: 15, letterSpacing: '-0.02em' }}>OMNIX</span>
            <ChevronRight size={14} color="#444466" />
            <span style={{ color: '#666688', fontSize: 13 }}>Client Portal</span>
            {data && (
              <>
                <ChevronRight size={14} color="#444466" />
                <span style={{ color: '#AAB0CC', fontSize: 13 }}>{data.client_name}</span>
              </>
            )}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {lastRefresh && (
              <span style={{ color: '#444466', fontSize: 11 }}>
                <Clock size={11} style={{ verticalAlign: 'middle', marginRight: 4 }} />
                {lastRefresh.toLocaleTimeString()}
              </span>
            )}
            <button
              onClick={handleRefresh}
              disabled={loading}
              style={{
                background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.10)',
                borderRadius: 8, padding: '6px 12px', color: '#AAB0CC',
                cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, fontSize: 12,
              }}
            >
              <RefreshCw size={13} style={loading ? { animation: 'spin 1s linear infinite' } : {}} />
              Refresh
            </button>
            <button
              onClick={() => { setApiKey(''); setData(null) }}
              style={{
                background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.20)',
                borderRadius: 8, padding: '6px 12px', color: '#EF4444',
                cursor: 'pointer', fontSize: 12,
              }}
            >
              Disconnect
            </button>
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '32px 28px' }}>
        {/* HEADER */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 32 }}>
          <div>
            <h1 style={{ fontSize: 26, fontWeight: 800, margin: '0 0 6px', letterSpacing: '-0.03em' }}>
              Governance Dashboard
            </h1>
            <p style={{ color: '#666688', fontSize: 14, margin: 0 }}>
              Real-time governance receipt analytics · Post-quantum signed · Chain-linked
            </p>
          </div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            {/* Days filter */}
            <div style={{ display: 'flex', gap: 4, background: 'rgba(255,255,255,0.04)', borderRadius: 8, padding: 3 }}>
              {[7, 30, 90].map(d => (
                <button
                  key={d}
                  onClick={() => handleDaysChange(d)}
                  style={{
                    padding: '5px 12px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                    border: 'none', cursor: 'pointer',
                    background: days === d ? 'rgba(0,198,255,0.15)' : 'transparent',
                    color: days === d ? '#00C6FF' : '#666688',
                  }}
                >{d}d</button>
              ))}
            </div>
            <button
              onClick={handlePdfDownload}
              disabled={pdfLoading || !data?.pdf_available}
              style={{
                display: 'flex', alignItems: 'center', gap: 8,
                padding: '9px 18px', borderRadius: 10,
                background: 'linear-gradient(135deg, #00C6FF22, #7B2FFF22)',
                border: '1px solid #00C6FF44', color: '#00C6FF',
                cursor: data?.pdf_available ? 'pointer' : 'not-allowed',
                opacity: data?.pdf_available ? 1 : 0.4,
                fontSize: 13, fontWeight: 600, letterSpacing: '0.02em',
                transition: 'all 0.2s',
              }}
            >
              <Download size={14} />
              {pdfLoading ? 'Generating…' : 'Due Diligence PDF'}
            </button>
          </div>
        </div>

        {error && (
          <div style={{
            background: 'rgba(239,68,68,0.08)', border: '1px solid #EF444433',
            borderRadius: 10, padding: '14px 18px', marginBottom: 24,
            color: '#EF4444', fontSize: 14, display: 'flex', gap: 10, alignItems: 'center',
          }}>
            <AlertTriangle size={16} /> {error}
          </div>
        )}

        {loading && !data && (
          <div style={{ textAlign: 'center', padding: '80px 0' }}>
            <RefreshCw size={24} color="#00C6FF" style={{ animation: 'spin 1s linear infinite', marginBottom: 16 }} />
            <p style={{ color: '#666688' }}>Loading governance data…</p>
          </div>
        )}

        {data && (
          <>
            {/* KPIs */}
            <div style={{ display: 'flex', gap: 16, marginBottom: 28 }}>
              <KpiCard
                label="Total Decisions"
                value={stats?.total_decisions ?? 0}
                sub={`Last ${days} days`}
                accent="#00C6FF"
              />
              <KpiCard
                label="Approved"
                value={stats?.approved ?? 0}
                sub={`${stats?.approval_rate ?? 0}% approval rate`}
                accent="#10B981"
              />
              <KpiCard
                label="Blocked"
                value={stats?.blocked ?? 0}
                sub="Governance controls enforced"
                accent="#EF4444"
              />
              <KpiCard
                label="Frameworks"
                value={data.regulatory_coverage.frameworks_count}
                sub={`${data.regulatory_coverage.checkpoints_mapped} checkpoints mapped`}
                accent="#7B2FFF"
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 28 }}>
              {/* DOMAIN BREAKDOWN */}
              <div style={{
                background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: 14, padding: 24,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
                  <BarChart3 size={16} color="#00C6FF" />
                  <span style={{ fontWeight: 700, fontSize: 14 }}>Domain Breakdown</span>
                </div>
                {domains.length === 0 ? (
                  <p style={{ color: '#444466', fontSize: 13, textAlign: 'center', padding: '20px 0' }}>
                    No domain data available for this period.
                  </p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                    {domains.map(([domain, dstats]) => {
                      const rate = dstats.total ? Math.round(dstats.approved / dstats.total * 100) : 0
                      const color = DOMAIN_COLORS[domain] || '#666688'
                      return (
                        <div key={domain}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                            <span style={{ fontSize: 13, color: '#AAB0CC' }}>
                              {DOMAIN_ICONS[domain] || '◆'} {DOMAIN_LABELS[domain] || domain}
                            </span>
                            <span style={{ fontSize: 12, fontWeight: 700, color }}>
                              {rate}% · {dstats.total} decisions
                            </span>
                          </div>
                          <div style={{ height: 6, background: 'rgba(255,255,255,0.06)', borderRadius: 99 }}>
                            <div style={{
                              height: 6, borderRadius: 99, width: `${rate}%`,
                              background: `linear-gradient(90deg, ${color}, ${color}88)`,
                              transition: 'width 0.6s ease',
                            }} />
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>

              {/* REGULATORY FRAMEWORKS */}
              <div style={{
                background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: 14, padding: 24,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
                  <Globe size={16} color="#7B2FFF" />
                  <span style={{ fontWeight: 700, fontSize: 14 }}>Regulatory Coverage</span>
                  <span style={{
                    marginLeft: 'auto', fontSize: 11, fontWeight: 700,
                    background: 'rgba(123,47,255,0.15)', color: '#7B2FFF',
                    padding: '2px 8px', borderRadius: 12,
                  }}>
                    {data.regulatory_coverage.frameworks_count} frameworks
                  </span>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                  {data.regulatory_coverage.frameworks.map(fw => (
                    <div
                      key={fw}
                      style={{
                        padding: '5px 12px', borderRadius: 20, fontSize: 11, fontWeight: 700,
                        background: `${FW_COLORS[fw] || '#666688'}18`,
                        color: FW_COLORS[fw] || '#AAB0CC',
                        border: `1px solid ${FW_COLORS[fw] || '#666688'}33`,
                        letterSpacing: '0.04em',
                      }}
                    >
                      {FW_SHORT[fw] || fw}
                    </div>
                  ))}
                </div>
                <div style={{
                  marginTop: 16, padding: '12px 14px',
                  background: 'rgba(16,185,129,0.06)', borderRadius: 10,
                  border: '1px solid rgba(16,185,129,0.15)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <CheckCircle size={13} color="#10B981" />
                    <span style={{ fontSize: 12, fontWeight: 700, color: '#10B981' }}>
                      {data.regulatory_coverage.checkpoints_mapped} checkpoints mapped
                    </span>
                  </div>
                  <p style={{ color: '#444466', fontSize: 11, margin: 0, lineHeight: 1.5 }}>
                    Every governance receipt includes a regulatory alignment attestation linking
                    each checkpoint result to applicable frameworks.
                  </p>
                </div>
              </div>
            </div>

            {/* RECENT RECEIPTS */}
            <div style={{
              background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: 14, padding: 24, marginBottom: 28,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
                <Activity size={16} color="#00C6FF" />
                <span style={{ fontWeight: 700, fontSize: 14 }}>Recent Governance Receipts</span>
                <span style={{
                  marginLeft: 'auto', fontSize: 11, color: '#444466',
                }}>
                  Post-quantum signed · Chain-linked
                </span>
              </div>

              {receipts.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '30px 0', color: '#444466' }}>
                  <FileText size={32} style={{ marginBottom: 12, opacity: 0.4 }} />
                  <p style={{ fontSize: 13 }}>No receipts found for this period.</p>
                </div>
              ) : (
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr>
                        {['Receipt ID', 'Decision', 'Domain', 'Asset', 'Timestamp'].map(h => (
                          <th key={h} style={{
                            textAlign: 'left', padding: '8px 12px',
                            color: '#444466', fontSize: 11, fontWeight: 700,
                            letterSpacing: '0.08em', borderBottom: '1px solid rgba(255,255,255,0.07)',
                          }}>{h.toUpperCase()}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {receipts.map((r, i) => (
                        <tr
                          key={r.receipt_id}
                          style={{
                            borderBottom: '1px solid rgba(255,255,255,0.04)',
                            background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.015)',
                          }}
                        >
                          <td style={{ padding: '10px 12px' }}>
                            <code style={{ fontSize: 11, color: '#00C6FF', fontFamily: 'monospace' }}>
                              {r.receipt_id.slice(0, 24)}…
                            </code>
                          </td>
                          <td style={{ padding: '10px 12px' }}>
                            <DecisionBadge decision={r.decision} />
                          </td>
                          <td style={{ padding: '10px 12px', fontSize: 12, color: '#AAB0CC' }}>
                            {DOMAIN_ICONS[r.domain] || ''} {DOMAIN_LABELS[r.domain] || r.domain || '—'}
                          </td>
                          <td style={{ padding: '10px 12px', fontSize: 12, color: '#AAB0CC' }}>
                            {r.asset || '—'}
                          </td>
                          <td style={{ padding: '10px 12px', fontSize: 11, color: '#444466', fontFamily: 'monospace' }}>
                            {r.timestamp?.slice(0, 19).replace('T', ' ') || '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* ATTESTATION */}
            <div style={{
              background: 'linear-gradient(135deg, rgba(0,198,255,0.05), rgba(123,47,255,0.05))',
              border: '1px solid rgba(0,198,255,0.15)', borderRadius: 14, padding: 24,
              marginBottom: 28,
            }}>
              <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                <div style={{
                  width: 36, height: 36, borderRadius: 10,
                  background: 'rgba(0,198,255,0.10)', flexShrink: 0,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <Lock size={16} color="#00C6FF" />
                </div>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 6 }}>
                    Cryptographic Attestation
                  </div>
                  <p style={{ color: '#666688', fontSize: 12, margin: 0, lineHeight: 1.7 }}>
                    {data.attestation}
                  </p>
                </div>
              </div>
            </div>

            {/* SDK SECTION */}
            <div style={{
              background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.07)',
              borderRadius: 14, padding: 24,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
                <Zap size={16} color="#F59E0B" />
                <span style={{ fontWeight: 700, fontSize: 14 }}>Integration SDKs</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                {[
                  {
                    lang: 'Python',
                    icon: '🐍',
                    code: `from omnix_sdk import OmnixClient\nclient = OmnixClient(api_key="${apiKey.slice(0,16)}…")\nresult = client.evaluate(signals)\nprint(result["decision"])  # APPROVED`,
                  },
                  {
                    lang: 'Node.js',
                    icon: '⬡',
                    code: `const OmnixClient = require('./omnix_sdk');\nconst client = new OmnixClient({ apiKey: '${apiKey.slice(0,16)}…' });\nconst result = await client.evaluate(signals);\nconsole.log(result.decision);  // APPROVED`,
                  },
                ].map(({ lang, icon, code }) => (
                  <div
                    key={lang}
                    style={{
                      background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)',
                      borderRadius: 10, padding: 16,
                    }}
                  >
                    <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 12, color: '#AAB0CC' }}>
                      {icon} {lang} SDK
                    </div>
                    <pre style={{
                      background: 'rgba(0,0,0,0.3)', borderRadius: 8, padding: '12px 14px',
                      fontSize: 11, color: '#10B981', margin: 0, overflow: 'auto',
                      fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                      lineHeight: 1.6,
                    }}>{code}</pre>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        * { box-sizing: border-box; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #0A0A0F; }
        ::-webkit-scrollbar-thumb { background: #1A1A2E; border-radius: 99px; }
      `}</style>
    </div>
  )
}
