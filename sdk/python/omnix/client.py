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

    # ── Oscillation Insight Engine (ADR-134) ────────────────────────────────

    def oscillation(
        self,
        domain:    str,
        view:      str = "full",
        num_weeks: int = 12,
    ) -> Dict[str, Any]:
        """
        Fetch governance oscillation analytics for a domain.

        Args:
            domain:    Governance domain (trading | insurance | energy | …)
            view:      "full" | "profile" | "phases" | "asymmetry" | "dampening"
            num_weeks: Analysis window 1–26 weeks (default 12)

        Returns:
            dict with oscillation_profile, asymmetry, dampening, hesitation_index,
            governance_quality_score, dominant_phase.

        No authentication required — public analytics endpoint.
        ADR-134.
        """
        path = f"/api/analytics/oscillation?domain={domain}&view={view}&num_weeks={num_weeks}"
        return self._get(path, authenticated=False)

    # ── Anomaly Response Engine (ADR-129) ────────────────────────────────────

    def anomaly_response(self, domain: str) -> Dict[str, Any]:
        """
        Run a full anomaly detection and response cycle for a domain.

        Args:
            domain: Governance domain to analyse.

        Returns:
            dict with anomalies, recommendations, new_logged, active_count.
        ADR-129.
        """
        return self._post("/api/governance/anomaly/response", {"domain": domain})

    def anomaly_active(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        List all ACTIVE anomaly recommendations.

        Args:
            domain: Optional domain filter.

        Returns:
            dict with recommendations list and total.
        ADR-129.
        """
        path = "/api/governance/anomaly/active"
        if domain:
            path += f"?domain={domain}"
        return self._get(path)

    def anomaly_summary(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Summary of anomaly recommendations by status and action code.
        ADR-129.
        """
        path = "/api/governance/anomaly/summary"
        if domain:
            path += f"?domain={domain}"
        return self._get(path)

    def anomaly_acknowledge(self, rec_id: str, note: str = "") -> Dict[str, Any]:
        """
        Acknowledge an active anomaly recommendation.
        ADR-129.
        """
        return self._post(
            f"/api/governance/anomaly/{rec_id}/acknowledge",
            {"acknowledge_note": note},
        )

    def anomaly_resolve(self, rec_id: str, note: str = "") -> Dict[str, Any]:
        """
        Resolve an active or acknowledged anomaly recommendation.
        ADR-129.
        """
        return self._post(
            f"/api/governance/anomaly/{rec_id}/resolve",
            {"resolution_note": note},
        )

    # ── Execution Integrity Layer (ADR-131) ──────────────────────────────────

    def execution_intent(
        self,
        order_id:            str,
        decision_receipt_id: str,
        asset:               str,
        domain:              str,
        direction:           str,
        size_usd:            float,
    ) -> Dict[str, Any]:
        """
        Capture execution intent before placing a trade.

        Must be called BEFORE the order is placed. If this call fails (503),
        the trade must NOT proceed — this is an ADR-131 hard invariant.

        Returns:
            dict with status, order_id, receipt_id, intent_logged.
        ADR-131.
        """
        return self._post("/api/governance/execution/intent", {
            "order_id":            order_id,
            "decision_receipt_id": decision_receipt_id,
            "asset":               asset,
            "domain":              domain,
            "direction":           direction,
            "size_usd":            size_usd,
        })

    def execution_receipts(
        self,
        decision_receipt_id: Optional[str] = None,
        status:              Optional[str] = None,
        limit:               int = 20,
        offset:              int = 0,
    ) -> Dict[str, Any]:
        """
        List execution receipts.

        Args:
            decision_receipt_id: Filter by linked governance decision ID.
            status:              Filter by status: PENDING | FILLED | PARTIAL | FAILED.
            limit:               Max records (default 20, max 100).
            offset:              Pagination offset.
        ADR-131.
        """
        params = f"?limit={limit}&offset={offset}"
        if decision_receipt_id:
            params += f"&decision_receipt_id={decision_receipt_id}"
        if status:
            params += f"&status={status}"
        return self._get(f"/api/governance/execution/receipts{params}")

    def execution_receipt(self, order_id: str) -> Dict[str, Any]:
        """
        Fetch a single execution receipt by order ID.
        ADR-131.
        """
        return self._get(f"/api/governance/execution/receipts/{order_id}")

    # ── Breach Containment Engine (ADR-142) ──────────────────────────────────

    def breach_status(self) -> Dict[str, Any]:
        """
        Get current containment status.

        Returns:
            dict with is_contained, active_event_id, trigger_code, severity,
            summary, triggered_at, total_events.

        No authentication required. Fail-closed: DB error → is_contained=True.
        ADR-142.
        """
        return self._get("/api/governance/breach/status", authenticated=False)

    def breach_activate(
        self,
        trigger_code: str,
        severity:     str,
        summary:      str,
        triggered_by: str = "sdk",
        detail:       Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Activate breach containment. Blocks ALL governance decisions immediately.

        Args:
            trigger_code: MANUAL_OPERATOR | TIMING_ANOMALY | CHECKSUM_MISMATCH |
                          PROCESS_ANOMALY | REPEATED_AUTH_FAILURE | API_TRIGGERED
            severity:     CRITICAL | HIGH | MEDIUM
            summary:      Human-readable description of the threat.
            triggered_by: Operator/system identifier.
            detail:       Optional extra context dict.

        WARNING: After activation, all governance decisions return BLOCKED
        until breach_release() is called with human authorization.
        ADR-142.
        """
        return self._post("/api/governance/breach/activate", {
            "trigger_code": trigger_code,
            "severity":     severity,
            "summary":      summary,
            "triggered_by": triggered_by,
            "detail":       detail or {},
        })

    def breach_release(
        self,
        event_id:      str,
        authorized_by: str,
        release_note:  str,
    ) -> Dict[str, Any]:
        """
        Release an active containment event. Requires human authorization.

        Args:
            event_id:      BCE event ID to release.
            authorized_by: Authorizing operator identifier.
            release_note:  Required — reason for release.
        ADR-142.
        """
        return self._post("/api/governance/breach/release", {
            "event_id":      event_id,
            "authorized_by": authorized_by,
            "release_note":  release_note,
        })

    def breach_assess(
        self,
        latency_ms:           Optional[float] = None,
        expected_latency_ms:  Optional[float] = None,
        latency_sigma:        Optional[float] = None,
        avm_snapshot_hash:    Optional[str]   = None,
        expected_hash:        Optional[str]   = None,
        auth_failure_count:   int = 0,
        auth_failure_window:  int = 300,
    ) -> Dict[str, Any]:
        """
        Run automated threat assessment. Does NOT auto-activate.

        Returns:
            dict with threats_detected, indicators, recommended_action.
            If recommended_action == "ACTIVATE_CONTAINMENT", call breach_activate().
        ADR-142.
        """
        return self._post("/api/governance/breach/assess", {
            "latency_ms":           latency_ms,
            "expected_latency_ms":  expected_latency_ms,
            "latency_sigma":        latency_sigma,
            "avm_snapshot_hash":    avm_snapshot_hash,
            "expected_hash":        expected_hash,
            "auth_failure_count":   auth_failure_count,
            "auth_failure_window":  auth_failure_window,
        })

    def breach_history(
        self,
        status: Optional[str] = None,
        limit:  int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Return paginated breach event history.
        ADR-142.
        """
        params = f"?limit={limit}&offset={offset}"
        if status:
            params += f"&status={status}"
        return self._get(f"/api/governance/breach/history{params}")

    # ── Multi-Domain Risk Governance (ADR-143) ───────────────────────────────

    def risk_evaluate(
        self,
        subject:       str,
        risk_signals:  Dict[str, Dict[str, Any]],
        weights:       Optional[Dict[str, float]] = None,
        client_domain: Optional[str] = None,
        assessed_by:   str = "sdk",
    ) -> Dict[str, Any]:
        """
        Evaluate multi-domain risk for a subject.

        Args:
            subject:       Entity or deployment identifier.
            risk_signals:  Dict mapping vector → signals. Vectors:
                           financial, technical, legal, human.
                           Each vector accepts domain-specific float signals.
            weights:       Optional custom weights (financial, technical, legal, human).
                           Values are normalized to sum to 1.0.
            client_domain: Client's operational domain context.
            assessed_by:   Operator/system identifier.

        Returns:
            dict with decision (APPROVED|REVIEW|BLOCKED), composite_score (0–100),
            vector_scores, breakdown, hard_block_vector, assessment_id.

        Decision logic:
            composite ≥ 80 → BLOCKED
            composite 60–79 → REVIEW
            composite < 60 → APPROVED
            Any single vector ≥ 95 → BLOCKED regardless of composite.
        ADR-143.
        """
        payload: Dict[str, Any] = {
            "subject":      subject,
            "risk_signals": risk_signals,
            "assessed_by":  assessed_by,
        }
        if weights:
            payload["weights"] = weights
        if client_domain:
            payload["client_domain"] = client_domain
        return self._post("/api/governance/risk/evaluate", payload)

    def risk_catalog(self) -> Dict[str, Any]:
        """
        Fetch supported risk vectors, signal definitions, and thresholds.
        No authentication required — public endpoint.
        ADR-143.
        """
        return self._get("/api/governance/risk/catalog", authenticated=False)

    def risk_history(
        self,
        subject:       Optional[str] = None,
        client_domain: Optional[str] = None,
        decision:      Optional[str] = None,
        limit:         int = 20,
        offset:        int = 0,
    ) -> Dict[str, Any]:
        """
        Return paginated risk assessment history.
        ADR-143.
        """
        params = f"?limit={limit}&offset={offset}"
        if subject:
            params += f"&subject={subject}"
        if client_domain:
            params += f"&client_domain={client_domain}"
        if decision:
            params += f"&decision={decision}"
        return self._get(f"/api/governance/risk/history{params}")

    def risk_summary(self, client_domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Aggregate statistics across all risk assessments.
        ADR-143.
        """
        path = "/api/governance/risk/summary"
        if client_domain:
            path += f"?client_domain={client_domain}"
        return self._get(path)

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
