"""
OMNIX Network Metrics Collector V6.5
=====================================

Recolección de métricas de salud de red blockchain.

Métricas clave:
- Active addresses: Indicador de adopción/uso
- Transaction count/volume: Actividad de la red
- Gas fees: Demanda de blockspace
- Hash rate (PoW): Seguridad de la red

Fuentes gratuitas:
- Blockchain.com API (BTC)
- Etherscan API (ETH)
- Messari API (múltiples)
"""

import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .models import NetworkMetrics

logger = logging.getLogger('OMNIX.OnChain.NetworkMetrics')


# APIs públicas gratuitas
BLOCKCHAIN_APIS = {
    'BTC': {
        'stats': 'https://blockchain.info/stats?format=json',
        'charts_base': 'https://api.blockchain.info/charts'
    },
    'ETH': {
        'gas': 'https://api.etherscan.io/api?module=gastracker&action=gasoracle',
        'supply': 'https://api.etherscan.io/api?module=stats&action=ethsupply'
    }
}


@dataclass
class NetworkHealthIndicator:
    """Indicador de salud de red normalizado"""
    metric: str
    value: float
    normalized_score: float  # 0-1
    trend: str  # up, down, stable
    interpretation: str


class NetworkMetricsCollector:
    """
    Collector de métricas de salud de redes blockchain.
    
    Proporciona indicadores sobre:
    - Actividad de la red (transacciones, direcciones activas)
    - Costos de la red (gas fees)
    - Seguridad (hash rate para PoW)
    
    Uso:
        collector = NetworkMetricsCollector()
        metrics = await collector.get_metrics('BTC', hours=24)
        health = collector.calculate_health_score(metrics)
    """
    
    def __init__(self, cache_ttl_seconds: int = 600):
        """
        Inicializa el collector.
        
        Args:
            cache_ttl_seconds: TTL del cache (default 10 min)
        """
        self.cache_ttl = cache_ttl_seconds
        self._cache: Dict[str, tuple] = {}
        self._session: Optional[aiohttp.ClientSession] = None
        self._historical: Dict[str, List[NetworkMetrics]] = {}
        
        logger.info("📈 NetworkMetricsCollector V6.5 initialized")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Obtiene o crea sesión HTTP"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self._session
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Obtiene valor del cache"""
        if key in self._cache:
            timestamp, value = self._cache[key]
            if datetime.utcnow() - timestamp < timedelta(seconds=self.cache_ttl):
                return value
        return None
    
    def _set_cached(self, key: str, value: Any):
        """Guarda en cache"""
        self._cache[key] = (datetime.utcnow(), value)
    
    async def get_btc_metrics(self) -> Optional[NetworkMetrics]:
        """
        Obtiene métricas de Bitcoin desde blockchain.com API.
        
        Returns:
            NetworkMetrics para BTC
        """
        cache_key = "btc_metrics"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            session = await self._get_session()
            
            async with session.get(BLOCKCHAIN_APIS['BTC']['stats']) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Obtener datos anteriores para calcular cambios
                    prev_metrics = None
                    if 'BTC' in self._historical and self._historical['BTC']:
                        prev_metrics = self._historical['BTC'][-1]
                    
                    # Calcular cambios porcentuales
                    n_tx = data.get('n_tx', 0)
                    n_tx_change = 0.0
                    if prev_metrics and prev_metrics.transaction_count > 0:
                        n_tx_change = (n_tx - prev_metrics.transaction_count) / prev_metrics.transaction_count * 100
                    
                    metrics = NetworkMetrics(
                        blockchain='bitcoin',
                        symbol='BTC',
                        period_hours=24,
                        active_addresses=0,  # No disponible directamente
                        active_addresses_change_pct=0.0,
                        transaction_count=n_tx,
                        transaction_volume=data.get('estimated_btc_sent', 0) / 100_000_000,  # Satoshis to BTC
                        transaction_volume_usd=data.get('estimated_transaction_volume_usd', 0),
                        transaction_count_change_pct=n_tx_change,
                        hash_rate=data.get('hash_rate', 0) / 1e9,  # Convert to EH/s
                        hash_rate_change_pct=0.0,
                        avg_gas_fee=None,
                        avg_gas_fee_usd=None,
                        timestamp=datetime.utcnow()
                    )
                    
                    # Calcular health score
                    metrics.network_health_score = self._calculate_btc_health(data)
                    metrics.activity_trend = self._determine_trend(n_tx_change)
                    
                    # Guardar en historial
                    if 'BTC' not in self._historical:
                        self._historical['BTC'] = []
                    self._historical['BTC'].append(metrics)
                    if len(self._historical['BTC']) > 168:  # 7 días
                        self._historical['BTC'].pop(0)
                    
                    self._set_cached(cache_key, metrics)
                    logger.info(f"📊 BTC network metrics: {n_tx} txs, health={metrics.network_health_score:.2f}")
                    
                    return metrics
                    
        except Exception as e:
            logger.error(f"Error fetching BTC metrics: {e}")
        
        return None
    
    async def get_eth_metrics(self, etherscan_api_key: Optional[str] = None) -> Optional[NetworkMetrics]:
        """
        Obtiene métricas de Ethereum.
        
        Args:
            etherscan_api_key: API key de Etherscan (opcional)
            
        Returns:
            NetworkMetrics para ETH
        """
        cache_key = "eth_metrics"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            session = await self._get_session()
            
            # Gas price
            gas_url = BLOCKCHAIN_APIS['ETH']['gas']
            if etherscan_api_key:
                gas_url += f"&apikey={etherscan_api_key}"
            
            gas_gwei = 30  # Default
            async with session.get(gas_url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('status') == '1':
                        result = data.get('result', {})
                        gas_gwei = float(result.get('ProposeGasPrice', 30))
            
            # Calcular costo promedio en USD (asumiendo tx simple de 21000 gas)
            # Necesitaríamos precio de ETH, usar estimación
            eth_price_usd = 2000  # Placeholder, deberíamos obtener precio real
            avg_fee_usd = (gas_gwei * 21000 * 1e-9) * eth_price_usd
            
            metrics = NetworkMetrics(
                blockchain='ethereum',
                symbol='ETH',
                period_hours=24,
                active_addresses=0,
                active_addresses_change_pct=0.0,
                transaction_count=0,
                transaction_volume=0,
                transaction_volume_usd=0,
                transaction_count_change_pct=0.0,
                avg_gas_fee=gas_gwei,
                avg_gas_fee_usd=avg_fee_usd,
                gas_fee_change_pct=0.0,
                timestamp=datetime.utcnow()
            )
            
            # Health basado en gas fees
            # Fees muy altos = congestión (puede ser bueno o malo)
            if gas_gwei < 20:
                metrics.network_health_score = 0.8
                metrics.activity_trend = "low_activity"
            elif gas_gwei < 50:
                metrics.network_health_score = 0.7
                metrics.activity_trend = "normal"
            elif gas_gwei < 100:
                metrics.network_health_score = 0.6
                metrics.activity_trend = "high_demand"
            else:
                metrics.network_health_score = 0.4
                metrics.activity_trend = "congested"
            
            self._set_cached(cache_key, metrics)
            logger.info(f"📊 ETH network metrics: {gas_gwei} gwei, health={metrics.network_health_score:.2f}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error fetching ETH metrics: {e}")
        
        return None
    
    async def get_metrics(
        self,
        symbol: str,
        hours: int = 24
    ) -> Optional[NetworkMetrics]:
        """
        Obtiene métricas de red para un símbolo.
        
        Args:
            symbol: Símbolo del activo (BTC, ETH, SOL)
            hours: Período de análisis
            
        Returns:
            NetworkMetrics o None
        """
        symbol = symbol.upper()
        
        if symbol == 'BTC':
            return await self.get_btc_metrics()
        elif symbol == 'ETH':
            return await self.get_eth_metrics()
        else:
            # Para otros símbolos, retornar métricas simuladas
            logger.debug(f"No direct metrics API for {symbol}, using estimates")
            return self._generate_estimated_metrics(symbol, hours)
    
    def _generate_estimated_metrics(
        self,
        symbol: str,
        hours: int
    ) -> NetworkMetrics:
        """Genera métricas estimadas para símbolos sin API directa"""
        return NetworkMetrics(
            blockchain=symbol.lower(),
            symbol=symbol,
            period_hours=hours,
            active_addresses=0,
            active_addresses_change_pct=0.0,
            transaction_count=0,
            transaction_volume=0,
            transaction_volume_usd=0,
            transaction_count_change_pct=0.0,
            network_health_score=0.5,
            activity_trend="unknown"
        )
    
    def _calculate_btc_health(self, data: Dict) -> float:
        """
        Calcula score de salud para Bitcoin.
        
        Factores:
        - Hash rate (seguridad)
        - Transaction count (adopción)
        - Market cap (valor)
        """
        score = 0.5  # Base
        
        # Hash rate > 400 EH/s es muy saludable
        hash_rate = data.get('hash_rate', 0) / 1e18  # En EH/s
        if hash_rate > 500:
            score += 0.2
        elif hash_rate > 400:
            score += 0.15
        elif hash_rate > 300:
            score += 0.1
        
        # Transaction count
        n_tx = data.get('n_tx', 0)
        if n_tx > 500000:
            score += 0.15
        elif n_tx > 300000:
            score += 0.1
        elif n_tx > 200000:
            score += 0.05
        
        # Limitar a 0-1
        return max(0.0, min(1.0, score))
    
    def _determine_trend(self, change_pct: float) -> str:
        """Determina tendencia basada en cambio porcentual"""
        if change_pct > 10:
            return "increasing"
        elif change_pct < -10:
            return "decreasing"
        else:
            return "stable"
    
    def get_health_indicators(
        self,
        metrics: NetworkMetrics
    ) -> List[NetworkHealthIndicator]:
        """
        Genera indicadores de salud individuales.
        
        Args:
            metrics: NetworkMetrics a analizar
            
        Returns:
            Lista de indicadores de salud
        """
        indicators = []
        
        # Transaction activity
        if metrics.transaction_count > 0:
            indicators.append(NetworkHealthIndicator(
                metric="transaction_activity",
                value=metrics.transaction_count,
                normalized_score=min(1.0, metrics.transaction_count / 500000),
                trend=self._determine_trend(metrics.transaction_count_change_pct),
                interpretation=f"{metrics.transaction_count:,} transactions in {metrics.period_hours}h"
            ))
        
        # Gas fees (for ETH)
        if metrics.avg_gas_fee is not None:
            # Lower fees = better (inverted score)
            fee_score = max(0.0, 1.0 - (metrics.avg_gas_fee / 200))
            indicators.append(NetworkHealthIndicator(
                metric="gas_fees",
                value=metrics.avg_gas_fee,
                normalized_score=fee_score,
                trend="low" if metrics.avg_gas_fee < 30 else "high" if metrics.avg_gas_fee > 80 else "normal",
                interpretation=f"{metrics.avg_gas_fee:.1f} gwei average"
            ))
        
        # Hash rate (for PoW)
        if metrics.hash_rate is not None and metrics.hash_rate > 0:
            # Higher = better, normalize to typical BTC range
            hr_score = min(1.0, metrics.hash_rate / 600)  # 600 EH/s as max
            indicators.append(NetworkHealthIndicator(
                metric="hash_rate",
                value=metrics.hash_rate,
                normalized_score=hr_score,
                trend=self._determine_trend(metrics.hash_rate_change_pct or 0),
                interpretation=f"{metrics.hash_rate:.1f} EH/s network security"
            ))
        
        return indicators
    
    async def close(self):
        """Cierra la sesión HTTP"""
        if self._session and not self._session.closed:
            await self._session.close()
