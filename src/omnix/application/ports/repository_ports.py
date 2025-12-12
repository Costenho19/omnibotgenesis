"""
OMNIX V7.0 Repository Ports
============================
Protocols for data persistence.
"""

from typing import Protocol, Optional, List
from datetime import datetime
from src.omnix.domain.trading.entities import Trade, Position, Signal
from src.omnix.domain.risk.entities import RiskAlert, LimitState, CircuitState


class ITradeRepository(Protocol):
    """Port for trade persistence."""
    
    async def save(self, trade: Trade) -> None:
        """Save a trade."""
        ...
    
    async def get_by_id(self, trade_id: str) -> Optional[Trade]:
        """Get trade by ID."""
        ...
    
    async def get_recent(
        self,
        limit: int = 100,
        user_id: Optional[str] = None,
    ) -> List[Trade]:
        """Get recent trades."""
        ...
    
    async def get_by_pair(
        self,
        pair: str,
        limit: int = 50,
    ) -> List[Trade]:
        """Get trades for a specific pair."""
        ...
    
    async def get_by_strategy(
        self,
        strategy: str,
        limit: int = 50,
    ) -> List[Trade]:
        """Get trades by strategy."""
        ...
    
    async def get_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """Get trade statistics."""
        ...


class IPositionRepository(Protocol):
    """Port for position persistence."""
    
    async def save(self, position: Position) -> None:
        """Save a position."""
        ...
    
    async def get_by_id(self, position_id: str) -> Optional[Position]:
        """Get position by ID."""
        ...
    
    async def get_open(self, user_id: Optional[str] = None) -> List[Position]:
        """Get all open positions."""
        ...
    
    async def get_by_pair(self, pair: str) -> Optional[Position]:
        """Get open position for a pair."""
        ...


class ISignalRepository(Protocol):
    """Port for signal persistence."""
    
    async def save(self, signal: Signal) -> None:
        """Save a signal."""
        ...
    
    async def get_by_id(self, signal_id: str) -> Optional[Signal]:
        """Get signal by ID."""
        ...
    
    async def get_recent(
        self,
        limit: int = 50,
        pair: Optional[str] = None,
    ) -> List[Signal]:
        """Get recent signals."""
        ...
    
    async def get_actionable(self) -> List[Signal]:
        """Get signals that are actionable."""
        ...


class IRiskRepository(Protocol):
    """Port for risk data persistence."""
    
    async def save_alert(self, alert: RiskAlert) -> None:
        """Save a risk alert."""
        ...
    
    async def get_active_alerts(
        self,
        user_id: Optional[str] = None,
    ) -> List[RiskAlert]:
        """Get active (unacknowledged) alerts."""
        ...
    
    async def get_limit_state(self, name: str) -> Optional[LimitState]:
        """Get current state of a limit."""
        ...
    
    async def save_limit_state(self, state: LimitState) -> None:
        """Save limit state."""
        ...
    
    async def get_circuit_state(self, name: str) -> Optional[CircuitState]:
        """Get circuit breaker state."""
        ...
    
    async def save_circuit_state(self, state: CircuitState) -> None:
        """Save circuit breaker state."""
        ...
    
    async def get_daily_stats(self) -> dict:
        """Get daily risk statistics."""
        ...
