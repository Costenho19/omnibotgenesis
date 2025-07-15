#!/usr/bin/env python3

import os
import time
import logging
import asyncio
import threading
from typing import Dict, Optional
import hashlib
import hmac
import base64
import requests
from urllib.parse import urlencode
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask, jsonify
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
KRAKEN_API_KEY = os.getenv('KRAKEN_API_KEY')
KRAKEN_SECRET = os.getenv('KRAKEN_SECRET')
PORT = int(os.getenv('PORT', 10000))

class KrakenModule:
    def __init__(self):
        self.api_key = KRAKEN_API_KEY
        self.secret = KRAKEN_SECRET
        self.base_url = "https://api.kraken.com"
        logger.info("Kraken inicializado")

def _generate_nonce(self) -> str:
    return str(int(time.time() * 1000))

def _get_kraken_signature(self, urlpath: str, data: Dict) -> str:
    postdata = urlencode(data)
    encoded = (str(data['nonce']) + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()
    signature = hmac.new(base64.b64decode(self.secret), message, hashlib.sha512)
    return base64.b64encode(signature.digest()).decode()

def _make_request(self, endpoint: str, data: Dict = None) -> Dict:
        try:
            url = f"{self.base_url}/{endpoint}"
            if not data:
                data = {}
            data['nonce'] = self._generate_nonce()
            headers = {
                'API-Key': self.api_key,
                'API-Sign': self._get_kraken_signature(f"/{endpoint}", data)
            }
            response = requests.post(url, headers=headers, data=data, timeout=30)
            result = response.json()
                if result.get('error'):
             logger.error(f"Error Kraken: {result['error']}")
                return {'success': False, 'error': result['error']}
            return {'success': True, 'result': result.get('result', {})}
        except Exception as e:
            logger.error(f"Error conexion: {e}")
            return {'success': False, 'error': str(e)}

def get_balance(self) -> Dict:
response = self._make_request('0/private/Balance')
return response['result'] if response['success'] else {}

def get_ticker_price(self, pair: str) -> Optional[float]:
try:
response = requests.get(f"{self.base_url}/0/public/Ticker?pair={pair}", timeout=30)
result = response.json()
if result.get('result'):
pair_data = list(result['result'].values())[0]
return float(pair_data['c'][0])
return None
except Exception as e:
logger.error(f"Error precio {pair}: {e}")
return None

def place_order(self, pair: str, side: str, volume: float) -> Dict:
data = {
'pair': pair,
'type': side,
'ordertype': 'market',
'volume': str(volume)
}
response = self._make_request('0/private/AddOrder', data)
if response['success']:
result = response['result']
txid = result.get('txid', [''])[0]
logger.info(f"Orden ejecutada: {txid}")
return {'success': True, 'txid': txid}
else:
return {'success': False, 'error': response['error']}

class TelegramBot:
def __init__(self, kraken_module):
self.token = TELEGRAM_TOKEN
self.kraken = kraken_module
self.bot = Bot(self.token)
logger.info("Telegram Bot inicializado")

def detect_language(self, message: str) -> str:
message_lower = message.lower()
spanish_words = ['hola', 'compra', 'vende', 'precio', 'balance']
english_words = ['hello', 'buy', 'sell', 'price', 'balance']
arabic_words = ['مرحبا', 'شراء', 'بيع', 'سعر', 'رصيد']
chinese_words = ['你好', '购买', '出售', '价格', '余额']
spanish_count = sum(1 for word in spanish_words if word in message_lower)
english_count = sum(1 for word in english_words if word in message_lower)
arabic_count = sum(1 for word in arabic_words if word in message_lower)
chinese_count = sum(1 for word in chinese_words if word in message_lower)
counts = {'es': spanish_count, 'en': english_count, 'ar': arabic_count, 'zh': chinese_count}
return max(counts, key=counts.get)

async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
username = update.effective_user.username or "Usuario"
welcome = f"Hola {username}! OMNIX Global Bot - Trading Cuadrilingue\n\nComandos:\n/balance - Ver balance\n/prices - Precios crypto\n\nEjemplos:\ncompra 20 dolares bitcoin\nvende ethereum\nprecio solana"
await update.message.reply_text(welcome)

async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
balance = self.kraken.get_balance()
if balance:
usd_balance = float(balance.get('ZUSD', 0))
sol_balance = float(balance.get('SOL', 0))
message = f"Balance:\nUSD: ${usd_balance:.2f}\nSOL: {sol_balance:.6f}"
else:
message = "Error obteniendo balance"
await update.message.reply_text(message)

async def prices_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
sol_price = self.kraken.get_ticker_price('SOLUSD')
btc_price = self.kraken.get_ticker_price('XBTUSD')
message = f"Precios:\nSOL: ${sol_price:.2f}\nBTC: ${btc_price:.2f}" if sol_price and btc_price else "Error obteniendo precios"
await update.message.reply_text(message)

async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
message = update.message.text.lower()
lang = self.detect_language(message)
if any(word in message for word in ['compra', 'buy', 'شراء', '购买']):
await self.handle_buy(update, lang)
elif any(word in message for word in ['vende', 'sell', 'بيع', '出售']):
await self.handle_sell(update, lang)
else:
responses = {
'es': "Hola! Soy OMNIX, tu asistente de trading crypto. Puedo ayudarte con precios, balances y operaciones.",
'en': "Hello! I'm OMNIX, your crypto trading assistant. I can help with prices, balances and operations.",
'ar': "مرحبا! أنا OMNIX، مساعد تداول العملات المشفرة.",
'zh': "你好！我是OMNIX，你的加密货币交易助手。"
}
await update.message.reply_text(responses.get(lang, responses['es']))

async def handle_buy(self, update: Update, lang: str):
try:
sol_price = self.kraken.get_ticker_price('SOLUSD')
if sol_price:
volume = 20 / sol_price
if volume >= 0.1:
result = self.kraken.place_order('SOLUSD', 'buy', volume)
if result['success']:
messages = {
'es': f"Compra ejecutada: {result['txid']}\n{volume:.6f} SOL @ ${sol_price:.2f}",
'en': f"Buy executed: {result['txid']}\n{volume:.6f} SOL @ ${sol_price:.2f}",
'ar': f"تم التنفيذ: {result['txid']}\n{volume:.6f} SOL @ ${sol_price:.2f}",
'zh': f"购买已执行: {result['txid']}\n{volume:.6f} SOL @ ${sol_price:.2f}"
}
await update.message.reply_text(messages.get(lang, messages['es']))
else:
await update.message.reply_text(f"Error: {result.get('error', 'Unknown error')}")
else:
await update.message.reply_text(f"Volumen muy pequeño: {volume:.6f}")
else:
await update.message.reply_text("No se pudo obtener precio de SOL")
except Exception as e:
await update.message.reply_text(f"Error: {str(e)}")

async def handle_sell(self, update: Update, lang: str):
try:
balance = self.kraken.get_balance()
sol_balance = float(balance.get('SOL', 0))
if sol_balance >= 0.1:
result = self.kraken.place_order('SOLUSD', 'sell', sol_balance)
if result['success']:
sol_price = self.kraken.get_ticker_price('SOLUSD')
usd_value = sol_balance * sol_price if sol_price else 0
messages = {
'es': f"Venta ejecutada: {result['txid']}\n{sol_balance:.6f} SOL -> ${usd_value:.2f}",
'en': f"Sale executed: {result['txid']}\n{sol_balance:.6f} SOL -> ${usd_value:.2f}",
'ar': f"تم البيع: {result['txid']}\n{sol_balance:.6f} SOL -> ${usd_value:.2f}",
'zh': f"出售已执行: {result['txid']}\n{sol_balance:.6f} SOL -> ${usd_value:.2f}"
}
await update.message.reply_text(messages.get(lang, messages['es']))
else:
await update.message.reply_text(f"Error: {result.get('error', 'Unknown error')}")
else:
messages = {
'es': f"Balance SOL insuficiente: {sol_balance:.6f}",
'en': f"Insufficient SOL balance: {sol_balance:.6f}",
'ar': f"رصيد SOL غير كافي: {sol_balance:.6f}",
'zh': f"SOL余额不足: {sol_balance:.6f}"
}
await update.message.reply_text(messages.get(lang, messages['es']))
except Exception as e:
await update.message.reply_text(f"Error: {str(e)}")

async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
await self.handle_buy(update, 'es')

def start_polling(self):
try:
application = Application.builder().token(self.token).build()
application.add_handler(CommandHandler("start", self.start_command))
application.add_handler(CommandHandler("balance", self.balance_command))
application.add_handler(CommandHandler("prices", self.prices_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
application.add_handler(MessageHandler(filters.VOICE, self.handle_voice))
logger.info("Bot iniciado con polling")
application.run_polling(allowed_updates=Update.ALL_TYPES)
except Exception as e:
logger.error(f"Error iniciando bot: {e}")

class AutoTrading:
def __init__(self, kraken_module):
self.kraken = kraken_module
self.running = True
self.trades_today = 0
self.max_trades = 15
logger.info("Auto-trading inicializado")

def run(self):
while self.running:
try:
balance = self.kraken.get_balance()
if balance:
usd_balance = float(balance.get('ZUSD', 0))
logger.info(f"Balance: ${usd_balance:.2f}")
if usd_balance > 160 and self.trades_today < self.max_trades:
sol_price = self.kraken.get_ticker_price('SOLUSD')
if sol_price:
volume = 20 / sol_price
if volume >= 0.1:
result = self.kraken.place_order('SOLUSD', 'buy', volume)
if result['success']:
self.trades_today += 1
logger.info(f"Auto-compra: {result['txid']}")
time.sleep(300)
except Exception as e:
logger.error(f"Error auto-trading: {e}")
time.sleep(60)

app = Flask(__name__)

@app.route('/')
def home():
return jsonify({
'status': 'OMNIX Global Bot Running',
'version': '1.0.0',
'features': ['Trading Cuadrilingue', 'Auto-trading', 'Voice Commands']
})

@app.route('/health')
def health():
return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

def main():
logger.info("Iniciando OMNIX Global Bot...")
if not all([TELEGRAM_TOKEN, KRAKEN_API_KEY, KRAKEN_SECRET]):
logger.error("Variables de entorno faltantes")
return
kraken = KrakenModule()
telegram_bot = TelegramBot(kraken)
auto_trading = AutoTrading(kraken)
telegram_thread = threading.Thread(target=telegram_bot.start_polling, daemon=True)
trading_thread = threading.Thread(target=auto_trading.run, daemon=True)
telegram_thread.start()
trading_thread.start()
logger.info("OMNIX Global Bot iniciado completamente")
app.run(host='0.0.0.0', port=PORT, debug=False)

if __name__ == "__main__":
main()
