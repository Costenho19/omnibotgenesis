# OMNIX – EXECUTIVE FACT SHEET

**Phase 1 — Institutional Validation**  
**Version**: 2.1  
**Issue Date**: 29 March 2026 · **Last Updated**: May 2026  
**Platform Identity**: Decision Governance Infrastructure for Automated Systems  
**ADR Count**: 171 ADRs (57 as of March 2026 — see evolution table §3)  
**Pipeline**: 11 Checkpoints + CAG + TIE (13 governance layers total)  
**Active Verticals**: 10 domains live (Trading · Islamic Credit · Insurance · Robotics · Medical AI · Energy · Real Estate · Agents · Stablecoin · Defense)  

---

## 1. SYSTEM STATUS — MARCH 2026

As of March 29, 2026, OMNIX operates as a multi-vertical governance platform with three independent governance engines running simultaneously 24/7:

| Engine | Domain | Cycle | Live Since |
|--------|---------|-------|-----------|
| **Trading Governance** | Digital asset trading (BTC, ETH, SOL) | 90 seconds | January 15, 2026 |
| **Islamic Credit Governance** | UAE/GCC credit applications (Murabaha, Ijara) | 5 minutes | March 27, 2026 |
| **Insurance Governance** | Global insurance claims (Auto, Property, Health, Cyber) | 4 minutes | March 29, 2026 |
| **Robotics Governance** | Pre-execution robot action safety | 3 minutes | March 29, 2026 |

Every decision across all engines passes through the same 11-checkpoint pipeline and receives a post-quantum cryptographically signed, independently verifiable governance receipt.

---

## 2. THE PIPELINE — 13 GOVERNANCE LAYERS

```
INPUT
  ↓
[CAG] Context Admission Gate — Is the global environment admissible?
  ↓
[EBIP·ACV] Admissibility Consistency — Do input signals contradict each other?
  ↓
[CP-0]  SIV    Signal Integrity Validator       — Data quality, freshness, completeness
[CP-1]  PROB   Monte Carlo Probability          — Win rate ≥ 48%, Expected Return > 0%
[CP-2]  RISK   Risk Limits                      — Position sizing, drawdown controls
[CP-3]  COH    Coherence Engine (DCI < 70)      — Internal signal alignment
[CP-4]  TREND  Trend Analysis                   — EMA + HMM regime confirmation
[CP-5]  STRESS Stress Resilience                — Black Swan detection, tail-risk
[CP-6]  SHAR   Sharia Governance Gate           — Halal screening, Riba/Gharar control
[CP-7]  TCV    Temporal Coherence Validation    — Backward-looking consistency
[CP-7b] FTI    Forward Trajectory Implicator    — Forward multi-step implications
[CP-8]  ECW    Edge Confirmation Window         — Persistence requirement (2+ cycles)
[CP-9]  AML    Anti-Money Laundering Gate       — FATF Rec.15, UAE AML/CFT, FinCEN
[CP-10] FRAUD  Fraud Detection Gate             — EU AI Act Art.6, MiFID II, SEC 10b-5
[CP-11] JUR    Jurisdiction Compliance Gate     — UAE/EU/US/GCC asset validation
  ↓
[TIE] Trajectory Invariant Enforcement — Is the trajectory of decisions safe?
  ↓
PQC-SIGNED RECEIPT (Dilithium-3 + Merkle hash chain)
  ↓
APPROVED | HOLD | BLOCKED
```

**All 13 layers are fail-closed**: if a layer encounters an unhandled exception, it defaults to BLOCKED — never passes through silently.

---

## 3. ARCHITECTURAL TIMELINE

```
CALIBRATION                OFFICIAL DAY 1         GAP CLOSURE            MULTI-VERTICAL
Nov 2025 – Jan 14, 2026 → Jan 15, 2026       → Mar 6, 2026        → Mar 29, 2026
─────────────────────────  ───────────────────  ────────────────────  ─────────────────
119 test trades            Track record begins  8 CP + 3-gate EGL    11 CP + CAG + TIE
Veto system calibrated     Starting capital     SIV, FTI, RCK, EGL   3 verticals live
Risk engine tuned          $984,801.27          36 ADRs               57 ADRs
                                                1 vertical            $137B+ TAM
```

---

## 4. PRODUCTION METRICS (Through February 2026 — Trading Vertical)

| Metric | Value | Notes |
|--------|-------|-------|
| PQC-Signed Receipts | 82,569+ | Dilithium-3, 100% coverage |
| Evaluation Cycles | 766,741+ | Motor running 24/7 since Jan 2026 |
| Capital Preserved | 98.42% | During BTC −7.37% drawdown |
| Governance Receipts Integrity | 100% | Hash chain: zero breaks |
| Check Interval | 90 seconds | Optimized from ~20s (Feb 2026) |
| B2B Payload Encryption | Active | Fernet AES-128-CBC + HMAC-SHA256 |

---

## 5. TAM — THREE VERTICALS NOW, THREE MORE PLANNED

| Vertical | Status | Market Size | Governance Problem |
|----------|--------|-------------|-------------------|
| **Digital Asset Trading** | Live | $5B | Uncontrolled automated execution |
| **Islamic Credit (UAE/GCC)** | Live | $2T AUM | Sharia-compliant credit at scale |
| **Insurance Claims** | Live | $7T+ premiums | Fraudulent claim approval |
| **Robotics / Autonomous** | Live | $80B | Pre-execution safety governance |
| Supply Chain (planned) | Year 2–3 | $20B | Supplier decision integrity |
| Energy Trading (planned) | Year 2–3 | $10B | Grid dispatch governance |

**Total demonstrable TAM: $137B+**

---

## 6. CRYPTOGRAPHIC INFRASTRUCTURE

Implemented since November 2025. Unchanged. Always active.

| Layer | Technology |
|-------|-----------|
| Decision signatures | NIST-standardized post-quantum signature algorithm |
| Key encapsulation | NIST-standardized post-quantum KEM (X25519 hybrid) |
| Payload encryption | AES-256 (Fernet) at rest |
| Timestamp | RFC 3161-style internal timestamp |
| Integrity chain | Rolling Merkle root — tamper-evident |
| Public verification | SHA-256 hash + signature check — zero internal data exposure |

---

## 7. GOVERNANCE STATEMENT

> "Three domains. One governance engine. Every decision cryptographically signed."

OMNIX doesn't optimize returns. It governs the conditions under which any automated system is permitted to act. When those conditions aren't met — across trading, credit, insurance, or robotics — no action forms.

**What appears on the dashboard is not a demo. It is governed decision-making, 24/7, across four simultaneous domains.**

---

## 8. INVESTMENT THESIS

**Seeking**: $500,000 USD pre-seed  
**Equity**: 16.7%  
**Pre-money valuation**: $3,000,000  
**Use of funds**: Team expansion · Institutional sales (UAE/GCC/EU) · Pilot client acquisition  

The governance infrastructure is built. The pipeline is running. The receipts are being generated. The question is no longer "can OMNIX govern multiple domains?" — the answer is already operational across four simultaneous governance engines.

---

## 9. DUE DILIGENCE DOCUMENTS

| Document | Content |
|----------|---------|
| `docs/business/investor/OMNIX_INVESTOR_UPDATE_MAR2026.md` | Complete March 2026 update with all technical detail |
| `docs/business/investor/PRODUCT_OVERVIEW.md` | Platform description for investors |
| `docs/business/investor/INVESTOR_FAQ.md` | Q&A for investor conversations |
| `docs/compliance/SECURITY_OVERVIEW.md` | Public security narrative |
| `docs/compliance/CRYPTOGRAPHIC_ARCHITECTURE_OVERVIEW.md` | Institutional PQC overview |
| `docs/compliance/audits/OMNIX_Security_Audit_v1.0_INTERNAL.md` | Full internal audit |
| `docs/reference/adr/` | 57 Architecture Decision Records (immutable) |

---

## References — March 2026 ADRs

| ADR | Title |
|-----|-------|
| ADR-045 | Execution Boundary Integrity Protocol (EBIP) |
| ADR-046 | Sharia Governance Gate (CP-6) |
| ADR-047 | AML Governance Gate (CP-9) |
| ADR-048 | Fraud Detection Gate (CP-10) |
| ADR-049 | Jurisdiction Compliance Gate (CP-11) |
| ADR-050 | Context Admission Gate (CAG) |
| ADR-051 | Dual Trading Mode (CORE/ACTIVE) |
| ADR-052 | Islamic Credit Governance Vertical |
| ADR-053 | Trajectory Invariant Enforcement (TIE) |
| ADR-054 | Insurance Governance Vertical |
| ADR-055 | Robotics Governance Vertical |
