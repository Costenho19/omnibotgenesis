import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

// ── Design System ──────────────────────────────────────────────────────────────
const GOLD        = '#C9A227'
const GOLD_DIM    = 'rgba(201,162,39,0.10)'
const GOLD_BORDER = 'rgba(201,162,39,0.22)'
const NAVY        = '#060F1E'
const NAVY2       = '#0A1628'
const NAVY3       = '#0D1E38'
const GREEN       = '#22c55e'
const GREEN_DIM   = 'rgba(34,197,94,0.09)'
const GREEN_BORDER= 'rgba(34,197,94,0.25)'
const RED         = '#ef4444'
const RED_DIM     = 'rgba(239,68,68,0.08)'
const RED_BORDER  = 'rgba(239,68,68,0.25)'
const AMBER       = '#f59e0b'
const AMBER_DIM   = 'rgba(245,158,11,0.10)'
const BLUE        = '#3b82f6'
const BLUE_DIM    = 'rgba(59,130,246,0.09)'
const SLATE       = '#64748b'
const TEXT        = '#e2e8f0'
const MUTED       = '#94a3b8'

// ── Types ──────────────────────────────────────────────────────────────────────
interface PlatformKeyInfo {
  status: string
  fingerprint: string | null
  fingerprint_short: string | null
  algorithm: string
  key_size_bytes: number
  configured: boolean
  published_at: string | null
  canonical_verification_url: string
  dns_txt_record?: { record_name: string; record_format: string; purpose: string }
  zenodo_reference?: { doi: string; note: string }
}

// ── Invariant data ─────────────────────────────────────────────────────────────
const INVARIANTS = [
  // ATF
  { id: 'ATF-INV-001', category: 'ATF', adr: 'ADR-156 / RFC-ATF-1', title: 'Monotonic Authority Reduction', desc: 'authority_budget_granted ≤ authority_budget_delegator along any chain', status: 'ACTIVE' },
  { id: 'ATF-INV-002', category: 'ATF', adr: 'ADR-156 / RFC-ATF-1', title: 'Receipt Signing', desc: 'Every Delegation Receipt must carry a PQC signature over its content hash', status: 'ACTIVE' },
  { id: 'ATF-INV-003', category: 'ATF', adr: 'ADR-156 / RFC-ATF-1', title: 'Chain Root Traceability', desc: 'Every DR must carry a chain_root_id linking back to the human origin', status: 'ACTIVE' },
  { id: 'ATF-INV-004', category: 'ATF', adr: 'ADR-156 / RFC-ATF-1', title: 'Budget Ceiling', desc: 'A principal cannot grant more authority than it currently holds', status: 'ACTIVE' },
  { id: 'ATF-INV-005', category: 'ATF', adr: 'ADR-156 / RFC-ATF-1', title: 'Receipt Immutability', desc: 'Once issued, Delegation Receipt content fields cannot be modified', status: 'ACTIVE' },
  { id: 'ATF-INV-006', category: 'ATF', adr: 'ADR-156 / RFC-ATF-1', title: 'Independent Verifiability', desc: 'Verification possible using only receipts and root public key — no OMNIX runtime needed', status: 'ACTIVE' },
  // RGC
  { id: 'RGC-INV-001', category: 'RGC', adr: 'ADR-159 / RFC-ATF-2', title: 'TAR Anchoring', desc: 'Every RCR must reference a valid Temporal Admissibility Record', status: 'ACTIVE' },
  { id: 'RGC-INV-002', category: 'RGC', adr: 'ADR-159 / RFC-ATF-2', title: 'Real-Time CES Computation', desc: 'CES computed from current values at the nanosecond of the sample', status: 'ACTIVE' },
  { id: 'RGC-INV-003', category: 'RGC', adr: 'ADR-159 / RFC-ATF-2', title: 'HALT Propagation', desc: 'When a session halts, all sibling sessions on the same chain root are revoked', status: 'ACTIVE' },
  { id: 'RGC-INV-004', category: 'RGC', adr: 'ADR-159 / RFC-ATF-2', title: 'Authority Fragmentation Guard', desc: 'Aggregate budget across active sessions must not exceed chain_root_budget × 0.90', status: 'ACTIVE' },
  { id: 'RGC-INV-005', category: 'RGC', adr: 'ADR-159 / RFC-ATF-2', title: 'RCR Immutability', desc: 'Runtime Continuity Records are write-once — no updates permitted', status: 'ACTIVE' },
  { id: 'RGC-INV-006', category: 'RGC', adr: 'ADR-159 / RFC-ATF-2', title: 'Chain Acyclicity', desc: 'RCR timestamps must be strictly increasing', status: 'ACTIVE' },
  { id: 'RGC-INV-007', category: 'RGC', adr: 'ADR-159 / RFC-ATF-2', title: 'CES Input Freshness', desc: 'CES inputs must not be older than 5s (Critical) or 30s (Nominal)', status: 'ACTIVE' },
  { id: 'RGC-INV-008', category: 'RGC', adr: 'ADR-159 / RFC-ATF-2', title: 'RC TTL Enforcement', desc: 'Reauthorization Challenges halt execution if not resolved within TTL', status: 'ACTIVE' },
  // EAP
  { id: 'EAP-INV-001', category: 'EAP', adr: 'ADR-163', title: 'Verification Preservation', desc: 'WARM/COLD artifacts must have original content_hash recomputable from original fields', status: 'ACTIVE' },
  { id: 'EAP-INV-002', category: 'EAP', adr: 'ADR-163', title: 'PQC Signature Preservation', desc: 'ML-DSA-65 signatures preserved in COLD storage in original form — no compression', status: 'ACTIVE' },
  { id: 'EAP-INV-003', category: 'EAP', adr: 'ADR-163', title: 'Block Chain Integrity', desc: 'predecessor_block_hash chain across COLD blocks must be unbroken', status: 'ACTIVE' },
  { id: 'EAP-INV-004', category: 'EAP', adr: 'ADR-163', title: 'Immutable Class Permanence', desc: 'LEGAL, PQC, CONTRACT, EXCEPTION classes stored in complete canonical form', status: 'ACTIVE' },
  { id: 'EAP-INV-005', category: 'EAP', adr: 'ADR-163', title: 'Offline Reconstructability', desc: 'Verification possible with only the COLD block, public key, and CLI verifier', status: 'ACTIVE' },
  { id: 'EAP-INV-006', category: 'EAP', adr: 'ADR-163', title: 'Manifest Completeness', desc: 'Every HOT→WARM and WARM→COLD transition creates a manifest entry or rolls back', status: 'ACTIVE' },
  { id: 'EAP-INV-007', category: 'EAP', adr: 'ADR-163/167', title: 'Global Block Uniqueness', desc: 'Block IDs globally unique via Redis INCR in production — no collision across dynos', status: 'ACTIVE' },
  // FVP
  { id: 'FVP-INV-007', category: 'FVP', adr: 'ADR-164/167', title: 'Key Identity Disclosure', desc: 'Every /verify response includes key_identity with platform_fingerprint when configured', status: 'ACTIVE' },
  // OEP
  { id: 'OEP-INV-001', category: 'OEP', adr: 'ADR-165', title: 'Offline Self-Containment', desc: 'OEPs verifiable with only the package and standard Python/pypqc — no network required', status: 'ACTIVE' },
  { id: 'OEP-INV-002', category: 'OEP', adr: 'ADR-165', title: 'File Integrity Lattice', desc: 'Every file in OEP listed in manifest.json with correct SHA-256', status: 'ACTIVE' },
  { id: 'OEP-INV-003', category: 'OEP', adr: 'ADR-165', title: 'Mandatory Package Signature', desc: 'SIGNATURE/package_signature.json must contain a valid ML-DSA-65 signature', status: 'ACTIVE' },
  { id: 'OEP-INV-004', category: 'OEP', adr: 'ADR-165', title: 'Chain Completeness', desc: 'All non-GENESIS predecessor blocks referenced in package must be in BLOCKS/', status: 'ACTIVE' },
  { id: 'OEP-INV-005', category: 'OEP', adr: 'ADR-165', title: 'Embedded Public Key', desc: 'KEYS/public_key.b64 contains the verification key — URL references prohibited', status: 'ACTIVE' },
  { id: 'OEP-INV-006', category: 'OEP', adr: 'ADR-165', title: 'Schema Version Lock', desc: 'manifest_version must be "oep-1.0"; parsers reject unknown versions', status: 'ACTIVE' },
  // FEA
  { id: 'FEA-INV-001', category: 'FEA', adr: 'ADR-166', title: 'Key Isolation', desc: 'Platform private keys never transmitted in HTTP request bodies in production', status: 'ACTIVE' },
  { id: 'FEA-INV-002', category: 'FEA', adr: 'ADR-166', title: 'Audit Logging', desc: 'Every OEP export logged with client_id, ip, key_source, package_id', status: 'ACTIVE' },
  { id: 'FEA-INV-003', category: 'FEA', adr: 'ADR-166', title: 'Auth Enforcement', desc: '/export returns 401 for missing, invalid, or expired API keys', status: 'ACTIVE' },
  { id: 'FEA-INV-004', category: 'FEA', adr: 'ADR-166', title: 'Fail-Closed Signing', desc: '/export returns 503 if no signing key is available', status: 'ACTIVE' },
  { id: 'FEA-INV-005', category: 'FEA', adr: 'ADR-166', title: 'Production Safety', desc: 'FORENSIC_EXPORT_ALLOW_CALLER_KEYS=true is forbidden in production', status: 'ACTIVE' },
  // TAR
  { id: 'TAR-INV-006', category: 'TAR', adr: 'ADR-157 rev.2', title: 'Compiled Staleness Bound', desc: 'RCR_CES_STALENESS_BOUND_SECONDS=300 compiled constant — CES inputs older than 5 min structurally rejected', status: 'ACTIVE' },
  // GPIL
  { id: 'GPIL-INV-001', category: 'GPIL', adr: 'ADR-161', title: 'Bilateral CRGC Signing', desc: 'Cross-runtime governance contracts require ML-DSA-65 signatures from both runtimes before admission', status: 'ACTIVE' },
  { id: 'GPIL-INV-002', category: 'GPIL', adr: 'ADR-161', title: 'ATF-GPI-Aligned Status', desc: 'Cross-runtime agent operations require ATF-GPI-Aligned status before first cross-runtime admission', status: 'ACTIVE' },
  { id: 'GPIL-INV-003', category: 'GPIL', adr: 'ADR-161', title: 'Restrictive Parameter Default', desc: 'Undeclared CRGC parameters default to the more restrictive runtime value — no silent permissiveness', status: 'ACTIVE' },
  // ELR
  { id: 'ELR-INV-001', category: 'ELR', adr: 'ADR-163', title: 'Evidence Class Immutability', desc: 'Evidence class is immutable protocol state — reclassification after write produces cryptographic hash mismatch', status: 'ACTIVE' },
  { id: 'ELR-INV-002', category: 'ELR', adr: 'ADR-163', title: 'Classification Hash Binding', desc: 'classification_hash binds evidence_class + payload + timestamp + evidentiary_meaning at write time', status: 'ACTIVE' },
  { id: 'ELR-INV-003', category: 'ELR', adr: 'ADR-163', title: 'Reclassification Detection', desc: 'POST /verify performs classification integrity verification and reclassification attack detection', status: 'ACTIVE' },
  { id: 'ELR-INV-004', category: 'ELR', adr: 'ADR-163', title: 'Legal Class Preservation', desc: 'LEGAL, PQC, CONTRACT, EXCEPTION class artifacts stored in complete canonical form — no field compression', status: 'ACTIVE' },
  // GECR
  { id: 'GECR-INV-001', category: 'GECR', adr: 'ADR-170', title: 'Control-Receipt Atomicity', desc: 'No controlled action proceeds without a receipt being issued first — the receipt IS the authorization, not a record of it', status: 'ACTIVE' },
  { id: 'GECR-INV-002', category: 'GECR', adr: 'ADR-170', title: 'Bounded Context Drift', desc: 'drift_delta < −0.05 → DRIFTED receipt; drift_delta < −0.15 → REVOKED, commit refused', status: 'ACTIVE' },
  { id: 'GECR-INV-003', category: 'GECR', adr: 'ADR-170', title: 'Authority Aggregate Ceiling', desc: 'Cross-agent authority at chain_root_id level never exceeds AFG limit (default 0.90, hard cap 0.95)', status: 'ACTIVE' },
  { id: 'GECR-INV-004', category: 'GECR', adr: 'ADR-170', title: 'Atomic HALT Propagation', desc: 'HALT propagates atomically to ALL sibling sessions on same chain_root_id — partial HALT is invalid state', status: 'ACTIVE' },
  { id: 'GECR-INV-005', category: 'GECR', adr: 'ADR-170', title: 'Cross-Runtime Pre-Authorization', desc: 'Cross-runtime operations require bilaterally signed CRGC before first admission', status: 'ACTIVE' },
  { id: 'GECR-INV-006', category: 'GECR', adr: 'ADR-170', title: 'RC TTL Non-Extensibility', desc: 'Reauthorization Challenge TTL is bounded and non-extensible — auto-HALT on expiry', status: 'ACTIVE' },
]

const CAT_COLOR: Record<string, string> = {
  ATF: '#a855f7', RGC: '#3b82f6', EAP: GOLD, FVP: GREEN, OEP: '#06b6d4', FEA: RED,
  TAR: '#8b5cf6', GPIL: '#0ea5e9', ELR: '#f97316', GECR: '#ec4899',
}

// ── Small components ───────────────────────────────────────────────────────────
function StatusBadge({ status, planned }: { status: string; planned?: boolean }) {
  const bg = planned ? AMBER_DIM : GREEN_DIM
  const border = planned ? 'rgba(245,158,11,0.3)' : GREEN_BORDER
  const color = planned ? AMBER : GREEN
  return (
    <span style={{
      fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 4,
      background: bg, border: `1px solid ${border}`, color,
      letterSpacing: '0.06em', whiteSpace: 'nowrap',
    }}>
      {planned ? 'PLANNED' : status}
    </span>
  )
}

function SectionHeader({ label, adr, id }: { label: string; adr?: string; id?: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'baseline', gap: 14, marginBottom: 24 }}>
      <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: TEXT, letterSpacing: '-0.01em' }}>{label}</h2>
      {adr && (
        <span style={{ fontSize: 11, color: SLATE, fontFamily: 'monospace' }}>{adr}</span>
      )}
      {id && (
        <span style={{ fontSize: 10, color: GOLD, fontFamily: 'monospace', letterSpacing: '0.04em' }}>{id}</span>
      )}
    </div>
  )
}

function CopyButton({ value, label }: { value: string; label?: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <button
      onClick={() => { navigator.clipboard.writeText(value); setCopied(true); setTimeout(() => setCopied(false), 2000) }}
      style={{
        background: copied ? GREEN_DIM : 'rgba(255,255,255,0.04)',
        border: `1px solid ${copied ? GREEN_BORDER : 'rgba(255,255,255,0.08)'}`,
        color: copied ? GREEN : MUTED, borderRadius: 5, padding: '3px 10px',
        fontSize: 11, cursor: 'pointer', transition: 'all 0.2s', fontWeight: 600,
        whiteSpace: 'nowrap',
      }}
    >{copied ? '✓ Copied' : (label || 'Copy')}</button>
  )
}

// ── Page ───────────────────────────────────────────────────────────────────────
export default function TrustInfrastructurePage() {
  const navigate = useNavigate()
  const [pkInfo, setPkInfo] = useState<PlatformKeyInfo | null>(null)
  const [pkLoading, setPkLoading] = useState(true)
  const [activeInvCat, setActiveInvCat] = useState<string>('ALL')
  const [expandedInv, setExpandedInv] = useState<string | null>(null)

  useEffect(() => {
    setPkLoading(true)
    fetch('/api/forensic/platform-key')
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setPkInfo(d) })
      .catch(() => {})
      .finally(() => setPkLoading(false))
  }, [])

  const filteredInvariants = activeInvCat === 'ALL'
    ? INVARIANTS
    : INVARIANTS.filter(i => i.category === activeInvCat)

  const fpConfigured = pkInfo?.configured && pkInfo?.fingerprint

  return (
    <div style={{ minHeight: '100vh', background: NAVY, color: TEXT, fontFamily: "'Inter', 'SF Pro Display', -apple-system, sans-serif" }}>

      {/* ── Header ── */}
      <div style={{ borderBottom: `1px solid rgba(201,162,39,0.15)`, background: NAVY2 }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '40px 32px' }}>
          <button
            onClick={() => navigate(-1)}
            style={{ background: 'none', border: 'none', color: SLATE, cursor: 'pointer', fontSize: 13, padding: 0, marginBottom: 24, display: 'flex', alignItems: 'center', gap: 6 }}
          >← Back</button>

          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 20 }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 10 }}>
                <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.14em', color: GOLD }}>OMNIX QUANTUM LTD</span>
                <span style={{ color: 'rgba(255,255,255,0.12)' }}>|</span>
                <span style={{ fontSize: 11, color: SLATE, letterSpacing: '0.06em' }}>TRUST INFRASTRUCTURE</span>
              </div>
              <h1 style={{ margin: '0 0 12px 0', fontSize: 36, fontWeight: 800, letterSpacing: '-0.02em', lineHeight: 1.1, color: TEXT }}>
                Platform Trust Registry
              </h1>
              <p style={{ margin: 0, fontSize: 15, color: MUTED, maxWidth: 600, lineHeight: 1.6 }}>
                Cryptographic evidence custody backed by ML-DSA-65 post-quantum signatures.
                47 enforced invariants across 9 families. Full offline verifiability. Independent of any OMNIX runtime.
              </p>
            </div>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              <button onClick={() => navigate('/archive-verify')}
                style={{ background: GOLD, color: NAVY, border: 'none', padding: '10px 20px', borderRadius: 8, fontWeight: 700, cursor: 'pointer', fontSize: 13 }}>
                Open Forensic Verifier
              </button>
              <button onClick={() => navigate('/protocol')}
                style={{ background: 'transparent', color: GOLD, border: `1px solid ${GOLD_BORDER}`, padding: '10px 20px', borderRadius: 8, fontWeight: 600, cursor: 'pointer', fontSize: 13 }}>
                Protocol Architecture
              </button>
            </div>
          </div>

          {/* Metric strip */}
          <div style={{ display: 'flex', gap: 40, marginTop: 32, paddingTop: 28, borderTop: `1px solid rgba(255,255,255,0.05)`, flexWrap: 'wrap' }}>
            {[
              { label: 'Invariants enforced', value: '67', sub: '9 families · 4 RFCs' },
              { label: 'PQC Algorithm', value: 'ML-DSA-65', sub: 'FIPS 204 · NIST Level 3' },
              { label: 'Verification planes', value: '3', sub: 'Browser · Server · Offline' },
              { label: 'Offline verifiable', value: 'Yes', sub: 'OEP + CLI verifier' },
              { label: 'Trust anchor', value: fpConfigured ? 'ACTIVE' : pkLoading ? 'Loading…' : 'NOT CONFIG', sub: 'ADR-167 · OMNIX-SEC-2026-001' },
            ].map(m => (
              <div key={m.label}>
                <div style={{ fontSize: 22, fontWeight: 800, color: GOLD, letterSpacing: '-0.01em' }}>{m.value}</div>
                <div style={{ fontSize: 12, color: TEXT, marginTop: 2 }}>{m.label}</div>
                <div style={{ fontSize: 11, color: SLATE, marginTop: 1 }}>{m.sub}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '48px 32px' }}>

        {/* ── Section 1: Platform Key Registry ── */}
        <div style={{ marginBottom: 56 }}>
          <SectionHeader label="Platform Key Registry" adr="ADR-167 · RFC-ATF-1" id="OMNIX-SEC-2026-001" />

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            {/* Left: Live fingerprint */}
            <div style={{ background: NAVY2, borderRadius: 14, border: `1px solid ${fpConfigured ? GOLD_BORDER : 'rgba(255,255,255,0.06)'}`, padding: 28 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
                <div style={{ width: 8, height: 8, borderRadius: '50%', background: fpConfigured ? GREEN : AMBER, boxShadow: fpConfigured ? '0 0 8px rgba(34,197,94,0.5)' : 'none' }} />
                <span style={{ fontSize: 12, fontWeight: 700, letterSpacing: '0.08em', color: MUTED }}>LIVE PLATFORM KEY</span>
                {fpConfigured && <StatusBadge status="ACTIVE" />}
              </div>

              {pkLoading ? (
                <div style={{ color: SLATE, fontSize: 13 }}>Fetching from registry…</div>
              ) : !pkInfo || !fpConfigured ? (
                <div>
                  <div style={{ color: AMBER, fontSize: 13, marginBottom: 12 }}>
                    Platform key not configured on this instance.
                  </div>
                  <div style={{ fontSize: 12, color: SLATE }}>
                    In Railway production, set <code style={{ color: GOLD }}>OMNIX_SIGNING_PUBLIC_KEY_B64</code> to activate the live fingerprint.
                  </div>
                </div>
              ) : (
                <>
                  <div style={{ marginBottom: 16 }}>
                    <div style={{ fontSize: 10, color: SLATE, letterSpacing: '0.08em', marginBottom: 8 }}>FINGERPRINT (SHA-256 of raw public key bytes)</div>
                    <div style={{ background: 'rgba(0,0,0,0.3)', borderRadius: 8, padding: '12px 14px', border: `1px solid ${GOLD_BORDER}` }}>
                      <code style={{ fontSize: 12, color: GOLD, wordBreak: 'break-all', fontFamily: 'monospace', lineHeight: 1.5 }}>
                        {pkInfo.fingerprint}
                      </code>
                    </div>
                    <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                      <CopyButton value={pkInfo.fingerprint!} label="Copy fingerprint" />
                      <CopyButton value={pkInfo.dns_txt_record?.record_format || ''} label="Copy DNS value" />
                    </div>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, fontSize: 12 }}>
                    <div>
                      <div style={{ color: SLATE, fontSize: 10, marginBottom: 3 }}>ALGORITHM</div>
                      <div style={{ color: TEXT }}>{pkInfo.algorithm}</div>
                    </div>
                    <div>
                      <div style={{ color: SLATE, fontSize: 10, marginBottom: 3 }}>KEY SIZE</div>
                      <div style={{ color: TEXT }}>{pkInfo.key_size_bytes?.toLocaleString()} bytes</div>
                    </div>
                    {pkInfo.published_at && (
                      <div>
                        <div style={{ color: SLATE, fontSize: 10, marginBottom: 3 }}>PUBLISHED AT</div>
                        <div style={{ color: TEXT }}>{new Date(pkInfo.published_at).toLocaleDateString()}</div>
                      </div>
                    )}
                    <div>
                      <div style={{ color: SLATE, fontSize: 10, marginBottom: 3 }}>STANDARD</div>
                      <div style={{ color: TEXT }}>FIPS 204</div>
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* Right: Verification channels */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {[
                {
                  icon: '⚡', label: 'HTTP API (Primary)', desc: 'Machine-readable, no auth required',
                  value: 'GET /api/forensic/platform-key', link: '/api/forensic/platform-key',
                  note: 'Canonical source · ADR-167', bg: GOLD_DIM, border: GOLD_BORDER, color: GOLD,
                },
                {
                  icon: '🌐', label: 'DNS TXT Record', desc: 'Independent of HTTP — survives platform outage',
                  value: '_omnix-key.omnixquantum.net',
                  note: 'dig TXT _omnix-key.omnixquantum.net +short', bg: BLUE_DIM, border: 'rgba(59,130,246,0.25)', color: BLUE,
                },
                {
                  icon: '📦', label: 'Zenodo Permanent Archive', desc: 'Immutable · time-stamped · citable DOI',
                  value: 'https://doi.org/10.5281/zenodo.20155016', link: 'https://doi.org/10.5281/zenodo.20155016',
                  note: 'OMNIX ATF Research Package · RFC-ATF-1', bg: 'rgba(168,85,247,0.08)', border: 'rgba(168,85,247,0.25)', color: '#a855f7',
                },
              ].map(ch => (
                <div key={ch.label} style={{ background: ch.bg, border: `1px solid ${ch.border}`, borderRadius: 12, padding: '16px 20px' }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                        <span>{ch.icon}</span>
                        <span style={{ fontSize: 13, fontWeight: 700, color: ch.color }}>{ch.label}</span>
                      </div>
                      <div style={{ fontSize: 12, color: MUTED }}>{ch.desc}</div>
                    </div>
                    {ch.link && (
                      <a href={ch.link} target="_blank" rel="noreferrer"
                        style={{ fontSize: 11, color: ch.color, textDecoration: 'none', flexShrink: 0 }}>↗ Open</a>
                    )}
                  </div>
                  <code style={{ display: 'block', fontSize: 11, color: TEXT, fontFamily: 'monospace', marginTop: 10, padding: '6px 10px', background: 'rgba(0,0,0,0.2)', borderRadius: 6, wordBreak: 'break-all' }}>
                    {ch.value}
                  </code>
                  <div style={{ fontSize: 11, color: SLATE, marginTop: 6 }}>{ch.note}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Section 2: Trust Level Distinction ── */}
        <div style={{ marginBottom: 56 }}>
          <SectionHeader label="Trust Level Classification" adr="ADR-167 · FVP-INV-007" />

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            {/* OMNIX_PLATFORM */}
            <div style={{ background: GREEN_DIM, border: `1px solid ${GREEN_BORDER}`, borderRadius: 14, padding: 28 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                <div style={{ width: 10, height: 10, borderRadius: '50%', background: GREEN }} />
                <span style={{ fontSize: 16, fontWeight: 800, color: GREEN, fontFamily: 'monospace' }}>OMNIX_PLATFORM</span>
              </div>
              <div style={{ fontSize: 13, color: TEXT, lineHeight: 1.7, marginBottom: 18 }}>
                The OEP or block was signed by the OMNIX QUANTUM LTD platform key. The fingerprint in <code style={{ color: GOLD }}>KEYS/public_key.b64</code> matches the live registry.
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {[
                  'Signed by OMNIX QUANTUM LTD',
                  'Verifiable against live registry + DNS TXT + Zenodo',
                  'Highest institutional trust level',
                  'Full chain endorsement from OMNIX',
                  'key_identity.matches_platform === true',
                ].map(item => (
                  <div key={item} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, fontSize: 12, color: TEXT }}>
                    <span style={{ color: GREEN, flexShrink: 0, marginTop: 1 }}>✓</span>
                    <span>{item}</span>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 18, padding: '10px 14px', background: 'rgba(0,0,0,0.2)', borderRadius: 8, fontSize: 11, color: MUTED, fontFamily: 'monospace' }}>
                Verify: curl /api/forensic/platform-key | jq .fingerprint
              </div>
            </div>

            {/* EXTERNAL */}
            <div style={{ background: AMBER_DIM, border: `1px solid rgba(245,158,11,0.3)`, borderRadius: 14, padding: 28 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                <div style={{ width: 10, height: 10, borderRadius: '50%', background: AMBER }} />
                <span style={{ fontSize: 16, fontWeight: 800, color: AMBER, fontFamily: 'monospace' }}>EXTERNAL</span>
              </div>
              <div style={{ fontSize: 13, color: TEXT, lineHeight: 1.7, marginBottom: 18 }}>
                Signed by a non-platform key. A PASS verdict is still cryptographically valid — the signature is mathematically sound for the provided key. But it is <em>not</em> an endorsement by OMNIX QUANTUM LTD.
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {[
                  'Signed by a caller-provided or test key',
                  'PASS verdict = cryptographic validity only',
                  'Expected for demo, test, and external OEPs',
                  'Cannot be attributed to OMNIX QUANTUM LTD',
                  'key_identity.matches_platform === false',
                ].map(item => (
                  <div key={item} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, fontSize: 12, color: TEXT }}>
                    <span style={{ color: AMBER, flexShrink: 0, marginTop: 1 }}>○</span>
                    <span>{item}</span>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 18, padding: '10px 14px', background: 'rgba(0,0,0,0.2)', borderRadius: 8, fontSize: 11, color: MUTED }}>
                FORENSIC_EXPORT_ALLOW_CALLER_KEYS is allowed only in dev/test environments (FEA-INV-005).
              </div>
            </div>
          </div>
        </div>

        {/* ── Section 3: Verification Architecture (3 planes) ── */}
        <div style={{ marginBottom: 56 }}>
          <SectionHeader label="Cryptographic Verification Architecture" adr="ADR-164 · ADR-165" />

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
            {[
              {
                plane: 'PLANE 1', label: 'Browser Verification', color: GOLD, bg: GOLD_DIM, border: GOLD_BORDER,
                subtitle: 'No server required · Instant · FVP-INV-001–005',
                checks: [
                  { name: 'Merkle root recomputation', inv: 'FVP-INV-002' },
                  { name: 'Canonical hash computation', inv: 'FVP-INV-001' },
                  { name: 'Predecessor chain validation', inv: 'FVP-INV-003' },
                  { name: 'BigInt-safe timestamp comparison', inv: 'FVP-INV-001' },
                  { name: 'ML-DSA-65 best-effort PQC', inv: 'FVP-INV-004' },
                ],
                note: 'Verdicts: PASS · INTEGRITY_VIOLATION · CHAIN_BREAK · ORPHANED · INCOMPLETE',
              },
              {
                plane: 'PLANE 2', label: 'Server Authoritative', color: BLUE, bg: BLUE_DIM, border: 'rgba(59,130,246,0.25)',
                subtitle: 'Definitive PQC · /api/forensic/verify · FVP-INV-004/006',
                checks: [
                  { name: 'ML-DSA-65 signature verification', inv: 'FVP-INV-004' },
                  { name: 'Platform key identity check', inv: 'FVP-INV-007' },
                  { name: 'Key fingerprint comparison', inv: 'ADR-167' },
                  { name: 'Trust conflict resolution', inv: 'FVP-INV-006' },
                  { name: 'Rate-limited: 60/min per client', inv: 'ADR-167' },
                ],
                note: 'Server verdict overrides browser for PQC. Hash violations are browser-final.',
              },
              {
                plane: 'PLANE 3', label: 'Offline OEP Verification', color: '#a855f7', bg: 'rgba(168,85,247,0.08)', border: 'rgba(168,85,247,0.25)',
                subtitle: 'Fully air-gapped · CLI verifier embedded · OEP-INV-001',
                checks: [
                  { name: 'Self-contained .oep bundle', inv: 'OEP-INV-001' },
                  { name: 'omnix_atf_verify.py embedded', inv: 'OEP-INV-001' },
                  { name: 'verify_all.sh bash script', inv: 'OEP-INV-001' },
                  { name: 'Package manifest signature', inv: 'OEP-INV-003' },
                  { name: 'SHA-256 file integrity lattice', inv: 'OEP-INV-002' },
                ],
                note: 'No OMNIX account, API key, or network access required for verification.',
              },
            ].map(plane => (
              <div key={plane.plane} style={{ background: plane.bg, border: `1px solid ${plane.border}`, borderRadius: 14, padding: 24 }}>
                <div style={{ fontSize: 10, fontWeight: 800, color: plane.color, letterSpacing: '0.12em', marginBottom: 6 }}>{plane.plane}</div>
                <div style={{ fontSize: 16, fontWeight: 700, color: TEXT, marginBottom: 6 }}>{plane.label}</div>
                <div style={{ fontSize: 11, color: MUTED, marginBottom: 18, lineHeight: 1.5 }}>{plane.subtitle}</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {plane.checks.map(ch => (
                    <div key={ch.name} style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                      <span style={{ color: plane.color, fontSize: 12, flexShrink: 0, marginTop: 1 }}>▸</span>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 12, color: TEXT }}>{ch.name}</div>
                        <div style={{ fontSize: 10, color: SLATE, fontFamily: 'monospace' }}>{ch.inv}</div>
                      </div>
                    </div>
                  ))}
                </div>
                <div style={{ marginTop: 16, padding: '8px 12px', background: 'rgba(0,0,0,0.2)', borderRadius: 7, fontSize: 11, color: MUTED, lineHeight: 1.5 }}>
                  {plane.note}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ── Section 4: Evidence Lifecycle HOT → WARM → COLD ── */}
        <div style={{ marginBottom: 56 }}>
          <SectionHeader label="Evidence Lifecycle" adr="ADR-163 · EAP-INV-001–007" />

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 4, marginBottom: 16 }}>
            {[
              {
                tier: 'HOT', color: '#ef4444', bg: RED_DIM, border: RED_BORDER, status: 'ACTIVE',
                desc: 'Decision receipts, WAL, live PostgreSQL. Sub-second access.',
                items: ['decision_receipts table', 'receipt_wal.py', 'Live API', 'SHA-256 chained'],
                inv: 'EAP-INV-001',
              },
              {
                tier: 'WARM', color: AMBER, bg: AMBER_DIM, border: 'rgba(245,158,11,0.3)', status: 'ACTIVE',
                desc: 'Archive transition manifests. HOT→WARM transition with integrity manifest.',
                items: ['Transition manifest', 'Content hash preservation', 'ELR lifecycle tracking', 'Rollback on failure'],
                inv: 'EAP-INV-006',
              },
              {
                tier: 'COLD', color: GOLD, bg: GOLD_DIM, border: GOLD_BORDER, status: 'ACTIVE',
                desc: 'Sealed immutable blocks. PQC-signed. Predecessor chain. Exportable.',
                items: ['cold_block_sealer.py', 'ML-DSA-65 signed', 'Predecessor chain', 'OEP exportable'],
                inv: 'EAP-INV-002–005',
              },
              {
                tier: 'OEP', color: '#06b6d4', bg: 'rgba(6,182,212,0.08)', border: 'rgba(6,182,212,0.25)', status: 'ACTIVE',
                desc: 'Self-contained forensic package. Offline verifiable. Legally defensible.',
                items: ['ZIP bundle', 'Embedded verifier', 'Package signature', 'HTML report'],
                inv: 'OEP-INV-001–006',
              },
            ].map((tier, i) => (
              <div key={tier.tier} style={{ position: 'relative' }}>
                {i > 0 && (
                  <div style={{ position: 'absolute', left: -4, top: '50%', transform: 'translateY(-50%)', fontSize: 18, color: SLATE, zIndex: 1 }}>→</div>
                )}
                <div style={{ background: tier.bg, border: `1px solid ${tier.border}`, borderRadius: 12, padding: '20px 18px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                    <span style={{ fontSize: 16, fontWeight: 800, color: tier.color, fontFamily: 'monospace' }}>{tier.tier}</span>
                    <StatusBadge status={tier.status} />
                  </div>
                  <div style={{ fontSize: 12, color: MUTED, marginBottom: 14, lineHeight: 1.5 }}>{tier.desc}</div>
                  {tier.items.map(item => (
                    <div key={item} style={{ fontSize: 11, color: TEXT, marginBottom: 4, display: 'flex', gap: 6 }}>
                      <span style={{ color: tier.color }}>·</span>{item}
                    </div>
                  ))}
                  <div style={{ marginTop: 12, fontSize: 10, color: SLATE, fontFamily: 'monospace' }}>{tier.inv}</div>
                </div>
              </div>
            ))}
          </div>
          <div style={{ padding: '12px 16px', borderRadius: 8, background: NAVY2, border: '1px solid rgba(255,255,255,0.05)', fontSize: 12, color: MUTED }}>
            Parquet archive segments for COLD blocks at scale are planned per ADR-163 §7 — <StatusBadge status="PLANNED" planned /> · Current production uses PostgreSQL for COLD block storage.
          </div>
        </div>

        {/* ── Section 5: Key Rotation Lifecycle ── */}
        <div style={{ marginBottom: 56 }}>
          <SectionHeader label="Key Rotation Lifecycle" adr="OMNIX-SEC-2026-001-B · ADR-167" />

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 4, marginBottom: 16 }}>
            {[
              { state: 'ACTIVE', color: GREEN, bg: GREEN_DIM, border: GREEN_BORDER, desc: 'Platform key in use. All new blocks signed with current key.' },
              { state: 'ROTATION SCHEDULED', color: GOLD, bg: GOLD_DIM, border: GOLD_BORDER, desc: '30-day notice sent. New key generated offline on isolated machine.' },
              { state: 'DUAL ACTIVE', color: BLUE, bg: BLUE_DIM, border: 'rgba(59,130,246,0.25)', desc: 'New key deployed. Old key still valid for historical verification (EAP-INV-001).' },
              { state: 'RETIRED', color: SLATE, bg: 'rgba(100,116,139,0.08)', border: 'rgba(100,116,139,0.2)', desc: 'Old key archived in registry. Historical blocks remain verifiable. DNS updated.' },
              { state: 'REVOKED', color: RED, bg: RED_DIM, border: RED_BORDER, desc: 'Emergency compromise response. All channels updated within 1h. Clients notified within 24h.' },
            ].map(s => (
              <div key={s.state} style={{ background: s.bg, border: `1px solid ${s.border}`, borderRadius: 10, padding: '16px 14px' }}>
                <div style={{ fontSize: 10, fontWeight: 800, color: s.color, letterSpacing: '0.08em', marginBottom: 8 }}>{s.state}</div>
                <div style={{ fontSize: 11, color: TEXT, lineHeight: 1.5 }}>{s.desc}</div>
              </div>
            ))}
          </div>
          <div style={{ fontSize: 12, color: MUTED, padding: '10px 0' }}>
            Emergency path: ACTIVE → REVOKED triggers Phase 1 (containment &lt;1h) · Phase 2 (new key deployed &lt;4h) · Phase 3 (all channels updated &lt;24h).
            See <code style={{ color: GOLD }}>docs/security/KEY_ROTATION_RUNBOOK.md §4</code>.
          </div>
        </div>

        {/* ── Section 6: Invariant Reference ── */}
        <div style={{ marginBottom: 56 }}>
          <SectionHeader label="Invariant Reference" adr="67 invariants · 9 families · RFC-ATF-1/2/3/4" />

          {/* Category filter */}
          <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
            {['ALL', 'ATF', 'RGC', 'EAP', 'FVP', 'OEP', 'FEA', 'TAR', 'GPIL', 'ELR', 'GECR'].map(cat => (
              <button key={cat} onClick={() => setActiveInvCat(cat)}
                style={{
                  padding: '5px 14px', borderRadius: 6, border: `1px solid ${activeInvCat === cat ? (CAT_COLOR[cat] || GOLD) : 'rgba(255,255,255,0.08)'}`,
                  background: activeInvCat === cat ? `${CAT_COLOR[cat] || GOLD}18` : 'transparent',
                  color: activeInvCat === cat ? (CAT_COLOR[cat] || GOLD) : MUTED,
                  cursor: 'pointer', fontSize: 12, fontWeight: 700, transition: 'all 0.15s',
                }}>
                {cat}
                {cat !== 'ALL' && (
                  <span style={{ marginLeft: 6, fontSize: 10, opacity: 0.7 }}>
                    {INVARIANTS.filter(i => i.category === cat).length}
                  </span>
                )}
              </button>
            ))}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {filteredInvariants.map(inv => (
              <div key={inv.id}
                onClick={() => setExpandedInv(expandedInv === inv.id ? null : inv.id)}
                style={{
                  background: expandedInv === inv.id ? NAVY3 : NAVY2,
                  border: `1px solid ${expandedInv === inv.id ? `${CAT_COLOR[inv.category]}40` : 'rgba(255,255,255,0.04)'}`,
                  borderRadius: 8, padding: '12px 16px', cursor: 'pointer', transition: 'all 0.15s',
                }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                  <span style={{ fontSize: 11, fontWeight: 800, color: CAT_COLOR[inv.category], fontFamily: 'monospace', minWidth: 96 }}>{inv.id}</span>
                  <span style={{ fontSize: 13, color: TEXT, flex: 1 }}>{inv.title}</span>
                  <span style={{ fontSize: 10, color: SLATE, fontFamily: 'monospace' }}>{inv.adr}</span>
                  <StatusBadge status={inv.status} />
                  <span style={{ color: SLATE, fontSize: 12 }}>{expandedInv === inv.id ? '▲' : '▼'}</span>
                </div>
                {expandedInv === inv.id && (
                  <div style={{ marginTop: 10, fontSize: 12, color: MUTED, lineHeight: 1.6, paddingLeft: 108, paddingRight: 80 }}>
                    {inv.desc}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* ── Section 7: Quick Navigation ── */}
        <div style={{ borderTop: `1px solid rgba(255,255,255,0.06)`, paddingTop: 40 }}>
          <SectionHeader label="Forensic Operations" />
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14 }}>
            {[
              { path: '/archive-verify', label: 'Forensic Verifier', sub: 'Upload blocks · Verify chain · Export OEP', color: GOLD, border: GOLD_BORDER },
              { path: '/protocol', label: 'Protocol Architecture', sub: '4 diagrams · Runtime legitimacy stack · GPIL', color: BLUE, border: 'rgba(59,130,246,0.25)' },
              { path: '/atf-verify', label: 'ATF Verifier', sub: 'DR · TAR · RCR · CES gauge · Chain lineage', color: '#a855f7', border: 'rgba(168,85,247,0.25)' },
              { path: '/verify-independently', label: 'Independent Verification', sub: 'Public receipt verifier · No account needed', color: '#06b6d4', border: 'rgba(6,182,212,0.25)' },
            ].map(nav => (
              <button key={nav.path} onClick={() => navigate(nav.path)}
                style={{
                  background: NAVY2, border: `1px solid ${nav.border}`, borderRadius: 12,
                  padding: '20px 18px', cursor: 'pointer', textAlign: 'left', transition: 'all 0.2s',
                }}>
                <div style={{ fontSize: 14, fontWeight: 700, color: nav.color, marginBottom: 6 }}>{nav.label}</div>
                <div style={{ fontSize: 11, color: MUTED, lineHeight: 1.5 }}>{nav.sub}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div style={{ marginTop: 48, paddingTop: 28, borderTop: `1px solid rgba(255,255,255,0.04)`, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
          <div style={{ fontSize: 12, color: SLATE }}>
            OMNIX QUANTUM LTD · Trust Infrastructure · OMNIX-SEC-2026-001
          </div>
          <div style={{ display: 'flex', gap: 20, fontSize: 11, color: SLATE }}>
            <span>ADR-156–170</span>
            <span>RFC-ATF-1 · RFC-ATF-2 · RFC-ATF-3 · RFC-ATF-4</span>
            <span>FIPS 204 · ML-DSA-65</span>
            <span>67 invariants · 9 families</span>
          </div>
        </div>

      </div>
    </div>
  )
}
