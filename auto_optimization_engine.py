#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNIX V5.3 ULTRA - AUTO-OPTIMIZATION ENGINE
Sistema de optimización automática usando algoritmos genéticos,
A/B testing y auto-ajuste basado en performance

Desarrollado por Harold Nunes - Noviembre 2025
"""

import logging
import random
import json
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class OptimizationStatus(Enum):
    """Estados de optimización"""
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"


class TestVariant(Enum):
    """Variantes de A/B testing"""
    CONTROL = "CONTROL"      # Estrategia original
    VARIANT_A = "VARIANT_A"  # Primera variante
    VARIANT_B = "VARIANT_B"  # Segunda variante


@dataclass
class StrategyParameters:
    """Parámetros optimizables de estrategias"""
    # Quantum Momentum
    quantum_threshold: float = 5.0  # Umbral de señal fuerte
    quantum_weight: float = 0.20
    
    # Kalman Filter
    kalman_threshold: float = 0.3
    kalman_weight: float = 0.15
    
    # Monte Carlo
    monte_carlo_simulations: int = 10000
    monte_carlo_confidence: float = 0.60
    monte_carlo_weight: float = 0.15
    
    # HMM Regime
    hmm_states: int = 3
    hmm_weight: float = 0.12
    
    # Kelly Criterion
    kelly_fraction: float = 0.25
    kelly_weight: float = 0.10
    
    # Black Swan
    black_swan_kurtosis_threshold: float = 3.0
    black_swan_weight: float = 0.10
    
    # Order Book
    order_book_depth: int = 10
    order_book_weight: float = 0.08
    
    # Sentiment
    sentiment_threshold: float = 60.0
    sentiment_weight: float = 0.06
    
    # Sharia Compliance
    sharia_weight: float = 0.04
    
    # Trading Parameters
    min_confidence_threshold: float = 0.60
    max_position_size_usd: float = 1000.0
    stop_loss_percentage: float = 0.05
    take_profit_percentage: float = 0.10
    
    def to_dict(self) -> Dict:
        """Convierte a diccionario"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StrategyParameters':
        """Crea desde diccionario"""
        return cls(**data)
    
    def mutate(self, mutation_rate: float = 0.1) -> 'StrategyParameters':
        """
        Muta los parámetros para algoritmo genético CON VALIDACIÓN ESTRICTA
        
        Args:
            mutation_rate: Probabilidad de mutación (0-1)
        
        Returns:
            Nueva instancia con parámetros mutados y validados
        """
        params = self.to_dict()
        mutated = {}
        
        # Definir límites válidos para cada parámetro
        param_bounds = {
            # Thresholds (0-10 range)
            'quantum_threshold': (1.0, 10.0),
            'kalman_threshold': (0.1, 1.0),
            'black_swan_kurtosis_threshold': (2.0, 5.0),
            'sentiment_threshold': (40.0, 80.0),
            
            # Confidence/probability parameters (0-1 range)
            'monte_carlo_confidence': (0.50, 0.90),
            'min_confidence_threshold': (0.50, 0.90),
            'kelly_fraction': (0.10, 0.50),
            'stop_loss_percentage': (0.02, 0.15),
            'take_profit_percentage': (0.05, 0.30),
            
            # Integer parameters
            'monte_carlo_simulations': (5000, 20000),
            'hmm_states': (2, 5),
            'order_book_depth': (5, 20),
            
            # Position size
            'max_position_size_usd': (100.0, 2000.0),
        }
        
        # Nombres de weights que deben sumar 1.0
        weight_keys = [
            'quantum_weight', 'kalman_weight', 'monte_carlo_weight',
            'hmm_weight', 'kelly_weight', 'black_swan_weight',
            'order_book_weight', 'sentiment_weight', 'sharia_weight'
        ]
        
        # Mutar parámetros NON-weight primero
        for key, value in params.items():
            if key not in weight_keys:
                if random.random() < mutation_rate:
                    if isinstance(value, float):
                        # Mutación gaussiana ±15%
                        change = random.gauss(0, 0.15)
                        new_value = value * (1 + change)
                        
                        # Aplicar límites si existen
                        if key in param_bounds:
                            min_val, max_val = param_bounds[key]
                            new_value = max(min_val, min(max_val, new_value))
                        else:
                            new_value = max(0.01, new_value)
                        
                        mutated[key] = new_value
                    elif isinstance(value, int):
                        # Mutación discreta ±20%
                        change = random.randint(-int(value * 0.2), int(value * 0.2))
                        new_value = value + change
                        
                        # Aplicar límites si existen
                        if key in param_bounds:
                            min_val, max_val = param_bounds[key]
                            new_value = int(max(min_val, min(max_val, new_value)))
                        else:
                            new_value = max(1, new_value)
                        
                        mutated[key] = new_value
                    else:
                        mutated[key] = value
                else:
                    mutated[key] = value
            else:
                # Weights se manejan por separado
                mutated[key] = params[key]
        
        # Mutar y normalizar weights para que sumen 1.0
        weights = [params[k] for k in weight_keys]
        
        # Mutar algunos weights
        for i, key in enumerate(weight_keys):
            if random.random() < mutation_rate:
                change = random.gauss(0, 0.15)
                weights[i] = max(0.01, weights[i] * (1 + change))
        
        # Normalizar para que sumen 1.0
        total_weight = sum(weights)
        if total_weight > 0:
            normalized_weights = [w / total_weight for w in weights]
        else:
            # Fallback: distribuir uniformemente
            normalized_weights = [1.0 / len(weights)] * len(weights)
        
        # Asignar weights normalizados
        for i, key in enumerate(weight_keys):
            mutated[key] = normalized_weights[i]
        
        return StrategyParameters.from_dict(mutated)
    
    def crossover(self, other: 'StrategyParameters') -> 'StrategyParameters':
        """
        Crossover genético con otro set de parámetros
        
        Args:
            other: Otro set de parámetros
            
        Returns:
            Nuevo hijo con genes combinados
        """
        params1 = self.to_dict()
        params2 = other.to_dict()
        child_params = {}
        
        for key in params1.keys():
            # 50% probabilidad de heredar de cada padre
            child_params[key] = params1[key] if random.random() < 0.5 else params2[key]
        
        return StrategyParameters.from_dict(child_params)


@dataclass
class Individual:
    """Individuo en población de algoritmo genético"""
    parameters: StrategyParameters
    fitness: float = 0.0
    generation: int = 0
    trades_count: int = 0
    win_rate: float = 0.0
    profit_usd: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    
    def calculate_fitness(self) -> float:
        """
        Calcula fitness basado en múltiples métricas
        
        Fórmula:
        fitness = (win_rate * 0.3) + (sharpe_ratio * 0.3) + 
                  (profit_normalized * 0.2) - (max_drawdown * 0.2)
        """
        if self.trades_count < 10:
            return 0.0  # Mínimo 10 trades para evaluar
        
        # Normalizar profit (0-100)
        profit_normalized = min(100, max(0, self.profit_usd / 10))
        
        # Penalizar drawdown alto
        drawdown_penalty = abs(self.max_drawdown) * 100
        
        fitness = (
            self.win_rate * 0.3 +
            self.sharpe_ratio * 0.3 +
            profit_normalized * 0.2 -
            drawdown_penalty * 0.2
        )
        
        self.fitness = max(0, fitness)
        return self.fitness


@dataclass
class ABTestResult:
    """Resultado de A/B testing"""
    variant: TestVariant
    trades_count: int
    win_rate: float
    avg_profit_per_trade: float
    total_profit: float
    sharpe_ratio: float
    max_drawdown: float
    confidence_interval: Tuple[float, float]  # (lower, upper)
    is_statistically_significant: bool
    p_value: float


class GeneticOptimizer:
    """
    Optimizador usando Algoritmo Genético
    
    Optimiza los parámetros de las estrategias de trading
    mediante selección natural, crossover y mutación
    """
    
    def __init__(
        self,
        population_size: int = 50,
        generations: int = 100,
        mutation_rate: float = 0.1,
        elite_size: int = 5,
        tournament_size: int = 5
    ):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.elite_size = elite_size
        self.tournament_size = tournament_size
        
        self.population: List[Individual] = []
        self.best_individual: Optional[Individual] = None
        self.generation_history: List[Dict] = []
        
        logger.info(f"🧬 Genetic Optimizer inicializado - Población: {population_size}, Generaciones: {generations}")
    
    def initialize_population(self) -> None:
        """Crea población inicial con parámetros aleatorios"""
        self.population = []
        
        for i in range(self.population_size):
            # Crear parámetros base y mutarlos aleatoriamente
            base_params = StrategyParameters()
            mutated_params = base_params.mutate(mutation_rate=0.5)  # Alta mutación inicial
            
            individual = Individual(
                parameters=mutated_params,
                generation=0
            )
            self.population.append(individual)
        
        logger.info(f"✅ Población inicial creada: {len(self.population)} individuos")
    
    def tournament_selection(self) -> Individual:
        """Selección por torneo - elige el mejor de N individuos aleatorios"""
        tournament = random.sample(self.population, self.tournament_size)
        winner = max(tournament, key=lambda ind: ind.fitness)
        return winner
    
    def evolve_generation(self) -> None:
        """Evoluciona una generación completa"""
        if not self.population:
            self.initialize_population()
            return
        
        # 1. Evaluar fitness de todos los individuos
        for individual in self.population:
            individual.calculate_fitness()
        
        # 2. Ordenar por fitness
        self.population.sort(key=lambda ind: ind.fitness, reverse=True)
        
        # 3. Guardar elite (mejores individuos pasan directamente)
        elite = self.population[:self.elite_size]
        
        # 4. Actualizar mejor individuo histórico
        current_best = self.population[0]
        if not self.best_individual or current_best.fitness > self.best_individual.fitness:
            self.best_individual = current_best
            logger.info(f"🏆 Nuevo mejor individuo - Fitness: {current_best.fitness:.2f}")
        
        # 5. Crear nueva población
        new_population = elite.copy()
        
        while len(new_population) < self.population_size:
            # Selección de padres
            parent1 = self.tournament_selection()
            parent2 = self.tournament_selection()
            
            # Crossover
            child_params = parent1.parameters.crossover(parent2.parameters)
            
            # Mutación
            child_params = child_params.mutate(self.mutation_rate)
            
            # Crear nuevo individuo
            child = Individual(
                parameters=child_params,
                generation=self.population[0].generation + 1
            )
            new_population.append(child)
        
        self.population = new_population
        
        # 6. Guardar historia
        gen_stats = {
            'generation': self.population[0].generation,
            'best_fitness': self.population[0].fitness,
            'avg_fitness': sum(ind.fitness for ind in self.population) / len(self.population),
            'worst_fitness': self.population[-1].fitness,
            'timestamp': datetime.now().isoformat()
        }
        self.generation_history.append(gen_stats)
        
        logger.info(f"📊 Gen {gen_stats['generation']}: Best={gen_stats['best_fitness']:.2f}, Avg={gen_stats['avg_fitness']:.2f}")
    
    def optimize(self, max_generations: Optional[int] = None) -> Individual:
        """
        Ejecuta optimización completa
        
        Args:
            max_generations: Número máximo de generaciones (usa self.generations si None)
            
        Returns:
            Mejor individuo encontrado
        """
        gens = max_generations or self.generations
        
        logger.info(f"🚀 Iniciando optimización genética - {gens} generaciones")
        
        self.initialize_population()
        
        for gen in range(gens):
            self.evolve_generation()
            
            if gen % 10 == 0:
                logger.info(f"⏳ Generación {gen}/{gens} completada")
        
        logger.info(f"✅ Optimización completada - Mejor fitness: {self.best_individual.fitness:.2f}")
        return self.best_individual
    
    def get_top_individuals(self, n: int = 10) -> List[Individual]:
        """Retorna los N mejores individuos"""
        self.population.sort(key=lambda ind: ind.fitness, reverse=True)
        return self.population[:n]


class ABTestingEngine:
    """
    Motor de A/B Testing para estrategias
    
    Compara múltiples variantes de parámetros de forma estadísticamente rigurosa
    """
    
    def __init__(self, database_service=None):
        self.database_service = database_service
        self.active_tests: Dict[str, Dict] = {}
        
        logger.info("🔬 A/B Testing Engine inicializado")
    
    def create_test(
        self,
        test_name: str,
        control_params: StrategyParameters,
        variant_a_params: StrategyParameters,
        variant_b_params: Optional[StrategyParameters] = None,
        duration_hours: int = 24,
        min_samples: int = 50
    ) -> str:
        """
        Crea nuevo test A/B
        
        Args:
            test_name: Nombre descriptivo del test
            control_params: Parámetros de control (baseline)
            variant_a_params: Primera variante
            variant_b_params: Segunda variante (opcional)
            duration_hours: Duración del test en horas
            min_samples: Mínimo de trades por variante
            
        Returns:
            test_id: ID único del test
        """
        test_id = f"ab_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        test_config = {
            'test_id': test_id,
            'test_name': test_name,
            'created_at': datetime.now(),
            'duration_hours': duration_hours,
            'min_samples': min_samples,
            'status': 'RUNNING',
            'variants': {
                TestVariant.CONTROL: {
                    'params': control_params.to_dict(),
                    'trades': [],
                    'metrics': {'wins': 0, 'losses': 0, 'profit': 0.0}
                },
                TestVariant.VARIANT_A: {
                    'params': variant_a_params.to_dict(),
                    'trades': [],
                    'metrics': {'wins': 0, 'losses': 0, 'profit': 0.0}
                }
            }
        }
        
        if variant_b_params:
            test_config['variants'][TestVariant.VARIANT_B] = {
                'params': variant_b_params.to_dict(),
                'trades': [],
                'metrics': {'wins': 0, 'losses': 0, 'profit': 0.0}
            }
        
        self.active_tests[test_id] = test_config
        
        logger.info(f"✅ Test A/B creado: {test_id} - {test_name}")
        return test_id
    
    def assign_variant(self, test_id: str) -> TestVariant:
        """Asigna variante aleatoriamente (distribución uniforme)"""
        if test_id not in self.active_tests:
            return TestVariant.CONTROL
        
        variants = list(self.active_tests[test_id]['variants'].keys())
        return random.choice(variants)
    
    def record_trade_result(
        self,
        test_id: str,
        variant: TestVariant,
        profit: float,
        is_win: bool
    ) -> None:
        """Registra resultado de un trade en el test"""
        if test_id not in self.active_tests:
            logger.warning(f"Test {test_id} no encontrado")
            return
        
        variant_data = self.active_tests[test_id]['variants'][variant]
        variant_data['trades'].append({
            'timestamp': datetime.now(),
            'profit': profit,
            'is_win': is_win
        })
        
        variant_data['metrics']['wins'] += 1 if is_win else 0
        variant_data['metrics']['losses'] += 0 if is_win else 1
        variant_data['metrics']['profit'] += profit
    
    def calculate_confidence_interval(
        self,
        data: List[float],
        confidence: float = 0.95
    ) -> Tuple[float, float]:
        """Calcula intervalo de confianza"""
        if len(data) < 2:
            return (0.0, 0.0)
        
        mean = np.mean(data)
        std = np.std(data, ddof=1)
        n = len(data)
        
        # t-distribution para muestras pequeñas
        from scipy import stats
        t_value = stats.t.ppf((1 + confidence) / 2, n - 1)
        margin = t_value * (std / np.sqrt(n))
        
        return (mean - margin, mean + margin)
    
    def analyze_test(self, test_id: str) -> Dict[TestVariant, ABTestResult]:
        """
        Analiza resultados del test A/B con estadística rigurosa
        
        Returns:
            Diccionario con resultados por variante
        """
        if test_id not in self.active_tests:
            logger.error(f"Test {test_id} no encontrado")
            return {}
        
        test = self.active_tests[test_id]
        results = {}
        
        for variant, variant_data in test['variants'].items():
            trades = variant_data['trades']
            
            if len(trades) < 10:
                logger.warning(f"Variante {variant.value} tiene solo {len(trades)} trades - Insuficiente")
                continue
            
            # Calcular métricas
            total_trades = len(trades)
            wins = variant_data['metrics']['wins']
            win_rate = wins / total_trades if total_trades > 0 else 0.0
            total_profit = variant_data['metrics']['profit']
            avg_profit = total_profit / total_trades if total_trades > 0 else 0.0
            
            # Calcular Sharpe Ratio
            profits = [t['profit'] for t in trades]
            sharpe = (np.mean(profits) / np.std(profits)) if np.std(profits) > 0 else 0.0
            
            # Max drawdown
            cumulative = np.cumsum(profits)
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0.0
            
            # Intervalo de confianza
            ci = self.calculate_confidence_interval(profits)
            
            # Test estadístico vs control (t-test)
            is_significant = False
            p_value = 1.0
            
            if variant != TestVariant.CONTROL:
                control_profits = [t['profit'] for t in test['variants'][TestVariant.CONTROL]['trades']]
                if len(control_profits) >= 10:
                    from scipy import stats
                    t_stat, p_value = stats.ttest_ind(profits, control_profits)
                    is_significant = p_value < 0.05  # 95% confianza
            
            results[variant] = ABTestResult(
                variant=variant,
                trades_count=total_trades,
                win_rate=win_rate,
                avg_profit_per_trade=avg_profit,
                total_profit=total_profit,
                sharpe_ratio=sharpe,
                max_drawdown=max_drawdown,
                confidence_interval=ci,
                is_statistically_significant=is_significant,
                p_value=p_value
            )
        
        return results
    
    def get_winner(self, test_id: str) -> Optional[TestVariant]:
        """
        Determina la variante ganadora
        
        Criterios:
        1. Estadísticamente significativa (p < 0.05)
        2. Mayor Sharpe Ratio
        3. Win rate > 55%
        """
        results = self.analyze_test(test_id)
        
        if not results:
            return None
        
        # Filtrar solo variantes significativas
        significant = {
            var: res for var, res in results.items()
            if res.is_statistically_significant and res.win_rate > 0.55
        }
        
        if not significant:
            logger.info("No hay variantes estadísticamente superiores al control")
            return TestVariant.CONTROL
        
        # Elegir la con mejor Sharpe Ratio
        winner = max(significant.items(), key=lambda x: x[1].sharpe_ratio)
        
        logger.info(f"🏆 Ganador del test: {winner[0].value} (Sharpe: {winner[1].sharpe_ratio:.2f})")
        return winner[0]


class AutoAdjustmentEngine:
    """
    Motor de auto-ajuste basado en performance en tiempo real
    
    Ajusta parámetros automáticamente cuando detecta bajo rendimiento
    """
    
    def __init__(self, lookback_trades: int = 100):
        self.lookback_trades = lookback_trades
        self.performance_history: List[Dict] = []
        self.adjustment_history: List[Dict] = []
        
        logger.info(f"⚙️ Auto-Adjustment Engine inicializado - Lookback: {lookback_trades} trades")
    
    def evaluate_performance(self, recent_trades: List[Dict]) -> Dict[str, float]:
        """
        Evalúa performance reciente
        
        Returns:
            Métricas de performance
        """
        if len(recent_trades) < 20:
            return {'status': 'INSUFFICIENT_DATA'}
        
        profits = [t.get('profit', 0) for t in recent_trades]
        wins = sum(1 for p in profits if p > 0)
        
        metrics = {
            'win_rate': wins / len(recent_trades),
            'avg_profit': np.mean(profits),
            'sharpe_ratio': np.mean(profits) / np.std(profits) if np.std(profits) > 0 else 0,
            'max_drawdown': self._calculate_max_drawdown(profits),
            'total_trades': len(recent_trades),
            'status': 'EVALUATED'
        }
        
        return metrics
    
    def _calculate_max_drawdown(self, profits: List[float]) -> float:
        """Calcula maximum drawdown"""
        cumulative = np.cumsum(profits)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / np.maximum(running_max, 1)
        return float(np.min(drawdown)) if len(drawdown) > 0 else 0.0
    
    def should_adjust(self, metrics: Dict[str, float]) -> Tuple[bool, str]:
        """
        Determina si se deben ajustar parámetros
        
        Triggers de ajuste:
        - Win rate < 45%
        - Sharpe ratio < 0.5
        - Max drawdown > 20%
        """
        reasons = []
        
        if metrics.get('status') == 'INSUFFICIENT_DATA':
            return False, "Datos insuficientes"
        
        if metrics['win_rate'] < 0.45:
            reasons.append(f"Win rate bajo: {metrics['win_rate']:.1%}")
        
        if metrics['sharpe_ratio'] < 0.5:
            reasons.append(f"Sharpe ratio bajo: {metrics['sharpe_ratio']:.2f}")
        
        if abs(metrics['max_drawdown']) > 0.20:
            reasons.append(f"Drawdown alto: {abs(metrics['max_drawdown']):.1%}")
        
        should_adjust = len(reasons) > 0
        reason_text = " | ".join(reasons) if reasons else "Performance aceptable"
        
        return should_adjust, reason_text
    
    def suggest_adjustments(
        self,
        current_params: StrategyParameters,
        metrics: Dict[str, float]
    ) -> StrategyParameters:
        """
        Sugiere ajustes basados en métricas de performance
        
        Estrategia:
        - Si win rate bajo → Aumentar umbral de confianza
        - Si drawdown alto → Reducir tamaño de posición y aumentar stop loss
        - Si sharpe bajo → Ajustar pesos de estrategias
        """
        adjusted = current_params.to_dict()
        
        # Win rate bajo → Más conservador
        if metrics['win_rate'] < 0.45:
            adjusted['min_confidence_threshold'] = min(0.75, adjusted['min_confidence_threshold'] * 1.1)
            adjusted['quantum_threshold'] = min(8.0, adjusted['quantum_threshold'] * 1.2)
            logger.info("📉 Win rate bajo → Aumentando umbrales de confianza")
        
        # Drawdown alto → Reducir riesgo
        if abs(metrics['max_drawdown']) > 0.20:
            adjusted['max_position_size_usd'] = adjusted['max_position_size_usd'] * 0.7
            adjusted['stop_loss_percentage'] = min(0.10, adjusted['stop_loss_percentage'] * 1.3)
            logger.info("🛡️ Drawdown alto → Reduciendo tamaño y aumentando stop loss")
        
        # Sharpe bajo → Rebalancear pesos
        if metrics['sharpe_ratio'] < 0.5:
            # Aumentar peso de estrategias más conservadoras
            adjusted['black_swan_weight'] = min(0.15, adjusted['black_swan_weight'] * 1.2)
            adjusted['monte_carlo_weight'] = min(0.20, adjusted['monte_carlo_weight'] * 1.1)
            adjusted['sentiment_weight'] = max(0.03, adjusted['sentiment_weight'] * 0.9)
            logger.info("⚖️ Sharpe bajo → Rebalanceando pesos hacia estrategias conservadoras")
        
        return StrategyParameters.from_dict(adjusted)


# ==============================================
# FUNCIONES DE UTILIDAD
# ==============================================

def format_ab_test_results(results: Dict[TestVariant, ABTestResult]) -> str:
    """Formatea resultados de A/B test para visualización"""
    lines = [
        "=" * 70,
        "🔬 OMNIX A/B TESTING - RESULTADOS",
        "=" * 70,
        ""
    ]
    
    for variant, result in results.items():
        sig_emoji = "✅" if result.is_statistically_significant else "⚠️"
        
        lines.extend([
            f"📊 {variant.value} {sig_emoji}",
            f"   Trades: {result.trades_count}",
            f"   Win Rate: {result.win_rate:.1%}",
            f"   Avg Profit/Trade: ${result.avg_profit_per_trade:.2f}",
            f"   Total Profit: ${result.total_profit:.2f}",
            f"   Sharpe Ratio: {result.sharpe_ratio:.2f}",
            f"   Max Drawdown: {result.max_drawdown:.1%}",
            f"   95% CI: [{result.confidence_interval[0]:.2f}, {result.confidence_interval[1]:.2f}]",
            f"   P-value: {result.p_value:.4f}",
            ""
        ])
    
    lines.append("=" * 70)
    return "\n".join(lines)


if __name__ == "__main__":
    # Ejemplo de uso
    print("🧬 Testing Genetic Optimizer...")
    
    optimizer = GeneticOptimizer(population_size=20, generations=10)
    
    # Simular fitness (en producción vendrá de trades reales)
    optimizer.initialize_population()
    for individual in optimizer.population:
        individual.trades_count = 50
        individual.win_rate = random.uniform(0.4, 0.7)
        individual.profit_usd = random.uniform(-100, 500)
        individual.sharpe_ratio = random.uniform(0, 2)
        individual.max_drawdown = random.uniform(-0.3, -0.05)
    
    best = optimizer.optimize(max_generations=10)
    print(f"\n✅ Mejor individuo encontrado:")
    print(f"   Fitness: {best.fitness:.2f}")
    print(f"   Win Rate: {best.win_rate:.1%}")
    print(f"   Profit: ${best.profit_usd:.2f}")
    
    print("\n✅ Auto-Optimization Engine listo para producción!")
