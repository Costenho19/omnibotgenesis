"""
OMNIX Market Data - Kraken Data Provider V6.1
Real-time market data from Kraken exchange with multi-crypto support

Updated: Dec 22, 2025 - Added price freshness validation for institutional trading
"""

import time
import logging
import requests
from datetime import datetime
from typing import Optional, Dict, Any

from omnix_services.market_data.validators import (
    validate_price_freshness,
    PriceDataState,
    PriceFreshness
)

logger = logging.getLogger(__name__)

# Cache global para datos de Kraken - evitar rate limits
_kraken_data_cache = {
    'data': None,
    'timestamp': 0,
    'ttl': 10  # 10 segundos de cache
}

# Cache específico por símbolo
_symbol_cache = {}
_symbol_cache_ttl = 15  # 15 segundos

# ============================================================================
# MAPEO COMPLETO DE CRIPTOMONEDAS - Kraken soporta 100+ pares
# ============================================================================
CRYPTO_MAPPING = {
    # Nombre común → (Símbolo, Par Kraken API)
    'bitcoin': ('BTC', 'XXBTZUSD'),
    'btc': ('BTC', 'XXBTZUSD'),
    'ethereum': ('ETH', 'XETHZUSD'),
    'eth': ('ETH', 'XETHZUSD'),
    'ether': ('ETH', 'XETHZUSD'),
    'cardano': ('ADA', 'ADAUSD'),
    'ada': ('ADA', 'ADAUSD'),
    'solana': ('SOL', 'SOLUSD'),
    'sol': ('SOL', 'SOLUSD'),
    'ripple': ('XRP', 'XXRPZUSD'),
    'xrp': ('XRP', 'XXRPZUSD'),
    'polkadot': ('DOT', 'DOTUSD'),
    'dot': ('DOT', 'DOTUSD'),
    'dogecoin': ('DOGE', 'XDGUSD'),
    'doge': ('DOGE', 'XDGUSD'),
    'avalanche': ('AVAX', 'AVAXUSD'),
    'avax': ('AVAX', 'AVAXUSD'),
    'chainlink': ('LINK', 'LINKUSD'),
    'link': ('LINK', 'LINKUSD'),
    'polygon': ('POL', 'POLUSD'),
    'pol': ('POL', 'POLUSD'),
    'matic': ('POL', 'POLUSD'),
    'litecoin': ('LTC', 'XLTCZUSD'),
    'ltc': ('LTC', 'XLTCZUSD'),
    'uniswap': ('UNI', 'UNIUSD'),
    'uni': ('UNI', 'UNIUSD'),
    'stellar': ('XLM', 'XXLMZUSD'),
    'xlm': ('XLM', 'XXLMZUSD'),
    'cosmos': ('ATOM', 'ATOMUSD'),
    'atom': ('ATOM', 'ATOMUSD'),
    'tron': ('TRX', 'TRXUSD'),
    'trx': ('TRX', 'TRXUSD'),
    'shiba': ('SHIB', 'SHIBUSD'),
    'shib': ('SHIB', 'SHIBUSD'),
    'shiba inu': ('SHIB', 'SHIBUSD'),
    'near': ('NEAR', 'NEARUSD'),
    'near protocol': ('NEAR', 'NEARUSD'),
    'algorand': ('ALGO', 'ALGOUSD'),
    'algo': ('ALGO', 'ALGOUSD'),
    'aave': ('AAVE', 'AAVEUSD'),
    'filecoin': ('FIL', 'FILUSD'),
    'fil': ('FIL', 'FILUSD'),
    'eos': ('EOS', 'EOSUSD'),
    'tezos': ('XTZ', 'XTZUSD'),
    'xtz': ('XTZ', 'XTZUSD'),
    'monero': ('XMR', 'XXMRZUSD'),
    'xmr': ('XMR', 'XXMRZUSD'),
    'maker': ('MKR', 'MKRUSD'),
    'mkr': ('MKR', 'MKRUSD'),
    'compound': ('COMP', 'COMPUSD'),
    'comp': ('COMP', 'COMPUSD'),
    'fantom': ('FTM', 'FTMUSD'),
    'ftm': ('FTM', 'FTMUSD'),
    'hedera': ('HBAR', 'HBARUSD'),
    'hbar': ('HBAR', 'HBARUSD'),
    'aptos': ('APT', 'APTUSD'),
    'apt': ('APT', 'APTUSD'),
    'arbitrum': ('ARB', 'ARBUSD'),
    'arb': ('ARB', 'ARBUSD'),
    'optimism': ('OP', 'OPUSD'),
    'op': ('OP', 'OPUSD'),
    'injective': ('INJ', 'INJUSD'),
    'inj': ('INJ', 'INJUSD'),
    'render': ('RNDR', 'RNDRUSD'),
    'rndr': ('RNDR', 'RNDRUSD'),
    'pepe': ('PEPE', 'PEPEUSD'),
    'bonk': ('BONK', 'BONKUSD'),
    'sui': ('SUI', 'SUIUSD'),
    'sei': ('SEI', 'SEIUSD'),
    'celestia': ('TIA', 'TIAUSD'),
    'tia': ('TIA', 'TIAUSD'),
    'jupiter': ('JUP', 'JUPUSD'),
    'jup': ('JUP', 'JUPUSD'),
}

# Lista de símbolos soportados para referencia rápida
SUPPORTED_SYMBOLS = list(set(v[0] for v in CRYPTO_MAPPING.values()))


def normalize_crypto_name(name: str) -> tuple:
    """
    Normalizar nombre de cripto a (símbolo, par_kraken)
    
    Args:
        name: Nombre común, símbolo o variante (ej: "cardano", "ADA", "Cardano")
        
    Returns:
        tuple: (símbolo, par_kraken) o (None, None) si no se encuentra
    """
    if not name:
        return (None, None)
    
    normalized = name.lower().strip()
    
    if normalized in CRYPTO_MAPPING:
        return CRYPTO_MAPPING[normalized]
    
    # Intentar como símbolo directo (ej: "BTC" pasado como "btc")
    for key, value in CRYPTO_MAPPING.items():
        if value[0].lower() == normalized:
            return value
    
    return (None, None)


def get_supported_cryptos() -> list:
    """Retornar lista de criptos soportadas para el prompt de la IA"""
    cryptos = {}
    for name, (symbol, _) in CRYPTO_MAPPING.items():
        if symbol not in cryptos:
            cryptos[symbol] = []
        if name != symbol.lower():
            cryptos[symbol].append(name.title())
    
    return [f"{sym} ({', '.join(names[:2])})" if names else sym 
            for sym, names in sorted(cryptos.items())]


def fetch_crypto_price(crypto_name: str) -> dict:
    """
    Obtener precio de CUALQUIER criptomoneda de Kraken
    
    Args:
        crypto_name: Nombre común o símbolo (ej: "cardano", "ADA", "Bitcoin")
        
    Returns:
        dict: {symbol, price, high_24h, low_24h, volume, change_24h, source, success}
    """
    global _symbol_cache
    
    symbol, kraken_pair = normalize_crypto_name(crypto_name)
    
    if not symbol:
        logger.warning(f"⚠️ Cripto no reconocida: {crypto_name}")
        return {
            'success': False,
            'error': f"No reconozco '{crypto_name}'. Criptos soportadas: BTC, ETH, ADA, SOL, XRP, DOT, DOGE, AVAX, LINK, MATIC, LTC, y 40+ más.",
            'symbol': None
        }
    
    # Check cache with freshness validation
    cache_key = symbol
    current_time = time.time()
    if cache_key in _symbol_cache:
        cached = _symbol_cache[cache_key]
        cache_age = current_time - cached['timestamp']
        
        if cache_age < _symbol_cache_ttl:
            cached_data = cached['data'].copy()
            
            if 'price' in cached_data and 'fetch_timestamp' in cached_data:
                price_state = validate_price_freshness(
                    symbol=symbol,
                    price=cached_data['price'],
                    fetch_timestamp=cached_data['fetch_timestamp'],
                    source=cached_data.get('source', 'cache')
                )
                cached_data['freshness'] = price_state.freshness.value
                cached_data['is_tradeable'] = price_state.is_tradeable
                cached_data['age_seconds'] = price_state.age_seconds
            
            logger.info(f"✅ {symbol} desde cache (age: {cache_age:.1f}s)")
            return cached_data
    
    result = {
        'symbol': symbol,
        'name': crypto_name.title(),
        'success': False,
        'source': 'unknown'
    }
    
    # Intento 1: API pública de Kraken
    try:
        url = f'https://api.kraken.com/0/public/Ticker?pair={kraken_pair}'
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, dict) and not data.get('error'):
                if 'result' in data and data['result']:
                    ticker_key = list(data['result'].keys())[0]
                    ticker = data['result'][ticker_key]
                    
                    price = float(ticker['c'][0])  # Current price
                    open_price = float(ticker['o'])  # Open price (24h)
                    
                    fetch_time = time.time()
                    
                    price_state = validate_price_freshness(
                        symbol=symbol,
                        price=price,
                        fetch_timestamp=fetch_time,
                        source="Kraken"
                    )
                    
                    result.update({
                        'price': price,
                        'high_24h': float(ticker['h'][1]),  # 24h high
                        'low_24h': float(ticker['l'][1]),   # 24h low
                        'volume': float(ticker['v'][1]),    # 24h volume
                        'change_24h': round(((price - open_price) / open_price) * 100, 2) if open_price > 0 else 0,
                        'source': 'Kraken',
                        'success': True,
                        'fetch_timestamp': fetch_time,
                        'freshness': price_state.freshness.value,
                        'is_tradeable': price_state.is_tradeable,
                        'age_seconds': price_state.age_seconds
                    })
                    
                    logger.info(f"✅ {symbol} precio Kraken: ${price:,.4f} (fresh: {price_state.freshness.value})")
                    
                    # Update cache with timestamp
                    _symbol_cache[cache_key] = {
                        'data': result,
                        'timestamp': fetch_time
                    }
                    
                    return result
            
            # Kraken devolvió error
            error_msg = data.get('error', ['Unknown error'])
            logger.warning(f"⚠️ Kraken error para {symbol}: {error_msg}")
            
    except Exception as e:
        logger.warning(f"⚠️ Error Kraken para {symbol}: {e}")
    
    # Intento 2: CoinGecko como fallback
    try:
        coingecko_ids = {
            'BTC': 'bitcoin', 'ETH': 'ethereum', 'ADA': 'cardano', 
            'SOL': 'solana', 'XRP': 'ripple', 'DOT': 'polkadot',
            'DOGE': 'dogecoin', 'AVAX': 'avalanche-2', 'LINK': 'chainlink',
            'MATIC': 'matic-network', 'LTC': 'litecoin', 'UNI': 'uniswap',
            'XLM': 'stellar', 'ATOM': 'cosmos', 'TRX': 'tron',
            'SHIB': 'shiba-inu', 'NEAR': 'near', 'ALGO': 'algorand',
            'AAVE': 'aave', 'FIL': 'filecoin', 'EOS': 'eos',
            'XTZ': 'tezos', 'XMR': 'monero', 'MKR': 'maker',
            'COMP': 'compound-governance-token', 'FTM': 'fantom',
            'HBAR': 'hedera-hashgraph', 'APT': 'aptos', 'ARB': 'arbitrum',
            'OP': 'optimism', 'INJ': 'injective-protocol', 'RNDR': 'render-token',
            'PEPE': 'pepe', 'BONK': 'bonk', 'SUI': 'sui', 'SEI': 'sei-network',
            'TIA': 'celestia', 'JUP': 'jupiter-exchange-solana'
        }
        
        cg_id = coingecko_ids.get(symbol)
        if cg_id:
            url = f'https://api.coingecko.com/api/v3/simple/price?ids={cg_id}&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true'
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if cg_id in data:
                    cg_data = data[cg_id]
                    result.update({
                        'price': cg_data.get('usd', 0),
                        'change_24h': round(cg_data.get('usd_24h_change', 0), 2),
                        'volume': cg_data.get('usd_24h_vol', 0),
                        'source': 'CoinGecko',
                        'success': True
                    })
                    
                    logger.info(f"✅ {symbol} precio CoinGecko: ${result['price']:,.4f}")
                    
                    # Update cache
                    _symbol_cache[cache_key] = {
                        'data': result,
                        'timestamp': current_time
                    }
                    
                    return result
                    
    except Exception as e:
        logger.warning(f"⚠️ Error CoinGecko para {symbol}: {e}")
    
    result['error'] = f"No se pudo obtener precio de {symbol} en este momento"
    return result


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
        btc_data = fetch_crypto_price('BTC')
        if btc_data.get('success'):
            real_market_data['btc_price'] = btc_data['price']
            real_market_data['btc_24h_high'] = btc_data.get('high_24h', 0)
            real_market_data['btc_24h_low'] = btc_data.get('low_24h', 0)
    
    # Actualizar cache
    if real_market_data:
        _kraken_data_cache['data'] = real_market_data
        _kraken_data_cache['timestamp'] = current_time
        logger.info(f"✅ Cache actualizado con {len(real_market_data)} datos de Kraken")
    
    return real_market_data


# ============================================================================
# OHLC DIARIO PARA BENCHMARKS
# ============================================================================

_ohlc_daily_cache = {}
_ohlc_daily_cache_ttl = 3600  # 1 hora


def get_ohlc_daily(symbol: str = 'BTC', days: int = 30) -> list:
    """
    Obtener OHLC diario de Kraken para benchmarks.
    Usa intervalo de 1440 minutos (1 día).
    
    Args:
        symbol: Símbolo cripto (BTC, ETH, SOL, etc.)
        days: Número de días de histórico (default 30, max 720)
        
    Returns:
        Lista de {date: str, price: float} ordenada por fecha ascendente
    """
    import time as time_module
    
    cache_key = f"ohlc_daily_{symbol}_{days}"
    current_time = time_module.time()
    
    if cache_key in _ohlc_daily_cache:
        cached = _ohlc_daily_cache[cache_key]
        if current_time - cached['timestamp'] < _ohlc_daily_cache_ttl:
            logger.info(f"✅ Usando OHLC diario {symbol} desde cache ({len(cached['data'])} puntos)")
            return cached['data']
    
    normalized = normalize_crypto_name(symbol.lower())
    if normalized[0] is None:
        logger.warning(f"Símbolo no reconocido: {symbol}")
        return []
    
    kraken_pair = normalized[1]
    
    since = int((current_time - (days * 86400)))
    
    url = f"https://api.kraken.com/0/public/OHLC?pair={kraken_pair}&interval=1440&since={since}"
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get('error') and len(data['error']) > 0:
            logger.warning(f"Error Kraken OHLC: {data['error']}")
            if cache_key in _ohlc_daily_cache:
                return _ohlc_daily_cache[cache_key]['data']
            return []
        
        result_keys = [k for k in data.get('result', {}).keys() if k != 'last']
        if not result_keys:
            logger.warning(f"Sin datos OHLC para {symbol}")
            return []
        
        ohlc_data = data['result'][result_keys[0]]
        
        result = []
        for candle in ohlc_data:
            timestamp = int(candle[0])
            close_price = float(candle[4])
            date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
            result.append({
                'date': date_str,
                'price': round(close_price, 2)
            })
        
        _ohlc_daily_cache[cache_key] = {
            'data': result,
            'timestamp': current_time
        }
        
        logger.info(f"✅ Obtenidos {len(result)} días de OHLC para {symbol}")
        return result
        
    except Exception as e:
        logger.error(f"Error obteniendo OHLC diario {symbol}: {e}")
        if cache_key in _ohlc_daily_cache:
            return _ohlc_daily_cache[cache_key]['data']
        return []
