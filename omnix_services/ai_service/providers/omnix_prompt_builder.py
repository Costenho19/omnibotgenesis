"""
OMNIX INSTITUTIONAL+ - Omnix Prompt Builder

Concrete implementation of PromptBuilderProtocol.
Delegates to existing PromptsContextManager for backward compatibility.

Part of Phase 2: Complete DI Container (AI Service Refactoring Roadmap)
"""

from typing import Dict, List, Any, Optional, TYPE_CHECKING
from omnix_core.utils.logger import get_logger
from omnix_config import VERSION_BANNER
from omnix_services.ai_service.interfaces.prompt_builder import (
    PromptBuilderProtocol,
    PromptContext,
    UserIntent,
)

if TYPE_CHECKING:
    from omnix_services.ai_service.ai_prompts import PromptsContextManager

logger = get_logger(__name__)


INTENT_INSTRUCTIONS = {
    UserIntent.GREETING: """Responde de manera amigable y profesional.
Menciona brevemente tu disponibilidad para análisis de mercado.
Mantén la respuesta corta (2-3 oraciones).""",

    UserIntent.MARKET_ANALYSIS: """Eres un analista cuantitativo senior de OMNIX INSTITUTIONAL+.

MOTORES DE ANÁLISIS ACTIVOS:
- Monte Carlo Simulation (10,000 iteraciones)
- Black Swan Detection (riesgo de cola)
- HMM Regime Analysis (estado del mercado)
- Kalman Filter (reducción de ruido)
- Non-Markovian Memory Kernel (patrones temporales)

FORMATO DE RESPUESTA:
1. Resumen Ejecutivo (2 líneas)
2. Análisis Técnico con datos REALES del contexto
3. Riesgos Identificados
4. Recomendación Clara (LONG / SHORT / NEUTRAL)

CRÍTICO: Usa SOLO datos reales del contexto proporcionado.
NUNCA inventes precios, porcentajes o datos de mercado.""",

    UserIntent.TRADING_QUERY: """Eres un ejecutor de trades institucional.

ANTES DE CONFIRMAR CUALQUIER TRADE:
1. Verifica el símbolo exacto (BTC, ETH, etc.)
2. Confirma el monto en USD
3. Muestra precio actual de mercado
4. Muestra comisiones estimadas

NUNCA ejecutes un trade sin confirmación explícita del usuario.""",

    UserIntent.PORTFOLIO: """Eres un gestor de portfolios institucional.

MOSTRAR:
- Balance actual por activo
- P&L total y por posición
- Métricas de exposición al riesgo
- Sugerencias de rebalanceo (si aplica)

Usa datos del contexto proporcionado.
Formatea números claramente con símbolos de moneda.""",

    UserIntent.HELP: """Eres una guía del sistema OMNIX.

COMANDOS PRINCIPALES:
/autotrading start|stop|status - Bot de trading automatizado
/paper_buy BTC 100 - Compra simulada ($100 de BTC)
/paper_sell ETH 50 - Venta simulada
/balance - Ver balance actual
/analysis BTC - Análisis técnico

Responde concisamente con ejemplos claros.""",

    UserIntent.GENERAL: """Eres un asistente conversacional.
Mantén el contexto de trading pero permite conversación casual.
Si detectas oportunidad de ofrecer análisis de mercado, sugiérelo sutilmente.
Mantén respuestas amigables y profesionales.""",

    UserIntent.VIDEO_ANALYSIS: """Eres un analizador de videos/imágenes financieras.
Examina el contenido visual proporcionado.
Identifica gráficos, indicadores técnicos, niveles de precio.
Proporciona análisis basado en lo que observas.""",

    UserIntent.NEWS: """Eres un analista de noticias financieras.
Sintetiza las noticias relevantes del mercado.
Identifica impacto potencial en precios.
Cita fuentes cuando sea posible.""",

    UserIntent.TECHNICAL: """Eres un experto en análisis técnico.
Explica conceptos técnicos de manera clara.
Usa ejemplos prácticos cuando sea útil.
Adapta la complejidad al nivel del usuario."""
}


class OmnixPromptBuilder:
    """
    Concrete implementation of PromptBuilderProtocol.
    
    Wraps the existing PromptsContextManager while providing
    a clean interface that follows the protocol contract.
    
    This allows gradual migration to the new DI-based architecture
    while maintaining backward compatibility.
    """
    
    def __init__(self, prompts_manager: Optional["PromptsContextManager"] = None):
        """
        Initialize with optional PromptsContextManager.
        
        Args:
            prompts_manager: Existing prompts manager to delegate to.
                           If None, will be lazy-loaded.
        """
        self._prompts_manager = prompts_manager
        self._initialized = False
        logger.info("OmnixPromptBuilder created (lazy initialization)")
    
    def _ensure_initialized(self) -> None:
        """Lazy initialization of prompts manager."""
        if self._initialized:
            return
        
        if self._prompts_manager is None:
            try:
                from omnix_services.ai_service.ai_prompts import PromptsContextManager
                self._prompts_manager = PromptsContextManager()
                logger.info("PromptsContextManager loaded")
            except ImportError as e:
                logger.error(f"Failed to load PromptsContextManager: {e}")
        
        self._initialized = True
    
    def analyze_intent(self, message: str) -> UserIntent:
        """
        Analyze user message to determine intent.
        
        Delegates to PromptsContextManager.analyze_intent() and maps
        the string result to UserIntent enum.
        """
        self._ensure_initialized()
        
        if self._prompts_manager is None:
            return UserIntent.GENERAL
        
        try:
            intent_str = self._prompts_manager.analyze_intent(message)
            
            intent_mapping = {
                "greeting": UserIntent.GREETING,
                "market_analysis": UserIntent.MARKET_ANALYSIS,
                "trading_query": UserIntent.TRADING_QUERY,
                "trading": UserIntent.TRADING_QUERY,
                "portfolio": UserIntent.PORTFOLIO,
                "help": UserIntent.HELP,
                "general": UserIntent.GENERAL,
                "video_analysis": UserIntent.VIDEO_ANALYSIS,
                "news": UserIntent.NEWS,
                "technical": UserIntent.TECHNICAL,
            }
            
            return intent_mapping.get(intent_str.lower(), UserIntent.GENERAL)
            
        except Exception as e:
            logger.error(f"Error analyzing intent: {e}")
            return UserIntent.GENERAL
    
    def build_system_prompt(
        self,
        context: PromptContext
    ) -> str:
        """
        Build complete system prompt with all context.
        
        Combines:
        - Base system instructions
        - Intent-specific instructions
        - Market data context
        - Trading context
        - Web search results
        """
        self._ensure_initialized()
        
        parts = []
        
        parts.append(f"Eres OMNIX {VERSION_BANNER}, un asistente de trading institucional avanzado.")
        parts.append(f"\nUsuario: {context.user_name}")
        
        intent_instructions = self.get_intent_specific_instructions(context.intent)
        if intent_instructions:
            parts.append(f"\n{intent_instructions}")
        
        if context.real_context_data:
            parts.append("\n\nCONTEXTO REAL DEL SISTEMA:")
            parts.append(self._format_context_data(context.real_context_data))
        
        if context.market_data:
            parts.append("\n\nDATOS DE MERCADO EN TIEMPO REAL:")
            parts.append(self._format_market_data(context.market_data))
        
        if context.trading_context:
            parts.append("\n\nCONTEXTO DE TRADING:")
            parts.append(self._format_trading_context(context.trading_context))
        
        if context.web_search_results:
            parts.append("\n\nRESULTADOS DE BÚSQUEDA WEB:")
            parts.append(context.web_search_results)
        
        parts.append("\n\nIMPORTANTE: Responde SIEMPRE en el mismo idioma que el usuario escriba su mensaje. Mantén un tono profesional pero accesible.")
        
        return "\n".join(parts)
    
    def build_user_prompt(
        self,
        context: PromptContext
    ) -> str:
        """
        Build formatted user prompt.
        
        Includes conversation history for context continuity.
        """
        self._ensure_initialized()
        
        parts = []
        
        if context.conversation_history:
            truncated = self.truncate_history(context.conversation_history)
            if truncated:
                parts.append("Historial reciente de conversación:")
                for msg in truncated:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")[:200]
                    parts.append(f"[{role}]: {content}")
                parts.append("")
        
        parts.append(f"Mensaje actual del usuario: {context.user_message}")
        
        return "\n".join(parts)
    
    def get_intent_specific_instructions(
        self,
        intent: UserIntent
    ) -> str:
        """Get specialized instructions for a specific intent."""
        return INTENT_INSTRUCTIONS.get(intent, INTENT_INSTRUCTIONS[UserIntent.GENERAL])
    
    def truncate_history(
        self,
        history: List[Dict[str, str]],
        max_messages: int = 10
    ) -> List[Dict[str, str]]:
        """Truncate conversation history to fit context window."""
        if not history:
            return []
        
        return history[-max_messages:]
    
    def _format_context_data(self, data: Dict[str, Any]) -> str:
        """Format real context data for inclusion in prompt."""
        if not data:
            return "No disponible"
        
        lines = []
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"- {key}:")
                for k, v in value.items():
                    lines.append(f"  - {k}: {v}")
            else:
                lines.append(f"- {key}: {value}")
        
        return "\n".join(lines)
    
    def _format_market_data(self, data: Dict[str, Any]) -> str:
        """Format market data for inclusion in prompt."""
        if not data:
            return "No disponible"
        
        lines = []
        for symbol, info in data.items():
            if isinstance(info, dict):
                price = info.get("price", "N/A")
                change = info.get("change_24h", "N/A")
                lines.append(f"- {symbol}: ${price} ({change}% 24h)")
            else:
                lines.append(f"- {symbol}: {info}")
        
        return "\n".join(lines) if lines else "No disponible"
    
    def _format_trading_context(self, data: Dict[str, Any]) -> str:
        """Format trading context for inclusion in prompt."""
        if not data:
            return "No disponible"
        
        lines = []
        
        if "positions" in data:
            lines.append("Posiciones abiertas:")
            for pos in data["positions"]:
                lines.append(f"  - {pos}")
        
        if "balance" in data:
            lines.append(f"Balance: ${data['balance']}")
        
        if "pnl" in data:
            lines.append(f"P&L: ${data['pnl']}")
        
        return "\n".join(lines) if lines else "No disponible"
