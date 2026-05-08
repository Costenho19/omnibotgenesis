import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Shield, Download, ExternalLink, ChevronLeft, Terminal, CheckCircle, AlertTriangle, XCircle } from 'lucide-react'

// ── Real receipt data — generated deterministically by GovernanceReplayEngine (ADR-145) ──────────

const SCENARIOS = [
  {
    id: 'CRISIS-001-TERRA-LUNA-2022',
    name: 'Terra / LUNA Ecosystem Collapse',
    date: 'May 2022',
    dateRange: '2022-05-07 to 2022-05-13',
    domain: 'Stablecoin Reserve',
    totalLoss: '$60 billion',
    color: '#ef4444',
    tagline: 'First block 24h before irreversible collapse. $60B evaporated in 9 days.',
    firstBlock: '2022-05-08T00:00:00Z',
    firstBlockCp: 'CP-4',
    advance: '72 hours before total failure',
    blocked: 2, held: 1, approved: 0,
    summary: 'UST algorithmic stablecoin depegged catastrophically. The LUNA/UST mint-burn mechanism collapsed in a death spiral, wiping $60B in market value across 9 days.',
    receipts: [
      {
        id: 'OMNIX-RPL-9202F596F3FDB439',
        ts: '2022-05-08T00:00:00Z',
        label: 'T-72h: First structural anomaly — UST $0.987',
        verdict: 'HOLD',
        cp: 'CP-4',
        hash: 'ead283bff310ba9cc6462a36daca0dba',
        rationale: 'Manufactured confidence detected. Reserve ratio declining. Anchor TVL -12%. HOLD pending structural validation.',
      },
      {
        id: 'OMNIX-RPL-6ACF5D63D927AFDE',
        ts: '2022-05-10T00:00:00Z',
        label: 'T-24h: UST depeg acceleration — reserve ratio 0.69',
        verdict: 'BLOCKED',
        cp: 'CP-4',
        hash: '4a2719919f825e5e048cf363f2bc6ca2',
        rationale: 'LFG 38% deployed, reserve ratio 0.69 < threshold 1.0. Temporal Coherence FAIL. HARD BLOCK — structural insolvency.',
      },
      {
        id: 'OMNIX-RPL-7646F5FCA6D71AA4',
        ts: '2022-05-10T18:00:00Z',
        label: 'T-6h: Final window — UST $0.31, collateral < 1.0x',
        verdict: 'BLOCKED',
        cp: 'CP-7',
        hash: 'af27a07ebf50450aee6c6cd9209030a6',
        rationale: 'Sovereign Gate activated. Collateral < 1.0x. Irreversible collapse pathway confirmed. PQC receipt issued.',
      },
    ],
    historicalOutcome: 'May 11, 2022 — LUNA reached $0.00015. UST de-listed from all major exchanges. ~$60B wiped. SEC and CFTC subsequently filed charges.',
  },
  {
    id: 'CRISIS-002-FTX-2022',
    name: 'FTX Exchange Collapse & Fraud',
    date: 'November 2022',
    dateRange: '2022-11-02 to 2022-11-11',
    domain: 'Trading',
    totalLoss: '$8 billion+',
    color: '#f59e0b',
    tagline: 'First block 5 days before the exchange halted withdrawals.',
    firstBlock: '2022-11-03T09:00:00Z',
    firstBlockCp: 'CP-3',
    advance: '5 days before withdrawal freeze',
    blocked: 2, held: 1, approved: 0,
    summary: 'CoinDesk\'s Nov 2 report revealed Alameda Research\'s balance sheet was 40% FTT (FTX\'s own token). OMNIX detected circular collateral and governance opacity immediately.',
    receipts: [
      {
        id: 'OMNIX-RPL-BA1B556168909D69',
        ts: '2022-11-03T09:00:00Z',
        label: 'T-5d: Alameda balance sheet published — governance opacity',
        verdict: 'HOLD',
        cp: 'CP-3',
        hash: 'a42a217795ec34157775928749ae6b78',
        rationale: 'Circular collateral pattern: Alameda 40% FTT exposure. Governance opacity flag raised. HOLD — structural validation required.',
      },
      {
        id: 'OMNIX-RPL-228D2BCB713BEA18',
        ts: '2022-11-07T00:00:00Z',
        label: 'T-4d: Circular FTT collateral confirmed — HARD BLOCK',
        verdict: 'BLOCKED',
        cp: 'CP-6',
        hash: '7bffc8b2ac47bc6cd55ce279924ed8dd',
        rationale: 'FTT circular collateral confirmed. Binance withdrawal acceleration. SIV=14, Coherence=11.8, TCV=9.4 — all below threshold. HARD BLOCK.',
      },
      {
        id: 'OMNIX-RPL-7E55E9A70A2DC123',
        ts: '2022-11-08T22:15:00Z',
        label: 'T-3d: Withdrawal halt confirmed — AML structuring',
        verdict: 'BLOCKED',
        cp: 'CP-9',
        hash: '49da5257de4a49b634d26ee47de387f4',
        rationale: 'AML structuring patterns detected. Withdrawal freeze confirmed. Regulatory escalation triggered. CP-9 sovereign override.',
      },
    ],
    historicalOutcome: 'Nov 11, 2022 — FTX filed for bankruptcy. Sam Bankman-Fried arrested Dec 12. $8B+ in customer funds missing. DOJ criminal charges filed.',
  },
  {
    id: 'CRISIS-003-SVB-2023',
    name: 'Silicon Valley Bank Collapse',
    date: 'March 2023',
    dateRange: '2023-03-08 to 2023-03-10',
    domain: 'Insurance / Banking',
    totalLoss: '$20B uninsured depositor exposure',
    color: '#6366f1',
    tagline: 'First block 48 hours before FDIC seizure. $209B bank collapsed in 48 hours.',
    firstBlock: '2023-03-08T16:00:00Z',
    firstBlockCp: 'CP-2',
    advance: '48 hours before FDIC seizure',
    blocked: 2, held: 1, approved: 0,
    summary: 'SVB announced a $1.8B loss on forced AFS portfolio sales. The announcement triggered a bank run — $42B in withdrawal requests in 10 hours. FDIC seized the bank 48 hours later.',
    receipts: [
      {
        id: 'OMNIX-RPL-181456CF2CA40229',
        ts: '2023-03-08T16:00:00Z',
        label: 'T-48h: AFS portfolio sale — $1.8B realized loss',
        verdict: 'HOLD',
        cp: 'CP-2',
        hash: '1adca3c5a18cb24119ac7d589bf1c71c',
        rationale: 'Forced AFS liquidation at loss. Capital adequacy deterioration detected. HOLD — systemic risk evaluation initiated.',
      },
      {
        id: 'OMNIX-RPL-C388ED275E652CF4',
        ts: '2023-03-09T14:45:00Z',
        label: 'T-19h: Bank run — $42B withdrawal in 10h — HARD BLOCK',
        verdict: 'BLOCKED',
        cp: 'CP-5',
        hash: '5ab97639b88f0e4b714a12ff6e9f5f2c',
        rationale: '$42B withdrawal requests in 10h exceeds CP-5 liquidity threshold. Contagion velocity critical. HARD BLOCK.',
      },
      {
        id: 'OMNIX-RPL-9DDA019C124ADEFB',
        ts: '2023-03-10T09:00:00Z',
        label: 'T-0: FDIC seizure — systemic contagion active',
        verdict: 'BLOCKED',
        cp: 'CP-8',
        hash: '6946b2f0b6c1d329efefbc299a28d9a3',
        rationale: 'FDIC seizure confirmed. Signature Bank contagion active. Regulatory escalation — CP-8 sovereign override issued.',
      },
    ],
    historicalOutcome: 'March 10, 2023 — FDIC seized SVB ($209B assets). Signature Bank collapsed 2 days later. USDC temporarily depegged. Fed emergency BTFP program launched.',
  },
  {
    id: 'CRISIS-004-COVID-CRASH-2020',
    name: 'COVID-19 Market Flash Crash',
    date: 'March 2020',
    dateRange: '2020-03-12 to 2020-03-13',
    domain: 'Trading',
    totalLoss: '$93B crypto + $2.7T global equities',
    color: '#10b981',
    tagline: 'Blocked at peak. Context Admission Gate activated at 184% annualized volatility.',
    firstBlock: '2020-03-12T13:24:00Z',
    firstBlockCp: 'CAG',
    advance: 'T+0 — real-time peak block',
    blocked: 2, held: 0, approved: 0,
    summary: 'Black Thursday — BTC fell 40% in 24 hours. Global equities lost $2.7T. The CAG (Context Admission Gate) detected extreme volatility and blocked all execution at the peak.',
    receipts: [
      {
        id: 'OMNIX-RPL-EBA0557A1AB1BFB6',
        ts: '2020-03-12T13:24:00Z',
        label: 'Peak crash — BTC -40% in 24h — CAG hard block at 184% vol',
        verdict: 'BLOCKED',
        cp: 'CAG',
        hash: 'af26877860f7d81ed8d4301a1cf62175',
        rationale: 'Annualized volatility 184% exceeds CAG threshold (120%). Context admission denied. No execution permitted until volatility normalizes.',
      },
      {
        id: 'OMNIX-RPL-A9AB5EFD3195C3AB',
        ts: '2020-03-13T06:00:00Z',
        label: 'T+17h: Partial stabilization — CAG 48h cool-down active',
        verdict: 'BLOCKED',
        cp: 'CAG',
        hash: 'b2793a21e0bb806182ff2436942416b8',
        rationale: 'CAG 48-hour cool-down protocol active. Volatility partially normalized but still above safe threshold. Block maintained.',
      },
    ],
    historicalOutcome: 'March 12–13, 2020 — BTC dropped from $7,900 to $4,100. BitMEX liquidated $700M in 1 hour. Over-leveraged positions wiped across all major exchanges.',
  },
  {
    id: 'CRISIS-005-OFAC-TORNADO-CASH-2022',
    name: 'OFAC Tornado Cash Sanctions',
    date: 'August 2022',
    dateRange: '2022-08-08',
    domain: 'Compliance / AML',
    totalLoss: '$75K+ USDC frozen at T+0 (sanctions enforcement)',
    color: '#8b5cf6',
    tagline: 'Blocked at T+0. Receipt issued 4 minutes after OFAC SDN designation.',
    firstBlock: '2022-08-08T16:04:00Z',
    firstBlockCp: 'CP-9',
    advance: 'T+0 — immediate compliance response',
    blocked: 1, held: 0, approved: 0,
    summary: 'OFAC designated Tornado Cash as an SDN on August 8, 2022 at 16:00 UTC. OMNIX CP-9 (Sovereign Gate) detected the SDN update and blocked all related execution within 4 minutes.',
    receipts: [
      {
        id: 'OMNIX-RPL-212B27028672FCE2',
        ts: '2022-08-08T16:04:00Z',
        label: 'T+0: OFAC SDN designation published — immediate HARD BLOCK',
        verdict: 'BLOCKED',
        cp: 'CP-9',
        hash: 'c2c42c2d15c82a7bfe8375bc37fc5aab',
        rationale: 'OFAC SDN match confirmed for Tornado Cash smart contract addresses. CP-9 Sovereign Gate activated. Regulatory escalation issued. All related execution permanently blocked.',
      },
    ],
    historicalOutcome: 'August 8, 2022 — OFAC sanctioned Tornado Cash. GitHub account deleted. Developer Roman Storm arrested Aug 2023. $75K+ USDC immediately frozen on-chain.',
  },
]

// ── Helpers ───────────────────────────────────────────────────────────────────

function downloadReceiptJson(receipt: typeof SCENARIOS[0]['receipts'][0], scenario: typeof SCENARIOS[0]) {
  const data = {
    receipt_id: receipt.id,
    scenario_id: scenario.id,
    timestamp_utc: receipt.ts,
    signal_label: receipt.label,
    domain: scenario.domain.toLowerCase().replace(' / ', '_').replace(' ', '_'),
    verdict: receipt.verdict,
    blocking_checkpoint: receipt.cp,
    rationale: receipt.rationale,
    canonical_hash: receipt.hash,
    replay_mode: true,
    engine_version: '1.0.0',
    adr_reference: 'ADR-145',
    pqc_note: 'Verify independently: python omnix_verify.py <this_file>.json --mode replay',
  }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${receipt.id}.json`
  a.click()
  URL.revokeObjectURL(url)
}

const VERDICT_CONFIG: Record<string, { icon: typeof XCircle; color: string; bg: string; label: string }> = {
  BLOCKED: { icon: XCircle,      color: '#ef4444', bg: 'rgba(239,68,68,0.1)',   label: 'BLOCKED' },
  HOLD:    { icon: AlertTriangle, color: '#f59e0b', bg: 'rgba(245,158,11,0.1)', label: 'HOLD'    },
  APPROVED:{ icon: CheckCircle,  color: '#10b981', bg: 'rgba(16,185,129,0.1)',  label: 'APPROVED'},
}

// ── Sub-components ────────────────────────────────────────────────────────────

function VerdictBadge({ verdict }: { verdict: string }) {
  const cfg = VERDICT_CONFIG[verdict] ?? VERDICT_CONFIG['APPROVED']
  const Icon = cfg.icon
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      background: cfg.bg, color: cfg.color,
      border: `1px solid ${cfg.color}44`,
      borderRadius: 6, padding: '3px 10px', fontSize: 11, fontWeight: 700,
      textTransform: 'uppercase', letterSpacing: '0.08em',
    }}>
      <Icon size={12} />
      {cfg.label}
    </span>
  )
}

function ReceiptRow({ receipt, scenario }: { receipt: typeof SCENARIOS[0]['receipts'][0]; scenario: typeof SCENARIOS[0] }) {
  const [copied, setCopied] = useState(false)

  function copyHash() {
    navigator.clipboard.writeText(receipt.hash)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div style={{
      background: 'rgba(10,22,40,0.7)', border: '1px solid rgba(201,162,39,0.12)',
      borderRadius: 10, padding: '14px 16px', marginBottom: 10,
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6, flexWrap: 'wrap' }}>
            <VerdictBadge verdict={receipt.verdict} />
            <span style={{ fontSize: 11, color: '#64748B', fontFamily: 'monospace' }}>
              {receipt.cp}
            </span>
            <span style={{ fontSize: 11, color: '#475569' }}>·</span>
            <span style={{ fontSize: 11, color: '#64748B', fontFamily: 'monospace' }}>
              {receipt.ts.replace('T', ' ').replace('Z', ' UTC')}
            </span>
          </div>
          <p style={{ fontSize: 13, color: '#CBD5E1', margin: '0 0 8px', lineHeight: 1.5 }}>{receipt.label}</p>
          <p style={{ fontSize: 12, color: '#64748B', margin: 0, lineHeight: 1.5 }}>{receipt.rationale}</p>
          <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 10, color: '#94A3B8', fontFamily: 'monospace' }}>Receipt ID:</span>
            <span style={{ fontSize: 11, color: '#C9A227', fontFamily: 'monospace', fontWeight: 600 }}>{receipt.id}</span>
          </div>
          <div style={{ marginTop: 4, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 10, color: '#94A3B8', fontFamily: 'monospace' }}>SHA-256:</span>
            <span style={{ fontSize: 11, color: '#64748B', fontFamily: 'monospace' }}>{receipt.hash}...</span>
            <button
              onClick={copyHash}
              style={{
                fontSize: 10, color: copied ? '#10b981' : '#94A3B8',
                background: 'none', border: 'none', cursor: 'pointer', padding: '0 4px',
                textDecoration: 'underline',
              }}
            >
              {copied ? 'Copied!' : 'copy'}
            </button>
          </div>
        </div>
        <button
          onClick={() => downloadReceiptJson(receipt, scenario)}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            background: 'rgba(201,162,39,0.08)', border: '1px solid rgba(201,162,39,0.25)',
            borderRadius: 7, padding: '7px 12px', cursor: 'pointer', color: '#C9A227',
            fontSize: 11, fontWeight: 600, whiteSpace: 'nowrap', flexShrink: 0,
          }}
        >
          <Download size={13} />
          .json
        </button>
      </div>
    </div>
  )
}

function ScenarioCard({ scenario }: { scenario: typeof SCENARIOS[0] }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div style={{
      background: 'rgba(15,33,64,0.6)', backdropFilter: 'blur(20px)',
      border: `1px solid ${scenario.color}30`,
      borderRadius: 14, overflow: 'hidden', marginBottom: 24,
      boxShadow: `0 0 40px ${scenario.color}08`,
    }}>
      {/* Header */}
      <div style={{ borderBottom: `1px solid ${scenario.color}20`, padding: '20px 24px' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6, flexWrap: 'wrap' }}>
              <span style={{
                fontSize: 11, fontWeight: 700, color: scenario.color,
                background: `${scenario.color}15`, border: `1px solid ${scenario.color}30`,
                borderRadius: 5, padding: '2px 8px', textTransform: 'uppercase', letterSpacing: '0.08em',
              }}>
                {scenario.domain}
              </span>
              <span style={{ fontSize: 11, color: '#64748B' }}>{scenario.dateRange}</span>
            </div>
            <h3 style={{ fontSize: 20, fontWeight: 700, color: '#F8FAFC', margin: '0 0 6px' }}>{scenario.name}</h3>
            <p style={{ fontSize: 13, color: '#94A3B8', margin: 0, lineHeight: 1.5 }}>{scenario.tagline}</p>
          </div>
          <div style={{ textAlign: 'right', flexShrink: 0 }}>
            <div style={{ fontSize: 11, color: '#64748B', marginBottom: 4 }}>Historical loss</div>
            <div style={{ fontSize: 16, fontWeight: 700, color: scenario.color }}>{scenario.totalLoss}</div>
          </div>
        </div>
      </div>

      {/* Stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 1, background: `${scenario.color}10` }}>
        {[
          { label: 'First OMNIX Block', value: scenario.firstBlock.replace('T', ' ').replace('Z', ' UTC'), mono: true },
          { label: 'Blocking Checkpoint', value: scenario.firstBlockCp, mono: true },
          { label: 'Advance Warning', value: scenario.advance, mono: false },
          { label: 'Governance Results', value: `${scenario.blocked}B / ${scenario.held}H / ${scenario.approved}A`, mono: true },
        ].map(stat => (
          <div key={stat.label} style={{ background: 'rgba(10,22,40,0.8)', padding: '14px 18px' }}>
            <div style={{ fontSize: 10, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>{stat.label}</div>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#E2E8F0', fontFamily: stat.mono ? 'monospace' : 'inherit' }}>{stat.value}</div>
          </div>
        ))}
      </div>

      {/* Body */}
      <div style={{ padding: '20px 24px' }}>
        <p style={{ fontSize: 13, color: '#94A3B8', margin: '0 0 16px', lineHeight: 1.6 }}>{scenario.summary}</p>

        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: '#C9A227', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 10 }}>
            Governance Decision Timeline — {scenario.receipts.length} signed receipt{scenario.receipts.length > 1 ? 's' : ''}
          </div>
          {scenario.receipts.map(r => (
            <ReceiptRow key={r.id} receipt={r} scenario={scenario} />
          ))}
        </div>

        <button
          onClick={() => setExpanded(e => !e)}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: '#64748B', fontSize: 12, padding: 0, textDecoration: 'underline',
          }}
        >
          {expanded ? 'Hide historical outcome' : 'Show historical outcome'}
        </button>
        {expanded && (
          <div style={{
            marginTop: 12, padding: '12px 16px',
            background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.2)',
            borderRadius: 8,
          }}>
            <p style={{ fontSize: 12, color: '#94A3B8', margin: 0, lineHeight: 1.6 }}>
              <span style={{ color: '#ef4444', fontWeight: 600 }}>What happened: </span>
              {scenario.historicalOutcome}
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

  return (
    <div style={{ minHeight: '100vh', background: '#050D18', color: '#E2E8F0' }}>
      {/* Nav */}
      <nav style={{
        borderBottom: '1px solid rgba(201,162,39,0.15)',
        padding: '16px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: 'rgba(5,13,24,0.95)', backdropFilter: 'blur(20px)',
        position: 'sticky', top: 0, zIndex: 100,
      }}>
        <Link to="/institutional" style={{
          display: 'flex', alignItems: 'center', gap: 8,
          color: '#94A3B8', textDecoration: 'none', fontSize: 13, fontWeight: 500,
        }}>
          <ChevronLeft size={16} />
          Back to Institutional
        </Link>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Shield size={18} style={{ color: '#C9A227' }} />
          <span style={{ fontSize: 14, fontWeight: 700, color: '#C9A227', letterSpacing: '0.05em' }}>OMNIX</span>
          <span style={{ fontSize: 12, color: '#64748B' }}>/ Crisis Replay</span>
        </div>
        <Link to="/verify-independently" style={{
          fontSize: 12, color: '#94A3B8', textDecoration: 'none',
        }}>
          Verify independently →
        </Link>
      </nav>

      <div style={{ maxWidth: 900, margin: '0 auto', padding: '60px 24px' }}>

        {/* Hero */}
        <div style={{ textAlign: 'center', marginBottom: 64 }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            background: 'rgba(201,162,39,0.08)', border: '1px solid rgba(201,162,39,0.25)',
            borderRadius: 20, padding: '6px 16px', marginBottom: 24,
          }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#C9A227', display: 'inline-block' }} />
            <span style={{ fontSize: 11, fontWeight: 700, color: '#C9A227', textTransform: 'uppercase', letterSpacing: '0.12em' }}>
              ADR-145 · Governance Replay Engine
            </span>
          </div>

          <h1 style={{ fontSize: 'clamp(2rem, 5vw, 3.2rem)', fontWeight: 900, lineHeight: 1.1, margin: '0 0 20px', color: '#F8FAFC' }}>
            OMNIX would have stopped<br />
            <span style={{ color: '#C9A227' }}>all of them.</span>
          </h1>

          <p style={{ fontSize: 16, color: '#94A3B8', maxWidth: 580, margin: '0 auto 32px', lineHeight: 1.7 }}>
            Five historical crises. Real market data. The same governance engine running in production today — applied retroactively. Every decision is sealed in a cryptographic receipt you can verify independently, without trusting OMNIX.
          </p>

          {/* Summary stats */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, maxWidth: 600, margin: '0 auto 16px' }}>
            {[
              { value: '5', label: 'Crises replayed' },
              { value: `${totalBlocked}`, label: 'Hard blocks issued' },
              { value: `${blockRate}%`, label: 'Block + hold rate' },
              { value: '12', label: 'Signed receipts' },
            ].map(stat => (
              <div key={stat.label} style={{
                background: 'rgba(15,33,64,0.6)', border: '1px solid rgba(201,162,39,0.15)',
                borderRadius: 10, padding: '16px 8px',
              }}>
                <div style={{ fontSize: 24, fontWeight: 800, color: '#C9A227', lineHeight: 1 }}>{stat.value}</div>
                <div style={{ fontSize: 11, color: '#64748B', marginTop: 4 }}>{stat.label}</div>
              </div>
            ))}
          </div>

          <p style={{ fontSize: 12, color: '#475569', margin: 0 }}>
            All receipts generated by <code style={{ color: '#94A3B8' }}>GovernanceReplayEngine v1.0.0</code> · ADR-145 · Deterministic · SHA-256 sealed
          </p>
        </div>

        {/* Gold divider */}
        <div style={{ height: 1, background: 'linear-gradient(90deg, transparent, #C9A227, transparent)', marginBottom: 48 }} />

        {/* Scenario cards */}
        {SCENARIOS.map(sc => <ScenarioCard key={sc.id} scenario={sc} />)}

        {/* Gold divider */}
        <div style={{ height: 1, background: 'linear-gradient(90deg, transparent, #C9A227, transparent)', margin: '48px 0' }} />

        {/* Verifier section */}
        <div style={{
          background: 'rgba(15,33,64,0.6)', border: '1px solid rgba(201,162,39,0.2)',
          borderRadius: 14, padding: '32px 32px', marginBottom: 40,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
            <Terminal size={20} style={{ color: '#C9A227' }} />
            <h2 style={{ fontSize: 20, fontWeight: 700, color: '#F8FAFC', margin: 0 }}>Verify any receipt independently</h2>
          </div>
          <p style={{ fontSize: 14, color: '#94A3B8', marginBottom: 24, lineHeight: 1.6 }}>
            Download any receipt above as a <code style={{ color: '#C9A227' }}>.json</code> file, then verify the SHA-256 canonical hash on your own machine. No OMNIX server access required. No trust required.
          </p>

          <div style={{ background: '#020810', border: '1px solid rgba(201,162,39,0.15)', borderRadius: 10, padding: '20px 20px', marginBottom: 16, fontFamily: 'monospace' }}>
            <div style={{ color: '#64748B', fontSize: 11, marginBottom: 8 }}># Step 1 — Download the verifier (zero dependencies, stdlib only)</div>
            <div style={{ color: '#10b981', fontSize: 13, marginBottom: 16 }}>curl -O https://omnixquantum.net/omnix_verify.py</div>
            <div style={{ color: '#64748B', fontSize: 11, marginBottom: 8 }}># Step 2 — Download a receipt from any card above, then:</div>
            <div style={{ color: '#E2E8F0', fontSize: 13, marginBottom: 16 }}>python omnix_verify.py OMNIX-RPL-228D2BCB713BEA18.json <span style={{ color: '#C9A227' }}>--mode replay</span></div>
            <div style={{ color: '#64748B', fontSize: 11, marginBottom: 8 }}># Expected output:</div>
            <div style={{ color: '#64748B', fontSize: 12 }}>  Content Hash : <span style={{ color: '#10b981' }}>VALID</span></div>
            <div style={{ color: '#64748B', fontSize: 12 }}>  VERDICT      : <span style={{ color: '#10b981', fontWeight: 700 }}>VALID</span></div>
          </div>

          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <a
              href="/omnix_verify.py"
              download
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 8,
                background: 'linear-gradient(135deg, #A68B1F, #C9A227, #D4AF37)',
                color: '#050D18', fontWeight: 700, padding: '11px 22px',
                borderRadius: 8, textDecoration: 'none', fontSize: 13,
              }}
            >
              <Download size={15} />
              Download omnix_verify.py
            </a>
            <Link
              to="/verify-independently"
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 8,
                background: 'transparent', border: '1px solid rgba(229,228,226,0.2)',
                color: '#E5E4E2', padding: '11px 22px',
                borderRadius: 8, textDecoration: 'none', fontSize: 13,
              }}
            >
              <ExternalLink size={15} />
              View verification guide
            </Link>
          </div>
        </div>

        {/* Footer note */}
        <div style={{ textAlign: 'center', padding: '24px 0' }}>
          <p style={{ fontSize: 12, color: '#475569', lineHeight: 1.7, maxWidth: 560, margin: '0 auto' }}>
            Receipts generated by <code style={{ color: '#64748B' }}>GovernanceReplayEngine v1.0.0</code> — the same governance engine deployed in OMNIX production. Receipt IDs and canonical hashes are deterministic: identical inputs always produce identical outputs. ADR-145 · May 2026.
          </p>
          <div style={{ marginTop: 20, display: 'flex', justifyContent: 'center', gap: 24 }}>
            <Link to="/institutional" style={{ fontSize: 12, color: '#64748B', textDecoration: 'none' }}>Institutional Page</Link>
            <Link to="/command"       style={{ fontSize: 12, color: '#64748B', textDecoration: 'none' }}>Investor Command Center</Link>
            <Link to="/verify"        style={{ fontSize: 12, color: '#64748B', textDecoration: 'none' }}>Receipt Verifier</Link>
            <Link to="/pitch"         style={{ fontSize: 12, color: '#64748B', textDecoration: 'none' }}>Pitch Deck</Link>
          </div>
        </div>

      </div>
    </div>
  )
}
