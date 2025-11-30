"""
OMNIX V6.4 INSTITUTIONAL+ Volatility Targeting Engine
Dynamic position sizing to maintain target portfolio volatility
Used by: Bridgewater, AQR, Two Sigma
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class RiskProfile(Enum):
    """Predefined risk profiles for investors"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    INSTITUTIONAL = "institutional"


@dataclass
class VolTargetResult:
    """Container for volatility targeting results"""
    original_weights: Dict[str, float]
    scaled_weights: Dict[str, float]
    scaling_factor: float
    target_volatility: float
    current_volatility: float
    leverage: float
    risk_profile: RiskProfile
    timestamp: datetime


class VolatilityTargetingEngine:
    """
    INSTITUTIONAL+ Volatility Targeting V6.4
    
    Purpose: Dynamically adjust portfolio exposure to maintain
    a consistent volatility level regardless of market conditions.
    
    Key Benefits:
    - Reduces exposure when markets are volatile
    - Increases exposure when markets are calm
    - Provides consistent risk experience to investors
    - Used by major quant funds globally
    
    Risk Profiles:
    - Conservative: 5% annual vol (pension funds)
    - Moderate: 10% annual vol (endowments)
    - Aggressive: 15% annual vol (hedge funds)
    - Institutional: 12% annual vol (balanced)
    """
    
    VERSION = "6.4.0"
    
    PROFILE_VOLATILITIES = {
        RiskProfile.CONSERVATIVE: 0.05,
        RiskProfile.MODERATE: 0.10,
        RiskProfile.AGGRESSIVE: 0.15,
        RiskProfile.INSTITUTIONAL: 0.12
    }
    
    def __init__(
        self,
        target_volatility_annual: float = 0.10,
        max_leverage: float = 1.5,
        min_leverage: float = 0.2,
        annualization_factor: int = 252,
        smoothing_halflife: int = 20
    ):
        self.target_volatility = target_volatility_annual
        self.max_leverage = max_leverage
        self.min_leverage = min_leverage
        self.annualization_factor = annualization_factor
        self.smoothing_halflife = smoothing_halflife
        
        self._volatility_history: List[float] = []
        self._scaling_history: List[float] = []
        
        logger.info(
            f"VolatilityTargetingEngine V{self.VERSION} | "
            f"Target: {target_volatility_annual:.1%} annual"
        )
    
    def set_risk_profile(self, profile: RiskProfile) -> None:
        """Set volatility target from predefined profile"""
        self.target_volatility = self.PROFILE_VOLATILITIES[profile]
        logger.info(f"Risk profile set to {profile.value}: {self.target_volatility:.1%}")
    
    def compute_portfolio_volatility(
        self,
        weights: np.ndarray,
        cov_matrix: np.ndarray,
        annualize: bool = True
    ) -> float:
        """
        Compute portfolio volatility from weights and covariance
        
        Args:
            weights: Portfolio weights (N,)
            cov_matrix: Covariance matrix (N,N)
            annualize: Convert to annual volatility
        
        Returns:
            Portfolio volatility (annual if annualize=True)
        """
        if len(weights) == 0 or cov_matrix.size == 0:
            return 0.0
        
        variance = weights @ cov_matrix @ weights
        daily_vol = np.sqrt(max(variance, 0))
        
        if annualize:
            return daily_vol * np.sqrt(self.annualization_factor)
        
        return daily_vol
    
    def compute_scaling_factor(
        self,
        weights: np.ndarray,
        cov_matrix: np.ndarray,
        smooth: bool = True
    ) -> float:
        """
        Compute scaling factor to achieve target volatility
        
        Args:
            weights: Current portfolio weights
            cov_matrix: Current covariance matrix
            smooth: Apply exponential smoothing to avoid whipsawing
        
        Returns:
            Scaling factor to apply to weights
        """
        current_vol = self.compute_portfolio_volatility(weights, cov_matrix)
        
        if current_vol == 0:
            return 1.0
        
        raw_scaling = self.target_volatility / current_vol
        
        if smooth and len(self._scaling_history) > 0:
            alpha = 2 / (self.smoothing_halflife + 1)
            prev_scaling = self._scaling_history[-1]
            raw_scaling = alpha * raw_scaling + (1 - alpha) * prev_scaling
        
        scaling = np.clip(raw_scaling, self.min_leverage, self.max_leverage)
        
        self._volatility_history.append(current_vol)
        self._scaling_history.append(scaling)
        
        if len(self._volatility_history) > 100:
            self._volatility_history = self._volatility_history[-100:]
            self._scaling_history = self._scaling_history[-100:]
        
        return float(scaling)
    
    def apply_volatility_targeting(
        self,
        weights: Dict[str, float],
        cov_matrix: np.ndarray,
        symbols: List[str],
        risk_profile: Optional[RiskProfile] = None
    ) -> VolTargetResult:
        """
        Apply volatility targeting to portfolio weights
        
        This is the MAIN entry point for vol targeting.
        
        Args:
            weights: Dict of current weights per symbol
            cov_matrix: Covariance matrix
            symbols: List of symbols (matching cov_matrix order)
            risk_profile: Optional profile override
        
        Returns:
            VolTargetResult with scaled weights and metrics
        """
        if risk_profile:
            target = self.PROFILE_VOLATILITIES[risk_profile]
        else:
            target = self.target_volatility
            risk_profile = self._detect_profile(target)
        
        original_target = self.target_volatility
        self.target_volatility = target
        
        weights_array = np.array([weights.get(s, 0.0) for s in symbols])
        
        if np.sum(weights_array) > 0:
            weights_array = weights_array / np.sum(weights_array)
        
        current_vol = self.compute_portfolio_volatility(weights_array, cov_matrix)
        scaling = self.compute_scaling_factor(weights_array, cov_matrix)
        
        scaled_array = weights_array * scaling
        
        if np.sum(np.abs(scaled_array)) > self.max_leverage:
            scaled_array = scaled_array * (self.max_leverage / np.sum(np.abs(scaled_array)))
        
        scaled_weights = {symbols[i]: round(float(scaled_array[i]), 6) 
                         for i in range(len(symbols))}
        
        leverage = float(np.sum(np.abs(scaled_array)))
        
        self.target_volatility = original_target
        
        result = VolTargetResult(
            original_weights=weights,
            scaled_weights=scaled_weights,
            scaling_factor=round(scaling, 4),
            target_volatility=round(target, 4),
            current_volatility=round(current_vol, 4),
            leverage=round(leverage, 4),
            risk_profile=risk_profile,
            timestamp=datetime.now()
        )
        
        logger.info(
            f"Vol targeting | Current: {current_vol:.1%} → Target: {target:.1%} | "
            f"Scaling: {scaling:.2f}x | Profile: {risk_profile.value}"
        )
        
        return result
    
    def _detect_profile(self, target_vol: float) -> RiskProfile:
        """Detect risk profile from target volatility"""
        if target_vol <= 0.06:
            return RiskProfile.CONSERVATIVE
        elif target_vol <= 0.11:
            return RiskProfile.MODERATE
        elif target_vol <= 0.13:
            return RiskProfile.INSTITUTIONAL
        else:
            return RiskProfile.AGGRESSIVE
    
    def get_volatility_regime(self) -> Dict:
        """Analyze current volatility regime"""
        if len(self._volatility_history) < 5:
            return {"regime": "unknown", "trend": "insufficient_data"}
        
        recent = np.mean(self._volatility_history[-5:])
        historical = np.mean(self._volatility_history)
        
        if recent > historical * 1.5:
            regime = "high_volatility"
            trend = "elevated"
        elif recent < historical * 0.7:
            regime = "low_volatility"
            trend = "compressed"
        else:
            regime = "normal"
            trend = "stable"
        
        return {
            "regime": regime,
            "trend": trend,
            "current_vol": round(recent, 4),
            "historical_vol": round(historical, 4),
            "ratio": round(recent / historical if historical > 0 else 1, 2)
        }
    
    def get_status(self) -> Dict:
        """Get engine status"""
        return {
            "engine": "VolatilityTargetingEngine",
            "version": self.VERSION,
            "target_volatility": self.target_volatility,
            "max_leverage": self.max_leverage,
            "history_length": len(self._volatility_history),
            "regime": self.get_volatility_regime()
        }
