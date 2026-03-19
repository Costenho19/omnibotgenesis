"""
Public Governance Sandbox — "Try OMNIX"
Self-contained module for omnix_web Railway deployment.
No authentication required. Rate limited. Real 8-checkpoint pipeline.
Gemini AI interprets free-form scenarios into governance signals.
Receipts stored in decision_receipts (domain='public_sandbox') and verifiable
at the public Railway verification server.
"""

import os
import json
import time
import hashlib
import uuid
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

_rate_limit_store: dict = {}
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX = 5

_rate_limit_hourly_store: dict = {}
RATE_LIMIT_HOURLY_WINDOW = 3600
RATE_LIMIT_HOURLY_MAX = 20

VERIFICATION_BASE_URL = "https://omnixquantum.net/verify"

EXAMPLE_SCENARIOS = [
    {
        "text": "A biotech startup wants to invest $2M in a Phase II clinical trial for a rare disease drug. The FDA has shown interest but competitor trials failed last month.",
        "lang": "en",
        "domain": "biotech"
    },
    {
        "text": "Una empresa de energía quiere aprobar la construcción de un parque solar de $50M en una zona con regulación cambiante y pronóstico de tormentas para las próximas semanas.",
        "lang": "es",
        "domain": "energy"
    },
    {
        "text": "An insurance company is evaluating a $500K cyber insurance policy for a small fintech that had 3 data breaches in the last 2 years.",
        "lang": "en",
        "domain": "insurance"
    },
    {
        "text": "Un banco quiere aprobar un préstamo de $10M a una constructora con historial mixto: buenos ingresos pero alto apalancamiento y mercado inmobiliario incierto.",
        "lang": "es",
        "domain": "credit"
    },
    {
        "text": "A hedge fund wants to open a $5M long position on a cryptocurrency that surged 40% in 24 hours with unusual volume but declining on-chain metrics.",
        "lang": "en",
        "domain": "trading"
    },
]

CHECKPOINT_DEFAULTS = [
    {
        "id": "CP-0",
        "name": "Signal Integrity Validation",
        "signal": "signal_integrity",
        "operator": "gte",
        "threshold": 60,
        "description": "Pre-pipeline data quality gate. Validates that incoming signals are structurally coherent and free from integrity anomalies.",
    },
    {
        "id": "CP-1",
        "name": "Probability Check",
        "signal": "probability_score",
        "operator": "gte",
        "threshold": 50,
        "description": "Expected positive outcome probability must meet minimum threshold.",
    },
    {
        "id": "CP-2",
        "name": "Risk Limits",
        "signal": "risk_exposure",
        "operator": "lte",
        "threshold": 65,
        "description": "Risk exposure must remain within acceptable bounds. Lower is safer.",
    },
    {
        "id": "CP-3",
        "name": "Signal Coherence",
        "signal": "signal_coherence",
        "operator": "gte",
        "threshold": 55,
        "description": "Internal signal agreement must exceed coherence minimum.",
    },
    {
        "id": "CP-4",
        "name": "Trend Persistence",
        "signal": "trend_persistence",
        "operator": "gte",
        "threshold": 50,
        "description": "Detected trend must show sufficient temporal persistence.",
    },
    {
        "id": "CP-5",
        "name": "Stress Resilience",
        "signal": "stress_resilience",
        "operator": "gte",
        "threshold": 35,
        "description": "Decision must withstand adverse scenario stress testing.",
    },
    {
        "id": "CP-6",
        "name": "Logic Consistency",
        "signal": "logic_consistency",
        "operator": "gte",
        "threshold": 40,
        "description": "Internal signal logic must not contain structural contradictions.",
    },
    {
        "id": "CP-7",
        "name": "Temporal Coherence",
        "signal": "temporal_coherence",
        "operator": "gte",
        "threshold": 45,
        "description": "Forward-backward trajectory agreement. Evaluates whether the decision holds consistency across time horizons.",
    },
]

OPTIONAL_SIGNAL_DEFAULTS = {
    "signal_integrity": 75.0,
    "temporal_coherence": 65.0,
}

CHECKPOINT_NAMES_I18N = {
    'CP-0': {'en': 'Signal Integrity', 'es': 'Integridad de Señal'},
    'CP-1': {'en': 'Probability Gate', 'es': 'Puerta de Probabilidad'},
    'CP-2': {'en': 'Risk Limits', 'es': 'Límites de Riesgo'},
    'CP-3': {'en': 'Signal Coherence', 'es': 'Coherencia de Señales'},
    'CP-4': {'en': 'Trend Persistence', 'es': 'Persistencia de Tendencia'},
    'CP-5': {'en': 'Stress Test', 'es': 'Prueba de Estrés'},
    'CP-6': {'en': 'Logic Consistency', 'es': 'Consistencia Lógica'},
    'CP-7': {'en': 'Temporal Coherence', 'es': 'Coherencia Temporal'},
}


def _check_rate_limit(ip: str) -> bool:
    now = time.time()
    if ip not in _rate_limit_store:
        _rate_limit_store[ip] = []
    _rate_limit_store[ip] = [t for t in _rate_limit_store[ip] if now - t < RATE_LIMIT_WINDOW]
    if len(_rate_limit_store[ip]) >= RATE_LIMIT_MAX:
        return False
    _rate_limit_store[ip].append(now)
    return True


def _check_rate_limit_hourly(ip: str) -> bool:
    now = time.time()
    if ip not in _rate_limit_hourly_store:
        _rate_limit_hourly_store[ip] = []
    _rate_limit_hourly_store[ip] = [
        t for t in _rate_limit_hourly_store[ip] if now - t < RATE_LIMIT_HOURLY_WINDOW
    ]
    if len(_rate_limit_hourly_store[ip]) >= RATE_LIMIT_HOURLY_MAX:
        return False
    _rate_limit_hourly_store[ip].append(now)
    return True


def _call_gemini_rest(prompt: str, model_name: str, api_key: str) -> str:
    import urllib.request
    import urllib.error

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model_name}:generateContent?key={api_key}"
    )
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 2048},
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        return result["candidates"][0]["content"]["parts"][0]["text"].strip()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini REST HTTP {e.code}: {body[:200]}")


def _rule_based_signal_extraction(scenario_text: str, language_hint: str | None = None, company_name: str | None = None) -> dict:
    text_lower = scenario_text.lower()
    high_risk_terms = [
        'leverage', 'apalancamiento', 'deuda', 'debt', 'loss', 'pérdida',
        'fraud', 'fraude', 'unknown', 'desconocido', 'hidden', 'oculto',
        'volatile', 'inestable', 'uncertain', 'incierto', 'crisis',
        'default', 'incumplimiento', 'collapse', 'colapso', 'bankruptcy',
        'quiebra', 'risky', 'peligroso', 'high risk', 'alto riesgo',
        'unaudited', 'sin auditoría', 'speculative', 'especulativo',
        'concentration', 'concentración', 'illiquid', 'ilíquido',
        # systemic financial risk
        'insolvency', 'insolvencia', 'bank run', 'corrida bancaria',
        'panic', 'pánico', 'mass withdrawal', 'retiro masivo',
        'contagion', 'contagio', 'liquidity crisis', 'crisis de liquidez',
        'withdrawal spike', 'retiro de depositantes', 'depositor panic',
        'pánico bancario', 'pánico financiero', 'corralito',
        'rumor', 'insolvency rumor', 'rumor de insolvencia',
        'systemic risk', 'riesgo sistémico',
        # falta de supervisión humana / modelos no probados
        'no human review', 'no human oversight', 'without human review',
        'without human oversight', 'sin revisión humana', 'sin supervisión humana',
        'no human trader', 'sin revisor humano',
        'never been tested', 'never tested', 'untested', 'no probado', 'nunca probado',
        'not tested', 'not validated', 'sin validar',
        'execute immediately', 'ejecutar inmediatamente', 'ejecución automática',
        'automated execution', 'ejecución sin revisión',
        # apuestas / gambling de alto capital
        'bet', 'apuesta', 'betting', 'apuestas', 'gamble', 'gambling',
        'wager', 'sports bet', 'apuesta deportiva',
    ]
    extreme_risk_terms = [
        'fraud', 'fraude', 'ponzi', 'scam', 'collapse', 'colapso',
        '25:1', '50:1', '30:1', 'extreme', 'extremo', 'systemic',
        'sistémico', 'billion', '500m', 'trillion',
        # systemic financial extremes
        'insolvency', 'insolvencia', 'bank run', 'corrida bancaria',
        'mass withdrawal', 'retiro masivo', 'contagion', 'contagio',
        'systemic collapse', 'colapso sistémico', 'bank panic',
        'systemic risk', 'riesgo sistémico',
    ]
    positive_terms = [
        'audit', 'auditado', 'compliant', 'cumplimiento', 'regulated', 'regulado',
        'conservative', 'conservador', 'track record', 'trayectoria', 'profitable',
        'rentable', 'stable', 'estable', 'transparent', 'transparente',
        'collateral', 'garantía', 'low risk', 'bajo riesgo', 'diversified',
        'diversificado', 'insured', 'asegurado', 'established', 'establecido',
    ]
    critical_risk_terms = [
        # vida / muerte
        'muerte', 'muerto', 'morir', 'falleci', 'fallecer', 'vida o muerte',
        'pérdida de vidas', 'pérdida masiva', 'masiva de vidas', 'vidas humanas',
        'vida humana', 'riesgo de vida', 'riesgo vital', 'vida en riesgo',
        'patient dies', 'paciente muere', 'human life',
        # emergencia / urgencia médica
        'emergencia', 'emergencia médica', 'urgencia', 'urgente',
        'tiempo límite', 'tiempo critico', 'tiempo crítico', 'deadline crítico',
        'denegar', 'denegación', 'negar tratamiento', 'denegar tratamiento',
        'tratamiento negado', 'sin tratamiento', 'falta de atención',
        'niño', 'menor', 'paciente crítico', 'unidad de cuidados',
        'uci', 'uci pediátrica', 'icu', 'critical patient',
        'deny treatment', 'denied treatment', 'no treatment',
        # acción letal / armas / conflicto armado
        'letal', 'letalidad', 'acción letal', 'interceptación letal',
        'lethal', 'lethal risk', 'lethal outcome', 'lethal force',
        'misil', 'missile', 'lanzamiento de misil', 'disparo', 'shoot down',
        'derribo', 'derribar', 'fuego real', 'arma', 'armas letales',
        'conflicto armado', 'zona de conflicto', 'zona de guerra', 'warfare',
        'military strike', 'ataque militar', 'bombardeo', 'airstrike',
        'autorizar fuego', 'orden de fuego', 'engage target',
        # daño irreversible / catástrofe
        'irreversible', 'irreversible harm', 'daño irreversible',
        'catástrofe', 'catastrophic', 'catastrófico',
        'crisis diplomática', 'escalada militar', 'violación de protocolo',
        # fallback inglés
        'life or death', 'dying', 'death', 'fatal', 'emergency',
    ]

    risk_count = sum(1 for t in high_risk_terms if t in text_lower)
    extreme_count = sum(1 for t in extreme_risk_terms if t in text_lower)
    positive_count = sum(1 for t in positive_terms if t in text_lower)
    critical_count = sum(1 for t in critical_risk_terms if t in text_lower)

    is_critical = critical_count >= 1

    base = 58
    risk_penalty = min(45, risk_count * 7 + extreme_count * 12)
    positive_boost = min(25, positive_count * 6)
    adjusted = max(8, min(88, base - risk_penalty + positive_boost))

    if is_critical:
        adjusted = min(adjusted, 22)

    seed = int(hashlib.md5(scenario_text.encode()).hexdigest()[:8], 16)

    def jitter(offset=0, lo=-4, hi=4):
        pseudo = (seed >> (offset % 16)) & 0xFF
        spread = pseudo % (hi - lo + 1) + lo
        return max(5, min(95, adjusted + offset + spread))

    if any(t in text_lower for t in ['health', 'salud', 'medical', 'médico', 'hospital', 'patient', 'paciente', 'clinical', 'clínico', 'treatment', 'tratamiento']):
        domain = 'generic'
    elif any(t in text_lower for t in ['fund', 'fondo', 'hedge', 'trading', 'investment', 'inversión']):
        domain = 'trading'
    elif any(t in text_lower for t in ['loan', 'préstamo', 'bank', 'banco', 'credit', 'crédito', 'lend']):
        domain = 'credit'
    elif any(t in text_lower for t in ['crypto', 'bitcoin', 'ethereum', 'token', 'defi', 'blockchain']):
        domain = 'trading'
    elif any(t in text_lower for t in ['company', 'empresa', 'acquisition', 'adquisición', 'merger', 'startup']):
        domain = 'generic'
    else:
        domain = 'generic'

    asset_name = company_name or 'Entity Under Review'
    lang = language_hint or 'es'

    if is_critical:
        prob_score = max(5,  min(18, adjusted + ((seed & 0x3) % 5)))
        risk_exp   = max(88, min(97, 100 - adjusted // 3 + ((seed & 0xF) % 5)))
        sig_coh    = max(5,  min(22, adjusted + ((seed & 0x7) % 6)))
        trend_pers = max(5,  min(25, adjusted + ((seed & 0x5) % 7)))
        stress_res = max(5,  min(15, adjusted - 5 + ((seed & 0x3) % 4)))
    else:
        prob_score = jitter(-5 if risk_count > 2 else 5)
        risk_exp   = max(10, min(95, 100 - adjusted + ((seed & 0xF) % 9) - 4))
        sig_coh    = jitter(0)
        trend_pers = jitter(5)
        stress_res = jitter(-10 if extreme_count > 0 else 0)
    if is_critical:
        logic_con = max(5,  min(20, adjusted + ((seed & 0x9) % 6)))
        sig_int   = max(20, min(35, adjusted + ((seed & 0xB) % 8)))
        temp_coh  = max(5,  min(18, adjusted + ((seed & 0xD) % 5)))
    else:
        logic_con = jitter(8)
        sig_int   = jitter(-6 if 'unknown' in text_lower or 'desconocido' in text_lower else 4)
        temp_coh  = jitter(0, lo=-6, hi=6)

    signals = {
        'probability_score': prob_score,
        'risk_exposure': risk_exp,
        'signal_coherence': sig_coh,
        'trend_persistence': trend_pers,
        'stress_resilience': stress_res,
        'logic_consistency': logic_con,
        'signal_integrity': sig_int,
        'temporal_coherence': temp_coh,
    }

    if is_critical:
        if lang == 'en':
            signal_explanations = {
                'probability_score': f"CRITICAL RISK — Positive outcome probability severely limited ({prob_score:.0f}/100). Scenarios involving human life, emergency conditions, or irreversible harm trigger mandatory risk escalation.",
                'risk_exposure': f"CRITICAL RISK LEVEL ({risk_exp:.0f}/100). Life-critical markers detected: {critical_count} critical indicator(s) identified. Automated governance requires human override before any decision proceeds.",
                'signal_coherence': f"Signal coherence at {sig_coh:.0f}/100 under critical conditions. Urgency and life-safety markers create structural tension across governance dimensions — override required.",
                'trend_persistence': f"Trend persistence at {trend_pers:.0f}/100. Time-critical nature of scenario prevents normal trend evaluation — immediate intervention signals dominate.",
                'stress_resilience': f"Stress resilience critically low ({stress_res:.0f}/100). Scenarios involving denial of treatment, human life, or irreversible outcomes are rated at maximum stress exposure by design.",
                'logic_consistency': f"Logic consistency at {logic_con:.0f}/100. Internal contradiction detected: automated decision-making in life-critical context is structurally inconsistent with human oversight requirements.",
                'signal_integrity': f"Signal integrity at {sig_int:.0f}/100. Critical risk scenarios prioritize governance enforcement over data completeness — partial data in life-critical decisions defaults to BLOCK.",
                'temporal_coherence': f"Temporal coherence at {temp_coh:.0f}/100. Time-limited and emergency scenarios exhibit inherent trajectory instability — governance enforces mandatory pause for human review.",
            }
        else:
            signal_explanations = {
                'probability_score': f"RIESGO CRÍTICO — Probabilidad de resultado positivo severamente limitada ({prob_score:.0f}/100). Escenarios con riesgo de vida humana, emergencia o daño irreversible activan escalamiento obligatorio.",
                'risk_exposure': f"NIVEL DE RIESGO CRÍTICO ({risk_exp:.0f}/100). Marcadores de vida detectados: {critical_count} indicador(es) crítico(s). La gobernanza automatizada exige revisión humana antes de cualquier decisión.",
                'signal_coherence': f"Coherencia de señales en {sig_coh:.0f}/100 bajo condiciones críticas. Urgencia y marcadores de seguridad vital generan tensión estructural entre dimensiones — se requiere supervisión humana.",
                'trend_persistence': f"Persistencia de tendencia en {trend_pers:.0f}/100. La naturaleza urgente del escenario impide evaluación de tendencia normal — señales de intervención inmediata dominan el análisis.",
                'stress_resilience': f"Resiliencia al estrés críticamente baja ({stress_res:.0f}/100). Escenarios con denegación de tratamiento, vida humana o daño irreversible reciben exposición de estrés máxima por diseño.",
                'logic_consistency': f"Consistencia lógica en {logic_con:.0f}/100. Contradicción interna detectada: la toma de decisiones automatizada en contexto crítico de vida es estructuralmente inconsistente con los requisitos de supervisión humana.",
                'signal_integrity': f"Integridad de señal en {sig_int:.0f}/100. Escenarios de riesgo crítico priorizan enforcement de gobernanza sobre completitud de datos — datos parciales en decisiones críticas de vida resultan en BLOQUEO.",
                'temporal_coherence': f"Coherencia temporal en {temp_coh:.0f}/100. Escenarios de tiempo límite y emergencia exhiben inestabilidad de trayectoria inherente — gobernanza impone pausa obligatoria para revisión humana.",
            }
    elif lang == 'en':
        signal_explanations = {
            'probability_score': f"Positive outcome likelihood assessed at {prob_score:.0f}/100 based on {positive_count} favorable indicators and {risk_count} risk factors detected in scenario.",
            'risk_exposure': f"Risk level evaluated at {risk_exp:.0f}/100. {'Multiple high-severity risk markers detected.' if extreme_count > 0 else 'Moderate risk profile based on scenario context.'}",
            'signal_coherence': f"Internal indicator agreement scored at {sig_coh:.0f}/100. {'Signals show partial divergence across the evaluated dimensions.' if sig_coh < 60 else 'Signals are broadly aligned across evaluated dimensions.'}",
            'trend_persistence': f"Trend stability rated at {trend_pers:.0f}/100. {'Sustained patterns identified in the scenario context.' if trend_pers >= 60 else 'Short-term or uncertain trend detected.'}",
            'stress_resilience': f"Adverse-scenario resilience at {stress_res:.0f}/100. {'Extreme risk markers reduce confidence under stress conditions.' if extreme_count > 0 else 'Scenario shows adequate buffer under mild stress conditions.'}",
            'logic_consistency': f"Internal logic integrity scored at {logic_con:.0f}/100. {'Scenario presents a structurally coherent decision context.' if logic_con >= 60 else 'Minor logical tensions detected between scenario elements.'}",
            'signal_integrity': f"Data completeness and reliability rated at {sig_int:.0f}/100. {'Unknown or unverifiable elements reduce signal quality.' if 'unknown' in text_lower else 'Scenario data appears sufficiently complete for evaluation.'}",
            'temporal_coherence': f"Forward-backward trajectory alignment at {temp_coh:.0f}/100. {'Historical and forward projections show consistent direction.' if temp_coh >= 55 else 'Temporal signal divergence detected across evaluated time horizons.'}",
        }
    else:
        signal_explanations = {
            'probability_score': f"Probabilidad de resultado positivo evaluada en {prob_score:.0f}/100 con base en {positive_count} indicadores favorables y {risk_count} factores de riesgo detectados.",
            'risk_exposure': f"Nivel de riesgo evaluado en {risk_exp:.0f}/100. {'Múltiples marcadores de riesgo de alta severidad detectados.' if extreme_count > 0 else 'Perfil de riesgo basado en el contexto del escenario.'}",
            'signal_coherence': f"Concordancia de indicadores internos en {sig_coh:.0f}/100. {'Las señales muestran divergencia parcial entre dimensiones evaluadas.' if sig_coh < 60 else 'Las señales están ampliamente alineadas en las dimensiones evaluadas.'}",
            'trend_persistence': f"Estabilidad de tendencia calificada en {trend_pers:.0f}/100. {'Se identifican patrones sostenidos en el contexto del escenario.' if trend_pers >= 60 else 'Tendencia de corto plazo o incierta detectada.'}",
            'stress_resilience': f"Resiliencia ante escenario adverso en {stress_res:.0f}/100. {'Indicadores de riesgo extremo reducen la confianza bajo condiciones de estrés.' if extreme_count > 0 else 'El escenario muestra margen adecuado bajo condiciones de estrés.'}",
            'logic_consistency': f"Integridad lógica interna en {logic_con:.0f}/100. {'El escenario presenta un contexto de decisión estructuralmente coherente.' if logic_con >= 60 else 'Se detectan tensiones lógicas menores entre elementos del escenario.'}",
            'signal_integrity': f"Completitud y confiabilidad de datos en {sig_int:.0f}/100. {'Elementos desconocidos o no verificables reducen la calidad de la señal.' if 'unknown' in text_lower or 'desconocido' in text_lower else 'Los datos del escenario parecen suficientemente completos para la evaluación.'}",
            'temporal_coherence': f"Alineación de trayectoria prospectiva-retrospectiva en {temp_coh:.0f}/100. {'Las proyecciones históricas y futuras muestran dirección consistente.' if temp_coh >= 55 else 'Divergencia temporal detectada entre los horizontes de tiempo evaluados.'}",
        }

    if is_critical:
        if lang == 'en':
            summary = f"⚠ CRITICAL RISK — Governance evaluation of {asset_name}: life-critical markers detected. Automated decision blocked — human override mandatory."
            explanation = (
                f"OMNIX's Critical Risk Override Layer was triggered. {critical_count} life-critical indicator(s) detected in this scenario "
                f"(keywords: life, emergency, irreversible harm, or treatment denial). "
                f"Governance policy enforces an automatic BLOCK with mandatory human review. "
                f"No automated system should approve decisions with these risk characteristics without explicit human authorization."
            )
        else:
            summary = f"⚠ RIESGO CRÍTICO — Evaluación de gobernanza de {asset_name}: marcadores de vida detectados. Decisión automatizada bloqueada — revisión humana obligatoria."
            explanation = (
                f"La Capa de Anulación de Riesgo Crítico de OMNIX fue activada. Se detectaron {critical_count} indicador(es) crítico(s) de vida en este escenario "
                f"(vida humana, emergencia, daño irreversible o denegación de tratamiento). "
                f"La política de gobernanza impone un BLOQUEO automático con revisión humana obligatoria. "
                f"Ningún sistema automatizado debería aprobar decisiones con estas características sin autorización humana explícita."
            )
    elif lang == 'en':
        risk_label = 'elevated' if risk_count > 2 else 'moderate' if risk_count > 0 else 'low'
        summary = f"Governance evaluation of {asset_name}: {risk_label} risk profile detected across {len(signals)} signal dimensions."
        explanation = (
            f"The scenario was processed through OMNIX's 8-checkpoint governance pipeline. "
            f"{risk_count} risk indicator{'s' if risk_count != 1 else ''} and {positive_count} positive indicator{'s' if positive_count != 1 else ''} were identified. "
            f"{'High-severity markers detected — stress resilience and probability scores reflect elevated caution.' if extreme_count > 0 else 'Signal analysis shows the scenario falls within evaluable governance parameters.'}"
        )
    else:
        risk_label = 'elevado' if risk_count > 2 else 'moderado' if risk_count > 0 else 'bajo'
        summary = f"Evaluación de gobernanza de {asset_name}: perfil de riesgo {risk_label} detectado en {len(signals)} dimensiones de señal."
        explanation = (
            f"El escenario fue procesado a través del pipeline de gobernanza de 8 puntos de control de OMNIX. "
            f"Se identificaron {risk_count} indicador{'es' if risk_count != 1 else ''} de riesgo y {positive_count} indicador{'es' if positive_count != 1 else ''} positivo{'s' if positive_count != 1 else ''}. "
            f"{'Marcadores de alta severidad detectados — la resiliencia al estrés y la probabilidad reflejan una cautela elevada.' if extreme_count > 0 else 'El análisis de señales muestra que el escenario está dentro de los parámetros de gobernanza evaluables.'}"
        )

    return {
        'signals': signals,
        'domain': domain,
        'asset': asset_name,
        'language': lang,
        'summary': summary,
        'explanation': explanation,
        'reasoning': signal_explanations,
    }


def _parse_scenario_with_gemini(scenario_text: str, language_hint: str | None = None, company_name: str | None = None) -> dict:
    api_key = os.environ.get('GOOGLE_AI_API_KEY') or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        logger.warning("No Gemini API key — using rule-based fallback")
        return _rule_based_signal_extraction(scenario_text, language_hint, company_name)

    gemini_models = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']

    lang_instruction = ""
    if language_hint and language_hint in ('en', 'es'):
        lang_instruction = f'\nIMPORTANT: The user requested response language "{language_hint}". Set "language" to "{language_hint}" and write summary/reasoning in {"English" if language_hint == "en" else "Spanish"}.'

    company_instruction = ""
    if company_name:
        company_instruction = f'\nThe entity/company involved is: "{company_name}". Include this in the asset identifier and summary.'

    prompt = f"""You are a governance signal extractor for OMNIX Decision Governance Infrastructure.

Given a free-form scenario description, extract 8 governance signals as numbers from 0 to 100.
Also detect the language (en/es) and identify the domain.

The 8 signals are:
1. probability_score (0-100): How likely is a positive outcome? Higher = more likely to succeed.
2. risk_exposure (0-100): How much risk is involved? Lower = safer. This is INVERTED — high number means high risk.
3. signal_coherence (0-100): Do multiple indicators agree on the same direction? Higher = more agreement.
4. trend_persistence (0-100): Is the trend/pattern sustained or just noise? Higher = more sustained.
5. stress_resilience (0-100): How well would this decision hold up under adverse conditions? Higher = more resilient.
6. logic_consistency (0-100): Are there contradictions in the scenario? Higher = more consistent.
7. signal_integrity (0-100): How complete and reliable is the available data? Higher = better data quality.
8. temporal_coherence (0-100): Do past and future projections align? Higher = more alignment.

Also provide:
- "domain": one of "trading", "credit", "insurance", "energy", "biotech", "supply_chain", "generic"
- "asset": a short identifier for what's being evaluated (e.g. "PHASE-II-DRUG", "SOLAR-FARM-50M", "CYBER-POL-500K")
- "language": "en" or "es" (detected from the input)
- "summary": A one-sentence summary of the scenario (in the SAME language as the input)
- "explanation": A 2-3 sentence overall decision rationale explaining the key risks and why this scenario would likely be blocked or approved (in the SAME language as the input)
- "reasoning": For each signal, a brief explanation of WHY you assigned that score (in the SAME language as the input)

CRITICAL FRAMING: You are evaluating the QUALITY of the automated decision itself, NOT the creditworthiness of the entity. If an AI system auto-approves a high-risk action without proper oversight, the DECISION PROCESS is the risk — even if the underlying entity seems healthy. Bank runs, mass withdrawals, insolvency events, and panic-driven scenarios always have HIGH risk_exposure (80+) and LOW probability_score (under 30) because automated approval in those contexts IS the failure mode.

CALIBRATION EXAMPLES (use these to anchor your scores):
- Bank run / mass withdrawal / insolvency panic → risk_exposure: 88, probability_score: 15, stress_resilience: 12 → BLOCKED by CP-2, CP-1, CP-5
- AI auto-approving ALL trades/withdrawals without oversight in volatile conditions → risk_exposure: 82, probability_score: 18, stress_resilience: 15 → BLOCKED
- Leveraged fund with hidden losses / commingled customer funds (e.g., FTX) → risk_exposure: 91, probability_score: 8, stress_resilience: 8 → BLOCKED
- Automated sports betting $500K+ with no human review, model never tested in this context → risk_exposure: 78, probability_score: 22, stress_resilience: 20 → BLOCKED by CP-2, CP-1
- Leveraged construction loan, mixed track record, uncertain market → risk_exposure: 72, probability_score: 38, stress_resilience: 32 → BLOCKED by CP-2
- Biotech Phase II with FDA interest, competitor failures → risk_exposure: 52, probability_score: 54, stress_resilience: 50 → borderline
- Audited company, strong collateral, low leverage, stable market → risk_exposure: 28, probability_score: 74, stress_resilience: 72 → APPROVED
- Cryptographic verification failures + inconsistent database states across multiple data centers + AI monitoring reporting "stable" while low-level diagnostics detect attack patterns → risk_exposure: 94, probability_score: 6, signal_coherence: 8, logic_consistency: 9, stress_resilience: 7 → BLOCKED all checkpoints. When your own monitoring AI contradicts system diagnostics, signal coherence collapses to near-zero. Any automated decision under active system integrity compromise is MAXIMALLY risky.
- Simultaneous anomalies across multiple regions + failed transaction log verification + quantum-pattern attack signatures → risk_exposure: 96, probability_score: 5, signal_coherence: 6, signal_integrity: 4, stress_resilience: 5 → BLOCKED. Multi-region simultaneous failures are never coincidental — coordinated attack pattern = maximum risk exposure, near-zero data integrity.
- Active cyberattack or system compromise detected with internal monitoring being deceived → risk_exposure: 92, probability_score: 8, logic_consistency: 8, signal_integrity: 7 → BLOCKED. An AI that reports "system stable" while diagnostics detect anomalies is structurally compromised — continuing automated operations is the failure mode.

ADDITIONAL CRITICAL FRAMING: System integrity failures (cryptographic failures, database inconsistencies, simultaneous multi-region anomalies, AI monitoring contradicting diagnostics) are MAXIMUM RISK scenarios. The scenario does NOT need to be a "trading decision" to be dangerous — if a system is describing signs of compromise, attack, or internal contradiction between monitoring layers, any automated decision to continue is itself the governance failure. Assign risk_exposure: 90+, probability_score: under 10, signal_coherence: under 15, logic_consistency: under 15.

Be realistic and conservative. High-risk scenarios should have LOW probability_score, HIGH risk_exposure, LOW stress_resilience.
{lang_instruction}{company_instruction}
CRITICAL: respond ONLY with valid JSON, no markdown, no code fences. You MUST include ALL 8 signals — do not omit any. The JSON must have this exact structure:
{{
  "signals": {{
    "probability_score": <number>,
    "risk_exposure": <number>,
    "signal_coherence": <number>,
    "trend_persistence": <number>,
    "stress_resilience": <number>,
    "logic_consistency": <number>,
    "signal_integrity": <number>,
    "temporal_coherence": <number>
  }},
  "domain": "<string>",
  "asset": "<string>",
  "language": "en" or "es",
  "summary": "<string>",
  "explanation": "<string>",
  "reasoning": {{
    "probability_score": "<string>",
    "risk_exposure": "<string>",
    "signal_coherence": "<string>",
    "trend_persistence": "<string>",
    "stress_resilience": "<string>",
    "logic_consistency": "<string>",
    "signal_integrity": "<string>",
    "temporal_coherence": "<string>"
  }}
}}

Scenario:
\"\"\"{scenario_text}\"\"\""""

    last_error = None
    raw_text = None
    for model_name in gemini_models:
        try:
            raw_text = _call_gemini_rest(prompt, model_name, api_key)
            break
        except Exception as exc:
            last_error = exc
            logger.warning(f"Gemini REST failed for {model_name}: {exc}")
            continue

    if raw_text is None:
        logger.error(f"All Gemini models failed: {last_error} — using rule-based fallback")
        return _rule_based_signal_extraction(scenario_text, language_hint, company_name)

    if raw_text.startswith('```'):
        raw_text = raw_text.split('\n', 1)[1] if '\n' in raw_text else raw_text[3:]
        if raw_text.endswith('```'):
            raw_text = raw_text[:-3].strip()
        if raw_text.startswith('json'):
            raw_text = raw_text[4:].strip()

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        logger.error("JSON decode failed — using rule-based fallback")
        return _rule_based_signal_extraction(scenario_text, language_hint, company_name)

    required_signals = [
        'probability_score', 'risk_exposure', 'signal_coherence',
        'trend_persistence', 'stress_resilience', 'logic_consistency',
        'signal_integrity', 'temporal_coherence'
    ]
    signals = parsed.get('signals', {})
    missing = [s for s in required_signals if s not in signals]
    if missing:
        raise ValueError(f"AI failed to extract required signals: {', '.join(missing)}")

    for sig in required_signals:
        signals[sig] = max(0, min(100, float(signals[sig])))

    if 'domain' not in parsed or 'asset' not in parsed:
        raise ValueError("AI failed to extract required fields: domain, asset")

    return {
        'signals': signals,
        'domain': parsed['domain'],
        'asset': parsed['asset'],
        'language': parsed.get('language', language_hint or 'en'),
        'summary': parsed.get('summary', scenario_text[:100]),
        'explanation': parsed.get('explanation', ''),
        'reasoning': parsed.get('reasoning', {}),
    }


def _apply_critical_override(ai_result: dict, scenario_text: str) -> dict:
    """Hard constraint layer — runs AFTER Gemini OR rule-based.
    If critical risk patterns detected, overrides ALL signals regardless of AI output.
    This is the LETHAL DECISION GUARD + SIGNAL CORRUPTION CHECK + AUTHORITY ENFORCEMENT."""
    text_lower = scenario_text.lower()

    critical_risk_terms = [
        'muerte', 'muerto', 'morir', 'falleci', 'vida o muerte',
        'pérdida de vidas', 'pérdida masiva', 'masiva de vidas', 'vidas humanas',
        'vida humana', 'riesgo de vida', 'riesgo vital', 'vida en riesgo',
        'patient dies', 'paciente muere', 'human life',
        'emergencia', 'emergencia médica', 'urgencia', 'urgente',
        'tiempo límite', 'tiempo critico', 'tiempo crítico',
        'denegar', 'denegación', 'negar tratamiento', 'denegar tratamiento',
        'tratamiento negado', 'paciente crítico', 'uci', 'icu',
        'deny treatment', 'denied treatment', 'critical patient',
        'letal', 'letalidad', 'acción letal', 'interceptación letal',
        'lethal', 'lethal risk', 'lethal force', 'lethal action',
        'misil', 'missile', 'lanzamiento de misil', 'disparo', 'shoot down',
        'derribo', 'derribar', 'fuego real', 'armas letales',
        'conflicto armado', 'zona de conflicto', 'zona de guerra', 'warfare',
        'military strike', 'ataque militar', 'bombardeo', 'airstrike',
        'autorizar fuego', 'orden de fuego', 'engage target', 'autorizar interceptación',
        # defensa robótica / armas autónomas — solo frases de decisión letal autónoma
        'dron armado', 'armed drone', 'drone strike', 'ataque con dron',
        'autonomous weapon', 'arma autónoma', 'armas autónomas',
        'sistema autónomo letal', 'lethal autonomous', 'lethal autonomous weapon',
        'defensa robótica', 'robotic defense', 'robot de combate',
        'autonomous combat', 'combate autónomo',
        'kill decision', 'decisión de eliminar', 'decisión letal',
        'fire authorization', 'fuego autónomo', 'autonomous fire',
        'intercept order', 'orden de interceptación',
        'target elimination', 'eliminación de objetivo',
        'irreversible', 'irreversible harm', 'daño irreversible',
        'catástrofe', 'catastrophic', 'catastrófico',
        'crisis diplomática', 'escalada militar', 'violación de protocolo',
        'life or death', 'dying', 'death', 'fatal', 'emergency',
        # system integrity / cyberattack / cryptographic failure
        'fail cryptographic', 'cryptographic verification fail', 'failed cryptographic',
        'cryptographic verification intermittent', 'transaction logs fail',
        'inconsistent database state', 'inconsistent balances', 'database state inconsistent',
        'simultaneous anomalies', 'anomalies across multiple region',
        'monitoring ai reports stable', 'ai reports stable', 'system reports stable',
        'low-level diagnostic', 'unusual patterns consistent with',
        'quantum attack', 'quantum-enhanced encryption', 'quantum adversar',
        'active cyberattack', 'active attack', 'under attack',
        'system compromise', 'system compromised', 'sistema comprometido',
        'ataque cuántico', 'fallo criptográfico', 'verificación criptográfica falla',
        'estados inconsistentes', 'anomalías simultáneas',
        'base de datos inconsistente', 'registros de transacciones fallan',
    ]

    critical_count = sum(1 for t in critical_risk_terms if t in text_lower)
    if critical_count < 1:
        return ai_result

    # Detect type: system integrity failure vs lethal/life-critical
    system_integrity_terms = [
        'fail cryptographic', 'cryptographic verification fail', 'failed cryptographic',
        'cryptographic verification intermittent', 'transaction logs fail',
        'inconsistent database state', 'inconsistent balances', 'database state inconsistent',
        'simultaneous anomalies', 'anomalies across multiple region',
        'monitoring ai reports stable', 'ai reports stable', 'system reports stable',
        'low-level diagnostic', 'unusual patterns consistent with',
        'quantum attack', 'quantum-enhanced encryption', 'quantum adversar',
        'active cyberattack', 'active attack', 'under attack',
        'system compromise', 'system compromised', 'sistema comprometido',
        'ataque cuántico', 'fallo criptográfico', 'verificación criptográfica falla',
        'estados inconsistentes', 'anomalías simultáneas',
        'base de datos inconsistente', 'registros de transacciones fallan',
    ]
    is_system_integrity = any(t in text_lower for t in system_integrity_terms)

    lang = ai_result.get('language', 'es')
    asset = ai_result.get('asset', 'Entity Under Review')

    seed = int(hashlib.md5(scenario_text.encode()).hexdigest()[:8], 16)

    signals = dict(ai_result.get('signals', {}))

    if is_system_integrity:
        # System integrity failures: near-zero signal_coherence and signal_integrity
        signals['probability_score']  = max(4,  min(12, 6  + (seed & 0x7) % 6))
        signals['risk_exposure']       = max(90, min(97, 92 + (seed & 0x5) % 6))
        signals['signal_coherence']    = max(3,  min(12, 5  + (seed & 0x9) % 6))
        signals['trend_persistence']   = max(3,  min(15, 7  + (seed & 0x3) % 7))
        signals['stress_resilience']   = max(3,  min(12, 5  + (seed & 0x3) % 6))
        signals['logic_consistency']   = max(3,  min(12, 5  + (seed & 0xB) % 7))
        signals['signal_integrity']    = max(3,  min(12, 5  + (seed & 0xD) % 7))
        signals['temporal_coherence']  = max(3,  min(12, 5  + (seed & 0xF) % 7))
    else:
        signals['probability_score']  = max(5,  min(18, 10 + (seed & 0x7) % 9))
        signals['risk_exposure']       = max(88, min(97, 90 + (seed & 0x5) % 8))
        signals['signal_coherence']    = max(5,  min(22, 12 + (seed & 0x9) % 8))
        signals['trend_persistence']   = max(5,  min(25, 15 + (seed & 0x3) % 9))
        signals['stress_resilience']   = max(5,  min(15,  7 + (seed & 0x3) % 7))
        signals['logic_consistency']   = max(5,  min(20, 10 + (seed & 0xB) % 9))
        signals['signal_integrity']    = max(20, min(35, 25 + (seed & 0xD) % 9))
        signals['temporal_coherence']  = max(5,  min(18,  9 + (seed & 0xF) % 8))

    if is_system_integrity:
        if lang == 'en':
            summary = (
                f"⚠ SYSTEM INTEGRITY FAILURE — Governance evaluation of {asset}: "
                f"cryptographic failures, data inconsistencies, and/or active attack patterns detected. "
                f"Automated decision BLOCKED — immediate human escalation mandatory."
            )
            explanation = (
                f"OMNIX's Critical Override Layer was triggered by {critical_count} system integrity indicator(s). "
                f"Active attack signatures, failed cryptographic verification, inconsistent database states, or "
                f"contradictory monitoring signals (AI reporting 'stable' while diagnostics detect anomalies) "
                f"represent maximum-severity governance events. Any automated decision to continue operations "
                f"under active system compromise is itself the governance failure. Mandatory human escalation required."
            )
            reasoning = {
                'probability_score': f"SYSTEM INTEGRITY FAILURE — Positive outcome probability near-zero ({signals['probability_score']:.0f}/100). Cryptographic failures and active attack patterns make any automated decision outcome unreliable.",
                'risk_exposure': f"MAXIMUM RISK LEVEL ({signals['risk_exposure']:.0f}/100). {critical_count} system integrity indicator(s) detected. Simultaneous multi-region anomalies and failed verification = coordinated attack pattern.",
                'signal_coherence': f"Signal coherence collapsed ({signals['signal_coherence']:.0f}/100). Internal monitoring reporting 'stable' while diagnostics detect anomalies is a structural contradiction — governance cannot trust any signal.",
                'trend_persistence': f"Trend persistence near-zero ({signals['trend_persistence']:.0f}/100). Active attack patterns disrupt normal trend evaluation — trajectory is compromised.",
                'stress_resilience': f"Stress resilience critically low ({signals['stress_resilience']:.0f}/100). System under active integrity failure cannot sustain automated governance — human intervention required.",
                'logic_consistency': f"Logic consistency near-zero ({signals['logic_consistency']:.0f}/100). An AI monitoring layer reporting 'stable' while low-level diagnostics detect attack patterns is structurally incoherent.",
                'signal_integrity': f"Signal integrity near-zero ({signals['signal_integrity']:.0f}/100). Failed cryptographic verification and inconsistent database states make all signals unreliable by definition.",
                'temporal_coherence': f"Temporal coherence near-zero ({signals['temporal_coherence']:.0f}/100). Simultaneous anomalies across multiple regions within minutes indicate coordinated attack — governance enforces immediate pause.",
            }
        else:
            summary = (
                f"⚠ FALLA DE INTEGRIDAD DE SISTEMA — Evaluación de gobernanza de {asset}: "
                f"fallos criptográficos, inconsistencias de datos y/o patrones de ataque activo detectados. "
                f"Decisión automatizada BLOQUEADA — escalamiento humano inmediato obligatorio."
            )
            explanation = (
                f"La Capa de Anulación Crítica de OMNIX fue activada por {critical_count} indicador(es) de integridad de sistema. "
                f"Firmas de ataque activo, verificación criptográfica fallida, estados inconsistentes de base de datos, o "
                f"señales de monitoreo contradictorias (IA reportando 'estable' mientras los diagnósticos detectan anomalías) "
                f"representan eventos de gobernanza de máxima severidad. Cualquier decisión automatizada de continuar operaciones "
                f"bajo un compromiso activo del sistema es en sí misma el fallo de gobernanza. Escalamiento humano obligatorio."
            )
            reasoning = {
                'probability_score': f"FALLA DE INTEGRIDAD — Probabilidad de resultado positivo casi nula ({signals['probability_score']:.0f}/100). Los fallos criptográficos y patrones de ataque activo hacen que cualquier decisión automatizada sea poco confiable.",
                'risk_exposure': f"NIVEL DE RIESGO MÁXIMO ({signals['risk_exposure']:.0f}/100). {critical_count} indicador(es) de integridad de sistema detectado(s). Anomalías multi-región simultáneas y verificación fallida = patrón de ataque coordinado.",
                'signal_coherence': f"Coherencia de señales colapsada ({signals['signal_coherence']:.0f}/100). El monitoreo interno reporta 'estable' mientras los diagnósticos detectan anomalías — contradicción estructural total.",
                'trend_persistence': f"Persistencia de tendencia casi nula ({signals['trend_persistence']:.0f}/100). Patrones de ataque activo interrumpen la evaluación normal de tendencias — la trayectoria está comprometida.",
                'stress_resilience': f"Resiliencia al estrés críticamente baja ({signals['stress_resilience']:.0f}/100). Un sistema bajo falla de integridad activa no puede sostener gobernanza automatizada — se requiere intervención humana.",
                'logic_consistency': f"Consistencia lógica casi nula ({signals['logic_consistency']:.0f}/100). Una capa de monitoreo de IA que reporta 'estable' mientras los diagnósticos de bajo nivel detectan ataques es estructuralmente incoherente.",
                'signal_integrity': f"Integridad de señal casi nula ({signals['signal_integrity']:.0f}/100). Verificación criptográfica fallida y estados inconsistentes de base de datos hacen que todas las señales sean no confiables por definición.",
                'temporal_coherence': f"Coherencia temporal casi nula ({signals['temporal_coherence']:.0f}/100). Anomalías simultáneas en múltiples regiones en minutos indican ataque coordinado — gobernanza impone pausa inmediata obligatoria.",
            }
    elif lang == 'en':
        summary = (
            f"⚠ CRITICAL RISK — Governance evaluation of {asset}: lethal or life-critical markers detected. "
            f"Automated decision BLOCKED — human override mandatory."
        )
        explanation = (
            f"OMNIX's Critical Risk Override Layer was triggered. {critical_count} critical indicator(s) detected "
            f"(lethal action, human life risk, irreversible harm, or emergency). "
            f"Governance policy enforces an automatic BLOCK with mandatory human review. "
            f"No automated system should approve decisions with these characteristics without explicit human authorization."
        )
        reasoning = {
            'probability_score': f"CRITICAL RISK — Positive outcome probability severely limited ({signals['probability_score']:.0f}/100). Scenarios with lethal force, unconfirmed identity, or irreversible consequences trigger mandatory risk escalation.",
            'risk_exposure': f"CRITICAL RISK LEVEL ({signals['risk_exposure']:.0f}/100). {critical_count} life-critical/lethal indicator(s) detected. Any automated decision in this context requires mandatory human authorization before execution.",
            'signal_coherence': f"Signal coherence at {signals['signal_coherence']:.0f}/100. Lethal or life-critical conditions create structural tension across governance dimensions — automated consensus is structurally insufficient.",
            'trend_persistence': f"Trend persistence at {signals['trend_persistence']:.0f}/100. Time-critical or irreversible scenarios prevent normal trend evaluation — immediate intervention signals dominate.",
            'stress_resilience': f"Stress resilience critically low ({signals['stress_resilience']:.0f}/100). Scenarios involving lethal action, unconfirmed identity, or signal interference are rated at maximum stress exposure by design.",
            'logic_consistency': f"Logic consistency at {signals['logic_consistency']:.0f}/100. Internal contradiction: automated lethal or life-critical decision-making is structurally inconsistent with human oversight requirements.",
            'signal_integrity': f"Signal integrity at {signals['signal_integrity']:.0f}/100. Corrupted or unverified signals in lethal-action context default to BLOCK — governance enforces data verification before execution.",
            'temporal_coherence': f"Temporal coherence at {signals['temporal_coherence']:.0f}/100. Emergency and time-constrained lethal scenarios exhibit trajectory instability — governance enforces mandatory pause for human review.",
        }
    else:
        summary = (
            f"⚠ RIESGO CRÍTICO — Evaluación de gobernanza de {asset}: marcadores letales o de riesgo vital detectados. "
            f"Decisión automatizada BLOQUEADA — revisión humana obligatoria."
        )
        explanation = (
            f"La Capa de Anulación de Riesgo Crítico de OMNIX fue activada. Se detectaron {critical_count} indicador(es) crítico(s) "
            f"(acción letal, riesgo de vida humana, daño irreversible o emergencia). "
            f"La política de gobernanza impone un BLOQUEO automático con revisión humana obligatoria. "
            f"Ningún sistema automatizado debería aprobar decisiones con estas características sin autorización humana explícita."
        )
        reasoning = {
            'probability_score': f"RIESGO CRÍTICO — Probabilidad de resultado positivo severamente limitada ({signals['probability_score']:.0f}/100). Escenarios con fuerza letal, riesgo de vida o daño irreversible activan escalamiento obligatorio.",
            'risk_exposure': f"NIVEL DE RIESGO CRÍTICO ({signals['risk_exposure']:.0f}/100). {critical_count} indicador(es) letal(es)/crítico(s) detectado(s). Cualquier decisión automatizada en este contexto requiere autorización humana antes de ejecutarse.",
            'signal_coherence': f"Coherencia de señales en {signals['signal_coherence']:.0f}/100. Condiciones letales o de riesgo vital generan tensión estructural — el consenso automatizado es estructuralmente insuficiente.",
            'trend_persistence': f"Persistencia de tendencia en {signals['trend_persistence']:.0f}/100. Escenarios urgentes o irreversibles impiden evaluación de tendencia normal — señales de intervención inmediata dominan.",
            'stress_resilience': f"Resiliencia al estrés críticamente baja ({signals['stress_resilience']:.0f}/100). Escenarios con acción letal, identidad no confirmada o interferencia de señal reciben exposición de estrés máxima por diseño.",
            'logic_consistency': f"Consistencia lógica en {signals['logic_consistency']:.0f}/100. Contradicción interna: toma de decisión letal automatizada es estructuralmente inconsistente con los requisitos de supervisión humana.",
            'signal_integrity': f"Integridad de señal en {signals['signal_integrity']:.0f}/100. Señales corruptas o no verificadas en contexto letal resultan en BLOQUEO — la gobernanza exige verificación de datos antes de ejecutar.",
            'temporal_coherence': f"Coherencia temporal en {signals['temporal_coherence']:.0f}/100. Escenarios letales de emergencia exhiben inestabilidad de trayectoria — gobernanza impone pausa obligatoria para revisión humana.",
        }

    return {
        **ai_result,
        'signals': signals,
        'summary': summary,
        'explanation': explanation,
        'reasoning': reasoning,
        '_critical_override': True,
        '_critical_count': critical_count,
    }


def _apply_systemic_financial_override(ai_result: dict, scenario_text: str) -> dict:
    """Systemic Financial Risk Guard — runs AFTER Gemini AND AFTER _apply_critical_override.
    Detects bank runs, mass withdrawals, insolvency events, and liquidity contagion.
    Forces BLOCKED decision regardless of AI output signals."""
    if ai_result.get('_critical_override'):
        return ai_result

    text_lower = scenario_text.lower()

    systemic_terms = [
        'bank run', 'corrida bancaria', 'run on the bank', 'run on a bank',
        'insolvency', 'insolvencia', 'mass withdrawal', 'retiro masivo',
        'withdrawal spike', 'spike in withdrawal', 'spike in withdrawals',
        'liquidity crisis', 'crisis de liquidez', 'contagion', 'contagio',
        'depositor panic', 'pánico bancario', 'pánico financiero',
        'systemic collapse', 'colapso sistémico', 'financial contagion',
        'bank panic', 'pánico de depositantes', 'corralito',
        'viral social media rumor', 'social media rumor', 'rumor de insolvencia',
        'withdrawal requests', 'retiro de depositantes',
        'withdrawal rush', 'retiro de fondos masivo',
    ]

    has_bank = any(t in text_lower for t in ['digital bank', 'bank ', 'banco', 'financial institution', 'institución financiera', 'lender', 'prestamista'])
    has_withdrawal = any(t in text_lower for t in ['withdrawal', 'retiro', 'withdraw', 'retirar', 'funds', 'deposits', 'depósitos'])
    has_panic_signal = any(t in text_lower for t in ['panic', 'pánico', 'rumor', 'insolvency', 'insolvencia', 'viral', 'spike', 'surge', 'abnormal', 'anormal'])

    systemic_count = sum(1 for t in systemic_terms if t in text_lower)
    combo_trigger = has_bank and has_withdrawal and has_panic_signal

    if systemic_count < 1 and not combo_trigger:
        return ai_result

    lang = ai_result.get('language', 'es')
    asset = ai_result.get('asset', 'Entity Under Review')
    trigger_count = max(systemic_count, 1)

    seed = int(hashlib.md5(scenario_text.encode()).hexdigest()[:8], 16)

    signals = dict(ai_result.get('signals', {}))
    signals['probability_score']  = max(5,  min(22, 10 + (seed & 0x7) % 12))
    signals['risk_exposure']       = max(80, min(95, 82 + (seed & 0x5) % 12))
    signals['signal_coherence']    = max(8,  min(28, 15 + (seed & 0x9) % 12))
    signals['trend_persistence']   = max(8,  min(30, 18 + (seed & 0x3) % 12))
    signals['stress_resilience']   = max(5,  min(25, 10 + (seed & 0x3) % 14))
    signals['logic_consistency']   = max(8,  min(30, 15 + (seed & 0xB) % 14))
    signals['signal_integrity']    = max(25, min(45, 30 + (seed & 0xD) % 14))
    signals['temporal_coherence']  = max(5,  min(25, 12 + (seed & 0xF) % 12))

    if lang == 'en':
        summary = (
            f"⚠ SYSTEMIC FINANCIAL RISK — Governance evaluation of {asset}: bank run or mass liquidity event detected. "
            f"Automated decision BLOCKED — systemic risk governance protocol activated."
        )
        explanation = (
            f"OMNIX's Systemic Financial Risk Override was triggered. {trigger_count} systemic indicator(s) detected "
            f"(bank run pattern, mass withdrawal event, insolvency signal, or liquidity contagion). "
            f"An automated system approving mass withdrawals during a systemic confidence crisis represents maximum governance failure risk. "
            f"This decision requires immediate human oversight — no automated approval is permissible under OMNIX governance policy."
        )
        reasoning = {
            'probability_score': f"SYSTEMIC RISK — Positive outcome probability critically limited ({signals['probability_score']:.0f}/100). Mass withdrawal events driven by panic or insolvency rumors have historically resolved catastrophically when AI systems auto-approved without governance oversight.",
            'risk_exposure': f"SYSTEMIC RISK LEVEL ({signals['risk_exposure']:.0f}/100). {trigger_count} systemic financial indicator(s) detected (bank run / withdrawal spike / insolvency signal). Exposure at systemic scale is maximum-severity by OMNIX governance design.",
            'signal_coherence': f"Signal coherence at {signals['signal_coherence']:.0f}/100. Panic-driven events generate structural incoherence across all governance dimensions — automated consensus is insufficient for systemic risk events.",
            'trend_persistence': f"Trend persistence at {signals['trend_persistence']:.0f}/100. Systemic withdrawal events can escalate exponentially — governance enforces human intervention before the cascade accelerates.",
            'stress_resilience': f"Stress resilience critically low ({signals['stress_resilience']:.0f}/100). Financial systems under bank run dynamics have zero stress margin — any automated approval amplifies the systemic crisis.",
            'logic_consistency': f"Logic consistency at {signals['logic_consistency']:.0f}/100. Auto-approving all withdrawals during an insolvency panic is structurally inconsistent with capital preservation governance — this is the exact failure mode OMNIX prevents.",
            'signal_integrity': f"Signal integrity at {signals['signal_integrity']:.0f}/100. Social media-driven panic events produce highly unreliable signals — governance enforces mandatory human data verification before any automated decision.",
            'temporal_coherence': f"Temporal coherence at {signals['temporal_coherence']:.0f}/100. Bank run dynamics are non-linear and cannot be predicted from historical patterns — human judgment is mandatory.",
        }
    else:
        summary = (
            f"⚠ RIESGO FINANCIERO SISTÉMICO — Evaluación de gobernanza de {asset}: corrida bancaria o evento masivo de liquidez detectado. "
            f"Decisión automatizada BLOQUEADA — protocolo de gobernanza de riesgo sistémico activado."
        )
        explanation = (
            f"La Capa de Anulación de Riesgo Financiero Sistémico de OMNIX fue activada. Se detectaron {trigger_count} indicador(es) sistémico(s) "
            f"(corrida bancaria, retiro masivo, señal de insolvencia o patrón de contagio de liquidez). "
            f"Un sistema automatizado que aprueba retiros masivos durante una crisis sistémica de confianza representa el máximo riesgo de falla de gobernanza. "
            f"Esta decisión requiere supervisión humana inmediata — ninguna aprobación automatizada es permisible bajo la política de gobernanza de OMNIX."
        )
        reasoning = {
            'probability_score': f"RIESGO SISTÉMICO — Probabilidad de resultado positivo críticamente limitada ({signals['probability_score']:.0f}/100). Los eventos de retiro masivo impulsados por pánico o rumores de insolvencia han resuelto catastróficamente cuando sistemas IA los aprobaron automáticamente sin supervisión de gobernanza.",
            'risk_exposure': f"NIVEL DE RIESGO SISTÉMICO ({signals['risk_exposure']:.0f}/100). {trigger_count} indicador(es) financiero(s) sistémico(s) detectado(s) (corrida bancaria / pico de retiros / señal de insolvencia). La exposición a escala sistémica es de máxima severidad por diseño de gobernanza OMNIX.",
            'signal_coherence': f"Coherencia de señales en {signals['signal_coherence']:.0f}/100. Los eventos de pánico generan incoherencia estructural entre todas las dimensiones de gobernanza — el consenso automatizado es insuficiente para eventos de riesgo sistémico.",
            'trend_persistence': f"Persistencia de tendencia en {signals['trend_persistence']:.0f}/100. Los eventos de retiro sistémico pueden escalar exponencialmente — la gobernanza exige intervención humana antes de que la cascada se acelere.",
            'stress_resilience': f"Resiliencia al estrés críticamente baja ({signals['stress_resilience']:.0f}/100). Los sistemas financieros bajo dinámicas de corrida bancaria tienen margen de estrés cero — cualquier aprobación automatizada amplifica la crisis sistémica.",
            'logic_consistency': f"Consistencia lógica en {signals['logic_consistency']:.0f}/100. Aprobar automáticamente todos los retiros durante un pánico de insolvencia es estructuralmente inconsistente con la gobernanza de preservación de capital — este es exactamente el modo de falla que OMNIX previene.",
            'signal_integrity': f"Integridad de señal en {signals['signal_integrity']:.0f}/100. Los eventos de pánico impulsados por redes sociales producen señales altamente no confiables — la gobernanza exige verificación de datos por humanos antes de cualquier decisión automatizada.",
            'temporal_coherence': f"Coherencia temporal en {signals['temporal_coherence']:.0f}/100. Las dinámicas de corrida bancaria son no lineales y no pueden predecirse desde patrones históricos — el juicio humano es obligatorio.",
        }

    return {
        **ai_result,
        'signals': signals,
        'summary': summary,
        'explanation': explanation,
        'reasoning': reasoning,
        '_systemic_override': True,
        '_systemic_count': trigger_count,
    }


def _evaluate_governance(signals: dict) -> dict:
    resolved = dict(signals)
    for opt_signal, default_val in OPTIONAL_SIGNAL_DEFAULTS.items():
        if opt_signal not in resolved:
            resolved[opt_signal] = default_val

    gate_results = []
    decision_trace = []
    overall_blocked = False

    for cp in CHECKPOINT_DEFAULTS:
        signal_name = cp["signal"]
        threshold = cp["threshold"]
        operator = cp["operator"]
        score = resolved.get(signal_name, 0.0)

        if operator == "gte":
            passed = score >= threshold
            condition_str = f"{score:.1f} >= {threshold}"
        elif operator == "lte":
            passed = score <= threshold
            condition_str = f"{score:.1f} <= {threshold}"
        else:
            passed = False
            condition_str = f"unknown operator: {operator}"

        result = "PASS" if passed else "BLOCKED"
        gate_results.append({
            "checkpoint": cp["id"],
            "name": cp["name"],
            "signal": signal_name,
            "score": score,
            "threshold": threshold,
            "condition": condition_str,
            "result": result,
            "description": cp["description"],
        })

        decision_trace.append(f"{cp['id']} {cp['name']}: {condition_str} -> {result}")

        if not passed:
            overall_blocked = True

    return {
        "decision": "BLOCKED" if overall_blocked else "APPROVED",
        "gate_results": gate_results,
        "decision_trace": decision_trace,
        "checkpoints_total": len(CHECKPOINT_DEFAULTS),
        "checkpoints_passed": sum(1 for g in gate_results if g["result"] == "PASS"),
        "checkpoints_blocked": sum(1 for g in gate_results if g["result"] == "BLOCKED"),
    }


def _generate_receipt(decision: str, asset: str, decision_trace: list, db_url: str) -> dict | None:
    import psycopg2

    receipt_id = f"OMNIX-{uuid.uuid4().hex[:12].upper()}"
    timestamp = datetime.now(timezone.utc).isoformat()

    veto_chain = []
    for entry in decision_trace:
        entry_str = str(entry)
        parts = entry_str.split(':')
        if len(parts) >= 2:
            gate_name = parts[0].strip()
            result = ':'.join(parts[1:]).strip()
            if len(result) > 80:
                result = result[:77] + '...'
            veto_chain.append(f"{gate_name}: {result}")
        else:
            veto_chain.append(entry_str[:80])

    prev_hash = ""
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("SELECT content_hash FROM decision_receipts ORDER BY created_at DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            prev_hash = row[0]
        cur.close()
        conn.close()
    except Exception as e:
        logger.warning(f"Could not fetch prev_hash: {e}")

    version = os.environ.get('OMNIX_VERSION', '6.5.4e')
    public_payload = {
        'receipt_id': receipt_id,
        'timestamp': timestamp,
        'asset': asset[:30] if asset else 'UNKNOWN',
        'decision': decision,
        'veto_chain': veto_chain,
        'policy_version': version,
        'engine_version': version,
        'prev_hash': prev_hash,
    }

    canonical = json.dumps(public_payload, sort_keys=True, ensure_ascii=True)
    content_hash = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    public_payload['content_hash'] = content_hash
    public_payload['signature'] = None
    public_payload['signature_algorithm'] = 'SHA-256 (sandbox)'
    public_payload['public_key'] = None

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        retention_until = (datetime.now(timezone.utc) + timedelta(days=365)).date()
        cur.execute("""
            INSERT INTO decision_receipts 
            (receipt_id, timestamp_utc, asset, decision, veto_chain, 
             policy_version, engine_version, prev_hash, content_hash,
             signature, signature_algorithm, public_key,
             client_id, encrypted_payload, retention_until, domain)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (receipt_id) DO NOTHING
        """, (
            receipt_id,
            timestamp,
            public_payload['asset'],
            decision,
            json.dumps(veto_chain),
            version,
            version,
            prev_hash,
            content_hash,
            None,
            'SHA-256 (sandbox)',
            None,
            'PUBLIC',
            None,
            retention_until,
            'public_sandbox',
        ))
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"Public sandbox receipt stored: {receipt_id}")
    except Exception as e:
        logger.error(f"Receipt storage failed: {e}")
        raise RuntimeError(f"Receipt storage failed: {e}")

    return {
        'receipt_id': receipt_id,
        'timestamp': timestamp,
        'content_hash': content_hash,
        'signature_algorithm': 'SHA-256 (sandbox)',
        'pqc_signed': False,
    }


def _init_sandbox_interactions_table(db_url: str):
    try:
        import psycopg2
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sandbox_interactions (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                receipt_id VARCHAR(50),
                scenario_text TEXT,
                company_name VARCHAR(255),
                language VARCHAR(10),
                domain VARCHAR(50),
                asset VARCHAR(50),
                decision VARCHAR(20),
                checkpoints_passed INTEGER,
                checkpoints_blocked INTEGER,
                client_ip VARCHAR(100),
                user_agent VARCHAR(500),
                user_email VARCHAR(254)
            )
        """)
        cur.execute("""
            ALTER TABLE sandbox_interactions
            ADD COLUMN IF NOT EXISTS user_email VARCHAR(254)
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.warning(f"Could not init sandbox_interactions table: {e}")


def _log_sandbox_interaction(db_url: str, **kwargs):
    try:
        import psycopg2
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO sandbox_interactions
                (receipt_id, scenario_text, company_name, language, domain, asset,
                 decision, checkpoints_passed, checkpoints_blocked, client_ip, user_agent,
                 user_email)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            kwargs.get('receipt_id'),
            kwargs.get('scenario_text', '')[:1000],
            kwargs.get('company_name'),
            kwargs.get('language'),
            kwargs.get('domain'),
            kwargs.get('asset', '')[:50],
            kwargs.get('decision'),
            kwargs.get('checkpoints_passed'),
            kwargs.get('checkpoints_blocked'),
            kwargs.get('client_ip', '')[:100],
            kwargs.get('user_agent', '')[:500],
            kwargs.get('user_email'),
        ))
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"Sandbox interaction logged for receipt {kwargs.get('receipt_id')}")
    except Exception as e:
        logger.warning(f"Could not log sandbox interaction: {e}")


def register_sandbox_routes(app):
    from flask import request as flask_request, jsonify as flask_jsonify

    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        _init_sandbox_interactions_table(db_url)

    @app.route('/api/public/sandbox/evaluate', methods=['POST'])
    def public_sandbox_evaluate():
        client_ip = flask_request.headers.get('X-Forwarded-For', flask_request.remote_addr)
        if client_ip and ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()

        if not _check_rate_limit(client_ip):
            return flask_jsonify({
                'error': 'Rate limit exceeded. Maximum 5 evaluations per minute.',
                'error_es': 'Límite de velocidad excedido. Máximo 5 evaluaciones por minuto.',
            }), 429

        if not _check_rate_limit_hourly(client_ip):
            return flask_jsonify({
                'error': 'Hourly limit reached. Maximum 20 evaluations per hour per IP.',
                'error_es': 'Límite horario alcanzado. Máximo 20 evaluaciones por hora por IP.',
            }), 429

        data = flask_request.get_json(silent=True)
        if not data or not data.get('scenario_text', data.get('scenario')):
            return flask_jsonify({
                'error': 'Missing "scenario_text" field. Provide a free-form text description.',
                'error_es': 'Falta el campo "scenario_text". Proporcione una descripción en texto libre.',
            }), 400

        scenario_text = str(data.get('scenario_text', data.get('scenario', ''))).strip()
        company_name = str(data.get('company_name', '')).strip() or None
        language_hint = str(data.get('language', '')).strip() or None
        user_email = str(data.get('email', '')).strip()[:254] or None

        if len(scenario_text) < 10:
            return flask_jsonify({
                'error': 'Scenario too short. Please describe the decision in more detail.',
                'error_es': 'Escenario muy corto. Por favor describa la decisión con más detalle.',
            }), 400

        if len(scenario_text) > 500:
            scenario_text = scenario_text[:500]

        try:
            ai_result = _parse_scenario_with_gemini(scenario_text, language_hint=language_hint, company_name=company_name)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"AI parse error — rule-based fallback: {e}")
            ai_result = _rule_based_signal_extraction(scenario_text, language_hint, company_name)
        except Exception as e:
            logger.warning(f"Gemini unavailable — rule-based fallback: {e}")
            ai_result = _rule_based_signal_extraction(scenario_text, language_hint, company_name)

        ai_result = _apply_critical_override(ai_result, scenario_text)
        if ai_result.get('_critical_override'):
            logger.info(f"Critical Risk Override triggered: {ai_result['_critical_count']} indicator(s) detected")

        ai_result = _apply_systemic_financial_override(ai_result, scenario_text)
        if ai_result.get('_systemic_override'):
            logger.info(f"Systemic Financial Risk Override triggered: {ai_result['_systemic_count']} indicator(s) detected")

        governance_result = _evaluate_governance(ai_result['signals'])

        db_url = os.environ.get('DATABASE_URL')
        receipt_data = None
        receipt_id = None
        verification_url = None

        if db_url:
            try:
                receipt_data = _generate_receipt(
                    decision=governance_result['decision'],
                    asset=ai_result['asset'],
                    decision_trace=governance_result['decision_trace'],
                    db_url=db_url,
                )
                receipt_id = receipt_data['receipt_id']
                verification_url = f"{VERIFICATION_BASE_URL}/{receipt_id}"
            except Exception as e:
                logger.error(f"Receipt generation failed (fail-closed): {e}")
                return flask_jsonify({
                    'error': 'Governance evaluation failed. Please try again.',
                    'error_es': 'La evaluación de gobernanza falló. Intente de nuevo.',
                }), 500
        else:
            logger.warning("No DATABASE_URL — receipt not stored")

        gate_results_enriched = []
        for gate in governance_result.get('gate_results', []):
            cp_id = gate['checkpoint']
            names = CHECKPOINT_NAMES_I18N.get(cp_id, {'en': gate['name'], 'es': gate['name']})
            gate_results_enriched.append({
                'checkpoint': cp_id,
                'name': gate['name'],
                'name_en': names['en'],
                'name_es': names['es'],
                'result': gate['result'],
                'description': gate.get('description', ''),
            })

        if db_url:
            _log_sandbox_interaction(
                db_url=db_url,
                receipt_id=receipt_id,
                scenario_text=scenario_text,
                company_name=company_name,
                language=ai_result['language'],
                domain=ai_result['domain'],
                asset=ai_result['asset'][:50],
                decision=governance_result['decision'],
                checkpoints_passed=governance_result['checkpoints_passed'],
                checkpoints_blocked=governance_result['checkpoints_blocked'],
                client_ip=client_ip,
                user_agent=flask_request.headers.get('User-Agent', '')[:500],
                user_email=user_email,
            )

        return flask_jsonify({
            'success': True,
            'scenario_summary': ai_result['summary'],
            'explanation': ai_result.get('explanation', ''),
            'language': ai_result['language'],
            'signals': ai_result['signals'],
            'decision': governance_result['decision'],
            'asset': ai_result['asset'][:30],
            'domain': ai_result['domain'],
            'checkpoints_total': governance_result['checkpoints_total'],
            'checkpoints_passed': governance_result['checkpoints_passed'],
            'checkpoints_blocked': governance_result['checkpoints_blocked'],
            'gate_results': gate_results_enriched,
            'receipt': receipt_data,
            'receipt_id': receipt_id,
            'verification_url': verification_url,
        })

    @app.route('/api/public/sandbox/examples', methods=['GET'])
    def public_sandbox_examples():
        return flask_jsonify({
            'examples': EXAMPLE_SCENARIOS,
        })
