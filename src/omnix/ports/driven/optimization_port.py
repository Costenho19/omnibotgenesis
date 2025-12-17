"""
OMNIX V7.0 - OptimizationPort Protocol
=======================================
Port for system optimization and adaptive learning.

Wraps legacy services:
- auto_optimizer.py
- adaptive_weights.py
- ml_module.py
- performance_analyzer.py

Feature flag: USE_OPTIMIZATION_PORT
"""

from typing import Protocol, Optional, List, Dict, Any, runtime_checkable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class OptimizationObjective(Enum):
    """Optimization objectives."""
    SHARPE_RATIO = "sharpe_ratio"
    SORTINO_RATIO = "sortino_ratio"
    MAX_RETURN = "max_return"
    MIN_DRAWDOWN = "min_drawdown"
    WIN_RATE = "win_rate"
    PROFIT_FACTOR = "profit_factor"
    RISK_ADJUSTED = "risk_adjusted"


class OptimizationStatus(Enum):
    """Optimization run status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WeightCategory(Enum):
    """Categories for adaptive weights."""
    SIGNAL_STRENGTH = "signal_strength"
    RISK_FACTOR = "risk_factor"
    ENTRY_TIMING = "entry_timing"
    EXIT_TIMING = "exit_timing"
    POSITION_SIZE = "position_size"
    CONFIDENCE = "confidence"


@dataclass
class OptimizationConfig:
    """Configuration for optimization run."""
    objective: OptimizationObjective
    parameters_to_optimize: List[str]
    constraints: Dict[str, Any] = field(default_factory=dict)
    max_iterations: int = 100
    convergence_threshold: float = 0.001
    use_ml: bool = True
    backtest_period_days: int = 90
    validation_period_days: int = 30
    cross_validation_folds: int = 5


@dataclass
class OptimizationResult:
    """Result of optimization run."""
    run_id: str
    status: OptimizationStatus
    objective: OptimizationObjective
    best_score: float
    optimized_params: Dict[str, Any]
    improvement_pct: float
    iterations_completed: int
    backtest_metrics: Dict[str, float]
    validation_metrics: Dict[str, float]
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    @property
    def is_success(self) -> bool:
        """Check if optimization completed successfully."""
        return self.status == OptimizationStatus.COMPLETED and self.improvement_pct > 0


@dataclass
class WeightSet:
    """Set of adaptive weights."""
    category: WeightCategory
    weights: Dict[str, float]
    version: int
    score: float
    last_updated: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    
    def get_weight(self, key: str, default: float = 1.0) -> float:
        """Get a specific weight."""
        return self.weights.get(key, default)


@dataclass
class PerformanceForecast:
    """Performance forecast based on current parameters."""
    forecast_period_days: int
    expected_return_pct: float
    expected_sharpe: float
    expected_win_rate: float
    confidence_level: float
    risk_of_drawdown_pct: float
    scenarios: Dict[str, Dict[str, float]] = field(default_factory=dict)
    assumptions: List[str] = field(default_factory=list)
    
    @property
    def is_favorable(self) -> bool:
        """Check if forecast is favorable."""
        return (
            self.expected_return_pct > 0 and
            self.expected_win_rate > 0.5 and
            self.confidence_level > 0.6
        )


@dataclass
class ParameterSensitivity:
    """Sensitivity analysis for a parameter."""
    parameter_name: str
    current_value: float
    optimal_value: float
    sensitivity_score: float  # How much score changes per unit change
    impact_on_objective: str  # 'positive', 'negative', 'neutral'
    recommended_range: tuple[float, float] = (0.0, 1.0)


@dataclass
class LearningProgress:
    """Progress of ML learning."""
    model_name: str
    training_samples: int
    validation_accuracy: float
    last_retrained: datetime
    next_retrain_scheduled: Optional[datetime] = None
    feature_importance: Dict[str, float] = field(default_factory=dict)
    is_ready: bool = True


@runtime_checkable
class OptimizationPort(Protocol):
    """
    Port for system optimization and adaptive learning.
    
    Provides:
    - Parameter optimization
    - Adaptive weight management
    - ML model training
    - Performance forecasting
    """
    
    def run_optimization(
        self,
        config: OptimizationConfig
    ) -> OptimizationResult:
        """
        Run parameter optimization.
        
        Args:
            config: Optimization configuration
            
        Returns:
            Optimization result
        """
        ...
    
    def get_optimization_status(
        self,
        run_id: str
    ) -> OptimizationResult:
        """
        Get status of optimization run.
        
        Args:
            run_id: Run ID
            
        Returns:
            Optimization result
        """
        ...
    
    def cancel_optimization(
        self,
        run_id: str
    ) -> bool:
        """
        Cancel running optimization.
        
        Args:
            run_id: Run ID to cancel
            
        Returns:
            True if cancelled
        """
        ...
    
    def apply_optimization_result(
        self,
        result: OptimizationResult
    ) -> bool:
        """
        Apply optimization result to system.
        
        Args:
            result: Result to apply
            
        Returns:
            True if applied
        """
        ...
    
    def get_adaptive_weights(
        self,
        category: Optional[WeightCategory] = None
    ) -> List[WeightSet]:
        """
        Get current adaptive weights.
        
        Args:
            category: Filter by category
            
        Returns:
            List of weight sets
        """
        ...
    
    def update_adaptive_weights(
        self,
        weight_set: WeightSet
    ) -> bool:
        """
        Update adaptive weights.
        
        Args:
            weight_set: New weights
            
        Returns:
            True if updated
        """
        ...
    
    def get_performance_forecast(
        self,
        horizon_days: int = 30
    ) -> PerformanceForecast:
        """
        Get performance forecast.
        
        Args:
            horizon_days: Forecast horizon
            
        Returns:
            Performance forecast
        """
        ...
    
    def run_sensitivity_analysis(
        self,
        parameters: Optional[List[str]] = None
    ) -> List[ParameterSensitivity]:
        """
        Run parameter sensitivity analysis.
        
        Args:
            parameters: Parameters to analyze
            
        Returns:
            Sensitivity results
        """
        ...
    
    def get_learning_progress(self) -> List[LearningProgress]:
        """
        Get ML learning progress.
        
        Returns:
            Learning progress for each model
        """
        ...
    
    def trigger_retraining(
        self,
        model_name: Optional[str] = None
    ) -> bool:
        """
        Trigger ML model retraining.
        
        Args:
            model_name: Specific model or all
            
        Returns:
            True if triggered
        """
        ...
    
    def get_parameter_recommendations(self) -> Dict[str, Any]:
        """
        Get parameter recommendations based on recent performance.
        
        Returns:
            Recommended parameter changes
        """
        ...
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check health of optimization services.
        
        Returns:
            Health status dictionary
        """
        ...
