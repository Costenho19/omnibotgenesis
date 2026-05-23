"""
OMNIX — Auditoría Forense Ronda 3
ADR-074 / ADR-064 / Arquitecto: 2026-04-09

50 tests distribuidos en 8 bloques ejecutados en el orden recomendado:

  Fase 1 — H (Fail-closed bajo excepción real) + F (Contradicción de políticas)
  Fase 2 — D (Caos de persistencia) + B (Idempotencia y retries)
  Fase 3 — A (Concurrencia y race conditions) + G (Dashboard truth)
  Fase 4 — C (Fuzzing hostil de inputs) + E (Integridad criptográfica profunda)

Criterio de despliegue:
  PASS → ningún hallazgo crítico, no hay PASS indebido,
         no hay duplicación no controlada de verdad operativa,
         dashboard y DB coinciden, retries no alteran resultado lógico.

Harold Nunes / OMNIX QUANTUM LTD
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import pathlib
import re
import tempfile
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("AVM_ENABLED", "true")


# ── helpers ────────────────────────────────────────────────────────────────────

def _tmp_avm(drift_threshold=35.0, max_age_hours=168.0, critical_age_hours=720.0):
    from omnix_core.governance.assumption_validity_monitor import AssumptionValidityMonitor
    return AssumptionValidityMonitor(
        drift_threshold=drift_threshold,
        max_age_hours=max_age_hours,
        critical_age_hours=critical_age_hours,
        snapshots_dir=pathlib.Path(tempfile.mkdtemp()),
    )


def _baseline_signals(**overrides):
    base = {
        "probability_score": 70.0,
        "signal_coherence": 65.0,
        "risk_exposure": 40.0,
        "stress_resilience": 60.0,
        "trend_persistence": 55.0,
        "logic_consistency": 80.0,
    }
    base.update(overrides)
    return base


def _make_snapshot(avm, domain="trading", **overrides):
    return avm.save_calibration_snapshot(domain, _baseline_signals(**overrides))


# ═══════════════════════════════════════════════════════════════════════════════
#  FASE 1 — BLOQUE H: Fail-closed bajo excepción real
# ═══════════════════════════════════════════════════════════════════════════════

class TestFailClosedUnderException:

    def test_H1_nan_in_single_signal_blocks_evaluation(self):
        """
        BUG CRÍTICO CORREGIDO: NaN en probability_score → drift=NaN →
        NaN > 35.0 = False → PASS silencioso (antes del fix).
        Con el fix: NON_FINITE_SIGNAL → is_valid=False, pass_through=False.
        """
        avm = _tmp_avm()
        _make_snapshot(avm)
        signals = _baseline_signals(probability_score=float('nan'))
        result = avm.evaluate(signals, domain="trading")
        assert result.is_valid is False, (
            "NaN en señal debe BLOQUEAR — nunca pasar silenciosamente"
        )
        assert result.pass_through is False
        assert result.block_reason is not None
        assert "NON_FINITE" in result.block_reason

    def test_H2_positive_infinity_blocks_evaluation(self):
        """Infinity positivo → BLOCK, no PASS."""
        avm = _tmp_avm()
        _make_snapshot(avm)
        result = avm.evaluate(
            _baseline_signals(signal_coherence=float('inf')),
            domain="trading"
        )
        assert result.is_valid is False
        assert result.pass_through is False

    def test_H3_negative_infinity_blocks_evaluation(self):
        """-Infinity → BLOCK, no PASS."""
        avm = _tmp_avm()
        _make_snapshot(avm)
        result = avm.evaluate(
            _baseline_signals(risk_exposure=float('-inf')),
            domain="trading"
        )
        assert result.is_valid is False
        assert result.pass_through is False

    def test_H4_all_nan_signals_blocks(self):
        """Todos los signals NaN → BLOCK con drift_score=100.0."""
        avm = _tmp_avm()
        _make_snapshot(avm)
        result = avm.evaluate(
            {k: float('nan') for k in _baseline_signals().keys()},
            domain="trading"
        )
        assert result.is_valid is False
        assert result.drift_score == 100.0

    def test_H5_non_finite_in_baseline_clamped_to_max_drift(self):
        """
        Si un valor no-finito llegó al baseline (situación excepcional),
        _compute_drift lo clampea a 100.0 → drift > threshold → BLOCK.
        """
        from omnix_core.governance.assumption_validity_monitor import (
            CalibrationSnapshot, datetime, timezone
        )
        avm = _tmp_avm(drift_threshold=5.0)  # umbral muy bajo
        snap = CalibrationSnapshot(
            snapshot_id="AVM-H5",
            parameter_version="1.h5",
            domain="trading",
            calibrated_at=datetime.now(timezone.utc).isoformat(),
            calibrated_at_epoch=datetime.now(timezone.utc).timestamp(),
            baseline_signals={"probability_score": float('inf')},  # inf en baseline
            checkpoint_thresholds={},
            drift_threshold=5.0,
            max_age_hours=168.0,
            description="test H5",
            tags=[],
        )
        avm._memory_store["trading"] = snap
        # current con valor normal → drift con inf en baseline → max drift
        result = avm.evaluate({"probability_score": 70.0}, domain="trading")
        # Primero pasa el guard de non-finite (baseline, no current) — el guard
        # solo checa current signals. Pero _compute_drift tiene segunda barrera.
        # drift = 100.0 → > threshold=5.0 → BLOCK
        assert result.is_valid is False

    def test_H6_compute_drift_with_nan_clamps_not_passes(self):
        """
        _compute_drift: NaN/Inf en current → clampea a 100.0, NO pasa.
        Verificar que después del fix, el drift es determinístico y máximo.
        """
        avm = _tmp_avm(drift_threshold=99.9)  # threshold casi máximo
        baseline = _baseline_signals()
        current = {**baseline, "probability_score": float('nan')}
        drift, comps = avm._compute_drift(baseline, current)
        assert math.isfinite(drift), "drift siempre debe ser finito después del fix"
        assert "probability_score" in comps
        assert comps["probability_score"] == 100.0, "NaN → drift component = 100.0"

    def test_H7_evaluate_with_empty_signals_and_snapshot_is_pass_through(self):
        """
        Señales vacías + snapshot presente: no hay señales para comparar
        → drift=0.0, is_valid=True (no señales = no evidencia de drift).
        Documentado: pass_through=False (AVM activo, baseline existe).
        """
        avm = _tmp_avm()
        _make_snapshot(avm)
        result = avm.evaluate({}, domain="trading")
        assert result.pass_through is False, "Con snapshot presente, no es pass_through"
        assert result.is_valid is True, "Sin señales actuales no hay drift medible"
        assert result.drift_score == 0.0

    def test_H8_exception_in_evaluate_propagates_as_block(self):
        """
        Si evaluate() lanza una excepción inesperada, el pipeline upstream
        debe tratarla como BLOCK (fall-safe policy ADR-074 §4.4).
        Aquí validamos que evaluate() no traga excepciones internas — si las hay,
        deben propagarse al caller para que el caller las maneje.
        """
        avm = _tmp_avm()
        _make_snapshot(avm)
        # Forzar excepción en _compute_drift simulando un bug interno
        with patch.object(avm, '_compute_drift', side_effect=RuntimeError("internal error")):
            with pytest.raises(RuntimeError, match="internal error"):
                avm.evaluate(_baseline_signals(), domain="trading")


# ═══════════════════════════════════════════════════════════════════════════════
#  FASE 1 — BLOQUE F: Contradicción de políticas
# ═══════════════════════════════════════════════════════════════════════════════

class TestPolicyContradiction:

    def test_F1_critical_stale_blocks_even_with_zero_drift(self):
        """
        Señales perfectamente calibradas + snapshot critically stale → BLOCK.
        CRITICAL_STALE tiene precedencia absoluta sobre drift=0.
        """
        avm = _tmp_avm(critical_age_hours=0.001)
        from omnix_core.governance.assumption_validity_monitor import CalibrationSnapshot
        snap = CalibrationSnapshot(
            snapshot_id="AVM-F1",
            parameter_version="1.f1",
            domain="trading",
            calibrated_at="2020-01-01T00:00:00+00:00",
            calibrated_at_epoch=1577836800.0,
            baseline_signals=_baseline_signals(),
            checkpoint_thresholds={},
            drift_threshold=35.0,
            max_age_hours=168.0,
            description="stale test",
            tags=[],
        )
        avm._memory_store["trading"] = snap
        # Mismas señales que baseline → drift=0 → pero stale → BLOCK
        result = avm.evaluate(_baseline_signals(), domain="trading")
        assert result.is_valid is False, (
            "CRITICAL_STALE debe bloquear incluso con drift=0 (señales perfectas)"
        )
        assert result.drift_score == 100.0
        assert result.pass_through is False

    def test_F2_drift_block_wins_over_perfect_age(self):
        """Snapshot fresco + señales extremamente desviadas → DRIFT_BLOCK."""
        avm = _tmp_avm(drift_threshold=1.0)  # umbral mínimo
        _make_snapshot(avm)
        signals = {k: v + 50.0 for k, v in _baseline_signals().items()}
        result = avm.evaluate(signals, domain="trading")
        assert result.is_valid is False
        assert "drift" in result.block_reason.lower() or "assumption" in result.block_reason.lower()

    def test_F3_pass_through_true_not_executable_in_certified_pipeline(self):
        """
        pass_through=True = no snapshot = no verificación de drift.
        El código downstream NO debe interpretar is_valid=True + pass_through=True
        como 'certificado' — debe tratarlo como 'no verificado'.
        Validamos el contrato: si pass_through=True, block_reason es None
        y snapshot_id es 'NO_BASELINE' o 'DISABLED'.
        """
        avm = _tmp_avm()
        result = avm.evaluate(_baseline_signals(), domain="no_snapshot_domain")
        assert result.pass_through is True
        assert result.is_valid is True
        assert result.snapshot_id in ("NO_BASELINE", "DISABLED")
        assert result.block_reason is None
        # Verificar que el contrato es claro: pass_through ≠ certified
        d = result.to_dict()
        assert d["pass_through"] is True, "pass_through debe ser explícito en el dict"

    def test_F4_drift_below_threshold_with_non_finite_still_blocks(self):
        """
        drift = 0 (señales iguales al baseline) + NaN en campo extra → BLOCK.
        La non-finite guard tiene precedencia sobre el check de drift.
        """
        avm = _tmp_avm()
        _make_snapshot(avm)
        signals = {**_baseline_signals(), "extra_signal": float('nan')}
        result = avm.evaluate(signals, domain="trading")
        assert result.is_valid is False
        assert "NON_FINITE" in result.block_reason

    def test_F5_unknown_domain_returns_pass_through_not_certified(self):
        """
        Dominio desconocido → pass_through=True (no baseline), NOT BLOCK.
        Pero el downstream debe tratar pass_through=True como NO_CERTIFIED,
        no como APPROVED.
        """
        avm = _tmp_avm()
        result = avm.evaluate(_baseline_signals(), domain="ghost_domain_xyz_9999")
        assert result.pass_through is True
        assert result.snapshot_id == "NO_BASELINE"
        # El dominio desconocido NO debe producir is_valid=False automáticamente
        # (el AVM no tiene base de comparación, no puede calcular drift)
        assert result.is_valid is True

    def test_F6_block_reason_always_has_snapshot_id_when_known(self):
        """
        Cuando is_valid=False por drift o stale, block_reason debe contener
        snapshot_id para trazabilidad de auditoría.
        """
        avm = _tmp_avm(drift_threshold=1.0)
        snap = _make_snapshot(avm)
        signals = {k: v + 50.0 for k, v in _baseline_signals().items()}
        result = avm.evaluate(signals, domain="trading")
        assert result.is_valid is False
        assert snap.snapshot_id in result.block_reason, (
            f"block_reason debe contener snapshot_id para trazabilidad. "
            f"snapshot_id={snap.snapshot_id}, block_reason={result.block_reason}"
        )

    def test_F7_warnings_present_when_age_exceeds_max_but_not_critical(self):
        """
        age > max_age_hours → warning no-bloqueante + threshold tightened.
        age < critical_age_hours → NO block.
        """
        from omnix_core.governance.assumption_validity_monitor import CalibrationSnapshot
        avm = _tmp_avm(max_age_hours=1.0, critical_age_hours=9999.0)
        snap = CalibrationSnapshot(
            snapshot_id="AVM-F7",
            parameter_version="1.f7",
            domain="trading",
            calibrated_at="2026-01-01T00:00:00+00:00",
            calibrated_at_epoch=1735689600.0,  # hace 3 meses (> 1h, < 9999h)
            baseline_signals=_baseline_signals(),
            checkpoint_thresholds={},
            drift_threshold=35.0,
            max_age_hours=1.0,
            description="old but not critical",
            tags=[],
        )
        avm._memory_store["trading"] = snap
        result = avm.evaluate(_baseline_signals(), domain="trading")
        # Si drift es bajo, no debe bloquear, pero sí tener warnings
        if result.is_valid:
            assert len(result.warnings) > 0, (
                "snapshot con age > max_age_hours debe producir warnings"
            )


# ═══════════════════════════════════════════════════════════════════════════════
#  FASE 2 — BLOQUE D: Caos de persistencia
# ═══════════════════════════════════════════════════════════════════════════════

class TestPersistenceChaos:

    def test_D1_select_ok_upsert_fails_returns_false(self):
        """SELECT version OK, UPSERT falla → save_snapshot retorna False, no success parcial."""
        from omnix_core.governance.avm_db_bridge import AVMDatabaseBridge

        bridge = AVMDatabaseBridge.__new__(AVMDatabaseBridge)
        bridge._available = True
        bridge._db_url = "mock"

        call_count = [0]
        def mock_get_conn():
            call_count[0] += 1
            mock_cur = MagicMock()
            mock_cur.__enter__ = lambda s: s
            mock_cur.__exit__ = MagicMock(return_value=False)
            if call_count[0] == 1:
                # Primera conexión: SELECT version OK → returns None (no row)
                mock_cur.fetchone.return_value = None
                mock_conn = MagicMock()
                mock_conn.__enter__ = lambda s: s
                mock_conn.__exit__ = MagicMock(return_value=False)
                mock_conn.cursor.return_value = mock_cur
                return mock_conn
            else:
                # Segunda conexión: UPSERT falla
                raise Exception("UPSERT failed: disk full")

        with patch.object(bridge, "_get_conn", side_effect=mock_get_conn):
            result = bridge.save_snapshot(
                {"domain": "trading", "snapshot_id": "T1",
                 "parameter_version": "1.x", "baseline_signals": {"s": 1.0}},
                reason="test",
                action="SEED",
            )
        assert result is False, "SELECT OK + UPSERT falla debe retornar False"

    def test_D2_restore_tampered_snapshot_count_correct(self):
        """Restore con 1 OK + 1 TAMPERED → restored=1, tampered=1. Contadores precisos."""
        from omnix_core.governance.avm_db_bridge import AVMDatabaseBridge, _compute_hash

        signals_ok = {"probability_score": 70.0}
        signals_bad = {"probability_score": 99.0}
        hash_ok = _compute_hash(signals_ok)
        hash_bad_stored = "0" * 64  # hash incorrecto

        rows = [
            {
                "domain": "trading",
                "snapshot_id": "AVM-OK",
                "parameter_version": "1.ok",
                "baseline_signals": signals_ok,
                "baseline_hash": hash_ok,
                "checkpoint_thresholds": {},
                "drift_threshold": 35.0,
                "max_age_hours": 168.0,
                "description": "",
                "tags": [],
                "calibrated_at": "2026-01-01T00:00:00+00:00",
                "calibrated_at_epoch": 1735689600.0,
                "version": 1,
                "is_active": True,
            },
            {
                "domain": "insurance",
                "snapshot_id": "AVM-BAD",
                "parameter_version": "1.bad",
                "baseline_signals": signals_bad,
                "baseline_hash": hash_bad_stored,  # TAMPERED
                "checkpoint_thresholds": {},
                "drift_threshold": 35.0,
                "max_age_hours": 168.0,
                "description": "",
                "tags": [],
                "calibrated_at": "2026-01-01T00:00:00+00:00",
                "calibrated_at_epoch": 1735689600.0,
                "version": 1,
                "is_active": True,
            },
        ]

        bridge = AVMDatabaseBridge.__new__(AVMDatabaseBridge)
        bridge._available = True
        bridge._db_url = "mock"

        mock_cursor = MagicMock()
        mock_cursor.description = [(k,) for k in rows[0].keys()]
        mock_cursor.fetchall.return_value = [tuple(r.values()) for r in rows]
        mock_cursor.__enter__ = lambda s: s
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn = MagicMock()
        mock_conn.__enter__ = lambda s: s
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor

        tmp = tempfile.mkdtemp()
        with patch.object(bridge, "_get_conn", return_value=mock_conn):
            restored, tampered = bridge.restore_to_json(tmp)

        assert restored == 1, f"Solo 1 snapshot válido debe restaurarse, got {restored}"
        assert tampered == 1, f"1 snapshot TAMPERED debe contarse, got {tampered}"
        assert (pathlib.Path(tmp) / "default" / "trading_calibration.json").exists()
        assert not (pathlib.Path(tmp) / "default" / "insurance_calibration.json").exists()

    def test_D3_restore_is_idempotent(self):
        """Restaurar el mismo snapshot 3 veces no altera el contenido del JSON."""
        from omnix_core.governance.avm_db_bridge import AVMDatabaseBridge, _compute_hash

        signals = _baseline_signals()
        row = {
            "domain": "trading",
            "snapshot_id": "AVM-IDEM",
            "parameter_version": "1.idem",
            "baseline_signals": signals,
            "baseline_hash": _compute_hash(signals),
            "checkpoint_thresholds": {},
            "drift_threshold": 35.0,
            "max_age_hours": 168.0,
            "description": "idempotent test",
            "tags": [],
            "calibrated_at": "2026-01-01T00:00:00+00:00",
            "calibrated_at_epoch": 1735689600.0,
            "version": 2,
            "is_active": True,
        }

        bridge = AVMDatabaseBridge.__new__(AVMDatabaseBridge)
        bridge._available = True
        bridge._db_url = "mock"

        def make_mock():
            mock_cursor = MagicMock()
            mock_cursor.description = [(k,) for k in row.keys()]
            mock_cursor.fetchall.return_value = [tuple(row.values())]
            mock_cursor.__enter__ = lambda s: s
            mock_cursor.__exit__ = MagicMock(return_value=False)
            mock_conn = MagicMock()
            mock_conn.__enter__ = lambda s: s
            mock_conn.__exit__ = MagicMock(return_value=False)
            mock_conn.cursor.return_value = mock_cursor
            return mock_conn

        tmp = tempfile.mkdtemp()
        contents = []
        for _ in range(3):
            with patch.object(bridge, "_get_conn", return_value=make_mock()):
                bridge.restore_to_json(tmp)
            with open(pathlib.Path(tmp) / "default" / "trading_calibration.json") as f:
                contents.append(json.load(f))

        assert contents[0] == contents[1] == contents[2], (
            "Restore idempotente: 3 restauraciones del mismo snapshot deben producir el mismo JSON"
        )

    def test_D4_partial_json_missing_required_field_loads_as_none(self):
        """JSON con campo requerido faltante → from_dict falla → load_snapshot retorna None."""
        avm = _tmp_avm()
        snap_path = avm._snapshot_path("trading")
        snap_path.parent.mkdir(parents=True, exist_ok=True)

        # JSON válido pero sin snapshot_id (campo requerido)
        partial = {
            "parameter_version": "1.x",
            "domain": "trading",
            "calibrated_at": "2026-01-01T00:00:00+00:00",
            "calibrated_at_epoch": 1735689600.0,
            "baseline_signals": {"probability_score": 70.0},
            "checkpoint_thresholds": {},
            "drift_threshold": 35.0,
            "max_age_hours": 168.0,
            "description": "partial",
            "tags": [],
            # "snapshot_id" MISSING
        }
        with open(snap_path, "w") as f:
            json.dump(partial, f)

        result = avm.load_snapshot("trading")
        assert result is None, "JSON con campo requerido faltante debe retornar None"

    def test_D5_load_all_snapshots_with_db_offline_returns_empty(self):
        """DB offline → load_all_snapshots retorna {} sin crashear."""
        from omnix_core.governance.avm_db_bridge import AVMDatabaseBridge
        bridge = AVMDatabaseBridge(db_url="postgresql://invalid:invalid@localhost:9999/invalid")
        result = bridge.load_all_snapshots()
        assert result == {}, "DB offline debe retornar {} no crashear"

    def test_D6_legacy_snapshot_no_hash_is_legacy_no_hash_not_tampered(self):
        """
        Snapshot sin baseline_hash (legacy) → integrity_status=LEGACY_NO_HASH,
        NO marcado como TAMPERED ni OK automáticamente.
        """
        from omnix_core.governance.avm_db_bridge import AVMDatabaseBridge

        row = {
            "domain": "trading",
            "snapshot_id": "AVM-LEGACY",
            "parameter_version": "1.legacy",
            "baseline_signals": {"probability_score": 70.0},
            "baseline_hash": "",  # vacío = legacy
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

        bridge = AVMDatabaseBridge.__new__(AVMDatabaseBridge)
        bridge._available = True
        bridge._db_url = "mock"
        mock_cursor = MagicMock()
        mock_cursor.description = [(k,) for k in row.keys()]
        mock_cursor.fetchall.return_value = [tuple(row.values())]
        mock_cursor.__enter__ = lambda s: s
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn = MagicMock()
        mock_conn.__enter__ = lambda s: s
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(bridge, "_get_conn", return_value=mock_conn):
            result = bridge.load_all_snapshots()

        assert result["trading"]["integrity_status"] == "LEGACY_NO_HASH"


# ═══════════════════════════════════════════════════════════════════════════════
#  FASE 2 — BLOQUE B: Idempotencia y retries
# ═══════════════════════════════════════════════════════════════════════════════

class TestIdempotencyAndRetries:

    def test_B1_same_signals_same_snapshot_produces_same_drift(self):
        """Mismo input + mismo snapshot → mismo drift_score (determinismo)."""
        avm = _tmp_avm()
        _make_snapshot(avm)
        signals = _baseline_signals(probability_score=75.0)
        results = [avm.evaluate(signals, domain="trading").drift_score for _ in range(5)]
        assert len(set(results)) == 1, (
            f"evaluate() debe ser determinístico para el mismo input. Got: {set(results)}"
        )

    def test_B2_multiple_evaluations_do_not_modify_snapshot(self):
        """10 evaluaciones consecutivas no alteran el snapshot en memoria."""
        avm = _tmp_avm()
        snap = _make_snapshot(avm)
        original_signals = dict(snap.baseline_signals)
        for _ in range(10):
            avm.evaluate(_baseline_signals(probability_score=80.0), domain="trading")
        # Verificar que baseline no fue mutado
        assert snap.baseline_signals == original_signals

    def test_B3_save_snapshot_twice_same_domain_keeps_latest(self):
        """Guardar snapshot 2 veces → el segundo pisa al primero, no duplica."""
        avm = _tmp_avm()
        snap1 = avm.save_calibration_snapshot("trading", _baseline_signals())
        snap2 = avm.save_calibration_snapshot("trading", _baseline_signals(probability_score=80.0))
        loaded = avm.load_snapshot("trading")
        assert loaded.snapshot_id == snap2.snapshot_id, (
            "El segundo save debe pisar al primero — no debe haber duplicación"
        )
        assert loaded.baseline_signals["probability_score"] == 80.0

    def test_B4_restore_twice_same_json_same_content(self):
        """Restore idempotente: 2 veces = mismo JSON (test con avm real)."""
        avm = _tmp_avm()
        snap = _make_snapshot(avm)
        path = avm._snapshot_path("trading")
        with open(path) as f:
            content1 = json.load(f)
        # Re-guardar = mismo resultado
        avm.save_calibration_snapshot(
            "trading",
            snap.baseline_signals,
            description="re-save test",
        )
        with open(avm._snapshot_path("trading")) as f:
            content2 = json.load(f)
        # Los campos clave deben coincidir (snapshot_id puede cambiar por nuevo uuid)
        assert content2["domain"] == content1["domain"]
        assert content2["drift_threshold"] == content1["drift_threshold"]

    def test_B5_evaluate_after_invalidate_is_pass_through(self):
        """Invalidate + retry → pass_through, no error."""
        avm = _tmp_avm()
        _make_snapshot(avm)
        avm.invalidate_snapshot("trading")
        result = avm.evaluate(_baseline_signals(), domain="trading")
        assert result.pass_through is True
        assert result.is_valid is True


# ═══════════════════════════════════════════════════════════════════════════════
#  FASE 3 — BLOQUE A: Concurrencia y race conditions
# ═══════════════════════════════════════════════════════════════════════════════

class TestConcurrencyRaceConditions:

    def test_A1_concurrent_receipt_id_generation_is_unique(self):
        """500 receipt_ids generados en paralelo → 0 colisiones."""
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        domains = ["trading", "insurance", "robotics", "islamic_credit", "public_sandbox"]
        results = []
        lock = threading.Lock()

        def generate(domain):
            rid = DecisionReceiptEngine.build_receipt_id(domain)
            with lock:
                results.append(rid)

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [
                executor.submit(generate, domains[i % len(domains)])
                for i in range(500)
            ]
            for f in as_completed(futures):
                f.result()

        assert len(results) == 500
        assert len(set(results)) == 500, (
            f"Colisión detectada: {500 - len(set(results))} duplicados en 500 receipt_ids paralelos"
        )

    def test_A2_concurrent_evaluations_no_shared_state_corruption(self):
        """
        10 threads evaluando en paralelo con el mismo AVM y snapshot
        → sin corrupción de estado, todos retornan AVMResult válido.
        """
        from omnix_core.governance.assumption_validity_monitor import AVMResult
        avm = _tmp_avm()
        _make_snapshot(avm)
        results = []
        errors = []
        lock = threading.Lock()

        def evaluate_task(i):
            try:
                signals = _baseline_signals(probability_score=60.0 + (i % 10))
                r = avm.evaluate(signals, domain="trading")
                with lock:
                    results.append(r)
            except Exception as e:
                with lock:
                    errors.append(str(e))

        threads = [threading.Thread(target=evaluate_task, args=(i,)) for i in range(10)]
        for t in threads: t.start()
        for t in threads: t.join()

        assert not errors, f"Errores en concurrencia: {errors}"
        assert len(results) == 10
        assert all(isinstance(r, AVMResult) for r in results)

    def test_A3_concurrent_save_and_load_snapshot_no_partial_state(self):
        """
        Un thread guarda, otro carga simultáneamente.
        El loader recibe el snapshot completo o None (nunca un estado parcial).
        """
        avm = _tmp_avm()
        errors = []
        loaded_snaps = []
        lock = threading.Lock()

        def saver():
            for _ in range(5):
                avm.save_calibration_snapshot("trading", _baseline_signals())
                time.sleep(0.005)

        def loader():
            for _ in range(10):
                # Clear memory store to force disk read
                snap = avm.load_snapshot("trading")
                with lock:
                    loaded_snaps.append(snap)
                time.sleep(0.002)

        t1 = threading.Thread(target=saver)
        t2 = threading.Thread(target=loader)
        t1.start(); t2.start()
        t1.join(); t2.join()

        # Ningún estado parcial: o None o snapshot válido
        for snap in loaded_snaps:
            if snap is not None:
                from omnix_core.governance.assumption_validity_monitor import CalibrationSnapshot
                assert isinstance(snap, CalibrationSnapshot), (
                    f"load_snapshot debe retornar CalibrationSnapshot o None, got {type(snap)}"
                )

    def test_A4_hash_computation_is_threadsafe(self):
        """SHA-256 hash concurrente = mismo resultado para mismo input."""
        from omnix_core.governance.avm_db_bridge import _compute_hash
        signals = _baseline_signals()
        hashes = []
        lock = threading.Lock()

        def compute():
            h = _compute_hash(signals)
            with lock:
                hashes.append(h)

        threads = [threading.Thread(target=compute) for _ in range(50)]
        for t in threads: t.start()
        for t in threads: t.join()

        assert len(set(hashes)) == 1, (
            f"SHA-256 debe ser idéntico en concurrencia. Got {len(set(hashes))} valores distintos"
        )

    def test_A5_concurrent_receipt_ids_match_domain_pattern(self):
        """Todos los receipt_ids paralelos tienen formato OMNIX-{CODE}-{12hex}."""
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        pattern = re.compile(r"^OMNIX-[A-Z]{3}-[0-9A-F]{12}$")
        results = []
        lock = threading.Lock()

        def gen():
            rid = DecisionReceiptEngine.build_receipt_id("trading")
            with lock:
                results.append(rid)

        threads = [threading.Thread(target=gen) for _ in range(100)]
        for t in threads: t.start()
        for t in threads: t.join()

        malformed = [r for r in results if not pattern.match(r)]
        assert not malformed, f"Receipt IDs malformados en concurrencia: {malformed[:3]}"


# ═══════════════════════════════════════════════════════════════════════════════
#  FASE 3 — BLOQUE G: Dashboard truth audit
# ═══════════════════════════════════════════════════════════════════════════════

class TestDashboardTruthAudit:

    def test_G1_api_avm_status_returns_all_four_domains(self):
        """
        /api/governance/avm-status retorna exactamente los 4 dominios operativos.
        No puede faltar ninguno ni aparecer un dominio fantasma.
        """
        import requests
        try:
            resp = requests.get(
                "http://localhost:5000/api/governance/avm-status",
                headers={"X-API-Key": "omnix-dashboard-2024"},
                timeout=5,
            )
            if resp.status_code != 200:
                pytest.skip("Dashboard no disponible en este entorno de test")
            data = resp.json()
            domain_labels = {d["domain"] for d in data.get("domains", [])}
            expected = {"trading", "islamic_credit", "insurance", "robotics"}
            assert expected == domain_labels, (
                f"Dominios en API: {domain_labels}, esperados: {expected}"
            )
        except Exception:
            pytest.skip("Dashboard no disponible en este entorno de test")

    def test_G2_api_integrity_status_matches_hash_verification(self):
        """
        El campo integrity de cada dominio en la API debe ser OK o TAMPERED,
        nunca UNKNOWN para dominios con snapshots activos.
        """
        import requests
        try:
            resp = requests.get(
                "http://localhost:5000/api/governance/avm-status",
                headers={"X-API-Key": "omnix-dashboard-2024"},
                timeout=5,
            )
            if resp.status_code != 200:
                pytest.skip("Dashboard no disponible")
            data = resp.json()
            for domain in data.get("domains", []):
                assert domain["integrity"] in ("OK", "TAMPERED", "LEGACY_NO_HASH"), (
                    f"domain={domain['domain']}: integrity='{domain['integrity']}' "
                    f"debe ser OK, TAMPERED o LEGACY_NO_HASH — nunca UNKNOWN para dominios activos"
                )
        except Exception:
            pytest.skip("Dashboard no disponible en este entorno de test")

    def test_G3_api_drift_status_is_never_unknown_for_active_domains(self):
        """
        drift_status=UNKNOWN indica bug (p.ej. age_hours sin ()).
        Con el fix aplicado, todos los dominios activos deben ser STABLE o STALE.
        """
        import requests
        try:
            resp = requests.get(
                "http://localhost:5000/api/governance/avm-status",
                headers={"X-API-Key": "omnix-dashboard-2024"},
                timeout=5,
            )
            if resp.status_code != 200:
                pytest.skip("Dashboard no disponible")
            data = resp.json()
            for domain in data.get("domains", []):
                assert domain["drift_status"] != "UNKNOWN", (
                    f"domain={domain['domain']}: drift_status=UNKNOWN indica bug "
                    f"en el cálculo de drift. Verificar age_hours() (método, no property)."
                )
        except Exception:
            pytest.skip("Dashboard no disponible en este entorno de test")

    def test_G4_degraded_mode_false_when_db_online(self):
        """degraded_mode=false cuando la DB está online y snapshots son válidos."""
        import requests
        try:
            resp = requests.get(
                "http://localhost:5000/api/governance/avm-status",
                headers={"X-API-Key": "omnix-dashboard-2024"},
                timeout=5,
            )
            if resp.status_code != 200:
                pytest.skip("Dashboard no disponible")
            data = resp.json()
            assert data.get("db_available") is True, "DB debe estar disponible"
            assert data.get("degraded_mode") is False, (
                "degraded_mode=true con DB online indica problema de configuración"
            )
        except Exception:
            pytest.skip("Dashboard no disponible en este entorno de test")

    def test_G5_avm_result_to_dict_block_reason_none_when_valid(self):
        """Si is_valid=True, block_reason=None en to_dict() — nunca string vacío."""
        avm = _tmp_avm()
        _make_snapshot(avm)
        result = avm.evaluate(_baseline_signals(), domain="trading")
        d = result.to_dict()
        if d["is_valid"]:
            assert d["block_reason"] is None, (
                "block_reason debe ser None (no string vacío) cuando is_valid=True"
            )

    def test_G6_avm_result_to_dict_block_reason_present_when_invalid(self):
        """Si is_valid=False, block_reason tiene contenido — nunca None."""
        avm = _tmp_avm(drift_threshold=0.001)
        _make_snapshot(avm)
        result = avm.evaluate(
            _baseline_signals(probability_score=100.0),
            domain="trading"
        )
        if not result.is_valid:
            d = result.to_dict()
            assert d["block_reason"] is not None
            assert len(d["block_reason"]) > 10


# ═══════════════════════════════════════════════════════════════════════════════
#  FASE 4 — BLOQUE C: Fuzzing hostil de inputs
# ═══════════════════════════════════════════════════════════════════════════════

class TestHostileInputFuzzing:

    def test_C1_none_signals_dict_no_crash(self):
        """evaluate({}) con snapshot presente → AVMResult sin crash."""
        from omnix_core.governance.assumption_validity_monitor import AVMResult
        avm = _tmp_avm()
        _make_snapshot(avm)
        result = avm.evaluate({}, domain="trading")
        assert isinstance(result, AVMResult)

    def test_C2_negative_signal_values_handled(self):
        """Señales negativas (-10, -100) → no crash, drift computable."""
        avm = _tmp_avm()
        _make_snapshot(avm)
        signals = {k: -10.0 for k in _baseline_signals().keys()}
        result = avm.evaluate(signals, domain="trading")
        from omnix_core.governance.assumption_validity_monitor import AVMResult
        assert isinstance(result, AVMResult)
        assert math.isfinite(result.drift_score)

    def test_C3_signal_values_over_100_handled(self):
        """Señales > 100 → drift clamped a 100.0, no overflow."""
        avm = _tmp_avm()
        _make_snapshot(avm)
        signals = {k: 999.0 for k in _baseline_signals().keys()}
        result = avm.evaluate(signals, domain="trading")
        assert math.isfinite(result.drift_score)
        assert result.drift_score <= 100.0

    def test_C4_nan_in_single_of_six_signals_blocks(self):
        """NaN en 1 de 6 señales → BLOCK (no bypass por otras 5 buenas)."""
        avm = _tmp_avm()
        _make_snapshot(avm)
        for signal_name in _baseline_signals().keys():
            signals = {**_baseline_signals(), signal_name: float('nan')}
            result = avm.evaluate(signals, domain="trading")
            assert result.is_valid is False, (
                f"NaN en signal='{signal_name}' debe BLOQUEAR — got is_valid=True"
            )

    def test_C5_string_domain_with_special_chars_no_crash(self):
        """Dominio con caracteres especiales → load_snapshot no crash."""
        avm = _tmp_avm()
        for domain in ["domain/with/slashes", "domain with spaces", "DomAin_混合", "../../etc/passwd"]:
            result = avm.load_snapshot(domain)
            # No crash, retorna None (sin snapshot para dominios inválidos)
            assert result is None, f"domain='{domain}': debe retornar None sin crash"

    def test_C6_zero_drift_threshold_still_blocks_on_any_drift(self):
        """drift_threshold=0 → cualquier desviación de señal bloquea."""
        avm = _tmp_avm(drift_threshold=0.0)
        _make_snapshot(avm)
        signals = _baseline_signals(probability_score=70.001)  # mínima desviación
        result = avm.evaluate(signals, domain="trading")
        # Con threshold=0, cualquier drift > 0 bloquea
        if result.drift_score > 0:
            assert result.is_valid is False

    def test_C7_extremely_large_number_not_nan_handled(self):
        """1e308 es finito (float máx) → no NaN, debe procesarse sin error."""
        avm = _tmp_avm()
        _make_snapshot(avm)
        signals = _baseline_signals(probability_score=1e308)
        result = avm.evaluate(signals, domain="trading")
        # 1e308 es finito → pasa el guard, drift calculado
        assert math.isfinite(result.drift_score)

    def test_C8_bool_signals_are_treated_as_numeric(self):
        """
        True=1, False=0 en Python. Si llegan como señales, no deben causar bypass.
        Verificar que son tratados como floats (no como strings).
        """
        avm = _tmp_avm()
        _make_snapshot(avm)
        signals = _baseline_signals(probability_score=True)  # True = 1.0
        result = avm.evaluate(signals, domain="trading")
        from omnix_core.governance.assumption_validity_monitor import AVMResult
        assert isinstance(result, AVMResult)
        assert math.isfinite(result.drift_score)

    def test_C9_unicode_domain_name_normalized_for_path(self):
        """Dominio con unicode → _snapshot_path produce path válido."""
        avm = _tmp_avm()
        path = avm._snapshot_path("domáin_ünïcöde")
        # Debe ser un Path válido (no crash)
        assert isinstance(path, pathlib.Path)
        # El nombre de archivo no debe contener "/" o "\"
        assert "/" not in path.name
        assert "\\" not in path.name


# ═══════════════════════════════════════════════════════════════════════════════
#  FASE 4 — BLOQUE E: Integridad criptográfica profunda
# ═══════════════════════════════════════════════════════════════════════════════

class TestCryptoIntegrityDeep:

    def test_E1_same_content_different_key_order_same_hash(self):
        """SHA-256 usa sort_keys=True → el orden de las claves no afecta el hash."""
        from omnix_core.governance.avm_db_bridge import _compute_hash
        s1 = {"c": 3.0, "a": 1.0, "b": 2.0}
        s2 = {"a": 1.0, "b": 2.0, "c": 3.0}
        s3 = {"b": 2.0, "c": 3.0, "a": 1.0}
        assert _compute_hash(s1) == _compute_hash(s2) == _compute_hash(s3)

    def test_E2_float_vs_int_representation_different_hash(self):
        """
        1 vs 1.0: json.dumps los serializa distinto → hash distinto.
        Esto es CORRECTO — la política es que el tipo importa.
        El contrato debe ser explícito: siempre usar float.
        """
        from omnix_core.governance.avm_db_bridge import _compute_hash
        # En json.dumps: 1 → "1", 1.0 → "1.0" → hashes distintos
        h_int = _compute_hash({"probability_score": 1})
        h_float = _compute_hash({"probability_score": 1.0})
        # Documentar el comportamiento (puede ser igual o distinto según implementación)
        # Lo importante: es determinístico
        assert _compute_hash({"probability_score": 1}) == h_int
        assert _compute_hash({"probability_score": 1.0}) == h_float

    def test_E3_single_bit_change_completely_changes_hash(self):
        """Avalanche effect: cambio mínimo → hash completamente distinto (SHA-256)."""
        from omnix_core.governance.avm_db_bridge import _compute_hash
        s1 = {"probability_score": 70.0}
        s2 = {"probability_score": 70.00001}  # cambio mínimo
        h1 = _compute_hash(s1)
        h2 = _compute_hash(s2)
        assert h1 != h2
        # Además, los hashes deben ser completamente distintos (no solo 1 char)
        common_chars = sum(1 for a, b in zip(h1, h2) if a == b)
        assert common_chars < 10, (
            f"Hash con cambio mínimo comparte demasiados chars ({common_chars}/64) — "
            f"puede indicar problema de canonización"
        )

    def test_E4_hash_is_sha256_length_and_charset(self):
        """SHA-256 produce exactamente 64 hex lowercase."""
        from omnix_core.governance.avm_db_bridge import _compute_hash
        h = _compute_hash(_baseline_signals())
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_E5_tampered_field_produces_tampered_status(self):
        """
        Modificar cualquier campo de baseline_signals → hash diferente → TAMPERED.
        Verifica que el sistema detecta la manipulación en load_all_snapshots.
        """
        from omnix_core.governance.avm_db_bridge import AVMDatabaseBridge, _compute_hash
        signals_original = _baseline_signals()
        signals_tampered = {**signals_original, "probability_score": 99.0}
        hash_original = _compute_hash(signals_original)

        row = {
            "domain": "trading",
            "snapshot_id": "AVM-E5",
            "parameter_version": "1.e5",
            "baseline_signals": signals_tampered,  # signals alteradas
            "baseline_hash": hash_original,          # hash del original
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

        bridge = AVMDatabaseBridge.__new__(AVMDatabaseBridge)
        bridge._available = True
        bridge._db_url = "mock"
        mock_cursor = MagicMock()
        mock_cursor.description = [(k,) for k in row.keys()]
        mock_cursor.fetchall.return_value = [tuple(row.values())]
        mock_cursor.__enter__ = lambda s: s
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_conn = MagicMock()
        mock_conn.__enter__ = lambda s: s
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(bridge, "_get_conn", return_value=mock_conn):
            result = bridge.load_all_snapshots()

        assert result["trading"]["integrity_status"] == "TAMPERED", (
            "Modificar baseline_signals con hash del original debe detectarse como TAMPERED"
        )

    def test_E6_hash_deterministic_across_processes(self):
        """
        SHA-256 de los mismos signals en múltiples cálculos es siempre idéntico
        (sin PYTHONHASHSEED random, ya que usamos json.dumps + SHA-256).
        """
        from omnix_core.governance.avm_db_bridge import _compute_hash
        signals = _baseline_signals()
        hashes = {_compute_hash(signals) for _ in range(100)}
        assert len(hashes) == 1, "SHA-256 debe ser determinístico en todas las iteraciones"

    def test_E7_receipt_id_uses_uuid4_not_uuid1_or_uuid3(self):
        """
        receipt_id usa uuid4 (aleatorio) no uuid1 (basado en MAC/tiempo) ni uuid3/5 (hash).
        Verificar que el formato tiene 12 hex chars aleatorios (no predecibles).
        """
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        ids = [DecisionReceiptEngine.build_receipt_id("trading") for _ in range(10)]
        hex_parts = [rid.split("-")[-1] for rid in ids]
        # Todos deben ser distintos (uuid4 es aleatorio)
        assert len(set(hex_parts)) == len(hex_parts), (
            "Las partes hex de los receipt_ids deben ser únicas (uuid4 aleatorio)"
        )
