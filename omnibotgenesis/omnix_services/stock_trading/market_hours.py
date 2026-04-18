"""
🕐 Market Hours Manager
NYSE/NASDAQ trading hours control
"""

import logging
from datetime import datetime, time
from typing import Optional, Dict, Any
import pytz

logger = logging.getLogger(__name__)


class MarketHoursManager:
    """
    Manage stock market trading hours
    NYSE/NASDAQ: Mon-Fri 9:30 AM - 4:00 PM EST
    """
    
    def __init__(self):
        self.timezone = pytz.timezone('America/New_York')
        self.market_open = time(9, 30)
        self.market_close = time(16, 0)
        self.pre_market_open = time(4, 0)
        self.after_hours_close = time(20, 0)
    
    def is_market_open(self) -> bool:
        """Check if market is currently open for regular trading"""
        now = datetime.now(self.timezone)
        
        # Weekend check
        if now.weekday() >= 5:  # Saturday=5, Sunday=6
            return False
        
        # Regular hours check
        current_time = now.time()
        return self.market_open <= current_time <= self.market_close
    
    def is_extended_hours(self) -> bool:
        """Check if in pre-market (4am-9:30am) or after-hours (4pm-8pm)"""
        now = datetime.now(self.timezone)
        
        if now.weekday() >= 5:
            return False
        
        current_time = now.time()
        
        # Pre-market
        if self.pre_market_open <= current_time < self.market_open:
            return True
        
        # After-hours
        if self.market_close < current_time <= self.after_hours_close:
            return True
        
        return False
    
    def time_until_open(self) -> Optional[str]:
        """Get time remaining until market opens"""
        now = datetime.now(self.timezone)
        
        if self.is_market_open():
            return None
        
        # If weekend, calculate to next Monday
        if now.weekday() >= 5:
            days_until_monday = 7 - now.weekday()
            next_open = now.replace(
                hour=self.market_open.hour,
                minute=self.market_open.minute,
                second=0
            )
            next_open = next_open + timedelta(days=days_until_monday)
        else:
            # Same day or next day
            next_open = now.replace(
                hour=self.market_open.hour,
                minute=self.market_open.minute,
                second=0
            )
            if now.time() > self.market_close:
                next_open = next_open + timedelta(days=1)
        
        time_diff = next_open - now
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if time_diff.days > 0:
            return f"{time_diff.days}d {hours}h {minutes}m"
        return f"{hours}h {minutes}m"
    
    def time_until_close(self) -> Optional[str]:
        """Get time remaining until market closes"""
        if not self.is_market_open():
            return None
        
        now = datetime.now(self.timezone)
        close_time = now.replace(
            hour=self.market_close.hour,
            minute=self.market_close.minute,
            second=0
        )
        
        time_diff = close_time - now
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        return f"{hours}h {minutes}m"
    
    def get_market_status(self) -> Dict[str, any]:
        """Get comprehensive market status"""
        is_open = self.is_market_open()
        is_extended = self.is_extended_hours()
        
        return {
            'is_open': is_open,
            'is_extended_hours': is_extended,
            'is_closed': not is_open and not is_extended,
            'time_until_open': self.time_until_open(),
            'time_until_close': self.time_until_close(),
            'status_text': self._get_status_text(is_open, is_extended)
        }
    
    def _get_status_text(self, is_open: bool, is_extended: bool) -> str:
        """Get human-readable status"""
        if is_open:
            return f"🟢 Mercado ABIERTO - Cierra en {self.time_until_close()}"
        elif is_extended:
            return "🟡 Horario Extendido (Pre-market/After-hours)"
        else:
            time_left = self.time_until_open()
            return f"🔴 Mercado CERRADO - Abre en {time_left}"


from datetime import timedelta
from typing import Optional
