"""
OMNIX V6.0 ULTRA - Conversational AI Adapter
Adapter class que mantiene compatibilidad con código legacy
pero usa ConversationalAIService enterprise internamente
"""

import logging
import os
import re
import asyncio
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# ==============================================================================
# POST-PROCESSING FILTER - Removes servile/prohibited phrases from AI responses
# This is a safety net in case the AI ignores prompt instructions
# ==============================================================================

BLACKLISTED_PHRASES = [
    # Full preamble patterns (Spanish) - with or without name
    r'^Absolutamente[,.\s]+(\w+[,.\s]+)?',   # "Absolutamente." or "Absolutamente, Harold."
    r'^Por supuesto[,.\s]+(\w+[,.\s]+)?',    # "Por supuesto." or "Por supuesto, Harold."
    r'^Con mucho gusto[,.\s]+',
    r'^Encantado de\s+',
    # Servile phrases (Spanish) - anywhere, with or without period
    r'Asumo la responsabilidad[^.]*\.?\s*',
    r'Me disculpo por[^.]*\.?\s*',
    r'Lamento que[^.]*\.?\s*',
    # Meta-comments (Spanish)
    r'^Esta pregunta es importante[^.]*\.?\s*',
    r'^Esta pregunta es fundamental[^.]*\.?\s*',
    r'^Esta pregunta es crucial[^.]*\.?\s*',
    r'Vale la pena señalar que\s*',
    r'Es crucial destacar que\s*',
    r'Entiendo la seriedad[^.]*\.?\s*',
    r'Entiendo tu pregunta[^.]*\.?\s*',
    r'Entiendo su pregunta[^.]*\.?\s*',
    # Full preamble patterns (English) - with or without name
    r'^Absolutely[,.\s]+(\w+[,.\s]+)?',
    r'^Of course[,.\s]+(\w+[,.\s]+)?',
    r'^With pleasure[,.\s]+',
    r'^Delighted to\s+',
    # Servile phrases (English) - with or without period
    r'I take responsibility[^.]*\.?\s*',
    r'I apologize for[^.]*\.?\s*',
    r'I regret that[^.]*\.?\s*',
    # Meta-comments (English)
    r'^This question is important[^.]*\.?\s*',
    r'^This question is fundamental[^.]*\.?\s*',
    r'^This question is crucial[^.]*\.?\s*',
    r"It's worth noting that\s*",
    r"It's crucial to highlight that\s*",
    r'I understand the seriousness[^.]*\.?\s*',
    r'I understand your question[^.]*\.?\s*',
    # Numbered section headers (remove preamble structure)
    r'^\*?\*?1\.\s*An[aá]lisis\s+Inmediato:?\*?\*?\s*',  # "1. Análisis Inmediato:"
    r'^\*?\*?2\.\s*Datos\s+T[eé]cnicos:?\*?\*?\s*',      # "2. Datos Técnicos:"
    r'^\*?\*?3\.\s*Conclusi[oó]n:?\*?\*?\s*',            # "3. Conclusión:"
    r'^\*?\*?1\.\s*Immediate\s+Analysis:?\*?\*?\s*',     # "1. Immediate Analysis:"
    r'^\*?\*?2\.\s*Technical\s+Data:?\*?\*?\s*',         # "2. Technical Data:"
    r'^\*?\*?3\.\s*Conclusion:?\*?\*?\s*',               # "3. Conclusion:"
]

BLACKLISTED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in BLACKLISTED_PHRASES]

def post_process_response(response: str) -> str:
    """
    Remove blacklisted phrases from AI response.
    This is a safety net that runs AFTER AI generation.
    
    Args:
        response: Raw AI response text
        
    Returns:
        Cleaned response with servile/prohibited phrases removed
    """
    if not response:
        return response
    
    cleaned = response
    
    # Remove blacklisted patterns
    for pattern in BLACKLISTED_PATTERNS:
        cleaned = pattern.sub('', cleaned)
    
    # Clean up leading whitespace/punctuation after removal
    cleaned = re.sub(r'^[\s,.\-]+', '', cleaned)
    
    # Ensure first character is uppercase if we removed something
    if cleaned and cleaned[0].islower() and response[0].isupper():
        cleaned = cleaned[0].upper() + cleaned[1:] if len(cleaned) > 1 else cleaned.upper()
    
    # Log if we made changes (for debugging)
    if cleaned != response:
        logger.info(f"🛡️ Post-process filter: Removed servile phrases from response")
    
    return cleaned.strip()

try:
    from src.omnix.infrastructure.adapters.authorization_adapter import get_authorization_adapter
    from src.omnix.ports.driven.authorization_port import Permission
    AUTHORIZATION_AVAILABLE = True
except ImportError:
    AUTHORIZATION_AVAILABLE = False
    get_authorization_adapter = None
    Permission = None

# Import dependencies
try:
    from omnix_services.ai_service import ConversationalAIService
    from omnix_core.utils.rate_limiter import RateLimitExceeded
    OMNIX_ENTERPRISE_AVAILABLE = True
except ImportError:
    OMNIX_ENTERPRISE_AVAILABLE = False
    RateLimitExceeded = Exception

# AI clients
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

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


class ConversationalAI:
    """
    Adapter class que mantiene compatibilidad con firma vieja
    pero usa el nuevo ConversationalAIService enterprise internamente
    
    ✅ Redis state (horizontal scaling)
    ✅ Async verdadero (no bloquea)
    ✅ Rate limiting per-user
    ✅ Modular y escalable
    """
    def __init__(self):
        # Si sistema enterprise disponible, usarlo
        if OMNIX_ENTERPRISE_AVAILABLE:
            logger.info("🚀 Inicializando ConversationalAI con ENTERPRISE backend")
            self.enterprise_service = ConversationalAIService()
            self.using_enterprise = True
        else:
            logger.info("✅ Sistema IA Directo Activado - Gemini 2.0 Flash + GPT-4o")
            self.using_enterprise = False
            # Modo directo con APIs
            self.model_name = "gemini-2.0-flash-exp"
            self.conversation_history = {}
            self.user_preferences = {}
            self.market_context = {}
            self.intelligence_level = "ULTRA_COMPETITIVE_ENTERPRISE"
            # Initialize legacy AI clients for fallback
            self._init_legacy_clients()
    
    def _init_legacy_clients(self):
        """Initialize legacy AI clients if enterprise not available"""
        if not self.using_enterprise:
            try:
                if OPENAI_AVAILABLE and os.environ.get('OPENAI_API_KEY'):
                    self.openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
                    logger.info("✅ OpenAI GPT-4o inicializado correctamente")
                
                if GEMINI_AVAILABLE and os.environ.get('GEMINI_API_KEY'):
                    if GEMINI_SDK_VERSION == 'new':
                        self.gemini_client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
                        logger.info("✅ Gemini 2.0 Flash inicializado con NUEVO SDK (google-genai)")
                    else:
                        genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
                        self.gemini_client = genai.GenerativeModel('gemini-2.0-flash-exp')
                        logger.info("✅ Gemini 2.0 Flash inicializado con LEGACY SDK")
            except Exception as e:
                logger.error(f"Error initializing legacy AI clients: {e}")
    
    async def generate_response_async(self, user_message, user_name="Usuario", chat_id="", user_id=None, trading_system=None, diagnostic_mode=False):
        """
        🚀 ASYNC ENTERPRISE-GRADE RESPONSE GENERATION
        
        FIX Dec 13, 2025: Versión async para evitar deadlock en telegram handlers.
        Usar esta versión desde handlers async de python-telegram-bot.
        
        Args:
            diagnostic_mode: If True, uses DIAGNOSTIC_ONLY_PROMPT for RULE 13 compliance (Jan 1, 2026)
        """
        try:
            if self.using_enterprise:
                logger.info(f"🚀 [ASYNC] Generando respuesta ENTERPRISE para {user_name} (diagnostic_mode={diagnostic_mode})")
                
                chat_id_int = 0
                if chat_id:
                    try:
                        chat_id_int = int(chat_id)
                    except (ValueError, TypeError):
                        chat_id_int = 0
                
                if chat_id_int == 0 and user_id:
                    try:
                        chat_id_int = int(user_id)
                    except (ValueError, TypeError):
                        chat_id_int = 0
                
                logger.info(f"🧠 MEMORIA: chat_id={chat_id_int}")
                
                real_market_data = await self._fetch_real_market_data_async(trading_system, user_message, user_id=user_id)
                
                result = await self.enterprise_service.generate_response(
                    chat_id=chat_id_int,
                    user_message=user_message,
                    user_name=user_name,
                    market_data=real_market_data,
                    apply_visual_style=True,
                    diagnostic_mode=diagnostic_mode
                )
                
                if result and 'response' in result:
                    response_text = result['response']
                    if result.get('web_search_used'):
                        web_indicator = "\n\n🔍 *Real-time verified information*"
                        if "verified information" not in response_text.lower():
                            response_text = response_text + web_indicator
                        logger.info(f"🔍 Web search used")
                    # Apply post-processing filter to remove servile phrases
                    return post_process_response(response_text)
                else:
                    logger.error("❌ No response from enterprise service")
                    return self._fallback_response()
            else:
                logger.warning("⚠️ Using legacy AI generation")
                return post_process_response(self._legacy_generate_response(user_message, user_name, chat_id, user_id, trading_system))
        except RateLimitExceeded as e:
            logger.warning(f"⚠️ Rate limit exceeded: {e}")
            return "⏳ Rate limit reached. Please wait a moment..."
        except Exception as e:
            logger.error(f"❌ Error generating async response: {e}", exc_info=True)
            return self._fallback_response()
    
    def generate_response(self, user_message, user_name="Usuario", chat_id="", user_id=None, trading_system=None):
        """
        🚀 ENTERPRISE-GRADE RESPONSE GENERATION (SYNC VERSION)
        
        Mantiene compatibilidad con firma vieja pero usa sistema enterprise modular
        FIX Nov 28, 2025: Ahora pasa DATOS REALES de Kraken al AI
        WARNING: NO usar desde handlers async de telegram - usar generate_response_async() en su lugar
        """
        try:
            if self.using_enterprise:
                # 🔥 USO DEL NUEVO SISTEMA ENTERPRISE
                logger.info(f"🚀 Generando respuesta ENTERPRISE para {user_name}")
                
                # FIX Nov 29, 2025: Convertir chat_id a int robusto
                # Prioridad: chat_id > user_id > 0
                chat_id_int = 0
                if chat_id:
                    try:
                        chat_id_int = int(chat_id)
                    except (ValueError, TypeError):
                        chat_id_int = 0
                
                if chat_id_int == 0 and user_id:
                    try:
                        chat_id_int = int(user_id)
                    except (ValueError, TypeError):
                        chat_id_int = 0
                
                logger.info(f"🧠 MEMORIA: Usando chat_id={chat_id_int} (original: chat_id='{chat_id}', user_id='{user_id}')")
                
                # 📊 FIX: OBTENER DATOS REALES DE KRAKEN ANTES DE GENERAR RESPUESTA
                # FIX Dec 10, 2025: Pasar user_id para obtener datos de trading específicos del usuario
                real_market_data = self._fetch_real_market_data(trading_system, user_message, user_id=user_id)
                
                # RAILWAY FIX: Usar asyncio de forma segura
                try:
                    # Intentar obtener loop existente (Railway webhook thread)
                    loop = asyncio.get_running_loop()
                    # Si hay un loop corriendo, usar run_coroutine_threadsafe
                    import concurrent.futures
                    future = asyncio.run_coroutine_threadsafe(
                        self.enterprise_service.generate_response(
                            chat_id=chat_id_int,
                            user_message=user_message,
                            user_name=user_name,
                            market_data=real_market_data,
                            apply_visual_style=True
                        ),
                        loop
                    )
                    # Esperar resultado con timeout de 30 segundos
                    result = future.result(timeout=30)
                except RuntimeError:
                    # No hay loop corriendo, crear uno nuevo (Replit/local)
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    result = loop.run_until_complete(
                        self.enterprise_service.generate_response(
                            chat_id=chat_id_int,
                            user_message=user_message,
                            user_name=user_name,
                            market_data=real_market_data,
                            apply_visual_style=True
                        )
                    )
                
                # Extraer respuesta del resultado (V6.5.4 Premium: con indicador de búsqueda)
                if result and 'response' in result:
                    response_text = result['response']
                    
                    if result.get('web_search_used'):
                        web_indicator = "\n\n🔍 *Real-time verified information*"
                        if "verified information" not in response_text.lower():
                            response_text = response_text + web_indicator
                        logger.info(f"🔍 Web search used for this response (query: {result.get('web_search_query', 'N/A')[:50]})")
                    
                    # Apply post-processing filter to remove servile phrases
                    return post_process_response(response_text)
                else:
                    logger.error("❌ No response from enterprise service")
                    return self._fallback_response()
                    
            else:
                # Legacy fallback
                logger.warning("⚠️ Using legacy AI generation")
                return post_process_response(self._legacy_generate_response(user_message, user_name, chat_id, user_id, trading_system))
                
        except RateLimitExceeded as e:
            logger.warning(f"⚠️ Rate limit exceeded: {e}")
            return "⏳ Rate limit reached. Please wait a moment..."
        except Exception as e:
            logger.error(f"❌ Error generating response: {e}", exc_info=True)
            return self._fallback_response()
    
    async def _fetch_real_market_data_async(self, trading_system, user_message: str, user_id: Optional[str] = None) -> dict:
        """
        📊 ASYNC VERSION - Obtener datos de mercado en PARALELO para reducir latencia.
        
        FIX Jan 19, 2026: Versión async que ejecuta todas las llamadas HTTP/DB en paralelo
        usando asyncio.gather(). Reduce latencia de ~20s a ~3-5s.
        
        FEATURE PARITY: Mantiene toda la funcionalidad del método sync:
        - Detección de criptos específicas (Solana, Cardano, etc.)
        - Kraken autenticado cuando disponible
        - Trading mode REAL/PAPER detection
        """
        import aiohttp
        import re
        from omnix_services.market_data.kraken_data import fetch_crypto_price, CRYPTO_MAPPING
        
        market_data = {}
        message_lower = user_message.lower()
        
        logger.info("🔍 [ASYNC] MARKET DATA: Iniciando obtención paralela de datos...")
        start_time = asyncio.get_event_loop().time()
        
        detected_crypto = None
        for crypto_name in CRYPTO_MAPPING.keys():
            if crypto_name in message_lower:
                detected_crypto = crypto_name
                break
        
        async def fetch_specific_crypto():
            """Fetch specific crypto price if detected in message"""
            if not detected_crypto or detected_crypto in ['btc', 'bitcoin']:
                return None
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, fetch_crypto_price, detected_crypto)
        
        async def fetch_kraken_auth():
            """Try authenticated Kraken API first (faster, more reliable)"""
            if not trading_system or not hasattr(trading_system, 'kraken_client'):
                return None
            try:
                loop = asyncio.get_event_loop()
                def _fetch():
                    btc_ticker = trading_system.kraken_client.client.fetch_ticker('BTC/USD')
                    if btc_ticker and 'last' in btc_ticker and btc_ticker['last']:
                        return {
                            'btc_price': float(btc_ticker['last']),
                            'btc_24h_high': float(btc_ticker.get('high', 0) or 0),
                            'btc_24h_low': float(btc_ticker.get('low', 0) or 0),
                            'btc_volume': float(btc_ticker.get('baseVolume', 0) or 0),
                            'data_source': 'Kraken'
                        }
                    return None
                return await asyncio.wait_for(loop.run_in_executor(None, _fetch), timeout=5.0)
            except Exception as e:
                logger.warning(f"⚠️ [ASYNC] Kraken AUTH failed: {e}")
            return None
        
        async def fetch_kraken_public():
            """Fetch BTC price from Kraken public API"""
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        'https://api.kraken.com/0/public/Ticker?pair=XBTUSD',
                        timeout=aiohttp.ClientTimeout(total=5),
                        headers={'User-Agent': 'OMNIX/6.0'}
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if not data.get('error') and 'result' in data:
                                result = data['result']
                                ticker_key = 'XXBTZUSD' if 'XXBTZUSD' in result else list(result.keys())[0] if result else None
                                if ticker_key and 'c' in result[ticker_key]:
                                    ticker = result[ticker_key]
                                    return {
                                        'btc_price': float(ticker['c'][0]),
                                        'btc_24h_high': float(ticker['h'][0]) if ticker.get('h') else 0,
                                        'btc_24h_low': float(ticker['l'][0]) if ticker.get('l') else 0,
                                        'btc_volume': float(ticker['v'][1]) if ticker.get('v') and len(ticker['v']) > 1 else 0,
                                        'data_source': 'Kraken'
                                    }
            except Exception as e:
                logger.warning(f"⚠️ [ASYNC] Kraken PUBLIC failed: {e}")
            return None
        
        async def fetch_coingecko_backup():
            """Fetch BTC price from CoinGecko as backup"""
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_high=true&include_24hr_low=true',
                        timeout=aiohttp.ClientTimeout(total=5),
                        headers={'User-Agent': 'OMNIX/6.0'}
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if 'bitcoin' in data and 'usd' in data['bitcoin']:
                                return {
                                    'btc_price': float(data['bitcoin']['usd']),
                                    'btc_24h_high': float(data['bitcoin'].get('usd_24h_high', 0) or 0),
                                    'btc_24h_low': float(data['bitcoin'].get('usd_24h_low', 0) or 0),
                                    'data_source': 'CoinGecko'
                                }
            except Exception as e:
                logger.warning(f"⚠️ [ASYNC] CoinGecko failed: {e}")
            return None
        
        async def fetch_trade_performance():
            """Fetch trade performance data from PostgreSQL (runs in thread pool)"""
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._fetch_trade_performance, user_message, user_id)
        
        async def fetch_veto_data():
            """Fetch veto data from PostgreSQL (runs in thread pool)"""
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._fetch_veto_data, user_message)
        
        async def fetch_investor_data():
            """Fetch investor data from PostgreSQL (runs in thread pool)"""
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._fetch_investor_data, user_message)
        
        results = await asyncio.gather(
            fetch_specific_crypto(),
            fetch_kraken_auth(),
            fetch_kraken_public(),
            fetch_coingecko_backup(),
            fetch_trade_performance(),
            fetch_veto_data(),
            fetch_investor_data(),
            return_exceptions=True
        )
        
        crypto_result, kraken_auth_result, kraken_public_result, coingecko_result, trade_result, veto_result, investor_result = results
        
        if detected_crypto and detected_crypto not in ['btc', 'bitcoin']:
            if crypto_result and not isinstance(crypto_result, Exception) and crypto_result.get('success'):
                market_data['requested_crypto'] = {
                    'symbol': crypto_result['symbol'],
                    'name': detected_crypto.title(),
                    'price': crypto_result['price'],
                    'change_24h': crypto_result.get('change_24h', 0),
                    'high_24h': crypto_result.get('high_24h'),
                    'low_24h': crypto_result.get('low_24h'),
                    'volume': crypto_result.get('volume'),
                    'source': crypto_result.get('source', 'Kraken')
                }
                logger.info(f"✅ [ASYNC] {crypto_result['symbol']}: ${crypto_result['price']:,.4f}")
            else:
                error_msg = crypto_result.get('error', 'Precio no disponible') if isinstance(crypto_result, dict) else 'Precio no disponible'
                market_data['crypto_error'] = error_msg
                logger.warning(f"⚠️ [ASYNC] Crypto {detected_crypto} fetch failed: {error_msg}")
        
        btc_obtained = False
        if kraken_auth_result and not isinstance(kraken_auth_result, Exception) and isinstance(kraken_auth_result, dict):
            market_data.update(kraken_auth_result)
            btc_obtained = True
            logger.info(f"✅ [ASYNC] Kraken AUTH: ${market_data['btc_price']:,.2f}")
        elif kraken_public_result and not isinstance(kraken_public_result, Exception) and isinstance(kraken_public_result, dict):
            market_data.update(kraken_public_result)
            btc_obtained = True
            logger.info(f"✅ [ASYNC] Kraken PUBLIC: ${market_data['btc_price']:,.2f}")
        elif coingecko_result and not isinstance(coingecko_result, Exception) and isinstance(coingecko_result, dict):
            market_data.update(coingecko_result)
            btc_obtained = True
            logger.info(f"✅ [ASYNC] CoinGecko fallback: ${market_data['btc_price']:,.2f}")
        
        if not btc_obtained:
            market_data['market_data_unavailable'] = True
            market_data['market_data_warning'] = "Market data temporarily unavailable"
            logger.error("❌ [ASYNC] All price sources failed")
        
        if trade_result and not isinstance(trade_result, Exception):
            market_data['trade_performance'] = trade_result
        
        if veto_result and not isinstance(veto_result, Exception):
            market_data['veto_data'] = veto_result
        
        if investor_result and not isinstance(investor_result, Exception):
            market_data['investor_data'] = investor_result
        
        try:
            if trading_system and hasattr(trading_system, 'paper_balance'):
                market_data['paper_balance_usd'] = trading_system.paper_balance
                market_data['trading_mode'] = 'PAPER'
            elif trading_system and hasattr(trading_system, 'real_trading_enabled'):
                market_data['trading_mode'] = 'REAL' if trading_system.real_trading_enabled else 'PAPER'
        except:
            pass
        
        leverage_match = re.search(r'(\d+)\s*x|leverage\s*(\d+)|apalancamiento\s*(\d+)', message_lower)
        if leverage_match:
            leverage_value = int(leverage_match.group(1) or leverage_match.group(2) or leverage_match.group(3))
            market_data['requested_leverage'] = leverage_value
            if leverage_value > 5:
                market_data['leverage_warning'] = f"⛔ APALANCAMIENTO {leverage_value}x RECHAZADO - Máximo permitido: 5x (política de riesgo institucional)"
                logger.warning(f"⚠️ [ASYNC] Leverage {leverage_value}x solicitado - EXCEDE LÍMITE 5x")
        
        elapsed = asyncio.get_event_loop().time() - start_time
        logger.info(f"✅ [ASYNC] Market data fetched in {elapsed:.2f}s (parallel execution)")
        
        return market_data
    
    def _fetch_real_market_data(self, trading_system, user_message: str, user_id: Optional[str] = None) -> dict:
        """
        📊 OBTENER DATOS REALES DE MERCADO - SISTEMA MULTI-CRIPTO V6.1
        
        FIX Nov 29, 2025: Soporte para 50+ criptomonedas (Cardano, Solana, XRP, etc.)
        FIX Dec 10, 2025: Acepta user_id para obtener datos de trading específicos del usuario.
        """
        import re
        import requests
        from omnix_services.market_data.kraken_data import fetch_crypto_price, normalize_crypto_name, CRYPTO_MAPPING
        
        market_data = {}
        btc_obtained = False
        logger.info("🔍 MARKET DATA: Iniciando obtención de datos...")
        
        # ═══════════════════════════════════════════════════════════════════
        # DETECCIÓN DE CRIPTO ESPECÍFICA EN EL MENSAJE
        # ═══════════════════════════════════════════════════════════════════
        detected_crypto = None
        message_lower = user_message.lower()
        
        # Buscar nombres de criptomonedas en el mensaje
        for crypto_name in CRYPTO_MAPPING.keys():
            if crypto_name in message_lower:
                detected_crypto = crypto_name
                break
        
        # Si detectamos una cripto específica (no BTC), obtener su precio
        if detected_crypto and detected_crypto not in ['btc', 'bitcoin']:
            logger.info(f"🔍 Cripto detectada: {detected_crypto}")
            crypto_data = fetch_crypto_price(detected_crypto)
            
            if crypto_data.get('success'):
                market_data['requested_crypto'] = {
                    'symbol': crypto_data['symbol'],
                    'name': detected_crypto.title(),
                    'price': crypto_data['price'],
                    'change_24h': crypto_data.get('change_24h', 0),
                    'high_24h': crypto_data.get('high_24h'),
                    'low_24h': crypto_data.get('low_24h'),
                    'volume': crypto_data.get('volume'),
                    'source': crypto_data.get('source', 'Kraken')
                }
                logger.info(f"✅ {crypto_data['symbol']}: ${crypto_data['price']:,.4f}")
            else:
                market_data['crypto_error'] = crypto_data.get('error', 'Precio no disponible')
        
        # 🚨 VALIDACIÓN DE APALANCAMIENTO (máximo 5x permitido)
        leverage_match = re.search(r'(\d+)\s*x|leverage\s*(\d+)|apalancamiento\s*(\d+)', user_message.lower())
        if leverage_match:
            leverage_value = int(leverage_match.group(1) or leverage_match.group(2) or leverage_match.group(3))
            market_data['requested_leverage'] = leverage_value
            if leverage_value > 5:
                market_data['leverage_warning'] = f"⛔ APALANCAMIENTO {leverage_value}x RECHAZADO - Máximo permitido: 5x (política de riesgo institucional)"
                logger.warning(f"⚠️ Leverage {leverage_value}x solicitado - EXCEDE LÍMITE 5x")
        
        # ═══════════════════════════════════════════════════════════════════
        # FUENTE 1: API AUTENTICADA DE KRAKEN
        # ═══════════════════════════════════════════════════════════════════
        if not btc_obtained and trading_system and hasattr(trading_system, 'kraken_client'):
            try:
                logger.info("📡 [1/3] Kraken AUTH...")
                btc_ticker = trading_system.kraken_client.client.fetch_ticker('BTC/USD')
                if btc_ticker and 'last' in btc_ticker and btc_ticker['last']:
                    market_data['btc_price'] = float(btc_ticker['last'])
                    market_data['btc_24h_high'] = float(btc_ticker.get('high', 0) or 0)
                    market_data['btc_24h_low'] = float(btc_ticker.get('low', 0) or 0)
                    market_data['btc_volume'] = float(btc_ticker.get('baseVolume', 0) or 0)
                    market_data['data_source'] = 'Kraken'
                    btc_obtained = True
                    logger.info(f"✅ KRAKEN AUTH: ${market_data['btc_price']:,.0f}")
            except Exception as e:
                logger.warning(f"⚠️ Kraken AUTH falló: {e}")
        
        # ═══════════════════════════════════════════════════════════════════
        # FUENTE 2: API PÚBLICA DE KRAKEN (MÉTODO PRINCIPAL)
        # ═══════════════════════════════════════════════════════════════════
        if not btc_obtained:
            try:
                logger.info("📡 [2/3] Kraken PUBLIC API...")
                resp = requests.get(
                    'https://api.kraken.com/0/public/Ticker?pair=XBTUSD',
                    timeout=10,
                    headers={'User-Agent': 'OMNIX/6.0'}
                )
                logger.info(f"📡 Kraken response status: {resp.status_code}")
                
                if resp.status_code == 200:
                    data = resp.json()
                    logger.info(f"📡 Kraken raw keys: {list(data.keys()) if data else 'None'}")
                    
                    # VALIDACIÓN MEJORADA: not error (más robusta que == [])
                    has_no_error = not data.get('error')
                    has_result = 'result' in data and data['result']
                    
                    if has_no_error and has_result:
                        result = data['result']
                        logger.info(f"📡 Kraken result keys: {list(result.keys())}")
                        
                        # Buscar XXBTZUSD o cualquier clave disponible
                        ticker_key = None
                        if 'XXBTZUSD' in result:
                            ticker_key = 'XXBTZUSD'
                        elif result:
                            ticker_key = list(result.keys())[0]
                        
                        if ticker_key:
                            ticker = result[ticker_key]
                            logger.info(f"📡 Ticker data: c={ticker.get('c')}, h={ticker.get('h')}, l={ticker.get('l')}")
                            
                            if 'c' in ticker and ticker['c'] and len(ticker['c']) > 0:
                                market_data['btc_price'] = float(ticker['c'][0])
                                market_data['btc_24h_high'] = float(ticker['h'][0]) if ticker.get('h') else 0
                                market_data['btc_24h_low'] = float(ticker['l'][0]) if ticker.get('l') else 0
                                market_data['btc_volume'] = float(ticker['v'][1]) if ticker.get('v') and len(ticker['v']) > 1 else 0
                                market_data['data_source'] = 'Kraken'
                                btc_obtained = True
                                logger.info(f"✅ KRAKEN PUBLIC SUCCESS: ${market_data['btc_price']:,.2f}")
                            else:
                                logger.warning(f"⚠️ Kraken: ticker['c'] inválido: {ticker.get('c')}")
                        else:
                            logger.warning(f"⚠️ Kraken: No ticker key found in result")
                    else:
                        logger.warning(f"⚠️ Kraken error: has_no_error={has_no_error}, has_result={has_result}, error={data.get('error')}")
                else:
                    logger.warning(f"⚠️ Kraken HTTP error: {resp.status_code}")
            except Exception as e:
                logger.warning(f"⚠️ Kraken PUBLIC falló: {type(e).__name__}: {e}")
        
        # ═══════════════════════════════════════════════════════════════════
        # FUENTE 3: COINGECKO BACKUP
        # ═══════════════════════════════════════════════════════════════════
        if not btc_obtained:
            try:
                logger.info("📡 [3/3] CoinGecko BACKUP...")
                resp = requests.get(
                    'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_high=true&include_24hr_low=true',
                    timeout=10,
                    headers={'User-Agent': 'OMNIX/6.0'}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if 'bitcoin' in data and 'usd' in data['bitcoin']:
                        market_data['btc_price'] = float(data['bitcoin']['usd'])
                        market_data['btc_24h_high'] = float(data['bitcoin'].get('usd_24h_high', 0) or 0)
                        market_data['btc_24h_low'] = float(data['bitcoin'].get('usd_24h_low', 0) or 0)
                        market_data['data_source'] = 'CoinGecko'
                        btc_obtained = True
                        logger.info(f"✅ COINGECKO: ${market_data['btc_price']:,.0f}")
                else:
                    logger.warning(f"⚠️ CoinGecko HTTP {resp.status_code}")
            except Exception as e:
                logger.warning(f"⚠️ CoinGecko falló: {e}")
        
        # ═══════════════════════════════════════════════════════════════════
        # RESULTADO FINAL
        # ═══════════════════════════════════════════════════════════════════
        if btc_obtained:
            logger.info(f"✅ BTC PRICE OBTAINED: ${market_data['btc_price']:,.0f} via {market_data.get('data_source', 'Unknown')}")
        else:
            market_data['market_data_unavailable'] = True
            market_data['market_data_warning'] = "Market data temporarily unavailable"
            logger.error("❌ ALL SOURCES FAILED - No BTC price")
        
        # 💰 PAPER TRADING BALANCE (si está disponible)
        try:
            if trading_system and hasattr(trading_system, 'paper_balance'):
                market_data['paper_balance_usd'] = trading_system.paper_balance
                market_data['trading_mode'] = 'PAPER'
            elif trading_system and hasattr(trading_system, 'real_trading_enabled'):
                market_data['trading_mode'] = 'REAL' if trading_system.real_trading_enabled else 'PAPER'
        except:
            pass
        
        # 📊 FIX Dec 10, 2025: Obtener datos REALES de trading desde PostgreSQL
        # Esto evita que el AI invente datos de trades/balance/win rate
        # FIX Dec 10, 2025 v2: Ahora pasa user_id correctamente para soporte multi-usuario
        trade_performance = self._fetch_trade_performance(user_message, user_id=user_id)
        if trade_performance:
            market_data['trade_performance'] = trade_performance
            logger.info(f"📊 Trade performance data added: {trade_performance.get('statistics', {}).get('total_trades', 0)} trades")
        
        # 📊 FIX Jan 8, 2026: Obtener datos REALES de vetoes desde PostgreSQL
        # Esto evita que el AI invente datos de capital protegido para auditorías
        veto_data = self._fetch_veto_data(user_message)
        if veto_data:
            market_data['veto_data'] = veto_data
            logger.info(f"📊 Veto data added: has_data={veto_data.get('has_data', False)}, query_type={veto_data.get('query_type', 'unknown')}")
        
        # 📊 ADR-013 Jan 16, 2026: Obtener datos SQL reales para inversores
        # Cuando detecta preguntas de due diligence, incluye métricas segmentadas
        investor_data = self._fetch_investor_data(user_message)
        if investor_data:
            market_data['investor_data'] = investor_data
            logger.info(f"📊 Investor data added: segmented expectancy, fee breakdown, pre/post hotfix stats")
        
        return market_data
    
    def _fetch_trade_performance(self, user_message: str, user_id: Optional[str] = None) -> dict:
        """
        📊 FIX Dec 10, 2025: Obtener datos REALES de trading desde PostgreSQL.
        
        PROBLEMA: El AI estaba inventando datos de trades, win rate, P&L.
        SOLUCIÓN: Consultar PostgreSQL directamente via PaperTradingRepository.
        
        Args:
            user_message: Mensaje del usuario para detectar intención
            user_id: ID del usuario para filtrar datos (opcional, si None retorna datos globales)
        
        Solo se ejecuta si el usuario pregunta por:
        - Balance, saldo, fondos
        - Historial, trades, operaciones
        - Rendimiento, performance, win rate
        - Estadísticas, métricas
        """
        message_lower = user_message.lower()
        
        # Detectar si el usuario pregunta por datos de trading
        trade_keywords = [
            'balance', 'saldo', 'fondos', 'dinero', 'capital',
            'historial', 'trades', 'operaciones', 'history',
            'rendimiento', 'performance', 'win rate', 'winrate',
            'estadísticas', 'métricas', 'metrics', 'stats',
            'ganadores', 'perdedores', 'p&l', 'pnl', 'profit',
            'cuantos trades', 'cuántos trades', 'informe', 'report'
        ]
        
        needs_trade_data = any(keyword in message_lower for keyword in trade_keywords)
        
        if not needs_trade_data:
            return None
        
        logger.info(f"📊 Detected trade/performance query - fetching REAL data from PostgreSQL (user_id={user_id})")
        
        try:
            from omnix_services.database_service.paper_trading_repository import get_paper_trading_repository
            
            repo = get_paper_trading_repository()
            performance = repo.get_full_performance_context(user_id=user_id)
            
            if performance.get('has_real_data'):
                logger.info(f"✅ REAL trade data obtained from PostgreSQL")
            else:
                logger.info(f"📊 No trade data in PostgreSQL - will inform user honestly")
            
            return performance
            
        except ImportError as e:
            logger.error(f"❌ Cannot import PaperTradingRepository: {e}")
            return {
                'has_real_data': False,
                'error': 'Repository not available',
                'statistics': {'total_trades': 0, 'data_source': 'unavailable'}
            }
        except Exception as e:
            logger.error(f"❌ Error fetching trade performance: {e}")
            return {
                'has_real_data': False,
                'error': str(e),
                'statistics': {'total_trades': 0, 'data_source': 'error'}
            }
    
    def _fetch_veto_data(self, user_message: str) -> Optional[dict]:
        """
        📊 FIX Jan 8, 2026: Obtener datos REALES de vetoes desde PostgreSQL.
        
        PROBLEMA: El AI estaba inventando datos de capital protegido para períodos específicos.
        SOLUCIÓN: Consultar VetoRepository con el método get_vetoes_by_timerange().
        
        Detecta si el usuario pregunta por:
        - Auditoría, reporte de bloqueos
        - Capital protegido, vetoes
        - Períodos específicos (fechas)
        """
        import re
        message_lower = user_message.lower()
        
        veto_keywords = [
            'auditoría', 'auditoria', 'audit', 'bloqueos', 'bloqueo',
            'capital protegido', 'protected capital', 'veto', 'vetoes',
            'coherence gate', 'black swan', 'cuarentena', 'quarantine',
            'reporte de bloqueos', 'protección', 'protection'
        ]
        
        needs_veto_data = any(keyword in message_lower for keyword in veto_keywords)
        
        if not needs_veto_data:
            return None
        
        logger.info("📊 Detected veto/audit query - fetching REAL data from PostgreSQL")
        
        from datetime import datetime
        current_year = datetime.now().year
        
        range_pattern = r'(\d{1,2})[/](\d{1,2})(?:[/](\d{4}))?[^\d]*(?:al?|to|-)[\s]*(\d{1,2})[/](\d{1,2})(?:[/](\d{4}))?'
        range_match = re.search(range_pattern, user_message)
        
        dates_found = []
        if range_match:
            d1, m1, y1, d2, m2, y2 = range_match.groups()
            year1 = y1 if y1 else str(current_year)
            year2 = y2 if y2 else str(current_year)
            dates_found = [(d1, m1, year1), (d2, m2, year2)]
            logger.info(f"📊 Date range detected: {d1}/{m1}/{year1} to {d2}/{m2}/{year2}")
        else:
            date_with_year = r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})'
            dates_with_year = re.findall(date_with_year, user_message)
            if len(dates_with_year) >= 2:
                dates_found = dates_with_year[:2]
        
        try:
            from omnix_services.database_service.veto_repository import get_veto_repository
            
            repo = get_veto_repository()
            if not repo:
                return {
                    'has_data': False,
                    'error': 'VetoRepository not available',
                    'summary_48h': None,
                    'summary_7d': None
                }
            
            if len(dates_found) >= 2:
                start_date = f"{dates_found[0][2]}-{dates_found[0][1]:0>2}-{dates_found[0][0]:0>2}"
                end_date = f"{dates_found[1][2]}-{dates_found[1][1]:0>2}-{dates_found[1][0]:0>2}"
                
                timerange_data = repo.get_vetoes_by_timerange(start_date, end_date)
                
                logger.info(f"📊 Veto data for {start_date} to {end_date}: {timerange_data.get('total_count', 0)} vetoes")
                
                return {
                    'has_data': timerange_data.get('has_data', False),
                    'timerange': timerange_data,
                    'query_type': 'specific_period',
                    'source': 'postgresql'
                }
            else:
                summary_48h = repo.get_veto_summary(hours=48)
                summary_7d = repo.get_veto_summary(hours=168)
                all_time = repo.get_all_time_total()
                
                logger.info(f"📊 Veto summary: 48h={summary_48h.get('total_count', 0)}, 7d={summary_7d.get('total_count', 0)}, all_time=${all_time:,.2f}")
                
                return {
                    'has_data': summary_48h.get('total_count', 0) > 0 or summary_7d.get('total_count', 0) > 0,
                    'summary_48h': summary_48h,
                    'summary_7d': summary_7d,
                    'all_time_total': all_time,
                    'query_type': 'general',
                    'source': 'postgresql'
                }
                
        except ImportError as e:
            logger.error(f"❌ Cannot import VetoRepository: {e}")
            return {
                'has_data': False,
                'error': 'VetoRepository not available',
                'source': 'unavailable'
            }
        except Exception as e:
            logger.error(f"❌ Error fetching veto data: {e}")
            return {
                'has_data': False,
                'error': str(e),
                'source': 'error'
            }
    
    def _fetch_investor_data(self, user_message: str) -> Optional[dict]:
        """
        📊 ADR-013 Jan 16, 2026: Obtener datos SQL reales para respuestas a inversores.
        
        PROBLEMA: El AI no podía dar datos segmentados cuando inversores hacían due diligence.
        SOLUCIÓN: InvestorDataProvider con queries SQL reales.
        
        Se activa cuando detecta:
        - Preguntas de due diligence (family office, AUM, seed, etc.)
        - Preguntas sobre expectancy, fees, hotfix, segmentación
        - Múltiples preguntas numeradas (3+)
        
        Returns:
            Dict con datos formateados o None si no aplica
        """
        message_lower = user_message.lower()
        
        investor_indicators = [
            'family office', 'aum', 'seed', 'pre-money', 'post-money',
            'due diligence', 'inversor institucional', 'institutional investor',
            'valuación', 'valuation', 'equity', 'term sheet', 'hedge fund',
            'sharia', 'regulatory', 'compliance', 'jurisdicción',
            'expectancy', 'segmented', 'segmentada', 'por régimen', 'by regime',
            'coherence bucket', 'hmm regime', 'fee breakdown', 'fees analysis',
            'pre hotfix', 'post hotfix', 'calibration', 'adr-007',
            'walk-forward', 'backtest', 'statistical significance',
            'query sql', 'datos reales', 'real data', 'show me the data'
        ]
        
        import re
        numbered_pattern = r'(\d+[\.\)]\s*.*?){3,}'
        has_numbered_questions = bool(re.search(numbered_pattern, user_message, re.DOTALL))
        
        word_count = len(user_message.split())
        is_long_question = word_count >= 80
        
        needs_investor_data = (
            any(ind in message_lower for ind in investor_indicators) or
            has_numbered_questions or
            is_long_question
        )
        
        if not needs_investor_data:
            return None
        
        logger.info("📊 Detected investor/due diligence query - fetching REAL segmented data from PostgreSQL")
        
        try:
            from omnix_services.ai_service.providers.investor_data_provider import get_investor_data_for_ai, get_formatted_investor_data
            
            data = get_investor_data_for_ai()
            
            if data.get('success'):
                formatted = get_formatted_investor_data()
                data['formatted_for_prompt'] = formatted
                logger.info("✅ Investor data obtained from PostgreSQL (segmented expectancy, fees, hotfix stats)")
            else:
                logger.warning(f"⚠️ Investor data fetch failed: {data.get('error')}")
            
            return data
            
        except ImportError as e:
            logger.error(f"❌ Cannot import InvestorDataProvider: {e}")
            return {
                'success': False,
                'error': 'InvestorDataProvider not available',
                'formatted_for_prompt': '[Investor metrics temporarily unavailable]'
            }
        except Exception as e:
            logger.error(f"❌ Error fetching investor data: {e}")
            return {
                'success': False,
                'error': str(e),
                'formatted_for_prompt': f'[Error loading investor data: {str(e)}]'
            }
    
    def _legacy_generate_response(self, user_message, user_name, chat_id, user_id, trading_system=None):
        """Legacy AI generation - GEMINI PRIMERO con CONSULTA KRAKEN REAL
        FIX Nov 29, 2025: Usar trading_system parámetro en lugar de global
        """
        # Context para continuidad de conversación
        context = ""
        if chat_id in self.conversation_history:
            context = "\n".join(self.conversation_history[chat_id][-6:])
        
        # HAROLD FIX: DETECTAR SI PREGUNTA POR BALANCE Y CONSULTAR KRAKEN EN TIEMPO REAL
        palabras_balance = ['balance', 'saldo', 'fondos', 'dinero', 'cuanto tengo', 'cuánto tengo', 'mi cuenta', 'capital']
        pregunta_balance = any(palabra in user_message.lower() for palabra in palabras_balance)
        
        kraken_info = ""
        balance_consultado = False
        
        try:
            if trading_system:
                if hasattr(trading_system, 'kraken') and trading_system.kraken:
                    if hasattr(trading_system, 'real_trading_enabled') and trading_system.real_trading_enabled:
                        can_view_real_balance = False
                        if AUTHORIZATION_AVAILABLE and get_authorization_adapter:
                            auth = get_authorization_adapter()
                            can_view_real_balance = auth.has_permission(str(user_id), Permission.VIEW_REAL_BALANCE)
                        else:
                            try:
                                from omnix_config.settings import settings
                                can_view_real_balance = str(user_id) == str(settings.TELEGRAM_ADMIN_ID)
                            except ImportError:
                                can_view_real_balance = str(user_id) == "7014748854"
                        
                        if pregunta_balance or can_view_real_balance:
                            try:
                                logger.info(f"💰 CONSULTANDO KRAKEN EN TIEMPO REAL para: {user_message[:50]}")
                                balance = trading_system.kraken.fetch_balance()
                                
                                # VERIFICAR QUE BALANCE NO SEA NONE
                                if not balance:
                                    raise Exception("fetch_balance() devolvió None")
                                
                                usd_free = balance.get('USD', {}).get('free', 0) if balance else 0
                                usd_total = balance.get('USD', {}).get('total', 0) if balance else 0
                                btc_free = balance.get('BTC', {}).get('free', 0) if balance else 0
                                btc_total = balance.get('BTC', {}).get('total', 0) if balance else 0
                                eth_free = balance.get('ETH', {}).get('free', 0) if balance else 0
                                eth_total = balance.get('ETH', {}).get('total', 0) if balance else 0
                                
                                balance_consultado = True
                                logger.info(f"✅ BALANCE OBTENIDO: USD=${usd_total:.2f}, BTC={btc_total:.8f}, ETH={eth_total:.6f}")
                                
                                # HAROLD FIX: Info detallada para la IA (PRIVADO - no se muestra al usuario)
                                # La IA conoce el balance exacto pero NO lo menciona automáticamente
                                kraken_info = f"\n\n🔗 KRAKEN CONECTADO (Actualizado {datetime.now().strftime('%H:%M:%S')}):\n"
                                
                                if usd_total > 0:
                                    kraken_info += f"- Balance USD: ${usd_free:,.2f} disponible / ${usd_total:,.2f} total\n"
                                if btc_total > 0:
                                    kraken_info += f"- Balance BTC: {btc_free:.8f} disponible / {btc_total:.8f} total\n"
                                if eth_total > 0:
                                    kraken_info += f"- Balance ETH: {eth_free:.6f} disponible / {eth_total:.6f} total\n"
                                
                                # Agregar otras monedas si existen
                                other_balances = []
                                for currency, data in balance.items():
                                    if currency not in ['USD', 'BTC', 'ETH', 'free', 'used', 'total', 'info']:
                                        # HAROLD FIX: Validar que data sea dict antes de .get()
                                        if isinstance(data, dict):
                                            total = data.get('total', 0)
                                            if total > 0:
                                                other_balances.append(f"{currency}: {total}")
                                
                                if other_balances:
                                    kraken_info += f"- Otras monedas: {', '.join(other_balances)}\n"
                                
                                kraken_info += "- Trading REAL activado\n"
                                kraken_info += "- API funcionando correctamente\n\n"
                                kraken_info += "INSTRUCCIÓN: Solo menciona balance si Harold pregunta específicamente por él. No lo menciones en respuestas generales."
                                
                            except Exception as balance_error:
                                logger.error(f"❌ Error consultando Kraken: {balance_error}")
                                kraken_info = "\n\n⚠️ KRAKEN: Temporary error fetching balance - Retrying..."
                        else:
                            kraken_info = "\n\n🔗 KRAKEN: Connected and ready"
                    else:
                        kraken_info = "\n\n⚠️ KRAKEN: API connected but trading not yet activated"
                else:
                    kraken_info = "\n\n⚠️ KRAKEN: Not connected - verify API credentials"
        except Exception as e:
            logger.error(f"❌ Error crítico verificando Kraken: {e}")
            kraken_info = "\n\n⚠️ KRAKEN: System temporarily unavailable"
        
        # V6.5.4d: AI-First Multilingual System Prompt
        from omnix_services.ai_service.prompt_templates import prompt_builder
        
        kraken_status = {
            'connected': bool(kraken_info and 'Conectado' in kraken_info or 'Connected' in kraken_info),
            'trading_enabled': bool(kraken_info and 'Trading' in kraken_info),
            'balance': None
        }
        
        system_prompt = prompt_builder.build_system_prompt(
            user_message=user_message,
            user_name=user_name,
            context=context,
            kraken_status=kraken_status if kraken_info else None,
            intent='general'
        )
        
        # PRIORIDAD 1: GEMINI (key válida en Railway)
        if hasattr(self, 'gemini_client') and self.gemini_client:
            try:
                logger.info("✅ Usando GEMINI en modo legacy")
                
                # Detectar SDK (nuevo vs clásico)
                if hasattr(self.gemini_client, 'models'):
                    # Nuevo SDK (google.genai.Client)
                    response = self.gemini_client.models.generate_content(
                        model='gemini-2.0-flash-exp',
                        contents=system_prompt
                    )
                    response_text = response.text
                else:
                    # SDK clásico (google.generativeai)
                    response = self.gemini_client.generate_content(system_prompt)
                    response_text = response.text
                
                # Guardar en historial
                if chat_id not in self.conversation_history:
                    self.conversation_history[chat_id] = []
                self.conversation_history[chat_id].append(f"Usuario: {user_message}")
                self.conversation_history[chat_id].append(f"OMNIX: {response_text}")
                if len(self.conversation_history[chat_id]) > 20:
                    self.conversation_history[chat_id] = self.conversation_history[chat_id][-20:]
                
                logger.info(f"✅ GEMINI respuesta exitosa: {len(response_text)} chars")
                return response_text
                
            except Exception as e:
                logger.warning(f"⚠️ Gemini falló: {e}, intentando GPT-4 fallback")
        
        # PRIORIDAD 2: GPT-4 fallback (solo si Gemini falla)
        if hasattr(self, 'openai_client') and self.openai_client:
            try:
                logger.info("⚠️ Usando GPT-4 fallback")
                
                user_content = f"Contexto: {context}\n\n{user_name}: {user_message}" if context else f"{user_name}: {user_message}"
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt.split("Contexto previo:")[0].strip()},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=0.7,
                    max_tokens=4000
                )
                
                response_text = response.choices[0].message.content
                logger.info(f"✅ GPT-4 respuesta exitosa: {len(response_text)} chars")
                return response_text
                
            except Exception as e:
                logger.error(f"❌ GPT-4 también falló: {e}")
        
        # FALLBACK FINAL: Mensaje estático
        logger.error("❌ Todas las IAs fallaron, usando respuesta estática")
        return self._fallback_response()
    
    def _fallback_response(self):
        """Ultimate fallback if all AI fails"""
        return "🤖 System temporarily unavailable. Please try again in a few moments."
    
    # Compatibility methods - delegate to enterprise or provide simple fallbacks
    def apply_ultra_visual_style(self, response_text, intent='general'):
        """Apply visual styling to response"""
        if self.using_enterprise:
            return self.enterprise_service.styles.apply_visual_enhancements(response_text, intent)
        else:
            # Simple emoji addition
            return f"🤖 {response_text}"
    
    def analyze_intent(self, message):
        """Analyze user intent"""
        if self.using_enterprise:
            return self.enterprise_service.prompts.detect_intent(message)
        else:
            return 'general'
