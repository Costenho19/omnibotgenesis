"""
OMNIX Insurance Governance Signal Adapter
ADR-054: Insurance Governance Vertical

Maps insurance claim parameters to OMNIX's 6 normalized governance signals (0-100).
This adapter makes the governance pipeline domain-agnostic — the same 11-checkpoint
engine that governs trading decisions now governs insurance claim approvals.

Signal mapping:
  probability_score   → Claim legitimacy probability (coverage match, history, evidence)
  risk_exposure       → Loss severity index (claim/limit ratio, fraud indicators)
  signal_coherence    → Evidence consistency (all documents and data align)
  trend_persistence   → Loss ratio stability (macro underwriting conditions)
  stress_resilience   → Reserve adequacy (insurer capacity to absorb this claim)
  logic_consistency   → Policy-claim alignment (no internal contradictions)

Supported insurance types:
  Auto, Property, Life, Health, Liability, Cyber, Marine, D&O
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("OMNIX.Insurance.SignalAdapter")

# Fraud risk thresholds by claim type
FRAUD_RISK_BASELINE: dict[str, float] = {
    "Auto": 18.0,
    "Property": 22.0,
    "Life": 8.0,
    "Health": 25.0,
    "Liability": 15.0,
    "Cyber": 12.0,
    "Marine": 10.0,
    "D&O": 9.0,
}

# Coverage ratio limits (claim_amount / policy_limit)
MAX_COVERAGE_RATIO = 1.0        # Cannot exceed policy limit
SUSPICIOUS_COVERAGE_RATIO = 0.95  # High ratio triggers scrutiny

# Loss ratio benchmarks by region
LOSS_RATIO_BENCHMARK: dict[str, float] = {
    "NA": 65.0,
    "EU": 70.0,
    "APAC": 72.0,
    "LATAM": 78.0,
    "MEA": 75.0,
    "GLOBAL": 68.0,
}


@dataclass
class InsuranceClaimInput:
    """Raw insurance claim parameters before signal adaptation."""
    claimant_type: str              # Individual, SME, Corporate, Institutional
    insurance_type: str             # Auto, Property, Life, Health, Liability, Cyber
    region: str                     # NA, EU, APAC, LATAM, MEA
    claim_amount_usd: float         # Claimed loss amount
    policy_limit_usd: float         # Maximum policy coverage
    claimant_history_score: float   # 0-100: clean history=100, prior fraud=0
    fraud_indicators: float         # 0-100: no indicators=0, strong indicators=100
    evidence_completeness: float    # 0-100: full documentation=100
    loss_ratio_trend: float         # 0-100: improving=100, deteriorating=0
    reserve_adequacy: float         # 0-100: fully reserved=100, under-reserved=0
    policy_claim_alignment: float   # 0-100: perfect match=100, contradictions=0
    incident_days_ago: int = 30     # Days since incident occurred
    prior_claims_count: int = 0     # Number of prior claims (last 5 years)
    is_catastrophe_event: bool = False  # CAT event (hurricane, earthquake, etc.)


@dataclass
class InsuranceGovernanceSignals:
    """6 normalized OMNIX governance signals for insurance domain."""
    probability_score: float    # 0-100: claim legitimacy probability
    risk_exposure: float        # 0-100: loss severity index (lower = safer)
    signal_coherence: float     # 0-100: evidence consistency
    trend_persistence: float    # 0-100: underwriting condition stability
    stress_resilience: float    # 0-100: reserve adequacy
    logic_consistency: float    # 0-100: policy-claim alignment

    # Metadata for dashboard display
    coverage_ratio: float = 0.0
    fraud_risk_adjusted: float = 0.0
    recommendation: str = ""

    def to_omnix_dict(self) -> dict:
        """Format for the OMNIX governance engine."""
        return {
            "probability_score": round(self.probability_score, 2),
            "risk_exposure": round(self.risk_exposure, 2),
            "signal_coherence": round(self.signal_coherence, 2),
            "trend_persistence": round(self.trend_persistence, 2),
            "stress_resilience": round(self.stress_resilience, 2),
            "logic_consistency": round(self.logic_consistency, 2),
        }


class InsuranceSignalAdapter:
    """
    Translates insurance claim parameters into OMNIX governance signals.
    The governance engine receives normalized 0-100 signals — it does not
    know it is evaluating an insurance claim vs a trade vs a credit application.
    """

    def adapt(self, claim: InsuranceClaimInput) -> InsuranceGovernanceSignals:
        """Convert raw claim parameters to 6 OMNIX governance signals."""
        try:
            coverage_ratio = min(claim.claim_amount_usd / max(claim.policy_limit_usd, 1), 1.0)
            fraud_baseline = FRAUD_RISK_BASELINE.get(claim.insurance_type, 15.0)
            benchmark_lr = LOSS_RATIO_BENCHMARK.get(claim.region, 68.0)

            # ── Signal 1: Probability Score (Claim Legitimacy) ──
            # Higher = more legitimate claim
            base_prob = claim.claimant_history_score * 0.35
            evidence_contribution = claim.evidence_completeness * 0.30
            alignment_contribution = claim.policy_claim_alignment * 0.25
            # Fraud adjustment — strong fraud indicators reduce legitimacy
            fraud_penalty = min(claim.fraud_indicators * 0.40, 40.0)
            # CAT events slightly reduce suspicion (corroborated by external event)
            cat_bonus = 5.0 if claim.is_catastrophe_event else 0.0
            # Prior claims penalty (each prior claim reduces legitimacy slightly)
            prior_penalty = min(claim.prior_claims_count * 3.0, 18.0)
            probability_score = max(0.0, min(100.0,
                base_prob + evidence_contribution + alignment_contribution
                - fraud_penalty + cat_bonus - prior_penalty + 10.0
            ))

            # ── Signal 2: Risk Exposure (Loss Severity) ──
            # Higher = more exposure (bad) → we invert so lower = safer for the engine
            coverage_risk = coverage_ratio * 60.0
            fraud_risk = (claim.fraud_indicators / 100.0) * fraud_baseline
            incident_age_factor = max(0.0, (90 - claim.incident_days_ago) / 90.0) * 10.0
            raw_exposure = coverage_risk + fraud_risk + incident_age_factor
            risk_exposure = max(0.0, min(100.0, raw_exposure))

            # ── Signal 3: Signal Coherence (Evidence Consistency) ──
            coherence_base = claim.evidence_completeness * 0.50
            history_coherence = claim.claimant_history_score * 0.30
            alignment_coherence = claim.policy_claim_alignment * 0.20
            # Inconsistency penalty if fraud indicators are high despite good history
            internal_contradiction = 0.0
            if claim.claimant_history_score > 80 and claim.fraud_indicators > 60:
                internal_contradiction = 15.0  # Suspicious mismatch
            signal_coherence = max(0.0, min(100.0,
                coherence_base + history_coherence + alignment_coherence - internal_contradiction
            ))

            # ── Signal 4: Trend Persistence (Market Stability) ──
            trend_base = claim.loss_ratio_trend * 0.60
            benchmark_factor = max(0.0, (100 - benchmark_lr) / 100.0 * 40.0)
            cat_penalty = 20.0 if claim.is_catastrophe_event else 0.0
            trend_persistence = max(0.0, min(100.0,
                trend_base + benchmark_factor - cat_penalty
            ))

            # ── Signal 5: Stress Resilience (Reserve Adequacy) ──
            reserve_base = claim.reserve_adequacy * 0.70
            # Large claims strain reserves more
            size_factor = math.exp(-coverage_ratio * 0.5) * 30.0
            stress_resilience = max(0.0, min(100.0, reserve_base + size_factor))

            # ── Signal 6: Logic Consistency (Policy-Claim Alignment) ──
            logic_base = claim.policy_claim_alignment * 0.60
            evidence_logic = claim.evidence_completeness * 0.25
            fraud_logic_penalty = min(claim.fraud_indicators * 0.30, 25.0)
            logic_consistency = max(0.0, min(100.0,
                logic_base + evidence_logic - fraud_logic_penalty
            ))

            # Recommendation
            composite = (probability_score + (100 - risk_exposure) + signal_coherence
                         + trend_persistence + stress_resilience + logic_consistency) / 6.0
            if composite >= 70:
                rec = "LIKELY_APPROVE"
            elif composite >= 50:
                rec = "REVIEW_REQUIRED"
            else:
                rec = "HIGH_RISK"

            return InsuranceGovernanceSignals(
                probability_score=probability_score,
                risk_exposure=risk_exposure,
                signal_coherence=signal_coherence,
                trend_persistence=trend_persistence,
                stress_resilience=stress_resilience,
                logic_consistency=logic_consistency,
                coverage_ratio=coverage_ratio,
                fraud_risk_adjusted=min(claim.fraud_indicators + fraud_baseline, 100.0),
                recommendation=rec,
            )

        except Exception as e:
            logger.error(f"InsuranceSignalAdapter.adapt error: {e}")
            return InsuranceGovernanceSignals(
                probability_score=50.0,
                risk_exposure=50.0,
                signal_coherence=50.0,
                trend_persistence=50.0,
                stress_resilience=50.0,
                logic_consistency=50.0,
                recommendation="ERROR_FALLBACK",
            )
