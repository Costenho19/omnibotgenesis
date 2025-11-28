"""
🧠 OMNIX CONVERSATIONAL BRAIN - SISTEMA DE RAZONAMIENTO AUTÓNOMO
Sistema único que hace que el bot "piense en voz alta" y explique cada decisión

Features:
- Generación de razonamiento pre-trade
- Auto-evaluación post-trade
- Aprendizaje de aciertos y errores
- Explicaciones en lenguaje natural
- Almacenamiento en PostgreSQL

Esto NO existe en bots retail. Solo en hedge funds top.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import json

logger = logging.getLogger(__name__)


class ConversationalBrain:
    """
    Cerebro Conversacional - El bot que piensa en voz alta
    
    Características:
    1. Genera razonamiento ANTES de cada trade
    2. Hace auto-evaluación DESPUÉS del trade
    3. Aprende de decisiones correctas e incorrectas
    4. Explica en lenguaje natural simple
    """
    
    def __init__(self, database_service=None):
        self.database = database_service
        self.reasoning_history = []
        self.evaluation_history = []
        
        logger.info("🧠 Conversational Brain initialized - Bot que piensa en voz alta")
    
    def generate_trade_reasoning(
        self,
        action: str,
        pair: str,
        amount_usd: float,
        signals: Dict,
        confidence: float
    ) -> Dict:
        """
        Generar razonamiento completo ANTES de ejecutar el trade
        
        Args:
            action: 'buy' o 'sell'
            pair: 'BTC/USD', etc.
            amount_usd: Monto en USD
            signals: Dict con señales de todas las estrategias
            confidence: Confianza total (0-1)
            
        Returns:
            Dict con razonamiento estructurado y texto
        """
        reasoning = {
            'timestamp': datetime.now().isoformat(),
            'action': action.upper(),
            'pair': pair,
            'amount_usd': amount_usd,
            'confidence': confidence,
            'signals': signals,
            'reasons': [],
            'summary': '',
            'full_explanation': ''
        }
        
        # Analizar cada señal y generar razones
        reasons = []
        
        # 1. Quantum Momentum
        if 'quantum_momentum' in signals:
            qm = signals['quantum_momentum']
            score = qm.get('signal', 0)
            if abs(score) > 5:
                direction = "muy alcista" if score > 0 else "muy bajista"
                emoji = "📈" if score > 0 else "📉"
                reasons.append({
                    'strategy': 'Quantum Momentum',
                    'emoji': '⚛️',
                    'value': score,
                    'interpretation': f"{emoji} {direction}",
                    'text': f"Quantum Momentum: {score:.1f}/10 ({direction})"
                })
        
        # 2. Kalman Filter
        if 'kalman_filter' in signals:
            kf = signals['kalman_filter']
            trend_strength = kf.get('trend_strength', 0)
            if trend_strength > 0.6:
                reasons.append({
                    'strategy': 'Kalman Filter',
                    'emoji': '📡',
                    'value': trend_strength,
                    'interpretation': 'trend fuerte detectado',
                    'text': f"Kalman Filter detectó trend fuerte ({trend_strength:.2f})"
                })
        
        # 3. Monte Carlo
        if 'monte_carlo' in signals:
            mc = signals['monte_carlo']
            win_rate = mc.get('win_rate', 0)
            if win_rate > 0.6:
                reasons.append({
                    'strategy': 'Monte Carlo',
                    'emoji': '🎲',
                    'value': win_rate,
                    'interpretation': f'{int(win_rate * 100)}% probabilidad ganancia',
                    'text': f"Monte Carlo: {int(win_rate * 100)}% probabilidad de ganancia"
                })
        
        # 4. Black Swan Risk
        if 'black_swan' in signals:
            bs = signals['black_swan']
            risk = bs.get('risk_level', 'MEDIUM')
            if risk == 'LOW':
                reasons.append({
                    'strategy': 'Black Swan',
                    'emoji': '🦢',
                    'value': risk,
                    'interpretation': 'riesgo bajo (seguro)',
                    'text': f"Black Swan Risk: {risk} (condiciones seguras)"
                })
        
        # 5. Kelly Criterion
        if 'kelly_criterion' in signals:
            kelly = signals['kelly_criterion']
            suggested = kelly.get('recommended_position_usd', 0)
            if suggested > 0:
                reasons.append({
                    'strategy': 'Kelly Criterion',
                    'emoji': '💎',
                    'value': suggested,
                    'interpretation': 'matemáticamente óptimo',
                    'text': f"Kelly sugirió ${suggested:.0f} (tamaño óptimo matemático)"
                })
        
        # 6. HMM Regime
        if 'hmm_regime' in signals:
            hmm = signals['hmm_regime']
            regime = hmm.get('regime', 'UNKNOWN')
            if regime in ['TRENDING', 'VOLATILE']:
                emoji = '📊' if regime == 'TRENDING' else '⚡'
                reasons.append({
                    'strategy': 'HMM Regime',
                    'emoji': emoji,
                    'value': regime,
                    'interpretation': f'mercado {regime.lower()}',
                    'text': f"Régimen de mercado: {regime}"
                })
        
        # 7. Sentiment
        if 'sentiment' in signals:
            sent = signals['sentiment']
            score = sent.get('score', 0.5)
            if score > 0.6:
                reasons.append({
                    'strategy': 'Sentiment Analysis',
                    'emoji': '😊',
                    'value': score,
                    'interpretation': 'sentimiento positivo',
                    'text': f"Sentimiento del mercado: {int(score * 100)}% positivo"
                })
        
        reasoning['reasons'] = reasons
        
        # Generar resumen
        summary = self._generate_summary(action, reasons, confidence)
        reasoning['summary'] = summary
        
        # 🌳 Generar Decision Graph (feature institucional)
        decision_graph = self._generate_decision_graph(signals, action, confidence)
        reasoning['decision_graph'] = decision_graph
        
        # Generar explicación completa
        full_explanation = self._generate_full_explanation(
            action, pair, amount_usd, reasons, confidence, decision_graph
        )
        reasoning['full_explanation'] = full_explanation
        
        # Guardar en historial
        self.reasoning_history.append(reasoning)
        
        # Guardar en base de datos si está disponible
        if self.database:
            self._save_reasoning_to_db(reasoning)
        
        return reasoning
    
    def _generate_decision_graph(self, signals: Dict, action: str, confidence: float) -> str:
        """
        🌳 DECISION GRAPH ENGINE - Árbol visual de decisiones
        
        Muestra cómo votó cada estrategia antes del trade.
        Feature institucional que NO existe en bots retail.
        """
        lines = []
        lines.append("┌─ DECISION TREE ─────────────────────────────┐")
        
        # Normalizar cada estrategia a formato uniforme
        strategies = []
        
        # 1. Quantum Momentum
        if 'quantum_momentum' in signals:
            qm = signals['quantum_momentum']
            score = qm.get('signal', 0)
            if score > 3:
                vote = "BUY"
            elif score < -3:
                vote = "SELL"
            else:
                vote = "HOLD"
            strategies.append({
                'name': 'Quantum Momentum',
                'vote': vote,
                'score': f"{score:.1f}/10",
                'emoji': '⚛️'
            })
        
        # 2. Kalman Filter
        if 'kalman_filter' in signals:
            kf = signals['kalman_filter']
            trend = kf.get('trend_strength', 0)
            prediction = kf.get('prediction', 0)
            if prediction > 0.02:
                vote = "BUY"
            elif prediction < -0.02:
                vote = "SELL"
            else:
                vote = "HOLD"
            strategies.append({
                'name': 'Kalman Filter',
                'vote': vote,
                'score': f"{trend:.2f}",
                'emoji': '📡'
            })
        
        # 3. Monte Carlo
        if 'monte_carlo' in signals:
            mc = signals['monte_carlo']
            win_rate = mc.get('win_rate', 0.5)
            if win_rate > 0.6:
                vote = "BUY"
            elif win_rate < 0.4:
                vote = "SELL"
            else:
                vote = "HOLD"
            strategies.append({
                'name': 'Monte Carlo',
                'vote': vote,
                'score': f"{int(win_rate * 100)}%",
                'emoji': '🎲'
            })
        
        # 4. HMM Regime
        if 'hmm_regime' in signals:
            hmm = signals['hmm_regime']
            regime = hmm.get('regime', 'UNKNOWN')
            status = "✅" if regime in ['TRENDING', 'VOLATILE'] else "⚠️"
            strategies.append({
                'name': 'Regime Detector',
                'vote': regime,
                'score': '',
                'emoji': '🔬',
                'status': status
            })
        
        # 5. Black Swan
        if 'black_swan' in signals:
            bs = signals['black_swan']
            risk = bs.get('risk_level', 'MEDIUM')
            status = "✅" if risk == 'LOW' else "⚠️" if risk == 'MEDIUM' else "🚨"
            strategies.append({
                'name': 'Black Swan',
                'vote': f"{risk} RISK",
                'score': '',
                'emoji': '🦢',
                'status': status
            })
        
        # 6. Kelly Criterion
        if 'kelly_criterion' in signals:
            kelly = signals['kelly_criterion']
            suggested = kelly.get('recommended_position_usd', 0)
            if suggested > 0:
                strategies.append({
                    'name': 'Kelly Criterion',
                    'vote': 'BUY',
                    'score': f"${suggested:.0f}",
                    'emoji': '💎'
                })
        
        # 7. Sentiment
        if 'sentiment' in signals:
            sent = signals['sentiment']
            score = sent.get('score', 0.5)
            if score > 0.6:
                vote = "BULLISH"
            elif score < 0.4:
                vote = "BEARISH"
            else:
                vote = "NEUTRAL"
            strategies.append({
                'name': 'Sentiment',
                'vote': vote,
                'score': f"{int(score * 100)}%",
                'emoji': '📊'
            })
        
        # Renderizar cada estrategia
        for strat in strategies:
            emoji = strat.get('emoji', '•')
            name = strat['name']
            vote = strat['vote']
            score = strat.get('score', '')
            status = strat.get('status', '')
            
            # Formatear línea
            if score:
                line = f"│ {emoji} {name}: {vote} ({score})"
            else:
                line = f"│ {emoji} {name}: {vote}"
            
            if status:
                line += f" {status}"
            
            # Padding para alinear
            line = line.ljust(47) + "│"
            lines.append(line)
        
        # Si no hay estrategias, mostrar mensaje
        if not strategies:
            lines.append("│ No hay datos suficientes                    │")
        
        # Separador
        lines.append("├─────────────────────────────────────────────┤")
        
        # Decisión final
        decision_emoji = "✔️" if action.upper() == "BUY" else "❌" if action.upper() == "SELL" else "⏸️"
        final_line = f"│ 🎯 Final Decision: {action.upper()} {decision_emoji}"
        final_line = final_line.ljust(47) + "│"
        lines.append(final_line)
        
        conf_line = f"│ 📊 Confidence: {int(confidence * 100)}%"
        conf_line = conf_line.ljust(47) + "│"
        lines.append(conf_line)
        
        lines.append("└─────────────────────────────────────────────┘")
        
        return "\n".join(lines)
    
    def _generate_summary(self, action: str, reasons: List[Dict], confidence: float) -> str:
        """Generar resumen corto del razonamiento"""
        if not reasons:
            return f"Decisión de {action} basada en análisis general"
        
        # Top 3 razones
        top_reasons = reasons[:3]
        summary_parts = [r['strategy'] for r in top_reasons]
        
        return f"{action.upper()} basado en: {', '.join(summary_parts)} (confianza {int(confidence * 100)}%)"
    
    def _generate_full_explanation(
        self,
        action: str,
        pair: str,
        amount_usd: float,
        reasons: List[Dict],
        confidence: float,
        decision_graph: Optional[str] = None
    ) -> str:
        """
        Generar explicación completa en lenguaje natural
        
        Esto es lo que hace al bot ÚNICO - explica como un humano
        """
        explanation = f"📊 RAZONAMIENTO DE TRADE\n\n"
        explanation += f"💰 Decisión: {action.upper()} {amount_usd:.2f} USD de {pair}\n\n"
        
        # 🌳 Agregar Decision Graph (árbol visual de estrategias)
        if decision_graph:
            explanation += f"\n{decision_graph}\n\n"
        
        if reasons:
            explanation += f"🧠 ¿Por qué tomé esta decisión?\n\n"
            
            for i, reason in enumerate(reasons, 1):
                emoji = reason.get('emoji', '•')
                text = reason.get('text', '')
                explanation += f"{i}. {emoji} {text}\n"
            
            explanation += f"\n✅ Confianza total: {int(confidence * 100)}%\n"
            
            # Agregar contexto adicional
            if confidence > 0.8:
                explanation += "\n💪 Confianza MUY ALTA - Todas las señales convergen"
            elif confidence > 0.6:
                explanation += "\n👍 Confianza ALTA - Mayoría de señales positivas"
            else:
                explanation += "\n⚠️ Confianza MODERADA - Algunas señales mixtas"
        else:
            explanation += "Análisis técnico general sugiere esta dirección.\n"
        
        return explanation
    
    def generate_post_trade_evaluation(
        self,
        trade_id: str,
        original_reasoning: Dict,
        trade_result: Dict,
        elapsed_minutes: int = 30
    ) -> Dict:
        """
        Auto-evaluación DESPUÉS del trade
        
        El bot se pregunta: "¿Fue buena decisión?"
        
        Args:
            trade_id: ID del trade
            original_reasoning: Razonamiento original pre-trade
            trade_result: Resultado del trade (profit/loss, etc.)
            elapsed_minutes: Tiempo transcurrido
            
        Returns:
            Dict con auto-evaluación
        """
        evaluation = {
            'trade_id': trade_id,
            'timestamp': datetime.now().isoformat(),
            'elapsed_minutes': elapsed_minutes,
            'original_action': original_reasoning.get('action'),
            'original_confidence': original_reasoning.get('confidence'),
            'result': trade_result,
            'was_correct': False,
            'learning_points': [],
            'adjustments_suggested': [],
            'full_review': ''
        }
        
        # Determinar si fue correcto
        profit_loss = trade_result.get('profit_loss', 0)
        evaluation['was_correct'] = profit_loss > 0
        
        # Analizar qué funcionó y qué no
        learning_points = []
        adjustments = []
        
        if profit_loss > 0:
            # Trade exitoso
            learning_points.append("✅ Decisión correcta - Trade rentable")
            learning_points.append(f"💰 Ganancia: ${profit_loss:.2f}")
            
            # Analizar qué señales fueron más acertadas
            reasons = original_reasoning.get('reasons', [])
            if reasons:
                top_strategy = reasons[0]['strategy']
                learning_points.append(f"🎯 {top_strategy} fue muy acertado")
                learning_points.append("✅ Mantener parámetros actuales")
        else:
            # Trade perdedor
            learning_points.append("❌ Decisión incorrecta - Trade perdedor")
            learning_points.append(f"💸 Pérdida: ${abs(profit_loss):.2f}")
            
            # Analizar qué falló
            confidence = original_reasoning.get('confidence', 0)
            if confidence < 0.6:
                learning_points.append("⚠️ Confianza era baja - debí evitar trade")
                adjustments.append("Aumentar threshold de confianza mínima")
            
            # Revisar señales específicas
            signals = original_reasoning.get('signals', {})
            if 'black_swan' in signals:
                risk = signals['black_swan'].get('risk_level')
                if risk != 'LOW':
                    learning_points.append(f"🦢 Black Swan riesgo era {risk} - señal de peligro")
                    adjustments.append("No tradear con Black Swan risk > LOW")
        
        evaluation['learning_points'] = learning_points
        evaluation['adjustments_suggested'] = adjustments
        
        # Generar review completo
        review = self._generate_full_review(evaluation, original_reasoning)
        evaluation['full_review'] = review
        
        # Guardar en historial
        self.evaluation_history.append(evaluation)
        
        # Guardar en base de datos
        if self.database:
            self._save_evaluation_to_db(evaluation)
        
        return evaluation
    
    def _generate_full_review(self, evaluation: Dict, original_reasoning: Dict) -> str:
        """Generar review completo de la decisión"""
        review = f"🔍 AUTO-EVALUACIÓN POST-TRADE\n\n"
        
        elapsed = evaluation['elapsed_minutes']
        review += f"⏱️ {elapsed} minutos después del trade\n\n"
        
        # Resultado
        was_correct = evaluation['was_correct']
        emoji = "✅" if was_correct else "❌"
        result_text = "EXITOSO" if was_correct else "PERDEDOR"
        
        review += f"{emoji} RESULTADO: {result_text}\n\n"
        
        # Learning points
        if evaluation['learning_points']:
            review += "📚 APRENDIZAJES:\n\n"
            for point in evaluation['learning_points']:
                review += f"• {point}\n"
            review += "\n"
        
        # Ajustes sugeridos
        if evaluation['adjustments_suggested']:
            review += "⚙️ AJUSTES SUGERIDOS:\n\n"
            for adj in evaluation['adjustments_suggested']:
                review += f"• {adj}\n"
        else:
            review += "✅ No se requieren ajustes - estrategia funcionó bien\n"
        
        return review
    
    def _save_reasoning_to_db(self, reasoning: Dict):
        """Guardar razonamiento en PostgreSQL"""
        try:
            if self.database is not None and hasattr(self.database, 'save_trade_reasoning'):
                self.database.save_trade_reasoning(reasoning)
                logger.debug(f"💾 Razonamiento guardado en DB")
        except Exception as e:
            logger.warning(f"Error guardando razonamiento: {e}")
    
    def _save_evaluation_to_db(self, evaluation: Dict):
        """Guardar evaluación en PostgreSQL"""
        try:
            if self.database is not None and hasattr(self.database, 'save_trade_evaluation'):
                self.database.save_trade_evaluation(evaluation)
                logger.debug(f"💾 Evaluación guardada en DB")
        except Exception as e:
            logger.warning(f"Error guardando evaluación: {e}")
    
    def get_recent_reasonings(self, limit: int = 10) -> List[Dict]:
        """Obtener razonamientos recientes"""
        return self.reasoning_history[-limit:]
    
    def get_recent_evaluations(self, limit: int = 10) -> List[Dict]:
        """Obtener evaluaciones recientes"""
        return self.evaluation_history[-limit:]
    
    def get_learning_summary(self) -> Dict:
        """
        Resumen de aprendizajes acumulados
        
        Returns:
            Estadísticas de qué funciona y qué no
        """
        total_evaluations = len(self.evaluation_history)
        if total_evaluations == 0:
            return {
                'total_trades_evaluated': 0,
                'success_rate': 0,
                'top_performing_strategies': [],
                'adjustments_needed': []
            }
        
        successful = sum(1 for e in self.evaluation_history if e['was_correct'])
        success_rate = successful / total_evaluations
        
        # Recopilar ajustes sugeridos
        all_adjustments = []
        for eval in self.evaluation_history:
            all_adjustments.extend(eval.get('adjustments_suggested', []))
        
        # Contar frecuencia de ajustes
        adjustment_counts = {}
        for adj in all_adjustments:
            adjustment_counts[adj] = adjustment_counts.get(adj, 0) + 1
        
        # Top ajustes
        top_adjustments = sorted(
            adjustment_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            'total_trades_evaluated': total_evaluations,
            'successful_trades': successful,
            'failed_trades': total_evaluations - successful,
            'success_rate': success_rate * 100,
            'top_adjustments_needed': [adj[0] for adj in top_adjustments],
            'overall_performance': 'EXCELENTE' if success_rate > 0.7 else 'BUENO' if success_rate > 0.5 else 'MEJORABLE'
        }


# Singleton global
_conversational_brain = None


def get_conversational_brain(database_service=None):
    """
    Obtener instancia singleton del Cerebro Conversacional
    
    Args:
        database_service: Servicio de base de datos (solo primera vez)
        
    Returns:
        ConversationalBrain instance
    """
    global _conversational_brain
    
    if _conversational_brain is None:
        _conversational_brain = ConversationalBrain(database_service=database_service)
        logger.info("🧠 Conversational Brain singleton creado")
    
    return _conversational_brain
