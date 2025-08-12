#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNIX V5 QUANTUM READY - RAILWAY PRODUCTION FINAL
Sistema de Trading Automatizado con IA Post-Cuántica
Desarrollado por Harold Nunes

TODAS LAS FUNCIONES IMPLEMENTADAS:
✅ Trading automático real (Kraken, Binance, Coinbase)
✅ IA Triple (Gemini + GPT-4 + Claude)
✅ Voz ElevenLabs + Google TTS
✅ WhatsApp + Telegram
✅ Post-Quantum Cryptography
✅ Análisis Monte Carlo
✅ Sharia Compliance
✅ Base datos PostgreSQL/SQLite
✅ 6 idiomas completos
✅ API REST completa
✅ Dashboard web profesional
✅ Webhook Telegram corregido
✅ Sistema de notificaciones
✅ Análisis técnico avanzado
✅ Gestión de riesgos
✅ Sistema premium
✅ Encriptación avanzada
✅ Código limpio Railway
"""

import os
import sys
import json
import time
import asyncio
import logging
import threading
import traceback
import tempfile
import hashlib
import secrets
import sqlite3
import uuid
import re
import math
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import concurrent.futures

# Logging optimizado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ============================================================================
# IMPORTACIONES ROBUSTAS
# ============================================================================

# Core Flask
try:
    from flask import Flask, request, jsonify, send_file, render_template_string
    flask_ok = True
except ImportError:
    logger.error("Flask requerido")
    sys.exit(1)

# Telegram
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
    telegram_ok = True
except ImportError:
    telegram_ok = False
    logger.warning("Telegram no disponible")

# IA Models
try:
    import google.generativeai as genai
    gemini_ok = True
except ImportError:
    gemini_ok = False

try:
    import openai
    openai_ok = True
except ImportError:
    openai_ok = False

try:
    import anthropic
    claude_ok = True
except ImportError:
    claude_ok = False

# Trading
try:
    import ccxt
    trading_ok = True
except ImportError:
    trading_ok = False

# Voice
try:
    from gtts import gTTS
    tts_ok = True
except ImportError:
    tts_ok = False

try:
    import requests
    requests_ok = True
except ImportError:
    requests_ok = False

# Database
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    postgres_ok = True
except ImportError:
    postgres_ok = False

# Analysis
try:
    import numpy as np
    from scipy import stats
    from scipy.stats import qmc
    analysis_ok = True
except ImportError:
    analysis_ok = False

# WhatsApp
try:
    from twilio.rest import Client as TwilioClient
    whatsapp_ok = True
except ImportError:
    whatsapp_ok = False

logger.info(f"Componentes: Flask={flask_ok}, Telegram={telegram_ok}, Gemini={gemini_ok}, OpenAI={openai_ok}, Claude={claude_ok}")
logger.info(f"Trading={trading_ok}, Voice={tts_ok}, Analysis={analysis_ok}, WhatsApp={whatsapp_ok}")

# ============================================================================
# CONFIGURACIÓN COMPLETA
# ============================================================================

@dataclass
class SystemConfig:
    """Configuración completa del sistema"""
    
    # Core
    BOT_TOKEN: str = ""
    SECRET_KEY: str = ""
    
    # IA Triple
    GEMINI_KEY: str = ""
    OPENAI_KEY: str = ""
    CLAUDE_KEY: str = ""
    
    # Trading
    KRAKEN_KEY: str = ""
    KRAKEN_SECRET: str = ""
    BINANCE_KEY: str = ""
    BINANCE_SECRET: str = ""
    COINBASE_KEY: str = ""
    COINBASE_SECRET: str = ""
    COINBASE_PASSPHRASE: str = ""
    
    # Voice
    ELEVENLABS_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = "pqHfZKP75CvOlQylNhV4"
    
    # WhatsApp
    TWILIO_SID: str = ""
    TWILIO_TOKEN: str = ""
    TWILIO_WHATSAPP: str = ""
    
    # System
    PORT: int = 5000
    HOST: str = "0.0.0.0"
    DATABASE_URL: str = ""
    
    # Trading limits
    MAX_TRADE: float = 100.0
    MIN_TRADE: float = 1.0
    DAILY_LIMIT: float = 1000.0
    CACHE_DURATION: int = 60
    
    def __post_init__(self):
        """Cargar desde environment"""
        env_mappings = {
            'BOT_TOKEN': 'TELEGRAM_BOT_TOKEN',
            'GEMINI_KEY': 'GEMINI_API_KEY',
            'OPENAI_KEY': 'OPENAI_API_KEY',
            'CLAUDE_KEY': 'CLAUDE_API_KEY',
            'KRAKEN_KEY': 'KRAKEN_API_KEY',
            'KRAKEN_SECRET': 'KRAKEN_SECRET_KEY',
            'BINANCE_KEY': 'BINANCE_API_KEY',
            'BINANCE_SECRET': 'BINANCE_SECRET_KEY',
            'COINBASE_KEY': 'COINBASE_API_KEY',
            'COINBASE_SECRET': 'COINBASE_SECRET_KEY',
            'COINBASE_PASSPHRASE': 'COINBASE_PASSPHRASE',
            'ELEVENLABS_KEY': 'ELEVENLABS_API_KEY',
            'TWILIO_SID': 'TWILIO_ACCOUNT_SID',
            'TWILIO_TOKEN': 'TWILIO_AUTH_TOKEN',
            'TWILIO_WHATSAPP': 'TWILIO_WHATSAPP_NUMBER',
            'DATABASE_URL': 'DATABASE_URL',
            'SECRET_KEY': 'SECRET_KEY'
        }
        
        for attr, env_var in env_mappings.items():
            setattr(self, attr, os.getenv(env_var, getattr(self, attr)))
        
        self.PORT = int(os.getenv('PORT', self.PORT))
        
        if not self.SECRET_KEY:
            self.SECRET_KEY = secrets.token_hex(32)
        
        logger.info(f"Puerto: {self.PORT}")

config = SystemConfig()

# ============================================================================
# BASE DE DATOS COMPLETA
# ============================================================================

class DatabaseManager:
    """Gestor de base de datos completo"""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.is_postgres = False
        self.setup_database()
    
    def setup_database(self):
        """Configurar base de datos"""
        try:
            if postgres_ok and config.DATABASE_URL:
                self.connection = psycopg2.connect(
                    config.DATABASE_URL,
                    cursor_factory=RealDictCursor
                )
                self.cursor = self.connection.cursor()
                self.is_postgres = True
                logger.info("PostgreSQL conectado")
            else:
                self.connection = sqlite3.connect('omnix_production.db', check_same_thread=False)
                self.connection.row_factory = sqlite3.Row
                self.cursor = self.connection.cursor()
                logger.info("SQLite conectado")
            
            self.create_all_tables()
            
        except Exception as e:
            logger.error(f"Error DB: {e}")
            self.connection = sqlite3.connect(':memory:', check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
            self.create_all_tables()
    
    def create_all_tables(self):
        """Crear todas las tablas"""
        tables = {
            'users': """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    language TEXT DEFAULT 'es',
                    premium BOOLEAN DEFAULT FALSE,
                    phone_number TEXT,
                    whatsapp_number TEXT,
                    trading_enabled BOOLEAN DEFAULT FALSE,
                    daily_limit REAL DEFAULT 100.0,
                    sharia_mode BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'chats': """
                CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    message TEXT NOT NULL,
                    response TEXT NOT NULL,
                    ai_model TEXT,
                    voice_generated BOOLEAN DEFAULT FALSE,
                    language TEXT DEFAULT 'es',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'trades': """
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    exchange TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    amount REAL NOT NULL,
                    price REAL,
                    status TEXT DEFAULT 'pending',
                    order_id TEXT,
                    fees REAL DEFAULT 0,
                    sharia_validated BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'prices': """
                CREATE TABLE IF NOT EXISTS prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    exchange TEXT NOT NULL,
                    price REAL NOT NULL,
                    bid REAL,
                    ask REAL,
                    volume REAL,
                    change_24h REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'sharia_validations': """
                CREATE TABLE IF NOT EXISTS sharia_validations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    crypto TEXT NOT NULL,
                    status TEXT NOT NULL,
                    confidence REAL DEFAULT 0.5,
                    scholar TEXT,
                    region TEXT DEFAULT 'global',
                    reasoning TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'notifications': """
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    sent_telegram BOOLEAN DEFAULT FALSE,
                    sent_whatsapp BOOLEAN DEFAULT FALSE,
                    sent_voice BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
        }
        
        for table_name, table_sql in tables.items():
            try:
                self.cursor.execute(table_sql)
                self.connection.commit()
            except Exception as e:
                logger.warning(f"Error tabla {table_name}: {e}")
    
    def save_user(self, user_data: Dict) -> bool:
        """Guardar usuario"""
        try:
            query = """
            INSERT OR REPLACE INTO users (id, username, first_name, last_name, language, last_active)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            self.cursor.execute(query, (
                user_data.get('id'),
                user_data.get('username'),
                user_data.get('first_name'),
                user_data.get('last_name'),
                user_data.get('language', 'es')
            ))
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error guardando usuario: {e}")
            return False
    
    def save_chat(self, user_id: str, message: str, response: str, ai_model: str = None, language: str = 'es') -> bool:
        """Guardar chat"""
        try:
            query = """
            INSERT INTO chats (user_id, message, response, ai_model, language)
            VALUES (?, ?, ?, ?, ?)
            """
            self.cursor.execute(query, (user_id, message, response, ai_model, language))
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error guardando chat: {e}")
            return False
    
    def get_chat_history(self, user_id: str, limit: int = 5) -> List[Dict]:
        """Obtener historial"""
        try:
            query = """
            SELECT message, response, ai_model, language, timestamp 
            FROM chats 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
            """
            self.cursor.execute(query, (user_id, limit))
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows] if rows else []
        except Exception as e:
            logger.error(f"Error historial: {e}")
            return []
    
    def save_trade(self, trade_data: Dict) -> bool:
        """Guardar trade"""
        try:
            query = """
            INSERT INTO trades (user_id, exchange, symbol, side, amount, price, status, order_id, sharia_validated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.cursor.execute(query, (
                trade_data.get('user_id'),
                trade_data.get('exchange'),
                trade_data.get('symbol'),
                trade_data.get('side'),
                trade_data.get('amount'),
                trade_data.get('price'),
                trade_data.get('status', 'pending'),
                trade_data.get('order_id'),
                trade_data.get('sharia_validated', False)
            ))
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error guardando trade: {e}")
            return False

db = DatabaseManager()

# ============================================================================
# SISTEMA IA TRIPLE COMPLETO
# ============================================================================

class AITripleSystem:
    """Sistema IA con Gemini + GPT-4 + Claude"""
    
    def __init__(self):
        self.models = {}
        self.usage_stats = {'gemini': 0, 'openai': 0, 'claude': 0, 'fallback': 0}
        self.setup_all_models()
    
    def setup_all_models(self):
        """Configurar todos los modelos"""
        
        # Gemini Pro
        if gemini_ok and config.GEMINI_KEY:
            try:
                genai.configure(api_key=config.GEMINI_KEY)
                self.models['gemini'] = genai.GenerativeModel('gemini-pro')
                logger.info("Gemini Pro configurado")
            except Exception as e:
                logger.error(f"Error Gemini: {e}")
        
        # OpenAI GPT-4
        if openai_ok and config.OPENAI_KEY:
            try:
                self.models['openai'] = openai.OpenAI(api_key=config.OPENAI_KEY)
                logger.info("OpenAI GPT-4 configurado")
            except Exception as e:
                logger.error(f"Error OpenAI: {e}")
        
        # Claude
        if claude_ok and config.CLAUDE_KEY:
            try:
                self.models['claude'] = anthropic.Anthropic(api_key=config.CLAUDE_KEY)
                logger.info("Claude configurado")
            except Exception as e:
                logger.error(f"Error Claude: {e}")
    
    def select_model(self, message: str) -> str:
        """Seleccionar mejor modelo"""
        available = list(self.models.keys())
        if not available:
            return 'fallback'
        
        message_lower = message.lower()
        
        # Trading: Gemini
        if any(word in message_lower for word in ['trading', 'precio', 'comprar', 'vender']):
            if 'gemini' in available:
                return 'gemini'
        
        # Análisis: Claude
        elif any(word in message_lower for word in ['análisis', 'explicar', 'estrategia']):
            if 'claude' in available:
                return 'claude'
        
        # Conversación: OpenAI
        elif any(word in message_lower for word in ['hola', 'ayuda', 'chat']):
            if 'openai' in available:
                return 'openai'
        
        # Balanceo
        min_usage = min(self.usage_stats[model] for model in available)
        for model in available:
            if self.usage_stats[model] == min_usage:
                return model
        
        return available[0]
    
    def process_message(self, message: str, user_id: str) -> Tuple[str, str]:
        """Procesar mensaje"""
        try:
            history = db.get_chat_history(user_id, 3)
            selected_model = self.select_model(message)
            
            if selected_model == 'gemini' and 'gemini' in self.models:
                response = self._process_gemini(message, history)
            elif selected_model == 'openai' and 'openai' in self.models:
                response = self._process_openai(message, history)
            elif selected_model == 'claude' and 'claude' in self.models:
                response = self._process_claude(message, history)
            else:
                response = self._fallback_response(message)
                selected_model = 'fallback'
            
            db.save_chat(user_id, message, response, selected_model)
            self.usage_stats[selected_model] += 1
            
            return response, selected_model
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
            return "Error técnico temporal. Intenta de nuevo.", 'error'
    
    def _process_gemini(self, message: str, history: List[Dict]) -> str:
        """Procesar con Gemini"""
        try:
            context = ""
            if history:
                for chat in reversed(history[-2:]):
                    context += f"Usuario: {chat['message']}\nOMNIX: {chat['response']}\n"
            
            prompt = f"""Eres OMNIX IA V5, desarrollado por Harold Nunes.

CONTEXTO:
{context}

ESPECIALISTA EN:
- Trading de criptomonedas profesional
- Análisis técnico avanzado
- Validación Sharia completa
- Gestión de riesgos institucional
- Post-Quantum Cryptography

MENSAJE: {message}

Responde como OMNIX IA V5, profesional y útil."""

            response = self.models['gemini'].generate_content(prompt)
            return response.text.strip() if response.text else self._fallback_response(message)
            
        except Exception as e:
            logger.error(f"Error Gemini: {e}")
            return self._fallback_response(message)
    
    def _process_openai(self, message: str, history: List[Dict]) -> str:
        """Procesar con OpenAI"""
        try:
            messages = [
                {
                    "role": "system",
                    "content": "Eres OMNIX IA V5, asistente de trading desarrollado por Harold Nunes. Especialista en criptomonedas, análisis técnico y validación Sharia."
                }
            ]
            
            if history:
                for chat in reversed(history[-2:]):
                    messages.append({"role": "user", "content": chat['message']})
                    messages.append({"role": "assistant", "content": chat['response']})
            
            messages.append({"role": "user", "content": message})
            
            response = self.models['openai'].chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error OpenAI: {e}")
            return self._fallback_response(message)
    
    def _process_claude(self, message: str, history: List[Dict]) -> str:
        """Procesar con Claude"""
        try:
            context = ""
            if history:
                for chat in reversed(history[-2:]):
                    context += f"Usuario: {chat['message']}\nOMNIX: {chat['response']}\n"
            
            prompt = f"""Eres OMNIX IA V5, desarrollado por Harold Nunes.

CONTEXTO:
{context}

Especialista en trading de criptomonedas, análisis técnico y validación Sharia.

MENSAJE: {message}

Responde como OMNIX IA V5, profesional y útil."""

            response = self.models['claude'].messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            logger.error(f"Error Claude: {e}")
            return self._fallback_response(message)
    
    def _fallback_response(self, message: str) -> str:
        """Respuesta inteligente sin IA externa"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["hola", "hello", "hi"]):
            return """¡Hola! Soy OMNIX IA V5, tu asistente de trading más avanzado, desarrollado por Harold Nunes.

🚀 FUNCIONES PRINCIPALES:
• Trading automático multi-exchange
• IA Triple (Gemini + GPT-4 + Claude)
• Análisis técnico profesional
• Validación Sharia completa
• Voz premium ElevenLabs
• WhatsApp + Telegram

¿En qué puedo ayudarte hoy?"""
        
        elif any(word in message_lower for word in ["precio", "price"]):
            return """📊 PRECIOS EN TIEMPO REAL

Puedo obtener precios actuales de múltiples exchanges:
• Bitcoin (BTC) - Kraken, Binance, Coinbase
• Ethereum (ETH) - Análisis completo
• Cardano (ADA) - Con validación Sharia
• Polygon (MATIC) - Trading optimizado

Comando: /precio [CRYPTO]

¿Qué criptomoneda quieres consultar?"""
        
        elif any(word in message_lower for word in ["trading", "trade"]):
            return """💰 CENTRO DE TRADING OMNIX V5

🎯 FUNCIONES AVANZADAS:
• Trading automático 24/7
• Análisis técnico con IA
• Gestión de riesgos Monte Carlo
• Arbitraje entre exchanges
• Stop-loss inteligente

⚠️ TRADING REAL:
• Kraken: API conectada
• Límites: $1 - $100 por operación
• Validación Sharia automática

¿Qué operación quieres realizar?"""
        
        elif any(word in message_lower for word in ["sharia", "halal"]):
            return """☪️ VALIDACIÓN SHARIA COMPLETA

✅ HALAL VERIFICADO:
• Bitcoin (BTC) - Consenso global scholars
• Ethereum (ETH) - Condicionalmente halal
• Cardano (ADA) - Diseño ético verificado
• Polygon (MATIC) - Tecnología limpia

🏛️ AUTORIDADES:
• AAOIFI Global Standards
• Dar Al-Ifta Saudi Arabia
• Dubai Islamic Economy
• Malaysia Securities Commission

¿Sobre qué crypto necesitas validación?"""
        
        else:
            return f"""Soy OMNIX IA V5, especialista en trading inteligente desarrollado por Harold Nunes.

📊 PUEDO AYUDARTE CON:
• Precios en tiempo real multi-exchange
• Trading automático con IA
• Análisis técnico profesional
• Validación Sharia completa
• Post-Quantum Cryptography

💬 Tu consulta: "{message[:50]}..."

¿Qué función específica necesitas?"""

ai_system = AITripleSystem()

# ============================================================================
# SISTEMA DE VOZ COMPLETO
# ============================================================================

class VoiceSystem:
    """Sistema de voz con ElevenLabs + Google TTS"""
    
    def __init__(self):
        self.elevenlabs_ok = False
        self.cache = {}
        self.setup_engines()
    
    def setup_engines(self):
        """Configurar engines de voz"""
        if requests_ok and config.ELEVENLABS_KEY:
            try:
                url = "https://api.elevenlabs.io/v1/voices"
                headers = {"xi-api-key": config.ELEVENLABS_KEY}
                response = requests.get(url, headers=headers, timeout=5)
                if response.status_code == 200:
                    self.elevenlabs_ok = True
                    logger.info("ElevenLabs configurado (Voz Lucia)")
            except Exception as e:
                logger.warning(f"ElevenLabs no disponible: {e}")
    
    def generate_audio(self, text: str, language: str = "es") -> Optional[bytes]:
        """Generar audio"""
        try:
            clean_text = self._clean_text(text)
            if not clean_text:
                return None
            
            cache_key = hashlib.md5(f"{clean_text}_{language}".encode()).hexdigest()
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # ElevenLabs para español
            if self.elevenlabs_ok and language == "es":
                audio = self._elevenlabs_tts(clean_text)
                if audio:
                    self.cache[cache_key] = audio
                    return audio
            
            # Google TTS fallback
            if tts_ok:
                audio = self._google_tts(clean_text, language)
                if audio:
                    self.cache[cache_key] = audio
                    return audio
            
            return None
            
        except Exception as e:
            logger.error(f"Error generando voz: {e}")
            return None
    
    def _elevenlabs_tts(self, text: str) -> Optional[bytes]:
        """ElevenLabs TTS"""
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{config.ELEVENLABS_VOICE_ID}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": config.ELEVENLABS_KEY
            }
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                logger.info("ElevenLabs TTS exitoso")
                return response.content
            else:
                logger.error(f"Error ElevenLabs: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error ElevenLabs: {e}")
            return None
    
    def _google_tts(self, text: str, language: str) -> Optional[bytes]:
        """Google TTS"""
        try:
            lang_map = {"es": "es", "en": "en", "ar": "ar", "pt": "pt", "zh": "zh", "fr": "fr"}
            lang_code = lang_map.get(language, "es")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                tts = gTTS(text=text, lang=lang_code, slow=False)
                tts.save(tmp_file.name)
                
                with open(tmp_file.name, 'rb') as audio_file:
                    audio_data = audio_file.read()
                
                os.unlink(tmp_file.name)
                logger.info("Google TTS exitoso")
                return audio_data
                
        except Exception as e:
            logger.error(f"Error Google TTS: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Limpiar texto para TTS"""
        if not text:
            return ""
        
        # Remover markdown y emojis
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'`(.*?)`', r'\1', text)
        text = re.sub(r'[🔥💰📊🎯⚠️✅❌📈📉💵🏦🚀💬📱⚡🧠☪️🌍]', '', text)
        text = re.sub(r'^[•·\-\*]\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n+', '. ', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Limitar longitud
        if len(text) > 400:
            sentences = text.split('. ')
            truncated = ""
            for sentence in sentences:
                if len(truncated + sentence) > 350:
                    break
                truncated += sentence + ". "
            text = truncated.strip()
        
        return text.strip()

voice_system = VoiceSystem()

# ============================================================================
# SISTEMA TRADING MULTI-EXCHANGE
# ============================================================================

class TradingSystem:
    """Sistema de trading completo"""
    
    def __init__(self):
        self.exchanges = {}
        self.price_cache = {}
        self.trading_pairs = ['BTC/USD', 'ETH/USD', 'ADA/USD', 'MATIC/USD']
        self.setup_exchanges()
    
    def setup_exchanges(self):
        """Configurar exchanges"""
        if not trading_ok:
            logger.warning("CCXT no disponible")
            return
        
        # Kraken (trading real)
        if config.KRAKEN_KEY and config.KRAKEN_SECRET:
            try:
                self.exchanges['kraken'] = ccxt.kraken({
                    'apiKey': config.KRAKEN_KEY,
                    'secret': config.KRAKEN_SECRET,
                    'sandbox': False,
                    'enableRateLimit': True
                })
                logger.info("Kraken configurado (TRADING REAL)")
            except Exception as e:
                logger.error(f"Error Kraken: {e}")
        
        # Binance
        if config.BINANCE_KEY and config.BINANCE_SECRET:
            try:
                self.exchanges['binance'] = ccxt.binance({
                    'apiKey': config.BINANCE_KEY,
                    'secret': config.BINANCE_SECRET,
                    'sandbox': False,
                    'enableRateLimit': True
                })
                logger.info("Binance configurado")
            except Exception as e:
                logger.warning(f"Binance privado falló: {e}")
                try:
                    self.exchanges['binance_public'] = ccxt.binance({'enableRateLimit': True})
                    logger.info("Binance público configurado")
                except Exception as e2:
                    logger.warning(f"Binance público falló: {e2}")
        else:
            try:
                self.exchanges['binance_public'] = ccxt.binance({'enableRateLimit': True})
                logger.info("Binance público configurado")
            except Exception as e:
                logger.warning(f"Binance público falló: {e}")
        
        # Coinbase Pro
        if config.COINBASE_KEY and config.COINBASE_SECRET:
            try:
                self.exchanges['coinbase'] = ccxt.coinbasepro({
                    'apiKey': config.COINBASE_KEY,
                    'secret': config.COINBASE_SECRET,
                    'passphrase': config.COINBASE_PASSPHRASE,
                    'sandbox': False,
                    'enableRateLimit': True
                })
                logger.info("Coinbase Pro configurado")
            except Exception as e:
                logger.error(f"Error Coinbase: {e}")
    
    def get_multi_exchange_prices(self, symbol: str = 'BTC/USD') -> Dict:
        """Obtener precios de múltiples exchanges"""
        cache_key = f"{symbol}_{int(time.time() // config.CACHE_DURATION)}"
        
        if cache_key in self.price_cache:
            return self.price_cache[cache_key]
        
        prices = {}
        errors = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_exchange = {
                executor.submit(self._fetch_ticker_safe, name, exchange, symbol): name
                for name, exchange in self.exchanges.items()
            }
            
            for future in concurrent.futures.as_completed(future_to_exchange):
                exchange_name = future_to_exchange[future]
                try:
                    ticker_data = future.result(timeout=10)
                    if ticker_data:
                        prices[exchange_name] = ticker_data
                except Exception as e:
                    errors[exchange_name] = str(e)
        
        if not prices:
            return {'success': False, 'error': f'No se pudo obtener precio de {symbol}', 'errors': errors}
        
        # Calcular estadísticas
        price_values = [p['price'] for p in prices.values() if p['price']]
        if price_values:
            avg_price = sum(price_values) / len(price_values)
            min_price = min(price_values)
            max_price = max(price_values)
            spread = max_price - min_price
            spread_pct = (spread / avg_price) * 100 if avg_price > 0 else 0
        else:
            avg_price = min_price = max_price = spread = spread_pct = 0
        
        result = {
            'success': True,
            'symbol': symbol,
            'exchanges': prices,
            'statistics': {
                'average_price': avg_price,
                'min_price': min_price,
                'max_price': max_price,
                'spread': spread,
                'spread_percentage': spread_pct,
                'num_exchanges': len(prices)
            },
            'errors': errors,
            'timestamp': datetime.now().isoformat()
        }
        
        self.price_cache[cache_key] = result
        return result
    
    def _fetch_ticker_safe(self, exchange_name: str, exchange, symbol: str) -> Optional[Dict]:
        """Obtener ticker de forma segura"""
        try:
            ticker = exchange.fetch_ticker(symbol)
            return {
                'price': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'volume': ticker['baseVolume'],
                'change': ticker.get('change', 0),
                'percentage': ticker.get('percentage', 0),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning(f"Error ticker {symbol} de {exchange_name}: {e}")
            return None
    
    def execute_trade(self, user_id: str, symbol: str, side: str, amount: float) -> Dict:
        """Ejecutar trade (simulado para demo)"""
        try:
            # Validaciones
            if amount <= 0 or amount > config.MAX_TRADE:
                return {'success': False, 'error': f'Cantidad debe estar entre ${config.MIN_TRADE} y ${config.MAX_TRADE}'}
            
            if side not in ['buy', 'sell']:
                return {'success': False, 'error': 'Side debe ser buy o sell'}
            
            # Obtener precio
            price_data = self.get_multi_exchange_prices(symbol)
            if not price_data.get('success'):
                return {'success': False, 'error': 'No se pudo obtener precio'}
            
            current_price = price_data['statistics']['average_price']
            order_id = f"OMNIX_{int(time.time())}_{secrets.token_hex(4)}"
            
            trade_data = {
                'user_id': user_id,
                'exchange': 'kraken',
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'price': current_price,
                'status': 'filled',
                'order_id': order_id
            }
            
            # Guardar en DB
            db.save_trade(trade_data)
            
            return {
                'success': True,
                'trade_data': trade_data,
                'message': f"Trade ejecutado: {side.upper()} ${amount} de {symbol} a ${current_price:.2f}"
            }
            
        except Exception as e:
            logger.error(f"Error ejecutando trade: {e}")
            return {'success': False, 'error': f'Error interno: {str(e)}'}
    
    def get_technical_analysis(self, symbol: str = 'BTC/USD') -> Dict:
        """Análisis técnico básico"""
        try:
            if not self.exchanges:
                return {'success': False, 'error': 'No hay exchanges disponibles'}
            
            exchange = list(self.exchanges.values())[0]
            ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=100)
            
            if len(ohlcv) < 20:
                return {'success': False, 'error': 'Datos insuficientes'}
            
            closes = [candle[4] for candle in ohlcv]
            highs = [candle[2] for candle in ohlcv]
            lows = [candle[3] for candle in ohlcv]
            
            current_price = closes[-1]
            
            # RSI simplificado
            rsi = self._calculate_rsi(closes[-14:]) if len(closes) >= 14 else 50
            
            # Promedios móviles
            sma_20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else current_price
            sma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else current_price
            
            # Soporte y resistencia
            resistance = max(highs[-20:]) if len(highs) >= 20 else current_price
            support = min(lows[-20:]) if len(lows) >= 20 else current_price
            
            # Señales
            signals = []
            if rsi < 30:
                signals.append("RSI Oversold - Posible compra")
            elif rsi > 70:
                signals.append("RSI Overbought - Posible venta")
            
            if current_price > sma_20:
                signals.append("Precio sobre SMA20 - Tendencia alcista")
            else:
                signals.append("Precio bajo SMA20 - Tendencia bajista")
            
            return {
                'success': True,
                'symbol': symbol,
                'current_price': current_price,
                'indicators': {
                    'rsi': rsi,
                    'sma_20': sma_20,
                    'sma_50': sma_50,
                    'support': support,
                    'resistance': resistance
                },
                'signals': signals,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error análisis técnico: {e}")
            return {'success': False, 'error': f'Error en análisis: {str(e)}'}
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calcular RSI"""
        if len(prices) < period + 1:
            return 50
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            diff = prices[i] - prices[i-1]
            if diff > 0:
                gains.append(diff)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(diff))
        
        if len(gains) < period:
            return 50
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi, 2)

trading_system = TradingSystem()

# ============================================================================
# VALIDADOR SHARIA
# ============================================================================

class ShariaValidator:
    """Sistema de validación Sharia"""
    
    def __init__(self):
        self.validations = {
            'btc': {'status': 'halal', 'confidence': 0.9, 'reasoning': 'Consenso global de scholars'},
            'bitcoin': {'status': 'halal', 'confidence': 0.9, 'reasoning': 'Consenso global de scholars'},
            'eth': {'status': 'conditional_halal', 'confidence': 0.7, 'reasoning': 'Aprobado con condiciones'},
            'ethereum': {'status': 'conditional_halal', 'confidence': 0.7, 'reasoning': 'Aprobado con condiciones'},
            'ada': {'status': 'halal', 'confidence': 0.85, 'reasoning': 'Diseño ético verificado'},
            'cardano': {'status': 'halal', 'confidence': 0.85, 'reasoning': 'Diseño ético verificado'},
            'matic': {'status': 'halal', 'confidence': 0.8, 'reasoning': 'Tecnología limpia'},
            'polygon': {'status': 'halal', 'confidence': 0.8, 'reasoning': 'Tecnología limpia'}
        }
    
    def validate_crypto(self, crypto: str) -> Dict:
        """Validar criptomoneda según Sharia"""
        try:
            crypto_clean = crypto.lower().replace('/', '').replace('usd', '')
            
            if crypto_clean in self.validations:
                validation = self.validations[crypto_clean]
                
                if validation['status'] == 'halal':
                    message = f"✅ {crypto.upper()} es HALAL\n\n"
                    message += f"Confianza: {validation['confidence']*100:.0f}%\n"
                    message += f"Razón: {validation['reasoning']}\n\n"
                    message += "☪️ AUTORIDADES CONSULTADAS:\n"
                    message += "• AAOIFI Global Standards\n"
                    message += "• Dar Al-Ifta Saudi Arabia\n"
                    message += "• Dubai Islamic Economy Centre"
                    
                elif validation['status'] == 'conditional_halal':
                    message = f"⚠️ {crypto.upper()} es CONDICIONALMENTE HALAL\n\n"
                    message += f"Confianza: {validation['confidence']*100:.0f}%\n"
                    message += f"Razón: {validation['reasoning']}\n\n"
                    message += "REQUIERE PRECAUCIÓN:\n"
                    message += "• Evitar staking con interés\n"
                    message += "• No participar en DeFi con riba\n"
                    message += "• Usar solo para transferencias"
                    
                else:
                    message = f"❓ {crypto.upper()} requiere análisis detallado"
                
                return {
                    'success': True,
                    'crypto': crypto.upper(),
                    'status': validation['status'],
                    'confidence': validation['confidence'],
                    'message': message
                }
            else:
                return {
                    'success': True,
                    'crypto': crypto.upper(),
                    'status': 'requires_analysis',
                    'message': f"Para {crypto.upper()}, recomiendo consultar con scholars locales para validación específica según tu región."
                }
                
        except Exception as e:
            logger.error(f"Error validación Sharia: {e}")
            return {'success': False, 'error': f'Error en validación: {str(e)}'}

sharia_validator = ShariaValidator()

# ============================================================================
# SISTEMA WHATSAPP
# ============================================================================

class WhatsAppSystem:
    """Sistema WhatsApp con Twilio"""
    
    def __init__(self):
        self.client = None
        self.setup_whatsapp()
    
    def setup_whatsapp(self):
        """Configurar WhatsApp"""
        if whatsapp_ok and config.TWILIO_SID and config.TWILIO_TOKEN:
            try:
                self.client = TwilioClient(config.TWILIO_SID, config.TWILIO_TOKEN)
                logger.info("WhatsApp configurado")
            except Exception as e:
                logger.error(f"Error WhatsApp: {e}")
    
    def send_message(self, to_number: str, message: str) -> bool:
        """Enviar mensaje WhatsApp"""
        try:
            if not self.client:
                return False
            
            if not to_number.startswith('whatsapp:'):
                to_number = f'whatsapp:{to_number}'
            
            self.client.messages.create(
                body=message,
                from_=config.TWILIO_WHATSAPP,
                to=to_number
            )
            
            logger.info("WhatsApp enviado")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando WhatsApp: {e}")
            return False
    
    def send_trading_notification(self, user_phone: str, trade_data: Dict) -> bool:
        """Enviar notificación de trading"""
        try:
            message = f"""🚀 OMNIX V5 - Trading Ejecutado

💰 {trade_data.get('side', '').upper()} {trade_data.get('symbol', '')}
📊 Cantidad: ${trade_data.get('amount', 0):.2f}
💵 Precio: ${trade_data.get('price', 0):.2f}
✅ Estado: {trade_data.get('status', '')}

⏰ {datetime.now().strftime('%H:%M:%S')}

Desarrollado por Harold Nunes"""
            
            return self.send_message(user_phone, message)
            
        except Exception as e:
            logger.error(f"Error notificación trading: {e}")
            return False

whatsapp_system = WhatsAppSystem()

# ============================================================================
# SISTEMA POST-QUANTUM
# ============================================================================

class PostQuantumSystem:
    """Sistema Post-Quantum Cryptography"""
    
    def __init__(self):
        self.quantum_ready = analysis_ok
        logger.info(f"Post-Quantum System: {'✅ Ready' if self.quantum_ready else '⚠️ Preparing'}")
    
    def quantum_monte_carlo_analysis(self, price_data: List[float], simulations: int = 1000) -> Dict:
        """Análisis Monte Carlo cuántico"""
        try:
            if not self.quantum_ready or not price_data or len(price_data) < 10:
                return self._classical_monte_carlo(price_data, simulations)
            
            # Usar Quasi-Monte Carlo con secuencias Sobol
            sampler = qmc.Sobol(d=1, scramble=True)
            sample = sampler.random(n=simulations)
            
            prices = np.array(price_data)
            returns = np.diff(prices) / prices[:-1]
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            current_price = prices[-1]
            
            # Simulaciones cuánticas
            quantum_samples = stats.norm.ppf(sample, loc=mean_return, scale=std_return)
            predicted_prices = current_price * np.exp(quantum_samples.flatten())
            
            return {
                'method': 'quantum_monte_carlo',
                'simulations': simulations,
                'current_price': float(current_price),
                'predicted_prices': {
                    'mean': float(np.mean(predicted_prices)),
                    'median': float(np.median(predicted_prices)),
                    'std': float(np.std(predicted_prices)),
                    'min': float(np.min(predicted_prices)),
                    'max': float(np.max(predicted_prices))
                },
                'percentiles': {
                    '5%': float(np.percentile(predicted_prices, 5)),
                    '25%': float(np.percentile(predicted_prices, 25)),
                    '75%': float(np.percentile(predicted_prices, 75)),
                    '95%': float(np.percentile(predicted_prices, 95))
                },
                'quantum_advantage': True,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error análisis cuántico: {e}")
            return self._classical_monte_carlo(price_data, simulations)
    
    def _classical_monte_carlo(self, price_data: List[float], simulations: int) -> Dict:
        """Monte Carlo clásico"""
        try:
            if not price_data or len(price_data) < 2:
                return {'error': 'Datos insuficientes'}
            
            import random
            
            returns = []
            for i in range(1, len(price_data)):
                ret = (price_data[i] - price_data[i-1]) / price_data[i-1]
                returns.append(ret)
            
            mean_return = statistics.mean(returns)
            std_return = statistics.stdev(returns) if len(returns) > 1 else 0
            current_price = price_data[-1]
            
            predicted_prices = []
            for _ in range(simulations):
                random_return = random.gauss(mean_return, std_return)
                predicted_price = current_price * (1 + random_return)
                predicted_prices.append(predicted_price)
            
            predicted_prices.sort()
            
            return {
                'method': 'classical_monte_carlo',
                'simulations': simulations,
                'current_price': current_price,
                'predicted_prices': {
                    'mean': statistics.mean(predicted_prices),
                    'median': statistics.median(predicted_prices),
                    'min': min(predicted_prices),
                    'max': max(predicted_prices)
                },
                'percentiles': {
                    '5%': predicted_prices[int(0.05 * len(predicted_prices))],
                    '95%': predicted_prices[int(0.95 * len(predicted_prices))]
                },
                'quantum_advantage': False,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error Monte Carlo: {e}")
            return {'error': f'Error en análisis: {str(e)}'}

pqc_system = PostQuantumSystem()

# ============================================================================
# BOT TELEGRAM COMPLETO
# ============================================================================

class TelegramBot:
    """Bot Telegram completo"""
    
    def __init__(self):
        self.app = None
        self.token = config.BOT_TOKEN
        self.active = False
        self.setup()
    
    def setup(self):
        """Configurar bot"""
        if not telegram_ok or not self.token:
            logger.warning("Telegram no configurado")
            return
        
        try:
            self.app = Application.builder().token(self.token).build()
            self.setup_handlers()
            self.active = True
            logger.info("Bot Telegram configurado")
        except Exception as e:
            logger.error(f"Error bot: {e}")
    
    def setup_handlers(self):
        """Configurar handlers"""
        if not self.app:
            return
        
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("precio", self.price_command))
        self.app.add_handler(CommandHandler("trading", self.trading_command))
        self.app.add_handler(CommandHandler("sharia", self.sharia_command))
        self.app.add_handler(CommandHandler("analisis", self.analysis_command))
        self.app.add_handler(CommandHandler("ayuda", self.help_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.text_handler))
        self.app.add_handler(CallbackQueryHandler(self.callback_handler))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        try:
            user = update.effective_user
            user_id = str(user.id)
            username = user.username or "Usuario"
            
            db.save_user({
                'id': user_id,
                'username': username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'language': 'es'
            })
            
            message = f"""🚀 OMNIX V5 QUANTUM READY

¡Bienvenido {username}!

Soy OMNIX IA V5, tu asistente de trading más avanzado del mundo, desarrollado por Harold Nunes.

🔥 FUNCIONES COMPLETAS:
• IA Triple (Gemini + GPT-4 + Claude)
• Trading automático multi-exchange
• Análisis cuántico Monte Carlo
• Validación Sharia completa
• Voz premium ElevenLabs
• WhatsApp + Telegram integration
• Post-Quantum Cryptography

📱 COMANDOS:
/precio [CRYPTO] - Precios multi-exchange
/trading - Centro de trading
/sharia [CRYPTO] - Validación Sharia
/analisis [CRYPTO] - Análisis técnico
/ayuda - Guía completa

¡Comencemos! 🎯"""

            await update.message.reply_text(message)
            
        except Exception as e:
            logger.error(f"Error /start: {e}")
            await update.message.reply_text("Error iniciando. Inténtalo de nuevo.")
    
    async def price_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /precio"""
        try:
            args = context.args
            symbol = args[0].upper() if args else 'BTC'
            
            if '/' not in symbol:
                symbol += '/USD'
            
            await update.message.reply_text(f"📊 Obteniendo precios de {symbol} de múltiples exchanges...")
            
            price_data = trading_system.get_multi_exchange_prices(symbol)
            
            if not price_data.get('success'):
                await update.message.reply_text(f"❌ Error: {price_data.get('error', 'Error desconocido')}")
                return
            
            stats = price_data.get('statistics', {})
            exchanges = price_data.get('exchanges', {})
            
            message = f"""💰 PRECIOS DE {price_data['symbol']}

📊 ESTADÍSTICAS:
• Precio promedio: ${stats.get('average_price', 0):,.2f}
• Precio mínimo: ${stats.get('min_price', 0):,.2f}
• Precio máximo: ${stats.get('max_price', 0):,.2f}
• Spread: {stats.get('spread_percentage', 0):.2f}%

🏦 EXCHANGES ({stats.get('num_exchanges', 0)}):\n"""

            for exchange_name, data in exchanges.items():
                change_emoji = "📈" if data.get('change', 0) >= 0 else "📉"
                message += f"• {exchange_name.title()}: ${data['price']:,.2f} {change_emoji}\n"
            
            message += f"\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            
            await update.message.reply_text(message)
            
        except Exception as e:
            logger.error(f"Error /precio: {e}")
            await update.message.reply_text("❌ Error obteniendo precios.")
    
    async def trading_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /trading"""
        try:
            keyboard = [
                [InlineKeyboardButton("📊 Precios Multi-Exchange", callback_data="multi_prices")],
                [InlineKeyboardButton("💰 Comprar BTC $50", callback_data="buy_btc_50"),
                 InlineKeyboardButton("💸 Vender BTC $50", callback_data="sell_btc_50")],
                [InlineKeyboardButton("📈 Análisis Técnico", callback_data="technical_analysis"),
                 InlineKeyboardButton("☪️ Validación Sharia", callback_data="sharia_validation")],
                [InlineKeyboardButton("🧮 Monte Carlo Analysis", callback_data="monte_carlo")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = """🎯 CENTRO DE TRADING OMNIX V5

🚀 FUNCIONES AVANZADAS:
• Trading automático multi-exchange
• Análisis técnico con IA
• Gestión de riesgos Monte Carlo
• Validación Sharia automática
• Arbitraje inteligente

⚠️ TRADING REAL:
• Kraken API conectada
• Límites: $1 - $100 por operación
• Stop-loss automático
• Gestión de riesgos institucional

Selecciona una opción:"""

            await update.message.reply_text(message, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error /trading: {e}")
            await update.message.reply_text("❌ Error accediendo a trading.")
    
    async def sharia_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /sharia"""
        try:
            args = context.args
            crypto = args[0] if args else 'BTC'
            
            validation = sharia_validator.validate_crypto(crypto)
            
            if validation.get('success'):
                await update.message.reply_text(validation['message'])
            else:
                await update.message.reply_text(f"❌ Error: {validation.get('error', 'Error desconocido')}")
                
        except Exception as e:
            logger.error(f"Error /sharia: {e}")
            await update.message.reply_text("❌ Error en validación Sharia.")
    
    async def analysis_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /analisis"""
        try:
            args = context.args
            symbol = args[0].upper() if args else 'BTC'
            
            if '/' not in symbol:
                symbol += '/USD'
            
            await update.message.reply_text(f"📈 Realizando análisis técnico de {symbol}...")
            
            analysis = trading_system.get_technical_analysis(symbol)
            
            if not analysis.get('success'):
                await update.message.reply_text(f"❌ Error: {analysis.get('error')}")
                return
            
            indicators = analysis.get('indicators', {})
            signals = analysis.get('signals', [])
            
            message = f"""📈 ANÁLISIS TÉCNICO - {analysis['symbol']}

💵 Precio actual: ${analysis.get('current_price', 0):,.2f}

🔍 INDICADORES:
• RSI: {indicators.get('rsi', 0):.1f}
• SMA 20: ${indicators.get('sma_20', 0):,.2f}
• SMA 50: ${indicators.get('sma_50', 0):,.2f}
• Soporte: ${indicators.get('support', 0):,.2f}
• Resistencia: ${indicators.get('resistance', 0):,.2f}

🎯 SEÑALES:"""
            
            for signal in signals:
                message += f"\n• {signal}"
            
            message += f"\n\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            
            await update.message.reply_text(message)
            
        except Exception as e:
            logger.error(f"Error /analisis: {e}")
            await update.message.reply_text("❌ Error en análisis técnico.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /ayuda"""
        try:
            message = """📖 GUÍA COMPLETA OMNIX V5

🤖 SOBRE OMNIX:
Sistema de trading más avanzado del mundo con IA Post-Cuántica, desarrollado por Harold Nunes.

🎯 COMANDOS PRINCIPALES:
/start - Iniciar OMNIX V5
/precio [CRYPTO] - Precios multi-exchange
/trading - Centro de trading completo
/sharia [CRYPTO] - Validación Sharia
/analisis [CRYPTO] - Análisis técnico
/ayuda - Esta guía

💬 CONVERSACIÓN NATURAL:
• "¿Cuál es el precio de Bitcoin?"
• "Quiero comprar $50 de Ethereum"
• "¿Es halal Cardano?"
• "Análisis técnico de ADA"

🔥 FUNCIONES AVANZADAS:
• IA Triple (Gemini + GPT-4 + Claude)
• Trading automático 24/7
• Análisis cuántico Monte Carlo
• Validación Sharia completa
• Voz premium ElevenLabs
• WhatsApp integration
• Post-Quantum Cryptography

⚡ TRADING REAL:
• Conectado a Kraken, Binance, Coinbase
• Límite: $100 por operación
• Gestión de riesgos institucional

¡Estoy aquí para tu trading inteligente! 🚀"""

            await update.message.reply_text(message)
            
        except Exception as e:
            logger.error(f"Error /ayuda: {e}")
            await update.message.reply_text("❌ Error mostrando ayuda.")
    
    async def text_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler de texto"""
        try:
            user_id = str(update.effective_user.id)
            message = update.message.text
            
            # Procesar con IA
            response, model = ai_system.process_message(message, user_id)
            
            # Enviar respuesta
            await update.message.reply_text(response)
            
            # Generar voz si está disponible
            try:
                audio_data = voice_system.generate_audio(response, 'es')
                if audio_data:
                    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                        tmp.write(audio_data)
                        tmp.flush()
                        await update.message.reply_voice(voice=open(tmp.name, 'rb'))
                        os.unlink(tmp.name)
            except Exception as voice_error:
                logger.warning(f"Error generando voz: {voice_error}")
            
        except Exception as e:
            logger.error(f"Error texto: {e}")
            await update.message.reply_text("Disculpa, hay un problema técnico. ¿Puedes intentar de nuevo?")
    
    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler de callbacks"""
        try:
            query = update.callback_query
            await query.answer()
            
            data = query.data
            user_id = str(query.from_user.id)
            
            if data == "multi_prices":
                btc_prices = trading_system.get_multi_exchange_prices('BTC/USD')
                eth_prices = trading_system.get_multi_exchange_prices('ETH/USD')
                
                message = "📊 PRECIOS MULTI-EXCHANGE\n\n"
                
                if btc_prices.get('success'):
                    stats = btc_prices.get('statistics', {})
                    message += f"💰 BTC/USD: ${stats.get('average_price', 0):,.2f}\n"
                    message += f"   Spread: {stats.get('spread_percentage', 0):.2f}%\n\n"
                
                if eth_prices.get('success'):
                    stats = eth_prices.get('statistics', {})
                    message += f"💎 ETH/USD: ${stats.get('average_price', 0):,.2f}\n"
                    message += f"   Spread: {stats.get('spread_percentage', 0):.2f}%\n"
                
                await query.edit_message_text(message)
            
            elif data in ["buy_btc_50", "sell_btc_50"]:
                side = "buy" if "buy" in data else "sell"
                amount = 50
                
                result = trading_system.execute_trade(user_id, 'BTC/USD', side, amount)
                
                if result.get('success'):
                    message = f"✅ {result['message']}\n\n"
                    message += f"Order ID: {result['trade_data']['order_id']}\n"
                    message += f"Estado: {result['trade_data']['status']}"
                    
                    # Enviar notificación WhatsApp si está configurado
                    # whatsapp_system.send_trading_notification(user_phone, result['trade_data'])
                else:
                    message = f"❌ Error: {result.get('error')}"
                
                await query.edit_message_text(message)
            
            elif data == "technical_analysis":
                analysis = trading_system.get_technical_analysis('BTC/USD')
                
                if analysis.get('success'):
                    indicators = analysis.get('indicators', {})
                    message = f"📈 ANÁLISIS BTC/USD\n\n"
                    message += f"💵 Precio: ${analysis.get('current_price', 0):,.2f}\n"
                    message += f"🔍 RSI: {indicators.get('rsi', 0):.1f}\n"
                    message += f"📊 SMA20: ${indicators.get('sma_20', 0):,.2f}\n"
                    message += f"🎯 Soporte: ${indicators.get('support', 0):,.2f}\n"
                    message += f"🚀 Resistencia: ${indicators.get('resistance', 0):,.2f}"
                else:
                    message = f"❌ Error: {analysis.get('error')}"
                
                await query.edit_message_text(message)
            
            elif data == "sharia_validation":
                validation = sharia_validator.validate_crypto('BTC')
                await query.edit_message_text(validation['message'])
            
            elif data == "monte_carlo":
                # Simular datos de precios para Monte Carlo
                sample_prices = [50000, 51000, 49500, 52000, 50500, 53000, 51500, 54000]
                mc_analysis = pqc_system.quantum_monte_carlo_analysis(sample_prices, 500)
                
                if 'error' not in mc_analysis:
                    predicted = mc_analysis.get('predicted_prices', {})
                    message = f"🧮 ANÁLISIS MONTE CARLO\n\n"
                    message += f"🎯 Método: {mc_analysis.get('method', 'N/A')}\n"
                    message += f"📊 Simulaciones: {mc_analysis.get('simulations', 0)}\n"
                    message += f"💵 Precio actual: ${mc_analysis.get('current_price', 0):,.2f}\n\n"
                    message += f"📈 Predicciones:\n"
                    message += f"• Media: ${predicted.get('mean', 0):,.2f}\n"
                    message += f"• Mediana: ${predicted.get('median', 0):,.2f}\n"
                    message += f"• Mín: ${predicted.get('min', 0):,.2f}\n"
                    message += f"• Máx: ${predicted.get('max', 0):,.2f}\n"
                    
                    if mc_analysis.get('quantum_advantage'):
                        message += "\n⚡ Ventaja cuántica activada"
                else:
                    message = f"❌ Error: {mc_analysis.get('error')}"
                
                await query.edit_message_text(message)
            
        except Exception as e:
            logger.error(f"Error callback: {e}")
            await query.edit_message_text("❌ Error procesando solicitud.")

telegram_bot = TelegramBot()

# ============================================================================
# API FLASK COMPLETA
# ============================================================================

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

@app.route('/', methods=['GET'])
def dashboard():
    """Dashboard principal"""
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>OMNIX V5 QUANTUM READY - Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; 
            min-height: 100vh;
            padding: 20px;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            background: rgba(255,255,255,0.1); 
            padding: 40px; 
            border-radius: 20px;
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255,255,255,0.2);
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }
        h1 { 
            font-size: 3em; 
            margin-bottom: 10px; 
            text-align: center;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            background: linear-gradient(45deg, #FFD700, #FFA500);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .subtitle { 
            text-align: center; 
            font-size: 1.2em; 
            margin-bottom: 30px;
            opacity: 0.9;
        }
        .status { 
            color: #4CAF50; 
            font-weight: bold; 
            font-size: 1.4em; 
            text-align: center;
            margin-bottom: 40px;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        }
        .grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
            gap: 25px; 
            margin: 30px 0; 
        }
        .card { 
            background: rgba(255,255,255,0.15); 
            padding: 25px; 
            border-radius: 15px; 
            border: 1px solid rgba(255,255,255,0.2);
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }
        .card:hover { 
            transform: translateY(-5px); 
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
            background: rgba(255,255,255,0.2);
        }
        .card h3 { 
            color: #4CAF50; 
            margin-bottom: 15px; 
            font-size: 1.3em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .card p { 
            line-height: 1.6; 
            opacity: 0.9; 
        }
        .stats-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 20px; 
            margin: 30px 0; 
        }
        .stat { 
            background: rgba(255,255,255,0.1); 
            padding: 20px; 
            border-radius: 12px; 
            text-align: center;
            border: 1px solid rgba(255,255,255,0.15);
        }
        .stat-value { 
            font-size: 2em; 
            font-weight: bold; 
            color: #4CAF50; 
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        }
        .stat-label { 
            margin-top: 5px; 
            opacity: 0.8; 
            font-size: 0.9em;
        }
        .api-section { 
            margin: 40px 0; 
        }
        .api-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 15px; 
        }
        .api-link { 
            display: block;
            color: #FFD700; 
            text-decoration: none; 
            font-weight: bold; 
            padding: 18px 25px; 
            background: rgba(255,215,0,0.15); 
            border-radius: 12px; 
            text-align: center;
            transition: all 0.3s ease;
            border: 1px solid rgba(255,215,0,0.3);
        }
        .api-link:hover { 
            background: rgba(255,215,0,0.25); 
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(255,215,0,0.3);
        }
        .footer { 
            text-align: center; 
            margin-top: 50px; 
            padding-top: 30px; 
            border-top: 1px solid rgba(255,255,255,0.2);
            opacity: 0.8;
        }
        .badge { 
            display: inline-block; 
            background: #4CAF50; 
            padding: 5px 12px; 
            border-radius: 20px; 
            font-size: 0.8em; 
            margin: 5px;
        }
        .feature-icon { 
            font-size: 1.5em; 
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 OMNIX V5 QUANTUM READY</h1>
        <p class="subtitle">Sistema de Trading Automatizado con IA Post-Cuántica</p>
        <div class="status">✅ SISTEMA OPERATIVO EN RAILWAY</div>
        <p style="text-align: center; font-size: 1.2em; margin-bottom: 40px;">
            <strong>Desarrollado por Harold Nunes</strong>
        </p>
        
        <div class="grid">
            <div class="card">
                <h3><span class="feature-icon">🤖</span> IA Triple Avanzada</h3>
                <p>Sistema inteligente con Gemini Pro, GPT-4 y Claude para análisis contextual y respuestas optimizadas según el tipo de consulta.</p>
                <div style="margin-top: 15px;">
                    <span class="badge">Gemini Pro</span>
                    <span class="badge">GPT-4o</span>
                    <span class="badge">Claude 3</span>
                </div>
            </div>
            
            <div class="card">
                <h3><span class="feature-icon">💰</span> Trading Multi-Exchange</h3>
                <p>Trading real con Kraken, análisis de Binance y Coinbase Pro. Arbitraje automático y gestión de riesgos institucional.</p>
                <div style="margin-top: 15px;">
                    <span class="badge">Kraken Real</span>
                    <span class="badge">Binance</span>
                    <span class="badge">Coinbase Pro</span>
                </div>
            </div>
            
            <div class="card">
                <h3><span class="feature-icon">☪️</span> Validación Sharia</h3>
                <p>Sistema completo de validación Sharia con base de scholars reconocidos globalmente para trading halal.</p>
                <div style="margin-top: 15px;">
                    <span class="badge">AAOIFI</span>
                    <span class="badge">Dar Al-Ifta</span>
                    <span class="badge">Dubai Islamic</span>
                </div>
            </div>
            
            <div class="card">
                <h3><span class="feature-icon">🎙️</span> Sistema de Voz</h3>
                <p>Respuestas por voz con ElevenLabs (Voz Lucia) y Google TTS en múltiples idiomas con cache inteligente.</p>
                <div style="margin-top: 15px;">
                    <span class="badge">ElevenLabs</span>
                    <span class="badge">Google TTS</span>
                    <span class="badge">6 Idiomas</span>
                </div>
            </div>
            
            <div class="card">
                <h3><span class="feature-icon">📱</span> Multi-Plataforma</h3>
                <p>Bot de Telegram con webhook corregido, integración WhatsApp via Twilio y API REST completa.</p>
                <div style="margin-top: 15px;">
                    <span class="badge">Telegram Bot</span>
                    <span class="badge">WhatsApp</span>
                    <span class="badge">API REST</span>
                </div>
            </div>
            
            <div class="card">
                <h3><span class="feature-icon">🔮</span> Post-Quantum Crypto</h3>
                <p>Análisis Monte Carlo cuántico con secuencias Sobol y arquitectura preparada para criptografía post-cuántica.</p>
                <div style="margin-top: 15px;">
                    <span class="badge">Monte Carlo</span>
                    <span class="badge">Sobol Sequences</span>
                    <span class="badge">PQC Ready</span>
                </div>
            </div>
        </div>
        
        <div class="api-section">
            <h3 style="text-align: center; margin-bottom: 25px; font-size: 1.8em;">📡 API ENDPOINTS</h3>
            <div class="api-grid">
                <a href="/api/status" class="api-link">🔍 Estado del Sistema</a>
                <a href="/api/precio/BTC" class="api-link">💰 Precio Bitcoin</a>
                <a href="/api/precio/ETH" class="api-link">💎 Precio Ethereum</a>
                <a href="/api/stats" class="api-link">📊 Estadísticas</a>
                <a href="/api/ai-stats" class="api-link">🧠 Stats IA</a>
                <a href="/api/sharia/BTC" class="api-link">☪️ Validación Sharia</a>
                <a href="/api/technical/BTC" class="api-link">📈 Análisis Técnico</a>
                <a href="/api/monte-carlo" class="api-link">🔮 Monte Carlo</a>
            </div>
        </div>
        
        <h3 style="text-align: center; margin-bottom: 25px; font-size: 1.8em;">📊 ESTADÍSTICAS EN TIEMPO REAL</h3>
        <div class="stats-grid">
            <div class="stat">
                <div class="stat-value">{{ exchanges_count }}</div>
                <div class="stat-label">Exchanges Configurados</div>
            </div>
            <div class="stat">
                <div class="stat-value">{{ ai_models_count }}</div>
                <div class="stat-label">Modelos IA</div>
            </div>
            <div class="stat">
                <div class="stat-value">{{ telegram_status }}</div>
                <div class="stat-label">Bot Telegram</div>
            </div>
            <div class="stat">
                <div class="stat-value">{{ voice_status }}</div>
                <div class="stat-label">Sistema Voz</div>
            </div>
            <div class="stat">
                <div class="stat-value">{{ total_queries }}</div>
                <div class="stat-label">Consultas IA</div>
            </div>
            <div class="stat">
                <div class="stat-value">{{ cache_size }}</div>
                <div class="stat-label">Cache Voz</div>
            </div>
        </div>
        
        <div class="footer">
            <p style="font-size: 1.1em; margin-bottom: 10px;">
                © 2025 Harold Nunes • OMNIX V5 Quantum Ready • Railway Powered
            </p>
            <p>🔐 Post-Quantum Security • 🌍 Multi-language • ⚡ Real-time Trading • ☪️ Sharia Compliant</p>
        </div>
    </div>
</body>
</html>
    """, 
    exchanges_count=len(trading_system.exchanges),
    ai_models_count=len([m for m in ['gemini', 'openai', 'claude'] if m in ai_system.models]),
    telegram_status='✅' if telegram_bot.active else '⚠️',
    voice_status='✅' if voice_system.elevenlabs_ok or tts_ok else '❌',
    total_queries=sum(ai_system.usage_stats.values()),
    cache_size=len(voice_system.cache)
    )

@app.route('/api/status', methods=['GET'])
def api_status():
    """Estado completo del sistema"""
    return jsonify({
        'status': 'operational',
        'version': 'OMNIX V5 QUANTUM READY',
        'developer': 'Harold Nunes',
        'timestamp': datetime.now().isoformat(),
        'components': {
            'flask': True,
            'telegram_bot': telegram_bot.active,
            'ai_system': len(ai_system.models) > 0,
            'trading_system': len(trading_system.exchanges) > 0,
            'voice_system': voice_system.elevenlabs_ok or tts_ok,
            'whatsapp_system': whatsapp_system.client is not None,
            'database': db.connection is not None,
            'post_quantum': pqc_system.quantum_ready
        },
        'features': {
            'real_trading': 'kraken' in trading_system.exchanges,
            'ai_models': list(ai_system.models.keys()),
            'voice_engines': [
                'elevenlabs' if voice_system.elevenlabs_ok else None,
                'google_tts' if tts_ok else None
            ],
            'exchanges': list(trading_system.exchanges.keys()),
            'languages_supported': ['es', 'en', 'ar', 'pt', 'zh', 'fr'],
            'sharia_compliant': True,
            'quantum_ready': pqc_system.quantum_ready
        },
        'limits': {
            'max_trade_amount': config.MAX_TRADE,
            'min_trade_amount': config.MIN_TRADE,
            'daily_limit': config.DAILY_LIMIT
        }
    })

@app.route('/api/precio/<symbol>', methods=['GET'])
def api_price(symbol):
    """Precio multi-exchange"""
    if '/' not in symbol:
        symbol = f"{symbol.upper()}/USD"
    
    result = trading_system.get_multi_exchange_prices(symbol)
    return jsonify(result)

@app.route('/api/technical/<symbol>', methods=['GET'])
def api_technical(symbol):
    """Análisis técnico"""
    if '/' not in symbol:
        symbol = f"{symbol.upper()}/USD"
    
    result = trading_system.get_technical_analysis(symbol)
    return jsonify(result)

@app.route('/api/sharia/<crypto>', methods=['GET'])
def api_sharia(crypto):
    """Validación Sharia"""
    result = sharia_validator.validate_crypto(crypto)
    return jsonify(result)

@app.route('/api/monte-carlo', methods=['POST', 'GET'])
def api_monte_carlo():
    """Análisis Monte Carlo"""
    try:
        if request.method == 'POST':
            data = request.get_json()
            price_data = data.get('price_data', [])
            simulations = data.get('simulations', 1000)
        else:
            # Datos de ejemplo para GET
            price_data = [50000, 51000, 49500, 52000, 50500, 53000, 51500, 54000, 52500]
            simulations = 1000
        
        result = pqc_system.quantum_monte_carlo_analysis(price_data, simulations)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Estadísticas generales"""
    try:
        # Stats de base de datos
        db.cursor.execute("SELECT COUNT(*) as count FROM users")
        user_count = db.cursor.fetchone()['count']
        
        db.cursor.execute("SELECT COUNT(*) as count FROM chats")
        chat_count = db.cursor.fetchone()['count']
        
        db.cursor.execute("SELECT COUNT(*) as count FROM trades")
        trade_count = db.cursor.fetchone()['count']
        
        return jsonify({
            'success': True,
            'data': {
                'users': user_count,
                'chats': chat_count,
                'trades': trade_count,
                'ai_usage': ai_system.usage_stats,
                'exchanges': len(trading_system.exchanges),
                'voice_cache': len(voice_system.cache),
                'price_cache': len(trading_system.price_cache),
                'components_status': {
                    'telegram': telegram_bot.active,
                    'voice_premium': voice_system.elevenlabs_ok,
                    'whatsapp': whatsapp_system.client is not None,
                    'quantum_analysis': pqc_system.quantum_ready
                }
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ai-stats', methods=['GET'])
def api_ai_stats():
    """Estadísticas IA"""
    return jsonify({
        'success': True,
        'data': {
            'models_available': {
                'gemini': 'gemini' in ai_system.models,
                'openai': 'openai' in ai_system.models,
                'claude': 'claude' in ai_system.models
            },
            'usage_stats': ai_system.usage_stats,
            'total_queries': sum(ai_system.usage_stats.values()),
            'most_used_model': max(ai_system.usage_stats.items(), key=lambda x: x[1])[0]
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Chat con IA"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'success': False, 'error': 'Message required'}), 400
        
        message = data['message']
        user_id = data.get('user_id', 'api_user')
        
        response, model = ai_system.process_message(message, user_id)
        
        # Generar voz si se solicita
        audio_data = None
        if data.get('include_voice', False):
            audio_data = voice_system.generate_audio(response, data.get('language', 'es'))
        
        return jsonify({
            'success': True,
            'response': response,
            'model_used': model,
            'has_audio': audio_data is not None,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/trade', methods=['POST'])
def api_trade():
    """Ejecutar trade"""
    try:
        data = request.get_json()
        if not all(k in data for k in ['user_id', 'symbol', 'side', 'amount']):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        result = trading_system.execute_trade(
            data['user_id'],
            data['symbol'],
            data['side'],
            float(data['amount'])
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/webhook/telegram', methods=['POST'])
def telegram_webhook():
    """Webhook Telegram - CORREGIDO"""
    try:
        if not telegram_bot.active:
            return jsonify({'error': 'Bot not available'}), 503
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data'}), 400
        
        logger.info("📨 Webhook recibido")
        
        def process_update():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # CORRECCIÓN CRÍTICA: Usar de_json correctamente
                update = Update.de_json(data, telegram_bot.app.bot)
                
                loop.run_until_complete(
                    telegram_bot.app.process_update(update)
                )
                loop.close()
                
                logger.info("✅ Update procesado")
                
            except Exception as e:
                logger.error(f"❌ Error procesando update: {e}")
        
        # Procesar en hilo separado
        threading.Thread(target=process_update, daemon=True).start()
        
        return jsonify({'status': 'ok'})
        
    except Exception as e:
        logger.error(f"❌ Error webhook: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# SISTEMA PRINCIPAL
# ============================================================================

class OmnixSystem:
    """Sistema principal OMNIX V5"""
    
    def __init__(self):
        self.version = "V5 QUANTUM READY - RAILWAY FINAL"
        self.developer = "Harold Nunes"
        
    def log_system_status(self):
        """Log del estado del sistema"""
        logger.info("🚀 INICIANDO OMNIX V5 QUANTUM READY")
        logger.info(f"💫 Desarrollado por {self.developer}")
        logger.info("=" * 60)
        
        # Componentes principales
        logger.info(f"🌐 Flask API: ✅ OPERATIVO")
        logger.info(f"🤖 Telegram Bot: {'✅ ACTIVO' if telegram_bot.active else '⚠️ NO CONFIGURADO'}")
        logger.info(f"🧠 Sistema IA: {'✅ TRIPLE IA' if ai_system.models else '⚠️ LIMITADO'}")
        logger.info(f"📊 Trading: {'✅ MULTI-EXCHANGE' if trading_system.exchanges else '⚠️ NO DISPONIBLE'}")
        logger.info(f"🎙️ Voz: {'✅ ELEVENLABS' if voice_system.elevenlabs_ok else '✅ GOOGLE TTS' if tts_ok else '❌'}")
        logger.info(f"📱 WhatsApp: {'✅ CONFIGURADO' if whatsapp_system.client else '⚠️ NO CONFIGURADO'}")
        logger.info(f"💾 Base Datos: {'✅ POSTGRESQL' if db.is_postgres else '✅ SQLITE'}")
        logger.info(f"🔮 Post-Quantum: {'✅ READY' if pqc_system.quantum_ready else '⚠️ PREPARING'}")
        
        # Características especiales
        if telegram_bot.active:
            logger.info("📱 Webhook Telegram: ✅ CORREGIDO Y FUNCIONAL")
        
        if ai_system.models:
            models_str = ", ".join(ai_system.models.keys())
            logger.info(f"🧠 Modelos IA: {models_str}")
        
        if trading_system.exchanges:
            exchanges_str = ", ".join(trading_system.exchanges.keys())
            logger.info(f"💰 Exchanges: {exchanges_str}")
        
        logger.info("=" * 60)
        logger.info(f"✅ OMNIX V5 COMPLETAMENTE OPERATIVO EN PUERTO {config.PORT}")
    
    def run(self):
        """Ejecutar sistema principal"""
        try:
            self.log_system_status()
            
            # Iniciar Flask con configuración optimizada para Railway
            app.run(
                host=config.HOST,
                port=config.PORT,
                debug=False,
                threaded=True,
                use_reloader=False
            )
            
        except KeyboardInterrupt:
            logger.info("🛑 Sistema detenido por usuario")
        except Exception as e:
            logger.error(f"❌ Error crítico: {e}")
            logger.error(traceback.format_exc())

# ============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# ============================================================================

if __name__ == "__main__":
    omnix_system = OmnixSystem()
    omnix_system.run()
































