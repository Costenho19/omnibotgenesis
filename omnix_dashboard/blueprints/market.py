"""
OMNIX Dashboard - Market Blueprint
Market API routes (/api/market/crypto, stocks, ohlc, volume, fear-greed, finnhub-news, technical-indicators)
"""

import os
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request

from omnix_dashboard.utils.external_apis import http_get_with_timeout

logger = logging.getLogger(__name__)

market_bp = Blueprint('market', __name__)


@market_bp.route('/api/market/crypto')
def api_market_crypto():
    """API endpoint for live crypto prices from Kraken"""
    pairs = [
        'XBTUSD', 'ETHUSD', 'SOLUSD', 'XRPUSD', 'ADAUSD',
        'XDGUSD', 'DOTUSD', 'AVAXUSD', 'LINKUSD', 'ATOMUSD'
    ]
    
    pair_str = ','.join(pairs)
    url = f'https://api.kraken.com/0/public/Ticker?pair={pair_str}'
    
    data = http_get_with_timeout(url, timeout=10, fallback=None)
    
    if data is None:
        return jsonify({'success': False, 'prices': [], 'error': 'Timeout fetching crypto prices', 'source': 'Kraken'})
    
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
        try:
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
        except (KeyError, IndexError, TypeError) as e:
            logger.debug(f"Skipping ticker {key}: {e}")
    
    prices.sort(key=lambda x: x['volume_24h'], reverse=True)
    
    return jsonify({
        'success': True,
        'prices': prices,
        'source': 'Kraken',
        'timestamp': datetime.now().isoformat()
    })


@market_bp.route('/api/market/stocks')
def api_market_stocks():
    """API endpoint for stock prices - using Alpaca"""
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
    
    alpaca_key = os.environ.get('ALPACA_API_KEY')
    alpaca_secret = os.environ.get('ALPACA_SECRET_KEY')
    
    if alpaca_key and alpaca_secret:
        headers = {
            'APCA-API-KEY-ID': alpaca_key,
            'APCA-API-SECRET-KEY': alpaca_secret
        }
        
        symbols = ','.join([s['symbol'] for s in stocks_data])
        url = f'https://data.alpaca.markets/v2/stocks/bars/latest?symbols={symbols}'
        
        data = http_get_with_timeout(url, headers=headers, timeout=10, fallback=None)
        
        if data and data.get('bars'):
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


@market_bp.route('/api/market/ohlc/<symbol>')
def api_market_ohlc(symbol):
    """API endpoint for OHLC candlestick data from Kraken"""
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
    url = f'https://api.kraken.com/0/public/OHLC?pair={kraken_pair}&interval=60'
    
    data = http_get_with_timeout(url, timeout=10, fallback=None)
    
    if data is None:
        return jsonify({'success': False, 'error': 'Timeout fetching OHLC data'})
    
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


@market_bp.route('/api/market/volume')
def api_market_volume():
    """API endpoint for 24h volume data"""
    url = 'https://api.kraken.com/0/public/Ticker?pair=XBTUSD,ETHUSD,SOLUSD,XRPUSD,ADAUSD'
    data = http_get_with_timeout(url, timeout=10, fallback=None)
    
    if data is None:
        return jsonify({'success': False, 'volumes': [], 'error': 'Timeout fetching volume data'})
    
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


@market_bp.route('/api/market/fear-greed')
def api_market_fear_greed():
    """API endpoint for Fear & Greed Index"""
    url = 'https://api.alternative.me/fng/?limit=1'
    data = http_get_with_timeout(url, timeout=10, fallback=None)
    
    if data is None:
        return jsonify({'success': False, 'error': 'Timeout fetching Fear & Greed Index'})
    
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


@market_bp.route('/api/market/finnhub-news')
def api_market_finnhub_news():
    """API endpoint for Finnhub market news"""
    api_key = os.environ.get('FINNHUB_API_KEY')
    if not api_key:
        return jsonify({
            'success': False,
            'error': 'FINNHUB_API_KEY not configured',
            'data': []
        })
    
    category = request.args.get('category', 'crypto')
    url = f'https://finnhub.io/api/v1/news?category={category}&token={api_key}'
    
    news = http_get_with_timeout(url, timeout=10, fallback=None)
    
    if news is None:
        return jsonify({'success': False, 'error': 'Timeout fetching Finnhub news', 'data': []})
    
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


@market_bp.route('/api/market/technical-indicators/<symbol>')
def api_market_technical_indicators(symbol):
    """API endpoint for Alpha Vantage technical indicators"""
    api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        return jsonify({
            'success': False,
            'error': 'ALPHA_VANTAGE_API_KEY not configured'
        })
    
    url = f'https://www.alphavantage.co/query?function=RSI&symbol={symbol}&interval=daily&time_period=14&series_type=close&apikey={api_key}'
    rsi_data = http_get_with_timeout(url, timeout=15, fallback=None)
    
    if rsi_data is None:
        return jsonify({'success': False, 'error': 'Timeout fetching technical indicators'})
    
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


@market_bp.route('/api/benchmarks')
def api_benchmarks():
    """API endpoint for benchmark comparisons (BTC and SPY normalized to %)."""
    from omnix_dashboard.utils.benchmark_service import get_benchmarks
    
    days = request.args.get('days', 30, type=int)
    base_date = request.args.get('base_date', None)
    
    days = min(max(days, 7), 90)
    
    benchmarks = get_benchmarks(days=days, base_date=base_date)
    
    return jsonify({
        'success': benchmarks['success'],
        'benchmarks': {
            'btc': benchmarks['btc'],
            'spy': benchmarks['spy']
        },
        'base_date': benchmarks['base_date'],
        'btc_available': benchmarks['btc_available'],
        'spy_available': benchmarks['spy_available'],
        'days': days,
        'timestamp': datetime.now().isoformat()
    })
