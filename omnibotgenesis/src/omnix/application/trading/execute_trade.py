"""
OMNIX V7.0 Execute Trade Use Case
===================================
Application service for executing trades.

This use case orchestrates the complete trade execution flow:
1. Validate trade parameters
2. Check risk limits
3. Execute order via trading port
4. Persist trade record
5. Send notifications
"""

from dataclasses import dataclass
from typing import Optional, Protocol
from datetime import datetime

from src.omnix.domain.trading.entities import Trade, TradeDirection, TradeStatus
from src.omnix.domain.trading.value_objects import ConfidenceScore


class ITradingPort(Protocol):
    """Port for trade execution."""
    async def execute_order(
        self,
        pair: str,
        direction: TradeDirection,
        quantity: float,
        price: Optional[float] = None,
    ) -> Trade:
        ...


class IRiskPort(Protocol):
    """Port for risk checks."""
    async def can_trade(self, pair: str, quantity: float, direction: TradeDirection) -> tuple[bool, Optional[str]]:
        ...
    
    async def record_trade(self, trade: Trade) -> None:
        ...


class ITradeRepositoryPort(Protocol):
    """Port for trade persistence."""
    async def save(self, trade: Trade) -> None:
        ...


class INotificationPort(Protocol):
    """Port for notifications."""
    async def notify_trade_executed(self, trade: Trade) -> None:
        ...


@dataclass
class ExecuteTradeRequest:
    """Request to execute a trade."""
    pair: str
    direction: TradeDirection
    quantity: float
    strategy: str
    confidence: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    user_id: Optional[str] = None
    is_paper: bool = True


@dataclass
class ExecuteTradeResponse:
    """Response from trade execution."""
    success: bool
    trade: Optional[Trade] = None
    error: Optional[str] = None
    risk_blocked: bool = False


class ExecuteTradeUseCase:
    """
    Use case for executing a trade.
    
    Coordinates between trading, risk, persistence, and notification ports.
    """
    
    def __init__(
        self,
        trading_port: ITradingPort,
        risk_port: IRiskPort,
        trade_repository: ITradeRepositoryPort,
        notification_port: Optional[INotificationPort] = None,
    ):
        self._trading = trading_port
        self._risk = risk_port
        self._repository = trade_repository
        self._notifications = notification_port
    
    async def execute(self, request: ExecuteTradeRequest) -> ExecuteTradeResponse:
        """
        Execute a trade following the complete flow.
        
        Args:
            request: Trade execution parameters
            
        Returns:
            ExecuteTradeResponse with trade details or error
        """
        try:
            can_trade, risk_reason = await self._risk.can_trade(
                request.pair,
                request.quantity,
                request.direction,
            )
            
            if not can_trade:
                return ExecuteTradeResponse(
                    success=False,
                    error=f"Risk check failed: {risk_reason}",
                    risk_blocked=True,
                )
            
            trade = await self._trading.execute_order(
                pair=request.pair,
                direction=request.direction,
                quantity=request.quantity,
            )
            
            trade.strategy = request.strategy
            trade.confidence = request.confidence
            trade.stop_loss = request.stop_loss
            trade.take_profit = request.take_profit
            trade.user_id = request.user_id
            trade.is_paper = request.is_paper
            trade.status = TradeStatus.EXECUTED
            trade.executed_at = datetime.utcnow()
            
            await self._repository.save(trade)
            
            await self._risk.record_trade(trade)
            
            if self._notifications:
                try:
                    await self._notifications.notify_trade_executed(trade)
                except Exception:
                    pass
            
            return ExecuteTradeResponse(
                success=True,
                trade=trade,
            )
            
        except Exception as e:
            return ExecuteTradeResponse(
                success=False,
                error=str(e),
            )
