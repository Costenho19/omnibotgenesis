"""
OMNIX V5.1 ENTERPRISE - Trading Service Orchestrator
Coordina todos los módulos de trading: Kraken API, Monte Carlo, Black Swan, PQC
"""

from typing import Dict, Any, Optional, List
from omnix_config.settings import settings
from omnix_core.utils.logger import get_logger
from omnix_core.cache.redis_cache import cache_result

from .kraken_client import KrakenAPIClient
from .monte_carlo import MonteCarloSimulator
from .black_swan import BlackSwanDetector
from omnix_core.security.pqc_security import PostQuantumSecurity
from .kraken_websocket import get_kraken_websocket
from .backtesting_engine import BacktestingEngine

logger = get_logger(__name__)


class TradingServiceEnterprise:
    """
    Enterprise Trading Service Orchestrator
    
    Integrates:
    - Kraken API for real trading
    - Monte Carlo simulations for risk analysis
    - Black Swan detection for extreme events
    - Post-Quantum Cryptography for security
    - Risk Management System (RMS) V6.0 integration
    
    Scalable to 100K+ users
    """
    
    def __init__(self):
        logger.info("🚀 Initializing Trading Service Enterprise...")
        
        # RMS Integration (set externally after initialization)
        self.limits_engine = None
        self.circuit_breaker = None
        self.alert_dispatcher = None
        self.rms_enabled = False
        
        # Initialize all sub-modules
        self.kraken = KrakenAPIClient()
        self.monte_carlo = MonteCarloSimulator(num_simulations=10000)
        self.black_swan = BlackSwanDetector()
        self.pqc = PostQuantumSecurity()
        
        # WebSocket para real-time feeds (escalable a 100K+ usuarios)
        try:
            self.ws = get_kraken_websocket()
            logger.info("🌐 WebSocket Real-Time enabled - Latency <500ms")
        except Exception as e:
            logger.warning(f"⚠️ WebSocket not available: {e}")
            self.ws = None
        
        # Backtesting Engine para validar estrategias
        try:
            self.backtesting = BacktestingEngine(kraken_client=self.kraken)
            logger.info("📈 Backtesting Engine enabled - Validate strategies with real data")
        except Exception as e:
            logger.warning(f"⚠️ Backtesting not available: {e}")
            self.backtesting = None
        
        # Verify Kraken connection
        if self.kraken.health_check():
            logger.info("✅ Kraken API connection verified")
        else:
            logger.warning("⚠️ Kraken API not accessible")
        
        logger.info("✅ Trading Service Enterprise initialized successfully")
    
    def configure_rms(self, limits_engine=None, circuit_breaker=None, alert_dispatcher=None) -> None:
        """
        Configure Risk Management System integration.
        
        Args:
            limits_engine: LimitsEngine instance for pre-trade validation
            circuit_breaker: CircuitBreaker instance for halt control
            alert_dispatcher: AlertDispatcher for risk notifications
        """
        self.limits_engine = limits_engine
        self.circuit_breaker = circuit_breaker
        self.alert_dispatcher = alert_dispatcher
        self.rms_enabled = limits_engine is not None or circuit_breaker is not None
        
        if self.rms_enabled:
            logger.info("🛡️ TradingService: RMS integration configured")
            if limits_engine:
                logger.info("   ✅ LimitsEngine: Pre-trade validation active")
            if circuit_breaker:
                logger.info("   ✅ CircuitBreaker: Halt protection active")
            if alert_dispatcher:
                logger.info("   ✅ AlertDispatcher: Risk notifications active")
    
    def _validate_rms(self, user_id: str, pair: str, side: str, amount: float, price: Optional[float] = None) -> Dict[str, Any]:
        """
        Validate trade against RMS before execution.
        
        Returns:
            Dict with 'approved', 'reason', and 'warnings'
        """
        import time
        import json
        from datetime import datetime
        
        validation_id = f"RMS_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        start_time = time.time()
        
        result = {'approved': True, 'reason': None, 'warnings': [], 'validation_id': validation_id}
        
        if not self.rms_enabled:
            return result
        
        # Check Circuit Breaker first
        cb_start = time.time()
        if self.circuit_breaker and self.circuit_breaker.is_trading_halted(user_id):
            cb_latency = (time.time() - cb_start) * 1000
            result['approved'] = False
            result['reason'] = 'Trading halted by Circuit Breaker'
            logger.warning(json.dumps({
                "event": "RMS_VALIDATION_REJECTED",
                "validation_id": validation_id,
                "user_id": user_id,
                "pair": pair,
                "side": side,
                "reason": "circuit_breaker_active",
                "cb_check_latency_ms": round(cb_latency, 2),
                "timestamp": datetime.utcnow().isoformat()
            }))
            return result
        cb_latency = (time.time() - cb_start) * 1000
        
        # Validate with LimitsEngine
        limits_latency = 0
        if self.limits_engine:
            limits_start = time.time()
            try:
                trade_value = amount * (price or 1.0)
                validation = self.limits_engine.validate_trade(
                    user_id=user_id,
                    symbol=pair,
                    side=side,
                    quantity=amount,
                    price=price or 0,
                    trade_value=trade_value
                )
                limits_latency = (time.time() - limits_start) * 1000
                
                if not validation.get('approved', True):
                    result['approved'] = False
                    result['reason'] = validation.get('reason', 'Trade rejected by LimitsEngine')
                    logger.warning(json.dumps({
                        "event": "RMS_VALIDATION_REJECTED",
                        "validation_id": validation_id,
                        "user_id": user_id,
                        "pair": pair,
                        "side": side,
                        "amount": amount,
                        "reason": result['reason'],
                        "limits_check_latency_ms": round(limits_latency, 2),
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                
                if validation.get('warnings'):
                    result['warnings'] = validation['warnings']
                    
            except Exception as e:
                limits_latency = (time.time() - limits_start) * 1000
                logger.error(f"⚠️ RMS validation error: {e}")
                result['warnings'].append(f"RMS validation failed: {e}")
        
        total_latency = (time.time() - start_time) * 1000
        
        # Log sync verification with timing
        if total_latency > 100:  # Alert if RMS validation takes >100ms
            logger.warning(json.dumps({
                "event": "RMS_SYNC_LATENCY_WARNING",
                "validation_id": validation_id,
                "user_id": user_id,
                "pair": pair,
                "total_latency_ms": round(total_latency, 2),
                "cb_latency_ms": round(cb_latency, 2),
                "limits_latency_ms": round(limits_latency, 2),
                "threshold_ms": 100,
                "timestamp": datetime.utcnow().isoformat()
            }))
        else:
            logger.debug(json.dumps({
                "event": "RMS_VALIDATION_COMPLETE",
                "validation_id": validation_id,
                "approved": result['approved'],
                "total_latency_ms": round(total_latency, 2),
                "timestamp": datetime.utcnow().isoformat()
            }))
        
        return result
    
    def get_account_status(self) -> Dict[str, Any]:
        """Get comprehensive account status"""
        try:
            balance = self.kraken.get_balance()
            
            # Calculate total USD value
            total_usd = balance.get('ZUSD', 0.0) if isinstance(balance.get('ZUSD'), (int, float)) else float(balance.get('ZUSD', '0'))
            
            return {
                'balance': balance,
                'total_usd': total_usd,
                'currencies': list(balance.keys()),
                'pqc_enabled': self.pqc.pqc_enabled
            }
        except Exception as e:
            logger.error(f"Failed to get account status: {e}")
            return {}
    
    def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current ticker data for a trading pair.
        
        FIXED Nov 30, 2025: Método faltante - PaperTradingManager necesita
        este método para obtener precios de mercado.
        
        Args:
            symbol: Trading pair (e.g., 'BTC', 'XBTUSD')
            
        Returns:
            Ticker data with 'last' price
        """
        try:
            pair = symbol
            if symbol in ['BTC', 'XBT']:
                pair = 'XBTUSD'
            elif symbol == 'ETH':
                pair = 'ETHUSD'
            elif symbol == 'SOL':
                pair = 'SOLUSD'
            elif not symbol.endswith('USD'):
                pair = f"{symbol}USD"
            
            ticker = self.kraken.get_ticker(pair)
            
            if ticker and 'c' in ticker:
                return {
                    'last': float(ticker['c'][0]),
                    'high': float(ticker['h'][1]) if 'h' in ticker else None,
                    'low': float(ticker['l'][1]) if 'l' in ticker else None,
                    'bid': float(ticker['b'][0]) if 'b' in ticker else None,
                    'ask': float(ticker['a'][0]) if 'a' in ticker else None,
                    'volume': float(ticker['v'][1]) if 'v' in ticker else None,
                    'pair': pair
                }
            
            return ticker
            
        except Exception as e:
            logger.error(f"❌ Error getting ticker for {symbol}: {e}")
            return None
    
    def analyze_trading_opportunity(
        self,
        pair: str = 'XBTUSD',
        investment_amount: float = 100.0
    ) -> Dict[str, Any]:
        """
        Comprehensive trading opportunity analysis
        
        Args:
            pair: Trading pair
            investment_amount: Amount to invest in USD
            
        Returns:
            Complete analysis including Monte Carlo and Black Swan
        """
        try:
            # Get current market data
            ticker = self.kraken.get_ticker(pair)
            
            if not ticker:
                return {'error': 'Failed to fetch market data'}
            
            current_price = float(ticker['c'][0]) if 'c' in ticker else 0
            
            if current_price == 0:
                return {'error': 'Invalid price data'}
            
            # Get historical data (simplified - in production use OHLC endpoint)
            # For now, estimate volatility from bid-ask spread
            bid = float(ticker['b'][0]) if 'b' in ticker else current_price
            ask = float(ticker['a'][0]) if 'a' in ticker else current_price
            spread = (ask - bid) / current_price
            estimated_volatility = max(0.4, spread * 100)  # Rough estimate
            
            # Monte Carlo simulation
            monte_carlo_result = self.monte_carlo.simulate(
                current_price=current_price,
                volatility=estimated_volatility,
                drift=0.0,
                days=30
            )
            
            # Position sizing
            account_status = self.get_account_status()
            account_balance = account_status.get('total_usd', 100.0)
            
            position_sizing = self.monte_carlo.calculate_optimal_position_size(
                current_price=current_price,
                volatility=estimated_volatility,
                account_balance=account_balance,
                risk_tolerance=0.02
            )
            
            # Black Swan analysis with REAL historical data from Kraken
            ohlc_data = self.kraken.get_ohlc(pair=pair, interval=60)  # 1-hour candles
            
            if len(ohlc_data) >= 30:
                # Extract close prices from OHLC data
                historical_prices = [float(candle[4]) for candle in ohlc_data[-100:]]  # Last 100 candles
                black_swan_result = self.black_swan.analyze(historical_prices)
                logger.info(f"✅ Black Swan analysis with {len(historical_prices)} real data points")
            else:
                logger.warning("⚠️ Insufficient OHLC data for Black Swan analysis")
                black_swan_result = {'detected': False, 'reason': 'insufficient_data'}
            
            analysis = {
                'pair': pair,
                'current_price': current_price,
                'market_data': {
                    'bid': bid,
                    'ask': ask,
                    'spread_pct': spread * 100,
                    'volume_24h': ticker.get('v', [0])[1] if 'v' in ticker else 0
                },
                'monte_carlo': monte_carlo_result,
                'position_sizing': position_sizing,
                'black_swan': black_swan_result,
                'recommendation': self._generate_recommendation(
                    monte_carlo_result,
                    black_swan_result,
                    position_sizing
                )
            }
            
            logger.info(f"✅ Trading analysis complete for {pair}")
            return analysis
            
        except Exception as e:
            logger.error(f"Trading analysis error: {e}")
            return {'error': str(e)}
    
    def execute_trade(
        self,
        pair: str,
        side: str,
        amount: float,
        order_type: str = 'market',
        price: Optional[float] = None,
        user_id: str = 'system'
    ) -> Dict[str, Any]:
        """
        Execute trade with PQC signature and RMS validation
        
        Args:
            pair: Trading pair
            side: 'buy' or 'sell'
            amount: Amount in base currency
            order_type: 'market' or 'limit'
            price: Limit price (required for limit orders)
            user_id: User ID for RMS validation
        """
        try:
            # 🛡️ RMS PRE-TRADE VALIDATION
            if self.rms_enabled:
                rms_check = self._validate_rms(
                    user_id=user_id,
                    pair=pair,
                    side=side,
                    amount=amount,
                    price=price
                )
                
                if not rms_check['approved']:
                    logger.warning(f"🛑 Trade BLOCKED by RMS: {rms_check['reason']}")
                    return {
                        'success': False,
                        'error': f"RMS Rejection: {rms_check['reason']}",
                        'rms_blocked': True
                    }
                
                if rms_check['warnings']:
                    for warning in rms_check['warnings']:
                        logger.warning(f"⚠️ RMS Warning: {warning}")
            
            # Prepare order data
            order_data = {
                'pair': pair,
                'side': side,
                'amount': amount,
                'type': order_type,
                'price': price,
                'timestamp': __import__('time').time()
            }
            
            # Sign order with PQC
            signature = None
            if self.pqc.pqc_enabled:
                try:
                    import json
                    order_bytes = json.dumps(order_data, sort_keys=True).encode()
                    keypair = self.pqc.generate_keypair_signature()
                    if keypair:
                        _, secret_key = keypair
                        signature = self.pqc.sign_message(order_bytes, secret_key)
                        if signature:
                            logger.info(f"✅ Order signed with Dilithium-3 ({len(signature)} bytes)")
                except Exception as e:
                    logger.warning(f"⚠️ PQC signing failed (continuing): {e}")
            
            # Execute order
            result = self.kraken.place_order(
                pair=pair,
                order_type=order_type,
                side=side,
                volume=amount,
                price=price
            )
            
            if result:
                logger.info(f"✅ Trade executed: {side} {amount} {pair}")
                return {
                    'success': True,
                    'order_id': result.get('txid', [''])[0] if 'txid' in result else '',
                    'signature': signature.hex() if signature else None,
                    'pqc_secured': signature is not None
                }
            else:
                return {'success': False, 'error': 'Order execution failed'}
                
        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _generate_recommendation(
        self,
        monte_carlo: Dict,
        black_swan: Dict,
        position_sizing: Dict
    ) -> Dict[str, Any]:
        """Generate trading recommendation based on all analyses"""
        try:
            # Extract key metrics
            win_rate = monte_carlo.get('win_rate', 0.5)
            risk_reward = monte_carlo.get('risk_reward_ratio', 1.0)
            black_swan_detected = black_swan.get('detected', False)
            black_swan_severity = black_swan.get('severity', 'low')
            
            # Decision logic
            if black_swan_detected and black_swan_severity == 'high':
                action = 'AVOID'
                confidence = 'low'
                reason = "Black Swan event detected - extreme risk"
            elif win_rate < 0.45:
                action = 'AVOID'
                confidence = 'medium'
                reason = f"Low win rate ({win_rate:.1%})"
            elif win_rate > 0.55 and risk_reward > 1.5:
                action = 'BUY'
                confidence = 'high'
                reason = f"Favorable odds: {win_rate:.1%} win rate, {risk_reward:.2f} R:R"
            elif win_rate > 0.50:
                action = 'BUY'
                confidence = 'medium'
                reason = f"Moderate odds: {win_rate:.1%} win rate"
            else:
                action = 'HOLD'
                confidence = 'medium'
                reason = "Insufficient edge"
            
            return {
                'action': action,
                'confidence': confidence,
                'reason': reason,
                'suggested_position_usd': position_sizing.get('recommended_position_usd', 0),
                'max_loss_usd': position_sizing.get('max_loss_usd', 0),
                'warnings': black_swan.get('recommendations', [])
            }
            
        except Exception as e:
            logger.error(f"Recommendation generation error: {e}")
            return {
                'action': 'HOLD',
                'confidence': 'low',
                'reason': 'Analysis error'
            }
    
    def health_check(self) -> Dict[str, bool]:
        """Check health of all trading service components"""
        return {
            'kraken_api': self.kraken.health_check(),
            'monte_carlo': True,  # Always available
            'black_swan': True,  # Always available
            'pqc_security': self.pqc.pqc_enabled
        }
