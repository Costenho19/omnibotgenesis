"""
OMNIX V7.0 User Config Adapter
================================
Adapter wrapping legacy database user_settings for hexagonal port interface.

This adapter allows use cases to work with user configuration without
depending directly on omnix_services.database_service implementation.

Delegates to existing user_settings table in PostgreSQL.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from src.omnix.ports.driven.user_config_port import UserConfig, UserConfigPort

logger = logging.getLogger(__name__)


class UserConfigAdapter:
    """
    Adapter for user configuration persistence.
    
    Implements UserConfigPort by delegating to legacy DatabaseService
    and user_settings table.
    
    Provides both sync and async methods for flexibility.
    """
    
    def __init__(self, database_service=None):
        """
        Initialize adapter with optional database service.
        
        Args:
            database_service: Instance of DatabaseService or None for lazy loading
        """
        self._db = database_service
        self._lazy_loaded = False
    
    def _get_db(self):
        """Lazy load database service if not provided."""
        if self._db is None and not self._lazy_loaded:
            try:
                from omnix_services.database_service.database_gateway import DatabaseGateway
                self._db = DatabaseGateway.get_instance()
            except ImportError:
                logger.warning("DatabaseGateway not available")
            except Exception as e:
                logger.error(f"Failed to load DatabaseGateway: {e}")
            self._lazy_loaded = True
        return self._db
    
    def _row_to_config(self, row: tuple, columns: List[str]) -> UserConfig:
        """Convert database row to UserConfig."""
        data = dict(zip(columns, row))
        
        trading_pairs = data.get('trading_pairs')
        if isinstance(trading_pairs, str):
            import json
            try:
                trading_pairs = json.loads(trading_pairs)
            except Exception:
                trading_pairs = None
        
        if not trading_pairs or not isinstance(trading_pairs, list):
            trading_pairs = UserConfig.default_trading_pairs()
        
        return UserConfig(
            user_id=str(data.get('user_id', '')),
            trading_pairs=trading_pairs,
            min_trade_usd=float(data.get('min_trade_usd', 75.0)),
            max_position_pct=float(data.get('max_position_pct', 0.12)),
            stop_loss_pct=float(data.get('stop_loss_pct', 0.02)),
            take_profit_pct=float(data.get('take_profit_pct', 0.05)),
            max_daily_loss_pct=float(data.get('max_daily_loss_pct', 0.08)),
            min_confidence=float(data.get('min_confidence', 0.14)),
            paper_mode=bool(data.get('paper_mode', True)),
            auto_trading=bool(data.get('auto_trading', False)),
            trading_enabled=bool(data.get('trading_enabled', True)),
            initial_balance=float(data.get('initial_balance', 1_000_000.0)),
            language=data.get('language', 'es'),
            timezone=data.get('timezone', 'America/New_York'),
            telegram_username=data.get('telegram_username'),
            telegram_first_name=data.get('telegram_first_name'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
        )
    
    def get_config(self, user_id: str) -> UserConfig:
        """
        Get or create configuration for the given user.
        
        If config doesn't exist, creates one with defaults.
        """
        db = self._get_db()
        if not db:
            logger.warning(f"No database, returning default config for {user_id}")
            return UserConfig(user_id=user_id)
        
        try:
            result = db.execute_query(
                """
                SELECT user_id, trading_pairs, min_trade_usd, max_position_pct,
                       stop_loss_pct, take_profit_pct, max_daily_loss_pct, min_confidence,
                       paper_mode, auto_trading, trading_enabled, initial_balance,
                       language, timezone, telegram_username, telegram_first_name,
                       created_at, updated_at
                FROM user_settings
                WHERE user_id = %s
                LIMIT 1
                """,
                (str(user_id),)
            )
            
            if result and len(result) > 0:
                columns = [
                    'user_id', 'trading_pairs', 'min_trade_usd', 'max_position_pct',
                    'stop_loss_pct', 'take_profit_pct', 'max_daily_loss_pct', 'min_confidence',
                    'paper_mode', 'auto_trading', 'trading_enabled', 'initial_balance',
                    'language', 'timezone', 'telegram_username', 'telegram_first_name',
                    'created_at', 'updated_at'
                ]
                return self._row_to_config(result[0], columns)
            
            config = UserConfig(user_id=user_id, created_at=datetime.utcnow())
            self.save_config(config)
            return config
            
        except Exception as e:
            logger.error(f"Error getting config for {user_id}: {e}")
            return UserConfig(user_id=user_id)
    
    def save_config(self, config: UserConfig) -> bool:
        """Persist user configuration to storage."""
        db = self._get_db()
        if not db:
            return False
        
        try:
            import json
            trading_pairs_json = json.dumps(config.trading_pairs)
            
            db.execute_query(
                """
                INSERT INTO user_settings (
                    user_id, trading_pairs, min_trade_usd, max_position_pct,
                    stop_loss_pct, take_profit_pct, max_daily_loss_pct, min_confidence,
                    paper_mode, auto_trading, trading_enabled, initial_balance,
                    language, timezone, telegram_username, telegram_first_name,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (user_id) DO UPDATE SET
                    trading_pairs = EXCLUDED.trading_pairs,
                    min_trade_usd = EXCLUDED.min_trade_usd,
                    max_position_pct = EXCLUDED.max_position_pct,
                    stop_loss_pct = EXCLUDED.stop_loss_pct,
                    take_profit_pct = EXCLUDED.take_profit_pct,
                    max_daily_loss_pct = EXCLUDED.max_daily_loss_pct,
                    min_confidence = EXCLUDED.min_confidence,
                    paper_mode = EXCLUDED.paper_mode,
                    auto_trading = EXCLUDED.auto_trading,
                    trading_enabled = EXCLUDED.trading_enabled,
                    initial_balance = EXCLUDED.initial_balance,
                    language = EXCLUDED.language,
                    timezone = EXCLUDED.timezone,
                    telegram_username = EXCLUDED.telegram_username,
                    telegram_first_name = EXCLUDED.telegram_first_name,
                    updated_at = NOW()
                """,
                (
                    str(config.user_id),
                    trading_pairs_json,
                    config.min_trade_usd,
                    config.max_position_pct,
                    config.stop_loss_pct,
                    config.take_profit_pct,
                    config.max_daily_loss_pct,
                    config.min_confidence,
                    config.paper_mode,
                    config.auto_trading,
                    config.trading_enabled,
                    config.initial_balance,
                    config.language,
                    config.timezone,
                    config.telegram_username,
                    config.telegram_first_name,
                    config.created_at or datetime.utcnow(),
                ),
                fetch=False
            )
            logger.info(f"Saved config for user {config.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving config for {config.user_id}: {e}")
            return False
    
    def update_config(
        self, 
        user_id: str, 
        updates: Dict[str, Any]
    ) -> Optional[UserConfig]:
        """Partial update of user configuration."""
        config = self.get_config(user_id)
        
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        config.updated_at = datetime.utcnow()
        
        if self.save_config(config):
            return config
        return None
    
    def delete_config(self, user_id: str) -> bool:
        """Remove a user's configuration from storage."""
        db = self._get_db()
        if not db:
            return False
        
        try:
            db.execute_query(
                "DELETE FROM user_settings WHERE user_id = %s",
                (str(user_id),),
                fetch=False
            )
            logger.info(f"Deleted config for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting config for {user_id}: {e}")
            return False
    
    def get_users_with_auto_trading(self) -> List[UserConfig]:
        """Get all users who have auto_trading enabled."""
        db = self._get_db()
        if not db:
            return []
        
        try:
            result = db.execute_query(
                """
                SELECT user_id, trading_pairs, min_trade_usd, max_position_pct,
                       stop_loss_pct, take_profit_pct, max_daily_loss_pct, min_confidence,
                       paper_mode, auto_trading, trading_enabled, initial_balance,
                       language, timezone, telegram_username, telegram_first_name,
                       created_at, updated_at
                FROM user_settings
                WHERE auto_trading = true AND trading_enabled = true
                """
            )
            
            if not result:
                return []
            
            columns = [
                'user_id', 'trading_pairs', 'min_trade_usd', 'max_position_pct',
                'stop_loss_pct', 'take_profit_pct', 'max_daily_loss_pct', 'min_confidence',
                'paper_mode', 'auto_trading', 'trading_enabled', 'initial_balance',
                'language', 'timezone', 'telegram_username', 'telegram_first_name',
                'created_at', 'updated_at'
            ]
            
            return [self._row_to_config(row, columns) for row in result]
            
        except Exception as e:
            logger.error(f"Error getting users with auto_trading: {e}")
            return []
    
    def set_auto_trading(self, user_id: str, enabled: bool) -> bool:
        """Toggle auto-trading for a user."""
        db = self._get_db()
        if not db:
            return False
        
        try:
            db.execute_query(
                """
                UPDATE user_settings 
                SET auto_trading = %s, updated_at = NOW()
                WHERE user_id = %s
                """,
                (enabled, str(user_id)),
                fetch=False
            )
            logger.info(f"Set auto_trading={enabled} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error setting auto_trading for {user_id}: {e}")
            return False
    
    def exists(self, user_id: str) -> bool:
        """Check if configuration exists for user."""
        db = self._get_db()
        if not db:
            return False
        
        try:
            result = db.execute_query(
                "SELECT 1 FROM user_settings WHERE user_id = %s LIMIT 1",
                (str(user_id),)
            )
            return bool(result and len(result) > 0)
        except Exception as e:
            logger.error(f"Error checking config existence for {user_id}: {e}")
            return False


_adapter_instance: Optional[UserConfigAdapter] = None


def get_user_config_adapter() -> UserConfigAdapter:
    """Get or create the singleton UserConfigAdapter instance."""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = UserConfigAdapter()
    return _adapter_instance
