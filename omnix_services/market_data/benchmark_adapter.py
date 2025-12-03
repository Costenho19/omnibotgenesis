"""
OMNIX Benchmark Adapter V6.5
Unified adapter for benchmark comparisons (BTC, SPY).
Consumes existing services: kraken_data for crypto, alpha_vantage for stocks.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


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


def get_btc_benchmark(days: int = 30) -> List[Dict]:
    """
    Get BTC benchmark prices from Kraken.
    
    Args:
        days: Number of days of historical data
        
    Returns:
        List of {date, price} dictionaries
    """
    try:
        from omnix_services.market_data.kraken_data import get_ohlc_daily
        return get_ohlc_daily('BTC', days)
    except Exception as e:
        logger.error(f"Error getting BTC benchmark: {e}")
        return []


def get_spy_benchmark(days: int = 30) -> List[Dict]:
    """
    Get SPY benchmark prices from Alpha Vantage.
    
    Args:
        days: Number of days of historical data
        
    Returns:
        List of {date, price} dictionaries
    """
    try:
        from omnix_services.market_intelligence.alpha_vantage_service import alpha_vantage_service
        return alpha_vantage_service.get_daily_prices('SPY', days)
    except Exception as e:
        logger.error(f"Error getting SPY benchmark: {e}")
        return []


def align_to_common_dates(btc_data: List[Dict], spy_data: List[Dict]) -> tuple:
    """
    Align BTC and SPY data to common overlapping dates.
    
    Returns:
        tuple: (btc_aligned, spy_aligned) with matching date ranges
    """
    if not btc_data or not spy_data:
        return btc_data, spy_data
    
    btc_dates = set(d['date'] for d in btc_data)
    spy_dates = set(d['date'] for d in spy_data)
    common_dates = btc_dates.intersection(spy_dates)
    
    if not common_dates:
        return btc_data, spy_data
    
    btc_aligned = [d for d in btc_data if d['date'] in common_dates]
    spy_aligned = [d for d in spy_data if d['date'] in common_dates]
    
    return sorted(btc_aligned, key=lambda x: x['date']), sorted(spy_aligned, key=lambda x: x['date'])


def get_benchmarks(days: int = 30, base_date: Optional[str] = None) -> Dict:
    """
    Get both BTC and SPY benchmarks normalized to percentage change.
    
    Args:
        days: Number of days of historical data (7-90)
        base_date: Optional base date for normalization (aligns with equity curve)
    
    Returns:
        {
            'btc': [{date, pct_change}],
            'spy': [{date, pct_change}],
            'base_date': str,
            'btc_available': bool,
            'spy_available': bool,
            'success': bool
        }
    """
    days = min(max(days, 7), 90)
    
    btc_prices = get_btc_benchmark(days)
    spy_prices = get_spy_benchmark(days)
    
    btc_aligned, spy_aligned = align_to_common_dates(btc_prices, spy_prices)
    
    effective_base = base_date
    if not effective_base:
        if btc_aligned and spy_aligned:
            effective_base = max(btc_aligned[0]['date'], spy_aligned[0]['date'])
        elif btc_aligned:
            effective_base = btc_aligned[0]['date']
        elif spy_aligned:
            effective_base = spy_aligned[0]['date']
    
    btc_normalized = normalize_to_percentage(btc_aligned, effective_base)
    spy_normalized = normalize_to_percentage(spy_aligned, effective_base)
    
    return {
        'btc': btc_normalized,
        'spy': spy_normalized,
        'base_date': effective_base,
        'btc_available': len(btc_normalized) > 0,
        'spy_available': len(spy_normalized) > 0,
        'success': len(btc_normalized) > 0 or len(spy_normalized) > 0,
        'timestamp': datetime.now().isoformat()
    }
