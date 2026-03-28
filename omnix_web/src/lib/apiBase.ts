/**
 * OMNIX API Base URL resolver
 *
 * Always same-origin. In the published Replit app, the CDN serves
 * pre-built static JSON snapshots placed in public/api/credit/*.
 * In Railway and localhost, Flask handles /api/* directly.
 */

export const API_BASE = ''
