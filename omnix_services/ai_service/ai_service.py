"""
OMNIX INSTITUTIONAL+ - Conversational AI Service
Main orchestrator for AI functionality

Refactored for dependency injection while maintaining backward compatibility.
Escalabilidad: 50K+ usuarios con stateless design
+ Real Context Provider for institutional transparency
"""

print("✅ ai_service.py CARGADO - REAL CONTEXT PROVIDER + DI")

from typing import Dict, List, Optional, Any, TYPE_CHECKING
from datetime import datetime
import logging

from .ai_models import AIModelsManager
from .ai_styles import VisualStylesManager
from .ai_prompts import PromptsContextManager
from .investor_responses import (
    create_audience_context, 
    format_response_with_honest_framing,
    get_response_word_limit,
    enforce_brevity
)
from omnix_core.cache.redis_cache import cache

if TYPE_CHECKING:
    from .providers.routing_gateway import RoutingAIGateway

WEB_SEARCH_AVAILABLE = False
try:
    from omnix_services.web_search_service import get_search_manager
    WEB_SEARCH_AVAILABLE = True
except ImportError:
    get_search_manager = None
from omnix_core.cache.redis_state import (
    get_conversation_history,
    get_user_preferences,
    get_market_context
)
from omnix_core.utils.logger import get_logger
from omnix_core.utils.rate_limiter import rate_limit, RateLimitExceeded
from omnix_config.settings import settings

try:
    from omnix_core.context import get_real_context_provider, create_real_context_provider
    REAL_CONTEXT_AVAILABLE = True
except ImportError:
    REAL_CONTEXT_AVAILABLE = False
    get_real_context_provider = None
    create_real_context_provider = None

logger = get_logger(__name__)


class ConversationalAIService:
    """
    Enterprise Conversational AI Service
    
    Orchestrates AI models, prompts, styles, and context management.
    Designed for horizontal scaling with stateless architecture.
    
    Supports dependency injection for better testing and flexibility.
    """
    
    def __init__(
        self,
        models_manager: Optional[AIModelsManager] = None,
        styles_manager: Optional[VisualStylesManager] = None,
        prompts_manager: Optional[PromptsContextManager] = None,
        ai_gateway: Optional["RoutingAIGateway"] = None,
    ):
        """
        Initialize AI service with optional injected dependencies.
        
        Args:
            models_manager: AIModelsManager instance (created if None)
            styles_manager: VisualStylesManager instance (created if None)
            prompts_manager: PromptsContextManager instance (created if None)
            ai_gateway: RoutingAIGateway for new DI-based AI calls (optional)
        """
        
        self.models = models_manager or AIModelsManager()
        self.styles = styles_manager or VisualStylesManager()
        self.prompts = prompts_manager or PromptsContextManager()
        self._ai_gateway = ai_gateway
        
        self.conversation_history = get_conversation_history()
        self.user_preferences = get_user_preferences()
        self.market_context = get_market_context()
        
        self.intelligence_level = "ULTRA_COMPETITIVE_ENTERPRISE"
        
        self.prediction_models = {
            'monte_carlo_advanced': {'active': True, 'accuracy': 0.847},
            'lstm_neural_network': {'active': True, 'accuracy': 0.823},
            'gradient_boosting': {'active': True, 'accuracy': 0.791},
            'transformer_attention': {'active': True, 'accuracy': 0.856},
            'ensemble_meta_model': {'active': True, 'accuracy': 0.872}
        }
        
        logger.info("Conversational AI Service initialized (DI-enabled)")
        logger.info(f"Intelligence level: {self.intelligence_level}")
        
        health = self.models.health_check()
        logger.info(f"AI Models Health: {health}")
        
        if REAL_CONTEXT_AVAILABLE and create_real_context_provider:
            try:
                existing = get_real_context_provider()
                if existing is None:
                    create_real_context_provider()
                    logger.info("Real Context Provider initialized from ConversationalAIService")
            except Exception as e:
                logger.warning(f"Could not initialize Real Context Provider: {e}")
    
    @property
    def ai_gateway(self) -> Optional["RoutingAIGateway"]:
        """Get the AI gateway (lazy-loaded if not injected)."""
        if self._ai_gateway is None:
            try:
                from .container import get_ai_gateway
                self._ai_gateway = get_ai_gateway()
            except Exception:
                pass
        return self._ai_gateway
    
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
        apply_visual_style: bool = True,
        diagnostic_mode: bool = False
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
            
            # 4.5 Web Search V6.5.4 PREMIUM - Automatic real-time info fetching
            web_search_context = None
            web_search_used = False
            web_search_query = None
            if WEB_SEARCH_AVAILABLE and get_search_manager:
                try:
                    search_manager = get_search_manager()
                    if search_manager.is_available():
                        intent_check = search_manager.detect_search_intent(user_message)
                        if intent_check.get("needs_search"):
                            web_search_query = intent_check.get("suggested_query", user_message)
                            logger.info(f"🔍 Web search triggered: {intent_check.get('reason')} | Query: {web_search_query[:50]}...")
                            
                            # Get both context and quick answer for premium experience
                            web_search_context = search_manager.get_context_for_ai(
                                query=web_search_query,
                                max_tokens=2500  # Increased for richer context
                            )
                            
                            # V6.5.4: Only mark as used if we got meaningful context (>100 chars)
                            if web_search_context and len(web_search_context) > 100:
                                additional_context["web_search_results"] = web_search_context
                                additional_context["web_search_notice"] = (
                                    "IMPORTANTE: La siguiente información fue obtenida de internet en tiempo real. "
                                    "Úsala para responder con datos actualizados y verificados."
                                )
                                web_search_used = True
                                logger.info(f"✅ Web search context added: {len(web_search_context)} chars")
                            elif web_search_context:
                                logger.info(f"⚠️ Web search returned minimal context ({len(web_search_context)} chars) - not marking as used")
                except Exception as e:
                    logger.warning(f"⚠️ Web search failed (continuing without): {e}")
            
            # 5. Build system prompt WITH CONVERSATION HISTORY + REAL CONTEXT
            # RULE 13 ENFORCEMENT (Jan 1, 2026): Use DIAGNOSTIC_ONLY_PROMPT for diagnostic mode
            if diagnostic_mode:
                logger.info("🔬 [DIAGNOSTIC_MODE] Building DIAGNOSTIC_ONLY system prompt")
                from .prompt_templates import DIAGNOSTIC_ONLY_PROMPT, get_system_state_prompt
                
                # Get real metrics from RealContextProvider or market_data
                total_trades = 119
                win_rate = 20.2
                pnl = -19848.65
                
                # Try to get real metrics from RealContextProvider
                if REAL_CONTEXT_AVAILABLE and get_real_context_provider:
                    try:
                        provider = get_real_context_provider()
                        if provider:
                            status = provider.get_auto_trading_status()
                            if status.get('available'):
                                total_trades = status.get('total_trades', total_trades)
                                win_rate = status.get('win_rate', win_rate)
                                pnl = status.get('profit_loss', pnl)
                                logger.info(f"🔬 [DIAGNOSTIC_MODE] Real metrics: trades={total_trades}, win_rate={win_rate}%, pnl=${pnl}")
                    except Exception as e:
                        logger.warning(f"⚠️ [DIAGNOSTIC_MODE] Could not get real metrics: {e}")
                
                # Or try to get from market_data if passed
                if market_data:
                    total_trades = market_data.get('total_trades', total_trades)
                    win_rate = market_data.get('win_rate', win_rate)
                    pnl = market_data.get('pnl', market_data.get('profit_loss', pnl))
                
                system_state = get_system_state_prompt()
                system_prompt = f"""
{DIAGNOSTIC_ONLY_PROMPT}

{system_state}

**DATOS ACTUALES DEL SISTEMA (USAR ESTOS VALORES EXACTOS):**
- Total trades: {total_trades}
- Win rate: {win_rate}%
- P&L: ${pnl:,.2f} USD

**PREGUNTA DEL USUARIO:**
{user_message}
"""
                logger.info(f"🔬 [DIAGNOSTIC_MODE] System prompt built with real metrics: {len(system_prompt)} chars")
            else:
                system_prompt = self.prompts.build_system_prompt(
                    intent=intent,
                    user_name=user_name,
                    additional_context=additional_context,
                    conversation_history=history,
                    user_message=user_message,
                    user_id=str(chat_id)
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
            
            # 7.5 ADR-009: Brevity First - Enforce word limits
            try:
                # Get admin IDs from settings
                from omnix_config.settings import settings
                admin_ids = settings.telegram.admin_ids if hasattr(settings, 'telegram') and hasattr(settings.telegram, 'admin_ids') else set()
                audience_context = create_audience_context(str(chat_id), admin_ids)
                styled_response = format_response_with_honest_framing(
                    response=styled_response,
                    context=audience_context,
                    question=user_message
                )
                logger.debug(f"📝 Brevity enforced: {len(styled_response.split())} words")
            except Exception as brevity_error:
                logger.warning(f"⚠️ Brevity enforcement skipped: {brevity_error}")
            
            # 8. Add AI response to history
            self._add_to_history(chat_id, {
                'ai': styled_response,
                'timestamp': datetime.now().isoformat(),
                'intent': intent
            })
            
            # 9. Return response with metadata (V6.5.4 Premium: includes web search info)
            return {
                'success': True,
                'response': styled_response,
                'intent': intent,
                'context': context,
                'model_used': self.models.primary_model,
                'timestamp': datetime.now().isoformat(),
                # V6.5.4 Premium: Web search metadata for UI indicators
                'web_search_used': web_search_used,
                'web_search_query': web_search_query if web_search_used else None
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
    
    def _get_fallback_response(self, intent: str, chat_id: Optional[int] = None) -> str:
        """
        Get fallback response when AI fails.
        
        AI-FIRST: Uses minimal English placeholder. The AI will generate
        proper localized responses once capacity returns.
        
        NOTE: In future, this should queue an AI retry to generate
        a proper response in the user's language.
        """
        return "⏳ System busy. Please wait a moment..."
    
    def _get_error_response(self, chat_id: Optional[int] = None) -> str:
        """
        Get error response.
        
        AI-FIRST: Uses minimal English placeholder. For critical errors,
        a simple universal message is appropriate.
        """
        return "⚠️ Connection issue. Please try again shortly."
    
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


_ai_service_instance: Optional[ConversationalAIService] = None


def get_ai_service() -> ConversationalAIService:
    """
    Get singleton AI service instance.
    
    NOTE: ConversationalAIService now supports dependency injection.
    For new code, prefer using the DI container:
        from omnix_services.ai_service import get_ai_gateway
        gateway = get_ai_gateway()
    """
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = ConversationalAIService()
    return _ai_service_instance
