"""
Advanced Transaction Cost Analysis (TCA)
Institutional-grade cost modeling for realistic backtesting

FEATURES:
- Spread varies by hour of day (3x higher at night)
- Slippage increases non-linearly with order size
- Volatility multiplies costs during crashes
- Kraken fee tiers by monthly volume

IMPACT:
- Fixed costs 0.41% → Variable costs 0.35%-0.85%
- More realistic backtest results
- Honest investor presentations
"""

import logging
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TCABreakdown:
    """Breakdown of transaction costs"""
    exchange_fee_pct: float
    spread_pct: float
    slippage_pct: float
    volatility_adjustment: float
    total_pct: float
    cost_usd: float
    
    def __str__(self) -> str:
        return (
            f"TCA: {self.total_pct:.3f}% "
            f"(Fee:{self.exchange_fee_pct:.2f}% + "
            f"Spread:{self.spread_pct:.2f}% + "
            f"Slip:{self.slippage_pct:.2f}%)"
        )


class RealisticTCA:
    """
    Transaction Cost Analysis with realistic variable costs
    
    Costs vary by:
    1. Hour of day (liquidity varies)
    2. Order size (market impact)
    3. Market volatility (spread explosion)
    4. Trading volume tier (Kraken fee schedule)
    """
    
    KRAKEN_FEE_TIERS = {
        "retail": {"maker": 0.16, "taker": 0.26},
        "intermediate": {"maker": 0.14, "taker": 0.24},
        "advanced": {"maker": 0.12, "taker": 0.22},
        "pro": {"maker": 0.10, "taker": 0.20},
        "institutional": {"maker": 0.00, "taker": 0.10}
    }
    
    SPREAD_BY_HOUR_UTC = {
        (0, 4): 0.15,
        (4, 8): 0.12,
        (8, 12): 0.08,
        (12, 16): 0.10,
        (16, 20): 0.08,
        (20, 24): 0.13
    }
    
    def __init__(self, volume_tier: str = "retail"):
        """
        Initialize TCA with volume tier
        
        Args:
            volume_tier: Kraken fee tier based on 30-day volume
                - retail: $0-50k/month
                - intermediate: $50k-100k/month
                - advanced: $100k-250k/month
                - pro: $250k-1M/month
                - institutional: $5M+/month
        """
        if volume_tier not in self.KRAKEN_FEE_TIERS:
            volume_tier = "retail"
        
        self.volume_tier = volume_tier
        self.fees = self.KRAKEN_FEE_TIERS[volume_tier]
        
        logger.info(f"TCA initialized with {volume_tier} tier")
        logger.info(f"   Maker: {self.fees['maker']:.2f}%, Taker: {self.fees['taker']:.2f}%")
    
    def get_spread_for_hour(self, hour: int) -> float:
        """Get expected spread for given hour UTC"""
        for (start, end), spread in self.SPREAD_BY_HOUR_UTC.items():
            if start <= hour < end:
                return spread
        return 0.10
    
    def calculate_slippage(self, order_size_usd: float) -> float:
        """
        Calculate slippage based on order size
        
        Slippage is NON-LINEAR:
        - $1k order: ~0.03% slippage
        - $10k order: ~0.05% slippage
        - $50k order: ~0.15% slippage
        - $200k order: ~0.40% slippage
        """
        if order_size_usd < 1000:
            return 0.03
        elif order_size_usd < 10000:
            base = 0.03
            additional = (order_size_usd - 1000) / 450000
            return base + additional
        elif order_size_usd < 50000:
            base = 0.05
            additional = (order_size_usd - 10000) / 200000
            return base + additional
        elif order_size_usd < 200000:
            base = 0.15
            additional = (order_size_usd - 50000) / 400000
            return base + additional
        else:
            return 0.40 + (order_size_usd - 200000) / 1000000
    
    def calculate_volatility_multiplier(self, volatility_pct: float) -> float:
        """
        Calculate spread multiplier based on volatility
        
        During high volatility, spreads can 2-3x:
        - Normal vol (20-30%): 1.0x multiplier
        - High vol (50%): 1.5x multiplier
        - Extreme vol (80%+): 2.0x+ multiplier
        """
        if volatility_pct <= 25:
            return 1.0
        elif volatility_pct <= 50:
            return 1.0 + (volatility_pct - 25) / 50
        elif volatility_pct <= 80:
            return 1.5 + (volatility_pct - 50) / 60
        else:
            return 2.0 + (volatility_pct - 80) / 100
    
    def calculate_total_cost(
        self,
        order_size_usd: float,
        timestamp: Optional[datetime] = None,
        volatility_pct: float = 30.0,
        is_maker: bool = False
    ) -> TCABreakdown:
        """
        Calculate total transaction cost with all factors
        
        Args:
            order_size_usd: Order size in USD
            timestamp: Trade timestamp (for hour-based spread)
            volatility_pct: Current market volatility (ATR or realized vol)
            is_maker: True if limit order (maker), False if market (taker)
        
        Returns:
            TCABreakdown with all cost components
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        exchange_fee = self.fees["maker"] if is_maker else self.fees["taker"]
        
        base_spread = self.get_spread_for_hour(timestamp.hour)
        vol_multiplier = self.calculate_volatility_multiplier(volatility_pct)
        adjusted_spread = base_spread * vol_multiplier
        
        slippage = self.calculate_slippage(order_size_usd)
        
        total_pct = exchange_fee + adjusted_spread + slippage
        
        cost_usd = order_size_usd * (total_pct / 100)
        
        return TCABreakdown(
            exchange_fee_pct=exchange_fee,
            spread_pct=adjusted_spread,
            slippage_pct=slippage,
            volatility_adjustment=vol_multiplier,
            total_pct=total_pct,
            cost_usd=cost_usd
        )
    
    def get_optimal_trading_hours(self) -> Dict[str, any]:
        """Return best and worst trading hours"""
        best_hours = []
        worst_hours = []
        
        for (start, end), spread in self.SPREAD_BY_HOUR_UTC.items():
            if spread <= 0.08:
                best_hours.append(f"{start:02d}:00-{end:02d}:00 UTC")
            elif spread >= 0.13:
                worst_hours.append(f"{start:02d}:00-{end:02d}:00 UTC")
        
        return {
            "best_hours": best_hours,
            "worst_hours": worst_hours,
            "recommendation": "Trade during 08:00-12:00 or 16:00-20:00 UTC for lowest costs"
        }
    
    def estimate_daily_costs(
        self,
        trades_per_day: int,
        avg_order_size: float,
        avg_volatility: float = 35.0
    ) -> Dict[str, float]:
        """Estimate daily trading costs"""
        from datetime import datetime
        
        test_times = [
            datetime(2024, 1, 1, 2, 0),
            datetime(2024, 1, 1, 10, 0),
            datetime(2024, 1, 1, 14, 0),
            datetime(2024, 1, 1, 18, 0),
            datetime(2024, 1, 1, 22, 0)
        ]
        
        costs = []
        for t in test_times:
            breakdown = self.calculate_total_cost(
                order_size_usd=avg_order_size,
                timestamp=t,
                volatility_pct=avg_volatility
            )
            costs.append(breakdown.total_pct)
        
        avg_cost_pct = sum(costs) / len(costs)
        min_cost_pct = min(costs)
        max_cost_pct = max(costs)
        
        daily_volume = trades_per_day * avg_order_size
        daily_cost_usd = daily_volume * (avg_cost_pct / 100)
        
        return {
            "trades_per_day": trades_per_day,
            "avg_order_size": avg_order_size,
            "daily_volume": daily_volume,
            "avg_cost_pct": round(avg_cost_pct, 3),
            "min_cost_pct": round(min_cost_pct, 3),
            "max_cost_pct": round(max_cost_pct, 3),
            "daily_cost_usd": round(daily_cost_usd, 2),
            "monthly_cost_usd": round(daily_cost_usd * 30, 2)
        }


if __name__ == "__main__":
    print("=" * 60)
    print("ADVANCED TRANSACTION COST ANALYSIS - TEST")
    print("=" * 60)
    
    tca = RealisticTCA(volume_tier="intermediate")
    
    print("\n1. Cost by Order Size:")
    for size in [1000, 10000, 50000, 100000, 200000]:
        breakdown = tca.calculate_total_cost(
            order_size_usd=size,
            volatility_pct=35.0
        )
        print(f"   ${size:,}: {breakdown.total_pct:.3f}% (${breakdown.cost_usd:.2f})")
    
    print("\n2. Cost by Hour of Day:")
    from datetime import datetime
    for hour in [2, 6, 10, 14, 18, 22]:
        breakdown = tca.calculate_total_cost(
            order_size_usd=25000,
            timestamp=datetime(2024, 1, 1, hour, 0),
            volatility_pct=35.0
        )
        print(f"   {hour:02d}:00 UTC: {breakdown.total_pct:.3f}%")
    
    print("\n3. Cost by Volatility:")
    for vol in [20, 35, 50, 70, 90]:
        breakdown = tca.calculate_total_cost(
            order_size_usd=25000,
            volatility_pct=vol
        )
        print(f"   Vol {vol}%: {breakdown.total_pct:.3f}% (mult: {breakdown.volatility_adjustment:.2f}x)")
    
    print("\n4. Daily Cost Estimate:")
    daily = tca.estimate_daily_costs(
        trades_per_day=10,
        avg_order_size=25000,
        avg_volatility=40.0
    )
    print(f"   Trades/day: {daily['trades_per_day']}")
    print(f"   Avg order: ${daily['avg_order_size']:,}")
    print(f"   Daily volume: ${daily['daily_volume']:,}")
    print(f"   Cost range: {daily['min_cost_pct']:.3f}% - {daily['max_cost_pct']:.3f}%")
    print(f"   Daily cost: ${daily['daily_cost_usd']:,.2f}")
    print(f"   Monthly cost: ${daily['monthly_cost_usd']:,.2f}")
    
    print("\n5. Optimal Trading Hours:")
    hours = tca.get_optimal_trading_hours()
    print(f"   Best: {', '.join(hours['best_hours'])}")
    print(f"   Worst: {', '.join(hours['worst_hours'])}")
    print(f"   {hours['recommendation']}")
    
    print("\n" + "=" * 60)
