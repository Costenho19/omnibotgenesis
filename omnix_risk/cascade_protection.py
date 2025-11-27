"""
CASCADE PROTECTION SYSTEM V1.0
Institutional-grade loss cascade prevention

PROBLEM:
Drawdowns often cluster together (cascading losses).
A trader losing 3x in a row is more likely to lose the 4th.

SOLUTION:
Progressive risk reduction after consecutive losses:
- 3 losses: -30% position size
- 4 losses: -50% position size  
- 5 losses: -70% position size
- 5+ severe: PAUSE TRADING

EXPECTED IMPACT:
- Clustering: MODERATE → LOW
- Max Consecutive Losses: 5 → 3
- Drawdown Grade: B → A
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


class ProtectionLevel(Enum):
    """Protection levels with risk multipliers"""
    NONE = (0, 1.0, "Normal trading")
    CAUTION = (1, 0.7, "Caution: -30% position size")
    WARNING = (2, 0.5, "Warning: -50% position size")
    CRITICAL = (3, 0.3, "Critical: -70% position size")
    EMERGENCY = (4, 0.0, "EMERGENCY: Trading paused")
    
    def __init__(self, level: int, multiplier: float, description: str):
        self.level = level
        self.multiplier = multiplier
        self.description = description


@dataclass
class TradeResult:
    """Record of a completed trade"""
    timestamp: datetime
    symbol: str
    side: str  # 'buy' or 'sell'
    entry_price: float
    exit_price: float
    position_size: float
    pnl: float
    pnl_pct: float
    is_winner: bool
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TradeResult':
        return cls(
            timestamp=data.get('timestamp', datetime.now()),
            symbol=data.get('symbol', 'UNKNOWN'),
            side=data.get('side', 'buy'),
            entry_price=data.get('entry_price', 0),
            exit_price=data.get('exit_price', 0),
            position_size=data.get('position_size', 0),
            pnl=data.get('pnl', 0),
            pnl_pct=data.get('pnl_pct', 0),
            is_winner=data.get('pnl', 0) > 0
        )


@dataclass
class ProtectionState:
    """Current state of cascade protection"""
    level: ProtectionLevel
    consecutive_losses: int
    consecutive_wins: int
    recent_pnl_pct: float
    is_paused: bool
    pause_reason: Optional[str]
    recovery_trades_needed: int
    last_updated: datetime


class CascadeProtection:
    """
    Institutional-grade cascade protection system
    
    Prevents loss spirals by progressively reducing risk
    after consecutive losses, with emergency pause capability.
    
    Features:
    - Progressive risk reduction (30% → 50% → 70%)
    - Emergency pause after severe cascades
    - Recovery mode requiring consecutive wins
    - Time-based cooldown after pauses
    - Detailed logging for audit trail
    """
    
    CASCADE_THRESHOLD = 3
    RECOVERY_WINS_NEEDED = 2
    SEVERE_LOSS_THRESHOLD = -10.0
    PAUSE_COOLDOWN_HOURS = 4
    MAX_LOOKBACK = 20
    
    def __init__(self, max_lookback: int = 20):
        """
        Initialize cascade protection
        
        Args:
            max_lookback: Number of recent trades to consider
        """
        self.max_lookback = max_lookback
        self.trade_history: List[TradeResult] = []
        self.protection_level = ProtectionLevel.NONE
        self.is_paused = False
        self.pause_start: Optional[datetime] = None
        self.pause_reason: Optional[str] = None
        
        self._consecutive_losses = 0
        self._consecutive_wins = 0
        
        logger.info("🛡️ Cascade Protection System initialized")
        logger.info(f"   Cascade threshold: {self.CASCADE_THRESHOLD} losses")
        logger.info(f"   Recovery required: {self.RECOVERY_WINS_NEEDED} wins")
        logger.info(f"   Lookback window: {self.max_lookback} trades")
    
    def record_trade(self, trade: TradeResult) -> ProtectionState:
        """
        Record a completed trade and update protection state
        
        Args:
            trade: Completed trade result
        
        Returns:
            Current protection state
        """
        self.trade_history.append(trade)
        
        if len(self.trade_history) > self.max_lookback:
            self.trade_history = self.trade_history[-self.max_lookback:]
        
        self._update_consecutive_counts(trade)
        self._update_protection_level()
        self._check_emergency_conditions()
        
        state = self.get_state()
        
        self._log_state_change(trade, state)
        
        return state
    
    def record_trade_from_dict(self, trade_data: Dict) -> ProtectionState:
        """Record trade from dictionary data"""
        trade = TradeResult.from_dict(trade_data)
        return self.record_trade(trade)
    
    def _update_consecutive_counts(self, trade: TradeResult):
        """Update consecutive win/loss counters"""
        if trade.is_winner:
            self._consecutive_wins += 1
            self._consecutive_losses = 0
        else:
            self._consecutive_losses += 1
            self._consecutive_wins = 0
    
    def _update_protection_level(self):
        """
        Update protection level based on consecutive losses
        
        Progression (as documented):
        - 3 losses: CAUTION (-30%, multiplier 0.7)
        - 4 losses: WARNING (-50%, multiplier 0.5)
        - 5 losses: CRITICAL (-70%, multiplier 0.3)
        - 5+ with severe conditions: EMERGENCY (pause)
        """
        
        if self._consecutive_wins >= self.RECOVERY_WINS_NEEDED:
            if self.protection_level != ProtectionLevel.NONE:
                logger.info(
                    f"✅ Recovery complete: {self._consecutive_wins} consecutive wins"
                )
            self.protection_level = ProtectionLevel.NONE
            self.is_paused = False
            self.pause_reason = None
            return
        
        if self._consecutive_losses >= 5:
            self.protection_level = ProtectionLevel.CRITICAL
        elif self._consecutive_losses == 4:
            self.protection_level = ProtectionLevel.WARNING
        elif self._consecutive_losses == self.CASCADE_THRESHOLD:
            self.protection_level = ProtectionLevel.CAUTION
        elif self._consecutive_losses < self.CASCADE_THRESHOLD:
            self.protection_level = ProtectionLevel.NONE
    
    def _check_emergency_conditions(self):
        """Check for emergency pause conditions"""
        
        if len(self.trade_history) < 5:
            return
        
        recent = self.trade_history[-5:]
        
        all_losses = all(not t.is_winner for t in recent)
        cumulative_pnl = sum(t.pnl_pct for t in recent)
        
        if all_losses and cumulative_pnl < self.SEVERE_LOSS_THRESHOLD:
            self._trigger_pause(
                f"Severe cascade: 5 losses = {cumulative_pnl:.1f}% drawdown"
            )
        
        recent_10 = self.trade_history[-10:] if len(self.trade_history) >= 10 else self.trade_history
        cumulative_10 = sum(t.pnl_pct for t in recent_10)
        
        if cumulative_10 < -15.0:
            self._trigger_pause(
                f"Extended drawdown: {cumulative_10:.1f}% over {len(recent_10)} trades"
            )
    
    def _trigger_pause(self, reason: str):
        """Trigger emergency trading pause"""
        if not self.is_paused:
            self.is_paused = True
            self.pause_start = datetime.now()
            self.pause_reason = reason
            self.protection_level = ProtectionLevel.EMERGENCY
            
            logger.critical(f"🛑 TRADING PAUSED: {reason}")
            logger.critical(f"   Pause started: {self.pause_start.isoformat()}")
            logger.critical(f"   Minimum cooldown: {self.PAUSE_COOLDOWN_HOURS} hours")
    
    def can_trade(self) -> Tuple[bool, Optional[str]]:
        """
        Check if trading is allowed
        
        Returns:
            (can_trade, reason_if_blocked)
        """
        if not self.is_paused:
            return True, None
        
        if self.pause_start:
            elapsed = datetime.now() - self.pause_start
            if elapsed < timedelta(hours=self.PAUSE_COOLDOWN_HOURS):
                remaining = timedelta(hours=self.PAUSE_COOLDOWN_HOURS) - elapsed
                hours = remaining.total_seconds() / 3600
                return False, f"Trading paused: {hours:.1f}h remaining. Reason: {self.pause_reason}"
        
        return False, f"Trading paused: {self.pause_reason}. Manual reset required."
    
    def get_risk_multiplier(self) -> float:
        """
        Get current position size multiplier
        
        Returns:
            Multiplier between 0.0 and 1.0
        """
        return self.protection_level.multiplier
    
    def get_state(self) -> ProtectionState:
        """Get current protection state"""
        recent_pnl = sum(t.pnl_pct for t in self.trade_history[-5:]) if self.trade_history else 0
        
        recovery_needed = 0
        if self.protection_level != ProtectionLevel.NONE:
            recovery_needed = max(0, self.RECOVERY_WINS_NEEDED - self._consecutive_wins)
        
        return ProtectionState(
            level=self.protection_level,
            consecutive_losses=self._consecutive_losses,
            consecutive_wins=self._consecutive_wins,
            recent_pnl_pct=recent_pnl,
            is_paused=self.is_paused,
            pause_reason=self.pause_reason,
            recovery_trades_needed=recovery_needed,
            last_updated=datetime.now()
        )
    
    def manual_resume(self, authorized_by: str = "admin") -> bool:
        """
        Manually resume trading after pause
        
        Args:
            authorized_by: Who authorized the resume
        
        Returns:
            True if resumed, False if not allowed
        """
        if not self.is_paused:
            return True
        
        if self.pause_start:
            elapsed = datetime.now() - self.pause_start
            if elapsed < timedelta(hours=self.PAUSE_COOLDOWN_HOURS / 2):
                logger.warning(
                    f"Cannot resume yet - minimum {self.PAUSE_COOLDOWN_HOURS/2:.1f}h required"
                )
                return False
        
        logger.info(f"✅ Trading resumed by {authorized_by}")
        logger.info(f"   Previous pause reason: {self.pause_reason}")
        
        self.is_paused = False
        self.pause_reason = None
        self.pause_start = None
        self.protection_level = ProtectionLevel.WARNING
        
        return True
    
    def _log_state_change(self, trade: TradeResult, state: ProtectionState):
        """Log state changes for audit trail"""
        emoji = "✅" if trade.is_winner else "❌"
        
        log_msg = (
            f"{emoji} Trade: {trade.symbol} {trade.side} | "
            f"PnL: {trade.pnl_pct:+.2f}% | "
            f"Protection: {state.level.name} ({state.level.multiplier:.0%}) | "
            f"Streak: L{state.consecutive_losses}/W{state.consecutive_wins}"
        )
        
        if state.level in [ProtectionLevel.CRITICAL, ProtectionLevel.EMERGENCY]:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)
    
    def get_statistics(self) -> Dict:
        """Get cascade protection statistics"""
        if not self.trade_history:
            return {"error": "No trade history"}
        
        wins = [t for t in self.trade_history if t.is_winner]
        losses = [t for t in self.trade_history if not t.is_winner]
        
        max_consecutive_losses = 0
        current_streak = 0
        for trade in self.trade_history:
            if not trade.is_winner:
                current_streak += 1
                max_consecutive_losses = max(max_consecutive_losses, current_streak)
            else:
                current_streak = 0
        
        return {
            "total_trades": len(self.trade_history),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": len(wins) / len(self.trade_history) * 100,
            "max_consecutive_losses": max_consecutive_losses,
            "current_consecutive_losses": self._consecutive_losses,
            "current_consecutive_wins": self._consecutive_wins,
            "protection_level": self.protection_level.name,
            "risk_multiplier": self.get_risk_multiplier(),
            "is_paused": self.is_paused,
            "pause_reason": self.pause_reason
        }
    
    def reset(self):
        """Reset protection state (use with caution)"""
        logger.warning("⚠️ Cascade Protection RESET")
        self.trade_history.clear()
        self.protection_level = ProtectionLevel.NONE
        self.is_paused = False
        self.pause_start = None
        self.pause_reason = None
        self._consecutive_losses = 0
        self._consecutive_wins = 0


class CascadeProtectionIntegration:
    """
    Integration layer for cascade protection with trading systems
    
    Wraps trade execution with cascade protection checks
    """
    
    def __init__(self, cascade_guard: Optional[CascadeProtection] = None):
        self.guard = cascade_guard or CascadeProtection()
        self.trades_executed = 0
        self.trades_blocked = 0
        self.trades_reduced = 0
    
    async def execute_with_protection(
        self,
        signal: Dict,
        execute_func,
        **kwargs
    ) -> Optional[Dict]:
        """
        Execute trade with cascade protection
        
        Args:
            signal: Trading signal with position_size
            execute_func: Async function to execute trade
            **kwargs: Additional args for execute_func
        
        Returns:
            Trade result or None if blocked
        """
        can_trade, reason = self.guard.can_trade()
        if not can_trade:
            logger.warning(f"🚫 Trade blocked: {reason}")
            self.trades_blocked += 1
            return None
        
        risk_mult = self.guard.get_risk_multiplier()
        
        original_size = signal.get('position_size', 0)
        if risk_mult < 1.0:
            adjusted_size = original_size * risk_mult
            signal['position_size'] = adjusted_size
            self.trades_reduced += 1
            
            logger.info(
                f"📉 Position reduced: ${original_size:,.0f} → ${adjusted_size:,.0f} "
                f"({risk_mult:.0%})"
            )
        
        result = await execute_func(signal, **kwargs)
        
        if result:
            self.guard.record_trade_from_dict(result)
            self.trades_executed += 1
        
        return result
    
    def get_integration_stats(self) -> Dict:
        """Get integration statistics"""
        return {
            "cascade_stats": self.guard.get_statistics(),
            "integration_stats": {
                "trades_executed": self.trades_executed,
                "trades_blocked": self.trades_blocked,
                "trades_reduced": self.trades_reduced,
                "block_rate": (
                    self.trades_blocked / (self.trades_executed + self.trades_blocked) * 100
                    if (self.trades_executed + self.trades_blocked) > 0 else 0
                )
            }
        }


if __name__ == "__main__":
    print("=" * 60)
    print("CASCADE PROTECTION SYSTEM - TEST")
    print("=" * 60)
    
    guard = CascadeProtection()
    
    test_trades = [
        {"symbol": "BTC/USD", "side": "buy", "pnl": 150, "pnl_pct": 1.5},
        {"symbol": "ETH/USD", "side": "buy", "pnl": -80, "pnl_pct": -0.8},
        {"symbol": "BTC/USD", "side": "sell", "pnl": -120, "pnl_pct": -1.2},
        {"symbol": "SOL/USD", "side": "buy", "pnl": -200, "pnl_pct": -2.0},
        {"symbol": "BTC/USD", "side": "buy", "pnl": -150, "pnl_pct": -1.5},
        {"symbol": "ETH/USD", "side": "sell", "pnl": -180, "pnl_pct": -1.8},
        {"symbol": "BTC/USD", "side": "buy", "pnl": 100, "pnl_pct": 1.0},
        {"symbol": "ETH/USD", "side": "buy", "pnl": 120, "pnl_pct": 1.2},
    ]
    
    print("\nSimulating trades:")
    for i, trade_data in enumerate(test_trades, 1):
        trade = TradeResult.from_dict(trade_data)
        state = guard.record_trade(trade)
        
        print(f"\nTrade {i}: {trade_data['symbol']} | PnL: {trade_data['pnl_pct']:+.1f}%")
        print(f"   Protection: {state.level.name}")
        print(f"   Risk Multiplier: {guard.get_risk_multiplier():.0%}")
        print(f"   Can Trade: {guard.can_trade()[0]}")
    
    print("\n" + "=" * 60)
    print("FINAL STATISTICS")
    print("=" * 60)
    stats = guard.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
