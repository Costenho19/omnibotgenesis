"""
OMNIX Market Data - Sentiment Analysis
Fear & Greed Index, BTC Dominance, and market metrics from free APIs
"""

import requests
from datetime import datetime


def get_fear_greed_index():
    """
    Obtener Fear & Greed Index GRATIS de Alternative.me
    Sin API key, sin límites estrictos, 60 req/min
    
    Returns:
        dict: {value: int, classification: str, success: bool}
    """
    try:
        response = requests.get('https://api.alternative.me/fng/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            value = int(data['data'][0]['value'])
            classification = data['data'][0]['value_classification']
            return {
                'value': value,
                'classification': classification,
                'success': True
            }
    except Exception:
        pass
    return {'success': False}


def get_btc_dominance():
    """
    Obtener dominancia BTC/ETH GRATIS de CoinGecko
    30 calls/min gratis, sin API key necesaria
    
    Returns:
        dict: {btc_dominance: float, eth_dominance: float, total_market_cap: float, success: bool}
    """
    try:
        response = requests.get('https://api.coingecko.com/api/v3/global', timeout=5)
        if response.status_code == 200:
            data = response.json()
            btc_dom = data['data']['market_cap_percentage'].get('btc', 0)
            eth_dom = data['data']['market_cap_percentage'].get('eth', 0)
            total_cap = data['data']['total_market_cap'].get('usd', 0)
            return {
                'btc_dominance': round(btc_dom, 2),
                'eth_dominance': round(eth_dom, 2),
                'total_market_cap': total_cap,
                'success': True
            }
    except Exception:
        pass
    return {'success': False}


def get_free_market_metrics():
    """
    Combinar TODAS las métricas gratuitas disponibles en UN SOLO LLAMADO
    Para que la IA tenga datos reales sin inventar números
    
    Returns:
        dict: Combined metrics from multiple free sources
    """
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'sources': [],
        'available': False
    }
    
    # Fear & Greed (Alternative.me)
    fg = get_fear_greed_index()
    if fg['success']:
        metrics['fear_greed_value'] = fg['value']
        metrics['fear_greed_classification'] = fg['classification']
        metrics['sources'].append('Alternative.me')
        metrics['available'] = True
    
    # Dominancia BTC (CoinGecko)
    dom = get_btc_dominance()
    if dom['success']:
        metrics['btc_dominance'] = dom['btc_dominance']
        metrics['eth_dominance'] = dom['eth_dominance']
        metrics['total_market_cap_usd'] = dom['total_market_cap']
        metrics['sources'].append('CoinGecko')
        metrics['available'] = True
    
    return metrics
