"""
OMNIX V6.0 ULTRA - Conversational AI Adapter
Adapter class que mantiene compatibilidad con código legacy
pero usa ConversationalAIService enterprise internamente
"""

import logging
import os
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

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
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


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
                # Inicializar OpenAI
                if OPENAI_AVAILABLE and os.environ.get('OPENAI_API_KEY'):
                    self.openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
                    logger.info("✅ OpenAI GPT-4o inicializado correctamente")
                
                # Inicializar Gemini (soporta AMBOS SDKs)
                if GEMINI_AVAILABLE and os.environ.get('GEMINI_API_KEY'):
                    if hasattr(genai, 'Client'):
                        # Nuevo SDK (google.genai)
                        self.gemini_client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
                        logger.info("✅ Gemini 2.0 Flash inicializado con SDK moderno")
                    else:
                        # SDK Clásico (google.generativeai)
                        genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
                        self.gemini_client = genai.GenerativeModel('gemini-2.0-flash-exp')
                        logger.info("✅ Gemini 2.0 Flash inicializado correctamente")
            except Exception as e:
                logger.error(f"Error initializing legacy AI clients: {e}")
    
    def generate_response(self, user_message, user_name="Usuario", chat_id="", user_id=None, trading_system=None):
        """
        🚀 ENTERPRISE-GRADE RESPONSE GENERATION
        
        Mantiene compatibilidad con firma vieja pero usa sistema enterprise modular
        FIX Nov 28, 2025: Ahora pasa DATOS REALES de Kraken al AI
        """
        try:
            if self.using_enterprise:
                # 🔥 USO DEL NUEVO SISTEMA ENTERPRISE
                logger.info(f"🚀 Generando respuesta ENTERPRISE para {user_name}")
                
                # Convertir chat_id a int si es string
                chat_id_int = int(chat_id) if chat_id else (user_id if user_id else 0)
                
                # 📊 FIX: OBTENER DATOS REALES DE KRAKEN ANTES DE GENERAR RESPUESTA
                real_market_data = self._fetch_real_market_data(trading_system, user_message)
                
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
                
                # Extraer respuesta del resultado
                if result and 'response' in result:
                    return result['response']
                else:
                    logger.error("❌ No response from enterprise service")
                    return self._fallback_response()
                    
            else:
                # Legacy fallback
                logger.warning("⚠️ Using legacy AI generation")
                return self._legacy_generate_response(user_message, user_name, chat_id, user_id)
                
        except RateLimitExceeded as e:
            logger.warning(f"⚠️ Rate limit exceeded: {e}")
            return "⚠️ Has alcanzado el límite de mensajes por minuto. Por favor espera un momento."
        except Exception as e:
            logger.error(f"❌ Error generating response: {e}", exc_info=True)
            return self._fallback_response()
    
    def _fetch_real_market_data(self, trading_system, user_message: str) -> dict:
        """
        📊 OBTENER DATOS REALES DE MERCADO - SISTEMA MULTI-CRIPTO V6.1
        
        FIX Nov 29, 2025: Soporte para 50+ criptomonedas (Cardano, Solana, XRP, etc.)
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
            market_data['market_data_warning'] = "Datos de mercado temporalmente no disponibles"
            logger.error("❌ TODAS LAS FUENTES FALLARON - Sin precio BTC")
        
        # 💰 PAPER TRADING BALANCE (si está disponible)
        try:
            if trading_system and hasattr(trading_system, 'paper_balance'):
                market_data['paper_balance_usd'] = trading_system.paper_balance
                market_data['trading_mode'] = 'PAPER'
            elif trading_system and hasattr(trading_system, 'real_trading_enabled'):
                market_data['trading_mode'] = 'REAL' if trading_system.real_trading_enabled else 'PAPER'
        except:
            pass
        
        return market_data
    
    def _legacy_generate_response(self, user_message, user_name, chat_id, user_id):
        """Legacy AI generation - GEMINI PRIMERO con CONSULTA KRAKEN REAL"""
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
            if 'global_trading_system' in globals() and global_trading_system:
                if hasattr(global_trading_system, 'kraken') and global_trading_system.kraken:
                    if hasattr(global_trading_system, 'real_trading_enabled') and global_trading_system.real_trading_enabled:
                        # SI PREGUNTA POR BALANCE O ES HAROLD, CONSULTAR KRAKEN AHORA
                        if pregunta_balance or str(user_id) == "7014748854":
                            try:
                                logger.info(f"💰 CONSULTANDO KRAKEN EN TIEMPO REAL para: {user_message[:50]}")
                                balance = global_trading_system.kraken.fetch_balance()
                                
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
                                kraken_info = "\n\n⚠️ KRAKEN: Error temporal consultando balance - Reintentando..."
                        else:
                            # No preguntó por balance, solo indicar que está conectado
                            kraken_info = "\n\n🔗 KRAKEN: Conectado y listo (consulta disponible cuando necesites)"
                    else:
                        kraken_info = "\n\n⚠️ KRAKEN: API conectada pero trading no activado aún"
                else:
                    kraken_info = "\n\n⚠️ KRAKEN: No conectado - verificar credenciales API"
        except Exception as e:
            logger.error(f"❌ Error crítico verificando Kraken: {e}")
            kraken_info = "\n\n⚠️ KRAKEN: Sistema temporalmente no disponible"
        
        # System prompt compacto V5.2 CON INFO KRAKEN
        system_prompt = f"""Eres OMNIX V5.2 QUANTUM ULTIMATE, asistente de trading automatizado creado por Harold Nunes.

Capacidades Core:
- Post-Quantum Cryptography (Kyber-768, Dilithium-3) para seguridad institucional
- Monte Carlo Simulator (10K simulaciones), Black Swan Detector, Kelly Criterion
- HMM Regime Detector, Dual Kalman Filter, OMNIX Quantum Momentum
- **Adaptive Weight System ω(t)**: Pesos dinámicos Kalman/Monte Carlo basados en Hurst Exponent H(t) y α-stable tail index - Sistema REAL implementado en adaptive_weight_system.py
- Real Trading con Kraken API (trades reales, NO simulados)
- Sharia Compliance, Voice bidirectional, Multi-language
- WebSocket real-time, Backtesting profesional, Smart Alerts 24/7{kraken_info}

Personalidad:
- Inteligente e independiente, menciona capacidades según contexto
- Respuestas naturales pero profundas para impresionar inversores
- SIEMPRE en español con Harold (user {user_id})

Contexto previo: {context}

Usuario {user_name}: {user_message}"""
        
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
        return "🤖 Sistema temporalmente no disponible. Por favor intenta de nuevo en unos momentos."
    
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
