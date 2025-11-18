"""
OMNIX V5.1 ENTERPRISE - Centralized Logging System
Features: Structured logging, rotation, monitoring integration
"""

import logging
import sys
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime
from omnix_config.settings import settings


class ColoredFormatter(logging.Formatter):
    """Colored console formatter for development"""
    
    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',   # Green
        'WARNING': '\033[33m', # Yellow
        'ERROR': '\033[31m',   # Red
        'CRITICAL': '\033[35m' # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


class StructuredFormatter(logging.Formatter):
    """JSON-like structured formatter for production"""
    
    def format(self, record):
        log_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        
        # Add exception info if present
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
        
        return str(log_record)


def setup_logging(service_name: str = "omnix"):
    """Setup enterprise logging system"""
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.monitoring.log_level))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console Handler (colored for development)
    console_handler = logging.StreamHandler(sys.stdout)
    if settings.DEBUG:
        console_formatter = ColoredFormatter(
            '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        console_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File Handler - All logs
    all_file_handler = RotatingFileHandler(
        log_dir / f"{service_name}_all.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    all_file_handler.setLevel(logging.DEBUG)
    if settings.is_production():
        all_file_formatter = StructuredFormatter()
    else:
        all_file_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    all_file_handler.setFormatter(all_file_formatter)
    root_logger.addHandler(all_file_handler)
    
    # File Handler - Errors only
    error_file_handler = TimedRotatingFileHandler(
        log_dir / f"{service_name}_errors.log",
        when='midnight',
        interval=1,
        backupCount=30  # Keep 30 days of error logs
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(all_file_formatter)
    root_logger.addHandler(error_file_handler)
    
    # File Handler - Trading specific (for audit)
    trading_file_handler = RotatingFileHandler(
        log_dir / f"{service_name}_trading.log",
        maxBytes=50*1024*1024,  # 50MB (important for audit)
        backupCount=10
    )
    trading_file_handler.setLevel(logging.INFO)
    trading_file_handler.addFilter(lambda record: 'trading' in record.name.lower())
    trading_file_handler.setFormatter(all_file_formatter)
    root_logger.addHandler(trading_file_handler)
    
    # Suppress noisy loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    logging.info(f"✅ Logging system initialized - Service: {service_name}, Level: {settings.monitoring.log_level}")


def get_logger(name: str) -> logging.Logger:
    """Get logger instance with name"""
    return logging.getLogger(name)


# Initialize logging on import
setup_logging()
