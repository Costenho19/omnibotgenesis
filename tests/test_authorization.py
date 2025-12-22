"""
OMNIX Authorization Tests
==========================
Tests for AuthorizationPort and AuthorizationAdapter.

Tests cover:
- Role assignment from database
- Permission checking
- OWNER vs PREMIUM vs PRO vs BASIC vs FREE roles
- Cache behavior
- Rate limiting
- Fallback to TELEGRAM_ADMIN_ID
"""

import pytest
import os
from unittest.mock import patch, MagicMock

from src.omnix.ports.driven.authorization_port import (
    UserRole,
    Permission,
    UserAuthorization,
    ROLE_PERMISSIONS,
    AuthorizationError,
)
from src.omnix.infrastructure.adapters.authorization_adapter import (
    AuthorizationAdapter,
    get_authorization_adapter,
    reset_authorization_adapter,
    CACHE_TTL_SECONDS,
)


class TestUserRole:
    """Tests for UserRole enum."""
    
    def test_role_hierarchy(self):
        """Verify role hierarchy ordering."""
        assert UserRole.FREE.value < UserRole.BASIC.value
        assert UserRole.BASIC.value < UserRole.PRO.value
        assert UserRole.PRO.value < UserRole.PREMIUM.value
        assert UserRole.PREMIUM.value < UserRole.OWNER.value
    
    def test_owner_is_highest(self):
        """OWNER should be the highest role."""
        assert UserRole.OWNER.value == max(r.value for r in UserRole)


class TestPermissions:
    """Tests for Permission enum and ROLE_PERMISSIONS mapping."""
    
    def test_owner_has_all_permissions(self):
        """OWNER should have all defined permissions."""
        owner_perms = ROLE_PERMISSIONS[UserRole.OWNER]
        assert Permission.REAL_TRADING in owner_perms
        assert Permission.REAL_AUTO_TRADING in owner_perms
        assert Permission.VIEW_REAL_BALANCE in owner_perms
        assert Permission.ADMIN_FUNCTIONS in owner_perms
        assert Permission.DERIVATIVES_TRADING in owner_perms
    
    def test_free_has_limited_permissions(self):
        """FREE should have minimal permissions."""
        free_perms = ROLE_PERMISSIONS[UserRole.FREE]
        assert Permission.READ_MARKET_DATA in free_perms
        assert Permission.BASIC_ANALYSIS in free_perms
        assert Permission.REAL_TRADING not in free_perms
        assert Permission.PAPER_TRADING not in free_perms
    
    def test_premium_cannot_real_trade(self):
        """PREMIUM should not have real trading permission."""
        premium_perms = ROLE_PERMISSIONS[UserRole.PREMIUM]
        assert Permission.REAL_TRADING not in premium_perms
        assert Permission.PAPER_TRADING in premium_perms
        assert Permission.VOICE_RESPONSES in premium_perms
    
    def test_pro_has_paper_trading(self):
        """PRO should have paper trading."""
        pro_perms = ROLE_PERMISSIONS[UserRole.PRO]
        assert Permission.PAPER_TRADING in pro_perms
        assert Permission.PAPER_AUTO_TRADING in pro_perms
        assert Permission.MANAGE_ALERTS in pro_perms
    
    def test_basic_has_limited_paper_trading(self):
        """BASIC should have paper trading but limited features."""
        basic_perms = ROLE_PERMISSIONS[UserRole.BASIC]
        assert Permission.PAPER_TRADING in basic_perms
        assert Permission.ADVANCED_ANALYSIS not in basic_perms


class TestUserAuthorization:
    """Tests for UserAuthorization dataclass."""
    
    def test_default_values(self):
        """Test default authorization values."""
        auth = UserAuthorization(user_id="123")
        assert auth.role == UserRole.FREE
        assert auth.is_owner is False
        assert auth.can_real_trade is False
        assert auth.can_paper_trade is False
    
    def test_owner_authorization(self):
        """Test OWNER authorization."""
        owner_perms = ROLE_PERMISSIONS[UserRole.OWNER]
        auth = UserAuthorization(
            user_id="7014748854",
            role=UserRole.OWNER,
            permissions=owner_perms,
            is_admin=True,
            subscription_tier="owner",
        )
        assert auth.is_owner is True
        assert auth.can_real_trade is True
        assert auth.can_paper_trade is True
    
    def test_has_permission(self):
        """Test has_permission method."""
        auth = UserAuthorization(
            user_id="123",
            permissions={Permission.READ_MARKET_DATA, Permission.BASIC_ANALYSIS}
        )
        assert auth.has_permission(Permission.READ_MARKET_DATA) is True
        assert auth.has_permission(Permission.REAL_TRADING) is False


class TestAuthorizationAdapter:
    """Tests for AuthorizationAdapter."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset adapter singleton before each test."""
        reset_authorization_adapter()
    
    def test_singleton_pattern(self):
        """Test that get_authorization_adapter returns singleton."""
        adapter1 = get_authorization_adapter()
        adapter2 = get_authorization_adapter()
        assert adapter1 is adapter2
    
    def test_admin_fallback(self):
        """Test fallback to TELEGRAM_ADMIN_ID for OWNER detection."""
        with patch.dict(os.environ, {'TELEGRAM_ADMIN_USER_ID': '7014748854'}):
            reset_authorization_adapter()
            adapter = AuthorizationAdapter(
                db_url=None,
                redis_url=None,
                admin_user_id='7014748854'
            )
            assert adapter.is_owner('7014748854') is True
            assert adapter.is_owner('999999999') is False
    
    def test_tier_to_role_conversion(self):
        """Test subscription tier to role conversion."""
        adapter = AuthorizationAdapter(db_url=None, redis_url=None)
        
        assert adapter._tier_to_role('owner', True) == UserRole.OWNER
        assert adapter._tier_to_role('premium', False) == UserRole.PREMIUM
        assert adapter._tier_to_role('pro', False) == UserRole.PRO
        assert adapter._tier_to_role('basic', False) == UserRole.BASIC
        assert adapter._tier_to_role('free', False) == UserRole.FREE
        assert adapter._tier_to_role('unknown', False) == UserRole.FREE
        assert adapter._tier_to_role('', False) == UserRole.FREE
    
    def test_is_admin_overrides_tier(self):
        """Test that is_admin=True always returns OWNER."""
        adapter = AuthorizationAdapter(db_url=None, redis_url=None)
        
        assert adapter._tier_to_role('free', True) == UserRole.OWNER
        assert adapter._tier_to_role('basic', True) == UserRole.OWNER
    
    def test_permissions_for_role(self):
        """Test getting permissions for each role."""
        adapter = AuthorizationAdapter(db_url=None, redis_url=None)
        
        owner_perms = adapter._get_permissions_for_role(UserRole.OWNER)
        assert Permission.REAL_TRADING in owner_perms
        
        free_perms = adapter._get_permissions_for_role(UserRole.FREE)
        assert Permission.REAL_TRADING not in free_perms
    
    def test_cache_key_format(self):
        """Test cache key generation."""
        adapter = AuthorizationAdapter(db_url=None, redis_url=None)
        key = adapter._cache_key("123456")
        assert key == "omnix:auth:123456"
    
    def test_authorization_to_dict(self):
        """Test serialization for cache."""
        adapter = AuthorizationAdapter(db_url=None, redis_url=None)
        auth = UserAuthorization(
            user_id="123",
            role=UserRole.PRO,
            permissions={Permission.PAPER_TRADING, Permission.BASIC_ANALYSIS},
        )
        
        data = adapter._authorization_to_dict(auth)
        assert data['user_id'] == "123"
        assert data['role'] == "PRO"
        assert 'PAPER_TRADING' in data['permissions']
    
    def test_dict_to_authorization(self):
        """Test deserialization from cache."""
        adapter = AuthorizationAdapter(db_url=None, redis_url=None)
        data = {
            'user_id': '123',
            'role': 'PREMIUM',
            'permissions': ['PAPER_TRADING', 'VOICE_RESPONSES'],
            'is_admin': False,
            'subscription_tier': 'premium',
        }
        
        auth = adapter._dict_to_authorization(data)
        assert auth.user_id == "123"
        assert auth.role == UserRole.PREMIUM
        assert Permission.PAPER_TRADING in auth.permissions


class TestAuthorizationError:
    """Tests for AuthorizationError exception."""
    
    def test_error_message(self):
        """Test error message format."""
        error = AuthorizationError("123", Permission.REAL_TRADING)
        assert "123" in str(error)
        assert "REAL_TRADING" in str(error)
    
    def test_custom_message(self):
        """Test custom error message."""
        error = AuthorizationError(
            "123",
            Permission.REAL_TRADING,
            "Custom error message"
        )
        assert str(error) == "Custom error message"


class TestMultiUserIsolation:
    """Tests for multi-user data isolation."""
    
    def test_different_users_different_roles(self):
        """Verify different users get different authorizations."""
        adapter = AuthorizationAdapter(
            db_url=None,
            redis_url=None,
            admin_user_id='7014748854'
        )
        
        owner_auth = adapter.get_authorization('7014748854')
        assert owner_auth.is_owner is True
        
        regular_auth = adapter.get_authorization('999999999')
        assert regular_auth.is_owner is False
        assert regular_auth.role == UserRole.FREE
    
    def test_owner_has_real_trading(self):
        """OWNER should have real trading permission."""
        adapter = AuthorizationAdapter(
            db_url=None,
            redis_url=None,
            admin_user_id='7014748854'
        )
        
        assert adapter.has_permission('7014748854', Permission.REAL_TRADING) is True
        assert adapter.has_permission('999999999', Permission.REAL_TRADING) is False
    
    def test_assert_permission_raises(self):
        """assert_permission should raise for unauthorized users."""
        adapter = AuthorizationAdapter(
            db_url=None,
            redis_url=None,
            admin_user_id='7014748854'
        )
        
        adapter.assert_permission('7014748854', Permission.REAL_TRADING)
        
        with pytest.raises(AuthorizationError):
            adapter.assert_permission('999999999', Permission.REAL_TRADING)


class TestRateLimiting:
    """Tests for rate limiting functionality."""
    
    def test_owner_unlimited(self):
        """OWNER should have unlimited requests."""
        adapter = AuthorizationAdapter(
            db_url=None,
            redis_url=None,
            admin_user_id='7014748854'
        )
        
        for _ in range(100):
            assert adapter.increment_request_count('7014748854') is True
    
    def test_rate_limit_status(self):
        """Test rate limit status response."""
        adapter = AuthorizationAdapter(
            db_url=None,
            redis_url=None,
            admin_user_id='7014748854'
        )
        
        status = adapter.get_rate_limit_status('999999999')
        assert 'used' in status
        assert 'limit' in status
        assert 'remaining' in status
        assert 'reset_at' in status


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
