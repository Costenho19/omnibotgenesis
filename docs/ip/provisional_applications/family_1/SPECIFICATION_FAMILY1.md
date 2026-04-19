# UNITED STATES PATENT AND TRADEMARK OFFICE
# PROVISIONAL APPLICATION FOR PATENT

**Application Reference:** OMNIX-PAT-2026-001
**Filing Date:** [DATE OF FILING]
**Inventor:** Harold Alberto Nunes Rodelo

---

# SPECIFICATION

## TITLE OF THE INVENTION

**GOVERNANCE CONTROL ARCHITECTURE FOR AUTOMATED DECISION SYSTEMS WITH SEQUENTIAL VETO-AUTHORITY CHECKPOINTS, COUNTERFACTUAL RISK FILTER CALIBRATION, AND SIGNAL CONTRADICTION DETECTION**

---

## CROSS-REFERENCE TO RELATED APPLICATIONS

This application does not claim priority to any previously filed application. This provisional application is filed pursuant to 35 U.S.C. § 111(b) to establish a priority date. See also related provisional applications OMNIX-PAT-2026-002 (Non-Markovian Adaptive Signal Processing System) and OMNIX-PAT-2026-003 (Ethical and Quantum-Secure Execution Framework), filed concurrently herewith by the same inventor.

---

## STATEMENT REGARDING FEDERALLY SPONSORED RESEARCH OR DEVELOPMENT

Not applicable. This invention was made without Federal sponsorship.

---

## TECHNICAL FIELD

The present invention relates to computer-implemented systems and methods for governing high-stakes automated decisions. More specifically, the invention relates to a domain-agnostic governance engine that enforces decision admissibility through a sequential pipeline of independent, veto-authority checkpoints; a counterfactual shadow portfolio system for continuous self-calibration of risk management filters; and a Decision Contradiction Index (DCI) for detecting internal signal divergence prior to execution commitment.

---

## BACKGROUND OF THE INVENTION

### 1. The Governance Gap in Automated Decision Systems

The deployment of automated decision systems across high-stakes institutional domains — including financial trading, insurance underwriting, credit evaluation, supply chain management, and healthcare AI — has accelerated substantially in the period from 2015 to the present. These systems operate at speeds and scales that are fundamentally incompatible with human-in-the-loop review of individual decisions. As a result, the governance of such systems has become a critical infrastructure challenge.

Existing approaches to automated decision governance suffer from a common structural deficiency: they are designed to describe governance rather than enforce it. Policy frameworks, audit committees, model risk management processes, and internal review boards represent organizational layers that operate at time horizons measured in days, weeks, or quarters — not at the millisecond-to-second timescales at which automated systems act. When a financial trading system executes thousands of orders per second, or when a credit scoring engine evaluates ten thousand loan applications per hour, organizational governance mechanisms are structurally incapable of providing real-time enforcement.

A further deficiency of existing systems is the failure to re-establish decision admissibility at the moment of execution commitment. Existing systems validate inputs at the time of model training, at the time of model deployment, or periodically through backtesting regimes. However, none of these validation events occurs at the precise moment when a decision transitions from a computed recommendation into an irreversible real-world action. This temporal gap between validation and execution is the primary locus of catastrophic failure in automated decision systems.

### 2. Historical Failures Attributable to the Governance Gap

The severity of this governance gap is illustrated by a series of well-documented incidents in automated financial systems:

**Knight Capital Group (August 1, 2012):** Knight Capital Group, a major U.S. broker-dealer, suffered a loss of approximately $440 million USD in a single 45-minute trading session as a result of the erroneous activation of a legacy software module that had not been properly decommissioned. The legacy module, known internally as the "Power Peg," generated thousands of unintended orders for approximately 150 stocks. There was no architectural mechanism capable of detecting the divergence between the intended system behavior and the actual system behavior at the point of execution. The loss effectively bankrupted the firm.

**Flash Crash (May 6, 2010):** The U.S. equity markets experienced a rapid, deep, and largely self-recovering crash in which the Dow Jones Industrial Average fell approximately 1,000 points (roughly 9%) in minutes before recovering. Investigations identified automated trading algorithms that responded to market conditions in mutually reinforcing patterns without any governance layer capable of detecting the systemic coherence failure.

**Zillow Offers Algorithm (2021):** Zillow Group, Inc. ceased its iBuying program ("Zillow Offers") after its algorithmic home price prediction system accumulated a portfolio of overvalued properties, resulting in a write-down of approximately $304 million and the elimination of approximately 25% of its workforce. The system continued to make commitments at prices that contradicted signals available in the broader market data, with no checkpoint capable of detecting and blocking the divergence.

These incidents share a common structural cause: the absence of a real-time, pre-execution governance layer capable of evaluating decision admissibility at the moment an action is about to become irreversible.

### 3. Deficiencies of Prior Art

Prior art approaches to automated decision governance include the following categories:

**(a) Post-Hoc Audit Systems:** Systems that record decision outputs for subsequent review. These systems do not prevent harmful decisions; they create records after harm has occurred. While valuable for regulatory compliance and forensic analysis, they provide no protective function.

**(b) Single-Layer Risk Limits:** Systems that apply a single threshold check — for example, maximum position size limits in trading systems — before execution. These systems are structurally fragile because they create a single point of failure; if the limit check is incorrect, corrupted, or subject to a software error, no alternative enforcement layer exists.

**(c) Consensus Aggregation Approaches:** Systems that aggregate signals from multiple sources into a single composite score (e.g., weighted average, voting ensemble) and evaluate the composite against a threshold. These systems mask internal signal disagreement by design. A situation in which three signals strongly indicate one direction and two signals strongly indicate the opposite direction will produce a composite score that appears to indicate moderate confidence in the majority direction, concealing the underlying contradiction.

**(d) Static Threshold Systems:** Systems that apply predetermined, fixed thresholds calibrated at system deployment. These systems do not adapt to changes in market conditions, operating environments, or observed filter accuracy over time. Thresholds that were appropriate at calibration time may be systematically too permissive or too restrictive under changed conditions.

**(e) Human Review Queues:** Systems that flag decisions for human review before execution. These systems are incompatible with the operational requirements of high-frequency automated decision environments, where the latency introduced by human review is operationally unacceptable.

None of the foregoing prior art approaches provides: (1) sequential, independent, veto-authority checkpoint evaluation at the moment of execution commitment; (2) automatic self-calibration of risk filters based on counterfactual outcome analysis; and (3) detection of internal signal contradiction as a distinct and independent veto condition. The present invention addresses all three deficiencies simultaneously.

---

## SUMMARY OF THE INVENTION

The present invention provides a computer-implemented governance control architecture comprising three integrated, independently patentable components:

### Component 1A: Domain-Agnostic Decision Governance Engine with Sequential Checkpoint Architecture

The first component is a domain-agnostic decision governance engine that evaluates proposed automated actions through a sequential pipeline of independent checkpoints, each having independent veto authority to block the proposed action. The engine receives domain-specific input data, transforms said data into a set of normalized governance signals through a pluggable domain adapter module, and evaluates said normalized signals through the sequential checkpoint pipeline. The domain-agnostic architecture is achieved through the normalization step: all domain-specific signals are translated into a common numerical format that allows identical checkpoint logic to govern decisions across fundamentally different institutional domains.

The default behavior of the system, when any checkpoint is unable to evaluate its assigned signals, is to block the proposed action. This "fail-closed" design ensures that uncertainty or system error results in conservative inaction rather than permissive action — a critical property for high-stakes automated decision environments.

### Component 1B: Counterfactual Shadow Portfolio for Automated Risk Filter Calibration

The second component is a counterfactual shadow portfolio system that continuously evaluates the accuracy of the governance system's veto decisions by comparing them against actual subsequent outcomes. When the governance engine blocks a proposed action, the shadow portfolio system records the complete decision context, tracks the outcome that would have occurred had the action been permitted, and classifies the veto as either capital-preserving (correct) or opportunity-blocking (incorrect). This classification data is aggregated over time to generate threshold adjustment recommendations for the checkpoint pipeline, enabling the governance system to self-calibrate based on its own historical performance.

### Component 1C: Decision Contradiction Index (DCI) — Signal Divergence Detection

The third component is the Decision Contradiction Index (DCI), a novel quantitative measure that detects internal contradiction among independent signal sources as a distinct governance condition. Unlike consensus aggregation approaches that mask signal disagreement by computing averages or weighted votes, the DCI explicitly quantifies the degree to which independent signals disagree with one another. When the DCI score exceeds a predetermined threshold, the system interprets this as a state of internal incoherence and mandates a conservative hold action, regardless of the direction or magnitude of any individual signal.

---

## BRIEF DESCRIPTION OF THE DRAWINGS

The accompanying drawings, which are incorporated in and constitute a part of this specification, illustrate preferred embodiments of the invention.

**FIG. 1** is a system architecture diagram illustrating the overall Governance Control Architecture, showing the relationship among the Domain Adapter Module, the Sequential Checkpoint Pipeline, the Decision Trace Generator, and the Counterfactual Shadow Portfolio system.

**FIG. 2** is a process flow diagram illustrating the step-by-step execution of the Sequential Checkpoint Pipeline for a representative proposed action, from signal normalization through final governance decision generation.

**FIG. 3** is a data flow diagram illustrating the Counterfactual Shadow Portfolio system, including the Shadow Event Logger, the Outcome Tracker, the Counterfactual Analyzer, and the Calibration Engine.

**FIG. 4** is a signal state diagram illustrating the Decision Contradiction Index (DCI) computation, classification thresholds (ALIGNED / TENSIONED / CONTRADICTORY), and the resulting governance actions.

---

## DETAILED DESCRIPTION OF THE PREFERRED EMBODIMENTS

### I. OVERVIEW OF THE SYSTEM

Referring to FIG. 1, the Governance Control Architecture (hereinafter "the System" or "OMNIX Governance Engine") comprises four primary subsystems operating in sequence: (1) a Domain Adapter Module (110); (2) a Sequential Checkpoint Pipeline (120) comprising a plurality of independent checkpoints (CP-0 through CP-11); (3) a Decision Trace Generator (130); and (4) a Counterfactual Shadow Portfolio System (140). The System further comprises a Decision Contradiction Index (DCI) Module (150), which operates as an integrated component of the Sequential Checkpoint Pipeline at a designated checkpoint position.

**Execution Boundary Principle:** The System is designed to operate at the execution boundary — the precise computational point at which a proposed action would transition from a computed recommendation into an irreversible real-world commitment. This placement is architecturally fundamental and distinguishes the present invention from all prior art approaches that apply governance at the model training stage, the model deployment stage, or through post-hoc audit mechanisms. Governance at the execution boundary means that every proposed action — regardless of its source, its confidence, or its prior validation history — must satisfy all checkpoint criteria at the moment it is about to become real, not at any earlier or later point. A proposed action that was valid at time T may be inadmissible at time T+1 if conditions have changed; the System enforces admissibility at T+1, not at T.

The System is designed to be deployed as a governance enforcement layer between a decision generation subsystem and an execution environment. The decision generation subsystem may be any automated system that produces recommendations or instructions, including but not limited to: machine learning models, algorithmic trading engines, credit scoring models, clinical decision support systems, autonomous robotic control systems, autonomous agent orchestration platforms, surgical or diagnostic AI systems, energy grid management and dispatch systems, autonomous supply chain management systems, insurance underwriting engines, legal contract execution systems, or any other automated system that generates actions with real-world consequences. The execution environment may be any system that converts a recommendation into an irreversible real-world action or commitment, including but not limited to: financial exchange interfaces, robotic actuator command interfaces, clinical order entry systems, autonomous vehicle control systems, energy dispatch systems, loan origination systems, claims processing systems, procurement systems, or any system that commits resources, physical actions, or obligations based on automated recommendations. The mandatory sequential pipeline — in which every proposed action must pass all checkpoints before crossing the execution boundary — is equally applicable and structurally identical regardless of the domain in which the System is deployed. The System does not replace the decision generation subsystem; it governs whether the outputs of that subsystem are permitted to cross the execution boundary.

### II. DOMAIN ADAPTER MODULE (110)

The Domain Adapter Module (110) receives domain-specific input data from a data source and transforms said data into a set of normalized governance signals. The normalization process is the architectural mechanism that enables the governance checkpoint pipeline to operate identically across fundamentally different institutional domains.

#### II.A. Normalized Governance Signal Set

The normalized governance signal set comprises at minimum the following six signal components, each expressed as a numerical value normalized to a common scale (preferably, but not limited to, the range [0.0, 1.0] or [0, 100]):

**Signal 1 — Probability Score (P):** A numerical value indicating the estimated likelihood of a favorable outcome from the proposed action. In financial trading applications, this corresponds to the estimated win probability derived from Monte Carlo simulation or historical backtesting. In insurance underwriting applications, this corresponds to the estimated probability that a proposed policy does not result in a claim exceeding the premium collected. In other domains, this signal is mapped from the domain-specific probability estimation method to the normalized scale.

**Signal 2 — Risk Exposure Score (R):** A numerical value indicating the potential magnitude of loss or adverse outcome associated with the proposed action. In trading applications, this corresponds to maximum drawdown exposure or capital-at-risk metrics. In insurance applications, this corresponds to maximum liability exposure as a fraction of total reserve capital. The Risk Exposure Score is typically inverse-normalized, such that lower values indicate lower risk (more favorable for governance approval) and higher values indicate higher risk (more likely to trigger veto).

**Signal 3 — Signal Coherence Score (C):** A numerical value indicating the degree of agreement among independent analytical signals or subsystems that contributed to the proposed action. A high Signal Coherence Score indicates that multiple independent analytical methods have converged on the same recommendation, increasing confidence in the proposed action. A low Signal Coherence Score indicates disagreement among independent analytical methods, decreasing confidence.

**Signal 4 — Trend Persistence Score (T):** A numerical value indicating the duration and stability of the condition or trend that motivates the proposed action. A high Trend Persistence Score indicates that the motivating condition has been present and stable for a meaningful historical period, reducing the likelihood that the proposed action is responding to transient noise. A low Trend Persistence Score indicates a recently emerged or unstable condition.

**Signal 5 — Stress Resilience Score (S):** A numerical value indicating the robustness of the proposed action under adverse simulated conditions. In trading applications, this corresponds to the performance of the proposed action across Monte Carlo stress scenarios. In other domains, this corresponds to the estimated performance of the proposed action under defined adverse conditions (e.g., increased claim frequency, supply chain disruption, or market volatility events).

**Signal 6 — Logic Consistency Score (L):** A numerical value indicating the internal logical coherence of the proposed action. This signal is computed by the Decision Contradiction Index Module (described in Section VI below) and represents the inverse of the DCI score: a high Logic Consistency Score indicates low internal contradiction, and a low Logic Consistency Score indicates high internal contradiction.

#### II.B. Domain Adapter Interchangeability

A key design property of the Domain Adapter Module is that it is interchangeable. The governance checkpoint pipeline operates exclusively on the normalized governance signal set (P, R, C, T, S, L) without any awareness of the originating domain. A different Domain Adapter Module may be substituted to extend the governance architecture to a new institutional domain without any modification to the checkpoint pipeline logic. In a preferred embodiment, the following domain adapter modules are provided:

- **Trading Adapter:** Maps financial market signals (EMA direction, HMM regime state, Kalman filter estimate, Monte Carlo win rate, drawdown exposure) to the normalized signal set.
- **Insurance Adapter:** Maps actuarial signals (loss ratio estimate, exposure coefficient, reserve adequacy ratio, catastrophe probability, reinsurance availability) to the normalized signal set.
- **Credit Adapter:** Maps creditworthiness signals (probability of default, debt-to-income ratio, credit utilization, payment history consistency, income stability) to the normalized signal set.
- **Supply Chain Adapter:** Maps logistics signals (supplier reliability score, lead time variance, inventory buffer adequacy, cascading failure probability, geopolitical risk index) to the normalized signal set.
- **Healthcare AI Adapter:** Maps clinical decision signals (diagnostic confidence, evidence base strength, contraindication check result, patient history coherence, regulatory compliance status) to the normalized signal set.

### III. SEQUENTIAL CHECKPOINT PIPELINE (120)

Referring to FIG. 2, the Sequential Checkpoint Pipeline (120) comprises a plurality of independent checkpoints arranged in a predetermined sequential order. In a preferred embodiment, the pipeline comprises twelve checkpoints designated CP-0 through CP-11, plus a Trajectory Invariant Enforcement (TIE) post-execution verification layer.

Each checkpoint in the pipeline has the following properties:

1. **Independence:** Each checkpoint evaluates its assigned governance signals independently of all other checkpoints. No checkpoint has access to the evaluation result of any other checkpoint at the time of its own evaluation.

2. **Veto Authority:** Each checkpoint has independent authority to block the proposed action by issuing a BLOCK verdict. A BLOCK verdict from any single checkpoint is sufficient to prevent the proposed action from proceeding to execution, regardless of the results of all other checkpoints.

3. **Fail-Closed Default:** If a checkpoint is unable to evaluate its assigned signals — due to data unavailability, signal corruption, computational error, or any other cause — the default behavior is to issue a BLOCK verdict. The system does not default to permitting actions in the face of uncertainty.

4. **Verdict Recording:** Each checkpoint records its evaluation result, including the signals evaluated, the thresholds applied, the verdict issued, and the reason for the verdict, as a component of the Decision Trace data structure.

#### III.A. Checkpoint Descriptions

The following describes the preferred embodiment of each checkpoint in the sequential pipeline:

**CP-0: Signal Integrity Gate**
Evaluates: Completeness and integrity of the normalized governance signal set.
Purpose: Verifies that all required governance signals are present, within valid numerical ranges, and have been generated within an acceptable recency window. If any signal is missing, out of range, or stale, CP-0 issues a BLOCK verdict, preventing the pipeline from proceeding with incomplete information.
Threshold: All six normalized signals must be present and within [0.0, 1.0]. Signal timestamp must be within the configured recency window (default: 60 seconds for high-frequency trading applications; configurable per deployment).

**CP-1: Context Admission Gate (CAG)**
Evaluates: Global operating context — macroeconomic volatility, liquidity conditions, and systemic risk indicators.
Purpose: Determines whether the current global operating context is suitable for any automated action, regardless of the specific proposed action's individual merits. If systemic conditions (e.g., extreme market volatility, liquidity crisis, regulatory halt) render the environment unsuitable for automated action, CP-1 blocks all actions during the affected period.
Threshold: Configurable per deployment context. In trading applications, CP-1 evaluates the VIX index, bid-ask spread anomalies, and on-chain liquidity metrics.

**CP-2: Probability Threshold Gate**
Evaluates: Probability Score (P).
Purpose: Ensures that the estimated probability of a favorable outcome from the proposed action meets a minimum threshold. Actions with insufficient estimated win probability are blocked.
Threshold: In one embodiment, P ≥ 0.52 (estimated win probability exceeding 52%). This threshold value is configurable and domain-specific; in other embodiments the threshold may be set to any value appropriate to the deployment context, risk tolerance of the deploying institution, and characteristics of the decision domain. The structural requirement — that a minimum probability threshold must be satisfied for the action to proceed — is preserved across all embodiments.

**CP-3: Temporal Coherence Gate**
Evaluates: Trend Persistence Score (T); trajectory consistency against historical decision baseline.
Purpose: Evaluates whether the condition motivating the proposed action has been present for a sufficient and consistent duration to distinguish genuine signal from transient noise. Also evaluates whether the proposed action is consistent with the system's established behavioral trajectory, detecting anomalous deviations from historical patterns.
Threshold: T ≥ 0.40 and trajectory consistency score within ±2 standard deviations of historical mean.

**CP-4: Risk Limits Gate**
Evaluates: Risk Exposure Score (R).
Purpose: Enforces hard capital and resource exposure limits. Ensures that the proposed action does not expose the system to loss or adverse outcome in excess of the configured maximum exposure threshold.
Threshold: R ≤ maximum configured exposure limit. In trading applications, this corresponds to maximum drawdown per trade as a percentage of total capital under management.

**CP-5: Signal Coherence Gate**
Evaluates: Signal Coherence Score (C).
Purpose: Evaluates the degree of agreement among independent analytical signals. Actions motivated by signals that disagree with one another are blocked or held, as signal disagreement indicates analytical uncertainty that is not captured by any single signal's probability estimate.
Threshold: In one embodiment, C ≥ 0.60. This threshold is configurable; in other embodiments, the minimum coherence requirement may be set to any value appropriate to the deployment context and the number of independent signal sources contributing to the coherence score.

**CP-6: Decision Contradiction Index (DCI) Gate**
Evaluates: Logic Consistency Score (L), computed by the DCI Module (described in Section VI).
Purpose: Detects internal signal contradiction among independent signal sources as a distinct veto condition. Issues a BLOCK verdict when the DCI score exceeds the CONTRADICTORY threshold, regardless of the values of any other governance signals.
Threshold: In one embodiment, DCI score < 70 is required to pass, with DCI ≥ 70 classified as CONTRADICTORY (BLOCK), DCI 35–69 classified as TENSIONED (degraded confidence mode), and DCI < 35 classified as ALIGNED. The specific threshold values are configurable; in other embodiments, the classification boundaries may be set to any values appropriate to the deployment context, provided that the three-tier classification structure (aligned / tensioned / contradictory) and the mandatory BLOCK behavior at the contradictory threshold are preserved.

**CP-7: Evidence Integrity Gate**
Evaluates: Quality, completeness, and provenance of the evidence base underlying the proposed action.
Purpose: Ensures that the proposed action is supported by a complete and traceable evidence chain, and that the evidence has not been corrupted, fabricated, or derived from inadmissible sources.
Threshold: Evidence integrity score ≥ configured minimum. All required evidence fields must be present and traceable to verified data sources.

**CP-8: Stress Test Gate**
Evaluates: Stress Resilience Score (S).
Purpose: Ensures that the proposed action demonstrates acceptable performance under adverse simulated conditions. Actions that perform acceptably under favorable conditions but collapse under stress scenarios are blocked.
Threshold: S ≥ 0.50. In trading applications, this corresponds to a positive expected return across Monte Carlo stress scenarios.

**CP-9: Audit Traceability Gate**
Evaluates: Completeness of the decision trace data structure to this point in the pipeline.
Purpose: Verifies that all preceding checkpoint evaluations have been recorded in the decision trace with sufficient detail to constitute a complete audit record. This checkpoint ensures that the governance architecture produces a defensible audit trail as a structural property of every decision, not as an optional logging feature.
Threshold: Decision trace must contain a complete evaluation record for each of CP-0 through CP-8.

**CP-10: Fraud and Anomaly Detection Gate**
Evaluates: Anomaly indicators, including behavioral deviation from historical patterns, unusual timing, unusual volume, and cross-signal anomaly patterns.
Purpose: Detects potential system compromise, data injection attacks, or unauthorized manipulation of the decision pipeline. Actions exhibiting anomaly patterns inconsistent with legitimate system behavior are blocked.
Threshold: Anomaly score ≤ configured maximum. Zero-day anomaly detection uses unsupervised deviation scoring from behavioral baseline.

**CP-11: Final Admissibility Gate**
Evaluates: Composite governance signal from all preceding checkpoints.
Purpose: Performs a final holistic evaluation of the proposed action before the execution commitment is issued. Confirms that all preceding checkpoints have rendered PASS verdicts, that no checkpoint has been bypassed, and that the proposed action has traversed the complete pipeline.
Threshold: All of CP-0 through CP-10 must have returned PASS verdicts. Any missing checkpoint result triggers BLOCK.

**TIE: Trajectory Invariant Enforcement**
Evaluates: Post-execution state consistency.
Purpose: After execution commitment, the TIE layer verifies that the resulting system state is consistent with the system's established behavioral trajectory. If the post-execution state represents an inadmissible deviation, the TIE layer flags the event for human review and may trigger circuit-breaker protocols. The TIE layer does not block execution (which has already occurred) but provides the final layer of the governance audit trail and triggers corrective protocols when necessary.

### IV. DECISION TRACE GENERATOR (130)

The Decision Trace Generator (130) assembles and persists the complete governance record for each proposed action evaluated by the System. The decision trace is a structured data object comprising the following fields:

- **decision_id:** A universally unique identifier (UUID) for the proposed action.
- **timestamp:** The precise timestamp (UTC, millisecond resolution) at which the governance evaluation was initiated.
- **domain:** The institutional domain of the proposed action (e.g., "TRADING", "INSURANCE", "CREDIT").
- **proposed_action:** A structured representation of the proposed action, including all relevant parameters.
- **governance_signals:** The complete normalized governance signal set (P, R, C, T, S, L) with provenance metadata.
- **checkpoint_results:** An ordered array of checkpoint evaluation records, one per checkpoint, each comprising: checkpoint identifier, signals evaluated, thresholds applied, verdict issued, reason for verdict, and evaluation timestamp.
- **final_verdict:** The overall governance verdict (APPROVE, HOLD, or BLOCK) and the checkpoint that triggered any non-APPROVE verdict.
- **cryptographic_receipt:** A post-quantum cryptographic digital signature over the complete decision trace, generated using Dilithium-3 (ML-DSA-65) as specified in NIST FIPS 204. This signature provides tamper-evident, quantum-resistant evidence of the governance decision.
- **parameter_version:** The version identifier of the governance parameters (checkpoint thresholds, domain adapter configuration) in effect at the time of the evaluation.
- **snapshot_id:** A reference to the market or environmental data snapshot against which the governance signals were evaluated.

The decision trace is persisted to a write-once audit log with cryptographic integrity protection. In a preferred embodiment, the audit log is stored in a distributed ledger to provide additional tamper-evidence guarantees.

### V. COUNTERFACTUAL SHADOW PORTFOLIO SYSTEM (140)

Referring to FIG. 3, the Counterfactual Shadow Portfolio System (140) provides a mechanism for continuous, self-calibrating evaluation of the accuracy of the governance system's veto decisions.

#### V.A. Shadow Event Logger Module

When the governance engine issues a BLOCK verdict for a proposed action, the Shadow Event Logger Module captures and stores a complete Shadow Event Record comprising the following fields:

- **shadow_event_id:** A unique identifier for the shadow event.
- **timestamp:** The timestamp of the blocked action.
- **asset_or_instrument:** The specific asset, instrument, or subject of the blocked action.
- **proposed_action_type:** The type of action that was blocked (e.g., BUY, SELL, APPROVE, REJECT).
- **proposed_action_parameters:** All relevant parameters of the blocked action.
- **governance_signals_at_veto:** The complete normalized governance signal set at the time of the veto.
- **blocking_checkpoint:** The checkpoint identifier that issued the blocking verdict.
- **veto_reason:** The detailed reason for the blocking verdict.
- **market_microstructure:** Market microstructure data at the time of the veto, including bid-ask spread, order book depth, and recent realized volatility (for financial domain applications).
- **evaluation_window:** The predetermined time window after which the counterfactual outcome will be evaluated.

#### V.B. Outcome Tracker Module

After the expiration of the evaluation window for each Shadow Event Record, the Outcome Tracker Module records the actual market or environmental outcome that would have occurred had the blocked action been permitted to execute. The outcome record includes:

- **actual_outcome:** The realized value or result of the relevant instrument, asset, or subject at the end of the evaluation window.
- **counterfactual_pnl:** The profit or loss (or equivalent domain metric) that would have resulted from the blocked action, computed by comparing the proposed action parameters against the actual outcome.
- **outcome_timestamp:** The timestamp of the outcome recording.

#### V.C. Counterfactual Analyzer Module

The Counterfactual Analyzer Module compares the outcome of each vetoed action against the intended action outcome to classify each veto as one of:

- **CORRECT_VETO (Capital-Preserving):** The veto prevented an action that would have resulted in a loss or adverse outcome. The blocking checkpoint made a correct governance decision.
- **INCORRECT_VETO (Opportunity-Blocking):** The veto prevented an action that would have resulted in a favorable outcome. The blocking checkpoint made an overly conservative governance decision.

The Counterfactual Analyzer accumulates these classifications over time, computing the following metrics per blocking checkpoint:

- **veto_accuracy_rate:** The fraction of vetos classified as CORRECT_VETO over a configurable trailing analysis window.
- **opportunity_cost_rate:** The fraction of vetos classified as INCORRECT_VETO over the same window.
- **aggregate_counterfactual_pnl:** The cumulative profit or loss attributable to veto decisions by each checkpoint over the analysis window.

#### V.D. Calibration Engine Module

The Calibration Engine Module generates threshold adjustment recommendations based on aggregate counterfactual analysis. If a checkpoint's veto_accuracy_rate falls below a configurable minimum threshold, the Calibration Engine recommends relaxing the checkpoint's thresholds. If a checkpoint's opportunity_cost_rate falls below a configurable minimum threshold, the Calibration Engine recommends tightening the checkpoint's thresholds.

In a preferred embodiment, threshold adjustment recommendations are not automatically applied to the governance checkpoint pipeline. All recommendations are presented to a designated human reviewer for approval prior to implementation. This design ensures that the self-calibration mechanism does not create an automated pathway for weakening governance controls without human oversight.

### VI. DECISION CONTRADICTION INDEX (DCI) MODULE (150)

Referring to FIG. 4, the Decision Contradiction Index (DCI) Module computes a quantitative measure of internal signal contradiction among a plurality of independent signal sources.

#### VI.A. Signal Sources

In a preferred embodiment, the DCI Module receives output values from at least five independent internal signal sources, comprising:

1. **EMA Regime Signal:** The directional verdict (bullish / bearish / neutral) derived from exponential moving average analysis.
2. **HMM Regime Signal:** The regime state (trending / ranging / volatile / transitional) identified by a Hidden Markov Model applied to the time-series of the relevant instrument or subject.
3. **Kalman Filter Estimate:** The state estimate generated by a Kalman filter tracking the relevant instrument or subject.
4. **Non-Markovian Memory Kernel Signal:** The regime classification generated by the Non-Markovian Memory Kernel (described in related provisional application OMNIX-PAT-2026-002).
5. **Kelly Criterion Capital Allocation Signal:** The position size recommendation generated by a Kelly Criterion-based capital allocation model.

Additional signal sources may be added without departing from the scope of the invention.

#### VI.B. DCI Computation

The DCI score is computed by measuring pairwise divergence among the plurality of independent signal sources. The DCI score quantifies the degree to which the independent signals disagree with one another, rather than aggregating them into a consensus value.

In a preferred embodiment, the DCI score is computed as follows:

1. Each signal source is mapped to a directional vector on a normalized scale.
2. For each pair of signal sources, a pairwise divergence value is computed as the absolute difference between the two directional vectors, normalized to the range [0, 100].
3. The DCI score is the arithmetic mean of all pairwise divergence values across all signal pairs.

The DCI score is thus a number in the range [0, 100], where 0 indicates perfect agreement among all signal sources and 100 indicates maximum disagreement.

#### VI.C. DCI Classification

The DCI score is classified according to the following threshold structure:

| DCI Score | Classification | Governance Action |
|-----------|---------------|-------------------|
| 0 – 34 | ALIGNED | Normal governance evaluation proceeds |
| 35 – 69 | TENSIONED | Degraded confidence mode: position sizes reduced; additional confirmation required |
| 70 – 100 | CONTRADICTORY | Mandatory HOLD/BLOCK: proposed action blocked regardless of other checkpoint verdicts |

#### VI.D. Architectural Distinctiveness from Consensus Aggregation

The DCI is architecturally distinct from consensus aggregation approaches in the following respect: consensus aggregation computes a single composite value from multiple signals and loses information about the distribution of individual signal values. A situation in which three signals indicate strong positive direction and two signals indicate strong negative direction produces a composite value indistinguishable from a situation in which all five signals indicate moderate positive direction. The DCI explicitly detects and acts on the former situation, treating it as a state of dangerous internal contradiction rather than as a state of moderate confidence.

---

## ALTERNATIVE EMBODIMENTS

### Embodiment A: Dynamic Checkpoint Count

The system may operate with a fixed number of checkpoints (as in the preferred embodiment of eleven checkpoints designated CP-0 through CP-11), a dynamic number of checkpoints selected based on the deployment domain and risk profile, or an adaptive structure in which checkpoints are added or removed from the pipeline based on governance requirements. The critical structural property — that each checkpoint has independent veto authority and that the default behavior on evaluation failure is BLOCK — is preserved across all embodiments regardless of the number of checkpoints.

### Embodiment B: Weighted Checkpoint Pipeline

In an alternative embodiment, checkpoints may be assigned configurable priority weights that determine the order in which their veto signals are evaluated. In this embodiment, a high-priority checkpoint's BLOCK verdict may immediately terminate pipeline evaluation without evaluating lower-priority checkpoints, reducing computational latency for clearly inadmissible actions while preserving the fail-closed guarantee.

### Embodiment C: Parallel Checkpoint Evaluation

In an alternative embodiment, checkpoints that evaluate independent signals without temporal dependencies may be evaluated in parallel rather than strictly sequentially. The final governance verdict is determined by aggregating checkpoint verdicts after parallel evaluation: any BLOCK verdict from any checkpoint in the parallel set produces a BLOCK verdict for the pipeline, regardless of the results of other checkpoints.

### Embodiment D: Domain-Specific Checkpoint Composition

In an alternative embodiment, the set of active checkpoints in the pipeline is composed differently for each deployment domain. A financial trading deployment may activate all eleven checkpoints; a healthcare AI deployment may substitute domain-specific checkpoints (e.g., a clinical evidence quality checkpoint) for trading-specific checkpoints (e.g., a signal agreement checkpoint), while preserving the same pipeline architecture, fail-closed default, and decision trace generation.

### Embodiment E: Federated Multi-Tenant Governance

In an alternative embodiment, the governance checkpoint pipeline is deployed as a multi-tenant service in which multiple institutional clients share the same pipeline infrastructure but maintain independent checkpoint threshold configurations, domain adapter modules, and audit logs. Each tenant's governance decisions are cryptographically isolated from other tenants.

### Embodiment F: Distributed Ledger Audit Log

In an alternative embodiment, the decision trace generated for each evaluated action is stored in a distributed ledger (blockchain) rather than a centralized write-once audit log, providing additional tamper-evidence guarantees through the consensus mechanism of the distributed ledger network.

---

## CLAIMS

*(Note: Claims are included in this provisional application for reference purposes. Formal claims will be refined in the corresponding nonprovisional application filed within 12 months of this provisional's priority date.)*

**Claim 1** — A computer-implemented method for governing high-stakes automated decisions, comprising: receiving domain-specific input data; transforming said data into a set of normalized governance signals through a domain adapter module; evaluating said normalized governance signals through a sequential pipeline of a plurality of independent checkpoints, each having independent veto authority; and generating a governance decision comprising one of APPROVE, HOLD, or BLOCK, together with a complete decision trace recording the evaluation result of each checkpoint.

**Claim 2** — The method of Claim 1, wherein the default behavior when any checkpoint is unable to evaluate its assigned signals is to issue a BLOCK verdict.

**Claim 3** — The method of Claim 1, wherein said normalized governance signals comprise at minimum a probability score, a risk exposure score, a signal coherence score, a trend persistence score, a stress resilience score, and a logic consistency score, each normalized to a common numerical scale.

**Claim 4** — The method of Claim 1, wherein said domain adapter module is interchangeable and the method further comprises selecting a domain adapter module from a set comprising adapters for at least two of: financial trading, insurance underwriting, credit evaluation, supply chain management, and healthcare AI.

**Claim 5** — The method of Claim 1, wherein said complete decision trace is cryptographically sealed using a post-quantum digital signature algorithm.

**Claim 6** — A computer-implemented system for calibrating risk management filters in an automated governance system, comprising: a shadow event logger that records the complete decision context of each blocked action; an outcome tracker that records the actual outcome that would have resulted from each blocked action; a counterfactual analyzer that classifies each blocked action as capital-preserving or opportunity-blocking based on the comparison of intended and actual outcomes; and a calibration engine that generates threshold adjustment recommendations based on aggregate counterfactual classification data.

**Claim 7** — The system of Claim 6, wherein threshold adjustment recommendations generated by the calibration engine are presented for human review and approval prior to implementation.

**Claim 8** — A computer-implemented method for detecting internal signal contradiction in an automated decision system, comprising: receiving output values from a plurality of independent internal signal sources; computing a Decision Contradiction Index (DCI) score by measuring pairwise divergence among said signal sources; classifying the internal signal state as ALIGNED, TENSIONED, or CONTRADICTORY based on said DCI score; and issuing a veto signal that blocks the proposed action when the DCI score is classified as CONTRADICTORY.

**Claim 9** — The method of Claim 8, wherein the DCI score classifies as CONTRADICTORY when said score is greater than or equal to 70 on a normalized scale of 0 to 100.

**Claim 10** — The method of Claim 8, wherein computing said DCI score comprises measuring pairwise divergence among at least five independent signal sources comprising an exponential moving average signal, a hidden Markov model signal, a Kalman filter estimate, a non-Markovian memory kernel signal, and a Kelly criterion capital allocation signal.

**Claim 11 (Broad System — Maximum Coverage)** — A system configured to enforce pre-execution governance over automated decisions, the system comprising one or more processors and a non-transitory computer-readable medium storing instructions that cause the system to: receive a proposed action from a decision generation subsystem; evaluate said proposed action through a plurality of independent enforcement units, each having authority to independently prevent said proposed action from reaching an execution environment; and generate a tamper-evident record of the evaluation of said proposed action prior to any execution commitment, wherein the default behavior of each enforcement unit when unable to complete its evaluation is to prevent execution.

**Claim 12 (Broad Method — Maximum Coverage)** — A computer-implemented method for preventing inadmissible automated actions from reaching an execution environment, comprising: receiving a proposed action; evaluating said proposed action through a sequential pipeline in which each stage independently determines whether said proposed action satisfies its assigned admissibility criteria; blocking said proposed action from execution if any stage determines that its admissibility criteria are not satisfied; and generating a cryptographically sealed record of the evaluation prior to any execution commitment.

---

## ABSTRACT

A computer-implemented governance control architecture enforces decision admissibility in automated decision systems through three integrated components. A domain-agnostic governance engine transforms domain-specific inputs into normalized governance signals and evaluates proposed actions through a sequential pipeline of independent checkpoints, each having veto authority and defaulting to block on uncertainty (fail-closed). A counterfactual shadow portfolio system records blocked actions, tracks their actual subsequent outcomes, classifies each veto as capital-preserving or opportunity-blocking, and generates threshold calibration recommendations based on aggregate accuracy analysis. A Decision Contradiction Index (DCI) detects internal signal divergence among independent analytical sources by measuring pairwise disagreement — as distinct from consensus aggregation — and mandates conservative action when disagreement exceeds a threshold. The architecture generates a cryptographically sealed, tamper-evident decision trace for every evaluated action. The domain adapter architecture enables identical checkpoint logic to govern decisions across financial trading, insurance underwriting, credit evaluation, supply chain management, healthcare AI, and other institutional domains.

---

## DRAWINGS

### FIG. 1 — System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    OMNIX GOVERNANCE ENGINE                          │
│                                                                     │
│  ┌─────────────────┐     ┌──────────────────────────────────────┐  │
│  │  DECISION       │     │  DOMAIN ADAPTER MODULE (110)         │  │
│  │  GENERATION     │────►│                                      │  │
│  │  SUBSYSTEM      │     │  Input: Domain-Specific Data         │  │
│  │  (External)     │     │  Output: Normalized Signal Set       │  │
│  └─────────────────┘     │  (P, R, C, T, S, L) ∈ [0.0, 1.0]  │  │
│                           └──────────────┬───────────────────────┘  │
│                                          │                           │
│                           ┌──────────────▼───────────────────────┐  │
│                           │  SEQUENTIAL CHECKPOINT PIPELINE (120) │  │
│                           │                                       │  │
│                           │  CP-0 → CP-1 → CP-2 → CP-3 → CP-4  │  │
│                           │  → CP-5 → CP-6(DCI) → CP-7 → CP-8  │  │
│                           │  → CP-9 → CP-10 → CP-11 → TIE       │  │
│                           │                                       │  │
│                           │  Each CP: Independent Veto Authority  │  │
│                           │  Default: FAIL-CLOSED (BLOCK)        │  │
│                           └──────────────┬────────────┬──────────┘  │
│                                          │            │              │
│                           ┌──────────────▼──┐  ┌─────▼───────────┐ │
│                           │ DECISION TRACE  │  │ SHADOW PORTFOLIO│ │
│                           │ GENERATOR (130) │  │ SYSTEM (140)    │ │
│                           │                 │  │                 │ │
│                           │ PQC-Sealed      │  │ Shadow Logger   │ │
│                           │ Audit Receipt   │  │ Outcome Tracker │ │
│                           │                 │  │ Counterfactual  │ │
│                           └────────────┬────┘  │ Analyzer        │ │
│                                        │        │ Calibration Eng │ │
│                           ┌────────────▼────┐  └─────────────────┘ │
│                           │  EXECUTION      │                        │
│                           │  ENVIRONMENT    │                        │
│                           │  (if APPROVED)  │                        │
│                           └─────────────────┘                        │
└─────────────────────────────────────────────────────────────────────┘
```

### FIG. 2 — Sequential Checkpoint Pipeline Process Flow

```
START: Proposed Action Received
          │
          ▼
┌─────────────────────┐
│ CP-0: Signal        │──BLOCK──► BLOCK VERDICT + TRACE ENTRY
│ Integrity Gate      │
└──────────┬──────────┘
           │ PASS
           ▼
┌─────────────────────┐
│ CP-1: Context       │──BLOCK──► BLOCK VERDICT + TRACE ENTRY
│ Admission Gate      │
└──────────┬──────────┘
           │ PASS
           ▼
┌─────────────────────┐
│ CP-2: Probability   │──BLOCK──► BLOCK VERDICT + TRACE ENTRY
│ Threshold Gate      │
│ (P ≥ 0.52)          │
└──────────┬──────────┘
           │ PASS
           ▼
┌─────────────────────┐
│ CP-3: Temporal      │──BLOCK──► BLOCK VERDICT + TRACE ENTRY
│ Coherence Gate      │
└──────────┬──────────┘
           │ PASS
           ▼
┌─────────────────────┐
│ CP-4: Risk Limits   │──BLOCK──► BLOCK VERDICT + TRACE ENTRY
│ Gate                │
└──────────┬──────────┘
           │ PASS
           ▼
┌─────────────────────┐
│ CP-5: Signal        │──BLOCK──► BLOCK VERDICT + TRACE ENTRY
│ Coherence Gate      │
│ (C ≥ 0.60)          │
└──────────┬──────────┘
           │ PASS
           ▼
┌─────────────────────┐
│ CP-6: DCI Gate      │──BLOCK──► BLOCK VERDICT + TRACE ENTRY
│ (DCI < 70)          │  (if CONTRADICTORY)
└──────────┬──────────┘
           │ PASS
           ▼
┌─────────────────────┐
│ CP-7 through CP-11  │──BLOCK──► BLOCK VERDICT + TRACE ENTRY
│ (Sequential)        │
└──────────┬──────────┘
           │ ALL PASS
           ▼
┌─────────────────────┐
│ APPROVE VERDICT     │
│ PQC-Sealed Receipt  │
│ Generated           │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ EXECUTION           │
│ COMMITMENT          │
└──────────┬──────────┘
           │
           ▼
    TIE POST-EXECUTION
    VERIFICATION
```

### FIG. 3 — Counterfactual Shadow Portfolio System

```
BLOCK VERDICT ISSUED
          │
          ▼
┌─────────────────────────┐
│ SHADOW EVENT LOGGER     │
│                         │
│ Records:                │
│ • decision_id           │
│ • timestamp             │
│ • proposed_action       │
│ • governance_signals    │
│ • blocking_checkpoint   │
│ • market_microstructure │
│ • evaluation_window     │
└────────────┬────────────┘
             │ After evaluation_window expires
             ▼
┌─────────────────────────┐
│ OUTCOME TRACKER         │
│                         │
│ Records:                │
│ • actual_outcome        │
│ • counterfactual_pnl    │
│ • outcome_timestamp     │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ COUNTERFACTUAL ANALYZER │
│                         │
│ Classification:         │
│ CORRECT_VETO            │
│   (loss prevented)      │
│ or                      │
│ INCORRECT_VETO          │
│   (gain prevented)      │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ CALIBRATION ENGINE      │
│                         │
│ Computes per checkpoint:│
│ • veto_accuracy_rate    │
│ • opportunity_cost_rate │
│ • aggregate_pnl         │
│                         │
│ Generates:              │
│ Threshold Adjustment    │
│ Recommendations         │
│ (Human Review Required) │
└─────────────────────────┘
```

### FIG. 4 — Decision Contradiction Index (DCI) Signal State Diagram

```
INDEPENDENT SIGNAL SOURCES (minimum 5):
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│  EMA     │ │  HMM     │ │  KALMAN  │ │ NON-MARK │ │  KELLY   │
│  SIGNAL  │ │  REGIME  │ │  FILTER  │ │  KERNEL  │ │ CRITERION│
└────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
     │             │             │             │             │
     └─────────────┴─────────────┴─────────────┴─────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │   PAIRWISE DIVERGENCE  │
                    │   COMPUTATION          │
                    │                        │
                    │ DCI = mean of all      │
                    │ pairwise |Si - Sj|     │
                    │ normalized to [0, 100] │
                    └────────────┬───────────┘
                                 │
                                 ▼
              ┌──────────────────────────────────────┐
              │         DCI CLASSIFICATION           │
              │                                      │
              │  DCI 0–34   → ALIGNED                │
              │              ↓ Normal Evaluation      │
              │                                      │
              │  DCI 35–69  → TENSIONED              │
              │              ↓ Reduced Position Size  │
              │                                      │
              │  DCI 70–100 → CONTRADICTORY          │
              │              ↓ MANDATORY BLOCK        │
              └──────────────────────────────────────┘
```

---

*End of Specification — Patent Family 1*
*Document Reference: OMNIX-PAT-2026-001*
*Inventor: Harold Alberto Nunes Rodelo*
*Date: [DATE OF FILING]*
*© 2026 OMNIX Quantum Ltd. All rights reserved. CONFIDENTIAL.*
