# OMNIX — 20 Tough Questions Judges Will Ask
## Eureka Dubai 2026 — Preparation Guide

**Purpose**: Structured answers for the hardest questions Eureka judges will ask.
**Rule**: Short, confident, data-backed. No rambling. No apologizing.
**Last Updated**: March 4, 2026 — Checkpoint 7 (TCV, ADR-032) added to trading pipeline.

> **NOTA ARQUITECTURA (Mar 2026):** El trading pipeline pasó de 6 a **7 checkpoints** con la adición de Temporal Coherence Validation (TCV, ADR-032). Todas las métricas publicadas (670,000+ ciclos, 91%, 98.5%) fueron generadas bajo el sistema validado de **6 checkpoints** hasta febrero 2026. TCV es el Checkpoint 7 — aditivo, no reemplaza los anteriores.

---

## CATEGORY 1: TRACTION & DATA

### Q1: "670,000 evaluation cycles — how many were REAL executed trades?"

**Answer:**
"119 trades were executed during our calibration phase. The 670,000 cycles represent our Shadow Portfolio engine — a counterfactual analysis system that tracks every decision the system evaluates, including the ones it blocks. Think of it as a flight simulator that runs continuously — the 119 real flights validated the system, and the 670,000 simulated scenarios trained it. Additionally, 16,000+ governance decisions are cryptographically signed and publicly verifiable at omnixquantum.net/verify — that is institutional-grade auditability, not a claim."

**Key terms to clarify if asked:**
- Evaluation cycle = one full pass through all governance checkpoints (6 checkpoints through Feb 2026; 7 checkpoints including TCV from March 2026)
- Executed trade = signal that passed all checkpoints and was placed on the exchange
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
"For statistical validation of the governance architecture, 119 trades are sufficient to validate the core logic. But the real validation comes from the 670,000+ counterfactual cycles — which confirm the system's restraint logic at scale. We also have a mathematical audit verifying 100% P&L reconciliation across all 119 trades — every cent accounted for against real exchange fill data from Kraken. These results are anchored to the 6-checkpoint system validated through February 2026. In March 2026 we added Checkpoint 7 (Temporal Coherence Validation, ADR-032)."

---

### Q5: "Is this backtested or live?"

**Answer:**
"Live. Running on Railway production infrastructure 24/7 since November 2025. Connected to Kraken exchange with real market data. The calibration phase used real capital. Every trade is reconciled against actual exchange fill data — we call this Execution Integrity. No simulated fills, no estimated prices."

---

## CATEGORY 2: TECHNOLOGY

### Q6: "What makes your 7 governance checkpoints better than existing risk management?"

**Answer:**
"Most risk systems have one layer — a stop-loss or a position limit. OMNIX has 7 independent checkpoints that ALL must agree. The key difference is fail-closed architecture: the default is 'don't act.' The system must earn the right to execute. This is how airport security works — one failed scanner and you don't board the plane. The first 6 checkpoints were validated across 670,000+ evaluation cycles (through February 2026). Checkpoint 7 — Temporal Coherence Validation — was added in March 2026 and ensures every decision is consistent with the system's recent trajectory."

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
"The architecture can be described in a slide. Building it takes 3+ months of continuous real-market operation, 32 documented architecture decisions (including ADR-032 for Checkpoint 7), a Shadow Portfolio engine with 670,000+ events, and domain expertise in behavioral risk. Our moat isn't just technology — it's the calibrated intelligence the system has accumulated. Plus, big players build for themselves. We build governance-as-infrastructure for everyone else."

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

### SOBRE EL PAPER DE SSRN (Si el juez lo menciona)

---

### Q-BONUS-4: "¿Fue revisado por pares?" / "Was this peer-reviewed?"

**Answer:**
"Es un preprint publicado en SSRN — no tiene revisión por pares, y quiero ser preciso sobre eso. Lo publicamos para establecer un registro técnico público con fecha, DOI y verificación. Los datos son reales y trazables contra Kraken exchange. SSRN es el repositorio estándar en finanzas y economía para exactamente este tipo de estudio — es donde los practitioners publican antes que las revistas académicas."

**Key framing:** Honestidad primero. No decir "peer-reviewed" si no lo es. SSRN es legítimo — es donde los investigadores del Fed, BIS y hedge funds publican preprints.

---

### Q-BONUS-5: "¿Lo escribiste tú solo?" / "Did you write this paper yourself?"

**Answer:**
"El contenido técnico — los datos, la arquitectura, los resultados, la metodología — son míos. Yo construí el sistema que el paper describe. Para la redacción académica usé asistencia de IA, igual que lo hacen hoy muchos investigadores y fundadores técnicos. Lo importante es que el sistema existe, corre en producción, y cada resultado en el paper es verificable contra datos reales."

**Key framing:** No esconder el uso de IA — eso sería peor si se descubre. La honestidad refuerza la credibilidad. El punto central es que los datos y el sistema son reales.

---

### Q-BONUS-6: "¿Por qué SSRN y no una revista académica?" / "Why SSRN and not a journal?"

**Answer:**
"Una revisión por pares tarda 12-18 meses. SSRN nos da lo que necesitamos en esta etapa: timestamp público permanente, DOI citable, e indexación en Google Scholar — esta semana, no en 2027. El paper no pretende ser investigación universitaria. Es documentación técnica de un deployment en producción, publicada para establecer registro público de la arquitectura antes de esta ronda de inversión."

---

### Q-BONUS-7: "¿Cuál es la contribución principal del paper?" / "What's the main contribution?"

**Answer:**
"El paper reporta el primer deployment en producción conocido de governance receipts firmados con criptografía post-quantum para sistemas de decisión autónomos. No es teórico — es una descripción de arquitectura con datos reales: 49 días de operación continua, 693,890 ciclos de evaluación, 27,449 receipts firmados con Dilithium-3 en una cadena SHA-256 verificable públicamente. Cualquier persona puede verificar cualquier receipt en omnixquantum.net/verify sin acceso interno."

---

### Q-BONUS-8: "El paper dice 693,890 ciclos pero el pitch dice 670,000+. ¿Por qué la diferencia?"

**Answer:**
"Períodos distintos. El paper cubre enero 9 a febrero 27, 2026 — 49 días específicos con 693,890 ciclos. El pitch usa 670,000+ como cifra conservadora redondeada que cubre el Track Record Oficial desde enero 15. El número real al momento actual es mayor — siempre usamos el más conservador en materiales públicos, nunca inflamos."

**Key framing:** Esta es la pregunta más técnica posible — si un juez la hace, significa que realmente leyó el paper. Tenerla preparada genera credibilidad inmediata.

---

### Q-BONUS-9: "¿Es citable? ¿Tiene DOI?" / "Is it citable?"

**Answer:**
"Sí. SSRN asigna DOI a todos los papers publicados. Está indexado en Google Scholar. Cualquier persona puede buscarlo, citarlo, y verificar la fecha de publicación — febrero 2026. Eso nos da un registro público de la arquitectura con timestamp anterior a cualquier conversación de inversión."

---

### Q-BONUS-10: "El paper menciona el caso Knight Capital. ¿La comparación es justa?" / "Is the Knight Capital comparison fair?"

**Answer:**
"Es justa como motivación del problema — no como comparación de escala. Knight Capital perdió $440M porque no había un mecanismo que bloqueara decisiones incorrectas antes de ejecutarlas. Ese es exactamente el problema que OMNIX resuelve. No reclamamos ser el sistema que Knight Capital necesitaba. Lo usamos para ilustrar qué pasa cuando sistemas autónomos operan sin governance en tiempo real — un problema de industria universal que va mucho más allá del trading."

---

### Q-BONUS-11: "Show me Level 5 signing in action. Can you demonstrate it right now?"

**Context**: A technical evaluator (or investor with cryptographic background) challenges the Level 3 choice and asks for a live demonstration of Level 5 capability. This tests whether the architecture is genuinely configurable or just a marketing claim.

**Verbal answer (institutional tier):**

"Yes — right now."

Run this:
```
python scripts/pqc_level_demo.py --level 5
```

"You will see Dilithium-5 (ML-DSA-87) generate a fresh key pair, sign a real governance decision payload — same structure we use in production — and verify it. Tamper detection also runs: modifying the payload by a single byte causes the verification to fail. Both levels are operational. We run Level 3 in production today because that's the NIST enterprise baseline appropriate for institutional capital governance. Level 5 is available by setting one environment variable in the deployment. No code changes, no architectural rewrite."

**What the output proves:**

1. **Dilithium-5 (ML-DSA-87) is operationally available** — not a claim. The library is present, the key generation works, the signing works, the verification works.

2. **The architecture is genuinely configurable** — `omnix_core/security/pqc_config.py` reads `PQC_SIGNING_LEVEL` at service startup. Setting `PQC_SIGNING_LEVEL=5` in Railway and redeploying activates Level 5 for all signing. Callers don't change.

3. **Level 3 is the correct production choice** — Level 3 signatures are 3,309 bytes at ~0.6ms. Level 5 signatures are 4,627 bytes (+39.8%) at ~0.9ms. At 700,000+ daily governance evaluations, that overhead is material. Level 3 (~192-bit classical security) is the NIST target for institutional deployments; Level 5 (~256-bit) is for national-grade or state-secrecy contexts.

**Side-by-side comparison command:**
```
python scripts/pqc_level_demo.py --compare
```

**For programmatic verification:**
```
python scripts/pqc_level_demo.py --compare --json
```

**If pushed: "Why not Level 5 in production right now?"**

"Because threat model drives level selection, not maximalism. OMNIX governs capital-sensitive institutional decisions — not classified state communications. AES-192 equivalent assurance (Level 3) is the designed NIST enterprise target. We would activate Level 5 for a client with national-grade assurance requirements. The architecture is ready. The decision is deployment-context driven."

**What NOT to say:**
- "We'll add Level 5 support later" — it's already there, running
- "Level 3 is our minimum" — Level 3 is the designed enterprise baseline
- "We can switch it in real-time without restart" — a service restart is required

**References**: ADR-022, ADR-031, `docs/business/investor/PQC_DUE_DILIGENCE_DEMO.md`

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
*Last Updated: March 4, 2026 — 7-checkpoint architecture (TCV, ADR-032)*
