# OMNIX — Real-Time Governance Behavior Snapshot

**Status**: Live Conditions — Capital Preservation Mode  
**Date**: February 17, 2026  
**Observation Period**: January 15 – February 17, 2026 (33 days)  
**Vertical**: Digital Asset Trading (First Validated Vertical)  
**Identity**: OMNIX is building the category of Decision Governance Infrastructure — a governance control architecture for automated decision systems.  
**ADR Compliance**: ADR-018 (DCI), ADR-019 (ECW), ADR-023, ADR-027  

---

## 1. Observación Operacional

**The system was technically capable of executing. It chose not to.**

During the last 33 days of live market conditions, OMNIX has continuously evaluated automated trading decisions — and consistently chosen preservation over execution. This is governance by design.

### Layer 1: External Guards

| Guard | Status | Meaning |
|-------|--------|---------|
| Monte Carlo Validation | PASSED | Win rate and expected return meet minimum thresholds |
| RMS (Risk Management) | PASSED | Position limits, circuit breakers — all clear |
| EMA Signal | PASSED | Trend detection active and generating signals |
| Coherence Pre-Gate | PASSED | Minimum coherence filter passed |
| ECW (Edge Confirmation Window) | PASSED | Edge persisted across required consecutive cycles |
| Consensus | PASSED | Module consensus achieved |

**All Layer 1 guards pass.** Most automated systems would execute here.

### Layer 2: Structural Coherence Analysis

After all guards pass, OMNIX runs the Coherence Engine V5.4 and Decision Contradiction Index (DCI) — checking whether **the decision-making system agrees with itself**.

| Metric | Observed Value | Threshold | Result |
|--------|---------------|-----------|--------|
| Coherence Engine Final Verdict | HOLD (BLOCKED) | — | Signals contradict at structural level |
| Decision Contradiction Index (DCI) | **72.9** | < 70 | CONTRADICTORY — preservation mode |
| Local Signal Strength | 21.4 / 40 | — | Weak internal alignment |
| Global Edge Penalty | 29.6 / 30 | — | Near-zero exploitable edge |
| Monte Carlo Win Rate | 50.6% | ≥ 50% | Passes threshold, but barely |
| Monte Carlo Expected Return | ~0.0000 | > 0% | Essentially zero edge |
| Coherence Score | 47% | > 10% (pre-gate) | Passed pre-gate, insufficient for execution |
| Overall Confidence | 58.5% | — | Below actionable threshold |

**Final Decision**: HOLD — Blocked by Coherence Engine (structural signal contradiction detected).

Layer 1 confirms signal availability. Layer 2 finds structural contradiction. DCI above execution threshold. Execution automatically blocked.

---

## 2. What This Means

The governance architecture detected **structural conflict between internal decision signals**:

- **Regime Misalignment**: Trend detection and regime classification pulling in different directions
- **Momentum vs. Reversion Tension**: EMA signals suggest movement, but Monte Carlo simulations show near-zero expected return — the edge is not real
- **Marginal Probability Instability**: Win rate statistically indistinguishable from random — edge structurally insufficient for execution

When DCI exceeds the execution threshold, the system enters capital preservation mode regardless of what individual guards indicate.

### DCI Classification Scale

| Range | Level | System Behavior |
|-------|-------|----------------|
| 0–34 | ALIGNED | High-confidence execution zone |
| 35–69 | TENSIONED | Exercising caution, reduced sizing |
| **70–100** | **CONTRADICTORY** | **Execution blocked** |

---

## 3. Why This Matters

Most automated decision systems operate when they can. OMNIX operates only when it should.

This governance control architecture — first validated in digital asset trading — has evaluated **670,000+ automated decisions and preserved 98.5% of capital** since November 2025. That result is not from prediction. It's from structural discipline.

### The Governance Difference

| System Type | Behavior in Ambiguous Conditions | Result |
|-------------|--------------------------------|--------|
| Traditional Automated Trading | Executes based on individual signal thresholds | Activity without discipline |
| Rule-Based Risk Management | Blocks only on explicit violations | Misses structural conflicts |
| **OMNIX Decision Governance** | **Detects contradiction between signal layers and blocks preemptively** | **Capital preservation by design** |

Behavior consistent across observation window — preservation mode activated systematically under structural contradiction.

---

## 4. How to Use This in Pitch

### Ready-to-Use Statement (English)

> "All external conditions are met. But internally, the Decision Contradiction Index detects that the signals don't agree with each other. DCI above execution threshold — contradictory. So it blocks. Automatically. No human intervention. Governance by design."

### Ready-to-Use Statement (Español)

> "Todas las condiciones externas se cumplen. Pero internamente, el Índice de Contradicción de Decisiones detecta que las señales no están de acuerdo entre sí. DCI por encima del umbral de ejecución — contradictorio. Entonces bloquea. Automáticamente. Sin intervención humana. Gobernanza por diseño."

### Investor Challenge Response

If an investor asks: *"Why isn't the system trading?"*

> "Because it shouldn't be. Internal signals contradict each other — even though all external guards pass. Win rate indistinguishable from random, near-zero expected return. Edge structurally insufficient. The architecture blocks. Same discipline that preserved capital during validation — operating right now."

### Structural Analogy

> "Think of it like a flight control system. All the runway conditions might be clear — visibility, wind, temperature. But if the internal instruments disagree with each other, the system does not authorize takeoff. You don't call that a malfunction. You call that safety architecture."

---

## 5. Slide Visual — Governance in Action

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│              GOVERNANCE IN ACTION                            │
│              Real-Time Production Data                       │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐     │
│  │  LAYER 1: External Guards                           │     │
│  │                                                     │     │
│  │  ✅ Monte Carlo    ✅ RMS    ✅ EMA Signal          │     │
│  │  ✅ Coherence Gate ✅ ECW    ✅ Consensus           │     │
│  │                                                     │     │
│  │  ALL PASSED — System capable of execution           │     │
│  └─────────────────────────────────────────────────────┘     │
│                          │                                   │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────┐     │
│  │  LAYER 2: Structural Coherence Analysis             │     │
│  │                                                     │     │
│  │  DCI above execution threshold                      │     │
│  │  Classification:  CONTRADICTORY                     │     │
│  │                                                     │     │
│  │  ⛔ BLOCKED — Internal signals do not agree         │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
│           ╔═══════════════════════════════════════╗           │
│           ║                                       ║           │
│           ║  Capable of execution.                ║           │
│           ║  Chose preservation.                  ║           │
│           ║                                       ║           │
│           ╚═══════════════════════════════════════╝           │
│                                                              │
│  OMNIX — When systems can act, but choose discipline.        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Slide Notes:** Layer 1 green. Layer 2 red/amber. Central statement in large bold typography.

---

## 6. Post-Eureka Roadmap

| Phase | Action | Rationale |
|-------|--------|-----------|
| Calibration Phase 2 | DCI threshold 70 → 75 | Allow trades with moderate contradiction |
| Asset Expansion | Add 2-3 trading pairs | More opportunities for signal alignment |
| Backtest Validation | 60-90 day historical backtest | Validate before live deployment |
| Voice Interface | OMNIX Voice — hands-free governance interaction | Web-based always-listening interface: speak to OMNIX, get voice responses with real-time governance analysis. Leverages existing TTS/STT infrastructure (Whisper + gTTS/ElevenLabs). |

**Current policy**: Discipline over movement.

**Governance Structure**: See [INSTITUTIONAL_GOVERNANCE_STRUCTURE.md](investor/INSTITUTIONAL_GOVERNANCE_STRUCTURE.md) for the full 3-layer governance framework (Human Authority, Control Architecture, Institutional Expansion).

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

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| Feb 17, 2026 | 1.0 | Initial snapshot. Real production log data from Railway. ADR-027 compliant. |
| Feb 17, 2026 | 1.1 | Framing adjustments: reduced number repetition, moved key statement to top, institutional tone, added slide visual. |
| Feb 17, 2026 | 2.0 | Institutional version: 15-20% text reduction, numbers only in tables/appendix, structural language throughout. Dual-purpose (pitch + due diligence). |

---

*OMNIX — Institutionalizing discipline in automated systems.*
