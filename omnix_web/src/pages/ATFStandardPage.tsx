import { useState } from 'react'

const GOLD = '#C9A227'
const NAVY = '#060F1E'
const NAVY2 = '#0A1628'
const BORDER = 'rgba(201,162,39,0.18)'
const BORDER2 = 'rgba(255,255,255,0.06)'

const premiumPhrase = {
  main: "OMNIX no solo gobierna decisiones de IA.",
  sub:  "OMNIX prueba criptográficamente quién autorizó a cada agente, qué autoridad tenía, cuándo era válida y si podía ejecutar en ese momento exacto."
}

type TabKey = 'dr' | 'tar' | 'dtr' | 'receipt'

const JSON_EXAMPLES: Record<TabKey, { label: string; lang: string; code: string }> = {
  dr: {
    label: 'Delegation Receipt',
    lang:  'ATFDR-...',
    code: `{
  "delegation_id":              "ATFDR-8B2C4D6E1F3A5B7C",
  "delegator_id":               "HUMAN-TIER1-HN-001",
  "delegate_id":                "AID-FINANCE-3A7F9B2C1D4E5F6A",
  "task_scope": {
    "action":      "compute_portfolio_risk",
    "domain":      "FINANCE",
    "constraints": ["read_only", "no_trading"]
  },
  "authority_budget_delegator": 100.0,
  "authority_budget_granted":   60.0,
  "chain_root_id":              "ATFDR-8B2C4D6E1F3A5B7C",
  "delegation_depth":           1,
  "delegator_public_key":       "<base64-dilithium3-pubkey>",
  "content_hash":               "a3f9b2c1d4e5f6a7b8c9...",
  "pqc_signature":              "<base64-dilithium3-sig>",
  "pqc_algorithm":              "dilithium3",
  "status":                     "ACTIVE",
  "created_at":                 "2026-05-12T14:00:00.000000+00:00"
}`,
  },
  tar: {
    label: 'Temporal Admissibility Record',
    lang: 'ATFTAR-...',
    code: `{
  "tar_id":                  "ATFTAR-C4D8E2F1A3B5C7D9",
  "delegation_id":           "ATFDR-8B2C4D6E1F3A5B7C",
  "agent_id":                "AID-FINANCE-3A7F9B2C1D4E5F6A",
  "execution_ref":           "OMNIX-FIN-20260512-A3F7B2",
  "execution_ns":            1747058400000000000,
  "execution_ts":            "2026-05-12T14:00:00.000000+00:00",
  "dr_status_at_admission":  "ACTIVE",
  "dr_expires_at":           "2026-05-13T14:00:00.000000+00:00",
  "authority_budget":        60.0,
  "domain":                  "FINANCE",
  "task_action":             "governance_evaluation:FINANCE:AAPL",
  "admission_status":        "ADMITTED",
  "rejection_reason":        null,
  "content_hash":            "b7f4c3d2e1a0b9c8...",
  "pqc_signature":           "<base64-dilithium3-sig>",
  "pqc_algorithm":           "dilithium3",
  "chain_root_id":           "ATFDR-8B2C4D6E1F3A5B7C",
  "issued_at":               "2026-05-12T14:00:00.000000+00:00"
}`,
  },
  dtr: {
    label: 'Domain Translation Receipt',
    lang: 'ATFDTR-...',
    code: `{
  "dtr_id":                   "ATFDTR-A1B2C3D4E5F6A7B8",
  "source_delegation_id":     "ATFDR-8B2C4D6E1F3A5B7C",
  "source_domain":            "FINANCE",
  "target_domain":            "HEALTHCARE",
  "source_agent_id":          "AID-FINANCE-3A7F9B2C1D4E5F6A",
  "target_agent_id":          "AID-HEALTHCARE-9B3C5D7E1F2A4B6C",
  "source_authority_budget":  60.0,
  "translated_budget":        42.0,
  "translation_discount":     0.30,
  "translation_policy":       "CDTP-FINA-HEAL-POLICY",
  "task_scope": {
    "action": "access_patient_financial_data",
    "domain": "HEALTHCARE",
    "constraints": ["anonymized", "read_only", "audit_log"]
  },
  "chain_root_id":            "ATFDR-8B2C4D6E1F3A5B7C",
  "content_hash":             "d9e8f7a6b5c4d3e2...",
  "pqc_signature":            "<base64-dilithium3-sig>",
  "pqc_algorithm":            "dilithium3",
  "status":                   "ACTIVE",
  "issued_at":                "2026-05-12T14:05:00.000000+00:00"
}`,
  },
  receipt: {
    label: 'Governance Receipt + ATF',
    lang: 'OMNIX-FIN-...',
    code: `{
  "receipt_id":     "OMNIX-FIN-20260512-A3F7B2",
  "timestamp_utc":  "2026-05-12T14:00:00.000000+00:00",
  "asset":          "AAPL",
  "decision":       "APPROVED",
  "content_hash":   "a9b8c7d6e5f4...",
  "pqc_signature":  "<base64-dilithium3-sig>",
  "pqc_algorithm":  "dilithium3",

  "atf_context": {
    "delegation_id":    "ATFDR-8B2C4D6E1F3A5B7C",
    "tar_id":           "ATFTAR-C4D8E2F1A3B5C7D9",
    "agent_id":         "AID-FINANCE-3A7F9B2C1D4E5F6A",
    "delegator_id":     "HUMAN-TIER1-HN-001",
    "admission_status": "ADMITTED",
    "execution_ns":     1747058400000000000,
    "authority_budget": 60.0,
    "chain_root_id":    "ATFDR-8B2C4D6E1F3A5B7C",
    "pqc_signed":       true
  }
}`,
  },
}

function ProofCard({ icon, title, claim, desc }: { icon: string; title: string; claim: string; desc: string }) {
  return (
    <div style={{
      padding: '24px', borderRadius: 14,
      background: 'rgba(255,255,255,0.02)',
      border: `1px solid ${BORDER}`,
    }}>
      <div style={{ fontSize: 28, marginBottom: 12 }}>{icon}</div>
      <div style={{ fontSize: 12, fontWeight: 700, color: GOLD, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>{title}</div>
      <div style={{ fontSize: 16, fontWeight: 700, color: '#f1f5f9', marginBottom: 8, lineHeight: 1.4 }}>{claim}</div>
      <div style={{ fontSize: 13, color: '#64748b', lineHeight: 1.6 }}>{desc}</div>
    </div>
  )
}

function ChainBox({ id, label, sub, color }: { id: string; label: string; sub: string; color: string }) {
  return (
    <div style={{
      padding: '16px 18px', borderRadius: 12,
      background: `rgba(${color},0.06)`,
      border: `1.5px solid rgba(${color},0.30)`,
      minWidth: 180, flex: 1,
    }}>
      <div style={{ fontSize: 11, fontWeight: 700, color: `rgb(${color})`, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>{label}</div>
      <div style={{
        fontSize: 11, fontFamily: '"JetBrains Mono", monospace',
        color: '#94a3b8', wordBreak: 'break-all',
      }}>{id}</div>
      <div style={{ fontSize: 12, color: '#475569', marginTop: 6 }}>{sub}</div>
    </div>
  )
}

function Arrow() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', color: '#334155', fontSize: 18, flexShrink: 0, padding: '0 8px' }}>→</div>
  )
}

function StandardBadge({ label, detail }: { label: string; detail: string }) {
  return (
    <div style={{
      padding: '16px 20px', borderRadius: 12,
      background: 'rgba(255,255,255,0.02)',
      border: `1px solid ${BORDER}`,
      display: 'flex', gap: 14, alignItems: 'flex-start',
    }}>
      <div style={{ width: 8, height: 8, borderRadius: '50%', background: GOLD, flexShrink: 0, marginTop: 5 }} />
      <div>
        <div style={{ fontSize: 13, fontWeight: 700, color: '#f1f5f9', marginBottom: 3 }}>{label}</div>
        <div style={{ fontSize: 12, color: '#64748b', lineHeight: 1.5 }}>{detail}</div>
      </div>
    </div>
  )
}

export default function ATFStandardPage() {
  const [activeTab, setActiveTab] = useState<TabKey>('receipt')
  const [verifyInput, setVerifyInput] = useState('')
  const [verifyLoading, setVerifyLoading] = useState(false)
  const [verifyResult, setVerifyResult] = useState<null | { ok: boolean; label: string }>(null)

  const handleQuickVerify = async () => {
    const id = verifyInput.trim()
    if (!id) return
    setVerifyLoading(true)
    setVerifyResult(null)
    try {
      const res = await fetch('/api/atf/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ delegation_id: id }),
      })
      const data = await res.json()
      if (data.error) {
        setVerifyResult({ ok: false, label: data.error })
      } else {
        setVerifyResult({ ok: data.status === 'verified', label: data.status === 'verified' ? 'VERIFIED ✓' : 'INVALID ✗' })
      }
    } catch {
      setVerifyResult({ ok: false, label: 'Network error' })
    } finally {
      setVerifyLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: NAVY, color: '#e2e8f0', fontFamily: '"Inter", -apple-system, sans-serif' }}>

      {/* Hero */}
      <div style={{
        borderBottom: `1px solid ${BORDER}`,
        background: NAVY2,
        padding: '72px 24px 64px',
        textAlign: 'center',
      }}>
        <div style={{ maxWidth: 780, margin: '0 auto' }}>
          <div style={{
            display: 'inline-block',
            padding: '6px 16px', borderRadius: 20,
            background: 'rgba(201,162,39,0.10)',
            border: `1px solid rgba(201,162,39,0.25)`,
            fontSize: 12, fontWeight: 700, color: GOLD,
            textTransform: 'uppercase', letterSpacing: '0.1em',
            marginBottom: 28,
          }}>
            RFC-ATF-1 · OMNIX QUANTUM Open Standard · May 2026
          </div>
          <div style={{ fontSize: 42, fontWeight: 800, color: '#f8fafc', lineHeight: 1.15, marginBottom: 20 }}>
            OMNIX ATF Standard
          </div>
          <div style={{ fontSize: 20, fontWeight: 700, color: '#f1f5f9', marginBottom: 16, lineHeight: 1.5 }}>
            {premiumPhrase.main}
          </div>
          <div style={{ fontSize: 17, color: '#94a3b8', lineHeight: 1.7, maxWidth: 640, margin: '0 auto 36px' }}>
            {premiumPhrase.sub}
          </div>
          <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
            <a href="/atf-verify" style={{
              padding: '13px 28px', borderRadius: 10, border: 'none',
              background: GOLD, color: NAVY, fontSize: 14, fontWeight: 700,
              textDecoration: 'none', display: 'inline-block',
            }}>🔐 Public Verifier</a>
            <a href="/agent-trust-fabric" style={{
              padding: '13px 28px', borderRadius: 10,
              border: `1.5px solid rgba(201,162,39,0.35)`,
              color: GOLD, fontSize: 14, fontWeight: 700,
              textDecoration: 'none', display: 'inline-block',
              background: 'rgba(201,162,39,0.06)',
            }}>📊 ATF Dashboard</a>
            <a href="/protocol" style={{
              padding: '13px 28px', borderRadius: 10,
              border: `1.5px solid rgba(0,229,255,0.30)`,
              color: '#00E5FF', fontSize: 14, fontWeight: 600,
              textDecoration: 'none', display: 'inline-block',
              background: 'rgba(0,229,255,0.04)',
            }}>Protocol Architecture →</a>
            <a href="https://github.com/omnixquantum" target="_blank" rel="noopener noreferrer" style={{
              padding: '13px 28px', borderRadius: 10,
              border: `1.5px solid ${BORDER2}`,
              color: '#94a3b8', fontSize: 14, fontWeight: 600,
              textDecoration: 'none', display: 'inline-block',
            }}>GitHub Release →</a>
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 1000, margin: '0 auto', padding: '64px 24px' }}>

        {/* 4 Proof Claims */}
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: GOLD, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 12 }}>
            What ATF Proves — Cryptographically
          </div>
          <div style={{ fontSize: 24, fontWeight: 700, color: '#f1f5f9' }}>
            Four questions, four cryptographic proofs
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16, marginBottom: 72 }}>
          <ProofCard
            icon="👤"
            title="Who authorized"
            claim="Quién autorizó al agente"
            desc="DelegationReceipt PQC-signed por el principal humano Tier-1. Cadena trazable al origen."
          />
          <ProofCard
            icon="⚖️"
            title="What authority"
            claim="Qué autoridad tenía"
            desc="Authority budget explícito (0–100). Invariante MAR: la autoridad solo decrece en cada delegación."
          />
          <ProofCard
            icon="⏱️"
            title="When valid"
            claim="Cuándo era válida"
            desc="TemporalAdmissibilityRecord con timestamp nanosegundo (TAR-INV-002). Inmutable post-emisión."
          />
          <ProofCard
            icon="✅"
            title="Was it admitted"
            claim="Si podía ejecutar en ese momento"
            desc="TAR.admission_status = ADMITTED | REJECTED. Prueba nanosegundo-precisa. Independientemente verificable."
          />
        </div>

        {/* Trust Chain Visualization */}
        <div style={{
          marginBottom: 72, padding: '32px', borderRadius: 16,
          background: NAVY2, border: `1px solid ${BORDER}`,
        }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: GOLD, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>
            Complete Trust Chain
          </div>
          <div style={{ fontSize: 18, fontWeight: 700, color: '#f1f5f9', marginBottom: 20 }}>
            Human → Agent → Decision — Every step cryptographically linked
          </div>

          {/* Chain diagram */}
          <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 8, marginBottom: 20 }}>
            <ChainBox
              id="HUMAN-TIER1-HN-001"
              label="Human Origin"
              sub="Full authority (100.0)"
              color="201,162,39"
            />
            <Arrow />
            <ChainBox
              id="ATFDR-8B2C4D6E1F3A5B7C"
              label="Delegation Receipt"
              sub="budget=60.0 · PQC signed"
              color="34,197,94"
            />
            <Arrow />
            <ChainBox
              id="ATFTAR-C4D8E2F1A3B5C7D9"
              label="Temporal Admissibility"
              sub="ns=1747058400000000000 · ADMITTED"
              color="59,130,246"
            />
            <Arrow />
            <ChainBox
              id="OMNIX-FIN-20260512-A3F7B2"
              label="Governance Receipt"
              sub="APPROVED · Dilithium-3"
              color="168,85,247"
            />
          </div>

          <div style={{
            padding: '14px 18px', borderRadius: 10,
            background: 'rgba(201,162,39,0.05)',
            border: `1px solid rgba(201,162,39,0.15)`,
            fontSize: 13, color: '#94a3b8', lineHeight: 1.6,
          }}>
            <strong style={{ color: GOLD }}>ATF-INV-006 — Independent Verifiability:</strong>{' '}
            Any regulator, auditor, or counterparty can verify this entire chain using only the receipt artifacts
            and the root public key. No platform access required. Receipts carry embedded
            <code style={{ color: '#e2e8f0', background: 'rgba(255,255,255,0.06)', padding: '1px 5px', borderRadius: 3, marginLeft: 4 }}>delegator_public_key</code>.
          </div>
        </div>

        {/* Quick Verifier */}
        <div style={{
          marginBottom: 72, padding: '32px', borderRadius: 16,
          background: NAVY2, border: `1px solid ${BORDER}`,
        }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: GOLD, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>
            Quick Verification
          </div>
          <div style={{ fontSize: 18, fontWeight: 700, color: '#f1f5f9', marginBottom: 20 }}>
            Verify any Delegation Receipt instantly
          </div>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 12 }}>
            <input
              type="text"
              value={verifyInput}
              onChange={e => setVerifyInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleQuickVerify()}
              placeholder="ATFDR-8B2C4D6E1F3A5B7C"
              style={{
                flex: 1, minWidth: 240,
                padding: '12px 16px', borderRadius: 10,
                background: NAVY, border: `1.5px solid ${BORDER}`,
                color: '#f1f5f9', fontSize: 14, fontFamily: 'inherit',
                outline: 'none',
              }}
            />
            <button
              onClick={handleQuickVerify}
              disabled={verifyLoading}
              style={{
                padding: '12px 24px', borderRadius: 10, border: 'none',
                background: GOLD, color: NAVY, fontSize: 14, fontWeight: 700,
                cursor: verifyLoading ? 'not-allowed' : 'pointer',
                opacity: verifyLoading ? 0.7 : 1,
              }}
            >{verifyLoading ? '⟳' : '🔐 Verify'}</button>
          </div>
          {verifyResult && (
            <div style={{
              padding: '12px 16px', borderRadius: 10,
              background: verifyResult.ok ? 'rgba(34,197,94,0.08)' : 'rgba(239,68,68,0.08)',
              border: `1px solid ${verifyResult.ok ? 'rgba(34,197,94,0.25)' : 'rgba(239,68,68,0.25)'}`,
              color: verifyResult.ok ? '#22c55e' : '#fca5a5',
              fontSize: 14, fontWeight: 600,
            }}>
              {verifyResult.label}
            </div>
          )}
          <div style={{ marginTop: 16 }}>
            <a href="/atf-verify" style={{ color: GOLD, fontSize: 13, textDecoration: 'none', fontWeight: 500 }}>
              Full verifier with chain, agent, and JSON paste mode →
            </a>
          </div>
        </div>

        {/* JSON Examples */}
        <div style={{ marginBottom: 72 }}>
          <div style={{ textAlign: 'center', marginBottom: 32 }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: GOLD, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>
              Wire Format — RFC-ATF-1 §9
            </div>
            <div style={{ fontSize: 24, fontWeight: 700, color: '#f1f5f9' }}>
              JSON Examples
            </div>
          </div>

          <div style={{
            display: 'flex', gap: 4, background: 'rgba(255,255,255,0.03)',
            borderRadius: 12, padding: 4, marginBottom: 16,
            border: `1px solid ${BORDER}`,
          }}>
            {(Object.keys(JSON_EXAMPLES) as TabKey[]).map(k => (
              <button
                key={k}
                onClick={() => setActiveTab(k)}
                style={{
                  flex: 1, padding: '10px 6px', borderRadius: 8, border: 'none',
                  cursor: 'pointer', fontSize: 12, fontWeight: 600,
                  background: activeTab === k ? 'rgba(201,162,39,0.18)' : 'transparent',
                  color: activeTab === k ? GOLD : '#64748b',
                  transition: 'all 0.2s',
                }}
              >
                {JSON_EXAMPLES[k].label}
              </button>
            ))}
          </div>

          <div style={{
            borderRadius: 12, overflow: 'hidden',
            border: `1px solid ${BORDER}`,
          }}>
            <div style={{
              padding: '10px 16px',
              background: 'rgba(255,255,255,0.03)',
              borderBottom: `1px solid ${BORDER}`,
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}>
              <span style={{ fontSize: 12, color: '#64748b', fontFamily: 'monospace' }}>
                {JSON_EXAMPLES[activeTab].lang}
              </span>
              <span style={{
                fontSize: 11, color: '#22c55e', fontWeight: 600,
                background: 'rgba(34,197,94,0.08)',
                border: '1px solid rgba(34,197,94,0.20)',
                padding: '2px 8px', borderRadius: 4,
              }}>RFC-ATF-1</span>
            </div>
            <pre style={{
              margin: 0, padding: '20px', overflowX: 'auto',
              background: NAVY, color: '#94a3b8',
              fontSize: 12, lineHeight: 1.7,
              fontFamily: '"JetBrains Mono", "Fira Code", monospace',
            }}>
              {JSON_EXAMPLES[activeTab].code
                .split('\n')
                .map((line, i) => {
                  const keyMatch = line.match(/^(\s*)"([^"]+)":/)
                  if (keyMatch) {
                    const indent = keyMatch[1]
                    const key = keyMatch[2]
                    const rest = line.slice(keyMatch[0].length)
                    return (
                      <span key={i}>
                        {indent}<span style={{ color: '#60a5fa' }}>"{key}"</span>:{rest}{'\n'}
                      </span>
                    )
                  }
                  return <span key={i}>{line}{'\n'}</span>
                })}
            </pre>
          </div>
        </div>

        {/* Standards Track */}
        <div style={{ marginBottom: 72 }}>
          <div style={{ textAlign: 'center', marginBottom: 32 }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: GOLD, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>
              Standards Track
            </div>
            <div style={{ fontSize: 24, fontWeight: 700, color: '#f1f5f9' }}>
              The ATF Formal Standard Ecosystem
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
            <StandardBadge
              label="RFC-ATF-1 — Agent Trust Fabric Protocol"
              detail="IETF-style specification. 16 sections, ABNF grammar, 6 invariants, 3 compliance levels, ML-DSA-65 (FIPS 204)."
            />
            <StandardBadge
              label="ADR-157 — Temporal Authority Admissibility"
              detail="Nanosecond-precise proof that a DR was ACTIVE at the exact moment of execution. 5 temporal invariants."
            />
            <StandardBadge
              label="ADR-158 — Cross-Domain Trust Portability"
              detail="Authority translation across governance domains with domain-pair discount policies. CDTP-INV-001/006."
            />
            <StandardBadge
              label="ATF-FV-1.0 — TLA+ Formal Verification"
              detail="Machine-checkable proofs of MAR, acyclicity, chain consistency, immutability. Same methods as AWS DynamoDB."
            />
          </div>
        </div>

        {/* CLI Download */}
        <div style={{
          marginBottom: 72, padding: '32px', borderRadius: 16,
          background: NAVY2, border: `1px solid ${BORDER}`,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 20 }}>
            <div style={{ flex: 1, minWidth: 280 }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: GOLD, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>
                CLI Verifier — ATF-INV-006
              </div>
              <div style={{ fontSize: 18, fontWeight: 700, color: '#f1f5f9', marginBottom: 12 }}>
                Standalone offline verification tool
              </div>
              <div style={{ fontSize: 13, color: '#64748b', lineHeight: 1.6, marginBottom: 20 }}>
                100% offline. No network, no account, no API key. Verify delegation receipts
                and full trust chains using only the receipt JSON and embedded public keys.
              </div>
              <div style={{
                background: NAVY, borderRadius: 10, padding: '14px 18px',
                fontFamily: '"JetBrains Mono", monospace', fontSize: 13,
                color: '#94a3b8', lineHeight: 1.8,
                border: `1px solid ${BORDER2}`,
              }}>
                <div><span style={{ color: '#22c55e' }}>$</span> python omnix_atf_verify.py receipt.json</div>
                <div><span style={{ color: '#22c55e' }}>$</span> python omnix_atf_verify.py <span style={{ color: '#64748b' }}>--mode chain</span> chain.json</div>
                <div><span style={{ color: '#22c55e' }}>$</span> python omnix_atf_verify.py receipt.json <span style={{ color: '#64748b' }}>--json</span></div>
              </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <a href="/atf-verify" style={{
                padding: '14px 24px', borderRadius: 10, border: 'none',
                background: GOLD, color: NAVY, fontSize: 14, fontWeight: 700,
                textDecoration: 'none', textAlign: 'center', display: 'block',
              }}>Open Web Verifier →</a>
              <a href="https://omnixquantum.com/atf" target="_blank" rel="noopener noreferrer" style={{
                padding: '14px 24px', borderRadius: 10,
                border: `1.5px solid ${BORDER}`,
                color: '#94a3b8', fontSize: 14, fontWeight: 600,
                textDecoration: 'none', textAlign: 'center', display: 'block',
              }}>Documentation</a>
            </div>
          </div>
        </div>

        {/* Compliance Map */}
        <div style={{ marginBottom: 48 }}>
          <div style={{ textAlign: 'center', marginBottom: 28 }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: '#f1f5f9', marginBottom: 8 }}>
              Regulatory Alignment
            </div>
            <div style={{ fontSize: 13, color: '#64748b' }}>
              ATF directly addresses accountability requirements in major AI regulations
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
            {[
              { reg: 'EU AI Act', art: 'Art. 13', req: 'Authorized scope at decision time' },
              { reg: 'DORA', art: 'Art. 9', req: 'ICT operational control evidence' },
              { reg: 'MiCA', art: 'Rec. 65', req: 'Algorithmic trading controls' },
              { reg: 'SOC 2', art: 'CC6', req: 'Logical access with human traceability' },
              { reg: 'ISO 27001', art: 'A.9.4', req: 'Information system access control' },
              { reg: 'NIST AI RMF', art: 'GOVERN', req: 'Accountable AI decision audit' },
            ].map(item => (
              <div key={item.reg} style={{
                padding: '16px', borderRadius: 10,
                background: 'rgba(255,255,255,0.02)',
                border: `1px solid ${BORDER}`,
              }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: GOLD }}>{item.reg}</div>
                <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>{item.art}</div>
                <div style={{ fontSize: 12, color: '#64748b', marginTop: 6, lineHeight: 1.5 }}>{item.req}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Priority Record Banner */}
        <div style={{
          padding: '24px 28px', borderRadius: 14,
          background: 'rgba(201,162,39,0.04)',
          border: `1px solid rgba(201,162,39,0.20)`,
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          flexWrap: 'wrap', gap: 20,
        }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: GOLD, marginBottom: 6 }}>
              OMNIX ATF — Priority Record
            </div>
            <div style={{ fontSize: 13, color: '#64748b', lineHeight: 1.7 }}>
              Published May 2026 · OMNIX QUANTUM LTD · Harold Nunes<br />
              RFC-ATF-1: Zenodo 10.5281/zenodo.20155016 · Figshare 10.6084/m9.figshare.32308077 · SSRN 6757339<br />
              RFC-ATF-2: Zenodo 10.5281/zenodo.20241344 · Figshare 10.6084/m9.figshare.32308095 · SSRN 6763978<br />
              RFC-ATF-3: Zenodo 10.5281/zenodo.20247342 · Figshare 10.6084/m9.figshare.32308119 · 47 formal invariants<br />
              RFC-ATF-4: Zenodo 10.5281/zenodo.20368895 · Figshare 10.6084/m9.figshare.32394192 · 19 Z3 proofs · dual Z3+TLA+
            </div>
          </div>
          <div style={{ fontSize: 12, color: '#475569', fontFamily: 'monospace' }}>
            RFC-ATF-1 · RFC-ATF-2 · RFC-ATF-3 · RFC-ATF-4 · ADR-156/157/158/159/161/170/174/181/182/183/184 · ATF-FV-1.0
          </div>
        </div>

      </div>
    </div>
  )
}
