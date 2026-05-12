import { useState, useCallback } from 'react'

const GOLD = '#C9A227'
const NAVY = '#060F1E'
const NAVY2 = '#0A1628'
const BORDER = 'rgba(201,162,39,0.18)'

type VerificationResult = {
  delegation_id: string
  hash_valid: boolean
  pqc_signature_valid: boolean
  pqc_checked: boolean
  mar_invariant_valid: boolean
  not_expired: boolean
  fully_verified: boolean
  delegation_depth: number
  authority_budget_granted: number
  authority_reduction_pct: number
  chain_root_id: string
  pqc_signed: boolean
  delegator_id: string
  delegate_id: string
  status: string
}

type ApiResponse = {
  verification: VerificationResult
  status: 'verified' | 'invalid'
}

const EXAMPLE_PLACEHOLDER = `{
  "delegation_id": "ATFDR-8B2C4D6E1F3A5B7C",
  "delegator_id": "HUMAN-TIER1-HN-001",
  "delegate_id": "AID-FINANCE-3A7F9B2C1D4E5F6A",
  "task_scope": {
    "action": "compute_portfolio_risk",
    "domain": "FINANCE"
  },
  "authority_budget_delegator": 100.0,
  "authority_budget_granted": 60.0,
  "chain_root_id": "ATFDR-8B2C4D6E1F3A5B7C",
  "delegation_depth": 1,
  "delegator_public_key": "<base64-dilithium3-pubkey>",
  "content_hash": "<sha256-hex>",
  "pqc_signature": "<base64-dilithium3-sig>",
  "status": "ACTIVE"
}`

function CheckRow({ ok, label, detail }: { ok: boolean; label: string; detail?: string }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'flex-start', gap: 12,
      padding: '10px 0', borderBottom: `1px solid ${BORDER}`,
    }}>
      <div style={{
        width: 24, height: 24, borderRadius: '50%', flexShrink: 0,
        background: ok ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)',
        border: `1.5px solid ${ok ? '#22c55e' : '#ef4444'}`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        marginTop: 1,
      }}>
        <span style={{ fontSize: 13, color: ok ? '#22c55e' : '#ef4444' }}>
          {ok ? '✓' : '✗'}
        </span>
      </div>
      <div>
        <div style={{ color: ok ? '#e2e8f0' : '#fca5a5', fontSize: 14, fontWeight: 500 }}>
          {label}
        </div>
        {detail && (
          <div style={{ color: '#64748b', fontSize: 12, marginTop: 3 }}>{detail}</div>
        )}
      </div>
    </div>
  )
}

function BudgetBar({ granted, delegator }: { granted: number; delegator: number }) {
  const pct = delegator > 0 ? Math.min(100, (granted / delegator) * 100) : 0
  const reduction = delegator > 0 ? (1 - granted / delegator) * 100 : 0
  return (
    <div style={{ marginTop: 4 }}>
      <div style={{
        height: 8, borderRadius: 4,
        background: 'rgba(255,255,255,0.05)',
        position: 'relative', overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute', left: 0, top: 0, bottom: 0,
          width: `${pct}%`, background: GOLD, borderRadius: 4,
          transition: 'width 0.5s ease',
        }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
        <span style={{ color: GOLD, fontSize: 12 }}>Granted: {granted.toFixed(1)}</span>
        <span style={{ color: '#64748b', fontSize: 12 }}>Reduced {reduction.toFixed(1)}% from {delegator}</span>
      </div>
    </div>
  )
}

export default function ATFVerifierPage() {
  const [mode, setMode] = useState<'id' | 'json'>('id')
  const [inputId, setInputId] = useState('')
  const [inputJson, setInputJson] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ApiResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const verify = useCallback(async () => {
    setLoading(true)
    setResult(null)
    setError(null)

    try {
      let body: Record<string, unknown>

      if (mode === 'id') {
        const id = inputId.trim()
        if (!id) { setError('Enter a delegation ID (ATFDR-...).'); setLoading(false); return }
        body = { delegation_id: id }
      } else {
        const raw = inputJson.trim()
        if (!raw) { setError('Paste a delegation receipt JSON.'); setLoading(false); return }
        let parsed: unknown
        try { parsed = JSON.parse(raw) } catch {
          setError('Invalid JSON — check the format and try again.'); setLoading(false); return
        }
        body = { receipt: parsed }
      }

      const res = await fetch('/api/atf/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await res.json()

      if (!res.ok || data.error) {
        setError(data.error || `Server returned ${res.status}`)
      } else {
        setResult(data as ApiResponse)
      }
    } catch (err) {
      setError('Network error — check your connection.')
    } finally {
      setLoading(false)
    }
  }, [mode, inputId, inputJson])

  const v = result?.verification
  const verified = result?.status === 'verified'

  return (
    <div style={{
      minHeight: '100vh', background: NAVY, color: '#e2e8f0',
      fontFamily: '"Inter", -apple-system, sans-serif',
    }}>
      {/* Header */}
      <div style={{
        borderBottom: `1px solid ${BORDER}`,
        padding: '24px 0',
        background: NAVY2,
      }}>
        <div style={{ maxWidth: 860, margin: '0 auto', padding: '0 24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <div style={{
              width: 48, height: 48, borderRadius: 12,
              background: 'rgba(201,162,39,0.12)',
              border: `1px solid ${BORDER}`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 22,
            }}>🔐</div>
            <div>
              <div style={{ fontSize: 22, fontWeight: 700, color: '#f1f5f9' }}>
                ATF Public Verifier
              </div>
              <div style={{ color: '#64748b', fontSize: 13, marginTop: 2 }}>
                RFC-ATF-1 · ML-DSA-65 (Dilithium-3) · Independent verification — no account required
              </div>
            </div>
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 860, margin: '0 auto', padding: '36px 24px' }}>
        {/* Protocol notice */}
        <div style={{
          padding: '14px 18px', borderRadius: 10, marginBottom: 32,
          background: 'rgba(201,162,39,0.06)',
          border: `1px solid rgba(201,162,39,0.20)`,
          fontSize: 13, color: '#94a3b8', lineHeight: 1.6,
        }}>
          <strong style={{ color: GOLD }}>ATF-INV-006 — Independent Verifiability:</strong>{' '}
          Any party can verify an Agent Trust Fabric delegation receipt using only the receipt itself
          and the delegator's embedded public key. No platform access, API key, or account required.
          Receipts signed with Dilithium-3 (FIPS 204, 128-bit post-quantum security).
        </div>

        {/* Mode tabs */}
        <div style={{
          display: 'flex', gap: 4, background: 'rgba(255,255,255,0.04)',
          borderRadius: 10, padding: 4, marginBottom: 24,
          border: `1px solid ${BORDER}`,
        }}>
          {([['id', '🔍  Verify by ID'], ['json', '📋  Paste Receipt JSON']] as const).map(([m, label]) => (
            <button
              key={m}
              onClick={() => { setMode(m); setResult(null); setError(null) }}
              style={{
                flex: 1, padding: '10px 0', borderRadius: 8, border: 'none',
                cursor: 'pointer', fontSize: 13, fontWeight: 600,
                background: mode === m ? 'rgba(201,162,39,0.18)' : 'transparent',
                color: mode === m ? GOLD : '#64748b',
                transition: 'all 0.2s',
              }}
            >{label}</button>
          ))}
        </div>

        {/* Input */}
        {mode === 'id' ? (
          <div style={{ marginBottom: 20 }}>
            <label style={{ display: 'block', fontSize: 13, color: '#94a3b8', marginBottom: 8, fontWeight: 500 }}>
              Delegation Receipt ID
            </label>
            <input
              type="text"
              value={inputId}
              onChange={e => setInputId(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && verify()}
              placeholder="ATFDR-8B2C4D6E1F3A5B7C"
              style={{
                width: '100%', padding: '12px 16px', borderRadius: 10,
                background: NAVY2, border: `1.5px solid ${BORDER}`,
                color: '#f1f5f9', fontSize: 14, fontFamily: 'inherit',
                outline: 'none', boxSizing: 'border-box',
              }}
            />
          </div>
        ) : (
          <div style={{ marginBottom: 20 }}>
            <label style={{ display: 'block', fontSize: 13, color: '#94a3b8', marginBottom: 8, fontWeight: 500 }}>
              Delegation Receipt JSON
            </label>
            <textarea
              value={inputJson}
              onChange={e => setInputJson(e.target.value)}
              placeholder={EXAMPLE_PLACEHOLDER}
              rows={12}
              style={{
                width: '100%', padding: '12px 16px', borderRadius: 10,
                background: NAVY2, border: `1.5px solid ${BORDER}`,
                color: '#f1f5f9', fontSize: 13,
                fontFamily: '"JetBrains Mono", "Fira Code", monospace',
                resize: 'vertical', outline: 'none', boxSizing: 'border-box',
                lineHeight: 1.5,
              }}
            />
          </div>
        )}

        {/* Verify button */}
        <button
          onClick={verify}
          disabled={loading}
          style={{
            width: '100%', padding: '14px', borderRadius: 10, border: 'none',
            background: loading ? 'rgba(201,162,39,0.4)' : GOLD,
            color: '#060F1E', fontSize: 15, fontWeight: 700,
            cursor: loading ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s',
          }}
        >
          {loading ? '⟳  Verifying...' : '🔐  Verify Receipt'}
        </button>

        {/* Error */}
        {error && (
          <div style={{
            marginTop: 20, padding: '14px 18px', borderRadius: 10,
            background: 'rgba(239,68,68,0.08)',
            border: '1px solid rgba(239,68,68,0.25)',
            color: '#fca5a5', fontSize: 14,
          }}>
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Result */}
        {v && (
          <div style={{ marginTop: 32 }}>
            {/* Verdict banner */}
            <div style={{
              padding: '20px 24px', borderRadius: 14,
              background: verified ? 'rgba(34,197,94,0.06)' : 'rgba(239,68,68,0.06)',
              border: `1.5px solid ${verified ? 'rgba(34,197,94,0.30)' : 'rgba(239,68,68,0.30)'}`,
              display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24,
            }}>
              <div style={{
                width: 52, height: 52, borderRadius: '50%', flexShrink: 0,
                background: verified ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)',
                border: `2px solid ${verified ? '#22c55e' : '#ef4444'}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 26,
              }}>
                {verified ? '✓' : '✗'}
              </div>
              <div>
                <div style={{
                  fontSize: 20, fontWeight: 800,
                  color: verified ? '#22c55e' : '#ef4444',
                }}>
                  {verified ? 'VERIFIED' : 'INVALID'}
                </div>
                <div style={{ fontSize: 13, color: '#94a3b8', marginTop: 2 }}>
                  {v.delegation_id}
                </div>
              </div>
              {v.pqc_signed && (
                <div style={{
                  marginLeft: 'auto',
                  padding: '6px 14px', borderRadius: 20,
                  background: 'rgba(201,162,39,0.10)',
                  border: `1px solid rgba(201,162,39,0.25)`,
                  fontSize: 12, fontWeight: 600, color: GOLD,
                }}>
                  ML-DSA-65 Signed
                </div>
              )}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
              {/* Left: Checks */}
              <div style={{
                background: NAVY2, borderRadius: 12,
                border: `1px solid ${BORDER}`, padding: 20,
              }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: '#94a3b8', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Verification Checks
                </div>
                <CheckRow
                  ok={v.hash_valid}
                  label="Content Hash"
                  detail={v.hash_valid ? 'SHA-256 matches — no tampering detected' : 'Hash mismatch — field tampering detected'}
                />
                <CheckRow
                  ok={v.pqc_checked ? v.pqc_signature_valid : true}
                  label={v.pqc_checked ? 'PQC Signature (ML-DSA-65)' : 'PQC Signature'}
                  detail={v.pqc_checked
                    ? (v.pqc_signature_valid ? 'Dilithium-3 signature valid' : 'Signature invalid — key mismatch')
                    : (v.pqc_signed ? 'Signature present — library unavailable for verification' : 'No PQC signature (SHA-256 only)')}
                />
                <CheckRow
                  ok={v.mar_invariant_valid}
                  label="MAR Invariant (ATF-INV-001)"
                  detail={v.mar_invariant_valid
                    ? `Budget: ${v.authority_budget_granted} ≤ delegator (no expansion)`
                    : 'Authority expansion detected — invariant violated'}
                />
                <CheckRow
                  ok={v.not_expired}
                  label="Expiry Status"
                  detail={v.not_expired ? 'Receipt is not expired' : 'Receipt has expired'}
                />
                <CheckRow
                  ok={v.status === 'ACTIVE'}
                  label={`Status: ${v.status}`}
                  detail={v.status === 'ACTIVE' ? 'Receipt is ACTIVE' : `Receipt is ${v.status}`}
                />
              </div>

              {/* Right: Details */}
              <div style={{
                background: NAVY2, borderRadius: 12,
                border: `1px solid ${BORDER}`, padding: 20,
              }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: '#94a3b8', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Authority Details
                </div>

                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 12, color: '#64748b', marginBottom: 4 }}>Authority Budget</div>
                  <BudgetBar granted={v.authority_budget_granted} delegator={100} />
                </div>

                <div style={{ display: 'grid', gap: 10 }}>
                  {[
                    ['Delegation Depth', `Depth ${v.delegation_depth}`],
                    ['Authority Granted', `${v.authority_budget_granted.toFixed(1)} / 100`],
                    ['Reduction', `${v.authority_reduction_pct.toFixed(1)}%`],
                    ['Chain Root', v.chain_root_id || '—'],
                  ].map(([label, value]) => (
                    <div key={label} style={{
                      display: 'flex', justifyContent: 'space-between',
                      padding: '8px 0', borderBottom: `1px solid ${BORDER}`,
                    }}>
                      <span style={{ fontSize: 12, color: '#64748b' }}>{label}</span>
                      <span style={{
                        fontSize: 12, color: '#e2e8f0',
                        fontFamily: '"JetBrains Mono", monospace',
                        maxWidth: '55%', textAlign: 'right',
                        overflow: 'hidden', textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}>{value}</span>
                    </div>
                  ))}
                </div>

                <div style={{ marginTop: 16, paddingTop: 14, borderTop: `1px solid ${BORDER}` }}>
                  <div style={{ fontSize: 12, color: '#64748b', marginBottom: 6 }}>Delegator</div>
                  <div style={{
                    fontSize: 12, color: GOLD,
                    fontFamily: '"JetBrains Mono", monospace',
                    wordBreak: 'break-all',
                  }}>{v.delegator_id}</div>
                  <div style={{ fontSize: 12, color: '#64748b', marginBottom: 6, marginTop: 10 }}>Delegate</div>
                  <div style={{
                    fontSize: 12, color: '#94a3b8',
                    fontFamily: '"JetBrains Mono", monospace',
                    wordBreak: 'break-all',
                  }}>{v.delegate_id}</div>
                </div>
              </div>
            </div>

            {/* RFC notice */}
            <div style={{
              marginTop: 20, padding: '12px 18px', borderRadius: 10,
              background: 'rgba(255,255,255,0.02)',
              border: `1px solid ${BORDER}`,
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              flexWrap: 'wrap', gap: 12,
            }}>
              <span style={{ fontSize: 12, color: '#475569' }}>
                Protocol: RFC-ATF-1 · Algorithm: ML-DSA-65 (Dilithium-3, FIPS 204) · OMNIX QUANTUM LTD
              </span>
              <a
                href="/agent-trust-fabric"
                style={{ fontSize: 12, color: GOLD, textDecoration: 'none', fontWeight: 500 }}
              >
                View ATF Dashboard →
              </a>
            </div>
          </div>
        )}

        {/* CLI section */}
        <div style={{
          marginTop: 48, padding: '24px', borderRadius: 14,
          background: 'rgba(255,255,255,0.02)',
          border: `1px solid ${BORDER}`,
        }}>
          <div style={{ fontSize: 15, fontWeight: 700, color: '#f1f5f9', marginBottom: 6 }}>
            Standalone CLI Verifier
          </div>
          <div style={{ fontSize: 13, color: '#64748b', marginBottom: 16, lineHeight: 1.6 }}>
            The ATF Public Verifier CLI runs entirely offline — no network, no account, no API key.
            Download <code style={{ color: GOLD, background: 'rgba(201,162,39,0.1)', padding: '1px 5px', borderRadius: 4 }}>omnix_atf_verify.py</code> and
            verify any delegation receipt independently.
          </div>
          <div style={{
            background: NAVY, borderRadius: 10,
            border: `1px solid rgba(255,255,255,0.06)`,
            padding: '16px 20px',
            fontFamily: '"JetBrains Mono", "Fira Code", monospace',
            fontSize: 13, lineHeight: 1.8, color: '#94a3b8',
          }}>
            <div><span style={{ color: '#22c55e' }}>$</span> python omnix_atf_verify.py receipt.json</div>
            <div><span style={{ color: '#22c55e' }}>$</span> python omnix_atf_verify.py receipt.json <span style={{ color: '#64748b' }}>--verbose</span></div>
            <div><span style={{ color: '#22c55e' }}>$</span> python omnix_atf_verify.py chain.json <span style={{ color: '#64748b' }}>--mode chain</span></div>
            <div><span style={{ color: '#22c55e' }}>$</span> python omnix_atf_verify.py receipt.json <span style={{ color: '#64748b' }}>--json</span></div>
          </div>
          <div style={{ marginTop: 12, fontSize: 12, color: '#475569' }}>
            ATF-INV-006 — Independent Verifiability: requires no OMNIX platform access.
            Compliant with RFC-ATF-1 §8 (Offline Verification).
          </div>
        </div>

        {/* Formal verification notice */}
        <div style={{
          marginTop: 20, padding: '20px 24px', borderRadius: 14,
          display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16,
        }}>
          {[
            {
              icon: '📐',
              title: 'TLA+ Formal Verification',
              desc: 'MAR invariant, acyclicity, and immutability proven in TLA+ using the same formal methods as AWS DynamoDB.',
            },
            {
              icon: '📄',
              title: 'RFC-ATF-1 Standard',
              desc: 'Full IETF-style specification with ABNF grammar, 6 invariants, 3 compliance levels, and security considerations.',
            },
          ].map(item => (
            <div key={item.title} style={{
              padding: '18px', borderRadius: 12,
              background: 'rgba(255,255,255,0.02)',
              border: `1px solid ${BORDER}`,
            }}>
              <div style={{ fontSize: 22, marginBottom: 8 }}>{item.icon}</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: '#f1f5f9', marginBottom: 6 }}>{item.title}</div>
              <div style={{ fontSize: 12, color: '#64748b', lineHeight: 1.6 }}>{item.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
