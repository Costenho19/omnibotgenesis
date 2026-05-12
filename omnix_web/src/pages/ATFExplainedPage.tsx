const GOLD = '#C9A227'
const NAVY = '#060F1E'
const NAVY2 = '#0A1628'
const BORDER = 'rgba(201,162,39,0.18)'

export default function ATFExplainedPage() {
  return (
    <div style={{ minHeight: '100vh', background: NAVY, color: '#e2e8f0', fontFamily: '"Inter", -apple-system, sans-serif' }}>

      {/* Hero */}
      <div style={{
        textAlign: 'center', padding: '80px 24px 72px',
        background: NAVY2, borderBottom: `1px solid ${BORDER}`,
      }}>
        <div style={{ maxWidth: 680, margin: '0 auto' }}>
          <div style={{
            display: 'inline-block', marginBottom: 28,
            padding: '5px 14px', borderRadius: 20,
            background: 'rgba(201,162,39,0.08)',
            border: `1px solid rgba(201,162,39,0.22)`,
            fontSize: 11, fontWeight: 700, color: GOLD,
            textTransform: 'uppercase', letterSpacing: '0.1em',
          }}>ATF Explained — Plain Language</div>

          <div style={{ fontSize: 38, fontWeight: 800, color: '#f8fafc', lineHeight: 1.2, marginBottom: 28 }}>
            Every AI agent receives mathematically bounded authority
            that can be independently verified before execution.
          </div>

          <div style={{ fontSize: 18, color: '#94a3b8', lineHeight: 1.7 }}>
            That's it. That's what ATF does.
            Here's what each part of that sentence means.
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 820, margin: '0 auto', padding: '64px 24px' }}>

        {/* Sentence breakdown */}
        <div style={{ marginBottom: 72 }}>
          {[
            {
              phrase: '"Every AI agent…"',
              icon: '🤖',
              plain: "Any software system that makes autonomous decisions — trading systems, medical AI, logistics routers, security bots.",
              key: "Not just AI chatbots. Any automated system that takes actions on behalf of an organization.",
            },
            {
              phrase: '"…receives mathematically bounded authority…"',
              icon: '⚖️',
              plain: "Before an agent can act, it receives an explicit permission slip — with a number attached. That number is its authority. It can't be inflated. It can only decrease as it gets passed down.",
              key: "Think of it like a budget. If you're given $60 to spend, you can't give someone else $80. The math makes this impossible — not just against the rules.",
            },
            {
              phrase: '"…that can be independently verified…"',
              icon: '🔍',
              plain: "Any auditor, regulator, or counterparty can check the entire permission chain — using only the documents the system produced. No calls to OMNIX. No API keys. No accounts.",
              key: "Like verifying a notarized signature. You don't need to call the notary to confirm it's real.",
            },
            {
              phrase: '"…before execution."',
              icon: '⏱️',
              plain: "The verification happens — and is recorded — BEFORE the agent runs its decision. Not after. Not during. Before. And that record is signed and timestamped, permanently.",
              key: "This is the part no other system does. You can prove exactly who had what authority at the exact moment a decision was made.",
            },
          ].map((item, i) => (
            <div key={i} style={{
              marginBottom: 32, padding: '28px 32px', borderRadius: 16,
              background: NAVY2, border: `1px solid ${BORDER}`,
            }}>
              <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>
                <div style={{ fontSize: 32, flexShrink: 0 }}>{item.icon}</div>
                <div style={{ flex: 1 }}>
                  <div style={{
                    fontSize: 17, fontWeight: 700, color: GOLD,
                    fontFamily: 'Georgia, serif', fontStyle: 'italic',
                    marginBottom: 12, lineHeight: 1.4,
                  }}>{item.phrase}</div>
                  <div style={{ fontSize: 15, color: '#cbd5e1', lineHeight: 1.7, marginBottom: 12 }}>
                    {item.plain}
                  </div>
                  <div style={{
                    padding: '10px 14px', borderRadius: 8,
                    background: 'rgba(201,162,39,0.05)',
                    border: `1px solid rgba(201,162,39,0.12)`,
                    fontSize: 13, color: '#94a3b8', lineHeight: 1.6,
                    fontStyle: 'italic',
                  }}>
                    {item.key}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Analogy section */}
        <div style={{
          marginBottom: 72, padding: '32px',
          borderRadius: 16, background: NAVY2,
          border: `1px solid ${BORDER}`,
        }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: GOLD, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 12 }}>
            An Analogy
          </div>
          <div style={{ fontSize: 20, fontWeight: 700, color: '#f1f5f9', marginBottom: 20 }}>
            Think of a power of attorney — but for AI
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            {[
              { label: 'Without ATF', color: '239,68,68', items: ['An AI system acts. Nobody knows who authorized it.', 'The audit says "decision approved" — by what, under whose authority?', 'A regulator asks: "was this system allowed to do this?" You search through logs.', 'You find a configuration file from 18 months ago. Nobody signed it.'] },
              { label: 'With ATF', color: '34,197,94', items: ['An AI system acts. A signed record shows who authorized it, when, and under what budget.', 'The audit record contains a verifiable certificate: "this agent had authority 60/100, issued by this human, valid until this date."', 'A regulator asks. You hand them a document and a CLI tool.', 'They verify it offline in 3 seconds. Case closed.'] },
            ].map(col => (
              <div key={col.label} style={{
                padding: '20px', borderRadius: 12,
                background: `rgba(${col.color},0.04)`,
                border: `1px solid rgba(${col.color},0.15)`,
              }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: `rgb(${col.color})`, marginBottom: 12 }}>
                  {col.label}
                </div>
                {col.items.map((item, i) => (
                  <div key={i} style={{ fontSize: 13, color: '#94a3b8', lineHeight: 1.6, marginBottom: 8, paddingLeft: 8, borderLeft: `2px solid rgba(${col.color},0.25)` }}>
                    {item}
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>

        {/* Three documents */}
        <div style={{ marginBottom: 72 }}>
          <div style={{ textAlign: 'center', marginBottom: 32 }}>
            <div style={{ fontSize: 22, fontWeight: 700, color: '#f1f5f9', marginBottom: 8 }}>
              Three documents. One complete answer.
            </div>
            <div style={{ fontSize: 14, color: '#64748b' }}>
              Every OMNIX decision with an AI agent produces exactly these three, linked together.
            </div>
          </div>

          {[
            {
              id: 'ATFDR-8B2C4D6E',
              name: 'Delegation Receipt',
              icon: '📜',
              answers: 'Who authorized this agent, and how much authority did they give it?',
              says: '"Sarah Chen (CFO, Tier-1) authorized this trading agent to act with 60/100 authority, for portfolio risk analysis only, until tomorrow noon."',
              signed: 'Signed by Sarah Chen\'s cryptographic key.',
            },
            {
              id: 'ATFTAR-C4D8E2F1',
              name: 'Temporal Admissibility Record',
              icon: '⏱️',
              answers: 'Was that authority valid at the exact moment the agent executed?',
              says: '"At 14:00:00.000000000 UTC on May 12, 2026, the above delegation was ACTIVE. Execution was ADMITTED."',
              signed: 'Signed at admission time — before any decision ran.',
            },
            {
              id: 'OMNIX-FIN-A3F7B2',
              name: 'Governance Receipt',
              icon: '✅',
              answers: 'What decision was made, and what was the complete context?',
              says: '"APPROVED. AAPL portfolio risk within AVM thresholds. Authorized under ATFDR-8B2C4D6E, admitted under ATFTAR-C4D8E2F1."',
              signed: 'Signed with the same post-quantum cryptography.',
            },
          ].map((doc, i) => (
            <div key={i} style={{
              marginBottom: 16, padding: '24px 28px', borderRadius: 14,
              background: NAVY2, border: `1px solid ${BORDER}`,
              display: 'flex', gap: 20,
            }}>
              <div style={{
                flexShrink: 0, width: 48, height: 48,
                borderRadius: 12, background: 'rgba(201,162,39,0.08)',
                border: `1px solid rgba(201,162,39,0.15)`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 22,
              }}>{doc.icon}</div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6, flexWrap: 'wrap', gap: 8 }}>
                  <div style={{ fontSize: 16, fontWeight: 700, color: '#f1f5f9' }}>{doc.name}</div>
                  <code style={{ fontSize: 11, color: '#475569', background: 'rgba(255,255,255,0.04)', padding: '3px 8px', borderRadius: 4 }}>{doc.id}</code>
                </div>
                <div style={{ fontSize: 12, fontWeight: 600, color: GOLD, marginBottom: 8 }}>Answers: {doc.answers}</div>
                <div style={{ fontSize: 13, color: '#94a3b8', lineHeight: 1.6, marginBottom: 8, fontStyle: 'italic' }}>{doc.says}</div>
                <div style={{ fontSize: 12, color: '#475569' }}>{doc.signed}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Who this matters to */}
        <div style={{ marginBottom: 72 }}>
          <div style={{ textAlign: 'center', marginBottom: 28 }}>
            <div style={{ fontSize: 22, fontWeight: 700, color: '#f1f5f9' }}>
              Who needs this, and why
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 14 }}>
            {[
              { who: 'Regulators', why: 'Can verify the complete authorization chain independently — without contacting the company or the platform.', icon: '🏛️' },
              { who: 'Enterprise Boards', why: 'Can see exactly who authorized each AI system and under what constraints, without relying on verbal assurances.', icon: '🏢' },
              { who: 'Audit Teams', why: 'Have a signed, timestamped artifact for every AI decision — no reconstruction from logs required.', icon: '📋' },
              { who: 'Legal Counsel', why: 'Have documentary evidence establishing human accountability for every AI action.', icon: '⚖️' },
              { who: 'CISO / Security', why: 'Can see exactly what each AI agent is authorized to do and verify the authority chain cryptographically.', icon: '🛡️' },
              { who: 'AI Developers', why: 'Can build agents knowing the governance infrastructure tracks authority correctly, enabling higher-autonomy deployment.', icon: '💻' },
            ].map(item => (
              <div key={item.who} style={{
                padding: '20px', borderRadius: 12,
                background: NAVY2, border: `1px solid ${BORDER}`,
              }}>
                <div style={{ fontSize: 22, marginBottom: 10 }}>{item.icon}</div>
                <div style={{ fontSize: 14, fontWeight: 700, color: '#f1f5f9', marginBottom: 8 }}>{item.who}</div>
                <div style={{ fontSize: 13, color: '#64748b', lineHeight: 1.6 }}>{item.why}</div>
              </div>
            ))}
          </div>
        </div>

        {/* The one-liner again, bigger */}
        <div style={{
          padding: '40px 32px', borderRadius: 16, textAlign: 'center',
          background: 'rgba(201,162,39,0.04)',
          border: `1.5px solid rgba(201,162,39,0.20)`,
          marginBottom: 48,
        }}>
          <div style={{ fontSize: 13, color: GOLD, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 16 }}>
            The One-Liner
          </div>
          <div style={{ fontSize: 24, fontWeight: 800, color: '#f8fafc', lineHeight: 1.4, maxWidth: 560, margin: '0 auto 24px' }}>
            "Every AI agent receives mathematically bounded authority that can be independently verified before execution."
          </div>
          <div style={{ fontSize: 14, color: '#475569' }}>
            That's ATF. Everything else is the implementation.
          </div>
        </div>

        {/* Navigation to technical docs */}
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 14, color: '#64748b', marginBottom: 20 }}>
            Ready for the technical depth?
          </div>
          <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
            <a href="/atf-standard" style={{
              padding: '12px 24px', borderRadius: 10,
              background: GOLD, color: NAVY, fontSize: 14, fontWeight: 700,
              textDecoration: 'none',
            }}>OMNIX ATF Standard →</a>
            <a href="/atf-verify" style={{
              padding: '12px 24px', borderRadius: 10,
              border: `1.5px solid ${BORDER}`,
              color: '#94a3b8', fontSize: 14, fontWeight: 600,
              textDecoration: 'none',
            }}>Public Verifier</a>
            <a href="/agent-trust-fabric" style={{
              padding: '12px 24px', borderRadius: 10,
              border: `1.5px solid ${BORDER}`,
              color: '#94a3b8', fontSize: 14, fontWeight: 600,
              textDecoration: 'none',
            }}>ATF Dashboard</a>
          </div>
        </div>

      </div>
    </div>
  )
}
