#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNIX V6.0 ULTRA - Professional Metrics Calculator
Calcula métricas de nivel institucional para backtesting
Hedge fund-grade performance analysis
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """
    Institutional-grade metrics calculator
    
    Métricas implementadas:
    - Win Rate, Profit Factor
    - Sharpe Ratio, Sortino Ratio, Calmar Ratio
    - Max Drawdown, Average Drawdown
    - Value at Risk (VaR), Conditional VaR
    - Return statistics (total, annual, monthly, daily)
    - Risk-adjusted returns
    - Win/Loss distribution
    """
    
    RISK_FREE_RATE = 0.04  # 4% annual risk-free rate (US Treasury)
    TRADING_DAYS_YEAR = 252
    
    def __init__(self):
        logger.info("📊 Metrics Calculator inicializado")
    
    def calculate_all_metrics(
        self,
        trades: List[Dict],
        initial_capital: float = 10000.0
    ) -> Dict:
        """
        Calculate all performance metrics
        
        Args:
            trades: List of trade dictionaries with keys:
                   'timestamp', 'type' (buy/sell), 'price', 'size', 'pnl'
            initial_capital: Starting capital
            
        Returns:
            Dictionary with all metrics
        """
        if not trades or len(trades) == 0:
            return self._empty_metrics()
        
        logger.info(f"📊 Calculando métricas para {len(trades)} trades...")
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(trades)
        
        # Build equity curve
        equity_curve = self._build_equity_curve(df, initial_capital)
        returns = equity_curve.pct_change().dropna()
        
        # Calculate metrics
        metrics = {
            # Basic stats
            'total_trades': len(trades),
            'winning_trades': len([t for t in trades if t.get('pnl', 0) > 0]),
            'losing_trades': len([t for t in trades if t.get('pnl', 0) < 0]),
            'neutral_trades': len([t for t in trades if t.get('pnl', 0) == 0]),
            
            # Win rate
            'win_rate': self._calculate_win_rate(trades),
            
            # Return metrics
            'total_return': self._calculate_total_return(equity_curve),
            'annual_return': self._calculate_annual_return(equity_curve),
            'monthly_return_avg': self._calculate_monthly_return(equity_curve),
            
            # Risk metrics
            'sharpe_ratio': self._calculate_sharpe_ratio(returns),
            'sortino_ratio': self._calculate_sortino_ratio(returns),
            'calmar_ratio': self._calculate_calmar_ratio(equity_curve),
            
            # Drawdown metrics
            'max_drawdown': self._calculate_max_drawdown(equity_curve),
            'max_drawdown_pct': self._calculate_max_drawdown_pct(equity_curve),
            'avg_drawdown': self._calculate_avg_drawdown(equity_curve),
            
            # PnL metrics
            'total_pnl': sum([t.get('pnl', 0) for t in trades]),
            'avg_win': np.mean([t['pnl'] for t in trades if t.get('pnl', 0) > 0]) if any(t.get('pnl', 0) > 0 for t in trades) else 0,
            'avg_loss': np.mean([t['pnl'] for t in trades if t.get('pnl', 0) < 0]) if any(t.get('pnl', 0) < 0 for t in trades) else 0,
            'profit_factor': self._calculate_profit_factor(trades),
            
            # Risk measures
            'var_95': self._calculate_var(returns, 0.95),
            'cvar_95': self._calculate_cvar(returns, 0.95),
            'volatility_annual': returns.std() * np.sqrt(self.TRADING_DAYS_YEAR),
            
            # Time metrics
            'start_date': df['timestamp'].min() if 'timestamp' in df.columns else None,
            'end_date': df['timestamp'].max() if 'timestamp' in df.columns else None,
            'trading_days': len(equity_curve),
            
            # Final values
            'initial_capital': initial_capital,
            'final_capital': equity_curve.iloc[-1] if len(equity_curve) > 0 else initial_capital,
            
            # Advanced
            'longest_winning_streak': self._calculate_longest_streak(trades, 'win'),
            'longest_losing_streak': self._calculate_longest_streak(trades, 'loss'),
        }
        
        logger.info("✅ Métricas calculadas exitosamente")
        return metrics
    
    def _build_equity_curve(self, df: pd.DataFrame, initial_capital: float) -> pd.Series:
        """Build equity curve from trades"""
        if 'pnl' not in df.columns:
            return pd.Series([initial_capital])
        
        equity = [initial_capital]
        current_equity = initial_capital
        
        for pnl in df['pnl']:
            current_equity += pnl
            equity.append(current_equity)
        
        return pd.Series(equity[1:])  # Remove initial value
    
    def _calculate_win_rate(self, trades: List[Dict]) -> float:
        """Calculate win rate percentage"""
        if not trades:
            return 0.0
        
        winning = sum(1 for t in trades if t.get('pnl', 0) > 0)
        return (winning / len(trades)) * 100
    
    def _calculate_total_return(self, equity_curve: pd.Series) -> float:
        """Calculate total return percentage"""
        if len(equity_curve) < 2:
            return 0.0
        
        return ((equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1) * 100
    
    def _calculate_annual_return(self, equity_curve: pd.Series) -> float:
        """Calculate annualized return"""
        if len(equity_curve) < 2:
            return 0.0
        
        total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
        days = len(equity_curve)
        years = days / self.TRADING_DAYS_YEAR
        
        if years <= 0:
            return 0.0
        
        return (((1 + total_return) ** (1 / years)) - 1) * 100
    
    def _calculate_monthly_return(self, equity_curve: pd.Series) -> float:
        """Calculate average monthly return"""
        if len(equity_curve) < 20:  # Need at least ~1 month of data
            return 0.0
        
        annual_return = self._calculate_annual_return(equity_curve)
        return annual_return / 12
    
    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = None) -> float:
        """
        Calculate Sharpe Ratio
        (Avg Return - Risk Free Rate) / Std Dev Returns
        """
        if len(returns) < 2:
            return 0.0
        
        if risk_free_rate is None:
            risk_free_rate = self.RISK_FREE_RATE
        
        excess_returns = returns - (risk_free_rate / self.TRADING_DAYS_YEAR)
        
        if returns.std() == 0:
            return 0.0
        
        sharpe = (excess_returns.mean() / returns.std()) * np.sqrt(self.TRADING_DAYS_YEAR)
        return sharpe
    
    def _calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float = None) -> float:
        """
        Calculate Sortino Ratio (like Sharpe but only downside volatility)
        """
        if len(returns) < 2:
            return 0.0
        
        if risk_free_rate is None:
            risk_free_rate = self.RISK_FREE_RATE
        
        excess_returns = returns - (risk_free_rate / self.TRADING_DAYS_YEAR)
        downside_returns = returns[returns < 0]
        
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0
        
        sortino = (excess_returns.mean() / downside_returns.std()) * np.sqrt(self.TRADING_DAYS_YEAR)
        return sortino
    
    def _calculate_calmar_ratio(self, equity_curve: pd.Series) -> float:
        """
        Calculate Calmar Ratio
        Annual Return / Max Drawdown
        """
        annual_return = self._calculate_annual_return(equity_curve)
        max_dd = abs(self._calculate_max_drawdown_pct(equity_curve))
        
        if max_dd == 0:
            return 0.0
        
        return annual_return / max_dd
    
    def _calculate_max_drawdown(self, equity_curve: pd.Series) -> float:
        """Calculate maximum drawdown in absolute value"""
        if len(equity_curve) < 2:
            return 0.0
        
        running_max = equity_curve.expanding().max()
        drawdown = equity_curve - running_max
        return drawdown.min()
    
    def _calculate_max_drawdown_pct(self, equity_curve: pd.Series) -> float:
        """Calculate maximum drawdown as percentage"""
        if len(equity_curve) < 2:
            return 0.0
        
        running_max = equity_curve.expanding().max()
        drawdown_pct = ((equity_curve - running_max) / running_max) * 100
        return drawdown_pct.min()
    
    def _calculate_avg_drawdown(self, equity_curve: pd.Series) -> float:
        """Calculate average drawdown"""
        if len(equity_curve) < 2:
            return 0.0
        
        running_max = equity_curve.expanding().max()
        drawdown = equity_curve - running_max
        drawdown_periods = drawdown[drawdown < 0]
        
        if len(drawdown_periods) == 0:
            return 0.0
        
        return drawdown_periods.mean()
    
    def _calculate_profit_factor(self, trades: List[Dict]) -> float:
        """
        Calculate Profit Factor
        Total Wins / Total Losses
        """
        gross_profit = sum([t['pnl'] for t in trades if t.get('pnl', 0) > 0])
        gross_loss = abs(sum([t['pnl'] for t in trades if t.get('pnl', 0) < 0]))
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
        
        return gross_profit / gross_loss
    
    def _calculate_var(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """
        Calculate Value at Risk (VaR)
        Maximum expected loss at given confidence level
        """
        if len(returns) < 10:
            return 0.0
        
        return np.percentile(returns, (1 - confidence) * 100)
    
    def _calculate_cvar(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """
        Calculate Conditional Value at Risk (CVaR)
        Expected loss when VaR is exceeded
        """
        if len(returns) < 10:
            return 0.0
        
        var = self._calculate_var(returns, confidence)
        cvar_returns = returns[returns <= var]
        
        if len(cvar_returns) == 0:
            return var
        
        return cvar_returns.mean()
    
    def _calculate_longest_streak(self, trades: List[Dict], streak_type: str) -> int:
        """Calculate longest winning or losing streak"""
        if not trades:
            return 0
        
        current_streak = 0
        max_streak = 0
        
        for trade in trades:
            pnl = trade.get('pnl', 0)
            
            if streak_type == 'win' and pnl > 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            elif streak_type == 'loss' and pnl < 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return max_streak
    
    def _empty_metrics(self) -> Dict:
        """Return empty metrics dict"""
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'total_return': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'error': 'No trades to analyze'
        }
    
    def format_metrics_report(self, metrics: Dict) -> str:
        """Format metrics as readable text report"""
        report = []
        report.append("=" * 70)
        report.append("📊 PERFORMANCE METRICS REPORT")
        report.append("=" * 70)
        report.append("")
        
        report.append("📈 TRADING STATISTICS:")
        report.append(f"  Total Trades: {metrics.get('total_trades', 0)}")
        report.append(f"  Winning Trades: {metrics.get('winning_trades', 0)}")
        report.append(f"  Losing Trades: {metrics.get('losing_trades', 0)}")
        report.append(f"  Win Rate: {metrics.get('win_rate', 0):.2f}%")
        report.append("")
        
        report.append("💰 RETURN METRICS:")
        report.append(f"  Total Return: {metrics.get('total_return', 0):.2f}%")
        report.append(f"  Annual Return: {metrics.get('annual_return', 0):.2f}%")
        report.append(f"  Monthly Avg Return: {metrics.get('monthly_return_avg', 0):.2f}%")
        report.append(f"  Total PnL: ${metrics.get('total_pnl', 0):,.2f}")
        report.append("")
        
        report.append("📊 RISK-ADJUSTED METRICS:")
        report.append(f"  Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.3f}")
        report.append(f"  Sortino Ratio: {metrics.get('sortino_ratio', 0):.3f}")
        report.append(f"  Calmar Ratio: {metrics.get('calmar_ratio', 0):.3f}")
        report.append(f"  Profit Factor: {metrics.get('profit_factor', 0):.2f}")
        report.append("")
        
        report.append("⚠️ RISK METRICS:")
        report.append(f"  Max Drawdown: {metrics.get('max_drawdown_pct', 0):.2f}%")
        report.append(f"  Avg Drawdown: {metrics.get('avg_drawdown', 0):.2f}")
        report.append(f"  VaR (95%): {metrics.get('var_95', 0):.4f}")
        report.append(f"  CVaR (95%): {metrics.get('cvar_95', 0):.4f}")
        report.append("")
        
        report.append("=" * 70)
        
        return "\n".join(report)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Example trades
    sample_trades = [
        {'timestamp': datetime.now(), 'pnl': 150},
        {'timestamp': datetime.now(), 'pnl': -50},
        {'timestamp': datetime.now(), 'pnl': 200},
        {'timestamp': datetime.now(), 'pnl': 100},
        {'timestamp': datetime.now(), 'pnl': -75},
    ]
    
    calc = MetricsCalculator()
    metrics = calc.calculate_all_metrics(sample_trades, initial_capital=10000)
    
    print(calc.format_metrics_report(metrics))
