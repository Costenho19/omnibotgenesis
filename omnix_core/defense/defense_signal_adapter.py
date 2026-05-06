"""
OMNIX Autonomous Defense Governance Signal Adapter
ADR-DEF-001: Autonomous Defense Governance Vertical

Maps autonomous defense decision inputs → OMNIX normalized 6-signal governance dict.
Same pipeline that governs trading, credit, insurance, robotics, medical AI,
autonomous agents, energy, real estate, and stablecoin reserve — now applied to
autonomous weapons systems, drone authorization, ROE compliance, and AI targeting.

Signal mapping (defense domain):
  probability_score   → Mission Success Probability (target confidence + ROE + legal)
  risk_exposure       → Engagement Risk Score (collateral damage + cyber + geofence breach)
  signal_coherence    → Sensor Fusion Agreement (multi-sensor target ID + comms + environment)
  trend_persistence   → Operational Stability (ROE validity + mission necessity sustained)
  stress_resilience   → Adversarial Resilience (cyber hardening + comms + platform health)
  logic_consistency   → Internal signal divergence (cross-checkpoint agreement)

Decision types:
  mission_authorization, target_validation, rules_of_engagement_check,
  autonomous_action_approval, escalation_review

Platform types:
  Autonomous_UAS, Ground_Robot_UGV, Maritime_USV,
  Directed_Energy_System, ISR_Surveillance, Counter_UAS

Operational theaters:
  Contested_Airspace, Urban_COIN, Maritime_Patrol,
  Border_Security, Critical_Infrastructure, Cyber_Physical
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("OMNIX.Defense.SignalAdapter")

THEATER_STRICTNESS: dict[str, float] = {
    "Contested_Airspace":     1.18,
    "Urban_COIN":             1.22,
    "Maritime_Patrol":        1.10,
    "Border_Security":        1.08,
    "Critical_Infrastructure": 1.15,
    "Cyber_Physical":         1.12,
}

PLATFORM_RISK_FACTOR: dict[str, float] = {
    "Autonomous_UAS":         1.15,
    "Ground_Robot_UGV":       1.10,
    "Maritime_USV":           1.08,
    "Directed_Energy_System": 1.20,
    "ISR_Surveillance":       1.00,
    "Counter_UAS":            1.12,
}


def _clamp(val: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, val))


@dataclass
class DefenseDecisionInput:
    decision_type: str
    platform_type: str
    operational_theater: str

    target_confidence: float          # 0-100  — sensor fusion target identification confidence
    target_discrimination: float      # 0-100  — combatant vs civilian positive discrimination
    collateral_damage_estimate: float # 0-100  — inverse (100 = zero collateral risk)
    roe_compliance_score: float       # 0-100  — rules of engagement compliance
    comms_integrity: float            # 0-100  — secure command link integrity
    cyber_vulnerability_score: float  # 0-100  — inverse (100 = fully cyber-hardened)
    mission_necessity_score: float    # 0-100  — IHL military necessity & proportionality
    human_oversight_available: float  # 0-100  — human-in-the-loop availability
    legal_authorization_score: float  # 0-100  — command authority + IHL compliance
    environmental_conditions: float   # 0-100  — operational environment clarity / visibility
    platform_readiness: float         # 0-100  — autonomous platform health & reliability
    geofence_compliance: float        # 0-100  — geographic boundary & exclusion zone compliance
    iff_confidence: float             # 0-100  — IFF (Identify Friend or Foe) confidence

    civilian_proximity_flag: bool = False
    roe_violation_flag: bool = False
    cyber_intrusion_flag: bool = False
    friendly_fire_risk_flag: bool = False
    chain_of_command_break: bool = False
    legal_prohibition_flag: bool = False

    engagement_range_km: float = 0.0
    mission_duration_hrs: float = 0.0

    @property
    def hard_block_reason(self) -> Optional[str]:
        if self.civilian_proximity_flag:
            return "HARD_BLOCK: Civilian proximity confirmed — engagement suspended per IHL Article 51(4)"
        if self.roe_violation_flag:
            return "HARD_BLOCK: Rules of Engagement violation — autonomous lethal action prohibited"
        if self.cyber_intrusion_flag:
            return "HARD_BLOCK: Active cyber intrusion on command link — authentication failure, control suspended"
        if self.friendly_fire_risk_flag:
            return "HARD_BLOCK: Friendly fire identification failure — IFF mismatch detected, engagement halted"
        if self.chain_of_command_break:
            return "HARD_BLOCK: Command authority chain broken — escalation to human commander required"
        if self.legal_prohibition_flag:
            return "HARD_BLOCK: Legal prohibition triggered — action not authorized under applicable law or treaty"
        return None


@dataclass
class DefenseSignals:
    probability_score: float
    risk_exposure: float
    signal_coherence: float
    trend_persistence: float
    stress_resilience: float
    logic_consistency: float
    hard_block_reason: Optional[str]
    target_confidence: float
    collateral_damage_estimate: float
    roe_compliance_score: float
    comms_integrity: float
    legal_authorization_score: float
    iff_confidence: float
    human_oversight_available: float
    engagement_risk_index: float

    def to_omnix_dict(self) -> dict:
        return {
            "probability_score":  self.probability_score,
            "risk_exposure":      self.risk_exposure,
            "signal_coherence":   self.signal_coherence,
            "trend_persistence":  self.trend_persistence,
            "stress_resilience":  self.stress_resilience,
            "logic_consistency":  self.logic_consistency,
        }


class DefenseSignalAdapter:
    """Adapts DefenseDecisionInput → normalized OMNIX 6-signal governance dict."""

    def adapt(self, inp: DefenseDecisionInput) -> DefenseSignals:
        strictness = THEATER_STRICTNESS.get(inp.operational_theater, 1.10)
        plat_risk  = PLATFORM_RISK_FACTOR.get(inp.platform_type, 1.10)

        probability_score = _clamp(
            (
                inp.target_confidence       * 0.25
                + inp.target_discrimination * 0.20
                + inp.mission_necessity_score * 0.20
                + inp.roe_compliance_score  * 0.20
                + inp.legal_authorization_score * 0.15
            ) / strictness
        )

        base_risk = (
            (100 - inp.collateral_damage_estimate) * 0.30
            + (100 - inp.cyber_vulnerability_score) * 0.25
            + (100 - inp.geofence_compliance)       * 0.20
            + (100 - inp.comms_integrity)            * 0.15
            + (100 - inp.human_oversight_available)  * 0.10
        )
        risk_exposure = _clamp(base_risk * plat_risk * 0.01 * 100)

        signal_coherence = _clamp(
            inp.target_confidence       * 0.30
            + inp.iff_confidence        * 0.25
            + inp.environmental_conditions * 0.25
            + inp.comms_integrity       * 0.20
        )

        trend_persistence = _clamp(
            inp.roe_compliance_score      * 0.35
            + inp.mission_necessity_score * 0.35
            + inp.legal_authorization_score * 0.30
        )

        stress_resilience = _clamp(
            inp.cyber_vulnerability_score * 0.30
            + inp.comms_integrity         * 0.25
            + inp.platform_readiness      * 0.25
            + inp.geofence_compliance     * 0.20
        )

        signals = [probability_score, 100.0 - risk_exposure,
                   signal_coherence, trend_persistence, stress_resilience]
        avg = sum(signals) / len(signals)
        variance = sum((s - avg) ** 2 for s in signals) / len(signals)
        divergence = variance ** 0.5
        logic_consistency = _clamp(100.0 - divergence * 1.8)

        engagement_risk_index = round(
            (100 - inp.collateral_damage_estimate) * 0.40
            + (100 - inp.target_discrimination) * 0.30
            + (100 - inp.roe_compliance_score) * 0.30,
            2,
        )

        return DefenseSignals(
            probability_score=round(probability_score, 2),
            risk_exposure=round(risk_exposure, 2),
            signal_coherence=round(signal_coherence, 2),
            trend_persistence=round(trend_persistence, 2),
            stress_resilience=round(stress_resilience, 2),
            logic_consistency=round(logic_consistency, 2),
            hard_block_reason=inp.hard_block_reason,
            target_confidence=inp.target_confidence,
            collateral_damage_estimate=inp.collateral_damage_estimate,
            roe_compliance_score=inp.roe_compliance_score,
            comms_integrity=inp.comms_integrity,
            legal_authorization_score=inp.legal_authorization_score,
            iff_confidence=inp.iff_confidence,
            human_oversight_available=inp.human_oversight_available,
            engagement_risk_index=engagement_risk_index,
        )
