import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    allowedHosts: true,
    proxy: {
      '/api/live-metrics': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/api/news': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/api/contact': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/evaluate': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        proxyTimeout: 15000,
        timeout: 15000,
      },
      '/api/verify': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        proxyTimeout: 15000,
        timeout: 15000,
      },
      '/api/public/sandbox': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        proxyTimeout: 120000,
        timeout: 120000,
      },
      '/api/public/verify': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/api/public/audit-demo': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/api/public/audit-live': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/api/governance/control': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        proxyTimeout: 30000,
        timeout: 30000,
      },
      '/api/governance': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/api/credit': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/api/metrics': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/api/insurance': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/api/robotics': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/api/medical': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/api/energy': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/api/agents': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/api/real-estate': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/api/stablecoin': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  }
})
