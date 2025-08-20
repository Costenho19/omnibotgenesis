#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNIX V5.1 – Railway Ready
Autor: Harold Nunes (ajustes operativos y hardening)
"""

import os
import time
import json
import threading
import logging
from datetime import datetime
from typing import Dict, Optional

import requests
from flask import Flask, request, jsonify

# Opcional/backup (no obligatorio en runtime, pero útil si lo tienes)
try:
    import ccxt
except Exception:
    ccxt = None

import base64
import hashlib
import hmac
import urllib.parse
import urllib.request

# =========================
#  ENV / LOGGING
# =========================
def load_env_variables():
    # Si hay variables de Railway, no hace falta .env
    railway_vars = ['KRAKEN_API_KEY', 'KRAKEN_SECRET', 'TELEGRAM_BOT_TOKEN']
    if any(os.getenv(v) for v in railway_vars):
        return
    # Fallback .env (opcional)
    try:
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    k, v = line.strip().split('=', 1)
                    os.environ.setdefault(k, v)
    except Exception:
        pass

load_env_variables()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] OMNIX: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("OMNIX")

# =========================
#  OMNIX CORE
# =========================
class OmnixRealSystem:
    def __init__(self):
        self._nonce_lock = threading.Lock()
        self._last_nonce = 0

        # API keys
        self.kraken_key = os.getenv('KRAKEN_API_KEY')
        self.kraken_secret = os.getenv('KRAKEN_SECRET') or os.getenv('KRAKEN_API_SECRET')
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_auth_chat = os.getenv('TELEGRAM_AUTH_CHAT_ID')  # opcional (solo autorizar un chat)

        # Endpoints
        self.kraken_api_url = 'https://api.kraken.com'

        # CCXT opcional como backup
        self.kraken_ccxt = None
        if ccxt and self.kraken_key and self.kraken_secret:
            try:
                self.kraken_ccxt = ccxt.kraken({
                    'apiKey': self.kraken_key,
                    'secret': self.kraken_secret,
                    'enableRateLimit': True,
                    'timeout': 30000,
                })
                self.kraken_ccxt.nonce = lambda: int(time.time() * 1000)
                logger.info("CCXT Kraken listo (backup).")
            except Exception as e:
                logger.warning(f"CCXT no disponible: {e}")

        logger.info("APIs configuradas.")

    # ---------- Utilidades Kraken ----------
    def _get_nonce(self) -> int:
        with self._nonce_lock:
            n = int(time.time() * 1_000_000)  # microsegundos (suficiente y monotónico)
            if n <= self._last_nonce:
                n = self._last_nonce + 1
            self._last_nonce = n
            return n

    def _kraken_sign(self, urlpath: str, data: dict) -> str:
        """
        Firma correcta Kraken:
        urlpath debe ser "/0/private/<Endpoint>"
        """
        postdata = urllib.parse.urlencode(data)
        encoded = (str(data['nonce']) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()
        mac = hmac.new(base64.b64decode(self.kraken_secret), message, hashlib.sha512)
        return base64.b64encode(mac.digest()).decode()

    def kraken_api_public(self, endpoint: str, params: dict = None) -> Dict:
        try:
            url = f"{self.kraken_api_url}/0/public/{endpoint}"
            r = requests.get(url, params=params or {}, timeout=15)
            r.raise_for_status()
            j = r.json()
            if j.get('error'):
                return {'success': False, 'error': j['error']}
            return {'success': True, 'data': j['result']}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def kraken_api_private(self, endpoint: str, data: dict = None) -> Optional[Dict]:
        """
        Llamada privada directa (más confiable). Devuelve dict result o {'error':[...]}.
        """
        if not (self.kraken_key and self.kraken_secret):
            return {'error': ['Faltan KRAKEN_API_KEY/KRAKEN_SECRET']}
        if data is None:
            data = {}
        data['nonce'] = self._get_nonce()

        urlpath = f"/0/private/{endpoint}"
        postdata = urllib.parse.urlencode(data).encode()
        headers = {
            'API-Key': self.kraken_key,
            'API-Sign': self._kraken_sign(urlpath, data),
            'User-Agent': 'OMNIX-Railway/1.0'
        }
        req = urllib.request.Request(self.kraken_api_url + urlpath, postdata, headers)
        try:
            with urllib.request.urlopen(req, timeout=20) as res:
                result = json.loads(res.read().decode())
            # Kraken responde {'error':[], 'result':{...}}
            if result.get('error'):
                return {'error': result['error']}
            return result.get('result', {})
        except Exception as e:
            logger.error(f"Kraken private error: {e}")
            return {'error': [str(e)]}

    # ---------- Conversión símbolos ----------
    @staticmethod
    def to_kraken_pair(symbol: str) -> str:
        """
        'BTC/USD' -> 'XBTUSD', 'ETH/USD'->'ETHUSD', etc.
        """
        s = symbol.upper().replace(' ', '')
        mapping = {
            'BTC/USD': 'XBTUSD', 'BTCUSD': 'XBTUSD',
            'ETH/USD': 'ETHUSD', 'ETHUSD': 'ETHUSD',
            'SOL/USD': 'SOLUSD', 'SOLUSD': 'SOLUSD',
            'ADA/USD': 'ADAUSD', 'ADAUSD': 'ADAUSD',
            'DOT/USD': 'DOTUSD', 'DOTUSD': 'DOTUSD',
        }
        return mapping.get(s, s)

    # ---------- Precios / Balance ----------
    def get_real_price(self, symbol: str) -> Dict:
        try:
            kr_pair = self.to_kraken_pair(symbol)
            pub = self.kraken_api_public('Ticker', {'pair': kr_pair})
            if not pub['success']:
                return {'success': False, 'error': str(pub.get('error'))}
            pair_key = list(pub['data'].keys())[0]
            t = pub['data'][pair_key]
            price = float(t['c'][0])
            openp = float(t['o'])
            change = ((price - openp) / openp) * 100 if openp else 0.0
            return {
                'success': True,
                'symbol': symbol,
                'price': price,
                'bid': float(t['b'][0]),
                'ask': float(t['a'][0]),
                'change_24h': round(change, 2),
                'volume': float(t['v'][1]),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_real_balance(self) -> Dict:
        try:
            res = self.kraken_api_private('Balance')
            if res is None:
                return {'success': False, 'error': 'Sin respuesta de Kraken'}
            if 'error' in res and res['error']:
                return {'success': False, 'error': res['error'][0]}

            bal = {}
            for cur, amt in res.items():
                try:
                    val = float(amt)
                except Exception:
                    continue
                if val <= 0:
                    continue
                clean = cur.replace('Z', '').replace('X', '')
                if clean == 'XBT':
                    clean = 'BTC'
                bal[clean] = {'total': val, 'available': val}
            return {'success': True, 'balance': bal, 'timestamp': datetime.now().isoformat()}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ---------- Órdenes ----------
    def execute_buy_order(self, symbol: str, amount_usd: float) -> Dict:
        """
        Compra a mercado por monto en USD (convierte a volumen).
        """
        if amount_usd <= 0:
            return {'success': False, 'error': 'amount debe ser > 0'}
        price_info = self.get_real_price(symbol)
        if not price_info['success']:
            return {'success': False, 'error': f"Precio no disponible: {price_info.get('error')}"}
        price = price_info['price']
        volume = max(amount_usd / price, 0.0)
        kr_pair = self.to_kraken_pair(symbol)

        order = self.kraken_api_private('AddOrder', {
            'pair': kr_pair,
            'type': 'buy',
            'ordertype': 'market',
            'volume': f"{volume:.8f}"
        })
        if order and 'txid' in order:
            txid = order['txid'][0] if isinstance(order['txid'], list) else order['txid']
            return {'success': True, 'symbol': symbol, 'amount_usd': amount_usd, 'volume': volume, 'txid': txid}
        return {'success': False, 'error': (order.get('error', ['Fallo desconocido'])[0] if isinstance(order, dict) else 'Fallo desconocido')}

    # Texto libre tipo “compra 20 btc”
    def process_buy_order_text(self, message: str) -> str:
        import re
        msg = message.lower()
        nums = re.findall(r'\d+\.?\d*', msg)
        amount = float(nums[0]) if nums else None
        crypto = None
        for name, pair in {
            'bitcoin': 'BTC/USD', 'btc': 'BTC/USD',
            'ethereum': 'ETH/USD', 'eth': 'ETH/USD',
            'solana': 'SOL/USD', 'sol': 'SOL/USD',
            'cardano': 'ADA/USD', 'ada': 'ADA/USD',
            'dot': 'DOT/USD', 'polkadot': 'DOT/USD'
        }.items():
            if name in msg:
                crypto = pair
                break

        if not amount or not crypto:
            return "⚠️ Especifica monto en USD y crypto (ej: compra 20 dólares de bitcoin)."

        if amount > 500:
            return f"❌ Límite máximo por orden: $500. Solicitaste ${amount:.2f}"

        r = self.execute_buy_order(crypto, amount)
        if r['success']:
            return f"✅ Compra ejecutada: ${amount:.2f} de {crypto} (≈ {r['volume']:.8f}). TX: {r['txid']}"
        return f"❌ Error al comprar: {r.get('error','desconocido')}"

    # Telegram commands
    def process_telegram_command(self, text: str) -> str:
        t = text.strip().lower()

        if t.startswith('/balance'):
            b = self.get_real_balance()
            if not b['success']:
                return f"❌ ERROR KRAKEN: {b.get('error')}"
            if not b.get('balance'):
                return "💰 Balance: 0"
            out = ["💰 Balance Kraken:"]
            for c, d in b['balance'].items():
                out.append(f"• {c}: {d['total']:.8f}")
            return "\n".join(out)

        if t.startswith('/precio') or t.startswith('/price'):
            parts = t.split()
            sym = 'BTC/USD'
            if len(parts) > 1:
                sym = f"{parts[1].upper()}/USD"
            p = self.get_real_price(sym)
            if not p['success']:
                return f"❌ {p.get('error')}"
            return f"📊 {sym}: ${p['price']:.2f} | 24h: {p['change_24h']:.2f}%"

        if any(k in t for k in ['/comprar', '/compra', 'compra ']):
            return self.process_buy_order_text(t)

        return "🤖 OMNIX listo. Usa /balance, /precio BTC, o escribe: compra 20 dólares de bitcoin."

# =========================
#  TELEGRAM POLLING
# =========================
def start_telegram_polling(omnix: OmnixRealSystem):
    token = omnix.telegram_token
    if not token:
        logger.warning("Telegram desactivado (TELEGRAM_BOT_TOKEN no definido).")
        return

    auth_chat = omnix.telegram_auth_chat  # puede ser None (sin restricción)
    offset = 0
    logger.info("Telegram polling activo…")

    while True:
        try:
            url = f'https://api.telegram.org/bot{token}/getUpdates'
            params = {'offset': offset, 'timeout': 50}
            r = requests.get(url, params=params, timeout=60)
            j = r.json()

            if j.get('ok'):
                for upd in j.get('result', []):
                    offset = upd['update_id'] + 1
                    msg = upd.get('message') or {}
                    chat_id = str(msg.get('chat', {}).get('id', ''))
                    text = msg.get('text', '')

                    if not text:
                        continue

                    # Restringir si se configuró TELEGRAM_AUTH_CHAT_ID
                    if auth_chat and chat_id != str(auth_chat):
                        continue

                    reply = omnix.process_telegram_command(text)
                    send_url = f'https://api.telegram.org/bot{token}/sendMessage'
                    requests.post(send_url, json={'chat_id': chat_id, 'text': reply}, timeout=20)
        except Exception as e:
            logger.error(f"Telegram polling error: {e}")
            time.sleep(5)

# =========================
#  FLASK API
# =========================
app = Flask(__name__)
omnix = OmnixRealSystem()

@app.route('/')
def index():
    return """
    <html><head><meta charset="utf-8"><title>OMNIX V5.1</title></head>
    <body style="background:#000;color:#0f0;font-family:monospace">
      <h1>OMNIX V5.1 – ONLINE</h1>
      <ul>
        <li>GET /api/status</li>
        <li>GET /api/balance</li>
        <li>GET /api/price/BTC</li>
        <li>POST /api/buy { "symbol": "BTC/USD", "amount": 20 }</li>
      </ul>
    </body></html>
    """

@app.route('/api/status')
def api_status():
    return jsonify({
        'status': 'operational',
        'telegram': 'active' if omnix.telegram_token else 'disabled',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/balance')
def api_balance():
    return jsonify(omnix.get_real_balance())

@app.route('/api/price/<symbol>')
def api_price(symbol):
    return jsonify(omnix.get_real_price(f"{symbol.upper()}/USD"))

@app.route('/api/buy', methods=['POST'])
def api_buy():
    data = request.get_json(silent=True) or {}
    symbol = data.get('symbol', 'BTC/USD')
    amount = float(data.get('amount', 0))
    return jsonify(omnix.execute_buy_order(symbol, amount)), 200 if amount > 0 else 400

# =========================
#  MAIN
# =========================
if __name__ == "__main__":
    # Iniciar Telegram polling en hilo daemon
    t = threading.Thread(target=start_telegram_polling, args=(omnix,), daemon=True)
    t.start()

    # Iniciar Flask (puerto dinámico para Railway)
    port = int(os.getenv("PORT", "5000"))
    logger.info(f"Servidor Flask en 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
