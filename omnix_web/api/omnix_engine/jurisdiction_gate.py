"""
OMNIX — Jurisdiction Compliance Gate (CP-11)
ADR-049: Jurisdictional Asset & Operation Validation Gate

Purpose:
    CP-11 validates that the proposed trading decision is compliant with
    the configured jurisdictional regulatory framework of the client.
    When enabled, it checks:
      - Asset permitted in client jurisdiction (UAE, EU, US, GCC)
      - Operation type allowed (spot, leveraged, derivatives)
      - Sanctioned asset list (OFAC/EU/UN sanctioned tokens)

Design:
    - Fail-safe: if module errors or disabled → pass-through (pipeline continues)
    - Configurable via JURISDICTION env var (default: "GLOBAL")
    - Default: DISABLED (zero impact on existing Railway operation)
    - Rule table: built-in defaults per jurisdiction; extensible

Implemented: March 2026
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

OFAC_SANCTIONED_ASSETS: set[str] = {
    "TRON_MIXER", "LAZARUS_TOKEN",
}

JURISDICTION_RULES: dict[str, dict] = {
    "UAE": {
        "allowed_spot": True,
        "allowed_leveraged": False,
        "allowed_derivatives": False,
        "prohibited_assets": {"XMR", "ZEC", "DASH", "GRIN", "BEAM", "FIRO"},
        "allowed_assets": set(),
        "description": "UAE Virtual Asset Regulatory Authority (VARA) — spot crypto allowed, derivatives/leverage require additional licensing",
    },
    "EU": {
        "allowed_spot": True,
        "allowed_leveraged": True,
        "allowed_derivatives": True,
        "prohibited_assets": {"XMR", "GRIN", "BEAM"},
        "allowed_assets": set(),
        "description": "EU MiCA (Markets in Crypto-Assets Regulation) — most assets allowed, anonymity coins restricted",
    },
    "US": {
        "allowed_spot": True,
        "allowed_leveraged": False,
        "allowed_derivatives": False,
        "prohibited_assets": {"XMR", "ZEC", "DASH", "GRIN", "BEAM", "FIRO", "PIVX"},
        "allowed_assets": set(),
        "description": "US FinCEN/SEC framework — privacy coins high-risk, derivatives require CFTC licensing",
    },
    "GCC": {
        "allowed_spot": True,
        "allowed_leveraged": False,
        "allowed_derivatives": False,
        "prohibited_assets": {"XMR", "ZEC", "DASH", "GRIN", "BEAM"},
        "allowed_assets": set(),
        "description": "GCC (Gulf Cooperation Council) — unified VARA-aligned framework, derivatives restricted",
    },
    "UK": {
        "allowed_spot": True,
        "allowed_leveraged": False,
        "allowed_derivatives": False,
        "prohibited_assets": {"XMR", "ZEC", "DASH", "GRIN", "BEAM", "FIRO"},
        "allowed_assets": set(),
        "description": "UK Financial Conduct Authority (FCA) — spot crypto allowed for registered firms; leveraged products and derivatives to retail require FCA authorization",
    },
    "SG": {
        "allowed_spot": True,
        "allowed_leveraged": False,
        "allowed_derivatives": False,
        "prohibited_assets": {"BEAM", "GRIN", "FIRO"},
        "allowed_assets": set(),
        "description": "Singapore Monetary Authority of Singapore (MAS) — Digital Payment Token services allowed; leveraged and derivative products require Capital Markets Services license",
    },
    "JP": {
        "allowed_spot": True,
        "allowed_leveraged": True,
        "allowed_derivatives": False,
        "prohibited_assets": {"XMR", "DASH", "ZEC", "GRIN", "BEAM", "FIRO"},
        "allowed_assets": set(),
        "description": "Japan Financial Services Agency (FSA) — privacy coins delisted from licensed exchanges; leverage capped at 2x for retail; derivatives require additional licensing",
    },
    "AU": {
        "allowed_spot": True,
        "allowed_leveraged": False,
        "allowed_derivatives": True,
        "prohibited_assets": {"XMR", "GRIN", "BEAM"},
        "allowed_assets": set(),
        "description": "Australia ASIC (Australian Securities and Investments Commission) — spot crypto allowed; retail leverage restricted; derivatives permitted under AFSL license",
    },
    "CA": {
        "allowed_spot": True,
        "allowed_leveraged": False,
        "allowed_derivatives": False,
        "prohibited_assets": {"XMR", "ZEC", "DASH", "GRIN", "BEAM"},
        "allowed_assets": set(),
        "description": "Canada CSA (Canadian Securities Administrators) — crypto trading platforms require registration; privacy coins restricted; leveraged/derivative products require prospectus exemption",
    },
    "BR": {
        "allowed_spot": True,
        "allowed_leveraged": False,
        "allowed_derivatives": True,
        "prohibited_assets": {"XMR", "GRIN", "BEAM"},
        "allowed_assets": set(),
        "description": "Brazil CVM (Comissão de Valores Mobiliários) — crypto assets regulated as financial instruments since 2023; spot allowed; derivatives with licensing; privacy coins restricted",
    },
    "KR": {
        "allowed_spot": True,
        "allowed_leveraged": False,
        "allowed_derivatives": False,
        "prohibited_assets": {"XMR", "DASH", "ZEC", "GRIN", "BEAM", "FIRO", "PIVX"},
        "allowed_assets": set(),
        "description": "South Korea FSC (Financial Services Commission) — VASP Act 2021 requires registration; privacy coins banned from licensed exchanges; derivatives restricted",
    },
    "CH": {
        "allowed_spot": True,
        "allowed_leveraged": True,
        "allowed_derivatives": True,
        "prohibited_assets": {"XMR", "GRIN"},
        "allowed_assets": set(),
        "description": "Switzerland FINMA (Financial Market Supervisory Authority) — crypto-progressive framework; Crypto Valley Zug; most assets and operations allowed under FINMA banking/securities rules",
    },
    "GLOBAL": {
        "allowed_spot": True,
        "allowed_leveraged": True,
        "allowed_derivatives": True,
        "prohibited_assets": set(),
        "allowed_assets": set(),
        "description": "No jurisdiction-specific restrictions — global default",
    },
}

SUPPORTED_JURISDICTIONS: list[str] = [
    "UAE", "EU", "US", "GCC", "UK", "SG", "JP", "AU", "CA", "BR", "KR", "CH", "GLOBAL"
]


@dataclass
class JurisdictionVetoResult:
    admissible: bool
    pass_through: bool = False
    reason: str = ""
    asset: str = ""
    violation: str = ""
    jurisdiction: str = "GLOBAL"
    compliance_score: float = 100.0


@dataclass
class JurisdictionGateConfig:
    enabled: bool = False
    jurisdiction: str = "GLOBAL"
    operation_type: str = "spot"
    custom_prohibited_assets: list[str] = field(default_factory=list)
    custom_allowed_assets: list[str] = field(default_factory=list)
    block_sanctioned_assets: bool = True


class JurisdictionGate:
    """
    CP-11: Jurisdiction Compliance Gate

    Validates trading decisions against the jurisdictional regulatory
    framework configured for this deployment or client. Positioned
    AFTER CP-10 (Fraud Gate) in the decision pipeline.

    Supported jurisdictions:
      - UAE: VARA framework (Virtual Asset Regulatory Authority)
      - EU: MiCA (Markets in Crypto-Assets Regulation)
      - US: FinCEN/SEC/CFTC combined framework
      - GCC: Gulf Cooperation Council unified framework
      - GLOBAL: No jurisdiction-specific restrictions (default)

    Usage:
        gate = JurisdictionGate(config)
        result = gate.evaluate(symbol, proposed_action, operation_type)
        if not result.admissible and not result.pass_through:
            # VETO — block the decision
    """

    def __init__(self, config: Optional[JurisdictionGateConfig] = None):
        self.config = config or JurisdictionGateConfig()
        jurisdiction_key = self.config.jurisdiction.upper()
        self._rules = JURISDICTION_RULES.get(jurisdiction_key, JURISDICTION_RULES["GLOBAL"]).copy()

        if self.config.custom_prohibited_assets:
            self._rules["prohibited_assets"] = self._rules["prohibited_assets"] | {
                a.upper() for a in self.config.custom_prohibited_assets
            }

        if self.config.custom_allowed_assets:
            self._rules["allowed_assets"] = {
                a.upper() for a in self.config.custom_allowed_assets
            }

    def evaluate(
        self,
        symbol: str,
        proposed_action: str,
        operation_type: str = "spot",
    ) -> JurisdictionVetoResult:
        """
        Evaluate a proposed decision against jurisdictional regulations.

        Args:
            symbol:           Trading pair (e.g., "BTC/USD")
            proposed_action:  "BUY", "SELL", or "HOLD"
            operation_type:   "spot", "leveraged", or "derivatives"

        Returns:
            JurisdictionVetoResult
        """
        if not self.config.enabled:
            return JurisdictionVetoResult(
                admissible=True,
                pass_through=True,
                reason="CP-11 Jurisdiction Gate: disabled",
                asset=symbol,
                jurisdiction=self.config.jurisdiction,
                compliance_score=100.0,
            )

        try:
            return self._run_checks(symbol, proposed_action, operation_type)
        except Exception as exc:
            logger.warning(f"⚠️ [JURISDICTION_GATE] Exception for {symbol}: {exc} → pass-through")
            return JurisdictionVetoResult(
                admissible=True,
                pass_through=True,
                reason=f"CP-11 Jurisdiction exception → pass-through: {exc}",
                asset=symbol,
                jurisdiction=self.config.jurisdiction,
            )

    def _run_checks(
        self,
        symbol: str,
        proposed_action: str,
        operation_type: str,
    ) -> JurisdictionVetoResult:
        jurisdiction = self.config.jurisdiction.upper()
        base_symbol = symbol.upper().replace("/USD", "").replace("/USDT", "").replace("-USD", "")
        full_symbol = symbol.upper()
        op_type = operation_type.lower()

        if proposed_action.upper() == "HOLD":
            return JurisdictionVetoResult(
                admissible=True,
                pass_through=False,
                reason=f"CP-11 JURISDICTION PASS: HOLD — no transaction to validate | {jurisdiction}",
                asset=symbol,
                jurisdiction=jurisdiction,
                compliance_score=100.0,
            )

        if self.config.block_sanctioned_assets and (
            base_symbol in OFAC_SANCTIONED_ASSETS or full_symbol in OFAC_SANCTIONED_ASSETS
        ):
            return JurisdictionVetoResult(
                admissible=False,
                pass_through=False,
                reason=(
                    f"CP-11 JURISDICTION VETO: {symbol} appears on OFAC/international sanctions list"
                ),
                asset=symbol,
                violation="SANCTIONED_ASSET",
                jurisdiction=jurisdiction,
                compliance_score=0.0,
            )

        prohibited = self._rules.get("prohibited_assets", set())
        if base_symbol in prohibited or full_symbol in prohibited:
            return JurisdictionVetoResult(
                admissible=False,
                pass_through=False,
                reason=(
                    f"CP-11 JURISDICTION VETO: {symbol} prohibited in {jurisdiction} "
                    f"({self._rules.get('description', '')})"
                ),
                asset=symbol,
                violation=f"PROHIBITED_IN_{jurisdiction}",
                jurisdiction=jurisdiction,
                compliance_score=0.0,
            )

        if op_type == "leveraged" and not self._rules.get("allowed_leveraged", True):
            return JurisdictionVetoResult(
                admissible=False,
                pass_through=False,
                reason=(
                    f"CP-11 JURISDICTION VETO: Leveraged operations not permitted in {jurisdiction}"
                ),
                asset=symbol,
                violation=f"LEVERAGE_PROHIBITED_{jurisdiction}",
                jurisdiction=jurisdiction,
                compliance_score=0.0,
            )

        if op_type == "derivatives" and not self._rules.get("allowed_derivatives", True):
            return JurisdictionVetoResult(
                admissible=False,
                pass_through=False,
                reason=(
                    f"CP-11 JURISDICTION VETO: Derivative operations not permitted in {jurisdiction}"
                ),
                asset=symbol,
                violation=f"DERIVATIVES_PROHIBITED_{jurisdiction}",
                jurisdiction=jurisdiction,
                compliance_score=0.0,
            )

        return JurisdictionVetoResult(
            admissible=True,
            pass_through=False,
            reason=(
                f"CP-11 JURISDICTION PASS: {symbol} compliant in {jurisdiction} "
                f"| op={op_type} | score 100/100"
            ),
            asset=symbol,
            jurisdiction=jurisdiction,
            compliance_score=100.0,
        )


def load_jurisdiction_config_from_env() -> JurisdictionGateConfig:
    """
    Load Jurisdiction Gate configuration from environment variables.
    Returns default (disabled) config if JURISDICTION_GATE_ENABLED is not 'true'.
    """
    enabled = os.environ.get("JURISDICTION_GATE_ENABLED", "false").lower() == "true"
    if not enabled:
        return JurisdictionGateConfig(enabled=False)

    return JurisdictionGateConfig(
        enabled=True,
        jurisdiction=os.environ.get("JURISDICTION", "GLOBAL").upper(),
        operation_type=os.environ.get("JURISDICTION_OP_TYPE", "spot").lower(),
        block_sanctioned_assets=os.environ.get(
            "JURISDICTION_BLOCK_SANCTIONED", "true"
        ).lower() == "true",
    )
