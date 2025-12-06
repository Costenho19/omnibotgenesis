"""
OMNIX V6.5.3 INSTITUTIONAL+ Position Manager
=============================================
Sistema profesional de gestión de posiciones con:
- ATR Calculator para volatilidad dinámica
- TP/SL dinámico basado en régimen de mercado
- Trailing Stop inteligente
- Break-even automático
- Integración completa con todos los motores OMNIX

Author: OMNIX Team
Version: 6.5.3 PREMIUM
"""

import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Régimen de mercado detectado por Non-Markovian Kernel"""
    TRENDING_BULL = "trending_bull"
    TRENDING_BEAR = "trending_bear"
    RANGING = "ranging"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    BREAKOUT = "breakout"


class PositionStatus(Enum):
    """Estados de una posición"""
    OPEN = "open"
    BREAK_EVEN = "break_even"
    TRAILING = "trailing"
    CLOSED_TP = "closed_tp"
    CLOSED_SL = "closed_sl"
    CLOSED_TRAILING = "closed_trailing"
    CLOSED_MANUAL = "closed_manual"


@dataclass
class PositionLevels:
    """Niveles de TP/SL para una posición"""
    entry_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    trailing_stop: Optional[float] = None
    break_even_active: bool = False
    atr_value: float = 0.0
    atr_multiplier_sl: float = 1.5
    atr_multiplier_tp: float = 2.5
    confidence_adjustment: float = 1.0
    regime: MarketRegime = MarketRegime.RANGING


@dataclass
class ATRData:
    """Datos de Average True Range"""
    symbol: str
    atr_14: float
    atr_7: float
    atr_percentage: float
    volatility_status: str
    timestamp: datetime = field(default_factory=datetime.now)


class ATRCalculator:
    """
    Calculador de Average True Range (ATR) profesional.
    
    El ATR mide la volatilidad real del mercado considerando:
    - High - Low del período
    - |High - Close anterior|
    - |Low - Close anterior|
    
    Se usa para calcular TP/SL dinámicos adaptados a la volatilidad actual.
    """
    
    def __init__(self, trading_service=None, redis_cache=None):
        self.trading_service = trading_service
        self.redis_cache = redis_cache
        self._atr_cache: Dict[str, ATRData] = {}
        self._cache_ttl = 300
        
    def calculate_atr(self, symbol: str, period: int = 14, 
                      ohlc_data: Optional[List[Dict]] = None) -> Optional[ATRData]:
        """
        Calcula el ATR para un símbolo.
        
        Args:
            symbol: Par de trading (ej: BTC/USD)
            period: Período para el cálculo (default 14)
            ohlc_data: Datos OHLC opcionales, si no se proveen se obtienen del servicio
            
        Returns:
            ATRData con los valores calculados
        """
        cache_key = f"atr_{symbol}_{period}"
        
        if cache_key in self._atr_cache:
            cached = self._atr_cache[cache_key]
            if (datetime.now() - cached.timestamp).seconds < self._cache_ttl:
                return cached
        
        try:
            if ohlc_data is None and self.trading_service:
                ohlc_data = self._get_ohlc_data(symbol, period + 5)
            
            if not ohlc_data or len(ohlc_data) < period:
                return self._fallback_atr(symbol)
            
            true_ranges = []
            
            for i in range(1, len(ohlc_data)):
                high = float(ohlc_data[i].get('high', 0))
                low = float(ohlc_data[i].get('low', 0))
                prev_close = float(ohlc_data[i-1].get('close', 0))
                
                if high <= 0 or low <= 0 or prev_close <= 0:
                    continue
                
                tr1 = high - low
                tr2 = abs(high - prev_close)
                tr3 = abs(low - prev_close)
                
                true_range = max(tr1, tr2, tr3)
                true_ranges.append(true_range)
            
            if len(true_ranges) < period:
                return self._fallback_atr(symbol)
            
            atr_14 = sum(true_ranges[-14:]) / min(14, len(true_ranges[-14:]))
            atr_7 = sum(true_ranges[-7:]) / min(7, len(true_ranges[-7:]))
            
            current_price = float(ohlc_data[-1].get('close', 0))
            if current_price > 0:
                atr_percentage = (atr_14 / current_price) * 100
            else:
                atr_percentage = 2.0
            
            if atr_percentage > 5:
                volatility_status = "EXTREME"
            elif atr_percentage > 3:
                volatility_status = "HIGH"
            elif atr_percentage > 1.5:
                volatility_status = "NORMAL"
            else:
                volatility_status = "LOW"
            
            atr_data = ATRData(
                symbol=symbol,
                atr_14=atr_14,
                atr_7=atr_7,
                atr_percentage=atr_percentage,
                volatility_status=volatility_status
            )
            
            self._atr_cache[cache_key] = atr_data
            
            logger.debug(f"📊 ATR calculado para {symbol}: ${atr_14:.2f} ({atr_percentage:.2f}%)")
            
            return atr_data
            
        except Exception as e:
            logger.warning(f"⚠️ Error calculando ATR para {symbol}: {e}")
            return self._fallback_atr(symbol)
    
    def _get_ohlc_data(self, symbol: str, periods: int) -> Optional[List[Dict]]:
        """Obtiene datos OHLC del servicio de trading"""
        try:
            if hasattr(self.trading_service, 'get_ohlc_data'):
                return self.trading_service.get_ohlc_data(symbol, periods)
            elif hasattr(self.trading_service, 'kraken_api'):
                return self.trading_service.kraken_api.get_ohlc(symbol, periods)
        except Exception as e:
            logger.debug(f"Error obteniendo OHLC: {e}")
        return None
    
    def _fallback_atr(self, symbol: str) -> ATRData:
        """ATR fallback basado en volatilidad típica por símbolo"""
        fallback_values = {
            'BTC/USD': (1500.0, 750.0, 1.5),
            'ETH/USD': (80.0, 40.0, 2.0),
            'SOL/USD': (3.0, 1.5, 2.5),
            'XRP/USD': (0.02, 0.01, 2.0),
            'ADA/USD': (0.015, 0.008, 2.0),
            'DOGE/USD': (0.005, 0.003, 3.0),
            'AVAX/USD': (1.5, 0.8, 2.5),
            'DOT/USD': (0.25, 0.12, 2.0),
            'LINK/USD': (0.5, 0.25, 2.5),
            'MATIC/USD': (0.02, 0.01, 2.5),
            'ATOM/USD': (0.3, 0.15, 2.0),
        }
        
        base_symbol = symbol.replace('/USD', '').replace('USD', '')
        key = f"{base_symbol}/USD"
        
        if key in fallback_values:
            atr_14, atr_7, pct = fallback_values[key]
        else:
            atr_14, atr_7, pct = (100.0, 50.0, 2.0)
        
        return ATRData(
            symbol=symbol,
            atr_14=atr_14,
            atr_7=atr_7,
            atr_percentage=pct,
            volatility_status="NORMAL"
        )


class DynamicPositionManager:
    """
    Gestor de posiciones dinámico V6.5.3 PREMIUM.
    
    Integra:
    - ATR Calculator para volatilidad
    - Non-Markovian Kernel para régimen de mercado
    - CAES para ajuste por confianza
    - Coherence Engine para validación
    - Risk Guardian para límites
    """
    
    REGIME_MULTIPLIERS = {
        MarketRegime.TRENDING_BULL: {'tp': 3.0, 'sl': 1.2},
        MarketRegime.TRENDING_BEAR: {'tp': 2.0, 'sl': 1.0},
        MarketRegime.RANGING: {'tp': 2.0, 'sl': 1.5},
        MarketRegime.HIGH_VOLATILITY: {'tp': 3.5, 'sl': 2.0},
        MarketRegime.LOW_VOLATILITY: {'tp': 1.5, 'sl': 1.0},
        MarketRegime.BREAKOUT: {'tp': 4.0, 'sl': 1.5},
    }
    
    CONFIDENCE_ADJUSTMENTS = {
        'high': {'trailing_distance': 0.8, 'tp_extension': 1.3},
        'medium': {'trailing_distance': 1.0, 'tp_extension': 1.0},
        'low': {'trailing_distance': 1.2, 'tp_extension': 0.8},
    }
    
    def __init__(self, trading_service=None, paper_trading=None,
                 non_markovian_kernel=None, coherence_engine=None,
                 risk_guardian=None, caes_engine=None, redis_cache=None):
        self.trading_service = trading_service
        self.paper_trading = paper_trading
        self.non_markovian_kernel = non_markovian_kernel
        self.coherence_engine = coherence_engine
        self.risk_guardian = risk_guardian
        self.caes_engine = caes_engine
        
        self.atr_calculator = ATRCalculator(trading_service, redis_cache)
        
        self._position_levels: Dict[str, PositionLevels] = {}
        self._trailing_state: Dict[str, Dict] = {}
        
        self.base_tp_multiplier = 2.5
        self.base_sl_multiplier = 1.5
        self.trailing_activation_atr = 1.5
        self.break_even_activation_atr = 1.0
        
        logger.info("📊 DynamicPositionManager V6.5.3 PREMIUM inicializado")
    
    def calculate_dynamic_levels(self, symbol: str, entry_price: float,
                                  side: str = 'buy', confidence: float = 0.5,
                                  original_analysis: Optional[Dict] = None) -> PositionLevels:
        """
        Calcula niveles dinámicos de TP/SL basados en ATR y régimen de mercado.
        
        Args:
            symbol: Par de trading
            entry_price: Precio de entrada
            side: 'buy' o 'sell'
            confidence: Nivel de confianza del trade (0-1)
            original_analysis: Análisis original para contexto
            
        Returns:
            PositionLevels con todos los niveles calculados
        """
        atr_data = self.atr_calculator.calculate_atr(symbol)
        if not atr_data:
            logger.warning(f"⚠️ No se pudo calcular ATR para {symbol}, usando fallback")
            atr_value = entry_price * 0.02
        else:
            atr_value = atr_data.atr_14
        
        regime = self._detect_market_regime(symbol, original_analysis)
        
        regime_mult = self.REGIME_MULTIPLIERS.get(regime, {'tp': 2.5, 'sl': 1.5})
        
        if confidence >= 0.7:
            conf_level = 'high'
        elif confidence >= 0.4:
            conf_level = 'medium'
        else:
            conf_level = 'low'
        
        conf_adj = self.CONFIDENCE_ADJUSTMENTS[conf_level]
        
        tp_distance = atr_value * regime_mult['tp'] * conf_adj['tp_extension']
        sl_distance = atr_value * regime_mult['sl']
        
        if side == 'buy':
            stop_loss = entry_price - sl_distance
            take_profit = entry_price + tp_distance
        else:
            stop_loss = entry_price + sl_distance
            take_profit = entry_price - tp_distance
        
        levels = PositionLevels(
            entry_price=entry_price,
            current_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            trailing_stop=None,
            break_even_active=False,
            atr_value=atr_value,
            atr_multiplier_sl=regime_mult['sl'],
            atr_multiplier_tp=regime_mult['tp'],
            confidence_adjustment=conf_adj['trailing_distance'],
            regime=regime
        )
        
        position_key = f"{symbol}_{entry_price}_{datetime.now().timestamp()}"
        self._position_levels[position_key] = levels
        
        tp_pct = ((take_profit - entry_price) / entry_price) * 100
        sl_pct = ((entry_price - stop_loss) / entry_price) * 100
        
        logger.info(f"""📊 V6.5.3 Niveles Dinámicos Calculados:
   Symbol: {symbol} | Entry: ${entry_price:.2f}
   ATR: ${atr_value:.2f} | Régimen: {regime.value}
   TP: ${take_profit:.2f} (+{tp_pct:.2f}%)
   SL: ${stop_loss:.2f} (-{sl_pct:.2f}%)
   Confianza: {confidence:.2%} → Ajuste: {conf_level}""")
        
        return levels
    
    def update_trailing_stop(self, position: Dict, current_price: float) -> Tuple[bool, Optional[float], str]:
        """
        Actualiza el trailing stop de una posición.
        
        Returns:
            (should_close, new_trailing_stop, reason)
        """
        symbol = position.get('symbol')
        entry_price = float(position.get('entry_price', 0))
        quantity = float(position.get('quantity', 0))
        
        if not symbol or entry_price <= 0:
            return False, None, "Invalid position data"
        
        atr_data = self.atr_calculator.calculate_atr(symbol)
        atr_value = atr_data.atr_14 if atr_data else entry_price * 0.02
        
        profit_distance = current_price - entry_price
        profit_in_atr = profit_distance / atr_value if atr_value > 0 else 0
        
        current_trailing = position.get('trailing_stop')
        
        if profit_in_atr >= self.break_even_activation_atr and not position.get('break_even_active'):
            new_trailing = entry_price + (atr_value * 0.1)
            logger.info(f"🔒 Break-even activado para {symbol}: ${new_trailing:.2f}")
            return False, new_trailing, "break_even_activated"
        
        if profit_in_atr >= self.trailing_activation_atr:
            confidence_adj = position.get('confidence_adjustment', 1.0)
            trailing_distance = atr_value * confidence_adj
            
            new_trailing = current_price - trailing_distance
            
            if current_trailing is None or new_trailing > current_trailing:
                logger.info(f"📈 Trailing stop actualizado para {symbol}: ${new_trailing:.2f} (profit: {profit_in_atr:.1f}x ATR)")
                return False, new_trailing, "trailing_updated"
        
        if current_trailing and current_price <= current_trailing:
            logger.info(f"🛑 Trailing stop alcanzado para {symbol}: ${current_price:.2f} <= ${current_trailing:.2f}")
            return True, current_trailing, "trailing_hit"
        
        return False, current_trailing, "no_change"
    
    def check_position_exit(self, position: Dict, current_price: float,
                            validate_with_coherence: bool = True) -> Tuple[bool, str, Dict]:
        """
        Verifica si una posición debe cerrarse.
        
        Integra:
        - TP/SL dinámico basado en ATR
        - Non-Markovian Kernel para régimen en tiempo real
        - CAES para ajuste por confianza original
        - Trailing stop con persistencia de estado
        - Break-even automático
        - Validación con Coherence Engine
        - Límites de Risk Guardian
        
        Returns:
            (should_close, reason, details)
        """
        symbol = position.get('symbol')
        entry_price = float(position.get('entry_price', 0))
        position_id = position.get('id', f"{symbol}_{entry_price}")
        
        if not symbol or entry_price <= 0 or current_price <= 0:
            return False, "invalid_data", {}
        
        atr_data = self.atr_calculator.calculate_atr(symbol)
        atr_value = atr_data.atr_14 if atr_data else entry_price * 0.02
        
        regime = self._detect_market_regime(symbol)
        regime_mult = self.REGIME_MULTIPLIERS.get(regime, {'tp': 2.5, 'sl': 1.5})
        
        confidence = 0.5
        conf_level = 'medium'
        if self.caes_engine:
            try:
                caes_data = position.get('caes_data', {})
                confidence = caes_data.get('confidence', 0.5)
                if confidence >= 0.7:
                    conf_level = 'high'
                elif confidence < 0.4:
                    conf_level = 'low'
            except Exception:
                pass
        
        conf_adj = self.CONFIDENCE_ADJUSTMENTS[conf_level]
        
        tp_distance = atr_value * regime_mult['tp'] * conf_adj['tp_extension']
        sl_distance = atr_value * regime_mult['sl']
        
        take_profit = entry_price + tp_distance
        stop_loss = entry_price - sl_distance
        
        trailing_state = self._trailing_state.get(position_id, {})
        current_trailing = trailing_state.get('trailing_stop')
        break_even_active = trailing_state.get('break_even_active', False)
        
        if current_trailing:
            stop_loss = max(stop_loss, current_trailing)
        
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        pnl_usd = (current_price - entry_price) * float(position.get('quantity', 0))
        
        details = {
            'symbol': symbol,
            'entry_price': entry_price,
            'current_price': current_price,
            'take_profit': take_profit,
            'stop_loss': stop_loss,
            'trailing_stop': current_trailing,
            'break_even_active': break_even_active,
            'pnl_pct': pnl_pct,
            'pnl_usd': pnl_usd,
            'atr': atr_value,
            'regime': regime.value,
            'confidence': confidence,
            'conf_level': conf_level
        }
        
        if self.risk_guardian:
            try:
                risk_check = self.risk_guardian.check_trade_allowed(
                    symbol=symbol,
                    side='sell',
                    amount_usd=abs(pnl_usd)
                )
                if risk_check and not risk_check.get('allowed', True):
                    details['risk_guardian_block'] = risk_check.get('reason', 'blocked')
            except Exception:
                pass
        
        if current_price >= take_profit:
            if validate_with_coherence and self.coherence_engine:
                coherence_ok = self._validate_exit_with_coherence(symbol, 'sell', current_price)
                if not coherence_ok:
                    logger.info(f"⏳ TP alcanzado pero Coherence Engine sugiere esperar: {symbol}")
                    return False, "coherence_hold", details
            
            self._trailing_state.pop(position_id, None)
            logger.info(f"✅ TAKE PROFIT: {symbol} @ ${current_price:.2f} (+{pnl_pct:.2f}%) | Régimen: {regime.value}")
            return True, "take_profit", details
        
        if current_price <= stop_loss:
            self._trailing_state.pop(position_id, None)
            logger.info(f"🛑 STOP LOSS: {symbol} @ ${current_price:.2f} ({pnl_pct:.2f}%) | Régimen: {regime.value}")
            return True, "stop_loss", details
        
        profit_distance = current_price - entry_price
        profit_in_atr = profit_distance / atr_value if atr_value > 0 else 0
        
        if profit_in_atr >= self.break_even_activation_atr and not break_even_active:
            new_trailing = entry_price + (atr_value * 0.1)
            self._trailing_state[position_id] = {
                'trailing_stop': new_trailing,
                'break_even_active': True,
                'last_update': datetime.now()
            }
            details['new_trailing_stop'] = new_trailing
            details['trailing_status'] = 'break_even_activated'
            logger.info(f"🔒 Break-even activado: {symbol} trailing @ ${new_trailing:.2f}")
        
        elif profit_in_atr >= self.trailing_activation_atr:
            trailing_distance = atr_value * conf_adj['trailing_distance']
            new_trailing = current_price - trailing_distance
            
            if current_trailing is None or new_trailing > current_trailing:
                self._trailing_state[position_id] = {
                    'trailing_stop': new_trailing,
                    'break_even_active': True,
                    'last_update': datetime.now()
                }
                details['new_trailing_stop'] = new_trailing
                details['trailing_status'] = 'trailing_updated'
                logger.debug(f"📈 Trailing actualizado: {symbol} @ ${new_trailing:.2f}")
        
        if current_trailing and current_price <= current_trailing:
            self._trailing_state.pop(position_id, None)
            details['trailing_stop'] = current_trailing
            logger.info(f"📉 TRAILING STOP: {symbol} @ ${current_price:.2f} <= ${current_trailing:.2f}")
            return True, "trailing_stop", details
        
        return False, "hold", details
    
    def manage_all_positions(self, user_id: str, paper_mode: bool = True) -> Dict[str, Any]:
        """
        Gestiona todas las posiciones abiertas de un usuario.
        
        Returns:
            Resumen de acciones tomadas
        """
        if not self.paper_trading:
            return {'error': 'Paper trading not available'}
        
        try:
            open_positions = self.paper_trading.get_open_positions(user_id)
            
            if not open_positions:
                return {'positions_checked': 0, 'actions': []}
            
            results = {
                'positions_checked': len(open_positions),
                'positions_closed': 0,
                'trailing_updates': 0,
                'break_even_activations': 0,
                'actions': [],
                'total_pnl': 0.0
            }
            
            for position in open_positions:
                symbol = position.get('symbol')
                
                current_price = self._get_current_price(symbol)
                if not current_price:
                    continue
                
                should_close, reason, details = self.check_position_exit(position, current_price)
                
                if should_close:
                    close_result = self._close_position(user_id, position, current_price, reason)
                    
                    if close_result.get('success'):
                        results['positions_closed'] += 1
                        results['total_pnl'] += details.get('pnl_usd', 0)
                        results['actions'].append({
                            'symbol': symbol,
                            'action': 'closed',
                            'reason': reason,
                            'pnl_usd': details.get('pnl_usd', 0),
                            'pnl_pct': details.get('pnl_pct', 0)
                        })
                else:
                    if details.get('trailing_status') == 'break_even_activated':
                        results['break_even_activations'] += 1
                    elif details.get('trailing_status') == 'trailing_updated':
                        results['trailing_updates'] += 1
            
            if results['positions_closed'] > 0:
                logger.info(f"📊 Position Manager: {results['positions_closed']} posiciones cerradas, P&L: ${results['total_pnl']:.2f}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error en manage_all_positions: {e}")
            return {'error': str(e)}
    
    def _detect_market_regime(self, symbol: str, 
                               analysis: Optional[Dict] = None) -> MarketRegime:
        """Detecta el régimen de mercado usando Non-Markovian Kernel"""
        if self.non_markovian_kernel:
            try:
                regime_data = self.non_markovian_kernel.get_current_regime(symbol)
                if regime_data:
                    regime_str = regime_data.get('regime', 'ranging').lower()
                    
                    regime_map = {
                        'bull': MarketRegime.TRENDING_BULL,
                        'trending_bull': MarketRegime.TRENDING_BULL,
                        'bear': MarketRegime.TRENDING_BEAR,
                        'trending_bear': MarketRegime.TRENDING_BEAR,
                        'ranging': MarketRegime.RANGING,
                        'sideways': MarketRegime.RANGING,
                        'high_vol': MarketRegime.HIGH_VOLATILITY,
                        'volatile': MarketRegime.HIGH_VOLATILITY,
                        'low_vol': MarketRegime.LOW_VOLATILITY,
                        'calm': MarketRegime.LOW_VOLATILITY,
                        'breakout': MarketRegime.BREAKOUT,
                    }
                    
                    return regime_map.get(regime_str, MarketRegime.RANGING)
            except Exception as e:
                logger.debug(f"Error obteniendo régimen de Non-Markovian: {e}")
        
        if analysis:
            sentiment = analysis.get('sentiment', 'neutral').lower()
            if sentiment in ['bullish', 'very_bullish']:
                return MarketRegime.TRENDING_BULL
            elif sentiment in ['bearish', 'very_bearish']:
                return MarketRegime.TRENDING_BEAR
        
        return MarketRegime.RANGING
    
    def _validate_exit_with_coherence(self, symbol: str, side: str, 
                                       current_price: float) -> bool:
        """Valida el cierre con Coherence Engine"""
        if not self.coherence_engine:
            return True
        
        try:
            coherence_result = self.coherence_engine.validate_signal(
                symbol=symbol,
                signal=side.upper(),
                price=current_price
            )
            
            coherence_score = coherence_result.get('coherence_score', 0.5)
            return coherence_score >= 0.3
            
        except Exception as e:
            logger.debug(f"Error validando con Coherence Engine: {e}")
            return True
    
    def _check_risk_guardian_override(self, symbol: str, pnl_usd: float) -> Optional[str]:
        """Verifica si Risk Guardian tiene alguna acción especial"""
        if not self.risk_guardian:
            return None
        
        try:
            return None
        except Exception:
            return None
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Obtiene el precio actual con reintentos usando Kraken API"""
        if not self.trading_service:
            logger.warning(f"⚠️ _get_current_price: trading_service no disponible")
            return None
        
        if not hasattr(self.trading_service, 'kraken') or not self.trading_service.kraken:
            logger.warning(f"⚠️ _get_current_price: Kraken client no disponible")
            return None
        
        symbol_map = {
            'BTC/USD': 'XBTUSD', 'ETH/USD': 'ETHUSD', 'SOL/USD': 'SOLUSD',
            'XRP/USD': 'XRPUSD', 'ADA/USD': 'ADAUSD', 'DOT/USD': 'DOTUSD',
            'LINK/USD': 'LINKUSD', 'AVAX/USD': 'AVAXUSD', 'POL/USD': 'POLUSD',
            'ATOM/USD': 'ATOMUSD', 'LTC/USD': 'LTCUSD', 'DOGE/USD': 'DOGEUSD',
            'MATIC/USD': 'MATICUSD', 'UNI/USD': 'UNIUSD', 'AAVE/USD': 'AAVEUSD',
            'SHIB/USD': 'SHIBUSD', 'CRV/USD': 'CRVUSD', 'APE/USD': 'APEUSD',
            'SAND/USD': 'SANDUSD', 'MANA/USD': 'MANAUSD', 'FTM/USD': 'FTMUSD',
            'BCH/USD': 'BCHUSD', 'TRX/USD': 'TRXUSD', 'ALGO/USD': 'ALGOUSD',
            'XLM/USD': 'XLMUSD', 'EOS/USD': 'EOSUSD', 'NEAR/USD': 'NEARUSD'
        }
        kraken_pair = symbol_map.get(symbol)
        if not kraken_pair:
            kraken_pair = symbol.replace('/', '')
            logger.warning(f"⚠️ Símbolo {symbol} no mapeado, usando fallback: {kraken_pair}")
        
        for attempt in range(3):
            try:
                ticker = self.trading_service.kraken.get_ticker(kraken_pair)
                if ticker and 'c' in ticker:
                    price = float(ticker['c'][0])
                    if price > 0:
                        return price
            except Exception as e:
                logger.debug(f"Intento {attempt+1}/3 obteniendo precio de {symbol}: {e}")
                time.sleep(0.3)
        
        logger.warning(f"⚠️ No se pudo obtener precio para {symbol} después de 3 intentos")
        return None
    
    def _close_position(self, user_id: str, position: Dict, 
                         exit_price: float, reason: str) -> Dict:
        """Cierra una posición usando el método FIFO"""
        if not self.paper_trading:
            return {'success': False, 'error': 'Paper trading not available'}
        
        try:
            symbol = position.get('symbol')
            quantity = float(position.get('quantity', 0))
            
            result = self.paper_trading._close_position_fifo_v2(
                user_id=user_id,
                symbol=symbol,
                sell_quantity=quantity,
                exit_price=exit_price
            )
            
            if result:
                result['close_reason'] = reason
                return {'success': True, **result}
            else:
                return {'success': False, 'error': 'FIFO close returned None'}
                
        except Exception as e:
            logger.error(f"❌ Error cerrando posición: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_position_summary(self, symbol: str, entry_price: float,
                              current_price: float, confidence: float = 0.5) -> Dict:
        """
        Obtiene un resumen completo de niveles para una posición.
        Útil para mostrar en dashboard o notificaciones.
        """
        levels = self.calculate_dynamic_levels(
            symbol=symbol,
            entry_price=entry_price,
            side='buy',
            confidence=confidence
        )
        
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        tp_distance_pct = ((levels.take_profit - entry_price) / entry_price) * 100
        sl_distance_pct = ((entry_price - levels.stop_loss) / entry_price) * 100
        
        progress_to_tp = min(100, max(0, (pnl_pct / tp_distance_pct) * 100)) if tp_distance_pct > 0 else 0
        
        return {
            'symbol': symbol,
            'entry_price': entry_price,
            'current_price': current_price,
            'take_profit': levels.take_profit,
            'stop_loss': levels.stop_loss,
            'trailing_stop': levels.trailing_stop,
            'break_even_active': levels.break_even_active,
            'pnl_pct': pnl_pct,
            'tp_distance_pct': tp_distance_pct,
            'sl_distance_pct': sl_distance_pct,
            'progress_to_tp': progress_to_tp,
            'atr': levels.atr_value,
            'regime': levels.regime.value,
            'risk_reward_ratio': tp_distance_pct / sl_distance_pct if sl_distance_pct > 0 else 0
        }
