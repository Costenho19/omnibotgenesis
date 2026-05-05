"""
OMNIX Energy Governance Signal Adapter
ADR-ENG-001: Energy Governance Vertical (INTERNAL)

Maps energy dispatch / trading decision parameters to OMNIX's 6 normalized
governance signals (0-100). The same 11-checkpoint pipeline that governs
digital asset trading, Islamic credit, insurance, robotics, medical AI,
autonomous agents, and real estate now governs automated energy decisions —
dispatch orders, curtailment instructions, PPA contracts, capacity trades,
carbon credit transactions, and real-time grid balancing actions.

Signal mapping (energy domain):
  probability_score   → Grid Stability Score (LMP forecast confidence, frequency health)
  risk_exposure       → Portfolio Energy Exposure (concentration, capacity margin, counterparty)
  signal_coherence    → Multi-Market Price Alignment (day-ahead vs real-time vs futures)
  trend_persistence   → Demand Trend Persistence (load stability, seasonality alignment)
  stress_resilience   → Grid Resilience Score (reserve margin, renewable buffer, interconnect)
  logic_consistency   → Regulatory & Carbon Compliance (FERC/OFGEM/ACER, carbon caps)

Decision types:
  dispatch_order, curtailment_order, ppa_contract,
  capacity_trade, carbon_credit, balancing_action

Grid regions:
  ERCOT (Texas), PJM (Mid-Atlantic US), UK (National Grid ESO),
  EU_ENTSO_E (European Network), AEMO (Australia), GCC (Gulf Interconnection)

Energy sources:
  Natural_Gas, Wind_Onshore, Wind_Offshore, Solar_Utility,
  Nuclear, Hydro, Battery_Storage, LNG, Coal
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger("OMNIX.Energy.SignalAdapter")

# ── Grid region regulatory strictness ────────────────────────────────────────
REGION_STRICTNESS: dict[str, float] = {
    "ERCOT":      1.02,   # Texas — deregulated, PUCT oversight
    "PJM":        1.08,   # Mid-Atlantic US — FERC regulated, most liquid
    "UK":         1.12,   # Ofgem regulated — strict carbon obligations
    "EU_ENTSO_E": 1.10,   # ACER / national TSOs — EU Green Deal pressure
    "AEMO":       1.06,   # Australian Energy Market Operator
    "GCC":        1.04,   # Gulf interconnection — GCCIA emerging framework
}

# ── Carbon intensity factors (tCO2e per MWh) ─────────────────────────────────
CARBON_INTENSITY: dict[str, float] = {
    "Natural_Gas":    0.370,
    "LNG":            0.430,
    "Coal":           0.820,
    "Nuclear":        0.012,
    "Hydro":          0.024,
    "Wind_Onshore":   0.011,
    "Wind_Offshore":  0.012,
    "Solar_Utility":  0.041,
    "Battery_Storage": 0.050,  # Depends on charging source
}

# ── Price volatility profile by energy source ─────────────────────────────────
SOURCE_VOLATILITY: dict[str, float] = {
    "Natural_Gas":    0.28,
    "LNG":            0.38,
    "Coal":           0.18,
    "Nuclear":        0.06,
    "Hydro":          0.15,
    "Wind_Onshore":   0.32,
    "Wind_Offshore":  0.28,
    "Solar_Utility":  0.30,
    "Battery_Storage": 0.12,
}

# ── Capacity margin thresholds (% reserve) ────────────────────────────────────
CAPACITY_MARGIN_HARD_BLOCK = 5.0    # < 5% → HARD BLOCK (grid collapse risk)
FREQUENCY_DEVIATION_HARD_BLOCK = 0.5  # > ±0.5 Hz → HARD BLOCK (emergency)
CARBON_CAP_BREACH_PENALTY = 35.0    # -35 pts if carbon position over cap

# ── Decision type governance weights ─────────────────────────────────────────
DECISION_TYPE_WEIGHTS: dict[str, dict] = {
    "dispatch_order": {
        "stability_weight": 0.45, "exposure_weight": 0.25,
        "coherence_weight": 0.15, "trend_weight": 0.15,
    },
    "curtailment_order": {
        "stability_weight": 0.50, "exposure_weight": 0.20,
        "coherence_weight": 0.10, "trend_weight": 0.20,
    },
    "ppa_contract": {
        "stability_weight": 0.20, "exposure_weight": 0.30,
        "coherence_weight": 0.25, "trend_weight": 0.25,
    },
    "capacity_trade": {
        "stability_weight": 0.25, "exposure_weight": 0.35,
        "coherence_weight": 0.20, "trend_weight": 0.20,
    },
    "carbon_credit": {
        "stability_weight": 0.15, "exposure_weight": 0.25,
        "coherence_weight": 0.30, "trend_weight": 0.30,
    },
    "balancing_action": {
        "stability_weight": 0.55, "exposure_weight": 0.20,
        "coherence_weight": 0.10, "trend_weight": 0.15,
    },
}


@dataclass
class EnergyDecisionInput:
    """Raw energy governance decision parameters before signal adaptation."""

    decision_type: str          # dispatch_order, curtailment_order, ppa_contract, capacity_trade, carbon_credit, balancing_action
    energy_source: str          # Natural_Gas, Wind_Onshore, Wind_Offshore, Solar_Utility, Nuclear, Hydro, Battery_Storage, LNG, Coal
    grid_region: str            # ERCOT, PJM, UK, EU_ENTSO_E, AEMO, GCC

    # Grid stability signals (0-100 unless noted)
    lmp_forecast_confidence: float      # Locational Marginal Price forecast accuracy (0-100)
    frequency_deviation_hz: float       # Current grid frequency deviation from nominal in Hz (0=perfect)
    grid_congestion_index: float        # Transmission congestion level (0=clear, 100=fully congested)
    capacity_margin_pct: float          # Available reserve capacity % (0=critical, 30+=healthy)

    # Price alignment signals (0-100)
    day_ahead_rt_spread: float          # Day-ahead vs real-time price spread (0=aligned, 100=diverged)
    futures_spot_convergence: float     # Futures converging to spot (100=converging, 0=diverging)
    cross_border_price_alignment: float # Inter-regional price alignment (100=aligned)

    # Demand & load signals (0-100)
    load_forecast_accuracy: float       # Load forecast accuracy over last 48h (0-100)
    demand_growth_stability: float      # Demand growth trend stability (0-100)
    seasonality_alignment: float        # Actual vs seasonal normal load (100=on-model)

    # Resilience signals (0-100)
    renewable_intermittency_buffer: float  # Buffer to absorb renewable variability (0-100)
    interconnect_capacity_utilization: float  # Interconnect usage (0=idle, 100=saturated)
    storage_readiness: float               # Battery/pumped hydro readiness (0-100)

    # Compliance & regulatory flags
    regulatory_violation_flag: bool = False  # FERC/Ofgem/ACER violation → HARD BLOCK
    carbon_position_over_cap: bool = False   # Carbon cap breach → HARD BLOCK
    counterparty_credit_default: bool = False  # Credit default on counterparty → HARD BLOCK
    sanctions_flag: bool = False              # Sanctions screening fail → HARD BLOCK

    # Sizing & contract parameters
    contracted_mw: float = 100.0       # MW contracted in this decision
    contract_term_years: float = 1.0   # Contract duration in years
    settlement_price_mwh: float = 55.0  # Settlement price USD/MWh

    # Carbon parameters
    carbon_intensity_override: float | None = None  # Override default intensity
    carbon_price_usd_tco2: float = 25.0  # Carbon price used in valuation


@dataclass
class EnergyGovernanceSignals:
    """6 normalized OMNIX governance signals for energy domain."""
    probability_score: float    # 0-100: Grid stability / LMP forecast confidence
    risk_exposure: float        # 0-100: Portfolio energy exposure (higher = riskier)
    signal_coherence: float     # 0-100: Multi-market price alignment
    trend_persistence: float    # 0-100: Demand trend persistence & load stability
    stress_resilience: float    # 0-100: Grid resilience (reserve, storage, interconnect)
    logic_consistency: float    # 0-100: Regulatory & carbon compliance

    # Computed metadata
    carbon_avoided_tco2e: float = 0.0      # Estimated CO2 avoided vs coal baseline
    settlement_risk_usd: float = 0.0       # Settlement risk in USD
    capacity_margin_pct: float = 0.0       # Capacity margin at decision time
    frequency_deviation_hz: float = 0.0    # Grid frequency deviation
    recommendation: str = ""
    hard_block_reason: str | None = None
    region_strictness: float = 1.0

    def to_omnix_dict(self) -> dict:
        return {
            "probability_score":  round(self.probability_score, 2),
            "risk_exposure":      round(self.risk_exposure, 2),
            "signal_coherence":   round(self.signal_coherence, 2),
            "trend_persistence":  round(self.trend_persistence, 2),
            "stress_resilience":  round(self.stress_resilience, 2),
            "logic_consistency":  round(self.logic_consistency, 2),
        }


class EnergySignalAdapter:
    """
    Adapts energy governance decision parameters to OMNIX governance signals.
    Domain-agnostic: same 11-checkpoint pipeline, energy vocabulary.

    Hard block conditions (any one triggers immediate BLOCK):
      - frequency_deviation_hz > 0.5 Hz  (grid emergency threshold)
      - capacity_margin_pct < 5.0%       (grid collapse risk)
      - counterparty_credit_default       (financial integrity)
      - carbon_position_over_cap          (regulatory breach)
      - regulatory_violation_flag         (FERC/Ofgem/ACER direct violation)
      - sanctions_flag                    (AML/sanctions screening)
    """

    def adapt(self, decision: EnergyDecisionInput) -> EnergyGovernanceSignals:
        try:
            region_factor = REGION_STRICTNESS.get(decision.grid_region, 1.0)
            source_vol    = SOURCE_VOLATILITY.get(decision.energy_source, 0.25)
            carbon_int    = decision.carbon_intensity_override or CARBON_INTENSITY.get(
                decision.energy_source, 0.5
            )
            coal_intensity = CARBON_INTENSITY["Coal"]

            # ── HARD BLOCK checks ─────────────────────────────────────────────
            hard_block_reason: str | None = None
            if decision.frequency_deviation_hz > FREQUENCY_DEVIATION_HARD_BLOCK:
                hard_block_reason = f"GRID_EMERGENCY: frequency deviation {decision.frequency_deviation_hz:.2f}Hz exceeds ±0.5Hz threshold"
            elif decision.capacity_margin_pct < CAPACITY_MARGIN_HARD_BLOCK:
                hard_block_reason = f"CAPACITY_CRITICAL: reserve margin {decision.capacity_margin_pct:.1f}% below 5% grid-collapse threshold"
            elif decision.counterparty_credit_default:
                hard_block_reason = "COUNTERPARTY_DEFAULT: counterparty credit rating D — settlement risk unacceptable"
            elif decision.carbon_position_over_cap:
                hard_block_reason = "CARBON_CAP_BREACH: carbon position exceeds regulatory allocation cap"
            elif decision.regulatory_violation_flag:
                hard_block_reason = "REGULATORY_VIOLATION: direct breach of FERC/Ofgem/ACER grid code"
            elif decision.sanctions_flag:
                hard_block_reason = "SANCTIONS: counterparty or asset flagged by AML/sanctions screening"

            # ── Signal 1: Grid Stability Score (probability_score) ────────────
            # LMP forecast confidence (40%), frequency health (35%), congestion (25%)
            freq_health = max(0.0, 100.0 - decision.frequency_deviation_hz * 150.0)
            congestion_clear = max(0.0, 100.0 - decision.grid_congestion_index)

            grid_stability = (
                decision.lmp_forecast_confidence * 0.40
                + freq_health * 0.35
                + congestion_clear * 0.25
            )

            # Source volatility dampens probability (high-vol sources = less predictable)
            vol_penalty = source_vol * 20.0
            probability_score = max(0.0, min(100.0,
                grid_stability - vol_penalty
            )) / region_factor

            # Hard block zeroes out probability
            if hard_block_reason:
                probability_score = 0.0

            # ── Signal 2: Portfolio Energy Exposure (risk_exposure) ───────────
            # Capacity concentration (35%), source volatility (30%), counterparty (20%), term (15%)
            mw_concentration = min(100.0, decision.contracted_mw / 10.0)   # 1000 MW = 100%
            vol_risk = source_vol * 100.0 * 0.30
            term_risk = min(20.0, decision.contract_term_years * 1.5)       # Long term = more exposure
            cap_margin_risk = max(0.0, (30.0 - decision.capacity_margin_pct) * 1.5)  # Low reserve = high risk

            raw_exposure = (
                mw_concentration * 0.35
                + vol_risk
                + term_risk * 0.15
                + cap_margin_risk * 0.20
            )
            risk_exposure = max(0.0, min(100.0, raw_exposure))

            # ── Signal 3: Multi-Market Price Alignment (signal_coherence) ─────
            # Day-ahead/RT spread (40%), futures convergence (35%), cross-border (25%)
            rt_alignment = max(0.0, 100.0 - decision.day_ahead_rt_spread)
            coherence_score = (
                rt_alignment * 0.40
                + decision.futures_spot_convergence * 0.35
                + decision.cross_border_price_alignment * 0.25
            )
            signal_coherence = max(0.0, min(100.0, coherence_score))

            # ── Signal 4: Demand Trend Persistence (trend_persistence) ────────
            # Load accuracy (40%), demand stability (35%), seasonality alignment (25%)
            trend_persistence = max(0.0, min(100.0,
                decision.load_forecast_accuracy * 0.40
                + decision.demand_growth_stability * 0.35
                + decision.seasonality_alignment * 0.25
            ))

            # ── Signal 5: Grid Resilience Score (stress_resilience) ───────────
            # Renewable intermittency buffer (35%), interconnect headroom (35%), storage (30%)
            interconnect_headroom = max(0.0, 100.0 - decision.interconnect_capacity_utilization)
            stress_resilience = max(0.0, min(100.0,
                decision.renewable_intermittency_buffer * 0.35
                + interconnect_headroom * 0.35
                + decision.storage_readiness * 0.30
            ))

            # Capacity margin strongly boosts resilience
            cap_bonus = min(15.0, decision.capacity_margin_pct * 0.5)
            stress_resilience = min(100.0, stress_resilience + cap_bonus)

            # ── Signal 6: Regulatory & Carbon Compliance (logic_consistency) ──
            # Base compliance (50%), carbon position (30%), grid code adherence (20%)
            base_compliance = 100.0
            if decision.regulatory_violation_flag: base_compliance -= 80.0
            if decision.sanctions_flag:            base_compliance -= 70.0
            if decision.carbon_position_over_cap:  base_compliance -= CARBON_CAP_BREACH_PENALTY

            # Carbon intensity score: cleaner sources score better
            carbon_compliance = max(0.0, 100.0 - (carbon_int / coal_intensity) * 80.0)
            carbon_compliance = min(100.0, carbon_compliance)

            logic_consistency = max(0.0, min(100.0,
                base_compliance * 0.50
                + carbon_compliance * 0.30
                + (100.0 if not decision.regulatory_violation_flag else 0.0) * 0.20
            )) / region_factor

            if hard_block_reason:
                logic_consistency = min(logic_consistency, 5.0)

            # ── Computed metadata ──────────────────────────────────────────────
            # Carbon avoided vs coal baseline (tCO2e)
            carbon_avoided = max(0.0,
                (coal_intensity - carbon_int) * decision.contracted_mw * max(1.0, decision.contract_term_years * 8760)
            )
            carbon_avoided = min(carbon_avoided, 1_000_000.0)  # Cap display

            # Settlement risk: MW × price × volatility × 0.1 (10% vol scenario)
            settlement_risk = decision.contracted_mw * decision.settlement_price_mwh * source_vol * 0.1

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
                rec = "DISPATCH_APPROVED"
            elif composite >= 55:
                rec = "GRID_OPERATOR_REVIEW"
            else:
                rec = "HIGH_RISK_BLOCK"

            return EnergyGovernanceSignals(
                probability_score=round(probability_score, 2),
                risk_exposure=round(risk_exposure, 2),
                signal_coherence=round(signal_coherence, 2),
                trend_persistence=round(trend_persistence, 2),
                stress_resilience=round(stress_resilience, 2),
                logic_consistency=round(logic_consistency, 2),
                carbon_avoided_tco2e=round(carbon_avoided / 1000.0, 2),  # in tCO2e (k)
                settlement_risk_usd=round(settlement_risk, 2),
                capacity_margin_pct=decision.capacity_margin_pct,
                frequency_deviation_hz=decision.frequency_deviation_hz,
                recommendation=rec,
                hard_block_reason=hard_block_reason,
                region_strictness=region_factor,
            )

        except Exception as exc:
            logger.error(f"EnergySignalAdapter.adapt error: {exc}")
            return EnergyGovernanceSignals(
                probability_score=50.0, risk_exposure=50.0,
                signal_coherence=50.0, trend_persistence=50.0,
                stress_resilience=50.0, logic_consistency=50.0,
                recommendation="ERROR_FALLBACK",
            )
