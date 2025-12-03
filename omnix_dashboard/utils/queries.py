"""
OMNIX Dashboard - Database Queries
Reusable query functions for trades, balances, and metrics
"""

import logging
from datetime import datetime
from .database import get_db_connection

logger = logging.getLogger(__name__)


def get_paper_trades(days=30, return_dict=False):
    """Fetch REAL paper trading history from database
    
    Args:
        days: Number of days to fetch
        return_dict: If True, returns {success, trades, error} dict for explicit error handling
    
    Returns:
        If return_dict=False: List of trades (legacy behavior)
        If return_dict=True: Dict with success, trades, error, db_connected fields
    """
    with get_db_connection() as conn:
        if not conn:
            logger.warning("No database connection - cannot fetch trades")
            if return_dict:
                return {
                    'success': False,
                    'trades': [],
                    'error': 'Database not connected',
                    'db_connected': False
                }
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, user_id, symbol, side, quantity, entry_price, exit_price, 
                       profit_loss, profit_pct, strategy, status, opened_at, closed_at
                FROM paper_trading_trades
                WHERE opened_at >= NOW() - INTERVAL '1 day' * %s
                ORDER BY opened_at DESC
                LIMIT 500
            ''', (days,))
            
            rows = cursor.fetchall()
            cursor.close()
            
            trades = []
            for row in rows:
                trades.append({
                    'id': row[0],
                    'user_id': row[1],
                    'symbol': row[2],
                    'side': row[3],
                    'quantity': float(row[4]) if row[4] else 0,
                    'entry_price': float(row[5]) if row[5] else 0,
                    'exit_price': float(row[6]) if row[6] else 0,
                    'pnl': float(row[7]) if row[7] else 0,
                    'pnl_percent': float(row[8]) if row[8] else 0,
                    'strategy_used': row[9] or 'OMNIX',
                    'status': row[10],
                    'opened_at': row[11],
                    'closed_at': row[12]
                })
            
            logger.info(f"Fetched {len(trades)} REAL trades from database")
            
            if return_dict:
                return {
                    'success': True,
                    'trades': trades,
                    'error': None,
                    'db_connected': True
                }
            return trades
            
        except Exception as e:
            logger.error(f"Error fetching real trades: {e}")
            if return_dict:
                return {
                    'success': False,
                    'trades': [],
                    'error': str(e),
                    'db_connected': True
                }
            return []


def get_balance_history(days=30):
    """Fetch REAL balance history from database - V6.5 corrected columns"""
    with get_db_connection() as conn:
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id, balance, change_amount, change_reason, recorded_at
                FROM balance_history
                WHERE recorded_at >= NOW() - INTERVAL '1 day' * %s
                ORDER BY recorded_at ASC
            ''', (days,))
            
            rows = cursor.fetchall()
            cursor.close()
            
            history = []
            for row in rows:
                history.append({
                    'user_id': row[0],
                    'total_usd': float(row[1]) if row[1] else 0,
                    'change_amount': float(row[2]) if row[2] else 0,
                    'change_reason': row[3] or 'Unknown',
                    'timestamp': row[4].isoformat() if row[4] else None
                })
            
            if not history:
                cursor2 = conn.cursor()
                cursor2.execute('''
                    SELECT user_id, balance_usd, total_realized_pnl_usd, updated_at
                    FROM paper_trading_balances
                    ORDER BY updated_at DESC
                    LIMIT 1
                ''')
                balance_row = cursor2.fetchone()
                cursor2.close()
                
                if balance_row:
                    history.append({
                        'user_id': balance_row[0],
                        'total_usd': float(balance_row[1]) if balance_row[1] else 1000000,
                        'change_amount': float(balance_row[2]) if balance_row[2] else 0,
                        'change_reason': 'Current Balance',
                        'timestamp': balance_row[3].isoformat() if balance_row[3] else datetime.now().isoformat()
                    })
            
            logger.info(f"Fetched {len(history)} REAL balance snapshots from database")
            return history
            
        except Exception as e:
            logger.error(f"Error fetching balance history: {e}")
            return []


def calculate_metrics(trades):
    """Calculate institutional trading metrics"""
    import numpy as np
    
    if not trades:
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'total_pnl': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'profit_factor': 0,
            'sharpe_ratio': 0,
            'sortino_ratio': 0,
            'max_drawdown': 0,
            'avg_trade_duration': 0,
            'best_trade': 0,
            'worst_trade': 0,
            'expectancy': 0
        }
    
    closed_trades = [t for t in trades if t.get('closed_at') is not None]
    
    if not closed_trades:
        return calculate_metrics([])
    
    pnls = [float(t.get('pnl', 0) or 0) for t in closed_trades]
    winning = [p for p in pnls if p > 0]
    losing = [p for p in pnls if p < 0]
    
    total_trades = len(closed_trades)
    winning_trades = len(winning)
    losing_trades = len(losing)
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    total_pnl = sum(pnls)
    avg_win = np.mean(winning) if winning else 0
    avg_loss = abs(np.mean(losing)) if losing else 0
    
    gross_profit = sum(winning) if winning else 0
    gross_loss = abs(sum(losing)) if losing else 1
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
    
    if len(pnls) > 1:
        initial_capital_for_sharpe = 1_000_000
        pct_returns = np.array(pnls) / initial_capital_for_sharpe * 100
        
        risk_free_rate = 0.05 / 252
        excess_returns = pct_returns - risk_free_rate
        
        if np.std(pct_returns) > 0:
            sharpe = np.mean(excess_returns) / np.std(pct_returns) * np.sqrt(min(len(pnls), 252))
            sharpe = np.clip(sharpe, -10, 10)
        else:
            sharpe = 0
        
        downside_returns = pct_returns[pct_returns < 0]
        if len(downside_returns) > 0 and np.std(downside_returns) > 0:
            sortino = np.mean(excess_returns) / np.std(downside_returns) * np.sqrt(min(len(pnls), 252))
            sortino = np.clip(sortino, -10, 10)
        else:
            sortino = 0
    else:
        sharpe = 0
        sortino = 0
    
    initial_capital = 1_000_000
    cumulative = np.cumsum(pnls)
    equity_curve = initial_capital + cumulative
    peak = np.maximum.accumulate(equity_curve)
    drawdown = (peak - equity_curve) / peak * 100
    drawdown = np.clip(drawdown, 0, 100)
    max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0
    
    best_trade = max(pnls) if pnls else 0
    worst_trade = min(pnls) if pnls else 0
    
    expectancy = (win_rate/100 * avg_win) - ((1 - win_rate/100) * avg_loss)
    
    return {
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'win_rate': round(win_rate, 2),
        'total_pnl': round(total_pnl, 2),
        'avg_win': round(avg_win, 2),
        'avg_loss': round(avg_loss, 2),
        'profit_factor': round(profit_factor, 2),
        'sharpe_ratio': round(sharpe, 2),
        'sortino_ratio': round(sortino, 2),
        'max_drawdown': round(max_drawdown, 2),
        'best_trade': round(best_trade, 2),
        'worst_trade': round(worst_trade, 2),
        'expectancy': round(expectancy, 2)
    }


def get_strategy_breakdown(trades):
    """Breakdown by strategy"""
    if not trades:
        return {}
    
    strategies = {}
    for trade in trades:
        strategy = trade.get('strategy_used', 'Unknown') or 'Manual'
        if strategy not in strategies:
            strategies[strategy] = {'trades': 0, 'pnl': 0, 'wins': 0}
        
        strategies[strategy]['trades'] += 1
        pnl = float(trade.get('pnl', 0) or 0)
        strategies[strategy]['pnl'] += pnl
        if pnl > 0:
            strategies[strategy]['wins'] += 1
    
    for strat in strategies:
        total = strategies[strat]['trades']
        strategies[strat]['win_rate'] = round(strategies[strat]['wins'] / total * 100, 1) if total > 0 else 0
        strategies[strat]['pnl'] = round(strategies[strat]['pnl'], 2)
    
    return strategies


def get_asset_breakdown(trades):
    """Breakdown by crypto vs stocks"""
    crypto_symbols = {'BTC', 'ETH', 'XRP', 'SOL', 'ADA', 'DOGE', 'DOT', 'AVAX', 'LINK', 'MATIC'}
    
    breakdown = {
        'crypto': {'trades': 0, 'pnl': 0, 'wins': 0},
        'stocks': {'trades': 0, 'pnl': 0, 'wins': 0}
    }
    
    for trade in trades:
        symbol = (trade.get('symbol', '') or '').upper().replace('/USD', '').replace('USD', '')
        is_crypto = symbol in crypto_symbols or any(c in symbol for c in crypto_symbols)
        
        category = 'crypto' if is_crypto else 'stocks'
        breakdown[category]['trades'] += 1
        pnl = float(trade.get('pnl', 0) or 0)
        breakdown[category]['pnl'] += pnl
        if pnl > 0:
            breakdown[category]['wins'] += 1
    
    for cat in breakdown:
        total = breakdown[cat]['trades']
        breakdown[cat]['win_rate'] = round(breakdown[cat]['wins'] / total * 100, 1) if total > 0 else 0
        breakdown[cat]['pnl'] = round(breakdown[cat]['pnl'], 2)
    
    return breakdown
