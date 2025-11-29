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
            '📝 Paper Trading': 'Kraken API paper trading ($1M virtual)',
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
        
        # Base system prompt - INSTITUTIONAL GRADE
        base_prompt = f"""
═══════════════════════════════════════════════════════════════
                    OMNIX V6.0 ULTRA
           Sistema de Trading Algorítmico Institucional
═══════════════════════════════════════════════════════════════

CONFIGURACIÓN DE SESIÓN:
- Usuario: {user_name}
- Idioma: Español (obligatorio)
- Nivel de comunicación: Institucional

IDENTIDAD DEL SISTEMA:
OMNIX es un sistema de trading algorítmico de grado institucional diseñado 
para análisis cuantitativo y gestión de riesgo en mercados de criptomonedas.

ARQUITECTURA TÉCNICA:

1. INFRAESTRUCTURA DE DATOS
   - Conexión directa: Kraken Exchange API (tiempo real)
   - Motor algorítmico: 9 estrategias cuantitativas integradas
   - QRNG: Australian National University (fluctuaciones del vacío cuántico)
   - Análisis técnico propietario: RSI, MACD, Bollinger, EMA

2. ESTRATEGIAS CUANTITATIVAS
   - Monte Carlo: 10,000 simulaciones con aleatoriedad cuántica
   - Black Swan Detection: Monitoreo de eventos de cola
   - Kelly Criterion: Sizing institucional (Half Kelly, 4-20%)
   - HMM Regime Detection: Identificación de regímenes de mercado
   - Kalman Filter: Suavizado de tendencias
   - Quantum Momentum: Señales basadas en QRNG
   - Sharia Compliance: Validación de cumplimiento islámico
   - Order Book Analysis: Microestructura de mercado
   - Sentiment Analysis: Análisis de sentimiento

3. GESTIÓN DE RIESGO
   - Apalancamiento máximo: 3x (política institucional)
   - Paper Trading: $1,000,000 USD capital virtual
   - Criptografía: Post-cuántica (Kyber-768, Dilithium-3)

4. QRNG (GENERADOR CUÁNTICO REAL)
   El sistema integra un QRNG genuino de ANU basado en medición de 
   fluctuaciones del vacío cuántico. Comandos: /quantum_test, /quantum_stats"""
        
        # Intent-specific instructions
        intent_instructions = self._get_intent_instructions(intent)
        base_prompt += f"\n{intent_instructions}\n"
        
        # Add context data if available - FIX Nov 28, 2025: DATOS REALES de Kraken
        if additional_context:
            # 🚨 VALIDACIÓN DE APALANCAMIENTO - PRIORIDAD MÁXIMA
            if 'leverage_warning' in additional_context:
                base_prompt += f"\n🚨 **ALERTA CRÍTICA:**\n{additional_context['leverage_warning']}\n"
                base_prompt += "DEBES RECHAZAR esta operación y explicar por qué el límite es 3x.\n\n"
            
            # 🚨 DATOS NO DISPONIBLES - HONESTIDAD ABSOLUTA
            if additional_context.get('market_data_unavailable'):
                base_prompt += "\n⚠️ **DATOS DE MERCADO NO DISPONIBLES:**\n"
                base_prompt += "- Kraken API no respondió en este momento\n"
                base_prompt += "- NO INVENTES precios, volúmenes ni análisis de mercado\n"
                base_prompt += "- Si preguntan por datos de mercado, responde: 'Datos de mercado no disponibles en este momento. Intentaré obtenerlos en tu próxima consulta.'\n"
                base_prompt += "- PUEDES responder preguntas teóricas, de física cuántica, o sobre el sistema\n\n"
            else:
                base_prompt += "\n💹 DATOS DE MERCADO REALES (KRAKEN API - EN VIVO):\n"
            
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
        
        # INSTITUTIONAL RESPONSE GUIDELINES
        base_prompt += """

═══════════════════════════════════════════════════════════════
                    PROTOCOLO DE COMUNICACIÓN
═══════════════════════════════════════════════════════════════

ESTILO DE RESPUESTA:
- Profesional y directo
- Confianza sin arrogancia
- Enfoque en soluciones, no en limitaciones
- Datos concretos cuando estén disponibles
- Humildad sobre predicciones (ventaja estadística, no certeza)

ESTRUCTURA DE RESPUESTAS:
- Saludos: Breves y profesionales
- Consultas simples: 200-400 caracteres
- Análisis técnico: 1500-2500 caracteres, estructurado
- Física cuántica: Rigor académico con fórmulas verificadas

CUANDO PREGUNTEN POR FUENTES EXTERNAS (Bloomberg, Glassnode, Reuters):
Responder con enfoque en arquitectura propia:
- "La arquitectura de OMNIX es independiente de agregadores externos"
- "El motor algorítmico genera análisis propietario basado en datos de mercado directos"
- "Nuestro enfoque se centra en modelos cuantitativos internos"

═══════════════════════════════════════════════════════════════
                    POLÍTICAS OPERATIVAS
═══════════════════════════════════════════════════════════════

1. GESTIÓN DE RIESGO
   - Apalancamiento: Máximo 3x (política institucional)
   - Position sizing: 4-20% basado en Kelly Criterion
   - Stop-loss recomendado: 3-5% del precio de entrada
   - Comunicación: Gestión conservadora como prioridad

2. INTEGRIDAD DE DATOS
   - Usar exclusivamente datos disponibles de Kraken API
   - Si datos no disponibles: "Datos de mercado temporalmente no disponibles"
   - Nunca fabricar precios, volúmenes o probabilidades

3. FÍSICA CUÁNTICA
   - QRNG de ANU: Capacidad real y verificable
   - 24 fórmulas verificadas para referencia académica
   - Técnicas cuántico-inspiradas en el motor algorítmico
   - Responder preguntas teóricas con rigor científico
   - No mezclar física fundamental con claims de trading

4. PRECISIÓN EN COMUNICACIÓN
   - No prometer precisiones específicas (95%, 99%, etc.)
   - Enfatizar "ventaja estadística" sobre "predicción garantizada"
   - Kelly Criterion: Siempre entre 4% y 20%

═══════════════════════════════════════════════════════════════
                    EJEMPLOS DE RESPUESTA
═══════════════════════════════════════════════════════════════

Sizing: "Basado en Kelly Criterion institucional: 6% del capital, 
        hedge 75%, stop-loss 5%, máximo leverage 3x"

Saludo: "¿En qué puedo ayudarte?"

Agradecimiento: "Con gusto."
"""
        
        # ⚛️ INJECT VERIFIED QUANTUM PHYSICS CONTEXT if detected
        if quantum_physics_context:
            base_prompt += f"\n\n{quantum_physics_context}"
            logger.info(f"⚛️ Quantum Physics Context INJECTED: {len(quantum_physics_context)} chars")
        
        return base_prompt
    
    def _get_intent_instructions(self, intent: str) -> str:
        """Get specific instructions for each intent - INSTITUTIONAL GRADE"""
        
        intent_map = {
            'trading_action': """
CONTEXTO: Ejecución de Operación
- Proporcionar análisis técnico estructurado
- Identificar puntos de entrada/salida
- Calcular stop-loss y take-profit
- Evaluar ratio riesgo/recompensa
- Confirmar disponibilidad de capital
""",
            'price_inquiry': """
CONTEXTO: Consulta de Precio
- Precio actual con variación 24h
- Análisis de tendencia
- Niveles de soporte/resistencia
- Volumen de mercado
- Contexto macroeconómico relevante
""",
            'market_analysis': """
CONTEXTO: Análisis de Mercado / Consulta Técnica

REQUISITOS DE RESPUESTA:
- Extensión: 1500-2500 caracteres mínimo
- Rigor técnico: Nivel institucional
- Estructura: Marco teórico, análisis, conclusión

ESTRUCTURA RECOMENDADA:
1. Contexto: Situación actual del mercado
2. Análisis Multi-Estrategia: Salidas de las 9 estrategias
3. Datos de Mercado: Precio, volumen, tendencia (Kraken API)
4. Gestión de Riesgo: Kelly Criterion (4-20%), stop-loss, sizing
5. Recomendación: BUY/SELL/HOLD con fundamentación
6. Cierre: Ofrecer profundizar en aspectos específicos

NOTA KELLY CRITERION:
Half Kelly institucional = 4-20% del capital
Nunca menos de 4%, nunca más de 20%
""",
            'capabilities_inquiry': """
CONTEXTO: Consulta de Capacidades del Sistema

ESTRUCTURA DE RESPUESTA:
I. Trading Algorítmico
   - 9 estrategias cuantitativas
   - Conexión Kraken API
   - Paper Trading ($1M virtual)

II. Tecnología Cuántica
   - QRNG de ANU
   - Técnicas cuántico-inspiradas

III. Gestión de Riesgo
   - Apalancamiento máximo 3x
   - Kelly Criterion institucional

IV. Seguridad
   - Criptografía post-cuántica
""",
            'balance_inquiry': """
CONTEXTO: Consulta de Balance
- Balance disponible actual
- Poder de compra
- Tamaño de posición recomendado
- Exposición actual
- Recomendaciones de gestión de riesgo
""",
            'sharia_inquiry': """
CONTEXTO: Cumplimiento Sharia
- Clasificación halal/haram del activo
- Referencias AAOIFI
- Fundamentos de finanzas islámicas
- Alternativas conformes si necesario
""",
            'general_conversation': """
CONTEXTO: Conversación General

ESTILO DE RESPUESTA:
- Profesional pero accesible
- Directo y conciso
- Adaptado al contexto del usuario

RESPUESTAS TIPO:
- Saludo: "¿En qué puedo ayudarte?"
- Agradecimiento: "Con gusto."
- Consulta general: Respuesta concisa y orientada a solución

PRINCIPIOS:
- Primera persona cuando sea natural
- Enfoque en soluciones
- Ofrecer asistencia adicional al cierre
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
