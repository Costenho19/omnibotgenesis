"""
📊 OMNIX PAPER TRADING SYSTEM
Sistema de trading simulado con datos REALES de Kraken

CARACTERÍSTICAS:
- Balance virtual inicial: $1,000,000 USD
- Datos reales de Kraken (precios, OHLC, análisis)
- Trades simulados (NO gasta dinero real)
- Performance tracking completo
- Integración con servicios enterprise
"""

import logging
import time
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class PaperTradingManager:
    """
    Sistema profesional de Paper Trading
    
    Ejecuta trades simulados con datos reales de Kraken
    para testing y validación de estrategias
    """
    
    def __init__(self, database_service=None, trading_service=None):
        self.database_service = database_service
        self.trading_service = trading_service
        
        # Balance virtual inicial
        self.INITIAL_BALANCE_USD = 1_000_000.00
        
        # Kraken fees (26 basis points = 0.26%)
        self.KRAKEN_FEE_BPS = 26.0
        self.KRAKEN_FEE_RATE = 0.0026
        
        logger.info("📊 PaperTradingManager inicializado - Balance inicial: $1,000,000")
    
    def initialize_user(self, user_id: str) -> Dict:
        """
        Inicializar usuario en paper trading con $1M
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Dict con balance inicial y metadata
        """
        try:
            if not self.database_service:
                return {'error': 'Database service no disponible'}
            
            # Verificar si ya existe
            existing = self._get_paper_balance(user_id)
            if existing:
                return {
                    'success': True,
                    'already_initialized': True,
                    'balance_usd': existing['balance_usd'],
                    'total_trades': existing['total_trades']
                }
            
            # Crear balance inicial V2
            balance_data = {
                'user_id': user_id,
                'balance_usd': self.INITIAL_BALANCE_USD,
                'btc_balance': 0.0,
                'eth_balance': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_realized_pnl_usd': 0.0,
                'available_margin_usd': self.INITIAL_BALANCE_USD,
                'created_at': datetime.now().isoformat()
            }
            
            # Guardar en database
            if hasattr(self.database_service, 'using_enterprise') and self.database_service.using_enterprise:
                # Usar método enterprise
                success = self._save_paper_balance_enterprise(balance_data)
            else:
                # Fallback legacy
                success = self._save_paper_balance_legacy(balance_data)
            
            if success:
                logger.info(f"✅ Usuario {user_id} inicializado con $1,000,000 paper trading")
                return {
                    'success': True,
                    'balance_usd': self.INITIAL_BALANCE_USD,
                    'message': '🎯 Paper Trading activado con $1,000,000 inicial'
                }
            else:
                return {'error': 'Error guardando balance inicial'}
                
        except Exception as e:
            logger.error(f"Error inicializando paper trading: {e}")
            return {'error': str(e)}
    
    def execute_paper_trade(self, user_id: str, side: str, symbol: str, amount_usd: float) -> Dict:
        """
        Ejecutar trade simulado con datos REALES de Kraken
        
        V2: Usa schema institucional con P&L tracking completo
        
        Args:
            user_id: ID del usuario
            side: 'buy' o 'sell'
            symbol: Par de trading (ej: 'BTC/USD')
            amount_usd: Cantidad en USD a tradear
            
        Returns:
            Dict con resultado del trade simulado
        """
        try:
            # 1. Obtener precio REAL de Kraken
            if self.trading_service and hasattr(self.trading_service, 'get_ticker'):
                ticker = self.trading_service.get_ticker(symbol)
                if not ticker or 'last' not in ticker:
                    return {'error': 'No se pudo obtener precio de Kraken'}
                current_price = float(ticker['last'])
            else:
                return {'error': 'Trading service no disponible'}
            
            # 2. Obtener balance actual
            balance = self._get_paper_balance(user_id)
            if not balance:
                return {'error': 'Usuario no inicializado en paper trading'}
            
            # Calcular cantidad de crypto
            crypto_amount = amount_usd / current_price
            fee_usd = self._calculate_fee(amount_usd)
            
            # 3. Ejecutar BUY o SELL con métodos V2
            if side == 'buy':
                # Validar fondos suficientes (incluye fees)
                total_cost = amount_usd + fee_usd
                if balance['balance_usd'] < total_cost:
                    return {
                        'error': f'Fondos insuficientes. Balance: ${balance["balance_usd"]:,.2f}, Necesitas: ${total_cost:,.2f} (incluye fee ${fee_usd:.2f})',
                        'balance_usd': balance['balance_usd']
                    }
                
                # Abrir posición V2
                trade_uuid = self._open_position_v2(
                    user_id=user_id,
                    symbol=symbol,
                    base_quantity=crypto_amount,
                    entry_price=current_price,
                    source_strategy='auto_trading_bot'
                )
                
                if not trade_uuid:
                    return {'error': 'Error abriendo posición'}
                
                logger.info(f"✅ BUY ejecutado: {crypto_amount:.8f} {symbol} @ ${current_price:,.2f} (fee: ${fee_usd:.2f})")
                
                return {
                    'success': True,
                    'side': 'buy',
                    'symbol': symbol,
                    'amount': crypto_amount,
                    'price': current_price,
                    'total_usd': amount_usd,
                    'fee_usd': fee_usd,
                    'total_cost': total_cost,
                    'trade_uuid': trade_uuid,
                    'message': f'✅ BUY {crypto_amount:.8f} {symbol} @ ${current_price:,.2f} | Fee: ${fee_usd:.2f}'
                }
                
            elif side == 'sell':
                # Cerrar posición FIFO V2
                close_result = self._close_position_fifo_v2(
                    user_id=user_id,
                    symbol=symbol,
                    sell_quantity=crypto_amount,
                    exit_price=current_price
                )
                
                if not close_result:
                    return {'error': 'Error cerrando posición o no hay posición abierta'}
                
                logger.info(f"✅ SELL ejecutado: {crypto_amount:.8f} {symbol} @ ${current_price:,.2f} | P&L: ${close_result['net_realized_pnl_usd']:,.2f}")
                
                return {
                    'success': True,
                    'side': 'sell',
                    'symbol': symbol,
                    'amount': crypto_amount,
                    'price': current_price,
                    'total_usd': amount_usd,
                    'fee_usd': close_result['fee_sell'],
                    'entry_price': close_result['entry_price'],
                    'exit_price': close_result['exit_price'],
                    'gross_pnl_usd': close_result['gross_pnl_usd'],
                    'net_realized_pnl_usd': close_result['net_realized_pnl_usd'],
                    'duration_seconds': close_result['duration_seconds'],
                    'is_winning_trade': close_result['is_winning_trade'],
                    'trade_uuid': close_result['trade_uuid'],
                    'message': f'✅ SELL {crypto_amount:.8f} {symbol} @ ${current_price:,.2f} | P&L: ${close_result["net_realized_pnl_usd"]:+,.2f} ({"WIN" if close_result["is_winning_trade"] else "LOSS"})'
                }
            else:
                return {'error': 'Side debe ser buy o sell'}
            
        except Exception as e:
            logger.error(f"Error ejecutando paper trade: {e}")
            return {'error': str(e)}
    
    def get_paper_balance(self, user_id: str) -> Dict:
        """Obtener balance actual de paper trading"""
        try:
            balance = self._get_paper_balance(user_id)
            if not balance:
                return {
                    'initialized': False,
                    'message': 'Usa /paper_start para inicializar paper trading con $1,000,000'
                }
            
            # Calcular valor total en USD
            total_usd = balance['balance_usd']
            
            # Obtener precios actuales para calcular valor de crypto
            if self.trading_service:
                try:
                    btc_ticker = self.trading_service.get_ticker('BTC/USD')
                    if btc_ticker and balance.get('btc_balance', 0) > 0:
                        total_usd += balance['btc_balance'] * float(btc_ticker['last'])
                except:
                    pass
                
                try:
                    eth_ticker = self.trading_service.get_ticker('ETH/USD')
                    if eth_ticker and balance.get('eth_balance', 0) > 0:
                        total_usd += balance['eth_balance'] * float(eth_ticker['last'])
                except:
                    pass
            
            # Calcular P&L
            profit_loss = total_usd - self.INITIAL_BALANCE_USD
            profit_loss_pct = (profit_loss / self.INITIAL_BALANCE_USD) * 100
            
            return {
                'initialized': True,
                'balance_usd': balance['balance_usd'],
                'btc_balance': balance.get('btc_balance', 0),
                'eth_balance': balance.get('eth_balance', 0),
                'total_value_usd': total_usd,
                'total_trades': balance.get('total_trades', 0),
                'profit_loss_usd': profit_loss,
                'profit_loss_pct': profit_loss_pct,
                'initial_balance': self.INITIAL_BALANCE_USD
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo paper balance: {e}")
            return {'error': str(e)}
    
    def _get_paper_balance(self, user_id: str) -> Optional[Dict]:
        """Obtener balance de paper trading desde PostgreSQL V2"""
        try:
            if self.database_service and hasattr(self.database_service, 'execute_query'):
                result = self.database_service.execute_query(
                    """
                    SELECT user_id, balance_usd, btc_balance, eth_balance, 
                           total_trades, winning_trades, losing_trades, 
                           total_realized_pnl_usd, available_margin_usd,
                           total_unrealized_pnl_usd, max_drawdown_pct, sharpe_ratio,
                           created_at, updated_at
                    FROM paper_trading_balances 
                    WHERE user_id = %s
                    """,
                    (user_id,)
                )
                
                if result and len(result) > 0:
                    row = result[0]
                    return {
                        'user_id': row[0],
                        'balance_usd': float(row[1]),
                        'btc_balance': float(row[2]),
                        'eth_balance': float(row[3]),
                        'total_trades': int(row[4]),
                        'winning_trades': int(row[5]) if row[5] else 0,
                        'losing_trades': int(row[6]) if row[6] else 0,
                        'total_realized_pnl_usd': float(row[7]) if row[7] else 0.0,
                        'available_margin_usd': float(row[8]) if row[8] else 1000000.0,
                        'total_unrealized_pnl_usd': float(row[9]) if row[9] else 0.0,
                        'max_drawdown_pct': float(row[10]) if row[10] else 0.0,
                        'sharpe_ratio': float(row[11]) if row[11] else 0.0,
                        'created_at': row[12],
                        'updated_at': row[13]
                    }
            return None
        except Exception as e:
            logger.warning(f"Error obteniendo balance desde DB: {e}")
            return None
    
    def _save_paper_balance_enterprise(self, balance_data: Dict) -> bool:
        """Guardar balance en PostgreSQL V2 - PERMANENTE"""
        try:
            if self.database_service and hasattr(self.database_service, 'execute_query'):
                self.database_service.execute_query(
                    """
                    INSERT INTO paper_trading_balances 
                    (user_id, balance_usd, btc_balance, eth_balance, 
                     total_trades, winning_trades, losing_trades, 
                     total_realized_pnl_usd, total_unrealized_pnl_usd,
                     available_margin_usd, max_drawdown_pct, sharpe_ratio,
                     created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    ON CONFLICT (user_id) 
                    DO UPDATE SET 
                        balance_usd = EXCLUDED.balance_usd,
                        btc_balance = EXCLUDED.btc_balance,
                        eth_balance = EXCLUDED.eth_balance,
                        total_trades = EXCLUDED.total_trades,
                        winning_trades = EXCLUDED.winning_trades,
                        losing_trades = EXCLUDED.losing_trades,
                        total_realized_pnl_usd = EXCLUDED.total_realized_pnl_usd,
                        total_unrealized_pnl_usd = EXCLUDED.total_unrealized_pnl_usd,
                        available_margin_usd = EXCLUDED.available_margin_usd,
                        max_drawdown_pct = EXCLUDED.max_drawdown_pct,
                        sharpe_ratio = EXCLUDED.sharpe_ratio,
                        updated_at = NOW()
                    """,
                    (
                        balance_data['user_id'],
                        balance_data['balance_usd'],
                        balance_data.get('btc_balance', 0.0),
                        balance_data.get('eth_balance', 0.0),
                        balance_data.get('total_trades', 0),
                        balance_data.get('winning_trades', 0),
                        balance_data.get('losing_trades', 0),
                        balance_data.get('total_realized_pnl_usd', 0.0),
                        balance_data.get('total_unrealized_pnl_usd', 0.0),
                        balance_data.get('available_margin_usd', 1000000.0),
                        balance_data.get('max_drawdown_pct', 0.0),
                        balance_data.get('sharpe_ratio', 0.0)
                    )
                )
                logger.info(f"✅ Balance guardado en PostgreSQL V2: ${balance_data['balance_usd']:,.2f}")
                return True
        except Exception as e:
            logger.error(f"Error guardando balance en DB: {e}")
        return False
    
    def _save_paper_balance_legacy(self, balance_data: Dict) -> bool:
        """Fallback a memoria temporal si DB falla"""
        if not hasattr(self, '_balances'):
            self._balances = {}
        self._balances[balance_data['user_id']] = balance_data
        logger.warning("⚠️ Balance guardado en memoria temporal - se perderá al reiniciar")
        return True
    
    def _update_paper_balance(self, balance_data: Dict) -> bool:
        """Actualizar balance en PostgreSQL"""
        try:
            if self.database_service and hasattr(self.database_service, 'execute_query'):
                self.database_service.execute_query(
                    """
                    UPDATE paper_trading_balances 
                    SET balance_usd = %s,
                        btc_balance = %s,
                        eth_balance = %s,
                        total_trades = %s,
                        updated_at = NOW()
                    WHERE user_id = %s
                    """,
                    (
                        balance_data['balance_usd'],
                        balance_data.get('btc_balance', 0.0),
                        balance_data.get('eth_balance', 0.0),
                        balance_data.get('total_trades', 0),
                        balance_data['user_id']
                    )
                )
                logger.info(f"✅ Balance actualizado en PostgreSQL")
                return True
        except Exception as e:
            logger.error(f"Error actualizando balance: {e}")
        return False
    
    def _save_paper_trade(self, trade_data: Dict) -> bool:
        """Guardar trade en PostgreSQL - HISTORIAL PERMANENTE
        
        Schema V6.5.3 (Dec 5, 2025): Usa columnas reales de paper_trading_trades:
        id, user_id, symbol, side, quantity, entry_price, exit_price, 
        profit_loss, profit_pct, strategy, status, opened_at, closed_at
        """
        try:
            if self.database_service and hasattr(self.database_service, 'execute_query'):
                self.database_service.execute_query(
                    """
                    INSERT INTO paper_trading_trades 
                    (user_id, symbol, side, quantity, entry_price, strategy, status, opened_at)
                    VALUES (%s, %s, %s, %s, %s, %s, 'open', NOW())
                    """,
                    (
                        trade_data['user_id'],
                        trade_data['symbol'],
                        trade_data['side'],
                        trade_data.get('amount', trade_data.get('quantity', 0)),
                        trade_data.get('price', trade_data.get('entry_price', 0)),
                        trade_data.get('strategy', 'auto_trading_bot')
                    )
                )
                logger.info(f"✅ Trade guardado en PostgreSQL: {trade_data['side']} {trade_data['symbol']}")
                return True
        except Exception as e:
            logger.error(f"Error guardando trade: {e}")
        return False
    
    def _calculate_fee(self, notional_usd: float) -> float:
        """Calcular fee de Kraken (0.26% = 26 bps)"""
        return notional_usd * self.KRAKEN_FEE_RATE
    
    def _open_position_v2(self, user_id: str, symbol: str, base_quantity: float, 
                         entry_price: float, source_strategy: str = 'auto_trading_bot') -> Optional[str]:
        """
        Abrir nueva posición (BUY) con schema V6.5.3
        
        Schema V6.5.3 (Dec 5, 2025): Usa columnas reales de paper_trading_trades:
        id, user_id, symbol, side, quantity, entry_price, exit_price, 
        profit_loss, profit_pct, strategy, status, opened_at, closed_at
        
        Returns:
            trade_id del trade creado, o None si falla
        """
        try:
            if not self.database_service or not hasattr(self.database_service, 'execute_query'):
                logger.error("Database service no disponible")
                return None
            
            # Calcular valores
            quote_notional_usd = base_quantity * entry_price
            fee_usd = self._calculate_fee(quote_notional_usd)
            total_cost = quote_notional_usd + fee_usd
            
            # Insertar trade en paper_trading_trades usando columnas reales
            result = self.database_service.execute_query(
                """
                INSERT INTO paper_trading_trades 
                (user_id, symbol, side, quantity, entry_price, strategy, status, opened_at)
                VALUES (%s, %s, 'buy', %s, %s, %s, 'open', NOW())
                RETURNING id
                """,
                (user_id, symbol, base_quantity, entry_price, source_strategy),
                fetch=True
            )
            
            trade_id = result[0][0] if result and len(result) > 0 else None
            
            if trade_id:
                # Actualizar balance (deducir USD gastado + fees)
                self.database_service.execute_query(
                    """
                    UPDATE paper_trading_balances
                    SET balance_usd = balance_usd - %s,
                        total_trades = total_trades + 1,
                        updated_at = NOW()
                    WHERE user_id = %s
                    """,
                    (total_cost, user_id)
                )
                
                logger.info(f"✅ Posición abierta: {base_quantity:.8f} {symbol} @ ${entry_price:,.2f} (fee: ${fee_usd:.2f})")
                return str(trade_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Error abriendo posición: {e}")
            return None
    
    def _close_position_fifo_v2(self, user_id: str, symbol: str, sell_quantity: float, 
                                exit_price: float) -> Optional[Dict]:
        """
        Cerrar posición FIFO (SELL) - V6.5.3
        
        Schema V6.5.3 (Dec 5, 2025): Usa columnas reales de paper_trading_trades:
        id, user_id, symbol, side, quantity, entry_price, exit_price, 
        profit_loss, profit_pct, strategy, status, opened_at, closed_at
        
        Returns:
            Dict con P&L info o None si falla
        """
        try:
            if not self.database_service or not hasattr(self.database_service, 'execute_query'):
                logger.error("Database service no disponible")
                return None
            
            # Buscar posición abierta más antigua (FIFO) usando columnas reales
            result = self.database_service.execute_query(
                """
                SELECT id, entry_price, quantity, opened_at
                FROM paper_trading_trades
                WHERE user_id = %s AND symbol = %s AND status = 'open'
                ORDER BY opened_at ASC
                LIMIT 1
                """,
                (user_id, symbol),
                fetch=True
            )
            
            if not result or len(result) == 0:
                logger.warning(f"No hay posición abierta para {symbol}")
                return None
            
            trade_id, entry_price_db, quantity_db, opened_at = result[0]
            entry_price_float = float(entry_price_db)
            quantity_float = float(quantity_db)
            
            # Calcular P&L
            quote_notional_usd = quantity_float * exit_price
            fee_usd = self._calculate_fee(quote_notional_usd)
            gross_pnl = (exit_price - entry_price_float) * quantity_float
            profit_pct = ((exit_price / entry_price_float) - 1) * 100 if entry_price_float > 0 else 0
            total_proceeds = quote_notional_usd - fee_usd
            
            # Cerrar trade usando columnas reales
            self.database_service.execute_query(
                """
                UPDATE paper_trading_trades
                SET exit_price = %s,
                    profit_loss = %s,
                    profit_pct = %s,
                    status = 'closed',
                    closed_at = NOW()
                WHERE id = %s
                """,
                (exit_price, gross_pnl, profit_pct, trade_id)
            )
            
            # Actualizar balance
            is_winning_trade = gross_pnl > 0
            
            self.database_service.execute_query(
                """
                UPDATE paper_trading_balances
                SET balance_usd = balance_usd + %s,
                    updated_at = NOW()
                WHERE user_id = %s
                """,
                (total_proceeds, user_id)
            )
            
            logger.info(f"✅ Posición cerrada FIFO: {quantity_float:.8f} {symbol} @ ${exit_price:,.2f} | P&L: ${gross_pnl:,.2f}")
            
            return {
                'trade_id': trade_id,
                'entry_price': entry_price_float,
                'exit_price': exit_price,
                'quantity': quantity_float,
                'gross_pnl': gross_pnl,
                'profit_pct': profit_pct,
                'fee_usd': fee_usd,
                'is_winning_trade': is_winning_trade
            }
            
        except Exception as e:
            logger.error(f"Error cerrando posición: {e}")
            return None
    
    def get_trade_pnl_report(self, user_id: str) -> Dict:
        """
        Reporte P&L detallado con posiciones abiertas/cerradas
        
        Schema V6.5.3 (Dec 5, 2025): Usa columnas reales de paper_trading_trades:
        id, user_id, symbol, side, quantity, entry_price, exit_price, 
        profit_loss, profit_pct, strategy, status, opened_at, closed_at
        
        Returns:
            Dict con summary y lista de trades
        """
        try:
            if not self.database_service or not hasattr(self.database_service, 'execute_query'):
                return {'error': 'Database service no disponible'}
            
            # Obtener todos los trades usando columnas reales
            result = self.database_service.execute_query(
                """
                SELECT id, symbol, side, entry_price, exit_price, 
                       quantity, profit_loss, profit_pct, strategy,
                       status, opened_at, closed_at
                FROM paper_trading_trades
                WHERE user_id = %s
                ORDER BY opened_at DESC
                """,
                (user_id,),
                fetch=True
            )
            
            if not result:
                return {'total_trades': 0, 'trades': []}
            
            trades = []
            total_realized_pnl = 0.0
            total_unrealized_pnl = 0.0
            open_positions = 0
            closed_positions = 0
            
            for row in result:
                trade_id, symbol, side, entry_price, exit_price, quantity, \
                profit_loss, profit_pct, strategy, status, opened_at, closed_at = row
                
                entry_price_float = float(entry_price) if entry_price else 0
                quantity_float = float(quantity) if quantity else 0
                
                # Calcular unrealized P&L para posiciones abiertas
                unrealized_pnl = 0.0
                if status == 'open' and self.trading_service:
                    try:
                        ticker = self.trading_service.get_ticker(symbol)
                        if ticker and 'last' in ticker:
                            current_price = float(ticker['last'])
                            unrealized_pnl = (current_price - entry_price_float) * quantity_float
                            total_unrealized_pnl += unrealized_pnl
                            open_positions += 1
                    except Exception as e:
                        logger.warning(f"Error calculando unrealized P&L: {e}")
                else:
                    closed_positions += 1
                    if profit_loss:
                        total_realized_pnl += float(profit_loss)
                
                trades.append({
                    'trade_id': trade_id,
                    'symbol': symbol,
                    'side': side,
                    'entry_price': entry_price_float,
                    'exit_price': float(exit_price) if exit_price else None,
                    'quantity': quantity_float,
                    'profit_loss': float(profit_loss) if profit_loss else None,
                    'profit_pct': float(profit_pct) if profit_pct else None,
                    'strategy': strategy,
                    'unrealized_pnl': unrealized_pnl if status == 'open' else None,
                    'opened_at': opened_at.isoformat() if opened_at else None,
                    'closed_at': closed_at.isoformat() if closed_at else None,
                    'status': status
                })
            
            return {
                'total_trades': len(trades),
                'open_positions': open_positions,
                'closed_positions': closed_positions,
                'total_realized_pnl_usd': total_realized_pnl,
                'total_unrealized_pnl_usd': total_unrealized_pnl,
                'total_pnl_usd': total_realized_pnl + total_unrealized_pnl,
                'trades': trades
            }
            
        except Exception as e:
            logger.error(f"Error generando reporte P&L: {e}")
            return {'error': str(e)}
