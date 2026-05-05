"""
OMNIX INSTITUTIONAL+ - AI Response Validator

Detects and handles corrupted, truncated, or incomplete AI responses.
Implements retry logic for malformed outputs.

Created: Jan 23, 2026
Reason: Fix for "lo mismo" truncation issue where AI generates incomplete responses
"""

import re
from typing import Tuple, Optional, List
from omnix_core.utils.logger import get_logger

logger = get_logger(__name__)


TRUNCATION_PATTERNS = [
    r'\*\d+\.\s*lo\s+mismo\s*$',
    r'\*\d+\.\s*$',
    r'\d+\.\s*$',
    r'\*\d+\s*$',
    r':\s*$',
    r',\s*$',
    r'\.\.\.\s*$',
    r'\s+y\s*$',
    r'\s+con\s*$',
    r'\s+para\s*$',
    r'\s+que\s*$',
    r'\s+de\s*$',
    r'\s+el\s*$',
    r'\s+la\s*$',
    r'\s+los\s*$',
    r'\s+las\s*$',
    r'\s+un\s*$',
    r'\s+una\s*$',
    r'\s+and\s*$',
    r'\s+the\s*$',
    r'\s+with\s*$',
    r'\s+for\s*$',
    r'\s+to\s*$',
]

INCOMPLETE_LIST_PATTERNS = [
    r'\*1\.[^*]+\*2\.\s*(?:lo\s+mismo)\s*$',
    r'\*\d+\.\s{0,3}$',
]

MIN_RESPONSE_LENGTH = 50
MIN_WORD_COUNT = 10


def is_response_incomplete(response: str) -> Tuple[bool, str]:
    """
    Check if an AI response appears to be incomplete or corrupted.
    
    Args:
        response: The AI-generated response text
        
    Returns:
        Tuple of (is_incomplete: bool, reason: str)
    """
    if not response:
        return True, "EMPTY_RESPONSE"
    
    response_stripped = response.strip()
    
    if len(response_stripped) < MIN_RESPONSE_LENGTH:
        return True, f"TOO_SHORT: {len(response_stripped)} chars < {MIN_RESPONSE_LENGTH}"
    
    word_count = len(response_stripped.split())
    if word_count < MIN_WORD_COUNT:
        return True, f"TOO_FEW_WORDS: {word_count} words < {MIN_WORD_COUNT}"
    
    for pattern in TRUNCATION_PATTERNS:
        if re.search(pattern, response_stripped, re.IGNORECASE):
            return True, f"TRUNCATION_PATTERN: matched '{pattern}'"
    
    for pattern in INCOMPLETE_LIST_PATTERNS:
        if re.search(pattern, response_stripped, re.IGNORECASE | re.DOTALL):
            return True, f"INCOMPLETE_LIST: matched '{pattern}'"
    
    if 'lo mismo' in response_stripped.lower() and response_stripped.lower().endswith('lo mismo'):
        return True, "ENDS_WITH_LO_MISMO"
    
    numbered_items = re.findall(r'\*(\d+)\.', response_stripped)
    if numbered_items:
        numbers = [int(n) for n in numbered_items]
        if len(numbers) >= 1:
            last_item_match = re.search(rf'\*{numbers[-1]}\.\s*([^*\n]*)', response_stripped)
            if last_item_match:
                last_item_content = last_item_match.group(1).strip()
                if len(last_item_content) < 10:
                    return True, f"INCOMPLETE_NUMBERED_LIST: item {numbers[-1]} too short ({len(last_item_content)} chars)"
    
    return False, "OK"


def validate_and_log_response(
    response: str,
    user_message: str,
    provider: str = "unknown"
) -> Tuple[bool, str, Optional[str]]:
    """
    Validate an AI response and log any issues found.
    
    Args:
        response: The AI-generated response
        user_message: Original user query (for logging context)
        provider: AI provider name (gemini, openai, etc.)
        
    Returns:
        Tuple of (is_valid: bool, reason: str, sanitized_response: Optional[str])
    """
    is_incomplete, reason = is_response_incomplete(response)
    
    if is_incomplete:
        logger.warning(
            f"⚠️ [RESPONSE_VALIDATOR] INCOMPLETE RESPONSE DETECTED | "
            f"Provider={provider} | Reason={reason} | "
            f"Query={user_message[:50]}... | "
            f"ResponseEnd=...{response[-100:] if len(response) > 100 else response}"
        )
        return False, reason, None
    
    logger.debug(f"✅ [RESPONSE_VALIDATOR] Response OK | Provider={provider} | Length={len(response)}")
    return True, "OK", response


def create_retry_prompt(original_message: str, failed_reason: str) -> str:
    """
    Create an enhanced prompt for retry after a failed/incomplete response.
    
    Args:
        original_message: The original user message
        failed_reason: Why the previous response was rejected
        
    Returns:
        Enhanced prompt with explicit instructions for complete response
    """
    retry_instruction = """
INSTRUCCIÓN CRÍTICA: Tu respuesta anterior fue detectada como INCOMPLETA o TRUNCADA.
Por favor, genera una respuesta COMPLETA y bien estructurada.

REGLAS PARA ESTA RESPUESTA:
1. Si usas listas numeradas, COMPLETA TODOS los puntos (no dejes ninguno vacío)
2. Termina cada oración correctamente con puntuación apropiada
3. No uses frases como "lo mismo" o "idem" - explica cada punto completamente
4. Asegúrate de que la respuesta tenga una conclusión clara
5. Máximo 800 palabras pero mínimo 100 palabras

PREGUNTA DEL USUARIO:
"""
    return retry_instruction + original_message


def should_retry_response(
    response: str,
    retry_count: int,
    max_retries: int = 2
) -> bool:
    """
    Determine if we should retry generating a response.
    
    Args:
        response: Current response
        retry_count: How many retries we've already done
        max_retries: Maximum allowed retries
        
    Returns:
        True if we should retry
    """
    if retry_count >= max_retries:
        logger.warning(f"⚠️ [RESPONSE_VALIDATOR] Max retries ({max_retries}) reached, accepting response")
        return False
    
    is_incomplete, reason = is_response_incomplete(response)
    
    if is_incomplete:
        logger.info(f"🔄 [RESPONSE_VALIDATOR] Retry {retry_count + 1}/{max_retries} triggered: {reason}")
        return True
    
    return False


def sanitize_incomplete_response(response: str) -> str:
    """
    Try to salvage an incomplete response by cleaning it up.
    Used as last resort when retries are exhausted.
    
    Args:
        response: The incomplete response
        
    Returns:
        Cleaned up response with truncation indicator
    """
    if not response:
        return "No pude generar una respuesta completa. Por favor, intenta reformular tu pregunta."
    
    response = response.strip()
    
    response = re.sub(r'\*\d+\.\s*lo\s+mismo\s*$', '', response, flags=re.IGNORECASE)
    response = re.sub(r'\*\d+\.\s*$', '', response)
    response = re.sub(r'\d+\.\s*$', '', response)
    
    response = re.sub(r'[,:\s]+$', '', response)
    
    if response and not response.endswith(('.', '!', '?', ':', ')')):
        response += '.'
    
    if len(response) > MIN_RESPONSE_LENGTH:
        response += "\n\n_(Respuesta resumida por límite de procesamiento)_"
    
    return response.strip()
