"""
🔴 OMNIX REAL CONTEXT PROVIDER V6.4 - TRANSPARENCIA INSTITUCIONAL
Sistema centralizado para inyectar datos REALES en todas las respuestas de IA

Garantiza que OMNIX siempre responda con información verificada del sistema.
"""

import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

_global_provider = None

class OMNIXRealContextProvider:
    """
    Proveedor centralizado de contexto real para OMNIX.
    Obtiene datos verificados del sistema para inyectar en prompts de IA.
    """
    
    def __init__(
        self,
        auto_trading_bot=None,
        paper_trading_manager=None,
        trading_service=None,
        database_manager=None,
        cache_ttl_seconds: int = 30
    ):
        self.auto_trading = auto_trading_bot
        self.paper_trading = paper_trading_manager
        self.trading_service = trading_service
        self.db_manager = database_manager
        self.cache_ttl = cache_ttl_seconds
        
        self._cache = {}
        self._cache_timestamps = {}
        
        self._cache_ttl_overrides = {
            'symbol_breakdown': 120,
            'regime_breakdown': 120,
            'coherence_breakdown': 120,
            'fee_impact': 120,
            'timing_patterns': 300
        }
        
        logger.info("🔴 OMNIXRealContextProvider inicializado - Transparencia Institucional ACTIVA")
    
    def _is_cache_valid(self, key: str) -> bool:
        """Verifica si el cache para una clave es válido usando TTL específico por clave"""
        if key not in self._cache_timestamps:
            return False
        ttl = self._cache_ttl_overrides.get(key, self.cache_ttl)
        return (time.time() - self._cache_timestamps[key]) < ttl
    
    def _update_cache(self, key: str, value: Any):
        """Actualiza el cache con un nuevo valor"""
        self._cache[key] = value
        self._cache_timestamps[key] = time.time()
    
    def get_auto_trading_status(self) -> Dict:
        """Obtener estado real del auto-trading"""
        cache_key = 'auto_trading_status'
        
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        try:
            if self.auto_trading:
                status = self.auto_trading.get_status()
                result = {
                    'available': True,
                    'running': status.get('running', False),
                    'paper_mode': status.get('paper_mode', True),
                    'trading_pair': status.get('trading_pair', 'BTC/USD'),
                    'total_trades': status.get('total_trades', 0),
                    'winning_trades': status.get('winning_trades', 0),
                    'losing_trades': status.get('losing_trades', 0),
                    'win_rate': status.get('win_rate', 0),
                    'win_rate_net': status.get('win_rate_net', status.get('win_rate', 0)),
                    'win_rate_directional': status.get('win_rate_directional', 0),
                    'fee_eroded_trades': status.get('fee_eroded_trades', 0),
                    'profit_loss': status.get('profit_loss', 0),
                    'roi': status.get('roi', 0),
                    'current_balance': status.get('current_balance', 0),
                    'initial_balance': status.get('initial_balance', 0),
                    'last_trade_time': status.get('last_trade_time', None),
                    'emergency_stop': status.get('emergency_stop', False),
                    'check_interval': status.get('check_interval', 30),
                    'auto_learning': status.get('auto_learning', {})
                }
                self._update_cache(cache_key, result)
                return result
            else:
                return {'available': False, 'running': False, 'message': 'Auto-trading no inicializado'}
        except Exception as e:
            logger.warning(f"⚠️ Error obteniendo estado auto-trading: {e}")
            return {'available': False, 'running': False, 'error': str(e)}
    
    def get_market_data(self) -> Dict:
        """Obtener datos de mercado reales de Kraken"""
        cache_key = 'market_data'
        
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        try:
            result = {}
            
            if self.trading_service:
                try:
                    if hasattr(self.trading_service, 'kraken_client') and self.trading_service.kraken_client:
                        btc_ticker = self.trading_service.kraken_client.client.fetch_ticker('BTC/USD')
                        result['btc_price'] = btc_ticker.get('last', 0)
                        result['btc_24h_high'] = btc_ticker.get('high', 0)
                        result['btc_24h_low'] = btc_ticker.get('low', 0)
                        result['btc_volume'] = btc_ticker.get('baseVolume', 0)
                        result['btc_change_24h'] = btc_ticker.get('percentage', 0)
                        
                        eth_ticker = self.trading_service.kraken_client.client.fetch_ticker('ETH/USD')
                        result['eth_price'] = eth_ticker.get('last', 0)
                        result['eth_24h_high'] = eth_ticker.get('high', 0)
                        result['eth_24h_low'] = eth_ticker.get('low', 0)
                        
                        result['source'] = 'kraken_auth'
                    elif hasattr(self.trading_service, 'get_ticker'):
                        btc_ticker = self.trading_service.get_ticker('BTC/USD')
                        if btc_ticker:
                            result['btc_price'] = float(btc_ticker.get('last', 0))
                            result['btc_24h_high'] = float(btc_ticker.get('high', 0))
                            result['btc_24h_low'] = float(btc_ticker.get('low', 0))
                        result['source'] = 'trading_service'
                except Exception as ts_error:
                    logger.warning(f"⚠️ Error obteniendo datos de trading service: {ts_error}")
            
            if not result.get('btc_price'):
                try:
                    import requests
                    response = requests.get(
                        'https://api.kraken.com/0/public/Ticker?pair=XBTUSD',
                        timeout=5
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if not data.get('error'):
                            ticker = data.get('result', {})
                            ticker_key = list(ticker.keys())[0] if ticker else None
                            if ticker_key:
                                t = ticker[ticker_key]
                                result['btc_price'] = float(t['c'][0]) if t.get('c') else 0
                                result['btc_24h_high'] = float(t['h'][0]) if t.get('h') else 0
                                result['btc_24h_low'] = float(t['l'][0]) if t.get('l') else 0
                                result['btc_volume'] = float(t['v'][1]) if t.get('v') else 0
                                result['source'] = 'kraken_public'
                except Exception as pub_error:
                    logger.warning(f"⚠️ Error Kraken public API: {pub_error}")
            
            result['timestamp'] = datetime.now().isoformat()
            self._update_cache(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos de mercado: {e}")
            return {'error': str(e), 'btc_price': 0}
    
    def get_paper_balance(self, user_id: str = None) -> Dict:
        """Obtener balance de paper trading"""
        try:
            if self.paper_trading and user_id:
                balance = self.paper_trading.get_paper_balance(user_id)
                return balance if balance else {'balance_usd': 0, 'initialized': False}
            return {'balance_usd': 0, 'initialized': False, 'message': 'Paper trading no disponible'}
        except Exception as e:
            logger.warning(f"⚠️ Error obteniendo paper balance: {e}")
            return {'error': str(e), 'balance_usd': 0}
    
    def get_open_positions(self, user_id: str = None) -> list:
        """Obtener posiciones abiertas"""
        try:
            if self.paper_trading and user_id:
                positions = self.paper_trading.get_open_positions(user_id)
                return positions if positions else []
            return []
        except Exception as e:
            logger.warning(f"⚠️ Error obteniendo posiciones: {e}")
            return []
    
    def get_recent_trades(self, user_id: str = None, limit: int = 5) -> list:
        """Obtener trades recientes"""
        try:
            if self.db_manager:
                rows = self.db_manager.execute_query(
                    """SELECT id, symbol, side, quantity, entry_price, exit_price, 
                              profit_loss, status, opened_at, closed_at
                       FROM paper_trading_trades 
                       WHERE user_id = %s::TEXT
                       ORDER BY id DESC LIMIT %s""",
                    (user_id, limit)
                )
                if rows:
                    trades = []
                    for row in rows:
                        if isinstance(row, tuple) and len(row) >= 8:
                            trades.append({
                                'id': row[0],
                                'symbol': row[1],
                                'side': row[2],
                                'quantity': row[3],
                                'entry_price': row[4],
                                'exit_price': row[5],
                                'profit_loss': row[6],
                                'status': row[7],
                                'opened_at': row[8] if len(row) > 8 else None,
                                'closed_at': row[9] if len(row) > 9 else None
                            })
                        elif isinstance(row, dict):
                            trades.append(row)
                    return trades
            return []
        except Exception as e:
            logger.warning(f"⚠️ Error obteniendo trades recientes: {e}")
            return []
    
    def get_symbol_breakdown(self) -> list:
        """Obtener breakdown detallado por símbolo - Cache 120s"""
        cache_key = 'symbol_breakdown'
        
        if self._is_cache_valid(cache_key):
            return self._cache.get(cache_key, [])
        
        try:
            if not self.db_manager:
                return []
            
            rows = self.db_manager.execute_query("""
                SELECT 
                    symbol,
                    COUNT(*) as total_trades,
                    COUNT(CASE WHEN profit_loss > 0 THEN 1 END) as wins,
                    ROUND(100.0 * COUNT(CASE WHEN profit_loss > 0 THEN 1 END) / NULLIF(COUNT(*), 0), 1) as win_rate,
                    COALESCE(SUM(profit_loss), 0) as total_pnl,
                    COALESCE(AVG(profit_loss), 0) as avg_pnl
                FROM paper_trading_trades
                WHERE status = 'closed'
                GROUP BY symbol
                ORDER BY total_pnl ASC
                LIMIT 10
            """)
            
            result = []
            if rows:
                for row in rows:
                    if isinstance(row, (tuple, list)) and len(row) >= 6:
                        result.append({
                            'symbol': row[0],
                            'total_trades': int(row[1] or 0),
                            'wins': int(row[2] or 0),
                            'win_rate': float(row[3] or 0),
                            'total_pnl': float(row[4] or 0),
                            'avg_pnl': float(row[5] or 0)
                        })
                    elif isinstance(row, dict):
                        result.append(row)
            
            self._update_cache(cache_key, result)
            self._cache_timestamps[cache_key] = time.time()
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ Error obteniendo symbol breakdown: {e}")
            return []
    
    def get_regime_breakdown(self) -> list:
        """Obtener breakdown por régimen HMM - Cache 120s"""
        cache_key = 'regime_breakdown'
        
        if self._is_cache_valid(cache_key):
            return self._cache.get(cache_key, [])
        
        try:
            if not self.db_manager:
                return []
            
            rows = self.db_manager.execute_query("""
                SELECT 
                    COALESCE(hmm_regime, 'UNKNOWN') as hmm_regime,
                    COUNT(*) as trades,
                    COUNT(CASE WHEN profit_loss > 0 THEN 1 END) as wins,
                    ROUND(100.0 * COUNT(CASE WHEN profit_loss > 0 THEN 1 END) / NULLIF(COUNT(*), 0), 1) as win_rate,
                    COALESCE(SUM(profit_loss), 0) as total_pnl,
                    COALESCE(AVG(profit_loss), 0) as avg_pnl
                FROM paper_trading_trades
                WHERE status = 'closed'
                GROUP BY hmm_regime
                ORDER BY avg_pnl ASC
            """)
            
            result = []
            if rows:
                for row in rows:
                    if isinstance(row, (tuple, list)) and len(row) >= 6:
                        result.append({
                            'hmm_regime': row[0] or 'UNKNOWN',
                            'trades': int(row[1] or 0),
                            'wins': int(row[2] or 0),
                            'win_rate': float(row[3] or 0),
                            'total_pnl': float(row[4] or 0),
                            'avg_pnl': float(row[5] or 0)
                        })
                    elif isinstance(row, dict):
                        result.append(row)
            
            self._update_cache(cache_key, result)
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ Error obteniendo regime breakdown: {e}")
            return []
    
    def get_coherence_breakdown(self) -> list:
        """Obtener breakdown por coherence state - Cache 120s"""
        cache_key = 'coherence_breakdown'
        
        if self._is_cache_valid(cache_key):
            return self._cache.get(cache_key, [])
        
        try:
            if not self.db_manager:
                return []
            
            rows = self.db_manager.execute_query("""
                SELECT 
                    CASE 
                        WHEN coherence_score IS NULL THEN 'NO_DATA'
                        WHEN coherence_score < 30 THEN 'CRITICAL'
                        WHEN coherence_score < 40 THEN 'POOR'
                        WHEN coherence_score < 60 THEN 'MODERATE'
                        WHEN coherence_score < 75 THEN 'GOOD'
                        ELSE 'EXCELLENT'
                    END as coherence_level,
                    COUNT(*) as trades,
                    COUNT(CASE WHEN profit_loss > 0 THEN 1 END) as wins,
                    ROUND(100.0 * COUNT(CASE WHEN profit_loss > 0 THEN 1 END) / NULLIF(COUNT(*), 0), 1) as win_rate,
                    COALESCE(SUM(profit_loss), 0) as total_pnl,
                    COALESCE(AVG(profit_loss), 0) as avg_pnl
                FROM paper_trading_trades
                WHERE status = 'closed'
                GROUP BY coherence_level
                ORDER BY 
                    CASE coherence_level
                        WHEN 'CRITICAL' THEN 1
                        WHEN 'POOR' THEN 2
                        WHEN 'MODERATE' THEN 3
                        WHEN 'GOOD' THEN 4
                        WHEN 'EXCELLENT' THEN 5
                        ELSE 6
                    END
            """)
            
            result = []
            if rows:
                for row in rows:
                    if isinstance(row, (tuple, list)) and len(row) >= 6:
                        result.append({
                            'coherence_level': row[0] or 'NO_DATA',
                            'trades': int(row[1] or 0),
                            'wins': int(row[2] or 0),
                            'win_rate': float(row[3] or 0),
                            'total_pnl': float(row[4] or 0),
                            'avg_pnl': float(row[5] or 0)
                        })
                    elif isinstance(row, dict):
                        result.append(row)
            
            self._update_cache(cache_key, result)
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ Error obteniendo coherence breakdown: {e}")
            return []
    
    def get_fee_impact(self) -> Dict:
        """Analizar impacto de fees (ADR-005: profit_loss < 0 para fee-eroded) - Cache 120s"""
        cache_key = 'fee_impact'
        
        if self._is_cache_valid(cache_key):
            return self._cache.get(cache_key, {})
        
        try:
            if not self.db_manager:
                return {}
            
            rows = self.db_manager.execute_query("""
                SELECT 
                    COUNT(*) as total_trades,
                    COUNT(CASE WHEN profit_pct > 0 AND profit_loss < 0 THEN 1 END) as fee_eroded,
                    COALESCE(AVG(CASE WHEN profit_pct > 0 AND profit_loss < 0 THEN ABS(profit_loss) END), 0) as avg_fee_erosion,
                    COALESCE(SUM(CASE WHEN profit_pct > 0 AND profit_loss < 0 THEN ABS(profit_loss) END), 0) as total_fee_erosion
                FROM paper_trading_trades
                WHERE status = 'closed'
            """)
            
            result = {'total_trades': 0, 'fee_eroded': 0, 'avg_fee_erosion': 0, 'total_fee_erosion': 0}
            if rows and len(rows) > 0:
                row = rows[0]
                if isinstance(row, (tuple, list)) and len(row) >= 4:
                    result = {
                        'total_trades': int(row[0] or 0),
                        'fee_eroded': int(row[1] or 0),
                        'avg_fee_erosion': float(row[2] or 0),
                        'total_fee_erosion': float(row[3] or 0)
                    }
                elif isinstance(row, dict):
                    result = row
            
            self._update_cache(cache_key, result)
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ Error obteniendo fee impact: {e}")
            return {}
    
    def get_timing_patterns(self) -> list:
        """Analizar patrones temporales (peores/mejores horas) - Cache 300s"""
        cache_key = 'timing_patterns'
        
        if self._is_cache_valid(cache_key):
            return self._cache.get(cache_key, [])
        
        try:
            if not self.db_manager:
                return []
            
            rows = self.db_manager.execute_query("""
                SELECT 
                    EXTRACT(HOUR FROM closed_at) as hour,
                    COUNT(*) as trades,
                    COUNT(CASE WHEN profit_loss > 0 THEN 1 END) as wins,
                    ROUND(100.0 * COUNT(CASE WHEN profit_loss > 0 THEN 1 END) / NULLIF(COUNT(*), 0), 1) as win_rate,
                    COALESCE(SUM(profit_loss), 0) as total_pnl,
                    COALESCE(AVG(profit_loss), 0) as avg_pnl
                FROM paper_trading_trades
                WHERE status = 'closed' AND closed_at IS NOT NULL
                GROUP BY hour
                ORDER BY avg_pnl ASC
                LIMIT 10
            """)
            
            result = []
            if rows:
                for row in rows:
                    if isinstance(row, (tuple, list)) and len(row) >= 6:
                        result.append({
                            'hour': int(row[0]) if row[0] is not None else 0,
                            'trades': int(row[1] or 0),
                            'wins': int(row[2] or 0),
                            'win_rate': float(row[3] or 0),
                            'total_pnl': float(row[4] or 0),
                            'avg_pnl': float(row[5] or 0)
                        })
                    elif isinstance(row, dict):
                        result.append(row)
            
            self._update_cache(cache_key, result)
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ Error obteniendo timing patterns: {e}")
            return []
    
    def get_analytics_context(self) -> Dict:
        """Obtener todos los breakdowns analíticos en una sola llamada"""
        return {
            'symbol_breakdown': self.get_symbol_breakdown(),
            'regime_breakdown': self.get_regime_breakdown(),
            'coherence_breakdown': self.get_coherence_breakdown(),
            'fee_impact': self.get_fee_impact(),
            'timing_patterns': self.get_timing_patterns()
        }
    
    def get_full_context(self, user_id: str = None) -> Dict:
        """Obtener contexto completo de OMNIX incluyendo analytics"""
        return {
            'auto_trading': self.get_auto_trading_status(),
            'market': self.get_market_data(),
            'paper_balance': self.get_paper_balance(user_id) if user_id else {},
            'open_positions': self.get_open_positions(user_id) if user_id else [],
            'recent_trades': self.get_recent_trades(user_id) if user_id else [],
            'analytics': self.get_analytics_context(),
            'timestamp': datetime.now().isoformat()
        }
    
    def format_for_prompt(self, user_id: str = None) -> str:
        """Formatear contexto completo para inyectar en prompts de IA"""
        ctx = self.get_full_context(user_id)
        
        at = ctx.get('auto_trading', {})
        market = ctx.get('market', {})
        balance = ctx.get('paper_balance', {})
        positions = ctx.get('open_positions', [])
        trades = ctx.get('recent_trades', [])
        
        prompt = """
🔴 === DATOS REALES DE OMNIX (VERIFICADOS - USA SOLO ESTOS) ===

"""
        
        if market.get('btc_price'):
            prompt += f"""📊 MERCADO EN TIEMPO REAL (Kraken API):
• Bitcoin (BTC/USD): ${market.get('btc_price', 0):,.2f}
• 24h High: ${market.get('btc_24h_high', 0):,.2f}
• 24h Low: ${market.get('btc_24h_low', 0):,.2f}
• Volumen 24h: {market.get('btc_volume', 0):,.2f} BTC
• Fuente: {market.get('source', 'API')}

"""
        
        if at.get('available'):
            is_running = at.get('running', False)
            wr_dir = at.get('win_rate_directional', 0)
            wr_net = at.get('win_rate_net', at.get('win_rate', 0))
            fee_eroded = at.get('fee_eroded_trades', 0)
            prompt += f"""🤖 AUTO-TRADING (Estado Real):
• Estado: {'🟢 ACTIVO 24/7' if is_running else '🔴 DETENIDO'}
• Modo: {'📝 PAPER TRADING ($1M virtual)' if at.get('paper_mode') else '💰 TRADING REAL'}
• Par: {at.get('trading_pair', 'BTC/USD') + ' (ejemplo actual)'}
• Total Trades: {at.get('total_trades', 0)}
• Ganadores: {at.get('winning_trades', 0)} | Perdedores: {at.get('losing_trades', 0)}
• Win Rate Precisión: {wr_dir:.1f}% (predicción de dirección correcta)
• Win Rate Rentable: {wr_net:.1f}% (ganancia después de fees)
• Trades Fee-Eroded: {fee_eroded} (acertaron dirección pero perdieron por fees)
• P&L Total: ${at.get('profit_loss', 0):+,.2f} (fase de validación)
• ROI: {at.get('roi', 0):+.2f}% (valor referencial en fase de pruebas)
• Último Trade: {at.get('last_trade_time') or 'Ninguno aún'}
• Parada Emergencia: {'🚨 ACTIVADA' if at.get('emergency_stop') else '✅ Normal'}

"""
        else:
            prompt += """🤖 AUTO-TRADING: ⚠️ No inicializado

"""
        
        if balance.get('initialized', False) or balance.get('balance_usd', 0) > 0:
            prompt += f"""💰 PAPER TRADING BALANCE:
• USD: ${balance.get('balance_usd', 0):,.2f}
• BTC: {balance.get('btc_balance', 0):.8f}
• ETH: {balance.get('eth_balance', 0):.8f}
• Trades Totales: {balance.get('total_trades', 0)}
• Ganadores: {balance.get('winning_trades', 0)} | Perdedores: {balance.get('losing_trades', 0)}

"""
        
        if positions:
            prompt += "📈 POSICIONES ABIERTAS:\n"
            for pos in positions[:5]:
                prompt += f"• {pos.get('symbol', 'N/A')}: {pos.get('quantity', 0):.8f} @ ${pos.get('entry_price', 0):,.2f}\n"
            prompt += "\n"
        
        if trades:
            prompt += "📋 TRADES RECIENTES:\n"
            for trade in trades[:5]:
                status = '✅' if trade.get('status') == 'closed' else '🔄'
                pnl = trade.get('profit_loss', 0) or 0
                prompt += f"• {status} {trade.get('symbol', 'N/A')} {trade.get('side', 'N/A').upper()}: ${pnl:+,.2f}\n"
            prompt += "\n"
        
        analytics = ctx.get('analytics', {})
        
        symbol_breakdown = analytics.get('symbol_breakdown', [])
        if symbol_breakdown:
            prompt += "📊 BREAKDOWN POR SÍMBOLO (ordenado por P&L, peores primero):\n"
            for s in symbol_breakdown[:5]:
                prompt += f"• {s.get('symbol', 'N/A')}: {s.get('total_trades', 0)} trades, {s.get('win_rate', 0):.1f}% WR, ${s.get('total_pnl', 0):+,.2f} P&L\n"
            prompt += "\n"
        
        regime_breakdown = analytics.get('regime_breakdown', [])
        if regime_breakdown:
            prompt += "🌊 BREAKDOWN POR RÉGIMEN HMM:\n"
            for r in regime_breakdown:
                prompt += f"• {r.get('hmm_regime', 'N/A')}: {r.get('trades', 0)} trades, {r.get('win_rate', 0):.1f}% WR, ${r.get('avg_pnl', 0):+,.2f} avg\n"
            prompt += "\n"
        
        coherence_breakdown = analytics.get('coherence_breakdown', [])
        if coherence_breakdown:
            prompt += "🎯 BREAKDOWN POR COHERENCE:\n"
            for c in coherence_breakdown:
                prompt += f"• {c.get('coherence_level', 'N/A')}: {c.get('trades', 0)} trades, {c.get('win_rate', 0):.1f}% WR, ${c.get('avg_pnl', 0):+,.2f} avg\n"
            prompt += "\n"
        
        fee_impact = analytics.get('fee_impact', {})
        if fee_impact.get('fee_eroded', 0) > 0:
            prompt += f"""💸 IMPACTO DE FEES:
• Trades fee-eroded: {fee_impact.get('fee_eroded', 0)} (ganaron dirección pero perdieron por fees)
• Erosión promedio: ${fee_impact.get('avg_fee_erosion', 0):.2f} por trade
• Erosión total: ${fee_impact.get('total_fee_erosion', 0):,.2f}

"""
        
        timing_patterns = analytics.get('timing_patterns', [])
        if timing_patterns:
            prompt += "⏰ PATRONES TEMPORALES (peores horas UTC):\n"
            for t in timing_patterns[:3]:
                prompt += f"• {int(t.get('hour', 0)):02d}:00 UTC: {t.get('trades', 0)} trades, {t.get('win_rate', 0):.1f}% WR, ${t.get('avg_pnl', 0):+,.2f} avg\n"
            prompt += "\n"
        
        prompt += """⚠️ REGLAS DE TRANSPARENCIA INSTITUCIONAL:
1. SIEMPRE usa los datos de arriba para responder - NUNCA inventes
2. Si el usuario pregunta "por qué perdemos", usa los BREAKDOWNS de arriba
3. YA TIENES TODOS LOS DATOS - NO digas "necesito ejecutar queries" o "no tengo información"
4. Para análisis detallado, usa los breakdowns por símbolo, régimen y coherence
5. Identifica patrones específicos: qué símbolos, regímenes o niveles de coherence pierden más
6. Propón acciones concretas basadas en los datos (ej: "bloquear SOL/USD" si pierde más)
7. Esta transparencia es CRÍTICA para inversores institucionales

"""
        return prompt


def get_real_context_provider() -> Optional[OMNIXRealContextProvider]:
    """Obtener la instancia global del proveedor de contexto"""
    global _global_provider
    return _global_provider


def set_real_context_provider(provider: OMNIXRealContextProvider):
    """Establecer la instancia global del proveedor de contexto"""
    global _global_provider
    _global_provider = provider
    logger.info("🔴 OMNIXRealContextProvider global establecido")


def create_real_context_provider(
    auto_trading_bot=None,
    paper_trading_manager=None,
    trading_service=None,
    database_manager=None
) -> OMNIXRealContextProvider:
    """Crear y establecer el proveedor de contexto global"""
    provider = OMNIXRealContextProvider(
        auto_trading_bot=auto_trading_bot,
        paper_trading_manager=paper_trading_manager,
        trading_service=trading_service,
        database_manager=database_manager
    )
    set_real_context_provider(provider)
    return provider
