"""
📨 Telegram Message Utilities V6.4 PREMIUM
Helpers for safe message handling with Telegram API limits
"""

import logging
from typing import List

logger = logging.getLogger(__name__)

TELEGRAM_MAX_LENGTH = 4096
SAFE_MAX_LENGTH = 4000


def split_message(message: str, max_length: int = SAFE_MAX_LENGTH) -> List[str]:
    """
    Divide un mensaje largo en partes que respeten el límite de Telegram.
    
    Args:
        message: Mensaje a dividir
        max_length: Longitud máxima por parte (default 4000 para margen de seguridad)
    
    Returns:
        Lista de partes del mensaje
    """
    if not message:
        return []
    
    if len(message) <= max_length:
        return [message]
    
    parts = []
    current_message = message
    
    while current_message:
        if len(current_message) <= max_length:
            parts.append(current_message)
            break
        
        split_point = max_length
        
        for separator in ['\n\n', '\n', '. ', ' ']:
            last_sep = current_message.rfind(separator, 0, max_length)
            if last_sep > max_length // 2:
                split_point = last_sep + len(separator)
                break
        
        parts.append(current_message[:split_point].rstrip())
        current_message = current_message[split_point:].lstrip()
    
    for i, part in enumerate(parts):
        if len(parts) > 1:
            header = f"📄 Parte {i+1}/{len(parts)}\n"
            if i > 0:
                parts[i] = header + part
    
    logger.debug(f"Mensaje dividido en {len(parts)} partes")
    return parts


def truncate_message(message: str, max_length: int = SAFE_MAX_LENGTH) -> str:
    """
    Trunca un mensaje si excede el límite, añadiendo indicador.
    
    Args:
        message: Mensaje a truncar
        max_length: Longitud máxima
    
    Returns:
        Mensaje truncado con indicador si fue necesario
    """
    if not message or len(message) <= max_length:
        return message
    
    truncate_indicator = "\n\n... (mensaje truncado)"
    truncate_point = max_length - len(truncate_indicator)
    
    last_newline = message.rfind('\n', 0, truncate_point)
    if last_newline > truncate_point // 2:
        truncate_point = last_newline
    
    return message[:truncate_point] + truncate_indicator
