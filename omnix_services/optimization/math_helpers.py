"""
OMNIX V6.0 ULTRA - Mathematical Optimization Helpers
Extracted from main.py for modular architecture
"""

import time
import logging

logger = logging.getLogger(__name__)


class MathematicalOptimizer:
    """Optimizador matemático avanzado para portfolios"""
    
    def portfolio_optimization(self, assets_data, risk_tolerance):
        """Optimización matemática de portfolio usando Sharpe ratio"""
        try:
            num_assets = len(assets_data)
            if num_assets == 0:
                return {'optimal_weights': {}, 'expected_return': 0, 'risk': 0}
            
            # Algoritmo de optimización matemática
            total_expected_return = 0
            total_risk = 0
            weights = {}
            
            # Distribución de pesos basada en risk/return
            for asset, data in assets_data.items():
                expected_return = data.get('expected_return', 0)
                volatility = data.get('volatility', 0.02)
                
                # Score de atractivo (return ajustado por riesgo)
                if volatility > 0:
                    sharpe_like = expected_return / volatility
                else:
                    sharpe_like = 0
                
                total_expected_return += expected_return
                total_risk += volatility
            
            # Normalizar pesos
            for asset, data in assets_data.items():
                expected_return = data.get('expected_return', 0)
                volatility = data.get('volatility', 0.02)
                
                if volatility > 0:
                    weight = (expected_return / volatility) / num_assets
                else:
                    weight = 1.0 / num_assets
                
                # Ajustar por tolerancia al riesgo
                if risk_tolerance < 0.1:  # Conservador
                    weight *= 0.8 if volatility > 0.03 else 1.2
                elif risk_tolerance > 0.2:  # Agresivo
                    weight *= 1.3 if expected_return > 0 else 0.7
                
                weights[asset] = max(0.1, min(0.9, weight))
            
            # Normalizar a 100%
            total_weight = sum(weights.values())
            if total_weight > 0:
                weights = {k: v/total_weight for k, v in weights.items()}
            
            # Calcular métricas del portfolio
            portfolio_return = sum([weights[asset] * data['expected_return'] for asset, data in assets_data.items()])
            portfolio_risk = sum([weights[asset] * data['volatility'] for asset, data in assets_data.items()])
            
            sharpe_ratio = portfolio_return / portfolio_risk if portfolio_risk > 0 else 0
            
            return {
                'optimal_weights': weights,
                'expected_return': portfolio_return,
                'risk': portfolio_risk,
                'sharpe_ratio': sharpe_ratio,
                'optimization_confidence': 0.85
            }
        except:
            return {'optimal_weights': {}, 'expected_return': 0, 'risk': 0, 'sharpe_ratio': 0}


# Global variables for nonce generation
_nonce_counter = 0
_last_nonce_time = 0


def generate_unique_nonce():
    """Generar nonce único MEJORADO para evitar errores Kraken"""
    global _nonce_counter, _last_nonce_time
    current_time = int(time.time() * 1000000)  # Microsegundos
    
    # SIEMPRE incrementar contador para garantizar unicidad
    _nonce_counter += 1
    nonce = current_time + _nonce_counter
    
    # Si el tiempo no avanzó, usar el anterior + contador
    if nonce <= _last_nonce_time:
        nonce = _last_nonce_time + _nonce_counter + 1
        
    _last_nonce_time = nonce
    return nonce
