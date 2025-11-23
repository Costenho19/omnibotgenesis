import logging

logger = logging.getLogger(__name__)

# Check if trading is available
try:
    import ccxt
    TRADING_AVAILABLE = True
except ImportError:
    TRADING_AVAILABLE = False


class MultiExchangeArbitrage:
    """Arbitraje multi-exchange REAL (usando APIs gratuitas)"""
    
    def __init__(self):
        self.exchanges = ['kraken', 'coinbase', 'binance']
        
    def check_arbitrage_opportunities(self, symbol='BTC/USD'):
        """Buscar oportunidades de arbitraje reales"""
        try:
            if not TRADING_AVAILABLE:
                return {'opportunities': []}
                
            import ccxt
            prices = {}
            
            try:
                kraken = ccxt.kraken()
                ticker = kraken.fetch_ticker(symbol)
                prices['kraken'] = {
                    'price': ticker['last'],
                    'exchange': 'kraken',
                    'volume': ticker['quoteVolume']
                }
            except:
                pass
            
            try:
                coinbase_pro = ccxt.coinbasepro()
                cb_ticker = coinbase_pro.fetch_ticker(symbol)
                prices['coinbase'] = {
                    'price': cb_ticker['last'],
                    'exchange': 'coinbase',
                    'volume': cb_ticker['quoteVolume']
                }
            except Exception as e:
                logger.warning(f"No se pudo obtener precio real de Coinbase: {e}")
                
            try:
                binance = ccxt.binance()
                binance_ticker = binance.fetch_ticker(symbol.replace('/', ''))
                prices['binance'] = {
                    'price': binance_ticker['last'],
                    'exchange': 'binance', 
                    'volume': binance_ticker['quoteVolume']
                }
            except Exception as e:
                logger.warning(f"No se pudo obtener precio real de Binance: {e}")
            
            opportunities = []
            exchanges = list(prices.keys())
            
            for i, ex1 in enumerate(exchanges):
                for ex2 in exchanges[i+1:]:
                    price1 = prices[ex1]['price']
                    price2 = prices[ex2]['price']
                    
                    if price1 > price2:
                        profit_pct = ((price1 - price2) / price2) * 100
                        if profit_pct > 0.1:
                            opportunities.append({
                                'buy_exchange': ex2,
                                'sell_exchange': ex1,
                                'buy_price': price2,
                                'sell_price': price1,
                                'profit_percentage': profit_pct,
                                'estimated_profit_usd': profit_pct * 1000 / 100
                            })
                    elif price2 > price1:
                        profit_pct = ((price2 - price1) / price1) * 100
                        if profit_pct > 0.1:
                            opportunities.append({
                                'buy_exchange': ex1,
                                'sell_exchange': ex2,
                                'buy_price': price1,
                                'sell_price': price2,
                                'profit_percentage': profit_pct,
                                'estimated_profit_usd': profit_pct * 1000 / 100
                            })
            
            return {
                'symbol': symbol,
                'opportunities': opportunities,
                'total_opportunities': len(opportunities),
                'max_profit': max([o['profit_percentage'] for o in opportunities], default=0)
            }
        except Exception as e:
            return {'opportunities': [], 'error': str(e)}
