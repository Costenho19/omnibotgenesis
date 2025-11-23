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
        logger.info("=" * 70)
        logger.info("🔧 INICIALIZANDO DatabaseManager")
        logger.info(f"📦 DATABASE_ENTERPRISE_AVAILABLE: {DATABASE_ENTERPRISE_AVAILABLE}")
        
        if DATABASE_ENTERPRISE_AVAILABLE:
            logger.info("🚀 Inicializando DatabaseManager con ENTERPRISE backend")
            self.enterprise_service = DatabaseServiceEnterprise()
            self.connected = self.enterprise_service.connected
            self.using_enterprise = True
            
            health = self.enterprise_service.health_check()
            logger.info(f"🏥 Health Check:")
            logger.info(f"   - psycopg2_available: {health.get('psycopg2_available', False)}")
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
        """
        import psycopg2
        
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise Exception("DATABASE_URL no configurado")
        
        return psycopg2.connect(database_url)
