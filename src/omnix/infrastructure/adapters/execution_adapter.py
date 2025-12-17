"""
OMNIX V7.0 Execution Adapter
============================
Bridges V7 Hexagonal Architecture with Legacy Execution services.

ARCHITECTURE DECISION (Dec 17, 2025):
This adapter is a PURE BRIDGE that delegates to legacy services:
- ExecutionProtocol (main orchestrator)
- LiquidityAnalyzer (orderbook analysis)
- CorrelationEngine (cross-asset correlation)
- MicroVolatilityEngine (regime detection)

The adapter ONLY translates between:
- V7 ExecutionPort DTOs ↔ Legacy service responses

This follows the Strangler Fig pattern: new interface wraps legacy implementation.
Feature Flag: USE_EXECUTION_PORT
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from src.omnix.ports.driven.execution_port import (
    ExecutionPort,
    LiquidityReport,
    VolatilityMetrics,
    VolatilityRegime,
    CorrelationMatrix,
    ContagionLevel,
    SlippagePrediction,
    ExecutionTiming,
    ExecutionOrder,
    ExecutionResult,
    ExecutionStyle,
    ExecutionUrgency,
    MarketCondition,
)

logger = logging.getLogger(__name__)


class ExecutionAdapter:
    """
    Adapter that implements ExecutionPort.
    
    DELEGATES to legacy execution services for actual analysis.
    This ensures USE_EXECUTION_PORT=true uses the same proven services
    as the legacy system.
    
    Translation:
    - V7 DTOs ↔ Legacy service responses
    """
    
    def __init__(
        self,
        execution_protocol: Optional[Any] = None,
        liquidity_analyzer: Optional[Any] = None,
        correlation_engine: Optional[Any] = None,
        volatility_engine: Optional[Any] = None,
    ):
        """
        Initialize the Execution Adapter.
        
        Args:
            execution_protocol: Legacy ExecutionProtocol instance
            liquidity_analyzer: Legacy LiquidityAnalyzer instance
            correlation_engine: Legacy CorrelationEngine instance
            volatility_engine: Legacy MicroVolatilityEngine instance
        """
        self._execution_protocol = execution_protocol
        self._liquidity_analyzer = liquidity_analyzer
        self._correlation_engine = correlation_engine
        self._volatility_engine = volatility_engine
        
        self._request_count = 0
        self._error_count = 0
        self._last_request: Optional[datetime] = None
        self._initialized = False
    
    def _ensure_services(self) -> bool:
        """Lazy initialize services if not injected."""
        if self._initialized:
            return True
        
        try:
            if self._execution_protocol is None:
                from omnix_services.execution_service.execution_protocol import ExecutionProtocol
                self._execution_protocol = ExecutionProtocol()
                logger.info("ExecutionAdapter: Initialized ExecutionProtocol")
            
            if self._liquidity_analyzer is None:
                from omnix_services.execution_service.liquidity_analyzer import LiquidityAnalyzer
                self._liquidity_analyzer = LiquidityAnalyzer()
                logger.info("ExecutionAdapter: Initialized LiquidityAnalyzer")
            
            if self._correlation_engine is None:
                from omnix_services.execution_service.correlation_engine import CrossAssetCorrelationEngine
                self._correlation_engine = CrossAssetCorrelationEngine()
                logger.info("ExecutionAdapter: Initialized CorrelationEngine")
            
            if self._volatility_engine is None:
                from omnix_services.execution_service.micro_volatility import MicroVolatilityEngine
                self._volatility_engine = MicroVolatilityEngine()
                logger.info("ExecutionAdapter: Initialized MicroVolatilityEngine")
            
            self._initialized = True
            return True
            
        except Exception as e:
            logger.error(f"ExecutionAdapter: Failed to initialize services: {e}")
            return False
    
    def _map_volatility_regime(self, regime_str: str) -> VolatilityRegime:
        """Map string regime to VolatilityRegime enum."""
        mapping = {
            'low': VolatilityRegime.LOW,
            'normal': VolatilityRegime.NORMAL,
            'high': VolatilityRegime.HIGH,
            'extreme': VolatilityRegime.EXTREME,
        }
        return mapping.get(regime_str.lower(), VolatilityRegime.NORMAL)
    
    def _map_contagion_level(self, level_str: str) -> ContagionLevel:
        """Map string level to ContagionLevel enum."""
        mapping = {
            'low': ContagionLevel.LOW,
            'elevated': ContagionLevel.ELEVATED,
            'high': ContagionLevel.HIGH,
            'extreme': ContagionLevel.EXTREME,
        }
        return mapping.get(level_str.lower(), ContagionLevel.LOW)
    
    def _map_execution_style(self, style_str: str) -> ExecutionStyle:
        """Map string style to ExecutionStyle enum."""
        mapping = {
            'market': ExecutionStyle.MARKET,
            'limit': ExecutionStyle.LIMIT,
            'twap': ExecutionStyle.TWAP,
            'vwap': ExecutionStyle.VWAP,
            'iceberg': ExecutionStyle.ICEBERG,
            'pov': ExecutionStyle.POV,
            'is': ExecutionStyle.IMPLEMENTATION_SHORTFALL,
        }
        return mapping.get(style_str.lower(), ExecutionStyle.MARKET)
    
    def _map_market_condition(self, condition_str: str) -> MarketCondition:
        """Map string condition to MarketCondition enum."""
        mapping = {
            'favorable': MarketCondition.FAVORABLE,
            'neutral': MarketCondition.NEUTRAL,
            'adverse': MarketCondition.ADVERSE,
            'crisis': MarketCondition.CRISIS,
        }
        return mapping.get(condition_str.lower(), MarketCondition.NEUTRAL)
    
    def evaluate_liquidity(
        self,
        symbol: str,
        order_size_usd: Optional[float] = None
    ) -> LiquidityReport:
        """Analyze liquidity for a trading pair."""
        self._request_count += 1
        self._last_request = datetime.now()
        
        if not self._ensure_services():
            self._error_count += 1
            return LiquidityReport(
                symbol=symbol,
                liquidity_score=0.0,
                bid_depth_usd=0.0,
                ask_depth_usd=0.0,
                spread_bps=0.0,
                depth_imbalance=0.0,
                hidden_liquidity_detected=False,
                hidden_liquidity_confidence=0.0,
                tblr_ratio=0.0,
                optimal_order_size_usd=0.0,
            )
        
        try:
            analysis = self._liquidity_analyzer.analyze(symbol, order_size_usd)
            
            return LiquidityReport(
                symbol=symbol,
                liquidity_score=analysis.get('liquidity_score', 0.5),
                bid_depth_usd=analysis.get('bid_depth_usd', 0.0),
                ask_depth_usd=analysis.get('ask_depth_usd', 0.0),
                spread_bps=analysis.get('spread_bps', 0.0),
                depth_imbalance=analysis.get('depth_imbalance', 0.0),
                hidden_liquidity_detected=analysis.get('hidden_liquidity', False),
                hidden_liquidity_confidence=analysis.get('hidden_confidence', 0.0),
                tblr_ratio=analysis.get('tblr_ratio', 1.0),
                optimal_order_size_usd=analysis.get('optimal_size', order_size_usd or 1000.0),
                impact_estimates=analysis.get('impact_estimates', {}),
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"ExecutionAdapter: Error evaluating liquidity for {symbol}: {e}")
            self._error_count += 1
            return LiquidityReport(
                symbol=symbol,
                liquidity_score=0.5,
                bid_depth_usd=0.0,
                ask_depth_usd=0.0,
                spread_bps=0.0,
                depth_imbalance=0.0,
                hidden_liquidity_detected=False,
                hidden_liquidity_confidence=0.0,
                tblr_ratio=1.0,
                optimal_order_size_usd=order_size_usd or 1000.0,
            )
    
    def assess_correlation(
        self,
        pairs: List[str],
        window_hours: int = 24
    ) -> CorrelationMatrix:
        """Analyze cross-asset correlations and contagion risk."""
        self._request_count += 1
        self._last_request = datetime.now()
        
        if not self._ensure_services():
            self._error_count += 1
            return CorrelationMatrix(
                pairs=pairs,
                correlation_matrix={},
                breakdown_detected=False,
                breakdown_pairs=[],
                contagion_level=ContagionLevel.LOW,
                contagion_index=0.0,
                safe_haven_flow='neutral',
                btc_dominance_trend='stable',
            )
        
        try:
            analysis = self._correlation_engine.analyze_correlations(pairs, window_hours)
            
            contagion_level_str = analysis.get('contagion_level', 'low')
            if hasattr(contagion_level_str, 'label'):
                contagion_level_str = contagion_level_str.label
            
            return CorrelationMatrix(
                pairs=pairs,
                correlation_matrix=analysis.get('correlation_matrix', {}),
                breakdown_detected=analysis.get('breakdown_detected', False),
                breakdown_pairs=analysis.get('breakdown_pairs', []),
                contagion_level=self._map_contagion_level(str(contagion_level_str)),
                contagion_index=analysis.get('contagion_index', 0.0),
                safe_haven_flow=analysis.get('safe_haven_flow', 'neutral'),
                btc_dominance_trend=analysis.get('btc_dominance_trend', 'stable'),
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"ExecutionAdapter: Error assessing correlation: {e}")
            self._error_count += 1
            return CorrelationMatrix(
                pairs=pairs,
                correlation_matrix={},
                breakdown_detected=False,
                breakdown_pairs=[],
                contagion_level=ContagionLevel.LOW,
                contagion_index=0.0,
                safe_haven_flow='neutral',
                btc_dominance_trend='stable',
            )
    
    def compute_micro_volatility(
        self,
        symbol: str,
        window_minutes: int = 60
    ) -> VolatilityMetrics:
        """Compute micro-volatility regime metrics."""
        self._request_count += 1
        self._last_request = datetime.now()
        
        if not self._ensure_services():
            self._error_count += 1
            return VolatilityMetrics(
                symbol=symbol,
                regime=VolatilityRegime.NORMAL,
                current_volatility=0.0,
                volatility_percentile=50.0,
                asymmetric_response=0.0,
                regime_duration_hours=0.0,
                stability_score=0.5,
                predicted_direction='neutral',
                confidence=0.5,
            )
        
        try:
            analysis = self._volatility_engine.analyze(symbol, window_minutes)
            
            regime_str = analysis.get('regime', 'normal')
            if hasattr(regime_str, 'value'):
                regime_str = regime_str.value
            
            return VolatilityMetrics(
                symbol=symbol,
                regime=self._map_volatility_regime(str(regime_str)),
                current_volatility=analysis.get('current_volatility', 0.0),
                volatility_percentile=analysis.get('percentile', 50.0),
                asymmetric_response=analysis.get('asymmetric_response', 0.0),
                regime_duration_hours=analysis.get('regime_duration', 0.0),
                stability_score=analysis.get('stability_score', 0.5),
                predicted_direction=analysis.get('predicted_direction', 'neutral'),
                confidence=analysis.get('confidence', 0.5),
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"ExecutionAdapter: Error computing volatility for {symbol}: {e}")
            self._error_count += 1
            return VolatilityMetrics(
                symbol=symbol,
                regime=VolatilityRegime.NORMAL,
                current_volatility=0.0,
                volatility_percentile=50.0,
                asymmetric_response=0.0,
                regime_duration_hours=0.0,
                stability_score=0.5,
                predicted_direction='neutral',
                confidence=0.5,
            )
    
    def predict_slippage(
        self,
        symbol: str,
        side: str,
        size_usd: float
    ) -> SlippagePrediction:
        """Predict slippage for a potential trade."""
        self._request_count += 1
        self._last_request = datetime.now()
        
        if not self._ensure_services():
            self._error_count += 1
            return SlippagePrediction(
                expected_slippage_bps=0.0,
                worst_case_slippage_bps=0.0,
                best_case_slippage_bps=0.0,
                confidence=0.0,
            )
        
        try:
            prediction = self._execution_protocol.predict_slippage(symbol, side, size_usd)
            
            if hasattr(prediction, 'expected_slippage_bps'):
                return SlippagePrediction(
                    expected_slippage_bps=prediction.expected_slippage_bps,
                    worst_case_slippage_bps=prediction.worst_case_slippage_bps,
                    best_case_slippage_bps=prediction.best_case_slippage_bps,
                    confidence=prediction.confidence,
                    impact_by_size=getattr(prediction, 'impact_by_size', {}),
                    factors=getattr(prediction, 'factors', {}),
                )
            
            return SlippagePrediction(
                expected_slippage_bps=prediction.get('expected_slippage_bps', 0.0),
                worst_case_slippage_bps=prediction.get('worst_case_slippage_bps', 0.0),
                best_case_slippage_bps=prediction.get('best_case_slippage_bps', 0.0),
                confidence=prediction.get('confidence', 0.5),
                impact_by_size=prediction.get('impact_by_size', {}),
                factors=prediction.get('factors', {}),
            )
        except Exception as e:
            logger.error(f"ExecutionAdapter: Error predicting slippage: {e}")
            self._error_count += 1
            return SlippagePrediction(
                expected_slippage_bps=10.0,
                worst_case_slippage_bps=50.0,
                best_case_slippage_bps=5.0,
                confidence=0.3,
            )
    
    def get_optimal_timing(
        self,
        symbol: str,
        urgency: ExecutionUrgency = ExecutionUrgency.NORMAL
    ) -> ExecutionTiming:
        """Get optimal execution timing recommendation."""
        self._request_count += 1
        self._last_request = datetime.now()
        
        if not self._ensure_services():
            self._error_count += 1
            return ExecutionTiming(
                execute_now=True,
                delay_seconds=0,
                reason="Services unavailable - defaulting to immediate",
            )
        
        try:
            timing = self._execution_protocol.get_timing(symbol, urgency.value)
            
            if hasattr(timing, 'execute_now'):
                return ExecutionTiming(
                    execute_now=timing.execute_now,
                    delay_seconds=timing.delay_seconds,
                    reason=timing.reason,
                    optimal_window_start=getattr(timing, 'optimal_window_start', None),
                    optimal_window_end=getattr(timing, 'optimal_window_end', None),
                    avoid_periods=getattr(timing, 'avoid_periods', []),
                    confidence=getattr(timing, 'confidence', 0.5),
                )
            
            return ExecutionTiming(
                execute_now=timing.get('execute_now', True),
                delay_seconds=timing.get('delay_seconds', 0),
                reason=timing.get('reason', 'Analysis complete'),
                confidence=timing.get('confidence', 0.5),
            )
        except Exception as e:
            logger.error(f"ExecutionAdapter: Error getting timing: {e}")
            self._error_count += 1
            return ExecutionTiming(
                execute_now=True,
                delay_seconds=0,
                reason="Error in timing analysis - defaulting to immediate",
            )
    
    def route_execution(
        self,
        order: ExecutionOrder
    ) -> ExecutionResult:
        """Full execution analysis and routing recommendation."""
        self._request_count += 1
        self._last_request = datetime.now()
        
        liquidity = self.evaluate_liquidity(order.symbol, order.size_usd)
        volatility = self.compute_micro_volatility(order.symbol)
        slippage = self.predict_slippage(order.symbol, order.side, order.size_usd)
        timing = self.get_optimal_timing(order.symbol, order.urgency)
        
        if not self._ensure_services():
            self._error_count += 1
            return ExecutionResult(
                order=order,
                recommended_style=ExecutionStyle.LIMIT,
                market_condition=MarketCondition.NEUTRAL,
                liquidity=liquidity,
                volatility=volatility,
                slippage=slippage,
                timing=timing,
                correlation_risk=0.0,
                contagion_risk=0.0,
                proceed_recommended=False,
                warnings=["Execution services unavailable"],
                confidence=0.0,
            )
        
        try:
            decision = self._execution_protocol.analyze(
                symbol=order.symbol,
                side=order.side,
                size_usd=order.size_usd,
                urgency=order.urgency.value
            )
            
            style_str = getattr(decision, 'recommended_style', 'limit')
            if hasattr(style_str, 'value'):
                style_str = style_str.value
            
            condition_str = getattr(decision, 'market_condition', 'neutral')
            if hasattr(condition_str, 'value'):
                condition_str = condition_str.value
            
            warnings = []
            if not slippage.is_acceptable:
                warnings.append(f"High slippage expected: {slippage.expected_slippage_bps:.1f} bps")
            if not liquidity.is_liquid:
                warnings.append(f"Low liquidity: score {liquidity.liquidity_score:.2f}")
            if volatility.regime in [VolatilityRegime.HIGH, VolatilityRegime.EXTREME]:
                warnings.append(f"High volatility regime: {volatility.regime.value}")
            
            proceed = (
                slippage.is_acceptable and
                liquidity.is_liquid and
                volatility.regime not in [VolatilityRegime.EXTREME]
            )
            
            return ExecutionResult(
                order=order,
                recommended_style=self._map_execution_style(str(style_str)),
                market_condition=self._map_market_condition(str(condition_str)),
                liquidity=liquidity,
                volatility=volatility,
                slippage=slippage,
                timing=timing,
                correlation_risk=getattr(decision, 'correlation_risk', 0.0),
                contagion_risk=getattr(decision, 'contagion_risk', 0.0),
                proceed_recommended=proceed,
                warnings=warnings,
                suggested_splits=getattr(decision, 'suggested_splits', []),
                confidence=getattr(decision, 'confidence', 0.5),
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"ExecutionAdapter: Error routing execution: {e}")
            self._error_count += 1
            return ExecutionResult(
                order=order,
                recommended_style=ExecutionStyle.LIMIT,
                market_condition=MarketCondition.NEUTRAL,
                liquidity=liquidity,
                volatility=volatility,
                slippage=slippage,
                timing=timing,
                correlation_risk=0.0,
                contagion_risk=0.0,
                proceed_recommended=False,
                warnings=["Error in execution analysis"],
                confidence=0.0,
            )
    
    def get_market_condition(
        self,
        symbol: str
    ) -> MarketCondition:
        """Get current market condition assessment."""
        self._request_count += 1
        self._last_request = datetime.now()
        
        if not self._ensure_services():
            return MarketCondition.NEUTRAL
        
        try:
            condition = self._execution_protocol.assess_market_condition(symbol)
            if hasattr(condition, 'value'):
                condition = condition.value
            return self._map_market_condition(str(condition))
        except Exception as e:
            logger.error(f"ExecutionAdapter: Error getting market condition: {e}")
            return MarketCondition.NEUTRAL
    
    def get_execution_summary(
        self,
        symbol: str
    ) -> Dict[str, Any]:
        """Get quick execution summary for a symbol."""
        liquidity = self.evaluate_liquidity(symbol)
        volatility = self.compute_micro_volatility(symbol)
        
        return {
            'symbol': symbol,
            'liquidity_score': liquidity.liquidity_score,
            'is_liquid': liquidity.is_liquid,
            'spread_bps': liquidity.spread_bps,
            'volatility_regime': volatility.regime.value,
            'volatility_percentile': volatility.volatility_percentile,
            'recommended_max_size': liquidity.optimal_order_size_usd,
            'timestamp': datetime.now().isoformat(),
        }
    
    def is_execution_safe(
        self,
        symbol: str,
        size_usd: float
    ) -> Tuple[bool, str]:
        """Quick safety check for execution."""
        liquidity = self.evaluate_liquidity(symbol, size_usd)
        volatility = self.compute_micro_volatility(symbol)
        slippage = self.predict_slippage(symbol, 'buy', size_usd)
        
        if volatility.regime == VolatilityRegime.EXTREME:
            return False, "Extreme volatility regime - execution not recommended"
        
        if not liquidity.is_liquid:
            return False, f"Insufficient liquidity (score: {liquidity.liquidity_score:.2f})"
        
        if not slippage.is_acceptable:
            return False, f"Slippage too high ({slippage.expected_slippage_bps:.1f} bps)"
        
        if size_usd > liquidity.optimal_order_size_usd * 2:
            return False, f"Order size exceeds 2x optimal ({liquidity.optimal_order_size_usd:.0f} USD)"
        
        return True, "Execution conditions favorable"
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of execution services."""
        components = {}
        
        if self._ensure_services():
            components['execution_protocol'] = self._execution_protocol is not None
            components['liquidity_analyzer'] = self._liquidity_analyzer is not None
            components['correlation_engine'] = self._correlation_engine is not None
            components['volatility_engine'] = self._volatility_engine is not None
        
        healthy = all(components.values()) if components else False
        
        return {
            'healthy': healthy,
            'adapter': 'ExecutionAdapter',
            'components': components,
            'request_count': self._request_count,
            'error_count': self._error_count,
            'last_request': self._last_request.isoformat() if self._last_request else None,
            'symbols_tracked': 0,
        }
