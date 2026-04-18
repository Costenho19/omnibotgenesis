# OMNIX — Investor FAQ
## Decision Governance Infrastructure

**Classification**: Investor Confidential
**Last Updated**: March 29, 2026 — Multi-vertical expansion: Insurance + Robotics 24/7 live. 11 checkpoints + CAG + TIE. 57 ADRs. TAM $137B+.

---

## Decision Governance Infrastructure

### Q1: Why does the Official Track Record show ~0 trades?

**A:** This is by design. The Official Track Record (starting January 15, 2026) operates with recalibrated, highly conservative parameters after learning from the baseline period. The system is in "extreme risk-aversion" mode during track record validation.

The 89,000+ blocked decisions demonstrate the veto architecture working correctly—OMNIX is designed to NOT trade when conditions aren't optimal. This is the core value proposition: capital preservation over forced returns.

### Q2: What's the difference between Learning Baseline and Official Track Record?

**A:**

| Period | Dates | Trades | P&L | Purpose |
|--------|-------|--------|-----|---------|
| **Learning Baseline** | Nov 2025 - Jan 14, 2026 | 119 | -$15,198.73 | Aggressive calibration, stress-testing |
| **Official Track Record** | Jan 15, 2026 - present | ~0 | $0 | Validation with recalibrated parameters |

The Learning Baseline was intentionally aggressive to stress-test the system and identify filter weaknesses. The Official Track Record uses the lessons learned to operate with institutional-grade risk controls.

### Q3: Why was there a -$15K loss in the Learning Baseline?

**A:** The Learning Baseline was designed as a stress-test phase with intentionally aggressive parameters. This allowed us to:

1. Identify which filters needed calibration
2. Test the Shadow Portfolio learning system
3. Collect counterfactual data on vetoed trades
4. Calibrate thresholds for the Edge Confirmation Window

The loss represents 1.5% of the $1M paper trading capital, demonstrating that even during aggressive testing, the core capital preservation mechanisms limited downside.

### Q4: What does "89,000+ blocked decisions" mean?

**A:** Every 5-minute cycle, OMNIX evaluates market conditions and makes a decision. When conditions don't meet our strict criteria, the system blocks the trade and logs it. This metric represents:

- **Active risk management**: The system is constantly evaluating
- **Veto system working**: Multiple layers rejecting low-quality setups
- **Capital preservation**: Each block is a potential loss avoided

**Important clarification:** This metric represents evaluation cycles, not trade opportunities or missed profits. It does NOT mean 89,000 profitable trades were missed—most blocked decisions would have resulted in losses based on Shadow Portfolio analysis.

---

## Risk Controls & Architecture

### Q5: How does OMNIX protect capital?

**A:** OMNIX uses a 13-layer hierarchical veto system — the most comprehensive governance pipeline we have built to date (March 29, 2026):

```
PRE-ADMISSION:
  CAG     Context Admission Gate     — Blocks if global market is structurally inadmissible
  ACV     Admissibility Consistency  — Blocks if input signals internally contradict

ENTRY PIPELINE (11 Checkpoints):
  CP-0   SIV    Signal Integrity     — Data quality, freshness, completeness
  CP-1   PROB   Monte Carlo          — Win Rate ≥ 48%, Expected Return > 0%
  CP-2   RISK   Risk Limits          — Position sizing, drawdown controls
  CP-3   COH    Coherence (DCI<70)   — Internal signal alignment
  CP-4   TREND  Trend Analysis       — EMA + HMM regime confirmation
  CP-5   STRESS Stress Resilience    — Black Swan, tail-risk detection
  CP-6   SHAR   Sharia Gate          — Halal screening, Riba/Gharar control
  CP-7   TCV    Temporal Coherence   — Backward signal consistency
  CP-7b  FTI    Forward Trajectory   — Multi-step forward implication
  CP-8   ECW    Edge Confirmation    — Persistence (2+ consecutive cycles)
  CP-9   AML    AML Gate             — FATF Rec.15, UAE AML/CFT, FinCEN
  CP-10  FRAUD  Fraud Detection      — EU AI Act Art.6, MiFID II, SEC 10b-5
  CP-11  JUR    Jurisdiction Gate    — UAE/EU/US/GCC asset compliance

POST-PIPELINE:
  TIE    Trajectory Invariant       — Blocks if trajectory of decisions is unsafe
  PQC    Quantum-Secure Receipt     — Dilithium-3 signature + Merkle hash chain
```

This is a **fail-closed architecture**: the default is NOT to act. Execution requires passing every layer.

### Q-EVOLUTION: How has the system evolved from March 6 to March 29, 2026?

**A:** March 2026 was the most architecturally dense month in OMNIX's history:

| Date | Change | ADR |
|------|--------|-----|
| Mar 6, 2026 | SIV (CP-0), FTI (CP-7b), RCK, EGL — architectural gap closure | ADR-033/034/035/036 |
| Mar 25, 2026 | Sharia Gate (CP-6) | ADR-046 |
| Mar 25, 2026 | AML Gate (CP-9), Fraud Gate (CP-10), Jurisdiction Gate (CP-11) | ADR-047/048/049 |
| Mar 26, 2026 | Context Admission Gate (CAG) | ADR-050 |
| Mar 26, 2026 | Dual Trading Mode (CORE/ACTIVE) | ADR-051 |
| Mar 27, 2026 | Islamic Credit Governance — 24/7 live | ADR-052 |
| Mar 27, 2026 | Trajectory Invariant Enforcement (TIE) | ADR-053 |
| Mar 29, 2026 | Insurance Governance — 24/7 live | ADR-054 |
| Mar 29, 2026 | Robotics Governance — 24/7 live | ADR-055 |

Total ADRs: **57** (was 36 on March 6). Total checkpoints: **11 + CAG + TIE** (was 8 on March 6).

### Q-MULTIVERTICAL: Is OMNIX really domain-agnostic, or is it just a trading system?

**A:** As of March 29, 2026, this is an empirical question with a live answer:

| Domain | Decision Type | Consequence | Live Since |
|--------|--------------|-------------|-----------|
| Trading | Execute trade / Don't execute | Capital preserved or lost | Jan 15, 2026 |
| Islamic Credit | Approve loan / Reject loan | Default avoided or credit granted | Mar 27, 2026 |
| Insurance | Approve claim / Block claim | Loss paid or fraud prevented | Mar 29, 2026 |
| Robotics | Execute action / Block action | Safety incident or task completed | Mar 29, 2026 |

Four structurally different domains. One governance engine. Zero changes to core pipeline logic. Every decision receives the same 11-checkpoint evaluation and the same PQC-signed receipt.

**The TAM implication**: The governance problem is not unique to trading. Every domain where automated systems make high-stakes binary decisions faces the same structural gap. OMNIX is the infrastructure that fills it.

### Q-TAM: How does the TAM change with multiple verticals?

**A:**

| Scope | TAM |
|-------|-----|
| March 6, 2026 (trading only) | $5B |
| March 29, 2026 (trading + insurance + robotics) | $137B+ |

- **Insurance**: $7T+ in global premiums annually. Fraudulent claims cost the industry $308B+ per year globally. OMNIX governance applied to claim decisions — every blocked fraudulent claim is quantifiable loss avoided.
- **Robotics**: $80B+ industrial robotics market. No comparable pre-execution governance infrastructure exists. Post-incident analysis is standard; OMNIX provides pre-execution governance.
- **Islamic Finance**: $2T+ AUM. Sharia-compliant governance at scale — the UAE/GCC market actively demands it.

This is not projection. These are markets where OMNIX governance engines are already running today.

### Q-ROBOTICS: What does "pre-execution governance" mean for robots?

**A:** In traditional robotics, governance happens *after* an incident — root cause analysis, logs, corrective action. OMNIX governance happens *before* the robot acts.

Every robot action is evaluated through the full 11-checkpoint pipeline:
- Sensor fusion agreement (LiDAR + Camera + IMU) → signal coherence checkpoint
- Battery, temperature, joint stress → stress resilience checkpoint
- Mission logic alignment → logic consistency checkpoint
- Collision and damage risk → risk limits checkpoint

If the pipeline blocks the action, the robot does not execute it. The decision is logged with a PQC-signed receipt. Every safety incident prevented is a measurable output.

**No comparable infrastructure exists.** The industrial robotics market ($80B+) has no pre-execution governance layer. OMNIX is building the first one.

### Q6: What is the Edge Confirmation Window (ECW)?

**A:** ECW is our "capital patience" mechanism. Before allowing any trade, the system requires:

- Monte Carlo Win Rate ≥ 52%
- Monte Carlo Expected Return > 0%
- Black Swan Severity ≤ MEDIUM
- **For 3 consecutive evaluation cycles**

This prevents trading on momentary signals and ensures edge persistence before capital deployment.

### Q7: What is the Decision Contradiction Index (DCI)?

**A:** DCI measures internal signal divergence. When different strategies (EMA, HMM, Kalman, etc.) disagree significantly:

- **DCI < 70**: Normal operation, trade evaluation continues
- **DCI ≥ 70**: High contradiction → Mandatory HOLD

This explains why the system doesn't trade during uncertain conditions—it's not hesitation, it's measured disagreement among strategies.

### Q8: What are the drawdown limits?

**A:**

| Limit | Value | Type | Description |
|-------|-------|------|-------------|
| **Hard System Cap** | 15% | Absolute maximum | Circuit breaker triggers, system pauses |
| **Observed in Baseline** | 1.5% | Actual performance | What occurred during Learning Baseline |
| Per-Trade Risk | 0.5-5% | Configurable | Based on risk profile |
| Daily Trade Limit | 20 | Operational | Prevents overtrading |

**Clarification:** The 15% is the hard system cap (absolute maximum before circuit breaker). The 1.5% is what was actually observed during the Learning Baseline period. The Risk Guardian V5.4 monitors these limits in real-time and activates circuit breakers automatically.

### Q-NEW: What is "Decision Governance Infrastructure" and why is OMNIX creating this category?

**A:** Decision Governance Infrastructure is the control layer for automated decision systems — ensuring that every automated decision passes through independent validation checkpoints before execution. 

Just as payment infrastructure became necessary before e-commerce could scale, governance infrastructure will become necessary before automated decision systems scale. OMNIX is building this governance layer. The first validated vertical is digital asset trading, with 670,000+ evaluation cycles and 98.5% of capital preserved.

The right question for investors is not "how much alpha does OMNIX generate?" but "how much capital risk exists in automated systems without governance control?"

### Q-LUNA: Has OMNIX been validated against real historical collapses?

**A:** Yes. We applied our full 8-checkpoint governance pipeline to the **Terra/LUNA collapse of May 2022** — the largest single-event failure in crypto history ($40B+ destroyed in 72 hours).

The forensic reconstruction shows OMNIX would have:

| Phase | Time Before Collapse | LUNA Price | OMNIX Decision |
|-------|---------------------|------------|----------------|
| Phase 1 | 72 hours | $68.84 | WARNING — Structural brittleness detected |
| Phase 2 | 24 hours | $18.14 | BLOCKED — All checkpoints below threshold |
| Phase 3 | 6 hours | $4.60 | BLOCKED + PQC-signed receipt issued |

**Key result**: OMNIX issued a BLOCKED decision 6 hours before the irreversible collapse. Capital would have been 100% preserved. Every probabilistic system in the market failed.

**How it detected the collapse when others didn't:**
1. **CP-0 (Signal Integrity)**: Detected that momentum was inherited from a stale 18-month bull regime — not earned from current conditions
2. **CP-7 (Temporal Coherence)**: Found the signal was "Forensically Inconsistent" — executing against a ghost of the previous regime
3. **CP-4 (Coherence Engine)**: All independent models disagreed with the surface signal

**Full forensic simulation report available** (499 KB PDF with 4-panel charts, checkpoint scores, and PQC-signed governance receipt).

*Disclosure: This is a forensic simulation applied to historical data. OMNIX was not operational during May 2022. The reconstruction demonstrates architectural capability.*

---

### Q-SVB: Has OMNIX been validated beyond crypto — in traditional banking?

**A:** Yes. We applied the same 8-checkpoint governance pipeline to the **Silicon Valley Bank collapse of March 2023** — the second-largest bank failure in U.S. history ($209B in assets). This demonstrates that OMNIX's governance architecture works across asset classes, not just crypto.

The forensic reconstruction shows OMNIX would have:

| Phase | Time Before Collapse | SVB Equity | OMNIX Decision |
|-------|---------------------|------------|----------------|
| Phase 1 | 90 days | $236.09/share | STRUCTURAL WARNING — High-risk flag raised |
| Phase 2 | 14 days | $287.42/share | SUSPENDED — Kelly = 0%, WARNING escalated |
| Phase 3 | 48 hours | $267.83 → $106.04 | BLOCKED + PQC-signed receipt issued |

**Key result**: OMNIX issued a BLOCKED decision 48 hours before FDIC takeover. Capital would have been 100% preserved. The stock had risen to $287 two weeks earlier — giving a false confidence signal that every traditional risk system missed.

**How it detected the collapse when others didn't:**
1. **CP-0 (Signal Integrity)**: Detected that 94.2% of confidence was inherited from the zero-rate era — a regime the Federal Reserve had explicitly terminated 12 months earlier
2. **CP-7 (Temporal Coherence)**: Found the confidence trajectory was structurally inconsistent with the current rate environment
3. **CP-1 (Monte Carlo)**: 98.7% of simulated paths showed catastrophic loss within 14 days

**Full forensic simulation report available** (192 KB PDF with capital preservation analysis, checkpoint scores, and PQC-signed governance receipt).

*Disclosure: This is a forensic simulation applied to historical data. OMNIX was not operational during March 2023. The reconstruction demonstrates cross-domain architectural capability.*

---

## Technology & Security

### Q9: What is OMNIX's position on Post-Quantum Cryptography?

**A:** OMNIX has **production-integrated post-quantum cryptography modules** for order signing and key exchange, aligned with NIST 2024 standards:

| Component | Algorithm | Standard | Purpose |
|-----------|-----------|----------|---------|
| Key Encapsulation | Kyber-768 (ML-KEM-768) | NIST-standardized | Secure key exchange |
| Digital Signatures | Dilithium-3 (ML-DSA-65) | NIST-standardized | Trading order authentication |

**Key facts:**
- Trading orders are signed with Dilithium-3 before execution
- Module located at `omnix_core/security/pqc_security.py`
- Both algorithms provide NIST Level 3 security (~192-bit classical equivalent)
- Protects against future quantum computer attacks

**Important disclaimer:** Currently applied to order authentication and internal security layers. This is not marketed as a compliance guarantee or external security certification.

### Q10: How auditable and explainable is the system? (XAI / Explainability)

**A:** OMNIX is designed as the opposite of a "black box." Every decision — executed or blocked — produces a full, structured audit record:

| Audit Component | Detail |
|----------------|--------|
| **Decision Trace** | Structured JSON per decision: timestamp, 8 checkpoint verdicts with individual data, final decision with reasoning, capital impact (6 checkpoints through Feb 2026 + 8 checkpoints from Mar 2026) |
| **Checkpoint Explainability** | Each of 8 checkpoints produces a human-readable verdict (e.g., "Win probability 48.7% — below 50% threshold", "TCV score 18/100 — trajectory inconsistent") |
| **Post-Quantum Signatures** | Every decision signed with NIST-standardized algorithms — immutable, tamper-proof |
| **Counterfactual Evidence** | Shadow Portfolio shows what would have happened if a blocked decision had been executed |
| **Export Format** | Grafana/Loki/ELK compatible. Structured JSON ready for regulatory submission |
| **Data Integrity** | >91% referential integrity across 45+ PostgreSQL tables |
| **Decision Dataset** | 670,000+ fully traced governance decisions available for audit |

**Compliance Officer Deliverables:**
1. Real-time Decision Audit Dashboard with checkpoint drill-down
2. Exportable Decision Traces (structured JSON, per-decision or bulk)
3. Cryptographically signed records (post-quantum — cannot be altered after the fact)
4. Counterfactual evidence proving governance value with hard numbers

A compliance officer or regulator can request the trace for any decision and receive it in minutes — not weeks.

### Q11: What external services does OMNIX integrate?

**A:**

| Category | Services |
|----------|----------|
| **Trading** | Kraken (crypto), Alpaca (stocks) |
| **AI Models** | Google Gemini 2.0, OpenAI GPT-4o, Anthropic Claude |
| **Data** | CoinGecko, Finnhub, Alpha Vantage, Alternative.me |
| **Infrastructure** | Railway (production), PostgreSQL, Redis |
| **Security** | ANU QRNG (quantum random numbers) |

---

## Compliance & Legal

### Q12: Does OMNIX guarantee returns?

**A:** **No.** OMNIX is a risk control infrastructure, not a return-generation promise. We explicitly state:

- Trading involves significant risk
- Past performance is not indicative of future results
- All metrics shown are from paper trading
- Capital preservation is the primary goal, not maximizing returns

### Q13: Is OMNIX pursuing regulatory compliance?

**A:** Yes. We are preparing for:

- **DIFC/ADGM** licensing in Dubai
- **No tokenization** — This is a SaaS product, not a token sale
- **No "democratizing finance" claims** — We serve advanced users, not retail novices

Our compliance posture is designed for institutional acceptance in regulated markets.

### Q14: Does OMNIX offer Sharia-compliant trading?

**A:** Yes. OMNIX has a built-in Sharia Screening Engine running in production. Specifically:

- **40+ crypto assets evaluated** across 12 categories (PoW, PoS, Stablecoins, DeFi, Meme coins, Islamic Native Coins, NFTs, Gaming tokens, and more)
- **Based on AAOIFI Sharia Standard 62** — the global reference standard for Islamic digital assets
- **Three categories automatically blocked**: Maysir (pure speculation — meme coins), Riba (interest-bearing instruments), Gharar (excessive uncertainty in contracts)
- **Scholarly sources cited per asset**: AAOIFI Standard 62, Mufti Taqi Usmani 2018, Shariyah Review Bureau
- **Real-time screening**: every governance decision includes a Sharia compliance check before execution
- `/sharia [crypto]` command for on-demand verification
- Auditable records synchronized with Risk Guardian

**Examples**: Bitcoin → Halal confirmed (high confidence, AAOIFI Standard 62). Dogecoin, Shiba Inu → Haram blocked (Maysir — pure speculation without utility). Ethereum → Questionable (PoS staking may constitute Riba — scholar debate ongoing).

**What we do NOT claim**: Formal Sharia board certification. That is a separate external process. OMNIX provides structural Sharia-aligned governance screening based on AAOIFI standards — accurate and defensible for GCC institutional investors.

---

## Due Diligence Questions

### Q15: What is OMNIX's data integrity status?

**A:** 
- **Referential integrity**: >91% across 45+ PostgreSQL tables
- **Audit trail**: Complete for all 119 baseline trades + 89,000+ blocked decisions
- **Uptime**: 99.9% since December 2025
- **Data processing**: Real-time 24/7 market data

### Q16: What is the team structure?

**A:** Currently founder-led with plans to expand:

- **Harold A. Nunes** — Founder & Architect (technical development, strategy)
- **Planned hires**: 3 FTE engineers post-funding

### Q17: What is the go-to-market strategy?

**A:**

1. Complete track record validation
2. First enterprise pilot (prop firm or trading platform) — Month 3
3. ADGM regulatory structure complete — Month 6
4. 3 paying enterprise clients — Month 9
5. Series A readiness with validated revenue metrics — Month 12

### Q18: What are the key risks?

**A:**

| Risk | Mitigation |
|------|------------|
| **Market Risk** | Fail-closed architecture, 8-checkpoint entry veto system + EGL exit governance (6 validated through Feb 2026 + 4 gaps closed Mar 2026) |
| **Technology Risk** | 99.9% uptime, redundant infrastructure |
| **Regulatory Risk** | DIFC/ADGM preparation, no token exposure |
| **Execution Risk** | Paper trading validation before live capital |
| **Key Person Risk** | 3-layer mitigation: (1) Documented architecture with 36 ADRs — senior engineer can onboard in 2-3 weeks; (2) First 3 hires Month 1-4 reduce founder dependency from 100% to ~30%; (3) IP assignment to company, key-person insurance, operational runbooks by Month 6 |

---

## Investment Terms

### Q19: What is the current ask?

**A:**

| Term | Value |
|------|-------|
| Round | Pre-Seed |
| Amount | $500,000 |
| Pre-money Valuation | $2.5M–$3M |
| Equity | 16.7% |
| Runway | 12-18 months |

### Q20: How will funds be used?

**A:**

| Allocation | Percentage | Purpose |
|------------|------------|---------|
| Strategy & Risk Engine | 35% | Algorithm refinement, Shadow Portfolio expansion, multi-vertical development |
| Dubai/ADGM Legal & Regulatory | 25% | Company formation, regulatory structure |
| Enterprise Infrastructure | 20% | API for prop firms, security certifications |
| Team & Operations | 15% | 2-3 key hires (Senior Backend, DevOps, Business Development) — eliminating key-person risk |
| Reserve | 5% | Contingency |

**Priority #1 within Team & Operations:** Eliminate single-founder dependency. Senior Backend Engineer (Month 1-2) absorbs core engine knowledge. DevOps (Month 2-3) makes infrastructure founder-independent. By Month 4, no critical function depends on a single person.

---

## Contact

**Harold A. Nunes**  
Founder & Architect  
Available for technical walkthrough and system demo

---

*This document is for informational purposes only and does not constitute an offer to sell or a solicitation of an offer to buy securities. Trading involves significant risk. Past performance is not indicative of future results.*
