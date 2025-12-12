"""
OMNIX V7.0 Trading Domain Entities
===================================
Core business entities for trading operations.

These entities are pure Python with no infrastructure dependencies.
They model the core trading concepts used throughout OMNIX.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import uuid4


class TradeDirection(Enum):
    """Direction of a trade."""
    BUY = "buy"
    SELL = "sell"
    
    @classmethod
    def from_string(cls, value: str) -> "TradeDirection":
        """Parse direction from string (case-insensitive)."""
        normalized = value.lower().strip()
        if normalized in ("buy", "long"):
            return cls.BUY
        elif normalized in ("sell", "short"):
            return cls.SELL
        raise ValueError(f"Invalid trade direction: {value}")


class TradeStatus(Enum):
    """Status of a trade throughout its lifecycle."""
    PENDING = "pending"
    EXECUTED = "executed"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    FAILED = "failed"
    CLOSED = "closed"


class SignalStrength(Enum):
    """Strength tier for trading signals (V6.5.4d)."""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"
    
    @classmethod
    def from_score(cls, score: float) -> "SignalStrength":
        """Convert numeric score to signal strength."""
        if score >= 15:
            return cls.VERY_STRONG
        elif score >= 12:
            return cls.STRONG
        elif score >= 8:
            return cls.MODERATE
        return cls.WEAK
    
    @property
    def min_score(self) -> float:
        """Minimum score for this strength tier."""
        return {
            SignalStrength.WEAK: 0,
            SignalStrength.MODERATE: 8,
            SignalStrength.STRONG: 12,
            SignalStrength.VERY_STRONG: 15,
        }[self]


class PositionStatus(Enum):
    """Status of an open position."""
    OPEN = "open"
    CLOSED = "closed"
    STOPPED_OUT = "stopped_out"
    TAKE_PROFIT = "take_profit"
    LIQUIDATED = "liquidated"


@dataclass
class Trade:
    """
    Core trading entity representing a single trade.
    
    Maps to paper_trading_trades table and Telegram notifications.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    pair: str = ""
    direction: TradeDirection = TradeDirection.BUY
    quantity: float = 0.0
    entry_price: float = 0.0
    status: TradeStatus = TradeStatus.PENDING
    strategy: str = ""
    confidence: float = 0.0
    signal_strength: SignalStrength = SignalStrength.MODERATE
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    exit_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    fees: float = 0.0
    
    user_id: Optional[str] = None
    order_id: Optional[str] = None
    exchange: str = "kraken"
    is_paper: bool = True
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_pnl(self, current_price: float) -> float:
        """Calculate unrealized P&L at current price."""
        if self.direction == TradeDirection.BUY:
            return (current_price - self.entry_price) * self.quantity - self.fees
        return (self.entry_price - current_price) * self.quantity - self.fees
    
    def calculate_pnl_percent(self, current_price: float) -> float:
        """Calculate P&L as percentage of entry."""
        if self.entry_price == 0:
            return 0.0
        pnl = self.calculate_pnl(current_price)
        cost_basis = self.entry_price * self.quantity
        return (pnl / cost_basis) * 100 if cost_basis != 0 else 0.0
    
    def is_profitable(self, current_price: float) -> bool:
        """Check if trade is currently profitable."""
        return self.calculate_pnl(current_price) > 0
    
    def should_stop_loss(self, current_price: float) -> bool:
        """Check if stop loss should trigger."""
        if self.stop_loss is None:
            return False
        if self.direction == TradeDirection.BUY:
            return current_price <= self.stop_loss
        return current_price >= self.stop_loss
    
    def should_take_profit(self, current_price: float) -> bool:
        """Check if take profit should trigger."""
        if self.take_profit is None:
            return False
        if self.direction == TradeDirection.BUY:
            return current_price >= self.take_profit
        return current_price <= self.take_profit
    
    def close(self, exit_price: float, status: TradeStatus = TradeStatus.CLOSED) -> None:
        """Close the trade at given price."""
        self.exit_price = exit_price
        self.status = status
        self.closed_at = datetime.utcnow()
        self.pnl = self.calculate_pnl(exit_price)
        self.pnl_percent = self.calculate_pnl_percent(exit_price)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "pair": self.pair,
            "direction": self.direction.value,
            "quantity": self.quantity,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "status": self.status.value,
            "strategy": self.strategy,
            "confidence": self.confidence,
            "signal_strength": self.signal_strength.value,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "pnl": self.pnl,
            "pnl_percent": self.pnl_percent,
            "fees": self.fees,
            "is_paper": self.is_paper,
            "exchange": self.exchange,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Trade":
        """Create Trade from dictionary."""
        trade = cls(
            id=data.get("id", str(uuid4())),
            pair=data.get("pair", ""),
            direction=TradeDirection(data.get("direction", "buy")),
            quantity=float(data.get("quantity", 0)),
            entry_price=float(data.get("entry_price", 0)),
            status=TradeStatus(data.get("status", "pending")),
            strategy=data.get("strategy", ""),
            confidence=float(data.get("confidence", 0)),
            is_paper=data.get("is_paper", True),
            exchange=data.get("exchange", "kraken"),
        )
        
        if data.get("signal_strength"):
            trade.signal_strength = SignalStrength(data["signal_strength"])
        if data.get("exit_price"):
            trade.exit_price = float(data["exit_price"])
        if data.get("stop_loss"):
            trade.stop_loss = float(data["stop_loss"])
        if data.get("take_profit"):
            trade.take_profit = float(data["take_profit"])
        if data.get("pnl"):
            trade.pnl = float(data["pnl"])
        if data.get("pnl_percent"):
            trade.pnl_percent = float(data["pnl_percent"])
            
        return trade


@dataclass
class Position:
    """
    Represents an open trading position.
    
    A position may consist of multiple trades and tracks
    aggregate exposure and P&L.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    pair: str = ""
    direction: TradeDirection = TradeDirection.BUY
    quantity: float = 0.0
    average_entry: float = 0.0
    status: PositionStatus = PositionStatus.OPEN
    
    opened_at: datetime = field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None
    
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop_pct: Optional[float] = None
    
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    max_drawdown: float = 0.0
    peak_pnl: float = 0.0
    
    trade_ids: List[str] = field(default_factory=list)
    user_id: Optional[str] = None
    strategy: str = ""
    
    def update_pnl(self, current_price: float) -> None:
        """Update unrealized P&L and track drawdown."""
        if self.direction == TradeDirection.BUY:
            self.unrealized_pnl = (current_price - self.average_entry) * self.quantity
        else:
            self.unrealized_pnl = (self.average_entry - current_price) * self.quantity
        
        if self.unrealized_pnl > self.peak_pnl:
            self.peak_pnl = self.unrealized_pnl
        
        drawdown = self.peak_pnl - self.unrealized_pnl
        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown
    
    def add_trade(self, trade: Trade) -> None:
        """Add a trade to this position (averaging in)."""
        if trade.direction != self.direction:
            raise ValueError("Cannot add opposing trade to position")
        
        total_cost = (self.average_entry * self.quantity) + (trade.entry_price * trade.quantity)
        self.quantity += trade.quantity
        self.average_entry = total_cost / self.quantity if self.quantity > 0 else 0
        self.trade_ids.append(trade.id)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "pair": self.pair,
            "direction": self.direction.value,
            "quantity": self.quantity,
            "average_entry": self.average_entry,
            "status": self.status.value,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": self.unrealized_pnl,
            "max_drawdown": self.max_drawdown,
            "trade_ids": self.trade_ids,
            "strategy": self.strategy,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
        }


@dataclass
class Signal:
    """
    Trading signal generated by strategy analysis.
    
    Represents the output of the signal generation stack
    before Coherence Engine veto evaluation.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    pair: str = ""
    direction: TradeDirection = TradeDirection.BUY
    strength: SignalStrength = SignalStrength.MODERATE
    score: float = 0.0
    confidence: float = 0.0
    
    strategy: str = ""
    strategy_votes: Dict[str, float] = field(default_factory=dict)
    
    entry_price: Optional[float] = None
    suggested_stop_loss: Optional[float] = None
    suggested_take_profit: Optional[float] = None
    suggested_size_pct: float = 1.0
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    regime: str = "unknown"
    volatility: float = 0.0
    
    coherence_passed: Optional[bool] = None
    coherence_score: Optional[float] = None
    veto_reason: Optional[str] = None
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_actionable(self) -> bool:
        """Check if signal meets minimum criteria for execution."""
        return (
            self.strength in (SignalStrength.STRONG, SignalStrength.VERY_STRONG)
            and self.coherence_passed is not False
            and self.confidence >= 0.5
        )
    
    def apply_coherence_result(self, passed: bool, score: float, reason: Optional[str] = None) -> None:
        """Apply Coherence Engine evaluation result."""
        self.coherence_passed = passed
        self.coherence_score = score
        if not passed:
            self.veto_reason = reason
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "pair": self.pair,
            "direction": self.direction.value,
            "strength": self.strength.value,
            "score": self.score,
            "confidence": self.confidence,
            "strategy": self.strategy,
            "strategy_votes": self.strategy_votes,
            "entry_price": self.entry_price,
            "suggested_stop_loss": self.suggested_stop_loss,
            "suggested_take_profit": self.suggested_take_profit,
            "regime": self.regime,
            "coherence_passed": self.coherence_passed,
            "coherence_score": self.coherence_score,
            "veto_reason": self.veto_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    @classmethod
    def from_strategy_output(
        cls,
        pair: str,
        direction: str,
        score: float,
        strategy: str,
        votes: Dict[str, float],
        **kwargs
    ) -> "Signal":
        """Create Signal from strategy analysis output."""
        return cls(
            pair=pair,
            direction=TradeDirection.from_string(direction),
            strength=SignalStrength.from_score(score),
            score=score,
            strategy=strategy,
            strategy_votes=votes,
            **kwargs
        )
