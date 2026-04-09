"""
OMNIX Credit Signal Adapter
ADR-052: Islamic Credit Governance Vertical

Maps Islamic finance credit parameters to OMNIX's 6 normalized governance signals (0-100).
This is the domain adapter that makes the governance pipeline domain-agnostic.

Signal mapping:
  probability_score   → Creditworthiness probability (credit score, DSR, collateral)
  risk_exposure       → Default risk index (PD × LGD proxy, lower = safer)
  signal_coherence    → Indicator agreement (all signals pointing same direction)
  trend_persistence   → Credit conditions stability (macro persistence)
  stress_resilience   → Income shock resilience (can borrower survive -20% income?)
  logic_consistency   → Application internal consistency (no contradictions)

Optional:
  signal_integrity    → Data completeness and quality
  temporal_coherence  → Macro conditions stability over time

Islamic Finance Constraints (additional layer beyond standard credit):
  - No Riba (interest): financing must be asset-backed (Murabaha/Ijara/Musharaka)
  - Halal sectors only
  - Gharar limit: uncertainty must be bounded
  - Debt ratio ≤ 33% of total assets (Islamic standard)
  - DSR ≤ 40% of monthly income
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Optional

from omnix_core.credit.credit_macro_data import MacroSnapshot

logger = logging.getLogger("OMNIX.Credit.SignalAdapter")

# Halal sectors for UAE Islamic finance
HALAL_SECTORS = {
    "technology", "healthcare", "education", "real_estate",
    "logistics", "agriculture", "manufacturing", "renewable_energy",
    "food_beverage", "retail", "hospitality", "construction",
    "transportation", "telecommunications", "professional_services",
    "media_entertainment",  # halal content only
}

HARAM_SECTORS = {
    "alcohol", "tobacco", "gambling", "weapons",
    "pork_products", "adult_entertainment",
    "conventional_banking",  # interest-based
    "derivatives_speculation",  # pure gharar
}

# UAE Central Bank DSR limits (Islamic finance standard)
ISLAMIC_DSR_MAX = 0.40           # 40% of monthly income
ISLAMIC_DEBT_RATIO_MAX = 0.33    # 33% of total assets
GHARAR_MAX = 65.0                # Maximum uncertainty score (0-100)


@dataclass
class CreditApplication:
    """
    Represents a credit/financing application in the Islamic finance context.
    All amounts in AED (UAE Dirham) by default.
    """
    application_id: str

    # Applicant
    applicant_type: str = "SME"           # SME | Individual | Corporate
    sector: str = "technology"

    # Financing
    requested_amount: float = 500_000.0  # AED
    tenor_months: int = 36
    financing_type: str = "Murabaha"     # Murabaha | Ijara | Musharaka | Diminishing_Musharaka
    purpose: str = "Working capital"
    currency: str = "AED"

    # Credit metrics
    credit_score: float = 650.0          # 300-850 scale
    debt_service_ratio: float = 0.35     # Current DSR (0-1)
    asset_backing_ratio: float = 1.20    # Collateral / Loan (> 1 = over-collateralized)
    annual_revenue: float = 2_000_000.0  # AED
    existing_obligations: float = 0.0   # Monthly debt obligations (AED)
    collateral_type: str = "property"   # property | equipment | inventory | guarantee

    # Islamic finance specific
    is_halal_sector: bool = True
    riba_free: bool = True               # Asset-backed, no interest
    gharar_score: float = 25.0           # Uncertainty score 0-100 (lower = better)


@dataclass
class CreditSignals:
    """OMNIX normalized signals derived from credit application + macro conditions."""
    # Core 6 required signals
    probability_score: float = 0.0
    risk_exposure: float = 0.0
    signal_coherence: float = 0.0
    trend_persistence: float = 0.0
    stress_resilience: float = 0.0
    logic_consistency: float = 0.0

    # Optional signals
    signal_integrity: float = 75.0
    temporal_coherence: float = 65.0

    # Metadata for transparency
    sharia_compliant: bool = True
    sharia_violation: str = ""
    pd_estimate: float = 0.0            # Probability of Default (0-1)
    lgd_estimate: float = 0.0          # Loss Given Default (0-1)
    adapter_notes: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "probability_score": round(self.probability_score, 2),
            "risk_exposure": round(self.risk_exposure, 2),
            "signal_coherence": round(self.signal_coherence, 2),
            "trend_persistence": round(self.trend_persistence, 2),
            "stress_resilience": round(self.stress_resilience, 2),
            "logic_consistency": round(self.logic_consistency, 2),
            "signal_integrity": round(self.signal_integrity, 2),
            "temporal_coherence": round(self.temporal_coherence, 2),
        }


class CreditSignalAdapter:
    """
    Translates Islamic finance credit parameters → OMNIX governance signals.

    This is the domain adapter layer. It takes a CreditApplication + MacroSnapshot
    and produces the 8 normalized signals that feed into the governance pipeline.

    The pipeline itself is completely unchanged — only the signal source differs
    from the trading vertical.
    """

    def adapt(
        self,
        app: CreditApplication,
        macro: MacroSnapshot,
    ) -> CreditSignals:
        """
        Main adaptation method. Converts credit parameters to OMNIX signals.
        """
        signals = CreditSignals()

        # 1. PROBABILITY SCORE — Creditworthiness probability
        signals.probability_score = self._compute_probability_score(app, macro)

        # 2. RISK EXPOSURE — Default risk (higher = more dangerous)
        signals.risk_exposure, signals.pd_estimate, signals.lgd_estimate = (
            self._compute_risk_exposure(app, macro)
        )

        # 3. SIGNAL COHERENCE — Are all credit indicators aligned?
        signals.signal_coherence = self._compute_signal_coherence(app, macro)

        # 4. TREND PERSISTENCE — Macro credit conditions stability
        signals.trend_persistence = self._compute_trend_persistence(macro)

        # 5. STRESS RESILIENCE — Can borrower survive income shock?
        signals.stress_resilience = self._compute_stress_resilience(app, macro)

        # 6. LOGIC CONSISTENCY — Internal application consistency
        signals.logic_consistency, notes = self._compute_logic_consistency(app)
        signals.adapter_notes = notes

        # 7. SIGNAL INTEGRITY — Data quality and completeness
        signals.signal_integrity = self._compute_signal_integrity(app)

        # 8. TEMPORAL COHERENCE — Macro stability over time
        signals.temporal_coherence = self._compute_temporal_coherence(macro)

        # Islamic compliance check (overlay, not a signal — goes to CP-6 equivalent)
        signals.sharia_compliant, signals.sharia_violation = (
            self._check_sharia_compliance(app)
        )

        logger.debug(
            f"[CreditAdapter] {app.application_id} | "
            f"P={signals.probability_score:.1f} R={signals.risk_exposure:.1f} "
            f"C={signals.signal_coherence:.1f} Sharia={'✅' if signals.sharia_compliant else '❌'}"
        )

        return signals

    # ──────────────────────────────────────────────────────────────────────────
    # Signal computation methods
    # ──────────────────────────────────────────────────────────────────────────

    def _compute_probability_score(self, app: CreditApplication, macro: MacroSnapshot) -> float:
        """
        Creditworthiness probability (0-100, higher = better borrower).

        Components:
          - Credit score normalized (40% weight)
          - DSR compliance (25% weight): DSR ≤ 40% Islamic standard
          - Collateral coverage (20% weight): asset_backing_ratio
          - Macro credit environment (15% weight): looser = higher probability
        """
        # Credit score: 300-850 scale → 0-100
        cs_score = max(0.0, min(100.0, (app.credit_score - 300.0) / 5.5))

        # DSR score: 0% = 100, 40%+ = 0
        dsr_score = max(0.0, min(100.0, (1.0 - app.debt_service_ratio / ISLAMIC_DSR_MAX) * 100.0))

        # Collateral score: 0.5x = 20, 1.0x = 60, 1.5x+ = 100
        coll_score = min(100.0, max(20.0, (app.asset_backing_ratio - 0.5) * 80.0 + 20.0))

        # Macro: tighter credit conditions reduce approval probability
        macro_adj = max(20.0, 100.0 - macro.credit_conditions_index * 0.6)

        score = (
            cs_score * 0.40
            + dsr_score * 0.25
            + coll_score * 0.20
            + macro_adj * 0.15
        )

        return round(min(98.0, max(5.0, score)), 2)

    def _compute_risk_exposure(
        self, app: CreditApplication, macro: MacroSnapshot
    ) -> tuple[float, float, float]:
        """
        Default risk index (0-100, lower = safer).

        Returns (risk_exposure, pd_estimate, lgd_estimate)

        PD (Probability of Default) estimated from:
          - Credit score
          - DSR
          - Sector risk
          - Macro stress

        LGD (Loss Given Default) estimated from:
          - Collateral coverage
          - Collateral type liquidity
        """
        # PD estimate
        cs_pd = max(0.01, 0.50 - (app.credit_score - 300.0) / 1100.0)
        dsr_pd = max(0.0, (app.debt_service_ratio - 0.20) * 0.8)
        macro_pd = macro.market_stress_index / 500.0
        pd = min(0.85, max(0.005, cs_pd + dsr_pd + macro_pd))

        # LGD estimate by collateral type
        lgd_by_collateral = {
            "property": 0.25,
            "equipment": 0.45,
            "inventory": 0.55,
            "guarantee": 0.40,
            "cash": 0.05,
            "gold": 0.15,
        }
        base_lgd = lgd_by_collateral.get(app.collateral_type, 0.45)
        coverage_adj = max(0.0, 1.0 - app.asset_backing_ratio * 0.5)
        lgd = min(0.90, max(0.05, base_lgd * (0.5 + coverage_adj * 0.5)))

        # Risk exposure = EL (Expected Loss) × 100, inverted for scale
        expected_loss_rate = pd * lgd
        risk_score = min(95.0, max(5.0, expected_loss_rate * 300.0))

        return round(risk_score, 2), round(pd, 4), round(lgd, 4)

    def _compute_signal_coherence(self, app: CreditApplication, macro: MacroSnapshot) -> float:
        """
        Agreement between credit indicators (0-100, higher = more coherent).

        High coherence: all indicators tell the same story.
        Low coherence: mixed signals (good credit score but terrible DSR, etc.)
        """
        # Create a list of normalized sub-scores
        cs_norm = (app.credit_score - 300.0) / 5.5           # 0-100
        dsr_norm = (1.0 - app.debt_service_ratio / ISLAMIC_DSR_MAX) * 100  # 0-100 (lower DSR = better); uses same ceiling as dsr_score (ADR-074)
        coll_norm = min(100.0, app.asset_backing_ratio * 60.0)  # 0-100
        macro_norm = 100.0 - macro.credit_conditions_index      # 0-100

        subs = [
            min(100.0, max(0.0, cs_norm)),
            min(100.0, max(0.0, dsr_norm)),
            min(100.0, max(0.0, coll_norm)),
            min(100.0, max(0.0, macro_norm)),
        ]

        mean = sum(subs) / len(subs)
        variance = sum((s - mean) ** 2 for s in subs) / len(subs)
        std_dev = math.sqrt(variance)

        # High std_dev = low coherence (indicators disagree)
        coherence = max(10.0, min(95.0, 100.0 - std_dev * 0.8))

        return round(coherence, 2)

    def _compute_trend_persistence(self, macro: MacroSnapshot) -> float:
        """
        Macro credit conditions stability (0-100, higher = more stable/persistent).

        Derived from:
          - Macro volatility (lower = more stable = higher persistence)
          - Credit conditions index stability
          - VIX proxy (lower = calmer = higher persistence)
        """
        volatility_score = max(10.0, 100.0 - macro.macro_volatility * 1.2)
        vix_score = max(10.0, 100.0 - macro.vix_proxy * 2.5)
        spread_stability = max(10.0, 100.0 - (macro.credit_spread_bps / 5.0))

        persistence = (
            volatility_score * 0.50
            + vix_score * 0.30
            + spread_stability * 0.20
        )

        return round(min(95.0, max(10.0, persistence)), 2)

    def _compute_stress_resilience(self, app: CreditApplication, macro: MacroSnapshot) -> float:
        """
        Income shock resilience (0-100, higher = more resilient).

        Islamic finance stress test: Can the borrower survive a 20% income reduction?
        Monthly_income = annual_revenue / 12
        Monthly_payment = (requested_amount / tenor_months) * (1 + profit_rate/12)
        Residual_after_shock = income_shock_80% - existing_obligations - new_payment
        """
        monthly_income = app.annual_revenue / 12.0
        shock_income = monthly_income * 0.80  # 20% income reduction

        # Estimate monthly payment (Islamic profit rate proxy)
        profit_rate = 0.055  # ~5.5% p.a. (UAE Islamic finance typical)
        monthly_payment = (app.requested_amount / app.tenor_months) * (1 + profit_rate / 12)
        existing_monthly = app.existing_obligations

        residual = shock_income - existing_monthly - monthly_payment

        # Normalize: residual > income*30% = 100, residual < 0 = 0
        threshold = monthly_income * 0.30
        resilience = min(100.0, max(0.0, (residual / threshold) * 70.0 + 30.0))

        # Macro stress penalty
        macro_penalty = macro.market_stress_index * 0.15
        resilience = max(5.0, resilience - macro_penalty)

        return round(resilience, 2)

    def _compute_logic_consistency(self, app: CreditApplication) -> tuple[float, list]:
        """
        Internal consistency of the application (0-100, higher = more consistent).

        Detects logical contradictions:
        - High annual revenue + very high DSR → contradiction
        - Large loan + very short tenor → unusual
        - Low credit score + claiming A-grade collateral → needs scrutiny
        - Halal sector claim + haram sector characteristics → contradiction
        """
        score = 100.0
        notes = []

        # Check DSR vs revenue ratio
        expected_monthly_income = app.annual_revenue / 12.0
        expected_obligations = expected_monthly_income * app.debt_service_ratio
        if expected_obligations > expected_monthly_income * 0.6:
            score -= 20.0
            notes.append("DSR inconsistent with reported revenue level")

        # Check loan-to-revenue ratio (should be ≤ 3x annual revenue for SME)
        if app.applicant_type == "SME":
            ltr = app.requested_amount / max(1, app.annual_revenue)
            if ltr > 3.0:
                score -= 15.0
                notes.append(f"Loan-to-revenue ratio {ltr:.1f}x exceeds SME norm (3x)")

        # Check collateral type vs sector
        if app.sector in {"technology", "professional_services"} and app.collateral_type == "inventory":
            score -= 10.0
            notes.append("Inventory collateral unusual for service sector")

        # Check gharar vs financing type
        if app.financing_type == "Murabaha" and app.gharar_score > 50.0:
            score -= 15.0
            notes.append(f"High gharar ({app.gharar_score:.0f}) inconsistent with Murabaha structure")

        # Check tenor reasonableness
        if app.tenor_months < 6 and app.requested_amount > 500_000:
            score -= 10.0
            notes.append("Very short tenor for large financing amount")

        return round(max(10.0, score), 2), notes

    def _compute_signal_integrity(self, app: CreditApplication) -> float:
        """
        Data completeness and quality (0-100).
        Higher when all fields are present and within valid ranges.
        """
        score = 100.0

        if app.credit_score < 300 or app.credit_score > 850:
            score -= 20.0
        if app.annual_revenue <= 0:
            score -= 25.0
        if app.debt_service_ratio < 0 or app.debt_service_ratio > 1:
            score -= 20.0
        if app.tenor_months <= 0 or app.tenor_months > 360:
            score -= 15.0
        if app.requested_amount <= 0:
            score -= 25.0

        return round(max(10.0, score), 2)

    def _compute_temporal_coherence(self, macro: MacroSnapshot) -> float:
        """
        Macro conditions temporal coherence (0-100).
        Are current conditions consistent with recent history?
        Higher when macro data is fresh and stable.
        """
        freshness = max(0.0, 1.0 - macro.age_seconds / 7200.0)  # Degrades over 2h
        stability = max(20.0, 100.0 - macro.macro_volatility * 0.8)

        coherence = freshness * 0.30 * 100.0 + stability * 0.70

        return round(min(95.0, max(20.0, coherence)), 2)

    def _check_sharia_compliance(self, app: CreditApplication) -> tuple[bool, str]:
        """
        Islamic finance compliance check.
        Returns (is_compliant, violation_reason).
        """
        # Haram sector check
        if app.sector.lower() in HARAM_SECTORS:
            return False, f"Sector '{app.sector}' is prohibited under Sharia principles"

        # Riba check
        if not app.riba_free:
            return False, "Financing structure contains interest (Riba) — not permissible"

        # Gharar limit
        if app.gharar_score > GHARAR_MAX:
            return False, (
                f"Excessive uncertainty (Gharar={app.gharar_score:.0f} > {GHARAR_MAX}). "
                "Contract must specify clear terms and deliverables."
            )

        # Debt ratio (simplified: DSR as proxy)
        if app.debt_service_ratio > ISLAMIC_DSR_MAX:
            return False, (
                f"Debt Service Ratio {app.debt_service_ratio*100:.1f}% exceeds Islamic limit of "
                f"{ISLAMIC_DSR_MAX*100:.0f}%"
            )

        # Asset-backing requirement
        if app.asset_backing_ratio < 0.50 and app.financing_type in {"Murabaha", "Ijara"}:
            return False, (
                f"Asset backing ratio {app.asset_backing_ratio:.2f} insufficient "
                "for asset-backed Islamic financing"
            )

        return True, ""
