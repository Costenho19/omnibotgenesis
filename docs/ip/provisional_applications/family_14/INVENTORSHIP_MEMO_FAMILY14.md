# INVENTORSHIP MEMO — FAMILY 14
## OMNIX-PAT-2026-014

**Invention:** Bidirectional Temporal Admissibility System (TCV + FTI)
**Inventor:** Harold Alberto Nunes Rodelo — April 19, 2026

## INVENTIVE CONTRIBUTIONS

1. **Bidirectional Temporal Admissibility Concept:** Design of the unified bilateral temporal assessment framework that simultaneously evaluates a governance decision against both the recent historical trajectory (retrospective) and the probable near-future trajectory (prospective) as a single combined admissibility gate.

2. **Three-Dimensional Retrospective Score (TCV):** Design of the composite scoring formula combining Direction Coherence (monotonicity of signal deltas), Regime-Action Alignment (proposed action vs. dominant historical regime), and Signal Stability (inverse direction-flip rate) — with configurable dimensional weights.

3. **Dual-Source Unbiased History:** Design of the dual-source history mechanism that combines shadow_trade_events (blocked decisions) and paper_trading_trades (approved decisions) to provide a complete, survivorship-bias-free view of the decision trajectory.

4. **HMM Adverse Regime Transition Risk (FTI):** Design of the adverse regime transition risk calculation using regime persistence probabilities and action-specific adverse regime sets — mapping the prospective governance problem to an HMM transition risk estimation.

5. **Bilateral Compound Blocking with Compound Reason:** Design of the bilateral blocking logic and the compound reason generation that identifies both the retrospective and prospective sources of temporal incoherence when both modules block simultaneously.

## REDUCTION TO PRACTICE
- `omnix_core/temporal/coherence_validator.py` — TCV, ADR-032, March 2026
- `omnix_core/temporal/forward_trajectory.py` — FTI, ADR-034, March 2026
Git hashes: [RETRIEVE BEFORE FILING]
