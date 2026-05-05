"""
OMNIX Market Data - Arbitrage Detection
Multi-exchange price comparison and arbitrage opportunity detection
"""

import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


def get_multi_exchange_prices(symbol='BTC/USDT'):
    """
    Obtener precios del mismo par en múltiples exchanges
    
    Args:
        symbol: Trading pair (default: 'BTC/USDT')
        
    Returns:
        dict: Prices from each exchange {exchange_name: price}
    """
    prices = {}
    
    # Kraken (API pública)
    try:
        kraken_symbol = 'XBTUSD' if symbol == 'BTC/USDT' else symbol.replace('/', '')
        response = requests.get(f'https://api.kraken.com/0/public/Ticker?pair={kraken_symbol}', timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data.get('error') == []:
                key = list(data['result'].keys())[0]
                prices['Kraken'] = float(data['result'][key]['c'][0])
    except Exception as e:
        logger.debug(f"Error Kraken price: {e}")
    
    # Binance (API pública)
    try:
        binance_symbol = symbol.replace('/', '')
        response = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={binance_symbol}', timeout=3)
        if response.status_code == 200:
            data = response.json()
            prices['Binance'] = float(data['price'])
    except Exception as e:
        logger.debug(f"Error Binance price: {e}")
    
    # Coinbase (API pública)
    try:
        response = requests.get(f'https://api.coinbase.com/v2/prices/{symbol.replace("/", "-")}/spot', timeout=3)
        if response.status_code == 200:
            data = response.json()
            prices['Coinbase'] = float(data['data']['amount'])
    except Exception as e:
        logger.debug(f"Error Coinbase price: {e}")
    
    return prices


def detect_arbitrage_opportunities(symbol='BTC/USDT', min_profit_pct=0.5):
    """
    Detectar oportunidades de arbitraje entre exchanges
    
    Args:
        symbol: Trading pair
        min_profit_pct: Profit mínimo en % para considerar oportunidad
        
    Returns:
        dict: Arbitrage opportunities with profit calculations
    """
    prices = get_multi_exchange_prices(symbol)
    
    if len(prices) < 2:
        return {
            'opportunities': [],
            'success': False,
            'message': 'No hay suficientes exchanges con datos'
        }
    
    opportunities = []
    exchanges = list(prices.keys())
    
    # Comparar todos los pares de exchanges
    for i, buy_exchange in enumerate(exchanges):
        for sell_exchange in exchanges[i+1:]:
            buy_price = prices[buy_exchange]
            sell_price = prices[sell_exchange]
            
            # Calcular profit (asumiendo fees típicos de 0.1% por lado)
            fee_pct = 0.2  # 0.1% compra + 0.1% venta
            profit_pct = ((sell_price - buy_price) / buy_price * 100) - fee_pct
            
            if abs(profit_pct) >= min_profit_pct:
                if profit_pct > 0:
                    opportunities.append({
                        'buy_exchange': buy_exchange,
                        'sell_exchange': sell_exchange,
                        'buy_price': buy_price,
                        'sell_price': sell_price,
                        'profit_pct': round(profit_pct, 2),
                        'profit_usd_per_1k': round(profit_pct * 10, 2)  # Profit en $1000
                    })
                else:
                    opportunities.append({
                        'buy_exchange': sell_exchange,
                        'sell_exchange': buy_exchange,
                        'buy_price': sell_price,
                        'sell_price': buy_price,
                        'profit_pct': round(abs(profit_pct), 2),
                        'profit_usd_per_1k': round(abs(profit_pct) * 10, 2)
                    })
    
    # Ordenar por profit descendente
    opportunities.sort(key=lambda x: x['profit_pct'], reverse=True)
    
    return {
        'symbol': symbol,
        'opportunities': opportunities,
        'prices': prices,
        'success': True,
        'timestamp': datetime.now().isoformat()
    }
