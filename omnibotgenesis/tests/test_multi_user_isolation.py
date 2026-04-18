"""
OMNIX V6.5.4d - Multi-User Isolation Tests

Phase 2 Step 8: Validates that different users have isolated sessions
and that data does not leak between users.

Test Categories:
1. Session Isolation - Different users have separate sessions
2. Data Isolation - One user's trades don't affect another
3. Concurrent Access - Multiple users can operate simultaneously
4. Persistence - Sessions survive restarts
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from omnix_core.sessions.user_session_manager import (
    UserSessionManager,
    UserTradingSession,
    SessionStatus
)


class TestUserTradingSession:
    """Tests for UserTradingSession dataclass"""
    
    def test_session_creation_with_defaults(self):
        """Each user gets unique session with default values"""
        session = UserTradingSession(user_id="12345")
        
        assert session.user_id == "12345"
        assert session.running == False
        assert session.paper_balance == 1_000_000.0
        assert session.total_trades == 0
        assert session.winning_trades == 0
        assert session.total_profit_loss == 0.0
    
    def test_session_isolation_different_users(self):
        """Two different users have completely separate sessions"""
        user_a = UserTradingSession(user_id="USER_A")
        user_b = UserTradingSession(user_id="USER_B")
        
        user_a.paper_balance = 500_000.0
        user_a.total_trades = 10
        user_a.winning_trades = 7
        user_a.running = True
        
        assert user_b.paper_balance == 1_000_000.0
        assert user_b.total_trades == 0
        assert user_b.winning_trades == 0
        assert user_b.running == False
        assert user_a.user_id != user_b.user_id
    
    def test_session_serialization(self):
        """Session can be serialized and deserialized"""
        original = UserTradingSession(
            user_id="SERIALIZE_TEST",
            paper_balance=750_000.0,
            total_trades=5,
            running=True
        )
        
        data = original.to_dict()
        restored = UserTradingSession.from_dict(data)
        
        assert restored.user_id == "SERIALIZE_TEST"
        assert restored.paper_balance == 750_000.0
        assert restored.total_trades == 5
        assert restored.running == True
    
    def test_update_stats_winning_trade(self):
        """Stats update correctly for winning trade"""
        session = UserTradingSession(user_id="STATS_TEST")
        
        session.update_stats({'profit_loss': 500.0})
        
        assert session.total_trades == 1
        assert session.winning_trades == 1
        assert session.losing_trades == 0
        assert session.total_profit_loss == 500.0
    
    def test_update_stats_losing_trade(self):
        """Stats update correctly for losing trade"""
        session = UserTradingSession(user_id="STATS_TEST")
        
        session.update_stats({'profit_loss': -200.0})
        
        assert session.total_trades == 1
        assert session.winning_trades == 0
        assert session.losing_trades == 1
        assert session.total_profit_loss == -200.0
    
    def test_win_rate_calculation(self):
        """Win rate calculates correctly"""
        session = UserTradingSession(user_id="WIN_RATE_TEST")
        session.total_trades = 10
        session.winning_trades = 6
        
        assert session.win_rate == 60.0
    
    def test_win_rate_zero_trades(self):
        """Win rate is 0 when no trades"""
        session = UserTradingSession(user_id="ZERO_TRADES")
        
        assert session.win_rate == 0.0


class TestUserSessionManager:
    """Tests for UserSessionManager multi-user isolation"""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        mock = MagicMock()
        mock.get.return_value = None
        mock.setex.return_value = True
        mock.sadd.return_value = 1
        mock.srem.return_value = 1
        mock.smembers.return_value = set()
        return mock
    
    @pytest.fixture
    def mock_redis_cache(self, mock_redis):
        """Mock Redis cache wrapper"""
        cache = MagicMock()
        cache.client = mock_redis
        return cache
    
    @pytest.fixture
    def mock_database(self):
        """Mock database service"""
        db = MagicMock()
        db.execute_query.return_value = []
        return db
    
    @pytest.fixture
    def session_manager(self, mock_redis_cache, mock_database):
        """Create session manager with mocked dependencies"""
        return UserSessionManager(
            redis_cache=mock_redis_cache,
            database_service=mock_database
        )
    
    def test_get_session_creates_new(self, session_manager):
        """Getting session for new user creates fresh session"""
        session = session_manager.get_session("NEW_USER_123")
        
        assert session.user_id == "NEW_USER_123"
        assert session.running == False
        assert session.paper_balance == 1_000_000.0
    
    def test_get_session_isolation(self, session_manager):
        """Different users get different isolated sessions"""
        session_a = session_manager.get_session("USER_ALPHA")
        session_b = session_manager.get_session("USER_BETA")
        
        session_a.paper_balance = 800_000.0
        session_a.running = True
        
        fresh_b = session_manager.get_session("USER_BETA")
        assert fresh_b.paper_balance == 1_000_000.0
        assert fresh_b.running == False
    
    def test_save_session_persists_changes(self, session_manager):
        """Saving session persists to local cache"""
        session = session_manager.get_session("PERSIST_TEST")
        session.paper_balance = 950_000.0
        session.total_trades = 3
        
        session_manager.save_session(session)
        
        retrieved = session_manager.get_session("PERSIST_TEST")
        assert retrieved.paper_balance == 950_000.0
        assert retrieved.total_trades == 3
    
    def test_multiple_users_concurrent_sessions(self, session_manager):
        """Multiple users can have active sessions simultaneously"""
        users = ["USER_1", "USER_2", "USER_3", "USER_4", "USER_5"]
        sessions = {}
        
        for i, user_id in enumerate(users):
            session = session_manager.get_session(user_id)
            session.paper_balance = 1_000_000.0 - (i * 10000)
            session.running = True
            session_manager.save_session(session)
            sessions[user_id] = session
        
        for i, user_id in enumerate(users):
            retrieved = session_manager.get_session(user_id)
            expected_balance = 1_000_000.0 - (i * 10000)
            assert retrieved.paper_balance == expected_balance
            assert retrieved.running == True
    
    def test_session_stats_isolated_between_users(self, session_manager):
        """Trade stats are isolated between users"""
        trader_a = session_manager.get_session("TRADER_A")
        trader_b = session_manager.get_session("TRADER_B")
        
        trader_a.update_stats({'profit_loss': 1000.0})
        trader_a.update_stats({'profit_loss': 500.0})
        trader_a.update_stats({'profit_loss': -200.0})
        session_manager.save_session(trader_a)
        
        trader_b.update_stats({'profit_loss': -100.0})
        session_manager.save_session(trader_b)
        
        assert trader_a.total_trades == 3
        assert trader_a.winning_trades == 2
        assert trader_a.total_profit_loss == 1300.0
        
        assert trader_b.total_trades == 1
        assert trader_b.winning_trades == 0
        assert trader_b.total_profit_loss == -100.0
    
    def test_redis_key_generation(self, session_manager):
        """Redis keys are unique per user"""
        key_a = session_manager._redis_key("USER_A")
        key_b = session_manager._redis_key("USER_B")
        
        assert key_a == "omnix:session:USER_A"
        assert key_b == "omnix:session:USER_B"
        assert key_a != key_b


class TestSessionDataIsolation:
    """Deep isolation tests - ensure no data leakage"""
    
    def test_paper_positions_isolation(self):
        """Paper positions are isolated between users"""
        user_a = UserTradingSession(user_id="POSITIONS_A")
        user_b = UserTradingSession(user_id="POSITIONS_B")
        
        user_a.paper_positions = {
            "BTC/USD": {"amount": 0.5, "avg_price": 50000.0}
        }
        
        assert user_b.paper_positions == {}
        assert "BTC/USD" not in user_b.paper_positions
    
    def test_trading_pairs_isolation(self):
        """Trading pairs can be customized per user"""
        user_a = UserTradingSession(user_id="PAIRS_A")
        user_b = UserTradingSession(user_id="PAIRS_B")
        
        user_a.trading_pairs = ["BTC/USD", "ETH/USD"]
        
        assert len(user_b.trading_pairs) == 11
        assert user_a.trading_pairs != user_b.trading_pairs
    
    def test_risk_parameters_isolation(self):
        """Risk parameters are isolated per user"""
        conservative = UserTradingSession(user_id="CONSERVATIVE")
        aggressive = UserTradingSession(user_id="AGGRESSIVE")
        
        conservative.max_position_pct = 0.05
        conservative.stop_loss_pct = 0.01
        
        aggressive.max_position_pct = 0.25
        aggressive.stop_loss_pct = 0.05
        
        assert conservative.max_position_pct != aggressive.max_position_pct
        assert conservative.stop_loss_pct != aggressive.stop_loss_pct


class TestLegacyCompatibility:
    """Tests for backward compatibility with legacy single-user mode"""
    
    def test_legacy_user_session_works(self):
        """Legacy user ID continues to work"""
        LEGACY_USER_ID = "7014748854"
        session = UserTradingSession(user_id=LEGACY_USER_ID)
        
        assert session.user_id == LEGACY_USER_ID
        assert session.paper_balance == 1_000_000.0
    
    def test_string_user_id_normalization(self):
        """User IDs are normalized to strings"""
        manager = UserSessionManager(redis_cache=None, database_service=None)
        
        session_str = manager.get_session("12345")
        session_int = manager.get_session(12345)
        
        assert session_str.user_id == "12345"
        assert session_int.user_id == "12345"
        assert session_str.user_id == session_int.user_id


class TestPersistenceIsolation:
    """Tests for persistence across restarts and cache boundaries"""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client with storage"""
        mock = MagicMock()
        mock._storage = {}
        
        def mock_get(key):
            return mock._storage.get(key)
        
        def mock_setex(key, ttl, value):
            mock._storage[key] = value
            return True
        
        mock.get = mock_get
        mock.setex = mock_setex
        mock.sadd.return_value = 1
        mock.srem.return_value = 1
        return mock
    
    @pytest.fixture
    def mock_redis_cache(self, mock_redis):
        cache = MagicMock()
        cache.client = mock_redis
        return cache
    
    def test_session_survives_cache_clear(self, mock_redis_cache, mock_redis):
        """Session persists to Redis and survives local cache clear"""
        manager = UserSessionManager(redis_cache=mock_redis_cache, database_service=None)
        
        session = manager.get_session("PERSIST_USER")
        session.paper_balance = 850_000.0
        session.total_trades = 5
        session.running = True
        manager.save_session(session)
        
        manager._local_sessions.clear()
        
        reloaded = manager.get_session("PERSIST_USER")
        
        assert reloaded.user_id == "PERSIST_USER"
        assert reloaded.paper_balance == 850_000.0
        assert reloaded.total_trades == 5
        assert reloaded.running == True
    
    def test_no_data_leak_between_users_via_redis(self, mock_redis_cache, mock_redis):
        """User A's data cannot be read by User B even with cache clear"""
        manager = UserSessionManager(redis_cache=mock_redis_cache, database_service=None)
        
        session_a = manager.get_session("USER_ALPHA")
        session_a.paper_balance = 500_000.0
        session_a.paper_positions = {"BTC/USD": {"amount": 1.0}}
        manager.save_session(session_a)
        
        session_b = manager.get_session("USER_BETA")
        session_b.paper_balance = 1_200_000.0
        manager.save_session(session_b)
        
        manager._local_sessions.clear()
        
        reloaded_a = manager.get_session("USER_ALPHA")
        reloaded_b = manager.get_session("USER_BETA")
        
        assert reloaded_a.paper_balance == 500_000.0
        assert reloaded_b.paper_balance == 1_200_000.0
        assert "BTC/USD" in reloaded_a.paper_positions
        assert reloaded_b.paper_positions == {}
    
    def test_redis_key_isolation(self, mock_redis_cache, mock_redis):
        """Each user's data is stored under a unique Redis key"""
        manager = UserSessionManager(redis_cache=mock_redis_cache, database_service=None)
        
        session_x = manager.get_session("USER_X")
        session_x.paper_balance = 100_000.0
        manager.save_session(session_x)
        
        session_y = manager.get_session("USER_Y")
        session_y.paper_balance = 200_000.0
        manager.save_session(session_y)
        
        assert "omnix:session:USER_X" in mock_redis._storage
        assert "omnix:session:USER_Y" in mock_redis._storage
        
        import json
        data_x = json.loads(mock_redis._storage["omnix:session:USER_X"])
        data_y = json.loads(mock_redis._storage["omnix:session:USER_Y"])
        
        assert data_x["user_id"] == "USER_X"
        assert data_y["user_id"] == "USER_Y"
        assert data_x["paper_balance"] == 100_000.0
        assert data_y["paper_balance"] == 200_000.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
