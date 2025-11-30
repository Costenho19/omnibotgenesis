"""
OMNIX V6.4 INSTITUTIONAL+ Exposure Manager
Controls: Sector limits, Asset limits, Beta targeting, Net exposure
Critical for institutional compliance and risk mandates
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class ExposureType(Enum):
    """Types of exposure to manage"""
    ASSET = "asset"
    SECTOR = "sector"
    BETA = "beta"
    GEOGRAPHIC = "geographic"
    NET = "net"


@dataclass
class ExposureReport:
    """Comprehensive exposure analysis"""
    asset_exposures: Dict[str, float]
    sector_exposures: Dict[str, float]
    portfolio_beta: float
    net_exposure: float
    gross_exposure: float
    long_exposure: float
    short_exposure: float
    violations: List[str]
    timestamp: datetime
    compliant: bool


@dataclass
class SectorMapping:
    """Sector classification for assets"""
    TECH = ["AAPL", "MSFT", "GOOGL", "GOOG", "META", "NVDA", "AMD", "INTC", "CRM", "ORCL", "ADBE", "CSCO"]
    FINANCE = ["JPM", "BAC", "GS", "MS", "WFC", "C", "BLK", "SCHW", "AXP", "V", "MA"]
    HEALTHCARE = ["JNJ", "UNH", "PFE", "MRK", "ABBV", "TMO", "ABT", "LLY", "BMY", "AMGN"]
    ENERGY = ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "HAL"]
    CONSUMER = ["AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "TGT", "COST", "WMT", "PG"]
    INDUSTRIAL = ["CAT", "BA", "HON", "UPS", "GE", "MMM", "LMT", "RTX", "DE", "UNP"]
    CRYPTO = ["BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "AVAX", "DOT", "MATIC", "LINK"]
    
    @classmethod
    def get_sector(cls, symbol: str) -> str:
        """Get sector for a symbol"""
        symbol = symbol.upper().replace("USD", "").replace("/", "")
        
        for sector_name in ["TECH", "FINANCE", "HEALTHCARE", "ENERGY", "CONSUMER", "INDUSTRIAL", "CRYPTO"]:
            if symbol in getattr(cls, sector_name):
                return sector_name
        return "OTHER"


class ExposureManager:
    """
    INSTITUTIONAL+ Exposure Manager V6.4
    
    Controls all portfolio exposures to ensure compliance with:
    - Asset concentration limits (max 15-20% per position)
    - Sector exposure limits (max 30-35% per sector)
    - Beta targeting (market-neutral to directional)
    - Net/Gross exposure limits
    
    This is CRITICAL for institutional mandates where risk
    limits are contractually defined.
    """
    
    VERSION = "6.4.0"
    
    def __init__(
        self,
        max_weight_per_asset: float = 0.15,
        max_weight_per_sector: float = 0.35,
        target_beta: Optional[float] = None,
        max_gross_exposure: float = 1.0,
        max_net_exposure: float = 1.0,
        min_net_exposure: float = -0.3
    ):
        self.max_weight_per_asset = max_weight_per_asset
        self.max_weight_per_sector = max_weight_per_sector
        self.target_beta = target_beta
        self.max_gross_exposure = max_gross_exposure
        self.max_net_exposure = max_net_exposure
        self.min_net_exposure = min_net_exposure
        
        self.sector_mapping = SectorMapping()
        
        logger.info(
            f"ExposureManager V{self.VERSION} | "
            f"Asset max: {max_weight_per_asset:.0%} | "
            f"Sector max: {max_weight_per_sector:.0%} | "
            f"Target β: {target_beta}"
        )
    
    def apply_asset_limits(
        self,
        weights: np.ndarray,
        symbols: List[str]
    ) -> np.ndarray:
        """
        Apply per-asset weight limits
        
        Args:
            weights: Portfolio weights
            symbols: Asset symbols
        
        Returns:
            Adjusted weights respecting limits
        """
        w = np.array(weights, dtype=float)
        
        w = np.clip(w, -self.max_weight_per_asset, self.max_weight_per_asset)
        
        if np.sum(np.abs(w)) > 0:
            w = w / np.sum(np.abs(w))
        
        return w
    
    def apply_sector_limits(
        self,
        weights: np.ndarray,
        symbols: List[str],
        sector_map: Optional[Dict[str, str]] = None
    ) -> np.ndarray:
        """
        Apply sector exposure limits
        
        Args:
            weights: Portfolio weights
            symbols: Asset symbols
            sector_map: Optional custom sector mapping
        
        Returns:
            Adjusted weights respecting sector limits
        """
        w = np.array(weights, dtype=float)
        
        sector_weights = defaultdict(float)
        symbol_sectors = {}
        
        for i, sym in enumerate(symbols):
            if sector_map and sym in sector_map:
                sector = sector_map[sym]
            else:
                sector = SectorMapping.get_sector(sym)
            
            symbol_sectors[sym] = sector
            sector_weights[sector] += abs(w[i])
        
        for sector, total_weight in sector_weights.items():
            if total_weight > self.max_weight_per_sector:
                reduction_factor = self.max_weight_per_sector / total_weight
                
                for i, sym in enumerate(symbols):
                    if symbol_sectors.get(sym) == sector:
                        w[i] *= reduction_factor
        
        if np.sum(np.abs(w)) > 0:
            w = w / np.sum(np.abs(w))
        
        return w
    
    def adjust_beta(
        self,
        weights: np.ndarray,
        symbols: List[str],
        betas: Dict[str, float]
    ) -> np.ndarray:
        """
        Adjust portfolio to achieve target beta
        
        Args:
            weights: Portfolio weights
            symbols: Asset symbols
            betas: Beta values per symbol
        
        Returns:
            Adjusted weights targeting specified beta
        """
        if self.target_beta is None:
            return weights
        
        w = np.array(weights, dtype=float)
        
        portfolio_beta = sum(w[i] * betas.get(symbols[i], 1.0) 
                           for i in range(len(symbols)))
        
        if abs(portfolio_beta) < 0.01:
            return w
        
        beta_diff = self.target_beta - portfolio_beta
        
        if abs(beta_diff) < 0.1:
            return w
        
        scaling = self.target_beta / portfolio_beta if portfolio_beta != 0 else 1.0
        scaling = np.clip(scaling, 0.5, 2.0)
        
        w = w * scaling
        
        max_sum = max(self.max_gross_exposure, 1.0)
        if np.sum(np.abs(w)) > max_sum:
            w = w * (max_sum / np.sum(np.abs(w)))
        
        return w
    
    def apply_net_gross_limits(
        self,
        weights: np.ndarray
    ) -> np.ndarray:
        """
        Apply net and gross exposure limits
        
        Net exposure = Long - Short (directional bias)
        Gross exposure = Long + Short (total leverage)
        
        Args:
            weights: Portfolio weights
        
        Returns:
            Adjusted weights respecting exposure limits
        """
        w = np.array(weights, dtype=float)
        
        long_exposure = np.sum(w[w > 0])
        short_exposure = np.sum(np.abs(w[w < 0]))
        net_exposure = long_exposure - short_exposure
        gross_exposure = long_exposure + short_exposure
        
        if gross_exposure > self.max_gross_exposure:
            w = w * (self.max_gross_exposure / gross_exposure)
        
        net_exposure = np.sum(w[w > 0]) - np.sum(np.abs(w[w < 0]))
        
        if net_exposure > self.max_net_exposure:
            excess = net_exposure - self.max_net_exposure
            long_mask = w > 0
            if np.any(long_mask):
                w[long_mask] -= excess * (w[long_mask] / np.sum(w[long_mask]))
        
        elif net_exposure < self.min_net_exposure:
            shortfall = self.min_net_exposure - net_exposure
            short_mask = w < 0
            if np.any(short_mask):
                reduction = shortfall / np.sum(np.abs(w[short_mask]))
                w[short_mask] = w[short_mask] * (1 - min(reduction, 0.9))
        
        return w
    
    def apply_all_limits(
        self,
        weights: Dict[str, float],
        symbols: List[str],
        betas: Optional[Dict[str, float]] = None,
        sector_map: Optional[Dict[str, str]] = None
    ) -> Tuple[Dict[str, float], ExposureReport]:
        """
        Apply ALL exposure limits in one call
        
        This is the MAIN entry point for exposure management.
        Order matters: Asset → Sector → Beta → Net/Gross
        
        Args:
            weights: Initial portfolio weights
            symbols: Asset symbols
            betas: Beta values per symbol
            sector_map: Optional custom sector mapping
        
        Returns:
            Tuple of (adjusted weights dict, exposure report)
        """
        w = np.array([weights.get(s, 0.0) for s in symbols])
        violations = []
        
        w_asset = self.apply_asset_limits(w, symbols)
        if not np.allclose(w, w_asset):
            violations.append("Asset limits applied")
        w = w_asset
        
        w_sector = self.apply_sector_limits(w, symbols, sector_map)
        if not np.allclose(w, w_sector):
            violations.append("Sector limits applied")
        w = w_sector
        
        if betas and self.target_beta is not None:
            w_beta = self.adjust_beta(w, symbols, betas)
            if not np.allclose(w, w_beta):
                violations.append(f"Beta adjusted toward {self.target_beta}")
            w = w_beta
        
        w_exp = self.apply_net_gross_limits(w)
        if not np.allclose(w, w_exp):
            violations.append("Net/Gross limits applied")
        w = w_exp
        
        adjusted_weights = {symbols[i]: round(float(w[i]), 6) for i in range(len(symbols))}
        
        sector_exposures = defaultdict(float)
        for i, sym in enumerate(symbols):
            sector = sector_map.get(sym) if sector_map else SectorMapping.get_sector(sym)
            sector_exposures[sector] += abs(w[i])
        
        long_exp = float(np.sum(w[w > 0]))
        short_exp = float(np.sum(np.abs(w[w < 0])))
        net_exp = long_exp - short_exp
        gross_exp = long_exp + short_exp
        
        port_beta = 0.0
        if betas:
            port_beta = sum(w[i] * betas.get(symbols[i], 1.0) for i in range(len(symbols)))
        
        report = ExposureReport(
            asset_exposures=adjusted_weights,
            sector_exposures=dict(sector_exposures),
            portfolio_beta=round(port_beta, 4),
            net_exposure=round(net_exp, 4),
            gross_exposure=round(gross_exp, 4),
            long_exposure=round(long_exp, 4),
            short_exposure=round(short_exp, 4),
            violations=violations,
            timestamp=datetime.now(),
            compliant=len(violations) == 0
        )
        
        logger.info(
            f"Exposure check | Net: {net_exp:.1%} | Gross: {gross_exp:.1%} | "
            f"Beta: {port_beta:.2f} | Violations: {len(violations)}"
        )
        
        return adjusted_weights, report
    
    def get_status(self) -> Dict:
        """Get manager status"""
        return {
            "engine": "ExposureManager",
            "version": self.VERSION,
            "limits": {
                "max_asset": self.max_weight_per_asset,
                "max_sector": self.max_weight_per_sector,
                "target_beta": self.target_beta,
                "max_gross": self.max_gross_exposure,
                "max_net": self.max_net_exposure,
                "min_net": self.min_net_exposure
            }
        }
