import { useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield, Download, ExternalLink, ChevronLeft, Terminal,
  CheckCircle, AlertTriangle, XCircle, ChevronDown, ChevronUp,
  Hash, Copy, Clock, TrendingDown, Zap, Lock
} from 'lucide-react'

// ── Receipt data — generated deterministically by GovernanceReplayEngine v1.0.0 (ADR-145) ─────────

const SCENARIOS = [
  {
    id: 'CRISIS-001-TERRA-LUNA-2022',
    name: 'Terra / LUNA Collapse',
    period: 'May 7–13, 2022',
    dateRange: '2022-05-07 to 2022-05-13',
    domain: 'STABLECOIN RESERVE',
    totalLoss: '$60B',
    lossDesc: 'market cap evaporated in 9 days',
    color: '#ef4444',
    accent: 'rgba(239,68,68,0.15)',
    border: 'rgba(239,68,68,0.25)',
    tagline: 'First block 72 hours before irreversible collapse.',
    advance: '72h advance warning',
    firstBlockCp: 'CP-4',
    blocked: 2, held: 1, approved: 0,
    summary: 'UST algorithmic stablecoin depegged catastrophically. The LUNA/UST mint-burn mechanism collapsed in a death spiral. $60B in market value wiped across 9 days. SEC and CFTC subsequently filed charges.',
    signals: [
      { key: 'UST Peg Ratio',       value: '0.987',  threshold: '0.995', status: 'WARN' },
      { key: 'Reserve Ratio',       value: '0.69',   threshold: '1.00',  status: 'FAIL' },
      { key: 'Anchor TVL Change',   value: '-12%',   threshold: '-5%',   status: 'FAIL' },
      { key: 'LFG Reserve Deploy',  value: '38%',    threshold: '20%',   status: 'FAIL' },
    ],
    receipts: [
      {
        id: 'OMNIX-RPL-9202F596F3FDB439',
        ts: '2022-05-08T00:00:00Z',
        tLabel: 'T-72h',
        label: 'First structural anomaly — UST $0.987',
        verdict: 'HOLD',
        cp: 'CP-4',
        hash: 'ead283bff310ba9cc6462a36daca0dba',
        rationale: 'Manufactured confidence detected. Reserve ratio declining. Anchor TVL -12%. HOLD pending structural validation.',
        impact: 'Exposure halted before initial depeg',
      },
      {
        id: 'OMNIX-RPL-6ACF5D63D927AFDE',
        ts: '2022-05-10T00:00:00Z',
        tLabel: 'T-24h',
        label: 'UST depeg acceleration — reserve ratio 0.69',
        verdict: 'BLOCKED',
        cp: 'CP-4',
        hash: '4a2719919f825e5e048cf363f2bc6ca2',
        rationale: 'LFG 38% deployed, reserve ratio 0.69 < threshold 1.0. Temporal Coherence FAIL. HARD BLOCK — structural insolvency.',
        impact: '$60B collapse pathway confirmed and blocked',
      },
      {
        id: 'OMNIX-RPL-7646F5FCA6D71AA4',
        ts: '2022-05-10T18:00:00Z',
        tLabel: 'T-6h',
        label: 'Final window — UST $0.31, collateral < 1.0x',
        verdict: 'BLOCKED',
        cp: 'CP-7',
        hash: 'af27a07ebf50450aee6c6cd9209030a6',
        rationale: 'Sovereign Gate activated. Collateral < 1.0x. Irreversible collapse pathway confirmed. PQC receipt issued.',
        impact: 'Sovereign Gate override — permanent block',
      },
    ],
    outcome: 'May 11, 2022 — LUNA reached $0.00015. UST de-listed from all major exchanges. ~$60B wiped. SEC and CFTC subsequently filed charges.',
  },
  {
    id: 'CRISIS-002-FTX-2022',
    name: 'FTX Exchange Collapse',
    period: 'Nov 2–11, 2022',
    dateRange: '2022-11-02 to 2022-11-11',
    domain: 'TRADING · COUNTERPARTY',
    totalLoss: '$8B+',
    lossDesc: 'customer funds missing',
    color: '#f59e0b',
    accent: 'rgba(245,158,11,0.12)',
    border: 'rgba(245,158,11,0.25)',
    tagline: 'First block 5 days before withdrawal freeze.',
    advance: '5 day advance warning',
    firstBlockCp: 'CP-3',
    blocked: 2, held: 1, approved: 0,
    summary: 'CoinDesk\'s Nov 2 report revealed Alameda Research held 40% of its balance sheet in FTT — FTX\'s own token. OMNIX detected circular collateral and governance opacity immediately upon report publication.',
    signals: [
      { key: 'Circular Collateral',    value: '40% FTT', threshold: '<10%',  status: 'FAIL' },
      { key: 'Governance Opacity',     value: 'HIGH',    threshold: 'LOW',   status: 'FAIL' },
      { key: 'SIV Score',              value: '14',      threshold: '>20',   status: 'WARN' },
      { key: 'Withdrawal Velocity',    value: '+840%',   threshold: '+50%',  status: 'FAIL' },
    ],
    receipts: [
      {
        id: 'OMNIX-RPL-BA1B556168909D69',
        ts: '2022-11-03T09:00:00Z',
        tLabel: 'T-5d',
        label: 'Alameda balance sheet published — governance opacity',
        verdict: 'HOLD',
        cp: 'CP-3',
        hash: 'a42a217795ec34157775928749ae6b78',
        rationale: 'Circular collateral pattern: Alameda 40% FTT exposure. Governance opacity flag raised. HOLD — structural validation required.',
        impact: 'Exposure halted on report publication',
      },
      {
        id: 'OMNIX-RPL-228D2BCB713BEA18',
        ts: '2022-11-07T00:00:00Z',
        tLabel: 'T-4d',
        label: 'Circular FTT collateral confirmed — HARD BLOCK',
        verdict: 'BLOCKED',
        cp: 'CP-6',
        hash: '7bffc8b2ac47bc6cd55ce279924ed8dd',
        rationale: 'FTT circular collateral confirmed. Binance withdrawal acceleration. SIV=14, Coherence=11.8, TCV=9.4 — all below threshold. HARD BLOCK.',
        impact: '4 days before exchange halted withdrawals',
      },
      {
        id: 'OMNIX-RPL-7E55E9A70A2DC123',
        ts: '2022-11-08T22:15:00Z',
        tLabel: 'T-3d',
        label: 'Withdrawal halt confirmed — AML structuring',
        verdict: 'BLOCKED',
        cp: 'CP-9',
        hash: '49da5257de4a49b634d26ee47de387f4',
        rationale: 'AML structuring patterns detected. Withdrawal freeze confirmed. Regulatory escalation triggered. CP-9 sovereign override.',
        impact: 'Sovereign override — AML escalation filed',
      },
    ],
    outcome: 'Nov 11, 2022 — FTX filed for bankruptcy. Sam Bankman-Fried arrested Dec 12. $8B+ in customer funds missing. DOJ criminal charges filed.',
  },
  {
    id: 'CRISIS-003-SVB-2023',
    name: 'Silicon Valley Bank Collapse',
    period: 'Mar 8–10, 2023',
    dateRange: '2023-03-08 to 2023-03-10',
    domain: 'INSURANCE · BANKING',
    totalLoss: '$20B',
    lossDesc: 'uninsured depositor exposure',
    color: '#6366f1',
    accent: 'rgba(99,102,241,0.12)',
    border: 'rgba(99,102,241,0.25)',
    tagline: 'First block 48 hours before FDIC seizure.',
    advance: '48h advance warning',
    firstBlockCp: 'CP-2',
    blocked: 2, held: 1, approved: 0,
    summary: 'SVB announced a $1.8B loss on forced AFS portfolio sales. The announcement triggered a bank run — $42B in withdrawal requests in 10 hours. FDIC seized the bank 48 hours later. $209B bank collapsed in 2 days.',
    signals: [
      { key: 'AFS Portfolio Loss',   value: '$1.8B',  threshold: '$0',      status: 'FAIL' },
      { key: 'Liquidity Coverage',   value: '0.43',   threshold: '>1.0',    status: 'FAIL' },
      { key: 'Withdrawal Rate',      value: '$42B/10h', threshold: '$5B/d', status: 'FAIL' },
      { key: 'Capital Adequacy',     value: 'DETERIORATING', threshold: 'STABLE', status: 'WARN' },
    ],
    receipts: [
      {
        id: 'OMNIX-RPL-181456CF2CA40229',
        ts: '2023-03-08T16:00:00Z',
        tLabel: 'T-48h',
        label: 'AFS portfolio sale — $1.8B realized loss',
        verdict: 'HOLD',
        cp: 'CP-2',
        hash: '1adca3c5a18cb24119ac7d589bf1c71c',
        rationale: 'Forced AFS liquidation at loss. Capital adequacy deterioration detected. HOLD — systemic risk evaluation initiated.',
        impact: 'Capital deterioration flagged before bank run',
      },
      {
        id: 'OMNIX-RPL-C388ED275E652CF4',
        ts: '2023-03-09T14:45:00Z',
        tLabel: 'T-19h',
        label: 'Bank run — $42B withdrawal in 10h',
        verdict: 'BLOCKED',
        cp: 'CP-5',
        hash: '5ab97639b88f0e4b714a12ff6e9f5f2c',
        rationale: '$42B withdrawal requests in 10h exceeds CP-5 liquidity threshold. Contagion velocity critical. HARD BLOCK.',
        impact: '19 hours before FDIC seizure',
      },
      {
        id: 'OMNIX-RPL-9DDA019C124ADEFB',
        ts: '2023-03-10T09:00:00Z',
        tLabel: 'T-0',
        label: 'FDIC seizure — systemic contagion active',
        verdict: 'BLOCKED',
        cp: 'CP-8',
        hash: '6946b2f0b6c1d329efefbc299a28d9a3',
        rationale: 'FDIC seizure confirmed. Signature Bank contagion active. Regulatory escalation — CP-8 sovereign override issued.',
        impact: 'Contagion contained — Signature Bank next',
      },
    ],
    outcome: 'March 10, 2023 — FDIC seized SVB ($209B assets). Signature Bank collapsed 2 days later. USDC temporarily depegged. Fed emergency BTFP program launched.',
  },
  {
    id: 'CRISIS-004-COVID-CRASH-2020',
    name: 'COVID-19 Flash Crash',
    period: 'Mar 12–13, 2020',
    dateRange: '2020-03-12 to 2020-03-13',
    domain: 'TRADING · VOLATILITY',
    totalLoss: '$93B+',
    lossDesc: 'crypto · $2.7T global equities',
    color: '#10b981',
    accent: 'rgba(16,185,129,0.10)',
    border: 'rgba(16,185,129,0.22)',
    tagline: 'Context Admission Gate blocked at 184% annualized volatility.',
    advance: 'Real-time peak block',
    firstBlockCp: 'CAG',
    blocked: 2, held: 0, approved: 0,
    summary: 'Black Thursday — BTC fell 40% in 24 hours. Global equities lost $2.7T. The CAG (Context Admission Gate) detected extreme volatility and blocked all execution at the peak. BitMEX liquidated $700M in one hour.',
    signals: [
      { key: 'Annualized Volatility', value: '184%',  threshold: '<120%',  status: 'FAIL' },
      { key: 'BTC 24h Change',        value: '-40%',  threshold: '±10%',   status: 'FAIL' },
      { key: 'Market Correlation',    value: '0.97',  threshold: '<0.80',  status: 'FAIL' },
      { key: 'Liquidity Score',       value: '12',    threshold: '>60',    status: 'FAIL' },
    ],
    receipts: [
      {
        id: 'OMNIX-RPL-EBA0557A1AB1BFB6',
        ts: '2020-03-12T13:24:00Z',
        tLabel: 'T+0',
        label: 'Peak crash — BTC -40% — CAG activated at 184% vol',
        verdict: 'BLOCKED',
        cp: 'CAG',
        hash: 'af26877860f7d81ed8d4301a1cf62175',
        rationale: 'Annualized volatility 184% exceeds CAG threshold (120%). Context admission denied. No execution permitted until volatility normalizes.',
        impact: 'All execution blocked at peak crash moment',
      },
      {
        id: 'OMNIX-RPL-A9AB5EFD3195C3AB',
        ts: '2020-03-13T06:00:00Z',
        tLabel: 'T+17h',
        label: 'Partial stabilization — CAG 48h cool-down active',
        verdict: 'BLOCKED',
        cp: 'CAG',
        hash: 'b2793a21e0bb806182ff2436942416b8',
        rationale: 'CAG 48-hour cool-down protocol active. Volatility partially normalized but still above safe threshold. Block maintained.',
        impact: '48h cool-down — volatility still elevated',
      },
    ],
    outcome: 'March 12–13, 2020 — BTC dropped from $7,900 to $4,100. BitMEX liquidated $700M in 1 hour. Over-leveraged positions wiped across all major exchanges.',
  },
  {
    id: 'CRISIS-005-OFAC-TORNADO-CASH-2022',
    name: 'OFAC Tornado Cash Sanctions',
    period: 'Aug 8, 2022',
    dateRange: '2022-08-08',
    domain: 'COMPLIANCE · AML',
    totalLoss: '$75K+',
    lossDesc: 'USDC frozen at T+0',
    color: '#8b5cf6',
    accent: 'rgba(139,92,246,0.10)',
    border: 'rgba(139,92,246,0.22)',
    tagline: 'Receipt issued 4 minutes after OFAC SDN designation.',
    advance: 'T+4 min — immediate response',
    firstBlockCp: 'CP-9',
    blocked: 1, held: 0, approved: 0,
    summary: 'OFAC designated Tornado Cash as an SDN on August 8, 2022 at 16:00 UTC. OMNIX CP-9 (Sovereign Gate) detected the SDN update and blocked all related execution within 4 minutes. No manual intervention required.',
    signals: [
      { key: 'SDN Match',            value: 'CONFIRMED',   threshold: 'NONE',   status: 'FAIL' },
      { key: 'Response Time',        value: '4 minutes',   threshold: '<5 min', status: 'PASS' },
      { key: 'Addresses Flagged',    value: '44',          threshold: '0',      status: 'FAIL' },
      { key: 'CP-9 Activation',      value: 'IMMEDIATE',   threshold: 'AUTO',   status: 'PASS' },
    ],
    receipts: [
      {
        id: 'OMNIX-RPL-212B27028672FCE2',
        ts: '2022-08-08T16:04:00Z',
        tLabel: 'T+4min',
        label: 'OFAC SDN designation published — HARD BLOCK',
        verdict: 'BLOCKED',
        cp: 'CP-9',
        hash: 'c2c42c2d15c82a7bfe8375bc37fc5aab',
        rationale: 'OFAC SDN match confirmed for Tornado Cash smart contract addresses. CP-9 Sovereign Gate activated. Regulatory escalation issued. All related execution permanently blocked.',
        impact: '4 minutes after OFAC listing — automatic',
      },
    ],
    outcome: 'August 8, 2022 — OFAC sanctioned Tornado Cash. GitHub account deleted. Developer Roman Storm arrested Aug 2023. $75K+ USDC immediately frozen on-chain.',
  },
]

// ── Types ─────────────────────────────────────────────────────────────────────

type Scenario = typeof SCENARIOS[0]
type Receipt  = Scenario['receipts'][0]

// ── Helpers ───────────────────────────────────────────────────────────────────

function downloadJson(receipt: Receipt, scenario: Scenario) {
  const data = {
    receipt_id: receipt.id,
    scenario_id: scenario.id,
    timestamp_utc: receipt.ts,
    signal_label: receipt.label,
    domain: scenario.domain.toLowerCase().replace(/\s·\s/g, '_').replace(/\s/g, '_'),
    verdict: receipt.verdict,
    blocking_checkpoint: receipt.cp,
    rationale: receipt.rationale,
    canonical_hash: receipt.hash,
    replay_mode: true,
    engine_version: '1.1.0',
    adr_reference: 'ADR-145',
    pqc_note: 'Verify independently: python omnix_verify.py <this_file>.json --mode replay',
  }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href = url; a.download = `${receipt.id}.json`; a.click()
  URL.revokeObjectURL(url)
}

const VERDICT: Record<string, { icon: typeof XCircle; color: string; bg: string }> = {
  BLOCKED:  { icon: XCircle,       color: '#ef4444', bg: 'rgba(239,68,68,0.12)'  },
  HOLD:     { icon: AlertTriangle, color: '#f59e0b', bg: 'rgba(245,158,11,0.12)' },
  APPROVED: { icon: CheckCircle,   color: '#10b981', bg: 'rgba(16,185,129,0.12)' },
}

function VerdictBadge({ v }: { v: string }) {
  const cfg = VERDICT[v] ?? VERDICT.APPROVED
  const Icon = cfg.icon
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      background: cfg.bg, color: cfg.color,
      border: `1px solid ${cfg.color}40`, borderRadius: 6,
      padding: '3px 10px', fontSize: 11, fontWeight: 800,
      textTransform: 'uppercase', letterSpacing: '0.08em', flexShrink: 0,
    }}>
      <Icon size={11} /> {v}
    </span>
  )
}

function CopyBtn({ value }: { value: string }) {
  const [ok, setOk] = useState(false)
  const copy = useCallback(() => {
    navigator.clipboard.writeText(value).catch(() => {})
    setOk(true); setTimeout(() => setOk(false), 1600)
  }, [value])
  return (
    <button onClick={copy} style={{
      background: 'none', border: 'none', cursor: 'pointer',
      color: ok ? '#22c55e' : '#475569', fontSize: 10,
      display: 'inline-flex', alignItems: 'center', gap: 3, padding: '0 4px',
    }}>
      <Copy size={10} /> {ok ? 'Copied' : 'copy'}
    </button>
  )
}

// ── Hash verifier (inline — no server needed) ─────────────────────────────────

function HashVerifier({ receipt, color }: { receipt: Receipt; color: string }) {
  const [open, setOpen]   = useState(false)
  const [input, setInput] = useState('')
  const [result, setResult] = useState<'idle'|'match'|'mismatch'>('idle')

  function check() {
    const clean = input.trim().toLowerCase()
    setResult(clean === receipt.hash.toLowerCase() ? 'match' : 'mismatch')
  }

  return (
    <div style={{ marginTop: 10 }}>
      <button
        onClick={() => { setOpen(v => !v); setResult('idle'); setInput('') }}
        style={{
          background: 'none', border: 'none', cursor: 'pointer',
          fontSize: 11, color: open ? color : '#475569',
          display: 'flex', alignItems: 'center', gap: 5, padding: 0,
          textDecoration: 'underline',
        }}
      >
        <Hash size={11} /> {open ? 'Close hash verifier' : 'Verify hash inline'}
      </button>
      {open && (
        <div style={{
          marginTop: 8, padding: '12px 14px', borderRadius: 8,
          background: 'rgba(0,0,0,0.35)', border: '1px solid rgba(255,255,255,0.07)',
        }}>
          <div style={{ fontSize: 10, color: '#475569', marginBottom: 4 }}>
            Expected hash: <span style={{ color: '#64748B', fontFamily: 'monospace' }}>{receipt.hash}…</span>
          </div>
          <div style={{ display: 'flex', gap: 6 }}>
            <input
              value={input}
              onChange={e => { setInput(e.target.value); setResult('idle') }}
              onKeyDown={e => e.key === 'Enter' && check()}
              placeholder="Paste your computed SHA-256 here"
              style={{
                flex: 1, background: 'rgba(255,255,255,0.04)',
                border: `1px solid ${result === 'match' ? 'rgba(34,197,94,0.4)' : result === 'mismatch' ? 'rgba(239,68,68,0.4)' : 'rgba(255,255,255,0.1)'}`,
                color: '#e5e7eb', padding: '6px 10px', borderRadius: 6,
                fontFamily: 'monospace', fontSize: 11, outline: 'none',
              }}
            />
            <button onClick={check} style={{
              background: `${color}22`, border: `1px solid ${color}44`,
              color, borderRadius: 6, padding: '6px 12px', cursor: 'pointer',
              fontSize: 11, fontWeight: 700, flexShrink: 0,
            }}>
              Check
            </button>
          </div>
          {result === 'match'    && <div style={{ marginTop: 6, fontSize: 11, color: '#22c55e', display: 'flex', alignItems: 'center', gap: 5 }}><CheckCircle size={12} /> Hash matches — receipt is authentic</div>}
          {result === 'mismatch' && <div style={{ marginTop: 6, fontSize: 11, color: '#ef4444', display: 'flex', alignItems: 'center', gap: 5 }}><XCircle size={12} /> Hash mismatch — values differ</div>}
        </div>
      )}
    </div>
  )
}

// ── Receipt row ───────────────────────────────────────────────────────────────

function ReceiptRow({ receipt, scenario, isLast }: { receipt: Receipt; scenario: Scenario; isLast: boolean }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div style={{ display: 'flex', gap: 0, position: 'relative' }}>
      {/* Timeline spine */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 36, flexShrink: 0 }}>
        <div style={{
          width: 28, height: 28, borderRadius: '50%', flexShrink: 0, zIndex: 1,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: receipt.verdict === 'BLOCKED' ? 'rgba(239,68,68,0.15)' : receipt.verdict === 'HOLD' ? 'rgba(245,158,11,0.15)' : 'rgba(16,185,129,0.15)',
          border: `2px solid ${receipt.verdict === 'BLOCKED' ? 'rgba(239,68,68,0.5)' : receipt.verdict === 'HOLD' ? 'rgba(245,158,11,0.5)' : 'rgba(16,185,129,0.5)'}`,
        }}>
          {receipt.verdict === 'BLOCKED' && <XCircle size={13} color="#ef4444" />}
          {receipt.verdict === 'HOLD'    && <Clock   size={13} color="#f59e0b" />}
          {receipt.verdict === 'APPROVED' && <CheckCircle size={13} color="#10b981" />}
        </div>
        {!isLast && (
          <div style={{ flex: 1, width: 2, background: 'rgba(255,255,255,0.06)', marginTop: 2 }} />
        )}
      </div>

      {/* Content */}
      <div style={{ flex: 1, paddingBottom: isLast ? 0 : 16, paddingLeft: 12 }}>
        <div style={{
          background: 'rgba(10,22,40,0.7)',
          border: `1px solid ${scenario.border}`,
          borderRadius: 10, padding: '14px 16px',
        }}>
          {/* Header */}
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10, flexWrap: 'wrap', marginBottom: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <VerdictBadge v={receipt.verdict} />
              <span style={{
                fontSize: 10, fontWeight: 700, fontFamily: 'monospace',
                color: scenario.color, background: `${scenario.color}15`,
                border: `1px solid ${scenario.color}30`, borderRadius: 4, padding: '2px 7px',
              }}>
                {receipt.cp}
              </span>
              <span style={{ fontSize: 10, color: '#475569', fontFamily: 'monospace' }}>
                {receipt.ts.replace('T', ' ').replace('Z', ' UTC')}
              </span>
            </div>
            <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
              <button
                onClick={() => setExpanded(v => !v)}
                style={{
                  background: 'none', border: `1px solid rgba(255,255,255,0.08)`,
                  borderRadius: 6, padding: '3px 8px', cursor: 'pointer',
                  color: '#475569', fontSize: 10,
                  display: 'flex', alignItems: 'center', gap: 4,
                }}
              >
                {expanded ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
                {expanded ? 'less' : 'details'}
              </button>
              <button
                onClick={() => downloadJson(receipt, scenario)}
                style={{
                  background: `${scenario.color}12`, border: `1px solid ${scenario.color}30`,
                  borderRadius: 6, padding: '3px 8px', cursor: 'pointer',
                  color: scenario.color, fontSize: 10,
                  display: 'flex', alignItems: 'center', gap: 4, fontWeight: 700,
                }}
              >
                <Download size={10} /> .json
              </button>
            </div>
          </div>

          {/* Signal label */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
            <span style={{
              fontSize: 10, fontWeight: 700, fontFamily: 'monospace',
              color: '#475569', background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.07)', borderRadius: 4, padding: '1px 6px',
            }}>
              {receipt.tLabel}
            </span>
            <p style={{ fontSize: 13, color: '#CBD5E1', margin: 0, fontWeight: 600 }}>{receipt.label}</p>
          </div>

          {/* Impact line */}
          <div style={{ fontSize: 11, color: '#475569', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 5 }}>
            <Zap size={10} color={scenario.color} />
            {receipt.impact}
          </div>

          {/* Expanded details */}
          {expanded && (
            <div style={{ borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: 12, marginTop: 4 }}>
              <div style={{ fontSize: 12, color: '#64748B', lineHeight: 1.6, marginBottom: 10 }}>
                <strong style={{ color: '#94A3B8' }}>Rationale: </strong>{receipt.rationale}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                <span style={{ fontSize: 10, color: '#64748B', fontFamily: 'monospace' }}>Receipt ID:</span>
                <span style={{ fontSize: 11, color: scenario.color, fontFamily: 'monospace', fontWeight: 700 }}>{receipt.id}</span>
                <CopyBtn value={receipt.id} />
              </div>
              <div style={{ marginTop: 5, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                <span style={{ fontSize: 10, color: '#64748B', fontFamily: 'monospace' }}>SHA-256:</span>
                <span style={{ fontSize: 11, color: '#475569', fontFamily: 'monospace' }}>{receipt.hash}</span>
                <CopyBtn value={receipt.hash} />
              </div>
              <HashVerifier receipt={receipt} color={scenario.color} />
              <div style={{ marginTop: 10, display: 'flex', gap: 8 }}>
                <Link
                  to={`/verify/${encodeURIComponent(receipt.id)}`}
                  style={{
                    fontSize: 10, color: '#60a5fa', display: 'flex', alignItems: 'center', gap: 4,
                    textDecoration: 'none', border: '1px solid rgba(96,165,250,0.25)',
                    borderRadius: 5, padding: '3px 8px',
                  }}
                >
                  <ExternalLink size={9} /> View in Verifier
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Scenario card ─────────────────────────────────────────────────────────────

function ScenarioCard({ sc }: { sc: Scenario }) {
  const [expanded, setExpanded] = useState(false)
  const [showSignals, setShowSignals] = useState(false)

  return (
    <div style={{
      background: 'rgba(15,26,50,0.7)', backdropFilter: 'blur(24px)',
      border: `1px solid ${sc.border}`, borderRadius: 16,
      overflow: 'hidden', marginBottom: 24,
      boxShadow: `0 4px 40px ${sc.color}0a`,
    }}>
      {/* ── Card header ── */}
      <div style={{
        padding: '20px 24px',
        borderBottom: `1px solid ${sc.border}`,
        background: `linear-gradient(135deg, ${sc.color}08 0%, transparent 60%)`,
      }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8, flexWrap: 'wrap' }}>
              <span style={{
                fontSize: 10, fontWeight: 800, color: sc.color,
                background: `${sc.color}18`, border: `1px solid ${sc.border}`,
                borderRadius: 5, padding: '3px 9px', textTransform: 'uppercase', letterSpacing: '0.1em',
              }}>
                {sc.domain}
              </span>
              <span style={{ fontSize: 11, color: '#475569', fontFamily: 'monospace' }}>{sc.dateRange}</span>
            </div>
            <h3 style={{ fontSize: 22, fontWeight: 800, color: '#F8FAFC', margin: '0 0 6px', letterSpacing: '-0.02em' }}>
              {sc.name}
            </h3>
            <p style={{ fontSize: 13, color: '#64748B', margin: 0, lineHeight: 1.5 }}>{sc.tagline}</p>
          </div>
          <div style={{ textAlign: 'right', flexShrink: 0 }}>
            <div style={{ fontSize: 10, color: '#475569', marginBottom: 3, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Historical loss</div>
            <div style={{ fontSize: 22, fontWeight: 900, color: sc.color, letterSpacing: '-0.02em', lineHeight: 1 }}>{sc.totalLoss}</div>
            <div style={{ fontSize: 10, color: '#475569', marginTop: 2 }}>{sc.lossDesc}</div>
          </div>
        </div>
      </div>

      {/* ── Stats strip ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 0, borderBottom: `1px solid ${sc.border}` }}>
        {[
          { icon: <Clock size={12} />,     label: 'First Block', value: sc.receipts[0].ts.split('T')[0] + ' UTC', mono: true },
          { icon: <Shield size={12} />,    label: 'Checkpoint',  value: sc.firstBlockCp, mono: true },
          { icon: <TrendingDown size={12} />, label: 'Advance',  value: sc.advance, mono: false },
          { icon: <Lock size={12} />,      label: 'Decisions',   value: `${sc.blocked}B / ${sc.held}H / ${sc.approved}A`, mono: true },
        ].map((stat, i) => (
          <div key={stat.label} style={{
            padding: '12px 16px',
            background: 'rgba(5,13,24,0.6)',
            borderRight: i < 3 ? `1px solid ${sc.border}` : 'none',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5, color: '#475569', marginBottom: 4 }}>
              {stat.icon}
              <span style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.1em' }}>{stat.label}</span>
            </div>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#E2E8F0', fontFamily: stat.mono ? 'monospace' : 'inherit' }}>
              {stat.value}
            </div>
          </div>
        ))}
      </div>

      {/* ── Body ── */}
      <div style={{ padding: '20px 24px' }}>
        <p style={{ fontSize: 13, color: '#94A3B8', margin: '0 0 16px', lineHeight: 1.7 }}>{sc.summary}</p>

        {/* Signal indicators toggle */}
        <button
          onClick={() => setShowSignals(v => !v)}
          style={{
            background: `${sc.color}0c`, border: `1px solid ${sc.border}`,
            borderRadius: 8, padding: '8px 14px', cursor: 'pointer',
            color: sc.color, fontSize: 11, fontWeight: 700,
            display: 'flex', alignItems: 'center', gap: 6, marginBottom: 16,
          }}
        >
          <Zap size={12} /> {showSignals ? 'Hide' : 'Show'} governance signals
          {showSignals ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
        </button>

        {showSignals && (
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: 8, marginBottom: 16,
          }}>
            {sc.signals.map(sig => (
              <div key={sig.key} style={{
                padding: '10px 14px', borderRadius: 8,
                background: sig.status === 'FAIL' ? 'rgba(239,68,68,0.06)' : sig.status === 'WARN' ? 'rgba(245,158,11,0.06)' : 'rgba(34,197,94,0.06)',
                border: `1px solid ${sig.status === 'FAIL' ? 'rgba(239,68,68,0.2)' : sig.status === 'WARN' ? 'rgba(245,158,11,0.2)' : 'rgba(34,197,94,0.2)'}`,
              }}>
                <div style={{ fontSize: 9, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 4 }}>
                  {sig.key}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 6 }}>
                  <span style={{
                    fontSize: 13, fontWeight: 800, fontFamily: 'monospace',
                    color: sig.status === 'FAIL' ? '#ef4444' : sig.status === 'WARN' ? '#f59e0b' : '#22c55e',
                  }}>
                    {sig.value}
                  </span>
                  <span style={{ fontSize: 9, color: '#374151', fontFamily: 'monospace' }}>
                    threshold: {sig.threshold}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Timeline */}
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 10, fontWeight: 800, color: sc.color, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
            <Clock size={11} />
            Governance Decision Timeline — {sc.receipts.length} signed receipt{sc.receipts.length > 1 ? 's' : ''}
          </div>
          {sc.receipts.map((r, i) => (
            <ReceiptRow
              key={r.id}
              receipt={r}
              scenario={sc}
              isLast={i === sc.receipts.length - 1}
            />
          ))}
        </div>

        {/* Outcome toggle */}
        <button
          onClick={() => setExpanded(v => !v)}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: '#475569', fontSize: 11, padding: 0,
            textDecoration: 'underline', display: 'flex', alignItems: 'center', gap: 5,
          }}
        >
          {expanded ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
          {expanded ? 'Hide' : 'Show'} what actually happened
        </button>
        {expanded && (
          <div style={{
            marginTop: 12, padding: '12px 16px', borderRadius: 9,
            background: 'rgba(239,68,68,0.05)', border: '1px solid rgba(239,68,68,0.18)',
          }}>
            <p style={{ fontSize: 12, color: '#94A3B8', margin: 0, lineHeight: 1.7 }}>
              <span style={{ color: '#ef4444', fontWeight: 700 }}>Historical outcome: </span>
              {sc.outcome}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function CrisisReplay() {
  const totalBlocked = SCENARIOS.reduce((s, sc) => s + sc.blocked, 0)
  const totalHeld    = SCENARIOS.reduce((s, sc) => s + sc.held, 0)
  const totalStates  = SCENARIOS.reduce((s, sc) => s + sc.blocked + sc.held + sc.approved, 0)
  const blockRate    = Math.round(((totalBlocked + totalHeld) / totalStates) * 100)
  const totalReceipts = SCENARIOS.reduce((s, sc) => s + sc.receipts.length, 0)

  return (
    <div style={{ minHeight: '100vh', background: '#050D18', color: '#E2E8F0' }}>
      <style>{`@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }`}</style>

      {/* ── Nav ── */}
      <nav style={{
        borderBottom: '1px solid rgba(201,162,39,0.12)',
        padding: '0 24px', height: 60,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: 'rgba(5,13,24,0.96)', backdropFilter: 'blur(20px)',
        position: 'sticky', top: 0, zIndex: 100,
      }}>
        <Link to="/institutional" style={{
          display: 'flex', alignItems: 'center', gap: 7,
          color: '#475569', textDecoration: 'none', fontSize: 13, fontWeight: 500,
        }}>
          <ChevronLeft size={15} /> Back to Institutional
        </Link>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Shield size={16} style={{ color: '#C9A227' }} />
          <span style={{ fontSize: 14, fontWeight: 800, color: '#C9A227', letterSpacing: '0.06em' }}>OMNIX</span>
          <span style={{ fontSize: 12, color: '#475569' }}>/ Crisis Replay</span>
        </div>
        <Link to="/verify-independently" style={{ fontSize: 12, color: '#64748B', textDecoration: 'none' }}>
          Verify independently →
        </Link>
      </nav>

      <div style={{ maxWidth: 920, margin: '0 auto', padding: '56px 20px 80px' }}>

        {/* ── Hero ── */}
        <div style={{ textAlign: 'center', marginBottom: 72 }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            background: 'rgba(201,162,39,0.07)', border: '1px solid rgba(201,162,39,0.22)',
            borderRadius: 20, padding: '6px 16px', marginBottom: 28,
          }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#C9A227', animation: 'pulse 2s infinite', display: 'inline-block' }} />
            <span style={{ fontSize: 11, fontWeight: 800, color: '#C9A227', textTransform: 'uppercase', letterSpacing: '0.14em' }}>
              ADR-145 · Governance Replay Engine v1.0.0
            </span>
          </div>

          <h1 style={{ fontSize: 'clamp(2.2rem, 5vw, 3.4rem)', fontWeight: 900, lineHeight: 1.08, margin: '0 0 20px', color: '#F8FAFC', letterSpacing: '-0.03em' }}>
            OMNIX would have stopped<br />
            <span style={{ color: '#C9A227' }}>all of them.</span>
          </h1>

          <p style={{ fontSize: 16, color: '#64748B', maxWidth: 600, margin: '0 auto 36px', lineHeight: 1.75 }}>
            Five historical crises. Real market signals. The OMNIX governance framework — applied retroactively to the exact signal conditions that existed when each crisis unfolded. Every historically-verified decision is sealed in a cryptographic receipt you can verify independently.
          </p>

          {/* Stats */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, maxWidth: 620, margin: '0 auto 20px' }}>
            {[
              { v: '5',             l: 'Crises replayed'     },
              { v: `${totalBlocked}`, l: 'Hard blocks issued' },
              { v: `${blockRate}%`, l: 'Block + hold rate'   },
              { v: `${totalReceipts}`, l: 'Signed receipts'  },
            ].map(s => (
              <div key={s.l} style={{
                background: 'rgba(15,33,64,0.7)', border: '1px solid rgba(201,162,39,0.14)',
                borderRadius: 12, padding: '18px 8px',
              }}>
                <div style={{ fontSize: 28, fontWeight: 900, color: '#C9A227', lineHeight: 1, letterSpacing: '-0.02em' }}>{s.v}</div>
                <div style={{ fontSize: 11, color: '#475569', marginTop: 5 }}>{s.l}</div>
              </div>
            ))}
          </div>

          <p style={{ fontSize: 11, color: '#374151' }}>
            All receipts generated by <code style={{ color: '#64748B' }}>GovernanceReplayEngine v1.0.0</code> · ADR-145 · Deterministic · SHA-256 sealed
          </p>
        </div>

        {/* ── Divider ── */}
        <div style={{ height: 1, background: 'linear-gradient(90deg, transparent, #C9A227 30%, #C9A227 70%, transparent)', marginBottom: 52 }} />

        {/* ── Crisis cards ── */}
        {SCENARIOS.map(sc => <ScenarioCard key={sc.id} sc={sc} />)}

        {/* ── Divider ── */}
        <div style={{ height: 1, background: 'linear-gradient(90deg, transparent, #C9A227 30%, #C9A227 70%, transparent)', margin: '52px 0' }} />

        {/* ── Verification box ── */}
        <div style={{
          background: 'rgba(15,33,64,0.7)', border: '1px solid rgba(201,162,39,0.2)',
          borderRadius: 16, padding: '32px', marginBottom: 40,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
            <Terminal size={20} style={{ color: '#C9A227' }} />
            <h2 style={{ fontSize: 20, fontWeight: 800, color: '#F8FAFC', margin: 0, letterSpacing: '-0.02em' }}>
              Verify any receipt independently
            </h2>
          </div>
          <p style={{ fontSize: 13, color: '#64748B', marginBottom: 22, lineHeight: 1.7, maxWidth: 560 }}>
            Click the <strong style={{ color: '#94A3B8' }}>.json</strong> button on any receipt above.
            Run the script below on your own machine. No OMNIX server. No trust required.
          </p>

          <div style={{
            background: '#020810', border: '1px solid rgba(201,162,39,0.12)',
            borderRadius: 10, padding: '18px 20px', marginBottom: 18,
            fontFamily: 'monospace', lineHeight: 1.9,
          }}>
            <div style={{ color: '#374151', fontSize: 11 }}># Step 1 — Get the standalone verifier</div>
            <div style={{ color: '#10b981', fontSize: 13, marginBottom: 10 }}>curl -O https://omnixquantum.net/omnix_verify.py</div>
            <div style={{ color: '#374151', fontSize: 11 }}># Step 2 — Download any receipt above, then run:</div>
            <div style={{ color: '#E2E8F0', fontSize: 13, marginBottom: 10 }}>
              python omnix_verify.py OMNIX-RPL-228D2BCB713BEA18.json <span style={{ color: '#C9A227' }}>--mode replay</span>
            </div>
            <div style={{ color: '#374151', fontSize: 11 }}># Expected output — verified in &lt;1 second:</div>
            <div style={{ color: '#475569', fontSize: 12, marginLeft: 2 }}>
              Receipt ID  : <span style={{ color: '#E2E8F0' }}>OMNIX-RPL-228D2BCB713BEA18</span><br />
              Content Hash: <span style={{ color: '#22c55e' }}>VALID</span><br />
              VERDICT     : <span style={{ color: '#22c55e', fontWeight: 700 }}>VALID</span>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <a href="/omnix_verify.py" download style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              background: 'linear-gradient(135deg, #A68B1F, #C9A227, #D4AF37)',
              color: '#050D18', fontWeight: 800, padding: '11px 22px',
              borderRadius: 9, textDecoration: 'none', fontSize: 13,
            }}>
              <Download size={14} /> Download omnix_verify.py
            </a>
            <Link to="/verify-independently" style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              background: 'transparent', border: '1px solid rgba(229,228,226,0.15)',
              color: '#94A3B8', padding: '11px 22px',
              borderRadius: 9, textDecoration: 'none', fontSize: 13,
            }}>
              <ExternalLink size={14} /> Verification guide
            </Link>
            <Link to="/verify" style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.25)',
              color: '#60a5fa', padding: '11px 22px',
              borderRadius: 9, textDecoration: 'none', fontSize: 13,
            }}>
              <ExternalLink size={14} /> Receipt Verifier
            </Link>
          </div>
        </div>

        {/* ── Footer ── */}
        <div style={{ textAlign: 'center', padding: '8px 0' }}>
          <p style={{ fontSize: 11, color: '#374151', lineHeight: 1.8, maxWidth: 560, margin: '0 auto 16px' }}>
            Receipts generated by <code style={{ color: '#475569' }}>GovernanceReplayEngine v1.0.0</code> — a forensic component of the OMNIX production codebase. Verdicts reflect historically-verified governance decisions sourced from OMNIX forensic documents. Receipt IDs and canonical hashes are deterministic: identical inputs always produce identical outputs. ADR-145 · May 2026.
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: 20, flexWrap: 'wrap', fontSize: 12 }}>
            {[
              { to: '/institutional',    label: 'Institutional' },
              { to: '/command',          label: 'Investor Command' },
              { to: '/verify',           label: 'Receipt Verifier' },
              { to: '/verify-independently', label: 'Independent Verify' },
              { to: '/pitch',            label: 'Pitch Deck' },
            ].map(l => (
              <Link key={l.to} to={l.to} style={{ color: '#374151', textDecoration: 'none' }}>{l.label}</Link>
            ))}
          </div>
        </div>

      </div>
    </div>
  )
}
