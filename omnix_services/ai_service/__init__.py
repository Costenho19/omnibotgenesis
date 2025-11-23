"""
OMNIX V5.1 ENTERPRISE - AI Service Package
Conversational AI with Multi-Model Strategy
"""

from .ai_service import ConversationalAIService, get_ai_service
from .ai_models import AIModelsManager
from .ai_styles import VisualStylesManager
from .ai_prompts import PromptsContextManager
from .conversational_brain import ConversationalBrain, get_conversational_brain
from .conversational_ai_adapter import ConversationalAI

__all__ = [
    'ConversationalAIService',
    'get_ai_service',
    'AIModelsManager',
    'VisualStylesManager',
    'PromptsContextManager',
    'ConversationalBrain',
    'get_conversational_brain',
    'ConversationalAI'
]

__version__ = '5.1.0'
