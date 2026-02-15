"""
OMNIX Microstructure Analyzer
Análisis de la microestructura del mercado (spreads, liquidez, eficiencia)
"""


class MicrostructureAnalyzer:
    """Análisis de microestructura de mercado"""
    
    def analyze_market_microstructure(self, market_data):
        """Analizar microestructura del mercado"""
        try:
            bid = market_data.get('bid', 0)
            ask = market_data.get('ask', 0)
            last = market_data.get('last', 0)
            volume = market_data.get('volume', 0)
            
            if bid > 0 and ask > 0:
                spread = ask - bid
                spread_pct = (spread / last) * 100 if last > 0 else 0
                
                # Score de liquidez basado en spread
                if spread_pct < 0.1:
                    liquidity_score = 90
                elif spread_pct < 0.5:
                    liquidity_score = 70
                elif spread_pct < 1.0:
                    liquidity_score = 50
                else:
                    liquidity_score = 30
                
                return {
                    'spread': spread,
                    'spread_percentage': spread_pct,
                    'liquidity_score': liquidity_score,
                    'market_efficiency': 'HIGH' if spread_pct < 0.2 else 'MEDIUM' if spread_pct < 0.8 else 'LOW'
                }
            else:
                return {'spread': 0, 'spread_percentage': 0, 'liquidity_score': 50, 'market_efficiency': 'MEDIUM'}
        except Exception:
            return {'spread': 0, 'spread_percentage': 0, 'liquidity_score': 50, 'market_efficiency': 'MEDIUM'}


class AdvancedRiskManagement:
    """Gestión avanzada de riesgos"""
    
    def calculate_portfolio_var(self, position_value, volatility, confidence=0.95):
        """Calcular Value at Risk del portfolio"""
        try:
            # VaR paramétrico simple
            if confidence == 0.95:
                z_score = 1.645
            elif confidence == 0.99:
                z_score = 2.326
            else:
                z_score = 1.96
                
            var_1d = position_value * volatility * z_score
            var_7d = var_1d * (7 ** 0.5)
            var_30d = var_1d * (30 ** 0.5)
            
            return {
                'var_1d': var_1d,
                'var_7d': var_7d,
                'var_30d': var_30d,
                'confidence_level': confidence
            }
        except Exception:
            return {'var_1d': 0, 'var_7d': 0, 'var_30d': 0, 'confidence_level': 0.95}
    
    def run_stress_test(self, position_btc, current_price):
        """Ejecutar stress test de la posición"""
        try:
            scenarios = {
                'flash_crash_50': -0.5,
                'major_correction_30': -0.3,
                'moderate_correction_15': -0.15,
                'recovery_20': 0.20,
                'bull_run_50': 0.50
            }
            
            results = {}
            current_value = position_btc * current_price
            
            for scenario_name, price_change_pct in scenarios.items():
                new_price = current_price * (1 + price_change_pct)
                new_value = position_btc * new_price
                pnl = new_value - current_value
                
                results[scenario_name] = {
                    'price_change_pct': price_change_pct * 100,
                    'new_price': new_price,
                    'new_value': new_value,
                    'pnl': pnl,
                    'pnl_pct': (pnl / current_value * 100) if current_value > 0 else 0
                }
            
            return {
                'current_value': current_value,
                'scenarios': results,
                'worst_case': min(results.values(), key=lambda x: x['pnl']),
                'best_case': max(results.values(), key=lambda x: x['pnl'])
            }
        except Exception:
            return {'current_value': 0, 'scenarios': {}, 'worst_case': {}, 'best_case': {}}
