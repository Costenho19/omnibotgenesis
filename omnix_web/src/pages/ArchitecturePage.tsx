import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Shield, ArrowRight, Lock, Database, Cpu, GitBranch, Eye, Layers, ChevronLeft, ExternalLink } from 'lucide-react'

type DiagramKey = 'pipeline' | 'receipt' | 'llm' | 'tenant' | 'trust' | 'authority'

interface Diagram {
  id: DiagramKey
  label: string
  icon: React.ReactNode
  adr: string
  description: string
}

const DIAGRAMS: Diagram[] = [
  { id: 'pipeline',   label: 'Governance Pipeline',     icon: <Layers size={16}/>,    adr: 'ADR-028/040',  description: '11-checkpoint decision evaluation — every automated action passes all gates before execution.' },
  { id: 'receipt',    label: 'Receipt Lifecycle',        icon: <Shield size={16}/>,    adr: 'ADR-078/097',  description: 'From decision to PQC-signed receipt to transparency chain — every decision is permanently auditable.' },
  { id: 'llm',        label: 'LLM Isolation Boundary',   icon: <Lock size={16}/>,      adr: 'ADR-148',      description: 'AI-generated content never reaches governance directly — only 22 approved numeric signal keys can cross the boundary.' },
  { id: 'tenant',     label: 'Tenant Isolation (AVM)',   icon: <Database size={16}/>,  adr: 'ISR-001',      description: 'Every client has its own isolated AVM calibration state — no cross-tenant signal contamination.' },
  { id: 'trust',      label: 'Trust Anchor Chain',       icon: <Eye size={16}/>,       adr: 'ADR-060/085',  description: 'Dilithium-3 (ML-DSA-65 / NIST FIPS 204) — post-quantum signing. Every receipt is independently verifiable without OMNIX infrastructure.' },
  { id: 'authority',  label: 'Runtime Authority Matrix', icon: <GitBranch size={16}/>, adr: 'ADR-146',      description: 'Four-tier authority model — explicit scope for every runtime governance action.' },
]

function PipelineDiagram() {
  const checkpoints = [
    { id: 'CP-0',  label: 'Signal Integrity',        color: '#3b82f6', sub: 'Input validation & sanitization' },
    { id: 'CP-1',  label: 'Context Admission Gate',  color: '#6366f1', sub: 'Market regime & Black Swan check' },
    { id: 'CP-2',  label: 'Temporal Coherence',      color: '#8b5cf6', sub: 'Non-Markovian memory validation' },
    { id: 'CP-3',  label: 'Risk Limits',             color: '#a855f7', sub: 'Drawdown & exposure caps' },
    { id: 'CP-4',  label: 'AML Gate',                color: '#d946ef', sub: 'Anti-money laundering screen' },
    { id: 'CP-5',  label: 'Ethics Screen',           color: '#ec4899', sub: 'Harm prevention filter' },
    { id: 'CP-6',  label: 'Adaptive Veto (AVM)',     color: '#f43f5e', sub: 'Per-tenant calibrated veto' },
    { id: 'CP-7',  label: 'Sharia Compliance',       color: '#ef4444', sub: 'Islamic finance gate' },
    { id: 'CP-8',  label: 'Execution Boundary',      color: '#f97316', sub: 'Execution integrity protocol' },
    { id: 'CP-9',  label: 'Scope Authorization',     color: '#f59e0b', sub: 'ADR-147 — scope defensibility' },
    { id: 'CP-10', label: 'PQC Receipt',             color: '#10b981', sub: 'Dilithium-3 signed receipt' },
    { id: 'CP-11', label: 'Jurisdictional',          color: '#22c55e', sub: 'Regulatory compliance check' },
  ]
  return (
    <div className="space-y-1.5">
      <div className="flex items-center gap-3 mb-4">
        <div className="px-3 py-1.5 rounded border text-xs font-mono" style={{background:'rgba(59,130,246,0.08)',borderColor:'rgba(59,130,246,0.3)',color:'#93c5fd'}}>
          INPUT SIGNAL
        </div>
        <ArrowRight size={14} className="text-slate-500"/>
        <span className="text-xs text-slate-500">11 checkpoints — fail-closed at every gate</span>
        <ArrowRight size={14} className="text-slate-500 ml-auto"/>
        <div className="px-3 py-1.5 rounded border text-xs font-mono" style={{background:'rgba(16,185,129,0.08)',borderColor:'rgba(16,185,129,0.3)',color:'#6ee7b7'}}>
          PQC RECEIPT
        </div>
      </div>
      <div className="grid grid-cols-2 gap-1.5 md:grid-cols-3 lg:grid-cols-4">
        {checkpoints.map((cp, i) => (
          <div key={cp.id} className="relative rounded-lg p-3 border" style={{background:`${cp.color}08`,borderColor:`${cp.color}25`}}>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded" style={{background:`${cp.color}20`,color:cp.color}}>{cp.id}</span>
              <span className="text-xs text-slate-300 font-medium truncate">{cp.label}</span>
            </div>
            <p className="text-[10px] text-slate-500">{cp.sub}</p>
            {i < checkpoints.length - 1 && (
              <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-px h-1.5" style={{background:cp.color,opacity:0.4}}/>
            )}
          </div>
        ))}
      </div>
      <div className="mt-4 p-3 rounded-lg border text-xs text-slate-400" style={{background:'rgba(239,68,68,0.05)',borderColor:'rgba(239,68,68,0.2)'}}>
        <span className="text-red-400 font-medium">Fail-closed invariant (INV-001):</span> Any checkpoint that cannot evaluate (exception, timeout, missing data) returns BLOCKED — never APPROVED.
      </div>
    </div>
  )
}

function ReceiptLifecycleDiagram() {
  const steps = [
    { step: '01', label: 'Decision Arrives',      detail: 'Input signal enters the pipeline via API, Telegram bot, or SDK call.', color: '#3b82f6' },
    { step: '02', label: '11-Checkpoint Eval',    detail: 'Every checkpoint runs sequentially. Any FAIL → BLOCKED verdict.', color: '#6366f1' },
    { step: '03', label: 'WAL Append (ISR-012)',  detail: 'Receipt written to Write-Ahead Log before DB attempt — zero data loss guarantee.', color: '#8b5cf6' },
    { step: '04', label: 'PQC Signing',           detail: 'Dilithium-3 (ML-DSA-65) signs the canonical hash. hash_version: sha256-v1 committed.', color: '#a855f7' },
    { step: '05', label: 'DB Commit',             detail: 'Receipt stored in decision_receipts. WAL entry committed (deleted).', color: '#10b981' },
    { step: '06', label: 'Transparency Chain',    detail: 'Entry appended to governance_transparency_log with merkle root. Chain verified on every read (ISR-022).', color: '#22c55e' },
    { step: '07', label: 'Independent Verify',    detail: 'Receipt verifiable at /verify or via omnix_verify.py — no OMNIX infra required.', color: '#f59e0b' },
  ]
  return (
    <div className="space-y-2">
      {steps.map((s, i) => (
        <div key={s.step} className="flex gap-3 items-start">
          <div className="flex flex-col items-center flex-shrink-0">
            <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold font-mono" style={{background:`${s.color}20`,color:s.color,border:`1px solid ${s.color}40`}}>
              {s.step}
            </div>
            {i < steps.length - 1 && <div className="w-px flex-1 mt-1" style={{background:`${s.color}30`,minHeight:16}}/>}
          </div>
          <div className="pb-3 flex-1">
            <div className="text-sm font-medium text-slate-200 mb-0.5">{s.label}</div>
            <div className="text-xs text-slate-500">{s.detail}</div>
          </div>
        </div>
      ))}
    </div>
  )
}

function LLMIsolationDiagram() {
  const approved = ['probability','risk_score','volatility','coherence_score','sentiment_score','confidence','drift_magnitude','veto_strength','regime_indicator','liquidity_score','concentration_risk','counterparty_risk','market_stress','correlation_breakdown','momentum_signal','mean_reversion','drawdown_pct','sharpe_estimate','var_estimate','tail_risk','anomaly_score','exposure_ratio']
  const forbidden = ['user_message','prompt','llm_response','raw_text','instruction','system_prompt','chat_history','context_window','model_output','token_sequence','completion','embedding']
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-stretch">
        {/* Left: LLM Side */}
        <div className="rounded-xl p-4 border" style={{background:'rgba(139,92,246,0.06)',borderColor:'rgba(139,92,246,0.2)'}}>
          <div className="text-xs font-mono text-purple-400 mb-2 uppercase tracking-wider">AI / LLM Layer</div>
          <p className="text-xs text-slate-400 mb-3">Conversational AI, Telegram bot, OpenAI / Gemini / Claude</p>
          <div className="space-y-1">
            {forbidden.slice(0,6).map(k => (
              <div key={k} className="text-[10px] font-mono px-2 py-0.5 rounded" style={{background:'rgba(239,68,68,0.1)',color:'#fca5a5',border:'1px solid rgba(239,68,68,0.15)'}}>✗ {k}</div>
            ))}
            <div className="text-[10px] text-slate-600 italic">+ {forbidden.length - 6} more forbidden keys…</div>
          </div>
        </div>
        {/* Center: Boundary */}
        <div className="flex flex-col items-center justify-center gap-3 py-4">
          <div className="rounded-xl px-4 py-3 border text-center" style={{background:'rgba(245,158,11,0.08)',borderColor:'rgba(245,158,11,0.3)'}}>
            <Lock size={20} className="mx-auto mb-1 text-amber-400"/>
            <div className="text-xs font-bold text-amber-400">LLM ISOLATION BOUNDARY</div>
            <div className="text-[10px] text-amber-300/60 mt-1">ADR-148 · INV-005</div>
            <div className="text-[10px] text-slate-500 mt-2">form_packet() — whitelist enforced<br/>Non-numeric values stripped<br/>Forbidden keys blocked (strict mode: raised)</div>
          </div>
          <div className="text-[10px] text-slate-600 text-center">Only GovernanceSignalPacket<br/>may cross →</div>
        </div>
        {/* Right: Governance Side */}
        <div className="rounded-xl p-4 border" style={{background:'rgba(16,185,129,0.06)',borderColor:'rgba(16,185,129,0.2)'}}>
          <div className="text-xs font-mono text-emerald-400 mb-2 uppercase tracking-wider">Governance Engine</div>
          <p className="text-xs text-slate-400 mb-3">11-checkpoint pipeline — only numeric signals</p>
          <div className="space-y-1">
            {approved.slice(0,8).map(k => (
              <div key={k} className="text-[10px] font-mono px-2 py-0.5 rounded" style={{background:'rgba(16,185,129,0.1)',color:'#6ee7b7',border:'1px solid rgba(16,185,129,0.15)'}}>✓ {k}</div>
            ))}
            <div className="text-[10px] text-slate-600 italic">+ {approved.length - 8} more approved keys…</div>
          </div>
        </div>
      </div>
      <div className="p-3 rounded-lg border text-xs text-slate-400" style={{background:'rgba(245,158,11,0.05)',borderColor:'rgba(245,158,11,0.15)'}}>
        <span className="text-amber-400 font-medium">INV-005:</span> No raw LLM-generated text or non-numeric artifact key may reach the governance pipeline. Every crossing is logged with packet_id, source, asset, domain, stripped_keys, and timestamp.
      </div>
    </div>
  )
}

function TenantIsolationDiagram() {
  const tenants = [
    { id: 'BANK-A',    color: '#3b82f6', weights: {risk_score:0.4,volatility:0.3,coherence:0.3}, threshold: 0.72 },
    { id: 'INSURER-B', color: '#8b5cf6', weights: {risk_score:0.3,volatility:0.2,coherence:0.5}, threshold: 0.65 },
    { id: 'FUND-C',    color: '#10b981', weights: {risk_score:0.5,volatility:0.4,coherence:0.1}, threshold: 0.80 },
  ]
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {tenants.map(t => (
          <div key={t.id} className="rounded-xl p-4 border" style={{background:`${t.color}08`,borderColor:`${t.color}25`}}>
            <div className="text-xs font-mono mb-3" style={{color:t.color}}>{t.id}</div>
            <div className="space-y-2">
              {Object.entries(t.weights).map(([k,v]) => (
                <div key={k}>
                  <div className="flex justify-between text-[10px] mb-0.5">
                    <span className="text-slate-400">{k}</span>
                    <span style={{color:t.color}}>{(v*100).toFixed(0)}%</span>
                  </div>
                  <div className="h-1.5 rounded-full" style={{background:'rgba(255,255,255,0.06)'}}>
                    <div className="h-full rounded-full" style={{width:`${v*100}%`,background:t.color,opacity:0.7}}/>
                  </div>
                </div>
              ))}
              <div className="mt-3 pt-2 border-t text-[10px] flex justify-between" style={{borderColor:`${t.color}20`}}>
                <span className="text-slate-500">Veto threshold</span>
                <span className="font-mono" style={{color:t.color}}>{t.threshold.toFixed(2)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="rounded-xl p-3 border text-xs text-center" style={{background:'rgba(15,23,42,0.8)',borderColor:'rgba(99,102,241,0.2)'}}>
        <span className="text-indigo-400 font-medium">get_avm_instance(tenant_id)</span>
        <span className="text-slate-500"> — each tenant is an isolated registry entry. No cross-tenant signal contamination. </span>
        <span className="text-indigo-400">ISR-001 · INV-004</span>
      </div>
    </div>
  )
}

function TrustAnchorDiagram() {
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div className="rounded-xl p-4 border space-y-3" style={{background:'rgba(16,185,129,0.06)',borderColor:'rgba(16,185,129,0.2)'}}>
          <div className="text-xs font-mono text-emerald-400 uppercase tracking-wider">Receipt Anatomy</div>
          {[
            ['receipt_id',   'OMNIX-GOV-A1B2C3D4E5F6',       'Globally unique — SHA-256 of inputs'],
            ['content_hash', 'a3f9…c2d1 (SHA-256)',           'hash_version: sha256-v1 committed inside'],
            ['signature',    'base64(Dilithium-3 sig)',        'NIST FIPS 204 — ML-DSA-65'],
            ['public_key',   'base64(Dilithium-3 pub)',        'Embedded — verify without OMNIX infra'],
            ['prev_hash',    'f7e2…88ab',                      'Links to prior receipt — chain continuity'],
          ].map(([k,v,note]) => (
            <div key={k as string} className="space-y-0.5">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono text-emerald-400/80">{k as string}</span>
                <span className="text-[10px] font-mono text-slate-400 truncate">{v as string}</span>
              </div>
              <div className="text-[10px] text-slate-600 pl-2">{note as string}</div>
            </div>
          ))}
        </div>
        <div className="rounded-xl p-4 border space-y-3" style={{background:'rgba(245,158,11,0.05)',borderColor:'rgba(245,158,11,0.2)'}}>
          <div className="text-xs font-mono text-amber-400 uppercase tracking-wider">Verification Chain</div>
          {[
            { step: '1', label: 'Compute canonical hash', detail: 'Sort keys, SHA-256 — reproducible without OMNIX' },
            { step: '2', label: 'Verify Dilithium-3 sig', detail: 'public_key embedded in receipt — no PKI required' },
            { step: '3', label: 'Check prev_hash chain',  detail: 'Every receipt links to prior — tamper is detectable' },
            { step: '4', label: 'Verify hash_version',    detail: 'sha256-v1 — algorithm explicit in every receipt' },
          ].map(s => (
            <div key={s.step} className="flex gap-2">
              <div className="w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center text-[10px] font-bold" style={{background:'rgba(245,158,11,0.2)',color:'#fbbf24'}}>{s.step}</div>
              <div>
                <div className="text-xs text-slate-300">{s.label}</div>
                <div className="text-[10px] text-slate-500">{s.detail}</div>
              </div>
            </div>
          ))}
          <Link to="/verify" className="flex items-center gap-2 text-xs text-amber-400 hover:text-amber-300 mt-2">
            <ExternalLink size={12}/> Open Receipt Verifier
          </Link>
        </div>
      </div>
    </div>
  )
}

function AuthorityMatrixDiagram() {
  const tiers = [
    { tier: 'TIER-1', label: 'Founder / Architect', holder: 'Harold Nunes', scope: 'ADR filing, invariant changes, key rotation, PQC algorithm changes', color: '#f59e0b', width: '100%' },
    { tier: 'TIER-2', label: 'Governance Admin',    holder: 'Authorized operator', scope: 'AVM calibration, threshold adjustments, scope authorization issuance', color: '#6366f1', width: '80%' },
    { tier: 'TIER-3', label: 'B2B Client (API)',    holder: 'Authenticated client', scope: 'Submit governance evaluations, read own receipts, configure own thresholds', color: '#3b82f6', width: '55%' },
    { tier: 'TIER-4', label: 'Public / Sandbox',   holder: 'Unauthenticated',       scope: 'Public sandbox evaluations, receipt verification, transparency log reads', color: '#10b981', width: '30%' },
  ]
  return (
    <div className="space-y-3">
      {tiers.map(t => (
        <div key={t.tier} className="rounded-xl p-4 border" style={{background:`${t.color}06`,borderColor:`${t.color}20`}}>
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0">
              <div className="text-[10px] font-mono px-2 py-0.5 rounded" style={{background:`${t.color}15`,color:t.color}}>{t.tier}</div>
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-1">
                <span className="text-sm font-medium text-slate-200">{t.label}</span>
                <span className="text-[10px] text-slate-500">{t.holder}</span>
              </div>
              <p className="text-[11px] text-slate-400 mb-2">{t.scope}</p>
              <div className="h-1 rounded-full" style={{background:'rgba(255,255,255,0.05)'}}>
                <div className="h-full rounded-full" style={{width:t.width,background:t.color,opacity:0.6}}/>
              </div>
            </div>
          </div>
        </div>
      ))}
      <div className="p-3 rounded-lg border text-xs text-slate-400" style={{background:'rgba(99,102,241,0.05)',borderColor:'rgba(99,102,241,0.15)'}}>
        <span className="text-indigo-400 font-medium">ADR-146:</span> Every runtime governance action maps explicitly to one of these tiers. No action exists outside the matrix. Authority cannot be escalated programmatically.
      </div>
    </div>
  )
}

const DIAGRAM_COMPONENTS: Record<DiagramKey, React.ReactNode> = {
  pipeline:  <PipelineDiagram/>,
  receipt:   <ReceiptLifecycleDiagram/>,
  llm:       <LLMIsolationDiagram/>,
  tenant:    <TenantIsolationDiagram/>,
  trust:     <TrustAnchorDiagram/>,
  authority: <AuthorityMatrixDiagram/>,
}

export default function ArchitecturePage() {
  const [active, setActive] = useState<DiagramKey>('pipeline')
  const current = DIAGRAMS.find(d => d.id === active)!

  return (
    <div className="min-h-screen text-white" style={{background:'linear-gradient(135deg,#0a0f1e 0%,#0d1529 50%,#0a0f1e 100%)'}}>
      {/* Header */}
      <div className="border-b" style={{borderColor:'rgba(255,255,255,0.06)'}}>
        <div className="max-w-6xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/" className="flex items-center gap-2 text-slate-400 hover:text-slate-200 text-sm">
              <ChevronLeft size={16}/> Back
            </Link>
            <div className="w-px h-4 bg-slate-700"/>
            <div className="flex items-center gap-2">
              <Cpu size={18} className="text-blue-400"/>
              <span className="text-base font-semibold text-slate-100">Architecture</span>
              <span className="text-xs text-slate-500 ml-1">OMNIX QUANTUM</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-[10px] font-mono px-2 py-1 rounded border" style={{background:'rgba(16,185,129,0.08)',borderColor:'rgba(16,185,129,0.25)',color:'#6ee7b7'}}>
              OMNIX-BASELINE-2026-Q2-001
            </span>
            <span className="text-[10px] font-mono px-2 py-1 rounded border" style={{background:'rgba(99,102,241,0.08)',borderColor:'rgba(99,102,241,0.25)',color:'#a5b4fc'}}>
              {DIAGRAMS.length} diagrams · 202 ADRs
            </span>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-10">
        {/* Title */}
        <div className="mb-10">
          <h1 className="text-3xl font-bold text-slate-100 mb-3">
            Decision Governance Infrastructure
          </h1>
          <p className="text-slate-400 max-w-2xl leading-relaxed">
            Six architectural diagrams that define how OMNIX verifies and governs automated decisions before execution.
            Every diagram maps directly to one or more Architecture Decision Records.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-1.5">
            {DIAGRAMS.map(d => (
              <button
                key={d.id}
                onClick={() => setActive(d.id)}
                className="w-full text-left rounded-xl p-3.5 border transition-all duration-150"
                style={active === d.id ? {
                  background:'rgba(99,102,241,0.12)',
                  borderColor:'rgba(99,102,241,0.4)',
                } : {
                  background:'rgba(255,255,255,0.02)',
                  borderColor:'rgba(255,255,255,0.06)',
                }}
              >
                <div className="flex items-center gap-2 mb-1" style={{color: active === d.id ? '#a5b4fc' : '#94a3b8'}}>
                  {d.icon}
                  <span className="text-xs font-medium">{d.label}</span>
                </div>
                <div className="text-[10px] font-mono" style={{color: active === d.id ? '#6366f1' : '#475569'}}>{d.adr}</div>
              </button>
            ))}

            {/* Links */}
            <div className="pt-4 space-y-2">
              <div className="text-[10px] text-slate-600 uppercase tracking-wider mb-2">Related</div>
              {[
                ['/verify',       'Receipt Verifier'],
                ['/crisis-replay','Crisis Replay'],
                ['/try',          'Live Sandbox'],
                ['/audit',        'Audit Trail'],
              ].map(([path,label]) => (
                <Link key={path} to={path} className="flex items-center gap-2 text-xs text-slate-500 hover:text-slate-300 transition-colors">
                  <ArrowRight size={11}/>{label}
                </Link>
              ))}
            </div>
          </div>

          {/* Main diagram area */}
          <div className="lg:col-span-3">
            <div className="rounded-2xl border" style={{background:'rgba(255,255,255,0.02)',borderColor:'rgba(255,255,255,0.07)'}}>
              {/* Diagram header */}
              <div className="p-5 border-b" style={{borderColor:'rgba(255,255,255,0.06)'}}>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className="text-slate-200 font-semibold">{current.label}</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded" style={{background:'rgba(99,102,241,0.15)',color:'#a5b4fc',border:'1px solid rgba(99,102,241,0.3)'}}>{current.adr}</span>
                    </div>
                    <p className="text-sm text-slate-400 leading-relaxed max-w-2xl">{current.description}</p>
                  </div>
                </div>
              </div>
              {/* Diagram content */}
              <div className="p-5">
                {DIAGRAM_COMPONENTS[active]}
              </div>
            </div>

            {/* Invariants strip */}
            <div className="mt-4 rounded-xl p-4 border" style={{background:'rgba(15,23,42,0.6)',borderColor:'rgba(255,255,255,0.06)'}}>
              <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-3">10 Governance Invariants — Frozen · OMNIX-BASELINE-2026-Q2-001</div>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
                {[
                  ['INV-001','Fail-Closed Pipeline'],
                  ['INV-002','Receipt per Decision'],
                  ['INV-003','Hash Version'],
                  ['INV-004','Tenant Isolation'],
                  ['INV-005','LLM Isolation'],
                  ['INV-006','Chain Read-Verify'],
                  ['INV-007','Replay Fidelity'],
                  ['INV-008','PQC Non-Negotiable'],
                  ['INV-009','AVM Security Params'],
                  ['INV-010','Semantic Version'],
                ].map(([id,label]) => (
                  <div key={id} className="flex items-center gap-1.5 text-[10px]">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 flex-shrink-0"/>
                    <span className="text-emerald-400 font-mono">{id}</span>
                    <span className="text-slate-500 truncate">{label}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
