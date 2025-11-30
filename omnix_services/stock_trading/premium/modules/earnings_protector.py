"""
📅 Earnings Calendar Protector V6.3
Blocks or adjusts trading around high-risk market events
Critical for institutional-grade risk management
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import pytz

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of market-moving events"""
    EARNINGS = "earnings"
    FOMC = "fomc"
    CPI = "cpi"
    NFP = "nfp"
    GDP = "gdp"
    RETAIL_SALES = "retail_sales"
    HOUSING = "housing"
    PMI = "pmi"
    LEGAL = "legal"
    FDA = "fda"
    DIVIDEND = "dividend"
    SPLIT = "split"
    IPO_LOCKUP = "ipo_lockup"


class EventImpact(Enum):
    """Impact level of events"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EarningsProtector:
    """
    Institutional-grade event risk protection
    
    Features:
    - Earnings calendar integration
    - FOMC/Fed meeting detection
    - Economic data release awareness
    - Automatic position sizing reduction
    - Trade blocking for critical events
    """
    
    EVENT_IMPACT_MAP = {
        EventType.EARNINGS: EventImpact.CRITICAL,
        EventType.FOMC: EventImpact.CRITICAL,
        EventType.CPI: EventImpact.HIGH,
        EventType.NFP: EventImpact.HIGH,
        EventType.GDP: EventImpact.HIGH,
        EventType.FDA: EventImpact.CRITICAL,
        EventType.LEGAL: EventImpact.HIGH,
        EventType.RETAIL_SALES: EventImpact.MEDIUM,
        EventType.HOUSING: EventImpact.MEDIUM,
        EventType.PMI: EventImpact.MEDIUM,
        EventType.DIVIDEND: EventImpact.LOW,
        EventType.SPLIT: EventImpact.LOW,
        EventType.IPO_LOCKUP: EventImpact.HIGH,
    }
    
    POSITION_MULTIPLIERS = {
        EventImpact.LOW: 0.9,
        EventImpact.MEDIUM: 0.7,
        EventImpact.HIGH: 0.4,
        EventImpact.CRITICAL: 0.0,
    }
    
    FOMC_DATES_2024_2025 = [
        "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12",
        "2024-07-31", "2024-09-18", "2024-11-07", "2024-12-18",
        "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18",
        "2025-07-30", "2025-09-17", "2025-11-05", "2025-12-17",
    ]
    
    def __init__(self, database_service=None):
        self.database_service = database_service
        self.et_tz = pytz.timezone('US/Eastern')
        
        self.earnings_cache: Dict[str, Dict] = {}
        self.event_calendar: List[Dict] = []
        self.blocked_symbols: set = set()
        
        self._load_known_events()
        
        logger.info("📅 Earnings Protector V6.3 inicializado")
    
    def _load_known_events(self):
        """Load known major events into calendar"""
        today = datetime.now(self.et_tz).date()
        
        for fomc_date_str in self.FOMC_DATES_2024_2025:
            fomc_date = datetime.strptime(fomc_date_str, "%Y-%m-%d").date()
            if fomc_date >= today:
                self.event_calendar.append({
                    'date': fomc_date,
                    'event_type': EventType.FOMC,
                    'symbol': 'MARKET',
                    'description': 'FOMC Meeting Decision',
                    'impact': EventImpact.CRITICAL
                })
        
        logger.info(f"   📆 {len(self.event_calendar)} eventos cargados en calendario")
    
    def check_earnings(
        self,
        symbol: str,
        earnings_date: Optional[str] = None
    ) -> Dict:
        """
        Check if symbol has upcoming earnings
        
        Args:
            symbol: Stock ticker
            earnings_date: Known earnings date (YYYY-MM-DD) if available
        
        Returns:
            Earnings risk assessment
        """
        today = datetime.now(self.et_tz).date()
        
        if earnings_date:
            try:
                earn_date = datetime.strptime(earnings_date, "%Y-%m-%d").date()
                self.earnings_cache[symbol] = {
                    'date': earn_date,
                    'confirmed': True
                }
            except ValueError:
                pass
        
        cached = self.earnings_cache.get(symbol, {})
        earn_date = cached.get('date')
        
        if not earn_date:
            return {
                'symbol': symbol,
                'has_earnings': False,
                'earnings_date': None,
                'days_until': None,
                'should_block': False,
                'position_multiplier': 1.0,
                'recommendation': "Sin earnings conocidos, proceder con precaución estándar"
            }
        
        days_until = (earn_date - today).days
        
        if days_until <= 0:
            should_block = True
            multiplier = 0.0
            recommendation = "🚫 EARNINGS HOY - Bloquear todo trading"
        elif days_until == 1:
            should_block = True
            multiplier = 0.0
            recommendation = "🚫 EARNINGS MAÑANA - Cerrar posiciones o cubrir"
        elif days_until <= 3:
            should_block = False
            multiplier = 0.3
            recommendation = "⚠️ Earnings en 3 días - Reducir exposición 70%"
        elif days_until <= 7:
            should_block = False
            multiplier = 0.6
            recommendation = "⚠️ Earnings esta semana - Reducir posición 40%"
        else:
            should_block = False
            multiplier = 1.0
            recommendation = "✅ Earnings lejano, operar normalmente"
        
        if should_block:
            self.blocked_symbols.add(symbol)
        
        return {
            'symbol': symbol,
            'has_earnings': True,
            'earnings_date': earn_date.strftime('%Y-%m-%d'),
            'days_until': days_until,
            'should_block': should_block,
            'position_multiplier': multiplier,
            'recommendation': recommendation,
            'confirmed': cached.get('confirmed', False)
        }
    
    def check_market_events(self, date: Optional[datetime] = None) -> Dict:
        """
        Check for market-wide events on a given date
        
        Returns:
            List of events and their impact
        """
        if date is None:
            date = datetime.now(self.et_tz)
        
        check_date = date.date()
        
        today_events = [
            e for e in self.event_calendar 
            if e['date'] == check_date
        ]
        
        tomorrow = check_date + timedelta(days=1)
        tomorrow_events = [
            e for e in self.event_calendar 
            if e['date'] == tomorrow
        ]
        
        week_end = check_date + timedelta(days=7)
        week_events = [
            e for e in self.event_calendar 
            if check_date < e['date'] <= week_end
        ]
        
        has_critical_today = any(
            e['impact'] == EventImpact.CRITICAL for e in today_events
        )
        has_critical_tomorrow = any(
            e['impact'] == EventImpact.CRITICAL for e in tomorrow_events
        )
        
        if has_critical_today:
            market_mode = "DEFENSIVE"
            market_multiplier = 0.3
        elif has_critical_tomorrow:
            market_mode = "CAUTIOUS"
            market_multiplier = 0.5
        elif week_events:
            market_mode = "AWARE"
            market_multiplier = 0.8
        else:
            market_mode = "NORMAL"
            market_multiplier = 1.0
        
        return {
            'date': check_date.strftime('%Y-%m-%d'),
            'today_events': [self._format_event(e) for e in today_events],
            'tomorrow_events': [self._format_event(e) for e in tomorrow_events],
            'week_events': [self._format_event(e) for e in week_events],
            'market_mode': market_mode,
            'market_multiplier': market_multiplier,
            'has_critical_today': has_critical_today,
            'has_critical_tomorrow': has_critical_tomorrow,
            'recommendation': self._market_recommendation(market_mode)
        }
    
    def should_block_trade(
        self,
        symbol: str,
        signal_type: str = "OPEN"
    ) -> Tuple[bool, str, float]:
        """
        Determine if trade should be blocked due to events
        
        Returns:
            (should_block, reason, position_multiplier)
        """
        earnings_check = self.check_earnings(symbol)
        market_check = self.check_market_events()
        
        if earnings_check['should_block']:
            return True, earnings_check['recommendation'], 0.0
        
        if market_check['has_critical_today']:
            return True, f"Evento crítico hoy: {market_check['today_events']}", 0.0
        
        if symbol in self.blocked_symbols:
            return True, f"{symbol} bloqueado por evento pendiente", 0.0
        
        final_multiplier = min(
            earnings_check['position_multiplier'],
            market_check['market_multiplier']
        )
        
        if final_multiplier < 0.5:
            reason = f"Posición reducida: earnings={earnings_check['position_multiplier']}, market={market_check['market_multiplier']}"
        else:
            reason = "OK para operar"
        
        return False, reason, final_multiplier
    
    def add_earnings_date(
        self,
        symbol: str,
        earnings_date: str,
        time_of_day: str = "AMC"
    ):
        """
        Add earnings date for a symbol
        
        Args:
            symbol: Stock ticker
            earnings_date: Date string YYYY-MM-DD
            time_of_day: BMO (Before Market Open), AMC (After Market Close)
        """
        try:
            earn_date = datetime.strptime(earnings_date, "%Y-%m-%d").date()
            self.earnings_cache[symbol] = {
                'date': earn_date,
                'time': time_of_day,
                'confirmed': True
            }
            logger.info(f"📅 Earnings añadido: {symbol} - {earnings_date} ({time_of_day})")
        except ValueError as e:
            logger.error(f"❌ Formato de fecha inválido: {e}")
    
    def add_custom_event(
        self,
        event_type: EventType,
        date: str,
        symbol: str = "MARKET",
        description: str = ""
    ):
        """Add custom event to calendar"""
        try:
            event_date = datetime.strptime(date, "%Y-%m-%d").date()
            self.event_calendar.append({
                'date': event_date,
                'event_type': event_type,
                'symbol': symbol,
                'description': description,
                'impact': self.EVENT_IMPACT_MAP.get(event_type, EventImpact.MEDIUM)
            })
            logger.info(f"📅 Evento añadido: {event_type.value} - {date}")
        except ValueError as e:
            logger.error(f"❌ Error añadiendo evento: {e}")
    
    def _format_event(self, event: Dict) -> Dict:
        """Format event for output"""
        return {
            'type': event['event_type'].value,
            'symbol': event['symbol'],
            'description': event['description'],
            'impact': event['impact'].value,
            'date': event['date'].strftime('%Y-%m-%d')
        }
    
    def _market_recommendation(self, mode: str) -> str:
        """Generate market mode recommendation"""
        recommendations = {
            'DEFENSIVE': "🚫 Modo defensivo: solo gestión de posiciones existentes",
            'CAUTIOUS': "⚠️ Modo cauteloso: reducir exposición, evitar nuevas posiciones grandes",
            'AWARE': "📊 Modo alerta: operar con tamaños reducidos",
            'NORMAL': "✅ Condiciones normales de mercado"
        }
        return recommendations.get(mode, "Evaluar manualmente")
    
    def clear_blocked_symbol(self, symbol: str):
        """Clear blocked symbol after event passes"""
        if symbol in self.blocked_symbols:
            self.blocked_symbols.remove(symbol)
            logger.info(f"✅ {symbol} desbloqueado")
    
    def get_high_risk_symbols(self) -> List[str]:
        """Get list of symbols with upcoming earnings in 3 days"""
        today = datetime.now(self.et_tz).date()
        high_risk = []
        
        for symbol, data in self.earnings_cache.items():
            if data.get('date'):
                days_until = (data['date'] - today).days
                if 0 <= days_until <= 3:
                    high_risk.append(symbol)
        
        return high_risk
    
    def get_status(self) -> Dict:
        """Get current earnings protector status"""
        market_check = self.check_market_events()
        high_risk = self.get_high_risk_symbols()
        
        return {
            'module': 'Earnings Protector V6.3',
            'status': 'ACTIVE',
            'market_mode': market_check['market_mode'],
            'market_multiplier': market_check['market_multiplier'],
            'blocked_symbols': list(self.blocked_symbols),
            'high_risk_earnings': high_risk,
            'upcoming_events': len(market_check['week_events']),
            'symbols_tracked': len(self.earnings_cache),
            'protection_rules': {
                'block_on_earnings_day': True,
                'reduce_before_earnings': True,
                'fomc_protection': True,
                'economic_data_awareness': True
            }
        }


class EarningsCalendarService:
    """
    Service to fetch and maintain earnings calendar
    Can integrate with external APIs like Alpha Vantage, Finnhub, etc.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.cache: Dict[str, Dict] = {}
    
    async def fetch_earnings(self, symbol: str) -> Optional[Dict]:
        """
        Fetch earnings date from external API
        TODO: Integrate with Alpha Vantage EARNINGS endpoint
        """
        pass
    
    async def fetch_economic_calendar(self) -> List[Dict]:
        """
        Fetch upcoming economic events
        TODO: Integrate with economic calendar API
        """
        pass
