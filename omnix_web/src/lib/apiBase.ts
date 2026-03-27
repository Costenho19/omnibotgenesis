/**
 * OMNIX API Base URL resolver
 *
 * Selects the correct Flask API base URL depending on the runtime environment:
 *
 * - Dev (Vite):          ''  → Vite proxy forwards /api/* to localhost:5000
 * - Railway / custom:    ''  → same-origin, gunicorn serves /api/* directly
 * - Replit published:    https://<dev-domain>  → bypasses CDN, hits Flask directly
 *
 * The Replit CDN (publicDir) intercepts same-origin /api/* calls in the published app
 * and returns index.html instead of JSON. Calling the workspace dev-domain directly
 * is cross-origin and bypasses the CDN entirely.
 */

const REPLIT_FLASK_URL =
  'https://c554b789-9f74-4d37-8420-c740ae31b663-00-1gx6dgvr464z3.worf.replit.dev'

function resolveApiBase(): string {
  if (typeof window === 'undefined') return ''
  const host = window.location.hostname
  if (host.endsWith('.replit.app') || host.endsWith('.repl.co')) {
    return REPLIT_FLASK_URL
  }
  return ''
}

export const API_BASE = resolveApiBase()
