"""
OMNIX V6.5.4d - Master Prompt Templates
AI-First Multilingual System with Modern Prompt Engineering

Architecture:
- Role + Mission + Language Policy + Safety + Output Format structure
- Language-neutral base prompts (English)
- Dynamic language detection and adaptation
- Chain-of-Thought triggers for analytical queries
- Self-verification patterns
- Thread-safe language detection with asyncio.Lock
- Redis persistence for detected language per chat_id

Created: Dec 19, 2025
Updated: Dec 19, 2025 - Added concurrency-safe language detection
"""

from typing import Optional, Dict, Any
import logging
import asyncio
import threading
from datetime import datetime

logger = logging.getLogger(__name__)

_language_detection_lock = threading.Lock()
_gemini_lang_client = None

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

## INSTITUTIONAL LANGUAGE POLICY [MANDATORY - INVESTOR PRESENTATION]
When discussing trading performance, losses, risk, or system status, you MUST speak as a 
"FOUNDER CONTROLLING RISK" - never as an "architect explaining problems".

**BLACKLISTED PHRASES - NEVER USE THESE (EN/ES):**
- "rendimiento subóptimo", "suboptimal performance", "poor performance"
- "señal de alerta", "warning sign", "red flag", "alarma"
- "riesgo de pérdidas reales", "risk of real losses", "real loss risk"
- "atención inmediata", "immediate attention", "urgent", "urgente"
- "recalibración urgente", "urgent recalibration", "needs fixing"
- "disclaimer de riesgo", "risk disclaimer", "descargo de responsabilidad"
- "no garantiza", "no guarantee", "sin garantía"
- "podrías perder todo", "you could lose everything", "perder todo"
- "falta de liquidez", "lack of liquidity", "sin liquidez"
- "ajuste manual", "manual adjustment", "requiere ajuste"
- "problema", "problem", "issue" (when discussing system)
- "error crítico", "critical error", "fallo", "failure"
- "pérdidas sustanciales", "substantial losses", "heavy losses"
- "desempeño negativo", "negative performance", "mal desempeño"
- "pérdida", "loss", "perdida" (as isolated term - use "capital deployment" instead)
- "drawdown", "drawdown crítico", "critical drawdown"
- "está fallando", "is failing", "no funciona", "not working"
- "bajo win rate", "low win rate", "poor win rate"
- "requiere atención", "needs attention", "requires attention"
- "riesgo alto", "high risk", "alto riesgo" (when discussing our system)
- "error del sistema", "system error", "fallo del sistema"

**APPROVED INSTITUTIONAL REFRAMES:**
- Instead of "losses" → "capital deployment in learning phase"
- Instead of "low win rate" → "strategy calibration in progress"
- Instead of "negative P&L" → "paper trading validation phase"
- Instead of "problem assets" → "assets under strategic review"
- Instead of "blocked trades" → "risk-managed positions"
- Instead of "system error" → "protective measure activated"
- Instead of "underperforming" → "building statistical baseline"

**FOUNDER NARRATIVE EXAMPLES:**
- "We identified this pattern early and implemented protective measures"
- "The system is designed to prioritize capital preservation during calibration"
- "Paper trading phase allows us to refine parameters without capital risk"
- "Our risk management protocols are actively protecting the portfolio"
- "We're building a verified track record with institutional discipline"

**WHEN USER ASKS ABOUT PERFORMANCE:**
1. Acknowledge the current phase (paper trading / calibration)
2. Emphasize what PROTECTIONS are active (quarantine, veto, Monte Carlo)
3. Frame any challenges as "expected during system optimization"
4. Never suggest the system is broken or needs urgent fixes
5. Always project confidence and control

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
    
    CONCURRENCY-SAFE: Uses locks to prevent language bleed between
    simultaneous requests from different users.
    
    REDIS PERSISTENCE: Stores detected language per chat_id for
    fallback scenarios and conversation continuity.
    """
    
    REDIS_LANGUAGE_PREFIX = "omnix:user_language:"
    REDIS_LANGUAGE_TTL = 86400  # 24 hours
    
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
            'hi': 'Hindi',
            'no': 'Norwegian',
            'sv': 'Swedish',
            'da': 'Danish',
            'nl': 'Dutch',
            'pl': 'Polish',
            'tr': 'Turkish'
        }
        self._redis_client = None
        
    def _get_redis(self):
        """Lazy load Redis client."""
        if self._redis_client is None:
            try:
                from omnix_services.redis_service.cache import cache
                self._redis_client = cache.client
            except Exception as e:
                logger.warning(f"Redis not available for language persistence: {e}")
        return self._redis_client
        
    def detect_language(self, text: str) -> str:
        """
        AI-FIRST language detection (THREAD-SAFE).
        
        Architecture (Dec 22, 2025):
        1. For long texts (50+ chars): Use fast-langdetect (FastText, very accurate)
        2. For short texts (<50 chars): Use Gemini AI for detection (true AI-first)
        3. Fallback: langdetect -> 'en'
        
        Returns ISO 639-1 language code.
        """
        if not text or len(text.strip()) < 2:
            return 'en'
        
        clean_text = text.strip()
        
        with _language_detection_lock:
            if len(clean_text) >= 50:
                detected = self._detect_with_fastlangdetect(clean_text)
                if detected and detected in self.supported_languages:
                    logger.info(f"🌍 Language detected (fast-langdetect): {detected} for '{text[:30]}'")
                    return detected
            
            detected = self._detect_with_gemini(clean_text)
            if detected and detected in self.supported_languages:
                logger.info(f"🌍 Language detected (Gemini AI): {detected} for '{text[:30]}'")
                return detected
            
            detected = self._detect_with_fastlangdetect(clean_text)
            if detected and detected in self.supported_languages:
                logger.info(f"🌍 Language detected (fast-langdetect fallback): {detected} for '{text[:30]}'")
                return detected
            
            detected = self._detect_with_langdetect(clean_text)
            if detected and detected in self.supported_languages:
                logger.info(f"🌍 Language detected (langdetect fallback): {detected} for '{text[:30]}'")
                return detected
            
            logger.debug(f"🌍 Could not detect language, defaulting to English")
            return 'en'
    
    def _detect_with_gemini(self, text: str) -> Optional[str]:
        """
        AI-FIRST: Use Gemini to detect language for short texts.
        This is the most accurate method for short inputs like "hello" or "hola".
        
        Uses a singleton client to reduce latency on repeated calls.
        
        Returns ISO 639-1 code or None on failure.
        """
        global _gemini_lang_client
        
        try:
            import os
            api_key = os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.debug("Gemini API key not available for language detection")
                return None
            
            try:
                from google import genai
                from google.genai import types
            except ImportError:
                logger.debug("google-genai not installed")
                return None
            
            if _gemini_lang_client is None:
                _gemini_lang_client = genai.Client(api_key=api_key)
            
            prompt = f"""Detect the language of this text and return ONLY the ISO 639-1 two-letter code.
            
Text: "{text}"

Return ONLY the code (en, es, fr, de, pt, it, nl, ar, zh, ja, ko, ru, hi, no, sv, da, pl, tr).
No explanation, just the code."""
            
            response = _gemini_lang_client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=5,
                    temperature=0.0,
                ),
            )
            
            if response and response.text:
                lang_code = response.text.strip().lower()[:2]
                if len(lang_code) == 2 and lang_code.isalpha():
                    return lang_code
            
            return None
            
        except Exception as e:
            logger.debug(f"Gemini language detection failed: {e}")
            return None
    
    def _detect_with_fastlangdetect(self, text: str) -> Optional[str]:
        """
        Use fast-langdetect (FastText-based) for language detection.
        FastText works best with 50+ character texts.
        
        Returns ISO 639-1 code or None on failure.
        """
        try:
            from fast_langdetect import detect
            result = detect(text, low_memory=True)
            if isinstance(result, dict):
                return result.get('lang', None)
            elif isinstance(result, str):
                return result
            return None
        except ImportError:
            logger.debug("fast-langdetect not installed")
            return None
        except Exception as e:
            logger.debug(f"fast-langdetect failed: {e}")
            return None
    
    def _detect_with_langdetect(self, text: str) -> Optional[str]:
        """
        Legacy fallback using langdetect library.
        Less accurate for short texts but works as backup.
        """
        try:
            from langdetect import detect as ld_detect, LangDetectException
            return ld_detect(text)
        except LangDetectException:
            return None
        except ImportError:
            return None
        except Exception:
            return None
    
    async def detect_language_async(self, text: str) -> str:
        """
        Async version of language detection (FULLY CONCURRENCY-SAFE).
        
        Uses asyncio.to_thread() to run detection in thread pool with the 
        global threading.Lock, ensuring process-wide serialization of 
        langdetect calls even across different event loops.
        """
        try:
            return await asyncio.to_thread(self.detect_language, text)
        except Exception as e:
            logger.warning(f"Async language detection error: {e}")
            return 'en'
    
    def persist_user_language(self, chat_id: int, lang_code: str) -> bool:
        """
        Store detected language in Redis for a chat/user.
        Allows fallback messages to use correct language even when AI fails.
        """
        redis = self._get_redis()
        if redis is None:
            return False
        
        try:
            key = f"{self.REDIS_LANGUAGE_PREFIX}{chat_id}"
            data = {
                'lang': lang_code,
                'updated': datetime.utcnow().isoformat()
            }
            import json
            redis.setex(key, self.REDIS_LANGUAGE_TTL, json.dumps(data))
            logger.debug(f"🌍 Persisted language {lang_code} for chat {chat_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to persist language: {e}")
            return False
    
    def get_user_language(self, chat_id: int) -> str:
        """
        Retrieve stored language for a chat/user from Redis.
        Returns 'en' as default if not found.
        """
        redis = self._get_redis()
        if redis is None:
            return 'en'
        
        try:
            key = f"{self.REDIS_LANGUAGE_PREFIX}{chat_id}"
            data = redis.get(key)
            if data:
                import json
                parsed = json.loads(data)
                return parsed.get('lang', 'en')
        except Exception as e:
            logger.warning(f"Failed to get stored language: {e}")
        
        return 'en'
    
    def detect_and_persist(self, text: str, chat_id: int) -> str:
        """
        Detect language and persist it to Redis in one call.
        This is the recommended method for production use.
        """
        lang = self.detect_language(text)
        self.persist_user_language(chat_id, lang)
        return lang
    
    async def detect_and_persist_async(self, text: str, chat_id: int) -> str:
        """
        Async version: Detect language and persist it to Redis.
        """
        lang = await self.detect_language_async(text)
        self.persist_user_language(chat_id, lang)
        return lang
    
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
