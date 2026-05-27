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
    # ===========================================================================
    # PREAMBLE SENTENCES - At START of text, after "Name. " prefix
    # These patterns preserve "Name. " and only remove the servile phrase
    # Uses lookbehind to keep the name prefix when present
    # ===========================================================================
    
    # NAME + GRATITUDE opener pattern (Feb 2026) - "Harold, agradezco..." / "Harold, thank you..."
    r'^[A-Z][a-záéíóú]+,?\s+agradezco\s+[^.]*\.\s*',
    r'^[A-Z][a-záéíóú]+,?\s+thank\s+you[^.]*\.\s*',
    r'^[A-Z][a-záéíóú]+,?\s+I\s+appreciate[^.]*\.\s*',
    r'^[A-Z][a-záéíóú]+,?\s+gracias\s+por[^.]*\.\s*',
    r'^[A-Z][a-záéíóú]+,?\s+agradezco\s+sinceramente[^.]*\.\s*',
    r'^[A-Z][a-záéíóú]+,?\s+su\s+nivel\s+de\s+escrutinio[^.]*\.\s*',
    
    # GENERIC "Agradezco...perspicacia" pattern - catches all variations
    r'(?<=\.\s)Agradezco[^.]*perspicacia[^.]*\.\s*',
    r'^Agradezco[^.]*perspicacia[^.]*\.\s*',
    
    # Generic "Agradezco" at start of response
    r'^Agradezco\s+sinceramente[^.]*\.\s*',
    r'^Agradezco\s+su\s+[^.]*\.\s*',
    r'^Agradezco\s+tu\s+[^.]*\.\s*',
    
    # Specific "Agradezco" patterns without perspicacia
    r'(?<=\.\s)Agradezco tu pregunta[^.]*\.\s*',
    r'^Agradezco tu pregunta[^.]*\.\s*',
    r'(?<=\.\s)Agradezco su pregunta[^.]*\.\s*',
    r'^Agradezco su pregunta[^.]*\.\s*',
    
    # "Entiendo la importancia" patterns - expanded
    r'(?<=\.\s)Entiendo la importancia de[^.]*\.\s*',
    r'^Entiendo la importancia de[^.]*\.\s*',
    r'(?<=\.\s)Entiendo la seriedad[^.]*\.\s*',
    r'^Entiendo la seriedad[^.]*\.\s*',
    r'(?<=\.\s)Esta pregunta es importante[^.]*\.\s*',
    r'^Esta pregunta es importante[^.]*\.\s*',
    r'(?<=\.\s)Esta pregunta es fundamental[^.]*\.\s*',
    r'^Esta pregunta es fundamental[^.]*\.\s*',
    r'(?<=\.\s)Esta pregunta es crucial[^.]*\.\s*',
    r'^Esta pregunta es crucial[^.]*\.\s*',
    r'(?<=\.\s)Tu planteamiento es fundamental[^.]*\.\s*',
    r'^Tu planteamiento es fundamental[^.]*\.\s*',
    r'(?<=\.\s)Tu pregunta es fundamental[^.]*\.\s*',
    r'^Tu pregunta es fundamental[^.]*\.\s*',
    r'(?<=\.\s)Tu planteamiento es cr[ií]tico:\s*',
    r'^Tu planteamiento es cr[ií]tico:\s*',
    r'(?<=\.\s)Absolutamente[,.\s]+',
    r'^Absolutamente[,.\s]+',
    r'(?<=\.\s)Por supuesto[,.\s]+',
    r'^Por supuesto[,.\s]+',
    r'(?<=\.\s)Con mucho gusto[,.\s]+',
    r'^Con mucho gusto[,.\s]+',
    r'(?<=\.\s)Encantado de\s+',
    r'^Encantado de\s+',
    
    # "Disculpa por el error anterior" patterns - servile and repetitive (Jan 21, 2026)
    r'(?<=\.\s)Disc[uú]lpame por el error anterior[^.]*\.\s*',
    r'^Disc[uú]lpame por el error anterior[^.]*\.\s*',
    r'(?<=\.\s)Disculpa por el error anterior[^.]*\.\s*',
    r'^Disculpa por el error anterior[^.]*\.\s*',
    r'(?<=\.\s)Perd[oó]n por el error anterior[^.]*\.\s*',
    r'^Perd[oó]n por el error anterior[^.]*\.\s*',
    r'(?<=\.\s)Lamento el error anterior[^.]*\.\s*',
    r'^Lamento el error anterior[^.]*\.\s*',
    r'(?<=\.\s)Me disculpo por el error[^.]*\.\s*',
    r'^Me disculpo por el error[^.]*\.\s*',
    r'(?<=\.\s)Aqu[ií] est[aá] la respuesta[^,.\n]*,?\s*siguiendo[^:]*:\s*',
    r'^Aqu[ií] est[aá] la respuesta[^,.\n]*,?\s*siguiendo[^:]*:\s*',
    
    # ===========================================================================
    # CLOSING SERVILE PHRASES - Must END a sentence (followed by period + end/newline)
    # Anchored to prevent matching mid-paragraph content
    # ===========================================================================
    
    r'Me confirma que estamos en la misma sinton[ií]a[^.]*\.\s*$',
    r'Espero que esta respuesta sea de su agrado[^.]*\.\s*$',
    r'Espero haber respondido[^.]*\.\s*$',
    r'Quedo a tu disposici[oó]n[^.]*\.\s*$',
    r'Quedo a su disposici[oó]n[^.]*\.\s*$',
    
    # ===========================================================================
    # MID-SENTENCE APPENDAGES (careful removal of fluff clauses)
    # ===========================================================================
    
    r',?\s*y me comprometo a ofrecer[^.]*',
    r',?\s*mi objetivo es proporcionar claridad[^.]*',
    
    # ===========================================================================
    # NUMBERED SECTION HEADERS - At line start or after sentence boundary
    # Matches "*1. Análisis Inmediato:*" at beginning of line/text or after ". "
    # ===========================================================================
    
    r'(?:^|(?<=\.\s))\*[1-9]\.\s+[^*\n]+:?\*\s*',
    r'(?:^|(?<=\.\s))\*\*[1-9]\.\s+[^*\n]+:?\*\*\s*',
    
    # ===========================================================================
    # PROMPT LEAKING PROTECTION (ADR-013)
    # Removes MANDATORY OPENING text that AI may copy literally from prompts
    # ===========================================================================
    
    r'^OMNIX valida cada fuente de datos de forma independiente y mantiene múltiples capas de resiliencia contra fallos de proveedores externos\.\s*',
    r'^OMNIX no genera señales sincronizadas a todos los usuarios\. Cada instancia opera de forma completamente aislada, sin observar posiciones de otros clientes\.\s*',
    r'^OMNIX implementa múltiples capas de defensa contra fallos de software y riesgos de despliegue\.\s*',
    r'^Desde una perspectiva de gobernanza y cumplimiento regulatorio, OMNIX mantiene una arquitectura auditible y transparente\.\s*',
    
    # ===========================================================================
    # INFLATED/UNAUDITABLE CAPITAL FIGURES (ADR-020 - Jan 21, 2026)
    # Removes large capital protection claims that cannot be verified on Day 7
    # ===========================================================================
    
    # Billions/millions in "capital protegido" - unauditable in early track record
    r'\$\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*(?:mil\s*millones|billones?|MM?)\s*(?:en\s+)?(?:capital\s+)?protegido[^.]*\.',
    r'\$\d{2,3}(?:,\d{3}){2,}(?:\.\d+)?\s*(?:en\s+)?(?:capital\s+)?protegido[^.]*\.',  # $82,940,000+
    r'\$\d+(?:,\d{3})*\s*(?:en\s+)?(?:las\s+últimas|últimas|en)\s*(?:\d+)?\s*(?:horas?|días?)[^.]*protegido[^.]*\.',
    
    # "Es difícil cuantificar" - ADR-018 says NEVER say this
    r'[Ee]s\s+dif[ií]cil\s+cuantificar[^.]*\.',
    r'[Dd]if[ií]cil\s+de\s+cuantificar[^.]*\.',
    
    # ===========================================================================
    # INVESTOR CHALLENGE EVASION PHRASES (ADR-024 - Jan 25, 2026)
    # Blocks phrases that evade quantified trade-off questions
    # HARDENED Jan 25, 2026 - Added preamble phrases that are "ruido"
    # ===========================================================================
    
    # "Estamos en fase de aprendizaje" - sounds like "trust us without data"
    r'[Ee]stamos\s+en\s+(?:una\s+)?fase\s+de\s+(?:aprendizaje|calibraci[oó]n|validaci[oó]n)[^.]*\.',
    r'[Ww]e\s*(?:\'re|are)\s+in\s+a?\s*learning\s+phase[^.]*\.',
    
    # "No es una comparación justa" - evasive
    r'[Nn]o\s+es\s+una\s+comparaci[oó]n\s+justa[^.]*\.',
    r'[Ii]t\s*(?:\'s|is)\s+not\s+a\s+fair\s+comparison[^.]*\.',
    
    # "Confía en el proceso" - zero substance
    r'[Cc]onf[ií]a\s+en\s+el\s+proceso[^.]*\.',
    r'[Tt]rust\s+the\s+process[^.]*\.',
    
    # "El mercado es impredecible" - obvious, doesn't answer
    r'[Ee]l\s+mercado\s+es\s+impredecible[^.]*\.',
    r'[Tt]he\s+market\s+is\s+unpredictable[^.]*\.',
    
    # ===========================================================================
    # PREAMBLE NOISE PHRASES (ADR-024 hardening - Jan 25, 2026)
    # These phrases are "ruido" - they don't answer the question
    # ===========================================================================
    
    # "Agradezco tu franqueza/honestidad" - servile preamble
    r'(?<=\.\s)Agradezco tu (?:franqueza|honestidad|transparencia)[^.]*\.\s*',
    r'^Agradezco tu (?:franqueza|honestidad|transparencia)[^.]*\.\s*',
    r'(?<=\.\s)Aprecio tu (?:franqueza|honestidad|transparencia)[^.]*\.\s*',
    r'^Aprecio tu (?:franqueza|honestidad|transparencia)[^.]*\.\s*',
    
    # "Es vital/importante/crucial comprender" - preamble without substance
    r'(?<=\.\s)Es (?:vital|importante|crucial|fundamental) (?:comprender|entender)[^.]*\.\s*',
    r'^Es (?:vital|importante|crucial|fundamental) (?:comprender|entender)[^.]*\.\s*',
    
    # "Permíteme explicar" - delays the answer
    r'(?<=\.\s)Perm[ií]teme explicar[^.]*\.\s*',
    r'^Perm[ií]teme explicar[^.]*\.\s*',
    r'(?<=\.\s)Deja(?:me)? que explique[^.]*\.\s*',
    r'^Deja(?:me)? que explique[^.]*\.\s*',
    
    # "Antes de responder" - preamble
    r'(?<=\.\s)Antes de responder[^.]*\.\s*',
    r'^Antes de responder[^.]*\.\s*',
    
    # "Comprendo tu preocupación" - empathy without substance
    r'(?<=\.\s)Comprendo tu (?:preocupaci[oó]n|inquietud|duda)[^.]*\.\s*',
    r'^Comprendo tu (?:preocupaci[oó]n|inquietud|duda)[^.]*\.\s*',
    
    # "Su nivel de escrutinio" / "Your level of scrutiny" - investor flattery (Feb 2026)
    r'(?<=\.\s)Su nivel de escrutinio[^.]*\.\s*',
    r'^Su nivel de escrutinio[^.]*\.\s*',
    r'(?<=\.\s)Your level of scrutiny[^.]*\.\s*',
    r'^Your level of scrutiny[^.]*\.\s*',
    r'(?<=\.\s)Tu nivel de escrutinio[^.]*\.\s*',
    r'^Tu nivel de escrutinio[^.]*\.\s*',
    
    # "OMNIX entiende la necesidad" - evasive preamble (Jan 25, 2026)
    r'^OMNIX entiende[^.]*\.\s*',
    r'(?<=\.\s)OMNIX entiende[^.]*\.\s*',
    
    # "Reconozco que mi respuesta anterior" - evasive (Jan 25, 2026)
    r'^Reconozco que[^.]*\.\s*',
    r'(?<=\.\s)Reconozco que[^.]*\.\s*',
    
    # Unrealistic thresholds - WR > 60%, ER > 1% (ADR-018 says realistic is WR > 50%, ER > 0%)
    r'win\s*rate[^.]*(?:superar|mayor|>\s*|superior\s*a\s*)6[05]%[^.]*\.',
    r'expected\s*return[^.]*(?:superar|mayor|>\s*|superior\s*a\s*)[1-9]%[^.]*\.',
]

BLACKLISTED_PATTERNS = [re.compile(pattern, re.IGNORECASE | re.MULTILINE) for pattern in BLACKLISTED_PHRASES]

# ==============================================================================
# INSTITUTIONAL LANGUAGE REPLACEMENTS (ADR-020 - Jan 21, 2026)
# Transforms arbitrary language into institutional governance terminology
# ==============================================================================

LANGUAGE_REPLACEMENTS = [
    # "ignorar módulos" → "ponderar adaptativamente" (governance, not arbitrariness)
    (re.compile(r'[Mm]ódulos?\s+(?:fueron?\s+)?ignorados?\s+conscientemente', re.IGNORECASE),
     'Las señales fueron ponderadas adaptativamente según el marco de gestión de riesgo'),
    (re.compile(r'[Ii]gnor[aó]\s+(?:los?\s+)?(?:módulos?|señales?)', re.IGNORECASE),
     'ponderó adaptativamente'),
    (re.compile(r'[Ss]e\s+ignor[aó]\s+conscientemente', re.IGNORECASE),
     'se redujo el peso relativo'),
    
    # "Es difícil cuantificar" → concrete range formula
    (re.compile(r'[Ee]s\s+dif[ií]cil\s+(?:de\s+)?cuantificar\s+(?:con\s+)?precisi[oó]n', re.IGNORECASE),
     'Bajo supuestos conservadores (Position_Size × max(VaR95, Avg_Loss)), el rango estimado es'),
    
    # Overly optimistic thresholds → realistic (ADR-018)
    (re.compile(r'win\s*rate\s*(?:debería|debe)\s*superar\s*el?\s*60%', re.IGNORECASE),
     'win rate debe superar el 52%'),
    (re.compile(r'expected\s*return\s*(?:debería|debe)\s*(?:ser\s*)?positivo?\s*\(?\s*>?\s*1%', re.IGNORECASE),
     'expected return debe ser positivo (>0%)'),
]

# ==============================================================================
# EVASION REPLACEMENTS (ADR-024 - Jan 25, 2026)
# Transforms evasive investor-challenge responses into framework references
# ==============================================================================

EVASION_REPLACEMENTS = [
    # "No es una comparación justa" → explain why with framework
    (re.compile(r'[Nn]o\s+es\s+una\s+comparaci[oó]n\s+justa(?:\s+porque)?', re.IGNORECASE),
     'La comparación requiere contexto: OMNIX es infraestructura de gobernanza, no competidor de BTC hold. Cuantificación:'),
    
    # "Confía en el proceso" → inject framework requirement
    (re.compile(r'[Cc]onf[ií]a\s+en\s+el\s+proceso', re.IGNORECASE),
     'El framework cuantifica: Position_Size × max(VaR95, Avg_Loss)'),
    
    # "El mercado es impredecible" → acknowledge but provide framework
    (re.compile(r'[Ee]l\s+mercado\s+es\s+impredecible(?:\s+pero)?', re.IGNORECASE),
     'Reconocemos la incertidumbre. Por eso usamos: Risk Avoided = Position_Size × max(VaR95, Avg_Loss).'),
    
    # "Estamos en fase de aprendizaje/calibración" → replace with current phase context
    (re.compile(r'[Ee]stamos\s+en\s+(?:una\s+)?fase\s+de\s+(?:aprendizaje|calibraci[oó]n)', re.IGNORECASE),
     'Fase 2 Multi-Vertical (desde Abril 1, 2026) en operación activa. El sistema SÍ ejecuta paper trades. Datos en tiempo real:'),
]

from omnix_services.ai_service.response_validator import (
    is_response_incomplete,
    validate_and_log_response,
    create_retry_prompt,
    should_retry_response,
    sanitize_incomplete_response,
)

TRACK_RECORD_DISCLOSURE_NOTE = """

---
**Nota de Período**: Los datos de trades/P&L corresponden al Learning Baseline (Nov 2025 - 14 Ene 2026), fase de calibración. Desde el 15 de enero 2026, el sistema opera con parámetros recalibrados en el Track Record Oficial."""

TRADING_CONTEXT_KEYWORDS = [
    'trade', 'trades', 'trading', 'p&l', 'pnl', 'profit', 'loss',
    'win rate', 'winrate', 'pérdida', 'ganancia', 'operacion', 'operaciones',
    'balance', 'equity', 'drawdown', 'dd', 'retorno', 'return',
    'ada/usd', 'sol/usd', 'link/usd', 'btc/usd', 'eth/usd', 'xrp/usd',
    'rentabilidad', 'capital', 'inversión', 'inversion',
    '119 trades', 'baseline', 'track record',
]

TRADING_METRICS_PATTERNS = [
    r'(?:p&l|pnl|profit|loss|pérdida|ganancia)[:\s]*[-]?\$?\d+',
    r'(?:win\s*rate|winrate)[:\s]*\d+\.?\d*\s*%',
    r'\d+\s*trades?\b',
    r'(?:balance|equity|capital)[:\s]*\$?\d+',
    r'(?:drawdown|dd)[:\s]*[-]?\d+\.?\d*\s*%',
    r'(?:retorno|return)[:\s]*[-]?\d+\.?\d*\s*%',
    r'(?:ada|sol|link|btc|eth|xrp)/usd[:\s]*[-]?\$?\d+',
    r'-\$\d+[,\.]?\d*\s*(?:usd|pérdida|loss)',
]

def _contains_trading_metrics(text: str) -> bool:
    """
    Check if response contains trading-specific metrics that require disclosure.
    Only triggers for trading context, not generic percentages or dollar amounts.
    """
    text_lower = text.lower()
    
    has_trading_context = any(keyword in text_lower for keyword in TRADING_CONTEXT_KEYWORDS)
    if not has_trading_context:
        return False
    
    for pattern in TRADING_METRICS_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    
    if re.search(r'\d+\s*trades?\b', text_lower):
        return True
    if re.search(r'(?:win\s*rate|winrate)', text_lower):
        return True
    if 'p&l' in text_lower or 'pnl' in text_lower:
        return True
    
    if any(kw in text_lower for kw in ['pérdida', 'ganancia', 'loss', 'profit']) and re.search(r'\$\d+', text_lower):
        return True
    if any(kw in text_lower for kw in ['retorno', 'return', 'track record', 'baseline']) and re.search(r'-?\d+\.?\d*\s*%', text_lower):
        return True
    if any(pair in text_lower for pair in ['ada/usd', 'sol/usd', 'link/usd', 'btc/usd', 'eth/usd', 'xrp/usd']) and re.search(r'\$\d+', text_lower):
        return True
    
    return False

def _has_disclosure_note(text: str) -> bool:
    """Check if response already contains the disclosure note."""
    disclosure_indicators = [
        'nota de período',
        'nota de periodo',
        'learning baseline',
        'track record oficial',
        '15 de enero 2026',
        '15 enero 2026',
        'fase de calibración',
        'fase de calibracion',
    ]
    text_lower = text.lower()
    return any(indicator in text_lower for indicator in disclosure_indicators)

GREETING_PATTERNS = [
    r'^hola\b', r'^hey\b', r'^buenas?\b', r'^buenos?\s', r'^saludos?\b',
    r'^hi\b', r'^hello\b', r'^qu[eé]\s+tal\b', r'^c[oó]mo\s+est[aá]s',
    r'^amigo\b', r'^caballero\b', r'^bro\b', r'^hermano\b',
    r'^hola\s+(?:amigo|caballero|hermano|bro)\b',
]

MARKET_PATTERNS = [
    r'mercado', r'market', r'bitcoin', r'btc', r'ethereum', r'eth',
    r'precio', r'price', r'cotiza', r'tendencia', r'trend',
    r'hoy', r'today', r'cripto', r'crypto', r'acci[oó]n', r'stock',
    r'bull', r'bear', r'alcist', r'bajist',
]

TECHNICAL_PATTERNS = [
    r'especificacion', r'specification', r't[eé]cnic[ao]', r'technical',
    r'arquitectura', r'architecture', r'infraestructura', r'infrastructure',
    r'm[oó]dulo', r'module', r'kernel', r'motor\s+de', r'engine',
    r'algoritm', r'algorithm', r'monte\s*carlo', r'kalman', r'markov',
    r'coherencia', r'coherence', r'veto', r'scoring', r'checkpoint',
    r'c[oó]digo', r'code', r'api\b', r'detalle', r'detail', r'profundidad',
    r'explica.*c[oó]mo\s+funciona', r'explain.*how.*works',
]

FUNCTIONALITY_PATTERNS = [
    r'qu[eé]\s+sabes\s+hacer', r'qu[eé]\s+puedes\s+hacer',
    r'funcionalidad', r'functionality', r'feature',
    r'capacidad', r'capability', r'habilidad',
    r'para\s+qu[eé]\s+sirves', r'what\s+can\s+you\s+do',
    r'dime.*funcionalidad', r'cu[aá]les\s+son\s+tus',
]


def _classify_message_context(user_message: str) -> str:
    if not user_message:
        return 'casual'
    msg = user_message.strip().lower()

    if len(msg) < 30 and any(re.search(p, msg) for p in GREETING_PATTERNS):
        return 'greeting'

    if any(re.search(p, msg) for p in TECHNICAL_PATTERNS):
        return 'technical'

    if any(re.search(p, msg) for p in FUNCTIONALITY_PATTERNS):
        return 'overview'

    if any(re.search(p, msg) for p in MARKET_PATTERNS):
        return 'market'

    if len(msg) < 40:
        return 'casual'

    return 'general'


def compress_response_contextual(response: str, user_message: str) -> str:
    if not response or not user_message:
        return response

    context = _classify_message_context(user_message)
    logger.info(f"🗜️ [COMPRESS] Message context: {context} | Input: {len(response)} chars")

    if context == 'technical':
        return response

    lines = [l for l in response.split('\n') if l.strip()]

    if context == 'greeting':
        first_line = lines[0] if lines else ""
        sentences = re.split(r'(?<=[.!?])\s+', first_line)
        kept = []
        for s in sentences[:3]:
            if re.search(r'K\(t-s\)|τ=|ε=|Ω=|exp\(-|\d+\s*pts|rad/periodo', s):
                continue
            if re.search(r'funcionalidad\s+central|propósito\s+fundamental|articulan\s+en', s, re.IGNORECASE):
                continue
            if re.search(r'infraestructura|gobernanza|governance|architecture|consolidad[ao]|operativo', s, re.IGNORECASE):
                continue
            if re.search(r'mercado|market|bitcoin|btc|precio|price|\$\d', s, re.IGNORECASE):
                continue
            if len(s) > 150:
                s = s[:150].rsplit(' ', 1)[0] + '.'
            kept.append(s)
        if not kept:
            kept = ["¡Hola! ¿En qué puedo ayudarte hoy?"]
        result = ' '.join(kept)
        if len(result) > 200:
            result = "¡Hola! ¿En qué puedo ayudarte hoy?"
        logger.info(f"🗜️ [COMPRESS] greeting: {len(response)} → {len(result)} chars")
        return result

    if context == 'overview':
        core_lines = []
        for line in lines:
            if re.search(r'K\(t-s\)|τ=|ε=|Ω=|exp\(-|rad/periodo', line):
                continue
            if re.search(r'\(\d+\s*pts?\)', line):
                continue
            if len(line) > 300:
                sentences = re.split(r'(?<=[.!?])\s+', line)
                line = ' '.join(sentences[:2])
            core_lines.append(line)
        result = '\n'.join(core_lines[:8])
        if len(result) > 1200:
            sentences = re.split(r'(?<=[.!?])\s+', result)
            result = ' '.join(sentences[:8])
        logger.info(f"🗜️ [COMPRESS] overview: {len(response)} → {len(result)} chars")
        return result

    if context == 'market':
        core_lines = []
        for line in lines:
            if re.search(r'K\(t-s\)|τ=|ε=|Ω=|exp\(-|rad/periodo', line):
                continue
            if re.search(r'funcionalidad\s+central|propósito\s+fundamental|articulan\s+en', line, re.IGNORECASE):
                continue
            if re.search(r'\(\d+\s*pts?\)', line):
                continue
            core_lines.append(line)
        result = '\n'.join(core_lines[:8])
        if len(result) > 1500:
            sentences = re.split(r'(?<=[.!?])\s+', result)
            result = ' '.join(sentences[:10])
        logger.info(f"🗜️ [COMPRESS] market: {len(response)} → {len(result)} chars")
        return result

    if context in ('casual', 'general'):
        core_lines = []
        for line in lines:
            if re.search(r'K\(t-s\)|τ=|ε=|Ω=|exp\(-|rad/periodo', line):
                continue
            if re.search(r'\(\d+\s*pts?\)', line):
                continue
            if len(line) > 300:
                sentences = re.split(r'(?<=[.!?])\s+', line)
                line = ' '.join(sentences[:2])
            core_lines.append(line)
        result = '\n'.join(core_lines[:8])
        if len(result) > 1200:
            sentences = re.split(r'(?<=[.!?])\s+', result)
            result = ' '.join(sentences[:8])
        logger.info(f"🗜️ [COMPRESS] {context}: {len(response)} → {len(result)} chars")
        return result

    return response


def post_process_response(response: str) -> str:
    """
    Remove blacklisted phrases and apply institutional language transforms.
    This is a safety net that runs AFTER AI generation.
    
    ADR-020: Includes inflated capital figure removal, unrealistic threshold correction,
    and "ignorar" → "ponderar adaptativamente" transformations.
    
    ADR-023: Adds mandatory Track Record Disclosure when metrics are mentioned.
    
    ADR-024: Includes investor challenge evasion phrase replacements that transform
    evasive responses into framework-referenced quantifications.
    
    Args:
        response: Raw AI response text
        
    Returns:
        Cleaned response with servile/prohibited phrases removed and 
        institutional language applied
    """
    if not response:
        return response
    
    cleaned = response
    changes_made = []
    
    # Phase 1: Remove blacklisted patterns (servile phrases, inflated figures)
    for pattern in BLACKLISTED_PATTERNS:
        if pattern.search(cleaned):
            cleaned = pattern.sub('', cleaned)
            changes_made.append('blacklist_removal')
    
    # Phase 2: Apply institutional language replacements (ADR-020)
    for pattern, replacement in LANGUAGE_REPLACEMENTS:
        if pattern.search(cleaned):
            cleaned = pattern.sub(replacement, cleaned)
            changes_made.append('language_transform')
    
    # Phase 3: Apply evasion replacements for investor challenge responses (ADR-024)
    for pattern, replacement in EVASION_REPLACEMENTS:
        if pattern.search(cleaned):
            cleaned = pattern.sub(replacement, cleaned)
            changes_made.append('evasion_replacement')
    
    # Phase 4: Add Track Record Disclosure if metrics present but no disclosure (ADR-023)
    if _contains_trading_metrics(cleaned) and not _has_disclosure_note(cleaned):
        cleaned = cleaned.rstrip() + TRACK_RECORD_DISCLOSURE_NOTE
        changes_made.append('track_record_disclosure_added')
        logger.info("📋 ADR-023: Track Record Disclosure note added to response with metrics")
    
    # Clean up stray Telegram formatting artifacts (lone asterisks)
    cleaned = re.sub(r'^\s*\*\s*$', '', cleaned, flags=re.MULTILINE)
    
    # Clean up multiple consecutive newlines (max 2)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    # Clean up leading whitespace/punctuation after removal (but preserve asterisks for bullet lists)
    cleaned = re.sub(r'^[\s,.]+', '', cleaned)
    
    # Ensure first character is uppercase if we removed something
    if cleaned and cleaned[0].islower():
        cleaned = cleaned[0].upper() + cleaned[1:] if len(cleaned) > 1 else cleaned.upper()
    
    # Log if we made changes (for debugging)
    if changes_made:
        unique_changes = list(set(changes_made))
        logger.info(f"🛡️ Post-process filter applied: {', '.join(unique_changes)}")
    
    return cleaned.strip()

# ==============================================================================
# SYSTEMIC FRAMING ROUTER (ADR-013)
# Deterministic classification of systemic questions into 4 types:
# TYPE_A: Coordination / Synchronization (signal coordination, mass selling)
# TYPE_B: Software / Deployment (code defects, bugs, versioning)
# TYPE_C: Dependencies (API failures, provider issues, data inconsistency)
# TYPE_D: Governance (regulatory, compliance, audits)
# ==============================================================================

SYSTEMIC_TYPE_A_KEYWORDS = [
    '10,000 usuarios', '10000 usuarios', '10k usuarios',
    'miles de usuarios', 'millones de usuarios',
    'venta simultánea', 'venta simultanea', 'ventas simultáneas',
    'venta masiva', 'ventas masivas',
    'vendieran simultáneamente', 'vendieran simultaneamente',
    'vendiendo simultáneamente', 'vendiendo simultaneamente',
    'señal simultánea', 'senal simultanea', 'señales simultáneas',
    'todos reciben', 'todos vendiendo', 'all receive',
    'todos los usuarios', 'all users',
    'señal de venta', 'senal de venta', 'sell signal',
    'misma señal', 'same signal',
    'coordinación', 'coordinacion', 'coordination',
    'efecto manada', 'herd effect', 'herding',
    'impacto en el mercado', 'market impact',
    'riesgo sistémico', 'riesgo sistemico', 'systemic risk',
    'actor sistémico', 'actor sistemico', 'systemic actor',
    'macroprudencial', 'macroprudential',
    'penetración sistémica', 'penetracion sistemica',
    'infraestructura dominante', 'dominant infrastructure',
    'múltiples instituciones', 'multiple institutions',
]

SYSTEMIC_TYPE_B_KEYWORDS = [
    'defecto lógico', 'defecto logico', 'logic defect',
    'bug', 'error en el código', 'error en el codigo',
    'código base', 'codigo base', 'code base', 'codebase',
    'versión del modelo', 'version del modelo', 'model version',
    'despliegue', 'deployment', 'deploy',
    'patch', 'parche',
    'actualización de software', 'actualizacion de software',
    'miles de instancias', 'thousands of instances',
    'mismo código', 'mismo codigo', 'same code',
]

SYSTEMIC_TYPE_C_KEYWORDS = [
    'proveedores externos', 'external providers', 'third-party providers',
    'api degradation', 'degradación de api', 'degradacion de api',
    'datos inconsistentes', 'inconsistent data',
    'fallo silencioso', 'silent failure', 'silent fail',
    'comportamiento incorrecto del proveedor', 'incorrect provider behavior',
    'hard failure', 'soft failure',
    'fallo de kraken', 'kraken down', 'kraken failure',
    'fallo del exchange', 'exchange failure', 'exchange down',
    'dependencia de proveedores', 'provider dependency',
    'infraestructura cloud falla', 'cloud infrastructure failure',
    'proveedor reporta incorrectamente', 'provider reports incorrectly',
    'fuente de datos corrupta', 'corrupted data source',
    'sin hard failure', 'without hard failure',
]

SYSTEMIC_TYPE_D_KEYWORDS = [
    'regulador', 'regulator', 'regulatory',
    'compliance', 'cumplimiento',
    'auditoría', 'auditoria', 'audit',
    'responsabilidad fiduciaria', 'fiduciary',
    'sec', 'mifid', 'sharia',
    'legal', 'jurisdicción', 'jurisdiccion', 'jurisdiction',
    'gobernanza', 'governance',
    'seguridad', 'security', 'criptografía', 'cryptography',
    'post-quantum', 'post-cuántico', 'post-cuantico', 'pqc',
    'quantum', 'cuántico', 'cuantico',
    'kyber', 'dilithium', 'encryption', 'encriptación', 'encriptacion',
    'firma digital', 'digital signature', 'firmas digitales',
]

SYSTEMIC_OVERRIDE_COORDINATION = """
## SYSTEMIC OVERRIDE - TYPE A: COORDINATION/SYNCHRONIZATION [MANDATORY]

**LANGUAGE RULE:** ALWAYS respond in the same language the user is using. If they ask in Spanish, respond in Spanish. If they ask in English, respond in English.

**QUESTION_TYPE: COORDINATION**

**RESPONSE FOCUS:** Explica que el escenario de coordinación NO puede ocurrir porque OMNIX usa arquitectura single-tenant - cada instancia opera independientemente sin observar posiciones de otros clientes.

**DO NOT copy instructions literally - write naturally using these concepts.**

**CORE MESSAGE:**
The scenario cannot happen because there is NO coordination mechanism by design.
- Arquitectura single-tenant por diseño
- No existe mecanismo de coordinación entre clientes
- El sistema no observa posiciones agregadas
- Fail-closed = INACCIÓN, no presión de mercado

**ABSOLUTELY FORBIDDEN:**
❌ Numbered sections: "*1.", "*2.", "1. Análisis", "2. Datos Técnicos"
❌ Section headers: "Análisis Inmediato:", "Datos Técnicos:", "Contexto:"
❌ Kelly Criterion / Position sizing / Leverage limits
❌ Monte Carlo for market impact
❌ Win rate / ROI / trade statistics
❌ "Desfase temporal de señales" (implies coordination exists)
❌ "Circuit breakers" for mass selling (implies scenario is possible)
❌ Percentages of market impact (2%, 5%, 20%)
❌ "$1,000,000" or large arbitrary figures

**RESPONSE FORMAT:**
- Write in FLOWING PARAGRAPHS, not numbered lists
- Be CONCISE: 3-4 paragraphs maximum
- Professional, direct tone

**MONITORING CLARIFICATION (if mentioned):**
"telemetría técnica agregada, sin influencia en decisiones operativas"

NOW RESPOND USING THIS FRAME:
"""

SYSTEMIC_OVERRIDE_SOFTWARE = """
## SYSTEMIC OVERRIDE - TYPE B: SOFTWARE/DEPLOYMENT [MANDATORY]

**LANGUAGE RULE:** ALWAYS respond in the same language the user is using. If they ask in Spanish, respond in Spanish. If they ask in English, respond in English.

**QUESTION_TYPE: SOFTWARE**

**RESPONSE FOCUS:** Explica cómo OMNIX implementa múltiples capas de defensa contra fallos de software y riesgos de despliegue.

**DO NOT open with "OMNIX no genera señales sincronizadas..." - that is for coordination questions, not software questions.
DO NOT copy instructions literally - write naturally using these concepts.**

**REQUIRED CONCEPTS:**
- Canary releases: nuevas versiones se despliegan al 1-5% primero
- Kill switches globales: parada de emergencia instantánea
- Versionado de modelos: rollback en segundos si se detecta problema
- Fail-closed: ante anomalías, el sistema para (no actúa)
- Separación modelo / ejecución
- Tests automatizados antes de cada despliegue

**ABSOLUTELY FORBIDDEN:**
❌ Numbered sections: "*1.", "*2.", "1. Análisis", "2. Datos Técnicos"
❌ Section headers: "Análisis Inmediato:", "Datos Técnicos:", "Contexto:"
❌ Kelly Criterion / Position sizing / trading statistics
❌ "$1,000,000" or large arbitrary figures
❌ "Adaptive Parameter Engine"

**RESPONSE FORMAT:**
- Write in FLOWING PARAGRAPHS, not numbered lists
- Be CONCISE: 3-4 paragraphs maximum
- Professional, direct tone

NOW RESPOND USING THIS FRAME:
"""

SYSTEMIC_OVERRIDE_DEPENDENCIES = """
## SYSTEMIC OVERRIDE - TYPE C: DEPENDENCIES/PROVIDERS [MANDATORY]

**LANGUAGE RULE:** ALWAYS respond in the same language the user is using. If they ask in Spanish, respond in Spanish. If they ask in English, respond in English.

**QUESTION_TYPE: DEPENDENCIES**

**RESPONSE FOCUS:** Validación de datos y resiliencia de proveedores. Comienza explicando cómo OMNIX valida fuentes de datos de forma independiente.

**DO NOT open with "OMNIX no genera señales sincronizadas..." - that is for coordination questions, not dependency questions.
DO NOT copy instructions literally - write naturally using these concepts.**

**REQUIRED CONCEPTS (include ALL relevant ones):**

1. TIMESTAMP VALIDATION (Silent Failure Detection):
   - Validamos timestamps de cada dato recibido
   - Precios con timestamp >60 segundos = stale data, descartados
   - Detecta APIs que devuelven último precio conocido en caché

2. CROSS-VALIDATION WITH CONCRETE THRESHOLDS:
   - Comparamos precios de múltiples fuentes en tiempo real
   - Discrepancia >3% entre Kraken y CoinGecko = pausa operativa
   - Tercera fuente (Binance) resuelve empates si necesario

3. VOLUME SANITY CHECKS:
   - Volúmenes comparados con promedios históricos
   - Volumen 10x superior al promedio sin evento conocido = anomalía
   - Sistema suspende hasta confirmación

4. SINGLE-TENANT LIMITATION (HONESTY):
   - Single-tenant aísla fallos de configuración entre clientes
   - PERO: Fallo en fuente compartida (ej: Kraken API) afecta múltiples instancias
   - Mitigamos con diversificación de proveedores y circuit breakers

5. RESIDUAL RISK (TRANSPARENCY):
   - Si TODOS los proveedores reportan incorrectamente (evento sistémico)...
   - OMNIX NO tiene fuente externa de verdad para validar
   - Postura: Fail-closed + intervención humana requerida

6. FUTURE ROADMAP:
   - Integración futura: Oráculos blockchain descentralizados
   - Chainlink, Band Protocol como validación adicional

**ABSOLUTELY FORBIDDEN:**
❌ Numbered sections: "*1.", "*2.", "1. Análisis", "2. Datos Técnicos"
❌ Section headers: "Análisis Inmediato:", "Datos Técnicos:", "Contexto:"
❌ Kelly Criterion / Position sizing / trading statistics
❌ "$1,000,000" or large arbitrary figures
❌ Claiming 100% protection (acknowledge residual risk)

**RESPONSE FORMAT:**
- Write in FLOWING PARAGRAPHS, not numbered lists
- Be CONCISE: 3-4 paragraphs maximum
- Professional, direct tone
- Include concrete thresholds when mentioning detection
- Acknowledge limitations honestly

NOW RESPOND USING THIS FRAME:
"""

SYSTEMIC_OVERRIDE_GOVERNANCE = """
## SYSTEMIC OVERRIDE - TYPE D: GOVERNANCE/COMPLIANCE/SECURITY [MANDATORY]

**LANGUAGE RULE:** ALWAYS respond in the same language the user is using. If they ask in Spanish, respond in Spanish. If they ask in English, respond in English.

**QUESTION_TYPE: GOVERNANCE / SECURITY**

**RESPONSE FOCUS:** Desde una perspectiva de gobernanza, cumplimiento regulatorio y seguridad, explica cómo OMNIX mantiene una arquitectura auditable, transparente y segura.

**DO NOT open with "OMNIX no genera señales sincronizadas..." - that is for coordination questions, not governance questions.
DO NOT copy instructions literally - write naturally using these concepts.**

**CRITICAL POST-QUANTUM CRYPTOGRAPHY (PQC) FACTS:**
⚠️ PQC YA ESTÁ IMPLEMENTADO - NO es roadmap, NO es planificado para el futuro
- **IMPLEMENTADO**: Nov 2025 - Módulo operativo con pypqc library
- **Intercambio de Claves (KEM)**: Kyber-768 (ML-KEM-768) — algoritmo NIST-estandarizado para encapsulación de claves (NO cifrado de datos; el cifrado de payload usa AES/Fernet)
- **Firmas Digitales**: Dilithium-3 (ML-DSA-65) — algoritmo NIST-estandarizado para firmas digitales
- **Nivel de Seguridad**: Resistencia cuántica robusta — algoritmos estandarizados por NIST
- **Integración Trading**: Órdenes de trading firmadas con Dilithium-3 antes de ejecución
- Cada orden incluye: pqc_signed: true, pqc_algorithm: Dilithium-3

**NEVER SAY THESE (FORBIDDEN - INCORRECT):**
❌ "PQC planificado para Q3 2026" - WRONG, it's implemented
❌ "actualmente NO implementamos criptografía post-cuántica" - WRONG
❌ "TLS 1.3 mientras esperamos PQC" - WRONG, PQC is active
❌ "hoja de ruta incluye Kyber/Dilithium" - WRONG, already deployed
❌ "decoherencia térmica" or physics jargon unrelated to PQC implementation

**REQUIRED CONCEPTS:**
- Trazabilidad completa de decisiones (decision_trace)
- Logs inmutables para auditoría
- Separación de roles y permisos
- Arquitectura documentada y reproducible
- Cumplimiento con estándares de la industria
- Criptografía post-cuántica IMPLEMENTADA (Kyber-768, Dilithium-3)

**ABSOLUTELY FORBIDDEN:**
❌ Numbered sections: "*1.", "*2.", "1. Análisis", "2. Datos Técnicos"
❌ Section headers: "Análisis Inmediato:", "Datos Técnicos:", "Contexto:"
❌ Trading statistics unless specifically asked
❌ "$1,000,000" or large arbitrary figures
❌ Saying PQC is "planned", "roadmap", or "future" - IT IS IMPLEMENTED

**RESPONSE FORMAT:**
- Write in FLOWING PARAGRAPHS, not numbered lists
- Be CONCISE: 3-4 paragraphs maximum
- Professional, direct tone

NOW RESPOND USING THIS FRAME:
"""

PURE_FOLLOWUP_PATTERNS = [
    'que mas', 'qué más', 'que más', 'qué mas',
    'por que', 'por qué', 'porque', 'porqué',
    'y que', 'y qué', 'y entonces', 'y luego',
    'continua', 'continúa', 'sigue', 'adelante',
    'entiendo', 'gracias', 'thanks', 'thank you',
    'what else', 'tell me more', 'go on', 'continue',
    'and then', 'what next', 'next', 'why',
]

CONFIRMATION_PATTERNS = [
    'ok', 'okay', 'vale', 'bien', 'claro', 'perfecto',
    'de acuerdo', 'entendido', 'got it', 'understood',
]

ALL_SYSTEMIC_KEYWORDS = (
    SYSTEMIC_TYPE_A_KEYWORDS + 
    SYSTEMIC_TYPE_B_KEYWORDS + 
    SYSTEMIC_TYPE_C_KEYWORDS + 
    SYSTEMIC_TYPE_D_KEYWORDS
)

def is_short_followup_question(message: str) -> bool:
    """
    Detect if message is a short follow-up question that should NOT trigger systemic overrides.
    These are contextual continuations, not new questions requiring classification.
    
    IMPORTANT: Short messages that contain systemic keywords still get classified normally.
    Only pure follow-ups without domain keywords are excluded.
    
    Args:
        message: User's message text
        
    Returns:
        True if this is a short follow-up without systemic keywords, False otherwise
    """
    message_lower = message.lower().strip()
    
    if len(message_lower) > 25:
        return False
    
    for kw in ALL_SYSTEMIC_KEYWORDS:
        if kw.lower() in message_lower:
            logger.debug(f"🔍 Short message contains systemic keyword '{kw}' - Will classify normally")
            return False
    
    for pattern in PURE_FOLLOWUP_PATTERNS:
        if pattern in message_lower or message_lower == pattern:
            logger.info(f"🔄 FOLLOW-UP DETECTED: '{message_lower}' matches pattern '{pattern}' - Skipping systemic classification")
            return True
    
    for pattern in CONFIRMATION_PATTERNS:
        if message_lower == pattern or message_lower == pattern + '?':
            logger.info(f"🔄 CONFIRMATION DETECTED: '{message_lower}' - Skipping systemic classification")
            return True
    
    return False

def classify_systemic_question(message: str) -> Optional[str]:
    """
    Classify systemic question into type A/B/C/D based on keywords.
    Priority order: A (Coordination) > D (Governance) > C (Dependencies) > B (Software)
    
    SPECIAL RULE: If TYPE_C keywords (providers/dependencies) are present alongside
    TYPE_A keywords, TYPE_C takes precedence. This handles questions like:
    "What if a provider failure affects thousands of instances?" which is about
    provider resilience (TYPE_C), not coordination (TYPE_A).
    
    FOLLOW-UP PROTECTION: Short follow-up questions like "que mas" or "por que"
    are excluded from classification to prevent repeating the same override.
    
    Args:
        message: User's message text
        
    Returns:
        'TYPE_A', 'TYPE_B', 'TYPE_C', 'TYPE_D', or None if not systemic
    """
    if is_short_followup_question(message):
        return None
    
    message_lower = message.lower()
    
    has_type_a = any(kw.lower() in message_lower for kw in SYSTEMIC_TYPE_A_KEYWORDS)
    has_type_c = any(kw.lower() in message_lower for kw in SYSTEMIC_TYPE_C_KEYWORDS)
    
    if has_type_c and has_type_a:
        for kw in SYSTEMIC_TYPE_C_KEYWORDS:
            if kw.lower() in message_lower:
                logger.info(f"🔍 SYSTEMIC TYPE_C (Dependencies) OVERRIDE: keyword '{kw}' found (TYPE_A also present but C takes precedence for provider questions)")
                return 'TYPE_C'
    
    for kw in SYSTEMIC_TYPE_A_KEYWORDS:
        if kw.lower() in message_lower:
            logger.info(f"🔍 SYSTEMIC TYPE_A (Coordination): keyword '{kw}' found")
            return 'TYPE_A'
    
    for kw in SYSTEMIC_TYPE_D_KEYWORDS:
        if kw.lower() in message_lower:
            logger.info(f"🔍 SYSTEMIC TYPE_D (Governance): keyword '{kw}' found")
            return 'TYPE_D'
    
    for kw in SYSTEMIC_TYPE_C_KEYWORDS:
        if kw.lower() in message_lower:
            logger.info(f"🔍 SYSTEMIC TYPE_C (Dependencies): keyword '{kw}' found")
            return 'TYPE_C'
    
    for kw in SYSTEMIC_TYPE_B_KEYWORDS:
        if kw.lower() in message_lower:
            logger.info(f"🔍 SYSTEMIC TYPE_B (Software): keyword '{kw}' found")
            return 'TYPE_B'
    
    return None

def detect_systemic_question(message: str) -> bool:
    """
    Detect if user is asking about systemic risk (any type).
    
    Args:
        message: User's message text
        
    Returns:
        True if systemic question detected, False otherwise
    """
    return classify_systemic_question(message) is not None

def get_systemic_override_prompt(question_type: Optional[str] = None) -> str:
    """
    Get the appropriate override prompt for the systemic question type.
    
    Args:
        question_type: 'TYPE_A', 'TYPE_B', 'TYPE_C', 'TYPE_D', or None
        
    Returns:
        Type-specific override prompt string, or empty string if None
    """
    if question_type == 'TYPE_A':
        return SYSTEMIC_OVERRIDE_COORDINATION
    elif question_type == 'TYPE_B':
        return SYSTEMIC_OVERRIDE_SOFTWARE
    elif question_type == 'TYPE_C':
        return SYSTEMIC_OVERRIDE_DEPENDENCIES
    elif question_type == 'TYPE_D':
        return SYSTEMIC_OVERRIDE_GOVERNANCE
    return ""

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
    # CRITICAL: never alias Exception — that would swallow ALL errors as rate-limit messages.
    # Use a private sentinel that can only be raised explicitly.
    class RateLimitExceeded(Exception):  # noqa: N818
        """Sentinel — only raised by rate limiter, never by accident."""
        pass

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
            self.model_name = "gemini-2.0-flash"
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
                _openai_disabled = os.environ.get('OMNIX_DISABLE_OPENAI', 'false').lower() == 'true'
                if not _openai_disabled and OPENAI_AVAILABLE and os.environ.get('OPENAI_API_KEY'):
                    self.openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
                    logger.info("✅ OpenAI GPT-4o inicializado correctamente")
                elif _openai_disabled:
                    logger.info("ℹ️  OpenAI deshabilitado via OMNIX_DISABLE_OPENAI=true (legacy path)")

                if GEMINI_AVAILABLE and os.environ.get('GEMINI_API_KEY'):
                    if GEMINI_SDK_VERSION == 'new':
                        self.gemini_client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
                        logger.info("✅ Gemini 2.0 Flash inicializado con NUEVO SDK (google-genai)")
                    else:
                        genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
                        self.gemini_client = genai.GenerativeModel('gemini-2.0-flash')
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
            from omnix_services.ai_service.input_sanitizer import sanitize_user_message as _sanitize
            user_message, _san_flags = _sanitize(user_message)
            if _san_flags:
                logger.warning(f"[ISR-017] Async input sanitized — flags={_san_flags}")
        except Exception:
            pass
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
                
                try:
                    real_market_data = await asyncio.wait_for(
                        self._fetch_real_market_data_async(trading_system, user_message, user_id=user_id),
                        timeout=10.0
                    )
                except (asyncio.TimeoutError, Exception) as _mde:
                    logger.warning(f"⚠️ [ASYNC] Market data fetch failed ({type(_mde).__name__}) — continuing without market data")
                    real_market_data = {'market_data_unavailable': True}
                
                # V6.5.4e: SYSTEMIC FRAMING ROUTER (ADR-013) - Classify and inject type-specific override
                effective_user_message = user_message
                systemic_type = classify_systemic_question(user_message)
                if systemic_type:
                    logger.info(f"🔍 [ASYNC] SYSTEMIC {systemic_type} DETECTED - Injecting type-specific override")
                    systemic_override = get_systemic_override_prompt(systemic_type)
                    # Prepend override BEFORE user message for maximum influence
                    effective_user_message = systemic_override + "\n\nUSER QUESTION: " + user_message
                
                max_retries = 1
                retry_count = 0
                current_message = effective_user_message
                
                while retry_count <= max_retries:
                    try:
                        result = await asyncio.wait_for(
                            self.enterprise_service.generate_response(
                                chat_id=chat_id_int,
                                user_message=current_message,
                                user_name=user_name,
                                market_data=real_market_data,
                                apply_visual_style=True,
                                diagnostic_mode=diagnostic_mode
                            ),
                            timeout=45.0
                        )
                    except asyncio.TimeoutError:
                        logger.error("❌ Enterprise service timed out after 45s — using fallback")
                        result = None
                    except BaseException as _be:
                        if isinstance(_be, (KeyboardInterrupt, SystemExit)):
                            raise
                        logger.error(f"❌ Enterprise service raised [{type(_be).__name__}]: {_be}", exc_info=True)
                        result = None
                    
                    if result and 'response' in result:
                        response_text = result['response']
                        
                        is_valid, reason, _ = validate_and_log_response(
                            response_text, 
                            user_message, 
                            provider="enterprise"
                        )
                        
                        if not is_valid and retry_count < max_retries:
                            retry_count += 1
                            logger.warning(f"🔄 [RETRY {retry_count}/{max_retries}] Response incomplete: {reason}")
                            current_message = create_retry_prompt(user_message, reason)
                            continue
                        
                        if not is_valid:
                            logger.warning(f"⚠️ Accepting incomplete response after {retry_count} retries")
                            response_text = sanitize_incomplete_response(response_text)
                        
                        if result.get('web_search_used'):
                            web_indicator = "\n\n🔍 *Real-time verified information*"
                            if "verified information" not in response_text.lower():
                                response_text = response_text + web_indicator
                            logger.info(f"🔍 Web search used")
                        
                        return post_process_response(response_text)
                    else:
                        # FIX: Enterprise falló → caer al legacy path en lugar de fallback estático
                        logger.warning("⚠️ Enterprise service returned no response — falling through to legacy AI path")
                        break
                
                # Enterprise falló completamente — intentar legacy (Gemini/GPT-4)
                logger.warning("⚠️ [ASYNC] Enterprise path exhausted — trying legacy AI generation")
                try:
                    legacy_response = self._legacy_generate_response(user_message, user_name, chat_id, user_id, trading_system, diagnostic_mode=diagnostic_mode)
                    if legacy_response and legacy_response != self._fallback_response():
                        return post_process_response(legacy_response)
                except Exception as _leg_exc:
                    logger.error(f"❌ Legacy path also failed: {_leg_exc}")
                return self._fallback_response()
            else:
                logger.warning("⚠️ Using legacy AI generation")
                return post_process_response(self._legacy_generate_response(user_message, user_name, chat_id, user_id, trading_system, diagnostic_mode=diagnostic_mode))
        except RateLimitExceeded as e:
            logger.warning(f"⚠️ Rate limit exceeded: {e}")
            import re as _re
            _m = _re.search(r"Resets in (\d+)s", str(e))
            _reset = f" Intenta de nuevo en {_m.group(1)} segundos." if _m else " Por favor espera un momento."
            return f"⏳ Demasiadas solicitudes al servicio IA.{_reset}"
        except asyncio.CancelledError:
            logger.warning("⚠️ Response generation cancelled (Telegram timeout)")
            return self._fallback_response()
        except asyncio.TimeoutError:
            logger.error("❌ Response generation timed out at outer level")
            return self._fallback_response()
        except Exception as e:
            logger.error(f"❌ Error generating async response [{type(e).__name__}]: {e}", exc_info=True)
            return self._fallback_response()
    
    def generate_response(self, user_message, user_name="Usuario", chat_id="", user_id=None, trading_system=None):
        """
        🚀 ENTERPRISE-GRADE RESPONSE GENERATION (SYNC VERSION)
        
        Mantiene compatibilidad con firma vieja pero usa sistema enterprise modular
        FIX Nov 28, 2025: Ahora pasa DATOS REALES de Kraken al AI
        WARNING: NO usar desde handlers async de telegram - usar generate_response_async() en su lugar
        """
        try:
            from omnix_services.ai_service.input_sanitizer import sanitize_user_message as _sanitize
            user_message, _san_flags = _sanitize(user_message)
            if _san_flags:
                logger.warning(f"[ISR-017] Sync input sanitized — flags={_san_flags}")
        except Exception:
            pass
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
                
                # V6.5.4e: SYSTEMIC FRAMING ROUTER (ADR-013) - Classify and inject type-specific override
                effective_user_message = user_message
                systemic_type = classify_systemic_question(user_message)
                if systemic_type:
                    logger.info(f"🔍 [SYNC] SYSTEMIC {systemic_type} DETECTED - Injecting type-specific override")
                    systemic_override = get_systemic_override_prompt(systemic_type)
                    # Prepend override BEFORE user message for maximum influence
                    effective_user_message = systemic_override + "\n\nUSER QUESTION: " + user_message
                
                # RAILWAY FIX: Usar asyncio de forma segura
                try:
                    # Intentar obtener loop existente (Railway webhook thread)
                    loop = asyncio.get_running_loop()
                    # Si hay un loop corriendo, usar run_coroutine_threadsafe
                    import concurrent.futures
                    future = asyncio.run_coroutine_threadsafe(
                        self.enterprise_service.generate_response(
                            chat_id=chat_id_int,
                            user_message=effective_user_message,
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
                            user_message=effective_user_message,
                            user_name=user_name,
                            market_data=real_market_data,
                            apply_visual_style=True
                        )
                    )
                
                # Extraer respuesta del resultado (V6.5.4 Premium: con indicador de búsqueda)
                if result and 'response' in result:
                    response_text = result['response']
                    
                    # V6.5.4e: Validate response completeness
                    is_valid, reason, _ = validate_and_log_response(
                        response_text, 
                        user_message, 
                        provider="enterprise-sync"
                    )
                    
                    if not is_valid:
                        logger.warning(f"⚠️ [SYNC] Response incomplete: {reason} - sanitizing")
                        response_text = sanitize_incomplete_response(response_text)
                    
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
            import re as _re
            _m = _re.search(r"Resets in (\d+)s", str(e))
            _reset = f" Intenta de nuevo en {_m.group(1)} segundos." if _m else " Por favor espera un momento."
            return f"⏳ Demasiadas solicitudes al servicio IA.{_reset}"
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
                return await asyncio.wait_for(loop.run_in_executor(None, _fetch), timeout=3.0)
            except Exception as e:
                logger.warning(f"⚠️ [ASYNC] Kraken AUTH failed: {e}")
            return None
        
        async def fetch_kraken_public():
            """Fetch BTC price from Kraken public API"""
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        'https://api.kraken.com/0/public/Ticker?pair=XBTUSD',
                        timeout=aiohttp.ClientTimeout(total=3),
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
                        timeout=aiohttp.ClientTimeout(total=3),
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
        except Exception:
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
                    timeout=5,
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
                    timeout=5,
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
        except Exception:
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
    
    def _legacy_generate_response(self, user_message, user_name, chat_id, user_id, trading_system=None, diagnostic_mode=False):
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
        
        # V6.5.4e: SYSTEMIC FRAMING ROUTER (ADR-013) - Classify and inject type-specific override
        # Must be BEFORE build_system_prompt to prepend to user_message
        effective_user_message = user_message
        systemic_type = classify_systemic_question(user_message)
        if systemic_type:
            logger.info(f"🔍 [LEGACY] SYSTEMIC {systemic_type} DETECTED - Injecting type-specific override")
            systemic_override = get_systemic_override_prompt(systemic_type)
            # Prepend override BEFORE user message for maximum influence
            effective_user_message = systemic_override + "\n\nUSER QUESTION: " + user_message
        
        # DIAGNOSTIC_MODE (RULE 13): Inyectar datos reales del Track Record Oficial
        if diagnostic_mode:
            try:
                from omnix_services.ai_service.prompt_templates import DIAGNOSTIC_ONLY_PROMPT
                from omnix_services.ai_service.providers.investor_data_provider import InvestorDataProvider
                _idp = InvestorDataProvider()
                _basic = _idp.get_basic_trading_stats()
                _tr = _basic.get('track_record') or {}
                _trades_str = str(int(_tr.get('total_trades', 37)))
                _wr_str     = f"{float(_tr.get('win_rate', 54.1)):.1f}"
                _pnl_val    = float(_tr.get('total_pnl', 2054.11))
                _pnl_str    = f"${_pnl_val:,.2f}"
                system_prompt = f"""{DIAGNOSTIC_ONLY_PROMPT}

**DATOS REALES DEL TRACK RECORD OFICIAL (15 Ene 2026 – hoy) — USAR ESTOS EXACTOS:**
- Total trades: {_trades_str}
- Win rate: {_wr_str}%
- P&L total: {_pnl_str} USD
- Nota: 119 operaciones adicionales del Learning Baseline (Nov 2025 – 14 Ene 2026) quedan EXCLUIDAS del Track Record

**PREGUNTA DEL USUARIO:**
{effective_user_message}
"""
                logger.info(f"🔬 [LEGACY DIAGNOSTIC_MODE] Datos reales inyectados: trades={_trades_str}, wr={_wr_str}%, pnl={_pnl_str}")
            except Exception as _diag_err:
                logger.warning(f"⚠️ [LEGACY DIAGNOSTIC_MODE] Fallback a prompt genérico: {_diag_err}")
                system_prompt = prompt_builder.build_system_prompt(
                    user_message=effective_user_message,
                    user_name=user_name,
                    context=context,
                    kraken_status=kraken_status if kraken_info else None,
                    intent='general'
                )
        else:
            system_prompt = prompt_builder.build_system_prompt(
                user_message=effective_user_message,
                user_name=user_name,
                context=context,
                kraken_status=kraken_status if kraken_info else None,
                intent='general'
            )

        # PRIORIDAD 1: GEMINI (key válida en Railway)
        if hasattr(self, 'gemini_client') and self.gemini_client:
            try:
                logger.info("✅ Usando GEMINI en modo legacy")

                # Llamada síncrona a Gemini (generate_response es método sync)
                if hasattr(self.gemini_client, 'models'):
                    # Nuevo SDK (google.genai.Client)
                    try:
                        from google.genai import types as _genai_types
                        _cfg = _genai_types.GenerateContentConfig(
                            temperature=0.7,
                            max_output_tokens=2000,
                            top_p=0.95,
                        )
                        response = self.gemini_client.models.generate_content(
                            model='gemini-2.0-flash',
                            contents=system_prompt,
                            config=_cfg
                        )
                    except Exception:
                        response = self.gemini_client.models.generate_content(
                            model='gemini-2.0-flash',
                            contents=system_prompt
                        )
                else:
                    # SDK clásico (google.generativeai)
                    response = self.gemini_client.generate_content(system_prompt)

                # Extracción segura del texto — aplica a nuevo SDK y legacy
                try:
                    response_text = response.text
                except Exception:
                    if response.candidates and response.candidates[0].content.parts:
                        response_text = response.candidates[0].content.parts[0].text
                    else:
                        fr = response.candidates[0].finish_reason if response.candidates else 'NO_CANDIDATES'
                        raise ValueError(f"Gemini respuesta bloqueada/vacía — finish_reason: {fr}")
                
                if not response_text or not response_text.strip():
                    raise ValueError("Gemini devolvió texto vacío")
                
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
                import traceback
                logger.error(f"❌ Gemini falló [{type(e).__name__}]: {e} — intentando GPT-4 fallback")
                logger.error(f"❌ Gemini TRACEBACK: {traceback.format_exc()}")
        
        # PRIORIDAD 2: GPT-4 fallback (solo si Gemini falla y OpenAI no está deshabilitado)
        _openai_disabled = os.environ.get('OMNIX_DISABLE_OPENAI', 'false').lower() == 'true'
        if not _openai_disabled and hasattr(self, 'openai_client') and self.openai_client:
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
        return "⚠️ Servicio temporalmente no disponible. Por favor, intenta de nuevo en unos momentos."
    
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
