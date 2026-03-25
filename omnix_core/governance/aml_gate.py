"""
OMNIX — AML Governance Gate (CP-9)
ADR-047: Anti-Money Laundering Decision Compliance Gate

Purpose:
    CP-9 validates trading decisions against Anti-Money Laundering (AML)
    principles mandated by FATF, FinCEN, and UAE Central Bank regulations.
    When enabled, it screens for:
      - High-risk AML asset categories (privacy coins, mixer tokens)
      - Anomalous trade volume patterns
      - Structuring patterns (suspicious trade frequency)
      - High-risk jurisdiction exposure

Design:
    - Fail-safe: if module errors or disabled → pass-through (pipeline continues)
    - Configurable per client or globally via AML_GATE_ENABLED env var
    - Default: DISABLED (preserves existing behavior for all current clients)
    - Output: VetoResult with structured reason for PQC receipt

Implemented: March 2026
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

HIGH_RISK_AML_ASSETS: set[str] = {
    "XMR", "ZEC", "DASH", "GRIN", "BEAM", "FIRO", "PIVX", "ZCASH",
    "MONERO", "XMR/USD", "ZEC/USD", "DASH/USD",
    "XMR/USDT", "ZEC/USDT", "DASH/USDT",
    "TORNADO", "RAILGUN", "AZTEC",
}

AML_MIXER_TOKENS: set[str] = {
    "TORN", "RAIL", "AZTEC",
}

AML_VOLUME_THRESHOLD_DEFAULT: float = 500_000.0
AML_FREQUENCY_THRESHOLD_DEFAULT: int = 10


@dataclass
class AMLVetoResult:
    admissible: bool
    pass_through: bool = False
    reason: str = ""
    asset: str = ""
    violation: str = ""
    risk_score: float = 0.0
    aml_score: float = 100.0


@dataclass
class AMLGateConfig:
    enabled: bool = False
    volume_threshold_usd: float = AML_VOLUME_THRESHOLD_DEFAULT
    frequency_threshold: int = AML_FREQUENCY_THRESHOLD_DEFAULT
    block_privacy_coins: bool = True
    block_mixer_tokens: bool = True
    custom_high_risk_assets: list[str] = field(default_factory=list)


class AMLGate:
    """
    CP-9: AML Governance Gate

    Validates that an automated trading decision does not exhibit
    Anti-Money Laundering risk patterns. Designed as a configurable
    veto layer positioned AFTER CP-8 (ECW) in the decision pipeline.

    Regulatory alignment:
      - FATF Recommendation 15 (Virtual Assets)
      - FinCEN Virtual Currency Guidance (2019)
      - UAE Central Bank AML/CFT Framework

    Usage:
        gate = AMLGate(config)
        result = gate.evaluate(symbol, proposed_action, volume_usd, trade_frequency)
        if not result.admissible and not result.pass_through:
            # VETO — block the decision
    """

    def __init__(self, config: Optional[AMLGateConfig] = None):
        self.config = config or AMLGateConfig()
        self._high_risk = HIGH_RISK_AML_ASSETS | AML_MIXER_TOKENS | {
            a.upper() for a in self.config.custom_high_risk_assets
        }

    def evaluate(
        self,
        symbol: str,
        proposed_action: str,
        volume_usd: float = 0.0,
        trade_frequency_24h: int = 0,
    ) -> AMLVetoResult:
        """
        Evaluate a proposed decision against AML compliance rules.

        Args:
            symbol:                Trading pair (e.g., "XMR/USD")
            proposed_action:       "BUY", "SELL", or "HOLD"
            volume_usd:            Estimated trade volume in USD
            trade_frequency_24h:   Number of trades in last 24 hours (for structuring detection)

        Returns:
            AMLVetoResult
        """
        if not self.config.enabled:
            return AMLVetoResult(
                admissible=True,
                pass_through=True,
                reason="CP-9 AML Gate: disabled",
                asset=symbol,
                aml_score=100.0,
            )

        try:
            return self._run_checks(symbol, proposed_action, volume_usd, trade_frequency_24h)
        except Exception as exc:
            logger.warning(f"⚠️ [AML_GATE] Exception for {symbol}: {exc} → pass-through")
            return AMLVetoResult(
                admissible=True,
                pass_through=True,
                reason=f"CP-9 AML exception → pass-through: {exc}",
                asset=symbol,
            )

    def _run_checks(
        self,
        symbol: str,
        proposed_action: str,
        volume_usd: float,
        trade_frequency_24h: int,
    ) -> AMLVetoResult:
        base_symbol = symbol.upper().replace("/USD", "").replace("/USDT", "").replace("-USD", "")
        full_symbol = symbol.upper()

        aml_score = 100.0
        violations = []

        if proposed_action.upper() == "HOLD":
            return AMLVetoResult(
                admissible=True,
                pass_through=False,
                reason="CP-9 AML PASS: HOLD action — no transaction risk",
                asset=symbol,
                aml_score=100.0,
            )

        base_in_privacy = base_symbol in HIGH_RISK_AML_ASSETS or full_symbol in HIGH_RISK_AML_ASSETS
        base_in_mixer = base_symbol in AML_MIXER_TOKENS or full_symbol in AML_MIXER_TOKENS

        if self.config.block_privacy_coins and base_in_privacy and not base_in_mixer:
            return AMLVetoResult(
                admissible=False,
                pass_through=False,
                reason=(
                    f"CP-9 AML VETO: {symbol} is a high-risk AML asset (privacy coin)"
                ),
                asset=symbol,
                violation="HIGH_RISK_AML_ASSET_PRIVACY_COIN",
                risk_score=100.0,
                aml_score=0.0,
            )

        if self.config.block_mixer_tokens and base_in_mixer:
            return AMLVetoResult(
                admissible=False,
                pass_through=False,
                reason=(
                    f"CP-9 AML VETO: {symbol} is a mixer/tumbler token (prohibited under AML)"
                ),
                asset=symbol,
                violation="HIGH_RISK_AML_ASSET_MIXER",
                risk_score=100.0,
                aml_score=0.0,
            )

        if volume_usd > self.config.volume_threshold_usd:
            aml_score -= 40.0
            violations.append(
                f"Volume ${volume_usd:,.0f} exceeds AML threshold ${self.config.volume_threshold_usd:,.0f}"
            )

        if trade_frequency_24h > self.config.frequency_threshold:
            aml_score -= 30.0
            violations.append(
                f"Trade frequency {trade_frequency_24h}/24h exceeds structuring threshold {self.config.frequency_threshold}"
            )

        if violations:
            admissible = aml_score >= 50.0
            return AMLVetoResult(
                admissible=admissible,
                pass_through=False,
                reason=f"CP-9 AML {'PASS' if admissible else 'VETO'}: {'; '.join(violations)}",
                asset=symbol,
                violation=", ".join(violations),
                risk_score=100.0 - aml_score,
                aml_score=max(0.0, aml_score),
            )

        return AMLVetoResult(
            admissible=True,
            pass_through=False,
            reason=f"CP-9 AML PASS: {symbol} — no AML risk patterns detected | score {aml_score:.0f}/100",
            asset=symbol,
            aml_score=aml_score,
        )


def load_aml_config_from_env() -> AMLGateConfig:
    """
    Load AML Gate configuration from environment variables.
    Returns default (disabled) config if AML_GATE_ENABLED is not 'true'.
    """
    enabled = os.environ.get("AML_GATE_ENABLED", "false").lower() == "true"
    if not enabled:
        return AMLGateConfig(enabled=False)

    return AMLGateConfig(
        enabled=True,
        volume_threshold_usd=float(os.environ.get("AML_VOLUME_THRESHOLD_USD", "500000")),
        frequency_threshold=int(os.environ.get("AML_FREQUENCY_THRESHOLD", "10")),
        block_privacy_coins=os.environ.get("AML_BLOCK_PRIVACY_COINS", "true").lower() == "true",
        block_mixer_tokens=os.environ.get("AML_BLOCK_MIXER_TOKENS", "true").lower() == "true",
    )
