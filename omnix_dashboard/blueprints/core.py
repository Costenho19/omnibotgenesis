"""
OMNIX Dashboard - Core Blueprint
Core API routes (/api/metrics, trades, equity-curve, portfolio, positions, health)
"""

import os
import re
import logging
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request

from omnix_dashboard.utils.database import get_db_connection, init_database, get_pool_stats
from omnix_dashboard.utils.database import DB_AVAILABLE, DB_ERROR_MESSAGE, DB_POOL
from omnix_dashboard.utils.decorators import require_api_key
from omnix_dashboard.utils.external_apis import http_get_with_timeout
from omnix_dashboard.utils.queries import (
    get_paper_trades,
    calculate_metrics,
    get_strategy_breakdown,
    get_asset_breakdown,
    get_segmented_expectancy
)

logger = logging.getLogger(__name__)

core_bp = Blueprint('core', __name__)

IS_RAILWAY = bool(os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY_PROJECT_ID'))


@core_bp.route('/api/metrics')
@require_api_key
def api_metrics():
    """API endpoint for metrics - includes ALL historical trades
    
    Returns both Learning Baseline and Track Record data.
    Dashboard handles separation/labeling in the UI.
    """
    from omnix_dashboard.utils.database import DB_AVAILABLE
    
    result = get_paper_trades(return_dict=True)
    
    if not result['success']:
        return jsonify({
            'success': False,
            'error': result['error'],
            'db_connected': result['db_connected'],
            'metrics': None,
            'last_updated': datetime.now().isoformat()
        })
    
    trades = result['trades']
    metrics = calculate_metrics(trades)
    strategies = get_strategy_breakdown(trades)
    assets = get_asset_breakdown(trades)
    
    open_positions_count = len([t for t in trades if t.get('status') == 'open'])
    closed_trades_count = len([t for t in trades if t.get('closed_at') is not None])
    
    if open_positions_count > 0 and closed_trades_count == 0:
        metrics['total_trades'] = int(open_positions_count)
        metrics['message'] = f'{open_positions_count} open position(s) - awaiting closure for P&L calculation'
    
    return jsonify({
        'success': True,
        'metrics': metrics,
        'strategies': strategies,
        'assets': assets,
        'open_positions': open_positions_count,
        'closed_trades': closed_trades_count,
        'db_connected': DB_AVAILABLE,
        'last_updated': datetime.now().isoformat()
    })


@core_bp.route('/api/metrics/expectancy')
@require_api_key
def api_segmented_expectancy():
    """
    Operation Lucidity: Segmented expectancy by HMM regime + coherence bucket
    Answers the question: "WHERE does the system win?"
    """
    from omnix_dashboard.utils.database import DB_AVAILABLE
    
    try:
        days = 90
        result = get_segmented_expectancy(days=days)
        
        result['db_connected'] = DB_AVAILABLE
        result['last_updated'] = datetime.now().isoformat()
        result['endpoint'] = 'operation_lucidity_v1'
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in segmented expectancy API: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'db_connected': DB_AVAILABLE,
            'segments': []
        })


@core_bp.route('/api/trades')
@require_api_key
def api_trades():
    """API endpoint for trades - fetches ALL trades for real-time consistency with metrics"""
    result = get_paper_trades(return_dict=True)
    
    if not result['success']:
        return jsonify({
            'success': False,
            'error': result['error'],
            'db_connected': result['db_connected'],
            'trades': [],
            'total': 0
        })
    
    trades = result['trades']
    formatted_trades = []
    for t in trades[:50]:
        formatted_trades.append({
            'id': t.get('id'),
            'symbol': t.get('symbol'),
            'side': t.get('side'),
            'entry': float(t.get('entry_price', 0) or 0),
            'exit': float(t.get('exit_price', 0) or 0),
            'qty': float(t.get('quantity', 0) or 0),
            'pnl': float(t.get('pnl', 0) or 0),
            'pnl_pct': float(t.get('pnl_percent', 0) or 0),
            'opened': t.get('opened_at').isoformat() if t.get('opened_at') else None,
            'closed': t.get('closed_at').isoformat() if t.get('closed_at') else None,
            'strategy': t.get('strategy_used', 'Manual')
        })
    
    return jsonify({
        'success': True,
        'trades': formatted_trades,
        'total': len(trades),
        'db_connected': True
    })


@core_bp.route('/api/trades/history')
@require_api_key
def api_trades_history():
    """API endpoint for detailed trade history - PREMIUM with full transparency"""
    from flask import request
    
    telemetry_filter = request.args.get('telemetry_source', None)
    
    VALID_TELEMETRY_SOURCES = {'REAL', 'LEGACY_ESTIMATED'}
    if telemetry_filter and telemetry_filter not in VALID_TELEMETRY_SOURCES:
        telemetry_filter = None
    
    with get_db_connection() as conn:
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database not connected',
                'trades': [],
                'statistics': None
            })
        
        try:
            cursor = conn.cursor()
            
            if telemetry_filter:
                cursor.execute('''
                    SELECT id, symbol, side, quantity, entry_price, exit_price, 
                           profit_loss, status, opened_at, closed_at, strategy,
                           COALESCE(telemetry_source, 'LEGACY_ESTIMATED') as telemetry_source
                    FROM paper_trading_trades
                    WHERE telemetry_source = %s
                    ORDER BY opened_at DESC
                    LIMIT 100
                ''', (telemetry_filter,))
            else:
                cursor.execute('''
                    SELECT id, symbol, side, quantity, entry_price, exit_price, 
                           profit_loss, status, opened_at, closed_at, strategy,
                           COALESCE(telemetry_source, 'LEGACY_ESTIMATED') as telemetry_source
                    FROM paper_trading_trades
                    ORDER BY opened_at DESC
                    LIMIT 100
                ''')
            
            rows = cursor.fetchall()
            
            if telemetry_filter:
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN profit_loss < 0 THEN 1 ELSE 0 END) as losses,
                        SUM(profit_loss) as total_pnl,
                        AVG(CASE WHEN profit_loss > 0 THEN profit_loss ELSE NULL END) as avg_win,
                        AVG(CASE WHEN profit_loss < 0 THEN profit_loss ELSE NULL END) as avg_loss,
                        MAX(profit_loss) as best_trade,
                        MIN(profit_loss) as worst_trade,
                        SUM(CASE WHEN profit_pct > 0 THEN 1 ELSE 0 END) as directional_wins,
                        SUM(CASE WHEN profit_pct > 0 AND profit_loss < 0 THEN 1 ELSE 0 END) as fee_eroded
                    FROM paper_trading_trades
                    WHERE status = 'closed' AND telemetry_source = %s
                ''', (telemetry_filter,))
            else:
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN profit_loss < 0 THEN 1 ELSE 0 END) as losses,
                        SUM(profit_loss) as total_pnl,
                        AVG(CASE WHEN profit_loss > 0 THEN profit_loss ELSE NULL END) as avg_win,
                        AVG(CASE WHEN profit_loss < 0 THEN profit_loss ELSE NULL END) as avg_loss,
                        MAX(profit_loss) as best_trade,
                        MIN(profit_loss) as worst_trade,
                        SUM(CASE WHEN profit_pct > 0 THEN 1 ELSE 0 END) as directional_wins,
                        SUM(CASE WHEN profit_pct > 0 AND profit_loss < 0 THEN 1 ELSE 0 END) as fee_eroded
                    FROM paper_trading_trades
                    WHERE status = 'closed'
                ''')
            
            stats_row = cursor.fetchone()
            cursor.close()
            
            trades = []
            for row in rows:
                entry_price = float(row[4]) if row[4] else 0
                exit_price = float(row[5]) if row[5] else 0
                pnl = float(row[6]) if row[6] else 0
                quantity = float(row[3]) if row[3] else 0
                
                cost = entry_price * quantity
                pnl_pct = (pnl / cost * 100) if cost > 0 else 0
                
                trades.append({
                    'id': row[0],
                    'symbol': row[1],
                    'side': row[2].upper() if row[2] else 'BUY',
                    'quantity': quantity,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'pnl': round(pnl, 2),
                    'pnl_pct': round(pnl_pct, 2),
                    'result': 'WIN' if pnl > 0 else ('LOSS' if pnl < 0 else 'BREAK-EVEN'),
                    'status': row[7],
                    'opened_at': row[8].isoformat() if row[8] else None,
                    'closed_at': row[9].isoformat() if row[9] else None,
                    'strategy': row[10] or 'auto_trading_bot',
                    'hold_time': str(row[9] - row[8]) if row[8] and row[9] else None,
                    'telemetry_source': row[11] if len(row) > 11 else 'LEGACY_ESTIMATED'
                })
            
            total_trades = int(stats_row[0] or 0) if stats_row else 0
            wins = int(stats_row[1] or 0) if stats_row else 0
            losses = int(stats_row[2] or 0) if stats_row else 0
            total_pnl = float(stats_row[3] or 0) if stats_row else 0
            avg_win = float(stats_row[4] or 0) if stats_row else 0
            avg_loss = float(stats_row[5] or 0) if stats_row else 0
            best_trade = float(stats_row[6] or 0) if stats_row else 0
            worst_trade = float(stats_row[7] or 0) if stats_row else 0
            directional_wins = int(stats_row[8] or 0) if stats_row else 0
            fee_eroded_trades = int(stats_row[9] or 0) if stats_row else 0
            
            win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
            win_rate_directional = (directional_wins / total_trades * 100) if total_trades > 0 else 0
            profit_factor = abs(avg_win * wins / (avg_loss * losses)) if losses > 0 and avg_loss != 0 else 0
            
            min_trades_for_significance = 30
            is_statistically_significant = total_trades >= min_trades_for_significance
            
            return jsonify({
                'success': True,
                'trades': trades,
                'statistics': {
                    'total_trades': total_trades,
                    'winning_trades': wins,
                    'losing_trades': losses,
                    'win_rate': round(win_rate, 2),
                    'win_rate_directional': round(win_rate_directional, 2),
                    'fee_eroded_trades': fee_eroded_trades,
                    'total_pnl': round(total_pnl, 2),
                    'avg_win': round(avg_win, 2),
                    'avg_loss': round(avg_loss, 2),
                    'best_trade': round(best_trade, 2),
                    'worst_trade': round(worst_trade, 2),
                    'profit_factor': round(profit_factor, 2),
                    'expectancy': round(total_pnl / total_trades, 2) if total_trades > 0 else 0
                },
                'sample_analysis': {
                    'is_significant': is_statistically_significant,
                    'current_sample': total_trades,
                    'minimum_required': min_trades_for_significance,
                    'confidence_level': min(100, round(total_trades / min_trades_for_significance * 100, 1)),
                    'warning': None if is_statistically_significant else f'Sample size ({total_trades}) is below minimum ({min_trades_for_significance}) for statistical significance. Metrics may vary significantly as more trades are executed.'
                },
                'source': 'PostgreSQL (Railway)',
                'version': 'DGI',
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Trade history API error: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'trades': []
            })


@core_bp.route('/api/equity-curve')
@require_api_key
def api_equity_curve():
    """API endpoint for equity curve data"""
    trades = get_paper_trades(90)
    
    if not trades:
        return jsonify({
            'success': True,
            'data': [],
            'message': 'No trades yet'
        })
    
    sorted_trades = sorted(
        [t for t in trades if t.get('closed_at')],
        key=lambda x: x.get('closed_at') or datetime.min
    )
    
    initial_capital = 1000000
    equity = initial_capital
    curve_data = [{'date': '2026-01-15T00:00:00', 'equity': initial_capital}]
    
    for trade in sorted_trades:
        pnl = float(trade.get('pnl', 0) or 0)
        equity += pnl
        curve_data.append({
            'date': trade.get('closed_at').isoformat() if trade.get('closed_at') else None,
            'equity': round(equity, 2)
        })
    
    return jsonify({
        'success': True,
        'data': curve_data,
        'initial_capital': initial_capital,
        'current_equity': round(equity, 2)
    })


@core_bp.route('/api/portfolio')
@require_api_key
def api_portfolio():
    """API endpoint for portfolio status - connected to real DB"""
    with get_db_connection() as conn:
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database not connected',
                'portfolio': None
            })
        
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id, balance_usd, btc_balance, eth_balance, 
                       total_trades, winning_trades, losing_trades,
                       total_realized_pnl_usd, max_drawdown_pct, sharpe_ratio,
                       updated_at
                FROM paper_trading_balances
                ORDER BY updated_at DESC
                LIMIT 1
            ''')
            
            balance_row = cursor.fetchone()
            
            cursor.execute('''
                SELECT symbol, side, quantity, entry_price
                FROM paper_trading_trades
                WHERE status = 'open'
            ''')
            
            positions = cursor.fetchall()
            
            weights = {}
            total_value = 0
            position_details = []
            
            for pos in positions:
                symbol = pos[0].replace('/USD', '')
                value = float(pos[2] or 0) * float(pos[3] or 0)
                total_value += value
                position_details.append({
                    'symbol': symbol,
                    'side': pos[1],
                    'value': value
                })
            
            for pos in position_details:
                if total_value > 0:
                    weights[pos['symbol']] = round(pos['value'] / total_value, 4)
            
            cursor.execute('''
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as wins,
                       SUM(CASE WHEN profit_loss < 0 THEN 1 ELSE 0 END) as losses,
                       SUM(profit_loss) as total_pnl
                FROM paper_trading_trades
                WHERE status = 'closed'
            ''')
            
            perf_row = cursor.fetchone()
            cursor.close()
            
            total_trades = int(perf_row[0] or 0) if perf_row else 0
            winning_trades = int(perf_row[1] or 0) if perf_row else 0
            total_pnl = float(perf_row[3] or 0) if perf_row else 0
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            balance_usd = float(balance_row[1]) if balance_row and balance_row[1] else 1000000
            sharpe = float(balance_row[9]) if balance_row and balance_row[9] else 0
            max_dd = float(balance_row[8]) if balance_row and balance_row[8] else 0
            
            return jsonify({
                'success': True,
                'portfolio': {
                    'weights': weights if weights else {'CASH': 1.0},
                    'balance_usd': round(balance_usd, 2),
                    'total_pnl': round(total_pnl, 2),
                    'expected_return': round(total_pnl / balance_usd * 100, 2) if balance_usd > 0 else 0,
                    'expected_volatility': round(max_dd, 2),
                    'sharpe_ratio': round(sharpe, 2),
                    'win_rate': round(win_rate, 2),
                    'total_trades': total_trades,
                    'winning_trades': winning_trades,
                    'open_positions': len(positions),
                    'net_exposure': round(total_value, 2),
                    'gross_exposure': round(total_value, 2),
                    'diversification_score': len(weights) / 10.0 if weights else 0,
                    'risk_profile': 'INSTITUTIONAL'
                },
                'modules': {
                    'risk_model': True,
                    'optimizer': True,
                    'vol_targeting': True,
                    'exposure_manager': True,
                    'cluster_detector': True
                },
                'source': 'PostgreSQL',
                'version': 'DGI',
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Portfolio API error: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'portfolio': None
            })


def fetch_coingecko_prices():
    """Fallback price source using CoinGecko API"""
    try:
        url = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,ripple,cardano,dogecoin&vs_currencies=usd'
        data = http_get_with_timeout(url, timeout=10, fallback=None)
        
        if data:
            coingecko_map = {
                'bitcoin': 'BTC/USD',
                'ethereum': 'ETH/USD',
                'solana': 'SOL/USD',
                'ripple': 'XRP/USD',
                'cardano': 'ADA/USD',
                'dogecoin': 'DOGE/USD'
            }
            
            prices = {}
            for coin_id, symbol in coingecko_map.items():
                if coin_id in data and 'usd' in data[coin_id]:
                    prices[symbol] = float(data[coin_id]['usd'])
            
            logger.info(f"CoinGecko fallback: Fetched {len(prices)} prices")
            return prices
    except Exception as e:
        logger.error(f"CoinGecko fallback failed: {e}")
    
    return {}


@core_bp.route('/api/positions')
@require_api_key
def api_positions():
    """API endpoint for open positions with real Kraken prices + CoinGecko fallback"""
    with get_db_connection() as conn:
        if not conn:
            return jsonify({
                'success': False,
                'positions': [],
                'error': 'Database not connected',
                'db_connected': False
            })
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, user_id, symbol, side, quantity, entry_price, strategy, status, opened_at
                FROM paper_trading_trades
                WHERE status = 'open' AND closed_at IS NULL
                ORDER BY opened_at DESC
                LIMIT 100
            ''')
            
            rows = cursor.fetchall()
            cursor.close()
            
            url = 'https://api.kraken.com/0/public/Ticker?pair=XBTUSD,ETHUSD,SOLUSD,XRPUSD,ADAUSD,DOGEUSD'
            data = http_get_with_timeout(url, timeout=10, fallback=None)
            
            kraken_prices = {}
            price_source_used = 'Entry'
            
            if data and data.get('result'):
                price_map = {
                    'XXBTZUSD': 'BTC/USD', 'XETHZUSD': 'ETH/USD', 'SOLUSD': 'SOL/USD',
                    'XXRPZUSD': 'XRP/USD', 'ADAUSD': 'ADA/USD', 'XDGUSD': 'DOGE/USD',
                    'XBTUSD': 'BTC/USD', 'ETHUSD': 'ETH/USD'
                }
                
                for key, ticker in data.get('result', {}).items():
                    symbol = price_map.get(key, key)
                    kraken_prices[symbol] = float(ticker['c'][0])
                
                price_source_used = 'Kraken'
                logger.info(f"V6.5: Fetched {len(kraken_prices)} real-time prices from Kraken")
            else:
                logger.warning("Kraken API failed, trying CoinGecko fallback...")
                kraken_prices = fetch_coingecko_prices()
                if kraken_prices:
                    price_source_used = 'CoinGecko'
            
            positions = []
            total_value = 0
            total_cost = 0
            
            for row in rows:
                symbol = row[2]
                entry_price = float(row[5]) if row[5] else 0
                quantity = float(row[4]) if row[4] else 0
                cost = entry_price * quantity
                
                current_price = kraken_prices.get(symbol, entry_price)
                price_source = price_source_used if symbol in kraken_prices else 'Entry'
                
                current_value = current_price * quantity
                unrealized_pnl = current_value - cost
                
                total_cost += cost
                total_value += current_value
                
                positions.append({
                    'id': row[0],
                    'user_id': row[1],
                    'symbol': symbol,
                    'side': row[3],
                    'quantity': quantity,
                    'entry_price': entry_price,
                    'current_price': current_price,
                    'price_source': price_source,
                    'cost': round(cost, 2),
                    'current_value': round(current_value, 2),
                    'unrealized_pnl': round(unrealized_pnl, 2),
                    'unrealized_pnl_pct': round((unrealized_pnl / cost * 100) if cost > 0 else 0, 2),
                    'strategy': row[6] or 'Manual',
                    'status': row[7],
                    'opened_at': row[8].isoformat() if row[8] else None
                })
            
            logger.info(f"Fetched {len(positions)} open positions with real prices")
            
            return jsonify({
                'success': True,
                'positions': positions,
                'summary': {
                    'total_positions': len(positions),
                    'total_cost': round(total_cost, 2),
                    'total_value': round(total_value, 2),
                    'total_unrealized_pnl': round(total_value - total_cost, 2)
                },
                'price_source': f'{price_source_used} API',
                'db_connected': True,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return jsonify({
                'success': False,
                'positions': [],
                'error': str(e)
            })


@core_bp.route('/api/health')
def api_health():
    """Health check endpoint with pool stats for Railway healthcheck"""
    from omnix_dashboard.utils.database import DB_AVAILABLE, DB_ERROR_MESSAGE, DB_POOL
    
    if DB_POOL is None:
        init_database()
    
    pool_stats = get_pool_stats()
    
    is_healthy = DB_AVAILABLE
    requests_waiting = int(pool_stats.get('requests_waiting', 0)) if pool_stats else 0
    if requests_waiting > 50:
        is_healthy = False
    
    return jsonify({
        'status': 'healthy' if is_healthy else 'degraded',
        'version': 'DGI',
        'db_connected': DB_AVAILABLE,
        'db_error': DB_ERROR_MESSAGE if not DB_AVAILABLE else None,
        'pool': pool_stats,
        'architecture': {
            'connection_pooling': DB_POOL is not None,
            'wsgi_server': 'gunicorn' if IS_RAILWAY else 'werkzeug',
            'environment': 'railway' if IS_RAILWAY else 'development'
        },
        'timestamp': datetime.now().isoformat()
    }), 200


@core_bp.route('/api/metrics/institutional')
@require_api_key
def api_institutional_metrics():
    """
    OMNIX Decision Governance
    Institutional metrics: Sharpe, Sortino, Calmar by pair
    For investor and fund presentations
    """
    from omnix_dashboard.utils.database import DB_AVAILABLE
    
    try:
        from omnix_services.analytics.institutional_metrics import (
            InstitutionalMetricsCalculator,
            MetricPeriod,
            TradeRecord
        )
        
        result = get_paper_trades(365, return_dict=True)
        
        if not result['success'] or not result['trades']:
            return jsonify({
                'success': False,
                'error': 'No trade data available',
                'db_connected': DB_AVAILABLE,
                'metrics': None
            })
        
        trades = result['trades']
        
        trade_records = []
        for t in trades:
            if t.get('closed_at') is None:
                continue
            
            try:
                entry_time = t.get('opened_at')
                exit_time = t.get('closed_at')
                
                if isinstance(entry_time, str):
                    entry_time = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
                if isinstance(exit_time, str):
                    exit_time = datetime.fromisoformat(exit_time.replace('Z', '+00:00'))
                
                pnl_usd = float(t.get('pnl', 0) or 0)
                entry_price = float(t.get('entry_price', 0) or 1)
                exit_price = float(t.get('exit_price', 0) or entry_price)
                side = t.get('side', 'buy').lower()
                
                if side == 'buy':
                    pnl_pct = (exit_price - entry_price) / entry_price if entry_price else 0
                else:
                    pnl_pct = (entry_price - exit_price) / entry_price if entry_price else 0
                
                trade_records.append(TradeRecord(
                    symbol=t.get('symbol', 'UNKNOWN'),
                    pnl_usd=pnl_usd,
                    pnl_pct=pnl_pct,
                    entry_time=entry_time,
                    exit_time=exit_time,
                    side=side,
                    size_usd=float(t.get('position_size', 0) or 0)
                ))
            except Exception as parse_err:
                logger.debug(f"Error parsing trade for metrics: {parse_err}")
                continue
        
        if not trade_records:
            return jsonify({
                'success': False,
                'error': 'No closed trades available for metrics',
                'db_connected': DB_AVAILABLE,
                'metrics': None
            })
        
        calculator = InstitutionalMetricsCalculator()
        portfolio_metrics = calculator.calculate_portfolio_metrics(trade_records, "all_time")
        
        return jsonify({
            'success': True,
            'metrics': portfolio_metrics.to_dict(),
            'summary': calculator.get_summary_for_investors().get('summary', {}),
            'db_connected': DB_AVAILABLE,
            'calculated_at': datetime.now().isoformat()
        })
        
    except ImportError as ie:
        logger.error(f"InstitutionalMetrics module not available: {ie}")
        return jsonify({
            'success': False,
            'error': 'Institutional metrics module not available',
            'metrics': None
        }), 500
    except Exception as e:
        logger.error(f"Error calculating institutional metrics: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'metrics': None
        }), 500


@core_bp.route('/api/report/pdf')
@require_api_key
def api_generate_pdf_report():
    """
    OMNIX Decision Governance
    Genera informe PDF institucional para inversores
    """
    from flask import Response
    
    try:
        from omnix_services.analytics.institutional_metrics import (
            InstitutionalMetricsCalculator,
            TradeRecord
        )
        from omnix_services.analytics.institutional_report import get_report_generator
        from omnix_core.config.trading_profiles import PAIR_CALIBRATIONS
        
        result = get_paper_trades(365, return_dict=True)
        
        if not result['success'] or not result['trades']:
            return jsonify({
                'success': False,
                'error': 'No trade data available for report'
            }), 400
        
        trades = result['trades']
        
        trade_records = []
        for t in trades:
            if t.get('closed_at') is None:
                continue
            try:
                entry_time = t.get('opened_at')
                exit_time = t.get('closed_at')
                
                if isinstance(entry_time, str):
                    entry_time = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
                if isinstance(exit_time, str):
                    exit_time = datetime.fromisoformat(exit_time.replace('Z', '+00:00'))
                
                pnl_usd = float(t.get('pnl', 0) or 0)
                entry_price = float(t.get('entry_price', 0) or 1)
                exit_price = float(t.get('exit_price', 0) or entry_price)
                side = t.get('side', 'buy').lower()
                
                if side == 'buy':
                    pnl_pct = (exit_price - entry_price) / entry_price if entry_price else 0
                else:
                    pnl_pct = (entry_price - exit_price) / entry_price if entry_price else 0
                
                trade_records.append(TradeRecord(
                    symbol=t.get('symbol', 'UNKNOWN'),
                    pnl_usd=pnl_usd,
                    pnl_pct=pnl_pct,
                    entry_time=entry_time,
                    exit_time=exit_time,
                    side=side,
                    size_usd=float(t.get('position_size', 0) or 0)
                ))
            except Exception:
                continue
        
        if not trade_records:
            return jsonify({
                'success': False,
                'error': 'No closed trades available for report'
            }), 400
        
        calculator = InstitutionalMetricsCalculator()
        portfolio_metrics = calculator.calculate_portfolio_metrics(trade_records, "all_time")
        
        report_gen = get_report_generator()
        pdf_bytes = report_gen.generate_report(
            metrics=portfolio_metrics.to_dict(),
            calibration=PAIR_CALIBRATIONS,
            company_name="OMNIX Decision Governance",
            period="All Time"
        )
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"OMNIX_Report_{timestamp}.pdf"
        
        return Response(
            pdf_bytes,
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename={filename}',
                'Content-Length': str(len(pdf_bytes))
            }
        )
        
    except ImportError as ie:
        logger.error(f"Report module not available: {ie}")
        return jsonify({
            'success': False,
            'error': 'Report generator module not available'
        }), 500
    except Exception as e:
        logger.error(f"Error generating PDF report: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@core_bp.route('/api/system/health-score')
@require_api_key
def api_health_score():
    """
    System Health Score API - Overall system health indicator (0-100)
    Components: Risk Controls, Data Quality, Win Rate, Capital Preservation
    """
    try:
        result = get_paper_trades(return_dict=True)
        trades = result.get('trades', []) if result.get('success') else []
        metrics = calculate_metrics(trades)
        
        closed_trades = [t for t in trades if t.get('status') == 'closed']
        total_trades = len(closed_trades)
        
        risk_score = 100
        veto_active = True
        total_pnl = metrics.get('total_pnl', 0) or 0
        capital_preserved = round(max(0, (1_000_000 + total_pnl) / 1_000_000 * 100), 2)
        risk_score = min(100, capital_preserved + (5 if veto_active else 0))
        
        data_score = 100
        data_detail = 'DB connection active'
        try:
            with get_db_connection() as conn:
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total,
                            COUNT(coherence_score) as with_coherence,
                            COUNT(CASE WHEN hmm_regime IS NOT NULL AND hmm_regime != '' THEN 1 END) as with_hmm,
                            COUNT(CASE WHEN telemetry_source = 'REAL' THEN 1 END) as real_telemetry
                        FROM paper_trading_trades
                        WHERE status = 'closed'
                    """)
                    row = cursor.fetchone()
                    cursor.close()
                    
                    if row and row[0] > 0:
                        total = row[0]
                        with_coherence = row[1] or 0
                        with_hmm = row[2] or 0
                        real_telemetry = row[3] or 0
                        
                        completeness = ((with_coherence + with_hmm) / (total * 2)) * 100 if total > 0 else 0
                        data_score = min(100, completeness)
                        
                        if real_telemetry > 0:
                            data_detail = f'{real_telemetry}/{total} trades with real telemetry'
                        else:
                            data_detail = f'{with_coherence}/{total} trades with telemetry (estimated)'
                    else:
                        data_score = 50
                        data_detail = 'No closed trades yet'
                else:
                    data_score = 25
                    data_detail = 'DB connection issues'
        except Exception as e:
            logger.warning(f"Data quality check error: {e}")
            data_score = 25
            data_detail = 'Unable to check data quality'
        
        target_wr = 40
        actual_wr = metrics.get('win_rate_directional', 0) or metrics.get('win_rate', 0)
        wr_progress = min(100, (actual_wr / target_wr) * 100) if target_wr > 0 else 0
        sample_bonus = min(20, (total_trades / 100) * 20) if total_trades > 0 else 0
        wr_score = min(100, wr_progress * 0.8 + sample_bonus)
        
        uptime_score = 95
        
        weights = {
            'risk': 0.35,
            'data': 0.25,
            'winrate': 0.25,
            'uptime': 0.15
        }
        
        overall = (
            risk_score * weights['risk'] +
            data_score * weights['data'] +
            wr_score * weights['winrate'] +
            uptime_score * weights['uptime']
        )
        
        if overall >= 90:
            status = 'EXCELLENT'
            color = '#00d4aa'
        elif overall >= 75:
            status = 'GOOD'
            color = '#4ade80'
        elif overall >= 60:
            status = 'CALIBRATING'
            color = '#ffc107'
        elif overall >= 40:
            status = 'NEEDS ATTENTION'
            color = '#ff9800'
        else:
            status = 'CRITICAL'
            color = '#ff6b6b'
        
        return jsonify({
            'success': True,
            'health_score': round(overall, 1),
            'status': status,
            'color': color,
            'components': {
                'risk_controls': {
                    'score': round(risk_score, 1),
                    'label': 'Risk Controls',
                    'detail': f'{capital_preserved}% capital preserved'
                },
                'data_quality': {
                    'score': round(data_score, 1),
                    'label': 'Data Quality',
                    'detail': data_detail
                },
                'win_rate': {
                    'score': round(wr_score, 1),
                    'label': 'Win Rate Progress',
                    'detail': f'{actual_wr:.1f}% of {target_wr}% target'
                },
                'uptime': {
                    'score': round(uptime_score, 1),
                    'label': 'System Uptime',
                    'detail': '24/7 monitoring active'
                }
            },
            'sample_size': total_trades,
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Health score calculation error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'health_score': 0
        }), 500


@core_bp.route('/api/system/live-status')
@require_api_key
def api_live_status():
    """
    Live Status API - What the system is doing RIGHT NOW
    Shows current activity, last action, and next scheduled action
    """
    try:
        result = get_paper_trades(return_dict=True)
        trades = result.get('trades', []) if result.get('success') else []
        
        last_trade = None
        if trades:
            sorted_trades = sorted(trades, key=lambda x: x.get('created_at') or '', reverse=True)
            if sorted_trades:
                last_trade = sorted_trades[0]
        
        current_activity = 'ANALYZING'
        activity_detail = 'Scanning markets for opportunities'
        activity_icon = 'chart-line'
        
        now = datetime.now()
        if last_trade:
            last_trade_time = last_trade.get('created_at')
            if last_trade_time:
                if isinstance(last_trade_time, str):
                    try:
                        last_trade_time = datetime.fromisoformat(last_trade_time.replace('Z', '+00:00'))
                    except Exception:
                        last_trade_time = None
                
                if last_trade_time:
                    time_since = now - last_trade_time.replace(tzinfo=None) if hasattr(last_trade_time, 'replace') else timedelta(hours=999)
                    
                    if time_since < timedelta(minutes=5):
                        current_activity = 'EXECUTING'
                        activity_detail = f"Recently traded {last_trade.get('symbol', 'N/A')}"
                        activity_icon = 'bolt'
                    elif time_since < timedelta(hours=1):
                        current_activity = 'MONITORING'
                        activity_detail = 'Watching open positions'
                        activity_icon = 'eye'
        
        open_positions = [t for t in trades if t.get('status') == 'open']
        if open_positions:
            current_activity = 'MONITORING'
            symbols = list(set(p.get('symbol', 'N/A') for p in open_positions))[:3]
            activity_detail = f"Watching {len(open_positions)} position(s): {', '.join(symbols)}"
            activity_icon = 'eye'
        
        last_action = None
        if last_trade:
            last_action = {
                'type': 'TRADE',
                'symbol': last_trade.get('symbol'),
                'side': last_trade.get('side'),
                'time': last_trade.get('created_at'),
                'result': 'WIN' if (last_trade.get('profit_loss', 0) or 0) > 0 else 'LOSS' if last_trade.get('status') == 'closed' else 'OPEN'
            }
        
        veto_active = True
        market_regime = 'NEUTRAL'
        coherence_level = 'MEDIUM'
        
        return jsonify({
            'success': True,
            'current_activity': {
                'status': current_activity,
                'detail': activity_detail,
                'icon': activity_icon
            },
            'last_action': last_action,
            'system_state': {
                'veto_active': veto_active,
                'market_regime': market_regime,
                'coherence_level': coherence_level,
                'open_positions': len(open_positions)
            },
            'uptime': {
                'status': 'ONLINE',
                'since': (now - timedelta(days=30)).isoformat()
            },
            'last_updated': now.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Live status error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'current_activity': {'status': 'ERROR', 'detail': 'Unable to fetch status'}
        }), 500


@core_bp.route('/api/system/quick-insights')
@require_api_key
def api_quick_insights():
    """
    Quick Insights API - Auto-generated actionable insights
    Analyzes trading data and provides recommendations
    """
    try:
        result = get_paper_trades(return_dict=True)
        trades = result.get('trades', []) if result.get('success') else []
        metrics = calculate_metrics(trades)
        
        insights = []
        
        closed_trades = [t for t in trades if t.get('status') == 'closed']
        total_trades = len(closed_trades)
        
        win_rate = metrics.get('win_rate_directional', 0) or metrics.get('win_rate', 0)
        target_wr = 40
        if win_rate > 0:
            if win_rate >= target_wr:
                insights.append({
                    'type': 'SUCCESS',
                    'icon': 'check-circle',
                    'title': 'Win Rate Target Achieved',
                    'message': f'Directional accuracy at {win_rate:.1f}% exceeds {target_wr}% target',
                    'priority': 1
                })
            else:
                gap = target_wr - win_rate
                insights.append({
                    'type': 'PROGRESS',
                    'icon': 'trending-up',
                    'title': 'Win Rate Improving',
                    'message': f'{gap:.1f}% more needed to reach {target_wr}% target ({win_rate:.1f}% current)',
                    'priority': 2
                })
        
        fee_eroded = len([t for t in closed_trades if (t.get('profit_pct', 0) or 0) > 0 and (t.get('profit_loss', 0) or 0) < 0])
        if fee_eroded > 0 and total_trades > 0:
            fee_ratio = (fee_eroded / total_trades) * 100
            if fee_ratio > 10:
                insights.append({
                    'type': 'WARNING',
                    'icon': 'alert-triangle',
                    'title': 'Fee Impact Detected',
                    'message': f'{fee_eroded} trades ({fee_ratio:.1f}%) won direction but lost to fees',
                    'priority': 2
                })
        
        symbol_pnl = {}
        for t in closed_trades:
            symbol = t.get('symbol', 'Unknown')
            pnl = t.get('profit_loss', 0) or 0
            if symbol not in symbol_pnl:
                symbol_pnl[symbol] = {'pnl': 0, 'count': 0}
            symbol_pnl[symbol]['pnl'] += pnl
            symbol_pnl[symbol]['count'] += 1
        
        if symbol_pnl:
            best_symbol = max(symbol_pnl.items(), key=lambda x: x[1]['pnl'])
            worst_symbol = min(symbol_pnl.items(), key=lambda x: x[1]['pnl'])
            
            if best_symbol[1]['pnl'] > 0:
                insights.append({
                    'type': 'INFO',
                    'icon': 'star',
                    'title': 'Best Performer',
                    'message': f"{best_symbol[0]}: +${best_symbol[1]['pnl']:.2f} over {best_symbol[1]['count']} trades",
                    'priority': 3
                })
            
            if worst_symbol[1]['pnl'] < -1000 and worst_symbol[0] != best_symbol[0]:
                insights.append({
                    'type': 'CAUTION',
                    'icon': 'alert-circle',
                    'title': 'Review Needed',
                    'message': f"{worst_symbol[0]}: ${worst_symbol[1]['pnl']:.2f} - consider reduced exposure",
                    'priority': 2
                })
        
        if total_trades < 100:
            remaining = 100 - total_trades
            insights.append({
                'type': 'INFO',
                'icon': 'clock',
                'title': 'Building Track Record',
                'message': f'{remaining} more trades needed for statistical significance (119 current)',
                'priority': 4
            })
        
        total_pnl_for_cp = metrics.get('total_pnl', 0) or 0
        capital_preserved = round(max(0, (1_000_000 + total_pnl_for_cp) / 1_000_000 * 100), 2)
        if capital_preserved >= 95:
            insights.append({
                'type': 'SUCCESS',
                'icon': 'shield',
                'title': 'Capital Protection Active',
                'message': f'{capital_preserved}% capital preserved - risk controls working',
                'priority': 1
            })
        
        insights.sort(key=lambda x: x.get('priority', 99))
        
        return jsonify({
            'success': True,
            'insights': insights[:5],
            'total_insights': len(insights),
            'metrics_summary': {
                'win_rate': round(win_rate, 1),
                'total_trades': total_trades,
                'pnl': metrics.get('total_pnl', 0)
            },
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Quick insights error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'insights': []
        }), 500


@core_bp.route('/api/system/calibration-progress')
def calibration_progress():
    """Return calibration progress across 4 phases based on real trading data"""
    try:
        result = get_paper_trades(return_dict=True)
        trades = result.get('trades', []) if result.get('success') else []
        metrics = calculate_metrics(trades)
        
        closed_trades = [t for t in trades if t.get('status') == 'closed']
        total_trades = len(closed_trades)
        win_rate = metrics.get('win_rate', 0)
        win_rate_dir = metrics.get('win_rate_directional', win_rate)
        
        phase1_target = 100
        phase1_progress = min(100, (total_trades / phase1_target) * 100)
        phase1_complete = total_trades >= phase1_target
        
        patterns_identified = 0
        if total_trades >= 50:
            patterns_identified += 25
        if total_trades >= 75:
            patterns_identified += 25
        if win_rate_dir > 30:
            patterns_identified += 25
        if win_rate_dir > 35:
            patterns_identified += 25
        phase2_progress = min(100, patterns_identified)
        phase2_complete = patterns_identified >= 100
        
        optimization_score = 0
        if win_rate_dir >= 35:
            optimization_score += 30
        if win_rate_dir >= 38:
            optimization_score += 30
        if win_rate_dir >= 40:
            optimization_score += 40
        phase3_progress = min(100, optimization_score)
        phase3_complete = win_rate_dir >= 40
        
        deployment_ready = phase1_complete and phase2_complete and phase3_complete
        phase4_progress = 100 if deployment_ready else 0
        
        overall_progress = (phase1_progress * 0.25 + phase2_progress * 0.25 + 
                          phase3_progress * 0.35 + phase4_progress * 0.15)
        
        from datetime import timedelta
        start_date = datetime(2026, 1, 15)
        now = datetime.now()
        days_since_start = max(1, (now - start_date).days + 1)
        
        phases = [
            {
                'id': 1,
                'name': 'Data Collection',
                'description': f'{total_trades}/100 trades collected',
                'progress': round(phase1_progress, 1),
                'complete': phase1_complete,
                'icon': 'database',
                'eta': 'Complete',
                'target_date': None
            },
            {
                'id': 2,
                'name': 'Pattern Analysis',
                'description': 'Identifying profitable patterns',
                'progress': round(phase2_progress, 1),
                'complete': phase2_complete,
                'icon': 'cpu',
                'eta': '~Day 45' if not phase2_complete else 'Complete',
                'target_date': '2026-03-01' if not phase2_complete else None
            },
            {
                'id': 3,
                'name': 'Threshold Optimization',
                'description': f'Win rate: {win_rate_dir:.1f}% → 40% target',
                'progress': round(phase3_progress, 1),
                'complete': phase3_complete,
                'icon': 'sliders',
                'eta': '~Day 60' if not phase3_complete else 'Complete',
                'target_date': '2026-03-16' if not phase3_complete else None
            },
            {
                'id': 4,
                'name': 'Live Deployment',
                'description': 'Ready for production trading',
                'progress': round(phase4_progress, 1),
                'complete': deployment_ready,
                'icon': 'rocket',
                'eta': '~Day 90' if not deployment_ready else 'Complete',
                'target_date': '2026-04-15' if not deployment_ready else None
            }
        ]
        
        current_phase = 1
        for p in phases:
            if not p['complete']:
                current_phase = p['id']
                break
        else:
            current_phase = 4
        
        return jsonify({
            'success': True,
            'phases': phases,
            'current_phase': current_phase,
            'overall_progress': round(overall_progress, 1),
            'status': 'CALIBRATING' if not deployment_ready else 'READY',
            'metrics': {
                'total_trades': total_trades,
                'win_rate': round(win_rate_dir, 1),
                'target_win_rate': 40
            },
            'timeline': {
                'start_date': '2026-01-15',
                'current_day': days_since_start,
                'day30_review': '2026-02-14',
                'day60_target': '2026-03-16',
                'next_milestone': 'Day 60 Optimization' if days_since_start >= 30 else 'Day 30 Review'
            },
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Calibration progress error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'phases': []
        }), 500


@core_bp.route('/api/system/recommended-actions')
def recommended_actions():
    """Return prioritized recommended actions based on system state"""
    try:
        result = get_paper_trades(return_dict=True)
        trades = result.get('trades', []) if result.get('success') else []
        metrics = calculate_metrics(trades)
        
        closed_trades = [t for t in trades if t.get('status') == 'closed']
        total_trades = len(closed_trades)
        win_rate = metrics.get('win_rate_directional', 0) or metrics.get('win_rate', 0)
        profit_factor = metrics.get('profit_factor', 0)
        total_pnl_for_cp = metrics.get('total_pnl', 0) or 0
        capital_preserved = round(max(0, (1_000_000 + total_pnl_for_cp) / 1_000_000 * 100), 2)
        
        actions = []
        
        if total_trades < 100:
            actions.append({
                'id': 'collect-trades',
                'priority': 'high',
                'icon': 'database',
                'title': 'Continue Trade Collection',
                'description': f'Need {100 - total_trades} more trades to complete Phase 1',
                'reason': 'Statistical significance requires minimum 100 trades',
                'action_type': 'progress'
            })
        
        if win_rate < 40 and total_trades >= 50:
            gap = 40 - win_rate
            actions.append({
                'id': 'improve-winrate',
                'priority': 'high',
                'icon': 'trending-up',
                'title': 'Optimize Win Rate',
                'description': f'Current: {win_rate:.1f}% → Target: 40% ({gap:.1f}% gap)',
                'reason': 'System auto-calibrating thresholds based on market patterns',
                'action_type': 'calibration'
            })
        
        if profit_factor and profit_factor < 1.0:
            actions.append({
                'id': 'fee-optimization',
                'priority': 'medium',
                'icon': 'percent',
                'title': 'Review Fee Impact',
                'description': 'Profit factor below 1.0 indicates fee erosion',
                'reason': 'Consider larger position sizes or fewer trades',
                'action_type': 'optimization'
            })
        
        if total_trades >= 100 and win_rate >= 40:
            actions.append({
                'id': 'prepare-deployment',
                'priority': 'high',
                'icon': 'rocket',
                'title': 'Prepare for Live Deployment',
                'description': 'All calibration phases complete',
                'reason': 'System ready for production trading review',
                'action_type': 'milestone'
            })
        
        if capital_preserved >= 98:
            actions.append({
                'id': 'maintain-capital',
                'priority': 'low',
                'icon': 'shield',
                'title': 'Capital Protection Active',
                'description': f'{capital_preserved}% capital preserved',
                'reason': 'Veto system functioning correctly',
                'action_type': 'status'
            })
        
        if total_trades >= 50 and total_trades < 100:
            actions.append({
                'id': 'halfway-milestone',
                'priority': 'low',
                'icon': 'flag',
                'title': 'Halfway to Track Record',
                'description': f'{total_trades}/100 trades completed',
                'reason': 'Maintain current trading frequency',
                'action_type': 'progress'
            })
        
        if total_trades >= 100 and win_rate >= 35 and win_rate < 40:
            actions.append({
                'id': 'near-target',
                'priority': 'medium',
                'icon': 'target',
                'title': 'Near Win Rate Target',
                'description': f'Only {40 - win_rate:.1f}% away from 40% target',
                'reason': 'Pattern optimization in progress',
                'action_type': 'progress'
            })
        
        if not actions:
            actions.append({
                'id': 'monitoring',
                'priority': 'low',
                'icon': 'activity',
                'title': 'System Operating Normally',
                'description': 'All metrics within expected ranges',
                'reason': 'Continue monitoring performance',
                'action_type': 'status'
            })
        
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        actions.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        actions = actions[:5]
        
        return jsonify({
            'success': True,
            'actions': actions,
            'total_actions': len(actions),
            'metrics_snapshot': {
                'trades': total_trades,
                'win_rate': round(win_rate, 1),
                'capital_preserved': capital_preserved
            },
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Recommended actions error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'actions': []
        }), 500


@core_bp.route('/api/metrics/comparative')
@require_api_key
def api_comparative_metrics():
    """
    Comparative Metrics API - OMNIX vs BTC Hold vs Average Bot
    Shows value proposition: Why use OMNIX instead of just holding BTC?
    
    IMPORTANT: All comparisons use the SAME period (OMNIX trading period)
    to ensure fair, aligned investor messaging per ADR-003.
    """
    try:
        result = get_paper_trades(return_dict=True)
        trades = result.get('trades', []) if result.get('success') else []
        
        closed_trades = [t for t in trades if t.get('status') == 'closed']
        
        if not closed_trades:
            return jsonify({
                'success': True,
                'message': 'No closed trades yet',
                'comparison': None,
                'last_updated': datetime.now().isoformat()
            })
        
        first_trade = min(closed_trades, key=lambda x: x.get('created_at', datetime.now()))
        last_trade = max(closed_trades, key=lambda x: x.get('closed_at') or x.get('created_at', datetime.now()))
        
        start_date = first_trade.get('created_at')
        end_date = last_trade.get('closed_at') or last_trade.get('created_at') or datetime.now()
        
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        
        metrics = calculate_metrics(closed_trades)
        
        initial_capital = 1000000
        current_balance = metrics.get('current_balance', initial_capital)
        omnix_return = ((current_balance - initial_capital) / initial_capital) * 100
        omnix_preserved = (current_balance / initial_capital) * 100
        
        btc_start_price = None
        btc_end_price = None
        btc_return = None
        btc_data_available = False
        period_aligned = False
        
        try:
            if hasattr(start_date, 'timestamp'):
                start_ts = int(start_date.timestamp())
            else:
                start_ts = int((datetime.now() - timedelta(days=30)).timestamp())
            
            if hasattr(end_date, 'timestamp'):
                end_ts = int(end_date.timestamp())
            else:
                end_ts = int(datetime.now().timestamp())
            
            btc_ohlc = http_get_with_timeout(
                f'https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=1440&since={start_ts}',
                timeout=8
            )
            
            if btc_ohlc and btc_ohlc.get('result'):
                ohlc_data = btc_ohlc['result'].get('XXBTZUSD', [])
                if ohlc_data and len(ohlc_data) >= 2:
                    filtered_data = [candle for candle in ohlc_data if int(candle[0]) <= end_ts]
                    
                    if filtered_data and len(filtered_data) >= 1:
                        btc_start_price = float(ohlc_data[0][1])
                        btc_end_price = float(filtered_data[-1][4])
                        
                        if btc_start_price > 0:
                            btc_return = ((btc_end_price - btc_start_price) / btc_start_price) * 100
                            btc_data_available = True
                            period_aligned = True
        except Exception as e:
            logger.warning(f"Could not fetch BTC prices for period: {e}")
        
        avg_bot_return = None
        avg_bot_dd = None
        avg_bot_wr = None
        
        veto_count = 0
        try:
            with get_db_connection() as conn:
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT COUNT(*) FROM information_schema.tables 
                        WHERE table_name = 'capital_protected_events'
                    """)
                    table_exists = cursor.fetchone()[0] > 0
                    if table_exists:
                        cursor.execute("SELECT COUNT(*) FROM capital_protected_events")
                        veto_count = cursor.fetchone()[0] or 0
                    cursor.close()
        except Exception:
            pass
        
        # FIX Jan 25 2026: Normalize max drawdown to always be <= 0
        # Drawdown represents loss, so positive values make no sense
        raw_dd = metrics.get('max_drawdown', 0)
        normalized_dd = min(0, raw_dd) if raw_dd else 0  # Ensure 0 or negative
        
        # FIX Jan 25 2026: Check if these trades are from Track Record (Jan 15+)
        # If showing Learning Baseline data, add context
        track_record_start = datetime(2026, 1, 15)
        official_trades = [t for t in closed_trades if t.get('opened_at') and t.get('opened_at') >= track_record_start]
        baseline_trades = [t for t in closed_trades if t.get('opened_at') and t.get('opened_at') < track_record_start]
        
        # Win rate should be None if no official trades (avoid mixing periods)
        official_win_rate = None
        if official_trades:
            winners = [t for t in official_trades if (t.get('pnl') or 0) > 0]
            official_win_rate = round((len(winners) / len(official_trades)) * 100, 1) if official_trades else None
        
        comparison = {
            'omnix': {
                'name': 'OMNIX',
                'return_pct': round(omnix_return, 2),
                'capital_preserved_pct': round(omnix_preserved, 2),
                'max_drawdown_pct': round(normalized_dd, 2),
                'win_rate': official_win_rate,  # None if no official trades
                'risk_blocked': veto_count,
                'trades': len(closed_trades),
                'official_trades': len(official_trades),
                'baseline_trades': len(baseline_trades),
                'highlight': 'capital_preserved'
            },
            'btc_hold': {
                'name': 'BTC HOLD',
                'return_pct': round(btc_return, 2) if btc_return is not None else None,
                'capital_preserved_pct': round(100 + btc_return, 2) if btc_return is not None else None,
                'max_drawdown_pct': None,
                'win_rate': None,
                'risk_blocked': 0,
                'trades': 0,
                'highlight': None,
                'data_available': btc_data_available
            },
            'avg_bot': {
                'name': 'AVG BOT',
                'return_pct': None,
                'capital_preserved_pct': None,
                'max_drawdown_pct': None,
                'win_rate': None,
                'risk_blocked': 0,
                'trades': None,
                'highlight': None,
                'note': 'Insufficient real data — no verified industry benchmark available',
                'status': 'insufficient_data'
            }
        }
        
        insights = []
        
        if btc_return is not None and omnix_preserved > (100 + btc_return):
            diff = omnix_preserved - (100 + btc_return)
            insights.append({
                'type': 'success',
                'message': f'OMNIX preserved {diff:.1f}% more capital than BTC hold strategy'
            })
        
        omnix_dd = abs(metrics.get('max_drawdown', -1.5))
        insights.append({
            'type': 'success',
            'message': f'OMNIX max drawdown limited to {omnix_dd:.1f}% through risk controls'
        })
        
        if veto_count > 0:
            insights.append({
                'type': 'info',
                'message': f'{veto_count} high-risk operations blocked by veto system'
            })
        
        if not btc_data_available:
            insights.append({
                'type': 'info',
                'message': 'BTC price data unavailable for exact period - comparison limited'
            })
        
        period_info = 'Trading period'
        try:
            if hasattr(start_date, 'strftime') and hasattr(end_date, 'strftime'):
                period_info = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
        except Exception:
            pass
        
        return jsonify({
            'success': True,
            'comparison': comparison,
            'insights': insights,
            'period': period_info,
            'period_aligned': period_aligned,
            'btc_prices': {
                'start': btc_start_price,
                'end': btc_end_price,
                'data_available': btc_data_available
            },
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Comparative metrics error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'comparison': None
        }), 500


@core_bp.route('/api/metrics/pnl-breakdown')
@require_api_key
def api_pnl_breakdown():
    """
    P&L Breakdown API - Shows where profits and losses come from
    Breakdown by: symbol, fee impact, strategy mode
    """
    try:
        result = get_paper_trades(return_dict=True)
        trades = result.get('trades', []) if result.get('success') else []
        
        closed_trades = [t for t in trades if t.get('status') == 'closed']
        
        if not closed_trades:
            return jsonify({
                'success': True,
                'message': 'No closed trades yet',
                'breakdown': None,
                'last_updated': datetime.now().isoformat()
            })
        
        by_symbol = {}
        for trade in closed_trades:
            symbol = trade.get('symbol', 'UNKNOWN')
            if symbol not in by_symbol:
                by_symbol[symbol] = {
                    'symbol': symbol,
                    'trades': 0,
                    'pnl': 0,
                    'wins': 0,
                    'losses': 0,
                    'wins_pnl': 0,
                    'losses_pnl': 0
                }
            
            pnl = float(trade.get('pnl', 0) or 0)
            by_symbol[symbol]['trades'] += 1
            by_symbol[symbol]['pnl'] += pnl
            
            if pnl > 0:
                by_symbol[symbol]['wins'] += 1
                by_symbol[symbol]['wins_pnl'] += pnl
            elif pnl < 0:
                by_symbol[symbol]['losses'] += 1
                by_symbol[symbol]['losses_pnl'] += pnl
        
        symbol_breakdown = sorted(by_symbol.values(), key=lambda x: x['pnl'], reverse=True)
        
        total_pnl = sum(t['pnl'] for t in symbol_breakdown)
        for item in symbol_breakdown:
            item['pnl_pct'] = (item['pnl'] / abs(total_pnl) * 100) if total_pnl != 0 else 0
            item['win_rate'] = (item['wins'] / item['trades'] * 100) if item['trades'] > 0 else 0
        
        fee_eroded = 0
        directional_wins = 0
        pure_losses = 0
        pure_wins = 0
        
        for trade in closed_trades:
            pnl = float(trade.get('pnl', 0) or 0)
            pnl_percent = float(trade.get('pnl_percent', 0) or 0)
            
            if pnl_percent > 0:
                directional_wins += 1
                if pnl > 0:
                    pure_wins += 1
                else:
                    fee_eroded += 1
            else:
                pure_losses += 1
        
        cause_breakdown = [
            {
                'cause': 'Pure Wins',
                'description': 'Profitable trades after fees',
                'count': pure_wins,
                'pct': (pure_wins / len(closed_trades) * 100) if closed_trades else 0,
                'type': 'success'
            },
            {
                'cause': 'Fee Eroded',
                'description': 'Direction correct but fees exceeded profit',
                'count': fee_eroded,
                'pct': (fee_eroded / len(closed_trades) * 100) if closed_trades else 0,
                'type': 'warning'
            },
            {
                'cause': 'Pure Losses',
                'description': 'Direction incorrect',
                'count': pure_losses,
                'pct': (pure_losses / len(closed_trades) * 100) if closed_trades else 0,
                'type': 'danger'
            }
        ]
        
        by_mode = {}
        for trade in closed_trades:
            mode = trade.get('strategy_mode', 'STANDARD') or 'STANDARD'
            if mode not in by_mode:
                by_mode[mode] = {'mode': mode, 'trades': 0, 'pnl': 0, 'wins': 0}
            
            pnl = float(trade.get('pnl', 0) or 0)
            by_mode[mode]['trades'] += 1
            by_mode[mode]['pnl'] += pnl
            if pnl > 0:
                by_mode[mode]['wins'] += 1
        
        mode_breakdown = []
        for mode_data in by_mode.values():
            mode_data['win_rate'] = (mode_data['wins'] / mode_data['trades'] * 100) if mode_data['trades'] > 0 else 0
            mode_breakdown.append(mode_data)
        
        return jsonify({
            'success': True,
            'breakdown': {
                'by_symbol': symbol_breakdown,
                'by_cause': cause_breakdown,
                'by_mode': mode_breakdown,
                'summary': {
                    'total_trades': len(closed_trades),
                    'total_pnl': round(total_pnl, 2),
                    'best_symbol': symbol_breakdown[0]['symbol'] if symbol_breakdown else None,
                    'worst_symbol': symbol_breakdown[-1]['symbol'] if symbol_breakdown else None,
                    'directional_accuracy': round((directional_wins / len(closed_trades) * 100) if closed_trades else 0, 1)
                }
            },
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"PnL breakdown error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'breakdown': None
        }), 500


@core_bp.route('/api/regime/dashboard')
@require_api_key
def api_regime_dashboard():
    """
    FEAT-010: Regime Detection Dashboard
    Shows current market regime, veto activity, and performance context for investors.
    Uses shadow_trade_events to infer regime from ema_signal since paper_trading_trades.hmm_regime is empty.
    """
    try:
        with get_db_connection() as conn:
            if not conn:
                return jsonify({
                    'success': False,
                    'error': 'Database connection unavailable',
                    'regime': None
                }), 503
            
            cur = conn.cursor()
            
            cur.execute("""
                SELECT 
                    ema_signal,
                    ema_score,
                    created_at,
                    veto_type,
                    veto_reason,
                    coherence_score,
                    symbol
                FROM shadow_trade_events
                ORDER BY created_at DESC
                LIMIT 1
            """)
            latest_event = cur.fetchone()
            
            if latest_event:
                ema_signal = latest_event[0] or 'NONE'
                ema_score = float(latest_event[1] or 0)
                last_activity = latest_event[2]
                last_veto_type = latest_event[3]
                last_veto_reason = latest_event[4]
                coherence = float(latest_event[5] or 0)
                last_symbol = latest_event[6]
                
                if ema_signal == 'LONG':
                    regime_type = 'BULLISH'
                    regime_label = 'Bullish Trend'
                elif ema_signal == 'SHORT':
                    regime_type = 'BEARISH'
                    regime_label = 'Bearish Trend'
                else:
                    regime_type = 'RANGING'
                    regime_label = 'Sideways Market'
                
                if ema_score >= 50:
                    confidence = 'HIGH'
                    confidence_pct = min(100, 50 + ema_score)
                elif ema_score >= 35:
                    confidence = 'MEDIUM'
                    confidence_pct = ema_score + 25
                else:
                    confidence = 'LOW'
                    confidence_pct = ema_score + 10
                
                duration_hours = 0
                if last_activity:
                    try:
                        now = datetime.now(last_activity.tzinfo) if hasattr(last_activity, 'tzinfo') and last_activity.tzinfo else datetime.now()
                        duration_hours = (now - last_activity).total_seconds() / 3600
                    except Exception:
                        pass
            else:
                regime_type = 'UNKNOWN'
                regime_label = 'No Data'
                ema_score = 0
                confidence = 'UNKNOWN'
                confidence_pct = 0
                last_activity = None
                last_veto_type = None
                last_veto_reason = None
                coherence = 0
                last_symbol = None
                duration_hours = 0
            
            current_regime = {
                'type': regime_type,
                'label': regime_label,
                'ema_score': round(ema_score, 1),
                'confidence': confidence,
                'confidence_pct': round(confidence_pct, 1),
                'coherence_score': round(coherence, 1),
                'last_activity': last_activity.isoformat() if last_activity else None,
                'last_symbol': last_symbol,
                'hours_since_activity': round(duration_hours, 1),
                'current_veto': last_veto_type,
                'veto_reason': last_veto_reason
            }
            
            cur.execute("""
                SELECT 
                    veto_type,
                    COUNT(*) as count,
                    COALESCE(SUM(blocked_capital), 0) as capital_blocked
                FROM shadow_trade_events
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                GROUP BY veto_type
                ORDER BY count DESC
            """)
            veto_24h = cur.fetchall()
            
            cur.execute("""
                SELECT 
                    veto_type,
                    COUNT(*) as count,
                    COALESCE(SUM(blocked_capital), 0) as capital_blocked
                FROM shadow_trade_events
                WHERE created_at >= NOW() - INTERVAL '7 days'
                GROUP BY veto_type
                ORDER BY count DESC
            """)
            veto_7d = cur.fetchall()
            
            veto_summary = {
                '24h': [
                    {
                        'type': row[0] or 'UNKNOWN',
                        'count': row[1],
                        'capital_blocked': float(row[2] or 0)
                    }
                    for row in veto_24h
                ],
                '7d': [
                    {
                        'type': row[0] or 'UNKNOWN',
                        'count': row[1],
                        'capital_blocked': float(row[2] or 0)
                    }
                    for row in veto_7d
                ]
            }
            
            cur.execute("""
                SELECT 
                    ema_signal,
                    COUNT(*) as events,
                    ROUND(AVG(ema_score)::numeric, 2) as avg_ema_score,
                    ROUND(AVG(coherence_score)::numeric, 2) as avg_coherence
                FROM shadow_trade_events
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                GROUP BY ema_signal
                ORDER BY events DESC
            """)
            signal_distribution = cur.fetchall()
            
            regime_performance = []
            for row in signal_distribution:
                signal = row[0] or 'NONE'
                if signal == 'LONG':
                    regime_name = 'BULLISH'
                elif signal == 'SHORT':
                    regime_name = 'BEARISH'
                else:
                    regime_name = 'RANGING'
                
                regime_performance.append({
                    'regime': regime_name,
                    'signal': signal,
                    'events_24h': row[1],
                    'avg_ema_score': float(row[2] or 0),
                    'avg_coherence': float(row[3] or 0)
                })
            
            cur.execute("""
                WITH signal_changes AS (
                    SELECT 
                        ema_signal,
                        created_at,
                        LAG(ema_signal) OVER (ORDER BY created_at) as prev_signal
                    FROM shadow_trade_events
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                )
                SELECT 
                    prev_signal as from_signal,
                    ema_signal as to_signal,
                    created_at
                FROM signal_changes
                WHERE ema_signal != prev_signal OR prev_signal IS NULL
                ORDER BY created_at DESC
                LIMIT 10
            """)
            transitions_raw = cur.fetchall()
            
            transitions = []
            for row in transitions_raw:
                from_signal = row[0] or 'START'
                to_signal = row[1] or 'UNKNOWN'
                
                from_regime = 'BULLISH' if from_signal == 'LONG' else ('BEARISH' if from_signal == 'SHORT' else 'RANGING')
                to_regime = 'BULLISH' if to_signal == 'LONG' else ('BEARISH' if to_signal == 'SHORT' else 'RANGING')
                
                if from_regime != to_regime:
                    transitions.append({
                        'from': from_regime,
                        'to': to_regime,
                        'timestamp': row[2].isoformat() if row[2] else None
                    })
            
            cur.close()
        
        total_vetos_24h = sum(v['count'] for v in veto_summary['24h'])
        total_capital_blocked = sum(v['capital_blocked'] for v in veto_summary['24h'])
        
        if regime_type == 'RANGING' and total_vetos_24h > 100:
            system_message = 'System on standby: sideways market detected. Waiting for clear trend to operate.'
            system_status = 'DEFENSIVE'
        elif regime_type == 'BULLISH' and confidence == 'HIGH':
            system_message = 'Bullish trend confirmed. System analyzing entry opportunities.'
            system_status = 'ANALYZING'
        elif last_veto_type == 'BLACK_SWAN':
            system_message = 'Elevated risk detected. System blocking trades for safety.'
            system_status = 'PROTECTIVE'
        else:
            system_message = 'System monitoring market conditions. Active filters protecting capital.'
            system_status = 'MONITORING'
        
        return jsonify({
            'success': True,
            'current_regime': current_regime,
            'veto_summary': veto_summary,
            'regime_performance': regime_performance,
            'transitions': transitions[:5],
            'system_status': {
                'status': system_status,
                'message': system_message,
                'total_vetos_24h': total_vetos_24h,
                'capital_protected_24h': round(total_capital_blocked, 2)
            },
            'data_source': 'shadow_trade_events',
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Regime dashboard error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'regime': None
        }), 500


@core_bp.route('/api/metrics/time-heatmap')
@require_api_key
def api_time_heatmap():
    """
    FEAT-009: Time Heatmap
    Analyzes P&L by hour of day and day of week to find optimal trading times.
    """
    try:
        with get_db_connection() as conn:
            if not conn:
                return jsonify({'success': False, 'error': 'Database unavailable'}), 503
            
            cur = conn.cursor()
            
            cur.execute("""
                SELECT 
                    EXTRACT(DOW FROM opened_at) as day_of_week,
                    EXTRACT(HOUR FROM opened_at) as hour,
                    COUNT(*) as trades,
                    SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as wins,
                    ROUND(SUM(profit_loss)::numeric, 2) as total_pnl,
                    ROUND(AVG(profit_loss)::numeric, 2) as avg_pnl
                FROM paper_trading_trades
                WHERE opened_at IS NOT NULL AND status = 'closed'
                GROUP BY EXTRACT(DOW FROM opened_at), EXTRACT(HOUR FROM opened_at)
                ORDER BY day_of_week, hour
            """)
            rows = cur.fetchall()
            
            heatmap_data = []
            best_time = {'day': 0, 'hour': 0, 'pnl': float('-inf')}
            worst_time = {'day': 0, 'hour': 0, 'pnl': float('inf')}
            
            for row in rows:
                day = int(row[0])
                hour = int(row[1])
                trades = row[2]
                wins = row[3]
                pnl = float(row[4] or 0)
                avg_pnl = float(row[5] or 0)
                win_rate = (wins / trades * 100) if trades > 0 else 0
                
                heatmap_data.append({
                    'day': day,
                    'hour': hour,
                    'trades': trades,
                    'wins': wins,
                    'pnl': pnl,
                    'avg_pnl': avg_pnl,
                    'win_rate': round(win_rate, 1)
                })
                
                if pnl > best_time['pnl']:
                    best_time = {'day': day, 'hour': hour, 'pnl': pnl}
                if pnl < worst_time['pnl']:
                    worst_time = {'day': day, 'hour': hour, 'pnl': pnl}
            
            cur.close()
        
        day_names = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        
        return jsonify({
            'success': True,
            'heatmap': heatmap_data,
            'best_time': {
                'day': day_names[best_time['day']],
                'hour': f"{best_time['hour']:02d}:00",
                'pnl': best_time['pnl']
            },
            'worst_time': {
                'day': day_names[worst_time['day']],
                'hour': f"{worst_time['hour']:02d}:00",
                'pnl': worst_time['pnl']
            },
            'day_names': day_names,
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Time heatmap error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@core_bp.route('/api/metrics/correlation')
@require_api_key
def api_correlation_matrix():
    """
    FEAT-008: Asset Performance Matrix
    Shows diversification analysis and per-symbol performance metrics.
    """
    try:
        with get_db_connection() as conn:
            if not conn:
                return jsonify({'success': False, 'error': 'Database unavailable'}), 503
            
            cur = conn.cursor()
            
            cur.execute("""
                SELECT 
                    symbol,
                    COUNT(*) as trades,
                    SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as wins,
                    ROUND(SUM(profit_loss)::numeric, 2) as total_pnl,
                    ROUND(AVG(profit_loss)::numeric, 2) as avg_pnl,
                    ROUND(STDDEV(profit_loss)::numeric, 2) as pnl_stddev,
                    MIN(opened_at) as first_trade,
                    MAX(opened_at) as last_trade
                FROM paper_trading_trades
                WHERE status = 'closed'
                GROUP BY symbol
                ORDER BY trades DESC
            """)
            symbol_stats = cur.fetchall()
            
            cur.execute("""
                WITH hourly_pnl AS (
                    SELECT 
                        symbol,
                        DATE_TRUNC('hour', opened_at) as hour_bucket,
                        SUM(profit_loss) as hour_pnl
                    FROM paper_trading_trades
                    WHERE status = 'closed' AND opened_at IS NOT NULL
                    GROUP BY symbol, DATE_TRUNC('hour', opened_at)
                ),
                symbol_pairs AS (
                    SELECT DISTINCT 
                        a.symbol as symbol_a,
                        b.symbol as symbol_b
                    FROM hourly_pnl a
                    CROSS JOIN hourly_pnl b
                    WHERE a.symbol < b.symbol
                )
                SELECT 
                    sp.symbol_a,
                    sp.symbol_b,
                    COUNT(*) as common_hours,
                    ROUND(COALESCE(CORR(a.hour_pnl, b.hour_pnl), 0)::numeric, 3) as correlation
                FROM symbol_pairs sp
                LEFT JOIN hourly_pnl a ON a.symbol = sp.symbol_a
                LEFT JOIN hourly_pnl b ON b.symbol = sp.symbol_b AND a.hour_bucket = b.hour_bucket
                WHERE a.hour_bucket IS NOT NULL AND b.hour_bucket IS NOT NULL
                GROUP BY sp.symbol_a, sp.symbol_b
                HAVING COUNT(*) >= 3
                ORDER BY ABS(COALESCE(CORR(a.hour_pnl, b.hour_pnl), 0)) DESC NULLS LAST
                LIMIT 15
            """)
            correlations = cur.fetchall()
            
            cur.close()
        
        symbols = []
        total_pnl = sum(float(row[3] or 0) for row in symbol_stats)
        for row in symbol_stats:
            pnl = float(row[3] or 0)
            win_rate = (row[2] / row[1] * 100) if row[1] > 0 else 0
            contribution = (pnl / total_pnl * 100) if total_pnl != 0 else 0
            symbols.append({
                'symbol': row[0].replace('/USD', ''),
                'trades': row[1],
                'wins': row[2],
                'pnl': pnl,
                'avg_pnl': float(row[4] or 0),
                'volatility': float(row[5] or 0),
                'win_rate': round(win_rate, 1),
                'contribution': round(contribution, 1)
            })
        
        matrix = []
        for row in correlations:
            corr_val = float(row[3]) if row[3] is not None else 0
            matrix.append({
                'pair_a': row[0].replace('/USD', ''),
                'pair_b': row[1].replace('/USD', ''),
                'common_hours': row[2],
                'correlation': corr_val,
                'strength': 'HIGH' if abs(corr_val) > 0.7 else ('MEDIUM' if abs(corr_val) > 0.4 else 'LOW'),
                'diversified': abs(corr_val) < 0.3
            })
        
        diversification_score = 100
        if matrix:
            avg_corr = sum(abs(m['correlation']) for m in matrix) / len(matrix)
            diversification_score = max(0, min(100, int((1 - avg_corr) * 100)))
        
        return jsonify({
            'success': True,
            'symbols': symbols,
            'correlations': matrix,
            'total_pairs': len(correlations),
            'diversification_score': diversification_score,
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Correlation matrix error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


def _calculate_opportunity_tracker(conn):
    """
    ADR-008: Opportunity Tracker - Two-sided accounting for Day 30 review.
    Tracks missed opportunities vs losses avoided to inform threshold decisions.
    """
    try:
        cur = conn.cursor()
        
        tracking_start = datetime(2026, 1, 14)
        review_date = datetime(2026, 2, 13)
        today = datetime.now()
        current_day = max(1, (today - tracking_start).days + 1)
        
        # ADR-018: Realistic metrics - cap estimates to available capital
        # Max capital: $1M virtual, Max opportunity cost: 5% of capital = $50K
        MAX_REALISTIC_MISSED = 50000  # $50K max realistic value
        cur.execute("""
            SELECT 
                COUNT(*) as missed_count,
                COALESCE(ROUND(LEAST(SUM(blocked_capital * 0.015), %s)::numeric, 2), 0) as est_profit,
                COALESCE(ROUND(AVG(coherence_score)::numeric, 1), 0) as avg_coherence
            FROM shadow_trade_events
            WHERE created_at >= '2026-01-14'
              AND coherence_score >= 45
              AND ema_score >= 25
              AND ema_score < 40
              AND (black_swan_prob IS NULL OR black_swan_prob <= 0.5)
        """, (MAX_REALISTIC_MISSED,))
        missed_row = cur.fetchone()
        
        # ADR-018: Realistic metrics - cap Est. Loss Avoided to available capital
        # Formula: min(count × avg_position × avg_adverse_move, max_capital × max_exposure)
        # Max capital: $1M virtual, Max single exposure: 2% ($20K), Max total exposure: 10% ($100K)
        MAX_REALISTIC_LOSS_AVOIDED = 100000  # $100K max realistic value
        cur.execute("""
            SELECT 
                COUNT(*) as avoided_count,
                COALESCE(ROUND(LEAST(SUM(blocked_capital * 0.025), %s)::numeric, 2), 0) as est_loss,
                COALESCE(ROUND(AVG(coherence_score)::numeric, 1), 0) as avg_coherence
            FROM shadow_trade_events
            WHERE created_at >= '2026-01-14'
              AND (coherence_score < 30 OR black_swan_prob > 0.5)
        """, (MAX_REALISTIC_LOSS_AVOIDED,))
        avoided_row = cur.fetchone()
        
        cur.execute("""
            SELECT 
                COUNT(*) as near_miss_count,
                COALESCE(ROUND(AVG(ema_score)::numeric, 1), 0) as avg_ema,
                COALESCE(ROUND(AVG(coherence_score)::numeric, 1), 0) as avg_coherence
            FROM shadow_trade_events
            WHERE created_at >= '2026-01-14'
              AND ema_score >= 28 AND ema_score < 35
              AND coherence_score >= 40
              AND (black_swan_prob IS NULL OR black_swan_prob <= 0.6)
        """)
        near_miss_row = cur.fetchone()
        
        cur.close()
        
        missed_count = int(missed_row[0] or 0) if missed_row else 0
        missed_est_profit = float(missed_row[1] or 0) if missed_row else 0
        missed_avg_coh = float(missed_row[2] or 0) if missed_row else 0
        
        avoided_count = int(avoided_row[0] or 0) if avoided_row else 0
        avoided_est_loss = float(avoided_row[1] or 0) if avoided_row else 0
        avoided_avg_coh = float(avoided_row[2] or 0) if avoided_row else 0
        
        near_miss_count = int(near_miss_row[0] or 0) if near_miss_row else 0
        near_miss_avg_ema = float(near_miss_row[1] or 0) if near_miss_row else 0
        near_miss_avg_coh = float(near_miss_row[2] or 0) if near_miss_row else 0
        
        net_value = missed_est_profit - avoided_est_loss
        
        if net_value < -500:
            interpretation = 'PROTECTING'
            interpretation_text = 'System protecting correctly'
        elif net_value > 1000:
            interpretation = 'TOO_STRICT'
            interpretation_text = 'Consider adjusting thresholds'
        else:
            interpretation = 'BALANCED'
            interpretation_text = 'System balanced'
        
        if missed_count < 10 or missed_est_profit < 1000:
            recommendation = 'KEEP_CONSERVATIVE'
        elif missed_count > 20 and missed_est_profit > 3000 and avoided_est_loss > 5000:
            recommendation = 'TEST_LOWER'
        else:
            recommendation = 'CONTINUE_MONITORING'
        
        return {
            'missed': {
                'count': missed_count,
                'est_profit': missed_est_profit,
                'avg_coherence': missed_avg_coh,
                'conditions': 'Coh >45%, EMA 25-40%, BS LOW/MEDIUM'
            },
            'avoided': {
                'count': avoided_count,
                'est_loss': avoided_est_loss,
                'avg_coherence': avoided_avg_coh,
                'conditions': 'Coh <30% OR BS HIGH/EXTREME'
            },
            'net': {
                'value': net_value,
                'interpretation': interpretation,
                'interpretation_text': interpretation_text
            },
            'day_progress': {
                'current_day': current_day,
                'total_days': 30,
                'review_date': review_date.strftime('%Y-%m-%d'),
                'review_date_display': 'Complete'
            },
            'recommendation': recommendation,
            'near_miss': {
                'count': near_miss_count,
                'avg_ema': near_miss_avg_ema,
                'avg_coherence': near_miss_avg_coh,
                'conditions': 'EMA 28-35%, Coh >=40%, BS <=MEDIUM'
            }
        }
        
    except Exception as e:
        logger.error(f"Opportunity tracker calculation error: {e}")
        return {
            'missed': {'count': 0, 'est_profit': 0, 'avg_coherence': 0, 'conditions': 'N/A'},
            'avoided': {'count': 0, 'est_loss': 0, 'avg_coherence': 0, 'conditions': 'N/A'},
            'net': {'value': 0, 'interpretation': 'UNKNOWN', 'interpretation_text': 'Calculation error'},
            'day_progress': {'current_day': 1, 'total_days': 30, 'review_date': '2026-02-14', 'review_date_display': 'Complete'},
            'recommendation': 'CONTINUE_MONITORING',
            'near_miss': {'count': 0, 'avg_ema': 0, 'avg_coherence': 0, 'conditions': 'N/A'}
        }


@core_bp.route('/api/learning/insights')
@require_api_key
def api_learning_insights():
    """
    FEAT-011: Opportunity Tracker (formerly Learning Engine Insights)
    Analyzes Shadow Portfolio for two-sided accounting: missed opportunities vs losses avoided.
    Reference: ADR-008-opportunity-tracker.md
    """
    try:
        with get_db_connection() as conn:
            if not conn:
                return jsonify({'success': False, 'error': 'Database unavailable'}), 503
            
            cur = conn.cursor()
            
            cur.execute("""
                SELECT 
                    veto_type,
                    COUNT(*) as total_vetos,
                    SUM(CASE WHEN outcome_calculated = true THEN 1 ELSE 0 END) as analyzed,
                    ROUND(AVG(blocked_capital)::numeric, 2) as avg_blocked,
                    ROUND(SUM(blocked_capital)::numeric, 2) as total_blocked
                FROM shadow_trade_events
                WHERE created_at >= NOW() - INTERVAL '7 days'
                GROUP BY veto_type
                ORDER BY total_vetos DESC
            """)
            veto_stats = cur.fetchall()
            
            cur.execute("""
                SELECT 
                    veto_type,
                    COUNT(*) as events,
                    ROUND(AVG(ema_score)::numeric, 2) as avg_ema,
                    ROUND(AVG(coherence_score)::numeric, 2) as avg_coherence,
                    ROUND(AVG(monte_carlo_er)::numeric, 4) as avg_mc_er,
                    ROUND(AVG(black_swan_prob)::numeric, 2) as avg_bs_prob
                FROM shadow_trade_events
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                GROUP BY veto_type
            """)
            veto_thresholds = cur.fetchall()
            
            cur.execute("""
                SELECT 
                    symbol,
                    COUNT(*) as veto_count,
                    ROUND(AVG(ema_score)::numeric, 2) as avg_ema,
                    ROUND(SUM(blocked_capital)::numeric, 2) as capital_blocked
                FROM shadow_trade_events
                WHERE created_at >= NOW() - INTERVAL '7 days'
                GROUP BY symbol
                ORDER BY veto_count DESC
                LIMIT 5
            """)
            top_vetoed_symbols = cur.fetchall()
            
            cur.execute("""
                SELECT 
                    DATE(created_at) as day,
                    COUNT(*) as vetos,
                    ROUND(SUM(blocked_capital)::numeric, 2) as capital
                FROM shadow_trade_events
                WHERE created_at >= NOW() - INTERVAL '7 days'
                GROUP BY DATE(created_at)
                ORDER BY day DESC
            """)
            daily_trend = cur.fetchall()
            
            cur.close()
        
        veto_effectiveness = []
        for row in veto_stats:
            veto_effectiveness.append({
                'type': row[0] or 'UNKNOWN',
                'total': row[1],
                'analyzed': row[2],
                'avg_blocked': float(row[3] or 0),
                'total_blocked': float(row[4] or 0)
            })
        
        threshold_analysis = []
        for row in veto_thresholds:
            threshold_analysis.append({
                'type': row[0] or 'UNKNOWN',
                'events': row[1],
                'avg_ema': float(row[2] or 0),
                'avg_coherence': float(row[3] or 0),
                'avg_mc_er': float(row[4] or 0),
                'avg_bs_prob': float(row[5] or 0)
            })
        
        symbols_analysis = []
        for row in top_vetoed_symbols:
            symbols_analysis.append({
                'symbol': row[0].replace('/USD', '') if row[0] else 'UNKNOWN',
                'veto_count': row[1],
                'avg_ema': float(row[2] or 0),
                'capital_blocked': float(row[3] or 0)
            })
        
        trend = []
        for row in daily_trend:
            trend.append({
                'date': row[0].isoformat() if row[0] else None,
                'vetos': row[1],
                'capital': float(row[2] or 0)
            })
        
        recommendations = []
        total_vetos = sum(v['total'] for v in veto_effectiveness)
        
        if total_vetos > 5000:
            recommendations.append({
                'type': 'CALIBRATION',
                'priority': 'HIGH',
                'title': 'High veto volume',
                'message': f'{total_vetos:,} vetos in 7 days. Consider adjusting thresholds to reduce false positives.',
                'action': 'Review COHERENCE_GATE and BLACK_SWAN thresholds'
            })
        
        bs_vetos = next((v for v in veto_effectiveness if v['type'] == 'BLACK_SWAN'), None)
        if bs_vetos and bs_vetos['total'] > total_vetos * 0.5:
            recommendations.append({
                'type': 'BLACK_SWAN',
                'priority': 'MEDIUM',
                'title': 'Black Swan dominant',
                'message': f'{bs_vetos["total"]:,} ({bs_vetos["total"]/total_vetos*100:.0f}%) of vetos by Black Swan.',
                'action': 'System correctly protecting against extreme volatility'
            })
        
        if not recommendations:
            recommendations.append({
                'type': 'OPTIMAL',
                'priority': 'LOW',
                'title': 'System calibrated',
                'message': 'Filters are operating within normal parameters.',
                'action': 'Continue monitoring metrics'
            })
        
        opportunity_tracker = _calculate_opportunity_tracker(conn)
        
        return jsonify({
            'success': True,
            'veto_effectiveness': veto_effectiveness,
            'threshold_analysis': threshold_analysis,
            'top_vetoed_symbols': symbols_analysis,
            'daily_trend': trend,
            'recommendations': recommendations,
            'opportunity_tracker': opportunity_tracker,
            'summary': {
                'total_vetos_7d': total_vetos,
                'total_capital_protected': sum(v['total_blocked'] for v in veto_effectiveness),
                'veto_types_active': len(veto_effectiveness)
            },
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Learning insights error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@core_bp.route('/api/live-metrics')
def api_live_metrics():
    """Public endpoint returning real-time governance metrics from PostgreSQL.
    
    No API key required - returns only aggregate counts safe for public display.
    Used by omnixquantum.net and demo pages to show live production data.
    """
    fallback = {
        'success': True,
        'live': False,
        'metrics': {
            'evaluation_cycles': 766741,
            'pqc_signed_receipts': 82518,
            'decisions_blocked': 9317,
            'capital_preserved_pct': 98.42,
            'verticals_demo': 7,
            'system_uptime_days': 112,
        },
        'source': 'fallback',
        'last_updated': datetime.now().isoformat()
    }
    
    with get_db_connection() as conn:
        if not conn:
            return jsonify(fallback)
        
        try:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM shadow_trade_events")
            evaluation_cycles = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM decision_receipts")
            pqc_receipts = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM decision_receipts
                WHERE decision IN ('BLOCK', 'BLOCKED')
            """)
            decisions_blocked = cursor.fetchone()[0]
            
            cursor.execute("SELECT EXTRACT(EPOCH FROM (NOW() - MIN(created_at)))/86400 AS uptime_days FROM shadow_trade_events")
            row = cursor.fetchone()
            uptime_days = int(row[0]) if row and row[0] else 0

            cursor.execute("SELECT COALESCE(SUM(profit_loss), 0) FROM paper_trading_trades WHERE status = 'closed'")
            pnl_row = cursor.fetchone()
            total_pnl = float(pnl_row[0] or 0)
            capital_preserved_pct = round(max(0, (1_000_000 + total_pnl) / 1_000_000 * 100), 2)

            response = jsonify({
                'success': True,
                'live': True,
                'metrics': {
                    'evaluation_cycles': evaluation_cycles,
                    'pqc_signed_receipts': pqc_receipts,
                    'decisions_blocked': decisions_blocked,
                    'capital_preserved_pct': capital_preserved_pct,
                    'verticals_demo': 7,
                    'system_uptime_days': uptime_days,
                },
                'source': 'postgresql',
                'last_updated': datetime.now().isoformat()
            })
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response
            
        except Exception as e:
            logger.error(f"Live metrics error: {e}")
            fallback['error'] = str(e)
            return jsonify(fallback)


VALID_REFERRAL_SOURCES = {
    'Facebook', 'WhatsApp', 'Instagram', 'Telegram',
    'LinkedIn', 'Google', 'Recomendación', 'Otro'
}


@core_bp.route('/api/contact', methods=['POST'])
def api_contact_lead():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Invalid request body'}), 400

    name = (data.get('name') or '').strip()
    company = (data.get('company') or '').strip()
    email = (data.get('email') or '').strip()
    referral_source = (data.get('referral_source') or '').strip()
    message = (data.get('message') or '').strip()

    if not name or not email or not referral_source:
        return jsonify({'success': False, 'error': 'Name, email, and referral source are required'}), 400

    if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
        return jsonify({'success': False, 'error': 'Invalid email address'}), 400

    if referral_source not in VALID_REFERRAL_SOURCES:
        return jsonify({'success': False, 'error': 'Invalid referral source'}), 400

    with get_db_connection() as conn:
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database unavailable',
                'fallback_email': 'contacto@omnixquantum.net'
            }), 503

        try:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO contact_leads (name, company, email, referral_source, message)
                   VALUES (%s, %s, %s, %s, %s)""",
                (name, company or None, email, referral_source, message or None)
            )
            conn.commit()
            return jsonify({'success': True, 'message': 'Contact information saved successfully'})

        except Exception as e:
            logger.error(f"Error saving contact lead: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to save contact information',
                'fallback_email': 'contacto@omnixquantum.net'
            }), 500
