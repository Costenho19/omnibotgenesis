"""
OMNIX Performance Dashboard V6.3 ULTRA
Professional Institutional-Grade Trading Analytics
Premium 2025 Design
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

def init_database():
    """Lazy database initialization"""
    global db, DB_AVAILABLE
    if db is not None:
        return
    
    try:
        from omnix_services.database_service import DatabaseManager
        db = DatabaseManager()
        DB_AVAILABLE = db.connected if hasattr(db, 'connected') else False
        logger.info(f"Database connected: {DB_AVAILABLE}")
    except Exception as e:
        logger.warning(f"Database not available (will use demo data): {e}")
        db = None
        DB_AVAILABLE = False


def get_paper_trades(days=30):
    """Fetch paper trading history - using demo data for now"""
    return get_demo_trades()


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
    """Fetch balance snapshots for equity curve - placeholder"""
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


@app.route('/api/health')
def api_health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': 'V6.3 ULTRA',
        'db_connected': DB_AVAILABLE,
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 OMNIX Dashboard starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
