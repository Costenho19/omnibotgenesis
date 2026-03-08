# OMNIX — Top 10 Panel Questions
## Eureka GCC 2026 — Q&A Preparation (Harold Nunes)

**Rule:** Number first. Explanation after. Short sentences. No rambling.
**Format:** Answer in under 30 seconds per question.
**Updated:** March 8, 2026 — 50,688 PQC receipts | 728,868 evaluations | 8-checkpoint + EGL | 36 ADRs

---

## THE 5 MOST LIKELY QUESTIONS

---

### Q1: "How many real trades vs simulations?"

**Answer:**
"119 trades validated execution. The 728,000+ cycles validated the governance logic.

Think of it like a flight simulator. The 119 real flights proved the system works. The 728,000 simulated scenarios stress-tested the governance engine at scale. Every real trade is reconciled against actual Kraken exchange fill data — every cent accounted for. Additionally, 50,688 decisions are post-quantum cryptographically signed and publicly verifiable at omnixquantum.net/verify."

**If they push on "only 119 real trades":**
"For validating governance architecture, the statistical threshold is much lower than for validating a strategy. We're testing whether the veto logic fires correctly — not whether a trading edge persists. 119 real trades plus 728,000 counterfactual cycles is rigorous validation for a governance layer."

---

### Q2: "Why can't a large bank or exchange build this internally?"

**Answer:**
"They can. And the biggest ones will. We build it for everyone else.

The same way Stripe didn't stop banks from building payments internally — Stripe built payments infrastructure for the companies that can't afford a 50-person payments team. OMNIX builds governance infrastructure for the prop firms, platforms, and regulated funds that can't afford a $1M/year internal quant governance team. Our moat: 4 months of real-market calibration, 36 documented architecture decisions, and a Shadow Portfolio engine with 728,000+ events. That's not a slide deck. That's operational intelligence."

---

### Q3: "Why would someone pay $15,000 per month for this?"

**Answer:**
"Because they're not paying for software. They're paying for capital they don't lose.

A prop firm with $10M under management loses an average of 2-3% per quarter to preventable risk events. That's $200K-$300K annually. If OMNIX reduces drawdown events by 40%, the ROI on $180K/year licensing is immediate and measurable. One avoided flash crash event covers the annual contract."

---

### Q4: "You built this alone?"

**Answer:**
"The architecture and core system — yes. I've worked with contract developers and infrastructure consultants for specific components. But the governance design, the 36 architecture decisions, and the production deployment are mine.

More importantly: the system runs autonomously 24/7 without my intervention. It's not dependent on me being present. Three mitigations for key-person risk: autonomous production infrastructure, 36 Architecture Decision Records documenting every technical decision, and 15% of this raise goes directly to hiring 2-3 key engineers in the first 4 months."

---

### Q5: "Why start with crypto? Isn't that a volatile, risky market?"

**Answer:**
"Exactly because it's volatile. Crypto is the harshest environment to validate governance infrastructure — 24/7 operation, high volatility, millisecond execution. If the system works here, it works anywhere.

The same 8-checkpoint governance engine applies to credit decisions, insurance underwriting, supply chain automation, and robotics. We're not a crypto company. We're a governance infrastructure company that validated in crypto first — because that's where automated decision failures are most visible and most measurable."

---

## 5 ADDITIONAL HIGH-PROBABILITY QUESTIONS

---

### Q6: "Is this a feature or a company?" *(Most dangerous question — be ready)*

**Answer:**
"It's a company. Here's why.

A feature lives inside one product. OMNIX is a horizontal infrastructure layer — the same engine governs decisions in trading, lending, insurance, and robotics. That's the AWS model: horizontal infrastructure that every vertical needs but none should build themselves.

The governance problem scales with automation. Every new automated system that goes into production becomes a potential client. As AI and automation expand across industries, the demand for pre-execution governance infrastructure grows with it. That's a platform, not a feature."

---

### Q7: "What does a customer integration actually look like? How long does it take?"

**Answer:**
"Three weeks for a standard integration.

Week 1: API connection — the client sends decision signals to our governance endpoint. Week 2: Calibration — we tune the checkpoints to their specific risk profile and asset class. Week 3: Shadow mode — the system runs in parallel with their existing flow, no live blocking, pure observation. After that, they flip the switch to active governance.

We designed it this way intentionally. Shadow mode first means zero disruption risk for the client. They see the system work before they depend on it."

---

### Q8: "What's your go-to-market plan after today?"

**Answer:**
"Three parallel tracks.

First: convert warm contacts from this competition — we already have 5 qualified conversations from LinkedIn with AI infrastructure builders. Second: target prop trading firms under $100M AUM — they need institutional governance but can't build it internally. Third: apply to Hub71 and fintech accelerators for enterprise introductions.

The goal for Year 1 is 3 paying pilots at $15K-$35K/month. That's $540K-$1.26M ARR — enough to close a Series A with revenue proof."

---

### Q9: "What if OMNIX blocks a good trade? Doesn't false positives cost money?"

**Answer:**
"Yes. We call it opportunity cost, and we track it explicitly.

In governance, false positives — blocking a good trade — are acceptable. False negatives — executing a bad one — destroy capital. The asymmetry is clear: a missed 2% gain costs $200. An executed flash crash loses $20,000. Our system is calibrated for that asymmetry deliberately.

We also run a Shadow Portfolio that tracks every blocked trade. If a blocked trade would have been profitable, we capture that data and use it to recalibrate the checkpoints. The system gets smarter over time — false positive rate decreases with calibration."

---

### Q10: "What does 12-month success look like for this raise?"

**Answer:**
"Three milestones. Twelve months.

One: 3 paying enterprise pilots live — at least $15K/month each. That's validated revenue, not an LOI.

Two: Governance receipts verifiable for at least 2 client verticals beyond crypto — proving domain-agnostic architecture.

Three: Series A ready — with revenue, reference clients, and a team of 4-5 people.

The $500K raise covers 18-24 months of runway. We don't need to rush to Series A — we need to build the proof points that make it inevitable."

---

## DELIVERY RULES

1. **Number first, always.** "98.5% capital preserved" — then explain.
2. **One breath per answer.** If you need a second breath, you're rambling.
3. **Never say "great question."** Just answer.
4. **If you don't know:** "I don't have that specific number with me, but here's what I do know..."
5. **After the final pitch line — stay silent.** Let it land.

---

*OMNIX — Governing Decisions Under Uncertainty*
*Eureka GCC 2026 — Semifinalist | Harold Nunes*
*Data as of March 8, 2026: 728,868 evaluations | 50,688 PQC receipts | 8-checkpoint entry + 3-gate EGL exit | 36 ADRs*
