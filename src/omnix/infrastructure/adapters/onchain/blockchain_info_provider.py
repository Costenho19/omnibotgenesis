"""
OMNIX Blockchain.info Provider - BTC Network Stats

FREE API provider for Bitcoin on-chain data.
No API key required, rate-limited.

API Endpoints:
- https://api.blockchain.info/stats - Network statistics
- https://blockchain.info/rawblock/{hash} - Block data
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import aiohttp

from src.omnix.ports.driven.onchain_data_port import (
    OnChainMetrics,
    WhaleActivity,
    WhaleTransaction,
    NetworkHealth,
    ExchangeFlows,
    OnChainAPIError
)

logger = logging.getLogger(__name__)


class BlockchainInfoProvider:
    """
    Blockchain.info API adapter for BTC on-chain data.
    
    Features:
    - Free API (no key required)
    - Rate limit: ~5 requests/second
    - BTC only
    """
    
    BASE_URL = "https://api.blockchain.info"
    TIMEOUT = 10
    PROVIDER_NAME = "Blockchain.info"
    
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_request_time: float = 0
        self._min_request_interval: float = 0.2
        logger.info(f"🔗 {self.PROVIDER_NAME} provider initialized")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.TIMEOUT)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def _rate_limit(self):
        """Simple rate limiting"""
        import time
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self._min_request_interval:
            await asyncio.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
    async def _request(self, endpoint: str) -> Dict[str, Any]:
        """Make rate-limited API request"""
        await self._rate_limit()
        session = await self._get_session()
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    raise OnChainAPIError(
                        "Rate limit exceeded",
                        provider=self.PROVIDER_NAME,
                        retryable=True
                    )
                else:
                    raise OnChainAPIError(
                        f"HTTP {response.status}",
                        provider=self.PROVIDER_NAME,
                        retryable=response.status >= 500
                    )
        except asyncio.TimeoutError:
            raise OnChainAPIError(
                "Request timeout",
                provider=self.PROVIDER_NAME,
                retryable=True
            )
        except aiohttp.ClientError as e:
            raise OnChainAPIError(
                f"Connection error: {e}",
                provider=self.PROVIDER_NAME,
                retryable=True
            )
    
    async def get_onchain_metrics(self, asset: str = "BTC") -> OnChainMetrics:
        """
        Get Bitcoin network metrics from blockchain.info/stats
        
        Only supports BTC. Other assets return error.
        """
        if asset.upper() != "BTC":
            raise OnChainAPIError(
                f"Asset {asset} not supported. Only BTC available.",
                provider=self.PROVIDER_NAME,
                retryable=False
            )
        
        try:
            data = await self._request("/stats")
            
            total_btc = data.get('totalbc', 0) / 100_000_000
            hash_rate = data.get('hash_rate', 0)
            difficulty = data.get('difficulty', 0)
            n_tx = data.get('n_tx', 0)
            trade_vol = data.get('trade_volume_btc', 0)
            miners_rev = data.get('miners_revenue_usd', 0)
            avg_block_time = data.get('minutes_between_blocks', 10) * 60
            
            return OnChainMetrics(
                asset="BTC",
                total_supply=21_000_000,
                circulating_supply=total_btc,
                hash_rate=hash_rate,
                difficulty=difficulty,
                avg_block_time=avg_block_time,
                active_addresses_24h=0,
                transaction_count_24h=n_tx,
                transaction_volume_24h=trade_vol,
                miners_revenue_24h=miners_rev,
                mempool_size=0,
                avg_fee_usd=0,
                source=self.PROVIDER_NAME,
                timestamp=datetime.utcnow()
            )
            
        except OnChainAPIError:
            raise
        except Exception as e:
            logger.error(f"Error fetching BTC metrics: {e}")
            raise OnChainAPIError(
                f"Failed to parse response: {e}",
                provider=self.PROVIDER_NAME,
                retryable=False
            )
    
    async def get_whale_activity(
        self,
        asset: str = "BTC",
        window_hours: int = 24,
        min_amount_usd: float = 1_000_000
    ) -> WhaleActivity:
        """
        Get whale activity summary.
        
        Note: Blockchain.info doesn't provide whale tracking directly.
        This returns estimated data based on available metrics.
        For accurate whale data, use Arkham or Glassnode providers.
        """
        if asset.upper() != "BTC":
            raise OnChainAPIError(
                f"Asset {asset} not supported",
                provider=self.PROVIDER_NAME,
                retryable=False
            )
        
        return WhaleActivity(
            asset="BTC",
            window_hours=window_hours,
            total_transactions=0,
            total_volume=0,
            total_volume_usd=0,
            net_direction="unknown",
            accumulation_score=0.5,
            transactions=[],
            source=f"{self.PROVIDER_NAME} (limited data)",
            timestamp=datetime.utcnow()
        )
    
    async def get_network_health(self, asset: str = "BTC") -> NetworkHealth:
        """
        Get network health based on available metrics.
        """
        if asset.upper() != "BTC":
            raise OnChainAPIError(
                f"Asset {asset} not supported",
                provider=self.PROVIDER_NAME,
                retryable=False
            )
        
        try:
            data = await self._request("/stats")
            
            hash_rate = data.get('hash_rate', 0)
            n_tx = data.get('n_tx', 0)
            minutes_between = data.get('minutes_between_blocks', 10)
            
            if minutes_between < 8:
                congestion = "low"
                health_score = 0.9
            elif minutes_between < 12:
                congestion = "normal"
                health_score = 0.75
            elif minutes_between < 15:
                congestion = "moderate"
                health_score = 0.6
            else:
                congestion = "high"
                health_score = 0.4
            
            hash_trend = "stable"
            
            return NetworkHealth(
                asset="BTC",
                health_score=health_score,
                congestion_level=congestion,
                fee_tier="normal",
                confirmation_time_estimate=f"~{int(minutes_between * 6)} minutes (6 confirmations)",
                hash_rate_trend=hash_trend,
                difficulty_adjustment_eta=None,
                network_status="operational",
                source=self.PROVIDER_NAME,
                timestamp=datetime.utcnow()
            )
            
        except OnChainAPIError:
            raise
        except Exception as e:
            logger.error(f"Error fetching network health: {e}")
            raise OnChainAPIError(
                f"Failed to get network health: {e}",
                provider=self.PROVIDER_NAME,
                retryable=True
            )
    
    async def get_exchange_flows(
        self,
        asset: str = "BTC",
        exchange: str = "all"
    ) -> List[ExchangeFlows]:
        """
        Get exchange flow data.
        
        Note: Blockchain.info doesn't provide exchange flow tracking.
        Returns empty list. Use Glassnode for this data.
        """
        return []
    
    async def close(self):
        """Close the aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
