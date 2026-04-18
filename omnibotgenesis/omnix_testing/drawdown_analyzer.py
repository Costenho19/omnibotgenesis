"""
Drawdown Sequencing Analysis
Advanced drawdown pattern detection for institutional risk assessment

FEATURES:
- Drawdown counting and frequency analysis
- Recovery time measurement
- Clustering detection (are losses grouped?)
- Pain Index / Ulcer Index calculation

WHY IT MATTERS:
Two strategies with same Max DD can be very different:
- Strategy A: 1 drawdown of 20%, recovers in 5 days
- Strategy B: 150 small drawdowns, recovers in 45 days avg
Strategy A is 10x better despite same Max DD
"""

import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import statistics

logger = logging.getLogger(__name__)


@dataclass
class Drawdown:
    """Represents a single drawdown event"""
    start_idx: int
    end_idx: int
    recovery_idx: Optional[int]
    depth_pct: float
    duration_periods: int
    recovery_periods: Optional[int]
    peak_value: float
    trough_value: float
    
    @property
    def is_recovered(self) -> bool:
        return self.recovery_idx is not None
    
    def __str__(self) -> str:
        recovery = f"{self.recovery_periods}p" if self.is_recovered else "ongoing"
        return f"DD: {self.depth_pct:.1f}% (dur: {self.duration_periods}p, rec: {recovery})"


@dataclass
class DrawdownReport:
    """Complete drawdown analysis report"""
    count: int
    max_depth_pct: float
    avg_depth_pct: float
    median_depth_pct: float
    avg_recovery_periods: float
    max_recovery_periods: int
    cluster_score: float
    pain_index: float
    ulcer_index: float
    health_grade: str
    warning: str
    drawdowns: List[Drawdown]


class DrawdownAnalyzer:
    """
    Analyze drawdown patterns, not just max drawdown
    
    Detects:
    - Rare but brutal (acceptable)
    - Frequent and small (death by 1000 cuts - bad)
    - Clustered losses (risk cascade - very bad)
    """
    
    def __init__(self, min_drawdown_pct: float = 0.5):
        """
        Initialize analyzer
        
        Args:
            min_drawdown_pct: Minimum drawdown to count (filter noise)
        """
        self.min_drawdown_pct = min_drawdown_pct
    
    def identify_drawdowns(self, equity_curve: List[float]) -> List[Drawdown]:
        """
        Identify all drawdowns in equity curve
        
        Args:
            equity_curve: List of portfolio values over time
        
        Returns:
            List of Drawdown objects
        """
        if len(equity_curve) < 2:
            return []
        
        drawdowns = []
        peak = equity_curve[0]
        peak_idx = 0
        in_drawdown = False
        dd_start = 0
        trough = peak
        trough_idx = 0
        
        for i, value in enumerate(equity_curve):
            if value >= peak:
                if in_drawdown:
                    depth = ((peak - trough) / peak) * 100
                    if depth >= self.min_drawdown_pct:
                        drawdowns.append(Drawdown(
                            start_idx=dd_start,
                            end_idx=trough_idx,
                            recovery_idx=i,
                            depth_pct=depth,
                            duration_periods=trough_idx - dd_start,
                            recovery_periods=i - trough_idx,
                            peak_value=peak,
                            trough_value=trough
                        ))
                    in_drawdown = False
                peak = value
                peak_idx = i
                trough = value
                trough_idx = i
            else:
                if not in_drawdown:
                    in_drawdown = True
                    dd_start = peak_idx
                if value < trough:
                    trough = value
                    trough_idx = i
        
        if in_drawdown:
            depth = ((peak - trough) / peak) * 100
            if depth >= self.min_drawdown_pct:
                drawdowns.append(Drawdown(
                    start_idx=dd_start,
                    end_idx=trough_idx,
                    recovery_idx=None,
                    depth_pct=depth,
                    duration_periods=trough_idx - dd_start,
                    recovery_periods=None,
                    peak_value=peak,
                    trough_value=trough
                ))
        
        return drawdowns
    
    def calculate_clustering(self, drawdowns: List[Drawdown]) -> float:
        """
        Calculate clustering score (0 to 1)
        
        Low clustering (good): Drawdowns spread evenly
        High clustering (bad): Drawdowns happen in bursts
        
        Returns:
            0.0-0.3: Well distributed (good)
            0.3-0.6: Some clustering (acceptable)
            0.6-0.8: Moderate clustering (concerning)
            0.8-1.0: High clustering (red flag)
        """
        if len(drawdowns) < 3:
            return 0.0
        
        gaps = []
        for i in range(1, len(drawdowns)):
            gap = drawdowns[i].start_idx - drawdowns[i-1].end_idx
            gaps.append(max(gap, 1))
        
        if not gaps:
            return 0.0
        
        mean_gap = statistics.mean(gaps)
        std_gap = statistics.stdev(gaps) if len(gaps) > 1 else 0
        
        if mean_gap == 0:
            return 1.0
        
        cv = std_gap / mean_gap
        
        clustering = cv / (1 + cv)
        
        return min(max(clustering, 0), 1)
    
    def calculate_pain_index(self, drawdowns: List[Drawdown]) -> float:
        """
        Calculate Pain Index (modified Ulcer Index)
        
        Combines depth AND duration of drawdowns
        Higher = more painful trading experience
        
        Interpretation:
        < 5: Low pain (comfortable trading)
        5-10: Moderate pain (normal)
        10-20: High pain (stressful)
        > 20: Extreme pain (difficult to sustain)
        """
        if not drawdowns:
            return 0.0
        
        pain_values = [
            (dd.depth_pct ** 2) * (dd.duration_periods + 1)
            for dd in drawdowns
        ]
        
        pain_index = (sum(pain_values) / len(pain_values)) ** 0.5
        
        return pain_index
    
    def calculate_ulcer_index(self, equity_curve: List[float]) -> float:
        """
        Calculate Ulcer Index (Peter Martin's formula)
        
        Measures downside volatility specifically
        Lower is better
        """
        if len(equity_curve) < 2:
            return 0.0
        
        peak = equity_curve[0]
        squared_drawdowns = []
        
        for value in equity_curve:
            if value > peak:
                peak = value
            dd_pct = ((peak - value) / peak) * 100
            squared_drawdowns.append(dd_pct ** 2)
        
        ulcer_index = (sum(squared_drawdowns) / len(squared_drawdowns)) ** 0.5
        
        return ulcer_index
    
    def grade_drawdown_health(
        self,
        count: int,
        avg_recovery: float,
        clustering: float,
        pain_index: float
    ) -> Tuple[str, str]:
        """
        Grade overall drawdown health
        
        Returns:
            (grade, warning_message)
        """
        issues = []
        
        if clustering > 0.7:
            issues.append("High clustering - drawdowns cascade together")
        elif clustering > 0.5:
            issues.append("Moderate clustering detected")
        
        if avg_recovery > 30:
            issues.append(f"Long recovery times ({avg_recovery:.0f} periods avg)")
        elif avg_recovery > 15:
            issues.append(f"Moderate recovery times ({avg_recovery:.0f} periods)")
        
        if count > 100:
            issues.append(f"Many drawdowns ({count}) - death by 1000 cuts risk")
        elif count > 50:
            issues.append(f"Frequent drawdowns ({count})")
        
        if pain_index > 20:
            issues.append(f"High pain index ({pain_index:.1f})")
        elif pain_index > 10:
            issues.append(f"Moderate pain index ({pain_index:.1f})")
        
        if len(issues) == 0:
            grade = "A"
            warning = "Healthy drawdown pattern"
        elif len(issues) == 1:
            grade = "B"
            warning = issues[0]
        elif len(issues) == 2:
            grade = "C"
            warning = "; ".join(issues)
        elif len(issues) == 3:
            grade = "D"
            warning = "; ".join(issues)
        else:
            grade = "F"
            warning = "; ".join(issues)
        
        return grade, warning
    
    def analyze(self, equity_curve: List[float]) -> DrawdownReport:
        """
        Complete drawdown analysis
        
        Args:
            equity_curve: List of portfolio values over time
        
        Returns:
            DrawdownReport with all metrics
        """
        drawdowns = self.identify_drawdowns(equity_curve)
        
        if not drawdowns:
            return DrawdownReport(
                count=0,
                max_depth_pct=0.0,
                avg_depth_pct=0.0,
                median_depth_pct=0.0,
                avg_recovery_periods=0.0,
                max_recovery_periods=0,
                cluster_score=0.0,
                pain_index=0.0,
                ulcer_index=self.calculate_ulcer_index(equity_curve),
                health_grade="A",
                warning="No significant drawdowns detected",
                drawdowns=[]
            )
        
        depths = [dd.depth_pct for dd in drawdowns]
        recoveries = [dd.recovery_periods for dd in drawdowns if dd.is_recovered and dd.recovery_periods is not None]
        
        max_depth = max(depths)
        avg_depth = statistics.mean(depths)
        median_depth = statistics.median(depths)
        
        avg_recovery = statistics.mean(recoveries) if recoveries else 0
        max_recovery = max(recoveries) if recoveries else 0
        
        clustering = self.calculate_clustering(drawdowns)
        pain_index = self.calculate_pain_index(drawdowns)
        ulcer_index = self.calculate_ulcer_index(equity_curve)
        
        grade, warning = self.grade_drawdown_health(
            count=len(drawdowns),
            avg_recovery=avg_recovery,
            clustering=clustering,
            pain_index=pain_index
        )
        
        return DrawdownReport(
            count=len(drawdowns),
            max_depth_pct=round(max_depth, 2),
            avg_depth_pct=round(avg_depth, 2),
            median_depth_pct=round(median_depth, 2),
            avg_recovery_periods=round(avg_recovery, 1),
            max_recovery_periods=max_recovery,
            cluster_score=round(clustering, 2),
            pain_index=round(pain_index, 2),
            ulcer_index=round(ulcer_index, 2),
            health_grade=grade,
            warning=warning,
            drawdowns=drawdowns
        )
    
    def generate_investor_summary(self, report: DrawdownReport) -> str:
        """Generate investor-ready text summary"""
        summary = f"""
DRAWDOWN SEQUENCING ANALYSIS
{'=' * 50}

OVERALL HEALTH GRADE: {report.health_grade}
{report.warning}

KEY METRICS:
  Total Drawdowns: {report.count}
  Max Depth: {report.max_depth_pct:.1f}%
  Average Depth: {report.avg_depth_pct:.1f}%
  Median Depth: {report.median_depth_pct:.1f}%

RECOVERY ANALYSIS:
  Avg Recovery Time: {report.avg_recovery_periods:.0f} periods
  Max Recovery Time: {report.max_recovery_periods} periods

RISK INDICATORS:
  Clustering Score: {report.cluster_score:.0%} {'(concerning)' if report.cluster_score > 0.5 else '(healthy)'}
  Pain Index: {report.pain_index:.1f} {'(high)' if report.pain_index > 10 else '(acceptable)'}
  Ulcer Index: {report.ulcer_index:.1f}

{'=' * 50}
INTERPRETATION:
"""
        if report.health_grade in ["A", "B"]:
            summary += """
The strategy shows a healthy drawdown pattern with:
- Reasonable recovery times
- Well-distributed losses (not clustered)
- Manageable pain levels for investors
"""
        elif report.health_grade == "C":
            summary += """
The strategy has some drawdown concerns that warrant monitoring:
- Recovery may take longer than ideal
- Some clustering of losses detected
- Consider position sizing adjustments
"""
        else:
            summary += """
The strategy shows concerning drawdown patterns:
- Losses tend to cluster together (risk cascade)
- Recovery times may be extended
- High pain levels may cause investor anxiety
- Recommend strategy modifications before live trading
"""
        
        return summary


if __name__ == "__main__":
    print("=" * 60)
    print("DRAWDOWN SEQUENCING ANALYSIS - TEST")
    print("=" * 60)
    
    import random
    random.seed(42)
    
    equity: List[float] = [100000.0]
    for i in range(250):
        change = random.gauss(0.001, 0.02)
        equity.append(float(equity[-1] * (1 + change)))
    
    analyzer = DrawdownAnalyzer(min_drawdown_pct=1.0)
    report = analyzer.analyze(equity)
    
    print(f"\nTotal Drawdowns: {report.count}")
    print(f"Max Depth: {report.max_depth_pct:.1f}%")
    print(f"Avg Depth: {report.avg_depth_pct:.1f}%")
    print(f"Avg Recovery: {report.avg_recovery_periods:.0f} periods")
    print(f"Clustering: {report.cluster_score:.0%}")
    print(f"Pain Index: {report.pain_index:.1f}")
    print(f"Ulcer Index: {report.ulcer_index:.1f}")
    print(f"Health Grade: {report.health_grade}")
    print(f"Warning: {report.warning}")
    
    if report.drawdowns:
        print("\nTop 5 Largest Drawdowns:")
        sorted_dds = sorted(report.drawdowns, key=lambda x: x.depth_pct, reverse=True)[:5]
        for i, dd in enumerate(sorted_dds, 1):
            print(f"  {i}. {dd}")
    
    print(analyzer.generate_investor_summary(report))
