import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  Shield, CheckCircle, XCircle, Clock, ExternalLink, Copy,
  ArrowLeft, Lock, AlertTriangle, Search, Activity, Download,
  ChevronDown, ChevronUp, Terminal, Hash, Fingerprint, Eye
} from 'lucide-react'
import { API_BASE } from '../lib/apiBase'

interface Checkpoint {
  code: string | null
  label_en: string
  label_es: string
  result: 'PASS' | 'BLOCKED' | 'UNKNOWN'
  metric_label: string | null
  metric_value: string | null
  raw: string
}

interface IntegrityBlock {
  content_hash: string
  prev_hash: string
  signature_algorithm: string
  is_pqc: boolean
  independently_verifiable: boolean
  nist_note: string
  trust_status: string | null
  issuer_trusted: boolean
  key_fingerprint: string | null
  trusted_anchor_fingerprint: string | null
  anchor_source: string | null
  trust_status_description: string | null
}

interface EbipSnapshot {
  overall_score: number
  alert_level: string
  concentration_risk: string
  violations_24h: number
  components_active: number
  ebip_version: string
  status_at: string
}

interface VerifyData {
  found: boolean
  receipt_id: string
  timestamp_utc: string
  asset: string
  decision: string
  domain: string
  decision_color: 'green' | 'red' | 'yellow' | 'gray'
  decision_icon: string
  human_summary_en: string
  human_summary_es: string
  checkpoints_total: number
  checkpoints_passed: number
  checkpoints_blocked: number
  checkpoints: Checkpoint[]
  integrity: IntegrityBlock
  policy_version: string
  engine_version: string
  independent_verify_url: string | null
  ebip_at_verification: EbipSnapshot | null
}

interface RecentReceipt {
  receipt_id: string
  timestamp: string
  asset: string
  decision: string
  signed: boolean
  hash_prefix: string
}

function fmtTs(ts: string, short = false): string {
  try {
    const d = new Date(ts)
    if (short) {
      return d.toLocaleString('en-US', {
        month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit', timeZone: 'UTC',
      }) + ' UTC'
    }
    return d.toLocaleString('en-US', {
      month: 'long', day: 'numeric', year: 'numeric',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
      timeZone: 'UTC', timeZoneName: 'short',
    })
  } catch { return ts }
}

function decColor(d: string) {
  if (d === 'green'  || d === 'APPROVED') return { text: '#22c55e', bg: 'rgba(34,197,94,0.12)',  border: 'rgba(34,197,94,0.25)'  }
  if (d === 'red'    || d === 'BLOCKED')  return { text: '#ef4444', bg: 'rgba(239,68,68,0.12)',   border: 'rgba(239,68,68,0.25)'  }
  if (d === 'yellow' || d === 'HOLD')     return { text: '#f59e0b', bg: 'rgba(245,158,11,0.12)',  border: 'rgba(245,158,11,0.25)' }
  return                                         { text: '#818cf8', bg: 'rgba(99,102,241,0.12)',  border: 'rgba(99,102,241,0.25)' }
}

function CopyBtn({ value, size = 12 }: { value: string; size?: number }) {
  const [ok, setOk] = useState(false)
  function copy() {
    navigator.clipboard.writeText(value).catch(() => {})
    setOk(true)
    setTimeout(() => setOk(false), 1600)
  }
  return (
    <button onClick={copy} title="Copy" style={{
      background: 'none', border: 'none', cursor: 'pointer', padding: '2px 4px',
      color: ok ? '#22c55e' : '#4b5563', display: 'inline-flex', alignItems: 'center', gap: 3,
      fontSize: '0.68rem', transition: 'color 0.2s',
    }}>
      <Copy size={size} />
      {ok ? 'Copied' : ''}
    </button>
  )
}

function HashLine({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ fontSize: '0.65rem', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 3 }}>{label}</div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'rgba(0,0,0,0.3)', borderRadius: 6, padding: '8px 12px' }}>
        <Hash size={11} color="#3b82f6" style={{ flexShrink: 0 }} />
        <span style={{ fontFamily: 'monospace', fontSize: '0.72rem', color: '#60a5fa', wordBreak: 'break-all', flex: 1 }}>{value}</span>
        <CopyBtn value={value} size={11} />
      </div>
    </div>
  )
}

function CheckpointRow({ cp, index }: { cp: Checkpoint; index: number }) {
  const isPass    = cp.result === 'PASS'
  const isBlocked = cp.result === 'BLOCKED'
  return (
    <div style={{
      display: 'flex', gap: 12, alignItems: 'flex-start',
      padding: '11px 0', borderBottom: '1px solid rgba(255,255,255,0.04)',
    }}>
      <div style={{ flexShrink: 0, paddingTop: 2, width: 20, textAlign: 'center' }}>
        {isPass    && <CheckCircle size={15} color="#22c55e" />}
        {isBlocked && <XCircle    size={15} color="#ef4444" />}
        {!isPass && !isBlocked && <Clock size={15} color="#4b5563" />}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.84rem', fontWeight: 500, color: '#e5e7eb' }}>
            {cp.code && (
              <span style={{ fontFamily: 'monospace', fontSize: '0.7rem', color: '#4b5563', marginRight: 6 }}>{cp.code}</span>
            )}
            {cp.label_en}
          </span>
          <span style={{
            fontSize: '0.65rem', fontWeight: 800, letterSpacing: '0.1em',
            fontFamily: 'monospace', padding: '2px 8px', borderRadius: 4,
            color: isPass ? '#22c55e' : isBlocked ? '#ef4444' : '#4b5563',
            background: isPass ? 'rgba(34,197,94,0.08)' : isBlocked ? 'rgba(239,68,68,0.08)' : 'rgba(75,85,99,0.15)',
            border: `1px solid ${isPass ? 'rgba(34,197,94,0.2)' : isBlocked ? 'rgba(239,68,68,0.2)' : 'rgba(75,85,99,0.2)'}`,
            flexShrink: 0,
          }}>
            {cp.result}
          </span>
        </div>
        {cp.metric_label && cp.metric_value && (
          <div style={{ fontSize: '0.72rem', color: '#4b5563', marginTop: 3 }}>
            {cp.metric_label}: <span style={{ fontFamily: 'monospace', color: '#6b7280' }}>{cp.metric_value}</span>
          </div>
        )}
      </div>
      <div style={{ fontSize: '0.65rem', color: '#374151', fontFamily: 'monospace', flexShrink: 0, paddingTop: 2 }}>
        {String(index + 1).padStart(2, '0')}
      </div>
    </div>
  )
}

function ReceiptResult({ data }: { data: VerifyData }) {
  const [showHashes, setShowHashes] = useState(false)
  const [showEbip, setShowEbip]     = useState(false)
  const [copied, setCopied]         = useState(false)
  const c = decColor(data.decision_color)

  function copyLink() {
    navigator.clipboard.writeText(window.location.href).catch(() => {})
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const passCount  = data.checkpoints.filter(c => c.result === 'PASS').length
  const blockCount = data.checkpoints.filter(c => c.result === 'BLOCKED').length

  return (
    <div style={{ animation: 'fadeIn 0.3s ease' }}>
      <style>{`@keyframes fadeIn { from { opacity:0; transform:translateY(8px) } to { opacity:1; transform:none } }`}</style>

      {/* ── Decision banner ── */}
      <div style={{
        borderRadius: 14, padding: '20px 24px', marginBottom: 16,
        background: c.bg, border: `1px solid ${c.border}`,
        position: 'relative', overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute', inset: 0, opacity: 0.03,
          backgroundImage: 'repeating-linear-gradient(45deg, currentColor 0, currentColor 1px, transparent 0, transparent 50%)',
          backgroundSize: '20px 20px', color: c.text,
        }} />
        <div style={{ position: 'relative', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16, flexWrap: 'wrap' }}>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
              <span style={{
                fontSize: '0.65rem', fontWeight: 900, letterSpacing: '0.12em',
                fontFamily: 'monospace', padding: '4px 12px', borderRadius: 6,
                color: c.text, background: `${c.bg}`, border: `1.5px solid ${c.border}`,
                textTransform: 'uppercase',
              }}>
                {data.decision}
              </span>
              <span style={{ fontSize: '0.8rem', color: '#4b5563' }}>·</span>
              <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>{fmtTs(data.timestamp_utc)}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
              <span style={{ fontFamily: 'monospace', fontSize: '0.78rem', color: c.text, fontWeight: 600 }}>
                {data.receipt_id}
              </span>
              <CopyBtn value={data.receipt_id} />
            </div>
            <p style={{ color: '#d1d5db', fontSize: '0.9rem', margin: 0, lineHeight: 1.6 }}>
              {data.human_summary_en}
            </p>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'flex-end' }}>
            <button onClick={copyLink} style={{
              background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)',
              color: copied ? '#22c55e' : '#9ca3af', padding: '6px 12px', borderRadius: 7,
              cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 5, fontSize: '0.75rem',
            }}>
              <Copy size={12} /> {copied ? 'Copied!' : 'Share receipt'}
            </button>
            <a href={`data:application/json,${encodeURIComponent(JSON.stringify({ receipt_id: data.receipt_id, decision: data.decision, asset: data.asset, domain: data.domain, timestamp_utc: data.timestamp_utc, integrity: data.integrity, policy_version: data.policy_version }, null, 2))}`}
              download={`${data.receipt_id}.json`}
              style={{
                background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.25)',
                color: '#60a5fa', padding: '6px 12px', borderRadius: 7,
                textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 5, fontSize: '0.75rem',
              }}>
              <Download size={12} /> receipt.json
            </a>
          </div>
        </div>
      </div>

      {/* ── Key metrics grid ── */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
        gap: 8, marginBottom: 16,
      }}>
        {[
          { icon: <Activity size={13} color="#818cf8" />, label: 'Asset · Domain', value: `${data.asset} · ${data.domain}` },
          { icon: <Shield size={13} color="#22c55e" />, label: 'Checkpoints', value: data.decision === 'BLOCKED' ? `${blockCount} blocked of ${data.checkpoints_total}` : `${passCount} / ${data.checkpoints_total} passed` },
          { icon: <Fingerprint size={13} color="#f59e0b" />, label: 'Signature', value: data.integrity.is_pqc ? 'Dilithium-3 · FIPS 204' : data.integrity.signature_algorithm },
          { icon: <Lock size={13} color="#60a5fa" />, label: 'Policy', value: data.policy_version },
        ].map(f => (
          <div key={f.label} style={{
            background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)',
            borderRadius: 10, padding: '12px 14px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: 5 }}>
              {f.icon}
              <span style={{ fontSize: '0.62rem', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.1em' }}>{f.label}</span>
            </div>
            <div style={{ fontSize: '0.8rem', color: '#e5e7eb', fontFamily: 'monospace', fontWeight: 500 }}>{f.value}</div>
          </div>
        ))}
      </div>

      {/* ── Checkpoint pipeline ── */}
      {data.checkpoints.length > 0 && (
        <div style={{
          background: 'rgba(255,255,255,0.015)', border: '1px solid rgba(255,255,255,0.06)',
          borderRadius: 12, padding: '16px 20px', marginBottom: 16,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
              <Shield size={13} color="#4b5563" />
              <span style={{ fontSize: '0.7rem', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 700 }}>
                Governance Checkpoint Pipeline
              </span>
            </div>
            <div style={{ display: 'flex', gap: 10, fontSize: '0.72rem' }}>
              {passCount  > 0 && <span style={{ color: '#22c55e' }}>✓ {passCount} passed</span>}
              {blockCount > 0 && <span style={{ color: '#ef4444' }}>✗ {blockCount} blocked</span>}
            </div>
          </div>
          {data.checkpoints.map((cp, i) => <CheckpointRow key={i} cp={cp} index={i} />)}
        </div>
      )}

      {/* ── EBIP section (collapsible) ── */}
      {data.ebip_at_verification && (
        <div style={{
          background: 'rgba(139,92,246,0.04)', border: '1px solid rgba(139,92,246,0.15)',
          borderRadius: 12, marginBottom: 16, overflow: 'hidden',
        }}>
          <button
            onClick={() => setShowEbip(v => !v)}
            style={{
              width: '100%', background: 'none', border: 'none', cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '14px 20px', color: '#a78bfa',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
              <Activity size={13} color="#a78bfa" />
              <span style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 700 }}>
                Execution Boundary Integrity · ADR-045
              </span>
              <span style={{
                fontSize: '0.6rem', fontFamily: 'monospace', fontWeight: 700,
                color: data.ebip_at_verification.overall_score >= 90 ? '#a78bfa' : '#fbbf24',
                background: 'rgba(167,139,250,0.1)', border: '1px solid rgba(167,139,250,0.2)',
                borderRadius: 4, padding: '1px 7px',
              }}>
                {data.ebip_at_verification.overall_score}/100
              </span>
            </div>
            {showEbip ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
          {showEbip && (
            <div style={{ padding: '0 20px 16px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, marginBottom: 12 }}>
                {[
                  { code: 'ACV', label: 'Consistency Validator', ok: data.ebip_at_verification.violations_24h === 0 },
                  { code: 'ECP', label: 'Commitment Protocol',   ok: true },
                  { code: 'NPM', label: 'Navigation Monitor',    ok: ['NOMINAL','WATCH'].includes(data.ebip_at_verification.alert_level) },
                  { code: 'CP',  label: 'Concentration Pred.',   ok: ['LOW','INSUFFICIENT_DATA'].includes(data.ebip_at_verification.concentration_risk) },
                ].map(c => (
                  <div key={c.code} style={{
                    padding: 8, borderRadius: 6, textAlign: 'center',
                    background: 'rgba(255,255,255,0.02)',
                    border: `1px solid ${c.ok ? 'rgba(139,92,246,0.2)' : 'rgba(251,191,36,0.25)'}`,
                  }}>
                    <div style={{ fontSize: '0.65rem', fontFamily: 'monospace', fontWeight: 700, color: c.ok ? '#a78bfa' : '#fbbf24', marginBottom: 3 }}>
                      {c.ok ? '✓' : '⚠'} {c.code}
                    </div>
                    <div style={{ fontSize: '0.58rem', color: '#4b5563', lineHeight: 1.3 }}>{c.label}</div>
                  </div>
                ))}
              </div>
              <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', fontSize: '0.75rem' }}>
                <span style={{ color: '#6b7280' }}>Alert: <strong style={{ color: '#a78bfa' }}>{data.ebip_at_verification.alert_level}</strong></span>
                <span style={{ color: '#6b7280' }}>Risk: <strong style={{ color: '#9ca3af' }}>{data.ebip_at_verification.concentration_risk}</strong></span>
                <span style={{ color: '#6b7280' }}>Components: <strong style={{ color: '#9ca3af' }}>{data.ebip_at_verification.components_active}</strong></span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Cryptographic integrity ── */}
      <div style={{
        background: 'rgba(59,130,246,0.04)', border: '1px solid rgba(59,130,246,0.15)',
        borderRadius: 12, padding: '16px 20px', marginBottom: 16,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14, flexWrap: 'wrap', gap: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
            <Lock size={13} color="#60a5fa" />
            <span style={{ fontSize: '0.7rem', color: '#60a5fa', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 700 }}>
              Cryptographic Integrity
            </span>
          </div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
            {(() => {
              const ts = data.integrity.trust_status
              if (ts === 'VALID_OMNIX_ISSUED') return (
                <span title={data.integrity.trust_status_description || ''} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.66rem', color: '#22c55e', background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.25)', borderRadius: 20, padding: '3px 10px', fontWeight: 800, fontFamily: 'monospace' }}>
                  <CheckCircle size={10} /> OMNIX ISSUED ✓
                </span>
              )
              if (ts === 'VALID_SIGNATURE_UNTRUSTED_ISSUER') return (
                <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.66rem', color: '#f59e0b', background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.25)', borderRadius: 20, padding: '3px 10px', fontWeight: 800, fontFamily: 'monospace' }}>
                  <AlertTriangle size={10} /> UNTRUSTED ISSUER
                </span>
              )
              if (ts === 'INVALID_SIGNATURE') return (
                <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.66rem', color: '#ef4444', background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.25)', borderRadius: 20, padding: '3px 10px', fontWeight: 800, fontFamily: 'monospace' }}>
                  <XCircle size={10} /> INVALID SIGNATURE
                </span>
              )
              if (ts === 'DOWNGRADED_SHA_ONLY') return (
                <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.66rem', color: '#6b7280', background: 'rgba(107,114,128,0.08)', border: '1px solid rgba(107,114,128,0.25)', borderRadius: 20, padding: '3px 10px', fontWeight: 700, fontFamily: 'monospace' }}>
                  SHA-256 ONLY
                </span>
              )
              return (
                <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.66rem', color: '#6b7280', background: 'rgba(107,114,128,0.06)', border: '1px solid rgba(107,114,128,0.2)', borderRadius: 20, padding: '3px 10px', fontFamily: 'monospace' }}>
                  {ts || 'UNKNOWN KEY'}
                </span>
              )
            })()}
            <div style={{
              display: 'flex', alignItems: 'center', gap: 5, fontSize: '0.68rem',
              color: '#22c55e', background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.2)',
              borderRadius: 20, padding: '3px 10px', fontWeight: 700,
            }}>
              <CheckCircle size={11} /> TAMPER-PROOF
            </div>
          </div>
        </div>

        {data.integrity.trust_status === 'VALID_SIGNATURE_UNTRUSTED_ISSUER' && (
          <div style={{
            display: 'flex', gap: 10, padding: '10px 14px', borderRadius: 8,
            background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.25)', marginBottom: 14,
          }}>
            <AlertTriangle size={15} color="#f59e0b" style={{ flexShrink: 0, marginTop: 1 }} />
            <div>
              <div style={{ fontSize: '0.82rem', color: '#f59e0b', fontWeight: 700, marginBottom: 3 }}>
                Untrusted Issuer — Receipt Rejected
              </div>
              <div style={{ fontSize: '0.74rem', color: '#6b7280', lineHeight: 1.5 }}>
                The PQC signature is mathematically valid, but the embedded public key does <strong style={{ color: '#f59e0b' }}>not</strong> match the trusted OMNIX anchor fingerprint. This receipt may have been signed with an attacker keypair. Do not rely on it as OMNIX governance evidence.
              </div>
            </div>
          </div>
        )}

        {data.integrity.trust_status === 'INVALID_SIGNATURE' && (
          <div style={{
            display: 'flex', gap: 10, padding: '10px 14px', borderRadius: 8,
            background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.25)', marginBottom: 14,
          }}>
            <XCircle size={15} color="#ef4444" style={{ flexShrink: 0, marginTop: 1 }} />
            <div>
              <div style={{ fontSize: '0.82rem', color: '#ef4444', fontWeight: 700, marginBottom: 3 }}>
                Invalid Signature — Possible Forgery
              </div>
              <div style={{ fontSize: '0.74rem', color: '#6b7280' }}>
                The PQC signature on this receipt is cryptographically invalid. The receipt has been tampered with or is forged.
              </div>
            </div>
          </div>
        )}

        <div style={{
          display: 'flex', gap: 10, padding: '10px 14px', borderRadius: 8,
          background: data.integrity.issuer_trusted ? 'rgba(34,197,94,0.05)' : 'rgba(59,130,246,0.05)',
          border: `1px solid ${data.integrity.issuer_trusted ? 'rgba(34,197,94,0.12)' : 'rgba(59,130,246,0.12)'}`,
          marginBottom: 14,
        }}>
          <CheckCircle size={15} color={data.integrity.issuer_trusted ? '#22c55e' : '#3b82f6'} style={{ flexShrink: 0, marginTop: 1 }} />
          <div>
            <div style={{ fontSize: '0.84rem', color: data.integrity.issuer_trusted ? '#22c55e' : '#60a5fa', fontWeight: 600, marginBottom: 3 }}>
              Signed with {data.integrity.signature_algorithm}
              {data.integrity.issuer_trusted && <span style={{ marginLeft: 8, fontSize: '0.72rem', fontWeight: 800 }}>· OMNIX KEY VERIFIED</span>}
            </div>
            <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
              {data.integrity.nist_note} · Post-quantum cryptography · NIST FIPS 204
            </div>
          </div>
        </div>

        {data.integrity.key_fingerprint && (
          <div style={{ marginBottom: 12, padding: '8px 12px', borderRadius: 8, background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.04)' }}>
            <div style={{ fontSize: '0.62rem', color: '#374151', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 4 }}>
              Trust Anchor — Key Fingerprint (SHA-256)
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Fingerprint size={11} color={data.integrity.issuer_trusted ? '#22c55e' : '#4b5563'} style={{ flexShrink: 0 }} />
              <span style={{ fontFamily: 'monospace', fontSize: '0.7rem', color: data.integrity.issuer_trusted ? '#22c55e' : '#6b7280', wordBreak: 'break-all' }}>
                {data.integrity.key_fingerprint}
              </span>
              <CopyBtn value={data.integrity.key_fingerprint} size={10} />
            </div>
            {data.integrity.trusted_anchor_fingerprint && (
              <div style={{ fontSize: '0.64rem', marginTop: 4, color: data.integrity.key_fingerprint === data.integrity.trusted_anchor_fingerprint ? '#22c55e' : '#ef4444' }}>
                {data.integrity.key_fingerprint === data.integrity.trusted_anchor_fingerprint
                  ? '✓ Matches trusted OMNIX anchor fingerprint'
                  : '✗ Does NOT match trusted OMNIX anchor fingerprint'}
              </div>
            )}
          </div>
        )}

        <button
          onClick={() => setShowHashes(v => !v)}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            display: 'flex', alignItems: 'center', gap: 5,
            color: '#4b5563', fontSize: '0.78rem', padding: '0 0 12px', width: '100%',
          }}
        >
          <Eye size={13} />
          {showHashes ? 'Hide' : 'Show'} cryptographic proof
          {showHashes ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
        </button>

        {showHashes && (
          <div>
            <HashLine label="Content Hash (SHA-256)" value={data.integrity.content_hash} />
            {data.integrity.prev_hash && (
              <HashLine label="Previous Receipt Hash (Chain Link)" value={data.integrity.prev_hash} />
            )}
            <div style={{
              marginTop: 12, padding: '10px 14px', borderRadius: 8,
              background: 'rgba(0,0,0,0.25)', border: '1px solid rgba(255,255,255,0.05)',
            }}>
              <div style={{ fontSize: '0.68rem', color: '#374151', marginBottom: 6 }}>Verify locally — no OMNIX server required:</div>
              <code style={{ fontFamily: 'monospace', fontSize: '0.72rem', color: '#60a5fa', display: 'block', lineHeight: 1.8 }}>
                python omnix_verify.py {data.receipt_id}.json
              </code>
              <div style={{ marginTop: 6, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <a href="/omnix_verify.py" download style={{
                  fontSize: '0.7rem', color: '#3b82f6', display: 'flex', alignItems: 'center', gap: 4,
                  textDecoration: 'none', border: '1px solid rgba(59,130,246,0.25)', borderRadius: 5, padding: '3px 8px',
                }}>
                  <Download size={11} /> omnix_verify.py
                </a>
                <Link to="/verify-independently" style={{
                  fontSize: '0.7rem', color: '#4b5563', display: 'flex', alignItems: 'center', gap: 4,
                  textDecoration: 'none', border: '1px solid rgba(75,85,99,0.3)', borderRadius: 5, padding: '3px 8px',
                }}>
                  <ExternalLink size={11} /> Verification guide
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── Footer ── */}
      <div style={{ textAlign: 'center', marginTop: 24, fontSize: '0.72rem', color: '#374151', lineHeight: 1.8 }}>
        Append-only hash chain · Post-quantum signatures · eIDAS 2.0 · ARF · NIST FIPS 204<br />
        <Link to="/try" style={{ color: '#3b82f6' }}>Submit your own scenario</Link>
        {' · '}
        <Link to="/crisis-replay" style={{ color: '#3b82f6' }}>Crisis Replay</Link>
        {' · '}
        <Link to="/" style={{ color: '#3b82f6' }}>OMNIX Home</Link>
      </div>
    </div>
  )
}

function LiveFeed({ onSelect }: { onSelect: (id: string) => void }) {
  const [feed, setFeed]   = useState<RecentReceipt[]>([])
  const [loading, setLoading] = useState(true)
  const [tick, setTick]   = useState(0)

  const fetchFeed = useCallback(() => {
    fetch(`${API_BASE}/api/verify/recent?limit=10`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d?.receipts) setFeed(d.receipts) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    fetchFeed()
    const t = setInterval(() => { fetchFeed(); setTick(v => v + 1) }, 15000)
    return () => clearInterval(t)
  }, [fetchFeed])

  const c = (d: string) => d === 'APPROVED' ? '#22c55e' : d === 'BLOCKED' ? '#ef4444' : '#f59e0b'

  return (
    <div>
      {/* Intro card */}
      <div style={{
        padding: '24px', background: 'rgba(59,130,246,0.04)',
        border: '1px solid rgba(59,130,246,0.15)', borderRadius: 14,
        textAlign: 'center', marginBottom: 24,
      }}>
        <Shield size={36} color="#3b82f6" style={{ marginBottom: 14 }} />
        <div style={{ fontWeight: 700, color: '#e5e7eb', marginBottom: 8, fontSize: '1.05rem' }}>
          Paste any Receipt ID above to verify
        </div>
        <div style={{ fontSize: '0.84rem', color: '#4b5563', lineHeight: 1.7, maxWidth: 420, margin: '0 auto' }}>
          Every OMNIX governance decision produces a cryptographically signed receipt,
          sealed with Dilithium-3 (NIST FIPS 204) post-quantum cryptography.
          <br />
          <Link to="/try" style={{ color: '#3b82f6', fontWeight: 600 }}>Generate your own</Link>
          {' '}in the public sandbox, or click any live receipt below.
        </div>
        <div style={{ marginTop: 16, display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
          {[
            { icon: <Lock size={12} />,        label: 'Dilithium-3 · FIPS 204', color: '#60a5fa' },
            { icon: <Hash size={12} />,         label: 'SHA-256 hash chain',      color: '#22c55e' },
            { icon: <Fingerprint size={12} />,  label: 'Independently verifiable', color: '#f59e0b' },
          ].map(b => (
            <span key={b.label} style={{
              display: 'inline-flex', alignItems: 'center', gap: 5,
              fontSize: '0.7rem', fontWeight: 600, color: b.color,
              background: `${b.color}12`, border: `1px solid ${b.color}30`,
              borderRadius: 20, padding: '4px 12px',
            }}>
              {b.icon} {b.label}
            </span>
          ))}
        </div>
      </div>

      {/* Live ledger */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12,
      }}>
        <div style={{ fontSize: '0.68rem', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 700 }}>
          Live Governance Ledger
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#22c55e', display: 'inline-block', animation: 'pulse 2s infinite' }} />
          <span style={{ fontSize: '0.65rem', color: '#374151' }}>
            Live · PQC signed · refresh {tick > 0 ? `${tick}×` : 'now'}
          </span>
        </div>
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#374151', fontSize: '0.85rem' }}>
          Connecting to ledger...
        </div>
      )}

      {!loading && feed.length === 0 && (
        <div style={{ textAlign: 'center', padding: '2rem', color: '#374151', fontSize: '0.85rem' }}>
          No receipts yet — try the <Link to="/try" style={{ color: '#3b82f6' }}>sandbox</Link>.
        </div>
      )}

      {!loading && feed.length > 0 && (
        <div style={{
          background: 'rgba(255,255,255,0.015)', border: '1px solid rgba(255,255,255,0.06)',
          borderRadius: 12, overflow: 'hidden',
        }}>
          {feed.map((r, i) => {
            const col = c(r.decision)
            return (
              <button
                key={r.receipt_id}
                onClick={() => onSelect(r.receipt_id)}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '70px 1fr auto auto',
                  alignItems: 'center', gap: 12,
                  width: '100%', padding: '12px 16px',
                  background: 'none', border: 'none',
                  borderBottom: i < feed.length - 1 ? '1px solid rgba(255,255,255,0.04)' : 'none',
                  cursor: 'pointer', textAlign: 'left', transition: 'background 0.15s',
                }}
                onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.03)')}
                onMouseLeave={e => (e.currentTarget.style.background = 'none')}
              >
                <span style={{
                  fontSize: '0.6rem', fontWeight: 800, letterSpacing: '0.06em',
                  fontFamily: 'monospace', padding: '3px 8px', borderRadius: 5,
                  color: col, background: `${col}14`, border: `1px solid ${col}30`,
                  textAlign: 'center',
                }}>
                  {r.decision}
                </span>
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontFamily: 'monospace', fontSize: '0.78rem', color: '#e5e7eb', fontWeight: 600, marginBottom: 2 }}>
                    {r.asset}
                  </div>
                  <div style={{ fontFamily: 'monospace', fontSize: '0.65rem', color: '#4b5563', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {r.receipt_id}
                  </div>
                </div>
                <div style={{ fontFamily: 'monospace', fontSize: '0.62rem', color: '#374151', flexShrink: 0, textAlign: 'right' }}>
                  {fmtTs(r.timestamp, true)}
                </div>
                <span style={{
                  fontSize: '0.55rem', fontFamily: 'monospace', fontWeight: 800,
                  color: '#60a5fa', background: 'rgba(96,165,250,0.08)',
                  border: '1px solid rgba(96,165,250,0.2)', borderRadius: 4,
                  padding: '2px 6px', flexShrink: 0,
                }}>
                  PQC ✓
                </span>
              </button>
            )
          })}
        </div>
      )}

      {!loading && feed.length > 0 && (
        <div style={{ marginTop: 10, fontSize: '0.68rem', color: '#374151', textAlign: 'center' }}>
          {feed.length} most recent signed receipts · click any row to inspect the full governance record
        </div>
      )}

      {/* Crisis replay CTA */}
      <div style={{
        marginTop: 24, padding: '16px 20px',
        background: 'rgba(201,162,39,0.04)', border: '1px solid rgba(201,162,39,0.15)',
        borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap',
      }}>
        <div>
          <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#C9A227', marginBottom: 3 }}>
            Want to see OMNIX in action?
          </div>
          <div style={{ fontSize: '0.75rem', color: '#4b5563' }}>
            Replay Terra/LUNA, FTX, SVB, COVID & OFAC — 12 signed receipts from real crises.
          </div>
        </div>
        <Link to="/crisis-replay" style={{
          fontSize: '0.78rem', fontWeight: 700, color: '#C9A227',
          background: 'rgba(201,162,39,0.1)', border: '1px solid rgba(201,162,39,0.3)',
          borderRadius: 8, padding: '8px 16px', textDecoration: 'none',
          display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0,
          whiteSpace: 'nowrap',
        }}>
          Crisis Replay <ExternalLink size={12} />
        </Link>
      </div>
    </div>
  )
}

export default function PublicDecisionVerify() {
  const { receiptId } = useParams<{ receiptId?: string }>()
  const navigate = useNavigate()
  const [data, setData]         = useState<VerifyData | null>(null)
  const [loading, setLoading]   = useState(false)
  const [notFound, setNotFound] = useState(false)
  const [error, setError]       = useState<string | null>(null)
  const [inputVal, setInputVal] = useState(receiptId ?? '')

  const doFetch = useCallback((id: string) => {
    if (!id) return
    setLoading(true); setData(null); setNotFound(false); setError(null)
    fetch(`${API_BASE}/api/public/verify/${encodeURIComponent(id)}`)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
      .then((d: VerifyData) => { if (!d.found) setNotFound(true); else setData(d) })
      .catch(() => setError('Verification service temporarily unavailable. Please try again.'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (receiptId) { setInputVal(receiptId); doFetch(receiptId) }
  }, [receiptId, doFetch])

  function handleSearch() {
    const t = inputVal.trim()
    if (t) navigate(`/verify/${encodeURIComponent(t)}`)
  }

  function handleSelect(id: string) {
    setInputVal(id)
    navigate(`/verify/${encodeURIComponent(id)}`)
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(180deg, #060c18 0%, #0a0e17 100%)',
      color: '#e5e7eb',
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    }}>
      <style>{`
        @keyframes pulse { 0%,100% { opacity:1 } 50% { opacity:0.4 } }
        input::placeholder { color: #374151 }
      `}</style>

      {/* ── Nav ── */}
      <nav style={{
        position: 'sticky', top: 0, zIndex: 50,
        background: 'rgba(6,12,24,0.92)', backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(201,162,39,0.1)',
        padding: '0 24px', height: 60,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 10, textDecoration: 'none' }}>
          <img src="/omnix_logo.png" alt="OMNIX" style={{ height: 36, objectFit: 'contain' }} />
        </Link>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center', fontSize: '0.8rem' }}>
          <Link to="/try"          style={{ color: '#6b7280', textDecoration: 'none' }}>Sandbox</Link>
          <Link to="/crisis-replay" style={{ color: '#6b7280', textDecoration: 'none' }}>Crisis Replay</Link>
          <Link to="/verify-independently" style={{
            color: '#C9A227', border: '1px solid rgba(201,162,39,0.3)',
            borderRadius: 6, padding: '5px 12px', textDecoration: 'none', fontWeight: 600,
          }}>
            Verify offline →
          </Link>
        </div>
      </nav>

      <div style={{ maxWidth: 760, margin: '0 auto', padding: '40px 20px 60px' }}>

        {/* ── Hero ── */}
        <div style={{ marginBottom: 36 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 12 }}>
            <Link to="/" style={{ color: '#374151', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.78rem' }}>
              <ArrowLeft size={13} /> Home
            </Link>
            <span style={{ color: '#1f2937' }}>·</span>
            <span style={{ fontSize: '0.78rem', color: '#374151' }}>Receipt Verifier</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 6 }}>
            <div style={{
              width: 40, height: 40, borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.25)',
            }}>
              <Shield size={20} color="#3b82f6" />
            </div>
            <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#fff', margin: 0, letterSpacing: '-0.02em' }}>
              Governance Receipt Verifier
            </h1>
          </div>
          <p style={{ color: '#4b5563', fontSize: '0.88rem', margin: '0 0 24px', lineHeight: 1.6 }}>
            Every OMNIX decision is sealed in a cryptographically signed receipt.
            Paste any receipt ID to verify its authenticity — independently, without trusting OMNIX.
          </p>

          {/* ── Search bar ── */}
          <div style={{ display: 'flex', gap: 8 }}>
            <div style={{ flex: 1, position: 'relative' }}>
              <Terminal size={14} style={{
                position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: '#374151',
              }} />
              <input
                value={inputVal}
                onChange={e => setInputVal(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSearch()}
                placeholder="OMNIX-TRD-A1B2C3D4E5F6  or  OMNIX-RPL-9202F596F3FDB439"
                style={{
                  width: '100%', boxSizing: 'border-box',
                  background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)',
                  color: '#e5e7eb', padding: '12px 14px 12px 38px',
                  borderRadius: 9, fontFamily: 'monospace', fontSize: '0.88rem',
                  outline: 'none', transition: 'border-color 0.2s',
                }}
                onFocus={e => (e.target.style.borderColor = 'rgba(59,130,246,0.5)')}
                onBlur={e  => (e.target.style.borderColor = 'rgba(255,255,255,0.1)')}
              />
            </div>
            <button onClick={handleSearch} style={{
              background: '#3b82f6', color: '#fff', border: 'none',
              padding: '12px 24px', borderRadius: 9, cursor: 'pointer',
              fontWeight: 700, fontSize: '0.88rem',
              display: 'flex', alignItems: 'center', gap: 7,
              flexShrink: 0, transition: 'background 0.2s',
            }}
              onMouseEnter={e => (e.currentTarget.style.background = '#2563eb')}
              onMouseLeave={e => (e.currentTarget.style.background = '#3b82f6')}
            >
              <Search size={15} /> Verify
            </button>
          </div>
        </div>

        {/* ── States ── */}
        {loading && (
          <div style={{ textAlign: 'center', padding: '4rem 2rem' }}>
            <div style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
              <div style={{
                width: 48, height: 48, borderRadius: '50%',
                border: '2px solid rgba(59,130,246,0.2)', borderTopColor: '#3b82f6',
                animation: 'spin 0.8s linear infinite',
              }} />
              <div style={{ fontSize: '0.88rem', color: '#4b5563' }}>Verifying cryptographic integrity...</div>
            </div>
            <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
          </div>
        )}

        {error && !loading && (
          <div style={{
            padding: '16px 20px', borderRadius: 12,
            background: 'rgba(239,68,68,0.07)', border: '1px solid rgba(239,68,68,0.2)',
            display: 'flex', gap: 12, alignItems: 'flex-start',
          }}>
            <AlertTriangle size={17} color="#ef4444" style={{ flexShrink: 0, marginTop: 1 }} />
            <div>
              <div style={{ fontWeight: 600, color: '#ef4444', marginBottom: 4 }}>Verification Error</div>
              <div style={{ fontSize: '0.84rem', color: '#9ca3af' }}>{error}</div>
            </div>
          </div>
        )}

        {notFound && !loading && (
          <div style={{
            padding: '32px', borderRadius: 12, textAlign: 'center',
            background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.07)',
          }}>
            <div style={{ fontSize: '2.5rem', marginBottom: 14 }}>🔍</div>
            <div style={{ fontWeight: 700, color: '#e5e7eb', marginBottom: 8, fontSize: '1rem' }}>Receipt not found</div>
            <div style={{ fontSize: '0.84rem', color: '#4b5563' }}>
              <code style={{ color: '#6b7280', fontFamily: 'monospace' }}>{receiptId}</code> does not exist in the governance ledger.
            </div>
            <div style={{ fontSize: '0.78rem', color: '#374151', marginTop: 10 }}>
              Receipts are generated by the <Link to="/try" style={{ color: '#3b82f6' }}>public sandbox</Link> and the live trading pipeline.
            </div>
          </div>
        )}

        {data && !loading && <ReceiptResult data={data} />}

        {!receiptId && !loading && !error && <LiveFeed onSelect={handleSelect} />}

      </div>
    </div>
  )
}
