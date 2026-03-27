"""
OMNIX Credit Governance Module
ADR-052: Islamic Credit Governance Vertical

Domain-agnostic governance engine adapted for Islamic finance credit decisions.
Runs 24/7 generating PQC-signed governance receipts for credit applications.
"""

from omnix_core.credit.credit_signal_adapter import CreditSignalAdapter
from omnix_core.credit.credit_macro_data import CreditMacroDataProvider

__all__ = ["CreditSignalAdapter", "CreditMacroDataProvider"]
