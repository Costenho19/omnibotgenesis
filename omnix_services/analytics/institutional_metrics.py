"""
OMNIX V6.5.4 INSTITUTIONAL+ PREMIUM
Institutional Metrics Calculator - Sharpe, Sortino, Calmar Ratios

Para inversores institucionales que exigen métricas estándar de la industria.
Cálculos por par y agregados para presentaciones a fondos.

METHODOLOGY (Industry-Standard for Paper Trading):
- Equity Curve: Continuous daily series with P&L prorated across holding period
- Returns: Daily returns as % of previous day's equity
- Sharpe: (Mean Daily Return - Risk-Free Rate/252) / StdDev * sqrt(252)
- Sortino: (Mean Daily Return - Risk-Free Rate/252) / Downside StdDev * sqrt(252)
- Calmar: Annualized Return / Max Drawdown
- Max Drawdown: Calculated as % of peak equity, not absolute P&L

PRORATION METHOD:
- For paper trading without intraday price data, P&L is linearly prorated
  across holding days (entry to exit) to capture time-in-market risk
- This is a documented approximation acceptable for paper trading track records
- For live trading with market data, mark-to-market would be preferred

CLAMPING:
- Ratios clamped to [-10, 10] range to prevent divide-by-zero artifacts
- Extreme negative values indicate poor performance, not calculation errors
"""

import logging
import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)

RISK_FREE_RATE = 0.05
INITIAL_CAPITAL = 100000.0


class MetricPeriod(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ALL_TIME = "all_time"


@dataclass
class TradeRecord:
    symbol: str
    pnl_usd: float
    pnl_pct: float
    entry_time: datetime
    exit_time: datetime
    side: str
    size_usd: float


@dataclass
class PairMetrics:
    symbol: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    avg_pnl: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': round(self.win_rate * 100, 2),
            'total_pnl': round(self.total_pnl, 2),
            'avg_pnl': round(self.avg_pnl, 2),
            'max_drawdown': round(self.max_drawdown * 100, 2),
            'sharpe_ratio': round(self.sharpe_ratio, 3),
            'sortino_ratio': round(self.sortino_ratio, 3),
            'calmar_ratio': round(self.calmar_ratio, 3),
            'profit_factor': round(self.profit_factor, 2),
            'avg_win': round(self.avg_win, 2),
            'avg_loss': round(self.avg_loss, 2),
            'largest_win': round(self.largest_win, 2),
            'largest_loss': round(self.largest_loss, 2)
        }


@dataclass
class PortfolioMetrics:
    total_trades: int
    total_pnl: float
    win_rate: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    profit_factor: float
    pair_metrics: Dict[str, PairMetrics] = field(default_factory=dict)
    period: str = "all_time"
    calculated_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_trades': self.total_trades,
            'total_pnl': round(self.total_pnl, 2),
            'win_rate': round(self.win_rate * 100, 2),
            'sharpe_ratio': round(self.sharpe_ratio, 3),
            'sortino_ratio': round(self.sortino_ratio, 3),
            'calmar_ratio': round(self.calmar_ratio, 3),
            'max_drawdown': round(self.max_drawdown * 100, 2),
            'profit_factor': round(self.profit_factor, 2),
            'pair_metrics': {k: v.to_dict() for k, v in self.pair_metrics.items()},
            'period': self.period,
            'calculated_at': self.calculated_at
        }


class InstitutionalMetricsCalculator:
    """
    V6.5.4 INSTITUTIONAL+ PREMIUM
    
    Calcula métricas estándar de la industria para fondos de inversión:
    - Sharpe Ratio: Retorno ajustado por riesgo total
    - Sortino Ratio: Retorno ajustado por riesgo de pérdida (downside)
    - Calmar Ratio: Retorno anualizado / Max Drawdown
    - Profit Factor: Ganancias brutas / Pérdidas brutas
    
    METHODOLOGY:
    - Construye curva de equity diaria desde trades
    - Calcula retornos diarios como % del equity anterior
    - Aplica anualización correcta con sqrt(252)
    
    Usado por: Citadel, Millennium, Point72, Two Sigma
    """
    
    def __init__(self, database_service=None, risk_free_rate: float = RISK_FREE_RATE, 
                 initial_capital: float = INITIAL_CAPITAL):
        self.database_service = database_service
        self.risk_free_rate = risk_free_rate
        self.initial_capital = initial_capital
        self.trading_days = 252
        logger.info("📊 InstitutionalMetricsCalculator V6.5.4 PREMIUM inicializado")
    
    def _build_daily_equity_curve(self, trades: List[TradeRecord]) -> List[Dict[str, Any]]:
        if not trades:
            return []
        
        daily_pnl: Dict[str, float] = defaultdict(float)
        
        for trade in trades:
            entry_date = trade.entry_time.date() if hasattr(trade.entry_time, 'date') else trade.entry_time
            exit_date = trade.exit_time.date() if hasattr(trade.exit_time, 'date') else trade.exit_time
            
            if isinstance(entry_date, datetime):
                entry_date = entry_date.date()
            if isinstance(exit_date, datetime):
                exit_date = exit_date.date()
            
            holding_days = max(1, (exit_date - entry_date).days)
            daily_pnl_amount = trade.pnl_usd / holding_days
            
            current = entry_date
            while current <= exit_date:
                date_key = current.strftime('%Y-%m-%d')
                daily_pnl[date_key] += daily_pnl_amount
                current += timedelta(days=1)
        
        if not daily_pnl:
            return []
        
        first_date = datetime.strptime(min(daily_pnl.keys()), '%Y-%m-%d').date()
        last_date = datetime.strptime(max(daily_pnl.keys()), '%Y-%m-%d').date()
        
        equity_curve = []
        current_equity = self.initial_capital
        current_date = first_date
        
        while current_date <= last_date:
            date_str = current_date.strftime('%Y-%m-%d')
            pnl = daily_pnl.get(date_str, 0.0)
            
            previous_equity = current_equity
            current_equity += pnl
            
            daily_return = pnl / previous_equity if previous_equity > 0 else 0
            
            equity_curve.append({
                'date': date_str,
                'equity': current_equity,
                'daily_pnl': pnl,
                'daily_return': daily_return
            })
            
            current_date += timedelta(days=1)
        
        return equity_curve
    
    def _calculate_max_drawdown_from_equity(self, equity_curve: List[Dict[str, Any]]) -> float:
        if not equity_curve:
            return 0.0
        
        peak = equity_curve[0]['equity']
        max_dd = 0.0
        
        for point in equity_curve:
            equity = point['equity']
            if equity > peak:
                peak = equity
            
            if peak > 0:
                dd = (peak - equity) / peak
                max_dd = max(max_dd, dd)
        
        return max_dd
    
    def _calculate_sharpe_from_equity(self, equity_curve: List[Dict[str, Any]]) -> float:
        if len(equity_curve) < 2:
            return 0.0
        
        daily_returns = [p['daily_return'] for p in equity_curve]
        
        mean_return = sum(daily_returns) / len(daily_returns)
        
        variance = sum((r - mean_return) ** 2 for r in daily_returns) / len(daily_returns)
        std_dev = math.sqrt(variance) if variance > 0 else 0.0001
        
        daily_rf = self.risk_free_rate / self.trading_days
        
        sharpe = ((mean_return - daily_rf) / std_dev) * math.sqrt(self.trading_days)
        
        return max(-10, min(10, sharpe))
    
    def _calculate_sortino_from_equity(self, equity_curve: List[Dict[str, Any]]) -> float:
        if len(equity_curve) < 2:
            return 0.0
        
        daily_returns = [p['daily_return'] for p in equity_curve]
        mean_return = sum(daily_returns) / len(daily_returns)
        
        negative_returns = [r for r in daily_returns if r < 0]
        if not negative_returns:
            return 10.0
        
        downside_variance = sum(r ** 2 for r in negative_returns) / len(daily_returns)
        downside_dev = math.sqrt(downside_variance) if downside_variance > 0 else 0.0001
        
        daily_rf = self.risk_free_rate / self.trading_days
        
        sortino = ((mean_return - daily_rf) / downside_dev) * math.sqrt(self.trading_days)
        
        return max(-10, min(10, sortino))
    
    def _calculate_calmar_from_equity(self, equity_curve: List[Dict[str, Any]], 
                                       max_drawdown: float) -> float:
        if not equity_curve or max_drawdown <= 0:
            return 0.0
        
        first_equity = equity_curve[0]['equity'] - equity_curve[0]['daily_pnl']
        last_equity = equity_curve[-1]['equity']
        total_return = (last_equity - first_equity) / first_equity if first_equity > 0 else 0
        
        first_date = datetime.strptime(equity_curve[0]['date'], '%Y-%m-%d')
        last_date = datetime.strptime(equity_curve[-1]['date'], '%Y-%m-%d')
        days = max(1, (last_date - first_date).days)
        
        years = days / 365.0
        if years > 0:
            annualized_return = ((1 + total_return) ** (1 / years)) - 1
        else:
            annualized_return = total_return
        
        calmar = annualized_return / max_drawdown
        
        return max(-10, min(10, calmar))
    
    def calculate_profit_factor(self, trades: List[TradeRecord]) -> float:
        gross_profit = sum(t.pnl_usd for t in trades if t.pnl_usd > 0)
        gross_loss = abs(sum(t.pnl_usd for t in trades if t.pnl_usd < 0))
        
        if gross_loss == 0:
            return 10.0 if gross_profit > 0 else 0.0
        
        return gross_profit / gross_loss
    
    def calculate_pair_metrics(self, symbol: str, trades: List[TradeRecord]) -> PairMetrics:
        if not trades:
            return PairMetrics(
                symbol=symbol,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                total_pnl=0.0,
                avg_pnl=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                calmar_ratio=0.0,
                profit_factor=0.0,
                avg_win=0.0,
                avg_loss=0.0,
                largest_win=0.0,
                largest_loss=0.0
            )
        
        winning = [t for t in trades if t.pnl_usd > 0]
        losing = [t for t in trades if t.pnl_usd < 0]
        
        total_pnl = sum(t.pnl_usd for t in trades)
        
        equity_curve = self._build_daily_equity_curve(trades)
        max_dd = self._calculate_max_drawdown_from_equity(equity_curve)
        sharpe = self._calculate_sharpe_from_equity(equity_curve)
        sortino = self._calculate_sortino_from_equity(equity_curve)
        calmar = self._calculate_calmar_from_equity(equity_curve, max_dd)
        
        return PairMetrics(
            symbol=symbol,
            total_trades=len(trades),
            winning_trades=len(winning),
            losing_trades=len(losing),
            win_rate=len(winning) / len(trades) if trades else 0.0,
            total_pnl=total_pnl,
            avg_pnl=total_pnl / len(trades) if trades else 0.0,
            max_drawdown=max_dd,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            calmar_ratio=calmar,
            profit_factor=self.calculate_profit_factor(trades),
            avg_win=sum(t.pnl_usd for t in winning) / len(winning) if winning else 0.0,
            avg_loss=sum(t.pnl_usd for t in losing) / len(losing) if losing else 0.0,
            largest_win=max((t.pnl_usd for t in winning), default=0.0),
            largest_loss=min((t.pnl_usd for t in losing), default=0.0)
        )
    
    def calculate_portfolio_metrics(self, trades: List[TradeRecord], period: str = "all_time") -> PortfolioMetrics:
        if not trades:
            return PortfolioMetrics(
                total_trades=0,
                total_pnl=0.0,
                win_rate=0.0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                calmar_ratio=0.0,
                max_drawdown=0.0,
                profit_factor=0.0,
                pair_metrics={},
                period=period,
                calculated_at=datetime.now(timezone.utc).isoformat()
            )
        
        trades_by_symbol: Dict[str, List[TradeRecord]] = {}
        for trade in trades:
            if trade.symbol not in trades_by_symbol:
                trades_by_symbol[trade.symbol] = []
            trades_by_symbol[trade.symbol].append(trade)
        
        pair_metrics = {}
        for symbol, symbol_trades in trades_by_symbol.items():
            pair_metrics[symbol] = self.calculate_pair_metrics(symbol, symbol_trades)
        
        equity_curve = self._build_daily_equity_curve(trades)
        
        max_dd = self._calculate_max_drawdown_from_equity(equity_curve)
        sharpe = self._calculate_sharpe_from_equity(equity_curve)
        sortino = self._calculate_sortino_from_equity(equity_curve)
        calmar = self._calculate_calmar_from_equity(equity_curve, max_dd)
        
        winning = [t for t in trades if t.pnl_usd > 0]
        total_pnl = sum(t.pnl_usd for t in trades)
        
        return PortfolioMetrics(
            total_trades=len(trades),
            total_pnl=total_pnl,
            win_rate=len(winning) / len(trades) if trades else 0.0,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            calmar_ratio=calmar,
            max_drawdown=max_dd,
            profit_factor=self.calculate_profit_factor(trades),
            pair_metrics=pair_metrics,
            period=period,
            calculated_at=datetime.now(timezone.utc).isoformat()
        )
    
    def get_metrics_from_database(self, period: MetricPeriod = MetricPeriod.ALL_TIME) -> Optional[PortfolioMetrics]:
        if not self.database_service:
            logger.warning("⚠️ No database service available for metrics calculation")
            return None
        
        try:
            if period == MetricPeriod.DAILY:
                start_date = datetime.now(timezone.utc) - timedelta(days=1)
            elif period == MetricPeriod.WEEKLY:
                start_date = datetime.now(timezone.utc) - timedelta(weeks=1)
            elif period == MetricPeriod.MONTHLY:
                start_date = datetime.now(timezone.utc) - timedelta(days=30)
            else:
                start_date = None
            
            raw_trades = self.database_service.get_closed_trades(
                start_date=start_date.isoformat() if start_date else None
            )
            
            if not raw_trades:
                return self.calculate_portfolio_metrics([], period.value)
            
            trades = []
            for t in raw_trades:
                try:
                    entry_time = t.get('entry_time') or t.get('opened_at') or datetime.now(timezone.utc)
                    exit_time = t.get('exit_time') or t.get('closed_at') or datetime.now(timezone.utc)
                    
                    if isinstance(entry_time, str):
                        entry_time = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
                    if isinstance(exit_time, str):
                        exit_time = datetime.fromisoformat(exit_time.replace('Z', '+00:00'))
                    
                    pnl_usd = float(t.get('pnl_usd') or t.get('realized_pnl') or t.get('pnl') or 0)
                    pnl_pct = float(t.get('pnl_pct') or t.get('pnl_percentage') or 0)
                    
                    if pnl_pct == 0 and t.get('entry_price') and t.get('exit_price'):
                        entry = float(t['entry_price'])
                        exit = float(t['exit_price'])
                        side = t.get('side', 'buy').lower()
                        if side == 'buy':
                            pnl_pct = (exit - entry) / entry if entry else 0
                        else:
                            pnl_pct = (entry - exit) / entry if entry else 0
                    
                    trades.append(TradeRecord(
                        symbol=t.get('symbol', 'UNKNOWN'),
                        pnl_usd=pnl_usd,
                        pnl_pct=pnl_pct,
                        entry_time=entry_time,
                        exit_time=exit_time,
                        side=t.get('side', 'buy'),
                        size_usd=float(t.get('size_usd') or t.get('position_size') or 0)
                    ))
                except Exception as parse_err:
                    logger.debug(f"Error parsing trade: {parse_err}")
                    continue
            
            return self.calculate_portfolio_metrics(trades, period.value)
            
        except Exception as e:
            logger.error(f"❌ Error calculating metrics from database: {e}")
            return None
    
    def get_summary_for_investors(self) -> Dict[str, Any]:
        metrics = self.get_metrics_from_database(MetricPeriod.ALL_TIME)
        
        if not metrics:
            return {
                'status': 'no_data',
                'message': 'No trade data available for metrics calculation'
            }
        
        grade = 'A' if metrics.sharpe_ratio >= 2.0 else \
                'B' if metrics.sharpe_ratio >= 1.0 else \
                'C' if metrics.sharpe_ratio >= 0.5 else 'D'
        
        return {
            'status': 'success',
            'summary': {
                'performance_grade': grade,
                'total_trades': metrics.total_trades,
                'total_pnl_usd': round(metrics.total_pnl, 2),
                'win_rate_pct': round(metrics.win_rate * 100, 1),
                'risk_adjusted_metrics': {
                    'sharpe_ratio': round(metrics.sharpe_ratio, 3),
                    'sortino_ratio': round(metrics.sortino_ratio, 3),
                    'calmar_ratio': round(metrics.calmar_ratio, 3)
                },
                'risk_metrics': {
                    'max_drawdown_pct': round(metrics.max_drawdown * 100, 2),
                    'profit_factor': round(metrics.profit_factor, 2)
                },
                'pair_breakdown': {
                    symbol: {
                        'trades': pm.total_trades,
                        'win_rate': round(pm.win_rate * 100, 1),
                        'pnl': round(pm.total_pnl, 2),
                        'sharpe': round(pm.sharpe_ratio, 2)
                    }
                    for symbol, pm in metrics.pair_metrics.items()
                }
            },
            'calculated_at': metrics.calculated_at
        }


_metrics_instance: Optional[InstitutionalMetricsCalculator] = None


def get_metrics_calculator(database_service=None) -> InstitutionalMetricsCalculator:
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = InstitutionalMetricsCalculator(database_service=database_service)
    return _metrics_instance
