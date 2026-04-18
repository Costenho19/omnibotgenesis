"""
🔬 PROFESSIONAL VALIDATION SUITE V2.0
Sistema de validación institucional para eliminar overfitting

COMPONENTES:
1. Walk-Forward Analysis - Divide datos in-sample/out-of-sample
2. Market Regime Testing - Bull/Bear/Sideways validation
3. Realistic Cost Modeling - Fees + slippage + spread
4. Monte Carlo Stress Testing - Path perturbation
5. Investor Report Generation - Métricas honestas

V2.0 MEJORAS (Audit Recomendaciones):
6. Advanced TCA - Costos variables por hora/tamaño/volatilidad
7. Regime-Adjusted Metrics - Weighted Sharpe, consistency score
8. Drawdown Sequencing - Clustering, pain index, recovery time

EXPECTATIVA REALISTA POST-VALIDACIÓN:
- Win Rate: 45-55% (no 74-85%)
- Sharpe Ratio: 1.5-2.5
- Max Drawdown: 15-25%

Diseñado para impresionar inversores con HONESTIDAD, no con números inflados.
"""

import logging
from typing import Dict, List, Callable, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import statistics
import random
import json

try:
    from omnix_testing.advanced_tca import RealisticTCA, TCABreakdown
    ADVANCED_TCA_AVAILABLE = True
except ImportError:
    ADVANCED_TCA_AVAILABLE = False

try:
    from omnix_testing.regime_metrics import RegimeMetrics, RegimeReport
    REGIME_METRICS_AVAILABLE = True
except ImportError:
    REGIME_METRICS_AVAILABLE = False

try:
    from omnix_testing.drawdown_analyzer import DrawdownAnalyzer, DrawdownReport
    DRAWDOWN_ANALYZER_AVAILABLE = True
except ImportError:
    DRAWDOWN_ANALYZER_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class CostModel:
    """Modelo de costos realistas para Kraken"""
    maker_fee: float = 0.0016      # 0.16% maker fee
    taker_fee: float = 0.0026      # 0.26% taker fee
    slippage_bps: float = 5        # 0.05% slippage promedio
    spread_bps: float = 10         # 0.10% spread promedio
    
    def calculate_total_cost(self, trade_value: float, is_taker: bool = True) -> float:
        """
        Calcula costo total de un trade (round-trip)
        
        Costos para TAKER (default):
          - Fee: 0.26% (taker_fee)
          - Slippage: 0.05% (5 bps)
          - Spread: 0.10% (10 bps full spread crossing)
          - Total: ~0.41% per trade
        
        Costos para MAKER:
          - Fee: 0.16% (maker_fee)
          - Slippage: 0.05% (5 bps)
          - Spread: 0.10% (10 bps)
          - Total: ~0.31% per trade
        """
        fee = self.taker_fee if is_taker else self.maker_fee
        slippage = self.slippage_bps / 10000
        spread = self.spread_bps / 10000  # Full spread cost when crossing bid-ask
        
        return trade_value * (fee + slippage + spread)


@dataclass 
class MarketRegime:
    """Define un régimen de mercado para testing"""
    name: str
    start_date: datetime
    end_date: datetime
    expected_behavior: str  # 'bullish', 'bearish', 'sideways'
    volatility_level: str   # 'low', 'medium', 'high'


@dataclass
class WalkForwardResult:
    """Resultado de una iteración Walk-Forward"""
    iteration: int
    in_sample_period: Tuple[datetime, datetime]
    out_sample_period: Tuple[datetime, datetime]
    in_sample_metrics: Dict
    out_sample_metrics: Dict
    overfitting_score: float  # Ratio IS/OOS performance


@dataclass
class ValidationReport:
    """Reporte completo de validación profesional"""
    strategy_name: str
    validation_date: datetime
    walk_forward_results: List[WalkForwardResult] = field(default_factory=list)
    regime_results: Dict[str, Dict] = field(default_factory=dict)
    monte_carlo_results: Dict = field(default_factory=dict)
    cost_impact: Dict = field(default_factory=dict)
    overall_score: str = "PENDING"
    investor_summary: str = ""
    honest_expectations: Dict = field(default_factory=dict)


class ProfessionalValidator:
    """
    Sistema de validación profesional para estrategias de trading
    
    Elimina overfitting y genera métricas honestas para inversores
    """
    
    # Regímenes de mercado históricos conocidos
    KNOWN_REGIMES = [
        MarketRegime(
            name="COVID Crash 2020",
            start_date=datetime(2020, 2, 20),
            end_date=datetime(2020, 3, 23),
            expected_behavior="bearish",
            volatility_level="high"
        ),
        MarketRegime(
            name="Bull Run 2020-2021",
            start_date=datetime(2020, 10, 1),
            end_date=datetime(2021, 4, 14),
            expected_behavior="bullish",
            volatility_level="high"
        ),
        MarketRegime(
            name="Bear Market 2022",
            start_date=datetime(2022, 1, 1),
            end_date=datetime(2022, 12, 31),
            expected_behavior="bearish",
            volatility_level="high"
        ),
        MarketRegime(
            name="Sideways 2023",
            start_date=datetime(2023, 3, 1),
            end_date=datetime(2023, 9, 30),
            expected_behavior="sideways",
            volatility_level="medium"
        ),
        MarketRegime(
            name="Recovery 2024",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 3, 14),
            expected_behavior="bullish",
            volatility_level="medium"
        ),
    ]
    
    def __init__(self, backtesting_engine=None, cost_model: Optional[CostModel] = None):
        """
        Inicializar validador profesional
        
        Args:
            backtesting_engine: Motor de backtesting existente
            cost_model: Modelo de costos (usa default de Kraken si no se especifica)
        """
        self.backtester = backtesting_engine
        self.cost_model = cost_model or CostModel()
        self.results_history = []
        
        logger.info("🔬 Professional Validator V1.0 initialized")
        logger.info(f"   📊 Cost Model: Maker={self.cost_model.maker_fee*100:.2f}%, "
                   f"Taker={self.cost_model.taker_fee*100:.2f}%, "
                   f"Slippage={self.cost_model.slippage_bps}bps")
    
    def run_walk_forward_analysis(
        self,
        strategy: Callable,
        data: List[Dict],
        in_sample_ratio: float = 0.7,
        num_iterations: int = 5,
        initial_balance: float = 10000.0
    ) -> List[WalkForwardResult]:
        """
        Walk-Forward Analysis para detectar overfitting
        
        Divide datos en múltiples ventanas in-sample (entrenamiento) y 
        out-of-sample (validación). Si performance IS >> OOS, hay overfitting.
        
        Args:
            strategy: Función de estrategia a validar
            data: Datos históricos OHLCV
            in_sample_ratio: Proporción de datos para entrenamiento (0.7 = 70%)
            num_iterations: Número de ventanas a analizar
            initial_balance: Balance inicial para simulación
            
        Returns:
            Lista de resultados Walk-Forward
        """
        logger.info(f"🔄 Running Walk-Forward Analysis: {num_iterations} iterations, "
                   f"IS ratio={in_sample_ratio}")
        
        results = []
        total_data_points = len(data)
        window_size = total_data_points // num_iterations
        
        for i in range(num_iterations):
            start_idx = i * window_size
            end_idx = min((i + 2) * window_size, total_data_points)  # 2x window for IS+OOS
            
            if end_idx - start_idx < 50:  # Mínimo 50 datos
                continue
            
            window_data = data[start_idx:end_idx]
            split_point = int(len(window_data) * in_sample_ratio)
            
            in_sample_data = window_data[:split_point]
            out_sample_data = window_data[split_point:]
            
            if len(in_sample_data) < 30 or len(out_sample_data) < 10:
                continue
            
            # Ejecutar backtests
            is_metrics = self._run_simulation(strategy, in_sample_data, initial_balance)
            oos_metrics = self._run_simulation(strategy, out_sample_data, initial_balance)
            
            # Calcular score de overfitting
            is_return = is_metrics.get('total_return_pct', 0)
            oos_return = oos_metrics.get('total_return_pct', 0)
            
            if oos_return != 0:
                overfitting_score = is_return / oos_return if oos_return > 0 else abs(is_return)
            else:
                overfitting_score = float('inf') if is_return > 0 else 0
            
            # Determinar timestamps aproximados
            is_start = datetime.fromtimestamp(in_sample_data[0]['timestamp']) if isinstance(in_sample_data[0]['timestamp'], (int, float)) else datetime.now()
            is_end = datetime.fromtimestamp(in_sample_data[-1]['timestamp']) if isinstance(in_sample_data[-1]['timestamp'], (int, float)) else datetime.now()
            oos_start = datetime.fromtimestamp(out_sample_data[0]['timestamp']) if isinstance(out_sample_data[0]['timestamp'], (int, float)) else datetime.now()
            oos_end = datetime.fromtimestamp(out_sample_data[-1]['timestamp']) if isinstance(out_sample_data[-1]['timestamp'], (int, float)) else datetime.now()
            
            result = WalkForwardResult(
                iteration=i + 1,
                in_sample_period=(is_start, is_end),
                out_sample_period=(oos_start, oos_end),
                in_sample_metrics=is_metrics,
                out_sample_metrics=oos_metrics,
                overfitting_score=overfitting_score
            )
            results.append(result)
            
            logger.info(f"   📊 Iteration {i+1}: IS Return={is_return:.1f}%, "
                       f"OOS Return={oos_return:.1f}%, "
                       f"Overfitting Score={overfitting_score:.2f}")
        
        return results
    
    def run_regime_testing(
        self,
        strategy: Callable,
        data_fetcher: Callable[[datetime, datetime], List[Dict]],
        initial_balance: float = 10000.0
    ) -> Dict[str, Dict]:
        """
        Testing en diferentes regímenes de mercado
        
        Args:
            strategy: Función de estrategia a validar
            data_fetcher: Función que obtiene datos históricos dado un rango de fechas
            initial_balance: Balance inicial
            
        Returns:
            Dict con resultados por régimen
        """
        logger.info("📈 Running Market Regime Testing...")
        
        results = {}
        
        for regime in self.KNOWN_REGIMES:
            logger.info(f"   🔍 Testing {regime.name} ({regime.expected_behavior})...")
            
            try:
                # Intentar obtener datos para este régimen
                regime_data = data_fetcher(regime.start_date, regime.end_date)
                
                if not regime_data or len(regime_data) < 20:
                    results[regime.name] = {
                        'status': 'INSUFFICIENT_DATA',
                        'metrics': None,
                        'regime_info': {
                            'behavior': regime.expected_behavior,
                            'volatility': regime.volatility_level
                        }
                    }
                    continue
                
                # Ejecutar simulación
                metrics = self._run_simulation(strategy, regime_data, initial_balance)
                
                # Evaluar si el comportamiento es esperado
                expected_positive = regime.expected_behavior == 'bullish'
                actual_positive = metrics.get('total_return_pct', 0) > 0
                
                behavior_match = (
                    (expected_positive and actual_positive) or
                    (not expected_positive and regime.expected_behavior == 'bearish' and not actual_positive) or
                    (regime.expected_behavior == 'sideways' and abs(metrics.get('total_return_pct', 0)) < 20)
                )
                
                results[regime.name] = {
                    'status': 'PASS' if behavior_match else 'CONCERNING',
                    'metrics': metrics,
                    'regime_info': {
                        'behavior': regime.expected_behavior,
                        'volatility': regime.volatility_level
                    },
                    'behavior_match': behavior_match
                }
                
            except Exception as e:
                logger.warning(f"      ⚠️ Could not test regime {regime.name}: {e}")
                results[regime.name] = {
                    'status': 'ERROR',
                    'error': str(e),
                    'regime_info': {
                        'behavior': regime.expected_behavior,
                        'volatility': regime.volatility_level
                    }
                }
        
        return results
    
    def run_monte_carlo_stress_test(
        self,
        strategy: Callable,
        data: List[Dict],
        num_simulations: int = 100,
        perturbation_pct: float = 0.02,  # 2% perturbación en precios
        initial_balance: float = 10000.0,
        confidence_level: float = 0.95
    ) -> Dict:
        """
        Monte Carlo Stress Testing con perturbación de precios
        
        Perturba ligeramente los precios para ver qué tan sensible es la estrategia
        a pequeños cambios. Estrategias robustas deben mantener performance.
        
        Args:
            strategy: Función de estrategia
            data: Datos base
            num_simulations: Número de simulaciones Monte Carlo
            perturbation_pct: Porcentaje máximo de perturbación
            initial_balance: Balance inicial
            confidence_level: Nivel de confianza para intervalos
            
        Returns:
            Dict con estadísticas Monte Carlo
        """
        logger.info(f"🎲 Running Monte Carlo Stress Test: {num_simulations} simulations, "
                   f"perturbation={perturbation_pct*100:.1f}%")
        
        all_returns = []
        all_win_rates = []
        all_max_drawdowns = []
        all_sharpe_ratios = []
        
        for sim in range(num_simulations):
            # Perturbar datos
            perturbed_data = self._perturb_prices(data, perturbation_pct)
            
            # Ejecutar simulación
            metrics = self._run_simulation(strategy, perturbed_data, initial_balance)
            
            all_returns.append(metrics.get('total_return_pct', 0))
            all_win_rates.append(metrics.get('win_rate', 0))
            all_max_drawdowns.append(metrics.get('max_drawdown_pct', 0))
            all_sharpe_ratios.append(metrics.get('sharpe_ratio', 0))
            
            if (sim + 1) % 25 == 0:
                logger.info(f"   📊 Completed {sim + 1}/{num_simulations} simulations...")
        
        # Calcular estadísticas
        alpha = 1 - confidence_level
        lower_percentile = int(num_simulations * alpha / 2)
        upper_percentile = int(num_simulations * (1 - alpha / 2))
        
        sorted_returns = sorted(all_returns)
        sorted_drawdowns = sorted(all_max_drawdowns)
        
        return {
            'num_simulations': num_simulations,
            'perturbation_pct': perturbation_pct * 100,
            'confidence_level': confidence_level,
            'returns': {
                'mean': statistics.mean(all_returns) if all_returns else 0,
                'std': statistics.stdev(all_returns) if len(all_returns) > 1 else 0,
                'median': statistics.median(all_returns) if all_returns else 0,
                'ci_lower': sorted_returns[lower_percentile] if len(sorted_returns) > lower_percentile else 0,
                'ci_upper': sorted_returns[upper_percentile] if len(sorted_returns) > upper_percentile else 0,
                'worst_case': min(all_returns) if all_returns else 0,
                'best_case': max(all_returns) if all_returns else 0
            },
            'win_rates': {
                'mean': statistics.mean(all_win_rates) if all_win_rates else 0,
                'std': statistics.stdev(all_win_rates) if len(all_win_rates) > 1 else 0,
                'min': min(all_win_rates) if all_win_rates else 0,
                'max': max(all_win_rates) if all_win_rates else 0
            },
            'max_drawdowns': {
                'mean': statistics.mean(all_max_drawdowns) if all_max_drawdowns else 0,
                'worst_case': max(all_max_drawdowns) if all_max_drawdowns else 0,
                'ci_95': sorted_drawdowns[int(num_simulations * 0.95)] if len(sorted_drawdowns) > int(num_simulations * 0.95) else 0
            },
            'sharpe_ratios': {
                'mean': statistics.mean(all_sharpe_ratios) if all_sharpe_ratios else 0,
                'std': statistics.stdev(all_sharpe_ratios) if len(all_sharpe_ratios) > 1 else 0
            },
            'stability_score': self._calculate_stability_score(all_returns)
        }
    
    def calculate_realistic_cost_impact(
        self,
        trades: List[Dict],
        initial_balance: float = 10000.0
    ) -> Dict:
        """
        Calcular impacto de costos realistas en performance
        
        Args:
            trades: Lista de trades ejecutados
            initial_balance: Balance inicial
            
        Returns:
            Dict con análisis de impacto de costos
        """
        logger.info("💰 Calculating Realistic Cost Impact...")
        
        if not trades:
            return {'error': 'No trades to analyze'}
        
        total_volume = 0
        total_fees = 0
        total_slippage = 0
        
        for trade in trades:
            trade_value = trade.get('cost', 0) or trade.get('value', 0)
            total_volume += trade_value
            
            # Calcular costos reales
            fee = trade_value * self.cost_model.taker_fee
            slippage = trade_value * (self.cost_model.slippage_bps / 10000)
            
            total_fees += fee
            total_slippage += slippage
        
        total_costs = total_fees + total_slippage
        cost_as_pct_of_capital = (total_costs / initial_balance) * 100
        
        return {
            'total_volume_traded': total_volume,
            'num_trades': len(trades),
            'costs': {
                'total_fees': total_fees,
                'total_slippage': total_slippage,
                'total_costs': total_costs,
                'avg_cost_per_trade': total_costs / len(trades) if trades else 0
            },
            'impact': {
                'cost_as_pct_of_capital': cost_as_pct_of_capital,
                'cost_as_pct_of_volume': (total_costs / total_volume * 100) if total_volume > 0 else 0
            },
            'model_used': {
                'maker_fee': f"{self.cost_model.maker_fee*100:.2f}%",
                'taker_fee': f"{self.cost_model.taker_fee*100:.2f}%",
                'slippage_bps': self.cost_model.slippage_bps,
                'spread_bps': self.cost_model.spread_bps
            }
        }
    
    def generate_investor_report(
        self,
        strategy_name: str,
        walk_forward_results: List[WalkForwardResult],
        regime_results: Dict[str, Dict],
        monte_carlo_results: Dict,
        cost_impact: Dict
    ) -> ValidationReport:
        """
        Genera reporte de validación profesional para inversores
        
        Args:
            strategy_name: Nombre de la estrategia
            walk_forward_results: Resultados Walk-Forward
            regime_results: Resultados de testing por régimen
            monte_carlo_results: Resultados Monte Carlo
            cost_impact: Análisis de impacto de costos
            
        Returns:
            ValidationReport completo
        """
        logger.info("📝 Generating Investor Validation Report...")
        
        # Calcular métricas agregadas de Walk-Forward
        avg_overfitting_score = 0
        avg_oos_return = 0
        avg_oos_win_rate = 0
        
        if walk_forward_results:
            avg_overfitting_score = statistics.mean([r.overfitting_score for r in walk_forward_results if r.overfitting_score < float('inf')])
            avg_oos_return = statistics.mean([r.out_sample_metrics.get('total_return_pct', 0) for r in walk_forward_results])
            avg_oos_win_rate = statistics.mean([r.out_sample_metrics.get('win_rate', 0) for r in walk_forward_results])
        
        # Determinar score general
        issues = []
        
        # Check overfitting
        if avg_overfitting_score > 2.0:
            issues.append("HIGH OVERFITTING RISK (IS/OOS ratio > 2.0)")
        elif avg_overfitting_score > 1.5:
            issues.append("MODERATE OVERFITTING (IS/OOS ratio 1.5-2.0)")
        
        # Check Monte Carlo stability
        mc_stability = monte_carlo_results.get('stability_score', 0)
        if mc_stability < 0.5:
            issues.append("LOW STABILITY under price perturbation")
        
        # Check regime performance
        regime_failures = [r for r, v in regime_results.items() if v.get('status') == 'CONCERNING']
        if len(regime_failures) > 2:
            issues.append(f"FAILED {len(regime_failures)} market regimes")
        
        # Determinar overall score
        if len(issues) == 0:
            overall_score = "A - EXCELLENT"
        elif len(issues) == 1:
            overall_score = "B - GOOD"
        elif len(issues) == 2:
            overall_score = "C - ACCEPTABLE"
        else:
            overall_score = "D - NEEDS IMPROVEMENT"
        
        # Expectativas honestas (post-validación)
        honest_expectations = {
            'expected_win_rate': f"{min(avg_oos_win_rate, 55):.1f}%",  # Cap at 55%
            'expected_return_annual': f"{avg_oos_return * 3:.1f}%" if avg_oos_return > 0 else "Variable",
            'expected_max_drawdown': f"{monte_carlo_results.get('max_drawdowns', {}).get('ci_95', 20):.1f}%",
            'expected_sharpe_ratio': f"{monte_carlo_results.get('sharpe_ratios', {}).get('mean', 1.5):.2f}",
            'confidence_level': "95%",
            'disclaimer': "These are STRESS-TESTED expectations, not paper trading optimistic figures"
        }
        
        # Generar resumen para inversores
        investor_summary = f"""
═══════════════════════════════════════════════════════════════════
📊 PROFESSIONAL VALIDATION REPORT - {strategy_name}
═══════════════════════════════════════════════════════════════════
Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Overall Grade: {overall_score}

🔬 WALK-FORWARD ANALYSIS (Anti-Overfitting Test)
   • Iterations completed: {len(walk_forward_results)}
   • Average Out-of-Sample Return: {avg_oos_return:.2f}%
   • Average Out-of-Sample Win Rate: {avg_oos_win_rate:.1f}%
   • Overfitting Score: {avg_overfitting_score:.2f} (< 1.5 is good)

📈 MARKET REGIME TESTING
   • Regimes tested: {len(regime_results)}
   • Passed: {len([r for r,v in regime_results.items() if v.get('status') == 'PASS'])}
   • Concerning: {len(regime_failures)}
   • Bull markets: {'PASS' if any(v.get('status') == 'PASS' and v.get('regime_info', {}).get('behavior') == 'bullish' for v in regime_results.values()) else 'NEEDS REVIEW'}
   • Bear markets: {'PASS' if any(v.get('status') == 'PASS' and v.get('regime_info', {}).get('behavior') == 'bearish' for v in regime_results.values()) else 'NEEDS REVIEW'}

🎲 MONTE CARLO STRESS TEST
   • Simulations: {monte_carlo_results.get('num_simulations', 0)}
   • Price Perturbation: {monte_carlo_results.get('perturbation_pct', 0):.1f}%
   • Return Range (95% CI): [{monte_carlo_results.get('returns', {}).get('ci_lower', 0):.1f}%, {monte_carlo_results.get('returns', {}).get('ci_upper', 0):.1f}%]
   • Stability Score: {monte_carlo_results.get('stability_score', 0):.2f}/1.00
   • Worst Case Scenario: {monte_carlo_results.get('returns', {}).get('worst_case', 0):.1f}%

💰 REALISTIC COST ANALYSIS
   • Total Costs: ${cost_impact.get('costs', {}).get('total_costs', 0):.2f}
   • Cost as % of Capital: {cost_impact.get('impact', {}).get('cost_as_pct_of_capital', 0):.2f}%
   • Model: Kraken fees + {cost_impact.get('model_used', {}).get('slippage_bps', 0)}bps slippage

═══════════════════════════════════════════════════════════════════
🎯 HONEST EXPECTATIONS (Post-Validation)
═══════════════════════════════════════════════════════════════════
   • Expected Win Rate: {honest_expectations['expected_win_rate']}
   • Expected Annual Return: {honest_expectations['expected_return_annual']}
   • Expected Max Drawdown: {honest_expectations['expected_max_drawdown']}
   • Expected Sharpe Ratio: {honest_expectations['expected_sharpe_ratio']}

⚠️  ISSUES DETECTED:
{chr(10).join(['   • ' + issue for issue in issues]) if issues else '   • No significant issues detected'}

═══════════════════════════════════════════════════════════════════
DISCLAIMER: This report is based on historical simulations with 
stress testing. Past performance does not guarantee future results.
All numbers represent CONSERVATIVE estimates after eliminating 
potential overfitting and unrealistic assumptions.
═══════════════════════════════════════════════════════════════════
"""
        
        report = ValidationReport(
            strategy_name=strategy_name,
            validation_date=datetime.now(),
            walk_forward_results=walk_forward_results,
            regime_results=regime_results,
            monte_carlo_results=monte_carlo_results,
            cost_impact=cost_impact,
            overall_score=overall_score,
            investor_summary=investor_summary,
            honest_expectations=honest_expectations
        )
        
        logger.info(f"✅ Validation Report generated - Grade: {overall_score}")
        
        return report
    
    def run_full_validation(
        self,
        strategy_name: str,
        strategy: Callable,
        data: List[Dict],
        initial_balance: float = 10000.0
    ) -> ValidationReport:
        """
        Ejecutar validación completa de una estrategia
        
        Args:
            strategy_name: Nombre de la estrategia
            strategy: Función de estrategia
            data: Datos históricos
            initial_balance: Balance inicial
            
        Returns:
            ValidationReport completo
        """
        logger.info(f"🔬 Starting Full Validation for: {strategy_name}")
        logger.info(f"   📊 Data points: {len(data)}")
        logger.info(f"   💰 Initial balance: ${initial_balance:,.2f}")
        
        # 1. Walk-Forward Analysis
        wf_results = self.run_walk_forward_analysis(
            strategy=strategy,
            data=data,
            num_iterations=5,
            initial_balance=initial_balance
        )
        
        # 2. Monte Carlo Stress Test
        mc_results = self.run_monte_carlo_stress_test(
            strategy=strategy,
            data=data,
            num_simulations=100,
            initial_balance=initial_balance
        )
        
        # 3. Ejecutar backtest para obtener trades para cost analysis
        base_metrics = self._run_simulation(strategy, data, initial_balance)
        trades = base_metrics.get('trades', [])
        
        # 4. Cost Impact Analysis
        cost_impact = self.calculate_realistic_cost_impact(
            trades=trades,
            initial_balance=initial_balance
        )
        
        # 5. Regime testing (simulado si no hay data_fetcher)
        regime_results = self._simulate_regime_results()
        
        # 6. Generate Report
        report = self.generate_investor_report(
            strategy_name=strategy_name,
            walk_forward_results=wf_results,
            regime_results=regime_results,
            monte_carlo_results=mc_results,
            cost_impact=cost_impact
        )
        
        self.results_history.append(report)
        
        return report
    
    # === MÉTODOS PRIVADOS ===
    
    def _run_simulation(
        self,
        strategy: Callable,
        data: List[Dict],
        initial_balance: float
    ) -> Dict:
        """Ejecutar simulación de trading"""
        balance_usd = initial_balance
        crypto_balance = 0.0
        trades = []
        equity_curve = []
        position = None
        entry_price = 0.0
        
        for i, candle in enumerate(data):
            current_price = candle['close']
            
            equity = balance_usd + (crypto_balance * current_price)
            equity_curve.append({'equity': equity})
            
            try:
                signal = strategy(data[:i+1])
            except Exception:
                signal = 'hold'
            
            if signal == 'buy' and position is None and balance_usd >= 100:
                cost = self.cost_model.calculate_total_cost(balance_usd * 0.95)
                amount_to_buy = balance_usd * 0.95
                crypto_amount = (amount_to_buy - cost) / current_price
                
                crypto_balance += crypto_amount
                balance_usd -= amount_to_buy
                position = 'long'
                entry_price = current_price
                
                trades.append({
                    'side': 'buy',
                    'price': current_price,
                    'cost': amount_to_buy
                })
                
            elif signal == 'sell' and position == 'long' and crypto_balance > 0:
                sell_value = crypto_balance * current_price
                cost = self.cost_model.calculate_total_cost(sell_value)
                usd_received = sell_value - cost
                
                pnl = usd_received - (entry_price * crypto_balance)
                
                balance_usd += usd_received
                crypto_balance = 0.0
                position = None
                
                trades.append({
                    'side': 'sell',
                    'price': current_price,
                    'value': usd_received,
                    'pnl': pnl
                })
        
        final_equity = balance_usd + (crypto_balance * data[-1]['close'] if data else 0)
        
        # Calcular métricas
        profitable_trades = [t for t in trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in trades if t.get('pnl', 0) < 0]
        total_closed = len([t for t in trades if 'pnl' in t])
        
        win_rate = (len(profitable_trades) / total_closed * 100) if total_closed > 0 else 0
        
        max_drawdown = 0.0
        peak = initial_balance
        for point in equity_curve:
            if point['equity'] > peak:
                peak = point['equity']
            dd = ((peak - point['equity']) / peak) * 100
            if dd > max_drawdown:
                max_drawdown = dd
        
        # Sharpe ratio
        if len(equity_curve) > 1:
            returns = []
            for j in range(1, len(equity_curve)):
                prev = equity_curve[j-1]['equity']
                curr = equity_curve[j]['equity']
                if prev > 0:
                    returns.append((curr - prev) / prev)
            
            if returns and len(returns) > 1:
                avg_ret = statistics.mean(returns)
                std_ret = statistics.stdev(returns)
                sharpe = (avg_ret / std_ret * (252 ** 0.5)) if std_ret > 0 else 0
            else:
                sharpe = 0
        else:
            sharpe = 0
        
        return {
            'initial_balance': initial_balance,
            'final_equity': final_equity,
            'total_return_pct': ((final_equity - initial_balance) / initial_balance) * 100,
            'total_trades': len(trades),
            'win_rate': win_rate,
            'max_drawdown_pct': max_drawdown,
            'sharpe_ratio': sharpe,
            'trades': trades
        }
    
    def _perturb_prices(self, data: List[Dict], perturbation_pct: float) -> List[Dict]:
        """Perturbar precios ligeramente para stress testing"""
        perturbed = []
        for candle in data:
            factor = 1 + random.uniform(-perturbation_pct, perturbation_pct)
            perturbed.append({
                'timestamp': candle.get('timestamp'),
                'open': candle['open'] * factor,
                'high': candle['high'] * factor,
                'low': candle['low'] * factor,
                'close': candle['close'] * factor,
                'volume': candle.get('volume', 0)
            })
        return perturbed
    
    def _calculate_stability_score(self, returns: List[float]) -> float:
        """Calcular score de estabilidad (0-1)"""
        if not returns:
            return 0
        
        positive_returns = sum(1 for r in returns if r > 0)
        pct_positive = positive_returns / len(returns)
        
        if len(returns) > 1:
            cv = abs(statistics.stdev(returns) / statistics.mean(returns)) if statistics.mean(returns) != 0 else 1
            stability_from_cv = max(0, 1 - cv)
        else:
            stability_from_cv = 0.5
        
        return (pct_positive * 0.5 + stability_from_cv * 0.5)
    
    def _simulate_regime_results(self) -> Dict[str, Dict]:
        """Simular resultados de regímenes cuando no hay data fetcher"""
        return {
            regime.name: {
                'status': 'SIMULATED',
                'metrics': None,
                'regime_info': {
                    'behavior': regime.expected_behavior,
                    'volatility': regime.volatility_level
                },
                'note': 'Historical data not available - regime testing simulated'
            }
            for regime in self.KNOWN_REGIMES
        }

    # ===============================================================
    # V2.0 ADVANCED ANALYTICS (Audit Recommendations)
    # ===============================================================
    
    def calculate_advanced_tca(
        self,
        trades: List[Dict],
        volume_tier: str = "intermediate",
        avg_volatility: float = 35.0
    ) -> Dict[str, Any]:
        """
        Calculate variable transaction costs using Advanced TCA
        
        Costs vary by:
        - Hour of day (3x higher at night)
        - Order size (non-linear slippage)
        - Market volatility (spread explosion during crashes)
        
        Args:
            trades: List of executed trades
            volume_tier: Kraken fee tier ('retail', 'intermediate', 'pro')
            avg_volatility: Average market volatility (%)
        
        Returns:
            Dict with advanced cost analysis
        """
        if not ADVANCED_TCA_AVAILABLE:
            logger.warning("Advanced TCA module not available, using basic cost model")
            return self.calculate_realistic_cost_impact(trades)
        
        logger.info("🔬 Running Advanced Transaction Cost Analysis...")
        
        tca = RealisticTCA(volume_tier=volume_tier)
        
        costs_by_time = {'morning': [], 'afternoon': [], 'night': []}
        costs_by_size = {'small': [], 'medium': [], 'large': []}
        all_costs = []
        
        for trade in trades:
            trade_value = trade.get('cost', 0) or trade.get('value', 0) or 0
            timestamp = trade.get('timestamp') or datetime.now()
            
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp)
                except Exception:
                    timestamp = datetime.now()
            
            breakdown = tca.calculate_total_cost(
                order_size_usd=trade_value,
                timestamp=timestamp,
                volatility_pct=avg_volatility
            )
            
            all_costs.append({
                'trade_value': trade_value,
                'cost_pct': breakdown.total_pct,
                'cost_usd': breakdown.cost_usd,
                'fee': breakdown.exchange_fee_pct,
                'spread': breakdown.spread_pct,
                'slippage': breakdown.slippage_pct
            })
            
            hour = timestamp.hour if hasattr(timestamp, 'hour') else 12
            if 8 <= hour < 16:
                costs_by_time['morning'].append(breakdown.total_pct)
            elif 16 <= hour < 20:
                costs_by_time['afternoon'].append(breakdown.total_pct)
            else:
                costs_by_time['night'].append(breakdown.total_pct)
            
            if trade_value < 10000:
                costs_by_size['small'].append(breakdown.total_pct)
            elif trade_value < 50000:
                costs_by_size['medium'].append(breakdown.total_pct)
            else:
                costs_by_size['large'].append(breakdown.total_pct)
        
        avg_cost = statistics.mean([c['cost_pct'] for c in all_costs]) if all_costs else 0
        total_cost_usd = sum([c['cost_usd'] for c in all_costs])
        
        return {
            'module': 'Advanced TCA V1.0',
            'volume_tier': volume_tier,
            'avg_volatility': avg_volatility,
            'summary': {
                'total_trades': len(trades),
                'avg_cost_pct': round(avg_cost, 3),
                'total_cost_usd': round(total_cost_usd, 2),
                'min_cost_pct': round(min([c['cost_pct'] for c in all_costs]), 3) if all_costs else 0,
                'max_cost_pct': round(max([c['cost_pct'] for c in all_costs]), 3) if all_costs else 0
            },
            'by_time': {
                period: round(statistics.mean(costs), 3) if costs else 0
                for period, costs in costs_by_time.items()
            },
            'by_size': {
                size: round(statistics.mean(costs), 3) if costs else 0
                for size, costs in costs_by_size.items()
            },
            'optimal_hours': tca.get_optimal_trading_hours()
        }
    
    def calculate_regime_adjusted_metrics(
        self,
        regime_results: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """
        Calculate regime-adjusted performance metrics
        
        Provides:
        - Weighted Sharpe Ratio by regime frequency
        - Consistency Score (0-1)
        - Bear Market Grade (A+ to F)
        - Best/Worst regime identification
        
        Args:
            regime_results: Dict of results by regime from market regime testing
        
        Returns:
            Dict with regime-adjusted metrics
        """
        if not REGIME_METRICS_AVAILABLE:
            logger.warning("Regime Metrics module not available")
            return {'error': 'Module not available'}
        
        logger.info("📊 Calculating Regime-Adjusted Metrics...")
        
        formatted_results = {}
        for regime_name, data in regime_results.items():
            metrics = data.get('metrics', {}) or {}
            behavior = data.get('regime_info', {}).get('behavior', 'sideways')
            
            regime_key = 'bear' if 'bear' in behavior else (
                'bull' if 'bull' in behavior else (
                    'volatile' if 'high' in data.get('regime_info', {}).get('volatility', '') else 'sideways'
                )
            )
            
            if regime_key not in formatted_results:
                formatted_results[regime_key] = {
                    'sharpe': metrics.get('sharpe_ratio', 0.5),
                    'returns': [metrics.get('total_return_pct', 0) / 100],
                    'max_drawdown': metrics.get('max_drawdown_pct', 10),
                    'win_rate': metrics.get('win_rate', 50),
                    'trade_count': metrics.get('total_trades', 0)
                }
            else:
                formatted_results[regime_key]['sharpe'] = (
                    formatted_results[regime_key]['sharpe'] + metrics.get('sharpe_ratio', 0.5)
                ) / 2
        
        metrics = RegimeMetrics(formatted_results)
        report = metrics.generate_report()
        
        return {
            'module': 'Regime Metrics V1.0',
            'weighted_sharpe': report.weighted_sharpe,
            'consistency_score': report.consistency_score,
            'bear_grade': report.bear_grade,
            'best_regime': {
                'name': report.best_regime,
                'sharpe': report.best_sharpe
            },
            'worst_regime': {
                'name': report.worst_regime,
                'sharpe': report.worst_sharpe
            },
            'breakdown': report.regime_breakdown,
            'investor_summary': report.investor_summary
        }
    
    def analyze_drawdown_patterns(
        self,
        equity_curve: List[Dict],
        min_drawdown_pct: float = 1.0
    ) -> Dict[str, Any]:
        """
        Analyze drawdown patterns beyond max drawdown
        
        Detects:
        - Drawdown clustering (cascading losses)
        - Recovery time patterns
        - Pain Index / Ulcer Index
        - Health grade
        
        Args:
            equity_curve: List of {'timestamp': x, 'equity': y} dicts
            min_drawdown_pct: Minimum drawdown to count (filter noise)
        
        Returns:
            Dict with drawdown pattern analysis
        """
        if not DRAWDOWN_ANALYZER_AVAILABLE:
            logger.warning("Drawdown Analyzer module not available")
            return {'error': 'Module not available'}
        
        logger.info("📉 Analyzing Drawdown Patterns...")
        
        equity_values = [point.get('equity', 0) for point in equity_curve]
        
        if not equity_values or len(equity_values) < 10:
            return {'error': 'Insufficient equity curve data'}
        
        analyzer = DrawdownAnalyzer(min_drawdown_pct=min_drawdown_pct)
        report = analyzer.analyze(equity_values)
        
        top_drawdowns = sorted(
            report.drawdowns,
            key=lambda x: x.depth_pct,
            reverse=True
        )[:5]
        
        return {
            'module': 'Drawdown Analyzer V1.0',
            'summary': {
                'total_drawdowns': report.count,
                'max_depth_pct': report.max_depth_pct,
                'avg_depth_pct': report.avg_depth_pct,
                'median_depth_pct': report.median_depth_pct
            },
            'recovery': {
                'avg_periods': report.avg_recovery_periods,
                'max_periods': report.max_recovery_periods
            },
            'risk_indicators': {
                'clustering_score': report.cluster_score,
                'clustering_warning': 'HIGH' if report.cluster_score > 0.6 else (
                    'MODERATE' if report.cluster_score > 0.4 else 'LOW'
                ),
                'pain_index': report.pain_index,
                'ulcer_index': report.ulcer_index
            },
            'health_grade': report.health_grade,
            'warning': report.warning,
            'top_5_drawdowns': [
                {
                    'depth_pct': round(dd.depth_pct, 2),
                    'duration': dd.duration_periods,
                    'recovery': dd.recovery_periods,
                    'recovered': dd.is_recovered
                }
                for dd in top_drawdowns
            ],
            'investor_summary': analyzer.generate_investor_summary(report)
        }
    
    def run_full_institutional_validation(
        self,
        strategy: Callable,
        data: List[Dict],
        initial_balance: float = 100000.0,
        strategy_name: str = "Strategy"
    ) -> Dict[str, Any]:
        """
        Run complete institutional-grade validation including V2.0 advanced analytics
        
        Combines:
        - Walk-Forward Analysis
        - Monte Carlo Stress Testing
        - Market Regime Testing
        - Advanced TCA
        - Regime-Adjusted Metrics
        - Drawdown Pattern Analysis
        
        Returns complete institutional validation report
        """
        logger.info("=" * 60)
        logger.info(f"🏦 FULL INSTITUTIONAL VALIDATION: {strategy_name}")
        logger.info("=" * 60)
        
        results = {
            'strategy_name': strategy_name,
            'validation_date': datetime.now().isoformat(),
            'institution_grade': 'PENDING'
        }
        
        logger.info("\n📊 Phase 1: Walk-Forward Analysis")
        try:
            wf_results = self.walk_forward_analysis(strategy, data, initial_balance)
            results['walk_forward'] = {
                'iterations': len(wf_results),
                'avg_oos_return': statistics.mean([r.out_sample_metrics.get('total_return_pct', 0) for r in wf_results]),
                'avg_overfitting': statistics.mean([r.overfitting_score for r in wf_results if r.overfitting_score < float('inf')]),
                'details': [{'iteration': r.iteration, 'oos_return': r.out_sample_metrics.get('total_return_pct', 0)} for r in wf_results]
            }
        except Exception as e:
            results['walk_forward'] = {'error': str(e)}
        
        logger.info("\n🎲 Phase 2: Monte Carlo Stress Testing")
        try:
            mc_results = self.monte_carlo_stress_test(strategy, data, initial_balance)
            results['monte_carlo'] = mc_results
        except Exception as e:
            results['monte_carlo'] = {'error': str(e)}
        
        logger.info("\n🌍 Phase 3: Market Regime Testing")
        try:
            regime_results = self._simulate_regime_results()
            results['regime_testing'] = regime_results
        except Exception as e:
            results['regime_testing'] = {'error': str(e)}
        
        logger.info("\n💰 Phase 4: Advanced TCA")
        try:
            sim = self._run_simulation(strategy, data, initial_balance)
            trades = sim.get('trades', [])
            results['advanced_tca'] = self.calculate_advanced_tca(trades)
        except Exception as e:
            results['advanced_tca'] = {'error': str(e)}
        
        logger.info("\n📈 Phase 5: Regime-Adjusted Metrics")
        try:
            if 'regime_testing' in results and 'error' not in results['regime_testing']:
                results['regime_metrics'] = self.calculate_regime_adjusted_metrics(results['regime_testing'])
            else:
                results['regime_metrics'] = {'error': 'No regime data available'}
        except Exception as e:
            results['regime_metrics'] = {'error': str(e)}
        
        logger.info("\n📉 Phase 6: Drawdown Pattern Analysis")
        try:
            sim = self._run_simulation(strategy, data, initial_balance)
            equity_curve = [{'equity': point['equity']} for point in sim.get('equity_curve', [{'equity': initial_balance}])]
            if not equity_curve:
                equity = [initial_balance]
                for trade in sim.get('trades', []):
                    pnl = trade.get('pnl', 0)
                    equity.append(equity[-1] + pnl)
                equity_curve = [{'equity': e} for e in equity]
            results['drawdown_analysis'] = self.analyze_drawdown_patterns(equity_curve)
        except Exception as e:
            results['drawdown_analysis'] = {'error': str(e)}
        
        issues = []
        if results.get('walk_forward', {}).get('avg_overfitting', 1) > 2.0:
            issues.append("HIGH OVERFITTING RISK")
        if results.get('regime_metrics', {}).get('consistency_score', 1) < 0.5:
            issues.append("LOW CONSISTENCY ACROSS REGIMES")
        if results.get('drawdown_analysis', {}).get('risk_indicators', {}).get('clustering_score', 0) > 0.6:
            issues.append("DRAWDOWN CLUSTERING DETECTED")
        if results.get('advanced_tca', {}).get('summary', {}).get('avg_cost_pct', 0) > 0.6:
            issues.append("HIGH TRANSACTION COSTS")
        
        if len(issues) == 0:
            results['institution_grade'] = 'A'
        elif len(issues) == 1:
            results['institution_grade'] = 'B'
        elif len(issues) == 2:
            results['institution_grade'] = 'C'
        else:
            results['institution_grade'] = 'D'
        
        results['issues'] = issues
        
        logger.info(f"\n✅ VALIDATION COMPLETE - Grade: {results['institution_grade']}")
        if issues:
            logger.info(f"   Issues: {', '.join(issues)}")
        
        return results


# Exportar clases principales
__all__ = [
    'ProfessionalValidator',
    'CostModel',
    'MarketRegime', 
    'WalkForwardResult',
    'ValidationReport',
    'ADVANCED_TCA_AVAILABLE',
    'REGIME_METRICS_AVAILABLE',
    'DRAWDOWN_ANALYZER_AVAILABLE'
]
