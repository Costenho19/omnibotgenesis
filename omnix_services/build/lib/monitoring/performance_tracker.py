"""
OMNIX V6.0 ULTRA - Advanced Performance Tracker
Sistema de métricas detalladas para OMNIX
"""

import logging
import time
from collections import defaultdict, deque
from datetime import datetime

logger = logging.getLogger(__name__)


class AdvancedPerformanceTracker:
    """Sistema de métricas detalladas para OMNIX - IMPLEMENTADO AHORA"""
    
    def __init__(self):
        self.metrics = {
            'function_performance': defaultdict(list),
            'response_times': deque(maxlen=1000),  
            'prediction_accuracy': defaultdict(list),
            'user_satisfaction': defaultdict(list),
            'system_resources': deque(maxlen=100),
            'trading_success': defaultdict(list),
            'error_rates': defaultdict(int),
            'daily_stats': {},
            'real_time_metrics': {}
        }
        self.start_time = time.time()
        self.total_interactions = 0
        self.successful_predictions = 0
        self.failed_predictions = 0
        
        logger.info("📊 SISTEMA MÉTRICAS AVANZADAS ACTIVADO - Tracking iniciado")
    
    def track_function_performance(self, func_name: str, execution_time: float, success: bool, details: dict = None):
        """Track rendimiento de funciones críticas"""
        timestamp = datetime.now()
        
        performance_data = {
            'timestamp': timestamp,
            'execution_time': execution_time,
            'success': success,
            'details': details or {},
            'memory_usage': self._get_memory_usage(),
            'cpu_usage': self._get_cpu_usage()
        }
        
        self.metrics['function_performance'][func_name].append(performance_data)
        
        # Log si es crítico (muy lento o falló)
        if execution_time > 5.0 or not success:
            logger.warning(f"⚠️ PERFORMANCE: {func_name} - {execution_time:.2f}s - {'✅' if success else '❌'}")
        
        return performance_data
    
    def track_trading_decision(self, decision_type: str, confidence: float, actual_result: float = None, profit_loss: float = None):
        """Track decisiones de trading y su éxito"""
        timestamp = datetime.now()
        
        trading_data = {
            'timestamp': timestamp,
            'decision_type': decision_type,  # 'buy', 'sell', 'hold'
            'confidence': confidence,
            'actual_result': actual_result,
            'profit_loss': profit_loss,
            'success': actual_result is not None and actual_result > 0 if decision_type in ['buy', 'sell'] else None
        }
        
        self.metrics['trading_success'][decision_type].append(trading_data)
        
        # Actualizar contadores de éxito
        if trading_data['success'] is not None:
            if trading_data['success']:
                self.successful_predictions += 1
                logger.info(f"✅ TRADING SUCCESS: {decision_type} - Profit: ${profit_loss:.2f}")
            else:
                self.failed_predictions += 1
                logger.warning(f"❌ TRADING FAIL: {decision_type} - Loss: ${profit_loss:.2f}")
    
    def track_user_interaction(self, user_id: int, response_time: float, user_rating: int = None, intent: str = None):
        """Track interacciones con usuarios"""
        timestamp = datetime.now()
        
        self.response_times.append(response_time)
        self.total_interactions += 1
        
        if user_rating:
            self.metrics['user_satisfaction'][user_id].append({
                'timestamp': timestamp,
                'rating': user_rating,
                'response_time': response_time,
                'intent': intent
            })
        
        # Alertas automáticas
        if response_time > 10.0:
            logger.warning(f"🐌 SLOW RESPONSE: {response_time:.2f}s para user {user_id}")
    
    def get_performance_summary(self) -> dict:
        """Obtener resumen completo de métricas"""
        current_time = time.time()
        uptime = current_time - self.start_time
        
        # Calcular promedios
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        # Accuracy de trading
        total_predictions = self.successful_predictions + self.failed_predictions
        accuracy_rate = (self.successful_predictions / total_predictions * 100) if total_predictions > 0 else 0
        
        # Top funciones más lentas
        slow_functions = {}
        for func_name, performances in self.metrics['function_performance'].items():
            if performances:
                avg_time = sum(p['execution_time'] for p in performances[-10:]) / len(performances[-10:])
                slow_functions[func_name] = avg_time
        
        slow_functions = dict(sorted(slow_functions.items(), key=lambda x: x[1], reverse=True)[:5])
        
        return {
            'system_uptime': f"{uptime/3600:.1f} horas",
            'total_interactions': self.total_interactions,
            'avg_response_time': f"{avg_response_time:.2f}s",
            'trading_accuracy': f"{accuracy_rate:.1f}%",
            'successful_predictions': self.successful_predictions,
            'failed_predictions': self.failed_predictions,
            'slow_functions': slow_functions,
            'memory_usage': f"{self._get_memory_usage():.1f} MB",
            'cpu_usage': f"{self._get_cpu_usage():.1f}%",
            'errors_today': sum(self.metrics['error_rates'].values()),
            'top_user_intents': self._get_top_intents()
        }
    
    def get_real_time_dashboard_data(self) -> dict:
        """Datos para dashboard en tiempo real"""
        recent_response_times = list(self.response_times)[-20:]  # Últimas 20
        
        return {
            'current_response_time': recent_response_times[-1] if recent_response_times else 0,
            'response_trend': recent_response_times,
            'active_functions': len(self.metrics['function_performance']),
            'system_health': self._calculate_system_health(),
            'live_memory': self._get_memory_usage(),
            'live_cpu': self._get_cpu_usage(),
            'predictions_today': self.successful_predictions + self.failed_predictions,
            'accuracy_trend': self._get_accuracy_trend()
        }
    
    def _get_memory_usage(self) -> float:
        """Obtener uso actual de memoria en MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except Exception:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """Obtener uso actual de CPU"""
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except Exception:
            return 0.0
    
    def _calculate_system_health(self) -> str:
        """Calcular salud general del sistema"""
        try:
            memory_ok = self._get_memory_usage() < 500  # Menos de 500MB
            cpu_ok = self._get_cpu_usage() < 80  # Menos de 80% CPU
            response_ok = (sum(list(self.response_times)[-10:]) / 10 if len(self.response_times) >= 10 else 0) < 3  # Menos de 3s promedio
            
            if memory_ok and cpu_ok and response_ok:
                return "🟢 EXCELENTE"
            elif memory_ok and cpu_ok:
                return "🟡 BUENO"
            else:
                return "🔴 NECESITA OPTIMIZACIÓN"
        except Exception:
            return "🟡 MIDIENDO"
    
    def _get_top_intents(self) -> dict:
        """Top intenciones de usuarios"""
        intents = defaultdict(int)
        for user_interactions in self.metrics['user_satisfaction'].values():
            for interaction in user_interactions:
                if interaction.get('intent'):
                    intents[interaction['intent']] += 1
        return dict(sorted(intents.items(), key=lambda x: x[1], reverse=True)[:3])
    
    def _get_accuracy_trend(self) -> list:
        """Tendencia de precisión últimas decisiones"""
        recent_decisions = []
        for decisions in self.metrics['trading_success'].values():
            recent_decisions.extend(decisions[-10:])  # Últimas 10 de cada tipo
        
        recent_decisions.sort(key=lambda x: x['timestamp'])
        return [1 if d.get('success', False) else 0 for d in recent_decisions[-10:]]
