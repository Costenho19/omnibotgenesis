"""
OMNIX V5.1 ENTERPRISE - Conversational AI Service
Main orchestrator for AI functionality
Reemplaza la clase ConversationalAI de main.py (1,133 líneas)
Escalabilidad: 50K+ usuarios con stateless design
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from .ai_models import AIModelsManager
from .ai_styles import VisualStylesManager
from .ai_prompts import PromptsContextManager
from omnix_core.cache.redis_cache import cache
from omnix_core.cache.redis_state import (
    get_conversation_history,
    get_user_preferences,
    get_market_context
)
from omnix_core.utils.logger import get_logger
from omnix_core.utils.rate_limiter import rate_limit, RateLimitExceeded
from omnix_config.settings import settings

logger = get_logger(__name__)


class ConversationalAIService:
    """
    Enterprise Conversational AI Service
    
    Orchestrates AI models, prompts, styles, and context management.
    Designed for horizontal scaling with stateless architecture.
    """
    
    def __init__(self):
        """Initialize AI service with all managers"""
        
        # Initialize sub-managers
        self.models = AIModelsManager()
        self.styles = VisualStylesManager()
        self.prompts = PromptsContextManager()
        
        # ✅ REDIS-BACKED STATE (Horizontal Scaling Ready)
        self.conversation_history = get_conversation_history()
        self.user_preferences = get_user_preferences()
        self.market_context = get_market_context()
        
        # Intelligence level
        self.intelligence_level = "ULTRA_COMPETITIVE_ENTERPRISE"
        
        # Prediction models configuration
        self.prediction_models = {
            'monte_carlo_advanced': {'active': True, 'accuracy': 0.847},
            'lstm_neural_network': {'active': True, 'accuracy': 0.823},
            'gradient_boosting': {'active': True, 'accuracy': 0.791},
            'transformer_attention': {'active': True, 'accuracy': 0.856},
            'ensemble_meta_model': {'active': True, 'accuracy': 0.872}
        }
        
        logger.info("🧠 Conversational AI Service initialized successfully")
        logger.info(f"🚀 Intelligence level: {self.intelligence_level}")
        
        # Check AI models health
        health = self.models.health_check()
        logger.info(f"🔍 AI Models Health: {health}")
    
    @rate_limit(
        max_requests=30, 
        window=60,
        identifier_func=lambda self, *args, **kwargs: str(kwargs.get('chat_id', args[0] if args else 'global'))
    )  # 30 requests per minute PER USER (robust extraction)
    async def generate_response(
        self,
        chat_id: int,
        user_message: str,
        user_name: str = 'Usuario',
        market_data: Optional[Dict[str, Any]] = None,
        apply_visual_style: bool = True
    ) -> Dict[str, Any]:
        """
        Generate AI response with full context and styling
        
        Args:
            user_message: User's message text
            chat_id: Unique chat identifier
            user_name: User's name
            market_data: Optional market data context
            apply_visual_style: Whether to apply visual formatting
            
        Returns:
            Response dictionary with text and metadata
        """
        
        try:
            # 1. Analyze intent
            intent = self.prompts.analyze_intent(user_message)
            logger.info(f"🎯 Intent detected: {intent}")
            
            # 2. Build user context
            history = self._get_conversation_history(chat_id)
            context = self.prompts.build_user_context(
                chat_id=chat_id,
                user_message=user_message,
                user_name=user_name,
                conversation_history=history
            )
            
            # 3. Add to conversation history
            self._add_to_history(chat_id, {
                'user': user_message,
                'timestamp': datetime.now().isoformat(),
                'intent': intent,
                'user_name': user_name
            })
            
            # 4. Prepare additional context
            additional_context = {}
            if market_data:
                additional_context.update(market_data)
            
            # 5. Build system prompt WITH CONVERSATION HISTORY
            system_prompt = self.prompts.build_system_prompt(
                intent=intent,
                user_name=user_name,
                additional_context=additional_context,
                conversation_history=history
            )
            
            # 6. Generate AI response (ASYNC VERDADERO)
            ai_response = await self.models.generate(
                prompt=user_message,
                system_prompt=system_prompt,
                model=settings.ai.primary_model
            )
            
            if not ai_response:
                logger.error("❌ Failed to generate AI response")
                ai_response = self._get_fallback_response(intent)
            
            # 7. Apply visual styling
            if apply_visual_style:
                current_price = market_data.get('price', 0.0) if market_data else 0.0
                styled_response = self.styles.apply_ultra_visual_style(
                    response_text=ai_response,
                    intent=intent,
                    current_price=current_price
                )
            else:
                styled_response = ai_response
            
            # 8. Add AI response to history
            self._add_to_history(chat_id, {
                'ai': styled_response,
                'timestamp': datetime.now().isoformat(),
                'intent': intent
            })
            
            # 9. Return response with metadata
            return {
                'success': True,
                'response': styled_response,
                'intent': intent,
                'context': context,
                'model_used': self.models.primary_model,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating response: {e}")
            return {
                'success': False,
                'response': self._get_error_response(),
                'error': str(e)
            }
    
    def _get_conversation_history(self, chat_id: int) -> List[Dict]:
        """
        Get conversation history for chat_id.
        
        FIX Nov 28, 2025: Primero intenta Redis, si está vacío usa PostgreSQL
        Esto garantiza que el bot recuerde conversaciones incluso después de restart
        """
        # 1. Intentar Redis primero (más rápido)
        redis_history = self.conversation_history.get_history(chat_id)
        if redis_history and len(redis_history) > 0:
            logger.debug(f"🧠 Historial cargado de Redis: {len(redis_history)} mensajes")
            return redis_history
        
        # 2. Si Redis está vacío, intentar PostgreSQL (persistente)
        try:
            from omnix_services.database_service.database_manager import DatabaseManager
            db_manager = DatabaseManager()
            if db_manager.using_enterprise:
                pg_history = db_manager.get_conversation_history(chat_id, limit=10)
                if pg_history and len(pg_history) > 0:
                    logger.info(f"🧠 Historial cargado de PostgreSQL: {len(pg_history)} mensajes (Redis vacío)")
                    # Opcionalmente: sincronizar a Redis para próximas consultas
                    for msg in pg_history:
                        if 'user' in msg:
                            self.conversation_history.add_message(chat_id, msg)
                    return pg_history
        except Exception as e:
            logger.warning(f"⚠️ No se pudo cargar historial de PostgreSQL: {e}")
        
        # 3. No hay historial
        logger.debug(f"🧠 No hay historial para chat {chat_id}")
        return []
    
    def _add_to_history(self, chat_id: int, message: Dict):
        """Add message to conversation history in Redis"""
        self.conversation_history.add_message(chat_id, message)
    
    def _get_fallback_response(self, intent: str) -> str:
        """Get fallback response when AI fails"""
        fallback_responses = {
            'trading_action': "⚠️ Sistema de trading temporalmente ocupado. Intenta de nuevo en unos segundos.",
            'price_inquiry': "⚠️ Datos de precios temporalmente no disponibles. Reintentando...",
            'market_analysis': "⚠️ Sistema de análisis temporalmente ocupado. Intenta de nuevo pronto.",
            'general_conversation': "⚠️ Sistema temporalmente ocupado. Harold, intenta de nuevo en unos segundos."
        }
        return fallback_responses.get(intent, fallback_responses['general_conversation'])
    
    def _get_error_response(self) -> str:
        """Get error response"""
        return """❌ Error en sistema de IA

🔧 **Acciones recomendadas:**
1. Verificar conexión a internet
2. Intentar de nuevo en unos segundos
3. Si persiste, contactar soporte técnico

💎 OMNIX V5.1 Enterprise"""
    
    def clear_history(self, chat_id: int):
        """Clear conversation history for chat_id from Redis"""
        self.conversation_history.clear_history(chat_id)
    
    def get_user_preferences(self, chat_id: int) -> Dict[str, Any]:
        """Get user preferences from Redis"""
        return self.user_preferences.get_preferences(chat_id)
    
    def set_user_preference(self, chat_id: int, key: str, value: Any):
        """Set user preference in Redis"""
        self.user_preferences.set_preference(chat_id, key, value)
    
    def update_market_context(self, symbol: str, data: Dict[str, Any]):
        """Update global market context in Redis"""
        self.market_context.update_market_data(symbol, data)
        logger.debug(f"📊 Market context updated for {symbol}")
    
    def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        return {
            'service': 'ConversationalAIService',
            'status': 'healthy',
            'models': self.models.health_check(),
            'state_backend': 'Redis',
            'intelligence_level': self.intelligence_level,
            'redis_available': cache.client is not None
        }


# Global service instance (singleton pattern)
# TODO: Replace with dependency injection for better testing
_ai_service_instance = None


def get_ai_service() -> ConversationalAIService:
    """Get singleton AI service instance"""
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = ConversationalAIService()
    return _ai_service_instance
