"""
🛡️ Gap Risk Protection V6.3
Protects against overnight gaps in stock trading
Critical for stocks where prices can gap 3-10% on news/earnings
"""

import logging
from datetime import datetime, time, timedelta
from typing import Dict, Optional, Tuple
from enum import Enum
import pytz

logger = logging.getLogger(__name__)


class GapRiskLevel(Enum):
    """Gap risk classification"""
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"


class GapProtection:
    """
    Institutional-grade gap risk protection
    
    Features:
    - Pre-market gap detection
    - After-hours risk assessment
    - Position sizing adjustment based on gap risk
    - Automatic trade blocking during high-risk periods
    """
    
    GAP_THRESHOLDS = {
        'minimal': 0.005,
        'low': 0.01,
        'moderate': 0.02,
        'high': 0.03,
        'extreme': 0.05
    }
    
    POSITION_MULTIPLIERS = {
        GapRiskLevel.MINIMAL: 1.0,
        GapRiskLevel.LOW: 0.85,
        GapRiskLevel.MODERATE: 0.6,
        GapRiskLevel.HIGH: 0.3,
        GapRiskLevel.EXTREME: 0.0
    }
    
    def __init__(self, market_hours_manager=None):
        self.market_hours = market_hours_manager
        self.et_tz = pytz.timezone('US/Eastern')
        self.recent_gaps: Dict[str, list] = {}
        self.blocked_symbols: set = set()
        
        self.MARKET_OPEN = time(9, 30)
        self.MARKET_CLOSE = time(16, 0)
        self.PRE_MARKET_START = time(4, 0)
        self.AFTER_HOURS_END = time(20, 0)
        
        self.CLOSE_BUFFER_MINUTES = 30
        self.OPEN_BUFFER_MINUTES = 15
        
        logger.info("🛡️ Gap Protection V6.3 inicializado")
    
    def analyze_gap_risk(
        self,
        symbol: str,
        current_price: float,
        previous_close: float,
        pre_market_price: Optional[float] = None,
        volume_ratio: float = 1.0
    ) -> Dict:
        """
        Analyze gap risk for a symbol
        
        Args:
            symbol: Stock ticker
            current_price: Current or opening price
            previous_close: Previous day's closing price
            pre_market_price: Pre-market price if available
            volume_ratio: Current volume vs average (> 1 = higher than normal)
        
        Returns:
            Gap risk analysis with recommendations
        """
        gap_pct = abs(current_price - previous_close) / previous_close
        gap_direction = "UP" if current_price > previous_close else "DOWN"
        
        risk_level = self._classify_gap_risk(gap_pct, volume_ratio)
        
        pre_market_gap = None
        if pre_market_price:
            pre_market_gap = (pre_market_price - previous_close) / previous_close
        
        position_multiplier = self.POSITION_MULTIPLIERS[risk_level]
        
        should_block = risk_level in [GapRiskLevel.HIGH, GapRiskLevel.EXTREME]
        
        self._record_gap(symbol, gap_pct, gap_direction)
        
        analysis = {
            'symbol': symbol,
            'gap_percentage': round(gap_pct * 100, 2),
            'gap_direction': gap_direction,
            'risk_level': risk_level.value,
            'position_multiplier': position_multiplier,
            'should_block_trade': should_block,
            'pre_market_gap': round(pre_market_gap * 100, 2) if pre_market_gap else None,
            'volume_ratio': volume_ratio,
            'historical_gap_avg': self._get_historical_gap_avg(symbol),
            'recommendation': self._generate_recommendation(risk_level, gap_direction),
            'timestamp': datetime.now(self.et_tz).isoformat()
        }
        
        if should_block:
            self.blocked_symbols.add(symbol)
            logger.warning(f"🚫 {symbol} bloqueado por gap extremo: {gap_pct*100:.2f}%")
        
        return analysis
    
    def _classify_gap_risk(self, gap_pct: float, volume_ratio: float) -> GapRiskLevel:
        """Classify gap risk level with volume adjustment"""
        adjusted_gap = gap_pct * (1 + (volume_ratio - 1) * 0.3)
        
        if adjusted_gap >= self.GAP_THRESHOLDS['extreme']:
            return GapRiskLevel.EXTREME
        elif adjusted_gap >= self.GAP_THRESHOLDS['high']:
            return GapRiskLevel.HIGH
        elif adjusted_gap >= self.GAP_THRESHOLDS['moderate']:
            return GapRiskLevel.MODERATE
        elif adjusted_gap >= self.GAP_THRESHOLDS['low']:
            return GapRiskLevel.LOW
        else:
            return GapRiskLevel.MINIMAL
    
    def check_trading_window(self) -> Dict:
        """
        Check if current time is safe for trading
        Returns trading window status and restrictions
        """
        now = datetime.now(self.et_tz)
        current_time = now.time()
        
        is_weekend = now.weekday() >= 5
        
        is_market_hours = self.MARKET_OPEN <= current_time <= self.MARKET_CLOSE
        is_pre_market = self.PRE_MARKET_START <= current_time < self.MARKET_OPEN
        is_after_hours = self.MARKET_CLOSE < current_time <= self.AFTER_HOURS_END
        
        close_buffer = (
            datetime.combine(now.date(), self.MARKET_CLOSE) - 
            timedelta(minutes=self.CLOSE_BUFFER_MINUTES)
        ).time()
        
        open_buffer = (
            datetime.combine(now.date(), self.MARKET_OPEN) + 
            timedelta(minutes=self.OPEN_BUFFER_MINUTES)
        ).time()
        
        near_close = close_buffer <= current_time <= self.MARKET_CLOSE
        near_open = self.MARKET_OPEN <= current_time <= open_buffer
        
        if is_weekend:
            status = "CLOSED_WEEKEND"
            can_trade = False
            risk_note = "Mercado cerrado - Gap risk alto el lunes"
        elif not is_market_hours:
            status = "PRE_MARKET" if is_pre_market else "AFTER_HOURS" if is_after_hours else "CLOSED"
            can_trade = False
            risk_note = "Evitar abrir posiciones fuera de horario regular"
        elif near_close:
            status = "NEAR_CLOSE"
            can_trade = True
            risk_note = "Precaución: cerca del cierre, considerar reducir exposición"
        elif near_open:
            status = "NEAR_OPEN"
            can_trade = True
            risk_note = "Precaución: alta volatilidad en apertura"
        else:
            status = "REGULAR_HOURS"
            can_trade = True
            risk_note = "Condiciones normales de trading"
        
        return {
            'status': status,
            'can_trade': can_trade,
            'is_weekend': is_weekend,
            'is_market_hours': is_market_hours,
            'near_close': near_close,
            'near_open': near_open,
            'risk_note': risk_note,
            'current_time_et': current_time.strftime('%H:%M:%S'),
            'next_open': self._get_next_market_open(now),
            'time_to_close': self._get_time_to_close(now) if is_market_hours else None
        }
    
    def should_block_new_position(
        self,
        symbol: str,
        signal_type: str
    ) -> Tuple[bool, str]:
        """
        Determine if a new position should be blocked
        
        Returns:
            (should_block, reason)
        """
        trading_window = self.check_trading_window()
        
        if not trading_window['can_trade']:
            return True, f"Mercado cerrado: {trading_window['status']}"
        
        if trading_window['near_close'] and signal_type == "OPEN":
            return True, "No abrir posiciones nuevas cerca del cierre (gap risk nocturno)"
        
        if symbol in self.blocked_symbols:
            return True, f"{symbol} bloqueado por gap extremo reciente"
        
        if trading_window['is_weekend']:
            return True, "Fin de semana - mercado cerrado"
        
        return False, "OK para operar"
    
    def calculate_overnight_risk(
        self,
        symbol: str,
        position_value: float,
        historical_gaps: Optional[list] = None
    ) -> Dict:
        """
        Calculate overnight holding risk
        """
        if historical_gaps:
            max_gap = max(abs(g) for g in historical_gaps)
            avg_gap = sum(abs(g) for g in historical_gaps) / len(historical_gaps)
        else:
            max_gap = 0.03
            avg_gap = 0.01
        
        max_loss = position_value * max_gap
        expected_loss = position_value * avg_gap
        
        if max_gap > 0.05:
            risk_rating = "EXTREME"
        elif max_gap > 0.03:
            risk_rating = "HIGH"
        elif max_gap > 0.02:
            risk_rating = "MODERATE"
        else:
            risk_rating = "LOW"
        
        return {
            'symbol': symbol,
            'position_value': position_value,
            'max_historical_gap': round(max_gap * 100, 2),
            'avg_historical_gap': round(avg_gap * 100, 2),
            'max_potential_loss': round(max_loss, 2),
            'expected_loss': round(expected_loss, 2),
            'risk_rating': risk_rating,
            'recommendation': self._overnight_recommendation(risk_rating, position_value)
        }
    
    def _record_gap(self, symbol: str, gap_pct: float, direction: str):
        """Record gap for historical analysis"""
        if symbol not in self.recent_gaps:
            self.recent_gaps[symbol] = []
        
        self.recent_gaps[symbol].append({
            'gap': gap_pct,
            'direction': direction,
            'timestamp': datetime.now(self.et_tz)
        })
        
        self.recent_gaps[symbol] = self.recent_gaps[symbol][-30:]
    
    def _get_historical_gap_avg(self, symbol: str) -> Optional[float]:
        """Get average historical gap for symbol"""
        if symbol not in self.recent_gaps or not self.recent_gaps[symbol]:
            return None
        
        gaps = [g['gap'] for g in self.recent_gaps[symbol]]
        return round(sum(gaps) / len(gaps) * 100, 2)
    
    def _generate_recommendation(self, risk_level: GapRiskLevel, direction: str) -> str:
        """Generate trading recommendation based on gap risk"""
        recommendations = {
            GapRiskLevel.MINIMAL: "Condiciones normales, proceder con estrategia estándar",
            GapRiskLevel.LOW: "Gap menor, considerar entrada parcial",
            GapRiskLevel.MODERATE: "Gap moderado, reducir tamaño de posición 40%",
            GapRiskLevel.HIGH: "Gap alto, evitar nuevas posiciones, considerar cobertura",
            GapRiskLevel.EXTREME: "Gap extremo, BLOQUEAR trading, solo gestión de riesgo"
        }
        return recommendations.get(risk_level, "Evaluar manualmente")
    
    def _overnight_recommendation(self, risk_rating: str, position_value: float) -> str:
        """Generate overnight holding recommendation"""
        if risk_rating == "EXTREME":
            return "CERRAR posición antes del cierre - riesgo inaceptable"
        elif risk_rating == "HIGH":
            return "Reducir posición al 50% o usar opciones de cobertura"
        elif risk_rating == "MODERATE":
            return "Considerar stop loss ajustado o reducción parcial"
        else:
            return "Riesgo aceptable para mantener overnight"
    
    def _get_next_market_open(self, now: datetime) -> str:
        """Calculate next market open time"""
        if now.weekday() >= 5:
            days_until_monday = 7 - now.weekday()
            next_open = now + timedelta(days=days_until_monday)
        elif now.time() >= self.MARKET_CLOSE:
            next_open = now + timedelta(days=1)
        else:
            next_open = now
        
        next_open = next_open.replace(
            hour=self.MARKET_OPEN.hour,
            minute=self.MARKET_OPEN.minute,
            second=0
        )
        return next_open.strftime('%Y-%m-%d %H:%M ET')
    
    def _get_time_to_close(self, now: datetime) -> str:
        """Calculate time remaining until market close"""
        close_dt = now.replace(
            hour=self.MARKET_CLOSE.hour,
            minute=self.MARKET_CLOSE.minute,
            second=0
        )
        delta = close_dt - now
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours}h {minutes}m"
    
    def clear_blocked_symbol(self, symbol: str):
        """Manually clear a blocked symbol"""
        if symbol in self.blocked_symbols:
            self.blocked_symbols.remove(symbol)
            logger.info(f"✅ {symbol} desbloqueado manualmente")
    
    def get_status(self) -> Dict:
        """Get current gap protection status"""
        trading_window = self.check_trading_window()
        
        return {
            'module': 'Gap Protection V6.3',
            'status': 'ACTIVE',
            'trading_window': trading_window,
            'blocked_symbols': list(self.blocked_symbols),
            'symbols_tracked': len(self.recent_gaps),
            'protection_rules': {
                'block_near_close': True,
                'block_after_hours': True,
                'block_extreme_gaps': True,
                'position_sizing_adjustment': True
            }
        }
