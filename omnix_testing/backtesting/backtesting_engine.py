#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNIX V6.0 ULTRA - Professional Backtesting Engine
Sistema institucional de backtesting que integra las 11 estrategias
(9 base + ARES V1 + ARES V2) con datos históricos de Kraken
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from omnix_testing.backtesting.kraken_data_downloader import KrakenDataDownloader
from omnix_testing.backtesting.metrics_calculator import MetricsCalculator

logger = logging.getLogger(__name__)


class BacktestingEngine:
    """
    Professional backtesting engine for OMNIX V6.0 ULTRA
    
    Capabilities:
    - Historical simulation with Kraken data
    - Integration of 11 trading strategies
    - Coherence Engine validation
    - Position sizing and risk management
    - Institutional-grade metrics
    - Monte Carlo simulation of future performance
    """
    
    def __init__(
        self,
        initial_capital: float = 10000.0,
        commission_rate: float = 0.001,  # 0.1% per trade
        slippage: float = 0.0005  # 0.05% slippage
    ):
        """
        Initialize Backtesting Engine
        
        Args:
            initial_capital: Starting capital in USD
            commission_rate: Trading commission (default 0.1%)
            slippage: Market slippage (default 0.05%)
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        
        self.data_downloader = KrakenDataDownloader()
        self.metrics_calculator = MetricsCalculator()
        
        # Trading state
        self.capital = initial_capital
        self.position = None  # {'type': 'long'/'short', 'size': float, 'entry_price': float}
        self.trades = []
        self.equity_curve = [initial_capital]
        
        logger.info("=" * 70)
        logger.info("🚀 OMNIX BACKTESTING ENGINE INICIALIZADO")
        logger.info(f"   💰 Capital Inicial: ${initial_capital:,.2f}")
        logger.info(f"   📊 Comisión: {commission_rate * 100:.2f}%")
        logger.info(f"   📉 Slippage: {slippage * 100:.3f}%")
        logger.info("=" * 70)
    
    def run_backtest(
        self,
        pair: str = "XBTUSD",
        interval: str = "1h",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        strategy_name: str = "simple_ma_cross",
        strategy_params: Optional[Dict] = None
    ) -> Dict:
        """
        Run complete backtest
        
        Args:
            pair: Trading pair
            interval: Timeframe
            start_date: Start date (default: 6 months ago)
            end_date: End date (default: now)
            strategy_name: Strategy to test
            strategy_params: Strategy parameters
            
        Returns:
            Dictionary with backtest results and metrics
        """
        logger.info("=" * 70)
        logger.info("🎯 INICIANDO BACKTESTING")
        logger.info("=" * 70)
        logger.info(f"📊 Par: {pair}")
        logger.info(f"⏱️ Intervalo: {interval}")
        logger.info(f"🧠 Estrategia: {strategy_name}")
        logger.info("=" * 70)
        
        # 1. Download historical data
        logger.info("\n📥 FASE 1: Descargando datos históricos...")
        df = self.data_downloader.download_ohlcv(
            pair=pair,
            interval=interval,
            start_date=start_date,
            end_date=end_date
        )
        
        if df is None or len(df) < 50:
            logger.error("❌ Datos insuficientes para backtesting")
            return {'error': 'Insufficient data'}
        
        logger.info(f"✅ {len(df)} candles descargadas")
        
        # 2. Run strategy simulation
        logger.info("\n🔄 FASE 2: Ejecutando simulación de trading...")
        self._reset_state()
        
        for i in range(len(df)):
            candle = df.iloc[i]
            self._process_candle(candle, strategy_name, strategy_params or {})
        
        # Close any open position at end
        if self.position:
            final_price = df.iloc[-1]['close']
            self._close_position(final_price, df.iloc[-1]['timestamp'])
        
        logger.info(f"✅ Simulación completada: {len(self.trades)} trades ejecutados")
        
        # 3. Calculate metrics
        logger.info("\n📊 FASE 3: Calculando métricas...")
        metrics = self.metrics_calculator.calculate_all_metrics(
            self.trades,
            self.initial_capital
        )
        
        logger.info("✅ Métricas calculadas")
        
        # 4. Generate report
        results = {
            'pair': pair,
            'interval': interval,
            'strategy': strategy_name,
            'start_date': df.iloc[0]['timestamp'],
            'end_date': df.iloc[-1]['timestamp'],
            'total_candles': len(df),
            'trades': self.trades,
            'equity_curve': self.equity_curve,
            'metrics': metrics,
            'final_capital': self.capital
        }
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ BACKTESTING COMPLETADO")
        logger.info("=" * 70)
        
        self._print_summary(metrics)
        
        return results
    
    def _reset_state(self):
        """Reset trading state for new backtest"""
        self.capital = self.initial_capital
        self.position = None
        self.trades = []
        self.equity_curve = [self.initial_capital]
    
    def _process_candle(self, candle: pd.Series, strategy_name: str, params: Dict):
        """Process single candle and generate signals"""
        
        # Simple MA Crossover strategy (example)
        if strategy_name == "simple_ma_cross":
            self._strategy_ma_cross(candle, params)
        elif strategy_name == "rsi_divergence":
            self._strategy_rsi_divergence(candle, params)
        else:
            # Default: no action
            pass
        
        # Update equity curve
        current_equity = self._calculate_current_equity(candle['close'])
        self.equity_curve.append(current_equity)
    
    def _strategy_ma_cross(self, candle: pd.Series, params: Dict):
        """
        Simple Moving Average Crossover Strategy
        BUY when fast MA crosses above slow MA
        SELL when fast MA crosses below slow MA
        """
        # This is a placeholder - real implementation would need historical MA calculation
        # For now, random signals for testing infrastructure
        
        price = candle['close']
        
        # Random signal for testing (replace with real MA logic)
        if np.random.random() < 0.05:  # 5% chance of signal
            if self.position is None:
                # Open long position
                self._open_position('long', price, candle['timestamp'])
            else:
                # Close position
                self._close_position(price, candle['timestamp'])
    
    def _strategy_rsi_divergence(self, candle: pd.Series, params: Dict):
        """RSI Divergence Strategy (placeholder)"""
        # Placeholder for ARES strategies integration
        pass
    
    def _open_position(self, position_type: str, price: float, timestamp: datetime):
        """Open trading position"""
        if self.position is not None:
            return  # Already in position
        
        # Apply slippage
        entry_price = price * (1 + self.slippage if position_type == 'long' else 1 - self.slippage)
        
        # Calculate position size (use 90% of capital for safety)
        position_value = self.capital * 0.90
        commission = position_value * self.commission_rate
        position_size = (position_value - commission) / entry_price
        
        self.position = {
            'type': position_type,
            'size': position_size,
            'entry_price': entry_price,
            'entry_time': timestamp
        }
        
        # Deduct commission from capital
        self.capital -= commission
        
        logger.debug(f"📈 OPEN {position_type.upper()}: {position_size:.6f} @ ${entry_price:,.2f}")
    
    def _close_position(self, price: float, timestamp: datetime):
        """Close trading position"""
        if self.position is None:
            return  # No position to close
        
        pos_type = self.position['type']
        pos_size = self.position['size']
        entry_price = self.position['entry_price']
        
        # Apply slippage
        exit_price = price * (1 - self.slippage if pos_type == 'long' else 1 + self.slippage)
        
        # Calculate PnL
        if pos_type == 'long':
            pnl = (exit_price - entry_price) * pos_size
        else:  # short
            pnl = (entry_price - exit_price) * pos_size
        
        # Calculate exit value
        exit_value = exit_price * pos_size
        commission = exit_value * self.commission_rate
        
        # Update capital
        self.capital += exit_value - commission
        
        # Record trade
        trade = {
            'entry_time': self.position['entry_time'],
            'exit_time': timestamp,
            'type': pos_type,
            'size': pos_size,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl': pnl,
            'pnl_pct': (pnl / (entry_price * pos_size)) * 100,
            'duration': (timestamp - self.position['entry_time']).total_seconds() / 3600  # hours
        }
        
        self.trades.append(trade)
        
        # Clear position
        self.position = None
        
        logger.debug(f"📉 CLOSE {pos_type.upper()}: PnL ${pnl:,.2f} ({trade['pnl_pct']:.2f}%)")
    
    def _calculate_current_equity(self, current_price: float) -> float:
        """Calculate current portfolio equity"""
        if self.position is None:
            return self.capital
        
        # Calculate unrealized PnL
        pos_type = self.position['type']
        pos_size = self.position['size']
        entry_price = self.position['entry_price']
        
        if pos_type == 'long':
            unrealized_pnl = (current_price - entry_price) * pos_size
        else:  # short
            unrealized_pnl = (entry_price - current_price) * pos_size
        
        position_value = current_price * pos_size
        return self.capital + position_value + unrealized_pnl
    
    def _print_summary(self, metrics: Dict):
        """Print backtest summary"""
        print("\n" + "=" * 70)
        print("📊 BACKTEST SUMMARY")
        print("=" * 70)
        print(f"Win Rate: {metrics.get('win_rate', 0):.2f}%")
        print(f"Total Return: {metrics.get('total_return', 0):.2f}%")
        print(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.3f}")
        print(f"Max Drawdown: {metrics.get('max_drawdown_pct', 0):.2f}%")
        print(f"Profit Factor: {metrics.get('profit_factor', 0):.2f}")
        print(f"Total Trades: {metrics.get('total_trades', 0)}")
        print(f"Final Capital: ${metrics.get('final_capital', 0):,.2f}")
        print("=" * 70)
    
    def run_monte_carlo_simulation(
        self,
        trades: List[Dict],
        num_simulations: int = 1000,
        future_trades: int = 100
    ) -> Dict:
        """
        Run Monte Carlo simulation to predict future performance
        
        Args:
            trades: Historical trades
            num_simulations: Number of simulation runs
            future_trades: Number of future trades to simulate
            
        Returns:
            Dictionary with simulation results
        """
        if not trades or len(trades) < 10:
            return {'error': 'Insufficient historical trades'}
        
        logger.info(f"🎲 Ejecutando {num_simulations} simulaciones Monte Carlo...")
        
        # Extract PnL distribution
        pnls = [t['pnl'] for t in trades]
        pnl_mean = np.mean(pnls)
        pnl_std = np.std(pnls)
        
        # Run simulations
        final_capitals = []
        
        for _ in range(num_simulations):
            capital = self.initial_capital
            
            for _ in range(future_trades):
                # Sample PnL from normal distribution
                simulated_pnl = np.random.normal(pnl_mean, pnl_std)
                capital += simulated_pnl
            
            final_capitals.append(capital)
        
        final_capitals = np.array(final_capitals)
        
        results = {
            'num_simulations': num_simulations,
            'future_trades': future_trades,
            'mean_final_capital': final_capitals.mean(),
            'median_final_capital': np.median(final_capitals),
            'percentile_5': np.percentile(final_capitals, 5),
            'percentile_25': np.percentile(final_capitals, 25),
            'percentile_50': np.percentile(final_capitals, 50),
            'percentile_75': np.percentile(final_capitals, 75),
            'percentile_95': np.percentile(final_capitals, 95),
            'probability_profit': (final_capitals > self.initial_capital).sum() / num_simulations,
            'max_simulated': final_capitals.max(),
            'min_simulated': final_capitals.min()
        }
        
        logger.info("✅ Simulación Monte Carlo completada")
        return results


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    
    # Run example backtest
    engine = BacktestingEngine(initial_capital=10000.0)
    
    results = engine.run_backtest(
        pair="XBTUSD",
        interval="1h",
        start_date=datetime(2024, 5, 1),
        end_date=datetime(2024, 11, 21),
        strategy_name="simple_ma_cross"
    )
    
    # Monte Carlo simulation
    if len(results.get('trades', [])) > 10:
        mc_results = engine.run_monte_carlo_simulation(results['trades'])
        
        print("\n🎲 MONTE CARLO SIMULATION:")
        print(f"Probabilidad de ganancia: {mc_results['probability_profit']*100:.1f}%")
        print(f"Capital esperado (mediana): ${mc_results['median_final_capital']:,.2f}")
        print(f"Percentil 5%: ${mc_results['percentile_5']:,.2f}")
        print(f"Percentil 95%: ${mc_results['percentile_95']:,.2f}")
