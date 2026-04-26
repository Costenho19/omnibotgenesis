"""
OMNIX Governance SDK — Python
==============================

Decision governance infrastructure for automated systems.
Cryptographic proof on every decision. 9 domains. Live.

Quick start:
    pip install omnix-quantum

    from omnix import OmnixClient

    client = OmnixClient(api_key="OMNIX-...")
    receipt = client.evaluate(
        domain="trading",
        asset="BTC/USD",
        signals={"price": 94200, "volume": 1.5, "volatility": 0.18},
    )

    print(receipt)          # ✅ APPROVED | OMNIX-TRD-... | 11/11 gates passed
    print(receipt.approved) # True
    print(receipt.receipt_id)
    print(receipt.content_hash)

Docs:   https://omnixquantum.net/docs
Verify: https://omnixquantum.net/verify-independently
DID:    did:web:omnixquantum.net
"""

from .client import OmnixClient
from .models import GovernanceReceipt, CheckpointResult
from .exceptions import (
    OmnixError,
    OmnixAuthError,
    OmnixValidationError,
    OmnixGovernanceBlock,
    OmnixRateLimitError,
    OmnixServerError,
    OmnixNetworkError,
)

__version__ = "1.0.0"
__all__ = [
    "OmnixClient",
    "GovernanceReceipt",
    "CheckpointResult",
    "OmnixError",
    "OmnixAuthError",
    "OmnixValidationError",
    "OmnixGovernanceBlock",
    "OmnixRateLimitError",
    "OmnixServerError",
    "OmnixNetworkError",
]


def evaluate(
    domain: str,
    asset: str,
    signals: dict,
    *,
    api_key: str,
    **kwargs,
) -> "GovernanceReceipt":
    """
    Convenience function — evaluate a governance decision.

    Args:
        domain:  Governance domain (trading | islamic_credit | insurance | ...)
        asset:   Asset identifier
        signals: Domain-specific signals
        api_key: Your OMNIX API key (OMNIX-...)

    Returns:
        GovernanceReceipt

    Example:
        from omnix import evaluate

        receipt = evaluate(
            domain="islamic_credit",
            asset="SME-AE-001",
            signals={"debt_to_income": 32, "collateral_ratio": 1.4, "sharia_compliant": True},
            api_key="OMNIX-...",
        )
        print(receipt.decision)  # "APPROVED"
    """
    client = OmnixClient(api_key=api_key, **kwargs)
    return client.evaluate(domain=domain, asset=asset, signals=signals)
