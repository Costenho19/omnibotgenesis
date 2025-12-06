"""
📊 OMNIX PAPER TRADING SYSTEM V6.4 INSTITUTIONAL+
Sistema de trading simulado con datos REALES de Kraken

CARACTERÍSTICAS:
- Balance virtual inicial: $1,000,000 USD
- Datos reales de Kraken (precios, OHLC, análisis)
- Trades simulados (NO gasta dinero real)
- Performance tracking completo
- Integración con servicios enterprise
- V6.4: Respeta límites personalizados del usuario

USER SETTINGS V6.4:
- Límites de trading por usuario
- Perfil de riesgo personalizado
- Auto-pausa por límite de pérdida
- Estrategias activas por usuario
"""

import logging
import time
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

try:
    from omnix_services.user_settings import UserSettingsService, RiskProfile
    USER_SETTINGS_AVAILABLE = True
except ImportError:
    USER_SETTINGS_AVAILABLE = False
    logger.warning("⚠️ UserSettingsService no disponible en PaperTradingManager")

try:
    from omnix_services.notifications import TradeNotificationService
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False
    TradeNotificationService = None
    logger.info("📢 TradeNotificationService no disponible (opcional)")


class PaperTradingManager:
    """
    Sistema profesional de Paper Trading V6.4 INSTITUTIONAL+
    
    Ejecuta trades simulados con datos reales de Kraken
    para testing y validación de estrategias
    
    V2: Integrado con Risk Management System (RMS)
    V6.4: Respeta límites personalizados de usuario (UserSettingsService)
    """
    
    def __init__(self, database_service=None, trading_service=None, limits_engine=None, 
                 circuit_breaker=None, user_settings_service=None, notification_service=None,
                 telegram_bot=None):
        self.database_service = database_service
        self.trading_service = trading_service
        self.limits_engine = limits_engine
        self.circuit_breaker = circuit_breaker
        self.user_settings_service = user_settings_service
        self.notification_service = notification_service
        self.telegram_bot = telegram_bot
        
        if not self.notification_service and NOTIFICATIONS_AVAILABLE and telegram_bot:
            self.notification_service = TradeNotificationService(
                telegram_bot=telegram_bot,
                database_service=database_service
            )
        
        self.INITIAL_BALANCE_USD = 1_000_000.00
        
        self.KRAKEN_FEE_BPS = 26.0
        self.KRAKEN_FEE_RATE = 0.0026
        
        rms_status = "RMS activo" if limits_engine else "RMS no configurado"
        uss_status = "UserSettings activo" if user_settings_service else "UserSettings no configurado"
        notif_status = "Notificaciones activas" if self.notification_service else "Sin notificaciones"
        logger.info(f"📊 PaperTradingManager V6.4 PREMIUM inicializado - Balance: $1M | {rms_status} | {uss_status} | {notif_status}")
    
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
    
    def execute_paper_trade(self, user_id: str, side: str, symbol: str, amount_usd: float, 
                              source_strategy: str = 'manual') -> Dict:
        """
        Ejecutar trade simulado con datos REALES de Kraken
        
        V2: Usa schema institucional con P&L tracking completo
        V3: Integrado con RMS (Risk Management System)
        V6.4: Respeta límites personalizados del usuario (UserSettingsService)
        
        Args:
            user_id: ID del usuario
            side: 'buy' o 'sell'
            symbol: Par de trading (ej: 'BTC/USD')
            amount_usd: Cantidad en USD a tradear
            source_strategy: Estrategia que origina el trade
            
        Returns:
            Dict con resultado del trade simulado
        """
        try:
            # ⚙️ V6.4: VALIDAR CONFIGURACIÓN PERSONALIZADA DEL USUARIO
            if self.user_settings_service and USER_SETTINGS_AVAILABLE:
                user_check = self.user_settings_service.validate_trade_request(
                    user_id=user_id,
                    symbol=symbol,
                    amount_usd=amount_usd,
                    strategy=source_strategy
                )
                
                if not user_check['allowed']:
                    logger.warning(f"⚙️ USER SETTINGS BLOCKED: {user_check['reason']} para user {user_id}")
                    return {
                        'error': user_check['reason'],
                        'user_settings_blocked': True,
                        'block_type': user_check.get('block_type', 'unknown'),
                        'suggestion': user_check.get('suggestion', ''),
                        'limits': user_check.get('limits', {})
                    }
                
                if user_check.get('warnings'):
                    for warning in user_check['warnings']:
                        logger.info(f"⚠️ User Settings Warning: {warning}")
            
            if self.circuit_breaker and self.circuit_breaker.is_trading_halted(user_id):
                halt_status = self.circuit_breaker.get_halt_status(user_id)
                return {
                    'error': 'Trading detenido por el sistema de riesgo',
                    'halt_reason': halt_status.reason.value if halt_status.reason else 'unknown',
                    'halt_message': halt_status.message,
                    'resume_at': halt_status.resume_at.isoformat() if halt_status.resume_at else None,
                    'rms_blocked': True
                }
            
            if self.limits_engine:
                validation = self.limits_engine.validate_order(
                    user_id=user_id,
                    symbol=symbol,
                    side=side,
                    amount_usd=amount_usd
                )
                
                if not validation.is_valid:
                    logger.warning(f"🚫 RMS BLOCKED: {validation.rejection_reason}")
                    return {
                        'error': f'Orden rechazada por RMS: {validation.rejection_reason}',
                        'rms_blocked': True,
                        'risk_score': validation.risk_score,
                        'breaches': [b.to_dict() for b in validation.breaches] if validation.breaches else []
                    }
                
                if validation.warnings:
                    for warning in validation.warnings:
                        logger.warning(f"⚠️ RMS Warning: {warning}")
            
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
                
                updated_balance = self._get_paper_balance(user_id)
                new_balance_usd = updated_balance['balance_usd'] if updated_balance else (balance['balance_usd'] - total_cost)
                new_btc_balance = updated_balance.get('btc_balance', 0.0) if updated_balance else 0.0
                new_eth_balance = updated_balance.get('eth_balance', 0.0) if updated_balance else 0.0
                
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
                    'new_balance_usd': new_balance_usd,
                    'new_btc_balance': new_btc_balance,
                    'new_eth_balance': new_eth_balance,
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
                
                updated_balance = self._get_paper_balance(user_id)
                new_balance_usd = updated_balance['balance_usd'] if updated_balance else balance['balance_usd']
                new_btc_balance = updated_balance.get('btc_balance', 0.0) if updated_balance else 0.0
                new_eth_balance = updated_balance.get('eth_balance', 0.0) if updated_balance else 0.0
                
                result = {
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
                    'new_balance_usd': new_balance_usd,
                    'new_btc_balance': new_btc_balance,
                    'new_eth_balance': new_eth_balance,
                    'message': f'✅ SELL {crypto_amount:.8f} {symbol} @ ${current_price:,.2f} | P&L: ${close_result["net_realized_pnl_usd"]:+,.2f} ({"WIN" if close_result["is_winning_trade"] else "LOSS"})'
                }
                
                auto_protection = self._check_and_trigger_auto_protection(user_id, close_result['net_realized_pnl_usd'])
                if auto_protection:
                    result['auto_protection_triggered'] = True
                    result['auto_protection'] = auto_protection
                    result['message'] += f"\n\n🛡️ AUTO-PROTECCIÓN: Trading pausado automáticamente"
                
                return result
            else:
                return {'error': 'Side debe ser buy o sell'}
            
        except Exception as e:
            logger.error(f"Error ejecutando paper trade: {e}")
            return {'error': str(e)}
    
    def _check_and_trigger_auto_protection(self, user_id: str, pnl_usd: float) -> Optional[Dict]:
        """
        V6.4: Verificar si se excedieron límites de pérdida y activar auto-protección
        
        Args:
            user_id: ID del usuario
            pnl_usd: P&L del trade recién cerrado (negativo si es pérdida)
            
        Returns:
            Dict con información de auto-pausa si se activó, None si no
        """
        if not self.user_settings_service or not USER_SETTINGS_AVAILABLE:
            return None
        
        try:
            settings = self.user_settings_service.get_user_settings(user_id)
            
            if not settings.protection_settings.auto_pause_enabled:
                return None
            
            daily_pnl = self._get_daily_pnl(user_id)
            
            if daily_pnl is None:
                return None
            
            total_daily_loss_pct = abs(daily_pnl + pnl_usd) / self.INITIAL_BALANCE_USD * 100
            
            if pnl_usd < 0 and total_daily_loss_pct >= settings.protection_settings.daily_loss_limit_pct:
                reason = f"Auto-protección: Pérdida diaria ({total_daily_loss_pct:.1f}%) excede límite ({settings.protection_settings.daily_loss_limit_pct}%)"
                cool_down = settings.protection_settings.cool_down_minutes
                
                success, message = self.user_settings_service.pause_trading(
                    user_id, reason, cool_down
                )
                
                if success:
                    logger.warning(f"🛡️ AUTO-PROTECCIÓN ACTIVADA para user {user_id}: {reason}")
                    return {
                        'auto_paused': True,
                        'reason': reason,
                        'daily_loss_pct': total_daily_loss_pct,
                        'limit_pct': settings.protection_settings.daily_loss_limit_pct,
                        'cool_down_minutes': cool_down,
                        'message': message
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error en auto-protección: {e}")
            return None
    
    def _get_daily_pnl(self, user_id: str) -> Optional[float]:
        """Obtener P&L total del día actual"""
        try:
            if not self.database_service:
                return None
            
            from datetime import date
            today = date.today()
            today_iso = today.isoformat()
            
            try:
                if hasattr(self.database_service, 'execute_query'):
                    query = """
                        SELECT COALESCE(SUM(profit_loss), 0) as daily_pnl
                        FROM paper_trading_trades
                        WHERE user_id = %s 
                        AND status = 'closed'
                        AND DATE(closed_at) = %s
                    """
                    result = self.database_service.execute_query(query, (user_id, today_iso), fetch=True)
                    if result and len(result) > 0:
                        return float(result[0][0]) if result[0][0] else 0.0
            except Exception as query_error:
                logger.warning(f"Error en query daily PnL: {query_error}")
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error obteniendo daily PnL: {e}")
            return None
    
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
                    WHERE user_id = %s::TEXT
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
        """
        ⚠️ DEPRECATED: Fallback a memoria temporal si PostgreSQL falla
        
        NOTA: Este método solo se usa cuando using_enterprise=False
        Los datos se pierden al reiniciar. Usar solo para desarrollo local.
        En producción, using_enterprise=True usa PostgreSQL directamente.
        """
        if not hasattr(self, '_balances'):
            self._balances = {}
        self._balances[balance_data['user_id']] = balance_data
        logger.warning("⚠️ DEPRECATED: Balance guardado en memoria temporal - NO SE PERSISTIRÁ en PostgreSQL")
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
                    WHERE user_id = %s::TEXT
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
    
    def _calculate_fee(self, notional_usd: float) -> float:
        """Calcular fee de Kraken (0.26% = 26 bps)"""
        return notional_usd * self.KRAKEN_FEE_RATE
    
    def _open_position_v2(self, user_id: str, symbol: str, base_quantity: float, 
                         entry_price: float, source_strategy: str = 'auto_trading_bot') -> Optional[str]:
        """
        Abrir nueva posición (BUY) con schema institucional V2
        
        Returns:
            trade_uuid del trade creado, o None si falla
        """
        try:
            logger.info(f"🔧 _open_position_v2: INICIANDO user={user_id}, symbol={symbol}, qty={base_quantity}")
            logger.info(f"🔧 _open_position_v2: database_service = {self.database_service}")
            logger.info(f"🔧 _open_position_v2: has execute_query = {hasattr(self.database_service, 'execute_query') if self.database_service else False}")
            
            if not self.database_service or not hasattr(self.database_service, 'execute_query'):
                logger.error("❌ _open_position_v2: Database service no disponible")
                return None
            
            quote_notional_usd = base_quantity * entry_price
            fee_usd = self._calculate_fee(quote_notional_usd)
            total_cost = quote_notional_usd + fee_usd
            
            logger.info(f"🔧 _open_position_v2: Ejecutando INSERT en paper_trading_trades...")
            
            result = self.database_service.execute_query(
                """
                INSERT INTO paper_trading_trades 
                (user_id, symbol, side, entry_price, quantity, 
                 profit_loss, profit_pct, strategy, status, opened_at)
                VALUES (%s, %s, 'buy', %s, %s, 0, 0, %s, 'open', NOW())
                RETURNING id
                """,
                (user_id, symbol, entry_price, base_quantity, source_strategy)
            )
            
            logger.info(f"🔧 _open_position_v2: INSERT result = {result}")
            
            trade_id = result[0][0] if result and len(result) > 0 else None
            trade_uuid = str(trade_id) if trade_id else None
            
            logger.info(f"🔧 _open_position_v2: trade_id = {trade_id}, trade_uuid = {trade_uuid}")
            
            if trade_uuid:
                self.database_service.execute_query(
                    """
                    UPDATE paper_trading_balances
                    SET balance_usd = balance_usd - %s,
                        available_margin_usd = available_margin_usd - %s,
                        total_trades = total_trades + 1,
                        updated_at = NOW()
                    WHERE user_id = %s::TEXT
                    """,
                    (total_cost, total_cost, user_id)
                )
                
                logger.info(f"✅ Posición abierta: {base_quantity:.8f} {symbol} @ ${entry_price:,.2f} (fee: ${fee_usd:.2f})")
                
                if self.notification_service:
                    try:
                        trade_data = {
                            'symbol': symbol,
                            'entry_price': entry_price,
                            'quantity': base_quantity,
                            'amount_usd': quote_notional_usd,
                            'strategy': source_strategy,
                            'signal_strength': 'MODERATE',
                            'confidence': 50.0
                        }
                        self.notification_service.notify_trade_sync('buy', trade_data, user_id)
                        logger.info(f"📢 Notificación de BUY enviada para {symbol}")
                    except Exception as notif_err:
                        logger.warning(f"Error enviando notificación BUY: {notif_err}")
                
                return str(trade_uuid)
            
            return None
            
        except Exception as e:
            logger.error(f"Error abriendo posición: {e}")
            return None
    
    def _close_position_fifo_v2(self, user_id: str, symbol: str, sell_quantity: float, 
                                exit_price: float) -> Optional[Dict]:
        """
        Cerrar posición FIFO (SELL) - V2: Soporta ventas parciales institucionales
        
        Returns:
            Dict con P&L info o None si falla
        """
        try:
            logger.info(f"🔧 _close_position_fifo_v2: INICIANDO SELL user={user_id}, symbol={symbol}, qty={sell_quantity}, price={exit_price}")
            logger.info(f"🔧 _close_position_fifo_v2: database_service = {self.database_service}")
            logger.info(f"🔧 _close_position_fifo_v2: has execute_query = {hasattr(self.database_service, 'execute_query') if self.database_service else False}")
            
            if not self.database_service or not hasattr(self.database_service, 'execute_query'):
                logger.error("❌ _close_position_fifo_v2: Database service no disponible - ABORTANDO SELL")
                return None
            
            logger.info(f"🔍 _close_position_fifo_v2: Buscando posición abierta para user={user_id}, symbol={symbol}")
            
            # Buscar posición abierta más antigua (FIFO) - usando columnas correctas del schema
            result = self.database_service.execute_query(
                """
                SELECT id, entry_price, quantity, opened_at
                FROM paper_trading_trades
                WHERE user_id = %s::TEXT AND symbol = %s AND status = 'open' AND closed_at IS NULL
                ORDER BY opened_at ASC
                LIMIT 1
                """,
                (user_id, symbol)
            )
            
            logger.info(f"🔍 _close_position_fifo_v2: Resultado SELECT = {result}")
            
            if not result or len(result) == 0:
                logger.warning(f"No hay posición abierta para {symbol}")
                return None
            
            trade_id, entry_price, quantity, opened_at = result[0]
            base_quantity = float(quantity)
            
            # V2: Ajustar sell_quantity si es mayor que la posición disponible
            actual_sell_quantity = min(sell_quantity, base_quantity)
            is_partial_close = actual_sell_quantity < base_quantity
            remaining_quantity = base_quantity - actual_sell_quantity
            
            # Calcular P&L basado en cantidad REAL vendida
            quote_notional_usd = actual_sell_quantity * exit_price
            fee_sell = self._calculate_fee(quote_notional_usd)
            # Fee de compra proporcional a lo vendido
            fee_buy_proportional = self._calculate_fee(actual_sell_quantity * float(entry_price))
            gross_pnl_usd = (exit_price - float(entry_price)) * actual_sell_quantity
            net_realized_pnl_usd = gross_pnl_usd - fee_buy_proportional - fee_sell
            total_proceeds = quote_notional_usd - fee_sell
            
            # Calcular duración y porcentaje P&L
            duration_seconds = int((datetime.now() - opened_at).total_seconds())
            profit_pct = ((exit_price / float(entry_price)) - 1) * 100
            
            if is_partial_close:
                logger.info(f"🔄 Ejecutando UPDATE venta parcial: quantity={remaining_quantity}, trade_id={trade_id}")
                try:
                    self.database_service.execute_query(
                        """
                        UPDATE paper_trading_trades
                        SET quantity = %s
                        WHERE id = %s
                        """,
                        (remaining_quantity, trade_id)
                    )
                    logger.info(f"✅ UPDATE VENTA PARCIAL EJECUTADO - trade_id={trade_id}")
                except Exception as update_err:
                    logger.error(f"❌ ERROR en UPDATE venta parcial: {update_err}")
                    raise
                logger.info(f"✅ Venta parcial FIFO: {actual_sell_quantity:.8f} de {base_quantity:.8f} {symbol} | Restante: {remaining_quantity:.8f}")
            else:
                logger.info(f"🔄 Ejecutando UPDATE cierre completo: exit_price={exit_price}, profit_loss={net_realized_pnl_usd}, profit_pct={profit_pct}, trade_id={trade_id}")
                try:
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
                        (exit_price, net_realized_pnl_usd, profit_pct, trade_id)
                    )
                    logger.info(f"✅ UPDATE CIERRE COMPLETO EJECUTADO - trade_id={trade_id}, status='closed'")
                except Exception as update_err:
                    logger.error(f"❌ ERROR en UPDATE cierre completo: {update_err}")
                    raise
                logger.info(f"✅ Posición cerrada FIFO en PostgreSQL: {actual_sell_quantity:.8f} {symbol} @ ${exit_price:,.2f} | P&L: ${net_realized_pnl_usd:,.2f}")
            
            is_winning_trade = net_realized_pnl_usd > 0
            
            winning_increment = 1 if (is_winning_trade and not is_partial_close) else 0
            losing_increment = 1 if (not is_winning_trade and not is_partial_close) else 0
            
            logger.info(f"🔧 Actualizando balance: proceeds=${total_proceeds:.2f}, pnl=${net_realized_pnl_usd:.2f}, win={winning_increment}, loss={losing_increment}")
            try:
                self.database_service.execute_query(
                    """
                    UPDATE paper_trading_balances
                    SET balance_usd = balance_usd + %s,
                        available_margin_usd = available_margin_usd + %s,
                        total_realized_pnl_usd = total_realized_pnl_usd + %s,
                        winning_trades = winning_trades + %s,
                        losing_trades = losing_trades + %s,
                        updated_at = NOW()
                    WHERE user_id = %s::TEXT
                    """,
                    (total_proceeds, total_proceeds, net_realized_pnl_usd,
                     winning_increment, losing_increment, user_id)
                )
                logger.info(f"✅ UPDATE BALANCE EJECUTADO para user={user_id}")
            except Exception as bal_err:
                logger.error(f"❌ ERROR actualizando balance: {bal_err}")
                raise
            
            trade_result = {
                'trade_uuid': str(trade_id),
                'symbol': symbol,
                'entry_price': float(entry_price),
                'exit_price': exit_price,
                'base_quantity': actual_sell_quantity,
                'original_quantity': base_quantity,
                'remaining_quantity': remaining_quantity,
                'is_partial_close': is_partial_close,
                'gross_pnl_usd': gross_pnl_usd,
                'net_realized_pnl_usd': net_realized_pnl_usd,
                'profit_pct': profit_pct,
                'fee_buy': fee_buy_proportional,
                'fee_sell': fee_sell,
                'duration_seconds': duration_seconds,
                'is_winning_trade': is_winning_trade
            }
            
            if self.notification_service and not is_partial_close:
                try:
                    self.notification_service.notify_trade_sync('sell', trade_result, user_id)
                    logger.info(f"📢 Notificación de SELL enviada para {symbol}")
                except Exception as notif_err:
                    logger.warning(f"Error enviando notificación: {notif_err}")
            
            return trade_result
            
        except Exception as e:
            logger.error(f"Error cerrando posición: {e}")
            return None
    
    def get_trade_pnl_report(self, user_id: str) -> Dict:
        """
        Reporte P&L detallado con posiciones abiertas/cerradas
        
        Returns:
            Dict con summary y lista de trades
        """
        try:
            if not self.database_service or not hasattr(self.database_service, 'execute_query'):
                return {'error': 'Database service no disponible'}
            
            # Obtener todos los trades - usando columnas correctas del schema
            result = self.database_service.execute_query(
                """
                SELECT id, symbol, side, entry_price, exit_price, 
                       quantity, profit_loss, profit_pct, strategy,
                       status, opened_at, closed_at
                FROM paper_trading_trades
                WHERE user_id = %s::TEXT
                ORDER BY opened_at DESC
                """,
                (user_id,)
            )
            
            if not result:
                return {'total_trades': 0, 'trades': []}
            
            trades = []
            total_realized_pnl = 0.0
            total_unrealized_pnl = 0.0
            open_positions = 0
            closed_positions = 0
            
            for row in result:
                # Columnas: id, symbol, side, entry_price, exit_price, quantity, profit_loss, profit_pct, strategy, status, opened_at, closed_at
                trade_id, symbol, side, entry_price, exit_price, quantity, \
                profit_loss, profit_pct, strategy, status, opened_at, closed_at = row
                
                base_quantity = float(quantity) if quantity else 0
                
                # Calcular unrealized P&L para posiciones abiertas
                unrealized_pnl = 0.0
                if status == 'open' and self.trading_service:
                    try:
                        ticker = self.trading_service.get_ticker(symbol)
                        if ticker and 'last' in ticker:
                            current_price = float(ticker['last'])
                            unrealized_pnl = (current_price - float(entry_price)) * base_quantity
                            total_unrealized_pnl += unrealized_pnl
                            open_positions += 1
                    except Exception as e:
                        logger.warning(f"Error calculando unrealized P&L: {e}")
                else:
                    closed_positions += 1
                    if profit_loss:
                        total_realized_pnl += float(profit_loss)
                
                trades.append({
                    'trade_uuid': str(trade_id),
                    'symbol': symbol,
                    'side': side,
                    'entry_price': float(entry_price) if entry_price else 0,
                    'exit_price': float(exit_price) if exit_price else None,
                    'base_quantity': base_quantity,
                    'strategy': strategy or 'OMNIX',
                    'net_realized_pnl_usd': float(profit_loss) if profit_loss else None,
                    'profit_pct': float(profit_pct) if profit_pct else None,
                    'unrealized_pnl_usd': unrealized_pnl if status == 'open' else None,
                    'opened_at': opened_at.isoformat() if opened_at else None,
                    'closed_at': closed_at.isoformat() if closed_at else None,
                    'status': status or 'open'
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
    
    def get_open_positions(self, user_id: str) -> list:
        """
        Obtener posiciones abiertas del usuario
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Lista de posiciones abiertas
        """
        try:
            if not self.database_service or not hasattr(self.database_service, 'execute_query'):
                logger.warning("get_open_positions: Database service no disponible")
                return []
            
            result = self.database_service.execute_query(
                """
                SELECT id, symbol, side, quantity, entry_price, opened_at
                FROM paper_trading_trades
                WHERE user_id = %s::TEXT AND status = 'open' AND closed_at IS NULL
                ORDER BY opened_at DESC
                """,
                (user_id,)
            )
            
            if not result:
                return []
            
            positions = []
            for row in result:
                trade_id, symbol, side, quantity, entry_price, opened_at = row
                positions.append({
                    'trade_id': str(trade_id),
                    'symbol': symbol,
                    'side': side,
                    'quantity': float(quantity) if quantity else 0,
                    'entry_price': float(entry_price) if entry_price else 0,
                    'opened_at': opened_at.isoformat() if opened_at else None
                })
            
            return positions
            
        except Exception as e:
            logger.error(f"Error obteniendo posiciones abiertas: {e}")
            return []
    
    def has_open_position_for_symbol(self, user_id: str, symbol: str) -> Dict:
        """
        Verificar si existe posición abierta para un símbolo específico
        
        Args:
            user_id: ID del usuario
            symbol: Par de trading (ej: BTC/USD, ETH/USD)
        
        Returns:
            Dict con:
              - has_position: bool
              - position: dict con detalles si existe
              - side: 'buy' o None
              - quantity: cantidad abierta
        """
        try:
            if not self.database_service or not hasattr(self.database_service, 'execute_query'):
                logger.warning("has_open_position_for_symbol: Database service no disponible")
                return {'has_position': False, 'position': None, 'side': None, 'quantity': 0}
            
            result = self.database_service.execute_query(
                """
                SELECT id, side, quantity, entry_price, opened_at
                FROM paper_trading_trades
                WHERE user_id = %s::TEXT 
                  AND symbol = %s 
                  AND status = 'open' 
                  AND closed_at IS NULL
                ORDER BY opened_at DESC
                LIMIT 1
                """,
                (user_id, symbol)
            )
            
            if not result or len(result) == 0:
                return {'has_position': False, 'position': None, 'side': None, 'quantity': 0}
            
            row = result[0]
            trade_id, side, quantity, entry_price, opened_at = row
            
            position = {
                'trade_id': str(trade_id),
                'symbol': symbol,
                'side': side,
                'quantity': float(quantity) if quantity else 0,
                'entry_price': float(entry_price) if entry_price else 0,
                'opened_at': opened_at.isoformat() if opened_at else None
            }
            
            logger.info(f"📊 has_open_position_for_symbol: {symbol} -> {side} qty={quantity}")
            
            return {
                'has_position': True,
                'position': position,
                'side': side,
                'quantity': float(quantity) if quantity else 0
            }
            
        except Exception as e:
            logger.error(f"Error verificando posición para {symbol}: {e}")
            return {'has_position': False, 'position': None, 'side': None, 'quantity': 0}
