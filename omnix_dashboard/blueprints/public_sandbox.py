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


def _parse_scenario_with_gemini(scenario_text: str, language_hint: str | None = None, company_name: str | None = None) -> dict:
    api_key = os.environ.get('GOOGLE_AI_API_KEY')
    if not api_key:
        raise RuntimeError("AI service not configured")

    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

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

    response = model.generate_content(prompt)
    raw_text = response.text.strip()
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
        prev_hash = receipt_engine.get_last_hash()
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
        stored = receipt_engine.store_receipt(receipt)
        if not stored:
            raise RuntimeError("Receipt storage returned False")
        receipt_id = receipt['receipt_id']
        receipt_data = {
            'receipt_id': receipt['receipt_id'],
            'timestamp': receipt['timestamp'],
            'content_hash': receipt['content_hash'],
            'signature_algorithm': receipt['signature_algorithm'],
            'pqc_signed': receipt['signature'] is not None,
        }
        logger.info(f"Public sandbox receipt stored: {receipt_id}")
    except Exception as e:
        logger.error(f"Receipt generation/storage failed (fail-closed): {e}")
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

    return {
        'decision': result['decision'],
        'asset': asset,
        'domain': domain,
        'checkpoints_total': result['checkpoints_total'],
        'checkpoints_passed': result['checkpoints_passed'],
        'checkpoints_blocked': result['checkpoints_blocked'],
        'gate_results': gate_results_enriched,
        'receipt': receipt_data,
        'receipt_id': receipt_id,
        'verification_url': f"https://omnibotgenesis-production.up.railway.app/verify/{receipt_id}" if receipt_id else None,
    }


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
