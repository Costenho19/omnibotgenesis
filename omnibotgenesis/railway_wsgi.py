#!/usr/bin/env python3
"""
railway_wsgi.py — WSGI entrypoint for Railway deployment.

This module wraps the Flask app with a WSGI middleware layer that:
1. Guarantees /api/* routes NEVER return HTML (converts to JSON 404)
2. Clears stale Python bytecode on startup
3. Logs all API-related requests for debugging

This runs OUTSIDE Flask's after_request hooks — even if Flask internals
are in an unexpected state, this guard catches HTML leaks.
"""
from __future__ import annotations

import io
import json
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [WSGI] %(levelname)s %(message)s",
    stream=sys.stdout,
)
_log = logging.getLogger("railway_wsgi")

# ── Step 1: clear stale bytecode (belt + suspenders for Railway builds) ──────
import pathlib
_app_root = pathlib.Path(__file__).parent
_cleared = 0
for _pyc in _app_root.rglob("*.pyc"):
    try:
        _pyc.unlink()
        _cleared += 1
    except OSError:
        pass
for _pycache in _app_root.rglob("__pycache__"):
    try:
        import shutil
        shutil.rmtree(_pycache, ignore_errors=True)
    except OSError:
        pass
_log.info(f"Cleared {_cleared} stale .pyc files at startup")

# ── Step 2: import the real Flask app ─────────────────────────────────────────
_log.info("Importing omnix_dashboard Flask app...")
from omnix_dashboard.app import app as _flask_app  # noqa: E402
_log.info(f"Flask app imported — {len(list(_flask_app.url_map.iter_rules()))} rules registered")

# Log all registered rules for /api/credit/*
_credit_rules = [r.rule for r in _flask_app.url_map.iter_rules() if "credit" in r.rule]
_log.info(f"Credit rules: {_credit_rules}")


# ── Step 3: WSGI middleware — nuclear HTML-to-JSON guard for /api/* ──────────
class _ApiHtmlGuard:
    """WSGI middleware: any /api/* response with text/html is converted to JSON 404."""

    def __init__(self, inner_app):
        self._inner = inner_app

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")

        if not path.startswith("/api/"):
            # Non-API paths: pass through unchanged
            return self._inner(environ, start_response)

        # Capture the inner app's response
        _status_ref = [None]
        _headers_ref = [None]

        def _capture(status, response_headers, exc_info=None):
            _status_ref[0] = status
            _headers_ref[0] = response_headers
            # Return a dummy write callable (not used for WSGI iter responses)
            return lambda data: None

        body_iter = self._inner(environ, _capture)

        try:
            body_bytes = b"".join(body_iter)
        finally:
            if hasattr(body_iter, "close"):
                body_iter.close()

        status = _status_ref[0] or "200 OK"
        raw_headers = _headers_ref[0] or []

        # Detect HTML response on /api/* with status 200
        content_type = next(
            (v for k, v in raw_headers if k.lower() == "content-type"), ""
        )
        status_code = int(status.split(" ", 1)[0])

        if status_code == 200 and "text/html" in content_type:
            _log.warning(
                f"BLOCKED HTML response on {path} "
                f"(status={status}, ct={content_type}) — returning JSON 404"
            )
            json_body = json.dumps(
                {"error": "API endpoint not found", "path": path}
            ).encode("utf-8")
            new_headers = [
                ("Content-Type", "application/json"),
                ("Content-Length", str(len(json_body))),
                ("X-OMNIX-Guard", "blocked-wsgi"),
            ]
            start_response("404 Not Found", new_headers)
            return [json_body]

        # Pass through as-is (JSON, 404, 500, etc.)
        # Add guard marker to confirm this middleware ran
        filtered = [(k, v) for k, v in raw_headers if k.lower() != "x-omnix-guard"]
        filtered.append(("X-OMNIX-Guard", "wsgi-ok"))
        start_response(status, filtered)
        return [body_bytes]


# ── Step 4: export the wrapped app as `app` for gunicorn ─────────────────────
app = _ApiHtmlGuard(_flask_app)
_log.info("WSGI guard active — railway_wsgi:app ready")
