"""
OMNIX V6.5.4d - Shadow Portfolio Runner

Daily job that calculates counterfactual outcomes for vetoed trades.
Determines: "Would this trade have won if executed?"

Created: Jan 9, 2026
Purpose: Learning Engine - Filter Calibration via Counterfactual Analysis

USAGE:
    python -m omnix_services.database_service.shadow_portfolio_runner

    Or programmatically:
        from omnix_services.database_service.shadow_portfolio_runner import ShadowPortfolioRunner
        runner = ShadowPortfolioRunner()
        runner.run_analysis()

SCHEDULE:
    Run daily via Railway cron or manually for immediate analysis.
    Analyzes shadow events >= 24h old by default.
"""

import logging
import os
import sys
import argparse
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple
from decimal import Decimal
import requests
import time

logger = logging.getLogger("OMNIX.ShadowRunner")

KRAKEN_INTERVALS = {
    '1h': 60,
    '4h': 240,
    '24h': 1440,
    '7d': 10080,
}

KRAKEN_SYMBOL_MAP = {
    'BTC': 'XXBTZUSD',
    'ETH': 'XETHZUSD',
    'SOL': 'SOLUSD',
    'XRP': 'XXRPZUSD',
    'DOGE': 'XDGUSD',
    'ADA': 'ADAUSD',
    'AVAX': 'AVAXUSD',
    'DOT': 'DOTUSD',
    'LINK': 'LINKUSD',
    'MATIC': 'MATICUSD',
    'ATOM': 'ATOMUSD',
    'UNI': 'UNIUSD',
    'LTC': 'XLTCZUSD',
}


class HistoricalPriceFetcher:
    """
    Fetches historical price data from Kraken public API.
    Used to determine counterfactual outcomes of vetoed trades.
    """
    
    def __init__(self, cache_ttl_seconds: int = 300):
        self._cache: Dict[str, Tuple[float, List[Dict]]] = {}
        self._cache_ttl = cache_ttl_seconds
    
    def get_price_at_time(
        self,
        symbol: str,
        target_time: datetime,
        tolerance_minutes: int = 30
    ) -> Optional[float]:
        """
        Get historical price at a specific time.
        
        Args:
            symbol: Crypto symbol (BTC, ETH, etc.)
            target_time: When we need the price
            tolerance_minutes: Acceptable range from target
            
        Returns:
            Price at target time or None if unavailable
        """
        try:
            candles = self._fetch_hourly_candles(symbol, target_time, hours_back=48)
            if not candles:
                return None
            
            target_ts = target_time.timestamp()
            
            for candle in sorted(candles, key=lambda c: abs(c['timestamp'] - target_ts)):
                time_diff_min = abs(candle['timestamp'] - target_ts) / 60
                if time_diff_min <= tolerance_minutes:
                    return candle['close']
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting price at time for {symbol}: {e}")
            return None
    
    def get_prices_after_veto(
        self,
        symbol: str,
        veto_time: datetime,
        entry_price: float
    ) -> Dict[str, Optional[float]]:
        """
        Get prices at multiple horizons after a veto.
        
        Args:
            symbol: Crypto symbol
            veto_time: When trade was vetoed
            entry_price: Price at veto time
            
        Returns:
            Dict with price_1h, price_4h, price_24h, price_7d, price_30d
        """
        prices: Dict[str, Optional[float]] = {
            '1h': None,
            '4h': None,
            '24h': None,
            '7d': None,
            '30d': None
        }
        
        horizons = [
            ('1h', timedelta(hours=1)),
            ('4h', timedelta(hours=4)),
            ('24h', timedelta(hours=24)),
            ('7d', timedelta(days=7)),
            ('30d', timedelta(days=30)),
        ]
        
        for key, delta in horizons:
            target_time = veto_time + delta
            
            if target_time > datetime.now(timezone.utc):
                continue
            
            price = self.get_price_at_time(symbol, target_time, tolerance_minutes=60)
            prices[key] = price
        
        return prices
    
    def _fetch_hourly_candles(
        self,
        symbol: str,
        around_time: datetime,
        hours_back: int = 48
    ) -> List[Dict]:
        """
        Fetch hourly OHLC candles from Kraken.
        
        Args:
            symbol: Crypto symbol
            around_time: Center time for data fetch
            hours_back: How far back to fetch
            
        Returns:
            List of candle dicts with timestamp, open, high, low, close, volume
        """
        cache_key = f"{symbol}_{around_time.date()}"
        
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if time.time() - cached_time < self._cache_ttl:
                return cached_data
        
        kraken_pair = KRAKEN_SYMBOL_MAP.get(symbol.upper())
        if not kraken_pair:
            kraken_pair = f"{symbol.upper()}USD"
        
        since = int((around_time - timedelta(hours=hours_back)).timestamp())
        
        url = f"https://api.kraken.com/0/public/OHLC?pair={kraken_pair}&interval=60&since={since}"
        
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if data.get('error') and len(data['error']) > 0:
                logger.warning(f"Kraken API error: {data['error']}")
                return []
            
            result_keys = [k for k in data.get('result', {}).keys() if k != 'last']
            if not result_keys:
                return []
            
            ohlc_data = data['result'][result_keys[0]]
            
            candles = []
            for candle in ohlc_data:
                candles.append({
                    'timestamp': int(candle[0]),
                    'open': float(candle[1]),
                    'high': float(candle[2]),
                    'low': float(candle[3]),
                    'close': float(candle[4]),
                    'volume': float(candle[6])
                })
            
            self._cache[cache_key] = (time.time(), candles)
            
            return candles
            
        except Exception as e:
            logger.error(f"Error fetching Kraken candles for {symbol}: {e}")
            return []


class CounterfactualAnalyzer:
    """
    Analyzes what would have happened if a vetoed trade was executed.
    """
    
    def calculate_outcome(
        self,
        intended_action: str,
        entry_price: float,
        prices_after: Dict[str, Optional[float]],
        intended_stop_loss: Optional[float] = None,
        intended_take_profit: Optional[float] = None,
        position_size_usd: float = 1000.0
    ) -> Dict[str, Any]:
        """
        Calculate counterfactual outcome for a vetoed trade.
        
        Args:
            intended_action: 'BUY' or 'SELL'
            entry_price: Price when trade was vetoed
            prices_after: Dict with prices at 1h, 4h, 24h, 7d, 30d
            intended_stop_loss: Stop loss price if known
            intended_take_profit: Take profit price if known
            position_size_usd: Position size for P&L calculation
            
        Returns:
            Dict with would_have_won, counterfactual_pnl, max_drawdown, max_favorable, verdict
        """
        if intended_action not in ('BUY', 'SELL'):
            return self._unknown_action_result()
        
        pnl = {}
        max_adverse = 0.0
        max_favorable = 0.0
        would_have_won = False
        
        for horizon, price in prices_after.items():
            if price is None:
                pnl[horizon] = None
                continue
            
            if intended_action == 'BUY':
                pnl_pct = (price - entry_price) / entry_price * 100
            else:
                pnl_pct = (entry_price - price) / entry_price * 100
            
            pnl[horizon] = round(pnl_pct, 4)
            
            if pnl_pct > max_favorable:
                max_favorable = pnl_pct
            if pnl_pct < max_adverse:
                max_adverse = pnl_pct
        
        primary_pnl = pnl.get('24h') or pnl.get('4h') or pnl.get('1h')
        if primary_pnl is not None:
            would_have_won = primary_pnl > 1.0
        
        veto_was_correct, verdict_reason = self._determine_veto_correctness(
            intended_action=intended_action,
            entry_price=entry_price,
            prices_after=prices_after,
            pnl=pnl,
            max_adverse=max_adverse,
            max_favorable=max_favorable,
            stop_loss=intended_stop_loss,
            take_profit=intended_take_profit
        )
        
        return {
            'would_have_won': would_have_won,
            'counterfactual_pnl': pnl,
            'max_drawdown_pct': abs(max_adverse),
            'max_favorable_pct': max_favorable,
            'veto_was_correct': veto_was_correct,
            'verdict_reason': verdict_reason
        }
    
    def _determine_veto_correctness(
        self,
        intended_action: str,
        entry_price: float,
        prices_after: Dict[str, Optional[float]],
        pnl: Dict[str, Optional[float]],
        max_adverse: float,
        max_favorable: float,
        stop_loss: Optional[float],
        take_profit: Optional[float]
    ) -> Tuple[bool, str]:
        """
        Determine if the veto was correct based on what would have happened.
        
        Veto is CORRECT if:
        - Trade would have hit stop loss before take profit
        - Trade would have lost > 2% in 24h
        - Max drawdown > 5%
        
        Veto is INCORRECT if:
        - Trade would have won > 3% in 24h
        - Trade would have hit take profit
        """
        pnl_24h = pnl.get('24h')
        
        if pnl_24h is None:
            pnl_4h = pnl.get('4h')
            pnl_1h = pnl.get('1h')
            
            if pnl_4h is not None:
                if pnl_4h < -1.5:
                    return True, f"4h P&L {pnl_4h:.2f}% - trade would have lost"
                elif pnl_4h > 2.0:
                    return False, f"4h P&L {pnl_4h:.2f}% - veto blocked profitable trade"
            
            if pnl_1h is not None:
                if pnl_1h < -1.0:
                    return True, f"1h P&L {pnl_1h:.2f}% - early loss indicates correct veto"
                elif pnl_1h > 1.5:
                    return False, f"1h P&L {pnl_1h:.2f}% - veto blocked quick profit"
            
            return True, "Insufficient data - defaulting to veto correct (conservative)"
        
        if pnl_24h < -2.0:
            return True, f"24h P&L {pnl_24h:.2f}% - veto protected from loss"
        
        if max_adverse < -5.0:
            return True, f"Max drawdown {abs(max_adverse):.2f}% - veto protected from significant loss"
        
        if stop_loss and intended_action == 'BUY':
            stop_pct = (stop_loss - entry_price) / entry_price * 100
            if max_adverse <= stop_pct:
                return True, f"Would have hit stop loss ({stop_pct:.2f}%)"
        
        if pnl_24h > 3.0:
            return False, f"24h P&L {pnl_24h:.2f}% - veto blocked highly profitable trade"
        
        if pnl_24h > 1.5:
            return False, f"24h P&L {pnl_24h:.2f}% - veto blocked profitable trade"
        
        if max_favorable > 3.0 and pnl_24h > 0:
            return False, f"Max favorable {max_favorable:.2f}% with positive close - missed profit opportunity"
        
        if abs(pnl_24h) < 1.0:
            return True, f"24h P&L {pnl_24h:.2f}% - marginal trade, veto was reasonable"
        
        return True, f"24h P&L {pnl_24h:.2f}% - inconclusive, defaulting to veto correct"
    
    def _unknown_action_result(self) -> Dict[str, Any]:
        """Result when action is unknown/cannot be analyzed."""
        return {
            'would_have_won': None,
            'counterfactual_pnl': {},
            'max_drawdown_pct': 0.0,
            'max_favorable_pct': 0.0,
            'veto_was_correct': True,
            'verdict_reason': "Unknown action - cannot analyze counterfactual"
        }


class ShadowPortfolioRunner:
    """
    Main runner that orchestrates counterfactual analysis for shadow trades.
    
    Pipeline:
    1. Fetch pending shadow events from database
    2. For each event, get historical prices after veto time
    3. Calculate counterfactual outcome (would have won/lost)
    4. Persist results to shadow_trade_outcomes table
    5. Update filter_calibration_metrics
    """
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize the runner.
        
        Args:
            dry_run: If True, analyze but don't persist results
        """
        self.dry_run = dry_run
        self.price_fetcher = HistoricalPriceFetcher()
        self.analyzer = CounterfactualAnalyzer()
        self._repository = None
    
    @property
    def repository(self):
        """Lazy load repository."""
        if self._repository is None:
            from omnix_services.database_service.shadow_portfolio_repository import (
                get_shadow_portfolio_repository
            )
            self._repository = get_shadow_portfolio_repository()
        return self._repository
    
    def run_analysis(
        self,
        min_age_hours: int = 24,
        max_events: int = 100,
        symbol_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run counterfactual analysis on pending shadow events.
        
        Args:
            min_age_hours: Only analyze events older than this
            max_events: Maximum events to process in one run
            symbol_filter: Only analyze specific symbol (optional)
            
        Returns:
            Summary of analysis results
        """
        logger.info(f"🔍 Starting Shadow Portfolio analysis (min_age={min_age_hours}h, max={max_events}, dry_run={self.dry_run})")
        
        if not self.repository:
            logger.error("Repository not available - check DATABASE_URL")
            return {'error': 'Repository unavailable', 'analyzed': 0}
        
        pending = self.repository.get_pending_outcomes(
            min_age_hours=min_age_hours,
            limit=max_events
        )
        
        if not pending:
            logger.info("📭 No pending shadow events to analyze")
            return {
                'analyzed': 0,
                'correct_vetoes': 0,
                'incorrect_vetoes': 0,
                'errors': 0
            }
        
        logger.info(f"📊 Found {len(pending)} shadow events to analyze")
        
        results = {
            'analyzed': 0,
            'correct_vetoes': 0,
            'incorrect_vetoes': 0,
            'unknown_action': 0,
            'errors': 0,
            'by_veto_type': {}
        }
        
        for event in pending:
            try:
                if symbol_filter and event['symbol'] != symbol_filter:
                    continue
                
                outcome = self._analyze_event(event)
                
                if outcome:
                    results['analyzed'] += 1
                    
                    if outcome.get('veto_was_correct') is True:
                        results['correct_vetoes'] += 1
                    elif outcome.get('veto_was_correct') is False:
                        results['incorrect_vetoes'] += 1
                    else:
                        results['unknown_action'] += 1
                    
                    veto_type = event.get('veto_type', 'UNKNOWN')
                    if veto_type not in results['by_veto_type']:
                        results['by_veto_type'][veto_type] = {
                            'total': 0, 'correct': 0, 'incorrect': 0
                        }
                    results['by_veto_type'][veto_type]['total'] += 1
                    if outcome.get('veto_was_correct'):
                        results['by_veto_type'][veto_type]['correct'] += 1
                    else:
                        results['by_veto_type'][veto_type]['incorrect'] += 1
                    
                    if not self.dry_run:
                        self._persist_outcome(event, outcome)
                else:
                    results['errors'] += 1
                    
            except Exception as e:
                logger.error(f"Error analyzing event {event.get('id')}: {e}")
                results['errors'] += 1
        
        accuracy = 0
        if results['analyzed'] > 0:
            accuracy = results['correct_vetoes'] / results['analyzed'] * 100
        
        logger.info(
            f"✅ Analysis complete: {results['analyzed']} analyzed, "
            f"{results['correct_vetoes']} correct vetoes ({accuracy:.1f}% accuracy), "
            f"{results['incorrect_vetoes']} incorrect, {results['errors']} errors"
        )
        
        return results
    
    def _analyze_event(self, event: Dict) -> Optional[Dict]:
        """
        Analyze a single shadow event.
        
        Args:
            event: Shadow event dict from get_pending_outcomes()
            
        Returns:
            Outcome dict or None if analysis failed
        """
        event_id = event.get('id')
        symbol = event.get('symbol', 'BTC')
        
        symbol_clean = symbol.replace('/USD', '').replace('USD', '').upper()
        
        veto_time_raw = event.get('created_at')
        if veto_time_raw is None:
            logger.warning(f"Event {event_id} missing created_at - skipping")
            return None
        
        if isinstance(veto_time_raw, str):
            veto_time = datetime.fromisoformat(veto_time_raw.replace('Z', '+00:00'))
        else:
            veto_time = veto_time_raw
        
        entry_price = event.get('intended_entry_price')
        intended_action = event.get('intended_action', 'UNKNOWN')
        
        if not entry_price:
            logger.warning(f"Event {event_id} missing entry price - skipping")
            return None
        
        logger.debug(f"Analyzing event {event_id}: {symbol_clean} {intended_action} @ {entry_price}")
        
        prices_after = self.price_fetcher.get_prices_after_veto(
            symbol=symbol_clean,
            veto_time=veto_time,
            entry_price=entry_price
        )
        
        if all(p is None for p in prices_after.values()):
            logger.warning(f"No price data available for event {event_id}")
            return None
        
        outcome = self.analyzer.calculate_outcome(
            intended_action=intended_action,
            entry_price=entry_price,
            prices_after=prices_after,
            intended_stop_loss=event.get('intended_stop_loss'),
            intended_take_profit=event.get('intended_take_profit'),
        )
        
        outcome['prices_after'] = prices_after
        outcome['entry_price'] = entry_price
        
        return outcome
    
    def _persist_outcome(self, event: Dict, outcome: Dict) -> bool:
        """
        Persist outcome to database.
        
        Args:
            event: Original shadow event
            outcome: Calculated outcome
            
        Returns:
            True if persisted successfully
        """
        if not self.repository:
            return False
        
        prices = outcome.get('prices_after', {})
        pnl = outcome.get('counterfactual_pnl', {})
        
        return self.repository.update_outcome(
            event_id=event['id'],
            price_at_veto=outcome.get('entry_price', 0),
            prices={
                '1h': prices.get('1h'),
                '4h': prices.get('4h'),
                '24h': prices.get('24h'),
                '7d': prices.get('7d'),
                '30d': prices.get('30d'),
            },
            would_have_won=outcome.get('would_have_won', False),
            counterfactual_pnl={
                '1h': pnl.get('1h'),
                '4h': pnl.get('4h'),
                '24h': pnl.get('24h'),
                '7d': pnl.get('7d'),
                '30d': pnl.get('30d'),
            },
            max_drawdown_pct=outcome.get('max_drawdown_pct', 0),
            max_favorable_pct=outcome.get('max_favorable_pct', 0),
            veto_was_correct=outcome.get('veto_was_correct', True),
            verdict_reason=outcome.get('verdict_reason', '')
        )


def main():
    """CLI entrypoint for Shadow Portfolio Runner."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(
        description='OMNIX Shadow Portfolio Runner - Counterfactual Analysis'
    )
    parser.add_argument(
        '--min-age',
        type=int,
        default=24,
        help='Minimum age of events to analyze (hours, default: 24)'
    )
    parser.add_argument(
        '--max-events',
        type=int,
        default=100,
        help='Maximum events to process (default: 100)'
    )
    parser.add_argument(
        '--symbol',
        type=str,
        default=None,
        help='Only analyze specific symbol (e.g., BTC)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Analyze but do not persist results'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger("OMNIX").setLevel(logging.DEBUG)
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║       OMNIX Shadow Portfolio Runner - Counterfactual         ║
║              Learning Engine Analysis Job                    ║
╠══════════════════════════════════════════════════════════════╣
║  Min Age:     {args.min_age:>5}h                                       ║
║  Max Events:  {args.max_events:>5}                                         ║
║  Symbol:      {(args.symbol or 'ALL'):>5}                                         ║
║  Dry Run:     {'Yes' if args.dry_run else 'No':>5}                                         ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    runner = ShadowPortfolioRunner(dry_run=args.dry_run)
    results = runner.run_analysis(
        min_age_hours=args.min_age,
        max_events=args.max_events,
        symbol_filter=args.symbol
    )
    
    print("\n📊 Results Summary:")
    print(f"   Analyzed:        {results.get('analyzed', 0)}")
    print(f"   Correct Vetoes:  {results.get('correct_vetoes', 0)}")
    print(f"   Incorrect Vetoes:{results.get('incorrect_vetoes', 0)}")
    print(f"   Unknown Action:  {results.get('unknown_action', 0)}")
    print(f"   Errors:          {results.get('errors', 0)}")
    
    if results.get('by_veto_type'):
        print("\n   By Veto Type:")
        for vtype, stats in results['by_veto_type'].items():
            acc = stats['correct'] / stats['total'] * 100 if stats['total'] > 0 else 0
            print(f"     {vtype}: {stats['total']} total, {acc:.1f}% accuracy")
    
    if results.get('analyzed', 0) > 0:
        accuracy = results['correct_vetoes'] / results['analyzed'] * 100
        print(f"\n   Overall Accuracy: {accuracy:.1f}%")
        
        if accuracy < 60:
            print("\n   ⚠️  Low accuracy suggests filters may be too conservative.")
            print("       Review LOOSEN recommendations in calibration dashboard.")
    
    return 0 if results.get('errors', 0) == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
