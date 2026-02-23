import { useState, useEffect } from 'react'

export interface LiveMetrics {
  evaluation_cycles: number
  pqc_signed_receipts: number
  capital_preserved_pct: number
  verticals_demo: number
  system_uptime_days: number
}

interface LiveMetricsResponse {
  success: boolean
  live: boolean
  metrics: LiveMetrics
  source: string
  last_updated: string
}

const FALLBACK_METRICS: LiveMetrics = {
  evaluation_cycles: 670000,
  pqc_signed_receipts: 16000,
  capital_preserved_pct: 98.5,
  verticals_demo: 4,
  system_uptime_days: 0,
}

const API_BASE = import.meta.env.VITE_API_BASE || ''

export function useLiveMetrics(refreshIntervalMs = 60000) {
  const [metrics, setMetrics] = useState<LiveMetrics>(FALLBACK_METRICS)
  const [isLive, setIsLive] = useState(false)
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true

    const fetchMetrics = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/live-metrics`)
        if (response.ok) {
          const data: LiveMetricsResponse = await response.json()
          if (mounted && data.success && data.metrics) {
            setMetrics(data.metrics)
            setIsLive(data.live)
            setLastUpdated(data.last_updated)
          }
        }
      } catch {
      } finally {
        if (mounted) setLoading(false)
      }
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
