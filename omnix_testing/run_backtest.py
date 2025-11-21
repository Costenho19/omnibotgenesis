#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNIX V6.0 ULTRA - Backtesting Runner Script
Script profesional para ejecutar backtests y generar reportes para inversionistas
Desarrollado por Harold Nunes - Noviembre 2025
"""

import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from omnix_testing.backtesting.backtesting_engine import BacktestingEngine
from omnix_testing.backtesting.kraken_data_downloader import KrakenDataDownloader
from omnix_testing.backtesting.metrics_calculator import MetricsCalculator


def setup_logging():
    """Configure professional logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('omnix_testing/reports/backtest_log.txt', mode='w')
        ]
    )


def run_ares_v1_backtest():
    """
    Run ARES V1 Swing Trading Strategy Backtest
    Target: 74-82% win rate
    """
    print("\n" + "=" * 70)
    print("🧬 ARES V1 - SWING TRADING STRATEGY BACKTEST")
    print("=" * 70)
    
    engine = BacktestingEngine(initial_capital=10000.0)
    
    # Run 6-month backtest
    results = engine.run_backtest(
        pair="XBTUSD",
        interval="4h",  # Swing trading - 4H timeframe
        start_date=datetime.now() - timedelta(days=180),
        end_date=datetime.now(),
        strategy_name="ares_v1_swing",
        strategy_params={
            'rsi_period': 14,
            'quantum_volatility_min': 18.0,
            'quantum_volatility_max': 86.0
        }
    )
    
    return results


def run_ares_v2_backtest():
    """
    Run ARES V2 Scalping M1 Strategy Backtest
    Target: 85% win rate
    """
    print("\n" + "=" * 70)
    print("🧨 ARES V2 - SCALPING M1 STRATEGY BACKTEST")
    print("=" * 70)
    
    engine = BacktestingEngine(initial_capital=10000.0)
    
    # Run 1-month backtest (M1 data is very heavy)
    results = engine.run_backtest(
        pair="XBTUSD",
        interval="1m",  # Scalping - 1 minute timeframe
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now(),
        strategy_name="ares_v2_scalping",
        strategy_params={
            'rsi_period': 5,
            'stop_loss': -0.28,
            'take_profit_1': 0.85
        }
    )
    
    return results


def run_benchmark_comparison():
    """
    Run Bitcoin Buy & Hold strategy for comparison
    """
    print("\n" + "=" * 70)
    print("📊 BITCOIN BUY & HOLD BENCHMARK")
    print("=" * 70)
    
    engine = BacktestingEngine(initial_capital=10000.0)
    
    results = engine.run_backtest(
        pair="XBTUSD",
        interval="1d",
        start_date=datetime.now() - timedelta(days=180),
        end_date=datetime.now(),
        strategy_name="buy_hold"
    )
    
    return results


def generate_investor_report(results: dict):
    """
    Generate professional report for investors
    """
    print("\n" + "=" * 70)
    print("📄 GENERANDO REPORTE PARA INVERSIONISTAS")
    print("=" * 70)
    
    metrics = results.get('metrics', {})
    
    print("\n🎯 RESULTADOS CLAVE:")
    print(f"  Win Rate: {metrics.get('win_rate', 0):.2f}%")
    print(f"  Total Return: {metrics.get('total_return', 0):.2f}%")
    print(f"  Annual Return: {metrics.get('annual_return', 0):.2f}%")
    print(f"  Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.3f}")
    print(f"  Sortino Ratio: {metrics.get('sortino_ratio', 0):.3f}")
    print(f"  Max Drawdown: {metrics.get('max_drawdown_pct', 0):.2f}%")
    print(f"  Profit Factor: {metrics.get('profit_factor', 0):.2f}")
    print(f"  Total Trades: {metrics.get('total_trades', 0)}")
    
    print("\n💰 CAPITAL:")
    print(f"  Inicial: ${metrics.get('initial_capital', 0):,.2f}")
    print(f"  Final: ${metrics.get('final_capital', 0):,.2f}")
    print(f"  Ganancia: ${metrics.get('total_pnl', 0):,.2f}")
    
    print("\n⏱️ PERIODO:")
    print(f"  Inicio: {results.get('start_date', 'N/A')}")
    print(f"  Fin: {results.get('end_date', 'N/A')}")
    print(f"  Días: {metrics.get('trading_days', 0)}")
    
    print("=" * 70)


def main():
    """Main execution"""
    setup_logging()
    
    print("\n" + "=" * 80)
    print("🚀 OMNIX V6.0 ULTRA - PROFESSIONAL BACKTESTING SYSTEM")
    print("   Sistema Institucional de Validación para Inversionistas")
    print("   Desarrollado por Harold Nunes - Noviembre 2025")
    print("=" * 80)
    
    # Test data downloader first
    print("\n📥 Verificando conexión con Kraken API...")
    downloader = KrakenDataDownloader()
    
    test_df = downloader.download_ohlcv(
        pair="XBTUSD",
        interval="1h",
        start_date=datetime.now() - timedelta(days=7),
        end_date=datetime.now()
    )
    
    if test_df is not None and len(test_df) > 0:
        print(f"✅ Conexión exitosa: {len(test_df)} candles descargadas")
        summary = downloader.get_summary(test_df)
        print(f"   Periodo: {summary['start_date']} → {summary['end_date']}")
        print(f"   Precio: ${summary['price_min']:,.0f} - ${summary['price_max']:,.0f}")
    else:
        print("❌ Error de conexión - verificar internet y API Kraken")
        return
    
    # Menu
    print("\n" + "=" * 70)
    print("📋 SELECCIONA BACKTESTING A EJECUTAR:")
    print("=" * 70)
    print("1. ARES V1 - Swing Trading (4H, 6 meses)")
    print("2. ARES V2 - Scalping M1 (1M, 1 mes)")
    print("3. Bitcoin Buy & Hold - Benchmark (1D, 6 meses)")
    print("4. EJECUTAR TODOS (completo para inversionistas)")
    print("=" * 70)
    
    choice = input("\nSelecciona opción (1-4): ").strip()
    
    if choice == '1':
        results = run_ares_v1_backtest()
        generate_investor_report(results)
    
    elif choice == '2':
        results = run_ares_v2_backtest()
        generate_investor_report(results)
    
    elif choice == '3':
        results = run_benchmark_comparison()
        generate_investor_report(results)
    
    elif choice == '4':
        print("\n🚀 EJECUTANDO SUITE COMPLETA DE BACKTESTING...")
        
        results_ares_v1 = run_ares_v1_backtest()
        generate_investor_report(results_ares_v1)
        
        results_ares_v2 = run_ares_v2_backtest()
        generate_investor_report(results_ares_v2)
        
        results_benchmark = run_benchmark_comparison()
        generate_investor_report(results_benchmark)
        
        print("\n" + "=" * 70)
        print("✅ SUITE COMPLETA EJECUTADA")
        print("   Todos los reportes generados para presentación a inversionistas")
        print("=" * 70)
    
    else:
        print("❌ Opción inválida")
        return
    
    print("\n" + "=" * 80)
    print("✅ BACKTESTING COMPLETADO EXITOSAMENTE")
    print("   📊 Reportes disponibles en: omnix_testing/reports/")
    print("   💼 Listo para presentar a inversionistas")
    print("=" * 80)


if __name__ == "__main__":
    main()
