from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

from .exceptions import (
    OmnixAuthError,
    OmnixGovernanceBlock,
    OmnixNetworkError,
    OmnixRateLimitError,
    OmnixServerError,
    OmnixValidationError,
)
from .models import GovernanceReceipt

_DEFAULT_BASE_URL = "https://omnixquantum.net"
_SDK_VERSION      = "1.0.0"


class OmnixClient:
    """
    OMNIX Governance SDK — Python client.

    Usage:
        from omnix import OmnixClient

        client = OmnixClient(api_key="OMNIX-...")
        receipt = client.evaluate(
            domain="trading",
            asset="BTC/USD",
            signals={"price": 94200, "volume": 1.5, "volatility": 0.18},
        )
        print(receipt)       # ✅ APPROVED | OMNIX-TRD-... | 11/11 gates passed
        print(receipt.approved)          # True
        print(receipt.content_hash)      # sha256:...
        print(receipt.signature_algorithm)  # Dilithium-3 (NIST FIPS 204)
    """

    def __init__(
        self,
        api_key:  str,
        base_url: str  = _DEFAULT_BASE_URL,
        timeout:  int  = 30,
        raise_on_block: bool = False,
    ):
        """
        Args:
            api_key:        Your OMNIX API key (OMNIX-...).
            base_url:       Base URL of the OMNIX server.
            timeout:        Request timeout in seconds.
            raise_on_block: If True, raise OmnixGovernanceBlock when decision=BLOCKED.
                            If False (default), return the receipt normally.
        """
        if not api_key or not api_key.startswith("OMNIX-"):
            raise OmnixAuthError(
                "Invalid API key format. Expected: OMNIX-<key>. "
                "Get yours at omnixquantum.net or contact us at omnixquantum.net."
            )
        self._api_key       = api_key
        self._base_url      = base_url.rstrip("/")
        self._timeout       = timeout
        self._raise_on_block = raise_on_block

    # ── Public API ──────────────────────────────────────────────────────────

    def evaluate(
        self,
        domain:  str,
        asset:   str,
        signals: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> GovernanceReceipt:
        """
        Evaluate a governance decision through OMNIX.

        Args:
            domain:  Governance domain (trading | islamic_credit | insurance |
                     energy | robotics | medical | real_estate | agents | stablecoin)
            asset:   Asset or subject identifier (e.g., "BTC/USD", "SME-AE-001")
            signals: Domain-specific signals dict.
            context: Optional extra context (jurisdiction override, metadata, etc.)

        Returns:
            GovernanceReceipt — the signed, immutable governance receipt.

        Raises:
            OmnixAuthError:        Invalid API key.
            OmnixValidationError:  Malformed request payload.
            OmnixGovernanceBlock:  Decision was BLOCKED (only if raise_on_block=True).
            OmnixRateLimitError:   Too many requests.
            OmnixServerError:      Unexpected server error.
            OmnixNetworkError:     Cannot reach the OMNIX server.
        """
        payload: Dict[str, Any] = {
            "domain":  domain,
            "asset":   asset,
            "signals": signals,
        }
        if context:
            payload["context"] = context

        raw = self._post("/api/governance/evaluate", payload)
        receipt = GovernanceReceipt.from_dict(raw)

        if self._raise_on_block and receipt.blocked:
            raise OmnixGovernanceBlock(raw)

        return receipt

    def verify(self, receipt_id: str) -> Dict[str, Any]:
        """
        Verify a receipt by ID using the stateless OMNIX trust endpoint.
        Does not require DB access — purely cryptographic verification.

        Returns:
            dict with hash_valid, signature_valid, overall_valid, issuer_did.
        """
        return self._get(f"/api/trust/verify/{receipt_id}")

    def get_receipt(self, receipt_id: str) -> GovernanceReceipt:
        """Fetch a receipt by ID from the OMNIX explorer."""
        raw = self._get(f"/api/explorer/receipt/{receipt_id}")
        return GovernanceReceipt.from_dict(raw)

    def trust_registry(self) -> Dict[str, Any]:
        """
        Fetch the public OMNIX trust registry.
        No authentication required — public endpoint.
        """
        return self._get("/api/trust/registry", authenticated=False)

    def public_key(self) -> Dict[str, Any]:
        """
        Fetch the current OMNIX signing public key (RFC 8615 well-known).
        No authentication required — public endpoint.
        """
        return self._get("/.well-known/omnix-public-key.json", authenticated=False)

    # ── Internal ────────────────────────────────────────────────────────────

    def _headers(self, authenticated: bool = True) -> Dict[str, str]:
        h = {
            "Content-Type": "application/json",
            "User-Agent":   f"omnix-python-sdk/{_SDK_VERSION}",
            "Accept":       "application/json",
        }
        if authenticated:
            h["X-API-Key"] = self._api_key
        return h

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url  = f"{self._base_url}{path}"
        body = json.dumps(payload).encode("utf-8")
        req  = urllib.request.Request(url, data=body, headers=self._headers(), method="POST")
        return self._execute(req)

    def _get(self, path: str, authenticated: bool = True) -> Dict[str, Any]:
        url = f"{self._base_url}{path}"
        req = urllib.request.Request(url, headers=self._headers(authenticated), method="GET")
        return self._execute(req)

    def _execute(self, req: urllib.request.Request) -> Dict[str, Any]:
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = {}
            try:
                body = json.loads(e.read().decode("utf-8"))
            except Exception:
                pass
            status = e.code
            if status == 401:
                raise OmnixAuthError("Invalid API key. Check your OMNIX-... key.") from e
            if status == 422:
                raise OmnixValidationError(
                    body.get("detail", "Validation error"),
                    errors=body.get("errors", []),
                ) from e
            if status == 429:
                retry = int(e.headers.get("Retry-After", 60))
                raise OmnixRateLimitError(retry_after=retry) from e
            raise OmnixServerError(status, body.get("error", str(e))) from e
        except urllib.error.URLError as e:
            raise OmnixNetworkError(
                f"Cannot reach OMNIX at {self._base_url}. Check your connection."
            ) from e
