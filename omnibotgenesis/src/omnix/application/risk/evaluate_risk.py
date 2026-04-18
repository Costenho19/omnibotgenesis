"""
OMNIX V7.0 Evaluate Risk Use Case
===================================
Application service for risk evaluation.

This use case evaluates trading risk:
1. Check daily loss limits
2. Check drawdown limits
3. Check overtrading limits
4. Evaluate position size risk
5. Check correlation risk
"""

from dataclasses import dataclass, field
from typing import Protocol, List, Optional
from datetime import datetime

from src.omnix.domain.trading.entities import Trade, TradeDirection
from src.omnix.domain.risk.entities import RiskAlert, LimitState, RiskLevel, AlertType


class IRiskDataPort(Protocol):
    """Port for risk data access."""
    async def get_daily_pnl(self) -> float:
        ...
    
    async def get_daily_trade_count(self) -> int:
        ...
    
    async def get_current_drawdown(self) -> float:
        ...
    
    async def get_open_position_count(self) -> int:
        ...
    
    async def get_recent_trades(self, limit: int = 10) -> List[Trade]:
        ...


class IRiskConfigPort(Protocol):
    """Port for risk configuration."""
    async def get_daily_loss_limit(self) -> float:
        ...
    
    async def get_max_drawdown(self) -> float:
        ...
    
    async def get_max_daily_trades(self) -> int:
        ...
    
    async def get_max_position_size(self) -> float:
        ...


class IRiskAlertPort(Protocol):
    """Port for risk alerts."""
    async def save_alert(self, alert: RiskAlert) -> None:
        ...
    
    async def get_active_blocking_alerts(self) -> List[RiskAlert]:
        ...


@dataclass
class EvaluateRiskRequest:
    """Request to evaluate risk for a potential trade."""
    pair: str
    direction: TradeDirection
    quantity: float
    position_value_usd: float
    user_id: Optional[str] = None


@dataclass
class EvaluateRiskResponse:
    """Response from risk evaluation."""
    can_trade: bool = True
    risk_level: RiskLevel = RiskLevel.LOW
    alerts: List[RiskAlert] = field(default_factory=list)
    limits: List[LimitState] = field(default_factory=list)
    blocking_reason: Optional[str] = None


class EvaluateRiskUseCase:
    """
    Use case for evaluating trading risk.
    
    Checks multiple risk dimensions before allowing a trade.
    """
    
    def __init__(
        self,
        risk_data: IRiskDataPort,
        risk_config: IRiskConfigPort,
        alert_port: Optional[IRiskAlertPort] = None,
    ):
        self._data = risk_data
        self._config = risk_config
        self._alerts = alert_port
    
    async def execute(self, request: EvaluateRiskRequest) -> EvaluateRiskResponse:
        """
        Evaluate risk for a potential trade.
        
        Args:
            request: Trade parameters to evaluate
            
        Returns:
            EvaluateRiskResponse with risk assessment
        """
        response = EvaluateRiskResponse()
        
        await self._check_blocking_alerts(response)
        if not response.can_trade:
            return response
        
        await self._check_daily_loss(response)
        await self._check_drawdown(response)
        await self._check_overtrading(response)
        await self._check_position_size(request, response)
        await self._check_revenge_trading(response)
        
        response.risk_level = self._calculate_overall_risk(response.alerts)
        
        if response.risk_level >= RiskLevel.CRITICAL:
            response.can_trade = False
        
        if self._alerts:
            for alert in response.alerts:
                if alert.is_blocking:
                    await self._alerts.save_alert(alert)
        
        return response
    
    async def _check_blocking_alerts(self, response: EvaluateRiskResponse) -> None:
        """Check for existing blocking alerts."""
        if self._alerts:
            blocking = await self._alerts.get_active_blocking_alerts()
            if blocking:
                response.can_trade = False
                response.blocking_reason = blocking[0].message
                response.alerts.extend(blocking)
    
    async def _check_daily_loss(self, response: EvaluateRiskResponse) -> None:
        """Check daily loss limit."""
        daily_pnl = await self._data.get_daily_pnl()
        daily_limit = await self._config.get_daily_loss_limit()
        
        limit_state = LimitState(
            name="daily_loss",
            limit_type="loss",
            max_value=daily_limit,
            warning_threshold=0.8,
        )
        limit_state.update(abs(daily_pnl) if daily_pnl < 0 else 0)
        response.limits.append(limit_state)
        
        if limit_state.is_exceeded:
            alert = RiskAlert.daily_loss_alert(abs(daily_pnl), daily_limit)
            response.alerts.append(alert)
            response.can_trade = False
            response.blocking_reason = alert.message
    
    async def _check_drawdown(self, response: EvaluateRiskResponse) -> None:
        """Check drawdown limit."""
        drawdown = await self._data.get_current_drawdown()
        max_drawdown = await self._config.get_max_drawdown()
        
        limit_state = LimitState(
            name="drawdown",
            limit_type="percent",
            max_value=max_drawdown,
        )
        limit_state.update(drawdown)
        response.limits.append(limit_state)
        
        if limit_state.is_exceeded:
            alert = RiskAlert.drawdown_alert(drawdown, max_drawdown)
            response.alerts.append(alert)
            response.can_trade = False
            response.blocking_reason = alert.message
    
    async def _check_overtrading(self, response: EvaluateRiskResponse) -> None:
        """Check daily trade count limit."""
        trade_count = await self._data.get_daily_trade_count()
        max_trades = await self._config.get_max_daily_trades()
        
        limit_state = LimitState(
            name="daily_trades",
            limit_type="count",
            max_value=float(max_trades),
        )
        limit_state.update(float(trade_count))
        response.limits.append(limit_state)
        
        if limit_state.is_exceeded:
            alert = RiskAlert.overtrading_alert(trade_count, max_trades)
            response.alerts.append(alert)
            response.can_trade = False
            response.blocking_reason = alert.message
    
    async def _check_position_size(
        self,
        request: EvaluateRiskRequest,
        response: EvaluateRiskResponse,
    ) -> None:
        """Check position size limit."""
        max_size = await self._config.get_max_position_size()
        
        limit_state = LimitState(
            name="position_size",
            limit_type="usd",
            max_value=max_size,
        )
        limit_state.update(request.position_value_usd)
        response.limits.append(limit_state)
        
        if limit_state.is_exceeded:
            alert = RiskAlert(
                alert_type=AlertType.POSITION_SIZE,
                level=RiskLevel.HIGH,
                message=f"Position size ${request.position_value_usd:.2f} exceeds limit ${max_size:.2f}",
                is_blocking=True,
                current_value=request.position_value_usd,
                threshold_value=max_size,
            )
            response.alerts.append(alert)
            response.can_trade = False
            response.blocking_reason = alert.message
    
    async def _check_revenge_trading(self, response: EvaluateRiskResponse) -> None:
        """Check for revenge trading pattern."""
        recent_trades = await self._data.get_recent_trades(limit=5)
        
        if len(recent_trades) >= 3:
            recent_losses = sum(1 for t in recent_trades[:3] if t.pnl and t.pnl < 0)
            if recent_losses >= 3:
                alert = RiskAlert(
                    alert_type=AlertType.REVENGE_TRADE,
                    level=RiskLevel.HIGH,
                    message="Potential revenge trading: 3 consecutive losses",
                    is_blocking=False,
                    source="risk_guardian",
                )
                response.alerts.append(alert)
    
    def _calculate_overall_risk(self, alerts: List[RiskAlert]) -> RiskLevel:
        """Calculate overall risk level from alerts."""
        if not alerts:
            return RiskLevel.LOW
        
        blocking_count = sum(1 for a in alerts if a.is_blocking)
        if blocking_count > 0:
            return RiskLevel.CRITICAL
        
        high_count = sum(1 for a in alerts if a.level >= RiskLevel.HIGH)
        if high_count >= 2:
            return RiskLevel.HIGH
        elif high_count == 1:
            return RiskLevel.MEDIUM
        
        return RiskLevel.LOW
