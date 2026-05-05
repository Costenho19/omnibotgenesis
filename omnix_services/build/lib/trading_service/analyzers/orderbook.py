"""
OMNIX Advanced Order Book Analyzer
Detectar manipulación de mercado y actividad de whales
"""


class AdvancedOrderBookAnalyzer:
    """Análisis avanzado de Order Book para detectar manipulación y whales"""
    
    def __init__(self):
        self.whale_threshold = 10000  # $10K+ orders
        
    def detect_whale_activity(self, order_book):
        """Detectar actividad de whales"""
        try:
            large_bids = [order for order in order_book.get('bids', []) if float(order[1]) * float(order[0]) > self.whale_threshold]
            large_asks = [order for order in order_book.get('asks', []) if float(order[1]) * float(order[0]) > self.whale_threshold]
            
            return {
                'whale_bids': len(large_bids),
                'whale_asks': len(large_asks),
                'total_whale_volume': sum([float(o[1]) for o in large_bids + large_asks]),
                'whale_activity_detected': len(large_bids + large_asks) > 0
            }
        except Exception:
            return {'whale_activity_detected': False, 'whale_bids': 0, 'whale_asks': 0}
    
    def calculate_market_depth_score(self, order_book):
        """Calcular score de profundidad de mercado"""
        try:
            bids = order_book.get('bids', [])[:10]  # Top 10 bids
            asks = order_book.get('asks', [])[:10]  # Top 10 asks
            
            bid_volume = sum([float(bid[1]) for bid in bids])
            ask_volume = sum([float(ask[1]) for ask in asks])
            total_volume = bid_volume + ask_volume
            
            if total_volume > 50:
                return min(100, total_volume / 2)  # Score 0-100
            return max(10, total_volume * 2)
        except Exception:
            return 50  # Score neutral
