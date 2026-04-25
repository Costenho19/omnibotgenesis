"""
OMNIX Trajectory Invariant Engine (TIE)
ADR-053: Trajectory Invariant Enforcement

Enforces that governance decisions maintain trajectory-level invariants over time.
Unlike reactive validators (which check current state), TIE constrains which
state transitions are permissible based on the full decision trajectory history.

Architecture position:
    Signals → 8-checkpoint pipeline → [APPROVED] → TIE → APPROVED | HOLD
                                      [BLOCKED]  → (TIE bypassed — already blocked)

Key principle (Rigel Randolph's "bounded evolution"):
    The system must not only reach valid states — it must reach them via
    valid PATHS. TIE enforces that approved decisions do not push the system
    toward globally inadmissible regions, even when each individual decision
    appears valid in isolation.

Invariants enforced:
    1. RISK_MONOTONIC_ASCENT   — risk_exposure trending upward for K+ consecutive decisions → HOLD
    2. PROBABILITY_DEAD_ZONE   — probability_score < threshold for K+ consecutive decisions → HOLD
    3. COHERENCE_STRUCTURAL_DECAY — signal_coherence < threshold for K+ consecutive decisions → HOLD
    4. TRAJECTORY_VOLATILITY   — high variance in probability_score over window → WARNING only
    5. GLOBAL_REGIME_COLLAPSE  — simultaneous degradation across 3+ assets → HOLD escalation

Storage: PostgreSQL `trajectory_states` table (rolling per-asset history).
Fail-safe: TIE exceptions → pass-through (never breaks the main pipeline).
Enabled via: TIE_ENABLED env var (default: true).

Internal use only — not exposed in external API documentation.
"""

from __future__ import annotations

import logging
import os
import statistics
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("OMNIX.TIE")

# ── Configuration ──────────────────────────────────────────────────────────────

TIE_ENABLED_DEFAULT = True
HISTORY_WINDOW = 20           # Max states stored per asset/domain in DB
RISK_ASCENT_WINDOW = 5        # Consecutive decisions for risk ascent invariant
RISK_ASCENT_THRESHOLD = 70    # risk_exposure above this = "high risk"
DEAD_ZONE_WINDOW = 4          # Consecutive decisions for probability dead zone
DEAD_ZONE_THRESHOLD = 35.0    # probability_score below this = dead zone
COHERENCE_DECAY_WINDOW = 3    # Consecutive decisions for coherence decay
COHERENCE_DECAY_THRESHOLD = 40.0   # signal_coherence below this = decay
VOLATILITY_WINDOW = 8         # Window for trajectory volatility calculation
VOLATILITY_THRESHOLD = 32.0   # Std dev above this = high volatility (warning)
GLOBAL_COLLAPSE_ASSET_MIN = 3 # Minimum assets in dead zone for global collapse


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class TrajectoryState:
    asset: str
    domain: str
    decision: str
    probability_score: float
    risk_exposure: float
    signal_coherence: float
    trend_persistence: float
    stress_resilience: float
    logic_consistency: float


@dataclass
class InvariantViolation:
    invariant_id: str
    invariant_name: str
    description: str
    severity: str         # "HOLD" | "WARNING"
    window_size: int
    trigger_value: float
    threshold: float


@dataclass
class TIEResult:
    passed: bool                          # True = no blocking violations
    trajectory_decision: str              # "APPROVED" | "HOLD"
    violations: list[InvariantViolation]
    warnings: list[InvariantViolation]
    trajectory_score: float               # 0–100, higher = healthier trajectory
    window_size: int                      # Actual history entries used
    asset: str
    domain: str
    pass_through_reason: str = ""         # ADR-066: populated when pass_through path taken
    signal_defaults: list = field(        # ADR-073G: signals that defaulted to 50.0 neutral stub
        default_factory=list
    )


# ── Core engine ────────────────────────────────────────────────────────────────

class TrajectoryInvariantEngine:
    """
    Evaluates trajectory-level invariants after the 8-checkpoint pipeline.

    APPROVED decisions may be converted to HOLD if trajectory invariants
    are violated. BLOCKED decisions are never modified by TIE.
    """

    def __init__(self, db_conn=None):
        """
        Args:
            db_conn: Optional psycopg2 connection. If None, TIE runs in
                     memory-only mode (no history persistence, no global collapse).
        """
        self.conn = db_conn
        self._enabled = os.environ.get("TIE_ENABLED", "true").lower() != "false"

    # ── Public API ──────────────────────────────────────────────────────────────

    def evaluate(
        self,
        current_signals: dict[str, float],
        asset: str,
        domain: str,
        current_decision: str,
        receipt_id: str | None = None,
    ) -> TIEResult:
        """
        Evaluate trajectory invariants for the current decision.

        Args:
            current_signals: The 6–8 normalized governance signals (0–100).
            asset: Asset identifier (e.g. 'BTC/USD', 'LOAN-XYZ').
            domain: Evaluation domain ('trading', 'islamic_credit', etc.)
            current_decision: Pipeline output before TIE ('APPROVED' or 'BLOCKED').
            receipt_id: Optional receipt ID for linkage.

        Returns:
            TIEResult — if violations found and current_decision was APPROVED,
            trajectory_decision will be 'HOLD'.
        """
        if not self._enabled:
            return self._pass_through(asset, domain, reason="TIE_DISABLED")

        # TIE only operates on APPROVED decisions
        if current_decision == "BLOCKED":
            return self._pass_through(asset, domain, reason="TIE_BLOCKED_BYPASS")

        try:
            history = self._load_history(asset, domain)
            result = self._run_invariants(current_signals, history, asset, domain)

            self._persist_state(
                current_signals, asset, domain, current_decision,
                receipt_id, result
            )

            if result.violations:
                logger.warning(
                    f"[TIE] HOLD issued for {asset} ({domain}) | "
                    f"Violations: {[v.invariant_id for v in result.violations]} | "
                    f"Window: {result.window_size}"
                )
            elif result.warnings:
                logger.info(
                    f"[TIE] WARNINGS for {asset} ({domain}) | "
                    f"{[w.invariant_id for w in result.warnings]} | "
                    f"TrajectoryScore={result.trajectory_score:.0f}"
                )

            return result

        except Exception as exc:
            logger.warning(f"[TIE] Exception for {asset} — pass-through: {exc}")
            return self._pass_through(
                asset, domain,
                reason=f"TIE_FAILSAFE: score=0 reflects module error, not trajectory health — {exc}"
            )

    def get_trajectory_summary(self, asset: str, domain: str = "generic") -> dict[str, Any]:
        """Return a human-readable trajectory health summary for an asset."""
        try:
            history = self._load_history(asset, domain)
            if not history:
                return {"asset": asset, "domain": domain, "status": "NO_HISTORY", "window": 0}

            avg_prob = statistics.mean(h["probability_score"] for h in history)
            avg_risk = statistics.mean(h["risk_exposure"] for h in history)
            avg_coherence = statistics.mean(h["signal_coherence"] for h in history)
            decisions = [h["decision"] for h in history]
            approved_pct = (decisions.count("APPROVED") / len(decisions)) * 100

            return {
                "asset": asset,
                "domain": domain,
                "window": len(history),
                "avg_probability_score": round(avg_prob, 1),
                "avg_risk_exposure": round(avg_risk, 1),
                "avg_signal_coherence": round(avg_coherence, 1),
                "approval_rate_pct": round(approved_pct, 1),
                "status": "HEALTHY" if avg_prob >= 55 and avg_risk <= 65 else "DEGRADED",
            }
        except Exception:
            return {"asset": asset, "domain": domain, "status": "ERROR", "window": 0}

    # ── Invariant evaluators ────────────────────────────────────────────────────

    def _run_invariants(
        self,
        current: dict[str, float],
        history: list[dict],
        asset: str,
        domain: str,
    ) -> TIEResult:
        """Execute all invariant checks against the current decision + history."""

        violations: list[InvariantViolation] = []
        warnings: list[InvariantViolation] = []

        # ADR-073G: Track which signals are absent from `current` and defaulted to 50.0.
        # 50.0 is a neutral stub — it won't trigger any invariant threshold (all are
        # well above or below 50.0), but it silently biases trajectory history toward
        # a "healthy neutral" state. Documenting defaults allows operators to distinguish
        # "genuinely 50" from "signal missing at evaluation time".
        _TIE_SIGNALS = (
            "probability_score", "risk_exposure", "signal_coherence",
            "trend_persistence", "stress_resilience", "logic_consistency",
        )
        signal_defaults = [
            f"TIE_SIGNAL_DEFAULT_APPLIED:{s}=50.0 (signal absent from caller)"
            for s in _TIE_SIGNALS
            if s not in current
        ]
        if signal_defaults:
            logger.debug(
                f"[TIE] {asset} ({domain}) — {len(signal_defaults)} signal(s) defaulted to 50.0: "
                f"{[s.split(':')[1] for s in signal_defaults]}"
            )

        # Build working window: history (oldest first) + current point
        window = history[-HISTORY_WINDOW:] + [{
            "decision": "PENDING",
            "probability_score": current.get("probability_score", 50.0),
            "risk_exposure": current.get("risk_exposure", 50.0),
            "signal_coherence": current.get("signal_coherence", 50.0),
            "trend_persistence": current.get("trend_persistence", 50.0),
            "stress_resilience": current.get("stress_resilience", 50.0),
            "logic_consistency": current.get("logic_consistency", 50.0),
        }]

        # I-1: Risk Monotonic Ascent
        v = self._check_risk_monotonic_ascent(window)
        if v:
            violations.append(v) if v.severity == "HOLD" else warnings.append(v)

        # I-2: Probability Dead Zone
        v = self._check_probability_dead_zone(window)
        if v:
            violations.append(v) if v.severity == "HOLD" else warnings.append(v)

        # I-3: Coherence Structural Decay
        v = self._check_coherence_structural_decay(window)
        if v:
            violations.append(v) if v.severity == "HOLD" else warnings.append(v)

        # I-4: Trajectory Volatility (warning only)
        v = self._check_trajectory_volatility(window)
        if v:
            warnings.append(v)

        # I-5: Global Regime Collapse (requires DB)
        v = self._check_global_regime_collapse(domain)
        if v:
            violations.append(v) if v.severity == "HOLD" else warnings.append(v)

        has_blocking = len(violations) > 0
        trajectory_score = self._compute_trajectory_score(window, violations, warnings)

        return TIEResult(
            passed=not has_blocking,
            trajectory_decision="HOLD" if has_blocking else "APPROVED",
            violations=violations,
            warnings=warnings,
            trajectory_score=trajectory_score,
            window_size=len(window) - 1,  # exclude the current (pending) point
            asset=asset,
            domain=domain,
            signal_defaults=signal_defaults,  # ADR-073G: signals that defaulted to 50.0
        )

    def _check_risk_monotonic_ascent(self, window: list[dict]) -> InvariantViolation | None:
        """
        I-1: If risk_exposure has been above threshold for K+ consecutive
        decisions AND is trending upward, the trajectory is heading toward
        the inadmissible high-risk region.
        """
        k = RISK_ASCENT_WINDOW
        if len(window) < k:
            return None

        recent = [w["risk_exposure"] for w in window[-k:]]
        above_threshold = all(r > RISK_ASCENT_THRESHOLD for r in recent)
        is_ascending = all(recent[i] <= recent[i + 1] for i in range(len(recent) - 1))

        if above_threshold and is_ascending:
            return InvariantViolation(
                invariant_id="I-1",
                invariant_name="RISK_MONOTONIC_ASCENT",
                description=(
                    f"risk_exposure has been above {RISK_ASCENT_THRESHOLD} "
                    f"and monotonically increasing for {k} consecutive decisions. "
                    f"Trajectory is heading toward inadmissible high-risk region."
                ),
                severity="HOLD",
                window_size=k,
                trigger_value=round(recent[-1], 2),
                threshold=float(RISK_ASCENT_THRESHOLD),
            )
        return None

    def _check_probability_dead_zone(self, window: list[dict]) -> InvariantViolation | None:
        """
        I-2: If probability_score has been below threshold for K+ consecutive
        decisions, the asset is in a "dead zone" — no trajectory exits
        without regime change.
        """
        k = DEAD_ZONE_WINDOW
        if len(window) < k:
            return None

        recent = [w["probability_score"] for w in window[-k:]]
        in_dead_zone = all(p < DEAD_ZONE_THRESHOLD for p in recent)

        if in_dead_zone:
            return InvariantViolation(
                invariant_id="I-2",
                invariant_name="PROBABILITY_DEAD_ZONE",
                description=(
                    f"probability_score has been below {DEAD_ZONE_THRESHOLD} "
                    f"for {k} consecutive decisions. Asset is in trajectory dead zone."
                ),
                severity="HOLD",
                window_size=k,
                trigger_value=round(recent[-1], 2),
                threshold=DEAD_ZONE_THRESHOLD,
            )
        return None

    def _check_coherence_structural_decay(self, window: list[dict]) -> InvariantViolation | None:
        """
        I-3: If signal_coherence has been below threshold for K+ consecutive
        decisions, the system has entered a state of structural incoherence
        that cannot self-correct within the current trajectory.
        """
        k = COHERENCE_DECAY_WINDOW
        if len(window) < k:
            return None

        recent = [w["signal_coherence"] for w in window[-k:]]
        decayed = all(c < COHERENCE_DECAY_THRESHOLD for c in recent)

        if decayed:
            return InvariantViolation(
                invariant_id="I-3",
                invariant_name="COHERENCE_STRUCTURAL_DECAY",
                description=(
                    f"signal_coherence has been below {COHERENCE_DECAY_THRESHOLD} "
                    f"for {k} consecutive decisions. Structural incoherence detected "
                    f"— trajectory is in decay mode."
                ),
                severity="HOLD",
                window_size=k,
                trigger_value=round(recent[-1], 2),
                threshold=COHERENCE_DECAY_THRESHOLD,
            )
        return None

    def _check_trajectory_volatility(self, window: list[dict]) -> InvariantViolation | None:
        """
        I-4 (WARNING): If the standard deviation of probability_score over
        the last N decisions is high, the trajectory is exhibiting chaotic
        behavior — a precursor to regime break.
        """
        k = VOLATILITY_WINDOW
        if len(window) < k:
            return None

        recent = [w["probability_score"] for w in window[-k:]]
        if len(recent) < 2:
            return None

        std_dev = statistics.stdev(recent)
        if std_dev > VOLATILITY_THRESHOLD:
            return InvariantViolation(
                invariant_id="I-4",
                invariant_name="TRAJECTORY_VOLATILITY",
                description=(
                    f"probability_score std_dev={std_dev:.1f} over last {k} decisions "
                    f"exceeds threshold {VOLATILITY_THRESHOLD}. "
                    f"Trajectory shows high volatility — potential regime break."
                ),
                severity="WARNING",
                window_size=k,
                trigger_value=round(std_dev, 2),
                threshold=VOLATILITY_THRESHOLD,
            )
        return None

    def _check_global_regime_collapse(self, domain: str) -> InvariantViolation | None:
        """
        I-5: If 3+ distinct assets simultaneously show probability_score
        in the dead zone, the system has entered a global regime collapse.
        All pending APPROVED decisions in this domain should be held.
        """
        if not self.conn:
            return None

        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT asset, AVG(probability_score) as avg_prob
                FROM (
                    SELECT asset, probability_score,
                           ROW_NUMBER() OVER (PARTITION BY asset ORDER BY recorded_at DESC) as rn
                    FROM trajectory_states
                    WHERE domain = %s
                      AND recorded_at > NOW() - INTERVAL '30 minutes'
                ) sub
                WHERE rn <= 3
                GROUP BY asset
                HAVING AVG(probability_score) < %s
            """, (domain, DEAD_ZONE_THRESHOLD))

            dead_zone_assets = cursor.fetchall()
            cursor.close()

            if len(dead_zone_assets) >= GLOBAL_COLLAPSE_ASSET_MIN:
                asset_list = [r[0] for r in dead_zone_assets]
                return InvariantViolation(
                    invariant_id="I-5",
                    invariant_name="GLOBAL_REGIME_COLLAPSE",
                    description=(
                        f"{len(dead_zone_assets)} assets simultaneously in dead zone "
                        f"(domain={domain}): {', '.join(asset_list[:5])}. "
                        f"Global regime collapse — all APPROVED decisions elevated to HOLD."
                    ),
                    severity="HOLD",
                    window_size=len(dead_zone_assets),
                    trigger_value=float(len(dead_zone_assets)),
                    threshold=float(GLOBAL_COLLAPSE_ASSET_MIN),
                )
        except Exception as e:
            logger.debug(f"[TIE] I-5 check skipped: {e}")

        return None

    # ── Scoring ─────────────────────────────────────────────────────────────────

    def _compute_trajectory_score(
        self,
        window: list[dict],
        violations: list[InvariantViolation],
        warnings: list[InvariantViolation],
    ) -> float:
        """
        Compute a 0–100 trajectory health score.
        100 = perfectly healthy trajectory, 0 = all invariants violated.
        """
        if len(window) < 2:
            return 75.0

        base = 100.0
        base -= len(violations) * 25.0
        base -= len(warnings) * 8.0

        recent = window[-min(5, len(window)):]
        avg_prob = statistics.mean(w["probability_score"] for w in recent)
        avg_coherence = statistics.mean(w["signal_coherence"] for w in recent)

        if avg_prob < 40:
            base -= 15.0
        if avg_coherence < 45:
            base -= 10.0

        return round(max(0.0, min(100.0, base)), 1)

    # ── Persistence ─────────────────────────────────────────────────────────────

    def _load_history(self, asset: str, domain: str) -> list[dict]:
        """Load recent trajectory states from PostgreSQL, oldest-first."""
        if not self.conn:
            return []
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT decision, probability_score, risk_exposure,
                       signal_coherence, trend_persistence,
                       stress_resilience, logic_consistency
                FROM trajectory_states
                WHERE asset = %s AND domain = %s
                ORDER BY recorded_at DESC
                LIMIT %s
            """, (asset, domain, HISTORY_WINDOW))
            rows = cursor.fetchall()
            cursor.close()
            cols = [
                "decision", "probability_score", "risk_exposure",
                "signal_coherence", "trend_persistence",
                "stress_resilience", "logic_consistency",
            ]
            return [dict(zip(cols, row)) for row in reversed(rows)]
        except Exception as e:
            logger.debug(f"[TIE] History load failed for {asset}: {e}")
            return []

    def _persist_state(
        self,
        signals: dict[str, float],
        asset: str,
        domain: str,
        decision: str,
        receipt_id: str | None,
        result: TIEResult,
    ) -> None:
        """Persist current evaluation state into trajectory_states."""
        if not self.conn:
            return
        try:
            violations_str = (
                ",".join(v.invariant_id for v in result.violations)
                if result.violations else None
            )
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO trajectory_states (
                    asset, domain, decision,
                    probability_score, risk_exposure, signal_coherence,
                    trend_persistence, stress_resilience, logic_consistency,
                    receipt_id, tie_applied, tie_hold_issued, tie_violations
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s, %s)
            """, (
                asset, domain, result.trajectory_decision,
                signals.get("probability_score", 50.0),
                signals.get("risk_exposure", 50.0),
                signals.get("signal_coherence", 50.0),
                signals.get("trend_persistence", 50.0),
                signals.get("stress_resilience", 50.0),
                signals.get("logic_consistency", 50.0),
                receipt_id,
                result.trajectory_decision == "HOLD",
                violations_str,
            ))

            # Prune old states: keep only last HISTORY_WINDOW per asset/domain
            cursor.execute("""
                DELETE FROM trajectory_states
                WHERE asset = %s AND domain = %s
                  AND id NOT IN (
                      SELECT id FROM trajectory_states
                      WHERE asset = %s AND domain = %s
                      ORDER BY recorded_at DESC
                      LIMIT %s
                  )
            """, (asset, domain, asset, domain, HISTORY_WINDOW))

            self.conn.commit()
            cursor.close()
        except Exception as e:
            logger.debug(f"[TIE] Persist failed for {asset}: {e}")
            try:
                self.conn.rollback()
            except Exception as _e:
                logger.debug(f"[TIE] Rollback also failed for {asset}: {_e}")

    # ── Helpers ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _pass_through(asset: str, domain: str, reason: str = "") -> TIEResult:
        """
        ADR-066: trajectory_score=0.0 (not 100.0) on any pass-through path.
        score=0 reflects absence of trajectory evaluation, not trajectory failure.
        pass_through_reason distinguishes disabled / blocked-bypass / failsafe.
        """
        return TIEResult(
            passed=True,
            trajectory_decision="APPROVED",
            violations=[],
            warnings=[],
            trajectory_score=0.0,
            window_size=0,
            asset=asset,
            domain=domain,
            pass_through_reason=reason or "TIE_PASS_THROUGH: score=0 reflects absence of trajectory evaluation, not trajectory health",
        )

    @staticmethod
    def result_to_dict(result: TIEResult) -> dict[str, Any]:
        """Serialize TIEResult to dict for inclusion in governance response."""
        d: dict[str, Any] = {
            "enabled": True,
            "trajectory_decision": result.trajectory_decision,
            "trajectory_score": result.trajectory_score,
            "passed": result.passed,
            "window_size": result.window_size,
            "violations": [
                {
                    "id": v.invariant_id,
                    "name": v.invariant_name,
                    "severity": v.severity,
                    "description": v.description,
                    "trigger_value": v.trigger_value,
                    "threshold": v.threshold,
                }
                for v in result.violations
            ],
            "warnings": [
                {
                    "id": w.invariant_id,
                    "name": w.invariant_name,
                    "description": w.description,
                    "trigger_value": w.trigger_value,
                }
                for w in result.warnings
            ],
        }
        if result.pass_through_reason:
            d["pass_through_reason"] = result.pass_through_reason
        return d
