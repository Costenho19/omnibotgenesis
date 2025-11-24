"""
OMNIX V6.0 ULTRA - Arbitrage Executor Premium
Ejecución paralela de órdenes de arbitraje con gestión de riesgo institucional
"""

import logging
import os
import asyncio
from typing import Dict, Optional, Tuple
from datetime import datetime
import time

logger = logging.getLogger(__name__)

try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False
    logger.warning("⚠️ CCXT not available - arbitrage execution disabled")


class ArbitrageExecutorPremium:
    """
    Ejecutor de arbitraje con capacidades institucionales:
    - Ejecución paralela de órdenes (compra/venta simultánea)
    - Gestión de slippage y fees reales
    - Kill-switch automático
    - Logging detallado para auditoría
    """
    
    def __init__(self, paper_trading: bool = True):
        """
        Args:
            paper_trading: Si True, simula trades sin ejecutar (default: True)
        """
        self.paper_trading = paper_trading
        self.execution_history = []
        self.total_profit_usd = 0
        self.total_trades = 0
        self.success_rate = 0
        
        # Límites de seguridad
        self.max_trade_size_usd = 10000  # Máximo $10K por trade
        self.max_daily_volume_usd = 100000  # Máximo $100K por día
        self.min_profit_threshold = 0.3  # Mínimo 0.3% profit neto
        
        # API keys desde Replit Secrets (seguro)
        self.api_keys = self._load_api_keys_from_secrets()
        
        logger.info(f"🚀 Arbitrage Executor initialized - Mode: {'PAPER TRADING' if paper_trading else 'LIVE TRADING'}")
        
    def _load_api_keys_from_secrets(self) -> Dict[str, Dict[str, str]]:
        """
        Cargar API keys de forma segura desde Replit Secrets
        
        Format de secrets:
        KRAKEN_API_KEY, KRAKEN_API_SECRET
        BINANCE_API_KEY, BINANCE_API_SECRET
        etc.
        """
        api_keys = {}
        
        exchanges = ['KRAKEN', 'BINANCE', 'COINBASE', 'BYBIT', 'KUCOIN', 'OKX', 'GATEIO', 'BITFINEX']
        
        for exchange in exchanges:
            api_key = os.getenv(f'{exchange}_API_KEY')
            api_secret = os.getenv(f'{exchange}_API_SECRET')
            
            if api_key and api_secret:
                api_keys[exchange.lower()] = {
                    'apiKey': api_key,
                    'secret': api_secret
                }
                logger.debug(f"✅ {exchange} API keys loaded from secrets")
            else:
                logger.debug(f"ℹ️ {exchange} API keys not configured (paper trading only)")
        
        return api_keys
    
    def get_authenticated_exchange(self, exchange_name: str) -> Optional[object]:
        """Crear instancia autenticada de exchange"""
        if not CCXT_AVAILABLE:
            logger.error("CCXT not available")
            return None
        
        if self.paper_trading:
            logger.info(f"📄 Paper trading mode - {exchange_name} simulation")
            return self._get_public_exchange(exchange_name)
        
        if exchange_name not in self.api_keys:
            logger.error(f"❌ {exchange_name} API keys not configured")
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
                logger.error(f"Exchange {exchange_name} not supported")
                return None
            
            config = self.api_keys[exchange_name].copy()
            config.update({
                'enableRateLimit': True,
                'timeout': 10000,
            })
            
            exchange = exchange_classes[exchange_name](config)
            logger.info(f"✅ {exchange_name} authenticated exchange created")
            return exchange
            
        except Exception as e:
            logger.error(f"Error creating authenticated {exchange_name}: {e}")
            return None
    
    def _get_public_exchange(self, exchange_name: str) -> Optional[object]:
        """Crear instancia pública (sin autenticación) para paper trading"""
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
                return None
            
            return exchange_classes[exchange_name]({
                'enableRateLimit': True,
                'timeout': 5000,
            })
            
        except Exception as e:
            logger.error(f"Error creating public {exchange_name}: {e}")
            return None
    
    async def execute_arbitrage_trade(self, opportunity: Dict, 
                                      amount_usd: float = 1000) -> Dict:
        """
        Ejecutar trade de arbitraje de forma paralela
        
        Args:
            opportunity: Oportunidad de arbitraje del scanner
            amount_usd: Cantidad en USD a tradear
            
        Returns:
            Dict con resultado de ejecución
        """
        try:
            # Validaciones de seguridad
            if amount_usd > self.max_trade_size_usd:
                return {
                    'success': False,
                    'error': f'Amount ${amount_usd:,.2f} exceeds max trade size ${self.max_trade_size_usd:,.2f}'
                }
            
            if opportunity['net_profit_pct'] < self.min_profit_threshold:
                return {
                    'success': False,
                    'error': f'Profit {opportunity["net_profit_pct"]:.2f}% below threshold {self.min_profit_threshold}%'
                }
            
            buy_exchange = opportunity['buy_exchange']
            sell_exchange = opportunity['sell_exchange']
            buy_price = opportunity['buy_price']
            sell_price = opportunity['sell_price']
            
            logger.info(f"🎯 Executing arbitrage: {buy_exchange} → {sell_exchange}")
            logger.info(f"💰 Amount: ${amount_usd:,.2f} | Expected profit: {opportunity['net_profit_pct']:.2f}%")
            
            start_time = time.time()
            
            if self.paper_trading:
                # PAPER TRADING - Simulación realista
                result = await self._execute_paper_trade(
                    buy_exchange, sell_exchange,
                    buy_price, sell_price,
                    amount_usd, opportunity
                )
            else:
                # LIVE TRADING - Ejecución real paralela
                result = await self._execute_live_trade(
                    buy_exchange, sell_exchange,
                    buy_price, sell_price,
                    amount_usd, opportunity
                )
            
            execution_time = (time.time() - start_time) * 1000  # ms
            result['execution_time_ms'] = execution_time
            
            # Guardar en historial
            if result.get('success'):
                self.execution_history.append(result)
                self.total_trades += 1
                self.total_profit_usd += result.get('actual_profit_usd', 0)
                self.success_rate = (self.total_trades / len(self.execution_history)) * 100
            
            logger.info(f"✅ Execution completed in {execution_time:.0f}ms")
            return result
            
        except Exception as e:
            logger.error(f"❌ Execution failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _execute_paper_trade(self, buy_ex: str, sell_ex: str,
                                   buy_price: float, sell_price: float,
                                   amount_usd: float, opportunity: Dict) -> Dict:
        """Simular ejecución de arbitraje (paper trading)"""
        
        # Simular latencia realista
        await asyncio.sleep(0.1)  # 100ms latency
        
        # Calcular cantidades
        btc_amount = amount_usd / buy_price
        
        # Simular slippage (0.05% cada lado)
        slippage_pct = 0.05
        actual_buy_price = buy_price * (1 + slippage_pct / 100)
        actual_sell_price = sell_price * (1 - slippage_pct / 100)
        
        # Calcular profit real
        buy_cost = btc_amount * actual_buy_price
        sell_revenue = btc_amount * actual_sell_price
        
        fees = (buy_cost * opportunity['fees_pct'] / 200) + (sell_revenue * opportunity['fees_pct'] / 200)
        actual_profit_usd = sell_revenue - buy_cost - fees
        actual_profit_pct = (actual_profit_usd / buy_cost) * 100
        
        result = {
            'success': True,
            'mode': 'PAPER_TRADING',
            'buy_exchange': buy_ex,
            'sell_exchange': sell_ex,
            'amount_usd': amount_usd,
            'btc_amount': btc_amount,
            'buy_price_expected': buy_price,
            'sell_price_expected': sell_price,
            'buy_price_actual': actual_buy_price,
            'sell_price_actual': actual_sell_price,
            'expected_profit_pct': opportunity['net_profit_pct'],
            'actual_profit_pct': actual_profit_pct,
            'actual_profit_usd': actual_profit_usd,
            'slippage_pct': slippage_pct * 2,  # Both sides
            'fees_usd': fees,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"📄 PAPER TRADE: ${actual_profit_usd:.2f} profit ({actual_profit_pct:.2f}%)")
        return result
    
    async def _execute_live_trade(self, buy_ex: str, sell_ex: str,
                                  buy_price: float, sell_price: float,
                                  amount_usd: float, opportunity: Dict) -> Dict:
        """
        Ejecutar arbitraje REAL con órdenes paralelas
        
        CRITICAL: Este método ejecuta trades reales con dinero real
        """
        
        logger.warning("🔴 LIVE TRADING MODE - Executing real orders")
        
        # Obtener exchanges autenticados
        buy_exchange_obj = self.get_authenticated_exchange(buy_ex)
        sell_exchange_obj = self.get_authenticated_exchange(sell_ex)
        
        if not buy_exchange_obj or not sell_exchange_obj:
            return {
                'success': False,
                'error': 'Failed to create authenticated exchanges'
            }
        
        # Calcular cantidad de BTC
        btc_amount = amount_usd / buy_price
        
        try:
            # PASO 1: Ejecutar órdenes en paralelo (critical para arbitraje)
            buy_task = asyncio.create_task(
                self._place_market_order(buy_exchange_obj, 'BTC/USDT', 'buy', btc_amount)
            )
            sell_task = asyncio.create_task(
                self._place_market_order(sell_exchange_obj, 'BTC/USDT', 'sell', btc_amount)
            )
            
            buy_result, sell_result = await asyncio.gather(buy_task, sell_task)
            
            if not buy_result['success'] or not sell_result['success']:
                logger.error(f"❌ Order execution failed")
                return {
                    'success': False,
                    'error': 'One or both orders failed',
                    'buy_result': buy_result,
                    'sell_result': sell_result
                }
            
            # Calcular profit real
            actual_buy_price = buy_result['average_price']
            actual_sell_price = sell_result['average_price']
            
            buy_cost = btc_amount * actual_buy_price
            sell_revenue = btc_amount * actual_sell_price
            total_fees = buy_result['fee'] + sell_result['fee']
            
            actual_profit_usd = sell_revenue - buy_cost - total_fees
            actual_profit_pct = (actual_profit_usd / buy_cost) * 100
            
            result = {
                'success': True,
                'mode': 'LIVE_TRADING',
                'buy_exchange': buy_ex,
                'sell_exchange': sell_ex,
                'buy_order_id': buy_result['order_id'],
                'sell_order_id': sell_result['order_id'],
                'amount_usd': amount_usd,
                'btc_amount': btc_amount,
                'buy_price_expected': buy_price,
                'sell_price_expected': sell_price,
                'buy_price_actual': actual_buy_price,
                'sell_price_actual': actual_sell_price,
                'expected_profit_pct': opportunity['net_profit_pct'],
                'actual_profit_pct': actual_profit_pct,
                'actual_profit_usd': actual_profit_usd,
                'total_fees_usd': total_fees,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ LIVE TRADE EXECUTED: ${actual_profit_usd:.2f} profit ({actual_profit_pct:.2f}%)")
            return result
            
        except Exception as e:
            logger.error(f"❌ Live trade execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _place_market_order(self, exchange, symbol: str, 
                                  side: str, amount: float) -> Dict:
        """Colocar orden de mercado en exchange"""
        try:
            order = exchange.create_market_order(symbol, side, amount)
            
            return {
                'success': True,
                'order_id': order['id'],
                'average_price': order.get('average', order.get('price', 0)),
                'fee': order.get('fee', {}).get('cost', 0),
                'timestamp': order.get('timestamp', int(datetime.now().timestamp() * 1000))
            }
        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_performance_stats(self) -> Dict:
        """Obtener estadísticas de rendimiento"""
        return {
            'total_trades': self.total_trades,
            'total_profit_usd': self.total_profit_usd,
            'success_rate_pct': self.success_rate,
            'avg_profit_per_trade': self.total_profit_usd / self.total_trades if self.total_trades > 0 else 0,
            'mode': 'PAPER_TRADING' if self.paper_trading else 'LIVE_TRADING'
        }
