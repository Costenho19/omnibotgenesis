"""
🔗 STOCK COHERENCE ADAPTER V6.2
Adaptador para integrar señales de acciones con Coherence Engine
Sistema de veto de 6 niveles adaptado para mercado tradicional
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class VetoLevel(Enum):
    NONE = 0
    ADVISORY = 1
    CAUTION = 2
    WARNING = 3
    BLOCK = 4
    CRITICAL = 5


@dataclass
class CoherenceResult:
    approved: bool
    veto_level: VetoLevel
    agreement_score: float
    signal_coherence: float
    fundamental_alignment: float
    regime_alignment: float
    reasons: List[str]
    recommendations: List[str]


class StockCoherenceAdapter:
    """
    Adaptador de Coherencia para Acciones
    
    Integra con Coherence Engine V5.4 ULTRA para validar
    acuerdo entre múltiples señales de trading de acciones.
    
    Sistema de Veto 6-Tier:
    - NONE: Sin objeciones, ejecutar
    - ADVISORY: Sugerencia, puede ejecutar
    - CAUTION: Precaución, reducir tamaño
    - WARNING: Advertencia, solo si confianza alta
    - BLOCK: Bloquear operación
    - CRITICAL: Veto absoluto
    
    Diferencias vs Crypto:
    - Umbral de coherencia más alto (0.65 vs 0.55)
    - Peso fundamental mayor (25% vs 0%)
    - Considera horarios de mercado
    """
    
    COHERENCE_PARAMS = {
        'min_agreement': 0.65,
        'fundamental_weight': 0.25,
        'technical_weight': 0.50,
        'regime_weight': 0.25,
        'min_signals': 3,
        'veto_thresholds': {
            VetoLevel.ADVISORY: 0.55,
            VetoLevel.CAUTION: 0.45,
            VetoLevel.WARNING: 0.35,
            VetoLevel.BLOCK: 0.25,
            VetoLevel.CRITICAL: 0.15
        }
    }
    
    def __init__(self, coherence_engine=None):
        """
        Args:
            coherence_engine: Instancia de CoherenceEngine crypto (opcional)
        """
        self.coherence_engine = coherence_engine
        self.validation_history = []
        
        logger.info("🔗 Stock Coherence Adapter V6.2 inicializado")
        logger.info(f"   📊 Min Agreement: {self.COHERENCE_PARAMS['min_agreement']:.0%}")
        logger.info(f"   🏛️ Fundamental Weight: {self.COHERENCE_PARAMS['fundamental_weight']:.0%}")
    
    def validate(
        self,
        signals: Dict[str, float],
        fundamental_score: float = 0.5,
        regime: str = "unknown",
        market_open: bool = True
    ) -> CoherenceResult:
        """
        Validar coherencia de señales de acciones
        
        Args:
            signals: Dict de señales {'monte_carlo': 0.5, 'kalman': 0.3, ...}
            fundamental_score: Score fundamental (0-1)
            regime: Régimen de mercado actual
            market_open: Si el mercado está abierto
            
        Returns:
            CoherenceResult con decisión y razones
        """
        try:
            reasons = []
            recommendations = []
            
            if not market_open:
                reasons.append("Mercado cerrado - análisis en modo offline")
                recommendations.append("Esperar apertura para ejecutar")
            
            if len(signals) < self.COHERENCE_PARAMS['min_signals']:
                reasons.append(f"Solo {len(signals)} señales (mínimo: {self.COHERENCE_PARAMS['min_signals']})")
            
            agreement = self._calculate_agreement(signals)
            
            signal_coherence = self._calculate_signal_coherence(signals)
            
            fundamental_alignment = self._check_fundamental_alignment(
                signals, fundamental_score
            )
            
            regime_alignment = self._check_regime_alignment(signals, regime)
            
            total_coherence = (
                signal_coherence * self.COHERENCE_PARAMS['technical_weight'] +
                fundamental_alignment * self.COHERENCE_PARAMS['fundamental_weight'] +
                regime_alignment * self.COHERENCE_PARAMS['regime_weight']
            )
            
            veto_level = self._determine_veto_level(total_coherence, agreement)
            
            if agreement < 0.5:
                reasons.append(f"Bajo acuerdo entre señales ({agreement:.0%})")
            
            if fundamental_alignment < 0.4 and fundamental_score != 0.5:
                reasons.append("Fundamental no alinea con técnico")
                recommendations.append("Revisar métricas fundamentales")
            
            if regime in ['crisis', 'bear'] and np.mean(list(signals.values())) > 0.3:
                reasons.append(f"Señal bullish en régimen {regime}")
                recommendations.append("Considerar posición reducida o hedge")
            
            approved = veto_level.value <= VetoLevel.CAUTION.value
            
            result = CoherenceResult(
                approved=approved,
                veto_level=veto_level,
                agreement_score=agreement,
                signal_coherence=signal_coherence,
                fundamental_alignment=fundamental_alignment,
                regime_alignment=regime_alignment,
                reasons=reasons,
                recommendations=recommendations
            )
            
            self._log_validation(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error en validación de coherencia: {e}")
            return CoherenceResult(
                approved=False,
                veto_level=VetoLevel.CRITICAL,
                agreement_score=0,
                signal_coherence=0,
                fundamental_alignment=0,
                regime_alignment=0,
                reasons=[f"Error en validación: {str(e)}"],
                recommendations=["Revisar configuración del sistema"]
            )
    
    def _calculate_agreement(self, signals: Dict[str, float]) -> float:
        """Calcular acuerdo direccional entre señales"""
        if not signals:
            return 0
        
        values = list(signals.values())
        
        significant = [v for v in values if abs(v) > 0.1]
        
        if not significant:
            return 0.5
        
        positive = sum(1 for v in significant if v > 0)
        negative = len(significant) - positive
        
        agreement = max(positive, negative) / len(significant)
        
        return agreement
    
    def _calculate_signal_coherence(self, signals: Dict[str, float]) -> float:
        """Calcular coherencia entre magnitudes de señales"""
        if len(signals) < 2:
            return 0.5
        
        values = list(signals.values())
        
        std = np.std(values)
        mean_abs = np.mean([abs(v) for v in values])
        
        if mean_abs == 0:
            return 0.5
        
        cv = std / mean_abs
        coherence = 1 - min(cv, 1)
        
        return coherence
    
    def _check_fundamental_alignment(
        self, 
        signals: Dict[str, float],
        fundamental_score: float
    ) -> float:
        """Verificar alineación entre señales técnicas y fundamental"""
        if fundamental_score == 0.5:
            return 0.5
        
        avg_signal = np.mean(list(signals.values()))
        
        fund_direction = 1 if fundamental_score > 0.5 else -1
        tech_direction = 1 if avg_signal > 0 else -1
        
        if fund_direction == tech_direction:
            strength = abs(fundamental_score - 0.5) * 2
            alignment = 0.5 + strength * 0.5
        else:
            strength = abs(fundamental_score - 0.5) * 2
            alignment = 0.5 - strength * 0.3
        
        return np.clip(alignment, 0, 1)
    
    def _check_regime_alignment(
        self, 
        signals: Dict[str, float],
        regime: str
    ) -> float:
        """Verificar alineación con régimen de mercado"""
        avg_signal = np.mean(list(signals.values()))
        
        regime_expectations = {
            'bull': 0.3,
            'bear': -0.3,
            'sideways': 0,
            'crisis': -0.5,
            'unknown': 0
        }
        
        expected = regime_expectations.get(regime.lower(), 0)
        
        diff = abs(avg_signal - expected)
        alignment = 1 - min(diff, 1)
        
        return alignment
    
    def _determine_veto_level(self, coherence: float, agreement: float) -> VetoLevel:
        """Determinar nivel de veto basado en coherencia y acuerdo"""
        combined = (coherence + agreement) / 2
        
        thresholds = self.COHERENCE_PARAMS['veto_thresholds']
        
        if combined >= thresholds[VetoLevel.ADVISORY]:
            return VetoLevel.NONE
        elif combined >= thresholds[VetoLevel.CAUTION]:
            return VetoLevel.ADVISORY
        elif combined >= thresholds[VetoLevel.WARNING]:
            return VetoLevel.CAUTION
        elif combined >= thresholds[VetoLevel.BLOCK]:
            return VetoLevel.WARNING
        elif combined >= thresholds[VetoLevel.CRITICAL]:
            return VetoLevel.BLOCK
        else:
            return VetoLevel.CRITICAL
    
    def _log_validation(self, result: CoherenceResult):
        """Registrar validación en historial"""
        self.validation_history.append({
            'timestamp': datetime.now(),
            'approved': result.approved,
            'veto_level': result.veto_level.name,
            'agreement': result.agreement_score,
            'coherence': result.signal_coherence
        })
        
        if len(self.validation_history) > 100:
            self.validation_history = self.validation_history[-100:]
    
    def get_approval_rate(self) -> float:
        """Obtener tasa de aprobación histórica"""
        if not self.validation_history:
            return 0
        
        approved = sum(1 for v in self.validation_history if v['approved'])
        return approved / len(self.validation_history)
    
    def get_status(self) -> Dict:
        """Obtener estado del adaptador"""
        return {
            'validations': len(self.validation_history),
            'approval_rate': self.get_approval_rate(),
            'avg_coherence': np.mean([v['coherence'] for v in self.validation_history]) if self.validation_history else 0,
            'params': self.COHERENCE_PARAMS
        }
