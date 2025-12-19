"""
AI Error Handler Module - OMNIX V6.5.4d INSTITUTIONAL+
Enterprise-grade error handling for AI SDKs (Gemini, OpenAI, Anthropic)

Based on 2025 SDK best practices:
- google-genai: errors.APIError with e.code and e.message
- openai: Specific exception classes (AuthenticationError, RateLimitError, etc.)
- anthropic: Similar pattern to OpenAI
"""

import logging
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Classification of AI API errors for retry/skip decisions"""
    AUTH_ERROR = "auth_error"           # 401, 403 - API key issues (non-retryable)
    RATE_LIMIT = "rate_limit"           # 429 - Rate limit exceeded (retryable with backoff)
    SERVER_ERROR = "server_error"       # 500, 502, 503, 504 - Server issues (retryable)
    TIMEOUT = "timeout"                 # Request timeout (retryable)
    VALIDATION = "validation"           # 400, 422 - Bad request (non-retryable)
    NOT_FOUND = "not_found"             # 404 - Model not found (non-retryable)
    QUOTA_EXCEEDED = "quota_exceeded"   # Billing/quota issues (non-retryable)
    CONTENT_FILTERED = "content_filtered"  # Safety filters blocked content
    UNKNOWN = "unknown"                 # Unclassified error


@dataclass
class AIError:
    """Structured error information from AI API calls"""
    provider: str           # gemini, openai, anthropic
    category: ErrorCategory
    http_code: Optional[int]
    message: str
    raw_error: Optional[Exception]
    is_retryable: bool
    suggested_action: str
    
    def log_message(self) -> str:
        """Generate diagnostic log message"""
        code_str = f"[{self.http_code}]" if self.http_code else ""
        return f"❌ {self.provider.upper()} {code_str} {self.message}"
    
    def user_message(self) -> str:
        """Generate user-friendly message (AI-FIRST: minimal English placeholder)"""
        messages = {
            ErrorCategory.AUTH_ERROR: f"🔑 {self.provider}: API key issue",
            ErrorCategory.RATE_LIMIT: f"⏳ {self.provider}: Rate limit, retrying...",
            ErrorCategory.SERVER_ERROR: f"🔧 {self.provider}: Server error",
            ErrorCategory.TIMEOUT: f"⏱️ {self.provider}: Timeout",
            ErrorCategory.VALIDATION: f"⚠️ {self.provider}: Validation error",
            ErrorCategory.NOT_FOUND: f"❓ {self.provider}: Model not found",
            ErrorCategory.QUOTA_EXCEEDED: f"💰 {self.provider}: API quota exceeded",
            ErrorCategory.CONTENT_FILTERED: f"🛡️ {self.provider}: Content filtered",
            ErrorCategory.UNKNOWN: f"❌ {self.provider}: Unknown error",
        }
        return messages.get(self.category, f"❌ {self.provider}: Error")


class ErrorClassifier:
    """Classifies errors from different AI SDKs into standardized categories"""
    
    # HTTP codes that are retryable
    RETRYABLE_CODES = {429, 500, 502, 503, 504}
    
    # HTTP codes that should skip immediately to next model
    NON_RETRYABLE_CODES = {400, 401, 403, 404, 422}
    
    @classmethod
    def classify_gemini_error(cls, error: Exception) -> AIError:
        """Classify errors from Google Gemini SDK (google-genai)"""
        try:
            from google.genai import errors as gemini_errors
            
            if isinstance(error, gemini_errors.APIError):
                code = getattr(error, 'code', None)
                message = getattr(error, 'message', str(error))
                
                return cls._classify_by_code(
                    provider="gemini",
                    code=code,
                    message=message,
                    raw_error=error
                )
        except ImportError:
            pass
        
        error_str = str(error).lower()
        
        if "api key" in error_str or "authentication" in error_str or "401" in error_str:
            return AIError(
                provider="gemini",
                category=ErrorCategory.AUTH_ERROR,
                http_code=401,
                message="API key inválida - Verificar GEMINI_API_KEY",
                raw_error=error,
                is_retryable=False,
                suggested_action="Verificar que GEMINI_API_KEY está configurada correctamente en Railway"
            )
        
        if "rate" in error_str or "quota" in error_str or "429" in error_str:
            return AIError(
                provider="gemini",
                category=ErrorCategory.RATE_LIMIT,
                http_code=429,
                message="Rate limit excedido - Esperando antes de reintentar",
                raw_error=error,
                is_retryable=True,
                suggested_action="Implementar exponential backoff"
            )
        
        if "500" in error_str or "503" in error_str or "internal" in error_str:
            return AIError(
                provider="gemini",
                category=ErrorCategory.SERVER_ERROR,
                http_code=500,
                message="Error del servidor de Gemini",
                raw_error=error,
                is_retryable=True,
                suggested_action="Reintentar con backoff"
            )
        
        if "safety" in error_str or "blocked" in error_str:
            return AIError(
                provider="gemini",
                category=ErrorCategory.CONTENT_FILTERED,
                http_code=None,
                message="Contenido bloqueado por filtros de seguridad",
                raw_error=error,
                is_retryable=False,
                suggested_action="Modificar el prompt para evitar contenido sensible"
            )
        
        return AIError(
            provider="gemini",
            category=ErrorCategory.UNKNOWN,
            http_code=None,
            message=str(error)[:200],
            raw_error=error,
            is_retryable=False,
            suggested_action="Revisar logs para más detalles"
        )
    
    @classmethod
    def classify_openai_error(cls, error: Exception) -> AIError:
        """Classify errors from OpenAI SDK"""
        try:
            import openai
            
            if isinstance(error, openai.AuthenticationError):
                return AIError(
                    provider="openai",
                    category=ErrorCategory.AUTH_ERROR,
                    http_code=401,
                    message="API key inválida - Verificar OPENAI_API_KEY",
                    raw_error=error,
                    is_retryable=False,
                    suggested_action="Verificar que OPENAI_API_KEY está configurada y es válida"
                )
            
            if isinstance(error, openai.RateLimitError):
                return AIError(
                    provider="openai",
                    category=ErrorCategory.RATE_LIMIT,
                    http_code=429,
                    message="Rate limit excedido",
                    raw_error=error,
                    is_retryable=True,
                    suggested_action="Esperar 60s antes de reintentar"
                )
            
            if isinstance(error, openai.APIConnectionError):
                return AIError(
                    provider="openai",
                    category=ErrorCategory.SERVER_ERROR,
                    http_code=None,
                    message="Error de conexión con OpenAI",
                    raw_error=error,
                    is_retryable=True,
                    suggested_action="Verificar conectividad de red"
                )
            
            if isinstance(error, openai.APITimeoutError):
                return AIError(
                    provider="openai",
                    category=ErrorCategory.TIMEOUT,
                    http_code=None,
                    message="Timeout de OpenAI",
                    raw_error=error,
                    is_retryable=True,
                    suggested_action="Aumentar timeout o reducir complejidad del prompt"
                )
            
            if isinstance(error, openai.PermissionDeniedError):
                return AIError(
                    provider="openai",
                    category=ErrorCategory.AUTH_ERROR,
                    http_code=403,
                    message="Permiso denegado - Verificar permisos de API key",
                    raw_error=error,
                    is_retryable=False,
                    suggested_action="Verificar que la API key tiene permisos para GPT-4"
                )
            
            if isinstance(error, openai.NotFoundError):
                return AIError(
                    provider="openai",
                    category=ErrorCategory.NOT_FOUND,
                    http_code=404,
                    message="Modelo no encontrado",
                    raw_error=error,
                    is_retryable=False,
                    suggested_action="Verificar nombre del modelo"
                )
            
            if isinstance(error, openai.InternalServerError):
                return AIError(
                    provider="openai",
                    category=ErrorCategory.SERVER_ERROR,
                    http_code=500,
                    message="Error interno de OpenAI",
                    raw_error=error,
                    is_retryable=True,
                    suggested_action="Reintentar con backoff"
                )
            
            if isinstance(error, openai.BadRequestError):
                return AIError(
                    provider="openai",
                    category=ErrorCategory.VALIDATION,
                    http_code=400,
                    message=f"Bad request: {str(error)[:100]}",
                    raw_error=error,
                    is_retryable=False,
                    suggested_action="Revisar parámetros del request"
                )
            
            if isinstance(error, openai.APIError):
                status = getattr(error, 'status_code', None)
                return cls._classify_by_code(
                    provider="openai",
                    code=status,
                    message=str(error)[:200],
                    raw_error=error
                )
                
        except ImportError:
            pass
        
        error_str = str(error).lower()
        
        if "401" in error_str or "unauthorized" in error_str or "invalid_api_key" in error_str:
            return AIError(
                provider="openai",
                category=ErrorCategory.AUTH_ERROR,
                http_code=401,
                message="API key inválida - Verificar OPENAI_API_KEY",
                raw_error=error,
                is_retryable=False,
                suggested_action="Actualizar OPENAI_API_KEY en Railway"
            )
        
        return AIError(
            provider="openai",
            category=ErrorCategory.UNKNOWN,
            http_code=None,
            message=str(error)[:200],
            raw_error=error,
            is_retryable=False,
            suggested_action="Revisar logs para más detalles"
        )
    
    @classmethod
    def classify_anthropic_error(cls, error: Exception) -> AIError:
        """Classify errors from Anthropic SDK"""
        try:
            import anthropic
            
            if isinstance(error, anthropic.AuthenticationError):
                return AIError(
                    provider="anthropic",
                    category=ErrorCategory.AUTH_ERROR,
                    http_code=401,
                    message="API key inválida - Verificar ANTHROPIC_API_KEY",
                    raw_error=error,
                    is_retryable=False,
                    suggested_action="Configurar ANTHROPIC_API_KEY en Railway"
                )
            
            if isinstance(error, anthropic.RateLimitError):
                return AIError(
                    provider="anthropic",
                    category=ErrorCategory.RATE_LIMIT,
                    http_code=429,
                    message="Rate limit excedido",
                    raw_error=error,
                    is_retryable=True,
                    suggested_action="Esperar antes de reintentar"
                )
            
            if isinstance(error, anthropic.APIConnectionError):
                return AIError(
                    provider="anthropic",
                    category=ErrorCategory.SERVER_ERROR,
                    http_code=None,
                    message="Error de conexión con Anthropic",
                    raw_error=error,
                    is_retryable=True,
                    suggested_action="Verificar conectividad"
                )
            
            if isinstance(error, anthropic.InternalServerError):
                return AIError(
                    provider="anthropic",
                    category=ErrorCategory.SERVER_ERROR,
                    http_code=500,
                    message="Error interno de Anthropic",
                    raw_error=error,
                    is_retryable=True,
                    suggested_action="Reintentar con backoff"
                )
            
            if isinstance(error, anthropic.APIError):
                status = getattr(error, 'status_code', None)
                return cls._classify_by_code(
                    provider="anthropic",
                    code=status,
                    message=str(error)[:200],
                    raw_error=error
                )
                
        except ImportError:
            pass
        
        return AIError(
            provider="anthropic",
            category=ErrorCategory.UNKNOWN,
            http_code=None,
            message=str(error)[:200],
            raw_error=error,
            is_retryable=False,
            suggested_action="Configurar ANTHROPIC_API_KEY si no está configurada"
        )
    
    @classmethod
    def _classify_by_code(
        cls, 
        provider: str, 
        code: Optional[int], 
        message: str, 
        raw_error: Exception
    ) -> AIError:
        """Classify error by HTTP status code"""
        
        if code == 400:
            return AIError(
                provider=provider,
                category=ErrorCategory.VALIDATION,
                http_code=400,
                message=f"Bad request: {message[:100]}",
                raw_error=raw_error,
                is_retryable=False,
                suggested_action="Revisar parámetros del request"
            )
        
        if code == 401:
            return AIError(
                provider=provider,
                category=ErrorCategory.AUTH_ERROR,
                http_code=401,
                message=f"API key inválida - Verificar {provider.upper()}_API_KEY",
                raw_error=raw_error,
                is_retryable=False,
                suggested_action=f"Actualizar {provider.upper()}_API_KEY en Railway"
            )
        
        if code == 403:
            return AIError(
                provider=provider,
                category=ErrorCategory.AUTH_ERROR,
                http_code=403,
                message="Acceso denegado - API key puede estar bloqueada",
                raw_error=raw_error,
                is_retryable=False,
                suggested_action="Verificar estado de la API key en el dashboard del proveedor"
            )
        
        if code == 404:
            return AIError(
                provider=provider,
                category=ErrorCategory.NOT_FOUND,
                http_code=404,
                message="Modelo no encontrado",
                raw_error=raw_error,
                is_retryable=False,
                suggested_action="Verificar nombre del modelo"
            )
        
        if code == 429:
            return AIError(
                provider=provider,
                category=ErrorCategory.RATE_LIMIT,
                http_code=429,
                message="Rate limit excedido",
                raw_error=raw_error,
                is_retryable=True,
                suggested_action="Esperar 30-60s antes de reintentar"
            )
        
        if code in (500, 502, 503, 504):
            return AIError(
                provider=provider,
                category=ErrorCategory.SERVER_ERROR,
                http_code=code,
                message=f"Error del servidor ({code})",
                raw_error=raw_error,
                is_retryable=True,
                suggested_action="Reintentar con exponential backoff"
            )
        
        return AIError(
            provider=provider,
            category=ErrorCategory.UNKNOWN,
            http_code=code,
            message=message[:200],
            raw_error=raw_error,
            is_retryable=code in cls.RETRYABLE_CODES if code else False,
            suggested_action="Revisar logs para más detalles"
        )
    
    @classmethod
    def classify_timeout(cls, provider: str, timeout_seconds: float) -> AIError:
        """Create AIError for timeout"""
        return AIError(
            provider=provider,
            category=ErrorCategory.TIMEOUT,
            http_code=None,
            message=f"Timeout después de {timeout_seconds}s",
            raw_error=None,
            is_retryable=True,
            suggested_action="Considerar aumentar el timeout o simplificar el prompt"
        )


def log_ai_error(ai_error: AIError, attempt: int = 1, max_attempts: int = 3) -> None:
    """Log AI error with structured format"""
    log_msg = ai_error.log_message()
    
    if ai_error.is_retryable:
        logger.warning(f"{log_msg} | Intento {attempt}/{max_attempts} | Acción: {ai_error.suggested_action}")
    else:
        logger.error(f"{log_msg} | NON-RETRYABLE | Acción: {ai_error.suggested_action}")


def should_skip_to_next_model(ai_error: AIError) -> bool:
    """Determine if we should skip retries and go to next model immediately"""
    non_retryable_categories = {
        ErrorCategory.AUTH_ERROR,
        ErrorCategory.VALIDATION,
        ErrorCategory.NOT_FOUND,
        ErrorCategory.QUOTA_EXCEEDED,
    }
    return ai_error.category in non_retryable_categories
