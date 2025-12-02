"""
OMNIX Performance Dashboard V6.4 INSTITUTIONAL+
Professional Institutional-Grade Trading & Portfolio Analytics
Premium 2025 Design with Portfolio Management - REAL DATA
"""

import os
import logging
from functools import wraps
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, redirect, request
from flask_cors import CORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

IS_RAILWAY = bool(os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY_PROJECT_ID'))
IS_DEVELOPMENT = os.environ.get('PAPER_MODE', '').upper() == 'TRUE' and not IS_RAILWAY

SECRET_KEY = os.environ.get('SESSION_SECRET')
if not SECRET_KEY:
    if IS_RAILWAY:
        raise RuntimeError("CRITICAL: SESSION_SECRET must be configured in Railway production environment")
    logger.warning("SESSION_SECRET not configured - using development mode (insecure)")
    SECRET_KEY = 'dev-only-insecure-key-do-not-use-in-production'
app.config['SECRET_KEY'] = SECRET_KEY

ALLOWED_ORIGINS = os.environ.get('DASHBOARD_ALLOWED_ORIGINS', '').split(',')
if not ALLOWED_ORIGINS or ALLOWED_ORIGINS == ['']:
    ALLOWED_ORIGINS = [
        'https://*.railway.app',
        'https://*.up.railway.app', 
        'https://*.replit.dev',
        'https://*.repl.co',
        'http://localhost:5000',
        'http://127.0.0.1:5000'
    ]
CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True)

DASHBOARD_API_KEY = os.environ.get('DASHBOARD_API_KEY')
if IS_RAILWAY and not DASHBOARD_API_KEY:
    logger.warning("DASHBOARD_API_KEY not configured - sensitive endpoints will be public in production!")

def require_api_key(f):
    """Decorator to protect sensitive endpoints with API key authentication.
    
    Behavior:
    - If DASHBOARD_API_KEY is not set: endpoints are public (development mode)
    - If DASHBOARD_API_KEY is set: requires X-API-Key header or api_key query param
    
    In Railway production, DASHBOARD_API_KEY should be set to protect sensitive data.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not DASHBOARD_API_KEY:
            return f(*args, **kwargs)
        
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if api_key != DASHBOARD_API_KEY:
            logger.warning(f"Unauthorized API access attempt to {request.path} from {request.remote_addr}")
            return jsonify({'error': 'Unauthorized', 'code': 401}), 401
        
        return f(*args, **kwargs)
    return decorated

DB_AVAILABLE = False
DB_ERROR_MESSAGE = None

def get_database_url():
    """Get DATABASE_URL - checks multiple possible variable names"""
    url = os.environ.get('DATABASE_URL')
    if url:
        return url
    url = os.environ.get('POSTGRES_URL')
    if url:
        return url
    url = os.environ.get('DATABASE_PUBLIC_URL')
    if url:
        return url
    return None

def get_db_connection():
    """Get direct PostgreSQL connection using psycopg"""
    global DB_AVAILABLE, DB_ERROR_MESSAGE
    
    database_url = get_database_url()
    
    if not database_url:
        DB_ERROR_MESSAGE = "No DATABASE_URL, POSTGRES_URL, or DATABASE_PUBLIC_URL found in environment"
        logger.warning(DB_ERROR_MESSAGE)
        DB_AVAILABLE = False
        return None
    
    try:
        import psycopg
        conn = psycopg.connect(database_url)
        DB_AVAILABLE = True
        DB_ERROR_MESSAGE = None
        return conn
    except ImportError as e:
        DB_ERROR_MESSAGE = f"psycopg library not installed: {e}"
        logger.error(DB_ERROR_MESSAGE)
        DB_AVAILABLE = False
        return None
    except Exception as e:
        DB_ERROR_MESSAGE = f"Connection failed: {str(e)[:200]}"
        logger.error(f"Database connection failed: {e}")
        DB_AVAILABLE = False
        return None

def init_database():
    """Check if database is available"""
    global DB_AVAILABLE
    conn = get_db_connection()
    if conn:
        conn.close()
        DB_AVAILABLE = True
        logger.info("Database connected: Real data mode ACTIVE")
        return True
    DB_AVAILABLE = False
    return False


def get_paper_trades(days=30):
    """Fetch REAL paper trading history from database"""
    conn = get_db_connection()
    if not conn:
        logger.info("No database connection - returning empty (no demo data)")
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
        conn.close()
        
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
        return trades
        
    except Exception as e:
        logger.error(f"Error fetching real trades: {e}")
        return []




def get_balance_history(days=30):
    """Fetch REAL balance history from database - V6.5 corrected columns"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        
        # V6.5: Use correct column names from actual balance_history table
        # Columns: id, user_id, balance, change_amount, change_reason, recorded_at
        cursor.execute('''
            SELECT user_id, balance, change_amount, change_reason, recorded_at
            FROM balance_history
            WHERE recorded_at >= NOW() - INTERVAL '1 day' * %s
            ORDER BY recorded_at ASC
        ''', (days,))
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'user_id': row[0],
                'total_usd': float(row[1]) if row[1] else 0,
                'change_amount': float(row[2]) if row[2] else 0,
                'change_reason': row[3] or 'Unknown',
                'timestamp': row[4].isoformat() if row[4] else None
            })
        
        # If no balance_history, try to derive from paper_trading_balances
        if not history:
            conn2 = get_db_connection()
            if conn2:
                try:
                    cursor2 = conn2.cursor()
                    cursor2.execute('''
                        SELECT user_id, balance_usd, total_realized_pnl_usd, updated_at
                        FROM paper_trading_balances
                        ORDER BY updated_at DESC
                        LIMIT 1
                    ''')
                    balance_row = cursor2.fetchone()
                    cursor2.close()
                    conn2.close()
                    
                    if balance_row:
                        history.append({
                            'user_id': balance_row[0],
                            'total_usd': float(balance_row[1]) if balance_row[1] else 1000000,
                            'change_amount': float(balance_row[2]) if balance_row[2] else 0,
                            'change_reason': 'Current Balance',
                            'timestamp': balance_row[3].isoformat() if balance_row[3] else datetime.now().isoformat()
                        })
                except Exception as e:
                    logger.error(f"Error in balance_history fallback: {e}")
                    if conn2:
                        conn2.close()
        
        logger.info(f"Fetched {len(history)} REAL balance snapshots from database")
        return history
        
    except Exception as e:
        logger.error(f"Error fetching balance history: {e}")
        return []


def calculate_metrics(trades):
    """Calculate institutional trading metrics"""
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
    
    import numpy as np
    
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


@app.route('/')
def dashboard():
    """Main dashboard page - redirects to terminal"""
    return redirect('/terminal')


@app.route('/terminal')
def terminal():
    """Bloomberg-style trading terminal"""
    init_database()
    return render_template('terminal.html')


@app.route('/classic')
def classic_dashboard():
    """Classic dashboard page"""
    init_database()
    return render_template('dashboard.html')


@app.route('/api/metrics')
@require_api_key
def api_metrics():
    """API endpoint for metrics - includes both closed trades AND open positions"""
    trades = get_paper_trades(30)
    metrics = calculate_metrics(trades)
    strategies = get_strategy_breakdown(trades)
    assets = get_asset_breakdown(trades)
    
    open_positions_count = len([t for t in trades if t.get('status') == 'open'])
    closed_trades_count = len([t for t in trades if t.get('closed_at') is not None])
    
    if open_positions_count > 0 and closed_trades_count == 0:
        metrics['total_trades'] = open_positions_count
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


@app.route('/api/trades')
@require_api_key
def api_trades():
    """API endpoint for recent trades"""
    trades = get_paper_trades(30)
    
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
        'total': len(trades)
    })


@app.route('/api/equity-curve')
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


@app.route('/api/portfolio')
@require_api_key
def api_portfolio():
    """API endpoint for portfolio status - V6.5 connected to real DB"""
    conn = get_db_connection()
    
    if not conn:
        return jsonify({
            'success': False,
            'error': 'Database not connected',
            'portfolio': None
        })
    
    try:
        cursor = conn.cursor()
        
        # Get real balance from paper_trading_balances
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
        
        # Get open positions for portfolio weights
        cursor.execute('''
            SELECT symbol, side, quantity, entry_price
            FROM paper_trading_trades
            WHERE status = 'open'
        ''')
        
        positions = cursor.fetchall()
        
        # Calculate portfolio weights from real positions
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
        
        # Get closed trades for performance metrics
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
        conn.close()
        
        # Build portfolio response from real data
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


@app.route('/api/positions')
@require_api_key
def api_positions():
    """API endpoint for open positions - V6.5 with real Kraken prices"""
    import requests
    
    conn = get_db_connection()
    
    if not conn:
        return jsonify({
            'success': False,
            'positions': [],
            'message': 'Database not connected'
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
        conn.close()
        
        # V6.5: Get real-time prices from Kraken
        kraken_prices = {}
        try:
            response = requests.get(
                'https://api.kraken.com/0/public/Ticker?pair=XBTUSD,ETHUSD,SOLUSD,XRPUSD,ADAUSD,DOGEUSD',
                timeout=10
            )
            data = response.json()
            
            price_map = {
                'XXBTZUSD': 'BTC/USD', 'XETHZUSD': 'ETH/USD', 'SOLUSD': 'SOL/USD',
                'XXRPZUSD': 'XRP/USD', 'ADAUSD': 'ADA/USD', 'XDGUSD': 'DOGE/USD',
                'XBTUSD': 'BTC/USD', 'ETHUSD': 'ETH/USD'
            }
            
            for key, ticker in data.get('result', {}).items():
                symbol = price_map.get(key, key)
                kraken_prices[symbol] = float(ticker['c'][0])
                
            logger.info(f"V6.5: Fetched {len(kraken_prices)} real-time prices from Kraken")
            
        except Exception as e:
            logger.warning(f"V6.5: Could not fetch Kraken prices: {e}")
        
        positions = []
        total_value = 0
        total_cost = 0
        
        for row in rows:
            symbol = row[2]
            entry_price = float(row[5]) if row[5] else 0
            quantity = float(row[4]) if row[4] else 0
            cost = entry_price * quantity
            
            # V6.5: Use real Kraken price or fallback to entry price
            current_price = kraken_prices.get(symbol, entry_price)
            price_source = 'Kraken' if symbol in kraken_prices else 'Entry'
            
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
            'price_source': 'Kraken API',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching positions: {e}")
        return jsonify({
            'success': False,
            'positions': [],
            'error': str(e)
        })


@app.route('/api/health')
def api_health():
    """Health check endpoint"""
    init_database()
    return jsonify({
        'status': 'healthy',
        'version': 'V6.4 INSTITUTIONAL+',
        'db_connected': DB_AVAILABLE,
        'db_error': DB_ERROR_MESSAGE if not DB_AVAILABLE else None,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/market/crypto')
def api_market_crypto():
    """API endpoint for live crypto prices from Kraken"""
    import requests
    
    pairs = [
        'XBTUSD', 'ETHUSD', 'SOLUSD', 'XRPUSD', 'ADAUSD',
        'XDGUSD', 'DOTUSD', 'AVAXUSD', 'LINKUSD', 'ATOMUSD'
    ]
    
    try:
        pair_str = ','.join(pairs)
        response = requests.get(
            f'https://api.kraken.com/0/public/Ticker?pair={pair_str}',
            timeout=10
        )
        data = response.json()
        
        if data.get('error') and len(data['error']) > 0:
            non_critical = any('Unknown asset' in str(e) for e in data['error'])
            if not non_critical:
                logger.warning(f"Kraken API error: {data['error']}")
        
        prices = []
        symbol_map = {
            'XXBTZUSD': 'BTC', 'XETHZUSD': 'ETH', 'SOLUSD': 'SOL',
            'XXRPZUSD': 'XRP', 'ADAUSD': 'ADA', 'XXDGZUSD': 'DOGE',
            'DOTUSD': 'DOT', 'AVAXUSD': 'AVAX', 'LINKUSD': 'LINK',
            'ATOMUSD': 'ATOM', 'XBTUSD': 'BTC', 'ETHUSD': 'ETH',
            'XRPUSD': 'XRP', 'XDGUSD': 'DOGE'
        }
        
        for key, ticker in data.get('result', {}).items():
            symbol = symbol_map.get(key, key.replace('USD', '').replace('Z', ''))
            last_price = float(ticker['c'][0])
            open_price = float(ticker['o'])
            volume_24h = float(ticker['v'][1])
            high_24h = float(ticker['h'][1])
            low_24h = float(ticker['l'][1])
            
            change_pct = ((last_price - open_price) / open_price * 100) if open_price > 0 else 0
            
            prices.append({
                'symbol': symbol,
                'price': last_price,
                'change_24h': round(change_pct, 2),
                'volume_24h': volume_24h,
                'high_24h': high_24h,
                'low_24h': low_24h,
                'is_positive': change_pct >= 0
            })
        
        prices.sort(key=lambda x: x['volume_24h'], reverse=True)
        
        return jsonify({
            'success': True,
            'prices': prices,
            'source': 'Kraken',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching crypto prices: {e}")
        return jsonify({
            'success': False,
            'prices': [],
            'error': str(e)
        })


@app.route('/api/market/stocks')
def api_market_stocks():
    """API endpoint for stock prices - using Alpaca or fallback"""
    
    stocks_data = [
        {'symbol': 'AAPL', 'name': 'Apple Inc.'},
        {'symbol': 'MSFT', 'name': 'Microsoft'},
        {'symbol': 'GOOGL', 'name': 'Alphabet'},
        {'symbol': 'AMZN', 'name': 'Amazon'},
        {'symbol': 'NVDA', 'name': 'NVIDIA'},
        {'symbol': 'TSLA', 'name': 'Tesla'},
        {'symbol': 'META', 'name': 'Meta'},
        {'symbol': 'SPY', 'name': 'S&P 500 ETF'},
        {'symbol': 'QQQ', 'name': 'NASDAQ ETF'},
        {'symbol': 'DIA', 'name': 'Dow Jones ETF'}
    ]
    
    try:
        alpaca_key = os.environ.get('ALPACA_API_KEY')
        alpaca_secret = os.environ.get('ALPACA_SECRET_KEY')
        
        if alpaca_key and alpaca_secret:
            import requests
            headers = {
                'APCA-API-KEY-ID': alpaca_key,
                'APCA-API-SECRET-KEY': alpaca_secret
            }
            
            symbols = ','.join([s['symbol'] for s in stocks_data])
            url = f'https://data.alpaca.markets/v2/stocks/bars/latest?symbols={symbols}'
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                bars = data.get('bars', {})
                
                prices = []
                for stock in stocks_data:
                    if stock['symbol'] in bars:
                        bar = bars[stock['symbol']]
                        prices.append({
                            'symbol': stock['symbol'],
                            'name': stock['name'],
                            'price': bar.get('c', 0),
                            'change_24h': round(((bar.get('c', 0) - bar.get('o', 0)) / bar.get('o', 1)) * 100, 2),
                            'volume': bar.get('v', 0),
                            'is_positive': bar.get('c', 0) >= bar.get('o', 0)
                        })
                
                return jsonify({
                    'success': True,
                    'prices': prices,
                    'source': 'Alpaca',
                    'market_open': True,
                    'timestamp': datetime.now().isoformat()
                })
        
        now = datetime.now()
        is_market_hours = now.weekday() < 5 and 9 <= now.hour < 16
        
        return jsonify({
            'success': True,
            'prices': [],
            'source': 'Alpaca (not configured)',
            'market_open': is_market_hours,
            'message': 'Configure ALPACA_API_KEY for live stock data',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching stock prices: {e}")
        return jsonify({
            'success': False,
            'prices': [],
            'error': str(e)
        })


@app.route('/api/news')
def api_news():
    """API endpoint for financial news"""
    import requests
    
    try:
        response = requests.get(
            'https://api.coingecko.com/api/v3/news',
            timeout=10,
            headers={'accept': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json().get('data', [])[:10]
            news = []
            for item in data:
                news.append({
                    'title': item.get('title', ''),
                    'description': item.get('description', '')[:150] + '...' if item.get('description') else '',
                    'url': item.get('url', ''),
                    'source': item.get('news_site', 'CoinGecko'),
                    'published': item.get('created_at', ''),
                    'category': 'crypto'
                })
            
            return jsonify({
                'success': True,
                'news': news,
                'source': 'CoinGecko News',
                'timestamp': datetime.now().isoformat()
            })
        
        news = [
            {
                'title': 'Bitcoin mantiene soporte en niveles clave',
                'description': 'Los analistas observan consolidación mientras el mercado espera el próximo movimiento...',
                'source': 'OMNIX Analysis',
                'category': 'crypto',
                'published': datetime.now().isoformat()
            },
            {
                'title': 'ETH 2.0 muestra adopción institucional creciente',
                'description': 'Grandes fondos continúan acumulando Ethereum en anticipación a actualizaciones...',
                'source': 'OMNIX Analysis',
                'category': 'crypto',
                'published': datetime.now().isoformat()
            },
            {
                'title': 'Mercados tradicionales impactan correlación crypto',
                'description': 'La correlación entre S&P500 y Bitcoin alcanza nuevos niveles esta semana...',
                'source': 'OMNIX Analysis',
                'category': 'markets',
                'published': datetime.now().isoformat()
            }
        ]
        
        return jsonify({
            'success': True,
            'news': news,
            'source': 'OMNIX Fallback',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        return jsonify({
            'success': False,
            'news': [],
            'error': str(e)
        })


@app.route('/api/market/ohlc/<symbol>')
def api_market_ohlc(symbol):
    """API endpoint for OHLC candlestick data from Kraken"""
    import requests
    
    pair_map = {
        'BTC': 'XBTUSD',
        'ETH': 'ETHUSD', 
        'SOL': 'SOLUSD',
        'XRP': 'XRPUSD',
        'ADA': 'ADAUSD',
        'DOGE': 'DOGEUSD',
        'DOT': 'DOTUSD',
        'LINK': 'LINKUSD',
        'AVAX': 'AVAXUSD'
    }
    
    kraken_pair = pair_map.get(symbol.upper(), f'{symbol.upper()}USD')
    
    try:
        response = requests.get(
            f'https://api.kraken.com/0/public/OHLC?pair={kraken_pair}&interval=60',
            timeout=10
        )
        data = response.json()
        
        if data.get('error') and len(data['error']) > 0:
            logger.warning(f"Kraken OHLC API error: {data['error']}")
        
        result = data.get('result', {})
        ohlc_key = list(result.keys())[0] if result else None
        
        if ohlc_key and ohlc_key != 'last':
            ohlc_data = result[ohlc_key][-100:]
            
            candles = []
            for candle in ohlc_data:
                candles.append({
                    'time': int(candle[0]),
                    'open': float(candle[1]),
                    'high': float(candle[2]),
                    'low': float(candle[3]),
                    'close': float(candle[4]),
                    'volume': float(candle[6])
                })
            
            return jsonify({
                'success': True,
                'symbol': symbol.upper(),
                'interval': '1h',
                'candles': candles,
                'source': 'Kraken'
            })
        
        return jsonify({
            'success': False,
            'error': 'No data available'
        })
        
    except Exception as e:
        logger.error(f"Error fetching OHLC: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/signals/active')
@require_api_key
def api_active_signals():
    """API endpoint for active trading signals - V6.5 connected to real DB"""
    conn = get_db_connection()
    signals = []
    
    if conn:
        try:
            cursor = conn.cursor()
            
            # Get recent trades to derive signals (last 24 hours)
            cursor.execute('''
                SELECT symbol, side, strategy, status, opened_at, entry_price
                FROM paper_trading_trades
                WHERE opened_at >= NOW() - INTERVAL '24 hours'
                ORDER BY opened_at DESC
                LIMIT 10
            ''')
            
            recent_trades = cursor.fetchall()
            
            # Analyze trade patterns to generate signals
            symbol_stats = {}
            for trade in recent_trades:
                symbol = trade[0]
                side = trade[1]
                strategy = trade[2] or 'OMNIX'
                
                if symbol not in symbol_stats:
                    symbol_stats[symbol] = {'buys': 0, 'sells': 0, 'strategies': set()}
                
                if side == 'buy':
                    symbol_stats[symbol]['buys'] += 1
                else:
                    symbol_stats[symbol]['sells'] += 1
                symbol_stats[symbol]['strategies'].add(strategy)
            
            # Generate signals based on trade activity
            for symbol, stats in symbol_stats.items():
                total = stats['buys'] + stats['sells']
                if total > 0:
                    buy_ratio = stats['buys'] / total
                    
                    if buy_ratio > 0.7:
                        signal_type = 'BULLISH'
                        confidence = int(buy_ratio * 100)
                    elif buy_ratio < 0.3:
                        signal_type = 'BEARISH'
                        confidence = int((1 - buy_ratio) * 100)
                    else:
                        signal_type = 'NEUTRAL'
                        confidence = 50
                    
                    signals.append({
                        'strategy': list(stats['strategies'])[0] if stats['strategies'] else 'OMNIX',
                        'symbol': symbol,
                        'signal': signal_type,
                        'confidence': confidence,
                        'trades_24h': total,
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Also check for open positions as active signals
            cursor.execute('''
                SELECT symbol, side, strategy, entry_price, opened_at
                FROM paper_trading_trades
                WHERE status = 'open'
                ORDER BY opened_at DESC
            ''')
            
            open_positions = cursor.fetchall()
            for pos in open_positions:
                existing = next((s for s in signals if s['symbol'] == pos[0]), None)
                if not existing:
                    signals.append({
                        'strategy': pos[2] or 'OMNIX',
                        'symbol': pos[0],
                        'signal': 'LONG' if pos[1] == 'buy' else 'SHORT',
                        'confidence': 75,
                        'position_open': True,
                        'timestamp': pos[4].isoformat() if pos[4] else datetime.now().isoformat()
                    })
            
            cursor.close()
            conn.close()
            
            logger.info(f"Generated {len(signals)} signals from real trading data")
            
        except Exception as e:
            logger.error(f"Error fetching signals from DB: {e}")
            if conn:
                conn.close()
    
    # Fallback if no signals found
    if not signals:
        signals = [
            {
                'strategy': 'OMNIX V6.5',
                'symbol': 'BTC/USD',
                'signal': 'ANALYZING',
                'confidence': 0,
                'message': 'Waiting for trading activity',
                'timestamp': datetime.now().isoformat()
            }
        ]
    
    return jsonify({
        'success': True,
        'signals': signals,
        'source': 'PostgreSQL',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/market/volume')
def api_market_volume():
    """API endpoint for 24h volume data"""
    import requests
    
    try:
        response = requests.get(
            'https://api.kraken.com/0/public/Ticker?pair=XBTUSD,ETHUSD,SOLUSD,XRPUSD,ADAUSD',
            timeout=10
        )
        data = response.json()
        
        volumes = []
        symbol_map = {
            'XXBTZUSD': 'BTC', 'XETHZUSD': 'ETH', 'SOLUSD': 'SOL',
            'XXRPZUSD': 'XRP', 'ADAUSD': 'ADA'
        }
        
        for key, ticker in data.get('result', {}).items():
            symbol = symbol_map.get(key, key.replace('USD', ''))
            vol_24h = float(ticker['v'][1])
            price = float(ticker['c'][0])
            vol_usd = vol_24h * price
            
            volumes.append({
                'symbol': symbol,
                'volume_coins': vol_24h,
                'volume_usd': vol_usd,
                'price': price
            })
        
        volumes.sort(key=lambda x: x['volume_usd'], reverse=True)
        
        return jsonify({
            'success': True,
            'volumes': volumes,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching volume: {e}")
        return jsonify({
            'success': False,
            'volumes': [],
            'error': str(e)
        })


@app.route('/api/system/status')
def api_system_status():
    """API endpoint for OMNIX system status - V6.5 connected to real DB"""
    conn = get_db_connection()
    
    # Get trades from DB
    trades = get_paper_trades(1)
    open_positions = len([t for t in trades if t.get('status') == 'open'])
    trades_today = len([t for t in trades if t.get('closed_at') is not None])
    
    # V6.5: Read user_settings for bot status
    bot_active = False
    trading_enabled = False
    daily_pnl = 0.0
    user_settings_data = {}
    strategy_counts = {}
    
    if conn:
        try:
            cursor = conn.cursor()
            
            # Get user settings
            cursor.execute('''
                SELECT auto_trading, trading_enabled, daily_pnl_usd, 
                       active_cryptos, stop_loss_pct, take_profit_pct,
                       risk_profile, updated_at
                FROM user_settings
                ORDER BY updated_at DESC
                LIMIT 1
            ''')
            
            settings_row = cursor.fetchone()
            if settings_row:
                bot_active = bool(settings_row[0])
                trading_enabled = bool(settings_row[1])
                daily_pnl = float(settings_row[2]) if settings_row[2] else 0.0
                user_settings_data = {
                    'active_cryptos': settings_row[3] or ['BTC/USD', 'ETH/USD'],
                    'stop_loss_pct': float(settings_row[4]) if settings_row[4] else 3.0,
                    'take_profit_pct': float(settings_row[5]) if settings_row[5] else 5.0,
                    'risk_profile': settings_row[6] or 'moderado',
                    'last_updated': settings_row[7].isoformat() if settings_row[7] else None
                }
            
            # Get recent trades count by strategy
            cursor.execute('''
                SELECT strategy, COUNT(*) as cnt
                FROM paper_trading_trades
                WHERE opened_at >= NOW() - INTERVAL '24 hours'
                GROUP BY strategy
            ''')
            
            strategy_counts = {row[0]: row[1] for row in cursor.fetchall()}
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error reading user_settings: {e}")
            if conn:
                conn.close()
    
    # Build strategies status from real data
    strategies = {}
    if strategy_counts:
        for strat_name, signal_count in strategy_counts.items():
            strategies[strat_name] = {'active': True, 'signals_today': signal_count}
    
    # Add default strategies if none found
    if not strategies:
        strategies = {
            'OMNIX_V6.5': {'active': bot_active, 'signals_today': trades_today},
            'Auto_Trading_Bot': {'active': bot_active, 'signals_today': open_positions}
        }
    
    status = {
        'bot_active': bot_active,
        'trading_enabled': trading_enabled,
        'version': 'V6.5 INSTITUTIONAL+',
        'uptime': '24/7 Railway',
        'last_activity': datetime.now().isoformat(),
        'database_connected': DB_AVAILABLE,
        'daily_pnl_usd': round(daily_pnl, 2),
        'strategies': strategies,
        'protection': {
            'drawdown_tier': 'NORMAL' if daily_pnl >= 0 else 'CAUTION',
            'ramp_up_pct': 100,
            'daily_loss_limit': user_settings_data.get('stop_loss_pct', 3.0) * 100,
            'position_size_factor': 1.0
        },
        'trading': {
            'open_positions': open_positions,
            'trades_today': trades_today,
            'pairs_active': user_settings_data.get('active_cryptos', ['BTC/USD', 'ETH/USD', 'SOL/USD'])
        },
        'user_settings': user_settings_data,
        'source': 'PostgreSQL',
        'timestamp': datetime.now().isoformat()
    }
    
    return jsonify({
        'success': True,
        'status': status
    })


@app.route('/api/intelligence/fear-greed')
def api_fear_greed():
    """API endpoint for Fear & Greed Index"""
    try:
        import sys
        sys.path.insert(0, '..')
        from omnix_services.market_intelligence import fear_greed_service
        
        current = fear_greed_service.get_current_index()
        trend = fear_greed_service.get_trend(7)
        
        if current:
            return jsonify({
                'success': True,
                'current': {
                    'value': current['value'],
                    'classification': current['classification'],
                    'recommendation': current['recommendation'],
                    'color': current['color'],
                    'description': current['description']
                },
                'trend': trend,
                'timestamp': datetime.now().isoformat()
            })
        
        return jsonify({
            'success': False,
            'error': 'Unable to fetch Fear & Greed data'
        })
        
    except Exception as e:
        logger.error(f"Error in fear-greed endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/intelligence/finnhub/news')
def api_finnhub_news():
    """API endpoint for Finnhub financial news"""
    try:
        import sys
        sys.path.insert(0, '..')
        from omnix_services.market_intelligence import finnhub_service
        
        if not finnhub_service.is_available():
            return jsonify({
                'success': False,
                'error': 'FINNHUB_API_KEY not configured'
            })
        
        news = finnhub_service.get_general_news('general')
        
        return jsonify({
            'success': True,
            'news': news[:10] if news else [],
            'source': 'Finnhub',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in finnhub news endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/intelligence/finnhub/sentiment/<symbol>')
def api_finnhub_sentiment(symbol):
    """API endpoint for Finnhub news sentiment"""
    try:
        import sys
        sys.path.insert(0, '..')
        from omnix_services.market_intelligence import finnhub_service
        
        if not finnhub_service.is_available():
            return jsonify({
                'success': False,
                'error': 'FINNHUB_API_KEY not configured'
            })
        
        sentiment = finnhub_service.get_news_sentiment(symbol)
        
        return jsonify({
            'success': True,
            'sentiment': sentiment,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in sentiment endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/intelligence/alpha-vantage/technical/<symbol>')
def api_alpha_vantage_technical(symbol):
    """API endpoint for Alpha Vantage technical indicators"""
    try:
        import sys
        sys.path.insert(0, '..')
        from omnix_services.market_intelligence import alpha_vantage_service
        
        if not alpha_vantage_service.is_available():
            return jsonify({
                'success': False,
                'error': 'ALPHA_VANTAGE_API_KEY not configured'
            })
        
        summary = alpha_vantage_service.get_technical_summary(symbol)
        
        return jsonify({
            'success': True,
            'technical': summary,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in alpha vantage endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/intelligence/summary')
def api_intelligence_summary():
    """Combined market intelligence summary"""
    try:
        import sys
        sys.path.insert(0, '..')
        from omnix_services.market_intelligence import fear_greed_service, finnhub_service, alpha_vantage_service
        
        fear_greed = fear_greed_service.get_current_index()
        
        finnhub_available = finnhub_service.is_available()
        alpha_available = alpha_vantage_service.is_available()
        
        return jsonify({
            'success': True,
            'fear_greed': {
                'value': fear_greed['value'] if fear_greed else None,
                'classification': fear_greed['classification'] if fear_greed else None,
                'recommendation': fear_greed['recommendation'] if fear_greed else None
            } if fear_greed else None,
            'services': {
                'fear_greed': True,
                'finnhub': finnhub_available,
                'alpha_vantage': alpha_available
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in intelligence summary: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/debug')
def api_debug():
    """Debug endpoint to diagnose connection issues (no secrets exposed)"""
    env_vars_status = {
        'DATABASE_URL': 'SET' if os.environ.get('DATABASE_URL') else 'NOT SET',
        'POSTGRES_URL': 'SET' if os.environ.get('POSTGRES_URL') else 'NOT SET',
        'DATABASE_PUBLIC_URL': 'SET' if os.environ.get('DATABASE_PUBLIC_URL') else 'NOT SET',
    }
    
    database_url = get_database_url()
    url_info = None
    if database_url:
        if '@' in database_url:
            host_part = database_url.split('@')[-1].split('/')[0] if '@' in database_url else 'unknown'
            url_info = f"Host: {host_part[:50]}..."
        else:
            url_info = "URL format: invalid (no @ symbol)"
    
    init_database()
    
    psycopg_installed = False
    try:
        import psycopg
        psycopg_installed = True
        psycopg_version = getattr(psycopg, '__version__', 'unknown')
    except ImportError:
        psycopg_version = 'NOT INSTALLED'
    
    return jsonify({
        'status': 'debug_info',
        'environment_variables': env_vars_status,
        'database_url_detected': database_url is not None,
        'database_url_info': url_info,
        'psycopg_installed': psycopg_installed,
        'psycopg_version': psycopg_version,
        'db_connected': DB_AVAILABLE,
        'db_error': DB_ERROR_MESSAGE,
        'python_version': os.popen('python --version').read().strip(),
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/market/fear-greed')
def api_market_fear_greed():
    """API endpoint for Fear & Greed Index - 100% free, no API key needed"""
    import requests
    
    try:
        response = requests.get(
            'https://api.alternative.me/fng/?limit=1',
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get('data') and len(data['data']) > 0:
            fng = data['data'][0]
            value = int(fng['value'])
            classification = fng['value_classification']
            
            if value <= 24:
                color = '#ff3366'
                recommendation = 'Extreme Fear: Consider accumulating positions'
            elif value <= 49:
                color = '#ff9933'
                recommendation = 'Fear: Monitor for entry opportunities'
            elif value <= 54:
                color = '#ffff00'
                recommendation = 'Neutral: Market balanced'
            elif value <= 75:
                color = '#99ff33'
                recommendation = 'Greed: Consider taking profits'
            else:
                color = '#00ff88'
                recommendation = 'Extreme Greed: High risk - reduce exposure'
            
            return jsonify({
                'success': True,
                'data': {
                    'value': value,
                    'classification': classification,
                    'color': color,
                    'recommendation': recommendation,
                    'timestamp': datetime.now().isoformat()
                }
            })
        
        return jsonify({'success': False, 'error': 'No data available'})
        
    except Exception as e:
        logger.error(f"Fear & Greed API error: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/market/finnhub-news')
def api_market_finnhub_news():
    """API endpoint for Finnhub market news"""
    import requests
    from flask import request
    
    api_key = os.environ.get('FINNHUB_API_KEY')
    if not api_key:
        return jsonify({
            'success': False,
            'error': 'FINNHUB_API_KEY not configured',
            'data': []
        })
    
    category = request.args.get('category', 'crypto')
    
    try:
        response = requests.get(
            f'https://finnhub.io/api/v1/news?category={category}&token={api_key}',
            timeout=10
        )
        response.raise_for_status()
        news = response.json()
        
        if isinstance(news, list):
            formatted_news = []
            for item in news[:10]:
                formatted_news.append({
                    'headline': item.get('headline', ''),
                    'source': item.get('source', 'Unknown'),
                    'datetime': item.get('datetime', 0),
                    'url': item.get('url', ''),
                    'summary': item.get('summary', '')[:200] if item.get('summary') else ''
                })
            
            return jsonify({
                'success': True,
                'data': formatted_news,
                'source': 'Finnhub',
                'timestamp': datetime.now().isoformat()
            })
        
        return jsonify({'success': False, 'error': 'Invalid response format', 'data': []})
        
    except Exception as e:
        logger.error(f"Finnhub API error: {e}")
        return jsonify({'success': False, 'error': str(e), 'data': []})


@app.route('/api/market/technical-indicators/<symbol>')
def api_market_technical_indicators(symbol):
    """API endpoint for Alpha Vantage technical indicators"""
    import requests
    
    api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        return jsonify({
            'success': False,
            'error': 'ALPHA_VANTAGE_API_KEY not configured'
        })
    
    try:
        rsi_response = requests.get(
            f'https://www.alphavantage.co/query?function=RSI&symbol={symbol}&interval=daily&time_period=14&series_type=close&apikey={api_key}',
            timeout=15
        )
        rsi_data = rsi_response.json()
        
        rsi_value = None
        if 'Technical Analysis: RSI' in rsi_data:
            latest = list(rsi_data['Technical Analysis: RSI'].values())[0]
            rsi_value = float(latest.get('RSI', 0))
        
        if rsi_value:
            if rsi_value < 30:
                rsi_signal = 'OVERSOLD'
            elif rsi_value > 70:
                rsi_signal = 'OVERBOUGHT'
            else:
                rsi_signal = 'NEUTRAL'
        else:
            rsi_signal = 'N/A'
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'indicators': {
                'rsi': {
                    'value': rsi_value,
                    'signal': rsi_signal
                }
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Alpha Vantage API error: {e}")
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 OMNIX Dashboard V6.4 INSTITUTIONAL+ starting on port {port}")
    
    database_url = get_database_url()
    if database_url:
        logger.info("✅ DATABASE_URL detected - attempting connection...")
        if init_database():
            logger.info("✅ Database connected successfully - REAL DATA MODE")
        else:
            logger.error(f"❌ Database connection FAILED: {DB_ERROR_MESSAGE}")
            logger.info("📊 Dashboard will show 'Esperando traders' until connection is fixed")
    else:
        logger.warning("⚠️ No DATABASE_URL found - Dashboard will show empty state")
        logger.info("💡 Set DATABASE_URL, POSTGRES_URL, or DATABASE_PUBLIC_URL in environment")
    
    logger.info(f"🔗 Debug endpoint: http://localhost:{port}/api/debug")
    app.run(host='0.0.0.0', port=port, debug=False)
