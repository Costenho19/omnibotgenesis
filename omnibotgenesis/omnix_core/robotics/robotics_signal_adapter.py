"""
OMNIX Robotics Governance Signal Adapter
ADR-055: Robotics & Autonomous Systems Governance Vertical

Maps robotic action parameters to OMNIX's 6 normalized governance signals (0-100).
The same 11-checkpoint pipeline that governs trading and insurance decisions now
governs autonomous robot action execution — pre-execution, not post-event.

Signal mapping:
  probability_score   → Action success probability (sensor confidence + model certainty)
  risk_exposure       → Collision / damage risk index (proximity, load, speed)
  signal_coherence    → Sensor fusion agreement (LiDAR + camera + IMU consistency)
  trend_persistence   → Environmental stability (consistent conditions over time)
  stress_resilience   → Mechanical margin (motor temps, battery level, stress limits)
  logic_consistency   → Mission logic consistency (action fits mission parameters)

Supported robot types:
  Industrial_Arm, AMR (Autonomous Mobile Robot), Cobot, Drone, AGV, Humanoid

Supported industries:
  Automotive, Electronics, Pharma, Food, Logistics, Construction, Healthcare, Defense
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("OMNIX.Robotics.SignalAdapter")

# Safety criticality by industry (higher = stricter governance)
INDUSTRY_CRITICALITY: dict[str, float] = {
    "Healthcare": 95.0,
    "Defense": 90.0,
    "Pharma": 88.0,
    "Food": 75.0,
    "Automotive": 72.0,
    "Electronics": 65.0,
    "Construction": 70.0,
    "Logistics": 60.0,
}

# Risk multipliers by action type
ACTION_RISK_MULTIPLIER: dict[str, float] = {
    "welding": 1.8,
    "assembly_critical": 1.6,
    "navigation_crowded": 1.5,
    "pick_and_place_fragile": 1.4,
    "inspection": 1.0,
    "navigation_clear": 0.8,
    "pick_and_place_standard": 1.1,
    "quality_check": 0.9,
    "packaging": 1.0,
    "charging": 0.7,
}

# Thermal thresholds (°C)
MOTOR_TEMP_WARNING = 75.0
MOTOR_TEMP_CRITICAL = 90.0

# Battery thresholds (%)
BATTERY_WARNING = 20.0
BATTERY_CRITICAL = 10.0


@dataclass
class RobotActionInput:
    """Raw robotic action parameters before signal adaptation."""
    robot_id: str               # Unique robot identifier
    robot_type: str             # Industrial_Arm, AMR, Cobot, Drone, AGV, Humanoid
    industry: str               # Automotive, Electronics, Pharma, etc.
    action_type: str            # pick_and_place, navigation, welding, etc.
    environment: str            # structured, semi_structured, unstructured, outdoor

    # Sensor data
    sensor_confidence: float    # 0-100: sensor readings reliability
    lidar_agreement: float      # 0-100: LiDAR point cloud consistency
    camera_confidence: float    # 0-100: computer vision certainty
    imu_stability: float        # 0-100: inertial measurement stability

    # Physical parameters
    proximity_cm: float         # Distance to nearest obstacle (cm)
    payload_kg: float           # Current payload weight
    max_payload_kg: float       # Robot's rated maximum payload
    speed_ms: float             # Current speed (m/s)
    max_speed_ms: float         # Robot's rated maximum speed

    # System health
    battery_pct: float          # Battery level (%)
    motor_temp_c: float         # Primary motor temperature (°C)
    joint_stress_pct: float     # Joint stress as % of rated capacity

    # Mission context
    mission_logic_score: float  # 0-100: action aligns with mission plan
    environmental_stability: float  # 0-100: conditions stable over time window
    historical_success_rate: float  # 0-100: this robot's success rate for this action


@dataclass
class RoboticsGovernanceSignals:
    """6 normalized OMNIX governance signals for robotics domain."""
    probability_score: float    # 0-100: action success probability
    risk_exposure: float        # 0-100: collision/damage risk (lower = safer)
    signal_coherence: float     # 0-100: sensor fusion agreement
    trend_persistence: float    # 0-100: environmental stability
    stress_resilience: float    # 0-100: mechanical margin
    logic_consistency: float    # 0-100: mission logic alignment

    # Metadata for dashboard display
    sensor_fusion_score: float = 0.0
    safety_margin_pct: float = 0.0
    criticality_level: str = ""

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


class RoboticsSignalAdapter:
    """
    Translates robotic action telemetry into OMNIX governance signals.
    Pre-execution governance: every robot action is evaluated before execution.
    A BLOCK decision prevents the action from being attempted.
    """

    def adapt(self, action: RobotActionInput) -> RoboticsGovernanceSignals:
        """Convert raw robot telemetry to 6 OMNIX governance signals."""
        try:
            industry_criticality = INDUSTRY_CRITICALITY.get(action.industry, 70.0)
            action_risk_mult = ACTION_RISK_MULTIPLIER.get(action.action_type, 1.0)
            payload_ratio = min(action.payload_kg / max(action.max_payload_kg, 0.1), 1.0)
            speed_ratio = min(action.speed_ms / max(action.max_speed_ms, 0.1), 1.0)

            # ── Signal 1: Probability Score (Action Success) ──
            sensor_base = action.sensor_confidence * 0.35
            history_base = action.historical_success_rate * 0.30
            mission_base = action.mission_logic_score * 0.20
            # Environmental uncertainty penalty
            env_penalty = max(0.0, (100 - action.environmental_stability) * 0.15)
            # Overload penalty
            overload_penalty = max(0.0, (payload_ratio - 0.8) * 40.0) if payload_ratio > 0.8 else 0.0
            probability_score = max(0.0, min(100.0,
                sensor_base + history_base + mission_base - env_penalty - overload_penalty
            ))

            # ── Signal 2: Risk Exposure (Collision/Damage Risk) ──
            # Proximity risk (exponential as robot gets closer to obstacles)
            if action.proximity_cm < 10:
                proximity_risk = 80.0
            elif action.proximity_cm < 30:
                proximity_risk = 50.0
            elif action.proximity_cm < 100:
                proximity_risk = 25.0
            else:
                proximity_risk = max(0.0, 100 - action.proximity_cm * 0.1)

            speed_risk = speed_ratio * 30.0
            payload_risk = payload_ratio * 20.0
            base_risk = (proximity_risk + speed_risk + payload_risk) / 3.0
            # Apply action and industry risk multipliers
            risk_exposure = max(0.0, min(100.0, base_risk * action_risk_mult * (industry_criticality / 70.0)))

            # ── Signal 3: Signal Coherence (Sensor Fusion Agreement) ──
            lidar_cam_agreement = 100.0 - abs(action.lidar_agreement - action.camera_confidence)
            imu_factor = action.imu_stability * 0.30
            sensor_avg = (action.lidar_agreement + action.camera_confidence) / 2.0
            coherence_base = sensor_avg * 0.50
            signal_coherence = max(0.0, min(100.0,
                coherence_base + imu_factor + lidar_cam_agreement * 0.20
            ))
            sensor_fusion_score = (action.lidar_agreement + action.camera_confidence + action.imu_stability) / 3.0

            # ── Signal 4: Trend Persistence (Environmental Stability) ──
            stability_base = action.environmental_stability * 0.70
            # Structured environments are more predictable
            env_bonus = {"structured": 20.0, "semi_structured": 10.0,
                         "unstructured": 0.0, "outdoor": -5.0}.get(action.environment, 5.0)
            trend_persistence = max(0.0, min(100.0, stability_base + env_bonus))

            # ── Signal 5: Stress Resilience (Mechanical Margin) ──
            # Battery health
            if action.battery_pct <= BATTERY_CRITICAL:
                battery_score = 5.0
            elif action.battery_pct <= BATTERY_WARNING:
                battery_score = 30.0
            else:
                battery_score = min(100.0, action.battery_pct)

            # Thermal health
            if action.motor_temp_c >= MOTOR_TEMP_CRITICAL:
                thermal_score = 5.0
            elif action.motor_temp_c >= MOTOR_TEMP_WARNING:
                thermal_score = 40.0
            else:
                thermal_score = max(0.0, 100.0 - (action.motor_temp_c / MOTOR_TEMP_WARNING) * 50.0)

            # Joint stress
            joint_score = max(0.0, 100.0 - action.joint_stress_pct)

            stress_resilience = (battery_score * 0.35 + thermal_score * 0.35 + joint_score * 0.30)
            safety_margin_pct = max(0.0, min(100.0, stress_resilience))

            # ── Signal 6: Logic Consistency (Mission Alignment) ──
            logic_base = action.mission_logic_score * 0.65
            # Sensor confidence contributes to logic (can't plan if sensors fail)
            sensor_logic = action.sensor_confidence * 0.25
            # Speed/payload contradictions reduce logic score
            overspec_penalty = max(0.0, (speed_ratio + payload_ratio - 1.2) * 20.0)
            logic_consistency = max(0.0, min(100.0, logic_base + sensor_logic - overspec_penalty))

            # Criticality level for UI
            composite = (probability_score + (100 - risk_exposure) + signal_coherence
                         + trend_persistence + stress_resilience + logic_consistency) / 6.0
            if composite >= 75:
                criticality = "LOW"
            elif composite >= 55:
                criticality = "MEDIUM"
            elif composite >= 35:
                criticality = "HIGH"
            else:
                criticality = "CRITICAL"

            return RoboticsGovernanceSignals(
                probability_score=probability_score,
                risk_exposure=risk_exposure,
                signal_coherence=signal_coherence,
                trend_persistence=trend_persistence,
                stress_resilience=stress_resilience,
                logic_consistency=logic_consistency,
                sensor_fusion_score=sensor_fusion_score,
                safety_margin_pct=safety_margin_pct,
                criticality_level=criticality,
            )

        except Exception as e:
            logger.error(f"RoboticsSignalAdapter.adapt error: {e}")
            return RoboticsGovernanceSignals(
                probability_score=50.0,
                risk_exposure=50.0,
                signal_coherence=50.0,
                trend_persistence=50.0,
                stress_resilience=50.0,
                logic_consistency=50.0,
                criticality_level="ERROR_FALLBACK",
            )
