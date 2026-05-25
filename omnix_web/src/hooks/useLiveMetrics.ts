import { useState, useEffect, useRef } from 'react'

export interface LiveMetrics {
  evaluation_cycles: number
  pqc_signed_receipts: number
  decisions_blocked: number
  capital_preserved_pct: number
  verticals_demo: number
  system_uptime_days: number
  ebip_score: number
}

const TRACK_RECORD_START = new Date('2026-01-15T00:00:00Z')
const calcUptimeDays = () =>
  Math.floor((Date.now() - TRACK_RECORD_START.getTime()) / 86400000) + 1

const FALLBACK_METRICS: LiveMetrics = {
  evaluation_cycles: 0,
  pqc_signed_receipts: 0,
  decisions_blocked: 0,
  capital_preserved_pct: 0,
  verticals_demo: 10,
  system_uptime_days: calcUptimeDays(),
  ebip_score: 0,
}

const RAILWAY_PUBLIC_API = import.meta.env.VITE_RAILWAY_API_URL || ''
const LOCAL_API = import.meta.env.VITE_API_BASE || ''
const FLASK_API = import.meta.env.VITE_FLASK_API_URL || ''

const NO_CACHE_OPTS: RequestInit = {
  cache: 'no-store',
}

export function useLiveMetrics(refreshIntervalMs = 10000) {
  const [metrics, setMetrics] = useState<LiveMetrics>(FALLBACK_METRICS)
  const [isLive, setIsLive] = useState(false)
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)
  const [animKey, setAnimKey] = useState(0)
  const wasLiveRef = useRef(false)

  useEffect(() => {
    let mounted = true

    const fetchEbipScore = async (): Promise<number> => {
      try {
        const url = FLASK_API
          ? `${FLASK_API}/api/governance/execution-integrity`
          : `${LOCAL_API}/api/governance/execution-integrity`
        const res = await fetch(url, NO_CACHE_OPTS)
        if (res.ok) {
          const d = await res.json()
          if (d.execution_integrity?.overall_execution_integrity != null) {
            return Math.round(d.execution_integrity.overall_execution_integrity)
          }
        }
      } catch {}
      return FALLBACK_METRICS.ebip_score
    }

    const fetchFromRailway = async (): Promise<boolean> => {
      if (!RAILWAY_PUBLIC_API) return false
      try {
        const ts = Date.now()
        const response = await fetch(`${RAILWAY_PUBLIC_API}/api/governance/metrics?_t=${ts}`, NO_CACHE_OPTS)
        if (response.ok) {
          const data = await response.json()
          if (mounted && data.governance_summary) {
            const gs = data.governance_summary
            const ebip = await fetchEbipScore()
            setMetrics({
              evaluation_cycles: gs.total_evaluation_cycles || FALLBACK_METRICS.evaluation_cycles,
              pqc_signed_receipts: gs.total_receipts || FALLBACK_METRICS.pqc_signed_receipts,
              decisions_blocked: gs.decisions_blocked ?? FALLBACK_METRICS.decisions_blocked,
              capital_preserved_pct: gs.capital_preserved_pct ?? FALLBACK_METRICS.capital_preserved_pct,
              verticals_demo: Math.max(gs.verticals_demo ?? 10, 10),
              system_uptime_days: gs.system_uptime_days ?? FALLBACK_METRICS.system_uptime_days,
              ebip_score: ebip,
            })
            setIsLive(true)
            setLastUpdated(new Date().toISOString())
            if (!wasLiveRef.current) {
              wasLiveRef.current = true
              setAnimKey(k => k + 1)
            }
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
          if (mounted && data.success && data.metrics) {
            const ebip = await fetchEbipScore()
            setMetrics({ ...data.metrics, ebip_score: ebip })
            setIsLive(data.live === true)
            setLastUpdated(data.last_updated)
            if (data.live && !wasLiveRef.current) {
              wasLiveRef.current = true
              setAnimKey(k => k + 1)
            }
            return true
          }
        }
      } catch {}
      return false
    }

    const fetchMetrics = async () => {
      const localOk = await fetchFromLocal()
      if (!localOk) {
        await fetchFromRailway()
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
    animKey,
  }
}
