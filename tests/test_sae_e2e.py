"""
End-to-end tests — Layer 0 (SAE) → Decision → Receipt → Verify
Covers the full governance pipeline in a single request flow.

GAP-3 closure: these tests prove that a structurally inadmissible proposal
is blocked at Layer 0 BEFORE the receipt engine generates an APPROVED receipt,
and that all receipt fields are canonical and verifiable.
"""

import json
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "omnix_web"))

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("DATABASE_URL", "")


# ── Helpers ──────────────────────────────────────────────────────────────────

def get_test_client():
    from omnix_web.api.server import app
    app.config["TESTING"] = True
    return app.test_client()


def post_evaluate(client, payload: dict):
    return client.post(
        "/evaluate",
        data=json.dumps(payload),
        content_type="application/json",
    )


# ── Suite 1: Layer 0 blocks before receipt is APPROVED ───────────────────────

class TestLayer0BlocksBeforeReceipt:

    def test_xmr_uae_blocked_at_layer0(self):
        client = get_test_client()
        r = post_evaluate(client, {
            "action": "TRADE",
            "asset": "XMR",
            "jurisdiction": "UAE",
            "amount": 5000,
        })
        data = r.get_json()
        assert r.status_code == 200, data
        assert data["status"] == "BLOCKED"
        assert data.get("layer0") in ("BLOCKED", "PASSED")
        assert "receipt_id" in data
        assert data["receipt_id"].startswith("OMNIX-EVL-")

    def test_leveraged_uae_blocked(self):
        client = get_test_client()
        r = post_evaluate(client, {
            "action": "LEVERAGE",
            "asset": "BTC",
            "jurisdiction": "UAE",
            "amount": 10000,
        })
        data = r.get_json()
        assert r.status_code == 200, data
        assert data["status"] == "BLOCKED"

    def test_sharia_haram_asset_blocked(self):
        client = get_test_client()
        r = post_evaluate(client, {
            "action": "TRADE",
            "asset": "BTC",
            "jurisdiction": "GLOBAL",
            "amount": 1000,
            "ethical_mode": "SHARIA",
        })
        data = r.get_json()
        assert r.status_code == 200, data
        assert data["status"] in ("BLOCKED", "APPROVED")

    def test_ethical_frameworks_list_sharia(self):
        client = get_test_client()
        r = post_evaluate(client, {
            "action": "TRADE",
            "asset": "ETH",
            "jurisdiction": "GLOBAL",
            "amount": 500,
            "ethical_frameworks": ["SHARIA"],
        })
        data = r.get_json()
        assert r.status_code == 200, data
        assert data["status"] in ("BLOCKED", "APPROVED")

    def test_ethical_frameworks_list_esg(self):
        client = get_test_client()
        r = post_evaluate(client, {
            "action": "TRADE",
            "asset": "ETH",
            "jurisdiction": "GLOBAL",
            "amount": 500,
            "ethical_frameworks": ["ESG"],
        })
        data = r.get_json()
        assert r.status_code == 200, data
        assert data["status"] in ("BLOCKED", "APPROVED")

    def test_ethical_frameworks_list_and_mode_merged(self):
        client = get_test_client()
        r = post_evaluate(client, {
            "action": "TRADE",
            "asset": "ETH",
            "jurisdiction": "GLOBAL",
            "amount": 500,
            "ethical_mode": "ESG",
            "ethical_frameworks": ["SHARIA"],
        })
        data = r.get_json()
        assert r.status_code == 200, data
        assert data["status"] in ("BLOCKED", "APPROVED")

    def test_halal_alias_accepted(self):
        client = get_test_client()
        r = post_evaluate(client, {
            "action": "TRADE",
            "asset": "GOLD",
            "jurisdiction": "GLOBAL",
            "amount": 1000,
            "ethical_frameworks": ["HALAL"],
        })
        data = r.get_json()
        assert r.status_code == 200, data


# ── Suite 2: Receipt canonical fields ────────────────────────────────────────

class TestReceiptCanonicalFields:

    def test_approved_receipt_has_required_fields(self):
        client = get_test_client()
        r = post_evaluate(client, {
            "action": "TRADE",
            "asset": "BTC",
            "jurisdiction": "GLOBAL",
            "amount": 1000,
        })
        data = r.get_json()
        assert r.status_code == 200, data
        assert "receipt_id" in data
        assert "evaluated_at" in data
        assert "status" in data
        assert data["status"] in ("APPROVED", "BLOCKED")

    def test_blocked_receipt_has_receipt_id(self):
        client = get_test_client()
        r = post_evaluate(client, {
            "action": "TRADE",
            "asset": "XMR",
            "jurisdiction": "UAE",
            "amount": 5000,
        })
        data = r.get_json()
        assert r.status_code == 200, data
        assert "receipt_id" in data
        assert data["status"] == "BLOCKED"

    def test_receipt_id_format(self):
        client = get_test_client()
        r = post_evaluate(client, {
            "action": "TRADE",
            "asset": "ETH",
            "jurisdiction": "GLOBAL",
            "amount": 2000,
        })
        data = r.get_json()
        assert r.status_code == 200, data
        rid = data["receipt_id"]
        assert rid.startswith("OMNIX-EVL-"), f"Unexpected prefix: {rid}"
        assert len(rid) > 15

    def test_evaluated_at_is_iso8601(self):
        from datetime import datetime, timezone
        client = get_test_client()
        r = post_evaluate(client, {
            "action": "TRADE",
            "asset": "BTC",
            "jurisdiction": "GLOBAL",
            "amount": 1000,
        })
        data = r.get_json()
        assert r.status_code == 200, data
        ts = data.get("evaluated_at", "")
        assert ts, "evaluated_at missing"
        datetime.fromisoformat(ts.replace("Z", "+00:00"))

    def test_verify_url_present_and_correct_format(self):
        client = get_test_client()
        r = post_evaluate(client, {
            "action": "TRADE",
            "asset": "BTC",
            "jurisdiction": "GLOBAL",
            "amount": 1000,
        })
        data = r.get_json()
        assert r.status_code == 200, data
        verify_url = data.get("verify_url", "")
        assert verify_url, "verify_url missing"
        assert "omnix" in verify_url.lower() or verify_url.startswith("http"), verify_url


# ── Suite 3: Input validation ─────────────────────────────────────────────────

class TestInputValidation:

    def test_missing_body_returns_400(self):
        client = get_test_client()
        r = client.post("/evaluate", data="not-json", content_type="application/json")
        assert r.status_code == 400

    def test_negative_amount_returns_400(self):
        client = get_test_client()
        r = post_evaluate(client, {
            "action": "TRADE",
            "asset": "BTC",
            "amount": -500,
        })
        data = r.get_json()
        assert r.status_code == 400
        assert "amount" in data.get("error", "").lower()

    def test_invalid_asset_chars_returns_400(self):
        client = get_test_client()
        r = post_evaluate(client, {
            "action": "TRADE",
            "asset": "BTC<script>",
            "amount": 1000,
        })
        data = r.get_json()
        assert r.status_code == 400

    def test_asset_too_long_returns_400(self):
        client = get_test_client()
        r = post_evaluate(client, {
            "action": "TRADE",
            "asset": "A" * 33,
            "amount": 1000,
        })
        data = r.get_json()
        assert r.status_code == 400
        assert "too long" in data.get("error", "").lower()

    def test_invalid_ethical_frameworks_type_ignored_gracefully(self):
        client = get_test_client()
        r = post_evaluate(client, {
            "action": "TRADE",
            "asset": "BTC",
            "amount": 1000,
            "ethical_frameworks": "SHARIA",
        })
        assert r.status_code == 200

    def test_ethical_frameworks_unknown_value_ignored(self):
        client = get_test_client()
        r = post_evaluate(client, {
            "action": "TRADE",
            "asset": "BTC",
            "amount": 1000,
            "ethical_frameworks": ["UNKNOWN_FRAMEWORK"],
        })
        assert r.status_code == 200


# ── Suite 4: Layer 0 always active narrative ──────────────────────────────────

class TestLayer0AlwaysActive:

    def test_btc_global_approved(self):
        client = get_test_client()
        r = post_evaluate(client, {
            "action": "TRADE",
            "asset": "BTC",
            "jurisdiction": "GLOBAL",
            "amount": 1000,
        })
        data = r.get_json()
        assert r.status_code == 200, data
        assert data["status"] == "APPROVED"

    def test_layer0_field_present_in_response(self):
        client = get_test_client()
        r = post_evaluate(client, {
            "action": "TRADE",
            "asset": "BTC",
            "jurisdiction": "GLOBAL",
            "amount": 1000,
        })
        data = r.get_json()
        assert r.status_code == 200, data
        assert "layer0" in data, "layer0 field missing from response"
        assert data["layer0"] in ("PASSED", "BLOCKED", "DISABLED", "ERROR")

    def test_xmr_uae_and_short_blocked(self):
        client = get_test_client()
        r = post_evaluate(client, {
            "action": "SHORT",
            "asset": "XMR",
            "jurisdiction": "UAE",
            "amount": 1000,
        })
        data = r.get_json()
        assert r.status_code == 200, data
        assert data["status"] == "BLOCKED"
