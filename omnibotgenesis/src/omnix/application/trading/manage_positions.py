"""
OMNIX V7.0 Manage Positions Use Case
======================================
Application service for position management.

This use case handles:
1. List open positions
2. Update position stop-loss/take-profit
3. Close positions
4. Calculate aggregate exposure
"""

from dataclasses import dataclass, field
from typing import Protocol, List, Optional, Dict
from datetime import datetime

from src.omnix.domain.trading.entities import Position, Trade, TradeDirection, TradeStatus


class IPositionRepositoryPort(Protocol):
    """Port for position persistence."""
    async def get_open_positions(self, user_id: Optional[str] = None) -> List[Position]:
        ...
    
    async def get_position(self, position_id: str) -> Optional[Position]:
        ...
    
    async def save_position(self, position: Position) -> None:
        ...
    
    async def close_position(self, position_id: str, exit_price: float) -> Optional[Position]:
        ...


class IMarketDataPort(Protocol):
    """Port for market data access."""
    async def get_current_price(self, pair: str) -> float:
        ...


class ITradingPort(Protocol):
    """Port for trade execution."""
    async def close_position(self, position_id: str, price: Optional[float] = None) -> Trade:
        ...


@dataclass
class ManagePositionsRequest:
    """Request for position management operations."""
    operation: str  # "list", "close", "update_sl_tp"
    user_id: Optional[str] = None
    position_id: Optional[str] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


@dataclass
class PositionSummary:
    """Summary of a position with current market data."""
    position: Position
    current_price: float
    unrealized_pnl: float
    pnl_percentage: float


@dataclass
class ManagePositionsResponse:
    """Response from position management operations."""
    success: bool = True
    positions: List[PositionSummary] = field(default_factory=list)
    closed_position: Optional[Position] = None
    total_exposure_usd: float = 0.0
    total_unrealized_pnl: float = 0.0
    error: Optional[str] = None


class ManagePositionsUseCase:
    """
    Use case for managing trading positions.
    
    Provides operations for listing, updating, and closing positions.
    """
    
    def __init__(
        self,
        position_repository: IPositionRepositoryPort,
        market_data: IMarketDataPort,
        trading_port: Optional[ITradingPort] = None,
    ):
        self._repository = position_repository
        self._market_data = market_data
        self._trading = trading_port
    
    async def execute(self, request: ManagePositionsRequest) -> ManagePositionsResponse:
        """
        Execute position management operation.
        
        Args:
            request: Operation parameters
            
        Returns:
            ManagePositionsResponse with results
        """
        try:
            if request.operation == "list":
                return await self._list_positions(request.user_id)
            elif request.operation == "close":
                return await self._close_position(request.position_id)
            elif request.operation == "update_sl_tp":
                return await self._update_sl_tp(
                    request.position_id,
                    request.stop_loss,
                    request.take_profit,
                )
            else:
                return ManagePositionsResponse(
                    success=False,
                    error=f"Unknown operation: {request.operation}",
                )
        except Exception as e:
            return ManagePositionsResponse(
                success=False,
                error=str(e),
            )
    
    async def _list_positions(self, user_id: Optional[str]) -> ManagePositionsResponse:
        """List all open positions with current market data."""
        positions = await self._repository.get_open_positions(user_id)
        
        summaries: List[PositionSummary] = []
        total_exposure = 0.0
        total_unrealized_pnl = 0.0
        
        for pos in positions:
            try:
                current_price = await self._market_data.get_current_price(pos.pair)
                unrealized_pnl = pos.calculate_pnl(current_price)
                pnl_percentage = pos.calculate_pnl_percentage(current_price)
                
                summary = PositionSummary(
                    position=pos,
                    current_price=current_price,
                    unrealized_pnl=unrealized_pnl,
                    pnl_percentage=pnl_percentage,
                )
                summaries.append(summary)
                
                total_exposure += pos.market_value(current_price)
                total_unrealized_pnl += unrealized_pnl
                
            except Exception:
                summaries.append(PositionSummary(
                    position=pos,
                    current_price=0.0,
                    unrealized_pnl=0.0,
                    pnl_percentage=0.0,
                ))
        
        return ManagePositionsResponse(
            success=True,
            positions=summaries,
            total_exposure_usd=total_exposure,
            total_unrealized_pnl=total_unrealized_pnl,
        )
    
    async def _close_position(self, position_id: Optional[str]) -> ManagePositionsResponse:
        """Close a specific position."""
        if not position_id:
            return ManagePositionsResponse(
                success=False,
                error="Position ID required for close operation",
            )
        
        position = await self._repository.get_position(position_id)
        if not position:
            return ManagePositionsResponse(
                success=False,
                error=f"Position not found: {position_id}",
            )
        
        current_price = await self._market_data.get_current_price(position.pair)
        
        if self._trading:
            await self._trading.close_position(position_id, current_price)
        
        closed = await self._repository.close_position(position_id, current_price)
        
        return ManagePositionsResponse(
            success=True,
            closed_position=closed,
        )
    
    async def _update_sl_tp(
        self,
        position_id: Optional[str],
        stop_loss: Optional[float],
        take_profit: Optional[float],
    ) -> ManagePositionsResponse:
        """Update stop-loss and take-profit for a position."""
        if not position_id:
            return ManagePositionsResponse(
                success=False,
                error="Position ID required for update operation",
            )
        
        position = await self._repository.get_position(position_id)
        if not position:
            return ManagePositionsResponse(
                success=False,
                error=f"Position not found: {position_id}",
            )
        
        if stop_loss is not None:
            position.stop_loss = stop_loss
        if take_profit is not None:
            position.take_profit = take_profit
        
        await self._repository.save_position(position)
        
        current_price = await self._market_data.get_current_price(position.pair)
        summary = PositionSummary(
            position=position,
            current_price=current_price,
            unrealized_pnl=position.calculate_pnl(current_price),
            pnl_percentage=position.calculate_pnl_percentage(current_price),
        )
        
        return ManagePositionsResponse(
            success=True,
            positions=[summary],
        )
