"""
OMNIX On-Chain Data Port - Blockchain Analytics Interface Contract

This module defines contracts for on-chain data operations:
- OnChainDataPort: Blockchain metrics, whale activity, network health
- ExchangeFlowPort: Exchange inflow/outflow tracking

SOLID Principles:
- SRP: Separated on-chain data from trading logic
- ISP: Segregated interfaces per concern
- DIP: Depend on abstractions for blockchain data providers

Providers:
- Blockchain.info (BTC network stats) - FREE
- Glassnode (advanced on-chain metrics) - PAID
- Arkham (entity-level tracking) - PAID
"""

from typing import Protocol, List, Dict, Any, Optional, runtime_checkable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ChainAsset(Enum):
    """Supported blockchain assets for on-chain analysis"""
    BTC = "bitcoin"
    ETH = "ethereum"
    SOL = "solana"


@dataclass
class OnChainMetrics:
    """On-chain network metrics for a blockchain asset"""
    asset: str
    total_supply: float
    circulating_supply: float
    hash_rate: float
    difficulty: float
    avg_block_time: float
    active_addresses_24h: int
    transaction_count_24h: int
    transaction_volume_24h: float
    miners_revenue_24h: float
    mempool_size: int
    avg_fee_usd: float
    source: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'asset': self.asset,
            'total_supply': self.total_supply,
            'circulating_supply': self.circulating_supply,
            'hash_rate': self.hash_rate,
            'difficulty': self.difficulty,
            'avg_block_time': self.avg_block_time,
            'active_addresses_24h': self.active_addresses_24h,
            'transaction_count_24h': self.transaction_count_24h,
            'transaction_volume_24h': self.transaction_volume_24h,
            'miners_revenue_24h': self.miners_revenue_24h,
            'mempool_size': self.mempool_size,
            'avg_fee_usd': self.avg_fee_usd,
            'source': self.source,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class WhaleTransaction:
    """Large transaction detected on-chain"""
    tx_hash: str
    asset: str
    amount: float
    amount_usd: float
    from_address: str
    to_address: str
    from_entity: Optional[str]
    to_entity: Optional[str]
    direction: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'tx_hash': self.tx_hash,
            'asset': self.asset,
            'amount': self.amount,
            'amount_usd': self.amount_usd,
            'from_address': self.from_address,
            'to_address': self.to_address,
            'from_entity': self.from_entity,
            'to_entity': self.to_entity,
            'direction': self.direction,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class WhaleActivity:
    """Summary of whale activity for a time window"""
    asset: str
    window_hours: int
    total_transactions: int
    total_volume: float
    total_volume_usd: float
    net_direction: str
    accumulation_score: float
    transactions: List[WhaleTransaction]
    source: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'asset': self.asset,
            'window_hours': self.window_hours,
            'total_transactions': self.total_transactions,
            'total_volume': self.total_volume,
            'total_volume_usd': self.total_volume_usd,
            'net_direction': self.net_direction,
            'accumulation_score': self.accumulation_score,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'source': self.source,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class NetworkHealth:
    """Overall network health status"""
    asset: str
    health_score: float
    congestion_level: str
    fee_tier: str
    confirmation_time_estimate: str
    hash_rate_trend: str
    difficulty_adjustment_eta: Optional[str]
    network_status: str
    source: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'asset': self.asset,
            'health_score': self.health_score,
            'congestion_level': self.congestion_level,
            'fee_tier': self.fee_tier,
            'confirmation_time_estimate': self.confirmation_time_estimate,
            'hash_rate_trend': self.hash_rate_trend,
            'difficulty_adjustment_eta': self.difficulty_adjustment_eta,
            'network_status': self.network_status,
            'source': self.source,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ExchangeFlows:
    """Exchange inflow/outflow metrics"""
    asset: str
    exchange: str
    inflow_24h: float
    outflow_24h: float
    net_flow_24h: float
    net_flow_usd: float
    flow_direction: str
    source: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'asset': self.asset,
            'exchange': self.exchange,
            'inflow_24h': self.inflow_24h,
            'outflow_24h': self.outflow_24h,
            'net_flow_24h': self.net_flow_24h,
            'net_flow_usd': self.net_flow_usd,
            'flow_direction': self.flow_direction,
            'source': self.source,
            'timestamp': self.timestamp.isoformat()
        }


@runtime_checkable
class OnChainDataPort(Protocol):
    """
    Contract for on-chain blockchain data providers.
    All methods are ASYNC for optimal network I/O.
    
    Implementations:
    - BlockchainInfoProvider (BTC only, free)
    - GlassnodeProvider (multi-chain, paid)
    - ArkhamProvider (entity tracking, paid)
    
    Feature Flag: USE_ONCHAIN_PORT
    """
    
    async def get_onchain_metrics(
        self,
        asset: str = "BTC"
    ) -> OnChainMetrics:
        """
        Get on-chain network metrics.
        
        Args:
            asset: Blockchain asset (BTC, ETH, SOL)
            
        Returns:
            OnChainMetrics with network statistics
            
        Raises:
            OnChainAPIError: If all providers fail
        """
        ...
    
    async def get_whale_activity(
        self,
        asset: str = "BTC",
        window_hours: int = 24,
        min_amount_usd: float = 1_000_000
    ) -> WhaleActivity:
        """
        Get whale (large holder) transaction activity.
        
        Args:
            asset: Blockchain asset
            window_hours: Time window to analyze (1-168)
            min_amount_usd: Minimum transaction size to track
            
        Returns:
            WhaleActivity with transaction summary and list
        """
        ...
    
    async def get_network_health(
        self,
        asset: str = "BTC"
    ) -> NetworkHealth:
        """
        Get overall network health status.
        
        Args:
            asset: Blockchain asset
            
        Returns:
            NetworkHealth with status indicators
        """
        ...
    
    async def get_exchange_flows(
        self,
        asset: str = "BTC",
        exchange: str = "all"
    ) -> List[ExchangeFlows]:
        """
        Get exchange inflow/outflow data.
        
        Args:
            asset: Blockchain asset
            exchange: Specific exchange or "all"
            
        Returns:
            List of ExchangeFlows per exchange
        """
        ...


class OnChainAPIError(Exception):
    """Exception raised when on-chain API calls fail"""
    
    def __init__(self, message: str, provider: str = "unknown", retryable: bool = True):
        self.message = message
        self.provider = provider
        self.retryable = retryable
        super().__init__(f"[{provider}] {message}")
