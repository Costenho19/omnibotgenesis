"""
OMNIX V7.0 Risk Guardian Adapter
=================================
Adapter wrapping legacy RiskGuardian for new port interface.
"""

from typing import Optional, List, Tuple

from src.omnix.domain.trading.entities import Trade, TradeDirection
from src.omnix.domain.risk.entities import RiskAlert


class RiskGuardianAdapter:
    """
    Adapter for legacy RiskGuardian.
    
    Implements IRiskPort by delegating to legacy implementation.
    """
    
    def __init__(self, legacy_guardian=None):
        """Initialize adapter with optional legacy guardian."""
        self._legacy = legacy_guardian
        self._lazy_loaded = False
    
    def _get_legacy(self):
        """Lazy load legacy guardian if not provided."""
        if self._legacy is None and not self._lazy_loaded:
            try:
                from omnix_services.monitoring.risk_guardian import RiskGuardian
                self._legacy = RiskGuardian()
            except ImportError:
                pass
            self._lazy_loaded = True
        return self._legacy
    
    async def can_trade(
        self,
        pair: str,
        quantity: float,
        direction: TradeDirection,
    ) -> Tuple[bool, Optional[str]]:
        """Check if trade is allowed by risk rules."""
        legacy = self._get_legacy()
        if legacy is None:
            return True, None
        
        try:
            result = await legacy.check_trade_allowed(
                pair=pair,
                amount=quantity,
                side=direction.value,
            )
            
            if isinstance(result, dict):
                return result.get("allowed", True), result.get("reason")
            return bool(result), None
            
        except Exception as e:
            return True, None
    
    async def record_trade(self, trade: Trade) -> None:
        """Record a completed trade for risk tracking."""
        legacy = self._get_legacy()
        if legacy is None:
            return
        
        try:
            await legacy.record_trade(
                pair=trade.pair,
                direction=trade.direction.value,
                quantity=trade.quantity,
                entry_price=trade.entry_price,
                pnl=trade.pnl,
            )
        except Exception:
            pass
    
    async def get_daily_pnl(self) -> float:
        """Get today's P&L."""
        legacy = self._get_legacy()
        if legacy is None:
            return 0.0
        
        try:
            return await legacy.get_daily_pnl()
        except Exception:
            return 0.0
    
    async def get_daily_trade_count(self) -> int:
        """Get today's trade count."""
        legacy = self._get_legacy()
        if legacy is None:
            return 0
        
        try:
            return await legacy.get_daily_trade_count()
        except Exception:
            return 0
    
    async def get_current_drawdown(self) -> float:
        """Get current drawdown percentage."""
        legacy = self._get_legacy()
        if legacy is None:
            return 0.0
        
        try:
            return await legacy.get_current_drawdown()
        except Exception:
            return 0.0
