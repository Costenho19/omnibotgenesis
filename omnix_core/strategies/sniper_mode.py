"""
🎯 OMNIX SNIPER MODE - Precision Trading System
Jan 2, 2026 - Harold's Request

FEATURES:
1. ATR-Based Adaptive Sizing: Stop loss = ATR × 2.5, position sized for max 0.5% risk
2. Volume Veto: Block trades if 5min volume < 1h average (avoid manipulation)
3. Strategy Mode Tracking: Tag trades as SNIPER or STANDARD for comparison

This module provides precision entry filtering for higher-quality trades.
"""

import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SniperMode:
    """
    Sniper Mode: Precision trading with ATR-based sizing and volume veto
    """
    
    def __init__(self, trading_service=None, max_risk_pct: float = 0.005):
        """
        Args:
            trading_service: TradingServiceEnterprise for OHLC/volume data
            max_risk_pct: Maximum risk per trade as decimal (0.5% = 0.005)
        """
        self.trading_service = trading_service
        self.max_risk_pct = max_risk_pct  # 0.5% default
        self.atr_multiplier = 2.5  # ATR × 2.5 for stop loss
        self.enabled = True
        
        logger.info(f"🎯 SniperMode initialized: max_risk={max_risk_pct*100:.1f}%, ATR_mult={self.atr_multiplier}")
    
    def calculate_atr(self, symbol: str, period: int = 14) -> Optional[float]:
        """
        Calculate Average True Range (ATR) for the symbol
        
        ATR = EMA(TrueRange, period) where:
        TrueRange = max(High-Low, abs(High-PrevClose), abs(Low-PrevClose))
        
        Returns:
            ATR value in USD, or None if data unavailable
        """
        if not self.trading_service:
            logger.warning("🎯 SniperMode: No trading_service, cannot calculate ATR")
            return None
        
        try:
            ohlc = self.trading_service.get_ohlc(pair=symbol, interval=60)
            
            if not ohlc or len(ohlc) < period + 1:
                logger.warning(f"🎯 SniperMode: Insufficient OHLC data for {symbol} (got {len(ohlc) if ohlc else 0})")
                return None
            
            true_ranges = []
            for i in range(1, min(len(ohlc), period + 1)):
                high = float(ohlc[i][2])
                low = float(ohlc[i][3])
                prev_close = float(ohlc[i-1][4])
                
                tr = max(
                    high - low,
                    abs(high - prev_close),
                    abs(low - prev_close)
                )
                true_ranges.append(tr)
            
            if not true_ranges:
                return None
            
            atr = sum(true_ranges) / len(true_ranges)
            
            logger.debug(f"🎯 ATR({period}) for {symbol}: ${atr:.2f}")
            return atr
            
        except Exception as e:
            logger.error(f"🎯 SniperMode ATR calculation error: {e}")
            return None
    
    def calculate_sniper_position_size(
        self,
        symbol: str,
        current_price: float,
        balance: float,
        base_size: float
    ) -> Tuple[float, Dict]:
        """
        Calculate position size using ATR-based stop loss and max risk cap
        
        Rule: If ATR × 2.5 creates a wide stop, reduce position so risk never exceeds 0.5% of balance
        
        Args:
            symbol: Trading pair
            current_price: Current price
            balance: Account balance in USD
            base_size: Base position size before sniper adjustment
            
        Returns:
            Tuple of (adjusted_size, info_dict)
        """
        info = {
            'mode': 'SNIPER' if self.enabled else 'STANDARD',
            'atr': None,
            'stop_loss_distance': None,
            'stop_loss_pct': None,
            'max_risk_usd': balance * self.max_risk_pct,
            'original_size': base_size,
            'adjusted_size': base_size,
            'adjustment_reason': None
        }
        
        if not self.enabled:
            return base_size, info
        
        atr = self.calculate_atr(symbol)
        
        if atr is None:
            info['adjustment_reason'] = 'ATR unavailable, using base size'
            return base_size, info
        
        info['atr'] = atr
        
        stop_loss_distance = atr * self.atr_multiplier
        stop_loss_pct = stop_loss_distance / current_price
        
        info['stop_loss_distance'] = stop_loss_distance
        info['stop_loss_pct'] = stop_loss_pct * 100
        
        max_risk_usd = balance * self.max_risk_pct
        info['max_risk_usd'] = max_risk_usd
        
        max_position_for_risk = max_risk_usd / stop_loss_pct if stop_loss_pct > 0 else base_size
        
        if base_size > max_position_for_risk:
            adjusted_size = max_position_for_risk
            info['adjusted_size'] = adjusted_size
            info['adjustment_reason'] = f'ATR stop too wide ({stop_loss_pct*100:.2f}%), reduced for 0.5% max risk'
            
            logger.info(f"🎯 SNIPER SIZE ADJUST: ${base_size:.2f} → ${adjusted_size:.2f} | "
                       f"ATR=${atr:.2f}, SL={stop_loss_pct*100:.2f}%, MaxRisk=${max_risk_usd:.2f}")
            
            return adjusted_size, info
        
        info['adjustment_reason'] = 'Base size within risk limits'
        return base_size, info
    
    def check_volume_veto(self, symbol: str) -> Tuple[bool, Dict]:
        """
        Volume Veto: Block entry if 5-minute volume < hourly average
        
        This filters out low-liquidity conditions that may indicate manipulation.
        
        Returns:
            Tuple of (trade_allowed: bool, info_dict)
        """
        info = {
            'veto_active': False,
            'volume_5min': None,
            'volume_1h_avg': None,
            'ratio': None,
            'reason': None
        }
        
        if not self.enabled or not self.trading_service:
            info['reason'] = 'Sniper mode disabled or no trading service'
            return True, info
        
        try:
            ohlc_5m = self.trading_service.get_ohlc(pair=symbol, interval=5)
            
            if not ohlc_5m or len(ohlc_5m) < 13:
                info['reason'] = 'Insufficient 5min data'
                return True, info
            
            current_5min_volume = float(ohlc_5m[-1][6]) if len(ohlc_5m) > 0 else 0
            
            hourly_volumes = [float(ohlc_5m[i][6]) for i in range(-13, -1) if i < len(ohlc_5m)]
            avg_5min_volume = sum(hourly_volumes) / len(hourly_volumes) if hourly_volumes else 0
            
            info['volume_5min'] = current_5min_volume
            info['volume_1h_avg'] = avg_5min_volume
            
            if avg_5min_volume > 0:
                ratio = current_5min_volume / avg_5min_volume
                info['ratio'] = ratio
                
                if ratio < 1.0:
                    info['veto_active'] = True
                    info['reason'] = f'Volume too low: {ratio:.2f}x of hourly avg'
                    
                    logger.warning(f"🎯 SNIPER VOLUME VETO: {symbol} | "
                                  f"5min vol={current_5min_volume:.4f}, "
                                  f"1h avg={avg_5min_volume:.4f}, "
                                  f"ratio={ratio:.2f}")
                    
                    return False, info
            
            info['reason'] = 'Volume OK'
            return True, info
            
        except Exception as e:
            logger.error(f"🎯 SniperMode volume check error: {e}")
            info['reason'] = f'Volume check error: {e}'
            return True, info
    
    def evaluate_entry(
        self,
        symbol: str,
        current_price: float,
        balance: float,
        base_size: float,
        orderbook_spread_pct: float = None
    ) -> Dict:
        """
        Full Sniper Mode evaluation combining all checks
        
        Args:
            symbol: Trading pair
            current_price: Current price
            balance: Account balance
            base_size: Base position size before adjustments
            orderbook_spread_pct: Optional spread percentage from orderbook
            
        Returns:
            Dict with all sniper analysis including:
            - allow_trade: bool
            - adjusted_size: float
            - strategy_mode: 'SNIPER' or 'STANDARD'
            - sizing_info: dict
            - volume_info: dict
            - veto_reasons: list
        """
        result = {
            'allow_trade': True,
            'adjusted_size': base_size,
            'strategy_mode': 'SNIPER' if self.enabled else 'STANDARD',
            'sizing_info': {},
            'volume_info': {},
            'veto_reasons': []
        }
        
        if not self.enabled:
            result['strategy_mode'] = 'STANDARD'
            return result
        
        volume_ok, volume_info = self.check_volume_veto(symbol)
        result['volume_info'] = volume_info
        
        if not volume_ok:
            result['allow_trade'] = False
            result['veto_reasons'].append(f"VOLUME_VETO: {volume_info.get('reason', 'Low volume')}")
        
        adjusted_size, sizing_info = self.calculate_sniper_position_size(
            symbol=symbol,
            current_price=current_price,
            balance=balance,
            base_size=base_size
        )
        result['adjusted_size'] = adjusted_size
        result['sizing_info'] = sizing_info
        
        if orderbook_spread_pct is not None and orderbook_spread_pct > 0.5:
            result['allow_trade'] = False
            result['veto_reasons'].append(f"SPREAD_VETO: Spread {orderbook_spread_pct:.2f}% > 0.5%")
        
        if result['veto_reasons']:
            logger.info(f"🎯 SNIPER ENTRY BLOCKED for {symbol}: {', '.join(result['veto_reasons'])}")
        else:
            logger.info(f"🎯 SNIPER ENTRY APPROVED for {symbol}: size=${adjusted_size:.2f}")
        
        return result


_sniper_instance: Optional[SniperMode] = None

def get_sniper_mode(trading_service=None, max_risk_pct: float = 0.005) -> SniperMode:
    """Get or create singleton SniperMode instance"""
    global _sniper_instance
    if _sniper_instance is None:
        _sniper_instance = SniperMode(trading_service=trading_service, max_risk_pct=max_risk_pct)
    elif trading_service and _sniper_instance.trading_service is None:
        _sniper_instance.trading_service = trading_service
    return _sniper_instance

def enable_sniper_mode(enabled: bool = True) -> None:
    """Enable or disable sniper mode globally"""
    global _sniper_instance
    if _sniper_instance:
        _sniper_instance.enabled = enabled
        logger.info(f"🎯 SniperMode {'ENABLED' if enabled else 'DISABLED'}")
