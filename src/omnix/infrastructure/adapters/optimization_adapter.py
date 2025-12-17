"""
OMNIX V7.0 - OptimizationAdapter
=================================
Adapter implementing OptimizationPort by wrapping legacy optimization services.

Wrapped Legacy Services:
- AutoOptimizer (omnix_services/optimization/)
- AdaptiveWeights (omnix_services/optimization/)
- PerformanceOptimizer (omnix_services/optimization/)
- MLModule (omnix_services/ml/)

Feature flag: USE_OPTIMIZATION_PORT
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from src.omnix.ports.driven.optimization_port import (
    OptimizationPort,
    OptimizationConfig,
    OptimizationResult,
    OptimizationStatus,
    OptimizationObjective,
    WeightSet,
    WeightCategory,
    PerformanceForecast,
    ParameterSensitivity,
    LearningProgress,
)

logger = logging.getLogger(__name__)


class NullAdaptiveWeights:
    """Null object fallback when AdaptiveWeights is not available."""
    
    def get_all(self, category: str = None) -> list:
        return []
    
    def update(self, data: dict) -> bool:
        return True
    
    def get_current_weights(self) -> dict:
        return {}


class OptimizationAdapter:
    """
    Adapter wrapping legacy optimization services.
    
    Implements OptimizationPort protocol with lazy loading
    and graceful degradation.
    """
    
    def __init__(
        self,
        auto_optimizer: Any = None,
        adaptive_weights: Any = None,
        performance_optimizer: Any = None,
        ml_module: Any = None
    ):
        self._auto_optimizer = auto_optimizer
        self._adaptive_weights = adaptive_weights
        self._performance_optimizer = performance_optimizer
        self._ml_module = ml_module
        self._initialized = False
        self._active_runs: Dict[str, OptimizationResult] = {}
        self._weight_sets: List[WeightSet] = []
        logger.info("OptimizationAdapter: Initialized with lazy-loaded services")
    
    def _ensure_services(self) -> None:
        """Lazy load services if not initialized."""
        if self._initialized:
            return
        
        if self._auto_optimizer is None:
            try:
                from omnix_services.optimization.auto_optimizer import AutoOptimizer
                self._auto_optimizer = AutoOptimizer()
            except ImportError:
                logger.warning("OptimizationAdapter: AutoOptimizer not available")
        
        if self._adaptive_weights is None:
            try:
                from omnix_services.optimization.adaptive_weights import AdaptiveWeights
                if hasattr(AdaptiveWeights, 'get_instance'):
                    self._adaptive_weights = AdaptiveWeights.get_instance()
                else:
                    import inspect
                    sig = inspect.signature(AdaptiveWeights.__init__)
                    params = [p for p in sig.parameters.keys() if p != 'self']
                    if params:
                        logger.info(f"OptimizationAdapter: AdaptiveWeights requires params: {params}, using NullAdaptiveWeights")
                        self._adaptive_weights = NullAdaptiveWeights()
                    else:
                        self._adaptive_weights = AdaptiveWeights()
            except (ImportError, TypeError, Exception) as e:
                logger.warning(f"OptimizationAdapter: AdaptiveWeights not available: {e}")
                self._adaptive_weights = NullAdaptiveWeights()
        
        if self._ml_module is None:
            try:
                from omnix_services.ml.ml_module import MLModule
                self._ml_module = MLModule()
            except ImportError:
                logger.warning("OptimizationAdapter: MLModule not available")
        
        if self._performance_optimizer is None:
            try:
                from omnix_services.optimization.performance_optimizer import PerformanceOptimizer
                self._performance_optimizer = PerformanceOptimizer()
            except ImportError:
                logger.warning("OptimizationAdapter: PerformanceOptimizer not available")
        
        self._initialized = True
    
    def _map_objective(self, obj_str: str) -> OptimizationObjective:
        """Map string to OptimizationObjective enum."""
        obj_lower = obj_str.lower()
        mapping = {
            "sharpe_ratio": OptimizationObjective.SHARPE_RATIO,
            "sortino_ratio": OptimizationObjective.SORTINO_RATIO,
            "max_return": OptimizationObjective.MAX_RETURN,
            "min_drawdown": OptimizationObjective.MIN_DRAWDOWN,
            "win_rate": OptimizationObjective.WIN_RATE,
            "profit_factor": OptimizationObjective.PROFIT_FACTOR,
            "risk_adjusted": OptimizationObjective.RISK_ADJUSTED,
        }
        return mapping.get(obj_lower, OptimizationObjective.SHARPE_RATIO)
    
    def _map_status(self, status_str: str) -> OptimizationStatus:
        """Map string to OptimizationStatus enum."""
        status_lower = status_str.lower()
        mapping = {
            "pending": OptimizationStatus.PENDING,
            "running": OptimizationStatus.RUNNING,
            "completed": OptimizationStatus.COMPLETED,
            "failed": OptimizationStatus.FAILED,
            "cancelled": OptimizationStatus.CANCELLED,
        }
        return mapping.get(status_lower, OptimizationStatus.PENDING)
    
    def _map_weight_category(self, cat_str: str) -> WeightCategory:
        """Map string to WeightCategory enum."""
        cat_lower = cat_str.lower()
        mapping = {
            "signal_strength": WeightCategory.SIGNAL_STRENGTH,
            "risk_factor": WeightCategory.RISK_FACTOR,
            "entry_timing": WeightCategory.ENTRY_TIMING,
            "exit_timing": WeightCategory.EXIT_TIMING,
            "position_size": WeightCategory.POSITION_SIZE,
            "confidence": WeightCategory.CONFIDENCE,
        }
        return mapping.get(cat_lower, WeightCategory.SIGNAL_STRENGTH)
    
    def run_optimization(
        self,
        config: OptimizationConfig
    ) -> OptimizationResult:
        """Run parameter optimization."""
        self._ensure_services()
        
        run_id = str(uuid.uuid4())[:8]
        now = datetime.now()
        
        result = OptimizationResult(
            run_id=run_id,
            status=OptimizationStatus.PENDING,
            objective=config.objective,
            best_score=0,
            optimized_params={},
            improvement_pct=0,
            iterations_completed=0,
            backtest_metrics={},
            validation_metrics={},
            started_at=now
        )
        
        try:
            if self._auto_optimizer and hasattr(self._auto_optimizer, 'optimize'):
                opt_result = self._auto_optimizer.optimize({
                    'objective': config.objective.value,
                    'parameters': config.parameters_to_optimize,
                    'constraints': config.constraints,
                    'max_iterations': config.max_iterations,
                    'backtest_days': config.backtest_period_days
                })
                
                if isinstance(opt_result, dict):
                    result.status = self._map_status(opt_result.get('status', 'completed'))
                    result.best_score = opt_result.get('best_score', 0)
                    result.optimized_params = opt_result.get('params', {})
                    result.improvement_pct = opt_result.get('improvement', 0)
                    result.iterations_completed = opt_result.get('iterations', 0)
                    result.backtest_metrics = opt_result.get('backtest', {})
                    result.validation_metrics = opt_result.get('validation', {})
                    result.completed_at = datetime.now()
        except Exception as e:
            logger.error(f"OptimizationAdapter: run_optimization error: {e}")
            result.status = OptimizationStatus.FAILED
            result.error_message = str(e)
        
        self._active_runs[run_id] = result
        return result
    
    def get_optimization_status(
        self,
        run_id: str
    ) -> OptimizationResult:
        """Get status of optimization run."""
        if run_id in self._active_runs:
            return self._active_runs[run_id]
        
        return OptimizationResult(
            run_id=run_id,
            status=OptimizationStatus.FAILED,
            objective=OptimizationObjective.SHARPE_RATIO,
            best_score=0,
            optimized_params={},
            improvement_pct=0,
            iterations_completed=0,
            backtest_metrics={},
            validation_metrics={},
            started_at=datetime.now(),
            error_message="Run not found"
        )
    
    def cancel_optimization(
        self,
        run_id: str
    ) -> bool:
        """Cancel running optimization."""
        self._ensure_services()
        
        try:
            if self._auto_optimizer and hasattr(self._auto_optimizer, 'cancel'):
                result = self._auto_optimizer.cancel(run_id)
                if run_id in self._active_runs:
                    self._active_runs[run_id].status = OptimizationStatus.CANCELLED
                return bool(result)
        except Exception as e:
            logger.error(f"OptimizationAdapter: cancel_optimization error: {e}")
        
        return False
    
    def apply_optimization_result(
        self,
        result: OptimizationResult
    ) -> bool:
        """Apply optimization result to system."""
        self._ensure_services()
        
        try:
            if self._auto_optimizer and hasattr(self._auto_optimizer, 'apply'):
                return self._auto_optimizer.apply({
                    'run_id': result.run_id,
                    'params': result.optimized_params
                })
        except Exception as e:
            logger.error(f"OptimizationAdapter: apply_optimization_result error: {e}")
        
        return False
    
    def get_adaptive_weights(
        self,
        category: Optional[WeightCategory] = None
    ) -> List[WeightSet]:
        """Get current adaptive weights."""
        self._ensure_services()
        
        try:
            if self._adaptive_weights and hasattr(self._adaptive_weights, 'get_all'):
                result = self._adaptive_weights.get_all(
                    category.value if category else None
                )
                
                if isinstance(result, list):
                    weight_sets = []
                    for ws in result:
                        weight_sets.append(WeightSet(
                            category=self._map_weight_category(ws.get('category', 'signal_strength')),
                            weights=ws.get('weights', {}),
                            version=ws.get('version', 1),
                            score=ws.get('score', 0),
                            last_updated=ws.get('updated_at', datetime.now()),
                            is_active=ws.get('active', True)
                        ))
                    return weight_sets
        except Exception as e:
            logger.error(f"OptimizationAdapter: get_adaptive_weights error: {e}")
        
        return self._weight_sets
    
    def update_adaptive_weights(
        self,
        weight_set: WeightSet
    ) -> bool:
        """Update adaptive weights."""
        self._ensure_services()
        
        try:
            if self._adaptive_weights and hasattr(self._adaptive_weights, 'update'):
                result = self._adaptive_weights.update({
                    'category': weight_set.category.value,
                    'weights': weight_set.weights,
                    'version': weight_set.version
                })
                if result:
                    existing = [ws for ws in self._weight_sets if ws.category != weight_set.category]
                    existing.append(weight_set)
                    self._weight_sets = existing
                    return True
        except Exception as e:
            logger.error(f"OptimizationAdapter: update_adaptive_weights error: {e}")
        
        existing = [ws for ws in self._weight_sets if ws.category != weight_set.category]
        existing.append(weight_set)
        self._weight_sets = existing
        return True
    
    def get_performance_forecast(
        self,
        horizon_days: int = 30
    ) -> PerformanceForecast:
        """Get performance forecast."""
        self._ensure_services()
        
        try:
            if self._performance_optimizer and hasattr(self._performance_optimizer, 'forecast'):
                result = self._performance_optimizer.forecast(horizon_days)
                
                if isinstance(result, dict):
                    return PerformanceForecast(
                        forecast_period_days=horizon_days,
                        expected_return_pct=result.get('expected_return', 0),
                        expected_sharpe=result.get('sharpe', 0),
                        expected_win_rate=result.get('win_rate', 0.5),
                        confidence_level=result.get('confidence', 0.5),
                        risk_of_drawdown_pct=result.get('drawdown_risk', 0),
                        scenarios=result.get('scenarios', {}),
                        assumptions=result.get('assumptions', [])
                    )
        except Exception as e:
            logger.error(f"OptimizationAdapter: get_performance_forecast error: {e}")
        
        return PerformanceForecast(
            forecast_period_days=horizon_days,
            expected_return_pct=0,
            expected_sharpe=0,
            expected_win_rate=0.5,
            confidence_level=0.5,
            risk_of_drawdown_pct=0
        )
    
    def run_sensitivity_analysis(
        self,
        parameters: Optional[List[str]] = None
    ) -> List[ParameterSensitivity]:
        """Run parameter sensitivity analysis."""
        self._ensure_services()
        
        try:
            if self._auto_optimizer and hasattr(self._auto_optimizer, 'sensitivity_analysis'):
                result = self._auto_optimizer.sensitivity_analysis(parameters)
                
                if isinstance(result, list):
                    sensitivities = []
                    for item in result:
                        sensitivities.append(ParameterSensitivity(
                            parameter_name=item.get('name', ''),
                            current_value=item.get('current', 0),
                            optimal_value=item.get('optimal', 0),
                            sensitivity_score=item.get('sensitivity', 0),
                            impact_on_objective=item.get('impact', 'neutral'),
                            recommended_range=(
                                item.get('min', 0),
                                item.get('max', 1)
                            )
                        ))
                    return sensitivities
        except Exception as e:
            logger.error(f"OptimizationAdapter: run_sensitivity_analysis error: {e}")
        
        return []
    
    def get_learning_progress(self) -> List[LearningProgress]:
        """Get ML learning progress."""
        self._ensure_services()
        
        try:
            if self._ml_module and hasattr(self._ml_module, 'get_progress'):
                result = self._ml_module.get_progress()
                
                if isinstance(result, list):
                    progress = []
                    for item in result:
                        progress.append(LearningProgress(
                            model_name=item.get('name', ''),
                            training_samples=item.get('samples', 0),
                            validation_accuracy=item.get('accuracy', 0),
                            last_retrained=item.get('last_trained', datetime.now()),
                            next_retrain_scheduled=item.get('next_train'),
                            feature_importance=item.get('features', {}),
                            is_ready=item.get('ready', True)
                        ))
                    return progress
        except Exception as e:
            logger.error(f"OptimizationAdapter: get_learning_progress error: {e}")
        
        return []
    
    def trigger_retraining(
        self,
        model_name: Optional[str] = None
    ) -> bool:
        """Trigger ML model retraining."""
        self._ensure_services()
        
        try:
            if self._ml_module and hasattr(self._ml_module, 'retrain'):
                return self._ml_module.retrain(model_name)
        except Exception as e:
            logger.error(f"OptimizationAdapter: trigger_retraining error: {e}")
        
        return False
    
    def get_parameter_recommendations(self) -> Dict[str, Any]:
        """Get parameter recommendations based on recent performance."""
        self._ensure_services()
        
        try:
            if self._performance_optimizer and hasattr(self._performance_optimizer, 'recommend'):
                return self._performance_optimizer.recommend()
        except Exception as e:
            logger.error(f"OptimizationAdapter: get_parameter_recommendations error: {e}")
        
        return {
            'recommendations': [],
            'based_on_trades': 0,
            'confidence': 0
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of optimization services."""
        self._ensure_services()
        
        components = {
            'auto_optimizer': self._auto_optimizer is not None,
            'adaptive_weights': self._adaptive_weights is not None,
            'ml_module': self._ml_module is not None,
            'performance_optimizer': self._performance_optimizer is not None,
        }
        
        healthy_count = sum(1 for v in components.values() if v)
        
        return {
            'healthy': healthy_count >= 2,
            'adapter': 'OptimizationAdapter',
            'components': components,
            'healthy_count': healthy_count,
            'total_components': len(components),
            'active_runs': len(self._active_runs),
            'weight_sets': len(self._weight_sets),
            'timestamp': datetime.now().isoformat()
        }
