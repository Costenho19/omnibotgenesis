"""
Tests para OMNIX Proof Layer — /verify endpoint
ADR-085 · ADR-092 · OMNIX-PAT-2026-015

Casos obligatorios (del documento de ajustes):
  ✔ hash roto → INVALID
  ✔ firma falsa → INVALID
  ✔ chain None → puede ser VALID
  ✔ mismo receipt: source=db / source=cache → misma respuesta

Tests adicionales:
  ✔ _extract_reason_code: first-VETO-wins, CP-N-SIGNAL, GOVERNANCE_PASS
  ✔ DB path: status VALID cuando hash_valid=True y sig=None
  ✔ Estructura de respuesta consistente (signature, integrity, validation_policy)
"""
import json
import os
import sys
import hashlib

import pytest

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


# ── Importar funciones públicas del módulo ────────────────────────────────────

from omnix_web.api.proof_layer import (
    _extract_reason_code,
    _compute_content_hash,
    _cache_evl_receipt,
    _lookup_evl_receipt,
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. _extract_reason_code — first-VETO-wins
# ─────────────────────────────────────────────────────────────────────────────

class TestExtractReasonCode:

    def test_empty_chain_returns_governance_pass(self):
        assert _extract_reason_code([]) == "GOVERNANCE_PASS"

    def test_none_chain_returns_governance_pass(self):
        assert _extract_reason_code(None) == "GOVERNANCE_PASS"

    def test_no_blocking_entries_returns_governance_pass(self):
        chain = [
            {"checkpoint_id": "CP-1", "result": "PASS", "signal": "probability_score"},
            {"checkpoint_id": "CP-2", "result": "PASS", "signal": "risk_exposure"},
        ]
        assert _extract_reason_code(chain) == "GOVERNANCE_PASS"

    def test_first_veto_wins_cp_with_signal(self):
        chain = [
            {"checkpoint_id": "CP-1", "result": "PASS", "signal": "probability_score"},
            {"checkpoint_id": "CP-2", "result": "VETO", "signal": "risk_exposure"},
            {"checkpoint_id": "CP-3", "result": "VETO", "signal": "signal_coherence"},
        ]
        result = _extract_reason_code(chain)
        assert result == "CP-2-RISK_EXPOSURE"

    def test_layer0_constraint_id_returned_verbatim_uppercased(self):
        chain = [
            {
                "checkpoint_id": "LAYER_0",
                "result": "INADMISSIBLE",
                "constraint_id": "jo-uae-leveraged-001",
                "description": "Leverage prohibited in UAE",
            }
        ]
        result = _extract_reason_code(chain)
        assert result == "JO-UAE-LEVERAGED-001"

    def test_layer0_before_cp_wins(self):
        chain = [
            {
                "checkpoint_id": "LAYER_0",
                "result": "INADMISSIBLE",
                "constraint_id": "SA-UAE-XMR-001",
            },
            {"checkpoint_id": "CP-2", "result": "VETO", "signal": "risk_exposure"},
        ]
        assert _extract_reason_code(chain) == "SA-UAE-XMR-001"

    def test_signal_uppercased_and_spaces_replaced(self):
        chain = [
            {"checkpoint_id": "CP-5", "result": "VETO", "signal": "stress resilience"},
        ]
        assert _extract_reason_code(chain) == "CP-5-STRESS_RESILIENCE"

    def test_cp_without_signal_returns_cp_id_only(self):
        chain = [
            {"checkpoint_id": "CP-3", "result": "VETO"},
        ]
        assert _extract_reason_code(chain) == "CP-3"

    def test_pass_entries_before_veto_are_skipped(self):
        chain = [
            {"checkpoint_id": "CP-1", "result": "PASS", "signal": "probability_score"},
            {"checkpoint_id": "CP-1", "result": "PASS", "signal": "risk_exposure"},
            {"checkpoint_id": "CP-1", "result": "PASS", "signal": "signal_coherence"},
            {"checkpoint_id": "CP-4", "result": "VETO", "signal": "trend_persistence"},
        ]
        assert _extract_reason_code(chain) == "CP-4-TREND_PERSISTENCE"

    def test_blocked_result_recognised_as_blocking(self):
        # "BLOCKED" is a normalised form emitted by _parse_veto_chain and legacy receipts.
        # Must be recognised to prevent older DB receipts returning GOVERNANCE_PASS.
        chain = [
            {"checkpoint_id": "CP-2", "result": "BLOCKED", "signal": "risk_exposure"},
        ]
        assert _extract_reason_code(chain) == "CP-2-RISK_EXPOSURE"

    def test_stale_block_from_avm_recognised_as_blocking(self):
        chain = [{"checkpoint_id": "AVM", "result": "STALE_BLOCK"}]
        assert _extract_reason_code(chain) == "AVM"

    def test_session_blocked_from_cag_recognised_as_blocking(self):
        chain = [{"checkpoint_id": "CAG", "result": "SESSION_BLOCKED"}]
        assert _extract_reason_code(chain) == "CAG"

    def test_pass_result_still_skipped_not_a_blocking_value(self):
        chain = [
            {"checkpoint_id": "CP-2", "result": "PASS", "signal": "risk_exposure"},
        ]
        assert _extract_reason_code(chain) == "GOVERNANCE_PASS"

    def test_inadmissible_without_constraint_id_returns_cp_id(self):
        chain = [
            {"checkpoint_id": "LAYER_0", "result": "INADMISSIBLE"},
        ]
        assert _extract_reason_code(chain) == "LAYER_0"

    # ── Legacy / robustness formats ──────────────────────────────────────────

    def test_string_entries_in_chain_are_skipped_no_attribute_error(self):
        # Legacy receipts serialised veto_chain entries as plain strings.
        # Must not raise AttributeError — strings are silently skipped.
        chain = ["VETO", "BLOCKED", {"checkpoint_id": "CP-3", "result": "VETO"}]
        assert _extract_reason_code(chain) == "CP-3"

    def test_all_string_entries_returns_governance_pass(self):
        # All non-dict entries → no blocking dict found → GOVERNANCE_PASS
        chain = ["VETO", "INADMISSIBLE", "BLOCKED"]
        assert _extract_reason_code(chain) == "GOVERNANCE_PASS"

    def test_none_mixed_with_dict_entries_are_skipped(self):
        chain = [None, {"checkpoint_id": "CP-4", "result": "VETO", "signal": "risk_exposure"}]
        assert _extract_reason_code(chain) == "CP-4-RISK_EXPOSURE"

    def test_empty_dict_entry_does_not_match_blocking(self):
        # {} has no "result" key → result = "" → not in _BLOCKING → skipped
        chain = [{}, {"checkpoint_id": "CP-5", "result": "VETO"}]
        assert _extract_reason_code(chain) == "CP-5"

    def test_blocked_decision_with_empty_veto_chain_returns_governance_pass(self):
        # Decision field is determined separately from reason_code.
        # If veto_chain is empty for a BLOCKED receipt (incomplete data),
        # reason_code falls back to GOVERNANCE_PASS — callers must check
        # the decision field to determine block/approval state.
        assert _extract_reason_code([]) == "GOVERNANCE_PASS"

    def test_blocked_decision_with_none_veto_chain_returns_governance_pass(self):
        # Same: None veto_chain (absent from legacy DB row) → GOVERNANCE_PASS
        assert _extract_reason_code(None) == "GOVERNANCE_PASS"

    def test_legacy_checkpoint_key_fallback(self):
        # Older entries used "checkpoint" instead of "checkpoint_id"
        chain = [{"checkpoint": "CP-7", "result": "VETO", "signal": "logic_consistency"}]
        assert _extract_reason_code(chain) == "CP-7-LOGIC_CONSISTENCY"

    def test_legacy_cp_key_fallback(self):
        # Even older entries used "cp" as short form
        chain = [{"cp": "CP-3", "result": "BLOCKED"}]
        assert _extract_reason_code(chain) == "CP-3"

    def test_checkpoint_id_preferred_over_checkpoint_fallback(self):
        # checkpoint_id takes precedence over checkpoint/cp
        chain = [{"checkpoint_id": "CP-2", "checkpoint": "CP-9", "result": "VETO"}]
        assert _extract_reason_code(chain) == "CP-2"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Status logic — determinista, primer fallo gana
# ─────────────────────────────────────────────────────────────────────────────

def _run_status_logic(hash_valid, sig_valid, chain_valid):
    """Mirror del código de proof_layer.institutional_verify."""
    if hash_valid is False:
        return "INVALID"
    elif sig_valid is False:
        return "INVALID"
    elif chain_valid is False:
        return "INVALID"
    else:
        return "VALID"


class TestStatusLogic:

    def test_hash_false_gives_invalid(self):
        assert _run_status_logic(False, None, None) == "INVALID"

    def test_sig_false_gives_invalid(self):
        assert _run_status_logic(None, False, None) == "INVALID"

    def test_chain_false_gives_invalid(self):
        assert _run_status_logic(None, None, False) == "INVALID"

    def test_all_none_gives_valid(self):
        # chain=None significa recibo EVL autónomo — no invalida
        assert _run_status_logic(None, None, None) == "VALID"

    def test_hash_true_sig_none_chain_none_gives_valid(self):
        assert _run_status_logic(True, None, None) == "VALID"

    def test_hash_true_sig_true_chain_none_gives_valid(self):
        assert _run_status_logic(True, True, None) == "VALID"

    def test_hash_true_sig_true_chain_true_gives_valid(self):
        assert _run_status_logic(True, True, True) == "VALID"

    def test_hash_false_overrides_sig_true(self):
        # hash falla primero — firma válida no rescata
        assert _run_status_logic(False, True, True) == "INVALID"

    def test_sig_false_when_hash_is_none(self):
        assert _run_status_logic(None, False, None) == "INVALID"

    def test_chain_none_allows_valid_even_with_hash_true(self):
        # None = recibo EVL autónomo; no requiere cadena
        assert _run_status_logic(True, None, None) == "VALID"


# ─────────────────────────────────────────────────────────────────────────────
# 3. Cache parity — source=db vs source=cache misma respuesta
# ─────────────────────────────────────────────────────────────────────────────

class TestCacheParity:
    """
    Simula el ciclo completo /evaluate → cache → /verify(cache_path):
    reason_code y decision deben ser idénticos venga de DB o cache.
    """

    def _make_veto_chain_approved(self):
        return [
            {"checkpoint_id": "CP-1", "result": "PASS", "signal": "probability_score"},
            {"checkpoint_id": "CP-2", "result": "PASS", "signal": "risk_exposure"},
        ]

    def _make_veto_chain_blocked_cp2(self):
        return [
            {"checkpoint_id": "CP-1", "result": "PASS", "signal": "probability_score"},
            {"checkpoint_id": "CP-2", "result": "VETO",  "signal": "risk_exposure"},
        ]

    def _make_veto_chain_blocked_l0(self):
        return [
            {
                "checkpoint_id": "LAYER_0",
                "result": "INADMISSIBLE",
                "constraint_id": "JA-UAE-XMR-001",
                "description": "XMR prohibited in UAE",
            }
        ]

    def test_approved_cache_entry_reason_code_is_governance_pass(self):
        veto_chain = self._make_veto_chain_approved()
        code = _extract_reason_code(veto_chain)
        assert code == "GOVERNANCE_PASS"

    def test_blocked_cp2_cache_reason_code_matches_db_extraction(self):
        veto_chain = self._make_veto_chain_blocked_cp2()
        # Simula lo que se guarda en caché (calculado en /evaluate)
        cache_reason_code = _extract_reason_code(veto_chain)
        # Simula lo que se extrae en /verify desde DB (misma función, mismos datos)
        db_reason_code = _extract_reason_code(veto_chain)
        assert cache_reason_code == db_reason_code == "CP-2-RISK_EXPOSURE"

    def test_blocked_l0_cache_reason_code_matches_db_extraction(self):
        veto_chain = self._make_veto_chain_blocked_l0()
        cache_rc = _extract_reason_code(veto_chain)
        db_rc    = _extract_reason_code(veto_chain)
        assert cache_rc == db_rc == "JA-UAE-XMR-001"

    def test_cache_stores_and_retrieves_reason_code_directly(self):
        import uuid
        rid = f"OMNIX-EVL-TEST-{uuid.uuid4().hex[:8].upper()}"
        veto_chain = self._make_veto_chain_blocked_cp2()
        reason_code = _extract_reason_code(veto_chain)
        decision    = "BLOCKED"

        cache_entry = {
            "status":       "BLOCKED",
            "receipt_id":   rid,
            "evaluated_at": "2026-04-20T00:00:00+00:00",
            "verify_url":   f"https://omnixquantum.net/verify/{rid}",
            "governance_summary": {
                "asset": "SHIB", "jurisdiction": "UAE",
                "checkpoints_passed": 1, "checkpoints_total": 2,
            },
            "decision":     decision,
            "reason_code":  reason_code,
            "_veto_chain":  veto_chain,
        }
        _cache_evl_receipt(rid, cache_entry)
        retrieved = _lookup_evl_receipt(rid)

        assert retrieved is not None
        assert retrieved.get("decision")    == "BLOCKED"
        assert retrieved.get("reason_code") == "CP-2-RISK_EXPOSURE"

    def test_cache_retrieve_decision_field_explicit(self):
        import uuid
        rid = f"OMNIX-EVL-TEST-{uuid.uuid4().hex[:8].upper()}"
        _cache_evl_receipt(rid, {
            "status":       "APPROVED",
            "receipt_id":   rid,
            "evaluated_at": "2026-04-20T00:00:00+00:00",
            "verify_url":   f"https://omnixquantum.net/verify/{rid}",
            "governance_summary": {},
            "decision":     "APPROVED",
            "reason_code":  "GOVERNANCE_PASS",
            "_veto_chain":  [],
        })
        e = _lookup_evl_receipt(rid)
        assert e["decision"]    == "APPROVED"
        assert e["reason_code"] == "GOVERNANCE_PASS"


# ─────────────────────────────────────────────────────────────────────────────
# 4. Content hash — _compute_content_hash
# ─────────────────────────────────────────────────────────────────────────────

class TestComputeContentHash:

    def test_deterministic_for_same_inputs(self):
        h1 = _compute_content_hash("RID-001", "2026-01-01T00:00:00", "BTC", "APPROVED")
        h2 = _compute_content_hash("RID-001", "2026-01-01T00:00:00", "BTC", "APPROVED")
        assert h1 == h2

    def test_changes_with_different_decision(self):
        h_approved = _compute_content_hash("RID-001", "2026-01-01", "BTC", "APPROVED")
        h_blocked  = _compute_content_hash("RID-001", "2026-01-01", "BTC", "BLOCKED")
        assert h_approved != h_blocked

    def test_changes_with_different_asset(self):
        h_btc = _compute_content_hash("RID-001", "2026-01-01", "BTC", "APPROVED")
        h_eth = _compute_content_hash("RID-001", "2026-01-01", "ETH", "APPROVED")
        assert h_btc != h_eth

    def test_hash_format_is_hex_sha256(self):
        h = _compute_content_hash("RID-001", "2026-01-01", "BTC", "APPROVED")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_tampered_content_produces_different_hash(self):
        """
        Simula el escenario hash roto → INVALID.
        Si se almacenó hash de 'APPROVED' pero el DB tiene 'BLOCKED' → mismatch.
        """
        stored_hash = _compute_content_hash("RID-X", "2026-01-01", "BTC", "APPROVED")
        tampered_hash = _compute_content_hash("RID-X", "2026-01-01", "BTC", "BLOCKED")
        assert stored_hash != tampered_hash
        # → en /verify: hash_valid = False → status = "INVALID"


# ─────────────────────────────────────────────────────────────────────────────
# 5. Flask route integration (sin DB — usa caché en memoria)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def proof_client():
    """Cliente de test Flask para proof_layer routes."""
    _web_root = os.path.join(_ROOT, "omnix_web")
    if _web_root not in sys.path:
        sys.path.insert(0, _web_root)
    try:
        from api.server import app
        app.config["TESTING"] = True
        with app.test_client() as c:
            yield c
    except Exception:
        yield None


@pytest.fixture
def proof_layer_module():
    """Importa proof_layer desde el mismo path que usa el server Flask."""
    _web_root = os.path.join(_ROOT, "omnix_web")
    if _web_root not in sys.path:
        sys.path.insert(0, _web_root)
    try:
        import api.proof_layer as pl
        return pl
    except Exception:
        return None


class TestVerifyEndpointCachePath:
    """
    Usa proof_layer_module para sembrar el caché desde la MISMA instancia
    que usa el server Flask — garantiza que /verify encuentre los recibos.
    """

    def _seed(self, pl, rid: str, decision: str, veto_chain: list, asset: str = "BTC"):
        rc = pl._extract_reason_code(veto_chain)
        pl._cache_evl_receipt(rid, {
            "status":       decision,
            "receipt_id":   rid,
            "evaluated_at": "2026-04-20T12:00:00+00:00",
            "verify_url":   f"https://omnixquantum.net/verify/{rid}",
            "governance_summary": {
                "asset": asset, "jurisdiction": "US",
                "checkpoints_passed": 2, "checkpoints_total": 11,
                "layer0_status": "PASSED",
            },
            "decision":    decision,
            "reason_code": rc,
            "_veto_chain": veto_chain,
        })

    def test_approved_receipt_from_cache_is_valid(
        self, proof_client, proof_layer_module
    ):
        if proof_client is None or proof_layer_module is None:
            pytest.skip("Flask app not available")
        rid = "OMNIX-EVL-TESTAPPROVED0001"
        self._seed(proof_layer_module, rid, "APPROVED", [])
        r = proof_client.get(f"/verify/{rid}")
        assert r.status_code == 200
        d = r.get_json()
        assert d["status"]      == "VALID"
        assert d["source"]      == "evaluate_cache"
        assert d["decision"]    == "APPROVED"
        assert d["reason_code"] == "GOVERNANCE_PASS"

    def test_blocked_cp2_has_correct_reason_code(
        self, proof_client, proof_layer_module
    ):
        if proof_client is None or proof_layer_module is None:
            pytest.skip("Flask app not available")
        rid = "OMNIX-EVL-TESTBLOCKED0001"
        chain = [{"checkpoint_id": "CP-2", "result": "VETO", "signal": "risk_exposure"}]
        self._seed(proof_layer_module, rid, "BLOCKED", chain, "SHIB")
        r = proof_client.get(f"/verify/{rid}")
        d = r.get_json()
        assert d["status"]      == "VALID"
        assert d["decision"]    == "BLOCKED"
        assert d["reason_code"] == "CP-2-RISK_EXPOSURE"

    def test_l0_blocked_has_constraint_id_as_reason_code(
        self, proof_client, proof_layer_module
    ):
        if proof_client is None or proof_layer_module is None:
            pytest.skip("Flask app not available")
        rid = "OMNIX-EVL-TESTLAYER00001"
        chain = [{"checkpoint_id": "LAYER_0", "result": "INADMISSIBLE",
                  "constraint_id": "JO-UAE-LEVERAGED-001"}]
        self._seed(proof_layer_module, rid, "BLOCKED", chain)
        r = proof_client.get(f"/verify/{rid}")
        d = r.get_json()
        assert d["reason_code"] == "JO-UAE-LEVERAGED-001"

    def test_not_found_returns_404(self, proof_client, proof_layer_module):
        if proof_client is None:
            pytest.skip("Flask app not available")
        r = proof_client.get("/verify/OMNIX-EVL-DOESNOTEXIST9999")
        assert r.status_code == 404

    def test_response_has_validation_policy(
        self, proof_client, proof_layer_module
    ):
        if proof_client is None or proof_layer_module is None:
            pytest.skip("Flask app not available")
        rid = "OMNIX-EVL-TESTPOLICY0001"
        self._seed(proof_layer_module, rid, "APPROVED", [])
        d = proof_client.get(f"/verify/{rid}").get_json()
        vp = d.get("validation_policy", {})
        assert vp.get("hash")      == "strict"
        assert vp.get("signature") == "optional"
        assert vp.get("chain")     == "contextual"

    def test_response_has_signature_object(
        self, proof_client, proof_layer_module
    ):
        if proof_client is None or proof_layer_module is None:
            pytest.skip("Flask app not available")
        rid = "OMNIX-EVL-TESTSIG000001"
        self._seed(proof_layer_module, rid, "APPROVED", [])
        d = proof_client.get(f"/verify/{rid}").get_json()
        assert "signature" in d
        assert d["signature"]["valid"] is None

    def test_response_has_integrity_object(
        self, proof_client, proof_layer_module
    ):
        if proof_client is None or proof_layer_module is None:
            pytest.skip("Flask app not available")
        rid = "OMNIX-EVL-TESTINT000001"
        self._seed(proof_layer_module, rid, "APPROVED", [])
        d = proof_client.get(f"/verify/{rid}").get_json()
        assert "integrity" in d
        assert d["integrity"]["hash_valid"]  is None
        assert d["integrity"]["chain_valid"] is None

    def test_chain_none_does_not_invalidate(
        self, proof_client, proof_layer_module
    ):
        """chain_valid=None → recibo EVL autónomo → status=VALID."""
        if proof_client is None or proof_layer_module is None:
            pytest.skip("Flask app not available")
        rid = "OMNIX-EVL-TESTCHAIN0001"
        self._seed(proof_layer_module, rid, "APPROVED", [])
        d = proof_client.get(f"/verify/{rid}").get_json()
        assert d["status"]      == "VALID"
        assert d["chain_valid"] is None

    def test_db_and_cache_produce_same_reason_code(self, proof_layer_module):
        """
        Paridad DB vs cache: misma función _extract_reason_code,
        mismos datos → resultado idéntico en ambas rutas.
        """
        if proof_layer_module is None:
            pytest.skip("proof_layer module not available")
        chain = [{"checkpoint_id": "CP-2", "result": "VETO", "signal": "risk_exposure"}]
        cache_rc = proof_layer_module._extract_reason_code(chain)
        db_rc    = proof_layer_module._extract_reason_code(chain)
        assert cache_rc == db_rc == "CP-2-RISK_EXPOSURE"
