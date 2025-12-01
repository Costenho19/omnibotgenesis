#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧠 NON-MARKOVIAN MEMORY KERNEL - OMNIX V6.1 ULTRA
Quantum-Inspired Temporal Memory for Market Regime Detection

KERNEL EQUATION:
K(t-s) = exp(-|t-s|/τ) × [1 + ε × cos(Ω(t-s))]

Where:
- τ (tau): Memory decay constant (temporal coherence length)
- ε (epsilon): Oscillation amplitude (memory modulation strength)  
- Ω (omega): Memory oscillation frequency (cyclical patterns)

This kernel captures non-Markovian dependencies in market data that
traditional models miss. Unlike Markov processes that only consider
the immediate past, this kernel integrates weighted historical
information with oscillatory memory patterns.

APPLICATIONS:
1. Enhanced regime detection (trend vs ranging vs volatile)
2. Cyclical pattern recognition (market rhythms)
3. Long-range correlation analysis
4. Improved signal quality scoring

Harold Nunes - Noviembre 2025
OMNIX V6.1 ULTRA - Institutional Trading System
"""

import logging
import numpy as np
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class NonMarkovianKernel:
    """
    🧠 Non-Markovian Memory Kernel for Enhanced Market Analysis
    
    Implements K(t-s) = exp(-|t-s|/τ)[1 + ε cos(Ω(t-s))]
    
    This kernel allows OMNIX to capture temporal dependencies that
    extend beyond the Markov assumption, detecting patterns in market
    data that reflect institutional memory and cyclical behavior.
    """
    
    def __init__(self, 
                 tau: float = 12.0,      # Memory decay (hours)
                 epsilon: float = 0.35,   # Oscillation amplitude
                 omega: float = 0.523,    # Oscillation frequency (rad/period)
                 window_size: int = 168): # 1 week of hourly data
        """
        Initialize the Non-Markovian Kernel.
        
        Args:
            tau: Memory decay constant (hours). Higher = longer memory.
                 Default 12.0 captures intraday institutional patterns.
            epsilon: Oscillation amplitude [0, 1]. Higher = stronger cyclical memory.
                 Default 0.35 balances stability with pattern detection.
            omega: Oscillation frequency (radians per period).
                 Default 0.523 ≈ π/6 captures 12-hour market cycles.
            window_size: Number of historical periods to consider.
                 Default 168 = 1 week of hourly data.
        """
        self.tau = tau
        self.epsilon = epsilon
        self.omega = omega
        self.window_size = window_size
        self.name = "NON-MARKOVIAN KERNEL"
        self.version = "1.0.0"
        
        self._price_history: List[float] = []
        self._timestamp_history: List[datetime] = []
        self._kernel_cache: Optional[np.ndarray] = None
        self._last_signal: Optional[str] = None
        self._last_confidence: float = 0.0
        
        # On-Chain Data Integration V6.5
        self._on_chain_signal: Optional[Dict] = None
        self._on_chain_weight: float = 0.15  # Weight for on-chain signals in composite score
        
        logger.info("=" * 70)
        logger.info("🧠 NON-MARKOVIAN KERNEL INITIALIZED")
        logger.info(f"   τ (tau) = {tau} hours (memory decay)")
        logger.info(f"   ε (epsilon) = {epsilon} (oscillation amplitude)")
        logger.info(f"   Ω (omega) = {omega} rad/period (frequency)")
        logger.info(f"   Window = {window_size} periods")
        logger.info("=" * 70)
    
    def compute_kernel(self, t: float, s: float) -> float:
        """
        Compute the non-Markovian kernel K(t-s).
        
        K(t-s) = exp(-|t-s|/τ) × [1 + ε × cos(Ω(t-s))]
        
        Args:
            t: Current time index
            s: Historical time index
            
        Returns:
            Kernel value representing memory weight
        """
        delta = abs(t - s)
        exponential_decay = np.exp(-delta / self.tau)
        oscillatory_modulation = 1.0 + self.epsilon * np.cos(self.omega * delta)
        return exponential_decay * oscillatory_modulation
    
    def compute_kernel_matrix(self, n_points: int) -> np.ndarray:
        """
        Compute the full kernel matrix for convolution.
        
        Args:
            n_points: Number of time points
            
        Returns:
            Kernel weight matrix of shape (n_points,)
        """
        kernel_weights = np.zeros(n_points)
        current_time = n_points - 1
        
        for i in range(n_points):
            kernel_weights[i] = self.compute_kernel(current_time, i)
        
        kernel_weights = kernel_weights / np.sum(kernel_weights)
        
        return kernel_weights
    
    def update_history(self, price: float, timestamp: Optional[datetime] = None) -> None:
        """
        Update the price history buffer.
        
        Args:
            price: Current price value
            timestamp: Optional timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        self._price_history.append(price)
        self._timestamp_history.append(timestamp)
        
        if len(self._price_history) > self.window_size:
            self._price_history = self._price_history[-self.window_size:]
            self._timestamp_history = self._timestamp_history[-self.window_size:]
        
        self._kernel_cache = None
    
    def get_history_length(self) -> int:
        """
        Get the current length of the price history buffer.
        
        Returns:
            Number of price points in history
        """
        return len(self._price_history)
    
    def seed_history(self, prices: list, clear_existing: bool = True, 
                     sampling_interval_hours: float = 1.0,
                     anchor_timestamp: Optional[datetime] = None) -> int:
        """
        Seed the kernel with historical price data in chronological order.
        
        Timestamps are generated with proper temporal spacing to preserve
        kernel decay calculations (τ=12h). The anchor timestamp represents
        when the most recent price was observed.
        
        Args:
            prices: List of prices in chronological order (oldest first)
            clear_existing: If True, clear existing history before seeding
            sampling_interval_hours: Time interval between samples in hours (default: 1h)
            anchor_timestamp: Timestamp for the last price (defaults to now minus 1 interval)
            
        Returns:
            Number of prices loaded
        """
        if clear_existing:
            self._price_history = []
            self._timestamp_history = []
            self._kernel_cache = None
        
        prices_to_load = prices[-self.window_size:]
        n_prices = len(prices_to_load)
        
        if n_prices == 0:
            return 0
        
        interval_delta = timedelta(hours=sampling_interval_hours)
        
        if anchor_timestamp is None:
            if self._timestamp_history:
                anchor_timestamp = self._timestamp_history[-1]
            else:
                anchor_timestamp = datetime.utcnow() - interval_delta
        
        start_time = anchor_timestamp - (interval_delta * (n_prices - 1))
        
        for i, price in enumerate(prices_to_load):
            timestamp = start_time + (interval_delta * i)
            self._price_history.append(price)
            self._timestamp_history.append(timestamp)
        
        self._kernel_cache = None
        return n_prices
    
    def compute_memory_weighted_price(self) -> Optional[float]:
        """
        Compute the memory-weighted price using kernel convolution.
        
        This gives more weight to prices at times that are relevant
        according to the non-Markovian kernel.
        
        Returns:
            Memory-weighted average price, or None if insufficient data
        """
        if len(self._price_history) < 2:
            return None
        
        prices = np.array(self._price_history)
        kernel_weights = self.compute_kernel_matrix(len(prices))
        
        memory_weighted_price = np.dot(prices, kernel_weights)
        
        return float(memory_weighted_price)
    
    def compute_memory_divergence(self, current_price: float) -> Optional[float]:
        """
        Compute divergence between current price and memory-weighted price.
        
        Positive divergence: Price above historical memory (bullish signal)
        Negative divergence: Price below historical memory (bearish signal)
        
        Args:
            current_price: Current market price
            
        Returns:
            Divergence percentage, or None if insufficient data
        """
        memory_price = self.compute_memory_weighted_price()
        if memory_price is None or memory_price == 0:
            return None
        
        divergence = ((current_price - memory_price) / memory_price) * 100.0
        
        return divergence
    
    def compute_memory_momentum(self) -> Optional[float]:
        """
        Compute momentum of the memory-weighted signal.
        
        This captures the rate of change of the kernel-convolved signal,
        detecting acceleration/deceleration in memory-integrated trends.
        
        Returns:
            Memory momentum value [-100, 100], or None if insufficient data
        """
        if len(self._price_history) < 10:
            return None
        
        prices = np.array(self._price_history)
        n = len(prices)
        
        kernel_weights = self.compute_kernel_matrix(n)
        weighted_prices = prices * kernel_weights
        
        cumsum = np.cumsum(weighted_prices)
        
        if n >= 10:
            recent = np.mean(cumsum[-5:])
            older = np.mean(cumsum[-10:-5])
            
            if older != 0:
                momentum = ((recent - older) / abs(older)) * 100.0
                return float(np.clip(momentum, -100, 100))
        
        return 0.0
    
    def compute_cyclical_strength(self) -> Optional[float]:
        """
        Measure the strength of cyclical patterns in memory.
        
        Uses autocorrelation analysis weighted by the kernel to detect
        periodic structures in the price history.
        
        Returns:
            Cyclical strength [0, 100], or None if insufficient data
        """
        if len(self._price_history) < 24:
            return None
        
        prices = np.array(self._price_history)
        n = len(prices)
        
        prices_normalized = prices - np.mean(prices)
        
        if np.std(prices_normalized) < 1e-10:
            return 0.0
        
        prices_normalized = prices_normalized / np.std(prices_normalized)
        
        max_lag = min(n // 2, 48)
        autocorr_weighted = []
        
        for lag in range(1, max_lag + 1):
            autocorr = np.corrcoef(prices_normalized[:-lag], 
                                   prices_normalized[lag:])[0, 1]
            weight = self.compute_kernel(0, lag)
            autocorr_weighted.append(autocorr * weight)
        
        if len(autocorr_weighted) == 0:
            return 0.0
        
        cyclical_strength = np.max(np.abs(autocorr_weighted)) * 100.0
        
        return float(np.clip(cyclical_strength, 0, 100))
    
    def compute_regime_coherence(self) -> Optional[Dict[str, float]]:
        """
        Compute multi-dimensional regime coherence analysis.
        
        Analyzes how coherent the current market regime is based on
        the kernel's memory perspective.
        
        Returns:
            Dictionary with coherence metrics, or None if insufficient data
        """
        if len(self._price_history) < 24:
            return None
        
        prices = np.array(self._price_history)
        n = len(prices)
        
        returns = np.diff(prices) / prices[:-1] * 100.0
        
        kernel_weights = self.compute_kernel_matrix(n - 1)
        
        weighted_mean_return = np.sum(returns * kernel_weights)
        weighted_variance = np.sum(((returns - weighted_mean_return) ** 2) * kernel_weights)
        weighted_volatility = np.sqrt(weighted_variance)
        
        if weighted_volatility < 1e-10:
            trend_coherence = 0.0
        else:
            trend_coherence = abs(weighted_mean_return) / weighted_volatility
        trend_coherence = min(trend_coherence * 50, 100.0)
        
        recent_vol = np.std(returns[-12:]) if len(returns) >= 12 else np.std(returns)
        historical_vol = np.std(returns)
        if historical_vol > 0:
            vol_ratio = recent_vol / historical_vol
            volatility_coherence = 100.0 - abs(vol_ratio - 1.0) * 50
            volatility_coherence = max(0, min(100, volatility_coherence))
        else:
            volatility_coherence = 50.0
        
        cyclical = self.compute_cyclical_strength()
        memory_coherence = cyclical if cyclical is not None else 50.0
        
        overall_coherence = (
            trend_coherence * 0.40 + 
            volatility_coherence * 0.30 + 
            memory_coherence * 0.30
        )
        
        return {
            "trend_coherence": round(trend_coherence, 2),
            "volatility_coherence": round(volatility_coherence, 2),
            "memory_coherence": round(memory_coherence, 2),
            "overall_coherence": round(overall_coherence, 2)
        }
    
    def integrate_on_chain_signal(self, on_chain_data: Dict) -> None:
        """
        🔗 Integrate on-chain signal into the kernel analysis.
        
        On-chain data provides additional market insight from:
        - Whale transaction activity
        - Exchange flow patterns
        - Network health metrics
        - Smart money movements
        
        Args:
            on_chain_data: Dict from OnChainSignal.to_kernel_format()
                Expected keys:
                - 'signal': float (-1 to 1, composite score)
                - 'bias': str ('bullish', 'bearish', 'neutral')
                - 'confidence': float (0 to 1)
                - 'components': dict with whale, exchange_flow, network, smart_money scores
        """
        self._on_chain_signal = on_chain_data
        logger.debug(
            f"🔗 On-chain signal integrated: bias={on_chain_data.get('bias')}, "
            f"score={on_chain_data.get('signal', 0):.3f}"
        )
    
    def set_on_chain_weight(self, weight: float) -> None:
        """
        Set the weight for on-chain signals in composite analysis.
        
        Args:
            weight: Weight between 0 and 0.3 (max 30% influence)
        """
        self._on_chain_weight = max(0.0, min(0.3, weight))
        logger.info(f"On-chain weight set to {self._on_chain_weight:.2f}")
    
    def _compute_on_chain_boost(self) -> Tuple[float, float, str]:
        """
        Compute signal boost from on-chain data.
        
        Returns:
            Tuple of (bullish_boost, bearish_boost, reason)
        """
        if not self._on_chain_signal:
            return 0.0, 0.0, ""
        
        signal = self._on_chain_signal.get('signal', 0)
        confidence = self._on_chain_signal.get('confidence', 0)
        bias = self._on_chain_signal.get('bias', 'neutral')
        
        # Scale boost by weight and confidence
        boost_factor = abs(signal) * confidence * self._on_chain_weight * 100
        
        bullish_boost = boost_factor if signal > 0 else 0.0
        bearish_boost = boost_factor if signal < 0 else 0.0
        
        components = self._on_chain_signal.get('components', {})
        
        reasons = []
        if components.get('whale', 0) > 0.2:
            reasons.append("whale accumulation")
        elif components.get('whale', 0) < -0.2:
            reasons.append("whale distribution")
        
        if components.get('exchange_flow', 0) > 0.2:
            reasons.append("exchange outflows (bullish)")
        elif components.get('exchange_flow', 0) < -0.2:
            reasons.append("exchange inflows (bearish)")
        
        reason = f"On-chain: {', '.join(reasons)}" if reasons else ""
        
        return bullish_boost, bearish_boost, reason
    
    def generate_signal(self, current_price: float, 
                        market_data: Optional[Dict] = None) -> Dict:
        """
        Generate trading signal based on non-Markovian analysis.
        
        Combines memory divergence, momentum, cyclical patterns,
        regime coherence, and on-chain data into a unified trading signal.
        
        Args:
            current_price: Current market price
            market_data: Optional additional market data
            
        Returns:
            Dictionary with signal, confidence, and detailed metrics
        """
        self.update_history(current_price)
        
        if len(self._price_history) < 24:
            return {
                "signal": "HOLD",
                "confidence": 0.0,
                "reason": "Insufficient data for non-Markovian analysis",
                "metrics": {
                    "data_points": len(self._price_history),
                    "required_minimum": 24
                }
            }
        
        divergence = self.compute_memory_divergence(current_price)
        momentum = self.compute_memory_momentum()
        cyclical = self.compute_cyclical_strength()
        coherence = self.compute_regime_coherence()
        
        if divergence is None or momentum is None:
            return {
                "signal": "HOLD",
                "confidence": 0.0,
                "reason": "Calculation error in kernel analysis",
                "metrics": {}
            }
        
        bullish_score = 0.0
        bearish_score = 0.0
        
        if divergence > 0.5:
            bullish_score += min(divergence * 2, 30)
        elif divergence < -0.5:
            bearish_score += min(abs(divergence) * 2, 30)
        
        if momentum > 5:
            bullish_score += min(momentum * 0.5, 25)
        elif momentum < -5:
            bearish_score += min(abs(momentum) * 0.5, 25)
        
        if coherence and coherence["overall_coherence"] > 60:
            coherence_boost = (coherence["overall_coherence"] - 60) * 0.5
            if bullish_score > bearish_score:
                bullish_score += coherence_boost
            else:
                bearish_score += coherence_boost
        
        if cyclical and cyclical > 50:
            cyclical_boost = (cyclical - 50) * 0.2
            if bullish_score > bearish_score:
                bullish_score += cyclical_boost
            else:
                bearish_score += cyclical_boost
        
        # On-Chain Data Integration V6.5
        on_chain_bullish, on_chain_bearish, on_chain_reason = self._compute_on_chain_boost()
        bullish_score += on_chain_bullish
        bearish_score += on_chain_bearish
        
        total_score = bullish_score + bearish_score
        
        if total_score < 20:
            signal = "HOLD"
            confidence = 30.0 + (20 - total_score)
        elif bullish_score > bearish_score * 1.3:
            signal = "BUY"
            confidence = min(bullish_score * 2, 85)
        elif bearish_score > bullish_score * 1.3:
            signal = "SELL"
            confidence = min(bearish_score * 2, 85)
        else:
            signal = "HOLD"
            confidence = 45.0
        
        self._last_signal = signal
        self._last_confidence = confidence
        
        return {
            "signal": signal,
            "confidence": round(confidence, 1),
            "reason": self._generate_reason(signal, divergence, momentum, coherence),
            "metrics": {
                "memory_divergence": round(divergence, 4),
                "memory_momentum": round(momentum, 2),
                "cyclical_strength": round(cyclical, 2) if cyclical else 0,
                "regime_coherence": coherence,
                "bullish_score": round(bullish_score, 2),
                "bearish_score": round(bearish_score, 2),
                "data_points": len(self._price_history),
                "kernel_params": {
                    "tau": self.tau,
                    "epsilon": self.epsilon,
                    "omega": self.omega
                }
            }
        }
    
    def _generate_reason(self, signal: str, divergence: float, 
                         momentum: float, coherence: Optional[Dict]) -> str:
        """Generate human-readable reason for the signal."""
        reasons = []
        
        if abs(divergence) > 0.5:
            direction = "above" if divergence > 0 else "below"
            reasons.append(f"Price {direction} memory-weighted mean ({divergence:.2f}%)")
        
        if abs(momentum) > 5:
            direction = "bullish" if momentum > 0 else "bearish"
            reasons.append(f"Memory momentum {direction} ({momentum:.1f})")
        
        if coherence and coherence["overall_coherence"] > 60:
            reasons.append(f"High regime coherence ({coherence['overall_coherence']:.0f}%)")
        
        if not reasons:
            return "No strong non-Markovian signals detected"
        
        return " | ".join(reasons)
    
    def get_kernel_explanation(self) -> str:
        """
        Get a detailed explanation of the kernel for investor presentations.
        
        Returns:
            Formatted explanation string
        """
        return f"""
🧠 NON-MARKOVIAN MEMORY KERNEL v{self.version}

KERNEL EQUATION:
K(t-s) = exp(-|t-s|/τ) × [1 + ε × cos(Ω(t-s))]

CURRENT PARAMETERS:
• τ (tau) = {self.tau} hours — Memory decay constant
• ε (epsilon) = {self.epsilon} — Oscillation amplitude  
• Ω (omega) = {self.omega} rad/period — Frequency

WHAT IT DOES:
Unlike Markov models that only look at the immediate past,
this kernel integrates weighted historical information with
oscillatory memory patterns. It captures:

1. TEMPORAL MEMORY: How past prices influence current analysis
2. CYCLICAL PATTERNS: Periodic market rhythms (12h, 24h cycles)
3. REGIME COHERENCE: Stability of the current market state
4. MEMORY DIVERGENCE: When price departs from historical trends

TRADING APPLICATION:
- Identifies regime transitions before they complete
- Detects institutional accumulation/distribution patterns
- Filters noise by weighting relevant historical data
- Improves signal quality through temporal coherence analysis

DATA POINTS IN MEMORY: {len(self._price_history)}/{self.window_size}
LAST SIGNAL: {self._last_signal or 'N/A'} ({self._last_confidence:.1f}% confidence)
"""
    
    def to_dict(self) -> Dict:
        """Export kernel state as dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "params": {
                "tau": self.tau,
                "epsilon": self.epsilon,
                "omega": self.omega,
                "window_size": self.window_size
            },
            "state": {
                "data_points": len(self._price_history),
                "last_signal": self._last_signal,
                "last_confidence": self._last_confidence
            }
        }
