import { useState } from 'react'

const GOLD = '#C9A227'
const NAVY = '#060F1E'
const DARK = '#0A1628'
const CARD = '#0D1B30'
const BORDER = 'rgba(201,162,39,0.18)'
const GREEN = '#22c55e'
const RED = '#ef4444'
const BLUE = '#38bdf8'
const GRAY = '#94a3b8'

interface ChainNode {
  depth: number
  actor_id: string
  actor_type: string
  delegation_id: string | null
  authority_budget: number
  authority_reduction_pct: number
  pqc_signed: boolean
  hash_valid: boolean
  pqc_signature_valid: boolean
  task_scope: Record<string, string>
  created_at: string | null
}

interface SimResult {
  simulation: {
    domain: string
    depth_simulated: number
    agents_created: Array<{ agent_id: string; display_name: string; authority_budget: number }>
    delegations_created: Array<{ delegation_id: string; authority_granted: number; delegation_depth: number }>
  }
  verification: {
    agent_id: string
    fully_verified: boolean
    chain_depth: number
    leaf_budget: number
    mar_valid: boolean
    all_pqc_signed: boolean
    root_actor_id: string
    chain_root_id: string | null
  }
  chain: ChainNode[]
  ccs: {
    atf_ccs: number
    atf_ccs_verdict: string
    components: Record<string, number>
    mar_valid: boolean
  }
  leaf_agent_id: string
  chain_root_id: string
  simulated_at: string
}

function Badge({ label, color, bg }: { label: string; color: string; bg: string }) {
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 10px',
      borderRadius: 12,
      fontSize: 11,
      fontWeight: 700,
      letterSpacing: '0.04em',
      color,
      background: bg,
      border: `1px solid ${color}33`,
    }}>{label}</span>
  )
}

function CCSGauge({ score, verdict }: { score: number; verdict: string }) {
  const color = score >= 90 ? GREEN : score >= 70 ? GOLD : score >= 50 ? '#f97316' : RED
  const pct = Math.min(score, 100)
  return (
    <div style={{ textAlign: 'center' }}>
      <div style={{ position: 'relative', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
        <svg width={120} height={120} viewBox="0 0 120 120">
          <circle cx={60} cy={60} r={50} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={10} />
          <circle
            cx={60} cy={60} r={50}
            fill="none"
            stroke={color}
            strokeWidth={10}
            strokeDasharray={`${2 * Math.PI * 50 * pct / 100} ${2 * Math.PI * 50 * (1 - pct / 100)}`}
            strokeDashoffset={2 * Math.PI * 50 * 0.25}
            strokeLinecap="round"
            style={{ transition: 'stroke-dasharray 0.8s ease' }}
          />
        </svg>
        <div style={{ position: 'absolute', textAlign: 'center' }}>
          <div style={{ fontSize: 26, fontWeight: 800, color, fontFamily: 'monospace' }}>{score}</div>
          <div style={{ fontSize: 10, color: GRAY, fontWeight: 600 }}>/ 100</div>
        </div>
      </div>
      <div style={{ marginTop: 6, fontWeight: 700, fontSize: 13, color, letterSpacing: '0.08em' }}>{verdict}</div>
    </div>
  )
}

function ChainViz({ chain }: { chain: ChainNode[] }) {
  if (!chain.length) return null
  const actors = [
    { id: 'HUMAN-TIER1', label: 'Human Operator', type: 'human', budget: 100 },
    ...chain.map(n => ({
      id: n.actor_id,
      label: n.actor_type === 'human_operator' ? 'Human Operator' : `Agent (Depth ${n.depth})`,
      type: n.actor_type,
      budget: n.authority_budget,
      node: n,
    }))
  ]
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0 }}>
      {actors.map((actor, i) => (
        <div key={actor.id + i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <div style={{
            background: actor.type === 'human_operator' || actor.type === 'human'
              ? `linear-gradient(135deg, ${GOLD}22, ${GOLD}08)` : CARD,
            border: `1.5px solid ${actor.type === 'human_operator' || actor.type === 'human' ? GOLD : BORDER}`,
            borderRadius: 12,
            padding: '12px 24px',
            minWidth: 260,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 16,
          }}>
            <div>
              <div style={{ fontSize: 11, color: GRAY, marginBottom: 2 }}>
                {actor.type === 'human' || actor.type === 'human_operator' ? 'HUMAN ORIGIN' : `DEPTH ${(actor as any).node?.depth || 0}`}
              </div>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#e2e8f0', fontFamily: 'monospace' }}>
                {actor.id.length > 28 ? actor.id.slice(0, 12) + '…' + actor.id.slice(-8) : actor.id}
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 11, color: GRAY }}>Authority Budget</div>
              <div style={{ fontSize: 18, fontWeight: 800, color: GOLD }}>{actor.budget}</div>
            </div>
          </div>
          {i < actors.length - 1 && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '2px 0' }}>
              <div style={{ width: 2, height: 14, background: `linear-gradient(${GOLD}, ${GOLD}44)` }} />
              <div style={{ fontSize: 9, color: GOLD, fontWeight: 700, letterSpacing: '0.06em', padding: '2px 8px',
                background: `${GOLD}14`, borderRadius: 6, border: `1px solid ${GOLD}33` }}>
                PQC DELEGATION ▼
              </div>
              <div style={{ width: 2, height: 14, background: `linear-gradient(${GOLD}44, ${GOLD})` }} />
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

export default function AgentTrustFabricPage() {
  const [domain, setDomain] = useState('FINANCE')
  const [depth, setDepth] = useState(3)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<SimResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'chain' | 'receipts' | 'ccs'>('chain')

  const simulate = async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await fetch('/api/atf/demo/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain, depth }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Simulation failed')
      setResult(data)
      setActiveTab('chain')
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ background: NAVY, minHeight: '100vh', fontFamily: "'Inter', sans-serif", color: '#e2e8f0' }}>

      {/* Nav */}
      <div style={{ borderBottom: `1px solid ${BORDER}`, padding: '16px 32px', display: 'flex', alignItems: 'center', gap: 20 }}>
        <a href="/" style={{ color: GOLD, textDecoration: 'none', fontSize: 13, fontWeight: 700, letterSpacing: '0.1em' }}>
          ← OMNIX QUANTUM
        </a>
        <span style={{ color: BORDER, fontSize: 13 }}>|</span>
        <span style={{ fontSize: 13, color: GRAY }}>Agent Trust Fabric — ADR-156</span>
      </div>

      {/* Hero */}
      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '60px 32px 40px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20 }}>
          <div style={{ background: `${GOLD}18`, border: `1px solid ${GOLD}44`, borderRadius: 8, padding: '4px 14px',
            fontSize: 11, fontWeight: 700, color: GOLD, letterSpacing: '0.12em' }}>
            ADR-156 · MAY 2026
          </div>
          <div style={{ background: `${GREEN}18`, border: `1px solid ${GREEN}44`, borderRadius: 8, padding: '4px 14px',
            fontSize: 11, fontWeight: 700, color: GREEN, letterSpacing: '0.12em' }}>
            LIVE
          </div>
        </div>

        <h1 style={{ fontSize: 42, fontWeight: 900, margin: '0 0 16px', lineHeight: 1.1,
          background: `linear-gradient(135deg, #fff 60%, ${GOLD})`, WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent' }}>
          Agent Trust Fabric
        </h1>
        <p style={{ fontSize: 18, color: GRAY, maxWidth: 680, margin: '0 0 12px', lineHeight: 1.6 }}>
          The world's first post-quantum cryptographic infrastructure for agent-to-agent
          authority delegation. Every AI agent action is traceable to its human origin
          with a verifiable, independently auditable chain of signed delegation receipts.
        </p>

        {/* Problem statement */}
        <div style={{ background: `${RED}08`, border: `1px solid ${RED}22`, borderRadius: 12, padding: '16px 24px',
          marginTop: 28, marginBottom: 40, maxWidth: 700 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: RED, letterSpacing: '0.1em', marginBottom: 8 }}>
            THE PROBLEM NO ONE HAS SOLVED
          </div>
          <p style={{ margin: 0, fontSize: 14, color: '#cbd5e1', lineHeight: 1.7 }}>
            Every AI agent framework today (LangChain, AutoGen, CrewAI) delegates authority
            implicitly — through environment variables, API keys, or runtime role assignments.
            These are not signed by the delegator, not independently verifiable, and not
            traceable back to a human origin. When something goes wrong, there is no
            cryptographic proof of who authorized what.
          </p>
        </div>

        {/* Differentiators grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16, marginBottom: 56 }}>
          {[
            {
              icon: '🔗',
              title: 'Cryptographic Delegation',
              desc: 'Every delegation event produces a Dilithium-3 (ML-DSA-65) signed receipt. The delegator cannot deny it. The chain is unforgeable.',
            },
            {
              icon: '📉',
              title: 'Monotonic Authority Reduction',
              desc: 'Authority budget can only decrease through delegation — never increase. Privilege escalation is impossible at the protocol level.',
            },
            {
              icon: '🔍',
              title: 'Independent Verification',
              desc: 'Any regulator or auditor can verify the full delegation chain with zero platform access. The delegator\'s public key is embedded in every receipt.',
            },
            {
              icon: '🌐',
              title: 'Human Root Traceability',
              desc: 'Every autonomous agent action traces cryptographically back to its authorizing human (Tier-1 operator) — satisfying EU AI Act Art. 14.',
            },
          ].map((item) => (
            <div key={item.title} style={{ background: CARD, border: `1px solid ${BORDER}`, borderRadius: 14, padding: 24 }}>
              <div style={{ fontSize: 28, marginBottom: 12 }}>{item.icon}</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: GOLD, marginBottom: 8 }}>{item.title}</div>
              <p style={{ margin: 0, fontSize: 13, color: GRAY, lineHeight: 1.6 }}>{item.desc}</p>
            </div>
          ))}
        </div>

        {/* Live Demo */}
        <div style={{ background: CARD, border: `1px solid ${BORDER}`, borderRadius: 18, padding: 36, marginBottom: 48 }}>
          <h2 style={{ margin: '0 0 6px', fontSize: 22, fontWeight: 800, color: '#fff' }}>
            Live Delegation Chain Simulator
          </h2>
          <p style={{ margin: '0 0 28px', fontSize: 13, color: GRAY }}>
            Simulate a real multi-agent delegation chain with PQC-signed receipts and full chain verification.
          </p>

          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 24 }}>
            <div>
              <label style={{ display: 'block', fontSize: 11, color: GOLD, fontWeight: 700,
                letterSpacing: '0.1em', marginBottom: 6 }}>GOVERNANCE DOMAIN</label>
              <select
                value={domain}
                onChange={e => setDomain(e.target.value)}
                style={{ background: DARK, border: `1px solid ${BORDER}`, borderRadius: 8, color: '#e2e8f0',
                  padding: '10px 16px', fontSize: 14, cursor: 'pointer', minWidth: 180 }}
              >
                {['FINANCE', 'HEALTHCARE', 'DEFENSE', 'ENERGY', 'INSURANCE'].map(d => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 11, color: GOLD, fontWeight: 700,
                letterSpacing: '0.1em', marginBottom: 6 }}>CHAIN DEPTH</label>
              <select
                value={depth}
                onChange={e => setDepth(Number(e.target.value))}
                style={{ background: DARK, border: `1px solid ${BORDER}`, borderRadius: 8, color: '#e2e8f0',
                  padding: '10px 16px', fontSize: 14, cursor: 'pointer', minWidth: 180 }}
              >
                <option value={1}>1 Level — Orchestrator</option>
                <option value={2}>2 Levels — + Analysis Agent</option>
                <option value={3}>3 Levels — + Data Agent</option>
              </select>
            </div>
            <div style={{ display: 'flex', alignItems: 'flex-end' }}>
              <button
                onClick={simulate}
                disabled={loading}
                style={{
                  background: loading ? `${GOLD}44` : `linear-gradient(135deg, ${GOLD}, #a37c19)`,
                  color: loading ? GRAY : '#000',
                  border: 'none', borderRadius: 10, padding: '10px 28px',
                  fontSize: 14, fontWeight: 800, cursor: loading ? 'not-allowed' : 'pointer',
                  letterSpacing: '0.06em', transition: 'all 0.2s',
                }}
              >
                {loading ? 'GENERATING CHAIN…' : 'SIMULATE CHAIN'}
              </button>
            </div>
          </div>

          {error && (
            <div style={{ background: `${RED}12`, border: `1px solid ${RED}44`, borderRadius: 10,
              padding: '12px 20px', color: RED, fontSize: 13, marginBottom: 20 }}>
              {error}
            </div>
          )}

          {result && (
            <div>
              {/* Summary bar */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                gap: 12, marginBottom: 24 }}>
                {[
                  { label: 'Chain Depth', value: result.verification.chain_depth, color: BLUE },
                  { label: 'Leaf Budget', value: `${result.verification.leaf_budget} / 100`, color: GOLD },
                  { label: 'MAR Valid', value: result.verification.mar_valid ? 'YES' : 'NO',
                    color: result.verification.mar_valid ? GREEN : RED },
                  { label: 'Fully Verified', value: result.verification.fully_verified ? 'YES' : 'NO',
                    color: result.verification.fully_verified ? GREEN : RED },
                  { label: 'PQC Signed', value: result.verification.all_pqc_signed ? 'ALL' : 'PARTIAL',
                    color: result.verification.all_pqc_signed ? GREEN : GOLD },
                ].map(item => (
                  <div key={item.label} style={{ background: DARK, borderRadius: 10,
                    border: `1px solid ${item.color}22`, padding: '12px 16px', textAlign: 'center' }}>
                    <div style={{ fontSize: 11, color: GRAY, marginBottom: 4 }}>{item.label}</div>
                    <div style={{ fontSize: 16, fontWeight: 800, color: item.color }}>{item.value}</div>
                  </div>
                ))}
              </div>

              {/* Tabs */}
              <div style={{ display: 'flex', gap: 4, marginBottom: 20, borderBottom: `1px solid ${BORDER}`, paddingBottom: 0 }}>
                {([['chain', 'Trust Chain'], ['receipts', 'Delegation Receipts'], ['ccs', 'Chain Completeness']] as const).map(([tab, label]) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    style={{
                      background: activeTab === tab ? `${GOLD}18` : 'transparent',
                      border: 'none',
                      borderBottom: activeTab === tab ? `2px solid ${GOLD}` : '2px solid transparent',
                      color: activeTab === tab ? GOLD : GRAY,
                      padding: '8px 20px',
                      fontSize: 13, fontWeight: 700, cursor: 'pointer',
                      letterSpacing: '0.04em',
                    }}
                  >{label}</button>
                ))}
              </div>

              {/* Tab: Chain */}
              {activeTab === 'chain' && (
                <div>
                  <p style={{ fontSize: 12, color: GRAY, marginBottom: 20 }}>
                    Each arrow is a PQC-signed Delegation Receipt. Authority budget decreases monotonically from root to leaf.
                    This chain is independently verifiable — no platform access required.
                  </p>
                  <ChainViz chain={result.chain} />

                  <div style={{ marginTop: 24, background: DARK, borderRadius: 10, padding: 16,
                    border: `1px solid ${BORDER}`, fontSize: 12, fontFamily: 'monospace', color: GRAY }}>
                    <div style={{ color: GOLD, fontWeight: 700, marginBottom: 8 }}>CHAIN ROOT ID</div>
                    <div style={{ wordBreak: 'break-all', color: '#e2e8f0' }}>{result.chain_root_id}</div>
                  </div>
                </div>
              )}

              {/* Tab: Receipts */}
              {activeTab === 'receipts' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {result.simulation.delegations_created.map((dr) => (
                    <div key={dr.delegation_id} style={{ background: DARK, border: `1px solid ${BORDER}`,
                      borderRadius: 12, padding: '16px 20px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 8 }}>
                        <div>
                          <div style={{ fontSize: 11, color: GRAY, marginBottom: 4 }}>
                            DELEGATION RECEIPT · DEPTH {dr.delegation_depth}
                          </div>
                          <div style={{ fontFamily: 'monospace', fontSize: 12, color: GOLD, wordBreak: 'break-all' }}>
                            {dr.delegation_id}
                          </div>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <div style={{ fontSize: 11, color: GRAY }}>Authority Granted</div>
                          <div style={{ fontSize: 20, fontWeight: 800, color: GOLD }}>{dr.authority_granted}</div>
                        </div>
                      </div>
                      <div style={{ marginTop: 12, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                        <Badge label="PQC SIGNED" color={GREEN} bg={`${GREEN}14`} />
                        <Badge label="DILITHIUM-3" color={BLUE} bg={`${BLUE}14`} />
                        <Badge label="HASH VERIFIED" color={GREEN} bg={`${GREEN}14`} />
                        <Badge label={`MAR ENFORCED`} color={GOLD} bg={`${GOLD}14`} />
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Tab: CCS */}
              {activeTab === 'ccs' && (
                <div>
                  <div style={{ display: 'flex', gap: 32, alignItems: 'flex-start', flexWrap: 'wrap' }}>
                    <CCSGauge score={result.ccs.atf_ccs} verdict={result.ccs.atf_ccs_verdict} />
                    <div style={{ flex: 1, minWidth: 240 }}>
                      <div style={{ fontSize: 13, fontWeight: 700, color: GOLD, marginBottom: 12,
                        letterSpacing: '0.08em' }}>ATF CHAIN COMPLETENESS SCORE</div>
                      <p style={{ fontSize: 12, color: GRAY, marginBottom: 16, lineHeight: 1.6 }}>
                        Analogous to the Transparency Chain CCS (ADR-155), the ATF CCS quantifies
                        the integrity of the delegation chain. A fully signed, MAR-compliant chain
                        with verified hashes scores 100.
                      </p>
                      {Object.entries(result.ccs.components).map(([key, val]) => (
                        <div key={key} style={{ marginBottom: 10 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                            <span style={{ fontSize: 12, color: GRAY }}>{key.replace(/_/g, ' ')}</span>
                            <span style={{ fontSize: 12, fontWeight: 700, color: GOLD }}>{val}</span>
                          </div>
                          <div style={{ height: 4, background: 'rgba(255,255,255,0.06)', borderRadius: 4 }}>
                            <div style={{ height: 4, borderRadius: 4, background: GOLD,
                              width: `${(val / 40) * 100}%`, transition: 'width 0.6s ease' }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Protocol spec */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 20, marginBottom: 56 }}>
          <div style={{ background: CARD, border: `1px solid ${BORDER}`, borderRadius: 14, padding: 28 }}>
            <div style={{ fontSize: 13, fontWeight: 800, color: GOLD, marginBottom: 16, letterSpacing: '0.08em' }}>
              ATF INVARIANTS
            </div>
            {[
              ['ATF-INV-001', 'Authority never expands through delegation'],
              ['ATF-INV-002', 'Every receipt is PQC-signed by delegator'],
              ['ATF-INV-003', 'Every chain traces to a root at depth 0'],
              ['ATF-INV-004', 'Delegator cannot grant beyond own budget'],
              ['ATF-INV-005', 'Receipts are immutable once issued'],
              ['ATF-INV-006', 'Verification requires no platform access'],
            ].map(([id, desc]) => (
              <div key={id} style={{ display: 'flex', gap: 12, marginBottom: 12, alignItems: 'flex-start' }}>
                <div style={{ background: `${GREEN}18`, border: `1px solid ${GREEN}33`, borderRadius: 6,
                  padding: '2px 8px', fontSize: 10, fontWeight: 700, color: GREEN, whiteSpace: 'nowrap', marginTop: 1 }}>
                  {id}
                </div>
                <div style={{ fontSize: 13, color: '#cbd5e1', lineHeight: 1.5 }}>{desc}</div>
              </div>
            ))}
          </div>

          <div style={{ background: CARD, border: `1px solid ${BORDER}`, borderRadius: 14, padding: 28 }}>
            <div style={{ fontSize: 13, fontWeight: 800, color: GOLD, marginBottom: 16, letterSpacing: '0.08em' }}>
              REGULATORY ALIGNMENT
            </div>
            {[
              ['EU AI Act Art. 14', 'Human oversight — every chain traces to Tier-1'],
              ['EU AI Act Art. 9', 'AI risk management — MAR invariant enforced'],
              ['NIST AI RMF GV-4.2', 'AI accountability — full chain verifiability'],
              ['OSFI E-23', 'Agent authority documented at issuance'],
              ['ISO/IEC 42001 §8.4', 'Trust lattice as formal governance artifact'],
            ].map(([framework, desc]) => (
              <div key={framework} style={{ marginBottom: 12, paddingBottom: 12,
                borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: BLUE, marginBottom: 2 }}>{framework}</div>
                <div style={{ fontSize: 12, color: GRAY }}>{desc}</div>
              </div>
            ))}
          </div>
        </div>

        {/* API reference */}
        <div style={{ background: CARD, border: `1px solid ${BORDER}`, borderRadius: 14, padding: 28, marginBottom: 56 }}>
          <div style={{ fontSize: 13, fontWeight: 800, color: GOLD, marginBottom: 16, letterSpacing: '0.08em' }}>
            ATF API ENDPOINTS
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 10 }}>
            {[
              ['POST', '/api/atf/agents/register', 'Register a new agent with Dilithium-3 identity'],
              ['POST', '/api/atf/delegate', 'Issue PQC-signed delegation receipt'],
              ['GET', '/api/atf/verify/:agent_id', 'Verify full delegation chain for agent'],
              ['POST', '/api/atf/verify', 'Verify a delegation receipt independently'],
              ['GET', '/api/atf/ccs/:agent_id', 'ATF Chain Completeness Score'],
              ['GET', '/api/atf/lattice', 'Full trust lattice state snapshot'],
              ['GET', '/api/atf/delegations/:agent_id', 'All delegations for an agent'],
              ['POST', '/api/atf/demo/simulate', 'Simulate multi-agent chain (demo)'],
            ].map(([method, path, desc]) => (
              <div key={path} style={{ background: DARK, borderRadius: 8, padding: '10px 14px',
                border: `1px solid ${BORDER}` }}>
                <div style={{ display: 'flex', gap: 8, marginBottom: 4, alignItems: 'center' }}>
                  <span style={{ fontSize: 10, fontWeight: 800, color: method === 'POST' ? GOLD : BLUE,
                    background: `${method === 'POST' ? GOLD : BLUE}18`, borderRadius: 4,
                    padding: '1px 6px', letterSpacing: '0.04em' }}>{method}</span>
                  <code style={{ fontSize: 11, color: '#e2e8f0', fontFamily: 'monospace' }}>{path}</code>
                </div>
                <div style={{ fontSize: 11, color: GRAY }}>{desc}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div style={{ borderTop: `1px solid ${BORDER}`, paddingTop: 32, display: 'flex',
          justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <div style={{ fontSize: 12, color: GOLD, fontWeight: 700, letterSpacing: '0.1em', marginBottom: 4 }}>
              OMNIX QUANTUM — AGENT TRUST FABRIC
            </div>
            <div style={{ fontSize: 12, color: GRAY }}>
              ADR-156 · omnixquantum.net · Harold Nunes
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <a href="/architecture" style={{ color: GRAY, textDecoration: 'none', fontSize: 12 }}>Architecture</a>
            <span style={{ color: BORDER }}>·</span>
            <a href="/security" style={{ color: GRAY, textDecoration: 'none', fontSize: 12 }}>Security</a>
            <span style={{ color: BORDER }}>·</span>
            <a href="/verify" style={{ color: GRAY, textDecoration: 'none', fontSize: 12 }}>Verify</a>
          </div>
        </div>
      </div>
    </div>
  )
}
