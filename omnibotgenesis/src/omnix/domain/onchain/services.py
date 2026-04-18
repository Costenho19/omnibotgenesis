"""
OMNIX On-Chain Domain Services - Business Logic for Blockchain Analytics

This module provides domain services that use OnChainDataPort to deliver
actionable trading insights from on-chain data.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from src.omnix.ports.driven.onchain_data_port import (
    OnChainMetrics,
    WhaleActivity,
    NetworkHealth,
    OnChainDataPort
)

logger = logging.getLogger(__name__)


class OnChainAnalysisService:
    """
    Domain service for on-chain analytics.
    Provides trading-relevant insights from blockchain data.
    """
    
    def __init__(self, onchain_port: OnChainDataPort):
        self._port = onchain_port
        logger.info("🔗 OnChainAnalysisService initialized")
    
    async def get_market_sentiment_from_chain(self, asset: str = "BTC") -> Dict[str, Any]:
        """
        Derive market sentiment from on-chain activity.
        
        Combines whale activity, network health, and exchange flows
        to produce a sentiment score.
        
        Returns:
            Dict with sentiment score (-100 to +100) and analysis
        """
        try:
            whale_data = await self._port.get_whale_activity(asset, window_hours=24)
            network_health = await self._port.get_network_health(asset)
            
            sentiment_score = 0
            signals = []
            
            if whale_data.net_direction == "accumulation":
                sentiment_score += 25
                signals.append("🐋 Whales accumulating")
            elif whale_data.net_direction == "distribution":
                sentiment_score -= 25
                signals.append("🐋 Whales distributing")
            
            sentiment_score += int((whale_data.accumulation_score - 0.5) * 50)
            
            if network_health.health_score > 0.8:
                sentiment_score += 10
                signals.append("✅ Network healthy")
            elif network_health.health_score < 0.5:
                sentiment_score -= 15
                signals.append("⚠️ Network stressed")
            
            if network_health.congestion_level == "low":
                sentiment_score += 5
            elif network_health.congestion_level == "high":
                sentiment_score -= 10
                signals.append("🚦 High congestion")
            
            sentiment_score = max(-100, min(100, sentiment_score))
            
            if sentiment_score > 30:
                sentiment_label = "Bullish"
            elif sentiment_score > 10:
                sentiment_label = "Slightly Bullish"
            elif sentiment_score < -30:
                sentiment_label = "Bearish"
            elif sentiment_score < -10:
                sentiment_label = "Slightly Bearish"
            else:
                sentiment_label = "Neutral"
            
            return {
                'asset': asset,
                'sentiment_score': sentiment_score,
                'sentiment_label': sentiment_label,
                'signals': signals,
                'whale_activity': whale_data.to_dict(),
                'network_health': network_health.to_dict(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting on-chain sentiment: {e}")
            return {
                'asset': asset,
                'sentiment_score': 0,
                'sentiment_label': "Unknown",
                'signals': ["❌ On-chain data unavailable"],
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def detect_whale_accumulation(
        self, 
        asset: str = "BTC",
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Detect if whales are in accumulation mode.
        
        Args:
            asset: Blockchain asset
            threshold: Accumulation score threshold (0-1)
            
        Returns:
            Dict with accumulation detection results
        """
        try:
            whale_data = await self._port.get_whale_activity(asset, window_hours=48)
            
            is_accumulating = whale_data.accumulation_score >= threshold
            
            return {
                'asset': asset,
                'is_accumulating': is_accumulating,
                'accumulation_score': whale_data.accumulation_score,
                'net_direction': whale_data.net_direction,
                'total_volume_usd': whale_data.total_volume_usd,
                'transaction_count': whale_data.total_transactions,
                'signal_strength': 'STRONG' if whale_data.accumulation_score > 0.8 else 'MODERATE' if whale_data.accumulation_score > 0.6 else 'WEAK',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error detecting whale accumulation: {e}")
            return {
                'asset': asset,
                'is_accumulating': False,
                'accumulation_score': 0.5,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def get_network_status_summary(self, asset: str = "BTC") -> Dict[str, Any]:
        """
        Get a human-readable network status summary.
        
        Returns:
            Dict with network status and recommendations
        """
        try:
            metrics = await self._port.get_onchain_metrics(asset)
            health = await self._port.get_network_health(asset)
            
            recommendations = []
            
            if health.congestion_level == "high":
                recommendations.append("⏳ Consider waiting for lower fees")
            
            if health.fee_tier == "expensive":
                recommendations.append("💸 Fees elevated - batch transactions if possible")
            
            if health.hash_rate_trend == "declining":
                recommendations.append("⚠️ Hash rate declining - monitor for difficulty adjustment")
            
            return {
                'asset': asset,
                'network_status': health.network_status,
                'health_score': health.health_score,
                'congestion': health.congestion_level,
                'fee_tier': health.fee_tier,
                'confirmation_time': health.confirmation_time_estimate,
                'hash_rate': metrics.hash_rate,
                'active_addresses': metrics.active_addresses_24h,
                'tx_volume_24h': metrics.transaction_volume_24h,
                'recommendations': recommendations,
                'source': metrics.source,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting network status: {e}")
            return {
                'asset': asset,
                'network_status': "Unknown",
                'health_score': 0.5,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
