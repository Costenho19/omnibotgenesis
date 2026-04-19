# PROVISIONAL PATENT APPLICATION
## OMNIX-PAT-2026-014

**Title:** BIDIRECTIONAL TEMPORAL ADMISSIBILITY SYSTEM FOR AUTOMATED GOVERNANCE DECISIONS WITH RETROSPECTIVE TRAJECTORY COHERENCE SCORING, PROSPECTIVE REGIME TRANSITION RISK EVALUATION USING HIDDEN MARKOV MODEL TRANSITION MATRICES, AND DUAL-SOURCE UNBIASED HISTORY ANALYSIS

**Inventor:** Harold Alberto Nunes Rodelo
**Applicant:** OMNIX QUANTUM LTD
**Filing Basis:** 35 U.S.C. § 111(b)
**Entity Status:** Micro Entity
**Date Prepared:** April 19, 2026
**Date of Filing:** April 19, 2026
**Related Applications:** OMNIX-PAT-2026-001 (Governance Control Architecture), OMNIX-PAT-2026-012 (Trajectory Invariant Engine), OMNIX-PAT-2026-013 (Exit Governance Layer)

---

## FIELD OF THE INVENTION

The present invention relates to automated decision governance systems, and more particularly to a bidirectional temporal admissibility system that determines whether a proposed governance decision is temporally admissible by simultaneously evaluating retrospective trajectory coherence — whether the proposed decision is consistent with the recent history of the system — and prospective trajectory implication — whether the proposed decision is consistent with the likely near-future trajectory of the system as estimated by a Hidden Markov Model regime transition matrix. The combined bilateral temporal assessment constitutes a governance checkpoint that extends the admissibility determination from the current instant to both the recent past and the probable near future.

---

## BACKGROUND

### I. LIMITATIONS OF INSTANTANEOUS GOVERNANCE VALIDATION

Multi-checkpoint governance pipelines for automated decision systems evaluate each proposed decision against a set of criteria that reflect the current state of the system: signal quality, probabilistic confidence, risk exposure, compliance thresholds, and coherence metrics. This evaluation is instantaneous — it considers the system's current state but not its trajectory through time.

Instantaneous validation has a fundamental limitation: a decision may be valid at the current instant but inconsistent with either (a) the trajectory from which the system has arrived at the current state, or (b) the likely trajectory into which the current decision will propel the system.

**The temporal admissibility gap has two dimensions:**

**Dimension A — Retrospective:** A system may generate a nominally valid decision that contradicts the direction, regime, and signal pattern established by its recent history. A BUY decision generated after 15 consecutive cycles of bearish signals and declining regime quality is nominally valid if it passes all current-state checkpoints. It is temporally inadmissible because it is incoherent with the trajectory from which it emerged.

**Dimension B — Prospective:** A system may generate a nominally valid decision that is likely to become inadmissible within a small number of future cycles, because the detected regime is likely to transition to an adverse regime. Approving a BUY decision in a regime that has an 80% probability of transitioning to BEARISH within 5 cycles approves an action that will, with high probability, be contradicted by the system's own future signals.

Existing governance systems address neither dimension:

**1.1 No Retrospective Trajectory Check:** Checkpoint pipelines evaluate current-state validity without analyzing the historical trajectory from which the system arrived at the current decision point.

**1.2 No Prospective Regime Analysis:** Checkpoint pipelines evaluate current regime conditions without projecting likely regime transitions and their implications for the admissibility of the proposed decision.

**1.3 Biased History Analysis:** Systems that do examine historical data typically use only executed trades as the historical source, creating a survivorship bias — the history reflects only decisions that were approved and executed, omitting the signal trajectory of decisions that were blocked. A complete picture of the system's trajectory requires both approved and blocked decisions.

**1.4 No Unified Bilateral Assessment:** No existing system unifies retrospective trajectory coherence and prospective regime implication into a single bilateral temporal admissibility determination.

The present invention addresses all four inadequacies through the Bidirectional Temporal Admissibility System, comprising two complementary components: the Temporal Coherence Validator (TCV) for retrospective assessment and the Forward Trajectory Implication (FTI) module for prospective assessment.

---

## SUMMARY OF THE INVENTION

The present invention provides a bidirectional temporal admissibility system comprising:

**Component A — Temporal Coherence Validator (TCV):** A retrospective trajectory coherence module that computes a composite score reflecting whether the proposed decision is consistent with the recent historical trajectory of the system. The score combines three dimensions: direction coherence (sign-consistency of signal deltas), regime-action alignment (consistency between the proposed action and the historically dominant regime), and signal stability (inverse of direction-flip rate). The TCV uses a dual-source history that includes both executed and blocked decisions to provide an unbiased view of the system's full decision trajectory.

**Component B — Forward Trajectory Implication (FTI):** A prospective regime analysis module that evaluates whether the proposed decision is consistent with the likely near-future trajectory of the system. The FTI uses a Hidden Markov Model (HMM) transition matrix to estimate the probability of adverse regime transitions within a configurable forward horizon, and combines this with implied decision consistency and signal momentum sustainability assessments.

Both components operate as fail-safe governance checkpoints: any module failure produces a pass-through result that does not block the upstream pipeline. Both components share the configurable parameter framework of the broader governance pipeline.

---

## DETAILED DESCRIPTION OF THE PREFERRED EMBODIMENTS

### I. SYSTEM ARCHITECTURE AND POSITIONING

The Bidirectional Temporal Admissibility System occupies governance checkpoint positions 7 (TCV) and 7b (FTI) in the multi-checkpoint governance pipeline:

```
CP-0 → CP-1 → ... → CP-6 → TCV (CP-7) → FTI (CP-7b) → CP-8 (Scoring) → TIE
       [probabilistic checkpoints]   [bilateral temporal]   [post-pipeline]
```

The temporal assessment spans two directions from the current decision instant:
- **Backward:** TCV analyzes the recent history of the system (in one embodiment: the past 15 decision cycles).
- **Forward:** FTI projects the likely near-future trajectory (in one embodiment: the next 5 decision cycles).

This bilateral temporal window — past N cycles and future M cycles — constitutes the temporal admissibility envelope within which the proposed decision must be coherent to proceed.

### II. COMPONENT A — TEMPORAL COHERENCE VALIDATOR (TCV)

#### II.A. Design Principle

The TCV evaluates whether the proposed decision is TEMPORALLY ADMISSIBLE given the recent trajectory of the system. It complements probabilistic governance (which asks "Is this decision valid now?") with a trajectory-level question: "Is this decision coherent with where the system has been?"

#### II.B. Dual-Source Unbiased History

A critical design feature of the TCV is its use of a dual-source history that includes both:

- **Primary source:** Shadow trade events (governance veto events — decisions that were blocked by the pipeline). These represent the signal trajectory of the system including all rejected signals.
- **Secondary source:** Executed trade records (decisions that were approved and executed). These represent the confirmed action history of the system.

Combining both sources provides an unbiased view of the system's full decision trajectory, avoiding the survivorship bias of systems that use only executed trades. A system that blocked 80% of signals in a given period but approved 20% shows a materially different trajectory signal than a system that approved 80% — and the TCV captures this distinction because it includes both the blocked and approved signals in its history.

#### II.C. Three-Dimensional Retrospective Score

The TCV computes a composite trajectory coherence score [0–100] combining three dimensions with configurable weights. In one embodiment:

**Dimension 1 — Direction Coherence (in one embodiment: 40% weight):**
Measures the sign-consistency (monotonicity) of consecutive EMA-score deltas across the historical window. If the signal has been consistently strengthening in one direction, direction coherence is high. Rapid reversals reduce direction coherence. This dimension measures whether the signal is TRENDING in a consistent direction, not merely whether it is stable at a level.

**Dimension 2 — Regime-Action Alignment (in one embodiment: 35% weight):**
Evaluates whether the proposed action (BUY, SELL, HOLD) matches the dominant historical regime across the analysis window. The dominant regime is computed from both shadow events and executed trades, providing an unbiased regime history. A BUY decision in a historically bearish regime reduces this dimension's contribution to the composite score.

**Dimension 3 — Signal Stability (in one embodiment: 25% weight):**
Measures the inverse of the direction-flip rate across recent signal labels (BULLISH, BEARISH, NEUTRAL). Rapid alternation between bullish and bearish signals reduces signal stability. A system that has been consistently generating signals in one direction has high signal stability; a system that has been oscillating has low signal stability.

In other embodiments, the three dimensions and their weights are configurable. Additional dimensions may be introduced, including but not limited to: volume-weighted signal strength, cross-asset signal correlation, or lagged autocorrelation of the signal series.

#### II.D. TCV Admissibility Determination

The TCV produces a binary admissibility determination (ADMISSIBLE / NOT ADMISSIBLE) based on whether the composite score meets or exceeds a configurable threshold (in one embodiment: TCV_THRESHOLD = 20 out of 100, reflecting a low-bar design that blocks only clear trajectory incoherence). The low default threshold reflects the design intent: TCV is not a strict filter but a trajectory-level incoherence detector.

If insufficient history is available (in one embodiment: fewer than TCV_MIN_EVENTS = 3 events in the analysis window), TCV returns ADMISSIBLE with a pass-through flag, avoiding false blocks due to insufficient data.

### III. COMPONENT B — FORWARD TRAJECTORY IMPLICATION (FTI)

#### III.A. Design Principle

The FTI evaluates whether the proposed decision is PROSPECTIVELY COHERENT — coherent with the likely near-future trajectory of the system. Where TCV asks "Is this decision coherent with the past?", FTI asks "Is this decision coherent with the likely near future?"

This prospective assessment adds a dimension to governance that no existing checkpoint-based system provides: the ability to evaluate a decision not only against current conditions but against the probabilistic implications of those conditions for the near future.

#### III.B. Hidden Markov Model Regime Transition Matrix

The FTI uses a Hidden Markov Model (HMM) transition matrix to estimate the probability of adverse regime transitions within a configurable forward horizon (in one embodiment: FTI_HORIZON = 5 cycles). The transition matrix maps the current regime to the probability distribution over possible regimes at each future cycle.

In one embodiment, regime persistence probabilities are maintained as a configurable table, reflecting the statistical tendency of each regime to persist across cycles:

- TRENDING: in one embodiment, regime persistence probability of 0.82 (high persistence)
- UPTREND: in one embodiment 0.78
- DOWNTREND: in one embodiment 0.76
- BULLISH: in one embodiment 0.75
- BEARISH: in one embodiment 0.74
- RANGING: in one embodiment 0.65
- NEUTRAL: in one embodiment 0.60
- VOLATILE: in one embodiment 0.45 (low persistence — volatile regimes transition rapidly)

In other embodiments, the regime persistence probabilities are estimated from historical regime transition data specific to the operational domain.

#### III.C. Three-Dimensional Prospective Score

The FTI computes a composite forward-looking score [0–100] combining three dimensions with configurable weights. In one embodiment:

**Dimension 1 — Regime Transition Risk (in one embodiment: 40% weight):**
Uses the HMM transition matrix to compute the probability that the operational regime transitions to an adverse regime within the forward horizon. The adverse regime set is defined relative to the proposed action:
- For a BUY decision: adverse regimes include BEARISH, DOWNTREND, VOLATILE, STRONG_SELL
- For a SELL decision: adverse regimes include BULLISH, UPTREND, VOLATILE, STRONG_BUY
- For a HOLD decision: no adverse regimes (all transitions are acceptable)

Dimension 1 score = (1 − adverse_transition_probability) × 100. A low probability of adverse transition yields a high score; a high probability of adverse transition yields a low score.

**Dimension 2 — Implied Decision Consistency (in one embodiment: 35% weight):**
Given the proposed action and the current regime, evaluates whether the system will be able to maintain decision consistency for the next N cycles, using historical regime persistence data. High regime persistence in the current regime yields high implied consistency; low persistence yields low consistency.

**Dimension 3 — Signal Momentum Sustainability (in one embodiment: 25% weight):**
Evaluates the slope of recent signal scores (in one embodiment: EMA score and confidence values). A BUY decision with rising signal momentum is more likely to be sustainable for N future cycles than a BUY decision with declining momentum. Score = (slope_normalized + 1) / 2 × 100, mapping negative slopes to scores below 50 and positive slopes to scores above 50.

In other embodiments, the three dimensions and their weights are configurable. The adverse regime table may be extended with domain-specific adverse conditions for non-financial applications.

#### III.D. FTI Admissibility Determination

The FTI produces a binary admissibility determination (PASSED / NOT PASSED) based on whether the composite implied score meets or exceeds a configurable threshold (in one embodiment: FTI_THRESHOLD = 25 out of 100). On any evaluation error or data unavailability, FTI returns PASSED with a pass-through flag.

### IV. BILATERAL TEMPORAL ADMISSIBILITY DETERMINATION

The bilateral temporal admissibility of a proposed governance decision is determined by the joint result of TCV and FTI:

- **Fully admissible:** TCV = ADMISSIBLE and FTI = PASSED → decision proceeds to next governance checkpoint
- **Retrospectively inadmissible:** TCV = NOT ADMISSIBLE → decision blocked (independent of FTI result)
- **Prospectively inadmissible:** FTI = NOT PASSED → decision blocked (independent of TCV result)
- **Bilaterally inadmissible:** Both TCV = NOT ADMISSIBLE and FTI = NOT PASSED → decision blocked with compound reason

The compound blocking reason from bilateral inadmissibility provides regulatory auditors with specific evidence of both the retrospective and prospective sources of temporal incoherence.

### V. FAIL-SAFE DESIGN

Both TCV and FTI implement fail-safe behavior:
- Any module failure, database connectivity error, or internal exception produces a pass-through result with `pass_through: True` flag.
- A pass-through result does not block the governance decision. The pipeline continues as if the temporal check were not present.
- Pass-through events are logged and included in the decision receipt for audit purposes.
- If TCV passes through, FTI is still evaluated. If FTI passes through, the decision proceeds.

### VI. ALTERNATIVE EMBODIMENTS

**6.1 Extended Retrospective Window:** In one embodiment, the TCV analysis window is extended beyond 15 cycles (configurable via TCV_WINDOW parameter) for applications where longer-term trajectory coherence is relevant. Clinical decision support applications may benefit from multi-week retrospective windows; high-frequency trading applications may benefit from shorter windows.

**6.2 Extended Prospective Horizon:** In one embodiment, the FTI forward horizon extends beyond 5 cycles (configurable via FTI_HORIZON parameter), providing longer-range prospective governance for decisions with extended commitment periods.

**6.3 Domain-Specific Adverse Regime Tables:** The adverse regime table of FTI Dimension 1 may be replaced with domain-specific tables for non-financial applications. For clinical governance: adverse conditions include deteriorating biomarker trends; for energy grid governance: adverse conditions include grid stability metrics below threshold.

**6.4 Learned Transition Matrices:** In one embodiment, the HMM transition matrix used in FTI Dimension 1 is estimated from historical domain-specific regime transition data rather than configured statically, enabling adaptive prospective governance that improves as more operational history is accumulated.

**6.5 Unified Bilateral Score:** In one embodiment, TCV and FTI scores are combined into a single bilateral temporal admissibility score (in one embodiment: weighted average of TCV score and FTI implied score), with a single configurable admissibility threshold applied to the combined score.

---

## CLAIMS

**Claim 1 (Broad — Core Bilateral System)** — A computer-implemented bidirectional temporal admissibility system for automated governance decisions, comprising: a retrospective trajectory coherence module that evaluates whether a proposed decision is consistent with the recent historical trajectory of the system; a prospective regime implication module that evaluates whether the proposed decision is consistent with the probable near-future trajectory of the system; and a bilateral admissibility determination that combines retrospective and prospective evaluations to determine temporal admissibility of the proposed decision.

**Claim 2 (Broad — TCV Three Dimensions)** — The system of Claim 1, wherein the retrospective trajectory coherence module computes a composite score combining: a direction coherence dimension measuring sign-consistency of consecutive signal deltas across the historical window; a regime-action alignment dimension measuring whether the proposed action matches the historically dominant regime; and a signal stability dimension measuring the inverse of the direction-flip rate across recent signal classifications.

**Claim 3 (Broad — Dual-Source History)** — The system of Claim 1, wherein the retrospective trajectory coherence module constructs its historical analysis from two independent data sources comprising blocked governance decisions and approved governance decisions, providing an unbiased view of the full decision trajectory that avoids survivorship bias from systems using only executed records.

**Claim 4 (Broad — HMM Prospective)** — The system of Claim 1, wherein the prospective regime implication module uses a Hidden Markov Model transition matrix to estimate the probability of adverse regime transitions within a configurable forward horizon, and wherein adverse regime sets are defined relative to the proposed action direction.

**Claim 5 (Broad — FTI Three Dimensions)** — The system of Claim 1, wherein the prospective regime implication module computes a composite score combining: a regime transition risk dimension based on adverse transition probability from the HMM transition matrix; an implied decision consistency dimension based on regime persistence statistics; and a signal momentum sustainability dimension based on the slope of recent signal values.

**Claim 6 (Specific — Adverse Regime Sets)** — The system of Claim 4, wherein, in one embodiment, adverse regimes for a buy-direction decision comprise bearish, downtrend, and volatile regime classifications, and adverse regimes for a sell-direction decision comprise bullish, uptrend, and volatile regime classifications, wherein the adverse regime set is configurable for domain-specific applications.

**Claim 7 (Broad — Bilateral Blocking)** — The system of Claim 1, wherein a governance decision is blocked when either the retrospective trajectory coherence module or the prospective regime implication module determines inadmissibility, and wherein blocking by both modules simultaneously produces a compound blocking reason identifying both the retrospective and prospective sources of temporal incoherence.

**Claim 8 (Broad — Fail-Safe)** — The system of Claim 1, wherein both the retrospective and prospective modules implement fail-safe behavior in which any module failure produces a pass-through admissibility result with a pass-through flag recorded for audit purposes, such that module failure does not introduce new blocking conditions.

**Claim 9 (Broad — Configurable Window)** — The system of Claim 1, wherein the retrospective analysis window and the prospective horizon are independently configurable parameters, enabling domain-specific calibration of the temporal admissibility envelope.

**Claim 10 (Broad — Method)** — A computer-implemented method for bidirectional temporal admissibility determination in automated governance decision pipelines, comprising: computing a retrospective trajectory coherence score from a dual-source unbiased history of recent system decisions; estimating a prospective regime transition risk using a Hidden Markov Model transition matrix over a configurable forward horizon; computing a prospective admissibility score combining regime transition risk, implied decision consistency, and signal momentum sustainability; blocking the proposed decision when either the retrospective or prospective score falls below a configurable admissibility threshold; and recording the bilateral temporal assessment in the governance decision receipt.

---

## ABSTRACT

A bidirectional temporal admissibility system for automated governance decisions combines retrospective trajectory coherence validation and prospective regime implication analysis into a unified bilateral temporal checkpoint. The retrospective component (Temporal Coherence Validator, TCV) computes a composite coherence score over a configurable historical window combining three dimensions — direction coherence (in one embodiment: 40% weight, measuring sign-consistency of signal deltas), regime-action alignment (in one embodiment: 35% weight, measuring consistency with the historically dominant regime), and signal stability (in one embodiment: 25% weight, measuring inverse direction-flip rate) — using a dual-source unbiased history comprising both blocked and approved governance decisions to avoid survivorship bias. The prospective component (Forward Trajectory Implication, FTI) evaluates whether the proposed decision is consistent with the likely near-future trajectory by computing adverse regime transition probability using a Hidden Markov Model transition matrix over a configurable forward horizon (in one embodiment: 5 cycles), combined with implied decision consistency and signal momentum sustainability assessments. A proposed decision is blocked when either the retrospective or prospective assessment falls below a configurable threshold; bilateral blocking produces a compound reason identifying both temporal sources of incoherence. Both components implement fail-safe behavior: any failure produces a pass-through result that does not introduce new blocking conditions. Applications span any regulated domain requiring temporal coherence validation of automated decisions, including algorithmic trading, clinical decision support, autonomous robotics, energy grid management, and insurance underwriting. To the inventor's knowledge, this is the first system unifying retrospective trajectory coherence scoring and prospective HMM-based regime transition risk evaluation into a bilateral temporal admissibility determination specifically for automated governance decision pipelines.

---

## DRAWINGS

```
FIG. 1 — Bidirectional Temporal Admissibility Envelope

             ← PAST (TCV window)  |  FUTURE (FTI horizon) →
             ─────────────────────┼──────────────────────────
  t-15  t-14 ... t-2  t-1   t=0  |  t+1  t+2  t+3  t+4  t+5
  ●────●────●────●────●    [DECISION]  ○────○────○────○────○
         TCV analyzes              FTI projects
         recent history            via HMM matrix

  ADMISSIBLE ↔ consistent with past trajectory AND near-future trajectory

FIG. 2 — TCV Three-Dimensional Retrospective Score

  DIMENSION             WEIGHT    MEASURES
  ──────────────────────────────────────────────────────
  Direction Coherence    40%      Monotonicity of signal deltas
  Regime-Action Align.   35%      Action vs. dominant historical regime
  Signal Stability       25%      Inverse direction-flip rate

  DATA SOURCES (dual-source, unbiased):
  ● shadow_trade_events   → blocked decisions (veto events)
  ● paper_trading_trades  → approved decisions (executed events)
  Combined → full trajectory (no survivorship bias)

FIG. 3 — FTI HMM Regime Transition Risk (Dimension 1)

  Current Regime: VOLATILE (persistence = 0.45)
  Proposed Action: BUY
  Adverse regimes: {BEARISH, DOWNTREND, VOLATILE, STRONG_SELL}

  Horizon = 5 cycles:
  P(adverse in 5 cycles | VOLATILE start) = HIGH
  Regime Transition Risk score → LOW
  FTI admissibility → potential BLOCK

FIG. 4 — Bilateral Admissibility Logic

  TCV Result      FTI Result      Bilateral Decision
  ──────────────────────────────────────────────────
  ADMISSIBLE      PASSED          ✅ PROCEEDS
  NOT ADMISSIBLE  PASSED          ❌ BLOCKED (retrospective)
  ADMISSIBLE      NOT PASSED      ❌ BLOCKED (prospective)
  NOT ADMISSIBLE  NOT PASSED      ❌ BLOCKED (bilateral — compound reason)
  PASS-THROUGH    PASSED          ⚠ PROCEEDS (TCV fail-safe)
  ADMISSIBLE      PASS-THROUGH    ⚠ PROCEEDS (FTI fail-safe)
```
