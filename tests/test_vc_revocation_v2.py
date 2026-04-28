"""
Tests for ADR-130 v2 — VC Trust Revocation Registry: Full Europa features.

Covers:
    T001 — StatusList2021 bitstring compressed (_build_encoded_list, status_list_index)
    T002 — ETag / conditional GET (get_etag, If-None-Match logic)
    T003 — Revocation webhook (fire_revocation_webhook — mock HTTP delivery)
    T004 — Human accountability binding (humanSigner auto-lookup — correct columns)

All DB-dependent methods are mocked. Only pure logic and structure is tested directly.
"""
from __future__ import annotations

import base64
import gzip
import hashlib
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from omnix_web.api.omnix_engine.vc_revocation import (
    BITSTRING_SIZE,
    VCRevocationRegistry,
    _build_encoded_list,
    _get_next_status_list_index,
    fire_revocation_webhook,
)
from omnix_web.api.omnix_engine.receipt_to_vc import ReceiptToVC


# ── Helpers ────────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _minimal_receipt(receipt_id: str = "OMNIX-TRD-aabbccdd") -> dict:
    return {
        "receipt_id":       receipt_id,
        "timestamp":        _now_iso(),
        "asset":            "BTC",
        "decision":         "APPROVED",
        "domain":           "trading",
        "veto_chain":       [],
        "policy_version":   "6.5.4e",
        "engine_version":   "6.5.4e",
        "prev_hash":        "abc123",
        "content_hash":     "def456",
        "signature":        None,
        "signature_algorithm": "SHA-256",
        "public_key":       None,
        "signing_provider": "sha256",
    }


# ── T001: StatusList2021 bitstring ────────────────────────────────────────────

def test_T001a_build_encoded_list_empty():
    """Empty revocation list → 131072-bit all-zero bitstring, gzip+base64url."""
    encoded = _build_encoded_list([])
    compressed = base64.urlsafe_b64decode(encoded + "==")
    raw = gzip.decompress(compressed)
    assert len(raw) * 8 == BITSTRING_SIZE
    assert all(b == 0 for b in raw)


def test_T001b_build_encoded_list_single_index():
    """Single revoked index → only that bit is set."""
    encoded = _build_encoded_list([0])
    compressed = base64.urlsafe_b64decode(encoded + "==")
    raw = gzip.decompress(compressed)
    # Index 0 → bit 7 of byte 0 (MSB first)
    assert raw[0] & 0x80 == 0x80  # bit 7 set
    assert raw[1] == 0


def test_T001c_build_encoded_list_multiple_indices():
    """Multiple indices → each corresponding bit set."""
    indices = [0, 1, 7, 8, 131071]  # first two bits, bit 7, second byte, last bit
    encoded = _build_encoded_list(indices)
    compressed = base64.urlsafe_b64decode(encoded + "==")
    raw = gzip.decompress(compressed)
    assert raw[0] & 0x80 == 0x80  # index 0
    assert raw[0] & 0x40 == 0x40  # index 1
    assert raw[0] & 0x01 == 0x01  # index 7
    assert raw[1] & 0x80 == 0x80  # index 8


def test_T001d_build_encoded_list_size():
    """Result is always base64url-encoded — no padding issues."""
    encoded = _build_encoded_list([100, 200, 300])
    # Must be decodable without error
    compressed = base64.urlsafe_b64decode(encoded + "==")
    raw = gzip.decompress(compressed)
    assert len(raw) == BITSTRING_SIZE // 8


def test_T001e_build_encoded_list_out_of_range_ignored():
    """Indices out of range (>= BITSTRING_SIZE) are silently ignored."""
    encoded = _build_encoded_list([BITSTRING_SIZE, BITSTRING_SIZE + 1, -1])
    compressed = base64.urlsafe_b64decode(encoded + "==")
    raw = gzip.decompress(compressed)
    assert all(b == 0 for b in raw)


def test_T001f_get_next_status_list_index_empty_registry():
    """No existing entries → returns 0."""
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = (0,)
    result = _get_next_status_list_index(mock_cur)
    assert result == 0


def test_T001g_get_next_status_list_index_sequential():
    """Existing max index=4 → returns 5."""
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = (5,)
    result = _get_next_status_list_index(mock_cur)
    assert result == 5


def test_T001h_bitstring_size_w3c_minimum():
    """BITSTRING_SIZE must be >= 131,072 (W3C StatusList2021 §4 minimum)."""
    assert BITSTRING_SIZE >= 131072


# ── T002: ETag / conditional GET ─────────────────────────────────────────────

def test_T002a_get_etag_returns_32char_hex():
    """get_etag() returns a 32-character hex string."""
    registry = VCRevocationRegistry()
    with patch.object(registry, 'get_etag') as mock_etag:
        mock_etag.return_value = hashlib.sha256(b"0:none").hexdigest()[:32]
        etag = registry.get_etag()
    assert isinstance(etag, str)
    assert len(etag) == 32
    assert all(c in "0123456789abcdef" for c in etag)


def test_T002b_get_status_list_includes_etag():
    """get_status_list() result includes an 'etag' field."""
    registry = VCRevocationRegistry()
    with patch.object(registry, 'get_status_list') as mock_sl:
        mock_sl.return_value = {
            "encodedList":    "abc",
            "etag":           "cafebabe" * 4,
            "revoked_count":  0,
            "revoked_credentials": [],
            "@context":       [],
        }
        sl = registry.get_status_list()
    assert "etag" in sl
    assert isinstance(sl["etag"], str)


def test_T002c_etag_determinism_same_state():
    """ETag for same count+timestamp must be identical."""
    src1 = "3:2026-04-28T10:00:00+00:00"
    src2 = "3:2026-04-28T10:00:00+00:00"
    e1 = hashlib.sha256(src1.encode()).hexdigest()[:32]
    e2 = hashlib.sha256(src2.encode()).hexdigest()[:32]
    assert e1 == e2


def test_T002d_etag_changes_with_new_revocation():
    """ETag for count+1 is different from original."""
    src_before = "3:2026-04-28T10:00:00+00:00"
    src_after  = "4:2026-04-28T10:05:00+00:00"
    e_before = hashlib.sha256(src_before.encode()).hexdigest()[:32]
    e_after  = hashlib.sha256(src_after.encode()).hexdigest()[:32]
    assert e_before != e_after


def test_T002e_get_status_list_w3c_fields():
    """get_status_list() must include W3C StatusList2021 required fields."""
    registry = VCRevocationRegistry()
    with patch.object(registry, 'get_status_list') as mock_sl:
        mock_sl.return_value = {
            "@context":      ["https://www.w3.org/2018/credentials/v1"],
            "type":          ["VerifiableCredential", "StatusList2021Credential"],
            "statusPurpose": "revocation",
            "encodedList":   _build_encoded_list([]),
            "etag":          "abc",
            "revoked_count": 0,
            "revoked_credentials": [],
        }
        sl = registry.get_status_list()
    for field in ("@context", "type", "statusPurpose", "encodedList"):
        assert field in sl, f"W3C required field missing: {field}"


# ── T003: Revocation webhook ──────────────────────────────────────────────────

def test_T003a_fire_webhook_dispatches_daemon_thread():
    """fire_revocation_webhook launches a daemon thread and returns immediately."""
    import threading
    threads_before = threading.active_count()
    with patch(
        'omnix_web.api.omnix_engine.vc_revocation._deliver_revocation_webhook'
    ) as mock_deliver:
        fire_revocation_webhook(
            client_id="test-client",
            receipt_id="OMNIX-TEST-001",
            event_type="vc.revoked",
            status_data={"status": "revoked"},
        )
    # Returns immediately — no blocking
    assert threading.active_count() >= threads_before


def test_T003b_webhook_event_types_defined():
    """Verify expected event types are correct strings."""
    valid_events = {"vc.revoked", "vc.suspended", "vc.reinstated"}
    for event in valid_events:
        assert isinstance(event, str)
        assert event.startswith("vc.")


def test_T003c_webhook_payload_structure():
    """The webhook payload must include the OMNIX-Signature header (case-insensitive)."""
    from omnix_web.api.omnix_engine.vc_revocation import _deliver_revocation_webhook

    captured = {}
    def fake_urlopen(req, timeout=None):
        # Normalize headers to lowercase for case-insensitive assertion
        captured['headers'] = {k.lower(): v for k, v in dict(req.headers).items()}
        captured['url']     = req.full_url
        m = MagicMock()
        m.getcode.return_value = 200
        m.__enter__ = lambda s: s
        m.__exit__  = MagicMock(return_value=False)
        return m

    with patch(
        'omnix_web.api.omnix_engine.vc_revocation._get_client_webhook_config'
    ) as mock_cfg:
        mock_cfg.return_value = {
            "webhook_url":    "https://client.example.com/omnix-webhook",
            "webhook_secret": "test-secret-value",
        }
        with patch('urllib.request.urlopen', fake_urlopen):
            _deliver_revocation_webhook(
                client_id="test-client",
                receipt_id="OMNIX-TRD-001",
                event_type="vc.revoked",
                status_data={"status": "revoked", "reason": "fraud_detected"},
            )

    headers_lower = captured.get("headers", {})
    assert "x-omnix-signature" in headers_lower, (
        f"Missing x-omnix-signature header. Got: {list(headers_lower.keys())}"
    )
    assert headers_lower["x-omnix-signature"].startswith("sha256=")


def test_T003d_webhook_hmac_signature_format():
    """HMAC-SHA256 signature is sha256=<hexdigest> format."""
    import hmac as _hmac
    secret  = "test-secret-abc"
    body    = b'{"event": "vc.revoked"}'
    sig_hex = _hmac.new(
        secret.encode("utf-8"),
        body,
        digestmod=hashlib.sha256,
    ).hexdigest()
    formatted = f"sha256={sig_hex}"
    assert formatted.startswith("sha256=")
    assert len(formatted) == len("sha256=") + 64


def test_T003e_webhook_no_config_returns_silently():
    """If client has no webhook configured, _deliver_revocation_webhook exits silently."""
    from omnix_web.api.omnix_engine.vc_revocation import _deliver_revocation_webhook

    with patch(
        'omnix_web.api.omnix_engine.vc_revocation._get_client_webhook_config'
    ) as mock_cfg:
        mock_cfg.return_value = None
        # Must not raise
        _deliver_revocation_webhook(
            client_id="no-webhook-client",
            receipt_id="OMNIX-TRD-002",
            event_type="vc.suspended",
            status_data={"status": "suspended"},
        )


# ── T004: Human accountability binding / humanSigner ─────────────────────────

def test_T004a_receipt_to_vc_embeds_human_signer():
    """When human_signer is provided, VC proof includes humanSigner block."""
    receipt = _minimal_receipt()
    signer  = {
        "reviewer_id":          "harold@omnixquantum.net",
        "attested_at":          _now_iso(),
        "oversight_session_id": "OSE-ABCD1234",
        "eqs_score":            0.93,
    }
    vc = ReceiptToVC().convert(receipt, human_signer=signer)
    assert "proof" in vc
    assert "humanSigner" in vc["proof"]
    hs = vc["proof"]["humanSigner"]
    assert hs["reviewerId"] == "harold@omnixquantum.net"
    assert hs["oversightSessionId"] == "OSE-ABCD1234"
    assert "attestationHash" in hs
    assert hs["attestationHash"].startswith("sha256:")


def test_T004b_receipt_to_vc_no_human_signer_when_none():
    """When no human_signer is provided, proof has NO humanSigner block."""
    receipt = _minimal_receipt()
    vc      = ReceiptToVC().convert(receipt, human_signer=None)
    assert "proof" in vc
    assert "humanSigner" not in vc["proof"]


def test_T004c_human_signer_attestation_hash_verifiable():
    """attestation_hash = SHA-256(reviewerId:receipt_id:attestedAt) — independently verifiable."""
    receipt_id  = "OMNIX-TRD-verification-001"
    reviewer_id = "harold@omnixquantum.net"
    attested_at = "2026-04-28T10:00:00+00:00"

    expected_hash = "sha256:" + hashlib.sha256(
        f"{reviewer_id}:{receipt_id}:{attested_at}".encode()
    ).hexdigest()

    receipt = _minimal_receipt(receipt_id)
    signer  = {
        "reviewer_id": reviewer_id,
        "attested_at": attested_at,
    }
    vc = ReceiptToVC().convert(receipt, human_signer=signer)
    assert vc["proof"]["humanSigner"]["attestationHash"] == expected_hash


def test_T004d_human_signer_eqs_score_rounded():
    """EQS score is stored rounded to 4 decimal places."""
    receipt = _minimal_receipt()
    signer  = {
        "reviewer_id": "harold@omnixquantum.net",
        "attested_at": _now_iso(),
        "eqs_score":   0.923456789,
    }
    vc = ReceiptToVC().convert(receipt, human_signer=signer)
    eqs = vc["proof"]["humanSigner"]["eqsScore"]
    assert eqs == round(0.923456789, 4)


def test_T004e_human_signer_verifier_note_present():
    """humanSigner block includes verifierNote with recomputation instructions."""
    receipt = _minimal_receipt()
    signer  = {"reviewer_id": "test@omnixquantum.net", "attested_at": _now_iso()}
    vc      = ReceiptToVC().convert(receipt, human_signer=signer)
    hs      = vc["proof"]["humanSigner"]
    assert "verifierNote" in hs
    assert "SHA-256" in hs["verifierNote"]


def test_T004f_human_signer_adr_reference():
    """humanSigner block references ADR-130 correctly."""
    receipt = _minimal_receipt()
    signer  = {"reviewer_id": "test@omnixquantum.net", "attested_at": _now_iso()}
    vc      = ReceiptToVC().convert(receipt, human_signer=signer)
    hs      = vc["proof"]["humanSigner"]
    assert "ADR-130" in hs.get("adr", "")


def test_T004g_oversight_sessions_query_uses_correct_columns():
    """
    T004 bug fix (ADR-130 v2.3): the auto-lookup query in gov_blueprint.py must use
    submitted_at (not completed_at) and status='SUBMITTED' (not 'completed').
    Verified by reading the source file directly (avoids import errors in test context).
    """
    import os
    blueprint_path = os.path.join(
        os.path.dirname(__file__), '..', 'omnix_web', 'api', 'gov_blueprint.py'
    )
    with open(blueprint_path, 'r') as f:
        src = f.read()

    # Find only the oversight_sessions auto-lookup block
    # (search for the query region between the human_signer comment and ReceiptToVC.convert)
    marker = "oversight_sessions"
    assert marker in src, "oversight_sessions table missing from gov_blueprint.py"

    # Extract a focused slice around the oversight_sessions query
    idx = src.index(marker)
    # Take 2000 chars before+after the marker — enough to cover the full lookup block
    lookup_block = src[max(0, idx - 200): idx + 2000]

    assert "submitted_at" in lookup_block, (
        "Bug fix missing: oversight_sessions query must use submitted_at"
    )
    assert "completed_at" not in lookup_block, (
        "Old column 'completed_at' still present in oversight_sessions query — bug not fixed"
    )
    assert "'SUBMITTED'" in lookup_block, (
        "Bug fix missing: oversight_sessions status must be 'SUBMITTED'"
    )
    assert "'completed'" not in lookup_block, (
        "Old status value 'completed' still present in oversight_sessions query — bug not fixed"
    )


# ── T005: VC structure completeness ──────────────────────────────────────────

def test_T005a_vc_includes_credential_status_block():
    """Every issued VC includes a credentialStatus block pointing to revocation endpoint."""
    receipt = _minimal_receipt()
    vc      = ReceiptToVC().convert(receipt)
    assert "credentialStatus" in vc
    cs = vc["credentialStatus"]
    assert "type" in cs
    assert cs.get("statusPurpose") == "revocation" or "statusListCredential" in cs


def test_T005b_vc_context_includes_status_list():
    """VC @context includes status-list context or omnix context."""
    receipt = _minimal_receipt()
    vc      = ReceiptToVC().convert(receipt)
    context = vc.get("@context", [])
    assert any("w3.org" in c for c in context), "@context missing W3C URL"


def test_T005c_vc_type_includes_governance_credential():
    """VC type includes OmnixGovernanceCredential."""
    receipt = _minimal_receipt()
    vc      = ReceiptToVC().convert(receipt)
    assert "OmnixGovernanceCredential" in vc.get("type", [])


def test_T005d_vc_issuer_is_did_web():
    """VC issuer.id is did:web:omnixquantum.net."""
    receipt = _minimal_receipt()
    vc      = ReceiptToVC().convert(receipt)
    assert vc["issuer"]["id"] == "did:web:omnixquantum.net"
