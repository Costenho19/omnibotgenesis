"""
OMNIX Market Data - Kraken Data Provider
Real-time market data from Kraken exchange with intelligent caching
"""

import time
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

# Cache global para datos de Kraken - evitar rate limits
_kraken_data_cache = {
    'data': None,
    'timestamp': 0,
    'ttl': 10  # 10 segundos de cache
}


def fetch_market_snapshot(trading_system):
    """
    Obtener datos reales de Kraken con cache de 10s para evitar rate limits
    Usada por polling (Replit) y webhook (Railway)
    
    Args:
        trading_system: Instancia del trading service con kraken_client
        
    Returns:
        dict: Market data con btc_price, balances, etc.
    """
    global _kraken_data_cache
    
    # Verificar cache
    current_time = time.time()
    if (_kraken_data_cache['data'] is not None and 
        current_time - _kraken_data_cache['timestamp'] < _kraken_data_cache['ttl']):
        logger.info("✅ Usando datos de Kraken desde cache")
        return _kraken_data_cache['data']
    
    real_market_data = {}
    
    try:
        if trading_system and hasattr(trading_system, 'kraken_client'):
            # Obtener precio real BTC/USD con timeout
            try:
                btc_ticker = trading_system.kraken_client.client.fetch_ticker('BTC/USD')
                real_market_data['btc_price'] = btc_ticker['last']
                real_market_data['btc_24h_high'] = btc_ticker['high']
                real_market_data['btc_24h_low'] = btc_ticker['low']
                real_market_data['btc_volume'] = btc_ticker['baseVolume']
                logger.info(f"✅ PRECIO BTC REAL: ${real_market_data['btc_price']:,.2f}")
            except Exception as ticker_error:
                logger.warning(f"⚠️ Error obteniendo ticker BTC: {ticker_error}")
            
            # Obtener balance real con timeout
            try:
                balance = trading_system.kraken_client.client.fetch_balance()
                if balance and isinstance(balance, dict):
                    real_market_data['balance_usd'] = balance.get('USD', {}).get('free', 0)
                    real_market_data['balance_btc'] = balance.get('BTC', {}).get('free', 0)
                    real_market_data['balance_eth'] = balance.get('ETH', {}).get('free', 0)
            except Exception as balance_error:
                logger.warning(f"⚠️ Error obteniendo balance: {balance_error}")
            
    except Exception as data_error:
        logger.error(f"⚠️ Error obteniendo datos Kraken: {data_error}")
    
    # Intentar API pública como fallback si falló la autenticada
    if 'btc_price' not in real_market_data:
        try:
            pub_response = requests.get('https://api.kraken.com/0/public/Ticker?pair=XBTUSD', timeout=3)
            if pub_response.status_code == 200:
                pub_data = pub_response.json()
                if pub_data.get('error') == [] and 'result' in pub_data:
                    real_market_data['btc_price'] = float(pub_data['result']['XXBTZUSD']['c'][0])
                    real_market_data['btc_24h_high'] = float(pub_data['result']['XXBTZUSD']['h'][0])
                    real_market_data['btc_24h_low'] = float(pub_data['result']['XXBTZUSD']['l'][0])
                    logger.info(f"✅ PRECIO BTC REAL (API pública): ${real_market_data['btc_price']:,.2f}")
        except Exception as pub_error:
            logger.error(f"❌ Error API pública Kraken: {pub_error}")
    
    # Actualizar cache
    if real_market_data:
        _kraken_data_cache['data'] = real_market_data
        _kraken_data_cache['timestamp'] = current_time
        logger.info(f"✅ Cache actualizado con {len(real_market_data)} datos de Kraken")
    
    return real_market_data
