# PROVISIONAL PATENT APPLICATION
## OMNIX-PAT-2026-013

**Title:** REGIME-ADAPTIVE EXIT GOVERNANCE PIPELINE FOR AUTOMATED DECISION SYSTEMS WITH MARKET-CONDITIONED THRESHOLD SCALING, EXIT COHERENCE VALIDATION, AND POST-QUANTUM-SIGNED EXIT RECEIPT GENERATION

**Inventor:** Harold Alberto Nunes Rodelo
**Applicant:** OMNIX QUANTUM LTD
**Filing Basis:** 35 U.S.C. § 111(b)
**Entity Status:** Micro Entity
**Date Prepared:** April 19, 2026
**Date of Filing:** April 19, 2026
**Related Applications:** OMNIX-PAT-2026-001 (Governance Control Architecture), OMNIX-PAT-2026-003 (PQC Auth), OMNIX-PAT-2026-010 (Transparency Chain), OMNIX-PAT-2026-012 (Trajectory Invariant Engine)

---

## FIELD OF THE INVENTION

The present invention relates to automated decision governance systems, and more particularly to a multi-gate exit governance pipeline that applies regime-adaptive threshold scaling, exit coherence validation, and temporal trajectory checking to automated exit decisions — closing the governance gap in which exit events, representing approximately 40% of all capital events in automated decision systems, receive no governance validation equivalent to that applied to entry decisions.

---

## BACKGROUND

### I. THE GOVERNANCE ASYMMETRY PROBLEM

Automated decision systems operating in regulated environments apply multi-checkpoint governance pipelines to entry decisions — decisions to initiate a new position, action, or commitment. These pipelines evaluate candidate decisions against signal quality, probabilistic confidence, risk exposure, coherence, and compliance thresholds before permitting execution.

Exit decisions — decisions to terminate an existing position, action, or commitment — are typically handled by simple threshold comparisons: if the current value exceeds a take-profit threshold, or falls below a stop-loss threshold, exit. No governance checkpoint equivalent to the entry pipeline is applied.

This asymmetry is architecturally significant:

**1.1 Exit Events Are Capital Events:** In automated decision systems, exit decisions represent approximately 40% of all capital events. An automated system that executes 1,000 entry decisions subject to full governance validation also executes approximately 1,000 exit decisions — each of which directly determines the realized gain or loss — subject to no equivalent governance.

**1.2 Fixed Thresholds Are Regime-Blind:** A take-profit threshold set at a fixed percentage above entry price does not account for market regime. In a trending regime, the optimal exit point is materially different from the optimal exit point in a volatile or ranging regime. A fixed threshold that performs well in trending conditions will exit prematurely in trending markets (leaving profit on the table) and too slowly in volatile markets (giving back gains). The regime-blindness of fixed thresholds is a systematic source of governance failure.

**1.3 Exit Coherence Is Not Evaluated:** An exit decision based solely on price comparison does not evaluate whether the exit is coherent with the current directional signal of the system. A system that holds a long position and receives a strong bearish signal should apply different exit logic than a system that holds the same long position with a neutral signal. The relationship between the current signal direction and the position direction is governance-relevant information that fixed-threshold exit systems do not evaluate.

**1.4 Exit Timing Is Not Trajectory-Checked:** The temporal context of an exit decision — whether exit timing is coherent with recent system trajectory — is relevant to governance but is not evaluated by any existing exit mechanism.

**1.5 No Cryptographic Evidence for Exit Decisions:** Entry governance pipelines produce cryptographic receipts as evidence of the governance evaluation. Exit decisions produce no equivalent cryptographic evidence, creating a regulatory audit gap: entry decisions are evidenced; exit decisions are not.

The present invention addresses all five inadequacies through the Exit Governance Layer (EGL).

---

## SUMMARY OF THE INVENTION

The present invention provides an Exit Governance Layer (EGL) comprising a three-gate governance pipeline applied to automated exit decisions. The EGL:

1. Applies regime-adaptive scaling to exit threshold parameters (take-profit and stop-loss) based on the detected market or operational regime, providing regime-conditioned exit governance rather than fixed-threshold comparison.
2. Evaluates exit coherence between the current directional signal and the position direction, providing a signal-coherence veto gate for exit decisions.
3. Optionally evaluates exit timing coherence against recent system trajectory using a temporal coherence validation mechanism.
4. Generates a cryptographically signed exit receipt providing auditable evidence of the governance evaluation for each exit decision, closing the regulatory audit gap between entry and exit evidence.
5. Operates with a fail-safe design that preserves the existing exit behavior on any gate module failure.

---

## DETAILED DESCRIPTION OF THE PREFERRED EMBODIMENTS

### I. ARCHITECTURAL POSITION AND MOTIVATION

The Exit Governance Layer is positioned in the automated decision pipeline at the point where exit decisions are evaluated. It sits between the signal generation / position monitoring layer and the execution layer:

```
Position Monitor → Exit Candidate → EGL (3-gate pipeline) → Exit Receipt → Execution Layer
```

The EGL is complementary to the entry governance pipeline (OMNIX-PAT-2026-001). Together, the entry pipeline and the EGL provide symmetric governance coverage over all capital events: every entry decision is governed before execution; every exit decision is governed before execution.

The EGL is applicable to any domain in which automated systems manage ongoing commitments with defined exit conditions, including but not limited to: algorithmic trading (take-profit and stop-loss exits), clinical decision support (treatment discontinuation decisions), autonomous robotics (mission abort and position release decisions), energy grid management (dispatch termination decisions), and insurance underwriting (policy termination trigger evaluation).

### II. GATE 1 — REGIME-ADAPTIVE THRESHOLD SCALING

Gate 1 transforms fixed take-profit and stop-loss threshold parameters into regime-conditioned dynamic thresholds based on the detected operational regime.

#### II.A. Regime Detection

The detected regime is provided to the EGL as an input parameter from the upstream signal analysis layer. In one embodiment, the regime is classified from a set including but not limited to: TRENDING, UPTREND, BULLISH, RANGING, NEUTRAL, VOLATILE, DOWNTREND, BEARISH.

#### II.B. Threshold Scaling Multipliers

Take-profit and stop-loss thresholds are scaled by regime-specific multipliers. In one embodiment, the multipliers are as follows:

**Take-profit multipliers by regime:**
- TRENDING / UPTREND: in one embodiment ×1.3 (let winners run in trending markets)
- BULLISH: in one embodiment ×1.2
- RANGING / NEUTRAL: in one embodiment ×0.8 to ×1.0 (take profits earlier in range-bound conditions)
- VOLATILE: in one embodiment ×0.7 (tighter profit target in high-volatility conditions)
- DOWNTREND / BEARISH: in one embodiment ×0.6 to ×0.8 (most conservative in adverse regimes)

**Stop-loss multipliers by regime:**
- TRENDING / UPTREND: in one embodiment ×0.8 (tighter stop in trending markets — less noise tolerance needed)
- RANGING: in one embodiment ×1.2 (wider stop in range-bound conditions — more noise tolerance required)
- VOLATILE: in one embodiment ×0.7 (tighter stop in high-volatility conditions — rapid adverse moves)
- DOWNTREND / BEARISH: in one embodiment ×0.6 to ×0.85 (most conservative in adverse regimes)

In other embodiments, the multiplier tables may be configured to any set of values appropriate to the operational domain, including domain-specific multiplier tables for non-financial applications.

#### II.C. Gate 1 Verdict

Gate 1 produces a regime-adjusted take-profit price and a regime-adjusted stop-loss price. The Gate 1 verdict is PASS if the current price satisfies the regime-adjusted threshold conditions for exit (i.e., regime-adjusted-TP ≤ current price, or current price ≤ regime-adjusted-SL). The Gate 1 verdict is HOLD if the current price does not satisfy the regime-adjusted exit conditions.

The regime-adjusted thresholds replace the fixed thresholds for all downstream gate evaluations in the current EGL cycle.

### III. GATE 2 — EXIT COHERENCE GATE

Gate 2 evaluates whether the proposed exit is coherent with the current directional signal of the system and the direction of the existing position.

#### III.A. Signal-Direction Alignment

Gate 2 receives as inputs:
- The current directional signal (e.g., BULLISH, BEARISH, NEUTRAL, from the upstream signal analysis layer)
- The direction of the existing position (e.g., LONG, SHORT, LONG_EQUIVALENT, SHORT_EQUIVALENT)

The gate evaluates whether the proposed exit is supported by signal-direction alignment. In one embodiment, the evaluation logic is:

- **Supportive alignment:** The directional signal contradicts the position direction (e.g., a BEARISH signal while holding a LONG position, or a BULLISH signal while holding a SHORT position). In this case, the signal provides directional support for exiting the position, and Gate 2 returns PASS.
- **Contradictory alignment:** The directional signal agrees with the position direction (e.g., a BULLISH signal while holding a LONG position that is near its stop-loss). In this case, the signal provides no directional support for exiting, and Gate 2 may return HOLD depending on other conditions.
- **Neutral alignment:** The directional signal is neutral or ambiguous. Gate 2 applies a configurable default (in one embodiment: PASS on neutral signals to avoid blocking exits when no directional information is available).

#### III.B. Confidence Weighting

In one embodiment, the Exit Coherence Gate weights the signal-direction alignment verdict by the confidence level of the current directional signal. A high-confidence contradictory signal provides stronger support for exit than a low-confidence contradictory signal. The weighted verdict contributes to the composite exit confidence score.

#### III.C. Gate 2 Verdict

Gate 2 produces a boolean verdict (PASS or HOLD) and a confidence contribution. Gate 2 HOLD does not unconditionally block exit — it is combined with Gate 1 and Gate 3 verdicts to produce the final EGL decision.

### IV. GATE 3 — TEMPORAL TRAJECTORY COHERENCE CHECK

Gate 3 applies a temporal coherence validation mechanism to evaluate whether the timing of the proposed exit is coherent with the recent trajectory of the system.

Gate 3 reuses the Temporal Coherence Validation (TCV) module (described in OMNIX-PAT-2026-014) in exit-specific mode. The TCV evaluates whether the exit timing is consistent with the directional trend, regime alignment, and signal stability observed in recent system history.

Gate 3 is designated optional in the preferred embodiment: if the TCV module is unavailable or produces an error, Gate 3 returns a pass-through result that does not block exit, and the final EGL decision is based on Gates 1 and 2 alone.

### V. EXIT RECEIPT GENERATION

Upon completion of all gate evaluations, the EGL generates a cryptographically signed exit receipt for each evaluated exit decision. The exit receipt provides auditable evidence equivalent to the entry governance receipt produced by the entry checkpoint pipeline.

#### V.A. Exit Receipt Content

The exit receipt comprises:
- **exit_receipt_id:** Unique identifier (in one embodiment: UUID v4)
- **asset / domain:** Operational entity identifier
- **position identifier:** Reference to the position or commitment being exited
- **gate verdicts:** Results of Gate 1, Gate 2, and Gate 3 (boolean + rationale)
- **regime_used:** The operational regime applied in Gate 1
- **regime_adjusted_tp / sl:** The adjusted thresholds computed in Gate 1
- **composite_confidence:** Weighted composite confidence score [0–100]
- **should_exit:** Final EGL decision
- **timestamp:** UTC ISO-8601 evaluation timestamp

#### V.B. Cryptographic Signature

In one embodiment, the exit receipt is signed using a post-quantum digital signature scheme (Dilithium-3, ML-DSA-65, NIST FIPS 204). In other embodiments, any cryptographic signing scheme may be applied, including classical or hybrid classical+post-quantum schemes. The signing provider identifier is embedded in the receipt for algorithm-bound verification.

The signed exit receipt may be submitted to a transparency chain (OMNIX-PAT-2026-010) for tamper-evident audit logging.

### VI. FAIL-SAFE DESIGN

The EGL implements a fail-safe design principle: on any module failure, exception, or gate evaluation error, the EGL returns the existing exit decision (the naive price-comparison result) unchanged. The fail-safe result is flagged with a `pass_through: true` indicator for audit purposes.

This design ensures that EGL's failure mode is identical to its absence — the system continues to operate using the existing exit logic without the EGL's governance enhancements. No new failure modes are introduced by the presence of the EGL.

### VII. COMPOSITE EXIT CONFIDENCE SCORE

The EGL computes a composite exit confidence score [0–100] by combining the verdicts and confidence contributions of all three gates. In one embodiment:

- Gate 1 contributes: 50% weight (primary exit condition)
- Gate 2 contributes: 30% weight (coherence validation)
- Gate 3 contributes: 20% weight (temporal trajectory check, when available)

In other embodiments, the weighting of gate contributions is configurable.

### VIII. ALTERNATIVE EMBODIMENTS

**8.1 Domain-Specific Regime Tables:** The regime multiplier tables of Gate 1 may be replaced with domain-specific tables appropriate to non-financial applications, including clinical treatment discontinuation thresholds, robotic mission abort criteria, or energy dispatch termination parameters.

**8.2 Additional Gates:** The three-gate pipeline may be extended with additional gates, including jurisdiction-specific exit compliance checks, cross-asset exit correlation analysis, or regulatory reporting gates.

**8.3 Continuous vs. Binary Verdicts:** In one embodiment, gate verdicts are binary (PASS/HOLD). In other embodiments, gates produce continuous scores that are combined into a composite exit admissibility score, with the final decision based on whether the composite score exceeds a configurable threshold.

**8.4 Symmetric Governance Coverage:** In one embodiment, the EGL integrates with the entry governance pipeline (OMNIX-PAT-2026-001) such that every position or commitment has an associated entry receipt and an associated exit receipt, providing complete symmetric governance coverage over the full lifecycle of every automated decision.

---

## CLAIMS

**Claim 1 (Broad — Core EGL)** — A computer-implemented exit governance pipeline for automated decision systems, comprising: a regime-adaptive threshold scaling gate that adjusts exit threshold parameters based on a detected operational regime; an exit coherence gate that evaluates directional alignment between a current signal and a position direction; and a receipt generation module that produces a cryptographically signed exit receipt documenting the governance evaluation of each exit decision.

**Claim 2 (Broad — Regime Scaling)** — The system of Claim 1, wherein the regime-adaptive threshold scaling gate transforms fixed exit thresholds into regime-conditioned dynamic thresholds by applying regime-specific scaling multipliers, such that in one embodiment a trending regime applies a take-profit multiplier greater than 1.0 and a stop-loss multiplier less than 1.0, and a volatile regime applies both multipliers less than 1.0.

**Claim 3 (Specific — Multiplier Table)** — The system of Claim 2, wherein regime-specific scaling multipliers are stored in a configurable mapping from operational regime identifiers to take-profit and stop-loss multiplier pairs, enabling domain-specific calibration of exit threshold scaling without modification of the gate logic.

**Claim 4 (Broad — Exit Coherence Gate)** — The system of Claim 1, wherein the exit coherence gate evaluates whether a current directional signal supports or contradicts the direction of an existing position, and wherein said evaluation contributes to a composite exit confidence score weighted by the confidence level of the current directional signal.

**Claim 5 (Broad — Temporal Gate)** — The system of Claim 1, further comprising a temporal trajectory coherence gate that evaluates whether exit timing is coherent with the recent trajectory of system decisions, wherein said gate is designated fail-safe and produces a pass-through result on any evaluation error without blocking exit.

**Claim 6 (Broad — PQC Exit Receipt)** — The system of Claim 1, wherein the receipt generation module produces a cryptographically signed exit receipt comprising gate verdicts, regime-adjusted thresholds, composite confidence score, and evaluation timestamp, and wherein in one embodiment the receipt is signed using a post-quantum digital signature scheme.

**Claim 7 (Broad — Symmetric Coverage)** — The system of Claim 1, wherein the exit governance pipeline provides symmetric governance coverage with an entry governance pipeline, such that every automated commitment generates both an entry governance receipt upon initiation and an exit governance receipt upon termination.

**Claim 8 (Broad — Fail-Safe)** — The system of Claim 1, wherein any failure of any gate in the exit governance pipeline produces a pass-through result that returns the existing exit decision unchanged, with a pass-through indicator recorded in the exit receipt for audit purposes.

**Claim 9 (Broad — Composite Score)** — The system of Claim 1, wherein a composite exit confidence score is computed by combining the verdicts and confidence contributions of the regime-adaptive gate, exit coherence gate, and temporal trajectory gate, with configurable weighting of each gate's contribution.

**Claim 10 (Broad — Method)** — A computer-implemented method for governed exit decision evaluation in automated decision systems, comprising: receiving an exit candidate and an operational regime identifier; computing regime-adjusted exit thresholds by applying regime-specific scaling multipliers to base threshold parameters; evaluating directional coherence between the current system signal and the position direction; optionally evaluating temporal trajectory coherence of the exit timing; combining gate verdicts into a composite exit decision; and generating a cryptographically signed exit receipt documenting the governance evaluation.

---

## ABSTRACT

A regime-adaptive exit governance pipeline closes the governance asymmetry in automated decision systems in which entry decisions receive full multi-checkpoint governance validation while exit decisions — representing approximately 40% of all capital events — receive only naive fixed-threshold comparison. The pipeline comprises three sequential gates applied to each exit candidate: Gate 1 applies regime-conditioned scaling multipliers to transform fixed take-profit and stop-loss thresholds into dynamic thresholds appropriate for the detected operational regime (in one embodiment: trending regime applies take-profit multiplier of ×1.3 and stop-loss multiplier of ×0.8; volatile regime applies both multipliers of ×0.7); Gate 2 evaluates directional coherence between the current system signal and the position direction, providing a signal-supported veto of incoherent exits; Gate 3 optionally applies temporal trajectory coherence validation to evaluate exit timing against recent system trajectory. Upon gate evaluation, a cryptographically signed exit receipt is generated (in one embodiment using a post-quantum digital signature scheme), providing auditable governance evidence equivalent to entry governance receipts and closing the regulatory audit gap between entry and exit decision records. The pipeline implements fail-safe design: any gate failure returns the existing exit decision unchanged with a pass-through indicator. Applications include algorithmic trading, clinical decision support, autonomous robotics, energy grid management, and any regulated automated decision domain with distinct initiation and termination events. To the inventor's knowledge, this is the first system applying multi-gate governance with regime-adaptive threshold scaling and post-quantum-signed receipt generation specifically to exit decisions in automated governance pipelines.

---

## DRAWINGS

```
FIG. 1 — Exit Governance Layer Architecture

  Position Monitor
        │
  Current Price + Regime + Signal + Position
        │
        ▼
  ┌─────────────────────────────────────────────┐
  │           EXIT GOVERNANCE LAYER             │
  │                                             │
  │  Gate 1: Regime-Adaptive Threshold Scaling  │
  │    TP_base × regime_tp_multiplier = TP_adj  │
  │    SL_base × regime_sl_multiplier = SL_adj  │
  │    price vs TP_adj / SL_adj → verdict       │
  │                    ↓                        │
  │  Gate 2: Exit Coherence Gate                │
  │    signal_direction ↔ position_direction    │
  │    confidence-weighted alignment → verdict  │
  │                    ↓                        │
  │  Gate 3: TCV Exit Check (optional)          │
  │    exit timing vs trajectory history        │
  │    → verdict (pass-through on error)        │
  │                    ↓                        │
  │  Composite Confidence Score                 │
  │  Exit Receipt (PQC-signed)                  │
  └──────────────────┬──────────────────────────┘
                     │
              should_exit: bool
              exit_receipt_id
              pqc_signature

FIG. 2 — Regime-Adaptive Threshold Scaling (Gate 1)

  Regime       TP Multiplier   SL Multiplier   Effect
  ─────────────────────────────────────────────────────────────
  TRENDING     ×1.3            ×0.8            Let winners run
  BULLISH      ×1.2            ×0.85           Optimistic
  NEUTRAL      ×1.0            ×1.0            Baseline
  RANGING      ×0.8            ×1.2            Quick take, wide stop
  VOLATILE     ×0.7            ×0.7            Tight on both
  BEARISH      ×0.6            ×0.6            Most conservative

  Example: TP_base = $105, Regime = VOLATILE
  TP_adj = $105 × 0.7 = $73.50
  SL_adj = SL_base × 0.7

FIG. 3 — Governance Symmetry

  ENTRY DECISION                    EXIT DECISION
  ──────────────                    ─────────────
  8-checkpoint pipeline             3-gate EGL pipeline
  PQC-signed entry receipt          PQC-signed exit receipt
  Transparency chain entry          Transparency chain entry
  ──────────────────────────────────────────────────────────
  100% governance coverage over complete decision lifecycle
```
