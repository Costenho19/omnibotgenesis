"""
OMNIX Voice Controller
======================
Módulo centralizado para manejo de voz (TTS/STT) y respuestas con audio.
Extraído de main.py para arquitectura modular.

Incluye:
- VoiceEngine: Adapter para VoiceServiceEnterprise con fallback legacy
- send_telegram_response_with_voice: Envío síncrono (legacy)
- schedule_voice_response: Envío asíncrono en hilo separado (V006 - Jan 2, 2026)

V006 Optimization (Jan 2, 2026):
- Text-first, voice-later: El texto se envía inmediatamente, la voz se genera en background
- Usa threading.Thread daemon para no bloquear el handler principal
- Reduce latencia percibida de ~5-10s a ~0.5s para respuestas de texto

V007 Reliability (Jan 4, 2026):
- Logging estructurado con chat_id/user_id en cada paso
- Retry con backoff para gTTS (3 intentos)
- Captura completa de errores en hilos daemon
- Voz habilitada para TODOS los usuarios (sin restricción por plan)
"""

import logging
import os
import tempfile
import requests
import re
import threading
import time
import traceback
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

# Global voice engine instance with thread-safe access
global_voice_engine = None
_voice_engine_lock = threading.Lock()


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
                except Exception:
                    pass
            self.using_enterprise = False
        
        # Set global instance
        global_voice_engine = self
        logger.info(f"🎤 VoiceEngine inicializado - Enterprise: {self.using_enterprise}, TTS: {self.active}")
    
    def text_to_speech(self, text, language='es', max_retries=3):
        """
        V007: Genera audio TTS con retry y backoff.
        
        Args:
            text: Texto a convertir
            language: Idioma ISO (es, en, etc.)
            max_retries: Número de intentos (default 3)
        
        Returns:
            str: Path al archivo de audio, o None si falla
        """
        if self.using_enterprise:
            return self.enterprise_service.text_to_speech(text, language)
        
        from gtts import gTTS
        
        for attempt in range(1, max_retries + 1):
            try:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                temp_path = temp_file.name
                temp_file.close()
                
                tts = gTTS(text=text, lang=language, slow=False)
                tts.save(temp_path)
                
                logger.info(f"🎤 [TTS] ✅ Audio generado (intento {attempt}/{max_retries}): {temp_path}")
                return temp_path
                
            except Exception as e:
                error_type = type(e).__name__
                logger.warning(f"🎤 [TTS] ⚠️ Intento {attempt}/{max_retries} falló ({error_type}): {e}")
                
                if attempt < max_retries:
                    backoff = attempt * 2
                    logger.info(f"🎤 [TTS] Esperando {backoff}s antes de reintentar...")
                    time.sleep(backoff)
                else:
                    logger.error(f"🎤 [TTS] ❌ Todos los intentos fallaron para texto de {len(text)} chars")
                    return None
        
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
                
                # Siempre usar sendVoice — Telegram acepta MP3, OGG y M4A como notas de voz
                voice_url = f"https://api.telegram.org/bot{bot_token}/sendVoice"
                if audio_path.endswith('.mp3'):
                    with open(audio_path, 'rb') as audio_file:
                        files = {'voice': ('voice.mp3', audio_file, 'audio/mpeg')}
                        data = {'chat_id': chat_id}
                        voice_response = requests.post(voice_url, files=files, data=data)
                else:
                    with open(audio_path, 'rb') as audio_file:
                        files = {'voice': ('voice.ogg', audio_file, 'audio/ogg')}
                        data = {'chat_id': chat_id}
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


def _process_and_send_voice(chat_id, response_text, user_name="Usuario", user_id=None, 
                            is_admin_user=False, is_admin_func=None):
    """
    V007 (Jan 4, 2026): Función interna para procesar y enviar voz.
    Esta función se ejecuta en un hilo separado para no bloquear el handler principal.
    
    V007 mejoras:
    - Logging detallado con chat_id/user_id en cada paso
    - Captura completa de errores
    - Sin restricción por plan (todos reciben voz)
    """
    effective_user = user_id or chat_id
    try:
        logger.info(f"🎤 [ASYNC] Iniciando generación de voz - chat_id={chat_id}, user={effective_user}")
        
        admin_id = user_id if user_id is not None else chat_id
        
        if is_admin_func:
            is_admin_voice = is_admin_func(admin_id)
        else:
            is_admin_voice = is_admin_user
        
        if is_admin_voice:
            voice_text = response_text
        else:
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
        
        global global_voice_engine
        with _voice_engine_lock:
            if not global_voice_engine or not hasattr(global_voice_engine, 'active'):
                logger.warning("🎤 [ASYNC] VoiceEngine perdido - REINICIALIZANDO...")
                try:
                    global_voice_engine = VoiceEngine()
                except Exception as reinit_error:
                    logger.error(f"🎤 [ASYNC] Error reinicializando VoiceEngine: {reinit_error}")
                    return
            
            if not global_voice_engine or not global_voice_engine.active:
                logger.error("🎤 [ASYNC] VoiceEngine no disponible")
                return
            
            voice_engine_ref = global_voice_engine
        
        GTTS_LANGUAGE_MAP = {
            'en': 'en', 'es': 'es', 'fr': 'fr', 'de': 'de', 'pt': 'pt',
            'it': 'it', 'nl': 'nl', 'ar': 'ar', 'zh': 'zh-CN', 'ja': 'ja',
            'ko': 'ko', 'ru': 'ru', 'hi': 'hi', 'no': 'no', 'sv': 'sv',
            'da': 'da', 'pl': 'pl', 'tr': 'tr',
        }
        
        detected_language = 'en'
        try:
            from omnix_services.ai_service.prompt_templates import LanguageContextManager
            lang_manager = LanguageContextManager()
            raw_lang = lang_manager.detect_language(voice_text[:200])
            detected_language = GTTS_LANGUAGE_MAP.get(raw_lang, 'en')
            logger.info(f"🎤 [ASYNC] TTS Language: {raw_lang} -> {detected_language}")
        except Exception as lang_err:
            logger.warning(f"🎤 [ASYNC] Language detection failed: {lang_err}")
        
        audio_path = voice_engine_ref.text_to_speech(voice_text, language=detected_language)
        
        if not audio_path or not os.path.exists(audio_path):
            logger.error("🎤 [ASYNC] Error generando audio")
            return
        
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        
        # Siempre usar sendVoice — Telegram acepta MP3, OGG y M4A como notas de voz
        voice_url = f"https://api.telegram.org/bot{bot_token}/sendVoice"
        if audio_path.endswith('.mp3'):
            with open(audio_path, 'rb') as audio_file:
                files = {'voice': ('voice.mp3', audio_file, 'audio/mpeg')}
                data = {'chat_id': chat_id}
                voice_response = requests.post(voice_url, files=files, data=data, timeout=30)
        else:
            with open(audio_path, 'rb') as audio_file:
                files = {'voice': ('voice.ogg', audio_file, 'audio/ogg')}
                data = {'chat_id': chat_id}
                voice_response = requests.post(voice_url, files=files, data=data, timeout=30)
        
        if voice_response.status_code == 200 and voice_response.json().get('ok'):
            logger.info(f"🎤 [ASYNC] ✅ Voz enviada exitosamente - chat_id={chat_id}, user={effective_user}")
        else:
            error_detail = voice_response.text[:500] if voice_response.text else "Unknown"
            logger.error(f"🎤 [ASYNC] ❌ Error enviando voz - chat_id={chat_id}, user={effective_user}, status={voice_response.status_code}, error={error_detail}")
        
        try:
            os.remove(audio_path)
            logger.debug(f"🎤 [ASYNC] Archivo temporal limpiado: {audio_path}")
        except Exception as cleanup_err:
            logger.debug(f"🎤 [ASYNC] No se pudo limpiar archivo temporal: {cleanup_err}")
            
    except Exception as e:
        logger.error(f"🎤 [ASYNC] ❌ Error crítico para chat_id={chat_id}, user={effective_user}: {type(e).__name__}: {e}")
        logger.error(f"🎤 [ASYNC] Traceback: {traceback.format_exc()}")


def schedule_voice_response(chat_id, response_text, user_name="Usuario", user_id=None,
                           is_admin_user=False, is_admin_func=None):
    """
    V007 (Jan 4, 2026): Programa voz async con logging estructurado.
    
    IMPORTANTE: Voz está habilitada para TODOS los usuarios.
    No hay restricción por plan en esta versión.
    
    Args:
        chat_id: ID del chat de Telegram
        response_text: Texto a convertir a voz
        user_name: Nombre del usuario
        user_id: ID del usuario
        is_admin_user: Si es admin (deprecated)
        is_admin_func: Función para verificar admin
    
    Returns:
        Thread: El hilo creado (para testing/debugging), o None si saltado
    """
    effective_user = user_id or chat_id
    text_len = len(response_text) if response_text else 0
    
    logger.info(f"🎤 [VOICE-V007] === INICIO schedule_voice_response ===")
    logger.info(f"🎤 [VOICE-V007] chat_id={chat_id}, user_id={effective_user}, user_name={user_name}")
    logger.info(f"🎤 [VOICE-V007] text_len={text_len} chars")
    
    if not response_text or text_len < 20:
        logger.warning(f"🎤 [VOICE-V007] ⏭️ SALTADO: Texto muy corto ({text_len} chars < 20)")
        return None
    
    global global_voice_engine
    with _voice_engine_lock:
        if not global_voice_engine:
            logger.warning(f"🎤 [VOICE-V007] VoiceEngine no existe - inicializando...")
            try:
                global_voice_engine = VoiceEngine()
            except Exception as init_err:
                logger.error(f"🎤 [VOICE-V007] ❌ Error inicializando VoiceEngine: {init_err}")
                return None
        
        if not global_voice_engine.active:
            logger.error(f"🎤 [VOICE-V007] ❌ SALTADO: VoiceEngine no activo")
            return None
    
    voice_thread = threading.Thread(
        target=_process_and_send_voice_safe,
        args=(chat_id, response_text, user_name, user_id, is_admin_user, is_admin_func),
        daemon=True,
        name=f"VoiceThread-{chat_id}-{int(time.time())}"
    )
    voice_thread.start()
    
    logger.info(f"🎤 [VOICE-V007] ✅ Hilo iniciado: {voice_thread.name}")
    return voice_thread


def _process_and_send_voice_safe(chat_id, response_text, user_name="Usuario", user_id=None, 
                                  is_admin_user=False, is_admin_func=None):
    """
    V007: Wrapper seguro que captura TODAS las excepciones en el hilo daemon.
    """
    effective_user = user_id or chat_id
    try:
        logger.info(f"🎤 [VOICE-V007] Hilo daemon iniciado para chat_id={chat_id}")
        _process_and_send_voice(chat_id, response_text, user_name, user_id, is_admin_user, is_admin_func)
        logger.info(f"🎤 [VOICE-V007] ✅ Hilo daemon completado exitosamente para chat_id={chat_id}")
    except Exception as e:
        logger.error(f"🎤 [VOICE-V007] ❌ ERROR CRÍTICO en hilo daemon para chat_id={chat_id}: {type(e).__name__}: {e}")
        logger.error(f"🎤 [VOICE-V007] Traceback: {traceback.format_exc()}")


def initialize_voice_engine():
    """
    Initialize global voice engine instance
    Returns the VoiceEngine instance
    """
    global global_voice_engine
    if global_voice_engine is None:
        global_voice_engine = VoiceEngine()
    return global_voice_engine
