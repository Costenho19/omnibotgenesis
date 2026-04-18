"""
OMNIX Optimized Concurrency Manager
===================================
Sistema de gestión inteligente de threads y concurrencia con priorización.
Optimiza ejecución paralela de tareas según criticidad.
"""

import logging
import time
import threading
import concurrent.futures
import multiprocessing

logger = logging.getLogger(__name__)


class OptimizedConcurrencyManager:
    """Gestión inteligente de threads y concurrencia - IMPLEMENTADO AHORA"""
    
    def __init__(self, max_workers: int = None, performance_tracker=None):
        # Auto-detectar cores disponibles
        self.available_cores = multiprocessing.cpu_count()
        self.optimal_workers = min(max_workers or (self.available_cores * 2), 16)
        
        # Thread pool para tareas críticas (Harold priority)
        self.critical_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=2, thread_name_prefix="OMNIX-Critical"
        )
        
        # Thread pool para tareas normales
        self.normal_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.optimal_workers, thread_name_prefix="OMNIX-Normal"
        )
        
        # Thread pool para tareas de background
        self.background_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=4, thread_name_prefix="OMNIX-Background"
        )
        
        # Contadores de rendimiento
        self.critical_tasks = 0
        self.normal_tasks = 0
        self.background_tasks = 0
        self.completed_tasks = 0
        
        # Optional performance tracker
        self.performance_tracker = performance_tracker
        
        logger.info(f"🧵 CONCURRENCIA OPTIMIZADA: {self.optimal_workers} workers, {self.available_cores} cores detectados")
    
    def execute_critical(self, func, *args, **kwargs):
        """Ejecutar tarea crítica (Harold, trading real)"""
        self.critical_tasks += 1
        future = self.critical_executor.submit(self._track_execution, func, *args, **kwargs)
        logger.debug(f"🔥 CRITICAL TASK: {func.__name__} - Total críticas: {self.critical_tasks}")
        return future
    
    def execute_normal(self, func, *args, **kwargs):
        """Ejecutar tarea normal (usuarios regulares)"""
        self.normal_tasks += 1
        future = self.normal_executor.submit(self._track_execution, func, *args, **kwargs)
        logger.debug(f"⚡ NORMAL TASK: {func.__name__} - Total normales: {self.normal_tasks}")
        return future
    
    def execute_background(self, func, *args, **kwargs):
        """Ejecutar tarea background (limpieza, métricas)"""
        self.background_tasks += 1
        future = self.background_executor.submit(self._track_execution, func, *args, **kwargs)
        logger.debug(f"🔄 BACKGROUND TASK: {func.__name__} - Total background: {self.background_tasks}")
        return future
    
    def _track_execution(self, func, *args, **kwargs):
        """Wrapper para tracking de ejecución"""
        start_time = time.time()
        thread_name = threading.current_thread().name
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            self.completed_tasks += 1
            
            # Track en performance tracker si está disponible
            if self.performance_tracker:
                self.performance_tracker.track_function_performance(
                    f"concurrent_{func.__name__}",
                    execution_time,
                    True,
                    {'thread': thread_name, 'args_count': len(args)}
                )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Error en {func.__name__} ({thread_name}): {e}")
            
            # Track error si performance tracker disponible
            if self.performance_tracker:
                self.performance_tracker.track_function_performance(
                    f"concurrent_{func.__name__}",
                    execution_time,
                    False,
                    {'thread': thread_name, 'error': str(e)}
                )
            
            raise
    
    def get_status(self) -> dict:
        """Estado actual de concurrencia"""
        return {
            'available_cores': self.available_cores,
            'optimal_workers': self.optimal_workers,
            'critical_tasks': self.critical_tasks,
            'normal_tasks': self.normal_tasks,
            'background_tasks': self.background_tasks,
            'completed_tasks': self.completed_tasks,
            'total_submitted': self.critical_tasks + self.normal_tasks + self.background_tasks,
            'success_rate': f"{(self.completed_tasks / max(1, self.critical_tasks + self.normal_tasks + self.background_tasks) * 100):.1f}%"
        }
    
    def shutdown_graceful(self):
        """Cierre limpio de todos los executors"""
        logger.info("🛑 Cerrando threads concurrencia...")
        self.critical_executor.shutdown(wait=True)
        self.normal_executor.shutdown(wait=True) 
        self.background_executor.shutdown(wait=True)
        logger.info("✅ Concurrencia cerrada exitosamente")
