"""
OMNIX V5.1 ENTERPRISE - Black Swan Detection System
Detecta eventos extremos y anomalías de mercado
"""

import numpy as np
from typing import Dict, Any, List, Optional
from omnix_config.settings import settings
from omnix_core.utils.logger import get_logger

# Initialize logger FIRST
logger = get_logger(__name__)

# Try to import scipy, fallback to numpy if not available
try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning("⚠️ SciPy not available - using NumPy fallback for Black Swan")


class BlackSwanDetector:
    """
    Advanced Black Swan event detection system
    
    Uses statistical analysis to detect:
    - Fat tails in return distributions
    - Extreme kurtosis and skewness
    - Volatility regime changes
    - Market crash probability
    """
    
    def __init__(self):
        self.kurtosis_threshold = 3.0  # Normal distribution = 3
        self.skewness_threshold = 0.5
        self.tail_threshold = 0.95  # 95th percentile
        logger.info("🦢 Black Swan Detector 2.0 initialized")
    
    def analyze(
        self,
        prices: List[float],
        returns: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Analyze price data for Black Swan indicators
        
        Args:
            prices: Historical price data
            returns: Optional pre-calculated returns
            
        Returns:
            Detection results with severity and probability
        """
        try:
            if len(prices) < 30:
                logger.warning("Insufficient data for Black Swan analysis")
                return {'detected': False, 'reason': 'insufficient_data'}
            
            # Calculate returns if not provided
            if returns is None:
                prices_arr = np.array(prices)
                returns = np.diff(prices_arr) / prices_arr[:-1]
            else:
                returns = np.array(returns)
            
            # Statistical moments
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            
            # Calculate skewness and kurtosis (with or without scipy)
            if SCIPY_AVAILABLE:
                skewness = stats.skew(returns)
                kurtosis = stats.kurtosis(returns, fisher=False)  # Pearson's kurtosis
            else:
                # NumPy fallback for skewness and kurtosis
                m3 = np.mean((returns - mean_return)**3)
                m4 = np.mean((returns - mean_return)**4)
                skewness = m3 / (std_return**3) if std_return > 0 else 0
                kurtosis = (m4 / (std_return**4)) if std_return > 0 else 3  # Excess kurtosis + 3
            
            # Detect fat tails
            tail_events = np.abs(returns) > (mean_return + 2 * std_return)
            tail_frequency = np.sum(tail_events) / len(returns)
            
            # Calculate extreme event probability
            extreme_threshold = mean_return + 3 * std_return
            extreme_events = np.abs(returns) > extreme_threshold
            extreme_frequency = np.sum(extreme_events) / len(returns)
            
            # Detect volatility clusters (ARCH effect)
            squared_returns = returns ** 2
            volatility_clustering = np.corrcoef(
                squared_returns[:-1],
                squared_returns[1:]
            )[0, 1]
            
            # Black Swan detection logic
            detected = False
            severity = 'low'
            indicators = []
            
            if kurtosis > self.kurtosis_threshold + 3:
                detected = True
                severity = 'high'
                indicators.append('extreme_kurtosis')
            elif kurtosis > self.kurtosis_threshold:
                detected = True
                severity = 'medium'
                indicators.append('elevated_kurtosis')
            
            if abs(skewness) > self.skewness_threshold + 1:
                detected = True
                if severity != 'high':
                    severity = 'medium'
                indicators.append('extreme_skewness')
            
            if tail_frequency > 0.1:  # More than 10% tail events
                detected = True
                severity = 'high'
                indicators.append('fat_tails')
            
            if extreme_frequency > 0.05:  # More than 5% extreme events
                detected = True
                severity = 'high'
                indicators.append('frequent_extremes')
            
            # Calculate crash probability using tail risk
            var_95 = np.percentile(returns, 5)
            cvar_95 = np.mean(returns[returns <= var_95])  # Conditional VaR
            crash_probability = extreme_frequency * (1 + abs(skewness))
            
            result = {
                'detected': detected,
                'severity': severity,
                'indicators': indicators,
                'statistics': {
                    'mean_return': mean_return,
                    'volatility': std_return,
                    'skewness': skewness,
                    'kurtosis': kurtosis,
                    'tail_frequency': tail_frequency,
                    'extreme_frequency': extreme_frequency,
                    'volatility_clustering': volatility_clustering
                },
                'risk_metrics': {
                    'var_95': var_95,
                    'cvar_95': cvar_95,
                    'crash_probability': crash_probability,
                    'tail_risk_score': kurtosis * tail_frequency
                },
                'recommendations': self._generate_recommendations(
                    detected, severity, indicators
                )
            }
            
            if detected:
                logger.warning(
                    f"🦢 Black Swan detected! Severity={severity}, "
                    f"Indicators={indicators}, Crash probability={crash_probability:.1%}"
                )
            else:
                logger.info("✅ No Black Swan events detected")
            
            return result
            
        except Exception as e:
            logger.error(f"Black Swan analysis error: {e}")
            return {'detected': False, 'error': str(e)}
    
    def _generate_recommendations(
        self,
        detected: bool,
        severity: str,
        indicators: List[str]
    ) -> List[str]:
        """Generate actionable recommendations based on detection"""
        recommendations = []
        
        if not detected:
            recommendations.append("Normal market conditions - standard risk management")
            return recommendations
        
        if severity == 'high':
            recommendations.append("⚠️ CRITICAL: Reduce position sizes immediately")
            recommendations.append("⚠️ Consider hedging strategies or stop-losses")
            recommendations.append("⚠️ Increase cash reserves")
        
        if severity == 'medium':
            recommendations.append("⚠️ Exercise caution - monitor closely")
            recommendations.append("⚠️ Tighten stop-losses")
        
        if 'fat_tails' in indicators:
            recommendations.append("Fat tail distribution detected - expect larger moves")
        
        if 'extreme_skewness' in indicators:
            recommendations.append("Asymmetric risk - one direction more likely")
        
        if 'frequent_extremes' in indicators:
            recommendations.append("High volatility regime - reduce leverage")
        
        return recommendations
    
    def estimate_tail_risk(self, returns: List[float]) -> Dict[str, float]:
        """Estimate tail risk using Extreme Value Theory"""
        try:
            returns_arr = np.array(returns)
            
            # Focus on left tail (losses)
            losses = -returns_arr[returns_arr < 0]
            
            if len(losses) < 10:
                return {}
            
            # Fit Generalized Pareto Distribution to tail
            threshold = np.percentile(losses, 90)
            exceedances = losses[losses > threshold] - threshold
            
            if len(exceedances) > 0:
                # Simple tail index estimate
                tail_index = np.mean(exceedances) / np.std(exceedances)
                
                return {
                    'tail_index': tail_index,
                    'tail_threshold': threshold,
                    'tail_observations': len(exceedances),
                    'max_loss_observed': np.max(losses)
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Tail risk estimation error: {e}")
            return {}
