"""
OMNIX On-Chain Infrastructure Adapters

Multi-provider adapter system for blockchain on-chain data.
Implements the Strangler Fig pattern with cooldown/fallback.
"""

from .blockchain_info_provider import BlockchainInfoProvider
from .onchain_adapter import OnChainDataAdapter

__all__ = [
    'BlockchainInfoProvider',
    'OnChainDataAdapter'
]
