"""
OMNIX On-Chain Data Service V6.5
=================================

Servicio principal que orquesta todos los componentes de datos on-chain:
- WhaleTracker: Seguimiento de transacciones grandes
- ExchangeFlowAnalyzer: Análisis de flujos de exchange
- NetworkMetricsCollector: Métricas de salud de red

Genera señales consolidadas para el Non-Markovian Memory Kernel.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass

from .models import (
    OnChainSignal,
    WhaleTransaction,
    ExchangeFlow,
    NetworkMetrics,
    SmartMoneySignal,
    MarketBias,
    SignalStrength
)
from .whale_tracker import WhaleTracker
from .exchange_flow_analyzer import ExchangeFlowAnalyzer
from .network_metrics import NetworkMetricsCollector

logger = logging.getLogger('OMNIX.OnChain')

# Singleton instance
_on_chain_service: Optional['OnChainDataService'] = None
_kernel_instance = None  # Will be set by bot


def set_kernel_instance(kernel):
    """Set the Non-Markovian Kernel instance for on-chain integration."""
    global _kernel_instance
    _kernel_instance = kernel
    logger.info("🔗 Kernel instance set for on-chain integration")


def get_on_chain_service(db=None) -> 'OnChainDataService':
    """
    Obtiene la instancia singleton del OnChainDataService.
    
    Args:
        db: Opcional - instancia de DatabaseService para persistencia
        
    Returns:
        OnChainDataService instance
    """
    global _on_chain_service
    if _on_chain_service is None:
        _on_chain_service = OnChainDataService(db=db)
    return _on_chain_service


class OnChainDataService:
    """
    Servicio principal de datos on-chain V6.5.
    
    Orquesta la recolección y análisis de datos on-chain
    para generar señales de trading.
    
    Componentes:
    - WhaleTracker: ClankApp + Arkham para transacciones whale
    - ExchangeFlowAnalyzer: Flujos a/desde exchanges
    - NetworkMetricsCollector: Métricas de red
    
    Uso:
        service = get_on_chain_service()
        signal = await service.get_consolidated_signal('BTC')
        print(f"On-chain bias: {signal.market_bias}")
    """
    
    VERSION = "6.5.4"
    
    # Símbolos soportados con tracking completo
    SUPPORTED_SYMBOLS = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'LTC', 'MATIC', 'AVAX']
    
    # Pesos para señal compuesta
    DEFAULT_WEIGHTS = {
        'whale': 0.30,
        'exchange_flow': 0.35,
        'network': 0.15,
        'smart_money': 0.20
    }
    
    def __init__(
        self,
        db=None,
        signal_callback: Optional[Callable[[OnChainSignal], None]] = None,
        cache_ttl_seconds: int = 300
    ):
        """
        Inicializa el OnChainDataService.
        
        Args:
            db: Instancia de DatabaseService para persistencia
            signal_callback: Callback para nuevas señales
            cache_ttl_seconds: TTL del cache
        """
        self.db = db
        self.signal_callback = signal_callback
        self.cache_ttl = cache_ttl_seconds
        
        # Componentes
        self.whale_tracker = WhaleTracker(cache_ttl_seconds=cache_ttl_seconds)
        self.flow_analyzer = ExchangeFlowAnalyzer()
        self.metrics_collector = NetworkMetricsCollector(cache_ttl_seconds=cache_ttl_seconds)
        
        # Cache de señales
        self._signal_cache: Dict[str, tuple] = {}
        self._last_update: Dict[str, datetime] = {}
        
        # Historial de señales para persistencia
        self._signal_history: List[OnChainSignal] = []
        self.max_history = 1000
        
        # Estado
        self.is_running = False
        self._update_task: Optional[asyncio.Task] = None
        
        logger.info(f"🔗 OnChainDataService V{self.VERSION} initialized")
        logger.info(f"   Supported symbols: {', '.join(self.SUPPORTED_SYMBOLS)}")
    
    async def get_whale_data(
        self,
        symbol: str,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Obtiene datos de actividad whale.
        
        Args:
            symbol: Símbolo del activo
            hours: Ventana de tiempo
            
        Returns:
            Dict con transacciones y análisis
        """
        transactions = await self.whale_tracker.get_whale_transactions(
            symbol, hours=hours
        )
        
        analysis = self.whale_tracker.analyze_whale_activity(transactions)
        
        return {
            'transactions': [tx.to_dict() for tx in transactions],
            'analysis': analysis,
            'symbol': symbol,
            'hours': hours,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def get_exchange_flows(
        self,
        symbol: str,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Obtiene análisis de flujos de exchange.
        
        Args:
            symbol: Símbolo del activo
            hours: Período de análisis
            
        Returns:
            Dict con flujos y señales
        """
        # Primero obtener transacciones whale
        transactions = await self.whale_tracker.get_whale_transactions(
            symbol, hours=hours
        )
        
        # Analizar flujos
        flow = self.flow_analyzer.analyze_from_transactions(
            transactions, symbol, period_hours=hours
        )
        
        signal = self.flow_analyzer.get_flow_signal(flow)
        
        return {
            'flow': flow.to_dict(),
            'signal': signal,
            'historical': self.flow_analyzer.get_historical_summary(symbol, hours),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def get_network_metrics(
        self,
        symbol: str
    ) -> Dict[str, Any]:
        """
        Obtiene métricas de red.
        
        Args:
            symbol: Símbolo del activo
            
        Returns:
            Dict con métricas e indicadores
        """
        metrics = await self.metrics_collector.get_metrics(symbol)
        
        if metrics:
            indicators = self.metrics_collector.get_health_indicators(metrics)
            return {
                'metrics': metrics.to_dict(),
                'indicators': [
                    {
                        'metric': ind.metric,
                        'value': ind.value,
                        'score': ind.normalized_score,
                        'trend': ind.trend,
                        'interpretation': ind.interpretation
                    }
                    for ind in indicators
                ],
                'timestamp': datetime.utcnow().isoformat()
            }
        
        return {
            'metrics': None,
            'indicators': [],
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def get_consolidated_signal(
        self,
        symbol: str,
        hours: int = 24,
        weights: Optional[Dict[str, float]] = None
    ) -> OnChainSignal:
        """
        Genera señal consolidada on-chain.
        
        Combina:
        - Actividad whale
        - Flujos de exchange
        - Métricas de red
        
        Args:
            symbol: Símbolo del activo
            hours: Ventana de tiempo
            weights: Pesos para componentes
            
        Returns:
            OnChainSignal consolidada
        """
        # Verificar cache
        cache_key = f"{symbol}_{hours}"
        if cache_key in self._signal_cache:
            timestamp, signal = self._signal_cache[cache_key]
            if datetime.utcnow() - timestamp < timedelta(seconds=self.cache_ttl):
                return signal
        
        if weights is None:
            weights = self.DEFAULT_WEIGHTS
        
        # Recolectar datos en paralelo
        whale_task = self.whale_tracker.get_whale_transactions(symbol, hours)
        metrics_task = self.metrics_collector.get_metrics(symbol)
        
        transactions, network_metrics = await asyncio.gather(
            whale_task, metrics_task
        )
        
        # Análisis de whales
        whale_analysis = self.whale_tracker.analyze_whale_activity(transactions)
        
        # Análisis de flujos
        flow = self.flow_analyzer.analyze_from_transactions(
            transactions, symbol, period_hours=hours
        )
        flow_signal = self.flow_analyzer.get_flow_signal(flow)
        
        # Crear señal consolidada
        signal = OnChainSignal(
            symbol=symbol,
            timestamp=datetime.utcnow(),
            whale_activity_score=whale_analysis['whale_activity_score'],
            exchange_flow_score=flow_signal.get('exchange_flow_score', 0.0),
            network_health_score=network_metrics.network_health_score if network_metrics else 0.5,
            smart_money_score=0.0,  # TODO: Implementar smart money tracking
            whale_transactions=transactions,
            exchange_flows=[flow],
            network_metrics=network_metrics
        )
        
        # Calcular compuesto
        signal.calculate_composite(weights)
        
        # Cache
        self._signal_cache[cache_key] = (datetime.utcnow(), signal)
        
        # Historial
        self._signal_history.append(signal)
        if len(self._signal_history) > self.max_history:
            self._signal_history.pop(0)
        
        # Callback
        if self.signal_callback:
            try:
                self.signal_callback(signal)
            except Exception as e:
                logger.error(f"Signal callback error: {e}")
        
        # Persistir si hay DB
        if self.db:
            await self._persist_signal(signal)
        
        # ========================================================
        # KERNEL INTEGRATION V6.5
        # Push signal to Non-Markovian Kernel for enhanced analysis
        # ========================================================
        global _kernel_instance
        if _kernel_instance is not None:
            try:
                kernel_format = signal.to_kernel_format()
                _kernel_instance.integrate_on_chain_signal(kernel_format)
                logger.debug(f"🔗 On-chain signal pushed to kernel: {kernel_format.get('bias')}")
            except Exception as e:
                logger.warning(f"Kernel integration error: {e}")
        
        logger.info(
            f"🔗 On-chain signal for {symbol}: "
            f"bias={signal.market_bias.value}, "
            f"score={signal.composite_score:.3f}, "
            f"confidence={signal.confidence:.2f}"
        )
        
        return signal
    
    async def get_multi_symbol_signals(
        self,
        symbols: Optional[List[str]] = None,
        hours: int = 24
    ) -> Dict[str, OnChainSignal]:
        """
        Obtiene señales para múltiples símbolos.
        
        Args:
            symbols: Lista de símbolos (default: SUPPORTED_SYMBOLS)
            hours: Ventana de tiempo
            
        Returns:
            Dict de símbolo -> OnChainSignal
        """
        if symbols is None:
            symbols = self.SUPPORTED_SYMBOLS[:3]  # Top 3 por defecto
        
        tasks = [
            self.get_consolidated_signal(sym, hours)
            for sym in symbols
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        signals = {}
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                logger.error(f"Error getting signal for {symbol}: {result}")
            else:
                signals[symbol] = result
        
        return signals
    
    async def _persist_signal(self, signal: OnChainSignal):
        """Persiste señal en base de datos (async, non-blocking)"""
        try:
            if hasattr(self.db, '_get_connection'):
                import threading
                
                def persist():
                    try:
                        conn = self.db._get_connection()
                        if conn:
                            cursor = conn.cursor()
                            cursor.execute('''
                                INSERT INTO on_chain_signals 
                                (symbol, timestamp, whale_score, flow_score, 
                                 network_score, smart_money_score, composite_score,
                                 market_bias, signal_strength, confidence)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ''', (
                                signal.symbol,
                                signal.timestamp,
                                signal.whale_activity_score,
                                signal.exchange_flow_score,
                                signal.network_health_score,
                                signal.smart_money_score,
                                signal.composite_score,
                                signal.market_bias.value,
                                signal.signal_strength.value,
                                signal.confidence
                            ))
                            conn.commit()
                            cursor.close()
                            conn.close()
                    except Exception as e:
                        logger.debug(f"Signal persist error: {e}")
                
                thread = threading.Thread(target=persist, daemon=True)
                thread.start()
        except Exception as e:
            logger.debug(f"Failed to persist signal: {e}")
    
    def to_kernel_format(self, signal: OnChainSignal) -> Dict[str, Any]:
        """
        Convierte señal a formato para Non-Markovian Kernel.
        
        Args:
            signal: OnChainSignal
            
        Returns:
            Dict en formato kernel
        """
        return signal.to_kernel_format()
    
    async def start_monitoring(
        self,
        symbols: Optional[List[str]] = None,
        interval_seconds: int = 300
    ):
        """
        Inicia monitoreo continuo de señales on-chain.
        
        Args:
            symbols: Símbolos a monitorear
            interval_seconds: Intervalo entre actualizaciones
        """
        if self.is_running:
            logger.warning("On-chain monitoring already running")
            return
        
        self.is_running = True
        symbols = symbols or self.SUPPORTED_SYMBOLS[:3]
        
        logger.info(f"🚀 Starting on-chain monitoring: {symbols}, interval={interval_seconds}s")
        
        async def monitor_loop():
            while self.is_running:
                try:
                    await self.get_multi_symbol_signals(symbols)
                    await asyncio.sleep(interval_seconds)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Monitoring error: {e}")
                    await asyncio.sleep(60)
        
        self._update_task = asyncio.create_task(monitor_loop())
    
    async def stop_monitoring(self):
        """Detiene el monitoreo continuo"""
        self.is_running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 On-chain monitoring stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene estado del servicio"""
        return {
            'version': self.VERSION,
            'is_running': self.is_running,
            'supported_symbols': self.SUPPORTED_SYMBOLS,
            'cached_signals': len(self._signal_cache),
            'signal_history_size': len(self._signal_history),
            'components': {
                'whale_tracker': 'active',
                'flow_analyzer': 'active',
                'metrics_collector': 'active'
            },
            'last_updates': {
                symbol: ts.isoformat() 
                for symbol, ts in self._last_update.items()
            }
        }
    
    async def close(self):
        """Cierra el servicio y libera recursos"""
        await self.stop_monitoring()
        await self.whale_tracker.close()
        await self.metrics_collector.close()
        logger.info("OnChainDataService closed")
