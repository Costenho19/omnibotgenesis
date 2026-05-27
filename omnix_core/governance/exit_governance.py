#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exit Governance Layer (EGL) — ADR-036 | March 2026

Provides a 3-gate governance pipeline for TRADING EXIT decisions,
complementing the existing 8-checkpoint entry governance pipeline.

THE GAP: Entry decisions pass through 8 checkpoints (SIV, Monte Carlo, RMS,
Coherence Gate, TCV, FTI, ECW, Scoring). Exit decisions are simple price
comparisons (current_price >= take_profit_price). This asymmetry means that
~40% of all capital events (exits) have zero governance.

SOLUTION: 3-gate exit pipeline with PQC-signed exit receipts.

PIPELINE:
  Gate 1: Regime-Adjusted Threshold Gate
           TP/SL are not fixed. They scale with market regime:
           - TRENDING: TP×1.3 (let winners run), SL×0.8 (tighter stop)
           - RANGING:  TP×0.8 (take quicker), SL×1.2 (more noise tolerance)
           - VOLATILE: TP×0.7 / SL×0.7 (both tighter)
           - BEARISH:  TP×0.6 / SL×0.6 (most conservative)

  Gate 2: Exit Coherence Gate
           If the EMA signal direction and position direction agree (e.g.,
           EMA says SELL while we hold a long position with small loss),
           this gate confirms the exit. If they disagree, it may veto.

  Gate 3: TCV Exit Check (optional)
           Reutilizes TemporalCoherenceValidator to check if exit timing
           is coherent with recent system trajectory.

OUTPUT: ExitGovernanceResult with should_exit, adjusted thresholds,
        gate verdicts, and a PQC-signed exit receipt.

FAIL-SAFE: On any EGL module error → should_exit equals the naive
           price-comparison result (existing behavior preserved).

Harold Nunes — OMNIX Decision Governance Infrastructure
"""

import hashlib
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_REGIME_TP_MULTIPLIERS: Dict[str, float] = {
    "TRENDING": 1.3,
    "UPTREND": 1.3,
    "BULLISH": 1.2,
    "RANGING": 0.8,
    "NEUTRAL": 1.0,
    "VOLATILE": 0.7,
    "DOWNTREND": 0.8,
    "BEARISH": 0.6,
}

_REGIME_SL_MULTIPLIERS: Dict[str, float] = {
    "TRENDING": 0.8,
    "UPTREND": 0.8,
    "BULLISH": 0.85,
    "RANGING": 1.2,
    "NEUTRAL": 1.0,
    "VOLATILE": 0.7,
    "DOWNTREND": 0.85,
    "BEARISH": 0.6,
}

_DEFAULT_TP_MULTIPLIER = 1.0
_DEFAULT_SL_MULTIPLIER = 1.0


@dataclass
class ExitGovernanceResult:
    """
    Result of Exit Governance evaluation for a single position.

    Fields:
        should_exit:               True if all gates recommend exit.
        reason:                    Human-readable exit decision reason.
        confidence:                Composite confidence [0-100].
        regime_adjusted_tp:        TP price adjusted for current regime.
        regime_adjusted_sl:        SL price adjusted for current regime.
        gate1_threshold_verdict:   Regime-adjusted threshold gate result.
        gate2_coherence_verdict:   Exit coherence gate result.
        gate3_tcv_verdict:         TCV exit gate result (None if not evaluated).
        regime_used:               Market regime applied in evaluation.
        exit_receipt_id:           UUID of the generated exit receipt.
        pqc_signature:             Dilithium-3 hex signature (or SHA-256 if PQC unavailable).
        pass_through:              True if EGL returned existing decision due to module error.
        timestamp:                 ISO-8601 UTC evaluation timestamp.
    """

    # ADR-122 Fail-Safe Default Policy:
    # should_exit=False means HOLD — the safe direction on uninitialized result.
    # This default is only reached if ExitGovernanceEngine crashes before returning;
    # normal paths always set this field explicitly.
    # NOTE: EGL uses fail-THROUGH (not fail-closed) on error — see pass_through flag.
    should_exit: bool = False
    reason: str = "EGL_UNINITIALIZED"
    confidence: float = 0.0
    regime_adjusted_tp: Optional[float] = None
    regime_adjusted_sl: Optional[float] = None
    gate1_threshold_verdict: bool = False
    gate2_coherence_verdict: bool = False
    gate3_tcv_verdict: Optional[bool] = None
    regime_used: str = "NEUTRAL"
    exit_receipt_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pqc_signature: str = ""
    pass_through: bool = False
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "should_exit": self.should_exit,
            "reason": self.reason,
            "confidence": round(self.confidence, 2),
            "regime_adjusted_tp": (
                round(self.regime_adjusted_tp, 8) if self.regime_adjusted_tp else None
            ),
            "regime_adjusted_sl": (
                round(self.regime_adjusted_sl, 8) if self.regime_adjusted_sl else None
            ),
            "gate1_threshold_verdict": self.gate1_threshold_verdict,
            "gate2_coherence_verdict": self.gate2_coherence_verdict,
            "gate3_tcv_verdict": self.gate3_tcv_verdict,
            "regime_used": self.regime_used,
            "exit_receipt_id": self.exit_receipt_id,
            "pqc_signature": self.pqc_signature[:32] + "..." if len(self.pqc_signature) > 35 else self.pqc_signature,
            "pass_through": self.pass_through,
            "timestamp": self.timestamp,
        }


class ExitGovernanceEngine:
    """
    Exit Governance Engine — ADR-036.

    Evaluates exit decisions through 3 governance gates before executing.
    Generates PQC-signed exit receipts for every evaluated position.

    All gates use fail-safe design: on internal error, the gate returns
    a neutral verdict that does not change the naive exit outcome.
    """

    def __init__(
        self,
        db_url: Optional[str] = None,
        tcv_instance: Any = None,
    ):
        self.db_url = db_url or os.getenv("DATABASE_URL")
        self._tcv = tcv_instance
        self._pqc_keys: Optional[Any] = None
        self._init_pqc()
        self._ensure_db_schema()

    def _init_pqc(self) -> None:
        try:
            from pqc.sign import dilithium3
            self._pqc_keys = dilithium3.keypair()
            self._dilithium3 = dilithium3
            logger.info("🔏 [EGL] Dilithium-3 signing keys initialized")
        except Exception as exc:
            self._pqc_keys = None
            self._dilithium3 = None
            logger.warning("⚠️ [EGL] PQC unavailable (%s) — SHA-256 fallback", exc)

    def _ensure_db_schema(self) -> None:
        if not self.db_url:
            return
        ddl = """
        CREATE TABLE IF NOT EXISTS exit_governance_receipts (
            id SERIAL PRIMARY KEY,
            receipt_id VARCHAR(36) UNIQUE NOT NULL,
            position_id VARCHAR(100),
            symbol VARCHAR(20),
            exit_reason VARCHAR(200),
            regime VARCHAR(50),
            should_exit BOOLEAN,
            gate1_threshold_verdict BOOLEAN,
            gate2_coherence_verdict BOOLEAN,
            gate3_tcv_verdict BOOLEAN,
            regime_adjusted_tp DECIMAL(20,8),
            regime_adjusted_sl DECIMAL(20,8),
            confidence DECIMAL(8,4),
            pqc_signature TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
        try:
            conn = self._get_conn()
            if conn:
                cur = conn.cursor()
                cur.execute(ddl)
                conn.commit()
                cur.close()
                conn.close()
        except Exception as exc:
            logger.warning("[EGL] Schema init failed (non-critical): %s", exc)

    def evaluate_exit(
        self,
        position: Dict[str, Any],
        current_price: float,
        naive_tp_triggered: bool,
        naive_sl_triggered: bool,
        regime: str = "NEUTRAL",
        context: Optional[Dict[str, Any]] = None,
    ) -> ExitGovernanceResult:
        """
        Evaluate whether a position should be exited through the 3-gate pipeline.

        Args:
            position:            Position dict with entry_price, take_profit_price,
                                 stop_loss_price, symbol, action, position_id.
            current_price:       Current market price.
            naive_tp_triggered:  Whether naive TP check (price >= tp_price) is True.
            naive_sl_triggered:  Whether naive SL check (price <= sl_price) is True.
            regime:              Current market regime string.
            context:             Optional dict with ema_signal_direction, recent_ema_scores,
                                 regime_history for coherence/TCV gates.

        Returns:
            ExitGovernanceResult. On any error → pass-through with original naive decision.
        """
        naive_exit = naive_tp_triggered or naive_sl_triggered
        try:
            return self._evaluate_internal(
                position=position,
                current_price=current_price,
                naive_tp_triggered=naive_tp_triggered,
                naive_sl_triggered=naive_sl_triggered,
                regime=regime,
                context=context or {},
                naive_exit=naive_exit,
            )
        except Exception as exc:
            logger.warning(
                "⚠️ [EGL] Exception for %s: %s → pass-through (naive=%s)",
                position.get("symbol", "?"), exc, naive_exit
            )
            result = ExitGovernanceResult(
                should_exit=naive_exit,
                reason="EGL_PASS_THROUGH: module error, using naive exit",
                confidence=50.0,
                pass_through=True,
                regime_used=regime,
            )
            return result

    def _evaluate_internal(
        self,
        position: Dict[str, Any],
        current_price: float,
        naive_tp_triggered: bool,
        naive_sl_triggered: bool,
        regime: str,
        context: Dict[str, Any],
        naive_exit: bool,
    ) -> ExitGovernanceResult:
        symbol = position.get("symbol", "UNKNOWN")
        entry_price = float(position.get("entry_price", current_price))
        tp_price = float(position.get("take_profit_price", current_price * 1.03))
        sl_price = float(position.get("stop_loss_price", current_price * 0.98))
        position_action = str(position.get("action", "BUY")).upper()
        position_id = str(position.get("position_id", str(uuid.uuid4())))
        regime_upper = regime.upper().strip()

        adj_tp, adj_sl = self._gate1_regime_adjusted_thresholds(
            tp_price=tp_price,
            sl_price=sl_price,
            entry_price=entry_price,
            current_price=current_price,
            regime=regime_upper,
        )
        gate1_tp = (current_price >= adj_tp) if position_action == "BUY" else (current_price <= adj_tp)
        gate1_sl = (current_price <= adj_sl) if position_action == "BUY" else (current_price >= adj_sl)
        gate1_verdict = gate1_tp or gate1_sl

        gate2_verdict, gate2_confidence = self._gate2_exit_coherence(
            position_action=position_action,
            current_price=current_price,
            entry_price=entry_price,
            context=context,
        )

        gate3_verdict: Optional[bool] = None
        if self._tcv is not None and naive_exit:
            gate3_verdict = self._gate3_tcv_exit(
                position_action=position_action,
                symbol=symbol,
                context=context,
            )

        should_exit, reason, confidence = self._aggregate_gates(
            gate1=gate1_verdict,
            gate2=gate2_verdict,
            gate3=gate3_verdict,
            gate1_tp=gate1_tp,
            gate1_sl=gate1_sl,
            gate2_confidence=gate2_confidence,
            naive_exit=naive_exit,
            symbol=symbol,
            current_price=current_price,
            adj_tp=adj_tp,
            adj_sl=adj_sl,
            regime=regime_upper,
        )

        receipt_payload = {
            "receipt_id": str(uuid.uuid4()),
            "position_id": position_id,
            "symbol": symbol,
            "exit_reason": reason,
            "regime": regime_upper,
            "should_exit": should_exit,
            "gate1": gate1_verdict,
            "gate2": gate2_verdict,
            "gate3": gate3_verdict,
            "confidence": confidence,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        pqc_sig = self._sign_receipt(receipt_payload)
        self._store_receipt(receipt_payload, pqc_sig, adj_tp, adj_sl)

        logger.info(
            "🚪 [EGL] %s | should_exit=%s | regime=%s | g1=%s g2=%s g3=%s | conf=%.0f",
            symbol, should_exit, regime_upper, gate1_verdict, gate2_verdict, gate3_verdict, confidence
        )

        return ExitGovernanceResult(
            should_exit=should_exit,
            reason=reason,
            confidence=confidence,
            regime_adjusted_tp=adj_tp,
            regime_adjusted_sl=adj_sl,
            gate1_threshold_verdict=gate1_verdict,
            gate2_coherence_verdict=gate2_verdict,
            gate3_tcv_verdict=gate3_verdict,
            regime_used=regime_upper,
            exit_receipt_id=receipt_payload["receipt_id"],
            pqc_signature=pqc_sig,
            pass_through=False,
        )

    def _gate1_regime_adjusted_thresholds(
        self,
        tp_price: float,
        sl_price: float,
        entry_price: float,
        current_price: float,
        regime: str,
    ) -> tuple:
        """
        Adjust TP and SL distances by regime multiplier.

        Regime adjustments apply to the DISTANCE from entry, not the absolute price.
        This preserves the direction of TP/SL while scaling how far away they sit.
        """
        tp_mult = _REGIME_TP_MULTIPLIERS.get(regime, _DEFAULT_TP_MULTIPLIER)
        sl_mult = _REGIME_SL_MULTIPLIERS.get(regime, _DEFAULT_SL_MULTIPLIER)

        tp_distance = abs(tp_price - entry_price)
        sl_distance = abs(sl_price - entry_price)

        adj_tp_dist = tp_distance * tp_mult
        adj_sl_dist = sl_distance * sl_mult

        adj_tp = entry_price + adj_tp_dist
        adj_sl = entry_price - adj_sl_dist

        return round(adj_tp, 8), round(adj_sl, 8)

    def _gate2_exit_coherence(
        self,
        position_action: str,
        current_price: float,
        entry_price: float,
        context: Dict[str, Any],
    ) -> tuple:
        """
        Gate 2: Exit Coherence Check.

        Evaluates whether exiting now is coherent with the EMA signal direction
        and the position's P&L state.

        Returns (verdict, confidence_score).
        """
        ema_direction = str(context.get("ema_signal_direction", "HOLD")).upper()
        unrealized_pnl_pct = (current_price - entry_price) / entry_price if entry_price > 0 else 0.0

        if position_action == "BUY":
            if ema_direction in ("SELL", "BEARISH", "STRONG_SELL"):
                return True, 80.0
            if ema_direction in ("BUY", "BULLISH", "STRONG_BUY") and unrealized_pnl_pct <= -0.005:
                return False, 60.0
            if ema_direction in ("BUY", "BULLISH", "STRONG_BUY") and unrealized_pnl_pct > 0:
                return True, 70.0
            return True, 55.0
        elif position_action == "SELL":
            if ema_direction in ("BUY", "BULLISH", "STRONG_BUY"):
                return True, 80.0
            if ema_direction in ("SELL", "BEARISH", "STRONG_SELL") and unrealized_pnl_pct <= -0.005:
                return False, 60.0
            return True, 55.0
        else:
            return True, 50.0

    def _gate3_tcv_exit(
        self,
        position_action: str,
        symbol: str,
        context: Dict[str, Any],
    ) -> bool:
        """
        Gate 3: TCV Exit Check.

        Reuses TCV in reverse: if the system trajectory suggests strong momentum
        in the position direction, holding is more coherent than exiting.
        If trajectory suggests the trade is running out of steam, exit is coherent.

        Returns True (exit is coherent) or False (exit not yet supported by trajectory).
        """
        try:
            inverse_action = "SELL" if position_action == "BUY" else "BUY"
            tcv_result = self._tcv.validate(
                proposed_action=inverse_action,
                symbol=symbol,
                context=context,
            )
            return tcv_result.admissible
        except Exception as exc:
            logger.warning("[EGL] Gate 3 TCV error: %s → neutral", exc)
            return True

    def _aggregate_gates(
        self,
        gate1: bool,
        gate2: bool,
        gate3: Optional[bool],
        gate1_tp: bool,
        gate1_sl: bool,
        gate2_confidence: float,
        naive_exit: bool,
        symbol: str,
        current_price: float,
        adj_tp: float,
        adj_sl: float,
        regime: str,
    ) -> tuple:
        """
        Aggregate gate results into final exit decision.

        Logic:
        - Gate 1 (regime threshold) is the primary gate. If it says no exit,
          and it's not a clear SL hit, the position is held.
        - Gate 2 (coherence) can override a marginal Gate 1 pass.
        - Gate 3 (TCV) is advisory and only considered when Gate 1 passes.
        - SL hits (gate1_sl) override coherence — capital protection is primary.
        """
        if gate1_sl:
            reason = f"SL_EXIT: Regime-adjusted SL hit ({adj_sl:.2f}) in {regime} regime"
            return True, reason, 90.0

        if gate1_tp and gate2:
            tcv_note = f" | TCV={'OK' if gate3 else 'HOLD'}" if gate3 is not None else ""
            reason = (
                f"TP_EXIT: Regime-adjusted TP hit ({adj_tp:.2f}) in {regime} regime"
                f" | coherence={gate2_confidence:.0f}{tcv_note}"
            )
            confidence = min(95.0, (gate2_confidence + 80.0) / 2.0)
            return True, reason, confidence

        if gate1_tp and not gate2:
            reason = (
                f"TP_HELD: TP hit but exit coherence gate denied "
                f"(EMA contradicts exit at {current_price:.2f})"
            )
            return False, reason, gate2_confidence

        if not gate1 and naive_exit:
            reason = (
                f"REGIME_HOLD: Regime-adjusted thresholds not met in {regime} "
                f"(adj_tp={adj_tp:.2f}, adj_sl={adj_sl:.2f})"
            )
            return False, reason, 65.0

        return False, "NO_EXIT_CONDITION", 50.0

    def _sign_receipt(self, payload: Dict[str, Any]) -> str:
        payload_bytes = json.dumps(payload, sort_keys=True, default=str).encode()
        if self._pqc_keys is not None and self._dilithium3 is not None:
            try:
                public_key, secret_key = self._pqc_keys
                sig = self._dilithium3.sign(payload_bytes, secret_key)
                return sig.hex()
            except Exception as exc:
                logger.warning("[EGL] PQC sign failed: %s → SHA-256", exc)
        return hashlib.sha256(payload_bytes).hexdigest()

    def _store_receipt(
        self,
        payload: Dict[str, Any],
        pqc_sig: str,
        adj_tp: Optional[float],
        adj_sl: Optional[float],
    ) -> None:
        if not self.db_url:
            return
        try:
            conn = self._get_conn()
            if not conn:
                return
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO exit_governance_receipts
                (receipt_id, position_id, symbol, exit_reason, regime,
                 should_exit, gate1_threshold_verdict, gate2_coherence_verdict,
                 gate3_tcv_verdict, regime_adjusted_tp, regime_adjusted_sl,
                 confidence, pqc_signature)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (receipt_id) DO NOTHING
                """,
                (
                    payload.get("receipt_id"),
                    payload.get("position_id"),
                    payload.get("symbol"),
                    payload.get("exit_reason", "")[:200],
                    payload.get("regime"),
                    payload.get("should_exit"),
                    payload.get("gate1"),
                    payload.get("gate2"),
                    payload.get("gate3"),
                    adj_tp,
                    adj_sl,
                    payload.get("confidence"),
                    pqc_sig[:2000] if pqc_sig else None,
                ),
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as exc:
            logger.warning("[EGL] Receipt storage failed (non-critical): %s", exc)

    def _get_conn(self) -> Any:
        if not self.db_url:
            return None
        try:
            import psycopg
            return psycopg.connect(self.db_url)
        except ImportError:
            logger.debug("[EGL] psycopg2 not available — trying psycopg3")
        try:
            import psycopg
            return psycopg.connect(self.db_url)
        except Exception as exc:
            logger.warning("[EGL] psycopg3 connection failed: %s", exc)
            return None


# ── Canonical alias (ADR-122) ─────────────────────────────────────────────────
# ExitGateResult is the preferred name in audit scripts and external tooling.
# ExitGovernanceResult remains the primary class name for backward compatibility.
ExitGateResult = ExitGovernanceResult
