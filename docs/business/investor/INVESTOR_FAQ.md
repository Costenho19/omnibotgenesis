# OMNIX — Investor FAQ
## Decision Governance Infrastructure

**Classification**: Investor Confidential
**Last Updated**: February 19, 2026

---

## Track Record & Performance

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

**A:** OMNIX uses a 6-tier hierarchical veto system:

```
1. MC VETO → Monte Carlo blocks if Win Rate <50% or Expected Return <0%
2. RMS VETO → Risk Management System enforcement
3. COHERENCE GATE → Blocks if signal agreement <45%
4. ECW GATE → Requires 3 consecutive cycles of edge persistence
5. SCORING → Multi-factor analysis (EMA, HMM, Kalman, Memory, Kelly)
6. DECISION → Only executes if ALL gates pass
```

This is a **fail-closed architecture**: the default is NOT to trade. Capital deployment requires passing every gate.

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

Just as payment infrastructure became necessary before e-commerce could scale, governance infrastructure will become necessary before automated decision systems scale. OMNIX is building this governance layer. The first validated vertical is digital asset trading, with 192,000+ governed decisions and 98.5% of capital preserved.

The right question for investors is not "how much alpha does OMNIX generate?" but "how much capital risk exists in automated systems without governance control?"

---

## Technology & Security

### Q9: What is OMNIX's position on Post-Quantum Cryptography?

**A:** OMNIX has **production-integrated post-quantum cryptography modules** for order signing and key exchange, aligned with NIST 2024 standards:

| Component | Algorithm | NIST Standard | Purpose |
|-----------|-----------|---------------|---------|
| Key Encapsulation | Kyber-768 (ML-KEM-768) | FIPS 203 | Secure key exchange |
| Digital Signatures | Dilithium-3 (ML-DSA-65) | FIPS 204 | Trading order authentication |

**Key facts:**
- Trading orders are signed with Dilithium-3 before execution
- Module located at `omnix_core/security/pqc_security.py`
- Both algorithms provide NIST Level 3 security (~192-bit classical equivalent)
- Protects against future quantum computer attacks

**Important disclaimer:** Currently applied to order authentication and internal security layers. This is not marketed as a compliance guarantee or external security certification.

### Q10: How auditable is the system?

**A:** Every decision is logged with:

- Unique `decision_id` (UUID)
- 11 lifecycle events per trade
- Complete `decision_trace` JSONB with all inputs
- Timestamps, scores, veto reasons

The InstitutionalDecisionLogger V6.5.4 provides Grafana/Loki/ELK compatible audit trails. Data integrity is >91% referential integrity across 45+ PostgreSQL tables.

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

**A:** Yes. We have:

- 40+ crypto assets evaluated for Sharia compliance
- Automatic classification by leverage, liquidity, exposure
- `/sharia [crypto]` command for real-time verification
- Auditable records synchronized with Risk Guardian

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
| **Market Risk** | Fail-closed architecture, 6-tier veto system |
| **Technology Risk** | 99.9% uptime, redundant infrastructure |
| **Regulatory Risk** | DIFC/ADGM preparation, no token exposure |
| **Execution Risk** | Paper trading validation before live capital |
| **Key Person Risk** | Documentation, codebase on GitHub, 25+ ADRs |

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
| Engineering | 40% | Risk system refinement, 3 FTE |
| Infrastructure | 20% | Security audits, scaling |
| Trading Capital | 20% | Live validation phase |
| Legal/Compliance | 10% | DIFC/ADGM preparation |
| Operations | 10% | Reserve, operational costs |

---

## Contact

**Harold A. Nunes**  
Founder & Architect  
Available for technical walkthrough and system demo

---

*This document is for informational purposes only and does not constitute an offer to sell or a solicitation of an offer to buy securities. Trading involves significant risk. Past performance is not indicative of future results.*
