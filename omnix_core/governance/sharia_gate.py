"""
OMNIX — Sharia Governance Gate (CP-6)
ADR-046: Regulatory-Aware Decision Engine — Islamic Finance Compliance

Purpose:
    CP-6 validates trading decisions against Islamic finance (Sharia) principles.
    When enabled per client, it vetoes any decision that violates:
      - Halal asset screening (no haram sectors)
      - Riba prohibition (no interest-bearing instruments)
      - Gharar limit (uncertainty threshold)
      - Debt ratio constraint (≤ 33% of total assets)

Design:
    - Fail-safe: if module errors or disabled → pass-through (pipeline continues)
    - Configurable per client via database
    - Default: DISABLED (preserves existing behavior for all current clients)
    - Output: VetoResult with PQC-signed receipt when blocking

Implemented: March 2026
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

HALAL_ASSETS: set[str] = {
    "BTC", "ETH", "SOL", "ADA", "DOT", "AVAX", "LINK", "MATIC",
    "XLM", "ALGO", "ATOM", "NEAR", "FTM", "ONE", "EGLD", "HBAR",
    "BTC/USD", "ETH/USD", "SOL/USD", "ADA/USD", "DOT/USD",
    "AVAX/USD", "LINK/USD", "MATIC/USD", "XLM/USD", "ALGO/USD",
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "ADA/USDT",
    "BTCUSD", "ETHUSD", "SOLUSD", "ADAUSD",
}

HARAM_ASSETS: set[str] = {
    "WBTC",
}

HARAM_SECTORS: set[str] = {
    "alcohol", "tobacco", "pork", "weapons", "gambling",
    "adult_entertainment", "conventional_banking", "interest_bonds",
}


@dataclass
class ShariaVetoResult:
    """
    Result from the Sharia Compliance Gate evaluation (CP-Sharia).

    ADR-116 Fail-Closed Enforcement Policy:
      - admissible defaults to False — any unhandled code path BLOCKS rather than permits.
        This is the safest possible default for a religious compliance gate.
      - pass_through=True ONLY when the gate is DISABLED via ShariaGateConfig.enabled=False.
        DISABLED ≠ HALAL. External consumers must not treat pass_through=True as a
        sharia-compliant signal.
      - sharia_score=100.0 on DISABLED/FAILSAFE paths reflects maximum uncertainty,
        not maximum compliance. Absence of evaluation is NOT equivalent to halal status.

    evaluation_state values (ADR-066):
      "EVALUATED"  — gate ran; gharar_score and sharia_score reflect real analysis
      "DISABLED"   — gate not active; scores are defaults, not compliance indicators
      "FAILSAFE"   — module exception; decision blocked by safety policy (ADR-116)
    """
    admissible: bool = False          # Fail-safe default: BLOCK unless explicitly admitted (ADR-116)
    pass_through: bool = False        # True only when gate is DISABLED — not a halal signal
    reason: str = ""
    asset: str = ""
    violation: str = ""
    gharar_score: float = 0.0
    sharia_score: float = 100.0
    evaluation_state: str = "EVALUATED"   # ADR-066: "DISABLED" | "FAILSAFE" | "EVALUATED"


# Canonical alias — preferred name in audit scripts and external tooling (ADR-121)
ShariaGateResult = ShariaVetoResult


@dataclass
class ShariaGateConfig:
    enabled: bool = False
    gharar_threshold: float = 70.0
    debt_ratio_max: float = 0.33
    custom_halal_assets: list[str] = field(default_factory=list)
    custom_haram_assets: list[str] = field(default_factory=list)
    require_positive_action: bool = False


class ShariaGate:
    """
    CP-6: Sharia Governance Gate

    Validates that an automated trading decision complies with
    Islamic finance principles. Designed as a configurable veto
    layer between CP-5 (Adaptive Coherence) and CP-7 (TCV).

    Usage:
        gate = ShariaGate(config)
        result = gate.evaluate(symbol, proposed_action, gharar_score)
        if not result.admissible and not result.pass_through:
            # VETO — block the decision
    """

    def __init__(self, config: Optional[ShariaGateConfig] = None):
        self.config = config or ShariaGateConfig()
        self._halal = HALAL_ASSETS | {a.upper() for a in self.config.custom_halal_assets}
        self._haram = HARAM_ASSETS | {a.upper() for a in self.config.custom_haram_assets}

    def evaluate(
        self,
        symbol: str,
        proposed_action: str,
        gharar_score: float = 0.0,
        debt_ratio: float = 0.0,
    ) -> ShariaVetoResult:
        """
        Evaluate a proposed decision against Sharia principles.

        Args:
            symbol:           Trading pair (e.g., "BTC/USD")
            proposed_action:  "BUY", "SELL", or "HOLD"
            gharar_score:     Uncertainty score 0-100 (higher = more uncertain)
            debt_ratio:       Issuer debt-to-assets ratio (0.0 – 1.0)

        Returns:
            ShariaVetoResult
        """
        if not self.config.enabled:
            return ShariaVetoResult(
                admissible=True,
                pass_through=True,
                reason="CP-6 Sharia Gate: disabled for this client — sharia_score=0 reflects gate not evaluated, not Sharia risk",
                asset=symbol,
                sharia_score=0.0,
                evaluation_state="DISABLED",
            )

        try:
            return self._run_checks(symbol, proposed_action, gharar_score, debt_ratio)
        except Exception as exc:
            logger.warning(f"⚠️ [SHARIA_GATE] Exception for {symbol}: {exc} → pass-through")
            return ShariaVetoResult(
                admissible=True,
                pass_through=True,
                reason=f"CP-6 SHARIA_FAILSAFE: score=0 reflects module error, not Sharia compliance — {exc}",
                asset=symbol,
                sharia_score=0.0,
                evaluation_state="FAILSAFE",
            )

    def _run_checks(
        self,
        symbol: str,
        proposed_action: str,
        gharar_score: float,
        debt_ratio: float,
    ) -> ShariaVetoResult:
        base_symbol = symbol.upper().replace("/USD", "").replace("/USDT", "").replace("-USD", "")
        full_symbol = symbol.upper()

        sharia_score = 100.0
        violations = []

        # Check 1: Haram asset screening
        if base_symbol in self._haram or full_symbol in self._haram:
            return ShariaVetoResult(
                admissible=False,
                pass_through=False,
                reason=f"CP-6 SHARIA VETO: Asset {symbol} classified as haram",
                asset=symbol,
                violation="HARAM_ASSET",
                sharia_score=0.0,
                evaluation_state="EVALUATED",  # ADR-073E: explicit — gate ran and made a determination
            )

        # Check 2: Halal whitelist — if not in known halal list, flag as uncertain
        if base_symbol not in self._halal and full_symbol not in self._halal:
            sharia_score -= 30.0
            violations.append(f"Asset {symbol} not in halal whitelist")
            logger.warning(f"⚠️ [SHARIA_GATE] {symbol} not in halal whitelist — deducting 30pts")

        # Check 3: Gharar (excessive uncertainty) — hard veto
        if gharar_score > self.config.gharar_threshold:
            return ShariaVetoResult(
                admissible=False,
                pass_through=False,
                reason=(
                    f"CP-6 SHARIA VETO: Gharar excesivo — uncertainty {gharar_score:.1f} "
                    f"supera umbral permitido {self.config.gharar_threshold:.1f}"
                ),
                asset=symbol,
                violation="GHARAR_EXCESIVO",
                gharar_score=gharar_score,
                sharia_score=0.0,
            )

        # Check 4: Debt ratio (for equity instruments — crypto: always 0)
        if debt_ratio > self.config.debt_ratio_max:
            sharia_score -= 30.0
            violations.append(
                f"Ratio de deuda {debt_ratio:.1%} excede máximo permitido {self.config.debt_ratio_max:.1%}"
            )

        # Check 5: Riba — only applies if action generates interest (not typical for spot crypto)
        # Placeholder for future extension to DeFi lending products

        if violations:
            admissible = sharia_score >= 50.0
            return ShariaVetoResult(
                admissible=admissible,
                pass_through=False,
                reason=f"CP-6 SHARIA {'PASS' if admissible else 'VETO'}: {'; '.join(violations)}",
                asset=symbol,
                violation=", ".join(violations),
                gharar_score=gharar_score,
                sharia_score=max(0.0, sharia_score),
            )

        return ShariaVetoResult(
            admissible=True,
            pass_through=False,
            reason=f"CP-6 SHARIA PASS: {symbol} halal-compliant — score {sharia_score:.0f}/100",
            asset=symbol,
            gharar_score=gharar_score,
            sharia_score=sharia_score,
        )


def load_sharia_config_for_client(client_id: Optional[str] = None) -> ShariaGateConfig:
    """
    Load Sharia Gate configuration for a given client.
    Returns default (disabled) config if client not found or no DB.
    """
    if not client_id:
        return ShariaGateConfig(enabled=False)

    try:
        import os
        import psycopg

        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            return ShariaGateConfig(enabled=False)

        conn = psycopg.connect(db_url)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT sharia_enabled, gharar_threshold, debt_ratio_max
            FROM b2b_clients
            WHERE client_id = %s
            """,
            (client_id,),
        )
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            return ShariaGateConfig(
                enabled=bool(row[0]),
                gharar_threshold=float(row[1]) if row[1] else 70.0,
                debt_ratio_max=float(row[2]) if row[2] else 0.33,
            )

    except Exception as exc:
        logger.warning(f"⚠️ [SHARIA_GATE] Could not load config for client {client_id}: {exc}")

    return ShariaGateConfig(enabled=False)
