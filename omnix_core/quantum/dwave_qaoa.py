#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNIX V6.0 ULTRA - D-Wave Leap Portfolio Optimization
======================================================
QUANTUM REAL - Utiliza computación cuántica REAL de D-Wave.

Este módulo conecta con D-Wave Leap (computadora cuántica real) para
optimización de portafolio usando Quantum Annealing y el solver híbrido CQM.

Requisitos:
- Cuenta en D-Wave Leap (https://cloud.dwavesys.com/leap)
- API Token de D-Wave configurado en DWAVE_API_TOKEN

Creado: Nov 27, 2025
Autor: OMNIX Team
"""

import logging
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

try:
    from dwave.system import LeapHybridCQMSampler, DWaveSampler, EmbeddingComposite
    from dwave.cloud import Client
    import dimod
    DWAVE_AVAILABLE = True
except ImportError:
    DWAVE_AVAILABLE = False
    logger.warning("D-Wave Ocean SDK not installed - quantum features limited")


@dataclass
class QuantumOptimizationResult:
    """Result from D-Wave quantum optimization"""
    optimal_weights: Dict[str, float]
    expected_return: float
    expected_risk: float
    sharpe_ratio: float
    solver_used: str
    qpu_access_time_ms: float
    is_quantum_real: bool
    timestamp: datetime


class DWavePortfolioOptimizer:
    """
    D-Wave Leap Portfolio Optimizer
    
    Utiliza computación cuántica REAL para optimizar portafolios.
    Soporta dos modos:
    - Hybrid CQM Solver (recomendado): Maneja restricciones complejas
    - QPU Directo: Acceso directo al procesador cuántico
    """
    
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.getenv('DWAVE_API_TOKEN')
        self._client = None
        self._sampler = None
        self._is_connected = False
        
        if not DWAVE_AVAILABLE:
            logger.error("D-Wave SDK not available - install with: pip install dwave-ocean-sdk")
            return
        
        if self.api_token:
            self._initialize_connection()
        else:
            logger.warning("DWAVE_API_TOKEN not configured - quantum optimization disabled")
            logger.info("Get your free API token at: https://cloud.dwavesys.com/leap")
    
    def _initialize_connection(self) -> bool:
        """Initialize connection to D-Wave Leap"""
        try:
            os.environ['DWAVE_API_TOKEN'] = self.api_token
            self._client = Client.from_config()
            
            solvers = self._client.get_solvers()
            solver_names = [s.name for s in solvers]
            
            logger.info("=" * 60)
            logger.info("⚛️ D-WAVE LEAP CONNECTION ESTABLISHED")
            logger.info(f"   🔗 Available solvers: {len(solver_names)}")
            for name in solver_names[:3]:
                logger.info(f"      • {name}")
            logger.info("   ✅ QUANTUM COMPUTING IS REAL")
            logger.info("=" * 60)
            
            self._is_connected = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to D-Wave: {e}")
            self._is_connected = False
            return False
    
    def is_available(self) -> bool:
        """Check if D-Wave quantum computing is available"""
        return DWAVE_AVAILABLE and self._is_connected
    
    def optimize_portfolio(
        self,
        assets: List[str],
        expected_returns: List[float],
        covariance_matrix: List[List[float]],
        budget: float = 1.0,
        risk_aversion: float = 0.5,
        min_weight: float = 0.0,
        max_weight: float = 1.0
    ) -> Optional[QuantumOptimizationResult]:
        """
        Optimize portfolio using D-Wave quantum annealing.
        
        Args:
            assets: List of asset symbols
            expected_returns: Expected returns for each asset
            covariance_matrix: Covariance matrix between assets
            budget: Total budget (normalized to 1.0)
            risk_aversion: Risk aversion parameter (0-1)
            min_weight: Minimum weight per asset
            max_weight: Maximum weight per asset
        
        Returns:
            QuantumOptimizationResult with optimal weights
        """
        if not self.is_available():
            logger.warning("D-Wave not available - using classical fallback")
            return self._classical_fallback(
                assets, expected_returns, covariance_matrix, 
                budget, risk_aversion
            )
        
        try:
            start_time = datetime.utcnow()
            n_assets = len(assets)
            
            cqm = dimod.ConstrainedQuadraticModel()
            
            weights = {
                asset: dimod.Real(
                    f'w_{asset}', 
                    lower_bound=min_weight, 
                    upper_bound=max_weight
                ) for asset in assets
            }
            
            risk_term = 0
            for i, asset_i in enumerate(assets):
                for j, asset_j in enumerate(assets):
                    risk_term += weights[asset_i] * weights[asset_j] * covariance_matrix[i][j]
            
            return_term = sum(
                weights[assets[i]] * expected_returns[i] 
                for i in range(n_assets)
            )
            
            objective = risk_aversion * risk_term - (1 - risk_aversion) * return_term
            cqm.set_objective(objective)
            
            cqm.add_constraint(
                sum(weights[asset] for asset in assets) == budget,
                label='budget_constraint'
            )
            
            logger.info("⚛️ Submitting to D-Wave Leap Hybrid Solver...")
            sampler = LeapHybridCQMSampler()
            sampleset = sampler.sample_cqm(cqm, label='OMNIX_Portfolio_Optimization')
            
            best_sample = sampleset.first.sample
            qpu_time = sampleset.info.get('timing', {}).get('qpu_access_time', 0) / 1000
            
            optimal_weights = {
                asset: float(best_sample[f'w_{asset}']) 
                for asset in assets
            }
            
            exp_return = sum(
                optimal_weights[assets[i]] * expected_returns[i] 
                for i in range(n_assets)
            )
            
            exp_risk = 0
            for i, asset_i in enumerate(assets):
                for j, asset_j in enumerate(assets):
                    exp_risk += optimal_weights[asset_i] * optimal_weights[asset_j] * covariance_matrix[i][j]
            exp_risk = np.sqrt(exp_risk)
            
            sharpe = exp_return / exp_risk if exp_risk > 0 else 0
            
            result = QuantumOptimizationResult(
                optimal_weights=optimal_weights,
                expected_return=exp_return,
                expected_risk=exp_risk,
                sharpe_ratio=sharpe,
                solver_used=sampler.solver.name,
                qpu_access_time_ms=qpu_time,
                is_quantum_real=True,
                timestamp=datetime.utcnow()
            )
            
            logger.info("=" * 60)
            logger.info("⚛️ D-WAVE QUANTUM OPTIMIZATION COMPLETE")
            logger.info(f"   📊 Assets: {n_assets}")
            logger.info(f"   💰 Expected Return: {exp_return:.4%}")
            logger.info(f"   📉 Expected Risk: {exp_risk:.4%}")
            logger.info(f"   📈 Sharpe Ratio: {sharpe:.3f}")
            logger.info(f"   ⏱️ QPU Time: {qpu_time:.2f}ms")
            logger.info(f"   🔧 Solver: {sampler.solver.name}")
            logger.info("   ✅ THIS IS REAL QUANTUM COMPUTING")
            logger.info("=" * 60)
            
            return result
            
        except Exception as e:
            logger.error(f"D-Wave optimization failed: {e}")
            return self._classical_fallback(
                assets, expected_returns, covariance_matrix, 
                budget, risk_aversion
            )
    
    def _classical_fallback(
        self,
        assets: List[str],
        expected_returns: List[float],
        covariance_matrix: List[List[float]],
        budget: float,
        risk_aversion: float
    ) -> QuantumOptimizationResult:
        """Classical fallback when quantum not available"""
        logger.info("Using classical optimization (quantum not available)")
        
        n_assets = len(assets)
        equal_weight = budget / n_assets
        
        optimal_weights = {asset: equal_weight for asset in assets}
        
        exp_return = sum(equal_weight * r for r in expected_returns)
        
        exp_risk = 0
        for i in range(n_assets):
            for j in range(n_assets):
                exp_risk += equal_weight * equal_weight * covariance_matrix[i][j]
        exp_risk = np.sqrt(exp_risk)
        
        sharpe = exp_return / exp_risk if exp_risk > 0 else 0
        
        return QuantumOptimizationResult(
            optimal_weights=optimal_weights,
            expected_return=exp_return,
            expected_risk=exp_risk,
            sharpe_ratio=sharpe,
            solver_used="classical_equal_weight",
            qpu_access_time_ms=0,
            is_quantum_real=False,
            timestamp=datetime.utcnow()
        )
    
    def get_solver_info(self) -> Dict[str, Any]:
        """Get information about available D-Wave solvers"""
        if not self.is_available():
            return {
                'available': False,
                'reason': 'D-Wave not configured or SDK not installed'
            }
        
        try:
            solvers = self._client.get_solvers()
            return {
                'available': True,
                'num_solvers': len(solvers),
                'solvers': [
                    {
                        'name': s.name,
                        'category': getattr(s, 'category', 'unknown'),
                        'qubits': getattr(s.properties, 'num_qubits', 'N/A')
                    }
                    for s in solvers
                ]
            }
        except Exception as e:
            return {
                'available': False,
                'reason': str(e)
            }
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test connection to D-Wave Leap"""
        if not DWAVE_AVAILABLE:
            return False, "D-Wave SDK not installed"
        
        if not self.api_token:
            return False, "DWAVE_API_TOKEN not configured"
        
        try:
            client = Client.from_config(token=self.api_token)
            solvers = list(client.get_solvers())
            return True, f"Connected! {len(solvers)} solvers available"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"


def demo_portfolio_optimization():
    """Demo function to test D-Wave portfolio optimization"""
    print("=" * 60)
    print("D-WAVE PORTFOLIO OPTIMIZATION DEMO")
    print("=" * 60)
    
    assets = ['BTC', 'ETH', 'SOL', 'AVAX']
    expected_returns = [0.15, 0.12, 0.20, 0.18]  
    covariance_matrix = [
        [0.04, 0.02, 0.01, 0.015],
        [0.02, 0.03, 0.01, 0.01],
        [0.01, 0.01, 0.05, 0.02],
        [0.015, 0.01, 0.02, 0.04]
    ]
    
    optimizer = DWavePortfolioOptimizer()
    
    if optimizer.is_available():
        print("⚛️ D-Wave Quantum Computing AVAILABLE!")
        print("   Submitting to real quantum hardware...")
    else:
        print("📊 D-Wave not configured - using classical simulation")
    
    result = optimizer.optimize_portfolio(
        assets=assets,
        expected_returns=expected_returns,
        covariance_matrix=covariance_matrix,
        budget=1.0,
        risk_aversion=0.5
    )
    
    if result:
        print(f"\nOptimal Portfolio Weights:")
        for asset, weight in result.optimal_weights.items():
            print(f"  {asset}: {weight:.2%}")
        print(f"\nExpected Return: {result.expected_return:.2%}")
        print(f"Expected Risk: {result.expected_risk:.2%}")
        print(f"Sharpe Ratio: {result.sharpe_ratio:.3f}")
        print(f"Quantum Real: {result.is_quantum_real}")
        print(f"Solver: {result.solver_used}")


if __name__ == "__main__":
    demo_portfolio_optimization()
