"""
OMNIX Dashboard - Gunicorn Configuration
Production WSGI server configuration for Railway deployment

Worker class: gevent for async I/O (API calls to Kraken/Finnhub)

Phase 2 (Dec 2025): Added post_fork hook for DatabaseGateway pool reinit
"""

import os
import multiprocessing
import logging

from omnix_config import VERSION_BANNER

logger = logging.getLogger(__name__)

USE_UNIFIED_GATEWAY = os.environ.get('USE_UNIFIED_GATEWAY', 'false').lower() == 'true'

bind = "0.0.0.0:5000"

workers = int(os.environ.get('WEB_CONCURRENCY', multiprocessing.cpu_count() * 2 + 1))
workers = min(workers, 4)

worker_class = "gevent"

worker_connections = 1000

timeout = 120

keepalive = 5

max_requests = 1000
max_requests_jitter = 50

accesslog = "-"
errorlog = "-"
loglevel = os.environ.get('LOG_LEVEL', 'info')

capture_output = True
enable_stdio_inheritance = True

preload_app = False

def on_starting(server):
    print(f"OMNIX Dashboard {VERSION_BANNER} - Gunicorn starting...")
    if USE_UNIFIED_GATEWAY:
        print("  DatabaseGateway mode: UNIFIED (post_fork reinit enabled)")
    else:
        print("  DatabaseGateway mode: LEGACY (per-worker pools)")


def post_fork(server, worker):
    """
    Phase 2: Reinitialize DatabaseGateway pool after worker fork.
    
    Gunicorn's prefork model creates child processes AFTER loading the app.
    Each worker needs its own fresh connection pool to avoid shared file 
    descriptors and connection state issues.
    
    This hook only activates when USE_UNIFIED_GATEWAY=true.
    """
    if USE_UNIFIED_GATEWAY:
        try:
            from omnix_services.database_service.database_gateway import DatabaseGateway
            DatabaseGateway.reinit_after_fork()
            print(f"Worker {worker.pid}: DatabaseGateway pool reinitialized")
        except ImportError as e:
            print(f"Worker {worker.pid}: DatabaseGateway not available: {e}")
        except Exception as e:
            print(f"Worker {worker.pid}: Error reinitializing gateway: {e}")


def on_exit(server):
    print(f"OMNIX Dashboard {VERSION_BANNER} - Gunicorn shutting down...")


def worker_exit(server, worker):
    print(f"Worker {worker.pid} exiting...")
