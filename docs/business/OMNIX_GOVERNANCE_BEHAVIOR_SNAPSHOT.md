# OMNIX — Real-Time Governance Behavior Snapshot

**Status**: Live Conditions — Capital Preservation Mode  
**Date**: February 17, 2026  
**Observation Period**: January 15 – February 17, 2026 (33 days)  
**Vertical**: Digital Asset Trading (First Validated Vertical)  
**Identity**: OMNIX is building the category of Decision Governance Infrastructure — a governance control architecture for automated decision systems.  
**ADR Compliance**: ADR-018 (DCI), ADR-019 (ECW), ADR-023, ADR-027  

---

## 1. Observación Operacional

During the last 33 days of live market conditions, OMNIX has been continuously evaluating automated trading decisions — and consistently choosing NOT to execute.

This is not a malfunction. This is governance.

### What the System Sees — Layer 1: External Guards

| Guard | Status | Meaning |
|-------|--------|---------|
| Monte Carlo Validation | PASSED | Win rate (50.6%) and expected return meet minimum thresholds |
| RMS (Risk Management) | PASSED | Position limits, circuit breakers — all clear |
| EMA Signal | PASSED | Trend detection active and generating signals |
| Coherence Pre-Gate | PASSED | Minimum coherence filter passed (47% vs 10% threshold) |
| ECW (Edge Confirmation Window) | PASSED | Edge persisted across required consecutive cycles |
| Consensus | PASSED | Module consensus achieved |

**All Layer 1 guards pass.** The system has cleared every individual threshold check. Most automated systems would execute here.

### What Blocks Execution — Layer 2: Structural Coherence Analysis

After all guards pass, OMNIX runs a deeper analysis: the Coherence Engine V5.4 and Decision Contradiction Index (DCI). This second layer doesn't check if individual rules are met — it checks whether **the decision-making system agrees with itself**.

| Metric | Observed Value | Threshold | Result |
|--------|---------------|-----------|--------|
| Coherence Engine Final Verdict | HOLD (BLOCKED) | — | Signals contradict at structural level |
| Decision Contradiction Index (DCI) | **72.9** | < 70 | CONTRADICTORY — preservation mode |
| Local Signal Strength | 21.4 / 40 | — | Weak internal alignment |
| Global Edge Penalty | 29.6 / 30 | — | Near-zero exploitable edge |
| Monte Carlo Win Rate | 50.6% | ≥ 50% | Passes threshold, but barely |
| Monte Carlo Expected Return | ~0.0000 | > 0% | Essentially zero edge |
| Coherence Score | 47% | > 10% (pre-gate) | Passed pre-gate, but insufficient for execution |
| Overall Confidence | 58.5% | — | Below actionable threshold |

**Final Decision**: HOLD — Blocked by Coherence Engine (structural signal contradiction detected).

The coherence pre-gate (Layer 1) confirms that the system is not broken — signals exist and exceed the minimum filter. But the Coherence Engine (Layer 2) analyzes how those signals relate to each other and finds structural contradiction. The DCI score of 72.9 quantifies this: the decision-making system does not agree with itself. Execution is automatically blocked.

---

## 2. What This Means

This is not inactivity. This is not a failure to find opportunities.

This is **structural conflict detection** between internal decision signals:

- **Regime Misalignment**: Trend detection and regime classification are pulling in different directions (TRENDING regime with 15-point penalty + MEDIUM risk at 7 points)
- **Momentum vs. Reversion Tension**: EMA signals suggest movement, but Monte Carlo simulations show near-zero expected return — the edge is not real
- **Marginal Probability Instability**: Win rate at 50.6% is statistically indistinguishable from a coin flip — the system recognizes this is not a tradeable edge

The DCI captures all of this in a single score. When that score exceeds 70, the system enters capital preservation mode regardless of what individual guards indicate.

### DCI Score Decomposition (Real Data)

| Component | Points | Max | What It Measures |
|-----------|--------|-----|------------------|
| Local Signal Strength | 21.4 | 40 | How strongly individual signals agree (NM confidence + EMA confidence) |
| Global Edge Penalty | 29.6 | 30 | How little exploitable edge exists (based on MC win rate and expected return) |
| Regime Misalignment | 15 | 15 | Whether market regime supports the trade direction |
| Risk Overlay | 7 | 15 | Black Swan severity level (MEDIUM) |
| **Total DCI** | **72.9** | **100** | **CONTRADICTORY — capital preservation mode** |

### DCI Classification Scale

| Range | Level | System Behavior |
|-------|-------|----------------|
| 0–34 | ALIGNED | All signals converging — high-confidence execution zone |
| 35–69 | TENSIONED | Mixed signals detected — exercising caution, reduced sizing |
| **70–100** | **CONTRADICTORY** | **Significant internal conflict — execution blocked** |

---

## 3. Why This Matters

Most automated decision systems operate when they can. OMNIX operates only when it should. This governance control architecture — first validated in digital asset trading — has evaluated 192,000+ automated decisions and preserved 98.5% of capital. That result is not from prediction. It's from structural discipline.

### The Governance Difference

| System Type | Behavior in Ambiguous Conditions | Result |
|-------------|--------------------------------|--------|
| Traditional Automated Trading | Executes based on individual signal thresholds | Activity without discipline |
| Rule-Based Risk Management | Blocks only on explicit violations (drawdown, position limits) | Misses structural conflicts |
| **OMNIX Decision Governance Infrastructure** | **Detects contradiction between signal layers and blocks preemptively** | **Capital preservation by design** |

The DCI does not check if rules are broken. It checks whether **the decision-making system agrees with itself**. If it doesn't, the fail-closed architecture activates automatically — as demonstrated by the 192,000+ decisions governed and 98.5% capital preserved since November 2025.

### Operational Evidence

Running 24/7 in production since November 2025, with fail-closed behavior activated consistently:

- **192,000+** automated decisions evaluated through the governance architecture
- **98.5%** of capital preserved under disciplined risk conditions
- **Zero** manual overrides — all blocks are automatic
- **Continuous operation** across volatile and stable market regimes

The architecture is not optimized for activity. It is optimized for discipline.

---

## 4. How to Use This in Pitch

### Ready-to-Use Statement (English)

> "Right now, the system could be executing. All external conditions are met — Monte Carlo, risk management, edge confirmation, all passing. But internally, the Decision Contradiction Index detects that the signals don't agree with each other. Score: 72.9 out of 100 — classified as contradictory. So it blocks. Automatically. No human intervention. That's not inactivity — that's governance in action."

### Ready-to-Use Statement (Español)

> "En este momento, el sistema podría estar ejecutando. Todas las condiciones externas se cumplen — Monte Carlo, gestión de riesgo, confirmación de edge, todo pasa. Pero internamente, el Índice de Contradicción de Decisiones detecta que las señales no están de acuerdo entre sí. Score: 72.9 de 100 — clasificado como contradictorio. Entonces bloquea. Automáticamente. Sin intervención humana. Eso no es inactividad — es gobernanza en acción."

### Investor Challenge Response

If an investor asks: *"Why isn't the system trading?"*

> "Because it shouldn't be. The system has evaluated over 192,000 decisions since November 2025. When internal signals contradict each other — even when external guards pass — the architecture blocks execution. A 50.6% win rate with near-zero expected return is not a tradeable edge. The system knows this. That discipline is why 98.5% of capital was preserved during the initial validation period — and why the governance architecture continues to block in current conditions."

### Structural Analogy

> "Think of it like a flight control system. All the runway conditions might be clear — visibility, wind, temperature. But if the internal instruments disagree with each other, the system does not authorize takeoff. You don't call that a malfunction. You call that safety architecture."

---

## 5. Post-Eureka Roadmap (For Reference Only)

This section documents the planned calibration adjustments **after** Eureka Dubai competition. No changes will be made before competition.

| Phase | Action | Rationale |
|-------|--------|-----------|
| Calibration Phase 2 | Consider DCI threshold from 70 → 75 (conservative) | Allow trades with moderate contradiction |
| Asset Expansion | Add 2-3 additional trading pairs | More opportunities for signal alignment |
| Backtest Validation | 60-90 day historical backtest with adjusted parameters | Validate before live deployment |
| Documentation | New dataset labeled "Calibration Phase 2" | Maintain full audit trail |

**Current policy**: Protect integrity over generating trades. Win the category, not the activity metric. Discipline over movement.

---

## Appendix: Raw Log Evidence

**Source**: Railway production logs — February 16-17, 2026

```
[2026-02-17 06:05:43] GUARDS_PASSED: MONTE_CARLO, RMS, EMA_SIGNAL, COHERENCE_GATE, ECW_GATE, CONSENSUS

[2026-02-17 06:05:43] Coherence: PASSED (47% vs 10% threshold)
[2026-02-17 06:05:43] → Action: HOLD (BLOCKED by COHERENCE)

[2026-02-17 06:05:43] DECISION_CONTRADICTION_INDEX:
[2026-02-17 06:05:43]    - Score: 72.9 (CONTRADICTORY)
[2026-02-17 06:05:43]    - Local strength: 21.4 (NM=63%, EMA=44%)
[2026-02-17 06:05:43]    - Edge penalty: 29.6 (WR=50.6%, ER=0.0000)
[2026-02-17 06:05:43]    - Regime: TRENDING (15pts) | Risk: MEDIUM (7pts)
[2026-02-17 06:05:43]    → Significant internal conflict - capital preservation mode

[2026-02-17 06:05:43] Análisis V5.2 completado: HOLD - Confianza: 58.5%
```

**Observation frequency**: Guards passing consistently every ~60 seconds during observation window. DCI blocking consistently at 72-73 range.

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| Feb 17, 2026 | 1.0 | Initial snapshot. Real production log data from Railway. ADR-027 compliant. |

---

*OMNIX — governing decisions under uncertainty.*
