"""
OMNIX V6.0 ENTERPRISE - AI Models Manager
Gestión de múltiples modelos IA: GPT-4o, Gemini 2.0, Claude
Escalabilidad: 50K+ usuarios con Async verdadero
Features: Retry with exponential backoff, response validation
"""

import logging
import os
import asyncio
import re
from typing import Optional, Dict, Any, Tuple
from openai import AsyncOpenAI
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
    GEMINI_SDK_VERSION = 'new'
except ImportError:
    try:
        import google.generativeai as genai
        from google.generativeai import types
        GEMINI_AVAILABLE = True
        GEMINI_SDK_VERSION = 'legacy'
    except ImportError:
        GEMINI_AVAILABLE = False
        GEMINI_SDK_VERSION = None

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except Exception:
    ANTHROPIC_AVAILABLE = False

from omnix_config.settings import settings
from omnix_core.cache.redis_cache import cache, cache_result
from omnix_core.utils.logger import get_logger
from omnix_services.ai_service.ai_error_handler import (
    ErrorClassifier, 
    ErrorCategory, 
    AIError,
    log_ai_error,
    should_skip_to_next_model
)

logger = get_logger(__name__)

# Timeouts adaptativos por proveedor (2025 best practices)
TIMEOUT_GEMINI    = 30.0   # Gemini necesita más tiempo para function calling
TIMEOUT_OPENAI    = 30.0   # OpenAI timeout aumentado para evitar cortes en respuestas largas
TIMEOUT_ANTHROPIC = 30.0   # Claude similar a OpenAI
TIMEOUT_GROQ      = 30.0   # Groq LPU inference — muy rápido, timeout conservador (ADR-190)
TIMEOUT_MISTRAL   = 30.0   # Mistral AI — European sovereign provider (ADR-190)


class AIModelsManager:
    """Enterprise AI Models Manager - Multi-AI Strategy"""
    
    MIN_RESPONSE_LENGTH = 50
    MIN_RESPONSE_LENGTH_SIMPLE = 10  # Lower threshold for simple queries (greetings, etc)
    MAX_RETRIES_PER_MODEL = 3
    BASE_DELAY_SECONDS = 0.5
    
    INVALID_RESPONSE_PATTERNS = [
        r'^error',
        r'^sorry.*cannot',
        r'^i apologize.*unable',
        r'^\s*$',
        r'^none$',
        r'^null$',
    ]
    
    def __init__(self):
        """Initialize AI clients with fallback strategy"""
        self.openai_client = None
        self.gemini_client = None
        self.anthropic_client = None
        
        self.primary_model = settings.ai.primary_model
        self.fallback_models = settings.ai.fallback_models
        
        self.groq_client    = None
        self.mistral_client = None

        self._initialize_openai()
        self._initialize_gemini()
        self._initialize_anthropic()
        self._initialize_groq()
        self._initialize_mistral()

        # ── ADR-190: Sovereign AI Layer — chain ordering ──────────────────────
        sovereign_mode = os.getenv('OMNIX_AI_SOVEREIGN_MODE', 'false').lower() == 'true'
        base_fallbacks  = list(self.fallback_models)

        if sovereign_mode:
            # Open-source models lead — Groq/Llama-3 first, Mistral second
            self.primary_model   = 'groq-llama-3'
            self.fallback_models = ['mistral-large'] + [self.primary_model] + base_fallbacks
            logger.info("🛡️  [SAL] SOVEREIGN MODE ACTIVE — Groq/Llama-3 leads | SAL-INV-001 enforced")
        else:
            # Standard chain: existing providers + sovereign providers appended as last fallbacks
            self.fallback_models = base_fallbacks + ['groq-llama-3', 'mistral-large']

        available = []
        if self.openai_client:    available.append("OpenAI")
        if self.gemini_client:    available.append("Gemini")
        if self.anthropic_client: available.append("Anthropic")
        if self.groq_client:      available.append("Groq/Llama-3[SOVEREIGN]")
        if self.mistral_client:   available.append("Mistral[SOVEREIGN-EU]")
        logger.info(
            f"🤖 AI Fallback Chain: Primary={self.primary_model} | "
            f"Available: {available or ['NONE']} | Sovereign={sovereign_mode}"
        )
    
    def _validate_response(self, response: Optional[str], is_simple: bool = False) -> Tuple[bool, str]:
        """
        Validate AI response before sending to user
        
        Args:
            response: The AI response text
            is_simple: If True, use relaxed validation for simple queries (greetings, etc)
        
        Returns:
            Tuple[bool, str]: (is_valid, reason)
        """
        if response is None:
            return False, "Response is None"
        
        if not isinstance(response, str):
            return False, f"Response is not string: {type(response)}"
        
        response_clean = response.strip()
        
        # Use relaxed length threshold for simple queries
        min_length = self.MIN_RESPONSE_LENGTH_SIMPLE if is_simple else self.MIN_RESPONSE_LENGTH
        if len(response_clean) < min_length:
            return False, f"Response too short: {len(response_clean)} chars (min: {min_length})"
        
        response_lower = response_clean.lower()
        for pattern in self.INVALID_RESPONSE_PATTERNS:
            if re.match(pattern, response_lower):
                return False, f"Response matches invalid pattern: {pattern}"
        
        return True, "Valid"
    
    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter"""
        import random
        delay = self.BASE_DELAY_SECONDS * (2 ** attempt)
        jitter = random.uniform(0, delay * 0.1)
        return min(delay + jitter, 5.0)
    
    def _initialize_openai(self):
        """Initialize OpenAI GPT-4o with Async support"""
        if os.getenv('OMNIX_DISABLE_OPENAI', 'false').lower() == 'true':
            logger.info("ℹ️  OpenAI deshabilitado via OMNIX_DISABLE_OPENAI=true")
            return
        try:
            if settings.ai.openai_key:
                self.openai_client = AsyncOpenAI(api_key=settings.ai.openai_key)
                logger.info("✅ OpenAI GPT-4o (Async) initialized successfully")
            else:
                logger.warning("⚠️ OpenAI API key not found")
        except Exception as e:
            logger.error(f"❌ Error initializing OpenAI: {e}")
    
    def _initialize_gemini(self):
        """Initialize Google Gemini 2.0 with new SDK (google-genai) or legacy fallback"""
        try:
            if GEMINI_AVAILABLE and settings.ai.gemini_key:
                if GEMINI_SDK_VERSION == 'new':
                    self.gemini_client = genai.Client(api_key=settings.ai.gemini_key)
                    logger.info("✅ Gemini 2.0 initialized with NEW SDK (google-genai)")
                else:
                    genai.configure(api_key=settings.ai.gemini_key)
                    self.gemini_client = True
                    logger.info("✅ Gemini 2.0 initialized with LEGACY SDK (google-generativeai)")
            else:
                logger.warning("⚠️ Gemini API key not found or library unavailable")
        except Exception as e:
            logger.error(f"❌ Error initializing Gemini: {e}")
    
    def _initialize_anthropic(self):
        """Initialize Anthropic Claude"""
        try:
            if ANTHROPIC_AVAILABLE and os.getenv('ANTHROPIC_API_KEY'):
                self.anthropic_client = anthropic.Anthropic(
                    api_key=os.getenv('ANTHROPIC_API_KEY')
                )
                logger.info("✅ Anthropic Claude initialized successfully")
        except Exception as e:
            logger.error(f"❌ Error initializing Anthropic: {e}")

    def _initialize_groq(self):
        """Initialize Groq/Llama-3 — open-source sovereign AI provider (ADR-190 SAL-INV-001)"""
        try:
            groq_key = os.getenv('GROQ_API_KEY')
            if groq_key:
                self.groq_client = AsyncOpenAI(
                    api_key=groq_key,
                    base_url="https://api.groq.com/openai/v1",
                )
                logger.info("✅ Groq/Llama-3 [SOVEREIGN] initialized — ADR-190 SAL-INV-001 active")
            else:
                logger.info("ℹ️  GROQ_API_KEY not set — Groq/Llama-3 unavailable (set to enable sovereign mode)")
        except Exception as e:
            logger.error(f"❌ Error initializing Groq: {e}")

    def _initialize_mistral(self):
        """Initialize Mistral AI — European sovereign provider (ADR-190)"""
        try:
            mistral_key = os.getenv('MISTRAL_API_KEY')
            if mistral_key:
                self.mistral_client = AsyncOpenAI(
                    api_key=mistral_key,
                    base_url="https://api.mistral.ai/v1",
                )
                logger.info("✅ Mistral AI [SOVEREIGN-EU] initialized — ADR-190 active")
            else:
                logger.info("ℹ️  MISTRAL_API_KEY not set — Mistral unavailable")
        except Exception as e:
            logger.error(f"❌ Error initializing Mistral: {e}")
    
    async def generate(
        self, 
        prompt: str, 
        system_prompt: str,
        model: Optional[str] = None,
        max_retries: int = 2
    ) -> Optional[str]:
        """
        Generate AI response with automatic fallback, retry logic, and validation
        
        Uses intelligent error classification to:
        - Skip immediately to next model on non-retryable errors (401, 403, 404)
        - Retry with backoff on retryable errors (429, 500, 503, timeout)
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            model: Specific model to use (optional)
            max_retries: Number of retries per model (default 3 with exponential backoff)
            
        Returns:
            Generated response or None
        """
        if model:
            model_priority = [model] + [m for m in self.fallback_models if m != model]
        else:
            model_priority = [self.primary_model] + self.fallback_models
        
        def _model_label(name: str) -> str:
            n = name.lower()
            if 'gpt-4o-mini' in n: return 'GPT-4o-mini'
            if 'gpt-4o' in n:      return 'GPT-4o'
            if 'gemini' in n:      return 'GEMINI'
            if 'claude' in n:      return 'CLAUDE'
            if 'groq' in n:        return 'GROQ/LLAMA-3[SOVEREIGN]'
            if 'mistral' in n:     return 'MISTRAL[SOVEREIGN-EU]'
            return name.upper()

        total_attempts = 0
        last_error: Optional[AIError] = None
        errors_summary: list = []

        for model_idx, model_name in enumerate(model_priority):
            model_failed_permanently = False
            label = _model_label(model_name)

            if model_idx == 0:
                logger.info(f"[AI] PRIMARY → {label}")
            else:
                prev_label = _model_label(model_priority[model_idx - 1])
                reason = last_error.category.value if last_error else "unknown"
                logger.warning(
                    f"[AI] PRIMARY_FAILED ({prev_label}) → FALLBACK_{label} | reason={reason} | attempts_so_far={total_attempts}"
                )

            for attempt in range(max_retries):
                total_attempts += 1
                response = None
                ai_error = None
                
                is_simple = False
                if 'gpt' in model_name.lower():
                    is_simple = self._is_simple_query(prompt)
                    if is_simple:
                        logger.info(f"[AI] {label} → fast-path (simple query)")
                        response, ai_error = await self._generate_openai_fast_async(prompt, system_prompt)
                    else:
                        response, ai_error = await self._generate_openai_async(prompt, system_prompt)
                elif 'gemini' in model_name.lower():
                    response, ai_error = await self._generate_gemini_async(prompt, system_prompt)
                elif 'claude' in model_name.lower():
                    response, ai_error = await self._generate_anthropic_async(prompt, system_prompt)
                elif 'groq' in model_name.lower():
                    response, ai_error = await self._generate_groq_async(prompt, system_prompt)
                elif 'mistral' in model_name.lower():
                    response, ai_error = await self._generate_mistral_async(prompt, system_prompt)
                
                if ai_error:
                    last_error = ai_error
                    errors_summary.append(f"{ai_error.provider}:{ai_error.category.value}")
                    
                    if should_skip_to_next_model(ai_error):
                        logger.warning(
                            f"[AI] {label} SKIP (non-retryable) | error={ai_error.category.value} | msg={ai_error.message[:80]}"
                        )
                        model_failed_permanently = True
                        break
                    
                    if ai_error.is_retryable and attempt < max_retries - 1:
                        delay = self._calculate_backoff_delay(attempt)
                        logger.info(f"[AI] {label} RETRY {attempt + 1}/{max_retries} | backoff={delay:.2f}s")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        continue
                
                is_valid, reason = self._validate_response(response, is_simple=is_simple)
                
                if is_valid:
                    logger.info(
                        f"[AI] {label} SUCCESS | attempt={attempt + 1} | total_attempts={total_attempts} | chars={len(response)}"
                    )
                    return response
                else:
                    logger.warning(f"[AI] {label} VALIDATION_FAIL | reason={reason}")
                    if attempt < max_retries - 1:
                        delay = self._calculate_backoff_delay(attempt)
                        await asyncio.sleep(delay)
                    continue
            
            if model_failed_permanently:
                logger.info(f"[AI] {label} SKIPPED (non-retryable error) — advancing to next model")
            else:
                logger.warning(f"[AI] {label} EXHAUSTED ({max_retries} attempts) — advancing to next model")
        
        error_msg = last_error.log_message() if last_error else "Unknown"
        suggestion = last_error.suggested_action if last_error else "Revisar configuración de API keys"
        logger.error(
            f"[AI] CHAIN_EXHAUSTED | all_models_failed | total_attempts={total_attempts}"
            f" | errors={errors_summary} | last_error={error_msg}"
        )
        logger.error(f"[AI] DIAGNOSTIC | action={suggestion}")
        return None
    
    async def _generate_openai_async(self, prompt: str, system_prompt: str) -> Tuple[Optional[str], Optional[AIError]]:
        """Generate with OpenAI GPT-4o (Async with timeout) - Returns (response, error)"""
        if not self.openai_client:
            return None, AIError(
                provider="openai",
                category=ErrorCategory.AUTH_ERROR,
                http_code=None,
                message="OpenAI client no inicializado - Falta OPENAI_API_KEY",
                raw_error=None,
                is_retryable=False,
                suggested_action="Configurar OPENAI_API_KEY en Railway"
            )
        
        try:
            enhanced_system = f"""{system_prompt}

## ENHANCED ANALYSIS REQUIREMENTS
- Deep analysis with 1500-2500 characters minimum
- Institutional-grade financial expertise
- Connect minimum 5 variables: price + volume + macro + psychology + on-chain
- Specific correlations with real numerical data
- Unique insights beyond the obvious
- Professional structure with numbered headers

## OMNIX CONTEXT
System operating with live Kraken APIs, Enterprise technical analysis, active bidirectional trading.

IMPORTANT: Demonstrate superintelligence in every response. Follow the language policy strictly."""

            response = await asyncio.wait_for(
                self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": enhanced_system},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.85,
                    max_tokens=4000,
                    top_p=0.95,
                    presence_penalty=0.1,
                    frequency_penalty=0.1
                ),
                timeout=TIMEOUT_OPENAI
            )
            
            result = response.choices[0].message.content if response.choices else None
            
            if result:
                logger.info(f"✅ GPT-4o generated {len(result)} characters")
            
            return result, None
        
        except asyncio.TimeoutError:
            ai_error = ErrorClassifier.classify_timeout("openai", TIMEOUT_OPENAI)
            log_ai_error(ai_error)
            return None, ai_error
        except Exception as e:
            ai_error = ErrorClassifier.classify_openai_error(e)
            log_ai_error(ai_error)
            return None, ai_error
    
    async def _generate_openai_fast_async(self, prompt: str, system_prompt: str) -> Tuple[Optional[str], Optional[AIError]]:
        """Generate with GPT-4o-mini for fast, simple responses - 3x faster than GPT-4o"""
        if not self.openai_client:
            return None, AIError(
                provider="openai",
                category=ErrorCategory.AUTH_ERROR,
                http_code=None,
                message="OpenAI client no inicializado - Falta OPENAI_API_KEY",
                raw_error=None,
                is_retryable=False,
                suggested_action="Configurar OPENAI_API_KEY en Railway"
            )
        
        try:
            response = await asyncio.wait_for(
                self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1500,
                    top_p=0.9
                ),
                timeout=15.0  # Mini es mucho más rápido
            )
            
            result = response.choices[0].message.content if response.choices else None
            
            if result:
                logger.info(f"⚡ GPT-4o-mini generated {len(result)} characters (fast mode)")
            
            return result, None
        
        except asyncio.TimeoutError:
            ai_error = ErrorClassifier.classify_timeout("openai-mini", 15.0)
            log_ai_error(ai_error)
            return None, ai_error
        except Exception as e:
            ai_error = ErrorClassifier.classify_openai_error(e)
            log_ai_error(ai_error)
            return None, ai_error
    
    def _is_simple_query(self, prompt: str) -> bool:
        """Detect simple queries that don't need GPT-4o full analysis"""
        simple_patterns = [
            r'^(hola|hello|hi|hey|buenos?\s*d[ií]as?|buenas?\s*tardes?|buenas?\s*noches?)',
            r'^(c[oó]mo\s*est[aá]s?|how\s*are\s*you|qu[eé]\s*tal)',
            r'^(gracias|thanks|thank\s*you|te agradezco)',
            r'^(adi[oó]s|bye|chao|hasta\s*luego|nos vemos)',
            r'^\?$',
            r'^(s[ií]|no|ok|okay|dale|listo|entendido|perfecto|genial)$',
            r'^(test|ping|status)$',
            r'^(qui[eé]n\s*eres|who\s*are\s*you|qu[eé]\s*eres)',
            r'^(ayuda|help|menu|men[uú])$',
            r'^(qu[eé]\s*puedes\s*hacer|what\s*can\s*you\s*do)',
            r'^(buen\s*d[ií]a|good\s*morning|good\s*night|good\s*evening)',
        ]
        
        prompt_lower = prompt.lower().strip()
        
        if len(prompt_lower) < 30:
            trading_keywords = ['btc', 'eth', 'xrp', 'sol', 'ada', 'precio', 'price', 'mercado', 'market', 
                               'trade', 'trading', 'buy', 'sell', 'comprar', 'vender', 
                               'análisis', 'analisis', 'analysis', 'reporte', 'report',
                               'portafolio', 'portfolio', 'balance', 'señal', 'signal',
                               'riesgo', 'risk', 'kelly', 'monte carlo', 'veto',
                               'inversi', 'invest', 'rendimiento', 'performance']
            has_trading = any(kw in prompt_lower for kw in trading_keywords)
            if not has_trading:
                return True
        
        for pattern in simple_patterns:
            if re.match(pattern, prompt_lower, re.IGNORECASE):
                return True
        
        return False
    
    async def generate_smart_async(self, prompt: str, system_prompt: str) -> Tuple[Optional[str], Optional[AIError]]:
        """Smart model selection: GPT-4o-mini for simple, GPT-4o for complex"""
        if self._is_simple_query(prompt):
            logger.info(f"⚡ Using GPT-4o-mini for simple query: '{prompt[:50]}...'")
            return await self._generate_openai_fast_async(prompt, system_prompt)
        else:
            return await self._generate_openai_async(prompt, system_prompt)
    
    async def _generate_gemini_async(self, prompt: str, system_prompt: str) -> Tuple[Optional[str], Optional[AIError]]:
        """Generate with Gemini 2.0 (Async via thread pool with timeout) - Returns (response, error)"""
        if not self.gemini_client:
            return None, AIError(
                provider="gemini",
                category=ErrorCategory.AUTH_ERROR,
                http_code=None,
                message="Gemini client no inicializado - Falta GEMINI_API_KEY",
                raw_error=None,
                is_retryable=False,
                suggested_action="Configurar GEMINI_API_KEY en Railway"
            )
        
        try:
            loop = asyncio.get_event_loop()
            result, sync_error = await asyncio.wait_for(
                loop.run_in_executor(None, self._generate_gemini_sync, prompt, system_prompt),
                timeout=TIMEOUT_GEMINI
            )
            return result, sync_error
        except asyncio.TimeoutError:
            ai_error = ErrorClassifier.classify_timeout("gemini", TIMEOUT_GEMINI)
            log_ai_error(ai_error)
            return None, ai_error
        except Exception as e:
            ai_error = ErrorClassifier.classify_gemini_error(e)
            log_ai_error(ai_error)
            return None, ai_error
    
    def _generate_gemini_sync(self, prompt: str, system_prompt: str) -> Tuple[Optional[str], Optional[AIError]]:
        """Generate with Gemini 2.0 (Sync) - Supports both new and legacy SDK - Returns (response, error)"""
        try:
            enhanced_prompt = f"""{system_prompt}

## CHAIN-OF-THOUGHT ANALYSIS FRAMEWORK
Follow this structured approach for comprehensive analysis:
**1. Immediate Analysis** **2. Technical Data** **3. Implications** **4. Recommendations** **5. Historical Perspective**

User Query: {prompt}

Generate a substantial response of 2000+ characters. Follow the language policy strictly - respond in the same language as the user's query."""

            if GEMINI_SDK_VERSION == 'new' and self.gemini_client:
                response = self.gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=enhanced_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.85,
                        max_output_tokens=8000,
                        top_p=0.95,
                        top_k=40
                    )
                )
                text = self._extract_gemini_text(response, 'new')
                if text:
                    logger.info(f"✅ Gemini (new SDK) generated {len(text)} characters")
                    return text, None
            elif GEMINI_SDK_VERSION == 'legacy':
                model = genai.GenerativeModel(
                    "gemini-2.5-flash",
                    system_instruction=system_prompt
                )
                response = model.generate_content(
                    enhanced_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.85,
                        top_p=0.95,
                        max_output_tokens=8000,
                        top_k=40
                    )
                )
                text = self._extract_gemini_text(response, 'legacy')
                if text:
                    logger.info(f"✅ Gemini (legacy SDK) generated {len(text)} characters")
                    return text, None
            
            return None, None
            
        except Exception as e:
            ai_error = ErrorClassifier.classify_gemini_error(e)
            log_ai_error(ai_error)
            return None, ai_error
    
    async def _generate_anthropic_async(self, prompt: str, system_prompt: str) -> Tuple[Optional[str], Optional[AIError]]:
        """Generate with Anthropic Claude (Async via thread pool with timeout) - Returns (response, error)"""
        if not self.anthropic_client:
            return None, AIError(
                provider="anthropic",
                category=ErrorCategory.AUTH_ERROR,
                http_code=None,
                message="Anthropic client no inicializado - Falta ANTHROPIC_API_KEY",
                raw_error=None,
                is_retryable=False,
                suggested_action="Configurar ANTHROPIC_API_KEY en Railway"
            )
        
        try:
            loop = asyncio.get_event_loop()
            result, sync_error = await asyncio.wait_for(
                loop.run_in_executor(None, self._generate_anthropic_sync, prompt, system_prompt),
                timeout=TIMEOUT_ANTHROPIC
            )
            return result, sync_error
        except asyncio.TimeoutError:
            ai_error = ErrorClassifier.classify_timeout("anthropic", TIMEOUT_ANTHROPIC)
            log_ai_error(ai_error)
            return None, ai_error
        except Exception as e:
            ai_error = ErrorClassifier.classify_anthropic_error(e)
            log_ai_error(ai_error)
            return None, ai_error
    
    def _generate_anthropic_sync(self, prompt: str, system_prompt: str) -> Tuple[Optional[str], Optional[AIError]]:
        """Generate with Anthropic Claude (Sync) - Returns (response, error)"""
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0.8,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = response.content[0].text if response.content else None
            
            if result:
                logger.info(f"✅ Claude generated {len(result)} characters")
            
            return result, None
            
        except Exception as e:
            ai_error = ErrorClassifier.classify_anthropic_error(e)
            log_ai_error(ai_error)
            return None, ai_error
    
    def _extract_gemini_text(self, response, sdk_version: str) -> Optional[str]:
        """Extract text from Gemini response - handles both new and legacy SDK formats"""
        if not response:
            return None
        try:
            if hasattr(response, 'text') and response.text:
                return response.text
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        return candidate.content.parts[0].text
            logger.warning(f"⚠️ Could not extract text from Gemini response (SDK: {sdk_version})")
            return None
        except Exception as e:
            logger.error(f"❌ Error extracting Gemini text: {e}")
            return None
    
    async def _generate_groq_async(self, prompt: str, system_prompt: str) -> Tuple[Optional[str], Optional[AIError]]:
        """Generate with Groq/Llama-3.3-70b — open-source sovereign inference (ADR-190)"""
        if not self.groq_client:
            return None, AIError(
                provider="groq",
                category=ErrorCategory.AUTH_ERROR,
                http_code=None,
                message="Groq client no inicializado — configura GROQ_API_KEY (ADR-190 SAL)",
                raw_error=None,
                is_retryable=False,
                suggested_action="Configurar GROQ_API_KEY en Railway para activar modo soberano"
            )
        try:
            response = await asyncio.wait_for(
                self.groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": prompt},
                    ],
                    temperature=0.8,
                    max_tokens=4000,
                    top_p=0.95,
                ),
                timeout=TIMEOUT_GROQ
            )
            result = response.choices[0].message.content if response.choices else None
            if result:
                logger.info(f"✅ Groq/Llama-3 [SOVEREIGN] generated {len(result)} characters")
            return result, None
        except asyncio.TimeoutError:
            ai_error = ErrorClassifier.classify_timeout("groq", TIMEOUT_GROQ)
            log_ai_error(ai_error)
            return None, ai_error
        except Exception as e:
            ai_error = AIError(
                provider="groq",
                category=ErrorCategory.UNKNOWN_ERROR,
                http_code=None,
                message=str(e)[:200],
                raw_error=e,
                is_retryable=True,
                suggested_action="Verificar GROQ_API_KEY y cuota en console.groq.com"
            )
            log_ai_error(ai_error)
            return None, ai_error

    async def _generate_mistral_async(self, prompt: str, system_prompt: str) -> Tuple[Optional[str], Optional[AIError]]:
        """Generate with Mistral AI — European sovereign provider (ADR-190)"""
        if not self.mistral_client:
            return None, AIError(
                provider="mistral",
                category=ErrorCategory.AUTH_ERROR,
                http_code=None,
                message="Mistral client no inicializado — configura MISTRAL_API_KEY (ADR-190 SAL)",
                raw_error=None,
                is_retryable=False,
                suggested_action="Configurar MISTRAL_API_KEY en Railway para activar proveedor EU soberano"
            )
        try:
            response = await asyncio.wait_for(
                self.mistral_client.chat.completions.create(
                    model="mistral-large-latest",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": prompt},
                    ],
                    temperature=0.8,
                    max_tokens=4000,
                    top_p=0.95,
                ),
                timeout=TIMEOUT_MISTRAL
            )
            result = response.choices[0].message.content if response.choices else None
            if result:
                logger.info(f"✅ Mistral AI [SOVEREIGN-EU] generated {len(result)} characters")
            return result, None
        except asyncio.TimeoutError:
            ai_error = ErrorClassifier.classify_timeout("mistral", TIMEOUT_MISTRAL)
            log_ai_error(ai_error)
            return None, ai_error
        except Exception as e:
            ai_error = AIError(
                provider="mistral",
                category=ErrorCategory.UNKNOWN_ERROR,
                http_code=None,
                message=str(e)[:200],
                raw_error=e,
                is_retryable=True,
                suggested_action="Verificar MISTRAL_API_KEY y cuota en console.mistral.ai"
            )
            log_ai_error(ai_error)
            return None, ai_error

    def health_check(self) -> Dict[str, bool]:
        """Check health status of all AI models — ADR-190: includes sovereign providers"""
        return {
            'openai':    self.openai_client    is not None,
            'gemini':    self.gemini_client    is not None,
            'anthropic': self.anthropic_client is not None,
            'groq':      self.groq_client      is not None,
            'mistral':   self.mistral_client   is not None,
        }
