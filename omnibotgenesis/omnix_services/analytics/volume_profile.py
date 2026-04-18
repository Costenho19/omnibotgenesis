import time
import logging

logger = logging.getLogger(__name__)


class VolumeProfileAnalyzer:
    """
    🔥 MEJORA REAL #2: Análisis Volume Profile para detectar zonas de alto volumen
    GRATUITO - Usa datos históricos para identificar niveles institucionales
    Harold solicitó mejoras REALES - Esta detecta dónde operan las ballenas
    """
    
    def __init__(self):
        self.price_levels = {}
        self.volume_distribution = {}
        self.high_volume_nodes = []
        self.value_area_percentage = 0.70
        
    def calculate_volume_profile(self, price_volume_data, num_levels=20):
        """
        Calcular Volume Profile desde datos históricos
        ENTRADA: Lista de (precio, volumen) de las últimas N velas
        SALIDA: Distribución de volumen por niveles de precio
        """
        try:
            if not price_volume_data:
                return None
            
            prices = [item['price'] for item in price_volume_data]
            volumes = [item['volume'] for item in price_volume_data]
            
            min_price = min(prices)
            max_price = max(prices)
            total_volume = sum(volumes)
            
            price_step = (max_price - min_price) / num_levels
            volume_by_level = {}
            
            for i in range(num_levels):
                level_min = min_price + (i * price_step)
                level_max = level_min + price_step
                level_center = level_min + (price_step / 2)
                
                level_volume = 0
                for data_point in price_volume_data:
                    price = data_point['price']
                    volume = data_point['volume']
                    
                    if level_min <= price < level_max:
                        level_volume += volume
                
                if level_volume > 0:
                    volume_by_level[level_center] = {
                        'volume': level_volume,
                        'percentage': (level_volume / total_volume) * 100,
                        'price_range': (level_min, level_max),
                        'transactions_count': len([d for d in price_volume_data if level_min <= d['price'] < level_max])
                    }
            
            poc_price = max(volume_by_level.keys(), key=lambda p: volume_by_level[p]['volume'])
            poc_volume = volume_by_level[poc_price]['volume']
            
            sorted_levels = sorted(volume_by_level.items(), key=lambda x: x[1]['volume'], reverse=True)
            value_area_volume = 0
            value_area_levels = []
            
            for price, data in sorted_levels:
                value_area_volume += data['volume']
                value_area_levels.append(price)
                if value_area_volume >= total_volume * self.value_area_percentage:
                    break
            
            value_area_high = max(value_area_levels) if value_area_levels else max_price
            value_area_low = min(value_area_levels) if value_area_levels else min_price
            
            avg_volume = total_volume / num_levels
            high_volume_nodes = []
            low_volume_nodes = []
            
            for price, data in volume_by_level.items():
                if data['volume'] > avg_volume * 1.5:
                    high_volume_nodes.append({
                        'price': price,
                        'volume': data['volume'],
                        'strength': 'HIGH' if data['volume'] > avg_volume * 2 else 'MEDIUM'
                    })
                elif data['volume'] < avg_volume * 0.5:
                    low_volume_nodes.append({
                        'price': price,
                        'volume': data['volume'],
                        'strength': 'GAP'
                    })
            
            return {
                'total_volume': total_volume,
                'price_range': (min_price, max_price),
                'point_of_control': {
                    'price': poc_price,
                    'volume': poc_volume,
                    'percentage': (poc_volume / total_volume) * 100
                },
                'value_area': {
                    'high': value_area_high,
                    'low': value_area_low,
                    'range': value_area_high - value_area_low,
                    'volume_percentage': self.value_area_percentage * 100
                },
                'volume_by_level': volume_by_level,
                'high_volume_nodes': high_volume_nodes,
                'low_volume_nodes': low_volume_nodes,
                'analysis_timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error calculando Volume Profile: {e}")
            return None
    
    def detect_volume_signals(self, current_price, volume_profile):
        """
        Detectar señales de trading basadas en Volume Profile
        SEÑALES: POC bounce, Value Area break, HVN rejection
        """
        try:
            signals = []
            
            if not volume_profile:
                return signals
            
            poc_price = volume_profile['point_of_control']['price']
            value_area_high = volume_profile['value_area']['high']
            value_area_low = volume_profile['value_area']['low']
            high_volume_nodes = volume_profile['high_volume_nodes']
            low_volume_nodes = volume_profile['low_volume_nodes']
            
            tolerance = 0.003
            
            if abs(current_price - poc_price) / poc_price <= tolerance:
                signals.append({
                    'type': 'POC_BOUNCE',
                    'action': 'STRONG_SIGNAL',
                    'level': poc_price,
                    'strength': 'VERY_HIGH',
                    'description': f"🎯 POC Bounce - Mayor volumen en ${poc_price:.2f}",
                    'volume_confidence': volume_profile['point_of_control']['percentage']
                })
            
            if value_area_low <= current_price <= value_area_high:
                signals.append({
                    'type': 'VALUE_AREA_TRADE',
                    'action': 'NEUTRAL',
                    'level': current_price,
                    'strength': 'MEDIUM',
                    'description': f"⚖️ Precio en Value Area (${value_area_low:.2f} - ${value_area_high:.2f})",
                    'area_info': 'Zona de trading normal - 70% del volumen'
                })
            
            if current_price > value_area_high:
                signals.append({
                    'type': 'VALUE_AREA_BREAKOUT',
                    'action': 'BUY',
                    'level': value_area_high,
                    'strength': 'HIGH',
                    'description': f"🚀 Ruptura Value Area - Arriba de ${value_area_high:.2f}",
                    'target': 'Próximo HVN o extensión'
                })
            elif current_price < value_area_low:
                signals.append({
                    'type': 'VALUE_AREA_BREAKDOWN',
                    'action': 'SELL',
                    'level': value_area_low,
                    'strength': 'HIGH',
                    'description': f"📉 Caída Value Area - Abajo de ${value_area_low:.2f}",
                    'target': 'Próximo soporte HVN'
                })
            
            for hvn in high_volume_nodes:
                hvn_price = hvn['price']
                if abs(current_price - hvn_price) / hvn_price <= tolerance:
                    action = 'BUY' if current_price > poc_price else 'SELL'
                    signals.append({
                        'type': 'HVN_REACTION',
                        'action': action,
                        'level': hvn_price,
                        'strength': hvn['strength'],
                        'description': f"🔥 Reacción HVN - Volumen alto en ${hvn_price:.2f}",
                        'volume_strength': hvn['volume']
                    })
            
            for lvn in low_volume_nodes:
                lvn_price = lvn['price']
                if abs(current_price - lvn_price) / lvn_price <= tolerance:
                    signals.append({
                        'type': 'LVN_ACCELERATION',
                        'action': 'MOMENTUM',
                        'level': lvn_price,
                        'strength': 'MEDIUM',
                        'description': f"⚡ Gap de Volumen - Movimiento rápido esperado en ${lvn_price:.2f}",
                        'expectation': 'Aceleración hacia próximo HVN'
                    })
            
            return signals
            
        except Exception as e:
            logger.error(f"Error detectando señales Volume Profile: {e}")
            return []
    
    def get_institutional_levels(self, volume_profile):
        """
        Identificar niveles donde operan las instituciones/ballenas
        CRITERIOS: Alto volumen + múltiples transacciones + persistencia
        """
        try:
            if not volume_profile:
                return None
            
            institutional_levels = []
            volume_by_level = volume_profile['volume_by_level']
            total_volume = volume_profile['total_volume']
            poc_price = volume_profile['point_of_control']['price']
            
            volume_threshold = total_volume * 0.05
            transaction_threshold = 10
            
            for price, data in volume_by_level.items():
                volume = data['volume']
                transactions = data['transactions_count']
                volume_percentage = data['percentage']
                
                institutional_score = 0
                
                if volume > volume_threshold:
                    institutional_score += 30
                
                if transactions > transaction_threshold:
                    institutional_score += 25
                
                if volume_percentage > 3.0:
                    institutional_score += 20
                
                distance_from_poc = abs(price - poc_price) / poc_price
                if distance_from_poc < 0.02:
                    institutional_score += 15
                
                if price % 100 == 0 or price % 500 == 0 or price % 1000 == 0:
                    institutional_score += 10
                
                if institutional_score >= 60:
                    institutional_levels.append({
                        'price': price,
                        'volume': volume,
                        'transactions': transactions,
                        'volume_percentage': volume_percentage,
                        'institutional_score': institutional_score,
                        'classification': 'MAJOR_INSTITUTIONAL' if institutional_score >= 80 else 'INSTITUTIONAL',
                        'activity_type': 'ACCUMULATION' if price < poc_price else 'DISTRIBUTION'
                    })
            
            institutional_levels.sort(key=lambda x: x['institutional_score'], reverse=True)
            
            return {
                'levels_found': len(institutional_levels),
                'institutional_levels': institutional_levels[:10],
                'total_institutional_volume': sum([level['volume'] for level in institutional_levels]),
                'institutional_dominance': (sum([level['volume'] for level in institutional_levels]) / total_volume) * 100,
                'analysis_confidence': min(90, len(institutional_levels) * 10)
            }
            
        except Exception as e:
            logger.error(f"Error identificando niveles institucionales: {e}")
            return None
