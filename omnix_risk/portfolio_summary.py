"""
PORTFOLIO SUMMARY V1.0
Executive-ready portfolio position reporting

PROBLEM:
After trades, investors want to know the exact portfolio state.
Current system lacks clear position summaries.

SOLUTION:
Real-time portfolio summarizer providing:
1. Net position as % of portfolio
2. Per-asset breakdown with USD values
3. Risk exposure metrics
4. P&L tracking

INVESTOR IMPACT:
- Instant visibility into current allocations
- Professional hedge fund-style reporting
- Transparent position management
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import statistics

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Individual position details"""
    symbol: str
    side: str
    size: float
    entry_price: float
    current_price: float
    entry_time: datetime
    
    @property
    def notional_usd(self) -> float:
        """Current notional value in USD"""
        return abs(self.size * self.current_price)
    
    @property
    def cost_basis_usd(self) -> float:
        """Original cost basis"""
        return abs(self.size * self.entry_price)
    
    @property
    def unrealized_pnl_usd(self) -> float:
        """Unrealized P&L in USD"""
        return self.size * (self.current_price - self.entry_price)
    
    @property
    def unrealized_pnl_pct(self) -> float:
        """Unrealized P&L as percentage"""
        if self.entry_price <= 0:
            return 0.0
        return ((self.current_price - self.entry_price) / self.entry_price) * 100
    
    @property
    def holding_period_hours(self) -> float:
        """How long position has been held"""
        return (datetime.now() - self.entry_time).total_seconds() / 3600


@dataclass
class PositionRisk:
    """Risk metrics for a position"""
    symbol: str
    notional_usd: float
    weight_pct: float
    beta: float
    contribution_to_var: float
    max_loss_usd: float
    stop_loss_distance_pct: float


@dataclass
class PortfolioState:
    """Complete portfolio state snapshot"""
    timestamp: datetime
    total_capital_usd: float
    cash_usd: float
    deployed_usd: float
    deployed_pct: float
    positions: Dict[str, Position]
    position_risks: Dict[str, PositionRisk]
    total_unrealized_pnl_usd: float
    total_unrealized_pnl_pct: float
    largest_position: Optional[str]
    concentration_score: float


class PortfolioSummary:
    """
    Executive Portfolio Summary Engine
    
    Provides real-time portfolio state with:
    - Position-level detail
    - Aggregate metrics
    - Risk exposure tracking
    - Professional formatting
    
    Designed for hedge fund-style reporting.
    """
    
    DEFAULT_STOP_LOSS_PCT = 5.0
    DEFAULT_BETA = 1.0
    CONCENTRATION_THRESHOLD = 25.0
    
    def __init__(
        self,
        total_capital_usd: float = 1_000_000,
        max_position_pct: float = 20.0
    ):
        """
        Initialize portfolio summary
        
        Args:
            total_capital_usd: Total portfolio value
            max_position_pct: Maximum single position size
        """
        self.total_capital_usd = total_capital_usd
        self.max_position_pct = max_position_pct
        
        self._positions: Dict[str, Position] = {}
        self._trade_history: List[Dict] = []
        self._daily_snapshots: List[PortfolioState] = []
        
        self._realized_pnl_usd = 0.0
        
        logger.info("📊 Portfolio Summary V1.0 initialized")
        logger.info(f"   Capital: ${total_capital_usd:,.0f}")
        logger.info(f"   Max Position: {max_position_pct}%")
    
    def add_position(
        self,
        symbol: str,
        side: str,
        size: float,
        entry_price: float,
        current_price: Optional[float] = None
    ):
        """
        Add or update a position
        
        Args:
            symbol: Trading pair
            side: 'long' or 'short'
            size: Position size in base currency
            entry_price: Entry price
            current_price: Current price (uses entry if not provided)
        """
        current_price = current_price or entry_price
        
        if symbol in self._positions:
            existing = self._positions[symbol]
            new_size = existing.size + size
            
            if abs(new_size) < 1e-8:
                self.close_position(symbol, current_price)
                return
            
            avg_entry = (existing.entry_price * abs(existing.size) + entry_price * abs(size)) / abs(new_size)
            self._positions[symbol] = Position(
                symbol=symbol,
                side=side,
                size=new_size,
                entry_price=avg_entry,
                current_price=current_price,
                entry_time=existing.entry_time
            )
        else:
            self._positions[symbol] = Position(
                symbol=symbol,
                side=side,
                size=size,
                entry_price=entry_price,
                current_price=current_price,
                entry_time=datetime.now()
            )
        
        logger.info(f"📈 Position updated: {symbol} | Size: {size} @ ${entry_price:,.2f}")
    
    def update_price(self, symbol: str, current_price: float):
        """
        Update current price for a position
        
        Args:
            symbol: Trading pair
            current_price: New current price
        """
        if symbol in self._positions:
            pos = self._positions[symbol]
            self._positions[symbol] = Position(
                symbol=pos.symbol,
                side=pos.side,
                size=pos.size,
                entry_price=pos.entry_price,
                current_price=current_price,
                entry_time=pos.entry_time
            )
    
    def close_position(
        self,
        symbol: str,
        exit_price: float
    ) -> Optional[Dict]:
        """
        Close a position and record P&L
        
        Args:
            symbol: Trading pair
            exit_price: Exit price
        
        Returns:
            Trade record or None if position doesn't exist
        """
        if symbol not in self._positions:
            return None
        
        pos = self._positions[symbol]
        realized_pnl = pos.size * (exit_price - pos.entry_price)
        realized_pnl_pct = ((exit_price - pos.entry_price) / pos.entry_price * 100) if pos.entry_price > 0 else 0
        
        trade = {
            'symbol': symbol,
            'side': pos.side,
            'size': pos.size,
            'entry_price': pos.entry_price,
            'exit_price': exit_price,
            'realized_pnl_usd': realized_pnl,
            'realized_pnl_pct': realized_pnl_pct,
            'holding_period_hours': pos.holding_period_hours,
            'closed_at': datetime.now().isoformat()
        }
        
        self._trade_history.append(trade)
        self._realized_pnl_usd += realized_pnl
        
        del self._positions[symbol]
        
        logger.info(f"📉 Position closed: {symbol} | P&L: ${realized_pnl:,.2f} ({realized_pnl_pct:+.2f}%)")
        
        return trade
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get a specific position"""
        return self._positions.get(symbol)
    
    def get_all_positions(self) -> Dict[str, Position]:
        """Get all current positions"""
        return self._positions.copy()
    
    def calculate_deployed_capital(self) -> Tuple[float, float]:
        """
        Calculate total deployed capital
        
        Returns:
            Tuple of (deployed_usd, deployed_pct)
        """
        total_deployed = sum(pos.notional_usd for pos in self._positions.values())
        deployed_pct = (total_deployed / self.total_capital_usd * 100) if self.total_capital_usd > 0 else 0
        
        return total_deployed, deployed_pct
    
    def calculate_unrealized_pnl(self) -> Tuple[float, float]:
        """
        Calculate total unrealized P&L
        
        Returns:
            Tuple of (unrealized_usd, unrealized_pct)
        """
        total_unrealized = sum(pos.unrealized_pnl_usd for pos in self._positions.values())
        total_cost = sum(pos.cost_basis_usd for pos in self._positions.values())
        
        unrealized_pct = (total_unrealized / total_cost * 100) if total_cost > 0 else 0
        
        return total_unrealized, unrealized_pct
    
    def calculate_position_risks(self) -> Dict[str, PositionRisk]:
        """
        Calculate risk metrics for all positions
        
        Returns:
            Dict of position risks
        """
        risks = {}
        
        for symbol, pos in self._positions.items():
            weight = (pos.notional_usd / self.total_capital_usd * 100) if self.total_capital_usd > 0 else 0
            
            max_loss = pos.notional_usd * (self.DEFAULT_STOP_LOSS_PCT / 100)
            var_contribution = pos.notional_usd * 0.02 * self.DEFAULT_BETA
            
            risks[symbol] = PositionRisk(
                symbol=symbol,
                notional_usd=pos.notional_usd,
                weight_pct=weight,
                beta=self.DEFAULT_BETA,
                contribution_to_var=var_contribution,
                max_loss_usd=max_loss,
                stop_loss_distance_pct=self.DEFAULT_STOP_LOSS_PCT
            )
        
        return risks
    
    def calculate_concentration(self) -> Tuple[Optional[str], float]:
        """
        Calculate portfolio concentration
        
        Returns:
            Tuple of (largest_position_symbol, herfindahl_score)
        """
        if not self._positions:
            return None, 0.0
        
        deployed, _ = self.calculate_deployed_capital()
        if deployed <= 0:
            return None, 0.0
        
        weights = [pos.notional_usd / deployed for pos in self._positions.values()]
        hhi = sum(w ** 2 for w in weights) * 100
        
        largest = max(self._positions.items(), key=lambda x: x[1].notional_usd)
        
        return largest[0], hhi
    
    def get_state(self) -> PortfolioState:
        """
        Get complete portfolio state snapshot
        
        Returns:
            PortfolioState with all metrics
        """
        deployed_usd, deployed_pct = self.calculate_deployed_capital()
        unrealized_usd, unrealized_pct = self.calculate_unrealized_pnl()
        risks = self.calculate_position_risks()
        largest, concentration = self.calculate_concentration()
        
        cash = self.total_capital_usd - deployed_usd
        
        return PortfolioState(
            timestamp=datetime.now(),
            total_capital_usd=self.total_capital_usd,
            cash_usd=cash,
            deployed_usd=deployed_usd,
            deployed_pct=deployed_pct,
            positions=self._positions.copy(),
            position_risks=risks,
            total_unrealized_pnl_usd=unrealized_usd,
            total_unrealized_pnl_pct=unrealized_pct,
            largest_position=largest,
            concentration_score=concentration
        )
    
    def take_snapshot(self):
        """Take and store a portfolio snapshot"""
        state = self.get_state()
        self._daily_snapshots.append(state)
        
        if len(self._daily_snapshots) > 365:
            self._daily_snapshots = self._daily_snapshots[-365:]
    
    def get_summary_dict(self) -> Dict:
        """
        Get summary as dictionary for external use
        
        Returns:
            Dict with all key metrics
        """
        state = self.get_state()
        
        positions_dict = {}
        for symbol, pos in state.positions.items():
            risk = state.position_risks.get(symbol)
            positions_dict[symbol] = {
                'side': pos.side,
                'size': pos.size,
                'entry_price': pos.entry_price,
                'current_price': pos.current_price,
                'notional_usd': round(pos.notional_usd, 2),
                'weight_pct': round(risk.weight_pct, 2) if risk else 0,
                'unrealized_pnl_usd': round(pos.unrealized_pnl_usd, 2),
                'unrealized_pnl_pct': round(pos.unrealized_pnl_pct, 2),
                'holding_hours': round(pos.holding_period_hours, 1)
            }
        
        return {
            'timestamp': state.timestamp.isoformat(),
            'summary': {
                'total_capital_usd': state.total_capital_usd,
                'cash_usd': round(state.cash_usd, 2),
                'deployed_usd': round(state.deployed_usd, 2),
                'deployed_pct': round(state.deployed_pct, 2),
                'net_position_pct': round(state.deployed_pct, 2)
            },
            'pnl': {
                'unrealized_usd': round(state.total_unrealized_pnl_usd, 2),
                'unrealized_pct': round(state.total_unrealized_pnl_pct, 2),
                'realized_usd': round(self._realized_pnl_usd, 2)
            },
            'risk': {
                'largest_position': state.largest_position,
                'concentration_score': round(state.concentration_score, 2),
                'position_count': len(state.positions)
            },
            'positions': positions_dict
        }
    
    def get_investor_summary(self) -> Dict:
        """
        Get investor-friendly summary
        
        Returns:
            Simplified dict for investor presentations
        """
        state = self.get_state()
        
        net_position = f"{state.deployed_pct:.1f}% of portfolio"
        if state.deployed_pct < 5:
            net_position = "0-5% of portfolio (conservative)"
        elif state.deployed_pct > 50:
            net_position = f"{state.deployed_pct:.1f}% of portfolio (aggressive)"
        
        status = "Conservative"
        if state.deployed_pct > 30:
            status = "Moderate"
        if state.deployed_pct > 50:
            status = "Aggressive"
        
        return {
            'net_position': net_position,
            'allocation_status': status,
            'cash_available': f"${state.cash_usd:,.0f}",
            'total_exposure': f"${state.deployed_usd:,.0f}",
            'position_count': len(state.positions),
            'unrealized_pnl': f"${state.total_unrealized_pnl_usd:+,.0f}" if state.total_unrealized_pnl_usd != 0 else "$0"
        }
    
    def format_summary_text(self) -> str:
        """
        Format portfolio summary as text
        
        Returns:
            Formatted summary string
        """
        state = self.get_state()
        
        lines = []
        lines.append("━" * 50)
        lines.append("📊 PORTFOLIO SUMMARY")
        lines.append("━" * 50)
        
        lines.append("")
        lines.append("💰 CAPITAL ALLOCATION")
        lines.append(f"   Total Capital: ${state.total_capital_usd:,.0f}")
        lines.append(f"   Deployed: ${state.deployed_usd:,.0f} ({state.deployed_pct:.1f}%)")
        lines.append(f"   Cash: ${state.cash_usd:,.0f} ({100-state.deployed_pct:.1f}%)")
        
        if state.deployed_pct < 5:
            lines.append(f"   📍 Net Position: 0-5% of portfolio")
        else:
            lines.append(f"   📍 Net Position: {state.deployed_pct:.1f}% of portfolio")
        
        lines.append("")
        lines.append("📈 PERFORMANCE")
        lines.append(f"   Unrealized P&L: ${state.total_unrealized_pnl_usd:+,.0f} ({state.total_unrealized_pnl_pct:+.2f}%)")
        lines.append(f"   Realized P&L: ${self._realized_pnl_usd:+,.0f}")
        lines.append(f"   Total P&L: ${state.total_unrealized_pnl_usd + self._realized_pnl_usd:+,.0f}")
        
        if state.positions:
            lines.append("")
            lines.append("📋 POSITIONS")
            
            sorted_positions = sorted(
                state.positions.items(),
                key=lambda x: x[1].notional_usd,
                reverse=True
            )
            
            for symbol, pos in sorted_positions[:5]:
                risk = state.position_risks.get(symbol)
                weight = risk.weight_pct if risk else 0
                pnl_icon = "📈" if pos.unrealized_pnl_usd > 0 else "📉" if pos.unrealized_pnl_usd < 0 else "➖"
                lines.append(f"   {pnl_icon} {symbol}")
                lines.append(f"      Weight: {weight:.1f}% | Value: ${pos.notional_usd:,.0f}")
                lines.append(f"      Entry: ${pos.entry_price:,.2f} → Current: ${pos.current_price:,.2f}")
                lines.append(f"      P&L: ${pos.unrealized_pnl_usd:+,.0f} ({pos.unrealized_pnl_pct:+.2f}%)")
            
            if len(sorted_positions) > 5:
                lines.append(f"   ... and {len(sorted_positions) - 5} more positions")
        else:
            lines.append("")
            lines.append("📋 POSITIONS")
            lines.append("   No open positions (100% cash)")
        
        if state.largest_position and state.concentration_score > 30:
            lines.append("")
            lines.append("⚠️ CONCENTRATION WARNING")
            lines.append(f"   Largest: {state.largest_position}")
            lines.append(f"   HHI Score: {state.concentration_score:.0f} (elevated)")
        
        lines.append("━" * 50)
        lines.append(f"   Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append("━" * 50)
        
        return "\n".join(lines)
    
    def format_post_trade_summary(
        self,
        trade_symbol: str,
        trade_side: str,
        trade_size_usd: float
    ) -> str:
        """
        Format summary specifically after a trade
        
        Args:
            trade_symbol: Symbol that was traded
            trade_side: 'buy' or 'sell'
            trade_size_usd: Size of the trade
        
        Returns:
            Formatted post-trade summary
        """
        state = self.get_state()
        
        lines = []
        lines.append("━" * 50)
        lines.append(f"📊 POST-TRADE PORTFOLIO STATUS")
        lines.append(f"   After {trade_side.upper()} ${trade_size_usd:,.0f} {trade_symbol}")
        lines.append("━" * 50)
        
        lines.append("")
        lines.append("📍 FINAL POSITION")
        lines.append(f"   Net Exposure: {state.deployed_pct:.1f}% of portfolio")
        lines.append(f"   Cash Remaining: ${state.cash_usd:,.0f}")
        
        if trade_symbol in state.positions:
            pos = state.positions[trade_symbol]
            risk = state.position_risks.get(trade_symbol)
            weight = risk.weight_pct if risk else 0
            lines.append("")
            lines.append(f"   {trade_symbol} Position:")
            lines.append(f"      Size: {pos.size:.6f}")
            lines.append(f"      Weight: {weight:.1f}% of portfolio")
            lines.append(f"      Value: ${pos.notional_usd:,.0f}")
        
        lines.append("")
        lines.append("📋 ASSET BREAKDOWN")
        if state.positions:
            for symbol, pos in sorted(state.positions.items(), key=lambda x: -x[1].notional_usd)[:5]:
                risk = state.position_risks.get(symbol)
                weight = risk.weight_pct if risk else 0
                lines.append(f"   • {symbol}: {weight:.1f}% (${pos.notional_usd:,.0f})")
        else:
            lines.append("   • CASH: 100%")
        
        lines.append("")
        lines.append("━" * 50)
        
        return "\n".join(lines)


def test_portfolio_summary():
    """Test the portfolio summary"""
    print("=" * 60)
    print("PORTFOLIO SUMMARY TEST")
    print("=" * 60)
    
    summary = PortfolioSummary(total_capital_usd=1_000_000)
    
    print("\n1. Empty portfolio:")
    print(summary.format_summary_text())
    
    print("\n2. Adding positions:")
    summary.add_position('BTC/USD', 'long', 0.5, 91500, 92000)
    summary.add_position('ETH/USD', 'long', 10, 3200, 3350)
    summary.add_position('SOL/USD', 'long', 100, 180, 185)
    
    print(summary.format_summary_text())
    
    print("\n3. Post-trade summary:")
    print(summary.format_post_trade_summary('BTC/USD', 'buy', 50000))
    
    print("\n4. Investor summary:")
    import json
    print(json.dumps(summary.get_investor_summary(), indent=2))
    
    print("\n5. Closing a position:")
    trade = summary.close_position('SOL/USD', 188)
    print(f"   Closed trade: {trade}")
    
    print("\n6. Final state:")
    print(summary.format_summary_text())
    
    print("\n✅ Portfolio Summary test complete!")


if __name__ == "__main__":
    test_portfolio_summary()
