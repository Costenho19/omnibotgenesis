import React from 'react'

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends React.Component<{ children: React.ReactNode }, State> {
  constructor(props: { children: React.ReactNode }) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[OMNIX] Rendering error caught by ErrorBoundary:', error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          background: '#050D18',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: 'Inter, system-ui, sans-serif',
          color: '#E2E8F0',
          padding: '2rem',
          textAlign: 'center',
        }}>
          <img src="/omnix_logo.png" alt="OMNIX" style={{ height: 40, marginBottom: 24, opacity: 0.8 }} />
          <h2 style={{ fontSize: 20, fontWeight: 700, color: '#F8FAFC', marginBottom: 8 }}>
            Loading dashboard…
          </h2>
          <p style={{ fontSize: 14, color: '#64748b', marginBottom: 24, maxWidth: 400 }}>
            The governance system is operational. Reloading this page will restore the dashboard.
          </p>
          <button
            onClick={() => { this.setState({ hasError: false, error: null }); window.location.reload() }}
            style={{
              background: 'rgba(201,162,39,0.12)',
              border: '1px solid rgba(201,162,39,0.3)',
              color: '#C9A227',
              padding: '0.6rem 1.5rem',
              borderRadius: 8,
              cursor: 'pointer',
              fontSize: 13,
              fontWeight: 600,
            }}
          >
            Reload Dashboard
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
