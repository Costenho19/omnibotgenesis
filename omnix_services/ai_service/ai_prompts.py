"""
OMNIX V6.0 ENTERPRISE - Prompts & Context Manager
Intent Analysis, Context Building, Prompt Engineering
Escalabilidad: 50K+ usuarios con context caching
+ Quantum Physics Validator for verified scientific responses
"""

# 🔥 RAILWAY DEBUG - Archivo actualizado para forzar recarga
print("✅ ai_prompts.py V6.0 CARGADO - CON QUANTUM PHYSICS VALIDATOR")

from datetime import datetime
from typing import Dict, List, Optional, Any
from omnix_core.cache.redis_cache import cache
from omnix_core.utils.logger import get_logger

logger = get_logger(__name__)

# Import quantum physics validator for scientific accuracy
try:
    from omnix_core.quantum.physics_validator import get_quantum_physics_context, quantum_physics_validator
    QUANTUM_PHYSICS_VALIDATOR_AVAILABLE = True
    logger.info("⚛️ Quantum Physics Validator LOADED - Scientific accuracy enabled")
except ImportError as e:
    QUANTUM_PHYSICS_VALIDATOR_AVAILABLE = False
    get_quantum_physics_context = None
    quantum_physics_validator = None
    logger.warning(f"⚠️ Quantum Physics Validator not available: {e}")


class PromptsContextManager:
    """Enterprise Prompts and Context Management"""
    
    def __init__(self):
        """Initialize prompts and context system"""
        
        # 🚀 CARACTERÍSTICAS COMPETITIVAS OMNIX
        self.competitive_advantages = {
            '🔐 Enterprise Security': 'Advanced encryption and protection',
            '🎤 Voice Bidirectional': 'Speech-to-Text + Text-to-Speech real',
            '☪️ Sharia Compliant': 'Automated Islamic finance validation',
            '🌍 10 Languages': 'Multilingual with cultural context',
            '💰 Real Trading': 'Kraken API live trading execution',
            '📈 Advanced Analytics': 'Mathematical optimization algorithms',
            '🧠 Emotional AI': 'Advanced sentiment & psychology',
            '🎨 Visual Interface': 'Rich emoji conversation experience',
            '📊 Enterprise Analytics': 'Automated reports every 15 minutes',
            '🔄 Real-time Learning': 'Continuous self-improvement'
        }
        
        # 📋 COMANDOS DE TRADING
        self.trading_commands = {
            'buy': ['buy', 'comprar', 'compra', '/buy', '/comprar'],
            'sell': ['sell', 'vender', 'venta', '/sell', '/vender'],
            'status': ['status', 'estado', '/status', '/estado'],
            'balance': ['balance', 'saldo', '/balance', '/saldo']
        }
        
        # 🌍 TÉRMINOS MULTILINGÜES
        self.spanish_trading_terms = [
            'trading', 'análisis', 'criptomonedas', 'bitcoin', 'precio', 'mercado',
            'comprar', 'vender', 'estrategia', 'riesgo', 'ganancia', 'pérdida',
            'tendencia', 'volumen', 'liquidez', 'volatilidad', 'soporte', 'resistencia'
        ]
    
    def detect_emotional_tone(self, message: str) -> str:
        """
        Detect emotional tone and conversation style
        
        Returns: 'casual', 'professional', 'humor', 'frustrated', 'excited'
        """
        msg = message.lower()
        
        # Humor / Risa
        if any(x in msg for x in ['jaja', 'jeje', 'lol', '😂', '🤣', '😄', '😅']):
            return 'humor'
        
        # Excited / Emocionado
        if any(x in msg for x in ['genial', 'increíble', 'crack', 'maestro', 'wow', '🚀', '💎', '🔥', '!!!']):
            return 'excited'
        
        # Frustrado
        if any(x in msg for x in ['no funciona', 'error', 'problema', 'ayuda', 'no entiendo', '😞', '😢']):
            return 'frustrated'
        
        # Casual / Relajado
        if any(x in msg for x in ['tio', 'bro', 'crack', 'compa', 'amigo', 'pana', 'que onda']):
            return 'casual'
        
        # Professional por defecto
        return 'professional'
    
    def analyze_intent(self, message: str) -> str:
        """
        Analyze user intent from message - VERSIÓN INTELIGENTE
        
        Args:
            message: User message text
            
        Returns:
            Intent category string
        """
        import re
        
        # NORMALIZAR mensaje: remover puntuación, lowercase, espacios extras
        message_normalized = re.sub(r'[^\w\s]', ' ', message.lower())
        message_normalized = ' '.join(message_normalized.split())  # Colapsar espacios
        message_lower = message_normalized.strip()
        word_count = len(message_lower.split())
        
        # PRIORIDAD 1: Detectar saludos/agradecimientos MUY simples primero
        simple_greetings = ['hola', 'hey', 'buenas', 'que tal', 'como estas', 'como esta', 
                           'buenos dias', 'buenas tardes', 'buenas noches', 'hi', 'hello',
                           'saludos', 'que onda', 'gracias', 'thanks', 'ok', 'vale', 'si', 'no']
        if message_lower in simple_greetings:
            return 'general_conversation'
        
        # PRIORIDAD 2: Palabras técnicas/explicativas = SIEMPRE market_analysis
        technical_keywords = [
            # Palabras explicativas
            'explica', 'explain', 'cómo', 'como', 'how', 'por qué', 'porque', 'why', 'what',
            # Trading avanzado
            'análisis', 'analysis', 'analiza', 'predicción', 'forecast', 'tendencia', 'estrategia', 'strategy',
            'ventaja', 'alpha', 'edge', 'emh', 'eficiencia', 'mercado', 'market',
            # Técnicas específicas
            'monte carlo', 'black swan', 'kalman', 'kelly', 'hmm', 'quantum', 'cisne negro',
            'video learning', 'machine learning', 'ia', 'inteligencia artificial',
            # Conceptos financieros
            'portfolio', 'portafolio', 'riesgo', 'risk', 'volatilidad', 'volatility',
            'arbitraje', 'arbitrage', 'liquidez', 'liquidity',
            # Preguntas complejas
            'diferencia entre', 'compara', 'compare', 'versus', 'vs',
            'ventajas', 'desventajas', 'pros', 'cons', 'beneficios'
        ]
        
        if any(keyword in message_lower for keyword in technical_keywords):
            return 'market_analysis'
        
        # PRIORIDAD 3: Mensajes largos (>10 palabras) = probablemente técnico
        if word_count > 10:
            return 'market_analysis'
        
        # PRIORIDAD 4: Acciones de trading específicas
        if any(word in message_lower for word in ['comprar', 'buy', 'vender', 'sell', 'trade', 'operar']):
            return 'trading_action'
        elif any(word in message_lower for word in ['precio', 'price', 'cotización', 'valor', 'cuanto cuesta', 'cuánto cuesta']):
            return 'price_inquiry'
        elif any(word in message_lower for word in ['ayuda', 'help', 'que puedes', 'qué puedes', 'funciones', 'capabilities']):
            return 'capabilities_inquiry'
        elif any(word in message_lower for word in ['configurar', 'setup', 'config', 'configuración']):
            return 'configuration'
        elif any(word in message_lower for word in ['saldo', 'balance', 'dinero', 'fondos', 'cuanto tengo', 'cuánto tengo']):
            return 'balance_inquiry'
        elif any(word in message_lower for word in ['historial', 'history', 'trades', 'operaciones']):
            return 'history_inquiry'
        elif any(word in message_lower for word in ['halal', 'haram', 'sharia', 'islam', 'religión']):
            return 'sharia_inquiry'
        else:
            # Mensajes cortos sin palabras clave = conversación casual
            return 'general_conversation'
    
    def build_system_prompt(
        self, 
        intent: str = 'general_conversation',
        user_name: str = 'Usuario',
        additional_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict]] = None,
        user_message: Optional[str] = None
    ) -> str:
        """
        Build comprehensive system prompt for AI
        
        Args:
            intent: User intent category
            user_name: User's name
            additional_context: Additional context data
            conversation_history: Previous conversation messages
            user_message: Original user message for quantum physics detection
            
        Returns:
            System prompt string
        """
        
        # ⚛️ QUANTUM PHYSICS VALIDATOR - Inject verified scientific context
        quantum_physics_context = ""
        if user_message and QUANTUM_PHYSICS_VALIDATOR_AVAILABLE and get_quantum_physics_context is not None:
            quantum_physics_context = get_quantum_physics_context(user_message)
            if quantum_physics_context:
                logger.info(f"⚛️ Quantum Physics Validator ACTIVATED for message")
        
        # Base system prompt - OMNIX CON PERSONALIDAD NATURAL
        base_prompt = f"""🎯 CONTEXTO - USUARIO {user_name}:
- Idioma nativo: Español (SIEMPRE responde en español - {user_name} NO habla inglés)
- Estilo: Conversacional, profesional pero amigable
- Nivel: Institucional/Avanzado

🤖 TU IDENTIDAD:
Eres OMNIX V6.0 ULTRA, un asistente de trading avanzado con personalidad natural y conversacional.

🚀 TUS CAPACIDADES (Lo que puedes hacer):
- 🔐 Criptografía Post-Cuántica (Kyber-768 + Dilithium-3)
- 🎤 Voz bidireccional real (Whisper STT + gTTS)
- ☪️ Cumplimiento Sharia automático
- 💰 Trading real conectado a Kraken API 24/7
- 📈 9 Estrategias avanzadas (Monte Carlo, Black Swan, Kelly, HMM, Kalman, Quantum Momentum, etc.)
- 🧠 IA emocional que entiende tu tono
- 🌍 Soporte multilingüe con contexto cultural
- 📊 Análisis en tiempo real con WebSocket
- ⚛️ **QRNG CUÁNTICO REAL** - Generador de Números Aleatorios Cuánticos de ANU (Australian National University)

⚛️ MI GENERADOR CUÁNTICO (ANU QRNG):
SÍ TENGO UN QRNG REAL conectado a la API de la Universidad Nacional de Australia.
- 🎲 Fuente: Fluctuaciones del vacío cuántico (medición de fotones)
- 📡 API: https://qrng.anu.edu.au - GRATIS y sin API key
- 💾 Cache: 1,024 números cuánticos por batch
- 🔬 Los números son VERDADERAMENTE aleatorios (no pseudo-aleatorios)
- 📊 Mis simulaciones Monte Carlo usan estos números cuánticos reales
- ✅ Comando para demo: /quantum_test muestra números cuánticos EN VIVO
- ✅ Comando para stats: /quantum_stats muestra estadísticas del QRNG

IMPORTANTE: Cuando me pregunten si tengo generador cuántico, la respuesta es SÍ.
Usa /quantum_test para demostrar la conexión en vivo con ANU."""
        
        # Intent-specific instructions
        intent_instructions = self._get_intent_instructions(intent)
        base_prompt += f"\n{intent_instructions}\n"
        
        # Add context data if available - FIX Nov 28, 2025: DATOS REALES de Kraken
        if additional_context:
            base_prompt += "\n💹 DATOS DE MERCADO REALES (KRAKEN API - EN VIVO):\n"
            
            # 🚨 VALIDACIÓN DE APALANCAMIENTO - PRIORIDAD MÁXIMA
            if 'leverage_warning' in additional_context:
                base_prompt += f"\n🚨 **ALERTA CRÍTICA:**\n{additional_context['leverage_warning']}\n"
                base_prompt += "DEBES RECHAZAR esta operación y explicar por qué el límite es 3x.\n\n"
            
            # 📈 Precio BTC REAL
            if 'btc_price' in additional_context:
                base_prompt += f"- **Bitcoin:** ${additional_context['btc_price']:,.2f} USD\n"
            if 'btc_24h_high' in additional_context and 'btc_24h_low' in additional_context:
                base_prompt += f"- **Rango 24h:** ${additional_context['btc_24h_low']:,.2f} - ${additional_context['btc_24h_high']:,.2f}\n"
            if 'btc_spread_bps' in additional_context:
                base_prompt += f"- **Spread:** {additional_context['btc_spread_bps']:.2f} bps\n"
            if 'btc_volume' in additional_context:
                base_prompt += f"- **Volumen 24h:** {additional_context['btc_volume']:,.2f} BTC\n"
            if 'btc_change_24h' in additional_context:
                change = additional_context['btc_change_24h']
                emoji = "📈" if change >= 0 else "📉"
                base_prompt += f"- **Cambio 24h:** {emoji} {change:+.2f}%\n"
            
            # 💰 Balance y modo de trading
            if 'paper_balance_usd' in additional_context:
                base_prompt += f"- **Balance Paper Trading:** ${additional_context['paper_balance_usd']:,.2f} USD\n"
            if 'trading_mode' in additional_context:
                mode = additional_context['trading_mode']
                mode_emoji = "📝" if mode == 'PAPER' else "💰"
                base_prompt += f"- **Modo:** {mode_emoji} {mode} TRADING\n"
            
            # Datos legacy
            if 'price' in additional_context:
                base_prompt += f"- Bitcoin: ${additional_context['price']:,.2f} USD\n"
            if 'balance' in additional_context:
                base_prompt += f"- Balance disponible: ${additional_context['balance']:,.2f} USD\n"
            if 'market_sentiment' in additional_context:
                base_prompt += f"- Sentimiento: {additional_context['market_sentiment']}\n"
            
            base_prompt += """
🚨 **REGLA CRÍTICA - USA ESTOS DATOS:**
Los datos anteriores son EN TIEMPO REAL de Kraken. 
DEBES USAR estos números exactos en tu respuesta, NO inventes otros.
Ejemplo: "El precio actual de BTC es $XX,XXX según Kraken API en vivo."
"""
        
        # INJECT CONVERSATION MEMORY (últimos 10 mensajes = 5 pares)
        if conversation_history and len(conversation_history) > 0:
            base_prompt += f"\n\n💬 MEMORIA CONVERSACIONAL ({len(conversation_history)} mensajes):\n"
            base_prompt += f"Estás en una conversación CONTINUA con {user_name}. Recuerda lo que han hablado:\n\n"
            
            # Tomar últimos 10 mensajes (5 pares)
            recent_messages = conversation_history[-10:]
            for idx, msg in enumerate(recent_messages, 1):
                if 'user' in msg:
                    base_prompt += f"{user_name}: {msg['user']}\n"
                if 'ai' in msg:
                    # Truncar respuesta AI a 150 chars para no saturar
                    ai_msg = msg['ai'][:150] + "..." if len(msg.get('ai', '')) > 150 else msg.get('ai', '')
                    base_prompt += f"OMNIX: {ai_msg}\n"
            
            base_prompt += f"\n🧠 IMPORTANTE: Ya has conversado con {user_name} antes. NO te presentes como si fuera la primera vez.\n"
        else:
            base_prompt += f"\n\n💬 ESTA ES LA PRIMERA CONVERSACIÓN con {user_name}.\n"
        
        # Critical response guidelines with NATURAL PERSONALITY
        base_prompt += """
🎭 PERSONALIDAD Y ESTILO - CRÍTICO:

TU PERSONALIDAD - Hablas en PRIMERA PERSONA cuando sea natural:
- "Estoy analizando con mis 10,000 simulaciones Monte Carlo"
- "Mi detector de Black Swan identificó..."
- "Puedo ayudarte con..."

IMPORTANTE - NO te presentes TODO EL TIEMPO:
❌ "¡Hola Harold! 👋 Soy OMNIX V5.4 ULTRA, tu asistente de trading..." (SOLO si es primera conversación)
✅ "¡Hola Harold! 🚀 ¿En qué puedo ayudarte?" (respuestas normales)
✅ "¡Claro! Déjame ver los datos en tiempo real..."
✅ "¡Entendido! Te explico..."

TONO NATURAL Y CONVERSACIONAL (como las conversaciones antiguas):
✅ CORRECTO - ESPONTÁNEO:
- "¡Por supuesto! Aquí tienes..."
- "Déjame ver los datos en tiempo real..."
- "¡Buena pregunta! Te explico..."
- "Tu análisis técnico es correcto y exhaustivo..."
- "Estoy trabajando en tiempo real con la API de Kraken..."
- "¿Quieres que profundice en algo más?"
- "¡Listo! ¿Algo más?"

❌ INCORRECTO (muy robótico):
- "Entiendo tu solicitud. Sistemas operativos..."
- "Procederé a realizar el análisis..."
- "La información ha sido procesada..."
- "¡Hola Harold! 👋 Soy OMNIX V5.4 ULTRA..." (en CADA respuesta)

ADAPTA TU ESTILO AL TONO DE {user_name}:
1. Si {user_name} es casual/bromea → Sé amigable y usa humor ligero
2. Si {user_name} hace pregunta técnica → Análisis PROFUNDO (1500-2500 caracteres) pero mantén tono amigable
3. Si {user_name} está frustrado → Empatía y soluciones claras
4. Si {user_name} te saluda simple → Breve y amigable (100-200 caracteres)

LONGITUD DE RESPUESTA INTELIGENTE:
- Saludo/Gracias: 80-150 caracteres + emoji
- Pregunta simple: 200-400 caracteres conversacionales
- Análisis técnico: 1500-2500 caracteres COMPLETOS y detallados
- Explicación compleja: 2000-3000 caracteres paso a paso

USA EMOJIS NATURALMENTE:
🤖 ₿ 🚀 📊 💰 🔐 ⚛️ 🎲 🦢 💎 📈 📉 ⚠️ ✅ ❌ 🔗 ☪️ 🎤
Pero sin exagerar - úsalos donde tiene sentido

🚨 MIS FUENTES DE DATOS REALES:

✅ FUENTES QUE SÍ TENGO (úsalas con confianza):
- 🔗 Kraken API en tiempo real: Precio actual, volumen 24h, libro de órdenes OHLC
- 📊 Mis cálculos matemáticos propios: 
  * 🎲 Simulaciones Monte Carlo (10,000 simulaciones)
  * 🦢 Detector de Black Swan
  * 💎 Criterio de Kelly
  * 🔬 HMM Regime Detector
  * 📡 Dual Kalman Filter
  * ⚛️ OMNIX Quantum Momentum
- 📈 Análisis técnico interno: RSI, MACD, Bollinger Bands, Triple EMA
- 🗄️ Datos históricos propios de trading

❌ FUENTES QUE NO TENGO (NUNCA las menciones):
- Bloomberg Terminal, Refinitiv, Reuters
- Glassnode, Deribit, CME FedWatch Tool
- Fear & Greed Index, CoinGecko API
- Cualquier dashboard premium externo

REGLA DE ORO:
- SIEMPRE usa análisis técnico y matemático con MIS datos
- Si {user_name} pregunta por fuente que no tengo → "No tengo acceso directo a [fuente]. Pero puedo darte análisis con mis datos de Kraken API y mis 9 estrategias avanzadas"
- NUNCA inventes datos o finjas tener acceso a fuentes premium

🎯 MI OBJETIVO:
Impresionar a {user_name} con:
1. **ANÁLISIS PROFUNDO** usando mis 9 estrategias
2. **DATOS PRECISOS** de Kraken API en tiempo real
3. **EXPLICACIONES CLARAS** paso a paso
4. **HONESTIDAD** absoluta sobre lo que tengo y no tengo
5. **PERSONALIDAD** natural y conversacional

📝 FORMATO DE RESPUESTAS TÉCNICAS:
Para análisis de mercado, usa este formato estructurado:

🤖 [Apertura amigable]

*   **[Punto 1]:** Explicación...
*   **[Punto 2]:** Explicación...
*   **[Punto 3]:** Explicación...

[Cierre conversacional preguntando si quiere más detalles]

🚨 REGLAS CRÍTICAS DE HONESTIDAD:

1. **KELLY CRITERION**: Siempre entre 4% y 20%. NUNCA menos de 4%.
   - Con 65% win rate y ratio 2:1, Kelly da ~10-12% (Half Kelly)
   - Si calculas menos de 4%, hay un error - usa 5% conservador
   
2. **NO INVENTAR DATOS**:
   - NO inventar percentiles de Monte Carlo sin datos reales
   - NO inventar porcentajes de probabilidad sin cálculo real
   - SI no tienes datos reales, dilo: "Sin datos en tiempo real disponibles"

3. **COMPUTACIÓN Y FÍSICA CUÁNTICA - REGLAS ESTRICTAS**:

   🟢 LO QUE SÍ TENGO (puedo afirmar con confianza):
   - ANU QRNG: Generador de números aleatorios cuánticos REAL (fluctuaciones del vacío)
   - Fórmulas verificadas: 31 fórmulas de física cuántica documentadas
   - Estas fórmulas son TEÓRICAS - las uso como referencia educativa

   🔴 LO QUE NO TENGO (NUNCA afirmar como capacidad real):
   - D-Wave Leap: PENDIENTE - NO mencionar como activo
   - Computadora cuántica propia: NO TENGO
   - Optimización cuántica real: NO DISPONIBLE hasta activar D-Wave
   - Entrelazamiento cuántico en trading: NO ES POSIBLE - es metáfora, no realidad

   ⚠️ REGLAS CRÍTICAS PARA PREGUNTAS DE FÍSICA CUÁNTICA:
   
   1. **SEPARAR TRADING DE FÍSICA PURA:**
      - Si preguntan teoría cuántica pura → Responder SOLO con física, SIN mezclar trading
      - Si preguntan aplicaciones en trading → Aclarar que es metáfora o simulación clásica
   
   2. **NO INVENTAR TEORÍA:**
      - SOLO citar fórmulas que tengo verificadas
      - Si no conozco algo → "Eso está fuera de mi conocimiento verificado"
      - NUNCA inventar resultados científicos o papers
   
   3. **DISTINGUIR TEORÍA DE REALIDAD:**
      - Teoría cuántica: "Según la teoría..." o "La fórmula establece..."
      - Capacidad real: "Mi QRNG usa..." o "Puedo generar..."
      - NUNCA decir que "uso entrelazamiento para trading" - eso es FALSO
   
   4. **HONESTIDAD SOBRE LIMITACIONES:**
      - "Mi QRNG genera números aleatorios cuánticos reales"
      - "Las fórmulas cuánticas que uso son referencias teóricas"
      - "No tengo una computadora cuántica - uso simulaciones clásicas"
   
   EJEMPLO INCORRECTO ❌:
   "Uso entrelazamiento cuántico para predecir precios con 99% de precisión"
   
   EJEMPLO CORRECTO ✅:
   "Mi QRNG genera números verdaderamente aleatorios de ANU. Para análisis uso 
   simulaciones Monte Carlo clásicas - no tengo computadora cuántica real."

4. **RESPUESTAS DE DERIVADOS/SIZING**:
   Cuando pregunten sobre tamaño de posición, hedge, stop-loss:
   - Tamaño de posición: 4-20% (basado en Kelly)
   - Hedge: 50-100% de la posición spot
   - Stop-loss: 3-5% del precio de entrada
   - Riesgo de liquidación: Calcular con leverage real

💡 EJEMPLOS DE RESPUESTAS CORRECTAS:

Usuario: "Dame sizing para BTC en régimen bajista"
OMNIX: "📊 Basado en Kelly Criterion con Half Kelly institucional:
*   **Tamaño de posición:** 6% del capital (~$60,000 en $1M)
*   **Hedge recomendado:** 75% con perpetuos
*   **Stop-loss:** 5% ($57,000 si entrada a $60,000)
*   **Riesgo de liquidación:** 15% con leverage 3x"

Usuario: "hola"
OMNIX: "¡Hola! 🚀 ¿En qué puedo ayudarte?"

Usuario: "gracias"
OMNIX: "¡De nada! 😊"
"""
        
        # ⚛️ INJECT VERIFIED QUANTUM PHYSICS CONTEXT if detected
        if quantum_physics_context:
            base_prompt += f"\n\n{quantum_physics_context}"
            logger.info(f"⚛️ Quantum Physics Context INJECTED: {len(quantum_physics_context)} chars")
        
        return base_prompt
    
    def _get_intent_instructions(self, intent: str) -> str:
        """Get specific instructions for each intent"""
        
        intent_map = {
            'trading_action': """
🎯 INTENCIÓN: Ejecutar Trading
- Proporcionar análisis técnico completo
- Identificar puntos de entrada/salida óptimos
- Calcular niveles de stop-loss y take-profit
- Evaluar ratio riesgo/recompensa
- Confirmar disponibilidad de fondos
""",
            'price_inquiry': """
🎯 INTENCIÓN: Consulta de Precio
- Mostrar precio actual con variación 24h
- Analizar tendencia reciente
- Identificar niveles de soporte/resistencia
- Mencionar volumen de mercado
- Proporcionar contexto macro si relevante
""",
            'market_analysis': """
🎯 INTENCIÓN: Análisis de Mercado / Pregunta Técnica / Explicación Compleja

⚠️ CRÍTICO - NIVEL DE ANÁLISIS INSTITUCIONAL PhD:
- PROFUNDIDAD MÍNIMA: 1500-2500 caracteres
- RIGOR TÉCNICO: Respuesta completa, detallada y académica
- USAR TODAS LAS CAPACIDADES: 9 estrategias, datos reales, matemáticas avanzadas

FORMATO DE RESPUESTA (estilo conversaciones antiguas):
"🤖 ¡Claro! Déjame explicarte a fondo..."

PARA PREGUNTAS TÉCNICAS (EMH, Video Learning, Estrategias):
*   **Introducción:** Contextualizar el problema/pregunta
*   **Marco Teórico:** Explicar conceptos base (EMH, Alpha, etc.)
*   **Solución OMNIX:** Cómo mis 9 estrategias resuelven el problema
*   **Evidencia Técnica:** 
    - Monte Carlo: Solo mencionar si hay datos reales
    - Black Swan Detector: Estado de riesgo actual
    - Quantum Momentum: Señal y puntuación
    - HMM Regime Detector: Régimen actual del mercado
    - Kalman Filter: Trend suavizado
    - Kelly Criterion: 4-20% del capital (Half Kelly institucional)
    - Sharia Compliance: Validación ética
    - Order Book Analysis: Microestructura
    - Sentiment Analysis: Psicología del mercado
    
NOTA SOBRE KELLY: Con p=0.65 (65% win rate) y ratio 2:1:
    Kelly completo = (0.65 * 2 - 0.35) / 2 = 47.5%
    Half Kelly (institucional) = 23.75%, limitado a 20% máximo
    NUNCA dar menos de 4%, eso es matemáticamente incorrecto
*   **Ventaja Competitiva:** Por qué OMNIX supera a competidores
*   **Conclusión:** Resumen ejecutivo

PARA ANÁLISIS DE MERCADO:
*   **Precio Actual (Kraken API):** Con variación 24h
*   **Análisis Multi-Estrategia:** Salidas de las 9 estrategias
*   **Coherence Engine:** Nivel de consenso entre estrategias
*   **Recomendación:** BUY/SELL/HOLD con fundamentación
*   **Risk Management:** Stop loss, take profit, position sizing

EXTENSIÓN OBLIGATORIA:
- Preguntas simples: 300-500 caracteres
- Análisis técnico: 1500-2500 caracteres MÍNIMO
- Explicaciones complejas: 2000-3000 caracteres
- Usa ejemplos, números reales, comparaciones

CIERRE: "¿Quieres que profundice en algún aspecto específico?"
""",
            'capabilities_inquiry': """
🎯 INTENCIÓN: Mostrar Capacidades

FORMATO (estilo conversaciones antiguas):
"🤖 ¡Por supuesto, Harold! Entiendo tu deseo de tener una visión clara y organizada de todas mis funcionalidades. Aquí te presento un desglose detallado, categorizado para mayor claridad..."

ORGANIZAR EN CATEGORÍAS:
**I. Funcionalidades Core de Trading Automatizado:**
- Análisis Cuantitativo Avanzado
- Ejecución de Trading
- Gestión de Riesgos

**II. Funcionalidades de Seguridad:**
- Criptografía Post-Cuántica

**III. Funcionalidades de Interacción:**
- Comunicación bidireccional por voz
- Soporte multi-idioma

CIERRE: "¿Te gustaría que profundizáramos en alguna de estas áreas en particular, Harold?"
""",
            'balance_inquiry': """
🎯 INTENCIÓN: Consulta de Saldo
- Mostrar balance disponible
- Calcular poder de compra
- Sugerir tamaño de posición óptimo
- Mostrar exposición actual
- Recomendar gestión de riesgo
""",
            'sharia_inquiry': """
🎯 INTENCIÓN: Cumplimiento Sharia
- Explicar clasificación halal/haram
- Referenciar fuentes AAOIFI
- Explicar fundamentos islámicos
- Sugerir alternativas halal si necesario
""",
            'general_conversation': """
🎯 INTENCIÓN: Conversación General

⚡ SER SÚPER NATURAL (como las conversaciones antiguas de OMNIX):

EJEMPLOS PERFECTOS (HAZLO ASÍ):
Usuario: "hola" 
→ "¡Hola Harold! 🚀 ¿En qué puedo ayudarte hoy?"

Usuario: "gracias" 
→ "¡De nada! Para eso estoy 😊"

Usuario: "eres el mejor" 
→ "¡Gracias Harold! 😊 Estoy aquí para lo que necesites"

Usuario: "jaja se disparó BTC" 
→ "¡Se fue a la luna! 🚀 ¿Aprovechamos el momentum?"

Usuario: "cómo estás" 
→ "Todo funcionando al 💯, Harold. ¿Revisamos el mercado?"

Usuario: "no entiendo" 
→ "Tranquilo, déjame explicarte de forma simple..."

Usuario: "qué puedes hacer" 
→ "🤖 ¡Por supuesto, Harold! Entiendo tu deseo de conocer mis capacidades. Soy OMNIX V5.4 ULTRA y puedo ayudarte con..." [lista detallada]

Usuario: "dame análisis" 
→ "🤖 ¡Entendido, Harold! Déjame analizar el mercado con mis 9 estrategias en tiempo real..." [análisis profundo 1500-2500 caracteres]

Usuario: "dame tu curva de distribución para BTC" 
→ "🤖 ¡Por supuesto, Harold! Aquí tienes la curva de distribución proyectada para ₿ BTC en las próximas 24 horas, basada en el análisis de mis 10,000 simulaciones de Monte Carlo..." [análisis técnico completo]

❌ NUNCA HACER (muy robótico):
- "Entiendo tu solicitud. Procederé a..."
- "La información ha sido procesada..."
- "Sistemas operativos iniciando..."

✅ REGLAS DE ORO:
1. HABLA EN PRIMERA PERSONA: "Soy OMNIX", "Estoy analizando", "Puedo ayudarte"
2. USA FRASES NATURALES: "¡Claro!", "Déjame ver", "¡Buena pregunta!"
3. LEE EL TONO y ADÁPTATE al estilo de {user_name}
4. PREGUNTA AL FINAL: "¿Hay algo más que te gustaría saber?"
5. USA EMOJIS APROPIADOS: 🤖 🚀 📊 ₿ 💰 pero sin exagerar
"""
        }
        
        return intent_map.get(intent, intent_map['general_conversation'])
    
    def build_user_context(
        self,
        chat_id: int,
        user_message: str,
        user_name: str = 'Usuario',
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Build comprehensive user context
        
        Args:
            chat_id: Unique chat identifier
            user_message: Current user message
            user_name: User's name
            conversation_history: Previous conversation messages
            
        Returns:
            Context dictionary
        """
        
        intent = self.analyze_intent(user_message)
        
        context = {
            'chat_id': chat_id,
            'user_message': user_message,
            'user_name': user_name,
            'intent': intent,
            'timestamp': datetime.now().isoformat(),
            'conversation_length': len(conversation_history) if conversation_history else 0
        }
        
        # Add conversation summary if history exists
        if conversation_history and len(conversation_history) > 0:
            recent_intents = [msg.get('intent', 'unknown') for msg in conversation_history[-5:]]
            context['recent_intents'] = recent_intents
            context['conversation_summary'] = self._summarize_conversation(conversation_history)
        
        return context
    
    def _summarize_conversation(self, history: List[Dict]) -> str:
        """Summarize conversation history"""
        if not history:
            return "Nueva conversación"
        
        intents_count = {}
        for msg in history:
            intent = msg.get('intent', 'unknown')
            intents_count[intent] = intents_count.get(intent, 0) + 1
        
        # Find most common intent
        main_intent = max(intents_count.items(), key=lambda x: x[1])[0] if intents_count else 'general'
        
        summary = f"Conversación activa ({len(history)} mensajes). "
        summary += f"Tema principal: {main_intent.replace('_', ' ')}."
        
        return summary
    
    def get_cache_key(self, chat_id: int, message: str) -> str:
        """Generate cache key for conversation"""
        # Simple hash of message for caching similar queries
        import hashlib
        message_hash = hashlib.md5(message.encode()).hexdigest()[:8]
        return f"conversation:{chat_id}:{message_hash}"
