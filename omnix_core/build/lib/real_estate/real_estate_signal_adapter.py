"""
OMNIX Real Estate Governance Signal Adapter
ADR-RES-001: Real Estate Governance Vertical

Maps property transaction decision parameters to OMNIX's 6 normalized governance
signals (0-100). The same 11-checkpoint engine that governs trading, credit,
medical AI, and autonomous agent decisions now governs automated property
decisions — valuations, mortgage underwriting, tenant screening, AML alerts,
and algorithmic rental pricing.

Signal mapping:
  probability_score   → AVM valuation confidence (comparable quality, model certainty, data freshness)
  risk_exposure       → Transaction risk index (LTV ratio, price deviation, fraud indicators)
  signal_coherence    → Multi-source data alignment (AVM vs comparables vs market trends)
  trend_persistence   → Market trajectory stability (price trend, demand index, inventory pressure)
  stress_resilience   → Portfolio stress resilience (liquidity, rate sensitivity, vacancy risk)
  logic_consistency   → Regulatory & compliance alignment (AML, Sharia for Islamic, RERA)

Supported decision types:
  property_valuation, mortgage_approval, tenant_screening,
  aml_transaction, rental_pricing

Jurisdictions supported:
  UAE (RERA / DLD), GCC (multi-national), UK (FCA / Land Registry),
  EU (national regulators), GLOBAL

Financing modes:
  Conventional, Murabaha (Islamic cost-plus), Ijarah (Islamic lease-to-own),
  Musharaka (Islamic diminishing partnership)
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("OMNIX.RealEstate.SignalAdapter")

# AVM confidence thresholds by decision type
AVM_CONFIDENCE_THRESHOLDS: dict[str, float] = {
    "property_valuation": 0.70,
    "mortgage_approval": 0.75,
    "tenant_screening": 0.65,
    "aml_transaction": 0.80,
    "rental_pricing": 0.68,
}

# Regulatory strictness by jurisdiction
JURISDICTION_STRICTNESS: dict[str, float] = {
    "UAE": 1.08,    # RERA / Dubai Land Department — increasingly strict post-FATF
    "GCC": 1.04,    # Saudi SAMA, QFMA, CBK — harmonizing standards
    "UK": 1.10,     # FCA regulated mortgages + UKFI AML requirements
    "EU": 1.06,     # MCD Mortgage Credit Directive + AMLD6
    "GLOBAL": 1.00,
}

# Risk amplifiers by market segment (luxury = higher fraud risk)
SEGMENT_RISK_AMPLIFIERS: dict[str, float] = {
    "Luxury":     1.35,   # High-value = elevated AML scrutiny
    "Premium":    1.15,
    "Mid_Market": 1.00,
    "Affordable": 0.90,
}

# Financing compliance strictness (Islamic financing = Sharia screening layer)
FINANCING_STRICTNESS: dict[str, float] = {
    "Conventional": 1.00,
    "Murabaha":     1.12,   # Cost-plus — Sharia Board sign-off required
    "Ijarah":       1.10,   # Lease-to-own — asset ownership transfer scrutiny
    "Musharaka":    1.15,   # Diminishing partnership — complex ratio governance
}

# LTV (Loan-to-Value) maximum thresholds by financing type
LTV_MAX_THRESHOLDS: dict[str, float] = {
    "Conventional": 90.0,   # >90% LTV → hard block
    "Murabaha":     85.0,   # Islamic max per AAOIFI standard
    "Ijarah":       85.0,
    "Musharaka":    80.0,   # Musharaka carries equity risk → stricter
}


@dataclass
class PropertyDecisionInput:
    """Raw property transaction parameters before signal adaptation."""
    decision_type: str          # property_valuation, mortgage_approval, tenant_screening, aml_transaction, rental_pricing
    property_type: str          # Residential, Commercial, Industrial, Mixed_Use, Land
    market_segment: str         # Luxury, Premium, Mid_Market, Affordable
    jurisdiction: str           # UAE, GCC, UK, EU, GLOBAL
    financing_mode: str         # Conventional, Murabaha, Ijarah, Musharaka

    # AVM & valuation signals (0-100)
    comparable_quality: float       # Quality and recency of comparable sales (0-100)
    model_accuracy: float           # AVM model back-test accuracy score (0-100)
    data_freshness: float           # Recency of underlying market data (0-100)
    market_depth: float             # Transaction volume / liquidity in the area (0-100)

    # Transaction risk signals (0-100 unless noted)
    ltv_ratio: float                # Loan-to-Value ratio in % (0-100, higher=riskier)
    price_deviation: float          # % deviation from AVM estimate (0-100)
    aml_risk_score: float           # AML screening composite risk (0-100, higher=riskier)
    comparable_alignment: float     # Inter-source valuation agreement (0-100)

    # Market trajectory signals (0-100)
    market_trend_score: float       # Market price trajectory index (0=declining, 100=rising)
    demand_index: float             # Buyer/renter demand relative to supply (0-100)
    inventory_pressure: float       # Available stock vs absorption rate (0-100, higher=more supply)

    # Stress & resilience signals (0-100)
    liquidity_score: float          # Ease of exit in downside scenario (0-100)
    rate_sensitivity: float         # Sensitivity to interest rate movements (0-100, higher=more sensitive)
    vacancy_risk: float             # Vacancy / void risk for the asset class (0-100, higher=riskier)

    # Compliance & regulatory flags
    aml_flag: bool = False              # AML alert triggered — HARD BLOCK
    rera_compliant: bool = True         # RERA / regulatory compliance status
    sharia_screening_passed: bool = True  # Sharia parameter screening for Islamic financing
    beneficial_owner_verified: bool = True  # UBO verification completed

    # Metadata
    days_since_last_valuation: int = 0   # AVM data staleness in days
    prior_aml_incidents: int = 0         # Historical AML incidents for counterparty


@dataclass
class PropertyGovernanceSignals:
    """6 normalized OMNIX governance signals for real estate domain."""
    probability_score: float    # 0-100: AVM valuation confidence
    risk_exposure: float        # 0-100: transaction risk index (higher = riskier)
    signal_coherence: float     # 0-100: multi-source data alignment
    trend_persistence: float    # 0-100: market trajectory stability
    stress_resilience: float    # 0-100: portfolio stress resilience
    logic_consistency: float    # 0-100: regulatory & compliance alignment

    # Metadata for dashboard display
    avm_threshold: float = 0.0
    adjusted_risk: float = 0.0
    recommendation: str = ""
    jurisdiction_strictness: float = 1.0
    ltv_hard_block: bool = False
    aml_block: bool = False

    def to_omnix_dict(self) -> dict:
        return {
            "probability_score":  round(self.probability_score, 2),
            "risk_exposure":      round(self.risk_exposure, 2),
            "signal_coherence":   round(self.signal_coherence, 2),
            "trend_persistence":  round(self.trend_persistence, 2),
            "stress_resilience":  round(self.stress_resilience, 2),
            "logic_consistency":  round(self.logic_consistency, 2),
        }


class RealEstateSignalAdapter:
    """
    Adapts property transaction parameters to OMNIX governance signals.
    Domain-agnostic: same 11-checkpoint pipeline, real estate vocabulary.
    """

    def adapt(self, decision: PropertyDecisionInput) -> PropertyGovernanceSignals:
        try:
            jx_factor = JURISDICTION_STRICTNESS.get(decision.jurisdiction, 1.0)
            seg_amp = SEGMENT_RISK_AMPLIFIERS.get(decision.market_segment, 1.0)
            fin_strictness = FINANCING_STRICTNESS.get(decision.financing_mode, 1.0)
            avm_threshold = AVM_CONFIDENCE_THRESHOLDS.get(decision.decision_type, 0.70)
            ltv_max = LTV_MAX_THRESHOLDS.get(decision.financing_mode, 90.0)

            # ── Signal 1: Probability Score (AVM Valuation Confidence) ──────────
            # Combines: comparable quality (30%), model accuracy (40%),
            # data freshness (20%), market depth (10%)
            comp_factor  = decision.comparable_quality * 0.30
            model_factor = decision.model_accuracy     * 0.40
            fresh_factor = decision.data_freshness     * 0.20
            depth_factor = decision.market_depth       * 0.10

            # Penalize stale AVM data (>30 days)
            staleness_penalty = min(25.0, max(0.0, (decision.days_since_last_valuation - 30) * 0.5))

            # Jurisdiction tightens the effective threshold
            base_prob = comp_factor + model_factor + fresh_factor + depth_factor - staleness_penalty
            probability_score = max(0.0, min(100.0, base_prob / jx_factor))

            # ── Signal 2: Risk Exposure (Transaction Risk Index) ─────────────────
            # LTV ratio (40%), price deviation from AVM (30%),
            # AML composite score (20%), prior AML incidents (10%)
            ltv_risk   = decision.ltv_ratio      * 0.40
            dev_risk   = decision.price_deviation * 0.30
            aml_risk   = decision.aml_risk_score  * 0.20
            incident_risk = min(20.0, decision.prior_aml_incidents * 5.0)

            raw_risk = (ltv_risk + dev_risk + aml_risk + incident_risk) * seg_amp
            risk_exposure = max(0.0, min(100.0, raw_risk))

            # LTV hard-block check
            ltv_hard_block = decision.ltv_ratio > ltv_max

            # ── Signal 3: Signal Coherence (Multi-Source Data Alignment) ─────────
            # AVM confidence (35%), comparable inter-source agreement (30%),
            # market trend alignment (25%) — price deviation creates incoherence (10%)
            avm_coh  = decision.model_accuracy       * 0.35
            comp_coh = decision.comparable_alignment * 0.30
            mkt_coh  = decision.market_trend_score   * 0.25

            # Price deviation from AVM estimate → incoherence penalty
            deviation_penalty = decision.price_deviation * 0.10
            signal_coherence = max(0.0, min(100.0,
                avm_coh + comp_coh + mkt_coh - deviation_penalty
            ))

            # ── Signal 4: Trend Persistence (Market Trajectory Stability) ────────
            # Rising prices & demand → high persistence; oversupply → drag
            trend_base   = decision.market_trend_score * 0.50
            demand_base  = decision.demand_index        * 0.30
            # Inventory pressure: high supply = negative drag on trend persistence
            inventory_drag = (100.0 - decision.inventory_pressure) * 0.20

            trend_persistence = max(0.0, min(100.0,
                trend_base + demand_base + inventory_drag
            ))

            # ── Signal 5: Stress Resilience (Portfolio Resilience) ───────────────
            # Liquidity (40%), inverse rate sensitivity (30%), inverse vacancy risk (30%)
            liquidity_base = decision.liquidity_score                  * 0.40
            rate_base      = (100.0 - decision.rate_sensitivity)       * 0.30
            vacancy_base   = (100.0 - decision.vacancy_risk)           * 0.30

            # Staleness further erodes resilience confidence
            resilience_penalty = staleness_penalty * 0.4
            stress_resilience = max(0.0, min(100.0,
                liquidity_base + rate_base + vacancy_base - resilience_penalty
            ))

            # ── Signal 6: Logic Consistency (Regulatory Compliance) ──────────────
            # RERA compliance (35%), AML status (35%), financing compliance (30%)
            rera_base = 85.0 if decision.rera_compliant else 0.0
            ubo_base  = 15.0 if decision.beneficial_owner_verified else 0.0

            # AML risk-adjusted compliance score
            aml_compliance = (100.0 - decision.aml_risk_score) * 0.35

            # Financing compliance: Sharia screening for Islamic modes
            if decision.financing_mode in ("Murabaha", "Ijarah", "Musharaka"):
                fin_compliance = 30.0 if decision.sharia_screening_passed else 0.0
            else:
                # Conventional: beneficial owner verification
                fin_compliance = 30.0 if decision.beneficial_owner_verified else 15.0

            raw_compliance = (rera_base + ubo_base) * 0.35 + aml_compliance + fin_compliance
            logic_consistency = max(0.0, min(100.0, raw_compliance / fin_strictness))

            # ── Composite recommendation ─────────────────────────────────────────
            composite = (
                probability_score
                + (100.0 - risk_exposure)
                + signal_coherence
                + trend_persistence
                + stress_resilience
                + logic_consistency
            ) / 6.0

            if decision.aml_flag or ltv_hard_block:
                rec = "HARD_BLOCK"
            elif composite >= 70:
                rec = "LIKELY_APPROVE"
            elif composite >= 52:
                rec = "COMPLIANCE_REVIEW"
            else:
                rec = "HIGH_RISK"

            return PropertyGovernanceSignals(
                probability_score=probability_score,
                risk_exposure=risk_exposure,
                signal_coherence=signal_coherence,
                trend_persistence=trend_persistence,
                stress_resilience=stress_resilience,
                logic_consistency=logic_consistency,
                avm_threshold=avm_threshold * 100.0,
                adjusted_risk=min(risk_exposure * seg_amp, 100.0),
                recommendation=rec,
                jurisdiction_strictness=jx_factor,
                ltv_hard_block=ltv_hard_block,
                aml_block=decision.aml_flag,
            )

        except Exception as e:
            logger.error(f"RealEstateSignalAdapter.adapt error: {e}")
            return PropertyGovernanceSignals(
                probability_score=50.0,
                risk_exposure=50.0,
                signal_coherence=50.0,
                trend_persistence=50.0,
                stress_resilience=50.0,
                logic_consistency=50.0,
                recommendation="ERROR_FALLBACK",
            )
