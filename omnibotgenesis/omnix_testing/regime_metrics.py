"""
Regime-Adjusted Performance Metrics
PhD-level portfolio analysis for institutional investors

FEATURES:
- Weighted Sharpe Ratio by regime frequency
- Consistency Score (does it work in ALL regimes?)
- Bear Market Performance Grade (A+ to F)
- Worst Regime Identification

WHY IT MATTERS:
- Investors want to know if strategy works consistently
- Not just "Sharpe is 2.5" but "B grade in bear markets"
- Transparency about weak points builds trust
"""

import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import statistics

logger = logging.getLogger(__name__)


@dataclass
class RegimePerformance:
    """Performance metrics for a single regime"""
    regime_name: str
    sharpe_ratio: float
    total_return_pct: float
    max_drawdown_pct: float
    win_rate_pct: float
    trade_count: int
    
    def grade(self) -> str:
        """Grade performance A+ to F"""
        if self.sharpe_ratio > 2.0:
            return "A+"
        elif self.sharpe_ratio > 1.5:
            return "A"
        elif self.sharpe_ratio > 1.0:
            return "B+"
        elif self.sharpe_ratio > 0.5:
            return "B"
        elif self.sharpe_ratio > 0.0:
            return "C"
        elif self.sharpe_ratio > -0.5:
            return "D"
        else:
            return "F"


@dataclass
class RegimeReport:
    """Complete regime-adjusted performance report"""
    weighted_sharpe: float
    consistency_score: float
    bear_grade: str
    worst_regime: str
    worst_sharpe: float
    best_regime: str
    best_sharpe: float
    regime_breakdown: Dict[str, Dict]
    investor_summary: str


class RegimeMetrics:
    """
    Calculate regime-adjusted performance metrics
    
    Uses historical regime frequencies to weight performance
    """
    
    REGIME_WEIGHTS = {
        "bull": 0.25,
        "bear": 0.25,
        "sideways": 0.35,
        "volatile": 0.15
    }
    
    REGIME_DESCRIPTIONS = {
        "bull": "Strong uptrend (2020-2021 bull run)",
        "bear": "Strong downtrend (2022 crypto winter)",
        "sideways": "Range-bound market (2023 consolidation)",
        "volatile": "High volatility (COVID crash, flash crashes)"
    }
    
    def __init__(self, results_by_regime: Optional[Dict[str, Dict]] = None):
        """
        Initialize with regime results
        
        Args:
            results_by_regime: {
                "bull": {"sharpe": 2.1, "returns": [...], "drawdown": -8.5},
                "bear": {"sharpe": 0.8, "returns": [...], "drawdown": -15.2},
                ...
            }
        """
        self.results = results_by_regime or {}
    
    def set_regime_results(self, results: Dict[str, Dict]):
        """Set or update regime results"""
        self.results = results
    
    def add_regime_result(
        self,
        regime: str,
        sharpe: float,
        returns: List[float],
        max_drawdown: float = 0,
        win_rate: float = 50.0,
        trade_count: int = 0
    ):
        """Add result for a single regime"""
        self.results[regime] = {
            "sharpe": sharpe,
            "returns": returns,
            "max_drawdown": max_drawdown,
            "win_rate": win_rate,
            "trade_count": trade_count
        }
    
    def calculate_weighted_sharpe(self) -> float:
        """
        Calculate Sharpe ratio weighted by historical regime frequency
        
        This gives a more realistic expected Sharpe than simple average
        """
        if not self.results:
            return 0.0
        
        total_weight = 0
        weighted_sum = 0
        
        for regime, weight in self.REGIME_WEIGHTS.items():
            if regime in self.results:
                sharpe = self.results[regime].get("sharpe", 0)
                weighted_sum += sharpe * weight
                total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return weighted_sum / total_weight * (sum(self.REGIME_WEIGHTS.values()))
    
    def calculate_consistency_score(self) -> float:
        """
        Calculate consistency across regimes (0 to 1)
        
        1.0 = Identical performance in all regimes (impossible)
        0.8+ = Very consistent (excellent)
        0.6-0.8 = Reasonably consistent (good)
        0.4-0.6 = Inconsistent (concerning)
        <0.4 = Highly inconsistent (red flag)
        """
        if len(self.results) < 2:
            return 1.0
        
        sharpes = [r.get("sharpe", 0) for r in self.results.values()]
        
        mean_sharpe = statistics.mean(sharpes)
        if mean_sharpe == 0:
            return 0.0
        
        std_sharpe = statistics.stdev(sharpes) if len(sharpes) > 1 else 0
        
        cv = std_sharpe / abs(mean_sharpe) if mean_sharpe != 0 else float('inf')
        
        consistency = 1 / (1 + cv)
        
        return min(max(consistency, 0), 1)
    
    def grade_bear_performance(self) -> Tuple[str, str]:
        """
        Grade performance specifically in bear markets
        
        Returns:
            (grade, explanation)
        """
        if "bear" not in self.results:
            return "N/A", "No bear market data available"
        
        bear_sharpe = self.results["bear"].get("sharpe", 0)
        bear_dd = self.results["bear"].get("max_drawdown", 0)
        
        if bear_sharpe > 1.0:
            grade = "A+"
            explanation = f"Exceptional: Sharpe {bear_sharpe:.2f} even in bear markets"
        elif bear_sharpe > 0.5:
            grade = "A"
            explanation = f"Excellent: Positive returns (Sharpe {bear_sharpe:.2f}) during downtrends"
        elif bear_sharpe > 0.0:
            grade = "B"
            explanation = f"Good: Slightly positive (Sharpe {bear_sharpe:.2f}) in bear markets"
        elif bear_sharpe > -0.3:
            grade = "C"
            explanation = f"Acceptable: Minor losses (Sharpe {bear_sharpe:.2f}) in bear markets"
        elif bear_sharpe > -0.7:
            grade = "D"
            explanation = f"Weak: Significant losses (Sharpe {bear_sharpe:.2f}) in bear markets"
        else:
            grade = "F"
            explanation = f"Poor: Severe losses (Sharpe {bear_sharpe:.2f}) during downtrends"
        
        return grade, explanation
    
    def identify_extremes(self) -> Tuple[Tuple[str, float], Tuple[str, float]]:
        """Identify best and worst performing regimes"""
        if not self.results:
            return ("N/A", 0.0), ("N/A", 0.0)
        
        sorted_regimes = sorted(
            self.results.items(),
            key=lambda x: x[1].get("sharpe", 0)
        )
        
        worst = sorted_regimes[0]
        best = sorted_regimes[-1]
        
        return (
            (worst[0], worst[1].get("sharpe", 0)),
            (best[0], best[1].get("sharpe", 0))
        )
    
    def generate_investor_summary(self) -> str:
        """Generate investor-ready text summary"""
        weighted_sharpe = self.calculate_weighted_sharpe()
        consistency = self.calculate_consistency_score()
        bear_grade, bear_explanation = self.grade_bear_performance()
        (worst_regime, worst_sharpe), (best_regime, best_sharpe) = self.identify_extremes()
        
        summary = f"""
REGIME-ADJUSTED PERFORMANCE ANALYSIS
{'=' * 50}

WEIGHTED SHARPE RATIO: {weighted_sharpe:.2f}
(Weighted by historical regime frequency)

CONSISTENCY SCORE: {consistency:.0%}
{'Excellent' if consistency > 0.7 else 'Good' if consistency > 0.5 else 'Needs Improvement'}

BEAR MARKET GRADE: {bear_grade}
{bear_explanation}

BEST PERFORMING REGIME: {best_regime.upper()}
Sharpe Ratio: {best_sharpe:.2f}

WORST PERFORMING REGIME: {worst_regime.upper()}
Sharpe Ratio: {worst_sharpe:.2f}

REGIME BREAKDOWN:
"""
        for regime, data in self.results.items():
            sharpe = data.get("sharpe", 0)
            dd = data.get("max_drawdown", 0)
            wr = data.get("win_rate", 50)
            weight = self.REGIME_WEIGHTS.get(regime, 0) * 100
            
            summary += f"""
  {regime.upper()} ({weight:.0f}% of time):
    Sharpe: {sharpe:.2f}
    Max DD: {dd:.1f}%
    Win Rate: {wr:.1f}%
"""
        
        summary += f"""
{'=' * 50}
INVESTOR TRANSPARENCY NOTE:
This analysis shows performance across different market
conditions. The weighted Sharpe of {weighted_sharpe:.2f} reflects
expected performance given historical regime frequencies.
Worst case scenario is {worst_regime} markets.
"""
        
        return summary
    
    def generate_report(self) -> RegimeReport:
        """Generate complete regime report"""
        weighted_sharpe = self.calculate_weighted_sharpe()
        consistency = self.calculate_consistency_score()
        bear_grade, bear_explanation = self.grade_bear_performance()
        (worst_regime, worst_sharpe), (best_regime, best_sharpe) = self.identify_extremes()
        
        regime_breakdown = {}
        for regime, data in self.results.items():
            regime_breakdown[regime] = {
                "sharpe": round(data.get("sharpe", 0), 2),
                "max_drawdown": round(data.get("max_drawdown", 0), 1),
                "win_rate": round(data.get("win_rate", 50), 1),
                "trade_count": data.get("trade_count", 0),
                "weight": self.REGIME_WEIGHTS.get(regime, 0),
                "grade": RegimePerformance(
                    regime, data.get("sharpe", 0), 0, 0, 0, 0
                ).grade()
            }
        
        return RegimeReport(
            weighted_sharpe=round(weighted_sharpe, 2),
            consistency_score=round(consistency, 2),
            bear_grade=bear_grade,
            worst_regime=worst_regime,
            worst_sharpe=round(worst_sharpe, 2),
            best_regime=best_regime,
            best_sharpe=round(best_sharpe, 2),
            regime_breakdown=regime_breakdown,
            investor_summary=self.generate_investor_summary()
        )


if __name__ == "__main__":
    print("=" * 60)
    print("REGIME-ADJUSTED METRICS - TEST")
    print("=" * 60)
    
    test_results = {
        "bull": {
            "sharpe": 2.5,
            "returns": [0.02, 0.03, 0.01, 0.04, 0.02],
            "max_drawdown": -8.5,
            "win_rate": 68,
            "trade_count": 45
        },
        "bear": {
            "sharpe": 0.7,
            "returns": [0.01, -0.01, 0.02, -0.005, 0.01],
            "max_drawdown": -15.2,
            "win_rate": 52,
            "trade_count": 38
        },
        "sideways": {
            "sharpe": 0.4,
            "returns": [0.005, -0.003, 0.002, 0.001, -0.002],
            "max_drawdown": -6.8,
            "win_rate": 48,
            "trade_count": 62
        },
        "volatile": {
            "sharpe": 1.2,
            "returns": [0.03, -0.02, 0.04, -0.01, 0.02],
            "max_drawdown": -12.3,
            "win_rate": 55,
            "trade_count": 28
        }
    }
    
    metrics = RegimeMetrics(test_results)
    report = metrics.generate_report()
    
    print(f"\nWeighted Sharpe: {report.weighted_sharpe}")
    print(f"Consistency Score: {report.consistency_score:.0%}")
    print(f"Bear Grade: {report.bear_grade}")
    print(f"Best Regime: {report.best_regime} ({report.best_sharpe})")
    print(f"Worst Regime: {report.worst_regime} ({report.worst_sharpe})")
    
    print("\nRegime Breakdown:")
    for regime, data in report.regime_breakdown.items():
        print(f"  {regime}: Sharpe={data['sharpe']}, Grade={data['grade']}")
    
    print("\n" + report.investor_summary)
