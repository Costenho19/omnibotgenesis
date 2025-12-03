"""
OMNIX Dashboard - Core Blueprint
Core API routes (/api/metrics, trades, equity-curve, portfolio, positions, health)
"""

import os
import logging
from datetime import datetime, timedelta
from flask import Blueprint, jsonify

from omnix_dashboard.utils.database import get_db_connection, init_database, get_pool_stats
from omnix_dashboard.utils.database import DB_AVAILABLE, DB_ERROR_MESSAGE, DB_POOL
from omnix_dashboard.utils.decorators import require_api_key
from omnix_dashboard.utils.external_apis import http_get_with_timeout
from omnix_dashboard.utils.queries import (
    get_paper_trades,
    calculate_metrics,
    get_strategy_breakdown,
    get_asset_breakdown
)

logger = logging.getLogger(__name__)

core_bp = Blueprint('core', __name__)

IS_RAILWAY = bool(os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY_PROJECT_ID'))


@core_bp.route('/api/metrics')
@require_api_key
def api_metrics():
    """API endpoint for metrics - includes both closed trades AND open positions"""
    from omnix_dashboard.utils.database import DB_AVAILABLE
    
    result = get_paper_trades(30, return_dict=True)
    
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


@core_bp.route('/api/trades')
@require_api_key
def api_trades():
    """API endpoint for recent trades"""
    result = get_paper_trades(30, return_dict=True)
    
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
    curve_data = [{'date': (datetime.now() - timedelta(days=30)).isoformat(), 'equity': initial_capital}]
    
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
    """API endpoint for portfolio status - V6.5 connected to real DB"""
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
                'version': '6.5 INSTITUTIONAL+',
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
    """API endpoint for open positions - V6.5 with real Kraken prices + CoinGecko fallback"""
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
    """Health check endpoint - V6.5 with pool stats for Railway healthcheck"""
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
        'version': 'V6.5 INSTITUTIONAL+',
        'db_connected': DB_AVAILABLE,
        'db_error': DB_ERROR_MESSAGE if not DB_AVAILABLE else None,
        'pool': pool_stats,
        'architecture': {
            'connection_pooling': DB_POOL is not None,
            'wsgi_server': 'gunicorn' if IS_RAILWAY else 'werkzeug',
            'environment': 'railway' if IS_RAILWAY else 'development'
        },
        'timestamp': datetime.now().isoformat()
    }), 200 if is_healthy else 503
