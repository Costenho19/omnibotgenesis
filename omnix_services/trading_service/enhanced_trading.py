"""
OMNIX V6.0 ULTRA - Enhanced Trading System
Sistema de Trading Mejorado con Multi-Moneda y Auto-Rotación
"""

import logging
import time
import threading
import os
from datetime import datetime
try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    ccxt = None
    CCXT_AVAILABLE = False
import requests

logger = logging.getLogger(__name__)

TRADING_AVAILABLE = True


class MultiCurrencyTradingEngine:
    """Motor de Trading Multi-Moneda Automático con Rotación Inteligente"""
    
    def __init__(self):
        self.available_pairs = [
            'BTCUSD', 'ETHUSD', 'XRPUSD', 'ADAUSD', 'DOTUSD', 
            'LINKUSD', 'LTCUSD', 'BCHUSD', 'ATOMUSD', 'ALGOUSD'
        ]
        self.current_pair_index = 0
        self.rotation_interval = 300  # 5 minutos
        self.trading_active = False
        self.last_rotation = time.time()
        logger.info(f"🔄 Motor Multi-Moneda inicializado: {len(self.available_pairs)} pares")
    
    def get_current_trading_pair(self):
        """Obtener el par de trading actual con rotación automática"""
        current_time = time.time()
        
        # Rotar cada 5 minutos
        if current_time - self.last_rotation >= self.rotation_interval:
            self.current_pair_index = (self.current_pair_index + 1) % len(self.available_pairs)
            self.last_rotation = current_time
            logger.info(f"🔄 Rotación automática: {self.available_pairs[self.current_pair_index]}")
        
        return self.available_pairs[self.current_pair_index]
    
    def get_technical_analysis_for_pair(self, pair):
        """Análisis técnico específico para cada par"""
        # Calcular trend strength típico
        trend_strength = 0.6  # Neutral-positivo por defecto
        
        # Simular análisis técnico avanzado
        analysis = {
            'pair': pair,
            'rsi': 50.0,  # RSI neutral por defecto
            'macd': 0.0,   # MACD neutral por defecto
            'volume_ratio': 1.2,  # Ratio volumen típico
            'trend_strength': trend_strength,
            'support_level': 0.965,  # Nivel soporte típico
            'resistance_level': 1.05,  # Nivel resistencia típico
            'recommendation': 'HOLD',  # Neutral por defecto
            'timestamp': datetime.now().isoformat()
        }
        
        return analysis


class EnhancedTradingSystem:
    """Sistema de Trading Mejorado con Multi-Moneda y Auto-Rotación"""
    
    def __init__(self):
        self.multi_currency_engine = MultiCurrencyTradingEngine()
        self.auto_trading_active = False
        self.trading_thread = None
        logger.info("🚀 Enhanced Trading System inicializado")
    
    def start_multi_currency_auto_trading(self):
        """Iniciar trading automático multi-moneda"""
        if self.auto_trading_active:
            logger.warning("⚠️ Auto-trading ya está activo")
            return
        
        self.auto_trading_active = True
        
        # Ejecutar en thread separado para no bloquear
        def auto_trading_loop():
            while self.auto_trading_active:
                try:
                    current_pair = self.multi_currency_engine.get_current_trading_pair()
                    analysis = self.multi_currency_engine.get_technical_analysis_for_pair(current_pair)
                    
                    logger.info(f"📊 {current_pair}: {analysis['recommendation']} "
                              f"(RSI: {analysis['rsi']:.1f}, Trend: {analysis['trend_strength']:.2f})")
                    
                    # Aquí se ejecutaría el trading real según el análisis
                    if analysis['recommendation'] == 'BUY' and analysis['rsi'] < 40:
                        logger.info(f"💹 Señal de COMPRA detectada para {current_pair}")
                    elif analysis['recommendation'] == 'SELL' and analysis['rsi'] > 60:
                        logger.info(f"💰 Señal de VENTA detectada para {current_pair}")
                    
                    time.sleep(30)  # Esperar 30 segundos entre análisis
                    
                except Exception as e:
                    logger.error(f"Error en auto-trading: {e}")
                    time.sleep(60)
        
        self.trading_thread = threading.Thread(target=auto_trading_loop, daemon=True)
        self.trading_thread.start()
        logger.info("🚀 AUTO-TRADING MULTI-MONEDA INICIADO")
    
    def stop_multi_currency_auto_trading(self):
        """Detener trading automático"""
        self.auto_trading_active = False
        if self.trading_thread:
            self.trading_thread.join(timeout=5)
        logger.info("🛑 AUTO-TRADING DETENIDO")
    
    def get_real_market_data(self, symbol='BTC/USD'):
        """SISTEMA FALLBACK DE PRECIOS: Kraken → CoinGecko → Binance"""
        # INTENTO 1: KRAKEN (principal)
        try:
            kraken = ccxt.kraken()
            ticker = kraken.fetch_ticker(symbol)
            logger.info(f"✅ Precio obtenido desde Kraken: {symbol}")
            return {
                'precio_actual': ticker['last'],
                'volumen': ticker['quoteVolume'] if ticker.get('quoteVolume') else ticker.get('baseVolume', 'N/A'),
                'cambio_24h': ticker.get('percentage', 0),
                'fuente': 'Kraken',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning(f"⚠️ Kraken falló para {symbol}: {e}")
        
        # INTENTO 2: COINGECKO (fallback 1)
        try:
            coin_id = symbol.split('/')[0].lower()
            
            # Mapeo completo de símbolos a IDs CoinGecko
            coingecko_map = {
                'btc': 'bitcoin',
                'eth': 'ethereum',
                'sol': 'solana',
                'ada': 'cardano',
                'xrp': 'ripple',
                'dot': 'polkadot',
                'doge': 'dogecoin',
                'avax': 'avalanche-2',
                'matic': 'matic-network',
                'link': 'chainlink',
                'ltc': 'litecoin',
                'bch': 'bitcoin-cash',
                'xlm': 'stellar',
                'atom': 'cosmos',
                'uni': 'uniswap',
                'etc': 'ethereum-classic',
                'algo': 'algorand',
                'vet': 'vechain',
                'icp': 'internet-computer',
                'fil': 'filecoin',
                'trx': 'tron',
                'eos': 'eos',
                'aave': 'aave',
                'xtz': 'tezos',
                'mkr': 'maker'
            }
            
            coin_id = coingecko_map.get(coin_id, coin_id)
            
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if coin_id in data:
                price_data = data[coin_id]
                logger.info(f"✅ Precio obtenido desde CoinGecko: {symbol}")
                return {
                    'precio_actual': price_data['usd'],
                    'volumen': price_data.get('usd_24h_vol', 'N/A'),
                    'cambio_24h': price_data.get('usd_24h_change', 0),
                    'fuente': 'CoinGecko',
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            logger.warning(f"⚠️ CoinGecko falló para {symbol}: {e}")
        
        # INTENTO 3: BINANCE (fallback 2)
        try:
            binance = ccxt.binance()
            
            # Convertir símbolo correctamente para Binance
            # BTC/USD → BTC/USDT, ETH/USD → ETH/USDT
            binance_symbol = symbol  # Default value
            parts = symbol.split('/')
            if len(parts) == 2:
                base = parts[0]
                quote = parts[1]
                
                # Binance usa USDT en lugar de USD
                if quote == 'USD':
                    binance_symbol = f"{base}/USDT"
            
            ticker = binance.fetch_ticker(binance_symbol)
            logger.info(f"✅ Precio obtenido desde Binance: {binance_symbol}")
            return {
                'precio_actual': ticker['last'],
                'volumen': ticker['quoteVolume'] if ticker.get('quoteVolume') else ticker.get('baseVolume', 'N/A'),
                'cambio_24h': ticker.get('percentage', 0),
                'fuente': 'Binance',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning(f"⚠️ Binance falló para {binance_symbol}: {e}")
        
        # SI TODO FALLA: Error claro
        logger.error(f"❌ TODAS las fuentes fallaron para {symbol}")
        return None
    
    def get_real_balance(self):
        """Obtener balance real de Kraken con fallback"""
        try:
            if not TRADING_AVAILABLE:
                return {'USD': 0, 'BTC': 0, 'ETH': 0, 'total_usd': 0}
            
            api_key = os.environ.get('KRAKEN_API_KEY', '')
            secret = os.environ.get('KRAKEN_API_SECRET', '')
            
            if not api_key or not secret:
                logger.warning("⚠️ Credenciales Kraken no configuradas")
                return {'USD': 0, 'BTC': 0, 'ETH': 0, 'total_usd': 0}
            
            kraken = ccxt.kraken({
                'apiKey': api_key,
                'secret': secret,
                'enableRateLimit': True
            })
            
            balance = kraken.fetch_balance()
            
            return {
                'USD': balance.get('USD', {}).get('free', 0),
                'BTC': balance.get('BTC', {}).get('free', 0),
                'ETH': balance.get('ETH', {}).get('free', 0),
                'total_usd': balance.get('total', {}).get('USD', 0)
            }
        except Exception as e:
            logger.error(f"Error obteniendo balance: {e}")
            return {'USD': 0, 'BTC': 0, 'ETH': 0, 'total_usd': 0}
    
    def generate_comprehensive_analysis(self, symbol='BTC/USD'):
        """Generar análisis técnico completo"""
        try:
            price_data = self.get_real_market_data(symbol)
            
            if not price_data:
                return "No se pudo obtener datos de mercado"
            
            analisis = f"""
**Precio actual:** ${price_data['precio_actual']:,.2f}
**Cambio 24h:** {price_data['cambio_24h']:.2f}%
**Volumen 24h:** {price_data['volumen']}
**Fuente:** {price_data['fuente']}

**Tendencia:** {'ALCISTA' if price_data['cambio_24h'] > 0 else 'BAJISTA'}
"""
            return analisis
            
        except Exception as e:
            logger.error(f"Error generando análisis: {e}")
            return "Error generando análisis"
