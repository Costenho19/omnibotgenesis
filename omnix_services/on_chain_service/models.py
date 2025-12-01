"""
OMNIX On-Chain Data Models V6.5
================================

Modelos de datos para información on-chain:
- WhaleTransaction: Transacciones grandes de ballenas
- ExchangeFlow: Flujos a/desde exchanges
- NetworkMetrics: Métricas de salud de la red
- SmartMoneySignal: Señales de dinero inteligente
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List, Any
import json


class FlowDirection(Enum):
    """Dirección del flujo de fondos"""
    INFLOW = "inflow"      # Hacia exchange (potencial venta)
    OUTFLOW = "outflow"    # Desde exchange (potencial HODL)
    INTERNAL = "internal"  # Movimiento interno


class TransactionType(Enum):
    """Tipo de transacción on-chain"""
    TRANSFER = "transfer"
    EXCHANGE_DEPOSIT = "exchange_deposit"
    EXCHANGE_WITHDRAWAL = "exchange_withdrawal"
    SMART_CONTRACT = "smart_contract"
    DEFI_INTERACTION = "defi_interaction"
    NFT_TRADE = "nft_trade"
    BRIDGE = "bridge"
    UNKNOWN = "unknown"


class SignalStrength(Enum):
    """Fuerza de la señal on-chain"""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


class MarketBias(Enum):
    """Sesgo de mercado derivado de datos on-chain"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass
class WhaleTransaction:
    """
    Representa una transacción grande de una ballena.
    
    Umbral típico: >$1M para BTC/ETH, ajustable por activo.
    """
    tx_hash: str
    blockchain: str  # bitcoin, ethereum, solana, etc.
    symbol: str      # BTC, ETH, SOL
    amount: float
    amount_usd: float
    from_address: str
    to_address: str
    from_label: Optional[str] = None  # "Binance", "Unknown Whale", etc.
    to_label: Optional[str] = None
    transaction_type: TransactionType = TransactionType.TRANSFER
    timestamp: datetime = field(default_factory=datetime.utcnow)
    block_number: Optional[int] = None
    
    # Análisis
    is_exchange_related: bool = False
    flow_direction: Optional[FlowDirection] = None
    market_impact_score: float = 0.0  # 0-1, impacto estimado en precio
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'tx_hash': self.tx_hash,
            'blockchain': self.blockchain,
            'symbol': self.symbol,
            'amount': self.amount,
            'amount_usd': self.amount_usd,
            'from_address': self.from_address,
            'to_address': self.to_address,
            'from_label': self.from_label,
            'to_label': self.to_label,
            'transaction_type': self.transaction_type.value,
            'timestamp': self.timestamp.isoformat(),
            'block_number': self.block_number,
            'is_exchange_related': self.is_exchange_related,
            'flow_direction': self.flow_direction.value if self.flow_direction else None,
            'market_impact_score': self.market_impact_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WhaleTransaction':
        return cls(
            tx_hash=data['tx_hash'],
            blockchain=data['blockchain'],
            symbol=data['symbol'],
            amount=data['amount'],
            amount_usd=data['amount_usd'],
            from_address=data['from_address'],
            to_address=data['to_address'],
            from_label=data.get('from_label'),
            to_label=data.get('to_label'),
            transaction_type=TransactionType(data.get('transaction_type', 'transfer')),
            timestamp=datetime.fromisoformat(data['timestamp']) if isinstance(data.get('timestamp'), str) else data.get('timestamp', datetime.utcnow()),
            block_number=data.get('block_number'),
            is_exchange_related=data.get('is_exchange_related', False),
            flow_direction=FlowDirection(data['flow_direction']) if data.get('flow_direction') else None,
            market_impact_score=data.get('market_impact_score', 0.0)
        )


@dataclass
class ExchangeFlow:
    """
    Flujos agregados de fondos hacia/desde exchanges.
    
    Regla general:
    - Inflows altos = Presión de venta (bearish)
    - Outflows altos = Acumulación/HODL (bullish)
    """
    symbol: str
    exchange: str  # "binance", "coinbase", "aggregate"
    period_hours: int  # 1, 4, 24
    
    inflow_amount: float
    inflow_usd: float
    inflow_count: int
    
    outflow_amount: float
    outflow_usd: float
    outflow_count: int
    
    net_flow: float  # Positivo = más inflows (bearish)
    net_flow_usd: float
    
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Análisis
    flow_ratio: float = 0.0  # inflow/outflow, >1 = bearish
    market_bias: MarketBias = MarketBias.NEUTRAL
    signal_strength: SignalStrength = SignalStrength.WEAK
    
    def __post_init__(self):
        # Calcular ratio y sesgo
        if self.outflow_amount > 0:
            self.flow_ratio = self.inflow_amount / self.outflow_amount
        else:
            self.flow_ratio = float('inf') if self.inflow_amount > 0 else 1.0
        
        # Determinar sesgo de mercado
        if self.flow_ratio > 1.5:
            self.market_bias = MarketBias.BEARISH
            self.signal_strength = SignalStrength.STRONG if self.flow_ratio > 2.0 else SignalStrength.MODERATE
        elif self.flow_ratio < 0.67:
            self.market_bias = MarketBias.BULLISH
            self.signal_strength = SignalStrength.STRONG if self.flow_ratio < 0.5 else SignalStrength.MODERATE
        else:
            self.market_bias = MarketBias.NEUTRAL
            self.signal_strength = SignalStrength.WEAK
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'exchange': self.exchange,
            'period_hours': self.period_hours,
            'inflow_amount': self.inflow_amount,
            'inflow_usd': self.inflow_usd,
            'inflow_count': self.inflow_count,
            'outflow_amount': self.outflow_amount,
            'outflow_usd': self.outflow_usd,
            'outflow_count': self.outflow_count,
            'net_flow': self.net_flow,
            'net_flow_usd': self.net_flow_usd,
            'timestamp': self.timestamp.isoformat(),
            'flow_ratio': self.flow_ratio,
            'market_bias': self.market_bias.value,
            'signal_strength': self.signal_strength.value
        }


@dataclass
class NetworkMetrics:
    """
    Métricas de salud de la red blockchain.
    
    Indicadores clave:
    - Active addresses: Adopción/actividad
    - Transaction volume: Demanda de blockspace
    - Gas fees: Congestión/demanda
    - Hash rate (PoW): Seguridad de la red
    """
    blockchain: str
    symbol: str
    period_hours: int
    
    active_addresses: int
    active_addresses_change_pct: float  # vs periodo anterior
    
    transaction_count: int
    transaction_volume: float
    transaction_volume_usd: float
    transaction_count_change_pct: float
    
    avg_gas_fee: Optional[float] = None  # En unidades nativas
    avg_gas_fee_usd: Optional[float] = None
    gas_fee_change_pct: Optional[float] = None
    
    hash_rate: Optional[float] = None  # Para PoW chains
    hash_rate_change_pct: Optional[float] = None
    
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Análisis
    network_health_score: float = 0.5  # 0-1
    activity_trend: str = "stable"  # increasing, decreasing, stable
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'blockchain': self.blockchain,
            'symbol': self.symbol,
            'period_hours': self.period_hours,
            'active_addresses': self.active_addresses,
            'active_addresses_change_pct': self.active_addresses_change_pct,
            'transaction_count': self.transaction_count,
            'transaction_volume': self.transaction_volume,
            'transaction_volume_usd': self.transaction_volume_usd,
            'transaction_count_change_pct': self.transaction_count_change_pct,
            'avg_gas_fee': self.avg_gas_fee,
            'avg_gas_fee_usd': self.avg_gas_fee_usd,
            'gas_fee_change_pct': self.gas_fee_change_pct,
            'hash_rate': self.hash_rate,
            'hash_rate_change_pct': self.hash_rate_change_pct,
            'timestamp': self.timestamp.isoformat(),
            'network_health_score': self.network_health_score,
            'activity_trend': self.activity_trend
        }


@dataclass
class SmartMoneySignal:
    """
    Señal derivada del comportamiento de "dinero inteligente".
    
    Smart money incluye:
    - Fondos institucionales
    - Wallets con histórico de trades exitosos
    - Early adopters de proyectos exitosos
    """
    symbol: str
    signal_type: str  # "accumulation", "distribution", "rotation"
    wallet_category: str  # "institution", "whale", "smart_trader"
    
    action: str  # "buy", "sell", "hold"
    amount_usd: float
    wallet_count: int  # Número de wallets con la misma acción
    
    confidence: float  # 0-1
    market_bias: MarketBias = MarketBias.NEUTRAL
    
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = "aggregate"  # arkham, debank, etc.
    
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'signal_type': self.signal_type,
            'wallet_category': self.wallet_category,
            'action': self.action,
            'amount_usd': self.amount_usd,
            'wallet_count': self.wallet_count,
            'confidence': self.confidence,
            'market_bias': self.market_bias.value,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'details': self.details
        }


@dataclass
class OnChainSignal:
    """
    Señal consolidada on-chain para el Non-Markovian Kernel.
    
    Combina múltiples fuentes de datos on-chain en una señal
    unificada que puede ser procesada por el kernel de memoria.
    """
    symbol: str
    timestamp: datetime
    
    # Componentes de la señal
    whale_activity_score: float = 0.0  # -1 a 1 (negativo=venta, positivo=compra)
    exchange_flow_score: float = 0.0   # -1 a 1 (negativo=inflows, positivo=outflows)
    network_health_score: float = 0.0  # 0 a 1
    smart_money_score: float = 0.0     # -1 a 1
    
    # Señal agregada
    composite_score: float = 0.0  # -1 a 1
    market_bias: MarketBias = MarketBias.NEUTRAL
    signal_strength: SignalStrength = SignalStrength.WEAK
    confidence: float = 0.0
    
    # Datos fuente
    whale_transactions: List[WhaleTransaction] = field(default_factory=list)
    exchange_flows: List[ExchangeFlow] = field(default_factory=list)
    network_metrics: Optional[NetworkMetrics] = None
    smart_money_signals: List[SmartMoneySignal] = field(default_factory=list)
    
    def calculate_composite(self, weights: Optional[Dict[str, float]] = None):
        """
        Calcula la señal compuesta ponderada.
        
        Args:
            weights: Pesos para cada componente (default: igual peso)
        """
        if weights is None:
            weights = {
                'whale': 0.30,
                'exchange_flow': 0.35,
                'network': 0.15,
                'smart_money': 0.20
            }
        
        self.composite_score = (
            self.whale_activity_score * weights.get('whale', 0.25) +
            self.exchange_flow_score * weights.get('exchange_flow', 0.25) +
            (self.network_health_score * 2 - 1) * weights.get('network', 0.25) +  # Normalize to -1,1
            self.smart_money_score * weights.get('smart_money', 0.25)
        )
        
        # Determinar sesgo y fuerza
        if self.composite_score > 0.3:
            self.market_bias = MarketBias.BULLISH
            self.signal_strength = SignalStrength.STRONG if self.composite_score > 0.5 else SignalStrength.MODERATE
        elif self.composite_score < -0.3:
            self.market_bias = MarketBias.BEARISH
            self.signal_strength = SignalStrength.STRONG if self.composite_score < -0.5 else SignalStrength.MODERATE
        else:
            self.market_bias = MarketBias.NEUTRAL
            self.signal_strength = SignalStrength.WEAK
        
        # Confidence basada en disponibilidad de datos
        data_sources = sum([
            1 if len(self.whale_transactions) > 0 else 0,
            1 if len(self.exchange_flows) > 0 else 0,
            1 if self.network_metrics is not None else 0,
            1 if len(self.smart_money_signals) > 0 else 0
        ])
        self.confidence = data_sources / 4.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'whale_activity_score': self.whale_activity_score,
            'exchange_flow_score': self.exchange_flow_score,
            'network_health_score': self.network_health_score,
            'smart_money_score': self.smart_money_score,
            'composite_score': self.composite_score,
            'market_bias': self.market_bias.value,
            'signal_strength': self.signal_strength.value,
            'confidence': self.confidence,
            'whale_tx_count': len(self.whale_transactions),
            'exchange_flow_count': len(self.exchange_flows),
            'has_network_metrics': self.network_metrics is not None,
            'smart_money_signal_count': len(self.smart_money_signals)
        }
    
    def to_kernel_format(self) -> Dict[str, Any]:
        """
        Formato para el Non-Markovian Memory Kernel.
        """
        return {
            'source': 'on_chain',
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'signal': self.composite_score,
            'bias': self.market_bias.value,
            'strength': self.signal_strength.value,
            'confidence': self.confidence,
            'components': {
                'whale': self.whale_activity_score,
                'exchange_flow': self.exchange_flow_score,
                'network': self.network_health_score,
                'smart_money': self.smart_money_score
            }
        }
