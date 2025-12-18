"""
Intent Classification Adapter
==============================

Implementation of IntentClassificationPort that provides AI-first
command detection for the OMNIX trading bot.

This adapter wraps the legacy NLP command detection with proper
slash-prefix gating to prevent false positives.

Strangler Fig Pattern:
- USE_LEGACY_CONFIG_NLP=true: Uses legacy UserSettingsService.process_natural_language_command()
- USE_LEGACY_CONFIG_NLP=false: Uses new Intent Value Objects only

Dec 18, 2025: Created as part of hexagonal architecture migration
"""

import os
import logging
from typing import Optional

from src.omnix.ports.driver.intent_classification_port import (
    IntentClassificationPort,
    IntentClassificationPortABC,
    ClassificationRequest,
    ClassificationResponse,
)
from src.omnix.domain.user_settings.intents import (
    Intent,
    IntentType,
    ConfigurationIntent,
    COMMAND_INTENTS,
)


logger = logging.getLogger(__name__)


USE_LEGACY_CONFIG_NLP = os.getenv("USE_LEGACY_CONFIG_NLP", "true").lower() == "true"


COMMAND_HELP: dict[str, str] = {
    "/pause": "Pausa el trading automático temporalmente.\nEjemplo: /pause",
    "/pausar": "Sinónimo de /pause en español.",
    "/resume": "Reanuda el trading automático.\nEjemplo: /resume",
    "/reanudar": "Sinónimo de /resume en español.",
    "/perfil": "Cambia tu perfil de riesgo.\nEjemplo: /perfil conservative",
    "/limite": "Establece límites de trading.\nEjemplo: /limite 500",
    "/autotrading": "Activa/desactiva trading automático.\nEjemplo: /autotrading activar ACEPTO",
    "/riesgo": "Ajusta parámetros de riesgo.\nEjemplo: /riesgo bajo",
}


class IntentClassificationAdapter(IntentClassificationPortABC):
    """
    Adapter that implements IntentClassificationPort.
    
    AI-First Design:
    1. Messages NOT starting with "/" → route to AI immediately
    2. Messages starting with "/" → classify as command and handle
    
    This prevents the "resumen" → "resume" false positive bug.
    """
    
    def __init__(self, legacy_nlp_service=None):
        """
        Initialize the adapter.
        
        Args:
            legacy_nlp_service: Optional legacy UserSettingsService for NLP
        """
        self._legacy_nlp_service = legacy_nlp_service
        self._use_legacy = USE_LEGACY_CONFIG_NLP and legacy_nlp_service is not None
        
        logger.info(
            f"IntentClassificationAdapter initialized | "
            f"USE_LEGACY_CONFIG_NLP={self._use_legacy}"
        )
    
    def classify(self, request: ClassificationRequest) -> ClassificationResponse:
        """
        Classify a user message to determine routing.
        
        AI-First Rule: Only messages starting with "/" are considered commands.
        All other messages immediately go to AI.
        """
        message = request.message.strip()
        
        if not message.startswith('/'):
            logger.debug(f"AI-First: Routing to AI (no slash prefix): {message[:50]}")
            return ClassificationResponse(
                intent=Intent(
                    type=IntentType.CONVERSATION,
                    raw_message=request.message,
                    confidence=1.0
                ),
                should_route_to_ai=True
            )
        
        intent = Intent.from_message(request.message)
        
        if intent.type == IntentType.CONFIGURATION and intent.config_intent:
            logger.info(
                f"COMANDO EXPLÍCITO: {intent.config_intent.value} | "
                f"user={request.user_id}"
            )
            
            action_handler = self._get_action_handler(intent.config_intent)
            action_params = self._extract_params(request.message, intent.config_intent)
            
            return ClassificationResponse(
                intent=intent,
                should_route_to_ai=False,
                action_handler=action_handler,
                action_params=action_params
            )
        
        if intent.type == IntentType.QUERY:
            logger.debug(f"Command query, routing to AI: {message[:50]}")
            return ClassificationResponse(
                intent=intent,
                should_route_to_ai=True
            )
        
        logger.debug(f"Unknown command format, routing to AI: {message[:50]}")
        return ClassificationResponse(
            intent=intent,
            should_route_to_ai=True
        )
    
    def get_command_help(self, command: str) -> Optional[str]:
        """Get help text for a specific command."""
        cmd = command.lower().strip()
        if not cmd.startswith('/'):
            cmd = '/' + cmd
        
        return COMMAND_HELP.get(cmd)
    
    def list_available_commands(self) -> list[str]:
        """List all available configuration commands."""
        return list(COMMAND_HELP.keys())
    
    def _get_action_handler(self, config_intent: ConfigurationIntent) -> str:
        """Map configuration intent to action handler name."""
        handlers = {
            ConfigurationIntent.PAUSE: "pause_trading",
            ConfigurationIntent.RESUME: "resume_trading",
            ConfigurationIntent.SET_PROFILE: "update_profile",
            ConfigurationIntent.UPDATE_LIMIT: "update_trading_limits",
            ConfigurationIntent.AUTO_TRADING: "toggle_auto_trading",
            ConfigurationIntent.UPDATE_RISK: "update_risk_settings",
        }
        return handlers.get(config_intent, "unknown")
    
    def _extract_params(
        self, 
        message: str, 
        config_intent: ConfigurationIntent
    ) -> dict:
        """Extract parameters from command message."""
        parts = message.strip().split(maxsplit=2)
        
        if len(parts) < 2:
            return {}
        
        if config_intent == ConfigurationIntent.SET_PROFILE:
            profile = parts[1].lower() if len(parts) > 1 else None
            accept = len(parts) > 2 and "acepto" in parts[2].lower()
            return {"profile": profile, "accepted": accept}
        
        if config_intent == ConfigurationIntent.UPDATE_LIMIT:
            try:
                value = float(parts[1].replace(',', '.'))
                return {"value": value, "type": "max_trade"}
            except (ValueError, IndexError):
                return {}
        
        if config_intent == ConfigurationIntent.AUTO_TRADING:
            action = parts[1].lower() if len(parts) > 1 else None
            accept = len(parts) > 2 and "acepto" in parts[2].lower()
            return {"enable": action == "activar", "accepted": accept}
        
        if config_intent == ConfigurationIntent.PAUSE:
            try:
                duration = int(parts[1]) if len(parts) > 1 else 60
                return {"duration_minutes": duration}
            except (ValueError, IndexError):
                return {"duration_minutes": 60}
        
        return {}


class NLPCommandShim:
    """
    Shim that bridges legacy NLP command detection with new port interface.
    
    This is used when USE_LEGACY_CONFIG_NLP=true to maintain compatibility
    while gradually migrating to the new Intent-based system.
    
    The shim follows Strangler Fig pattern - it wraps the legacy service
    without modifying its behavior.
    """
    
    def __init__(self, legacy_nlp_service):
        """
        Initialize the shim with legacy NLP service.
        
        Args:
            legacy_nlp_service: UserSettingsService instance
        """
        self._legacy = legacy_nlp_service
        logger.info("NLPCommandShim initialized with legacy UserSettingsService")
    
    def classify(self, request: ClassificationRequest) -> ClassificationResponse:
        """
        Classify using legacy NLP but with slash-prefix gate.
        
        Even in legacy mode, we enforce the slash-prefix requirement
        to prevent false positives.
        """
        message = request.message.strip()
        
        if not message.startswith('/'):
            return ClassificationResponse(
                intent=Intent(
                    type=IntentType.CONVERSATION,
                    raw_message=request.message,
                    confidence=1.0
                ),
                should_route_to_ai=True
            )
        
        if self._legacy is None:
            return IntentClassificationAdapter().classify(request)
        
        nlp_result = self._legacy.process_natural_language_command(
            request.user_id,
            request.message
        )
        
        if nlp_result:
            action, params = nlp_result
            logger.info(f"Legacy NLP detected: {action} with params: {params}")
            
            config_intent = self._map_legacy_action(action)
            
            return ClassificationResponse(
                intent=Intent(
                    type=IntentType.CONFIGURATION,
                    config_intent=config_intent,
                    raw_message=request.message,
                    confidence=1.0
                ),
                should_route_to_ai=False,
                action_handler=action,
                action_params=params
            )
        
        return ClassificationResponse(
            intent=Intent(
                type=IntentType.QUERY,
                raw_message=request.message,
                confidence=0.5
            ),
            should_route_to_ai=True
        )
    
    def _map_legacy_action(self, action: str) -> Optional[ConfigurationIntent]:
        """Map legacy action string to ConfigurationIntent."""
        mapping = {
            "pause": ConfigurationIntent.PAUSE,
            "resume": ConfigurationIntent.RESUME,
            "update_risk": ConfigurationIntent.UPDATE_RISK,
            "update_limit": ConfigurationIntent.UPDATE_LIMIT,
            "auto_trading": ConfigurationIntent.AUTO_TRADING,
            "set_profile": ConfigurationIntent.SET_PROFILE,
        }
        return mapping.get(action)
