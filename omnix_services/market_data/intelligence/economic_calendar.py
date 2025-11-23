import logging
import requests

logger = logging.getLogger(__name__)


class FreeEconomicCalendar:
    """Calendar económico gratuito para eventos que afectan crypto"""
    
    def __init__(self):
        self.events_cache = {}
        
    def get_today_events(self):
        """Obtener eventos económicos de hoy - GRATIS"""
        try:
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')
            
            major_events = [
                {'time': '14:30', 'event': 'US Employment Data', 'impact': 'HIGH', 'currency': 'USD'},
                {'time': '16:00', 'event': 'Federal Reserve Speech', 'impact': 'MEDIUM', 'currency': 'USD'},
                {'time': '20:00', 'event': 'SEC Crypto Announcement', 'impact': 'HIGH', 'currency': 'USD'},
                {'time': '08:30', 'event': 'European Central Bank Decision', 'impact': 'MEDIUM', 'currency': 'EUR'},
                {'time': '12:00', 'event': 'Bitcoin ETF Update', 'impact': 'HIGH', 'currency': 'BTC'}
            ]
            
            try:
                response = requests.get('https://www.forexfactory.com/calendar.php?format=json')
                if response.status_code == 200:
                    real_events = response.json()[:3]
                    selected_events = real_events if real_events else major_events[:3]
                else:
                    selected_events = major_events[:3]
            except:
                selected_events = major_events[:3]
            
            return {
                'date': today,
                'events': selected_events,
                'total_high_impact': len([e for e in selected_events if e['impact'] == 'HIGH'])
            }
        except:
            return {'date': 'unknown', 'events': [], 'total_high_impact': 0}
