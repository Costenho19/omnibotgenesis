"""
OMNIX Dashboard - Database Queries
Reusable query functions for trades, balances, and metrics
"""

import logging
import time
from datetime import datetime
from .database import get_db_connection

logger = logging.getLogger(__name__)

# Simple in-memory cache for faster dashboard loading
_cache = {}
_cache_ttl = 60  # Cache TTL in seconds (1 minute)


def _get_cached(key):
    """Get value from cache if not expired"""
    if key in _cache:
        cached_time, value = _cache[key]
        if time.time() - cached_time < _cache_ttl:
            return value
    return None


def _set_cached(key, value):
    """Store value in cache with current timestamp"""
    _cache[key] = (time.time(), value)


def clear_cache():
    """Clear all cached data - useful after new trades"""
    global _cache
    _cache = {}
    logger.info("Query cache cleared")


def get_paper_trades(days=None, return_dict=False, track_record_only=False):
    """Fetch REAL paper trading history from database
    
    Args:
        days: Number of days to fetch. If None, fetches ALL trades (real-time complete data)
        return_dict: If True, returns {success, trades, error} dict for explicit error handling
        track_record_only: If True, only fetches trades from Official Track Record (Jan 15, 2026+)
    
    Returns:
        If return_dict=False: List of trades (legacy behavior)
        If return_dict=True: Dict with success, trades, error, db_connected fields
    
    FIX Jan 7 2026: Default changed to None (all trades) to ensure dashboard 
    always shows complete real-time data matching PostgreSQL exactly.
    
    FIX Jan 25 2026: Added track_record_only flag to separate Learning Baseline 
    from Official Track Record for investor-facing metrics.
    
    FIX Jan 28 2026: Added caching for faster dashboard loading.
    """
    cache_key = f"trades_{days}_{return_dict}_{track_record_only}"
    cached = _get_cached(cache_key)
    if cached is not None:
        logger.debug(f"Using cached trades for {cache_key}")
        return cached
    
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
            if track_record_only:
                cursor.execute('''
                    SELECT id, user_id, symbol, side, quantity, entry_price, exit_price, 
                           profit_loss, profit_pct, strategy, status, opened_at, closed_at
                    FROM paper_trading_trades
                    WHERE opened_at >= '2026-01-15'
                    ORDER BY opened_at DESC
                    LIMIT 1000
                ''')
            elif days is None:
                cursor.execute('''
                    SELECT id, user_id, symbol, side, quantity, entry_price, exit_price, 
                           profit_loss, profit_pct, strategy, status, opened_at, closed_at
                    FROM paper_trading_trades
                    ORDER BY opened_at DESC
                    LIMIT 1000
                ''')
            else:
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
                result = {
                    'success': True,
                    'trades': trades,
                    'error': None,
                    'db_connected': True
                }
                _set_cached(cache_key, result)
                return result
            _set_cached(cache_key, trades)
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
    """Fetch REAL balance history from database"""
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
            'win_rate_net': 0,
            'win_rate_directional': 0,
            'directional_winners': 0,
            'fee_eroded_trades': 0,
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
            'expectancy': 0,
            'open_positions': 0
        }
    
    all_trades_count = len(trades)
    open_positions = [t for t in trades if t.get('status') == 'open' or t.get('closed_at') is None]
    closed_trades = [t for t in trades if t.get('closed_at') is not None]
    
    if not closed_trades:
        return {
            'total_trades': all_trades_count,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'win_rate_net': 0,
            'win_rate_directional': 0,
            'directional_winners': 0,
            'fee_eroded_trades': 0,
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
            'expectancy': 0,
            'open_positions': len(open_positions)
        }
    
    pnls = [float(t.get('pnl', 0) or 0) for t in closed_trades]
    winning = [p for p in pnls if p > 0]
    losing = [p for p in pnls if p < 0]
    
    total_trades = len(closed_trades)
    winning_trades = len(winning)
    losing_trades = len(losing)
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    profit_pcts = [float(t.get('pnl_percent', 0) or 0) for t in closed_trades]
    directional_winners = len([p for p in profit_pcts if p > 0])
    directional_win_rate = (directional_winners / total_trades * 100) if total_trades > 0 else 0
    fee_eroded_trades = len([i for i, pct in enumerate(profit_pcts) if pct > 0 and pnls[i] < 0])
    
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
        'total_trades': all_trades_count,
        'closed_trades': len(closed_trades),
        'open_positions': len(open_positions),
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'win_rate': round(win_rate, 2),
        'win_rate_net': round(win_rate, 2),
        'win_rate_directional': round(directional_win_rate, 2),
        'directional_winners': directional_winners,
        'fee_eroded_trades': fee_eroded_trades,
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


def consolidated_trade_metrics(days=10, symbols=None):
    """
    FASE 4 Tracker: Consolidated metrics for BTC/USD and XRP/USD paper trades.
    
    Args:
        days: Number of days to analyze (default 10 for FASE 4 evaluation)
        symbols: List of symbols to track (default ["BTC/USD", "XRP/USD"])
    
    Returns:
        Dict with trade_count, gross_pnl, net_pnl, win_rate, avg_win, avg_loss,
        max_drawdown, kelly_utilization, days_tracked, target_progress
    """
    if symbols is None:
        symbols = ["BTC/USD", "XRP/USD"]
    
    with get_db_connection() as conn:
        if not conn:
            logger.warning("No database connection - cannot fetch FASE 4 metrics")
            return {
                'success': False,
                'error': 'Database not connected',
                'trade_count': 0,
                'symbols': symbols
            }
        
        try:
            cursor = conn.cursor()
            
            placeholders = ','.join(['%s'] * len(symbols))
            cursor.execute(f'''
                SELECT 
                    symbol, side, quantity, entry_price, exit_price,
                    profit_loss, profit_pct, status, opened_at, closed_at
                FROM paper_trading_trades
                WHERE opened_at >= NOW() - INTERVAL '1 day' * %s
                  AND symbol IN ({placeholders})
                  AND status = 'closed'
                ORDER BY opened_at DESC
            ''', (days, *symbols))
            
            rows = cursor.fetchall()
            cursor.close()
            
            trades = []
            wins = []
            losses = []
            
            for row in rows:
                pnl = float(row[5]) if row[5] else 0
                trades.append({
                    'symbol': row[0],
                    'side': row[1],
                    'quantity': float(row[2]) if row[2] else 0,
                    'entry_price': float(row[3]) if row[3] else 0,
                    'exit_price': float(row[4]) if row[4] else 0,
                    'pnl': pnl,
                    'pnl_pct': float(row[6]) if row[6] else 0,
                    'opened_at': row[8],
                    'closed_at': row[9]
                })
                
                if pnl > 0:
                    wins.append(pnl)
                elif pnl < 0:
                    losses.append(pnl)
            
            trade_count = len(trades)
            gross_pnl = sum(t['pnl'] for t in trades)
            win_count = len(wins)
            loss_count = len(losses)
            win_rate = (win_count / trade_count * 100) if trade_count > 0 else 0
            avg_win = sum(wins) / len(wins) if wins else 0
            avg_loss = sum(losses) / len(losses) if losses else 0
            
            running_pnl = 0
            peak = 0
            max_drawdown = 0
            for t in reversed(trades):
                running_pnl += t['pnl']
                if running_pnl > peak:
                    peak = running_pnl
                drawdown = peak - running_pnl
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            target_trades = 50
            target_win_rate = 45.0
            trade_progress = min(100, (trade_count / target_trades) * 100)
            win_rate_progress = min(100, (win_rate / target_win_rate) * 100) if target_win_rate > 0 else 0
            
            logger.info(f"📊 FASE 4 Metrics: {trade_count} trades, {win_rate:.1f}% win rate, ${gross_pnl:.2f} P/L")
            
            return {
                'success': True,
                'symbols': symbols,
                'days_tracked': days,
                'trade_count': trade_count,
                'win_count': win_count,
                'loss_count': loss_count,
                'gross_pnl': round(gross_pnl, 2),
                'net_pnl': round(gross_pnl, 2),
                'win_rate': round(win_rate, 1),
                'avg_win': round(avg_win, 2),
                'avg_loss': round(avg_loss, 2),
                'max_drawdown': round(max_drawdown, 2),
                'target_trades': target_trades,
                'target_win_rate': target_win_rate,
                'trade_progress_pct': round(trade_progress, 1),
                'win_rate_progress_pct': round(win_rate_progress, 1),
                'on_track': trade_count >= 5 and win_rate >= 35.0
            }
            
        except Exception as e:
            logger.error(f"Error fetching FASE 4 metrics: {e}")
            return {
                'success': False,
                'error': str(e),
                'trade_count': 0,
                'symbols': symbols
            }


def get_segmented_expectancy(days=90):
    """
    Operation Lucidity: Calculate expectancy segmented by (hmm_regime, coherence_bucket)
    
    Formula: E = (Win% × AvgWin) - (Loss% × |AvgLoss|)
    
    Args:
        days: Days back to analyze
        
    Returns:
        Dict with segments and their expectancy
    """
    with get_db_connection() as conn:
        if not conn:
            return {
                'success': False,
                'error': 'Database not connected',
                'segments': []
            }
        
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                WITH coherence_buckets AS (
                    SELECT 
                        id,
                        hmm_regime,
                        coherence_score,
                        profit_loss,
                        CASE 
                            WHEN coherence_score IS NULL THEN 'NO_DATA'
                            WHEN coherence_score < 40 THEN 'LOW (<40)'
                            WHEN coherence_score < 70 THEN 'MED (40-70)'
                            ELSE 'HIGH (70+)'
                        END AS coherence_bucket
                    FROM paper_trading_trades
                    WHERE status = 'closed'
                      AND opened_at >= NOW() - INTERVAL '1 day' * %s
                      AND profit_loss IS NOT NULL
                )
                SELECT 
                    COALESCE(hmm_regime, 'UNKNOWN') as regime,
                    coherence_bucket,
                    COUNT(*) as trade_count,
                    COUNT(*) FILTER (WHERE profit_loss > 0) as wins,
                    COUNT(*) FILTER (WHERE profit_loss <= 0) as losses,
                    COALESCE(AVG(profit_loss) FILTER (WHERE profit_loss > 0), 0) as avg_win,
                    COALESCE(AVG(ABS(profit_loss)) FILTER (WHERE profit_loss <= 0), 0) as avg_loss,
                    SUM(profit_loss) as total_pnl
                FROM coherence_buckets
                GROUP BY hmm_regime, coherence_bucket
                ORDER BY 
                    CASE hmm_regime 
                        WHEN 'BULLISH' THEN 1 
                        WHEN 'BEARISH' THEN 2 
                        WHEN 'RANGING' THEN 3 
                        ELSE 4 
                    END,
                    coherence_bucket
            ''', (days,))
            
            rows = cursor.fetchall()
            cursor.close()
            
            segments = []
            best_expectancy = None
            best_segment = None
            
            for row in rows:
                regime = row[0]
                coherence_bucket = row[1]
                trade_count = row[2]
                wins = row[3]
                losses = row[4]
                avg_win = float(row[5]) if row[5] else 0
                avg_loss = float(row[6]) if row[6] else 0
                total_pnl = float(row[7]) if row[7] else 0
                
                win_rate = (wins / trade_count * 100) if trade_count > 0 else 0
                loss_rate = 100 - win_rate
                
                expectancy = (win_rate/100 * avg_win) - (loss_rate/100 * avg_loss)
                
                segment_data = {
                    'regime': regime,
                    'coherence_bucket': coherence_bucket,
                    'trade_count': trade_count,
                    'wins': wins,
                    'losses': losses,
                    'win_rate': round(win_rate, 1),
                    'avg_win': round(avg_win, 2),
                    'avg_loss': round(avg_loss, 2),
                    'expectancy': round(expectancy, 2),
                    'total_pnl': round(total_pnl, 2),
                    'is_profitable': expectancy > 0
                }
                
                segments.append(segment_data)
                
                if trade_count >= 5:
                    if best_expectancy is None or expectancy > best_expectancy:
                        best_expectancy = expectancy
                        best_segment = f"{regime} + {coherence_bucket}"
            
            overall_expectancy = sum(s['expectancy'] * s['trade_count'] for s in segments)
            total_trades = sum(s['trade_count'] for s in segments)
            if total_trades > 0:
                overall_expectancy = overall_expectancy / total_trades
            else:
                overall_expectancy = 0
            
            profitable_segments = [s for s in segments if s['expectancy'] > 0 and s['trade_count'] >= 5]
            
            logger.info(f"📊 LUCIDEZ: {len(segments)} segmentos, best={best_segment}, E={best_expectancy}")
            
            return {
                'success': True,
                'days_analyzed': days,
                'total_trades': total_trades,
                'segment_count': len(segments),
                'segments': segments,
                'best_segment': best_segment,
                'best_expectancy': round(best_expectancy, 2) if best_expectancy is not None else None,
                'overall_expectancy': round(overall_expectancy, 2),
                'profitable_segment_count': len(profitable_segments),
                'recommendation': f"Focus on {best_segment}" if best_segment else "Insufficient data for recommendation"
            }
            
        except Exception as e:
            logger.error(f"Error calculating segmented expectancy: {e}")
            return {
                'success': False,
                'error': str(e),
                'segments': []
            }


def compare_sniper_vs_standard(days=30, min_trades=10):
    """
    Compare Sniper Mode vs Standard Mode performance
    
    V006 (Jan 2, 2026): Modo Sniper comparison query
    
    Args:
        days: Number of days to analyze
        min_trades: Minimum trades per mode for valid comparison
        
    Returns:
        Dict with comparison metrics for both modes
    """
    with get_db_connection() as conn:
        if not conn:
            return {'success': False, 'error': 'No database connection'}
        
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                WITH mode_stats AS (
                    SELECT 
                        COALESCE(strategy_mode, 'STANDARD') as mode,
                        COUNT(*) as total_trades,
                        SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN profit_loss < 0 THEN 1 ELSE 0 END) as losses,
                        SUM(profit_loss) as total_pnl,
                        AVG(profit_loss) as avg_pnl,
                        SUM(CASE WHEN profit_loss > 0 THEN profit_loss ELSE 0 END) as gross_profit,
                        ABS(SUM(CASE WHEN profit_loss < 0 THEN profit_loss ELSE 0 END)) as gross_loss,
                        MIN(profit_loss) as worst_trade,
                        MAX(profit_loss) as best_trade
                    FROM paper_trading_trades
                    WHERE status = 'closed'
                      AND closed_at >= NOW() - INTERVAL '1 day' * %s
                    GROUP BY COALESCE(strategy_mode, 'STANDARD')
                )
                SELECT 
                    mode,
                    total_trades,
                    wins,
                    losses,
                    ROUND((wins::numeric / NULLIF(total_trades, 0) * 100), 1) as win_rate,
                    total_pnl,
                    avg_pnl,
                    CASE WHEN gross_loss > 0 THEN ROUND(gross_profit / gross_loss, 2) ELSE NULL END as profit_factor,
                    worst_trade,
                    best_trade
                FROM mode_stats
                ORDER BY mode
            ''', (days,))
            
            rows = cursor.fetchall()
            cursor.close()
            
            results = {
                'SNIPER': None,
                'STANDARD': None
            }
            
            for row in rows:
                mode = row[0]
                results[mode] = {
                    'total_trades': int(row[1]),
                    'wins': int(row[2]),
                    'losses': int(row[3]),
                    'win_rate': float(row[4]) if row[4] else 0,
                    'total_pnl': float(row[5]) if row[5] else 0,
                    'avg_pnl': float(row[6]) if row[6] else 0,
                    'profit_factor': float(row[7]) if row[7] else 0,
                    'worst_trade': float(row[8]) if row[8] else 0,
                    'best_trade': float(row[9]) if row[9] else 0
                }
            
            sniper = results.get('SNIPER') or {}
            standard = results.get('STANDARD') or {}
            
            sniper_trades = sniper.get('total_trades', 0)
            standard_trades = standard.get('total_trades', 0)
            
            comparison_valid = sniper_trades >= min_trades and standard_trades >= min_trades
            
            winner = None
            if comparison_valid:
                sniper_pf = sniper.get('profit_factor', 0)
                standard_pf = standard.get('profit_factor', 0)
                if sniper_pf > standard_pf:
                    winner = 'SNIPER'
                elif standard_pf > sniper_pf:
                    winner = 'STANDARD'
                else:
                    winner = 'TIE'
            
            logger.info(f"🎯 SNIPER COMPARISON: SNIPER={sniper_trades} trades, STANDARD={standard_trades} trades, winner={winner}")
            
            return {
                'success': True,
                'days_analyzed': days,
                'comparison_valid': comparison_valid,
                'min_trades_required': min_trades,
                'sniper': results.get('SNIPER'),
                'standard': results.get('STANDARD'),
                'winner': winner,
                'recommendation': f"{winner} mode outperforms" if winner and winner != 'TIE' else "Insufficient data or tie"
            }
            
        except Exception as e:
            logger.error(f"Error comparing sniper vs standard: {e}")
            return {
                'success': False,
                'error': str(e)
            }
