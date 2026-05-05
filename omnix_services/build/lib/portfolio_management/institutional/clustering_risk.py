"""
OMNIX V6.4 INSTITUTIONAL+ Clustering Risk Detector
Detects hidden concentration risk from correlated assets
Prevents the illusion of diversification
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class ClusterInfo:
    """Information about a detected cluster"""
    cluster_id: int
    symbols: List[str]
    total_weight: float
    avg_correlation: float
    max_correlation: float
    risk_level: str
    recommendation: str


@dataclass
class ClusterRiskReport:
    """Complete clustering risk analysis"""
    clusters: List[ClusterInfo]
    total_clusters_detected: int
    high_risk_clusters: int
    concentration_score: float
    diversification_score: float
    effective_n_assets: float
    warnings: List[str]
    timestamp: datetime


class ClusteringRiskDetector:
    """
    INSTITUTIONAL+ Clustering Risk Detector V6.4
    
    Purpose: Detect when you think you're diversified but you're NOT.
    
    Example problem:
    You hold NVDA (15%), AMD (10%), SOXX (8%), SMH (7%) = 40% total
    Correlation between these: 85%+
    
    Effective exposure = ~35% to a single factor (semiconductors)
    This is HIDDEN concentration risk.
    
    This module detects these clusters and warns before disaster strikes.
    
    Key Metrics:
    - Cluster detection via correlation threshold
    - Effective N (how many truly independent positions)
    - Concentration score (higher = more risk)
    - Actionable recommendations
    """
    
    VERSION = "6.4.0"
    
    RISK_LEVELS = {
        "critical": {"threshold": 0.90, "max_weight": 0.20},
        "high": {"threshold": 0.80, "max_weight": 0.30},
        "moderate": {"threshold": 0.70, "max_weight": 0.40},
        "acceptable": {"threshold": 0.60, "max_weight": 0.50}
    }
    
    def __init__(
        self,
        corr_threshold: float = 0.75,
        cluster_weight_limit: float = 0.35,
        min_cluster_size: int = 2
    ):
        self.corr_threshold = corr_threshold
        self.cluster_weight_limit = cluster_weight_limit
        self.min_cluster_size = min_cluster_size
        
        logger.info(
            f"ClusteringRiskDetector V{self.VERSION} | "
            f"Correlation threshold: {corr_threshold:.0%}"
        )
    
    def detect_clusters(
        self,
        corr_matrix: np.ndarray,
        symbols: List[str]
    ) -> List[Set[int]]:
        """
        Detect clusters of highly correlated assets
        
        Uses single-linkage clustering based on correlation threshold.
        
        Args:
            corr_matrix: Correlation matrix (N,N)
            symbols: List of symbols
        
        Returns:
            List of sets, each containing indices of clustered assets
        """
        n = len(symbols)
        clusters = []
        visited = set()
        
        for i in range(n):
            if i in visited:
                continue
            
            cluster = {i}
            queue = [i]
            
            while queue:
                current = queue.pop(0)
                for j in range(n):
                    if j not in visited and j not in cluster:
                        if abs(corr_matrix[current, j]) >= self.corr_threshold:
                            cluster.add(j)
                            queue.append(j)
            
            if len(cluster) >= self.min_cluster_size:
                clusters.append(cluster)
                visited.update(cluster)
        
        return clusters
    
    def analyze_cluster(
        self,
        cluster_indices: Set[int],
        corr_matrix: np.ndarray,
        symbols: List[str],
        weights: np.ndarray,
        cluster_id: int
    ) -> ClusterInfo:
        """
        Analyze a single cluster for risk metrics
        
        Args:
            cluster_indices: Set of indices in this cluster
            corr_matrix: Full correlation matrix
            symbols: All symbols
            weights: Portfolio weights
            cluster_id: Identifier for this cluster
        
        Returns:
            ClusterInfo with analysis
        """
        indices = list(cluster_indices)
        cluster_symbols = [symbols[i] for i in indices]
        
        cluster_weights = np.array([weights[i] for i in indices])
        total_weight = float(np.sum(np.abs(cluster_weights)))
        
        n_cluster = len(indices)
        correlations = []
        for i in range(n_cluster):
            for j in range(i + 1, n_cluster):
                correlations.append(abs(corr_matrix[indices[i], indices[j]]))
        
        avg_corr = float(np.mean(correlations)) if correlations else 0.0
        max_corr = float(np.max(correlations)) if correlations else 0.0
        
        if max_corr >= 0.90:
            risk_level = "CRITICAL"
            max_allowed = self.RISK_LEVELS["critical"]["max_weight"]
        elif max_corr >= 0.80:
            risk_level = "HIGH"
            max_allowed = self.RISK_LEVELS["high"]["max_weight"]
        elif max_corr >= 0.70:
            risk_level = "MODERATE"
            max_allowed = self.RISK_LEVELS["moderate"]["max_weight"]
        else:
            risk_level = "ACCEPTABLE"
            max_allowed = self.RISK_LEVELS["acceptable"]["max_weight"]
        
        if total_weight > max_allowed:
            excess = total_weight - max_allowed
            recommendation = f"REDUCE cluster exposure by {excess:.1%}"
        elif total_weight > self.cluster_weight_limit:
            recommendation = "MONITOR - approaching concentration limit"
        else:
            recommendation = "Within acceptable limits"
        
        return ClusterInfo(
            cluster_id=cluster_id,
            symbols=cluster_symbols,
            total_weight=round(total_weight, 4),
            avg_correlation=round(avg_corr, 4),
            max_correlation=round(max_corr, 4),
            risk_level=risk_level,
            recommendation=recommendation
        )
    
    def compute_effective_n(
        self,
        weights: np.ndarray,
        corr_matrix: np.ndarray
    ) -> float:
        """
        Compute effective number of independent assets
        
        A portfolio with 10 assets at 10% each but 90% correlated
        has effective N ≈ 1.5 (barely diversified)
        
        Uses the formula: N_eff = 1 / sum(w_i^2 * (1 + (N-1)*rho))
        
        Args:
            weights: Portfolio weights
            corr_matrix: Correlation matrix
        
        Returns:
            Effective number of independent positions
        """
        n = len(weights)
        if n <= 1:
            return float(n)
        
        avg_corr = (np.sum(corr_matrix) - n) / (n * (n - 1)) if n > 1 else 0
        avg_corr = np.clip(avg_corr, -1, 1)
        
        w_squared_sum = np.sum(weights ** 2)
        
        if w_squared_sum == 0:
            return 0.0
        
        hhi = w_squared_sum
        
        correlation_factor = 1 + (n - 1) * max(avg_corr, 0)
        effective_n = 1 / (hhi * correlation_factor) if (hhi * correlation_factor) > 0 else n
        
        return min(float(effective_n), float(n))
    
    def compute_concentration_score(
        self,
        weights: np.ndarray,
        corr_matrix: np.ndarray
    ) -> float:
        """
        Compute concentration score (0 = diversified, 1 = concentrated)
        
        Considers both weight concentration and correlation.
        
        Args:
            weights: Portfolio weights
            corr_matrix: Correlation matrix
        
        Returns:
            Concentration score between 0 and 1
        """
        n = len(weights)
        if n == 0:
            return 0.0
        
        hhi = np.sum(weights ** 2)
        
        avg_corr = (np.sum(corr_matrix) - n) / (n * (n - 1)) if n > 1 else 0
        avg_corr = np.clip(avg_corr, -1, 1)
        
        weight_concentration = hhi * n
        correlation_penalty = max(avg_corr, 0)
        
        score = 0.6 * weight_concentration + 0.4 * correlation_penalty
        
        return min(max(score, 0.0), 1.0)
    
    def analyze_portfolio(
        self,
        corr_matrix: np.ndarray,
        symbols: List[str],
        weights: Dict[str, float]
    ) -> ClusterRiskReport:
        """
        Complete portfolio clustering risk analysis
        
        This is the MAIN entry point for cluster risk detection.
        
        Args:
            corr_matrix: Correlation matrix
            symbols: List of symbols
            weights: Portfolio weights dict
        
        Returns:
            ClusterRiskReport with full analysis
        """
        weights_array = np.array([weights.get(s, 0.0) for s in symbols])
        
        if np.sum(np.abs(weights_array)) > 0:
            weights_array = weights_array / np.sum(np.abs(weights_array))
        
        cluster_indices_list = self.detect_clusters(corr_matrix, symbols)
        
        clusters = []
        high_risk_count = 0
        warnings = []
        
        for idx, cluster_indices in enumerate(cluster_indices_list):
            cluster_info = self.analyze_cluster(
                cluster_indices, corr_matrix, symbols, weights_array, idx + 1
            )
            clusters.append(cluster_info)
            
            if cluster_info.risk_level in ["CRITICAL", "HIGH"]:
                high_risk_count += 1
                warnings.append(
                    f"Cluster {idx + 1} ({', '.join(cluster_info.symbols[:3])}...): "
                    f"{cluster_info.risk_level} risk at {cluster_info.total_weight:.1%} weight"
                )
        
        effective_n = self.compute_effective_n(weights_array, corr_matrix)
        concentration = self.compute_concentration_score(weights_array, corr_matrix)
        diversification = 1 - concentration
        
        report = ClusterRiskReport(
            clusters=clusters,
            total_clusters_detected=len(clusters),
            high_risk_clusters=high_risk_count,
            concentration_score=round(concentration, 4),
            diversification_score=round(diversification, 4),
            effective_n_assets=round(effective_n, 2),
            warnings=warnings,
            timestamp=datetime.now()
        )
        
        logger.info(
            f"Cluster analysis | Detected: {len(clusters)} clusters | "
            f"High risk: {high_risk_count} | Effective N: {effective_n:.1f}"
        )
        
        return report
    
    def get_reduction_recommendations(
        self,
        report: ClusterRiskReport,
        target_cluster_weight: float = 0.25
    ) -> Dict[str, float]:
        """
        Generate weight reduction recommendations per symbol
        
        Args:
            report: ClusterRiskReport from analyze_portfolio
            target_cluster_weight: Target max weight per cluster
        
        Returns:
            Dict mapping symbol to recommended reduction (negative = reduce)
        """
        recommendations = {}
        
        for cluster in report.clusters:
            if cluster.total_weight > target_cluster_weight:
                excess_ratio = (cluster.total_weight - target_cluster_weight) / cluster.total_weight
                
                for symbol in cluster.symbols:
                    if symbol in recommendations:
                        recommendations[symbol] = min(recommendations[symbol], -excess_ratio)
                    else:
                        recommendations[symbol] = -excess_ratio
        
        return {k: round(v, 4) for k, v in recommendations.items()}
    
    def get_status(self) -> Dict:
        """Get detector status"""
        return {
            "engine": "ClusteringRiskDetector",
            "version": self.VERSION,
            "correlation_threshold": self.corr_threshold,
            "cluster_weight_limit": self.cluster_weight_limit,
            "min_cluster_size": self.min_cluster_size,
            "risk_levels": list(self.RISK_LEVELS.keys())
        }
