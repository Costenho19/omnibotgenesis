"""
OMNIX V7.0 AI Voice Port
=========================
Protocol definition for voice services (TTS + STT).

Enables VoiceServiceAdapter to replace VoiceServiceEnterprise via feature flag.
Supports gTTS for TTS and OpenAI Whisper for STT.

Migration Status: Phase 3 - AI Service Integration
"""

from typing import Protocol, Optional, Dict, Any, List, runtime_checkable
from dataclasses import dataclass, field
from enum import Enum


class VoiceLanguage(Enum):
    """Supported voice languages."""
    SPANISH = "es"
    ENGLISH = "en"
    ARABIC = "ar"
    FRENCH = "fr"
    GERMAN = "de"
    PORTUGUESE = "pt"
    ITALIAN = "it"
    RUSSIAN = "ru"
    CHINESE = "zh"
    JAPANESE = "ja"


@dataclass
class TTSRequest:
    """Request DTO for Text-to-Speech."""
    text: str
    language: VoiceLanguage = VoiceLanguage.SPANISH
    speed: float = 1.0
    user_id: Optional[str] = None
    cache_enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TTSResponse:
    """Response DTO for Text-to-Speech."""
    audio_path: Optional[str]
    duration_seconds: float = 0.0
    language: VoiceLanguage = VoiceLanguage.SPANISH
    cached: bool = False
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class STTRequest:
    """Request DTO for Speech-to-Text."""
    audio_path: str
    language: Optional[VoiceLanguage] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class STTResponse:
    """Response DTO for Speech-to-Text."""
    text: str
    detected_language: Optional[VoiceLanguage] = None
    confidence: float = 0.0
    duration_seconds: float = 0.0
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class VoiceBiometricsResult:
    """Result of voice biometrics verification."""
    user_id: str
    is_verified: bool
    confidence: float = 0.0
    voice_signature_hash: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class AIVoicePort(Protocol):
    """
    Protocol for voice services (Text-to-Speech + Speech-to-Text).
    
    Replaces VoiceServiceEnterprise from legacy omnix_services/voice_service.
    
    Features:
    - Text-to-Speech (TTS) with gTTS
    - Speech-to-Text (STT) with OpenAI Whisper
    - Voice biometrics (future)
    - Audio caching
    
    SOLID Principles:
    - SRP: Only voice operations
    - ISP: Focused interface for TTS/STT
    - DIP: High-level code depends on this abstraction
    """
    
    async def text_to_speech(
        self,
        request: TTSRequest
    ) -> TTSResponse:
        """
        Convert text to speech audio.
        
        Args:
            request: TTSRequest with text and language options
            
        Returns:
            TTSResponse with audio file path
        """
        ...
    
    async def speech_to_text(
        self,
        request: STTRequest
    ) -> STTResponse:
        """
        Transcribe speech audio to text.
        
        Args:
            request: STTRequest with audio file path
            
        Returns:
            STTResponse with transcribed text
        """
        ...
    
    def get_supported_languages(self) -> List[VoiceLanguage]:
        """Get list of supported languages for TTS/STT."""
        ...
    
    def cleanup_temp_files(self, max_age_seconds: int = 3600) -> int:
        """
        Clean up temporary audio files older than max_age.
        
        Args:
            max_age_seconds: Maximum age of files to keep
            
        Returns:
            Number of files deleted
        """
        ...
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check health of voice services.
        
        Returns:
            Dict with:
            - tts_available: bool
            - stt_available: bool
            - cache_size: int
            - temp_dir_exists: bool
        """
        ...
