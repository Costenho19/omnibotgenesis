import logging
import os

logger = logging.getLogger(__name__)

try:
    from omnix_services.database_service import DatabaseServiceEnterprise
    DATABASE_ENTERPRISE_AVAILABLE = True
except ImportError:
    DATABASE_ENTERPRISE_AVAILABLE = False


class DatabaseManager:
    """
    Adapter class - mantiene compatibilidad con código legacy
    pero usa DatabaseServiceEnterprise internamente
    """
    def __init__(self):
        import os
        logger.info("=" * 70)
        logger.info("🔧 INICIALIZANDO DatabaseManager")
        logger.info(f"📦 DATABASE_ENTERPRISE_AVAILABLE: {DATABASE_ENTERPRISE_AVAILABLE}")
        
        db_url = os.environ.get('DATABASE_URL')
        if db_url:
            logger.info(f"✅ DATABASE_URL DETECTADA ({len(db_url)} caracteres)")
        else:
            logger.error("❌ DATABASE_URL NO ENCONTRADA - Memoria NO funcionará")
        
        if DATABASE_ENTERPRISE_AVAILABLE:
            logger.info("🚀 Inicializando DatabaseManager con ENTERPRISE backend")
            self.enterprise_service = DatabaseServiceEnterprise()
            self.connected = self.enterprise_service.connected
            self.using_enterprise = True
            
            health = self.enterprise_service.health_check()
            logger.info(f"🏥 Health Check:")
            logger.info(f"   - psycopg_available: {health.get('psycopg_available', False)}")
            logger.info(f"   - database_url_configured: {health.get('database_url_configured', False)}")
            logger.info(f"   - database_connected: {health.get('database_connected', False)}")
            
            if self.connected:
                logger.info("✅ DatabaseManager CONECTADO exitosamente")
            else:
                logger.error("❌ DatabaseManager NO CONECTADO - Revisar logs arriba")
        else:
            logger.warning("⚠️ Fallback a sistema legacy - Database Enterprise no disponible")
            self.connected = True
            self.using_enterprise = False
        
        logger.info(f"📊 Estado final - Enterprise: {self.using_enterprise}, Connected: {self.connected}")
        logger.info("=" * 70)

    
    def save_balance_snapshot(self, user_id, balance_data):
        if self.using_enterprise:
            return self.enterprise_service.save_balance_snapshot(user_id, balance_data)
        return False
    
    def get_balance_history(self, user_id, days=30):
        if self.using_enterprise:
            return self.enterprise_service.get_balance_history(user_id, days)
        return []
    
    def calculate_performance_metrics(self, history):
        if self.using_enterprise:
            return self.enterprise_service.calculate_performance_metrics(history)
        return None
    
    def health_check(self):
        if self.using_enterprise:
            return self.enterprise_service.health_check()
        return {'connected': self.connected, 'enterprise': False}
    
    def get_connection(self):
        """
        Retorna conexión PostgreSQL directa para módulos que la necesitan
        como AI Risk Guardian
        
        UPDATED Nov 29, 2025: Usa psycopg3 via DatabaseServiceEnterprise
        """
        if self.using_enterprise:
            return self.enterprise_service._get_connection()
        
        raise Exception("DATABASE_URL no configurado - Enterprise service no disponible")
    
    def ensure_user_exists(self, user_id: str, username: str = None, 
                           first_name: str = None, language_code: str = 'auto') -> bool:
        """
        Garantizar que el usuario existe en la tabla users.
        CRITICAL: Debe llamarse ANTES de cualquier write a tablas con FK a users.
        ADDED Nov 28, 2025: Fix para FK constraint violations
        UPDATED Dec 19, 2025: Default 'auto' = AI auto-detection de idioma
        """
        if self.using_enterprise:
            return self.enterprise_service.ensure_user_exists(user_id, username, first_name, language_code)
        return False
    
    def save_conversation(self, user_id: str, user_message: str, ai_response: str, language: str = 'es') -> bool:
        """
        Guardar conversación en la base de datos
        FIXED Nov 26, 2025: Método faltante agregado
        """
        if self.using_enterprise:
            return self.enterprise_service.save_conversation(user_id, user_message, ai_response, language)
        return False
    
    def get_conversation_history(self, chat_id: int, limit: int = 10) -> list:
        """
        Obtener historial de conversaciones
        FIXED Nov 26, 2025: Método faltante agregado
        """
        if self.using_enterprise:
            return self.enterprise_service.get_conversation_history(chat_id, limit)
        return []
    
    def execute_query(self, sql: str, params: tuple = None, fetch: bool = None):
        """
        Ejecutar query SQL genérica - Delegado a enterprise_service
        
        FIXED Nov 30, 2025: Método faltante - causaba que paper trading 
        no guardara trades en PostgreSQL
        
        Args:
            sql: Query SQL a ejecutar
            params: Parámetros para la query (tuple)
            fetch: Si True, retorna resultados. Si None, auto-detecta.
            
        Returns:
            Lista de tuplas con resultados si es SELECT/RETURNING, None si es INSERT/UPDATE
        """
        if self.using_enterprise and hasattr(self.enterprise_service, 'execute_query'):
            return self.enterprise_service.execute_query(sql, params, fetch)
        logger.error("❌ execute_query no disponible - enterprise_service no configurado")
        return None
    
    def get_paper_trading_balance(self, user_id: str) -> dict:
        """
        Obtener balance de paper trading del usuario
        FIXED Nov 30, 2025: RMS necesita este método para calcular drawdown
        """
        if self.using_enterprise:
            return self.enterprise_service.get_paper_trading_balance(user_id)
        return {'balance': 1_000_000.0, 'available': 1_000_000.0, 'total_pnl': 0.0}
    
    def get_risk_limits(self, user_id: str) -> list:
        """
        Obtener límites de riesgo del usuario
        FIXED Nov 30, 2025: RMS LimitsEngine necesita este método
        """
        if self.using_enterprise:
            return self.enterprise_service.get_risk_limits(user_id)
        return []
    
    def get_circuit_breaker_status(self, user_id: str) -> dict:
        """
        Obtener estado del circuit breaker
        FIXED Nov 30, 2025: RMS CircuitBreaker necesita este método
        """
        if self.using_enterprise:
            return self.enterprise_service.get_circuit_breaker_status(user_id)
        return None
    
    def get_daily_trading_stats(self, user_id: str) -> dict:
        """
        Obtener estadísticas de trading del día
        FIXED Nov 30, 2025: RMS necesita este método para PnL diario
        """
        if self.using_enterprise:
            return self.enterprise_service.get_daily_trading_stats(user_id)
        return None
    
    def get_open_positions(self, user_id: str) -> list:
        """
        Obtener posiciones abiertas del usuario
        FIXED Nov 30, 2025: RMS necesita este método para exposición
        """
        if self.using_enterprise:
            return self.enterprise_service.get_open_positions(user_id)
        return []
    
    def get_due_evaluations(self) -> list:
        """
        Obtener evaluaciones pendientes que ya deben procesarse
        FIXED Dec 2, 2025: Método faltante que bloqueaba módulo de evaluación
        
        Returns:
            Lista de evaluaciones pendientes donde due_time <= NOW()
        """
        if self.using_enterprise:
            try:
                sql = """
                    SELECT id, trade_id, evaluation_type, due_time, 
                           conditions, status, created_at
                    FROM pending_evaluations 
                    WHERE due_time <= NOW() 
                    AND status = 'pending'
                    ORDER BY due_time ASC
                    LIMIT 100
                """
                rows = self.enterprise_service.execute_query(sql, fetch=True)
                if rows:
                    columns = ['id', 'trade_id', 'evaluation_type', 'due_time', 
                               'conditions', 'status', 'created_at']
                    return [dict(zip(columns, row)) for row in rows]
                return []
            except Exception as e:
                logger.warning(f"⚠️ Error obteniendo evaluaciones pendientes: {e}")
                return []
        return []
    
    def mark_evaluation_processed(self, evaluation_id: int, result: str = 'processed') -> bool:
        """
        Marcar una evaluación como procesada
        ADDED Dec 2, 2025: Complemento de get_due_evaluations
        """
        if self.using_enterprise:
            try:
                sql = """
                    UPDATE pending_evaluations 
                    SET status = %s, processed_at = NOW()
                    WHERE id = %s
                """
                self.enterprise_service.execute_query(sql, (result, evaluation_id), fetch=False)
                return True
            except Exception as e:
                logger.warning(f"⚠️ Error marcando evaluación {evaluation_id}: {e}")
                return False
        return False
    
    def log_risk_event(self, risk_type: str, risk_level: str, description: str,
                       action_taken: str, metadata: dict = None, user_id: int = None) -> bool:
        """
        Registrar evento del AI Risk Guardian
        FIXED Dec 5, 2025: Método faltante que causaba error en cada ciclo de trading
        
        Error original: 'DatabaseManager' object has no attribute 'log_risk_event'
        
        Args:
            risk_type: Tipo de riesgo (e.g., 'EXCESSIVE_TRADE_SIZE', 'DRAWDOWN_WARNING')
            risk_level: Nivel de riesgo (e.g., 'WARNING', 'CRITICAL')
            description: Descripción del evento
            action_taken: Acción tomada (e.g., 'REDUCED_POSITION', 'BLOCKED')
            metadata: Datos adicionales (dict)
            user_id: ID del usuario (opcional)
            
        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        if self.using_enterprise:
            return self.enterprise_service.log_risk_event(
                risk_type=risk_type,
                risk_level=risk_level,
                description=description,
                action_taken=action_taken,
                metadata=metadata,
                user_id=user_id
            )
        return False
