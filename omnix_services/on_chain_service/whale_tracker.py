"""
OMNIX Whale Tracker V6.5
=========================

Tracking de transacciones de ballenas usando APIs gratuitas:
- ClankApp: 24 blockchains, transacciones grandes
- Arkham Intelligence: Identidad de wallets, portfolios

Detecta:
- Movimientos grandes a/desde exchanges
- Acumulación por wallets conocidas
- Patrones de distribución
"""

import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json

from .models import (
    WhaleTransaction,
    FlowDirection,
    TransactionType,
    MarketBias
)

logger = logging.getLogger('OMNIX.OnChain.WhaleTracker')


# ============================================================================
# ARKHAM INTELLIGENCE INTEGRATION V6.5
# ============================================================================

class ArkhamClient:
    """
    Cliente para Arkham Intelligence API.
    
    Arkham proporciona:
    - Identidad de wallets (instituciones, exchanges, fondos)
    - Alertas de movimientos de whales
    - Portfolios de entidades conocidas
    
    API Base: https://api.arkhamintelligence.com
    Nota: Features premium requieren API key
    """
    
    ARKHAM_API_BASE = "https://api.arkhamintelligence.com/intelligence"
    
    # Labels conocidos de Arkham (public data)
    KNOWN_ENTITIES = {
        'binance': {'type': 'exchange', 'risk': 'low'},
        'coinbase': {'type': 'exchange', 'risk': 'low'},
        'ftx': {'type': 'exchange', 'risk': 'high'},
        'jump_trading': {'type': 'market_maker', 'risk': 'low'},
        'alameda': {'type': 'trading_firm', 'risk': 'high'},
        'three_arrows': {'type': 'hedge_fund', 'risk': 'high'},
        'grayscale': {'type': 'institution', 'risk': 'low'},
        'microstrategy': {'type': 'institution', 'risk': 'low'},
        'blackrock': {'type': 'institution', 'risk': 'low'},
        'fidelity': {'type': 'institution', 'risk': 'low'},
    }
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 10):
        self.api_key = api_key
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None
        self._label_cache: Dict[str, Dict] = {}
        self._cache_ttl = 3600  # 1 hour
        self._last_cache_update: Dict[str, datetime] = {}
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            headers = {'Accept': 'application/json'}
            if self.api_key:
                headers['API-Key'] = self.api_key
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers=headers
            )
        return self._session
    
    async def get_address_label(self, address: str, chain: str = 'ethereum') -> Optional[Dict]:
        """
        Obtiene el label/identidad de una dirección.
        
        Args:
            address: Dirección blockchain
            chain: Cadena (ethereum, bitcoin, etc.)
            
        Returns:
            Dict con entity info o None
        """
        cache_key = f"{chain}:{address.lower()}"
        
        # Check cache
        if cache_key in self._label_cache:
            last_update = self._last_cache_update.get(cache_key)
            if last_update and (datetime.utcnow() - last_update).seconds < self._cache_ttl:
                return self._label_cache[cache_key]
        
        try:
            session = await self._get_session()
            
            # Arkham's public entity lookup (if available)
            url = f"{self.ARKHAM_API_BASE}/address/{chain}/{address}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    entity = data.get('entity', {})
                    
                    result = {
                        'address': address,
                        'chain': chain,
                        'name': entity.get('name'),
                        'type': entity.get('type'),
                        'is_exchange': entity.get('type') == 'exchange',
                        'is_institution': entity.get('type') in ['institution', 'hedge_fund', 'trading_firm'],
                        'risk_level': entity.get('risk', 'unknown'),
                        'arkham_score': entity.get('score'),
                        'source': 'arkham'
                    }
                    
                    self._label_cache[cache_key] = result
                    self._last_cache_update[cache_key] = datetime.utcnow()
                    
                    return result
                elif response.status == 404:
                    # Address not in Arkham database
                    return None
                else:
                    logger.debug(f"Arkham API returned {response.status}")
                    return None
                    
        except aiohttp.ClientError as e:
            logger.debug(f"Arkham API error: {e}")
        except Exception as e:
            logger.debug(f"Arkham lookup error: {e}")
        
        return None
    
    async def get_whale_alerts(self, chain: str = 'all', limit: int = 50) -> List[Dict]:
        """
        Obtiene alertas recientes de whales desde Arkham.
        
        Args:
            chain: Blockchain específica o 'all'
            limit: Número máximo de alertas
            
        Returns:
            Lista de alertas de whale
        """
        alerts = []
        
        try:
            session = await self._get_session()
            
            url = f"{self.ARKHAM_API_BASE}/alerts/whale"
            params = {'chain': chain, 'limit': limit}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    alerts = data.get('alerts', [])
                    logger.debug(f"Arkham: {len(alerts)} whale alerts fetched")
                    
        except Exception as e:
            logger.debug(f"Arkham alerts error: {e}")
        
        return alerts
    
    def enrich_local_label(self, address: str) -> Optional[Dict]:
        """
        Enriquece una dirección con datos locales conocidos.
        
        Fallback cuando API no está disponible.
        """
        addr_lower = address.lower()
        
        for entity, info in self.KNOWN_ENTITIES.items():
            # This would match against known addresses
            pass
        
        return None
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()


# Wallets de exchanges conocidas para clasificación
KNOWN_EXCHANGE_WALLETS = {
    'ethereum': {
        '0x28c6c06298d514db089934071355e5743bf21d60': 'Binance',
        '0x21a31ee1afc51d94c2efccaa2092ad1028285549': 'Binance',
        '0xdfd5293d8e347dfe59e90efd55b2956a1343963d': 'Binance',
        '0x56eddb7aa87536c09ccc2793473599fd21a8b17f': 'Binance',
        '0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43': 'Coinbase',
        '0x71660c4005ba85c37ccec55d0c4493e66fe775d3': 'Coinbase',
        '0x503828976d22510aad0201ac7ec88293211d23da': 'Coinbase',
        '0x2faf487a4414fe77e2327f0bf4ae2a264a776ad2': 'FTX',  # Historical
        '0xc098b2a3aa256d2140208c3de6543aaef5cd3a94': 'FTX',  # Historical
        '0x267be1c1d684f78cb4f6a176c4911b741e4ffdc0': 'Kraken',
        '0x2910543af39aba0cd09dbb2d50200b3e800a63d2': 'Kraken',
        '0x0d0707963952f2fba59dd06f2b425ace40b492fe': 'Gate.io',
        '0x1c4b70a3968436b9a0a9cf5205c787eb81bb558c': 'Gate.io',
    },
    'bitcoin': {
        '1NDyJtNTjmwk5xPNhjgAMu4HDHigtobu1s': 'Binance',
        '3M219KR5vEneNb47ewrPfWyb5jQ2DjxRP6': 'Binance',
        'bc1qm34lsc65zpw79lxes69zkqmk6ee3ewf0j77s3h': 'Binance',
        '3Kzh9qAqVWQhEsfQz7zEQL1EuSx5tyNLNS': 'Bitfinex',
        '1KYiKJEfdJtap9QX2v9BXJMpz2SfU4pgZw': 'Bitfinex',
        '3JZq4atUahhuA9rLhXLMhhTo133J9rF97j': 'Bitfinex',
    }
}

# Umbrales para considerar transacción como "whale"
WHALE_THRESHOLDS_USD = {
    'BTC': 1_000_000,
    'ETH': 500_000,
    'SOL': 250_000,
    'XRP': 500_000,
    'default': 500_000
}


class WhaleTracker:
    """
    Tracker de transacciones de ballenas.
    
    Fuentes:
    - ClankApp API (GRATIS): Transacciones grandes en 24+ blockchains
    - Arkham Intelligence (GRATIS): Identidad de wallets y alertas
    
    Uso:
        tracker = WhaleTracker()
        transactions = await tracker.get_whale_transactions('BTC', hours=24)
    """
    
    # API Endpoints
    CLANKAPP_API = "https://clankapp.com/api/v1"
    
    # Circuit breaker settings
    MAX_FAILURES = 3
    FAILURE_WINDOW_SECONDS = 300
    
    def __init__(self, cache_ttl_seconds: int = 300, arkham_api_key: Optional[str] = None):
        """
        Inicializa el WhaleTracker.
        
        Args:
            cache_ttl_seconds: TTL del cache en segundos (default 5 min)
            arkham_api_key: API key para Arkham Intelligence (opcional)
        """
        self.cache_ttl = cache_ttl_seconds
        self._cache: Dict[str, Tuple[datetime, Any]] = {}
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Arkham Intelligence client
        self.arkham = ArkhamClient(api_key=arkham_api_key, timeout=10)
        
        # Circuit breaker state
        self._api_failures: Dict[str, List[datetime]] = {}
        self._circuit_open: Dict[str, bool] = {}
        
        logger.info("🐋 WhaleTracker initialized - ClankApp + Arkham integration")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Obtiene o crea sesión HTTP"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    'User-Agent': 'OMNIX/6.5 WhaleTracker',
                    'Accept': 'application/json'
                }
            )
        return self._session
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Obtiene valor del cache si no ha expirado"""
        if key in self._cache:
            timestamp, value = self._cache[key]
            if datetime.utcnow() - timestamp < timedelta(seconds=self.cache_ttl):
                return value
            del self._cache[key]
        return None
    
    def _set_cached(self, key: str, value: Any):
        """Guarda valor en cache"""
        self._cache[key] = (datetime.utcnow(), value)
    
    def _classify_address(self, address: str, blockchain: str) -> Optional[str]:
        """Clasifica una dirección como exchange u otro tipo conocido"""
        chain_wallets = KNOWN_EXCHANGE_WALLETS.get(blockchain.lower(), {})
        return chain_wallets.get(address.lower())
    
    def _check_circuit_breaker(self, api_name: str) -> bool:
        """
        Verifica si el circuit breaker está abierto para un API.
        
        Returns:
            True si podemos hacer la llamada, False si el circuito está abierto
        """
        if self._circuit_open.get(api_name, False):
            # Check if we can reset
            failures = self._api_failures.get(api_name, [])
            if failures:
                oldest = failures[0]
                if (datetime.utcnow() - oldest).seconds > self.FAILURE_WINDOW_SECONDS * 2:
                    # Reset circuit breaker
                    self._circuit_open[api_name] = False
                    self._api_failures[api_name] = []
                    logger.info(f"Circuit breaker reset for {api_name}")
                    return True
            return False
        return True
    
    def _record_api_failure(self, api_name: str):
        """Registra un fallo de API para el circuit breaker"""
        now = datetime.utcnow()
        
        if api_name not in self._api_failures:
            self._api_failures[api_name] = []
        
        # Remove old failures
        self._api_failures[api_name] = [
            f for f in self._api_failures[api_name]
            if (now - f).seconds < self.FAILURE_WINDOW_SECONDS
        ]
        
        self._api_failures[api_name].append(now)
        
        # Check if we should open the circuit
        if len(self._api_failures[api_name]) >= self.MAX_FAILURES:
            self._circuit_open[api_name] = True
            logger.warning(f"Circuit breaker OPEN for {api_name} after {self.MAX_FAILURES} failures")
    
    async def _enrich_with_arkham(self, tx: WhaleTransaction) -> WhaleTransaction:
        """
        Enriquece una transacción con datos de Arkham Intelligence.
        
        Agrega información de identidad para from/to addresses.
        """
        if not self._check_circuit_breaker('arkham'):
            return tx
        
        try:
            # Enrich from address
            if tx.from_address and not tx.from_label:
                from_info = await self.arkham.get_address_label(
                    tx.from_address, tx.blockchain
                )
                if from_info and from_info.get('name'):
                    tx.from_label = from_info['name']
                    if from_info.get('is_exchange'):
                        tx.is_exchange_related = True
                        tx.flow_direction = FlowDirection.OUTFLOW
                        tx.transaction_type = TransactionType.EXCHANGE_WITHDRAWAL
            
            # Enrich to address
            if tx.to_address and not tx.to_label:
                to_info = await self.arkham.get_address_label(
                    tx.to_address, tx.blockchain
                )
                if to_info and to_info.get('name'):
                    tx.to_label = to_info['name']
                    if to_info.get('is_exchange'):
                        tx.is_exchange_related = True
                        tx.flow_direction = FlowDirection.INFLOW
                        tx.transaction_type = TransactionType.EXCHANGE_DEPOSIT
            
        except Exception as e:
            self._record_api_failure('arkham')
            logger.debug(f"Arkham enrichment failed: {e}")
        
        return tx
    
    def _get_whale_threshold(self, symbol: str) -> float:
        """Obtiene umbral de whale para un símbolo"""
        return WHALE_THRESHOLDS_USD.get(symbol.upper(), WHALE_THRESHOLDS_USD['default'])
    
    async def _fetch_with_retry(
        self,
        url: str,
        params: Optional[Dict] = None,
        max_retries: int = 3,
        api_name: str = 'clankapp'
    ) -> Optional[Dict]:
        """
        Fetch con retry y circuit breaker.
        
        Args:
            url: URL a llamar
            params: Query parameters
            max_retries: Número máximo de reintentos
            api_name: Nombre del API para circuit breaker
            
        Returns:
            Response JSON o None
        """
        if not self._check_circuit_breaker(api_name):
            logger.debug(f"{api_name} circuit breaker is open, skipping")
            return None
        
        session = await self._get_session()
        last_error = None
        
        for attempt in range(max_retries):
            try:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:
                        # Rate limited, wait and retry
                        await asyncio.sleep(2 ** attempt)
                    else:
                        logger.debug(f"{api_name} returned {response.status}")
                        if attempt == max_retries - 1:
                            self._record_api_failure(api_name)
                        
            except asyncio.TimeoutError:
                last_error = "timeout"
                logger.debug(f"{api_name} timeout on attempt {attempt + 1}")
                await asyncio.sleep(1)
            except aiohttp.ClientError as e:
                last_error = str(e)
                logger.debug(f"{api_name} error: {e}")
                await asyncio.sleep(1)
        
        self._record_api_failure(api_name)
        logger.warning(f"{api_name} failed after {max_retries} attempts: {last_error}")
        return None

    async def get_whale_transactions_clankapp(
        self,
        symbol: str,
        limit: int = 50,
        enrich_arkham: bool = True
    ) -> List[WhaleTransaction]:
        """
        Obtiene transacciones de ballenas desde ClankApp.
        
        ClankApp es 100% gratuito y cubre 24+ blockchains.
        
        Args:
            symbol: Símbolo del activo (BTC, ETH, SOL, etc.)
            limit: Número máximo de transacciones
            enrich_arkham: Si enriquecer con datos de Arkham
            
        Returns:
            Lista de WhaleTransaction
        """
        cache_key = f"clankapp_{symbol}_{limit}"
        cached = self._get_cached(cache_key)
        if cached:
            logger.debug(f"Cache hit for ClankApp {symbol}")
            return cached
        
        transactions = []
        blockchain_map = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'SOL': 'solana',
            'XRP': 'ripple',
            'DOGE': 'dogecoin',
            'LTC': 'litecoin',
            'ADA': 'cardano',
            'DOT': 'polkadot',
            'MATIC': 'polygon',
            'AVAX': 'avalanche'
        }
        
        blockchain = blockchain_map.get(symbol.upper(), symbol.lower())
        
        # Use retry helper
        url = f"{self.CLANKAPP_API}/whales/{blockchain}"
        data = await self._fetch_with_retry(url, params={'limit': limit}, api_name='clankapp')
        
        if data:
            threshold = self._get_whale_threshold(symbol)
            
            tx_list = data.get('transactions', data if isinstance(data, list) else [])
            
            for tx in tx_list:
                try:
                    amount_usd = float(tx.get('amount_usd', tx.get('usd_value', 0)))
                    
                    if amount_usd >= threshold:
                        from_addr = tx.get('from', tx.get('from_address', ''))
                        to_addr = tx.get('to', tx.get('to_address', ''))
                        
                        from_label = self._classify_address(from_addr, blockchain)
                        to_label = self._classify_address(to_addr, blockchain)
                        
                        # Determinar tipo y dirección
                        is_exchange = from_label is not None or to_label is not None
                        flow_dir = None
                        tx_type = TransactionType.TRANSFER
                        
                        if from_label and not to_label:
                            flow_dir = FlowDirection.OUTFLOW  # Saliendo de exchange
                            tx_type = TransactionType.EXCHANGE_WITHDRAWAL
                        elif to_label and not from_label:
                            flow_dir = FlowDirection.INFLOW  # Entrando a exchange
                            tx_type = TransactionType.EXCHANGE_DEPOSIT
                        
                        whale_tx = WhaleTransaction(
                            tx_hash=tx.get('hash', tx.get('tx_hash', '')),
                            blockchain=blockchain,
                            symbol=symbol.upper(),
                            amount=float(tx.get('amount', 0)),
                            amount_usd=amount_usd,
                            from_address=from_addr,
                            to_address=to_addr,
                            from_label=from_label,
                            to_label=to_label,
                            transaction_type=tx_type,
                            timestamp=datetime.fromisoformat(
                                tx.get('timestamp', tx.get('time', datetime.utcnow().isoformat()))
                                .replace('Z', '+00:00')
                            ) if isinstance(tx.get('timestamp', tx.get('time')), str) else datetime.utcnow(),
                            block_number=tx.get('block', tx.get('block_number')),
                            is_exchange_related=is_exchange,
                            flow_direction=flow_dir,
                            market_impact_score=min(amount_usd / 10_000_000, 1.0)
                        )
                        transactions.append(whale_tx)
                except Exception as e:
                    logger.debug(f"Error parsing transaction: {e}")
                    continue
            
            # Enrich with Arkham if enabled
            if enrich_arkham and transactions:
                enriched = []
                for tx in transactions[:10]:  # Limit Arkham calls
                    enriched_tx = await self._enrich_with_arkham(tx)
                    enriched.append(enriched_tx)
                # Keep non-enriched for remaining
                enriched.extend(transactions[10:])
                transactions = enriched
            
            logger.info(f"🐋 ClankApp: {len(transactions)} whale transactions for {symbol}")
        
        if transactions:
            self._set_cached(cache_key, transactions)
        
        return transactions
    
    async def get_whale_transactions_fallback(
        self,
        symbol: str,
        limit: int = 50
    ) -> List[WhaleTransaction]:
        """
        Fallback usando datos públicos de exploradores de blockchain.
        
        Usa APIs públicas gratuitas como etherscan, blockchair, etc.
        """
        transactions = []
        
        # Mapeo de símbolos a APIs de explorador
        explorer_apis = {
            'BTC': 'https://blockchair.com/bitcoin/blocks?q=transaction_count(100..)&s=time(desc)&limit=10',
            'ETH': 'https://api.etherscan.io/api?module=account&action=txlist&address=0x0&sort=desc&page=1&offset=10',
        }
        
        # Por ahora, generar datos simulados basados en patrones típicos
        # En producción, esto se conectaría a APIs reales
        
        logger.debug(f"Using fallback whale data for {symbol}")
        
        return transactions
    
    async def get_whale_transactions(
        self,
        symbol: str,
        hours: int = 24,
        limit: int = 100
    ) -> List[WhaleTransaction]:
        """
        Obtiene transacciones de ballenas de múltiples fuentes.
        
        Args:
            symbol: Símbolo del activo
            hours: Ventana de tiempo en horas
            limit: Número máximo de transacciones
            
        Returns:
            Lista de WhaleTransaction ordenadas por timestamp
        """
        all_transactions = []
        
        # Intentar ClankApp primero
        clankapp_txs = await self.get_whale_transactions_clankapp(symbol, limit)
        all_transactions.extend(clankapp_txs)
        
        # Si no hay datos, usar fallback
        if not all_transactions:
            fallback_txs = await self.get_whale_transactions_fallback(symbol, limit)
            all_transactions.extend(fallback_txs)
        
        # Filtrar por tiempo
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        filtered = [tx for tx in all_transactions if tx.timestamp >= cutoff]
        
        # Ordenar por timestamp descendente
        filtered.sort(key=lambda x: x.timestamp, reverse=True)
        
        return filtered[:limit]
    
    def analyze_whale_activity(
        self,
        transactions: List[WhaleTransaction]
    ) -> Dict[str, Any]:
        """
        Analiza la actividad de ballenas para generar señales.
        
        Returns:
            Dict con métricas de actividad:
            - total_volume_usd: Volumen total
            - inflow_volume_usd: Volumen hacia exchanges
            - outflow_volume_usd: Volumen desde exchanges
            - net_flow_usd: Flujo neto
            - whale_activity_score: Score -1 a 1
            - market_bias: bullish/bearish/neutral
        """
        if not transactions:
            return {
                'total_volume_usd': 0,
                'inflow_volume_usd': 0,
                'outflow_volume_usd': 0,
                'net_flow_usd': 0,
                'whale_activity_score': 0.0,
                'market_bias': 'neutral',
                'transaction_count': 0
            }
        
        inflow_volume = sum(
            tx.amount_usd for tx in transactions 
            if tx.flow_direction == FlowDirection.INFLOW
        )
        
        outflow_volume = sum(
            tx.amount_usd for tx in transactions 
            if tx.flow_direction == FlowDirection.OUTFLOW
        )
        
        total_volume = sum(tx.amount_usd for tx in transactions)
        net_flow = inflow_volume - outflow_volume
        
        # Calcular score: -1 (bearish/inflows) a 1 (bullish/outflows)
        if total_volume > 0:
            score = -net_flow / total_volume  # Negativo si más inflows
        else:
            score = 0.0
        
        # Determinar sesgo
        if score > 0.2:
            bias = 'bullish'
        elif score < -0.2:
            bias = 'bearish'
        else:
            bias = 'neutral'
        
        return {
            'total_volume_usd': total_volume,
            'inflow_volume_usd': inflow_volume,
            'outflow_volume_usd': outflow_volume,
            'net_flow_usd': net_flow,
            'whale_activity_score': max(-1, min(1, score)),
            'market_bias': bias,
            'transaction_count': len(transactions)
        }
    
    async def close(self):
        """Cierra la sesión HTTP"""
        if self._session and not self._session.closed:
            await self._session.close()
