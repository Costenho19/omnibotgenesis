"""
OMNIX Python SDK
Official client library for the OMNIX Decision Governance API.

Install: copy this file into your project or install via pip (coming soon).

Usage:
    from omnix_sdk import OmnixClient

    client = OmnixClient(api_key="OMNIX-your-key-here")

    result = client.evaluate({
        "signal_integrity": 75,
        "probability_score": 68,
        "risk_exposure": 42,
        "signal_coherence": 60,
        "trend_persistence": 55,
        "stress_resilience": 48,
        "logic_consistency": 65,
        "temporal_coherence": 58,
        "domain": "trading",
        "asset": "BTC/USD",
        "scenario": "Long position pre-execution"
    })

    print(result["decision"])       # "APPROVED" | "BLOCKED" | "HOLD"
    print(result["receipt_id"])     # "OMNIX-XXXXXXXXXXXXXXXX"
    print(result["pqc_signed"])     # True
"""

import json
import urllib.request
import urllib.error
from typing import Optional


class OmnixAuthError(Exception):
    """Invalid or expired API key."""


class OmnixRateLimitError(Exception):
    """Rate limit exceeded."""


class OmnixAPIError(Exception):
    """Unexpected API error."""


class OmnixClient:
    """
    OMNIX Governance API Client.

    Parameters
    ----------
    api_key : str
        Your OMNIX API key (format: OMNIX-<40 chars>).
    base_url : str
        API base URL. Default: https://omnixquantum.net
    timeout : int
        Request timeout in seconds. Default: 30.
    """

    DEFAULT_BASE_URL = "https://omnixquantum.net"

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = 30,
    ):
        if not api_key or not api_key.startswith("OMNIX-"):
            raise ValueError("Invalid API key format. Expected: OMNIX-<key>")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def _request(self, method: str, path: str, body: Optional[dict] = None) -> dict:
        url = f"{self._base_url}{path}"
        headers = {
            "X-API-Key": self._api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "omnix-python-sdk/1.0",
        }
        data = json.dumps(body).encode("utf-8") if body else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body_bytes = e.read()
            try:
                error_body = json.loads(body_bytes.decode("utf-8"))
                msg = error_body.get("error", str(e))
            except Exception:
                msg = str(e)
            if e.code == 401:
                raise OmnixAuthError(f"Authentication failed: {msg}") from e
            if e.code == 429:
                raise OmnixRateLimitError("Rate limit exceeded. Retry after 60s.") from e
            raise OmnixAPIError(f"API error {e.code}: {msg}") from e
        except urllib.error.URLError as e:
            raise OmnixAPIError(f"Network error: {e.reason}") from e

    def evaluate(self, signals: dict) -> dict:
        """
        Submit a decision for governance evaluation.

        Parameters
        ----------
        signals : dict
            Decision signals. Required fields:
            - signal_integrity (int 0-100): Input data quality score
            - probability_score (int 0-100): Confidence in the decision
            - risk_exposure (int 0-100): Estimated risk level (lower = safer)
            - signal_coherence (int 0-100): Internal signal consistency
            - trend_persistence (int 0-100): Trend alignment score
            - stress_resilience (int 0-100): Resilience under stress conditions
            - logic_consistency (int 0-100): Logical coherence of the scenario
            - temporal_coherence (int 0-100): Time-context validity
            Optional fields:
            - domain (str): "trading" | "credit" | "insurance" | "robotics"
            - asset (str): Asset or entity identifier (e.g. "BTC/USD")
            - scenario (str): Human-readable description of the decision

        Returns
        -------
        dict with keys:
            - decision: "APPROVED" | "BLOCKED" | "HOLD"
            - receipt_id: Unique receipt identifier
            - pqc_signed: bool — whether receipt is post-quantum signed
            - checkpoints_passed: int
            - checkpoints_total: int
            - summary: Executive summary of the governance decision
            - regulatory_alignment: Regulatory frameworks evaluated
            - timestamp: ISO 8601 timestamp
        """
        required = [
            "signal_integrity", "probability_score", "risk_exposure",
            "signal_coherence", "trend_persistence", "stress_resilience",
            "logic_consistency", "temporal_coherence",
        ]
        missing = [f for f in required if f not in signals]
        if missing:
            raise ValueError(f"Missing required signal fields: {missing}")

        return self._request("POST", "/api/governance/evaluate", signals)

    def get_receipt(self, receipt_id: str) -> dict:
        """
        Retrieve a specific governance receipt by ID.

        Parameters
        ----------
        receipt_id : str
            Receipt identifier (format: OMNIX-<hex>).

        Returns
        -------
        dict with full receipt details including checkpoint results and PQC signature.
        """
        return self._request("GET", f"/api/governance/receipts/{receipt_id}")

    def list_receipts(self, page: int = 1, per_page: int = 20) -> dict:
        """
        List your governance receipts (paginated, most recent first).

        Returns
        -------
        dict with keys: receipts (list), total, page, per_page
        """
        return self._request(
            "GET",
            f"/api/governance/receipts?page={page}&per_page={per_page}"
        )

    def get_schema(self) -> dict:
        """Return the signal schema documentation."""
        return self._request("GET", "/api/governance/schema")

    def get_regulatory_catalog(self) -> dict:
        """Return the full regulatory framework catalog covered by OMNIX."""
        return self._request("GET", "/api/governance/regulatory/catalog")

    def get_due_diligence_report(self, format: str = "json") -> dict:
        """
        Generate a governance due diligence report for your account.

        Parameters
        ----------
        format : str
            "json" (default) or "pdf" — PDF returns a download URL.

        Returns
        -------
        dict with governance statistics, regulatory alignment, and receipt samples.
        Suitable for M&A due diligence, investor review, and regulatory audits.
        """
        return self._request(
            "GET",
            f"/api/governance/due-diligence-report?format={format}"
        )
