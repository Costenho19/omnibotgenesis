"""
Tests for Shadow Portfolio Runner - Counterfactual Analysis

Tests the counterfactual logic that determines if vetoed trades
would have been profitable.

Created: Jan 9, 2026
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock


class TestCounterfactualAnalyzer:
    """Tests for counterfactual outcome calculation."""
    
    def test_buy_trade_would_have_won(self):
        """BUY trade with price increase >1% should show would_have_won=True."""
        from omnix_services.database_service.shadow_portfolio_runner import CounterfactualAnalyzer
        
        analyzer = CounterfactualAnalyzer()
        
        result = analyzer.calculate_outcome(
            intended_action='BUY',
            entry_price=100.0,
            prices_after={
                '1h': 101.0,
                '4h': 103.0,
                '24h': 105.0,
                '7d': None,
                '30d': None
            }
        )
        
        assert result['would_have_won'] is True
        assert result['counterfactual_pnl']['24h'] == pytest.approx(5.0, rel=0.01)
        assert result['veto_was_correct'] is False
    
    def test_buy_trade_would_have_lost(self):
        """BUY trade with price decrease should show would_have_won=False."""
        from omnix_services.database_service.shadow_portfolio_runner import CounterfactualAnalyzer
        
        analyzer = CounterfactualAnalyzer()
        
        result = analyzer.calculate_outcome(
            intended_action='BUY',
            entry_price=100.0,
            prices_after={
                '1h': 99.0,
                '4h': 97.0,
                '24h': 95.0,
                '7d': None,
                '30d': None
            }
        )
        
        assert result['would_have_won'] is False
        assert result['counterfactual_pnl']['24h'] == pytest.approx(-5.0, rel=0.01)
        assert result['veto_was_correct'] is True
    
    def test_sell_trade_would_have_won(self):
        """SELL trade with price decrease should show would_have_won=True."""
        from omnix_services.database_service.shadow_portfolio_runner import CounterfactualAnalyzer
        
        analyzer = CounterfactualAnalyzer()
        
        result = analyzer.calculate_outcome(
            intended_action='SELL',
            entry_price=100.0,
            prices_after={
                '1h': 99.0,
                '4h': 97.0,
                '24h': 95.0,
                '7d': None,
                '30d': None
            }
        )
        
        assert result['would_have_won'] is True
        assert result['counterfactual_pnl']['24h'] == pytest.approx(5.0, rel=0.01)
        assert result['veto_was_correct'] is False
    
    def test_sell_trade_would_have_lost(self):
        """SELL trade with price increase should show would_have_won=False."""
        from omnix_services.database_service.shadow_portfolio_runner import CounterfactualAnalyzer
        
        analyzer = CounterfactualAnalyzer()
        
        result = analyzer.calculate_outcome(
            intended_action='SELL',
            entry_price=100.0,
            prices_after={
                '1h': 101.0,
                '4h': 103.0,
                '24h': 105.0,
                '7d': None,
                '30d': None
            }
        )
        
        assert result['would_have_won'] is False
        assert result['counterfactual_pnl']['24h'] == pytest.approx(-5.0, rel=0.01)
        assert result['veto_was_correct'] is True
    
    def test_unknown_action_defaults_to_correct(self):
        """UNKNOWN action should default to veto_was_correct=True."""
        from omnix_services.database_service.shadow_portfolio_runner import CounterfactualAnalyzer
        
        analyzer = CounterfactualAnalyzer()
        
        result = analyzer.calculate_outcome(
            intended_action='UNKNOWN',
            entry_price=100.0,
            prices_after={'24h': 110.0}
        )
        
        assert result['would_have_won'] is None
        assert result['veto_was_correct'] is True
        assert 'Unknown action' in result['verdict_reason']
    
    def test_max_drawdown_triggers_correct_veto(self):
        """Large drawdown should mark veto as correct even if final P&L positive."""
        from omnix_services.database_service.shadow_portfolio_runner import CounterfactualAnalyzer
        
        analyzer = CounterfactualAnalyzer()
        
        result = analyzer.calculate_outcome(
            intended_action='BUY',
            entry_price=100.0,
            prices_after={
                '1h': 93.0,
                '4h': 95.0,
                '24h': 101.0,
                '7d': None,
                '30d': None
            }
        )
        
        assert result['max_drawdown_pct'] == pytest.approx(7.0, rel=0.01)
        assert result['veto_was_correct'] is True
        assert 'drawdown' in result['verdict_reason'].lower()
    
    def test_highly_profitable_marks_incorrect_veto(self):
        """Very profitable trade (>3%) should mark veto as incorrect."""
        from omnix_services.database_service.shadow_portfolio_runner import CounterfactualAnalyzer
        
        analyzer = CounterfactualAnalyzer()
        
        result = analyzer.calculate_outcome(
            intended_action='BUY',
            entry_price=100.0,
            prices_after={
                '1h': 102.0,
                '4h': 104.0,
                '24h': 108.0,
                '7d': None,
                '30d': None
            }
        )
        
        assert result['counterfactual_pnl']['24h'] == pytest.approx(8.0, rel=0.01)
        assert result['veto_was_correct'] is False
        assert 'highly profitable' in result['verdict_reason'].lower()
    
    def test_marginal_trade_defaults_to_correct_veto(self):
        """P&L < 1% should mark veto as correct (marginal trade)."""
        from omnix_services.database_service.shadow_portfolio_runner import CounterfactualAnalyzer
        
        analyzer = CounterfactualAnalyzer()
        
        result = analyzer.calculate_outcome(
            intended_action='BUY',
            entry_price=100.0,
            prices_after={
                '1h': 100.2,
                '4h': 100.3,
                '24h': 100.8,
                '7d': None,
                '30d': None
            }
        )
        
        assert abs(result['counterfactual_pnl']['24h']) < 1.0
        assert result['veto_was_correct'] is True
        assert 'marginal' in result['verdict_reason'].lower()


class TestHistoricalPriceFetcher:
    """Tests for historical price fetching (mocked)."""
    
    def test_price_fetcher_initialization(self):
        """Price fetcher should initialize with cache."""
        from omnix_services.database_service.shadow_portfolio_runner import HistoricalPriceFetcher
        
        fetcher = HistoricalPriceFetcher(cache_ttl_seconds=300)
        assert fetcher._cache == {}
        assert fetcher._cache_ttl == 300
    
    @patch('omnix_services.database_service.shadow_portfolio_runner.requests.get')
    def test_fetch_returns_candles(self, mock_get):
        """Fetcher should parse Kraken OHLC response correctly."""
        from omnix_services.database_service.shadow_portfolio_runner import HistoricalPriceFetcher
        
        mock_response = Mock()
        mock_response.json.return_value = {
            'error': [],
            'result': {
                'XXBTZUSD': [
                    [1700000000, '50000.0', '50100.0', '49900.0', '50050.0', '0', '100.5', 50],
                    [1700003600, '50050.0', '50200.0', '50000.0', '50150.0', '0', '150.2', 75],
                ]
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        fetcher = HistoricalPriceFetcher()
        candles = fetcher._fetch_hourly_candles('BTC', datetime.utcnow())
        
        assert len(candles) == 2
        assert candles[0]['close'] == 50050.0
        assert candles[1]['close'] == 50150.0


class TestShadowPortfolioRunner:
    """Tests for the main runner orchestration."""
    
    def test_runner_dry_run_mode(self):
        """Runner in dry_run mode should not persist results."""
        from omnix_services.database_service.shadow_portfolio_runner import ShadowPortfolioRunner
        
        runner = ShadowPortfolioRunner(dry_run=True)
        assert runner.dry_run is True
    
    def test_runner_analyze_event_missing_entry_price(self):
        """Events without entry_price should be skipped."""
        from omnix_services.database_service.shadow_portfolio_runner import ShadowPortfolioRunner
        
        runner = ShadowPortfolioRunner(dry_run=True)
        
        event = {
            'id': 1,
            'symbol': 'BTC',
            'created_at': datetime.utcnow() - timedelta(days=2),
            'intended_entry_price': None,
            'intended_action': 'BUY'
        }
        
        result = runner._analyze_event(event)
        assert result is None
    
    def test_runner_analyze_event_missing_created_at(self):
        """Events without created_at should be skipped."""
        from omnix_services.database_service.shadow_portfolio_runner import ShadowPortfolioRunner
        
        runner = ShadowPortfolioRunner(dry_run=True)
        
        event = {
            'id': 1,
            'symbol': 'BTC',
            'created_at': None,
            'intended_entry_price': 50000.0,
            'intended_action': 'BUY'
        }
        
        result = runner._analyze_event(event)
        assert result is None
    
    @patch.object(__import__('omnix_services.database_service.shadow_portfolio_runner', fromlist=['HistoricalPriceFetcher']).HistoricalPriceFetcher, 'get_prices_after_veto')
    def test_runner_analyze_event_with_prices(self, mock_get_prices):
        """Runner should calculate outcome when prices are available."""
        from omnix_services.database_service.shadow_portfolio_runner import ShadowPortfolioRunner
        
        mock_get_prices.return_value = {
            '1h': 51000.0,
            '4h': 52000.0,
            '24h': 53000.0,
            '7d': None,
            '30d': None
        }
        
        runner = ShadowPortfolioRunner(dry_run=True)
        runner.price_fetcher.get_prices_after_veto = mock_get_prices
        
        event = {
            'id': 1,
            'symbol': 'BTC/USD',
            'created_at': datetime.utcnow() - timedelta(days=2),
            'intended_entry_price': 50000.0,
            'intended_action': 'BUY'
        }
        
        result = runner._analyze_event(event)
        
        assert result is not None
        assert result['would_have_won'] is True
        assert result['veto_was_correct'] is False


class TestVetoCorrectnessLogic:
    """Detailed tests for veto correctness determination."""
    
    def test_loss_greater_than_2pct_is_correct_veto(self):
        """24h loss > 2% should be marked as correct veto."""
        from omnix_services.database_service.shadow_portfolio_runner import CounterfactualAnalyzer
        
        analyzer = CounterfactualAnalyzer()
        
        result = analyzer.calculate_outcome(
            intended_action='BUY',
            entry_price=100.0,
            prices_after={'1h': 99.0, '4h': 98.0, '24h': 97.5, '7d': None, '30d': None}
        )
        
        assert result['veto_was_correct'] is True
        assert 'protected from loss' in result['verdict_reason'].lower()
    
    def test_gain_greater_than_3pct_is_incorrect_veto(self):
        """24h gain > 3% should be marked as incorrect veto."""
        from omnix_services.database_service.shadow_portfolio_runner import CounterfactualAnalyzer
        
        analyzer = CounterfactualAnalyzer()
        
        result = analyzer.calculate_outcome(
            intended_action='BUY',
            entry_price=100.0,
            prices_after={'1h': 101.0, '4h': 102.0, '24h': 103.5, '7d': None, '30d': None}
        )
        
        assert result['veto_was_correct'] is False
        assert 'profitable' in result['verdict_reason'].lower()
    
    def test_fallback_to_4h_when_24h_missing(self):
        """Should use 4h P&L when 24h not available."""
        from omnix_services.database_service.shadow_portfolio_runner import CounterfactualAnalyzer
        
        analyzer = CounterfactualAnalyzer()
        
        result = analyzer.calculate_outcome(
            intended_action='BUY',
            entry_price=100.0,
            prices_after={'1h': 99.0, '4h': 97.0, '24h': None, '7d': None, '30d': None}
        )
        
        assert result['veto_was_correct'] is True
        assert '4h' in result['verdict_reason']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
