"""
OMNIX Voice Controller
======================
Módulo centralizado para manejo de voz (TTS/STT) y respuestas con audio.
Extraído de main.py para arquitectura modular.

Incluye:
- VoiceEngine: Adapter para VoiceServiceEnterprise con fallback legacy
- send_telegram_response_with_voice: Envío automático de respuestas con voz a Telegram
"""

import logging
import os
import tempfile
import requests
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Import conditionals - same as main.py
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
    SPEECH_TO_TEXT_ENABLED = True
except ImportError:
    OPENAI_AVAILABLE = False
    SPEECH_TO_TEXT_ENABLED = False

# Import Voice Enterprise Service
try:
    from omnix_services.voice_service import VoiceServiceEnterprise
    VOICE_ENTERPRISE_AVAILABLE = True
except ImportError:
    VOICE_ENTERPRISE_AVAILABLE = False
    logger.warning("⚠️ Voice Enterprise Service not available")

# Global voice engine instance
global_voice_engine = None


# 🎤 VOICE ENGINE ENTERPRISE ADAPTER
class VoiceEngine:
    """
    Adapter class - mantiene compatibilidad con código legacy
    pero usa VoiceServiceEnterprise internamente
    """
    def __init__(self):
        global global_voice_engine
        
        if VOICE_ENTERPRISE_AVAILABLE:
            logger.info("🚀 Inicializando VoiceEngine con ENTERPRISE backend")
            self.enterprise_service = VoiceServiceEnterprise()
            health = self.enterprise_service.health_check()
            self.active = health.get('tts_available', False)
            self.using_enterprise = True
        else:
            logger.warning("⚠️ Fallback a sistema legacy - Voice Enterprise no disponible")
            # HAROLD FIX: FORZAR ACTIVACIÓN porque gtts SIEMPRE está en requirements.txt
            self.active = True  # ✅ Google TTS siempre disponible
            self.temp_dir = tempfile.gettempdir()
            self.voice_cache = {}
            self.speech_to_text_enabled = SPEECH_TO_TEXT_ENABLED
            self.openai_client = None
            if OPENAI_AVAILABLE and os.environ.get('OPENAI_API_KEY') and SPEECH_TO_TEXT_ENABLED:
                try:
                    self.openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
                except:
                    pass
            self.using_enterprise = False
        
        # Set global instance
        global_voice_engine = self
        logger.info(f"🎤 VoiceEngine inicializado - Enterprise: {self.using_enterprise}, TTS: {self.active}")
    
    def text_to_speech(self, text, language='es'):
        if self.using_enterprise:
            return self.enterprise_service.text_to_speech(text, language)
        
        # Legacy mode: usar Google TTS directamente
        try:
            from gtts import gTTS
            import tempfile
            import os
            
            # Crear archivo temporal
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            temp_path = temp_file.name
            temp_file.close()
            
            # Generar audio con Google TTS
            tts = gTTS(text=text, lang=language, slow=False)
            tts.save(temp_path)
            
            logger.info(f"🎤 Audio generado con Google TTS: {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"🎤 Error generando TTS legacy: {e}")
            return None
    
    def speech_to_text(self, audio_file_path, language='es'):
        if self.using_enterprise:
            return self.enterprise_service.speech_to_text(audio_file_path, language)
        return None
    
    def create_voice_signature(self, audio_file_path, user_id):
        if self.using_enterprise:
            return self.enterprise_service.create_voice_signature(audio_file_path, user_id)
        return {'success': False, 'error': 'Enterprise not available'}
    
    def verify_voice_signature(self, audio_file_path, user_id, threshold=0.85):
        if self.using_enterprise:
            return self.enterprise_service.verify_voice_signature(audio_file_path, user_id, threshold)
        return {'success': False, 'verified': False}
    
    def download_telegram_voice(self, file_id, bot_token):
        if self.using_enterprise:
            return self.enterprise_service.download_telegram_voice(file_id, bot_token)
        return None
    
    def health_check(self):
        if self.using_enterprise:
            return self.enterprise_service.health_check()
        return {'tts_available': self.active, 'stt_available': self.openai_client is not None, 'enterprise': False}


def send_telegram_response_with_voice(chat_id, response_text, user_name="Usuario", user_id=None, 
                                      is_admin_user=False, trading_system=None, reference_message=None, 
                                      is_admin_func=None):
    """
    Función compartida para enviar respuestas con voz automática
    Usada tanto por polling (Replit) como por webhook (Railway)
    
    Args:
        chat_id: ID del chat de Telegram
        response_text: Texto de la respuesta
        user_name: Nombre del usuario
        user_id: ID del usuario
        is_admin_user: Si el usuario es admin (deprecated, usar is_admin_func)
        trading_system: Sistema de trading (no usado actualmente)
        reference_message: Mensaje de referencia (no usado actualmente)
        is_admin_func: Función para verificar si user es admin (debe recibir user_id)
    """
    try:
        logger.info(f"🎤 DEBUG: Generando voz para chat_id='{chat_id}'")
        
        # 🔒 USAR USER_ID PARA DETECCIÓN ROBUSTA DE ADMIN EN VOZ
        admin_id = user_id if user_id is not None else chat_id
        
        # Use provided is_admin function or fallback to is_admin_user parameter
        if is_admin_func:
            is_admin_voice = is_admin_func(admin_id)
        else:
            is_admin_voice = is_admin_user
        
        logger.info(f"🎤 ✅ INICIANDO GENERACIÓN DE VOZ - Admin: {is_admin_voice} (User: {admin_id})")
        
        # Aplicar filtros de seguridad si no es admin
        if is_admin_voice:
            voice_text = response_text  # Sin restricciones para admin
        else:
            # Filtrar contenido sensible para usuarios no-admin
            voice_text = response_text
            voice_text = re.sub(r'\$[\d,]+\.?\d*', '$X.XX', voice_text)
            voice_text = re.sub(r'[\d,]+\.?\d*\s*(BTC|ETH)', 'X.XX crypto', voice_text)
        
        NUMBER_WORDS = {
            '1': 'uno', '2': 'dos', '3': 'tres', '4': 'cuatro', '5': 'cinco',
            '6': 'seis', '7': 'siete', '8': 'ocho', '9': 'nueve', '10': 'diez',
            '11': 'once', '12': 'doce', '13': 'trece', '14': 'catorce', '15': 'quince'
        }
        
        def convert_list_number(match):
            num = match.group(1)
            word = NUMBER_WORDS.get(num, num)
            return f"Punto {word}, "
        
        voice_text = re.sub(r'\*(\d{1,2})\.\s*', convert_list_number, voice_text)
        voice_text = re.sub(r'^(\d{1,2})\.\s+', convert_list_number, voice_text, flags=re.MULTILINE)
        
        voice_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', voice_text)
        voice_text = re.sub(r'\*([^*]+)\*', r'\1', voice_text)
        
        voice_text = re.sub(r'\*+', '', voice_text)
        
        voice_text = re.sub(r':\*', ',', voice_text)
        
        voice_text = voice_text.replace('→', ', ')
        voice_text = voice_text.replace('←', ', ')
        voice_text = voice_text.replace('↑', ', ')
        voice_text = voice_text.replace('↓', ', ')
        voice_text = voice_text.replace('⟶', ', ')
        voice_text = voice_text.replace('➡', ', ')
        voice_text = voice_text.replace('➔', ', ')
        
        voice_text = re.sub(r'[🚀💰🤖📊📋💬📈⏰💲📰📅⚡🆓🎥🖥️📱🎭🏆🧠🎯🌍❓✅❌⚠️🔍💳📧🔄]', '', voice_text)
        voice_text = voice_text.replace('\n', '. ')
        voice_text = voice_text.strip()
        
        logger.info(f"🎤 Texto completo para voz preparado: {len(voice_text)} caracteres - SIN RESTRICCIONES")
        
        # Verificar VoiceEngine - REINICIALIZAR SI ES NECESARIO (FIX RAILWAY)
        global global_voice_engine
        if not global_voice_engine or not hasattr(global_voice_engine, 'active'):
            logger.warning("🎤 ⚠️ VoiceEngine perdido - REINICIALIZANDO...")
            try:
                # FIX Dec 31, 2025: Siempre usar VoiceEngine() que envuelve VoiceServiceEnterprise
                # VoiceEngine tiene el atributo 'active', VoiceServiceEnterprise directo no
                global_voice_engine = VoiceEngine()
                logger.info("🎤 ✅ VoiceEngine reinicializado exitosamente")
            except Exception as reinit_error:
                logger.error(f"🎤 ❌ Error reinicializando VoiceEngine: {reinit_error}")
                global_voice_engine = None
        
        if global_voice_engine and global_voice_engine.active:
            logger.info("🎤 VoiceEngine disponible - generando audio")
            
            GTTS_LANGUAGE_MAP = {
                'en': 'en',
                'es': 'es',
                'fr': 'fr',
                'de': 'de',
                'pt': 'pt',
                'it': 'it',
                'nl': 'nl',
                'ar': 'ar',
                'zh': 'zh-CN',
                'ja': 'ja',
                'ko': 'ko',
                'ru': 'ru',
                'hi': 'hi',
                'no': 'no',
                'sv': 'sv',
                'da': 'da',
                'pl': 'pl',
                'tr': 'tr',
            }
            
            detected_language = 'en'
            try:
                from omnix_services.ai_service.prompt_templates import LanguageContextManager
                lang_manager = LanguageContextManager()
                raw_lang = lang_manager.detect_language(voice_text[:200])
                detected_language = GTTS_LANGUAGE_MAP.get(raw_lang, 'en')
                logger.info(f"🎤 TTS Language: {raw_lang} -> {detected_language}")
            except Exception as lang_err:
                logger.warning(f"🎤 Language detection failed, using English: {lang_err}")
                detected_language = 'en'
            
            audio_path = global_voice_engine.text_to_speech(voice_text, language=detected_language)
            
            if audio_path and os.path.exists(audio_path):
                logger.info("🎤 Audio generado exitosamente - enviando a Telegram")
                
                # Enviar audio a Telegram usando requests
                # NOTA: gTTS genera archivos MP3, debemos usar sendAudio con MIME correcto
                bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
                
                # Detectar tipo de archivo y usar endpoint correcto
                if audio_path.endswith('.mp3'):
                    # Para MP3: usar sendAudio con MIME correcto
                    audio_url = f"https://api.telegram.org/bot{bot_token}/sendAudio"
                    with open(audio_path, 'rb') as audio_file:
                        files = {'audio': ('voice.mp3', audio_file, 'audio/mpeg')}
                        caption = "🎤 OMNIX Voz automática - Respuesta completa" if is_admin_voice else "🎤 OMNIX Voz automática"
                        data = {
                            'chat_id': chat_id,
                            'caption': caption,
                            'title': 'OMNIX Voice Response'
                        }
                        voice_response = requests.post(audio_url, files=files, data=data)
                else:
                    # Para OGG/OPUS: usar sendVoice
                    voice_url = f"https://api.telegram.org/bot{bot_token}/sendVoice"
                    with open(audio_path, 'rb') as audio_file:
                        files = {'voice': ('voice.ogg', audio_file, 'audio/ogg')}
                        caption = "🎤 OMNIX Voz automática - Respuesta completa" if is_admin_voice else "🎤 OMNIX Voz automática"
                        data = {
                            'chat_id': chat_id,
                            'caption': caption
                        }
                        voice_response = requests.post(voice_url, files=files, data=data)
                
                # Verificar respuesta de Telegram
                if voice_response.status_code == 200:
                    response_json = voice_response.json()
                    if response_json.get('ok'):
                        user_type = "HAROLD" if is_admin_voice else "USUARIO"
                        logger.info(f"🎤 ✅ VOZ AUTOMÁTICA ENVIADA A {user_type} EXITOSAMENTE")
                    else:
                        logger.error(f"🎤 ❌ Telegram rechazó audio: {response_json.get('description', 'Unknown error')}")
                else:
                    logger.error(f"🎤 ❌ Error HTTP enviando voz: {voice_response.status_code} - {voice_response.text}")
                
                # Limpiar archivo temporal
                try:
                    os.remove(audio_path)
                    logger.info(f"🎤 Archivo temporal limpiado: {audio_path}")
                except Exception as cleanup_error:
                    logger.warning(f"🎤 Error limpiando archivo: {cleanup_error}")
            else:
                logger.error(f"🎤 ❌ Error generando audio. Path: {audio_path}, Existe: {os.path.exists(audio_path) if audio_path else False}")
        else:
            logger.error(f"🎤 ❌ VoiceEngine no disponible. Engine: {global_voice_engine is not None}, Active: {global_voice_engine.active if global_voice_engine else 'N/A'}")
            
    except Exception as voice_error:
        logger.error(f"🎤 ❌ Error crítico generando voz: {voice_error}")
        import traceback
        logger.error(f"🎤 ❌ TRACEBACK VOZ: {traceback.format_exc()}")
        # Continuar sin enviar voz si hay error


def initialize_voice_engine():
    """
    Initialize global voice engine instance
    Returns the VoiceEngine instance
    """
    global global_voice_engine
    if global_voice_engine is None:
        global_voice_engine = VoiceEngine()
    return global_voice_engine
