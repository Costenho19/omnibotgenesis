"""
OMNIX Exchange Flow Analyzer
============================

Análisis de flujos de fondos hacia/desde exchanges.

Señales clave:
- High Inflows → Presión de venta (bearish)
- High Outflows → Acumulación/HODL (bullish)
- Sudden spikes → Posible movimiento grande inminente

Fuentes:
- Agregación de whale transactions
- APIs públicas de exchanges
- CryptoQuant (premium opcional)
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

from .models import (
    ExchangeFlow,
    WhaleTransaction,
    FlowDirection,
    MarketBias,
    SignalStrength
)

logger = logging.getLogger('OMNIX.OnChain.ExchangeFlowAnalyzer')


@dataclass
class FlowHistory:
    """Historial de flujos para análisis de tendencia"""
    symbol: str
    flows: List[ExchangeFlow] = field(default_factory=list)
    max_history: int = 168  # 7 días de datos horarios
    
    def add(self, flow: ExchangeFlow):
        self.flows.append(flow)
        if len(self.flows) > self.max_history:
            self.flows.pop(0)
    
    def get_trend(self, hours: int = 24) -> str:
        """Calcula tendencia de flujos"""
        if len(self.flows) < 2:
            return "insufficient_data"
        
        recent = [f for f in self.flows[-hours:]]
        if len(recent) < 2:
            return "insufficient_data"
        
        # Comparar primera y segunda mitad
        mid = len(recent) // 2
        first_half_avg = sum(f.net_flow for f in recent[:mid]) / mid
        second_half_avg = sum(f.net_flow for f in recent[mid:]) / (len(recent) - mid)
        
        if second_half_avg > first_half_avg * 1.2:
            return "increasing_inflows"  # Más venta
        elif second_half_avg < first_half_avg * 0.8:
            return "increasing_outflows"  # Más acumulación
        else:
            return "stable"


class ExchangeFlowAnalyzer:
    """
    Analiza flujos de fondos hacia/desde exchanges.
    
    Principio fundamental:
    - Fondos entrando a exchanges = Preparando para vender = Bearish
    - Fondos saliendo de exchanges = HODL/Acumulación = Bullish
    
    Uso:
        analyzer = ExchangeFlowAnalyzer()
        flow = analyzer.analyze_from_transactions(whale_txs, 'BTC', hours=24)
        print(f"Market bias: {flow.market_bias}")
    """
    
    # Exchanges principales para tracking
    MAJOR_EXCHANGES = [
        'Binance', 'Coinbase', 'Kraken', 'FTX', 
        'Bitfinex', 'OKX', 'Huobi', 'Gate.io',
        'KuCoin', 'Bybit', 'Gemini', 'Bitstamp'
    ]
    
    # Umbrales para señales significativas
    SIGNIFICANT_FLOW_THRESHOLDS = {
        'BTC': 50_000_000,   # $50M
        'ETH': 25_000_000,   # $25M
        'SOL': 10_000_000,   # $10M
        'default': 10_000_000
    }
    
    def __init__(self):
        self.flow_history: Dict[str, FlowHistory] = {}
        logger.info("📊 ExchangeFlowAnalyzer initialized")
    
    def _get_threshold(self, symbol: str) -> float:
        """Obtiene umbral de flujo significativo"""
        return self.SIGNIFICANT_FLOW_THRESHOLDS.get(
            symbol.upper(), 
            self.SIGNIFICANT_FLOW_THRESHOLDS['default']
        )
    
    def analyze_from_transactions(
        self,
        transactions: List[WhaleTransaction],
        symbol: str,
        period_hours: int = 24,
        exchange: str = "aggregate"
    ) -> ExchangeFlow:
        """
        Analiza flujos de exchange a partir de transacciones de ballenas.
        
        Args:
            transactions: Lista de WhaleTransaction
            symbol: Símbolo del activo
            period_hours: Período de análisis
            exchange: Exchange específico o "aggregate"
            
        Returns:
            ExchangeFlow con análisis completo
        """
        # Filtrar transacciones relevantes
        if exchange != "aggregate":
            relevant_txs = [
                tx for tx in transactions
                if tx.from_label == exchange or tx.to_label == exchange
            ]
        else:
            relevant_txs = [tx for tx in transactions if tx.is_exchange_related]
        
        # Calcular inflows (hacia exchange)
        inflow_txs = [
            tx for tx in relevant_txs 
            if tx.flow_direction == FlowDirection.INFLOW
        ]
        inflow_amount = sum(tx.amount for tx in inflow_txs)
        inflow_usd = sum(tx.amount_usd for tx in inflow_txs)
        
        # Calcular outflows (desde exchange)
        outflow_txs = [
            tx for tx in relevant_txs 
            if tx.flow_direction == FlowDirection.OUTFLOW
        ]
        outflow_amount = sum(tx.amount for tx in outflow_txs)
        outflow_usd = sum(tx.amount_usd for tx in outflow_txs)
        
        # Flujo neto
        net_flow = inflow_amount - outflow_amount
        net_flow_usd = inflow_usd - outflow_usd
        
        flow = ExchangeFlow(
            symbol=symbol,
            exchange=exchange,
            period_hours=period_hours,
            inflow_amount=inflow_amount,
            inflow_usd=inflow_usd,
            inflow_count=len(inflow_txs),
            outflow_amount=outflow_amount,
            outflow_usd=outflow_usd,
            outflow_count=len(outflow_txs),
            net_flow=net_flow,
            net_flow_usd=net_flow_usd
        )
        
        # Guardar en historial
        if symbol not in self.flow_history:
            self.flow_history[symbol] = FlowHistory(symbol=symbol)
        self.flow_history[symbol].add(flow)
        
        return flow
    
    def get_flow_signal(
        self,
        flow: ExchangeFlow,
        historical_context: bool = True
    ) -> Dict[str, Any]:
        """
        Genera señal de trading basada en flujos.
        
        Args:
            flow: ExchangeFlow actual
            historical_context: Si usar contexto histórico
            
        Returns:
            Dict con señal y recomendación
        """
        signal = {
            'symbol': flow.symbol,
            'timestamp': datetime.utcnow().isoformat(),
            'period_hours': flow.period_hours,
            'net_flow_usd': flow.net_flow_usd,
            'flow_ratio': flow.flow_ratio,
            'market_bias': flow.market_bias.value,
            'signal_strength': flow.signal_strength.value,
            'recommendation': 'hold',
            'confidence': 0.5,
            'reasoning': []
        }
        
        threshold = self._get_threshold(flow.symbol)
        
        # Análisis de magnitud
        if abs(flow.net_flow_usd) > threshold:
            if flow.net_flow_usd > 0:
                signal['recommendation'] = 'reduce_exposure'
                signal['reasoning'].append(
                    f"High inflows detected: ${flow.net_flow_usd:,.0f} entering exchanges"
                )
            else:
                signal['recommendation'] = 'increase_exposure'
                signal['reasoning'].append(
                    f"High outflows detected: ${abs(flow.net_flow_usd):,.0f} leaving exchanges"
                )
            signal['confidence'] = 0.7
        
        # Análisis de ratio
        if flow.flow_ratio > 2.0:
            signal['reasoning'].append(
                f"Flow ratio {flow.flow_ratio:.2f}x indicates strong selling pressure"
            )
            signal['confidence'] = min(signal['confidence'] + 0.1, 0.9)
        elif flow.flow_ratio < 0.5:
            signal['reasoning'].append(
                f"Flow ratio {flow.flow_ratio:.2f}x indicates strong accumulation"
            )
            signal['confidence'] = min(signal['confidence'] + 0.1, 0.9)
        
        # Contexto histórico
        if historical_context and flow.symbol in self.flow_history:
            trend = self.flow_history[flow.symbol].get_trend()
            signal['trend'] = trend
            
            if trend == "increasing_inflows":
                signal['reasoning'].append("Trend: Increasing inflows over past 24h")
                if signal['market_bias'] != 'bearish':
                    signal['market_bias'] = 'bearish'
            elif trend == "increasing_outflows":
                signal['reasoning'].append("Trend: Increasing outflows over past 24h")
                if signal['market_bias'] != 'bullish':
                    signal['market_bias'] = 'bullish'
        
        # Score normalizado para el kernel (-1 a 1)
        # Negativo = bearish (inflows), Positivo = bullish (outflows)
        max_flow = threshold * 2
        signal['exchange_flow_score'] = max(-1, min(1, -flow.net_flow_usd / max_flow))
        
        return signal
    
    def aggregate_flows(
        self,
        flows_by_exchange: Dict[str, ExchangeFlow]
    ) -> ExchangeFlow:
        """
        Agrega flujos de múltiples exchanges.
        
        Args:
            flows_by_exchange: Dict de exchange -> ExchangeFlow
            
        Returns:
            ExchangeFlow agregado
        """
        if not flows_by_exchange:
            # Retornar flow vacío
            return ExchangeFlow(
                symbol='UNKNOWN',
                exchange='aggregate',
                period_hours=24,
                inflow_amount=0,
                inflow_usd=0,
                inflow_count=0,
                outflow_amount=0,
                outflow_usd=0,
                outflow_count=0,
                net_flow=0,
                net_flow_usd=0
            )
        
        # Obtener símbolo del primer flow
        symbol = list(flows_by_exchange.values())[0].symbol
        period_hours = list(flows_by_exchange.values())[0].period_hours
        
        total_inflow_amount = sum(f.inflow_amount for f in flows_by_exchange.values())
        total_inflow_usd = sum(f.inflow_usd for f in flows_by_exchange.values())
        total_inflow_count = sum(f.inflow_count for f in flows_by_exchange.values())
        
        total_outflow_amount = sum(f.outflow_amount for f in flows_by_exchange.values())
        total_outflow_usd = sum(f.outflow_usd for f in flows_by_exchange.values())
        total_outflow_count = sum(f.outflow_count for f in flows_by_exchange.values())
        
        return ExchangeFlow(
            symbol=symbol,
            exchange='aggregate',
            period_hours=period_hours,
            inflow_amount=total_inflow_amount,
            inflow_usd=total_inflow_usd,
            inflow_count=total_inflow_count,
            outflow_amount=total_outflow_amount,
            outflow_usd=total_outflow_usd,
            outflow_count=total_outflow_count,
            net_flow=total_inflow_amount - total_outflow_amount,
            net_flow_usd=total_inflow_usd - total_outflow_usd
        )
    
    def get_historical_summary(
        self,
        symbol: str,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Obtiene resumen histórico de flujos.
        
        Args:
            symbol: Símbolo del activo
            hours: Horas de historial
            
        Returns:
            Dict con resumen estadístico
        """
        if symbol not in self.flow_history:
            return {
                'symbol': symbol,
                'hours': hours,
                'data_points': 0,
                'average_net_flow_usd': 0,
                'total_inflow_usd': 0,
                'total_outflow_usd': 0,
                'trend': 'insufficient_data'
            }
        
        history = self.flow_history[symbol]
        recent_flows = history.flows[-hours:] if len(history.flows) >= hours else history.flows
        
        if not recent_flows:
            return {
                'symbol': symbol,
                'hours': hours,
                'data_points': 0,
                'average_net_flow_usd': 0,
                'total_inflow_usd': 0,
                'total_outflow_usd': 0,
                'trend': 'insufficient_data'
            }
        
        return {
            'symbol': symbol,
            'hours': hours,
            'data_points': len(recent_flows),
            'average_net_flow_usd': sum(f.net_flow_usd for f in recent_flows) / len(recent_flows),
            'total_inflow_usd': sum(f.inflow_usd for f in recent_flows),
            'total_outflow_usd': sum(f.outflow_usd for f in recent_flows),
            'max_inflow_usd': max(f.inflow_usd for f in recent_flows),
            'max_outflow_usd': max(f.outflow_usd for f in recent_flows),
            'trend': history.get_trend(hours),
            'bias_distribution': {
                'bullish': sum(1 for f in recent_flows if f.market_bias == MarketBias.BULLISH),
                'bearish': sum(1 for f in recent_flows if f.market_bias == MarketBias.BEARISH),
                'neutral': sum(1 for f in recent_flows if f.market_bias == MarketBias.NEUTRAL)
            }
        }
