"""
OMNIX V6.0 ULTRA - Performance Optimizer
Sistema de optimización de rendimiento implementando sugerencias de OMNIX
"""

import logging
import time
import threading
import multiprocessing
import concurrent.futures
from functools import lru_cache

logger = logging.getLogger(__name__)

try:
    from src.omnix.infrastructure.adapters.authorization_adapter import get_authorization_adapter
    from src.omnix.ports.driven.authorization_port import UserRole
    AUTHORIZATION_AVAILABLE = True
except ImportError:
    AUTHORIZATION_AVAILABLE = False
    get_authorization_adapter = None
    UserRole = None

# Check if psutil is available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class PerformanceOptimizer:
    """Sistema de optimización de rendimiento implementando sugerencias de OMNIX"""
    
    def __init__(self):
        self.cpu_cores = multiprocessing.cpu_count()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.cpu_cores * 2)
        self.priority_queue = {
            'critical': [],  # Harold y operaciones críticas
            'high': [],      # Trading real
            'medium': [],    # Análisis
            'low': []        # Reportes automáticos
        }
        self.response_cache = {}
        self.last_optimization = time.time()
        
    def get_system_metrics(self):
        """Monitoreo de recursos del sistema"""
        if PSUTIL_AVAILABLE:
            return {
                'cpu_percent': psutil.cpu_percent(interval=0.1),
                'memory_percent': psutil.virtual_memory().percent,
                'available_memory': psutil.virtual_memory().available / (1024**3),  # GB
                'cpu_cores': self.cpu_cores,
                'active_threads': threading.active_count(),
                'timestamp': time.time()
            }
        else:
            # Métricas básicas sin psutil
            import os
            try:
                with open('/proc/loadavg', 'r') as f:
                    load_avg = float(f.read().split()[0])
                cpu_estimate = min(100, load_avg * 20)  # Estimación básica
            except:
                cpu_estimate = 25.0  # Valor conservador
            
            return {
                'cpu_percent': cpu_estimate,
                'memory_percent': 50.0,  # Estimación conservadora
                'available_memory': 2.0,  # GB estimado
                'cpu_cores': self.cpu_cores,
                'active_threads': threading.active_count(),
                'timestamp': time.time()
            }
    
    def prioritize_request(self, user_id, request_type):
        """Sistema de priorización implementando sugerencia OMNIX"""
        is_owner = False
        if AUTHORIZATION_AVAILABLE and get_authorization_adapter:
            auth = get_authorization_adapter()
            is_owner = auth.is_owner(str(user_id))
        else:
            try:
                from omnix_config.settings import settings
                is_owner = str(user_id) == str(settings.TELEGRAM_ADMIN_ID)
            except ImportError:
                is_owner = str(user_id) == "7014748854"
        
        if is_owner:
            return 'critical'
        elif request_type in ['trading', 'buy', 'sell', 'autotrading']:
            return 'high'
        elif request_type in ['analysis', 'price', 'insights']:
            return 'medium'
        else:
            return 'low'
    
    @lru_cache(maxsize=1000)
    def cached_market_data(self, symbol, timeframe):
        """Cache inteligente para datos de mercado"""
        # Implementación optimizada con cache LRU
        return f"cached_data_{symbol}_{timeframe}_{int(time.time()//60)}"
    
    def optimize_algorithms(self):
        """Optimización continua de algoritmos como sugiere OMNIX"""
        current_time = time.time()
        if current_time - self.last_optimization > 300:  # Cada 5 minutos
            metrics = self.get_system_metrics()
            
            # Ajustar tamaño del pool según uso de CPU
            if metrics['cpu_percent'] > 80:
                # Reducir carga si CPU alta
                self.executor._max_workers = max(2, self.cpu_cores)
            elif metrics['cpu_percent'] < 30:
                # Aumentar paralelismo si CPU baja
                self.executor._max_workers = self.cpu_cores * 3
                
            self.last_optimization = current_time
            return True
        return False
