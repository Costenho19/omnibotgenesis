"""
OMNIX V6.5.4d INSTITUTIONAL+ PREMIUM
=====================================
Test Automático Post-Migración WIN_RATE_OPTIMIZED

Verifica:
1. No hay posiciones huérfanas en símbolos excluidos
2. Solo BTC/USD y XRP/USD son aceptados para trades
3. El perfil WIN_RATE_OPTIMIZED está correctamente configurado
4. SL/TP ratios son correctos (R:R 2.9:1)
5. El intervalo de check es 15s

Migrated from: scripts/test_migration.py
"""
import os
import pytest


ALLOWED_SYMBOLS = ['BTC/USD', 'XRP/USD']
EXCLUDED_SYMBOLS = [
    'SOL/USD', 'ETH/USD', 'DOT/USD', 'AVAX/USD', 
    'LINK/USD', 'ATOM/USD', 'POL/USD', 'ADA/USD', 'LTC/USD'
]


class TestProfileConfiguration:
    """Test WIN_RATE_OPTIMIZED profile configuration."""

    def test_profile_name(self):
        """Verify profile name is correct."""
        from omnix_core.config.trading_profiles import WIN_RATE_OPTIMIZED_PROFILE
        assert WIN_RATE_OPTIMIZED_PROFILE.name == "WIN_RATE_OPTIMIZED"

    def test_stop_loss_percentage(self):
        """Verify stop loss is 1.2%."""
        from omnix_core.config.trading_profiles import WIN_RATE_OPTIMIZED_PROFILE
        assert WIN_RATE_OPTIMIZED_PROFILE.stop_loss_pct == 0.012

    def test_take_profit_percentage(self):
        """Verify take profit is 3.5%."""
        from omnix_core.config.trading_profiles import WIN_RATE_OPTIMIZED_PROFILE
        assert WIN_RATE_OPTIMIZED_PROFILE.take_profit_pct == 0.035

    def test_check_interval(self):
        """Verify check interval is 15 seconds."""
        from omnix_core.config.trading_profiles import WIN_RATE_OPTIMIZED_PROFILE
        assert WIN_RATE_OPTIMIZED_PROFILE.check_interval_seconds == 15

    def test_min_confidence(self):
        """Verify minimum confidence is 0.25."""
        from omnix_core.config.trading_profiles import WIN_RATE_OPTIMIZED_PROFILE
        assert WIN_RATE_OPTIMIZED_PROFILE.min_confidence == 0.25

    def test_risk_reward_ratio(self):
        """Verify R:R ratio is at least 2.5:1."""
        from omnix_core.config.trading_profiles import WIN_RATE_OPTIMIZED_PROFILE
        p = WIN_RATE_OPTIMIZED_PROFILE
        rr_ratio = p.take_profit_pct / p.stop_loss_pct
        assert rr_ratio >= 2.5, f"R:R ratio {rr_ratio:.1f}:1 is below minimum 2.5:1"

    def test_profile_in_registry(self):
        """Verify profile is registered in TRADING_PROFILES."""
        from omnix_core.config.trading_profiles import TRADING_PROFILES
        assert "WIN_RATE_OPTIMIZED" in TRADING_PROFILES


class TestSymbolFilter:
    """Test symbol filtering logic."""

    def test_allowed_symbols_configured(self):
        """Verify allowed symbols are correctly configured."""
        from omnix_core.config.trading_profiles import WIN_RATE_OPTIMIZED_PROFILE
        allowed = WIN_RATE_OPTIMIZED_PROFILE.extra_params.get('allowed_symbols', [])
        assert set(allowed) == set(ALLOWED_SYMBOLS)

    def test_excluded_symbols_configured(self):
        """Verify excluded symbols are correctly configured."""
        from omnix_core.config.trading_profiles import WIN_RATE_OPTIMIZED_PROFILE
        excluded = WIN_RATE_OPTIMIZED_PROFILE.extra_params.get('excluded_symbols', [])
        for symbol in EXCLUDED_SYMBOLS:
            assert symbol in excluded, f"{symbol} should be in excluded list"


@pytest.mark.skipif(
    not os.environ.get('DATABASE_URL'),
    reason="Database not configured"
)
class TestDatabaseIntegrity:
    """Test database integrity for migration."""

    def test_no_orphan_positions(self):
        """Verify no open positions in excluded symbols."""
        import psycopg2
        
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT symbol, COUNT(*) as count
            FROM paper_trading_trades
            WHERE status = 'open'
            GROUP BY symbol
        """)
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        orphans = [
            f"{symbol}: {count}" 
            for symbol, count in rows 
            if symbol in EXCLUDED_SYMBOLS
        ]
        
        assert not orphans, f"Found orphan positions: {orphans}"
