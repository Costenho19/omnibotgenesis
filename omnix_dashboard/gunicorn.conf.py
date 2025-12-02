"""
OMNIX Dashboard V6.5 - Gunicorn Configuration
Production WSGI server configuration for Railway deployment

Worker class: gevent for async I/O (API calls to Kraken/Finnhub)
"""

import os
import multiprocessing

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
    print("OMNIX Dashboard V6.5 - Gunicorn starting...")

def on_exit(server):
    print("OMNIX Dashboard V6.5 - Gunicorn shutting down...")

def worker_exit(server, worker):
    print(f"Worker {worker.pid} exiting...")
