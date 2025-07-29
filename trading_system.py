import logging
import time
import hmac
import hashlib
import base64
import urllib.parse
import requests

# Importamos las claves desde nuestro archivo de configuración central
from config import KRAKEN_API_KEY, KRAKEN_SECRET_KEY

logger = logging.getLogger(__name__)

class KrakenTradingSystem:
    """Sistema de trading integrado con Kraken"""
    
    def __init__(self):
        self.api_key = KRAKEN_API_KEY
        self.secret_key = KRAKEN_SECRET_KEY
        self.base_url = "https://api.kraken.com"
        
    def get_kraken_signature(self, urlpath, data):
        """Generar firma para API de Kraken"""
        postdata = urllib.parse.urlencode(data)
        encoded = (str(data['nonce']) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()
        mac = hmac.new(base64.b64decode(self.secret_key), message, hashlib.sha512)
        sigdigest = base64.b64encode(mac.digest())
        return sigdigest.decode()
        
    def kraken_request(self, uri_path, data=None):
        """Realizar request a API de Kraken"""
        if not self.api_key or not self.secret_key:
            logger.warning("Claves de API de Kraken no configuradas. El módulo de trading está deshabilitado.")
            return {"error": "API keys no configuradas"}
            
        if data is None:
            data = {}
            
        data['nonce'] = str(int(1000*time.time()))
        headers = {
            'API-Key': self.api_key,
            'API-Sign': self.get_kraken_signature(uri_path, data)
        }
        
        try:
            response = requests.post(
                self.base_url + uri_path, 
                headers=headers, 
                data=data,
                timeout=20 # Tiempo de espera razonable
            )
            response.raise_for_status() # Lanza un error si la respuesta es 4xx o 5xx
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en la petición a Kraken: {e}")
            return {"error": str(e)}
            
    def get_account_balance(self):
        """Obtener balance de la cuenta"""
        result = self.kraken_request('/0/private/Balance')
        if result and 'result' in result:
            return result['result']
        logger.error(f"No se pudo obtener el balance de Kraken. Respuesta: {result.get('error', 'desconocido')}")
        return {"error": "No se pudo obtener balance"}
        
    def get_ticker_price(self, pair):
        """Obtener precio actual de un par"""
        try:
            response = requests.get(f"{self.base_url}/0/public/Ticker?pair={pair}", timeout=10)
            response.raise_for_status()
            data = response.json()
            if 'result' in data and pair in data['result']:
                return float(data['result'][pair]['c'][0])
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error obteniendo el precio del ticker de Kraken para {pair}: {e}")
            return None
            
    def place_market_order(self, pair, order_type, volume):
        """Colocar orden de mercado"""
        data = {
            'pair': pair,
            'type': order_type,
            'ordertype': 'market',
            'volume': str(volume),
            'validate': True # Añadimos validación para no ejecutar la orden en pruebas
        }
        logger.info(f"Simulando orden de mercado en Kraken: {order_type} {volume} de {pair}")
        return self.kraken_request('/0/private/AddOrder', data)
# Función externa para ejecutar trading directo
def ejecutar_trade(symbol="BTC/USD", side="buy", amount=0.001):
    try:
        trader = KrakenTradingSystem()
        result = trader.place_market_order(pair=symbol, order_type=side, volume=amount)
        return f"✅ Trade ejecutado: {side.upper()} {amount} {symbol} \n{result}"
    except Exception as e:
        return f"❌ Error al ejecutar trade real: {str(e)}"

        
