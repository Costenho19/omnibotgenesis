# coding=utf-8
import requests
import os
import logging
import hmac
import hashlib
import base64
import time
import pandas as pd
import ta
from decimal import Decimal
from abc import ABC, abstractmethod
import json
import sys

# Importaciones para el análisis de sentimiento
# NOTA: Estas librerías son internas del entorno de ejecución.
import google_search
import content_fetcher

# Importación para la integración con Telegram
import telebot

# Importación para la integración con PostgreSQL
import psycopg2
from psycopg2 import sql

# Importaciones para la funcionalidad de Voz (TTS) con gTTS
# Debes instalar estas librerías: pip install gtts playsound
from gtts import gTTS
from playsound import playsound

# Configuración básica del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Clase de abstracción de Exchanges ---
class Exchange(ABC):
    """Clase base abstracta para la interfaz de exchanges de criptomonedas."""
        
    @abstractmethod
    def get_ohlc_data(self, pair, interval):
        """Obtiene datos de velas (OHLC) para un par de activos."""
        pass
        
    @abstractmethod
    def get_account_balance(self, currency):
        """Obtiene el balance de la cuenta para una divisa específica."""
        pass
        
    @abstractmethod
    def place_order(self, pair, type, ordertype, volume, price=None):
        """Coloca una orden de compra o venta en el mercado."""
        pass

# --- Implementación específica para Kraken ---
class KrakenExchange(Exchange):
    """Implementación de la interfaz de Exchange para Kraken."""
        
    def __init__(self, api_key, private_key):
        self.api_key = api_key
        self.private_key = private_key
        self.public_api_url = "https://api.kraken.com/0/public/"
        self.private_api_url = "https://api.kraken.com/0/private/"
        
    def _get_kraken_signature(self, urlpath, data):
        """Genera una firma para la autenticación en la API privada de Kraken."""
        nonce = str(int(1000 * time.time()))
        post_data = nonce + '&'.join(f'{k}={v}' for k, v in data.items())
        sha256_hash = hashlib.sha256(post_data.encode()).digest()
        message = urlpath.encode() + sha256_hash
        private_key = base64.b64decode(self.private_key)
        signature = hmac.new(private_key, message, hashlib.sha512).digest()
        return base64.b64encode(signature).decode()

    def _private_api_request(self, urlpath, data=None):
        """Realiza una solicitud a un endpoint privado de Kraken."""
        if data is None:
            data = {}
        data['nonce'] = int(1000 * time.time())
        headers = {
            'API-Key': self.api_key,
            'API-Sign': self._get_kraken_signature(urlpath, data)
        }
        url = f"{self.private_api_url}{urlpath}"
            
        try:
            response = requests.post(url, headers=headers, data=data, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data['error']:
                error_details = data['error']
                logger.error(f"Error de la API: {error_details}")
                return {"status": "error", "message": "Error de la API de Kraken", "details": error_details}
            return {"status": "success", "data": data['result']}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión con la API de Kraken: {e}")
            return {"status": "error", "message": f"Error de conexión: {e}"}
        except Exception as e:
            logger.error(f"Un error inesperado ocurrió: {e}")
            return {"status": "error", "message": f"Error inesperado: {e}"}

    def get_ohlc_data(self, pair, interval=1):
        """Obtiene datos de velas (OHLC) para un par de activos de Kraken."""
        endpoint = "OHLC"
        url = f"{self.public_api_url}{endpoint}"
        params = {'pair': pair, 'interval': interval}
            
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data['error']:
                return {"status": "error", "message": "Error de la API de Kraken", "details": data['error']}
            return {"status": "success", "data": data['result']}
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": f"Error de conexión: {e}"}
            
    def get_account_balance(self, currency):
        """Obtiene el balance de la cuenta de Kraken."""
        balance_response = self._private_api_request("Balance")
        if balance_response['status'] == 'success':
            balance_val = balance_response['data'].get(currency, '0')
            return {"status": "success", "data": Decimal(balance_val)}
        else:
            return balance_response

    def place_order(self, pair, type, ordertype, volume, price=None):
        """Coloca una orden de compra o venta en Kraken."""
        logger.info(f"Intentando colocar una orden de tipo '{ordertype}' para '{pair}' con volumen {volume}...")
        endpoint = "AddOrder"
        data = {
            'pair': pair,
            'type': type,
            'ordertype': ordertype,
            'volume': str(volume)
        }
        if ordertype in ['limit', 'stop-loss', 'take-profit'] and price is not None:
            data['price'] = str(price)
        return self._private_api_request(endpoint, data)

# --- Implementación específica para Binance ---
class BinanceExchange(Exchange):
    """Implementación de la interfaz de Exchange para Binance."""

    def __init__(self, api_key, private_key):
        self.api_key = api_key
        self.private_key = private_key
        self.base_url = "https://api.binance.com"

    def _get_signature(self, params):
        """Genera una firma para la autenticación en la API de Binance."""
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        signature = hmac.new(
            self.private_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def get_ohlc_data(self, pair, interval):
        """Obtiene datos de velas (OHLC) de Binance."""
        endpoint = "/api/v3/klines"
        url = self.base_url + endpoint
            
        # Binance tiene un formato de intervalo diferente (ej. '5m' en vez de 5)
        binance_interval = f"{interval}m"

        params = {
            'symbol': pair.replace('USD', 'USDT'), # La API de Binance usa 'USDT' en lugar de 'USD'
            'interval': binance_interval,
            'limit': 100
        }
            
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
                
            # Formato de Kraken: [['tiempo', 'apertura', 'alta', 'baja', 'cierre', ...]]
            # Formato de Binance: [['tiempo', 'apertura', 'alta', 'baja', 'cierre', 'volumen', ...]]
            # Adaptamos el formato para que sea compatible con el resto del código
            kraken_format_data = [[str(candle[0]), candle[1], candle[2], candle[3], candle[4]] for candle in data]

            return {"status": "success", "data": {pair: kraken_format_data}}
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": f"Error de conexión: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Error inesperado: {e}"}

    def get_account_balance(self, currency):
        """Obtiene el balance de la cuenta de Binance."""
        endpoint = "/api/v3/account"
        url = self.base_url + endpoint
        params = {'timestamp': int(time.time() * 1000)}
        params['signature'] = self._get_signature(params)

        headers = {'X-MBX-APIKEY': self.api_key}
            
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
                
            balance_data = next((item for item in data['balances'] if item["asset"] == currency), None)
            if balance_data:
                return {"status": "success", "data": Decimal(balance_data['free'])}
            else:
                return {"status": "success", "data": Decimal('0')}
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": f"Error de conexión: {e}"}

    def place_order(self, pair, type, ordertype, volume, price=None):
        """Coloca una orden de compra o venta en Binance."""
        endpoint = "/api/v3/order"
        url = self.base_url + endpoint
            
        # Binance usa 'BUY' y 'SELL', no 'buy' y 'sell'
        type_binance = 'BUY' if type == 'buy' else 'SELL'
            
        params = {
            'symbol': pair.replace('USD', 'USDT'),
            'side': type_binance,
            'type': ordertype.upper(),
            'quantity': str(volume),
            'timestamp': int(time.time() * 1000),
        }
            
        if price is not None:
            params['price'] = str(price)

        params['signature'] = self._get_signature(params)
        headers = {'X-MBX-APIKEY': self.api_key}

        try:
            response = requests.post(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return {"status": "success", "data": data}
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": f"Error de conexión: {e}"}


# --- Clase para enviar notificaciones de Telegram ---
class TelegramNotifier:
    """Clase para enviar mensajes a un chat de Telegram."""
    def __init__(self, token, chat_id):
        self.bot = telebot.TeleBot(token)
        self.chat_id = chat_id
            
    def send_message(self, message):
        """Envía un mensaje de texto al chat configurado."""
        try:
            self.bot.send_message(self.chat_id, message)
            logger.info("✅ Mensaje de Telegram enviado con éxito.")
        except Exception as e:
            logger.error(f"❌ Fallo al enviar el mensaje de Telegram: {e}")
            
# --- Funciones para la conversión y reproducción de audio TTS con gTTS ---
def text_to_speech_gtts(message_text, filename="temp_audio.mp3"):
    """
    Convierte un texto a voz usando gTTS y lo reproduce.
    Args:
        message_text (str): El texto a convertir.
        filename (str): El nombre del archivo de audio temporal.
    """
    try:
        tts = gTTS(text=message_text, lang='es')
        tts.save(filename)
        playsound(filename)
        os.remove(filename)  # Eliminar el archivo temporal
        logger.info(f"✅ Texto convertido a voz y reproducido.")
    except Exception as e:
        logger.error(f"❌ Ocurrió un error en la síntesis o reproducción de voz con gTTS: {e}")
        return False


# --- La clase TradingSystem ahora es independiente del exchange y usa Postgres ---
class TradingSystem:
    """
    La clase central del sistema de trading.
    Gestiona la estrategia y las operaciones a través de una instancia de Exchange y una base de datos Postgres.
    """
    def __init__(self, exchange_client, notifier, db_conn):
        """
        Inicializa el sistema de trading con un cliente de exchange, un notificador y la conexión a Postgres.
            
        Args:
            exchange_client (Exchange): Una instancia de una clase que hereda de Exchange.
            notifier (TelegramNotifier): Una instancia de la clase de notificación.
            db_conn (psycopg2.connection): La conexión a la base de datos de Postgres.
        """
        self.exchange = exchange_client
        self.notifier = notifier
        self.db_conn = db_conn
        # El estado ahora es un diccionario que se carga de Postgres
        self.is_holding = self._load_state()

    def place_order(self, pair, type, ordertype, volume, price=None):
        """
        Coloca una orden usando la instancia del exchange, y actualiza el estado en Postgres.
        """
        if not isinstance(volume, Decimal) or volume <= 0:
            message = f"❌ Error: El volumen de la orden para {pair} no es válido."
            if self.notifier:
                self.notifier.send_message(message)
            text_to_speech_gtts(message)
            return {"status": "error", "message": "El volumen de la orden no es válido."}

        order_response = self.exchange.place_order(pair, type, ordertype, volume, price)
            
        if order_response['status'] == 'success':
            message = f"✅ Orden colocada con éxito para el par {pair}. Tipo: {type}, Volumen: {volume}"
            if self.notifier:
                self.notifier.send_message(message)
            text_to_speech_gtts(message)
            logger.info(message)
            if type == 'buy':
                self.is_holding[pair] = True
            elif type == 'sell':
                self.is_holding[pair] = False
            self._save_state(self.is_holding)
            return order_response
        else:
            message = f"❌ Fallo al colocar la orden para el par {pair}: {order_response['message']}"
            if self.notifier:
                self.notifier.send_message(message)
            text_to_speech_gtts(message)
            logger.error(message)
            return order_response

    def _save_state(self, state):
        """
        Guarda el estado del bot en la base de datos Postgres.
        """
        try:
            with self.db_conn.cursor() as cursor:
                for pair, is_holding in state.items():
                    cursor.execute(
                        sql.SQL("INSERT INTO trading_state (pair, is_holding) VALUES (%s, %s) ON CONFLICT (pair) DO UPDATE SET is_holding = EXCLUDED.is_holding"),
                        (pair, is_holding)
                    )
                self.db_conn.commit()
            logger.info("✅ Estado del bot guardado en Postgres.")
        except psycopg2.Error as e:
            logger.error(f"Error al guardar el estado en Postgres: {e}")
            self.db_conn.rollback() # Revertir la transacción en caso de error

    def _load_state(self):
        """
        Carga el estado del bot desde la base de datos Postgres.
        """
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute("CREATE TABLE IF NOT EXISTS trading_state (pair VARCHAR(255) PRIMARY KEY, is_holding BOOLEAN);")
                self.db_conn.commit()
                cursor.execute("SELECT pair, is_holding FROM trading_state;")
                rows = cursor.fetchall()
                state = {row[0]: row[1] for row in rows}
                logger.info("✅ Estado del bot cargado desde Postgres.")
                return state
        except psycopg2.Error as e:
            logger.error(f"Error al cargar el estado desde Postgres: {e}")
            return {}

def get_market_sentiment(query):
    """
    Usa Google Search y un LLM para analizar el sentimiento de las noticias del mercado.
    """
    try:
        logger.info(f"🔍 Buscando noticias para '{query}'...")
        search_results = google_search.search(queries=[f"{query} news", f"noticias de {query}"])
            
        if not search_results or not search_results[0].results:
            logger.warning("No se encontraron resultados de búsqueda para analizar.")
            return False

        source_refs = [
            content_fetcher.SourceReference(id=result.url, type="web_page")
            for result in search_results[0].results if result.url
        ]

        logger.info("📄 Obteniendo el contenido de las noticias...")
        content = content_fetcher.fetch(query=f"contenidos de noticias sobre {query}", source_references=source_refs)
            
        if not content:
            logger.warning("No se pudo obtener el contenido de las noticias.")
            return False

        logger.info("🧠 Analizando el sentimiento de las noticias con IA...")
        payload = {
            "contents": [
                {"parts": [
                    {"text": f"Analiza el siguiente texto de noticias sobre criptomonedas y determina el sentimiento general. La respuesta debe ser un objeto JSON con la clave 'sentiment' y un valor 'positive', 'negative' o 'neutral'. No añadas más texto.\n\n{content}"}
                ]}
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": {
                    "type": "OBJECT",
                    "properties": {
                        "sentiment": {"type": "STRING", "enum": ["positive", "negative", "neutral"]}
                    }
                }
            }
        }
            
        api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key="
        response = requests.post(
            api_url, 
            headers={'Content-Type': 'application/json'}, 
            data=json.dumps(payload),
            timeout=10
        )
            
        try:
            result_json = response.json()
            sentiment_text = result_json.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text')
                
            if sentiment_text:
                parsed_sentiment = json.loads(sentiment_text)['sentiment']
                logger.info(f"Sentimiento de la IA: {parsed_sentiment.upper()}")
                return parsed_sentiment == "positive"
                
            logger.warning("La respuesta del LLM no contiene un sentimiento válido.")
            return False
            
        except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error al analizar la respuesta de la IA: {e}")
            return False

    except Exception as e:
        logger.error(f"Error en la función de análisis de sentimiento: {e}")
        return False

def calculate_indicators(close_prices):
    """
    Calcula los indicadores técnicos (RSI, EMA y Bollinger Bands) a partir de una lista de precios de cierre.
    """
    if len(close_prices) < 26:
        return None, None, None, None, None
        
    df = pd.DataFrame({'close': close_prices})
        
    # RSI
    rsi = ta.momentum.RSIIndicator(close=df['close'], window=14).rsi().iloc[-1]
        
    # EMAs
    ema_fast = ta.trend.EMAIndicator(close=df['close'], window=12).ema_indicator().iloc[-1]
    ema_slow = ta.trend.EMAIndicator(close=df['close'], window=26).ema_indicator().iloc[-1]

    # Bollinger Bands
    bollinger = ta.volatility.BollingerBands(close=df['close'], window=20, window_dev=2)
    bollinger_upper = bollinger.bollinger_hband().iloc[-1]
    bollinger_lower = bollinger.bollinger_lband().iloc[-1]
        
    return rsi, ema_fast, ema_slow, bollinger_upper, bollinger_lower

def run_manual_trading(trading_system, trading_pairs):
    """
    Ejecuta el bot en modo de trading manual.
    """
    print("\n--- Modo de Trading Manual ---")
    print("Comandos disponibles:")
    print("  buy <PAR> <VOLUMEN> - Coloca una orden de compra a mercado (ej: buy XBTUSD 0.001)")
    print("  sell <PAR> <VOLUMEN> - Coloca una orden de venta a mercado (ej: sell XBTUSD 0.001)")
    print("  balance <DIVISA> - Muestra el balance de una divisa (ej: balance ZUSD)")
    print("  status - Muestra el estado actual del bot (pares en posesión)")
    print("  exit - Sale del modo manual")
    
    while True:
        try:
            command = input("Ingrese un comando > ").strip().split()
            if not command:
                continue

            action = command[0].lower()
            
            if action == 'exit':
                print("Saliendo del modo manual...")
                break
            
            elif action == 'buy' or action == 'sell':
                if len(command) != 3:
                    print("Uso: <buy|sell> <PAR> <VOLUMEN>")
                    continue
                pair, volume = command[1].upper(), Decimal(command[2])
                if pair not in trading_pairs:
                    print(f"Par no válido: {pair}. Los pares disponibles son: {trading_pairs}")
                    continue
                trading_system.place_order(pair, action, 'market', volume)

            elif action == 'balance':
                if len(command) != 2:
                    print("Uso: balance <DIVISA>")
                    continue
                currency = command[1].upper()
                balance_response = trading_system.exchange.get_account_balance(currency)
                if balance_response['status'] == 'success':
                    print(f"Balance de {currency}: {balance_response['data']:.8f}")
                else:
                    print(f"Error al obtener el balance: {balance_response['message']}")

            elif action == 'status':
                print("\n--- Estado Actual del Bot ---")
                for pair, is_holding in trading_system.is_holding.items():
                    print(f"Par: {pair} -> {'EN POSESIÓN' if is_holding else 'NO EN POSESIÓN'}")
                print("---------------------------\n")

            else:
                print("Comando no reconocido. Use 'help' para ver los comandos disponibles.")
        except Exception as e:
            print(f"Ocurrió un error: {e}")
            
def run_automatic_trading(trading_system, trading_pairs):
    """
    Ejecuta el bot en modo de trading automático.
    """
    logger.info("🤖 Modo de trading automático iniciado.")
    ohlc_interval = 5   # Intervalo de 5 minutos
    overbought_threshold = 70
    oversold_threshold = 30
    profit_percentage = Decimal('0.05')
    stop_loss_percentage = Decimal('0.02')
    
    # Mapeo de pares a la moneda base utilizada en los balances de Kraken
    currency_map = {
        'XBTUSD': 'XXBT',
        'ETHUSD': 'XETH',
        'SOLUSD': 'SOL',
        'ADAUSD': 'ADA',
        'DOTUSD': 'DOT'
    }
        
    try:
        while True:
            # 1. Obtener el sentimiento general del mercado una sola vez por ciclo
            market_sentiment_is_positive = get_market_sentiment(query="Bitcoin")
                
            # 2. Recorrer cada par de trading en la lista
            for pair in trading_pairs:
                logger.info(f"--- Procesando el par: {pair} ---")
                    
                # Recargar el estado de la base de datos para cada ciclo
                trading_system.is_holding = trading_system._load_state()

                if pair not in trading_system.is_holding:
                    trading_system.is_holding[pair] = False

                # Obtener los datos de precio más recientes
                ohlc_response = trading_system.exchange.get_ohlc_data(pair=pair, interval=ohlc_interval)
                    
                if ohlc_response['status'] == 'success':
                    ohlc_data = list(ohlc_response['data'].values())[0]
                    close_prices = [float(candle[4]) for candle in ohlc_data]
                        
                    if len(close_prices) < 26:
                        logger.warning(f"Datos OHLC insuficientes para {pair}. Esperando...")
                        continue

                    last_price = Decimal(str(close_prices[-1]))

                    # Calcular los indicadores técnicos
                    current_rsi, ema_fast, ema_slow, bollinger_upper, bollinger_lower = calculate_indicators(close_prices)
                        
                    if current_rsi is not None:
                        logger.info(f"Estado de {pair}: {'HOLDING' if trading_system.is_holding[pair] else 'NO HOLDING'} | Último precio: {last_price:.2f} | RSI: {current_rsi:.2f}")

                        # Lógica de la estrategia (compra/venta)
                            
                        # Condición para comprar: RSI, EMA, IA y Bollinger Bands
                        if current_rsi < oversold_threshold and ema_fast > ema_slow and not trading_system.is_holding[pair] and market_sentiment_is_positive and last_price > bollinger_lower:
                            logger.info(f"¡Señal de COMPRA para {pair}! El mercado está en sobreventa, la tendencia es alcista, las noticias son positivas y el precio está recuperándose de la banda inferior.")
                                
                            balance_response = trading_system.exchange.get_account_balance(currency='ZUSD')
                            if balance_response['status'] == 'success' and balance_response['data'] > 0:
                                volume_to_buy = (balance_response['data'] * Decimal('0.5')) / last_price
                                volume_to_buy = volume_to_buy.quantize(Decimal('0.00000001'))
                                    
                                buy_order_response = trading_system.place_order(
                                    pair=pair,
                                    type='buy',
                                    ordertype='market',
                                    volume=volume_to_buy
                                )

                                if buy_order_response['status'] == 'success':
                                    logger.info(f"✅ Compra exitosa en {pair}. Colocando órdenes de gestión de riesgo.")
                                    take_profit_price = last_price * (Decimal('1') + profit_percentage)
                                    stop_loss_price = last_price * (Decimal('1') - stop_loss_percentage)

                                    trading_system.place_order(
                                        pair=pair,
                                        type='sell',
                                        ordertype='take-profit',
                                        volume=volume_to_buy,
                                        price=take_profit_price
                                    )

                                    trading_system.place_order(
                                        pair=pair,
                                        type='sell',
                                        ordertype='stop-loss',
                                        volume=volume_to_buy,
                                        price=stop_loss_price
                                    )
                            else:
                                logger.warning(f"No hay suficiente balance para comprar {pair} o no se pudo obtener el balance.")
                                text_to_speech_gtts(f"Atención. No hay suficiente balance para comprar {pair}.")
                                    
                        # Condición para vender: RSI, EMA y Bollinger Bands
                        elif current_rsi > overbought_threshold and ema_fast < ema_slow and trading_system.is_holding[pair] and last_price < bollinger_upper:
                            logger.info(f"¡Señal de VENTA para {pair}! El mercado está en sobrecompra, la tendencia es bajista y el precio está rebotando desde la banda superior.")
                            
                            # Obtener el balance del activo a vender
                            currency_to_sell = currency_map.get(pair)
                            balance_response = trading_system.exchange.get_account_balance(currency_to_sell)
                            if balance_response['status'] == 'success' and balance_response['data'] > 0:
                                volume_to_sell = balance_response['data']
                                sell_order_response = trading_system.place_order(
                                    pair=pair,
                                    type='sell',
                                    ordertype='market',
                                    volume=volume_to_sell
                                )
                                if sell_order_response['status'] == 'success':
                                    text_to_speech_gtts(f"Venta exitosa para el par {pair}. El volumen de la venta es {volume_to_sell}")
                            else:
                                logger.warning(f"No hay suficiente balance de {currency_to_sell} para vender.")
                                text_to_speech_gtts(f"Atención. No hay suficiente balance de {currency_to_sell} para vender.")

            logger.info("Esperando 5 minutos antes de la siguiente iteración...")
            time.sleep(300) # Espera 5 minutos

    except Exception as e:
        logger.error(f"Ocurrió un error grave en el modo automático: {e}")
        text_to_speech_gtts(f"Error crítico en el modo automático. El bot se ha detenido.")
    finally:
        if trading_system.db_conn:
            trading_system.db_conn.close()
            logger.info("Conexión a la base de datos de Postgres cerrada.")

def main():
    """
    Función principal para la inicialización y selección de modo.
    """
    # Obtener las claves de API desde las variables de entorno de Railway
    kraken_api_key = os.environ.get('KRAKEN_API_KEY')
    kraken_private_key = os.environ.get('KRAKEN_SECRET_KEY') 
        
    if not kraken_api_key or not kraken_private_key:
        logger.error("No se encontraron las claves de API de Kraken en las variables de entorno.")
        logger.error("Asegúrate de configurar KRAKEN_API_KEY y KRAKEN_SECRET_KEY.")
        text_to_speech_gtts("Error. No se encontraron las claves de la API en el entorno. Por favor, revisa la configuración.")
        return

    # Configuración de Telegram
    telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    notifier = None
    if telegram_token and telegram_chat_id:
        try:
            notifier = TelegramNotifier(token=telegram_token, chat_id=telegram_chat_id)
            initial_message = "El bot de trading ha sido iniciado. Operando en múltiples pares."
            if notifier:
                notifier.send_message(initial_message)
            text_to_speech_gtts(initial_message)
        except Exception as e:
            logger.error(f"❌ Fallo al inicializar el notificador de Telegram: {e}")
            notifier = None

    # Inicializar la conexión a Postgres usando las variables de entorno de Railway
    db_conn = None
    try:
        db_conn = psycopg2.connect(
            host=os.environ.get('PGHOST'),
            database=os.environ.get('PGDATABASE'),
            user=os.environ.get('PGUSER'),
            password=os.environ.get('PGPASSWORD'),
            port=os.environ.get('PGPORT')
        )
        logger.info("✅ Conexión a Postgres establecida con éxito.")
    except Exception as e:
        logger.error(f"❌ Fallo al conectar a Postgres: {e}")
        text_to_speech_gtts(f"Error crítico, no se pudo conectar a la base de datos de Postgres. El bot se detendrá.")
        return

    kraken_client = KrakenExchange(api_key=kraken_api_key, private_key=kraken_private_key)
    trading_system = TradingSystem(exchange_client=kraken_client, notifier=notifier, db_conn=db_conn)
    
    trading_pairs = ['XBTUSD', 'ETHUSD', 'SOLUSD', 'ADAUSD', 'DOTUSD']

    print("Seleccione el modo de operación:")
    print("1. Modo Automático (Ejecuta la estrategia de forma continua)")
    print("2. Modo Manual (Permite colocar órdenes y consultar balances manualmente)")
    choice = input("Ingrese su elección (1 o 2): ")
    
    if choice == '1':
        run_automatic_trading(trading_system, trading_pairs)
    elif choice == '2':
        run_manual_trading(trading_system, trading_pairs)
    else:
        print("Opción no válida. Saliendo del programa.")
        if db_conn:
            db_conn.close()

if __name__ == "__main__":
    main()
