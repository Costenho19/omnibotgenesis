"""
📢 OMNIX Notifications Module V6.4 PREMIUM
"""

from .trade_notification_service import TradeNotificationService

try:
    from .daily_summary_service import DailySummaryService
except ImportError:
    DailySummaryService = None

__all__ = ['TradeNotificationService', 'DailySummaryService']
