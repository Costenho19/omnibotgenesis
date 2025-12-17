"""
OMNIX V7.0 - RiskControlAdapter
================================
Adapter implementing RiskControlPort by wrapping legacy risk services.

Wrapped Legacy Services:
- CircuitBreakerManager (omnix_core/risk/)
- LimitsEngine (omnix_services/risk/)
- PositionMonitor (omnix_core/portfolio/)
- AlertDispatcher (omnix_services/notifications/)

Feature flag: USE_RISK_CONTROL_PORT
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid

from src.omnix.ports.driven.risk_control_port import (
    RiskControlPort,
    RiskAssessmentRequest,
    RiskDecision,
    RiskLevel,
    CircuitBreakEvent,
    CircuitBreakerState,
    LimitStatus,
    LimitType,
    PositionRisk,
    PortfolioRiskSummary,
    Alert,
    AlertPriority,
)

logger = logging.getLogger(__name__)


class RiskControlAdapter:
    """
    Adapter wrapping legacy risk control services.
    
    Implements RiskControlPort protocol with lazy loading
    and graceful degradation.
    """
    
    def __init__(
        self,
        circuit_breaker: Any = None,
        limits_engine: Any = None,
        position_monitor: Any = None,
        alert_dispatcher: Any = None
    ):
        self._circuit_breaker = circuit_breaker
        self._limits_engine = limits_engine
        self._position_monitor = position_monitor
        self._alert_dispatcher = alert_dispatcher
        self._initialized = False
        self._alerts_cache: List[Alert] = []
        logger.info("RiskControlAdapter: Initialized with lazy-loaded services")
    
    def _ensure_services(self) -> None:
        """Lazy load services if not initialized."""
        if self._initialized:
            return
        
        if self._circuit_breaker is None:
            try:
                from omnix_core.risk.circuit_breaker_manager import CircuitBreakerManager
                self._circuit_breaker = CircuitBreakerManager()
            except ImportError:
                logger.warning("RiskControlAdapter: CircuitBreakerManager not available")
        
        if self._limits_engine is None:
            try:
                from omnix_services.risk.limits_engine import LimitsEngine
                self._limits_engine = LimitsEngine()
            except ImportError:
                logger.warning("RiskControlAdapter: LimitsEngine not available")
        
        if self._position_monitor is None:
            try:
                from omnix_core.portfolio.position_monitor import PositionMonitor
                self._position_monitor = PositionMonitor()
            except ImportError:
                logger.warning("RiskControlAdapter: PositionMonitor not available")
        
        if self._alert_dispatcher is None:
            try:
                from omnix_services.notifications.alert_dispatcher import AlertDispatcher
                self._alert_dispatcher = AlertDispatcher()
            except ImportError:
                logger.warning("RiskControlAdapter: AlertDispatcher not available")
        
        self._initialized = True
    
    def _map_risk_level(self, score: float) -> RiskLevel:
        """Map risk score to RiskLevel enum."""
        if score < 10:
            return RiskLevel.MINIMAL
        elif score < 25:
            return RiskLevel.LOW
        elif score < 50:
            return RiskLevel.MODERATE
        elif score < 75:
            return RiskLevel.HIGH
        elif score < 90:
            return RiskLevel.CRITICAL
        return RiskLevel.EXTREME
    
    def _map_circuit_state(self, state: str) -> CircuitBreakerState:
        """Map string state to CircuitBreakerState enum."""
        state_lower = state.lower()
        if state_lower == "open":
            return CircuitBreakerState.OPEN
        elif state_lower == "half_open" or state_lower == "half-open":
            return CircuitBreakerState.HALF_OPEN
        return CircuitBreakerState.CLOSED
    
    def _map_limit_type(self, type_str: str) -> LimitType:
        """Map string to LimitType enum."""
        type_lower = type_str.lower()
        mapping = {
            "position_size": LimitType.POSITION_SIZE,
            "daily_loss": LimitType.DAILY_LOSS,
            "drawdown": LimitType.DRAWDOWN,
            "leverage": LimitType.LEVERAGE,
            "concentration": LimitType.CONCENTRATION,
            "correlation": LimitType.CORRELATION,
        }
        return mapping.get(type_lower, LimitType.POSITION_SIZE)
    
    def _map_alert_priority(self, priority: str) -> AlertPriority:
        """Map string to AlertPriority enum."""
        priority_lower = priority.lower()
        mapping = {
            "debug": AlertPriority.DEBUG,
            "info": AlertPriority.INFO,
            "warning": AlertPriority.WARNING,
            "error": AlertPriority.ERROR,
            "critical": AlertPriority.CRITICAL,
        }
        return mapping.get(priority_lower, AlertPriority.INFO)
    
    def assess_trade_risk(
        self,
        request: RiskAssessmentRequest
    ) -> RiskDecision:
        """Assess risk for a proposed trade."""
        self._ensure_services()
        
        try:
            if self._limits_engine and hasattr(self._limits_engine, 'assess_trade'):
                result = self._limits_engine.assess_trade(
                    symbol=request.symbol,
                    side=request.side,
                    size_usd=request.size_usd,
                    entry_price=request.entry_price,
                    stop_loss=request.stop_loss
                )
                
                if isinstance(result, dict):
                    score = result.get('risk_score', 50.0)
                    return RiskDecision(
                        approved=result.get('approved', True),
                        risk_level=self._map_risk_level(score),
                        score=score,
                        reasons=result.get('reasons', []),
                        warnings=result.get('warnings', []),
                        adjustments=result.get('adjustments', {}),
                        max_allowed_size=result.get('max_size'),
                        recommended_stop_loss=result.get('recommended_stop'),
                        veto_source=result.get('veto_source')
                    )
        except Exception as e:
            logger.error(f"RiskControlAdapter: assess_trade_risk error: {e}")
        
        return RiskDecision(
            approved=True,
            risk_level=RiskLevel.MODERATE,
            score=50.0,
            reasons=["Fallback assessment - no legacy service"],
            warnings=["Risk engine unavailable, using conservative defaults"]
        )
    
    def get_circuit_breaker_status(
        self,
        breaker_id: Optional[str] = None
    ) -> List[CircuitBreakEvent]:
        """Get circuit breaker status."""
        self._ensure_services()
        
        try:
            if self._circuit_breaker and hasattr(self._circuit_breaker, 'get_status'):
                result = self._circuit_breaker.get_status(breaker_id)
                
                if isinstance(result, list):
                    events = []
                    for item in result:
                        events.append(CircuitBreakEvent(
                            breaker_id=item.get('id', 'unknown'),
                            state=self._map_circuit_state(item.get('state', 'closed')),
                            trigger_reason=item.get('reason', ''),
                            triggered_at=item.get('triggered_at', datetime.now()),
                            auto_recovery_at=item.get('recovery_at'),
                            affected_symbols=item.get('symbols', []),
                            metrics_at_trigger=item.get('metrics', {})
                        ))
                    return events
        except Exception as e:
            logger.error(f"RiskControlAdapter: get_circuit_breaker_status error: {e}")
        
        return []
    
    def trip_circuit_breaker(
        self,
        breaker_id: str,
        reason: str,
        duration_minutes: int = 60
    ) -> CircuitBreakEvent:
        """Manually trip a circuit breaker."""
        self._ensure_services()
        
        now = datetime.now()
        
        try:
            if self._circuit_breaker and hasattr(self._circuit_breaker, 'trip'):
                self._circuit_breaker.trip(breaker_id, reason, duration_minutes)
        except Exception as e:
            logger.error(f"RiskControlAdapter: trip_circuit_breaker error: {e}")
        
        return CircuitBreakEvent(
            breaker_id=breaker_id,
            state=CircuitBreakerState.OPEN,
            trigger_reason=reason,
            triggered_at=now,
            auto_recovery_at=now + timedelta(minutes=duration_minutes)
        )
    
    def reset_circuit_breaker(
        self,
        breaker_id: str
    ) -> bool:
        """Reset a circuit breaker to closed state."""
        self._ensure_services()
        
        try:
            if self._circuit_breaker and hasattr(self._circuit_breaker, 'reset'):
                return self._circuit_breaker.reset(breaker_id)
        except Exception as e:
            logger.error(f"RiskControlAdapter: reset_circuit_breaker error: {e}")
        
        return False
    
    def get_limit_status(
        self,
        limit_type: Optional[LimitType] = None
    ) -> List[LimitStatus]:
        """Get current status of trading limits."""
        self._ensure_services()
        
        try:
            if self._limits_engine and hasattr(self._limits_engine, 'get_limits'):
                type_str = limit_type.value if limit_type else None
                result = self._limits_engine.get_limits(type_str)
                
                if isinstance(result, list):
                    statuses = []
                    for item in result:
                        statuses.append(LimitStatus(
                            limit_type=self._map_limit_type(item.get('type', 'position_size')),
                            limit_value=item.get('limit', 0),
                            current_value=item.get('current', 0),
                            utilization_pct=item.get('utilization', 0),
                            is_breached=item.get('breached', False),
                            headroom=item.get('headroom', 0)
                        ))
                    return statuses
        except Exception as e:
            logger.error(f"RiskControlAdapter: get_limit_status error: {e}")
        
        return [
            LimitStatus(
                limit_type=LimitType.POSITION_SIZE,
                limit_value=50000,
                current_value=0,
                utilization_pct=0,
                is_breached=False,
                headroom=50000
            )
        ]
    
    def check_limits(
        self,
        symbol: str,
        side: str,
        size_usd: float
    ) -> tuple[bool, List[str]]:
        """Check if a trade would breach any limits."""
        self._ensure_services()
        
        try:
            if self._limits_engine and hasattr(self._limits_engine, 'check'):
                result = self._limits_engine.check(symbol, side, size_usd)
                if isinstance(result, tuple):
                    return result
                if isinstance(result, dict):
                    return result.get('within_limits', True), result.get('breaches', [])
        except Exception as e:
            logger.error(f"RiskControlAdapter: check_limits error: {e}")
        
        return True, []
    
    def get_position_risks(
        self,
        symbols: Optional[List[str]] = None
    ) -> List[PositionRisk]:
        """Get risk metrics for open positions."""
        self._ensure_services()
        
        try:
            if self._position_monitor and hasattr(self._position_monitor, 'get_risks'):
                result = self._position_monitor.get_risks(symbols)
                
                if isinstance(result, list):
                    risks = []
                    for item in result:
                        risks.append(PositionRisk(
                            symbol=item.get('symbol', ''),
                            side=item.get('side', 'long'),
                            size_usd=item.get('size_usd', 0),
                            unrealized_pnl=item.get('unrealized_pnl', 0),
                            unrealized_pnl_pct=item.get('unrealized_pnl_pct', 0),
                            risk_score=item.get('risk_score', 0),
                            distance_to_stop_pct=item.get('stop_distance_pct'),
                            time_in_position_hours=item.get('hours_held', 0),
                            correlation_risk=item.get('correlation_risk', 0),
                            liquidity_risk=item.get('liquidity_risk', 0)
                        ))
                    return risks
        except Exception as e:
            logger.error(f"RiskControlAdapter: get_position_risks error: {e}")
        
        return []
    
    def get_portfolio_risk_summary(self) -> PortfolioRiskSummary:
        """Get portfolio-level risk summary."""
        self._ensure_services()
        
        try:
            if self._position_monitor and hasattr(self._position_monitor, 'get_summary'):
                result = self._position_monitor.get_summary()
                
                if isinstance(result, dict):
                    return PortfolioRiskSummary(
                        total_exposure_usd=result.get('total_exposure', 0),
                        net_exposure_usd=result.get('net_exposure', 0),
                        gross_exposure_usd=result.get('gross_exposure', 0),
                        position_count=result.get('positions', 0),
                        long_count=result.get('long_count', 0),
                        short_count=result.get('short_count', 0),
                        total_unrealized_pnl=result.get('unrealized_pnl', 0),
                        max_single_position_pct=result.get('max_position_pct', 0),
                        concentration_score=result.get('concentration', 0),
                        correlation_risk_score=result.get('correlation_risk', 0),
                        overall_risk_level=self._map_risk_level(result.get('risk_score', 25)),
                        warnings=result.get('warnings', [])
                    )
        except Exception as e:
            logger.error(f"RiskControlAdapter: get_portfolio_risk_summary error: {e}")
        
        return PortfolioRiskSummary(
            total_exposure_usd=0,
            net_exposure_usd=0,
            gross_exposure_usd=0,
            position_count=0,
            long_count=0,
            short_count=0,
            total_unrealized_pnl=0,
            max_single_position_pct=0,
            concentration_score=0,
            correlation_risk_score=0,
            overall_risk_level=RiskLevel.MINIMAL
        )
    
    def dispatch_alert(
        self,
        priority: AlertPriority,
        category: str,
        title: str,
        message: str,
        symbol: Optional[str] = None,
        action_required: bool = False
    ) -> Alert:
        """Dispatch a risk alert."""
        self._ensure_services()
        
        alert_id = str(uuid.uuid4())[:8]
        now = datetime.now()
        
        alert = Alert(
            alert_id=alert_id,
            priority=priority,
            category=category,
            title=title,
            message=message,
            created_at=now,
            related_symbol=symbol,
            action_required=action_required
        )
        
        try:
            if self._alert_dispatcher and hasattr(self._alert_dispatcher, 'dispatch'):
                self._alert_dispatcher.dispatch(
                    priority=priority.value,
                    category=category,
                    title=title,
                    message=message,
                    symbol=symbol
                )
        except Exception as e:
            logger.error(f"RiskControlAdapter: dispatch_alert error: {e}")
        
        self._alerts_cache.append(alert)
        if len(self._alerts_cache) > 100:
            self._alerts_cache = self._alerts_cache[-50:]
        
        return alert
    
    def get_recent_alerts(
        self,
        hours: int = 24,
        priority: Optional[AlertPriority] = None
    ) -> List[Alert]:
        """Get recent alerts."""
        self._ensure_services()
        
        cutoff = datetime.now() - timedelta(hours=hours)
        
        try:
            if self._alert_dispatcher and hasattr(self._alert_dispatcher, 'get_alerts'):
                result = self._alert_dispatcher.get_alerts(hours, priority.value if priority else None)
                if isinstance(result, list):
                    alerts = []
                    for item in result:
                        alerts.append(Alert(
                            alert_id=item.get('id', ''),
                            priority=self._map_alert_priority(item.get('priority', 'info')),
                            category=item.get('category', ''),
                            title=item.get('title', ''),
                            message=item.get('message', ''),
                            created_at=item.get('created_at', datetime.now()),
                            acknowledged=item.get('acknowledged', False),
                            related_symbol=item.get('symbol'),
                            action_required=item.get('action_required', False)
                        ))
                    return alerts
        except Exception as e:
            logger.error(f"RiskControlAdapter: get_recent_alerts error: {e}")
        
        filtered = [a for a in self._alerts_cache if a.created_at > cutoff]
        if priority:
            filtered = [a for a in filtered if a.priority == priority]
        return filtered
    
    def acknowledge_alert(
        self,
        alert_id: str
    ) -> bool:
        """Acknowledge an alert."""
        self._ensure_services()
        
        try:
            if self._alert_dispatcher and hasattr(self._alert_dispatcher, 'acknowledge'):
                return self._alert_dispatcher.acknowledge(alert_id)
        except Exception as e:
            logger.error(f"RiskControlAdapter: acknowledge_alert error: {e}")
        
        for alert in self._alerts_cache:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                alert.acknowledged_at = datetime.now()
                return True
        
        return False
    
    def is_trading_allowed(self) -> tuple[bool, str]:
        """Check if trading is currently allowed."""
        self._ensure_services()
        
        try:
            breakers = self.get_circuit_breaker_status()
            for breaker in breakers:
                if breaker.is_active:
                    return False, f"Circuit breaker {breaker.breaker_id} is open: {breaker.trigger_reason}"
            
            limits = self.get_limit_status()
            for limit in limits:
                if limit.is_breached:
                    return False, f"Limit breached: {limit.limit_type.value}"
        except Exception as e:
            logger.error(f"RiskControlAdapter: is_trading_allowed error: {e}")
        
        return True, "Trading allowed"
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of risk control components."""
        self._ensure_services()
        
        components = {
            'circuit_breaker': self._circuit_breaker is not None,
            'limits_engine': self._limits_engine is not None,
            'position_monitor': self._position_monitor is not None,
            'alert_dispatcher': self._alert_dispatcher is not None,
        }
        
        healthy_count = sum(1 for v in components.values() if v)
        
        return {
            'healthy': healthy_count >= 2,
            'adapter': 'RiskControlAdapter',
            'components': components,
            'healthy_count': healthy_count,
            'total_components': len(components),
            'alerts_cached': len(self._alerts_cache),
            'timestamp': datetime.now().isoformat()
        }
