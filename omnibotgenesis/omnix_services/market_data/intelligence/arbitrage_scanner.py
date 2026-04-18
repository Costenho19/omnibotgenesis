"""
OMNIX V6.0 ULTRA - Multi-Exchange Arbitrage Scanner Premium
Soporte para 8 exchanges institucionales con detección en tiempo real
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

# Check if trading is available
try:
    import ccxt
    TRADING_AVAILABLE = True
except ImportError:
    TRADING_AVAILABLE = False
    logger.warning("⚠️ CCXT not available - arbitrage detection disabled")


class MultiExchangeArbitragePremium:
    """
    Arbitraje multi-exchange PREMIUM (8 exchanges institucionales)
    
    Exchanges soportados:
    - Kraken (Tier 1 - Regulado USA/Europa)
    - Binance (Mayor liquidez global)
    - Coinbase (Institucional USA)
    - Bybit (Derivados + Spot)
    - KuCoin (Altcoins + Liquidez)
    - OKX (Asia + Global)
    - Gate.io (Mayor variedad de pares)
    - Bitfinex (Institucional + Liquidez profunda)
    """
    
    def __init__(self):
        self.exchanges_config = {
            'kraken': {'enabled': True, 'tier': 1, 'fees': 0.16},
            'binance': {'enabled': True, 'tier': 1, 'fees': 0.10},
            'coinbase': {'enabled': True, 'tier': 1, 'fees': 0.50},
            'bybit': {'enabled': True, 'tier': 2, 'fees': 0.10},
            'kucoin': {'enabled': True, 'tier': 2, 'fees': 0.10},
            'okx': {'enabled': True, 'tier': 2, 'fees': 0.10},
            'gateio': {'enabled': True, 'tier': 2, 'fees': 0.15},
            'bitfinex': {'enabled': True, 'tier': 1, 'fees': 0.20}
        }
        
        self.min_profit_threshold = 0.3  # Mínimo 0.3% profit después de fees
        logger.info(f"🏦 Arbitrage Scanner Premium initialized - {len(self.exchanges_config)} exchanges")
        
    def normalize_symbol(self, symbol: str, exchange_name: str) -> str:
        """Normalizar símbolo según formato del exchange"""
        symbol_map = {
            'kraken': {
                'BTC/USD': 'BTC/USD',
                'BTC/USDT': 'XBT/USDT',
                'ETH/USD': 'ETH/USD',
                'ETH/USDT': 'ETH/USDT'
            },
            'binance': {
                'BTC/USD': 'BTC/USDT',  # Binance usa USDT
                'BTC/USDT': 'BTC/USDT',
                'ETH/USD': 'ETH/USDT',
                'ETH/USDT': 'ETH/USDT'
            }
        }
        
        if exchange_name in symbol_map and symbol in symbol_map[exchange_name]:
            return symbol_map[exchange_name][symbol]
        return symbol
    
    def get_exchange_instance(self, exchange_name: str) -> Optional[object]:
        """Crear instancia de exchange con configuración optimizada"""
        if not TRADING_AVAILABLE:
            return None
            
        try:
            import ccxt
            
            exchange_classes = {
                'kraken': ccxt.kraken,
                'binance': ccxt.binance,
                'coinbase': ccxt.coinbase,
                'bybit': ccxt.bybit,
                'kucoin': ccxt.kucoin,
                'okx': ccxt.okx,
                'gateio': ccxt.gateio,
                'bitfinex': ccxt.bitfinex
            }
            
            if exchange_name not in exchange_classes:
                logger.warning(f"Exchange {exchange_name} not supported")
                return None
            
            # Configuración optimizada para velocidad
            exchange = exchange_classes[exchange_name]({
                'enableRateLimit': True,
                'rateLimit': 50,  # ms entre requests
                'timeout': 5000,  # 5 segundos timeout
            })
            
            return exchange
            
        except Exception as e:
            logger.error(f"Error creating {exchange_name} instance: {e}")
            return None
    
    def fetch_price_from_exchange(self, exchange_name: str, symbol: str) -> Optional[Dict]:
        """Obtener precio de un exchange específico"""
        try:
            if not self.exchanges_config.get(exchange_name, {}).get('enabled', False):
                return None
            
            exchange = self.get_exchange_instance(exchange_name)
            if not exchange:
                return None
            
            normalized_symbol = self.normalize_symbol(symbol, exchange_name)
            ticker = exchange.fetch_ticker(normalized_symbol)
            
            if not ticker or 'last' not in ticker:
                logger.debug(f"{exchange_name}: No ticker data for {normalized_symbol}")
                return None
            
            price_data = {
                'exchange': exchange_name,
                'symbol': normalized_symbol,
                'price': float(ticker['last']),
                'bid': float(ticker.get('bid', ticker['last'])),
                'ask': float(ticker.get('ask', ticker['last'])),
                'volume_24h': float(ticker.get('quoteVolume', 0)),
                'timestamp': ticker.get('timestamp', int(datetime.now().timestamp() * 1000)),
                'fees_pct': self.exchanges_config[exchange_name]['fees']
            }
            
            logger.debug(f"✅ {exchange_name}: ${price_data['price']:,.2f} (vol: ${price_data['volume_24h']:,.0f})")
            return price_data
            
        except Exception as e:
            logger.debug(f"❌ {exchange_name} fetch error: {str(e)[:100]}")
            return None
    
    def check_arbitrage_opportunities(self, symbol: str = 'BTC/USD', 
                                     min_profit_pct: float = None) -> Dict:
        """
        Buscar oportunidades de arbitraje en 8 exchanges
        
        Args:
            symbol: Par de trading (BTC/USD, ETH/USD, etc.)
            min_profit_pct: Profit mínimo requerido (default: 0.3%)
            
        Returns:
            Dict con opportunities, prices, statistics
        """
        try:
            if not TRADING_AVAILABLE:
                return {
                    'success': False,
                    'error': 'CCXT not available',
                    'opportunities': []
                }
            
            min_profit = min_profit_pct if min_profit_pct is not None else self.min_profit_threshold
            
            logger.info(f"🔍 Scanning {len(self.exchanges_config)} exchanges for {symbol}...")
            
            # Fetch prices from all exchanges
            prices = {}
            for exchange_name in self.exchanges_config.keys():
                price_data = self.fetch_price_from_exchange(exchange_name, symbol)
                if price_data:
                    prices[exchange_name] = price_data
            
            if len(prices) < 2:
                return {
                    'success': False,
                    'error': f'Insufficient exchanges with data (got {len(prices)}, need 2+)',
                    'opportunities': [],
                    'prices': prices
                }
            
            # Detectar oportunidades de arbitraje
            opportunities = []
            exchanges = list(prices.keys())
            
            for i, buy_ex in enumerate(exchanges):
                for sell_ex in exchanges[i+1:]:
                    buy_data = prices[buy_ex]
                    sell_data = prices[sell_ex]
                    
                    # Usar ask price para compra, bid price para venta (real slippage)
                    buy_price = buy_data['ask']
                    sell_price = sell_data['bid']
                    
                    # Calcular fees totales
                    total_fees = buy_data['fees_pct'] + sell_data['fees_pct']
                    
                    # Calcular profit neto
                    if sell_price > buy_price:
                        gross_profit_pct = ((sell_price - buy_price) / buy_price) * 100
                        net_profit_pct = gross_profit_pct - total_fees
                        
                        if net_profit_pct >= min_profit:
                            opportunity = {
                                'buy_exchange': buy_ex,
                                'sell_exchange': sell_ex,
                                'buy_price': buy_price,
                                'sell_price': sell_price,
                                'spread_pct': gross_profit_pct,
                                'fees_pct': total_fees,
                                'net_profit_pct': net_profit_pct,
                                'profit_per_1k_usd': (net_profit_pct / 100) * 1000,
                                'profit_per_10k_usd': (net_profit_pct / 100) * 10000,
                                'volume_buy': buy_data['volume_24h'],
                                'volume_sell': sell_data['volume_24h'],
                                'timestamp': datetime.now().isoformat()
                            }
                            opportunities.append(opportunity)
                            
                    # Revisar dirección opuesta
                    elif buy_price > sell_price:
                        gross_profit_pct = ((buy_price - sell_price) / sell_price) * 100
                        net_profit_pct = gross_profit_pct - total_fees
                        
                        if net_profit_pct >= min_profit:
                            opportunity = {
                                'buy_exchange': sell_ex,
                                'sell_exchange': buy_ex,
                                'buy_price': sell_price,
                                'sell_price': buy_price,
                                'spread_pct': gross_profit_pct,
                                'fees_pct': total_fees,
                                'net_profit_pct': net_profit_pct,
                                'profit_per_1k_usd': (net_profit_pct / 100) * 1000,
                                'profit_per_10k_usd': (net_profit_pct / 100) * 10000,
                                'volume_buy': sell_data['volume_24h'],
                                'volume_sell': buy_data['volume_24h'],
                                'timestamp': datetime.now().isoformat()
                            }
                            opportunities.append(opportunity)
            
            # Ordenar por profit descendente
            opportunities.sort(key=lambda x: x['net_profit_pct'], reverse=True)
            
            # Estadísticas
            stats = {
                'total_exchanges_scanned': len(self.exchanges_config),
                'exchanges_with_data': len(prices),
                'total_opportunities': len(opportunities),
                'best_profit_pct': opportunities[0]['net_profit_pct'] if opportunities else 0,
                'avg_profit_pct': sum(o['net_profit_pct'] for o in opportunities) / len(opportunities) if opportunities else 0,
                'total_potential_profit_10k': sum(o['profit_per_10k_usd'] for o in opportunities) if opportunities else 0
            }
            
            logger.info(f"✅ Found {len(opportunities)} arbitrage opportunities")
            if opportunities:
                best = opportunities[0]
                logger.info(f"🏆 Best: {best['buy_exchange']} → {best['sell_exchange']}: {best['net_profit_pct']:.2f}% net profit")
            
            return {
                'success': True,
                'symbol': symbol,
                'opportunities': opportunities,
                'prices': prices,
                'statistics': stats,
                'timestamp': datetime.now().isoformat(),
                'scan_duration_ms': 0  # TODO: Add timing
            }
            
        except Exception as e:
            logger.error(f"❌ Arbitrage scan failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'opportunities': []
            }
    
    def get_top_opportunities(self, symbol: str = 'BTC/USD', limit: int = 3) -> List[Dict]:
        """Obtener las mejores oportunidades de arbitraje"""
        result = self.check_arbitrage_opportunities(symbol)
        if result.get('success'):
            return result['opportunities'][:limit]
        return []
    
    def format_opportunity(self, opp: Dict) -> str:
        """Formatear oportunidad para Telegram"""
        return f"""
🎯 **Arbitrage Opportunity**

💰 **Profit**: {opp['net_profit_pct']:.2f}% net
   └ Spread: {opp['spread_pct']:.2f}%
   └ Fees: -{opp['fees_pct']:.2f}%

📊 **Strategy**:
   🛒 BUY at {opp['buy_exchange']}: ${opp['buy_price']:,.2f}
   💸 SELL at {opp['sell_exchange']}: ${opp['sell_price']:,.2f}

💵 **Potential Profit**:
   • $1,000 → ${opp['profit_per_1k_usd']:.2f}
   • $10,000 → ${opp['profit_per_10k_usd']:.2f}

⏰ Detected: {opp['timestamp']}
"""
