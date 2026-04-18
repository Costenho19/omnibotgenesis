"""
Gunicorn configuration for OMNIX Dashboard on Railway.
Applies a runtime nuclear guard in each worker process to ensure
/api/* routes NEVER return HTML regardless of Flask blueprint state.
"""
import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8080')}"
workers = 2
threads = 4
timeout = 120
worker_class = "sync"
preload_app = False
accesslog = "-"
errorlog = "-"
loglevel = "info"


def post_fork(server, worker):
    """
    Called in EACH worker process after forking from master.
    Registers a nuclear after_request guard that converts any
    HTML response on /api/* to a JSON 404.
    This runs regardless of what code is in app.py or blueprints.
    """
    try:
        from omnix_dashboard.app import app
        from flask import jsonify, request as _req

        @app.after_request
        def _nuclear_api_guard(response):
            if (
                _req.path.startswith("/api/")
                and response.status_code == 200
                and response.content_type
                and "text/html" in response.content_type
            ):
                new_resp = jsonify(
                    {
                        "error": "API endpoint not found",
                        "path": _req.path,
                        "status": 404,
                        "guard": "gunicorn-runtime-v1",
                    }
                )
                new_resp.status_code = 404
                return new_resp
            return response

        server.log.info("[OMNIX] Runtime nuclear API guard registered in worker %s", worker.pid)
    except Exception as exc:
        server.log.error("[OMNIX] Failed to register runtime guard: %s", exc)
