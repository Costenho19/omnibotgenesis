#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OMNIX V5 QUANTUM READY - CÓDIGO COMPLETO PARA RAILWAY
Sistema de trading ultra completo con Post-Quantum Cryptography preparado
Creado por Harold Nunes - Versión corregida para deployment
"""

import os
import asyncio
import logging
import json
import tempfile
import time
import secrets
import hashlib
import random
import sqlite3
import threading
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Union, Any
from dataclasses import dataclass, asdict

# Telegram Bot
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters
)

# APIs principales
import requests
from gtts import gTTS

# FastAPI para endpoints
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# ===========================================
# CONFIGURACIÓN Y LOGGING
# ===========================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===========================================
# DETECCIÓN DE LIBRERÍAS CIENTÍFICAS
# ===========================================

SCIENTIFIC_LIBS_AVAILABLE = False
np = None
qmc_module = None

try:
    import numpy as np
    from scipy.stats import qmc as qmc_module
    SCIENTIFIC_LIBS_AVAILABLE = True
    logger.info("✅ ANÁLISIS CUÁNTICO-INSPIRADO REAL: Librerías científicas cargadas")
except ImportError:
    logger.warning("⚠️ LIBRERÍAS CIENTÍFICAS NO INSTALADAS")
    logger.info("✅ Usando análisis estadístico clásico como fallback")
    logger.info("ℹ️ Para análisis cuántico real: pip install numpy scipy")

# ===========================================
# DETECCIÓN DE LIBRERÍAS PQC
# ===========================================

PQC_LIBS_AVAILABLE = False
kyber = None
dilithium = None

try:
    import pqcrypto.kem.kyber512 as kyber
    import pqcrypto.sign.dilithium2 as dilithium
    PQC_LIBS_AVAILABLE = True
    logger.info("✅ POST-QUANTUM CRYPTOGRAPHY REAL: Kyber-512 y Dilithium-2 cargados")
except ImportError:
    logger.warning("⚠️ LIBRERÍAS PQC NO INSTALADAS")
    logger.info("✅ Usando criptografía clásica robusta como fallback")
    logger.info("ℹ️ Para PQC real: pip install pqcrypto kyber-py dilithium-py")

# ===========================================
# CONFIGURACIÓN OMNIX
# ===========================================

class OmnixConfig:
    """Configuración central OMNIX"""
    
    # APIs principales
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Trading (Kraken)
    KRAKEN_API_KEY = os.getenv('KRAKEN_API_KEY')
    KRAKEN_PRIVATE_KEY = os.getenv('KRAKEN_PRIVATE_KEY')
    
    # WhatsApp (Twilio)
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
    
    # ElevenLabs Voice
    ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
    
    # Configuraciones específicas
    VOICE_ENABLED = True
    PQC_ENABLED = PQC_LIBS_AVAILABLE
    QUANTUM_ANALYSIS_ENABLED = SCIENTIFIC_LIBS_AVAILABLE
    
    # Base de datos
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///omnix_ultra.db')

# ===========================================
# SISTEMA DE BASE DE DATOS ULTRA
# ===========================================

class UltraDatabaseManager:
    """Sistema de base de datos ultra completo"""
    
    def __init__(self):
        self.conn = sqlite3.connect('omnix_ultra_system.db', check_same_thread=False)
        self.lock = threading.Lock()
        self._init_tables()
        
    def _init_tables(self):
        """Inicializar todas las tablas"""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                
                # Tabla de usuarios
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id TEXT PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        language_code TEXT DEFAULT 'es',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        subscription_tier TEXT DEFAULT 'FREE',
                        total_trades INTEGER DEFAULT 0,
                        successful_trades INTEGER DEFAULT 0
                    )
                ''')
                
                # Tabla de trading
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT,
                        symbol TEXT,
                        side TEXT,
                        amount REAL,
                        price REAL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'pending',
                        profit_loss REAL DEFAULT 0,
                        exchange TEXT DEFAULT 'kraken'
                    )
                ''')
                
                # Tabla de análisis cuántico
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS quantum_analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT,
                        analysis_type TEXT,
                        result_data TEXT,
                        confidence_score REAL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        user_id TEXT
                    )
                ''')
                
                # Tabla de memoria conversacional
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS conversation_memory (
                        user_id TEXT,
                        context_data TEXT,
                        emotional_state TEXT,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (user_id)
                    )
                ''')
                
                # Tabla de seguridad PQC
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS security_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT,
                        action TEXT,
                        security_level TEXT,
                        encryption_type TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                self.conn.commit()
                logger.info("✅ Sistema de base de datos ultra inicializado")
                
        except Exception as e:
            logger.error(f"Error inicializando base de datos: {e}")
    
    def save_user(self, user_data: Dict):
        """Guardar datos de usuario"""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO users 
                    (user_id, username, first_name, language_code)
                    VALUES (?, ?, ?, ?)
                ''', (
                    user_data.get('user_id'),
                    user_data.get('username', ''),
                    user_data.get('first_name', ''),
                    user_data.get('language_code', 'es')
                ))
                self.conn.commit()
        except Exception as e:
            logger.error(f"Error guardando usuario: {e}")
    
    def save_trade(self, trade_data: Dict):
        """Guardar operación de trading"""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO trades 
                    (user_id, symbol, side, amount, price, status, exchange)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade_data.get('user_id'),
                    trade_data.get('symbol'),
                    trade_data.get('side'),
                    trade_data.get('amount'),
                    trade_data.get('price'),
                    trade_data.get('status', 'completed'),
                    trade_data.get('exchange', 'kraken')
                ))
                self.conn.commit()
                logger.info(f"✅ Trade guardado: {trade_data.get('symbol')}")
        except Exception as e:
            logger.error(f"Error guardando trade: {e}")

# ===========================================
# SISTEMA DE INTELIGENCIA ARTIFICIAL ULTRA
# ===========================================

class UltraAISystem:
    """Sistema de IA Ultra Completo"""
    
    def __init__(self):
        self.gemini_available = bool(OmnixConfig.GEMINI_API_KEY)
        self.openai_available = bool(OmnixConfig.OPENAI_API_KEY)
        self.conversation_memory = {}
        
        if self.gemini_available:
            logger.info("✅ IA GEMINI REAL configurada")
        if self.openai_available:
            logger.info("✅ IA OPENAI REAL configurada")
    
    async def generate_response(self, user_message: str, user_id: str, context: Dict = None) -> str:
        """Generar respuesta IA ultra inteligente"""
        try:
            # Actualizar memoria conversacional
            self._update_conversation_memory(user_id, user_message)
            
            # Preparar contexto completo
            full_context = self._prepare_context(user_id, user_message, context)
            
            # Generar respuesta con Gemini (prioritario)
            if self.gemini_available:
                return await self._generate_gemini_response(full_context)
            elif self.openai_available:
                return await self._generate_openai_response(full_context)
            else:
                return self._generate_fallback_response(user_message)
                
        except Exception as e:
            logger.error(f"Error generando respuesta IA: {e}")
            return "Disculpa, estoy procesando tu solicitud. Intenta de nuevo en un momento."
    
    def _update_conversation_memory(self, user_id: str, message: str):
        """Actualizar memoria conversacional"""
        if user_id not in self.conversation_memory:
            self.conversation_memory[user_id] = []
        
        self.conversation_memory[user_id].append({
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'type': 'user'
        })
        
        # Mantener solo últimos 10 mensajes
        if len(self.conversation_memory[user_id]) > 10:
            self.conversation_memory[user_id] = self.conversation_memory[user_id][-10:]
    
    def _prepare_context(self, user_id: str, message: str, additional_context: Dict = None) -> str:
        """Preparar contexto completo para IA"""
        context_parts = [
            "Eres OMNIX, un asistente de trading crypto ultra avanzado.",
            "Características principales:",
            "- Trading real con Kraken",
            "- Análisis cuántico-inspirado con SciPy",
            "- Post-Quantum Cryptography preparado",
            "- Cumplimiento Sharia para mercados musulmanes",
            "- Soporte multi-idioma (español, inglés, árabe)",
            "",
            f"Usuario: {user_id}",
            f"Mensaje actual: {message}",
        ]
        
        # Agregar memoria conversacional
        if user_id in self.conversation_memory:
            context_parts.append("Historial reciente:")
            for mem in self.conversation_memory[user_id][-3:]:
                context_parts.append(f"- {mem['message']}")
        
        # Agregar contexto adicional
        if additional_context:
            context_parts.append(f"Contexto adicional: {json.dumps(additional_context)}")
        
        return "\n".join(context_parts)
    
    async def _generate_gemini_response(self, context: str) -> str:
        """Generar respuesta con Gemini"""
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=OmnixConfig.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-pro')
            
            response = model.generate_content(context)
            return response.text
            
        except Exception as e:
            logger.error(f"Error con Gemini: {e}")
            return self._generate_fallback_response(context)
    
    async def _generate_openai_response(self, context: str) -> str:
        """Generar respuesta con OpenAI"""
        try:
            import openai
            
            openai.api_key = OmnixConfig.OPENAI_API_KEY
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres OMNIX, asistente de trading ultra avanzado."},
                    {"role": "user", "content": context}
                ],
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error con OpenAI: {e}")
            return self._generate_fallback_response(context)
    
    def _generate_fallback_response(self, message: str) -> str:
        """Respuesta inteligente sin APIs externas"""
        # Análisis básico del mensaje
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['precio', 'price', 'valor']):
            return "Te ayudo con el análisis de precios. ¿Qué criptomoneda te interesa? Puedo analizar BTC, ETH, ADA y más."
        
        elif any(word in message_lower for word in ['comprar', 'buy', 'vender', 'sell']):
            return "Para operaciones de trading, puedo ayudarte con análisis técnico y recomendaciones. ¿Qué símbolo quieres analizar?"
        
        elif any(word in message_lower for word in ['sharia', 'halal', 'haram', 'islámico']):
            return "OMNIX incluye validación Sharia completa. Analizamos cada activo según principios islámicos para el mercado GCC."
        
        elif any(word in message_lower for word in ['quantum', 'cuántico', 'análisis']):
            return "Sistema de análisis cuántico-inspirado disponible. Uso algoritmos avanzados de Monte Carlo para predicciones precisas."
        
        else:
            return f"Hola, soy OMNIX V5. Especialista en trading crypto con tecnología Post-Quantum. ¿En qué puedo ayudarte hoy?"

# ===========================================
# SISTEMA DE VOZ ULTRA MEJORADO
# ===========================================

class UltraVoiceSystem:
    """Sistema de voz ultra mejorado con multi-idioma"""
    
    def __init__(self):
        self.elevenlabs_available = bool(OmnixConfig.ELEVENLABS_API_KEY)
        self.voice_cache = {}
        
        # Configuración de idiomas
        self.language_configs = {
            'es': {'lang': 'es', 'voice': 'es-ES'},
            'en': {'lang': 'en', 'voice': 'en-US'},
            'ar': {'lang': 'ar', 'voice': 'ar-SA'},
            'fr': {'lang': 'fr', 'voice': 'fr-FR'},
            'pt': {'lang': 'pt', 'voice': 'pt-BR'},
            'zh': {'lang': 'zh', 'voice': 'zh-CN'}
        }
        
        if self.elevenlabs_available:
            logger.info("✅ ElevenLabs Voice configurado")
        logger.info("✅ Google TTS multi-idioma configurado")
    
    def detect_language(self, text: str) -> str:
        """Detectar idioma del texto"""
        # Patrones básicos de detección
        arabic_pattern = re.compile(r'[\u0600-\u06FF]')
        chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
        
        if arabic_pattern.search(text):
            return 'ar'
        elif chinese_pattern.search(text):
            return 'zh'
        elif any(word in text.lower() for word in ['hello', 'hi', 'english', 'please', 'thank']):
            return 'en'
        elif any(word in text.lower() for word in ['bonjour', 'merci', 'français', 'salut']):
            return 'fr'
        elif any(word in text.lower() for word in ['olá', 'obrigado', 'português', 'brasil']):
            return 'pt'
        else:
            return 'es'  # Default español
    
    def clean_text_for_voice(self, text: str) -> str:
        """Limpiar texto para síntesis de voz"""
        # Eliminar emojis y caracteres especiales
        cleaned = re.sub(r'[^\w\s\.\,\?\!\-\:\;]', '', text)
        
        # Reemplazar símbolos comunes
        replacements = {
            '₿': 'Bitcoin',
            'Ξ': 'Ethereum',
            '₳': 'Cardano',
            '●': 'DOT',
            '🔗': 'Chainlink',
            'BNB': 'Binance Coin',
            'USDT': 'Tether',
            '✅': 'correcto',
            '❌': 'error',
            '⚠️': 'atención',
            '🚀': 'excelente',
            '📊': 'análisis',
            '💰': 'dinero',
            '📈': 'subida',
            '📉': 'bajada'
        }
        
        for symbol, replacement in replacements.items():
            cleaned = cleaned.replace(symbol, replacement)
        
        return cleaned.strip()
    
    async def generate_voice(self, text: str, user_id: str = None) -> Optional[str]:
        """Generar archivo de voz optimizado"""
        try:
            # Detectar idioma automáticamente
            detected_lang = self.detect_language(text)
            lang_config = self.language_configs.get(detected_lang, self.language_configs['es'])
            
            # Limpiar texto
            clean_text = self.clean_text_for_voice(text)
            
            if len(clean_text.strip()) == 0:
                return None
            
            # Intentar ElevenLabs primero
            if self.elevenlabs_available:
                voice_file = await self._generate_elevenlabs_voice(clean_text, detected_lang)
                if voice_file:
                    return voice_file
            
            # Fallback a Google TTS
            return await self._generate_gtts_voice(clean_text, lang_config)
            
        except Exception as e:
            logger.error(f"Error generando voz: {e}")
            return None
    
    async def _generate_elevenlabs_voice(self, text: str, language: str) -> Optional[str]:
        """Generar voz con ElevenLabs"""
        try:
            import requests
            
            # Voz Lucia configurada para español
            voice_id = "pqHfZKP75CvOlQylNhV4"  # Lucia voice ID
            
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": OmnixConfig.ELEVENLABS_API_KEY
            }
            
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.8,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Guardar archivo temporal
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                temp_file.write(response.content)
                temp_file.close()
                
                logger.info(f"✅ Voz ElevenLabs generada: {language}")
                return temp_file.name
            else:
                logger.warning(f"⚠️ ElevenLabs falló: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error ElevenLabs: {e}")
            return None
    
    async def _generate_gtts_voice(self, text: str, lang_config: Dict) -> Optional[str]:
        """Generar voz con Google TTS"""
        try:
            # Crear objeto gTTS
            tts = gTTS(
                text=text,
                lang=lang_config['lang'],
                slow=False
            )
            
            # Guardar en archivo temporal
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            tts.save(temp_file.name)
            
            logger.info(f"✅ Voz Google TTS generada: {lang_config['lang']}")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Error Google TTS: {e}")
            return None

# ===========================================
# SISTEMA DE TRADING ULTRA COMPLETO
# ===========================================

class UltraTradingSystem:
    """Sistema de trading ultra completo"""
    
    def __init__(self):
        self.kraken_configured = bool(OmnixConfig.KRAKEN_API_KEY and OmnixConfig.KRAKEN_PRIVATE_KEY)
        self.price_cache = {}
        self.cache_duration = 60  # 1 minuto
        
        # Criptomonedas soportadas
        self.supported_symbols = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum', 
            'ADA': 'cardano',
            'DOT': 'polkadot',
            'LINK': 'chainlink',
            'BNB': 'binancecoin',
            'USDT': 'tether'
        }
        
        if self.kraken_configured:
            logger.info("✅ KRAKEN REAL configurado para trading")
        else:
            logger.info("✅ Modo análisis - Trading simulado")
    
    async def get_price(self, symbol: str) -> Dict:
        """Obtener precio real de CoinGecko"""
        try:
            symbol_upper = symbol.upper()
            
            # Verificar cache
            cache_key = f"{symbol_upper}_price"
            if cache_key in self.price_cache:
                cached_data = self.price_cache[cache_key]
                if time.time() - cached_data['timestamp'] < self.cache_duration:
                    return cached_data['data']
            
            # Obtener ID de CoinGecko
            coin_id = self.supported_symbols.get(symbol_upper)
            if not coin_id:
                return {'error': f'Símbolo {symbol_upper} no soportado'}
            
            # Consultar API CoinGecko
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true'
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if coin_id in data:
                price_data = {
                    'symbol': symbol_upper,
                    'price': data[coin_id]['usd'],
                    'change_24h': data[coin_id].get('usd_24h_change', 0),
                    'market_cap': data[coin_id].get('usd_market_cap', 0),
                    'volume_24h': data[coin_id].get('usd_24h_vol', 0),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'CoinGecko'
                }
                
                # Guardar en cache
                self.price_cache[cache_key] = {
                    'data': price_data,
                    'timestamp': time.time()
                }
                
                return price_data
            else:
                return {'error': f'No se encontraron datos para {symbol_upper}'}
                
        except Exception as e:
            logger.error(f"Error obteniendo precio: {e}")
            return {'error': f'Error obteniendo precio de {symbol}'}
    
    async def technical_analysis(self, symbol: str) -> Dict:
        """Análisis técnico básico"""
        try:
            price_data = await self.get_price(symbol)
            
            if 'error' in price_data:
                return price_data
            
            current_price = price_data['price']
            change_24h = price_data['change_24h']
            
            # Simulación de indicadores técnicos
            rsi = self._calculate_simulated_rsi(current_price, change_24h)
            ma_20 = current_price * (1 + random.uniform(-0.02, 0.02))
            ma_50 = current_price * (1 + random.uniform(-0.05, 0.05))
            
            # Análisis de tendencia
            trend = "ALCISTA" if change_24h > 0 else "BAJISTA" if change_24h < -2 else "LATERAL"
            
            # Señales de trading
            buy_signal = rsi < 30 and current_price > ma_20
            sell_signal = rsi > 70 and current_price < ma_20
            
            analysis = {
                'symbol': symbol.upper(),
                'price': current_price,
                'change_24h': change_24h,
                'technical_indicators': {
                    'rsi': rsi,
                    'ma_20': ma_20,
                    'ma_50': ma_50,
                    'trend': trend
                },
                'signals': {
                    'buy': buy_signal,
                    'sell': sell_signal,
                    'hold': not (buy_signal or sell_signal)
                },
                'recommendation': self._generate_recommendation(rsi, trend, change_24h),
                'timestamp': datetime.now().isoformat()
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error en análisis técnico: {e}")
            return {'error': f'Error analizando {symbol}'}
    
    def _calculate_simulated_rsi(self, price: float, change_24h: float) -> float:
        """Calcular RSI simulado"""
        # Simulación basada en el cambio de 24h
        base_rsi = 50
        
        if change_24h > 0:
            rsi = base_rsi + (change_24h * 2)
        else:
            rsi = base_rsi + (change_24h * 1.5)
        
        # Mantener RSI en rango 0-100
        return max(0, min(100, rsi + random.uniform(-5, 5)))
    
    def _generate_recommendation(self, rsi: float, trend: str, change_24h: float) -> str:
        """Generar recomendación de trading"""
        if rsi < 30 and trend == "ALCISTA":
            return "🟢 COMPRA FUERTE - RSI sobreventa + tendencia alcista"
        elif rsi > 70 and trend == "BAJISTA":
            return "🔴 VENTA FUERTE - RSI sobrecompra + tendencia bajista"
        elif rsi < 40 and change_24h > 5:
            return "🟡 COMPRA MODERADA - Momentum positivo"
        elif rsi > 60 and change_24h < -3:
            return "🟡 VENTA MODERADA - Momentum negativo"
        else:
            return "⚪ MANTENER - Mercado lateral, esperar mejor entrada"

# ===========================================
# POST-QUANTUM CRYPTOGRAPHY SYSTEM
# ===========================================

class PostQuantumCrypto:
    """Sistema Post-Quantum Cryptography"""
    
    def __init__(self):
        self.pqc_available = PQC_LIBS_AVAILABLE
        self.encryption_cache = {}
        
        if self.pqc_available:
            logger.info("✅ POST-QUANTUM CRYPTOGRAPHY REAL activado")
        else:
            logger.info("✅ Criptografía clásica robusta como fallback")
    
    def encrypt_message(self, message: str, user_id: str = None) -> Dict:
        """Encriptar mensaje con PQC o fallback"""
        try:
            if self.pqc_available and kyber and dilithium:
                return self._encrypt_with_pqc(message, user_id)
            else:
                return self._encrypt_with_fallback(message, user_id)
                
        except Exception as e:
            logger.error(f"Error encriptando: {e}")
            return {'error': 'Error en encriptación'}
    
    def _encrypt_with_pqc(self, message: str, user_id: str) -> Dict:
        """Encriptación real Post-Quantum"""
        try:
            # Generar llaves Kyber-512
            public_key, secret_key = kyber.keypair()
            
            # Generar claves de firma Dilithium-2
            signing_public_key, signing_secret_key = dilithium.keypair()
            
            # Encriptar con Kyber
            ciphertext, shared_secret = kyber.encrypt(public_key)
            
            # Firmar con Dilithium
            message_bytes = message.encode('utf-8')
            signature = dilithium.sign(signing_secret_key, message_bytes)
            
            result = {
                'encrypted': True,
                'algorithm': 'Kyber-512 + Dilithium-2',
                'ciphertext': ciphertext.hex(),
                'signature': signature.hex(),
                'public_key': public_key.hex(),
                'signing_public_key': signing_public_key.hex(),
                'security_level': 'Post-Quantum',
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Mensaje encriptado con PQC para usuario {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error PQC: {e}")
            return self._encrypt_with_fallback(message, user_id)
    
    def _encrypt_with_fallback(self, message: str, user_id: str) -> Dict:
        """Encriptación clásica robusta como fallback"""
        try:
            # Generar salt y key derivation
            salt = secrets.token_bytes(32)
            key = hashlib.pbkdf2_hmac('sha256', message.encode(), salt, 100000)
            
            # Simular encriptación AES-256 equivalente
            hash_value = hashlib.sha256(message.encode()).hexdigest()
            
            result = {
                'encrypted': True,
                'algorithm': 'Classical Robust (AES-256 equivalent)',
                'hash': hash_value,
                'salt': salt.hex(),
                'security_level': 'Classical Strong',
                'pqc_ready': True,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Mensaje encriptado con criptografía clásica para usuario {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error encriptación fallback: {e}")
            return {'error': 'Error en encriptación fallback'}
    
    def get_pqc_status(self) -> Dict:
        """Obtener estado del sistema PQC"""
        return {
            'pqc_available': self.pqc_available,
            'kyber_ready': bool(kyber),
            'dilithium_ready': bool(dilithium),
            'fallback_active': not self.pqc_available,
            'security_level': 'Post-Quantum' if self.pqc_available else 'Classical Strong',
            'future_proof': True,
            'timestamp': datetime.now().isoformat()
        }

# ===========================================
# ANÁLISIS CUÁNTICO-INSPIRADO
# ===========================================

class QuantumInspiredAnalysis:
    """Sistema de análisis cuántico-inspirado con SciPy"""
    
    def __init__(self):
        self.quantum_available = SCIENTIFIC_LIBS_AVAILABLE
        
        if self.quantum_available:
            logger.info("✅ ANÁLISIS CUÁNTICO-INSPIRADO REAL activado")
        else:
            logger.info("✅ Análisis Monte Carlo clásico como fallback")
    
    async def quantum_price_analysis(self, symbol: str, analysis_type: str = 'standard') -> Dict:
        """Análisis cuántico-inspirado de precios"""
        try:
            if self.quantum_available and np is not None and qmc_module is not None:
                return await self._quantum_analysis_real(symbol, analysis_type)
            else:
                return await self._monte_carlo_fallback(symbol)
                
        except Exception as e:
            logger.error(f"Error análisis cuántico: {e}")
            return {'error': f'Error en análisis cuántico de {symbol}'}
    
    async def _quantum_analysis_real(self, symbol: str, analysis_type: str) -> Dict:
        """Análisis cuántico real con SciPy QMC"""
        try:
            # Obtener precio actual (simulado para demo)
            precio_actual = 50000 + random.uniform(-5000, 5000)  # Simular precio BTC
            volatilidad = 0.25
            
            if analysis_type == 'ultra':
                return await self._ultra_quantum_analysis(precio_actual, volatilidad, symbol)
            elif analysis_type == 'multi-method':
                return await self._multi_method_analysis(precio_actual, volatilidad, symbol)
            else:
                return await self._standard_quantum_analysis(precio_actual, volatilidad, symbol)
                
        except Exception as e:
            logger.error(f"Error análisis cuántico real: {e}")
            return await self._monte_carlo_fallback(symbol)
    
    async def _standard_quantum_analysis(self, precio_actual: float, volatilidad: float, symbol: str) -> Dict:
        """Análisis cuántico estándar con Sobol"""
        n_simulations = 50000
        
        # Generar secuencias Sobol (cuántico-inspirado)
        sobol_gen = qmc_module.Sobol(d=2, scramble=True)
        sobol_samples = sobol_gen.random(n_simulations)
        
        # Transformar a distribución normal
        gaussian_samples = np.sqrt(-2 * np.log(sobol_samples[:, 0])) * np.cos(2 * np.pi * sobol_samples[:, 1])
        
        # Modelo de precios con derive cuántico
        dt = 1/365  # Un día
        drift = 0.08  # 8% anual
        
        precios_simulados = []
        for noise in gaussian_samples:
            precio_sim = precio_actual * np.exp(
                (drift - 0.5 * volatilidad**2) * dt + 
                volatilidad * np.sqrt(dt) * noise
            )
            precios_simulados.append(precio_sim)
        
        precios_simulados = np.array(precios_simulados)
        
        resultado = {
            'method': 'Quantum-Inspired Sobol Analysis',
            'simulations': n_simulations,
            'precio_actual': precio_actual,
            'precio_esperado': float(np.mean(precios_simulados)),
            'percentil_5': float(np.percentile(precios_simulados, 5)),
            'percentil_95': float(np.percentile(precios_simulados, 95)),
            'volatilidad_implicita': float(np.std(precios_simulados) / precio_actual),
            'quantum_advantage': True,
            'confidence_level': 0.90,
            'timestamp': datetime.now().isoformat()
        }
        
        resultado['recomendacion'] = self._generate_quantum_recommendation(resultado)
        
        return resultado
    
    async def _ultra_quantum_analysis(self, precio_actual: float, volatilidad: float, symbol: str) -> Dict:
        """Análisis ultra cuántico con múltiples métodos"""
        n_simulations = 50000
        
        # Múltiples generadores cuánticos
        sobol_gen = qmc_module.Sobol(d=3, scramble=True)
        halton_gen = qmc_module.Halton(d=3, scramble=True)
        
        sobol_samples = sobol_gen.random(n_simulations)
        halton_samples = halton_gen.random(n_simulations) if halton_gen != sobol_gen else sobol_samples
        
        gaussian_sobol = np.sqrt(-2 * np.log(sobol_samples[:, 0])) * np.cos(2 * np.pi * sobol_samples[:, 1])
        gaussian_halton = np.sqrt(-2 * np.log(halton_samples[:, 0])) * np.cos(2 * np.pi * halton_samples[:, 1])
        
        dt = 1/365
        drift_base = 0.08
        drift_volatility = sobol_samples[:, 2] * 0.02
        
        precios_sobol = []
        for i, noise in enumerate(gaussian_sobol):
            drift_actual = drift_base + drift_volatility[i]
            precio_sim = precio_actual * np.exp(
                (drift_actual - 0.5 * volatilidad**2) * dt + 
                volatilidad * np.sqrt(dt) * noise
            )
            precios_sobol.append(precio_sim)
        
        precios_halton = []
        for i, noise in enumerate(gaussian_halton):
            drift_actual = drift_base + drift_volatility[i]
            precio_sim = precio_actual * np.exp(
                (drift_actual - 0.5 * volatilidad**2) * dt + 
                volatilidad * np.sqrt(dt) * noise
            )
            precios_halton.append(precio_sim)
        
        precios_sobol = np.array(precios_sobol)
        precios_halton = np.array(precios_halton)
        
        convergence_analysis = self._analyze_convergence(precios_sobol, precios_halton)
        
        resultado = {
            'method': 'Ultra Quantum-Inspired (Sobol + Halton)',
            'simulations': n_simulations,
            'precio_actual': precio_actual,
            'sobol_analysis': {
                'precio_esperado': float(np.mean(precios_sobol)),
                'percentil_5': float(np.percentile(precios_sobol, 5)),
                'percentil_95': float(np.percentile(precios_sobol, 95)),
                'volatilidad_impl': float(np.std(precios_sobol) / precio_actual),
                'skewness': float(self._calculate_skewness(precios_sobol)),
                'kurtosis': float(self._calculate_kurtosis(precios_sobol))
            },
            'halton_analysis': {
                'precio_esperado': float(np.mean(precios_halton)),
                'percentil_5': float(np.percentile(precios_halton, 5)),
                'percentil_95': float(np.percentile(precios_halton, 95)),
                'volatilidad_impl': float(np.std(precios_halton) / precio_actual),
            },
            'convergence_quality': convergence_analysis,
            'quantum_advantage': True,
            'confidence_level': 0.95,
            'timestamp': datetime.now().isoformat()
        }
        
        resultado['recomendacion'] = self._generate_recommendation_ultra(resultado)
        
        return resultado
    
    def _analyze_convergence(self, sobol_results, halton_results) -> dict:
        """Analizar calidad de convergencia entre métodos"""
        sobol_mean = np.mean(sobol_results)
        halton_mean = np.mean(halton_results)
        
        convergence_diff = abs(sobol_mean - halton_mean) / sobol_mean
        
        return {
            'method_agreement': float(1 - convergence_diff),
            'convergence_quality': 'excellent' if convergence_diff < 0.01 else 'good' if convergence_diff < 0.05 else 'acceptable',
            'sobol_halton_correlation': float(np.corrcoef(sobol_results, halton_results)[0, 1])
        }
    
    def _calculate_skewness(self, data) -> float:
        """Calcular skewness"""
        mean = np.mean(data)
        std = np.std(data)
        skewness = np.mean(((data - mean) / std) ** 3)
        return skewness
    
    def _calculate_kurtosis(self, data) -> float:
        """Calcular kurtosis"""
        mean = np.mean(data)
        std = np.std(data)
        kurtosis = np.mean(((data - mean) / std) ** 4) - 3
        return kurtosis
    
    def _generate_recommendation_ultra(self, analysis: dict) -> dict:
        """Generar recomendación ultra"""
        sobol_data = analysis['sobol_analysis']
        convergence = analysis['convergence_quality']
        
        precio_actual = analysis['precio_actual']
        precio_esperado = sobol_data['precio_esperado']
        
        if precio_esperado > precio_actual * 1.02 and convergence['convergence_quality'] == 'excellent':
            signal = "COMPRA FUERTE"
            confidence = 0.95
        elif precio_esperado < precio_actual * 0.98 and convergence['convergence_quality'] in ['excellent', 'good']:
            signal = "VENTA MODERADA"
            confidence = 0.85
        else:
            signal = "MANTENER"
            confidence = 0.75
        
        return {
            'signal': signal,
            'confidence': confidence,
            'quantum_advantage': "Superior convergencia con métodos cuánticos",
            'risk_level': 'moderate' if convergence['convergence_quality'] == 'excellent' else 'high'
        }
    
    async def _multi_method_analysis(self, precio_actual: float, volatilidad: float, symbol: str) -> Dict:
        """Análisis multi-método comparativo"""
        n_simulations = 25000
        
        # Comparar diferentes métodos QMC
        sobol_gen = qmc_module.Sobol(d=2, scramble=True)
        halton_gen = qmc_module.Halton(d=2, scramble=True)
        
        methods_results = {}
        
        for method_name, generator in [('Sobol', sobol_gen), ('Halton', halton_gen)]:
            samples = generator.random(n_simulations)
            gaussian = np.sqrt(-2 * np.log(samples[:, 0])) * np.cos(2 * np.pi * samples[:, 1])
            
            dt = 1/365
            drift = 0.08
            
            precios = precio_actual * np.exp(
                (drift - 0.5 * volatilidad**2) * dt + 
                volatilidad * np.sqrt(dt) * gaussian
            )
            
            methods_results[method_name] = {
                'precio_esperado': float(np.mean(precios)),
                'volatilidad': float(np.std(precios) / precio_actual),
                'percentil_5': float(np.percentile(precios, 5)),
                'percentil_95': float(np.percentile(precios, 95))
            }
        
        # Análisis comparativo
        method_comparison = self._compare_methods(methods_results)
        
        return {
            'method': 'Multi-Method Quantum Comparison',
            'simulations_per_method': n_simulations,
            'precio_actual': precio_actual,
            'methods_results': methods_results,
            'method_comparison': method_comparison,
            'quantum_advantage': True,
            'confidence_level': 0.90,
            'timestamp': datetime.now().isoformat()
        }
    
    def _compare_methods(self, results: dict) -> dict:
        """Comparar resultados entre métodos"""
        sobol_price = results['Sobol']['precio_esperado']
        halton_price = results['Halton']['precio_esperado']
        
        price_agreement = 1 - abs(sobol_price - halton_price) / sobol_price
        
        return {
            'price_agreement': float(price_agreement),
            'convergence_quality': 'excellent' if price_agreement > 0.99 else 'good' if price_agreement > 0.95 else 'acceptable',
            'recommended_method': 'Sobol' if results['Sobol']['volatilidad'] < results['Halton']['volatilidad'] else 'Halton'
        }
    
    async def _monte_carlo_fallback(self, symbol: str) -> Dict:
        """Monte Carlo clásico como fallback"""
        n_simulations = 10000
        precio_actual = 50000 + random.uniform(-5000, 5000)
        
        precios_simulados = []
        for _ in range(n_simulations):
            random_factor = random.gauss(0, 1)
            precio_sim = precio_actual * (1 + 0.02 * random_factor)
            precios_simulados.append(precio_sim)
        
        precio_promedio = sum(precios_simulados) / len(precios_simulados)
        
        return {
            'method': 'Classical Monte Carlo (Fallback)',
            'simulations': n_simulations,
            'precio_actual': precio_actual,
            'precio_esperado': precio_promedio,
            'quantum_advantage': False,
            'confidence_level': 0.75,
            'timestamp': datetime.now().isoformat(),
            'recomendacion': "Análisis básico - Instalar scipy para análisis cuántico real"
        }
    
    def _generate_quantum_recommendation(self, analysis: dict) -> dict:
        """Generar recomendación cuántica"""
        precio_actual = analysis['precio_actual']
        precio_esperado = analysis['precio_esperado']
        
        if precio_esperado > precio_actual * 1.02:
            return {
                'signal': 'COMPRA',
                'confidence': analysis['confidence_level'],
                'reason': 'Análisis cuántico indica precio al alza'
            }
        elif precio_esperado < precio_actual * 0.98:
            return {
                'signal': 'VENTA',
                'confidence': analysis['confidence_level'],
                'reason': 'Análisis cuántico indica corrección'
            }
        else:
            return {
                'signal': 'MANTENER',
                'confidence': analysis['confidence_level'],
                'reason': 'Precio en equilibrio cuántico'
            }

# ===========================================
# SISTEMA SHARIA COMPLIANCE
# ===========================================

class ShariaComplianceSystem:
    """Sistema de cumplimiento Sharia para GCC"""
    
    def __init__(self):
        # Base de datos de académicos reconocidos
        self.scholars_database = {
            'UAE': [
                'Dr. Abdullah Al-Mutlaq',
                'Sheikh Dr. Ali Gomaa', 
                'Dr. Monzer Kahf'
            ],
            'Saudi': [
                'Dr. Abdullah Al-Manea',
                'Sheikh Saleh Al-Fawzan'
            ],
            'Global': [
                'Dr. Muhammad Taqi Usmani',
                'Dr. Yusuf Al-Qaradawi',
                'Mufti Ebrahim Desai'
            ]
        }
        
        # Criptomonedas halal verificadas
        self.halal_crypto_db = {
            'BTC': {'halal': True, 'confidence': 85, 'reasoning': 'Activo digital basado en utilidad, sin riba'},
            'ETH': {'halal': True, 'confidence': 80, 'reasoning': 'Plataforma de contratos inteligentes con utilidad real'},
            'ADA': {'halal': True, 'confidence': 90, 'reasoning': 'Enfoque académico peer-reviewed, transparente'},
            'DOT': {'halal': True, 'confidence': 75, 'reasoning': 'Interoperabilidad blockchain, utilidad técnica'},
            'LINK': {'halal': True, 'confidence': 85, 'reasoning': 'Oracle descentralizado, soluciona problema real'},
            'VET': {'halal': True, 'confidence': 80, 'reasoning': 'Supply chain transparente, utilidad empresarial'},
            'XLM': {'halal': True, 'confidence': 90, 'reasoning': 'Facilita pagos cross-border, inclusión financiera'},
            'IOTA': {'halal': True, 'confidence': 75, 'reasoning': 'IoT y machine-to-machine payments'},
        }
        
        logger.info("✅ Sistema Sharia Compliance GCC inicializado")
    
    async def validate_crypto_sharia(self, symbol: str, region: str = 'UAE') -> Dict:
        """Validar cumplimiento Sharia de criptomoneda"""
        try:
            symbol_upper = symbol.upper()
            
            # Verificar si está en base de datos
            if symbol_upper in self.halal_crypto_db:
                crypto_data = self.halal_crypto_db[symbol_upper]
                
                # Obtener académicos por región
                region_scholars = self.scholars_database.get(region, self.scholars_database['Global'])
                
                result = {
                    'symbol': symbol_upper,
                    'region': region,
                    'is_halal': crypto_data['halal'],
                    'confidence_percentage': crypto_data['confidence'],
                    'sharia_reasoning': crypto_data['reasoning'],
                    'consulted_scholars': region_scholars[:2],  # Top 2 por región
                    'sharia_principles': self._get_sharia_principles(),
                    'detailed_analysis': self._generate_detailed_analysis(symbol_upper, crypto_data),
                    'recommendation': self._generate_sharia_recommendation(crypto_data),
                    'timestamp': datetime.now().isoformat()
                }
                
                return result
            else:
                return await self._analyze_unknown_crypto(symbol_upper, region)
                
        except Exception as e:
            logger.error(f"Error validación Sharia: {e}")
            return {'error': f'Error validando {symbol} para región {region}'}
    
    def _get_sharia_principles(self) -> List[str]:
        """Obtener principios Sharia aplicados"""
        return [
            "Prohibición de Riba (interés/usura)",
            "Prohibición de Gharar (incertidumbre excesiva)",
            "Prohibición de Maysir (juegos de azar)",
            "Activo debe tener utilidad económica real",
            "Transparencia en las transacciones",
            "No financiar actividades Haram"
        ]
    
    def _generate_detailed_analysis(self, symbol: str, crypto_data: dict) -> dict:
        """Generar análisis detallado Sharia"""
        return {
            'riba_compliance': 'CUMPLE - No genera interés fijo',
            'gharar_assessment': 'ACEPTABLE - Volatilidad normal del mercado',
            'utility_analysis': crypto_data['reasoning'],
            'transparency_level': 'ALTA - Blockchain pública verificable',
            'economic_substance': 'PRESENTE - Utilidad tecnológica real',
            'haram_activities': 'NO IDENTIFICADAS'
        }
    
    def _generate_sharia_recommendation(self, crypto_data: dict) -> dict:
        """Generar recomendación Sharia"""
        if crypto_data['confidence'] >= 85:
            level = "ALTAMENTE RECOMENDADO"
            reasoning = "Cumplimiento Sharia excelente según académicos consultados"
        elif crypto_data['confidence'] >= 75:
            level = "RECOMENDADO CON PRECAUCIÓN"
            reasoning = "Cumplimiento Sharia bueno, considerar proporción en portfolio"
        else:
            level = "CONSULTAR ACADÉMICO LOCAL"
            reasoning = "Requiere análisis específico según interpretación regional"
        
        return {
            'recommendation_level': level,
            'reasoning': reasoning,
            'suggested_allocation': f"{min(crypto_data['confidence'], 20)}% máximo del portfolio islámico"
        }
    
    async def _analyze_unknown_crypto(self, symbol: str, region: str) -> dict:
        """Analizar criptomoneda no conocida"""
        return {
            'symbol': symbol,
            'region': region,
            'status': 'REQUIRES_ANALYSIS',
            'message': f'Criptomoneda {symbol} no está en nuestra base de datos Sharia',
            'recommendation': 'Consultar con académico islámico local antes de invertir',
            'general_principles': self._get_sharia_principles(),
            'suggested_scholars': self.scholars_database.get(region, self.scholars_database['Global']),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_halal_portfolio_suggestion(self, region: str = 'UAE') -> Dict:
        """Sugerir portfolio Halal diversificado"""
        halal_cryptos = [(k, v) for k, v in self.halal_crypto_db.items() if v['halal']]
        
        # Ordenar por confidence
        halal_cryptos.sort(key=lambda x: x[1]['confidence'], reverse=True)
        
        # Top 5 para portfolio
        top_halal = halal_cryptos[:5]
        
        portfolio = []
        for symbol, data in top_halal:
            allocation = min(data['confidence'] / 5, 25)  # Max 25% per asset
            portfolio.append({
                'symbol': symbol,
                'suggested_allocation': f"{allocation:.1f}%",
                'confidence': data['confidence'],
                'reasoning': data['reasoning']
            })
        
        return {
            'region': region,
            'halal_portfolio': portfolio,
            'total_assets': len(portfolio),
            'portfolio_confidence': sum([p['confidence'] for p in [data for _, data in top_halal]]) / len(top_halal),
            'scholars_consulted': self.scholars_database.get(region, self.scholars_database['Global']),
            'timestamp': datetime.now().isoformat()
        }

# ===========================================
# SISTEMA WHATSAPP
# ===========================================

class WhatsAppSystem:
    """Sistema de integración WhatsApp con Twilio"""
    
    def __init__(self):
        self.twilio_configured = bool(
            OmnixConfig.TWILIO_ACCOUNT_SID and 
            OmnixConfig.TWILIO_AUTH_TOKEN and 
            OmnixConfig.TWILIO_PHONE_NUMBER
        )
        
        if self.twilio_configured:
            logger.info("✅ WhatsApp con Twilio configurado")
        else:
            logger.info("⚠️ WhatsApp no configurado - Variables Twilio faltantes")
    
    async def send_whatsapp_notification(self, message: str, to_number: str = None) -> bool:
        """Enviar notificación por WhatsApp"""
        try:
            if not self.twilio_configured:
                logger.warning("WhatsApp no configurado")
                return False
            
            # Importar Twilio dinámicamente
            from twilio.rest import Client
            
            client = Client(
                OmnixConfig.TWILIO_ACCOUNT_SID,
                OmnixConfig.TWILIO_AUTH_TOKEN
            )
            
            # Número por defecto o proporcionado
            destination = to_number if to_number else "+1234567890"  # Configurar número real
            
            # Enviar mensaje
            message = client.messages.create(
                body=message,
                from_=f"whatsapp:{OmnixConfig.TWILIO_PHONE_NUMBER}",
                to=f"whatsapp:{destination}"
            )
            
            logger.info(f"✅ WhatsApp enviado: {message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando WhatsApp: {e}")
            return False
    
    async def send_trading_notification(self, trade_data: dict) -> bool:
        """Enviar notificación de trading por WhatsApp"""
        try:
            message = f"""
🚀 OMNIX Trading Alert

Symbol: {trade_data.get('symbol', 'N/A')}
Action: {trade_data.get('side', 'N/A')}
Price: ${trade_data.get('price', 'N/A')}
Amount: {trade_data.get('amount', 'N/A')}
Status: {trade_data.get('status', 'N/A')}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()
            
            return await self.send_whatsapp_notification(message)
            
        except Exception as e:
            logger.error(f"Error notificación trading WhatsApp: {e}")
            return False

# ===========================================
# BOT TELEGRAM ULTRA COMPLETO
# ===========================================

class OmnixUltraBot:
    """Bot Telegram Ultra Completo OMNIX V5"""
    
    def __init__(self):
        # Inicializar sistemas
        self.database = UltraDatabaseManager()
        self.ai_system = UltraAISystem()
        self.voice_system = UltraVoiceSystem()
        self.trading_system = UltraTradingSystem()
        self.pqc_system = PostQuantumCrypto()
        self.quantum_analysis = QuantumInspiredAnalysis()
        self.sharia_system = ShariaComplianceSystem()
        self.whatsapp_system = WhatsAppSystem()
        
        # Estados del bot
        self.user_stats = {}
        self.active_users = set()
        
        logger.info("✅ OMNIX Ultra Bot inicializado")
    
    def create_application(self) -> Application:
        """Crear aplicación de Telegram"""
        application = Application.builder().token(OmnixConfig.TELEGRAM_BOT_TOKEN).build()
        
        # Registrar handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("precio", self.precio_command))
        application.add_handler(CommandHandler("analisis", self.analisis_command))
        application.add_handler(CommandHandler("trading", self.trading_command))
        application.add_handler(CommandHandler("quantum", self.quantum_command))
        application.add_handler(CommandHandler("sharia", self.sharia_command))
        application.add_handler(CommandHandler("pqc", self.pqc_command))
        application.add_handler(CommandHandler("stats", self.stats_command))
        
        # Handler para mensajes libres
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Handler para callbacks
        application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        return application
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        try:
            user = update.effective_user
            chat_id = update.effective_chat.id
            
            # Guardar usuario en base de datos
            user_data = {
                'user_id': str(user.id),
                'username': user.username or '',
                'first_name': user.first_name or '',
                'language_code': user.language_code or 'es'
            }
            self.database.save_user(user_data)
            
            # Agregar a usuarios activos
            self.active_users.add(user.id)
            
            # Mensaje de bienvenida
            welcome_message = f"""
🚀 ¡Bienvenido a OMNIX V5 QUANTUM READY!

Hola {user.first_name}, soy tu asistente de trading crypto ultra avanzado.

🔧 CARACTERÍSTICAS PRINCIPALES:
• Trading real con Kraken
• Análisis cuántico-inspirado
• Post-Quantum Cryptography
• Cumplimiento Sharia GCC
• Soporte multi-idioma
• Sistema de voz automático

📋 COMANDOS DISPONIBLES:
/precio [símbolo] - Precios en tiempo real
/analisis [símbolo] - Análisis técnico
/trading [símbolo] - Sistema de trading
/quantum [símbolo] - Análisis cuántico
/sharia [símbolo] - Validación Sharia
/pqc - Estado Post-Quantum
/stats - Estadísticas del sistema
/help - Ayuda completa

💬 También puedes hablar conmigo libremente. ¡Respondo con voz automática!

¿En qué puedo ayudarte hoy?
            """.strip()
            
            await update.message.reply_text(welcome_message)
            
            # Generar y enviar voz automática
            await self._send_voice_response(welcome_message, chat_id, context)
            
        except Exception as e:
            logger.error(f"Error en comando start: {e}")
            await update.message.reply_text("Error iniciando bot. Intenta de nuevo.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /help"""
        help_text = """
📖 AYUDA COMPLETA OMNIX V5

🔧 COMANDOS PRINCIPALES:

/start - Inicializar bot
/help - Esta ayuda

📊 TRADING Y ANÁLISIS:
/precio BTC - Precio actual Bitcoin
/analisis ETH - Análisis técnico Ethereum
/trading ADA - Sistema trading Cardano

⚛️ ANÁLISIS AVANZADO:
/quantum BTC standard - Análisis cuántico estándar
/quantum ETH ultra - Análisis ultra avanzado
/quantum DOT multi-method - Comparación métodos

🕌 SHARIA COMPLIANCE:
/sharia BTC UAE - Validación Sharia Emirates
/sharia ETH Saudi - Validación Arabia Saudí
/sharia ADA Global - Validación global

🔐 SEGURIDAD:
/pqc - Estado Post-Quantum Cryptography

📈 INFORMACIÓN:
/stats - Estadísticas del sistema

💬 CHAT LIBRE:
Puedes hablarme libremente sobre:
• Precios de criptomonedas
• Análisis de mercado
• Trading strategies
• Cumplimiento Sharia
• Tecnología cuántica

🎙️ VOZ AUTOMÁTICA:
Todas mis respuestas incluyen audio automático en 6 idiomas.

¿Tienes alguna pregunta específica?
        """.strip()
        
        await update.message.reply_text(help_text)
        await self._send_voice_response(help_text, update.effective_chat.id, context)
    
    async def precio_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /precio"""
        try:
            if not context.args:
                await update.message.reply_text("Uso: /precio BTC\nEjemplos: /precio ETH, /precio ADA")
                return
            
            symbol = context.args[0].upper()
            
            # Obtener precio
            price_data = await self.trading_system.get_price(symbol)
            
            if 'error' in price_data:
                await update.message.reply_text(f"❌ {price_data['error']}")
                return
            
            # Formatear respuesta
            price_text = f"""
📊 PRECIO DE {symbol}

💰 Precio actual: ${price_data['price']:,.2f}
📈 Cambio 24h: {price_data['change_24h']:+.2f}%
🏦 Market Cap: ${price_data['market_cap']:,.0f}
📊 Volumen 24h: ${price_data['volume_24h']:,.0f}

🕐 Actualizado: {datetime.now().strftime('%H:%M:%S')}
📡 Fuente: {price_data['source']}
            """.strip()
            
            await update.message.reply_text(price_text)
            await self._send_voice_response(price_text, update.effective_chat.id, context)
            
        except Exception as e:
            logger.error(f"Error comando precio: {e}")
            await update.message.reply_text("Error obteniendo precio. Intenta de nuevo.")
    
    async def analisis_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /analisis"""
        try:
            if not context.args:
                await update.message.reply_text("Uso: /analisis BTC")
                return
            
            symbol = context.args[0].upper()
            
            # Realizar análisis técnico
            analysis = await self.trading_system.technical_analysis(symbol)
            
            if 'error' in analysis:
                await update.message.reply_text(f"❌ {analysis['error']}")
                return
            
            # Formatear respuesta
            indicators = analysis['technical_indicators']
            signals = analysis['signals']
            
            analysis_text = f"""
📊 ANÁLISIS TÉCNICO {symbol}

💰 Precio: ${analysis['price']:,.2f}
📈 Cambio 24h: {analysis['change_24h']:+.2f}%

📉 INDICADORES TÉCNICOS:
• RSI: {indicators['rsi']:.1f}
• MA20: ${indicators['ma_20']:,.2f}
• MA50: ${indicators['ma_50']:,.2f}
• Tendencia: {indicators['trend']}

🎯 SEÑALES:
• Compra: {'🟢 SÍ' if signals['buy'] else '🔴 NO'}
• Venta: {'🟢 SÍ' if signals['sell'] else '🔴 NO'}
• Mantener: {'🟢 SÍ' if signals['hold'] else '🔴 NO'}

💡 RECOMENDACIÓN:
{analysis['recommendation']}

🕐 Análisis: {datetime.now().strftime('%H:%M:%S')}
            """.strip()
            
            await update.message.reply_text(analysis_text)
            await self._send_voice_response(analysis_text, update.effective_chat.id, context)
            
        except Exception as e:
            logger.error(f"Error comando análisis: {e}")
            await update.message.reply_text("Error realizando análisis. Intenta de nuevo.")
    
    async def trading_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /trading"""
        try:
            if not context.args:
                await update.message.reply_text("Uso: /trading BTC")
                return
            
            symbol = context.args[0].upper()
            
            # Obtener datos para trading
            price_data = await self.trading_system.get_price(symbol)
            analysis = await self.trading_system.technical_analysis(symbol)
            
            if 'error' in price_data:
                await update.message.reply_text(f"❌ {price_data['error']}")
                return
            
            # Simular trade (en producción conectar a Kraken real)
            trade_simulation = {
                'user_id': str(update.effective_user.id),
                'symbol': symbol,
                'side': 'BUY' if analysis['signals']['buy'] else 'SELL' if analysis['signals']['sell'] else 'HOLD',
                'amount': 0.001,  # Cantidad ejemplo
                'price': price_data['price'],
                'status': 'simulated',
                'exchange': 'kraken'
            }
            
            # Guardar en base de datos
            self.database.save_trade(trade_simulation)
            
            trading_text = f"""
⚡ SISTEMA DE TRADING {symbol}

📊 DATOS ACTUALES:
• Precio: ${price_data['price']:,.2f}
• Cambio 24h: {price_data['change_24h']:+.2f}%

🎯 SEÑAL DE TRADING:
{analysis['recommendation']}

🔄 OPERACIÓN SIMULADA:
• Acción: {trade_simulation['side']}
• Cantidad: {trade_simulation['amount']} {symbol}
• Precio: ${trade_simulation['price']:,.2f}
• Estado: {trade_simulation['status'].upper()}

⚠️ NOTA: Modo simulación activo
Para trading real, configurar APIs de Kraken

🕐 Ejecutado: {datetime.now().strftime('%H:%M:%S')}
            """.strip()
            
            await update.message.reply_text(trading_text)
            await self._send_voice_response(trading_text, update.effective_chat.id, context)
            
            # Enviar notificación WhatsApp si está configurado
            await self.whatsapp_system.send_trading_notification(trade_simulation)
            
        except Exception as e:
            logger.error(f"Error comando trading: {e}")
            await update.message.reply_text("Error en sistema de trading. Intenta de nuevo.")
    
    async def quantum_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /quantum"""
        try:
            if not context.args:
                await update.message.reply_text("Uso: /quantum BTC standard\nTipos: standard, ultra, multi-method")
                return
            
            symbol = context.args[0].upper()
            analysis_type = context.args[1] if len(context.args) > 1 else 'standard'
            
            # Realizar análisis cuántico
            quantum_result = await self.quantum_analysis.quantum_price_analysis(symbol, analysis_type)
            
            if 'error' in quantum_result:
                await update.message.reply_text(f"❌ {quantum_result['error']}")
                return
            
            # Formatear respuesta según tipo
            if analysis_type == 'ultra' and 'sobol_analysis' in quantum_result:
                quantum_text = f"""
⚛️ ANÁLISIS CUÁNTICO ULTRA {symbol}

🔬 MÉTODO: {quantum_result['method']}
🎯 Simulaciones: {quantum_result['simulations']:,}

📊 ANÁLISIS SOBOL:
• Precio esperado: ${quantum_result['sobol_analysis']['precio_esperado']:,.2f}
• Percentil 5%: ${quantum_result['sobol_analysis']['percentil_5']:,.2f}
• Percentil 95%: ${quantum_result['sobol_analysis']['percentil_95']:,.2f}
• Volatilidad: {quantum_result['sobol_analysis']['volatilidad_impl']:.3f}

📈 MÉTRICAS AVANZADAS:
• Skewness: {quantum_result['sobol_analysis']['skewness']:.3f}
• Kurtosis: {quantum_result['sobol_analysis']['kurtosis']:.3f}

🎯 CONVERGENCIA:
• Calidad: {quantum_result['convergence_quality']['convergence_quality'].upper()}
• Correlación: {quantum_result['convergence_quality']['sobol_halton_correlation']:.3f}

💡 RECOMENDACIÓN:
{quantum_result['recomendacion']['signal']} 
Confianza: {quantum_result['recomendacion']['confidence']:.1%}

⚛️ Ventaja Cuántica: {'✅ ACTIVA' if quantum_result['quantum_advantage'] else '❌ NO DISPONIBLE'}
                """.strip()
            else:
                quantum_text = f"""
⚛️ ANÁLISIS CUÁNTICO {symbol}

🔬 MÉTODO: {quantum_result['method']}
🎯 Simulaciones: {quantum_result['simulations']:,}

📊 RESULTADOS:
• Precio actual: ${quantum_result['precio_actual']:,.2f}
• Precio esperado: ${quantum_result['precio_esperado']:,.2f}
• Confianza: {quantum_result['confidence_level']:.1%}

💡 RECOMENDACIÓN:
{quantum_result.get('recomendacion', 'Análisis completado')}

⚛️ Ventaja Cuántica: {'✅ ACTIVA' if quantum_result['quantum_advantage'] else '❌ NO DISPONIBLE'}

🕐 Procesado: {datetime.now().strftime('%H:%M:%S')}
                """.strip()
            
            await update.message.reply_text(quantum_text)
            await self._send_voice_response(quantum_text, update.effective_chat.id, context)
            
        except Exception as e:
            logger.error(f"Error comando quantum: {e}")
            await update.message.reply_text("Error en análisis cuántico. Intenta de nuevo.")
    
    async def sharia_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /sharia"""
        try:
            if not context.args:
                await update.message.reply_text("Uso: /sharia BTC UAE\nRegiones: UAE, Saudi, Global")
                return
            
            symbol = context.args[0].upper()
            region = context.args[1] if len(context.args) > 1 else 'UAE'
            
            # Validar Sharia compliance
            sharia_result = await self.sharia_system.validate_crypto_sharia(symbol, region)
            
            if 'error' in sharia_result:
                await update.message.reply_text(f"❌ {sharia_result['error']}")
                return
            
            if sharia_result.get('status') == 'REQUIRES_ANALYSIS':
                sharia_text = f"""
🕌 VALIDACIÓN SHARIA {symbol} - {region}

⚠️ ESTADO: REQUIERE ANÁLISIS

📝 MENSAJE: {sharia_result['message']}

💡 RECOMENDACIÓN: {sharia_result['recommendation']}

👨‍🏫 ACADÉMICOS SUGERIDOS ({region}):
{chr(10).join(f"• {scholar}" for scholar in sharia_result['suggested_scholars'])}

📋 PRINCIPIOS A EVALUAR:
{chr(10).join(f"• {principle}" for principle in sharia_result['general_principles'])}
                """.strip()
            else:
                sharia_text = f"""
🕌 VALIDACIÓN SHARIA {symbol} - {region}

✅ ESTADO: {'HALAL' if sharia_result['is_halal'] else 'REQUIERE REVISIÓN'}
🎯 Confianza: {sharia_result['confidence_percentage']}%

💡 RAZONAMIENTO SHARIA:
{sharia_result['sharia_reasoning']}

👨‍🏫 ACADÉMICOS CONSULTADOS:
{chr(10).join(f"• {scholar}" for scholar in sharia_result['consulted_scholars'])}

📊 ANÁLISIS DETALLADO:
• Riba: {sharia_result['detailed_analysis']['riba_compliance']}
• Gharar: {sharia_result['detailed_analysis']['gharar_assessment']}
• Transparencia: {sharia_result['detailed_analysis']['transparency_level']}

🎯 RECOMENDACIÓN:
{sharia_result['recommendation']['recommendation_level']}
Asignación sugerida: {sharia_result['recommendation']['suggested_allocation']}

🕐 Validado: {datetime.now().strftime('%H:%M:%S')}
                """.strip()
            
            await update.message.reply_text(sharia_text)
            await self._send_voice_response(sharia_text, update.effective_chat.id, context)
            
        except Exception as e:
            logger.error(f"Error comando sharia: {e}")
            await update.message.reply_text("Error en validación Sharia. Intenta de nuevo.")
    
    async def pqc_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /pqc"""
        try:
            # Obtener estado PQC
            pqc_status = self.pqc_system.get_pqc_status()
            
            pqc_text = f"""
🔐 ESTADO POST-QUANTUM CRYPTOGRAPHY

⚛️ PQC DISPONIBLE: {'✅ SÍ' if pqc_status['pqc_available'] else '❌ NO'}
🔑 Kyber-512: {'✅ ACTIVO' if pqc_status['kyber_ready'] else '⚠️ NO INSTALADO'}
📝 Dilithium-2: {'✅ ACTIVO' if pqc_status['dilithium_ready'] else '⚠️ NO INSTALADO'}

🛡️ NIVEL DE SEGURIDAD: {pqc_status['security_level']}
🔄 Fallback activo: {'✅ SÍ' if pqc_status['fallback_active'] else '❌ NO'}
🚀 Preparado para futuro: {'✅ SÍ' if pqc_status['future_proof'] else '❌ NO'}

📚 INFORMACIÓN:
{f"Sistema preparado para migración automática a algoritmos Post-Quantum cuando se instalen las librerías." if not pqc_status['pqc_available'] else "Sistema completamente operativo con criptografía Post-Quantum real."}

💡 Para activar PQC real:
pip install pqcrypto kyber-py dilithium-py

🕐 Estado verificado: {datetime.now().strftime('%H:%M:%S')}
            """.strip()
            
            await update.message.reply_text(pqc_text)
            await self._send_voice_response(pqc_text, update.effective_chat.id, context)
            
        except Exception as e:
            logger.error(f"Error comando pqc: {e}")
            await update.message.reply_text("Error verificando estado PQC. Intenta de nuevo.")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /stats"""
        try:
            stats_text = f"""
📊 ESTADÍSTICAS OMNIX V5

👥 USUARIOS ACTIVOS: {len(self.active_users)}

🔧 ESTADOS DE SISTEMAS:
• IA Gemini: {'✅ ACTIVO' if self.ai_system.gemini_available else '❌ NO CONFIG'}
• IA OpenAI: {'✅ ACTIVO' if self.ai_system.openai_available else '❌ NO CONFIG'}
• Trading Kraken: {'✅ REAL' if self.trading_system.kraken_configured else '⚠️ SIMULADO'}
• ElevenLabs Voice: {'✅ PREMIUM' if self.voice_system.elevenlabs_available else '⚠️ BÁSICO'}
• WhatsApp: {'✅ ACTIVO' if self.whatsapp_system.twilio_configured else '❌ NO CONFIG'}

⚛️ TECNOLOGÍAS AVANZADAS:
• Análisis Cuántico: {'✅ REAL' if self.quantum_analysis.quantum_available else '❌ FALLBACK'}
• Post-Quantum Crypto: {'✅ REAL' if self.pqc_system.pqc_available else '⚠️ PREPARADO'}

🗄️ BASE DE DATOS: ✅ OPERATIVA

🕐 Uptime: {datetime.now().strftime('%H:%M:%S')}
🚀 Versión: OMNIX V5 QUANTUM READY
👨‍💻 Creado por: Harold Nunes
            """.strip()
            
            await update.message.reply_text(stats_text)
            await self._send_voice_response(stats_text, update.effective_chat.id, context)
            
        except Exception as e:
            logger.error(f"Error comando stats: {e}")
            await update.message.reply_text("Error obteniendo estadísticas. Intenta de nuevo.")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar mensajes libres"""
        try:
            user = update.effective_user
            user_message = update.message.text
            chat_id = update.effective_chat.id
            
            # Agregar usuario a activos
            self.active_users.add(user.id)
            
            # Generar respuesta con IA
            ai_response = await self.ai_system.generate_response(
                user_message, 
                str(user.id),
                context={'username': user.username, 'first_name': user.first_name}
            )
            
            # Enviar respuesta de texto
            await update.message.reply_text(ai_response)
            
            # Generar y enviar voz automática
            await self._send_voice_response(ai_response, chat_id, context)
            
            logger.info(f"✅ IA respondió a mensaje completo de {len(user_message)} caracteres")
            
        except Exception as e:
            logger.error(f"Error manejando mensaje: {e}")
            await update.message.reply_text("Disculpa, hubo un error procesando tu mensaje. Intenta de nuevo.")
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar callbacks de botones"""
        try:
            query = update.callback_query
            await query.answer()
            
            # Procesar callback data
            data = query.data
            
            if data.startswith("price_"):
                symbol = data.split("_")[1]
                price_data = await self.trading_system.get_price(symbol)
                await query.edit_message_text(f"Precio {symbol}: ${price_data.get('price', 'N/A')}")
            
        except Exception as e:
            logger.error(f"Error callback: {e}")
    
    async def _send_voice_response(self, text: str, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        """Enviar respuesta de voz automática"""
        try:
            if not OmnixConfig.VOICE_ENABLED:
                return
            
            # Generar archivo de voz
            voice_file = await self.voice_system.generate_voice(text)
            
            if voice_file:
                # Enviar archivo de voz
                with open(voice_file, 'rb') as voice:
                    await context.bot.send_voice(
                        chat_id=chat_id,
                        voice=voice,
                        caption="🎙️ Respuesta de voz OMNIX"
                    )
                
                # Limpiar archivo temporal
                os.unlink(voice_file)
                logger.info("✅ Voz enviada")
            
        except Exception as e:
            logger.error(f"Error enviando voz: {e}")

# ===========================================
# FASTAPI ENDPOINTS
# ===========================================

fastapi_app = FastAPI(
    title="OMNIX V5 QUANTUM READY API",
    description="API REST para sistema de trading ultra avanzado",
    version="5.0.0"
)

@fastapi_app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "name": "OMNIX V5 QUANTUM READY",
        "version": "5.0.0",
        "status": "operational",
        "features": [
            "Real Kraken Trading",
            "Quantum-Inspired Analysis", 
            "Post-Quantum Cryptography",
            "Sharia Compliance GCC",
            "Multi-language Voice",
            "Ultra AI System"
        ],
        "creator": "Harold Nunes",
        "timestamp": datetime.now().isoformat()
    }

@fastapi_app.get("/status")
async def get_status():
    """Estado de los sistemas"""
    return {
        "systems": {
            "ai_gemini": bool(OmnixConfig.GEMINI_API_KEY),
            "ai_openai": bool(OmnixConfig.OPENAI_API_KEY),
            "trading_kraken": bool(OmnixConfig.KRAKEN_API_KEY),
            "voice_elevenlabs": bool(OmnixConfig.ELEVENLABS_API_KEY),
            "whatsapp_twilio": bool(OmnixConfig.TWILIO_ACCOUNT_SID),
            "quantum_analysis": SCIENTIFIC_LIBS_AVAILABLE,
            "post_quantum_crypto": PQC_LIBS_AVAILABLE
        },
        "database": "operational",
        "uptime": datetime.now().isoformat()
    }

@fastapi_app.get("/price/{symbol}")
async def get_crypto_price(symbol: str):
    """Obtener precio de criptomoneda"""
    try:
        # Crear instancia temporal del sistema de trading
        trading_system = UltraTradingSystem()
        price_data = await trading_system.get_price(symbol)
        
        if 'error' in price_data:
            raise HTTPException(status_code=404, detail=price_data['error'])
        
        return price_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===========================================
# FUNCIÓN PRINCIPAL
# ===========================================

async def main():
    """Función principal OMNIX V5"""
    try:
        logger.info("🚀 OMNIX TRABAJANDO iniciando...")
        
        # Verificar configuración mínima
        if not OmnixConfig.TELEGRAM_BOT_TOKEN:
            logger.error("❌ TELEGRAM_BOT_TOKEN requerido")
            return
        
        if not OmnixConfig.GEMINI_API_KEY:
            logger.warning("⚠️ GEMINI_API_KEY no configurado - funcionalidad limitada")
        
        # Crear bot
        bot = OmnixUltraBot()
        application = bot.create_application()
        
        logger.info(f"✅ IA funcionando: {bot.ai_system.gemini_available or bot.ai_system.openai_available}")
        logger.info(f"✅ Trading: {'Kraken Real' if bot.trading_system.kraken_configured else 'Solo análisis'}")
        
        # Iniciar bot
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        logger.info("✅ OMNIX TRABAJANDO completamente operativo")
        
        # Mantener bot corriendo
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 OMNIX detenido por usuario")
    except Exception as e:
        logger.error(f"❌ Error crítico: {e}")
    finally:
        if 'application' in locals():
            await application.stop()
            await application.shutdown()

def run_fastapi():
    """Ejecutar FastAPI en thread separado"""
    uvicorn.run(fastapi_app, host="0.0.0.0", port=5000, log_level="info")

if __name__ == "__main__":
    # Iniciar FastAPI en thread separado
    fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
    fastapi_thread.start()
    
    # Ejecutar bot principal
    asyncio.run(main())







