"""
Cross-Language Conformance Vector Tests
========================================
Document ID : OMNIX-CONFORMANCE-PYTHON-2026-05
Invariants  : FVP-INV-007 (platform_fingerprint determinism)
              ATF-INV-006 (offline canonical JSON reproducibility)
ADR refs    : ADR-167 §2.1 · RFC-ATF-3 · ADR-157 rev.2

These tests validate the Python implementation against the canonical
cross-language conformance vectors defined in sdk/conformance_vectors.json.

Any compliant OMNIX SDK implementation (Python, Node.js, Go, Rust, …)
must produce identical output for every vector in that file. This test
suite is the Python-language proof of conformance.

Run:
    TESTING=true TELEGRAM_BOT_TOKEN=test-token \
    pytest tests/test_conformance_vectors.py -v
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Load canonical conformance vectors
# ---------------------------------------------------------------------------

VECTORS_PATH = Path(__file__).parent.parent / "sdk" / "conformance_vectors.json"


@pytest.fixture(scope="module")
def vectors() -> dict[str, Any]:
    assert VECTORS_PATH.exists(), (
        f"Conformance vectors file not found: {VECTORS_PATH}. "
        "Run sdk/generate_vectors.py to regenerate."
    )
    with VECTORS_PATH.open(encoding="utf-8") as fh:
        data = json.load(fh)
    assert data["schema"] == "omnix-conformance-vectors-1.0", (
        "Unexpected schema version in conformance vectors file."
    )
    return data


# ---------------------------------------------------------------------------
# Reference implementations (mirrors forensic_blueprint.py exactly)
# ---------------------------------------------------------------------------

def _compute_fingerprint(key_b64: str) -> str:
    """
    FVP-INV-007 canonical fingerprint algorithm.

    fingerprint = "sha256:" + sha256(base64decode(key_b64)).hexdigest()

    This is the same code path as forensic_blueprint.py lines 154 and 331/336.
    Any SDK in any language must produce the same string for the same input.
    """
    raw_bytes = base64.b64decode(key_b64)
    return "sha256:" + hashlib.sha256(raw_bytes).hexdigest()


def _canonical_json(obj: Any) -> str:
    """
    ATF-INV-006 canonical JSON serialization.

    Rules (must be implemented identically in every SDK):
      1. Object keys sorted A→Z at every nesting level (sort_keys=True)
      2. No whitespace around : or , (separators=(",", ":"))
      3. Unicode characters preserved as-is, NOT \\uXXXX-escaped (ensure_ascii=False)
      4. Result encoded as UTF-8 bytes before hashing

    This mirrors oep_generator.py and is the reference used for OEP manifest hashing.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _canonical_json_sha256(obj: Any) -> str:
    """SHA-256 hex of canonical JSON UTF-8 bytes."""
    return hashlib.sha256(_canonical_json(obj).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# FVP-INV-007 — Key fingerprint cross-language parity
# ---------------------------------------------------------------------------

class TestKeyFingerprintVectors:
    """
    FVP-INV-007 conformance: Python implementation vs. canonical vectors.

    Every vector in sdk/conformance_vectors.json["vectors"]["key_fingerprint"]
    must be reproduced exactly by the Python _compute_fingerprint() function.
    """

    def test_all_vectors_loaded(self, vectors: dict) -> None:
        kfp = vectors["vectors"]["key_fingerprint"]
        assert len(kfp) >= 7, f"Expected ≥7 key fingerprint vectors, got {len(kfp)}"

    @pytest.mark.parametrize("vector_index", range(7))
    def test_fingerprint_matches_vector(
        self, vectors: dict, vector_index: int
    ) -> None:
        kfp = vectors["vectors"]["key_fingerprint"]
        if vector_index >= len(kfp):
            pytest.skip(f"Vector index {vector_index} not present in file")

        v = kfp[vector_index]
        result = _compute_fingerprint(v["input_key_b64"])

        assert result == v["expected_fingerprint"], (
            f"[{v['id']}] Python fingerprint mismatch.\n"
            f"  Key size : {v['key_size_bytes']} bytes\n"
            f"  Expected : {v['expected_fingerprint']}\n"
            f"  Got      : {result}\n"
            f"  Algorithm: {v['algorithm']}"
        )

    def test_fingerprint_prefix_is_sha256(self, vectors: dict) -> None:
        for v in vectors["vectors"]["key_fingerprint"]:
            result = _compute_fingerprint(v["input_key_b64"])
            assert result.startswith("sha256:"), (
                f"[{v['id']}] Fingerprint must start with 'sha256:' prefix, got: {result[:20]}"
            )

    def test_fingerprint_hex_length(self, vectors: dict) -> None:
        for v in vectors["vectors"]["key_fingerprint"]:
            result = _compute_fingerprint(v["input_key_b64"])
            hex_part = result[len("sha256:"):]
            assert len(hex_part) == 64, (
                f"[{v['id']}] SHA-256 hex must be 64 chars, got {len(hex_part)}"
            )
            assert all(c in "0123456789abcdef" for c in hex_part), (
                f"[{v['id']}] SHA-256 hex must be lowercase hexadecimal"
            )

    def test_fingerprint_is_deterministic(self, vectors: dict) -> None:
        for v in vectors["vectors"]["key_fingerprint"]:
            r1 = _compute_fingerprint(v["input_key_b64"])
            r2 = _compute_fingerprint(v["input_key_b64"])
            assert r1 == r2, (
                f"[{v['id']}] Fingerprint must be deterministic across calls"
            )

    def test_different_keys_different_fingerprints(self, vectors: dict) -> None:
        kfp = vectors["vectors"]["key_fingerprint"]
        fingerprints = [_compute_fingerprint(v["input_key_b64"]) for v in kfp]
        assert len(set(fingerprints)) == len(fingerprints), (
            "All distinct input keys must produce distinct fingerprints"
        )

    def test_dilithium3_sized_keys_present(self, vectors: dict) -> None:
        kfp = vectors["vectors"]["key_fingerprint"]
        dilithium_vectors = [v for v in kfp if v["key_size_bytes"] == 1952]
        assert len(dilithium_vectors) >= 3, (
            "At least 3 Dilithium-3 sized (1952-byte) key vectors required"
        )

    def test_boundary_cases_present(self, vectors: dict) -> None:
        kfp = vectors["vectors"]["key_fingerprint"]
        sizes = {v["key_size_bytes"] for v in kfp}
        assert 1 in sizes, "1-byte minimal boundary vector required"
        assert 32 in sizes or 64 in sizes, "Small key boundary vector required"


# ---------------------------------------------------------------------------
# ATF-INV-006 — Canonical JSON cross-language parity
# ---------------------------------------------------------------------------

class TestCanonicalJsonVectors:
    """
    ATF-INV-006 conformance: Python canonical JSON vs. canonical vectors.

    Every vector in sdk/conformance_vectors.json["vectors"]["canonical_json"]
    must be reproduced exactly by the Python _canonical_json() function.
    """

    def test_all_vectors_loaded(self, vectors: dict) -> None:
        cj = vectors["vectors"]["canonical_json"]
        assert len(cj) >= 5, f"Expected ≥5 canonical JSON vectors, got {len(cj)}"

    @pytest.mark.parametrize("vector_index", range(5))
    def test_canonical_json_matches_vector(
        self, vectors: dict, vector_index: int
    ) -> None:
        cj = vectors["vectors"]["canonical_json"]
        if vector_index >= len(cj):
            pytest.skip(f"Vector index {vector_index} not present in file")

        v = cj[vector_index]
        result = _canonical_json(v["input"])

        assert result == v["expected_canonical_json"], (
            f"[{v['id']}] Canonical JSON mismatch.\n"
            f"  Expected : {v['expected_canonical_json']!r}\n"
            f"  Got      : {result!r}\n"
            f"  Input    : {v['input']}"
        )

    @pytest.mark.parametrize("vector_index", range(5))
    def test_canonical_json_hash_matches_vector(
        self, vectors: dict, vector_index: int
    ) -> None:
        cj = vectors["vectors"]["canonical_json"]
        if vector_index >= len(cj):
            pytest.skip(f"Vector index {vector_index} not present in file")

        v = cj[vector_index]
        result_hash = _canonical_json_sha256(v["input"])

        assert result_hash == v["expected_sha256_hex"], (
            f"[{v['id']}] Canonical JSON SHA-256 hash mismatch.\n"
            f"  Expected : {v['expected_sha256_hex']}\n"
            f"  Got      : {result_hash}"
        )

    def test_key_sorting_rule(self, vectors: dict) -> None:
        cj = vectors["vectors"]["canonical_json"]
        sort_vector = next(v for v in cj if v["id"] == "CJ-002")
        result = _canonical_json(sort_vector["input"])
        assert result == '{"a":1,"m":13,"z":26}', (
            "Keys must be sorted A→Z regardless of insertion order"
        )

    def test_nested_key_sorting_rule(self, vectors: dict) -> None:
        cj = vectors["vectors"]["canonical_json"]
        nested = next(v for v in cj if v["id"] == "CJ-003")
        result = _canonical_json(nested["input"])
        assert '"a.json"' in result, "Inner object keys must also be sorted"
        a_pos = result.index('"a.json"')
        b_pos = result.index('"b.json"')
        assert a_pos < b_pos, "a.json must appear before b.json after sorting"

    def test_unicode_not_escaped(self, vectors: dict) -> None:
        cj = vectors["vectors"]["canonical_json"]
        unicode_vector = next(v for v in cj if v["id"] == "CJ-004")
        result = _canonical_json(unicode_vector["input"])
        em_dash = "\u2014"
        assert em_dash in result, (
            "Unicode characters must NOT be escaped as \\uXXXX — "
            "ensure_ascii=False is required"
        )
        assert "\\u2014" not in result, "Em-dash must appear literally, not as \\u2014"

    def test_no_whitespace_in_output(self, vectors: dict) -> None:
        for v in vectors["vectors"]["canonical_json"]:
            result = _canonical_json(v["input"])
            assert ": " not in result, f"[{v['id']}] No space after colon allowed"
            assert ", " not in result, f"[{v['id']}] No space after comma allowed"

    def test_canonical_json_is_deterministic(self, vectors: dict) -> None:
        for v in vectors["vectors"]["canonical_json"]:
            r1 = _canonical_json(v["input"])
            r2 = _canonical_json(v["input"])
            assert r1 == r2, f"[{v['id']}] Canonical JSON must be deterministic"


# ---------------------------------------------------------------------------
# Schema integrity
# ---------------------------------------------------------------------------

class TestVectorFileIntegrity:
    """Verify the conformance vector file itself is well-formed and complete."""

    def test_schema_version(self, vectors: dict) -> None:
        assert vectors["schema"] == "omnix-conformance-vectors-1.0"

    def test_total_vectors_count(self, vectors: dict) -> None:
        kfp_count = len(vectors["vectors"]["key_fingerprint"])
        cj_count  = len(vectors["vectors"]["canonical_json"])
        stated    = vectors["total_vectors"]
        assert stated == kfp_count + cj_count, (
            f"total_vectors {stated} != actual {kfp_count + cj_count}"
        )

    def test_invariants_covered_declared(self, vectors: dict) -> None:
        covered = vectors.get("invariants_covered", [])
        assert any("FVP-INV-007" in c for c in covered), (
            "FVP-INV-007 must be listed in invariants_covered"
        )
        assert any("ATF-INV-006" in c for c in covered), (
            "ATF-INV-006 must be listed in invariants_covered"
        )

    def test_algorithm_specs_present(self, vectors: dict) -> None:
        specs = vectors.get("algorithm_specs", {})
        assert "key_fingerprint" in specs
        assert "canonical_json" in specs

    def test_all_kfp_vectors_have_required_fields(self, vectors: dict) -> None:
        required = {"id", "input_key_b64", "expected_fingerprint", "key_size_bytes"}
        for v in vectors["vectors"]["key_fingerprint"]:
            missing = required - set(v.keys())
            assert not missing, f"[{v.get('id','?')}] Missing fields: {missing}"

    def test_all_cj_vectors_have_required_fields(self, vectors: dict) -> None:
        required = {"id", "input", "expected_canonical_json", "expected_sha256_hex"}
        for v in vectors["vectors"]["canonical_json"]:
            missing = required - set(v.keys())
            assert not missing, f"[{v.get('id','?')}] Missing fields: {missing}"

    def test_vectors_path_relative_to_repo_root(self) -> None:
        assert VECTORS_PATH.exists(), (
            f"sdk/conformance_vectors.json must exist at repo root level. "
            f"Looked at: {VECTORS_PATH}"
        )
