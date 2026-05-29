/**
 * OMNIX Institutional Protocol Brief — /institutional-brief
 * ==========================================================
 * Structured as: institutional protocol brief (not a pitch deck).
 * Sections: Cover · Problem · Solution · Governance Lifecycle ·
 *           Key Properties · RFC Stack · Conformance · Verification · Closing
 *
 * PDF export via html2canvas + jsPDF.
 * Harold Nunes — OMNIX QUANTUM LTD — May 2026
 */

import { useRef, useState } from 'react'

const GOLD   = '#C9A227'
const NAVY   = '#060F1E'
const NAVY2  = '#0A1628'
const NAVY3  = '#0D1F35'
const BORDER = '#1a2d45'
const TEXT   = '#e2e8f0'
const MUTED  = '#94a3b8'
const SLATE  = '#475569'
const GREEN  = '#22c55e'
const CYAN   = '#22d3ee'
const RED    = '#ef4444'
const PURPLE = '#a855f7'

const DOI_ATF1 = 'https://doi.org/10.5281/zenodo.20155016'
const DOI_ATF2 = 'https://doi.org/10.5281/zenodo.20241344'
const DOI_ATF3 = 'https://doi.org/10.5281/zenodo.20247342'
const DOI_ATF4 = 'https://doi.org/10.5281/zenodo.20368895'

const KEY_PROPERTIES = [
  { label: 'Runtime Admissibility', desc: 'Execution authority verified at the exact moment a decision is bound to consequences — not after.', color: GOLD },
  { label: 'PQC Receipts', desc: 'Every governance outcome is sealed with ML-DSA-65 (NIST FIPS 204) — independently verifiable without OMNIX.', color: CYAN },
  { label: 'Offline Verification', desc: 'Any auditor can verify any receipt with only the receipt and the public key. No platform access required.', color: GREEN },
  { label: 'Immutable Evidence Lifecycle', desc: 'HOT → WARM → COLD archival pipeline. Merkle-chained blocks. Evidence custody preserved permanently.', color: PURPLE },
  { label: 'HALT Enforcement', desc: 'When governance cannot confirm admissibility, execution is blocked. No graceful degradation. No override path.', color: RED },
  { label: 'Sovereign Governance Interoperability', desc: 'Sovereign runtimes maintain independent policy while preserving cross-domain cryptographic verifiability.', color: '#f59e0b' },
]

const LIFECYCLE_NODES = [
  { id: 'L1', label: 'Human Authority', tag: 'ML-DSA-65 · DR', color: GOLD },
  { id: 'L2', label: 'Runtime Governance', tag: 'CES · RCR', color: CYAN },
  { id: 'L3', label: 'Governance Event', tag: 'CTAG · RC', color: PURPLE },
  { id: 'HALT', label: 'ENFORCEMENT', tag: 'HALT / ALLOW', color: RED, gate: true },
  { id: 'L4', label: 'Evidence Archive', tag: 'COLD Block', color: '#3b82f6' },
  { id: 'L5', label: 'OEP Export', tag: 'Offline Package', color: '#f59e0b' },
  { id: 'L6', label: 'Offline Verify', tag: 'No OMNIX needed', color: GREEN },
]

const RFC_STACK = [
  {
    id: 'RFC-ATF-1',
    title: 'Agent Trust Fabric Delegation Protocol',
    invariants: 'ATF-INV-001–006',
    scope: 'Identity, delegation, Monotonic Authority Reduction, PQC signing, chain root traceability.',
    doi: DOI_ATF1,
    doiLabel: 'zenodo.20155016',
    color: GOLD,
  },
  {
    id: 'RFC-ATF-2',
    title: 'Runtime Governance Continuity',
    invariants: 'RGC-INV-001–008',
    scope: 'CES lifecycle, temporal admissibility, RCR states (NOMINAL → HALT), cross-domain continuity.',
    doi: DOI_ATF2,
    doiLabel: 'zenodo.20241344',
    color: CYAN,
  },
  {
    id: 'RFC-ATF-3',
    title: 'Forensic Evidence & Interoperability',
    invariants: 'EAP/OEP/FEA/FVP · 26 invariants',
    scope: 'Evidence archive pipeline, offline export, forensic verification, cross-runtime interoperability.',
    doi: DOI_ATF3,
    doiLabel: 'zenodo.20247342',
    color: PURPLE,
  },
  {
    id: 'RFC-ATF-4',
    title: 'Proactive Governance Layer',
    invariants: 'AGV/SSD/DSPP · 19 Z3 proofs · dual Z3+TLA+',
    scope: 'Anticipatory Governance Veto Protocol (AGVP), Structural Shift Detector (CRSI), Dynamic Semantic Portability (DSPP). First dual-methodology verified AI governance RFC.',
    doi: DOI_ATF4,
    doiLabel: 'zenodo.20368895',
    color: '#f97316',
  },
]

export default function InstitutionalBriefPage() {
  const briefRef = useRef<HTMLDivElement>(null)
  const [exporting, setExporting] = useState(false)

  async function handleExport() {
    if (!briefRef.current || exporting) return
    setExporting(true)
    try {
      const { default: html2canvas } = await import('html2canvas')
      const { jsPDF } = await import('jspdf')
      const el = briefRef.current
      const canvas = await html2canvas(el, {
        scale: 2,
        useCORS: true,
        backgroundColor: NAVY,
        width: el.scrollWidth,
        height: el.scrollHeight,
        windowWidth: el.scrollWidth,
        windowHeight: el.scrollHeight,
      })
      const imgData = canvas.toDataURL('image/jpeg', 0.95)
      const pdfW = 210
      const pdfH = (canvas.height * pdfW) / canvas.width
      const pdf = new jsPDF({ orientation: pdfH > pdfW ? 'portrait' : 'landscape', unit: 'mm', format: 'a4' })
      const pageH = 297
      let yOffset = 0
      while (yOffset < pdfH) {
        if (yOffset > 0) pdf.addPage()
        pdf.addImage(imgData, 'JPEG', 0, -yOffset, pdfW, pdfH)
        yOffset += pageH
      }
      pdf.save(`OMNIX-ATF-Institutional-Brief-${new Date().toISOString().slice(0, 10)}.pdf`)
    } finally {
      setExporting(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: NAVY, fontFamily: "'Inter', system-ui, sans-serif", color: TEXT }}>

      {/* Top action bar */}
      <div style={{
        position: 'sticky', top: 0, zIndex: 100,
        background: `${NAVY}f0`, backdropFilter: 'blur(12px)',
        borderBottom: `1px solid ${BORDER}`,
        padding: '12px 32px', display: 'flex', alignItems: 'center', gap: 16,
      }}>
        <a href="/" style={{ color: GOLD, fontSize: 12, fontWeight: 700, fontFamily: 'monospace', textDecoration: 'none', letterSpacing: '0.08em' }}>
          OMNIX QUANTUM LTD
        </a>
        <span style={{ color: SLATE, fontSize: 11 }}>|</span>
        <span style={{ color: MUTED, fontSize: 11, letterSpacing: '0.06em' }}>INSTITUTIONAL PROTOCOL BRIEF</span>
        <div style={{ flex: 1 }} />
        <a href="/governance-flow" style={{ color: MUTED, fontSize: 11, textDecoration: 'none' }}
          onMouseEnter={e => (e.target as HTMLElement).style.color = GOLD}
          onMouseLeave={e => (e.target as HTMLElement).style.color = MUTED}>
          Governance Flow ↗
        </a>
        <a href="/archive-verify" style={{ color: MUTED, fontSize: 11, textDecoration: 'none' }}
          onMouseEnter={e => (e.target as HTMLElement).style.color = GOLD}
          onMouseLeave={e => (e.target as HTMLElement).style.color = MUTED}>
          Forensic Verifier ↗
        </a>
        <button
          onClick={handleExport}
          disabled={exporting}
          style={{
            padding: '8px 20px', borderRadius: 7,
            border: `1px solid ${GOLD}55`, background: exporting ? `${GOLD}10` : `${GOLD}20`,
            color: exporting ? MUTED : GOLD, fontSize: 12, fontWeight: 700,
            cursor: exporting ? 'not-allowed' : 'pointer', fontFamily: 'monospace',
          }}
        >
          {exporting ? 'Generating PDF…' : '↓ Export PDF'}
        </button>
      </div>

      {/* Brief content */}
      <div ref={briefRef} style={{ maxWidth: 900, margin: '0 auto', padding: '60px 40px 80px' }}>

        {/* ── COVER ─────────────────────────────────────────────────────────── */}
        <div style={{
          borderBottom: `1px solid ${BORDER}`, paddingBottom: 56, marginBottom: 56,
          display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 24,
        }}>
          <div>
            <div style={{ fontSize: 10, fontWeight: 700, color: GOLD, letterSpacing: '0.20em', marginBottom: 20 }}>
              OMNIX QUANTUM LTD · INSTITUTIONAL PROTOCOL BRIEF
            </div>
            <h1 style={{ fontSize: 'clamp(28px,4vw,42px)', fontWeight: 800, lineHeight: 1.15, margin: '0 0 16px', letterSpacing: '-0.02em' }}>
              ATF Runtime Governance<br />
              <span style={{ color: GOLD }}>Infrastructure</span>
            </h1>
            <p style={{ fontSize: 15, color: MUTED, margin: '0 0 28px', lineHeight: 1.7, maxWidth: 540 }}>
              Cryptographically verifiable runtime authority governance for autonomous systems.
              From human-signed delegation to immutable forensic archive — at the exact moment execution occurs.
            </p>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              {['169 Active Invariants', '28 Invariant Families', '6 Published RFCs', '202 ADRs', 'ML-DSA-65 · FIPS 204'].map(t => (
                <span key={t} style={{
                  fontSize: 10, fontWeight: 600, color: GOLD,
                  background: `${GOLD}12`, border: `1px solid ${GOLD}28`,
                  padding: '3px 10px', borderRadius: 4, fontFamily: 'monospace',
                }}>{t}</span>
              ))}
            </div>
          </div>
          <div style={{ textAlign: 'right', fontSize: 11, color: SLATE, lineHeight: 2 }}>
            <div>Harold Nunes · Founder & CEO</div>
            <div>OMNIX QUANTUM LTD</div>
            <div>United Kingdom · OMNIX QUANTUM LTD</div>
            <div style={{ marginTop: 8, color: MUTED, fontFamily: 'monospace' }}>May 2026 · v1.0</div>
            <div style={{ color: MUTED, fontFamily: 'monospace', fontSize: 10 }}>OMNIX-WALK-001</div>
          </div>
        </div>

        {/* ── PROBLEM ───────────────────────────────────────────────────────── */}
        <Section label="PROBLEM">
          <div style={{
            background: `rgba(239,68,68,0.04)`, border: `1px solid rgba(239,68,68,0.15)`,
            borderLeft: `3px solid ${RED}`, borderRadius: '0 8px 8px 0',
            padding: '20px 24px',
          }}>
            <p style={{ fontSize: 17, fontWeight: 600, color: TEXT, margin: '0 0 10px', lineHeight: 1.5 }}>
              AI systems can execute actions.
            </p>
            <p style={{ fontSize: 17, fontWeight: 600, color: MUTED, margin: 0, lineHeight: 1.5 }}>
              Most organizations cannot prove execution legitimacy at runtime.
            </p>
          </div>
          <p style={{ fontSize: 13, color: SLATE, marginTop: 16, lineHeight: 1.75 }}>
            Existing governance platforms produce reports and dashboards — retrospectively.
            They document what happened. None produce cryptographic evidence that a decision
            was made under valid authority conditions <em>before</em> the action occurred.
            When a regulator, auditor, or institutional counterparty asks for proof of
            governance at the moment of execution, there is no artifact to present.
          </p>
        </Section>

        {/* ── WHAT OMNIX ATF DOES ───────────────────────────────────────────── */}
        <Section label="WHAT OMNIX ATF DOES">
          <div style={{
            background: `${GOLD}08`, border: `1px solid ${GOLD}22`,
            borderLeft: `3px solid ${GOLD}`, borderRadius: '0 8px 8px 0',
            padding: '20px 24px', marginBottom: 20,
          }}>
            <p style={{ fontSize: 16, fontWeight: 700, color: TEXT, margin: 0, lineHeight: 1.5 }}>
              OMNIX ATF enforces runtime authority governance — producing cryptographically signed,
              independently verifiable artifacts at every execution decision, sealed before the action occurs.
            </p>
          </div>
          <p style={{ fontSize: 13, color: SLATE, margin: '0 0 8px', lineHeight: 1.75 }}>
            The Agent Trust Fabric (ATF) is a four-layer governance stack: Identity (L1) → Delegation (L2) →
            Temporal (L3) → Runtime Continuity (L4). Every autonomous execution path traverses all layers.
            Authority propagates downward. Evidence flows upward to immutable custody.
            The protocol decides whether execution is admitted — not the application, not the operator.
          </p>
        </Section>

        {/* ── GOVERNANCE LIFECYCLE ──────────────────────────────────────────── */}
        <Section label="GOVERNANCE LIFECYCLE · OMNIX-WALK-001">
          <div style={{ display: 'flex', alignItems: 'center', gap: 0, overflowX: 'auto', paddingBottom: 8 }}>
            {LIFECYCLE_NODES.map((n, i) => (
              <div key={n.id} style={{ display: 'flex', alignItems: 'center', flexShrink: 0 }}>
                <div style={{
                  padding: n.gate ? '14px 18px' : '12px 16px',
                  borderRadius: n.gate ? 0 : 8,
                  background: n.gate ? `${RED}18` : `${n.color}0d`,
                  border: `1px solid ${n.color}${n.gate ? '66' : '30'}`,
                  clipPath: n.gate ? 'polygon(8% 0%, 92% 0%, 100% 50%, 92% 100%, 8% 100%, 0% 50%)' : undefined,
                  textAlign: 'center', minWidth: n.gate ? 90 : 80,
                }}>
                  <div style={{ fontSize: 9, fontWeight: 800, color: n.color, fontFamily: 'monospace', letterSpacing: '0.06em', marginBottom: 4 }}>
                    {n.id}
                  </div>
                  <div style={{ fontSize: 10, fontWeight: 700, color: TEXT, marginBottom: 2, lineHeight: 1.2 }}>{n.label}</div>
                  <div style={{ fontSize: 9, color: MUTED, fontFamily: 'monospace' }}>{n.tag}</div>
                </div>
                {i < LIFECYCLE_NODES.length - 1 && (
                  <div style={{ width: 16, height: 1, background: BORDER, flexShrink: 0 }} />
                )}
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 24, marginTop: 20, flexWrap: 'wrap' }}>
            {[
              { label: 'Delegation ID', value: 'ATFDR-7F3A9B2C1E4D8F6A' },
              { label: 'HALT fired at', value: '15:33:01Z · CES 8.33' },
              { label: 'Block sealed', value: 'OMNIX-BLOCK-20260518-000147' },
              { label: 'OEP export', value: 'OEP-20260518-A3F8C241' },
            ].map(f => (
              <div key={f.label} style={{ fontSize: 11 }}>
                <div style={{ color: SLATE, marginBottom: 2, fontSize: 10 }}>{f.label}</div>
                <div style={{ color: CYAN, fontFamily: 'monospace', fontWeight: 600 }}>{f.value}</div>
              </div>
            ))}
          </div>
        </Section>

        {/* ── KEY PROPERTIES ────────────────────────────────────────────────── */}
        <Section label="KEY PROPERTIES">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 12 }}>
            {KEY_PROPERTIES.map(p => (
              <div key={p.label} style={{
                padding: '16px 18px', borderRadius: 8,
                background: `${p.color}07`, border: `1px solid ${p.color}22`,
              }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: p.color, marginBottom: 6, fontFamily: 'monospace' }}>
                  {p.label}
                </div>
                <div style={{ fontSize: 12, color: MUTED, lineHeight: 1.65 }}>{p.desc}</div>
              </div>
            ))}
          </div>
        </Section>

        {/* ── RFC STACK ─────────────────────────────────────────────────────── */}
        <Section label="FOUNDATIONAL RFC STACK">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {RFC_STACK.map(r => (
              <div key={r.id} style={{
                display: 'flex', gap: 20, alignItems: 'flex-start',
                padding: '16px 20px', borderRadius: 8,
                background: `${r.color}07`, border: `1px solid ${r.color}22`,
              }}>
                <div style={{ flexShrink: 0, paddingTop: 2 }}>
                  <div style={{
                    fontSize: 10, fontWeight: 800, color: r.color, fontFamily: 'monospace',
                    background: `${r.color}18`, border: `1px solid ${r.color}40`,
                    padding: '3px 10px', borderRadius: 6, marginBottom: 6, whiteSpace: 'nowrap',
                  }}>{r.id}</div>
                  <a href={r.doi} target="_blank" rel="noopener noreferrer" style={{
                    fontSize: 9, color: SLATE, fontFamily: 'monospace', textDecoration: 'none',
                    display: 'block', whiteSpace: 'nowrap',
                  }}
                    onMouseEnter={e => (e.target as HTMLElement).style.color = r.color}
                    onMouseLeave={e => (e.target as HTMLElement).style.color = SLATE}
                  >DOI: {r.doiLabel} ↗</a>
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 700, color: TEXT, marginBottom: 4 }}>{r.title}</div>
                  <div style={{ fontSize: 11, color: r.color, fontFamily: 'monospace', marginBottom: 6 }}>{r.invariants}</div>
                  <div style={{ fontSize: 12, color: SLATE, lineHeight: 1.6 }}>{r.scope}</div>
                </div>
              </div>
            ))}
          </div>
        </Section>

        {/* ── CONFORMANCE ───────────────────────────────────────────────────── */}
        <Section label="CONFORMANCE BASELINE · GOVERNANCE_BASELINE-2026-Q2-001">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 1, background: BORDER, borderRadius: 10, overflow: 'hidden' }}>
            {[
              { value: '169', label: 'Active Invariants', sub: 'across 28 families', color: GOLD },
              { value: '28', label: 'Invariant Families', sub: 'ATF/RGC/BEV/MIVP/CGE/GUGT/TGB/OGR/OGI/RCEP', color: CYAN },
              { value: '202', label: 'Architecture Decisions', sub: 'ADR-001 through ADR-202', color: PURPLE },
              { value: 'Yes', label: 'Offline Verifiable', sub: 'OEP + CLI verifier · no OMNIX needed', color: GREEN },
            ].map(s => (
              <div key={s.label} style={{ background: NAVY2, padding: '24px 20px', textAlign: 'center' }}>
                <div style={{ fontSize: 32, fontWeight: 800, color: s.color, fontFamily: 'monospace', marginBottom: 6 }}>{s.value}</div>
                <div style={{ fontSize: 11, fontWeight: 700, color: TEXT, marginBottom: 4 }}>{s.label}</div>
                <div style={{ fontSize: 10, color: SLATE, fontFamily: 'monospace', lineHeight: 1.4 }}>{s.sub}</div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 14, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            {['245+ tests passing', 'Architecture freeze active', 'ML-DSA-65 · NIST FIPS 204', 'Zenodo + Figshare deposits'].map(t => (
              <span key={t} style={{
                fontSize: 10, color: MUTED, background: NAVY3, border: `1px solid ${BORDER}`,
                padding: '3px 10px', borderRadius: 4, fontFamily: 'monospace',
              }}>{t}</span>
            ))}
          </div>
        </Section>

        {/* ── VERIFICATION ──────────────────────────────────────────────────── */}
        <Section label="INDEPENDENT VERIFICATION">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div style={{
              padding: '20px 22px', borderRadius: 8,
              background: `${GREEN}07`, border: `1px solid ${GREEN}20`,
            }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: GREEN, letterSpacing: '0.12em', marginBottom: 12, fontFamily: 'monospace' }}>
                FORENSIC ARCHIVE VERIFIER
              </div>
              <p style={{ fontSize: 12, color: MUTED, margin: '0 0 14px', lineHeight: 1.7 }}>
                Any auditor can verify any OMNIX governance receipt using only:
                the receipt file, the platform public key, and the open-source CLI verifier.
                No OMNIX account. No platform access. No vendor dependency.
              </p>
              <a href="/archive-verify" style={{
                fontSize: 11, color: GREEN, fontFamily: 'monospace', textDecoration: 'none', fontWeight: 600,
              }}>Open Forensic Verifier ↗</a>
            </div>
            <div style={{
              padding: '20px 22px', borderRadius: 8,
              background: `${CYAN}07`, border: `1px solid ${CYAN}20`,
            }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: CYAN, letterSpacing: '0.12em', marginBottom: 12, fontFamily: 'monospace' }}>
                THREE VERIFICATION PLANES
              </div>
              {[
                { plane: 'Plane 1 · Browser', desc: 'Merkle hash + canonical hash — instant' },
                { plane: 'Plane 2 · Server', desc: 'ML-DSA-65 PQC signature — authoritative' },
                { plane: 'Plane 3 · Offline OEP', desc: 'EAP-INV-005 — no connectivity required' },
              ].map(v => (
                <div key={v.plane} style={{ marginBottom: 10 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: TEXT, fontFamily: 'monospace', marginBottom: 2 }}>{v.plane}</div>
                  <div style={{ fontSize: 11, color: MUTED }}>{v.desc}</div>
                </div>
              ))}
            </div>
          </div>
        </Section>

        {/* ── CLOSING ───────────────────────────────────────────────────────── */}
        <div style={{
          marginTop: 56, padding: '40px 44px', borderRadius: 14,
          border: `1px solid ${GOLD}28`,
          background: `linear-gradient(135deg, ${GOLD}08 0%, transparent 70%)`,
          textAlign: 'center',
        }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: GOLD, letterSpacing: '0.20em', marginBottom: 20 }}>
            OMNIX ATF · CORE PRINCIPLE
          </div>
          <p style={{
            fontSize: 'clamp(18px, 3vw, 26px)', fontWeight: 700, color: TEXT,
            fontFamily: 'monospace', letterSpacing: '0.02em',
            margin: '0 0 28px', lineHeight: 1.4,
          }}>
            "The protocol decides whether execution is admitted."
          </p>
          <p style={{ fontSize: 13, color: MUTED, margin: '0 auto 28px', maxWidth: 560, lineHeight: 1.75 }}>
            Not the application. Not the operator. Not the AI model.
            Runtime legitimacy is enforced by the governance stack —
            and preserved immutably in the forensic archive.
          </p>
          <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
            <a href="/governance-flow" style={{
              padding: '10px 24px', borderRadius: 8, fontSize: 12, fontWeight: 700,
              background: GOLD, color: '#05070B', textDecoration: 'none',
            }}>Governance Lifecycle ↗</a>
            <a href="/archive-verify" style={{
              padding: '10px 24px', borderRadius: 8, fontSize: 12, fontWeight: 700,
              border: `1px solid ${CYAN}44`, color: CYAN, textDecoration: 'none',
            }}>Forensic Verifier ↗</a>
            <a href="/protocol" style={{
              padding: '10px 24px', borderRadius: 8, fontSize: 12, fontWeight: 700,
              border: `1px solid ${BORDER}`, color: MUTED, textDecoration: 'none',
            }}>Protocol Architecture ↗</a>
          </div>
        </div>

        {/* Footer */}
        <div style={{
          marginTop: 48, paddingTop: 24, borderTop: `1px solid ${BORDER}`,
          display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10,
        }}>
          <div style={{ fontSize: 11, color: SLATE, fontFamily: 'monospace' }}>
            OMNIX QUANTUM LTD · United Kingdom · omnixquantum.com
          </div>
          <div style={{ fontSize: 11, color: SLATE, fontFamily: 'monospace' }}>
            RFC-ATF-1/2/3/4/5/6 · 169 invariants · 202 ADRs · GOVERNANCE_BASELINE-2026-Q2-001
          </div>
        </div>

      </div>
    </div>
  )
}

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 48 }}>
      <div style={{
        fontSize: 9, fontWeight: 800, color: SLATE, letterSpacing: '0.18em',
        marginBottom: 18, fontFamily: 'monospace',
        display: 'flex', alignItems: 'center', gap: 12,
      }}>
        <span style={{ display: 'inline-block', width: 20, height: 1, background: SLATE }} />
        {label}
      </div>
      {children}
    </div>
  )
}
