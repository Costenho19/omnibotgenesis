"""
OMNIX V7.0 - OptimizationPort Tests
====================================
Unit tests for OptimizationPort and OptimizationAdapter.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

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
from src.omnix.infrastructure.adapters.optimization_adapter import OptimizationAdapter


class TestOptimizationEnums:
    """Test optimization-related enums."""
    
    def test_optimization_objectives(self):
        assert OptimizationObjective.SHARPE_RATIO.value == "sharpe_ratio"
        assert OptimizationObjective.MAX_RETURN.value == "max_return"
        assert OptimizationObjective.MIN_DRAWDOWN.value == "min_drawdown"
        assert OptimizationObjective.WIN_RATE.value == "win_rate"
    
    def test_optimization_statuses(self):
        assert OptimizationStatus.PENDING.value == "pending"
        assert OptimizationStatus.RUNNING.value == "running"
        assert OptimizationStatus.COMPLETED.value == "completed"
        assert OptimizationStatus.FAILED.value == "failed"
    
    def test_weight_categories(self):
        assert WeightCategory.SIGNAL_STRENGTH.value == "signal_strength"
        assert WeightCategory.RISK_FACTOR.value == "risk_factor"
        assert WeightCategory.POSITION_SIZE.value == "position_size"


class TestOptimizationResult:
    """Test OptimizationResult DTO."""
    
    def test_successful_result(self):
        result = OptimizationResult(
            run_id="OPT001",
            status=OptimizationStatus.COMPLETED,
            objective=OptimizationObjective.SHARPE_RATIO,
            best_score=1.85,
            optimized_params={'risk_factor': 0.7},
            improvement_pct=15.5,
            iterations_completed=100,
            backtest_metrics={'return': 0.25},
            validation_metrics={'return': 0.22},
            started_at=datetime.now()
        )
        
        assert result.is_success is True
    
    def test_failed_result(self):
        result = OptimizationResult(
            run_id="OPT002",
            status=OptimizationStatus.FAILED,
            objective=OptimizationObjective.MAX_RETURN,
            best_score=0,
            optimized_params={},
            improvement_pct=0,
            iterations_completed=10,
            backtest_metrics={},
            validation_metrics={},
            started_at=datetime.now(),
            error_message="Convergence failed"
        )
        
        assert result.is_success is False
    
    def test_negative_improvement_not_success(self):
        result = OptimizationResult(
            run_id="OPT003",
            status=OptimizationStatus.COMPLETED,
            objective=OptimizationObjective.SHARPE_RATIO,
            best_score=0.5,
            optimized_params={},
            improvement_pct=-5.0,
            iterations_completed=50,
            backtest_metrics={},
            validation_metrics={},
            started_at=datetime.now()
        )
        
        assert result.is_success is False


class TestWeightSet:
    """Test WeightSet DTO."""
    
    def test_weight_set_creation(self):
        weight_set = WeightSet(
            category=WeightCategory.SIGNAL_STRENGTH,
            weights={'rsi': 1.2, 'macd': 0.8, 'volume': 1.0},
            version=5,
            score=0.75
        )
        
        assert weight_set.category == WeightCategory.SIGNAL_STRENGTH
        assert weight_set.version == 5
    
    def test_get_weight(self):
        weight_set = WeightSet(
            category=WeightCategory.RISK_FACTOR,
            weights={'volatility': 0.6, 'correlation': 0.8},
            version=1,
            score=0.5
        )
        
        assert weight_set.get_weight('volatility') == 0.6
        assert weight_set.get_weight('missing', 1.0) == 1.0


class TestPerformanceForecast:
    """Test PerformanceForecast DTO."""
    
    def test_favorable_forecast(self):
        forecast = PerformanceForecast(
            forecast_period_days=30,
            expected_return_pct=8.5,
            expected_sharpe=1.5,
            expected_win_rate=0.58,
            confidence_level=0.72,
            risk_of_drawdown_pct=12.0
        )
        
        assert forecast.is_favorable is True
    
    def test_unfavorable_forecast(self):
        forecast = PerformanceForecast(
            forecast_period_days=30,
            expected_return_pct=-2.0,
            expected_sharpe=0.3,
            expected_win_rate=0.45,
            confidence_level=0.4,
            risk_of_drawdown_pct=25.0
        )
        
        assert forecast.is_favorable is False


class TestOptimizationAdapter:
    """Test OptimizationAdapter implementation."""
    
    def test_adapter_initialization(self):
        adapter = OptimizationAdapter()
        
        assert adapter._auto_optimizer is None
        assert adapter._adaptive_weights is None
        assert adapter._ml_module is None
        assert adapter._performance_analyzer is None
        assert adapter._initialized is False
    
    def test_adapter_with_injected_services(self):
        mock_optimizer = Mock()
        mock_weights = Mock()
        
        adapter = OptimizationAdapter(
            auto_optimizer=mock_optimizer,
            adaptive_weights=mock_weights
        )
        
        assert adapter._auto_optimizer == mock_optimizer
        assert adapter._adaptive_weights == mock_weights
    
    def test_objective_mapping(self):
        adapter = OptimizationAdapter()
        
        assert adapter._map_objective("sharpe_ratio") == OptimizationObjective.SHARPE_RATIO
        assert adapter._map_objective("max_return") == OptimizationObjective.MAX_RETURN
        assert adapter._map_objective("win_rate") == OptimizationObjective.WIN_RATE
    
    def test_status_mapping(self):
        adapter = OptimizationAdapter()
        
        assert adapter._map_status("pending") == OptimizationStatus.PENDING
        assert adapter._map_status("running") == OptimizationStatus.RUNNING
        assert adapter._map_status("completed") == OptimizationStatus.COMPLETED
    
    def test_weight_category_mapping(self):
        adapter = OptimizationAdapter()
        
        assert adapter._map_weight_category("signal_strength") == WeightCategory.SIGNAL_STRENGTH
        assert adapter._map_weight_category("risk_factor") == WeightCategory.RISK_FACTOR
        assert adapter._map_weight_category("position_size") == WeightCategory.POSITION_SIZE
    
    def test_health_check_no_services(self):
        adapter = OptimizationAdapter()
        health = adapter.health_check()
        
        assert 'healthy' in health
        assert 'adapter' in health
        assert health['adapter'] == 'OptimizationAdapter'
        assert 'components' in health
    
    def test_run_optimization(self):
        adapter = OptimizationAdapter()
        
        config = OptimizationConfig(
            objective=OptimizationObjective.SHARPE_RATIO,
            parameters_to_optimize=['risk_factor', 'position_size']
        )
        
        result = adapter.run_optimization(config)
        
        assert isinstance(result, OptimizationResult)
        assert result.run_id is not None
    
    def test_get_performance_forecast_fallback(self):
        adapter = OptimizationAdapter()
        
        result = adapter.get_performance_forecast(30)
        
        assert isinstance(result, PerformanceForecast)
        assert result.forecast_period_days == 30
    
    def test_update_adaptive_weights(self):
        adapter = OptimizationAdapter()
        
        weight_set = WeightSet(
            category=WeightCategory.CONFIDENCE,
            weights={'high': 1.5, 'medium': 1.0, 'low': 0.5},
            version=1,
            score=0.8
        )
        
        result = adapter.update_adaptive_weights(weight_set)
        
        assert result is True
        assert len(adapter._weight_sets) > 0


class TestOptimizationPortProtocol:
    """Test that OptimizationAdapter implements OptimizationPort protocol."""
    
    def test_adapter_has_required_methods(self):
        adapter = OptimizationAdapter()
        
        required_methods = [
            'run_optimization',
            'get_optimization_status',
            'cancel_optimization',
            'apply_optimization_result',
            'get_adaptive_weights',
            'update_adaptive_weights',
            'get_performance_forecast',
            'run_sensitivity_analysis',
            'get_learning_progress',
            'trigger_retraining',
            'get_parameter_recommendations',
            'health_check',
        ]
        
        for method_name in required_methods:
            assert hasattr(adapter, method_name), f"Missing method: {method_name}"
            assert callable(getattr(adapter, method_name)), f"Not callable: {method_name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
