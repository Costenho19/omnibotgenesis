/**
 * OMNIX API Base URL resolver
 *
 * Strategy:
 * - localhost          → '' (Vite proxy handles /api/*)
 * - omnixquantum.net  → '' (Railway Flask, same-origin)
 * - Everything else   → direct workspace Flask URL (bypasses Replit CDN)
 */

const REPLIT_FLASK_URL =
  'https://c554b789-9f74-4d37-8420-c740ae31b663-00-1gx6dgvr464z3.worf.replit.dev'

function resolveApiBase(): string {
  if (typeof window === 'undefined') return ''
  const host = window.location.hostname
  if (
    host === 'localhost' ||
    host === '127.0.0.1' ||
    host === 'omnixquantum.net' ||
    host === 'www.omnixquantum.net' ||
    host.endsWith('.railway.app') ||
    host.endsWith('.up.railway.app')
  ) {
    return ''
  }
  return REPLIT_FLASK_URL
}

export const API_BASE = resolveApiBase()
