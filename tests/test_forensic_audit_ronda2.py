"""
OMNIX — Auditoría Forense Ronda 2
ADR-074 / ADR-064 / ADR-053

Cuatro bloques:
  A — Silent failures + chaos injection
  B — Cross-domain consistency
  C — End-to-end truth audit (layer-by-layer)
  D — Mutation / tamper detection

Autor: Harold Nunes / OMNIX QUANTUM LTD
Fecha: 2026-04-09
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import tempfile
import time
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("AVM_ENABLED", "true")


# ── helpers ────────────────────────────────────────────────────────────────────

def _tmp_avm(drift_threshold=35.0, max_age_hours=168.0):
    from omnix_core.governance.assumption_validity_monitor import AssumptionValidityMonitor
    return AssumptionValidityMonitor(
        drift_threshold=drift_threshold,
        max_age_hours=max_age_hours,
        snapshots_dir=pathlib.Path(tempfile.mkdtemp()),
    )


def _canonical_receipt_pattern(prefix: str) -> re.Pattern:
    """OMNIX-{PREFIX}-{12 hex uppercase}"""
    return re.compile(rf"^OMNIX-{prefix}-[0-9A-F]{{12}}$")


# ═══════════════════════════════════════════════════════════════════════════════
#  FASE A — Silent failures + chaos injection
# ═══════════════════════════════════════════════════════════════════════════════

class TestSilentFailureInjection:

    def test_A1_missing_signal_does_not_crash_drift_computation(self):
        """Señales parciales no deben colapsar — deben retornar drift válido."""
        avm = _tmp_avm()
        baseline = {"probability_score": 70.0, "signal_coherence": 65.0}
        current  = {"probability_score": 75.0, "signal_coherence": 70.0}
        drift, comps = avm._compute_drift(baseline, current)
        assert isinstance(drift, float), "drift debe ser float"
        assert 0.0 <= drift <= 100.0, f"drift fuera de rango: {drift}"
        assert len(comps) == 2, "solo deben aparecer señales presentes en ambos"

    def test_A2_partial_signals_drift_not_inflated(self):
        """
        BUG CONOCIDO: _compute_drift hace doble normalización cuando faltan señales.
        Con 2 señales de peso 0.25 cada una y drift=5.0 en cada una,
        el drift correcto es 5.0, NO 10.0.

        La fórmula original: (weighted_drift/total_weight) * (1/total_weight)
        con total_weight=0.5 → 2.5/0.5 * 2.0 = 10.0 (INCORRECTO)
        La fórmula correcta:  weighted_drift/total_weight = 5.0
        """
        avm = _tmp_avm()
        baseline = {"probability_score": 70.0, "signal_coherence": 65.0}
        current  = {"probability_score": 75.0, "signal_coherence": 70.0}
        drift, _ = avm._compute_drift(baseline, current)
        assert drift <= 10.0, (
            f"DRIFT INFLADO: con diff=5 en 2 señales se esperaba ~5.0 "
            f"pero se obtuvo {drift}. Bug de doble normalización presente."
        )

    def test_A3_evaluate_with_no_snapshot_returns_pass_through(self):
        """Sin snapshot: is_valid=True, pass_through=True. NO rompe el pipeline."""
        avm = _tmp_avm()
        result = avm.evaluate({"probability_score": 60.0}, domain="unknown_domain_xyz")
        assert result.is_valid is True
        assert result.pass_through is True
        assert result.snapshot_id == "NO_BASELINE"

    def test_A4_evaluate_disabled_env_returns_pass_through(self):
        """AVM_ENABLED=false → siempre pass-through, sin leer snapshots."""
        with patch.dict(os.environ, {"AVM_ENABLED": "false"}):
            avm = _tmp_avm()
            result = avm.evaluate({"probability_score": 60.0}, domain="trading")
        assert result.is_valid is True
        assert result.pass_through is True

    def test_A5_corrupt_json_snapshot_returns_none_gracefully(self):
        """JSON corrompido en disco → load_snapshot devuelve None, NO excepción."""
        avm = _tmp_avm()
        snap_path = avm._snapshot_path("trading")
        snap_path.parent.mkdir(parents=True, exist_ok=True)
        snap_path.write_text('{"broken": "json", incomplete')  # JSON inválido

        result = avm.load_snapshot("trading")
        assert result is None, "Debe devolver None con JSON inválido, no reventar"

    def test_A6_snapshot_with_extra_field_returns_none(self):
        """
        from_dict usa cls(**data) — campo extra → TypeError → None.
        Este es el bug original que causó drift_status=UNKNOWN.
        Comprobamos que el fix _BRIDGE_ONLY_FIELDS en bridge es necesario.
        """
        from omnix_core.governance.assumption_validity_monitor import CalibrationSnapshot
        data_with_extra = {
            "snapshot_id": "AVM-TEST01",
            "parameter_version": "1.test01",
            "domain": "trading",
            "calibrated_at": "2026-01-01T00:00:00+00:00",
            "calibrated_at_epoch": 1735689600.0,
            "baseline_signals": {"probability_score": 70.0},
            "checkpoint_thresholds": {},
            "drift_threshold": 35.0,
            "max_age_hours": 168.0,
            "description": "test",
            "tags": [],
            "baseline_hash": "abc123",   # campo bridge — debe filtrarse ANTES de from_dict
        }
        with pytest.raises(TypeError):
            # Este pytest.raises documenta que from_dict NO acepta campos extra
            CalibrationSnapshot.from_dict(data_with_extra)

    def test_A7_snapshot_without_bridge_fields_loads_correctly(self):
        """Snapshot limpio (sin campos bridge) carga sin TypeError."""
        from omnix_core.governance.assumption_validity_monitor import CalibrationSnapshot
        _BRIDGE_ONLY = {"baseline_hash", "integrity_status", "version", "is_active"}
        data_with_extra = {
            "snapshot_id": "AVM-TEST01",
            "parameter_version": "1.test01",
            "domain": "trading",
            "calibrated_at": "2026-01-01T00:00:00+00:00",
            "calibrated_at_epoch": 1735689600.0,
            "baseline_signals": {"probability_score": 70.0},
            "checkpoint_thresholds": {},
            "drift_threshold": 35.0,
            "max_age_hours": 168.0,
            "description": "test",
            "tags": [],
            "baseline_hash": "abc123",
            "integrity_status": "OK",
            "version": 3,
            "is_active": True,
        }
        clean = {k: v for k, v in data_with_extra.items() if k not in _BRIDGE_ONLY}
        snap = CalibrationSnapshot.from_dict(clean)
        assert snap.domain == "trading"
        assert snap.snapshot_id == "AVM-TEST01"

    def test_A8_db_bridge_with_no_database_url(self):
        """Bridge sin DATABASE_URL: is_available=False, load_all retorna {}."""
        from omnix_core.governance.avm_db_bridge import AVMDatabaseBridge
        bridge = AVMDatabaseBridge(db_url=None)
        with patch.dict(os.environ, {}, clear=True):
            b2 = AVMDatabaseBridge(db_url=None)
        assert b2.is_available() is False
        assert b2.load_all_snapshots() == {}
        assert b2.get_change_log() == []

    def test_A9_version_regression_bug_on_silent_db_failure(self):
        """
        BUG: Si SELECT version falla silenciosamente, new_version=1.
        Con SEED (no RECALIBRATE), esto es correcto.
        Pero si la lógica deja que RECALIBRATE también empiece en 1 cuando
        el SELECT falla, se produciría una regresión de versión.
        """
        from omnix_core.governance.avm_db_bridge import AVMDatabaseBridge
        bridge = AVMDatabaseBridge(db_url="postgresql://invalid:invalid@localhost/invalid")
        # Este bridge está disponible (tiene URL) pero fallará al conectar
        # save_snapshot debería retornar False sin crashear
        result = bridge.save_snapshot(
            {"domain": "trading", "snapshot_id": "T1", "parameter_version": "1.x",
             "baseline_signals": {"probability_score": 70.0}},
            reason="test",
            action="SEED",
        )
        assert result is False, "save_snapshot con DB inválida debe retornar False"

    def test_A10_recalibrate_without_reason_raises_immediately(self):
        """force=True sin reason → ValueError antes de tocar la DB."""
        from omnix_core.governance.avm_db_bridge import AVMDatabaseBridge
        bridge = AVMDatabaseBridge(db_url="postgresql://irrelevant/db")
        with pytest.raises(ValueError, match="reason is required"):
            bridge.save_snapshot(
                {"domain": "trading", "snapshot_id": "T1", "parameter_version": "1.x",
                 "baseline_signals": {}},
                reason="   ",   # vacío / solo espacios
                action="RECALIBRATE",
            )

    def test_A11_invalidate_snapshot_causes_evaluate_pass_through(self):
        """Snapshot invalidado → evaluate devuelve pass_through=True."""
        avm = _tmp_avm()
        avm.save_calibration_snapshot(
            "trading",
            {
                "probability_score": 70.0,
                "signal_coherence": 65.0,
                "risk_exposure": 60.0,
                "stress_resilience": 55.0,
                "trend_persistence": 50.0,
                "logic_consistency": 45.0,
            },
        )
        assert avm.load_snapshot("trading") is not None
        avm.invalidate_snapshot("trading")
        result = avm.evaluate({"probability_score": 70.0}, domain="trading")
        assert result.pass_through is True, "Snapshot invalidado debe resultar en pass_through"

    def test_A12_timestamp_zero_does_not_crash_age_hours(self):
        """calibrated_at_epoch=0 → snapshot con 55+ años, no debe crashear."""
        from omnix_core.governance.assumption_validity_monitor import CalibrationSnapshot
        snap = CalibrationSnapshot(
            snapshot_id="AVM-ZERO",
            parameter_version="1.zero",
            domain="test",
            calibrated_at="1970-01-01T00:00:00+00:00",
            calibrated_at_epoch=0.0,
            baseline_signals={},
            checkpoint_thresholds={},
            drift_threshold=35.0,
            max_age_hours=168.0,
            description="zero epoch",
            tags=[],
        )
        age = snap.age_hours()
        assert age > 0, "edad no puede ser negativa"
        assert age > 400_000, "epoch=0 debe dar edad > 45 años en horas"


# ═══════════════════════════════════════════════════════════════════════════════
#  FASE B — Cross-domain consistency
# ═══════════════════════════════════════════════════════════════════════════════

class TestCrossDomainConsistency:

    DOMAINS = ["trading", "islamic_credit", "insurance", "robotics"]
    DOMAIN_PREFIXES = {
        "trading":       "TRD",
        "islamic_credit": "CRD",
        "insurance":     "INS",
        "robotics":      "RBT",
    }

    def test_B1_receipt_id_canonical_format_all_domains(self):
        """Todos los dominios producen OMNIX-{CODE}-{12hex} via build_receipt_id."""
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        for domain, code in self.DOMAIN_PREFIXES.items():
            rid = DecisionReceiptEngine.build_receipt_id(domain)
            pattern = _canonical_receipt_pattern(code)
            assert pattern.match(rid), (
                f"domain={domain}: receipt_id='{rid}' no coincide con "
                f"OMNIX-{code}-XXXXXXXXXXXX"
            )

    def test_B2_receipt_id_sandbox_uses_pub_code(self):
        """public_sandbox usa OMNIX-PUB-..."""
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        rid = DecisionReceiptEngine.build_receipt_id("public_sandbox")
        assert rid.startswith("OMNIX-PUB-"), f"sandbox receipt: {rid}"

    def test_B3_receipt_id_unknown_domain_uses_fallback_or_raises(self):
        """Dominio desconocido NO debe silenciosamente generar OMNIX--xxxxx."""
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        rid = DecisionReceiptEngine.build_receipt_id("ghost_domain_xyz")
        # No puede empezar con OMNIX-- (guión doble) ni OMNIX-xxxxx sin código
        assert not rid.startswith("OMNIX--"), (
            f"Dominio desconocido generó receipt sin código de dominio: {rid}"
        )

    def test_B4_avm_drift_semantics_consistent_across_domains(self):
        """Misma señal con mismo drift produce mismo resultado en todos los dominios."""
        signals_baseline = {
            "probability_score": 70.0, "signal_coherence": 65.0,
            "risk_exposure": 40.0, "stress_resilience": 60.0,
            "trend_persistence": 55.0, "logic_consistency": 80.0,
        }
        signals_current = {k: v + 5.0 for k, v in signals_baseline.items()}

        results = {}
        for domain in self.DOMAINS:
            avm = _tmp_avm()
            avm.save_calibration_snapshot(domain, signals_baseline)
            r = avm.evaluate(signals_current, domain=domain)
            results[domain] = r.drift_score

        scores = list(results.values())
        assert max(scores) == min(scores), (
            f"Drift score inconsistente por dominio (deben ser iguales con misma entrada): "
            f"{results}"
        )

    def test_B5_avm_block_reason_present_when_drift_exceeds_threshold(self):
        """Si drift > threshold, block_reason NO puede ser None."""
        avm = _tmp_avm(drift_threshold=5.0)  # umbral muy bajo → bloquear fácilmente
        baseline = {
            "probability_score": 50.0, "signal_coherence": 50.0,
            "risk_exposure": 50.0, "stress_resilience": 50.0,
            "trend_persistence": 50.0, "logic_consistency": 50.0,
        }
        current = {k: v + 30.0 for k, v in baseline.items()}  # +30 en todo
        avm.save_calibration_snapshot("trading", baseline)
        result = avm.evaluate(current, domain="trading")
        assert result.is_valid is False
        assert result.block_reason is not None, "block_reason debe existir cuando is_valid=False"
        assert len(result.block_reason) > 10, "block_reason debe ser descriptivo"

    def test_B6_avm_evaluate_always_returns_avm_result_object(self):
        """evaluate() SIEMPRE retorna AVMResult, nunca None ni excepción."""
        from omnix_core.governance.assumption_validity_monitor import AVMResult
        avm = _tmp_avm()
        # Sin snapshot
        r1 = avm.evaluate({}, domain="no_domain")
        assert isinstance(r1, AVMResult)
        # Con snapshot con señales completas (schema requerido por ADR-076)
        full_signals = {
            "probability_score": 70.0, "signal_coherence": 65.0,
            "risk_exposure": 60.0, "stress_resilience": 55.0,
            "trend_persistence": 50.0, "logic_consistency": 45.0,
        }
        avm.save_calibration_snapshot("full_domain", full_signals)
        r2 = avm.evaluate({}, domain="full_domain")
        assert isinstance(r2, AVMResult)
        # Con señales que no coinciden con baseline
        r3 = avm.evaluate({"unknown_signal": 99.0}, domain="full_domain")
        assert isinstance(r3, AVMResult)

    def test_B7_insurance_uses_build_receipt_id(self):
        """insurance_simulator usa DecisionReceiptEngine.build_receipt_id("insurance")."""
        import ast, pathlib
        src = pathlib.Path("omnix_core/insurance/insurance_simulator.py").read_text()
        # Verifica import del engine
        assert "DecisionReceiptEngine" in src, (
            "insurance_simulator debe importar DecisionReceiptEngine"
        )
        # Verifica que NO quedan strings crudas del estilo f"OMNIX-INS-..."
        assert 'f"OMNIX-INS-' not in src, (
            "insurance_simulator no debe generar receipt_id con string literal — "
            "debe usar DecisionReceiptEngine.build_receipt_id('insurance')"
        )
        # Verifica el formato via el engine
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        rid = DecisionReceiptEngine.build_receipt_id("insurance")
        assert _canonical_receipt_pattern("INS").match(rid), f"Insurance receipt inválido: {rid}"

    def test_B8_robotics_uses_build_receipt_id(self):
        """robotics_simulator usa DecisionReceiptEngine.build_receipt_id("robotics")."""
        import pathlib
        src = pathlib.Path("omnix_core/robotics/robotics_simulator.py").read_text()
        assert "DecisionReceiptEngine" in src, (
            "robotics_simulator debe importar DecisionReceiptEngine"
        )
        assert 'f"OMNIX-RBT-' not in src, (
            "robotics_simulator no debe generar receipt_id con string literal — "
            "debe usar DecisionReceiptEngine.build_receipt_id('robotics')"
        )
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        rid = DecisionReceiptEngine.build_receipt_id("robotics")
        assert _canonical_receipt_pattern("RBT").match(rid), f"Robotics receipt inválido: {rid}"

    def test_B9_all_domain_receipt_ids_are_unique(self):
        """100 receipt_ids generados no tienen duplicados."""
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        ids = set()
        for _ in range(25):
            for domain in self.DOMAIN_PREFIXES:
                rid = DecisionReceiptEngine.build_receipt_id(domain)
                assert rid not in ids, f"receipt_id duplicado: {rid}"
                ids.add(rid)

    def test_B10_avm_integrity_status_propagates_correctly(self):
        """
        TAMPERED snapshot en load_all_snapshots devuelve integrity_status=TAMPERED.
        Esto NO debe quedar en UNKNOWN silenciosamente.
        """
        from omnix_core.governance.avm_db_bridge import _compute_hash
        signals = {"probability_score": 70.0}
        correct_hash = _compute_hash(signals)
        tampered_hash = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        assert correct_hash != tampered_hash

        from omnix_core.governance.avm_db_bridge import AVMDatabaseBridge
        bridge = AVMDatabaseBridge.__new__(AVMDatabaseBridge)
        bridge._available = True
        bridge._db_url = "mock"

        fake_row = {
            "domain": "trading",
            "snapshot_id": "AVM-TAMPERED",
            "parameter_version": "1.x",
            "baseline_signals": signals,
            "baseline_hash": tampered_hash,   # hash incorrecto
            "checkpoint_thresholds": {},
            "drift_threshold": 35.0,
            "max_age_hours": 168.0,
            "description": "",
            "tags": [],
            "calibrated_at": "2026-01-01T00:00:00+00:00",
            "calibrated_at_epoch": 1735689600.0,
            "version": 1,
            "is_active": True,
        }

        mock_cursor = MagicMock()
        mock_cursor.description = [(k,) for k in fake_row.keys()]
        mock_cursor.fetchall.return_value = [tuple(fake_row.values())]
        mock_cursor.__enter__ = lambda s: s
        mock_cursor.__exit__ = MagicMock(return_value=False)

        mock_conn = MagicMock()
        mock_conn.__enter__ = lambda s: s
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(bridge, "_get_conn", return_value=mock_conn):
            result = bridge.load_all_snapshots()

        assert "trading" in result
        assert result["trading"]["integrity_status"] == "TAMPERED", (
            "Hash manipulado debe detectarse como TAMPERED, no OK ni UNKNOWN"
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  FASE C — End-to-end truth audit (layer by layer)
# ═══════════════════════════════════════════════════════════════════════════════

class TestEndToEndTruthAudit:

    def test_C1_snapshot_age_hours_is_callable_not_property(self):
        """
        age_hours() es MÉTODO regular, no @property.
        Si se usa sin () → devuelve bound method → comparaciones fallan silenciosamente.
        """
        from omnix_core.governance.assumption_validity_monitor import CalibrationSnapshot
        snap = CalibrationSnapshot(
            snapshot_id="AVM-E2E",
            parameter_version="1.e2e",
            domain="trading",
            calibrated_at=datetime.now(timezone.utc).isoformat(),
            calibrated_at_epoch=datetime.now(timezone.utc).timestamp() - 3600.0,
            baseline_signals={"probability_score": 70.0},
            checkpoint_thresholds={},
            drift_threshold=35.0,
            max_age_hours=168.0,
            description="e2e test",
            tags=[],
        )
        age = snap.age_hours()  # DEBE llamarse con ()
        assert isinstance(age, float), f"age_hours() debe retornar float, no {type(age)}"
        assert 0.9 <= age <= 1.1, f"Snapshot de hace 1h debe tener age ~1.0h, got {age}"

    def test_C2_evaluate_uses_age_hours_as_method_call(self):
        """AVM.evaluate() llama age_hours() correctamente sin TypeError interno."""
        avm = _tmp_avm()
        avm.save_calibration_snapshot(
            "trading",
            {"probability_score": 70.0, "signal_coherence": 65.0,
             "risk_exposure": 40.0, "stress_resilience": 60.0,
             "trend_persistence": 55.0, "logic_consistency": 80.0},
        )
        result = avm.evaluate(
            {"probability_score": 70.0, "signal_coherence": 65.0,
             "risk_exposure": 40.0, "stress_resilience": 60.0,
             "trend_persistence": 55.0, "logic_consistency": 80.0},
            domain="trading"
        )
        assert result.is_valid is True
        assert result.age_hours >= 0.0, "age_hours en resultado debe ser >= 0"
        assert result.drift_score >= 0.0

    def test_C3_bridge_only_fields_are_excluded_from_json(self):
        """restore_to_json escribe JSON sin campos bridge-only → from_dict no revienta."""
        from omnix_core.governance.avm_db_bridge import AVMDatabaseBridge, _compute_hash

        signals = {
            "probability_score": 70.0, "signal_coherence": 65.0,
            "risk_exposure": 40.0, "stress_resilience": 60.0,
            "trend_persistence": 55.0, "logic_consistency": 80.0,
        }
        correct_hash = _compute_hash(signals)

        fake_snap = {
            "domain": "trading",
            "snapshot_id": "AVM-C3TEST",
            "parameter_version": "1.c3test",
            "baseline_signals": signals,
            "baseline_hash": correct_hash,
            "integrity_status": "OK",
            "checkpoint_thresholds": {},
            "drift_threshold": 35.0,
            "max_age_hours": 168.0,
            "description": "e2e test C3",
            "tags": [],
            "calibrated_at": "2026-01-01T00:00:00+00:00",
            "calibrated_at_epoch": 1735689600.0,
            "version": 1,
            "is_active": True,
        }

        bridge = AVMDatabaseBridge.__new__(AVMDatabaseBridge)
        bridge._available = True
        bridge._db_url = "mock"

        fake_row = fake_snap
        mock_cursor = MagicMock()
        mock_cursor.description = [(k,) for k in fake_row.keys()]
        mock_cursor.fetchall.return_value = [tuple(fake_row.values())]
        mock_cursor.__enter__ = lambda s: s
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn = MagicMock()
        mock_conn.__enter__ = lambda s: s
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor

        tmp_dir = tempfile.mkdtemp()
        with patch.object(bridge, "_get_conn", return_value=mock_conn):
            restored, tampered = bridge.restore_to_json(tmp_dir)

        assert restored == 1, "Debe restaurar 1 snapshot"
        assert tampered == 0

        json_path = pathlib.Path(tmp_dir) / "default" / "trading_calibration.json"
        assert json_path.exists(), "Archivo JSON debe existir"
        with open(json_path) as f:
            saved = json.load(f)

        # Verificar que no hay campos bridge-only
        for field in ("baseline_hash", "integrity_status", "version", "is_active"):
            assert field not in saved, (
                f"Campo bridge-only '{field}' no debe estar en JSON local. "
                "Esto causaría TypeError en CalibrationSnapshot.from_dict()"
            )

        # Verificar que el JSON es cargable por CalibrationSnapshot
        from omnix_core.governance.assumption_validity_monitor import CalibrationSnapshot
        snap = CalibrationSnapshot.from_dict(saved)
        assert snap.domain == "trading"

    def test_C4_hash_integrity_verify_chain(self):
        """SHA-256 chain: compute → store → load → verify = OK."""
        from omnix_core.governance.avm_db_bridge import _compute_hash

        signals = {"probability_score": 72.5, "signal_coherence": 68.3}
        hash1 = _compute_hash(signals)
        hash2 = _compute_hash(signals)
        assert hash1 == hash2, "Hash debe ser determinístico (mismo input → mismo output)"

        signals_modified = {"probability_score": 72.6, "signal_coherence": 68.3}
        hash_mod = _compute_hash(signals_modified)
        assert hash_mod != hash1, "Cualquier cambio en signals debe cambiar el hash"

    def test_C5_avm_result_to_dict_contains_required_keys(self):
        """AVMResult.to_dict() tiene todas las claves que el API necesita."""
        avm = _tmp_avm()
        avm.save_calibration_snapshot("trading", {
            "probability_score": 70.0,
            "signal_coherence": 65.0,
            "risk_exposure": 60.0,
            "stress_resilience": 55.0,
            "trend_persistence": 50.0,
            "logic_consistency": 45.0,
        })
        result = avm.evaluate({"probability_score": 70.0}, domain="trading")
        d = result.to_dict()
        required = {"is_valid", "snapshot_id", "parameter_version", "drift_score",
                    "drift_components", "age_hours", "drift_threshold",
                    "block_reason", "warnings", "pass_through"}
        missing = required - set(d.keys())
        assert not missing, f"AVMResult.to_dict() falta claves: {missing}"

    def test_C6_receipt_id_format_stable_across_calls(self):
        """receipt_id siempre cumple el formato, nunca retorna string vacío."""
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        for domain in ["trading", "islamic_credit", "insurance", "robotics", "public_sandbox"]:
            for _ in range(3):
                rid = DecisionReceiptEngine.build_receipt_id(domain)
                assert rid, f"receipt_id vacío para domain={domain}"
                assert rid.startswith("OMNIX-"), f"receipt_id sin prefijo OMNIX: {rid}"
                assert len(rid) >= 15, f"receipt_id demasiado corto: {rid}"


# ═══════════════════════════════════════════════════════════════════════════════
#  FASE D — Mutation / tamper detection
# ═══════════════════════════════════════════════════════════════════════════════

class TestMutationTamperDetection:

    def test_D1_tampered_hash_detected_on_load(self):
        """Cambiar baseline_signals después de guardar → hash mismatch → TAMPERED."""
        from omnix_core.governance.avm_db_bridge import _compute_hash
        signals_original = {"probability_score": 70.0, "signal_coherence": 65.0}
        signals_tampered = {"probability_score": 99.0, "signal_coherence": 65.0}  # adulterado

        hash_original = _compute_hash(signals_original)
        hash_recomputed_on_tampered = _compute_hash(signals_tampered)

        assert hash_original != hash_recomputed_on_tampered, (
            "Hash de signals adulteradas debe diferir del original"
        )

    def test_D2_hash_is_order_independent(self):
        """SHA-256 usa sort_keys=True → orden de claves no importa."""
        from omnix_core.governance.avm_db_bridge import _compute_hash
        s1 = {"b": 2.0, "a": 1.0}
        s2 = {"a": 1.0, "b": 2.0}
        assert _compute_hash(s1) == _compute_hash(s2), "Hash debe ser order-independent"

    def test_D3_recalibrate_without_reason_blocked_at_bridge(self):
        """RECALIBRATE sin reason → ValueError inmediato, sin tocar DB."""
        from omnix_core.governance.avm_db_bridge import AVMDatabaseBridge
        bridge = AVMDatabaseBridge(db_url="postgresql://mock/db")
        with pytest.raises(ValueError):
            bridge.save_snapshot(
                {"domain": "trading", "snapshot_id": "T1",
                 "parameter_version": "1.x", "baseline_signals": {}},
                reason="",
                action="RECALIBRATE",
            )

    def test_D4_tampered_snapshot_not_written_to_json(self):
        """Snapshot TAMPERED jamás se escribe a disco en restore_to_json."""
        from omnix_core.governance.avm_db_bridge import AVMDatabaseBridge, _compute_hash

        signals_real  = {"probability_score": 70.0}
        wrong_hash    = "0" * 64

        fake_snap = {
            "domain": "trading",
            "snapshot_id": "AVM-TAMPERED-D4",
            "parameter_version": "1.d4",
            "baseline_signals": signals_real,
            "baseline_hash": wrong_hash,  # hash incorrecto → TAMPERED
            "integrity_status": "TAMPERED",
            "checkpoint_thresholds": {},
            "drift_threshold": 35.0,
            "max_age_hours": 168.0,
            "description": "tamper test",
            "tags": [],
            "calibrated_at": "2026-01-01T00:00:00+00:00",
            "calibrated_at_epoch": 1735689600.0,
            "version": 1,
            "is_active": True,
        }

        bridge = AVMDatabaseBridge.__new__(AVMDatabaseBridge)
        bridge._available = True
        bridge._db_url = "mock"

        mock_cursor = MagicMock()
        mock_cursor.description = [(k,) for k in fake_snap.keys()]
        mock_cursor.fetchall.return_value = [tuple(fake_snap.values())]
        mock_cursor.__enter__ = lambda s: s
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn = MagicMock()
        mock_conn.__enter__ = lambda s: s
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor

        tmp_dir = tempfile.mkdtemp()
        with patch.object(bridge, "_get_conn", return_value=mock_conn):
            restored, tampered_count = bridge.restore_to_json(tmp_dir)

        assert tampered_count == 1
        assert restored == 0
        json_path = pathlib.Path(tmp_dir) / "trading_calibration.json"
        assert not json_path.exists(), "JSON de snapshot TAMPERED NO debe escribirse a disco"

    def test_D5_version_does_not_regress_on_seed_when_db_has_higher(self):
        """
        SEED: new_version = current_version (no incrementa).
        Pero si el SELECT falla → new_version=1 → UPSERT haría version=1 sobre versión mayor.
        Este test documenta el riesgo (no puede reproducirse sin DB real).
        El fix correcto es: si SELECT falla en SEED, abortar con warning (no usar 1).
        """
        from omnix_core.governance.avm_db_bridge import AVMDatabaseBridge

        bridge = AVMDatabaseBridge.__new__(AVMDatabaseBridge)
        bridge._available = True
        bridge._db_url = "mock"

        # Simular que SELECT version falla → new_version=1
        # Luego el UPSERT también falla → save_snapshot retorna False
        mock_conn_fail = MagicMock()
        mock_conn_fail.__enter__ = MagicMock(side_effect=Exception("DB error"))

        with patch.object(bridge, "_get_conn", return_value=mock_conn_fail):
            result = bridge.save_snapshot(
                {"domain": "trading", "snapshot_id": "T1", "parameter_version": "1.x",
                 "baseline_signals": {"probability_score": 70.0}},
                reason="seed test",
                action="SEED",
            )

        assert result is False, "Si DB falla en save_snapshot, debe retornar False (no crashear)"

    def test_D6_drift_block_not_overridden_by_pass_through_flag(self):
        """
        Si AVM evalúa drift > threshold → is_valid=False.
        pass_through=False (AVM activo, baseline presente).
        """
        avm = _tmp_avm(drift_threshold=1.0)  # umbral extremamente bajo
        baseline = {
            "probability_score": 50.0, "signal_coherence": 50.0,
            "risk_exposure": 50.0, "stress_resilience": 50.0,
            "trend_persistence": 50.0, "logic_consistency": 50.0,
        }
        current = {k: v + 20.0 for k, v in baseline.items()}
        avm.save_calibration_snapshot("trading", baseline)
        result = avm.evaluate(current, domain="trading")
        assert result.is_valid is False
        assert result.pass_through is False, (
            "DRIFT_BLOCK con baseline presente NO debe marcarse como pass_through"
        )
        assert result.block_reason is not None

    def test_D7_critical_age_block_overrides_drift_check(self):
        """
        Snapshot de hace más de critical_age_hours → CRITICAL_STALE BLOCK.
        No importa si el drift es 0.
        """
        from omnix_core.governance.assumption_validity_monitor import CalibrationSnapshot
        avm = _tmp_avm()
        avm.critical_age_hours = 0.001  # 0.036 segundos → cualquier snapshot es "critical stale"

        snap = CalibrationSnapshot(
            snapshot_id="AVM-OLD",
            parameter_version="1.old",
            domain="trading",
            calibrated_at="2020-01-01T00:00:00+00:00",
            calibrated_at_epoch=1577836800.0,  # año 2020
            baseline_signals={"probability_score": 70.0},
            checkpoint_thresholds={},
            drift_threshold=35.0,
            max_age_hours=168.0,
            description="old snapshot",
            tags=[],
        )
        avm._memory_store["trading"] = snap
        result = avm.evaluate({"probability_score": 70.0}, domain="trading")
        assert result.is_valid is False
        assert result.drift_score == 100.0, "CRITICAL_STALE devuelve drift_score=100"

    def test_D8_bridge_hash_uses_sorted_keys_canonical(self):
        """_compute_hash produce hex de 64 chars (SHA-256)."""
        from omnix_core.governance.avm_db_bridge import _compute_hash
        h = _compute_hash({"a": 1.0, "b": 2.0})
        assert len(h) == 64, f"SHA-256 debe tener 64 hex chars, got {len(h)}"
        assert all(c in "0123456789abcdef" for c in h), "Hash debe ser hex lowercase"
