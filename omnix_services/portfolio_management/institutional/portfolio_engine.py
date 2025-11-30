"""
OMNIX V6.4 INSTITUTIONAL+ Portfolio Engine
Unified integration layer - combines all institutional modules
The brain that orchestrates portfolio construction
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .risk_model_engine import RiskModelEngine, RiskMetrics
from .portfolio_optimizer import PortfolioOptimizer, OptimizationResult, OptimizationMode
from .volatility_targeting import VolatilityTargetingEngine, VolTargetResult, RiskProfile
from .exposure_manager import ExposureManager, ExposureReport
from .clustering_risk import ClusteringRiskDetector, ClusterRiskReport

logger = logging.getLogger(__name__)


@dataclass
class PortfolioSnapshot:
    """Complete portfolio state at a point in time"""
    weights: Dict[str, float]
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    portfolio_beta: float
    effective_n_assets: float
    diversification_score: float
    net_exposure: float
    gross_exposure: float
    sector_exposures: Dict[str, float]
    cluster_warnings: List[str]
    risk_profile: str
    timestamp: datetime
    version: str


@dataclass
class RebalanceOrder:
    """Order generated from rebalancing"""
    symbol: str
    side: str
    weight_change: float
    current_weight: float
    target_weight: float
    priority: int
    reason: str


class OmnixPortfolioEngine:
    """
    OMNIX V6.4 INSTITUTIONAL+ Portfolio Engine
    
    The MASTER orchestrator that combines all institutional modules:
    1. RiskModelEngine - Covariance, correlation, beta
    2. PortfolioOptimizer - Markowitz + Black-Litterman
    3. VolatilityTargetingEngine - Dynamic sizing
    4. ExposureManager - Limits and compliance
    5. ClusteringRiskDetector - Hidden concentration
    
    Pipeline:
    Signals (HMM, ARES, etc) → Views → Optimizer → Vol Target → 
    Exposure Limits → Cluster Check → Final Weights → Orders
    
    This is what you present to a $50M+ fund.
    """
    
    VERSION = "6.4.0"
    CODENAME = "INSTITUTIONAL+"
    
    def __init__(
        self,
        target_volatility: float = 0.10,
        target_beta: Optional[float] = 0.5,
        risk_aversion: float = 3.0,
        max_weight_per_asset: float = 0.15,
        max_weight_per_sector: float = 0.35,
        correlation_threshold: float = 0.75,
        benchmark_symbol: str = "SPY"
    ):
        self.risk_model = RiskModelEngine(
            benchmark_symbol=benchmark_symbol,
            lookback_days=90
        )
        
        self.optimizer = PortfolioOptimizer(
            risk_aversion=risk_aversion,
            risk_free_rate=0.045
        )
        
        self.vol_engine = VolatilityTargetingEngine(
            target_volatility_annual=target_volatility,
            max_leverage=1.5,
            min_leverage=0.2
        )
        
        self.exposure_manager = ExposureManager(
            max_weight_per_asset=max_weight_per_asset,
            max_weight_per_sector=max_weight_per_sector,
            target_beta=target_beta
        )
        
        self.cluster_detector = ClusteringRiskDetector(
            corr_threshold=correlation_threshold,
            cluster_weight_limit=0.35
        )
        
        self._last_snapshot: Optional[PortfolioSnapshot] = None
        self._last_risk_metrics: Optional[RiskMetrics] = None
        
        logger.info(
            f"OmnixPortfolioEngine V{self.VERSION} {self.CODENAME} initialized | "
            f"Target Vol: {target_volatility:.0%} | Target Beta: {target_beta}"
        )
    
    def build_portfolio(
        self,
        prices: Dict[str, List[float]],
        signals: Dict[str, Dict],
        risk_profile: Optional[RiskProfile] = None,
        view_confidence: float = 0.5,
        sector_map: Optional[Dict[str, str]] = None
    ) -> PortfolioSnapshot:
        """
        MAIN ENTRY POINT - Build optimal institutional portfolio
        
        Args:
            prices: Dict mapping symbol to price history (oldest first)
            signals: Dict of signals from OMNIX modules (HMM, ARES, etc.)
                Each signal: {'direction': 'LONG/SHORT/NEUTRAL', 
                              'confidence': 0.0-1.0,
                              'source': 'HMM/ARES/etc'}
            risk_profile: Optional profile override
            view_confidence: How much to trust module signals vs market
            sector_map: Optional custom sector mapping
        
        Returns:
            PortfolioSnapshot with optimal weights and all metrics
        """
        logger.info(f"Building institutional portfolio | {len(prices)} assets | {len(signals)} signals")
        
        risk_metrics = self.risk_model.compute_all_metrics(prices)
        self._last_risk_metrics = risk_metrics
        
        symbols = risk_metrics.symbols
        cov_matrix = risk_metrics.covariance_matrix
        corr_matrix = risk_metrics.correlation_matrix
        betas = risk_metrics.betas
        
        opt_result = self.optimizer.optimize_with_views(
            cov_matrix=cov_matrix,
            symbols=symbols,
            signals=signals,
            view_confidence=view_confidence,
            max_weight=self.exposure_manager.max_weight_per_asset
        )
        
        vol_result = self.vol_engine.apply_volatility_targeting(
            weights=opt_result.weights,
            cov_matrix=cov_matrix,
            symbols=symbols,
            risk_profile=risk_profile
        )
        
        final_weights, exposure_report = self.exposure_manager.apply_all_limits(
            weights=vol_result.scaled_weights,
            symbols=symbols,
            betas=betas,
            sector_map=sector_map
        )
        
        cluster_report = self.cluster_detector.analyze_portfolio(
            corr_matrix=corr_matrix,
            symbols=symbols,
            weights=final_weights
        )
        
        final_weights_array = np.array([final_weights.get(s, 0) for s in symbols])
        final_vol = self.vol_engine.compute_portfolio_volatility(final_weights_array, cov_matrix)
        final_return = float(final_weights_array @ np.array([
            signals.get(s, {}).get('expected_return', 0.08) for s in symbols
        ]))
        final_sharpe = (final_return - 0.045) / final_vol if final_vol > 0 else 0
        
        snapshot = PortfolioSnapshot(
            weights=final_weights,
            expected_return=round(final_return, 4),
            expected_volatility=round(final_vol, 4),
            sharpe_ratio=round(final_sharpe, 4),
            portfolio_beta=exposure_report.portfolio_beta,
            effective_n_assets=cluster_report.effective_n_assets,
            diversification_score=cluster_report.diversification_score,
            net_exposure=exposure_report.net_exposure,
            gross_exposure=exposure_report.gross_exposure,
            sector_exposures=exposure_report.sector_exposures,
            cluster_warnings=cluster_report.warnings,
            risk_profile=vol_result.risk_profile.value if vol_result.risk_profile else "unknown",
            timestamp=datetime.now(),
            version=self.VERSION
        )
        
        self._last_snapshot = snapshot
        
        logger.info(
            f"Portfolio built | Sharpe: {final_sharpe:.2f} | Vol: {final_vol:.1%} | "
            f"Beta: {exposure_report.portfolio_beta:.2f} | Positions: {len([w for w in final_weights.values() if w > 0.01])}"
        )
        
        return snapshot
    
    def generate_rebalance_orders(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float],
        min_change_threshold: float = 0.01
    ) -> List[RebalanceOrder]:
        """
        Generate rebalance orders from current to target weights
        
        Args:
            current_weights: Current portfolio weights
            target_weights: Target portfolio weights
            min_change_threshold: Minimum weight change to trigger order
        
        Returns:
            List of RebalanceOrder sorted by priority
        """
        orders = []
        
        all_symbols = set(current_weights.keys()) | set(target_weights.keys())
        
        for symbol in all_symbols:
            current = current_weights.get(symbol, 0.0)
            target = target_weights.get(symbol, 0.0)
            change = target - current
            
            if abs(change) < min_change_threshold:
                continue
            
            if change > 0:
                side = "BUY"
                reason = "Increase position"
                priority = 2
            else:
                side = "SELL"
                reason = "Reduce position"
                priority = 1
            
            if target == 0:
                reason = "Exit position completely"
                priority = 0
            elif current == 0:
                reason = "New position entry"
                priority = 3
            
            orders.append(RebalanceOrder(
                symbol=symbol,
                side=side,
                weight_change=round(abs(change), 4),
                current_weight=round(current, 4),
                target_weight=round(target, 4),
                priority=priority,
                reason=reason
            ))
        
        orders.sort(key=lambda x: (x.priority, -x.weight_change))
        
        return orders
    
    def get_portfolio_status(self) -> Dict[str, Any]:
        """
        Get comprehensive portfolio status for Telegram/Dashboard
        
        Returns detailed status suitable for /portfolio_status command
        """
        if not self._last_snapshot:
            return {
                "status": "NO_PORTFOLIO",
                "message": "No portfolio has been constructed yet",
                "version": self.VERSION
            }
        
        snap = self._last_snapshot
        
        top_positions = sorted(
            [(s, w) for s, w in snap.weights.items() if w > 0.01],
            key=lambda x: -x[1]
        )[:5]
        
        status = {
            "status": "ACTIVE",
            "version": self.VERSION,
            "codename": self.CODENAME,
            "timestamp": snap.timestamp.isoformat(),
            "performance": {
                "expected_return": f"{snap.expected_return:.1%}",
                "expected_volatility": f"{snap.expected_volatility:.1%}",
                "sharpe_ratio": round(snap.sharpe_ratio, 2),
                "risk_profile": snap.risk_profile
            },
            "exposure": {
                "portfolio_beta": round(snap.portfolio_beta, 2),
                "net_exposure": f"{snap.net_exposure:.1%}",
                "gross_exposure": f"{snap.gross_exposure:.1%}",
                "sector_breakdown": {k: f"{v:.1%}" for k, v in snap.sector_exposures.items()}
            },
            "diversification": {
                "effective_n_assets": round(snap.effective_n_assets, 1),
                "diversification_score": f"{snap.diversification_score:.0%}",
                "total_positions": len([w for w in snap.weights.values() if w > 0.01])
            },
            "top_positions": [
                {"symbol": s, "weight": f"{w:.1%}"} for s, w in top_positions
            ],
            "warnings": snap.cluster_warnings,
            "modules_active": {
                "risk_model": True,
                "optimizer": True,
                "vol_targeting": True,
                "exposure_manager": True,
                "cluster_detector": True
            }
        }
        
        return status
    
    def get_risk_report(self) -> Dict[str, Any]:
        """Get detailed risk report for /risk_dashboard command"""
        if not self._last_risk_metrics:
            return {"status": "NO_DATA", "message": "No risk metrics computed yet"}
        
        metrics = self._last_risk_metrics
        snap = self._last_snapshot
        
        vol_regime = self.vol_engine.get_volatility_regime()
        
        report = {
            "version": self.VERSION,
            "timestamp": datetime.now().isoformat(),
            "data_quality": f"{metrics.data_quality_score:.0%}",
            "benchmark": self.risk_model.benchmark_symbol,
            "volatility_regime": {
                "status": vol_regime.get("regime", "unknown"),
                "trend": vol_regime.get("trend", "unknown"),
                "current_vs_historical": vol_regime.get("ratio", 1.0)
            },
            "betas": {k: round(v, 2) for k, v in list(metrics.betas.items())[:10]},
            "volatilities": {k: f"{v:.1%}" for k, v in list(metrics.volatilities.items())[:10]},
            "cluster_risks": {
                "warnings_count": len(snap.cluster_warnings) if snap else 0,
                "diversification": f"{snap.diversification_score:.0%}" if snap else "N/A"
            },
            "exposure_limits": self.exposure_manager.get_status()["limits"]
        }
        
        return report
    
    def format_telegram_status(self) -> str:
        """Format portfolio status for Telegram message"""
        status = self.get_portfolio_status()
        
        if status["status"] == "NO_PORTFOLIO":
            return "**OMNIX V6.4 INSTITUTIONAL+**\nNo portfolio constructed yet."
        
        msg = f"""**OMNIX V6.4 INSTITUTIONAL+**
Portfolio Status

**Performance**
Expected Return: {status['performance']['expected_return']}
Volatility: {status['performance']['expected_volatility']}
Sharpe Ratio: {status['performance']['sharpe_ratio']}
Risk Profile: {status['performance']['risk_profile'].upper()}

**Exposure**
Portfolio Beta: {status['exposure']['portfolio_beta']}
Net Exposure: {status['exposure']['net_exposure']}
Gross Exposure: {status['exposure']['gross_exposure']}

**Diversification**
Effective Assets: {status['diversification']['effective_n_assets']}
Diversification: {status['diversification']['diversification_score']}
Total Positions: {status['diversification']['total_positions']}

**Top 5 Positions**
"""
        for pos in status['top_positions']:
            msg += f"  {pos['symbol']}: {pos['weight']}\n"
        
        if status['warnings']:
            msg += f"\n**Warnings** ({len(status['warnings'])})\n"
            for warn in status['warnings'][:3]:
                msg += f"  {warn}\n"
        
        return msg
    
    def get_all_module_status(self) -> Dict[str, Any]:
        """Get status of all institutional modules"""
        return {
            "portfolio_engine": {
                "version": self.VERSION,
                "codename": self.CODENAME,
                "last_build": self._last_snapshot.timestamp.isoformat() if self._last_snapshot else None
            },
            "risk_model": self.risk_model.get_status(),
            "optimizer": self.optimizer.get_status(),
            "volatility_targeting": self.vol_engine.get_status(),
            "exposure_manager": self.exposure_manager.get_status(),
            "cluster_detector": self.cluster_detector.get_status()
        }
