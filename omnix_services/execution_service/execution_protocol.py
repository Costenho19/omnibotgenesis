"""
OMNIX Execution Protocol INSTITUTIONAL+
Main orchestrator for institutional-grade execution analysis

Integrates:
- LiquidityAnalyzer: Order book analysis, TBLR, hidden liquidity
- MicroVolatilityEngine: Regime detection, asymmetric response
- CrossAssetCorrelationEngine: Contagion risk, safe-haven flows

Provides:
- Execution Decision Matrix (TWAP/VWAP/ICEBERG/MARKET)
- Slippage prediction model
- Optimal execution timing
- Pre-trade analytics
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

import numpy as np

from omnix_config import VERSION_BANNER

logger = logging.getLogger(__name__)


class ExecutionStyle(Enum):
    """Execution algorithm selection"""
    MARKET = "market"
    LIMIT = "limit"
    TWAP = "twap"
    VWAP = "vwap"
    ICEBERG = "iceberg"
    POV = "pov"
    IMPLEMENTATION_SHORTFALL = "is"


class ExecutionUrgency(Enum):
    """Trade urgency classification"""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    PASSIVE = "passive"


class MarketCondition(Enum):
    """Current market condition assessment"""
    FAVORABLE = "favorable"
    NEUTRAL = "neutral"
    ADVERSE = "adverse"
    CRISIS = "crisis"


@dataclass
class SlippagePrediction:
    """Slippage estimation for trade execution"""
    expected_slippage_bps: float
    worst_case_slippage_bps: float
    best_case_slippage_bps: float
    confidence: float
    impact_by_size: Dict[float, float] = field(default_factory=dict)
    factors: Dict[str, float] = field(default_factory=dict)
    
    @property
    def expected_slippage_pct(self) -> float:
        return self.expected_slippage_bps / 100.0
    
    @property
    def is_acceptable(self) -> bool:
        return self.expected_slippage_bps < 50  # <0.5% acceptable
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'expected_slippage_bps': round(self.expected_slippage_bps, 2),
            'worst_case_slippage_bps': round(self.worst_case_slippage_bps, 2),
            'best_case_slippage_bps': round(self.best_case_slippage_bps, 2),
            'confidence': round(self.confidence, 3),
            'expected_slippage_pct': round(self.expected_slippage_pct, 4),
            'is_acceptable': self.is_acceptable,
            'factors': self.factors
        }


@dataclass
class ExecutionTiming:
    """Optimal execution timing recommendation"""
    execute_now: bool
    delay_seconds: int
    reason: str
    optimal_window_start: Optional[datetime] = None
    optimal_window_end: Optional[datetime] = None
    avoid_periods: List[str] = field(default_factory=list)
    confidence: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'execute_now': self.execute_now,
            'delay_seconds': self.delay_seconds,
            'reason': self.reason,
            'confidence': round(self.confidence, 3),
            'avoid_periods': self.avoid_periods
        }


@dataclass
class ExecutionDecision:
    """Complete execution recommendation from protocol"""
    symbol: str
    side: str
    size_usd: float
    recommended_style: ExecutionStyle
    urgency: ExecutionUrgency
    market_condition: MarketCondition
    slippage: SlippagePrediction
    timing: ExecutionTiming
    liquidity_score: float
    volatility_regime: str
    correlation_risk: float
    contagion_risk: float
    safe_haven_flow: str
    execution_params: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    confidence: float = 0.5
    timestamp: datetime = field(default_factory=datetime.now)
    data_integrity_block: bool = False
    block_reason: str = ""
    liquidity_data_available: bool = True
    correlation_data_available: bool = True
    
    @property
    def should_execute(self) -> bool:
        if self.data_integrity_block:
            return False
        return (
            self.timing.execute_now and
            self.slippage.is_acceptable and
            self.market_condition != MarketCondition.CRISIS and
            self.contagion_risk < 80
        )
    
    @property
    def risk_adjusted_size(self) -> float:
        risk_factor = 1.0
        if self.volatility_regime in ['HIGH', 'EXTREME']:
            risk_factor *= 0.5
        if self.contagion_risk > 50:
            risk_factor *= 0.7
        if self.correlation_risk > 70:
            risk_factor *= 0.8
        if self.market_condition == MarketCondition.ADVERSE:
            risk_factor *= 0.6
        return self.size_usd * risk_factor
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'side': self.side,
            'size_usd': round(self.size_usd, 2),
            'risk_adjusted_size': round(self.risk_adjusted_size, 2),
            'recommended_style': self.recommended_style.value,
            'urgency': self.urgency.value,
            'market_condition': self.market_condition.value,
            'should_execute': self.should_execute,
            'data_integrity_block': self.data_integrity_block,
            'block_reason': self.block_reason,
            'liquidity_data_available': self.liquidity_data_available,
            'correlation_data_available': self.correlation_data_available,
            'liquidity_score': round(self.liquidity_score, 2),
            'volatility_regime': self.volatility_regime,
            'correlation_risk': round(self.correlation_risk, 2),
            'contagion_risk': round(self.contagion_risk, 2),
            'safe_haven_flow': self.safe_haven_flow,
            'slippage': self.slippage.to_dict(),
            'timing': self.timing.to_dict(),
            'execution_params': self.execution_params,
            'warnings': self.warnings,
            'confidence': round(self.confidence, 3),
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class PreTradeAnalytics:
    """Pre-trade analysis summary"""
    symbol: str
    timestamp: datetime
    liquidity_analysis: Dict[str, Any]
    volatility_state: Dict[str, Any]
    correlation_state: Dict[str, Any]
    market_condition: MarketCondition
    overall_score: float
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'market_condition': self.market_condition.value,
            'overall_score': round(self.overall_score, 2),
            'liquidity_analysis': self.liquidity_analysis,
            'volatility_state': self.volatility_state,
            'correlation_state': self.correlation_state,
            'recommendations': self.recommendations
        }


class ExecutionProtocol:
    """
    OMNIX Execution Protocol V6.5.4 INSTITUTIONAL+
    
    Main orchestrator for institutional-grade execution analysis.
    Integrates liquidity, volatility, and correlation engines to provide
    optimal execution recommendations.
    
    Features:
    - Execution Decision Matrix (TWAP/VWAP/ICEBERG/MARKET selection)
    - Slippage prediction model with confidence scoring
    - Optimal execution timing with market condition awareness
    - Pre-trade analytics with comprehensive risk assessment
    - Real-time market condition classification
    
    Usage:
        protocol = ExecutionProtocol()
        decision = protocol.get_execution_decision(
            symbol='BTC/USD',
            side='buy',
            size_usd=10000.0
        )
        if decision.should_execute:
            # Execute with recommended style
            execute_order(
                style=decision.recommended_style,
                params=decision.execution_params
            )
    """
    
    SLIPPAGE_THRESHOLDS = {
        'excellent': 5,
        'good': 15,
        'acceptable': 30,
        'poor': 50,
        'unacceptable': 100
    }
    
    SIZE_THRESHOLDS = {
        'small': 1000,
        'medium': 10000,
        'large': 50000,
        'institutional': 100000,
        'whale': 500000
    }
    
    def __init__(
        self,
        liquidity_analyzer=None,
        volatility_engine=None,
        correlation_engine=None,
        trading_service=None
    ):
        """
        Initialize ExecutionProtocol with component engines.
        
        Args:
            liquidity_analyzer: LiquidityAnalyzer instance
            volatility_engine: MicroVolatilityEngine instance
            correlation_engine: CrossAssetCorrelationEngine instance
            trading_service: Trading service for market data
        """
        self._lock = threading.RLock()
        self.trading_service = trading_service
        
        try:
            from .liquidity_analyzer import LiquidityAnalyzer
            self.liquidity_analyzer = liquidity_analyzer or LiquidityAnalyzer(trading_service)
            self._liquidity_available = True
            logger.info(f"[{VERSION_BANNER}] LiquidityAnalyzer connected")
        except Exception as e:
            self.liquidity_analyzer = None
            self._liquidity_available = False
            logger.warning(f"[{VERSION_BANNER}] LiquidityAnalyzer not available: {e}")
        
        try:
            from .micro_volatility import MicroVolatilityEngine
            self.volatility_engine = volatility_engine or MicroVolatilityEngine()
            self._volatility_available = True
            logger.info(f"[{VERSION_BANNER}] MicroVolatilityEngine connected")
        except Exception as e:
            self.volatility_engine = None
            self._volatility_available = False
            logger.warning(f"[{VERSION_BANNER}] MicroVolatilityEngine not available: {e}")
        
        try:
            from .correlation_engine import CrossAssetCorrelationEngine
            self.correlation_engine = correlation_engine or CrossAssetCorrelationEngine()
            self._correlation_available = True
            logger.info(f"[{VERSION_BANNER}] CrossAssetCorrelationEngine connected")
        except Exception as e:
            self.correlation_engine = None
            self._correlation_available = False
            logger.warning(f"[{VERSION_BANNER}] CrossAssetCorrelationEngine not available: {e}")
        
        self._decision_cache: Dict[str, Tuple[ExecutionDecision, float]] = {}
        self._cache_ttl = 10.0
        
        logger.info(f"[{VERSION_BANNER}] ExecutionProtocol INSTITUTIONAL+ initialized")
        logger.info(f"   Liquidity: {'✅' if self._liquidity_available else '❌'}")
        logger.info(f"   Volatility: {'✅' if self._volatility_available else '❌'}")
        logger.info(f"   Correlation: {'✅' if self._correlation_available else '❌'}")
    
    def get_execution_decision(
        self,
        symbol: str,
        side: str,
        size_usd: float,
        urgency: ExecutionUrgency = ExecutionUrgency.NORMAL,
        force_refresh: bool = False
    ) -> ExecutionDecision:
        """
        Get complete execution recommendation.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USD')
            side: 'buy' or 'sell'
            size_usd: Order size in USD
            urgency: Trade urgency level
            force_refresh: Bypass cache
            
        Returns:
            ExecutionDecision with all recommendations
        """
        with self._lock:
            try:
                liquidity_data = self._get_liquidity_data(symbol)
                volatility_data = self._get_volatility_data(symbol)
                correlation_data = self._get_correlation_data()
                
                liquidity_available = liquidity_data.get('available', False)
                correlation_available = correlation_data.get('available', False)
                data_integrity_block = False
                block_reason = ""
                
                if not liquidity_available and not correlation_available:
                    data_integrity_block = True
                    block_reason = "CRITICAL: Both liquidity and correlation data unavailable - execution blocked for safety"
                    logger.warning(f"[{VERSION_BANNER}] 🛑 DATA INTEGRITY BLOCK: {block_reason}")
                elif not liquidity_available:
                    data_integrity_block = True
                    block_reason = "CRITICAL: Liquidity data unavailable - cannot assess execution risk"
                    logger.warning(f"[{VERSION_BANNER}] 🛑 DATA INTEGRITY BLOCK: {block_reason}")
                elif not correlation_available:
                    data_integrity_block = True
                    block_reason = "CRITICAL: Correlation/contagion data unavailable - cannot assess systemic risk"
                    logger.warning(f"[{VERSION_BANNER}] 🛑 DATA INTEGRITY BLOCK: {block_reason}")
                
                market_condition = self._assess_market_condition(
                    liquidity_data, volatility_data, correlation_data
                )
                
                slippage = self._predict_slippage(
                    symbol, side, size_usd, liquidity_data, volatility_data
                )
                
                timing = self._get_optimal_timing(
                    volatility_data, correlation_data, urgency
                )
                
                style, params = self._select_execution_style(
                    size_usd, urgency, market_condition, 
                    liquidity_data, volatility_data
                )
                
                warnings = self._generate_warnings(
                    slippage, market_condition, correlation_data, volatility_data
                )
                
                if data_integrity_block:
                    warnings.insert(0, f"🛑 BLOCKED: {block_reason}")
                
                confidence = self._calculate_confidence(
                    liquidity_data, volatility_data, correlation_data
                )
                
                decision = ExecutionDecision(
                    symbol=symbol,
                    side=side,
                    size_usd=size_usd,
                    recommended_style=style,
                    urgency=urgency,
                    market_condition=market_condition,
                    slippage=slippage,
                    timing=timing,
                    liquidity_score=liquidity_data.get('score', 50.0),
                    volatility_regime=volatility_data.get('regime', 'NORMAL'),
                    correlation_risk=correlation_data.get('correlation_risk', 0.0),
                    contagion_risk=correlation_data.get('contagion_risk', 0.0),
                    safe_haven_flow=correlation_data.get('safe_haven_flow', 'NEUTRAL'),
                    execution_params=params,
                    warnings=warnings,
                    confidence=confidence,
                    data_integrity_block=data_integrity_block,
                    block_reason=block_reason,
                    liquidity_data_available=liquidity_available,
                    correlation_data_available=correlation_available
                )
                
                if data_integrity_block:
                    logger.warning(
                        f"[{VERSION_BANNER}] 🛑 EXECUTION BLOCKED for {symbol} {side} ${size_usd:.0f}: "
                        f"{block_reason}"
                    )
                else:
                    logger.info(
                        f"[{VERSION_BANNER}] Execution decision for {symbol} {side} ${size_usd:.0f}: "
                        f"{style.value.upper()} | {market_condition.value} | "
                        f"Slippage: {slippage.expected_slippage_bps:.1f}bps"
                    )
                
                return decision
                
            except Exception as e:
                logger.error(f"[{VERSION_BANNER}] Error generating execution decision: {e}")
                return self._get_fallback_decision(symbol, side, size_usd, urgency)
    
    def get_pre_trade_analytics(self, symbol: str) -> PreTradeAnalytics:
        """
        Get comprehensive pre-trade analysis.
        
        Args:
            symbol: Trading pair
            
        Returns:
            PreTradeAnalytics with all metrics
        """
        with self._lock:
            liquidity_data = self._get_liquidity_data(symbol)
            volatility_data = self._get_volatility_data(symbol)
            correlation_data = self._get_correlation_data()
            
            market_condition = self._assess_market_condition(
                liquidity_data, volatility_data, correlation_data
            )
            
            overall_score = self._calculate_overall_score(
                liquidity_data, volatility_data, correlation_data
            )
            
            recommendations = self._generate_recommendations(
                liquidity_data, volatility_data, correlation_data, market_condition
            )
            
            return PreTradeAnalytics(
                symbol=symbol,
                timestamp=datetime.now(),
                liquidity_analysis=liquidity_data,
                volatility_state=volatility_data,
                correlation_state=correlation_data,
                market_condition=market_condition,
                overall_score=overall_score,
                recommendations=recommendations
            )
    
    def predict_slippage(
        self,
        symbol: str,
        side: str,
        size_usd: float
    ) -> SlippagePrediction:
        """
        Predict slippage for a potential trade.
        
        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            size_usd: Order size in USD
            
        Returns:
            SlippagePrediction with estimates
        """
        with self._lock:
            liquidity_data = self._get_liquidity_data(symbol)
            volatility_data = self._get_volatility_data(symbol)
            return self._predict_slippage(
                symbol, side, size_usd, liquidity_data, volatility_data
            )
    
    def _get_liquidity_data(self, symbol: str) -> Dict[str, Any]:
        """Get liquidity metrics from analyzer"""
        if not self._liquidity_available or not self.liquidity_analyzer:
            return {
                'score': 50.0,
                'depth_imbalance': 0.0,
                'tblr': 0.5,
                'hidden_liquidity_confidence': 'NONE',
                'available': False
            }
        
        try:
            analysis = self.liquidity_analyzer.analyze_liquidity(symbol)
            if analysis:
                return {
                    'score': getattr(analysis.depth, 'weighted_depth_score', 50.0) if analysis.depth else 50.0,
                    'depth_imbalance': analysis.snapshot.depth_imbalance_ratio if analysis.snapshot else 0.0,
                    'tblr': analysis.tblr.ratio if analysis.tblr else 0.5,
                    'hidden_liquidity_confidence': (
                        analysis.hidden_liquidity.confidence.value 
                        if analysis.hidden_liquidity else 'NONE'
                    ),
                    'grade': analysis.depth.grade if analysis.depth else 'C',
                    'available': True
                }
        except Exception as e:
            logger.warning(f"Error getting liquidity data: {e}")
        
        return {
            'score': 50.0,
            'depth_imbalance': 0.0,
            'tblr': 0.5,
            'hidden_liquidity_confidence': 'NONE',
            'available': False
        }
    
    def _get_volatility_data(self, symbol: str) -> Dict[str, Any]:
        """Get volatility metrics from engine"""
        if not self._volatility_available or not self.volatility_engine:
            return {
                'regime': 'NORMAL',
                'realized_vol': 0.02,
                'asymmetric_ratio': 1.0,
                'available': False
            }
        
        try:
            state = self.volatility_engine.get_volatility_state(symbol)
            if state:
                return {
                    'regime': state.regime.value if hasattr(state.regime, 'value') else str(state.regime),
                    'realized_vol': state.realized_volatility,
                    'asymmetric_ratio': (
                        state.asymmetric_metrics.asymmetric_ratio 
                        if state.asymmetric_metrics else 1.0
                    ),
                    'percentile': state.volatility_percentile,
                    'available': True
                }
        except Exception as e:
            logger.warning(f"Error getting volatility data: {e}")
        
        return {
            'regime': 'NORMAL',
            'realized_vol': 0.02,
            'asymmetric_ratio': 1.0,
            'available': False
        }
    
    def _get_correlation_data(self) -> Dict[str, Any]:
        """Get correlation metrics from engine"""
        if not self._correlation_available or not self.correlation_engine:
            return {
                'correlation_risk': 0.0,
                'contagion_risk': 0.0,
                'safe_haven_flow': 'NEUTRAL',
                'breakdown_count': 0,
                'available': False
            }
        
        try:
            state = self.correlation_engine.get_correlation_state()
            contagion = self.correlation_engine.get_contagion_risk()
            safe_haven = self.correlation_engine.get_safe_haven_flow()
            breakdowns = self.correlation_engine.detect_breakdown()
            
            return {
                'correlation_risk': contagion.risk_score if contagion else 0.0,
                'contagion_risk': contagion.risk_score if contagion else 0.0,
                'contagion_level': contagion.risk_level.value if contagion else 'LOW',
                'safe_haven_flow': (
                    safe_haven.flow_direction.value if safe_haven else 'NEUTRAL'
                ),
                'breakdown_count': len(breakdowns) if breakdowns else 0,
                'breakdowns': [b.to_dict() for b in breakdowns[:3]] if breakdowns else [],
                'available': True
            }
        except Exception as e:
            logger.warning(f"Error getting correlation data: {e}")
        
        return {
            'correlation_risk': 0.0,
            'contagion_risk': 0.0,
            'safe_haven_flow': 'NEUTRAL',
            'breakdown_count': 0,
            'available': False
        }
    
    def _assess_market_condition(
        self,
        liquidity: Dict,
        volatility: Dict,
        correlation: Dict
    ) -> MarketCondition:
        """Assess overall market condition"""
        crisis_indicators = 0
        adverse_indicators = 0
        
        if volatility.get('regime') == 'EXTREME':
            crisis_indicators += 1
        elif volatility.get('regime') == 'HIGH':
            adverse_indicators += 1
        
        if correlation.get('contagion_risk', 0) > 80:
            crisis_indicators += 1
        elif correlation.get('contagion_risk', 0) > 50:
            adverse_indicators += 1
        
        if liquidity.get('score', 50) < 20:
            crisis_indicators += 1
        elif liquidity.get('score', 50) < 40:
            adverse_indicators += 1
        
        if correlation.get('breakdown_count', 0) >= 3:
            adverse_indicators += 1
        
        if crisis_indicators >= 2:
            return MarketCondition.CRISIS
        elif crisis_indicators >= 1 or adverse_indicators >= 2:
            return MarketCondition.ADVERSE
        elif adverse_indicators >= 1:
            return MarketCondition.NEUTRAL
        else:
            return MarketCondition.FAVORABLE
    
    def _predict_slippage(
        self,
        symbol: str,
        side: str,
        size_usd: float,
        liquidity: Dict,
        volatility: Dict
    ) -> SlippagePrediction:
        """Predict execution slippage"""
        base_slippage = 5.0
        
        size_factor = 1.0
        if size_usd > self.SIZE_THRESHOLDS['whale']:
            size_factor = 3.0
        elif size_usd > self.SIZE_THRESHOLDS['institutional']:
            size_factor = 2.0
        elif size_usd > self.SIZE_THRESHOLDS['large']:
            size_factor = 1.5
        elif size_usd > self.SIZE_THRESHOLDS['medium']:
            size_factor = 1.2
        
        liquidity_factor = 1.0
        liq_score = liquidity.get('score', 50)
        if liq_score < 30:
            liquidity_factor = 2.0
        elif liq_score < 50:
            liquidity_factor = 1.5
        elif liq_score > 80:
            liquidity_factor = 0.7
        
        vol_factor = 1.0
        regime = volatility.get('regime', 'NORMAL')
        if regime == 'EXTREME':
            vol_factor = 3.0
        elif regime == 'HIGH':
            vol_factor = 1.8
        elif regime == 'LOW':
            vol_factor = 0.8
        
        imbalance_factor = 1.0
        imbalance = liquidity.get('depth_imbalance', 0)
        if (side == 'buy' and imbalance < -0.3) or (side == 'sell' and imbalance > 0.3):
            imbalance_factor = 1.5
        elif (side == 'buy' and imbalance > 0.3) or (side == 'sell' and imbalance < -0.3):
            imbalance_factor = 0.8
        
        expected = base_slippage * size_factor * liquidity_factor * vol_factor * imbalance_factor
        worst_case = expected * 2.5
        best_case = expected * 0.4
        
        confidence = 0.7
        if not liquidity.get('available'):
            confidence -= 0.2
        if not volatility.get('available'):
            confidence -= 0.2
        
        impact_by_size = {}
        for mult in [0.5, 1.0, 2.0, 5.0]:
            test_size = size_usd * mult
            test_factor = (test_size / size_usd) ** 0.7
            impact_by_size[test_size] = expected * test_factor
        
        return SlippagePrediction(
            expected_slippage_bps=expected,
            worst_case_slippage_bps=worst_case,
            best_case_slippage_bps=best_case,
            confidence=confidence,
            impact_by_size=impact_by_size,
            factors={
                'base': base_slippage,
                'size_factor': size_factor,
                'liquidity_factor': liquidity_factor,
                'volatility_factor': vol_factor,
                'imbalance_factor': imbalance_factor
            }
        )
    
    def _get_optimal_timing(
        self,
        volatility: Dict,
        correlation: Dict,
        urgency: ExecutionUrgency
    ) -> ExecutionTiming:
        """Determine optimal execution timing"""
        if urgency == ExecutionUrgency.CRITICAL:
            return ExecutionTiming(
                execute_now=True,
                delay_seconds=0,
                reason="Critical urgency - immediate execution",
                confidence=0.9
            )
        
        avoid_periods = []
        delay_seconds = 0
        reasons = []
        
        regime = volatility.get('regime', 'NORMAL')
        if regime == 'EXTREME':
            delay_seconds = max(delay_seconds, 300)
            reasons.append("Extreme volatility - wait for stabilization")
            avoid_periods.append("Current volatility spike")
        elif regime == 'HIGH':
            delay_seconds = max(delay_seconds, 60)
            reasons.append("High volatility - consider brief delay")
        
        if correlation.get('contagion_risk', 0) > 70:
            delay_seconds = max(delay_seconds, 180)
            reasons.append("High contagion risk - wait for normalization")
        
        if correlation.get('breakdown_count', 0) >= 2:
            delay_seconds = max(delay_seconds, 120)
            reasons.append("Multiple correlation breakdowns")
        
        if urgency == ExecutionUrgency.HIGH:
            delay_seconds = min(delay_seconds, 60)
        elif urgency == ExecutionUrgency.LOW:
            delay_seconds = max(delay_seconds, 60)
        
        execute_now = delay_seconds == 0
        reason = "; ".join(reasons) if reasons else "Conditions favorable for execution"
        
        return ExecutionTiming(
            execute_now=execute_now,
            delay_seconds=delay_seconds,
            reason=reason,
            avoid_periods=avoid_periods,
            confidence=0.7 if not execute_now else 0.85
        )
    
    def _select_execution_style(
        self,
        size_usd: float,
        urgency: ExecutionUrgency,
        market_condition: MarketCondition,
        liquidity: Dict,
        volatility: Dict
    ) -> Tuple[ExecutionStyle, Dict[str, Any]]:
        """Select optimal execution algorithm"""
        params = {}
        
        if urgency == ExecutionUrgency.CRITICAL:
            return ExecutionStyle.MARKET, {}
        
        if market_condition == MarketCondition.CRISIS:
            params['max_participation'] = 0.05
            return ExecutionStyle.POV, params
        
        if size_usd < self.SIZE_THRESHOLDS['small']:
            return ExecutionStyle.LIMIT, {'post_only': True}
        
        if size_usd > self.SIZE_THRESHOLDS['institutional']:
            if liquidity.get('hidden_liquidity_confidence') in ['HIGH', 'MEDIUM']:
                params['display_size_pct'] = 0.1
                params['refresh_rate'] = 'fast'
                return ExecutionStyle.ICEBERG, params
            else:
                params['duration_minutes'] = min(30, size_usd / 10000)
                params['participation_rate'] = 0.15
                return ExecutionStyle.TWAP, params
        
        if size_usd > self.SIZE_THRESHOLDS['large']:
            regime = volatility.get('regime', 'NORMAL')
            if regime in ['HIGH', 'EXTREME']:
                params['duration_minutes'] = 15
                return ExecutionStyle.TWAP, params
            else:
                params['duration_minutes'] = 10
                return ExecutionStyle.VWAP, params
        
        if size_usd > self.SIZE_THRESHOLDS['medium']:
            if liquidity.get('score', 50) > 70:
                return ExecutionStyle.LIMIT, {'post_only': True}
            else:
                params['display_size_pct'] = 0.3
                return ExecutionStyle.ICEBERG, params
        
        return ExecutionStyle.LIMIT, {'post_only': True}
    
    def _generate_warnings(
        self,
        slippage: SlippagePrediction,
        market_condition: MarketCondition,
        correlation: Dict,
        volatility: Dict
    ) -> List[str]:
        """Generate execution warnings"""
        warnings = []
        
        if slippage.expected_slippage_bps > 30:
            warnings.append(f"High expected slippage: {slippage.expected_slippage_bps:.1f}bps")
        
        if market_condition == MarketCondition.CRISIS:
            warnings.append("CRISIS CONDITIONS - Consider delaying non-urgent trades")
        elif market_condition == MarketCondition.ADVERSE:
            warnings.append("Adverse market conditions - Increased execution risk")
        
        if correlation.get('contagion_risk', 0) > 70:
            warnings.append(f"High contagion risk: {correlation['contagion_risk']:.0f}/100")
        
        if volatility.get('regime') == 'EXTREME':
            warnings.append("EXTREME volatility regime - Size appropriately")
        
        safe_haven = correlation.get('safe_haven_flow', 'NEUTRAL')
        if safe_haven == 'FLIGHT_TO_QUALITY':
            warnings.append("Flight to quality detected - Risk assets under pressure")
        
        return warnings
    
    def _calculate_confidence(
        self,
        liquidity: Dict,
        volatility: Dict,
        correlation: Dict
    ) -> float:
        """Calculate overall decision confidence"""
        confidence = 0.5
        
        if liquidity.get('available'):
            confidence += 0.15
        if volatility.get('available'):
            confidence += 0.15
        if correlation.get('available'):
            confidence += 0.15
        
        if liquidity.get('score', 50) > 70:
            confidence += 0.05
        
        return min(confidence, 0.95)
    
    def _calculate_overall_score(
        self,
        liquidity: Dict,
        volatility: Dict,
        correlation: Dict
    ) -> float:
        """Calculate overall market score (0-100)"""
        liquidity_score = liquidity.get('score', 50) * 0.4
        
        regime = volatility.get('regime', 'NORMAL')
        vol_scores = {'LOW': 90, 'NORMAL': 70, 'HIGH': 40, 'EXTREME': 10}
        vol_score = vol_scores.get(regime, 50) * 0.3
        
        contagion = correlation.get('contagion_risk', 0)
        corr_score = (100 - contagion) * 0.3
        
        return liquidity_score + vol_score + corr_score
    
    def _generate_recommendations(
        self,
        liquidity: Dict,
        volatility: Dict,
        correlation: Dict,
        market_condition: MarketCondition
    ) -> List[str]:
        """Generate trading recommendations"""
        recs = []
        
        if market_condition == MarketCondition.FAVORABLE:
            recs.append("Market conditions favorable for execution")
        elif market_condition == MarketCondition.CRISIS:
            recs.append("REDUCE exposure - Crisis conditions detected")
            recs.append("Use smaller position sizes")
            recs.append("Consider defensive hedges")
        elif market_condition == MarketCondition.ADVERSE:
            recs.append("Increase caution - Adverse conditions")
            recs.append("Use TWAP/VWAP for larger orders")
        
        if liquidity.get('hidden_liquidity_confidence') in ['HIGH', 'MEDIUM']:
            recs.append("Hidden liquidity detected - ICEBERG orders may be effective")
        
        regime = volatility.get('regime', 'NORMAL')
        if regime == 'EXTREME':
            recs.append("EXTREME volatility - Wait for stabilization or reduce size 50%")
        elif regime == 'HIGH':
            recs.append("High volatility - Consider splitting orders")
        
        safe_haven = correlation.get('safe_haven_flow', 'NEUTRAL')
        if safe_haven == 'FLIGHT_TO_QUALITY':
            recs.append("Flight to quality active - Favor BTC/stablecoins over alts")
        elif safe_haven == 'RISK_ON':
            recs.append("Risk-on sentiment - Alts may outperform")
        
        return recs
    
    def _get_fallback_decision(
        self,
        symbol: str,
        side: str,
        size_usd: float,
        urgency: ExecutionUrgency
    ) -> ExecutionDecision:
        """Get conservative fallback decision when engines unavailable"""
        return ExecutionDecision(
            symbol=symbol,
            side=side,
            size_usd=size_usd,
            recommended_style=ExecutionStyle.LIMIT,
            urgency=urgency,
            market_condition=MarketCondition.NEUTRAL,
            slippage=SlippagePrediction(
                expected_slippage_bps=20.0,
                worst_case_slippage_bps=50.0,
                best_case_slippage_bps=5.0,
                confidence=0.3
            ),
            timing=ExecutionTiming(
                execute_now=True,
                delay_seconds=0,
                reason="Fallback mode - Limited market data",
                confidence=0.3
            ),
            liquidity_score=50.0,
            volatility_regime='UNKNOWN',
            correlation_risk=0.0,
            contagion_risk=0.0,
            safe_haven_flow='UNKNOWN',
            warnings=["Limited market data - Using conservative estimates"],
            confidence=0.3
        )
    
    def health_check(self) -> Dict[str, bool]:
        """Check health of all components"""
        return {
            'liquidity_analyzer': self._liquidity_available,
            'volatility_engine': self._volatility_available,
            'correlation_engine': self._correlation_available,
            'operational': any([
                self._liquidity_available,
                self._volatility_available,
                self._correlation_available
            ])
        }
