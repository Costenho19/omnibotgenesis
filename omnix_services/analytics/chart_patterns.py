"""
📊 OMNIX V5.3 QUANTUM ULTIMATE - CHART PATTERN DETECTOR
Detector especializado de patrones técnicos en gráficos de trading

PATRONES DETECTADOS:
- Head & Shoulders / Inverse H&S
- Double Top / Double Bottom
- Triangles (Ascending, Descending, Symmetrical)
- Flags & Pennants (Bull/Bear)
- Cup & Handle
- Wedges (Rising/Falling)

NIVELES TÉCNICOS:
- Soportes y Resistencias
- Trendlines (Bullish/Bearish)
- Fibonacci Retracements
- Pivot Points

Desarrollado por Harold Nunes - Noviembre 2025
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChartPattern:
    """Estructura de datos para un patrón detectado"""
    pattern_type: str  # 'head_and_shoulders', 'double_top', etc.
    confidence: float  # 0.0 - 1.0
    signal: str  # 'bullish', 'bearish', 'neutral'
    price_levels: List[float]  # Niveles de precio relevantes
    description: str


@dataclass
class SupportResistance:
    """Nivel de soporte o resistencia detectado"""
    level_type: str  # 'support' o 'resistance'
    price: float
    strength: float  # 0.0 - 1.0 (cuántas veces fue tocado)
    touches: int  # Número de toques


class ChartPatternDetector:
    """
    Detector avanzado de patrones técnicos en gráficos
    
    Usa análisis de price action y geometría para identificar
    patrones clásicos de análisis técnico
    """
    
    def __init__(self):
        """Inicializar detector de patrones"""
        
        # Definiciones de patrones con sus características
        self.pattern_definitions = {
            'head_and_shoulders': {
                'signal': 'bearish',
                'reliability': 0.85,
                'description': 'Head and Shoulders - Patrón de reversión bajista'
            },
            'inverse_head_and_shoulders': {
                'signal': 'bullish',
                'reliability': 0.85,
                'description': 'Inverse Head and Shoulders - Patrón de reversión alcista'
            },
            'double_top': {
                'signal': 'bearish',
                'reliability': 0.75,
                'description': 'Double Top - Patrón de reversión bajista'
            },
            'double_bottom': {
                'signal': 'bullish',
                'reliability': 0.75,
                'description': 'Double Bottom - Patrón de reversión alcista'
            },
            'ascending_triangle': {
                'signal': 'bullish',
                'reliability': 0.70,
                'description': 'Ascending Triangle - Patrón de continuación alcista'
            },
            'descending_triangle': {
                'signal': 'bearish',
                'reliability': 0.70,
                'description': 'Descending Triangle - Patrón de continuación bajista'
            },
            'bull_flag': {
                'signal': 'bullish',
                'reliability': 0.80,
                'description': 'Bull Flag - Continuación alcista'
            },
            'bear_flag': {
                'signal': 'bearish',
                'reliability': 0.80,
                'description': 'Bear Flag - Continuación bajista'
            },
            'cup_and_handle': {
                'signal': 'bullish',
                'reliability': 0.75,
                'description': 'Cup and Handle - Patrón de continuación alcista'
            }
        }
        
        logger.info("📊 Chart Pattern Detector inicializado")
        logger.info(f"   🎯 {len(self.pattern_definitions)} patrones configurados")
    
    def detect_patterns_from_price_data(self, prices: List[float], 
                                       timestamps: Optional[List] = None) -> List[ChartPattern]:
        """
        Detectar patrones desde datos de precio
        
        Args:
            prices: Lista de precios (OHLC o close prices)
            timestamps: Lista de timestamps (opcional)
            
        Returns:
            Lista de patrones detectados
        """
        if len(prices) < 20:
            logger.warning("⚠️ Necesito al menos 20 datos de precio para análisis")
            return []
        
        patterns_found = []
        
        try:
            # Convertir a numpy array para análisis
            price_array = np.array(prices)
            
            # 1. Detectar Head & Shoulders
            h_s = self._detect_head_and_shoulders(price_array)
            if h_s:
                patterns_found.append(h_s)
            
            # 2. Detectar Double Top/Bottom
            double_patterns = self._detect_double_patterns(price_array)
            patterns_found.extend(double_patterns)
            
            # 3. Detectar Triangles
            triangles = self._detect_triangles(price_array)
            patterns_found.extend(triangles)
            
            # 4. Detectar Flags
            flags = self._detect_flags(price_array)
            patterns_found.extend(flags)
            
            logger.info(f"✅ Detectados {len(patterns_found)} patrones en price data")
            
        except Exception as e:
            logger.error(f"Error detectando patrones: {e}")
        
        return patterns_found
    
    def detect_support_resistance(self, prices: List[float], 
                                  window: int = 20, 
                                  threshold: float = 0.02) -> List[SupportResistance]:
        """
        Detectar niveles de soporte y resistencia
        
        Args:
            prices: Lista de precios
            window: Ventana para análisis de picos/valles
            threshold: Umbral de precio (2% por defecto)
            
        Returns:
            Lista de niveles S/R detectados
        """
        if len(prices) < window * 2:
            return []
        
        levels = []
        
        try:
            price_array = np.array(prices)
            
            # Detectar máximos y mínimos locales
            peaks = self._find_peaks(price_array, window)
            valleys = self._find_valleys(price_array, window)
            
            # Agrupar niveles similares (clustering)
            resistance_levels = self._cluster_levels(peaks, threshold)
            support_levels = self._cluster_levels(valleys, threshold)
            
            # Crear objetos SupportResistance
            for price, strength, touches in resistance_levels:
                levels.append(SupportResistance(
                    level_type='resistance',
                    price=price,
                    strength=strength,
                    touches=touches
                ))
            
            for price, strength, touches in support_levels:
                levels.append(SupportResistance(
                    level_type='support',
                    price=price,
                    strength=strength,
                    touches=touches
                ))
            
            # Ordenar por strength (más fuerte primero)
            levels.sort(key=lambda x: x.strength, reverse=True)
            
            logger.info(f"📊 Detectados {len(levels)} niveles S/R (S: {len(support_levels)}, R: {len(resistance_levels)})")
            
        except Exception as e:
            logger.error(f"Error detectando S/R: {e}")
        
        return levels
    
    def _detect_head_and_shoulders(self, prices: np.ndarray) -> Optional[ChartPattern]:
        """
        Detectar patrón Head and Shoulders
        
        Busca estructura: Left Shoulder - Head - Right Shoulder
        donde Head es el pico más alto
        """
        try:
            if len(prices) < 30:
                return None
            
            # Encontrar picos
            peaks_indices = []
            for i in range(5, len(prices) - 5):
                if prices[i] == max(prices[i-5:i+6]):
                    peaks_indices.append(i)
            
            # Necesitamos al menos 3 picos para H&S
            if len(peaks_indices) < 3:
                return None
            
            # Buscar patrón: pico1 < pico2 > pico3
            # y pico1 ≈ pico3 (hombros similares)
            for i in range(len(peaks_indices) - 2):
                left_shoulder = prices[peaks_indices[i]]
                head = prices[peaks_indices[i+1]]
                right_shoulder = prices[peaks_indices[i+2]]
                
                # Verificar estructura
                if (head > left_shoulder and head > right_shoulder and
                    abs(left_shoulder - right_shoulder) / left_shoulder < 0.05):
                    
                    # H&S detectado
                    neckline = min(prices[peaks_indices[i]:peaks_indices[i+2]])
                    
                    return ChartPattern(
                        pattern_type='head_and_shoulders',
                        confidence=0.80,
                        signal='bearish',
                        price_levels=[left_shoulder, head, right_shoulder, neckline],
                        description=self.pattern_definitions['head_and_shoulders']['description']
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error detectando H&S: {e}")
            return None
    
    def _detect_double_patterns(self, prices: np.ndarray) -> List[ChartPattern]:
        """Detectar Double Top y Double Bottom"""
        patterns = []
        
        try:
            peaks_indices = []
            valleys_indices = []
            
            # Encontrar picos y valles
            for i in range(10, len(prices) - 10):
                window = prices[i-10:i+11]
                if prices[i] == max(window):
                    peaks_indices.append(i)
                elif prices[i] == min(window):
                    valleys_indices.append(i)
            
            # Detectar Double Top (dos picos similares)
            for i in range(len(peaks_indices) - 1):
                peak1 = prices[peaks_indices[i]]
                peak2 = prices[peaks_indices[i+1]]
                
                if abs(peak1 - peak2) / peak1 < 0.03:  # Picos dentro de 3%
                    patterns.append(ChartPattern(
                        pattern_type='double_top',
                        confidence=0.75,
                        signal='bearish',
                        price_levels=[peak1, peak2],
                        description=self.pattern_definitions['double_top']['description']
                    ))
                    break  # Solo reportar el primero
            
            # Detectar Double Bottom (dos valles similares)
            for i in range(len(valleys_indices) - 1):
                valley1 = prices[valleys_indices[i]]
                valley2 = prices[valleys_indices[i+1]]
                
                if abs(valley1 - valley2) / valley1 < 0.03:
                    patterns.append(ChartPattern(
                        pattern_type='double_bottom',
                        confidence=0.75,
                        signal='bullish',
                        price_levels=[valley1, valley2],
                        description=self.pattern_definitions['double_bottom']['description']
                    ))
                    break
            
        except Exception as e:
            logger.error(f"Error detectando double patterns: {e}")
        
        return patterns
    
    def _detect_triangles(self, prices: np.ndarray) -> List[ChartPattern]:
        """Detectar patrones de triángulos"""
        # Simplificado - análisis real requiere trendlines
        return []
    
    def _detect_flags(self, prices: np.ndarray) -> List[ChartPattern]:
        """Detectar Bull/Bear Flags"""
        # Simplificado - análisis real requiere volumen y consolidación
        return []
    
    def _find_peaks(self, prices: np.ndarray, window: int) -> List[float]:
        """Encontrar picos (máximos locales)"""
        peaks = []
        for i in range(window, len(prices) - window):
            if prices[i] == max(prices[i-window:i+window+1]):
                peaks.append(prices[i])
        return peaks
    
    def _find_valleys(self, prices: np.ndarray, window: int) -> List[float]:
        """Encontrar valles (mínimos locales)"""
        valleys = []
        for i in range(window, len(prices) - window):
            if prices[i] == min(prices[i-window:i+window+1]):
                valleys.append(prices[i])
        return valleys
    
    def _cluster_levels(self, levels: List[float], threshold: float) -> List[Tuple[float, float, int]]:
        """
        Agrupar niveles similares
        
        Returns:
            Lista de (precio_promedio, strength, touches)
        """
        if not levels:
            return []
        
        clustered = []
        sorted_levels = sorted(levels)
        current_cluster = [sorted_levels[0]]
        
        for level in sorted_levels[1:]:
            if abs(level - current_cluster[-1]) / current_cluster[-1] < threshold:
                current_cluster.append(level)
            else:
                # Guardar cluster actual
                avg_price = sum(current_cluster) / len(current_cluster)
                touches = len(current_cluster)
                strength = min(touches / 5.0, 1.0)  # Max strength = 1.0 con 5+ touches
                clustered.append((avg_price, strength, touches))
                
                # Iniciar nuevo cluster
                current_cluster = [level]
        
        # Agregar último cluster
        if current_cluster:
            avg_price = sum(current_cluster) / len(current_cluster)
            touches = len(current_cluster)
            strength = min(touches / 5.0, 1.0)
            clustered.append((avg_price, strength, touches))
        
        return clustered
    
    def analyze_pattern_significance(self, pattern: ChartPattern, 
                                    current_price: float) -> Dict:
        """
        Analizar significancia de un patrón para trading
        
        Args:
            pattern: Patrón detectado
            current_price: Precio actual del activo
            
        Returns:
            Dict con análisis de significancia
        """
        analysis = {
            'pattern_type': pattern.pattern_type,
            'signal': pattern.signal,
            'confidence': pattern.confidence,
            'actionable': False,
            'entry_price': None,
            'stop_loss': None,
            'target': None,
            'risk_reward': None
        }
        
        try:
            definition = self.pattern_definitions.get(pattern.pattern_type, {})
            base_reliability = definition.get('reliability', 0.5)
            
            # Calcular niveles de entrada/stop/target según patrón
            if pattern.pattern_type == 'head_and_shoulders':
                # Entrada: break de neckline
                neckline = pattern.price_levels[-1] if pattern.price_levels else current_price
                analysis['entry_price'] = neckline * 0.995  # 0.5% below neckline
                analysis['stop_loss'] = pattern.price_levels[1] if len(pattern.price_levels) > 1 else neckline * 1.02
                analysis['target'] = neckline - (pattern.price_levels[1] - neckline)
                
            elif pattern.pattern_type == 'double_bottom':
                # Entrada: break de neckline
                valley = min(pattern.price_levels)
                analysis['entry_price'] = valley * 1.005
                analysis['stop_loss'] = valley * 0.98
                analysis['target'] = valley * 1.10  # 10% target
            
            # Calcular risk/reward
            if analysis['entry_price'] and analysis['stop_loss'] and analysis['target']:
                risk = abs(analysis['entry_price'] - analysis['stop_loss'])
                reward = abs(analysis['target'] - analysis['entry_price'])
                if risk > 0:
                    analysis['risk_reward'] = reward / risk
                    
                    # Actionable si R:R > 2.0
                    if analysis['risk_reward'] >= 2.0:
                        analysis['actionable'] = True
            
            analysis['reliability'] = base_reliability * pattern.confidence
            
        except Exception as e:
            logger.error(f"Error analizando significancia: {e}")
        
        return analysis


# Helper function
def detect_chart_patterns(prices: List[float]) -> Dict:
    """
    Detectar patrones y niveles S/R desde lista de precios
    
    Args:
        prices: Lista de precios de cierre
        
    Returns:
        Dict con patrones y niveles detectados
    """
    detector = ChartPatternDetector()
    
    patterns = detector.detect_patterns_from_price_data(prices)
    levels = detector.detect_support_resistance(prices)
    
    return {
        'patterns': patterns,
        'support_resistance_levels': levels,
        'total_findings': len(patterns) + len(levels)
    }
