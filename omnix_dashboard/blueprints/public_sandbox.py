"""
Public Governance Sandbox — "Try OMNIX"
No authentication required. Rate limited. Real 8-checkpoint pipeline.
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
    import google.generativeai as genai
    from google.api_core import exceptions as gapi_exc
    api_key = os.environ.get('GOOGLE_AI_API_KEY') or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise RuntimeError("No Gemini API key configured (GOOGLE_AI_API_KEY or GEMINI_API_KEY)")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(
        prompt,
        request_options={'timeout': 90},
    )
    return response.text.strip()


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
    ]
    extreme_risk_terms = [
        'fraud', 'fraude', 'ponzi', 'scam', 'collapse', 'colapso',
        '25:1', '50:1', '30:1', 'extreme', 'extremo', 'systemic',
        'sistémico', 'billion', '500m', '$500', 'trillion',
    ]
    positive_terms = [
        'audit', 'auditado', 'compliant', 'cumplimiento', 'regulated', 'regulado',
        'conservative', 'conservador', 'track record', 'trayectoria', 'profitable',
        'rentable', 'stable', 'estable', 'transparent', 'transparente',
        'collateral', 'garantía', 'low risk', 'bajo riesgo', 'diversified',
        'diversificado', 'insured', 'asegurado', 'established', 'establecido',
    ]

    risk_count = sum(1 for t in high_risk_terms if t in text_lower)
    extreme_count = sum(1 for t in extreme_risk_terms if t in text_lower)
    positive_count = sum(1 for t in positive_terms if t in text_lower)

    base = 58
    risk_penalty = min(45, risk_count * 7 + extreme_count * 12)
    positive_boost = min(25, positive_count * 6)
    adjusted = max(8, min(88, base - risk_penalty + positive_boost))

    seed = int(hashlib.md5(scenario_text.encode()).hexdigest()[:8], 16)
    def jitter(offset=0, lo=-4, hi=4):
        pseudo = (seed >> (offset % 16)) & 0xFF
        spread = pseudo % (hi - lo + 1) + lo
        return max(5, min(95, adjusted + offset + spread))

    if any(t in text_lower for t in ['fund', 'fondo', 'hedge', 'trading', 'investment', 'inversión']):
        domain = 'hedge_fund'
    elif any(t in text_lower for t in ['loan', 'préstamo', 'bank', 'banco', 'credit', 'crédito', 'lend']):
        domain = 'lending'
    elif any(t in text_lower for t in ['crypto', 'bitcoin', 'ethereum', 'token', 'defi', 'blockchain']):
        domain = 'crypto'
    elif any(t in text_lower for t in ['company', 'empresa', 'acquisition', 'adquisición', 'merger', 'startup']):
        domain = 'corporate'
    else:
        domain = 'financial'

    asset_name = company_name or 'Entity Under Review'

    lang = language_hint or 'es'
    if lang == 'en':
        summary = (
            f"Rule-based risk evaluation of {len(scenario_text.split())} scenario tokens. "
            f"Risk indicators: {risk_count} detected ({extreme_count} extreme). "
            f"Positive factors: {positive_count}. "
            f"Net risk adjustment: {risk_penalty - positive_boost:+d} points from neutral."
        )
        expl = "Derived from keyword-based risk analysis (AI temporarily unavailable)."
    else:
        summary = (
            f"Evaluación de riesgo basada en {len(scenario_text.split())} indicadores del escenario. "
            f"Indicadores de riesgo: {risk_count} detectados ({extreme_count} extremos). "
            f"Factores positivos: {positive_count}. "
            f"Ajuste de riesgo neto: {risk_penalty - positive_boost:+d} puntos desde neutro."
        )
        expl = "Derivado de análisis de palabras clave de riesgo (IA temporalmente no disponible)."

    signals = {
        'probability_score':  jitter(-5 if risk_count > 2 else 5),
        'risk_exposure':      max(10, min(95, 100 - adjusted + ((seed & 0xF) % 9) - 4)),
        'signal_coherence':   jitter(0),
        'trend_persistence':  jitter(5),
        'stress_resilience':  jitter(-10 if extreme_count > 0 else 0),
        'logic_consistency':  jitter(8),
        'signal_integrity':   jitter(-6 if 'unknown' in text_lower or 'desconocido' in text_lower else 4),
        'temporal_coherence': jitter(0, lo=-6, hi=6),
    }
    signal_explanations = {k: expl for k in signals}

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
        'CP-0': {'en': 'Signal Integrity', 'es': 'Integridad de Señal'},
        'CP-1': {'en': 'Probability Gate', 'es': 'Puerta de Probabilidad'},
        'CP-2': {'en': 'Risk Limits', 'es': 'Límites de Riesgo'},
        'CP-3': {'en': 'Signal Coherence', 'es': 'Coherencia de Señales'},
        'CP-4': {'en': 'Trend Persistence', 'es': 'Persistencia de Tendencia'},
        'CP-5': {'en': 'Stress Test', 'es': 'Prueba de Estrés'},
        'CP-6': {'en': 'Logic Consistency', 'es': 'Consistencia Lógica'},
        'CP-7': {'en': 'Temporal Coherence', 'es': 'Coherencia Temporal'},
    }

    gate_results_enriched = []
    for gate in result.get('gate_results', []):
        cp_id = gate['checkpoint']
        names = checkpoint_names.get(cp_id, {'en': gate['name'], 'es': gate['name']})
        signal_key = gate.get('signal', '')
        gate_results_enriched.append({
            'checkpoint': cp_id,
            'name': gate['name'],
            'name_en': names['en'],
            'name_es': names['es'],
            'score': gate['score'],
            'threshold': gate['threshold'],
            'result': gate['result'],
            'description': gate.get('description', ''),
            'reasoning': reasoning.get(signal_key, ''),
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

    if len(scenario_text) > 500:
        scenario_text = scenario_text[:500]

    try:
        ai_result = _parse_scenario_with_gemini(scenario_text, language_hint=language_hint, company_name=company_name)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"AI signal extraction failed: {e}")
        return jsonify({
            'error': 'AI failed to extract governance signals. Please try rephrasing your scenario.',
            'error_es': 'La IA no pudo extraer las señales de gobernanza. Intente reformular su escenario.',
        }), 500
    except Exception as e:
        logger.error(f"Gemini parsing failed: {e}")
        return jsonify({
            'error': 'AI service temporarily unavailable. Please try again.',
            'error_es': 'Servicio de IA temporalmente no disponible. Intente de nuevo.',
        }), 503

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

    return jsonify({
        'success': True,
        'scenario_summary': ai_result['summary'],
        'explanation': ai_result.get('explanation', ''),
        'language': ai_result['language'],
        'signals': ai_result['signals'],
        **pipeline_result,
    })


@public_sandbox_bp.route('/api/public/sandbox/examples', methods=['GET'])
def public_sandbox_examples():
    return jsonify({
        'examples': EXAMPLE_SCENARIOS,
    })
