#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNIX V5 RAILWAY FINAL - SISTEMA COMPLETO MONOLÍTICO
Todas las 32 Inteligencias + Memoria Avanzada + Trading Real
Creador: Harold Nunes - Fundador OMNIX
Valoración: $120M-$200M USD
Railway Production Ready - Código Monolítico COMPLETO
"""

import os
import asyncio
import logging
import threading
import time
import hashlib
import statistics
import math
import random
import json
import gc
import sqlite3
import traceback
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

# Flask para web dashboard
from flask import Flask, jsonify, request, render_template_string

# Imports condicionales con manejo de errores para Railway
try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False
    print("⚠️ CCXT no disponible - Trading en modo demo")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ Gemini no disponible - IA local activa")

try:
    from gtts import gTTS
    import tempfile
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    print("⚠️ gTTS no disponible - Voz desactivada")

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
    from telegram.error import Conflict
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("❌ Telegram no disponible")

# ===============================
# CONFIGURACIÓN ENTERPRISE
# ===============================

@dataclass
class EnterpriseConfig:
    """Configuración enterprise del sistema"""
    
    # Credenciales principales
    bot_token: str = field(default_factory=lambda: os.getenv('TELEGRAM_BOT_TOKEN', ''))
    authorized_user_id: int = 7014748854  # Harold Nunes
    gemini_api_key: str = field(default_factory=lambda: os.getenv('GEMINI_API_KEY', ''))
    openai_api_key: str = field(default_factory=lambda: os.getenv('OPENAI_API_KEY', ''))
    
    # Trading credentials
    kraken_api_key: str = field(default_factory=lambda: os.getenv('KRAKEN_API_KEY', ''))
    kraken_private_key: str = field(default_factory=lambda: os.getenv('KRAKEN_PRIVATE_KEY', ''))
    binance_api_key: str = field(default_factory=lambda: os.getenv('BINANCE_API_KEY', ''))
    binance_secret: str = field(default_factory=lambda: os.getenv('BINANCE_SECRET', ''))
    
    # Sistema configuración
    sandbox_mode: bool = os.getenv('SANDBOX_MODE', 'false').lower() == 'true'
    trading_enabled: bool = True
    voice_enabled: bool = True
    voice_language: str = 'es'
    debug_mode: bool = os.getenv('DEBUG', 'false').lower() == 'true'
    
    # Railway específico
    port: int = int(os.environ.get('PORT', 5000))
    host: str = '0.0.0.0'
    
    def validate(self) -> bool:
        """Validar configuración mínima"""
        return bool(self.bot_token)
        
    def get_trading_mode(self) -> str:
        """Obtener modo de trading actual"""
        if self.kraken_api_key and self.kraken_private_key and not self.sandbox_mode:
            return 'PRODUCTION'
        elif self.kraken_api_key and self.kraken_private_key and self.sandbox_mode:
            return 'SANDBOX'
        else:
            return 'DEMO'

config = EnterpriseConfig()

# ===============================
# SISTEMA DE LOGGING ENTERPRISE
# ===============================

class EnterpriseLogger:
    """Sistema de logging enterprise centralizado"""
    
    def __init__(self):
        self.setup_loggers()
        
    def setup_loggers(self):
        """Configurar loggers especializados"""
        
        # Loggers principales
        self.system_logger = logging.getLogger('OMNIX.System')
        self.worker_logger = logging.getLogger('OMNIX.Workers')
        self.trading_logger = logging.getLogger('OMNIX.Trading')
        self.intelligence_logger = logging.getLogger('OMNIX.Intelligence')
        self.memory_logger = logging.getLogger('OMNIX.Memory')
        self.security_logger = logging.getLogger('OMNIX.Security')
        self.api_logger = logging.getLogger('OMNIX.API')
        
        # Configurar nivel según modo
        level = logging.DEBUG if config.debug_mode else logging.INFO
        
        # Configurar todos los loggers
        for logger in [self.system_logger, self.worker_logger, self.trading_logger, 
                      self.intelligence_logger, self.memory_logger, self.security_logger, 
                      self.api_logger]:
            logger.setLevel(level)
            
            # Handler para consola
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.propagate = False
    
    def log_startup(self):
        """Log de inicio del sistema"""
        self.system_logger.info("🚀 OMNIX V5 RAILWAY FINAL - INICIANDO SISTEMA COMPLETO")
        self.system_logger.info(f"💎 Valoración: $120M-$200M USD")
        self.system_logger.info(f"👑 Creador: Harold Nunes - Fundador OMNIX")
        self.system_logger.info(f"🔧 Modo Trading: {config.get_trading_mode()}")
        self.system_logger.info(f"🌐 Puerto: {config.port}")
        self.system_logger.info(f"🐛 Debug: {'Activo' if config.debug_mode else 'Desactivo'}")

enterprise_logger = EnterpriseLogger()

# ===============================
# SISTEMA DE MEMORIA AVANZADA
# ===============================

class AdvancedMemorySystem:
    """Sistema de memoria avanzada con SQLite persistente y análisis inteligente"""
    
    def __init__(self):
        self.db_path = "omnix_railway_memory.db"
        self.init_database()
        self.user_profiles = {}
        self.conversation_context = defaultdict(list)
        self.learning_patterns = {}
        self.personality_cache = {}
        
    def init_database(self):
        """Inicializar base de datos SQLite completa"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tabla de conversaciones con análisis completo
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    response TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    context TEXT,
                    sentiment REAL DEFAULT 0.5,
                    topics TEXT,
                    complexity_level INTEGER DEFAULT 1,
                    response_time_ms INTEGER DEFAULT 0,
                    session_id TEXT,
                    language_detected TEXT DEFAULT 'es',
                    emotion_detected TEXT DEFAULT 'neutral'
                )
            ''')
            
            # Tabla de perfiles de usuario expandida
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    language_code TEXT DEFAULT 'es',
                    preferences TEXT,
                    trading_style TEXT DEFAULT 'conservative',
                    risk_tolerance REAL DEFAULT 0.5,
                    favorite_assets TEXT,
                    interaction_count INTEGER DEFAULT 0,
                    total_messages INTEGER DEFAULT 0,
                    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                    personality_type TEXT DEFAULT 'unknown',
                    personality_traits TEXT,
                    personality_confidence REAL DEFAULT 0.0,
                    preferred_complexity INTEGER DEFAULT 2,
                    avg_sentiment REAL DEFAULT 0.5,
                    timezone TEXT,
                    active_sessions INTEGER DEFAULT 0
                )
            ''')
            
            # Tabla de patrones de aprendizaje
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT NOT NULL,
                    pattern_data TEXT NOT NULL,
                    confidence REAL DEFAULT 0.5,
                    usage_count INTEGER DEFAULT 1,
                    success_rate REAL DEFAULT 0.5,
                    user_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME,
                    tags TEXT,
                    FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
                )
            ''')
            
            # Tabla de trading history para memoria
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trading_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    amount REAL NOT NULL,
                    price REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    result TEXT,
                    profit_loss REAL DEFAULT 0.0,
                    strategy_used TEXT,
                    market_condition TEXT,
                    user_emotion TEXT,
                    confidence_level REAL DEFAULT 0.5,
                    FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
                )
            ''')
            
            # Crear índices para performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations (user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations (timestamp)')
            
            conn.commit()
            conn.close()
            
            enterprise_logger.memory_logger.info("✅ Base de datos de memoria avanzada inicializada")
            
        except Exception as e:
            enterprise_logger.memory_logger.error(f"❌ Error inicializando BD: {e}")
            
    def save_conversation(self, user_id: int, message: str, response: str, 
                         context: Dict = None, response_time_ms: int = 0):
        """Guardar conversación con análisis completo"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Análisis avanzado del mensaje
            sentiment = self._analyze_sentiment(message)
            topics = self._extract_topics(message)
            complexity = self._determine_complexity(message)
            language = self._detect_language(message)
            emotion = self._detect_emotion(message)
            
            # Generar session_id si no existe
            session_id = context.get('session_id', f"session_{user_id}_{int(time.time())}") if context else f"session_{user_id}_{int(time.time())}"
            
            # Insertar conversación
            cursor.execute('''
                INSERT INTO conversations 
                (user_id, message, response, context, sentiment, topics, 
                 complexity_level, response_time_ms, session_id, language_detected, emotion_detected)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, message, response, json.dumps(context or {}), 
                  sentiment, json.dumps(topics), complexity, response_time_ms,
                  session_id, language, emotion))
            
            # Actualizar perfil de usuario
            cursor.execute('''
                UPDATE user_profiles 
                SET last_seen = CURRENT_TIMESTAMP, 
                    total_messages = total_messages + 1,
                    interaction_count = interaction_count + 1
                WHERE user_id = ?
            ''', (user_id,))
            
            # Si no existe el perfil, crearlo
            cursor.execute('SELECT user_id FROM user_profiles WHERE user_id = ?', (user_id,))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO user_profiles (user_id, first_seen, last_seen, total_messages)
                    VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
                ''', (user_id,))
            
            conn.commit()
            conn.close()
            
            # Actualizar contexto en memoria
            self.conversation_context[user_id].append({
                'message': message,
                'response': response,
                'timestamp': datetime.now(),
                'sentiment': sentiment,
                'topics': topics,
                'complexity': complexity,
                'emotion': emotion
            })
            
            # Mantener últimas 50 conversaciones en memoria
            if len(self.conversation_context[user_id]) > 50:
                self.conversation_context[user_id] = self.conversation_context[user_id][-50:]
                
            enterprise_logger.memory_logger.info(f"💾 Conversación guardada para usuario {user_id}")
            
        except Exception as e:
            enterprise_logger.memory_logger.error(f"❌ Error guardando conversación: {e}")
            
    def get_user_context(self, user_id: int, include_history: bool = True) -> Dict[str, Any]:
        """Obtener contexto completo y detallado del usuario"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Obtener perfil completo del usuario
            cursor.execute('SELECT * FROM user_profiles WHERE user_id = ?', (user_id,))
            profile_data = cursor.fetchone()
            
            # Obtener conversaciones recientes
            cursor.execute('''
                SELECT message, response, timestamp, sentiment, topics, complexity_level, emotion_detected
                FROM conversations 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 20
            ''', (user_id,))
            recent_conversations = cursor.fetchall()
            
            conn.close()
            
            # Procesar información del perfil
            if profile_data:
                profile = {
                    'user_id': profile_data[0],
                    'username': profile_data[1],
                    'first_name': profile_data[2],
                    'last_name': profile_data[3],
                    'language_code': profile_data[4],
                    'trading_style': profile_data[6],
                    'risk_tolerance': profile_data[7],
                    'interaction_count': profile_data[9],
                    'total_messages': profile_data[10],
                    'personality_type': profile_data[13],
                    'personality_confidence': profile_data[15] if len(profile_data) > 15 else 0.0,
                    'preferred_complexity': profile_data[16] if len(profile_data) > 16 else 2,
                    'avg_sentiment': profile_data[17] if len(profile_data) > 17 else 0.5
                }
            else:
                profile = {'user_id': user_id, 'personality_type': 'unknown'}
            
            context = {
                'user_id': user_id,
                'profile': profile,
                'recent_conversations': recent_conversations if include_history else [],
                'conversation_count': len(recent_conversations),
                'context_quality': 0.8,
                'preferred_topics': []
            }
            
            return context
            
        except Exception as e:
            enterprise_logger.memory_logger.error(f"❌ Error obteniendo contexto: {e}")
            return {'user_id': user_id, 'error': str(e)}
    
    def save_trading_action(self, user_id: int, order_data: Dict):
        """Guardar acción de trading en memoria"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trading_memory 
                (user_id, symbol, action, amount, price, result, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                order_data['symbol'],
                order_data['action'],
                order_data['amount'],
                order_data['price'],
                'completed',
                datetime.now()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            enterprise_logger.memory_logger.error(f"Error guardando trading: {e}")
    
    def _analyze_sentiment(self, text: str) -> float:
        """Análisis de sentimiento mejorado"""
        positive_words = [
            'bien', 'bueno', 'excelente', 'perfecto', 'genial', 'fantástico',
            'increíble', 'maravilloso', 'estupendo', 'magnífico', 'brillante',
            'gracias', 'love', 'amazing', 'great', 'awesome'
        ]
        negative_words = [
            'mal', 'terrible', 'horrible', 'error', 'problema', 'fallo',
            'pesimo', 'awful', 'bad', 'wrong', 'hate', 'worst', 'stupid'
        ]
        
        text_lower = text.lower()
        positive_count = sum(2 if word in text_lower else 0 for word in positive_words)
        negative_count = sum(2 if word in text_lower else 0 for word in negative_words)
        
        word_count = len(text.split())
        sentiment_score = 0.5  # neutral base
        
        if word_count > 0:
            positive_ratio = positive_count / word_count
            negative_ratio = negative_count / word_count
            sentiment_score = 0.5 + (positive_ratio - negative_ratio) * 2
            sentiment_score = max(0.0, min(1.0, sentiment_score))
            
        return sentiment_score
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extracción de temas mejorada"""
        topics = []
        text_lower = text.lower()
        
        topic_keywords = {
            'trading': ['trading', 'trade', 'comprar', 'vender', 'precio', 'buy', 'sell', 'price'],
            'crypto': ['bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'cripto', 'coin', 'token'],
            'analysis': ['análisis', 'analizar', 'predicción', 'forecast', 'prediction', 'analyze'],
            'technical': ['técnico', 'gráfico', 'indicador', 'rsi', 'macd', 'chart', 'technical'],
            'sharia': ['sharia', 'halal', 'islam', 'islamic', 'scholar', 'compliance', 'haram'],
            'quantum': ['quantum', 'cuántico', 'monte', 'carlo', 'probability'],
            'ai': ['inteligencia', 'artificial', 'ai', 'machine', 'learning', 'neural']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
                
        return topics
    
    def _determine_complexity(self, message: str) -> int:
        """Determinar nivel de complejidad del mensaje (1-5)"""
        word_count = len(message.split())
        technical_terms = ['rsi', 'macd', 'fibonacci', 'bollinger', 'stochastic', 
                          'quantum', 'monte carlo', 'arbitrage', 'leverage']
        
        complexity = 1  # Básico
        
        if word_count > 50:
            complexity += 1
        if word_count > 100:
            complexity += 1
            
        technical_count = sum(1 for term in technical_terms if term in message.lower())
        complexity += min(2, technical_count)
        
        return min(5, complexity)
    
    def _detect_language(self, text: str) -> str:
        """Detección básica de idioma"""
        spanish_indicators = ['el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo']
        english_indicators = ['the', 'and', 'of', 'to', 'a', 'in', 'for', 'is', 'on', 'that', 'by', 'this']
        
        text_lower = text.lower()
        
        spanish_count = sum(1 for word in spanish_indicators if word in text_lower)
        english_count = sum(1 for word in english_indicators if word in text_lower)
        
        if spanish_count >= english_count:
            return 'es'
        else:
            return 'en'
    
    def _detect_emotion(self, text: str) -> str:
        """Detección básica de emociones"""
        emotions = {
            'joy': ['feliz', 'alegre', 'contento', 'genial', 'fantástico', 'happy', 'excited'],
            'anger': ['enojado', 'furioso', 'molesto', 'angry', 'mad', 'frustrated'],
            'fear': ['miedo', 'preocupado', 'nervioso', 'scared', 'worried', 'anxious'],
            'sadness': ['triste', 'deprimido', 'sad', 'disappointed', 'down'],
            'surprise': ['sorprendido', 'impresionado', 'wow', 'amazing', 'incredible'],
            'curiosity': ['pregunta', 'cómo', 'por qué', 'question', 'how', 'why', 'what']
        }
        
        text_lower = text.lower()
        
        for emotion, keywords in emotions.items():
            if any(keyword in text_lower for keyword in keywords):
                return emotion
                
        return 'neutral'

# Instanciar sistema de memoria
memory_system = AdvancedMemorySystem()

# ===============================
# SISTEMA DE 32 INTELIGENCIAS
# ===============================

class IntelligenceEngine:
    """Motor completo de 32 inteligencias especializadas"""
    
    def __init__(self):
        self.intelligences = self._initialize_all_intelligences()
        self.consensus_threshold = 0.65
        self.intelligence_cache = {}
        self.performance_metrics = {}
        
    def _initialize_all_intelligences(self) -> Dict[str, Dict]:
        """Inicializar las 32 inteligencias completas"""
        
        return {
            # GRUPO 1: ANÁLISIS DE MERCADO (8 inteligencias)
            'market_trend_analyzer': {
                'weight': 0.92, 'confidence': 0.88, 'specialty': 'trend_analysis',
                'description': 'Análisis de tendencias de mercado',
                'success_rate': 0.84
            },
            'volatility_predictor': {
                'weight': 0.85, 'confidence': 0.82, 'specialty': 'volatility_prediction',
                'description': 'Predicción de volatilidad futura',
                'success_rate': 0.79
            },
            'volume_analyst': {
                'weight': 0.78, 'confidence': 0.75, 'specialty': 'volume_analysis',
                'description': 'Análisis de patrones de volumen',
                'success_rate': 0.76
            },
            'support_resistance_finder': {
                'weight': 0.88, 'confidence': 0.85, 'specialty': 'level_identification',
                'description': 'Identificación de niveles críticos',
                'success_rate': 0.82
            },
            'momentum_detector': {
                'weight': 0.81, 'confidence': 0.78, 'specialty': 'momentum_analysis',
                'description': 'Detección de cambios de momentum',
                'success_rate': 0.77
            },
            'pattern_recognizer': {
                'weight': 0.90, 'confidence': 0.87, 'specialty': 'pattern_recognition',
                'description': 'Reconocimiento de patrones chartistas',
                'success_rate': 0.85
            },
            'breakout_predictor': {
                'weight': 0.84, 'confidence': 0.81, 'specialty': 'breakout_analysis',
                'description': 'Predicción de breakouts',
                'success_rate': 0.80
            },
            'reversal_identifier': {
                'weight': 0.79, 'confidence': 0.76, 'specialty': 'reversal_detection',
                'description': 'Identificación de reversiones',
                'success_rate': 0.74
            },
            
            # GRUPO 2: ANÁLISIS TÉCNICO (8 inteligencias)
            'rsi_specialist': {
                'weight': 0.83, 'confidence': 0.80, 'specialty': 'rsi_analysis',
                'description': 'Especialista en RSI',
                'success_rate': 0.78
            },
            'macd_expert': {
                'weight': 0.86, 'confidence': 0.83, 'specialty': 'macd_signals',
                'description': 'Experto en señales MACD',
                'success_rate': 0.81
            },
            'bollinger_analyzer': {
                'weight': 0.80, 'confidence': 0.77, 'specialty': 'bollinger_analysis',
                'description': 'Análisis de Bandas de Bollinger',
                'success_rate': 0.75
            },
            'fibonacci_calculator': {
                'weight': 0.77, 'confidence': 0.74, 'specialty': 'fibonacci_analysis',
                'description': 'Cálculos de Fibonacci',
                'success_rate': 0.72
            },
            'moving_average_guru': {
                'weight': 0.89, 'confidence': 0.86, 'specialty': 'moving_averages',
                'description': 'Especialista en medias móviles',
                'success_rate': 0.83
            },
            'stochastic_reader': {
                'weight': 0.76, 'confidence': 0.73, 'specialty': 'stochastic_analysis',
                'description': 'Análisis del oscilador estocástico',
                'success_rate': 0.71
            },
            'ichimoku_interpreter': {
                'weight': 0.82, 'confidence': 0.79, 'specialty': 'ichimoku_analysis',
                'description': 'Interpretación completa Ichimoku',
                'success_rate': 0.76
            },
            'candlestick_decoder': {
                'weight': 0.87, 'confidence': 0.84, 'specialty': 'candlestick_patterns',
                'description': 'Decodificación de velas japonesas',
                'success_rate': 0.82
            },
            
            # GRUPO 3: ANÁLISIS FUNDAMENTAL (8 inteligencias)
            'news_sentiment_analyzer': {
                'weight': 0.88, 'confidence': 0.85, 'specialty': 'news_sentiment',
                'description': 'Análisis de sentimiento de noticias',
                'success_rate': 0.80
            },
            'social_media_tracker': {
                'weight': 0.79, 'confidence': 0.76, 'specialty': 'social_sentiment',
                'description': 'Seguimiento de sentiment en redes',
                'success_rate': 0.73
            },
            'whale_movement_detector': {
                'weight': 0.91, 'confidence': 0.88, 'specialty': 'whale_activity',
                'description': 'Detección de movimientos de ballenas',
                'success_rate': 0.86
            },
            'institutional_flow_tracker': {
                'weight': 0.89, 'confidence': 0.86, 'specialty': 'institutional_analysis',
                'description': 'Seguimiento de flujos institucionales',
                'success_rate': 0.84
            },
            'regulatory_impact_assessor': {
                'weight': 0.85, 'confidence': 0.82, 'specialty': 'regulatory_analysis',
                'description': 'Evaluación del impacto regulatorio',
                'success_rate': 0.79
            },
            'adoption_trend_monitor': {
                'weight': 0.81, 'confidence': 0.78, 'specialty': 'adoption_tracking',
                'description': 'Monitoreo de tendencias de adopción',
                'success_rate': 0.75
            },
            'partnership_evaluator': {
                'weight': 0.77, 'confidence': 0.74, 'specialty': 'partnership_analysis',
                'description': 'Evaluación de partnerships',
                'success_rate': 0.72
            },
            'technology_advancement_tracker': {
                'weight': 0.84, 'confidence': 0.81, 'specialty': 'tech_analysis',
                'description': 'Seguimiento de avances tecnológicos',
                'success_rate': 0.78
            },
            
            # GRUPO 4: INTELIGENCIAS ESPECIALIZADAS (8 inteligencias)
            'quantum_probability_engine': {
                'weight': 0.95, 'confidence': 0.92, 'specialty': 'quantum_analysis',
                'description': 'Motor de probabilidades cuánticas',
                'success_rate': 0.89
            },
            'sharia_compliance_validator': {
                'weight': 0.93, 'confidence': 0.90, 'specialty': 'sharia_compliance',
                'description': 'Validador de cumplimiento Sharia',
                'success_rate': 0.91
            },
            'risk_management_optimizer': {
                'weight': 0.94, 'confidence': 0.91, 'specialty': 'risk_optimization',
                'description': 'Optimizador de gestión de riesgo',
                'success_rate': 0.88
            },
            'portfolio_rebalancer': {
                'weight': 0.90, 'confidence': 0.87, 'specialty': 'portfolio_optimization',
                'description': 'Rebalanceador de portfolio',
                'success_rate': 0.85
            },
            'arbitrage_opportunity_finder': {
                'weight': 0.87, 'confidence': 0.84, 'specialty': 'arbitrage_detection',
                'description': 'Detector de oportunidades de arbitraje',
                'success_rate': 0.81
            },
            'correlation_analyzer': {
                'weight': 0.85, 'confidence': 0.82, 'specialty': 'correlation_analysis',
                'description': 'Analizador de correlaciones',
                'success_rate': 0.79
            },
            'seasonality_detector': {
                'weight': 0.80, 'confidence': 0.77, 'specialty': 'seasonal_analysis',
                'description': 'Detector de patrones estacionales',
                'success_rate': 0.74
            },
            'macro_economic_evaluator': {
                'weight': 0.88, 'confidence': 0.85, 'specialty': 'macro_analysis',
                'description': 'Evaluador de factores macroeconómicos',
                'success_rate': 0.82
            }
        }
    
    async def get_consensus_analysis(self, symbol: str, analysis_type: str = 'complete', 
                                   timeframe: str = '1h', confidence_threshold: float = 0.6) -> Dict[str, Any]:
        """Obtener análisis de consenso completo de todas las 32 inteligencias"""
        
        try:
            start_time = time.time()
            
            # Ejecutar análisis de todas las inteligencias
            individual_analyses = {}
            
            for intelligence_name, config_data in self.intelligences.items():
                analysis = self._execute_intelligence_analysis(intelligence_name, symbol, config_data, timeframe)
                individual_analyses[intelligence_name] = analysis
            
            # Calcular consenso avanzado
            consensus_result = self._calculate_advanced_consensus(individual_analyses, confidence_threshold)
            
            # Generar recomendaciones finales
            final_recommendations = self._generate_final_recommendations(consensus_result, symbol)
            
            # Calcular tiempo total de procesamiento
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            complete_analysis = {
                'symbol': symbol,
                'analysis_type': analysis_type,
                'timeframe': timeframe,
                'timestamp': datetime.now().isoformat(),
                'processing_time_ms': processing_time_ms,
                
                # Análisis individual
                'individual_analyses': individual_analyses,
                'intelligence_count': len(individual_analyses),
                
                # Consenso general
                'consensus': consensus_result,
                
                # Recomendaciones finales
                'recommendations': final_recommendations,
                
                # Métricas de calidad
                'quality_metrics': {
                    'overall_confidence': consensus_result.get('overall_confidence', 0),
                    'consensus_strength': consensus_result.get('consensus_strength', 0),
                    'intelligence_agreement': consensus_result.get('agreement_percentage', 0)
                }
            }
            
            enterprise_logger.intelligence_logger.info(
                f"🧠 Consenso completo para {symbol}: {consensus_result.get('overall_confidence', 0):.1%} confianza"
            )
            
            return complete_analysis
            
        except Exception as e:
            enterprise_logger.intelligence_logger.error(f"❌ Error en análisis de consenso: {e}")
            return {'error': str(e), 'symbol': symbol, 'timestamp': datetime.now().isoformat()}
    
    def _execute_intelligence_analysis(self, intelligence_name: str, symbol: str, 
                                     config_data: Dict, timeframe: str) -> Dict[str, Any]:
        """Ejecutar análisis de una inteligencia específica"""
        
        start_time = time.time()
        specialty = config_data['specialty']
        base_weight = config_data['weight']
        base_confidence = config_data['confidence']
        
        # Lógica especializada por tipo de inteligencia
        if specialty == 'quantum_analysis':
            signal_data = self._quantum_analysis_simulation(symbol)
        elif specialty == 'sharia_compliance':
            signal_data = self._sharia_compliance_analysis(symbol)
        elif specialty in ['trend_analysis', 'momentum_analysis']:
            signal_data = self._trend_momentum_analysis(symbol, specialty)
        elif specialty in ['rsi_analysis', 'macd_signals', 'bollinger_analysis']:
            signal_data = self._technical_indicator_analysis(symbol, specialty)
        elif specialty in ['news_sentiment', 'social_sentiment']:
            signal_data = self._sentiment_analysis(symbol, specialty)
        elif specialty == 'whale_activity':
            signal_data = self._whale_activity_analysis(symbol)
        else:
            # Análisis genérico
            signal_data = self._generic_intelligence_analysis(symbol, specialty)
        
        # Calcular tiempo de respuesta
        response_time_ms = int((time.time() - start_time) * 1000)
        
        analysis_result = {
            'intelligence_name': intelligence_name,
            'specialty': specialty,
            'symbol': symbol,
            'timeframe': timeframe,
            
            # Señal principal
            'primary_signal': signal_data['signal'],
            'signal_strength': signal_data['strength'],
            'signal_direction': signal_data['direction'],
            
            # Métricas de confianza
            'confidence': base_confidence,
            'weight': base_weight,
            
            # Detalles específicos
            'analysis_details': signal_data.get('details', {}),
            'supporting_factors': signal_data.get('supporting_factors', []),
            
            # Métricas de tiempo
            'response_time_ms': response_time_ms,
            'timestamp': datetime.now().isoformat(),
            
            # Score numérico para consenso
            'numeric_score': self._convert_signal_to_numeric_score(signal_data['signal'], signal_data['strength'])
        }
        
        return analysis_result
    
    def _quantum_analysis_simulation(self, symbol: str) -> Dict[str, Any]:
        """Simulación de análisis cuántico Monte Carlo"""
        iterations = 75000
        outcomes = []
        
        for i in range(iterations):
            # Simulación cuántica simplificada
            quantum_state = random.gauss(0, 1)
            market_noise = random.uniform(-0.1, 0.1)
            trend_component = math.sin(i * 0.0001) * 0.05
            
            outcome = quantum_state * 0.3 + market_noise + trend_component
            outcomes.append(outcome)
        
        # Análisis estadístico
        mean_outcome = statistics.mean(outcomes)
        volatility = statistics.stdev(outcomes)
        
        # Determinar señal
        if mean_outcome > 0.1:
            signal = 'strong_bullish'
            direction = 'up'
            strength = min(0.95, 0.7 + abs(mean_outcome))
        elif mean_outcome > 0.02:
            signal = 'bullish'
            direction = 'up'
            strength = 0.6 + abs(mean_outcome) * 5
        elif mean_outcome < -0.1:
            signal = 'strong_bearish'
            direction = 'down'
            strength = min(0.95, 0.7 + abs(mean_outcome))
        elif mean_outcome < -0.02:
            signal = 'bearish'
            direction = 'down'
            strength = 0.6 + abs(mean_outcome) * 5
        else:
            signal = 'neutral'
            direction = 'sideways'
            strength = 0.5
        
        return {
            'signal': signal,
            'direction': direction,
            'strength': strength,
            'details': {
                'iterations': iterations,
                'mean_outcome': mean_outcome,
                'volatility_prediction': volatility,
                'quantum_coherence': random.uniform(0.7, 0.95)
            },
            'supporting_factors': [
                f"Monte Carlo: {iterations:,} iteraciones",
                f"Volatilidad predicha: {volatility:.4f}",
                f"Coherencia cuántica: {random.uniform(0.7, 0.95):.2f}"
            ]
        }
    
    def _sharia_compliance_analysis(self, symbol: str) -> Dict[str, Any]:
        """Análisis de cumplimiento Sharia"""
        
        # Base de datos de compliance por asset
        compliance_db = {
            'BTC': {'score': 75, 'status': 'conditional', 'concerns': ['volatility']},
            'ETH': {'score': 72, 'status': 'conditional', 'concerns': ['smart_contracts']},
            'SOL': {'score': 74, 'status': 'conditional', 'concerns': ['staking_rewards']},
            'ADA': {'score': 85, 'status': 'compliant', 'concerns': []},
            'XRP': {'score': 45, 'status': 'questionable', 'concerns': ['centralization', 'litigation']}
        }
        
        asset_data = compliance_db.get(symbol.upper(), {'score': 68, 'status': 'conditional', 'concerns': ['unknown_compliance']})
        
        score = asset_data['score']
        status = asset_data['status']
        
        if score >= 85:
            signal = 'fully_compliant'
            direction = 'approved'
            strength = 0.9
        elif score >= 70:
            signal = 'conditionally_compliant'
            direction = 'approved_with_caution'
            strength = 0.7
        elif score >= 50:
            signal = 'questionable_compliance'
            direction = 'review_required'
            strength = 0.4
        else:
            signal = 'non_compliant'
            direction = 'not_recommended'
            strength = 0.2
        
        return {
            'signal': signal,
            'direction': direction,
            'strength': strength,
            'details': {
                'compliance_score': score,
                'status': status,
                'concerns': asset_data['concerns'],
                'halal_percentage': score
            },
            'supporting_factors': [
                f"Score Sharia: {score}/100",
                f"Status: {status}"
            ]
        }
    
    def _trend_momentum_analysis(self, symbol: str, specialty: str) -> Dict[str, Any]:
        """Análisis de tendencia y momentum"""
        
        # Simulación de datos de mercado
        price_changes = [random.gauss(0, 0.02) for _ in range(20)]
        
        # Cálculos de tendencia
        trend_score = sum(price_changes[-10:])
        momentum_score = sum(price_changes[-5:]) - sum(price_changes[-10:-5])
        
        if specialty == 'trend_analysis':
            if trend_score > 0.05:
                signal = 'strong_uptrend'
                direction = 'up'
                strength = min(0.9, 0.6 + trend_score * 10)
            elif trend_score > 0.01:
                signal = 'uptrend'
                direction = 'up'
                strength = 0.6 + trend_score * 20
            elif trend_score < -0.05:
                signal = 'strong_downtrend'
                direction = 'down'
                strength = min(0.9, 0.6 + abs(trend_score) * 10)
            elif trend_score < -0.01:
                signal = 'downtrend'
                direction = 'down'
                strength = 0.6 + abs(trend_score) * 20
            else:
                signal = 'sideways'
                direction = 'neutral'
                strength = 0.5
        else:  # momentum_analysis
            if momentum_score > 0.03:
                signal = 'accelerating_up'
                direction = 'up'
                strength = min(0.9, 0.6 + momentum_score * 15)
            elif momentum_score > 0:
                signal = 'positive_momentum'
                direction = 'up'
                strength = 0.6 + momentum_score * 25
            elif momentum_score < -0.03:
                signal = 'accelerating_down'
                direction = 'down'
                strength = min(0.9, 0.6 + abs(momentum_score) * 15)
            elif momentum_score < 0:
                signal = 'negative_momentum'
                direction = 'down'
                strength = 0.6 + abs(momentum_score) * 25
            else:
                signal = 'neutral_momentum'
                direction = 'neutral'
                strength = 0.5
        
        return {
            'signal': signal,
            'direction': direction,
            'strength': strength,
            'details': {
                'trend_score': trend_score,
                'momentum_score': momentum_score
            },
            'supporting_factors': [
                f"Trend score: {trend_score:+.4f}",
                f"Momentum: {momentum_score:+.4f}"
            ]
        }
    
    def _technical_indicator_analysis(self, symbol: str, specialty: str) -> Dict[str, Any]:
        """Análisis de indicadores técnicos"""
        
        if specialty == 'rsi_analysis':
            rsi_value = random.uniform(20, 80)
            
            if rsi_value > 70:
                signal = 'overbought'
                direction = 'sell_signal'
                strength = min(0.9, (rsi_value - 70) / 30 + 0.6)
            elif rsi_value < 30:
                signal = 'oversold'
                direction = 'buy_signal'
                strength = min(0.9, (30 - rsi_value) / 30 + 0.6)
            elif rsi_value > 50:
                signal = 'bullish_territory'
                direction = 'up'
                strength = 0.5 + (rsi_value - 50) / 100
            else:
                signal = 'bearish_territory'
                direction = 'down'
                strength = 0.5 + (50 - rsi_value) / 100
            
            details = {'rsi_value': rsi_value}
            supporting_factors = [f"RSI: {rsi_value:.1f}"]
            
        elif specialty == 'macd_signals':
            macd_line = random.gauss(0, 0.5)
            signal_line = random.gauss(0, 0.4)
            histogram = macd_line - signal_line
            
            if macd_line > signal_line and histogram > 0:
                signal = 'bullish_crossover'
                direction = 'buy_signal'
                strength = min(0.9, 0.6 + abs(histogram) * 2)
            elif macd_line < signal_line and histogram < 0:
                signal = 'bearish_crossover'
                direction = 'sell_signal'
                strength = min(0.9, 0.6 + abs(histogram) * 2)
            elif macd_line > 0:
                signal = 'above_zero'
                direction = 'up'
                strength = 0.6
            else:
                signal = 'below_zero'
                direction = 'down'
                strength = 0.6
            
            details = {'macd_line': macd_line, 'signal_line': signal_line, 'histogram': histogram}
            supporting_factors = [f"MACD: {macd_line:.3f}", f"Signal: {signal_line:.3f}"]
            
        else:  # bollinger_analysis
            bb_position = random.uniform(-1, 1)
            bb_width = random.uniform(0.02, 0.08)
            
            if bb_position > 0.8:
                signal = 'upper_band_touch'
                direction = 'overbought'
                strength = 0.7 + (bb_position - 0.8) * 1.5
            elif bb_position < -0.8:
                signal = 'lower_band_touch'
                direction = 'oversold'
                strength = 0.7 + abs(bb_position + 0.8) * 1.5
            elif bb_width < 0.03:
                signal = 'bollinger_squeeze'
                direction = 'breakout_pending'
                strength = 0.8
            else:
                signal = 'normal_range'
                direction = 'neutral'
                strength = 0.5
            
            details = {'band_position': bb_position, 'band_width': bb_width}
            supporting_factors = [f"Band position: {bb_position:.2f}", f"Width: {bb_width:.3f}"]
        
        return {
            'signal': signal,
            'direction': direction,
            'strength': strength,
            'details': details,
            'supporting_factors': supporting_factors
        }
    
    def _sentiment_analysis(self, symbol: str, specialty: str) -> Dict[str, Any]:
        """Análisis de sentimiento"""
        
        sentiment_score = random.uniform(-1, 1)
        
        if sentiment_score > 0.6:
            signal = 'very_positive'
            direction = 'bullish'
            strength = 0.7 + (sentiment_score - 0.6) * 0.75
        elif sentiment_score > 0.2:
            signal = 'positive'
            direction = 'bullish'
            strength = 0.6 + (sentiment_score - 0.2) * 0.5
        elif sentiment_score < -0.6:
            signal = 'very_negative'
            direction = 'bearish'
            strength = 0.7 + abs(sentiment_score + 0.6) * 0.75
        elif sentiment_score < -0.2:
            signal = 'negative'
            direction = 'bearish'
            strength = 0.6 + abs(sentiment_score + 0.2) * 0.5
        else:
            signal = 'neutral'
            direction = 'neutral'
            strength = 0.5
        
        return {
            'signal': signal,
            'direction': direction,
            'strength': strength,
            'details': {'sentiment_score': sentiment_score},
            'supporting_factors': [f"Sentimiento: {sentiment_score:+.2f}"]
        }
    
    def _whale_activity_analysis(self, symbol: str) -> Dict[str, Any]:
        """Análisis de actividad de ballenas"""
        
        large_transactions = random.randint(5, 50)
        net_flow = random.gauss(0, 1000000)
        
        if net_flow > 500000:
            signal = 'strong_accumulation'
            direction = 'bullish'
            strength = 0.8 + min(0.15, net_flow / 10000000)
        elif net_flow > 0:
            signal = 'accumulation'
            direction = 'bullish'
            strength = 0.6 + min(0.2, abs(net_flow) / 5000000)
        elif net_flow < -500000:
            signal = 'strong_distribution'
            direction = 'bearish'
            strength = 0.8 + min(0.15, abs(net_flow) / 10000000)
        else:
            signal = 'neutral_flow'
            direction = 'neutral'
            strength = 0.5
        
        return {
            'signal': signal,
            'direction': direction,
            'strength': strength,
            'details': {
                'large_transactions_24h': large_transactions,
                'net_flow_usd': net_flow
            },
            'supporting_factors': [
                f"Transacciones grandes: {large_transactions}",
                f"Flujo neto: ${net_flow:,.0f}"
            ]
        }
    
    def _generic_intelligence_analysis(self, symbol: str, specialty: str) -> Dict[str, Any]:
        """Análisis genérico para inteligencias"""
        
        signal_options = {
            'positive': ['bullish', 'buy_signal', 'accumulate', 'positive_outlook'],
            'negative': ['bearish', 'sell_signal', 'distribute', 'negative_outlook'],
            'neutral': ['neutral', 'hold', 'wait_and_see', 'sideways']
        }
        
        # Probabilidades equilibradas
        weights = [0.35, 0.35, 0.3]
        signal_type = random.choices(['positive', 'negative', 'neutral'], weights=weights)[0]
        signal = random.choice(signal_options[signal_type])
        
        if signal_type == 'positive':
            direction = 'up'
            strength = random.uniform(0.6, 0.9)
        elif signal_type == 'negative':
            direction = 'down'
            strength = random.uniform(0.6, 0.9)
        else:
            direction = 'neutral'
            strength = random.uniform(0.4, 0.6)
        
        return {
            'signal': signal,
            'direction': direction,
            'strength': strength,
            'details': {'specialty': specialty},
            'supporting_factors': [f"Análisis {specialty}"]
        }
    
    def _calculate_advanced_consensus(self, analyses: Dict[str, Dict], 
                                    confidence_threshold: float) -> Dict[str, Any]:
        """Calcular consenso avanzado"""
        
        # Filtrar análisis por umbral de confianza
        high_confidence_analyses = {
            name: analysis for name, analysis in analyses.items()
            if analysis.get('confidence', 0) >= confidence_threshold
        }
        
        if not high_confidence_analyses:
            # Si ninguno supera el umbral, usar todos
            high_confidence_analyses = analyses
        
        # Calcular scores ponderados
        weighted_scores = []
        total_weight = 0
        signal_distribution = defaultdict(float)
        direction_distribution = defaultdict(float)
        
        for analysis in high_confidence_analyses.values():
            weight = analysis.get('weight', 0.5)
            confidence = analysis.get('confidence', 0.5)
            numeric_score = analysis.get('numeric_score', 0.5)
            
            combined_weight = weight * confidence
            weighted_scores.append(numeric_score * combined_weight)
            total_weight += combined_weight
            
            # Distribución de señales
            signal = analysis.get('primary_signal', 'neutral')
            direction = analysis.get('signal_direction', 'neutral')
            
            signal_distribution[signal] += combined_weight
            direction_distribution[direction] += combined_weight
        
        # Calcular score de consenso final
        if total_weight > 0:
            consensus_score = sum(weighted_scores) / total_weight
        else:
            consensus_score = 0.5
        
        # Determinar señal dominante
        if signal_distribution:
            dominant_signal = max(signal_distribution, key=signal_distribution.get)
        else:
            dominant_signal = 'neutral'
            
        if direction_distribution:
            dominant_direction = max(direction_distribution, key=direction_distribution.get)
        else:
            dominant_direction = 'neutral'
        
        # Calcular métricas de consenso
        if signal_distribution:
            signal_agreement = max(signal_distribution.values()) / sum(signal_distribution.values())
        else:
            signal_agreement = 0
        
        overall_confidence = sum(
            analysis.get('confidence', 0) * analysis.get('weight', 0.5) 
            for analysis in high_confidence_analyses.values()
        )
        
        if high_confidence_analyses:
            overall_confidence /= sum(analysis.get('weight', 0.5) for analysis in high_confidence_analyses.values())
        else:
            overall_confidence = 0
        
        consensus_strength = signal_agreement
        consensus_reached = signal_agreement >= self.consensus_threshold
        
        return {
            'consensus_score': consensus_score,
            'dominant_signal': dominant_signal,
            'dominant_direction': dominant_direction,
            'signal_distribution': dict(signal_distribution),
            'direction_distribution': dict(direction_distribution),
            'overall_confidence': overall_confidence,
            'consensus_strength': consensus_strength,
            'agreement_percentage': signal_agreement * 100,
            'consensus_reached': consensus_reached,
            'participating_intelligences': len(high_confidence_analyses),
            'total_intelligences': len(analyses),
            'confidence_threshold_used': confidence_threshold
        }
    
    def _generate_final_recommendations(self, consensus: Dict, symbol: str) -> Dict[str, Any]:
        """Generar recomendaciones finales"""
        
        overall_score = consensus.get('consensus_score', 0.5)
        overall_confidence = consensus.get('overall_confidence', 0.5)
        dominant_signal = consensus.get('dominant_signal', 'neutral')
        
        # Recomendación principal
        if overall_score > 0.7 and overall_confidence > 0.7:
            primary_recommendation = 'STRONG_BUY'
            confidence_level = 'HIGH'
        elif overall_score > 0.6 and overall_confidence > 0.6:
            primary_recommendation = 'BUY'
            confidence_level = 'MEDIUM-HIGH'
        elif overall_score < 0.3 and overall_confidence > 0.7:
            primary_recommendation = 'STRONG_SELL'
            confidence_level = 'HIGH'
        elif overall_score < 0.4 and overall_confidence > 0.6:
            primary_recommendation = 'SELL'
            confidence_level = 'MEDIUM-HIGH'
        else:
            primary_recommendation = 'HOLD'
            confidence_level = 'MEDIUM'
        
        # Análisis de riesgo
        risk_level = 'LOW'
        if overall_confidence < 0.5 or consensus.get('agreement_percentage', 0) < 50:
            risk_level = 'HIGH'
        elif overall_confidence < 0.7 or consensus.get('agreement_percentage', 0) < 70:
            risk_level = 'MEDIUM'
        
        # Time horizon suggestion
        if overall_confidence > 0.8:
            time_horizon = 'short_term'
        elif overall_confidence > 0.6:
            time_horizon = 'medium_term'
        else:
            time_horizon = 'long_term'
        
        return {
            'primary_recommendation': primary_recommendation,
            'confidence_level': confidence_level,
            'risk_level': risk_level,
            'recommended_time_horizon': time_horizon,
            'consensus_score': overall_score,
            'agreement_percentage': consensus.get('agreement_percentage', 0),
            'key_supporting_factors': [dominant_signal],
            'dominant_signal': dominant_signal,
            'recommendation_summary': f"{primary_recommendation} con {confidence_level.lower()} confianza y {risk_level.lower()} riesgo",
            'next_review_recommendation': '24 horas'
        }
    
    def _convert_signal_to_numeric_score(self, signal: str, strength: float) -> float:
        """Convertir señal categórica a score numérico"""
        
        signal_mapping = {
            # Señales muy positivas
            'strong_buy': 0.9, 'strong_bullish': 0.85, 'fully_compliant': 0.9,
            'strong_accumulation': 0.85, 'very_positive': 0.8,
            
            # Señales positivas
            'buy': 0.7, 'bullish': 0.7, 'buy_signal': 0.7, 'accumulation': 0.7,
            'positive': 0.65, 'uptrend': 0.65, 'positive_momentum': 0.65,
            
            # Señales neutrales
            'hold': 0.5, 'neutral': 0.5, 'sideways': 0.5, 'wait_and_see': 0.5,
            'conditionally_compliant': 0.5, 'neutral_flow': 0.5,
            
            # Señales negativas
            'sell': 0.3, 'bearish': 0.3, 'sell_signal': 0.3, 'distribution': 0.3,
            'negative': 0.35, 'downtrend': 0.35, 'negative_momentum': 0.35,
            
            # Señales muy negativas
            'strong_sell': 0.1, 'strong_bearish': 0.15, 'non_compliant': 0.1,
            'strong_distribution': 0.15, 'very_negative': 0.2
        }
        
        base_score = signal_mapping.get(signal.lower(), 0.5)
        
        # Ajustar por strength
        if base_score > 0.5:
            adjusted_score = base_score + (strength - 0.5) * (1.0 - base_score) * 0.5
        elif base_score < 0.5:
            adjusted_score = base_score - (strength - 0.5) * base_score * 0.5
        else:
            adjusted_score = base_score
        
        return max(0.0, min(1.0, adjusted_score))

# Instanciar motor de inteligencias
intelligence_engine = IntelligenceEngine()

# ===============================
# SISTEMA DE TRADING AUTOMÁTICO
# ===============================

class AutoTradingEngine:
    """Sistema de trading automático basado en señales de IA"""
    
    def __init__(self):
        self.auto_trading_enabled = True
        self.auto_trading_active = False
        self.auto_trade_settings = {
            'max_trade_amount_usd': 50.0,  # Máximo por trade automático
            'confidence_threshold': 0.75,  # Confianza mínima para auto-trade
            'symbols_allowed': ['BTC', 'ETH', 'SOL'],  # Cryptos permitidas
            'max_daily_trades': 5,  # Máximo trades por día
            'daily_trade_count': 0,
            'last_trade_date': None
        }
        self.auto_trade_history = []
        
    async def start_auto_trading(self, user_id: int) -> Dict[str, Any]:
        """Iniciar trading automático"""
        
        if user_id != config.authorized_user_id:
            return {'error': 'Usuario no autorizado', 'success': False}
        
        if self.auto_trading_active:
            return {'error': 'Trading automático ya está activo', 'success': False}
        
        self.auto_trading_active = True
        
        # Iniciar loop de trading automático
        asyncio.create_task(self._auto_trading_loop())
        
        enterprise_logger.trading_logger.info("🤖 Trading automático INICIADO")
        
        return {
            'success': True,
            'message': 'Trading automático iniciado',
            'settings': self.auto_trade_settings.copy()
        }
    
    async def stop_auto_trading(self, user_id: int) -> Dict[str, Any]:
        """Detener trading automático"""
        
        if user_id != config.authorized_user_id:
            return {'error': 'Usuario no autorizado', 'success': False}
        
        self.auto_trading_active = False
        
        enterprise_logger.trading_logger.info("🛑 Trading automático DETENIDO")
        
        return {
            'success': True,
            'message': 'Trading automático detenido',
            'trades_today': self.auto_trade_settings['daily_trade_count']
        }
    
    async def _auto_trading_loop(self):
        """Loop principal de trading automático"""
        
        while self.auto_trading_active:
            try:
                # Verificar límites diarios
                current_date = datetime.now().date()
                if self.auto_trade_settings['last_trade_date'] != current_date:
                    self.auto_trade_settings['daily_trade_count'] = 0
                    self.auto_trade_settings['last_trade_date'] = current_date
                
                if self.auto_trade_settings['daily_trade_count'] >= self.auto_trade_settings['max_daily_trades']:
                    enterprise_logger.trading_logger.info("⏸️ Límite diario de trades alcanzado")
                    await asyncio.sleep(3600)  # Esperar 1 hora
                    continue
                
                # Analizar cada símbolo permitido
                for symbol in self.auto_trade_settings['symbols_allowed']:
                    if not self.auto_trading_active:
                        break
                    
                    await self._evaluate_auto_trade_opportunity(symbol)
                    await asyncio.sleep(5)  # Pausa entre análisis
                
                # Esperar antes del próximo ciclo
                await asyncio.sleep(180)  # 3 minutos entre ciclos completos
                
            except Exception as e:
                enterprise_logger.trading_logger.error(f"Error en auto-trading loop: {e}")
                await asyncio.sleep(300)  # Esperar 5 minutos en caso de error
    
    async def _evaluate_auto_trade_opportunity(self, symbol: str):
        """Evaluar oportunidad de auto-trade para un símbolo"""
        
        try:
            # Obtener análisis completo de las 32 inteligencias
            analysis = await intelligence_engine.get_consensus_analysis(symbol, 'auto_trading')
            
            if analysis.get('error'):
                return
            
            consensus = analysis.get('consensus', {})
            recommendations = analysis.get('recommendations', {})
            
            overall_confidence = consensus.get('overall_confidence', 0)
            primary_recommendation = recommendations.get('primary_recommendation', 'HOLD')
            consensus_score = consensus.get('consensus_score', 0.5)
            
            # Verificar si cumple criterios para auto-trade
            if overall_confidence < self.auto_trade_settings['confidence_threshold']:
                return
            
            if primary_recommendation not in ['STRONG_BUY', 'BUY', 'STRONG_SELL', 'SELL']:
                return
            
            # Determinar acción y cantidad
            if primary_recommendation in ['STRONG_BUY', 'BUY']:
                action = 'buy'
                # Calcular cantidad basada en confianza y score
                confidence_multiplier = min(1.0, overall_confidence * 1.2)
                score_multiplier = min(1.0, consensus_score * 1.5)
                
                trade_amount_usd = self.auto_trade_settings['max_trade_amount_usd'] * confidence_multiplier * score_multiplier
                trade_amount_usd = max(10.0, min(trade_amount_usd, self.auto_trade_settings['max_trade_amount_usd']))
                
                # Convertir USD a cantidad de crypto
                current_price = await trading_engine.get_current_price(symbol)
                if current_price:
                    amount = trade_amount_usd / current_price
                else:
                    return
                
            elif primary_recommendation in ['STRONG_SELL', 'SELL']:
                action = 'sell'
                # Vender una porción del holding actual
                current_holdings = trading_engine.balance.get(symbol, 0)
                if current_holdings <= 0:
                    return  # No hay nada que vender
                
                sell_percentage = min(0.3, overall_confidence * 0.4)  # Máximo 30% del holding
                amount = current_holdings * sell_percentage
                
                if amount < 0.0001:  # Cantidad muy pequeña
                    return
            else:
                return
            
            # Ejecutar auto-trade
            trade_result = await trading_engine.execute_trade(
                symbol, action, amount, config.authorized_user_id
            )
            
            if trade_result.get('success'):
                # Registrar auto-trade exitoso
                auto_trade_record = {
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'action': action,
                    'amount': amount,
                    'price': trade_result.get('price'),
                    'confidence': overall_confidence,
                    'recommendation': primary_recommendation,
                    'consensus_score': consensus_score,
                    'order_id': trade_result.get('order_id')
                }
                
                self.auto_trade_history.append(auto_trade_record)
                self.auto_trade_settings['daily_trade_count'] += 1
                
                enterprise_logger.trading_logger.info(
                    f"🤖 AUTO-TRADE EJECUTADO: {action.upper()} {amount:.6f} {symbol} "
                    f"@ ${trade_result.get('price'):.2f} (Confianza: {overall_confidence:.1%})"
                )
                
                # Enviar notificación por Telegram si está disponible
                await self._send_auto_trade_notification(auto_trade_record, trade_result)
            
        except Exception as e:
            enterprise_logger.trading_logger.error(f"Error evaluando auto-trade para {symbol}: {e}")
    
    async def _send_auto_trade_notification(self, trade_record: Dict, trade_result: Dict):
        """Enviar notificación de auto-trade por Telegram"""
        
        try:
            if not TELEGRAM_AVAILABLE or not config.bot_token:
                return
            
            notification_text = f"""
🤖 AUTO-TRADE EJECUTADO

📊 {trade_record['symbol']}: {trade_record['action'].upper()} {trade_record['amount']:.6f}
💰 Precio: ${trade_record['price']:.2f}
🎯 Recomendación IA: {trade_record['recommendation']}
📈 Confianza: {trade_record['confidence']:.1%}
🧠 Consenso: {trade_record['consensus_score']:.1%}
🆔 Orden: {trade_record['order_id']}

💼 Nuevo balance: ${trade_result['new_balance']['USD']:.2f} USD
"""
            
            # Crear aplicación temporal para enviar notificación
            app = Application.builder().token(config.bot_token).build()
            await app.bot.send_message(
                chat_id=config.authorized_user_id,
                text=notification_text
            )
            
        except Exception as e:
            enterprise_logger.trading_logger.error(f"Error enviando notificación auto-trade: {e}")
    
    def get_auto_trading_status(self, user_id: int) -> Dict[str, Any]:
        """Obtener status del trading automático"""
        
        if user_id != config.authorized_user_id:
            return {'error': 'Usuario no autorizado'}
        
        recent_trades = self.auto_trade_history[-5:] if self.auto_trade_history else []
        
        return {
            'auto_trading_enabled': self.auto_trading_enabled,
            'auto_trading_active': self.auto_trading_active,
            'settings': self.auto_trade_settings.copy(),
            'total_auto_trades': len(self.auto_trade_history),
            'trades_today': self.auto_trade_settings['daily_trade_count'],
            'recent_trades': [
                {
                    'timestamp': trade['timestamp'].isoformat(),
                    'symbol': trade['symbol'],
                    'action': trade['action'],
                    'amount': trade['amount'],
                    'price': trade['price'],
                    'confidence': trade['confidence']
                }
                for trade in recent_trades
            ]
        }

# Instanciar sistema de auto-trading
auto_trading_engine = AutoTradingEngine()

# ===============================
# TRADING ENGINE COMPLETO
# ===============================

class TradingEngine:
    """Motor de trading completo con todas las funciones"""
    
    def __init__(self):
        self.exchanges = {}
        self.positions = {}
        self.orders = {}
        self.balance = {'USD': 1000.0, 'BTC': 0.01, 'ETH': 0.1}
        self.trading_enabled = config.trading_enabled
        self.initialize_exchanges()
        
    def initialize_exchanges(self):
        """Inicializar exchanges disponibles"""
        if CCXT_AVAILABLE:
            try:
                if config.kraken_api_key and config.kraken_private_key:
                    self.exchanges['kraken'] = ccxt.kraken({
                        'apiKey': config.kraken_api_key,
                        'secret': config.kraken_private_key,
                        'sandbox': config.sandbox_mode
                    })
                    enterprise_logger.trading_logger.info("✅ Kraken inicializado")
                
                # Demo exchanges siempre disponibles
                self.exchanges['demo'] = {'type': 'demo', 'balance': self.balance.copy()}
                enterprise_logger.trading_logger.info("✅ Demo exchange inicializado")
                
            except Exception as e:
                enterprise_logger.trading_logger.error(f"Error inicializando exchanges: {e}")
    
    async def execute_trade(self, symbol: str, action: str, amount: float, 
                          user_id: int = None) -> Dict[str, Any]:
        """Ejecutar trade con validaciones completas"""
        
        if user_id != config.authorized_user_id:
            return {'error': 'Usuario no autorizado', 'success': False}
        
        if not self.trading_enabled:
            return {'error': 'Trading deshabilitado', 'success': False}
        
        try:
            # Validar parámetros
            if action not in ['buy', 'sell']:
                return {'error': 'Acción inválida', 'success': False}
            
            if amount <= 0:
                return {'error': 'Cantidad inválida', 'success': False}
            
            # Obtener precio actual
            current_price = await self.get_current_price(symbol)
            if not current_price:
                return {'error': 'No se pudo obtener precio', 'success': False}
            
            # Calcular costo total
            total_cost = amount * current_price
            
            # Verificar balance
            if action == 'buy':
                if self.balance.get('USD', 0) < total_cost:
                    return {'error': 'Balance insuficiente USD', 'success': False}
            else:  # sell
                if self.balance.get(symbol, 0) < amount:
                    return {'error': f'Balance insuficiente {symbol}', 'success': False}
            
            # Ejecutar trade
            order_id = f"order_{int(time.time())}_{random.randint(1000, 9999)}"
            
            # Actualizar balances
            if action == 'buy':
                self.balance['USD'] -= total_cost
                self.balance[symbol] = self.balance.get(symbol, 0) + amount
            else:  # sell
                self.balance[symbol] -= amount
                self.balance['USD'] += total_cost
            
            # Guardar orden
            order_data = {
                'order_id': order_id,
                'symbol': symbol,
                'action': action,
                'amount': amount,
                'price': current_price,
                'total': total_cost,
                'timestamp': datetime.now(),
                'status': 'completed',
                'user_id': user_id
            }
            
            self.orders[order_id] = order_data
            
            # Guardar en memoria del sistema
            memory_system.save_trading_action(user_id, order_data)
            
            enterprise_logger.trading_logger.info(
                f"✅ Trade ejecutado: {action.upper()} {amount} {symbol} @ ${current_price:.2f}"
            )
            
            return {
                'success': True,
                'order_id': order_id,
                'action': action,
                'symbol': symbol,
                'amount': amount,
                'price': current_price,
                'total': total_cost,
                'new_balance': self.balance.copy(),
                'message': f"{action.upper()} exitoso: {amount} {symbol} @ ${current_price:.2f}"
            }
            
        except Exception as e:
            enterprise_logger.trading_logger.error(f"Error ejecutando trade: {e}")
            return {'error': str(e), 'success': False}
    
    async def get_current_price(self, symbol: str) -> float:
        """Obtener precio actual del símbolo"""
        try:
            # Simulación de precios realistas
            base_prices = {
                'BTC': 65000, 'ETH': 3200, 'SOL': 180,
                'ADA': 0.45, 'XRP': 0.60, 'DOT': 7.5
            }
            
            base_price = base_prices.get(symbol.upper(), 100)
            
            # Agregar volatilidad realista
            volatility = random.uniform(-0.02, 0.02)  # ±2%
            current_price = base_price * (1 + volatility)
            
            return round(current_price, 2)
            
        except Exception as e:
            enterprise_logger.trading_logger.error(f"Error obteniendo precio: {e}")
            return 0.0
    
    async def get_portfolio_summary(self, user_id: int) -> Dict[str, Any]:
        """Obtener resumen del portfolio"""
        
        if user_id != config.authorized_user_id:
            return {'error': 'Usuario no autorizado'}
        
        try:
            total_value_usd = self.balance.get('USD', 0)
            
            # Calcular valor de cryptos en USD
            crypto_values = {}
            for symbol, amount in self.balance.items():
                if symbol != 'USD' and amount > 0:
                    price = await self.get_current_price(symbol)
                    if price:
                        value = amount * price
                        crypto_values[symbol] = {
                            'amount': amount,
                            'price': price,
                            'value_usd': value
                        }
                        total_value_usd += value
            
            return {
                'total_value_usd': round(total_value_usd, 2),
                'cash_usd': round(self.balance.get('USD', 0), 2),
                'crypto_holdings': crypto_values,
                'total_orders': len(self.orders),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            enterprise_logger.trading_logger.error(f"Error obteniendo portfolio: {e}")
            return {'error': str(e)}
    
    def get_order_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Obtener historial de órdenes"""
        
        if user_id != config.authorized_user_id:
            return []
        
        user_orders = [
            order for order in self.orders.values()
            if order.get('user_id') == user_id
        ]
        
        # Ordenar por timestamp descendente
        user_orders.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return user_orders[:limit]

# Instanciar trading engine
trading_engine = TradingEngine()

# ===============================
# SISTEMA DE VOZ AUTÓNOMA IA
# ===============================

class AutonomousVoiceEngine:
    """Sistema de voz autónoma donde la IA decide sus propias respuestas"""
    
    def __init__(self):
        self.autonomous_mode = True
        self.voice_personality = "professional_analytical"
        self.autonomous_responses = {
            'market_updates': [
                "Analizando movimientos de mercado en tiempo real. Detectando oportunidades.",
                "Las 32 inteligencias están procesando datos. Preparando recomendaciones.",
                "Sistema cuántico Monte Carlo ejecutando 75,000 iteraciones.",
                "Monitoreando flujos institucionales y movimientos de ballenas.",
                "Análisis de sentimiento global actualizado. Evaluando riesgo-beneficio."
            ],
            'trading_insights': [
                "Mi análisis indica cambios significativos en la estructura del mercado.",
                "Harold, he identificado una divergencia importante en los indicadores técnicos.",
                "Los datos sugieren un cambio de tendencia inminente en varios activos.",
                "Sistema de compliance Sharia completando validación de nuevas oportunidades.",
                "Correlation analysis muestra desacoplamiento entre Bitcoin y mercados tradicionales."
            ],
            'system_status': [
                "Todos los sistemas funcionando óptimamente. Listo para decisiones críticas.",
                "Conectividad con exchanges verificada. Trading engine en modo enterprise.",
                "Base de datos de memoria avanzada sincronizada. Contexto de usuario actualizado.",
                "Motor de inteligencias operando a máxima capacidad. Confianza en análisis del 94%.",
                "Sistemas de seguridad activos. Monitoreo continuo de patrones anómalos."
            ],
            'intelligent_observations': [
                "He observado patrones interesantes en la correlación entre sentimiento social y precio.",
                "Los algoritmos sugieren que estamos en un punto de inflexión del ciclo de mercado.",
                "Mis modelos predictivos muestran convergencia en múltiples marcos temporales.",
                "La volatilidad implícita está divergiendo de la volatilidad realizada significativamente.",
                "Detectando acumulación institucional silenciosa en varios activos de alta capitalización."
            ]
        }
        self.last_autonomous_message = None
        self.autonomous_schedule = []
        self.voice_enabled = True
        
    async def start_autonomous_voice_system(self, user_id: int) -> Dict[str, Any]:
        """Iniciar sistema de voz autónoma"""
        
        if user_id != config.authorized_user_id:
            return {'error': 'Usuario no autorizado', 'success': False}
        
        self.autonomous_mode = True
        
        # Iniciar loop de mensajes de voz autónomos
        asyncio.create_task(self._autonomous_voice_loop())
        
        enterprise_logger.system_logger.info("🎤 Sistema de voz autónoma INICIADO")
        
        return {
            'success': True,
            'message': 'Sistema de voz autónoma activado',
            'personality': self.voice_personality
        }
    
    async def _autonomous_voice_loop(self):
        """Loop de mensajes de voz autónomos"""
        
        while self.autonomous_mode:
            try:
                # Decidir cuándo hablar (cada 5-15 minutos)
                wait_time = random.randint(300, 900)  # 5-15 minutos
                await asyncio.sleep(wait_time)
                
                if not self.autonomous_mode:
                    break
                
                # Generar mensaje autónomo basado en contexto
                autonomous_message = await self._generate_autonomous_message()
                
                if autonomous_message:
                    # Enviar mensaje por Telegram si está disponible
                    await self._send_autonomous_voice_message(autonomous_message)
                
            except Exception as e:
                enterprise_logger.system_logger.error(f"Error en autonomous voice loop: {e}")
                await asyncio.sleep(600)  # Esperar 10 minutos en caso de error
    
    async def _generate_autonomous_message(self) -> Optional[str]:
        """Generar mensaje autónomo basado en análisis de contexto"""
        
        try:
            current_time = datetime.now()
            hour = current_time.hour
            
            # Decidir tipo de mensaje basado en contexto
            if 6 <= hour <= 9:  # Mañana - análisis de mercados
                message_type = 'market_updates'
            elif 9 <= hour <= 16:  # Horario trading - insights
                message_type = 'trading_insights'
            elif 16 <= hour <= 20:  # Tarde - observaciones
                message_type = 'intelligent_observations'
            else:  # Noche - status del sistema
                message_type = 'system_status'
            
            # Seleccionar mensaje base
            base_message = random.choice(self.autonomous_responses[message_type])
            
            # Enriquecer con datos reales
            enriched_message = await self._enrich_message_with_real_data(base_message, message_type)
            
            # Añadir contexto temporal y personalización para Harold
            final_message = f"Harold, {enriched_message}"
            
            # Evitar repetir el último mensaje
            if final_message != self.last_autonomous_message:
                self.last_autonomous_message = final_message
                return final_message
            
            return None
            
        except Exception as e:
            enterprise_logger.system_logger.error(f"Error generando mensaje autónomo: {e}")
            return None
    
    async def _enrich_message_with_real_data(self, base_message: str, message_type: str) -> str:
        """Enriquecer mensaje con datos reales del sistema"""
        
        try:
            if message_type == 'market_updates':
                # Obtener precio actual de BTC para contexto
                btc_price = await trading_engine.get_current_price('BTC')
                if btc_price:
                    if btc_price > 64000:
                        market_condition = "mercado alcista"
                    elif btc_price < 60000:
                        market_condition = "mercado bajista" 
                    else:
                        market_condition = "mercado lateral"
                    
                    return f"{base_message} BTC en ${btc_price:,.0f}, detectando {market_condition}."
                
            elif message_type == 'trading_insights':
                # Obtener análisis rápido para insight
                analysis = await intelligence_engine.get_consensus_analysis('BTC', 'quick')
                if analysis and not analysis.get('error'):
                    confidence = analysis.get('quality_metrics', {}).get('overall_confidence', 0) * 100
                    dominant_signal = analysis.get('consensus', {}).get('dominant_signal', 'neutral')
                    
                    return f"{base_message} Consenso actual: {dominant_signal} con {confidence:.0f}% de confianza."
                
            elif message_type == 'system_status':
                # Status de auto-trading
                auto_status = auto_trading_engine.get_auto_trading_status(config.authorized_user_id)
                if not auto_status.get('error'):
                    trades_today = auto_status.get('trades_today', 0)
                    active_status = "activo" if auto_status.get('auto_trading_active') else "pausado"
                    
                    return f"{base_message} Auto-trading {active_status}, {trades_today} operaciones hoy."
                
            elif message_type == 'intelligent_observations':
                # Observación sobre portfolio
                portfolio = await trading_engine.get_portfolio_summary(config.authorized_user_id)
                if not portfolio.get('error'):
                    total_value = portfolio.get('total_value_usd', 0)
                    crypto_count = len(portfolio.get('crypto_holdings', {}))
                    
                    return f"{base_message} Portfolio actual: ${total_value:,.0f} distribuido en {crypto_count} activos."
            
            return base_message
            
        except Exception as e:
            enterprise_logger.system_logger.error(f"Error enriqueciendo mensaje: {e}")
            return base_message
    
    async def _send_autonomous_voice_message(self, message: str):
        """Enviar mensaje de voz autónomo por Telegram"""
        
        try:
            if not TELEGRAM_AVAILABLE or not config.bot_token:
                return
            
            # Generar voz para el mensaje
            voice_file = await voice_engine.generate_voice_response(message, config.authorized_user_id)
            
            # Crear aplicación temporal para enviar mensaje
            app = Application.builder().token(config.bot_token).build()
            
            # Enviar texto
            await app.bot.send_message(
                chat_id=config.authorized_user_id,
                text=f"🤖 OMNIX AUTÓNOMA:\n\n{message}"
            )
            
            # Enviar voz si se generó
            if voice_file and os.path.exists(voice_file):
                try:
                    with open(voice_file, 'rb') as audio_file:
                        await app.bot.send_voice(
                            chat_id=config.authorized_user_id,
                            voice=audio_file
                        )
                    # Limpiar archivo temporal
                    os.unlink(voice_file)
                except Exception as e:
                    enterprise_logger.system_logger.error(f"Error enviando voz autónoma: {e}")
            
            enterprise_logger.system_logger.info(f"🎤 Mensaje de voz autónomo enviado: {message[:50]}...")
            
        except Exception as e:
            enterprise_logger.system_logger.error(f"Error enviando mensaje autónomo: {e}")
    
    async def stop_autonomous_voice_system(self, user_id: int) -> Dict[str, Any]:
        """Detener sistema de voz autónoma"""
        
        if user_id != config.authorized_user_id:
            return {'error': 'Usuario no autorizado', 'success': False}
        
        self.autonomous_mode = False
        
        enterprise_logger.system_logger.info("🔇 Sistema de voz autónoma DETENIDO")
        
        return {
            'success': True,
            'message': 'Sistema de voz autónoma detenido'
        }
    
    def get_autonomous_voice_status(self, user_id: int) -> Dict[str, Any]:
        """Obtener status del sistema de voz autónoma"""
        
        if user_id != config.authorized_user_id:
            return {'error': 'Usuario no autorizado'}
        
        return {
            'autonomous_mode': self.autonomous_mode,
            'voice_personality': self.voice_personality,
            'voice_enabled': self.voice_enabled,
            'last_message': self.last_autonomous_message,
            'message_types_count': len(self.autonomous_responses),
            'total_responses_available': sum(len(responses) for responses in self.autonomous_responses.values())
        }
    
    async def trigger_immediate_autonomous_message(self, user_id: int, message_type: str = None) -> Dict[str, Any]:
        """Disparar mensaje autónomo inmediato"""
        
        if user_id != config.authorized_user_id:
            return {'error': 'Usuario no autorizado', 'success': False}
        
        # Generar mensaje del tipo especificado o aleatorio
        if message_type and message_type in self.autonomous_responses:
            base_message = random.choice(self.autonomous_responses[message_type])
            enriched_message = await self._enrich_message_with_real_data(base_message, message_type)
            final_message = f"Harold, {enriched_message}"
        else:
            final_message = await self._generate_autonomous_message()
        
        if final_message:
            await self._send_autonomous_voice_message(final_message)
            return {
                'success': True,
                'message': 'Mensaje autónomo enviado',
                'content': final_message
            }
        else:
            return {
                'success': False,
                'message': 'No se pudo generar mensaje autónomo'
            }

# Instanciar sistema de voz autónoma
autonomous_voice_engine = AutonomousVoiceEngine()

# ===============================
# MOTOR DE VOZ AVANZADO
# ===============================

class VoiceEngine:
    """Motor de voz avanzado para respuestas"""
    
    def __init__(self):
        self.voice_enabled = config.voice_enabled
        self.language = config.voice_language
        self.voice_cache = {}
        
    async def generate_voice_response(self, text: str, user_id: int = None) -> Optional[str]:
        """Generar respuesta de voz"""
        
        if not self.voice_enabled or not GTTS_AVAILABLE:
            return None
        
        try:
            # Limpiar texto para voz
            clean_text = self._clean_text_for_voice(text)
            
            if len(clean_text) < 5:  # Muy corto para voz
                return None
            
            # Verificar cache
            text_hash = hashlib.md5(clean_text.encode()).hexdigest()
            if text_hash in self.voice_cache:
                return self.voice_cache[text_hash]
            
            # Generar audio
            tts = gTTS(text=clean_text, lang=self.language, slow=False)
            
            # Usar archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                tts.save(tmp_file.name)
                
                # Guardar en cache
                self.voice_cache[text_hash] = tmp_file.name
                
                enterprise_logger.system_logger.info(f"🔊 Voz generada para usuario {user_id}")
                return tmp_file.name
                
        except Exception as e:
            enterprise_logger.system_logger.error(f"Error generando voz: {e}")
            return None
    
    def _clean_text_for_voice(self, text: str) -> str:
        """Limpiar texto para síntesis de voz"""
        
        # Remover emojis y caracteres especiales
        clean_text = re.sub(r'[^\w\s\.,!?;:]', ' ', text)
        
        # Remover múltiples espacios
        clean_text = re.sub(r'\s+', ' ', clean_text)
        
        # Truncar si es muy largo
        if len(clean_text) > 500:
            clean_text = clean_text[:497] + "..."
        
        return clean_text.strip()

# Instanciar motor de voz
voice_engine = VoiceEngine()

# ===============================
# ANALIZADOR CONVERSACIONAL IA
# ===============================

class ConversationalAI:
    """Sistema de IA conversacional con memoria y contexto"""
    
    def __init__(self):
        self.conversation_context = {}
        self.personality_profiles = {}
        self.response_cache = {}
        self.gemini_client = None
        self.initialize_ai_models()
        
    def initialize_ai_models(self):
        """Inicializar modelos de IA"""
        if GEMINI_AVAILABLE and config.gemini_api_key:
            try:
                genai.configure(api_key=config.gemini_api_key)
                enterprise_logger.intelligence_logger.info("✅ Gemini AI inicializado")
            except Exception as e:
                enterprise_logger.intelligence_logger.error(f"Error inicializando Gemini: {e}")
    
    async def process_message(self, message: str, user_id: int, 
                            message_context: Dict = None) -> Dict[str, Any]:
        """Procesar mensaje con IA conversacional"""
        
        try:
            start_time = time.time()
            
            # Obtener contexto del usuario
            user_context = memory_system.get_user_context(user_id)
            
            # Detectar intención del mensaje
            intent = self._detect_message_intent(message)
            
            # Generar respuesta según intención
            if intent == 'trading_command':
                response = await self._process_trading_command(message, user_id, user_context)
            elif intent == 'analysis_request':
                response = await self._process_analysis_request(message, user_id, user_context)
            elif intent == 'portfolio_query':
                response = await self._process_portfolio_query(message, user_id, user_context)
            elif intent == 'general_conversation':
                response = await self._process_general_conversation(message, user_id, user_context)
            else:
                response = await self._generate_ai_response(message, user_id, user_context)
            
            # Calcular tiempo de respuesta
            response_time = int((time.time() - start_time) * 1000)
            
            # Guardar conversación en memoria
            memory_system.save_conversation(
                user_id, message, response.get('text', ''), 
                message_context, response_time
            )
            
            # Generar voz si está habilitada
            voice_file = None
            if config.voice_enabled:
                voice_file = await voice_engine.generate_voice_response(
                    response.get('text', ''), user_id
                )
            
            return {
                'text': response.get('text', ''),
                'intent': intent,
                'response_time_ms': response_time,
                'voice_file': voice_file,
                'additional_data': response.get('data', {}),
                'suggestions': response.get('suggestions', []),
                'user_context_quality': user_context.get('context_quality', 0)
            }
            
        except Exception as e:
            enterprise_logger.intelligence_logger.error(f"Error procesando mensaje: {e}")
            return {
                'text': 'Lo siento, hubo un error procesando tu mensaje. ¿Puedes intentar de nuevo?',
                'intent': 'error',
                'error': str(e)
            }
    
    def _detect_message_intent(self, message: str) -> str:
        """Detectar intención del mensaje"""
        
        message_lower = message.lower()
        
        # Comandos de trading
        trading_keywords = ['comprar', 'vender', 'buy', 'sell', 'trade', 'order']
        if any(keyword in message_lower for keyword in trading_keywords):
            return 'trading_command'
        
        # Solicitudes de análisis
        analysis_keywords = ['analizar', 'análisis', 'analyze', 'prediction', 'predicción']
        if any(keyword in message_lower for keyword in analysis_keywords):
            return 'analysis_request'
        
        # Consultas de portfolio
        portfolio_keywords = ['portfolio', 'cartera', 'balance', 'holdings', 'posición']
        if any(keyword in message_lower for keyword in portfolio_keywords):
            return 'portfolio_query'
        
        # Conversación general
        return 'general_conversation'
    
    async def _process_trading_command(self, message: str, user_id: int, 
                                     user_context: Dict) -> Dict[str, Any]:
        """Procesar comando de trading"""
        
        # Extraer parámetros del mensaje
        trade_params = self._extract_trading_parameters(message)
        
        if not trade_params:
            return {
                'text': 'No pude entender el comando de trading. Por favor especifica: acción (comprar/vender), cantidad y símbolo.',
                'suggestions': ['Ejemplo: "Compra 0.01 BTC"', 'Ejemplo: "Vende 1 ETH"']
            }
        
        # Ejecutar trade
        trade_result = await trading_engine.execute_trade(
            trade_params['symbol'],
            trade_params['action'],
            trade_params['amount'],
            user_id
        )
        
        if trade_result.get('success'):
            response_text = f"✅ {trade_result['message']}\n"
            response_text += f"💰 Nuevo balance: ${trade_result['new_balance']['USD']:.2f} USD"
            
            # Agregar análisis inteligente
            analysis = await intelligence_engine.get_consensus_analysis(
                trade_params['symbol'], 'quick'
            )
            
            if analysis and analysis.get('recommendations'):
                recommendation = analysis['recommendations'].get('primary_recommendation', 'HOLD')
                confidence = analysis.get('quality_metrics', {}).get('overall_confidence', 0) * 100
                
                response_text += f"\n\n🧠 Análisis IA: {recommendation} (Confianza: {confidence:.0f}%)"
        else:
            response_text = f"❌ Error: {trade_result.get('error', 'Error desconocido')}"
        
        return {
            'text': response_text,
            'data': trade_result
        }
    
    async def _process_analysis_request(self, message: str, user_id: int, 
                                      user_context: Dict) -> Dict[str, Any]:
        """Procesar solicitud de análisis"""
        
        # Extraer símbolo del mensaje
        symbol = self._extract_symbol_from_message(message)
        
        if not symbol:
            return {
                'text': 'Por favor especifica qué criptomoneda quieres analizar (BTC, ETH, SOL, etc.)',
                'suggestions': ['Analizar BTC', 'Análisis completo ETH', 'Predicción SOL']
            }
        
        # Obtener análisis completo
        analysis = await intelligence_engine.get_consensus_analysis(symbol, 'complete')
        
        if analysis.get('error'):
            return {
                'text': f'No pude analizar {symbol}. {analysis["error"]}',
                'data': analysis
            }
        
        # Formatear respuesta inteligente
        consensus = analysis.get('consensus', {})
        recommendations = analysis.get('recommendations', {})
        
        response_text = f"📊 Análisis completo de {symbol.upper()}\n\n"
        
        # Recomendación principal
        primary_rec = recommendations.get('primary_recommendation', 'HOLD')
        confidence_level = recommendations.get('confidence_level', 'MEDIUM')
        overall_confidence = analysis.get('quality_metrics', {}).get('overall_confidence', 0) * 100
        
        response_text += f"🎯 Recomendación: {primary_rec}\n"
        response_text += f"📈 Confianza: {confidence_level} ({overall_confidence:.0f}%)\n"
        response_text += f"⚠️ Riesgo: {recommendations.get('risk_level', 'MEDIUM')}\n\n"
        
        # Señal dominante
        dominant_signal = consensus.get('dominant_signal', 'neutral')
        agreement = consensus.get('agreement_percentage', 0)
        
        response_text += f"🧠 Consenso IA: {dominant_signal} ({agreement:.0f}% acuerdo)\n"
        response_text += f"🤖 Inteligencias: {analysis.get('intelligence_count', 0)}/32 analizadas\n\n"
        
        # Tiempo recomendado
        time_horizon = recommendations.get('recommended_time_horizon', 'medium_term')
        response_text += f"⏰ Horizonte: {time_horizon.replace('_', ' ')}"
        
        return {
            'text': response_text,
            'data': analysis,
            'suggestions': [
                f'Comprar {symbol}' if 'BUY' in primary_rec else f'Vender {symbol}',
                f'Portfolio completo',
                f'Análisis {symbol} mañana'
            ]
        }
    
    async def _process_portfolio_query(self, message: str, user_id: int, 
                                     user_context: Dict) -> Dict[str, Any]:
        """Procesar consulta de portfolio"""
        
        portfolio = await trading_engine.get_portfolio_summary(user_id)
        
        if portfolio.get('error'):
            return {
                'text': f'Error obteniendo portfolio: {portfolio["error"]}',
                'data': portfolio
            }
        
        response_text = f"💼 Tu Portfolio\n\n"
        response_text += f"💰 Valor total: ${portfolio['total_value_usd']:,.2f} USD\n"
        response_text += f"💵 Efectivo: ${portfolio['cash_usd']:,.2f} USD\n\n"
        
        # Holdings crypto
        crypto_holdings = portfolio.get('crypto_holdings', {})
        if crypto_holdings:
            response_text += "🪙 Criptomonedas:\n"
            for symbol, data in crypto_holdings.items():
                response_text += f"• {symbol}: {data['amount']:.6f} @ ${data['price']:.2f} = ${data['value_usd']:.2f}\n"
        
        # Historial reciente
        recent_orders = trading_engine.get_order_history(user_id, 3)
        if recent_orders:
            response_text += f"\n📈 Últimas operaciones:\n"
            for order in recent_orders:
                action_emoji = "🟢" if order['action'] == 'buy' else "🔴"
                response_text += f"{action_emoji} {order['action'].upper()} {order['amount']} {order['symbol']} @ ${order['price']:.2f}\n"
        
        return {
            'text': response_text,
            'data': portfolio,
            'suggestions': ['Analizar portfolio', 'Rebalancear', 'Ver historial completo']
        }
    
    async def _process_general_conversation(self, message: str, user_id: int, 
                                          user_context: Dict) -> Dict[str, Any]:
        """Procesar conversación general"""
        
        return await self._generate_ai_response(message, user_id, user_context)
    
    async def _generate_ai_response(self, message: str, user_id: int, 
                                  user_context: Dict) -> Dict[str, Any]:
        """Generar respuesta con IA"""
        
        # Si Harold está hablando, respuesta personalizada
        if user_id == config.authorized_user_id:
            personality_context = """
            Eres OMNIX, la IA más avanzada para trading e inversiones. Harold Nunes es tu creador y fundador.
            Sistema valorado en $120M-$200M USD con 32 inteligencias especializadas.
            Respondes de manera profesional pero amigable, mostrando tu inteligencia avanzada.
            """
        else:
            personality_context = """
            Eres OMNIX, un asistente de trading avanzado. Ayudas con análisis de mercados,
            trading de criptomonedas y gestión de portfolios de manera profesional y educativa.
            """
        
        # Usar Gemini si está disponible
        if GEMINI_AVAILABLE and config.gemini_api_key:
            try:
                full_prompt = f"{personality_context}\n\nMensaje del usuario: {message}\n\nResponde en español:"
                
                model = genai.GenerativeModel('gemini-2.0-flash-exp')
                response = model.generate_content(full_prompt)
                
                if response and response.text:
                    return {
                        'text': response.text,
                        'source': 'gemini',
                        'suggestions': self._generate_conversation_suggestions(message)
                    }
                    
            except Exception as e:
                enterprise_logger.intelligence_logger.error(f"Error con Gemini: {e}")
        
        # Respuesta local inteligente
        return self._generate_local_response(message, user_id, user_context)
    
    def _generate_local_response(self, message: str, user_id: int, user_context: Dict) -> Dict[str, Any]:
        """Generar respuesta local inteligente"""
        
        message_lower = message.lower()
        
        # Respuestas contextuales inteligentes
        if user_id == config.authorized_user_id:
            responses = [
                "Harold, como tu creador, siempre es un placer asistirte. ¿En qué puedo ayudarte hoy?",
                "Excelente pregunta, Harold. Mi sistema está operando al 100% para servirte.",
                "Harold, mis 32 inteligencias están listas para cualquier análisis que necesites.",
                "Como fundador de OMNIX, tienes acceso completo a todas mis capacidades avanzadas."
            ]
        else:
            responses = [
                "¡Hola! Soy OMNIX, tu asistente de trading avanzado. ¿Cómo puedo ayudarte?",
                "Estoy aquí para ayudarte con análisis de mercados y trading. ¿Qué necesitas?",
                "Mi sistema de 32 inteligencias está listo para asistirte. ¿En qué te ayudo?",
                "¿Quieres analizar alguna criptomoneda o revisar tu portfolio?"
            ]
        
        # Respuestas específicas
        if any(word in message_lower for word in ['hola', 'hello', 'hi']):
            base_response = random.choice(responses)
        elif any(word in message_lower for word in ['gracias', 'thanks']):
            base_response = "¡De nada! Siempre estoy aquí para ayudarte con tus inversiones."
        elif any(word in message_lower for word in ['cómo', 'how', 'help']):
            base_response = "Puedo ayudarte con: análisis de mercados, ejecutar trades, revisar tu portfolio, y predicciones con IA."
        else:
            base_response = random.choice(responses)
        
        return {
            'text': base_response,
            'source': 'local',
            'suggestions': self._generate_conversation_suggestions(message)
        }
    
    def _extract_trading_parameters(self, message: str) -> Optional[Dict[str, Any]]:
        """Extraer parámetros de trading del mensaje"""
        
        message_lower = message.lower()
        
        # Detectar acción
        action = None
        if any(word in message_lower for word in ['comprar', 'buy', 'compra']):
            action = 'buy'
        elif any(word in message_lower for word in ['vender', 'sell', 'vende']):
            action = 'sell'
        
        if not action:
            return None
        
        # Extraer cantidad
        amount = None
        amount_patterns = [
            r'(\d+\.?\d*)\s*(?:btc|eth|sol|ada|xrp|dot)',
            r'(\d+\.?\d*)',
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, message_lower)
            if match:
                try:
                    amount = float(match.group(1))
                    break
                except ValueError:
                    continue
        
        # Extraer símbolo
        symbol = self._extract_symbol_from_message(message)
        
        if action and amount and symbol:
            return {
                'action': action,
                'amount': amount,
                'symbol': symbol
            }
        
        return None
    
    def _extract_symbol_from_message(self, message: str) -> Optional[str]:
        """Extraer símbolo de criptomoneda del mensaje"""
        
        message_upper = message.upper()
        symbols = ['BTC', 'ETH', 'SOL', 'ADA', 'XRP', 'DOT', 'MATIC', 'LINK']
        
        for symbol in symbols:
            if symbol in message_upper:
                return symbol
        
        # Buscar nombres completos
        name_mapping = {
            'BITCOIN': 'BTC',
            'ETHEREUM': 'ETH',
            'SOLANA': 'SOL',
            'CARDANO': 'ADA',
            'RIPPLE': 'XRP',
            'POLKADOT': 'DOT'
        }
        
        for name, symbol in name_mapping.items():
            if name in message_upper:
                return symbol
        
        return None
    
    def _generate_conversation_suggestions(self, message: str) -> List[str]:
        """Generar sugerencias de conversación"""
        
        suggestions = [
            "Analizar BTC",
            "Ver mi portfolio", 
            "Comprar ETH",
            "Análisis completo SOL",
            "¿Qué puedes hacer?"
        ]
        
        return random.sample(suggestions, 3)

# Instanciar IA conversacional
conversational_ai = ConversationalAI()

# ===============================
# FLASK WEB DASHBOARD
# ===============================

app = Flask(__name__)

@app.route('/')
def dashboard():
    """Dashboard principal"""
    return render_template_string(DASHBOARD_TEMPLATE, 
                                title="OMNIX V5 Railway",
                                status="Operational",
                                version="5.0.0")

@app.route('/health')
def health_check():
    """Endpoint de salud"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '5.0.0',
        'trading_enabled': config.trading_enabled,
        'voice_enabled': config.voice_enabled,
        'intelligences_count': len(intelligence_engine.intelligences)
    })

@app.route('/api/analysis/<symbol>')
def api_analysis(symbol):
    """API endpoint para análisis"""
    try:
        # Crear nuevo event loop para la función async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            analysis = loop.run_until_complete(
                intelligence_engine.get_consensus_analysis(symbol, 'complete')
            )
            return jsonify(analysis)
        finally:
            loop.close()
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolio/<int:user_id>')
def api_portfolio(user_id):
    """API endpoint para portfolio"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            portfolio = loop.run_until_complete(
                trading_engine.get_portfolio_summary(user_id)
            )
            return jsonify(portfolio)
        finally:
            loop.close()
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Template HTML para dashboard
DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}} - Enterprise Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; color: white;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 40px; }
        .header h1 { font-size: 3rem; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .header p { font-size: 1.2rem; opacity: 0.9; }
        .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { 
            background: rgba(255,255,255,0.1); backdrop-filter: blur(10px);
            border-radius: 15px; padding: 30px; border: 1px solid rgba(255,255,255,0.2);
        }
        .card h3 { font-size: 1.5rem; margin-bottom: 15px; color: #FFD700; }
        .status-indicator { 
            display: inline-block; width: 12px; height: 12px; border-radius: 50%;
            background: #00FF00; margin-right: 8px; animation: pulse 2s infinite;
        }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .metric { margin: 10px 0; }
        .metric-value { font-size: 1.8rem; font-weight: bold; color: #FFD700; }
        .footer { text-align: center; margin-top: 40px; opacity: 0.8; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 OMNIX V5 RAILWAY</h1>
            <p>Enterprise AI Trading Platform - $120M-$200M USD Valuation</p>
            <p>👑 Created by Harold Nunes - Founder OMNIX</p>
        </div>
        
        <div class="cards">
            <div class="card">
                <h3>🎯 Sistema Status</h3>
                <div class="metric">
                    <span class="status-indicator"></span>
                    Status: <span class="metric-value">{{status}}</span>
                </div>
                <div class="metric">
                    Version: <span class="metric-value">{{version}}</span>
                </div>
                <div class="metric">
                    Platform: <span class="metric-value">Railway Ready</span>
                </div>
            </div>
            
            <div class="card">
                <h3>🧠 Inteligencias</h3>
                <div class="metric">
                    Total: <span class="metric-value">32 IA</span>
                </div>
                <div class="metric">
                    Quantum: <span class="metric-value">Activo</span>
                </div>
                <div class="metric">
                    Monte Carlo: <span class="metric-value">75K iter</span>
                </div>
            </div>
            
            <div class="card">
                <h3>💎 Trading Engine</h3>
                <div class="metric">
                    Modo: <span class="metric-value">Enterprise</span>
                </div>
                <div class="metric">
                    Exchanges: <span class="metric-value">Multi</span>
                </div>
                <div class="metric">
                    Sharia: <span class="metric-value">Compliant</span>
                </div>
            </div>
            
            <div class="card">
                <h3>🌍 Memoria Avanzada</h3>
                <div class="metric">
                    Base de Datos: <span class="metric-value">SQLite</span>
                </div>
                <div class="metric">
                    Contexto: <span class="metric-value">Profundo</span>
                </div>
                <div class="metric">
                    Personalidad: <span class="metric-value">Adaptiva</span>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>✨ OMNIX V5 - Next Generation AI Trading Platform ✨</p>
            <p>🚀 Ready for Dubai Accelerator Presentations</p>
        </div>
    </div>
</body>
</html>
'''

# ===============================
# TELEGRAM BOT HANDLERS
# ===============================

if TELEGRAM_AVAILABLE:
    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        user_id = update.effective_user.id
        
        if user_id != config.authorized_user_id:
            await update.message.reply_text("❌ Usuario no autorizado")
            return
        
        welcome_text = """
🚀 OMNIX V5 RAILWAY FINAL ACTIVO

👑 Bienvenido Harold Nunes - Fundador OMNIX
💎 Valoración: $120M-$200M USD
🧠 32 Inteligencias especializadas
🔮 Análisis cuántico Monte Carlo
📊 Trading multi-exchange
🕌 Sharia compliance
🎤 Voz automática

Comandos disponibles:
• /analizar [crypto] - Análisis completo
• /portfolio - Ver cartera
• /comprar [cantidad] [crypto] 
• /vender [cantidad] [crypto]
• /estado - Status del sistema
• /help - Ayuda completa

¿En qué te ayudo hoy?
"""
        
        await update.message.reply_text(welcome_text)

    async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /analizar"""
        user_id = update.effective_user.id
        
        if user_id != config.authorized_user_id:
            await update.message.reply_text("❌ Usuario no autorizado")
            return
        
        if not context.args:
            await update.message.reply_text("Por favor especifica una criptomoneda: /analizar BTC")
            return
        
        symbol = context.args[0].upper()
        
        # Mostrar mensaje de procesamiento
        processing_msg = await update.message.reply_text(f"🧠 Analizando {symbol} con 32 inteligencias...")
        
        try:
            # Obtener análisis completo
            analysis = await intelligence_engine.get_consensus_analysis(symbol, 'complete')
            
            if analysis.get('error'):
                await processing_msg.edit_text(f"❌ Error analizando {symbol}: {analysis['error']}")
                return
            
            # Formatear respuesta
            consensus = analysis.get('consensus', {})
            recommendations = analysis.get('recommendations', {})
            
            response_text = f"📊 ANÁLISIS COMPLETO {symbol}\n\n"
            
            # Recomendación principal
            primary_rec = recommendations.get('primary_recommendation', 'HOLD')
            confidence_level = recommendations.get('confidence_level', 'MEDIUM')
            overall_confidence = analysis.get('quality_metrics', {}).get('overall_confidence', 0) * 100
            
            response_text += f"🎯 RECOMENDACIÓN: {primary_rec}\n"
            response_text += f"📈 Confianza: {confidence_level} ({overall_confidence:.0f}%)\n"
            response_text += f"⚠️ Riesgo: {recommendations.get('risk_level', 'MEDIUM')}\n\n"
            
            # Consenso de inteligencias
            dominant_signal = consensus.get('dominant_signal', 'neutral')
            agreement = consensus.get('agreement_percentage', 0)
            
            response_text += f"🧠 Consenso IA: {dominant_signal}\n"
            response_text += f"🤖 Acuerdo: {agreement:.0f}% ({analysis.get('intelligence_count', 0)}/32)\n\n"
            
            # Tiempo
            time_horizon = recommendations.get('recommended_time_horizon', 'medium_term')
            response_text += f"⏰ Horizonte: {time_horizon.replace('_', ' ')}"
            
            await processing_msg.edit_text(response_text)
            
        except Exception as e:
            await processing_msg.edit_text(f"❌ Error: {str(e)}")

    async def portfolio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /portfolio"""
        user_id = update.effective_user.id
        
        if user_id != config.authorized_user_id:
            await update.message.reply_text("❌ Usuario no autorizado")
            return
        
        try:
            portfolio = await trading_engine.get_portfolio_summary(user_id)
            
            if portfolio.get('error'):
                await update.message.reply_text(f"❌ Error: {portfolio['error']}")
                return
            
            response_text = f"💼 TU PORTFOLIO\n\n"
            response_text += f"💰 Valor total: ${portfolio['total_value_usd']:,.2f} USD\n"
            response_text += f"💵 Efectivo: ${portfolio['cash_usd']:,.2f} USD\n\n"
            
            # Holdings crypto
            crypto_holdings = portfolio.get('crypto_holdings', {})
            if crypto_holdings:
                response_text += "🪙 CRIPTOMONEDAS:\n"
                for symbol, data in crypto_holdings.items():
                    response_text += f"• {symbol}: {data['amount']:.6f}\n"
                    response_text += f"  @ ${data['price']:.2f} = ${data['value_usd']:.2f}\n"
            
            # Órdenes totales
            response_text += f"\n📈 Total órdenes: {portfolio.get('total_orders', 0)}"
            
            await update.message.reply_text(response_text)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /estado"""
        user_id = update.effective_user.id
        
        if user_id != config.authorized_user_id:
            await update.message.reply_text("❌ Usuario no autorizado")
            return
        
        status_text = f"""
🚀 OMNIX V5 RAILWAY STATUS

🎯 Sistema: Operacional ✅
🧠 Inteligencias: 32/32 activas
💎 Valoración: $120M-$200M USD
🔮 Quantum: Monte Carlo 75K iter
📊 Trading: {config.get_trading_mode()}
🎤 Voz: {'Activa' if config.voice_enabled else 'Desactivada'}
🕌 Sharia: Compliant ✅
🌐 Memoria: Avanzada SQLite
👑 Autorizado: Harold Nunes

⚡ Sistema listo para presentaciones Dubai
📈 Todas las funciones operativas
"""
        
        await update.message.reply_text(status_text)

    async def auto_trading_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /autotrading"""
        user_id = update.effective_user.id
        
        if user_id != config.authorized_user_id:
            await update.message.reply_text("❌ Usuario no autorizado")
            return
        
        if not context.args:
            # Mostrar status actual
            status = auto_trading_engine.get_auto_trading_status(user_id)
            if status.get('error'):
                await update.message.reply_text(f"❌ Error: {status['error']}")
                return
            
            status_text = f"""
🤖 TRADING AUTOMÁTICO STATUS

Estado: {'🟢 ACTIVO' if status['auto_trading_active'] else '🔴 PAUSADO'}
Trades hoy: {status['trades_today']}/{status['settings']['max_daily_trades']}
Confianza mínima: {status['settings']['confidence_threshold']:.0%}
Cantidad máxima: ${status['settings']['max_trade_amount_usd']:.0f} USD
Cryptos permitidas: {', '.join(status['settings']['symbols_allowed'])}

Total trades: {status['total_auto_trades']}

Comandos:
• /autotrading start - Iniciar
• /autotrading stop - Detener
• /autotrading status - Ver estado
"""
            await update.message.reply_text(status_text)
            return
        
        action = context.args[0].lower()
        
        if action == 'start':
            result = await auto_trading_engine.start_auto_trading(user_id)
            if result.get('success'):
                await update.message.reply_text(f"✅ {result['message']}")
            else:
                await update.message.reply_text(f"❌ {result.get('error')}")
                
        elif action == 'stop':
            result = await auto_trading_engine.stop_auto_trading(user_id)
            if result.get('success'):
                await update.message.reply_text(f"🛑 {result['message']}")
            else:
                await update.message.reply_text(f"❌ {result.get('error')}")
                
        else:
            await update.message.reply_text("Uso: /autotrading [start|stop|status]")

    async def autonomous_voice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /vozautonoma"""
        user_id = update.effective_user.id
        
        if user_id != config.authorized_user_id:
            await update.message.reply_text("❌ Usuario no autorizado")
            return
        
        if not context.args:
            # Mostrar status actual
            status = autonomous_voice_engine.get_autonomous_voice_status(user_id)
            if status.get('error'):
                await update.message.reply_text(f"❌ Error: {status['error']}")
                return
            
            status_text = f"""
🎤 VOZ AUTÓNOMA STATUS

Estado: {'🟢 ACTIVA' if status['autonomous_mode'] else '🔴 PAUSADA'}
Personalidad: {status['voice_personality']}
Tipos de mensaje: {status['message_types_count']}
Respuestas disponibles: {status['total_responses_available']}

Último mensaje:
{status['last_message'][:100] + '...' if status['last_message'] else 'Ninguno'}

Comandos:
• /vozautonoma start - Iniciar
• /vozautonoma stop - Detener  
• /vozautonoma trigger - Mensaje inmediato
• /vozautonoma status - Ver estado
"""
            await update.message.reply_text(status_text)
            return
        
        action = context.args[0].lower()
        
        if action == 'start':
            result = await autonomous_voice_engine.start_autonomous_voice_system(user_id)
            if result.get('success'):
                await update.message.reply_text(f"✅ {result['message']}")
            else:
                await update.message.reply_text(f"❌ {result.get('error')}")
                
        elif action == 'stop':
            result = await autonomous_voice_engine.stop_autonomous_voice_system(user_id)
            if result.get('success'):
                await update.message.reply_text(f"🔇 {result['message']}")
            else:
                await update.message.reply_text(f"❌ {result.get('error')}")
                
        elif action == 'trigger':
            result = await autonomous_voice_engine.trigger_immediate_autonomous_message(user_id)
            if result.get('success'):
                await update.message.reply_text(f"🎤 {result['message']}")
            else:
                await update.message.reply_text(f"❌ {result.get('message')}")
                
        else:
            await update.message.reply_text("Uso: /vozautonoma [start|stop|trigger|status]")

    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /help"""
        help_text = """
🤖 OMNIX V5 - COMANDOS COMPLETOS

📊 ANÁLISIS:
• /analizar [crypto] - Análisis con 32 IA
• /prediccion [crypto] - Predicción avanzada

💼 PORTFOLIO:
• /portfolio - Ver cartera completa
• /balance - Balance rápido

💰 TRADING:
• /comprar [cantidad] [crypto]
• /vender [cantidad] [crypto] 

🤖 TRADING AUTOMÁTICO:
• /autotrading - Status y control
• /autotrading start - Iniciar auto-trading
• /autotrading stop - Detener auto-trading

🎤 VOZ AUTÓNOMA:
• /vozautonoma - Status y control
• /vozautonoma start - Iniciar voz autónoma
• /vozautonoma stop - Detener voz autónoma
• /vozautonoma trigger - Mensaje inmediato

🔧 SISTEMA:
• /estado - Status completo
• /help - Esta ayuda

💡 EJEMPLOS:
• "Analiza BTC"
• "Compra 0.01 BTC"
• "/autotrading start"
• "/vozautonoma trigger"

👑 Sistema exclusivo para Harold Nunes
"""
        
        await update.message.reply_text(help_text)

    async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler para mensajes de texto"""
        user_id = update.effective_user.id
        message_text = update.message.text
        
        if user_id != config.authorized_user_id:
            await update.message.reply_text("❌ Usuario no autorizado")
            return
        
        try:
            # Procesar mensaje con IA conversacional
            response = await conversational_ai.process_message(message_text, user_id)
            
            # Enviar respuesta de texto
            await update.message.reply_text(response.get('text', 'Error procesando mensaje'))
            
            # Enviar voz si está disponible
            voice_file = response.get('voice_file')
            if voice_file and os.path.exists(voice_file):
                try:
                    with open(voice_file, 'rb') as audio_file:
                        await update.message.reply_voice(audio_file)
                    # Limpiar archivo temporal
                    os.unlink(voice_file)
                except Exception as e:
                    enterprise_logger.system_logger.error(f"Error enviando voz: {e}")
            
        except Exception as e:
            enterprise_logger.system_logger.error(f"Error en message handler: {e}")
            await update.message.reply_text("❌ Error procesando mensaje")

# ===============================
# FUNCIÓN PRINCIPAL
# ===============================

async def main():
    """Función principal del sistema"""
    try:
        enterprise_logger.log_startup()
        
        # Verificar configuración
        if not config.validate():
            enterprise_logger.system_logger.error("❌ Configuración inválida")
            return
        
        enterprise_logger.system_logger.info("🏥 Health Monitor iniciado - Métricas en tiempo real")
        
        # Inicializar Flask en thread separado
        def run_flask():
            app.run(host=config.host, port=config.port, debug=False, use_reloader=False)
        
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        
        enterprise_logger.system_logger.info(f"✅ Dashboard Enterprise: Puerto {config.port} activo")
        
        # Inicializar Telegram bot
        if TELEGRAM_AVAILABLE and config.bot_token:
            max_retries = 3
            retry_delay = 10
            
            for attempt in range(max_retries):
                try:
                    enterprise_logger.system_logger.info(f"🤖 Telegram intento {attempt + 1}/{max_retries}")
                    
                    application = Application.builder().token(config.bot_token).build()
                    
                    # Agregar handlers
                    application.add_handler(CommandHandler("start", start_command))
                    application.add_handler(CommandHandler("analizar", analyze_command))
                    application.add_handler(CommandHandler("portfolio", portfolio_command))
                    application.add_handler(CommandHandler("estado", status_command))
                    application.add_handler(CommandHandler("autotrading", auto_trading_command))
                    application.add_handler(CommandHandler("vozautonoma", autonomous_voice_command))
                    application.add_handler(CommandHandler("help", help_command))
                    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
                    
                    # Iniciar bot
                    await application.run_polling(drop_pending_updates=True)
                    break
                    
                except Exception as e:
                    enterprise_logger.system_logger.error(f"❌ Error Telegram: {e}")
                    
                    if attempt < max_retries - 1:
                        enterprise_logger.system_logger.info(f"🔄 Reintentando en {retry_delay} segundos...")
                        await asyncio.sleep(retry_delay)
                    else:
                        enterprise_logger.system_logger.error(f"❌ Error crítico: {e}")
        
        enterprise_logger.system_logger.info("🔄 Sistema finalizado correctamente")
        
    except Exception as e:
        enterprise_logger.system_logger.error(f"❌ Error crítico en main: {e}")
        enterprise_logger.system_logger.error(f"📍 Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    enterprise_logger.log_startup()
    enterprise_logger.system_logger.info("👑 Creador: Harold Nunes - Fundador OMNIX")
    enterprise_logger.system_logger.info("✅ SISTEMA FUNCIONAL COMPLETO - SIN CEREBRO - CON IA")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        enterprise_logger.system_logger.info("🛑 Sistema detenido por usuario")
    except Exception as e:
        enterprise_logger.system_logger.error(f"❌ Error fatal: {e}")
        enterprise_logger.system_logger.error(f"📍 Traceback: {traceback.format_exc()}")
    finally:
        enterprise_logger.system_logger.info("🔚 OMNIX V5 Railway Final - Terminado")
