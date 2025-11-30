"""
🔧 STOCK AUTO-OPTIMIZER V6.2
Motor de optimización continua para estrategias de acciones
Algoritmo genético + A/B Testing + Auto-ajuste
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import random

logger = logging.getLogger(__name__)


class OptimizationType(Enum):
    GENETIC = "genetic"
    AB_TEST = "ab_test"
    BAYESIAN = "bayesian"
    GRID_SEARCH = "grid_search"


@dataclass
class ParameterConfig:
    name: str
    min_value: float
    max_value: float
    current_value: float
    step: float = 0.01
    optimization_priority: int = 1


@dataclass
class OptimizationResult:
    parameters: Dict[str, float]
    fitness_score: float
    sharpe_ratio: float
    win_rate: float
    max_drawdown: float
    total_trades: int
    improvement_pct: float
    timestamp: datetime


class StockAutoOptimizer:
    """
    Auto-Optimizador para Estrategias de Acciones
    
    Características:
    - Algoritmo Genético para búsqueda de parámetros óptimos
    - A/B Testing para validar mejoras
    - Optimización Bayesiana para eficiencia
    - Auto-ajuste basado en régimen de mercado
    
    Parámetros optimizables:
    - Lookback periods
    - Thresholds de señales
    - Stop loss / Take profit
    - Pesos de indicadores
    - Parámetros de Kalman/HMM
    """
    
    DEFAULT_PARAMS = {
        'lookback_short': ParameterConfig('lookback_short', 5, 30, 14, 1, 1),
        'lookback_long': ParameterConfig('lookback_long', 20, 120, 60, 5, 1),
        'signal_threshold': ParameterConfig('signal_threshold', 0.1, 0.5, 0.25, 0.05, 2),
        'stop_loss_pct': ParameterConfig('stop_loss_pct', 0.01, 0.10, 0.03, 0.005, 2),
        'take_profit_pct': ParameterConfig('take_profit_pct', 0.02, 0.20, 0.06, 0.01, 2),
        'rsi_oversold': ParameterConfig('rsi_oversold', 20, 40, 30, 2, 1),
        'rsi_overbought': ParameterConfig('rsi_overbought', 60, 80, 70, 2, 1),
        'kalman_process_noise': ParameterConfig('kalman_process_noise', 0.0001, 0.01, 0.001, 0.0005, 3),
        'monte_carlo_paths': ParameterConfig('monte_carlo_paths', 500, 5000, 2000, 500, 3),
        'weight_technical': ParameterConfig('weight_technical', 0.3, 0.7, 0.5, 0.05, 2),
        'weight_fundamental': ParameterConfig('weight_fundamental', 0.1, 0.4, 0.25, 0.05, 2),
    }
    
    GENETIC_CONFIG = {
        'population_size': 20,
        'generations': 50,
        'mutation_rate': 0.15,
        'crossover_rate': 0.7,
        'elite_count': 2,
        'tournament_size': 3
    }
    
    def __init__(
        self,
        strategy_engine=None,
        database_service=None,
        optimization_type: OptimizationType = OptimizationType.GENETIC
    ):
        self.strategy_engine = strategy_engine
        self.database_service = database_service
        self.optimization_type = optimization_type
        
        self.parameters = {k: v.current_value for k, v in self.DEFAULT_PARAMS.items()}
        self.param_configs = dict(self.DEFAULT_PARAMS)
        
        self.optimization_history = []
        self.best_result: Optional[OptimizationResult] = None
        self.current_generation = 0
        self.ab_tests = {}
        
        logger.info(f"🔧 Stock Auto-Optimizer V6.2 inicializado")
        logger.info(f"   📊 Tipo: {optimization_type.value}")
        logger.info(f"   🧬 Población: {self.GENETIC_CONFIG['population_size']}")
        logger.info(f"   🔢 Parámetros: {len(self.parameters)}")
    
    def optimize(
        self,
        historical_data: List[Dict],
        fitness_function: Optional[Callable] = None,
        generations: int = None
    ) -> OptimizationResult:
        """
        Ejecutar optimización de parámetros
        
        Args:
            historical_data: Datos históricos para backtesting
            fitness_function: Función de fitness personalizada
            generations: Número de generaciones (overrides config)
            
        Returns:
            OptimizationResult con mejores parámetros
        """
        try:
            if self.optimization_type == OptimizationType.GENETIC:
                return self._genetic_optimization(
                    historical_data,
                    fitness_function,
                    generations or self.GENETIC_CONFIG['generations']
                )
            elif self.optimization_type == OptimizationType.BAYESIAN:
                return self._bayesian_optimization(historical_data, fitness_function)
            else:
                return self._grid_search(historical_data, fitness_function)
                
        except Exception as e:
            logger.error(f"Error en optimización: {e}")
            return OptimizationResult(
                parameters=self.parameters,
                fitness_score=0,
                sharpe_ratio=0,
                win_rate=0,
                max_drawdown=0,
                total_trades=0,
                improvement_pct=0,
                timestamp=datetime.now()
            )
    
    def _genetic_optimization(
        self,
        data: List[Dict],
        fitness_fn: Optional[Callable],
        generations: int
    ) -> OptimizationResult:
        """Optimización por algoritmo genético"""
        logger.info(f"🧬 Iniciando optimización genética: {generations} generaciones")
        
        population = self._initialize_population()
        
        best_ever = None
        best_fitness = float('-inf')
        
        for gen in range(generations):
            self.current_generation = gen
            
            fitness_scores = []
            for individual in population:
                score = self._evaluate_fitness(individual, data, fitness_fn)
                fitness_scores.append((individual, score))
            
            fitness_scores.sort(key=lambda x: x[1], reverse=True)
            
            if fitness_scores[0][1] > best_fitness:
                best_fitness = fitness_scores[0][1]
                best_ever = fitness_scores[0][0].copy()
                logger.info(f"   Gen {gen}: Nuevo mejor fitness = {best_fitness:.4f}")
            
            elite = [fs[0] for fs in fitness_scores[:self.GENETIC_CONFIG['elite_count']]]
            
            new_population = elite.copy()
            
            while len(new_population) < self.GENETIC_CONFIG['population_size']:
                parent1 = self._tournament_select(fitness_scores)
                parent2 = self._tournament_select(fitness_scores)
                
                if random.random() < self.GENETIC_CONFIG['crossover_rate']:
                    child = self._crossover(parent1, parent2)
                else:
                    child = parent1.copy()
                
                child = self._mutate(child)
                new_population.append(child)
            
            population = new_population
        
        self.parameters = best_ever
        
        metrics = self._calculate_metrics(best_ever, data)
        
        result = OptimizationResult(
            parameters=best_ever,
            fitness_score=best_fitness,
            sharpe_ratio=metrics['sharpe'],
            win_rate=metrics['win_rate'],
            max_drawdown=metrics['max_drawdown'],
            total_trades=metrics['total_trades'],
            improvement_pct=metrics.get('improvement', 0),
            timestamp=datetime.now()
        )
        
        self.best_result = result
        self.optimization_history.append(result)
        
        logger.info(f"✅ Optimización completada: Fitness = {best_fitness:.4f}")
        
        return result
    
    def _initialize_population(self) -> List[Dict[str, float]]:
        """Inicializar población aleatoria"""
        population = []
        
        population.append(self.parameters.copy())
        
        for _ in range(self.GENETIC_CONFIG['population_size'] - 1):
            individual = {}
            for name, config in self.param_configs.items():
                value = random.uniform(config.min_value, config.max_value)
                value = round(value / config.step) * config.step
                individual[name] = value
            population.append(individual)
        
        return population
    
    def _evaluate_fitness(
        self,
        params: Dict[str, float],
        data: List[Dict],
        custom_fn: Optional[Callable]
    ) -> float:
        """Evaluar fitness de un conjunto de parámetros"""
        if custom_fn:
            return custom_fn(params, data)
        
        metrics = self._calculate_metrics(params, data)
        
        fitness = (
            metrics['sharpe'] * 0.3 +
            metrics['win_rate'] * 0.25 +
            (1 - metrics['max_drawdown']) * 0.25 +
            min(metrics['total_trades'] / 100, 1) * 0.1 +
            metrics.get('profit_factor', 1) * 0.1
        )
        
        return fitness
    
    def _calculate_metrics(self, params: Dict[str, float], data: List[Dict]) -> Dict:
        """Calcular métricas de rendimiento para parámetros"""
        if not data:
            return {
                'sharpe': 0,
                'win_rate': 0.5,
                'max_drawdown': 0.1,
                'total_trades': 0,
                'profit_factor': 1
            }
        
        closes = [d['close'] for d in data if 'close' in d]
        
        if len(closes) < 50:
            return {
                'sharpe': 0,
                'win_rate': 0.5,
                'max_drawdown': 0.1,
                'total_trades': 0,
                'profit_factor': 1
            }
        
        returns = np.diff(closes) / closes[:-1]
        
        lookback = int(params.get('lookback_short', 14))
        threshold = params.get('signal_threshold', 0.25)
        
        trades = []
        position = 0
        entry_price = 0
        
        for i in range(lookback, len(closes) - 1):
            window = closes[i-lookback:i]
            sma = np.mean(window)
            current = closes[i]
            
            signal = (current - sma) / sma
            
            if position == 0 and signal > threshold:
                position = 1
                entry_price = current
            elif position == 1 and signal < -threshold:
                pnl = (current - entry_price) / entry_price
                trades.append(pnl)
                position = 0
        
        if not trades:
            trades = [0]
        
        wins = sum(1 for t in trades if t > 0)
        win_rate = wins / len(trades) if trades else 0.5
        
        cumulative = np.cumsum(trades)
        peak = np.maximum.accumulate(cumulative)
        drawdown = peak - cumulative
        max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0.1
        
        avg_return = np.mean(trades)
        std_return = np.std(trades) if len(trades) > 1 else 0.01
        sharpe = (avg_return / std_return * np.sqrt(252)) if std_return > 0 else 0
        
        gross_profit = sum(t for t in trades if t > 0)
        gross_loss = abs(sum(t for t in trades if t < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 2
        
        return {
            'sharpe': np.clip(sharpe, -3, 3),
            'win_rate': win_rate,
            'max_drawdown': min(max_drawdown, 1),
            'total_trades': len(trades),
            'profit_factor': min(profit_factor, 5)
        }
    
    def _tournament_select(self, fitness_scores: List[Tuple]) -> Dict[str, float]:
        """Selección por torneo"""
        tournament = random.sample(fitness_scores, self.GENETIC_CONFIG['tournament_size'])
        winner = max(tournament, key=lambda x: x[1])
        return winner[0].copy()
    
    def _crossover(self, parent1: Dict, parent2: Dict) -> Dict:
        """Cruce de dos individuos"""
        child = {}
        for key in parent1.keys():
            if random.random() < 0.5:
                child[key] = parent1[key]
            else:
                child[key] = parent2[key]
        return child
    
    def _mutate(self, individual: Dict) -> Dict:
        """Mutación de un individuo"""
        mutated = individual.copy()
        
        for name, value in mutated.items():
            if random.random() < self.GENETIC_CONFIG['mutation_rate']:
                config = self.param_configs[name]
                
                mutation_range = (config.max_value - config.min_value) * 0.2
                mutation = random.gauss(0, mutation_range / 3)
                
                new_value = value + mutation
                new_value = np.clip(new_value, config.min_value, config.max_value)
                new_value = round(new_value / config.step) * config.step
                
                mutated[name] = new_value
        
        return mutated
    
    def _bayesian_optimization(
        self,
        data: List[Dict],
        fitness_fn: Optional[Callable]
    ) -> OptimizationResult:
        """Optimización bayesiana simplificada"""
        logger.info("📊 Iniciando optimización bayesiana")
        
        n_iterations = 30
        evaluated_points = []
        
        for _ in range(5):
            params = {}
            for name, config in self.param_configs.items():
                params[name] = random.uniform(config.min_value, config.max_value)
            
            score = self._evaluate_fitness(params, data, fitness_fn)
            evaluated_points.append((params, score))
        
        for _ in range(n_iterations - 5):
            best_idx = np.argmax([p[1] for p in evaluated_points])
            best_params = evaluated_points[best_idx][0]
            
            new_params = {}
            for name, value in best_params.items():
                config = self.param_configs[name]
                range_size = (config.max_value - config.min_value) * 0.1
                new_value = value + random.gauss(0, range_size)
                new_value = np.clip(new_value, config.min_value, config.max_value)
                new_params[name] = new_value
            
            score = self._evaluate_fitness(new_params, data, fitness_fn)
            evaluated_points.append((new_params, score))
        
        best_idx = np.argmax([p[1] for p in evaluated_points])
        best_params, best_score = evaluated_points[best_idx]
        
        self.parameters = best_params
        metrics = self._calculate_metrics(best_params, data)
        
        return OptimizationResult(
            parameters=best_params,
            fitness_score=best_score,
            sharpe_ratio=metrics['sharpe'],
            win_rate=metrics['win_rate'],
            max_drawdown=metrics['max_drawdown'],
            total_trades=metrics['total_trades'],
            improvement_pct=0,
            timestamp=datetime.now()
        )
    
    def _grid_search(
        self,
        data: List[Dict],
        fitness_fn: Optional[Callable]
    ) -> OptimizationResult:
        """Búsqueda en grid simplificada"""
        logger.info("🔍 Iniciando grid search")
        
        priority_params = sorted(
            self.param_configs.items(),
            key=lambda x: x[1].optimization_priority
        )[:3]
        
        best_params = self.parameters.copy()
        best_score = float('-inf')
        
        for name, config in priority_params:
            for value in np.arange(config.min_value, config.max_value, config.step * 5):
                test_params = best_params.copy()
                test_params[name] = value
                
                score = self._evaluate_fitness(test_params, data, fitness_fn)
                
                if score > best_score:
                    best_score = score
                    best_params = test_params.copy()
        
        self.parameters = best_params
        metrics = self._calculate_metrics(best_params, data)
        
        return OptimizationResult(
            parameters=best_params,
            fitness_score=best_score,
            sharpe_ratio=metrics['sharpe'],
            win_rate=metrics['win_rate'],
            max_drawdown=metrics['max_drawdown'],
            total_trades=metrics['total_trades'],
            improvement_pct=0,
            timestamp=datetime.now()
        )
    
    def create_ab_test(
        self,
        test_name: str,
        param_name: str,
        variant_value: float,
        duration_days: int = 7
    ) -> str:
        """Crear un A/B test para un parámetro"""
        test_id = f"ab_{test_name}_{datetime.now().strftime('%Y%m%d')}"
        
        self.ab_tests[test_id] = {
            'name': test_name,
            'param': param_name,
            'control_value': self.parameters[param_name],
            'variant_value': variant_value,
            'start_time': datetime.now(),
            'end_time': datetime.now() + timedelta(days=duration_days),
            'control_results': [],
            'variant_results': [],
            'status': 'active'
        }
        
        logger.info(f"🔬 A/B Test creado: {test_id}")
        return test_id
    
    def record_ab_result(self, test_id: str, is_variant: bool, result: float):
        """Registrar resultado de A/B test"""
        if test_id not in self.ab_tests:
            return
        
        test = self.ab_tests[test_id]
        
        if is_variant:
            test['variant_results'].append(result)
        else:
            test['control_results'].append(result)
    
    def evaluate_ab_test(self, test_id: str) -> Optional[Dict]:
        """Evaluar resultados de A/B test"""
        if test_id not in self.ab_tests:
            return None
        
        test = self.ab_tests[test_id]
        
        control = test['control_results']
        variant = test['variant_results']
        
        if len(control) < 10 or len(variant) < 10:
            return {'status': 'insufficient_data'}
        
        control_mean = np.mean(control)
        variant_mean = np.mean(variant)
        
        improvement = (variant_mean - control_mean) / abs(control_mean) if control_mean != 0 else 0
        
        pooled_std = np.sqrt(
            (np.var(control) + np.var(variant)) / 2
        )
        t_stat = (variant_mean - control_mean) / (pooled_std * np.sqrt(2/len(control)))
        
        significant = abs(t_stat) > 1.96
        
        return {
            'control_mean': control_mean,
            'variant_mean': variant_mean,
            'improvement': improvement,
            't_statistic': t_stat,
            'significant': significant,
            'recommendation': 'adopt_variant' if significant and improvement > 0 else 'keep_control'
        }
    
    def get_current_params(self) -> Dict[str, float]:
        """Obtener parámetros actuales"""
        return self.parameters.copy()
    
    def get_status(self) -> Dict:
        """Obtener estado del optimizador"""
        return {
            'type': self.optimization_type.value,
            'current_generation': self.current_generation,
            'total_optimizations': len(self.optimization_history),
            'active_ab_tests': sum(1 for t in self.ab_tests.values() if t['status'] == 'active'),
            'best_fitness': self.best_result.fitness_score if self.best_result else 0,
            'parameters': self.parameters
        }
