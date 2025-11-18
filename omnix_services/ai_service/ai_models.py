"""
OMNIX V5.1 ENTERPRISE - AI Models Manager
Gestión de múltiples modelos IA: GPT-4o, Gemini 2.0, Claude
Escalabilidad: 50K+ usuarios con Async verdadero
"""

import logging
import os
import asyncio
from typing import Optional, Dict, Any
from openai import AsyncOpenAI
try:
    import google.generativeai as genai
    from google.generativeai import types
    GEMINI_AVAILABLE = True
except:
    GEMINI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except:
    ANTHROPIC_AVAILABLE = False

from omnix_config.settings import settings
from omnix_core.cache.redis_cache import cache, cache_result
from omnix_core.utils.logger import get_logger

logger = get_logger(__name__)


class AIModelsManager:
    """Enterprise AI Models Manager - Multi-AI Strategy"""
    
    def __init__(self):
        """Initialize AI clients with fallback strategy"""
        self.openai_client = None
        self.gemini_client = None
        self.anthropic_client = None
        
        self.primary_model = settings.ai.primary_model
        self.fallback_models = settings.ai.fallback_models
        
        self._initialize_openai()
        self._initialize_gemini()
        self._initialize_anthropic()
    
    def _initialize_openai(self):
        """Initialize OpenAI GPT-4o with Async support"""
        try:
            if settings.ai.openai_key:
                self.openai_client = AsyncOpenAI(api_key=settings.ai.openai_key)
                logger.info("✅ OpenAI GPT-4o (Async) initialized successfully")
            else:
                logger.warning("⚠️ OpenAI API key not found")
        except Exception as e:
            logger.error(f"❌ Error initializing OpenAI: {e}")
    
    def _initialize_gemini(self):
        """Initialize Google Gemini 2.0"""
        try:
            if GEMINI_AVAILABLE and settings.ai.gemini_key:
                if hasattr(genai, 'Client'):
                    self.gemini_client = genai.Client(api_key=settings.ai.gemini_key)
                else:
                    genai.configure(api_key=settings.ai.gemini_key)
                logger.info("✅ Gemini 2.0 initialized successfully")
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
    
    async def generate(
        self, 
        prompt: str, 
        system_prompt: str,
        model: Optional[str] = None,
        max_retries: int = 1
    ) -> Optional[str]:
        """
        Generate AI response with automatic fallback
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            model: Specific model to use (optional)
            max_retries: Number of retries per model (default 1 for speed)
            
        Returns:
            Generated response or None
        """
        # Determine model priority
        if model:
            model_priority = [model] + [m for m in self.fallback_models if m != model]
        else:
            # Siempre usar primary_model primero, luego fallbacks
            model_priority = [self.primary_model] + self.fallback_models
        
        # Try each model in priority order (1 intento por modelo para velocidad)
        for model_name in model_priority:
            for attempt in range(max_retries):
                try:
                    if 'gpt' in model_name.lower():
                        response = await self._generate_openai_async(prompt, system_prompt)
                        if response:
                            logger.info(f"✅ OpenAI response generated (attempt {attempt + 1})")
                            return response
                    
                    elif 'gemini' in model_name.lower():
                        response = await self._generate_gemini_async(prompt, system_prompt)
                        if response:
                            logger.info(f"✅ Gemini response generated (attempt {attempt + 1})")
                            return response
                    
                    elif 'claude' in model_name.lower():
                        response = await self._generate_anthropic_async(prompt, system_prompt)
                        if response:
                            logger.info(f"✅ Claude response generated (attempt {attempt + 1})")
                            return response
                    
                except Exception as e:
                    logger.warning(f"⚠️ {model_name} attempt {attempt + 1} failed: {e}")
                    # Sin delay - pasar inmediatamente al siguiente modelo
                    continue
        
        logger.error("❌ All AI models failed to generate response")
        return None
    
    async def _generate_openai_async(self, prompt: str, system_prompt: str) -> Optional[str]:
        """Generate with OpenAI GPT-4o (Async with timeout)"""
        if not self.openai_client:
            return None
        
        try:
            # Enhanced system prompt for Harold
            enhanced_system = f"""{system_prompt}

🧠 SUPERINTELIGENCIA GPT-4o PARA HAROLD:
- Análisis profundo de 1500-2500 caracteres
- Expertise financiero nivel institucional
- Conectar mínimo 5 variables: precio + volumen + macro + psicología + on-chain
- Correlaciones específicas con datos numéricos reales
- Insights únicos más allá de lo obvio
- Estructura profesional con headers numerados

💹 CONTEXTO OMNIX:
Sistema operando con APIs Kraken en tiempo real, análisis técnico Enterprise, trading bidireccional activo.

⚠️ IMPORTANTE: Harold necesita demostración de superinteligencia en cada respuesta."""

            # TIMEOUT DE 10 SEGUNDOS para GPT-4o
            response = await asyncio.wait_for(
                self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": enhanced_system},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.85,
                    max_tokens=1500,
                    top_p=0.95,
                    presence_penalty=0.1,
                    frequency_penalty=0.1
                ),
                timeout=10.0
            )
            
            result = response.choices[0].message.content if response.choices else None
            
            if result:
                logger.info(f"✅ GPT-4o generated {len(result)} characters")
            
            return result
        
        except asyncio.TimeoutError:
            logger.warning("⚠️ OpenAI timeout (10s) - intentando siguiente modelo")
            return None
        except Exception as e:
            logger.error(f"❌ OpenAI generation error: {e}")
            return None
    
    async def _generate_gemini_async(self, prompt: str, system_prompt: str) -> Optional[str]:
        """Generate with Gemini 2.0 (Async via thread pool with timeout)"""
        try:
            # Gemini SDK doesn't have native async, run in thread pool WITH TIMEOUT
            loop = asyncio.get_event_loop()
            # TIMEOUT DE 8 SEGUNDOS - Si Gemini tarda más, abortar y pasar al siguiente
            result = await asyncio.wait_for(
                loop.run_in_executor(None, self._generate_gemini_sync, prompt, system_prompt),
                timeout=8.0
            )
            return result
        except asyncio.TimeoutError:
            logger.warning("⚠️ Gemini timeout (8s) - intentando siguiente modelo")
            return None
        except Exception as e:
            logger.error(f"❌ Gemini async generation error: {e}")
            return None
    
    def _generate_gemini_sync(self, prompt: str, system_prompt: str) -> Optional[str]:
        """Generate with Gemini 2.0 (Sync)"""
        try:
            # Enhanced prompt for deep analysis
            enhanced_prompt = f"""{system_prompt}

IMPORTANTE: Harold necesita análisis PROFUNDO e inteligente:
**1. Análisis Inmediato** **2. Datos Técnicos** **3. Implicaciones** **4. Recomendaciones** **5. Perspectiva Histórica**

Usuario: {prompt}

GENERAR RESPUESTA SUSTANCIAL DE 2000+ CARACTERES."""

            if hasattr(genai, 'Client') and self.gemini_client:
                response = self.gemini_client.models.generate_content(
                    model="gemini-2.0-flash-exp",
                    contents=enhanced_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.85,
                        max_output_tokens=4000,
                        top_p=0.95,
                        top_k=40
                    )
                )
                if response and response.text:
                    logger.info(f"✅ Gemini generated {len(response.text)} characters")
                    return response.text
            else:
                model = genai.GenerativeModel(
                    "gemini-2.0-flash-exp",
                    system_instruction=system_prompt
                )
                response = model.generate_content(
                    enhanced_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.85,
                        top_p=0.95,
                        max_output_tokens=4000,
                        top_k=40
                    )
                )
                if response and response.text:
                    logger.info(f"✅ Gemini generated {len(response.text)} characters")
                    return response.text
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Gemini generation error: {e}")
            return None
    
    async def _generate_anthropic_async(self, prompt: str, system_prompt: str) -> Optional[str]:
        """Generate with Anthropic Claude (Async via thread pool with timeout)"""
        if not self.anthropic_client:
            return None
        
        try:
            # Anthropic SDK doesn't have native async, run in thread pool WITH TIMEOUT
            loop = asyncio.get_event_loop()
            # TIMEOUT DE 8 SEGUNDOS - Si Claude tarda más, abortar
            result = await asyncio.wait_for(
                loop.run_in_executor(None, self._generate_anthropic_sync, prompt, system_prompt),
                timeout=8.0
            )
            return result
        except asyncio.TimeoutError:
            logger.warning("⚠️ Claude timeout (8s) - abortando")
            return None
        except Exception as e:
            logger.error(f"❌ Anthropic async generation error: {e}")
            return None
    
    def _generate_anthropic_sync(self, prompt: str, system_prompt: str) -> Optional[str]:
        """Generate with Anthropic Claude (Sync)"""
        if not self.anthropic_client:
            return None
        
        try:
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                temperature=0.8,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = response.content[0].text if response.content else None
            
            if result:
                logger.info(f"✅ Claude generated {len(result)} characters")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Anthropic generation error: {e}")
            return None
    
    def health_check(self) -> Dict[str, bool]:
        """Check health status of all AI models"""
        return {
            'openai': self.openai_client is not None,
            'gemini': self.gemini_client is not None,
            'anthropic': self.anthropic_client is not None
        }
