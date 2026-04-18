"""
OMNIX V7.0 Trading Service Adapter
====================================
Adapter wrapping legacy TradingService for new port interface.

This adapter allows the new use cases to work with the existing
TradingService implementation during migration.
"""

import asyncio
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

from src.omnix.domain.trading.entities import Trade, Position, TradeDirection, TradeStatus

_executor = ThreadPoolExecutor(max_workers=4)


async def _run_sync(func, *args, **kwargs):
    """Run a synchronous function in executor for async context."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, lambda: func(*args, **kwargs))


class TradingServiceAdapter:
    """
    Adapter for legacy TradingService.
    
    Implements ITradingService port by delegating to legacy implementation.
    """
    
    def __init__(self, legacy_service=None):
        """
        Initialize adapter with optional legacy service.
        
        Args:
            legacy_service: Instance of legacy TradingService or None for lazy loading
        """
        self._legacy = legacy_service
        self._lazy_loaded = False
    
    def _get_legacy(self):
        """Lazy load legacy service if not provided."""
        if self._legacy is None and not self._lazy_loaded:
            try:
                from omnix_services.trading_service.trading_service import TradingService
                self._legacy = TradingService()
            except ImportError:
                pass
            self._lazy_loaded = True
        return self._legacy
    
    async def execute_order(
        self,
        pair: str,
        direction: TradeDirection,
        quantity: float,
        price: Optional[float] = None,
        order_type: str = "market",
    ) -> Trade:
        """Execute a trade order via legacy service."""
        legacy = self._get_legacy()
        if legacy is None:
            raise RuntimeError("TradingService not available")
        
        place_order = getattr(legacy, 'place_order', None)
        if place_order is None:
            raise RuntimeError("TradingService.place_order not available")
        
        if asyncio.iscoroutinefunction(place_order):
            result = await place_order(
                pair=pair,
                side=direction.value,
                amount=quantity,
                price=price,
                order_type=order_type,
            )
        else:
            result = await _run_sync(
                place_order,
                pair=pair,
                side=direction.value,
                amount=quantity,
                price=price,
                order_type=order_type,
            )
        
        return Trade(
            id=result.get("order_id", ""),
            pair=pair,
            direction=direction,
            quantity=quantity,
            entry_price=result.get("price", price or 0),
            status=TradeStatus.EXECUTED if result.get("success") else TradeStatus.FAILED,
            order_id=result.get("order_id"),
        )
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order."""
        legacy = self._get_legacy()
        if legacy is None:
            return False
        
        result = await legacy.cancel_order(order_id)
        return result.get("success", False)
    
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get current order status."""
        legacy = self._get_legacy()
        if legacy is None:
            return {"error": "Service not available"}
        
        return await legacy.get_order_status(order_id)
    
    async def get_open_positions(self, user_id: Optional[str] = None) -> List[Position]:
        """Get all open positions."""
        legacy = self._get_legacy()
        if legacy is None:
            return []
        
        positions = await legacy.get_open_positions()
        return [self._convert_position(p) for p in positions]
    
    async def get_balance(self) -> Dict[str, float]:
        """Get current account balance."""
        legacy = self._get_legacy()
        if legacy is None:
            return {}
        
        return await legacy.get_balance()
    
    def _convert_position(self, legacy_pos: dict) -> Position:
        """Convert legacy position dict to Position entity."""
        return Position(
            id=legacy_pos.get("id", ""),
            pair=legacy_pos.get("pair", ""),
            direction=TradeDirection(legacy_pos.get("direction", "buy")),
            quantity=legacy_pos.get("quantity", 0),
            average_entry=legacy_pos.get("entry_price", 0),
        )
