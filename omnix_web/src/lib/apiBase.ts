/**
 * OMNIX API Base URL resolver
 *
 * Always same-origin. Flask handles all /api/* routes directly
 * whether in development (port 5000) or production (gunicorn).
 * React Vite proxy forwards /api/* to Flask:5000 in dev mode.
 */

export const API_BASE = ''
