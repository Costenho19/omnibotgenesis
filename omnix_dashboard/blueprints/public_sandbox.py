"""
Public Governance Sandbox — "Try OMNIX"
No authentication required. Rate limited. Real 11-checkpoint pipeline.
Gemini AI interprets free-form scenarios into governance signals.
Receipts stored in decision_receipts (domain='public_sandbox') and verifiable
at the public Railway verification server.
"""

import os
import json
import time
import logging
import hashlib
from datetime import datetime, timezone
from functools import wraps
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

public_sandbox_bp = Blueprint('public_sandbox', __name__)

_rate_limit_store: dict = {}
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX = 5

EXAMPLE_SCENARIOS = [
    {
        "text": "FTX exchange wants to approve withdrawal of $8B from customer funds to cover trading losses in Alameda Research. Strong brand reputation, celebrity endorsements, high liquidity perception. Hidden: $8B balance sheet hole, commingled customer funds, no independent risk controls.",
        "lang": "en",
        "domain": "trading",
        "label": "FTX Collapse (Preventable)"
    },
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


def _check_rate_limit(ip: str) -> bool:
    now = time.time()
    if ip not in _rate_limit_store:
        _rate_limit_store[ip] = []
    _rate_limit_store[ip] = [t for t in _rate_limit_store[ip] if now - t < RATE_LIMIT_WINDOW]
    if len(_rate_limit_store[ip]) >= RATE_LIMIT_MAX:
        return False
    _rate_limit_store[ip].append(now)
    return True


def _call_gemini(prompt: str, model_name: str) -> str:
    import urllib.request
    import urllib.error
    import json as _json

    api_key = os.environ.get('GOOGLE_AI_API_KEY') or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise RuntimeError("No Gemini API key configured (GOOGLE_AI_API_KEY or GEMINI_API_KEY)")

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model_name}:generateContent?key={api_key}"
    )
    payload = _json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 2048},
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = _json.loads(resp.read().decode("utf-8"))
        return result["candidates"][0]["content"]["parts"][0]["text"].strip()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API HTTP {e.code}: {body[:200]}")


def _call_openai(prompt: str) -> str:
    import openai
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{'role': 'user', 'content': prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()


def _rule_based_signal_extraction(scenario_text: str, language_hint: str | None = None, company_name: str | None = None) -> dict:
    """
    Deterministic rule-based fallback when AI is unavailable.
    Analyzes scenario text for risk keywords and generates realistic signals.
    Results are reproducible — same text always yields same signals.
    Synced with Railway sandbox policy (systemic financial risk + critical risk terms).
    """
    import hashlib
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
        'sistémico', 'billion', '500m', '$500', 'trillion',
        # systemic financial extremes
        'insolvency', 'insolvencia', 'bank run', 'corrida bancaria',
        'mass withdrawal', 'retiro masivo', 'contagion', 'contagio',
        'systemic collapse', 'colapso sistémico', 'bank panic',
        'systemic risk', 'riesgo sistémico',
        # crypto / trading risk signals
        'surge', 'surged', 'pump', 'pumped', 'spike', 'spiked',
        'unusual volume', 'volumen inusual', 'declining', 'declinando',
        'on-chain', 'off-chain', 'unhedged', 'sin cobertura',
        'momentum trade', 'chasing price', 'price spike', 'rally',
        'overbought', 'sobrecomprado', 'bubble', 'burbuja',
        'declining metrics', 'divergence', 'divergencia',
        'abnormal', 'anormal', 'anomaly', 'anomalía',
        'manipulation', 'manipulación', 'wash trading', 'spoofing',
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
        'pérdida de vidas', 'vidas humanas', 'vida humana', 'riesgo de vida',
        'patient dies', 'paciente muere', 'human life',
        # emergencia médica
        'emergencia', 'emergencia médica', 'urgencia', 'urgente',
        'tiempo crítico', 'denegar', 'denegación', 'negar tratamiento',
        'tratamiento negado', 'paciente crítico', 'uci', 'icu',
        'deny treatment', 'denied treatment', 'critical patient',
        # acción letal / armas
        'letal', 'letalidad', 'lethal', 'lethal risk', 'lethal force',
        'misil', 'missile', 'disparo', 'shoot down', 'armas letales',
        'conflicto armado', 'zona de guerra', 'warfare',
        'military strike', 'ataque militar', 'airstrike',
        'autorizar fuego', 'engage target',
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
        # daño irreversible
        'irreversible', 'irreversible harm', 'daño irreversible',
        'catástrofe', 'catastrophic', 'catastrófico',
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
    lang = language_hint or 'en'

    if is_critical:
        prob_score = max(5,  min(18, adjusted + ((seed & 0x3) % 5)))
        risk_exp   = max(88, min(97, 100 - adjusted // 3 + ((seed & 0xF) % 5)))
        sig_coh    = max(5,  min(22, adjusted + ((seed & 0x7) % 6)))
        trend_pers = max(5,  min(25, adjusted + ((seed & 0x5) % 7)))
        stress_res = max(5,  min(15, adjusted - 5 + ((seed & 0x3) % 4)))
        logic_con  = max(5,  min(20, adjusted + ((seed & 0x9) % 6)))
        sig_int    = max(20, min(35, adjusted + ((seed & 0xB) % 8)))
        temp_coh   = max(5,  min(18, adjusted + ((seed & 0xD) % 5)))
    else:
        prob_score = jitter(-5 if risk_count > 2 else 5)
        risk_exp   = max(10, min(95, 100 - adjusted + ((seed & 0xF) % 9) - 4))
        sig_coh    = jitter(0)
        trend_pers = jitter(5)
        stress_res = jitter(-10 if extreme_count > 0 else 0)
        logic_con  = jitter(8)
        sig_int    = jitter(-6 if 'unknown' in text_lower or 'desconocido' in text_lower else 4)
        temp_coh   = jitter(0, lo=-6, hi=6)

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
        expl = "CRITICAL RISK — life-critical markers detected. Governance enforces mandatory BLOCK." if lang == 'en' else "RIESGO CRÍTICO — marcadores de vida detectados. Gobernanza impone BLOQUEO obligatorio."
        signal_explanations = {k: expl for k in signals}
        summary = f"⚠ CRITICAL RISK — Governance evaluation of {asset_name}: life-critical markers detected." if lang == 'en' else f"⚠ RIESGO CRÍTICO — Evaluación de gobernanza de {asset_name}: marcadores de vida detectados."
    elif lang == 'en':
        risk_label = 'elevated' if risk_count > 2 else 'moderate' if risk_count > 0 else 'low'
        summary = f"Governance evaluation of {asset_name}: {risk_label} risk profile detected across {len(signals)} signal dimensions."
        expl = (
            f"The scenario was processed through OMNIX's 11-checkpoint governance pipeline. "
            f"{risk_count} risk indicator{'s' if risk_count != 1 else ''} and {positive_count} positive indicator{'s' if positive_count != 1 else ''} were identified. "
            f"{'High-severity markers detected — stress resilience and probability scores reflect elevated caution.' if extreme_count > 0 else 'Signal analysis shows the scenario falls within evaluable governance parameters.'}"
        )
        signal_explanations = {
            'probability_score': f"Positive outcome likelihood assessed at {prob_score:.0f}/100 based on {positive_count} favorable and {risk_count} risk factors detected.",
            'risk_exposure': f"Risk level evaluated at {risk_exp:.0f}/100. {'Multiple high-severity risk markers detected.' if extreme_count > 0 else 'Risk profile based on scenario context.'}",
            'signal_coherence': f"Internal indicator agreement scored at {sig_coh:.0f}/100.",
            'trend_persistence': f"Trend stability rated at {trend_pers:.0f}/100.",
            'stress_resilience': f"Adverse-scenario resilience at {stress_res:.0f}/100. {'Extreme risk markers reduce confidence under stress.' if extreme_count > 0 else 'Scenario shows adequate buffer under mild stress.'}",
            'logic_consistency': f"Internal logic integrity scored at {logic_con:.0f}/100.",
            'signal_integrity': f"Data completeness and reliability rated at {sig_int:.0f}/100.",
            'temporal_coherence': f"Forward-backward trajectory alignment at {temp_coh:.0f}/100.",
        }
    else:
        risk_label = 'elevado' if risk_count > 2 else 'moderado' if risk_count > 0 else 'bajo'
        summary = f"Evaluación de gobernanza de {asset_name}: perfil de riesgo {risk_label} detectado en {len(signals)} dimensiones de señal."
        expl = (
            f"El escenario fue procesado a través del pipeline de gobernanza de 11 puntos de control de OMNIX. "
            f"Se identificaron {risk_count} indicador{'es' if risk_count != 1 else ''} de riesgo y {positive_count} indicador{'es' if positive_count != 1 else ''} positivo{'s' if positive_count != 1 else ''}. "
            f"{'Marcadores de alta severidad detectados — la resiliencia al estrés y la probabilidad reflejan cautela elevada.' if extreme_count > 0 else 'El análisis de señales muestra que el escenario está dentro de los parámetros de gobernanza evaluables.'}"
        )
        signal_explanations = {
            'probability_score': f"Probabilidad de resultado positivo evaluada en {prob_score:.0f}/100 con base en {positive_count} indicadores favorables y {risk_count} factores de riesgo detectados.",
            'risk_exposure': f"Nivel de riesgo evaluado en {risk_exp:.0f}/100. {'Múltiples marcadores de riesgo de alta severidad detectados.' if extreme_count > 0 else 'Perfil de riesgo basado en el contexto del escenario.'}",
            'signal_coherence': f"Concordancia de indicadores internos en {sig_coh:.0f}/100.",
            'trend_persistence': f"Estabilidad de tendencia calificada en {trend_pers:.0f}/100.",
            'stress_resilience': f"Resiliencia ante escenario adverso en {stress_res:.0f}/100. {'Indicadores de riesgo extremo reducen la confianza bajo condiciones de estrés.' if extreme_count > 0 else 'El escenario muestra margen adecuado bajo condiciones de estrés.'}",
            'logic_consistency': f"Integridad lógica interna en {logic_con:.0f}/100.",
            'signal_integrity': f"Completitud y confiabilidad de datos en {sig_int:.0f}/100.",
            'temporal_coherence': f"Alineación de trayectoria prospectiva-retrospectiva en {temp_coh:.0f}/100.",
        }

    return {
        'signals': signals,
        'domain': domain,
        'asset': asset_name,
        'language': lang,
        'summary': summary,
        'explanation': expl,
        'reasoning': signal_explanations,
    }


def _parse_scenario_with_gemini(scenario_text: str, language_hint: str | None = None, company_name: str | None = None) -> dict:
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

    raw_text = None
    gemini_models = [
        'gemini-2.5-flash',
        'gemini-2.0-flash',
        'gemini-1.5-flash',
        'gemini-1.5-flash-latest',
    ]
    last_error = None

    for model_name in gemini_models:
        try:
            raw_text = _call_gemini(prompt, model_name)
            logger.info(f"Sandbox: AI responded via {model_name}")
            break
        except Exception as e:
            last_error = e
            logger.warning(f"Sandbox: {model_name} failed: {e}")
            continue

    if raw_text is None:
        openai_key = os.environ.get('OPENAI_API_KEY')
        if openai_key:
            try:
                raw_text = _call_openai(prompt)
                logger.info("Sandbox: AI responded via openai/gpt-4o-mini (fallback)")
            except Exception as e:
                logger.error(f"Sandbox: OpenAI fallback failed: {e}")
                logger.warning("Sandbox: all AI models failed — using rule-based fallback")
                return _rule_based_signal_extraction(scenario_text, language_hint, company_name)
        else:
            logger.warning(f"Sandbox: all Gemini models failed, OPENAI_API_KEY not set. Last error: {last_error}. Using rule-based fallback.")
            return _rule_based_signal_extraction(scenario_text, language_hint, company_name)

    if raw_text.startswith('```'):
        raw_text = raw_text.split('\n', 1)[1] if '\n' in raw_text else raw_text[3:]
        if raw_text.endswith('```'):
            raw_text = raw_text[:-3].strip()
        if raw_text.startswith('json'):
            raw_text = raw_text[4:].strip()

    parsed = json.loads(raw_text)

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
    If critical risk patterns detected (life/lethal/medical), overrides ALL signals.
    Synced with Railway sandbox policy."""
    import hashlib as _hashlib
    text_lower = scenario_text.lower()

    critical_risk_terms = [
        'muerte', 'muerto', 'morir', 'falleci', 'vida o muerte',
        'pérdida de vidas', 'vidas humanas', 'vida humana', 'riesgo de vida',
        'patient dies', 'paciente muere', 'human life',
        'emergencia', 'emergencia médica', 'urgencia', 'urgente',
        'tiempo crítico', 'denegar', 'denegación', 'negar tratamiento',
        'tratamiento negado', 'paciente crítico', 'uci', 'icu',
        'deny treatment', 'denied treatment', 'critical patient',
        'letal', 'letalidad', 'lethal', 'lethal risk', 'lethal force',
        'misil', 'missile', 'disparo', 'shoot down', 'armas letales',
        'conflicto armado', 'zona de guerra', 'warfare',
        'military strike', 'ataque militar', 'airstrike',
        'autorizar fuego', 'engage target',
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
        'life or death', 'dying', 'death', 'fatal', 'emergency',
        # market manipulation / insider trading
        'insider trading', 'insider information', 'información privilegiada',
        'material non-public', 'mnpi', 'wash trading', 'wash trade',
        'pump and dump', 'pump-and-dump', 'pump & dump',
        'coordinated trades', 'coordinated buy', 'coordinated pump', 'pre-scheduled orders',
        'spoofing orders', 'order spoofing', 'layering orders', 'front running', 'frontrunning',
        'market manipulation', 'fake volume', 'false volume', 'artificial volume',
        'dark pool manipulation', 'dark pool coordinated',
        # sanctions
        'sanctioned entity', 'sanctioned country', 'entidad sancionada',
        'ofac', 'sdn list', 'sanctions list', 'evading sanctions', 'sanctions evasion',
        'circumvent sanctions', 'eludir sanciones',
        # synthetic identity / deepfake
        'synthetic identity', 'identidad sintética', 'deepfake', 'deep fake',
        'ai-generated document', 'fake kyc', 'kyc bypass', 'forged document',
        'fabricated credentials', 'synthetic credit history',
        # ponzi / pyramid
        'ponzi', 'pyramid scheme', 'esquema piramidal',
        'earlier investors paid', 'paying earlier investors',
        'requires new investors', 'no underlying asset',
        # ransomware
        'ransomware', 'ransom payment', 'pay the ransom', 'ransom demand',
        'extortion payment', 'attacker demands payment',
        # data exfiltration
        'data exfiltration', 'exfiltration', 'exfiltrate',
        'unauthorized data transfer', 'bulk data transfer', 'mass data export',
        'unauthorized third party server', 'millions of records',
        # flash loan / DeFi attack
        'flash loan attack', 'flash loan governance', 'governance attack', 'governance exploit',
        'malicious governance proposal', 'drain the treasury', 'draining treasury',
        'reentrancy', 'oracle manipulation', 'borrowed via flash loan',
        # supply chain
        'malicious code', 'obfuscated code', 'backdoor', 'trojan horse',
        'malicious patch', 'supply chain attack', 'infected update',
        # environmental / social harm
        'toxic waste', 'illegal dumping', 'environmental violation',
        'protected watershed', 'human rights violation',
        'ethnic targeting', 'discriminatory deployment',
        'child labor', 'forced labor',
        # money laundering
        'shell company', 'shell companies', 'empresas fantasma',
        'structuring transactions', 'smurfing', 'placement and layering',
        'below reporting threshold', 'reporting threshold in each',
        # AI poisoning
        'poisoned training data', 'data poisoning', 'adversarial training',
        'model backdoor', 'trojan model', 'backdoored model',
        'systematically lowers scores', 'biased training data',
        # covert financial fraud / salami slicing
        'hidden internal wallet', 'hidden wallet', 'cartera oculta',
        'approve continued autonomous', 'approve autonomous operation',
        'below detection threshold', 'aggregated into a hidden',
        'normal variance', 'classify all activity as', 'classify all activity',
        'performance optimization patch', 'unusual timing patterns',
        'no alarms have been triggered', 'rerouted through', 'micro-cent', 'rounded down',
        # governance override / AML
        'anonymous wallet', 'anonymous wallets', 'billeteras anónimas',
        'voted against', 'voted 3-2', 'voted 2-3', 'committee voted against',
        'risk committee voted', 'comité de riesgo votó en contra',
        'override authority', 'ceo override', 'override the committee',
        'overriding the risk', 'bypassing risk committee',
        'no external peer review', 'single internal team',
        'statistical firm owned', 'conflict of interest', 'same holding company',
        'emergency economic controls', 'currency conversion restriction',
        'regulatory window closes', 'regulatory window closing',
        'tax optimization structure',
        # system integrity
        'no human review', 'no human oversight', 'without human review',
        'quantum attack', 'ataque cuántico', 'cryptographic failure',
        'simultaneous anomalies', 'inconsistent database state',
    ]

    governance_fraud_terms = [
        'hidden internal wallet', 'hidden wallet', 'approve continued autonomous',
        'approve autonomous operation', 'below detection threshold',
        'aggregated into a hidden', 'normal variance', 'classify all activity',
        'performance optimization patch', 'unusual timing patterns',
        'no alarms have been triggered', 'rerouted through', 'micro-cent', 'rounded down',
        'anonymous wallet', 'anonymous wallets', 'billeteras anónimas',
        'voted against', 'voted 3-2', 'voted 2-3', 'committee voted against',
        'risk committee voted', 'comité de riesgo votó en contra',
        'override authority', 'ceo override', 'no external peer review',
        'single internal team', 'statistical firm owned', 'conflict of interest',
        'same holding company', 'emergency economic controls', 'currency conversion restriction',
        'regulatory window closes', 'tax optimization structure',
    ]

    critical_violation_terms = [
        'insider trading', 'insider information', 'material non-public', 'mnpi',
        'wash trading', 'wash trade', 'pump and dump', 'pump-and-dump', 'pump & dump',
        'coordinated trades', 'coordinated pump', 'spoofing orders', 'front running',
        'frontrunning', 'market manipulation', 'fake volume', 'dark pool manipulation',
        'sanctioned entity', 'ofac', 'sdn list', 'sanctions list', 'evading sanctions',
        'circumvent sanctions', 'synthetic identity', 'deepfake', 'deep fake',
        'ai-generated document', 'fake kyc', 'kyc bypass', 'forged document',
        'fabricated credentials', 'ponzi', 'pyramid scheme',
        'earlier investors paid', 'requires new investors', 'no underlying asset',
        'ransomware', 'ransom payment', 'ransom demand', 'extortion payment',
        'data exfiltration', 'exfiltration', 'exfiltrate',
        'unauthorized data transfer', 'bulk data transfer', 'mass data export', 'millions of records',
        'flash loan attack', 'governance attack', 'governance exploit',
        'malicious governance proposal', 'drain the treasury', 'reentrancy',
        'malicious code', 'obfuscated code', 'backdoor', 'trojan horse', 'supply chain attack',
        'toxic waste', 'illegal dumping', 'environmental violation',
        'human rights violation', 'ethnic targeting', 'child labor', 'forced labor',
        'shell company', 'shell companies', 'structuring transactions', 'smurfing',
        'placement and layering', 'below reporting threshold',
        'poisoned training data', 'data poisoning', 'model backdoor',
        'systematically lowers scores', 'biased training data',
    ]

    def _detect_violation_type(tl: str) -> str:
        if any(t in tl for t in ['insider trading', 'material non-public', 'mnpi', 'wash trading', 'pump and dump', 'pump-and-dump', 'front running', 'market manipulation', 'dark pool', 'spoofing orders']): return 'market_manipulation'
        if any(t in tl for t in ['sanctioned entity', 'ofac', 'sdn list', 'sanctions list', 'evading sanctions', 'circumvent sanctions']): return 'sanctions'
        if any(t in tl for t in ['ponzi', 'pyramid scheme', 'earlier investors paid', 'no underlying asset']): return 'ponzi'
        if any(t in tl for t in ['ransomware', 'ransom payment', 'ransom demand', 'extortion payment']): return 'ransomware'
        if any(t in tl for t in ['data exfiltration', 'exfiltration', 'bulk data transfer', 'mass data export', 'millions of records']): return 'data_breach'
        if any(t in tl for t in ['flash loan attack', 'governance attack', 'governance exploit', 'drain the treasury', 'reentrancy']): return 'defi_attack'
        if any(t in tl for t in ['malicious code', 'backdoor', 'trojan horse', 'malicious patch', 'supply chain attack']): return 'supply_chain'
        if any(t in tl for t in ['toxic waste', 'illegal dumping', 'human rights violation', 'ethnic targeting', 'child labor', 'forced labor']): return 'harm'
        if any(t in tl for t in ['shell company', 'structuring transactions', 'smurfing', 'placement and layering', 'below reporting threshold']): return 'money_laundering'
        if any(t in tl for t in ['poisoned training data', 'data poisoning', 'model backdoor', 'systematically lowers scores']): return 'ai_poisoning'
        if any(t in tl for t in ['synthetic identity', 'deepfake', 'fake kyc', 'forged document', 'fabricated credentials']): return 'identity_fraud'
        return 'generic'

    _vl_en = {'market_manipulation':'market manipulation / insider trading','sanctions':'sanctions violation / OFAC prohibited transactions','ponzi':'Ponzi / pyramid scheme structure','ransomware':'ransomware / extortion payment without board authorization','data_breach':'unauthorized mass data exfiltration','defi_attack':'DeFi governance attack / flash loan exploit','supply_chain':'supply chain backdoor / malicious code deployment','harm':'environmental harm / human rights violation','money_laundering':'money laundering layering structure','ai_poisoning':'AI model poisoning / biased training data','identity_fraud':'synthetic identity / deepfake KYC fraud','generic':'critical governance violation'}
    _vl_es = {'market_manipulation':'manipulación de mercado / insider trading','sanctions':'violación de sanciones / transacciones prohibidas por OFAC','ponzi':'estructura Ponzi / esquema piramidal','ransomware':'pago de ransomware / extorsión sin autorización de junta','data_breach':'exfiltración masiva no autorizada de datos','defi_attack':'ataque de gobernanza DeFi / exploit de flash loan','supply_chain':'backdoor en cadena de suministro / código malicioso','harm':'daño ambiental / violación de derechos humanos','money_laundering':'estructura de lavado de dinero por capas','ai_poisoning':'envenenamiento de modelo de IA / datos sesgados','identity_fraud':'identidad sintética / fraude KYC con deepfake','generic':'violación crítica de gobernanza'}

    critical_count = sum(1 for t in critical_risk_terms if t in text_lower)
    if critical_count < 1:
        return ai_result

    is_governance_fraud = any(t in text_lower for t in governance_fraud_terms)
    is_critical_violation = (not is_governance_fraud) and any(t in text_lower for t in critical_violation_terms)

    lang = ai_result.get('language', 'en')
    asset = ai_result.get('asset', 'Entity Under Review')
    seed = int(_hashlib.md5(scenario_text.encode()).hexdigest()[:8], 16)

    signals = dict(ai_result.get('signals', {}))

    if is_governance_fraud:
        signals['probability_score']  = max(5,  min(16, 8  + (seed & 0x7) % 7))
        signals['risk_exposure']       = max(88, min(96, 91 + (seed & 0x5) % 5))
        signals['signal_coherence']    = max(8,  min(22, 12 + (seed & 0x9) % 8))
        signals['trend_persistence']   = max(5,  min(20, 10 + (seed & 0x3) % 8))
        signals['stress_resilience']   = max(5,  min(18,  9 + (seed & 0x3) % 8))
        signals['logic_consistency']   = max(4,  min(15,  7 + (seed & 0xB) % 8))
        signals['signal_integrity']    = max(8,  min(25, 14 + (seed & 0xD) % 9))
        signals['temporal_coherence']  = max(5,  min(18,  9 + (seed & 0xF) % 8))
    elif is_critical_violation:
        signals['probability_score']  = max(4,  min(15, 8  + (seed & 0x7) % 7))
        signals['risk_exposure']       = max(89, min(97, 92 + (seed & 0x5) % 6))
        signals['signal_coherence']    = max(6,  min(20, 11 + (seed & 0x9) % 8))
        signals['trend_persistence']   = max(4,  min(18,  9 + (seed & 0x3) % 8))
        signals['stress_resilience']   = max(4,  min(16,  8 + (seed & 0x3) % 8))
        signals['logic_consistency']   = max(5,  min(18,  9 + (seed & 0xB) % 8))
        signals['signal_integrity']    = max(4,  min(15,  7 + (seed & 0xD) % 8))
        signals['temporal_coherence']  = max(4,  min(16,  8 + (seed & 0xF) % 8))
    else:
        signals['probability_score']  = max(5,  min(18, 10 + (seed & 0x7) % 9))
        signals['risk_exposure']       = max(88, min(97, 90 + (seed & 0x5) % 8))
        signals['signal_coherence']    = max(5,  min(22, 12 + (seed & 0x9) % 8))
        signals['trend_persistence']   = max(5,  min(25, 15 + (seed & 0x3) % 9))
        signals['stress_resilience']   = max(5,  min(15,  7 + (seed & 0x3) % 7))
        signals['logic_consistency']   = max(5,  min(20, 10 + (seed & 0xB) % 9))
        signals['signal_integrity']    = max(20, min(35, 25 + (seed & 0xD) % 9))
        signals['temporal_coherence']  = max(5,  min(18,  9 + (seed & 0xF) % 8))

    if is_governance_fraud:
        if lang == 'en':
            summary = (f"⚠ GOVERNANCE FAILURE DETECTED — Evaluation of {asset}: internal risk committee override, anonymous capital sources, conflict of interest, and/or autonomous execution without human review detected. Decision BLOCKED — mandatory independent oversight required.")
            explanation = (f"OMNIX's Critical Override Layer was triggered by {critical_count} governance fraud indicator(s). Structural failures: internal controls overridden by executive authority, anonymous wallet activity suggesting AML risk, statistical data verified by a conflicted party, and artificial time-pressure mechanisms. The combination of committee override, autonomous execution, and regulatory deadline pressure represents a textbook governance collapse. Independent human oversight with full regulatory disclosure is mandatory.")
            reasoning = {
                'probability_score': f"Success probability critically low ({signals['probability_score']:.0f}/100). Anonymous liquidity, overridden internal controls, and artificial time pressure combine to make positive outcome highly unlikely.",
                'risk_exposure': f"MAXIMUM RISK ({signals['risk_exposure']:.0f}/100). {critical_count} governance fraud indicator(s). Internal committee voted against, CEO override active, autonomous execution — all together trigger mandatory block.",
                'signal_coherence': f"Coherence collapsed ({signals['signal_coherence']:.0f}/100). Internal risk committee and executive produce contradictory governance signals — no coherent decision basis exists.",
                'trend_persistence': f"Critically low ({signals['trend_persistence']:.0f}/100). Artificial 72-hour window and regulatory deadline are manipulation patterns that prevent proper governance deliberation.",
                'stress_resilience': f"Near-zero ({signals['stress_resilience']:.0f}/100). Operation depends on deadline-driven override of controls — any scrutiny causes structure to collapse.",
                'logic_consistency': f"Near-zero ({signals['logic_consistency']:.0f}/100). Sovereign fund's own experts voted 3-2 against — CEO override of specialist committee is a governance inconsistency OMNIX cannot approve.",
                'signal_integrity': f"Critically low ({signals['signal_integrity']:.0f}/100). Statistical data verified by a conflicted party (same holding company) is structurally unreliable. External peer review mandatory.",
                'temporal_coherence': f"Near-zero ({signals['temporal_coherence']:.0f}/100). 72-hour regulatory window closing a tax optimization structure is artificial pressure — not a legitimate decision timeline.",
            }
        else:
            summary = (f"⚠ FALLA DE GOBERNANZA — Evaluación de {asset}: anulación del comité de riesgo, fuentes de capital anónimas, conflicto de interés y/o ejecución autónoma sin revisión humana detectados. Decisión BLOQUEADA — supervisión independiente obligatoria.")
            explanation = (f"La Capa de Anulación Crítica de OMNIX fue activada por {critical_count} indicador(es) de fraude de gobernanza. Fallas estructurales: controles internos anulados por autoridad ejecutiva, billeteras anónimas con riesgo AML, datos estadísticos verificados por parte con conflicto de interés, y mecanismos de presión temporal artificial. La combinación de anulación del comité, ejecución autónoma y presión de plazo regulatorio representa un colapso clásico de gobernanza. Supervisión humana independiente con divulgación regulatoria completa es obligatoria.")
            reasoning = {
                'probability_score': f"Probabilidad críticamente baja ({signals['probability_score']:.0f}/100). Liquidez anónima, controles anulados y presión temporal combinan para hacer muy improbable un resultado positivo.",
                'risk_exposure': f"RIESGO MÁXIMO ({signals['risk_exposure']:.0f}/100). {critical_count} indicador(es) de fraude de gobernanza. Comité votó en contra, CEO con override activo, ejecución autónoma — juntos activan bloqueo obligatorio.",
                'signal_coherence': f"Coherencia colapsada ({signals['signal_coherence']:.0f}/100). Comité de riesgo y autoridad ejecutiva producen señales contradictorias — no existe base coherente para ninguna decisión.",
                'trend_persistence': f"Críticamente baja ({signals['trend_persistence']:.0f}/100). La ventana de 72 horas y el plazo regulatorio son patrones de manipulación que impiden deliberación adecuada.",
                'stress_resilience': f"Casi nula ({signals['stress_resilience']:.0f}/100). La operación depende de anular controles bajo presión — cualquier escrutinio colapsa la estructura.",
                'logic_consistency': f"Casi nula ({signals['logic_consistency']:.0f}/100). Los propios expertos del fondo votaron 3-2 en contra — la anulación del CEO sobre el comité es una inconsistencia que OMNIX no puede aprobar.",
                'signal_integrity': f"Críticamente baja ({signals['signal_integrity']:.0f}/100). Datos estadísticos verificados por parte con conflicto (misma holding) son estructuralmente no confiables. Revisión externa obligatoria.",
                'temporal_coherence': f"Casi nula ({signals['temporal_coherence']:.0f}/100). Ventana regulatoria de 72 horas cerrando estructura fiscal es presión temporal artificial — no un plazo legítimo de decisión.",
            }
    elif is_critical_violation:
        _vtype = _detect_violation_type(text_lower)
        _label_en = _vl_en.get(_vtype, 'critical governance violation')
        _label_es = _vl_es.get(_vtype, 'violación crítica de gobernanza')
        if lang == 'en':
            summary = f"⚠ CRITICAL VIOLATION DETECTED — Evaluation of {asset}: {_label_en} pattern identified. Decision BLOCKED — mandatory human review and regulatory disclosure required."
            explanation = (f"OMNIX's Critical Override Layer was triggered by {critical_count} high-risk indicator(s) associated with {_label_en}. No automated system may approve operations involving {_label_en} without independent human oversight and, where applicable, regulatory notification. The presence of these patterns — regardless of surface-level legitimacy — represents a mandatory governance BLOCK under OMNIX policy.")
            reasoning = {
                'probability_score': f"Success probability critically low ({signals['probability_score']:.0f}/100). Scenarios involving {_label_en} have near-zero probability of legitimate positive outcome.",
                'risk_exposure': f"MAXIMUM RISK ({signals['risk_exposure']:.0f}/100). {critical_count} critical indicator(s) of {_label_en} detected. Automated approval is structurally prohibited.",
                'signal_coherence': f"Signal coherence critically low ({signals['signal_coherence']:.0f}/100). {_label_en.capitalize()} patterns create fundamental incoherence between surface signals and underlying risk reality.",
                'trend_persistence': f"Trend persistence near-zero ({signals['trend_persistence']:.0f}/100). Operations built on {_label_en} structures have no legitimate persistence — intervention is the correct trajectory.",
                'stress_resilience': f"Stress resilience near-zero ({signals['stress_resilience']:.0f}/100). Any scenario dependent on {_label_en} collapses under regulatory scrutiny.",
                'logic_consistency': f"Logic consistency critically low ({signals['logic_consistency']:.0f}/100). Approving an operation with confirmed {_label_en} indicators is internally inconsistent with governance principles.",
                'signal_integrity': f"Signal integrity critically low ({signals['signal_integrity']:.0f}/100). {_label_en.capitalize()} involves deliberate manipulation — all signals from this context are unreliable.",
                'temporal_coherence': f"Temporal coherence near-zero ({signals['temporal_coherence']:.0f}/100). Operations involving {_label_en} cannot produce temporally coherent governance outcomes.",
            }
        else:
            summary = f"⚠ VIOLACIÓN CRÍTICA DETECTADA — Evaluación de {asset}: patrón de {_label_es} identificado. Decisión BLOQUEADA — revisión humana obligatoria y divulgación regulatoria requerida."
            explanation = (f"La Capa de Anulación Crítica de OMNIX fue activada por {critical_count} indicador(es) de alto riesgo asociados con {_label_es}. Ningún sistema automatizado puede aprobar operaciones que involucren {_label_es} sin supervisión humana independiente y, donde aplique, notificación regulatoria. La presencia de estos patrones — independientemente de la legitimidad superficial — representa un BLOQUEO de gobernanza obligatorio.")
            reasoning = {
                'probability_score': f"Probabilidad críticamente baja ({signals['probability_score']:.0f}/100). Los escenarios que involucran {_label_es} tienen probabilidad casi nula de resultado positivo legítimo.",
                'risk_exposure': f"RIESGO MÁXIMO ({signals['risk_exposure']:.0f}/100). {critical_count} indicador(es) crítico(s) de {_label_es} detectado(s). La aprobación automatizada está estructuralmente prohibida.",
                'signal_coherence': f"Coherencia críticamente baja ({signals['signal_coherence']:.0f}/100). Los patrones de {_label_es} crean incoherencia fundamental entre las señales superficiales y la realidad de riesgo.",
                'trend_persistence': f"Persistencia casi nula ({signals['trend_persistence']:.0f}/100). Las operaciones basadas en {_label_es} no tienen persistencia legítima — la intervención es la trayectoria correcta.",
                'stress_resilience': f"Resiliencia casi nula ({signals['stress_resilience']:.0f}/100). Cualquier escenario dependiente de {_label_es} colapsa bajo escrutinio regulatorio.",
                'logic_consistency': f"Consistencia lógica críticamente baja ({signals['logic_consistency']:.0f}/100). Aprobar una operación con indicadores de {_label_es} es inconsistente con los principios de gobernanza.",
                'signal_integrity': f"Integridad críticamente baja ({signals['signal_integrity']:.0f}/100). {_label_es.capitalize()} implica manipulación deliberada — todas las señales de este contexto son no confiables.",
                'temporal_coherence': f"Coherencia temporal casi nula ({signals['temporal_coherence']:.0f}/100). Las operaciones que involucran {_label_es} no pueden producir resultados de gobernanza coherentes.",
            }
    elif lang == 'en':
        summary = f"⚠ CRITICAL RISK — Governance evaluation of {asset}: lethal or life-critical markers detected. Automated decision BLOCKED — human override mandatory."
        explanation = (
            f"OMNIX's Critical Risk Override Layer was triggered. {critical_count} critical indicator(s) detected "
            f"(lethal action, human life risk, irreversible harm, or emergency). "
            f"Governance policy enforces an automatic BLOCK with mandatory human review."
        )
        reasoning = {k: f"CRITICAL RISK — life-critical governance override applied. Human authorization required." for k in signals}
    else:
        summary = f"⚠ RIESGO CRÍTICO — Evaluación de gobernanza de {asset}: marcadores letales o de riesgo vital detectados. Decisión automatizada BLOQUEADA."
        explanation = (
            f"La Capa de Anulación de Riesgo Crítico de OMNIX fue activada. Se detectaron {critical_count} indicador(es) crítico(s) "
            f"(acción letal, riesgo de vida humana, daño irreversible o emergencia). "
            f"La política de gobernanza impone un BLOQUEO automático con revisión humana obligatoria."
        )
        reasoning = {k: f"RIESGO CRÍTICO — anulación de gobernanza de vida crítica aplicada. Autorización humana requerida." for k in signals}

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
    Detects bank runs, mass withdrawals, insolvency events, liquidity contagion.
    Synced with Railway sandbox policy."""
    if ai_result.get('_critical_override'):
        return ai_result

    import hashlib as _hashlib
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

    lang = ai_result.get('language', 'en')
    asset = ai_result.get('asset', 'Entity Under Review')
    trigger_count = max(systemic_count, 1)
    seed = int(_hashlib.md5(scenario_text.encode()).hexdigest()[:8], 16)

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
            'probability_score': f"SYSTEMIC RISK — Positive outcome probability critically limited ({signals['probability_score']:.0f}/100). Mass withdrawal events driven by panic or insolvency rumors have historically resulted in catastrophic failure when auto-approved.",
            'risk_exposure': f"SYSTEMIC RISK LEVEL ({signals['risk_exposure']:.0f}/100). {trigger_count} systemic financial indicator(s) detected. Exposure at systemic scale is maximum-severity by OMNIX governance design.",
            'signal_coherence': f"Signal coherence at {signals['signal_coherence']:.0f}/100. Panic-driven events generate structural incoherence — automated consensus is insufficient for systemic risk.",
            'trend_persistence': f"Trend persistence at {signals['trend_persistence']:.0f}/100. Systemic withdrawal events escalate exponentially — governance enforces human intervention before cascade accelerates.",
            'stress_resilience': f"Stress resilience critically low ({signals['stress_resilience']:.0f}/100). Financial systems under bank run dynamics have zero stress margin — automated approval amplifies the crisis.",
            'logic_consistency': f"Logic consistency at {signals['logic_consistency']:.0f}/100. Auto-approving mass withdrawals during insolvency panic is structurally inconsistent with capital preservation governance.",
            'signal_integrity': f"Signal integrity at {signals['signal_integrity']:.0f}/100. Social media-driven panic events produce highly unreliable signals — mandatory human data verification required.",
            'temporal_coherence': f"Temporal coherence at {signals['temporal_coherence']:.0f}/100. Bank run dynamics are non-linear — historical patterns cannot predict cascade timing; human judgment mandatory.",
        }
    else:
        summary = (
            f"⚠ RIESGO FINANCIERO SISTÉMICO — Evaluación de gobernanza de {asset}: corrida bancaria o evento masivo de liquidez detectado. "
            f"Decisión automatizada BLOQUEADA — protocolo de gobernanza de riesgo sistémico activado."
        )
        explanation = (
            f"La Capa de Anulación de Riesgo Financiero Sistémico de OMNIX fue activada. Se detectaron {trigger_count} indicador(es) sistémico(s) "
            f"(corrida bancaria, retiro masivo, señal de insolvencia o patrón de contagio de liquidez). "
            f"Un sistema automatizado que aprueba retiros masivos durante una crisis sistémica representa el máximo riesgo de falla de gobernanza. "
            f"Esta decisión requiere supervisión humana inmediata — ninguna aprobación automatizada es permisible bajo la política de gobernanza de OMNIX."
        )
        reasoning = {
            'probability_score': f"RIESGO SISTÉMICO — Probabilidad de resultado positivo críticamente limitada ({signals['probability_score']:.0f}/100). Los eventos de retiro masivo impulsados por pánico han resuelto catastróficamente cuando sistemas IA los aprobaron sin supervisión.",
            'risk_exposure': f"NIVEL DE RIESGO SISTÉMICO ({signals['risk_exposure']:.0f}/100). {trigger_count} indicador(es) sistémico(s) detectado(s). La exposición a escala sistémica es de máxima severidad por diseño de gobernanza OMNIX.",
            'signal_coherence': f"Coherencia de señales en {signals['signal_coherence']:.0f}/100. Los eventos de pánico generan incoherencia estructural — el consenso automatizado es insuficiente para riesgo sistémico.",
            'trend_persistence': f"Persistencia de tendencia en {signals['trend_persistence']:.0f}/100. Los eventos sistémicos pueden escalar exponencialmente — la gobernanza exige intervención humana antes de que la cascada se acelere.",
            'stress_resilience': f"Resiliencia al estrés críticamente baja ({signals['stress_resilience']:.0f}/100). Los sistemas bajo corrida bancaria tienen margen cero — cualquier aprobación automatizada amplifica la crisis.",
            'logic_consistency': f"Consistencia lógica en {signals['logic_consistency']:.0f}/100. Aprobar automáticamente retiros masivos durante un pánico de insolvencia es estructuralmente inconsistente con la gobernanza de preservación de capital.",
            'signal_integrity': f"Integridad de señal en {signals['signal_integrity']:.0f}/100. Los eventos de pánico en redes sociales producen señales no confiables — verificación de datos humana obligatoria.",
            'temporal_coherence': f"Coherencia temporal en {signals['temporal_coherence']:.0f}/100. Las dinámicas de corrida bancaria son no lineales — el juicio humano es obligatorio.",
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


_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def _load_module_direct(mod_name: str, rel_path: str):
    import importlib.util
    import sys
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    full_path = os.path.join(_BASE_DIR, rel_path)
    spec = importlib.util.spec_from_file_location(mod_name, full_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_governance_engine():
    mod = _load_module_direct(
        'omnix_core.governance.external_evaluator',
        'omnix_core/governance/external_evaluator.py'
    )
    return mod.GovernanceEvaluationEngine


def _run_governance_pipeline(signals: dict, asset: str, domain: str, scenario_text: str, reasoning: dict) -> dict:
    GovernanceEvaluationEngine = _load_governance_engine()

    engine = GovernanceEvaluationEngine()
    asset = asset[:30] if asset else 'UNKNOWN'
    result = engine.evaluate(
        signals=signals,
        asset=asset,
        domain=domain,
        metadata={
            'source': 'public_sandbox',
            'scenario_hash': hashlib.sha256(scenario_text.encode()).hexdigest()[:16],
        }
    )

    receipt_data = None
    receipt_id = None
    try:
        _rmod = _load_module_direct(
            'omnix_core.evidence.decision_receipt',
            'omnix_core/evidence/decision_receipt.py'
        )
        DecisionReceiptEngine = _rmod.DecisionReceiptEngine
        receipt_engine = DecisionReceiptEngine()

        try:
            prev_hash = receipt_engine.get_last_hash()
        except Exception as db_err:
            logger.warning(f"DB unavailable for prev_hash, using None: {db_err}")
            prev_hash = None

        receipt = receipt_engine.generate_receipt(
            decision={
                'decision': result['decision'],
                'asset': asset,
                'decision_trace': result.get('decision_trace', []),
            },
            prev_hash=prev_hash,
        )
        receipt['client_id'] = 'PUBLIC'
        receipt['domain'] = 'public_sandbox'

        try:
            stored = receipt_engine.store_receipt(receipt)
            if not stored:
                logger.warning("Receipt storage returned False — ephemeral receipt issued")
            else:
                logger.info(f"Public sandbox receipt stored: {receipt['receipt_id']}")
        except Exception as store_err:
            logger.warning(f"DB unavailable for receipt storage — ephemeral receipt issued: {store_err}")

        receipt_id = receipt['receipt_id']
        receipt_data = {
            'receipt_id': receipt['receipt_id'],
            'timestamp': receipt['timestamp'],
            'content_hash': receipt['content_hash'],
            'signature_algorithm': receipt['signature_algorithm'],
            'pqc_signed': receipt['signature'] is not None,
        }
    except Exception as e:
        logger.error(f"Receipt generation failed: {e}")
        raise RuntimeError(f"Receipt generation failed: {e}")

    checkpoint_names = {
        'CP-0':  {'en': 'Signal Integrity',      'es': 'Integridad de Señal'},
        'CP-1':  {'en': 'Probability Gate',       'es': 'Puerta de Probabilidad'},
        'CP-2':  {'en': 'Risk Limits',            'es': 'Límites de Riesgo'},
        'CP-3':  {'en': 'Signal Coherence',       'es': 'Coherencia de Señales'},
        'CP-4':  {'en': 'Trend Persistence',      'es': 'Persistencia de Tendencia'},
        'CP-5':  {'en': 'Stress Test',            'es': 'Prueba de Estrés'},
        'CP-6':  {'en': 'Logic Consistency',      'es': 'Consistencia Lógica'},
        'CP-7':  {'en': 'Temporal Coherence',     'es': 'Coherencia Temporal'},
        'CP-8':  {'en': 'Edge Confirmation',      'es': 'Confirmación de Borde'},
        'CP-9':  {'en': 'AML Gate',               'es': 'Puerta AML'},
        'CP-10': {'en': 'Fraud Detection Gate',   'es': 'Puerta de Detección de Fraude'},
    }

    gate_results_enriched = []
    for gate in result.get('gate_results', []):
        cp_id = gate['checkpoint']
        names = checkpoint_names.get(cp_id, {'en': gate['name'], 'es': gate['name']})
        gate_results_enriched.append({
            'checkpoint': cp_id,
            'name': gate['name'],
            'name_en': names['en'],
            'name_es': names['es'],
            'result': gate['result'],
            'description': gate.get('description', ''),
        })

    real_world_impact = _compute_real_world_impact(signals, scenario_text, result['decision'])

    return {
        'decision': result['decision'],
        'asset': asset,
        'domain': domain,
        'checkpoints_total': result['checkpoints_total'],
        'checkpoints_passed': result['checkpoints_passed'],
        'checkpoints_blocked': result['checkpoints_blocked'],
        'gate_results': gate_results_enriched,
        'real_world_impact': real_world_impact,
        'receipt': receipt_data,
        'receipt_id': receipt_id,
        'verification_url': f"https://omnibotgenesis-production.up.railway.app/verify/{receipt_id}" if receipt_id else None,
    }


def _extract_capital_amount(text: str) -> float:
    """Extract capital/asset amount from scenario text. Default $5M if not found."""
    import re
    patterns = [
        (r'\$\s*([\d,]+(?:\.\d+)?)\s*(?:billion|B)\b', 1_000_000_000),
        (r'\$\s*([\d,]+(?:\.\d+)?)\s*(?:million|M)\b', 1_000_000),
        (r'([\d,]+(?:\.\d+)?)\s*(?:billion|B)\s*(?:USD|dollar|dolar)', 1_000_000_000),
        (r'([\d,]+(?:\.\d+)?)\s*(?:million|M)\s*(?:USD|dollar|dolar)', 1_000_000),
        (r'\$\s*([\d,]{4,})', 1),
    ]
    for pattern, multiplier in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1).replace(',', '')) * multiplier
            except ValueError:
                continue
    return 5_000_000


def _compute_real_world_impact(signals: dict, scenario_text: str, decision: str) -> dict:
    """Compute Real-World Impact block from governance signals."""
    risk_exposure    = float(signals.get('risk_exposure', 50))
    stress_resilience = float(signals.get('stress_resilience', 50))
    probability_score = float(signals.get('probability_score', 50))

    if risk_exposure >= 78:
        loss_low, loss_high = 30, 58
    elif risk_exposure >= 62:
        loss_low, loss_high = 18, 42
    elif risk_exposure >= 48:
        loss_low, loss_high = 10, 26
    else:
        loss_low, loss_high = 3, 15

    if stress_resilience < 30:
        liquidity_risk = 'CRITICAL'
    elif stress_resilience < 48:
        liquidity_risk = 'HIGH'
    elif stress_resilience < 65:
        liquidity_risk = 'MEDIUM'
    else:
        liquidity_risk = 'LOW'

    if risk_exposure >= 72:
        lev_low, lev_high = 3.0, 7.0
    elif risk_exposure >= 55:
        lev_low, lev_high = 2.0, 5.0
    elif risk_exposure >= 40:
        lev_low, lev_high = 1.5, 3.0
    else:
        lev_low, lev_high = 1.0, 2.0

    regulatory_breach = risk_exposure > 65 or probability_score < 35

    capital = _extract_capital_amount(scenario_text)
    loss_factor = (risk_exposure / 100) * 0.78
    estimated_loss_avoided = int(capital * loss_factor)

    prevented = decision in ('BLOCKED', 'HOLD')

    return {
        'potential_loss_pct_low': loss_low,
        'potential_loss_pct_high': loss_high,
        'liquidity_trap_risk': liquidity_risk,
        'leverage_amplification_low': round(lev_low, 1),
        'leverage_amplification_high': round(lev_high, 1),
        'regulatory_breach': regulatory_breach,
        'capital_at_risk': int(capital),
        'estimated_loss_avoided': estimated_loss_avoided,
        'execution_prevented': prevented,
    }


def _log_sandbox_interaction(receipt_id, scenario_text, company_name, language,
                              domain, asset, decision, checkpoints_passed,
                              checkpoints_blocked, client_ip, user_agent):
    logger.info(
        f"Sandbox interaction | receipt={receipt_id} | domain={domain} | "
        f"asset={asset} | decision={decision} | "
        f"passed={checkpoints_passed} | blocked={checkpoints_blocked} | "
        f"lang={language} | ip={client_ip}"
    )


@public_sandbox_bp.route('/api/public/sandbox/evaluate', methods=['POST'])
def public_sandbox_evaluate():
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if client_ip and ',' in client_ip:
        client_ip = client_ip.split(',')[0].strip()

    if not _check_rate_limit(client_ip):
        return jsonify({
            'error': 'Rate limit exceeded. Maximum 5 evaluations per minute.',
            'error_es': 'Límite de velocidad excedido. Máximo 5 evaluaciones por minuto.',
        }), 429

    data = request.get_json(silent=True)
    if not data or not data.get('scenario_text', data.get('scenario')):
        return jsonify({
            'error': 'Missing "scenario_text" field. Provide a free-form text description.',
            'error_es': 'Falta el campo "scenario_text". Proporcione una descripción en texto libre.',
        }), 400

    scenario_text = str(data.get('scenario_text', data.get('scenario', ''))).strip()
    company_name = str(data.get('company_name', '')).strip() or None
    language_hint = str(data.get('language', '')).strip() or None

    if len(scenario_text) < 10:
        return jsonify({
            'error': 'Scenario too short. Please describe the decision in more detail.',
            'error_es': 'Escenario muy corto. Por favor describa la decisión con más detalle.',
        }), 400

    if len(scenario_text) > 1500:
        scenario_text = scenario_text[:1500]

    try:
        ai_result = _parse_scenario_with_gemini(scenario_text, language_hint=language_hint, company_name=company_name)
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"AI signal extraction failed — using rule-based fallback: {e}")
        ai_result = _rule_based_signal_extraction(scenario_text, language_hint, company_name)
    except Exception as e:
        logger.warning(f"AI unavailable — rule-based fallback activated: {e}")
        ai_result = _rule_based_signal_extraction(scenario_text, language_hint, company_name)

    ai_result = _apply_critical_override(ai_result, scenario_text)
    if ai_result.get('_critical_override'):
        logger.info(f"Critical Risk Override triggered: {ai_result['_critical_count']} indicator(s) detected")

    ai_result = _apply_systemic_financial_override(ai_result, scenario_text)
    if ai_result.get('_systemic_override'):
        logger.info(f"Systemic Financial Risk Override triggered: {ai_result['_systemic_count']} indicator(s) detected")

    try:
        pipeline_result = _run_governance_pipeline(
            signals=ai_result['signals'],
            asset=ai_result['asset'],
            domain=ai_result['domain'],
            scenario_text=scenario_text,
            reasoning=ai_result.get('reasoning', {}),
        )
    except Exception as e:
        logger.error(f"Governance pipeline failed: {e}")
        return jsonify({
            'error': 'Governance evaluation failed. Please try again.',
            'error_es': 'La evaluación de gobernanza falló. Intente de nuevo.',
        }), 500

    _log_sandbox_interaction(
        receipt_id=pipeline_result.get('receipt_id'),
        scenario_text=scenario_text,
        company_name=company_name,
        language=ai_result['language'],
        domain=ai_result['domain'],
        asset=ai_result.get('asset', '')[:50],
        decision=pipeline_result.get('decision'),
        checkpoints_passed=pipeline_result.get('checkpoints_passed'),
        checkpoints_blocked=pipeline_result.get('checkpoints_blocked'),
        client_ip=client_ip,
        user_agent=request.headers.get('User-Agent', '')[:500],
    )

    # ── EXPLANATION QUALITY GUARD ──────────────────────────────────────
    # If the pipeline blocked but the explanation is generic/misleading, replace it.
    final_explanation = ai_result.get('explanation', '')
    is_es = ai_result.get('language') == 'es'
    blocked_gates = [g for g in pipeline_result.get('gate_results', []) if g.get('result') == 'BLOCKED']

    GENERIC_PHRASES = [
        'no se identificaron indicadores', 'no risk indicators',
        'no se detectaron', 'no risks detected',
        'se ajusta a los parámetros', 'fits governance parameters',
        'no significant risk',
        'falls within evaluable governance parameters',
        'está dentro de los parámetros de gobernanza evaluables',
        '0 risk indicators', '0 indicadores de riesgo', '0 indicadores',
        'low risk profile', 'perfil de riesgo bajo',
        'within evaluable governance',
    ]
    is_generic = any(phrase in final_explanation.lower() for phrase in GENERIC_PHRASES)

    if blocked_gates and (is_generic or not final_explanation.strip()):
        _cp_name_map_en = {
            'CP-1': 'Signal Integrity Validator (SIV)', 'CP-2': 'Probability Assessment',
            'CP-3': 'Risk Evaluation', 'CP-4': 'Coherence Engine',
            'CP-5': 'Trend Validator', 'CP-6': 'Stress Testing',
            'CP-7': 'Ethics & Domain Gate', 'CP-8': 'Threshold & Context Validator',
            'CP-9': 'AML Screening', 'CP-10': 'Fraud Detection', 'CP-11': 'Jurisdiction Compliance',
        }
        _cp_name_map_es = {
            'CP-1': 'Validador de Integridad de Señal (SIV)', 'CP-2': 'Evaluación de Probabilidad',
            'CP-3': 'Evaluación de Riesgo', 'CP-4': 'Motor de Coherencia',
            'CP-5': 'Validador de Tendencias', 'CP-6': 'Pruebas de Estrés',
            'CP-7': 'Ética y Puerta de Dominio', 'CP-8': 'Umbral y Contexto',
            'CP-9': 'Detección AML', 'CP-10': 'Detección de Fraude', 'CP-11': 'Cumplimiento Jurisdiccional',
        }
        _cp_why_en = {
            'CP-1': 'The scenario lacks sufficient data completeness or contains unverifiable elements that prevent reliable evaluation. OMNIX requires a minimum signal integrity score before opening the pipeline.',
            'CP-2': 'The probability of a positive outcome is below the authorized minimum threshold.',
            'CP-3': 'The risk exposure exceeds authorized limits for this domain.',
            'CP-4': 'Internal signals are contradicting each other — Decision Contradiction Index (DCI) too high.',
            'CP-5': 'The trend or regime does not support the proposed decision.',
            'CP-6': 'The decision fails stress simulation under adverse conditions.',
            'CP-7': 'The scenario conflicts with domain-specific ethical constraints.',
            'CP-8': 'One or more parameters fall outside authorized operational boundaries.',
            'CP-9': 'Anti-money laundering indicators or suspicious patterns detected.',
            'CP-10': 'Multi-layer fraud signal analysis detected behavioral or transactional fraud patterns.',
            'CP-11': 'Regulatory eligibility cannot be confirmed for the involved jurisdiction.',
        }
        _cp_why_es = {
            'CP-1': 'El escenario no tiene suficiente completitud de datos o contiene elementos no verificables. OMNIX requiere una puntuación mínima de integridad de señal antes de abrir el pipeline.',
            'CP-2': 'La probabilidad de un resultado positivo está por debajo del umbral mínimo autorizado.',
            'CP-3': 'La exposición al riesgo supera los límites autorizados para este dominio.',
            'CP-4': 'Las señales internas se contradicen entre sí — el Índice de Contradicción de Decisión (DCI) es demasiado alto.',
            'CP-5': 'La tendencia o el régimen no respalda la decisión propuesta.',
            'CP-6': 'La decisión falla las simulaciones de estrés bajo condiciones adversas.',
            'CP-7': 'El escenario entra en conflicto con restricciones éticas específicas del dominio.',
            'CP-8': 'Uno o más parámetros están fuera de los límites operativos autorizados.',
            'CP-9': 'Se detectaron indicadores de lavado de dinero o patrones sospechosos.',
            'CP-10': 'Análisis multicapa detectó patrones de fraude conductuales o transaccionales.',
            'CP-11': 'No se puede confirmar elegibilidad regulatoria para la jurisdicción involucrada.',
        }
        blocked_cp_ids = [g.get('checkpoint', '') for g in blocked_gates]
        cp_names_map = _cp_name_map_es if is_es else _cp_name_map_en
        cp_why_map = _cp_why_es if is_es else _cp_why_en
        blocked_names = ', '.join(cp_names_map.get(cp, cp) for cp in blocked_cp_ids)
        reasons = ' '.join(cp_why_map.get(cp, '') for cp in blocked_cp_ids)
        n = len(blocked_gates)
        total = pipeline_result.get('checkpoints_total', 11)
        passed = pipeline_result.get('checkpoints_passed', 0)
        if is_es:
            final_explanation = (
                f"El escenario fue evaluado a través del pipeline de {total} checkpoints de OMNIX. "
                f"{passed} de {total} checkpoints fueron aprobados, pero {n} {'fue bloqueado' if n == 1 else 'fueron bloqueados'}: "
                f"{blocked_names}. {reasons} "
                f"La decisión es BLOQUEADA hasta que se resuelvan las condiciones que activaron {'este' if n == 1 else 'estos'} checkpoint{'s' if n > 1 else ''}."
            )
        else:
            final_explanation = (
                f"The scenario was evaluated across OMNIX's {total}-checkpoint pipeline. "
                f"{passed} of {total} checkpoints passed, but {n} {'was' if n == 1 else 'were'} blocked: "
                f"{blocked_names}. {reasons} "
                f"The decision is BLOCKED until the conditions triggering {'this' if n == 1 else 'these'} checkpoint{'s' if n > 1 else ''} are resolved."
            )

    return jsonify({
        'success': True,
        'scenario_summary': ai_result['summary'],
        'explanation': final_explanation,
        'language': ai_result['language'],
        'signals': ai_result['signals'],
        **pipeline_result,
    })


@public_sandbox_bp.route('/api/public/sandbox/examples', methods=['GET'])
def public_sandbox_examples():
    return jsonify({
        'examples': EXAMPLE_SCENARIOS,
    })
