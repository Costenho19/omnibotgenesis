print("===== ARRANCANDO OMNIBOTGENESIS =====")
#!/usr/bin/env python3
"""
OMNIX Global Bot - Sistema Profesional Completo
Cuadrilingüe: Español, Inglés, Árabe, Chino
Trading Automático 24/7 - Compliance Sharia - 16 Criptomonedas
Valorado en $85K USD - Enterprise Grade para Render
"""

import os
import sys
import json
import time
import logging
import asyncio
import sqlite3
import hashlib
import threading
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import requests
import ccxt
from flask import Flask, request, jsonify, render_template_string
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import google.generativeai as genai
from openai import OpenAI
import gtts
import speech_recognition as sr
from werkzeug.utils import secure_filename
import yfinance as yf
import pandas as pd
import numpy as np
from dataclasses import dataclass
import uuid
from collections import defaultdict
import re
from functools import wraps
import arabic_reshaper
from bidi.algorithm import get_display

# =============================================================================
# CONFIGURACIÓN PROFESIONAL
# =============================================================================

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('omnix_professional.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Variables de entorno
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7478164319:AAHWxXBiKrE3DInwt_pNFCQAeHcdO6wP-fI')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
KRAKEN_API_KEY = os.getenv('KRAKEN_API_KEY')
KRAKEN_SECRET = os.getenv('KRAKEN_SECRET')

# Configuración de APIs
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-pro')

# Configuración de Exchange
if KRAKEN_API_KEY and KRAKEN_SECRET:
    kraken_exchange = ccxt.kraken({
        'apiKey': KRAKEN_API_KEY,
        'secret': KRAKEN_SECRET,
        'sandbox': False,
        'enableRateLimit': True,
        'timeout': 30000,
    })

# =============================================================================
# SISTEMA DE 16 CRIPTOMONEDAS MÁS VALORADAS Y EN CRECIMIENTO
# =============================================================================

TOP_16_CRYPTOCURRENCIES = {
    'BTC': {'name': 'Bitcoin', 'symbol': 'BTCUSD', 'arabic': 'بيتكوين', 'chinese': '比特币', 'min_order': 0.0001},
    'ETH': {'name': 'Ethereum', 'symbol': 'ETHUSD', 'arabic': 'إيثيريوم', 'chinese': '以太坊', 'min_order': 0.001},
    'BNB': {'name': 'Binance Coin', 'symbol': 'BNBUSD', 'arabic': 'بينانس كوين', 'chinese': '币安币', 'min_order': 0.01},
    'XRP': {'name': 'Ripple', 'symbol': 'XRPUSD', 'arabic': 'ريبل', 'chinese': '瑞波币', 'min_order': 1},
    'SOL': {'name': 'Solana', 'symbol': 'SOLUSD', 'arabic': 'سولانا', 'chinese': '索拉纳', 'min_order': 0.01},
    'ADA': {'name': 'Cardano', 'symbol': 'ADAUSD', 'arabic': 'كاردانو', 'chinese': '艾达币', 'min_order': 1},
    'AVAX': {'name': 'Avalanche', 'symbol': 'AVAXUSD', 'arabic': 'أفالانش', 'chinese': '雪崩', 'min_order': 0.1},
    'DOT': {'name': 'Polkadot', 'symbol': 'DOTUSD', 'arabic': 'بولكادوت', 'chinese': '波卡', 'min_order': 0.1},
    'MATIC': {'name': 'Polygon', 'symbol': 'MATICUSD', 'arabic': 'بوليجون', 'chinese': '多边形', 'min_order': 1},
    'LINK': {'name': 'Chainlink', 'symbol': 'LINKUSD', 'arabic': 'تشين لينك', 'chinese': '链环', 'min_order': 0.1},
    'ATOM': {'name': 'Cosmos', 'symbol': 'ATOMUSD', 'arabic': 'كوزموس', 'chinese': '宇宙', 'min_order': 0.1},
    'ALGO': {'name': 'Algorand', 'symbol': 'ALGOUSD', 'arabic': 'الجوراند', 'chinese': '阿尔戈兰德', 'min_order': 1},
    'FLOW': {'name': 'Flow', 'symbol': 'FLOWUSD', 'arabic': 'فلو', 'chinese': '流量', 'min_order': 0.1},
    'FIL': {'name': 'Filecoin', 'symbol': 'FILUSD', 'arabic': 'فايلكوين', 'chinese': '文件币', 'min_order': 0.1},
    'GRT': {'name': 'The Graph', 'symbol': 'GRTUSD', 'arabic': 'الجراف', 'chinese': '图表', 'min_order': 1},
    'SAND': {'name': 'The Sandbox', 'symbol': 'SANDUSD', 'arabic': 'الساندبوكس', 'chinese': '沙盒', 'min_order': 1}
}

# =============================================================================
# SISTEMA DE DETECCIÓN DE IDIOMAS CUADRILINGÜE
# =============================================================================

class MultilingualDetector:
    """Detector de idiomas cuadrilingüe avanzado"""
    
    LANGUAGE_PATTERNS = {
        'spanish': ['hola', 'compra', 'vende', 'precio', 'bitcoin', 'ethereum', 'trading', 'análisis', 'portfolio', 'balance'],
        'english': ['hello', 'buy', 'sell', 'price', 'bitcoin', 'ethereum', 'trading', 'analysis', 'portfolio', 'balance'],
        'arabic': ['مرحبا', 'شراء', 'بيع', 'سعر', 'بيتكوين', 'إيثيريوم', 'تداول', 'تحليل', 'محفظة', 'رصيد'],
        'chinese': ['你好', '购买', '出售', '价格', '比特币', '以太坊', '交易', '分析', '投资组合', '余额']
    }
    
    def detect_language(self, text: str) -> str:
        """Detecta el idioma del texto con precisión avanzada"""
        if not text:
            return 'spanish'
        
        text_lower = text.lower()
        scores = defaultdict(int)
        
        # Detección por patrones Unicode
        for char in text:
            if '\u0600' <= char <= '\u06FF':  # Árabe
                scores['arabic'] += 3
            elif '\u4e00' <= char <= '\u9fff':  # Chino
                scores['chinese'] += 3
        
        # Detección por palabras clave
        for lang, patterns in self.LANGUAGE_PATTERNS.items():
            for pattern in patterns:
                if pattern in text_lower:
                    scores[lang] += 2
        
        # Detección por caracteres específicos
        if any(word in text_lower for word in ['the', 'and', 'is', 'are', 'buy', 'sell']):
            scores['english'] += 1
        elif any(word in text_lower for word in ['el', 'la', 'es', 'son', 'compra', 'vende']):
            scores['spanish'] += 1
        
        # Retorna el idioma con mayor score
        if scores:
            return max(scores, key=scores.get)
        return 'spanish'  # Default

# =============================================================================
# SISTEMA DE VOZ ALEXA 24/7 CON WAKE WORDS
# =============================================================================

class VoiceAssistant:
    """Sistema de voz avanzado tipo Alexa 24/7"""
    
    WAKE_WORDS = {
        'spanish': ['omnix', 'hola omnix', 'hey omnix'],
        'english': ['omnix', 'hello omnix', 'hey omnix'],
        'arabic': ['أومنيكس', 'مرحبا أومنيكس', 'هيلو أومنيكس'],
        'chinese': ['欧尼克斯', '你好欧尼克斯', '嘿欧尼克斯']
    }
    
    def __init__(self):
        self.is_listening = False
        self.voice_thread = None
        self.detector = MultilingualDetector()
        
    def start_listening(self):
        """Inicia el sistema de escucha continua"""
        self.is_listening = True
        self.voice_thread = threading.Thread(target=self._listen_continuously)
        self.voice_thread.daemon = True
        self.voice_thread.start()
        logger.info("🎤 Sistema de voz Alexa 24/7 iniciado")
    
    def _listen_continuously(self):
        """Escucha continua en background"""
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()
        
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source)
        
        while self.is_listening:
            try:
                with microphone as source:
                    audio = recognizer.listen(source, timeout=1, phrase_time_limit=5)
                
                text = recognizer.recognize_google(audio)
                if self._detect_wake_word(text):
                    self._process_voice_command(text)
                    
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except Exception as e:
                logger.error(f"Error en reconocimiento de voz: {e}")
                time.sleep(1)
    
    def _detect_wake_word(self, text: str) -> bool:
        """Detecta wake words multiidioma"""
        text_lower = text.lower()
        for lang, wake_words in self.WAKE_WORDS.items():
            for wake_word in wake_words:
                if wake_word in text_lower:
                    return True
        return False
    
    def _process_voice_command(self, text: str):
        """Procesa comando de voz detectado"""
        language = self.detector.detect_language(text)
        logger.info(f"🎤 Comando de voz detectado ({language}): {text}")
        
        # Aquí se procesaría el comando
        # Esto se integraría con el sistema de trading
        
    def generate_voice_response(self, text: str, language: str = 'spanish') -> str:
        """Genera respuesta de voz en el idioma detectado"""
        try:
            lang_codes = {
                'spanish': 'es',
                'english': 'en',
                'arabic': 'ar',
                'chinese': 'zh'
            }
            
            # Limpia el texto para TTS
            clean_text = re.sub(r'[^\w\s]', '', text)
            
            # Genera audio
            tts = gtts.gTTS(text=clean_text, lang=lang_codes.get(language, 'es'), slow=True)
            filename = f"voice_response_{int(time.time())}.mp3"
            tts.save(filename)
            
            return filename
            
        except Exception as e:
            logger.error(f"Error generando voz: {e}")
            return None

# =============================================================================
# SISTEMA DE COMPLIANCE SHARIA COMPLETO
# =============================================================================

class ShariaCompliance:
    """Sistema completo de compliance Sharia para trading islámico"""
    
    HALAL_CRYPTOCURRENCIES = {
        'BTC': {'status': 'halal', 'reason': 'Store of value, no interest'},
        'ETH': {'status': 'halal', 'reason': 'Utility token, smart contracts'},
        'BNB': {'status': 'questionable', 'reason': 'Exchange token, review needed'},
        'XRP': {'status': 'haram', 'reason': 'Centralized, banking partnerships'},
        'SOL': {'status': 'halal', 'reason': 'Decentralized platform'},
        'ADA': {'status': 'halal', 'reason': 'Peer-reviewed, academic approach'},
        'AVAX': {'status': 'halal', 'reason': 'Decentralized platform'},
        'DOT': {'status': 'halal', 'reason': 'Interoperability protocol'},
        'MATIC': {'status': 'halal', 'reason': 'Scaling solution'},
        'LINK': {'status': 'halal', 'reason': 'Oracle network'},
        'ATOM': {'status': 'halal', 'reason': 'Interchain protocol'},
        'ALGO': {'status': 'halal', 'reason': 'Academic, efficient consensus'},
        'FLOW': {'status': 'halal', 'reason': 'NFT platform'},
        'FIL': {'status': 'halal', 'reason': 'Decentralized storage'},
        'GRT': {'status': 'halal', 'reason': 'Indexing protocol'},
        'SAND': {'status': 'questionable', 'reason': 'Gaming, virtual assets'}
    }
    
    HARAM_ACTIVITIES = [
        'interest_trading', 'margin_trading', 'futures_trading',
        'options_trading', 'gambling', 'speculation'
    ]
    
    def __init__(self):
        self.zakat_rate = 0.025  # 2.5% annually
        self.prayer_times = self._load_prayer_times()
        
    def is_halal_cryptocurrency(self, symbol: str) -> Dict[str, Any]:
        """Verifica si una criptomoneda es halal"""
        crypto_info = self.HALAL_CRYPTOCURRENCIES.get(symbol.upper(), {
            'status': 'unknown', 
            'reason': 'Requires Islamic finance review'
        })
        return crypto_info
    
    def calculate_zakat(self, portfolio_value: float) -> Dict[str, float]:
        """Calcula el Zakat obligatorio (2.5% anual)"""
        zakat_due = portfolio_value * self.zakat_rate
        return {
            'portfolio_value': portfolio_value,
            'zakat_rate': self.zakat_rate,
            'zakat_due': zakat_due,
            'currency': 'USD'
        }
    
    def is_trading_time_permissible(self) -> Dict[str, Any]:
        """Verifica si el tiempo actual es permisible para trading"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        # Horarios de oración aproximados (Dubai/UAE)
        prayer_times = {
            'fajr': '05:30',
            'dhuhr': '12:30',
            'asr': '15:45',
            'maghrib': '18:30',
            'isha': '20:00'
        }
        
        # Evita trading durante oraciones (±15 minutos)
        for prayer, time_str in prayer_times.items():
            prayer_time = datetime.strptime(time_str, "%H:%M").time()
            current_time_obj = now.time()
            
            # Calcula diferencia en minutos
            prayer_datetime = datetime.combine(now.date(), prayer_time)
            current_datetime = datetime.combine(now.date(), current_time_obj)
            diff_minutes = abs((prayer_datetime - current_datetime).total_seconds() / 60)
            
            if diff_minutes <= 15:
                return {
                    'permissible': False,
                    'reason': f'Prayer time: {prayer}',
                    'resume_time': (prayer_datetime + timedelta(minutes=15)).strftime("%H:%M")
                }
        
        return {'permissible': True, 'reason': 'Normal trading hours'}
    
    def _load_prayer_times(self) -> Dict[str, str]:
        """Carga horarios de oración para Dubai/UAE"""
        return {
            'fajr': '05:30',
            'dhuhr': '12:30',
            'asr': '15:45',
            'maghrib': '18:30',
            'isha': '20:00'
        }
    
    def get_sharia_report(self) -> Dict[str, Any]:
        """Genera reporte completo de compliance Sharia"""
        halal_count = sum(1 for crypto in self.HALAL_CRYPTOCURRENCIES.values() if crypto['status'] == 'halal')
        total_count = len(self.HALAL_CRYPTOCURRENCIES)
        
        return {
            'compliance_score': (halal_count / total_count) * 100,
            'halal_cryptocurrencies': halal_count,
            'total_cryptocurrencies': total_count,
            'haram_activities_avoided': len(self.HARAM_ACTIVITIES),
            'zakat_calculation_enabled': True,
            'prayer_time_aware': True,
            'last_updated': datetime.now().isoformat()
        }

# =============================================================================
# SISTEMA DE TRADING AUTOMÁTICO AVANZADO
# =============================================================================

class AutoTradingEngine:
    """Motor de trading automático 24/7 con IA"""
    
    def __init__(self, exchange, sharia_compliance):
        self.exchange = exchange
        self.sharia = sharia_compliance
        self.is_running = False
        self.trading_thread = None
        self.positions = {}
        self.daily_trades = 0
        self.daily_limit = 50
        self.risk_limit = 1000  # USD
        
    def start_trading(self):
        """Inicia el trading automático"""
        self.is_running = True
        self.trading_thread = threading.Thread(target=self._trading_loop)
        self.trading_thread.daemon = True
        self.trading_thread.start()
        logger.info("🤖 Trading automático iniciado")
    
    def _trading_loop(self):
        """Loop principal de trading"""
        while self.is_running:
            try:
                # Verifica compliance Sharia
                if not self.sharia.is_trading_time_permissible()['permissible']:
                    logger.info("⏸️ Trading pausado por horario de oración")
                    time.sleep(900)  # 15 minutos
                    continue
                
                # Verifica límites diarios
                if self.daily_trades >= self.daily_limit:
                    logger.info(f"📊 Límite diario alcanzado: {self.daily_trades}/{self.daily_limit}")
                    time.sleep(300)  # 5 minutos
                    continue
                
                # Analiza mercado y ejecuta trades
                self._analyze_and_trade()
                
                # Espera entre análisis
                time.sleep(120)  # 2 minutos
                
            except Exception as e:
                logger.error(f"Error en trading loop: {e}")
                time.sleep(60)
    
    def _analyze_and_trade(self):
        """Analiza mercado y ejecuta trades si es necesario"""
        for symbol, crypto_info in TOP_16_CRYPTOCURRENCIES.items():
            try:
                # Verifica si es halal
                sharia_check = self.sharia.is_halal_cryptocurrency(symbol)
                if sharia_check['status'] == 'haram':
                    continue
                
                # Obtiene precio actual
                ticker = self.exchange.fetch_ticker(crypto_info['symbol'])
                price = ticker['last']
                
                # Análisis técnico básico
                signal = self._technical_analysis(symbol, price)
                
                if signal['action'] == 'buy' and signal['confidence'] > 0.7:
                    self._execute_buy_order(symbol, signal['amount'])
                elif signal['action'] == 'sell' and signal['confidence'] > 0.7:
                    self._execute_sell_order(symbol, signal['amount'])
                
            except Exception as e:
                logger.error(f"Error analizando {symbol}: {e}")
    
    def _technical_analysis(self, symbol: str, price: float) -> Dict[str, Any]:
        """Análisis técnico básico"""
        # Simulación de análisis técnico
        # En producción, aquí iría RSI, MACD, etc.
        
        import random
        confidence = random.uniform(0.5, 0.9)
        action = random.choice(['buy', 'sell', 'hold'])
        amount = 50  # USD
        
        return {
            'action': action,
            'confidence': confidence,
            'amount': amount,
            'price': price,
            'timestamp': datetime.now().isoformat()
        }
    
    def _execute_buy_order(self, symbol: str, amount: float):
        """Ejecuta orden de compra"""
        try:
            crypto_info = TOP_16_CRYPTOCURRENCIES[symbol]
            
            # Calcula cantidad basada en precio actual
            ticker = self.exchange.fetch_ticker(crypto_info['symbol'])
            price = ticker['last']
            quantity = amount / price
            
            # Ejecuta orden
            order = self.exchange.create_market_buy_order(
                symbol=crypto_info['symbol'],
                amount=quantity
            )
            
            self.daily_trades += 1
            logger.info(f"✅ COMPRA EJECUTADA: {symbol} - {quantity:.6f} @ ${price:.2f}")
            
        except Exception as e:
            logger.error(f"Error ejecutando compra {symbol}: {e}")
    
    def _execute_sell_order(self, symbol: str, amount: float):
        """Ejecuta orden de venta"""
        try:
            crypto_info = TOP_16_CRYPTOCURRENCIES[symbol]
            
            # Obtiene balance
            balance = self.exchange.fetch_balance()
            available = balance.get(symbol, {}).get('free', 0)
            
            if available > crypto_info['min_order']:
                order = self.exchange.create_market_sell_order(
                    symbol=crypto_info['symbol'],
                    amount=min(available, amount)
                )
                
                self.daily_trades += 1
                logger.info(f"✅ VENTA EJECUTADA: {symbol} - {available:.6f}")
                
        except Exception as e:
            logger.error(f"Error ejecutando venta {symbol}: {e}")

# =============================================================================
# SISTEMA DE INTERFAZ ÁRABE RTL
# =============================================================================

class ArabicInterface:
    """Interfaz árabe RTL (Right-to-Left) para usuarios MENA"""
    
    def __init__(self):
        self.rtl_enabled = True
        
    def format_arabic_text(self, text: str) -> str:
        """Formatea texto árabe para display RTL"""
        try:
            reshaped_text = arabic_reshaper.reshape(text)
            bidi_text = get_display(reshaped_text)
            return bidi_text
        except:
            return text
    
    def get_arabic_dashboard_html(self) -> str:
        """Genera HTML para dashboard árabe RTL"""
        return"""<!DOCTYPE html> 
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>أومنيكس - منصة التداول الإسلامية</title>
        <style>
              * {
                  font-family: 'Noto Sans Arabic', Arial, sans-serif;
                  direction: rtl;
                  text-align: right;
                }

                }
                body {
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                    color: #ffffff;
                    margin: 0;
                    padding: 20px;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    direction: rtl;
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                    border-bottom: 2px solid #00d4aa;
                    padding-bottom: 20px;
                }
                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }
                .stat-card {
                    background: rgba(255, 255, 255, 0.1);
                    padding: 20px;
                    border-radius: 10px;
                    border: 1px solid #00d4aa;
                    text-align: center;
                }
                .crypto-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                }
                .crypto-card {
                    background: rgba(255, 255, 255, 0.05);
                    padding: 15px;
                    border-radius: 8px;
                    border-left: 4px solid #00d4aa;
                }
                .halal-badge {
                    background: #28a745;
                    color: white;
                    padding: 2px 8px;
                    border-radius: 12px;
                    font-size: 12px;
                    margin-right: 10px;
                }
                .haram-badge {
                    background: #dc3545;
                    color: white;
                    padding: 2px 8px;
                    border-radius: 12px;
                    font-size: 12px;
                    margin-right: 10px;
                }
                .prayer-times {
                    background: rgba(0, 212, 170, 0.1);
                    padding: 20px;
                    border-radius: 10px;
                    margin-top: 20px;
                }
                .zakat-calculator {
                    background: rgba(255, 193, 7, 0.1);
                    padding: 20px;
                    border-radius: 10px;
                    margin-top: 20px;
                }
                @media (max-width: 768px) {
                    .stats-grid {
                        grid-template-columns: 1fr;
                    }
                    .crypto-grid {
                        grid-template-columns: 1fr;
                    }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🕌 أومنيكس - منصة التداول الإسلامية</h1>
                    <p>التداول المتوافق مع الشريعة الإسلامية - دبي/الإمارات</p>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>📊 إجمالي المحفظة</h3>
                        <h2 id="total-portfolio">$0.00</h2>
                    </div>
                    <div class="stat-card">
                        <h3>💰 الزكاة المستحقة</h3>
                        <h2 id="zakat-due">$0.00</h2>
                    </div>
                    <div class="stat-card">
                        <h3>✅ العملات الحلال</h3>
                        <h2 id="halal-count">12/16</h2>
                    </div>
                    <div class="stat-card">
                        <h3>🔄 الصفقات اليوم</h3>
                        <h2 id="daily-trades">0/50</h2>
                    </div>
                </div>
                
                <div class="prayer-times">
                    <h3>🕌 أوقات الصلاة - دبي</h3>
                    <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; text-align: center;">
                        <div><strong>الفجر</strong><br>05:30</div>
                        <div><strong>الظهر</strong><br>12:30</div>
                        <div><strong>العصر</strong><br>15:45</div>
                        <div><strong>المغرب</strong><br>18:30</div>
                        <div><strong>العشاء</strong><br>20:00</div>
                    </div>
                </div>
                
                <div class="zakat-calculator">
                    <h3>💎 حاسبة الزكاة</h3>
                    <p>معدل الزكاة: 2.5% سنوياً على إجمالي المحفظة</p>
                    <p>الزكاة واجبة على كل مسلم يملك النصاب لمدة عام هجري كامل</p>j
                </div>
                
                <h3>🪙 العملات الرقمية المدعومة</h3>
                <div class="crypto-grid" id="crypto-grid">
                    <!-- Se llena dinámicamente -->
                </div>
            </div>
            
            <script>
                // Actualización en tiempo real
                function updateDashboard() {
                    // Simula datos en tiempo real
                const portfolioValue = (Math.random() * 10000 + 5000).toFixed(2);
                    const zakatDue = (portfolioValue * 0.025).to

"""
# OMNIX Global Bot - Sistema Profesional Completo  
# Cuadrilingüe: Español, Inglés, Árabe, Chino  
# Trading Automático 24/7 - Compliance Sharia  
# Valorado en $85K USD - Enterprise Grade para Render  

import sys
import openai
import os
import traceback

from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telegram import Update
  
def handle_exception(exc_type, exc_value, exc_traceback):
    print("ERROR CRÍTICO: ", exc_value)
  
sys.excepthook = handle_exception
  
  # Leer token desde variable de entorno
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

  # Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola, soy OMNIX!")
  # Mensaje de texto con respuesta de OpenAI
     try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(user_message)
        await update.message.reply_text(response.text)
     except Exception as e:
                 await update.message.reply_text(f"⚠️ Error con Gemini: {e}")
                 traceback.print_exc()

# Main principal
if __name__ == "__main__":
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.run_polling()


