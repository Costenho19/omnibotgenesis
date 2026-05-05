"""
🔴 OMNIX REAL CONTEXT PROVIDER - TRANSPARENCIA INSTITUCIONAL
Sistema centralizado para inyectar datos REALES en todas las respuestas de IA

Este módulo garantiza que OMNIX siempre responda con datos verificados:
- Estado del auto-trading (running, trades, win rate, P&L)
- Precios de mercado de Kraken (BTC, ETH, etc.)
- Balance del paper trading
- Posiciones abiertas
- Historial de trades recientes

NUNCA MÁS respuestas inventadas - SIEMPRE datos reales verificados.
"""

from .real_data_provider import (
    OMNIXRealContextProvider, 
    get_real_context_provider,
    set_real_context_provider,
    create_real_context_provider
)

__all__ = [
    'OMNIXRealContextProvider', 
    'get_real_context_provider',
    'set_real_context_provider',
    'create_real_context_provider'
]
