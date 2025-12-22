"""
OMNIX V6.5.4d - Market Data Validators
=======================================
Validates freshness and quality of market data before trading decisions.

Key Features:
- Price Stale Detection: Blocks trading on outdated prices
- Configurable thresholds per environment (paper vs production)
- Admin alert integration for institutional monitoring

Created: Dec 22, 2025
"""

import time
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class PriceFreshness(Enum):
    FRESH = "fresh"
    WARNING = "warning"
    STALE = "stale"
    UNKNOWN = "unknown"


@dataclass
class PriceDataState:
    symbol: str
    price: float
    fetch_timestamp: float
    source: str = "kraken"
    freshness: PriceFreshness = PriceFreshness.UNKNOWN
    age_seconds: float = 0.0
    is_tradeable: bool = True
    reason: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "price": self.price,
            "fetch_timestamp": self.fetch_timestamp,
            "source": self.source,
            "freshness": self.freshness.value,
            "age_seconds": round(self.age_seconds, 2),
            "is_tradeable": self.is_tradeable,
            "reason": self.reason
        }


@dataclass
class StaleCheckConfig:
    stale_threshold_seconds: float = 30.0
    warning_threshold_seconds: float = 20.0
    enabled: bool = True
    block_trading_on_stale: bool = True
    

class MarketDataValidator:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        config: Optional[StaleCheckConfig] = None,
        admin_alert_callback: Optional[Callable] = None
    ):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self.config = config or StaleCheckConfig()
        self._admin_alert_callback = admin_alert_callback
        self._stale_event_count: Dict[str, int] = {}
        self._last_stale_alert: Dict[str, float] = {}
        self._alert_cooldown_seconds = 60
        
        self._initialized = True
        logger.info(f"📊 MarketDataValidator initialized")
        logger.info(f"   ⏱️ Stale threshold: {self.config.stale_threshold_seconds}s")
        logger.info(f"   ⚠️ Warning threshold: {self.config.warning_threshold_seconds}s")
        logger.info(f"   🚫 Block on stale: {self.config.block_trading_on_stale}")
    
    def set_admin_alert_callback(self, callback: Callable) -> None:
        self._admin_alert_callback = callback
        logger.info("📢 MarketDataValidator: Admin alert callback configured")
    
    def validate_price(
        self,
        symbol: str,
        price: float,
        fetch_timestamp: float,
        source: str = "kraken"
    ) -> PriceDataState:
        if not self.config.enabled:
            return PriceDataState(
                symbol=symbol,
                price=price,
                fetch_timestamp=fetch_timestamp,
                source=source,
                freshness=PriceFreshness.FRESH,
                age_seconds=0,
                is_tradeable=True
            )
        
        current_time = time.time()
        age_seconds = current_time - fetch_timestamp
        
        if age_seconds >= self.config.stale_threshold_seconds:
            freshness = PriceFreshness.STALE
            is_tradeable = not self.config.block_trading_on_stale
            reason = f"Price is {age_seconds:.1f}s old (threshold: {self.config.stale_threshold_seconds}s)"
            
            self._handle_stale_event(symbol, age_seconds, price)
            
        elif age_seconds >= self.config.warning_threshold_seconds:
            freshness = PriceFreshness.WARNING
            is_tradeable = True
            reason = f"Price approaching stale ({age_seconds:.1f}s)"
            
        else:
            freshness = PriceFreshness.FRESH
            is_tradeable = True
            reason = None
        
        state = PriceDataState(
            symbol=symbol,
            price=price,
            fetch_timestamp=fetch_timestamp,
            source=source,
            freshness=freshness,
            age_seconds=age_seconds,
            is_tradeable=is_tradeable,
            reason=reason
        )
        
        if freshness == PriceFreshness.STALE:
            logger.warning(f"🚨 STALE PRICE: {symbol} @ ${price} - {reason}")
        elif freshness == PriceFreshness.WARNING:
            logger.debug(f"⚠️ Price warning: {symbol} - {reason}")
        
        return state
    
    def _handle_stale_event(self, symbol: str, age_seconds: float, price: float) -> None:
        self._stale_event_count[symbol] = self._stale_event_count.get(symbol, 0) + 1
        
        current_time = time.time()
        last_alert = self._last_stale_alert.get(symbol, 0)
        
        if current_time - last_alert >= self._alert_cooldown_seconds:
            self._last_stale_alert[symbol] = current_time
            
            if self._admin_alert_callback:
                try:
                    self._admin_alert_callback(
                        event_type="price_stale",
                        severity="warning",
                        title=f"🚨 Stale Price: {symbol}",
                        message=(
                            f"Price data for {symbol} is {age_seconds:.1f}s old.\n"
                            f"Last price: ${price:,.2f}\n"
                            f"Trading blocked: {self.config.block_trading_on_stale}\n"
                            f"Total stale events: {self._stale_event_count[symbol]}"
                        ),
                        metadata={
                            "symbol": symbol,
                            "age_seconds": age_seconds,
                            "price": price,
                            "stale_count": self._stale_event_count[symbol]
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to send stale price admin alert: {e}")
    
    def is_price_fresh(
        self,
        symbol: str,
        price: float,
        fetch_timestamp: float
    ) -> bool:
        state = self.validate_price(symbol, price, fetch_timestamp)
        return state.is_tradeable
    
    def get_stale_stats(self) -> Dict:
        return {
            "enabled": self.config.enabled,
            "stale_threshold_seconds": self.config.stale_threshold_seconds,
            "warning_threshold_seconds": self.config.warning_threshold_seconds,
            "block_trading_on_stale": self.config.block_trading_on_stale,
            "stale_event_counts": dict(self._stale_event_count),
            "total_stale_events": sum(self._stale_event_count.values())
        }
    
    def reset_stats(self) -> None:
        self._stale_event_count.clear()
        self._last_stale_alert.clear()
        logger.info("📊 MarketDataValidator stats reset")


_validator_instance: Optional[MarketDataValidator] = None


def get_market_data_validator(
    config: Optional[StaleCheckConfig] = None
) -> MarketDataValidator:
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = MarketDataValidator(config)
    return _validator_instance


def validate_price_freshness(
    symbol: str,
    price: float,
    fetch_timestamp: float,
    source: str = "kraken"
) -> PriceDataState:
    validator = get_market_data_validator()
    return validator.validate_price(symbol, price, fetch_timestamp, source)


def is_price_tradeable(
    symbol: str,
    price: float,
    fetch_timestamp: float
) -> bool:
    validator = get_market_data_validator()
    return validator.is_price_fresh(symbol, price, fetch_timestamp)
