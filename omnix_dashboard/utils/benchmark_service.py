"""
OMNIX Dashboard - Benchmark Service
Fetches historical price data for BTC and SPY to compare with portfolio performance.
Uses CoinGecko (free) for BTC and Alpha Vantage for SPY.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from omnix_dashboard.utils.external_apis import http_get_with_timeout

logger = logging.getLogger(__name__)

_benchmark_cache: Dict[str, Any] = {}
CACHE_TTL_SECONDS = 3600


def _is_cache_valid(cache_key: str) -> bool:
    """Check if cached data is still valid."""
    if cache_key not in _benchmark_cache:
        return False
    cached = _benchmark_cache[cache_key]
    if 'timestamp' not in cached:
        return False
    age = (datetime.now() - cached['timestamp']).total_seconds()
    return age < CACHE_TTL_SECONDS


def get_btc_historical(days: int = 30) -> List[Dict]:
    """
    Fetch BTC/USD historical prices from CoinGecko.
    
    Args:
        days: Number of days of historical data (default 30)
    
    Returns:
        List of {date: ISO string, price: float} dictionaries
    """
    cache_key = f"btc_{days}"
    
    if _is_cache_valid(cache_key):
        logger.info(f"Using cached BTC data ({days} days)")
        return _benchmark_cache[cache_key]['data']
    
    url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days={days}&interval=daily"
    
    data = http_get_with_timeout(url, timeout=15, fallback=None)
    
    if not data or 'prices' not in data:
        logger.warning("Failed to fetch BTC historical data from CoinGecko")
        return []
    
    result = []
    for point in data['prices']:
        timestamp_ms = point[0]
        price = point[1]
        dt = datetime.fromtimestamp(timestamp_ms / 1000)
        result.append({
            'date': dt.strftime('%Y-%m-%d'),
            'price': round(price, 2)
        })
    
    _benchmark_cache[cache_key] = {
        'data': result,
        'timestamp': datetime.now()
    }
    
    logger.info(f"Fetched {len(result)} BTC price points from CoinGecko")
    return result


def get_spy_historical(days: int = 30) -> List[Dict]:
    """
    Fetch SPY historical prices from Alpha Vantage.
    
    Args:
        days: Number of days of historical data (default 30)
    
    Returns:
        List of {date: ISO string, price: float} dictionaries
    """
    cache_key = f"spy_{days}"
    
    if _is_cache_valid(cache_key):
        logger.info(f"Using cached SPY data ({days} days)")
        return _benchmark_cache[cache_key]['data']
    
    api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        logger.warning("ALPHA_VANTAGE_API_KEY not set, cannot fetch SPY data")
        return []
    
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=SPY&apikey={api_key}&outputsize=compact"
    
    data = http_get_with_timeout(url, timeout=15, fallback=None)
    
    if not data or 'Time Series (Daily)' not in data:
        if data and 'Note' in data:
            logger.warning(f"Alpha Vantage rate limit: {data.get('Note', '')[:100]}")
        else:
            logger.warning("Failed to fetch SPY historical data from Alpha Vantage")
        return []
    
    time_series = data['Time Series (Daily)']
    cutoff_date = datetime.now() - timedelta(days=days)
    
    result = []
    for date_str, values in sorted(time_series.items()):
        date = datetime.strptime(date_str, '%Y-%m-%d')
        if date >= cutoff_date:
            result.append({
                'date': date_str,
                'price': round(float(values['4. close']), 2)
            })
    
    _benchmark_cache[cache_key] = {
        'data': result,
        'timestamp': datetime.now()
    }
    
    logger.info(f"Fetched {len(result)} SPY price points from Alpha Vantage")
    return result


def normalize_to_percentage(prices: List[Dict], base_date: Optional[str] = None) -> List[Dict]:
    """
    Normalize price series to percentage change from base date.
    
    Args:
        prices: List of {date, price} dictionaries
        base_date: Optional base date (default: first date in series)
    
    Returns:
        List of {date, pct_change} dictionaries
    """
    if not prices:
        return []
    
    sorted_prices = sorted(prices, key=lambda x: x['date'])
    
    base_price = None
    if base_date:
        for p in sorted_prices:
            if p['date'] >= base_date:
                base_price = p['price']
                break
    
    if base_price is None:
        base_price = sorted_prices[0]['price']
    
    if base_price == 0:
        return []
    
    result = []
    for p in sorted_prices:
        pct = ((p['price'] - base_price) / base_price) * 100
        result.append({
            'date': p['date'],
            'pct_change': round(pct, 2)
        })
    
    return result


def get_benchmarks(days: int = 30, base_date: Optional[str] = None) -> Dict:
    """
    Get both BTC and SPY benchmarks normalized to percentage change.
    
    Args:
        days: Number of days of historical data
        base_date: Optional base date for normalization
    
    Returns:
        {
            'btc': [{date, pct_change}],
            'spy': [{date, pct_change}],
            'base_date': str,
            'success': bool
        }
    """
    btc_prices = get_btc_historical(days)
    spy_prices = get_spy_historical(days)
    
    effective_base = base_date
    if not effective_base and btc_prices:
        effective_base = btc_prices[0]['date']
    
    btc_normalized = normalize_to_percentage(btc_prices, effective_base)
    spy_normalized = normalize_to_percentage(spy_prices, effective_base)
    
    return {
        'btc': btc_normalized,
        'spy': spy_normalized,
        'base_date': effective_base,
        'btc_available': len(btc_normalized) > 0,
        'spy_available': len(spy_normalized) > 0,
        'success': len(btc_normalized) > 0 or len(spy_normalized) > 0
    }
