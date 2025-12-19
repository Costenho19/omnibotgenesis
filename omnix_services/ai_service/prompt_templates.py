"""
OMNIX V6.5.4d - Master Prompt Templates
AI-First Multilingual System with Modern Prompt Engineering

Architecture:
- Role + Mission + Language Policy + Safety + Output Format structure
- Language-neutral base prompts (English)
- Dynamic language detection and adaptation
- Chain-of-Thought triggers for analytical queries
- Self-verification patterns

Created: Dec 19, 2025
"""

from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

MASTER_SYSTEM_PROMPT = """You are OMNIX V6.5.4d INSTITUTIONAL+, an advanced automated trading assistant created by Harold Nunes.

## ROLE
Expert AI trading advisor specializing in cryptocurrency and stock markets with institutional-grade analysis.

## MISSION
Provide intelligent, data-driven market analysis and trading insights while maintaining a professional yet accessible tone.

## CORE CAPABILITIES
- Post-Quantum Cryptography (Kyber-768, Dilithium-3) for institutional security
- Monte Carlo Simulator (10K simulations), Black Swan Detector, Kelly Criterion
- HMM Regime Detector, Dual Kalman Filter, OMNIX Quantum Momentum
- Adaptive Weight System ω(t): Dynamic Kalman/Monte Carlo weights based on Hurst Exponent H(t) and α-stable tail index
- Real Trading with Kraken API (actual trades, NOT simulated)
- Sharia Compliance, Bidirectional Voice, Multi-language
- Real-time WebSocket, Professional Backtesting, Smart Alerts 24/7

## LANGUAGE POLICY [CRITICAL]
**ALWAYS respond in the SAME language the user writes their message.**
- If user writes in English → respond in English
- If user writes in Spanish → respond in Spanish  
- If user writes in Arabic → respond in Arabic
- If user writes in any other language → respond in that language
This is mandatory for all responses without exception.

## PERSONALITY
- Intelligent and independent, mention capabilities based on context
- Natural but deep responses to impress investors
- Professional institutional tone with accessible explanations

## OUTPUT FORMAT
- Use clear headers and sections for complex analyses
- Include relevant data points and metrics
- Provide actionable insights when applicable
"""

ENHANCED_ANALYSIS_PROMPT = """
## ANALYTICAL FRAMEWORK [Chain-of-Thought]
For complex analysis, follow this structured approach:

**Step 1: Immediate Analysis**
- Current price action and key levels
- Volume analysis and market sentiment

**Step 2: Technical Data**
- Key indicators and their signals
- Support/resistance levels

**Step 3: Implications**
- What does this data suggest?
- Risk factors to consider

**Step 4: Recommendations**
- Actionable insights
- Position sizing considerations

**Step 5: Historical Perspective**
- Similar past patterns
- Lessons from history
"""

TRADING_CONTEXT_TEMPLATE = """
## CURRENT TRADING CONTEXT
{trading_context}

## USER QUERY
User {user_name}: {user_message}
"""

KRAKEN_CONTEXT_ACTIVE = """
## KRAKEN STATUS: Connected and Ready
- API: Active
- Trading: Enabled
{balance_info}
NOTE: Only mention balance if user specifically asks for it.
"""

KRAKEN_CONTEXT_INACTIVE = """
## KRAKEN STATUS: Connection pending
- API: Checking credentials
"""


class LanguageContextManager:
    """
    Manages dynamic language detection and prompt adaptation.
    Detects user language and generates appropriate directives.
    """
    
    def __init__(self):
        self.supported_languages = {
            'en': 'English',
            'es': 'Spanish', 
            'ar': 'Arabic',
            'zh': 'Chinese',
            'fr': 'French',
            'de': 'German',
            'pt': 'Portuguese',
            'it': 'Italian',
            'ja': 'Japanese',
            'ko': 'Korean',
            'ru': 'Russian',
            'hi': 'Hindi'
        }
        
    def detect_language(self, text: str) -> str:
        """
        Detect the language of user input.
        Returns ISO 639-1 language code.
        """
        try:
            from langdetect import detect, LangDetectException
        except ImportError:
            logger.warning("langdetect not installed, defaulting to English")
            return 'en'
        
        try:
            detected = detect(text)
            if detected in self.supported_languages:
                return detected
            return detected
        except LangDetectException:
            return 'en'
        except Exception as e:
            logger.warning(f"Language detection error: {e}")
            return 'en'
    
    def get_language_directive(self, detected_lang: str) -> str:
        """
        Generate a language directive for the prompt.
        Reinforces the language policy with specific guidance.
        """
        lang_name = self.supported_languages.get(detected_lang, detected_lang.upper())
        return f"""
## LANGUAGE DIRECTIVE
The user is writing in **{lang_name}**.
You MUST respond entirely in {lang_name}. Do not switch languages mid-response.
Maintain professional tone appropriate for {lang_name}-speaking institutional investors.
"""

    def build_complete_prompt(
        self,
        user_message: str,
        user_name: str = "User",
        context: str = "",
        kraken_info: str = "",
        include_analysis_framework: bool = False
    ) -> str:
        """
        Build a complete prompt with all components.
        
        Args:
            user_message: The user's input message
            user_name: User's display name
            context: Previous conversation context
            kraken_info: Trading platform status info
            include_analysis_framework: Whether to include CoT for analysis
            
        Returns:
            Complete assembled prompt string
        """
        detected_lang = self.detect_language(user_message)
        
        prompt_parts = [
            MASTER_SYSTEM_PROMPT,
            self.get_language_directive(detected_lang)
        ]
        
        if kraken_info:
            prompt_parts.append(kraken_info)
        
        if include_analysis_framework:
            prompt_parts.append(ENHANCED_ANALYSIS_PROMPT)
        
        trading_context = TRADING_CONTEXT_TEMPLATE.format(
            trading_context=context if context else "No previous context",
            user_name=user_name,
            user_message=user_message
        )
        prompt_parts.append(trading_context)
        
        return "\n".join(prompt_parts)


class PromptBuilder:
    """
    High-level interface for building prompts.
    Integrates with the existing AI service architecture.
    """
    
    def __init__(self):
        self.language_manager = LanguageContextManager()
        
    def build_system_prompt(
        self,
        user_message: str,
        user_name: str = "User",
        context: str = "",
        kraken_status: Optional[Dict[str, Any]] = None,
        intent: str = "general"
    ) -> str:
        """
        Build a complete system prompt for AI generation.
        
        Args:
            user_message: User's input text
            user_name: Display name
            context: Conversation history
            kraken_status: Trading platform status dict
            intent: Detected user intent
            
        Returns:
            Complete prompt string
        """
        kraken_info = self._format_kraken_info(kraken_status)
        
        include_analysis = intent in [
            'market_analysis', 'price_query', 'technical_analysis',
            'portfolio_query', 'trading_advice'
        ]
        
        return self.language_manager.build_complete_prompt(
            user_message=user_message,
            user_name=user_name,
            context=context,
            kraken_info=kraken_info,
            include_analysis_framework=include_analysis
        )
    
    def _format_kraken_info(self, kraken_status: Optional[Dict[str, Any]]) -> str:
        """Format Kraken status for prompt inclusion."""
        if not kraken_status:
            return KRAKEN_CONTEXT_INACTIVE
        
        if kraken_status.get('connected') and kraken_status.get('trading_enabled'):
            balance_info = ""
            if kraken_status.get('balance'):
                balance = kraken_status['balance']
                balance_info = f"- USD: ${balance.get('USD', 0):,.2f}\n"
                if balance.get('BTC'):
                    balance_info += f"- BTC: {balance['BTC']:.8f}\n"
            return KRAKEN_CONTEXT_ACTIVE.format(balance_info=balance_info)
        
        return KRAKEN_CONTEXT_INACTIVE
    
    def get_detected_language(self, text: str) -> str:
        """Get the detected language code for a text."""
        return self.language_manager.detect_language(text)


prompt_builder = PromptBuilder()
