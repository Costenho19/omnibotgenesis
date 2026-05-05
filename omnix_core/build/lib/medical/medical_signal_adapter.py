"""
OMNIX Medical AI Governance Signal Adapter
ADR-MED-001: Medical AI Governance Vertical

Maps clinical AI decision parameters to OMNIX's 6 normalized governance signals (0-100).
This adapter makes the governance pipeline domain-agnostic — the same 11-checkpoint
engine that governs trading decisions now governs clinical AI decisions.

Signal mapping:
  probability_score   → Diagnostic / clinical confidence (model certainty, evidence strength)
  risk_exposure       → Patient risk index (contraindications, severity, comorbidities)
  signal_coherence    → Multi-signal clinical alignment (symptom-decision consistency)
  trend_persistence   → Patient trajectory stability (recovery trend, baseline drift)
  stress_resilience   → Clinical edge-case resilience (comorbidity amplification, device failure)
  logic_consistency   → Care plan alignment and ethics compliance (consent, protocol match)

Supported decision types:
  rehabilitation_guidance, diagnostic_alert, therapeutic_recommendation,
  monitoring_alert, surgical_clearance
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("OMNIX.Medical.SignalAdapter")

# Diagnostic confidence thresholds by decision type
CONFIDENCE_THRESHOLDS: dict[str, float] = {
    "rehabilitation_guidance": 0.72,
    "diagnostic_alert": 0.80,
    "therapeutic_recommendation": 0.85,
    "monitoring_alert": 0.70,
    "surgical_clearance": 0.90,
}

# Risk amplifiers by patient profile
RISK_AMPLIFIERS: dict[str, float] = {
    "post_surgery": 1.40,
    "chronic_condition": 1.25,
    "acute_care": 1.35,
    "rehabilitation": 1.15,
    "preventive": 0.85,
    "pediatric": 1.30,
    "geriatric": 1.20,
}

# Regulatory jurisdiction thresholds
JURISDICTION_STRICTNESS: dict[str, float] = {
    "USA": 1.10,    # FDA SaMD — strictest
    "EU": 1.05,     # EU MDR / AI Act High Risk
    "UAE": 1.00,    # DOH AI Framework
    "UK": 1.08,     # MHRA guidance
    "GLOBAL": 1.00,
}


@dataclass
class MedicalDecisionInput:
    """Raw clinical AI decision parameters before signal adaptation."""
    device_type: str                    # Wearable, Clinical_AI, Monitoring_System, Surgical_Robot
    decision_type: str                  # rehabilitation_guidance, diagnostic_alert, etc.
    patient_profile: str                # post_surgery, chronic_condition, acute_care, etc.
    jurisdiction: str                   # USA, EU, UAE, UK

    # Clinical signals (0-100 unless noted)
    sensor_confidence: float            # Device sensor data quality and calibration (0-100)
    diagnostic_confidence: float        # AI model confidence in its output (0-100)
    patient_risk_score: float           # Patient risk stratification index (0-100, higher=riskier)
    contraindication_score: float       # Contraindication severity (0-100, higher=more contraindicated)
    evidence_completeness: float        # Clinical data completeness (0-100)
    care_plan_alignment: float          # Alignment with established care plan (0-100)
    recovery_trend: float               # Patient trajectory (0-100, higher=improving)
    comorbidity_index: float            # Comorbidity burden (0-100, higher=more comorbidities)

    # Ethics & compliance flags
    ethics_flag: bool = False           # Ethics review triggered
    consent_verified: bool = True       # Informed consent status
    off_label_use: bool = False         # Off-label device/AI use

    # Metadata
    days_since_calibration: int = 1    # Device calibration recency
    prior_adverse_events: int = 0      # Prior adverse events for this patient


@dataclass
class MedicalGovernanceSignals:
    """6 normalized OMNIX governance signals for medical AI domain."""
    probability_score: float    # 0-100: clinical confidence probability
    risk_exposure: float        # 0-100: patient risk index (lower = safer)
    signal_coherence: float     # 0-100: multi-signal clinical consistency
    trend_persistence: float    # 0-100: patient trajectory stability
    stress_resilience: float    # 0-100: edge-case resilience
    logic_consistency: float    # 0-100: care plan and ethics alignment

    # Metadata for dashboard display
    confidence_threshold: float = 0.0
    adjusted_risk: float = 0.0
    recommendation: str = ""
    jurisdiction_strictness: float = 1.0

    def to_omnix_dict(self) -> dict:
        return {
            "probability_score": round(self.probability_score, 2),
            "risk_exposure": round(self.risk_exposure, 2),
            "signal_coherence": round(self.signal_coherence, 2),
            "trend_persistence": round(self.trend_persistence, 2),
            "stress_resilience": round(self.stress_resilience, 2),
            "logic_consistency": round(self.logic_consistency, 2),
        }


class MedicalSignalAdapter:
    """
    Adapts clinical AI decision parameters to OMNIX governance signals.
    Domain-agnostic: same 11-checkpoint pipeline, medical vocabulary.
    """

    def adapt(self, decision: MedicalDecisionInput) -> MedicalGovernanceSignals:
        try:
            jx_factor = JURISDICTION_STRICTNESS.get(decision.jurisdiction, 1.0)
            risk_amp = RISK_AMPLIFIERS.get(decision.patient_profile, 1.0)
            conf_threshold = CONFIDENCE_THRESHOLDS.get(decision.decision_type, 0.75)

            # ── Signal 1: Probability Score (Clinical Confidence) ──────────────
            # Combines sensor quality, diagnostic model confidence, evidence completeness
            sensor_factor = decision.sensor_confidence * 0.30
            diag_factor = decision.diagnostic_confidence * 0.50
            evidence_factor = decision.evidence_completeness * 0.20

            # Penalize for stale calibration (>24h = penalty starts)
            calibration_penalty = min(20.0, max(0.0, (decision.days_since_calibration - 1) * 2.0))

            # Jurisdiction makes threshold stricter
            base_prob = sensor_factor + diag_factor + evidence_factor - calibration_penalty
            probability_score = max(0.0, min(100.0, base_prob / jx_factor))

            # ── Signal 2: Risk Exposure (Patient Risk Index) ───────────────────
            # Higher = more risky. Inverted from other signals for display.
            base_risk = decision.patient_risk_score * 0.40
            contra_risk = decision.contraindication_score * 0.35
            comorbidity_risk = decision.comorbidity_index * 0.25
            adverse_penalty = min(15.0, decision.prior_adverse_events * 5.0)

            raw_risk = (base_risk + contra_risk + comorbidity_risk + adverse_penalty) * risk_amp
            risk_exposure = max(0.0, min(100.0, raw_risk))

            # ── Signal 3: Signal Coherence (Clinical Consistency) ─────────────
            # Multi-signal alignment: do sensors, diagnostics, and care plan agree?
            diag_coherence = decision.diagnostic_confidence * 0.35
            sensor_coherence = decision.sensor_confidence * 0.30
            evidence_coherence = decision.evidence_completeness * 0.25

            # Contraindication creates incoherence
            contra_penalty = decision.contraindication_score * 0.10
            signal_coherence = max(0.0, min(100.0,
                diag_coherence + sensor_coherence + evidence_coherence - contra_penalty
            ))

            # ── Signal 4: Trend Persistence (Patient Trajectory) ──────────────
            # Is the patient improving? Is the trajectory stable?
            recovery_base = decision.recovery_trend * 0.60
            risk_drag = (100.0 - decision.patient_risk_score) * 0.25
            comorbidity_drag = (100.0 - decision.comorbidity_index) * 0.15

            trend_persistence = max(0.0, min(100.0,
                recovery_base + risk_drag + comorbidity_drag
            ))

            # ── Signal 5: Stress Resilience (Edge-Case Robustness) ────────────
            # Can this decision handle comorbidities, device failure modes, edge cases?
            base_resilience = (100.0 - decision.comorbidity_index) * 0.50
            recovery_resilience = decision.recovery_trend * 0.30
            sensor_resilience = decision.sensor_confidence * 0.20

            # Calibration staleness reduces resilience
            resilience_penalty = calibration_penalty * 0.5
            stress_resilience = max(0.0, min(100.0,
                base_resilience + recovery_resilience + sensor_resilience - resilience_penalty
            ))

            # ── Signal 6: Logic Consistency (Ethics & Care Plan) ──────────────
            # Does the decision align with care plan, ethics, consent?
            care_base = decision.care_plan_alignment * 0.55
            evidence_logic = decision.evidence_completeness * 0.20

            # Ethics and consent penalties
            ethics_penalty = 30.0 if decision.ethics_flag else 0.0
            consent_penalty = 40.0 if not decision.consent_verified else 0.0
            off_label_penalty = 15.0 if decision.off_label_use else 0.0

            logic_consistency = max(0.0, min(100.0,
                care_base + evidence_logic
                - ethics_penalty - consent_penalty - off_label_penalty
            ))

            # Recommendation
            composite = (
                probability_score
                + (100.0 - risk_exposure)
                + signal_coherence
                + trend_persistence
                + stress_resilience
                + logic_consistency
            ) / 6.0

            if composite >= 72:
                rec = "LIKELY_APPROVE"
            elif composite >= 50:
                rec = "CLINICAL_REVIEW"
            else:
                rec = "HIGH_RISK"

            return MedicalGovernanceSignals(
                probability_score=probability_score,
                risk_exposure=risk_exposure,
                signal_coherence=signal_coherence,
                trend_persistence=trend_persistence,
                stress_resilience=stress_resilience,
                logic_consistency=logic_consistency,
                confidence_threshold=conf_threshold * 100.0,
                adjusted_risk=min(risk_exposure * risk_amp, 100.0),
                recommendation=rec,
                jurisdiction_strictness=jx_factor,
            )

        except Exception as e:
            logger.error(f"MedicalSignalAdapter.adapt error: {e}")
            return MedicalGovernanceSignals(
                probability_score=50.0,
                risk_exposure=50.0,
                signal_coherence=50.0,
                trend_persistence=50.0,
                stress_resilience=50.0,
                logic_consistency=50.0,
                recommendation="ERROR_FALLBACK",
            )
