# OMNIX — 20 Tough Questions Judges Will Ask
## Eureka Dubai 2026 — Preparation Guide

**Purpose**: Structured answers for the hardest questions Eureka judges will ask.
**Rule**: Short, confident, data-backed. No rambling. No apologizing.

---

## CATEGORY 1: TRACTION & DATA

### Q1: "670,000 evaluation cycles — how many were REAL executed trades?"

**Answer:**
"119 trades were executed during our calibration phase. The 670,000 cycles represent our Shadow Portfolio engine — a counterfactual analysis system that tracks every decision the system evaluates, including the ones it blocks. Think of it as a flight simulator that runs continuously — the 119 real flights validated the system, and the 670,000 simulated scenarios trained it. Additionally, 16,000+ governance decisions are cryptographically signed and publicly verifiable at omnixquantum.net/verify — that is institutional-grade auditability, not a claim."

**Key terms to clarify if asked:**
- Evaluation cycle = one full pass through all 6 checkpoints
- Executed trade = signal that passed all 6 checkpoints and was placed on the exchange
- Veto = signal that was blocked by one or more checkpoints
- Shadow event = a counterfactual record tracking what would have happened
- PQC receipt = cryptographically signed governance decision, publicly verifiable

---

### Q2: "98.5% capital preserved — what's the exact period and benchmark?"

**Answer:**
"January 15 to February 13, 2026 — 30 calendar days. During that period, Bitcoin dropped 7.37% from peak to trough. OMNIX preserved 98.5% of capital by blocking high-risk signals. The benchmark is simple: BTC buy-and-hold would have lost 7.37%. OMNIX lost 1.5%. This was live operation, not backtesting."

---

### Q3: "91% block accuracy — how do you measure that?"

**Answer:**
"We track every blocked trade in our Shadow Portfolio. After the block, we monitor what the price actually did. Of the 47 trades blocked, 43 would have resulted in a loss if executed. That's 91%. The remaining 9% were missed opportunities — but in governance, false positives are acceptable. False negatives destroy capital."

---

### Q4: "119 trades in calibration — isn't that a small sample?"

**Answer:**
"For statistical validation of the 6-checkpoint architecture, 119 trades are sufficient. But the real validation comes from the 670,000+ counterfactual cycles — which confirm the system's restraint logic at scale. We also have a mathematical audit verifying 100% P&L reconciliation across all 119 trades — every cent accounted for against real exchange fill data from Kraken."

---

### Q5: "Is this backtested or live?"

**Answer:**
"Live. Running on Railway production infrastructure 24/7 since November 2025. Connected to Kraken exchange with real market data. The calibration phase used real capital. Every trade is reconciled against actual exchange fill data — we call this Execution Integrity. No simulated fills, no estimated prices."

---

## CATEGORY 2: TECHNOLOGY

### Q6: "What makes your 6 checkpoints better than existing risk management?"

**Answer:**
"Most risk systems have one layer — a stop-loss or a position limit. OMNIX has 6 independent checkpoints that ALL must agree. The key difference is fail-closed architecture: the default is 'don't act.' The system must earn the right to execute. This is how airport security works — one failed scanner and you don't board the plane."

---

### Q7: "Tell me about the post-quantum cryptography."

**Answer:**
"Every decision OMNIX makes — whether executed or blocked — is cryptographically signed using NIST-standardized post-quantum algorithms. This creates an immutable, tamper-proof audit trail. It's operational since November 2025 — not a roadmap item."

**If they ask deeper (Dilithium-3, Kyber-768):**
"We use Dilithium-3 for digital signatures and have the architecture ready for Kyber-768 key encapsulation. These are the algorithms NIST standardized in 2024. We implemented them because institutional clients will need quantum-resistant audit trails as regulatory requirements evolve."

---

### Q8: "What happens when your AI models disagree?"

**Answer:**
"That's exactly the point. We use a Decision Contradiction Index — when models significantly disagree, the system holds. High contradiction means high uncertainty, and high uncertainty means don't act. The system has 5 independent models. If they can't reach 45% consensus, the action is blocked. Disagreement is a feature, not a bug."

---

### Q9: "Why three AI providers? Isn't that expensive?"

**Answer:**
"Zero single-provider dependency. If Google goes down, we fail over to OpenAI. If OpenAI goes down, we fail over to Anthropic. For a governance infrastructure that institutions rely on, single-provider dependency is unacceptable. The cost is marginal compared to the reliability it provides."

---

### Q10: "Can this be copied by a big player?"

**Answer:**
"The architecture can be described in a slide. Building it takes 3+ months of continuous real-market operation, 27 documented architecture decisions, a Shadow Portfolio engine with 670,000+ events, and domain expertise in behavioral risk. Our moat isn't just technology — it's the calibrated intelligence the system has accumulated. Plus, big players build for themselves. We build governance-as-infrastructure for everyone else."

---

## CATEGORY 3: BUSINESS MODEL & MARKET

### Q11: "Why would a prop firm pay $15K-$35K per month for this?"

**Answer:**
"Because one bad drawdown event costs them $100K or more. A prop firm with 20 traders managing $50M in capital loses an average of 2-3% per quarter to preventable risk events. That's $1M-$1.5M annually. If OMNIX reduces drawdown events by 40%, the ROI is immediate. They're not paying for software — they're paying for capital they don't lose."

---

### Q12: "Why not performance fees? Wouldn't that align incentives?"

**Answer:**
"Performance fees create perverse incentives — they reward action over restraint. Our product's value is in what it PREVENTS, not what it generates. License-based pricing means our incentive is aligned with theirs: keep the system accurate, keep the client protected. Also, performance fees trigger different regulatory classifications in ADGM and under MiCA. Clean licensing avoids that entirely."

---

### Q13: "3 enterprise pilots in Year 1 — isn't that slow?"

**Answer:**
"For enterprise governance infrastructure, that's aggressive. These are not $49/month SaaS signups — they're $15K-$35K/month institutional contracts requiring security reviews, compliance checks, and integration work. Three paying pilots in Year 1 gives us validated revenue, reference clients, and the proof points needed for Series A."

---

### Q14: "Who are your competitors?"

**Answer:**
"There are trading bots — 3Commas, Cryptohopper — that optimize for action. There are institutional risk platforms — Gauntlet, Risk Labs — that serve large hedge funds. And there are internal quant teams. Nobody occupies the middle: institutional-grade governance infrastructure accessible to prop firms, platforms, and regulated funds. That's our position."

**If pressed on comparability:**
"We don't compete with trading bots on returns. We don't compete with internal quant teams on customization. We compete on accessibility of institutional governance — making what only the biggest funds have available to everyone who needs it."

---

### Q15: "$2.5M-$3M pre-money — how do you justify that for a pre-revenue company?"

**Answer:**
"Three factors. First, the product exists and runs in production — this isn't a concept. Second, we have 670,000+ data points validating the architecture. Third, Chainalysis raised at $4M pre-money at a similar stage — pre-revenue but with a working product and clear regulatory tailwind. MiCA alone will create demand for governance infrastructure across 2,000+ platforms."

---

## CATEGORY 4: REGULATORY & GEOGRAPHIC

### Q16: "Are you ADGM licensed?"

**Answer:**
"Not yet — and that's intentional. We're designing our corporate structure to align with ADGM requirements. Part of this raise — 25% — is allocated specifically to Dubai/ADGM legal and regulatory setup. We're building the product first, then wrapping the regulatory structure around it. That's more capital-efficient than licensing first and building second."

---

### Q17: "What if MiCA requirements change?"

**Answer:**
"MiCA mandates audit trails and risk governance — those requirements will only get stricter, not looser. Our architecture is regulation-agnostic: we provide governance infrastructure and audit trails regardless of the specific regulatory framework. If requirements change, we adapt the reporting layer — the core engine stays the same."

---

### Q18: "Why Dubai and not London or Singapore?"

**Answer:**
"Three reasons. ADGM has the most progressive regulatory framework for digital assets. There are 200+ prop firms in ADGM and DIFC — immediate addressable market. And sovereign capital in the region is actively deploying into fintech and AI infrastructure. Dubai isn't just a headquarters — it's our first market."

---

## CATEGORY 5: FOUNDER & EXECUTION

### Q19: "You built this alone — what happens if you get hit by a bus?"

**Answer:**
"Fair question. Three mitigations. First, the system runs autonomously on production infrastructure — it doesn't need me to operate day-to-day. Second, we have 27 Architecture Decision Records documenting every technical decision, plus complete documentation. Third, 15% of this raise goes directly to hiring 2-3 key team members in months 1-4 — that's specifically to eliminate key-person risk."

---

### Q20: "How did one person build all of this?"

**Answer:**
"Lean architecture designed for scalability. I use AI as a force multiplier — not to write code blindly, but as an engineering partner for architecture, testing, and documentation. AI-assisted development reduces burn while maintaining velocity. The result: zero burn rate before funding, all IP created with personal capital, and a working product in production. That's capital efficiency that investors value."

---

## BONUS: THE "TRAP" QUESTIONS

### Q-BONUS-1: "What's your unfair advantage?"

**Answer:**
"Three months of real-market operation. 670,000+ calibrated data points. And a fail-closed architecture that, to our knowledge, no comparable infrastructure is building — because the industry is optimized for action, not restraint. Our unfair advantage is discipline — encoded into software."

---

### Q-BONUS-2: "What keeps you up at night?"

**Answer:**
"Execution speed on enterprise sales. The technology works. The market exists. The regulatory tailwind is real. The risk is: can we close enterprise pilots fast enough to prove revenue before Series A? That's why 15% of the raise goes to business development from Month 3."

---

### Q-BONUS-3: "If you could only say one sentence about OMNIX, what would it be?"

**Answer:**
"OMNIX is the governance layer that prevents costly mistakes before they happen — in trading, and eventually in any high-stakes decision domain."

---

## DELIVERY RULES

1. **Start with the answer, then explain.** Never start with background.
2. **Use numbers first.** "98.5% capital preserved" before "our system is conservative."
3. **Keep sentences short.** Under 15 words per sentence when possible.
4. **Never say "that's a great question."** Just answer it.
5. **If you don't know, say:** "I don't have that specific data point, but here's what I do know..."
6. **Maintain posture.** You're not defending — you're informing.

---

*OMNIX — Governing Decisions Under Uncertainty*
*Eureka Dubai 2026 — Semifinalist*
