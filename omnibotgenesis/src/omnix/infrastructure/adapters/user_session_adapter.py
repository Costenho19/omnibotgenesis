"""
OMNIX V7.0 User Session Adapter
=================================
Adapter wrapping legacy UserSessionManager for hexagonal port interface.

This adapter allows use cases to work with sessions without
depending directly on omnix_core.sessions implementation.
"""

import asyncio
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

from src.omnix.ports.driven.user_session_port import UserSession, UserSessionPort

_executor = ThreadPoolExecutor(max_workers=2)


async def _run_sync(func, *args, **kwargs):
    """Run a synchronous function in executor for async context."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, lambda: func(*args, **kwargs))


class UserSessionAdapter:
    """
    Adapter for legacy UserSessionManager.
    
    Implements UserSessionPort by delegating to legacy implementation.
    Provides both sync and async methods for flexibility.
    """
    
    def __init__(self, legacy_manager=None):
        """
        Initialize adapter with optional legacy manager.
        
        Args:
            legacy_manager: Instance of UserSessionManager or None for lazy loading
        """
        self._legacy = legacy_manager
        self._lazy_loaded = False
    
    def _get_legacy(self):
        """Lazy load legacy manager if not provided."""
        if self._legacy is None and not self._lazy_loaded:
            try:
                from omnix_core.sessions.user_session_manager import get_session_manager
                self._legacy = get_session_manager()
            except ImportError:
                pass
            except Exception:
                pass
            self._lazy_loaded = True
        return self._legacy
    
    def _convert_to_port_session(self, legacy_session) -> UserSession:
        """Convert legacy UserTradingSession to port UserSession."""
        return UserSession(
            user_id=getattr(legacy_session, 'user_id', ''),
            status=getattr(legacy_session, 'status', 'inactive'),
            running=getattr(legacy_session, 'running', False),
            paused=getattr(legacy_session, 'paused', False),
            emergency_stop=getattr(legacy_session, 'emergency_stop', False),
            total_trades=getattr(legacy_session, 'total_trades', 0),
            winning_trades=getattr(legacy_session, 'winning_trades', 0),
            losing_trades=getattr(legacy_session, 'losing_trades', 0),
            total_profit_loss=getattr(legacy_session, 'total_profit_loss', 0.0),
            daily_profit_loss=getattr(legacy_session, 'daily_profit_loss', 0.0),
            paper_balance=getattr(legacy_session, 'paper_balance', 1_000_000.0),
            paper_positions=getattr(legacy_session, 'paper_positions', None) or {},
            initial_balance=getattr(legacy_session, 'initial_balance', 1_000_000.0),
            last_trade_time=getattr(legacy_session, 'last_trade_time', None),
            last_activity=getattr(legacy_session, 'last_activity', None),
            start_time=getattr(legacy_session, 'start_time', None),
            trading_pairs=getattr(legacy_session, 'trading_pairs', None) or [],
            min_trade_usd=getattr(legacy_session, 'min_trade_usd', 75.0),
            max_position_pct=getattr(legacy_session, 'max_position_pct', 0.12),
            stop_loss_pct=getattr(legacy_session, 'stop_loss_pct', 0.02),
            max_daily_loss_pct=getattr(legacy_session, 'max_daily_loss_pct', 0.08),
            min_confidence=getattr(legacy_session, 'min_confidence', 0.14),
            created_at=getattr(legacy_session, 'created_at', None),
            updated_at=getattr(legacy_session, 'updated_at', None),
            config_snapshot=getattr(legacy_session, 'config_snapshot', None),
        )
    
    def _copy_to_legacy_session(self, port_session: UserSession, legacy_session):
        """Copy port UserSession fields to legacy UserTradingSession with proper handling."""
        from datetime import datetime
        import copy
        
        legacy_session.status = port_session.status
        legacy_session.running = port_session.running
        legacy_session.paused = port_session.paused
        legacy_session.emergency_stop = port_session.emergency_stop
        legacy_session.total_trades = port_session.total_trades
        legacy_session.winning_trades = port_session.winning_trades
        legacy_session.losing_trades = port_session.losing_trades
        legacy_session.total_profit_loss = port_session.total_profit_loss
        legacy_session.daily_profit_loss = port_session.daily_profit_loss
        legacy_session.paper_balance = port_session.paper_balance
        
        if port_session.paper_positions:
            legacy_session.paper_positions = copy.deepcopy(port_session.paper_positions)
        
        legacy_session.initial_balance = port_session.initial_balance
        legacy_session.last_trade_time = port_session.last_trade_time
        legacy_session.last_activity = port_session.last_activity
        
        if hasattr(legacy_session, 'start_time'):
            legacy_session.start_time = port_session.start_time
        
        if port_session.trading_pairs:
            legacy_session.trading_pairs = list(port_session.trading_pairs)
        
        legacy_session.min_trade_usd = port_session.min_trade_usd
        legacy_session.max_position_pct = port_session.max_position_pct
        legacy_session.stop_loss_pct = port_session.stop_loss_pct
        legacy_session.max_daily_loss_pct = port_session.max_daily_loss_pct
        legacy_session.min_confidence = port_session.min_confidence
        
        if port_session.config_snapshot:
            legacy_session.config_snapshot = copy.deepcopy(port_session.config_snapshot)
        
        if port_session.created_at:
            legacy_session.created_at = port_session.created_at
        legacy_session.updated_at = datetime.utcnow().isoformat()
    
    def get_session(self, user_id: str) -> UserSession:
        """Get or create a session for the given user."""
        legacy = self._get_legacy()
        if legacy is None:
            return UserSession(user_id=user_id)
        
        legacy_session = legacy.get_session(user_id)
        return self._convert_to_port_session(legacy_session)
    
    async def get_session_async(self, user_id: str) -> UserSession:
        """Async version of get_session."""
        return await _run_sync(self.get_session, user_id)
    
    def save_session(self, session: UserSession) -> bool:
        """Persist session to storage."""
        legacy = self._get_legacy()
        if legacy is None:
            return False
        
        try:
            legacy_session = legacy.get_session(session.user_id)
            self._copy_to_legacy_session(session, legacy_session)
            legacy.save_session(legacy_session)
            return True
        except Exception:
            return False
    
    async def save_session_async(self, session: UserSession) -> bool:
        """Async version of save_session."""
        return await _run_sync(self.save_session, session)
    
    def get_active_sessions(self) -> List[UserSession]:
        """Get all sessions where running=True."""
        legacy = self._get_legacy()
        if legacy is None:
            return []
        
        try:
            active_entries = legacy.get_active_sessions()
            sessions = []
            for entry in active_entries:
                if isinstance(entry, str):
                    legacy_session = legacy.get_session(entry)
                    sessions.append(self._convert_to_port_session(legacy_session))
                elif isinstance(entry, dict):
                    try:
                        from omnix_core.sessions.user_session_manager import UserTradingSession
                        legacy_session = UserTradingSession.from_dict(entry)
                        sessions.append(self._convert_to_port_session(legacy_session))
                    except Exception:
                        user_id = entry.get('user_id', '')
                        if user_id:
                            legacy_session = legacy.get_session(user_id)
                            sessions.append(self._convert_to_port_session(legacy_session))
                else:
                    sessions.append(self._convert_to_port_session(entry))
            return sessions
        except Exception:
            return []
    
    async def get_active_sessions_async(self) -> List[UserSession]:
        """Async version of get_active_sessions."""
        return await _run_sync(self.get_active_sessions)
    
    def set_emergency_stop(self, user_id: str, stop: bool = True) -> bool:
        """Toggle emergency stop for a user."""
        legacy = self._get_legacy()
        if legacy is None:
            return False
        
        try:
            session = legacy.get_session(user_id)
            session.emergency_stop = stop
            legacy.save_session(session)
            return True
        except Exception:
            return False
    
    def pause_session(self, user_id: str, paused: bool = True) -> bool:
        """Pause or resume a user's trading session."""
        legacy = self._get_legacy()
        if legacy is None:
            return False
        
        try:
            session = legacy.get_session(user_id)
            session.paused = paused
            legacy.save_session(session)
            return True
        except Exception:
            return False
    
    def delete_session(self, user_id: str) -> bool:
        """Remove a user's session from storage."""
        legacy = self._get_legacy()
        if legacy is None:
            return False
        
        try:
            if hasattr(legacy, 'delete_session'):
                legacy.delete_session(user_id)
                return True
            return False
        except Exception:
            return False
    
    def is_available(self) -> bool:
        """Check if the legacy manager is available."""
        return self._get_legacy() is not None
