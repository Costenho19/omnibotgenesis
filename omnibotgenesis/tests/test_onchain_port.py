"""
OMNIX OnChainDataPort Tests
============================
Unit and integration tests for the On-Chain Data Port.

Tests:
1. Protocol compliance (runtime_checkable)
2. Domain model serialization
3. Adapter fallback behavior
4. Provider error handling
5. Cooldown mechanism
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.omnix.ports.driven.onchain_data_port import (
    OnChainDataPort,
    OnChainMetrics,
    WhaleTransaction,
    WhaleActivity,
    NetworkHealth,
    ExchangeFlows,
    ChainAsset,
    OnChainAPIError
)
from src.omnix.infrastructure.adapters.onchain.blockchain_info_provider import BlockchainInfoProvider
from src.omnix.infrastructure.adapters.onchain.onchain_adapter import OnChainDataAdapter


class TestOnChainModels:
    """Test domain model serialization"""
    
    def test_onchain_metrics_to_dict(self):
        """OnChainMetrics serializes correctly"""
        metrics = OnChainMetrics(
            asset="BTC",
            total_supply=21_000_000,
            circulating_supply=19_800_000,
            hash_rate=700_000_000_000_000_000_000,
            difficulty=72_000_000_000_000,
            avg_block_time=600,
            active_addresses_24h=1_000_000,
            transaction_count_24h=500_000,
            transaction_volume_24h=100_000,
            miners_revenue_24h=50_000_000,
            mempool_size=10_000,
            avg_fee_usd=2.5,
            source="Test",
            timestamp=datetime(2025, 12, 17, 12, 0, 0)
        )
        
        result = metrics.to_dict()
        
        assert result['asset'] == "BTC"
        assert result['total_supply'] == 21_000_000
        assert result['circulating_supply'] == 19_800_000
        assert result['source'] == "Test"
        assert "2025-12-17" in result['timestamp']
    
    def test_whale_transaction_to_dict(self):
        """WhaleTransaction serializes correctly"""
        tx = WhaleTransaction(
            tx_hash="abc123",
            asset="BTC",
            amount=100.5,
            amount_usd=10_000_000,
            from_address="1A1zP1...",
            to_address="bc1qxy...",
            from_entity="Binance",
            to_entity="Unknown",
            direction="exchange_outflow",
            timestamp=datetime(2025, 12, 17, 12, 0, 0)
        )
        
        result = tx.to_dict()
        
        assert result['tx_hash'] == "abc123"
        assert result['amount'] == 100.5
        assert result['from_entity'] == "Binance"
        assert result['direction'] == "exchange_outflow"
    
    def test_whale_activity_to_dict(self):
        """WhaleActivity serializes with nested transactions"""
        tx = WhaleTransaction(
            tx_hash="abc123",
            asset="BTC",
            amount=100.5,
            amount_usd=10_000_000,
            from_address="1A1zP1...",
            to_address="bc1qxy...",
            from_entity=None,
            to_entity=None,
            direction="transfer",
            timestamp=datetime(2025, 12, 17, 12, 0, 0)
        )
        
        activity = WhaleActivity(
            asset="BTC",
            window_hours=24,
            total_transactions=5,
            total_volume=500.0,
            total_volume_usd=50_000_000,
            net_direction="accumulation",
            accumulation_score=0.75,
            transactions=[tx],
            source="Test",
            timestamp=datetime(2025, 12, 17, 12, 0, 0)
        )
        
        result = activity.to_dict()
        
        assert result['total_transactions'] == 5
        assert result['net_direction'] == "accumulation"
        assert len(result['transactions']) == 1
        assert result['transactions'][0]['tx_hash'] == "abc123"
    
    def test_network_health_to_dict(self):
        """NetworkHealth serializes correctly"""
        health = NetworkHealth(
            asset="BTC",
            health_score=0.85,
            congestion_level="low",
            fee_tier="normal",
            confirmation_time_estimate="~60 minutes",
            hash_rate_trend="stable",
            difficulty_adjustment_eta="3 days",
            network_status="operational",
            source="Test",
            timestamp=datetime(2025, 12, 17, 12, 0, 0)
        )
        
        result = health.to_dict()
        
        assert result['health_score'] == 0.85
        assert result['congestion_level'] == "low"
        assert result['network_status'] == "operational"
    
    def test_chain_asset_enum(self):
        """ChainAsset enum has correct values"""
        assert ChainAsset.BTC.value == "bitcoin"
        assert ChainAsset.ETH.value == "ethereum"
        assert ChainAsset.SOL.value == "solana"


class TestOnChainAPIError:
    """Test custom exception"""
    
    def test_retryable_error(self):
        """Retryable errors have correct attributes"""
        error = OnChainAPIError(
            "Rate limit exceeded",
            provider="Blockchain.info",
            retryable=True
        )
        
        assert error.retryable is True
        assert error.provider == "Blockchain.info"
        assert "Rate limit exceeded" in str(error)
    
    def test_non_retryable_error(self):
        """Non-retryable errors have correct attributes"""
        error = OnChainAPIError(
            "Asset not supported",
            provider="Blockchain.info",
            retryable=False
        )
        
        assert error.retryable is False


class TestBlockchainInfoProvider:
    """Test BlockchainInfoProvider adapter"""
    
    @pytest.fixture
    def provider(self):
        return BlockchainInfoProvider()
    
    @pytest.mark.asyncio
    async def test_unsupported_asset_raises_error(self, provider):
        """Non-BTC assets raise OnChainAPIError"""
        with pytest.raises(OnChainAPIError) as exc_info:
            await provider.get_onchain_metrics("ETH")
        
        assert "not supported" in str(exc_info.value)
        assert exc_info.value.retryable is False
    
    @pytest.mark.asyncio
    async def test_whale_activity_returns_empty(self, provider):
        """Whale activity returns placeholder (no API support)"""
        result = await provider.get_whale_activity("BTC", 24)
        
        assert result.asset == "BTC"
        assert result.total_transactions == 0
        assert "limited data" in result.source
    
    @pytest.mark.asyncio
    async def test_exchange_flows_returns_empty(self, provider):
        """Exchange flows returns empty list (no API support)"""
        result = await provider.get_exchange_flows("BTC")
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_close_session(self, provider):
        """Session closes cleanly"""
        await provider.close()
        assert provider._session is None


class TestOnChainDataAdapter:
    """Test multi-provider adapter with fallback"""
    
    @pytest.fixture
    def mock_provider(self):
        provider = MagicMock(spec=BlockchainInfoProvider)
        provider.get_onchain_metrics = AsyncMock()
        provider.get_whale_activity = AsyncMock()
        provider.get_network_health = AsyncMock()
        provider.get_exchange_flows = AsyncMock(return_value=[])
        provider.close = AsyncMock()
        return provider
    
    @pytest.fixture
    def adapter(self, mock_provider):
        return OnChainDataAdapter(
            blockchain_info_provider=mock_provider,
            legacy_service=None
        )
    
    def test_cooldown_initially_false(self, adapter):
        """Adapter starts without cooldown"""
        assert adapter.is_in_cooldown() is False
    
    def test_record_failure_enters_cooldown(self, adapter):
        """Recording failure triggers cooldown"""
        adapter._record_failure()
        
        assert adapter.is_in_cooldown() is True
        assert adapter._failure_count == 1
    
    def test_reset_failures_exits_cooldown(self, adapter):
        """Resetting failures clears cooldown"""
        adapter._record_failure()
        adapter._reset_failures()
        
        assert adapter.is_in_cooldown() is False
        assert adapter._failure_count == 0
    
    def test_cooldown_expires(self, adapter):
        """Cooldown expires after COOLDOWN_SECONDS"""
        adapter._record_failure()
        adapter._last_failure_time = datetime.utcnow() - timedelta(seconds=301)
        
        assert adapter.is_in_cooldown() is False
    
    @pytest.mark.asyncio
    async def test_get_metrics_success(self, adapter, mock_provider):
        """Successful metrics call resets failures"""
        adapter._is_enabled = True
        expected = OnChainMetrics(
            asset="BTC",
            total_supply=21_000_000,
            circulating_supply=19_800_000,
            hash_rate=700_000_000_000_000_000_000,
            difficulty=72_000_000_000_000,
            avg_block_time=600,
            active_addresses_24h=0,
            transaction_count_24h=0,
            transaction_volume_24h=0,
            miners_revenue_24h=0,
            mempool_size=0,
            avg_fee_usd=0,
            source="Blockchain.info",
            timestamp=datetime.utcnow()
        )
        mock_provider.get_onchain_metrics.return_value = expected
        
        result = await adapter.get_onchain_metrics("BTC")
        
        assert result.asset == "BTC"
        assert adapter._failure_count == 0
    
    @pytest.mark.asyncio
    async def test_get_metrics_fallback_on_error(self, adapter, mock_provider):
        """Fallback to legacy on provider error"""
        adapter._is_enabled = True
        mock_provider.get_onchain_metrics.side_effect = OnChainAPIError(
            "API down",
            provider="Blockchain.info",
            retryable=False
        )
        
        result = await adapter.get_onchain_metrics("BTC")
        
        assert "Fallback" in result.source
        assert adapter.is_in_cooldown() is True
    
    @pytest.mark.asyncio
    async def test_disabled_uses_legacy(self, adapter, mock_provider):
        """Disabled adapter uses legacy directly"""
        adapter._is_enabled = False
        
        result = await adapter.get_onchain_metrics("BTC")
        
        mock_provider.get_onchain_metrics.assert_not_called()
        assert "Fallback" in result.source or "Estimated" in result.source
    
    @pytest.mark.asyncio
    async def test_cooldown_uses_legacy(self, adapter, mock_provider):
        """Adapter in cooldown uses legacy"""
        adapter._is_enabled = True
        adapter._record_failure()
        
        result = await adapter.get_onchain_metrics("BTC")
        
        mock_provider.get_onchain_metrics.assert_not_called()
        assert "Fallback" in result.source or "Estimated" in result.source
    
    @pytest.mark.asyncio
    async def test_close_closes_provider(self, adapter, mock_provider):
        """Close delegates to provider"""
        await adapter.close()
        
        mock_provider.close.assert_called_once()


class TestProtocolCompliance:
    """Test that adapter implements OnChainDataPort protocol"""
    
    def test_onchain_adapter_is_runtime_checkable(self):
        """OnChainDataAdapter implements OnChainDataPort"""
        adapter = OnChainDataAdapter()
        
        assert hasattr(adapter, 'get_onchain_metrics')
        assert hasattr(adapter, 'get_whale_activity')
        assert hasattr(adapter, 'get_network_health')
        assert hasattr(adapter, 'get_exchange_flows')
    
    def test_blockchain_info_provider_has_methods(self):
        """BlockchainInfoProvider has required methods"""
        provider = BlockchainInfoProvider()
        
        assert hasattr(provider, 'get_onchain_metrics')
        assert hasattr(provider, 'get_whale_activity')
        assert hasattr(provider, 'get_network_health')
        assert hasattr(provider, 'get_exchange_flows')


class TestContainerIntegration:
    """Test DI container integration"""
    
    def test_container_has_onchain_adapter(self):
        """Container exposes onchain_adapter property"""
        from src.omnix.bootstrap.container import Container
        
        container = Container.create(lazy=True)
        
        assert hasattr(container, 'onchain_adapter')
        assert hasattr(container, 'use_onchain_port')
    
    def test_container_health_check_includes_onchain(self):
        """Health check includes onchain status"""
        from src.omnix.bootstrap.container import Container
        
        container = Container.create(lazy=True)
        health = container.health_check()
        
        assert 'onchain_adapter' in health
        assert 'use_onchain_port' in health


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
