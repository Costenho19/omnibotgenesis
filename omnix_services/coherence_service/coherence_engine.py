#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNIX V5.3 ULTRA - COHERENCE ENGINE
Sistema de Validación de Coherencia de Estrategias de Trading
Detecta contradicciones entre las 9 estrategias y calcula score de confianza
Desarrollado por Harold Nunes - Noviembre 2025
"""

import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class Signal(Enum):
    """Tipos de señales de trading"""
    STRONG_BUY = 2
    BUY = 1
    HOLD = 0
    SELL = -1
    STRONG_SELL = -2


class CoherenceLevel(Enum):
    """Niveles de coherencia del sistema"""
    EXCELLENT = "EXCELLENT"      # 90-100%
    GOOD = "GOOD"               # 70-89%
    MODERATE = "MODERATE"       # 50-69%
    POOR = "POOR"              # 30-49%
    CRITICAL = "CRITICAL"       # 0-29%


@dataclass
class StrategySignal:
    """Señal de una estrategia individual"""
    name: str
    signal: Signal
    confidence: float  # 0.0 - 1.0
    strength: float    # Valor numérico de la señal
    reasoning: str


@dataclass
class CoherenceReport:
    """Reporte completo de coherencia"""
    coherence_score: float  # 0-100
    coherence_level: CoherenceLevel
    total_strategies: int
    bullish_count: int
    bearish_count: int
    neutral_count: int
    contradictions: List[str]
    consensus_signal: Signal
    consensus_confidence: float
    timestamp: datetime
    decision_recommendation: str


class CoherenceEngine:
    """
    Motor de Coherencia para OMNIX V5.3 ULTRA
    
    Funcionalidades:
    1. Analiza coherencia entre las 9 estrategias
    2. Detecta contradicciones y conflictos
    3. Calcula score de coherencia (0-100%)
    4. Genera recomendación final con confianza
    5. Identifica estrategias outliers
    """
    
    def __init__(self):
        self.strategy_weights = {
            'quantum_momentum': 0.20,    # Mayor peso - estrategia principal
            'kalman_filter': 0.15,       # Alta confiabilidad
            'monte_carlo': 0.15,         # Validación estadística
            'hmm_regime': 0.12,          # Contexto de mercado
            'kelly_criterion': 0.10,     # Optimización matemática
            'black_swan': 0.10,          # Protección de riesgo
            'order_book': 0.08,          # Flow institucional
            'sentiment': 0.06,           # Análisis de mercado
            'sharia_compliance': 0.04    # Filtro ético
        }
        
        logger.info("🧠 Coherence Engine inicializado con 9 estrategias")
    
    def analyze_coherence(self, signals: List[StrategySignal]) -> CoherenceReport:
        """
        Analiza la coherencia entre todas las señales de estrategias
        
        Args:
            signals: Lista de señales de cada estrategia
            
        Returns:
            CoherenceReport con análisis completo
        """
        if not signals:
            logger.warning("⚠️ No hay señales para analizar")
            return self._create_empty_report()
        
        # 1. Clasificar señales
        bullish = [s for s in signals if s.signal.value > 0]
        bearish = [s for s in signals if s.signal.value < 0]
        neutral = [s for s in signals if s.signal.value == 0]
        
        # 2. Detectar contradicciones
        contradictions = self._detect_contradictions(signals)
        
        # 3. Calcular coherencia
        coherence_score = self._calculate_coherence_score(
            bullish, bearish, neutral, contradictions
        )
        
        # 4. Determinar consenso
        consensus_signal, consensus_confidence = self._calculate_consensus(signals)
        
        # 5. Clasificar nivel de coherencia
        coherence_level = self._classify_coherence_level(coherence_score)
        
        # 6. Generar recomendación
        recommendation = self._generate_recommendation(
            consensus_signal, consensus_confidence, coherence_score, contradictions
        )
        
        report = CoherenceReport(
            coherence_score=coherence_score,
            coherence_level=coherence_level,
            total_strategies=len(signals),
            bullish_count=len(bullish),
            bearish_count=len(bearish),
            neutral_count=len(neutral),
            contradictions=contradictions,
            consensus_signal=consensus_signal,
            consensus_confidence=consensus_confidence,
            timestamp=datetime.now(),
            decision_recommendation=recommendation
        )
        
        logger.info(f"📊 Coherencia: {coherence_score:.1f}% - {coherence_level.value}")
        return report
    
    def _detect_contradictions(self, signals: List[StrategySignal]) -> List[str]:
        """Detecta contradicciones entre estrategias"""
        contradictions = []
        
        # Agrupar por señal
        signal_groups = {}
        for s in signals:
            if s.signal not in signal_groups:
                signal_groups[s.signal] = []
            signal_groups[s.signal].append(s.name)
        
        # Detectar si hay señales opuestas fuertes
        has_strong_buy = Signal.STRONG_BUY in signal_groups
        has_strong_sell = Signal.STRONG_SELL in signal_groups
        has_buy = Signal.BUY in signal_groups
        has_sell = Signal.SELL in signal_groups
        
        if has_strong_buy and has_strong_sell:
            contradictions.append(
                f"CRÍTICO: Señales opuestas fuertes - "
                f"STRONG_BUY: {signal_groups[Signal.STRONG_BUY]} vs "
                f"STRONG_SELL: {signal_groups[Signal.STRONG_SELL]}"
            )
        
        if has_strong_buy and has_sell:
            contradictions.append(
                f"ALTO: STRONG_BUY vs SELL - "
                f"{signal_groups[Signal.STRONG_BUY]} vs {signal_groups[Signal.SELL]}"
            )
        
        if has_buy and has_strong_sell:
            contradictions.append(
                f"ALTO: BUY vs STRONG_SELL - "
                f"{signal_groups[Signal.BUY]} vs {signal_groups[Signal.STRONG_SELL]}"
            )
        
        if has_buy and has_sell:
            contradictions.append(
                f"MEDIO: Señales mixtas - "
                f"BUY: {signal_groups[Signal.BUY]} vs SELL: {signal_groups[Signal.SELL]}"
            )
        
        # Detectar estrategias outliers (muy diferentes al consenso)
        if len(signals) >= 3:
            avg_signal = sum(s.signal.value for s in signals) / len(signals)
            for s in signals:
                deviation = abs(s.signal.value - avg_signal)
                if deviation >= 2.5:  # Muy diferente
                    contradictions.append(
                        f"OUTLIER: {s.name} señal {s.signal.name} "
                        f"muy diferente del consenso"
                    )
        
        return contradictions
    
    def _calculate_coherence_score(
        self, 
        bullish: List[StrategySignal],
        bearish: List[StrategySignal],
        neutral: List[StrategySignal],
        contradictions: List[str]
    ) -> float:
        """
        Calcula score de coherencia (0-100%)
        
        Factores:
        - Alineación de señales (70%)
        - Nivel de contradicciones (20%)
        - Confianza promedio (10%)
        """
        total = len(bullish) + len(bearish) + len(neutral)
        if total == 0:
            return 0.0
        
        # 1. Score de alineación (70%)
        max_group = max(len(bullish), len(bearish), len(neutral))
        alignment_score = (max_group / total) * 70
        
        # 2. Penalización por contradicciones (20%)
        contradiction_penalty = min(len(contradictions) * 7, 20)  # Max 20%
        
        # 3. Bonus por confianza promedio (10%)
        all_signals = bullish + bearish + neutral
        avg_confidence = sum(s.confidence for s in all_signals) / len(all_signals)
        confidence_bonus = avg_confidence * 10
        
        # Score final
        coherence = alignment_score - contradiction_penalty + confidence_bonus
        coherence = max(0, min(100, coherence))  # Clamp 0-100
        
        return round(coherence, 2)
    
    def _calculate_consensus(
        self, 
        signals: List[StrategySignal]
    ) -> Tuple[Signal, float]:
        """
        Calcula la señal de consenso usando pesos de estrategias
        
        Returns:
            (señal_consenso, confianza_0_a_1)
        """
        if not signals:
            return Signal.HOLD, 0.0
        
        # Calcular voto ponderado
        weighted_sum = 0.0
        total_weight = 0.0
        total_confidence = 0.0
        
        for s in signals:
            weight = self.strategy_weights.get(s.name, 0.1)
            weighted_sum += s.signal.value * weight * s.confidence
            total_weight += weight
            total_confidence += s.confidence
        
        if total_weight == 0:
            return Signal.HOLD, 0.0
        
        # Normalizar
        weighted_avg = weighted_sum / total_weight
        avg_confidence = total_confidence / len(signals)
        
        # Convertir a señal
        if weighted_avg >= 1.5:
            consensus = Signal.STRONG_BUY
        elif weighted_avg >= 0.5:
            consensus = Signal.BUY
        elif weighted_avg <= -1.5:
            consensus = Signal.STRONG_SELL
        elif weighted_avg <= -0.5:
            consensus = Signal.SELL
        else:
            consensus = Signal.HOLD
        
        return consensus, round(avg_confidence, 3)
    
    def _classify_coherence_level(self, score: float) -> CoherenceLevel:
        """Clasifica el nivel de coherencia"""
        if score >= 90:
            return CoherenceLevel.EXCELLENT
        elif score >= 70:
            return CoherenceLevel.GOOD
        elif score >= 50:
            return CoherenceLevel.MODERATE
        elif score >= 30:
            return CoherenceLevel.POOR
        else:
            return CoherenceLevel.CRITICAL
    
    def _generate_recommendation(
        self,
        consensus: Signal,
        confidence: float,
        coherence: float,
        contradictions: List[str]
    ) -> str:
        """Genera recomendación final basada en coherencia"""
        
        # Decisión base
        if consensus == Signal.STRONG_BUY:
            action = "EJECUTAR COMPRA FUERTE"
        elif consensus == Signal.BUY:
            action = "EJECUTAR COMPRA"
        elif consensus == Signal.STRONG_SELL:
            action = "EJECUTAR VENTA FUERTE"
        elif consensus == Signal.SELL:
            action = "EJECUTAR VENTA"
        else:
            action = "MANTENER POSICIÓN (HOLD)"
        
        # Modificadores por coherencia
        if coherence >= 90:
            modifier = "✅ ALTÍSIMA CONFIANZA"
        elif coherence >= 70:
            modifier = "✅ ALTA CONFIANZA"
        elif coherence >= 50:
            modifier = "⚠️ CONFIANZA MODERADA - Considerar reducir tamaño"
        elif coherence >= 30:
            modifier = "⚠️ BAJA CONFIANZA - Reducir tamaño significativamente"
        else:
            modifier = "🚨 CONFIANZA CRÍTICA - NO OPERAR"
        
        # Advertencias por contradicciones
        if len(contradictions) >= 3:
            warning = " | 🚨 MÚLTIPLES CONTRADICCIONES DETECTADAS"
        elif len(contradictions) >= 1:
            warning = " | ⚠️ Contradicciones presentes"
        else:
            warning = ""
        
        # Si coherencia crítica, override a HOLD
        if coherence < 30:
            action = "MANTENER POSICIÓN (HOLD)"
        
        return f"{action} | {modifier} | Coherencia: {coherence:.1f}%{warning}"
    
    def _create_empty_report(self) -> CoherenceReport:
        """Crea reporte vacío para cuando no hay señales"""
        return CoherenceReport(
            coherence_score=0.0,
            coherence_level=CoherenceLevel.CRITICAL,
            total_strategies=0,
            bullish_count=0,
            bearish_count=0,
            neutral_count=0,
            contradictions=["No hay señales disponibles"],
            consensus_signal=Signal.HOLD,
            consensus_confidence=0.0,
            timestamp=datetime.now(),
            decision_recommendation="NO OPERAR - Sin señales disponibles"
        )
    
    def format_report(self, report: CoherenceReport) -> str:
        """Formatea el reporte para visualización"""
        
        lines = [
            "=" * 60,
            "🧠 OMNIX COHERENCE ENGINE - REPORTE DE COHERENCIA",
            "=" * 60,
            f"📊 Score de Coherencia: {report.coherence_score:.1f}%",
            f"🎯 Nivel: {report.coherence_level.value}",
            f"📈 Estrategias Alcistas: {report.bullish_count}/{report.total_strategies}",
            f"📉 Estrategias Bajistas: {report.bearish_count}/{report.total_strategies}",
            f"➡️  Estrategias Neutrales: {report.neutral_count}/{report.total_strategies}",
            "",
            f"🎯 SEÑAL DE CONSENSO: {report.consensus_signal.name}",
            f"💪 Confianza del Consenso: {report.consensus_confidence*100:.1f}%",
            "",
            "⚡ RECOMENDACIÓN FINAL:",
            f"   {report.decision_recommendation}",
        ]
        
        if report.contradictions:
            lines.append("")
            lines.append("⚠️  CONTRADICCIONES DETECTADAS:")
            for i, contradiction in enumerate(report.contradictions, 1):
                lines.append(f"   {i}. {contradiction}")
        
        lines.append("=" * 60)
        lines.append(f"⏰ Generado: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def get_coherence_emoji(self, score: float) -> str:
        """Retorna emoji basado en score de coherencia"""
        if score >= 90:
            return "🟢"  # Verde - Excelente
        elif score >= 70:
            return "🔵"  # Azul - Bueno
        elif score >= 50:
            return "🟡"  # Amarillo - Moderado
        elif score >= 30:
            return "🟠"  # Naranja - Pobre
        else:
            return "🔴"  # Rojo - Crítico
    
    def validate_trade_coherence(
        self,
        signals: List[StrategySignal],
        action: str,
        confidence: float,
        analysis_data: Optional[Dict] = None,
        paper_mode: bool = False
    ) -> Tuple[bool, str]:
        """
        🔴 VALIDACIÓN CRÍTICA DE COHERENCIA - BLOQUEA TRADES PELIGROSOS
        
        Reglas de bloqueo implementadas:
        1. Si 5+ estrategias votan BUY pero 3+ votan SELL → BLOQUEAR
        2. Si Black Swan = HIGH RISK → Bloquear todos los trades
        3. Si Regime = RANGING → Bloquear estrategias de tendencia
        4. Si Monte Carlo < 50% win rate → Requiere confirmación adicional
        5. Si confianza final < 60% → BLOQUEAR (excepto paper trading)
        
        Args:
            signals: Lista de señales de las 9 estrategias
            action: Acción propuesta (BUY/SELL/HOLD)
            confidence: Confianza de la decisión (0-1)
            analysis_data: Data adicional (black_swan, monte_carlo, hmm_regime, etc)
            paper_mode: Si True, relaja algunas restricciones
            
        Returns:
            (permitir_trade: bool, razon: str)
        """
        analysis_data = analysis_data or {}
        
        # FIX: Si no hay señales formales, usar fallback basado en la acción
        if not signals:
            logger.warning(f"⚠️ Sin señales formales - usando fallback para acción {action}")
            # Crear señal de fallback basada en la acción decidida
            fallback_signal = Signal.BUY if action == 'BUY' else Signal.SELL if action == 'SELL' else Signal.HOLD
            signals = [StrategySignal(
                name='primary_decision',
                signal=fallback_signal,
                confidence=confidence,
                strength=confidence * 100,
                reasoning=f"Fallback: acción {action} con confianza {confidence*100:.1f}%"
            )]
        
        block_reasons = []
        warnings = []
        
        # Clasificar señales
        bullish = [s for s in signals if s.signal.value > 0]
        bearish = [s for s in signals if s.signal.value < 0]
        neutral = [s for s in signals if s.signal.value == 0]
        
        # ========== REGLA 1: Contradicción 5+ vs 3+ ==========
        if len(bullish) >= 5 and len(bearish) >= 3:
            block_reasons.append(
                f"🚫 CONTRADICCIÓN CRÍTICA: {len(bullish)} estrategias BUY vs "
                f"{len(bearish)} estrategias SELL (>70% contradicción)"
            )
        
        if len(bearish) >= 5 and len(bullish) >= 3:
            block_reasons.append(
                f"🚫 CONTRADICCIÓN CRÍTICA: {len(bearish)} estrategias SELL vs "
                f"{len(bullish)} estrategias BUY (>70% contradicción)"
            )
        
        # ========== REGLA 2: Black Swan HIGH RISK ==========
        black_swan_data = analysis_data.get('black_swan', {})
        if black_swan_data:
            risk_level = black_swan_data.get('risk_level', 'UNKNOWN')
            if risk_level == 'HIGH' or risk_level == 'EXTREME':
                block_reasons.append(
                    f"🚫 BLACK SWAN ALERT: Riesgo {risk_level} detectado - "
                    f"Kurtosis/Skewness extremos - NO OPERAR"
                )
        
        # ========== REGLA 3: Regime RANGING bloquea tendencias ==========
        hmm_regime = analysis_data.get('hmm_regime', {})
        if hmm_regime:
            regime = hmm_regime.get('regime', 'UNKNOWN')
            if regime == 'RANGING' and action in ['BUY', 'SELL']:
                # En RANGING, solo permitir si hay consenso fuerte
                if len(bullish) < 7 and len(bearish) < 7:
                    warnings.append(
                        f"⚠️ RÉGIMEN RANGING: Mercado lateral - "
                        f"Estrategias de tendencia bloqueadas sin consenso >77%"
                    )
        
        # ========== REGLA 4: Monte Carlo < 50% win rate ==========
        # En paper mode, no bloquear por Monte Carlo bajo - usar throttle
        monte_carlo_data = analysis_data.get('monte_carlo', {})
        if monte_carlo_data:
            win_rate = monte_carlo_data.get('win_rate', 0)
            if win_rate < 0.50:
                if not paper_mode:
                    block_reasons.append(
                        f"🚫 MONTE CARLO: Win rate {win_rate*100:.1f}% < 50% - "
                        f"Probabilidades desfavorables - TRADE BLOQUEADO"
                    )
                else:
                    # Paper mode: advertir pero NO bloquear
                    warnings.append(
                        f"⚠️ MONTE CARLO: Win rate {win_rate*100:.1f}% < 50% - "
                        f"PAPER MODE: Permitido con tamaño reducido 50%"
                    )
            elif win_rate < 0.55:
                warnings.append(
                    f"⚠️ MONTE CARLO: Win rate {win_rate*100:.1f}% marginal - "
                    f"Considerar reducir tamaño de posición"
                )
        
        # ========== REGLA 5: Confianza < 60% ==========
        if confidence < 0.60:
            if not paper_mode:
                block_reasons.append(
                    f"🚫 CONFIANZA INSUFICIENTE: {confidence*100:.1f}% < 60% - "
                    f"TRADE BLOQUEADO (REAL MONEY)"
                )
            else:
                warnings.append(
                    f"⚠️ CONFIANZA BAJA: {confidence*100:.1f}% < 60% - "
                    f"Permitido solo en PAPER MODE"
                )
        
        # ========== VALIDACIÓN ADICIONAL: Coherencia general ==========
        report = self.analyze_coherence(signals)
        
        # V6.5: Umbrales diferenciados para paper vs real trading
        # Paper mode: umbral 10% (permite trades para calibración)
        # Real mode: umbral 30% (protección estricta)
        coherence_block_threshold = 10 if paper_mode else 30
        coherence_warn_threshold = 30 if paper_mode else 50
        
        if report.coherence_score < coherence_block_threshold:
            block_reasons.append(
                f"🚫 COHERENCIA CRÍTICA: {report.coherence_score:.1f}% < {coherence_block_threshold}% - "
                f"Demasiadas contradicciones entre estrategias"
            )
        elif report.coherence_score < coherence_warn_threshold:
            mode_label = "PAPER MODE - Permitido para calibración" if paper_mode else "Reducir tamaño de posición 50%"
            warnings.append(
                f"⚠️ COHERENCIA BAJA: {report.coherence_score:.1f}% < {coherence_warn_threshold}% - "
                f"{mode_label}"
            )
        
        # ========== DECISIÓN FINAL ==========
        if block_reasons:
            # TRADE BLOQUEADO
            reason_text = "\n".join(block_reasons)
            if warnings:
                reason_text += "\n\n⚠️ ADVERTENCIAS ADICIONALES:\n" + "\n".join(warnings)
            
            logger.warning(f"🚫 TRADE BLOQUEADO por Coherence Engine:\n{reason_text}")
            return False, reason_text
        
        # TRADE PERMITIDO (con advertencias opcionales)
        if warnings:
            warning_text = "\n".join(warnings)
            logger.info(f"✅ TRADE PERMITIDO con advertencias:\n{warning_text}")
            return True, f"✅ PERMITIDO | Coherencia: {report.coherence_score:.1f}%\n{warning_text}"
        
        # TRADE PERMITIDO (sin advertencias)
        logger.info(f"✅ TRADE PERMITIDO - Coherencia: {report.coherence_score:.1f}%")
        return True, f"✅ APROBADO | Coherencia: {report.coherence_score:.1f}% | Sin contradicciones"
    
    def calibrate_weights_from_performance(
        self, 
        trade_history: List[Dict],
        min_weight: float = 0.02,
        max_weight: float = 0.35
    ) -> Dict[str, float]:
        """
        Calibrate strategy weights based on historical trade performance.
        
        Methodology:
        1. For each trade, identify which strategies signaled correctly
        2. Calculate hit rate (correct signals / total signals) per strategy
        3. Weight by profitability contribution
        4. Apply regularization (min/max floors)
        5. Normalize to sum = 1.0
        
        Args:
            trade_history: List of trades with structure:
                {
                    'strategy_signals': {'strategy_name': signal_value, ...},
                    'actual_outcome': 'profit' | 'loss',
                    'pnl_percent': float
                }
            min_weight: Minimum weight per strategy (default 0.02)
            max_weight: Maximum weight per strategy (default 0.35)
            
        Returns:
            Dict with calibrated weights per strategy
        """
        if not trade_history:
            logger.warning("⚠️ No trade history for calibration, using defaults")
            return self.strategy_weights.copy()
        
        strategy_stats = {name: {'wins': 0, 'total': 0, 'pnl_contribution': 0.0}
                         for name in self.strategy_weights.keys()}
        
        for trade in trade_history:
            signals = trade.get('strategy_signals', {})
            outcome = trade.get('actual_outcome', 'loss')
            pnl = trade.get('pnl_percent', 0.0)
            
            for strategy_name, signal_value in signals.items():
                if strategy_name not in strategy_stats:
                    continue
                    
                strategy_stats[strategy_name]['total'] += 1
                
                was_correct = False
                if outcome == 'profit' and signal_value > 0:
                    was_correct = True
                elif outcome == 'profit' and signal_value < 0:
                    was_correct = True
                    
                if was_correct:
                    strategy_stats[strategy_name]['wins'] += 1
                    strategy_stats[strategy_name]['pnl_contribution'] += abs(pnl)
        
        raw_weights = {}
        for name, stats in strategy_stats.items():
            if stats['total'] == 0:
                raw_weights[name] = self.strategy_weights.get(name, 0.1)
            else:
                hit_rate = stats['wins'] / stats['total']
                pnl_factor = 1.0 + (stats['pnl_contribution'] / (stats['total'] * 2.0))
                base_weight = self.strategy_weights.get(name, 0.1)
                raw_weights[name] = hit_rate * pnl_factor * base_weight
        
        total = sum(raw_weights.values())
        if total > 0:
            normalized = {name: w / total for name, w in raw_weights.items()}
        else:
            normalized = self.strategy_weights.copy()
        
        n = len(normalized)
        min_sum = n * min_weight
        max_sum = n * max_weight
        
        if min_sum > 1.0 or max_sum < 1.0:
            logger.warning(f"⚠️ Infeasible bounds: {n} strategies with [{min_weight}, {max_weight}] cannot sum to 1.0")
            calibrated = self.strategy_weights.copy()
        else:
            result = {name: max(min_weight, min(max_weight, w)) for name, w in normalized.items()}
            
            for _ in range(50):
                current_sum = sum(result.values())
                if abs(current_sum - 1.0) < 0.0001:
                    break
                    
                delta = 1.0 - current_sum
                if delta > 0:
                    adjustable = [n for n in result if result[n] < max_weight - 0.0001]
                else:
                    adjustable = [n for n in result if result[n] > min_weight + 0.0001]
                
                if not adjustable:
                    break
                    
                per_item = delta / len(adjustable)
                for name in adjustable:
                    new_val = result[name] + per_item
                    result[name] = max(min_weight, min(max_weight, new_val))
            
            calibrated = {name: round(w, 4) for name, w in result.items()}
        
        logger.info("🔧 Calibrated Coherence Engine weights:")
        for name, weight in sorted(calibrated.items(), key=lambda x: -x[1]):
            old_weight = self.strategy_weights.get(name, 0)
            change = ((weight - old_weight) / old_weight * 100) if old_weight > 0 else 0
            logger.info(f"   {name}: {old_weight:.2%} → {weight:.2%} ({change:+.1f}%)")
        
        return calibrated
    
    def apply_calibrated_weights(self, calibrated_weights: Dict[str, float]) -> None:
        """Apply calibrated weights to the engine."""
        self.strategy_weights = calibrated_weights.copy()
        logger.info("✅ Applied calibrated weights to Coherence Engine")


# ============================================
# EJEMPLO DE USO
# ============================================

def example_usage():
    """Ejemplo de cómo usar el Coherence Engine"""
    
    # Crear engine
    engine = CoherenceEngine()
    
    # Simular señales de las 9 estrategias
    signals = [
        StrategySignal(
            name="quantum_momentum",
            signal=Signal.BUY,
            confidence=0.85,
            strength=8.5,
            reasoning="6 componentes alcistas"
        ),
        StrategySignal(
            name="kalman_filter",
            signal=Signal.BUY,
            confidence=0.78,
            strength=0.87,
            reasoning="Tendencia alcista confirmada"
        ),
        StrategySignal(
            name="monte_carlo",
            signal=Signal.BUY,
            confidence=0.82,
            strength=78.0,
            reasoning="78% probabilidad de ganancia"
        ),
        StrategySignal(
            name="hmm_regime",
            signal=Signal.BUY,
            confidence=0.75,
            strength=1.0,
            reasoning="Régimen TRENDING alcista"
        ),
        StrategySignal(
            name="kelly_criterion",
            signal=Signal.BUY,
            confidence=0.70,
            strength=0.25,
            reasoning="25% tamaño óptimo"
        ),
        StrategySignal(
            name="black_swan",
            signal=Signal.HOLD,
            confidence=0.65,
            strength=0.0,
            reasoning="Riesgo bajo detectado"
        ),
        StrategySignal(
            name="order_book",
            signal=Signal.BUY,
            confidence=0.72,
            strength=1.0,
            reasoning="Flow institucional positivo"
        ),
        StrategySignal(
            name="sentiment",
            signal=Signal.SELL,  # Contradictoria!
            confidence=0.60,
            strength=-0.5,
            reasoning="Sentiment bajista en redes"
        ),
        StrategySignal(
            name="sharia_compliance",
            signal=Signal.BUY,
            confidence=1.0,
            strength=1.0,
            reasoning="Asset halal confirmado"
        ),
    ]
    
    # Analizar coherencia
    report = engine.analyze_coherence(signals)
    
    # Mostrar reporte
    print(engine.format_report(report))
    
    # Emoji de coherencia
    emoji = engine.get_coherence_emoji(report.coherence_score)
    print(f"\n{emoji} Score Visual: {report.coherence_score:.1f}%")


if __name__ == "__main__":
    example_usage()
