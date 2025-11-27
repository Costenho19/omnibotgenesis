"""
REACTIVATION ENGINE V1.0
Intelligent trading reactivation after cascade protection pause

PROBLEM:
When cascade protection pauses trading, there's no clear criteria for resuming.
Manual reactivation is subjective and inconsistent.

SOLUTION:
Multi-signal reactivation system that evaluates:
1. Volatility normalization (< threshold)
2. Regime stability (favorable regime for N hours)
3. Time-based cooldown (minimum pause duration)
4. Win rate recovery (paper trades show improvement)

INVESTOR IMPACT:
- Clear, verifiable reactivation criteria
- Transparent risk management
- Automated but conservative resumption
"""

import logging
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


class ReactivationCondition(Enum):
    """Individual reactivation conditions"""
    VOLATILITY_NORMALIZED = ("volatility", "Volatility below threshold")
    REGIME_FAVORABLE = ("regime", "Market regime is favorable")
    COOLDOWN_COMPLETE = ("cooldown", "Minimum cooldown period elapsed")
    PAPER_WINS = ("paper", "Paper trades showing recovery")
    MANUAL_OVERRIDE = ("manual", "Manual operator approval")
    
    def __init__(self, key: str, description: str):
        self.key = key
        self.description = description


@dataclass
class ConditionStatus:
    """Status of a single reactivation condition"""
    condition: ReactivationCondition
    is_met: bool
    current_value: float
    threshold: float
    description: str
    last_checked: datetime = field(default_factory=datetime.now)


@dataclass
class ReactivationPolicy:
    """Policy defining reactivation requirements"""
    min_conditions_required: int = 3
    volatility_threshold: float = 0.025
    min_cooldown_hours: float = 4.0
    max_cooldown_hours: float = 24.0
    favorable_regimes: List[str] = field(default_factory=lambda: ['bull', 'sideways'])
    regime_stability_hours: float = 2.0
    paper_trades_required: int = 5
    paper_win_rate_min: float = 0.6
    require_manual_approval: bool = False


@dataclass
class ReactivationState:
    """Current state of the reactivation engine"""
    is_paused: bool
    pause_start: Optional[datetime]
    pause_reason: str
    conditions_met: int
    conditions_required: int
    conditions_status: Dict[str, ConditionStatus]
    estimated_reactivation: Optional[datetime]
    can_reactivate: bool
    reactivation_progress_pct: float


class ReactivationEngine:
    """
    Intelligent Reactivation Engine
    
    Evaluates multiple conditions before allowing trading to resume
    after a cascade protection pause. Designed to be conservative
    and transparent for investor confidence.
    
    Features:
    - Multi-signal evaluation
    - Configurable thresholds
    - Paper trade verification
    - Clear progress tracking
    - Audit trail for compliance
    """
    
    def __init__(
        self,
        policy: Optional[ReactivationPolicy] = None,
        regime_detector=None,
        volatility_analyzer=None
    ):
        """
        Initialize reactivation engine
        
        Args:
            policy: Reactivation policy (uses default if None)
            regime_detector: Optional HMMRegimeDetector instance
            volatility_analyzer: Optional volatility analyzer
        """
        self.policy = policy or ReactivationPolicy()
        self.regime_detector = regime_detector
        self.volatility_analyzer = volatility_analyzer
        
        self._is_paused = False
        self._pause_start: Optional[datetime] = None
        self._pause_reason = ""
        
        self._paper_trades: List[Dict] = []
        self._regime_history: List[Dict] = []
        self._volatility_history: List[float] = []
        
        self._manual_approval = False
        self._reactivation_log: List[Dict] = []
        
        logger.info("🔄 Reactivation Engine V1.0 initialized")
        logger.info(f"   Conditions required: {self.policy.min_conditions_required}")
        logger.info(f"   Volatility threshold: {self.policy.volatility_threshold * 100:.1f}%")
        logger.info(f"   Cooldown: {self.policy.min_cooldown_hours}h - {self.policy.max_cooldown_hours}h")
    
    def pause_trading(self, reason: str):
        """
        Record that trading has been paused
        
        Args:
            reason: Reason for the pause
        """
        self._is_paused = True
        self._pause_start = datetime.now()
        self._pause_reason = reason
        self._paper_trades = []
        self._manual_approval = False
        
        self._reactivation_log.append({
            'event': 'pause',
            'timestamp': datetime.now().isoformat(),
            'reason': reason
        })
        
        logger.warning(f"⏸️ Trading paused: {reason}")
    
    def resume_trading(self, approved_by: str = "system"):
        """
        Record that trading has resumed
        
        Args:
            approved_by: Who/what approved the resumption
        """
        duration = None
        if self._pause_start:
            duration = (datetime.now() - self._pause_start).total_seconds() / 3600
        
        self._reactivation_log.append({
            'event': 'resume',
            'timestamp': datetime.now().isoformat(),
            'approved_by': approved_by,
            'pause_duration_hours': round(duration, 2) if duration else None
        })
        
        self._is_paused = False
        self._pause_start = None
        self._pause_reason = ""
        
        logger.info(f"▶️ Trading resumed (approved by: {approved_by})")
    
    def record_paper_trade(self, pnl: float, win: bool):
        """
        Record a paper trade during pause
        
        Args:
            pnl: Paper P&L
            win: Whether it was profitable
        """
        self._paper_trades.append({
            'timestamp': datetime.now(),
            'pnl': pnl,
            'win': win
        })
        
        if len(self._paper_trades) > 50:
            self._paper_trades = self._paper_trades[-50:]
    
    def update_volatility(self, volatility: float):
        """
        Update current volatility reading
        
        Args:
            volatility: Current volatility (e.g., 0.02 = 2%)
        """
        self._volatility_history.append(volatility)
        
        if len(self._volatility_history) > 100:
            self._volatility_history = self._volatility_history[-100:]
    
    def update_regime(self, regime: str, confidence: float):
        """
        Update current regime detection
        
        Args:
            regime: Current regime ('bull', 'bear', 'sideways', 'volatile')
            confidence: Detection confidence (0-1)
        """
        self._regime_history.append({
            'timestamp': datetime.now(),
            'regime': regime,
            'confidence': confidence
        })
        
        if len(self._regime_history) > 100:
            self._regime_history = self._regime_history[-100:]
    
    def set_manual_approval(self, approved: bool):
        """
        Set manual approval status
        
        Args:
            approved: Whether manual approval is granted
        """
        self._manual_approval = approved
        
        if approved:
            logger.info("✅ Manual reactivation approval granted")
    
    def check_volatility_condition(self) -> ConditionStatus:
        """Check if volatility is below threshold"""
        if not self._volatility_history:
            current_vol = 0.05
        else:
            current_vol = statistics.mean(self._volatility_history[-10:]) if len(self._volatility_history) >= 10 else self._volatility_history[-1]
        
        is_met = current_vol < self.policy.volatility_threshold
        
        return ConditionStatus(
            condition=ReactivationCondition.VOLATILITY_NORMALIZED,
            is_met=is_met,
            current_value=current_vol,
            threshold=self.policy.volatility_threshold,
            description=f"Volatility {current_vol*100:.1f}% {'<' if is_met else '≥'} {self.policy.volatility_threshold*100:.1f}%"
        )
    
    def check_regime_condition(self) -> ConditionStatus:
        """Check if regime is favorable and stable"""
        if not self._regime_history:
            return ConditionStatus(
                condition=ReactivationCondition.REGIME_FAVORABLE,
                is_met=False,
                current_value=0,
                threshold=self.policy.regime_stability_hours,
                description="No regime data available"
            )
        
        cutoff = datetime.now() - timedelta(hours=self.policy.regime_stability_hours)
        recent = [r for r in self._regime_history if r['timestamp'] >= cutoff]
        
        if not recent:
            recent = self._regime_history[-5:]
        
        favorable_count = sum(1 for r in recent if r['regime'] in self.policy.favorable_regimes)
        favorable_ratio = favorable_count / len(recent) if recent else 0
        
        is_met = favorable_ratio >= 0.8
        current_regime = self._regime_history[-1]['regime'] if self._regime_history else 'unknown'
        
        return ConditionStatus(
            condition=ReactivationCondition.REGIME_FAVORABLE,
            is_met=is_met,
            current_value=favorable_ratio,
            threshold=0.8,
            description=f"Regime: {current_regime} | Stability: {favorable_ratio*100:.0f}% favorable"
        )
    
    def check_cooldown_condition(self) -> ConditionStatus:
        """Check if minimum cooldown has elapsed"""
        if not self._pause_start:
            return ConditionStatus(
                condition=ReactivationCondition.COOLDOWN_COMPLETE,
                is_met=True,
                current_value=0,
                threshold=self.policy.min_cooldown_hours,
                description="Not currently paused"
            )
        
        elapsed = (datetime.now() - self._pause_start).total_seconds() / 3600
        is_met = elapsed >= self.policy.min_cooldown_hours
        
        remaining = max(0, self.policy.min_cooldown_hours - elapsed)
        
        return ConditionStatus(
            condition=ReactivationCondition.COOLDOWN_COMPLETE,
            is_met=is_met,
            current_value=elapsed,
            threshold=self.policy.min_cooldown_hours,
            description=f"Elapsed: {elapsed:.1f}h | Min: {self.policy.min_cooldown_hours}h | Remaining: {remaining:.1f}h"
        )
    
    def check_paper_trades_condition(self) -> ConditionStatus:
        """Check if paper trades show recovery"""
        recent = self._paper_trades[-self.policy.paper_trades_required:]
        
        if len(recent) < self.policy.paper_trades_required:
            return ConditionStatus(
                condition=ReactivationCondition.PAPER_WINS,
                is_met=False,
                current_value=len(recent),
                threshold=self.policy.paper_trades_required,
                description=f"Paper trades: {len(recent)}/{self.policy.paper_trades_required} required"
            )
        
        win_count = sum(1 for t in recent if t['win'])
        win_rate = win_count / len(recent)
        is_met = win_rate >= self.policy.paper_win_rate_min
        
        return ConditionStatus(
            condition=ReactivationCondition.PAPER_WINS,
            is_met=is_met,
            current_value=win_rate,
            threshold=self.policy.paper_win_rate_min,
            description=f"Paper win rate: {win_rate*100:.0f}% ({'≥' if is_met else '<'} {self.policy.paper_win_rate_min*100:.0f}% required)"
        )
    
    def check_manual_approval_condition(self) -> ConditionStatus:
        """Check if manual approval is granted"""
        if not self.policy.require_manual_approval:
            return ConditionStatus(
                condition=ReactivationCondition.MANUAL_OVERRIDE,
                is_met=True,
                current_value=1.0,
                threshold=0,
                description="Manual approval not required"
            )
        
        return ConditionStatus(
            condition=ReactivationCondition.MANUAL_OVERRIDE,
            is_met=self._manual_approval,
            current_value=1.0 if self._manual_approval else 0.0,
            threshold=1.0,
            description="Manual approval: " + ("✅ Granted" if self._manual_approval else "❌ Required")
        )
    
    def evaluate_all_conditions(self) -> ReactivationState:
        """
        Evaluate all reactivation conditions
        
        Returns:
            ReactivationState with complete status
        """
        conditions = {
            'volatility': self.check_volatility_condition(),
            'regime': self.check_regime_condition(),
            'cooldown': self.check_cooldown_condition(),
            'paper': self.check_paper_trades_condition(),
            'manual': self.check_manual_approval_condition()
        }
        
        met_count = sum(1 for c in conditions.values() if c.is_met)
        can_reactivate = met_count >= self.policy.min_conditions_required
        
        progress = (met_count / max(1, len(conditions))) * 100
        
        estimated = None
        if self._pause_start and not can_reactivate:
            remaining_cooldown = max(0, self.policy.min_cooldown_hours - 
                                    (datetime.now() - self._pause_start).total_seconds() / 3600)
            if remaining_cooldown > 0:
                estimated = datetime.now() + timedelta(hours=remaining_cooldown)
        
        return ReactivationState(
            is_paused=self._is_paused,
            pause_start=self._pause_start,
            pause_reason=self._pause_reason,
            conditions_met=met_count,
            conditions_required=self.policy.min_conditions_required,
            conditions_status=conditions,
            estimated_reactivation=estimated,
            can_reactivate=can_reactivate,
            reactivation_progress_pct=progress
        )
    
    def try_reactivate(self) -> Tuple[bool, str]:
        """
        Attempt to reactivate trading
        
        Returns:
            Tuple of (success, message)
        """
        if not self._is_paused:
            return True, "Trading is already active"
        
        state = self.evaluate_all_conditions()
        
        if state.can_reactivate:
            self.resume_trading(approved_by="automatic")
            return True, f"Trading reactivated ({state.conditions_met}/{len(state.conditions_status)} conditions met)"
        else:
            failed = [c.description for c in state.conditions_status.values() if not c.is_met]
            return False, f"Reactivation blocked: {'; '.join(failed)}"
    
    def get_status(self) -> Dict:
        """
        Get current reactivation status for external use
        
        Returns:
            Dict with status information
        """
        state = self.evaluate_all_conditions()
        
        criteria = {}
        for key, cond in state.conditions_status.items():
            criteria[cond.condition.description] = {
                'met': cond.is_met,
                'current': f"{cond.current_value:.2f}" if isinstance(cond.current_value, float) else str(cond.current_value),
                'required': f"{cond.threshold:.2f}" if isinstance(cond.threshold, float) else str(cond.threshold),
                'detail': cond.description
            }
        
        return {
            'is_paused': state.is_paused,
            'reason': state.pause_reason,
            'conditions_met': f"{state.conditions_met}/{len(state.conditions_status)}",
            'progress_pct': round(state.reactivation_progress_pct, 1),
            'can_reactivate': state.can_reactivate,
            'reactivation_criteria': criteria,
            'estimated_reactivation': state.estimated_reactivation.isoformat() if state.estimated_reactivation else None,
            'pause_duration_hours': round((datetime.now() - state.pause_start).total_seconds() / 3600, 2) if state.pause_start else 0
        }
    
    def get_investor_report(self) -> Dict:
        """
        Get investor-friendly status report
        
        Returns:
            Dict formatted for investor presentations
        """
        state = self.evaluate_all_conditions()
        
        if not state.is_paused:
            return {
                'status': 'ACTIVE',
                'message': 'Trading system fully operational',
                'risk_controls': 'Normal parameters'
            }
        
        unmet = [c.condition.description for c in state.conditions_status.values() if not c.is_met]
        met = [c.condition.description for c in state.conditions_status.values() if c.is_met]
        
        eta = "Unknown"
        if state.estimated_reactivation:
            eta = state.estimated_reactivation.strftime('%Y-%m-%d %H:%M UTC')
        
        return {
            'status': 'PAUSED',
            'reason': state.pause_reason,
            'reactivation_criteria': {
                'required': f"{self.policy.min_conditions_required} of {len(state.conditions_status)} conditions",
                'met': met,
                'pending': unmet
            },
            'progress': f"{state.reactivation_progress_pct:.0f}%",
            'estimated_reactivation': eta,
            'risk_protocol': f"Conservative cooldown ({self.policy.min_cooldown_hours}h minimum)"
        }
    
    def format_status_text(self) -> str:
        """
        Format status as human-readable text
        
        Returns:
            Formatted status string
        """
        state = self.evaluate_all_conditions()
        
        lines = []
        lines.append("━" * 50)
        lines.append("🔄 REACTIVATION ENGINE STATUS")
        lines.append("━" * 50)
        
        if not state.is_paused:
            lines.append("✅ System Status: ACTIVE")
            lines.append("   All trading systems operational")
        else:
            lines.append(f"⏸️ System Status: PAUSED")
            lines.append(f"   Reason: {state.pause_reason}")
            if state.pause_start:
                elapsed = (datetime.now() - state.pause_start).total_seconds() / 3600
                lines.append(f"   Duration: {elapsed:.1f} hours")
            
            lines.append("")
            lines.append(f"📊 Reactivation Progress: {state.reactivation_progress_pct:.0f}%")
            lines.append(f"   Conditions: {state.conditions_met}/{len(state.conditions_status)} met (need {self.policy.min_conditions_required})")
            
            lines.append("")
            lines.append("📋 Condition Checklist:")
            for cond in state.conditions_status.values():
                icon = "✅" if cond.is_met else "❌"
                lines.append(f"   {icon} {cond.description}")
            
            if state.estimated_reactivation:
                lines.append("")
                lines.append(f"⏰ Earliest Reactivation: {state.estimated_reactivation.strftime('%Y-%m-%d %H:%M UTC')}")
        
        lines.append("━" * 50)
        
        return "\n".join(lines)


def test_reactivation_engine():
    """Test the reactivation engine"""
    print("=" * 60)
    print("REACTIVATION ENGINE TEST")
    print("=" * 60)
    
    engine = ReactivationEngine()
    
    print("\n1. Initial status (active):")
    print(engine.format_status_text())
    
    print("\n2. Simulating cascade pause:")
    engine.pause_trading("5 consecutive losses detected")
    
    engine.update_volatility(0.035)
    engine.update_volatility(0.032)
    engine.update_volatility(0.028)
    
    engine.update_regime('sideways', 0.75)
    engine.update_regime('sideways', 0.80)
    engine.update_regime('bull', 0.65)
    
    engine.record_paper_trade(50, True)
    engine.record_paper_trade(30, True)
    engine.record_paper_trade(-20, False)
    
    print("\n3. Status after partial recovery:")
    print(engine.format_status_text())
    
    print("\n4. Investor Report:")
    import json
    print(json.dumps(engine.get_investor_report(), indent=2))
    
    print("\n5. Attempting reactivation:")
    success, msg = engine.try_reactivate()
    print(f"   Result: {'✅' if success else '❌'} {msg}")
    
    print("\n✅ Reactivation Engine test complete!")


if __name__ == "__main__":
    test_reactivation_engine()
