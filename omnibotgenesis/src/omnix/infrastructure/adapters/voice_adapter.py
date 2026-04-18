"""
OMNIX V7.0 Voice Service Adapter
=================================
Implements AIVoicePort by wrapping legacy VoiceServiceEnterprise.

Provides TTS (gTTS) and STT (Whisper) functionality with caching
and Telegram integration support.

Migration Status: Phase 3 - AI Service Integration
"""

import asyncio
import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from src.omnix.ports.driven.ai_voice_port import (
    AIVoicePort,
    TTSRequest,
    TTSResponse,
    STTRequest,
    STTResponse,
    VoiceLanguage,
    VoiceBiometricsResult,
)

logger = logging.getLogger(__name__)


class VoiceServiceAdapter:
    """
    Infrastructure adapter for voice services (TTS + STT).
    
    Implements AIVoicePort:
    - text_to_speech: Convert text to audio using gTTS
    - speech_to_text: Transcribe audio using OpenAI Whisper
    - cleanup_temp_files: Clean temporary audio files
    - health_check: Check service availability
    
    Wraps legacy VoiceServiceEnterprise with:
    - Async interface
    - Structured DTOs
    - Request tracking
    - Error handling
    
    Strangler Fig: Wraps legacy VoiceServiceEnterprise without modification.
    """
    
    def __init__(self, voice_service: Optional[Any] = None):
        """
        Initialize voice adapter.
        
        Args:
            voice_service: VoiceServiceEnterprise instance (MUST be injected by container).
                          NO lazy-loading - container controls the lifecycle.
        """
        self._voice_service = voice_service
        self._request_count = 0
        self._error_count = 0
        self._last_request: Optional[datetime] = None
        self._cache: Dict[str, str] = {}
        
        if voice_service is not None:
            logger.info("✅ VoiceServiceAdapter initialized with injected VoiceServiceEnterprise")
    
    def _get_voice_service(self) -> Optional[Any]:
        """
        Get the injected VoiceServiceEnterprise (NO lazy initialization).
        
        This method only returns the service if it was explicitly injected
        during construction. It does NOT create a new service to avoid
        violating the container's cooldown mechanism.
        
        The container is responsible for injecting the service when creating
        the adapter. If no service was injected, returns None and the adapter
        reports unhealthy, triggering fallback to legacy VoiceServiceEnterprise.
        """
        return self._voice_service
    
    def _language_to_code(self, language: VoiceLanguage) -> str:
        """Convert VoiceLanguage enum to language code string."""
        return language.value
    
    def _code_to_language(self, code: str) -> Optional[VoiceLanguage]:
        """Convert language code string to VoiceLanguage enum."""
        try:
            return VoiceLanguage(code)
        except ValueError:
            return None
    
    async def text_to_speech(
        self,
        request: TTSRequest
    ) -> TTSResponse:
        """
        Convert text to speech audio.
        
        Uses gTTS for text-to-speech conversion.
        Supports caching to avoid regenerating same audio.
        """
        self._request_count += 1
        self._last_request = datetime.utcnow()
        start_time = time.time()
        
        service = self._get_voice_service()
        if service is None:
            self._error_count += 1
            return TTSResponse(
                audio_path=None,
                language=request.language,
                success=False,
                error_message="Voice service not available"
            )
        
        if request.cache_enabled:
            cache_key = f"{hash(request.text)}_{request.language.value}"
            if cache_key in self._cache:
                cached_path = self._cache[cache_key]
                if os.path.exists(cached_path):
                    return TTSResponse(
                        audio_path=cached_path,
                        language=request.language,
                        cached=True,
                        success=True
                    )
        
        try:
            lang_code = self._language_to_code(request.language)
            audio_path = await asyncio.to_thread(
                service.text_to_speech,
                request.text,
                lang_code
            )
            
            if audio_path is None:
                self._error_count += 1
                return TTSResponse(
                    audio_path=None,
                    language=request.language,
                    success=False,
                    error_message="TTS generation failed"
                )
            
            duration = time.time() - start_time
            
            if request.cache_enabled:
                cache_key = f"{hash(request.text)}_{request.language.value}"
                self._cache[cache_key] = audio_path
            
            return TTSResponse(
                audio_path=audio_path,
                duration_seconds=duration,
                language=request.language,
                cached=False,
                success=True
            )
            
        except Exception as e:
            self._error_count += 1
            logger.error(f"VoiceServiceAdapter: TTS error: {e}")
            return TTSResponse(
                audio_path=None,
                language=request.language,
                success=False,
                error_message=str(e)
            )
    
    async def speech_to_text(
        self,
        request: STTRequest
    ) -> STTResponse:
        """
        Transcribe speech audio to text.
        
        Uses OpenAI Whisper for speech-to-text.
        """
        self._request_count += 1
        self._last_request = datetime.utcnow()
        start_time = time.time()
        
        service = self._get_voice_service()
        if service is None:
            self._error_count += 1
            return STTResponse(
                text="",
                success=False,
                error_message="Voice service not available"
            )
        
        if not os.path.exists(request.audio_path):
            self._error_count += 1
            return STTResponse(
                text="",
                success=False,
                error_message=f"Audio file not found: {request.audio_path}"
            )
        
        try:
            lang_code = request.language.value if request.language else None
            
            if hasattr(service, 'speech_to_text'):
                result = await asyncio.to_thread(
                    service.speech_to_text,
                    request.audio_path,
                    lang_code
                )
            else:
                self._error_count += 1
                return STTResponse(
                    text="",
                    success=False,
                    error_message="STT not supported by voice service"
                )
            
            if result is None:
                self._error_count += 1
                return STTResponse(
                    text="",
                    success=False,
                    error_message="STT transcription failed"
                )
            
            duration = time.time() - start_time
            
            detected_lang = None
            confidence = 0.9
            if isinstance(result, dict):
                text = result.get('text', '')
                detected_lang = self._code_to_language(result.get('language', ''))
                confidence = result.get('confidence', 0.9)
            else:
                text = str(result)
            
            return STTResponse(
                text=text,
                detected_language=detected_lang or request.language,
                confidence=confidence,
                duration_seconds=duration,
                success=True
            )
            
        except Exception as e:
            self._error_count += 1
            logger.error(f"VoiceServiceAdapter: STT error: {e}")
            return STTResponse(
                text="",
                success=False,
                error_message=str(e)
            )
    
    def get_supported_languages(self) -> List[VoiceLanguage]:
        """Get list of supported languages for TTS/STT."""
        return [
            VoiceLanguage.SPANISH,
            VoiceLanguage.ENGLISH,
            VoiceLanguage.ARABIC,
            VoiceLanguage.FRENCH,
            VoiceLanguage.GERMAN,
            VoiceLanguage.PORTUGUESE,
            VoiceLanguage.ITALIAN,
            VoiceLanguage.RUSSIAN,
            VoiceLanguage.CHINESE,
            VoiceLanguage.JAPANESE,
        ]
    
    def cleanup_temp_files(self, max_age_seconds: int = 3600) -> int:
        """
        Clean up temporary audio files older than max_age.
        
        Args:
            max_age_seconds: Maximum age of files to keep
            
        Returns:
            Number of files deleted
        """
        import tempfile
        
        temp_dir = tempfile.gettempdir()
        deleted_count = 0
        current_time = time.time()
        
        try:
            for filename in os.listdir(temp_dir):
                if filename.startswith('omnix_voice_'):
                    filepath = os.path.join(temp_dir, filename)
                    if os.path.isfile(filepath):
                        file_age = current_time - os.path.getmtime(filepath)
                        if file_age > max_age_seconds:
                            os.remove(filepath)
                            deleted_count += 1
                            
                            for cache_key, cached_path in list(self._cache.items()):
                                if cached_path == filepath:
                                    del self._cache[cache_key]
        except Exception as e:
            logger.error(f"VoiceServiceAdapter: cleanup error: {e}")
        
        return deleted_count
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check health of voice services.
        
        Reports healthy=True only if service is available AND at least one
        capability (TTS or STT) is working. This ensures the container can
        fallback to legacy service if the adapter is unhealthy.
        """
        import tempfile
        
        service = self._get_voice_service()
        
        if service is None:
            return {
                'healthy': False,
                'backend': 'VoiceServiceEnterprise (not available)',
                'tts_available': False,
                'stt_available': False,
                'cache_size': len(self._cache),
                'temp_dir_exists': os.path.exists(tempfile.gettempdir()),
                'request_count': self._request_count,
                'error_count': self._error_count,
                'error_rate': self._error_count / max(self._request_count, 1),
            }
        
        service_health = service.health_check() if hasattr(service, 'health_check') else {}
        
        tts_available = service_health.get('tts_available', False)
        stt_available = service_health.get('stt_available', False)
        at_least_one_available = tts_available or stt_available
        error_rate = self._error_count / max(self._request_count, 1)
        too_many_errors = error_rate > 0.8 and self._request_count >= 5
        
        healthy = at_least_one_available and not too_many_errors
        
        return {
            'healthy': healthy,
            'backend': 'VoiceServiceEnterprise (legacy with TTS/STT)',
            'tts_available': tts_available,
            'stt_available': stt_available,
            'cache_size': len(self._cache),
            'temp_dir_exists': os.path.exists(tempfile.gettempdir()),
            'request_count': self._request_count,
            'error_count': self._error_count,
            'error_rate': error_rate,
            'service_health': service_health,
        }


def get_voice_adapter() -> VoiceServiceAdapter:
    """Factory function to create VoiceServiceAdapter instance."""
    return VoiceServiceAdapter()
