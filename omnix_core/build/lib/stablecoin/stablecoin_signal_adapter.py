"""
OMNIX Stablecoin Reserve Governance Signal Adapter
ADR-SRG-001: Stablecoin & Tokenization Governance Vertical (INTERNAL)

Maps stablecoin reserve management decision parameters to OMNIX's 6 normalized
governance signals (0-100). The same 11-checkpoint pipeline that governs
trading, credit, insurance, robotics, medical AI, autonomous agents, real estate,
and energy now governs stablecoin reserve decisions — rebalancing, redemptions,
collateral adjustments, peg defense, and yield optimization.

Signal mapping (stablecoin domain):
  probability_score   → Reserve Stability Score (peg health, coverage ratio, liquidity)
  risk_exposure       → Collateral Risk (crypto exposure, concentration, counterparty)
  signal_coherence    → Peg Coherence (on-chain/off-chain alignment, cross-exchange)
  trend_persistence   → Reserve Flow Stability (TVL trend, redemption patterns)
  stress_resilience   → Stress Test Resilience (bank-run buffer, emergency lines)
  logic_consistency   → Regulatory Compliance (MiCA, AML, audit completeness)

Decision types:
  reserve_rebalancing, redemption_processing, collateral_adjustment,
  peg_defense, yield_optimization

Reserve assets:
  US_Treasury_Bills, US_Treasury_Notes, USDC, Repo_Agreements,
  Money_Market_Funds, Commercial_Paper, ETH_Staked, BTC

Regulatory jurisdictions:
  EU_MiCA (most strict — 60% liquid reserves required)
  US_NYDFS, UAE_VARA, SG_MAS, UK_FCA, GCC

Hard block conditions:
  - peg_deviation_pct > 2.0%         → PEG_BREAK_RISK (depeg emergency)
  - reserve_coverage_ratio < 100.0%  → UNDERCOLLATERALIZED (systemic risk)
  - liquid_reserve_ratio < 60.0%     → MICA_LIQUID_BREACH (EU regulatory min)
  - aml_flag = True                  → AML_BLOCK
  - sanctions_flag = True            → SANCTIONS
  - counterparty_credit_default=True → COUNTERPARTY_DEFAULT
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger("OMNIX.Stablecoin.SignalAdapter")

# ── Jurisdiction regulatory strictness multipliers ────────────────────────────
JURISDICTION_STRICTNESS: dict[str, float] = {
    "EU_MiCA":  1.18,   # MiCA — strictest: 60% liquid reserves, 1:1 backing
    "US_NYDFS": 1.12,   # NYDFS BitLicense — monthly reserve attestations
    "UK_FCA":   1.10,   # FCA crypto asset regime — full backing required
    "SG_MAS":   1.08,   # MAS PSA — reserve audit every 6 months
    "UAE_VARA": 1.06,   # Dubai VARA — new but active, full reserve required
    "GCC":      1.04,   # Gulf region — emerging, less strict than EU
}

# ── Reserve asset risk scores (0=safest, 100=riskiest) ────────────────────────
ASSET_RISK_SCORE: dict[str, float] = {
    "US_Treasury_Bills":   2.0,    # Sovereign, liquid, near-zero credit risk
    "Repo_Agreements":     5.0,    # Overnight repos — very safe
    "Money_Market_Funds": 8.0,    # Regulated MMFs — safe
    "US_Treasury_Notes":  10.0,   # Longer duration, small rate risk
    "USDC":               12.0,   # Digital dollar — Circle regulated
    "Commercial_Paper":   28.0,   # Short-term corporate debt, some credit risk
    "ETH_Staked":         55.0,   # Crypto asset — market + slashing risk
    "BTC":                70.0,   # Volatile crypto, not accepted by MiCA
}

# ── Asset MiCA liquidity classification (True=counts as liquid reserve) ───────
ASSET_MICA_LIQUID: dict[str, bool] = {
    "US_Treasury_Bills":   True,
    "Repo_Agreements":     True,
    "Money_Market_Funds":  True,
    "US_Treasury_Notes":   True,
    "USDC":                True,
    "Commercial_Paper":    False,  # Not unconditionally liquid under MiCA
    "ETH_Staked":          False,  # Crypto — not liquid under MiCA
    "BTC":                 False,  # Crypto — not accepted by MiCA
}

# ── Decision type governance weights ─────────────────────────────────────────
DECISION_TYPE_WEIGHTS: dict[str, dict] = {
    "reserve_rebalancing": {
        "stability_weight": 0.35, "risk_weight": 0.25,
        "coherence_weight": 0.20, "resilience_weight": 0.20,
    },
    "redemption_processing": {
        "stability_weight": 0.40, "risk_weight": 0.20,
        "coherence_weight": 0.15, "resilience_weight": 0.25,
    },
    "collateral_adjustment": {
        "stability_weight": 0.30, "risk_weight": 0.35,
        "coherence_weight": 0.15, "resilience_weight": 0.20,
    },
    "peg_defense": {
        "stability_weight": 0.50, "risk_weight": 0.20,
        "coherence_weight": 0.20, "resilience_weight": 0.10,
    },
    "yield_optimization": {
        "stability_weight": 0.20, "risk_weight": 0.40,
        "coherence_weight": 0.20, "resilience_weight": 0.20,
    },
}

# ── Peg deviation hard block thresholds ───────────────────────────────────────
PEG_DEVIATION_HARD_BLOCK   = 2.0    # >2% depeg → HARD BLOCK (systemic risk)
RESERVE_COVERAGE_HARD_BLOCK = 100.0  # <100% coverage → UNDERCOLLATERALIZED
MICA_LIQUID_HARD_BLOCK      = 60.0  # <60% liquid reserves → MiCA breach


@dataclass
class StablecoinDecisionInput:
    """Raw stablecoin reserve governance decision parameters before signal adaptation."""

    decision_type: str      # reserve_rebalancing, redemption_processing, collateral_adjustment, peg_defense, yield_optimization
    reserve_asset: str      # US_Treasury_Bills, US_Treasury_Notes, USDC, Repo_Agreements, Money_Market_Funds, Commercial_Paper, ETH_Staked, BTC
    jurisdiction:  str      # EU_MiCA, US_NYDFS, UAE_VARA, SG_MAS, UK_FCA, GCC

    # Reserve stability parameters
    peg_deviation_pct: float        # Current peg deviation from $1.00 in % (0=perfect)
    reserve_coverage_ratio: float   # Total reserves / total supply × 100 (min 100%)
    liquid_reserve_ratio: float     # Liquid reserves / total reserves × 100 (MiCA min 60%)

    # Collateral risk parameters
    crypto_exposure_pct: float      # % of reserves in crypto assets (0=none, 100=all crypto)
    concentration_risk: float       # Largest single asset % in reserves (0=diversified, 100=100% one asset)
    counterparty_credit_risk: float # Counterparty credit risk score (0=AAA, 100=default imminent)
    reserve_duration_days: float    # Weighted average duration of reserves in days (0=overnight, 365=1yr)

    # Peg coherence parameters
    on_chain_off_chain_alignment: float  # On-chain price vs off-chain attestation alignment (100=perfect)
    cross_exchange_consistency: float    # Price consistency across exchanges (100=consistent)
    oracle_confidence: float             # Oracle price feed confidence (100=high confidence)

    # Reserve flow parameters
    reserve_flow_stability: float    # Reserve inflow/outflow stability over 7d (100=stable)
    tvl_trend_7d: float             # TVL change trend (50=flat, >50=growing, <50=shrinking)
    redemption_pattern_stability: float  # Redemption request pattern regularity (100=predictable)

    # Stress resilience parameters
    instant_liquidity_coverage: float   # Can cover 24h bank-run scenario (100=fully covered)
    emergency_reserve_buffer: float     # Reserves above minimum requirement % (0=at minimum, 100=2x)
    credit_facility_available: float    # Emergency credit lines available (100=fully available)

    # Regulatory compliance parameters
    mica_compliance_score: float         # MiCA compliance checklist score (100=fully compliant)
    aml_screening_completeness: float    # AML/KYC screening completeness (100=complete)
    audit_completeness: float            # Reserve audit completeness (100=fully audited, up to date)

    # Hard block flags
    aml_flag: bool = False               # AML/CFT screening failure → HARD BLOCK
    sanctions_flag: bool = False         # Sanctions list match → HARD BLOCK
    counterparty_credit_default: bool = False  # Counterparty default event → HARD BLOCK

    # Transaction sizing
    transaction_amount_usd: float = 1_000_000.0   # Transaction value in USD
    total_supply_usd: float = 100_000_000.0        # Total stablecoin supply in USD


@dataclass
class StablecoinGovernanceSignals:
    """6 normalized OMNIX governance signals for stablecoin domain."""
    probability_score: float    # 0-100: Reserve Stability Score
    risk_exposure: float        # 0-100: Collateral Risk Exposure
    signal_coherence: float     # 0-100: Peg Coherence
    trend_persistence: float    # 0-100: Reserve Flow Stability
    stress_resilience: float    # 0-100: Stress Test Resilience
    logic_consistency: float    # 0-100: Regulatory Compliance

    # Computed metadata
    peg_deviation_pct: float = 0.0
    reserve_coverage_ratio: float = 0.0
    liquid_reserve_ratio: float = 0.0
    crypto_exposure_pct: float = 0.0
    transaction_risk_usd: float = 0.0
    recommendation: str = ""
    hard_block_reason: str | None = None
    jurisdiction_strictness: float = 1.0

    def to_omnix_dict(self) -> dict:
        return {
            "probability_score":  round(self.probability_score, 2),
            "risk_exposure":      round(self.risk_exposure, 2),
            "signal_coherence":   round(self.signal_coherence, 2),
            "trend_persistence":  round(self.trend_persistence, 2),
            "stress_resilience":  round(self.stress_resilience, 2),
            "logic_consistency":  round(self.logic_consistency, 2),
        }


class StablecoinSignalAdapter:
    """
    Adapts stablecoin reserve governance decision parameters to OMNIX governance signals.
    Domain-agnostic: same 11-checkpoint pipeline, stablecoin vocabulary.

    Hard block conditions (any one triggers immediate BLOCK):
      - peg_deviation_pct > 2.0%       (depeg emergency — systemic risk)
      - reserve_coverage_ratio < 100%  (undercollateralized — systemic risk)
      - liquid_reserve_ratio < 60%     (MiCA minimum liquid reserve breach)
      - aml_flag = True                (AML/CFT failure)
      - sanctions_flag = True          (sanctions screening failure)
      - counterparty_credit_default    (counterparty default event)
    """

    def adapt(self, decision: StablecoinDecisionInput) -> StablecoinGovernanceSignals:
        try:
            jurisdiction_factor = JURISDICTION_STRICTNESS.get(decision.jurisdiction, 1.0)
            asset_risk = ASSET_RISK_SCORE.get(decision.reserve_asset, 30.0)
            is_mica_liquid = ASSET_MICA_LIQUID.get(decision.reserve_asset, False)

            # ── HARD BLOCK checks ─────────────────────────────────────────────
            hard_block_reason: str | None = None
            if decision.peg_deviation_pct > PEG_DEVIATION_HARD_BLOCK:
                hard_block_reason = (
                    f"PEG_BREAK_RISK: peg deviation {decision.peg_deviation_pct:.2f}% "
                    f"exceeds 2% systemic risk threshold — depeg emergency protocol"
                )
            elif decision.reserve_coverage_ratio < RESERVE_COVERAGE_HARD_BLOCK:
                hard_block_reason = (
                    f"UNDERCOLLATERALIZED: reserve coverage {decision.reserve_coverage_ratio:.1f}% "
                    f"below 100% — stablecoin under-backed, systemic solvency risk"
                )
            elif decision.liquid_reserve_ratio < MICA_LIQUID_HARD_BLOCK:
                hard_block_reason = (
                    f"MICA_LIQUID_BREACH: liquid reserves {decision.liquid_reserve_ratio:.1f}% "
                    f"below MiCA 60% minimum — EU regulatory hard block"
                )
            elif decision.aml_flag:
                hard_block_reason = "AML_BLOCK: transaction flagged by AML/CFT screening — counterparty identity unresolved"
            elif decision.sanctions_flag:
                hard_block_reason = "SANCTIONS: counterparty or reserve asset flagged by OFAC/EU/UN sanctions screening"
            elif decision.counterparty_credit_default:
                hard_block_reason = "COUNTERPARTY_DEFAULT: custodian or reserve counterparty credit default event detected"

            # ── Signal 1: Reserve Stability Score (probability_score) ─────────
            # Peg health (40%), reserve coverage (35%), liquidity (25%)
            peg_score = max(0.0, 100.0 - decision.peg_deviation_pct * 40.0)  # 2.5% deviation = 0
            coverage_score = min(100.0, max(0.0, (decision.reserve_coverage_ratio - 100.0) * 2.0 + 70.0))
            liquid_score = min(100.0, decision.liquid_reserve_ratio * (100.0 / 80.0))  # 80% = 100pts

            reserve_stability = (
                peg_score * 0.40
                + coverage_score * 0.35
                + liquid_score * 0.25
            )
            probability_score = max(0.0, min(100.0, reserve_stability)) / jurisdiction_factor

            if hard_block_reason:
                probability_score = 0.0

            # ── Signal 2: Collateral Risk Exposure (risk_exposure) ────────────
            # Crypto exposure (35%), concentration (30%), counterparty (20%), duration (15%)
            crypto_risk = decision.crypto_exposure_pct * 0.35
            conc_risk = decision.concentration_risk * 0.30
            cp_risk = decision.counterparty_credit_risk * 0.20
            duration_risk = min(30.0, decision.reserve_duration_days / 365.0 * 30.0) * 0.15

            # Asset inherent risk adds to exposure
            asset_risk_contrib = asset_risk * 0.10

            risk_exposure = max(0.0, min(100.0,
                crypto_risk + conc_risk + cp_risk + duration_risk + asset_risk_contrib
            ))

            # ── Signal 3: Peg Coherence (signal_coherence) ────────────────────
            # On-chain/off-chain alignment (50%), cross-exchange (35%), oracle (15%)
            signal_coherence = max(0.0, min(100.0,
                decision.on_chain_off_chain_alignment * 0.50
                + decision.cross_exchange_consistency * 0.35
                + decision.oracle_confidence * 0.15
            ))

            # Peg deviation dampens coherence
            peg_coherence_penalty = decision.peg_deviation_pct * 15.0
            signal_coherence = max(0.0, signal_coherence - peg_coherence_penalty)

            # ── Signal 4: Reserve Flow Stability (trend_persistence) ───────────
            # Flow stability (40%), TVL trend (35%), redemption pattern (25%)
            trend_persistence = max(0.0, min(100.0,
                decision.reserve_flow_stability * 0.40
                + decision.tvl_trend_7d * 0.35
                + decision.redemption_pattern_stability * 0.25
            ))

            # ── Signal 5: Stress Test Resilience (stress_resilience) ─────────
            # Instant liquidity coverage (40%), emergency buffer (35%), credit facility (25%)
            stress_resilience = max(0.0, min(100.0,
                decision.instant_liquidity_coverage * 0.40
                + decision.emergency_reserve_buffer * 0.35
                + decision.credit_facility_available * 0.25
            ))

            # MiCA liquid asset boosts resilience
            if is_mica_liquid:
                stress_resilience = min(100.0, stress_resilience + 8.0)

            # ── Signal 6: Regulatory Compliance (logic_consistency) ───────────
            # MiCA compliance (40%), AML completeness (35%), audit (25%)
            base_compliance = (
                decision.mica_compliance_score * 0.40
                + decision.aml_screening_completeness * 0.35
                + decision.audit_completeness * 0.25
            )

            # Hard violation flags reduce compliance
            if decision.aml_flag:         base_compliance -= 80.0
            if decision.sanctions_flag:   base_compliance -= 75.0
            if decision.counterparty_credit_default: base_compliance -= 50.0

            logic_consistency = max(0.0, min(100.0, base_compliance)) / jurisdiction_factor

            if hard_block_reason:
                logic_consistency = min(logic_consistency, 5.0)

            # ── Composite recommendation ────────────────────────────────────────
            composite = (
                probability_score
                + (100.0 - risk_exposure)
                + signal_coherence
                + trend_persistence
                + stress_resilience
                + logic_consistency
            ) / 6.0

            if hard_block_reason:
                rec = "HARD_BLOCK"
            elif composite >= 72:
                rec = "RESERVE_ACTION_APPROVED"
            elif composite >= 55:
                rec = "COMPLIANCE_OFFICER_REVIEW"
            else:
                rec = "HIGH_RISK_BLOCK"

            # Transaction risk: amount × crypto exposure × (1 - coverage headroom)
            coverage_headroom = max(0.01, (decision.reserve_coverage_ratio - 100.0) / 100.0)
            transaction_risk = (
                decision.transaction_amount_usd
                * (decision.crypto_exposure_pct / 100.0)
                * (1.0 - min(coverage_headroom, 1.0))
            )

            return StablecoinGovernanceSignals(
                probability_score=round(probability_score, 2),
                risk_exposure=round(risk_exposure, 2),
                signal_coherence=round(signal_coherence, 2),
                trend_persistence=round(trend_persistence, 2),
                stress_resilience=round(stress_resilience, 2),
                logic_consistency=round(logic_consistency, 2),
                peg_deviation_pct=decision.peg_deviation_pct,
                reserve_coverage_ratio=decision.reserve_coverage_ratio,
                liquid_reserve_ratio=decision.liquid_reserve_ratio,
                crypto_exposure_pct=decision.crypto_exposure_pct,
                transaction_risk_usd=round(transaction_risk, 2),
                recommendation=rec,
                hard_block_reason=hard_block_reason,
                jurisdiction_strictness=jurisdiction_factor,
            )

        except Exception as exc:
            logger.error(f"StablecoinSignalAdapter.adapt error: {exc}")
            return StablecoinGovernanceSignals(
                probability_score=50.0, risk_exposure=50.0,
                signal_coherence=50.0, trend_persistence=50.0,
                stress_resilience=50.0, logic_consistency=50.0,
                recommendation="ERROR_FALLBACK",
            )
