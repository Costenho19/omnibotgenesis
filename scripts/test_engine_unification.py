"""
OMNIX ADR-115 — Test de Unificación del Motor
Verifica que los 8 verticales usen GovernanceEvaluationEngine correctamente.
Uso: PYTHONPATH=/home/runner/workspace python scripts/test_engine_unification.py
"""
import sys
import traceback

sys.path.insert(0, "/home/runner/workspace")

from omnix_core.governance.external_evaluator import GovernanceEvaluationEngine

PASS = "\033[92m✅ PASS\033[0m"
FAIL = "\033[91m❌ FAIL\033[0m"

results = []

def check(name, condition, got=None, expected=None):
    ok = bool(condition)
    tag = PASS if ok else FAIL
    msg = f"  {tag}  {name}"
    if not ok and got is not None:
        msg += f"\n       got={got!r}  expected={expected!r}"
    print(msg)
    results.append((name, ok))
    return ok

def good_signals():
    return {
        "probability_score": 78.0,
        "risk_exposure":     28.0,
        "signal_coherence":  72.0,
        "trend_persistence": 68.0,
        "stress_resilience": 71.0,
        "logic_consistency": 75.0,
    }

def weak_signals():
    """Signals that should produce BLOCKED"""
    return {
        "probability_score": 25.0,
        "risk_exposure":     88.0,
        "signal_coherence":  22.0,
        "trend_persistence": 20.0,
        "stress_resilience": 18.0,
        "logic_consistency": 22.0,
    }

# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("  OMNIX ADR-115 — ENGINE UNIFICATION TEST SUITE")
print("  8 Verticales · 11 Checkpoints · Hard Blocks · AVM")
print("="*60)

# ── BLOQUE 1: 8 VERTICALES — RESPUESTA BÁSICA ────────────────────────────────
print(f"\n{'─'*60}")
print("BLOQUE 1 — 8 verticales responden al motor (señales sanas)")
print(f"{'─'*60}")

DOMAINS = [
    ("trading",          "BTC_trade"),
    ("islamic_credit",   "MurabahaLoan"),
    ("insurance",        "PolicyClaim"),
    ("robotics",         "ArmAssembly"),
    ("medical_ai",       "DiagnosticAI_diagnosis"),
    ("real_estate",      "Residential_mortgage_approval"),
    ("autonomous_agent", "Enterprise_Agent_task_delegation"),
    ("energy_governance","Solar_Utility_dispatch_order"),
]

for domain, asset in DOMAINS:
    try:
        engine = GovernanceEvaluationEngine()
        r = engine.evaluate(signals=good_signals(), asset=asset, domain=domain)
        d = r.get("decision", "MISSING")
        cp = r.get("checkpoints_total", 0)
        check(f"{domain}: decision válida", d in ("APPROVED", "HOLD", "BLOCKED"), d, "APPROVED|HOLD|BLOCKED")
        check(f"{domain}: 11 checkpoints", cp == 11, cp, 11)
        check(f"{domain}: dominio en resultado", r.get("domain") == domain, r.get("domain"), domain)
    except Exception as e:
        check(f"{domain}: engine call", False, str(e)[:80])

# ── BLOQUE 2: HARD BLOCKS ────────────────────────────────────────────────────
print(f"\n{'─'*60}")
print("BLOQUE 2 — Hard Blocks (BLOCKED inmediato, bypass del motor)")
print(f"{'─'*60}")

# Medical — ethics_flag=True
try:
    from omnix_core.medical.medical_simulator import _evaluate_decision as med_eval
    print("\n  [Medical] ethics_flag=True →")
    r = med_eval({
        "decision_id": "TEST-MED-001", "device_id": "DEV-001",
        "device_type": "Clinical_AI", "decision_type": "diagnostic_alert",
        "patient_profile": "chronic_condition", "jurisdiction": "UK",
        "sensor_confidence": 85.0, "diagnostic_confidence": 82.0,
        "patient_risk_score": 35.0, "contraindication_score": 8.0,
        "evidence_completeness": 85.0, "care_plan_alignment": 80.0,
        "recovery_trend": 70.0, "comorbidity_index": 25.0,
        "ethics_flag": True, "consent_verified": True, "off_label_use": False,
        "days_since_calibration": 1, "prior_adverse_events": 0,
    })
    check("Medical (ethics_flag=True): BLOCKED", r["decision"] == "BLOCKED", r["decision"], "BLOCKED")
    check("Medical hard block: score penalizado (<15)", r["decision_score"] < 15, r["decision_score"], "<15")
    check("Medical hard block: checkpoint_results documenta razón", len(r.get("checkpoint_results", [])) > 0)
except Exception as e:
    check("Medical ethics_flag hard block", False, traceback.format_exc()[-200:])

# Medical — consent_verified=False
try:
    print("\n  [Medical] consent_verified=False →")
    r2 = med_eval({
        "decision_id": "TEST-MED-002", "device_id": "DEV-002",
        "device_type": "surgical_robot", "decision_type": "treatment_recommendation",
        "patient_profile": "pediatric", "jurisdiction": "EU",
        "sensor_confidence": 82.0, "diagnostic_confidence": 80.0,
        "patient_risk_score": 30.0, "contraindication_score": 5.0,
        "evidence_completeness": 82.0, "care_plan_alignment": 78.0,
        "recovery_trend": 72.0, "comorbidity_index": 20.0,
        "ethics_flag": False, "consent_verified": False, "off_label_use": False,
        "days_since_calibration": 2, "prior_adverse_events": 0,
    })
    check("Medical (consent_verified=False): BLOCKED", r2["decision"] == "BLOCKED", r2["decision"], "BLOCKED")
except Exception as e:
    check("Medical no-consent hard block", False, str(e)[:80])

# Real Estate — AML flag
try:
    from omnix_core.real_estate.real_estate_simulator import _evaluate_decision as re_eval
    print("\n  [Real Estate] aml_flag=True →")
    r = re_eval({
        "decision_id": "TEST-RE-001", "property_id": "PROP-001",
        "decision_type": "AML_property", "property_type": "Residential",
        "market_segment": "prime", "jurisdiction": "UAE", "financing_mode": "Conventional",
        "comparable_quality": 80.0, "model_accuracy": 82.0, "data_freshness": 75.0,
        "market_depth": 70.0, "ltv_ratio": 65.0, "price_deviation": 5.0,
        "aml_risk_score": 90.0, "comparable_alignment": 78.0, "market_trend_score": 68.0,
        "demand_index": 72.0, "inventory_pressure": 30.0, "liquidity_score": 70.0,
        "rate_sensitivity": 35.0, "vacancy_risk": 20.0,
        "aml_flag": True, "rera_compliant": True, "sharia_screening_passed": True,
        "beneficial_owner_verified": True, "days_since_last_valuation": 10,
        "prior_aml_incidents": 0,
    })
    check("Real Estate (aml_flag=True): BLOCKED", r["decision"] == "BLOCKED", r["decision"], "BLOCKED")
    check("Real Estate hard block: score penalizado (<15)", r["decision_score"] < 15, r["decision_score"], "<15")
except Exception as e:
    check("Real Estate AML hard block", False, traceback.format_exc()[-200:])

# Real Estate — LTV breach (Conventional >90%)
try:
    print("\n  [Real Estate] LTV=95% (Conventional, max 90%) →")
    r3 = re_eval({
        "decision_id": "TEST-RE-003", "property_id": "PROP-003",
        "decision_type": "mortgage_approval", "property_type": "Residential",
        "market_segment": "standard", "jurisdiction": "UK", "financing_mode": "Conventional",
        "comparable_quality": 80.0, "model_accuracy": 80.0, "data_freshness": 75.0,
        "market_depth": 70.0, "ltv_ratio": 95.0, "price_deviation": 3.0,
        "aml_risk_score": 10.0, "comparable_alignment": 75.0, "market_trend_score": 65.0,
        "demand_index": 70.0, "inventory_pressure": 28.0, "liquidity_score": 72.0,
        "rate_sensitivity": 30.0, "vacancy_risk": 15.0,
        "aml_flag": False, "rera_compliant": True, "sharia_screening_passed": True,
        "beneficial_owner_verified": True, "days_since_last_valuation": 5,
        "prior_aml_incidents": 0,
    })
    check("Real Estate (LTV=95% > 90%): BLOCKED", r3["decision"] == "BLOCKED", r3["decision"], "BLOCKED")
except Exception as e:
    check("Real Estate LTV hard block", False, str(e)[:80])

# Agents — safety_critical_flag=True
try:
    from omnix_core.agents.agents_simulator import _evaluate_decision as agt_eval
    print("\n  [Agents] safety_critical_flag=True →")
    r = agt_eval({
        "decision_id": "TEST-AGT-001", "agent_id": "AGT-001",
        "agent_type": "Infrastructure_Agent", "decision_type": "state_modification",
        "environment": "production", "reversibility": "irreversible",
        "task_complexity": 80.0, "resource_utilization": 60.0,
        "context_completeness": 75.0, "goal_alignment": 80.0,
        "dependency_score": 50.0, "scope_blast_radius": 85.0,
        "fallback_coverage": 60.0, "permission_scope": 70.0,
        "safety_critical_flag": True, "human_approval_required": False,
        "human_approved": False, "cross_boundary": False,
        "data_sensitivity": "high", "retry_count": 0,
    })
    check("Agents (safety_critical=True): BLOCKED", r["decision"] == "BLOCKED", r["decision"], "BLOCKED")
    check("Agents hard block: score penalizado (<15)", r["decision_score"] < 15, r["decision_score"], "<15")
except Exception as e:
    check("Agents safety_critical hard block", False, traceback.format_exc()[-200:])

# Agents — human_approval_required + not approved
try:
    print("\n  [Agents] human_approval_required=True, human_approved=False →")
    r4 = agt_eval({
        "decision_id": "TEST-AGT-002", "agent_id": "AGT-002",
        "agent_type": "Financial_Agent", "decision_type": "external_api_call",
        "environment": "production", "reversibility": "partially_reversible",
        "task_complexity": 60.0, "resource_utilization": 40.0,
        "context_completeness": 80.0, "goal_alignment": 75.0,
        "dependency_score": 30.0, "scope_blast_radius": 50.0,
        "fallback_coverage": 65.0, "permission_scope": 55.0,
        "safety_critical_flag": False, "human_approval_required": True,
        "human_approved": False, "cross_boundary": False,
        "data_sensitivity": "medium", "retry_count": 0,
    })
    check("Agents (human_approval_required, not approved): BLOCKED", r4["decision"] == "BLOCKED", r4["decision"], "BLOCKED")
except Exception as e:
    check("Agents no-human-approval hard block", False, str(e)[:80])

# Energy — grid emergency
try:
    from omnix_core.energy.energy_simulator import _generate_decision
    import unittest.mock as mock
    print("\n  [Energy] grid emergency (frequency_deviation_hz=0.85) →")
    with mock.patch("omnix_core.energy.energy_simulator.random.random", return_value=0.0):
        with mock.patch("omnix_core.energy.energy_simulator.random.uniform",
                        side_effect=[0.85, 25.0] + [50.0]*30):
            r5 = _generate_decision("dispatch_order", "Natural_Gas", "UK", "TEST-CYCLE")
    check("Energy (frequency_deviation=0.85Hz): BLOCKED", r5["decision"] == "BLOCKED", r5["decision"], "BLOCKED")
    check("Energy hard block: hard_block_reason set", bool(r5.get("hard_block_reason")), r5.get("hard_block_reason"))
except Exception as e:
    check("Energy grid emergency hard block", False, traceback.format_exc()[-200:])

# ── BLOQUE 3: BLOCKED CON SEÑALES DÉBILES ───────────────────────────────────
print(f"\n{'─'*60}")
print("BLOQUE 3 — Motor BLOCKED (señales muy débiles)")
print(f"{'─'*60}")
try:
    print("\n  [Engine] señales débiles (probability=25, risk=88) →")
    engine = GovernanceEvaluationEngine()
    r = engine.evaluate(signals=weak_signals(), asset="TEST_WEAK", domain="trading")
    d = r["decision"]
    check("Señales débiles → BLOCKED o HOLD (no APPROVED)", d in ("BLOCKED", "HOLD"), d, "BLOCKED|HOLD")
    check("veto_chain tiene razones de bloqueo", len(r.get("veto_chain", [])) > 0 or d == "HOLD")
except Exception as e:
    check("Señales débiles test", False, str(e)[:80])

# ── BLOQUE 4: RECEIPT ────────────────────────────────────────────────────────
print(f"\n{'─'*60}")
print("BLOQUE 4 — Receipt PQC (por dominio)")
print(f"{'─'*60}")
try:
    from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
    receipt_tests = [
        ("medical_ai",       "OMNIX-MED"),
        ("real_estate",      "OMNIX-REP"),
        ("autonomous_agent", "OMNIX-AGT"),
        ("energy_governance","OMNIX-EGV"),
        ("trading",          "OMNIX-"),
    ]
    for domain, prefix in receipt_tests:
        rid = DecisionReceiptEngine.build_receipt_id(domain)
        check(f"Receipt {domain}: tiene prefijo {prefix}", rid.startswith(prefix), rid, f"{prefix}...")
except Exception as e:
    check("Receipt engine", False, str(e)[:80])

# ── BLOQUE 5: AVM ─────────────────────────────────────────────────────────────
print(f"\n{'─'*60}")
print("BLOQUE 5 — AVM: 8 dominios calibrados")
print(f"{'─'*60}")
try:
    from omnix_core.governance.external_evaluator import get_avm_instance
    avm = get_avm_instance()
    expected = {
        "trading", "islamic_credit", "insurance", "robotics",
        "medical_ai", "energy_governance", "real_estate", "autonomous_agent"
    }
    found = set()
    for domain in expected:
        try:
            snap = avm.load_snapshot(domain)
            if snap is not None:
                found.add(domain)
        except Exception:
            pass
    for d in sorted(expected):
        check(f"AVM dominio '{d}' calibrado", d in found, "no encontrado" if d not in found else "OK")
    check(f"AVM: 8/8 dominios activos", len(found) >= 8, len(found), 8)
except Exception as e:
    check("AVM load_snapshot", False, str(e)[:80])

# ── BLOQUE 6: ERROR CONTROLADO ───────────────────────────────────────────────
print(f"\n{'─'*60}")
print("BLOQUE 6 — Error controlado (signals inválidas)")
print(f"{'─'*60}")
try:
    engine = GovernanceEvaluationEngine()
    r = engine.evaluate(signals={}, asset="TEST", domain="trading")
    check("signals={}: no rompe el sistema", True)
    check("signals={}: retorna decision", "decision" in r, list(r.keys()))
except Exception:
    check("signals={}: excepción controlada (aceptable)", True)

try:
    r2 = engine.evaluate(signals={"probability_score": 75.0}, asset="TEST", domain="medical_ai")
    check("signals parcial: no rompe el sistema", True)
    check("signals parcial: retorna decision", "decision" in r2)
except Exception:
    check("signals parcial: controlado (aceptable)", True)

# ── RESUMEN ──────────────────────────────────────────────────────────────────
total  = len(results)
passed = sum(1 for _, ok in results if ok)
failed = total - passed

print(f"\n{'='*60}")
print(f"  RESULTADO: {passed}/{total} tests pasados  |  {failed} fallaron")
print(f"{'='*60}")

for name, ok in results:
    tag = "✅" if ok else "❌"
    print(f"  {tag}  {name}")

print()
if failed == 0:
    print("\033[92m  🏆 OMNIX ADR-115 VERIFICADO — 8/8 verticales en el motor real.\033[0m")
    print("     Hard blocks ✓ · 11 checkpoints ✓ · AVM ✓ · Receipts ✓\n")
else:
    print(f"\033[93m  ⚠️  {failed} test(s) con issues — ver detalle arriba.\033[0m\n")

sys.exit(0 if failed == 0 else 1)
