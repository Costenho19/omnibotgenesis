"""
OMNIX V6.0 ULTRA - Orderbook Depth Analyzer
=============================================
Multi-level orderbook analysis for institutional execution.

Analyzes orderbook depth at L1/L2/L5 levels to calculate
real slippage and execution quality for large orders.

Author: OMNIX Team
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum
import logging
import requests

logger = logging.getLogger(__name__)


class DepthLevel(Enum):
    """Orderbook depth levels"""
    L1 = (1, "Best Bid/Ask only")
    L2 = (5, "Top 5 levels")
    L5 = (25, "Top 25 levels (institutional)")
    L10 = (50, "Top 50 levels (full depth)")
    
    def __init__(self, levels: int, description: str):
        self.levels = levels
        self.description = description


@dataclass
class OrderbookLevel:
    """Single price level in orderbook"""
    price: float
    quantity: float
    order_count: int = 1
    
    @property
    def notional_usd(self) -> float:
        """Total value at this level in USD"""
        return self.price * self.quantity


@dataclass
class OrderbookSide:
    """One side of the orderbook (bids or asks)"""
    levels: List[OrderbookLevel]
    
    @property
    def total_quantity(self) -> float:
        """Total quantity across all levels"""
        return sum(level.quantity for level in self.levels)
    
    @property
    def total_notional_usd(self) -> float:
        """Total notional value across all levels"""
        return sum(level.notional_usd for level in self.levels)
    
    @property
    def best_price(self) -> Optional[float]:
        """Best price (top of book)"""
        return self.levels[0].price if self.levels else None
    
    @property
    def weighted_avg_price(self) -> float:
        """Volume-weighted average price"""
        if not self.levels or self.total_quantity == 0:
            return 0.0
        return sum(l.price * l.quantity for l in self.levels) / self.total_quantity


@dataclass
class OrderbookSnapshot:
    """Complete orderbook snapshot"""
    symbol: str
    exchange: str
    bids: OrderbookSide
    asks: OrderbookSide
    timestamp: datetime
    depth_level: DepthLevel
    
    @property
    def mid_price(self) -> float:
        """Mid-market price"""
        if not self.bids.best_price or not self.asks.best_price:
            return 0.0
        return (self.bids.best_price + self.asks.best_price) / 2
    
    @property
    def spread_absolute(self) -> float:
        """Absolute bid-ask spread"""
        if not self.bids.best_price or not self.asks.best_price:
            return 0.0
        return self.asks.best_price - self.bids.best_price
    
    @property
    def spread_bps(self) -> float:
        """Spread in basis points"""
        if self.mid_price == 0:
            return 0.0
        return (self.spread_absolute / self.mid_price) * 10000
    
    @property
    def total_bid_depth_usd(self) -> float:
        """Total USD value on bid side"""
        return self.bids.total_notional_usd
    
    @property
    def total_ask_depth_usd(self) -> float:
        """Total USD value on ask side"""
        return self.asks.total_notional_usd
    
    @property
    def imbalance_ratio(self) -> float:
        """Bid/Ask imbalance ratio (>1 = more buy pressure)"""
        if self.total_ask_depth_usd == 0:
            return 0.0
        return self.total_bid_depth_usd / self.total_ask_depth_usd


@dataclass
class SlippageAnalysis:
    """Slippage analysis for a hypothetical order"""
    symbol: str
    side: str
    order_size_usd: float
    avg_execution_price: float
    mid_price: float
    slippage_usd: float
    slippage_bps: float
    levels_consumed: int
    total_levels: int
    fully_filled: bool
    unfilled_usd: float


class OrderbookDepthAnalyzer:
    """
    Institutional Orderbook Depth Analyzer
    
    Features:
    - Multi-level depth analysis (L1/L2/L5/L10)
    - Slippage calculation for large orders
    - Liquidity scoring
    - Market impact estimation
    - Depth comparison across exchanges
    """
    
    EXCHANGE_ENDPOINTS = {
        'kraken': {
            'url': 'https://api.kraken.com/0/public/Depth',
            'symbol_format': lambda s: s.replace('/', '').replace('BTC', 'XBT'),
            'parse_response': '_parse_kraken_orderbook'
        }
    }
    
    def __init__(self):
        """Initialize orderbook analyzer"""
        self.snapshots: Dict[str, OrderbookSnapshot] = {}
        logger.info("📊 Orderbook Depth Analyzer initialized")
    
    def fetch_orderbook(
        self,
        symbol: str = "BTC/USD",
        exchange: str = "kraken",
        depth_level: DepthLevel = DepthLevel.L5
    ) -> Optional[OrderbookSnapshot]:
        """
        Fetch orderbook from exchange
        
        Args:
            symbol: Trading pair (e.g., "BTC/USD")
            exchange: Exchange identifier
            depth_level: Depth level (L1, L2, L5, L10)
        
        Returns:
            OrderbookSnapshot or None if failed
        """
        if exchange not in self.EXCHANGE_ENDPOINTS:
            logger.error(f"Exchange {exchange} not supported")
            return None
        
        config = self.EXCHANGE_ENDPOINTS[exchange]
        
        try:
            formatted_symbol = config['symbol_format'](symbol)
            url = f"{config['url']}?pair={formatted_symbol}&count={depth_level.levels}"
            
            response = requests.get(url, timeout=10)
            data = response.json()
            
            parse_method = getattr(self, config['parse_response'])
            snapshot = parse_method(data, symbol, depth_level)
            
            if snapshot:
                key = f"{exchange}:{symbol}"
                self.snapshots[key] = snapshot
                
            return snapshot
            
        except Exception as e:
            logger.error(f"Failed to fetch orderbook: {e}")
            return None
    
    def _parse_kraken_orderbook(
        self,
        data: Dict,
        symbol: str,
        depth_level: DepthLevel
    ) -> Optional[OrderbookSnapshot]:
        """Parse Kraken orderbook response"""
        try:
            if data.get('error'):
                logger.error(f"Kraken API error: {data['error']}")
                return None
            
            result = data.get('result', {})
            if not result:
                return None
            
            pair_key = list(result.keys())[0]
            orderbook_data = result[pair_key]
            
            bids = OrderbookSide(levels=[
                OrderbookLevel(
                    price=float(level[0]),
                    quantity=float(level[1])
                )
                for level in orderbook_data.get('bids', [])[:depth_level.levels]
            ])
            
            asks = OrderbookSide(levels=[
                OrderbookLevel(
                    price=float(level[0]),
                    quantity=float(level[1])
                )
                for level in orderbook_data.get('asks', [])[:depth_level.levels]
            ])
            
            return OrderbookSnapshot(
                symbol=symbol,
                exchange="kraken",
                bids=bids,
                asks=asks,
                timestamp=datetime.now(),
                depth_level=depth_level
            )
            
        except Exception as e:
            logger.error(f"Failed to parse Kraken orderbook: {e}")
            return None
    
    def calculate_slippage(
        self,
        snapshot: OrderbookSnapshot,
        order_size_usd: float,
        side: str = "buy"
    ) -> SlippageAnalysis:
        """
        Calculate expected slippage for a given order size
        
        Args:
            snapshot: Orderbook snapshot
            order_size_usd: Order size in USD
            side: 'buy' or 'sell'
        
        Returns:
            SlippageAnalysis with detailed slippage metrics
        
        Calculation method:
        - Iterates through orderbook levels
        - Consumes liquidity at each level until order is filled
        - Calculates volume-weighted average execution price
        - Computes slippage vs mid-market price
        """
        levels = snapshot.asks.levels if side == "buy" else snapshot.bids.levels
        mid_price = snapshot.mid_price
        
        if not levels or mid_price == 0 or order_size_usd <= 0:
            return SlippageAnalysis(
                symbol=snapshot.symbol,
                side=side,
                order_size_usd=order_size_usd,
                avg_execution_price=mid_price,
                mid_price=mid_price,
                slippage_usd=0.0,
                slippage_bps=0.0,
                levels_consumed=0,
                total_levels=len(levels),
                fully_filled=False,
                unfilled_usd=order_size_usd
            )
        
        remaining_usd = order_size_usd
        total_quantity = 0.0
        total_cost = 0.0
        levels_consumed = 0
        
        for level in levels:
            if remaining_usd <= 0:
                break
            
            level_notional = level.price * level.quantity
            
            if level_notional >= remaining_usd:
                quantity_filled = remaining_usd / level.price
                total_quantity += quantity_filled
                total_cost += quantity_filled * level.price
                remaining_usd = 0
            else:
                total_quantity += level.quantity
                total_cost += level_notional
                remaining_usd -= level_notional
            
            levels_consumed += 1
        
        avg_price = total_cost / total_quantity if total_quantity > 0 else mid_price
        
        if mid_price > 0:
            if side == "buy":
                slippage_usd = (avg_price - mid_price) * total_quantity
                slippage_bps = ((avg_price / mid_price) - 1) * 10000
            else:
                slippage_usd = (mid_price - avg_price) * total_quantity
                slippage_bps = (1 - (avg_price / mid_price)) * 10000
        else:
            slippage_usd = 0.0
            slippage_bps = 0.0
        
        return SlippageAnalysis(
            symbol=snapshot.symbol,
            side=side,
            order_size_usd=order_size_usd,
            avg_execution_price=round(avg_price, 2),
            mid_price=round(mid_price, 2),
            slippage_usd=round(abs(slippage_usd), 2),
            slippage_bps=round(abs(slippage_bps), 2),
            levels_consumed=levels_consumed,
            total_levels=len(levels),
            fully_filled=remaining_usd <= 0,
            unfilled_usd=round(remaining_usd, 2)
        )
    
    def get_depth_summary(self, snapshot: OrderbookSnapshot) -> Dict:
        """
        Get summary of orderbook depth
        
        Args:
            snapshot: Orderbook snapshot
        
        Returns:
            Dict with depth metrics
        """
        return {
            'symbol': snapshot.symbol,
            'exchange': snapshot.exchange,
            'depth_level': snapshot.depth_level.name,
            'timestamp': snapshot.timestamp.isoformat(),
            'pricing': {
                'mid_price': f"${snapshot.mid_price:,.2f}",
                'best_bid': f"${snapshot.bids.best_price:,.2f}" if snapshot.bids.best_price else "N/A",
                'best_ask': f"${snapshot.asks.best_price:,.2f}" if snapshot.asks.best_price else "N/A",
                'spread_usd': f"${snapshot.spread_absolute:,.2f}",
                'spread_bps': f"{snapshot.spread_bps:.2f} bps"
            },
            'depth': {
                'bid_depth_usd': f"${snapshot.total_bid_depth_usd:,.2f}",
                'ask_depth_usd': f"${snapshot.total_ask_depth_usd:,.2f}",
                'total_depth_usd': f"${snapshot.total_bid_depth_usd + snapshot.total_ask_depth_usd:,.2f}",
                'imbalance_ratio': f"{snapshot.imbalance_ratio:.2f}"
            },
            'levels': {
                'bid_levels': len(snapshot.bids.levels),
                'ask_levels': len(snapshot.asks.levels)
            }
        }
    
    def analyze_execution_quality(
        self,
        snapshot: OrderbookSnapshot,
        order_sizes_usd: List[float] = None
    ) -> Dict:
        """
        Analyze execution quality for various order sizes
        
        Args:
            snapshot: Orderbook snapshot
            order_sizes_usd: List of order sizes to analyze
        
        Returns:
            Dict with execution quality analysis
        """
        if order_sizes_usd is None:
            order_sizes_usd = [10_000, 50_000, 100_000, 250_000, 500_000]
        
        buy_slippage = []
        sell_slippage = []
        
        for size in order_sizes_usd:
            buy_analysis = self.calculate_slippage(snapshot, size, "buy")
            sell_analysis = self.calculate_slippage(snapshot, size, "sell")
            
            buy_slippage.append({
                'order_size_usd': f"${size:,}",
                'slippage_bps': buy_analysis.slippage_bps,
                'slippage_usd': f"${buy_analysis.slippage_usd:,.2f}",
                'levels_used': buy_analysis.levels_consumed,
                'filled': buy_analysis.fully_filled
            })
            
            sell_slippage.append({
                'order_size_usd': f"${size:,}",
                'slippage_bps': sell_analysis.slippage_bps,
                'slippage_usd': f"${sell_analysis.slippage_usd:,.2f}",
                'levels_used': sell_analysis.levels_consumed,
                'filled': sell_analysis.fully_filled
            })
        
        return {
            'symbol': snapshot.symbol,
            'exchange': snapshot.exchange,
            'analysis_time': datetime.now().isoformat(),
            'buy_side': buy_slippage,
            'sell_side': sell_slippage,
            'recommendation': self._get_execution_recommendation(buy_slippage, sell_slippage)
        }
    
    def _get_execution_recommendation(
        self,
        buy_slippage: List[Dict],
        sell_slippage: List[Dict]
    ) -> str:
        """Generate execution recommendation based on slippage analysis"""
        avg_buy_slippage = sum(s['slippage_bps'] for s in buy_slippage) / len(buy_slippage)
        avg_sell_slippage = sum(s['slippage_bps'] for s in sell_slippage) / len(sell_slippage)
        avg_slippage = (avg_buy_slippage + avg_sell_slippage) / 2
        
        if avg_slippage < 5:
            return "EXCELLENT - Market has deep liquidity, suitable for large orders"
        elif avg_slippage < 15:
            return "GOOD - Adequate liquidity for most order sizes"
        elif avg_slippage < 30:
            return "MODERATE - Consider splitting large orders (TWAP/VWAP)"
        else:
            return "CAUTION - Limited liquidity, use algorithmic execution"
    
    def get_investor_report(self, symbol: str = "BTC/USD") -> Dict:
        """
        Generate investor-friendly orderbook report
        
        Args:
            symbol: Trading pair
        
        Returns:
            Dict with formatted depth data
        """
        snapshot = self.fetch_orderbook(symbol, "kraken", DepthLevel.L5)
        
        if not snapshot:
            return {'error': 'Failed to fetch orderbook'}
        
        summary = self.get_depth_summary(snapshot)
        execution = self.analyze_execution_quality(snapshot)
        
        return {
            'orderbook_summary': summary,
            'execution_analysis': execution,
            'depth_levels_explained': {
                'L1': 'Best bid/ask only - basic pricing',
                'L2': 'Top 5 levels - retail trading',
                'L5': 'Top 25 levels - institutional trading',
                'L10': 'Top 50 levels - full market depth'
            }
        }


def demo_orderbook_analyzer():
    """Demonstrate Orderbook Depth Analyzer capabilities"""
    print("=" * 60)
    print("📊 ORDERBOOK DEPTH ANALYZER - INSTITUTIONAL DEMO")
    print("=" * 60)
    
    analyzer = OrderbookDepthAnalyzer()
    
    print("\n🔍 Fetching BTC/USD orderbook from Kraken (L5 depth)...")
    snapshot = analyzer.fetch_orderbook("BTC/USD", "kraken", DepthLevel.L5)
    
    if not snapshot:
        print("❌ Failed to fetch orderbook")
        return None
    
    summary = analyzer.get_depth_summary(snapshot)
    
    print("\n📈 Orderbook Summary:")
    print("-" * 40)
    print(f"   Symbol: {summary['symbol']} on {summary['exchange']}")
    print(f"   Depth Level: {summary['depth_level']}")
    print(f"   Mid Price: {summary['pricing']['mid_price']}")
    print(f"   Spread: {summary['pricing']['spread_usd']} ({summary['pricing']['spread_bps']})")
    print(f"   Bid Depth: {summary['depth']['bid_depth_usd']}")
    print(f"   Ask Depth: {summary['depth']['ask_depth_usd']}")
    print(f"   Imbalance: {summary['depth']['imbalance_ratio']}")
    
    print("\n💹 Slippage Analysis (Buy Orders):")
    print("-" * 40)
    print(f"   {'Order Size':>12} | {'Slippage':>10} | {'Cost':>12} | Levels")
    print("   " + "-" * 50)
    
    for size in [10_000, 50_000, 100_000, 250_000]:
        analysis = analyzer.calculate_slippage(snapshot, size, "buy")
        filled = "✅" if analysis.fully_filled else "⚠️"
        print(f"   ${size:>10,} | {analysis.slippage_bps:>8.2f}bp | ${analysis.slippage_usd:>10,.2f} | {analysis.levels_consumed:>2} {filled}")
    
    execution = analyzer.analyze_execution_quality(snapshot)
    print(f"\n💡 Recommendation: {execution['recommendation']}")
    
    print("\n✅ Orderbook Analyzer ready for institutional use")
    return analyzer


if __name__ == "__main__":
    demo_orderbook_analyzer()
