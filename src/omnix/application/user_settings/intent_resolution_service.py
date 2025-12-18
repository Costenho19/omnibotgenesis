"""
Intent Resolution Service
==========================

Application service that orchestrates the AI-first message routing flow.
This service coordinates between intent classification, AI gateway, and
configuration handlers.

Architecture:
    TelegramPort → IntentResolutionService → (AI Gateway | Config Handler)

Dec 18, 2025: Created as part of hexagonal architecture migration
"""

import logging
from dataclasses import dataclass
from typing import Optional, Callable, Awaitable

from src.omnix.ports.driver.intent_classification_port import (
    IntentClassificationPort,
    ClassificationRequest,
    ClassificationResponse,
)
from src.omnix.domain.user_settings.intents import (
    Intent,
    IntentType,
    ConfigurationIntent,
)


logger = logging.getLogger(__name__)


@dataclass
class ResolutionContext:
    """Context for intent resolution."""
    
    user_id: str
    chat_id: str
    message: str
    pending_confirmation: Optional[ConfigurationIntent] = None


@dataclass
class ResolutionResult:
    """Result of intent resolution."""
    
    handled: bool
    response_text: Optional[str] = None
    needs_confirmation: bool = False
    pending_intent: Optional[ConfigurationIntent] = None
    routed_to_ai: bool = False
    error: Optional[str] = None


class IntentResolutionService:
    """
    Service that resolves user intents and routes messages appropriately.
    
    AI-First Flow:
    1. Receive message from TelegramPort
    2. Classify intent (only /commands trigger config actions)
    3. If config command → execute or request confirmation
    4. If conversation → route to AI Gateway
    
    This service does NOT call AI directly - it returns routing decisions
    that the caller (TelegramPort) acts upon.
    """
    
    def __init__(
        self,
        intent_classifier: IntentClassificationPort,
        pending_confirmations: Optional[dict] = None
    ):
        """
        Initialize the service.
        
        Args:
            intent_classifier: Port for classifying user intents
            pending_confirmations: Dict to track pending confirmations by user_id
        """
        self._classifier = intent_classifier
        self._pending = pending_confirmations or {}
        
        logger.info("IntentResolutionService initialized")
    
    async def resolve(self, context: ResolutionContext) -> ResolutionResult:
        """
        Resolve user intent and determine routing.
        
        Args:
            context: Resolution context with user info and message
            
        Returns:
            ResolutionResult with routing decision
        """
        try:
            if context.pending_confirmation:
                return await self._handle_confirmation_response(context)
            
            request = ClassificationRequest(
                user_id=context.user_id,
                message=context.message,
                chat_id=context.chat_id
            )
            
            classification = self._classifier.classify(request)
            
            if classification.should_route_to_ai:
                logger.debug(f"Routing to AI: {context.message[:50]}")
                return ResolutionResult(
                    handled=False,
                    routed_to_ai=True
                )
            
            return await self._handle_configuration_command(
                context, 
                classification
            )
            
        except Exception as e:
            logger.error(f"Intent resolution error: {e}")
            return ResolutionResult(
                handled=False,
                error=str(e),
                routed_to_ai=True
            )
    
    async def _handle_configuration_command(
        self,
        context: ResolutionContext,
        classification: ClassificationResponse
    ) -> ResolutionResult:
        """Handle a classified configuration command."""
        intent = classification.intent
        
        if intent.requires_confirmation and intent.config_intent is not None:
            self._pending[context.user_id] = intent.config_intent
            
            return ResolutionResult(
                handled=True,
                needs_confirmation=True,
                pending_intent=intent.config_intent,
                response_text=self._get_confirmation_message(intent.config_intent)
            )
        
        return ResolutionResult(
            handled=True,
            response_text=None
        )
    
    async def _handle_confirmation_response(
        self,
        context: ResolutionContext
    ) -> ResolutionResult:
        """Handle a response to a pending confirmation."""
        pending = context.pending_confirmation
        message_lower = context.message.lower().strip()
        
        if message_lower in ('si', 'sí', 'yes', 'acepto', 'confirmo'):
            if context.user_id in self._pending:
                del self._pending[context.user_id]
            action_name = pending.value if pending else "desconocida"
            return ResolutionResult(
                handled=True,
                response_text=f"✅ Acción {action_name} confirmada y ejecutada."
            )
        
        elif message_lower in ('no', 'cancelar', 'cancel'):
            if context.user_id in self._pending:
                del self._pending[context.user_id]
            return ResolutionResult(
                handled=True,
                response_text="❌ Acción cancelada."
            )
        
        return ResolutionResult(
            handled=False,
            routed_to_ai=True
        )
    
    def _get_confirmation_message(self, intent: ConfigurationIntent) -> str:
        """Get confirmation message for a given intent."""
        messages = {
            ConfigurationIntent.UPDATE_RISK: (
                "⚠️ Vas a modificar tu perfil de riesgo.\n"
                "Esto afectará los límites de trading.\n\n"
                "¿Confirmas? (sí/no)"
            ),
            ConfigurationIntent.AUTO_TRADING: (
                "🤖 Vas a modificar el trading automático.\n"
                "Esta acción puede afectar tus operaciones.\n\n"
                "¿Confirmas? (sí/no)"
            ),
        }
        
        return messages.get(
            intent,
            f"¿Confirmas la acción '{intent.value}'? (sí/no)"
        )
    
    def get_pending_confirmation(self, user_id: str) -> Optional[ConfigurationIntent]:
        """Get pending confirmation for a user, if any."""
        return self._pending.get(user_id)
    
    def clear_pending_confirmation(self, user_id: str) -> None:
        """Clear any pending confirmation for a user."""
        self._pending.pop(user_id, None)
