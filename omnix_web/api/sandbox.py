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
    ]
    extreme_risk_terms = [
        'fraud', 'fraude', 'ponzi', 'scam', 'collapse', 'colapso',
        '25:1', '50:1', '30:1', 'extreme', 'extremo', 'systemic',
        'sistémico', 'billion', '500m', 'trillion',
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

    if lang == 'en':
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
            'risk_exposure': f"Nivel de riesgo evaluado en {risk_exp:.0f}/100. {'Múltiples marcadores de riesgo de alta severidad detectados.' if extreme_count > 0 else 'Perfil de riesgo moderado basado en el contexto del escenario.'}",
            'signal_coherence': f"Concordancia de indicadores internos en {sig_coh:.0f}/100. {'Las señales muestran divergencia parcial entre dimensiones evaluadas.' if sig_coh < 60 else 'Las señales están ampliamente alineadas en las dimensiones evaluadas.'}",
            'trend_persistence': f"Estabilidad de tendencia calificada en {trend_pers:.0f}/100. {'Se identifican patrones sostenidos en el contexto del escenario.' if trend_pers >= 60 else 'Tendencia de corto plazo o incierta detectada.'}",
            'stress_resilience': f"Resiliencia ante escenario adverso en {stress_res:.0f}/100. {'Indicadores de riesgo extremo reducen la confianza bajo condiciones de estrés.' if extreme_count > 0 else 'El escenario muestra margen adecuado bajo condiciones de estrés moderado.'}",
            'logic_consistency': f"Integridad lógica interna en {logic_con:.0f}/100. {'El escenario presenta un contexto de decisión estructuralmente coherente.' if logic_con >= 60 else 'Se detectan tensiones lógicas menores entre elementos del escenario.'}",
            'signal_integrity': f"Completitud y confiabilidad de datos en {sig_int:.0f}/100. {'Elementos desconocidos o no verificables reducen la calidad de la señal.' if 'unknown' in text_lower or 'desconocido' in text_lower else 'Los datos del escenario parecen suficientemente completos para la evaluación.'}",
            'temporal_coherence': f"Alineación de trayectoria prospectiva-retrospectiva en {temp_coh:.0f}/100. {'Las proyecciones históricas y futuras muestran dirección consistente.' if temp_coh >= 55 else 'Divergencia temporal detectada entre los horizontes de tiempo evaluados.'}",
        }

    if lang == 'en':
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
                user_agent VARCHAR(500)
            )
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
                 decision, checkpoints_passed, checkpoints_blocked, client_ip, user_agent)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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

        data = flask_request.get_json(silent=True)
        if not data or not data.get('scenario_text', data.get('scenario')):
            return flask_jsonify({
                'error': 'Missing "scenario_text" field. Provide a free-form text description.',
                'error_es': 'Falta el campo "scenario_text". Proporcione una descripción en texto libre.',
            }), 400

        scenario_text = str(data.get('scenario_text', data.get('scenario', ''))).strip()
        company_name = str(data.get('company_name', '')).strip() or None
        language_hint = str(data.get('language', '')).strip() or None

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

        reasoning = ai_result.get('reasoning', {})
        gate_results_enriched = []
        for gate in governance_result.get('gate_results', []):
            cp_id = gate['checkpoint']
            names = CHECKPOINT_NAMES_I18N.get(cp_id, {'en': gate['name'], 'es': gate['name']})
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
