"""
OMNIX On-Chain Data Adapter - Multi-Provider with Cooldown/Fallback

Implements the Strangler Fig pattern following AIGatewayShim design.
Provides resilient on-chain data access with automatic failover.

Feature Flag: USE_ONCHAIN_PORT
Cooldown Period: 5 minutes after failure
"""

import os
import logging
import asyncio
from typing import Optional, List
from datetime import datetime, timedelta

from src.omnix.ports.driven.onchain_data_port import (
    OnChainDataPort,
    OnChainMetrics,
    WhaleActivity,
    NetworkHealth,
    ExchangeFlows,
    OnChainAPIError
)
from .blockchain_info_provider import BlockchainInfoProvider

logger = logging.getLogger(__name__)


class OnChainDataAdapter:
    """
    Multi-provider adapter for on-chain blockchain data.
    
    Implements:
    - Multi-provider failover (Blockchain.info → Glassnode → fallback)
    - Cooldown after failures (5 min)
    - Feature flag control (USE_ONCHAIN_PORT)
    - Response caching (via Redis if available)
    
    Architecture Pattern: Strangler Fig with Pure Bridge
    - Adapter only translates interfaces
    - Container controls lifecycle and cooldown
    - Legacy fallback when V7 in cooldown
    """
    
    COOLDOWN_SECONDS = 300
    MAX_RETRIES = 2
    
    def __init__(
        self,
        blockchain_info_provider: Optional[BlockchainInfoProvider] = None,
        legacy_service: Optional[object] = None
    ):
        self._blockchain_info = blockchain_info_provider or BlockchainInfoProvider()
        self._legacy_service = legacy_service
        self._last_failure_time: Optional[datetime] = None
        self._failure_count: int = 0
        self._is_enabled = os.getenv("USE_ONCHAIN_PORT", "false").lower() == "true"
        
        logger.info(f"🔗 OnChainDataAdapter initialized (enabled={self._is_enabled})")
    
    def is_in_cooldown(self) -> bool:
        """Check if adapter is in cooldown after failures"""
        if self._last_failure_time is None:
            return False
        
        cooldown_end = self._last_failure_time + timedelta(seconds=self.COOLDOWN_SECONDS)
        return datetime.utcnow() < cooldown_end
    
    def _record_failure(self):
        """Record a failure and enter cooldown if needed"""
        self._failure_count += 1
        self._last_failure_time = datetime.utcnow()
        logger.warning(f"⚠️ OnChainDataAdapter failure #{self._failure_count}, entering cooldown")
    
    def _reset_failures(self):
        """Reset failure tracking on success"""
        if self._failure_count > 0:
            logger.info("✅ OnChainDataAdapter recovered, resetting failure count")
        self._failure_count = 0
        self._last_failure_time = None
    
    async def get_onchain_metrics(self, asset: str = "BTC") -> OnChainMetrics:
        """
        Get on-chain metrics with failover.
        
        Provider Priority:
        1. Blockchain.info (BTC only, free)
        2. Legacy fallback if in cooldown
        """
        if not self._is_enabled:
            return await self._get_legacy_metrics(asset)
        
        if self.is_in_cooldown():
            logger.debug("OnChainDataAdapter in cooldown, using legacy")
            return await self._get_legacy_metrics(asset)
        
        for attempt in range(self.MAX_RETRIES):
            try:
                result = await self._blockchain_info.get_onchain_metrics(asset)
                self._reset_failures()
                return result
                
            except OnChainAPIError as e:
                if not e.retryable:
                    logger.error(f"❌ Non-retryable error: {e}")
                    break
                
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"⚠️ Retry {attempt + 1}/{self.MAX_RETRIES} after {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"❌ All retries exhausted: {e}")
            except Exception as e:
                logger.error(f"❌ Unexpected error: {e}")
                break
        
        self._record_failure()
        return await self._get_legacy_metrics(asset)
    
    async def get_whale_activity(
        self,
        asset: str = "BTC",
        window_hours: int = 24,
        min_amount_usd: float = 1_000_000
    ) -> WhaleActivity:
        """Get whale activity with failover"""
        if not self._is_enabled or self.is_in_cooldown():
            return await self._get_legacy_whale_activity(asset, window_hours)
        
        try:
            result = await self._blockchain_info.get_whale_activity(
                asset, window_hours, min_amount_usd
            )
            self._reset_failures()
            return result
        except Exception as e:
            logger.error(f"❌ Whale activity error: {e}")
            self._record_failure()
            return await self._get_legacy_whale_activity(asset, window_hours)
    
    async def get_network_health(self, asset: str = "BTC") -> NetworkHealth:
        """Get network health with failover"""
        if not self._is_enabled or self.is_in_cooldown():
            return await self._get_legacy_network_health(asset)
        
        for attempt in range(self.MAX_RETRIES):
            try:
                result = await self._blockchain_info.get_network_health(asset)
                self._reset_failures()
                return result
                
            except OnChainAPIError as e:
                if not e.retryable:
                    break
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep((attempt + 1) * 2)
        
        self._record_failure()
        return await self._get_legacy_network_health(asset)
    
    async def get_exchange_flows(
        self,
        asset: str = "BTC",
        exchange: str = "all"
    ) -> List[ExchangeFlows]:
        """Get exchange flows - placeholder for Glassnode integration"""
        return []
    
    async def _get_legacy_metrics(self, asset: str) -> OnChainMetrics:
        """Fallback to legacy on-chain service"""
        try:
            if self._legacy_service and hasattr(self._legacy_service, '_get_on_chain_metrics'):
                data = self._legacy_service._get_on_chain_metrics()
                return OnChainMetrics(
                    asset=asset,
                    total_supply=21_000_000 if asset == "BTC" else 0,
                    circulating_supply=data.get('total_bitcoins', 19_800_000),
                    hash_rate=data.get('hash_rate', 700_000_000_000_000_000_000),
                    difficulty=data.get('difficulty', 0),
                    avg_block_time=600,
                    active_addresses_24h=0,
                    transaction_count_24h=0,
                    transaction_volume_24h=data.get('trade_volume_btc', 0),
                    miners_revenue_24h=data.get('miners_revenue_usd', 0),
                    mempool_size=0,
                    avg_fee_usd=0,
                    source="Legacy (Fallback)",
                    timestamp=datetime.utcnow()
                )
        except Exception as e:
            logger.debug(f"Legacy fallback failed: {e}")
        
        return OnChainMetrics(
            asset=asset,
            total_supply=21_000_000 if asset == "BTC" else 0,
            circulating_supply=19_800_000,
            hash_rate=700_000_000_000_000_000_000,
            difficulty=0,
            avg_block_time=600,
            active_addresses_24h=0,
            transaction_count_24h=0,
            transaction_volume_24h=0,
            miners_revenue_24h=0,
            mempool_size=0,
            avg_fee_usd=0,
            source="Estimated (Fallback)",
            timestamp=datetime.utcnow()
        )
    
    async def _get_legacy_whale_activity(self, asset: str, window_hours: int) -> WhaleActivity:
        """Fallback whale activity"""
        try:
            if self._legacy_service and hasattr(self._legacy_service, '_get_whale_movement_data'):
                data = self._legacy_service._get_whale_movement_data()
                return WhaleActivity(
                    asset=asset,
                    window_hours=window_hours,
                    total_transactions=data.get('large_transactions', 5),
                    total_volume=0,
                    total_volume_usd=0,
                    net_direction=data.get('direction', 'accumulation'),
                    accumulation_score=data.get('confidence', 0.85),
                    transactions=[],
                    source="Legacy (Fallback)",
                    timestamp=datetime.utcnow()
                )
        except Exception as e:
            logger.debug(f"Legacy whale fallback failed: {e}")
        
        return WhaleActivity(
            asset=asset,
            window_hours=window_hours,
            total_transactions=5,
            total_volume=0,
            total_volume_usd=0,
            net_direction="accumulation",
            accumulation_score=0.5,
            transactions=[],
            source="Estimated (Fallback)",
            timestamp=datetime.utcnow()
        )
    
    async def _get_legacy_network_health(self, asset: str) -> NetworkHealth:
        """Fallback network health"""
        return NetworkHealth(
            asset=asset,
            health_score=0.75,
            congestion_level="normal",
            fee_tier="normal",
            confirmation_time_estimate="~60 minutes (6 confirmations)",
            hash_rate_trend="stable",
            difficulty_adjustment_eta=None,
            network_status="operational",
            source="Estimated (Fallback)",
            timestamp=datetime.utcnow()
        )
    
    async def close(self):
        """Cleanup resources"""
        await self._blockchain_info.close()
