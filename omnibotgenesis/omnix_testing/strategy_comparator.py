#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNIX V6.0 ULTRA - Strategy Comparator
Compara ARES V1/V2 vs Buy & Hold en eventos históricos
Sistema PREMIUM para demostrar ventaja competitiva a inversionistas
Desarrollado por Harold Nunes - Noviembre 2025
"""

import logging
from datetime import datetime
from typing import Dict, List
import json
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)


class StrategyComparator:
    """
    Compara rendimiento de múltiples estrategias
    
    Características:
    - Comparación lado a lado
    - Métricas de ventaja competitiva
    - Visualización de resultados
    - Reportes para inversionistas
    """
    
    def __init__(self, backtesting_engine=None):
        """
        Initialize Strategy Comparator
        
        Args:
            backtesting_engine: BacktestingEngine instance
        """
        self.backtesting_engine = backtesting_engine
        self.comparisons = []
        
        # Create reports directory
        self.reports_dir = Path("omnix_testing/reports/comparisons")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("📊 Strategy Comparator inicializado")
    
    def compare_strategies(
        self,
        strategies: List[str],
        pair: str = "XBTUSD",
        interval: str = "4h",
        start_date: datetime = None,
        end_date: datetime = None,
        initial_capital: float = 10000.0
    ) -> Dict:
        """
        Compara múltiples estrategias en el mismo período
        
        Args:
            strategies: Lista de nombres de estrategias
            pair: Par de trading
            interval: Timeframe
            start_date: Fecha inicio
            end_date: Fecha fin
            initial_capital: Capital inicial
            
        Returns:
            Dictionary con resultados comparativos
        """
        if not self.backtesting_engine:
            logger.error("❌ BacktestingEngine no configurado")
            return {'error': 'No backtesting engine'}
        
        logger.info("=" * 70)
        logger.info("🔬 COMPARACIÓN DE ESTRATEGIAS")
        logger.info("=" * 70)
        logger.info(f"📊 Estrategias: {', '.join(strategies)}")
        logger.info(f"📅 Período: {start_date.date()} → {end_date.date()}")
        logger.info("=" * 70)
        
        results = {}
        
        for strategy in strategies:
            logger.info(f"\n🎯 Ejecutando: {strategy}")
            
            try:
                result = self.backtesting_engine.run_backtest(
                    pair=pair,
                    interval=interval,
                    start_date=start_date,
                    end_date=end_date,
                    strategy_name=strategy
                )
                
                results[strategy] = result
                
                metrics = result.get('metrics', {})
                logger.info(f"   ✅ Return: {metrics.get('total_return', 0):.2f}%")
                logger.info(f"   ✅ Sharpe: {metrics.get('sharpe_ratio', 0):.3f}")
                
            except Exception as e:
                logger.error(f"   ❌ Error: {str(e)}")
                results[strategy] = {'error': str(e)}
        
        # Generate comparison
        comparison = self._generate_comparison(results, strategies)
        
        # Save results
        self._save_comparison(comparison, strategies)
        
        # Print summary
        self._print_comparison_summary(comparison)
        
        return comparison
    
    def ares_vs_buyhold(
        self,
        start_date: datetime,
        end_date: datetime,
        ares_version: str = "v1"
    ) -> Dict:
        """
        Comparación específica: ARES vs Buy & Hold
        
        Args:
            start_date: Fecha inicio
            end_date: Fecha fin
            ares_version: "v1" (swing) o "v2" (scalping)
            
        Returns:
            Dictionary con resultados comparativos
        """
        logger.info("=" * 70)
        logger.info(f"⚡ ARES {ares_version.upper()} VS BUY & HOLD")
        logger.info("=" * 70)
        
        # Select strategy and timeframe
        if ares_version == "v1":
            ares_strategy = "ares_v1_swing"
            interval = "4h"
        elif ares_version == "v2":
            ares_strategy = "ares_v2_scalping"
            interval = "1m"
        else:
            logger.error("❌ Versión ARES inválida (usa 'v1' o 'v2')")
            return {'error': 'Invalid ARES version'}
        
        strategies = [ares_strategy, "buy_hold"]
        
        return self.compare_strategies(
            strategies=strategies,
            interval=interval,
            start_date=start_date,
            end_date=end_date
        )
    
    def _generate_comparison(self, results: Dict, strategies: List[str]) -> Dict:
        """Generate comparative analysis"""
        comparison = {
            'timestamp': datetime.now().isoformat(),
            'strategies': strategies,
            'results': {},
            'winner': None,
            'metrics_comparison': {}
        }
        
        # Extract metrics for each strategy
        for strategy in strategies:
            if strategy in results and 'metrics' in results[strategy]:
                metrics = results[strategy]['metrics']
                comparison['results'][strategy] = {
                    'total_return': metrics.get('total_return', 0),
                    'annual_return': metrics.get('annual_return', 0),
                    'win_rate': metrics.get('win_rate', 0),
                    'sharpe_ratio': metrics.get('sharpe_ratio', 0),
                    'sortino_ratio': metrics.get('sortino_ratio', 0),
                    'max_drawdown': metrics.get('max_drawdown_pct', 0),
                    'profit_factor': metrics.get('profit_factor', 0),
                    'total_trades': metrics.get('total_trades', 0),
                    'final_capital': metrics.get('final_capital', 0)
                }
        
        # Determine winner based on Sharpe Ratio
        if comparison['results']:
            winner = max(
                comparison['results'].items(),
                key=lambda x: x[1].get('sharpe_ratio', 0)
            )
            comparison['winner'] = winner[0]
            comparison['winner_metrics'] = winner[1]
        
        # Calculate relative performance
        if len(comparison['results']) >= 2:
            strategies_list = list(comparison['results'].keys())
            strategy_a = strategies_list[0]
            strategy_b = strategies_list[1]
            
            metrics_a = comparison['results'][strategy_a]
            metrics_b = comparison['results'][strategy_b]
            
            comparison['relative_performance'] = {
                'return_difference': metrics_a['total_return'] - metrics_b['total_return'],
                'sharpe_improvement': metrics_a['sharpe_ratio'] - metrics_b['sharpe_ratio'],
                'drawdown_difference': metrics_a['max_drawdown'] - metrics_b['max_drawdown'],
                'better_strategy': strategy_a if metrics_a['sharpe_ratio'] > metrics_b['sharpe_ratio'] else strategy_b
            }
        
        return comparison
    
    def _print_comparison_summary(self, comparison: Dict):
        """Print comparison summary"""
        print("\n" + "=" * 70)
        print("📊 RESUMEN DE COMPARACIÓN")
        print("=" * 70)
        
        for strategy, metrics in comparison['results'].items():
            print(f"\n🎯 {strategy.upper()}")
            print(f"   Return Total: {metrics['total_return']:.2f}%")
            print(f"   Return Anual: {metrics['annual_return']:.2f}%")
            print(f"   Win Rate: {metrics['win_rate']:.1f}%")
            print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
            print(f"   Max Drawdown: {metrics['max_drawdown']:.2f}%")
            print(f"   Profit Factor: {metrics['profit_factor']:.2f}")
            print(f"   Trades: {metrics['total_trades']}")
        
        if comparison.get('winner'):
            print(f"\n🏆 GANADOR: {comparison['winner'].upper()}")
            print(f"   Mejor Sharpe Ratio: {comparison['winner_metrics']['sharpe_ratio']:.3f}")
        
        if 'relative_performance' in comparison:
            rel = comparison['relative_performance']
            print(f"\n📈 VENTAJA COMPETITIVA:")
            print(f"   Diferencia Return: {rel['return_difference']:+.2f}%")
            print(f"   Mejora Sharpe: {rel['sharpe_improvement']:+.3f}")
            print(f"   Diferencia Drawdown: {rel['drawdown_difference']:+.2f}%")
        
        print("=" * 70)
    
    def _save_comparison(self, comparison: Dict, strategies: List[str]):
        """Save comparison results to JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comparison_{'_vs_'.join(strategies)}_{timestamp}.json"
        filepath = self.reports_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(comparison, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n💾 Comparación guardada: {filepath}")
    
    def generate_comparison_table(self, comparison: Dict) -> pd.DataFrame:
        """
        Generate DataFrame table for easy visualization
        
        Args:
            comparison: Comparison results
            
        Returns:
            pandas DataFrame with comparison table
        """
        if not comparison.get('results'):
            return pd.DataFrame()
        
        data = []
        for strategy, metrics in comparison['results'].items():
            data.append({
                'Strategy': strategy,
                'Total Return %': metrics['total_return'],
                'Annual Return %': metrics['annual_return'],
                'Win Rate %': metrics['win_rate'],
                'Sharpe Ratio': metrics['sharpe_ratio'],
                'Max Drawdown %': metrics['max_drawdown'],
                'Profit Factor': metrics['profit_factor'],
                'Total Trades': metrics['total_trades'],
                'Final Capital': metrics['final_capital']
            })
        
        df = pd.DataFrame(data)
        return df


def main():
    """Main execution for testing"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from omnix_testing.backtesting.backtesting_engine import BacktestingEngine
    from datetime import timedelta
    
    # Initialize
    engine = BacktestingEngine(initial_capital=10000.0)
    comparator = StrategyComparator(backtesting_engine=engine)
    
    # Example comparison
    print("\n🔬 Ejecutando comparación ARES V1 vs Buy & Hold (6 meses)...")
    
    comparison = comparator.ares_vs_buyhold(
        start_date=datetime.now() - timedelta(days=180),
        end_date=datetime.now(),
        ares_version="v1"
    )
    
    # Generate table
    df = comparator.generate_comparison_table(comparison)
    print("\n📊 TABLA COMPARATIVA:")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
