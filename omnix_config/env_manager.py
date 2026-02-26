#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNIX V6.0 ULTRA - Centralized Environment Configuration Manager
Sistema centralizado de gestión de variables de entorno con precedencia, validación y seguridad
Desarrollado por Harold Nunes - Noviembre 2025
"""

import os
import sys
import logging
import re
import threading
from typing import Any, Dict, List, Optional, Set
from enum import Enum

logger = logging.getLogger(__name__)


class EnvSource(Enum):
    """Fuentes de variables de entorno con precedencia"""
    REPLIT_SECRET = "Replit Secret"
    ENV_LOCAL = ".env.local"
    DEFAULT = "Default Value"
    NOT_SET = "Not Set"


class EnvCategory(Enum):
    """Categorías de variables de entorno"""
    TELEGRAM = "telegram"
    AI_APIS = "ai_apis"
    TRADING_APIS = "trading_apis"
    DATABASE = "database"
    SECURITY = "security"
    APP_SETTINGS = "app_settings"
    MONITORING = "monitoring"
    CELERY = "celery"


class EnvConfig:
    """
    Singleton thread-safe para gestión centralizada de variables de entorno
    
    Precedencia de carga: Replit Secrets (os.environ) > .env.local > defaults
    
    Features:
    - Validación de formato (API keys, URLs, tokens)
    - Categorización de variables
    - Logging de fuentes de carga
    - Métodos get() y get_required()
    - Thread-safe singleton pattern
    """
    
    _instance = None
    _lock = threading.Lock()
    
    # Catálogo completo de variables con metadata
    VARIABLE_CATALOG = {
        # TELEGRAM
        'TELEGRAM_BOT_TOKEN': {
            'category': EnvCategory.TELEGRAM,
            'required': True,
            'validator': lambda x: bool(re.match(r'^\d+:[A-Za-z0-9_-]{35}$', x)),
            'description': 'Token del bot de Telegram',
            'example': '123456789:ABCdefGHIjklMNOpqrsTUVwxyz1234567890'
        },
        'TELEGRAM_ADMIN_USER_ID': {
            'category': EnvCategory.TELEGRAM,
            'required': False,
            'validator': lambda x: x.isdigit() and len(x) >= 8,
            'description': 'User ID del administrador de Telegram (configurable via settings.py default)',
            'example': '123456789'
        },
        
        # AI APIS
        'GEMINI_API_KEY': {
            'category': EnvCategory.AI_APIS,
            'required': False,
            'validator': lambda x: len(x) > 20,
            'description': 'API Key de Google Gemini',
            'example': 'AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
        },
        'OPENAI_API_KEY': {
            'category': EnvCategory.AI_APIS,
            'required': False,
            'validator': lambda x: len(x) > 20,
            'description': 'API Key de OpenAI GPT-4',
            'example': 'sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
        },
        'ANTHROPIC_API_KEY': {
            'category': EnvCategory.AI_APIS,
            'required': False,
            'validator': lambda x: x.startswith('sk-ant-') and len(x) > 40,
            'description': 'API Key de Anthropic Claude',
            'example': 'sk-ant-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
        },
        
        # TRADING APIS
        'KRAKEN_API_KEY': {
            'category': EnvCategory.TRADING_APIS,
            'required': False,
            'validator': lambda x: len(x) > 30,
            'description': 'API Key de Kraken Exchange',
            'example': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
        },
        'KRAKEN_API_SECRET': {
            'category': EnvCategory.TRADING_APIS,
            'required': False,
            'validator': lambda x: len(x) > 30,
            'description': 'API Secret de Kraken Exchange',
            'example': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
        },
        'ALPACA_API_KEY': {
            'category': EnvCategory.TRADING_APIS,
            'required': False,
            'validator': lambda x: len(x) > 15,
            'description': 'API Key de Alpaca Trading (Stocks)',
            'example': 'PKXXXXXXXXXXXXXXXXXXXXX'
        },
        'ALPACA_API_SECRET': {
            'category': EnvCategory.TRADING_APIS,
            'required': False,
            'validator': lambda x: len(x) > 30,
            'description': 'API Secret de Alpaca Trading',
            'example': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
        },
        
        # DATABASE
        'DATABASE_URL': {
            'category': EnvCategory.DATABASE,
            'required': False,
            'validator': lambda x: x.startswith(('postgres://', 'postgresql://', 'sqlite://')),
            'description': 'URL de conexión a base de datos',
            'example': 'postgresql://user:pass@host:5432/dbname'
        },
        'REDIS_URL': {
            'category': EnvCategory.DATABASE,
            'required': False,
            'validator': lambda x: x.startswith(('redis://', 'rediss://')),
            'description': 'URL de conexión a Redis',
            'example': 'redis://localhost:6379/0'
        },
        'REDIS_HOST': {
            'category': EnvCategory.DATABASE,
            'required': False,
            'default': 'localhost',
            'validator': lambda x: len(x) > 0,
            'description': 'Host de Redis',
            'example': 'localhost'
        },
        'REDIS_PORT': {
            'category': EnvCategory.DATABASE,
            'required': False,
            'default': '6379',
            'validator': lambda x: x.isdigit() and 1 <= int(x) <= 65535,
            'description': 'Puerto de Redis',
            'example': '6379'
        },
        'REDIS_DB': {
            'category': EnvCategory.DATABASE,
            'required': False,
            'default': '0',
            'validator': lambda x: x.isdigit() and 0 <= int(x) <= 15,
            'description': 'Número de base de datos Redis (0-15)',
            'example': '0'
        },
        'REDIS_PASSWORD': {
            'category': EnvCategory.DATABASE,
            'required': False,
            'validator': lambda x: True,
            'description': 'Password de Redis (opcional)',
            'example': 'your_redis_password'
        },
        
        # SECURITY
        'SESSION_SECRET': {
            'category': EnvCategory.SECURITY,
            'required': False,
            'validator': lambda x: len(x) >= 32,
            'description': 'Secret key para sesiones (min 32 chars)',
            'example': 'your-very-long-secret-key-here-min-32-chars'
        },
        'ENCRYPTION_KEY': {
            'category': EnvCategory.SECURITY,
            'required': False,
            'validator': lambda x: len(x) >= 32,
            'description': 'Key de encriptación (min 32 chars)',
            'example': 'your-encryption-key-here-min-32-chars'
        },
        'SECRET_KEY': {
            'category': EnvCategory.SECURITY,
            'required': False,
            'default': None,
            'validator': lambda x: len(x) >= 20,
            'description': 'Secret key general de la aplicación (debe configurarse como variable de entorno)',
            'example': 'set-via-environment-variable-only'
        },
        
        # APP SETTINGS
        'PORT': {
            'category': EnvCategory.APP_SETTINGS,
            'required': False,
            'default': '8000',
            'validator': lambda x: x.isdigit() and 1 <= int(x) <= 65535,
            'description': 'Puerto del servidor web',
            'example': '8000'
        },
        'HOST': {
            'category': EnvCategory.APP_SETTINGS,
            'required': False,
            'default': '0.0.0.0',
            'validator': lambda x: True,
            'description': 'Host del servidor web',
            'example': '0.0.0.0'
        },
        'STOCK_TRADING_ENABLED': {
            'category': EnvCategory.APP_SETTINGS,
            'required': False,
            'default': 'true',
            'validator': lambda x: x.lower() in ['true', 'false'],
            'description': 'Habilitar trading de acciones (true/false)',
            'example': 'true'
        },
        'PAPER_MODE': {
            'category': EnvCategory.APP_SETTINGS,
            'required': False,
            'default': 'true',
            'validator': lambda x: x.lower() in ['true', 'false'],
            'description': 'Modo paper trading (true/false)',
            'example': 'true'
        },
        'LOG_LEVEL': {
            'category': EnvCategory.APP_SETTINGS,
            'required': False,
            'default': 'INFO',
            'validator': lambda x: x.upper() in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            'description': 'Nivel de logging',
            'example': 'INFO'
        },
        'ENVIRONMENT': {
            'category': EnvCategory.APP_SETTINGS,
            'required': False,
            'default': 'development',
            'validator': lambda x: x in ['development', 'production', 'staging', 'test'],
            'description': 'Entorno de ejecución',
            'example': 'production'
        },
        'DEBUG': {
            'category': EnvCategory.APP_SETTINGS,
            'required': False,
            'default': 'false',
            'validator': lambda x: x.lower() in ['true', 'false'],
            'description': 'Modo debug (true/false)',
            'example': 'false'
        },
        
        # MONITORING
        'ENABLE_METRICS': {
            'category': EnvCategory.MONITORING,
            'required': False,
            'default': 'true',
            'validator': lambda x: x.lower() in ['true', 'false'],
            'description': 'Habilitar métricas de monitoreo',
            'example': 'true'
        },
        'METRICS_PORT': {
            'category': EnvCategory.MONITORING,
            'required': False,
            'default': '9090',
            'validator': lambda x: x.isdigit() and 1 <= int(x) <= 65535,
            'description': 'Puerto para métricas Prometheus',
            'example': '9090'
        },
        'SENTRY_DSN': {
            'category': EnvCategory.MONITORING,
            'required': False,
            'validator': lambda x: x.startswith('https://') and 'sentry.io' in x,
            'description': 'Sentry DSN para error tracking',
            'example': 'https://xxxxx@xxxxx.ingest.sentry.io/xxxxx'
        },
        
        # CELERY
        'CELERY_BROKER_URL': {
            'category': EnvCategory.CELERY,
            'required': False,
            'default': 'redis://localhost:6379/1',
            'validator': lambda x: x.startswith(('redis://', 'rediss://', 'amqp://')),
            'description': 'URL del broker Celery (Redis/RabbitMQ)',
            'example': 'redis://localhost:6379/1'
        },
        'CELERY_RESULT_BACKEND': {
            'category': EnvCategory.CELERY,
            'required': False,
            'default': 'redis://localhost:6379/2',
            'validator': lambda x: x.startswith(('redis://', 'rediss://', 'rpc://')),
            'description': 'URL del backend de resultados Celery',
            'example': 'redis://localhost:6379/2'
        }
    }
    
    def __new__(cls):
        """Thread-safe singleton pattern"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(EnvConfig, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize configuration (only once)"""
        if self._initialized:
            return
        
        with self._lock:
            if self._initialized:
                return
            
            self._env_data: Dict[str, Any] = {}
            self._env_sources: Dict[str, EnvSource] = {}
            self._dotenv_available = False
            
            # Try to import python-dotenv
            try:
                from dotenv import load_dotenv
                self._dotenv_available = True
                logger.info("✅ python-dotenv disponible")
            except ImportError:
                logger.info("⚠️ python-dotenv no instalado - usando solo os.environ")
            
            # Load configuration
            self._load_configuration()
            self._initialized = True
    
    def _load_configuration(self):
        """Load configuration with precedence: Replit Secrets > .env.local > defaults"""
        logger.info("=" * 70)
        logger.info("🔧 CARGANDO CONFIGURACIÓN DE ENTORNO - OMNIX V6.0")
        logger.info("=" * 70)
        
        # Step 1: Load .env.local if available
        if self._dotenv_available:
            try:
                from dotenv import load_dotenv
                env_local_path = os.path.join(os.getcwd(), '.env.local')
                if os.path.exists(env_local_path):
                    load_dotenv(env_local_path, override=False)
                    logger.info(f"✅ Cargado .env.local desde: {env_local_path}")
                else:
                    logger.info("ℹ️ Archivo .env.local no encontrado (opcional)")
            except Exception as e:
                logger.warning(f"⚠️ Error cargando .env.local: {e}")
        
        # Step 2: Load all variables with precedence
        for var_name, var_meta in self.VARIABLE_CATALOG.items():
            value = None
            source = EnvSource.NOT_SET
            
            # Check os.environ (highest priority - Replit Secrets)
            if var_name in os.environ:
                value = os.environ[var_name]
                source = EnvSource.REPLIT_SECRET
            
            # Check defaults (lowest priority)
            elif 'default' in var_meta:
                value = var_meta['default']
                source = EnvSource.DEFAULT
            
            # Store value and source
            if value is not None:
                self._env_data[var_name] = value
                self._env_sources[var_name] = source
        
        # Step 3: Log loaded configuration
        self._log_configuration_summary()
    
    def _log_configuration_summary(self):
        """Log summary of loaded configuration"""
        logger.info("\n📊 RESUMEN DE CONFIGURACIÓN CARGADA:")
        logger.info("-" * 70)
        
        # Group by category
        by_category: Dict[EnvCategory, List[str]] = {}
        for var_name, var_meta in self.VARIABLE_CATALOG.items():
            category = var_meta['category']
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(var_name)
        
        # Log each category
        for category in EnvCategory:
            if category in by_category:
                logger.info(f"\n🔹 {category.value.upper().replace('_', ' ')}:")
                for var_name in sorted(by_category[category]):
                    if var_name in self._env_data:
                        source = self._env_sources[var_name]
                        is_secret = self._is_secret_variable(var_name)
                        value_display = "***HIDDEN***" if is_secret else self._env_data[var_name]
                        logger.info(f"   ✅ {var_name}: {value_display} [from: {source.value}]")
                    else:
                        is_required = self.VARIABLE_CATALOG[var_name].get('required', False)
                        status = "❌ REQUIRED" if is_required else "⚪ Optional"
                        logger.info(f"   {status} {var_name}: Not Set")
        
        logger.info("-" * 70)
        logger.info(f"✅ Total variables cargadas: {len(self._env_data)}/{len(self.VARIABLE_CATALOG)}")
        logger.info("=" * 70 + "\n")
    
    def _is_secret_variable(self, var_name: str) -> bool:
        """Check if variable contains sensitive data"""
        sensitive_keywords = ['TOKEN', 'KEY', 'SECRET', 'PASSWORD', 'API', 'ENCRYPTION']
        sensitive_exact_names = ['DATABASE_URL', 'REDIS_URL', 'CELERY_BROKER_URL', 'CELERY_RESULT_BACKEND', 'SENTRY_DSN']
        return (
            any(keyword in var_name.upper() for keyword in sensitive_keywords) or
            var_name in sensitive_exact_names
        )
    
    def _validate_value(self, var_name: str, value: str) -> bool:
        """Validate value format according to catalog rules"""
        if var_name not in self.VARIABLE_CATALOG:
            return True
        
        is_pytest = os.environ.get('PYTEST_CURRENT_TEST') is not None or \
                    (os.environ.get('TESTING', '').lower() in ('true', '1', 'yes') and 
                     'pytest' in sys.modules)
        if is_pytest and var_name == 'TELEGRAM_BOT_TOKEN':
            return True
        
        validator = self.VARIABLE_CATALOG[var_name].get('validator')
        if validator is None:
            return True
        
        try:
            return validator(value)
        except Exception as e:
            logger.warning(f"⚠️ Error validando {var_name}: {e}")
            return False
    
    def get(self, var_name: str, default: Any = None, cast_type: type = str) -> Any:
        """
        Get environment variable with default and type casting
        
        Args:
            var_name: Name of the variable
            default: Default value if not found
            cast_type: Type to cast the value to (str, int, bool, float)
        
        Returns:
            Variable value with proper type
        """
        value = self._env_data.get(var_name, default)
        
        if value is None:
            return None
        
        # Type casting
        try:
            if cast_type == bool:
                if isinstance(value, bool):
                    return value
                return str(value).lower() in ['true', '1', 'yes', 'on']
            elif cast_type == int:
                return int(value)
            elif cast_type == float:
                return float(value)
            else:
                return str(value)
        except (ValueError, TypeError) as e:
            logger.warning(f"⚠️ Error casting {var_name} to {cast_type.__name__}: {e}")
            return default
    
    def get_required(self, var_name: str, cast_type: type = str) -> Any:
        """
        Get required environment variable (raises error if not found)
        
        Args:
            var_name: Name of the variable
            cast_type: Type to cast the value to
        
        Returns:
            Variable value
        
        Raises:
            ValueError: If variable is not set or validation fails
        """
        is_pytest = os.environ.get('PYTEST_CURRENT_TEST') is not None or \
                    (os.environ.get('TESTING', '').lower() in ('true', '1', 'yes') and 
                     'pytest' in sys.modules)
        if is_pytest and var_name == 'TELEGRAM_BOT_TOKEN':
            test_token = os.environ.get('TELEGRAM_BOT_TOKEN', 'test-mode-token')
            return test_token
        
        if var_name not in self._env_data:
            raise ValueError(
                f"❌ VARIABLE REQUERIDA NO ENCONTRADA: {var_name}\n"
                f"Por favor configura {var_name} en Replit Secrets o .env.local"
            )
        
        value = self._env_data[var_name]
        
        # Validate value
        if not self._validate_value(var_name, str(value)):
            raise ValueError(
                f"❌ VALIDACIÓN FALLIDA PARA: {var_name}\n"
                f"Formato inválido. Ejemplo esperado: {self.VARIABLE_CATALOG[var_name].get('example', 'N/A')}"
            )
        
        # Cast and return
        return self.get(var_name, cast_type=cast_type)
    
    def list_variables(self, category: Optional[EnvCategory] = None, 
                      include_values: bool = False) -> Dict[str, Any]:
        """
        List all configured variables (without exposing secrets)
        
        Args:
            category: Filter by category (optional)
            include_values: Include actual values (NOT RECOMMENDED for secrets)
        
        Returns:
            Dictionary with variable information
        """
        result = {}
        
        for var_name, var_meta in self.VARIABLE_CATALOG.items():
            # Filter by category if specified
            if category and var_meta['category'] != category:
                continue
            
            is_set = var_name in self._env_data
            is_secret = self._is_secret_variable(var_name)
            
            var_info = {
                'category': var_meta['category'].value,
                'required': var_meta.get('required', False),
                'is_set': is_set,
                'source': self._env_sources.get(var_name, EnvSource.NOT_SET).value,
                'description': var_meta.get('description', ''),
                'example': var_meta.get('example', '')
            }
            
            # Include value only if requested and not secret
            if include_values and is_set:
                if is_secret:
                    var_info['value'] = '***HIDDEN***'
                else:
                    var_info['value'] = self._env_data[var_name]
            
            result[var_name] = var_info
        
        return result
    
    def get_by_category(self, category: EnvCategory) -> Dict[str, Any]:
        """Get all variables from a specific category"""
        return {
            var_name: self.get(var_name)
            for var_name, var_meta in self.VARIABLE_CATALOG.items()
            if var_meta['category'] == category and var_name in self._env_data
        }
    
    def validate_all_required(self) -> List[str]:
        """
        Validate all required variables are set
        
        Returns:
            List of missing required variables (empty if all OK)
        """
        missing = []
        for var_name, var_meta in self.VARIABLE_CATALOG.items():
            if var_meta.get('required', False) and var_name not in self._env_data:
                missing.append(var_name)
        
        if missing:
            logger.error(f"❌ Variables requeridas faltantes: {', '.join(missing)}")
        else:
            logger.info("✅ Todas las variables requeridas están configuradas")
        
        return missing
    
    def __repr__(self) -> str:
        """String representation"""
        return f"<EnvConfig: {len(self._env_data)}/{len(self.VARIABLE_CATALOG)} variables loaded>"


# Singleton instance
env_config = EnvConfig()


# Convenience functions for backward compatibility
def get_env(var_name: str, default: Any = None, cast_type: type = str) -> Any:
    """Get environment variable (backward compatible)"""
    return env_config.get(var_name, default, cast_type)


def get_required_env(var_name: str, cast_type: type = str) -> Any:
    """Get required environment variable (backward compatible)"""
    return env_config.get_required(var_name, cast_type)
