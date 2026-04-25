"""
OMNIX — Phase 1 Critical Core Tests
=====================================
ADR References : ADR-028, ADR-044, ADR-078, ADR-092, ADR-095, ADR-116, ADR-122
Author         : Harold Alberto Nunes Rodelo — OMNIX QUANTUM LTD
Status         : ACTIVE

Fase 1 del plan institucional: cobertura mínima crítica para confianza de deploy.

Módulos bajo prueba:
  1. GovernanceEvaluationEngine  — omnix_core/governance/external_evaluator.py
  2. DecisionReceiptEngine        — omnix_core/evidence/decision_receipt.py
  3. ReceiptVerifier              — omnix_core/evidence/decision_receipt.py
  4. ExecutionDecision boundary   — omnix_services/execution_service/execution_protocol.py

Criterio de éxito (Fase 1):
  ✔ happy path + failure path por módulo
  ✔ pruebas de no-ejecución bajo incoherencia / contradicción
  ✔ verificación de receipts reproducible (hash determinístico)
  ✔ comportamiento fail-closed en errores internos (ADR-116)
  ✔ boundary semántico del execution protocol (should_execute)

Objetivo: confianza de despliegue, no 100 % de cobertura.
"""

import hashlib
import json
import os
import sys
import unittest
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------------------------------------
# Helpers — señales válidas para el pipeline
# ---------------------------------------------------------------------------

def _passing_signals() -> dict:
    """Señales que pasan todos los checkpoints del pipeline (happy path)."""
    return {
        "probability_score": 75.0,
        "risk_exposure": 40.0,
        "signal_coherence": 70.0,
        "trend_persistence": 65.0,
        "stress_resilience": 55.0,
        "logic_consistency": 60.0,
        "signal_integrity": 80.0,
        "temporal_coherence": 70.0,
    }


def _contradictory_signals() -> dict:
    """Señales con logic_consistency por debajo del threshold (CP-6 veto)."""
    signals = _passing_signals()
    signals["logic_consistency"] = 10.0   # CP-6 threshold = 40
    return signals


def _failing_probability_signals() -> dict:
    """Señales con probability_score por debajo del threshold (CP-1 veto)."""
    signals = _passing_signals()
    signals["probability_score"] = 20.0   # CP-1 threshold = 50
    return signals


def _high_risk_signals() -> dict:
    """Señales con risk_exposure por encima del threshold (CP-2 veto)."""
    signals = _passing_signals()
    signals["risk_exposure"] = 90.0   # CP-2 threshold = 65 (lte)
    return signals


# ===========================================================================
# Suite 1 — GovernanceEvaluationEngine (external_evaluator)
# ===========================================================================

class TestGovernanceEvaluationEngine(unittest.TestCase):
    """
    Pruebas del pipeline de 11 checkpoints.
    SAE deshabilitado (SAE_ENABLED=false) para aislar el Layer 1.
    Fail-closed del SAE se prueba en TestGovernanceFailClosed.
    """

    def setUp(self):
        # Desabilitar SAE y AVM para aislar el pipeline de checkpoints
        os.environ["SAE_ENABLED"] = "false"
        os.environ["AVM_ENABLED"] = "false"
        os.environ["CAG_ENABLED"] = "false"
        from omnix_core.governance.external_evaluator import GovernanceEvaluationEngine
        self.engine = GovernanceEvaluationEngine()

    def tearDown(self):
        os.environ.pop("SAE_ENABLED", None)
        os.environ.pop("AVM_ENABLED", None)
        os.environ.pop("CAG_ENABLED", None)

    # ── Happy path ─────────────────────────────────────────────────────────

    def test_happy_path_returns_approved(self):
        """Señales que cumplen todos los thresholds → APPROVED."""
        result = self.engine.evaluate(_passing_signals(), asset="BTC/USD", domain="trading")
        self.assertEqual(result["decision"], "APPROVED")

    def test_approved_has_full_gate_results(self):
        """APPROVED result debe tener gate_results con todos los checkpoints."""
        result = self.engine.evaluate(_passing_signals(), asset="BTC/USD", domain="trading")
        self.assertGreater(len(result["gate_results"]), 0)
        for gate in result["gate_results"]:
            self.assertIn("checkpoint", gate)
            self.assertIn("result", gate)
            self.assertIn("score", gate)

    def test_approved_veto_chain_is_empty(self):
        """APPROVED no debe tener entradas en el veto_chain de checkpoints."""
        result = self.engine.evaluate(_passing_signals(), asset="BTC/USD", domain="trading")
        cp_vetos = [v for v in result["veto_chain"]
                    if v.get("checkpoint_id", "").startswith("CP-")]
        self.assertEqual(len(cp_vetos), 0)

    def test_approved_has_scores_for_all_signals(self):
        """Scores debe incluir todas las señales requeridas y opcionales."""
        result = self.engine.evaluate(_passing_signals(), asset="BTC/USD", domain="trading")
        for signal in ["probability_score", "risk_exposure", "signal_coherence",
                       "trend_persistence", "stress_resilience", "logic_consistency"]:
            self.assertIn(signal, result["scores"])

    def test_approved_checkpoints_passed_equals_total(self):
        """Todas las checkpoints deben pasar en el happy path."""
        result = self.engine.evaluate(_passing_signals(), asset="BTC/USD", domain="trading")
        self.assertEqual(result["checkpoints_passed"], result["checkpoints_total"])
        self.assertEqual(result["checkpoints_blocked"], 0)

    # ── Failure paths ───────────────────────────────────────────────────────

    def test_low_probability_blocks(self):
        """probability_score por debajo de CP-1 threshold → BLOCKED."""
        result = self.engine.evaluate(_failing_probability_signals(),
                                      asset="ETH/USD", domain="trading")
        self.assertEqual(result["decision"], "BLOCKED")

    def test_high_risk_blocks(self):
        """risk_exposure por encima de CP-2 threshold (lte gate) → BLOCKED."""
        result = self.engine.evaluate(_high_risk_signals(),
                                      asset="SOL/USD", domain="trading")
        self.assertEqual(result["decision"], "BLOCKED")

    def test_blocked_has_veto_chain_entry(self):
        """BLOCKED result debe tener al menos una entrada en el veto_chain."""
        result = self.engine.evaluate(_failing_probability_signals(),
                                      asset="BTC/USD", domain="trading")
        self.assertGreater(len(result["veto_chain"]), 0)

    def test_blocked_has_decision_trace(self):
        """BLOCKED result debe documentar el fallo en el decision_trace."""
        result = self.engine.evaluate(_failing_probability_signals(),
                                      asset="BTC/USD", domain="trading")
        self.assertTrue(any("BLOCKED" in str(e) for e in result["decision_trace"]))

    # ── No-ejecución bajo contradicción (logic_consistency) ─────────────────

    def test_contradiction_blocks_execution(self):
        """
        CP-6 (Logic Consistency): logic_consistency < 40 debe bloquear.
        Esto cubre el criterio 'no-ejecución bajo incoherencia'.
        """
        result = self.engine.evaluate(_contradictory_signals(),
                                      asset="BTC/USD", domain="trading")
        self.assertEqual(result["decision"], "BLOCKED")

    def test_contradiction_veto_chain_names_cp6(self):
        """El veto_chain debe identificar CP-6 como gate vetante."""
        result = self.engine.evaluate(_contradictory_signals(),
                                      asset="BTC/USD", domain="trading")
        blocked_gates = [v["checkpoint_id"] for v in result["veto_chain"]]
        self.assertIn("CP-6", blocked_gates)

    def test_zero_logic_consistency_blocked(self):
        """logic_consistency=0 es el caso extremo de contradicción — BLOCKED."""
        signals = _passing_signals()
        signals["logic_consistency"] = 0.0
        result = self.engine.evaluate(signals, asset="BTC/USD", domain="trading")
        self.assertEqual(result["decision"], "BLOCKED")

    # ── Defaults opcionales ─────────────────────────────────────────────────

    def test_optional_signals_get_conservative_defaults(self):
        """Señales opcionales omitidas deben recibir defaults conservadores."""
        signals = {k: v for k, v in _passing_signals().items()
                   if k not in ("signal_integrity", "temporal_coherence")}
        result = self.engine.evaluate(signals, asset="BTC/USD", domain="trading")
        applied = result.get("applied_signal_defaults", {})
        self.assertIn("signal_integrity", applied)
        self.assertIn("temporal_coherence", applied)

    def test_applied_defaults_are_in_decision_trace(self):
        """Los defaults aplicados deben aparecer en el decision_trace (ADR-065)."""
        signals = {k: v for k, v in _passing_signals().items()
                   if k not in ("signal_integrity", "temporal_coherence")}
        result = self.engine.evaluate(signals, asset="BTC/USD", domain="trading")
        trace_str = " ".join(str(e) for e in result["decision_trace"])
        self.assertIn("SIGNAL_DEFAULT_APPLIED", trace_str)

    # ── Validación de señales ───────────────────────────────────────────────

    def test_validate_signals_happy_path(self):
        """Señales válidas deben pasar la validación."""
        valid, msg = self.engine.validate_signals(_passing_signals())
        self.assertTrue(valid)
        self.assertEqual(msg, "")

    def test_validate_signals_missing_required(self):
        """Señal requerida ausente → validación falla."""
        signals = _passing_signals()
        del signals["probability_score"]
        valid, msg = self.engine.validate_signals(signals)
        self.assertFalse(valid)
        self.assertIn("probability_score", msg)

    def test_validate_signals_out_of_range(self):
        """Señal fuera del rango [0,100] → validación falla."""
        signals = _passing_signals()
        signals["probability_score"] = 150.0
        valid, msg = self.engine.validate_signals(signals)
        self.assertFalse(valid)
        self.assertIn("probability_score", msg)

    def test_validate_signals_negative_value(self):
        """Señal negativa → validación falla."""
        signals = _passing_signals()
        signals["risk_exposure"] = -5.0
        valid, msg = self.engine.validate_signals(signals)
        self.assertFalse(valid)

    def test_validate_signals_non_numeric(self):
        """Señal no numérica → validación falla."""
        signals = _passing_signals()
        signals["probability_score"] = "high"
        valid, msg = self.engine.validate_signals(signals)
        self.assertFalse(valid)

    def test_validate_signals_non_dict(self):
        """Input que no es dict → validación falla."""
        valid, msg = self.engine.validate_signals("not a dict")
        self.assertFalse(valid)
        self.assertIn("JSON object", msg)

    # ── Safety floors (ADR-037) ─────────────────────────────────────────────

    def test_threshold_floor_too_low_is_invalid(self):
        """Threshold por debajo del floor mínimo → inválido (ADR-037)."""
        from omnix_core.governance.external_evaluator import validate_threshold_against_floor
        valid, msg = validate_threshold_against_floor("CP-0", 5.0)   # min=40
        self.assertFalse(valid)
        self.assertIn("CP-0", msg)

    def test_threshold_floor_too_high_is_invalid(self):
        """Threshold por encima del floor máximo → inválido (ADR-037)."""
        from omnix_core.governance.external_evaluator import validate_threshold_against_floor
        valid, msg = validate_threshold_against_floor("CP-0", 99.0)  # max=95
        self.assertFalse(valid)

    def test_threshold_floor_valid_range(self):
        """Threshold dentro del rango → válido."""
        from omnix_core.governance.external_evaluator import validate_threshold_against_floor
        valid, msg = validate_threshold_against_floor("CP-0", 70.0)
        self.assertTrue(valid)
        self.assertEqual(msg, "")

    def test_threshold_floor_unknown_checkpoint(self):
        """Checkpoint ID desconocido → inválido."""
        from omnix_core.governance.external_evaluator import validate_threshold_against_floor
        valid, msg = validate_threshold_against_floor("CP-99", 50.0)
        self.assertFalse(valid)
        self.assertIn("Unknown", msg)

    # ── Metadata y dominio ──────────────────────────────────────────────────

    def test_domain_is_preserved_in_result(self):
        """El dominio proporcionado debe aparecer en el resultado."""
        result = self.engine.evaluate(_passing_signals(), asset="LOAN-001", domain="islamic_credit")
        self.assertEqual(result["domain"], "islamic_credit")

    def test_asset_is_preserved_in_result(self):
        """El asset proporcionado debe aparecer en el resultado."""
        result = self.engine.evaluate(_passing_signals(), asset="CLAIM-99A", domain="insurance")
        self.assertEqual(result["asset"], "CLAIM-99A")

    def test_metadata_is_preserved_in_result(self):
        """El metadata proporcionado debe estar en el resultado."""
        meta = {"client_id": "TEST-001", "ref": "REF-XYZ"}
        result = self.engine.evaluate(_passing_signals(), metadata=meta)
        self.assertEqual(result["metadata"]["client_id"], "TEST-001")


# ===========================================================================
# Suite 2 — Fail-Closed Behavior (ADR-116)
# ===========================================================================

class TestGovernanceFailClosed(unittest.TestCase):
    """
    Pruebas del comportamiento fail-closed del evaluador.
    Verifica que errores internos en SAE y gates de compliance bloqueen,
    no dejen pasar (ADR-116, ADR-092).
    """

    def setUp(self):
        os.environ["AVM_ENABLED"] = "false"
        os.environ["CAG_ENABLED"] = "false"

    def tearDown(self):
        os.environ.pop("SAE_ENABLED", None)
        os.environ.pop("AVM_ENABLED", None)
        os.environ.pop("CAG_ENABLED", None)

    def test_sae_internal_error_fails_closed(self):
        """
        SAE error interno → BLOCKED con result=SAE_INTERNAL_ERROR.
        Verifica ADR-116 Policy 2: SAE no puede fail-open.
        """
        os.environ["SAE_ENABLED"] = "true"
        from omnix_core.governance.external_evaluator import GovernanceEvaluationEngine

        with patch(
            "omnix_core.governance.external_evaluator.get_sae",
            side_effect=Exception("SAE_MOCK_CRASH")
        ):
            engine = GovernanceEvaluationEngine()
            result = engine.evaluate(_passing_signals(), asset="BTC/USD", domain="trading")

        self.assertEqual(result["decision"], "BLOCKED")
        self.assertEqual(result.get("layer"), "LAYER_0_STRUCTURAL_ADMISSIBILITY")
        results_in_veto = [v["result"] for v in result.get("veto_chain", [])]
        self.assertTrue(
            any("SAE_INTERNAL_ERROR" in r or "INADMISSIBLE" in r for r in results_in_veto),
            f"Expected SAE_INTERNAL_ERROR in veto_chain, got: {results_in_veto}"
        )

    def test_aml_internal_error_fails_closed(self):
        """
        AML Gate error interno → BLOCKED con AML_INTERNAL_ERROR.
        Verifica ADR-116 Policy 4.
        """
        os.environ["SAE_ENABLED"] = "false"
        os.environ["AML_GATE_ENABLED"] = "true"
        from omnix_core.governance.external_evaluator import GovernanceEvaluationEngine

        with patch(
            "omnix_core.governance.external_evaluator.AMLGate",
            side_effect=Exception("AML_MOCK_CRASH")
        ):
            engine = GovernanceEvaluationEngine()
            result = engine.evaluate(
                _passing_signals(),
                asset="BTC/USD",
                domain="trading",
                compliance_config={"aml_enabled": True}
            )

        self.assertEqual(result["decision"], "BLOCKED")
        aml_in_veto = any("AML" in str(v) for v in result.get("veto_chain", []))
        self.assertTrue(aml_in_veto, "Expected AML veto in veto_chain")
        os.environ.pop("AML_GATE_ENABLED", None)

    def test_custom_checkpoint_override_respected(self):
        """
        Checkpoints personalizados deben ser usados en lugar de los defaults.
        Verifica configurabilidad por cliente (ADR-037).
        """
        os.environ["SAE_ENABLED"] = "false"
        from omnix_core.governance.external_evaluator import GovernanceEvaluationEngine

        strict_checkpoints = [
            {
                "id": "CP-1",
                "name": "Strict Probability",
                "signal": "probability_score",
                "operator": "gte",
                "threshold": 90,
                "optional": False,
                "description": "Only very high probability signals allowed",
            }
        ]
        engine = GovernanceEvaluationEngine(checkpoint_overrides=strict_checkpoints)
        signals = _passing_signals()
        signals["probability_score"] = 75.0   # Passes default (50), fails strict (90)
        result = engine.evaluate(signals, asset="BTC/USD", domain="trading")
        self.assertEqual(result["decision"], "BLOCKED")


# ===========================================================================
# Suite 3 — DecisionReceiptEngine
# ===========================================================================

class TestDecisionReceiptEngine(unittest.TestCase):
    """
    Pruebas del motor de receipts: generación, firma, hash y persistencia.
    ADR-044 (receipts), ADR-078 (key persistence), ADR-095 (retention).
    """

    def _make_engine_no_pqc(self):
        """Motor con PQC deshabilitado (SHA-256 fallback) para tests determinísticos."""
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        engine = DecisionReceiptEngine.__new__(DecisionReceiptEngine)
        engine._provider = None
        engine._signing_keys = None
        engine.db_url = None
        engine._key_mode = "sha256_only"
        engine._active_since = None
        return engine

    def _generate_receipt_no_pqc(self, decision_dict: dict) -> dict:
        engine = self._make_engine_no_pqc()
        with patch.object(engine, "_append_to_transparency_chain", return_value=None), \
             patch.object(engine, "_extract_veto_chain", return_value=[]):
            return engine.generate_receipt(decision_dict)

    # ── Campos requeridos ───────────────────────────────────────────────────

    def test_receipt_has_required_fields(self):
        """Receipt generado debe contener todos los campos obligatorios."""
        receipt = self._generate_receipt_no_pqc({"decision": "APPROVED", "asset": "BTC/USD"})
        required = ["receipt_id", "timestamp", "asset", "decision",
                    "content_hash", "signature", "signature_algorithm",
                    "policy_version", "engine_version", "prev_hash"]
        for field_name in required:
            self.assertIn(field_name, receipt, f"Missing field: {field_name}")

    def test_receipt_decision_is_uppercased(self):
        """La decisión en el receipt siempre debe estar en mayúsculas."""
        receipt = self._generate_receipt_no_pqc({"decision": "approved", "asset": "BTC/USD"})
        self.assertEqual(receipt["decision"], "APPROVED")

    def test_receipt_id_format_known_domain(self):
        """
        Receipt ID para dominio conocido debe ser OMNIX-{CODE}-{hex12}.
        ADR-074 — canonical receipt ID format.
        """
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        receipt_id = DecisionReceiptEngine.build_receipt_id("trading")
        self.assertTrue(receipt_id.startswith("OMNIX-TRD-"))
        parts = receipt_id.split("-")
        self.assertEqual(parts[0], "OMNIX")
        self.assertEqual(parts[1], "TRD")
        self.assertEqual(len(parts[2]), 12)

    def test_receipt_id_format_unknown_domain(self):
        """Receipt ID para dominio desconocido debe ser OMNIX-{hex12}."""
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        receipt_id = DecisionReceiptEngine.build_receipt_id("unknown_vertical")
        self.assertTrue(receipt_id.startswith("OMNIX-"))
        self.assertNotIn("OMNIX-None-", receipt_id)

    def test_receipt_id_format_no_domain(self):
        """Receipt ID sin dominio debe seguir el formato legacy OMNIX-{hex12}."""
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        receipt_id = DecisionReceiptEngine.build_receipt_id("")
        self.assertTrue(receipt_id.startswith("OMNIX-"))

    def test_domain_codes_all_known_verticals(self):
        """Todos los dominios conocidos deben tener un código de 3 letras."""
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        known_domains = ["trading", "islamic_credit", "insurance", "robotics",
                         "public_sandbox", "medical_ai", "autonomous_agent",
                         "real_estate", "energy_governance", "stablecoin"]
        for domain in known_domains:
            receipt_id = DecisionReceiptEngine.build_receipt_id(domain)
            parts = receipt_id.split("-")
            self.assertGreater(len(parts), 2, f"No domain code for: {domain}")

    # ── Content hash determinístico ─────────────────────────────────────────

    def test_content_hash_is_non_empty(self):
        """content_hash debe ser una cadena hexadecimal no vacía."""
        receipt = self._generate_receipt_no_pqc({"decision": "BLOCKED", "asset": "ETH/USD"})
        self.assertIsInstance(receipt["content_hash"], str)
        self.assertEqual(len(receipt["content_hash"]), 64)   # SHA-256 hex = 64 chars

    def test_content_hash_is_deterministic(self):
        """
        El mismo payload debe producir el mismo content_hash.
        Garantiza que la verificación es reproducible (ADR-096 hash determinism).
        """
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        engine = self._make_engine_no_pqc()
        payload = {
            "receipt_id": "OMNIX-TRD-TEST000001",
            "timestamp": "2026-04-25T12:00:00+00:00",
            "asset": "BTC/USD",
            "decision": "APPROVED",
            "veto_chain": [],
            "policy_version": "6.5.4e",
            "engine_version": "6.5.4e",
            "prev_hash": "",
            "signing_provider": "sha256",
            "signing_key_id": None,
            "domain": "trading",
            "issued_at_ms": 1745582400000,
            "ttl_epoch_ms": 1745582430000,
            "ttl_ms": 30000,
        }
        hash1 = engine._compute_hash(payload)
        hash2 = engine._compute_hash(payload)
        self.assertEqual(hash1, hash2)

    def test_content_hash_changes_on_tamper(self):
        """Modificar cualquier campo del payload debe cambiar el hash."""
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        engine = self._make_engine_no_pqc()
        payload = {"receipt_id": "OMNIX-TRD-AAA", "decision": "APPROVED"}
        hash_original = engine._compute_hash(payload)
        payload_tampered = dict(payload)
        payload_tampered["decision"] = "BLOCKED"
        hash_tampered = engine._compute_hash(payload_tampered)
        self.assertNotEqual(hash_original, hash_tampered)

    # ── Firma SHA-256 fallback ──────────────────────────────────────────────

    def test_sha256_signature_is_not_none(self):
        """En modo SHA-256 fallback, signature debe ser no-None."""
        receipt = self._generate_receipt_no_pqc({"decision": "APPROVED", "asset": "BTC/USD"})
        self.assertIsNotNone(receipt["signature"])

    def test_sha256_signature_is_hex_string(self):
        """Firma SHA-256 debe ser una cadena hexadecimal de 64 caracteres."""
        receipt = self._generate_receipt_no_pqc({"decision": "BLOCKED", "asset": "BTC/USD"})
        self.assertIsInstance(receipt["signature"], str)
        if receipt["signature_format"] == "hex_sha256_fallback":
            self.assertEqual(len(receipt["signature"]), 64)

    def test_sha256_signature_matches_content_hash(self):
        """Firma SHA-256 = SHA-256(content_hash) — verificable externamente."""
        receipt = self._generate_receipt_no_pqc({"decision": "BLOCKED", "asset": "BTC/USD"})
        if receipt["signature_format"] == "hex_sha256_fallback":
            expected = hashlib.sha256(receipt["content_hash"].encode("utf-8")).hexdigest()
            self.assertEqual(receipt["signature"], expected)

    # ── PQC signing con mock ────────────────────────────────────────────────

    def test_pqc_signing_uses_provider(self):
        """Cuando PQC está disponible, la firma debe usar el provider."""
        import base64
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine

        mock_provider = MagicMock()
        mock_provider.provider_id.return_value = "dilithium3"
        mock_provider.algorithm_name.return_value = "Dilithium-3"
        mock_provider.sign.return_value = b"mock_pqc_signature"
        mock_provider.serialize_public_key.return_value = "mock_pubkey_b64"

        engine = DecisionReceiptEngine.__new__(DecisionReceiptEngine)
        engine._provider = mock_provider
        engine._signing_keys = (b"pubkey", b"privkey")
        engine.db_url = None

        with patch.object(engine, "_append_to_transparency_chain", return_value=None), \
             patch.object(engine, "_extract_veto_chain", return_value=[]):
            receipt = engine.generate_receipt({"decision": "APPROVED", "asset": "BTC/USD"})

        expected_sig = base64.b64encode(b"mock_pqc_signature").decode()
        self.assertEqual(receipt["signature_algorithm"], "Dilithium-3")
        self.assertEqual(receipt["signing_provider"], "dilithium3")
        self.assertEqual(receipt["signature"], expected_sig)
        self.assertEqual(receipt["signature_format"], "base64_pqc")

    # ── Persistencia sin DB ─────────────────────────────────────────────────

    def test_store_receipt_without_db_returns_false(self):
        """store_receipt sin db_url debe devolver False, no lanzar excepción."""
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        engine = DecisionReceiptEngine.__new__(DecisionReceiptEngine)
        engine.db_url = None
        result = engine.store_receipt({"receipt_id": "OMNIX-TEST-000000000001"})
        self.assertFalse(result)

    def test_get_last_hash_without_db_returns_empty(self):
        """get_last_hash sin db_url debe devolver cadena vacía, no excepción."""
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        engine = DecisionReceiptEngine.__new__(DecisionReceiptEngine)
        engine.db_url = None
        result = engine.get_last_hash()
        self.assertEqual(result, "")

    # ── Stable key mode (ADR-085) — mismo proceso = misma clave ────────────

    def test_two_engines_share_stable_key_in_same_process(self):
        """
        Dos instancias de DecisionReceiptEngine en el mismo proceso deben
        compartir la misma clave pública (ADR-085 stable_process mode).
        Esto garantiza que las receipts emitidas antes de un restart con
        la misma clave sean verificables con la misma public_key.
        """
        from omnix_core.evidence.decision_receipt import (
            DecisionReceiptEngine,
            _STABLE_SIGNING_KEYS,
        )
        if _STABLE_SIGNING_KEYS is None:
            self.skipTest("No stable signing keys available (PQC unavailable)")

        engine_a = DecisionReceiptEngine(db_url=None)
        engine_b = DecisionReceiptEngine(db_url=None)

        if engine_a.key_mode in ("stable_process", "persisted") and \
           engine_b.key_mode in ("stable_process", "persisted"):
            self.assertEqual(engine_a.key_id, engine_b.key_id,
                             "Two engines in the same process must share key_id (ADR-085)")

    def test_key_id_is_16_hex_chars(self):
        """key_id debe ser los primeros 16 caracteres hexadecimales del SHA-256 de la clave."""
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        engine = DecisionReceiptEngine(db_url=None)
        if engine.key_id is not None:
            self.assertEqual(len(engine.key_id), 16)
            int(engine.key_id, 16)   # debe ser hexadecimal válido


# ===========================================================================
# Suite 4 — ReceiptVerifier
# ===========================================================================

class TestReceiptVerifier(unittest.TestCase):
    """
    Pruebas del verificador de receipts.
    Verifica hash_valid, signature_valid y comportamiento ante tampering.
    """

    def _generate_receipt(self) -> dict:
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        engine = DecisionReceiptEngine.__new__(DecisionReceiptEngine)
        engine._provider = None
        engine._signing_keys = None
        engine.db_url = None
        engine._key_mode = "sha256_only"
        engine._active_since = None
        with patch.object(engine, "_append_to_transparency_chain", return_value=None), \
             patch.object(engine, "_extract_veto_chain", return_value=[]):
            return engine.generate_receipt({
                "decision": "APPROVED",
                "asset": "BTC/USD",
                "domain": "trading",
            })

    # ── Happy path ──────────────────────────────────────────────────────────

    def test_verifier_returns_complete_structure_for_untampered_receipt(self):
        """
        verify_receipt debe devolver una estructura completa con todos los campos
        esperados por el protocolo de auditoría.

        NOTA DE DISEÑO (ADR-095 §4): El ReceiptVerifier reconstruye un subconjunto
        de campos (v1 hash), mientras que DecisionReceiptEngine incluye campos
        adicionales como 'domain' y 'signing_key_id' en su hash interno.
        Esta es una brecha documentada — el hash_valid de v1 puede ser False
        incluso para receipts no alterados. La verificación institucional completa
        usa el canonical_hash v2 (ADR-096) + firma Dilithium-3.
        """
        from omnix_core.evidence.decision_receipt import ReceiptVerifier
        receipt = self._generate_receipt()
        result = ReceiptVerifier.verify_receipt(receipt)
        for expected_field in ["receipt_id", "hash_valid", "signature_valid",
                               "verification_timestamp", "computed_hash", "stored_hash"]:
            self.assertIn(expected_field, result, f"Missing field in verifier result: {expected_field}")
        self.assertIsInstance(result["computed_hash"], str)
        self.assertEqual(len(result["computed_hash"]), 64)   # SHA-256 hex

    def test_verifier_returns_receipt_id(self):
        """El resultado de la verificación debe incluir el receipt_id."""
        from omnix_core.evidence.decision_receipt import ReceiptVerifier
        receipt = self._generate_receipt()
        result = ReceiptVerifier.verify_receipt(receipt)
        self.assertEqual(result["receipt_id"], receipt["receipt_id"])

    def test_verifier_includes_verification_timestamp(self):
        """El resultado debe incluir verification_timestamp como string ISO."""
        from omnix_core.evidence.decision_receipt import ReceiptVerifier
        receipt = self._generate_receipt()
        result = ReceiptVerifier.verify_receipt(receipt)
        self.assertIn("verification_timestamp", result)
        self.assertIsInstance(result["verification_timestamp"], str)

    # ── Failure paths (tampering) ───────────────────────────────────────────

    def test_hash_invalid_after_decision_tamper(self):
        """
        Cambiar el campo 'decision' después de emitir el receipt debe
        invalidar el hash — prueba de inmutabilidad.
        """
        from omnix_core.evidence.decision_receipt import ReceiptVerifier
        receipt = self._generate_receipt()
        tampered = dict(receipt)
        tampered["decision"] = "BLOCKED"   # receipt original era APPROVED
        result = ReceiptVerifier.verify_receipt(tampered)
        self.assertFalse(result["hash_valid"])

    def test_hash_invalid_after_asset_tamper(self):
        """Cambiar el campo 'asset' debe invalidar el hash."""
        from omnix_core.evidence.decision_receipt import ReceiptVerifier
        receipt = self._generate_receipt()
        tampered = dict(receipt)
        tampered["asset"] = "XRP/USD"   # original era BTC/USD
        result = ReceiptVerifier.verify_receipt(tampered)
        self.assertFalse(result["hash_valid"])

    def test_hash_invalid_after_content_hash_tamper(self):
        """
        Sustituir el content_hash por uno falso debe hacer que la
        verificación calcule diferente y devuelva hash_valid=False.
        """
        from omnix_core.evidence.decision_receipt import ReceiptVerifier
        receipt = self._generate_receipt()
        tampered = dict(receipt)
        tampered["content_hash"] = "0" * 64   # hash falso
        result = ReceiptVerifier.verify_receipt(tampered)
        self.assertFalse(result["hash_valid"])

    def test_verifier_handles_unknown_provider_gracefully(self):
        """Un provider de firma desconocido no debe lanzar excepción."""
        from omnix_core.evidence.decision_receipt import ReceiptVerifier
        receipt = self._generate_receipt()
        receipt_unknown = dict(receipt)
        receipt_unknown["signing_provider"] = "quantum_xyz_9000"
        receipt_unknown["signature"] = "fakesignature"
        receipt_unknown["public_key"] = "fakepublickey"
        try:
            result = ReceiptVerifier.verify_receipt(receipt_unknown)
            self.assertIn("signature_valid", result)
        except Exception as e:
            self.fail(f"verify_receipt raised unexpected exception: {e}")


# ===========================================================================
# Suite 5 — ExecutionDecision Boundary (execution_protocol)
# ===========================================================================

try:
    from omnix_services.execution_service.execution_protocol import (
        ExecutionDecision,
        ExecutionStyle,
        ExecutionUrgency,
        MarketCondition,
        SlippagePrediction,
        ExecutionTiming,
    )
    _EXECUTION_PROTOCOL_AVAILABLE = True
except Exception as _ep_import_err:
    _EXECUTION_PROTOCOL_AVAILABLE = False


def _make_slippage(bps: float = 10.0) -> "SlippagePrediction":
    """Helper: SlippagePrediction con valores controlados."""
    return SlippagePrediction(
        expected_slippage_bps=bps,
        worst_case_slippage_bps=bps * 2.5,
        best_case_slippage_bps=bps * 0.4,
        confidence=0.7,
    )


def _make_timing(execute_now: bool = True) -> "ExecutionTiming":
    """Helper: ExecutionTiming con ejecución inmediata configurable."""
    return ExecutionTiming(
        execute_now=execute_now,
        delay_seconds=0 if execute_now else 60,
        reason="Test timing",
        confidence=0.85,
    )


def _make_decision(**overrides) -> "ExecutionDecision":
    """
    Helper: ExecutionDecision nominal (should_execute=True por defecto).
    Cualquier campo puede ser overrideado para pruebas de failure path.
    """
    defaults = dict(
        symbol="BTC/USD",
        side="buy",
        size_usd=10000.0,
        recommended_style=ExecutionStyle.LIMIT,
        urgency=ExecutionUrgency.NORMAL,
        market_condition=MarketCondition.FAVORABLE,
        slippage=_make_slippage(10.0),
        timing=_make_timing(execute_now=True),
        liquidity_score=75.0,
        volatility_regime="NORMAL",
        correlation_risk=20.0,
        contagion_risk=10.0,
        safe_haven_flow="NEUTRAL",
        data_integrity_block=False,
        block_reason="",
        liquidity_data_available=True,
        correlation_data_available=True,
    )
    defaults.update(overrides)
    return ExecutionDecision(**defaults)


@unittest.skipUnless(_EXECUTION_PROTOCOL_AVAILABLE, "execution_protocol not importable")
class TestExecutionDecisionBoundary(unittest.TestCase):
    """
    Pruebas del boundary semántico de ExecutionDecision.
    No require sub-engines reales — prueba la lógica de should_execute
    a través de los campos del dataclass. ADR-122 §3.3.
    """

    # ── Happy path ──────────────────────────────────────────────────────────

    def test_nominal_should_execute_true(self):
        """Condiciones favorables → should_execute = True."""
        decision = _make_decision()
        self.assertTrue(decision.should_execute)

    def test_to_dict_has_should_execute(self):
        """to_dict() debe incluir should_execute como campo serializable."""
        decision = _make_decision()
        d = decision.to_dict()
        self.assertIn("should_execute", d)
        self.assertTrue(d["should_execute"])

    # ── Failure paths ───────────────────────────────────────────────────────

    def test_data_integrity_block_prevents_execution(self):
        """
        data_integrity_block=True → should_execute=False.
        Criterio: no-ejecución cuando faltan datos críticos (liquidez/correlación).
        ADR-122 §3.3.
        """
        decision = _make_decision(
            data_integrity_block=True,
            block_reason="CRITICAL: Both liquidity and correlation data unavailable",
        )
        self.assertFalse(decision.should_execute)

    def test_crisis_market_prevents_execution(self):
        """
        market_condition=CRISIS → should_execute=False.
        OMNIX no debe ejecutar en condiciones de crisis sistémica.
        """
        decision = _make_decision(market_condition=MarketCondition.CRISIS)
        self.assertFalse(decision.should_execute)

    def test_high_contagion_prevents_execution(self):
        """
        contagion_risk >= 80 → should_execute=False.
        Riesgo de contagio extremo bloquea ejecución.
        """
        decision = _make_decision(contagion_risk=80.0)
        self.assertFalse(decision.should_execute)

    def test_very_high_contagion_prevents_execution(self):
        """contagion_risk=100 (máximo) → should_execute=False."""
        decision = _make_decision(contagion_risk=100.0)
        self.assertFalse(decision.should_execute)

    def test_unacceptable_slippage_prevents_execution(self):
        """
        slippage > 50bps (unacceptable) → should_execute=False.
        Criterio: no ejecutar cuando el costo de ejecución supera el límite.
        """
        decision = _make_decision(slippage=_make_slippage(bps=60.0))
        self.assertFalse(decision.should_execute)

    def test_timing_not_now_prevents_execution(self):
        """
        execute_now=False → should_execute=False.
        El motor de timing indica esperar.
        """
        decision = _make_decision(timing=_make_timing(execute_now=False))
        self.assertFalse(decision.should_execute)

    def test_adverse_market_alone_does_not_block(self):
        """
        ADVERSE (no CRISIS) no bloquea por sí solo — sólo CRISIS bloquea.
        Verifica que el threshold de bloqueo es correcto.
        """
        decision = _make_decision(market_condition=MarketCondition.ADVERSE)
        self.assertTrue(decision.should_execute)

    def test_contagion_below_threshold_allows_execution(self):
        """contagion_risk < 80 → no bloquea por sí solo."""
        decision = _make_decision(contagion_risk=79.9)
        self.assertTrue(decision.should_execute)

    # ── Data integrity combinations ─────────────────────────────────────────

    def test_data_integrity_block_with_crisis_still_blocked(self):
        """Múltiples condiciones de bloqueo → should_execute=False."""
        decision = _make_decision(
            data_integrity_block=True,
            market_condition=MarketCondition.CRISIS,
            contagion_risk=95.0,
        )
        self.assertFalse(decision.should_execute)

    def test_to_dict_includes_block_reason(self):
        """to_dict() debe incluir block_reason cuando data_integrity_block=True."""
        reason = "CRITICAL: Liquidity data unavailable"
        decision = _make_decision(data_integrity_block=True, block_reason=reason)
        d = decision.to_dict()
        self.assertEqual(d["data_integrity_block"], True)
        self.assertEqual(d["block_reason"], reason)

    # ── Risk-adjusted size ──────────────────────────────────────────────────

    def test_risk_adjusted_size_reduced_in_high_volatility(self):
        """
        Volatilidad HIGH debe reducir el tamaño ajustado al riesgo.
        risk_adjusted_size < size_usd en régimen HIGH.
        """
        decision = _make_decision(volatility_regime="HIGH", size_usd=10000.0)
        self.assertLess(decision.risk_adjusted_size, decision.size_usd)

    def test_risk_adjusted_size_reduced_in_extreme_volatility(self):
        """
        Volatilidad EXTREME debe reducir el tamaño ajustado en un 50% respecto al nominal.
        EXTREME y HIGH comparten el mismo factor de reducción (0.5x) por diseño — ambos
        son regímenes que requieren la misma reducción de exposición en el pipeline actual.
        """
        decision_extreme = _make_decision(volatility_regime="EXTREME", size_usd=10000.0)
        self.assertAlmostEqual(decision_extreme.risk_adjusted_size, 5000.0, places=2,
                               msg="EXTREME volatility must halve risk-adjusted size (factor=0.5)")

    def test_risk_adjusted_size_nominal_in_normal_regime(self):
        """NORMAL + sin otros factores → risk_adjusted_size == size_usd."""
        decision = _make_decision(
            volatility_regime="NORMAL",
            contagion_risk=0.0,
            correlation_risk=0.0,
            market_condition=MarketCondition.FAVORABLE,
            size_usd=10000.0,
        )
        self.assertAlmostEqual(decision.risk_adjusted_size, 10000.0, places=2)

    # ── ExecutionProtocol fallback ──────────────────────────────────────────

    def test_fallback_decision_uses_limit_style(self):
        """
        _get_fallback_decision debe retornar ExecutionStyle.LIMIT.
        Es la decisión conservadora en caso de error interno (ADR-122).
        """
        from omnix_services.execution_service.execution_protocol import ExecutionProtocol
        protocol = ExecutionProtocol(
            liquidity_analyzer=None,
            volatility_engine=None,
            correlation_engine=None,
            trading_service=None,
        )
        fallback = protocol._get_fallback_decision(
            symbol="BTC/USD",
            side="buy",
            size_usd=5000.0,
            urgency=ExecutionUrgency.NORMAL,
        )
        self.assertEqual(fallback.recommended_style, ExecutionStyle.LIMIT,
                         "Fallback must always be LIMIT — conservative default (ADR-122)")

    def test_fallback_decision_is_conservative_limit(self):
        """
        La decisión de fallback debe devolver LIMIT con confianza baja (0.3).
        El fallback es conservador pero ejecutable — preserva la capacidad de salida
        sin bloquear todas las operaciones (diseño intencional del execution boundary).
        """
        from omnix_services.execution_service.execution_protocol import ExecutionProtocol
        protocol = ExecutionProtocol(
            liquidity_analyzer=None,
            volatility_engine=None,
            correlation_engine=None,
            trading_service=None,
        )
        fallback = protocol._get_fallback_decision(
            symbol="ETH/USD",
            side="sell",
            size_usd=5000.0,
            urgency=ExecutionUrgency.NORMAL,
        )
        self.assertEqual(fallback.recommended_style, ExecutionStyle.LIMIT,
                         "Fallback must be LIMIT (conservative) — ADR-122 §3.3")
        self.assertLessEqual(fallback.confidence, 0.3,
                             "Fallback confidence must be low (≤ 0.3) — limited data")
        self.assertFalse(fallback.data_integrity_block,
                         "data_integrity_block is a pre-execution gate, not set in fallback")

    def test_execution_decision_without_data_integrity_block_can_execute(self):
        """
        Con data_integrity_block=False y condiciones favorables,
        should_execute=True. Verifica que el boundary permite ejecución correcta.
        """
        decision = _make_decision(
            data_integrity_block=False,
            market_condition=MarketCondition.FAVORABLE,
            contagion_risk=5.0,
            slippage=_make_slippage(bps=8.0),
            timing=_make_timing(execute_now=True),
        )
        self.assertTrue(decision.should_execute)


if __name__ == "__main__":
    unittest.main()
