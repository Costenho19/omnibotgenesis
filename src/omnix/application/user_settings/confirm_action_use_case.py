"""
Confirm Action Use Case
========================

Use case for handling configuration action confirmations.
This implements the confirmation dialog pattern for high-risk actions
like enabling auto-trading or changing risk profiles.

Dec 18, 2025: Created as part of hexagonal architecture migration
"""

import logging
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta

from src.omnix.domain.user_settings.intents import ConfigurationIntent


logger = logging.getLogger(__name__)


@dataclass
class ConfirmationState:
    """State of a pending confirmation."""
    
    intent: ConfigurationIntent
    params: dict
    created_at: datetime
    expires_at: datetime
    attempts: int = 0
    
    @property
    def is_expired(self) -> bool:
        """Check if confirmation has expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def remaining_attempts(self) -> int:
        """Get remaining confirmation attempts."""
        return max(0, 3 - self.attempts)


@dataclass
class ConfirmationRequest:
    """Request to confirm an action."""
    
    user_id: str
    response: str
    
    @property
    def is_affirmative(self) -> bool:
        """Check if response is affirmative."""
        return self.response.lower().strip() in (
            'si', 'sí', 'yes', 'acepto', 'confirmo', 'ok', 'dale', 'va'
        )
    
    @property
    def is_negative(self) -> bool:
        """Check if response is negative."""
        return self.response.lower().strip() in (
            'no', 'cancelar', 'cancel', 'nope', 'nel', 'nah'
        )


@dataclass
class ConfirmationResult:
    """Result of confirmation processing."""
    
    confirmed: bool
    cancelled: bool = False
    expired: bool = False
    message: str = ""
    action_to_execute: Optional[str] = None
    action_params: Optional[dict] = None


class ConfirmActionUseCase:
    """
    Use case for confirming configuration actions.
    
    Flow:
    1. Action requiring confirmation is detected
    2. User is prompted for confirmation
    3. User responds (yes/no/other)
    4. Action is executed or cancelled
    
    Features:
    - Timeout after 5 minutes
    - Maximum 3 attempts
    - Clear confirmation messages in Spanish
    """
    
    CONFIRMATION_TIMEOUT_MINUTES = 5
    MAX_ATTEMPTS = 3
    
    def __init__(self):
        """Initialize the use case."""
        self._pending: dict[str, ConfirmationState] = {}
        logger.info("ConfirmActionUseCase initialized")
    
    def request_confirmation(
        self,
        user_id: str,
        intent: ConfigurationIntent,
        params: Optional[dict] = None
    ) -> str:
        """
        Request confirmation from user for an action.
        
        Args:
            user_id: User ID requesting the action
            intent: The configuration intent to confirm
            params: Parameters for the action
            
        Returns:
            Confirmation prompt message
        """
        now = datetime.utcnow()
        expires = now + timedelta(minutes=self.CONFIRMATION_TIMEOUT_MINUTES)
        
        self._pending[user_id] = ConfirmationState(
            intent=intent,
            params=params or {},
            created_at=now,
            expires_at=expires
        )
        
        logger.info(
            f"Confirmation requested | user={user_id} | "
            f"intent={intent.value} | expires={expires.isoformat()}"
        )
        
        return self._get_confirmation_prompt(intent, params)
    
    def process_confirmation(
        self,
        request: ConfirmationRequest
    ) -> ConfirmationResult:
        """
        Process a confirmation response from user.
        
        Args:
            request: The confirmation request
            
        Returns:
            Result of processing the confirmation
        """
        state = self._pending.get(request.user_id)
        
        if state is None:
            return ConfirmationResult(
                confirmed=False,
                message="No hay ninguna acción pendiente de confirmar."
            )
        
        if state.is_expired:
            del self._pending[request.user_id]
            return ConfirmationResult(
                confirmed=False,
                expired=True,
                message="⏰ La confirmación ha expirado. Por favor, vuelve a intentarlo."
            )
        
        state.attempts += 1
        
        if request.is_affirmative:
            del self._pending[request.user_id]
            
            action = self._get_action_handler(state.intent)
            
            logger.info(
                f"Confirmation ACCEPTED | user={request.user_id} | "
                f"intent={state.intent.value} | attempts={state.attempts}"
            )
            
            return ConfirmationResult(
                confirmed=True,
                message=f"✅ {state.intent.value.replace('_', ' ').title()} confirmado.",
                action_to_execute=action,
                action_params=state.params
            )
        
        if request.is_negative:
            del self._pending[request.user_id]
            
            logger.info(
                f"Confirmation CANCELLED | user={request.user_id} | "
                f"intent={state.intent.value}"
            )
            
            return ConfirmationResult(
                confirmed=False,
                cancelled=True,
                message="❌ Acción cancelada."
            )
        
        if state.remaining_attempts <= 0:
            del self._pending[request.user_id]
            return ConfirmationResult(
                confirmed=False,
                message="❌ Demasiados intentos. Acción cancelada."
            )
        
        return ConfirmationResult(
            confirmed=False,
            message=(
                f"No entendí tu respuesta. "
                f"Por favor, responde 'sí' para confirmar o 'no' para cancelar.\n"
                f"({state.remaining_attempts} intentos restantes)"
            )
        )
    
    def has_pending_confirmation(self, user_id: str) -> bool:
        """Check if user has a pending confirmation."""
        state = self._pending.get(user_id)
        if state is None:
            return False
        if state.is_expired:
            del self._pending[user_id]
            return False
        return True
    
    def get_pending_intent(self, user_id: str) -> Optional[ConfigurationIntent]:
        """Get the pending intent for a user."""
        state = self._pending.get(user_id)
        if state and not state.is_expired:
            return state.intent
        return None
    
    def cancel_pending(self, user_id: str) -> bool:
        """Cancel any pending confirmation for a user."""
        if user_id in self._pending:
            del self._pending[user_id]
            return True
        return False
    
    def _get_confirmation_prompt(
        self,
        intent: ConfigurationIntent,
        params: Optional[dict]
    ) -> str:
        """Get the confirmation prompt for an intent."""
        prompts = {
            ConfigurationIntent.UPDATE_RISK: (
                "⚠️ **Cambio de Perfil de Riesgo**\n\n"
                "Esta acción modificará tus límites de trading:\n"
                "• Tamaño máximo de posición\n"
                "• Exposición total permitida\n"
                "• Niveles de stop-loss\n\n"
                "¿Confirmas este cambio? (sí/no)"
            ),
            ConfigurationIntent.AUTO_TRADING: (
                "🤖 **Trading Automático**\n\n"
                "Vas a modificar el estado del trading automático.\n"
                "Esto permitirá que OMNIX ejecute operaciones en tu nombre.\n\n"
                "⚠️ *Riesgo: El trading automático puede generar pérdidas.*\n\n"
                "¿Confirmas? (sí/no)"
            ),
            ConfigurationIntent.SET_PROFILE: (
                "📊 **Cambio de Perfil**\n\n"
                f"Perfil solicitado: {params.get('profile', 'desconocido') if params else 'desconocido'}\n\n"
                "¿Confirmas el cambio de perfil? (sí/no)"
            ),
        }
        
        return prompts.get(
            intent,
            f"¿Confirmas la acción '{intent.value}'? (sí/no)"
        )
    
    def _get_action_handler(self, intent: ConfigurationIntent) -> str:
        """Map intent to action handler name."""
        handlers = {
            ConfigurationIntent.PAUSE: "pause_trading",
            ConfigurationIntent.RESUME: "resume_trading",
            ConfigurationIntent.UPDATE_RISK: "update_risk_settings",
            ConfigurationIntent.UPDATE_LIMIT: "update_trading_limits",
            ConfigurationIntent.AUTO_TRADING: "toggle_auto_trading",
            ConfigurationIntent.SET_PROFILE: "update_profile",
        }
        return handlers.get(intent, "unknown")
