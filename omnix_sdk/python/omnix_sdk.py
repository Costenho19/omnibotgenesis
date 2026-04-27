"""
OMNIX Python SDK — v2.0.0
==========================

Official client library for the OMNIX Decision Governance API.
Production endpoint: https://omnixquantum.net

Zero external dependencies. Python 3.8+.

Quick start:
    from omnix_sdk import OmnixClient

    client = OmnixClient(api_key="OMNIX-your-key-here")

    # 1. Govern a decision
    receipt = client.evaluate({
        "signal_integrity": 75, "probability_score": 68,
        "risk_exposure": 42,    "signal_coherence": 60,
        "trend_persistence": 55,"stress_resilience": 48,
        "logic_consistency": 65,"temporal_coherence": 58,
        "domain": "trading",    "asset": "BTC/USD",
        "scenario": "Long position — 2% capital",
    })
    print(receipt["decision"])    # APPROVED | BLOCKED | HOLD
    print(receipt["receipt_id"])  # OMNIX-a3f8e2...

    # 2. Log the execution result
    exec_receipt = client.execute(
        decision_receipt_id = receipt["receipt_id"],
        order_id            = "ORD-001",
        symbol              = "BTC/USD",
        side                = "BUY",
        size_usd            = 10_000.0,
        final_status        = "FILLED",
        executed_price      = 65_100.0,
        filled_quantity     = 0.15,
    )

    # 3. Issue a W3C Verifiable Credential
    vc = client.get_vc(receipt["receipt_id"])

    # 4. Verify the receipt (PQC)
    result = client.verify(receipt["receipt_id"])

    # 5. Revoke (admin only)
    client.revoke(receipt["receipt_id"], reason="Assumption invalidated by AVM")

Author:  OMNIX Quantum Ltd — Harold Alberto Nunes Rodelo
Spec:    ADR-132 — SDK Public API Surface
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

__version__ = "2.0.0"
__author__  = "OMNIX Quantum Ltd"
__all__     = [
    "OmnixClient",
    "OmnixError",
    "OmnixAuthError",
    "OmnixNotFoundError",
    "OmnixValidationError",
    "OmnixRateLimitError",
    "OmnixTimeoutError",
    "OmnixServerError",
    "OmnixAPIError",
]

# ── Exception hierarchy ────────────────────────────────────────────────────────

class OmnixError(Exception):
    """Base class for all OMNIX SDK errors."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class OmnixAuthError(OmnixError):
    """
    Authentication failed.
    Causes: missing key, invalid key format, revoked key, wrong permissions.
    """


class OmnixNotFoundError(OmnixError):
    """
    The requested resource does not exist.
    Causes: unknown receipt_id, expired resource, wrong client scope.
    """


class OmnixValidationError(OmnixError):
    """
    Request body failed server-side validation.
    Causes: missing required fields, out-of-range values, invalid enums.
    """


class OmnixRateLimitError(OmnixError):
    """
    Rate limit exceeded.
    Default: 200 requests per minute per API key.
    Retry after 60 seconds or inspect the Retry-After response header.
    """
    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class OmnixTimeoutError(OmnixError):
    """Request timed out before the server responded."""
    def __init__(self, message: str = "Request timed out"):
        super().__init__(message, status_code=408)


class OmnixServerError(OmnixError):
    """
    Unexpected server-side error (5xx).
    OMNIX Quantum Ltd has been automatically notified.
    """


class OmnixAPIError(OmnixError):
    """Catch-all for API errors not covered by specific subclasses."""


# ── Signal field reference ─────────────────────────────────────────────────────

REQUIRED_SIGNALS: List[str] = [
    "signal_integrity",
    "probability_score",
    "risk_exposure",
    "signal_coherence",
    "trend_persistence",
    "stress_resilience",
    "logic_consistency",
    "temporal_coherence",
]

SUPPORTED_DOMAINS: List[str] = [
    "trading", "credit", "insurance", "robotics",
    "medical", "energy", "real_estate", "stablecoin", "agents",
]

EXECUTION_STATUSES: List[str] = ["FILLED", "PARTIAL", "FAILED"]


# ── Client ─────────────────────────────────────────────────────────────────────

class OmnixClient:
    """
    OMNIX Decision Governance API client.

    Covers the full OMNIX audit chain:
      evaluate()  → govern a decision, get a signed receipt
      execute()   → log the execution result, seal the audit chain
      verify()    → verify receipt integrity (PQC Dilithium-3)
      get_vc()    → issue a W3C Verifiable Credential for a receipt
      revoke()    → revoke a VC (admin only)
      reinstate() → reinstate a revoked VC (admin only)

    Parameters
    ----------
    api_key : str
        Your OMNIX API key (format: ``OMNIX-<40 chars>``).
        Falls back to the ``OMNIX_API_KEY`` environment variable if not provided.
    base_url : str
        API base URL. Defaults to ``https://omnixquantum.net``.
        Override via ``OMNIX_BASE_URL`` environment variable.
    timeout : int
        Per-request timeout in seconds. Default: 30.
    max_retries : int
        Maximum number of automatic retries on transient failures (429, 503).
        Default: 3. Set to 0 to disable retries.
    retry_backoff : float
        Base backoff in seconds between retries (exponential). Default: 1.0.

    Example
    -------
    ::

        # Via constructor
        client = OmnixClient(api_key="OMNIX-your-key-here")

        # Via environment variable
        os.environ["OMNIX_API_KEY"] = "OMNIX-your-key-here"
        client = OmnixClient()

        # As context manager
        with OmnixClient(api_key="OMNIX-your-key-here") as client:
            result = client.evaluate(signals)
    """

    DEFAULT_BASE_URL = "https://omnixquantum.net"

    def __init__(
        self,
        api_key      : Optional[str] = None,
        base_url     : Optional[str] = None,
        timeout      : int           = 30,
        max_retries  : int           = 3,
        retry_backoff: float         = 1.0,
    ):
        resolved_key = api_key or os.environ.get("OMNIX_API_KEY", "")
        if not resolved_key:
            raise OmnixAuthError(
                "No API key provided. Pass api_key= or set the OMNIX_API_KEY "
                "environment variable."
            )
        if not resolved_key.startswith("OMNIX-"):
            raise OmnixValidationError(
                f"Invalid API key format. Expected OMNIX-<key>, got: {resolved_key[:10]}..."
            )
        if timeout < 1:
            raise ValueError("timeout must be >= 1 second")
        if max_retries < 0:
            raise ValueError("max_retries must be >= 0")

        self._api_key      = resolved_key
        self._base_url     = (base_url or os.environ.get("OMNIX_BASE_URL", self.DEFAULT_BASE_URL)).rstrip("/")
        self._timeout      = timeout
        self._max_retries  = max_retries
        self._retry_backoff = retry_backoff

    # ── Context manager ──────────────────────────────────────────────────────

    def __enter__(self) -> "OmnixClient":
        return self

    def __exit__(self, *args) -> None:
        pass

    def __repr__(self) -> str:
        key_preview = self._api_key[:12] + "..." if len(self._api_key) > 12 else self._api_key
        return (
            f"OmnixClient(api_key={key_preview!r}, "
            f"base_url={self._base_url!r}, "
            f"timeout={self._timeout})"
        )

    # ── Internal HTTP layer ──────────────────────────────────────────────────

    def _request(
        self,
        method : str,
        path   : str,
        body   : Optional[Dict[str, Any]] = None,
        params : Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute an authenticated HTTP request with automatic retry on transient errors.

        Retries on:
          - 429 Rate Limit (respects Retry-After header)
          - 503 Service Unavailable (Railway cold start / deploy)

        Raises on:
          - 401 → OmnixAuthError
          - 403 → OmnixAuthError (insufficient permissions)
          - 404 → OmnixNotFoundError
          - 422 → OmnixValidationError
          - 408 / timeout → OmnixTimeoutError
          - 5xx → OmnixServerError
          - Other 4xx → OmnixAPIError
        """
        query = ""
        if params:
            query = "?" + "&".join(
                f"{k}={v}" for k, v in params.items() if v is not None
            )
        url     = f"{self._base_url}{path}{query}"
        headers = {
            "X-API-Key"    : self._api_key,
            "Content-Type" : "application/json",
            "Accept"       : "application/json",
            "User-Agent"   : f"omnix-python-sdk/{__version__}",
        }
        data = json.dumps(body).encode("utf-8") if body else None
        req  = urllib.request.Request(url, data=data, headers=headers, method=method)

        last_error: Optional[Exception] = None
        for attempt in range(self._max_retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                    raw = resp.read().decode("utf-8")
                    try:
                        return json.loads(raw)
                    except json.JSONDecodeError:
                        return {"raw": raw}

            except urllib.error.HTTPError as exc:
                status = exc.code
                try:
                    err_body  = json.loads(exc.read().decode("utf-8"))
                    err_msg   = err_body.get("error") or err_body.get("message") or str(exc)
                except Exception:
                    err_msg   = str(exc)

                if status == 401:
                    raise OmnixAuthError(f"Authentication failed: {err_msg}", 401) from exc
                if status == 403:
                    raise OmnixAuthError(f"Insufficient permissions: {err_msg}", 403) from exc
                if status == 404:
                    raise OmnixNotFoundError(f"Not found: {err_msg}", 404) from exc
                if status == 422:
                    raise OmnixValidationError(f"Validation error: {err_msg}", 422) from exc
                if status == 429:
                    retry_after = int(exc.headers.get("Retry-After", 60))
                    last_error  = OmnixRateLimitError(
                        f"Rate limit exceeded. Retry after {retry_after}s.",
                        retry_after=retry_after,
                    )
                    if attempt < self._max_retries:
                        time.sleep(min(retry_after, self._retry_backoff * (2 ** attempt)))
                        continue
                    raise last_error from exc
                if status == 503 and attempt < self._max_retries:
                    last_error = OmnixServerError(f"Service unavailable: {err_msg}", 503)
                    time.sleep(self._retry_backoff * (2 ** attempt))
                    continue
                if status >= 500:
                    raise OmnixServerError(f"Server error {status}: {err_msg}", status) from exc
                raise OmnixAPIError(f"API error {status}: {err_msg}", status) from exc

            except urllib.error.URLError as exc:
                reason = str(exc.reason) if hasattr(exc, "reason") else str(exc)
                if "timed out" in reason.lower():
                    raise OmnixTimeoutError(f"Request timed out after {self._timeout}s") from exc
                last_error = OmnixAPIError(f"Network error: {reason}")
                if attempt < self._max_retries:
                    time.sleep(self._retry_backoff * (2 ** attempt))
                    continue
                raise last_error from exc

        raise last_error or OmnixAPIError("Request failed after retries")

    # ── 1. Governance — evaluate ─────────────────────────────────────────────

    def evaluate(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit a decision for governance evaluation.

        OMNIX runs the decision through 11 sequential checkpoints covering
        epistemic validity, coherence, regulatory compliance, and risk limits.
        The result is a PQC-signed (Dilithium-3) governance receipt that serves
        as tamper-evident evidence for audit, compliance, and litigation.

        Parameters
        ----------
        signals : dict
            Required fields (all int, 0–100):

            +-----------------------+--------------------------------------------+
            | Field                 | Description                                |
            +=======================+============================================+
            | signal_integrity      | Input data quality — how clean is the data |
            | probability_score     | Confidence in the decision outcome         |
            | risk_exposure         | Risk level — **lower = safer**             |
            | signal_coherence      | Internal consistency of signals            |
            | trend_persistence     | Alignment with prevailing trend            |
            | stress_resilience     | Robustness under adverse conditions        |
            | logic_consistency     | Logical coherence of the decision scenario |
            | temporal_coherence    | Time-context validity                      |
            +-----------------------+--------------------------------------------+

            Optional fields:

            - ``domain`` (str): ``"trading"`` | ``"credit"`` | ``"insurance"`` |
              ``"robotics"`` | ``"medical"`` | ``"energy"`` | ``"real_estate"`` |
              ``"stablecoin"`` | ``"agents"``
            - ``asset`` (str): Asset or entity identifier (e.g. ``"BTC/USD"``)
            - ``scenario`` (str): Human-readable decision description

        Returns
        -------
        dict
            - ``decision`` (str): ``"APPROVED"`` | ``"BLOCKED"`` | ``"HOLD"``
            - ``receipt_id`` (str): Unique receipt identifier (``OMNIX-<hex>``)
            - ``pqc_signed`` (bool): Whether receipt carries a Dilithium-3 signature
            - ``checkpoints_passed`` (int): Number of governance checkpoints passed
            - ``checkpoints_total`` (int): Total checkpoints (typically 11)
            - ``summary`` (str): Executive summary of the governance outcome
            - ``regulatory_alignment`` (list): Regulatory frameworks evaluated
            - ``timestamp`` (str): ISO 8601 UTC timestamp

        Raises
        ------
        OmnixValidationError
            If required signal fields are missing or out of range.

        Example
        -------
        ::

            receipt = client.evaluate({
                "signal_integrity": 75, "probability_score": 68,
                "risk_exposure": 35,    "signal_coherence": 72,
                "trend_persistence": 60,"stress_resilience": 55,
                "logic_consistency": 70,"temporal_coherence": 65,
                "domain": "trading",
                "asset": "ETH/USD",
                "scenario": "Long position on breakout — 1.5% capital",
            })
            if receipt["decision"] == "APPROVED":
                place_order(receipt["receipt_id"])
        """
        missing = [f for f in REQUIRED_SIGNALS if f not in signals]
        if missing:
            raise OmnixValidationError(
                f"Missing required signal fields: {missing}. "
                f"All 8 numeric fields (0–100) are required."
            )
        return self._request("POST", "/api/governance/evaluate", signals)

    # ── 2. Execution integrity ───────────────────────────────────────────────

    def execute(
        self,
        decision_receipt_id : str,
        order_id            : str,
        symbol              : str,
        side                : str,
        size_usd            : float,
        final_status        : str,
        executed_price      : Optional[float]          = None,
        filled_quantity     : Optional[float]          = None,
        requested_price     : Optional[float]          = None,
        requested_quantity  : Optional[float]          = None,
        execution_style     : str                      = "MARKET",
        exchange_response   : Optional[Dict[str, Any]] = None,
        failure_reason      : str                      = "",
    ) -> Dict[str, Any]:
        """
        Log the result of a trade execution and bind it to a governance decision.

        This seals the decision→execution audit chain (ADR-131).
        Every governed decision should have a corresponding execution receipt,
        whether the trade was filled, partially filled, or failed.

        OMNIX computes and stores:
          - ``latency_ms``: time between intent and result
          - ``slippage_bps``: price drift from requested to executed
          - ``fill_ratio``: filled_quantity / requested_quantity
          - ``receipt_hash``: SHA-256 tamper-evident seal

        Parameters
        ----------
        decision_receipt_id : str
            The ``receipt_id`` returned by ``evaluate()``.
            This binds the execution to its governance decision.
        order_id : str
            Your exchange's order reference identifier.
        symbol : str
            Instrument symbol (e.g. ``"BTC/USD"``).
        side : str
            ``"BUY"`` or ``"SELL"``.
        size_usd : float
            Notional value of the order in USD.
        final_status : str
            ``"FILLED"`` | ``"PARTIAL"`` | ``"FAILED"``.
        executed_price : float, optional
            Actual fill price. Required for FILLED and PARTIAL.
        filled_quantity : float, optional
            Units actually filled. Required for FILLED and PARTIAL.
        requested_price : float, optional
            Limit price (omit for MARKET orders).
        requested_quantity : float, optional
            Units requested. Used to compute fill_ratio.
        execution_style : str, optional
            ``"MARKET"`` | ``"LIMIT"`` | ``"TWAP"`` | ``"VWAP"`` | etc.
        exchange_response : dict, optional
            Raw exchange response. Stored verbatim for audit.
        failure_reason : str, optional
            Human-readable reason. Required when final_status is ``"FAILED"``.

        Returns
        -------
        dict
            - ``receipt_id`` (str): Execution receipt identifier
            - ``decision_receipt_id`` (str): Linked governance receipt
            - ``final_status`` (str): ``FILLED`` | ``PARTIAL`` | ``FAILED``
            - ``latency_ms`` (float): Round-trip latency
            - ``slippage_bps`` (float): Price slippage in basis points
            - ``fill_ratio`` (float): Portion of order filled (0.0–1.0)
            - ``receipt_hash`` (str): SHA-256 tamper-evident seal

        Raises
        ------
        OmnixValidationError
            If ``final_status`` is invalid or required fields are missing.

        Example
        -------
        ::

            receipt = client.evaluate(signals)
            if receipt["decision"] == "APPROVED":
                resp = exchange.create_order(symbol="BTC/USD", side="buy", amount=0.15)
                exec_receipt = client.execute(
                    decision_receipt_id = receipt["receipt_id"],
                    order_id            = resp["id"],
                    symbol              = "BTC/USD",
                    side                = "BUY",
                    size_usd            = 10_000.0,
                    final_status        = "FILLED",
                    executed_price      = resp["average"],
                    filled_quantity     = resp["filled"],
                    exchange_response   = resp,
                )
        """
        if final_status not in EXECUTION_STATUSES:
            raise OmnixValidationError(
                f"Invalid final_status: {final_status!r}. "
                f"Must be one of: {EXECUTION_STATUSES}"
            )
        if final_status == "FAILED" and not failure_reason:
            raise OmnixValidationError(
                "failure_reason is required when final_status is 'FAILED'."
            )
        if final_status in ("FILLED", "PARTIAL") and executed_price is None:
            raise OmnixValidationError(
                "executed_price is required when final_status is 'FILLED' or 'PARTIAL'."
            )

        return self._request("POST", "/api/execution/receipts", {
            "decision_receipt_id" : decision_receipt_id,
            "order_id"            : order_id,
            "symbol"              : symbol,
            "side"                : side.upper(),
            "size_usd"            : size_usd,
            "final_status"        : final_status,
            "executed_price"      : executed_price,
            "filled_quantity"     : filled_quantity,
            "requested_price"     : requested_price,
            "requested_quantity"  : requested_quantity,
            "execution_style"     : execution_style,
            "exchange_response"   : exchange_response or {},
            "failure_reason"      : failure_reason,
        })

    def get_execution_receipt(self, receipt_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific execution receipt by its ID.

        Parameters
        ----------
        receipt_id : str
            The execution receipt identifier returned by ``execute()``.

        Returns
        -------
        dict
            Full execution receipt including latency, slippage, fill_ratio,
            receipt_hash, and the full audit trail.
        """
        return self._request("GET", f"/api/execution/receipts/{receipt_id}")

    # ── 3. Receipts ──────────────────────────────────────────────────────────

    def get_receipt(self, receipt_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific governance receipt by ID.

        Parameters
        ----------
        receipt_id : str
            Receipt identifier returned by ``evaluate()``.

        Returns
        -------
        dict
            Full receipt including checkpoint results, PQC signature,
            epistemic transparency score, and regulatory alignment.

        Raises
        ------
        OmnixNotFoundError
            If the receipt does not exist or does not belong to your API key.
        """
        return self._request("GET", f"/api/governance/receipts/{receipt_id}")

    def list_receipts(
        self,
        page     : int           = 1,
        per_page : int           = 20,
        domain   : Optional[str] = None,
        asset    : Optional[str] = None,
        decision : Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List your governance receipts (paginated, most recent first).

        Parameters
        ----------
        page : int
            Page number (1-indexed). Default: 1.
        per_page : int
            Results per page (max 100). Default: 20.
        domain : str, optional
            Filter by domain (e.g. ``"trading"``).
        asset : str, optional
            Filter by asset (e.g. ``"BTC/USD"``).
        decision : str, optional
            Filter by decision: ``"APPROVED"`` | ``"BLOCKED"`` | ``"HOLD"``.

        Returns
        -------
        dict
            - ``receipts`` (list): List of receipt summary objects
            - ``total`` (int): Total matching receipts
            - ``page`` (int): Current page
            - ``per_page`` (int): Results per page
        """
        return self._request("GET", "/api/governance/receipts", params={
            "page"    : page,
            "per_page": per_page,
            "domain"  : domain,
            "asset"   : asset,
            "decision": decision,
        })

    # ── 4. Verification ──────────────────────────────────────────────────────

    def verify(self, receipt_id: str) -> Dict[str, Any]:
        """
        Cryptographically verify a governance receipt.

        Runs a full verification pass:
          - SHA-256 content hash integrity check
          - PQC Dilithium-3 signature verification
          - Tamper detection on decision fields
          - Timestamp and domain consistency

        Parameters
        ----------
        receipt_id : str
            The receipt identifier to verify.

        Returns
        -------
        dict
            - ``valid`` (bool): True if receipt passes all checks
            - ``receipt_id`` (str): Verified receipt identifier
            - ``signature_valid`` (bool): PQC signature verification result
            - ``hash_valid`` (bool): Content hash integrity result
            - ``tamper_detected`` (bool): True if tampering was detected
            - ``checks`` (dict): Per-check breakdown
            - ``verified_at`` (str): ISO 8601 timestamp of verification

        Example
        -------
        ::

            result = client.verify("OMNIX-a3f8e2...")
            if not result["valid"]:
                raise Exception("Receipt integrity compromised")
        """
        return self._request("POST", "/api/trust/verify", {"receipt_id": receipt_id})

    # ── 5. Verifiable Credentials ────────────────────────────────────────────

    def get_vc(
        self,
        receipt_id   : str,
        human_signer : Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Issue a W3C Verifiable Credential for a governance receipt.

        The VC wraps the OMNIX receipt in a W3C JSON-LD envelope with:
          - issuer: ``did:web:omnixquantum.net``
          - PQC Dilithium-3 proof block
          - credentialStatus pointing to the live revocation registry
          - Optional human accountability binding (ADR-130)

        Compatible with EUDI wallets, eIDAS 2.0, and any W3C VC verifier.

        Parameters
        ----------
        receipt_id : str
            The governance receipt to wrap in a VC.
        human_signer : dict, optional
            Human accountability binding block (ADR-130 §7). If provided,
            the VC proof includes a ``humanSigner`` field.
            Fields: ``reviewer_id`` (str), ``attested_at`` (ISO 8601),
            ``oversight_session_id`` (str, optional), ``eqs_score`` (float, optional).

        Returns
        -------
        dict
            W3C Verifiable Credential as a JSON-LD object.
            Fields: ``@context``, ``type``, ``id``, ``issuer``,
            ``issuanceDate``, ``credentialSubject``, ``credentialStatus``, ``proof``.

        Example
        -------
        ::

            vc = client.get_vc(receipt["receipt_id"])
            print(vc["proof"]["type"])         # "Dilithium3Signature2024"
            print(vc["credentialStatus"])       # StatusList2021 revocation entry
        """
        body: Dict[str, Any] = {"receipt_id": receipt_id}
        if human_signer:
            body["human_signer"] = human_signer
        return self._request("POST", "/api/governance/receipt/vc", body)

    def get_vc_status(self, receipt_id: str) -> Dict[str, Any]:
        """
        Check the current trust status of a Verifiable Credential.

        Returns the live revocation state from the OMNIX VC Trust Registry.
        Status is ``"active"`` by default (innocent-until-revoked, ADR-130).

        Parameters
        ----------
        receipt_id : str
            The receipt whose VC status you want to check.

        Returns
        -------
        dict
            - ``status`` (str): ``"active"`` | ``"revoked"`` | ``"suspended"``
            - ``receipt_id`` (str)
            - ``revoked_at`` (str, optional): ISO 8601 timestamp of revocation
            - ``revoked_by`` (str, optional): Actor that revoked (redacted for privacy)
            - ``reason`` (str, optional): Public revocation reason
            - ``status_list_index`` (int, optional): W3C StatusList2021 bit index
        """
        return self._request("GET", f"/api/trust/vc-status/{receipt_id}")

    def get_status_list(self) -> Dict[str, Any]:
        """
        Retrieve the W3C StatusList2021 revocation bitstring.

        Returns a GZIP-compressed, base64url-encoded bitstring compatible
        with any EUDI wallet or W3C VC verifier (ADR-130 §4).

        Returns
        -------
        dict
            - ``encodedList`` (str): GZIP + base64url bitstring
            - ``type`` (str): ``"StatusList2021"``
            - ``statusPurpose`` (str): ``"revocation"``
            - ``total_revoked`` (int): Number of revoked credentials
        """
        return self._request("GET", "/api/trust/status-list")

    # ── 6. Revocation (admin only) ───────────────────────────────────────────

    def revoke(self, receipt_id: str, reason: str) -> Dict[str, Any]:
        """
        Revoke a Verifiable Credential permanently. **Admin API key required.**

        Records an immutable revocation entry in the OMNIX VC Trust Registry.
        The credential will appear as ``revoked`` in all future VC status checks.
        Fires a real-time webhook to registered B2B endpoints (ADR-130).

        Parameters
        ----------
        receipt_id : str
            The receipt whose VC to revoke.
        reason : str
            Revocation reason (minimum 10 characters). Required for audit trail.

        Returns
        -------
        dict
            - ``revoked`` (bool): True on success
            - ``receipt_id`` (str)
            - ``revoked_at`` (str): ISO 8601 timestamp

        Raises
        ------
        OmnixAuthError
            If your API key does not have admin permissions.
        OmnixValidationError
            If reason is shorter than 10 characters.

        Example
        -------
        ::

            client.revoke(
                receipt_id = "OMNIX-a3f8e2...",
                reason     = "AVM detected assumption drift — domain suspended",
            )
        """
        if len(reason) < 10:
            raise OmnixValidationError(
                "revocation reason must be at least 10 characters."
            )
        return self._request("POST", f"/api/trust/revoke/{receipt_id}", {"reason": reason})

    def reinstate(self, receipt_id: str, reason: str) -> Dict[str, Any]:
        """
        Reinstate a previously revoked or suspended VC. **Admin API key required.**

        The original revocation event is preserved in the immutable audit trail.
        The VC status returns to ``"active"`` after reinstatement.

        Parameters
        ----------
        receipt_id : str
            The receipt to reinstate.
        reason : str
            Reinstatement justification (minimum 20 characters).

        Returns
        -------
        dict
            - ``reinstated`` (bool): True on success
            - ``receipt_id`` (str)
            - ``reinstated_at`` (str): ISO 8601 timestamp

        Raises
        ------
        OmnixValidationError
            If reason is shorter than 20 characters.
        """
        if len(reason) < 20:
            raise OmnixValidationError(
                "reinstatement reason must be at least 20 characters."
            )
        return self._request("POST", f"/api/trust/reinstate/{receipt_id}", {"reason": reason})

    # ── 7. Utility ───────────────────────────────────────────────────────────

    def health(self) -> Dict[str, Any]:
        """
        Check the health of the OMNIX API and its components.

        Returns a status summary for governance engine, PQC signing,
        database, AVM, revocation registry, and trust layer.

        Returns
        -------
        dict
            - ``status`` (str): ``"healthy"`` | ``"degraded"`` | ``"down"``
            - ``components`` (dict): Per-component health status
            - ``version`` (str): API version
            - ``timestamp`` (str): ISO 8601
        """
        return self._request("GET", "/api/health")

    def get_schema(self) -> Dict[str, Any]:
        """
        Return the governance signal schema with field descriptions and valid ranges.

        Useful for building input validation in your own application before
        calling ``evaluate()``.

        Returns
        -------
        dict
            Schema object describing all signal fields, types, ranges, and examples.
        """
        return self._request("GET", "/api/governance/schema")

    def get_regulatory_frameworks(self) -> Dict[str, Any]:
        """
        Return the full catalog of regulatory frameworks covered by OMNIX.

        Includes frameworks per domain: MiFID II, Basel IV, GDPR, ISO 13849,
        HIPAA, eIDAS 2.0, Dodd-Frank, Solvency II, and more.

        Returns
        -------
        dict
            Catalog with frameworks grouped by domain and compliance level.
        """
        return self._request("GET", "/api/governance/regulatory/catalog")

    def get_due_diligence_report(self, format: str = "json") -> Dict[str, Any]:
        """
        Generate a governance due diligence report for your account.

        Returns statistics, regulatory alignment summary, sample receipts,
        and audit metrics. Suitable for M&A due diligence, investor review,
        and regulatory audit submissions.

        Parameters
        ----------
        format : str
            ``"json"`` (default) — full structured report.
            ``"pdf"`` — returns a ``download_url`` for a PDF version.

        Returns
        -------
        dict
            Governance statistics, regulatory alignment, and receipt samples.
            If ``format="pdf"``, includes ``download_url``.
        """
        if format not in ("json", "pdf"):
            raise OmnixValidationError(
                f"Invalid format: {format!r}. Must be 'json' or 'pdf'."
            )
        return self._request(
            "GET",
            "/api/governance/due-diligence-report",
            params={"format": format},
        )
