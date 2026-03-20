import { useState, useEffect } from 'react'

export interface LiveMetrics {
  evaluation_cycles: number
  pqc_signed_receipts: number
  decisions_blocked: number
  capital_preserved_pct: number
  verticals_demo: number
  system_uptime_days: number
}

const TRACK_RECORD_START = new Date('2026-01-15T00:00:00Z')
const calcUptimeDays = () =>
  Math.floor((Date.now() - TRACK_RECORD_START.getTime()) / 86400000) + 1

const FALLBACK_METRICS: LiveMetrics = {
  evaluation_cycles: 766741,
  pqc_signed_receipts: 82518,
  decisions_blocked: 9317,
  capital_preserved_pct: 98.42,
  verticals_demo: 4,
  system_uptime_days: calcUptimeDays(),
}

const RAILWAY_PUBLIC_API = 'https://omnibotgenesis-production.up.railway.app'
const LOCAL_API = import.meta.env.VITE_API_BASE || ''

const NO_CACHE_OPTS: RequestInit = {
  cache: 'no-store',
  headers: { 'Cache-Control': 'no-cache, no-store, must-revalidate', 'Pragma': 'no-cache' },
}

export function useLiveMetrics(refreshIntervalMs = 60000) {
  const [metrics, setMetrics] = useState<LiveMetrics>(FALLBACK_METRICS)
  const [isLive, setIsLive] = useState(false)
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true

    const fetchFromRailway = async (): Promise<boolean> => {
      try {
        const ts = Date.now()
        const response = await fetch(`${RAILWAY_PUBLIC_API}/api/governance/metrics?_t=${ts}`, NO_CACHE_OPTS)
        if (response.ok) {
          const data = await response.json()
          if (mounted && data.governance_summary) {
            const gs = data.governance_summary
            setMetrics({
              evaluation_cycles: gs.total_evaluation_cycles || FALLBACK_METRICS.evaluation_cycles,
              pqc_signed_receipts: gs.total_receipts || FALLBACK_METRICS.pqc_signed_receipts,
              decisions_blocked: gs.decisions_blocked ?? FALLBACK_METRICS.decisions_blocked,
              capital_preserved_pct: gs.capital_preserved_pct ?? FALLBACK_METRICS.capital_preserved_pct,
              verticals_demo: gs.verticals_demo ?? FALLBACK_METRICS.verticals_demo,
              system_uptime_days: gs.system_uptime_days ?? FALLBACK_METRICS.system_uptime_days,
            })
            setIsLive(true)
            setLastUpdated(new Date().toISOString())
            return true
          }
        }
      } catch {}
      return false
    }

    const fetchFromLocal = async (): Promise<boolean> => {
      try {
        const ts = Date.now()
        const response = await fetch(`${LOCAL_API}/api/live-metrics?_t=${ts}`, NO_CACHE_OPTS)
        if (response.ok) {
          const data = await response.json()
          if (mounted && data.success && data.metrics && data.live) {
            setMetrics(data.metrics)
            setIsLive(true)
            setLastUpdated(data.last_updated)
            return true
          }
        }
      } catch {}
      return false
    }

    const fetchMetrics = async () => {
      const railwayOk = await fetchFromRailway()
      if (!railwayOk) {
        await fetchFromLocal()
      }
      if (mounted) setLoading(false)
    }

    fetchMetrics()
    const interval = setInterval(fetchMetrics, refreshIntervalMs)

    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [refreshIntervalMs])

  const formatNumber = (n: number): string => {
    if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M+`
    if (n >= 1000) return `${(n / 1000).toFixed(0)}K+`
    return n.toLocaleString()
  }

  const formatNumberFull = (n: number): string => {
    return n.toLocaleString()
  }

  return {
    metrics,
    isLive,
    loading,
    lastUpdated,
    formatNumber,
    formatNumberFull,
  }
}
