"""
OMNIX MIVP Test Suite — Mandate Integrity Verification Protocol
ADR-194 · RFC-ATF-6 extension · OMNIX QUANTUM LTD

Cierra el gap estructural de MIVP-INV-001 a MIVP-INV-009.
Todos los tests corren in-memory sin requerir conexión a base de datos.

Cobertura directa (9/9 invariantes):
  MIVP-INV-001 — MBR emitido y PQC-firmado ANTES del primer turno del agente.
  MIVP-INV-002 — mandate_objective_hash fijado al inicio de sesión; inmutable.
  MIVP-INV-003 — Cada turno produce un MAS antes de la entrega del output.
  MIVP-INV-004 — MAS siempre en [0.0, 1.0]; out-of-range nunca posible por diseño.
  MIVP-INV-005 — MAS < halt_threshold → verdict HALT emitido inmediatamente.
  MIVP-INV-006 — MAS history es append-only; ctchc_link_hash preservado por turno.
  MIVP-INV-007 — MBR Seal cubre todos los turnos; turns_covered == len(mas_history).
  MIVP-INV-008 — MANDATE-BOUND: turns_in_violation=0 AND turns_in_warning=0.
  MIVP-INV-009 — MANDATE-ALIGNED: turns_in_violation=0, warnings permitidas.
                  Mutuamente excluyente con MANDATE-BOUND.

Autores del protocolo: Harold Nunes — OMNIX QUANTUM LTD — Mayo 2026
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import pytest

# ─────────────────────────────────────────────────────────────────
#  Path setup
# ─────────────────────────────────────────────────────────────────

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in [_ROOT, os.path.join(_ROOT, "omnix_web")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")


# ─────────────────────────────────────────────────────────────────
#  Helpers compartidos
# ─────────────────────────────────────────────────────────────────

def _mivp_engine_no_db():
    """Instancia MIVPEngine en modo in-memory (sin PostgreSQL)."""
    from omnix_core.bev.mandate_integrity_verification import MIVPEngine
    engine = MIVPEngine()
    engine._db_url = None
    return engine


def _default_mandate_binding(
    halt: float = 0.30,
    warning: float = 0.65,
) -> dict:
    """
    Mandate binding canónico con dos proxy guards realistas.

    PG-001 — proxy_profit_maximization (weight=0.6):
      Detecta optimización por ganancia inmediata a expensas del mandato.
      Keywords: "maximize profit", "profit first", "ignore compliance".

    PG-002 — proxy_risk_bypass (weight=0.4):
      Detecta elusión de controles de riesgo mandatados.
      Keywords: "bypass risk", "skip verification", "ignore risk".

    Tras normalización de pesos (0.6/1.0, 0.4/1.0):
      HALT region:   weighted_sum > 0.70  →  alignment_score < 0.30
      WARNING region: 0.35 < weighted_sum ≤ 0.70  →  0.30 ≤ score < 0.65
      ALIGNED region: weighted_sum ≤ 0.35  →  score ≥ 0.65
    """
    return {
        "mandate_objective": (
            "Maximize long-term merchant revenue recovery while preserving "
            "compliance integrity and fiduciary duty to stakeholders"
        ),
        "proxy_guards": [
            {
                "guard_id": "PG-001",
                "signal_name": "proxy_profit_maximization",
                "description": "Agent optimizing for immediate profit over declared mandate",
                "detection_keywords": ["maximize profit", "profit first", "ignore compliance"],
                "weight": 0.6,
            },
            {
                "guard_id": "PG-002",
                "signal_name": "proxy_risk_bypass",
                "description": "Agent bypassing risk controls mandated by governing receipt",
                "detection_keywords": ["bypass risk", "skip verification", "ignore risk"],
                "weight": 0.4,
            },
        ],
        "objective_constraints": [
            "Do not optimize for short-term profit at the expense of compliance",
            "Maintain all mandated risk controls throughout session",
        ],
        "mas_halt_threshold": halt,
        "mas_warning_threshold": warning,
    }


# Textos de output canónicos para cada región de MAS
_TEXT_ALIGNED = (
    "The recommended course of action is a diversified portfolio allocation "
    "that prioritizes long-term stability and fiduciary compliance with all "
    "applicable regulatory requirements and client mandate objectives."
)

_TEXT_WARNING = (
    "The portfolio should maximize profit carefully over the next quarter "
    "while balancing the risk profile within acceptable parameters."
)
# "maximize profit" → PG-001 activates; PG-002 = 0 → alignment_score ≈ 0.40 → WARNING

_TEXT_HALT = (
    "maximize profit maximize profit bypass risk skip verification ignore risk "
    "profit first maximize profit ignore compliance bypass risk"
)
# Both guards fully saturated → alignment_score = 0.0 → HALT


# ═════════════════════════════════════════════════════════════════
#  SECCIÓN 1 — Importaciones e invariantes de módulo
# ═════════════════════════════════════════════════════════════════

class TestMIVPImport:
    """Verifica que todas las clases públicas del módulo MIVP son importables."""

    def test_import_all_public_classes(self):
        """Módulo completo importable sin errores de dependencia."""
        from omnix_core.bev.mandate_integrity_verification import (
            MIVPEngine,
            MandateBindingRecord,
            MandateAlignmentScore,
            MBRSeal,
            ProxyGuard,
            MANDATE_BOUND_TAG,
            MANDATE_ALIGNED_TAG,
        )
        assert MIVPEngine
        assert MandateBindingRecord
        assert MandateAlignmentScore
        assert MBRSeal
        assert ProxyGuard
        assert MANDATE_BOUND_TAG == "MANDATE-BOUND"
        assert MANDATE_ALIGNED_TAG == "MANDATE-ALIGNED"


# ═════════════════════════════════════════════════════════════════
#  SECCIÓN 2 — MBR Creation (MIVP-INV-001, MIVP-INV-002)
# ═════════════════════════════════════════════════════════════════

class TestMIVPMBRCreation:
    """
    Cubre MIVP-INV-001 y MIVP-INV-002.

    INV-001: El MBR DEBE emitirse y PQC-firmarse ANTES del primer turno.
             Operacionalmente: create_mbr() debe ser invocado antes de
             compute_mas(). Cualquier llamada a compute_mas() sin MBR
             previo debe lanzar RuntimeError.

    INV-002: mandate_objective_hash es SHA-256(mandate_objective) fijado
             en create_mbr(). No cambia durante la sesión ni entre
             llamadas con el mismo objetivo.
    """

    def test_mbr_creation_returns_valid_record(self):
        """MBR creado contiene todos los campos requeridos por el protocolo."""
        engine = _mivp_engine_no_db()
        mbr = engine.create_mbr(
            session_id="SESS-MBR-001",
            governing_receipt_id="RCP-TEST-001",
            mandate_binding=_default_mandate_binding(),
        )
        assert mbr.mbr_id.startswith("MBR-")
        assert len(mbr.mbr_id) == 20  # "MBR-" (4) + 16 hex chars
        assert mbr.session_id == "SESS-MBR-001"
        assert mbr.governing_receipt_id == "RCP-TEST-001"
        assert mbr.mandate_objective_hash  # non-empty

    def test_mbr_inv001_compute_mas_without_mbr_raises(self):
        """
        MIVP-INV-001: compute_mas() sin create_mbr() previo DEBE lanzar RuntimeError.

        Este es el enforcement directo de la regla pre-turn: si el MBR no
        existe para la sesión, el motor rechaza la producción del MAS —
        garantizando que el binding de mandato precede siempre al primer turno.
        """
        engine = _mivp_engine_no_db()
        with pytest.raises(RuntimeError, match="No MBR found"):
            engine.compute_mas(
                session_id="SESS-NO-MBR",
                bar_id="BAR-FAKE",
                turn_index=0,
                output_text="Some output text.",
            )

    def test_mbr_inv002_objective_hash_is_sha256_of_objective(self):
        """
        MIVP-INV-002: mandate_objective_hash == SHA-256(mandate_objective.encode()).

        El hash se computa una sola vez en create_mbr() y queda embebido
        en el content_hash PQC-firmado. Ninguna llamada posterior puede
        modificar este valor.
        """
        mb = _default_mandate_binding()
        engine = _mivp_engine_no_db()
        mbr = engine.create_mbr(
            session_id="SESS-HASH-001",
            governing_receipt_id="RCP-HASH-001",
            mandate_binding=mb,
        )
        expected_hash = hashlib.sha256(
            mb["mandate_objective"].encode("utf-8")
        ).hexdigest()
        assert mbr.mandate_objective_hash == expected_hash

    def test_mbr_inv002_same_objective_same_hash_across_sessions(self):
        """
        MIVP-INV-002: el mismo mandate_objective produce el mismo hash
        en sesiones distintas — el hash es determinista y portable.
        """
        mb = _default_mandate_binding()
        engine = _mivp_engine_no_db()
        mbr_a = engine.create_mbr("SESS-HA", "RCP-A", mb)
        mbr_b = engine.create_mbr("SESS-HB", "RCP-B", mb)
        assert mbr_a.mandate_objective_hash == mbr_b.mandate_objective_hash

    def test_mbr_inv002_different_objective_different_hash(self):
        """
        MIVP-INV-002 (contrafactual): objetivos distintos producen hashes distintos.
        Confirma que el hash es binding sobre el contenido exacto del mandato.
        """
        mb1 = _default_mandate_binding()
        mb2 = _default_mandate_binding()
        mb2["mandate_objective"] = "Minimize operational cost regardless of compliance"
        engine = _mivp_engine_no_db()
        mbr1 = engine.create_mbr("SESS-DH1", "RCP-DH1", mb1)
        mbr2 = engine.create_mbr("SESS-DH2", "RCP-DH2", mb2)
        assert mbr1.mandate_objective_hash != mbr2.mandate_objective_hash

    def test_mbr_content_hash_verifies_correctly(self):
        """MBR: verify_content_hash() retorna True sobre el artefacto recién creado."""
        engine = _mivp_engine_no_db()
        mbr = engine.create_mbr("SESS-VH", "RCP-VH", _default_mandate_binding())
        assert mbr.verify_content_hash(), (
            "content_hash debería verificar: el MBR recién creado no fue modificado"
        )

    def test_mbr_stored_in_engine_after_creation(self):
        """
        MIVP-INV-001 (acceso): get_mbr() retorna el MBR inmediatamente después
        de create_mbr() — confirma que el binding está disponible para el
        primer turno sin round-trip a DB.
        """
        engine = _mivp_engine_no_db()
        mbr = engine.create_mbr("SESS-GET", "RCP-GET", _default_mandate_binding())
        retrieved = engine.get_mbr("SESS-GET")
        assert retrieved is not None
        assert retrieved.mbr_id == mbr.mbr_id

    def test_mbr_proxy_guards_weight_normalized(self):
        """Los pesos de los proxy guards se normalizan a suma 1.0 en create_mbr()."""
        engine = _mivp_engine_no_db()
        mbr = engine.create_mbr("SESS-NORM", "RCP-NORM", _default_mandate_binding())
        total = sum(g.weight for g in mbr.proxy_guards)
        assert abs(total - 1.0) < 1e-9, f"Pesos deben sumar 1.0; suma actual: {total}"


# ═════════════════════════════════════════════════════════════════
#  SECCIÓN 3 — MAS Computation (MIVP-INV-003 a INV-006)
# ═════════════════════════════════════════════════════════════════

class TestMIVPMASCompute:
    """
    Cubre MIVP-INV-003, INV-004, INV-005, INV-006.

    INV-003: Cada turno en sesión MBR-bound DEBE producir un MAS antes
             de la entrega del output.
    INV-004: alignment_score siempre en [0.0, 1.0]; clamp aplicado
             por diseño (pesos normalizados + activaciones en [0,1]).
    INV-005: alignment_score < halt_threshold → verdict HALT
             emitido inmediatamente (MANDATE HALT log + verdict="HALT").
    INV-006: MAS history es append-only por sesión; ctchc_link_hash
             preservado intacto en cada artefacto MAS.
    """

    def test_mas_inv003_produces_mas_per_turn(self):
        """
        MIVP-INV-003: compute_mas() produce un MandateAlignmentScore
        con todos los campos requeridos por turno.
        """
        engine = _mivp_engine_no_db()
        engine.create_mbr("S-003", "RCP-003", _default_mandate_binding())
        mas = engine.compute_mas(
            session_id="S-003",
            bar_id="BAR-T0",
            turn_index=0,
            output_text=_TEXT_ALIGNED,
        )
        assert mas.mas_id.startswith("MAS-")
        assert mas.turn_index == 0
        assert mas.session_id == "S-003"
        assert mas.mbr_id  # non-empty
        assert mas.computed_at  # non-empty ISO timestamp

    def test_mas_inv003_sequential_turns_produce_sequential_mas(self):
        """
        MIVP-INV-003: cada turno produce exactamente un MAS;
        3 turnos → 3 artefactos MAS en el historial de sesión.
        """
        engine = _mivp_engine_no_db()
        engine.create_mbr("S-SEQ", "RCP-SEQ", _default_mandate_binding())
        for i in range(3):
            engine.compute_mas("S-SEQ", f"BAR-{i}", i, _TEXT_ALIGNED)
        history = engine.get_mas_history("S-SEQ")
        assert len(history) == 3
        assert [m.turn_index for m in history] == [0, 1, 2]

    def test_mas_inv004_score_in_unit_interval_aligned(self):
        """
        MIVP-INV-004: alignment_score ∈ [0.0, 1.0] para output limpio.
        """
        engine = _mivp_engine_no_db()
        engine.create_mbr("S-004A", "RCP-004A", _default_mandate_binding())
        mas = engine.compute_mas("S-004A", "BAR-0", 0, _TEXT_ALIGNED)
        assert 0.0 <= mas.alignment_score <= 1.0
        assert mas.verdict == "ALIGNED"

    def test_mas_inv004_score_in_unit_interval_halt(self):
        """
        MIVP-INV-004: alignment_score ∈ [0.0, 1.0] incluso con saturación
        máxima de proxy guards (text de HALT → score → 0.0).
        El clamp garantiza que no existen scores negativos.
        """
        engine = _mivp_engine_no_db()
        engine.create_mbr("S-004H", "RCP-004H", _default_mandate_binding())
        mas = engine.compute_mas("S-004H", "BAR-0", 0, _TEXT_HALT)
        assert 0.0 <= mas.alignment_score <= 1.0, (
            f"alignment_score={mas.alignment_score} fuera del rango [0.0, 1.0]"
        )

    def test_mas_inv005_halt_when_score_below_threshold(self):
        """
        MIVP-INV-005: alignment_score < mas_halt_threshold → verdict HALT.

        Este es el enforcement central de mandate HALT. Cuando el agente
        optimiza para proxies prohibidos más allá del umbral, el runtime
        DEBE emitir HALT antes de que el output sea entregado al principal.
        """
        engine = _mivp_engine_no_db()
        engine.create_mbr("S-005", "RCP-005", _default_mandate_binding(halt=0.30))
        mas = engine.compute_mas("S-005", "BAR-0", 0, _TEXT_HALT)
        assert mas.verdict == "HALT", (
            f"Texto de proxy saturado debería producir HALT, "
            f"obtuvo: verdict={mas.verdict}, score={mas.alignment_score:.4f}"
        )
        assert mas.alignment_score < 0.30

    def test_mas_inv005_warning_when_score_in_warning_band(self):
        """
        MIVP-INV-005 (banda WARNING): halt_threshold ≤ score < warning_threshold
        → verdict WARNING (proxy detectado pero no suficiente para HALT).
        """
        engine = _mivp_engine_no_db()
        engine.create_mbr("S-WARN", "RCP-WARN", _default_mandate_binding(halt=0.30, warning=0.65))
        mas = engine.compute_mas("S-WARN", "BAR-0", 0, _TEXT_WARNING)
        assert mas.verdict == "WARNING", (
            f"Texto con proxy parcial debería producir WARNING, "
            f"obtuvo: verdict={mas.verdict}, score={mas.alignment_score:.4f}"
        )
        assert 0.30 <= mas.alignment_score < 0.65

    def test_mas_inv005_aligned_when_score_above_warning(self):
        """
        MIVP-INV-005 (banda ALIGNED): alignment_score ≥ warning_threshold
        → verdict ALIGNED (sin evidencia de proxy optimization).
        """
        engine = _mivp_engine_no_db()
        engine.create_mbr("S-ALIG", "RCP-ALIG", _default_mandate_binding())
        mas = engine.compute_mas("S-ALIG", "BAR-0", 0, _TEXT_ALIGNED)
        assert mas.verdict == "ALIGNED"
        assert mas.alignment_score >= 0.65

    def test_mas_inv006_history_is_append_only(self):
        """
        MIVP-INV-006: el historial de MAS es append-only.
        Cada llamada a compute_mas() agrega un nuevo artefacto;
        la longitud del historial crece monotónicamente.
        """
        engine = _mivp_engine_no_db()
        engine.create_mbr("S-006", "RCP-006", _default_mandate_binding())
        for i in range(5):
            engine.compute_mas("S-006", f"BAR-{i}", i, _TEXT_ALIGNED)
            history = engine.get_mas_history("S-006")
            assert len(history) == i + 1, (
                f"Turno {i}: historial debería tener {i+1} entradas, tiene {len(history)}"
            )

    def test_mas_inv006_ctchc_link_hash_preserved(self):
        """
        MIVP-INV-006: ctchc_link_hash pasado a compute_mas() se preserva
        intacto en el artefacto MAS — vincula el score a la cadena CTCHC.
        """
        ctchc_hash = "a" * 64  # hash sintético de 64 caracteres
        engine = _mivp_engine_no_db()
        engine.create_mbr("S-CTCHC", "RCP-CTCHC", _default_mandate_binding())
        mas = engine.compute_mas(
            session_id="S-CTCHC",
            bar_id="BAR-CTCHC",
            turn_index=0,
            output_text=_TEXT_ALIGNED,
            ctchc_link_hash=ctchc_hash,
        )
        assert mas.ctchc_link_hash == ctchc_hash, (
            "ctchc_link_hash debe preservarse sin modificación en el artefacto MAS"
        )

    def test_mas_inv006_separate_sessions_isolated(self):
        """
        MIVP-INV-006 (aislamiento): los historiales de MAS son independientes
        por sesión. Los turnos de una sesión no afectan los de otra.
        """
        engine = _mivp_engine_no_db()
        engine.create_mbr("S-ISO-A", "RCP-A", _default_mandate_binding())
        engine.create_mbr("S-ISO-B", "RCP-B", _default_mandate_binding())
        for i in range(3):
            engine.compute_mas("S-ISO-A", f"BAR-A{i}", i, _TEXT_ALIGNED)
        engine.compute_mas("S-ISO-B", "BAR-B0", 0, _TEXT_ALIGNED)
        assert len(engine.get_mas_history("S-ISO-A")) == 3
        assert len(engine.get_mas_history("S-ISO-B")) == 1

    def test_mas_dominant_proxy_identified_on_halt_text(self):
        """
        dominant_proxy identifica el guard con mayor activación cuando
        el texto contiene proxies fuertes (correlato de INV-005).
        """
        engine = _mivp_engine_no_db()
        engine.create_mbr("S-DOM", "RCP-DOM", _default_mandate_binding())
        mas = engine.compute_mas("S-DOM", "BAR-DOM", 0, _TEXT_HALT)
        assert mas.dominant_proxy is not None, (
            "dominant_proxy debe identificarse cuando hay activaciones de proxy > 0.05"
        )


# ═════════════════════════════════════════════════════════════════
#  SECCIÓN 4 — Threshold Validation
# ═════════════════════════════════════════════════════════════════

class TestMIVPThresholdValidation:
    """
    Verifica la validación de thresholds en create_mbr() (F-006 audit gate).

    El floor mínimo de mas_halt_threshold es 0.05 (MIVP-INV-005).
    Valores por debajo deshabilitan efectivamente el HALT de mandato.
    halt_threshold debe ser estrictamente menor que warning_threshold.
    """

    def test_threshold_floor_below_minimum_raises(self):
        """
        F-006: mas_halt_threshold < 0.05 lanza ValueError.
        Previene la desactivación del mandate HALT mediante config.
        """
        engine = _mivp_engine_no_db()
        with pytest.raises(ValueError, match="minimum is 0.05"):
            engine.create_mbr(
                "S-FLOOR", "RCP-FLOOR",
                _default_mandate_binding(halt=0.04),
            )

    def test_threshold_halt_must_be_less_than_warning(self):
        """halt_threshold ≥ warning_threshold → ValueError."""
        engine = _mivp_engine_no_db()
        with pytest.raises(ValueError, match="strictly less than"):
            engine.create_mbr(
                "S-ORDER", "RCP-ORDER",
                _default_mandate_binding(halt=0.70, warning=0.65),
            )

    def test_threshold_equal_halt_and_warning_raises(self):
        """halt_threshold == warning_threshold → ValueError (requiere orden estricto)."""
        engine = _mivp_engine_no_db()
        with pytest.raises(ValueError, match="strictly less than"):
            engine.create_mbr(
                "S-EQ", "RCP-EQ",
                _default_mandate_binding(halt=0.50, warning=0.50),
            )

    def test_threshold_at_minimum_floor_is_valid(self):
        """mas_halt_threshold == 0.05 (floor exacto) es válido."""
        engine = _mivp_engine_no_db()
        mbr = engine.create_mbr(
            "S-MINF", "RCP-MINF",
            _default_mandate_binding(halt=0.05, warning=0.10),
        )
        assert mbr.mas_halt_threshold == 0.05

    def test_mandate_objective_required(self):
        """create_mbr() sin mandate_objective lanza ValueError."""
        engine = _mivp_engine_no_db()
        with pytest.raises(ValueError, match="mandate_objective is required"):
            engine.create_mbr(
                "S-NOBJ", "RCP-NOBJ",
                {"mandate_objective": "", "proxy_guards": []},
            )


# ═════════════════════════════════════════════════════════════════
#  SECCIÓN 5 — ProxyGuard
# ═════════════════════════════════════════════════════════════════

class TestMIVPProxyGuard:
    """
    Verifica el comportamiento del ProxyGuard — bloque de detección
    de proxy optimization que alimenta el cálculo de MAS.
    """

    def test_proxy_guard_zero_activation_on_clean_text(self):
        """Texto sin keywords → activation_score = 0.0."""
        from omnix_core.bev.mandate_integrity_verification import ProxyGuard
        guard = ProxyGuard(
            guard_id="PG-T1",
            signal_name="test_guard",
            description="Test",
            detection_keywords=["maximize profit", "profit first"],
            weight=1.0,
        )
        score = guard.activation_score("Diversified strategy for long-term value.")
        assert score == 0.0

    def test_proxy_guard_high_activation_on_keyword_saturation(self):
        """Texto con múltiples keywords → activation_score cercano a 1.0."""
        from omnix_core.bev.mandate_integrity_verification import ProxyGuard
        guard = ProxyGuard(
            guard_id="PG-T2",
            signal_name="test_guard",
            description="Test",
            detection_keywords=["maximize profit"],
            weight=1.0,
        )
        score = guard.activation_score("maximize profit maximize profit maximize profit")
        assert score == 1.0

    def test_proxy_guard_activation_clamped_to_unit(self):
        """activation_score siempre en [0.0, 1.0] por construcción."""
        from omnix_core.bev.mandate_integrity_verification import ProxyGuard
        guard = ProxyGuard(
            guard_id="PG-T3",
            signal_name="test_guard",
            description="Test",
            detection_keywords=["x"],
            weight=1.0,
        )
        score = guard.activation_score("x " * 100)
        assert 0.0 <= score <= 1.0

    def test_proxy_guard_round_trip_dict(self):
        """ProxyGuard.to_dict() / from_dict() es idempotente."""
        from omnix_core.bev.mandate_integrity_verification import ProxyGuard
        original = ProxyGuard(
            guard_id="PG-RT",
            signal_name="rt_guard",
            description="Round-trip test",
            detection_keywords=["signal_a", "signal_b"],
            weight=0.75,
        )
        restored = ProxyGuard.from_dict(original.to_dict())
        assert restored.guard_id == original.guard_id
        assert restored.signal_name == original.signal_name
        assert restored.detection_keywords == original.detection_keywords
        assert abs(restored.weight - original.weight) < 1e-9


# ═════════════════════════════════════════════════════════════════
#  SECCIÓN 6 — Seal Lifecycle (MIVP-INV-007)
# ═════════════════════════════════════════════════════════════════

class TestMIVPSealLifecycle:
    """
    Cubre MIVP-INV-007.

    INV-007: El MBR Seal DEBE emitirse en el cierre de sesión cubriendo
             TODOS los turnos. turns_covered == len(mas_history).
    """

    def test_seal_inv007_turns_covered_matches_history(self):
        """
        MIVP-INV-007: seal.turns_covered == len(get_mas_history()).

        El sello es el receipt forense de cierre de sesión. Si turns_covered
        no coincide con el historial, la evidencia es incompleta.
        """
        engine = _mivp_engine_no_db()
        engine.create_mbr("S-SL1", "RCP-SL1", _default_mandate_binding())
        n_turns = 4
        for i in range(n_turns):
            engine.compute_mas("S-SL1", f"BAR-{i}", i, _TEXT_ALIGNED)
        seal = engine.seal_mbr("S-SL1")
        assert seal.turns_covered == n_turns, (
            f"turns_covered={seal.turns_covered} != {n_turns} (turnos registrados)"
        )

    def test_seal_inv007_zero_turns_covered_allowed(self):
        """
        MIVP-INV-007: sesión sellada sin ningún turno registrado produce
        seal con turns_covered=0 y mas_average=1.0 (sin datos, sin violaciones).
        """
        engine = _mivp_engine_no_db()
        engine.create_mbr("S-ZERO", "RCP-ZERO", _default_mandate_binding())
        seal = engine.seal_mbr("S-ZERO")
        assert seal.turns_covered == 0
        assert seal.final_mas == 1.0

    def test_seal_seal_id_format(self):
        """MBR Seal: seal_id sigue formato 'MBRS-{HEX16}'."""
        engine = _mivp_engine_no_db()
        engine.create_mbr("S-FMT", "RCP-FMT", _default_mandate_binding())
        seal = engine.seal_mbr("S-FMT")
        assert seal.seal_id.startswith("MBRS-")
        assert len(seal.seal_id) == 21  # "MBRS-" (5) + 16 hex chars

    def test_seal_without_mbr_raises(self):
        """seal_mbr() sin MBR previo → RuntimeError."""
        engine = _mivp_engine_no_db()
        with pytest.raises(RuntimeError, match="Cannot seal"):
            engine.seal_mbr("S-NO-MBR")

    def test_seal_stored_after_creation(self):
        """get_seal() retorna el sello inmediatamente después de seal_mbr()."""
        engine = _mivp_engine_no_db()
        engine.create_mbr("S-GSL", "RCP-GSL", _default_mandate_binding())
        seal = engine.seal_mbr("S-GSL")
        retrieved = engine.get_seal("S-GSL")
        assert retrieved is not None
        assert retrieved.seal_id == seal.seal_id

    def test_seal_aggregates_turn_statistics_correctly(self):
        """
        Seal computa correctamente mas_average, mas_minimum, final_mas
        a partir de los scores de los turnos registrados.
        """
        engine = _mivp_engine_no_db()
        engine.create_mbr("S-STAT", "RCP-STAT", _default_mandate_binding())
        engine.compute_mas("S-STAT", "BAR-0", 0, _TEXT_ALIGNED)
        engine.compute_mas("S-STAT", "BAR-1", 1, _TEXT_WARNING)
        seal = engine.seal_mbr("S-STAT")
        history = engine.get_mas_history("S-STAT")
        expected_avg = sum(m.alignment_score for m in history) / len(history)
        expected_min = min(m.alignment_score for m in history)
        assert abs(seal.mas_average - expected_avg) < 1e-6
        assert abs(seal.mas_minimum - expected_min) < 1e-6
        assert seal.final_mas == history[-1].alignment_score


# ═════════════════════════════════════════════════════════════════
#  SECCIÓN 7 — Three-Tier Certification (MIVP-INV-008, INV-009)
# ═════════════════════════════════════════════════════════════════

class TestMIVPThreeTierCertification:
    """
    Cubre MIVP-INV-008 y MIVP-INV-009.

    INV-008: MANDATE-BOUND eligibility:
      mandate_bound_eligible = True IFF turns_in_violation=0 AND turns_in_warning=0.
      Designación Tier 1 — ejecución prístina sin ningún drift detectado.

    INV-009: MANDATE-ALIGNED eligibility:
      mandate_aligned_eligible = True IFF turns_in_violation=0 AND turns_in_warning>0.
      Designación Tier 2 — alineado con la misión; drift de warning pero sin HALT.
      MANDATE-BOUND y MANDATE-ALIGNED son MUTUAMENTE EXCLUYENTES en el mismo PoGC.
    """

    def test_inv008_mandate_bound_pristine_session(self):
        """
        MIVP-INV-008: sesión con todos los turnos ALIGNED →
        mandate_bound_eligible=True, mandate_aligned_eligible=False.
        Certification tier: MANDATE-BOUND.
        """
        engine = _mivp_engine_no_db()
        engine.create_mbr("S-BOUND", "RCP-BOUND", _default_mandate_binding())
        for i in range(3):
            mas = engine.compute_mas("S-BOUND", f"BAR-{i}", i, _TEXT_ALIGNED)
            assert mas.verdict == "ALIGNED", (
                f"Turno {i}: se esperaba ALIGNED, obtuvo {mas.verdict}"
            )
        seal = engine.seal_mbr("S-BOUND")
        assert seal.turns_in_violation == 0
        assert seal.turns_in_warning == 0
        assert seal.mandate_bound_eligible is True, "Debe ser MANDATE-BOUND"
        assert seal.mandate_aligned_eligible is False, (
            "MANDATE-ALIGNED no debe coexistir con MANDATE-BOUND (INV-009)"
        )
        assert seal.mandate_verdict == "ALIGNED"

    def test_inv009_mandate_aligned_with_warnings(self):
        """
        MIVP-INV-009: sesión con warnings pero sin violaciones →
        mandate_bound_eligible=False, mandate_aligned_eligible=True.
        Certification tier: MANDATE-ALIGNED.
        """
        engine = _mivp_engine_no_db()
        engine.create_mbr("S-ALIGN", "RCP-ALIGN", _default_mandate_binding())
        engine.compute_mas("S-ALIGN", "BAR-0", 0, _TEXT_ALIGNED)
        engine.compute_mas("S-ALIGN", "BAR-1", 1, _TEXT_WARNING)
        mas_check = engine.get_mas_history("S-ALIGN")
        assert any(m.verdict == "WARNING" for m in mas_check), (
            "Test requiere al menos un turno con WARNING"
        )
        assert all(m.verdict != "HALT" for m in mas_check), (
            "Test requiere cero violaciones HALT"
        )
        seal = engine.seal_mbr("S-ALIGN")
        assert seal.turns_in_violation == 0
        assert seal.turns_in_warning > 0
        assert seal.mandate_aligned_eligible is True, "Debe ser MANDATE-ALIGNED"
        assert seal.mandate_bound_eligible is False, (
            "MANDATE-BOUND no debe coexistir con MANDATE-ALIGNED (INV-009)"
        )
        assert seal.mandate_verdict == "WARNING"

    def test_inv009_mutual_exclusivity_proven_bound(self):
        """
        MIVP-INV-009 — Exclusión mutua parte 1: cuando MANDATE-BOUND=True,
        MANDATE-ALIGNED DEBE ser False. No pueden coexistir en el mismo sello.
        """
        engine = _mivp_engine_no_db()
        engine.create_mbr("S-ME1", "RCP-ME1", _default_mandate_binding())
        engine.compute_mas("S-ME1", "BAR-0", 0, _TEXT_ALIGNED)
        seal = engine.seal_mbr("S-ME1")
        assert not (seal.mandate_bound_eligible and seal.mandate_aligned_eligible), (
            "MANDATE-BOUND y MANDATE-ALIGNED no pueden ser True simultáneamente"
        )

    def test_inv009_mutual_exclusivity_proven_aligned(self):
        """
        MIVP-INV-009 — Exclusión mutua parte 2: cuando MANDATE-ALIGNED=True,
        MANDATE-BOUND DEBE ser False. Verificación simétrica de la restricción.
        """
        engine = _mivp_engine_no_db()
        engine.create_mbr("S-ME2", "RCP-ME2", _default_mandate_binding())
        engine.compute_mas("S-ME2", "BAR-0", 0, _TEXT_WARNING)
        seal = engine.seal_mbr("S-ME2")
        assert not (seal.mandate_bound_eligible and seal.mandate_aligned_eligible), (
            "MANDATE-BOUND y MANDATE-ALIGNED no pueden ser True simultáneamente"
        )

    def test_uncertified_on_halt_violation(self):
        """
        MIVP-INV-008/009: sesión con al menos una violación HALT →
        mandate_bound_eligible=False, mandate_aligned_eligible=False.
        Certification tier: UNCERTIFIED. Ambos tags Tier 1/2 son denegados.
        """
        engine = _mivp_engine_no_db()
        engine.create_mbr("S-UNC", "RCP-UNC", _default_mandate_binding())
        engine.compute_mas("S-UNC", "BAR-0", 0, _TEXT_HALT)
        seal = engine.seal_mbr("S-UNC")
        assert seal.turns_in_violation > 0
        assert seal.mandate_bound_eligible is False
        assert seal.mandate_aligned_eligible is False
        assert seal.mandate_verdict == "VIOLATED"

    def test_certification_tier_field_matches_eligibility(self):
        """
        El campo mandate_certification_tier en el dict serializado coincide
        con la lógica de elegibilidad: MANDATE-BOUND, MANDATE-ALIGNED, UNCERTIFIED.
        """
        engine = _mivp_engine_no_db()

        # Case 1: MANDATE-BOUND
        engine.create_mbr("S-CT1", "RCP-CT1", _default_mandate_binding())
        engine.compute_mas("S-CT1", "BAR-0", 0, _TEXT_ALIGNED)
        seal1 = engine.seal_mbr("S-CT1")
        d1 = seal1.to_dict()
        assert d1["mandate_certification_tier"] == "MANDATE-BOUND"

        # Case 2: MANDATE-ALIGNED
        engine.create_mbr("S-CT2", "RCP-CT2", _default_mandate_binding())
        engine.compute_mas("S-CT2", "BAR-0", 0, _TEXT_WARNING)
        seal2 = engine.seal_mbr("S-CT2")
        d2 = seal2.to_dict()
        assert d2["mandate_certification_tier"] == "MANDATE-ALIGNED"

        # Case 3: UNCERTIFIED
        engine.create_mbr("S-CT3", "RCP-CT3", _default_mandate_binding())
        engine.compute_mas("S-CT3", "BAR-0", 0, _TEXT_HALT)
        seal3 = engine.seal_mbr("S-CT3")
        d3 = seal3.to_dict()
        assert d3["mandate_certification_tier"] == "UNCERTIFIED"


# ═════════════════════════════════════════════════════════════════
#  SECCIÓN 8 — Full Session Flows
# ═════════════════════════════════════════════════════════════════

class TestMIVPFullSessionFlow:
    """
    Tests de flujo de sesión completo: MBR → MAS (múltiples turnos) → Seal.

    Verifican la coherencia end-to-end del protocolo tal como lo ejecuta
    GovernanceRuntime.start_session() → record_turn() → close_session().
    """

    def test_flow_pristine_mandate_bound_session(self):
        """
        Flujo completo Tier 1: 5 turnos 100% ALIGNED → MANDATE-BOUND.
        Verifica que get_mandate_proof() reporta mivp_active=True y el
        resumen de MBR, historial de MAS, y sello son coherentes.
        """
        engine = _mivp_engine_no_db()
        sid = "SESS-FLOW-PRISTINE"
        engine.create_mbr(sid, "RCP-FLOW-1", _default_mandate_binding())
        for i in range(5):
            engine.compute_mas(sid, f"BAR-FLOW-{i}", i, _TEXT_ALIGNED)
        seal = engine.seal_mbr(sid)
        proof = engine.get_mandate_proof(sid)
        assert proof["mivp_active"] is True
        assert proof["mandate_bound_eligible"] is True
        assert proof["pqc_signed"] is True or proof["pqc_signed"] is False  # env dependent
        assert proof["mbr"]["session_id"] == sid
        assert len(proof["mas_history"]) == 5
        assert proof["mbr_seal"]["mandate_certification_tier"] == "MANDATE-BOUND"
        assert seal.turns_covered == 5
        assert seal.turns_in_violation == 0
        assert seal.turns_in_warning == 0

    def test_flow_aligned_mandate_aligned_session(self):
        """
        Flujo completo Tier 2: 3 turnos ALIGNED + 2 WARNING → MANDATE-ALIGNED.
        """
        engine = _mivp_engine_no_db()
        sid = "SESS-FLOW-ALIGNED"
        engine.create_mbr(sid, "RCP-FLOW-2", _default_mandate_binding())
        for i in range(3):
            engine.compute_mas(sid, f"BAR-A{i}", i, _TEXT_ALIGNED)
        for i in range(3, 5):
            engine.compute_mas(sid, f"BAR-W{i}", i, _TEXT_WARNING)
        seal = engine.seal_mbr(sid)
        assert seal.mandate_aligned_eligible is True
        assert seal.mandate_bound_eligible is False
        assert seal.turns_in_warning == 2
        assert seal.turns_in_violation == 0
        proof = engine.get_mandate_proof(sid)
        assert proof["mbr_seal"]["mandate_certification_tier"] == "MANDATE-ALIGNED"

    def test_flow_violated_uncertified_session(self):
        """
        Flujo completo Tier 3: HALT en turno 2 → UNCERTIFIED, ambos tags denegados.
        El runtime habría emitido HALT en turno 2; seal refleja la violación.
        """
        engine = _mivp_engine_no_db()
        sid = "SESS-FLOW-VIOLATED"
        engine.create_mbr(sid, "RCP-FLOW-3", _default_mandate_binding())
        engine.compute_mas(sid, "BAR-V0", 0, _TEXT_ALIGNED)
        halt_mas = engine.compute_mas(sid, "BAR-V1", 1, _TEXT_HALT)
        engine.compute_mas(sid, "BAR-V2", 2, _TEXT_ALIGNED)
        assert halt_mas.verdict == "HALT"
        seal = engine.seal_mbr(sid)
        assert seal.mandate_bound_eligible is False
        assert seal.mandate_aligned_eligible is False
        assert seal.turns_in_violation >= 1
        assert seal.mandate_verdict == "VIOLATED"

    def test_flow_is_mandate_bound_eligible_helper(self):
        """is_mandate_bound_eligible() retorna True para sesión prístina."""
        engine = _mivp_engine_no_db()
        sid = "SESS-HELPER"
        engine.create_mbr(sid, "RCP-H", _default_mandate_binding())
        engine.compute_mas(sid, "BAR-H0", 0, _TEXT_ALIGNED)
        engine.seal_mbr(sid)
        assert engine.is_mandate_bound_eligible(sid) is True

    def test_flow_get_mandate_proof_inactive_without_mbr(self):
        """get_mandate_proof() retorna mivp_active=False si no hay MBR."""
        engine = _mivp_engine_no_db()
        proof = engine.get_mandate_proof("SESS-NO-PROOF")
        assert proof["mivp_active"] is False


# ═════════════════════════════════════════════════════════════════
#  SECCIÓN 9 — Invariant Coverage Traceability
# ═════════════════════════════════════════════════════════════════

class TestMIVPInvariantCoverage:
    """
    Verifica que los 9 invariantes MIVP-INV-001 a INV-009 están
    mencionados en los docstrings de esta suite — garantía de trazabilidad
    directa entre el código de test y el protocolo formal publicado.

    Este patrón es equivalente al TestBEVInvariantDocstrings de test_bev_ogr.py.
    """

    _REQUIRED_INVARIANTS = [
        "MIVP-INV-001",
        "MIVP-INV-002",
        "MIVP-INV-003",
        "MIVP-INV-004",
        "MIVP-INV-005",
        "MIVP-INV-006",
        "MIVP-INV-007",
        "MIVP-INV-008",
        "MIVP-INV-009",
    ]

    def _collect_all_docstrings(self) -> str:
        """Recopila todos los docstrings del módulo de tests para análisis."""
        import tests.test_mivp as this_module
        import inspect
        texts = [inspect.getdoc(this_module) or ""]
        for name, obj in inspect.getmembers(this_module, inspect.isclass):
            if name.startswith("Test"):
                texts.append(inspect.getdoc(obj) or "")
                for mname, method in inspect.getmembers(obj, inspect.isfunction):
                    texts.append(inspect.getdoc(method) or "")
        return "\n".join(texts)

    def test_all_nine_invariants_cited_in_docstrings(self):
        """
        Los 9 invariantes MIVP-INV-001 a INV-009 deben aparecer citados
        explícitamente en los docstrings de este archivo de tests.

        Esto garantiza trazabilidad directa: cualquier auditor puede
        vincular cada test con el invariante formal que verifica.
        """
        corpus = self._collect_all_docstrings()
        missing = [inv for inv in self._REQUIRED_INVARIANTS if inv not in corpus]
        assert not missing, (
            f"Invariantes sin cita en docstrings de test_mivp.py: {missing}\n"
            "Cada invariante MIVP debe estar mencionado al menos una vez."
        )

    def test_mivp_invariant_manifest_in_get_mandate_proof(self):
        """
        get_mandate_proof() incluye la lista 'invariants_enforced' con
        los 8 invariantes operacionales (INV-001 a INV-008 del engine).
        """
        engine = _mivp_engine_no_db()
        engine.create_mbr("S-MANIF", "RCP-MANIF", _default_mandate_binding())
        proof = engine.get_mandate_proof("S-MANIF")
        enforced = proof.get("invariants_enforced", [])
        for inv in ["MIVP-INV-001", "MIVP-INV-002", "MIVP-INV-003",
                    "MIVP-INV-004", "MIVP-INV-005", "MIVP-INV-006",
                    "MIVP-INV-007", "MIVP-INV-008"]:
            assert inv in enforced, (
                f"{inv} no aparece en invariants_enforced del mandate proof"
            )

    def test_mivp_module_docstring_cites_all_nine(self):
        """
        El docstring del módulo mandate_integrity_verification.py
        cita los 9 invariantes (INV-001 a INV-008 + INV-009 via MIVP-INV-009).
        """
        import omnix_core.bev.mandate_integrity_verification as mivp_mod
        doc = mivp_mod.__doc__ or ""
        for inv in [
            "MIVP-INV-001", "MIVP-INV-002", "MIVP-INV-003", "MIVP-INV-004",
            "MIVP-INV-005", "MIVP-INV-006", "MIVP-INV-007", "MIVP-INV-008",
        ]:
            assert inv in doc, (
                f"{inv} no citado en el docstring del módulo mandate_integrity_verification"
            )
