"""
Kelly Criterion Position Sizing Module
Optimiza el tamaño de posición matemáticamente basado en win rate y win/loss ratio
"""

import logging
from typing import Dict, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class KellyCriterionOptimizer:
    """
    Implementa Kelly Criterion para optimización de tamaño de posiciones
    
    Kelly % = (W * R - L) / R
    Donde:
    - W = Win rate (probabilidad de ganar)
    - L = Loss rate (probabilidad de perder) = 1 - W
    - R = Win/Loss ratio (promedio ganancia / promedio pérdida)
    """
    
    def __init__(self, fractional_kelly: float = 0.50):
        """
        Args:
            fractional_kelly: Fracción del Kelly Criterion a usar (0.50 = Half Kelly)
                             Half Kelly es estándar institucional - balance óptimo
                             entre crecimiento y volatilidad.
        """
        self.fractional_kelly = fractional_kelly
        logger.info(f"💎 Kelly Criterion Optimizer initialized - Fractional: {fractional_kelly}")
    
    def calculate_optimal_position(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        total_capital: float,
        min_position: float = 0.04,
        max_position: float = 0.20
    ) -> Dict:
        """
        Calcula el tamaño óptimo de posición usando Kelly Criterion
        
        Args:
            win_rate: Tasa de éxito (0-1)
            avg_win: Ganancia promedio por trade ganador
            avg_loss: Pérdida promedio por trade perdedor (positivo)
            total_capital: Capital total disponible
            min_position: Tamaño mínimo de posición (% del capital) - Default 4%
            max_position: Tamaño máximo de posición (% del capital) - Default 20%
        
        Returns:
            Dict con kelly_fraction, position_size, position_usd, confidence
            
        Nota: Con win_rate=0.65 y ratio 2:1, Kelly da ~47.5%.
              Con Half Kelly (0.50), eso es ~23.75%.
              Limitado a max_position=20% para control de riesgo institucional.
        """
        
        # Validaciones
        if not (0 < win_rate < 1):
            logger.warning(f"⚠️ Win rate inválido: {win_rate}, usando 0.5")
            win_rate = 0.5
        
        if avg_win <= 0 or avg_loss <= 0:
            logger.warning(f"⚠️ Avg win/loss inválidos: {avg_win}/{avg_loss}")
            return self._conservative_position(total_capital, min_position)
        
        # Calcular componentes Kelly
        loss_rate = 1 - win_rate
        win_loss_ratio = avg_win / avg_loss
        
        # Kelly Criterion Formula
        # K = (W * R - L) / R = (p * b - q) / b
        # Donde p=win_rate, q=loss_rate, b=win_loss_ratio
        kelly_fraction = (win_rate * win_loss_ratio - loss_rate) / win_loss_ratio
        
        # Aplicar fractional Kelly (más conservador)
        fractional_kelly_value = kelly_fraction * self.fractional_kelly
        
        # Limitar entre min y max
        kelly_clamped = np.clip(fractional_kelly_value, min_position, max_position)
        
        # Calcular tamaño en USD
        position_usd = total_capital * kelly_clamped
        
        # Calcular confianza (qué tan robusto es el Kelly)
        confidence = self._calculate_confidence(win_rate, win_loss_ratio)
        
        result = {
            'kelly_fraction': kelly_fraction,
            'fractional_kelly': fractional_kelly_value,
            'position_size': kelly_clamped,
            'position_usd': position_usd,
            'win_rate': win_rate,
            'win_loss_ratio': win_loss_ratio,
            'confidence': confidence,
            'recommendation': self._get_recommendation(kelly_clamped, confidence)
        }
        
        logger.info(
            f"💎 Kelly Criterion: {kelly_clamped:.2%} of capital "
            f"(${position_usd:.2f}) - Confidence: {confidence}"
        )
        
        return result
    
    def calculate_from_history(
        self,
        trades_history: list,
        total_capital: float
    ) -> Dict:
        """
        Calcula Kelly óptimo desde histórico de trades
        
        Args:
            trades_history: Lista de trades con 'profit' y 'status' ('win'/'loss')
            total_capital: Capital total
        
        Returns:
            Dict con resultados Kelly Criterion
        """
        if not trades_history or len(trades_history) < 10:
            logger.warning("⚠️ Histórico insuficiente para Kelly, usando posición conservadora")
            return self._conservative_position(total_capital, 0.05)
        
        # Separar wins y losses
        wins = [t['profit'] for t in trades_history if t.get('status') == 'win' and t.get('profit', 0) > 0]
        losses = [abs(t['profit']) for t in trades_history if t.get('status') == 'loss' and t.get('profit', 0) < 0]
        
        if not wins or not losses:
            logger.warning("⚠️ Sin wins o losses suficientes")
            return self._conservative_position(total_capital, 0.05)
        
        # Calcular estadísticas
        total_trades = len(wins) + len(losses)
        win_rate = len(wins) / total_trades
        avg_win = float(np.mean(wins))
        avg_loss = float(np.mean(losses))
        
        return self.calculate_optimal_position(
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            total_capital=total_capital
        )
    
    def _calculate_confidence(self, win_rate: float, win_loss_ratio: float) -> str:
        """
        Evalúa confianza en el Kelly Criterion basado en métricas
        """
        # Kelly es más robusto cuando:
        # 1. Win rate está entre 40-60% (realista)
        # 2. Win/Loss ratio > 1.5 (ganancias significativamente mayores)
        
        confidence_score = 0
        
        # Win rate check
        if 0.40 <= win_rate <= 0.60:
            confidence_score += 2
        elif 0.30 <= win_rate <= 0.70:
            confidence_score += 1
        
        # Win/Loss ratio check
        if win_loss_ratio >= 2.0:
            confidence_score += 3
        elif win_loss_ratio >= 1.5:
            confidence_score += 2
        elif win_loss_ratio >= 1.0:
            confidence_score += 1
        
        # Mapear a categorías
        if confidence_score >= 4:
            return "HIGH"
        elif confidence_score >= 2:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _get_recommendation(self, position_size: float, confidence: str) -> str:
        """
        Genera recomendación basada en tamaño y confianza
        """
        if confidence == "LOW":
            return "CAUTIOUS - Consider reducing position or improving strategy"
        elif position_size >= 0.20:
            return "AGGRESSIVE - Large position, ensure risk management"
        elif position_size >= 0.10:
            return "MODERATE - Balanced position size"
        else:
            return "CONSERVATIVE - Small position, low risk"
    
    def _conservative_position(self, total_capital: float, fraction: float = 0.05) -> Dict:
        """
        Retorna posición conservadora cuando no hay datos suficientes.
        
        Nota: El default de 5% es adecuado para situaciones sin datos.
              Con datos reales, Kelly típicamente da 4-20%.
        """
        return {
            'kelly_fraction': fraction,
            'fractional_kelly': fraction,
            'position_size': fraction,
            'position_usd': total_capital * fraction,
            'win_rate': 0.5,
            'win_loss_ratio': 1.0,
            'confidence': 'LOW',
            'recommendation': 'CONSERVATIVE - Datos insuficientes para optimización Kelly. Usando 5% conservador.'
        }
    
    def adjust_for_var(
        self,
        kelly_position: Dict,
        var_95: float,
        total_capital: float,
        max_var_percent: float = 0.05
    ) -> Dict:
        """
        Ajusta posición Kelly basado en VaR (Value at Risk)
        
        Args:
            kelly_position: Resultado de calculate_optimal_position
            var_95: VaR al 95% confianza (pérdida máxima esperada)
            total_capital: Capital total
            max_var_percent: Máximo % de capital que puede estar en riesgo
        
        Returns:
            Posición ajustada por VaR
        """
        max_var_usd = total_capital * max_var_percent
        
        # Si el VaR excede límite, reducir posición
        if abs(var_95) > max_var_usd:
            reduction_factor = max_var_usd / abs(var_95)
            adjusted_position = kelly_position['position_size'] * reduction_factor
            
            logger.warning(
                f"⚠️ VaR adjustment: ${abs(var_95):.2f} > ${max_var_usd:.2f} "
                f"- Reducing position from {kelly_position['position_size']:.2%} "
                f"to {adjusted_position:.2%}"
            )
            
            kelly_position['position_size'] = adjusted_position
            kelly_position['position_usd'] = total_capital * adjusted_position
            kelly_position['var_adjusted'] = True
            kelly_position['var_95'] = var_95
        else:
            kelly_position['var_adjusted'] = False
            kelly_position['var_95'] = var_95
        
        return kelly_position


# Ejemplo de uso
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    kelly = KellyCriterionOptimizer(fractional_kelly=0.25)
    
    # Ejemplo: Strategy con 60% win rate, avg win $100, avg loss $50
    result = kelly.calculate_optimal_position(
        win_rate=0.60,
        avg_win=100,
        avg_loss=50,
        total_capital=10000
    )
    
    print(f"\n💎 KELLY CRITERION RESULTS:")
    print(f"Kelly Fraction: {result['kelly_fraction']:.2%}")
    print(f"Fractional Kelly: {result['fractional_kelly']:.2%}")
    print(f"Position Size: {result['position_size']:.2%}")
    print(f"Position USD: ${result['position_usd']:.2f}")
    print(f"Confidence: {result['confidence']}")
    print(f"Recommendation: {result['recommendation']}")
