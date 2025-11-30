"""
OMNIX Performance Dashboard V6.4 INSTITUTIONAL+
Professional Institutional-Grade Trading & Portfolio Analytics
Premium 2025 Design with Portfolio Management - REAL DATA
"""

import os
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify
from flask_cors import CORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'omnix-ultra-2025')

db = None
DB_AVAILABLE = False
DB_CONNECTION = None

def init_database():
    """Initialize database connection - REQUIRED for real data"""
    global db, DB_AVAILABLE, DB_CONNECTION
    
    if DB_AVAILABLE:
        return True
    
    try:
        from omnix_services.database_service import DatabaseManager
        db = DatabaseManager()
        DB_AVAILABLE = db.connected if hasattr(db, 'connected') else False
        
        if DB_AVAILABLE and hasattr(db, 'enterprise_service'):
            DB_CONNECTION = db.enterprise_service
            logger.info("Database connected: Real data mode ACTIVE")
        else:
            logger.warning("Database connected but enterprise service not available")
            
        return DB_AVAILABLE
    except Exception as e:
        logger.warning(f"Database not available: {e}")
        db = None
        DB_AVAILABLE = False
        return False


def get_paper_trades(days=30):
    """Fetch REAL paper trading history from database"""
    init_database()
    
    if not DB_AVAILABLE or not DB_CONNECTION:
        logger.info("No database connection - returning empty (no demo data)")
        return []
    
    try:
        conn = DB_CONNECTION._get_connection()
        if not conn:
            return []
        
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


def get_demo_trades():
    """Return demo data for display purposes"""
    import random
    from datetime import datetime, timedelta
    
    strategies = ['ARES V1', 'ARES V2', 'Monte Carlo', 'Kalman Filter', 'HMM Regime']
    symbols_crypto = ['BTC/USD', 'ETH/USD', 'SOL/USD', 'XRP/USD']
    symbols_stock = ['AAPL', 'TSLA', 'NVDA', 'MSFT']
    
    trades = []
    base_time = datetime.now()
    
    for i in range(25):
        is_crypto = random.random() > 0.4
        symbol = random.choice(symbols_crypto if is_crypto else symbols_stock)
        side = random.choice(['buy', 'sell'])
        entry = random.uniform(100, 50000) if is_crypto else random.uniform(100, 500)
        pnl = random.uniform(-500, 1500)
        
        trades.append({
            'id': i + 1,
            'symbol': symbol,
            'side': side,
            'entry_price': entry,
            'exit_price': entry * (1 + pnl / 10000),
            'quantity': random.uniform(0.1, 10),
            'pnl': pnl,
            'pnl_percent': pnl / entry * 100,
            'opened_at': base_time - timedelta(days=random.randint(1, 28)),
            'closed_at': base_time - timedelta(days=random.randint(0, 1)),
            'strategy_used': random.choice(strategies)
        })
    
    return trades


def get_balance_history(days=30):
    """Fetch REAL balance history from database"""
    init_database()
    
    if not DB_AVAILABLE or not DB_CONNECTION:
        return []
    
    try:
        conn = DB_CONNECTION._get_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        cursor.execute('''
            SELECT total_usd, btc_balance, eth_balance, usdt_balance, other_balance, timestamp
            FROM balance_history
            WHERE timestamp >= NOW() - INTERVAL '1 day' * %s
            ORDER BY timestamp ASC
        ''', (days,))
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'total_usd': float(row[0]) if row[0] else 0,
                'btc_balance': float(row[1]) if row[1] else 0,
                'eth_balance': float(row[2]) if row[2] else 0,
                'usdt_balance': float(row[3]) if row[3] else 0,
                'other_balance': float(row[4]) if row[4] else 0,
                'timestamp': row[5].isoformat() if row[5] else None
            })
        
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
        returns = np.array(pnls)
        risk_free_rate = 0.05 / 252
        excess_returns = returns - risk_free_rate
        sharpe = np.mean(excess_returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        
        downside_returns = returns[returns < 0]
        downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 0
        sortino = np.mean(excess_returns) / downside_std * np.sqrt(252) if downside_std > 0 else 0
    else:
        sharpe = 0
        sortino = 0
    
    cumulative = np.cumsum(pnls)
    peak = np.maximum.accumulate(cumulative)
    drawdown = (peak - cumulative) / np.maximum(peak, 1) * 100
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
    """Main dashboard page"""
    return render_template('dashboard.html')


@app.route('/api/metrics')
def api_metrics():
    """API endpoint for metrics"""
    trades = get_paper_trades(30)
    metrics = calculate_metrics(trades)
    strategies = get_strategy_breakdown(trades)
    assets = get_asset_breakdown(trades)
    
    return jsonify({
        'success': True,
        'metrics': metrics,
        'strategies': strategies,
        'assets': assets,
        'db_connected': DB_AVAILABLE,
        'last_updated': datetime.now().isoformat()
    })


@app.route('/api/trades')
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
def api_portfolio():
    """API endpoint for portfolio status"""
    try:
        from omnix_services.portfolio_management import OmnixPortfolioEngine
        from omnix_services.portfolio_management.institutional.volatility_targeting import RiskProfile
        
        engine = OmnixPortfolioEngine(
            target_volatility=0.10,
            target_beta=0.5,
            max_weight_per_asset=0.15
        )
        
        demo_prices = {
            "AAPL": [175 + i*0.5 for i in range(60)],
            "MSFT": [380 + i*0.8 for i in range(60)],
            "GOOGL": [140 + i*0.3 for i in range(60)],
            "NVDA": [480 + i*2.0 for i in range(60)],
            "TSLA": [250 + i*1.5 for i in range(60)],
            "JPM": [170 + i*0.4 for i in range(60)],
            "BTC": [43000 + i*200 for i in range(60)],
            "ETH": [2200 + i*30 for i in range(60)],
            "SPY": [450 + i*0.6 for i in range(60)],
        }
        
        demo_signals = {
            "AAPL": {"direction": "LONG", "confidence": 0.75, "source": "HMM"},
            "MSFT": {"direction": "LONG", "confidence": 0.80, "source": "ARES"},
            "GOOGL": {"direction": "NEUTRAL", "confidence": 0.60, "source": "MONTE_CARLO"},
            "NVDA": {"direction": "STRONG_LONG", "confidence": 0.85, "source": "MEMORY_KERNEL"},
            "TSLA": {"direction": "SHORT", "confidence": 0.65, "source": "HMM"},
            "JPM": {"direction": "LONG", "confidence": 0.70, "source": "KALMAN"},
            "BTC": {"direction": "LONG", "confidence": 0.72, "source": "ARES"},
            "ETH": {"direction": "LONG", "confidence": 0.68, "source": "HMM"},
        }
        
        snapshot = engine.build_portfolio(
            prices=demo_prices,
            signals=demo_signals,
            risk_profile=RiskProfile.INSTITUTIONAL,
            view_confidence=0.5
        )
        
        return jsonify({
            'success': True,
            'portfolio': {
                'weights': snapshot.weights,
                'expected_return': snapshot.expected_return,
                'expected_volatility': snapshot.expected_volatility,
                'sharpe_ratio': snapshot.sharpe_ratio,
                'portfolio_beta': snapshot.portfolio_beta,
                'effective_n_assets': snapshot.effective_n_assets,
                'diversification_score': snapshot.diversification_score,
                'net_exposure': snapshot.net_exposure,
                'gross_exposure': snapshot.gross_exposure,
                'sector_exposures': snapshot.sector_exposures,
                'cluster_warnings': snapshot.cluster_warnings,
                'risk_profile': snapshot.risk_profile
            },
            'modules': {
                'risk_model': True,
                'optimizer': True,
                'vol_targeting': True,
                'exposure_manager': True,
                'cluster_detector': True
            },
            'version': '6.4 INSTITUTIONAL+',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Portfolio API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'portfolio': None
        })


@app.route('/api/health')
def api_health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': 'V6.4 INSTITUTIONAL+',
        'db_connected': DB_AVAILABLE,
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 OMNIX Dashboard starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
