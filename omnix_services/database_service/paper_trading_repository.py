"""
OMNIX Paper Trading Repository V6.5.4
Repository para consultar datos REALES de paper trading desde PostgreSQL

FIX Dec 10, 2025: Creado para que el AI NO invente datos de trades.
El bot DEBE usar este repositorio para obtener historial y métricas reales.
"""

import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PaperTradingRepository:
    """
    Repository para consultar paper trading data desde PostgreSQL.
    
    Usa DatabaseGateway para conexión pooled.
    Retorna datos REALES o indicadores claros de "sin datos".
    """
    
    def __init__(self):
        self._gateway = None
    
    def _get_gateway(self):
        """Lazy-load DatabaseGateway para evitar imports circulares."""
        if self._gateway is None:
            try:
                from omnix_services.database_service.database_gateway import DatabaseGateway
                self._gateway = DatabaseGateway
            except ImportError as e:
                logger.error(f"❌ PaperTradingRepository: Cannot import DatabaseGateway: {e}")
        return self._gateway
    
    def get_trade_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Obtener estadísticas de trading desde PostgreSQL.
        
        Args:
            user_id: ID del usuario (OBLIGATORIO para aislamiento multi-usuario)
        
        Returns:
            Dict con:
            - total_trades: int
            - winning_trades: int
            - losing_trades: int
            - win_rate: float (0-100)
            - total_pnl: float
            - total_pnl_pct: float
            - data_source: str ("postgresql" o "no_data")
            - error: str (si hubo error)
        """
        gateway = self._get_gateway()
        
        if gateway is None:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'total_pnl_pct': 0.0,
                'data_source': 'database_unavailable',
                'error': 'DatabaseGateway not available'
            }
        
        try:
            query = """
                SELECT 
                    COUNT(*) as total_trades,
                    COUNT(CASE WHEN profit_loss > 0 THEN 1 END) as winning_trades,
                    COUNT(CASE WHEN profit_loss <= 0 THEN 1 END) as losing_trades,
                    COALESCE(SUM(profit_loss), 0) as total_pnl,
                    COALESCE(AVG(profit_pct), 0) as avg_pnl_pct
                FROM paper_trading_trades
                WHERE status = 'CLOSED'
                AND user_id = %s
            """
            params = (str(user_id),)
            
            result = gateway.execute_query(query, params)
            
            if result and len(result) > 0:
                row = result[0]
                total_trades = int(row[0]) if row[0] else 0
                winning_trades = int(row[1]) if row[1] else 0
                losing_trades = int(row[2]) if row[2] else 0
                total_pnl = float(row[3]) if row[3] else 0.0
                avg_pnl_pct = float(row[4]) if row[4] else 0.0
                
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
                
                logger.info(f"📊 PaperTradingRepository: {total_trades} trades, {win_rate:.1f}% win rate, ${total_pnl:,.2f} P&L")
                
                return {
                    'total_trades': total_trades,
                    'winning_trades': winning_trades,
                    'losing_trades': losing_trades,
                    'win_rate': round(win_rate, 1),
                    'total_pnl': round(total_pnl, 2),
                    'total_pnl_pct': round(avg_pnl_pct, 2),
                    'data_source': 'postgresql',
                    'error': None
                }
            else:
                logger.info("📊 PaperTradingRepository: No closed trades found")
                return {
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'win_rate': 0.0,
                    'total_pnl': 0.0,
                    'total_pnl_pct': 0.0,
                    'data_source': 'no_data',
                    'error': None
                }
                
        except Exception as e:
            logger.error(f"❌ PaperTradingRepository.get_trade_statistics error: {e}")
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'total_pnl_pct': 0.0,
                'data_source': 'error',
                'error': str(e)
            }
    
    def get_recent_trades(self, user_id: str, limit: int = 10) -> Dict[str, Any]:
        """
        Obtener trades recientes desde PostgreSQL.
        
        Args:
            user_id: ID del usuario (OBLIGATORIO para aislamiento multi-usuario)
            limit: Número máximo de trades a retornar
        
        Returns:
            Dict con:
            - trades: List[Dict] con cada trade
            - count: int número de trades retornados
            - data_source: str
            - error: str (si hubo error)
        """
        gateway = self._get_gateway()
        
        if gateway is None:
            return {
                'trades': [],
                'count': 0,
                'data_source': 'database_unavailable',
                'error': 'DatabaseGateway not available'
            }
        
        try:
            query = """
                SELECT 
                    id,
                    symbol,
                    side,
                    quantity,
                    entry_price,
                    exit_price,
                    profit_loss,
                    profit_pct,
                    strategy,
                    status,
                    opened_at,
                    closed_at,
                    created_at
                FROM paper_trading_trades
                WHERE user_id = %s 
                ORDER BY COALESCE(closed_at, opened_at, created_at) DESC 
                LIMIT %s
            """
            params = (str(user_id), limit)
            
            result = gateway.execute_query(query, params)
            
            if result and len(result) > 0:
                trades = []
                for row in result:
                    trade = {
                        'id': row[0],
                        'symbol': row[1],
                        'side': row[2],
                        'quantity': float(row[3]) if row[3] else 0,
                        'entry_price': float(row[4]) if row[4] else 0,
                        'exit_price': float(row[5]) if row[5] else None,
                        'profit_loss': float(row[6]) if row[6] else 0,
                        'profit_pct': float(row[7]) if row[7] else 0,
                        'strategy': row[8],
                        'status': row[9],
                        'opened_at': row[10].isoformat() if row[10] else None,
                        'closed_at': row[11].isoformat() if row[11] else None
                    }
                    trades.append(trade)
                
                logger.info(f"📊 PaperTradingRepository: Retrieved {len(trades)} recent trades")
                
                return {
                    'trades': trades,
                    'count': len(trades),
                    'data_source': 'postgresql',
                    'error': None
                }
            else:
                logger.info("📊 PaperTradingRepository: No trades found in database")
                return {
                    'trades': [],
                    'count': 0,
                    'data_source': 'no_data',
                    'error': None
                }
                
        except Exception as e:
            logger.error(f"❌ PaperTradingRepository.get_recent_trades error: {e}")
            return {
                'trades': [],
                'count': 0,
                'data_source': 'error',
                'error': str(e)
            }
    
    def get_paper_balance(self, user_id: str) -> Dict[str, Any]:
        """
        Obtener balance de paper trading desde PostgreSQL.
        
        Args:
            user_id: ID del usuario (OBLIGATORIO para aislamiento multi-usuario)
        
        Returns:
            Dict con:
            - balance_usd: float
            - balance_btc: float
            - balance_eth: float
            - total_trades: int
            - winning_trades: int
            - losing_trades: int
            - total_pnl: float
            - last_updated: str
            - data_source: str
            - error: str (si hubo error)
        """
        gateway = self._get_gateway()
        
        if gateway is None:
            return {
                'balance_usd': None,
                'balance_btc': None,
                'balance_eth': None,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_pnl': 0.0,
                'last_updated': None,
                'data_source': 'database_unavailable',
                'error': 'DatabaseGateway not available'
            }
        
        try:
            query = """
                SELECT 
                    balance_usd,
                    btc_balance,
                    eth_balance,
                    total_trades,
                    winning_trades,
                    losing_trades,
                    total_realized_pnl_usd,
                    updated_at
                FROM paper_trading_balances
                WHERE user_id = %s 
                ORDER BY updated_at DESC 
                LIMIT 1
            """
            params = (str(user_id),)
            
            result = gateway.execute_query(query, params)
            
            if result and len(result) > 0:
                row = result[0]
                balance_usd = float(row[0]) if row[0] else 0.0
                balance_btc = float(row[1]) if row[1] else 0.0
                balance_eth = float(row[2]) if row[2] else 0.0
                total_trades = int(row[3]) if row[3] else 0
                winning_trades = int(row[4]) if row[4] else 0
                losing_trades = int(row[5]) if row[5] else 0
                total_pnl = float(row[6]) if row[6] else 0.0
                last_updated = row[7].isoformat() if row[7] else None
                
                logger.info(f"📊 PaperTradingRepository: Balance ${balance_usd:,.2f}, {total_trades} trades, P&L ${total_pnl:,.2f}")
                
                return {
                    'balance_usd': balance_usd,
                    'balance_btc': balance_btc,
                    'balance_eth': balance_eth,
                    'total_trades': total_trades,
                    'winning_trades': winning_trades,
                    'losing_trades': losing_trades,
                    'total_pnl': total_pnl,
                    'last_updated': last_updated,
                    'data_source': 'postgresql',
                    'error': None
                }
            else:
                logger.info("📊 PaperTradingRepository: No balance record found")
                return {
                    'balance_usd': None,
                    'balance_btc': None,
                    'balance_eth': None,
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'total_pnl': 0.0,
                    'last_updated': None,
                    'data_source': 'no_data',
                    'error': None
                }
                
        except Exception as e:
            logger.error(f"❌ PaperTradingRepository.get_paper_balance error: {e}")
            return {
                'balance_usd': None,
                'balance_btc': None,
                'balance_eth': None,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_pnl': 0.0,
                'last_updated': None,
                'data_source': 'error',
                'error': str(e)
            }
    
    def get_full_performance_context(self, user_id: str) -> Dict[str, Any]:
        """
        Obtener contexto completo de rendimiento para el AI.
        Combina estadísticas, trades recientes y balance.
        
        Args:
            user_id: ID del usuario (OBLIGATORIO para aislamiento multi-usuario)
        
        Returns:
            Dict con toda la información de rendimiento o indicadores claros de "sin datos".
        """
        stats = self.get_trade_statistics(user_id)
        recent = self.get_recent_trades(user_id, limit=5)
        balance = self.get_paper_balance(user_id)
        
        has_data = (
            stats.get('data_source') == 'postgresql' or 
            recent.get('data_source') == 'postgresql' or
            balance.get('data_source') == 'postgresql'
        )
        
        # FIX: Usar métricas de paper_trading_balances si tiene más datos
        # (La tabla balance tiene agregados más completos)
        balance_trades = balance.get('total_trades', 0) or 0
        stats_trades = stats.get('total_trades', 0) or 0
        
        if balance_trades > stats_trades:
            # Los datos de balance son más completos - usarlos para stats
            logger.info(f"📊 Using balance table metrics: {balance_trades} trades vs {stats_trades} from trades table")
            stats = {
                'total_trades': balance_trades,
                'winning_trades': balance.get('winning_trades', 0),
                'losing_trades': balance.get('losing_trades', 0),
                'win_rate': round((balance.get('winning_trades', 0) / balance_trades * 100) if balance_trades > 0 else 0, 1),
                'total_pnl': balance.get('total_pnl', 0),
                'total_pnl_pct': 0.0,  # No disponible en balance table
                'data_source': 'postgresql_balances',
                'error': None
            }
        
        return {
            'statistics': stats,
            'recent_trades': recent,
            'balance': balance,
            'has_real_data': has_data,
            'timestamp': datetime.utcnow().isoformat()
        }


_repository_instance = None


def get_paper_trading_repository() -> PaperTradingRepository:
    """Singleton para obtener el repositorio."""
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = PaperTradingRepository()
    return _repository_instance
