"""
OMNIX V6.0 ULTRA - USD Risk Calculator
=====================================
Institutional-grade risk metrics in USD for investor presentations.

Converts all percentage-based risk metrics to dollar amounts
for clearer communication with investors.

Author: OMNIX Team
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RiskCategory(Enum):
    """Risk severity categories with USD thresholds"""
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"


@dataclass
class PositionRiskUSD:
    """Risk metrics for a single position in USD"""
    symbol: str
    position_size_usd: float
    entry_price: float
    current_price: float
    stop_loss_price: Optional[float]
    take_profit_price: Optional[float]
    
    @property
    def unrealized_pnl_usd(self) -> float:
        """Current unrealized P&L in USD"""
        if self.entry_price == 0:
            return 0.0
        price_change_pct = (self.current_price - self.entry_price) / self.entry_price
        return self.position_size_usd * price_change_pct
    
    @property
    def max_loss_usd(self) -> float:
        """Maximum potential loss if stop loss is hit"""
        if not self.stop_loss_price or self.entry_price == 0:
            return self.position_size_usd
        loss_pct = (self.entry_price - self.stop_loss_price) / self.entry_price
        return abs(self.position_size_usd * loss_pct)
    
    @property
    def max_profit_usd(self) -> float:
        """Maximum potential profit if take profit is hit"""
        if not self.take_profit_price or self.entry_price == 0:
            return 0.0
        profit_pct = (self.take_profit_price - self.entry_price) / self.entry_price
        return self.position_size_usd * profit_pct
    
    @property
    def risk_reward_ratio(self) -> float:
        """Risk/Reward ratio"""
        if self.max_loss_usd == 0:
            return 0.0
        return self.max_profit_usd / self.max_loss_usd


@dataclass
class PortfolioRiskUSD:
    """Aggregated portfolio risk in USD"""
    total_capital_usd: float
    positions: List[PositionRiskUSD] = field(default_factory=list)
    
    @property
    def total_exposure_usd(self) -> float:
        """Total capital deployed in positions"""
        return sum(p.position_size_usd for p in self.positions)
    
    @property
    def exposure_pct(self) -> float:
        """Portfolio exposure as percentage"""
        if self.total_capital_usd == 0:
            return 0.0
        return (self.total_exposure_usd / self.total_capital_usd) * 100
    
    @property
    def total_unrealized_pnl_usd(self) -> float:
        """Total unrealized P&L across all positions"""
        return sum(p.unrealized_pnl_usd for p in self.positions)
    
    @property
    def total_risk_usd(self) -> float:
        """Total capital at risk (sum of all max losses)"""
        return sum(p.max_loss_usd for p in self.positions)
    
    @property
    def available_capital_usd(self) -> float:
        """Capital available for new positions"""
        return self.total_capital_usd - self.total_exposure_usd


@dataclass
class RiskLimitsUSD:
    """Risk limits expressed in USD"""
    max_position_size_usd: float
    max_daily_loss_usd: float
    max_weekly_loss_usd: float
    max_monthly_loss_usd: float
    max_total_exposure_usd: float
    max_single_trade_risk_usd: float
    
    @classmethod
    def from_capital(cls, capital_usd: float) -> 'RiskLimitsUSD':
        """
        Create institutional risk limits based on total capital
        
        Standard institutional limits:
        - Max position: 5% of capital
        - Max daily loss: 2% of capital
        - Max weekly loss: 5% of capital
        - Max monthly loss: 10% of capital
        - Max exposure: 40% of capital
        - Max single trade risk: 1% of capital
        """
        return cls(
            max_position_size_usd=capital_usd * 0.05,
            max_daily_loss_usd=capital_usd * 0.02,
            max_weekly_loss_usd=capital_usd * 0.05,
            max_monthly_loss_usd=capital_usd * 0.10,
            max_total_exposure_usd=capital_usd * 0.40,
            max_single_trade_risk_usd=capital_usd * 0.01
        )


class USDRiskCalculator:
    """
    Institutional-grade USD Risk Calculator
    
    Converts all percentage-based metrics to dollar amounts
    for clearer investor communication.
    
    Example output for $1M capital:
    - "Maximum drawdown: $150,000 (15%)"
    - "Daily VaR (95%): $23,450"
    - "Risk per trade: $10,000 max"
    """
    
    def __init__(self, total_capital_usd: float = 1_000_000.0):
        """
        Initialize calculator with total capital
        
        Args:
            total_capital_usd: Total portfolio capital in USD
        """
        self.total_capital_usd = total_capital_usd
        self.limits = RiskLimitsUSD.from_capital(total_capital_usd)
        self.daily_pnl_usd: List[float] = []
        self.trades_today: List[Dict] = []
        self._daily_loss_usd = 0.0
        self._weekly_loss_usd = 0.0
        self._monthly_loss_usd = 0.0
        
        logger.info(f"💵 USD Risk Calculator initialized: ${total_capital_usd:,.2f}")
    
    def pct_to_usd(self, percentage: float) -> float:
        """Convert percentage to USD based on total capital"""
        return self.total_capital_usd * (percentage / 100)
    
    def usd_to_pct(self, amount_usd: float) -> float:
        """Convert USD amount to percentage of capital"""
        if self.total_capital_usd == 0:
            return 0.0
        return (amount_usd / self.total_capital_usd) * 100
    
    def calculate_position_risk(
        self,
        symbol: str,
        entry_price: float,
        position_size_units: float,
        stop_loss_pct: float = 2.0,
        take_profit_pct: float = 4.0
    ) -> PositionRiskUSD:
        """
        Calculate risk metrics for a position in USD
        
        Args:
            symbol: Trading pair (e.g., "BTC/USD")
            entry_price: Entry price
            position_size_units: Position size in base currency
            stop_loss_pct: Stop loss percentage (default 2%)
            take_profit_pct: Take profit percentage (default 4%)
        
        Returns:
            PositionRiskUSD with all metrics in dollars
        """
        position_size_usd = entry_price * position_size_units
        stop_loss_price = entry_price * (1 - stop_loss_pct / 100)
        take_profit_price = entry_price * (1 + take_profit_pct / 100)
        
        return PositionRiskUSD(
            symbol=symbol,
            position_size_usd=position_size_usd,
            entry_price=entry_price,
            current_price=entry_price,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price
        )
    
    def calculate_var_usd(
        self,
        returns: List[float],
        confidence: float = 0.95,
        holding_period_days: int = 1
    ) -> Dict:
        """
        Calculate Value at Risk in USD
        
        Args:
            returns: List of historical daily returns (as decimals)
            confidence: Confidence level (default 95%)
            holding_period_days: Holding period in days
        
        Returns:
            Dict with VaR metrics in USD
        """
        import numpy as np
        
        empty_result = {
            'var_usd': 0.0,
            'var_pct': 0.0,
            'cvar_usd': 0.0,
            'cvar_pct': 0.0,
            'confidence': confidence,
            'holding_period': holding_period_days,
            'note': ''
        }
        
        if not returns or len(returns) < 20:
            empty_result['note'] = 'Insufficient data for VaR calculation'
            return empty_result
        
        returns_array = np.array(returns, dtype=float)
        
        var_pct = float(np.percentile(returns_array, (1 - confidence) * 100))
        var_pct_adjusted = var_pct * np.sqrt(holding_period_days)
        var_usd = abs(self.total_capital_usd * var_pct_adjusted)
        
        tail_returns = returns_array[returns_array <= var_pct]
        cvar_pct = float(tail_returns.mean()) if len(tail_returns) > 0 else var_pct
        cvar_usd = abs(self.total_capital_usd * cvar_pct * np.sqrt(holding_period_days))
        
        return {
            'var_usd': round(float(var_usd), 2),
            'var_pct': round(abs(float(var_pct_adjusted)) * 100, 4),
            'cvar_usd': round(float(cvar_usd), 2),
            'cvar_pct': round(abs(float(cvar_pct)) * 100, 4),
            'confidence': confidence,
            'holding_period': holding_period_days,
            'note': ''
        }
    
    def calculate_drawdown_usd(
        self,
        equity_curve: List[float]
    ) -> Dict[str, float]:
        """
        Calculate drawdown metrics in USD
        
        Args:
            equity_curve: List of portfolio values over time
        
        Returns:
            Dict with drawdown metrics in USD
        """
        empty_result = {
            'current_drawdown_usd': 0.0,
            'current_drawdown_pct': 0.0,
            'max_drawdown_usd': 0.0,
            'max_drawdown_pct': 0.0,
            'peak_value_usd': 0.0,
            'current_value_usd': 0.0,
            'recovery_needed_usd': 0.0
        }
        
        if not equity_curve or len(equity_curve) < 2:
            return empty_result
        
        import numpy as np
        equity = np.array(equity_curve, dtype=float)
        
        if np.all(equity <= 0):
            return empty_result
        
        peak = np.maximum.accumulate(equity)
        
        drawdown = np.where(peak > 0, peak - equity, 0.0)
        drawdown_pct = np.where(peak > 0, (drawdown / peak) * 100, 0.0)
        
        max_dd_idx = int(np.argmax(drawdown))
        max_drawdown_usd = float(drawdown[max_dd_idx])
        max_drawdown_pct = float(drawdown_pct[max_dd_idx])
        
        current_drawdown_usd = float(drawdown[-1])
        current_peak = float(peak[-1])
        current_value = float(equity[-1])
        recovery_needed_usd = max(0.0, current_peak - current_value)
        
        return {
            'current_drawdown_usd': round(current_drawdown_usd, 2),
            'current_drawdown_pct': round(float(drawdown_pct[-1]), 2),
            'max_drawdown_usd': round(max_drawdown_usd, 2),
            'max_drawdown_pct': round(max_drawdown_pct, 2),
            'peak_value_usd': round(current_peak, 2),
            'current_value_usd': round(current_value, 2),
            'recovery_needed_usd': round(recovery_needed_usd, 2)
        }
    
    def record_trade_result(self, pnl_usd: float) -> Dict[str, any]:
        """
        Record a trade result and update risk tracking
        
        Args:
            pnl_usd: Trade P&L in USD (positive or negative)
        
        Returns:
            Dict with current risk status
        """
        self.daily_pnl_usd.append(pnl_usd)
        
        if pnl_usd < 0:
            self._daily_loss_usd += abs(pnl_usd)
            self._weekly_loss_usd += abs(pnl_usd)
            self._monthly_loss_usd += abs(pnl_usd)
        
        breaches = []
        if self._daily_loss_usd > self.limits.max_daily_loss_usd:
            breaches.append(f"Daily loss ${self._daily_loss_usd:,.0f} > limit ${self.limits.max_daily_loss_usd:,.0f}")
        if self._weekly_loss_usd > self.limits.max_weekly_loss_usd:
            breaches.append(f"Weekly loss ${self._weekly_loss_usd:,.0f} > limit ${self.limits.max_weekly_loss_usd:,.0f}")
        if self._monthly_loss_usd > self.limits.max_monthly_loss_usd:
            breaches.append(f"Monthly loss ${self._monthly_loss_usd:,.0f} > limit ${self.limits.max_monthly_loss_usd:,.0f}")
        
        return {
            'pnl_usd': pnl_usd,
            'daily_pnl_usd': sum(self.daily_pnl_usd),
            'daily_loss_usd': self._daily_loss_usd,
            'weekly_loss_usd': self._weekly_loss_usd,
            'monthly_loss_usd': self._monthly_loss_usd,
            'limit_breaches': breaches,
            'trading_allowed': len(breaches) == 0
        }
    
    def get_risk_category(self, loss_usd: float) -> RiskCategory:
        """
        Categorize risk level based on USD loss
        
        Args:
            loss_usd: Loss amount in USD
        
        Returns:
            RiskCategory enum
        """
        loss_pct = self.usd_to_pct(loss_usd)
        
        if loss_pct < 1:
            return RiskCategory.MINIMAL
        elif loss_pct < 2:
            return RiskCategory.LOW
        elif loss_pct < 5:
            return RiskCategory.MODERATE
        elif loss_pct < 10:
            return RiskCategory.HIGH
        else:
            return RiskCategory.EXTREME
    
    def get_investor_summary(self) -> Dict[str, any]:
        """
        Generate investor-friendly risk summary in USD
        
        Returns:
            Dict with all key metrics in dollar amounts
        """
        return {
            'capital_summary': {
                'total_capital_usd': f"${self.total_capital_usd:,.2f}",
                'daily_loss_limit_usd': f"${self.limits.max_daily_loss_usd:,.2f}",
                'weekly_loss_limit_usd': f"${self.limits.max_weekly_loss_usd:,.2f}",
                'monthly_loss_limit_usd': f"${self.limits.max_monthly_loss_usd:,.2f}",
                'max_position_size_usd': f"${self.limits.max_position_size_usd:,.2f}",
                'max_single_trade_risk_usd': f"${self.limits.max_single_trade_risk_usd:,.2f}"
            },
            'current_status': {
                'daily_loss_usd': f"${self._daily_loss_usd:,.2f}",
                'weekly_loss_usd': f"${self._weekly_loss_usd:,.2f}",
                'monthly_loss_usd': f"${self._monthly_loss_usd:,.2f}",
                'daily_remaining_usd': f"${max(0, self.limits.max_daily_loss_usd - self._daily_loss_usd):,.2f}"
            },
            'limits_in_pct': {
                'daily_loss_pct': '2.0%',
                'weekly_loss_pct': '5.0%',
                'monthly_loss_pct': '10.0%',
                'max_position_pct': '5.0%',
                'max_exposure_pct': '40.0%'
            }
        }
    
    def format_usd(self, amount: float) -> str:
        """Format USD amount for display"""
        if amount >= 0:
            return f"${amount:,.2f}"
        else:
            return f"-${abs(amount):,.2f}"
    
    def reset_daily(self):
        """Reset daily tracking (call at start of each trading day)"""
        self.daily_pnl_usd = []
        self._daily_loss_usd = 0.0
        logger.info("📅 Daily risk counters reset")
    
    def reset_weekly(self):
        """Reset weekly tracking (call at start of each week)"""
        self._weekly_loss_usd = 0.0
        logger.info("📅 Weekly risk counters reset")
    
    def reset_monthly(self):
        """Reset monthly tracking (call at start of each month)"""
        self._monthly_loss_usd = 0.0
        logger.info("📅 Monthly risk counters reset")


def demo_usd_risk_calculator():
    """Demonstrate USD Risk Calculator capabilities"""
    print("=" * 60)
    print("💵 USD RISK CALCULATOR - INSTITUTIONAL DEMO")
    print("=" * 60)
    
    calc = USDRiskCalculator(total_capital_usd=1_000_000)
    
    print("\n📊 Risk Limits (Based on $1M Capital):")
    summary = calc.get_investor_summary()
    for key, value in summary['capital_summary'].items():
        print(f"   {key}: {value}")
    
    print("\n📈 Example Position Risk:")
    position = calc.calculate_position_risk(
        symbol="BTC/USD",
        entry_price=95000,
        position_size_units=0.5,
        stop_loss_pct=2.0,
        take_profit_pct=4.0
    )
    print(f"   Position Size: ${position.position_size_usd:,.2f}")
    print(f"   Max Loss (at SL): ${position.max_loss_usd:,.2f}")
    print(f"   Max Profit (at TP): ${position.max_profit_usd:,.2f}")
    print(f"   Risk/Reward: {position.risk_reward_ratio:.2f}")
    
    print("\n💹 Simulated Trades:")
    trades = [-500, 800, -300, 1200, -1500]
    for pnl in trades:
        result = calc.record_trade_result(pnl)
        status = "✅" if result['trading_allowed'] else "❌"
        print(f"   Trade: {calc.format_usd(pnl)} | Daily Total: {calc.format_usd(result['daily_pnl_usd'])} {status}")
    
    print("\n📉 Drawdown Analysis (simulated equity curve):")
    equity_curve = [1_000_000, 1_020_000, 1_015_000, 980_000, 950_000, 970_000, 1_010_000]
    dd = calc.calculate_drawdown_usd(equity_curve)
    print(f"   Max Drawdown: ${dd['max_drawdown_usd']:,.2f} ({dd['max_drawdown_pct']:.2f}%)")
    print(f"   Current Value: ${dd['current_value_usd']:,.2f}")
    print(f"   Recovery Needed: ${dd['recovery_needed_usd']:,.2f}")
    
    print("\n✅ USD Risk Calculator ready for institutional use")
    return calc


if __name__ == "__main__":
    demo_usd_risk_calculator()
